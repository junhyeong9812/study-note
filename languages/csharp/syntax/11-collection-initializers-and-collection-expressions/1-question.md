# csharp/syntax/11 — 컬렉션 초기화와 컬렉션 식(C# 12) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「무엇이 만들어지나」를 맞히는 것**이 절반이다 —
> 출력은 어느 대상 타입에서도 같으므로 **IL 과 할당 바이트로** 답해야 한다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다(MSBuild 안 씀) · `-langversion:latest` · `-preferreduilang:en-US`.
> ★★ **네 번째·다섯 번째 창은 「IL」과 「할당 바이트」다** — 이 주제의 중심이 그 둘이다.
> ★ **「부적용인 창」이 있다** — **예외 전문**. 컬렉션 식은 **런타임에 던질 자리가 원리적으로 없다**
> (대상 타입이 안 맞으면 전부 컴파일 에러다). **「안 쟀다」가 아니라 「실을 전문이 없다」다.**
> ★★★ **할당 바이트에는 측정 조건이 붙는다** — `csc -optimize` 여부와 **티어드 JIT** 여부로 **네 판**을 돌렸다(9번).
> 선행 — [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)(무엇을 고르나)·[03번](../03-boxing-and-unboxing/)(할당 바이트 재는 법)·[09번](../09-arrays-index-and-range/)(`..` 의 다른 뜻).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★ `=` 하나를 넣고 빼면 (예측)

```csharp
// cs11b-objinit.cs
using System;
using System.Collections.Generic;

var p = new Point { X = 1, Y = 2 };
Console.WriteLine($"객체 초기화자           : {p}");

var box = new Box { Label = "바깥", Inner = { X = 7, Y = 8 } };
Console.WriteLine($"중첩 초기화자(=  없음)  : {box.Label} / {box.Inner}   ← Inner 를 새로 만들지 않고 이미 있는 것을 고친다");

var box2 = new Box { Label = "바깥2", Inner = new Point { X = 9, Y = 9 } };
Console.WriteLine($"중첩 초기화자(= 있음)   : {box2.Label} / {box2.Inner}   ← 새로 만들어 갈아 끼운다");

var tags = new Box { Label = "리스트", Tags = { "a", "b" } };
Console.WriteLine($"중첩 컬렉션 초기화자    : {tags.Label} / [{string.Join(", ", tags.Tags)}]   ← Add 를 두 번 부른다");

var old = new Point { X = 5, Y = 5 };
var q = old;
try { q = new Point { X = 1, Y = Boom() }; }
catch (InvalidOperationException) { Console.WriteLine($"초기화자가 도중에 던지면  : q = {q}   ← 옛 객체가 그대로다(변수는 끝에 가서야 대입된다)"); }

static int Boom() => throw new InvalidOperationException("터진다");

class Point { public int X { get; set; } public int Y { get; set; } public override string ToString() => $"({X}, {Y})"; }
class Box {
    public string Label { get; set; } = "";
    public Point Inner { get; set; } = new Point();
    public List<string> Tags { get; } = new List<string>();
}
```

- `box.Inner` 와 `box2.Inner` 의 값을 각각 맞힐 수 있는가 — **무엇이 다른가**?
- ★ `tags.Tags` 에 `a`·`b` 가 들어간 것은 **무슨 메서드**가 불렸기 때문인가?
- ★★ 초기화자가 도중에 던졌을 때 **`q` 의 값**은 무엇인가 — 왜 그런가?
- ★★ 객체 초기화자의 IL 이 손으로 쓴 판과 **다른 한 가지**는 무엇인가?

### 2. ★★★ 내 타입에 `{ 1, 2 }` 를 붙이면 (예측)

```csharp
// cs11b-add.cs
using System;
using System.Collections;
using System.Collections.Generic;

var a = new NoAdd { 1, 2 };
var b = new NoEnumerable { 1, 2 };
Console.WriteLine($"{a} {b}");

class NoAdd : IEnumerable {
    public IEnumerator GetEnumerator() => new List<int>().GetEnumerator();
}
class NoEnumerable {
    public void Add(int x) { }
}
```

