# csharp/syntax/29 — 이벤트와 `event` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·GC 결과는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **진단 코드 · 스크립트가 센 「막힌 칸 N / M」 · 옵코드 · 리플렉션의 이름 · 「회수됐나」 참/거짓** 이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **막힌 칸 12 / 30** — 바깥·파생은 `+=`·`-=` 만 · 접근자형은 안에서도 `CS0079`

**출력**

```text
===== 소스: cs29b-grid.cs =====
using System;
class Pub {
    public Action? F;
    public event Action? E;
    Action? store;
    public event Action? C { add { store += value; } remove { store -= value; } }
    void Inside() {
        E += H;                            // cell += event·inside
        E -= H;                            // cell -= event·inside
        E = H;                             // cell = event·inside
        E();                               // cell () event·inside
        E = null;                          // cell =null event·inside
        _ = E!.GetInvocationList();        // cell list event·inside
        C += H;                            // cell += custom·inside
        C -= H;                            // cell -= custom·inside
        C = H;                             // cell = custom·inside
        C();                               // cell () custom·inside
        C = null;                          // cell =null custom·inside
        _ = C!.GetInvocationList();        // cell list custom·inside
    }
    static void H() { }
}
class Sub : Pub {
    void Derived() {
        E += H;                            // cell += event·derived
        E -= H;                            // cell -= event·derived
        E = H;                             // cell = event·derived
        E();                               // cell () event·derived
        E = null;                          // cell =null event·derived
        _ = E!.GetInvocationList();        // cell list event·derived
    }
    static void H() { }
}
class Other {
    static void H() { }
    static void Outside(Pub p) {
        p.F += H;                          // cell += field·outside
        p.F -= H;                          // cell -= field·outside
        p.F = H;                           // cell = field·outside
        p.F();                             // cell () field·outside
        p.F = null;                        // cell =null field·outside
        _ = p.F!.GetInvocationList();      // cell list field·outside
        p.E += H;                          // cell += event·outside
        p.E -= H;                          // cell -= event·outside
        p.E = H;                           // cell = event·outside
        p.E();                             // cell () event·outside
        p.E = null;                        // cell =null event·outside
        _ = p.E!.GetInvocationList();      // cell list event·outside
    }
}
===== csc -nullable:enable -target:library -out:g29.dll cs29b-grid.cs 2>&1 | sort (cc exit=1) =====
cs29b-grid.cs(16,9): error CS0079: The event 'Pub.C' can only appear on the left hand side of += or -=
cs29b-grid.cs(17,9): error CS0079: The event 'Pub.C' can only appear on the left hand side of += or -=
cs29b-grid.cs(18,9): error CS0079: The event 'Pub.C' can only appear on the left hand side of += or -=
cs29b-grid.cs(19,13): error CS0079: The event 'Pub.C' can only appear on the left hand side of += or -=
cs29b-grid.cs(27,9): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(28,9): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(29,9): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(30,13): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(45,11): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(46,11): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(47,11): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(48,15): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
===== python3 cellgrid.py cs29b-grid.cs <위 진단> — 칸마다 진단 코드 =====
식 \ 자리           event·inside     custom·inside    event·derived    field·outside    event·outside
+=               ok               ok               ok               ok               ok
-=               ok               ok               ok               ok               ok
=                ok               CS0079           CS0070           ok               CS0070
()               ok               CS0079           CS0070           ok               CS0070
=null            ok               CS0079           CS0070           ok               CS0070
list             ok               CS0079           CS0070           ok               CS0070
막힌 칸 12 / 30
```

**왜 그런가**

- ★★★ **바깥(`event·outside`) — `+=`·`-=` 만 `ok`, 나머지 넷 `CS0070`** — 필드형 이벤트는 선언한 타입 밖에서 **`+=`·`-=` 의 왼쪽에만** 올 수 있다.
- ★★★ **파생(`event·derived`)은 바깥과 같다** — 「선언한 타입」은 `Pub` 뿐이다.
- ★★ **안(`event·inside`)은 전부 `ok` · 필드(`field·outside`)도 전부 `ok`** — 이벤트는 안에서는 **필드**다.
- ★★ **접근자형 `C` 는 안에서도 넷이 `CS0079`** — 6번.

