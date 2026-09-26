# csharp/syntax/28 — 람다식과 클로저 캡처 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트·GC 결과는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **옵코드 · 컴파일러가 만든 타입의 필드·메서드 · 진단 코드 · 「회수됐나」 참/거짓 · 스크립트가 센 줄 수** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「`static` 람다가 빠르다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`20`** — `n` 은 **`<>c__DisplayClass0_0` 의 필드**가 됐다 · `static` 람다의 IL 은 **같다**

**출력**

```text
===== 소스: cs28b-il.cs =====
using System;
using System.Linq;
using System.Reflection;
public static class Probe {
    public static Func<int> Capture() {
        int n = 10;
        Func<int> f = () => n;
        n = 20;
        return f;
    }
    public static Func<int, int> NoCapture() => x => x + 1;
    public static Func<int, int> StaticLambda() => static x => x + 1;
}
class Program {
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    static void Main() {
        Console.WriteLine($"[0] Probe.Capture()() = {Probe.Capture()()}");
        foreach (var n in new[] { "Capture", "NoCapture", "StaticLambda" }) Il.Dump(typeof(Probe), n);
        foreach (var t in typeof(Probe).GetNestedTypes(BindingFlags.NonPublic).OrderBy(t => t.Name, StringComparer.Ordinal)) {
            Console.WriteLine($"=== 컴파일러가 만든 타입 {t.Name} (sealed={t.IsSealed})");
            foreach (var f in t.GetFields(All).OrderBy(f => f.Name, StringComparer.Ordinal))
                Console.WriteLine($"    필드   {(f.IsStatic ? "static " : "")}{f.FieldType.Name} {f.Name}");
            foreach (var m in t.GetMethods(All).OrderBy(m => m.Name, StringComparer.Ordinal)) {
                Console.WriteLine($"    메서드 {(m.IsStatic ? "static " : "")}{m.Name}");
                Il.Dump(t, m.Name);
            }
        }
    }
}
===== csc -r:il.dll -out:ex.dll cs28b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[0] Probe.Capture()() = 20
--- Probe.Capture ---
  .locals [0] Probe+<>c__DisplayClass0_0
  .locals [1] System.Func<System.Int32>
  .locals [2] System.Func<System.Int32>
  IL_0000: newobj Probe+<>c__DisplayClass0_0::.ctor
  IL_0005: stloc.0
  IL_0006: nop
  IL_0007: ldloc.0
  IL_0008: ldc.i4.s 10
  IL_000a: stfld Probe+<>c__DisplayClass0_0::n
  IL_000f: ldloc.0
  IL_0010: ldftn Probe+<>c__DisplayClass0_0::<Capture>b__0
  IL_0016: newobj System.Func<System.Int32>::.ctor
  IL_001b: stloc.1
  IL_001c: ldloc.0
  IL_001d: ldc.i4.s 20
  IL_001f: stfld Probe+<>c__DisplayClass0_0::n
  IL_0024: ldloc.1
  IL_0025: stloc.2
  IL_0026: br.s IL_0028
  IL_0028: ldloc.2
  IL_0029: ret
--- Probe.NoCapture ---
  IL_0000: ldsfld Probe+<>c::<>9__1_0
  IL_0005: dup
  IL_0006: brtrue.s IL_001f
  IL_0008: pop
  IL_0009: ldsfld Probe+<>c::<>9
  IL_000e: ldftn Probe+<>c::<NoCapture>b__1_0
  IL_0014: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_0019: dup
  IL_001a: stsfld Probe+<>c::<>9__1_0
  IL_001f: ret
--- Probe.StaticLambda ---
  IL_0000: ldsfld Probe+<>c::<>9__2_0
  IL_0005: dup
  IL_0006: brtrue.s IL_001f
  IL_0008: pop
  IL_0009: ldsfld Probe+<>c::<>9
  IL_000e: ldftn Probe+<>c::<StaticLambda>b__2_0
  IL_0014: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_0019: dup
  IL_001a: stsfld Probe+<>c::<>9__2_0
  IL_001f: ret
=== 컴파일러가 만든 타입 <>c (sealed=True)
    필드   static <>c <>9
    필드   static Func`2 <>9__1_0
    필드   static Func`2 <>9__2_0
    메서드 <NoCapture>b__1_0
--- <>c.<NoCapture>b__1_0 ---
  IL_0000: ldarg.1
  IL_0001: ldc.i4.1
  IL_0002: add
  IL_0003: ret
    메서드 <StaticLambda>b__2_0
--- <>c.<StaticLambda>b__2_0 ---
  IL_0000: ldarg.1
  IL_0001: ldc.i4.1
  IL_0002: add
  IL_0003: ret
=== 컴파일러가 만든 타입 <>c__DisplayClass0_0 (sealed=True)
    필드   Int32 n
    메서드 <Capture>b__0
--- <>c__DisplayClass0_0.<Capture>b__0 ---
  IL_0000: ldarg.0
  IL_0001: ldfld Probe+<>c__DisplayClass0_0::n
  IL_0006: ret
```

