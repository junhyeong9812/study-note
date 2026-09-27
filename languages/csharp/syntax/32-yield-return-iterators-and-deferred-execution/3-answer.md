# csharp/syntax/32 — `yield return` 반복자와 지연 실행 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **실행 로그의 줄 수와 순서 · 상태 값 · 옵코드 · 진단 코드 · 스크립트가 센 「N / M」** 이다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「LINQ 는 느리다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`[1]`·`[2]` 뒤 0 줄** — `MoveNext` 마다 한 토막 · `[6]` 은 `본문: 끝` 뒤 **`False`**

**출력**

```text
===== 소스: cs32b-lazy.cs =====
using System;
using System.Collections.Generic;
class Program {
    static IEnumerable<int> Numbers() {
        Console.WriteLine("    본문: 시작");
        for (int i = 1; i <= 3; i++) {
            Console.WriteLine($"    본문: yield {i} 직전");
            yield return i;
            Console.WriteLine($"    본문: yield {i} 뒤로 돌아옴");
        }
        Console.WriteLine("    본문: 끝");
    }
    static void Main() {
        Console.WriteLine("[1] var seq = Numbers();");
        var seq = Numbers();
        Console.WriteLine("[2] var e = seq.GetEnumerator();");
        var e = seq.GetEnumerator();
        for (int k = 1; k <= 4; k++) {
            Console.WriteLine($"[{k + 2}] e.MoveNext() 부름");
            bool r = e.MoveNext();
            Console.WriteLine($"    → {r}{(r ? $" · Current = {e.Current}" : "")}");
        }
    }
}
===== csc -out:ex.dll cs32b-lazy.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] var seq = Numbers();
[2] var e = seq.GetEnumerator();
[3] e.MoveNext() 부름
    본문: 시작
    본문: yield 1 직전
    → True · Current = 1
[4] e.MoveNext() 부름
    본문: yield 1 뒤로 돌아옴
    본문: yield 2 직전
    → True · Current = 2
[5] e.MoveNext() 부름
    본문: yield 2 뒤로 돌아옴
    본문: yield 3 직전
    → True · Current = 3
[6] e.MoveNext() 부름
    본문: yield 3 뒤로 돌아옴
    본문: 끝
    → False
```

**왜 그런가**

- ★★★ **부르기(`[1]`)와 열거자 받기(`[2]`)는 본문을 안 돌린다** — `본문: 시작` 은 **첫 `MoveNext`** 에서야 찍힌다.
- ★★★ **`[4]`\~`[6]` 은 `yield N 뒤로 돌아옴` 으로 시작한다** — 멈춘 `yield return` 바로 뒤에서 이어진다. `[6]` 은 본문을 끝까지 돌린 뒤 `False`.

### 2. ★★★ **`[1]` 은 열거 때 · `[2]` 는 호출 때**

**출력**

```text
===== 소스: cs32b-arg.cs =====
using System;
using System.Collections.Generic;
class Program {
    static IEnumerable<int> Doubled(IEnumerable<int> src) {
        if (src is null) throw new ArgumentNullException(nameof(src));
        foreach (var x in src) yield return x * 2;
    }
    static IEnumerable<int> DoubledSplit(IEnumerable<int> src) {
        if (src is null) throw new ArgumentNullException(nameof(src));
        return Core();
        IEnumerable<int> Core() { foreach (var x in src) yield return x * 2; }
    }
    static void Try(string label, Func<IEnumerable<int>> call) {
        IEnumerable<int> seq;
        try { seq = call(); Console.WriteLine($"{label} 호출 : 돌아옴"); }
        catch (Exception e) { Console.WriteLine($"{label} 호출 : {e.GetType().Name}"); return; }
        try { foreach (var _ in seq) { } Console.WriteLine($"{label} 열거 : 끝까지 돎"); }
        catch (Exception e) { Console.WriteLine($"{label} 열거 : {e.GetType().Name}"); }
    }
    static void Main() {
        Try("[1] Doubled(null)     ", () => Doubled(null!));
        Try("[2] DoubledSplit(null)", () => DoubledSplit(null!));
    }
}
===== csc -nullable:enable -out:ex.dll cs32b-arg.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Doubled(null)      호출 : 돌아옴
[1] Doubled(null)      열거 : ArgumentNullException
[2] DoubledSplit(null) 호출 : ArgumentNullException
```

