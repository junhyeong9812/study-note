# csharp/syntax/35 — LINQ 그룹·조인·집계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**`GroupBy` 는 묶는 방법이고 `ToLookup` 은 묶어 놓은 것이다 · 시작값이 없는 집계는 빈 입력에서 설 곳이 없다**」 한 줄로 거의 다 풀린다. **원본을 몇 번 읽나 · 비었을 때 무엇이 나오나**를 세라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`.
> ★★★ **본체 창은 ⑤ 실행 로그 + ② 빈 입력 결과 격자다.**
> 선행 — [33번](../33-linq-method-syntax-and-deferred-execution/)(즉시와 지연 · `GroupBy` 칸).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★ 길이로 묶기 (예측)

```csharp
// cs35b-group.cs
using System;
using System.Linq;
class Program {
    static void Main() {
        string[] words = { "bb", "a", "ccc", "d", "ee", "fffff", "g" };
        Console.WriteLine("[1] words.GroupBy(w => w.Length)");
        foreach (var g in words.GroupBy(w => w.Length))
            Console.WriteLine($"    키 {g.Key} : [{string.Join(", ", g)}]");
        var lk = words.ToLookup(w => w.Length);
        Console.WriteLine($"[2] lk.Count = {lk.Count} · lk.Contains(4) = {lk.Contains(4)} · lk[4].Count() = {lk[4].Count()}");
        var counts = words.CountBy(w => w.Length).Select(p => $"{p.Key}:{p.Value}");
        Console.WriteLine($"[3] CountBy : {string.Join(" ", counts)}");
    }
}
```

- ★★ `[1]` 의 묶음은 몇 개이고 어떤 차례로 나오나? 각 묶음 안의 원소 차례는?
- ★★ `[2]`·`[3]` 줄은?

### 2. ★★★ 묶은 결과를 여러 번 쓰면 (예측)

```csharp
// cs35b-twice.cs
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static int reads;
    static IEnumerable<string> Load() {
        reads++;
        Console.WriteLine($"    Load 본문 #{reads}");
        yield return "bb"; yield return "a"; yield return "ccc"; yield return "d";
    }
    static void Main() {
        Console.WriteLine("[1] var g = Load().GroupBy(w => w.Length);");
        var g = Load().GroupBy(w => w.Length);
        Console.WriteLine("[2] foreach (var x in g) 첫째");
        foreach (var x in g) { }
        Console.WriteLine("[3] foreach (var x in g) 둘째");
        foreach (var x in g) { }
        Console.WriteLine("[4] g.Count()");
        _ = g.Count();
        Console.WriteLine($"    GroupBy 쪽 Load 본문 {reads} 번");
        reads = 0;
        Console.WriteLine("[5] var lk = Load().ToLookup(w => w.Length);");
        var lk = Load().ToLookup(w => w.Length);
        Console.WriteLine("[6] foreach (var x in lk) 첫째");
        foreach (var x in lk) { }
        Console.WriteLine("[7] foreach (var x in lk) 둘째");
        foreach (var x in lk) { }
        Console.WriteLine("[8] lk.Count");
        _ = lk.Count;
        Console.WriteLine($"    ToLookup 쪽 Load 본문 {reads} 번");
    }
}
```

- ★★★ `[1]`\~`[8]` 각각 뒤에 `Load 본문` 줄이 찍히나? 두 합계 줄의 수는?

### 3. ★★★ 두 소스를 잇는 `Join` 의 소스 로그 (예측)

