# csharp/syntax/32 — `yield return` 반복자와 지연 실행 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**`yield` 메서드를 부르면 본문 대신 상태 기계 객체가 돌아오고, 본문은 `MoveNext` 가 한 토막씩 돌린다**」 한 줄로 거의 다 풀린다. **본문의 어느 줄이 언제 도나**를 세라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest`(판 문항만 판을 바꾼다) · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ③ 리플렉션 + ① IL 덤프다**(상태 기계). 「언제 도나」는 **실행 로그**로 물었다.
> 선행 — [31번](../31-ienumerable-and-foreach/)(`foreach` 가 `MoveNext`/`Current`/`Dispose` 로 풀린다) · [28번](../28-lambdas-and-closure-capture/)(지역 변수가 필드가 된다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 부르고 · 열거자를 받고 · 한 칸씩 당기면 (예측)

```csharp
// cs32b-lazy.cs
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
```

- ★★★ `[1]`·`[2]` 뒤에 `본문:` 줄이 몇 줄 찍히나?
- ★★★ `[3]`\~`[6]` 각각 뒤에 찍히는 `본문:` 줄은? `[6]` 의 `MoveNext` 는 무엇을 돌려주나?

### 2. ★★★ `null` 인자 검사 — 두 판 (예측)

```csharp
// cs32b-arg.cs
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
```

- ★★★ `[1]` 과 `[2]` 에서 예외는 **호출** 때 나나 **열거** 때 나나?

### 3. ★★★ 컴파일러가 만든 상태 기계를 열어 보면 (예측)

```csharp
// cs32b-sm.cs
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
```

- 중첩 타입의 이름 모양 · 구현한 인터페이스 · 필드는?
- ★★★ `[1]`\~`[8]` 의 `<>1__state` 값과 `ReferenceEquals` 는?
- ★★ `Numbers` 메서드 자신의 IL 에 본문(`for`)이 있나?
- ★★ `Three` 의 `MoveNext` 에서 `switch` 의 갈래는 몇 개인가?

### 4. ★★★ `finally` 는 언제 도나 — 소비자마다 (예측)

```csharp
// cs32b-fin.cs
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
```

- ★★★ 열 줄 각각에 `finally` 가 찍히나? 마지막 줄의 수는?

### 5. ★★ `Select`·`Where`·`Take(2)` 사슬 (예측)

```csharp
// cs32b-linq.cs
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
```

- ★★★ `[1]`·`[2]` 의 `map`·`filter` 호출 수와 순서는? 사슬을 만든 직후 로그는 몇 줄인가?

### 6. ★★ 같은 `IEnumerable` 을 두 번 쓰면 (예측)

```csharp
// cs32b-twice.cs
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
```

- `[1]`·`[2]` 에서 `Load` 본문은 몇 번 도나?

### 7. ★★★ 1번의 `[1]`·`[2]` 를 IL 로 (왜)

- 1번의 결과를 3번의 `Numbers` IL 로 설명하라. **명세**가 보장하는 부분과 **Roslyn** 이 적은 부분은 어디서 갈리나?

### 8. ★★★ 4번의 `[2]` 대 `[4]` (왜)

- 두 줄의 차이를 [31번](../31-ienumerable-and-foreach/) (4)의 `finally` 로 설명하라.
- ★★ JS 제너레이터의 `return()` 과 견주면(JS 20번 (3)) — 「시작 전에 멈추게 하면」 두 언어는 같은가?

### 9. ★★ `yield` 를 쓸 수 없는 자리 · 판 경계 (경계)

- `finally` 안 · `catch` 가 있는 `try` 안 · 람다 안 · `ref` 매개변수 · `List<int>` 반환 · `return` 과 섞기 — 각각의 진단 코드는? C# 1 에서는?
- ★ Java 에서 `yield return 1;` 을 쓰면?

### 10. ★★ 할당 바이트 — 부르기만 · 한 번 열거 · 같은 것을 두 번 열거 (경계)

- `Numbers()` 를 1000번 **부르기만** 한 판 · **부르고 한 번 `foreach`** 한 판 · **같은 결과를 두 번 `foreach`** 한 판의 할당은 같은가 다른가? 3번의 `[7]`·`[8]` 로 설명하라.

### 11. ★★ 다른 언어의 제너레이터와 (연결)

- 「부르기만 하면 본문이 안 돈다」는 Python·JS 에서도 같은가? Go 의 `iter.Seq` 는 **당기는(pull)** 쪽인가 **미는(push)** 쪽인가 — C# 은?
- ★ 5번의 두 수는 JS 21번 · Rust 36번 · Python 44번의 표와 같은가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
