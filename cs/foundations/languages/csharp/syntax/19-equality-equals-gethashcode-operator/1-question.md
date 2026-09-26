# csharp/syntax/19 — 동등성 규칙 — `Equals`/`GetHashCode`/`==` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제는 **계약형**이다 — 「조항 세기」보다 「**어기면 무엇이 출력되나**」를 묻는다. 예외는 **안 난다** — 값만 틀린다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`.
> ★★★ **본체 창은 실행 출력 격자다**(계약 위반 × 자료구조) — ② 진단이 짝이고, ① IL 이 `==` 의 정체를 보인다.
> ★★ **④ 할당 바이트는 2×2 판 격자**로 쟀고 **시간은 안 쟀다.**
> ★★ **해시 값은 한 번도 찍지 않았다** — 「같나 다르나」와 **가짓수**만 찍었다.
> 선행 — [18번](../18-record-value-equality-and-with/)(★★★ record 가 만드는 `==`·`Equals` 의 IL)·[10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)(`CS0659` · `Count = 3`)·[02번](../02-struct-vs-class-choosing/)(구조체 `Equals` 의 박싱).
> 대비 — Python 갈래 **30번** · Rust 갈래 **28번** · Kotlin 갈래 **32번**(링크는 [2-summary.md](2-summary.md) 머리말).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 계약을 하나씩 깬 키를 셋과 리스트에 넣으면 (예측)

```csharp
// cs19b-grid.cs
using System;
using System.Collections.Generic;

// R1 — 반사성을 깬다: Equals 가 늘 false · 해시는 정직하다
class R1 { public int V; public R1(int v) => V = v;
    public override bool Equals(object? o) => false;
    public override int GetHashCode() => V; }

// R2 — GetHashCode 를 안 고친다: Equals 만 값으로
#pragma warning disable CS0659
class R2 { public int V; public R2(int v) => V = v;
    public override bool Equals(object? o) => o is R2 r && r.V == V; }
#pragma warning restore CS0659

// R3 — 넣은 뒤 바꾼다: record 의 가변 필드
record R3 { public int V; public R3(int v) => V = v; }

// R4 — 추이성을 깬다: 차이 1 이하면 같다 · 해시는 전부 0 (해시 규약은 지킨다)
class R4 { public int V; public R4(int v) => V = v;
    public override bool Equals(object? o) => o is R4 r && Math.Abs(r.V - V) <= 1;
    public override int GetHashCode() => 0; }

// R5 — 대칭성을 깬다: 문자열과도 같다고 답한다
class R5 { public string S; public R5(string s) => S = s;
    public override bool Equals(object? o) => o switch {
        R5 r     => string.Equals(r.S, S, StringComparison.OrdinalIgnoreCase),
        string t => string.Equals(t, S, StringComparison.OrdinalIgnoreCase),
        _        => false };
    public override int GetHashCode() => S.ToLowerInvariant().GetHashCode(); }

// R6 — 대조군
record R6(int V);

class Program {
    static int split, cells;
    static void Row(string name, Func<object> make, Action<object>? mutate = null) {
        var k = make();
        var set = new HashSet<object> { k };
        set.Add(make());
        mutate?.Invoke(k);
        var list = new List<object> { k };
        bool sk = set.Contains(k), sn = set.Contains(make());
        bool lk = list.Contains(k), ln = list.Contains(make());
        cells += 2;
        if (sk != lk) split++;
        if (sn != ln) split++;
        Console.WriteLine($"{name,-3}| Count={set.Count} | set.Contains(k)={sk,-5} | set.Contains(new)={sn,-5} | list.Contains(k)={lk,-5} | list.Contains(new)={ln,-5}");
    }
    static void Main() {
        Row("R1", () => new R1(1));
        Row("R2", () => new R2(1));
        Row("R3", () => new R3(1), o => ((R3)o).V = 2);
        Row("R6", () => new R6(1));
        Console.WriteLine($"set 과 list 가 갈린 칸 {split} / {cells}");
        var a = new HashSet<object>(); foreach (var v in new[] { 1, 3, 2 }) a.Add(new R4(v));
        var b = new HashSet<object>(); foreach (var v in new[] { 2, 1, 3 }) b.Add(new R4(v));
        Console.WriteLine($"R4 | order 1,3,2 -> Count={a.Count} | order 2,1,3 -> Count={b.Count}");
        var s1 = new HashSet<object> { new R5("A") };
        var s2 = new HashSet<object> { "a" };
        Console.WriteLine($"R5 | {{R5(A)}}.Contains(\"a\")={s1.Contains("a")} | {{\"a\"}}.Contains(R5(A))={s2.Contains(new R5("A"))}");
        Console.WriteLine($"R5 | R5(A).Equals(\"a\")={new R5("A").Equals("a")} | \"a\".Equals(R5(A))={"a".Equals(new R5("A"))}");
    }
}
```

