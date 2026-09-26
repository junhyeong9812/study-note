# csharp/syntax/24 — 제네릭과 타입 매개변수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-335(CLI) 6판](https://ecma-international.org/publications-and-standards/standards/ecma-335/) · [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 제네릭 타입과 메서드](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/generics)(열어서 확인: 「C# 제네릭은 Java 제네릭·C++ 템플릿과 비슷하지만 **런타임 타입 정보가 온전하고 타입 소거가 없다**」 ·\
> 「제네릭 컬렉션은 값 타입의 **박싱을 피한다**」) ·
> [Learn — 런타임의 제네릭](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/generics/generics-in-the-run-time)(열어서 확인: 「값 타입으로 처음 구성되면 런타임이 **특수화된 타입을 만든다 — 값 타입마다 한 번**」 ·\
> 「참조 타입이면 **처음 한 번만** 객체 참조를 넣은 특수화를 만들고, **어떤 참조 타입이든 그것을 재사용**한다 — 참조는 크기가 같으니까」 · 「리플렉션으로 **실제 타입과 타입 매개변수를 런타임에 알 수 있다**」)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`). **대비는 실측이다** — **javac 21.0.5** 로 같은 모양 8개를 던지고 Java 프로그램 하나를 돌렸다((3)).
> **버전** — 제네릭 **C# 2.0 / CLR 2.0** · `where T : unmanaged` **C# 7.3** · `notnull` **C# 8**. ★ 이 문서는 판을 안 가렸다.
> **경계** — ★★★ **제약 `where` 와 `default(T)` 의 전반**은 목록의 **25번 주제**가 정본이다 — 여기서는 **제약을 어기면 무엇이 나오나**((6))와 `new T()` 가 **런타임까지 남는 증거**로만 쓴다.\
> ★ **공변·반변**은 목록의 **26번 주제** · **박싱 자체**는 [03번](../03-boxing-and-unboxing/) — 그 (4)가 `List<int>` 대 `ArrayList` 를 **한 판**에서 쟀고 「정본은 24번 주제」라고 넘겼다. 여기서는 **2×2 판 격자로 다시** 잰다((7)).
> ★★★ **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번**([`19-type-erasure/`](../../../java/syntax/19-type-erasure/))·**17번**([`17-generic-declarations/`](../../../java/syntax/17-generic-declarations/)) ·\
> Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **12번**([`12-reified-type-parameters/`](../../../kotlin/syntax/12-reified-type-parameters/)) — 소거를 `inline`+`reified` 로 **뚫는** 설계 ·\
> Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **31번**([`31-generics-trait-bounds-where-and-monomorphization/`](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/)) — **단형화** ·\
> Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **37번**(제네릭 — 폴더가 아직 없다). ★ Kotlin·Rust·Go 는 **대비만** 한다(이 판에서 던지지 않았다).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **코드 주소·메서드 핸들의 값 자체**(실행마다 다르다 — 문서에 싣지 않았다) | ★★★ 그 값들이 **「같나 다르나」**((4) — 두 판에서 같았다) |
> | 진단 **문구** · javac 의 `where T is a type-variable` 보충 줄 | ★★★ **진단 코드**(`CS0452`·`CS0453`·`CS0310`·`CS8377`·`CS8714`) · **javac `exit`** |
> | **IL 오프셋 폭** | ★★★ **옵코드와 토큰**(`ldtoken T` · `newarr T` · `initobj T` · `isinst T` · `Activator::CreateInstance`) |
> | 증분의 절댓값 일부(규칙 24) | ★★★ **「Java 에서 막히거나 소거되는 칸 N / M」 · 「네 판에서 갈린 줄 N / M」**(스크립트가 센 마지막 줄) |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version (exit=0) =====
javac 21.0.5
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **CLI 명세(ECMA-335)** | ★★★ **실행 엔진이 약속한 것** | ★★★ **제네릭 타입·메서드가 메타데이터와 IL 에 그대로 있고, 런타임이 타입 인자마다 구성된 타입을 만든다** — `List<int>` 와 `List<string>` 은 **다른 타입**이다 |
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | `new T()` 는 `new()` 제약이 있어야 · 제약 위반은 **컴파일 에러** · 정적 필드는 **구성된 타입마다** |
| **런타임 구현(CoreCLR)** | 그것을 **어떻게 JIT 하나** | ★★★ **참조 타입 인자는 코드 한 벌을 공유(`__Canon`)**, **값 타입 인자는 따로** — 이것은 **구현**이다 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 코드 주소가 같다/다르다 · 할당 바이트 · 진단 문구 |

★★★ **이 주제의 층 구분이 가장 중요하다 —**\
**「런타임까지 타입이 남는다」는 ECMA-335 가 보장**한다(구성된 타입이 **런타임의 진짜 타입**). **「참조 타입끼리 코드를 공유한다」는 CoreCLR 의 선택**이다 — Learn 의 「런타임의 제네릭」 글이 설명하지만, 다른 런타임(예: 전부 미리 컴파일하는 AOT)이 다르게 해도 **명세 위반이 아니다.**

## 한눈에 — 쉽게 말하면

**C# 의 `List<int>` 와 `List<string>` 은 다른 틀로 찍은 다른 물건이다 — Java 의 `List<Integer>` 와 `List<String>` 은 같은 물건에 붙인 다른 라벨이다.**

과자 공장을 생각하자.

- **Java(소거)** — 틀은 **하나**(`ArrayList`). 「초코 과자」·「딸기 과자」는 **포장지 라벨**일 뿐, 공장 안에서는 **같은 과자**다. 라벨은 **출고 전에 떼어진다**(컴파일 뒤 소거).
- **C#(구체화)** — 「초코 틀」·「딸기 틀」이 **따로 있다**(`List<int>`·`List<string>` 이 다른 타입). 그래서 공장 안에서도 **「이건 딸기 과자」라고 물을 수 있다**(`typeof(T)`·`o is List<string>`).
- **틀은 따로인데 기계는 나눠 쓴다** — **포장 크기가 같은 과자**(참조 타입 — 전부 「포인터 한 칸」)는 **같은 기계**(`__Canon` 공유 코드)로 찍는다. **크기가 다른 과자**(`int`·`long`)는 **기계를 따로** 짠다.
- **Rust(단형화)** — 과자마다 **기계까지 전부 새로** 짠다(Rust 31번).

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 틀이 따로 있다 | ★★★ **`typeof(List<int>) == typeof(List<string>)` 가 `False`** · Java `getClass()` 는 **`true`** | (1)(3) |
| 공장 안에서 물을 수 있다 | ★★★ **`typeof(T).Name`·`new T()`·`new T[n]`·`o is T`** 가 다 된다 — Java 는 **8칸 전부 javac 에러** | (1)(3) |
| 틀마다 따로 세는 계수기 | ★★★ **`Holder<int>.Count`·`Holder<string>.Count` 가 따로** · Java 는 **하나** | (5)(3) |
| 크기가 같으면 기계를 나눠 쓴다 | ★★★ **`List<string>.Add` 와 `List<object>.Add` 의 코드 주소가 같다** · `List<int>` 와는 **다르다** | (4) |
| 값 과자는 포장 없이 | ★★★ **`List<int>.Add` 1000번 0 바이트** · `ArrayList` 는 24000 — **네 판 같음** | (7) |

★★★ **이 주제의 본체 그림 — 소스 한 벌이 런타임에 몇 벌이 되나.**

```text
   소스                IL(메타데이터)                  런타임 타입(ECMA-335 보장)          JIT 코드(CoreCLR 구현)
   ──────────          ─────────────────────           ────────────────────────────       ──────────────────────────
   List<T>             List`1 한 벌 + T 자리 표시   →   List<int>     ─────────────────▶   List<int>.Add    (따로)
                       (newarr T · ldtoken T …)        List<long>    ─────────────────▶   List<long>.Add   (따로)
                                                        List<string>  ─┐
                                                        List<object>  ─┼──────────────▶   List<__Canon>.Add (한 벌 공유)
                                                        List<Uri>     ─┘

   Java  List<T>   →  바이트코드 ArrayList 한 벌 (T 는 Object 로 지워짐)  →  런타임 클래스 하나 · 코드 한 벌

   ★★★ C# 은 「타입은 인자마다, 코드는 크기마다」 — Java 는 「타입도 코드도 하나」.
       타입이 남으니 typeof(T)·new T()·is List<string> 이 되고, 정적 필드가 인자마다 따로다.
```

