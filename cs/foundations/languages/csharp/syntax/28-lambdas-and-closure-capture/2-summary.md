# csharp/syntax/28 — 람다식과 클로저 캡처 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 람다 식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/lambda-expressions)(열어서 확인: 「람다는 **바깥 변수**를 참조할 수 있다 — 캡처하면 **변수가 범위를 벗어나 보통은 회수될 때에도** 람다가 그것을 보관한다」 ·\
> 「**캡처한 변수는 그것을 참조하는 델리게이트가 회수 대상이 될 때까지 회수되지 않는다**」 · 「**`static` 람다는 지역 변수나 인스턴스 상태를 캡처할 수 없지만 정적 멤버와 상수는 참조할 수 있다**」 ·\
> 예제 출력 「Another lambda observes a new value of captured variable: True」) ·
> [Eric Lippert — Closing over the loop variable considered harmful](https://ericlippert.com/2009/11/12/closing-over-the-loop-variable-considered-harmful-part-one/)(열어서 확인, 머리의 UPDATE: 「**C# 5 에서 `foreach` 의 반복 변수는 논리적으로 루프 안**에 있게 되어 클로저가 **매번 새 변수**를 닫는다. **`for` 루프는 바뀌지 않는다**」) ·
> [Learn — C# 버전 이력](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-version-history)(열어서 확인: 3.0 「Lambda expressions」 · 9 「**`static` anonymous functions**」).
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트·GC 결과는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. **대비는 실측이다** — **javac 21.0.5** 로 캡처 규칙 한 쌍 + 우회 하나를 던졌다((7)).
> **버전** — 람다 **C# 3**(익명 메서드 C# 2) · `foreach` 캡처 의미 **C# 5** · `static` 람다 **C# 9**(★ `-langversion:8` 에서 `CS8400 … 9.0 or greater` 를 받았다 · (2)).\
> ★★★ **`foreach` 의 C# 5 변화는 `-langversion` 으로 되살아나지 않는다** — `-langversion:3`·`4` 로 던져도 **`0 1 2`** 다((3)). 판 격자로 보일 수 없어 **손으로 옛 풀이를 적은 판**(`hand`)으로 쪼개 보였다.
> **경계** — ★★★ **람다라는 개념**(이름 없는 함수 · 파이썬 `lambda`)은 [`variables-and-memory/`](../../../../variables-and-memory/) §9 「람다 함수」 가 정본이다 — **그 절에는 캡처가 없다.** 여기는 **C# 의 캡처 의미론**만 쓴다.\
> ★ **델리게이트 값 자체**(봉인 클래스 · 메서드 그룹 캐시)는 [27번](../27-delegates-and-func-action/) · **이벤트 구독 누수**는 목록의 **29번 주제**.\
> ★★★ **반복 변수 캡처의 교차 갈래 대비는 인용한다** — [Go 13번](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/) (2)(`//go:build go1.21` 로 **한 빌드에서 `3 3 3` 대 `0 1 2`**) · [JS 05번](../../../js/syntax/05-var-let-const-and-tdz/) (4)(`var` `[3,3,3]` 대 `let` `[0,1,2]`) · [Python 22번](../../../python/syntax/22-closures-and-late-binding/)(늦은 바인딩 `[2, 2, 2]`).
> ★★★ **본체 창은 ① IL 덤프와 ③ 리플렉션이다** — 「변수가 **필드가 된다**」는 **컴파일러가 만든 클래스를 열어 봐야** 보인다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 진단 **순서**(배너에 `sort`) · IL **오프셋 폭** | ★★★ **진단 코드**(`CS8820`·`CS8821`·`CS8400`) · **옵코드**(`newobj <>c__DisplayClass…` · `stfld`/`ldfld` · `ldsfld <>c::<>9`) |
> | ★ 컴파일러가 지은 **이름의 숫자**(`DisplayClass0_0` · `<>9__1_0`) — Roslyn 구현 | ★★★ 이름의 **모양**(`<>c__DisplayClass` · `<>c`) · **필드가 생겼나** · `sealed` |
> | GC 가 **언제** 도나 | ★★★ **「회수됐나」 참/거짓** · **「네 판에서 갈린 줄 N / M」** · **「판에 따라 갈린 칸 N / M」** |
> | 증분의 절댓값 일부(규칙 24) | ★★ 할당 바이트의 **0 대 비(非)0** |

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
| **언어 명세(ECMA-334)** | ★★★ **C# 언어가 약속한 것** | ★★★ **람다는 값이 아니라 변수를 캡처한다** — 나중에 고친 값이 보이고, 람다 안에서 고치면 바깥이 본다 · **`foreach` 변수는 반복마다 새 변수(C# 5)** · **`for` 변수는 하나** · `static` 람다는 캡처 금지 |
| **런타임(CLI · GC)** | 실행 엔진 | ★★ 캡처된 변수는 **도달 가능한 동안** 회수되지 않는다(Learn) — 델리게이트가 **디스플레이 객체를 붙들기** 때문 |
| **컴파일러 구현(Roslyn)** | ★★★ 그것을 **어떻게 적나** | ★★★ 캡처된 지역 변수 → **`<>c__DisplayClass` 의 필드** · 람다 → **그 클래스의 인스턴스 메서드** · 캡처 없는 람다 → **`<>c` 싱글턴 + 캐시 필드** · ★★★ **한 범위의 람다들이 디스플레이 객체 하나를 나눠 쓴다** |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 할당 바이트 · GC 결과 · 진단 문구 |

★★★ **이 주제의 층 구분이 가장 중요하다 —**\
**「변수를 캡처한다(값이 아니라)」는 명세**다. **디스플레이 클래스의 이름·모양·「한 범위에 하나」는 Roslyn 구현**이다 — 그리고 (5)의 **「형제 람다가 큰 객체를 붙든다」 누수는 명세가 아니라 그 구현의 귀결**이다.

## 한눈에 — 쉽게 말하면

**람다가 바깥 변수를 쓰면, 그 변수는 「방」에서 「사물함」으로 이사 간다 — 람다는 사물함 열쇠를 들고 다닌다.**

- **방(스택의 지역 변수)** — 메서드가 끝나면 비워진다.
- **사물함(디스플레이 객체 · 힙)** — 람다가 캡처한 변수는 처음부터 **사물함에 산다.** 메서드도 람다도 **같은 사물함 칸**을 본다 — 그래서 **나중에 고친 값이 람다에 보인다.**
- **열쇠(델리게이트의 `Target`)** — 람다를 누가 붙들고 있는 한 **사물함이 안 치워진다**(수명이 늘어난다).
- **한 방의 사물함은 하나** — 같은 범위의 람다 둘이 **서로 다른 변수**를 캡처해도 **같은 사물함**에 넣는다. 작은 것만 쓰는 람다가 **큰 것까지 붙들고** 다닌다.
- **`for` 는 사물함 하나 · `foreach` 는 반복마다 새 사물함** — 그래서 `for` 로 만든 람다 셋은 **같은 `i`**(마지막 값 3)를 본다.
- **`static` 람다** — 「나는 **사물함 열쇠를 안 받겠다**」는 선언. 캡처하면 **컴파일 에러**다.

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 사물함으로 이사 | ★★★ **`newobj <>c__DisplayClass0_0` · `stfld …::n`** — 지역 변수 `n` 이 **필드**가 됐다 | (1) |
| 같은 칸을 본다 | ★★★ `n = 20` 뒤 람다가 **`20`** · 람다 안 `count += 100` 이 바깥 `count` 를 **`102`** 로 | (1)(6) |
| 열쇠가 있는 한 | ★★★ 람다를 정적 필드에 두면 캡처된 10MB 가 **회수 안 됨(`False`)** · 비우면 **`True`** | (5) |
| 한 방에 사물함 하나 | ★★★ **`small` 만 쓰는 람다를 붙들어도 `big` 이 회수 안 됨** | (5) |
| `for` 는 하나 · `foreach` 는 새로 | ★★★ **`for` `3 3 3` · `foreach` `0 1 2` · 옛 풀이 `2 2 2`** — 판 넷에서 같다 | (3)(4) |
| 열쇠를 안 받겠다 | ★★★ **`CS8820`**(지역) · **`CS8821`**(`this`) · 상수·정적 필드는 통과 | (2) |

★★★ **이 주제의 본체 그림 — 캡처가 만드는 것.**

```text
   소스                                     Roslyn 이 만든 것
   ──────────────────────────────           ─────────────────────────────────────────────────────
   static Func<int> Capture() {             sealed class <>c__DisplayClass0_0 {      ← 사물함(힙)
       int n = 10;                              public int n;                         ← 지역 변수가 필드로
       Func<int> f = () => n;                   int <Capture>b__0() => this.n;        ← 람다 = 인스턴스 메서드
       n = 20;                              }
       return f;                            Capture():
   }                                            d = newobj <>c__DisplayClass0_0       ← 메서드 첫머리에
                                                d.n = 10                               (stfld)
                                                f = new Func<int>(d, &<Capture>b__0)  ← Target = d
                                                d.n = 20                               (stfld — 같은 칸)
                                                return f                     → f() == 20

   static Func<int,int> NoCapture() => x => x + 1;
                                            sealed class <>c {                        ← 캡처 없음 = 싱글턴
                                                static <>c <>9;                       ← 그 하나
                                                static Func<int,int> <>9__1_0;        ← 델리게이트 캐시
                                                int <NoCapture>b__1_0(int x) => x+1;
                                            }

   ★★★ 캡처하면 「변수」가 객체의 필드가 되고 람다는 그 객체의 메서드가 된다 — 값 복사가 아니다.
       static x => x + 1 도 <>c 에 똑같이 생긴다((1) — IL 이 한 글자도 같다).
```

## 이 주제가 답하려는 질문

1. **캡처하면 무엇이 생기나** — 디스플레이 클래스 · `<>c` · `static` 람다의 IL((1)).
2. **`static` 람다는 무엇을 막고 무엇을 안 막나**((2)).
3. **`for` 와 `foreach` 의 반복 변수는 몇 개인가** — 판을 바꾸면((3)(4)).
4. **캡처는 수명을 얼마나 늘리나** — 형제 람다까지((5)).
5. **변수를 캡처한다는 것은 무엇이 보인다는 뜻인가 · Java 는**((6)(7)) · **할당은**((8)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ① IL 덤프와 ③ 리플렉션이다** — 캡처는 **소스에 안 보이는 클래스**를 만든다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 덤프** | ★★★ `newobj <>c__DisplayClass` · `stfld`/`ldfld` · `<>c::<>9` 캐시 · **`for` 는 루프 밖에서, `foreach` 는 루프 안에서 `newobj`** | (1)(4) |
| ★★★ **③ 리플렉션** | ★★★ 컴파일러가 만든 **중첩 타입의 필드·메서드** · `static` 람다와 일반 람다가 **같은 곳에** 생기는 것 | (1) |
| ★★★ **GC 창(`WeakReference`)** | ★★★ **제5의 상태** — 「수명이 늘었나」는 할당 바이트로 못 묻는다. **「회수됐나」 참/거짓**으로 물었다(2×2 판 격자 + `GC.Collect`). ★ 이 창이 못 보는 것 — **언제 회수되나**(시점) · 메모리 양 | (5) |
| ★★ **② 진단 격자** | ★★ `CS8820`·`CS8821` · `CS8400`(C# 8) · 반복 변수 **판 격자**(C# 3·4·5·latest) · javac `effectively final` | (2)(3)(7) |
| ★★ **④ 할당 바이트** | ★★ 캡처 람다 **64024** 대 캡처 없음·`static` **0** — 2×2 | (8) |
| **부적용인 창** | 없다 — 다섯 창을 다 썼다 | — |

### (1) ★★★ 본체 — 캡처가 무엇이 되나

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

- ★★★ **`[0]` `Capture()()` 가 `20`** — 람다를 **만든 뒤** `n = 20` 을 했는데 람다가 **20 을 본다.** 캡처한 것은 **값 `10` 이 아니라 변수 `n`** 이다.
- ★★★ **`Capture` 의 IL 첫 명령이 `newobj Probe+<>c__DisplayClass0_0::.ctor`** — 지역 변수 `n` 이 **힙 객체의 필드**가 되고, `n = 10` 과 `n = 20` 이 **둘 다 `stfld …::n`** 이다. 람다는 **`ldftn <>c__DisplayClass0_0::<Capture>b__0`** + **대상 `ldloc.0`(그 객체)** 로 만든 델리게이트다.
- ★★★ **디스플레이 클래스의 몸통** — **`필드 Int32 n` 하나 · 메서드 `<Capture>b__0`**, 그 IL 은 **`ldarg.0` · `ldfld …::n`** — 「내 객체의 `n` 필드를 읽는다」.
- ★★★ **캡처 없는 `NoCapture` 는 `ldsfld <>c::<>9__1_0` → 비었으면 `<>c::<>9`(싱글턴)를 대상으로 `newobj` → `stsfld`** — **한 번 만들어 재사용**한다([27번](../27-delegates-and-func-action/) (5)).
- ★★★ **`static` 람다 `StaticLambda` 의 IL 은 `NoCapture` 와 이름(`__2_0`)만 다르고 한 글자도 같다** — 몸통도 둘 다 `ldarg.1` · `ldc.i4.1` · `add` · `ret`. **`static` 은 코드 생성을 바꾸지 않는다** — 캡처를 **컴파일 시점에 금지**할 뿐이다((2)).
- ★★ **람다 몸통은 `<>c` 의 인스턴스 메서드**(`ldarg.1` 이 `x` — `ldarg.0` 은 `<>c` 자신)다. `static` 을 적어도 **정적 메서드가 되지 않는다** — Roslyn 의 선택이다(이유는 **이 판에서 안 쟀다**).

### (2) ★★ `static` 람다가 막는 것 · 안 막는 것 · 판 경계

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

- ★★★ **지역 변수 `local` → `CS8820`**(「static 익명 함수는 `'local'` 을 참조할 수 없다」) · **`field`·`this.field` → `CS8821`**(「`'this'` 나 `'base'` 를」) — 인스턴스 필드도 **`this` 를 거치므로** 같은 코드다.
- ★★★ **`K + S`(상수 · 정적 필드)와 `x * K` 는 진단이 없다** — Learn: 「정적 멤버와 상수는 참조할 수 있다」. **캡처가 필요 없는 것**만 허락된다.
- ★★ **`-langversion:8` 은 `static` 다섯 자리에 `CS8400 … 9.0 or greater`** — `static` 람다는 **C# 9** 다. ★ 8 판에서도 `CS8820`·`CS8821` 이 **같이** 나왔다 — 판 에러와 캡처 에러는 **따로** 매겨진다.

### (3) ★★★ 반복 변수 캡처 — `for` 대 `foreach` × 판 넷 · 그리고 옛 풀이

**언제 쓰나** — 「루프 안에서 만든 람다 셋을 나중에 부르면 무엇이 나오나」.

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

- ★★★ **`for` `3 3 3` · `foreach` `0 1 2` · `hand` `2 2 2`** — `for` 의 `i` 는 **루프 전체에 하나**라 세 람다가 **루프가 끝난 뒤의 `i`(3)** 를 본다. `foreach` 의 `j` 는 **반복마다 새 변수**다.
- ★★★ **판에 따라 갈린 칸 0 / 3** — **C# 3·4 로 던져도 `foreach` 가 `0 1 2`** 다. **Roslyn 은 C# 5 의 `foreach` 변화를 `-langversion` 에 묶지 않았다** — 옛 동작을 판 격자로 되살릴 수 없다.
- ★★★ **그 0 이 진짜인가**(규칙 22) — 같은 블록 끝의 **대조군**이 `-langversion:3` 에서 문자열 보간을 **`CS8024 … C# 3`** 으로 막았다. **판 플래그는 살아 있다** — 안 갈린 것은 `foreach` 의 의미가 **판을 안 타기** 때문이다.
- ★★★ **`hand` — C# 4 까지의 `foreach` 풀이를 손으로 적은 판** — 변수 `k` 를 **`while` 밖에** 선언하고 `k = e.Current` 를 반복한다. 결과는 **`2 2 2`** — **마지막 원소**다. `for` 의 `3 3 3`(**루프가 끝난 뒤의 증가 값**)과 **숫자가 다르다.** 옛 `foreach` 함정은 **「3 3 3」이 아니라 「2 2 2」** 였다.

```text
   변수가 몇 개인가 — 람다 셋이 보는 칸

   for (int i = 0; i < 3; i++)            [ i ] ← 하나. 세 람다가 공유. 끝나면 i = 3        → 3 3 3
   foreach (int j in {0,1,2})  (C# 5+)    [ j ][ j ][ j ] ← 반복마다 새로                  → 0 1 2
   int k; while (MoveNext()) k = Current  [ k ] ← 하나. 마지막 대입은 Current = 2            → 2 2 2
     (C# 4 까지의 foreach 풀이)

   ★ 교차 갈래 —  Go 1.21 for      [3 3 3] → Go 1.22+  [0 1 2]   (Go 13편 — 언어 판 한 줄로 한 빌드 안에서)
                  JS  for (var)    [3,3,3] · for (let) [0,1,2]   (JS 05편 (4))
                  Python for      [2, 2, 2]  (늦은 바인딩 — 이름 하나를 부를 때 푼다 · Python 22편)
     ★★★ C# 의 for 는 JS var · Go 1.21 쪽, C# 의 foreach 는 JS let · Go 1.22 쪽, 옛 foreach 는 Python 쪽 숫자다.
         Go 는 판 한 줄로 두 의미를 나란히 냈지만 C# 은 판 플래그로 옛 의미를 못 부른다 — 차이가 거기다.
```

### (4) ★★ IL — 디스플레이 객체를 어디서 만드나

```text
===== 소스: cs28b-loopil.cs =====
using System;
using System.Collections.Generic;
public static class L {
    public static void For(List<Func<int>> a) { for (int i = 0; i < 3; i++) a.Add(() => i); }
    public static void Foreach(List<Func<int>> b, int[] xs) { foreach (int j in xs) b.Add(() => j); }
}
class Program {
    static void Main() { Il.Dump(typeof(L), "For"); Il.Dump(typeof(L), "Foreach"); }
}
===== csc -optimize -r:il.dll -out:exo.dll cs28b-loopil.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- L.For ---
  .locals [0] L+<>c__DisplayClass0_0
  .locals [1] System.Int32
  IL_0000: newobj L+<>c__DisplayClass0_0::.ctor
  IL_0005: stloc.0
  IL_0006: ldloc.0
  IL_0007: ldc.i4.0
  IL_0008: stfld L+<>c__DisplayClass0_0::i
  IL_000d: br.s IL_0031
  IL_000f: ldarg.0
  IL_0010: ldloc.0
  IL_0011: ldftn L+<>c__DisplayClass0_0::<For>b__0
  IL_0017: newobj System.Func<System.Int32>::.ctor
  IL_001c: callvirt System.Collections.Generic.List<System.Func<System.Int32>>::Add
  IL_0021: ldloc.0
  IL_0022: ldfld L+<>c__DisplayClass0_0::i
  IL_0027: stloc.1
  IL_0028: ldloc.0
  IL_0029: ldloc.1
  IL_002a: ldc.i4.1
  IL_002b: add
  IL_002c: stfld L+<>c__DisplayClass0_0::i
  IL_0031: ldloc.0
  IL_0032: ldfld L+<>c__DisplayClass0_0::i
  IL_0037: ldc.i4.3
  IL_0038: blt.s IL_000f
  IL_003a: ret
--- L.Foreach ---
  .locals [0] System.Int32[]
  .locals [1] System.Int32
  .locals [2] L+<>c__DisplayClass1_0
  IL_0000: ldarg.1
  IL_0001: stloc.0
  IL_0002: ldc.i4.0
  IL_0003: stloc.1
  IL_0004: br.s IL_002b
  IL_0006: newobj L+<>c__DisplayClass1_0::.ctor
  IL_000b: stloc.2
  IL_000c: ldloc.2
  IL_000d: ldloc.0
  IL_000e: ldloc.1
  IL_000f: ldelem.i4
  IL_0010: stfld L+<>c__DisplayClass1_0::j
  IL_0015: ldarg.0
  IL_0016: ldloc.2
  IL_0017: ldftn L+<>c__DisplayClass1_0::<Foreach>b__0
  IL_001d: newobj System.Func<System.Int32>::.ctor
  IL_0022: callvirt System.Collections.Generic.List<System.Func<System.Int32>>::Add
  IL_0027: ldloc.1
  IL_0028: ldc.i4.1
  IL_0029: add
  IL_002a: stloc.1
  IL_002b: ldloc.1
  IL_002c: ldloc.0
  IL_002d: ldlen
  IL_002e: conv.i4
  IL_002f: blt.s IL_0006
  IL_0031: ret
```

- ★★★ **`For` 는 `newobj <>c__DisplayClass0_0` 가 `IL_0000` — 루프 앞에서 한 번**이고, 루프 변수 `i` 가 **그 객체의 필드**(`ldfld`/`stfld …::i`)로 증가·비교된다. 세 람다가 **같은 객체**를 대상으로 받는다.
- ★★★ **`Foreach` 는 `newobj <>c__DisplayClass1_0` 가 `IL_0006` — 루프 몸통 안**(`blt.s IL_0006` 이 되돌아오는 자리)이다. 반복마다 **새 객체**에 `j` 를 넣는다.
- ★★ **(3)의 `3 3 3` 대 `0 1 2` 가 `newobj` 한 줄의 위치로 설명된다.**

### (5) ★★★ 캡처가 수명을 늘린다 — `WeakReference` 로 「회수됐나」

**언제 쓰나** — 「람다를 오래 들고 있으면 무엇이 안 풀리나」.

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

- ★★★ **네 판에서 갈린 줄 0 / 5 · 첫 판에서 「회수됨(True)」 줄 3 / 5** — `csc` 기본/`-optimize` × 티어링 기본/`TC=0` 에서 같다.
- ★★★ **`[1]` 람다를 정적 필드에 둔 채 → `False`**(10MB `big` 이 안 풀린다) · **`[2]` 필드를 비우면 `True`** · **`[3]` 어디에도 안 두면 `True`** — 캡처된 변수의 수명은 **델리게이트의 수명**이다(Learn).
- ★★★ **`[4]` `small` 만 쓰는 람다(`usesSmall`)를 붙들었는데 `big` 이 `False`** — 같은 범위의 두 람다가 **디스플레이 객체 하나**를 나눠 쓰므로, `usesSmall` 의 `Target` 이 **`big` 필드까지 든 객체**다. **`[5]` 비우면 `True`.**
- ★★ **「GC 가 언제 도나」는 안 봤다** — 매번 `GC.Collect()` 를 두 번 불러 **「이 시점에 도달 가능한가」** 만 물었다.

```text
   MakeSibling() 의 사물함 — 한 범위 = 디스플레이 객체 하나

   ┌ <>c__DisplayClass ─────────┐
   │  byte[] big   (10 MB)      │ ◀── usesBig   (지역 — 메서드가 끝나면 사라짐)
   │  int    small              │ ◀── usesSmall ── keep (정적 필드) ── 여기서 붙든다
   └────────────────────────────┘
   ★★★ usesSmall 은 small 만 읽지만 Target 은 「사물함 전체」 — big 도 같이 산다([4] False).
       이것은 명세가 아니라 Roslyn 이 「범위마다 하나」 로 만든 결과다.
```

### (6) ★★★ 캡처한 변수를 고치면 — 양쪽이 본다

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

- ★★★ **`[2]` `count = 2` 뒤 `read()` 가 `2`** — 바깥에서 고친 것을 람다가 본다.
- ★★★ **`[3]` `bump()`(람다 안에서 `count += 100`) 뒤 바깥 `count` 가 `102`, `read()` 도 `102`** — **세 곳(메서드·`read`·`bump`)이 같은 필드 하나**를 본다. Learn 예제의 「**다른 람다가 캡처된 변수의 새 값을 본다: True**」와 같은 모양이다.

### (7) ★★★ Java 짝 — 「사실상 final」만 캡처한다

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

- ★★★ **캡처한 뒤 바깥에서 고치면(`G28a`) · 람다 안에서 고치면(`G28b`) 둘 다 javac `local variables referenced from a lambda expression must be final or effectively final`** — C# (6)의 두 줄이 **Java 에서는 둘 다 컴파일 에러**다.
- ★★★ **이유가 설계에 있다** — Java 는 캡처할 때 **값을 복사**하므로(변수 자체를 옮기지 않는다) 바꿀 수 있으면 **둘이 갈라진다** — 그래서 **바꾸지 못하게** 막았다([Java 29번](../../../java/syntax/29-lambda-expressions/) — 같은 에러를 먼저 실측했다). **C# 은 변수를 힙으로 옮겨** 갈라질 일을 없앴다.
- ★★ **Java 의 우회는 「상자 하나」** — `int[] count = { 1 }` 을 캡처하면 **배열 참조는 final 이고 칸은 바꿀 수 있어** `count[0] = 2` 뒤 `read()` 가 `2`. **C# 디스플레이 클래스를 손으로 만든 것**과 같다.

```text
                         캡처하는 것          바깥에서 고치면              람다 안에서 고치면
   C#                    변수(→ 힙의 필드)     람다가 새 값을 본다 (2)       바깥이 새 값을 본다 (102)
   Java                  값(복사)             ✕ effectively final 에러      ✕ effectively final 에러
   Java 우회 int[]        배열 참조(값)         칸을 고치면 보인다 (2)         —
```

### (8) ★★ 할당 바이트 — 캡처 · 캡처 없음 · `static` 람다

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

- ★★★ **네 판에서 갈린 줄 0 / 3** — **캡처하는 람다 64024 · 캡처 없는 람다 0 · `static` 람다 0**.
- ★★★ **`static` 람다와 캡처 없는 람다는 같다(둘 다 0)** — (1)의 IL 이 같으니 당연한 결과다. **「`static` 람다가 더 빠르다·더 적게 할당한다」는 이 판에서 근거가 없다** — `static` 은 **실수로 캡처하는 것을 막는 컴파일 검사**다.
- ★★★ **64024 = 64 × 1000 + 24** — 델리게이트 1000개(한 개 64바이트 — [27번](../27-delegates-and-func-action/) (6)) + **디스플레이 객체 하나**(24바이트). 캡처된 `i` 가 **`for` 변수라 루프 전체에 객체 하나**다((3)(4)) — 반복마다 새로 생기는 것은 **델리게이트뿐**이다.
- ★ **시간은 안 쟀다.**

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs28b-form.cs =====
using System;
using System.Collections.Generic;

Func<int, int> MakeAdder(int step) => x => x + step;
var add5 = MakeAdder(5);
int calls = 0;
Func<int, int> counted = x => { calls++; return x * 2; };
var list = new List<int> { 3, 1, 2 };
list.Sort(static (a, b) => a.CompareTo(b));
Console.WriteLine($"{add5(10)} · {counted(1)}{counted(2)} · calls={calls} · {string.Join(",", list)}");
===== csc -out:ex.dll cs28b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
15 · 24 · calls=2 · 1,2,3
```

- ★★★ **`MakeAdder(5)` 가 돌려준 람다가 `step` 을 들고 있다** — 메서드가 끝난 뒤에도 `add5(10)` 이 `15`(캡처 = 수명 연장).
- ★★ **`counted` 가 바깥 `calls` 를 두 번 올려 `calls=2`** — 람다 안의 대입이 바깥 변수에 닿는다.
- ★★ **`list.Sort(static (a, b) => a.CompareTo(b))`** — 아무것도 캡처하지 않는다는 **의도를 컴파일러가 검사**하게 한다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `static` 람다가 지역 변수를 읽음 | `CS8820` | (2) |
| `static` 람다가 인스턴스 필드·`this` 를 읽음 | `CS8821` | (2) |
| C# 8 이하에서 `static` 람다 | `CS8400` | (2) |
| Java 에서 캡처 뒤 대입 · 람다 안 대입 | javac `effectively final` | (7) |
| ★★★ `for` 변수를 캡처한 람다를 나중에 부름 | ★★★ **진단 없음** — `3 3 3` | (3) |

## 어디서 틀리나

1. ★★★ **「람다는 만들 때의 값을 기억한다」** — **변수를 캡처**한다. 나중에 고친 값이 보인다((1) `[0]` · (6)).
2. ★★★ **「`for` 도 C# 5 에서 고쳐졌다」** — **`foreach` 만**이다. `for` 는 지금도 `3 3 3`((3)).
3. ★★★ **「`-langversion:4` 로 옛 `foreach` 를 재현할 수 있다」** — **안 된다**(판 넷 모두 `0 1 2`). 옛 함정의 숫자는 **`2 2 2`**((3)).
4. ★★★ **「작은 것만 쓰는 람다는 작은 것만 붙든다」** — **같은 범위의 디스플레이 객체 전체**를 붙든다((5) `[4]`).
5. ★★★ **「`static` 람다가 더 빠르다」** — IL 이 **같고** 할당도 **같다**((1)(8)). 잰 적 없는 성능을 믿지 마라.
6. ★★ **「`static` 람다는 정적 멤버도 못 쓴다」** — **상수·정적 필드는 된다**((2)).
7. ★★ **「캡처 없는 람다도 부를 때마다 할당한다」** — **`<>c` 에 캐시**된다 — 0((1)(8)).
8. ★★ **「Java 처럼 C# 도 바꾼 변수는 캡처 못 한다」** — C# 은 **된다**. 에러는 Java 쪽이다((7)).
9. ★ **「디스플레이 클래스 이름은 믿고 써도 된다」** — `<>c__DisplayClass0_0` 의 **숫자와 모양은 Roslyn 구현**이다.

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **값이 아니라 변수를 캡처 · 양방향으로 보인다** | ★★★ **언어(334)** | (1)(6) |
| **`foreach` 변수는 반복마다 새 변수 · `for` 는 하나** | ★★★ **언어(C# 5)** | (3) |
| **`static` 람다의 캡처 금지 · 상수/정적 허용** | ★★★ **언어(C# 9)** | (2) |
| **캡처된 변수는 델리게이트가 도달 가능한 동안 산다** | ★★ **언어 + GC**(Learn) | (5) |
| **디스플레이 클래스 · 필드 · `<>c` 싱글턴과 캐시** | ★★★ **Roslyn 구현** | (1)(4) |
| **한 범위의 람다가 디스플레이 객체 하나를 공유 → 형제 누수** | ★★★ **Roslyn 구현의 귀결** | (5) |
| **`foreach` 의미가 `-langversion` 에 안 묶임** | ★★ **Roslyn 의 선택** | (3) |
| **할당 바이트 값** | ★ **이 판의 관찰** | (8) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **루프 안에서 람다를 만들면 `for` 변수를 직접 캡처하지 마라** — 몸통에 `int k = i;` 를 두면 **반복마다 새 변수**다(`foreach` 와 같은 모양이 된다)((3)(4)).
- ★★★ **오래 사는 델리게이트(이벤트·캐시·정적 필드)에 넣는 람다는 같은 범위에서 큰 객체를 캡처하는 람다와 떼어 놓아라** — 형제 누수((5)). 필요한 값만 **별도 메서드의 매개변수로** 넘겨 범위를 가르면 된다.
- ★★ **캡처할 생각이 없는 람다에는 `static` 을 붙여라** — 성능이 아니라 **실수를 컴파일 에러로 바꾸는 것**이 이득이다((2)(8)).
- ★★ **캡처한 변수를 양쪽에서 고치는 코드는 읽기 어렵다** — 되는 것과 권할 것은 다르다((6)).
- ★ **뜨거운 경로에서는 캡처 람다가 호출마다 델리게이트를 할당한다는 것을 기억해라**((8) `[1]`).

## 핵심 문장

1. ★★★ **람다는 값이 아니라 변수를 캡처한다** — Roslyn 은 그 변수를 **`<>c__DisplayClass` 의 필드**로 옮기고 람다를 그 클래스의 메서드로 만든다((1)).
2. ★★★ **`for` 는 변수 하나(`3 3 3`), `foreach` 는 반복마다 새 변수(`0 1 2`)** — `newobj` 가 루프 **밖**이냐 **안**이냐다((3)(4)). **판 플래그로 옛 `foreach`(`2 2 2`)는 안 돌아온다.**
3. ★★★ **캡처는 수명을 늘린다 — 형제 람다가 캡처한 큰 객체까지** 붙든다(`WeakReference` 네 판 같음)((5)).
4. ★★★ **`static` 람다는 캡처를 에러(`CS8820`·`CS8821`)로 막을 뿐, IL 과 할당은 캡처 없는 람다와 같다**((1)(2)(8)).
5. ★★ **Java 는 사실상 final 만 캡처한다** — C# 에서 되는 두 줄이 javac 에러다((7)).

## 관련 자료

- [`variables-and-memory/`](../../../../variables-and-memory/) §9 「람다 함수」 — **경계**: 이름 없는 함수라는 **개념**(파이썬 `lambda`·정렬 키)은 거기. **캡처는 거기에 없다** — C# 의 캡처 의미론은 여기.
- [27번 — 델리게이트](../27-delegates-and-func-action/) — **경계**: 델리게이트 값 · 메서드 그룹 캐시는 거기. `<>c` 캐시는 두 편이 같이 본다.
- 목록의 **29번 주제**(`event`) — 구독 해제 누락 누수는 (5)의 수명 연장이 **이벤트에서** 나타난 것.
- 목록의 **32번 주제**(`yield`) — 반복자도 지역 변수를 **필드로 옮기는** 같은 수법(상태 기계).
- Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **13번**([`13-closures-variable-capture-and-loop-variable-change/`](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/)) — 루프 변수 의미가 **Go 1.22 에서 바뀐** 것.
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **05번**([`05-var-let-const-and-tdz/`](../../../js/syntax/05-var-let-const-and-tdz/)) · **06번**([`06-scope-and-closures/`](../../../js/syntax/06-scope-and-closures/)) — `var` 대 `let`.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **22번**([`22-closures-and-late-binding/`](../../../python/syntax/22-closures-and-late-binding/)) — 늦은 바인딩.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **29번**([`29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/)) — `effectively final` 과 `invokedynamic`.

## 용어 풀이

- **클로저(closure)** — 바깥 변수를 캡처한 함수 값.
- **캡처(capture)** — 람다가 자기 밖의 지역 변수·매개변수·`this` 를 쓰는 것. C# 은 **변수 자체**를 공유한다.
- **디스플레이 클래스(display class)** — Roslyn 이 캡처된 변수를 필드로 담으려고 만드는 숨은 봉인 클래스(`<>c__DisplayClass…`). **구현 용어**다.
- **`<>c`** — 캡처 없는 람다를 담는 숨은 싱글턴 클래스. `<>9` 가 그 인스턴스, `<>9__…` 가 델리게이트 캐시.
- **`static` 람다** — 캡처를 금지하는 한정자(C# 9). 코드 생성은 바꾸지 않는다(이 판).
- **사실상 final(effectively final)** — Java 에서 선언 뒤 한 번도 다시 대입하지 않는 지역 변수. 람다가 캡처할 수 있는 유일한 지역 변수다.
- **`WeakReference`** — 대상을 붙들지 않는 참조. `IsAlive` 로 「회수됐나」를 물을 수 있다.
- **늦은 바인딩(late binding)** — 이름을 **부를 때** 값으로 푸는 것(파이썬의 클로저).

## 더 들어가면

- ★ **로컬 함수의 캡처** — 델리게이트로 안 바꾸면 **구조체 디스플레이**로 할당 없이 캡처한다고 알려져 있다. **이 판에서 안 던졌다.**
- ★ **`this` 만 캡처하는 람다** — 디스플레이 클래스 없이 **메서드가 그 클래스의 인스턴스 메서드**가 된다고 알려져 있다 — **안 찍었다.**
- ★ **범위가 여럿인 캡처**(바깥 블록 변수 + 안쪽 블록 변수) — 디스플레이 객체가 **사슬**로 이어진다. **안 찍었다.**