- `R1`·`R2`·`R3`·`R6` 네 줄의 **`Count` 와 네 `Contains`** 를 전부 채울 수 있는가?
- ★★★ `set 과 list 가 갈린 칸 N / M` 의 N 과 M 은?
- ★★★ `R1` 의 `set.Contains(k)` — **넣은 바로 그 객체**로 물었다 — 는 무엇인가?
- ★★ `R4` 의 두 `Count` 는? 왜 넣는 순서가 답을 바꾸는가?
- ★★★ `R5` 의 두 `Contains` 는 각각 무엇인가 — 마지막 줄의 두 `Equals` 와 어떻게 이어지는가?

### 2. ★★★ `==` 와 `Equals` 를 여러 타입으로 (예측)

```csharp
// cs19b-opeq.cs
using System;
class Money {
    public int Won;
    public Money(int w) => Won = w;
    public override bool Equals(object? o) => o is Money m && m.Won == Won;
    public override int GetHashCode() => Won;
}
static class Probe {
    public static bool A(Money a, Money b)   => a == b;
    public static bool B(string a, string b) => a == b;
    public static bool C(object a, object b) => a == b;
    public static bool D<T>(T a, T b) where T : class => a == b;
}
class Program {
    static void Main() {
        var a = new Money(100); var b = new Money(100);
        Console.WriteLine($"[1] Money  a == b           : {a == b}");
        Console.WriteLine($"[2] Money  a.Equals(b)      : {a.Equals(b)}");
        string s = "hello";
        string t = new string("hello".ToCharArray());      // 내용이 같은 다른 객체
        object os = s, ot = t;
        Console.WriteLine($"[3] string s == t           : {s == t}");
        Console.WriteLine($"[4] object os == ot         : {os == ot}");
        Console.WriteLine($"[5] object os.Equals(ot)    : {os.Equals(ot)}");
        Console.WriteLine($"[6] Probe.D<string>(s, t)   : {Probe.D(s, t)}");
        Console.WriteLine($"[7] object.Equals(s, t)     : {object.Equals(s, t)}");
        Console.WriteLine($"[8] ReferenceEquals(s, t)   : {ReferenceEquals(s, t)}");
        foreach (var n in new[] { "A", "B", "C", "D" }) Il.Dump(typeof(Probe), n);
    }
}
```

- `[1]`\~`[8]` 에 무엇이 찍히는가?
- ★★★ `[3]` 과 `[4]` 는 **같은 두 객체**를 비교한다 — 답이 같은가?
- ★★★ `[6]` 의 `Probe.D<string>` 은 `T` 가 `string` 인데 어떻게 되는가?
- ★★ `Probe.A`\~`D` 네 IL 중 **`ceq` 가 아닌 것**은 어느 것이고 대신 무엇이 나오는가?

### 3. ★★ 동등성 짝을 어긋나게 둔 여섯 타입과 네 비교 (예측)

