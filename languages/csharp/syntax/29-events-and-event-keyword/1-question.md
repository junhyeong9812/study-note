# csharp/syntax/29 — 이벤트와 `event` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**`event` 는 멀티캐스트 델리게이트 필드를 숨기고 `add`/`remove` 두 메서드만 밖에 연다**」 한 줄로 거의 다 풀린다. **밖에서 무엇을 부를 수 있나**와 **누가 누구를 붙드나**를 세라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`.
> ★★★ **본체 창은 ② 진단 격자다**(「`event` 가 막는 것」). 누수는 **`WeakReference` 의 「회수됐나」** 로 물었다(2×2 판 격자).
> 선행 — [27번](../27-delegates-and-func-action/)(멀티캐스트 — 반환값·중간 예외·`-=`) · [28번](../28-lambdas-and-closure-capture/)(캡처가 수명을 늘린다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 같은 델리게이트를 필드로 · `event` 로 · 접근자로 — 식 여섯 × 자리 다섯 (예측)

```csharp
// cs29b-grid.cs
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
```

- 30칸 중 **진단이 나는 칸**은 어디이고, 코드는 무엇인가?
- ★★★ `event` 를 **바깥**(`Other`)에서 쓸 때 남는 식은 무엇인가?
- ★★ **파생 클래스**(`Sub`)는 바깥과 같은가, 안쪽과 같은가?
- ★★ 접근자를 직접 쓴 `C` 는 **선언한 클래스 안에서도** 막히는 칸이 있나?

### 2. ★★★ `event` 를 열어 보면 (예측)

```csharp
// cs29b-il.cs
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
```

- `Pub` 에는 필드가 몇 개이고, `E` 라는 이름의 필드가 있나? 그 접근성은?
- ★★★ `event E` 는 어떤 메서드 둘이 되나? 속성 `P` 와 모양이 같은가?
- ★★ `add_E` 의 IL 에는 `Delegate::Combine` 말고 무엇이 더 있나?
- ★★★ `p.F += H` 와 `p.E += H` 의 IL 은 어디가 다른가?

### 3. ★★ 구독자가 없을 때 · 떼기 셋 (예측)

```csharp
// cs29b-raise.cs
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
```

- `[1]`\~`[3]` 은?
- ★★★ `[4]`·`[5]`·`[6]` 의 `Count` 는 각각 몇인가?

### 4. ★★★ 오래 사는 발행자와 짧게 사는 구독자 (예측)

```csharp
// cs29b-leak.cs
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
```

- `[1]`\~`[8]` 은 각각 `True` 인가 `False` 인가?
- ★★★ `[5]` — 구독을 **해제하지 않았다.** 그래도?
- ★ 네 판(2×2)에서 갈리는 줄이 있는가?

### 5. ★★ `add`/`remove` 를 직접 쓰면 (예측)

```csharp
// cs29b-acc.cs
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
```

- 출력 순서는? `p.Tick += A` 는 어느 코드를 부르나?

### 6. ★★ 1번의 두 「안쪽」 열 — `event·inside` 와 `custom·inside` (왜)

- 두 열의 결과를 **「그 이벤트에 필드가 있나」** 로 설명하라.

### 7. ★★★ 이벤트를 발생시키는 것은 멀티캐스트 델리게이트를 부르는 것이다 (연결)

- [27번](../27-delegates-and-func-action/) (4)의 세 결론(반환값은 마지막 것만 · 중간이 던지면 뒤가 안 불린다 · `-=` 는 끝에서부터)은 이벤트에서 각각 무엇을 뜻하나?

### 8. ★★ 무엇이 명세이고 무엇이 구현인가 (왜)

- 「바깥에서는 `+=`·`-=` 만」·「`add_E`/`remove_E` 라는 이름」·「숨은 필드의 이름이 이벤트와 같다」·「`add_E` 안의 `CompareExchange` 고리」는 각각 어느 층인가?

### 9. ★★★ 28번의 누수와 이 주제의 누수 (경계)

- 28번 (5)는 「**람다가** 캡처한 객체를 붙든다」였다. 4번의 `[2]` 에서 **누가 누구를** 붙드나? `[5]` 는 그 방향으로 어떻게 설명되나?

### 10. ★★ `?.Invoke` 와 `EventHandler<TEventArgs>` (경계)

- 3번 `[2]`·`[3]` 에 비추어, 이벤트를 발생시킬 때 `?.Invoke` 를 쓰는 이유는?
- ★ .NET 관례의 두 인자(`sender`·`e`)는 언어가 강제하나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 멀티캐스트의 호출 목록·`-=` 규칙의 정본은 몇 번이고, 수명 연장의 정본은 몇 번인가?
- ★ 속성이 `get_`/`set_` 메서드가 되는 것을 먼저 본 주제는 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
