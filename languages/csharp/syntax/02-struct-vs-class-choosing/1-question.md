# csharp/syntax/02 — `struct` 대 `class` 고르기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> ★★★ **3번이 이 주제의 이유다** — **경고 없이 복사가 생기는 자리**를 맞힐 수 있는지 묻는다.
> ★★ 이 주제의 창은 여섯이다 — 실행 출력 · 컴파일 진단 · ★**「진단 0줄」** · IL · 할당 바이트 · 시간.
> 선행 — [01번](../01-value-types-and-reference-types/). 뒤따르는 것은 [03번](../03-boxing-and-unboxing/)이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 값 타입 배열과 참조 타입 배열 (예측)

```csharp
// cs02b-size.cs
using System;
using System.Runtime.CompilerServices;

Warm();

Console.WriteLine($"Unsafe.SizeOf<Small>()  = {Unsafe.SizeOf<Small>()}");
Console.WriteLine($"Unsafe.SizeOf<Big>()    = {Unsafe.SizeOf<Big>()}");
Console.WriteLine($"Unsafe.SizeOf<BigCls>() = {Unsafe.SizeOf<BigCls>()}  (참조 하나의 크기다)");

long a0 = GC.GetAllocatedBytesForCurrentThread();
var sArr = new Big[1000];
long a1 = GC.GetAllocatedBytesForCurrentThread();
var cArr = new BigCls[1000];
long a2 = GC.GetAllocatedBytesForCurrentThread();
for (int i = 0; i < 1000; i++) cArr[i] = new BigCls();
long a3 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"new Big[1000]           : +{a1 - a0} 바이트  (1000개가 이미 다 들어 있다)");
Console.WriteLine($"new BigCls[1000]        : +{a2 - a1} 바이트  (1000개의 null 이다)");
Console.WriteLine($"  거기에 1000개 채우기  : +{a3 - a2} 바이트");
Console.WriteLine($"sArr[0].A={sArr[0].A} cArr[0]!.A={cArr[0]!.A}");

static void Warm() { var _ = new BigCls[1]; var __ = new Big[1]; GC.GetAllocatedBytesForCurrentThread(); }

struct Small { public int A; public int B; }
struct Big { public long A, B, C, D, E, F, G, H; }
class BigCls { public long A, B, C, D, E, F, G, H; }
```

- `Unsafe.SizeOf<BigCls>()`(클래스)가 답하는 숫자는 **무엇의 크기**인가?
- `new Big[1000]` 과 `new BigCls[1000]` 중 **더 많이 쓰는** 쪽은?
- 그런데 `BigCls` 를 1000개 **채우고 나면** 어느 쪽이 더 많이 쓰나?
- 이 실험으로 「구조체가 빠르다」를 말할 수 있는가 — **무엇을 잰 것**인가?

### 2. ★★ `readonly` 를 붙이면 (예측)

```csharp
// cs02b-readonly-write.cs
readonly struct Money {
    public readonly int Won;
    public Money(int won) { Won = won; }
    public void Add(int d) { Won += d; }        // ① readonly struct 의 메서드가 필드에 쓴다
    public void Reset() { this = default; }     // ② this 에 통째로 쓴다
}

struct Mutable {
    public int Won;
    public void Add(int d) { Won += d; }        // ③ 보통 구조체는 둘 다 된다
    public void Reset() { this = default; }
}

class Program {
    static void Main() {
        var m = new Mutable(); m.Add(1); System.Console.WriteLine(m.Won);
    }
}
```

- 에러가 **몇 개** 나는가 — 각각 어느 줄인가?
- `this = default;` 가 **보통 구조체에서는 되는** 이유는?
- **클래스**에서 같은 코드를 쓰면 어떻게 되는가?

### 3. ★★★ 같은 메서드를 세 번 부르면 (예측)

```csharp
// cs02b-defensive.cs
using System;

var box = new Box();
Console.WriteLine($"[가변 필드]   Next() 세 번 : {box.Plain.Next()} {box.Plain.Next()} {box.Plain.Next()}");
Console.WriteLine($"[가변 필드]   그 뒤 N      : {box.Plain.N}");
Console.WriteLine($"[readonly 필드] Next() 세 번 : {box.Frozen.Next()} {box.Frozen.Next()} {box.Frozen.Next()}");
Console.WriteLine($"[readonly 필드] 그 뒤 N      : {box.Frozen.N}");

var c = new Counter();
Console.WriteLine($"[지역 변수]   Next() 세 번 : {c.Next()} {c.Next()} {c.Next()}");
Console.WriteLine($"[지역 변수]   그 뒤 N      : {c.N}");

var d = new Counter();
Console.WriteLine($"[in 매개변수] Next() 세 번 : {ViaIn(in d)} {ViaIn(in d)} {ViaIn(in d)}");
Console.WriteLine($"[in 매개변수] 그 뒤 N      : {d.N}");

var e = new Counter();
Console.WriteLine($"[ref 매개변수] Next() 세 번 : {ViaRef(ref e)} {ViaRef(ref e)} {ViaRef(ref e)}");
Console.WriteLine($"[ref 매개변수] 그 뒤 N      : {e.N}");

static int ViaIn(in Counter c) { return c.Next(); }
static int ViaRef(ref Counter c) { return c.Next(); }

struct Counter { public int N; public int Next() { return ++N; } }

class Box {
    public Counter Plain = new Counter();
    public readonly Counter Frozen = new Counter();
}
```

