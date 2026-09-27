# csharp/syntax/30 — 확장 메서드와 확장 멤버(C# 14) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 확장 멤버 선언(`extension`)](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/extension)(열어서 확인: 「**C# 14 부터** 최상위 비제네릭 `static class` 가 `extension` 블록으로 확장 멤버를 선언할 수 있다」 ·\
> 「`extension` 블록 안에 **메서드·속성·인덱서·연산자**를 선언할 수 있다」 · 「**두 형태의 확장 메서드는 같은 IL 을 만든다** — 호출자는 둘을 구별할 수 없다」 ·\
> 「이름 없는 수신자 `extension(IEnumerable<int>)` 는 멤버가 전부 정적일 때」 · ★★★ 「**C# 15 부터** `extension` 블록에 **인덱서**를 선언할 수 있다」) ·
> [Learn — 반복문(`foreach`)](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/iteration-statements)(열어서 확인: 「`GetEnumerator` 는 **확장 메서드여도 된다**」).
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. **대비는 실측이다** — **javac 21.0.5** 로 「없다」를 던졌다((5)).
> **버전** — `this` 확장 메서드 **C# 3**(★ `-langversion:2` 에서 **`CS8023 … 3 or greater`** · (4)) · `extension` 블록 **C# 14** · 확장 인덱서 **C# 15 예정**(Learn · 이 판 `CS8652` preview).\
> ★★★ **C# 13 은 `extension` 블록을 「판이 낮다」로 막지 않는다 — 파서가 못 읽는다**(`CS1513`·`CS1022`·`CS1001`). 「14 이상을 쓰라」는 안내가 **없다**((4)).
> **경계** — ★★★ **확장 인덱서**는 [14번](../14-indexers/) (7)이 먼저 던졌다(`CS8652` · preview 에서 선언은 통과하는데 호출하면 **`CS0029`** — 후보에 안 올라온다) — **인용하고, 여기서는 같은 판 격자의 한 행으로만** 다시 찍는다.\
> ★ 정적 메서드 그룹은 [27번](../27-delegates-and-func-action/) · `callvirt` 의 널 검사는 [16번](../16-inheritance-virtual-override-abstract-sealed-new/) · `foreach` 의 확장 `GetEnumerator` 는 [31번](../31-ienumerable-and-foreach/) (2).
> ★★★ **본체 창은 ① IL 덤프다** — 「문법 설탕」은 **두 호출의 IL 이 한 글자도 같은 것**으로만 증명된다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · IL **오프셋 폭** | ★★★ **진단 코드**(`CS8023` · `CS8652` · `CS0029` · `CS1513`) · **「된 칸 N / M」** |
> | ★ 컴파일러가 지은 **표지 타입 이름의 해시**(`<G>$BA41…` · `<M>$DE9F…`) | ★★★ **옵코드**(`call Ext::Twice` 대 `callvirt Object::GetHashCode`) · `[Extension]` 이 **어디에 붙나** · 이름의 **모양**(`get_Square`) |

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
| **언어 명세(ECMA-334)** | ★★★ **C# 언어가 약속한 것** | ★★★ 확장 메서드는 **첫 매개변수에 `this` 를 붙인 정적 메서드** · **인스턴스 멤버가 먼저** 찾아지고 없을 때만 확장을 본다 · **정적 타입으로 고른다** |
| **CLI · 메타데이터** | 실행 엔진이 보는 것 | ★★ 런타임에게는 **그냥 정적 메서드**(`call`) — `ExtensionAttribute` 는 **컴파일러용 표지** |
| **컴파일러 구현(Roslyn)** | ★★★ 그것을 **어떻게 적나** | ★★★ `extension` 블록의 멤버 → **`Ext` 의 정적 메서드**(`Thrice(Int32 x)` · `get_Square(Int32 x)`) + **`<G>$…` 표지 중첩 타입** · 확장 인덱서는 **preview 에서도 호출 불가** |
| **이 판의 관찰** | .NET SDK 10.0.401 · linux-x64 · javac 21.0.5 | 진단 문구 · C# 13 의 파서 에러 모양 |

★★★ **이 주제의 층 구분 —**\
**「확장 = 정적 메서드 + 수신자는 첫 인자 · 인스턴스 멤버 우선」은 명세**다. **확장 속성이 `get_Square(Int32)` 정적 메서드 + 표지 타입으로 적히는 것은 Roslyn 구현**이다(Learn 은 「두 형태가 같은 IL」까지만 말한다).

