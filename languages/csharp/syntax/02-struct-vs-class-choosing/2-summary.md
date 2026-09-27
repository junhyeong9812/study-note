# csharp/syntax/02 — `struct` 대 `class` 고르기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/value-types) · [Learn — 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/reference-types) · [.NET API — `GC.GetAllocatedBytesForCurrentThread`](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-24).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> ★★★ **진단 언어를 영어로 고정했다.** 안 그러면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 실측으로 받은 한국어 판이 ``error CS0029: 암시적으로 'string' 형식을 'int' 형식으로 변환할 수 없습니다.`` 였다.\
> 고정하는 법은 둘을 같이 거는 것이다 — 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`**.
> **던진 형태** — MSBuild(`dotnet build`·`dotnet run`)를 **안 썼다.** Roslyn 컴파일러를 **직접** 부른다 —\
> 그래야 `bin/`·`obj/` 가 안 생기고, 진단 경로가 **절대 경로가 아니라 파일명**으로 나오며, 한 판이 0.3초 안에 끝난다.\
> 배너의 `csc` 는 아래 셸 함수이고, `ex.runtimeconfig.json` 은 아래 한 줄짜리 파일이다.
>
> ```text
> export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
> export DOTNET_CLI_UI_LANGUAGE=en            # ★★★ 안 주면 진단이 한국어로 나온다
> D=$(dirname "$(readlink -f "$(command -v dotnet)")")
> ls "$D"/packs/Microsoft.NETCore.App.Ref/10.0.12/ref/net10.0/*.dll | sed 's/^/-r:/' > refs.rsp
> echo '{"runtimeOptions":{"tfm":"net10.0","framework":{"name":"Microsoft.NETCore.App","version":"10.0.0"}}}' > ex.runtimeconfig.json
> csc() { dotnet exec "$D/sdk/10.0.401/Roslyn/bincore/csc.dll" \
>           -nologo -nostdlib -noconfig @refs.rsp \
>           -preferreduilang:en-US -langversion:latest -target:exe "$@"; }
> ```
>
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.\
> 그래서 이 문서의 트레이스는 ``at Program.<Main>$(String[] args)`` 에서 끝나고, 어느 머신에서 돌려도 같다.
> **버전** — `readonly struct` 는 **C# 7.2부터** · `in` 매개변수도 **C# 7.2부터** ·\
> **구조체의 필드 초기자와 매개변수 없는 생성자는 C# 10부터** · `record struct` 도 **C# 10부터**다.\
> ★ 「구조체에 기본 생성자를 못 쓴다」는 **C# 9 까지의 이야기**다 — (4)에서 던져 확인했다.
> **경계** — 「값 타입이 무엇인가」의 정본은 [01번](../01-value-types-and-reference-types/)이다.\
> 여기는 **그래서 무엇을 고르나** — 크기·불변성·복사 비용·동등성이다.\
> **박싱**은 [03번](../03-boxing-and-unboxing/)이 정본이고, `record` 의 문법 전반은 목록의 **18번 주제**,\
> `Equals`/`GetHashCode` 계약은 목록의 **19번 주제**, `ref struct`·`Span<T>` 는 목록의 **45**·**46번 주제**다.\
> *「값 타입이 JVM 보다 20년 앞섰다」는 **논증**은* [`../../c-cpp-csharp.md`](../../../c-cpp-csharp.md) *에 있다 — 여기는 **선택 기준**이다.*\
> Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **05번**이 **같은 집안의 질문**이다 —\
> 거기도 「**값이냐 헤더냐**」가 축이고, 「대입이 무엇을 복사하나」로 갈린다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **`GC.GetAllocatedBytesForCurrentThread()` 의 절댓값**(프로세스 시작부터의 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | `Stopwatch` 로 잰 **ns 수치** · 그때의 CPU 상태 | **자릿수 차이**(10배·40배 같은 비율) |
> | `GetHashCode()` 값 · 객체 주소 | **진단 코드**(`CS0029` 류) · **진단 문구** · **`(행,열)`** |
> | 빌드 시간 · `dotnet` 패치 버전이 오르면 달라질 수 있는 것 | **`cc exit` 와 `run exit`**(갈라 적었다) |
> | — | **IL 명령어 열**(`box` · `unbox.any` · `ldobj` · `initobj` · `newobj`) |

## 한눈에 — 쉽게 말하면

**`class` 는 「사물함」이고 `struct` 는 「쪽지」다.** 그런데 **쪽지에는 조용한 대가가 둘** 있다.

쪽지를 고르는 이유는 **사물함을 안 빌려도 되는 것**([01번](../01-value-types-and-reference-types/)의 (5))인데,\
그 대신 **쓸 때마다 베껴진다.** 문제는 **그 베끼기가 눈에 안 보이는 자리**가 있다는 것이다.

| 비유 | 실체 |
|---|---|
| **사물함** | `class` — 동일성이 있고, 상속되고, 널이 된다 |
| **쪽지** | `struct` — 값이고, 복사되고, 힙을 안 쓴다 |
| ★ **「이 쪽지는 안 고친다」고 도장 찍기** | `readonly struct`(C# 7.2) — **필드가 전부 `readonly` 여야 한다**((2)) |
| ★★★ **도장 없는 쪽지를 「안 고친다」는 서랍에 넣으면** | **볼 때마다 몰래 베껴진다** — **방어적 복사**((3)) |
| ★★★ **그 베끼기에 경고가 없다** | ★★★ **`-warn:9` 로도 0줄**((3)) |
| ★ **「값이 같으면 같다」를 공짜로 얻기** | `record struct`(C# 10)((6)) |
| ★★ **그걸 손으로 안 하면** | 기본 `Equals` 가 **박싱하고 리플렉션으로 돈다**((5)) |

- ★★★ **이 주제의 함정은 「느리다」가 아니라 「조용하다」다.**\
  `readonly` 가 아닌 구조체를 **`readonly` 필드**나 **`in` 매개변수**로 다루면\
  **호출마다 복사본이 생기고, 거기에 쓴 것은 버려진다**((3)). **에러도 경고도 없다.**
- ★★ **그래서 규칙이 하나로 줄어든다 — 구조체를 만들면 `readonly struct` 로 만든다.**\
  (3)에서 `readonly struct` 로 바꾸자 **IL 의 복사 명령이 사라졌다.**
- ★★ **`Equals` 를 안 짜면 두 번 손해**다((5)) — **박싱**(할당)과 **느린 경로**(참조 필드가 있으면 40배).\
  ★ `record struct` 나 `IEquatable<T>` 가 둘 다 없앤다.

```text
   구조체를 고르는 값과 대가

   값                                     대가
   +----------------------------+        +----------------------------------+
   | new 해도 힙 할당 0바이트     |        | 대입·전달·필드 저장마다 값 복사    |
   | 배열에 값이 통째로 들어간다   |        | 크면 복사 비용이 눈에 안 보이게 든다 |
   | GC 가 훑을 참조가 없다       |        | ★ readonly 가 아니면 방어적 복사   |
   | null 이 아니라는 게 타입에 있다|        | ★ Equals 기본 경로가 박싱 + 느림   |
   +----------------------------+        +----------------------------------+
        ↑ 01번 (5) 에서 쟀다                    ↑ (3)·(5) 에서 잰다
```

```text
   ★★★ 방어적 복사 — 세 자리에서 갈린다

   struct Counter { int N; int Next() { return ++N; } }      ← readonly 가 아니다

   지역 변수      c.Next() c.Next() c.Next()  →  1 2 3   N=3   (원본을 고친다)
   ref 매개변수   c.Next() c.Next() c.Next()  →  1 2 3   N=3   (원본을 고친다)
   ─────────────────────────────────────────────────────────────────────────
   readonly 필드  c.Next() c.Next() c.Next()  →  1 1 1   N=0   ★ 매번 새 복사본
   in 매개변수    c.Next() c.Next() c.Next()  →  1 1 1   N=0   ★ 매번 새 복사본

   그 복사가 IL 에 보인다:   ldarg.0 ; ldobj Counter ; stloc.0 ; ldloca.s 0 ; call
                                      ^^^^^^^^^^^^^^^^^^^^^^^  ← 이 두 줄이 복사다
   readonly struct 로 바꾸면:  ldarg.0 ; call        ← 사라진다
```

> **`readonly struct`** — 「이 구조체는 만들어진 뒤 안 바뀐다」를 **타입에 새기는 것**(C# 7.2).\
> **모든 인스턴스 필드가 `readonly` 여야** 한다. 예: `readonly struct Money { public readonly int Won; }`

> **방어적 복사(defensive copy)** — 컴파일러가 **읽기 전용 자리의 구조체를 지키려고 몰래 만드는 복사본**.\
> 예: `readonly Counter c;` 의 `c.Next()` 는 **복사본의 `N`** 을 올리고 끝난다 — 원본은 그대로다.

> **`record struct`** — 값 동등성·`ToString`·해체를 **컴파일러가 만들어 주는 구조체**(C# 10).\
> `readonly record struct` 로 쓰면 **불변성까지** 함께 온다.

> **`IEquatable<T>`** — 「박싱 없이 같은 타입끼리 비교하는 법」을 약속하는 인터페이스.\
> 이것이 있으면 `Equals(T)` 가 **오버로드 해소에서 먼저 뽑혀** 박싱이 안 생긴다((5)).

## 이 주제가 답하려는 질문

1. **무엇을 보고 고르나** — 크기·불변성·복사 비용·동일성 중 **무엇이 결정적인가**((1)·(7)).
2. **구조체를 고르면 무엇을 더 해야 하나** — `readonly` 와 `Equals` 를 **왜 그냥 두면 안 되나**((2)·(3)·(5)).
3. **조용히 틀리는 자리가 어디인가** — ★★★ **경고 없이 복사가 생기는 곳**을 짚을 수 있나((3)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| **실행 출력** | ★★★ **방어적 복사가 결과를 바꾼 것**(`1 1 1` 대 `1 2 3`) | (3)·(4)·(6) |
| **컴파일 진단** | `readonly` 가 막는 것 · `record struct` 가 막는 것 | (2)·(6) |
| ★★ **「진단 0줄」** | ★★★ **경고가 안 난다는 사실 자체** — `-warn:9` 로 확인했다 | (3) |
| ★★ **IL** | ★★★ **`ldobj` 가 복사를 직접 보여 준다** | (3) |
| ★★ **할당 바이트** | 기본 `Equals` 가 **박싱한다**는 것 | (5) |
| **시간(`Stopwatch`)** | ★ 기본 `Equals` 의 **자릿수 차이** — 절댓값은 안 쓴다 | (5) |

★★★ **세 번째 창(「진단 0줄」)이 이 주제 고유의 창**이다.\
「에러도 출력이다」의 **정반대 쪽** — **아무 말도 안 하는 것이 결론**인 자리라 그것을 따로 찍어 뒀다.

### (1) 크기 — 무엇이 얼마나 복사되나

**언제 쓰나** — 「이 구조체 커도 되나?」 할 때.

```text
===== 소스: cs02b-size.cs =====
using System;
using System.Runtime.CompilerServices;

Warm();

Console.WriteLine($"Unsafe.SizeOf<Small>()  = {Unsafe.SizeOf<Small>()}");
Console.WriteLine($"Unsafe.SizeOf<Big>()    = {Unsafe.SizeOf<Big>()}");
Console.WriteLine($"Unsafe.SizeOf<BigCls>() = {Unsafe.SizeOf<BigCls>()}  (참조 하나의 크기다)");

long a0 = GC.GetAllocatedBytesForCurrentThread();
var sArr = new Big[1000];
long a1 = GC.GetAllocatedBytesForCurrentThread();
var cArr = new BigCls[1000];
long a2 = GC.GetAllocatedBytesForCurrentThread();
for (int i = 0; i < 1000; i++) cArr[i] = new BigCls();
long a3 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"new Big[1000]           : +{a1 - a0} 바이트  (1000개가 이미 다 들어 있다)");
Console.WriteLine($"new BigCls[1000]        : +{a2 - a1} 바이트  (1000개의 null 이다)");
Console.WriteLine($"  거기에 1000개 채우기  : +{a3 - a2} 바이트");
Console.WriteLine($"sArr[0].A={sArr[0].A} cArr[0]!.A={cArr[0]!.A}");

static void Warm() { var _ = new BigCls[1]; var __ = new Big[1]; GC.GetAllocatedBytesForCurrentThread(); }

struct Small { public int A; public int B; }
struct Big { public long A, B, C, D, E, F, G, H; }
class BigCls { public long A, B, C, D, E, F, G, H; }
===== csc -out:ex.dll cs02b-size.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Unsafe.SizeOf<Small>()  = 8
Unsafe.SizeOf<Big>()    = 64
Unsafe.SizeOf<BigCls>() = 8  (참조 하나의 크기다)
new Big[1000]           : +64024 바이트  (1000개가 이미 다 들어 있다)
new BigCls[1000]        : +8024 바이트  (1000개의 null 이다)
  거기에 1000개 채우기  : +80000 바이트
sArr[0].A=0 cArr[0]!.A=0
```

| 물어본 것 | 값 | 읽는 법 |
|---|---|---|
| `Unsafe.SizeOf<Big>()` | **64** | `long` 여덟 |
| `Unsafe.SizeOf<BigCls>()` | ★ **8** | **참조 하나의 크기**다 — 객체 크기가 아니다 |
| `new Big[1000]` | **+64024** | ★ **1000개가 이미 다 들어 있다** |
| `new BigCls[1000]` | **+8024** | ★ **`null` 1000개**다 |
| 거기에 1000개 채우기 | **+80000** | 객체 하나가 80바이트(헤더 16 + 필드 64) |

- ★★★ **값 타입 배열은 「이미 다 들어 있고」 참조 타입 배열은 「아직 비어 있다」.**\
  총합으로 보면 `Big[1000]` 이 **64024**, `BigCls[1000]` 을 다 채우면 **88024** 다.\
  ★ 차이는 **객체 헤더 16바이트 × 1000** 과 **배열이 참조를 또 드는 8바이트 × 1000** 이다.
- ★★ **그렇다고 「크면 class」가 자동으로 참은 아니다.** 여기서 잰 것은 **할당**이지 **복사 비용**이 아니다.\
  ★ **복사 비용은 이 문서가 안 쟀다** — 그것은 「대입·전달을 몇 번 하느냐」에 달렸고,\
  **그 수치를 재려면 벤치마크 하네스가 따로 필요하다.**
- ★ 널리 도는 「16바이트 이하면 `struct`」는 **가이드라인이지 측정이 아니다.**\
  이 문서가 실측으로 말할 수 있는 것은 ①할당((1)) ②방어적 복사((3)) ③`Equals` 비용((5)) 셋이다.

### (2) `readonly struct` 가 막는 것

**언제 쓰나** — 구조체를 만들 때. **거의 항상 여기서 시작하는 게 맞다**((3) 때문이다).

```text
===== 소스: cs02b-readonly.cs =====
readonly struct A {
    public int Won;                        // ① readonly struct 에 가변 필드
    public A(int won) { Won = won; }
}

readonly struct B {
    public readonly int Won;
    public B(int won) { Won = won; }
    public void Add(int d) { Won += d; }   // ② readonly struct 의 메서드가 필드에 쓴다
}

readonly struct C {
    public readonly int Won;
    public C(int won) { Won = won; }
    public C Add(int d) => new C(Won + d); // ③ 새 값을 돌려주는 쪽은 된다
}

class Program {
    static void Main() {
        System.Console.WriteLine(new C(100).Add(1).Won);
    }
}
===== csc -out:ex.dll cs02b-readonly.cs (cc exit=1) =====
cs02b-readonly.cs(2,16): error CS8340: Instance fields of readonly structs must be readonly.
```

- ★★ **`readonly struct` 는 「모든 인스턴스 필드가 `readonly` 일 것」을 요구한다** — ``error CS8340``.\
  **타입에 도장을 찍는 것이지 선언만 바꾸는 것이 아니다.**

필드를 `readonly` 로 만들면 이번엔 메서드가 막힌다.

```text
===== 소스: cs02b-readonly-write.cs =====
readonly struct Money {
    public readonly int Won;
    public Money(int won) { Won = won; }
    public void Add(int d) { Won += d; }        // ① readonly struct 의 메서드가 필드에 쓴다
    public void Reset() { this = default; }     // ② this 에 통째로 쓴다
}

struct Mutable {
    public int Won;
    public void Add(int d) { Won += d; }        // ③ 보통 구조체는 둘 다 된다
    public void Reset() { this = default; }
}

class Program {
    static void Main() {
        var m = new Mutable(); m.Add(1); System.Console.WriteLine(m.Won);
    }
}
===== csc -out:ex.dll cs02b-readonly-write.cs (cc exit=1) =====
cs02b-readonly-write.cs(4,30): error CS0191: A readonly field cannot be assigned to (except in a constructor or init-only setter of the type in which the field is defined or a variable initializer)
cs02b-readonly-write.cs(5,27): error CS1604: Cannot assign to 'this' because it is read-only
```

| 쓴 것 | 진단 | 무엇을 말하나 |
|---|---|---|
| `readonly struct` 의 가변 필드 | ``error CS8340: Instance fields of readonly structs must be readonly.`` | 필드부터 막는다 |
| `readonly` 필드에 `Won += d;` | ``error CS0191: A readonly field cannot be assigned to …`` | 메서드도 막는다 |
| `readonly struct` 에서 `this = default;` | ★ ``error CS1604: Cannot assign to 'this' because it is read-only`` | **`this` 통째 대입도** 막는다 |
| 보통 구조체의 같은 코드 | **통과** | ★★ **구조체에서는 `this` 에 대입할 수 있다** — 클래스에는 없는 일이다 |

- ★★★ **마지막 줄이 놀라운 자리**다 — **보통 구조체의 메서드는 `this = default;` 를 할 수 있다.**\
  `this` 가 **값이라 대입 대상**이 되기 때문이다. 클래스에서는 문법 자체가 없다.
- ★ 그래서 `readonly struct` 가 막는 것은 **셋**이다 — 가변 필드 · 필드 쓰기 · **`this` 대입**.
- ★ **새 값을 돌려주는 쪽**(`C Add(int d) => new C(Won + d);`)은 얼마든지 된다.\
  불변 구조체의 「변경」은 항상 「**새 값을 만들어 돌려주기**」다 — `record struct` 의 `with` 가 그것을 문법으로 만든 것이다((6)).

### (3) ★★★ 방어적 복사 — 조용히 복사가 생긴다

**언제 쓰나** — ★★★ **이 절이 이 주제의 이유다.** 「구조체 메서드를 불렀는데 아무 일도 안 일어난다」 할 때.

```text
===== 소스: cs02b-defensive.cs =====
using System;

var box = new Box();
Console.WriteLine($"[가변 필드]   Next() 세 번 : {box.Plain.Next()} {box.Plain.Next()} {box.Plain.Next()}");
Console.WriteLine($"[가변 필드]   그 뒤 N      : {box.Plain.N}");
Console.WriteLine($"[readonly 필드] Next() 세 번 : {box.Frozen.Next()} {box.Frozen.Next()} {box.Frozen.Next()}");
Console.WriteLine($"[readonly 필드] 그 뒤 N      : {box.Frozen.N}");

var c = new Counter();
Console.WriteLine($"[지역 변수]   Next() 세 번 : {c.Next()} {c.Next()} {c.Next()}");
Console.WriteLine($"[지역 변수]   그 뒤 N      : {c.N}");

var d = new Counter();
Console.WriteLine($"[in 매개변수] Next() 세 번 : {ViaIn(in d)} {ViaIn(in d)} {ViaIn(in d)}");
Console.WriteLine($"[in 매개변수] 그 뒤 N      : {d.N}");

var e = new Counter();
Console.WriteLine($"[ref 매개변수] Next() 세 번 : {ViaRef(ref e)} {ViaRef(ref e)} {ViaRef(ref e)}");
Console.WriteLine($"[ref 매개변수] 그 뒤 N      : {e.N}");

static int ViaIn(in Counter c) { return c.Next(); }
static int ViaRef(ref Counter c) { return c.Next(); }

struct Counter { public int N; public int Next() { return ++N; } }

class Box {
    public Counter Plain = new Counter();
    public readonly Counter Frozen = new Counter();
}
===== csc -out:ex.dll cs02b-defensive.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[가변 필드]   Next() 세 번 : 1 2 3
[가변 필드]   그 뒤 N      : 3
[readonly 필드] Next() 세 번 : 1 1 1
[readonly 필드] 그 뒤 N      : 0
[지역 변수]   Next() 세 번 : 1 2 3
[지역 변수]   그 뒤 N      : 3
[in 매개변수] Next() 세 번 : 1 1 1
[in 매개변수] 그 뒤 N      : 0
[ref 매개변수] Next() 세 번 : 1 2 3
[ref 매개변수] 그 뒤 N      : 3
```

| 구조체가 놓인 자리 | `Next()` 세 번 | 그 뒤 `N` | 무슨 일이 났나 |
|---|---|---|---|
| **지역 변수** | `1 2 3` | **3** | 원본을 고친다 |
| **`ref` 매개변수** | `1 2 3` | **3** | 원본을 고친다 |
| **가변 필드** | `1 2 3` | **3** | 원본을 고친다 |
| ★★★ **`readonly` 필드** | **`1 1 1`** | ★★★ **0** | **부를 때마다 새 복사본**이다 |
| ★★★ **`in` 매개변수** | **`1 1 1`** | ★★★ **0** | 〃 |

- ★★★ **`1 1 1` 이 이 배치에서 가장 무서운 출력**이다.\
  같은 객체의 `Next()` 를 세 번 불렀는데 **매번 1 이 나오고 원본은 0** 이다.\
  ★ 컴파일러가 「`readonly` 자리의 값은 못 바꾼다」를 지키려고 **호출 직전에 복사본을 만들었고**,\
  `Next()` 는 **그 복사본**을 올린 뒤 버렸다.
- ★★★ **그리고 아무도 말해 주지 않는다.** 최대 경고 수준으로 다시 던져 봤다.

```text
===== 소스: cs02b-defensive.cs =====
using System;

var box = new Box();
Console.WriteLine($"[가변 필드]   Next() 세 번 : {box.Plain.Next()} {box.Plain.Next()} {box.Plain.Next()}");
Console.WriteLine($"[가변 필드]   그 뒤 N      : {box.Plain.N}");
Console.WriteLine($"[readonly 필드] Next() 세 번 : {box.Frozen.Next()} {box.Frozen.Next()} {box.Frozen.Next()}");
Console.WriteLine($"[readonly 필드] 그 뒤 N      : {box.Frozen.N}");

var c = new Counter();
Console.WriteLine($"[지역 변수]   Next() 세 번 : {c.Next()} {c.Next()} {c.Next()}");
Console.WriteLine($"[지역 변수]   그 뒤 N      : {c.N}");

var d = new Counter();
Console.WriteLine($"[in 매개변수] Next() 세 번 : {ViaIn(in d)} {ViaIn(in d)} {ViaIn(in d)}");
Console.WriteLine($"[in 매개변수] 그 뒤 N      : {d.N}");

var e = new Counter();
Console.WriteLine($"[ref 매개변수] Next() 세 번 : {ViaRef(ref e)} {ViaRef(ref e)} {ViaRef(ref e)}");
Console.WriteLine($"[ref 매개변수] 그 뒤 N      : {e.N}");

static int ViaIn(in Counter c) { return c.Next(); }
static int ViaRef(ref Counter c) { return c.Next(); }

struct Counter { public int N; public int Next() { return ++N; } }

class Box {
    public Counter Plain = new Counter();
    public readonly Counter Frozen = new Counter();
}
===== csc -warn:9 -out:ex.dll cs02b-defensive.cs (cc exit=0) =====

```

- ★★★ **`-warn:9` 에 `cc exit=0` 이고 출력이 0줄**이다. **경고가 없다는 사실 자체가 이 절의 결론**이다.\
  ★ 「경고 0건」을 셀 때는 **종료 코드를 같이 봐야** 뜻이 있다 — `cc exit=0` 이라 **정말 깨끗하게 통과**한 것이다.
- ★★★ **그러면 무엇으로 보나 — IL 이다.**

```text
===== 소스: cs02b-defensive-il.cs =====
Il.Dump(typeof(Probe), "ViaRef");
Il.Dump(typeof(Probe), "ViaIn");
Il.Dump(typeof(Probe), "ViaInReadonly");

static class Probe {
    public static int ViaRef(ref Counter c) { return c.Next(); }
    public static int ViaIn(in Counter c) { return c.Next(); }
    public static int ViaInReadonly(in RoCounter c) { return c.Peek(); }
}

struct Counter { public int N; public int Next() { return ++N; } }
readonly struct RoCounter { public readonly int N; public int Peek() { return N; } }
===== csc -r:il.dll -out:ex.dll cs02b-defensive-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.ViaRef ---
  .locals [0] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: call Counter::Next
  IL_0007: stloc.0
  IL_0008: br.s IL_000a
  IL_000a: ldloc.0
  IL_000b: ret
--- Probe.ViaIn ---
  .locals [0] Counter
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: ldobj Counter
  IL_0007: stloc.0
  IL_0008: ldloca.s 0
  IL_000a: call Counter::Next
  IL_000f: stloc.1
  IL_0010: br.s IL_0012
  IL_0012: ldloc.1
  IL_0013: ret
--- Probe.ViaInReadonly ---
  .locals [0] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: call RoCounter::Peek
  IL_0007: stloc.0
  IL_0008: br.s IL_000a
  IL_000a: ldloc.0
  IL_000b: ret
```

| 받는 방법 | IL | 복사가 있나 |
|---|---|---|
| `ref Counter` | `ldarg.0` → `call Counter::Next` | ★ **없다** |
| ★★★ **`in Counter`**(보통 구조체) | `ldarg.0` → ★★★ **`ldobj Counter`** → `stloc.0` → `ldloca.s 0` → `call` | ★★★ **있다** |
| **`in RoCounter`**(`readonly struct`) | `ldarg.0` → `call RoCounter::Peek` | ★ **없다 — 사라졌다** |

- ★★★ **`ldobj Counter` + `stloc.0` 두 줄이 방어적 복사의 실체**다.\
  「참조로 받았지만 메서드를 부르기 전에 값을 통째로 지역에 옮겨 담는다」는 뜻이다.\
  그 뒤 `ldloca.s 0` 으로 **복사본의 주소**를 얹고 호출하니, `Next()` 가 올린 것은 복사본이다.
- ★★★ **`readonly struct` 로 바꾸면 그 두 줄이 통째로 사라진다.**\
  컴파일러가 「이 타입은 자기를 못 바꾼다」를 **타입에서** 알기 때문에 지킬 것이 없다.
- ★★ **그래서 `in` 은 「공짜 최적화」가 아니다.** `readonly struct` 가 아닌 타입에 붙이면\
  **복사를 줄이려다 복사를 늘린다.** 규칙은 하나다 — **`in` 을 쓰려면 `readonly struct` 부터.**
- ★ 같은 일이 **`readonly` 필드**에서도 난다(위 실행 출력). **필드 선언에 `readonly` 를 붙였을 뿐인데** 그렇다.

### (4) 구조체의 기본 생성자 — 되는데, 건너뛰어진다

**언제 쓰나** — 「구조체에 기본값을 주고 싶다」 할 때. **C# 10 에서 판이 바뀐 자리**다.

```text
===== 소스: cs02b-ctor.cs =====
using System;

var a = new Money();            // 기본 생성자가 있으면 그것이 불린다
var b = default(Money);         // default 는 생성자를 건너뛴다
var c = new Money[2];           // 배열도 건너뛴다
var d = new Money(50);

Console.WriteLine($"new Money()    : Won={a.Won}  Tag={a.Tag ?? "(null)"}");
Console.WriteLine($"default(Money) : Won={b.Won}  Tag={b.Tag ?? "(null)"}");
Console.WriteLine($"new Money[2][0]: Won={c[0].Won}  Tag={c[0].Tag ?? "(null)"}");
Console.WriteLine($"new Money(50)  : Won={d.Won}  Tag={d.Tag ?? "(null)"}");
Console.WriteLine($"a.Equals(b)    : {a.Equals(b)}");

struct Money {
    public int Won = 100;             // C# 10 부터 구조체 필드 초기자가 된다
    public string Tag = "won";
    public Money() { }                // C# 10 부터 구조체 매개변수 없는 생성자가 된다
    public Money(int won) { Won = won; Tag = "won"; }
}
===== csc -out:ex.dll cs02b-ctor.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new Money()    : Won=100  Tag=won
default(Money) : Won=0  Tag=(null)
new Money[2][0]: Won=0  Tag=(null)
new Money(50)  : Won=50  Tag=won
a.Equals(b)    : False
```

| 쓴 것 | `Won` | `Tag` | 읽는 법 |
|---|---|---|---|
| `new Money()` | **100** | `won` | ★ **생성자가 불렸다**(C# 10부터 된다) |
| `default(Money)` | ★★★ **0** | ★★★ **`(null)`** | ★★★ **생성자를 건너뛴다** |
| `new Money[2]` 의 원소 | ★★★ **0** | ★★★ **`(null)`** | ★★★ **배열도 건너뛴다** |
| `new Money(50)` | 50 | `won` | 인자 있는 생성자 |

- ★★★ **「구조체에 매개변수 없는 생성자를 못 쓴다」는 C# 9 까지의 이야기**다.\
  **C# 10부터** 구조체에 필드 초기자와 `public S() { }` 를 쓸 수 있다.
- ★★★ **그런데 「항상 불린다」는 보장은 여전히 없다.** `default(T)`·**배열 할당**·`Array.Resize`·\
  제네릭의 `default(T)` 는 **생성자를 건너뛰고 모든 비트를 0 으로** 만든다.\
  ★ 그래서 `a.Equals(b)` 가 **`False`** 다 — `new Money()` 와 `default(Money)` 가 **다른 값**이다.
- ★★ **결론 — 구조체에서 「0 이 아닌 기본값」에 기대면 안 된다.**\
  `default(T)` 가 유효한 값이 되도록 **타입을 설계하는 편**이 맞다.\
  ★ 이것이 **클래스와 갈리는 큰 자리**다 — 클래스는 생성자를 건너뛸 방법이 없다.

### (5) ★★ 기본 `Equals` 의 대가 — 박싱과 느린 경로

**언제 쓰나** — 「구조체를 `Dictionary` 키로 쓴다」 · 「`Contains` 를 돈다」 할 때.

```text
===== 소스: cs02b-equals-alloc.cs =====
using System;

Warm();

var p1 = new Plain { A = 1, B = 2 };
var p2 = new Plain { A = 1, B = 2 };
var f1 = new Fast { A = 1, B = 2 };
var f2 = new Fast { A = 1, B = 2 };
var r1 = new RefField { A = 1, S = "x" };
var r2 = new RefField { A = 1, S = "x" };

long a0 = GC.GetAllocatedBytesForCurrentThread();
bool b1 = p1.Equals(p2);                 // ValueType.Equals(object) — 인자가 박싱된다
long a1 = GC.GetAllocatedBytesForCurrentThread();
bool b2 = f1.Equals(f2);                 // IEquatable<Fast>.Equals(Fast) — 박싱 없음
long a2 = GC.GetAllocatedBytesForCurrentThread();
bool b3 = r1.Equals(r2);                 // 참조 필드가 있는 구조체
long a3 = GC.GetAllocatedBytesForCurrentThread();
bool b4 = object.Equals(p1, p2);         // 양쪽 다 박싱된다
long a4 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"p1.Equals(p2)         = {b1}   할당 +{a1 - a0} 바이트");
Console.WriteLine($"f1.Equals(f2)         = {b2}   할당 +{a2 - a1} 바이트");
Console.WriteLine($"r1.Equals(r2)         = {b3}   할당 +{a3 - a2} 바이트");
Console.WriteLine($"object.Equals(p1, p2) = {b4}   할당 +{a4 - a3} 바이트");

static void Warm() {
    var x = new Plain(); var y = new Plain(); _ = x.Equals(y);
    var u = new Fast(); var v = new Fast(); _ = u.Equals(v);
    var s = new RefField(); var t = new RefField(); _ = s.Equals(t);
    _ = object.Equals(x, y);
    GC.GetAllocatedBytesForCurrentThread();
}

struct Plain { public int A; public int B; }
struct RefField { public int A; public string S; }

struct Fast : IEquatable<Fast> {
    public int A; public int B;
    public bool Equals(Fast other) => A == other.A && B == other.B;
    public override bool Equals(object? o) => o is Fast f && Equals(f);
    public override int GetHashCode() => HashCode.Combine(A, B);
}
===== csc -out:ex.dll cs02b-equals-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
p1.Equals(p2)         = True   할당 +48 바이트
f1.Equals(f2)         = True   할당 +0 바이트
r1.Equals(r2)         = True   할당 +152 바이트
object.Equals(p1, p2) = True   할당 +48 바이트
```

| 쓴 것 | 할당 | 왜 |
|---|---|---|
| `p1.Equals(p2)`(오버로드 없음) | ★ **+48** | ★★ **`this` 와 인자가 둘 다 박싱**된다(24 × 2) |
| `f1.Equals(f2)`(`IEquatable<Fast>`) | ★★★ **+0** | **`Equals(Fast)` 가 먼저 뽑힌다** |
| `r1.Equals(r2)`(참조 필드가 있는 구조체) | ★★★ **+152** | ★★★ **리플렉션 경로**가 더 쓴다 |
| `object.Equals(p1, p2)` | **+48** | 매개변수가 `object` 둘이다 |

- ★★★ **`+0` 과 `+152` 의 대비가 이 절의 결론**이다.\
  `IEquatable<T>` 를 구현하면 **박싱이 통째로 사라지고**, 안 하면 **매 비교가 힙을 쓴다.**
- ★★ **`Plain`(48)과 `RefField`(152)가 갈리는 이유**는 CoreCLR 이 **두 경로**를 갖기 때문이다 —\
  **참조를 하나도 안 품은 구조체**는 바이트를 통째로 비교할 수 있지만,\
  **참조 필드가 있으면 필드를 하나씩 돌며 각각의 `Equals` 를 불러야** 한다.\
  ★ 그 갈림을 [01번](../01-value-types-and-reference-types/)의 (8)에서 `IsReferenceOrContainsReferences<T>()` 로 봤다.
- 시간도 재 봤다.

```text
===== 소스: cs02b-equals-time.cs =====
using System;
using System.Diagnostics;

// 델리게이트 호출 비용이 섞이지 않게 루프를 각각 직접 돈다.
for (int w = 0; w < 3; w++) { PlainRun(); RefRun(); FastRun(); }   // 워밍업(JIT 계층 승격)

Console.WriteLine("판 | Plain 기본 Equals | RefField 기본 Equals | Fast IEquatable<T>");
for (int t = 1; t <= 5; t++)
    Console.WriteLine($" {t} | {PlainRun(),9} ns/회 | {RefRun(),12} ns/회 | {FastRun(),10} ns/회");
Console.WriteLine("(1,000,000 회 반복의 평균 · 절댓값이 아니라 자릿수 차이가 근거다)");

static long PlainRun() {
    var a = new Plain { A = 1, B = 2 }; var b = new Plain { A = 1, B = 2 };
    var sw = Stopwatch.StartNew(); bool s = false;
    for (int i = 0; i < 1_000_000; i++) s ^= a.Equals(b);
    sw.Stop(); GC.KeepAlive(s);
    return (long)Math.Round(sw.Elapsed.TotalNanoseconds / 1_000_000);
}

static long RefRun() {
    var a = new RefField { A = 1, S = "x" }; var b = new RefField { A = 1, S = "x" };
    var sw = Stopwatch.StartNew(); bool s = false;
    for (int i = 0; i < 1_000_000; i++) s ^= a.Equals(b);
    sw.Stop(); GC.KeepAlive(s);
    return (long)Math.Round(sw.Elapsed.TotalNanoseconds / 1_000_000);
}

static long FastRun() {
    var a = new Fast { A = 1, B = 2 }; var b = new Fast { A = 1, B = 2 };
    var sw = Stopwatch.StartNew(); bool s = false;
    for (int i = 0; i < 1_000_000; i++) s ^= a.Equals(b);
    sw.Stop(); GC.KeepAlive(s);
    return (long)Math.Round(sw.Elapsed.TotalNanoseconds / 1_000_000);
}

struct Plain { public int A; public int B; }
struct RefField { public int A; public string S; }

struct Fast : IEquatable<Fast> {
    public int A; public int B;
    public bool Equals(Fast other) => A == other.A && B == other.B;
    public override bool Equals(object? o) => o is Fast f && Equals(f);
    public override int GetHashCode() => HashCode.Combine(A, B);
}
===== csc -out:ex.dll cs02b-equals-time.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
판 | Plain 기본 Equals | RefField 기본 Equals | Fast IEquatable<T>
 1 |        34 ns/회 |          146 ns/회 |          4 ns/회
 2 |        36 ns/회 |          144 ns/회 |          3 ns/회
 3 |        35 ns/회 |          146 ns/회 |          4 ns/회
 4 |        38 ns/회 |          146 ns/회 |          4 ns/회
 5 |        36 ns/회 |          149 ns/회 |          4 ns/회
(1,000,000 회 반복의 평균 · 절댓값이 아니라 자릿수 차이가 근거다)
```

- ★★ **다섯 판이 전부 같은 자릿수**다 — `Fast` 3\~4 · `Plain` 34\~38 · `RefField` 144\~149 ns.\
  **신호 대 잡음**: 한 판 안의 다섯 줄이 15% 안쪽, 캡처를 다시 돌리면 20% 까지 움직이는데\
  **세 열의 차이는 10배와 40배**다. 신호가 잡음보다 훨씬 크다.
- ★★★ **근거로 쓰는 것은 「약 10배·약 40배」이지 `4 ns` 나 `146 ns` 가 아니다.**\
  ns 절댓값은 **흔들리는 칸**이다(머리말 표). 머신이 바뀌면 다 바뀐다.
- ★ **측정 조건** — `Stopwatch` 로 **1,000,000회 반복의 평균**, **워밍업 3회**(JIT 계층 승격을 측정 밖으로 뺐다),\
  델리게이트를 안 끼우고 **루프를 각각 직접** 돌았다. 전용 벤치마크 도구(BenchmarkDotNet)는 **안 썼다.**
- ★★ **그래서 「`struct` 가 `class` 보다 빠르다」를 이걸로 말하면 안 된다.** 잰 것은 **`Equals` 한 축**이다.

### (6) `record struct` — 값 동등성을 공짜로

**언제 쓰나** — 「값이 같으면 같은 것」이 맞는 타입일 때. **대부분의 구조체가 그렇다.**

```text
===== 소스: cs02b-record.cs =====
using System;

var a = new Money(100, "KRW");
var b = new Money(100, "KRW");
var c = a with { Won = 200 };

Console.WriteLine($"a          : {a}");
Console.WriteLine($"c = a with : {c}");
Console.WriteLine($"a == b     : {a == b}");
Console.WriteLine($"a.Equals(b): {a.Equals(b)}");
Console.WriteLine($"a.GetHashCode() == b.GetHashCode() : {a.GetHashCode() == b.GetHashCode()}");

var (won, cur) = a;
Console.WriteLine($"해체       : won={won} cur={cur}");

Warm(a, b);
long g0 = GC.GetAllocatedBytesForCurrentThread();
bool eq = a.Equals(b);
long g1 = GC.GetAllocatedBytesForCurrentThread();
Console.WriteLine($"a.Equals(b) 할당 : +{g1 - g0} 바이트 (결과 {eq})");

static void Warm(Money x, Money y) { _ = x.Equals(y); GC.GetAllocatedBytesForCurrentThread(); }

readonly record struct Money(int Won, string Currency);
===== csc -out:ex.dll cs02b-record.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
a          : Money { Won = 100, Currency = KRW }
c = a with : Money { Won = 200, Currency = KRW }
a == b     : True
a.Equals(b): True
a.GetHashCode() == b.GetHashCode() : True
해체       : won=100 cur=KRW
a.Equals(b) 할당 : +0 바이트 (결과 True)
```

| 얻은 것 | 결과 |
|---|---|
| `ToString()` | `Money { Won = 100, Currency = KRW }` |
| `==` · `Equals` | **값 비교**(`True`) |
| `GetHashCode()` | 값이 같으면 같다 |
| 해체(`var (won, cur) = a;`) | 된다 |
| `with` 식 | `a with { Won = 200 }` |
| ★★★ **`Equals` 할당** | ★★★ **+0 바이트** — **박싱이 없다** |

- ★★★ **`record struct` 는 `IEquatable<T>` 를 자동으로 구현한다** — 그래서 (5)의 `Fast` 와 같은 **+0** 이다.\
  손으로 `Equals`·`GetHashCode` 를 짜는 일이 통째로 없어진다.
- ★★ **`readonly record struct` 로 쓰면 (2)·(3)의 문제도 같이 사라진다** —\
  불변이라 방어적 복사가 안 생기고, 속성이 `init` 전용이 된다.

```text
===== 소스: cs02b-record-mutate.cs =====
readonly record struct Money(int Won);

class Program {
    static void Main() {
        var m = new Money(100);
        m.Won = 200;
        System.Console.WriteLine(m.Won);
    }
}
===== csc -out:ex.dll cs02b-record-mutate.cs (cc exit=1) =====
cs02b-record-mutate.cs(6,9): error CS8852: Init-only property or indexer 'Money.Won' can only be assigned in an object initializer, or on 'this' or 'base' in an instance constructor or an 'init' accessor.
```

- ★ ``error CS8852: Init-only property … can only be assigned in an object initializer`` —\
  **위치 매개변수 속성은 `init` 전용**이 된다. 「바꾸려면 `with` 를 쓰라」는 뜻이다.
- ★ `record struct`(`readonly` 없이)는 속성이 **`get`/`set`** 이라 이 에러가 안 난다.\
  ★ **이 문서는 `readonly record struct` 만 던졌다.**

### (7) 고를 것을 손으로 돌리는 순서

1. **「동일성이 있나?」** — 「같은 주문」·「같은 사용자」처럼 **복사되면 안 되는 것**이면 **`class`**.
2. **「상속·다형성이 필요한가?」** — 그러면 **`class`**(구조체는 상속을 못 한다).
3. **「널이 의미가 있나?」** — 있으면 **`class`**(또는 `T?` — [01번](../01-value-types-and-reference-types/)의 (7)).
4. **「값이 같으면 같은 것인가?」** — 그러면 **`readonly record struct`** 가 첫 후보다((6)).
5. **「작고 안 바뀌나?」** — 그러면 **`readonly struct`**((2)). ★ **`readonly` 를 빼지 마라**((3)).
6. **「배열·리스트에 잔뜩 담나?」** — 값 타입이 **헤더 값을 안 낸다**((1)).
7. 여기까지 와서 애매하면 **`class`** 다. ★ **구조체는 이유가 있을 때 고른다.**

## 문법 — 형태와 규칙

### 형태

```csharp
// cs02b-defensive.cs
using System;

var box = new Box();
Console.WriteLine($"[가변 필드]   Next() 세 번 : {box.Plain.Next()} {box.Plain.Next()} {box.Plain.Next()}");
Console.WriteLine($"[가변 필드]   그 뒤 N      : {box.Plain.N}");
Console.WriteLine($"[readonly 필드] Next() 세 번 : {box.Frozen.Next()} {box.Frozen.Next()} {box.Frozen.Next()}");
Console.WriteLine($"[readonly 필드] 그 뒤 N      : {box.Frozen.N}");

var c = new Counter();
Console.WriteLine($"[지역 변수]   Next() 세 번 : {c.Next()} {c.Next()} {c.Next()}");
Console.WriteLine($"[지역 변수]   그 뒤 N      : {c.N}");

var d = new Counter();
Console.WriteLine($"[in 매개변수] Next() 세 번 : {ViaIn(in d)} {ViaIn(in d)} {ViaIn(in d)}");
Console.WriteLine($"[in 매개변수] 그 뒤 N      : {d.N}");

var e = new Counter();
Console.WriteLine($"[ref 매개변수] Next() 세 번 : {ViaRef(ref e)} {ViaRef(ref e)} {ViaRef(ref e)}");
Console.WriteLine($"[ref 매개변수] 그 뒤 N      : {e.N}");

static int ViaIn(in Counter c) { return c.Next(); }
static int ViaRef(ref Counter c) { return c.Next(); }

struct Counter { public int N; public int Next() { return ++N; } }

class Box {
    public Counter Plain = new Counter();
    public readonly Counter Frozen = new Counter();
}
```

규칙 불릿.

- **구조체는 `System.ValueType` 을 상속하고, 그 밖의 상속은 못 한다.** 인터페이스 구현은 된다.
- **`readonly struct` 는 모든 인스턴스 필드가 `readonly` 여야 한다**((2)) — ``CS8340``.
- ★★★ **`readonly` 가 아닌 구조체를 `readonly` 필드·`in` 매개변수로 다루면 방어적 복사가 생긴다**((3)).\
  **에러도 경고도 없다.** IL 의 `ldobj` 만이 그것을 보여 준다.
- **구조체의 메서드는 `this = default;` 를 할 수 있다**((2)) — 클래스에는 없는 일이고, `readonly struct` 는 막는다.
- **C# 10부터 구조체에 필드 초기자와 매개변수 없는 생성자를 쓸 수 있다**((4)).\
  ★ 단 **`default(T)` 와 배열 할당은 그것을 건너뛴다.**
- **기본 `Equals` 는 박싱하고, 참조 필드가 있으면 느린 경로를 탄다**((5)).\
  `IEquatable<T>` 나 `record struct` 가 둘 다 없앤다.
- **`record struct` 는 C# 10부터** · **`readonly record struct` 의 위치 속성은 `init` 전용**이다((6)).

### 금지 사례 — 던져서 받은 넷

| 쓴 것 | 진단 |
|---|---|
| `readonly struct` 에 가변 필드 | ``error CS8340: Instance fields of readonly structs must be readonly.`` |
| `readonly` 필드에 쓰기 | ``error CS0191: A readonly field cannot be assigned to (except in a constructor or init-only setter …)`` |
| `readonly struct` 에서 `this = default;` | ``error CS1604: Cannot assign to 'this' because it is read-only`` |
| `readonly record struct` 의 속성에 대입 | ``error CS8852: Init-only property or indexer 'Money.Won' can only be assigned in an object initializer …`` |

★★★ **그리고 「진단이 안 나는 사례」가 하나 더 있다** — **방어적 복사**((3)).\
**`-warn:9` 로도 0줄**이라, 이 표에 들어갈 자리가 없다. **그것이 이 주제의 값어치다.**

## 어디서 틀리나

### 1. ★★★ 「`in` 을 붙이면 복사가 준다」

**`readonly struct` 가 아니면 늘어난다**((3)). IL 에 **`ldobj`** 가 들어가고,\
**메서드를 부를 때마다** 복사본이 생긴다. ★ **경고는 `-warn:9` 로도 0줄**이다.

### 2. ★★★ 「구조체 메서드를 불렀는데 값이 안 바뀐다 — 버그다」

**버그가 아니라 규칙이다**((3)). `readonly` 필드나 `in` 매개변수면 **복사본을 고친 것**이다.\
★ 고치는 법은 두 가지 — **`readonly struct` 로 만들거나**, **`ref` 로 받거나**.

### 3. ★★★ 「구조체는 생성자를 못 만든다」

**C# 10부터 된다**((4)). 다만 **`default(T)` 와 배열 할당이 그것을 건너뛴다.**\
★ **「항상 불린다」가 보장이 아니므로 0 이 유효한 값이 되게 설계한다.**

### 4. ★★ 「구조체는 `Equals` 를 알아서 잘 해 준다」

**해 주긴 하는데 두 가지를 낸다**((5)) — **박싱 48바이트**와,\
**참조 필드가 있으면 약 40배 느린 경로**(3\~4 ns 대 144\~149 ns).\
★ `record struct` 나 `IEquatable<T>` 로 **둘 다 없앤다.**

### 5. ★★ 「작으면 `struct`, 크면 `class`」

**가이드라인이지 이 문서의 측정이 아니다.** 실측으로 말할 수 있는 것은\
**할당**((1))·**방어적 복사**((3))·**`Equals` 비용**((5)) 셋이다.\
★ **복사 비용 자체는 안 쟀다** — 재려면 벤치마크 하네스가 따로 필요하다.

### 6. ★★ 「값 타입 배열이 항상 이득이다」

**담는 값이 크면 배열 자체가 커진다**((1)) — `Big[1000]` 이 **64024바이트**를 **한 덩어리로** 잡는다.\
★ 이득은 「객체 헤더 × 개수」와 「GC 가 훑을 참조 수」에서 나오는 것이지 **총 바이트에서 나오는 게 아니다.**

### 7. ★ 「`record struct` 를 쓰면 불변이 된다」

**`readonly` 를 붙여야 불변이다**((6)). 그냥 `record struct` 는 속성이 **`get`/`set`** 이라 바뀐다.\
★ 이 문서는 **`readonly record struct` 만** 던졌다.

### 8. ★ 「구조체는 상속이 안 되니 다형성을 못 쓴다」

**인터페이스는 구현할 수 있다.** 다만 **인터페이스로 올리면 박싱**된다 —\
그 정본은 [03번](../03-boxing-and-unboxing/)이고, **제네릭 제약**이 그것을 피하는 법이다.

### 9. ★ 「`this` 에 대입한다는 건 말이 안 된다」

**구조체에서는 된다**((2)). `this` 가 **값**이라 대입 대상이 되기 때문이고,\
`readonly struct` 가 그것을 `CS1604` 로 막는다.

### 10. 「Java 를 알면 그대로 온다」

**이 주제가 통째로 없다.** Java 에는 **사용자 정의 값 타입이 없고**(JEP 401 은 미리보기),\
`record` 도 **항상 참조 타입**이다. ★ 그래서 방어적 복사라는 개념 자체가 Java 에는 없다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **`readonly struct` 의 필드가 전부 `readonly` 여야 하는** 것 | **언어**(C# 7.2) |
| **`readonly struct` 에서 `this` 대입이 막히는** 것 · **보통 구조체에서는 되는** 것 | **언어** |
| ★★★ **`readonly` 가 아닌 구조체를 읽기 전용 자리에서 쓰면 복사본이 관찰되는** 것 | ★★★ **언어**다 — 읽기 전용 자리의 값이 **안 바뀌어야 한다**가 규칙이고, 복사는 그 규칙의 **귀결**이다 |
| ★★ **그 복사가 `ldobj` 로 나오는** 것 · **`readonly struct` 면 사라지는** 것 | ★★ **Roslyn 의 코드 생성**이다. 규칙은 「안 바뀐다」이고 **명령 이름이 규칙이 아니다** |
| ★★★ **경고가 한 줄도 안 나는** 것 | ★★★ **컴파일러 구현**이다. 분석기(analyzer)를 켜면 달라질 수 있다 — **이 문서는 분석기를 안 켰다** |
| **C# 10부터 구조체 필드 초기자·매개변수 없는 생성자가 되는** 것 | **언어**(C# 10) |
| **`default(T)`·배열 할당이 생성자를 건너뛰는** 것 | **언어** + CLI — 「모든 비트 0」이 값 타입의 기본값이다 |
| ★★ **기본 `Equals` 가 박싱하는** 것 | ★★ **언어**다 — `ValueType.Equals(object)` 의 시그니처가 `object` 다 |
| ★★★ **참조 필드가 있으면 40배 느린** 것 · **48·152바이트** | ★★★ **CoreCLR 10 의 구현**이다. 「두 경로가 있다」가 관찰이고 **배수는 이 판의 수치**다 |
| ★ **`record struct` 가 `IEquatable<T>` 를 자동 구현하는** 것 | ★ **언어**(C# 10 기능 명세) |
| 진단 문구 · 진단 코드 | **컴파일러 구현**(Roslyn) |

## 언제 쓰고 언제 안 쓰나

**`readonly record struct` 를 첫 후보로 두는 자리**\
① **값이 같으면 같은 것** — 금액·좌표·기간·식별자.\
② **작고 안 바뀌는 것.** ③ **배열·리스트에 잔뜩 담는 것**((1)).\
★ 이것 하나로 (2)·(3)·(5)·(6)의 문제가 **전부** 사라진다.

**`class` 를 고르는 자리**\
① **동일성이 있는 것** ② **상속·다형성** ③ **크거나 자라는 것** ④ **널이 의미 있는 것**.

**`struct` 를 골랐다면 반드시 같이 하는 것 셋**\
① **`readonly` 를 붙인다**((3)) ② **`IEquatable<T>` 를 구현한다**(또는 `record struct`)((5))\
③ **`default(T)` 가 유효한 값이 되게 설계한다**((4)).

**`in` 을 쓰는 조건** — ★ **`readonly struct` 일 때만**((3)).\
그 밖에는 **`ref`** 를 쓰거나 **그냥 값으로** 받는다.

## 핵심 문장

1. **구조체의 함정은 「느리다」가 아니라 「조용하다」다** — 방어적 복사에 경고가 없다((3)).
2. **`readonly` 가 아닌 구조체를 `in`·`readonly` 필드로 다루면 복사본이 생긴다** — `1 1 1` 이 그 증거다.
3. **그 복사가 IL 의 `ldobj` 다** — `readonly struct` 로 바꾸면 사라진다.
4. **C# 10부터 구조체에 기본 생성자가 되지만, `default(T)` 와 배열은 그것을 건너뛴다.**
5. **기본 `Equals` 는 박싱하고, 참조 필드가 있으면 이 판에서 40배 느렸다** — `record struct` 가 둘 다 없앤다.
6. **고민되면 `class` 다** — 구조체는 **이유가 있을 때** 고른다.

## 관련 자료

- [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/) — ★ **선행.**\
  「대입이 무엇을 복사하나」와 **할당 바이트 0**이 거기다. (1)의 크기 이야기가 거기 (8)에서 시작한다.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — ★★ (5)의 **박싱 48바이트**가 거기서 정본이 된다.\
  「인터페이스로 올리면 박싱된다」와 「제네릭이 그것을 없앤다」도 거기다.
- [04번 — 변수 선언·`var`·타겟 타입 `new`](../04-var-and-target-typed-new/) — `Point p = new(1, 2);` 의 문법.
- [`../../c-cpp-csharp.md`](../../../c-cpp-csharp.md) — *값 타입이 JVM 대비 20년 앞섰다는 **논증**.*\
  **거기는 「왜 이 언어를 고르나」까지, 여기는 「그래서 무엇을 고르나」부터.**
- 목록의 **18번 주제**(`record` 와 `with`) — ★ (6)의 정본. `record class` 와의 대비가 거기다.
- 목록의 **19번 주제**(`Equals`/`GetHashCode`/`==`) — ★ (5)의 계약 쪽 정본.
- 목록의 **44번 주제**(`ref`/`out`/`in`) — (3)의 `in` 자체의 정본.
- 목록의 **45번 주제**(`ref struct`) · **46번 주제**(`Span<T>`) — 「힙으로 못 가는 구조체」.
- 목록의 **56번 주제**(불변성 도구 정리) — `readonly`·`init`·`record`·`ImmutableArray` 를 층별로 고르는 자리.
- Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **05번**(배열과 슬라이스) —\
  ★ **같은 집안의 질문이다.** Go 의 배열은 **값**, 슬라이스는 **헤더**라 대입이 무엇을 복사하는지로 갈린다.\
  ★★ 다만 Go 에는 **`readonly` 가 없어** 방어적 복사라는 개념이 없다 — **이 함정은 C# 고유**다.

## 용어 풀이

> **`readonly struct`** — 「만들어진 뒤 안 바뀐다」를 타입에 새긴 구조체(C# 7.2).\
> 예: `readonly struct Money { public readonly int Won; }` — 필드가 전부 `readonly` 여야 한다.

> **방어적 복사(defensive copy)** — 읽기 전용 자리의 구조체를 지키려고 **컴파일러가 몰래 만드는 복사본**.\
> 예: `readonly Counter c;` 의 `c.Next()` 는 복사본을 올리고 버린다 — 원본은 0 그대로다.

> **`ldobj`** — 「주소가 가리키는 값을 통째로 스택에 올려라」는 IL 명령.\
> 방어적 복사가 있는지 없는지를 **이 명령 하나로 가린다**((3)).

> **`IEquatable<T>`** — 「같은 타입끼리 박싱 없이 비교하는 법」을 약속하는 인터페이스.\
> 구현하면 `Equals(T)` 가 먼저 뽑혀 **할당이 0** 이 된다((5)).

> **리플렉션 경로** — 참조 필드가 있는 구조체의 기본 `Equals` 가 타는 길.\
> 필드를 하나씩 돌며 각각의 `Equals` 를 부른다 — 이 판에서 **40배** 느렸다.

> **`record struct`** — 값 동등성·`ToString`·해체·`with` 를 컴파일러가 만들어 주는 구조체(C# 10).

> **`default(T)`** — 「모든 비트를 0 으로」. 구조체의 **생성자를 건너뛴다**((4)).

## 더 들어가면

- **`ref struct`** — 힙으로 절대 못 가는 구조체(`Span<T>` 가 그것이다). ★ 안 던졌다 — 목록의 **45번 주제**.
- **`readonly` 멤버**(C# 8) — 구조체 **전체**가 아니라 **메서드 하나**에 `readonly` 를 붙이는 것.\
  ★ 이 문서는 **타입 수준의 `readonly` 만** 던졌다. 멤버 수준은 `CS8656` 경고와 얽혀 있다.
- **분석기 경고** — 방어적 복사를 잡아 주는 **외부 분석기**가 있다.\
  ★ 이 문서는 **분석기를 안 켰다** — 그래서 (3)의 「경고 0줄」은 **소박한 `csc` 기준**이다.
- **`Equals` 의 두 경로를 CoreCLR 소스에서 확인하기** — ★ 안 봤다.\
  관찰된 것은 「**참조 필드가 있으면 40배 느리다**」까지이고, **그 구현을 읽어 확인하지는 않았다.**
- **복사 비용 자체의 측정** — ★ **못 쟀다.** 크기를 바꿔 가며 대입·전달 횟수를 돌리는\
  **벤치마크 하네스가 따로 필요**하고, 이 문서에는 없다. (1)이 잰 것은 **할당**이지 복사가 아니다.
- **`record struct`(`readonly` 없는 것)** — ★ 안 던졌다. 속성이 `get`/`set` 이라 (6)의 에러가 안 난다.