- **에러가 몇 건** 나고, **코드는 무엇**인가?
- ★★ `NoAdd` 쪽 에러가 **두 건**인 이유는?
- ★★★ `Add` 가 **그 타입의 메서드가 아니어도** 컬렉션 초기화자가 성립하는가?
- ★ `{ "a", 1 }` 처럼 **원소가 둘인 꼴**은 무엇을 찾는가?

### 3. ★ 중복 키를 두 꼴로 적으면 (예측)

```csharp
// cs11b-idx.cs
using System;
using System.Collections.Generic;

try {
    var d1 = new Dictionary<string, int> { { "a", 1 }, { "a", 2 } };
    Console.WriteLine("Add 꼴  { \"a\", 1 }, { \"a\", 2 }  → 통과했다. 값 = " + d1["a"]);
} catch (ArgumentException ex) {
    Console.WriteLine("Add 꼴  { \"a\", 1 }, { \"a\", 2 }  → " + ex.GetType().Name + ": " + ex.Message);
}

var d2 = new Dictionary<string, int> { ["a"] = 1, ["a"] = 2 };
Console.WriteLine("인덱스 꼴 [\"a\"] = 1, [\"a\"] = 2  → 통과. 값 = " + d2["a"] + ", Count = " + d2.Count);
Console.WriteLine();

var grid = new Grid { [0] = "영", [2] = "둘" };
Console.WriteLine("인덱스 초기화자는 내 타입에도 붙는다 : " + grid.Log);
Console.WriteLine();

var byAdd = new List<int> { 1, 2, 3 };
var byExpr = new List<int>();
Console.WriteLine("컬렉션 초기화자는 Add 를 부르므로 List 의 Capacity 가 " + byAdd.Capacity + " 다");
List<int> byColl = [1, 2, 3];
Console.WriteLine("컬렉션 식은 개수를 미리 알아 Capacity 가 " + byColl.Capacity + " 다");
Console.WriteLine("  같은 세 값인데 빈 자리가 " + (byAdd.Capacity - byAdd.Count) + " 대 " + (byColl.Capacity - byColl.Count) + " 로 다르다");
GC.KeepAlive(byExpr);

class Grid {
    public string Log = "";
    public string this[int i] { get => Log; set => Log += $"set_Item({i}, {value}) "; }
}
```

- `{ "a", 1 }, { "a", 2 }` 와 `["a"] = 1, ["a"] = 2` 는 각각 **어떻게 되는가**?
- ★ 뒤쪽의 `Count` 와 값은?
- ★★ `new List<int> { 1, 2, 3 }` 과 `List<int> x = [1, 2, 3]` 의 **`Capacity`** 는 각각 얼마인가 — 왜 다른가?

### 4. ★★★ 같은 오른쪽, 다른 왼쪽 (예측)

```csharp
// cs11b-expr.cs
using System;
using System.Collections.Generic;

int[] other = [30, 40];
int[] a = [10, 20, ..other, 50];
Console.WriteLine($"int[] a = [10, 20, ..other, 50]  →  [{string.Join(", ", a)}]");

List<int> l = [1, ..a, 99];
Console.WriteLine($"List<int> l = [1, ..a, 99]       →  [{string.Join(", ", l)}]  Count={l.Count}");

Span<int> s = [7, 8, 9];
Console.WriteLine($"Span<int> s = [7, 8, 9]          →  [{string.Join(", ", s.ToArray())}]  Length={s.Length}");

IEnumerable<int> e = [1, 2, 3];
Console.WriteLine($"IEnumerable<int> e = [1, 2, 3]   →  런타임 타입 {e.GetType().Name}");

int[] empty = [];
Console.WriteLine($"int[] empty = []                 →  Length={empty.Length}  Array.Empty 와 같은 객체 = {ReferenceEquals(empty, Array.Empty<int>())}");

string[] words = ["하나", "둘"];
string[] more = [..words, "셋"];
Console.WriteLine($"[..words, \"셋\"]                   →  [{string.Join(", ", more)}]");

List<int> src = [1, 2, 3];
int[] fromList = [..src];
Console.WriteLine($"[..src] 에서 src 가 List 여도     →  int[] {{{string.Join(", ", fromList)}}}");

int[] nested = [..(int[])[1, 2], ..(List<int>)[3, 4]];
Console.WriteLine($"서로 다른 컬렉션을 한 줄에 퍼뜨리면 →  [{string.Join(", ", nested)}]");
```