## 이 주제가 답하려는 질문

1. **「런타임까지 타입이 남는다」는 무엇으로 보이나**((1)(2)).
2. **Java 에서는 그 칸들이 어떻게 되나** — 몇 칸이 막히거나 소거되나((3)).
3. **타입이 인자마다 다르면 코드도 인자마다 다른가** — `__Canon` 공유((4)).
4. **정적 필드는 누구 것인가**((5)) · **제약을 어기면**((6)).
5. **「제네릭은 박싱이 없다」는 판을 바꿔도 참인가**((7)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ③ 리플렉션과, 그것을 Java 와 맞댄 격자다** — 「타입이 런타임에 남는다」는 **런타임에게 물어서**만 보인다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **③ 리플렉션** | ★★★ `typeof(List<int>) != typeof(List<string>)` · `GetGenericArguments()` · `typeof(T).Name` · 인자마다 따로인 정적 필드 | (1)(5) |
| ★★★ **② 진단 격자(C# 대 Java)** | ★★★ **같은 모양 10칸을 두 언어로** — 스크립트가 **「Java 에서 막히거나 소거되는 칸 N / M」** 을 센다 · 제약 위반 코드 | (3)(6) |
| ★★ **① IL 덤프** | ★★ **`ldtoken T` · `newarr T` · `initobj T` · `isinst T`** — IL 이 **`T` 를 그대로** 들고 있다 | (2) |
| ★★ **런타임 핸들 비교** | ★★ **제5의 상태** — `__Canon` 공유는 IL 에도 리플렉션 타입에도 안 보인다(IL 은 한 벌, 타입은 인자마다). **JIT 이 만든 코드의 주소**(`GetFunctionPointer`)와 **메서드 핸들**을 **「같나 다르나」로만** 견줬다. ★ 이 창이 못 보는 것 — **코드 내용**(어셈블리 덤프)은 안 봤다 | (4) |
| ★★ **④ 할당 바이트** | ★★ `ArrayList`·`object` 인자 **박싱** 대 `List<int>`·`Pick<int>` **0** — 2×2 판 격자 | (7) |

### (1) ★★★ 런타임까지 남는다 — 리플렉션으로

**언제 쓰나** — 「제네릭 안에서 `T` 가 무엇인지 알 수 있나」를 물을 때.

```text
===== 소스: cs24b-refl.cs =====
using System;
using System.Collections.Generic;
class Holder<T> { public static int Count; }
static class Gen {
    public static string Name<T>()            => typeof(T).Name;
    public static T Make<T>() where T : new() => new T();
    public static T[] Arr<T>(int n)           => new T[n];
    public static T Def<T>()                  => default!;
    public static bool Is<T>(object o)        => o is T;
    public static string Over(List<int> xs)    => "List<int> 판";
    public static string Over(List<string> xs) => "List<string> 판";
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] typeof(List<int>) == typeof(List<string>) : {typeof(List<int>) == typeof(List<string>)}");
        object xs = new List<string>();
        Console.WriteLine($"[2] 인자 : {string.Join(",", Array.ConvertAll(xs.GetType().GetGenericArguments(), t => t.Name))}");
        Console.WriteLine($"[3] xs is List<int> : {xs is List<int>} · xs is List<string> : {xs is List<string>}");
        Console.WriteLine($"[4] Name<int>() = {Gen.Name<int>()} · Name<string>() = {Gen.Name<string>()}");
        Console.WriteLine($"[5] Make<List<int>>().GetType() = {Gen.Make<List<int>>().GetType().Name}");
        Console.WriteLine($"[6] Arr<string>(3).GetType() = {Gen.Arr<string>(3).GetType()} · Arr<int>(3) = {Gen.Arr<int>(3).GetType()}");
        Console.WriteLine($"[7] Def<int>() = {Gen.Def<int>()} · Def<string>() is null = {Gen.Def<string>() is null}");
        Console.WriteLine($"[8] Is<string>(\"a\") = {Gen.Is<string>("a")} · Is<int>(\"a\") = {Gen.Is<int>("a")}");
        Console.WriteLine($"[9] {Gen.Over(new List<int>())} · {Gen.Over(new List<string>())}");
        Holder<int>.Count = 1; Holder<string>.Count = 2; Holder<object>.Count = 3;
        Console.WriteLine($"[10] Holder<int>.Count={Holder<int>.Count} Holder<string>.Count={Holder<string>.Count} Holder<object>.Count={Holder<object>.Count}");
        Console.WriteLine($"[11] typeof(List<>) = {typeof(List<>)} · IsGenericTypeDefinition={typeof(List<>).IsGenericTypeDefinition}");
    }
}
===== csc -out:ex.dll cs24b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] typeof(List<int>) == typeof(List<string>) : False
[2] 인자 : String
[3] xs is List<int> : False · xs is List<string> : True
[4] Name<int>() = Int32 · Name<string>() = String
[5] Make<List<int>>().GetType() = List`1
[6] Arr<string>(3).GetType() = System.String[] · Arr<int>(3) = System.Int32[]
[7] Def<int>() = 0 · Def<string>() is null = True
[8] Is<string>("a") = True · Is<int>("a") = False
[9] List<int> 판 · List<string> 판
[10] Holder<int>.Count=1 Holder<string>.Count=2 Holder<object>.Count=3
[11] typeof(List<>) = System.Collections.Generic.List`1[T] · IsGenericTypeDefinition=True
```

- ★★★ **`[1]` `typeof(List<int>) == typeof(List<string>)` 가 `False`** — **다른 런타임 타입**이다.
- ★★★ **`[2]` `object` 로 받은 값의 `GetGenericArguments()` 가 `String`** — 타입 인자가 **값에 붙어** 다닌다.
- ★★★ **`[3]` `xs is List<int>` 는 `False`, `xs is List<string>` 은 `True`** — **타입 인자까지 검사**한다.
- ★★★ **`[4]` 제네릭 메서드 안에서 `typeof(T).Name` 이 `Int32`·`String`** · **`[5]` `new T()`** · **`[6]` `new T[3]` 이 진짜 `String[]`·`Int32[]`** · **`[7]` `default(T)` 가 `0`·`null`** · **`[8]` `o is T`**.
- ★★ **`[9]` `List<int>` 와 `List<string>` 을 받는 오버로드 둘**이 공존한다 — 서명이 **다른 타입**이라서다.
- ★★ **`[11]` `typeof(List<>)`** — 인자를 안 채운 **제네릭 타입 정의**도 런타임 객체다(`IsGenericTypeDefinition=True`).

### (2) ★★ IL 은 `T` 를 그대로 들고 있다

```text
===== 소스: cs24b-il.cs =====
using System;
public static class Gen {
    public static string Name<T>()            => typeof(T).Name;
    public static T Make<T>() where T : new() => new T();
    public static T[] Arr<T>(int n)           => new T[n];
    public static T Def<T>()                  => default!;
    public static bool Is<T>(object o)        => o is T;
}
class Program {
    static void Main() {
        foreach (var n in new[] { "Name", "Make", "Arr", "Def", "Is" }) Il.Dump(typeof(Gen), n);
    }
}
===== csc -r:il.dll -out:ex.dll cs24b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Gen.Name ---
  IL_0000: ldtoken T
  IL_0005: call System.Type::GetTypeFromHandle
  IL_000a: callvirt System.Reflection.MemberInfo::get_Name
  IL_000f: ret
--- Gen.Make ---
  IL_0000: call System.Activator::CreateInstance
  IL_0005: ret
--- Gen.Arr ---
  IL_0000: ldarg.0
  IL_0001: newarr T
  IL_0006: ret
--- Gen.Def ---
  .locals [0] T
  IL_0000: ldloca.s 0
  IL_0002: initobj T
  IL_0008: ldloc.0
  IL_0009: ret
--- Gen.Is ---
  IL_0000: ldarg.0
  IL_0001: isinst T
  IL_0006: ldnull
  IL_0007: cgt.un
  IL_0009: ret
```

- ★★★ **`Name` 은 `ldtoken T` → `GetTypeFromHandle`** — IL 이 **「T 의 토큰」** 을 싣는다. 실제 타입으로 바꾸는 것은 **JIT 이 인스턴스화할 때**다.
- ★★★ **`Arr` 는 `newarr T`** · **`Def` 는 `initobj T`** · **`Is` 는 `isinst T`** — Java 바이트코드라면 `T` 가 **`Object` 로 지워져** 이런 명령이 **성립하지 않는다.**
- ★★ **`Make`(`new T()`)는 `call System.Activator::CreateInstance`** — 생성자를 **런타임에 찾는다.** `where T : new()` 가 그것을 **허락하는 계약**이다(25번 주제).

### (3) ★★★ C# 대 Java 격자 — 같은 모양 10칸

**언제 쓰나** — 「Java 에서 안 되던 것이 C# 에서는 되나」를 **한 표로** 답할 때.

```text
===== 소스: cs24b-grid.cs =====
using System;
using System.Collections.Generic;
class G1<T> where T : new() { public T Make() => new T(); }
class G2<T> { public T[] Arr(int n) => new T[n]; }
class G3<T> { public string Name() => typeof(T).Name; }
class G4<T> { public bool Test(object o) => o is T; }
class G5 { public bool Test(object o) => o is List<string>; }
class G6 { public string F(List<string> a) => "s"; public string F(List<int> a) => "i"; }
class G7 { public List<int> Xs = new(); }
class G8<T> { public static T? Shared; }
class Holder<T> { public static int Count; public void Bump() => Count++; }
class Program {
    static void Main() {
        Console.WriteLine($"[1] {new G1<List<int>>().Make().GetType().Name}");
        Console.WriteLine($"[2] {new G2<string>().Arr(2).GetType()}");
        Console.WriteLine($"[3] {new G3<string>().Name()}");
        Console.WriteLine($"[4] {new G4<string>().Test("a")} {new G4<string>().Test(1)}");
        Console.WriteLine($"[5] {new G5().Test(new List<string>())} {new G5().Test(new List<int>())}");
        Console.WriteLine($"[6] {new G6().F(new List<string>())}{new G6().F(new List<int>())}");
        Console.WriteLine($"[7] {new G7().Xs.GetType().GetGenericArguments()[0]}");
        G8<int>.Shared = 1; G8<string>.Shared = "b";
        Console.WriteLine($"[8] {G8<int>.Shared} {G8<string>.Shared}");
        Console.WriteLine($"[9] List<string> 와 List<int> 의 GetType() 이 같나 : {new List<string>().GetType() == new List<int>().GetType()}");
        new Holder<string>().Bump(); new Holder<int>().Bump();
        Console.WriteLine($"[10] Holder<string>.Count={Holder<string>.Count} Holder<int>.Count={Holder<int>.Count}");
    }
}
===== csc -nullable:enable -out:ex.dll cs24b-grid.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] List`1
[2] System.String[]
[3] String
[4] True False
[5] True False
[6] si
[7] System.Int32
[8] 1 b
[9] List<string> 와 List<int> 의 GetType() 이 같나 : False
[10] Holder<string>.Count=1 Holder<int>.Count=1
===== 소스: G1.java =====
class G1<T> { T make() { return new T(); } }
===== javac -d j24out j24/G1.java (cc exit=1) =====
j24/G1.java:1: error: unexpected type
class G1<T> { T make() { return new T(); } }
                                    ^
  required: class
  found:    type parameter T
  where T is a type-variable:
    T extends Object declared in class G1
1 error
===== 소스: G2.java =====
class G2<T> { T[] arr(int n) { return new T[n]; } }
===== javac -d j24out j24/G2.java (cc exit=1) =====
j24/G2.java:1: error: generic array creation
class G2<T> { T[] arr(int n) { return new T[n]; } }
                                      ^
1 error
===== 소스: G3.java =====
class G3<T> { String name() { return T.class.getName(); } }
===== javac -d j24out j24/G3.java (cc exit=1) =====
j24/G3.java:1: error: cannot select from a type variable
class G3<T> { String name() { return T.class.getName(); } }
                                      ^
1 error
===== 소스: G4.java =====
class G4<T> { boolean test(Object o) { return o instanceof T; } }
===== javac -d j24out j24/G4.java (cc exit=1) =====
j24/G4.java:1: error: Object cannot be safely cast to T
class G4<T> { boolean test(Object o) { return o instanceof T; } }
                                              ^
  where T is a type-variable:
    T extends Object declared in class G4
1 error
===== 소스: G5.java =====
import java.util.List;
class G5 { boolean test(Object o) { return o instanceof List<String>; } }
===== javac -d j24out j24/G5.java (cc exit=1) =====
j24/G5.java:2: error: Object cannot be safely cast to List<String>
class G5 { boolean test(Object o) { return o instanceof List<String>; } }
                                           ^
1 error
===== 소스: G6.java =====
import java.util.List;
class G6 { void f(List<String> a) { } void f(List<Integer> a) { } }
===== javac -d j24out j24/G6.java (cc exit=1) =====
j24/G6.java:2: error: name clash: f(List<Integer>) and f(List<String>) have the same erasure
class G6 { void f(List<String> a) { } void f(List<Integer> a) { } }
                                           ^
1 error
===== 소스: G7.java =====
import java.util.List;
class G7 { List<int> xs; }
===== javac -d j24out j24/G7.java (cc exit=1) =====
j24/G7.java:2: error: unexpected type
class G7 { List<int> xs; }
                ^
  required: reference
  found:    int
1 error
===== 소스: G8.java =====
class G8<T> { static T shared; }
===== javac -d j24out j24/G8.java (cc exit=1) =====
j24/G8.java:1: error: non-static type variable T cannot be referenced from a static context
class G8<T> { static T shared; }
                     ^
1 error
===== 소스: Ex24.java =====
import java.util.ArrayList;
class Holder<T> { static int count; void bump() { count++; } }
public class Ex24 {
    public static void main(String[] a) {
        System.out.println("[9] ArrayList<String> 와 ArrayList<Integer> 의 getClass() 가 같나 : "
            + (new ArrayList<String>().getClass() == new ArrayList<Integer>().getClass()));
        new Holder<String>().bump(); new Holder<Integer>().bump();
        System.out.println("[10] Holder<String> 과 Holder<Integer> 를 한 번씩 bump 한 뒤 count : " + Holder.count);
    }
}
===== javac -d j24out j24/Ex24.java && java -cp j24out Ex24 (cc exit=0 · run exit=0) =====
[9] ArrayList<String> 와 ArrayList<Integer> 의 getClass() 가 같나 : true
[10] Holder<String> 과 Holder<Integer> 를 한 번씩 bump 한 뒤 count : 2
===== 격자 — 행;C# 컴파일;Java 결과 =====
1;new T();C# cc exit=0;Java 막힘(javac exit=1)
2;new T[n];C# cc exit=0;Java 막힘(javac exit=1)
3;typeof(T) · T.class;C# cc exit=0;Java 막힘(javac exit=1)
4;o is T · instanceof T;C# cc exit=0;Java 막힘(javac exit=1)
5;o is List<string> · instanceof List<String>;C# cc exit=0;Java 막힘(javac exit=1)
6;타입 인자만 다른 오버로드;C# cc exit=0;Java 막힘(javac exit=1)
7;값 타입 인자 List<int>;C# cc exit=0;Java 막힘(javac exit=1)
8;정적 필드의 타입이 T;C# cc exit=0;Java 막힘(javac exit=1)
9;두 인스턴스화의 런타임 클래스;C# cc exit=0;Java 소거(같은 클래스)
10;정적 필드가 인스턴스화마다 따로;C# cc exit=0;Java 소거(카운터 하나)
Java 에서 막히거나 소거되는 칸 10 / 10
```

- ★★★ **Java 에서 막히거나 소거되는 칸 10 / 10** · **C# 은 10칸 전부 `cc exit=0`**(한 파일)이고 실행 결과가 위에 있다.
- ★★★ **1\~8 은 javac 가 컴파일부터 거절한다** —\
  `new T()` → `unexpected type` · `new T[n]` → **`generic array creation`** · `T.class` → **`cannot select from a type variable`** · `instanceof T`·`instanceof List<String>` → **`Object cannot be safely cast to …`** ·\
  타입 인자만 다른 오버로드 → **`name clash: … have the same erasure`** · `List<int>` → `unexpected type`(참조 타입이 필요) · 정적 필드의 타입이 `T` → **`non-static type variable T cannot be referenced from a static context`**.
- ★★★ **9·10 은 Java 가 돌아간다 — 그런데 지워져 있다** — `ArrayList<String>` 과 `ArrayList<Integer>` 의 `getClass()` 가 **`true`(같다)**, `Holder<String>`·`Holder<Integer>` 를 한 번씩 올린 **`count` 가 2**(카운터가 **하나**).\
  **C# 은 `[9]` `False` · `[10]` 각각 1** 이다.
- ★★ **여덟 에러의 뿌리는 하나** — Java 는 런타임에 **`T` 가 무엇인지 모른다.** 그래서 「`T` 를 런타임에 써야 하는 것」이 전부 막힌다. [Java 19번](../../../java/syntax/19-type-erasure/)이 같은 에러들을 **소거의 결과**로 정리했다.

```text
   칸                                 C#                            Java(javac 21.0.5)
   1  new T()                         ○ (where T : new())           ✕ unexpected type
   2  new T[n]                        ○ 진짜 String[]                ✕ generic array creation
   3  typeof(T) · T.class             ○ "String"                    ✕ cannot select from a type variable
   4  o is T                          ○                             ✕ Object cannot be safely cast to T
   5  o is List<string>               ○ 인자까지 검사                  ✕ Object cannot be safely cast to List<String>
   6  List<string>/List<int> 오버로드   ○                             ✕ name clash … same erasure
   7  List<int>                       ○ 박싱 없이                     ✕ unexpected type(참조만)
   8  static T 필드                    ○ 인자마다 따로                  ✕ non-static type variable T …
   9  두 인스턴스화의 클래스             다르다(False)                   ★ 같다(true)
   10 정적 카운터                      인자마다 1 · 1                  ★ 하나 · 2

   ★★★ 10 / 10 — 소거가 막는 것은 전부 「런타임에 T 를 쓰는 것」 이다.
```

- ★★ **Kotlin 은 같은 소거 위에서 `inline fun <reified T>` 로 뚫는다** — `reified` 없이 `x is T` 는 **`cannot check for instance of erased type`**([Kotlin 12번](../../../kotlin/syntax/12-reified-type-parameters/) 실측). **C# 은 그런 장치가 필요 없다** — 모든 제네릭이 처음부터 「reified」다.

### (4) ★★★ 타입은 따로, 코드는 공유 — `__Canon`

**언제 쓰나** — 「`List<A>`·`List<B>`… 참조 타입 인자 100개면 코드도 100벌인가」.

```text
===== 소스: cs24b-canon.cs =====
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
class Box<T> {
    [MethodImpl(MethodImplOptions.NoInlining)] public int Size() => 1;
}
class Program {
    static IntPtr Code(Type t, string m) {
        var mi = t.GetMethod(m)!;
        RuntimeHelpers.PrepareMethod(mi.MethodHandle, new[] { t.TypeHandle });   // JIT 을 먼저 시킨다
        return mi.MethodHandle.GetFunctionPointer();
    }
    static IntPtr Desc(Type t, string m) => t.GetMethod(m)!.MethodHandle.Value;
    static void Main() {
        Console.WriteLine($"[1] System.__Canon 이 있나 : {typeof(object).Assembly.GetType("System.__Canon") is not null}");
        Type ls = typeof(List<string>), lo = typeof(List<object>), li = typeof(List<int>), ll = typeof(List<long>);
        Console.WriteLine($"[2] 코드 주소  List<string>.Add == List<object>.Add : {Code(ls, "Add") == Code(lo, "Add")}");
        Console.WriteLine($"[3] 코드 주소  List<string>.Add == List<int>.Add    : {Code(ls, "Add") == Code(li, "Add")}");
        Console.WriteLine($"[4] 코드 주소  List<int>.Add    == List<long>.Add   : {Code(li, "Add") == Code(ll, "Add")}");
        Console.WriteLine($"[5] 메서드 핸들 List<string>.Add == List<object>.Add : {Desc(ls, "Add") == Desc(lo, "Add")}");
        Console.WriteLine($"[6] 메서드 핸들 List<int>.Add    == List<long>.Add   : {Desc(li, "Add") == Desc(ll, "Add")}");
        Type bs = typeof(Box<string>), bu = typeof(Box<Uri>), bi = typeof(Box<int>);
        Console.WriteLine($"[7] 코드 주소  Box<string>.Size == Box<Uri>.Size    : {Code(bs, "Size") == Code(bu, "Size")}");
        Console.WriteLine($"[8] 코드 주소  Box<string>.Size == Box<int>.Size    : {Code(bs, "Size") == Code(bi, "Size")}");
        Console.WriteLine($"[9] 타입 핸들  Box<string> == Box<Uri>              : {bs.TypeHandle.Value == bu.TypeHandle.Value}");
    }
}
===== csc -out:ex.dll cs24b-canon.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] System.__Canon 이 있나 : True
[2] 코드 주소  List<string>.Add == List<object>.Add : True
[3] 코드 주소  List<string>.Add == List<int>.Add    : False
[4] 코드 주소  List<int>.Add    == List<long>.Add   : False
[5] 메서드 핸들 List<string>.Add == List<object>.Add : True
[6] 메서드 핸들 List<int>.Add    == List<long>.Add   : False
[7] 코드 주소  Box<string>.Size == Box<Uri>.Size    : True
[8] 코드 주소  Box<string>.Size == Box<int>.Size    : False
[9] 타입 핸들  Box<string> == Box<Uri>              : False
===== csc -optimize -out:exo.dll cs24b-canon.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] System.__Canon 이 있나 : True
[2] 코드 주소  List<string>.Add == List<object>.Add : True
[3] 코드 주소  List<string>.Add == List<int>.Add    : False
[4] 코드 주소  List<int>.Add    == List<long>.Add   : False
[5] 메서드 핸들 List<string>.Add == List<object>.Add : True
[6] 메서드 핸들 List<int>.Add    == List<long>.Add   : False
[7] 코드 주소  Box<string>.Size == Box<Uri>.Size    : True
[8] 코드 주소  Box<string>.Size == Box<int>.Size    : False
[9] 타입 핸들  Box<string> == Box<Uri>              : False
```

- ★★★ **`[1]` `System.__Canon` 이라는 타입이 코어 라이브러리에 있다** — 공유 코드가 **「아무 참조 타입」** 자리에 쓰는 표식이다.
- ★★★ **`[2]` `List<string>.Add` 와 `List<object>.Add` 의 JIT 코드 주소가 같다** · **`[3]` `List<int>.Add` 와는 다르다** · **`[4]` `List<int>` 와 `List<long>` 도 다르다.**
- ★★★ **`[5]` 메서드 핸들까지 같다** — 런타임이 두 `Add` 를 **같은 메서드 하나**로 다룬다. **`[6]` 값 타입 둘은 다르다.**
- ★★ **`[7]`·`[8]` 내가 만든 `Box<T>` 도 같은 모양** — `Box<string>`·`Box<Uri>` 는 코드 공유, `Box<int>` 는 따로.
- ★★★ **`[9]` 그런데 `Box<string>` 과 `Box<Uri>` 의 타입 핸들은 다르다** — **타입은 따로, 코드는 하나.** 이것이 (1)의 「런타임까지 남는다」와 「코드 공유」가 **함께 성립하는** 방식이다.
- ★★ **`csc -optimize` + `TieredCompilation=0` 판도 아홉 줄이 같다** — 최적화 여부와 무관한 **구조**다.

```text
   Box<string>  타입 핸들 A ──┐                       Box<int>   타입 핸들 C ──▶ Box<int>.Size  코드 Z
   Box<Uri>     타입 핸들 B ──┴─▶ Box<__Canon>.Size 코드 Y
                ★ A ≠ B (타입은 따로)   ★ 코드는 Y 하나

   공유 코드 안에서도 typeof(T) 는 맞게 나온다((1) [4]) — 어떻게 찾는지는 「더 들어가면」(이 판에서 안 찍었다).
   값 타입은 크기가 인자마다 달라 한 코드로 못 다룬다(Learn 「런타임의 제네릭」) — 인자마다 따로 JIT.
