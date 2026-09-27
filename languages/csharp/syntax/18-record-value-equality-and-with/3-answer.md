# csharp/syntax/18 — `record` 와 값 동등성·`with` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 대비는 **javac 21.0.5 · 25.0.1** 이다. 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — **진단 문구·IL 오프셋 폭·생성 멤버의 IL 모양**은 흔들리는 칸이다(IL 모양은 **Roslyn 의 구현**).\
> 근거로 쓰는 것은 **생성 멤버의 목록 · 진단 코드와 `(행,열)` · 옵코드와 호출 대상 · 네 판에서 갈린 줄 수** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「`record struct` 가 빠르다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ record class **16개** · struct 둘 **13개** — 빠지는 셋은 `EqualityContract`·복제·복사 생성자

**출력**

```text
===== 소스: cs18b-gen.cs =====
using System;
using System.Linq;
using System.Reflection;

public record                 RC(string Name, int Age);    // record class (C# 9)
public record struct          RS(string Name, int Age);    // record struct (C# 10)
public readonly record struct RR(string Name, int Age);    // readonly record struct (C# 10)
public class PC { public string Name { get; init; } = ""; public int Age { get; init; } }   // 대조군 — 평범한 클래스

class Program {
    static string Acc(MethodBase m) =>
        m.IsPublic ? "public" : m.IsFamily ? "protected" : m.IsPrivate ? "private" : m.IsAssembly ? "internal" : "?";
    static void Show(Type t) {
        var ms = t.GetMembers(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)
                  .OfType<MethodBase>()
                  .Select(m => {
                      var ps  = string.Join(",", m.GetParameters().Select(p => p.ParameterType.Name));
                      var mod = m is MethodInfo mi && mi.ReturnParameter.GetRequiredCustomModifiers().Length > 0 ? " modreq(IsExternalInit)" : "";
                      return $"{Acc(m),-9}{(m.IsStatic ? " static" : "")}{(m.IsVirtual ? " virtual" : "")} {m.Name}({ps}){mod}";
                  })
                  .OrderBy(x => x, StringComparer.Ordinal).ToArray();
        Console.WriteLine($"=== {t.Name} — {(t.IsValueType ? "struct" : "class")} · 메서드·생성자 {ms.Length}개 · 인터페이스 [{string.Join(",", t.GetInterfaces().Select(i => i.Name))}] ===");
        foreach (var x in ms) Console.WriteLine("  " + x);
    }
    static void Main() { Show(typeof(RC)); Show(typeof(RS)); Show(typeof(RR)); Show(typeof(PC)); }
}
===== csc -out:ex.dll cs18b-gen.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
=== RC — class · 메서드·생성자 16개 · 인터페이스 [IEquatable`1] ===
  protected .ctor(RC)
  protected virtual PrintMembers(StringBuilder)
  protected virtual get_EqualityContract()
  public    .ctor(String,Int32)
  public    Deconstruct(String&,Int32&)
  public    get_Age()
  public    get_Name()
  public    set_Age(Int32) modreq(IsExternalInit)
  public    set_Name(String) modreq(IsExternalInit)
  public    static op_Equality(RC,RC)
  public    static op_Inequality(RC,RC)
  public    virtual <Clone>$()
  public    virtual Equals(Object)
  public    virtual Equals(RC)
  public    virtual GetHashCode()
  public    virtual ToString()
=== RS — struct · 메서드·생성자 13개 · 인터페이스 [IEquatable`1] ===
  private   PrintMembers(StringBuilder)
  public    .ctor(String,Int32)
  public    Deconstruct(String&,Int32&)
  public    get_Age()
  public    get_Name()
  public    set_Age(Int32)
  public    set_Name(String)
  public    static op_Equality(RS,RS)
  public    static op_Inequality(RS,RS)
  public    virtual Equals(Object)
  public    virtual Equals(RS)
  public    virtual GetHashCode()
  public    virtual ToString()
=== RR — struct · 메서드·생성자 13개 · 인터페이스 [IEquatable`1] ===
  private   PrintMembers(StringBuilder)
  public    .ctor(String,Int32)
  public    Deconstruct(String&,Int32&)
  public    get_Age()
  public    get_Name()
  public    set_Age(Int32) modreq(IsExternalInit)
  public    set_Name(String) modreq(IsExternalInit)
  public    static op_Equality(RR,RR)
  public    static op_Inequality(RR,RR)
  public    virtual Equals(Object)
  public    virtual Equals(RR)
  public    virtual GetHashCode()
  public    virtual ToString()