- `IEnumerable<int> e = [1, 2, 3]` 의 **런타임 타입 이름**은 무엇인가?
- ★★★ `int[] empty = []` 이 `Array.Empty<int>()` 와 **같은 객체인가**?
- ★ `[..src]` 에서 `src` 가 `List<int>` 인데 왼쪽이 `int[]` 면 **무엇이 나오나**?
- ★★ IL 로 보면 `List<int> x = [1, 2, 3]` 은 **`Add` 를 몇 번** 부르는가?
- ★★ `Span<int> s = [1, 2, 3]` 의 IL 에 **`newarr` 이 있는가**?

### 5. ★★★ 대상 타입별 할당 바이트 (예측)

```csharp
// cs11b-alloc.cs
using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Runtime.CompilerServices;

class P {
    [MethodImpl(MethodImplOptions.NoInlining)] static int[] Arr() => [1, 2, 3];
    [MethodImpl(MethodImplOptions.NoInlining)] static int[] ArrVar(int a, int b, int c) => [a, b, c];
    [MethodImpl(MethodImplOptions.NoInlining)] static List<int> Lst() => [1, 2, 3];
    [MethodImpl(MethodImplOptions.NoInlining)] static List<int> LstOld() => new List<int> { 1, 2, 3 };
    [MethodImpl(MethodImplOptions.NoInlining)] static int Spn() { Span<int> s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int Ros() { ReadOnlySpan<int> s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static IEnumerable<int> Iface() => [1, 2, 3];
    [MethodImpl(MethodImplOptions.NoInlining)] static int Imm() { ImmutableArray<int> a = [1, 2, 3]; return a[0] + a[1] + a[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int[] Spread(int[] o) => [1, 2, ..o];
    [MethodImpl(MethodImplOptions.NoInlining)] static int[] EmptyArr() => [];
    [MethodImpl(MethodImplOptions.NoInlining)] static List<int> EmptyLst() => [];
    [MethodImpl(MethodImplOptions.NoInlining)] static IEnumerable<int> EmptyIface() => [];
    [MethodImpl(MethodImplOptions.NoInlining)] static int EmptySpn() { Span<int> s = []; return s.Length; }

    static long Measure(Action f) {
        for (int i = 0; i < 10; i++) f();
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 100; i++) f();
        long b1 = GC.GetAllocatedBytesForCurrentThread();
        return (b1 - b0) / 100;
    }

    static void Main() {
        int[] o = [4, 5];
        int acc = 0;
        Console.WriteLine($"int[]             x = [1, 2, 3] : {Measure(() => GC.KeepAlive(Arr()))} 바이트/회");
        Console.WriteLine($"int[]             x = [a, b, c] : {Measure(() => GC.KeepAlive(ArrVar(1, 2, 3)))} 바이트/회   ★ 같은 모양인데 다르다");
        Console.WriteLine($"List<int>         x = [1, 2, 3] : {Measure(() => GC.KeepAlive(Lst()))} 바이트/회");
        Console.WriteLine($"new List<int> {{ 1, 2, 3 }}       : {Measure(() => GC.KeepAlive(LstOld()))} 바이트/회");
        Console.WriteLine($"Span<int>         x = [1, 2, 3] : {Measure(() => acc += Spn())} 바이트/회   ★ 스택에 담는다");
        Console.WriteLine($"ReadOnlySpan<int> x = [1, 2, 3] : {Measure(() => acc += Ros())} 바이트/회   ★ 배열이 없는데도 낸다");
        Console.WriteLine($"IEnumerable<int>  x = [1, 2, 3] : {Measure(() => GC.KeepAlive(Iface()))} 바이트/회");
        Console.WriteLine($"ImmutableArray<int> x=[1, 2, 3] : {Measure(() => acc += Imm())} 바이트/회");
        Console.WriteLine($"int[]  x = [1, 2, ..other]      : {Measure(() => GC.KeepAlive(Spread(o)))} 바이트/회");
        Console.WriteLine();
        Console.WriteLine($"int[]             x = []        : {Measure(() => GC.KeepAlive(EmptyArr()))} 바이트/회");
        Console.WriteLine($"IEnumerable<int>  x = []        : {Measure(() => GC.KeepAlive(EmptyIface()))} 바이트/회");
        Console.WriteLine($"Span<int>         x = []        : {Measure(() => acc += EmptySpn())} 바이트/회");
        Console.WriteLine($"List<int>         x = []        : {Measure(() => GC.KeepAlive(EmptyLst()))} 바이트/회   ★ 여기만 0 이 아니다");
        Console.WriteLine();
        Console.WriteLine($"런타임 타입 — IEnumerable<int> x = [1,2,3] 은 {Iface().GetType().Name}");
        Console.WriteLine($"런타임 타입 — IEnumerable<int> x = []      은 {EmptyIface().GetType().Name}");
        Console.WriteLine($"List<int> x = [1,2,3] 의 Capacity = {Lst().Capacity} · new List<int>{{1,2,3}} 의 Capacity = {LstOld().Capacity}");
        Console.WriteLine($"int[] x = [] 은 Array.Empty 와 같은 객체 = {ReferenceEquals(EmptyArr(), Array.Empty<int>())}   (acc={acc % 2})");
    }
}
```