**왜 그런가**

- ★★★ `Doubled` 는 `yield` 가 있어 **메서드 전체가 반복자** — 검사 줄도 첫 `MoveNext` 에서 돈다. `DoubledSplit` 은 바깥이 **보통 메서드**라 검사가 바로 돌고, `yield` 는 지역 함수 `Core` 에만 있다.

### 3. ★★★ **`<Numbers>d__0` · 인터페이스 다섯 · 필드 여섯** — 상태 **`-2 → 0 → 1 → 1 → -1`**, `Dispose` 뒤 **`-2`** · 첫 `GetEnumerator` 는 **자기 자신**

**출력**

```text
===== 소스: cs32b-sm.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
public static class Gen {
    public static IEnumerable<int> Numbers(int limit) {
        for (int i = 1; i <= limit; i++) yield return i * 10;
    }
    public static IEnumerable<string> Three() {
        yield return "a";
        yield return "b";
        yield return "c";
    }
}
class Program {
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    static void Main() {
        var t = typeof(Gen).GetNestedTypes(BindingFlags.NonPublic).Single(n => n.Name.Contains("Numbers"));
        Console.WriteLine($"=== 컴파일러가 만든 타입 {t.Name} (class={t.IsClass} sealed={t.IsSealed})");
        Console.WriteLine($"    구현한 인터페이스 : {string.Join(", ", t.GetInterfaces().Select(i => i.Name).OrderBy(n => n, StringComparer.Ordinal))}");
        foreach (var f in t.GetFields(All).OrderBy(f => f.Name, StringComparer.Ordinal))
            Console.WriteLine($"    필드   {f.FieldType.Name} {f.Name}");
        var state = t.GetField("<>1__state", All)!;
        var seq = Gen.Numbers(2);
        Console.WriteLine($"[1] Numbers(2) 직후                <>1__state = {state.GetValue(seq)}");
        var e = seq.GetEnumerator();
        Console.WriteLine($"[2] 첫 GetEnumerator 뒤            <>1__state = {state.GetValue(e)} · ReferenceEquals(seq, e) = {ReferenceEquals(seq, e)}");
        var e2 = seq.GetEnumerator();
        Console.WriteLine($"[3] 두 번째 GetEnumerator          ReferenceEquals(seq, e2) = {ReferenceEquals(seq, e2)} · e2 의 <>1__state = {state.GetValue(e2)}");
        for (int k = 1; k <= 3; k++) {
            bool r = e.MoveNext();
            Console.WriteLine($"[{k + 3}] MoveNext → {r,-5}              <>1__state = {state.GetValue(e)} · <>2__current = {t.GetField("<>2__current", All)!.GetValue(e)}");
        }
        e.Dispose();
        Console.WriteLine($"[7] Dispose 뒤                       <>1__state = {state.GetValue(e)}");
        var e3 = seq.GetEnumerator();
        Console.WriteLine($"[8] 그 뒤 GetEnumerator            ReferenceEquals(seq, e3) = {ReferenceEquals(seq, e3)}");
        Il.Dump(typeof(Gen), "Numbers");
        Il.Dump(t, "MoveNext");
        Il.Dump(typeof(Gen).GetNestedTypes(BindingFlags.NonPublic).Single(n => n.Name.Contains("Three")), "MoveNext");
    }
}
===== csc -optimize -r:il.dll -out:exo.dll cs32b-sm.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
=== 컴파일러가 만든 타입 <Numbers>d__0 (class=True sealed=True)
    구현한 인터페이스 : IDisposable, IEnumerable, IEnumerable`1, IEnumerator, IEnumerator`1
    필드   Int32 <>1__state
    필드   Int32 <>2__current
    필드   Int32 <>3__limit
    필드   Int32 <>l__initialThreadId
    필드   Int32 <i>5__2
    필드   Int32 limit
[1] Numbers(2) 직후                <>1__state = -2
[2] 첫 GetEnumerator 뒤            <>1__state = 0 · ReferenceEquals(seq, e) = True
[3] 두 번째 GetEnumerator          ReferenceEquals(seq, e2) = False · e2 의 <>1__state = 0
[4] MoveNext → True               <>1__state = 1 · <>2__current = 10
[5] MoveNext → True               <>1__state = 1 · <>2__current = 20
[6] MoveNext → False              <>1__state = -1 · <>2__current = 20
[7] Dispose 뒤                       <>1__state = -2
[8] 그 뒤 GetEnumerator            ReferenceEquals(seq, e3) = True
--- Gen.Numbers ---
  IL_0000: ldc.i4.s -2
  IL_0002: newobj Gen+<Numbers>d__0::.ctor
  IL_0007: dup
  IL_0008: ldarg.0
  IL_0009: stfld Gen+<Numbers>d__0::<>3__limit
  IL_000e: ret
--- <Numbers>d__0.MoveNext ---
  .locals [0] System.Int32
  .locals [1] System.Int32
  IL_0000: ldarg.0
  IL_0001: ldfld Gen+<Numbers>d__0::<>1__state
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: brfalse.s IL_0010
  IL_000a: ldloc.0
  IL_000b: ldc.i4.1
  IL_000c: beq.s IL_0038
  IL_000e: ldc.i4.0
  IL_000f: ret
  IL_0010: ldarg.0
  IL_0011: ldc.i4.m1
  IL_0012: stfld Gen+<Numbers>d__0::<>1__state
  IL_0017: ldarg.0
  IL_0018: ldc.i4.1
  IL_0019: stfld Gen+<Numbers>d__0::<i>5__2
  IL_001e: br.s IL_004f
  IL_0020: ldarg.0
  IL_0021: ldarg.0
  IL_0022: ldfld Gen+<Numbers>d__0::<i>5__2
  IL_0027: ldc.i4.s 10
  IL_0029: mul
  IL_002a: stfld Gen+<Numbers>d__0::<>2__current
  IL_002f: ldarg.0
  IL_0030: ldc.i4.1
  IL_0031: stfld Gen+<Numbers>d__0::<>1__state
  IL_0036: ldc.i4.1
  IL_0037: ret
  IL_0038: ldarg.0
  IL_0039: ldc.i4.m1
  IL_003a: stfld Gen+<Numbers>d__0::<>1__state
  IL_003f: ldarg.0
  IL_0040: ldfld Gen+<Numbers>d__0::<i>5__2
  IL_0045: stloc.1
  IL_0046: ldarg.0
  IL_0047: ldloc.1
  IL_0048: ldc.i4.1
  IL_0049: add
  IL_004a: stfld Gen+<Numbers>d__0::<i>5__2
  IL_004f: ldarg.0
  IL_0050: ldfld Gen+<Numbers>d__0::<i>5__2
  IL_0055: ldarg.0
  IL_0056: ldfld Gen+<Numbers>d__0::limit
  IL_005b: ble.s IL_0020
  IL_005d: ldc.i4.0
  IL_005e: ret
--- <Three>d__1.MoveNext ---
  .locals [0] System.Int32
  IL_0000: ldarg.0
  IL_0001: ldfld Gen+<Three>d__1::<>1__state
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: switch (IL_001f, IL_003a, IL_0055, IL_0070)
  IL_001d: ldc.i4.0
  IL_001e: ret
  IL_001f: ldarg.0
  IL_0020: ldc.i4.m1
  IL_0021: stfld Gen+<Three>d__1::<>1__state
  IL_0026: ldarg.0
  IL_0027: ldstr "a"
  IL_002c: stfld Gen+<Three>d__1::<>2__current
  IL_0031: ldarg.0
  IL_0032: ldc.i4.1
  IL_0033: stfld Gen+<Three>d__1::<>1__state
  IL_0038: ldc.i4.1
  IL_0039: ret
  IL_003a: ldarg.0
  IL_003b: ldc.i4.m1
  IL_003c: stfld Gen+<Three>d__1::<>1__state
  IL_0041: ldarg.0
  IL_0042: ldstr "b"
  IL_0047: stfld Gen+<Three>d__1::<>2__current
  IL_004c: ldarg.0
  IL_004d: ldc.i4.2
  IL_004e: stfld Gen+<Three>d__1::<>1__state
  IL_0053: ldc.i4.1
  IL_0054: ret
  IL_0055: ldarg.0
  IL_0056: ldc.i4.m1
  IL_0057: stfld Gen+<Three>d__1::<>1__state
  IL_005c: ldarg.0
  IL_005d: ldstr "c"
  IL_0062: stfld Gen+<Three>d__1::<>2__current
  IL_0067: ldarg.0
  IL_0068: ldc.i4.3
  IL_0069: stfld Gen+<Three>d__1::<>1__state
  IL_006e: ldc.i4.1
  IL_006f: ret
  IL_0070: ldarg.0
  IL_0071: ldc.i4.m1
  IL_0072: stfld Gen+<Three>d__1::<>1__state
  IL_0077: ldc.i4.0
  IL_0078: ret
```