### 2. ★★★ **숨은 필드 `private Action E` + `add_E`/`remove_E`** — 바깥의 `+=` 는 **`callvirt add_E`**

**출력**

```text
===== 소스: cs29b-il.cs =====
using System;
using System.Linq;
using System.Reflection;
public class Pub {
    public Action? F;
    public event Action? E;
    public int P { get; set; }
}
public static class Use {
    static void H() { }
    public static void AddToField(Pub p) => p.F += H;
    public static void AddToEvent(Pub p) => p.E += H;
}
class Program {
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    static void Main() {
        foreach (var f in typeof(Pub).GetFields(All).OrderBy(f => f.Name, StringComparer.Ordinal))
            Console.WriteLine($"필드   {(f.IsPublic ? "public " : "private")} {f.FieldType.Name} {f.Name}");
        foreach (var m in typeof(Pub).GetMethods(All).OrderBy(m => m.Name, StringComparer.Ordinal))
            Console.WriteLine($"메서드 {(m.IsPublic ? "public " : "private")} {m.Name} (specialname={m.IsSpecialName})");
        foreach (var e in typeof(Pub).GetEvents(All))
            Console.WriteLine($"이벤트 {e.Name} : {e.EventHandlerType!.Name} · add={e.AddMethod!.Name} · remove={e.RemoveMethod!.Name} · raise={(e.RaiseMethod?.Name ?? "(없음)")}");
        foreach (var p in typeof(Pub).GetProperties(All))
            Console.WriteLine($"속성   {p.Name} : get={p.GetMethod!.Name} · set={p.SetMethod!.Name}");
        Il.Dump(typeof(Pub), "add_E");
        Il.Dump(typeof(Use), "AddToField");
        Il.Dump(typeof(Use), "AddToEvent");
    }
}
===== csc -nullable:enable -optimize -r:il.dll -out:exo.dll cs29b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
cs29b-il.cs(6,26): warning CS0067: The event 'Pub.E' is never used
필드   private Int32 <P>k__BackingField
필드   private Action E
필드   public  Action F
메서드 public  add_E (specialname=True)
메서드 public  get_P (specialname=True)
메서드 public  remove_E (specialname=True)
메서드 public  set_P (specialname=True)
이벤트 E : Action · add=add_E · remove=remove_E · raise=(없음)
속성   P : get=get_P · set=set_P
--- Pub.add_E ---
  .locals [0] System.Action
  .locals [1] System.Action
  .locals [2] System.Action
  IL_0000: ldarg.0
  IL_0001: ldfld Pub::E
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: stloc.1
  IL_0009: ldloc.1
  IL_000a: ldarg.1
  IL_000b: call System.Delegate::Combine
  IL_0010: castclass System.Action
  IL_0015: stloc.2
  IL_0016: ldarg.0
  IL_0017: ldflda Pub::E
  IL_001c: ldloc.2
  IL_001d: ldloc.1
  IL_001e: call System.Threading.Interlocked::CompareExchange<System.Action>
  IL_0023: stloc.0
  IL_0024: ldloc.0
  IL_0025: ldloc.1
  IL_0026: bne.un.s IL_0007
  IL_0028: ret
--- Use.AddToField ---
  IL_0000: ldarg.0
  IL_0001: dup
  IL_0002: ldfld Pub::F
  IL_0007: ldsfld Use+<>O::<0>__H
  IL_000c: dup
  IL_000d: brtrue.s IL_0022
  IL_000f: pop
  IL_0010: ldnull
  IL_0011: ldftn Use::H
  IL_0017: newobj System.Action::.ctor
  IL_001c: dup
  IL_001d: stsfld Use+<>O::<0>__H
  IL_0022: call System.Delegate::Combine
  IL_0027: castclass System.Action
  IL_002c: stfld Pub::F
  IL_0031: ret
--- Use.AddToEvent ---
  IL_0000: ldarg.0
  IL_0001: ldsfld Use+<>O::<0>__H
  IL_0006: dup
  IL_0007: brtrue.s IL_001c
  IL_0009: pop
  IL_000a: ldnull
  IL_000b: ldftn Use::H
  IL_0011: newobj System.Action::.ctor
  IL_0016: dup
  IL_0017: stsfld Use+<>O::<0>__H
  IL_001c: callvirt Pub::add_E
  IL_0021: ret
```