```csharp
// cs35b-join.cs
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static readonly List<string> log = new();
    static IEnumerable<int> Traced(string tag, int[] xs) {
        log.Add($"{tag}:start");
        foreach (var x in xs) { log.Add($"{tag}:{x}"); yield return x; }
        log.Add($"{tag}:end");
    }
    static string Take() { var s = string.Join(" ", log); log.Clear(); return s; }
    static void Main() {
        int[] outer = { 1, 2, 3 }, inner = { 2, 3, 3, 4 };
        var j = Traced("O", outer).Join(Traced("I", inner), o => o, i => i, (o, i) => $"{o}-{i}");
        Console.WriteLine($"[1] Join 직후          : {Take()}");
        using var e = j.GetEnumerator();
        e.MoveNext();
        Console.WriteLine($"[2] 첫 MoveNext → {e.Current}  : {Take()}");
        var rest = new List<string>();
        while (e.MoveNext()) rest.Add(e.Current);
        Console.WriteLine($"[3] 나머지 {string.Join(" ", rest)}   : {Take()}");
        var none = Traced("O", new int[0]).Join(Traced("I", inner), o => o, i => i, (o, i) => o).ToList();
        Console.WriteLine($"[4] 바깥이 빈 Join → {none.Count} 개 : {Take()}");
    }
}
```

- ★★★ `[1]`\~`[4]` 네 줄의 로그는?

### 4. ★★ 조인 다섯 꼴 (예측)

```csharp
// cs35b-shape.cs
using System;
using System.Linq;
class Program {
    static void Main() {
        var people = new[] { (Id: 1, Name: "kim"), (Id: 2, Name: "lee"), (Id: 3, Name: "park") };
        var orders = new[] { (PersonId: 1, Item: "pen"), (PersonId: 3, Item: "cup"), (PersonId: 1, Item: "ink"), (PersonId: 9, Item: "box") };
        var inner = people.Join(orders, p => p.Id, o => o.PersonId, (p, o) => $"{p.Name}-{o.Item}");
        Console.WriteLine($"[1] Join            : {string.Join(" ", inner)}");
        var gj = people.GroupJoin(orders, p => p.Id, o => o.PersonId, (p, os) => $"{p.Name}[{string.Join(",", os.Select(o => o.Item))}]");
        Console.WriteLine($"[2] GroupJoin       : {string.Join(" ", gj)}");
        var left = people.GroupJoin(orders, p => p.Id, o => o.PersonId, (p, os) => (p, os))
                         .SelectMany(t => t.os.DefaultIfEmpty(), (t, o) => $"{t.p.Name}-{o.Item ?? "(없음)"}");
        Console.WriteLine($"[3] GroupJoin + DefaultIfEmpty : {string.Join(" ", left)}");
        var left10 = people.LeftJoin(orders, p => p.Id, o => o.PersonId, (p, o) => $"{p.Name}-{o.Item ?? "(없음)"}");
        Console.WriteLine($"[4] LeftJoin        : {string.Join(" ", left10)}");
        var zip = people.Zip(new[] { "A", "B" }, (p, g) => $"{p.Name}{g}");
        Console.WriteLine($"[5] Zip (3 개 · 2 개) : {string.Join(" ", zip)}");
    }
}
```

- ★★ 다섯 줄의 결과는? `lee` 와 `box` 는 각각 어느 줄에 나오나?

### 5. ★★★ 빈 입력 스물두 칸 (예측)

