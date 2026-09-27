# csharp/syntax/01 — 값 타입과 참조 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> 기본 명령은 `csc -out:ex.dll <파일>.cs && dotnet exec ex.dll` 이고, `csc` 는 Roslyn 을 직접 부르는 셸 함수다(서머리 머리말).
> ★★★ **「값 타입은 스택에 있다」를 먼저 의심해라** — 7번에서 **할당 바이트**로 직접 잰다.
> ★ **이 주제의 다섯 번째 창은 `GC.GetAllocatedBytesForCurrentThread()`** 다. 네 번째는 **IL** 이다(9번).
> 선행 — 없음. 뒤따르는 것은 [02번](../02-struct-vs-class-choosing/)·[03번](../03-boxing-and-unboxing/)·[04번](../04-var-and-target-typed-new/)이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 모양의 대입이 다른 일을 한다 (예측)

```csharp
// cs01b-copy.cs
using System;

var s1 = new Point { X = 1, Y = 2 };
var s2 = s1;                       // 구조체 대입
s2.X = 99;

var c1 = new Node { X = 1, Y = 2 };
var c2 = c1;                       // 클래스 대입
c2.X = 99;

Console.WriteLine($"struct : s1.X={s1.X}  s2.X={s2.X}");
Console.WriteLine($"class  : c1.X={c1.X}  c2.X={c2.X}");

BumpStruct(s1);
BumpClass(c1);
Console.WriteLine($"인자 전달 뒤 : s1.X={s1.X}  c1.X={c1.X}");

Console.WriteLine($"ReferenceEquals(c1, c2) : {ReferenceEquals(c1, c2)}");
Console.WriteLine($"c1.Equals(c2)           : {c1.Equals(c2)}");
Console.WriteLine($"s1.Equals(s2)           : {s1.Equals(s2)}");
var s3 = s1;
Console.WriteLine($"s1.Equals(s3)           : {s1.Equals(s3)}");

static void BumpStruct(Point p) { p.X = 1000; }
static void BumpClass(Node n) { n.X = 1000; }

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
```

- 출력 일곱 줄을 **각각** 맞힐 수 있는가?
- `s2.X = 99;` 와 `c2.X = 99;` 가 원본에 닿는가 안 닿는가 — **왜 다른가**?
- `BumpStruct(s1)` 과 `BumpClass(c1)` 중 **원본이 바뀌는** 쪽은?
- `s1.Equals(s2)` 와 `c1.Equals(c2)` 가 **서로 다른 기준**으로 답하는 이유는?

### 2. ★★ 한정자를 붙이면 무엇이 달라지나 (예측)

```csharp
// cs01b-refoutin.cs
using System;

var p = new Point { X = 1 };
var n = new Node { X = 1 };

ByRefStruct(ref p);
ByRefClass(ref n);
Console.WriteLine($"ref 뒤        : p.X={p.X}  n.X={n.X}");

Replace(ref n);
Console.WriteLine($"ref 재대입 뒤 : n.X={n.X}");

ByValue(n);
Console.WriteLine($"값 전달 재대입 뒤 : n.X={n.X}");

Out(out Point q);
Console.WriteLine($"out           : q.X={q.X}");

var big = new Point { X = 7 };
Console.WriteLine($"in 으로 읽기  : {ReadOnly(in big)}");

static void ByRefStruct(ref Point p) { p.X = 42; }
static void ByRefClass(ref Node n) { n.X = 42; }
static void Replace(ref Node n) { n = new Node { X = 777 }; }
static void ByValue(Node n) { n = new Node { X = -1 }; }
static void Out(out Point p) { p = new Point { X = 5 }; }
static int ReadOnly(in Point p) { return p.X; }

struct Point { public int X; }
class Node { public int X; }
```

- 출력 다섯 줄을 맞힐 수 있는가?
- `Replace(ref n)` 뒤의 `n.X` 는 얼마인가 — **그 다음 줄**의 `ByValue(n)` 뒤에는?
- **참조 타입에 `ref` 를 붙이는 것**이 의미가 있는가 — 있다면 무엇이 달라지는가?
- `out` 이 `ref` 와 다른 점 **둘**은?