## 한눈에 — 쉽게 말하면

**확장 메서드는 「남의 가게 문에 붙인 내 안내판」이다 — 손님은 가게 물건인 줄 알고 집지만, 실제로는 옆 사무실(정적 클래스)로 안내된다.**

- **안내판(`s.Shout()`)** — 수신자 **뒤에 점을 찍어** 부르는 모양. 실제로는 `TextExt.Shout(s)` **정적 호출**이다.
- **가게 물건이 먼저** — 가게에 같은 이름의 물건(인스턴스 메서드)이 있으면 **안내판은 안 본다.**
- **문 앞 간판으로 고른다** — 수신자의 **실제 타입이 아니라 선언된 타입**으로 안내판을 고른다. 가상 호출이 없다.
- **빈 가게여도 안내된다** — 수신자가 `null` 이어도 **사무실로 가는 것은 된다**(인자로 `null` 이 갈 뿐).
- **C# 14 의 `extension` 블록** — 안내판을 **메서드뿐 아니라 속성·정적 멤버·연산자**로도 붙인다. **인덱서는 아직(이 판 preview · C# 15 예정).**

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 안내판 = 정적 호출 | ★★★ `n.Twice()` 와 `Ext.Twice(n)` 의 IL 이 **둘 다 `call Ext::Twice`** | (1) |
| 빈 가게여도 | ★★★ `null` 수신자 확장 → **`True`** · 인스턴스 → **`NullReferenceException`** · `call` 대 `callvirt` | (2) |
| 가게 물건이 먼저 | ★★ `g.Hello()` → **인스턴스** | (3) |
| 문 앞 간판으로 | ★★ `object o = "x"; o.Describe()` → **`Describe(object)`** | (3) |
| 속성 안내판 | ★★★ 확장 속성 `Square` → **`static get_Square(Int32 x)`** | (1) |
| 아직 못 붙이는 것 | ★★★ 인덱서 — 14 `CS8652` · preview **`CS0029`** | (4) |

★★★ **이 주제의 본체 그림 — 점 하나가 무엇으로 바뀌나.**

```text
   소스                                   컴파일러가 만드는 것(IL)
   ─────────────────────────────          ────────────────────────────────────────────
   n.Twice()          (this 확장)          call  Ext::Twice(n)            ← 정적 호출 · 인자 1개
   Ext.Twice(n)       (그냥 정적 호출)      call  Ext::Twice(n)            ← 한 글자도 같다
   n.Thrice()         (extension 블록)      call  Ext::Thrice(n)           ← 블록 메서드도 같은 모양
   n.Square           (확장 속성)           call  Ext::get_Square(n)       ← 속성이 아니라 정적 메서드
   s.GetHashCode()    (인스턴스)            callvirt Object::GetHashCode   ← 수신자 널 검사 + 가상 디스패치

   이름 찾기 순서 — s.M() 을 만나면
     ① s 의 정적 타입에 인스턴스 멤버 M 이 있나 ──있다──▶ 그것 (확장은 안 본다)
     ② 없으면 using 된 정적 클래스의 확장 M 중 s 의 「정적 타입」 에 맞는 것
   ★★★ 실행 시점의 타입은 어디에도 끼지 않는다 — 전부 컴파일 시점에 끝난다.
```

## 이 주제가 답하려는 질문

