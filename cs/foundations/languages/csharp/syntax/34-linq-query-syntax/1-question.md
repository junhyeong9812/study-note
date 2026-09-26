# csharp/syntax/34 — LINQ 쿼리 구문 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**쿼리 구문은 컴파일러가 메서드 호출로 바꿔 쓰는 언어 기능이고, 바꿔 쓸 때는 이름만 본다**」 한 줄로 거의 다 풀린다. **절마다 어떤 이름의 메서드가 불리나**를 적어라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`.
> ★★★ **본체 창은 ① IL 호출 목록 격자다.** 시간은 묻지 않는다 — 1번의 답이 그 까닭이다.
> 선행 — [33번](../33-linq-method-syntax-and-deferred-execution/)(메서드 구문 · 즉시와 지연).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 쿼리 구문 열네 꼴이 부르는 메서드 (예측)

```csharp
// cs34b-q.cs
using System.Linq;
public static class Q {
    static readonly int[] xs = { 1, 2, 3 }, ys = { 2, 3, 4 };
    static readonly object[] objs = { 1, 2 };
    public static object Q01() => from x in xs where x > 1 select x * 2;
    public static object Q02() => from x in xs where x > 1 select x;
    public static object Q03() => from x in xs select x;
    public static object Q04() => from x in xs let y = x * 2 where y > 2 select y;
    public static object Q05() => from x in xs from y in ys select x + y;
    public static object Q06() => from x in xs orderby x descending, x % 2 select x;
    public static object Q07() => from x in xs group x by x % 2;
    public static object Q08() => from x in xs group x * 10 by x % 2;
    public static object Q09() => from x in xs join y in ys on x equals y select x + y;
    public static object Q10() => from x in xs join y in ys on x equals y into g select g.Count();
    public static object Q11() => from int x in objs select x;
    public static object Q12() => from x in xs select x into z where z > 1 select z;
    public static object Q13() => from x in xs where x > 1 select x;
    public static object Q14() => from x in xs orderby x orderby x % 2 select x;
}
```

- ★★★ Q01\~Q12 · Q14 각각을 컴파일하면 IL 은 `System.Linq.Enumerable` 의 어떤 메서드를 **어떤 차례로** 부르나?
- ★★ Q04 의 첫 호출의 둘째 타입 인자는 무엇인가?

### 2. ★★★ `System.Linq` 도 `IEnumerable` 도 없는 타입에 쿼리 구문 (예측)

```csharp
// cs34b-user.cs
using System;
class Box<T> {
    public readonly T Value;
    public Box(T v) { Value = v; }
    public Box<U> Select<U>(Func<T, U> f) { Console.WriteLine("  Box.Select 불림"); return new Box<U>(f(Value)); }
    public Box<T> Where(Func<T, bool> p) { Console.WriteLine("  Box.Where 불림"); return p(Value) ? this : new Box<T>(default!); }
}
class Program {
    static void Main() {
        var b = new Box<int>(21);
        Console.WriteLine("[1] from x in b where x > 10 select x * 2");
        var r = from x in b where x > 10 select x * 2;
        Console.WriteLine($"[2] 결과 타입 {r.GetType().Name} · Value = {r.Value}");
        Console.WriteLine($"[3] b is System.Collections.IEnumerable = {b is System.Collections.IEnumerable}");
    }
}
```

- ★★★ 컴파일되나? 된다면 출력 다섯 줄은?

### 3. ★★★ 절 여섯 × 원본 타입 셋 (예측)