**왜 그런가**

- ★★★ **`Numbers` 의 IL 은 `ldc.i4.s -2` · `newobj` · `stfld <>3__limit` · `ret`** — 본문(`for`)이 없다. 본문은 `<Numbers>d__0.MoveNext` 로 옮겨졌고, 지역 변수 `i` 는 필드 **`<i>5__2`** 다.
- ★★★ **`[2]` `True` · `[3]` `False`** — 만든 스레드에서 처음 `GetEnumerator` 하면 **자기 자신**, 이미 쓰는 중이면 **새 객체**(상태 `0`).
- ★★ **`[7]` `-2` · `[8]` `True`** — 이 판 Roslyn 은 `Dispose` 뒤 상태를 `-2` 로 되돌려 **재사용**한다.
- ★★ **`Three` 의 `switch` 갈래 넷**(`IL_001f` · `IL_003a` · `IL_0055` · `IL_0070`) — `yield` 셋 + 끝. `Numbers` 는 상태가 둘이라 `brfalse.s`/`beq.s` 다.

### 4. ★★★ **finally 가 돈 소비자 7 / 10** — 안 도는 것은 **`Dispose` 안 부른 손 열거 · `MoveNext` 전 `Dispose` · 부르기만**

**출력**

```text
===== 소스: cs32b-fin.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static readonly List<string> log = new();
    static IEnumerable<int> Guarded() {
        try {
            log.Add("try");
            yield return 1;
            yield return 2;
            yield return 3;
        } finally {
            log.Add("finally");
        }
    }
    static int ran, total;
    static void Probe(string label, Action consume) {
        log.Clear(); total++;
        try { consume(); } catch (InvalidOperationException) { log.Add("(바깥 catch)"); }
        if (log.Contains("finally")) ran++;
        Console.WriteLine($"{label,-40} {string.Join(" / ", log)}");
    }
    static void Main() {
        Probe("[1] foreach 끝까지", () => { foreach (var x in Guarded()) { } });
        Probe("[2] foreach · x==1 에서 break", () => { foreach (var x in Guarded()) if (x == 1) break; });
        Probe("[3] foreach · x==1 에서 몸통이 던짐", () => { foreach (var x in Guarded()) throw new InvalidOperationException(); });
        Probe("[4] MoveNext 한 번 · Dispose 안 부름", () => { var e = Guarded().GetEnumerator(); e.MoveNext(); });
        Probe("[5] MoveNext 한 번 · Dispose 부름", () => { var e = Guarded().GetEnumerator(); e.MoveNext(); e.Dispose(); });
        Probe("[6] MoveNext 전에 Dispose", () => { var e = Guarded().GetEnumerator(); e.Dispose(); });
        Probe("[7] 부르기만 함", () => { _ = Guarded(); });
        Probe("[8] First()", () => { _ = Guarded().First(); });
        Probe("[9] Take(1).ToList()", () => { _ = Guarded().Take(1).ToList(); });
        Probe("[10] Any()", () => { _ = Guarded().Any(); });
        Console.WriteLine($"finally 가 돈 소비자 {ran} / {total}");
    }
}
===== csc -out:ex.dll cs32b-fin.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] foreach 끝까지                          try / finally
[2] foreach · x==1 에서 break              try / finally
[3] foreach · x==1 에서 몸통이 던짐             try / finally / (바깥 catch)
[4] MoveNext 한 번 · Dispose 안 부름          try
[5] MoveNext 한 번 · Dispose 부름            try / finally
[6] MoveNext 전에 Dispose                  
[7] 부르기만 함                               
[8] First()                              try / finally
[9] Take(1).ToList()                     try / finally
[10] Any()                               try / finally
finally 가 돈 소비자 7 / 10
```