```

> **어느 층인가** — ★★★ **`__Canon` 공유는 CoreCLR 의 구현**이다. ECMA-335 는 **「구성된 타입이 있다」** 까지만 요구하고 **코드를 몇 벌 만들지**는 정하지 않는다.\
> ★ Learn 「런타임의 제네릭」 글이 이 공유를 설명하지만 **글이 있다고 명세가 되지는 않는다.**\
> ★★ **다른 설계와 대비** — **Rust 는 인자마다 코드를 전부 찍는다**(단형화 — [Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/)) ·\
> **Go 는 「GC shape」(메모리 모양)이 같은 인자끼리 코드를 나눈다**고 알려져 있다(Go 갈래 목록의 **37번** — 폴더가 아직 없다 · **이 판에서 안 던졌다**) — **.NET 의 「참조 타입끼리 공유 · 값 타입은 따로」와 같은 계열의 절충**이다.

### (5) ★★ 정적 필드는 구성된 타입마다 따로

- ★★★ **(1) `[10]` `Holder<int>.Count=1 · Holder<string>.Count=2 · Holder<object>.Count=3`** — **세 값이 따로 남는다.** 정적 필드는 **`Holder<T>` 가 아니라 `Holder<int>`·`Holder<string>` 각각**의 것이다.
- ★★★ **(4)에서 `Holder<string>` 과 `Holder<object>` 는 코드를 공유하는데도** 정적 필드는 따로다 — 정적 필드는 **타입(핸들)에 붙고**, 타입은 인자마다 따로이기 때문이다.
- ★★ **Java 는 카운터가 하나**((3) 10행 — `count : 2`) · 정적 필드의 타입으로 `T` 를 **쓰지도 못한다**(8행).
- ★ 쓸모 — **타입마다 캐시 하나**(`static class Cache<T> { public static readonly … }`) 가 자물쇠·사전 없이 된다. 함정 — **「전역 카운터」를 제네릭 클래스에 두면 인자마다 쪼개진다.**

### (6) ★ 제약을 어기면 — 25번 주제의 예고편

```text
===== 소스: cs24b-cons.cs =====
using System;
class NoCtor { NoCtor(int x) { } }
static class C {
    public static void Ref<T>() where T : class { }
    public static void Val<T>() where T : struct { }
    public static void New<T>() where T : new() { }
    public static void Unm<T>() where T : unmanaged { }
    public static void Nn<T>(T x) where T : notnull { }
}
class Program {
    static void Main() {
        C.Ref<int>();
        C.Val<string>();
        C.Val<int?>();
        C.New<NoCtor>();
        C.Unm<string>();
        string? s = null;
        C.Nn(s);
    }
}
===== csc -nullable:enable -out:ex.dll cs24b-cons.cs 2>&1 | sort (cc exit=1) =====
cs24b-cons.cs(12,11): error CS0452: The type 'int' must be a reference type in order to use it as parameter 'T' in the generic type or method 'C.Ref<T>()'
cs24b-cons.cs(13,11): error CS0453: The type 'string' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'C.Val<T>()'
cs24b-cons.cs(14,11): error CS0453: The type 'int?' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'C.Val<T>()'
cs24b-cons.cs(15,11): error CS0310: 'NoCtor' must be a non-abstract type with a public parameterless constructor in order to use it as parameter 'T' in the generic type or method 'C.New<T>()'
cs24b-cons.cs(16,11): error CS8377: The type 'string' must be a non-nullable value type, along with all fields at any level of nesting, in order to use it as parameter 'T' in the generic type or method 'C.Unm<T>()'
cs24b-cons.cs(18,9): warning CS8714: The type 'string?' cannot be used as type parameter 'T' in the generic type or method 'C.Nn<T>(T)'. Nullability of type argument 'string?' doesn't match 'notnull' constraint.
```

- ★★ **`class` 제약에 `int` → `CS0452`** · **`struct` 제약에 `string` → `CS0453`** · ★ **`int?` 도 `CS0453`**(「**널 불가** 값 타입이어야」) ·\
  **`new()` 제약에 공개 기본 생성자 없는 타입 → `CS0310`** · **`unmanaged` 에 `string` → `CS8377`** · **`notnull` 에 `string?` → `CS8714` — 경고**.
- ★★ **다섯은 에러, `notnull` 하나만 경고** — `notnull` 은 **널 허용 분석**([06번](../06-nullable-reference-types/))의 일부라 경고로 내려앉는다.
- ★ **제약이 런타임까지 남는다**는 것(`new T()` 가 `Activator` 로 풀리는 것 — (2))과 **각 제약의 선택 기준**은 목록의 **25번 주제**가 정본이다.

### (7) ★★ 「제네릭은 박싱이 없다」 — 2×2 판 격자로 다시

**언제 쓰나** — [03번](../03-boxing-and-unboxing/) (4)가 한 판에서 잰 `+24000` 대 `+0` 을 **판을 바꿔도 참인지** 확인할 때.

```text
===== 소스: cs24b-alloc.cs =====
using System;
using System.Collections;
using System.Collections.Generic;
class Program {
    static int SumObj(object a, object b) => (int)a + (int)b;
    static T Pick<T>(T a, T b) => a;
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        var al = new ArrayList(1000);
        var li = new List<int>(1000);
        long sink = 0;
        Console.WriteLine($"[1] ArrayList.Add(i)         1000번 : {M(() => { al.Clear(); for (int i = 0; i < 1000; i++) al.Add(i); })} 바이트");
        Console.WriteLine($"[2] List<int>.Add(i)         1000번 : {M(() => { li.Clear(); for (int i = 0; i < 1000; i++) li.Add(i); })} 바이트");
        Console.WriteLine($"[3] SumObj(i, i) object 인자 1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += SumObj(i, i); })} 바이트");
        Console.WriteLine($"[4] Pick<int>(i, i)          1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Pick(i, i); })} 바이트");
        GC.KeepAlive(sink);
    }
}
===== csc -out:ex.dll cs24b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] ArrayList.Add(i)         1000번 : 24000 바이트
[2] List<int>.Add(i)         1000번 : 0 바이트
[3] SumObj(i, i) object 인자 1000번 : 48000 바이트
[4] Pick<int>(i, i)          1000번 : 0 바이트
===== csc -out:ex.dll cs24b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] ArrayList.Add(i)         1000번 : 24000 바이트
[2] List<int>.Add(i)         1000번 : 0 바이트
[3] SumObj(i, i) object 인자 1000번 : 48000 바이트
[4] Pick<int>(i, i)          1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs24b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] ArrayList.Add(i)         1000번 : 24000 바이트
[2] List<int>.Add(i)         1000번 : 0 바이트
[3] SumObj(i, i) object 인자 1000번 : 48000 바이트
[4] Pick<int>(i, i)          1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs24b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] ArrayList.Add(i)         1000번 : 24000 바이트
[2] List<int>.Add(i)         1000번 : 0 바이트
[3] SumObj(i, i) object 인자 1000번 : 48000 바이트
[4] Pick<int>(i, i)          1000번 : 0 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 4
```

- ★★★ **네 판에서 갈린 줄 0 / 4** — 03번의 한 판 값이 **판을 안 탔다.** [20번](../20-enum-and-flags/)의 `HasFlag` 처럼 **JIT 최적화가 박싱을 지우는 자리가 아니다** — 박싱이 **처음부터 IL 에 없다**(값 타입 인자는 인자마다 따로 JIT 되므로 (4)).
- ★★★ **`ArrayList.Add` 24000 · `SumObj(i, i)`(`object` 인자 둘) 48000** 대 **`List<int>.Add` 0 · `Pick<int>` 0**.
- ★★ **「제네릭은 박싱이 없다」의 정확한 뜻** — **값 타입 인자로 인스턴스화하면** 박싱할 자리가 **생기지 않는다.** 제네릭 안에서도 **`object`·인터페이스로 올리면**(예: 제약 없는 `T` 를 `object` 에 담기) 박싱한다 — 그 자리는 **이 판에서 안 쟀다.**
- ★ **시간은 안 쟀다.**

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs24b-form.cs =====
using System;
using System.Collections.Generic;

var stack = new Stack2<int>();
stack.Push(1); stack.Push(2);
Console.WriteLine($"{stack.Pop()} · {stack.Count} · {Max(3, 7)} · {Max("apple", "banana")}");
Console.WriteLine(Describe<List<int>>());

static T Max<T>(T a, T b) where T : IComparable<T> => a.CompareTo(b) >= 0 ? a : b;
static string Describe<T>() => $"{typeof(T).Name}<{string.Join(",", Array.ConvertAll(typeof(T).GetGenericArguments(), t => t.Name))}>";

class Stack2<T> {
    readonly List<T> items = new();
    public int Count => items.Count;
    public void Push(T x) => items.Add(x);
    public T Pop() { var x = items[^1]; items.RemoveAt(items.Count - 1); return x; }
}
===== csc -out:ex.dll cs24b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
2 · 1 · 7 · banana
List`1<Int32>
```

- ★★★ **제약으로 연산을 허락받는다** — `where T : IComparable<T>` 가 있어야 `a.CompareTo(b)` 를 쓴다.
- ★★ **`typeof(T)`·`GetGenericArguments()`** — 제네릭 안에서 **타입을 런타임에 묻는** 길(`Describe<List<int>>` → ``List`1<Int32>``).
- ★★ **제네릭 클래스 `Stack2<T>`** — `List<T>` 를 감싸 **값 타입 인자에서도 박싱 없이** 동작한다.
- ★ **타입 인자 추론** — `Max(3, 7)` 은 `Max<int>` 를 적지 않아도 된다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `class` 제약에 값 타입 | `CS0452` | (6) |
| `struct` 제약에 참조 타입 · `Nullable<T>` | `CS0453` | (6) |
| `new()` 제약에 공개 기본 생성자 없는 타입 | `CS0310` | (6) |
| `unmanaged` 제약에 참조 타입 | `CS8377` | (6) |
| `notnull` 제약에 널 허용 타입 | `CS8714`(**경고**) | (6) |
| ★★★ `new T()`·`new T[n]`·`typeof(T)`·`o is T`·`o is List<string>` | ★★★ **C# 은 진단 없음** — Java 는 전부 에러 | (3) |