1. **확장 메서드는 무엇으로 컴파일되나** — `call` · `[Extension]` · 블록 멤버((1)).
2. **정적 메서드라서 생기는 결과는** — `null` 수신자 · 인스턴스 우선 · 정적 타입 선택((2)(3)).
3. **C# 14 는 어디까지 넓혔나** — 멤버 일곱 × 판 셋((4)) · **Java 는**((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ① IL 덤프다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 덤프** | ★★★ `n.Twice()` = `Ext.Twice(n)` = **`call Ext::Twice`** · 확장 속성 = **`call Ext::get_Square`** · 인스턴스 = **`callvirt`** | (1)(2) |
| ★★★ **② 진단(판) 격자** | ★★★ 멤버 일곱 × `-langversion:13`·`14`·`preview` = 21칸 · `CS8023`(C# 2) · javac `cannot find symbol` | (4)(5) |
| ★★ **③ 리플렉션** | ★★ `Ext` 의 메서드가 **전부 `static`** · `[Extension]` 이 `Twice`·`Thrice` 에는 있고 **`get_Square` 에는 없다** · 표지 중첩 타입 `<G>$…` · LINQ `Where` 도 `[Extension]` | (1) |
| **부적용인 창** | ★ **④ 할당 바이트** — 확장 호출은 **정적 호출 한 번**이라 인스턴스 호출과 달리 **할당할 것이 없다**(IL 에 `newobj`·`box` 가 없다 — (1)(2)). **잴 것이 없다**(제4의 상태) | — |

### (1) ★★★ 본체 — 확장 메서드는 정적 메서드다

```text
===== 소스: cs30b-il.cs =====
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
public static class Ext {
    public static int Twice(this int x) => x * 2;
    extension(int x) {
        public int Thrice() => x * 3;
        public int Square => x * x;
    }
}
public static class Use {
    public static int CallSugar(int n) => n.Twice();
    public static int CallPlain(int n) => Ext.Twice(n);
    public static int CallBlock(int n) => n.Thrice() + n.Square;
}
class Program {
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    static void Main() {
        var t = typeof(Ext);
        Console.WriteLine($"Ext : abstract={t.IsAbstract} sealed={t.IsSealed} [Extension]={t.IsDefined(typeof(ExtensionAttribute))}");
        foreach (var m in t.GetMethods(All).OrderBy(m => m.Name, StringComparer.Ordinal))
            Console.WriteLine($"  메서드 {(m.IsStatic ? "static " : "")}{m.ReturnType.Name} {m.Name}({string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name))}) [Extension]={m.IsDefined(typeof(ExtensionAttribute))} specialname={m.IsSpecialName}");
        foreach (var p in t.GetProperties(All))
            Console.WriteLine($"  속성   {p.Name}");
        foreach (var n in t.GetNestedTypes(All).OrderBy(n => n.Name, StringComparer.Ordinal)) {
            Console.WriteLine($"  중첩 타입 {n.Name}");
            foreach (var m in n.GetMembers(All).OrderBy(m => m.Name, StringComparer.Ordinal))
                Console.WriteLine($"    {m.MemberType} {m.Name}");
        }
        Il.Dump(typeof(Use), "CallSugar");
        Il.Dump(typeof(Use), "CallPlain");
        Il.Dump(typeof(Use), "CallBlock");
        Console.WriteLine($"[결과] {Use.CallSugar(5)} {Use.CallPlain(5)} {Use.CallBlock(5)}");
        var where = typeof(Enumerable).GetMethods().Where(m => m.Name == "Where").ToArray();
        Console.WriteLine($"[LINQ] Enumerable.Where 오버로드 {where.Length} 개 · static 인 것 {where.Count(m => m.IsStatic)} · [Extension] 인 것 {where.Count(m => m.IsDefined(typeof(ExtensionAttribute)))} · 첫 매개변수 타입 {where[0].GetParameters()[0].ParameterType.Name}");
    }
}
===== csc -optimize -r:il.dll -out:exo.dll cs30b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
Ext : abstract=True sealed=True [Extension]=True
  메서드 static Int32 Thrice(Int32 x) [Extension]=True specialname=False
  메서드 static Int32 Twice(Int32 x) [Extension]=True specialname=False
  메서드 static Int32 get_Square(Int32 x) [Extension]=False specialname=False
  중첩 타입 <G>$BA41CFE2B5EDAEB8C1B9062F59ED4D69
    NestedType <M>$DE9F57644BDC66EDA3F1FD365749DA9F
    Property Square
    Method Thrice
    Method get_Square
--- Use.CallSugar ---
  IL_0000: ldarg.0
  IL_0001: call Ext::Twice
  IL_0006: ret
--- Use.CallPlain ---
  IL_0000: ldarg.0
  IL_0001: call Ext::Twice
  IL_0006: ret
--- Use.CallBlock ---
  IL_0000: ldarg.0
  IL_0001: call Ext::Thrice
  IL_0006: ldarg.0
  IL_0007: call Ext::get_Square
  IL_000c: add
  IL_000d: ret
[결과] 10 10 40
[LINQ] Enumerable.Where 오버로드 2 개 · static 인 것 2 · [Extension] 인 것 2 · 첫 매개변수 타입 IEnumerable`1
```

- ★★★ **`CallSugar`(`n.Twice()`) 와 `CallPlain`(`Ext.Twice(n)`) 의 IL 이 한 글자도 같다** — `ldarg.0` · **`call Ext::Twice`** · `ret`. 점 찍기는 **소스에만** 있다.
- ★★★ **`Ext` 는 `abstract=True sealed=True`**(= C# 의 `static class`) · **`[Extension]=True`** — 컴파일러가 **「이 클래스에 확장이 있다」** 를 표시한다.
- ★★★ **`extension(int x)` 블록의 `Thrice()` 가 `static Int32 Thrice(Int32 x)` 로** — 수신자 `x` 가 **첫 매개변수**가 됐다. `this` 형 `Twice(Int32 x)` 와 **같은 모양 · 같은 `[Extension]=True`** — Learn 의 「두 형태가 같은 IL」.
- ★★★ **확장 속성 `Square` → `static Int32 get_Square(Int32 x)`** — `Ext` 에는 **속성이 없다**(「속성」 줄이 안 찍혔다). 호출은 **`call Ext::get_Square`**. 그리고 이 메서드에는 **`[Extension]=False` · `specialname=False`** 다.
- ★★ **속성 `Square` 는 표지 중첩 타입 `<G>$BA41…` 안에** 있다 — 거기에 `Thrice` · `get_Square` · `Square` 와 또 하나의 중첩 `<M>$…` 이 있다. **컴파일러가 「원래 선언 모양」을 기록해 두는 자리**로 읽힌다(Roslyn 구현 — 이름의 해시는 근거로 쓰지 않는다).
- ★ **`[LINQ]` `Enumerable.Where` 오버로드 2개가 전부 `static` · `[Extension]`** · 첫 매개변수 `IEnumerable` — LINQ 가 **확장 메서드 묶음**이다([32번](../32-yield-return-iterators-and-deferred-execution/) (6)이 그 게으름을 잰다).

### (2) ★★★ `null` 수신자 — 확장은 안 터진다 · `call` 대 `callvirt`

```text
===== 소스: cs30b-null.cs =====
using System;
public static class Ext {
    public static bool IsBlank(this string? s) => s is null || s.Trim().Length == 0;
}
public static class Probe {
    public static bool ViaExtension(string? s) => s.IsBlank();
    public static int ViaInstance(string? s) => s!.GetHashCode();
}
class Program {
    static void Main() {
        string? s = null;
        try { Console.WriteLine($"[1] s.IsBlank() : {Probe.ViaExtension(s)}"); }
        catch (Exception e) { Console.WriteLine($"[1] s.IsBlank() : {e.GetType().Name}"); }
        try { Console.WriteLine($"[2] s.GetHashCode() : {Probe.ViaInstance(s)}"); }
        catch (Exception e) { Console.WriteLine($"[2] s.GetHashCode() : {e.GetType().Name}"); }
        Il.Dump(typeof(Probe), "ViaExtension");
        Il.Dump(typeof(Probe), "ViaInstance");
    }
}
===== csc -nullable:enable -optimize -r:il.dll -out:exo.dll cs30b-null.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] s.IsBlank() : True
[2] s.GetHashCode() : NullReferenceException
--- Probe.ViaExtension ---
  IL_0000: ldarg.0
  IL_0001: call Ext::IsBlank
  IL_0006: ret
