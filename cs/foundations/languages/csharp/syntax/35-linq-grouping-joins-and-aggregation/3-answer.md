# csharp/syntax/35 — LINQ 그룹·조인·집계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 근거로 쓰는 것은 **로그의 줄 수와 순서 · 묶음의 키·원소 순서 · 예외 타입 · 「던진 칸 N / M」** 이다. 예외 **문구**는 판에 매인다.
> ★★★ **이 문서는 시간을 재지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **묶음 넷 — 키 `2 · 1 · 3 · 5`(처음 나온 순서)** · 원소는 **원본 순서** · 키 4 는 **없다** · `lk[4]` 는 **빈 시퀀스**

**출력**

```text
===== 소스: cs35b-group.cs =====
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
===== csc -out:ex.dll cs35b-group.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] words.GroupBy(w => w.Length)
    키 2 : [bb, ee]
    키 1 : [a, d, g]
    키 3 : [ccc]
    키 5 : [fffff]
[2] lk.Count = 4 · lk.Contains(4) = False · lk[4].Count() = 0
[3] CountBy : 2:2 1:3 3:1 5:1
```

**왜 그런가**

- ★★★ `GroupBy` 는 **있는 키만** 만들고, 키는 **처음 나온 차례**로 낸다(이 판의 관찰 — XML 은 키 순서를 말하지 않는다). 묶음 안의 원소 순서는 원본 그대로다(`ToLookup` 은 이것을 XML 이 약속한다).
- ★★ `ILookup` 의 없는 키는 **예외가 아니라 빈 시퀀스** — 「있나」는 `Contains` 로 묻는다.

### 2. ★★★ **`GroupBy` 쪽 3 번**(`foreach` 둘 · `Count()` 하나마다) · **`ToLookup` 쪽 1 번**(만드는 줄에서만)

**출력**

```text
===== 소스: cs35b-twice.cs =====
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
===== csc -out:ex.dll cs35b-twice.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] var g = Load().GroupBy(w => w.Length);
[2] foreach (var x in g) 첫째
    Load 본문 #1
[3] foreach (var x in g) 둘째
    Load 본문 #2
[4] g.Count()
    Load 본문 #3
    GroupBy 쪽 Load 본문 3 번
[5] var lk = Load().ToLookup(w => w.Length);
    Load 본문 #1
[6] foreach (var x in lk) 첫째
[7] foreach (var x in lk) 둘째
[8] lk.Count
    ToLookup 쪽 Load 본문 1 번
```

**왜 그런가**

- ★★★ `GroupBy` 는 지연 — 부를 때 0 줄, **소비할 때마다** 원본을 처음부터 읽어 다시 묶는다. `ToLookup` 은 즉시 — 만드는 줄에서 끝까지 읽고 그 뒤 원본을 **안 본다.**

### 3. ★★★ **`[1]` 0 줄 · `[2]` `O:start O:1 I:start I:2 I:3 I:3 I:4 I:end O:2` · `[3]` `O:3 O:end` · `[4]` `O:start O:end`**

**출력**

```text
===== 소스: cs35b-join.cs =====
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
===== csc -out:ex.dll cs35b-join.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Join 직후          : 
[2] 첫 MoveNext → 2-2  : O:start O:1 I:start I:2 I:3 I:3 I:4 I:end O:2
[3] 나머지 3-3 3-3   : O:3 O:end
[4] 바깥이 빈 Join → 0 개 : O:start O:end
```

**왜 그런가**

- ★★★ 첫 `MoveNext` 에서 바깥을 **한 칸** 본 뒤 안쪽을 **통째로** 읽어 두고, 그 뒤로는 바깥만 한 칸씩 당긴다. 바깥이 비면 **안쪽을 열 일이 없다.**

### 4. ★★ **`[1]` `kim-pen kim-ink park-cup` · `[2]` `kim[pen,ink] lee[] park[cup]` · `[3]`=`[4]` `kim-pen kim-ink lee-(없음) park-cup` · `[5]` `kimA leeB`** — `lee` 는 `[2]`\~`[5]` 에, `box` 는 **어디에도 없다**

**출력**

```text
===== 소스: cs35b-shape.cs =====
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
===== csc -out:ex.dll cs35b-shape.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Join            : kim-pen kim-ink park-cup
[2] GroupJoin       : kim[pen,ink] lee[] park[cup]
[3] GroupJoin + DefaultIfEmpty : kim-pen kim-ink lee-(없음) park-cup
[4] LeftJoin        : kim-pen kim-ink lee-(없음) park-cup
[5] Zip (3 개 · 2 개) : kimA leeB
```

**왜 그런가**

- ★★★ 내부 조인은 **양쪽 짝이 있는 것만** — 주문 없는 `lee`, 사람 없는 `box` 가 둘 다 빠진다. `GroupJoin` 은 바깥마다 한 줄이라 `lee` 가 **빈 묶음**으로 남고, 거기에 `DefaultIfEmpty` 를 넣으면 `LeftJoin` 과 같다. `box` 는 **안쪽에만** 있으므로 왼쪽 외부 조인에도 없다.
- ★★ `Zip` 은 **위치**로 짝짓고 짧은 쪽(2 개)에서 멈춘다.