**왜 그런가**

- ★★★ **필드 셋 — `F`(public) · `E`(private) · `<P>k__BackingField`** — 이벤트의 숨은 필드는 **이름이 `E` 그대로**다.
- ★★★ **`add_E`·`remove_E` 는 `public` · `specialname=True`** — 속성 `P` 의 `get_P`·`set_P` 와 같은 모양이다. **`raise` 메서드는 없다.**
- ★★ **`add_E` = `Combine` + `Interlocked::CompareExchange` + `bne.un.s` 로 되돌아가는 고리** — 남이 먼저 바꿨으면 다시 읽는다.
- ★★★ **`p.F += H` 는 `ldfld F` · `Combine` · `stfld F` — 호출자가 필드를 고친다. `p.E += H` 는 `callvirt Pub::add_E` 한 줄.**

### 3. ★★ **`True` · `NullReferenceException` · 예외 없음** — `Count` 는 **`0` · `1` · `0`**

**출력**

```text
===== 소스: cs29b-raise.cs =====
using System;
class Pub {
    public event Action? Tick;
    public int Count => Tick?.GetInvocationList().Length ?? 0;
    public bool IsNull => Tick is null;
    public void RaiseDirect() => Tick!();
    public void RaiseSafe() => Tick?.Invoke();
}
class Sub {
    public int Seen;
    public void OnTick() => Seen++;
}
class Program {
    static void Main() {
        var p = new Pub();
        Console.WriteLine($"[1] 구독자 0 · Tick is null : {p.IsNull}");
        try { p.RaiseDirect(); Console.WriteLine("[2] Tick!() : 예외 없음"); }
        catch (Exception e) { Console.WriteLine($"[2] Tick!() : {e.GetType().Name}"); }
        try { p.RaiseSafe(); Console.WriteLine("[3] Tick?.Invoke() : 예외 없음"); }
        catch (Exception e) { Console.WriteLine($"[3] Tick?.Invoke() : {e.GetType().Name}"); }
        var s = new Sub();
        var p4 = new Pub(); p4.Tick += s.OnTick; p4.Tick -= s.OnTick;
        Console.WriteLine($"[4] 새 발행자에 += s.OnTick · -= s.OnTick 뒤 Count : {p4.Count}");
        var p5 = new Pub(); p5.Tick += () => s.OnTick(); p5.Tick -= () => s.OnTick();
        Console.WriteLine($"[5] 새 발행자에 += 람다 · -= 같은 모양의 람다 뒤 Count : {p5.Count}");
        Action h = () => s.OnTick();
        var p6 = new Pub(); p6.Tick += h; p6.Tick -= h;
        Console.WriteLine($"[6] 새 발행자에 += h · -= h 뒤 Count : {p6.Count}");
        p5.RaiseSafe();
        Console.WriteLine($"[7] [5] 의 발행자를 한 번 발생시킨 뒤 s.Seen : {s.Seen}");
    }
}
===== csc -nullable:enable -out:ex.dll cs29b-raise.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 구독자 0 · Tick is null : True
[2] Tick!() : NullReferenceException
[3] Tick?.Invoke() : 예외 없음
[4] 새 발행자에 += s.OnTick · -= s.OnTick 뒤 Count : 0
[5] 새 발행자에 += 람다 · -= 같은 모양의 람다 뒤 Count : 1
[6] 새 발행자에 += h · -= h 뒤 Count : 0
[7] [5] 의 발행자를 한 번 발생시킨 뒤 s.Seen : 1
```

**왜 그런가**

- ★★ **구독자가 없으면 이벤트는 `null`** — `Tick!()` 는 터지고 `?.Invoke()` 는 안 터진다.
- ★★★ **`[4]` `0`** — 메서드 그룹 `s.OnTick` 을 두 번 변환한 두 델리게이트는 **대상과 메서드가 같아** `-=` 가 찾는다.
- ★★★ **`[5]` `1`** — 두 람다는 **다른 메서드**로 컴파일된다. `-=` 가 **조용히 아무것도 안 뗀다.** **`[6]` `0`** — 같은 `h` 로 떼면 된다.