**왜 그런가**

- ★★★ **`foreach`(끝까지 · `break` · 예외)와 LINQ(`First` · `Take(1).ToList` · `Any`)는 전부 `Dispose` 를 부른다** — 반복자의 `Dispose` 가 멈춘 자리의 `finally` 를 돌린다.
- ★★★ **`[4]`** — `MoveNext` 로 `try` 에 들어갔는데 `Dispose` 를 안 불렀다 — `finally` 가 **안 돈다.** `[6]`·`[7]` 은 `try` 에 들어간 적이 없다.

### 5. ★★ **`[1]` map 10 · filter 10(가로) · `[2]` 만든 직후 0 줄 · map 4 · filter 4(세로)**

**출력**

```text
===== 소스: cs32b-linq.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static readonly List<string> log = new();
    static int Map(int x) { log.Add($"map({x})"); return x * 10; }
    static bool Keep(int x) { log.Add($"filter({x})"); return x % 20 == 0; }
    static int N(string p) => log.Count(m => m.StartsWith(p));
    static void Main() {
        var src = Enumerable.Range(1, 10).ToList();
        Console.WriteLine("[1] 단계마다 ToList: Select → ToList → Where → ToList → Take(2) → ToList");
        var a = src.Select(Map).ToList().Where(Keep).ToList().Take(2).ToList();
        Console.WriteLine($"    결과 [{string.Join(", ", a)}] · map 호출 {N("map(")} · filter 호출 {N("filter(")}");
        Console.WriteLine($"    순서 {string.Join(" ", log)}");
        log.Clear();
        Console.WriteLine("[2] 사슬: src.Select(Map).Where(Keep).Take(2)");
        var pipe = src.Select(Map).Where(Keep).Take(2);
        Console.WriteLine($"    사슬을 만든 직후 로그 {log.Count} 줄");
        var h = pipe.ToList();
        Console.WriteLine($"    ToList() 뒤 결과 [{string.Join(", ", h)}] · map 호출 {N("map(")} · filter 호출 {N("filter(")}");
        Console.WriteLine($"    순서 {string.Join(" ", log)}");
    }
}
===== csc -out:ex.dll cs32b-linq.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 단계마다 ToList: Select → ToList → Where → ToList → Take(2) → ToList
    결과 [20, 40] · map 호출 10 · filter 호출 10
    순서 map(1) map(2) map(3) map(4) map(5) map(6) map(7) map(8) map(9) map(10) filter(10) filter(20) filter(30) filter(40) filter(50) filter(60) filter(70) filter(80) filter(90) filter(100)
[2] 사슬: src.Select(Map).Where(Keep).Take(2)
    사슬을 만든 직후 로그 0 줄
    ToList() 뒤 결과 [20, 40] · map 호출 4 · filter 호출 4
    순서 map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)
```

