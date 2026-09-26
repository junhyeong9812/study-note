# csharp/syntax/19 — 동등성 규칙 — `Equals`/`GetHashCode`/`==` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — **해시 값**은 한 번도 안 찍었다. **격자 `R2` 줄의 `Count=2`** 는 원리상 흔들릴 수 있다(기본 해시 둘이 우연히 같으면).\
> 근거로 쓰는 것은 **격자의 나머지 칸 · 「갈린 칸 N / M」 · 진단 코드와 `(행,열)` · 옵코드 · 네 판에서 갈린 줄 수 · 가짓수** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「`IEquatable` 이 빠르다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **갈린 칸 2 / 8** — `R1` 은 **넣은 그 객체로도 `False`**, `R5` 는 **Kotlin 과 방향이 반대**

**출력**

```text
===== 소스: cs19b-grid.cs =====
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
===== csc -nullable:enable -out:ex.dll cs19b-grid.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
R1 | Count=2 | set.Contains(k)=False | set.Contains(new)=False | list.Contains(k)=False | list.Contains(new)=False
R2 | Count=2 | set.Contains(k)=True  | set.Contains(new)=False | list.Contains(k)=True  | list.Contains(new)=True 
R3 | Count=1 | set.Contains(k)=False | set.Contains(new)=False | list.Contains(k)=True  | list.Contains(new)=False
R6 | Count=1 | set.Contains(k)=True  | set.Contains(new)=True  | list.Contains(k)=True  | list.Contains(new)=True 
set 과 list 가 갈린 칸 2 / 8
R4 | order 1,3,2 -> Count=2 | order 2,1,3 -> Count=1
R5 | {R5(A)}.Contains("a")=True | {"a"}.Contains(R5(A))=False
R5 | R5(A).Equals("a")=True | "a".Equals(R5(A))=False
```

**왜 그런가**

- ★★★ **`R2`** — 셋 `Contains(new)` **`False`** · 리스트 **`True`**. 새 객체는 해시가 달라 **다른 칸**을 보고, `Equals` 가 **불리지도 않는다.** 리스트는 해시를 안 쓴다.
- ★★★ **`R3`** — 셋 `Contains(k)` **`False`** · 리스트 **`True`**. 넣은 뒤 `V` 를 바꿔 해시가 바뀌었다 — **셋 안에 있는데** 못 찾는다.
- ★★★ **`R1`** — 셋 `Contains(k)` 가 **`False`**. **이 판의 .NET `HashSet` 은 같은 참조여도 `Equals` 를 부른다**(지름길이 없다).\
  리스트도 `False` 라 **이 줄은 「갈린 칸」에 안 들어간다** — 그래서 Kotlin 의 **`3 / 8`** 이 여기서는 **`2 / 8`** 이다.
- ★★ **`R4`** — `1,3,2` 순 **`Count=2`** · `2,1,3` 순 **`Count=1`**. 추이성이 없으면 **먼저 앉은 원소가 누구를 튕길지** 정한다.
- ★★★ **`R5`** — `{R5(A)}.Contains("a")` **`True`** · `{"a"}.Contains(R5(A))` **`False`**. 마지막 줄 — `R5(A).Equals("a")` **`True`** · `"a".Equals(R5(A))` **`False`**.\
  **첫째가 `True` 이려면 원소 `R5(A)` 의 `Equals` 가 불렸어야** 한다 — 7번.

### 2. ★★★ `==` 는 **변수 타입이 고른다** — 같은 두 문자열이 `True` 에서 `False` 로

**출력**

```text
===== 소스: cs19b-opeq.cs =====
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
===== csc -nullable:enable -r:il.dll -out:ex.dll cs19b-opeq.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Money  a == b           : False
[2] Money  a.Equals(b)      : True
[3] string s == t           : True
[4] object os == ot         : False
[5] object os.Equals(ot)    : True
[6] Probe.D<string>(s, t)   : False
[7] object.Equals(s, t)     : True
[8] ReferenceEquals(s, t)   : False
--- Probe.A ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: ceq
  IL_0004: ret
--- Probe.B ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: call System.String::op_Equality
  IL_0007: ret
--- Probe.C ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: ceq
  IL_0004: ret
--- Probe.D ---
  IL_0000: ldarg.0
  IL_0001: box T
  IL_0006: ldarg.1
  IL_0007: box T
  IL_000c: ceq
  IL_000e: ret
===== csc -nullable:enable -warn:9 -r:il.dll -out:ex.dll cs19b-opeq.cs    # 같은 소스를 -warn:9 로 — 진단이 몇 줄인가 (cc exit=0) =====
```