=== PC — class · 메서드·생성자 5개 · 인터페이스 [] ===
  public    .ctor()
  public    get_Age()
  public    get_Name()
  public    set_Age(Int32) modreq(IsExternalInit)
  public    set_Name(String) modreq(IsExternalInit)
```

**왜 그런가**

- ★★★ **`RC`** — 공용 생성자 · **`protected` 복사 생성자 `.ctor(RC)`** · `Deconstruct` · 속성 접근자 넷 ·\
  `op_Equality`/`op_Inequality` · **`<Clone>$`**(public virtual) · `Equals(object)`/`Equals(RC)` · `GetHashCode` · `ToString` ·\
  **`PrintMembers`**(protected virtual) · **`get_EqualityContract`**(protected virtual).
- ★★★ **struct 쪽에 없는 셋** — `EqualityContract`(상속이 없으니 양식 번호가 필요 없다) · `<Clone>$` 와 복사 생성자(**대입이 곧 복사**다).\
  ★ `PrintMembers` 는 있지만 **`private`** 다 — 파생이 없으니 열 필요가 없다.
- ★★★ **`RS` 의 `set_Age` 에는 `modreq(IsExternalInit)` 가 없다** — `init` 이 아니라 **보통 `set`** 이다. `RC`·`RR` 은 `init` 이다.
- ★ **이름 자체가 약속이 아닌 것** — **`<Clone>$`**. Learn 이 「복제 메서드의 **실제 이름은 컴파일러가 만든다**」고 적는다.

### 2. ★★★ **`<Clone>$`(→ 복사 생성자) 다음 `set_Age`** — struct 는 복제가 없다

**출력**

```text
===== 소스: cs18b-with.cs =====
using System;
public record        RC(string Name, int Age);
public record struct RS(string Name, int Age);
static class Probe {
    public static RC WithC(RC r) => r with { Age = 30 };
    public static RS WithS(RS r) => r with { Age = 30 };
}
class Program {
    static void Main() {
        Il.Dump(typeof(Probe), "WithC");
        Il.Dump(typeof(Probe), "WithS");
        Il.Dump(typeof(RC), "<Clone>$");
        // <Clone>$ 의 newobj 가 어느 생성자를 부르는지 — 토큰을 풀어 매개변수 타입을 찍는다
        var il  = typeof(RC).GetMethod("<Clone>$")!.GetMethodBody()!.GetILAsByteArray()!;
        var ctor = typeof(RC).Module.ResolveMethod(BitConverter.ToInt32(il, 2))!;
        Console.WriteLine($"newobj 의 대상 : {ctor.DeclaringType!.Name}({string.Join(",", Array.ConvertAll(ctor.GetParameters(), p => p.ParameterType.Name))}) · public={ctor.IsPublic} protected={ctor.IsFamily}");
    }
}
===== csc -r:il.dll -out:ex.dll cs18b-with.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.WithC ---
  IL_0000: ldarg.0
  IL_0001: callvirt RC::<Clone>$
  IL_0006: dup
  IL_0007: ldc.i4.s 30
  IL_0009: callvirt RC::set_Age
  IL_000e: nop
  IL_000f: ret
--- Probe.WithS ---
  .locals [0] RS
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldloca.s 0
  IL_0004: ldc.i4.s 30
  IL_0006: call RS::set_Age
  IL_000b: nop
  IL_000c: ldloc.0
  IL_000d: ret
--- RC.<Clone>$ ---
  IL_0000: ldarg.0
  IL_0001: newobj RC::.ctor
  IL_0006: ret