## 어디서 틀리나

1. ★★★ **「C# 제네릭도 Java 처럼 컴파일 뒤 지워진다」** — **`List<int>` 와 `List<string>` 은 다른 런타임 타입**이다((1)).
2. ★★★ **「타입이 인자마다 따로면 코드도 인자마다 따로다」** — **참조 타입 인자는 코드를 공유**한다(`__Canon`)((4)).
3. ★★★ **「코드를 공유하니 타입도 하나다」** — **타입 핸들은 다르고 정적 필드도 따로**다((4) `[9]` · (5)).
4. ★★★ **「`__Canon` 공유는 언어가 보장한다」** — **CoreCLR 구현**이다. 명세는 **구성된 타입**까지만((4)).
5. ★★ **「제네릭 정적 필드는 하나다」** — **구성된 타입마다** 따로다((5)). Java 는 하나.
6. ★★ **「제네릭은 박싱이 없다」를 JIT 최적화 덕으로 알기** — **IL 에 박싱이 애초에 없다** · 네 판 같음((7)).
7. ★★ **「`new T()` 는 생성자를 직접 부른다」** — IL 은 **`Activator::CreateInstance`**((2)).
8. ★ **「`struct` 제약이면 `int?` 도 된다」** — **`CS0453`**((6)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **제네릭 타입이 런타임까지 남는다 · 구성된 타입마다 다른 타입** | ★★★ **CLI 명세(ECMA-335)** | (1)(3) |
| **정적 필드가 구성된 타입마다 따로** | ★★★ **CLI 명세 · 언어** | (5) |
| **제약 위반이 컴파일 에러** | ★★★ **언어(334)** | (6) |
| **`notnull` 위반이 경고** | ★★ **널 허용 분석(컴파일러)** | (6) |
| **참조 타입 인자의 코드 공유(`__Canon`)** | ★★ **CoreCLR 구현** | (4) |
| **값 타입 인자는 인자마다 따로 JIT** | ★★ **CoreCLR 구현** | (4) |
| **`new T()` 가 `Activator.CreateInstance<T>` 로** | ★ **Roslyn 구현** | (2) |
| **할당 바이트 값** | ★ **이 판의 관찰** | (7) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **값 타입을 담는 컬렉션·도우미는 제네릭으로** — `object` 인자는 **부를 때마다 박싱**한다((7)).
- ★★★ **`typeof(T)` 가 필요하면 그냥 쓴다** — C# 에서는 `Class<T>` 토큰을 넘기는 Java 관용구가 필요 없다((1)(3)).
- ★★ **타입마다 하나인 캐시는 제네릭 정적 필드로** — 대신 **전역 하나여야 하는 상태**를 제네릭 클래스에 두지 마라((5)).
- ★★ **제약은 필요한 만큼만** — `new()`·`struct`·`class` 는 **호출자를 좁힌다**(25번 주제).
- ★ **참조 타입 인자 100개가 코드 100벌이 될까 걱정하지 않아도 된다** — 이 판에서는 **공유**했다((4)). 값 타입 인자는 **인자마다 한 벌**이다.

## 핵심 문장

1. ★★★ **C# 제네릭은 런타임까지 남는다** — `typeof(List<int>) != typeof(List<string>)`, `typeof(T)`·`new T()`·`o is List<string>` 이 된다. 이것은 **ECMA-335 가 보장**한다((1)).
2. ★★★ **Java 에서는 같은 모양 10칸이 전부 막히거나 소거된다** — 8칸은 javac 에러, 2칸은 돌지만 지워져 있다((3)).
3. ★★★ **타입은 인자마다, 코드는 크기마다** — `List<string>.Add` 와 `List<object>.Add` 는 코드 주소가 같고, `List<int>` 와는 다르다. **`__Canon` 공유는 CoreCLR 구현**이다((4)).
4. ★★ **정적 필드는 구성된 타입마다 따로다** — 코드를 공유해도((5)).
5. ★★ **`List<int>.Add` 0 바이트는 네 판에서 같았다** — 박싱이 IL 에 애초에 없다((7)).

## 관련 자료

- [03번 — 박싱](../03-boxing-and-unboxing/) (4) — ★★ `List<int>` 대 `ArrayList` 를 **한 판**에서 쟀다. **경계**: 박싱 자체는 거기, **판 격자와 런타임 구조**는 여기.
- 목록의 **25번 주제**(제약 `where` 와 `default(T)`) — **경계**: 제약의 **선택 기준**과 `default(T)` 가 타입마다 다른 것은 거기.
- 목록의 **26번 주제**(공변·반변) — `IEnumerable<out T>`.
- [20번 — `enum`](../20-enum-and-flags/) (6) — **JIT 최적화가 박싱을 지우는** 자리와 대비((7)).
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번**([`19-type-erasure/`](../../../java/syntax/19-type-erasure/)) — **경계**: 소거의 결과(브리지 메서드·힙 오염)는 거기.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **12번**([`12-reified-type-parameters/`](../../../kotlin/syntax/12-reified-type-parameters/)) — 소거를 `reified` 로 뚫는다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **31번**([`31-generics-trait-bounds-where-and-monomorphization/`](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/)) — **단형화**.
- Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **37번** — Go 제네릭(폴더가 생기면 GC shape 대비를 거기서).

## 용어 풀이

- **타입 매개변수(type parameter)** — `List<T>` 의 `T`. **타입 인자(type argument)** 는 그 자리에 넣은 `int`·`string`.
- **구성된 타입(constructed type)** — `List<int>` 처럼 인자를 채운 타입. **런타임의 진짜 타입**이다(ECMA-335).
- **타입 소거(type erasure)** — Java 가 컴파일 뒤 타입 인자를 지우는 방식. 런타임에 `List<String>` 과 `List<Integer>` 가 같은 클래스다.
- **구체화(reification)** — 타입 인자가 런타임까지 남는 것. C#(.NET)의 방식.
- **`__Canon`** — CoreCLR 이 **참조 타입 인자 자리**에 쓰는 표식 타입. `List<__Canon>` 코드 한 벌을 모든 참조 타입 인자가 나눠 쓴다.
- **단형화(monomorphization)** — 타입 인자마다 코드를 **전부 따로** 만드는 방식(Rust).
- **`GetFunctionPointer`** — 메서드의 **JIT 된 코드 진입점 주소**를 돌려준다. 값은 실행마다 달라 **같나 다르나**로만 썼다.

## 더 들어가면

- ★ **공유 코드가 `T` 를 찾는 길**(사전·「generic dictionary」) — 객체의 타입 핸들이나 숨은 인자에서 찾는다고 알려져 있다. **이 판에서 안 찍었다.**
- ★ **제네릭 메서드(`M<T>()`)의 공유** — 인스턴스화 스텁이 끼어 **코드 주소 비교가 달라질 수 있다**고 알려져 있다. 이 문서는 **클래스의 인스턴스 메서드**로만 쟀다.
- ★ **NativeAOT 에서의 공유** — **안 던졌다.**