### 5. ★★★ **던진 칸 10 / 22** — `int[]` 의 `Average`·`Max`·`Min`·`MaxBy`·시드 없는 `Aggregate`·`First`·`Single`·`Last` 와 `string[]` 의 시드 없는 `Aggregate` 가 **`InvalidOperationException`**, `ElementAt(0)` 이 **`ArgumentOutOfRangeException`** · 나머지는 값(`0` · `null` · `[0]` · `[-1]`)

**출력**

```text
===== 소스: cs35b-empty.cs =====
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
===== csc -nullable:enable -out:ex.dll cs35b-empty.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int[] Sum()	0
int[] Count()	0
int[] Average()	InvalidOperationException — Sequence contains no elements
int[] Max()	InvalidOperationException — Sequence contains no elements
int[] Min()	InvalidOperationException — Sequence contains no elements
int[] MaxBy(x => x)	InvalidOperationException — Sequence contains no elements
int[] Aggregate((a, b) => a + b)	InvalidOperationException — Sequence contains no elements
int[] Aggregate(0, (a, b) => a + b)	0
int[] First()	InvalidOperationException — Sequence contains no elements
int[] FirstOrDefault()	0
int[] Single()	InvalidOperationException — Sequence contains no elements
int[] Last()	InvalidOperationException — Sequence contains no elements
int[] ElementAt(0)	ArgumentOutOfRangeException — Index was out of range. Must be non-negative and less than the size of the collection. (Parameter 'index')
string[] Max()	null
string[] MaxBy(x => x.Length)	null
string[] Aggregate((a, b) => a + b)	InvalidOperationException — Sequence contains no elements
int?[] Max()	null
int?[] Average()	null
int?[] Sum()	0
int[] GroupBy(x => x).Count()	0
int[] DefaultIfEmpty()	[0]
int[] DefaultIfEmpty(-1)	[-1]
던진 칸 10 / 22
```

**왜 그런가**

- ★★★ **시작값이 없으면 던진다** — 「첫 원소」가 있어야 답이 서는 연산(평균·최대·최소·첫/끝/단 하나·시드 없는 접기)이다. **항등원이나 시드가 있으면 값**이다(`Sum` `0` · 시드 `Aggregate` `0` · `Count` `0`).
- ★★ **참조형·널 허용 값형의 `Max`·`MaxBy` 는 `null`** — 「없음」을 `null` 로 말할 수 있다. `int[]` 는 그럴 수 없어 던진다.

### 6. ★ **`-8` · `31415` · `합 14` · `홀:10 짝:4`**

**출력**

```text
===== 소스: cs35b-form.cs =====
using System;
using System.Linq;

int[] xs = { 3, 1, 4, 1, 5 };
Console.WriteLine(xs.Aggregate((acc, x) => acc - x));
Console.WriteLine(xs.Aggregate("", (acc, x) => acc + x));
Console.WriteLine(xs.Aggregate(0, (acc, x) => acc + x, acc => $"합 {acc}"));
var byParity = xs.GroupBy(x => x % 2 == 0 ? "짝" : "홀", (k, g) => $"{k}:{g.Sum()}");
Console.WriteLine(string.Join(" ", byParity));
===== csc -out:ex.dll cs35b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
-8
31415
합 14
홀:10 짝:4
```

- ★ 시드 없음은 **첫 원소(3)가 시작값** · 시드 `""` 는 **누적 타입이 `string`** · 결과 선택자는 **끝에 한 번.** `GroupBy` 결과 선택자는 키 순서가 **처음 나온 순서**라 `홀` 이 먼저(첫 원소 3).

### 7. ★★★ **`g` 는 「묶는 방법」, `lk` 는 「묶어 놓은 것」** — 32번 (7)의 「결과가 아니라 만드는 방법을 들고 있다」와 같은 뿌리 · `g.Count()` 는 **지름길이 없다**

- ★★★ 지연 쿼리를 변수에 두면 **소비 횟수만큼** 원본을 읽는다 — [32번](../32-yield-return-iterators-and-deferred-execution/) (7)의 `Load` 가 두 번 돈 것과 같다. 그룹 결과라고 달라지지 않는다.
- ★★ [33번](../33-linq-method-syntax-and-deferred-execution/) (2)의 지름길은 **`ICollection<T>`** 일 때다. `GroupBy` 의 결과는 컬렉션이 아니라 **묶어 봐야 개수를 아는** 지연 시퀀스다 — 그래서 `#3` 이 찍혔다.

### 8. ★★★ **안쪽은 통째로 한 번 · 바깥은 한 칸씩** · `[4]` 는 **안쪽 로그 0 줄** — 바깥에서 첫 원소를 못 얻으면 짝을 찾을 일이 없다 · ★ **순서는 문서가 약속하지 않는다**