**왜 그런가**

- ★★★ `ToList()` 가 `Take` 의 `MoveNext` 를 부르고, `Take` 가 `Where` 를, `Where` 가 `Select` 를 당긴다 — **원소 하나가 사슬 전체를** 지나간다. `Take(2)` 가 둘을 채우면 더 안 당긴다.

### 6. ★★ **`[1]` 2 번 · `[2]` 1 번**

**출력**

```text
===== 소스: cs32b-twice.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static int runs;
    static IEnumerable<int> Load() {
        runs++;
        Console.WriteLine($"  Load 본문 실행 #{runs}");
        yield return 1; yield return 2; yield return 3;
    }
    static void Main() {
        Console.WriteLine("[1] var q = Load(); q.Count(); q.Sum();");
        var q = Load();
        var c = q.Count(); var s = q.Sum();
        Console.WriteLine($"  Count={c} Sum={s} · 본문 실행 {runs} 번");
        runs = 0;
        Console.WriteLine("[2] var m = Load().ToList(); m.Count; m.Sum();");
        var m = Load().ToList();
        var c2 = m.Count; var s2 = m.Sum();
        Console.WriteLine($"  Count={c2} Sum={s2} · 본문 실행 {runs} 번");
    }
}
===== csc -out:ex.dll cs32b-twice.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] var q = Load(); q.Count(); q.Sum();
  Load 본문 실행 #1
  Load 본문 실행 #2
  Count=3 Sum=6 · 본문 실행 2 번
[2] var m = Load().ToList(); m.Count; m.Sum();
  Load 본문 실행 #1
  Count=3 Sum=6 · 본문 실행 1 번
```