- 다섯 자리(지역 변수 · 가변 필드 · `readonly` 필드 · `in` · `ref`)의 출력을 **각각** 맞힐 수 있는가?
- **`1 2 3` 이 아닌** 곳은 어디이고, 그때 `N` 은 얼마인가?
- 그렇게 되는 **이유**가 무엇인가 — 버그인가 규칙인가?
- 고치는 방법 **둘**을 댈 수 있는가?

### 4. ★★ 컴파일러가 무슨 말을 하는가 (경계)

- 3번의 소스를 **최대 경고 수준**(`-warn:9`)으로 컴파일하면 경고가 **몇 줄** 나오는가?
- 「경고 0건」을 셀 때 **같이 봐야 하는 것**은 무엇인가?
- 그러면 이 복사를 **무엇으로** 볼 수 있는가?

### 5. ★★ IL 은 그 복사를 어떻게 적나 (왜)

```csharp
// cs02b-defensive-il.cs
Il.Dump(typeof(Probe), "ViaRef");
Il.Dump(typeof(Probe), "ViaIn");
Il.Dump(typeof(Probe), "ViaInReadonly");

static class Probe {
    public static int ViaRef(ref Counter c) { return c.Next(); }
    public static int ViaIn(in Counter c) { return c.Next(); }
    public static int ViaInReadonly(in RoCounter c) { return c.Peek(); }
}

struct Counter { public int N; public int Next() { return ++N; } }
readonly struct RoCounter { public readonly int N; public int Peek() { return N; } }
```

- 세 메서드의 IL 중 **한 메서드에만 있는 두 줄**은 무엇인가?
- `readonly struct` 로 바꾸면 그 두 줄이 어떻게 되는가?
- 그러면 「`in` 은 복사를 줄인다」는 **언제 참**인가?

### 6. ★★ 구조체의 기본 생성자 (예측)

```csharp
// cs02b-ctor.cs
using System;

var a = new Money();            // 기본 생성자가 있으면 그것이 불린다
var b = default(Money);         // default 는 생성자를 건너뛴다
var c = new Money[2];           // 배열도 건너뛴다
var d = new Money(50);

Console.WriteLine($"new Money()    : Won={a.Won}  Tag={a.Tag ?? "(null)"}");
Console.WriteLine($"default(Money) : Won={b.Won}  Tag={b.Tag ?? "(null)"}");
Console.WriteLine($"new Money[2][0]: Won={c[0].Won}  Tag={c[0].Tag ?? "(null)"}");
Console.WriteLine($"new Money(50)  : Won={d.Won}  Tag={d.Tag ?? "(null)"}");
Console.WriteLine($"a.Equals(b)    : {a.Equals(b)}");

struct Money {
    public int Won = 100;             // C# 10 부터 구조체 필드 초기자가 된다
    public string Tag = "won";
    public Money() { }                // C# 10 부터 구조체 매개변수 없는 생성자가 된다
    public Money(int won) { Won = won; Tag = "won"; }
}
```

- 네 줄의 `Won`·`Tag` 를 **각각** 맞힐 수 있는가?
- `new Money()` 와 `default(Money)` 가 **같은가 다른가**?
- 배열 원소는 어느 쪽을 따르는가?
- 이 문법은 **C# 몇부터**인가 — 그 전에는 무엇이 달랐는가?

### 7. ★★ 기본 `Equals` 는 얼마를 내나 (예측)