### 3. ★ `in` 매개변수에 쓰면 (경계)

- 컴파일이 되는가 안 되는가 — 진단 코드와 문구는?
- `in` 은 **성능 최적화**인가 **타입 수준의 약속**인가?
- `in` 을 붙였는데 **오히려 복사가 늘어나는** 경우가 있는가 — 어느 주제가 그것의 정본인가?

### 4. ★★ 이 다섯 줄을 던지면 (예측)

```csharp
// cs01b-null.cs
struct Point { public int X; }

class Program {
    static void Main() {
        int i = null;
        Point p = null;
        string s = null;
        object o = null;
        int? q = null;
        System.Console.WriteLine($"{i} {p} {s} {o} {q}");
    }
}
```

- 다섯 줄 중 **에러가 나는** 것은 몇 줄인가?
- 진단 문구가 대는 **이유**는 무엇인가?
- `string s = null;` 이 **경고도 안 나는** 이유는?

### 5. ★★ 이것이 값 타입인가 참조 타입인가 (예측)

```csharp
// cs01b-string.cs
using System;

string a = "hello";
string b = "hello";
string c = new string(['h', 'e', 'l', 'l', 'o']);
string d = a;

Console.WriteLine($"a == b                  : {a == b}");
Console.WriteLine($"a == c                  : {a == c}");
Console.WriteLine($"ReferenceEquals(a, b)   : {ReferenceEquals(a, b)}");
Console.WriteLine($"ReferenceEquals(a, c)   : {ReferenceEquals(a, c)}");
Console.WriteLine($"ReferenceEquals(a, d)   : {ReferenceEquals(a, d)}");

string e = a;
a = a.ToUpper();                 // 바꾼 것처럼 보이는 자리
Console.WriteLine($"a={a}  e={e}");
Console.WriteLine($"ReferenceEquals(a, e)   : {ReferenceEquals(a, e)}");

object boxed1 = 5;
object boxed2 = 5;
Console.WriteLine($"ReferenceEquals(5, 5)   : {ReferenceEquals(boxed1, boxed2)}");
```

- 여덟 줄을 **각각** 맞힐 수 있는가?
- `a == c` 와 `ReferenceEquals(a, c)` 가 **갈리는** 이유는?
- `a = a.ToUpper()` 뒤에 `e` 가 무엇을 담고 있는가 — **왜**인가?
- **마지막 줄**이 Java 와 갈리는 자리다 — Java 였다면 무엇이 나왔겠는가?

### 6. ★ `int?` 는 무엇인가 (경계)

- `typeof(int?)` 가 무엇을 답하는가 — **값 타입인가 참조 타입인가**?
- `object o = (int?)5;` 한 뒤 `o.GetType()` 은 무엇을 답하는가?
- 값이 없는 `int?` 의 `.Value` 를 읽으면 무슨 예외가 나는가?

### 7. ★★★ 힙을 쓰나 안 쓰나 (예측)

```csharp
// cs01b-alloc.cs
using System;

// 워밍업 — 첫 호출이 끌고 오는 할당을 측정 밖으로 뺀다.
Warm();

long a0 = GC.GetAllocatedBytesForCurrentThread();
var p = new Point { X = 1, Y = 2 };
long a1 = GC.GetAllocatedBytesForCurrentThread();
var n = new Node { X = 1, Y = 2 };
long a2 = GC.GetAllocatedBytesForCurrentThread();
var arrS = new Point[1000];
long a3 = GC.GetAllocatedBytesForCurrentThread();
var arrC = new Node[1000];
long a4 = GC.GetAllocatedBytesForCurrentThread();
for (int i = 0; i < 1000; i++) arrC[i] = new Node();
long a5 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"new Point()      : +{a1 - a0} 바이트");
Console.WriteLine($"new Node()       : +{a2 - a1} 바이트");
Console.WriteLine($"new Point[1000]  : +{a3 - a2} 바이트");
Console.WriteLine($"new Node[1000]   : +{a4 - a3} 바이트");
Console.WriteLine($"거기에 Node 1000개 채우기 : +{a5 - a4} 바이트");
Console.WriteLine($"(합계는 흔들리는 칸이다 — 읽을 것은 0 이냐 아니냐와 증분이다)");
Console.WriteLine($"p.X={p.X} n.X={n.X} arrS.Length={arrS.Length} arrC[0]!.X={arrC[0]!.X}");

static void Warm() { var _ = new Node(); var __ = new Point[1]; GC.GetAllocatedBytesForCurrentThread(); }

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
```