--- Probe.ViaInstance ---
  IL_0000: ldarg.0
  IL_0001: callvirt System.Object::GetHashCode
  IL_0006: ret
```

- ★★★ **`[1]` `s.IsBlank()` → `True`** — `s` 가 `null` 인데 **호출이 성공**했다. 확장 메서드는 `IsBlank(null)` 이라는 **정적 호출**이고, 본문이 `s is null` 을 먼저 봤다.
- ★★★ **`[2]` `s.GetHashCode()` → `NullReferenceException`** — 인스턴스 메서드는 **`callvirt`** 로 불리고, `callvirt` 는 **대상이 `null` 이면 던진다**([16번](../16-inheritance-virtual-override-abstract-sealed-new/) — C# 은 비가상 메서드도 `callvirt` 로 불러 널 검사를 얻는다).
- ★★ **IL 차이는 한 단어다** — `call Ext::IsBlank` 대 `callvirt System.Object::GetHashCode`.

### (3) ★★ 이름이 겹치면 · 정적 타입과 실제 타입이 다르면

```text
===== 소스: cs30b-win.cs =====
using System;
class Greeter {
    public string Hello() => "Greeter.Hello (인스턴스)";
}
static class Ext {
    public static string Hello(this Greeter g) => "Ext.Hello (확장)";
    public static string Describe(this object o) => "Describe(object)";
    public static string Describe(this string s) => "Describe(string)";
}
class Program {
    static void Main() {
        var g = new Greeter();
        Console.WriteLine($"[1] g.Hello()       : {g.Hello()}");
        Console.WriteLine($"[2] Ext.Hello(g)    : {Ext.Hello(g)}");
        string s = "x";
        object o = s;
        Console.WriteLine($"[3] s.Describe()    : {s.Describe()}");
        Console.WriteLine($"[4] o.Describe()    : {o.Describe()}  (o 의 실제 타입 = {o.GetType().Name})");
    }
}
===== csc -out:ex.dll cs30b-win.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] g.Hello()       : Greeter.Hello (인스턴스)
[2] Ext.Hello(g)    : Ext.Hello (확장)
[3] s.Describe()    : Describe(string)
[4] o.Describe()    : Describe(object)  (o 의 실제 타입 = String)
```

- ★★★ **`[1]` 인스턴스가 이긴다** — 같은 이름·같은 모양의 확장이 있어도 `g.Hello()` 는 `Greeter.Hello`. 확장은 **인스턴스 멤버 찾기가 실패했을 때만** 본다. **경고도 없다** — 확장 쪽이 **조용히 죽은 코드**가 된다.
- ★★ **`[2]` 확장을 부르려면 정적 호출로** — `Ext.Hello(g)`.
- ★★★ **`[3]` `s.Describe()` → `Describe(string)` · `[4]` `o.Describe()` → `Describe(object)`**(실제 타입은 `String`) — 확장은 **오버로드 해석**이다. **변수의 선언 타입**으로 고르고, 실행 시점의 타입은 안 본다.

### (4) ★★★ C# 14 확장 멤버 판 격자 — 일곱 × 셋

```text
===== 소스: classic.cs =====
static class E {
    public static int Twice(this int x) => x * 2;
}
class Program { static void Main() { System.Console.WriteLine(3.Twice()); } }
===== 소스: method.cs =====
static class E {
    extension(int x) { public int Twice() => x * 2; }
}
class Program { static void Main() { System.Console.WriteLine(3.Twice()); } }
===== 소스: prop.cs =====
static class E {
    extension(int x) { public int Double => x * 2; }
}
class Program { static void Main() { System.Console.WriteLine(3.Double); } }
===== 소스: smethod.cs =====
static class E {
    extension(int) { public static int Zero() => 0; }
}
class Program { static void Main() { System.Console.WriteLine(int.Zero()); } }
===== 소스: sprop.cs =====
static class E {
    extension(int) { public static int Seven => 7; }
}
class Program { static void Main() { System.Console.WriteLine(int.Seven); } }
===== 소스: oper.cs =====
static class E {
    extension(string) { public static string operator *(string a, int n) => a + n; }
}
class Program { static void Main() { System.Console.WriteLine("a" * 3); } }
===== 소스: indexer.cs =====
static class E {
    extension(int[] a) { public int this[string k] => a[0] + k.Length; }
}
class Program { static void Main() { System.Console.WriteLine(new int[] { 5 }["ab"]); } }
===== 격자 — 파일마다 csc -langversion:{13,14,preview} -out:ex.dll k30/<종류>.cs · 되면 ok=<dotnet ex.dll 의 출력>, 안 되면 진단 코드 =====
kind      C# 13                     C# 14                     preview
classic   ok=6                      ok=6                      ok=6
method    CS1022,CS1513             ok=6                      ok=6
prop      CS1022,CS1513             ok=6                      ok=6
smethod   CS1001,CS1022,CS1513      ok=0                      ok=0
sprop     CS1001,CS1022,CS1513      ok=7                      ok=7
oper      CS1001,CS1022,CS1513      ok=a3                     ok=a3
indexer   CS1022,CS1513             CS8652                    CS0029
된 칸 13 / 21
===== csc -langversion:13 -out:ex.dll k30/prop.cs (cc exit=1) =====
k30/prop.cs(2,24): error CS1513: } expected
k30/prop.cs(3,1): error CS1022: Type or namespace definition, or end-of-file expected
===== csc -langversion:preview -out:ex.dll k30/indexer.cs (cc exit=1) =====
k30/indexer.cs(4,79): error CS0029: Cannot implicitly convert type 'string' to 'int'
===== csc -langversion:2 -out:ex.dll k30/classic.cs (cc exit=1) =====
k30/classic.cs(2,29): error CS8023: Feature 'extension method' is not available in C# 2. Please use language version 3 or greater.
```

- ★★★ **된 칸 13 / 21** — 스크립트가 셌다.
- ★★★ **C# 14 열 — 인덱서만 빼고 여섯이 된다** — 블록의 인스턴스 메서드 · **인스턴스 속성**(`3.Double`) · **정적 메서드**(`int.Zero()`) · **정적 속성**(`int.Seven`) · **연산자**(`"a" * 3` → `a3`). **C# 3 의 `this` 형은 세 판 모두** 된다.
- ★★★ **인덱서 — 14 에서 `CS8652`(「`extension indexers` 는 **Preview**」) · preview 에서 `CS0029`** — preview 는 **선언은 받는데**, `new int[] { 5 }["ab"]` 가 **확장 인덱서를 후보로 안 올리고** 배열의 기본 인덱싱으로 읽어 「`string` → `int` 변환 불가」를 냈다. [14번](../14-indexers/) (7)의 결과와 **같다**. Learn 은 **C# 15** 로 적었다.
- ★★★ **C# 13 열 — 블록 여섯이 전부 파서 에러**(`CS1513 } expected` · `CS1022` · `CS1001`) — **「이 기능은 C# 14 부터」 류(`CS8400`·`CS8652`) 진단이 없다.** `extension` 이 13 에서는 **키워드가 아니라** 이름으로 읽혀 문법이 깨진 것이다. ★ 대조 — `this` 형을 `-langversion:2` 로 던지면 **`CS8023 … use language version 3 or greater`** 로 판을 **정확히** 말해 준다.
- ★ 이 격자는 **판마다 결과가 갈리는 것이 결론**이다(0 이 결론이 아니다) — 대조군은 **C# 2 의 `CS8023`** 이 대신한다.

```text
                    C# 13            C# 14             preview (C# 15 예정)
   this 확장 메서드    ✓                ✓                 ✓          ← C# 3 부터
   블록 인스턴스 메서드  파서 에러          ✓                 ✓
   인스턴스 속성       파서 에러          ✓  get_X(recv)      ✓
   정적 메서드         파서 에러          ✓  T.M()            ✓
   정적 속성          파서 에러          ✓  T.P              ✓
   연산자             파서 에러          ✓  a * n            ✓
   인덱서             파서 에러          CS8652 (preview)   CS0029 — 선언만 되고 호출 후보에 없다