```csharp
// cs02b-equals-alloc.cs
using System;

Warm();

var p1 = new Plain { A = 1, B = 2 };
var p2 = new Plain { A = 1, B = 2 };
var f1 = new Fast { A = 1, B = 2 };
var f2 = new Fast { A = 1, B = 2 };
var r1 = new RefField { A = 1, S = "x" };
var r2 = new RefField { A = 1, S = "x" };

long a0 = GC.GetAllocatedBytesForCurrentThread();
bool b1 = p1.Equals(p2);                 // ValueType.Equals(object) — 인자가 박싱된다
long a1 = GC.GetAllocatedBytesForCurrentThread();
bool b2 = f1.Equals(f2);                 // IEquatable<Fast>.Equals(Fast) — 박싱 없음
long a2 = GC.GetAllocatedBytesForCurrentThread();
bool b3 = r1.Equals(r2);                 // 참조 필드가 있는 구조체
long a3 = GC.GetAllocatedBytesForCurrentThread();
bool b4 = object.Equals(p1, p2);         // 양쪽 다 박싱된다
long a4 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"p1.Equals(p2)         = {b1}   할당 +{a1 - a0} 바이트");
Console.WriteLine($"f1.Equals(f2)         = {b2}   할당 +{a2 - a1} 바이트");
Console.WriteLine($"r1.Equals(r2)         = {b3}   할당 +{a3 - a2} 바이트");
Console.WriteLine($"object.Equals(p1, p2) = {b4}   할당 +{a4 - a3} 바이트");

static void Warm() {
    var x = new Plain(); var y = new Plain(); _ = x.Equals(y);
    var u = new Fast(); var v = new Fast(); _ = u.Equals(v);
    var s = new RefField(); var t = new RefField(); _ = s.Equals(t);
    _ = object.Equals(x, y);
    GC.GetAllocatedBytesForCurrentThread();
}

struct Plain { public int A; public int B; }
struct RefField { public int A; public string S; }

struct Fast : IEquatable<Fast> {
    public int A; public int B;
    public bool Equals(Fast other) => A == other.A && B == other.B;
    public override bool Equals(object? o) => o is Fast f && Equals(f);
    public override int GetHashCode() => HashCode.Combine(A, B);
}
```

- 네 줄의 할당 증분을 **각각** 맞힐 수 있는가?
- `Plain`(필드가 전부 `int`)과 `RefField`(`string` 필드가 있다)가 **갈리는** 이유는?
- `Fast`(`IEquatable<Fast>`)가 **0** 인 이유는?
- `p1.Equals(p2)` 에서 **무엇이 몇 개** 박싱되는가?

### 8. ★ 시간으로는 얼마나 갈리나 (왜)

- 7번의 세 구조체를 백만 번씩 비교하면 **어느 쪽이 몇 배** 걸리겠는가?
- 이 측정에서 **근거로 쓸 수 있는 칸**은 ns 절댓값인가 비율인가?
- 「`struct` 가 `class` 보다 빠르다」를 이 측정으로 말할 수 있는가?

### 9. ★★ `record struct` 가 주는 것 (예측)

```csharp
// cs02b-record.cs
using System;

var a = new Money(100, "KRW");
var b = new Money(100, "KRW");
var c = a with { Won = 200 };

Console.WriteLine($"a          : {a}");
Console.WriteLine($"c = a with : {c}");
Console.WriteLine($"a == b     : {a == b}");
Console.WriteLine($"a.Equals(b): {a.Equals(b)}");
Console.WriteLine($"a.GetHashCode() == b.GetHashCode() : {a.GetHashCode() == b.GetHashCode()}");

var (won, cur) = a;
Console.WriteLine($"해체       : won={won} cur={cur}");

Warm(a, b);
long g0 = GC.GetAllocatedBytesForCurrentThread();
bool eq = a.Equals(b);
long g1 = GC.GetAllocatedBytesForCurrentThread();
Console.WriteLine($"a.Equals(b) 할당 : +{g1 - g0} 바이트 (결과 {eq})");

static void Warm(Money x, Money y) { _ = x.Equals(y); GC.GetAllocatedBytesForCurrentThread(); }

readonly record struct Money(int Won, string Currency);
```

- `ToString()`·`==`·해체·`with` 중 **자동으로 오는** 것은 몇 개인가?
- `a.Equals(b)` 의 할당 증분은 얼마인가 — **왜** 그런가?
- `readonly record struct` 의 속성에 대입하면 어떻게 되는가?
- `readonly` 를 빼면 무엇이 달라지는가?

### 10. ★ 구조체가 못 하는 것 (경계)

- 구조체는 **상속**을 할 수 있는가 — **인터페이스 구현**은?
- 인터페이스로 올리면 무슨 일이 생기는가 — 어느 주제가 정본인가?
- 구조체에 `null` 을 넣으려면 무엇이 필요한가?

### 11. 다른 주제와 잇기 (연결)

- 「대입이 무엇을 복사하나」의 정본은 **어느 주제**인가?
- (5)의 **박싱**이 정본이 되는 주제는?
- `ref`/`out`/`in` **자체**의 정본은 목록의 몇 번인가?
- `record` 문법 전반과 `Equals`/`GetHashCode` 계약은 각각 목록의 몇 번인가?
- 「값이냐 헤더냐」가 축인 **다른 언어 갈래**는 어디인가 — 거기에는 **없는** 함정이 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