**왜 그런가**

- ★★★ **`[1]` `False` · `[2]` `True`** — `Money` 는 `Equals` 만 고쳤다. **`==` 는 참조 비교 그대로** — IL `A` 가 **`ceq`** 다.
- ★★★ **`[3]` `True` · `[4]` `False`** — **같은 두 객체**인데 **변수 타입만** 다르다. `string` 변수면 **`call String::op_Equality`**(IL `B`), `object` 변수면 **`ceq`**(IL `C`).\
  ★ 연산자는 **정적 타입으로 고르고**, `Equals` 는 **가상으로** 고른다 — `[5]` `os.Equals(ot)` 는 **`True`**.
- ★★★ **`[6]` `False`** — `where T : class` 안의 `==` 는 **`box T` · `box T` · `ceq`**(IL `D`). 컴파일 때 `T` 를 모르니 `op_Equality` 를 고를 수 없다.
- ★★ **`[7]` `True`** — 정적 `object.Equals` 는 가상 `Equals` 를 부른다. **`[8]` `False`** — 두 문자열은 다른 객체다.
- ★ **`ceq` 가 아닌 것은 `B` 하나**(`call String::op_Equality`)다.
- ★ 마지막 배너 — **`-warn:9` 로 던져도 진단 0줄**이다. `[1]`·`[4]`·`[6]` 의 함정에 **경고가 없다.**

### 3. ★★ 진단이 붙은 줄 **여섯** — 탐침 5 는 **침묵인데 두 값이 다 틀린다**

**출력**

```text
===== 소스: cs19b-probe.cs =====
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
===== csc -nullable:enable -warn:9 -out:ex.dll cs19b-probe.cs 2>&1 | sort && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs19b-probe.cs(13,7): warning CS0659: 'P3' overrides Object.Equals(object o) but does not override Object.GetHashCode()
cs19b-probe.cs(13,7): warning CS0661: 'P3' defines operator == or operator != but does not override Object.GetHashCode()
cs19b-probe.cs(31,47): warning CS0252: Possible unintended reference comparison; to get a value comparison, cast the left hand side to type 'string'
cs19b-probe.cs(32,47): warning CS0253: Possible unintended reference comparison; to get a value comparison, cast the right hand side to type 'string'
cs19b-probe.cs(36,47): warning CS1718: Comparison made to same variable; did you mean to compare something else?
cs19b-probe.cs(5,7): warning CS0659: 'P1' overrides Object.Equals(object o) but does not override Object.GetHashCode()
cs19b-probe.cs(8,7): warning CS0660: 'P2' defines operator == or operator != but does not override Object.Equals(object o)
cs19b-probe.cs(8,7): warning CS0661: 'P2' defines operator == or operator != but does not override Object.GetHashCode()
탐침 7 : o == s  → False
탐침 8 : s == o  → False
탐침 9 : p6.Equals(p6) → True
탐침 10 : n == n → True
탐침 2 : new P2 { V = 1 } == new P2 { V = 1 } → True · HashSet Count → 2
탐침 5 : ((object)x).Equals(y) → False · HashSet Count → 2
===== csc -nullable:enable -warn:9 -out:ex.dll cs19b-probe.cs 2>&1 | grep -o "cs19b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 10개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
6
```

**왜 그런가**

- ★★★ **탐침 1 `CS0659` · 탐침 2 `CS0660`+`CS0661` · 탐침 3 `CS0659`+`CS0661` · 탐침 7 `CS0252` · 탐침 8 `CS0253` · 탐침 10 `CS1718`** — 줄로 **6**.
- ★★★ **탐침 5 — 진단 없음.** `((object)x).Equals(y)` **`False`** · `HashSet` **`Count 2`**.\
  `IEquatable<P5>.Equals` 는 값으로 비교하지만 **`Equals(object)` 는 참조**, **`GetHashCode` 도 `object` 것** — 셋은 **해시가 달라** 둘을 다 넣는다.\
  ★★ **`CS0659` 는 `Equals(object)` 재정의만 본다** — 이 모양은 못 본다.
