# csharp/syntax/09 — 배열과 인덱스·범위 연산자(C# 8) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> ★★★ **4번이 이 주제의 중심이다** — **출력만 보면 두 답이 같다.** 갈라야 하는 것은 **바이트**다.
> ★★ **9번은 값으로는 원리상 못 푼다** — **진단이 가리키는 열**을 읽어야 답이 나온다.
> ★ **2번의 `^0` 을 「마지막 원소」로 답하면 3번이 안 풀린다.**
> 선행 — [01번](../01-value-types-and-reference-types/)(배열이 참조 타입인 것) · [03번](../03-boxing-and-unboxing/)(할당 바이트를 재는 법).
> 경계 — **동적 배열의 원리**는 [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이다.
> 대비 — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **15번** ·
> Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **9번** ·
> Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **5번**.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 배열에게 자기가 무엇인지 물으면 (예측)

```csharp
// cs09b-ref.cs
using System;

int[] a = { 10, 20, 30, 40, 50 };
int[] b = a;                       // 참조만 복사된다
b[0] = 999;

Console.WriteLine($"typeof(int[]).IsValueType      : {typeof(int[]).IsValueType}");
Console.WriteLine($"typeof(int[]).BaseType         = {typeof(int[]).BaseType}");
Console.WriteLine($"typeof(int[]).IsArray          : {typeof(int[]).IsArray}");
Console.WriteLine($"typeof(int[]).GetElementType() = {typeof(int[]).GetElementType()}");
Console.WriteLine($"a is System.Collections.IList  : {a is System.Collections.IList}");
Console.WriteLine();
Console.WriteLine($"ReferenceEquals(a, b)          : {ReferenceEquals(a, b)}");
Console.WriteLine($"b[0] = 999 뒤 a[0]             : {a[0]}");
Console.WriteLine($"a.Length                       : {a.Length}   a.Rank : {a.Rank}");

Bump(a);
Console.WriteLine($"Bump(a) 뒤 a[1]                : {a[1]}   ← 메서드가 원본을 바꿨다");

int[] c = (int[])a.Clone();
c[1] = -1;
Console.WriteLine($"Clone() 뒤 a[1]={a[1]} c[1]={c[1]}  ReferenceEquals={ReferenceEquals(a, c)}");

int[] fresh = new int[3];
Console.WriteLine($"new int[3] 의 원소            : [{string.Join(", ", fresh)}]  ← 0 으로 채워진다");
string[] strs = new string[2];
Console.WriteLine($"new string[2] 의 원소         : [{(strs[0] is null ? "null" : strs[0])}, {(strs[1] is null ? "null" : strs[1])}]");

static void Bump(int[] arr) { arr[1] += 1; }
```

- `typeof(int[]).IsValueType` 과 `BaseType` 은 각각 무엇인가?
- ★ `int[] b = a;` 뒤 `b[0] = 999` 를 하면 **`a[0]` 은 무엇인가**?
- `Bump(a)` 는 `ref` 가 없는데 **원본을 바꾸는가**?
- `Clone()` 한 배열은 `ReferenceEquals` 가 무엇인가?
- `new string[2]` 의 원소는 무엇인가 — [06번](../06-nullable-reference-types/)이 이것을 **경고로 잡아 주는가**?

### 2. ★★ `var i = ^1;` 과 `var r = 1..^1;` 을 찍으면 (예측)

```csharp
// cs09b-index.cs
using System;

var i = ^1;
var r = 1..^1;
Console.WriteLine($"var i = ^1;     i.GetType() = {i.GetType()}");
Console.WriteLine($"var r = 1..^1;  r.GetType() = {r.GetType()}");
Console.WriteLine($"typeof(Index).IsValueType : {typeof(Index).IsValueType}   typeof(Range).IsValueType : {typeof(Range).IsValueType}");
Console.WriteLine();

Index e1 = ^1, e0 = ^0, s2 = 2;
Console.WriteLine($"^1 : Value={e1.Value} IsFromEnd={e1.IsFromEnd}  ToString()='{e1}'");
Console.WriteLine($"^0 : Value={e0.Value} IsFromEnd={e0.IsFromEnd}  ToString()='{e0}'");
Console.WriteLine($" 2 : Value={s2.Value} IsFromEnd={s2.IsFromEnd}  ToString()='{s2}'");
Console.WriteLine($"Index.Start={Index.Start}  Index.End={Index.End}  (Index.End 의 IsFromEnd={Index.End.IsFromEnd})");
Console.WriteLine();

int len = 5;
Console.WriteLine($"^1.GetOffset(5) = {e1.GetOffset(len)}");
Console.WriteLine($"^0.GetOffset(5) = {e0.GetOffset(len)}   ← 길이와 같다");
Console.WriteLine($" 2.GetOffset(5) = {s2.GetOffset(len)}");
Console.WriteLine();

Console.WriteLine($"1..^1 : Start={r.Start} End={r.End}  ToString()='{r}'");
Console.WriteLine($"Range.All : Start={Range.All.Start} End={Range.All.End}  ToString()='{Range.All}'");
var ol = r.GetOffsetAndLength(5);
Console.WriteLine($"(1..^1).GetOffsetAndLength(5) = (offset={ol.Offset}, length={ol.Length})");
Console.WriteLine();

int[] a = { 10, 20, 30, 40, 50 };
Console.WriteLine($"a[^1]   = {a[^1]}     a[^5] = {a[^5]}");
Console.WriteLine($"a[1..^1] = [{string.Join(", ", a[1..^1])}]");
Console.WriteLine($"a[..2]   = [{string.Join(", ", a[..2])}]");
Console.WriteLine($"a[3..]   = [{string.Join(", ", a[3..])}]");
Console.WriteLine($"a[..]    = [{string.Join(", ", a[..])}]   ← 전체");
Console.WriteLine($"a[2..2]  = [{string.Join(", ", a[2..2])}] (길이 {a[2..2].Length})  ← 빈 배열, 예외가 아니다");
Console.WriteLine($"a[^3..^1] = [{string.Join(", ", a[^3..^1])}]");
```

- ★★★ **두 `GetType()` 이 각각 무엇을 찍는가** — `IsValueType` 은?
- `^1`·`^0`·`2` 의 `Value`·`IsFromEnd` 는 각각 무엇인가?
- ★★★ **`^0.GetOffset(5)` 는 무엇인가**?
- `Range.All` 의 `ToString()` 은?
- `a[2..2]` 는 예외인가, 무엇인가?

### 3. `a[^0]` 을 읽으면 (예측)

```csharp
// cs09b-end0.cs
using System;

int[] a = { 10, 20, 30, 40, 50 };
Console.WriteLine(a[^0]);
```

- **예외 타입**과 **메시지 전문**은?
- 이것을 **컴파일러가 막아 주는가**?
- ★★ 그런데 `a[3..^0]` 은 **왜 정상인가**?

### 4. ★★★ 같은 세 숫자를 두 방법으로 얻으면 (예측)

```csharp
// cs09b-alloc.cs
using System;

Warm();

int[] a = { 10, 20, 30, 40, 50 };

long b0 = GC.GetAllocatedBytesForCurrentThread();
int[] copy = a[1..^1];                        // 배열의 .. — 새 배열
long b1 = GC.GetAllocatedBytesForCurrentThread();
Span<int> view = a.AsSpan()[1..^1];           // Span 의 .. — 뷰
long b2 = GC.GetAllocatedBytesForCurrentThread();
int one = a[^1];                              // 끝 기준 인덱싱
long b3 = GC.GetAllocatedBytesForCurrentThread();
int[] whole = a[..];                          // 전체 범위
long b4 = GC.GetAllocatedBytesForCurrentThread();
int[] none = a[2..2];                         // 빈 범위
long b5 = GC.GetAllocatedBytesForCurrentThread();
Span<int> sneaky = a[1..^1];                  // Span 에 받아도 배열 인덱서가 먼저 돈다
long b6 = GC.GetAllocatedBytesForCurrentThread();
string s = "abcdef";
string sub = s[1..^1];                        // string 의 .. — Substring
long b7 = GC.GetAllocatedBytesForCurrentThread();
ReadOnlySpan<char> chars = s.AsSpan()[1..^1]; // ReadOnlySpan 의 .. — 뷰
long b8 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"int[] copy   = a[1..^1]            : +{b1 - b0} 바이트");
Console.WriteLine($"Span<int>    = a.AsSpan()[1..^1]   : +{b2 - b1} 바이트");
Console.WriteLine($"int one      = a[^1]               : +{b3 - b2} 바이트");
Console.WriteLine($"int[] whole  = a[..]               : +{b4 - b3} 바이트");
Console.WriteLine($"int[] none   = a[2..2]             : +{b5 - b4} 바이트  (길이 {none.Length})");
Console.WriteLine($"Span<int>    = a[1..^1]            : +{b6 - b5} 바이트  ← AsSpan() 을 안 거쳤다");
Console.WriteLine($"string sub   = s[1..^1]            : +{b7 - b6} 바이트  (\"{sub}\")");
Console.WriteLine($"ROSpan<char> = s.AsSpan()[1..^1]   : +{b8 - b7} 바이트  (길이 {chars.Length})");
Console.WriteLine();

copy[0] = -1;
Console.WriteLine($"copy[0] = -1 뒤  a[1] = {a[1]}   ← 원본이 안 바뀐다");
view[0] = -2;
Console.WriteLine($"view[0] = -2 뒤  a[1] = {a[1]}   ← 원본이 바뀐다");
sneaky[0] = -3;
Console.WriteLine($"sneaky[0] = -3 뒤 a[1] = {a[1]}   ← 안 바뀐다 (복사본을 보고 있다)");
Console.WriteLine($"a = [{string.Join(", ", a)}]  one={one}  whole.Length={whole.Length}");
Console.WriteLine($"ReferenceEquals(a, a[..]) : {ReferenceEquals(a, a[..])}");
Console.WriteLine();

long c0 = GC.GetAllocatedBytesForCurrentThread();
for (int k = 0; k < 1000; k++) { int[] t = a[1..^1]; GC.KeepAlive(t); }
long c1 = GC.GetAllocatedBytesForCurrentThread();
int acc = 0;
long d0 = GC.GetAllocatedBytesForCurrentThread();
for (int k = 0; k < 1000; k++) { Span<int> t = a.AsSpan()[1..^1]; acc += t[0]; }
long d1 = GC.GetAllocatedBytesForCurrentThread();
Console.WriteLine($"배열 슬라이스 1000번 : +{c1 - c0} 바이트");
Console.WriteLine($"Span 슬라이스 1000번 : +{d1 - d0} 바이트   (acc={acc})");

static void Warm() {
    int[] w = { 1, 2, 3 };
    int[] wc = w[0..2];
    Span<int> ws = w.AsSpan()[0..2];
    string wsx = "abc"[0..2];
    ReadOnlySpan<char> wrs = "abc".AsSpan()[0..2];
    GC.KeepAlive(wc); GC.KeepAlive(wsx);
    GC.KeepAlive(ws.Length + wrs.Length);
    GC.GetAllocatedBytesForCurrentThread();
}
```

- ★★★ **여덟 줄의 증분 바이트**를 각각 맞힐 수 있는가?
- ★★★ `copy[0] = -1` 과 `view[0] = -2` 뒤의 **`a[1]`** 은 각각 무엇인가?
- ★★★ `Span<int> sneaky = a[1..^1];` 은 몇 바이트이고, `sneaky[0] = -3` 이 원본을 바꾸는가?
- `a[..]` 는 몇 바이트이고 `ReferenceEquals(a, a[..])` 는 무엇인가?
- `a[2..2]` 는 왜 그 수인가 — 그것이 **언어 보장인가**?
- 마지막 두 줄(1000번 루프)의 차이는?

### 5. ★★ 내 타입에 `[^1]` 과 `[1..^1]` 을 붙이려면 (예측)

```csharp
// cs09b-custom.cs
using System;
using System.Collections.Generic;

var bag = new Bag(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Bag : Length + this[int] + Slice");
Console.WriteLine($"  bag[^1]    = {bag[^1]}");
Console.WriteLine($"  bag[1..^1] = {bag[1..^1]}");

var cnt = new Counted(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Counted : Count + this[int] + Slice   ← Length 가 아니라 Count 다");
Console.WriteLine($"  cnt[^1]    = {cnt[^1]}");
Console.WriteLine($"  cnt[1..^1] = {cnt[1..^1]}");

var ex = new Explicit(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Explicit : this[Index] · this[Range] 를 직접 받았다");
Console.WriteLine($"  ex[^2]   = {ex[^2]}");
Console.WriteLine($"  ex[1..3] = {ex[1..3]}");
Console.WriteLine($"  ex[2]    = {ex[2]}");

Console.WriteLine("List<int> : BCL 이 같은 계약을 만족하나?");
var list = new List<int> { 1, 2, 3, 4, 5 };
Console.WriteLine($"  List<int>.Slice 가 있나 : {typeof(List<int>).GetMethod("Slice") is not null}");
Console.WriteLine($"  list[^1]    = {list[^1]}");
var sub = list[1..^1];
Console.WriteLine($"  list[1..^1] = [{string.Join(", ", sub)}]  (타입 {sub.GetType().Name})");
sub[0] = -1;
Console.WriteLine($"  sub[0] = -1 뒤 list[1] = {list[1]}   ← 복사다");

class Bag {
    readonly int[] _items;
    public Bag(int[] items) => _items = items;
    public int Length => _items.Length;
    public int this[int i] => _items[i];
    public Bag Slice(int start, int length) => new Bag(_items[start..(start + length)]);
    public override string ToString() => "[" + string.Join(", ", _items) + "]";
}

class Counted {
    readonly int[] _items;
    public Counted(int[] items) => _items = items;
    public int Count => _items.Length;
    public int this[int i] => _items[i];
    public Counted Slice(int start, int length) => new Counted(_items[start..(start + length)]);
    public override string ToString() => "[" + string.Join(", ", _items) + "]";
}

class Explicit {
    readonly int[] _items;
    public Explicit(int[] items) => _items = items;
    public string this[Index i] => $"this[Index] 가 받았다 — {i} → {_items[i.GetOffset(_items.Length)]}";
    public string this[Range r] {
        get { var ol = r.GetOffsetAndLength(_items.Length); return $"this[Range] 가 받았다 — {r} → offset={ol.Offset} length={ol.Length}"; }
    }
}
```

- `Bag` 이 **무엇을 갖고 있어서** 둘 다 되는가?
- ★★ `Counted` 는 `Length` 가 없는데 되는가 — **되면 왜인가**?
- `Explicit` 에서 `ex[2]` 는 어느 인덱서로 가는가?
- ★★★ **`List<int>` 에 `Slice` 가 있는가** — `list[1..^1]` 은 컴파일되는가?
- 그 결과는 **뷰인가 복사인가**?

### 6. 격자를 두 가지로 담으면 (예측)

```csharp
// cs09b-dims.cs
using System;

Warm();

long b0 = GC.GetAllocatedBytesForCurrentThread();
int[,] md = new int[3, 4];
long b1 = GC.GetAllocatedBytesForCurrentThread();
int[][] jag = new int[3][];
for (int i = 0; i < 3; i++) jag[i] = new int[4];
long b2 = GC.GetAllocatedBytesForCurrentThread();
int[] flat = new int[12];
long b3 = GC.GetAllocatedBytesForCurrentThread();

md[1, 2] = 7;
jag[1][2] = 7;

Console.WriteLine($"new int[3,4]                  : +{b1 - b0} 바이트");
Console.WriteLine($"new int[3][] + int[4] 셋       : +{b2 - b1} 바이트");
Console.WriteLine($"new int[12]                   : +{b3 - b2} 바이트");
Console.WriteLine();
Console.WriteLine($"int[,]  : Rank={md.Rank} Length={md.Length} GetLength(0)={md.GetLength(0)} GetLength(1)={md.GetLength(1)}");
Console.WriteLine($"int[][] : Rank={jag.Rank} Length={jag.Length} jag[0].Length={jag[0].Length}");
Console.WriteLine($"md.GetType()  = {md.GetType()}");
Console.WriteLine($"jag.GetType() = {jag.GetType()}");
Console.WriteLine($"md[1,2]={md[1, 2]}   jag[1][2]={jag[1][2]}");
Console.WriteLine();

jag[2] = new int[7];
Console.WriteLine($"jag[2] = new int[7] 뒤 jag[2].Length = {jag[2].Length}   ← 줄마다 길이가 달라도 된다");
Console.WriteLine($"jag[^1].Length = {jag[^1].Length}   ← 바깥 배열에는 ^ 가 된다");
Console.WriteLine($"jag[0..2].Length = {jag[0..2].Length}   ← 바깥 배열에는 .. 도 된다");
Console.WriteLine();

int total = 0;
foreach (int v in md) total += v;
Console.WriteLine($"foreach (int v in md) 의 합 = {total}   ← int[,] 는 원소를 직접 준다");
Console.WriteLine($"md 의 원소 수 {md.Length} = 3 × 4");
foreach (int[] row in jag) Console.WriteLine($"  foreach (int[] row in jag) — row.Length = {row.Length}   ← 줄을 준다");

static void Warm() {
    int[,] w = new int[2, 2];
    int[][] wj = new int[2][];
    wj[0] = new int[2]; wj[1] = new int[2];
    int[] wf = new int[4];
    GC.KeepAlive(w); GC.KeepAlive(wj); GC.KeepAlive(wf);
    GC.GetAllocatedBytesForCurrentThread();
}
```

- ★ **세 줄의 할당 바이트**를 각각 맞힐 수 있는가 — 왜 그렇게 갈리는가?
- `int[,]` 와 `int[][]` 의 `Rank`·`Length` 는 각각 무엇인가?
- `jag[^1]`·`jag[0..2]` 는 되는가?
- `foreach` 가 각각 **무엇을 주는가**?

### 7. 안 되는 자리 (경계)

```csharp
// cs09b-nolength.cs
using System;
using System.Collections.Generic;

var sz = new SizeOnly();
Console.WriteLine(sz[^1]);

var nosl = new NoSlice();
Console.WriteLine(nosl[^1]);
Console.WriteLine(nosl[1..^1]);

var set = new HashSet<int> { 1, 2, 3 };
Console.WriteLine(set[^1]);

class SizeOnly {
    public int Size => 3;
    public int this[int i] => i;
}

class NoSlice {
    public int Length => 3;
    public int this[int i] => i;
}
```

```csharp
// cs09b-dimsfail.cs
using System;

int[,] md = new int[3, 4];
Console.WriteLine(md[^1, 0]);
Console.WriteLine(md[0..1, 0]);
Console.WriteLine(md[^1]);

int[][] jag = new int[3][];
Console.WriteLine(jag[^1]);
```

- 위 블록의 **진단 번호 셋**은 각각 무엇이고 **무엇이 없어서** 나는가?
- ★ `Size` 대신 무슨 이름이라야 하는가 — **둘**이다.
- 아래 블록에서 `md[^1, 0]` 과 `md[^1]` 의 **진단이 왜 다른가**?
- ★ `jag[^1]` 은 왜 진단에 없는가?

### 8. ★★ IL 은 `^` 와 `..` 를 무엇으로 푸는가 (왜)

```csharp
// cs09b-il.cs
Il.Dump(typeof(Probe), "ArrIndex");
Il.Dump(typeof(Probe), "ArrRange");
Il.Dump(typeof(Probe), "SpanRange");
Il.Dump(typeof(Probe), "StrRange");

static class Probe {
    public static int    ArrIndex(int[] a) => a[^1];
    public static int[]  ArrRange(int[] a) => a[1..^1];
    public static System.Span<int> SpanRange(System.Span<int> s) => s[1..^1];
    public static string StrRange(string s) => s[1..^1];
}
```

- ★★★ `a[^1]` 의 IL 에 **`Index` 가 등장하는가**?
- `a[1..^1]` 은 **어느 메서드**를 부르는가?
- ★★★ 같은 `[1..^1]` 이 `Span<int>` 와 `string` 에서는 각각 **무엇**을 부르는가?
- 그 셋이 4번의 바이트 차이를 **설명하는가**?

### 9. ★★ `..` 와 `-` 중 무엇이 먼저 묶이나 (왜)

```csharp
// cs09b-prec.cs
using System;

string s = "x";
var a = 0..1 - s;
var b = (0..1) - s;
var c = 0..(1 - s);
var d = ^1 - s;
var e = ^(1 - s);

int[] arr = { 10, 20, 30, 40, 50 };
var f = arr[1..arr.Length - 1];
Console.WriteLine($"{a} {b} {c} {d} {e} {f}");
```

- ★★★ **여섯 줄의 진단이 가리키는 열**과 **피연산자 타입**을 맞힐 수 있는가?
- 그래서 `0..1 - s` 는 어떻게 묶였는가?
- ★★★ `arr[1..arr.Length - 1]` 은 **컴파일되는가** — 안 되면 무엇으로 고치는가?
- ★ 이 사실을 **값(출력)으로 증명할 수 있는가** — 없다면 왜인가?

### 10. 무엇을 고르나 (경계)

- 부분을 **읽기만** 할 때와 **떼어 보관**할 때 각각 무엇을 쓰나?
- ★ `Span<T>` 를 쓸 수 **없는** 자리는 어디인가?
- `int[,]` 와 `int[][]` 중 어느 쪽을 언제 고르나 — 기준 **셋**을 댈 수 있는가?
- `a[..]` 와 `Clone()` 과 `Array.Copy` 는 각각 무엇이 다른가?

### 11. ★★ Rust · Python · Go 의 슬라이싱과 잇기 (연결)

- ★★★ Rust 의 `&v[1..4]` 와 C# 의 `a[1..4]` 는 **기본값이 어떻게 반대인가**?
- ★★ Python 의 `a[-1]` 과 C# 의 `a[^1]` 은 **타입 층위에서 무엇이 다른가**?
- C# 에서 `a[-1]` 을 쓰면 어떻게 되는가?
- Go 의 「배열」과 C# 의 「배열」이 **가리키는 것이 왜 다른가**?

### 12. ★ 01 · 03 과 잇기 (연결)

- 배열이 **참조 타입**인 것이 4번의 결과에 **어떻게 쓰이는가**?
- `Span<T>` 가 **구조체**인 것이 「+0바이트」와 무슨 상관인가?
- ★ 이 주제에서 **박싱이 난 자리가 있는가** — 없다면 왜인가?
- 할당 바이트를 **증분으로만** 읽는 이유는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