- ★★★ `O:1` 을 본 **뒤에** `I:start … I:end` — 안쪽을 서랍장(룩업)으로 만든 것으로 읽힌다. 그 뒤 `O:2`·`O:3` 은 서랍을 여는 것뿐이라 안쪽을 다시 안 읽는다.
- ★ XML 문서는 `Join` 의 **결과**(「일치하는 키로 두 시퀀스의 원소를 짝짓는다」)만 말한다. 읽는 **순서**는 BCL 구현이다.

### 9. ★★★ **던진다고 약속** — 시드 없는 `Aggregate`·`Average(int)`·`Max(int)`·`First`·`ElementAt`·`MaxBy`(기본형) · **값을 약속** — `Average(int?)` 의 `null` · **침묵** — 제네릭 `Max<T>`(`string[] Max()` 의 `null`)·`Max(int?)` 의 `null`

- ★★★ XML 을 열어 대조한 결과다(2-summary (5)의 표). **같은 `null` 인데 `int?[] Average()` 는 계약이고 `string[] Max()` 는 관찰**이다.
- ★★ **`MaxBy` 의 조항은 「`TSource` 가 기본형이고 원본이 비었으면」** — `int` 는 그 안이라 던지고, `string` 은 그 밖이라 `null` 이다. **한 조항이 두 칸을 가른다.**

### 10. ★★ **`GroupJoin` 이 빈 묶음을 만든다(`lee[]`) · `GroupBy` 는 안 만든다(키 4 가 없다)** — 그 빈 묶음에 `DefaultIfEmpty()` 로 기본값 하나를 넣어 펼치면 **왼쪽 외부 조인**

- ★★ `GroupBy` 는 **원본에 있는 원소**에서 키를 만든다 — 원소가 없는 키는 나올 수가 없다. `GroupJoin` 은 **바깥 원소마다** 한 줄이라, 짝이 없어도 줄이 생기고 묶음이 빈다.

### 11. ★★ **Java 는 `Optional.empty` 를 준다 — C# 은 던진다** · 2번의 `GroupBy` 줄은 33번 (1)의 **`GroupBy` 칸(호출 0 줄 · 첫 `MoveNext` 에서 끝까지)**

- ★★ [Java 46번](../../../java/syntax/46-terminal-operations/) — 항등원 없는 `reduce` 가 빈 스트림에서 `Optional.empty`. 「비어 있음」을 **값**으로 준다. C# 의 시드 없는 `Aggregate` 는 **예외**로 준다.
- ★ [33번](../33-linq-method-syntax-and-deferred-execution/) (1) — `GroupBy` 는 부를 때 0 줄, 첫 `MoveNext` 에서 끝까지 읽는다. 2번은 그것이 **소비마다** 일어난다는 것이다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs35b-group.cs` | csc 1회 · 실행 1회 | 키 `2 · 1 · 3 · 5` · 키 4 없음 · `lk[4]` 빈 것 |
| `cs35b-twice.cs` | csc 1회 · 실행 1회 | ★★★ **`GroupBy` 3 번 · `ToLookup` 1 번** |
| `cs35b-join.cs` | csc 1회 · 실행 1회 | ★★★ 안쪽 통째로 한 번 · 바깥이 비면 안쪽 0 줄 |
| `cs35b-shape.cs` | csc 1회 · 실행 1회 | 내부 · 그룹 · 왼쪽 외부 둘(같음) · `Zip` |
| `cs35b-empty.cs` | csc 1회 · 실행 1회 | ★★★ **던진 칸 10 / 22** |
| `cs35b-form.cs` | csc 1회 · 실행 1회 | `-8` · `31415` · `합 14` · `홀:10 짝:4` |
| `System.Linq.xml` | 조항을 열어 대조 | 예외·반환 조항(9번) |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12)에서만** 그렇다.

- ★★★ **`Join` 의 읽는 순서** · `GroupBy` 의 **키 순서** · **문서가 침묵하는 `null`**(`string[] Max()` · `int?[] Max()`) · 예외 문구.

**문서가 보장하는 것**(구현이 바뀌어도 같다)

- **시드 없는 `Aggregate`·`Average(int)`·`Max(int)`·`First` 의 빈 입력 → `InvalidOperationException`** · **`MaxBy` 는 기본형일 때만** · **`Average(int?)` 의 `null`** · **`ToLookup` 의 원소 순서.**

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ 무한 안쪽 시퀀스의 `Join`(끝나지 않는 실험) · `RightJoin`.
- **못 잰 것** — ★ 연산자마다 **들어온 판**(참조 팩이 10.0.12 하나뿐) · ★★★ **시간**.
- **잴 것이 없는 것** — ★ **IL** — 전부 `call Enumerable::…` 한 줄씩이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **5번의 「침묵」 칸 · 3번 · 1번의 키 순서** — 문서가 약속하지 않은 것들이다.