- ★★ **탐침 2 — `==` 는 `True`, `HashSet` 은 `Count 2`.** `==` 는 값으로 정의했는데 **컬렉션은 `==` 를 안 쓴다** — `Equals`·`GetHashCode` 를 쓰고 그것은 **참조** 그대로다. 경고 둘(`CS0660`·`CS0661`)이 정확히 이 자리다.
- ★ **탐침 7·8 은 둘 다 `False`** — `s` 는 내용이 같은 **다른 객체**라 참조 비교가 `False` 다. 경고(`CS0252`·`CS0253`)가 「왼쪽/오른쪽을 `string` 으로 캐스트하라」고 가리킨다.

### 4. ★★ **`HashSet<Plain>` 72 · `Equals` 직접 48 · `GetHashCode` 직접 24** — 나머지 **0**, 네 판 모두

**출력**

```text
===== 소스: cs19b-alloc.cs =====
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
===== csc -nullable:enable -out:ex.dll cs19b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
List<Plain>.Contains    1000회 : 0 바이트
List<Fast>.Contains     1000회 : 0 바이트
HashSet<Plain>.Contains 1000회 : 72000 바이트
HashSet<Fast>.Contains  1000회 : 0 바이트
kp.Equals(kp2)          1000회 : 48000 바이트
kp.GetHashCode()        1000회 : 24000 바이트
(합 10000)
===== csc -nullable:enable -out:ex.dll cs19b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
List<Plain>.Contains    1000회 : 0 바이트
List<Fast>.Contains     1000회 : 0 바이트
HashSet<Plain>.Contains 1000회 : 72000 바이트
HashSet<Fast>.Contains  1000회 : 0 바이트
kp.Equals(kp2)          1000회 : 48000 바이트
kp.GetHashCode()        1000회 : 24000 바이트
(합 10000)
===== csc -nullable:enable -optimize -out:exo.dll cs19b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
List<Plain>.Contains    1000회 : 0 바이트
List<Fast>.Contains     1000회 : 0 바이트
HashSet<Plain>.Contains 1000회 : 72000 바이트
HashSet<Fast>.Contains  1000회 : 0 바이트
kp.Equals(kp2)          1000회 : 48000 바이트
kp.GetHashCode()        1000회 : 24000 바이트
(합 10000)
===== csc -nullable:enable -optimize -out:exo.dll cs19b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
List<Plain>.Contains    1000회 : 0 바이트
List<Fast>.Contains     1000회 : 0 바이트
HashSet<Plain>.Contains 1000회 : 72000 바이트
HashSet<Fast>.Contains  1000회 : 0 바이트
kp.Equals(kp2)          1000회 : 48000 바이트
kp.GetHashCode()        1000회 : 24000 바이트
(합 10000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 6
```

**왜 그런가**

- ★★★ **`HashSet<Plain>` 호출당 72 = 해시 24 + `Equals` 48** — 아래 두 줄이 그 분해다(`GetHashCode` 는 `this` 박싱 하나, `Equals` 는 `this`·인자 둘).
- ★★★ **`HashSet<Fast>` 0** — `EqualityComparer<Fast>.Default` 가 `IEquatable<Fast>` 를 골랐다.
- ★★★ **`List<Plain>` 도 0** — `IEquatable` 이 없는데도. 5번이 이유다.
- ★★★ **네 판에서 갈린 줄 0 / 6** — 근거로 쓸 수 있다.

### 5. ★★★ **`IsBitwiseEquatable<Plain>` = `True`** — 바이트째 비교하는 길로 간다

**출력**