```csharp
// cs19b-probe.cs
using System;
using System.Collections.Generic;

// 탐침 1 — Equals 만 재정의한다
class P1 { public int V { get; set; } public override bool Equals(object? o) => o is P1 p && p.V == V; }

// 탐침 2 — == 와 != 만 정의한다
class P2 { public int V { get; set; }
    public static bool operator ==(P2? a, P2? b) => a?.V == b?.V;
    public static bool operator !=(P2? a, P2? b) => !(a == b); }

// 탐침 3 — == · != · Equals 를 정의하고 GetHashCode 는 안 쓴다
class P3 { public int V { get; set; }
    public static bool operator ==(P3? a, P3? b) => a?.V == b?.V;
    public static bool operator !=(P3? a, P3? b) => !(a == b);
    public override bool Equals(object? o) => o is P3 p && p.V == V; }

// 탐침 4 — GetHashCode 만 재정의한다
class P4 { public int V { get; set; } public override int GetHashCode() => V; }

// 탐침 5 — IEquatable<T> 만 구현한다 (Equals(object)·GetHashCode 는 그대로)
class P5 : IEquatable<P5> { public int V { get; set; } public bool Equals(P5? o) => o is not null && o.V == V; }

// 탐침 6 — Equals 를 안 고친 구조체
struct P6 { public int V { get; set; } }

class Program {
    static void Main() {
        object o = "ab";
        string s = new string("ab".ToCharArray());
        Console.WriteLine($"탐침 7 : o == s  → {o == s}");
        Console.WriteLine($"탐침 8 : s == o  → {s == o}");
        var p6 = new P6();
        Console.WriteLine($"탐침 9 : p6.Equals(p6) → {p6.Equals(p6)}");
        int n = 1;
        Console.WriteLine($"탐침 10 : n == n → {n == n}");
        Console.WriteLine($"탐침 2 : new P2 {{ V = 1 }} == new P2 {{ V = 1 }} → {new P2 { V = 1 } == new P2 { V = 1 }} · HashSet Count → {new HashSet<P2> { new() { V = 1 }, new() { V = 1 } }.Count}");
        Console.WriteLine($"탐침 5 : ((object)x).Equals(y) → {((object)new P5 { V = 1 }).Equals(new P5 { V = 1 })} · HashSet Count → {new HashSet<P5> { new() { V = 1 }, new() { V = 1 } }.Count}");
    }
}
```

- `-warn:9` 로 컴파일하면 **어느 탐침**에 어떤 진단 코드가 붙는가 — 진단이 붙은 줄은 몇 개인가?
- ★★★ 탐침 5 에 진단이 붙는가 — 실행 줄의 두 값은?
- ★★ 탐침 2 의 `==` 결과와 `HashSet` `Count` 는 각각 무엇이고, 왜 서로 반대인가?
- ★ 탐침 7·8 의 실행 결과는?

### 4. ★★ 구조체를 컬렉션에서 찾을 때의 할당 바이트 (예측)

```csharp
// cs19b-alloc.cs
using System;
using System.Collections.Generic;
struct Plain { public int A; public int B; }                              // Equals 를 안 고쳤다
struct Fast : IEquatable<Fast> {
    public int A; public int B;
    public bool Equals(Fast o) => A == o.A && B == o.B;
    public override bool Equals(object? o) => o is Fast f && Equals(f);
    public override int GetHashCode() => HashCode.Combine(A, B);
}
class Program {
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        var lp = new List<Plain>    { new() { A = 1, B = 2 } };
        var lf = new List<Fast>     { new() { A = 1, B = 2 } };
        var hp = new HashSet<Plain> { new() { A = 1, B = 2 } };
        var hf = new HashSet<Fast>  { new() { A = 1, B = 2 } };
        var kp = new Plain { A = 1, B = 2 }; var kp2 = new Plain { A = 1, B = 2 };
        var kf = new Fast  { A = 1, B = 2 };
        Console.WriteLine($"List<Plain>.Contains    1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += lp.Contains(kp) ? 1 : 0; })} 바이트");
        Console.WriteLine($"List<Fast>.Contains     1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += lf.Contains(kf) ? 1 : 0; })} 바이트");
        Console.WriteLine($"HashSet<Plain>.Contains 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += hp.Contains(kp) ? 1 : 0; })} 바이트");
        Console.WriteLine($"HashSet<Fast>.Contains  1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += hf.Contains(kf) ? 1 : 0; })} 바이트");
        Console.WriteLine($"kp.Equals(kp2)          1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += kp.Equals(kp2) ? 1 : 0; })} 바이트");
        int h = 0;                                       // 해시 값은 프로세스마다 다르다 — 찍지 않는다
        Console.WriteLine($"kp.GetHashCode()        1000회 : {M(() => { for (int i = 0; i < 1000; i++) h ^= kp.GetHashCode(); })} 바이트");
        GC.KeepAlive(h);
        Console.WriteLine($"(합 {sink})");
    }
}
```

- 여섯 줄 중 **0 이 아닌** 줄은 어느 것인가 — 각각 호출당 몇 바이트인가?
- ★★★ `HashSet<Plain>` 의 한 호출 바이트를 **아래 두 줄로 분해**할 수 있는가?
- ★★★ `List<Plain>.Contains` 는? — `Plain` 은 `IEquatable` 이 없다.
- ★ 네 판(csc 최적화 × 티어링)에서 **움직인 줄**이 있는가?