- 아홉 줄의 **바이트/회**를 맞힐 수 있는가 — 특히 `Span` 과 `ReadOnlySpan`?
- ★★★ `int[] x = [1, 2, 3]` 과 `int[] x = [a, b, c]` 중 **큰 쪽**은? 차이는 얼마인가?
- ★★★ **빈 것 네 줄** 중 **0 이 아닌 하나**는 무엇인가?
- ★ `int[] x = [1, 2, ..other]` 가 **중간 리스트를 만드는가**?
- ★ `List<int> x = [1, 2, 3]` 과 `new List<int> { 1, 2, 3 }` 의 바이트는 **같은가 다른가**?

### 6. ★★ 원소가 `byte` 면 (예측)

```csharp
// cs11b-blob.cs
using System;
using System.Runtime.CompilerServices;

class P {
    [MethodImpl(MethodImplOptions.NoInlining)] static int RosByte() { ReadOnlySpan<byte> s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int RosInt() { ReadOnlySpan<int> s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int ArrByte() { byte[] s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int ArrInt() { int[] s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int NewByte() { byte[] s = new byte[3]; return s.Length; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int NewInt() { int[] s = new int[3]; return s.Length; }

    static long Measure(Func<int> f) {
        for (int i = 0; i < 10; i++) f();
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 100; i++) f();
        long b1 = GC.GetAllocatedBytesForCurrentThread();
        return (b1 - b0) / 100;
    }

    static void Main() {
        long rb = Measure(RosByte), ri = Measure(RosInt);
        long ab = Measure(ArrByte), ai = Measure(ArrInt);
        long nb = Measure(NewByte), ni = Measure(NewInt);
        Console.WriteLine($"new byte[3]                    : {nb,4} 바이트/회   ← 배열 자체의 값");
        Console.WriteLine($"new int[3]                     : {ni,4} 바이트/회   ← 배열 자체의 값");
        Console.WriteLine($"byte[] x = [1, 2, 3]           : {ab,4} 바이트/회   (배열 {nb} + {ab - nb})");
        Console.WriteLine($"int[]  x = [1, 2, 3]           : {ai,4} 바이트/회   (배열 {ni} + {ai - ni})");
        Console.WriteLine($"ReadOnlySpan<byte> x = [1,2,3] : {rb,4} 바이트/회   ← 배열이 없다");
        Console.WriteLine($"ReadOnlySpan<int>  x = [1,2,3] : {ri,4} 바이트/회   ← 배열이 없는데도 낸다");
        Console.WriteLine();
        Console.WriteLine($"★ 배열 값을 뺀 나머지가 상수 블록 경로의 몫이다 — byte {ab - nb} · int {ai - ni} · ROSpan<byte> {rb} · ROSpan<int> {ri}");
    }
}
```