```text
===== 소스: cs19b-bitwise.cs =====
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
struct Plain    { public int A; public int B; }
struct RefField { public int A; public string S; }
struct Fast : IEquatable<Fast> {
    public int A; public int B;
    public bool Equals(Fast o) => A == o.A && B == o.B;
    public override bool Equals(object? o) => o is Fast f && Equals(f);
    public override int GetHashCode() => HashCode.Combine(A, B);
}
class Program {
    // 런타임 내부 판정 — 「바이트째 비교해도 되는 타입인가」. 비공개 API 라 리플렉션으로 부른다.
    static bool Bitwise<T>() => (bool)typeof(RuntimeHelpers)
        .GetMethod("IsBitwiseEquatable", BindingFlags.NonPublic | BindingFlags.Static)!
        .MakeGenericMethod(typeof(T)).Invoke(null, null)!;
    static long M(Action a) { a(); var b = GC.GetAllocatedBytesForCurrentThread(); a(); return GC.GetAllocatedBytesForCurrentThread() - b; }
    static void Main() {
        _ = new Fast { A = 1, B = 2 };
        Console.WriteLine($"IsBitwiseEquatable : Plain={Bitwise<Plain>()} · RefField={Bitwise<RefField>()} · Fast={Bitwise<Fast>()} · int={Bitwise<int>()}");
        int sink = 0;
        var lr = new List<RefField> { new() { A = 1, S = "x" } }; var kr = new RefField { A = 1, S = "x" };
        Console.WriteLine($"List<RefField>.Contains 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += lr.Contains(kr) ? 1 : 0; })} 바이트");
        int r1 = new RefField { A = 1, S = "x" }.GetHashCode(), r2 = new RefField { A = 2, S = "x" }.GetHashCode(), r3 = new RefField { A = 1, S = "y" }.GetHashCode();
        Console.WriteLine($"RefField 해시 : (1,x) 와 (2,x) 같나 {r1 == r2} · (1,x) 와 (1,y) 같나 {r1 == r3}");
        int p1 = new Plain { A = 1, B = 2 }.GetHashCode(), p2 = new Plain { A = 1, B = 3 }.GetHashCode(), p3 = new Plain { A = 9, B = 2 }.GetHashCode();
        Console.WriteLine($"Plain 해시    : (1,2) 와 (1,3) 같나 {p1 == p2} · (1,2) 와 (9,2) 같나 {p1 == p3}");
        Console.WriteLine($"RefField (1,x) 와 (1,y) 의 Equals : {new RefField { A = 1, S = "x" }.Equals(new RefField { A = 1, S = "y" })}");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -nullable:enable -optimize -out:ex.dll cs19b-bitwise.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
IsBitwiseEquatable : Plain=True · RefField=False · Fast=False · int=True
List<RefField>.Contains 1000회 : 152000 바이트
RefField 해시 : (1,x) 와 (2,x) 같나 False · (1,x) 와 (1,y) 같나 True
Plain 해시    : (1,2) 와 (1,3) 같나 False · (1,2) 와 (9,2) 같나 False
RefField (1,x) 와 (1,y) 의 Equals : False
(합 2000)
```

**왜 그런가**

- ★★★ **`Plain` `True` · `RefField` `False` · `Fast` `False` · `int` `True`.**\
  참조가 없고 `Equals` 를 안 고친 구조체는 **메모리를 바이트째 비교해도 `Equals` 와 같다** — 런타임이 그렇게 판정했다.
- ★★★ **`List<RefField>.Contains` 는 1000회 152000** — 판정이 `False` 라 **필드별 리플렉션 경로**로 간다. [02번](../02-struct-vs-class-choosing/) (5)의 **+152** 와 같은 값이다.
- ★★ **실측인 것** — 판정값(네 `True`/`False`)과 바이트(0 대 152000)가 **함께 맞는다**는 것.\
  **읽지 않은 것** — `List.Contains` 가 그 판정으로 **분기하는 코드**. 설명은 두 실측을 잇는 **해석**이다.
- ★★ **`RefField` 해시 — `(1,x)`/`(1,y)` 같음 · `(1,x)`/`(2,x)` 다름.** 첫 필드(`A`)만 섞었다.\
  **계약 위반은 아니다** — 다른 값이 같은 해시를 가져도 된다(역은 요구하지 않는다). **문제는 충돌**이다 — 첫 필드가 같은 키들이 **한 칸에 몰린다.**\
  ★ 「첫 필드만」은 **이 판의 구현**이다. 문서는 「필드 값으로 계산한다」만 적는다.

### 6. ★★ C# **`False`** · Kotlin **`true`** — **라이브러리**가 정했다

**출력**

1번 블록의 `R1` 줄.

**왜 그런가**

- ★★★ **C# `HashSet` 은 같은 참조여도 `Equals` 를 부르고**, `Equals` 가 늘 `false` 라 **`False`** 다.\
  **JDK `HashMap` 은 해시가 같으면 `==`(동일성)를 먼저** 보고 맞으면 `equals` 를 건너뛰어 **`true`** 였다([Kotlin 32번](../../../kotlin/syntax/32-equality-and-equals-contract/) (4)).