```csharp
// cs34b-miss.cs
using System;
using System.Collections.Generic;
class Only<T> { public Only<U> Select<U>(Func<T, U> f) => new Only<U>(); }
class P {
    static void M(Only<int> o, List<int> l, int n) {
        var a1 = from x in o select x + 1;                       // cell select Only<int>
        var a2 = from x in l select x + 1;                       // cell select List<int>
        var a3 = from x in n select x + 1;                       // cell select int
        var b1 = from x in o where x > 1 select x;               // cell where Only<int>
        var b2 = from x in l where x > 1 select x;               // cell where List<int>
        var b3 = from x in n where x > 1 select x;               // cell where int
        var c1 = from x in o orderby x select x;                 // cell orderby Only<int>
        var c2 = from x in l orderby x select x;                 // cell orderby List<int>
        var c3 = from x in n orderby x select x;                 // cell orderby int
        var d1 = from x in o group x by x;                       // cell group Only<int>
        var d2 = from x in l group x by x;                       // cell group List<int>
        var d3 = from x in n group x by x;                       // cell group int
        var e1 = from x in o from y in o select x + y;           // cell from-from Only<int>
        var e2 = from x in l from y in l select x + y;           // cell from-from List<int>
        var e3 = from x in n from y in n select x + y;           // cell from-from int
        var f1 = from x in o join y in o on x equals y select x; // cell join Only<int>
        var f2 = from x in l join y in l on x equals y select x; // cell join List<int>
        var f3 = from x in n join y in n on x equals y select x; // cell join int
    }
    static void Main() { }
}
```

- ★★★ 열여덟 칸 각각에 나는 진단 코드는(없으면 `ok`)?
- ★★ 진단이 가리키는 **열**은 행마다 같은가?

### 4. ★★ 쿼리 구문에 칸이 없는 연산자 (예측)

```csharp
// cs34b-mix.cs
using System;
using System.Linq;
class Program {
    static void Main() {
        int[] xs = { 5, 3, 8, 1, 9, 2 };
        var top2 = (from x in xs where x > 2 orderby x descending select x).Take(2).ToList();
        int n = (from x in xs where x % 2 == 1 select x).Count();
        var same = xs.Where(x => x > 2).OrderByDescending(x => x).Take(2).ToList();
        Console.WriteLine($"[{string.Join(", ", top2)}] · {n} · [{string.Join(", ", same)}]");
    }
}
```

```csharp
// cs34b-kw.cs
using System.Linq;
class P {
    static void Main() {
        int[] xs = { 1, 2, 3 };
        var a = from x in xs where x > 1 take 2 select x;
        var b = from x in xs where x > 1;
    }
}
```

- ★★ 첫 프로그램의 출력은? 둘째 프로그램의 진단 코드는(두 줄 각각)?

### 5. ★★★ 1번의 Q02 와 Q03 (왜)

- 두 꼴의 끝 `select x` 는 IL 에서 각각 어떻게 됐나 — 그렇게 처리한 까닭은?

### 6. ★★ 1번의 Q04 — `let` (왜)

- `let y = x * 2` 의 `y` 는 IL 에서 어디에 사나? 뒤의 `where y > 2` 는 그것을 어떻게 읽나?

### 7. ★★★ 1번의 Q13 (경계)

- Q13 은 Q02 와 **같은 쿼리**인데, 비교 스크립트는 그 짝을 Q02 의 짝과 **다르게** 썼다. 왜 이런 칸을 넣나 — 이 칸이 없으면 「같은 칸 N / M」은 무엇을 증명하지 **못**하나?

### 8. ★★★ 쿼리 구문 대 메서드 구문의 시간은 재야 하나 (경계)

- 1번의 옵코드 열과 람다 본문 비교를 근거로, 이 문서가 할당·시간 창을 「잴 것이 없다」로 둔 까닭을 말하라.

### 9. ★★ 2번과 31번 (1) (연결)

- 2번의 결과를 [31번](../31-ienumerable-and-foreach/) (1)의 인터페이스 없는 `foreach` 와 견주면 같은 모양인가 다른 모양인가? 「바꿔 쓰기」 단계와 「메서드 찾기」 단계를 갈라 말하라.

### 10. ★★ 어느 쪽이 읽기 쉬운 자리인가 (연결)

- `join`·`let`·두 `from` 이 든 쿼리와 `Take`·`Count` 로 끝나는 쿼리 — 각각 어느 구문이 짧아지나? 그 판단은 성능과 관계가 있나?
- ★ 쿼리 구문의 결과를 [33번](../33-linq-method-syntax-and-deferred-execution/) (1)의 격자에서 찾으면 어느 칸인가 — 즉시인가 지연인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