**왜 그런가**

- ★★★ **`[0]` `20`** — 람다는 값 `10` 이 아니라 **변수 `n`** 을 캡처했다.
- ★★★ **첫 명령 `newobj Probe+<>c__DisplayClass0_0::.ctor`** · `n = 10`·`n = 20` 은 **둘 다 `stfld …::n`** — 메서드와 람다가 **같은 필드**를 본다.
- ★★★ **타입 둘** — `<>c`(필드 `static <>c <>9` · ``static Func`2 <>9__1_0`` · `<>9__2_0`, 메서드 두 람다 몸통)와 `<>c__DisplayClass0_0`(필드 `Int32 n`, 메서드 `<Capture>b__0` = `ldarg.0` · `ldfld n`). 둘 다 `sealed=True`.
- ★★ **`NoCapture` 와 `StaticLambda` 는 캐시 필드 이름(`__1_0`/`__2_0`)만 다르고 같다** — 몸통 IL 도 같다. `static` 은 **컴파일 검사**일 뿐이다.

### 2. ★★ **`a` `CS8820` · `b`·`c` `CS8821`** — `d`·`e` 는 통과 · 8 판은 **`CS8400` 다섯**

**출력**

```text
===== 소스: cs28b-static.cs =====
using System;
class Program {
    int field = 1;
    const int K = 5;
    static int S = 2;
    void M() {
        int local = 3;
        Func<int> a = static () => local;
        Func<int> b = static () => field;
        Func<int> c = static () => this.field;
        Func<int> d = static () => K + S;
        Func<int, int> e = static x => x * K;
    }
    static void Main() { }
}
===== csc -out:ex.dll cs28b-static.cs 2>&1 | sort (cc exit=1) =====
cs28b-static.cs(10,36): error CS8821: A static anonymous function cannot contain a reference to 'this' or 'base'.
cs28b-static.cs(8,36): error CS8820: A static anonymous function cannot contain a reference to 'local'.
cs28b-static.cs(9,36): error CS8821: A static anonymous function cannot contain a reference to 'this' or 'base'.
===== csc -langversion:8 -out:ex.dll cs28b-static.cs 2>&1 | sort (cc exit=1) =====
cs28b-static.cs(10,23): error CS8400: Feature 'static anonymous function' is not available in C# 8.0. Please use language version 9.0 or greater.
cs28b-static.cs(10,36): error CS8821: A static anonymous function cannot contain a reference to 'this' or 'base'.
cs28b-static.cs(11,23): error CS8400: Feature 'static anonymous function' is not available in C# 8.0. Please use language version 9.0 or greater.
cs28b-static.cs(12,28): error CS8400: Feature 'static anonymous function' is not available in C# 8.0. Please use language version 9.0 or greater.
cs28b-static.cs(8,23): error CS8400: Feature 'static anonymous function' is not available in C# 8.0. Please use language version 9.0 or greater.
cs28b-static.cs(8,36): error CS8820: A static anonymous function cannot contain a reference to 'local'.
cs28b-static.cs(9,23): error CS8400: Feature 'static anonymous function' is not available in C# 8.0. Please use language version 9.0 or greater.
cs28b-static.cs(9,36): error CS8821: A static anonymous function cannot contain a reference to 'this' or 'base'.
```

**왜 그런가**

- ★★★ **지역 변수는 `CS8820`, 인스턴스 필드는 `this` 를 거치므로 `CS8821`** — 둘 다 **캡처가 필요한 것**이다.
- ★★ **`K + S` · `x * K`** — 상수와 정적 필드는 캡처가 아니다(Learn). **`-langversion:8` 은 `static` 이 적힌 다섯 자리에 `CS8400 … 9.0 or greater`** 를 더한다.

### 3. ★★★ **`3 3 3` · `0 1 2` · `2 2 2`** — 판 넷에서 **안 바뀐다**

**출력**

```text
===== 소스: cs28b-loop.cs =====
using System;
using System.Collections.Generic;
class Program {
    static string Run(List<Func<int>> fs) { string s = ""; foreach (var f in fs) s += f() + " "; return s.TrimEnd(); }
    static void Main() {
        var a = new List<Func<int>>();
        for (int i = 0; i < 3; i++) a.Add(delegate { return i; });
        var b = new List<Func<int>>();
        foreach (int j in new int[] { 0, 1, 2 }) b.Add(delegate { return j; });
        var c = new List<Func<int>>();
        IEnumerator<int> e = ((IEnumerable<int>)new int[] { 0, 1, 2 }).GetEnumerator();
        int k;
        while (e.MoveNext()) { k = e.Current; c.Add(delegate { return k; }); }
        Console.WriteLine("for=" + Run(a) + ";foreach=" + Run(b) + ";hand=" + Run(c));
    }
}
===== csc -langversion:3 -out:ex.dll cs28b-loop.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
for=3 3 3;foreach=0 1 2;hand=2 2 2
===== csc -langversion:4 -out:ex.dll cs28b-loop.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
for=3 3 3;foreach=0 1 2;hand=2 2 2
===== csc -langversion:5 -out:ex.dll cs28b-loop.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
for=3 3 3;foreach=0 1 2;hand=2 2 2
===== csc -langversion:latest -out:ex.dll cs28b-loop.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
for=3 3 3;foreach=0 1 2;hand=2 2 2
===== 판 대조 — 칸마다(for · foreach · hand) 판 넷의 값이 같은가 =====
for — [C# 3] 3 3 3  [C# 4] 3 3 3  [C# 5] 3 3 3  [C# latest] 3 3 3
foreach — [C# 3] 0 1 2  [C# 4] 0 1 2  [C# 5] 0 1 2  [C# latest] 0 1 2
hand — [C# 3] 2 2 2  [C# 4] 2 2 2  [C# 5] 2 2 2  [C# latest] 2 2 2
판에 따라 갈린 칸 0 / 3
===== 소스: cs28b-ctl.cs =====
class Program { static void Main() { int n = 1; System.Console.WriteLine($"{n}"); } }
===== csc -langversion:3 -out:ex.dll cs28b-ctl.cs (cc exit=1) =====
cs28b-ctl.cs(1,74): error CS8024: Feature 'interpolated strings' is not available in C# 3. Please use language version 6 or greater.
```

**왜 그런가**

- ★★★ **`for` 는 변수 하나**(끝난 뒤 `3`) · **`foreach` 는 반복마다 새 변수** · **`hand` 는 C# 4 식 풀이**(`while` 밖의 `k` 하나 · 마지막 대입 `2`).
- ★★★ **C# 3·4 로 던져도 `foreach` 가 `0 1 2`** — 판에 따라 갈린 칸 **0 / 3**. 대조군이 `-langversion:3` 에서 `CS8024` 로 막혀 **판 플래그는 살아 있음**을 보였다 — **Roslyn 이 이 의미를 판에 안 묶었다.**
- ★★ **`hand` `2 2 2` 대 `for` `3 3 3`** — 숫자가 다르다. 옛 `foreach` 는 **마지막 원소**를, `for` 는 **루프가 끝난 뒤의 증가 값**을 본다.

### 4. ★★★ **`False` · `True` · `True` · `False` · `True`** — 네 판 **0 / 5**

**출력**

```text
===== 소스: cs28b-life.cs =====
using System;
using System.Runtime.CompilerServices;
class Program {
    static Func<int>? keep;
    [MethodImpl(MethodImplOptions.NoInlining)]
    static WeakReference Make(bool hold) {
        var big = new byte[10_000_000];
        Func<int> f = () => big.Length;
        if (hold) keep = f;
        return new WeakReference(big);
    }
    [MethodImpl(MethodImplOptions.NoInlining)]
    static WeakReference MakeSibling() {
        var big = new byte[10_000_000];
        int small = 1;
        Func<int> usesBig = () => big.Length;
        Func<int> usesSmall = () => small;
        keep = usesSmall;
        return new WeakReference(big);
    }
    static bool Collected(WeakReference w) { GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect(); return !w.IsAlive; }
    static void Main() {
        var w1 = Make(hold: true);
        Console.WriteLine($"[1] 람다를 정적 필드에 둔 채 GC · big 회수됐나 : {Collected(w1)}");
        keep = null;
        Console.WriteLine($"[2] 정적 필드를 비운 뒤 GC · big 회수됐나     : {Collected(w1)}");
        var w2 = Make(hold: false);
        Console.WriteLine($"[3] 람다를 어디에도 안 둔 경우 GC · big 회수됐나 : {Collected(w2)}");
        var w3 = MakeSibling();
        Console.WriteLine($"[4] usesSmall 만 정적 필드에 둔 채 GC · big 회수됐나 : {Collected(w3)}");
        keep = null;
        Console.WriteLine($"[5] 그것도 비운 뒤 GC · big 회수됐나           : {Collected(w3)}");
    }
}
===== csc -nullable:enable -out:ex.dll cs28b-life.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 람다를 정적 필드에 둔 채 GC · big 회수됐나 : False
[2] 정적 필드를 비운 뒤 GC · big 회수됐나     : True
[3] 람다를 어디에도 안 둔 경우 GC · big 회수됐나 : True
[4] usesSmall 만 정적 필드에 둔 채 GC · big 회수됐나 : False
[5] 그것도 비운 뒤 GC · big 회수됐나           : True
===== csc -nullable:enable -out:ex.dll cs28b-life.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 람다를 정적 필드에 둔 채 GC · big 회수됐나 : False
[2] 정적 필드를 비운 뒤 GC · big 회수됐나     : True
[3] 람다를 어디에도 안 둔 경우 GC · big 회수됐나 : True
[4] usesSmall 만 정적 필드에 둔 채 GC · big 회수됐나 : False
[5] 그것도 비운 뒤 GC · big 회수됐나           : True
===== csc -nullable:enable -optimize -out:exo.dll cs28b-life.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] 람다를 정적 필드에 둔 채 GC · big 회수됐나 : False
[2] 정적 필드를 비운 뒤 GC · big 회수됐나     : True
[3] 람다를 어디에도 안 둔 경우 GC · big 회수됐나 : True
[4] usesSmall 만 정적 필드에 둔 채 GC · big 회수됐나 : False
[5] 그것도 비운 뒤 GC · big 회수됐나           : True
===== csc -nullable:enable -optimize -out:exo.dll cs28b-life.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] 람다를 정적 필드에 둔 채 GC · big 회수됐나 : False
[2] 정적 필드를 비운 뒤 GC · big 회수됐나     : True
[3] 람다를 어디에도 안 둔 경우 GC · big 회수됐나 : True
[4] usesSmall 만 정적 필드에 둔 채 GC · big 회수됐나 : False
[5] 그것도 비운 뒤 GC · big 회수됐나           : True
===== 네 판 대조 — 「회수됐나」 줄마다 네 판의 참/거짓이 같은가 =====
네 판에서 갈린 줄 0 / 5 · 첫 판에서 「회수됨(True)」 줄 3 / 5
```

**왜 그런가**

- ★★★ **`[1]` `False`** — 정적 필드의 람다가 디스플레이 객체를 붙들고, 그 객체가 `big` 을 붙든다. **`[2]`·`[3]` `True`** — 붙든 것이 없으면 풀린다.
- ★★★ **`[4]` `False`** — `usesSmall` 과 `usesBig` 은 **같은 범위라 디스플레이 객체 하나**를 나눠 쓴다. `usesSmall` 의 `Target` 에 `big` 필드도 있다. **`[5]` 비우면 `True`.**
- ★ **네 판에서 갈린 줄 0 / 5** — 최적화·티어링과 무관했다(`NoInlining` 메서드 안에서 만들어 지역 변수 수명의 영향을 뺐다).

### 5. ★★★ **`1` · `2` · `102 · 102`** — Java 는 **둘 다 `effectively final` 에러**

**출력**

```text
===== 소스: cs28b-mut.cs =====
using System;
class Program {
    static void Main() {
        int count = 1;
        Func<int> read = () => count;
        Action bump = () => count += 100;
        Console.WriteLine($"[1] read() = {read()}");
        count = 2;
        Console.WriteLine($"[2] count = 2 뒤 read() = {read()}");
        bump();
        Console.WriteLine($"[3] bump() 뒤 count = {count} · read() = {read()}");
    }
}
===== csc -out:ex.dll cs28b-mut.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] read() = 1
[2] count = 2 뒤 read() = 2
[3] bump() 뒤 count = 102 · read() = 102
```

```text
===== 소스: G28a.java =====
import java.util.function.IntSupplier;
class G28a {
    void f() {
        int count = 1;
        IntSupplier read = () -> count;
        count = 2;
    }
}
===== javac -d j28out j28/G28a.java (cc exit=1) =====
j28/G28a.java:5: error: local variables referenced from a lambda expression must be final or effectively final
        IntSupplier read = () -> count;
                                 ^
1 error
===== 소스: G28b.java =====
class G28b {
    void f() {
        int count = 1;
        Runnable bump = () -> count += 100;
    }
}
===== javac -d j28out j28/G28b.java (cc exit=1) =====
j28/G28b.java:4: error: local variables referenced from a lambda expression must be final or effectively final
        Runnable bump = () -> count += 100;
                              ^
1 error
===== 소스: Ex28.java =====
import java.util.function.IntSupplier;
public class Ex28 {
    public static void main(String[] args) {
        int[] count = { 1 };
        IntSupplier read = () -> count[0];
        count[0] = 2;
        System.out.println("count[0] = 2 뒤 read() = " + read.getAsInt());
    }
}
===== javac -d j28out j28/Ex28.java && java -cp j28out Ex28 (cc exit=0 · run exit=0) =====
count[0] = 2 뒤 read() = 2
```

**왜 그런가**

- ★★★ **C#** — 바깥의 `count = 2` 를 람다가 보고(`[2]`), 람다 안의 `count += 100` 을 바깥이 본다(`[3]`). **필드 하나를 셋이 공유**한다.
- ★★★ **Java** — `G28a`(캡처 뒤 대입)·`G28b`(람다 안 대입) 둘 다 **`local variables referenced from a lambda expression must be final or effectively final`**. Java 는 **값을 복사해 캡처**하므로 바꿀 수 있으면 갈라진다 — 그래서 막는다. 우회 `int[]` 상자는 `2` 를 본다.

### 6. ★★ **64024 · 0 · 0** — `[2]` 와 `[3]` 은 **같다**

**출력**

```text
===== 소스: cs28b-alloc.cs =====
using System;
class Program {
    static int Use(Func<int, int> f) => f(1);
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        long sink = 0;
        Console.WriteLine($"[1] 캡처하는 람다  Use(x => x + i)       1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(x => x + i); })} 바이트");
        Console.WriteLine($"[2] 캡처 없는 람다 Use(x => x + 1)       1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(x => x + 1); })} 바이트");
        Console.WriteLine($"[3] static 람다    Use(static x => x + 1) 1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(static x => x + 1); })} 바이트");
        GC.KeepAlive(sink);
    }
}
===== csc -out:ex.dll cs28b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 캡처하는 람다  Use(x => x + i)       1000번 : 64024 바이트
[2] 캡처 없는 람다 Use(x => x + 1)       1000번 : 0 바이트
[3] static 람다    Use(static x => x + 1) 1000번 : 0 바이트
===== csc -out:ex.dll cs28b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 캡처하는 람다  Use(x => x + i)       1000번 : 64024 바이트
[2] 캡처 없는 람다 Use(x => x + 1)       1000번 : 0 바이트
[3] static 람다    Use(static x => x + 1) 1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs28b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] 캡처하는 람다  Use(x => x + i)       1000번 : 64024 바이트
[2] 캡처 없는 람다 Use(x => x + 1)       1000번 : 0 바이트
[3] static 람다    Use(static x => x + 1) 1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs28b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] 캡처하는 람다  Use(x => x + i)       1000번 : 64024 바이트
[2] 캡처 없는 람다 Use(x => x + 1)       1000번 : 0 바이트
[3] static 람다    Use(static x => x + 1) 1000번 : 0 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 3
```

**왜 그런가**

- ★★★ **캡처 없는 람다와 `static` 람다는 둘 다 0** — `<>c` 캐시(1번 IL 이 같다). **`static` 이 할당을 줄이는 것이 아니다.**
- ★★ **`+24` 는 디스플레이 객체 하나** — 캡처된 `i` 가 **`for` 변수라 루프 전체에 객체 하나**이고(3·7번), 반복마다 생기는 것은 **64바이트 델리게이트** 1000개뿐이다.

### 7. ★★★ **`for` 는 루프 앞 `IL_0000` 에서 한 번, `foreach` 는 몸통 `IL_0006` 에서 반복마다**

- ★★★ 요약 (4)의 덤프 — `For` 는 `newobj <>c__DisplayClass0_0` 가 **첫 명령**이고 `i` 의 증가·비교가 **그 객체의 필드**(`ldfld`/`stfld …::i`)로 돈다. `Foreach` 는 **`blt.s IL_0006` 이 되돌아오는 자리**에 `newobj <>c__DisplayClass1_0` 가 있다. **객체가 하나면 `3 3 3`, 반복마다면 `0 1 2`.**

### 8. ★★★ **명세 · Roslyn · Roslyn 의 귀결** — `foreach` 의미는 **판 플래그에 안 묶였다**

- ★★★ **「변수를 캡처한다」는 언어 명세**(5번의 양방향이 그 증거) · **디스플레이 클래스는 Roslyn 구현**(이름·모양) · **형제 누수는 「범위마다 객체 하나」라는 Roslyn 구현의 귀결**(명세는 「도달 가능한 동안 산다」까지만).
- ★★ **C# 5 의 `foreach` 변화는 `-langversion` 과 무관하게 적용된다** — 판 넷이 같았고(3번), 대조군으로 플래그가 살아 있음을 확인했다. 그래서 옛 의미는 **손으로 적은 풀이(`hand`)** 로 쪼개 보였다.

### 9. ★★ **성능이 아니라 실수 방지**다

- ★★ 1번 — IL 이 캡처 없는 람다와 **같다**. 6번 — 할당도 **같다(0)**. 이득은 **「캡처하면 에러」**(2번 `CS8820`·`CS8821`) — 뜨거운 경로에서 **캡처가 몰래 끼어드는 것**(→ 호출마다 할당, 6번 `[1]`)을 컴파일 시점에 막는다.

### 10. ★★ **`for` = JS `var`·Go 1.21 (`3 3 3`) · `foreach` = JS `let`·Go 1.22 (`0 1 2`) · 옛 `foreach` = Python (`2 2 2`)**

- ★★ [Go 13번](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/) (2) · [JS 05번](../../../js/syntax/05-var-let-const-and-tdz/) (4) · [Python 22번](../../../python/syntax/22-closures-and-late-binding/)의 실측을 인용했다.
- ★ **Go 는 파일 첫 줄 `//go:build go1.21` 로 언어 판을 파일마다 골라** 한 빌드에서 두 의미를 냈다. **C# 은 판 플래그를 바꿔도 `foreach` 의미가 안 바뀐다**(3번) — 되살릴 레버가 없다.