- ★★★ **둘 다 BCL/JDK 구현**이다 — C#·Kotlin·Java **언어 어느 것도** 이 지름길을 약속하지 않는다.
- ★ [18번](../18-record-value-equality-and-with/) (3)의 **record `Equals` 첫머리 `beq`** 는 **`Equals` 메서드 안**에 있는 지름길이다 — **컬렉션이 아니라 타입이** 가진 것이다.\
  그래서 record 키는 C# `HashSet` 에서도 **넣은 그 객체로 찾아진다**(대조군 `R6` 의 `True` — 다만 `R6` 은 반사성을 지키므로 지름길 없이도 `True` 다).

### 7. ★★ C# 은 **`원소.Equals(인자)`** · Kotlin(JDK) 은 **`인자.equals(원소)`**

**출력**

1번 블록의 `R5` 두 줄.

**왜 그런가**

- ★★★ **근거** — `{R5(A)}.Contains("a")` 가 `True` 다. 두 방향의 `Equals` 중 `True` 를 내는 것은 **`R5(A).Equals("a")` 뿐**이다(마지막 줄). 그러니 **원소 `R5(A)` 의 `Equals` 가 불렸다.**\
  ★ 반대 셋 `{"a"}.Contains(R5(A))` 는 `False` — 원소 `"a"` 의 `Equals` 가 불렸고 `"a".Equals(R5(A))` 는 `False` 다. **두 칸이 같은 방향을 가리킨다.**
- ★★ **Kotlin 은 두 칸이 정반대**(`false` / `true`) — 인자의 `equals` 를 부른다.
- ★★★ **대칭이 지켜지면** `a.Equals(b) == b.Equals(a)` 이므로 **누가 누구를 부르든 답이 같다.** 방향 차이가 드러나는 것 자체가 **대칭성 위반의 증상**이다.

### 8. ★★ `CS0216`(에러) · `CS0019`(에러) · **`IEquatable` 만이면 경고 없음**

**출력**

```text
===== 소스: cs19b-op2.cs =====
class Half { public static bool operator ==(Half a, Half b) => true; }      // != 를 안 적었다
struct Pt { public int X; }
class Program {
    static void Main() {
        var p = new Pt(); var q = new Pt();
        bool same = p == q;                                                  // 구조체에 == 를 쓴다
    }
}
===== csc -out:ex.dll cs19b-op2.cs 2>&1 | sort (cc exit=1) =====
cs19b-op2.cs(1,42): error CS0216: The operator 'Half.operator ==(Half, Half)' requires a matching operator '!=' to also be defined
cs19b-op2.cs(1,7): warning CS0660: 'Half' defines operator == or operator != but does not override Object.Equals(object o)
cs19b-op2.cs(1,7): warning CS0661: 'Half' defines operator == or operator != but does not override Object.GetHashCode()
```

**왜 그런가**

- ★★★ **`CS0216`** — `==` 를 정의하면 **`!=` 도 반드시** 정의해야 한다. **에러**다 — 이 주제에서 짝이 **강제되는 유일한 자리**다.
- ★★ 같은 타입에 **`CS0660`·`CS0661`**(경고)도 함께 났다 — `Equals`·`GetHashCode` 도 짝이다.
- ★★★ **`CS0019`** — 구조체에는 **`==` 가 기본으로 없다.** 구조체의 같음은 `Equals` 뿐이다.
- ★★★ **`IEquatable<T>` 만 구현** — **진단 0**(3번 탐침 5). 결과는 틀린다.

### 9. ★ **`Plain` 8가지 · `"alpha"` 8가지 · `Obj` 1가지 · `1` 1가지**

**출력**

```text
===== 소스: cs19b-hash.cs =====
using System;
struct Plain { public int A; public int B; }
class Obj { }
class Program {
    static void Main() {
        Console.WriteLine($"{new Plain { A = 1, B = 2 }.GetHashCode()} {new Obj().GetHashCode()} {"alpha".GetHashCode()} {1.GetHashCode()}");
    }
}
===== csc -out:ex.dll cs19b-hash.cs (cc exit=0) =====
===== for i in 1 2 3 4 5 6 7 8; do dotnet ex.dll; done | awk ...    # 8판을 돌려 열마다 서로 다른 값이 몇 가지인가 (exit=0) =====
Plain(1,2) 8가지 · new Obj() 1가지 · "alpha" 8가지 · 1 1가지 (8판 중)
```

**왜 그런가**

