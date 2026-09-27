# csharp/syntax/26 — 공변·반변 (`out`/`in`) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-335(CLI) 6판](https://ecma-international.org/publications-and-standards/standards/ecma-335/) · [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 제네릭의 공변성과 반공변성](https://learn.microsoft.com/en-us/dotnet/standard/generics/covariance-and-contravariance)(열어서 확인: 「변성 타입 매개변수는 **제네릭 인터페이스와 제네릭 델리게이트에만**」 ·\
> 「변성은 **참조 타입에만** 적용된다 — 변성 매개변수에 **값 타입을 주면 그 구성 타입에서는 불변**이다」 · 「변성은 **델리게이트 결합에는 적용되지 않는다**」 ·\
> 「기본적으로 제네릭 타입 매개변수는 **불변** — `List<Derived>` 와 `List<Base>` 는 **관계가 없다**」) ·
> [Learn — C# 버전 이력](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-version-history)(열어서 확인: C# 4.0 「**Generic covariant and contravariant**」).
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. **대비는 실측이다** — **javac 21.0.5** 로 배열 공변 한 쌍과 불변 제네릭 하나를 던졌다((3)).
> **버전** — 인터페이스·델리게이트 변성 **C# 4 / .NET Framework 4** — ★ `-langversion:3` 으로 던져 **`CS8024 … version 4 or greater`** 를 받았다((6)). **배열 공변은 C# 1 부터**(CLI 에 처음부터 있다).
> **경계** — ★★★ **변성 위반 검사**(`out T` 를 인자 자리에 쓰면 `CS1961` · 클래스에 `out` 을 달면 `CS1960`)는 **Kotlin 28편이 C# 으로 직접 던졌다** — [Kotlin 28번](../../../kotlin/syntax/28-generics-variance-in-out-star-where/) 의 `variance28.cs` 블록을 인용하고 **다시 재지 않는다.**\
> ★ **Java 와일드카드·PECS 의 정본**은 [Java 18번](../../../java/syntax/18-wildcards-pecs/) · **제네릭이 런타임까지 남는 것**은 [24번](../24-generics-and-type-parameters/) · **제약**은 [25번](../25-generic-constraints-where-and-default/) · **델리게이트 자체**는 [27번](../27-delegates-and-func-action/).
> ★★★ **본체 창은 ② 진단 격자다** — 변환 16개를 한 파일에 적어 **스크립트가 진단의 줄 번호로 행을 되돌려 「막힌 칸 N / M」을 센다.**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 진단 **순서**(배너에 `sort`) · 예외 **메시지** | ★★★ **진단 코드**(`CS0029` 대 `CS0266`) · **`cc exit`** · 예외 **타입** |
> | **IL 오프셋 폭** | ★★★ **옵코드**(변환 자리에 **명령 없음** · `stelem.ref` · `castclass`) |
> | — | ★★★ **「막힌 칸 N / M」**(스크립트가 센 마지막 줄) · 리플렉션 **`Covariant`/`Contravariant`/`None`** |

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
| **CLI 명세(ECMA-335)** | ★★★ **실행 엔진이 약속한 것** | ★★★ **변성은 타입 매개변수의 메타데이터 플래그**(`+`/`-`)이고, **런타임의 `is`·`IsAssignableFrom`·캐스트가 그 플래그를 따른다** · ★★★ **배열 공변과 저장 시 런타임 검사**도 CLI 가 보장한다 |
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | `out`/`in` 은 **인터페이스·델리게이트에만** · 변성 **안전성 검사**(`CS1961`) · **암시적 참조 변환**의 규칙 |
| **컴파일러 구현(Roslyn)** | 그것을 **어떻게 적나** | 공변 변환 자리에 **IL 명령을 하나도 안 낸다** · 명시적 캐스트는 `castclass` |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 진단 문구 · 예외 메시지 |

★★★ **이 주제의 층 구분 —**\
**제네릭 변성과 배열 공변은 둘 다 CLI 명세**다. 차이는 **「언제 막느냐」** 다 — 제네릭 변성은 **안전한 방향만 컴파일러가 허락**하고, 배열 공변은 **전부 허락한 뒤 런타임이 저장마다 검사**한다.

## 한눈에 — 쉽게 말하면

**「사과 상자를 과일 상자로 불러도 되나」는 그 상자로 무엇을 하느냐에 달렸다.**

- **꺼내기만 하는 상자**(`IEnumerable<out T>`) — 사과 상자를 **과일 상자라고 불러도 안전**하다. 꺼내면 늘 과일(사과)이 나온다 → **공변(`out`)**.
- **넣기만 하는 구멍**(`Action<in T>`) — **과일 아무거나 넣을 수 있는 구멍**을 「사과 넣는 구멍」이라 불러도 안전하다. 사과를 넣으면 과일이니까 → **반변(`in`)**.
- **넣고 꺼내는 상자**(`IList<T>`) — 사과 상자를 과일 상자라 부르면 **누가 바나나를 넣는다** → 그래서 **불변**이다.
- **배열**(`string[]`)은 **넣고 꺼내는데도 과일 상자라고 부르게 해 준다** — 대신 **넣을 때마다 경비가 검사**한다(`ArrayTypeMismatchException`). **Java 배열도 똑같다**(`ArrayStoreException`).
- **값 과자**(`int`)는 **상자째 과일 상자가 못 된다** — 과일 상자는 「포장된 과자(참조)」만 담는데 `int` 는 포장이 없다(박싱이 필요하다).

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 꺼내기만 하면 안전 | ★★★ `IEnumerable<string>` → `IEnumerable<object>` **ok** · `Func<string>` → `Func<object>` **ok** | (1) |
| 넣기만 하면 반대로 안전 | ★★★ `Action<object>` → `Action<string>` **ok** · `IComparer<object>` → `IComparer<string>` **ok** | (1) |
| 넣고 꺼내면 불변 | ★★★ `IList<string>` → `IList<object>` **`CS0266`** · `List<>` 는 **`CS0029`** | (1) |
| 배열은 경비가 막는다 | ★★★ `object[] objs = new string[2]; objs[1] = 42;` → **`ArrayTypeMismatchException`** · Java **`ArrayStoreException`** | (2)(3) |
| 값 과자는 안 된다 | ★★★ `IEnumerable<int>` → `IEnumerable<object>` **`CS0266`** · `int[]` → `object[]` **`CS0029`** | (1) |

★★★ **이 주제의 본체 그림 — 변환 16칸이 어디서 막히나.**

```text
                                     변성(C# 4)           결과        막는 곳
   IEnumerable<string> → <object>     out T              ok          —
   IReadOnlyList<string> → <object>   out T              ok          —
   List<string> → IEnumerable<object> 구현 + out T        ok          —
   Func<string> → Func<object>        out TResult        ok          —
   Action<object> → Action<string>    in T               ok          —
   IComparer<object> → <string>       in T               ok          —
   Func<object,string> → <string,object>  in · out       ok          —
   string[] → object[]                배열 공변(C# 1)      ok  ★      런타임(저장할 때마다)
   ─────────────────────────────────────────────────────────────────────────────────
   IList<string> → IList<object>      불변               CS0266      컴파일러
   IBox<string> → IBox<object>        불변(내 인터페이스)   CS0266      컴파일러
   Func<object> → Func<string>        방향이 거꾸로        CS0266      컴파일러
   Action<string> → Action<object>    방향이 거꾸로        CS0266      컴파일러
   IEnumerable<int> → <object>        값 타입              CS0266      컴파일러
   List<string> → List<object>        클래스는 불변         CS0029      컴파일러
   int[] → object[]                   값 타입 배열          CS0029      컴파일러
   Func<int> → Func<object>           값 타입              CS0029      컴파일러

   ★★★ CS0266 = 「명시적 변환은 있다」(캐스트하면 컴파일은 된다 → 런타임에 InvalidCastException((2)))
       CS0029 = 「변환 자체가 없다」(클래스·값 타입 — 캐스트로도 못 간다)
```

## 이 주제가 답하려는 질문

1. **어떤 변환이 되고 어떤 것이 막히나** — 16칸 격자((1)).
2. **배열은 왜 되고, 되면 무엇이 대신 막나** — C# 대 Java 한 쌍((2)(3)).
3. **변환하면 무엇이 일어나나** — IL·객체 동일성((4)(5)).
4. **변성은 어디에 적혀 있고 누가 지키나** — 메타데이터 플래그와 런타임 검사((5)).
5. **내 인터페이스에 `out`/`in` 을 달면**((6)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ② 진단 격자다** — 「이 변환이 되나」는 **컴파일러에게 물어서** 답한다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **② 진단 격자** | ★★★ **변환 16칸** — `CS0029`·`CS0266`·`ok` 를 스크립트가 센다 · **C# 3 판 격자**(`CS8024`) · Java `incompatible types` | (1)(3)(6) |
| ★★★ **③ 리플렉션** | ★★★ **`GenericParameterAttributes` 의 `Covariant`/`Contravariant`** · 런타임 `is`·`IsAssignableFrom` 이 변성을 따르나 · **변환 뒤 같은 객체인가** | (5) |
| ★★ **① IL 덤프** | ★★ **공변 변환은 명령이 없다**(`ldarg.0` · `ret`) · 배열 저장 **`stelem.ref`** · 명시적 캐스트 **`castclass`** | (4) |
| ★★ **실행 로그(예외)** | ★★ **컴파일러가 통과시키고 런타임이 막는 자리** — `ArrayTypeMismatchException` · `InvalidCastException` | (2) |
| **부적용인 창** | ★★★ **④ 할당 바이트 — 잴 것이 없다**(제4의 상태). 변환 자리에 IL 이 **한 줄도 없고**((4)) 변환 뒤 **같은 객체**다((5) [C] `True`). 할당이 일어날 자리가 **없다** | — |

### (1) ★★★ 본체 — 변환 16칸

**언제 쓰나** — 「`List<string>` 을 `IEnumerable<object>` 자리에 넘길 수 있나」를 **한 표로** 답할 때.

```text
===== 소스: cs26b-grid.cs =====
using System;
using System.Collections.Generic;
interface IBox<T> { T Get(); }
static class V {
    static void R1(IEnumerable<string> x) { IEnumerable<object> y = x; }
    static void R2(IReadOnlyList<string> x) { IReadOnlyList<object> y = x; }
    static void R3(IList<string> x) { IList<object> y = x; }
    static void R4(List<string> x) { List<object> y = x; }
    static void R5(List<string> x) { IEnumerable<object> y = x; }
    static void R6(IBox<string> x) { IBox<object> y = x; }
    static void R7(Func<string> x) { Func<object> y = x; }
    static void R8(Func<object> x) { Func<string> y = x; }
    static void R9(Action<object> x) { Action<string> y = x; }
    static void R10(Action<string> x) { Action<object> y = x; }
    static void R11(IComparer<object> x) { IComparer<string> y = x; }
    static void R12(Func<object, string> x) { Func<string, object> y = x; }
    static void R13(string[] x) { object[] y = x; }
    static void R14(int[] x) { object[] y = x; }
    static void R15(IEnumerable<int> x) { IEnumerable<object> y = x; }
    static void R16(Func<int> x) { Func<object> y = x; }
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs26b-grid.cs 2>&1 | sort (cc exit=1) =====
cs26b-grid.cs(10,55): error CS0266: Cannot implicitly convert type 'IBox<string>' to 'IBox<object>'. An explicit conversion exists (are you missing a cast?)
cs26b-grid.cs(12,55): error CS0266: Cannot implicitly convert type 'System.Func<object>' to 'System.Func<string>'. An explicit conversion exists (are you missing a cast?)
cs26b-grid.cs(14,60): error CS0266: Cannot implicitly convert type 'System.Action<string>' to 'System.Action<object>'. An explicit conversion exists (are you missing a cast?)
cs26b-grid.cs(18,45): error CS0029: Cannot implicitly convert type 'int[]' to 'object[]'
cs26b-grid.cs(19,67): error CS0266: Cannot implicitly convert type 'System.Collections.Generic.IEnumerable<int>' to 'System.Collections.Generic.IEnumerable<object>'. An explicit conversion exists (are you missing a cast?)
cs26b-grid.cs(20,53): error CS0029: Cannot implicitly convert type 'System.Func<int>' to 'System.Func<object>'
cs26b-grid.cs(7,57): error CS0266: Cannot implicitly convert type 'System.Collections.Generic.IList<string>' to 'System.Collections.Generic.IList<object>'. An explicit conversion exists (are you missing a cast?)
cs26b-grid.cs(8,55): error CS0029: Cannot implicitly convert type 'System.Collections.Generic.List<string>' to 'System.Collections.Generic.List<object>'
===== 격자 — 위 진단을 줄 번호로 행에 되돌린 표 (행;원래 → 대상;결과) =====
1  ;IEnumerable<string>        → IEnumerable<object>       ;ok
2  ;IReadOnlyList<string>      → IReadOnlyList<object>     ;ok
3  ;IList<string>              → IList<object>             ;CS0266
4  ;List<string>               → List<object>              ;CS0029
5  ;List<string>               → IEnumerable<object>       ;ok
6  ;IBox<string>               → IBox<object>              ;CS0266
7  ;Func<string>               → Func<object>              ;ok
8  ;Func<object>               → Func<string>              ;CS0266
9  ;Action<object>             → Action<string>            ;ok
10 ;Action<string>             → Action<object>            ;CS0266
11 ;IComparer<object>          → IComparer<string>         ;ok
12 ;Func<object, string>       → Func<string, object>      ;ok
13 ;string[]                   → object[]                  ;ok
14 ;int[]                      → object[]                  ;CS0029
15 ;IEnumerable<int>           → IEnumerable<object>       ;CS0266
16 ;Func<int>                  → Func<object>              ;CS0029
막힌 칸 8 / 16
```

- ★★★ **막힌 칸 8 / 16** — 스크립트가 진단의 **줄 번호로** 행을 되돌렸다.
- ★★★ **통과 8칸은 전부 「안전한 방향」** — `out` 자리(`IEnumerable`·`IReadOnlyList`·`Func` 의 결과)는 **더 넓은 쪽으로**, `in` 자리(`Action`·`IComparer`·`Func` 의 인자)는 **더 좁은 쪽으로**. **12행 `Func<object, string>` → `Func<string, object>`** 는 **두 방향을 한 번에** 쓴다.
- ★★★ **`IList<string>` → `IList<object>` 는 `CS0266`** — `IList<T>` 는 `T` 를 **넣고(`Add`) 꺼낸다(`this[i]`)** — 불변이다. `IReadOnlyList<T>` 는 **꺼내기만** 해서 `out T` 이고 통과한다(2행).
- ★★★ **`CS0266` 과 `CS0029` 가 갈린다** — **인터페이스·델리게이트 사이는 「명시적 변환은 있다」(`CS0266`)**, **클래스(`List<>`)·값 타입 인자·값 타입 배열은 「변환이 없다」(`CS0029`)**.
- ★★★ **15·16행 — 값 타입 인자에는 변성이 안 먹는다** — `IEnumerable<int>` → `IEnumerable<object>` 는 `CS0266`, `Func<int>` → `Func<object>` 는 `CS0029`. `string` 은 참조라 **그대로 `object` 로 읽히지만** `int` 는 **박싱을 거쳐야** `object` 가 된다 — 변성 변환은 **표현을 안 바꾸는 변환**이라 박싱을 끼워 넣지 않는다(Learn: 「변성은 **참조 타입에만**」).
- ★★ **6행 내 인터페이스 `IBox<T>` 는 `out` 을 안 달아 불변** — `T Get()` 만 있어 공변이 **될 수 있는데도** 선언이 없으면 안 된다. 변성은 **추론되지 않는다** — **선언 지점에 적어야** 한다((6)).

### (2) ★★★ 컴파일러가 통과시킨 뒤 런타임이 막는 자리

**언제 쓰나** — 「배열은 공변인데 무엇이 안전을 지키나」 · 「`CS0266` 에 캐스트를 붙이면 어떻게 되나」.

```text
===== 소스: cs26b-array.cs =====
using System;
using System.Collections.Generic;
class Program {
    static void Run(string label, Action a) {
        try { a(); Console.WriteLine($"{label} → 예외 없음"); }
        catch (Exception e) { Console.WriteLine($"{label} → {e.GetType().FullName}: {e.Message}"); }
    }
    static void Main() {
        object[] objs = new string[2];
        Console.WriteLine($"[0] objs 의 실제 타입 : {objs.GetType()}");
        Run("[1] objs[0] = \"text\"", () => objs[0] = "text");
        Run("[2] objs[1] = 42    ", () => objs[1] = 42);
        Run("[3] objs[1] = null  ", () => objs[1] = null!);
        IList<string> ls = new List<string>();
        Run("[4] (IList<object>)ls", () => { IList<object> lo = (IList<object>)ls; });
        IEnumerable<int> ei = new List<int> { 1 };
        Run("[5] (IEnumerable<object>)ei", () => { IEnumerable<object> eo = (IEnumerable<object>)ei; });
        Action<string> say = s => Console.WriteLine(s);
        Run("[6] (Action<object>)say", () => { Action<object> ao = (Action<object>)say; });
    }
}
===== csc -out:ex.dll cs26b-array.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[0] objs 의 실제 타입 : System.String[]
[1] objs[0] = "text" → 예외 없음
[2] objs[1] = 42     → System.ArrayTypeMismatchException: Attempted to access an element as a type incompatible with the array.
[3] objs[1] = null   → 예외 없음
[4] (IList<object>)ls → System.InvalidCastException: Unable to cast object of type 'System.Collections.Generic.List`1[System.String]' to type 'System.Collections.Generic.IList`1[System.Object]'.
[5] (IEnumerable<object>)ei → System.InvalidCastException: Unable to cast object of type 'System.Collections.Generic.List`1[System.Int32]' to type 'System.Collections.Generic.IEnumerable`1[System.Object]'.
[6] (Action<object>)say → System.InvalidCastException: Unable to cast object of type 'System.Action`1[System.String]' to type 'System.Action`1[System.Object]'.
```

- ★★★ **`[0]` `object[]` 변수 안의 실제 타입은 `System.String[]`** — 배열 공변은 **같은 배열을 다른 이름으로 부르는 것**이다.
- ★★★ **`[2]` `objs[1] = 42` → `System.ArrayTypeMismatchException`** — 컴파일러는 `object[]` 에 `int`(박싱된 `object`)를 넣는 것을 **막을 수 없다**(정적 타입으로는 합법이다). **런타임이 저장할 때마다 실제 원소 타입을 검사**해 막는다.
- ★★ **`[1]` `"text"` 와 `[3]` `null` 은 예외 없음** — `null` 은 **어느 참조 배열에나** 들어간다.
- ★★★ **`[4]`\~`[6]` `CS0266` 자리에 캐스트를 붙이면 컴파일은 되고 런타임에 `InvalidCastException`** — `(IList<object>)ls` · `(IEnumerable<object>)ei`(값 타입) · `(Action<object>)say`(방향이 거꾸로). 「명시적 변환이 있다」는 **「런타임에 확인하겠다」** 는 뜻이다.

```text
   컴파일러가 막는 자리 대 런타임이 막는 자리

   IList<object> lo = ls;            ── 컴파일러 ✕ CS0266
   IList<object> lo = (IList<object>)ls;  ── 컴파일러 ○ ─▶ 런타임 castclass ✕ InvalidCastException
   object[] objs = new string[2];    ── 컴파일러 ○ (배열 공변)
   objs[1] = 42;                     ── 컴파일러 ○ ─▶ 런타임 stelem.ref ✕ ArrayTypeMismatchException

   ★★★ 제네릭 변성은 「안전한 것만 허락」해 런타임 검사가 필요 없다.
       배열 공변은 「일단 허락」하고 저장할 때마다 값을 치른다 — 1행 차이가 설계 차이다.
```

### (3) ★★★ Java 짝 — 배열은 같고, 제네릭은 선언 지점 변성이 없다

```text
===== 소스: Ex26.java =====
public class Ex26 {
    static void run(String label, Runnable r) {
        try { r.run(); System.out.println(label + " → 예외 없음"); }
        catch (Exception e) { System.out.println(label + " → " + e.getClass().getName() + ": " + e.getMessage()); }
    }
    public static void main(String[] a) {
        Object[] objs = new String[2];
        System.out.println("[0] objs 의 실제 타입 : " + objs.getClass().getName());
        run("[1] objs[0] = \"text\"", () -> objs[0] = "text");
        run("[2] objs[1] = 42    ", () -> objs[1] = 42);
        run("[3] objs[1] = null  ", () -> objs[1] = null);
    }
}
===== javac -d j26out j26/Ex26.java && java -cp j26out Ex26 (cc exit=0 · run exit=0) =====
[0] objs 의 실제 타입 : [Ljava.lang.String;
[1] objs[0] = "text" → 예외 없음
[2] objs[1] = 42     → java.lang.ArrayStoreException: java.lang.Integer
[3] objs[1] = null   → 예외 없음
===== 소스: G26.java =====
import java.util.ArrayList;
import java.util.List;
class G26 {
    void f() {
        List<String> ls = new ArrayList<>();
        List<Object> lo = ls;
        List<? extends Object> le = ls;
    }
}
===== javac -d j26out j26/G26.java (cc exit=1) =====
j26/G26.java:6: error: incompatible types: List<String> cannot be converted to List<Object>
        List<Object> lo = ls;
                          ^
1 error
```

- ★★★ **Java 도 `Object[] objs = new String[2]` 가 되고 `objs[1] = 42` 가 `java.lang.ArrayStoreException: java.lang.Integer`** — **이름만 다르고 모양이 같다.** 두 언어가 **같은 시대의 같은 선택**(배열 공변 + 저장 검사)을 했다. [Java 18번](../../../java/syntax/18-wildcards-pecs/)이 같은 예외를 `aastore` 명령의 검사로 정리했다.
- ★★★ **`List<Object> lo = ls` 는 javac `incompatible types`** — Java 제네릭도 **불변**이다. 대신 **쓰는 자리에서** `List<? extends Object>` 로 공변을 **그때그때** 얻는다(**사용 지점 변성** — 7행이 통과했다).
- ★★ **C# 은 반대로 선언 지점 변성**이다 — `IEnumerable<out T>` 를 **라이브러리가 한 번** 선언하면 쓰는 쪽은 아무것도 안 적는다. **C# 에는 와일드카드가 없다.**

```text
                     배열 공변            제네릭 변성은 어디에 적나           클래스에도 되나
   C#               ○ ArrayTypeMismatch   선언 지점 — interface I<out T>      ✕ (인터페이스·델리게이트만 · CS1960)
   Java             ○ ArrayStoreException 사용 지점 — List<? extends T>       ○ (쓰는 자리라 타입 종류 무관)
   Kotlin           ✕ (Array<T> 는 무공변)  선언 지점 + 사용 지점 둘 다          ○ class Box<out T>

   ★ Kotlin 칸은 Kotlin 28편 인용((4)의 「Array<T> 는 무공변」) — 그 편이 C# 의 CS1960 · CS1961 도 직접 던졌다.
```

### (4) ★★ IL — 공변 변환은 명령이 없다

```text
===== 소스: cs26b-il.cs =====
using System;
using System.Collections.Generic;
public static class P {
    public static IEnumerable<object> Up(IEnumerable<string> s) => s;
    public static Action<string> Down(Action<object> a) => a;
    public static object[] Arr(string[] s) => s;
    public static void Store(object[] a, object v) { a[0] = v; }
    public static IList<object> Cast(IList<string> s) => (IList<object>)s;
}
class Program {
    static void Main() {
        foreach (var n in new[] { "Up", "Down", "Arr", "Store", "Cast" }) Il.Dump(typeof(P), n);
    }
}
===== csc -optimize -r:il.dll -out:exo.dll cs26b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- P.Up ---
  IL_0000: ldarg.0
  IL_0001: ret
--- P.Down ---
  IL_0000: ldarg.0
  IL_0001: ret
--- P.Arr ---
  .locals [0] System.Object[]
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldloc.0
  IL_0003: ret
--- P.Store ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.0
  IL_0002: ldarg.1
  IL_0003: stelem.ref
  IL_0004: ret
--- P.Cast ---
  IL_0000: ldarg.0
  IL_0001: castclass System.Collections.Generic.IList<System.Object>
  IL_0006: ret
```

- ★★★ **`Up`(`IEnumerable<string>` → `IEnumerable<object>`)은 `ldarg.0` · `ret`** — **변환 명령이 없다.** 같은 참조를 그대로 돌려준다. `Down`(`Action<object>` → `Action<string>`)도 같다.
- ★★★ **`Arr`(`string[]` → `object[]`)도 명령이 없다** — 배열 공변 역시 **참조 그대로**다.
- ★★★ **`Store` 는 `stelem.ref`** — 이 명령이 (2)의 **`ArrayTypeMismatchException` 을 던지는 자리**다. 원소 타입 검사가 **명령에 들어 있다**(ECMA-335).
- ★★ **`Cast` 는 `castclass IList<object>`** — (2) [4] 의 `InvalidCastException` 이 여기서 난다.

### (5) ★★★ 리플렉션 — 변성은 메타데이터 플래그, 런타임도 그 플래그를 따른다

```text
===== 소스: cs26b-refl.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static string Var(Type g) => string.Join(" , ", g.GetGenericArguments().Select(p => $"{p.Name}:{p.GenericParameterAttributes & System.Reflection.GenericParameterAttributes.VarianceMask}"));
    static void Main() {
        foreach (var g in new[] { typeof(IEnumerable<>), typeof(IReadOnlyList<>), typeof(IList<>), typeof(List<>), typeof(IComparer<>), typeof(Func<>), typeof(Action<>), typeof(Func<,>) })
            Console.WriteLine($"[A] {g.Name,-18} {Var(g)}");
        object o = new List<string> { "a" };
        Console.WriteLine($"[B1] List<string> is IEnumerable<object> : {o is IEnumerable<object>}");
        Console.WriteLine($"[B2] List<string> is IList<object>       : {o is IList<object>}");
        object oi = new List<int> { 1 };
        Console.WriteLine($"[B3] List<int>    is IEnumerable<object> : {oi is IEnumerable<object>}");
        Console.WriteLine($"[B4] IsAssignableFrom Func<object> ← Func<string> : {typeof(Func<object>).IsAssignableFrom(typeof(Func<string>))}");
        Console.WriteLine($"[B5] IsAssignableFrom Func<object> ← Func<int>    : {typeof(Func<object>).IsAssignableFrom(typeof(Func<int>))}");
        var s = new List<string> { "a" };
        IEnumerable<object> up = s;
        Console.WriteLine($"[C] 변환 뒤 같은 객체인가 : {ReferenceEquals(up, s)} · up.GetType() = {up.GetType().Name}");
    }
}
===== csc -out:ex.dll cs26b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[A] IEnumerable`1      T:Covariant
[A] IReadOnlyList`1    T:Covariant
[A] IList`1            T:None
[A] List`1             T:None
[A] IComparer`1        T:Contravariant
[A] Func`1             TResult:Covariant
[A] Action`1           T:Contravariant
[A] Func`2             T:Contravariant , TResult:Covariant
[B1] List<string> is IEnumerable<object> : True
[B2] List<string> is IList<object>       : False
[B3] List<int>    is IEnumerable<object> : False
[B4] IsAssignableFrom Func<object> ← Func<string> : True
[B5] IsAssignableFrom Func<object> ← Func<int>    : False
[C] 변환 뒤 같은 객체인가 : True · up.GetType() = List`1
```

- ★★★ **[A] ``IEnumerable`1`` `T:Covariant` · ``IReadOnlyList`1`` `Covariant` · ``IList`1`` `None` · ``List`1`` `None` · ``IComparer`1`` `Contravariant` · ``Func`1`` `TResult:Covariant` · ``Action`1`` `Contravariant` · ``Func`2`` `T:Contravariant , TResult:Covariant`** — 변성은 **타입 매개변수에 붙은 플래그**다.
- ★★★ **[B1] 런타임 `is` 도 변성을 안다** — `object` 로 받은 `List<string>` 이 `is IEnumerable<object>` → **`True`**. 컴파일 시점의 변환 규칙이 아니라 **CLI 의 타입 검사 규칙**이다.
- ★★★ **[B2] `is IList<object>` 는 `False` · [B3] `List<int>` 는 `is IEnumerable<object>` 가 `False` · [B5] `Func<int>` 도 `False`** — 값 타입 불변이 **런타임에서도** 같다.
- ★★★ **[C] 변환 뒤 `ReferenceEquals(up, s)` 가 `True`** — 포장을 새로 만들지 않는다. **④ 할당 바이트 창이 부적용인 근거**다.

> **어느 층인가** — ★★★ **변성 플래그와 그것을 따르는 런타임 캐스트·`is` 는 ECMA-335** 다. 그래서 **C# 이 아닌 언어로 만든 어셈블리**도 같은 규칙을 따른다.\
> ★★ **C# 이 더하는 것**은 **「선언이 안전한가」 검사**(`CS1961`)와 **「인터페이스·델리게이트에만」**(`CS1960`)이다 — Kotlin 28편의 `variance28.cs` 블록이 두 진단을 직접 받았다: `CS1960` 「`Only interface and delegate type parameters can be specified as variant.`」 · `CS1961` 「`… must be contravariantly valid on 'IBad<T>.Push(T)'. 'T' is covariant.`」.

### (6) ★★ 내가 선언하는 변성 — 그리고 C# 3 판

```text
===== 소스: cs26b-decl.cs =====
using System;
interface ISource<out T> { T Get(); }
interface ISink<in T> { void Put(T x); }
delegate TR Map<in TA, out TR>(TA a);
class Text : ISource<string>, ISink<object> {
    public string Get() => "hello";
    public void Put(object x) => Console.WriteLine($"Put({x})");
}
class Program {
    static void Main() {
        var t = new Text();
        ISource<object> src = t;
        ISink<string> sink = t;
        Map<object, string> m1 = o => $"<{o}>";
        Map<string, object> m2 = m1;
        Console.WriteLine(src.Get());
        sink.Put("world");
        Console.WriteLine(m2("x"));
    }
}
===== csc -out:ex.dll cs26b-decl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
hello
Put(world)
<x>
===== csc -langversion:3 -out:ex.dll cs26b-decl.cs 2>&1 | sort (cc exit=1) =====
cs26b-decl.cs(2,19): error CS8024: Feature 'type variance' is not available in C# 3. Please use language version 4 or greater.
cs26b-decl.cs(3,17): error CS8024: Feature 'type variance' is not available in C# 3. Please use language version 4 or greater.
cs26b-decl.cs(4,17): error CS8024: Feature 'type variance' is not available in C# 3. Please use language version 4 or greater.
cs26b-decl.cs(4,24): error CS8024: Feature 'type variance' is not available in C# 3. Please use language version 4 or greater.
```

- ★★★ **`ISource<out T>` · `ISink<in T>` · `delegate TR Map<in TA, out TR>`** — `Text` 하나가 `ISource<string>` 을 구현하면 **`ISource<object>` 로**, `ISink<object>` 를 구현하면 **`ISink<string>` 으로** 쓰인다. 델리게이트 `Map<object,string>` 이 `Map<string,object>` 로 간다.
- ★★★ **`-langversion:3` 은 `out`·`in` 네 곳에 전부 `CS8024 … Feature 'type variance' is not available in C# 3. Please use language version 4 or greater.`** — **변성은 C# 4** 다.
- ★ 위반(`out T` 를 인자 자리에)은 **`CS1961`** — (5)의 인용으로 대신한다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs26b-form.cs =====
using System;
using System.Collections.Generic;

IEnumerable<string> names = new List<string> { "kim", "lee" };
PrintAll(names);
Action<object> log = o => Console.Write($"[{o}]");
Action<string> logText = log;
logText("x");
Console.WriteLine();
Func<string> make = () => "made";
Func<object> makeObj = make;
Console.WriteLine(makeObj());

static void PrintAll(IEnumerable<object> xs) { foreach (var x in xs) Console.Write($"{x} "); Console.WriteLine(); }
===== csc -out:ex.dll cs26b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
kim lee 
[x]
made
```

- ★★★ **`IEnumerable<object>` 매개변수에 `IEnumerable<string>` 을 그대로** — 공변이 **호출자 쪽 코드를 한 글자도 안 늘린다.**
- ★★ **`Action<object>` 를 `Action<string>` 자리에** — 「무엇이든 받는 처리기」를 **좁은 자리에 재사용**한다(반변).
- ★★ **선언은 `interface I<out T>` · `interface I<in T>` · `delegate R D<in A, out R>(A a)`** — `out T` 는 **반환 자리만**, `in T` 는 **인자 자리만**.
- ★ **클래스·구조체에는 못 단다**(`CS1960` — Kotlin 28편 인용).

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| 불변 인터페이스·거꾸로 된 방향·값 타입 인자(인터페이스·델리게이트) | `CS0266` | (1) |
| 클래스 `List<string>` → `List<object>` · `int[]` → `object[]` · `Func<int>` → `Func<object>` | `CS0029` | (1) |
| `out T` 를 인자 자리에 | `CS1961` | Kotlin 28편 인용 |
| 클래스에 `out`/`in` | `CS1960` | Kotlin 28편 인용 |
| C# 3 판에서 `out`/`in` | `CS8024` | (6) |
| ★★★ `object[] objs = new string[n]; objs[i] = 42;` | ★★★ **진단 없음** — 런타임 `ArrayTypeMismatchException` | (2) |

## 어디서 틀리나

1. ★★★ **「`string` 이 `object` 니까 `IList<string>` 도 `IList<object>`」** — **넣고 꺼내면 불변**이다(`CS0266`). 꺼내기만 하는 `IReadOnlyList<T>` 는 된다((1)).
2. ★★★ **「배열도 제네릭처럼 컴파일러가 지켜 준다」** — 배열 공변은 **런타임이 저장마다 막는다**(`ArrayTypeMismatchException`). 경고도 없다((2)).
3. ★★★ **「`IEnumerable<int>` 도 `IEnumerable<object>` 로 간다」** — **값 타입 인자에는 변성이 없다**((1) 15·16행 · (5) [B3]).
4. ★★ **「`CS0266` 이면 캐스트를 붙이면 된다」** — 컴파일만 된다. 실제 객체가 그 인터페이스가 아니면 **`InvalidCastException`**((2) [4]\~[6]).
5. ★★ **「공변 변환은 감싸는 객체를 만든다」** — **같은 참조**다. IL 에 명령도 없다((4)(5) [C]).
6. ★★ **「`out` 을 안 달아도 반환만 하면 공변이다」** — **선언해야** 한다(`IBox<T>` 가 `CS0266`)((1) 6행).
7. ★★ **「C# 에도 `? extends` 같은 것이 있다」** — 없다. **선언 지점 변성**뿐이다((3)).
8. ★ **「변성은 C# 컴파일러만 아는 것」** — **CLI 플래그**라 런타임 `is` 가 따른다((5) [B1]).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **변성 플래그 · 런타임 `is`/캐스트가 변성을 따른다** | ★★★ **CLI 명세(ECMA-335)** | (5) |
| **배열 공변 · 저장 시 원소 타입 검사(`stelem.ref`)** | ★★★ **CLI 명세** | (2)(4) |
| **값 타입 인자는 불변** | ★★★ **CLI 명세**(Learn 「참조 타입에만」) | (1)(5) |
| **`out`/`in` 은 인터페이스·델리게이트에만 · 안전성 검사** | ★★★ **언어(334)** | (6) · Kotlin 28편 |
| **공변 변환 자리에 IL 명령이 없다** | ★★ **Roslyn 구현**(참조 그대로가 뜻의 귀결) | (4) |
| **예외 메시지 문구** | ★ **이 판의 관찰** | (2)(3) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **읽기만 하는 매개변수는 `IEnumerable<T>`·`IReadOnlyList<T>` 로 받아라** — 호출자가 `List<Derived>` 를 **그대로** 넘긴다((1)(형태)).
- ★★★ **내 인터페이스가 `T` 를 반환만 하면 `out`, 받기만 하면 `in` 을 달아라** — 안 달면 쓰는 쪽이 불변에 막힌다((1) 6행).
- ★★ **배열을 공변으로 넘기지 마라** — 받는 쪽이 쓰면 **런타임에 터진다.** 읽기 전용이면 `IReadOnlyList<T>` 로((2)).
- ★★ **값 타입 시퀀스를 `object` 로 보고 싶으면 명시적으로 박싱해라**(`xs.Cast<object>()` 류) — 변성은 대신해 주지 않는다((1)).
- ★ **캐스트로 `CS0266` 을 누르지 마라** — 대개 `InvalidCastException` 이 기다린다((2)).

## 핵심 문장

1. ★★★ **변환 16칸 중 막힌 칸 8** — 통과한 것은 **전부 안전한 방향**(`out` 은 넓게, `in` 은 좁게)이다((1)).
2. ★★★ **배열은 공변이라 컴파일러가 못 막고 런타임이 막는다** — C# `ArrayTypeMismatchException` · Java `ArrayStoreException`((2)(3)).
3. ★★★ **값 타입 인자에는 변성이 없다** — 박싱이 필요하기 때문이다. 런타임 `is` 도 `False`((1)(5)).
4. ★★★ **변성은 CLI 메타데이터 플래그**이고 **변환은 같은 참조**다 — IL 명령도 할당도 없다((4)(5)).
5. ★★ **C# 은 선언 지점 변성, Java 는 사용 지점 와일드카드**((3)).

## 관련 자료

- [24번 — 제네릭](../24-generics-and-type-parameters/) — **경계**: 타입이 런타임까지 남는 것은 거기. 변성 플래그가 **런타임에서 쓸모가 있는 이유**가 그것이다.
- [25번 — 제약](../25-generic-constraints-where-and-default/) — 제네릭 사슬의 앞 편.
- [17번 — 인터페이스](../17-interfaces-default-members-explicit-implementation/) — `out`/`in` 이 붙는 자리.
- [27번 — 델리게이트](../27-delegates-and-func-action/) — `Func<in T, out TResult>` 의 델리게이트 쪽.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **28번**([`28-generics-variance-in-out-star-where/`](../../../kotlin/syntax/28-generics-variance-in-out-star-where/)) — ★★★ **C# 의 `CS1960`·`CS1961` 을 직접 던진 정본.** **경계**: 선언 지점 + 사용 지점(`*`)은 거기.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **18번**([`18-wildcards-pecs/`](../../../java/syntax/18-wildcards-pecs/)) — **경계**: 와일드카드·PECS 의 정본.

## 용어 풀이

- **공변(covariance, `out`)** — `A` 가 `B` 의 하위 타입이면 `I<A>` 를 `I<B>` 로 쓸 수 있는 것. 반환 자리에만 쓰는 `T`.
- **반변(contravariance, `in`)** — 반대로 `I<B>` 를 `I<A>` 로 쓸 수 있는 것. 인자 자리에만 쓰는 `T`.
- **불변(invariance)** — 둘 다 안 되는 것. 제네릭의 기본값.
- **배열 공변** — `string[]` 을 `object[]` 로 부를 수 있는 것. 저장할 때 런타임 검사가 따른다.
- **선언 지점 변성(declaration-site)** — 타입을 **정의하는 곳**에서 `out`/`in` 을 적는 방식(C#·Kotlin).
- **사용 지점 변성(use-site)** — 타입을 **쓰는 곳**에서 `? extends`·`? super` 로 적는 방식(Java).
- **`stelem.ref`** — 참조 배열에 원소를 저장하는 IL 명령. 원소 타입 검사를 포함한다.
- **`castclass`** — 참조를 지정한 타입으로 확인·변환하는 IL 명령. 실패하면 `InvalidCastException`.

## 더 들어가면

- ★ **변성 인터페이스의 모호한 구현** — 한 클래스가 `IEnumerable<A>` 와 `IEnumerable<B>` 를 둘 다 구현하면 `IEnumerable<object>` 로 볼 때 **어느 쪽인가** — **안 던졌다.**
- ★ **델리게이트 결합과 변성** — Learn: 「변성은 **델리게이트 결합에는 적용되지 않는다**」. `+` 로 합치면 런타임 예외라고 알려져 있다 — **이 판에서 안 던졌다**(27번의 멀티캐스트와 잇는 자리).
- ★ **공변 반환(C# 9)** — `override` 가 더 좁은 반환 타입을 쓰는 것. 이름은 같지만 **제네릭 변성과 다른 기능**이다.
