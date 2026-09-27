# csharp/syntax/18 — `record` 와 값 동등성·`with` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**record class 와 record struct 를 갈라 답하라**」가 절반이다 — 「record 는 ~다」로 뭉개지 마라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`. 대비는 **javac 21.0.5 · 25.0.1** 이다.
> ★★★ **본체 창은 ③ 리플렉션이다** — 생성 멤버는 **소스에 한 글자도 없다.** ① IL 이 짝이다(「무엇을 한다」).
> ★★ **④ 할당 바이트는 적용이다** — 2×2 판 격자로 쟀고 **시간은 안 쟀다.**
> ★★★ **생성 멤버의 목록은 명세, 그 IL 모양은 구현이다** — 답할 때 둘을 갈라라.
> 선행 — [13번](../13-properties-init-required-field/)(`init`)·[02번](../02-struct-vs-class-choosing/)(`record struct` 고르기). 다음 — 목록의 **19번 주제**(동등성 규칙).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ `record` 한 줄이 만드는 것 (경계)

- `public record RC(string Name, int Age);` 가 만드는 **메서드·생성자**를 전부 대라 — 이름·접근성·`virtual` 여부까지.
- ★★★ `public record struct RS(string Name, int Age);` 에서는 **무엇이 빠지는가** — 왜 빠지는가?
- ★★★ `RS` 의 `set_Age` 는 `RC` 의 `set_Age` 와 **무엇이 다른가**?
- ★ 이 목록 중 **이름 자체가 약속이 아닌** 것은 무엇인가?

### 2. ★★★ `with` 가 부르는 것 (왜)

- `r with { Age = 30 }` 의 IL 은 record class 일 때 **무엇을 먼저 부르고** 그다음 무엇을 부르는가?
- ★★ 그 복제 메서드의 본문은 **어느 생성자**를 부르는가 — 접근성은?
- ★★★ record struct 일 때는 IL 이 어떻게 다른가 — 복제 메서드가 있는가?
- ★ 복제 메서드가 **가상**인 것이 왜 필요한가?

### 3. ★★★ 멤버를 하나도 안 더한 파생 record (예측)

```csharp
// cs18b-contract.cs
using System;
using System.Reflection;
record Pt(int X);
record Tagged(int X) : Pt(X);                  // 멤버를 하나도 안 더한 파생 record
record Pt3(int X, int Z) : Pt(X);
class Program {
    static string Contract(object o) =>
        ((Type)o.GetType().GetProperty("EqualityContract", BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(o)!).Name;
    static void Main() {
        Pt a = new Pt(1);
        Pt b = new Tagged(1);
        Console.WriteLine($"a = {a} · b = {b}");
        Console.WriteLine($"a == b : {a == b} · a.Equals(b) : {a.Equals(b)} · b.Equals(a) : {b.Equals(a)}");
        Console.WriteLine($"a.EqualityContract = {Contract(a)} · b.EqualityContract = {Contract(b)}");
        Pt c = b with { X = 2 };
        Console.WriteLine($"Pt 변수 b 에 with : {c} · c.GetType() = {c.GetType().Name}");
        Pt d = new Pt3(1, 9), e = new Pt3(1, 7);
        Console.WriteLine($"Pt 변수로 받은 Pt3(1,9) == Pt3(1,7) : {d == e}");
    }
}
```

- 다섯 줄에 무엇이 찍히는가?
- ★★★ `a == b` · `a.Equals(b)` · `b.Equals(a)` 는 각각 무엇인가 — **셋이 대칭인가**?
- ★★ `Pt` 변수 `b` 에 `with` 를 하면 결과의 **타입**은?

### 4. ★★ 위치 속성에 대입하기 (예측)

```csharp
// cs18b-mut.cs
record                 RC(int X);
record struct          RS(int X);
readonly record struct RR(int X);
class Program {
    static void Main() {
        var c = new RC(1);
        c.X = 2;
        var s = new RS(1);
        s.X = 2;
        var r = new RR(1);
        r.X = 2;
    }
}
```