- ★★★ **구조체·문자열의 기본 해시는 프로세스마다 다르다** — 8판에서 8가지.
- ★★ **보장인 것** — 「같은 실행 안에서 같은 값이면 같은 해시」뿐이다(API 문서: 「**다시 실행하면 다른 해시가 나올 수 있다**」).\
  **`Obj`·`1` 이 1가지였던 것은 이 판의 관찰**이다.
- ★ API 문서 — **직렬화·DB 저장·프로세스 간 전송·키로 쓰기**에 쓰지 말라.

### 10. ★★★ **Rust(컴파일 에러) → C#(컴파일 경고) → Python(런타임 에러) → Kotlin(침묵)**

**왜 그런가**

- ★★★ **Rust** — `HashMap` 키에 `Eq + Hash` 경계 · **C#** — `CS0659`/`CS0660`/`CS0661` **경고**(빌드는 된다) ·\
  **Python** — `__eq__` 만 쓰면 `__hash__` 가 `None` → `TypeError` · **Kotlin** — `-Wextra` 도 **경고 0줄**.
- ★★★ **C# 만 가진 칸 둘** — ① **`==` 가 `Equals` 와 어긋날 수 있다**(정적 타입이 연산자를 고른다, 2번) ② **짝 안 맞춤이 「경고」다.**
- ★★ **Kotlin 과 갈리는 두 자리** — `R1`(지름길 유무)·`R5`(`Contains` 방향). **둘 다 라이브러리 구현** 층이다(6·7번).
- ★ 표 전체는 [2-summary.md](2-summary.md) (2)에 있다.

### 11. ★★ **`IEquatable<T>.Equals(T)` · `Equals(object)` · `GetHashCode` · `==` · `!=`**

**출력**

```text
===== 소스: cs19b-form.cs =====
using System;
using System.Collections.Generic;

var a = new Money(100, "KRW"); var b = new Money(100, "KRW");
Console.WriteLine($"{a == b} {a.Equals(b)} {a.Equals((object)b)} {a.GetHashCode() == b.GetHashCode()} {new HashSet<Money> { a, b }.Count}");

sealed class Money : IEquatable<Money> {                       // sealed — 파생이 대칭성을 깨지 못하게
    public int Won { get; }                                     // 불변 — 넣은 뒤 해시가 안 바뀐다
    public string Currency { get; }
    public Money(int won, string currency) { Won = won; Currency = currency; }
    public bool Equals(Money? o) => o is not null && Won == o.Won && Currency == o.Currency;
    public override bool Equals(object? o) => Equals(o as Money);               // 한 곳으로 모은다
    public override int GetHashCode() => HashCode.Combine(Won, Currency);       // Equals 가 보는 것만 섞는다
    public static bool operator ==(Money? x, Money? y) => x is null ? y is null : x.Equals(y);
    public static bool operator !=(Money? x, Money? y) => !(x == y);
}
===== csc -nullable:enable -warn:9 -out:ex.dll cs19b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
True True True True 1
```

**왜 그런가**

- ★★★ **`Equals(object)` 는 `Equals(T)` 로 모은다** — 규칙이 **한 곳**에 있어야 어긋나지 않는다.
- ★★★ **`GetHashCode` 는 `Equals` 가 보는 것만** 섞는다 — `HashCode.Combine(Won, Currency)`.
- ★★ **`==` 는 널부터** 처리하고 `Equals` 를 부른다 — `==` 와 `Equals` 가 **같은 답**을 낸다(`True True True True 1`).
- ★★ **`sealed`** — 파생이 `Equals` 를 덮어 **대칭성**을 깨지 못하게(1번 `R5`). **불변 속성** — 넣은 뒤 해시가 **안 바뀌게**(1번 `R3`).
- ★ `-warn:9` 에서 **진단 0줄**이다 — 짝이 다 맞았다.

### 12. 잇기