**왜 그런가**

- ★★★ `q` 는 **결과가 아니라 만드는 방법** — `Count()` 와 `Sum()` 이 **각자 열거**해 본문이 두 번 돈다. `ToList()` 는 한 번 돌려 **결과를 담는다.**

### 7. ★★★ **호출 = `newobj` + 인자 복사, 본문 = `MoveNext`** — 명세는 「언제」, Roslyn 은 「어떻게」

- ★★★ 1번 — 호출 뒤 `본문:` 0 줄. 3번 — `Numbers` 의 IL 에 **`for` 가 없고 객체를 만들 뿐**이다. 둘을 합치면 「호출 시점에는 본문이 없다」.
- ★★★ **명세** — 「부르면 열거자를 돌려주고, `MoveNext` 가 다음 `yield` 까지 돌린다 · 멈췄다 이어진다」. **Roslyn** — 클래스 `<Numbers>d__0` · 필드 `<>1__state` 등 · 상태 값 `-2/0/1/-1` · `switch`. **이름과 값을 외우지 말고 「책갈피 필드 + 갈래 고르기」라는 모양을 외워라.**

### 8. ★★★ **`foreach` 의 `finally` 가 `Dispose` 를 부르고, 반복자의 `Dispose` 가 멈춘 자리의 `finally` 를 돌린다** — `Dispose` 를 안 부르면 **`finally` 가 안 돈다** · JS 와 **같다**

- ★★★ 4번 `[2]` — `break` → 31번 (4)의 `finally` → `Dispose` → 반복자의 `finally`. `[4]` — 손으로 `MoveNext` 만 부르고 버리면 **그 사슬의 첫 고리가 없다.**
- ★★ **JS 20번 (3)** — `return()` 을 **시작 전**에 부르면 `body (no log)` · **멈춘 뒤**면 `finally` · **끝난 뒤**면 `no log`. C# 4번 `[6]` · `[5]` · `[1]` 과 **같은 표**다. 갈리는 칸은 **`finally` 안의 `yield`** — JS 는 되고 C# 은 `CS1625`(9번).

### 9. ★★ **`CS1625` · `CS1626` · `CS1621` · `CS1623` · `CS1624` · `CS1622`**(+ `catch` 안 `CS1631`) · C# 1 **`CS8022`** · Java **`not a statement`**

**출력**