### 4. ★★★ **`True` · `False` · `False` · `True` · `True` · `True` · `True` · `True`** — 네 판 **0 / 8**

**출력**

```text
===== 소스: cs29b-leak.cs =====
using System;
using System.Runtime.CompilerServices;
class Pub {
    public event Action? Tick;
    public int Count => Tick?.GetInvocationList().Length ?? 0;
    public void Clear() => Tick = null;
}
class Sub {
    readonly byte[] big = new byte[10_000_000];
    public void OnTick() => _ = big.Length;
}
class Program {
    static readonly Pub[] longLived = { new(), new(), new(), new(), new(), new(), new() };
    static void StaticHandler() { }
    [MethodImpl(MethodImplOptions.NoInlining)]
    static WeakReference Case(int k) {
        var s = new Sub();
        var p = longLived[k];
        switch (k) {
            case 1: p.Tick += s.OnTick; p.Tick -= s.OnTick; break;
            case 2: p.Tick += s.OnTick; break;
            case 3: p.Tick += () => s.OnTick(); p.Tick -= () => s.OnTick(); break;
            case 4: { Action h = () => s.OnTick(); p.Tick += h; p.Tick -= h; break; }
            case 5: { var shortLived = new Pub(); shortLived.Tick += s.OnTick; break; }
            case 6: p.Tick += StaticHandler; break;
        }
        return new WeakReference(s);
    }
    static bool Collected(WeakReference w) { GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect(); return !w.IsAlive; }
    static void Main() {
        string[] what = { "", "메서드로 구독 · 해제함", "메서드로 구독 · 해제 안 함", "람다로 구독 · 새 람다로 해제", "람다를 변수에 두고 · 같은 변수로 해제", "짧게 사는 발행자에 구독 · 해제 안 함", "구독자와 무관한 정적 메서드로 구독" };
        var w = new WeakReference[7];
        for (int k = 1; k <= 6; k++) {
            w[k] = Case(k);
            Console.WriteLine($"[{k}] {what[k]} · 오래 사는 발행자 목록 {longLived[k].Count} · 구독자 회수됐나 : {Collected(w[k])}");
        }
        longLived[2].Clear(); longLived[3].Clear();
        Console.WriteLine($"[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : {Collected(w[2])}");
        Console.WriteLine($"[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : {Collected(w[3])}");
    }
}
===== csc -nullable:enable -out:ex.dll cs29b-leak.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 메서드로 구독 · 해제함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[2] 메서드로 구독 · 해제 안 함 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[3] 람다로 구독 · 새 람다로 해제 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[4] 람다를 변수에 두고 · 같은 변수로 해제 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[5] 짧게 사는 발행자에 구독 · 해제 안 함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[6] 구독자와 무관한 정적 메서드로 구독 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : True
[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : True
[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : True
===== csc -nullable:enable -out:ex.dll cs29b-leak.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 메서드로 구독 · 해제함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[2] 메서드로 구독 · 해제 안 함 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[3] 람다로 구독 · 새 람다로 해제 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[4] 람다를 변수에 두고 · 같은 변수로 해제 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[5] 짧게 사는 발행자에 구독 · 해제 안 함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[6] 구독자와 무관한 정적 메서드로 구독 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : True
[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : True
[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : True
===== csc -nullable:enable -optimize -out:exo.dll cs29b-leak.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] 메서드로 구독 · 해제함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[2] 메서드로 구독 · 해제 안 함 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[3] 람다로 구독 · 새 람다로 해제 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[4] 람다를 변수에 두고 · 같은 변수로 해제 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[5] 짧게 사는 발행자에 구독 · 해제 안 함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[6] 구독자와 무관한 정적 메서드로 구독 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : True
[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : True
[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : True
===== csc -nullable:enable -optimize -out:exo.dll cs29b-leak.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] 메서드로 구독 · 해제함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[2] 메서드로 구독 · 해제 안 함 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[3] 람다로 구독 · 새 람다로 해제 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[4] 람다를 변수에 두고 · 같은 변수로 해제 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[5] 짧게 사는 발행자에 구독 · 해제 안 함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[6] 구독자와 무관한 정적 메서드로 구독 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : True
[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : True
[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : True
===== 네 판 대조 — 「회수됐나」 줄마다 네 판의 참/거짓이 같은가 =====
네 판에서 갈린 줄 0 / 8 · 첫 판에서 「회수됨(True)」 줄 6 / 8
```