```csharp
// cs35b-empty.cs
using System;
using System.Collections;
using System.Linq;
class Program {
    static int n, threw;
    static void Cell(string name, Func<object?> f) {
        n++;
        string r;
        try {
            var v = f();
            r = v is null ? "null" : v is IEnumerable e && v is not string ? $"[{string.Join(",", e.Cast<object>())}]" : v.ToString()!;
        }
        catch (Exception e) { threw++; r = $"{e.GetType().Name} — {e.Message}"; }
        Console.WriteLine($"{name}\t{r}");
    }
    static void Main() {
        int[] e = { };
        string[] s = { };
        int?[] ni = { };
        Cell("int[] Sum()", () => e.Sum());
        Cell("int[] Count()", () => e.Count());
        Cell("int[] Average()", () => e.Average());
        Cell("int[] Max()", () => e.Max());
        Cell("int[] Min()", () => e.Min());
        Cell("int[] MaxBy(x => x)", () => e.MaxBy(x => x));
        Cell("int[] Aggregate((a, b) => a + b)", () => e.Aggregate((a, b) => a + b));
        Cell("int[] Aggregate(0, (a, b) => a + b)", () => e.Aggregate(0, (a, b) => a + b));
        Cell("int[] First()", () => e.First());
        Cell("int[] FirstOrDefault()", () => e.FirstOrDefault());
        Cell("int[] Single()", () => e.Single());
        Cell("int[] Last()", () => e.Last());
        Cell("int[] ElementAt(0)", () => e.ElementAt(0));
        Cell("string[] Max()", () => s.Max());
        Cell("string[] MaxBy(x => x.Length)", () => s.MaxBy(x => x.Length));
        Cell("string[] Aggregate((a, b) => a + b)", () => s.Aggregate((a, b) => a + b));
        Cell("int?[] Max()", () => ni.Max());
        Cell("int?[] Average()", () => ni.Average());
        Cell("int?[] Sum()", () => ni.Sum());
        Cell("int[] GroupBy(x => x).Count()", () => e.GroupBy(x => x).Count());
        Cell("int[] DefaultIfEmpty()", () => e.DefaultIfEmpty());
        Cell("int[] DefaultIfEmpty(-1)", () => e.DefaultIfEmpty(-1));
        Console.WriteLine($"던진 칸 {threw} / {n}");
    }
}
```

- ★★★ 스물두 칸 각각 값인가 예외인가(예외면 타입)? 마지막 줄의 `N / M` 은?

### 6. ★ `Aggregate` 세 꼴과 결과 선택자 (예측)

```csharp
// cs35b-form.cs
using System;
using System.Linq;

int[] xs = { 3, 1, 4, 1, 5 };
Console.WriteLine(xs.Aggregate((acc, x) => acc - x));
Console.WriteLine(xs.Aggregate("", (acc, x) => acc + x));
Console.WriteLine(xs.Aggregate(0, (acc, x) => acc + x, acc => $"합 {acc}"));
var byParity = xs.GroupBy(x => x % 2 == 0 ? "짝" : "홀", (k, g) => $"{k}:{g.Sum()}");
Console.WriteLine(string.Join(" ", byParity));
```

- ★ 네 줄의 출력은?

### 7. ★★★ 2번의 두 합계 (왜)

- 두 수를 「`g` 가 들고 있는 것」과 「`lk` 가 들고 있는 것」으로 설명하라. [32번](../32-yield-return-iterators-and-deferred-execution/) (7)의 무엇과 같은 뿌리인가?
- ★★ `g.Count()` 는 [33번](../33-linq-method-syntax-and-deferred-execution/) (2)의 지름길을 탈 수 있나?

### 8. ★★★ 3번의 `[2]` 와 `[4]` (왜)

- 안쪽 소스와 바깥 소스는 각각 어떤 방식으로 읽혔나? `[4]` 에서 안쪽 로그가 어떻게 됐나 — 그 까닭은?
- ★ 이 읽는 순서는 문서가 약속하나?

### 9. ★★★ 5번의 칸들은 문서의 약속인가 관찰인가 (경계)

- XML 문서의 예외·반환 조항으로 5번을 가르면 — 「던진다고 약속한 칸」 · 「값을 약속한 칸」 · 「문서가 침묵하는 칸」은 각각 어느 것인가?
- ★★ `MaxBy` 의 XML 예외 조항은 `int[]` 와 `string[]` 에 똑같이 걸리나?

### 10. ★★ 1번과 4번의 묶음 (경계)

- `GroupBy` 와 `GroupJoin` 중 **빈 묶음**을 만드는 쪽은 어느 것인가? 그 차이가 왼쪽 외부 조인을 만드는 데 어떻게 쓰이나?

### 11. ★★ 다른 언어의 접기와 (연결)

- 시드 없는 접기를 빈 입력에 하면 Java 는 무엇을 주나([Java 46번](../../../java/syntax/46-terminal-operations/)) — C# 과 무엇이 다른가?
- ★ 2번의 `GroupBy` 줄은 [33번](../33-linq-method-syntax-and-deferred-execution/) (1) 격자의 어느 칸과 같은 이야기인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
