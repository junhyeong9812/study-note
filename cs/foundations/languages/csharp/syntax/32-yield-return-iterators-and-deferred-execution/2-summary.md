# csharp/syntax/32 — `yield return` 반복자와 지연 실행 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) §13.15 「The yield statement」(Learn 의 명세 링크가 가리키는 절) ·
> [Learn — `yield` 문](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/yield)(열어서 확인: 「**반복자를 부르면 바로 실행되지 않는다**」 · 「열거를 시작하면 **첫 `yield return` 까지** 실행되고 멈춘다 — 다음 반복마다 **멈춘 `yield return` 뒤에서** 이어진다」 ·\
> 「`yield` 는 **`in`/`ref`/`out` 매개변수가 있는 메서드 · 람다와 익명 메서드 · `catch`·`finally` 블록 · `catch` 가 딸린 `try` 블록**에서 못 쓴다 — **`finally` 만 딸린 `try`** 에서는 된다」 ·\
> 「`using` 으로 잡은 자원은 반복자가 끝나거나 **반복자 자체가 `Dispose` 될 때(호출자가 일찍 `break` 할 때 등)** 해제된다」) ·
> [Learn — C# 버전 이력](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-version-history)(C# 2.0 「Iterators」 — ★ 이 판에서 `-langversion:1` 이 **`CS8022 … 'iterators' … 2 or greater`** 로 확인해 줬다 · (5)).
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. **대비는 실측이다** — **javac 21.0.5** 로 `yield return` 한 줄을 던졌다((5)).
> **버전** — `yield return`·`yield break` **C# 2** · 지역 함수 **C# 7**(인자 검사를 나누는 관용구 · (2)) · LINQ **C# 3**.
> **경계** — ★★★ **`foreach` 가 `MoveNext`/`Current`/`Dispose` 로 풀리는 것**은 [31번](../31-ienumerable-and-foreach/)이 정본이다 — 여기는 **그 셋을 컴파일러가 만들어 주는 쪽.**\
> ★★ **「지역 변수가 컴파일러가 만든 클래스의 필드가 된다」** 는 [28번](../28-lambdas-and-closure-capture/) (1)의 디스플레이 클래스와 **같은 수법**이다 — 여기서는 상태 기계로.\
> ★★★ **교차 갈래 대비는 인용한다** — [Python 17번](../../../python/syntax/17-generators-yield/) §1 「**호출해도 몸통이 안 돈다**」 · [JS 20번](../../../js/syntax/20-generators/) (1)(「본문은 안 돌지만 **매개변수 목록은 돈다**」)·(3)(`return()` 과 `finally` — **상태에 따라 다르다**) · [JS 19번](../../../js/syntax/19-iterable-protocol-and-for-of/)(소비자 17가지 중 `return()` 을 부르는 자리) · [Go 39번](../../../go/syntax/39-iter-and-custom-iterators/)(**push** 반복자) ·\
> 게으름 로그 [JS 21번](../../../js/syntax/21-iterator-helpers/) · [Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/) · [Python 44번](../../../python/syntax/44-itertools/) — 세 갈래가 같은 파이프라인으로 **`10 · 10` 대 `4 · 4`** 를 냈다. **C# LINQ 로 한 칸 더**((6)).
> ★★★ **본체 창은 ③ 리플렉션 + ① IL 덤프다** — 「상태 기계」는 **컴파일러가 만든 클래스의 필드와 `MoveNext` 의 `switch`** 로만 보인다. 「언제 도나」는 **실행 로그**가 짝이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 진단 **순서**(배너에 `sort`) · IL **오프셋 폭** | ★★★ **진단 코드**(`CS1621`·`CS1622`·`CS1623`·`CS1624`·`CS1625`·`CS1626`·`CS1631`·`CS8022`) · **옵코드**(`newobj <Numbers>d__0` · `switch` · `stfld <>1__state`) |
> | ★ 컴파일러가 지은 **이름의 숫자**(`d__0` · `<i>5__2`) — Roslyn 구현 | ★★★ 이름의 **모양**(`<메서드>d__N` · `<>1__state` · `<>2__current` · `<>3__매개변수`) · **상태 값**(`-2` · `0` · `1` · `-1`) |
> | 증분의 절댓값 일부(규칙 24) | ★★★ **실행 로그의 줄 수와 순서** · **「finally 가 돈 소비자 N / M」** · 호출 수 **`4 · 4`** · **「네 판에서 갈린 줄 N / M」** |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version (exit=0) =====
javac 21.0.5
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | ★★★ **C# 언어가 약속한 것** | ★★★ 반복자 메서드를 부르면 **열거자 객체만** 돌아오고 본문은 **`MoveNext` 가** 돌린다 · `yield return` 에서 **멈추고** 다음 `MoveNext` 에서 **이어진다** · `Dispose` 가 **멈춘 자리의 `finally`** 를 돌린다 · `yield` 금지 자리 |
| **컴파일러 구현(Roslyn)** | ★★★ 그것을 **어떻게 적나** | ★★★ 중첩 클래스 **`<Numbers>d__0`** · 필드 **`<>1__state`·`<>2__current`·`<>3__limit`·`<>l__initialThreadId`·`<i>5__2`** · `MoveNext` 의 **`switch`** · 상태 값 **`-2`/`0`/`1`/`-1`** · ★★ **첫 `GetEnumerator` 는 자기 자신을 돌려준다 · `Dispose` 뒤 상태를 `-2` 로 되돌려 재사용** |
| **BCL(LINQ)** | 라이브러리 | ★★ `Select`·`Where`·`Take` 가 **게으른 반복자** — 사슬을 만들 때 로그 0 줄 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 할당 바이트 · 진단 문구 |

★★★ **이 주제의 층 구분이 급소다 —**\
**「호출 시점이 아니라 열거 시점에 실행된다」는 명세**다. **상태 기계의 클래스 이름 · 필드 이름 · 상태 값 · `switch` 는 Roslyn 구현**이다 — 명세는 「멈췄다가 이어진다」만 말하고 **어떻게** 멈추는지는 말하지 않는다. (3)의 **「두 번 열거해도 객체가 하나」** 는 그 구현의 귀결이지 명세가 아니다.

## 한눈에 — 쉽게 말하면

**`yield` 메서드는 「책갈피가 꽂힌 책」을 돌려준다 — 부른 사람은 책을 받았을 뿐이고, 읽기는 「다음 쪽」(`MoveNext`)을 누를 때마다 책갈피에서 한 토막씩 이어진다.**

- **책을 받는다(호출)** — 본문은 **한 줄도 안 돈다.** 매개변수만 책 속 쪽지에 적어 둔다(`<>3__limit`).
- **다음 쪽(`MoveNext`)** — 책갈피 자리(`<>1__state`)부터 **다음 `yield return` 까지** 읽고, 그 값을 `Current` 에 두고 **책갈피를 옮겨 꽂는다.**
- **지역 변수는 책 속에 산다** — `for` 의 `i` 가 **필드**(`<i>5__2`)가 된다. 그래서 멈췄다 이어져도 값이 남는다.
- **책을 덮는다(`Dispose`)** — 읽다 만 자리가 `try` 안이면 **`finally` 를 읽고** 덮는다. **안 덮고 버리면 `finally` 는 영영 안 돈다.**
- **입구 검사는 표지가 아니라 첫 쪽에 적힌다** — 본문 첫 줄의 `if (x == null) throw` 는 **첫 `MoveNext` 에서야** 읽힌다.

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 책만 받는다 | ★★★ `Numbers()` 뒤 · `GetEnumerator()` 뒤 **`본문:` 0 줄** | (1) |
| 한 토막씩 | ★★★ `MoveNext` 마다 **`yield … 뒤로 돌아옴` → 다음 `yield … 직전`** | (1) |
| 책갈피 | ★★★ **`<>1__state`** — 만든 직후 **`-2`** · 받은 뒤 **`0`** · 멈춤 **`1`** · 끝 **`-1`** | (3) |
| 지역 변수가 책 속에 | ★★★ **`<i>5__2` 필드** · `MoveNext` 가 `ldfld`/`stfld` 로 증가 | (3) |
| 덮으면 `finally` | ★★★ `break` · 예외 · `First()` 는 `finally` · **`Dispose` 안 부름은 안 돈다** — **7 / 10** | (4) |
| 입구 검사가 늦다 | ★★★ `Doubled(null)` **호출 : 돌아옴** · 열거 : `ArgumentNullException` | (2) |

★★★ **이 주제의 본체 그림 — 상태 기계.**

```text
   소스                                          Roslyn 이 만든 것
   ─────────────────────────────────────         ──────────────────────────────────────────────────────────
   static IEnumerable<string> Three() {          Three() {                                  ← 본문이 없다
       yield return "a";                             return new <Three>d__1(-2);            ← 상태 -2 로 객체만
       yield return "b";                         }
       yield return "c";                         sealed class <Three>d__1 : IEnumerable<string>, IEnumerator<string>, IDisposable
   }                                               int    <>1__state;      ← 책갈피
                                                   string <>2__current;    ← Current
                                                   int    <>l__initialThreadId;
                                                   bool MoveNext() {
                                                     switch (<>1__state) {
                                                       case 0: state = -1; current = "a"; state = 1; return true;
                                                       case 1: state = -1; current = "b"; state = 2; return true;
                                                       case 2: state = -1; current = "c"; state = 3; return true;
                                                       case 3: state = -1;                           return false;
                                                       default:                                       return false;
                                                     }
                                                   }
                                                 }

   상태 값 (이 판)
     -2  만든 직후 — 아직 GetEnumerator 전 ──GetEnumerator──▶  0  시작 전
      0 ──MoveNext──▶ (-1 로 두고 본문 토막 실행) ──yield──▶  1 · 2 · 3 …  멈춤(다음에 어느 토막인가)
      끝에 닿으면 ─▶ -1 · Dispose 하면 ─▶ -2 (★ 이 판 Roslyn — 다시 GetEnumerator 하면 같은 객체를 재사용)

   ★★★ 「멈췄다가 이어진다」 는 명세 — 「switch 가 붙은 MoveNext 와 state 필드」 는 Roslyn 이 고른 방법이다.
```

## 이 주제가 답하려는 질문

1. **본문은 언제 도나** — 부를 때 · `GetEnumerator` 때 · `MoveNext` 때((1)) — 그리고 그 결과 **인자 검사가 늦게 터지는** 함정((2)).
2. **상태 기계는 무엇으로 되어 있나** — 클래스 · 필드 · 상태 값 · `switch`((3)).
3. **`finally` 는 언제 도나** — `break` · 예외 · `Dispose` 안 부름((4)) · **어디서 `yield` 를 못 쓰나**((5)).
4. **LINQ 는 얼마나 게으른가 · 두 번 열거하면**((6)(7)) · **할당은**((8)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ③ 리플렉션 + ① IL 덤프다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **③ 리플렉션** | ★★★ 컴파일러가 만든 **`<Numbers>d__0`** 의 인터페이스 다섯 · 필드 여섯 · **`<>1__state` 값을 한 걸음씩** · `ReferenceEquals(seq, e)` | (3) |
| ★★★ **① IL 덤프** | ★★★ `Numbers` 에 본문이 없다(`ldc.i4.s -2` · `newobj` · `stfld <>3__limit`) · `MoveNext` 의 **`switch`**(`Three`) · 두 상태면 `brfalse`/`beq` | (3) |
| ★★★ **실행 로그** | ★★★ 「언제 도나」 — `본문:` 줄 · `finally` 줄 · `map(…)`/`filter(…)` 호출 순서 · 본문 실행 횟수 | (1)(2)(4)(6)(7) |
| ★★ **② 진단 격자** | ★★ `yield` 금지 자리 여덟 코드 · `CS8022`(C# 1) · javac `not a statement` | (5) |
| ★★ **④ 할당 바이트** | ★★ 부르기만 · 한 번 열거 · **두 번 열거가 같은 32000** — 2×2 | (8) |
| **부적용인 창** | 없다 | — |

### (1) ★★★ 본체 — 부를 때는 0 줄, `MoveNext` 가 한 토막씩

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

- ★★★ **`[1]` `Numbers()` 와 `[2]` `GetEnumerator()` 뒤에 `본문:` 줄이 하나도 없다** — 부르기만 해서는 **`본문: 시작` 조차 안 찍힌다.** [Python 17번](../../../python/syntax/17-generators-yield/) §1 · [JS 20번](../../../js/syntax/20-generators/) (1)과 **같은 성질**이다.
- ★★★ **`[3]` 첫 `MoveNext` 에서 `본문: 시작` · `yield 1 직전` 까지 돌고 `True · Current = 1`** — 첫 `yield return` 에서 멈췄다.
- ★★★ **`[4]`·`[5]` 는 `yield N 뒤로 돌아옴` 으로 시작한다** — 지난번 **멈춘 자리 바로 뒤**에서 이어진다(Learn 의 문장 그대로).
- ★★ **`[6]` 마지막 `MoveNext` 가 `yield 3 뒤로 돌아옴` · `본문: 끝` 을 돌리고 `False`** — 끝을 알리는 것도 **본문을 끝까지 돌린 뒤**다.

### (2) ★★★ 인자 검사가 늦게 터진다 — 지역 함수로 나누는 관용구

**언제 쓰나** — 「반복자 메서드의 첫머리에 `if (x is null) throw` 를 두었는데 **왜 엉뚱한 곳에서** 터지나」.

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

- ★★★ **`[1]` `Doubled(null)` — 호출 : 돌아옴 · 열거 : `ArgumentNullException`** — 검사 줄도 **본문의 일부**라서 첫 `MoveNext` 까지 **안 돈다.** 잘못된 인자를 넘긴 **호출 자리**가 아니라, 한참 뒤 그것을 **`foreach` 한 자리**에서 터진다.
- ★★★ **`[2]` `DoubledSplit(null)` — 호출 : `ArgumentNullException`** — 바깥 메서드에는 **`yield` 가 없어서 보통 메서드**다. 검사가 **바로** 돌고, 반복자는 안쪽 **지역 함수 `Core()`** 가 된다.
- ★★ **관용구의 뼈대** — 「**바깥 = 검사 + `return Core();`** · **안 = `yield`**」. `yield` 가 한 줄이라도 있으면 **메서드 전체가 반복자**가 된다는 것이 함정의 뿌리다.

```text
   Doubled(null)                               DoubledSplit(null)
   ─────────────────────────                   ───────────────────────────────────
   호출  → new <Doubled>d__(…)  (검사 안 함)     호출  → if (src is null) throw   ✕ 여기서
   …                                                     return Core();
   foreach → MoveNext                          (Core 는 반복자 — 검사가 이미 끝났다)
            → if (src is null) throw   ✕ 여기서
   ★ 두 판의 차이는 「검사 줄이 어느 메서드에 있나」 하나다.
```

### (3) ★★★ 상태 기계 — 클래스 · 필드 · 상태 값 · `switch`

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

- ★★★ **중첩 타입 `<Numbers>d__0`(`class` · `sealed`)** — 구현한 인터페이스가 **`IDisposable` · `IEnumerable` · `IEnumerable<T>` · `IEnumerator` · `IEnumerator<T>` 다섯**. **열거 가능이면서 열거자**다 — 한 객체가 두 역할([31번](../31-ienumerable-and-foreach/) (3))을 겸한다.
- ★★★ **필드 여섯** — **`<>1__state`**(책갈피) · **`<>2__current`**(`Current`) · **`<>3__limit`**(호출 때 받은 인자의 원본) · **`limit`**(열거자가 쓰는 사본) · **`<>l__initialThreadId`**(만든 스레드) · **`<i>5__2`**(지역 변수 `i` — [28번](../28-lambdas-and-closure-capture/) (1)처럼 **지역 변수가 필드**가 됐다).
- ★★★ **`Numbers` 의 IL 에 `for` 가 없다** — **`ldc.i4.s -2` · `newobj <Numbers>d__0::.ctor` · `stfld <>3__limit` · `ret`**. 호출은 **객체를 만들고 인자를 적는 것**이 전부다. 이것이 「호출 시점에 안 돈다」의 **IL 증명**이다.
- ★★★ **상태 값** — `[1]` 만든 직후 **`-2`** · `[2]` 첫 `GetEnumerator` 뒤 **`0`** · `[4]`·`[5]` `MoveNext → True` 뒤 **`1`**(멈춤) · `[6]` `False` 뒤 **`-1`**(끝).
- ★★★ **`[2]` 첫 `GetEnumerator` 는 `ReferenceEquals(seq, e) = True` — 자기 자신을 돌려준다** · **`[3]` 두 번째는 `False`** — 이미 쓰는 중이라 **새 객체**를 만든다(상태 `0`). `<>l__initialThreadId` 와 상태 `-2` 가 그 판단의 재료다(Roslyn 구현).
- ★★ **`[7]` `Dispose` 뒤 상태가 `-2` · `[8]` 그 뒤 `GetEnumerator` 는 다시 `True`(같은 객체)** — **이 판의 Roslyn 은 다 쓴 객체를 되살려 쓴다.** (8)의 할당이 이것으로 설명된다.
- ★★★ **`Three` 의 `MoveNext` — `switch (IL_001f, IL_003a, IL_0055, IL_0070)` 갈래 넷** — `yield` 셋 + 끝 하나. 갈래마다 **`state = -1`(실행 중) → `<>2__current` 에 값 → `state = N` → `return true`**. 본체 그림이 이 덤프를 그대로 읽은 것이다.
- ★★ **`Numbers` 의 `MoveNext` 는 `switch` 가 아니라 `brfalse.s`/`beq.s`** — 상태가 **둘(0 · 1)** 뿐이라 Roslyn 이 비교 두 번으로 적었다. `for` 고리 자체는 `<i>5__2` 필드를 `ldfld`/`stfld` 하는 **보통 고리**다.

### (4) ★★★ `finally` 는 언제 도나 — 소비자 열 가지

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

- ★★★ **finally 가 돈 소비자 7 / 10** — 스크립트가 셌다.
- ★★★ **`[2]` `break` → `try / finally`** — `foreach` 의 `finally` 가 **열거자의 `Dispose`** 를 부르고([31번](../31-ienumerable-and-foreach/) (4)), 반복자의 `Dispose` 가 **멈춘 자리(`yield return 1` — `try` 안)의 `finally`** 를 돌린다. **`[3]` 몸통이 던져도** 같다(`finally` 가 바깥 `catch` 보다 **먼저**).
- ★★★ **`[4]` `MoveNext` 한 번 뒤 `Dispose` 를 안 부르면 `try` 만** — **`finally` 가 영영 안 돈다.** 열거자를 손으로 다룰 때는 **`using`** 을 써라. **`[5]` `Dispose` 를 부르면 `finally`.**
- ★★ **`[6]` `MoveNext` 전에 `Dispose` · `[7]` 부르기만 → 로그 0 줄** — `try` 에 **들어간 적이 없으니** `finally` 도 없다.
- ★★ **`[8]` `First()` · `[9]` `Take(1).ToList()` · `[10]` `Any()` → `try / finally`** — LINQ 도 **하나만 보고 떠날 때 `Dispose` 를 부른다.**

```text
   JS 제너레이터와 한 쌍 — 「중간에 떠나면 정리가 도나」

                         C# yield  (Dispose)                  JS function* (return())  — JS 20편 (3)
   시작 전에 멈춤         [6] 로그 0 줄 — finally 없음           return('R') 시작 전 — body (no log)
   yield 에서 멈춘 뒤      [5] finally                            return('R') 멈춤 — body: finally
   다 끝난 뒤             (이미 finally 가 돌았다 [1])             return('R') 완료 뒤 — body (no log)
   for 를 break           [2] finally  (foreach 가 Dispose)       break 가 return() — JS 19편 · finally
   finally 안에서 yield    ✕ CS1625 (5)                           된다 — finally 가 한 번 더 멈춘다 (JS 20편 (3)[2])

   ★★★ 세 상태의 표가 두 언어에서 같다. 갈리는 칸은 「finally 안의 yield」 하나 — C# 은 컴파일 에러로 막는다.
```

### (5) ★★ `yield` 를 쓸 수 없는 자리 · 판 경계 · Java

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

- ★★★ **여덟 줄** — `finally` 안 **`CS1625`** · `catch` 가 딸린 `try` 안 **`CS1626`** · `catch` 안 **`CS1631`** · `ref` 매개변수 **`CS1623`** · 람다 안 **`CS1621`**(+ 반환 경로 `CS1643`) · `List<int>` 반환 **`CS1624`**(「반복자 인터페이스 타입이 아니다」) · `yield` 와 `return 값` 섞기 **`CS1622`**. Learn 의 금지 목록(`in`/`ref`/`out` · 람다 · `catch`/`finally` · `catch` 딸린 `try`)이 전부 진단으로 나왔다.
- ★★ **`catch` 가 딸린 `try` 는 안 되고 `finally` 만 딸린 `try` 는 된다**((4)의 `Guarded` 가 그것이다) — 멈춘 자리에서 **예외를 잡아 이어 갈 방법**이 상태 기계에 없다는 뜻으로 읽힌다(이유는 명세를 **안 읽었다**).
- ★★ **`-langversion:1` → `CS8022 … 'iterators' … 2 or greater` · `2` → 통과** — `yield` 는 **C# 2** 다.
- ★★★ **Java `yield return 1;` → `not a statement` · `';' expected`** — Java 에는 반복자 `yield` 가 없다. Java 의 `yield` 는 **`switch` 식에서 값을 내는** 다른 낱말이다([Java 21번](../../../java/syntax/21-switch-statement-and-expression/)). 게으른 시퀀스는 **`Iterator` 를 손으로 쓰거나 `Stream`** 으로 우회한다.

### (6) ★★★ LINQ 게으름 — `10 · 10` 대 `4 · 4`

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

- ★★★ **`[2]` 사슬을 만든 직후 로그 0 줄** — `Select`·`Where`·`Take` 는 (1)의 `Numbers()` 처럼 **객체만 돌려준다.**
- ★★★ **`[2]` `ToList()` 뒤 map 4 · filter 4 · 순서 `map(1) filter(10) map(2) filter(20) …`** — **원소 하나가 사슬 전체를 세로로** 지나간다. `Take(2)` 가 둘을 채우자 **원본을 더 안 당겼다.**
- ★★★ **`[1]` 단계마다 `ToList` 는 map 10 · filter 10 · 가로로** — 단계마다 **전부** 돈다.
- ★★★ **JS 21번 · Rust 36번 · Python 44번과 수도 순서도 같다** — 네 번째 갈래가 **같은 표**를 만들었다. 게으름은 **언어가 아니라 「당기는 반복자 사슬」의 성질**이다.
- ★★★ **「LINQ 는 느리다」는 이 문서가 잰 것이 아니다** — 잰 것은 **호출 수**다.

```text
   같은 파이프라인 — 원본 1..10 · map x*10 · filter 20 의 배수 · 앞의 둘

                    단계마다 모으기            사슬(게으름)
   JS   21편        map 10 · filter 10        map 4 · filter 4
   Rust 36편        map 10 · filter 10        map 4 · filter 4
   Python 44편      map 10 · filter 10        map 4 · filter 4
   C#   (6)         map 10 · filter 10        map 4 · filter 4     ← 한 칸 더

   ★ 네 언어 모두 pull — 소비자(ToList · collect · list())가 MoveNext/next 를 부른다.
     Go 의 iter.Seq 는 push — 반복자가 몸통(yield 콜백)을 부른다 (Go 39편). C# 의 yield 는 이름은 같아도 pull 쪽이다.
```

### (7) ★★ 두 번 열거하면 두 번 실행된다

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

- ★★★ **`[1]` `q.Count()` · `q.Sum()` → 본문 실행 2 번** — `q` 는 **결과가 아니라 「결과를 만드는 방법」** 이다. 쓸 때마다 **처음부터 다시** 돈다. 본문이 DB·파일·네트워크를 읽는다면 **두 번 읽는다.**
- ★★★ **`[2]` `ToList()` 로 한 번 모으면 1 번** — 그 뒤 `Count`·`Sum` 은 **리스트**를 읽는다.

### (8) ★★ 할당 바이트 — 부르기만 해도 객체는 생긴다 · 2×2 판 격자

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

- ★★★ **네 판에서 갈린 줄 0 / 3 · 세 줄이 전부 32000** — **`[1]` 부르기만 해도** 본문은 0 줄이지만 **상태 기계 객체는 생긴다.**
- ★★★ **`[2]` 부르고 한 번 `foreach` 가 `[1]` 과 같다** — 첫 `GetEnumerator` 가 **자기 자신**을 돌려주므로((3) `[2]`) 열거자를 따로 안 만든다.
- ★★★ **`[3]` 같은 결과를 두 번 `foreach` 해도 같다** — 첫 `foreach` 의 `Dispose` 가 상태를 `-2` 로 되돌려((3) `[7]`) **두 번째 `GetEnumerator` 가 같은 객체를 재사용**했다((3) `[8]`). ★ **이 판 Roslyn 의 구현**이다 — 명세는 「두 번째 열거에 새 객체를 쓰느냐」를 정하지 않는다.
- ★ **시간은 안 쟀다.**

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs32b-form.cs =====
using System;
using System.Collections.Generic;
using System.Linq;

static IEnumerable<int> Evens(int upto) {
    for (int i = 0; i <= upto; i += 2) yield return i;
}
static IEnumerable<int> UntilNegative(IEnumerable<int> xs) {
    foreach (var x in xs) { if (x < 0) yield break; yield return x; }
}
static IEnumerable<long> Fib() { long a = 0, b = 1; while (true) { yield return a; (a, b) = (b, a + b); } }

Console.WriteLine($"{string.Join(",", Evens(8))} · {string.Join(",", UntilNegative([3, 1, -1, 9]))} · {string.Join(",", Fib().Take(8))}");
===== csc -out:ex.dll cs32b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
0,2,4,6,8 · 3,1 · 0,1,1,2,3,5,8,13
```

- ★★★ **`yield return 값;`** — 한 값을 내고 멈춘다 · **`yield break;`** — 끝낸다(`UntilNegative` 는 `-1` 에서 끝나 `3,1`).
- ★★ **반환 타입은 `IEnumerable<T>`·`IEnumerator<T>`(또는 제네릭 아닌 둘)** — `List<T>` 면 `CS1624`((5)).
- ★★ **무한 반복자** — `Fib()` 는 `while (true)` 인데 **`Take(8)` 이 여덟 번만 당겨** 끝난다. 게으르기 때문에 성립한다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `finally` 안의 `yield` | `CS1625` | (5) |
| `catch` 가 딸린 `try` 안의 `yield return` | `CS1626` | (5) |
| `catch` 안의 `yield` | `CS1631` | (5) |
| `ref`·`in`·`out` 매개변수가 있는 반복자 | `CS1623` | (5) |
| 람다·익명 메서드 안의 `yield` | `CS1621` | (5) |
| 반환 타입이 반복자 인터페이스가 아님 | `CS1624` | (5) |
| `yield` 와 `return 값;` 을 섞음 | `CS1622` | (5) |
| C# 1 에서 반복자 | `CS8022` | (5) |
| Java 에서 `yield return` | javac `not a statement` | (5) |
| ★★★ 반복자 안의 인자 검사 | ★★★ **진단 없음** — 열거 때 터진다 | (2) |
| ★★★ 같은 `IEnumerable` 을 두 번 소비 | ★★★ **진단 없음** — 본문이 두 번 돈다 | (7) |

## 어디서 틀리나

1. ★★★ **「`yield` 메서드를 부르면 본문이 돈다」** — **0 줄**이다. 첫 `MoveNext` 부터다((1)).
2. ★★★ **「첫머리의 인자 검사는 호출할 때 터진다」** — **열거할 때** 터진다. 지역 함수로 나눠라((2)).
3. ★★★ **「`break` 하면 반복자의 `finally` 는 안 돈다」** — **돈다**(`foreach` 가 `Dispose`)((4) `[2]`). **안 도는 것은 `Dispose` 를 안 부른 손 열거**다((4) `[4]`).
4. ★★★ **「`IEnumerable` 변수는 결과를 들고 있다」** — **만드는 방법**을 들고 있다. 두 번 쓰면 두 번 돈다((7)).
5. ★★★ **「LINQ 사슬은 단계마다 전부 돈다」** — **원소 하나씩 세로로**, 필요한 만큼만 돈다(`4 · 4`)((6)).
6. ★★ **「부르기만 하면 비용이 0 이다」** — 본문은 0 줄이어도 **객체는 생긴다**(1000번 32000)((8)).
7. ★★ **「`finally` 안에서도 `yield` 할 수 있다」** — C# 은 **`CS1625`**. JS 는 된다((4)(5)).
8. ★★ **「상태 기계의 필드 이름·상태 값은 C# 의 규칙이다」** — **Roslyn 구현**이다((3)).
9. ★ **「Java 의 `yield` 도 같은 것이다」** — `switch` 식의 값 내기다. 반복자 `yield` 는 **없다**((5)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **부르면 본문이 안 돌고 `MoveNext` 가 돌린다 · 멈췄다 이어진다** | ★★★ **언어(334)** | (1)(3) |
| **`Dispose` 가 멈춘 자리의 `finally` 를 돌린다** | ★★★ **언어** | (4) |
| **`yield` 금지 자리** | ★★★ **언어** | (5) |
| **인자 검사가 늦게 터지는 것** | ★★★ **언어의 귀결**(검사도 본문이다) | (2) |
| **클래스 `<M>d__N` · 필드 `<>1__state`·`<>2__current`·`<>3__x` · 상태 값 `-2/0/1/-1` · `switch`** | ★★★ **Roslyn 구현** | (3) |
| **첫 `GetEnumerator` 가 자기 자신 · `Dispose` 뒤 `-2` 로 재사용** | ★★★ **Roslyn 구현** | (3)(8) |
| **LINQ `Select`·`Where`·`Take` 가 게으르다** | ★★ **BCL 계약**(문서화된 지연 실행) | (6) |
| **할당 바이트 값** | ★ **이 판의 관찰** | (8) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **열거자를 손으로 쓸 자리면 `yield` 로 써라** — [31번](../31-ienumerable-and-foreach/) (7)의 `Traced` 가 20줄이면 `yield` 는 몇 줄이다. 상태 기계는 컴파일러가 만든다.
- ★★★ **반복자에 인자 검사가 있으면 바깥 메서드 + 지역 함수로 나눠라**((2)).
- ★★★ **여러 번 쓸 결과면 `ToList()`/`ToArray()` 로 한 번 모아라** — 특히 본문이 I/O 를 할 때((7)).
- ★★ **반복자에서 자원을 잡으면 `using`/`try`/`finally` 로** — 소비자가 `foreach` 를 쓰면 `break` 에도 정리된다. 손으로 `GetEnumerator()` 를 부르는 소비자는 **`using` 을 써야** 한다((4)).
- ★★ **무한·거대 시퀀스는 게으름의 몫이다** — `Take`·`First` 가 필요한 만큼만 당긴다((6) · 형태의 `Fib`).
- ★ **순서가 중요한 부수 효과(로그·카운터)를 LINQ 람다에 넣지 마라** — 세로로 번갈아 돈다((6)).

## 핵심 문장

1. ★★★ **`yield` 메서드를 부르면 본문은 0 줄 — `newobj <M>d__N` + 인자 복사가 전부이고, 본문은 `MoveNext` 가 한 토막씩 돌린다**((1)(3)).
2. ★★★ **그래서 첫머리의 인자 검사도 열거 때 터진다 — 바깥 메서드 + 지역 함수로 나눈다**((2)).
3. ★★★ **상태 기계 = `<>1__state`(-2 · 0 · 1 · -1) + `<>2__current` + 필드가 된 지역 변수 + `MoveNext` 의 `switch`** — 전부 Roslyn 구현이고, 「멈췄다 이어진다」만 명세다((3)).
4. ★★★ **`break` 는 `Dispose` 로 `finally` 를 돌린다 — `Dispose` 를 안 부른 손 열거만 안 돈다(7 / 10)** — JS 의 `return()` 표와 같다((4)).
5. ★★★ **LINQ 사슬은 `4 · 4`, 단계마다 모으면 `10 · 10`** — JS·Rust·Python 과 같은 표 · 두 번 열거하면 두 번 돈다((6)(7)).

## 관련 자료

- [31번 — `IEnumerable<T>` 와 `foreach`](../31-ienumerable-and-foreach/) — **경계**: `foreach` 가 `MoveNext`/`Current`/`Dispose` 로 풀리는 것은 거기. 여기는 그 셋을 **컴파일러가 만든다.**
- [28번 — 람다와 캡처](../28-lambdas-and-closure-capture/) (1) — 지역 변수가 필드가 되는 같은 수법(디스플레이 클래스).
- [30번 — 확장 메서드](../30-extension-methods-and-extension-members/) (1) — LINQ 가 확장 메서드 묶음이라는 것.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **17번**([`17-generators-yield/`](../../../python/syntax/17-generators-yield/)) · **44번**([`44-itertools/`](../../../python/syntax/44-itertools/)).
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **19번**([`19-iterable-protocol-and-for-of/`](../../../js/syntax/19-iterable-protocol-and-for-of/)) · **20번**([`20-generators/`](../../../js/syntax/20-generators/)) · **21번**([`21-iterator-helpers/`](../../../js/syntax/21-iterator-helpers/)).
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **36번**([`36-iterator-adapters-laziness-and-collect/`](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/)).
- Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **39번**([`39-iter-and-custom-iterators/`](../../../go/syntax/39-iter-and-custom-iterators/)) — push 반복자.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **21번**([`21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/)) — Java 의 `yield` 는 `switch` 식의 것.

## 용어 풀이

- **반복자(iterator)** — 본문에 `yield return`/`yield break` 가 있는 메서드(또는 접근자). 부르면 열거자 객체를 돌려준다.
- **지연 실행(deferred execution)** — 결과를 **쓸 때** 계산하는 것. 부르는 때가 아니라 열거하는 때.
- **상태 기계(state machine)** — 「지금 몇 번째 토막인가」를 필드(`<>1__state`)에 적어 두고 `MoveNext` 가 그 값으로 갈래를 고르는 구조.
- **`<>1__state` · `<>2__current` · `<>3__x`** — Roslyn 이 짓는 필드 이름. 상태 · 현재 값 · 인자 원본.
- **pull 대 push** — 소비자가 `MoveNext` 로 **당기는** 반복자(C# · JS · Python · Rust) 대 반복자가 몸통을 **부르는** 반복자(Go `iter.Seq`).
- **지역 함수(local function)** — 메서드 안에 선언한 메서드(C# 7). 인자 검사를 반복자 밖으로 빼는 데 쓴다.

## 더 들어가면

- ★ **`IAsyncEnumerable<T>` · `await foreach`(C# 8)** — 비동기 반복자. 비동기 묶음에서.
- ★ **`Reset()`** — 반복자의 `Reset` 은 `NotSupportedException` 을 던진다고 알려져 있다. **이 판에서 안 불렀다.**
- ★ **여러 스레드에서 같은 반복자 결과를 동시에 `GetEnumerator`** — `<>l__initialThreadId` 가 그 판단에 쓰인다((3)). **스레드 실험은 안 돌렸다.**
- ★ **Dispose 뒤 상태를 `-2` 로 되돌리는 것이 언제부터의 Roslyn 인가** — 옛 컴파일러는 확인하지 않았다.