**왜 그런가**

- ★★★ **`[2]` 해제 안 함 · `[3]` 새 람다로 해제 → `False`** — 오래 사는 발행자의 호출 목록 → 델리게이트 → 구독자 → `big`.
- ★★★ **`[5]` `True`** — 붙드는 것은 **발행자**다. 발행자가 지역 변수라 메서드가 끝나면 **사슬의 머리가 루트가 아니다** — 해제를 안 해도 새지 않는다.
- ★★ **`[6]` `True`** — 정적 메서드 델리게이트는 구독자를 가리키지 않는다. **`[7]`·`[8]`** — 발행자가 목록을 비우면 풀린다.
- ★ **네 판에서 갈린 줄 0 / 8.**

### 5. ★★ **`add ← A` · `add ← B` · `A 실행` · `B 실행` · `remove ← A` · `B 실행`**

**출력**

```text
===== 소스: cs29b-acc.cs =====
using System;
class Pub {
    Action? store;
    public event Action Tick {
        add { Console.WriteLine($"  add    ← {value.Method.Name}"); store += value; }
        remove { Console.WriteLine($"  remove ← {value.Method.Name}"); store -= value; }
    }
    public void Raise() => store?.Invoke();
}
class Program {
    static void A() => Console.WriteLine("  A 실행");
    static void B() => Console.WriteLine("  B 실행");
    static void Main() {
        var p = new Pub();
        Console.WriteLine("[1] p.Tick += A; p.Tick += B;");
        p.Tick += A; p.Tick += B;
        Console.WriteLine("[2] p.Raise()");
        p.Raise();
        Console.WriteLine("[3] p.Tick -= A; p.Raise()");
        p.Tick -= A; p.Raise();
    }
}
===== csc -nullable:enable -out:ex.dll cs29b-acc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] p.Tick += A; p.Tick += B;
  add    ← A
  add    ← B
[2] p.Raise()
  A 실행
  B 실행
[3] p.Tick -= A; p.Raise()
  remove ← A
  B 실행
```

**왜 그런가**

- ★★ **`p.Tick += A` 는 `add` 블록을 `value = A` 로 부른다** — 2번의 `callvirt add_E` 가 사용자 코드로 바뀐 것. 저장(`store`)과 발생(`Raise`)은 **발행자가 직접** 한다.

### 6. ★★ **접근자형 이벤트에는 필드가 없다** — 안에서 `C` 라고 쓰면 읽을 것이 없다

- ★★ 필드형 `E` 는 안에서 **숨은 필드 `E`** 를 가리키므로 여섯 식이 다 된다. `C` 는 `add`/`remove` **두 메서드뿐**이라 안에서도 `C` 는 **이벤트**로만 읽히고, `+=`·`-=` 외에는 `CS0079`(「`+=`·`-=` 의 왼쪽에만」 — `CS0070` 의 「타입 안에서는 예외」 꼬리가 **없다**). 목록을 부르려면 **자기 필드(`store`)** 를 부른다.

### 7. ★★★ **마지막 구독자의 반환값만 · 한 구독자가 던지면 뒤 구독자는 안 불린다 · 같은 처리기를 두 번 붙였으면 `-=` 는 마지막 것을 뗀다**

- ★★★ [27번](../27-delegates-and-func-action/) (4) 인용 — 이벤트 발생은 **호출 목록을 차례로 부르는 것**이라 세 규칙이 그대로 온다. 그래서 이벤트 델리게이트는 보통 **`void` 반환**이고(반환값이 버려지므로), 구독자 하나의 예외가 **다른 구독자를 굶긴다** — 막으려면 발행자가 **안에서** `GetInvocationList()` 를 돌며 `try` 해야 한다(바깥은 1번 `list` 행처럼 **못 한다**).