newobj 의 대상 : RC(RC) · public=False protected=True
```

**왜 그런가**

- ★★★ **`callvirt RC::<Clone>$` → `dup` → `callvirt RC::set_Age`**. 복제한 새 객체에 **`init` 세터**를 부른다.
- ★★ **`<Clone>$` 는 `newobj RC::.ctor`** — 토큰을 풀면 **`RC(RC)` · `protected`** 인 복사 생성자다.
- ★★★ **record struct** — `ldarg.0` → `stloc.0`(대입으로 복사) → `ldloca.s 0` → **`call RS::set_Age`**. 복제 메서드가 **없다.**
- ★ **복제가 가상이어야 하는 이유** — `Pt` 변수에 `Tagged` 가 들었을 때 **`Tagged` 를 복제해야** 하기 때문이다(3번).

### 3. ★★★ 셋 다 **`False`** — 대칭이다

**출력**

```text
===== 소스: cs18b-contract.cs =====
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
===== csc -out:ex.dll cs18b-contract.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
a = Pt { X = 1 } · b = Tagged { X = 1 }
a == b : False · a.Equals(b) : False · b.Equals(a) : False
a.EqualityContract = Pt · b.EqualityContract = Tagged
Pt 변수 b 에 with : Tagged { X = 2 } · c.GetType() = Tagged
Pt 변수로 받은 Pt3(1,9) == Pt3(1,7) : False
```

**왜 그런가**

- ★★★ **`EqualityContract` 가 `Pt` 대 `Tagged`** — 생성된 `Equals` 가 멤버보다 **먼저** 이것을 비교한다(9번 IL).
- ★★★ **`a.Equals(b)` 와 `b.Equals(a)` 가 둘 다 `False`** — 양쪽이 **같은 규칙**(실제 타입 + 멤버)을 쓰니 **대칭이 깨지지 않는다.**\
  ★ 손으로 쓴 `Equals` 에서 흔히 깨지는 것이 바로 이 대칭이다(목록의 **19번 주제**의 `R5`).
- ★★ **`with` 결과는 `Tagged { X = 2 }`** — `<Clone>$` 가 가상이라 **런타임 타입의 복제**가 불렸다.
- ★ **`Pt3(1,9)` 대 `Pt3(1,7)`** 는 `Pt` 변수로 받아도 **`False`** — 파생 멤버 `Z` 까지 비교한다.

### 4. ★★ **`RC`·`RR` 은 `CS8852` · `RS` 는 통과**

**출력**

```text
===== 소스: cs18b-mut.cs =====
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
===== csc -out:ex.dll cs18b-mut.cs 2>&1 | sort (cc exit=1) =====
cs18b-mut.cs(11,9): error CS8852: Init-only property or indexer 'RR.X' can only be assigned in an object initializer, or on 'this' or 'base' in an instance constructor or an 'init' accessor.
cs18b-mut.cs(7,9): error CS8852: Init-only property or indexer 'RC.X' can only be assigned in an object initializer, or on 'this' or 'base' in an instance constructor or an 'init' accessor.
```

**왜 그런가**

- ★★★ **`record struct` 의 위치 속성은 `set`** 이다(1번의 `modreq` 없는 `set_Age`). Learn — 「위치 속성은 `record class` 와 `readonly record struct` 에서 **불변**, `record struct` 에서 **가변**」.
- ★★ **이름에 `record` 가 붙은 것은 「값 동등성을 만들어 달라」는 뜻**이지 「불변으로 하라」가 아니다. 불변은 **`readonly`** 가 준다.

### 5. ★★★ 배열은 **참조로 비교**되고, `with` 는 **리스트를 공유**한다

**출력**

```text
===== 소스: cs18b-shallow.cs =====
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
===== csc -out:ex.dll cs18b-shallow.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] new Arr(new[] {1,2}) == new Arr(new[] {1,2}) : False
[2] new Arr(shared) == new Arr(shared)         : True
[3] b.Xs.Add(2) 뒤 a.Xs.Count                   : 2
[4] ReferenceEquals(a, b) : False · ReferenceEquals(a.Xs, b.Xs) : True
[5] a == b                                     : True
[6] a.ToString()                               : Bag { Xs = System.Collections.Generic.List`1[System.Int32] }
```

**왜 그런가**

- ★★★ **`[1]` `False` · `[2]` `True`** — 배열 멤버는 `EqualityComparer<int[]>.Default` 로 비교되고 배열은 **참조 비교**다.
- ★★★ **`[3]` `2`** — `with {}` 는 **리스트의 참조만** 복사했다. `b.Xs.Add` 가 `a.Xs` 에도 보인다.
- ★★ **`[4]` `False` · `True`** — record 는 새 객체, 리스트는 **같은 객체**다. **`[5]` `True`** — 같은 리스트를 가리키니 멤버가 같다.
- ★ **`[6]`** — ``List`1[System.Int32]`` 뿐이다. **내용이 안 보인다.**

### 6. ★★ 진단은 **탐침 1 의 `CS8851` 하나** — 나머지 여섯은 침묵

**출력**

```text
===== 소스: cs18b-probe.cs =====
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
===== csc -nullable:enable -warn:9 -out:ex.dll cs18b-probe.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs18b-probe.cs(5,40): warning CS8851: 'R1' defines 'Equals' but not 'GetHashCode'
탐침 2 : new R2(new[] {1}) == new R2(new[] {1}) = False
탐침 4 : 넣은 뒤 k.X = 2 · set.Contains(k) = False · set.Contains(new R4(1)) = True
탐침 5 : new R5(x) == new R5(y) = True · x == y = False   (x, y 는 둘 다 double.NaN)
탐침 6 : 넣은 뒤 Y = 5 · set.Contains(r6) = False
===== csc -nullable:enable -warn:9 -out:ex.dll cs18b-probe.cs 2>&1 | grep -o "cs18b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 7개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
1
```

**왜 그런가**

- ★★★ **진단이 붙은 줄은 1** — `CS8851`(「`Equals` 를 정의했는데 `GetHashCode` 가 없다」).
- ★★★ **탐침 4 — `Contains(k)` `False` · `Contains(new R4(1))` `True`.** 셋이 가진 것은 **사본**이다.\
  `k.X = 2` 는 **내 변수만** 바꿨고 셋 안의 `R4(1)` 은 그대로다. ★★ **클래스 키였다면 셋 안의 그 객체가 바뀌어\
  `Contains(new …(1))` 도 `False` 가 됐을 것이다**(목록의 **19번 주제** 격자의 `R3`).
- ★★★ **탐침 5 — `new R5(x) == new R5(y)` 는 `True`, `x == y` 는 `False`.** 생성된 동등성은 필드를 **`double.Equals`** 로 비교하고\
  그것은 **`NaN` 을 `NaN` 과 같다고 본다.** `==` 연산자는 **IEEE** 라 `False` 다.
- ★★ **탐침 6 — `Contains` `False`.** 위치 밖의 `Y` 도 **필드**라 동등성과 해시에 들어가고, 넣은 뒤 바꾸니 **다른 칸**을 본다.
- ★ 탐침 2 는 5번 `[1]` 과 같은 모양이다(`False`).

### 7. ★★ **`with RC` 와 `RS.Equals(object)` 만 24000** — 네 판 모두

**출력**

```text
===== 소스: cs18b-alloc.cs =====
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
===== csc -out:ex.dll cs18b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
with RC           1000회 : 24000 바이트
with RS           1000회 : 0 바이트
with RR           1000회 : 0 바이트
== RC             1000회 : 0 바이트
== RS             1000회 : 0 바이트
== RR             1000회 : 0 바이트
RS.Equals(object) 1000회 : 24000 바이트
(합 3005000)
===== csc -out:ex.dll cs18b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
with RC           1000회 : 24000 바이트
with RS           1000회 : 0 바이트
with RR           1000회 : 0 바이트
== RC             1000회 : 0 바이트
== RS             1000회 : 0 바이트
== RR             1000회 : 0 바이트
RS.Equals(object) 1000회 : 24000 바이트
(합 3005000)
===== csc -optimize -out:exo.dll cs18b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
with RC           1000회 : 24000 바이트
with RS           1000회 : 0 바이트
with RR           1000회 : 0 바이트
== RC             1000회 : 0 바이트
== RS             1000회 : 0 바이트
== RR             1000회 : 0 바이트
RS.Equals(object) 1000회 : 24000 바이트
(합 3005000)
===== csc -optimize -out:exo.dll cs18b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
with RC           1000회 : 24000 바이트
with RS           1000회 : 0 바이트
with RR           1000회 : 0 바이트
== RC             1000회 : 0 바이트
== RS             1000회 : 0 바이트
== RR             1000회 : 0 바이트
RS.Equals(object) 1000회 : 24000 바이트
(합 3005000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 7
```

**왜 그런가**

- ★★★ **`with RC` 24000**(호출당 24) — `<Clone>$` 의 `newobj`. **`with RS`·`with RR` 은 0** — 대입 복사라 힙에 안 간다.
- ★★ **`==` 셋은 0** — 생성된 `op_Equality` 가 **`Equals(R)`** 를 부른다. **`RS.Equals(object)` 는 24000** — **인자 박싱**이다.
- ★★★ **네 판에서 갈린 줄 0 / 7** — 근거로 쓸 수 있다.
- ★★★ **「`record struct` 가 빠르다」고 말하면 안 된다** — 잰 것은 **할당**이고 **시간은 안 쟀다.**\
  ★ 구조체는 대입마다 **통째로 복사**하므로 멤버가 크면 다른 비용이 생긴다 — 그것도 **안 쟀다.**

### 8. ★★ **파서가 모른다** — 21 도 25 preview 도

**출력**

```text
===== 소스: j18/Ex18.java =====
record Pt(int x, int y) { }
public class Ex18 {
    public static void main(String[] a) {
        Pt p = new Pt(1, 2);
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
        System.out.println(q);
    }
}
===== javac -d j18out j18/Ex18.java (cc exit=1) =====
j18/Ex18.java:5: error: ';' expected
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                ^
j18/Ex18.java:5: error: not a statement
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                 ^
j18/Ex18.java:5: error: ';' expected
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                     ^
3 errors
===== ~/.sdkman/candidates/java/25.0.1-tem/bin/javac --enable-preview --release 25 -d j18out25 j18/Ex18.java (cc exit=1) =====
j18/Ex18.java:5: error: ';' expected
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                ^
j18/Ex18.java:5: error: not a statement
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                 ^
j18/Ex18.java:5: error: ';' expected
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                     ^
3 errors
===== 소스: j18/Ex18b.java =====
record Pt(int x, int y) {
    Pt withX(int nx) { return new Pt(nx, y); }      // 손으로 쓴 wither
}
public class Ex18b {
    public static void main(String[] a) {
        Pt p = new Pt(1, 2);
        System.out.println(p + " -> " + p.withX(9) + " · p.equals(new Pt(1, 2)) = " + p.equals(new Pt(1, 2)));
    }
}
===== javac -d j18out j18/Ex18b.java && java -cp j18out Ex18b (cc exit=0 · run exit=0) =====
Pt[x=1, y=2] -> Pt[x=9, y=2] · p.equals(new Pt(1, 2)) = true
```

**왜 그런가**

- ★★★ **`';' expected` · `not a statement`** — 파서가 `with` 를 **식의 일부로 모른다.** 문법 단계에서 막혔다.
- ★★ **javac 25 `--enable-preview --release 25` 도 같다** — 이 판에서는 **미리보기로도 없다.**
- ★ Java 는 **`withX` 같은 메서드를 손으로** 쓴다. 동등성은 C# record 와 같게 **값 동등**이다(`true`).

### 9. ★★ **참조가 같나 · 실제 타입이 같나** — 그다음에 필드

**출력**

```text
===== 소스: cs18b-eqil.cs =====
using System;
record Pt(int X);
class Program {
    static void Main() {
        Il.Dump(typeof(Pt), "Equals", typeof(Pt));
        Il.Dump(typeof(Pt), "GetHashCode");
        Il.Dump(typeof(Pt), "op_Equality");
    }
}
===== csc -optimize -r:il.dll -out:ex.dll cs18b-eqil.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Pt.Equals(Pt) ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: beq.s IL_0033
  IL_0004: ldarg.1
  IL_0005: brfalse.s IL_0031
  IL_0007: ldarg.0
  IL_0008: callvirt Pt::get_EqualityContract
  IL_000d: ldarg.1
  IL_000e: callvirt Pt::get_EqualityContract
  IL_0013: call System.Type::op_Equality
  IL_0018: brfalse.s IL_0031
  IL_001a: call System.Collections.Generic.EqualityComparer<System.Int32>::get_Default
  IL_001f: ldarg.0
  IL_0020: ldfld Pt::<X>k__BackingField
  IL_0025: ldarg.1
  IL_0026: ldfld Pt::<X>k__BackingField
  IL_002b: callvirt System.Collections.Generic.EqualityComparer<System.Int32>::Equals
  IL_0030: ret
  IL_0031: ldc.i4.0
  IL_0032: ret
  IL_0033: ldc.i4.1
  IL_0034: ret
--- Pt.GetHashCode ---
  IL_0000: call System.Collections.Generic.EqualityComparer<System.Type>::get_Default
  IL_0005: ldarg.0
  IL_0006: callvirt Pt::get_EqualityContract
  IL_000b: callvirt System.Collections.Generic.EqualityComparer<System.Type>::GetHashCode
  IL_0010: ldc.i4 -1521134295
  IL_0015: mul
  IL_0016: call System.Collections.Generic.EqualityComparer<System.Int32>::get_Default
  IL_001b: ldarg.0
  IL_001c: ldfld Pt::<X>k__BackingField
  IL_0021: callvirt System.Collections.Generic.EqualityComparer<System.Int32>::GetHashCode
  IL_0026: add
  IL_0027: ret
--- Pt.op_Equality ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: beq.s IL_0011
  IL_0004: ldarg.0
  IL_0005: brfalse.s IL_000f
  IL_0007: ldarg.0
  IL_0008: ldarg.1
  IL_0009: callvirt Pt::Equals
  IL_000e: ret
  IL_000f: ldc.i4.0
  IL_0010: ret
  IL_0011: ldc.i4.1
  IL_0012: ret
```

**왜 그런가**

- ★★★ **`beq.s`** — 같은 참조면 곧장 `true`. 그다음 **`EqualityContract` 둘을 `Type::op_Equality`** 로 비교한다.
- ★★★ **필드는 `EqualityComparer<T>.Default.Equals`** — `double` 이면 `double.Equals`(**`NaN` 이 같다**, 6번 탐침 5),\
  배열이면 **참조 비교**(5번 `[1]`).
- ★★★ **`op_Equality` 는 참조 비교 → 널 확인 → `callvirt Pt::Equals`** — **`==` 가 `Equals` 를 부르므로 둘이 어긋날 수 없다.**\
  ★ 목록의 **19번 주제**의 「`Equals` 만 고친 클래스에서 `==` 가 여전히 참조 비교」는 **record 에서는 원리상 안 난다.**
- ★★ **`-1521134295` 는 약속이 아니다** — Roslyn 의 구현이다. 명세는 「같은 값이면 같은 해시」만 약속한다.

### 10. ★ **`CS0111`** — `Equals(R)` 만 문이 열려 있다

**출력**

```text
===== 소스: cs18b-dup.cs =====
record R(int X) {
    public override bool Equals(object o) => false;       // 컴파일러가 만드는 것을 손으로 쓴다
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs18b-dup.cs (cc exit=1) =====
cs18b-dup.cs(2,26): error CS0111: Type 'R' already defines a member called 'Equals' with the same parameter types
```

**왜 그런가**

- ★★★ **`Equals(object)` 를 쓰면 `CS0111`** — 컴파일러가 이미 만든 것과 겹친다. Learn — 「명시적으로 선언하면 **에러**」.
- ★★ **`Equals(R)` 는 쓸 수 있다** — 대신 **`GetHashCode` 를 같이** 써야 하고, 안 쓰면 **`CS8851`**(6번 탐침 1).
- ★★★ **유일한 문은 `Equals(R)` + `GetHashCode`** — `==`·`Equals(object)` 는 그것을 **부르도록 생성되므로** 자동으로 따라온다(9번).

### 11. 잇기

- ★★★ **`init`·`modreq(IsExternalInit)`** — [13번](../13-properties-init-required-field/).
- ★★ **`readonly record struct` 의 `CS8852`** 는 [02번](../02-struct-vs-class-choosing/)이 먼저 찍었다 — 거기는 **`readonly record struct` 만** 던졌고,\
  ★★★ **이 문서가 `record struct`(readonly 없이)의 가변을 처음 찍었다**(4번).
- ★★★ 9번의 **생성된 `op_Equality` 가 `Equals` 를 부르는 IL** 이 목록의 **19번 주제**의 「**`==` 와 `Equals` 가 어긋나는 사고**」가 record 에서 안 나는 이유다.
- ★ Java record 의 **`invokedynamic` 동등성** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **14번**([`14-records/`](../../../java/syntax/14-records/)).\
  Kotlin `copy` 가 **본문 프로퍼티를 되돌린다**는 것은 Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **22번**([`22-data-class-generated-members/`](../../../kotlin/syntax/22-data-class-generated-members/)).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs18b-gen.cs` 생성 멤버 | csc 1회 · 네 타입 | ★★★ **16 · 13 · 13 · 5** · `RS` 만 `set` |
| `cs18b-with.cs` `with` IL | csc 1회 | ★★★ **`<Clone>$` → `set_Age`** · 복제 본문은 **`RC(RC)` protected** · struct 는 복제 없음 |
| `cs18b-eqil.cs` 동등성 IL | csc 1회(`-optimize`) | ★★★ **`beq` 지름길 → `EqualityContract` → 필드별 `EqualityComparer`** · `op_Equality` → `Equals` |
| `cs18b-contract.cs` 파생 record | csc 1회 | ★★★ **셋 다 `False`** · `with` 결과 `Tagged` |
| `cs18b-mut.cs` 위치 속성 대입 | csc 1회 | ★★★ **`CS8852` 둘** · `RS` 통과 |
| `cs18b-alloc.cs` 할당 바이트 | **2×2 판 격자** | ★★★ `with RC`·`RS.Equals(object)` **24000** · 나머지 **0** · **갈린 줄 0 / 7** |
| `cs18b-shallow.cs` 얕음 | csc 1회 | ★★★ 배열 **참조 비교** · `with` 가 **리스트 공유** |
| `cs18b-probe.cs` 탐침 일곱 | csc 1회(`-warn:9`) + 실행 | ★★★ **진단이 붙은 줄 1**(`CS8851`) · `NaN` 이 같다 · struct 키는 사본 |
| `cs18b-dup.cs` `Equals(object)` 손으로 | csc 1회 | ★★★ **`CS0111`** |
| `Ex18.java` · `Ex18b.java` | javac 21 두 번 · javac 25 한 번 | ★★★ **`with` 는 파서가 모른다**(25 preview 도) |
| `cs18b-form.cs` 형태 | csc 1회 | `민수,31 / True` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · Roslyn · javac 21.0.5 · 25.0.1)에서만** 그렇다.

- ★★★ **복제 메서드 이름 `<Clone>$`** · **`Equals` 의 `beq` 지름길** · **해시 상수 `-1521134295`** · **`EqualityComparer<T>.Default` 경유** — 전부 **Roslyn 이 짠 IL 모양**이다.
- ★★ **`with RC` 호출당 24바이트** — 객체 크기는 런타임 배치다.
- ★★ **`-warn:9` 탐침 일곱 중 하나만 답한 것** · ★ **javac 25 preview 에 `with` 가 없는 것** — 다음 판에서 바뀔 수 있다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **생성 멤버의 목록** · **위치 속성의 `init`/`set` 구분** · **`with` 가 복제 후 설정하고 결과가 런타임 타입인 것**.
- **파생 record 는 실제 타입이 같아야 같다**(`EqualityContract`) · **`Equals(object)` 를 손으로 못 쓴다**.
- **동등성이 선언한 모든 필드를 본다** · **`with` 는 얕다**(Learn: 「결과는 **얕은 복사**」).

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **`sealed record` 의 생성 멤버 한정자** · ★★ **사용자 정의 복사 생성자**(깊은 복사) ·\
  ★ **본문 `init` 속성이 `with` 에서 어떻게 복사되나**(Kotlin `copy` 와의 대비를 값으로) · ★ **`record struct` 의 매개변수 없는 생성자** ·\
  ★ **C# 15 의 `closed` record**(이 판의 `latest` 범위 밖).
- **못 잰 것** — ★★★ **「record 가 빠르다/느리다」.** 할당만 쟀고 **시간은 한 줄도 안 쟀다.**
- **잴 것이 없는 것** — 없다. **④ 할당 바이트는 적용**이다(`with` 가 새 객체를 만든다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **9번의 IL** — Roslyn 이 생성 코드 모양을 바꾸면 **지름길·상수**가 움직인다. **목록(1번)은 안 움직여야 한다** — 움직이면 그것이 뉴스다.
- ★★ **8번의 javac** — Java 에 파생 record 생성 문법이 들어오면 그 블록이 바뀐다. **판과 날짜를 같이 적어라.**
- ★★ **7번의 판 격자** — JIT 이 `with` 의 복제를 스택으로 내리면 `24000` 이 움직인다. **그때도 2×2 로 재라.**