```

### (5) ★★ Java 짝 — 확장 메서드가 없다

```text
===== 소스: Ex30.java =====
final class Strs {
    private Strs() { }
    static String shout(String s) { return s.toUpperCase() + "!"; }
}
public class Ex30 {
    public static void main(String[] args) {
        System.out.println(Strs.shout("hi"));
    }
}
===== javac -d j30out j30/Ex30.java && java -cp j30out Ex30 (cc exit=0 · run exit=0) =====
HI!
===== 소스: G30.java =====
class G30 {
    static String shout(String s) { return s.toUpperCase() + "!"; }
    void f() {
        String r = "hi".shout();
    }
}
===== javac -d j30out j30/G30.java (cc exit=1) =====
j30/G30.java:4: error: cannot find symbol
        String r = "hi".shout();
                       ^
  symbol:   method shout()
  location: class String
1 error
```

- ★★★ **`"hi".shout()` → javac `cannot find symbol` · `symbol: method shout()` · `location: class String`** — 같은 클래스에 `static shout(String)` 이 **있어도** 수신자 문법으로는 못 부른다. Java 는 **메서드를 찾을 때 수신자 타입(`String`)만** 본다.
- ★★ **관용은 정적 유틸 클래스** — `Strs.shout("hi")` → `HI!`. C# 확장 메서드의 **IL 과 같은 모양**(정적 호출 · 첫 인자)을 **소스에 그대로** 쓴 것이다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs30b-form.cs =====
using System;
using System.Collections.Generic;

Console.WriteLine($"{"hello".Shout()} · {"hello".Initial} · {string.Repeat("ab", 3)} · {new[] { 3, 1, 2 }.SumAll()}");

static class TextExt {
    public static string Shout(this string s) => s.ToUpper() + "!";
    extension(string s) {
        public char Initial => s[0];
    }
    extension(string) {
        public static string Repeat(string x, int n) => string.Concat(System.Linq.Enumerable.Repeat(x, n));
    }
    extension<T>(IEnumerable<T> xs) where T : System.Numerics.INumber<T> {
        public T SumAll() { T acc = T.Zero; foreach (var x in xs) acc += x; return acc; }
    }
}
===== csc -out:ex.dll cs30b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
HELLO! · h · ababab · 6
```

