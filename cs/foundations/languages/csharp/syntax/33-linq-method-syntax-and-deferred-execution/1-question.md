# csharp/syntax/33 — LINQ 메서드 구문과 지연 실행 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**지연 실행은 언어가 아니라 `System.Linq` 가 연산자마다 짠 것이고, 「지연」은 「부를 때 안 돈다」까지만 말한다**」 한 줄로 거의 다 풀린다. **소스가 언제 · 몇 줄 로그를 남기나**를 세라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`. 대비는 **javac/java 21.0.5** 다.
> ★★★ **본체 창은 ⑤ 실행 로그 격자다.** 시간은 묻지 않는다.
> 선행 — [30번](../30-extension-methods-and-extension-members/)(LINQ 는 확장 메서드) · [32번](../32-yield-return-iterators-and-deferred-execution/)(사슬은 0 줄 · 두 번 열거하면 두 번) · [28번](../28-lambdas-and-closure-capture/)(람다는 변수를 잡는다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 연산자 열여섯 — 호출 직후와 첫 `MoveNext` 뒤 (예측)

```csharp
// cs33b-grid.cs
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
class Program {
    static readonly List<string> log = new();
    static IEnumerable<int> Src() {
        foreach (var x in new[] { 3, 1, 4, 2, 5 }) { log.Add($"pull({x})"); yield return x; }
        log.Add("end");
    }
    static int rows, touched, drained;
    static void Row(string name, Func<IEnumerable<int>, object> op) {
        log.Clear();
        object r = op(Src());
        int atCall = log.Count;
        string atFirst = "-";
        if (r is IEnumerable en) { var e = en.GetEnumerator(); e.MoveNext(); atFirst = log.Count.ToString(); }
        rows++;
        if (atCall > 0) touched++;
        if (atCall == 0 && log.Contains("end")) drained++;
        string[] cells = { name, atCall.ToString(), atFirst, r.GetType().Name, string.Join(" ", log) };
        if (cells.Length != 5) throw new Exception("칸 수 어긋남");
        Console.WriteLine(string.Join("\t", cells));
    }
    static void Main() {
        Console.WriteLine(string.Join("\t", "연산자", "호출직후", "첫MoveNext뒤", "돌려준타입(이 판)", "소스 로그"));
        Row("Where", s => s.Where(x => x > 0));
        Row("Select", s => s.Select(x => x * 10));
        Row("OrderBy", s => s.OrderBy(x => x));
        Row("Take(2)", s => s.Take(2));
        Row("Distinct", s => s.Distinct());
        Row("Reverse", s => s.Reverse());
        Row("GroupBy", s => s.GroupBy(x => x % 2));
        Row("Chunk(2)", s => s.Chunk(2));
        Row("AsEnumerable", s => s.AsEnumerable());
        Row("ToList", s => s.ToList());
        Row("ToArray", s => s.ToArray());
        Row("Count()", s => s.Count());
        Row("Any()", s => s.Any());
        Row("First()", s => s.First());
        Row("Sum()", s => s.Sum());
        Row("ToDictionary", s => s.ToDictionary(x => x));
        Console.WriteLine($"호출 즉시 소스를 건드린 칸 {touched} / {rows}");
        Console.WriteLine($"호출 직후 0 줄 · 첫 MoveNext 뒤 end 가 찍힌 칸 {drained} / {rows}");
    }
}
```

- ★★★ 열여섯 줄 각각 「호출직후」 칸과 「첫MoveNext뒤」 칸의 수는?
- ★★★ 마지막 두 줄의 `N / M` 은?

### 2. ★★ `OrderBy` 뒤에서 첫 원소를 꺼내는 네 소비자 (예측)

```csharp
// cs33b-sort.cs
using System;
using System.Collections.Generic;
using System.Linq;
class Counting : IComparer<int> {
    public int calls;
    public int Compare(int a, int b) { calls++; return a.CompareTo(b); }
}
class Program {
    static int keys;
    static int Key(int x) { keys++; return x; }
    static void Run(string label, Func<IEnumerable<int>, Counting, object> consume) {
        var src = new List<int> { 8, 3, 9, 1, 7, 2, 6, 4, 5, 0 };
        var cmp = new Counting(); keys = 0;
        var r = consume(src, cmp);
        Console.WriteLine($"{label,-36} 결과 {r,-3} · 키 선택자 {keys,2} 번 · Compare {cmp.calls,2} 번");
    }
    static void Main() {
        Run("[1] OrderBy(Key, cmp).First()", (s, c) => s.OrderBy(Key, c).First());
        Run("[2] OrderBy(Key, cmp).Take(1).ToList()", (s, c) => s.OrderBy(Key, c).Take(1).ToList()[0]);
        Run("[3] foreach 로 첫 원소만 보고 break", (s, c) => { foreach (var x in s.OrderBy(Key, c)) return x; return -1; });
        Run("[4] OrderBy(Key, cmp).ToList()", (s, c) => s.OrderBy(Key, c).ToList().Count);
    }
}
```

- ★★ 네 줄의 키 선택자 호출 수는 같은가?
- ★★★ 네 줄의 `Compare` 호출 수는?

### 3. ★★★ 같은 호출 · 두 소스 타입 (예측)

```csharp
// cs33b-count.cs
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
class Traced : ICollection<int> {
    public static readonly List<string> log = new();
    readonly List<int> items = new() { 3, 1, 4 };
    public int Count { get { log.Add("Count 속성"); return items.Count; } }
    public IEnumerator<int> GetEnumerator() { log.Add("GetEnumerator"); return items.GetEnumerator(); }
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
    public bool IsReadOnly => true;
    public void Add(int item) => throw new NotSupportedException();
    public void Clear() => throw new NotSupportedException();
    public bool Contains(int item) { log.Add("Contains"); return items.Contains(item); }
    public void CopyTo(int[] array, int i) { log.Add("CopyTo"); items.CopyTo(array, i); }
    public bool Remove(int item) => throw new NotSupportedException();
}
class SeqOnly : IEnumerable<int> {
    readonly List<int> items = new() { 3, 1, 4 };
    public IEnumerator<int> GetEnumerator() { Traced.log.Add("GetEnumerator"); return items.GetEnumerator(); }
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}
class Program {
    static int cells, skipped;
    static void Pair(string name, Func<IEnumerable<int>, object> op) {
        var outs = new List<string> { name };
        foreach (IEnumerable<int> s in new IEnumerable<int>[] { new Traced(), new SeqOnly() }) {
            Traced.log.Clear();
            var r = op(s);
            cells++;
            if (!Traced.log.Contains("GetEnumerator")) skipped++;
            outs.Add($"{r} · {string.Join(" / ", Traced.log)}");
        }
        if (outs.Count != 3) throw new Exception("칸 수 어긋남");
        Console.WriteLine(string.Join("\t", outs));
    }
    static void Main() {
        Console.WriteLine(string.Join("\t", "호출", "ICollection<int> 구현", "IEnumerable<int> 만 구현"));
        Pair("Count()", s => s.Count());
        Pair("Any()", s => s.Any());
        Pair("ToList().Count", s => s.ToList().Count);
        Pair("Contains(4)", s => s.Contains(4));
        Pair("Count(x => x > 1)", s => s.Count(x => x > 1));
        Pair("Where(x => true).Count()", s => s.Where(x => true).Count());
        Console.WriteLine($"GetEnumerator 가 안 불린 칸 {skipped} / {cells}");
    }
}
```

- ★★★ 여섯 줄 각각 두 칸에 찍히는 로그는? 마지막 줄의 `N / M` 은?

### 4. ★★★ 쿼리를 만든 뒤 변수와 소스를 바꾸면 (예측)

```csharp
// cs33b-capture.cs
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static void Main() {
        var src = new List<int> { 1, 2, 3, 4, 5 };
        int threshold = 2;
        var q = src.Where(x => x > threshold);
        var snap = src.Where(x => x > threshold).ToList();
        threshold = 4;
        Console.WriteLine($"[1] q    : [{string.Join(", ", q)}]");
        Console.WriteLine($"[2] snap : [{string.Join(", ", snap)}]");
        src.Add(6);
        Console.WriteLine($"[3] src.Add(6) 뒤 q    : [{string.Join(", ", q)}]");
        Console.WriteLine($"[4] src.Add(6) 뒤 snap : [{string.Join(", ", snap)}]");
    }
}
```

- ★★★ `[1]`\~`[4]` 네 줄의 결과는?

### 5. ★★ 호출 때인가 열거 때인가 (예측)

```csharp
// cs33b-when.cs
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static void Try(string label, Func<IEnumerable<int>> call) {
        IEnumerable<int> q;
        try { q = call(); Console.WriteLine($"{label,-36} 호출 : 돌아옴"); }
        catch (Exception e) { Console.WriteLine($"{label,-36} 호출 : {e.GetType().Name}"); return; }
        try { foreach (var _ in q) { } Console.WriteLine($"{label,-36} 열거 : 끝까지 돎"); }
        catch (Exception e) { Console.WriteLine($"{label,-36} 열거 : {e.GetType().Name}"); }
    }
    static void Main() {
        IEnumerable<int> none = null!;
        int[] xs = { 1, 0, 2 };
        Try("[1] none.Where(x => x > 0)", () => none.Where(x => x > 0));
        Try("[2] xs.Where(null)", () => xs.Where((Func<int, bool>)null!));
        Try("[3] xs.Select(x => 10 / x)", () => xs.Select(x => 10 / x));
        Try("[4] xs.OrderBy(x => 10 / x)", () => xs.OrderBy(x => 10 / x));
    }
}
```

- ★★ 네 탐침 각각 예외는 **호출** 때 나나 **열거** 때 나나 — 무슨 타입인가?

### 6. ★★★ 같은 사슬을 두 번 소비 — C# 과 Java (예측)

```csharp
// cs33b-reuse.cs
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static void Main() {
        IEnumerable<int> q = new List<int> { 1, 2, 3, 4 }.Where(x => x % 2 == 0);
        try { Console.WriteLine($"첫째 : {q.Count()}"); } catch (Exception e) { Console.WriteLine($"첫째 : {e.GetType().FullName}"); }
        try { Console.WriteLine($"둘째 : {q.Count()}"); } catch (Exception e) { Console.WriteLine($"둘째 : {e.GetType().FullName}"); }
    }
}
```

```java
// Reuse33.java
import java.util.List;
import java.util.stream.Stream;
class Reuse33 {
    public static void main(String[] args) {
        Stream<Integer> q = List.of(1, 2, 3, 4).stream().filter(x -> x % 2 == 0);
        try { System.out.println("첫째 : " + q.count()); } catch (Exception e) { System.out.println("첫째 : " + e); }
        try { System.out.println("둘째 : " + q.count()); } catch (Exception e) { System.out.println("둘째 : " + e); }
    }
}
```

- ★★★ 두 프로그램의 「둘째」 줄은 각각 무엇인가?

### 7. ★★★ 1번의 `OrderBy`·`Reverse`·`GroupBy`·`Distinct` 네 줄 (왜)

- 네 연산자의 「첫MoveNext뒤」 값을 **「첫 결과 하나를 내려면 소스에 대해 무엇을 알아야 하나」** 로 설명하라.
- ★★ 그 설명과 2번의 `Compare` 수는 같은 것을 말하나, 다른 것을 말하나?

### 8. ★★ 반환 타입으로 즉시와 지연을 가를 수 있나 (경계)

- `ToList`·`ToArray`·`ToDictionary` 의 결과는 `IEnumerable` 인가? 그렇다면 1번 스크립트는 그 셋에 `MoveNext` 를 불렀나?
- ★ `AsEnumerable` 이 돌려준 객체의 타입은 무엇이고, 그것은 무엇을 뜻하나?

### 9. ★★★ 3번의 결과는 언어 · 문서 · 구현 중 어디에 기대나 (경계)

- 3번 `ICollection<int>` 열의 로그를 **C# 언어 보장**으로 적어도 되나? XML 문서의 `Count` 조항에는 무엇이 있나?
- ★★ 「열거하지 않는다」를 **문서가 약속**하는 메서드는 무엇인가?

### 10. ★★ 32번 (2)의 인자 검사와 5번 (연결)

- 32번 (2)의 `Doubled(null)` 은 **열거 때** 터졌다. 5번의 `[1]`·`[2]` 는 왜 다른가 — 32번 (2)의 어느 판과 같은 모양인가?
- ★ 4번의 `[1]` 을 [28번](../28-lambdas-and-closure-capture/) (6)으로 설명하라.

### 11. ★★ 다른 언어의 스트림·시퀀스와 (연결)

- 6번의 Java 쪽을 [Java 46번](../../../java/syntax/46-terminal-operations/)과, 1번의 `OrderBy` 줄을 [Java 45번](../../../java/syntax/45-intermediate-operations/)의 `sorted` 와 견주면?
- ★ 같은 제너레이터를 두 번 소비하면 Python 은 무엇을 내나([Python 15번](../../../python/syntax/15-generator-expressions-lazy-eval/) §4) — C# · Java · Python 세 언어는 어떻게 갈리나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