### 11. 잇기

- ★★ **[`variables-and-memory/`](../../../../variables-and-memory/) §9 「람다 함수」** — 파이썬 `lambda` 로 이름 없는 함수의 **개념**만 다룬다. **캡처는 그 절에 없다.**
- ★ **(5) 수명 연장**과 같은 뿌리 — 이벤트가 구독자의 델리게이트를 붙들면 대상이 안 풀린다. 목록의 **29번 주제**.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs28b-il.cs` | csc 1회 · 실행 1회 | ★★★ `<>c__DisplayClass0_0` 필드 `n` · `<>c` 싱글턴·캐시 · `static` 람다 IL 동일 |
| `cs28b-static.cs` | csc 2회(latest · `8`) | `CS8820` · `CS8821` ×2 · 8 판 `CS8400` ×5 |
| `cs28b-loop.cs` + `cs28b-ctl.cs` | csc 4회(3·4·5·latest) + 격자 4회 + 대조 1회 · 실행 8회 | ★★★ `3 3 3` · `0 1 2` · `2 2 2` · **판에 따라 갈린 칸 0 / 3** |
| `cs28b-loopil.cs` | csc 1회(`-optimize`) · 실행 1회 | `for` 는 루프 앞 · `foreach` 는 루프 안 `newobj` |
| `cs28b-life.cs` | **2×2 판 격자** | ★★★ `False` · `True` · `True` · `False` · `True` · **갈린 줄 0 / 5** |
| `cs28b-mut.cs` | csc 1회 · 실행 1회 | `1` · `2` · `102 · 102` |
| `G28a`·`G28b`·`Ex28.java` | javac 3회 · java 1회 | ★★★ `effectively final` ×2 · `int[]` 우회 `2` |
| `cs28b-alloc.cs` | **2×2 판 격자** | 64024 · 0 · 0 · **갈린 줄 0 / 3** |
| `cs28b-form.cs` | csc 1회 · 실행 1회 | `15 · 24 · calls=2 · 1,2,3` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **디스플레이 클래스의 이름·모양·범위당 하나 · `<>c` 의 모양 · 람다 몸통이 인스턴스 메서드인 것 · `foreach` 의미가 판에 안 묶인 것** — Roslyn · ★ 할당 바이트 값.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **변수 캡처(값이 아니다) · `foreach` 반복마다 새 변수 · `for` 는 하나 · `static` 람다의 캡처 금지 · 캡처된 변수는 델리게이트가 살아 있는 동안 산다.**

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ 로컬 함수의 구조체 캡처 · `this` 만 캡처하는 람다 · 범위가 여럿인 디스플레이 사슬 · C# 4 **이전 컴파일러**(옛 `foreach` 의 실제 출력 — 이 판에 없다).
- **못 잰 것** — ★★★ **시간** · ★★ **GC 가 언제 회수하나**(시점 — 「이 시점에 도달 가능한가」만 물었다).
- **잴 것이 없는 것** — 없다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번** — Roslyn 이 범위를 **람다마다** 쪼개게 되면 `[4]` 가 `True` 로 움직인다.
- ★★ **1·6번** — `static` 람다를 **정적 메서드**로 내게 되면 IL 이 갈린다(할당도 다시 재라).