- ★★★ 해시 표의 원리와 계약 한 문장 — [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 의 「**사전 지식 — hashCode 와 equals 의 약속**」·「**동작 — 조회**」 절.
- ★★★ record 에서 `==` 가 `Equals` 를 부르게 생성되는 IL — [18번](../18-record-value-equality-and-with/) (3).
- ★★ `CS0659`·`Count = 3` — [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/) (6). 구조체 `Equals` 한 호출의 **+48/+152/+0** — [02번](../02-struct-vs-class-choosing/) (5).
- ★ 다섯 모양 — Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **32번**([`32-equality-and-equals-contract/`](../../../kotlin/syntax/32-equality-and-equals-contract/)) (4).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs19b-grid.cs` 계약 위반 × 자료구조 | csc 1회 | ★★★ **갈린 칸 2 / 8**(Kotlin 3 / 8) · `R1` 셋 **`False`** · `R5` 방향 **반대** · `R4` **2 / 1** |
| `cs19b-opeq.cs` `==` 대 `Equals` + IL | csc 2회(기본·`-warn:9`) | ★★★ 같은 두 문자열이 **`True` → `False`** · IL **`ceq` 대 `call op_Equality`** · **경고 0줄** |
| `cs19b-probe.cs` 탐침 열 | csc 1회(`-warn:9`) + 실행 | ★★★ **진단이 붙은 줄 6** · 탐침 5 **침묵** · `Count 2` |
| `cs19b-op2.cs` 연산자 짝 · 구조체 `==` | csc 1회 | ★★★ **`CS0216`·`CS0019`** + `CS0660`·`CS0661` |
| `cs19b-alloc.cs` 할당 바이트 | **2×2 판 격자** | ★★★ `HashSet<Plain>` **72000** · `List<Plain>` **0** · **갈린 줄 0 / 6** |
| `cs19b-bitwise.cs` 런타임 판정 | csc 1회(`-optimize`) | ★★★ `IsBitwiseEquatable` **T/F/F/T** · `List<RefField>` **152000** · 첫 필드 해시 |
| `cs19b-hash.cs` 해시 가짓수 | 8판 | ★★★ **8 · 1 · 8 · 1 가지** |
| `cs19b-form.cs` 다섯 멤버 한 벌 | csc 1회(`-warn:9`) | `True True True True 1` · **진단 0줄** |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · BCL)에서만** 그렇다.

- ★★★ **`HashSet` 에 참조 지름길이 없는 것 · `Contains` 가 `원소.Equals(인자)` 인 것** — BCL 구현. **Kotlin 과 갈린 두 칸**이 여기 달렸다.
- ★★★ **`IsBitwiseEquatable` 로 `List<Plain>.Contains` 가 0 인 것** · **`ValueType.GetHashCode` 가 첫 필드만 본 것** — 런타임 구현.
- ★★ **할당 바이트 72·48·24·152** · **해시 가짓수의 `Obj` 1가지** · **`-warn:9` 탐침 열 중 여섯**.

**언어·라이브러리가 보장하는 것**(구현이 바뀌어도 같다)

- **연산자는 정적 타입으로 고른다** — `object` 변수의 `==` 는 참조 비교다. **`==` 를 정의하면 `!=` 도**(`CS0216`) · **구조체에 기본 `==` 없음**(`CS0019`).
- **「같으면 해시도 같다」 · 역은 아님 · 해시를 저장·전송하지 마라** — API 문서의 계약.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **`Dictionary` 로 같은 격자**(같은 비교자를 쓰니 같을 것이다 — **안 던졌다**) · ★★ **`IEqualityComparer<T>` 를 넘기는 경우** ·\
  ★ **`HashSet` 의 비교 방향을 소스 코드로 확인** · ★ **`List.Contains` 의 `IsBitwiseEquatable` 분기 코드** · ★ **Python·Rust 에서 `R3`\~`R5` 모양**(그 갈래가 안 던진 칸).
- **못 잰 것** — ★★★ **「`IEquatable` 이 빠르다」.** 할당만 쟀다. 시간은 [02번](../02-struct-vs-class-choosing/)이 한 호출 단위로 쟀다.
- **잴 것이 없는 것** — 없다. **④ 할당 바이트는 적용**이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1번 격자의 `R1`·`R5`** — BCL 이 `HashSet` 에 지름길을 넣거나 비교 방향을 바꾸면 **`2 / 8` 이 움직인다.**
- ★★★ **4·5번** — `IsBitwiseEquatable` 의 판정 범위가 넓어지거나 JIT 이 박싱을 없애면 **`72000` 이 움직인다. 그때도 2×2 로 재라.**
- ★★ **3번의 탐침** — Roslyn 이 탐침 5(`IEquatable` 만) 모양에 경고를 넣으면 **여섯이 일곱이 된다.**
- ★ **2번** — 명세가 정한 것이라 바뀔 일이 없다. 바뀌면 그것이 뉴스다.