- **몇 번째 대입**이 막히는가 — 진단 코드는?
- ★★★ 막히지 **않는** 대입이 있다면 그것은 어느 것이고, 이름에 `record` 가 붙었는데 왜 통과하는가?

### 5. ★★★ 배열·리스트를 담은 record (예측)

```csharp
// cs18b-shallow.cs
using System;
using System.Collections.Generic;
record Arr(int[] Xs);
record Bag(List<int> Xs);
class Program {
    static void Main() {
        Console.WriteLine($"[1] new Arr(new[] {{1,2}}) == new Arr(new[] {{1,2}}) : {new Arr(new[] { 1, 2 }) == new Arr(new[] { 1, 2 })}");
        var shared = new[] { 1, 2 };
        Console.WriteLine($"[2] new Arr(shared) == new Arr(shared)         : {new Arr(shared) == new Arr(shared)}");
        var a = new Bag(new List<int> { 1 });
        var b = a with { };
        b.Xs.Add(2);
        Console.WriteLine($"[3] b.Xs.Add(2) 뒤 a.Xs.Count                   : {a.Xs.Count}");
        Console.WriteLine($"[4] ReferenceEquals(a, b) : {ReferenceEquals(a, b)} · ReferenceEquals(a.Xs, b.Xs) : {ReferenceEquals(a.Xs, b.Xs)}");
        Console.WriteLine($"[5] a == b                                     : {a == b}");
        Console.WriteLine($"[6] a.ToString()                               : {a}");
    }
}
```

- `[1]` 과 `[2]` 는 각각 무엇인가 — 왜 갈리는가?
- ★★★ `[3]` 의 `a.Xs.Count` 는 몇인가?
- ★★ `[4]` 의 두 `ReferenceEquals` 는? `[5]` 의 `a == b` 는?
- ★ `[6]` 이 리스트 **내용**을 보여 주는가?

### 6. ★★ 동등성 옆에 심은 함정들 (예측)

```csharp
// cs18b-probe.cs
using System;
using System.Collections.Generic;

// 탐침 1 — Equals(R1) 를 손으로 쓰고 GetHashCode 는 안 쓴다
record R1(int X) { public virtual bool Equals(R1? o) => o is not null && o.X == X; }

// 탐침 2 — 위치 매개변수가 배열이다
record R2(int[] Xs);

// 탐침 3 — 위치 매개변수가 가변 컬렉션이다
record R3(List<int> Xs);

// 탐침 4 — record struct 를 셋의 키로 쓰고, 넣은 뒤 바꾼다
record struct R4(int X);

// 탐침 5 — double 을 담는다
record R5(double V);

// 탐침 6 — 위치 밖에 가변 속성을 둔다
record R6(int X) { public int Y { get; set; } }

// 탐침 7 — GetHashCode 만 손으로 쓴다
record R7(int X) { public override int GetHashCode() => 0; }

class Program {
    static void Main() {
        Console.WriteLine($"탐침 2 : new R2(new[] {{1}}) == new R2(new[] {{1}}) = {new R2(new[] { 1 }) == new R2(new[] { 1 })}");
        var set = new HashSet<R4>(); var k = new R4(1); set.Add(k); k.X = 2;
        Console.WriteLine($"탐침 4 : 넣은 뒤 k.X = 2 · set.Contains(k) = {set.Contains(k)} · set.Contains(new R4(1)) = {set.Contains(new R4(1))}");
        double x = double.NaN, y = double.NaN;
        Console.WriteLine($"탐침 5 : new R5(x) == new R5(y) = {new R5(x) == new R5(y)} · x == y = {x == y}   (x, y 는 둘 다 double.NaN)");
        var h = new HashSet<R6>(); var r6 = new R6(1); h.Add(r6); r6.Y = 5;
        Console.WriteLine($"탐침 6 : 넣은 뒤 Y = 5 · set.Contains(r6) = {h.Contains(r6)}");
    }
}
```