```text
===== 소스: cs32b-ban.cs =====
using System;
using System.Collections.Generic;
class P {
    static IEnumerable<int> InFinally() { try { yield return 1; } finally { yield return 2; } }
    static IEnumerable<int> InTryCatch() { try { yield return 1; } catch { } }
    static IEnumerable<int> InCatch() { try { } catch { yield return 1; } }
    static IEnumerable<int> RefParam(ref int x) { yield return x; }
    static void M() { Func<IEnumerable<int>> f = () => { yield return 1; }; }
    static List<int> NotIter() { yield return 1; }
    static IEnumerable<int> Both() { yield return 1; return null; }
    static void Main() { }
}
===== csc -out:ex.dll cs32b-ban.cs 2>&1 | sort (cc exit=1) =====
cs32b-ban.cs(10,54): error CS1622: Cannot return a value from an iterator. Use the yield return statement to return a value, or yield break to end the iteration.
cs32b-ban.cs(4,77): error CS1625: Cannot yield in the body of a finally clause
cs32b-ban.cs(5,50): error CS1626: Cannot yield a value in the body of a try block with a catch clause
cs32b-ban.cs(6,57): error CS1631: Cannot yield a value in the body of a catch clause
cs32b-ban.cs(7,46): error CS1623: Iterators cannot have ref, in or out parameters
cs32b-ban.cs(8,53): error CS1643: Not all code paths return a value in lambda expression of type 'Func<IEnumerable<int>>'
cs32b-ban.cs(8,58): error CS1621: The yield statement cannot be used inside an anonymous method or lambda expression
cs32b-ban.cs(9,22): error CS1624: The body of 'P.NotIter()' cannot be an iterator block because 'List<int>' is not an iterator interface type
===== 소스: cs32b-v1.cs =====
using System.Collections;
class P { static IEnumerable N() { yield return 1; } static void Main() { } }
===== csc -langversion:1 -out:ex.dll cs32b-v1.cs (cc exit=1) =====
cs32b-v1.cs(2,36): error CS8022: Feature 'iterators' is not available in C# 1. Please use language version 2 or greater.
===== csc -langversion:2 -out:ex.dll cs32b-v1.cs (cc exit=0) =====
===== 소스: G32.java =====
import java.util.List;
class G32 {
    static Iterable<Integer> numbers() {
        yield return 1;
    }
}
===== javac -d j32out j32/G32.java (cc exit=1) =====
j32/G32.java:4: error: not a statement
        yield return 1;
        ^
j32/G32.java:4: error: ';' expected
        yield return 1;
             ^
2 errors
```

**왜 그런가**

- ★★ `finally` **만** 딸린 `try` 는 된다(4번 `Guarded`). **`catch` 가 끼면 안 된다.** Java 에는 반복자 `yield` 가 **없다** — `yield` 는 `switch` 식의 낱말이다.

### 10. ★★ **셋 다 같다(1000번 32000)** — 부르기만 해도 객체 하나 · 첫 `GetEnumerator` 는 자기 자신 · `Dispose` 뒤 재사용

**출력**

```text
===== 소스: cs32b-alloc.cs =====
using System;
using System.Collections.Generic;
class Program {
    static IEnumerable<int> Numbers() { yield return 1; yield return 2; }
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        System.Threading.Thread.Sleep(300);
        for (int i = 0; i < 300; i++) a();
        System.Threading.Thread.Sleep(300);
        for (int i = 0; i < 300; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        long sink = 0;
        Console.WriteLine($"[1] Numbers() 부르기만                   1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Numbers().GetHashCode() & 1; })} 바이트");
        Console.WriteLine($"[2] Numbers() 부르고 foreach 한 번        1000번 : {M(() => { for (int i = 0; i < 1000; i++) foreach (var x in Numbers()) sink += x; })} 바이트");
        Console.WriteLine($"[3] Numbers() 부르고 같은 것을 foreach 두 번 1000번 : {M(() => { for (int i = 0; i < 1000; i++) { var q = Numbers(); foreach (var x in q) sink += x; foreach (var x in q) sink += x; } })} 바이트");
        GC.KeepAlive(sink);
    }
}
===== csc -out:ex.dll cs32b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Numbers() 부르기만                   1000번 : 32000 바이트
[2] Numbers() 부르고 foreach 한 번        1000번 : 32000 바이트
[3] Numbers() 부르고 같은 것을 foreach 두 번 1000번 : 32000 바이트
===== csc -out:ex.dll cs32b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Numbers() 부르기만                   1000번 : 32000 바이트
[2] Numbers() 부르고 foreach 한 번        1000번 : 32000 바이트
[3] Numbers() 부르고 같은 것을 foreach 두 번 1000번 : 32000 바이트
===== csc -optimize -out:exo.dll cs32b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] Numbers() 부르기만                   1000번 : 32000 바이트
[2] Numbers() 부르고 foreach 한 번        1000번 : 32000 바이트
[3] Numbers() 부르고 같은 것을 foreach 두 번 1000번 : 32000 바이트
===== csc -optimize -out:exo.dll cs32b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] Numbers() 부르기만                   1000번 : 32000 바이트
[2] Numbers() 부르고 foreach 한 번        1000번 : 32000 바이트
[3] Numbers() 부르고 같은 것을 foreach 두 번 1000번 : 32000 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 3
```