- ★★★ **`this` 형** — `public static string Shout(this string s)` — **최상위 비제네릭 `static class`** 안에서만.
- ★★★ **`extension(string s) { … }`** — 이름 있는 수신자. 인스턴스 메서드·**속성**(`Initial`)을 둔다.
- ★★ **`extension(string) { public static … }`** — 이름 없는 수신자. **정적 멤버만**(`string.Repeat("ab", 3)`).
- ★★ **`extension<T>(IEnumerable<T> xs) where T : INumber<T>`** — 수신자의 타입 매개변수와 제약은 **블록에** 둔다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| C# 2 이하에서 `this` 확장 메서드 | `CS8023` | (4) |
| C# 13 이하에서 `extension` 블록 | `CS1513`·`CS1022`·`CS1001`(파서) | (4) |
| C# 14 에서 확장 인덱서 | `CS8652` | (4) · [14번](../14-indexers/) (7) |
| preview 에서 확장 인덱서를 부름 | `CS0029` | (4) · [14번](../14-indexers/) (7) |
| Java 에서 `"hi".shout()` | javac `cannot find symbol` | (5) |
| ★★★ 인스턴스 메서드와 같은 이름의 확장 | ★★★ **진단 없음** — 확장이 안 불린다 | (3) |

## 어디서 틀리나