- `ReadOnlySpan<byte>` 와 `ReadOnlySpan<int>` 의 바이트가 **같은가 다른가**?
- ★★★ 그 차이를 **IL 의 어느 명령 하나**가 설명하는가?
- ★ `byte[] x = [1, 2, 3]` 에서 **배열 값을 뺀 나머지**는 얼마인가 — `int[]` 와 같은가?

### 7. ★ 대상 타입이 없으면 (경계)

- `var x = [];` 와 `var y = [1, 2, 3];` 은 컴파일되는가 — **진단 코드**는?
- ★★ `object o = [1, 2, 3];` 은 **같은 코드**인가 다른 코드인가 — 문구는 무엇을 말하는가?
- ★ 그래서 컬렉션 식이 **런타임에 실패하지 않는** 이유를 한 줄로 말할 수 있는가?

### 8. ★★ `..` 는 어디까지 묶이나 (경계)

- `[.. 1..3]` 과 `[..(1..3)]` 은 **같은 에러**인가 — **`(행,열)`** 은 각각 얼마인가?
- ★★★ 이 질문을 **값으로는 못 가르는** 이유는?
- ★ `[.. a[1..3]]` 은 왜 통과하는가 — 같은 `..` 가 **한 줄에서 두 뜻**으로 쓰이는 자리를 짚을 수 있는가?
- ★ 스프레드가 피연산자에 요구하는 것은 무엇인가?

### 9. ★★★ 판을 바꾸면 무엇이 움직이나 (경계)

- `csc -optimize` 와 `DOTNET_TieredCompilation=0` 으로 **네 판**을 돌리면 **움직이는 칸이 몇 개**인가?
- ★★★ 그 움직이는 폭이 **전부 같은 수의 배수**인데, 그 수는 얼마이고 **무엇의 값**인가?
- ★★★ **네 판에서 안 움직인 것**은 무엇인가 — 그것이 왜 결론인가?
- ★★ `-optimize` 만으로는 안 되고 `TC=0` 까지 필요했던 이유는?
- ★ `-warn:9` 로 탐침 여덟을 물으면 **몇 건**이 나오는가?

### 10. 다른 주제와 잇기 (연결)

- **무엇을 고르나**의 정본은 몇 번 주제인가 — 「넣는 법 셋」은 거기서 어떻게 갈리나?
- **할당 바이트 재는 법과 `cs-il.cs`** 는 몇 번 주제에서 왔는가?
- **`..` 가 범위 연산자인** 주제는 몇 번인가?
- **`var` 가 오른쪽에서 타입을 받는데 컬렉션 식은 왼쪽에서 받는다** — 같은 집안의 문법은 몇 번 주제인가?
- ★★ **`Span<T>` 가 0바이트인 이유**의 정본은 몇 번 주제인가?
- ★★ C++ 의 `{}` 초기화와 **방향이 어떻게 반대인가** — 어느 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