- `-warn:9` 로 컴파일하면 **어느 탐침**에 진단이 붙는가 — 코드는?
- ★★★ 탐침 4 의 두 `Contains` 는 각각 무엇인가 — **클래스 키였다면** 무엇이 달랐겠는가?
- ★★★ 탐침 5 의 두 비교는 각각 무엇인가 — 왜 반대가 되는가?
- ★★ 탐침 6 의 `Contains` 는 무엇인가 — 위치 매개변수가 아닌 속성도 동등성에 들어가는가?

### 7. ★★ `with`·`==`·`Equals(object)` 의 할당 바이트 (예측)

```csharp
// cs18b-alloc.cs
using System;
record                 RC(int X, int Y);
record struct          RS(int X, int Y);
readonly record struct RR(int X, int Y);
class Program {
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        var c = new RC(1, 2); var s = new RS(1, 2); var r = new RR(1, 2);
        var c2 = new RC(1, 2); var s2 = new RS(1, 2); var r2 = new RR(1, 2);
        Console.WriteLine($"with RC           1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (c with { X = i }).X; })} 바이트");
        Console.WriteLine($"with RS           1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (s with { X = i }).X; })} 바이트");
        Console.WriteLine($"with RR           1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (r with { X = i }).X; })} 바이트");
        Console.WriteLine($"== RC             1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += c == c2 ? 1 : 0; })} 바이트");
        Console.WriteLine($"== RS             1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += s == s2 ? 1 : 0; })} 바이트");
        Console.WriteLine($"== RR             1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += r == r2 ? 1 : 0; })} 바이트");
        Console.WriteLine($"RS.Equals(object) 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += s.Equals((object)s2) ? 1 : 0; })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
```

- 일곱 줄 중 **0 이 아닌** 줄은 어느 것인가 — 한 번에 몇 바이트인가?
- ★★★ `with RC` 와 `with RS` 가 갈리는 이유를 (2)의 IL 로 설명할 수 있는가?
- ★★ `== RS` 와 `RS.Equals(object)` 가 갈리는 이유는?
- ★★ **csc 최적화 × 티어링 네 판**에서 움직인 줄이 있는가 — 이 표로 「`record struct` 가 빠르다」고 말해도 되는가?

### 8. ★★ Java record 에 `with` 를 쓰면 (왜)

- javac 21 은 `p with { x = 9; }` 에 어떤 진단을 내는가 — **어느 단계**에서 막힌 것인가?
- ★ javac 25 에 `--enable-preview --release 25` 를 주면?
- ★ Java 는 대신 무엇을 손으로 쓰는가?

### 9. ★★ 생성된 `Equals(Pt)` 의 첫 세 줄 (왜)

- 생성된 `Equals(Pt)` 의 IL 은 **필드를 비교하기 전에** 무엇을 두 번 확인하는가?
- ★★★ 필드는 **무엇으로** 비교되는가 — 그 선택이 `double` 과 배열 멤버에서 무엇을 낳는가?
- ★★★ 생성된 `op_Equality` 는 무엇을 부르는가 — 그래서 `==` 와 `Equals` 가 **어긋날 수 있는가**?
- ★ `GetHashCode` 가 곱하는 상수는 **언어가 약속한 것**인가?

### 10. ★ record 에 `Equals` 를 손으로 쓰기 (경계)

- `public override bool Equals(object o)` 를 record 에 쓰면? — 진단 코드는?
- ★★ `Equals(R? o)` 를 쓰는 것은 되는가 — 그때 무엇을 **같이** 써야 하고, 안 쓰면 어떤 진단이 나오는가?
- ★ 그렇다면 record 에서 동등성을 바꾸는 **유일한 문**은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- ★★★ `init`·`modreq(IsExternalInit)` 의 정본은 몇 번 주제인가?
- ★★ `readonly record struct` 의 `CS8852` 를 먼저 찍은 것은 몇 번 주제이고, 이 문서가 **처음 찍은** 것은 무엇인가?
- ★★★ 이 문서의 (3) IL 이 목록의 **19번 주제**의 **어떤 사고**가 record 에서 안 나는 이유가 되는가?
- ★ Java record 의 **`invokedynamic` 동등성**은 어느 갈래 몇 번인가? Kotlin `copy` 가 **본문 프로퍼티를 되돌린다**는 것은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