- 다섯 증분을 **각각** 맞힐 수 있는가 — 특히 **첫 줄**?
- `new Point[1000]` 과 `new Node[1000]` 의 증분이 **같은가 다른가** — 그 숫자가 **같은 뜻**인가?
- 마지막 줄(`Node` 1000개 채우기)이 **왜 따로 드는가**?
- 이 실험에서 **근거로 쓸 수 있는 칸**은 절댓값인가 증분인가?

### 8. ★★ 구조체의 크기를 재려면 (예측)

```csharp
// cs01b-sizeof.cs
struct Point { public int X = 0; public int Y = 0; public Point() { } }
struct Holder { public string S = ""; public Holder() { } }

class Program {
    static void Main() {
        int a = sizeof(int);
        int b = sizeof(Point);
        int c = sizeof(Holder);
        int d = sizeof(string);
        System.Console.WriteLine($"{a} {b} {c} {d}");
    }
}
```

- 네 줄 중 **에러가 나는** 것은 몇 줄인가?
- `sizeof(int)` 은 되는데 `sizeof(Point)` 는 왜 안 되는가?
- 안전한 문맥에서 크기를 묻는 **대안**은 무엇인가?
- `Unsafe.SizeOf<Node>()`(클래스)가 답하는 숫자는 **무엇의 크기**인가?

### 9. ★★ IL 은 둘을 어떻게 적나 (왜)

```csharp
// cs01b-il.cs
Il.Dump(typeof(Probe), "MakeStruct");
Il.Dump(typeof(Probe), "MakeClass");
Il.Dump(typeof(Probe), "CopyStruct");
Il.Dump(typeof(Probe), "CopyClass");

static class Probe {
    public static Point MakeStruct() { var p = new Point(); p.X = 1; return p; }
    public static Node MakeClass() { var n = new Node(); n.X = 1; return n; }
    public static int CopyStruct(Point a) { var b = a; b.X = 9; return a.X; }
    public static int CopyClass(Node a) { var b = a; b.X = 9; return a.X; }
}

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
```

- 값 타입을 만들 때와 참조 타입을 만들 때 **다른 명령**이 나오는가?
- 대입(`var b = a;`)에서는 **다른 명령**이 나오는가?
- 그러면 「무엇이 복사되는지」를 정하는 것은 **명령인가 타입인가**?
- 이 절로 「구조체 대입이 느리다」를 **증명할 수 있는가**?

### 10. ★ 동일성은 무엇으로 판정하나 (경계)

- `ReferenceEquals` 에 **값 타입**을 넣으면 무슨 일이 생기는가?
- `ReferenceEquals(5, 5)` 는 참인가 거짓인가 — **왜**인가?
- 「같은 값이냐」와 「같은 객체냐」를 **각각** 무엇으로 묻는가?

### 11. 다른 주제와 잇기 (연결)

- 「`struct` 를 언제 고르나」의 정본은 **어느 주제**인가?
- 「값 타입이 `object` 로 올라갈 때 무슨 일이 나나」의 정본은?
- `ref`/`out`/`in` **자체**의 정본은 목록의 몇 번인가?
- 「값이냐 참조냐」라는 **개념 자체**는 이 갈래 밖 어디가 정본인가?
- C++ 의 참조/포인터와 **축이 어떻게 다른가** — 어느 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