### 8. ★★ **명세 · CLI · Roslyn · Roslyn**

- ★★★ **「바깥에서는 `+=`·`-=` 만」 = 언어 명세**(1번 — `CS0070`). **`add_`/`remove_` + `specialname` = CLI 메타데이터 관례**(속성과 같은 모양). **숨은 필드 이름이 `E` · `CompareExchange` 고리 = Roslyn 구현**(2번 — 다른 컴파일러는 다르게 적을 수 있다).

### 9. ★★★ **발행자의 목록이 구독자를** 붙든다 — 그래서 발행자가 먼저 죽으면(`[5]`) 안 샌다

- ★★★ 28번은 **델리게이트의 `Target` 이 디스플레이 객체**를 붙들었다. 여기는 **발행자 → 호출 목록 → 델리게이트 → `Target`(구독자)** 사슬이다. GC 규칙은 같다 — **루트에서 닿으면 산다.** `[5]` 는 사슬의 머리(짧게 사는 발행자)가 **루트에서 안 닿으니** 전부 풀린다. **「해제를 빠뜨리면 샌다」가 아니라 「오래 사는 쪽이 짧게 사는 쪽을 가리키면 샌다」** 다.

### 10. ★★ **구독자가 없으면 이벤트가 `null` 이라서** — 두 인자 모양은 **관례**다

- ★★ 3번 `[2]` — `Tick!()` 는 `NullReferenceException`. `?.Invoke` 는 **읽기 한 번으로** `null` 검사와 호출을 한다(Learn 예제 주석 「thread-safe manner」).
- ★ 언어는 **「델리게이트 타입」** 만 요구한다(`CS0066`). `Action` 이벤트도 1·3번에서 통과했다 — `sender`·`e` 는 **.NET 설계 지침**이다.

### 11. 잇기

- ★★ **멀티캐스트 규칙 = [27번](../27-delegates-and-func-action/) (4)** · **수명 연장 = [28번](../28-lambdas-and-closure-capture/) (5)**.
- ★ **[13번](../13-properties-init-required-field/)** — 속성의 `get_`/`set_`.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs29b-grid.cs` | csc 2회(진단 · 격자 파서용) | ★★★ **막힌 칸 12 / 30** — `CS0070` ×8 · `CS0079` ×4 |
| `cs29b-il.cs` | csc 1회(`-optimize`) · 실행 1회 | 숨은 필드 `E` · `add_E`/`remove_E` · `CompareExchange` 고리 · `callvirt add_E` |
| `cs29b-raise.cs` | csc 1회 · 실행 1회 | `null` · NRE · `Count` `0 · 1 · 0` |
| `cs29b-leak.cs` | **2×2 판 격자** | ★★★ `True False False True True True True True` · **갈린 줄 0 / 8** |
| `cs29b-acc.cs` | csc 1회 · 실행 1회 | `add`/`remove` 가 `+=`/`-=` 에서 불림 |
| `cs29b-form.cs` · `cs29b-bad.cs` | csc 2회 · 실행 1회 | `thermo : 20 → 21 …` · `CS0066` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12)에서만** 그렇다.

- ★★★ **숨은 필드의 이름 · `add_E` 의 `CompareExchange` 고리 · 캐시 이름 `<>O`** — Roslyn · ★ 진단 문구.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **바깥·파생에서는 `+=`·`-=` 만 · 접근자형은 안에서도 · 이벤트 타입은 델리게이트.**

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ `partial` 이벤트(C# 14) · 여러 스레드의 동시 구독 경쟁 · 약한 이벤트 패턴.
- **못 잰 것** — ★★ **GC 가 언제 회수하나**(시점).
- **잴 것이 없는 것** — ★ **④ 할당 바이트** — 이 주제의 물음이 수명이라 창을 GC 로 바꿨다(제5의 상태).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **2번** — `add_E` 를 다르게 적게 되면(잠금 · 다른 원자 연산) 덤프가 갈린다.
- ★ **1번** — Learn 의 「파생 클래스에서도 호출」과 다른 결과가 나온 칸(`event·derived`)을 다음 판에서 다시 찍어라.