1. ★★★ **「확장 메서드는 그 타입의 메서드가 된다」** — **정적 메서드**다. 타입은 **아무것도 안 바뀐다**((1) IL).
2. ★★★ **「`null` 에 점을 찍으면 무조건 터진다」** — 확장은 **안 터진다**. 본문이 `null` 을 받는다((2)).
3. ★★★ **「확장으로 기존 메서드를 덮어쓸 수 있다」** — **인스턴스가 이긴다**, 경고 없이((3) `[1]`).
4. ★★★ **「확장도 가상처럼 실제 타입을 따라간다」** — **선언 타입**으로 고른다((3) `[4]`).
5. ★★★ **「C# 14 로 인덱서도 붙인다」** — 이 판은 **preview 에서도 못 부른다**(Learn: C# 15)((4)).
6. ★★ **「C# 13 으로 컴파일하면 『14 를 쓰라』고 알려 준다」** — **파서 에러**만 나온다((4)).
7. ★★ **「확장 속성은 메타데이터에서도 속성이다」** — `Ext` 에는 **정적 메서드 `get_Square(Int32)`** 만 있다. 속성은 **표지 타입 안**에 있다((1)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **확장 메서드 = `this` 첫 매개변수의 정적 메서드 · 호출은 정적 호출** | ★★★ **언어(334)** | (1) |
| **인스턴스 멤버 우선 · 선언 타입으로 고른다** | ★★★ **언어(334)** | (3) |
| **`null` 수신자가 그대로 인자로 간다** | ★★★ **언어의 귀결**(정적 호출이므로) | (2) |
| **`extension` 블록 — 메서드·속성·정적 멤버·연산자(C# 14)** | ★★★ **언어(C# 14)** | (4) |
| **확장 인덱서** | ★★ **언어(C# 15 예정 · Learn)** — 이 판 preview · 호출 불가 | (4) |
| **블록 멤버가 `Ext` 의 정적 메서드 + `<G>$…` 표지 타입** | ★★★ **Roslyn 구현** | (1) |
| **C# 13 이 파서 에러로 막는 것** | ★ **이 판의 관찰** | (4) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **소스를 못 고치는 타입(BCL · 인터페이스)에 동사를 붙일 때** — LINQ 가 그 예다((1) `[LINQ]`).
- ★★★ **인스턴스 메서드와 같은 이름을 짓지 마라** — 조용히 무시된다((3)). 라이브러리가 나중에 같은 이름을 **추가**하면 **내 확장이 조용히 꺼진다.**
- ★★ **`null` 을 받는 확장을 쓸 때는 본문에서 확인해라** — 되는 것(`IsBlank`)이 편하지만, **읽는 사람은 `null.Method()` 가 터질 것으로 기대**한다((2)).
- ★★ **C# 14 확장 속성·정적 확장은 `TargetFramework` 의 언어 판이 14 이상일 때만** — 13 은 파서 에러라 원인이 **판**이라고 안 알려 준다((4)).
- ★ **다형성이 필요하면 확장이 아니라 인터페이스·가상 메서드** — 확장은 **선언 타입**으로 고른다((3) `[4]`).

## 핵심 문장

1. ★★★ **확장 메서드는 정적 메서드의 문법 설탕이다** — `n.Twice()` 와 `Ext.Twice(n)` 은 IL 이 **둘 다 `call Ext::Twice`**((1)).
2. ★★★ **정적 호출이라 `null` 수신자도 불리고(`True`), 인스턴스는 `callvirt` 라 터진다**((2)).
3. ★★★ **인스턴스 멤버가 먼저, 확장은 선언 타입으로** — 가상 디스패치가 없다((3)).
4. ★★★ **C# 14 는 속성·정적 멤버·연산자까지 넓혔다(된 칸 13 / 21) — 인덱서는 이 판 preview 에서도 못 부른다**((4)).
5. ★★ **Java 에는 대응물이 없다** — `"hi".shout()` 는 `cannot find symbol`, 관용은 정적 유틸((5)).

## 관련 자료

- [14번 — 인덱서](../14-indexers/) (7) — **경계**: 확장 인덱서를 먼저 던진 곳(`CS8652` · `CS9303` · preview `CS0029`). 여기는 **확장 멤버 전체의 판 격자**에 그 한 행을 둔다.
- [16번 — 상속](../16-inheritance-virtual-override-abstract-sealed-new/) — `callvirt` 의 널 검사 · 비가상 기본값.
- [27번 — 델리게이트](../27-delegates-and-func-action/) — 정적 메서드 그룹 · README 의 줄기(델리게이트 → 람다 → 확장 → `IEnumerable` → `yield` → LINQ).
- [31번 — `foreach`](../31-ienumerable-and-foreach/) (2) — 확장 메서드 `GetEnumerator` 로 `int` 를 `foreach`(C# 9).
- [32번 — `yield`](../32-yield-return-iterators-and-deferred-execution/) (6) — LINQ 확장 메서드의 게으름.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **29번**([`29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/)) — Java 쪽 함수형 줄기. **확장 메서드에 해당하는 주제는 Java 목록에 없다.**

## 용어 풀이

- **확장 메서드(extension method)** — 첫 매개변수에 `this` 를 붙인 정적 메서드. 수신자 뒤에 점을 찍어 부를 수 있다(C# 3).
- **확장 멤버(extension member)** — C# 14 의 `extension(수신자) { … }` 블록에 둔 메서드·속성·정적 멤버·연산자.
- **수신자(receiver)** — 점 앞의 값. 확장에서는 **첫 인자**가 된다.
- **`ExtensionAttribute`** — 컴파일러가 확장 메서드와 그 클래스에 붙이는 표지. 런타임 동작은 없다.
- **`call` 대 `callvirt`** — 정적·비가상 호출 대 널 검사를 겸한 (가상) 호출 옵코드.
- **선언 타입(정적 타입)** — 변수를 선언한 타입. 실행 시점의 실제 타입과 다를 수 있다.

## 더 들어가면

- ★ **`ref` 수신자 확장**(`this ref int x`) · **구조체 수신자의 복사** — 안 던졌다.
- ★ **확장 멤버 해석 순서가 여러 `using` 사이에서 겹칠 때**(모호성 `CS0121`) — 안 던졌다.
- ★ **`<G>$…` 표지 타입의 정확한 구조** — 리플렉션으로 이름만 봤다. 메타데이터 명세는 **안 읽었다.**
