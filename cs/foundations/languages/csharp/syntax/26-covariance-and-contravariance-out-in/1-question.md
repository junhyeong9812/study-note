# csharp/syntax/26 — 공변·반변 (`out`/`in`) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**그 `T` 로 넣나, 꺼내나, 둘 다인가**」와 「**`T` 가 참조 타입인가**」 두 줄로 거의 다 풀린다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest`(판 격자 문항만 `3`) · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ② 진단 격자다.** 변환 16개를 한 파일에 적고 스크립트가 줄 번호로 되돌려 센다.
> 선행 — [24번](../24-generics-and-type-parameters/)(제네릭) · [25번](../25-generic-constraints-where-and-default/)(제약).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 변환 16개를 한 번에 (예측)

```csharp
// cs26b-grid.cs
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
```

- 16행 각각 — 통과인가, 막히면 **`CS0029` 인가 `CS0266` 인가**?
- ★★★ 3행(`IList`)과 2행(`IReadOnlyList`)은 같은 결과인가?
- ★★★ 13행(`string[]`)과 14행(`int[]`) · 1행과 15행(`IEnumerable<int>`)은?

### 2. ★★★ 공변 배열에 값을 넣고 · `CS0266` 자리에 캐스트를 붙이면 (예측)

```csharp
// cs26b-array.cs
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
```

- `[0]`\~`[6]` 에 무엇이 찍히는가 — 예외가 나면 **타입**은?
- ★★ `[3]` `null` 은?

### 3. ★★★ 같은 모양을 Java 로 (예측)

```java
// Ex26.java
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
```

- `[0]`\~`[3]` 에 무엇이 찍히는가 — `objs[1] = 42` 는 C# 2번과 같은가?
- ★★ `List<String> ls = …; List<Object> lo = ls;` 는 javac 가 받나 · `List<? extends Object> le = ls;` 는?

### 4. ★★ 변환 · 저장 · 캐스트의 IL (예측)

```csharp
// cs26b-il.cs
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
```

- `Up`·`Down`·`Arr` 에 **변환 명령**이 있는가?
- ★★ `Store` 와 `Cast` 의 핵심 명령은 — 런타임 예외는 어느 명령에서 나나?

### 5. ★★★ 변성을 리플렉션으로 · 런타임 `is` 로 (예측)

```csharp
// cs26b-refl.cs
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
```

- `[A]` 여덟 줄 — 각 타입 매개변수의 변성은?
- ★★★ `[B1]`\~`[B5]` 와 `[C]` 는?

### 6. ★★ 내가 선언한 `out`·`in` · C# 3 판 (예측)

```csharp
// cs26b-decl.cs
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
```

- 이 판에서 출력은?
- ★★ `-langversion:3` 으로 던지면 진단은 몇 곳에 무엇이 나오나?

### 7. ★★★ 값 타입 인자에는 왜 변성이 안 먹나 (왜)

- 1번 15·16행이 막히는 이유를 **「표현」** 이라는 말로 설명하라.
- ★ 런타임 `is` 로 물어도 같은가(5번)?

### 8. ★★★ 배열 공변은 누가 막나 (왜)

- 제네릭 변성은 런타임 검사가 필요 없는데 배열은 왜 필요한가?
- ★★ 그 검사는 **어느 층**이 보장하나 — IL 의 어느 명령인가?

### 9. ★★ `CS0266` 과 `CS0029` (경계)

- 두 코드는 무엇을 가르나 — 1번에서 각각 어떤 행들인가?
- ★ `CS0266` 에 캐스트를 붙이는 것은 언제 안전한가?

### 10. ★★ 선언 지점 대 사용 지점 (경계)

- C#·Java·Kotlin 은 변성을 **어디에** 적나 — 클래스에도 되나?
- ★ C# 의 클래스에 `out` 을 달면 무슨 진단인가 — 그 진단을 직접 받은 주제는?

### 11. 다른 주제와 잇기 (연결)

- ★★ Java 의 `? extends`·`? super` 정본은 어느 갈래 몇 번인가?
- ★ 변환이 같은 참조라는 것이 **할당 바이트 창**에 무엇을 뜻하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