### 5. ★★★ 구조체 `Contains` 의 경로를 가르는 런타임 판정 (왜)

- 런타임 내부 판정 **`IsBitwiseEquatable<T>`** 는 `Plain`·`RefField`·`Fast`·`int` 에서 각각 무엇인가?
- ★★★ 그 판정이 `List.Contains` 의 경로를 어떻게 가르는가 — `List<RefField>.Contains` 1000회는 몇 바이트였나?
- ★★ 이 설명 중 **실측인 부분**과 **읽지 않은 부분**을 가를 수 있는가?
- ★★ `RefField` 의 기본 해시가 `(1,x)`·`(1,y)` 를 **같게** 준 것은 계약 위반인가 — 무엇이 문제인가?

### 6. ★★ 반사성을 깬 키를 넣은 그 객체로 찾기 — C# 과 Kotlin (왜)

- C# `HashSet` 에서 `R1` 의 `set.Contains(k)` 와 Kotlin(JDK `HashSet`)의 같은 칸은 각각 무엇이었나?
- ★★★ 그 차이는 **누가** 정한 것인가 — 언어인가 라이브러리인가?
- ★ record 의 생성된 `Equals` 안에도 비슷한 **지름길**이 있다 — 그것과 이것은 **어디에** 있느냐가 어떻게 다른가?

### 7. ★★ 대칭성을 깬 키 — `Contains` 는 누구의 `Equals` 를 부르나 (왜)

- C# `HashSet.Contains(x)` 는 **`원소.Equals(x)`** 와 **`x.Equals(원소)`** 중 어느 쪽을 불렀다고 읽히는가 — 근거는?
- ★★ Kotlin(JDK) 은 어느 쪽이었나?
- ★★★ 대칭성이 **지켜지면** 이 방향 차이가 왜 상관없어지는가?

### 8. ★★ 연산자 짝과 구조체의 `==` (경계)

- `==` 만 정의하고 `!=` 를 안 쓰면? — 경고인가 에러인가, 코드는?
- ★★ 구조체에 `==` 를 쓰면(연산자를 정의 안 했을 때)?
- ★★★ `IEquatable<T>.Equals(T)` 만 구현하고 `Equals(object)`·`GetHashCode` 를 안 고치면 **어떤 경고**가 나는가?

### 9. ★ 해시 값을 여러 프로세스에서 (경계)

- 같은 프로그램을 8번 돌려 `Plain(1,2)`·`new Obj()`·`"alpha"`·`1` 의 해시가 **몇 가지** 나왔나?
- ★★ 그중 **보장**인 것과 **이 판의 관찰**인 것을 가를 수 있는가?
- ★ .NET API 문서는 해시를 **어디에 쓰지 말라**고 하는가?

### 10. ★★★ 네 갈래 대비표의 C# 칸 (연결)

- Python·Rust·Kotlin·C# 을 **「짝을 안 맞춘 것을 언제 잡나」** 순서로 늘어놓을 수 있는가 — 각각 무엇으로 잡나?
- ★★★ C# **만** 가진 칸 둘은 무엇인가?
- ★★ C# 칸이 Kotlin 칸과 갈리는 두 자리는 무엇이고, 그 차이는 **어느 층**인가?

### 11. ★★ 다섯 멤버를 한 벌로 (경계)

- 값 동등성을 손으로 쓸 때 **한 벌로 써야 하는 다섯 멤버**를 대라.
- ★★ 각 멤버에서 지켜야 할 한 가지씩 — `Equals(object)` 는 어디로 모으나, `GetHashCode` 는 무엇만 섞나, `==` 는 무엇부터 처리하나?
- ★ 왜 `sealed` 와 **불변 속성**을 권하는가 — 1번 격자의 어느 줄과 이어지나?

### 12. 다른 주제와 잇기 (연결)

- ★★★ 해시 표의 **원리**와 **계약 한 문장**은 어디가 정본인가 — 그 문서의 **어느 절**인가?
- ★★★ record 에서 2번의 `[1]` 사고가 **안 나는 이유**를 IL 로 보인 것은 몇 번 주제인가?
- ★★ `CS0659` 와 `Count = 3` 을 먼저 잰 것은? 구조체 `Equals` 한 호출의 **+48/+152/+0** 은?
- ★ 1번 격자의 다섯 모양은 **어느 갈래 몇 번**에서 가져왔나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