**왜 그런가**

- ★★★ **`[1]`** — 본문은 0 줄이어도 **상태 기계 객체**는 생긴다. **`[2]`** — 3번 `[2]` 처럼 **자기 자신**을 열거자로 쓴다. **`[3]`** — 3번 `[7]`·`[8]` 처럼 **다 쓴 객체를 재사용**했다 — 이 판 Roslyn 의 구현이다. 네 판 **0 / 3**.

### 11. ★★ **Python·JS 도 같다(부르면 본문 0 줄)** · Go `iter.Seq` 는 **push**, C# 은 **pull** · 5번의 표는 **세 갈래와 같다**

- ★★ [Python 17번](../../../python/syntax/17-generators-yield/) §1 · [JS 20번](../../../js/syntax/20-generators/) (1)(★ JS 는 **매개변수 목록은 돈다** — C# 도 인자는 호출 때 `<>3__limit` 에 적힌다) · [Go 39번](../../../go/syntax/39-iter-and-custom-iterators/) — 반복자가 몸통 콜백을 부른다.
- ★ [JS 21번](../../../js/syntax/21-iterator-helpers/) · [Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/) · [Python 44번](../../../python/syntax/44-itertools/) 모두 **`10 · 10` 대 `4 · 4`**.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs32b-lazy.cs` | csc 1회 · 실행 1회 | ★★★ 부르기·`GetEnumerator` 뒤 **0 줄** · `MoveNext` 마다 한 토막 |
| `cs32b-arg.cs` | csc 1회 · 실행 1회 | ★★★ `[1]` 열거 때 · `[2]` 호출 때 `ArgumentNullException` |
| `cs32b-sm.cs` | csc 1회(`-optimize`) · 실행 1회 | ★★★ `<Numbers>d__0` 필드 여섯 · 상태 `-2 0 1 1 -1` · `Dispose` 뒤 `-2` · `switch` 넷 |
| `cs32b-fin.cs` | csc 1회 · 실행 1회 | ★★★ **finally 가 돈 소비자 7 / 10** |
| `cs32b-ban.cs` · `cs32b-v1.cs` · `G32.java` | csc 3회(latest · 1 · 2) · javac 1회 | 금지 여덟 코드 · `CS8022` · `not a statement` |
| `cs32b-linq.cs` | csc 1회 · 실행 1회 | ★★★ `10 · 10` 대 **`4 · 4`** · 만든 직후 0 줄 |
| `cs32b-twice.cs` | csc 1회 · 실행 1회 | 2 번 대 1 번 |
| `cs32b-alloc.cs` | **2×2 판 격자**(길게 데움) | 세 줄 32000 · **갈린 줄 0 / 3** |
| `cs32b-form.cs` | csc 1회 · 실행 1회 | `0,2,4,6,8 · 3,1 · 0,1,1,2,3,5,8,13` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **상태 기계의 클래스·필드 이름 · 상태 값 · `switch` 대 비교 분기 · 첫 `GetEnumerator` 의 자기 반환 · `Dispose` 뒤 재사용** — Roslyn · ★ 할당 바이트 값.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **부르면 본문이 안 돈다 · `MoveNext` 가 다음 `yield` 까지 · `Dispose` 가 멈춘 자리의 `finally` · `yield` 금지 자리.**

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ `IAsyncEnumerable<T>` · `Reset()` · 여러 스레드의 `GetEnumerator` · 옛 Roslyn 의 `Dispose` 뒤 상태.
- **못 잰 것** — ★★★ **시간**.
- **잴 것이 없는 것** — 없다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **3번 `[7]`·`[8]` · 10번 `[3]`** — Roslyn 이 `Dispose` 뒤 재사용을 그만두면 `[8]` 이 `False`, 10번 `[3]` 이 커진다.
- ★★ **3번** — 상태 값·필드 이름이 바뀌면 덤프가 갈린다(명세는 안 바뀐다).
