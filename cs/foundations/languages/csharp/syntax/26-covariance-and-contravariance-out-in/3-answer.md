# csharp/syntax/26 — 공변·반변 (`out`/`in`) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **진단 코드 · 옵코드 · 예외 타입 · 리플렉션 변성 플래그 · 스크립트가 센 칸 수** 다.
> ★★★ **이 문서는 시간도 할당 바이트도 재지 않았다** — 할당 창은 **잴 것이 없다**(4·5번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **막힌 칸 8 / 16** — 통과는 **전부 안전한 방향**

**출력**

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

**왜 그런가**

- ★★★ **3행 `IList` `CS0266` · 2행 `IReadOnlyList` `ok`** — `IList<T>` 는 넣고 꺼내 **불변**, `IReadOnlyList<out T>` 는 꺼내기만 해 **공변**.
- ★★★ **13행 `string[]` `ok` · 14행 `int[]` `CS0029`** · **1행 `ok` · 15행 `IEnumerable<int>` `CS0266`** — **값 타입 인자에는 변성이 없다.**
- ★★ **`CS0266`(명시적 변환 있음)은 인터페이스·델리게이트 사이**, **`CS0029`(변환 없음)는 클래스·값 타입 배열·`Func<int>`**.
- ★★ **6행 `IBox<T>`** 는 반환만 하는데도 `out` 을 안 달아 **`CS0266`** — 변성은 **선언해야** 생긴다.

### 2. ★★★ **`[2]` `ArrayTypeMismatchException`** · **`[4]`\~`[6]` `InvalidCastException`**

**출력**

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

**왜 그런가**

- ★★★ **`[0]` 실제 타입은 `System.String[]`** — `object[]` 는 **같은 배열의 다른 이름**이다. 그래서 **`[2]` `42` 저장이 런타임에 막힌다.**
- ★★ **`[1]` `"text"`·`[3]` `null` 은 예외 없음** — `null` 은 어느 참조 배열에나 들어간다.
- ★★★ **`[4]`\~`[6]`** — `CS0266` 자리에 캐스트를 붙이면 **컴파일은 되고** 실제 객체가 그 타입이 아니라 **`InvalidCastException`**.

### 3. ★★★ **같다** — Java 는 **`ArrayStoreException`** · 제네릭은 **불변**이고 **와일드카드는 통과**

**출력**

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

**왜 그런가**

- ★★★ **`[2]` `java.lang.ArrayStoreException: java.lang.Integer`** — C# 의 `ArrayTypeMismatchException` 과 **같은 모양**이다. 두 언어 모두 **배열 공변 + 저장 시 검사**를 골랐다.
- ★★ **`List<Object> lo = ls` 는 javac `incompatible types`**(6행 · `exit=1`) — Java 제네릭도 불변. **7행 `List<? extends Object>` 는 에러가 없다**(진단이 6행 하나뿐) — **사용 지점 변성**이다.

### 4. ★★ 변환은 **명령 없음** · 저장은 **`stelem.ref`** · 캐스트는 **`castclass`**

**출력**

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

**왜 그런가**

- ★★★ **`Up`·`Down` 은 `ldarg.0` · `ret`, `Arr` 도 명령 없이 지역 변수를 거칠 뿐** — 같은 참조를 그대로 넘긴다.
- ★★★ **`Store` 의 `stelem.ref` 에서 `ArrayTypeMismatchException`**, **`Cast` 의 `castclass` 에서 `InvalidCastException`**(2번).

### 5. ★★★ 변성은 **타입 매개변수의 플래그** — 런타임 `is` 도 따른다 · 변환은 **같은 객체**

**출력**

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

**왜 그런가**

- ★★★ **[A] `IEnumerable`·`IReadOnlyList` `Covariant` · `IList`·`List` `None` · `IComparer`·`Action` `Contravariant` · `Func<T,TResult>` 는 `T` 반변 · `TResult` 공변.**
- ★★★ **[B1] `True` · [B2] `False` · [B3] `False` · [B4] `True` · [B5] `False`** — 런타임 타입 검사가 **변성과 값 타입 불변을 그대로** 따른다(CLI 규칙).
- ★★★ **[C] `True` · ``List`1``** — 변환이 새 객체를 안 만든다. **할당 창이 부적용인 근거**다.

### 6. ★★ **`hello` · `Put(world)` · `<x>`** — C# 3 판은 **`CS8024` 네 곳**

**출력**

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

**왜 그런가**

- ★★ **`ISource<out T>` 는 넓게, `ISink<in T>` 는 좁게, `Map<in TA, out TR>` 은 두 방향으로** 쓰였다.
- ★★ **`-langversion:3` 은 `out`·`in` 이 적힌 네 자리(2행 · 3행 · 4행 두 곳)에 `CS8024 … language version 4 or greater`** — 변성은 **C# 4** 다.

### 7. ★★★ 변성 변환은 **표현을 안 바꾸는 변환**이다 — `int` 를 `object` 로 보려면 **박싱**(표현이 바뀐다)이 필요하다

- ★★★ `string` 참조는 **그 비트 그대로** `object` 참조로 읽힌다 — 그래서 `IEnumerable<string>` 을 `IEnumerable<object>` 로 **같은 객체째** 볼 수 있다. `int` 는 `object` 가 되려면 **힙에 상자를 새로 만들어야** 하고, 변성 변환은 그런 일을 끼워 넣지 않는다.
- ★ **런타임도 같다** — 5번 [B3] `List<int> is IEnumerable<object>` 가 `False`, [B5] 도 `False`.

### 8. ★★★ 배열은 **넣기까지 허락**하기 때문이다 — 검사는 **ECMA-335 의 `stelem.ref`**

- ★★★ 제네릭 변성은 **넣는 쪽을 못 쓰게 하는 방향만** 허락해 **런타임에 틀릴 일이 없다.** 배열 공변은 `object[]` 로 **넣기까지** 허락하므로 실제 원소 타입과 어긋날 수 있고, 그래서 **저장할 때마다 검사**한다.
- ★★ **CLI 명세**가 배열 공변과 그 검사를 정한다 — IL 은 **`stelem.ref`**(4번). Java 는 같은 자리가 `aastore` 다([Java 18번](../../../java/syntax/18-wildcards-pecs/)).

### 9. ★★ **`CS0266` = 「명시적 변환은 있다」 · `CS0029` = 「변환이 없다」**

- ★★ **`CS0266`** — 3·6·8·10·15행(인터페이스·델리게이트 사이). **`CS0029`** — 4·14·16행(클래스 `List<>` · 값 타입 배열 · `Func<int>`).
- ★ **캐스트가 안전한 것은 실제 객체가 그 타입임을 알 때뿐**이다 — 2번 [4]\~[6] 은 전부 `InvalidCastException`.

### 10. ★★ **C# 선언 지점(인터페이스·델리게이트만) · Java 사용 지점 · Kotlin 둘 다(클래스에도)**

- ★★ C# 은 `interface I<out T>` 로 **정의하는 곳에만**, Java 는 `List<? extends T>` 로 **쓰는 곳에만**, Kotlin 은 **둘 다** 되고 `class Box<out T>` 까지 된다.
- ★ **C# 클래스에 `out` 을 달면 `CS1960`** — [Kotlin 28번](../../../kotlin/syntax/28-generics-variance-in-out-star-where/)이 `variance28.cs` 로 직접 받았다(`CS1961` 도 함께).

### 11. 잇기

- ★★ **와일드카드·PECS** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **18번**([`18-wildcards-pecs/`](../../../java/syntax/18-wildcards-pecs/)).
- ★ **같은 참조 = 할당할 자리가 없다** — 「재 봤더니 0」이 아니라 **「잴 것이 없다」(제4의 상태)** 다(5번 [C] · 4번).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs26b-grid.cs` 16칸 | csc 2회(격자·표본) | ★★★ **막힌 칸 8 / 16** |
| `cs26b-array.cs` | csc 1회 · 실행 1회 | `ArrayTypeMismatchException` · `InvalidCastException` ×3 |
| `Ex26.java` · `G26.java` | javac 2회 · java 1회 | ★★★ `ArrayStoreException` · `incompatible types`(와일드카드 행은 통과) |
| `cs26b-il.cs` | csc 1회(`-optimize`) · 실행 1회 | 변환 명령 없음 · `stelem.ref` · `castclass` |
| `cs26b-refl.cs` | csc 1회 · 실행 1회 | 변성 플래그 여덟 · 런타임 `is` 다섯 · 같은 참조 |
| `cs26b-decl.cs` | csc 2회(latest · `3`) · 실행 1회 | `hello · Put(world) · <x>` · `CS8024` ×4 |
| `cs26b-form.cs` | csc 1회 · 실행 1회 | `kim lee` · `[x]` · `made` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★ **진단 문구 · 예외 메시지** — 코드와 타입만 근거로 썼다.

**언어·CLI 가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **변성 플래그와 런타임 검사 · 배열 공변과 `stelem.ref` 검사 · 값 타입 불변**(ECMA-335) · **`out`/`in` 은 인터페이스·델리게이트에만**(334).

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ 변성 인터페이스를 둘 구현한 모호성 · 변성 델리게이트의 결합(`+`) · 공변 반환(C# 9) · `CS1960`/`CS1961`(Kotlin 28편 인용으로 대신).
- **못 잰 것** — 없다.
- **잴 것이 없는 것** — ★★★ **④ 할당 바이트** — 변환에 IL 명령이 없고 같은 참조다(4·5번).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★ **1번 격자** — BCL 이 인터페이스의 변성을 바꾸면(예: 새 읽기 전용 인터페이스) 행이 움직인다. 명세 칸은 안 움직인다.
