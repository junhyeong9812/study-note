# csharp/syntax/02 — `struct` 대 `class` 고르기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/value-types) · [Learn — 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/reference-types) · [.NET API — `GC.GetAllocatedBytesForCurrentThread`](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-24).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **읽는 법** — 할당 바이트는 **증분만** 근거로 쓴다(절댓값은 프로세스 누적이라 흔들린다).\
> `Stopwatch` 의 **ns 절댓값도 흔들리는 칸**이고, 근거로 쓰는 것은 **자릿수 차이**다.\
> ★★★ **3번과 4번은 「출력이 없는 것」이 결론인 자리**다 — 경고가 0줄이라는 사실 자체를 근거로 쓴다.\
> 자세한 환경은 [2-summary.md](2-summary.md) 머리말에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ `Big[1000]` 이 **64024**, `BigCls[1000]` 은 **8024** — 채우면 뒤집힌다

**출력**

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

**왜 그런가**

| 물어본 것 | 값 | 읽는 법 |
|---|---|---|
| `Unsafe.SizeOf<BigCls>()` | ★ **8** | **참조 하나의 크기**다 — 객체 크기가 아니다 |
| `new Big[1000]` | **+64024** | 64 × 1000 + 배열 헤더 24 — ★ **1000개가 이미 다 들어 있다** |
| `new BigCls[1000]` | **+8024** | 참조 8 × 1000 + 24 — ★ **`null` 1000개**다 |
| 거기에 1000개 채우기 | **+80000** | 객체 하나가 80(헤더 16 + 필드 64) |

- ★★★ **총합으로 보면 뒤집힌다** — `Big[1000]` 은 **64024**, `BigCls` 를 다 채우면 **88024** 다.\
  차이는 **객체 헤더 16바이트 × 1000** 과 **배열이 참조를 또 드는 8바이트 × 1000** 이다.
- ★★ **이 실험이 잰 것은 「할당」이지 「속도」가 아니다.** 「구조체가 빠르다」는 여기서 안 나온다.\
  ★ **복사 비용은 이 문서가 안 쟀다** — 재려면 대입·전달 횟수를 돌리는 **벤치마크 하네스**가 따로 필요하다.
- ★ 「16바이트 이하면 `struct`」 같은 규칙은 **가이드라인**이지 이 문서의 측정이 아니다.

### 2. ★★ 에러 **둘** — 필드 쓰기(`CS0191`)와 `this` 대입(`CS1604`)

**출력**

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

**왜 그런가**

| 쓴 것 | 진단 | 무엇을 말하나 |
|---|---|---|
| `readonly` 필드에 `Won += d;` | ``error CS0191: A readonly field cannot be assigned to …`` | 생성자 밖에서는 못 쓴다 |
| `readonly struct` 에서 `this = default;` | ★ ``error CS1604: Cannot assign to 'this' because it is read-only`` | **`this` 통째 대입도** 막는다 |
| **보통 구조체**의 같은 두 줄 | ★★ **통과** | 구조체의 `this` 는 **값이라 대입 대상**이다 |

- ★★★ **보통 구조체의 메서드는 `this = default;` 를 할 수 있다.**\
  **클래스에서는 그 문법 자체가 없다** — `this` 가 읽기 전용 참조이기 때문이다.\
  ★ 「구조체는 값이다」가 여기서도 그대로 드러난다.
- ★ 따로 던진 블록에서 **`readonly struct` 의 가변 필드**도 막힌다 — ``error CS8340: Instance fields of readonly structs must be readonly.``

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

- ★ 그래서 `readonly struct` 가 막는 것은 **셋**이다 — 가변 필드 · 필드 쓰기 · **`this` 대입**.\
  ★★ **새 값을 돌려주는 쪽**(`C Add(int d) => new C(Won + d);`)은 얼마든지 된다.\
  불변 구조체의 「변경」은 항상 「**새 값 만들기**」이고, `with` 식이 그것을 문법으로 만든 것이다(9번).

### 3. ★★★ `readonly` 필드와 `in` 에서만 **`1 1 1`** 이고 `N` 은 **0** 이다

**출력**

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

**왜 그런가**

| 구조체가 놓인 자리 | `Next()` 세 번 | 그 뒤 `N` | 무슨 일이 났나 |
|---|---|---|---|
| **지역 변수** | `1 2 3` | **3** | 원본을 고친다 |
| **가변 필드** | `1 2 3` | **3** | 원본을 고친다 |
| **`ref` 매개변수** | `1 2 3` | **3** | 원본을 고친다 |
| ★★★ **`readonly` 필드** | **`1 1 1`** | ★★★ **0** | **부를 때마다 새 복사본**이다 |
| ★★★ **`in` 매개변수** | **`1 1 1`** | ★★★ **0** | 〃 |

- ★★★ **버그가 아니라 규칙이다.** 「읽기 전용 자리의 값은 안 바뀌어야 한다」가 언어의 약속이고,\
  `Counter` 는 **`readonly struct` 가 아니라** `Next()` 가 자기를 바꿀 수 있는 메서드다.\
  그래서 컴파일러가 **호출 직전에 복사본을 만들어** 그 위에서 부른다 — **약속을 지킨 결과**다.
- ★★★ **세 번 불러 세 번 다 `1` 이 나오는 것**이 결정적이다.\
  한 번만 불렀으면 `1` 이 맞아 보여서 **못 잡는다.** 이 함정은 **반복 호출에서만 드러난다.**
- ★★ **고치는 법은 둘** — ① **`readonly struct` 로 만든다**(5번에서 IL 이 달라진다)\
  ② **`ref` 로 받는다**(위 표에서 `ref` 는 `1 2 3` 이다).\
  ★ 「`in` 을 떼고 값으로 받기」는 **고치는 게 아니다** — 그것도 복사본이라 `1 1 1` 이 된다.
- ★ **`readonly` 필드 쪽이 더 나쁘다** — `in` 은 시그니처에 보이기라도 하는데,\
  **필드 선언에 `readonly` 를 붙였을 뿐**인데 호출 지점이 조용히 바뀐다.

### 4. ★★ 경고 **0줄** · `cc exit=0` — 아무도 말해 주지 않는다

**출력**

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

**왜 그런가**

- ★★★ **최대 경고 수준(`-warn:9`)에 출력이 0줄이고 종료 코드가 0** 이다.\
  「깨끗하게 통과」한 것이지 **컴파일이 실패해서 경고가 없는 게 아니다** —\
  ★★ **「경고 0건」은 종료 코드를 같이 봐야 뜻이 있다.**
- ★★★ **「출력이 없다」가 이 절의 결론**이다. 에러 메시지가 교재인 언어(C·Rust)와 **정반대 자리**라,\
  이 주제는 **「진단 0줄」을 따로 캡처해 두는 것**으로 그 사실을 근거로 만들었다.
- ★★ **그러면 무엇으로 보나 — IL 이다**(5번). 실행 출력(3번)이 **증상**을, IL 이 **원인**을 보여 준다.
- ★ **주의** — 이건 **소박한 `csc` 기준**이다. 방어적 복사를 잡아 주는 **외부 분석기**가 있고,\
  ★ **이 문서는 분석기를 안 켰다.**

### 5. ★★★ `ldobj Counter` + `stloc.0` 두 줄이 그 복사다

**출력**

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

**왜 그런가**

| 받는 방법 | IL | 복사가 있나 |
|---|---|---|
| `ref Counter` | `ldarg.0` → `call Counter::Next` | ★ **없다** |
| ★★★ **`in Counter`**(보통 구조체) | `ldarg.0` → ★★★ **`ldobj Counter`** → `stloc.0` → `ldloca.s 0` → `call` | ★★★ **있다** |
| **`in RoCounter`**(`readonly struct`) | `ldarg.0` → `call RoCounter::Peek` | ★ **없다 — 사라졌다** |

- ★★★ `ldobj Counter` 는 「**주소가 가리키는 값을 통째로 스택에 올려라**」이고,\
  이어지는 `stloc.0` 이 그것을 **지역 0번**에 담는다. 그 다음 `ldloca.s 0` 으로 **복사본의 주소**를 얹고 호출한다.\
  **`Next()` 가 올린 것은 그 복사본의 `N`** 이고, 메서드가 끝나면 버려진다 — 3번의 `1 1 1` 이 이것이다.
- ★★★ **`readonly struct` 로 바꾸면 그 두 줄이 통째로 사라진다.**\
  컴파일러가 「이 타입은 자기를 못 바꾼다」를 **타입에서** 알아 지킬 것이 없다.
- ★★ **그래서 「`in` 은 복사를 줄인다」가 참인 것은 `readonly struct` 일 때뿐**이다.\
  아니면 **복사를 줄이려다 늘린다** — 값으로 받으면 **한 번** 복사하는데, `in` 으로 받으면 **호출마다** 복사한다.
- ★ **규칙 하나로 줄이면** — **`in` 을 쓰려면 `readonly struct` 부터.**

### 6. ★★ `new Money()` 는 **100/won**, `default(Money)` 와 배열은 **0/null**

**출력**

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

**왜 그런가**

| 쓴 것 | `Won` | `Tag` | 읽는 법 |
|---|---|---|---|
| `new Money()` | **100** | `won` | ★ **생성자가 불렸다** |
| `default(Money)` | ★★★ **0** | ★★★ **`(null)`** | ★★★ **생성자를 건너뛴다** |
| `new Money[2]` 의 원소 | ★★★ **0** | ★★★ **`(null)`** | ★★★ **배열도 건너뛴다** |
| `new Money(50)` | 50 | `won` | 인자 있는 생성자 |

- ★★★ **「구조체에 매개변수 없는 생성자를 못 쓴다」는 C# 9 까지의 이야기**다.\
  **C# 10부터** 필드 초기자(`public int Won = 100;`)와 `public Money() { }` 가 된다.
- ★★★ **그런데 「항상 불린다」는 보장이 여전히 없다.**\
  `default(T)` · **배열 할당** · `Array.Resize` · 제네릭의 `default(T)` 는\
  **생성자를 건너뛰고 모든 비트를 0 으로** 만든다. `a.Equals(b)` 가 **`False`** 인 것이 그 증거다.
- ★★ **결론 — 구조체에서 「0 이 아닌 기본값」에 기대면 안 된다.**\
  `default(T)` 가 **유효한 값**이 되도록 타입을 설계한다.\
  ★ **클래스와 갈리는 큰 자리**다 — 클래스는 생성자를 건너뛸 방법이 없다.

### 7. ★★ **+48** · **+0** · **+152** · **+48** — `this` 와 인자가 박싱된다

**출력**

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

**왜 그런가**

| 쓴 것 | 할당 | 왜 |
|---|---|---|
| `p1.Equals(p2)`(오버로드 없음) | ★ **+48** | ★★ **`this` 와 인자가 둘 다 박싱**된다(24 × 2) |
| `f1.Equals(f2)`(`IEquatable<Fast>`) | ★★★ **+0** | **`Equals(Fast)` 가 오버로드 해소에서 먼저 뽑힌다** |
| `r1.Equals(r2)`(`string` 필드가 있다) | ★★★ **+152** | ★★★ **리플렉션 경로**가 더 쓴다 |
| `object.Equals(p1, p2)` | **+48** | 매개변수가 `object` 둘이다 |

- ★★★ **`p1.Equals(p2)` 가 48 인 이유** — `Plain` 에는 `Equals` 오버라이드가 없어\
  `ValueType.Equals(object)` 가 뽑히고, **인자가 박싱**(24)되며 **`this` 도 박싱**(24)된다.\
  ★ 값 타입에서 **오버라이드되지 않은 기반 클래스 가상 메서드**를 부르려면 `this` 를 박싱해야 한다.
- ★★★ **`Plain`(48)과 `RefField`(152)가 갈리는 이유**는 CoreCLR 에 **두 경로**가 있기 때문이다 —\
  **참조를 하나도 안 품은 구조체**는 바이트를 통째로 비교할 수 있고,\
  **참조 필드가 있으면** 필드를 하나씩 돌며 각각의 `Equals` 를 부른다.\
  ★ 그 갈림은 [01번](../01-value-types-and-reference-types/)의 (8)에서 `IsReferenceOrContainsReferences<T>()` 로 봤다.
- ★★★ **`IEquatable<Fast>` 하나로 48 이 0 이 된다.** 이것이 구조체를 만들 때 반드시 같이 하는 일이다.

### 8. ★ 약 **10배**와 약 **40배** — 절댓값이 아니라 자릿수가 근거다

**출력**

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

**왜 그런가**

- ★★ **다섯 판이 전부 같은 자릿수**다 — `Fast` **3\~4** · `Plain` **34\~38** · `RefField` **144\~149** ns.
- ★★★ **제출 직전에 다시 돌렸더니 이 칸이 움직였다** — `Plain` **37\~41** · `RefField` **129\~140** · `Fast` **3\~4**.\
  ★ **처음 값을 지우지 않고 나란히 적는다** — **움직였다는 사실 자체가 이 칸이 흔들린다는 증거**다.\
  ★★ **안 움직인 것은 비율**이다 — 두 판 모두 `Fast` 대비 `Plain` 이 **약 10배**, `RefField` 가 **약 40배**였다.
- ★★★ **신호 대 잡음** — 한 판 안의 다섯 줄이 **15% 안쪽**, 캡처를 다시 돌리면 **20% 까지** 움직이는데\
  **열 사이 차이는 10배와 40배**다.\
  신호가 잡음보다 훨씬 커서 **순서가 뒤집힐 여지가 없다.**
- ★★★ **근거로 쓰는 것은 「약 10배·약 40배」이지 `4 ns` 나 `146 ns` 가 아니다.**\
  ns 절댓값은 **흔들리는 칸**이다 — 머신이 바뀌면 전부 바뀐다.
- ★ **측정 조건** — `Stopwatch`, **1,000,000회 반복의 평균**, **워밍업 3회**(JIT 계층 승격을 측정 밖으로 뺐다),\
  **델리게이트를 안 끼우고** 루프를 각각 직접 돌았다. **전용 벤치마크 도구는 안 썼다.**
- ★★ **「`struct` 가 `class` 보다 빠르다」를 이 측정으로 말할 수 없다.**\
  잰 것은 **`Equals` 한 축**이고, 그것도 **구조체끼리의 비교**다.

### 9. ★★ 넷 다 자동으로 오고, `Equals` 할당은 **+0** 이다

**출력**

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

**왜 그런가**

| 얻은 것 | 결과 |
|---|---|
| `ToString()` | `Money { Won = 100, Currency = KRW }` |
| `==` · `Equals` | **값 비교**(`True`) |
| `GetHashCode()` | 값이 같으면 같다 |
| 해체 · `with` | 된다 |
| ★★★ **`Equals` 할당** | ★★★ **+0 바이트** |

- ★★★ **`record struct` 는 `IEquatable<T>` 를 자동으로 구현한다** — 그래서 7번의 `Fast` 와 같은 **+0** 이다.\
  손으로 `Equals`·`GetHashCode` 를 짜는 일이 **통째로 없어진다.**
- ★★ **`readonly record struct` 는 속성이 `init` 전용**이라 대입이 막힌다.

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

- ★ ``error CS8852: Init-only property or indexer 'Money.Won' can only be assigned in an object initializer …`` —\
  「바꾸려면 `with` 를 쓰라」는 뜻이다.
- ★★ **`readonly` 를 빼면** 속성이 **`get`/`set`** 이 되어 이 에러가 안 나고,\
  대신 **3번의 방어적 복사 문제가 되돌아온다.** ★ **이 문서는 `readonly record struct` 만 던졌다.**

### 10. ★ 상속은 못 하고 인터페이스는 된다 — 다만 올리면 박싱된다

**왜 그런가**

- **구조체는 `System.ValueType` 을 상속하고, 그 밖의 상속은 못 한다.** `sealed` 인 셈이다.\
  ★ **인터페이스 구현은 된다** — 7번의 `Fast : IEquatable<Fast>` 가 그 예다.
- ★★ **그런데 인터페이스 타입 변수에 담으면 박싱된다.** 정본은 [03번](../03-boxing-and-unboxing/)이고,\
  **제네릭 제약**(`where T : IEquatable<T>`)이 그것을 피하는 법이다.
- **구조체에 `null` 을 넣으려면 `T?`**(`Nullable<T>`)가 필요하다 —\
  [01번](../01-value-types-and-reference-types/)의 (7)이 정본이다.

### 11. 잇는 자리

- **「대입이 무엇을 복사하나」** — [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/).\
  ★ 1번의 크기 이야기가 거기 (8)에서 시작하고, 7번의 두 경로도 거기 (8)에서 갈렸다.
- **박싱** — [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/). 7번의 **+48** 이 거기서 정본이 된다.
- **`ref`/`out`/`in` 자체** — 목록의 **44번 주제**.
- **`record` 문법 전반** — 목록의 **18번 주제**(`record class` 와의 대비가 거기다).\
  **`Equals`/`GetHashCode` 계약** — 목록의 **19번 주제**.
- **「값이냐 헤더냐」가 축인 다른 갈래** — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **05번**.\
  ★★ 거기도 「대입이 무엇을 복사하나」가 축이지만, **Go 에는 `readonly` 가 없어 방어적 복사가 없다.**\
  ★ **이 함정은 C# 고유**다 — 「불변을 타입에 새길 수 있게 한 언어」만이 그 대가로 갖는다.
- **선택 논증** — [`../../c-cpp-csharp.md`](../../../c-cpp-csharp.md). *거기는 「왜 이 언어인가」, 여기는 「무엇을 고르나」.*

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64** 에서\
캡처 스크립트로 받았다. **제출 직전에 전부 다시 돌려 `diff -rq` 로 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs02b-size.cs` | `Big[1000]` **+64024** · `BigCls[1000]` **+8024** · 채우면 **+80000** | `csc` + 실행 |
| `cs02b-readonly.cs` | `error CS8340`(가변 필드) | `csc` 만 |
| `cs02b-readonly-write.cs` | `error CS0191` · ★ `error CS1604`(`this` 대입) | 〃 |
| `cs02b-defensive.cs` | ★★★ `readonly` 필드·`in` 에서 **`1 1 1` · N=0** | `csc` + 실행 |
| 〃 `-warn:9` | ★★★ **경고 0줄 · `cc exit=0`** | `csc -warn:9` |
| `cs02b-defensive-il.cs` | ★★★ `in` 에만 **`ldobj Counter` + `stloc.0`** | `csc -r:il.dll` + 실행 |
| `cs02b-ctor.cs` | `new Money()` **100** · `default` **0/null** | `csc` + 실행 |
| `cs02b-equals-alloc.cs` | ★★ **+48 · +0 · +152 · +48** | 〃 |
| `cs02b-equals-time.cs` | ★ **3\~4 / 34\~38 / 144\~149 ns**(5판) · ★★ 재실행에서 **3\~4 / 37\~41 / 129\~140** 으로 움직였다 | 〃 |
| `cs02b-record.cs` | `with`·해체·`==` · **`Equals` +0** | 〃 |
| `cs02b-record-mutate.cs` | `error CS8852`(init 전용) | `csc` 만 |

**구현 의존 항목** — 다음은 **이 환경(.NET 10.0.12 · CoreCLR · x64 linux)에서만** 그렇다.

- ★★★ **`Equals` 의 48·152바이트와 40배** — 「**두 경로가 있다**」가 관찰이고 **배수는 이 판의 수치**다.\
  판이 바뀌면 배수가 달라질 수 있다. **CoreCLR 소스를 읽어 확인하지는 않았다.**
- ★★★ **경고가 0줄인 것** — **컴파일러 구현**이다. **분석기를 켜면 달라진다**(이 문서는 안 켰다).
- ★★ **IL 명령 이름**(`ldobj`·`ldloca.s`) — Roslyn 의 코드 생성이다.\
  규칙은 「**읽기 전용 자리의 값은 안 바뀐다**」이고 **명령 이름이 규칙이 아니다.**
- ★ **객체 헤더 16바이트** · **80바이트 객체** — x64 CoreCLR 기준.
- ★ **ns 절댓값** — 머신·CPU 상태에 달렸다. **비율만** 근거로 쓴다.
- 진단 문구·진단 코드 — Roslyn 구현.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`readonly struct` 의 필드가 전부 `readonly` 여야 하는** 것 · **`this` 대입이 막히는** 것.
- ★★★ **읽기 전용 자리의 구조체 값이 안 바뀌는** 것 — **방어적 복사는 그 규칙의 귀결**이다.
- **C# 10부터 구조체 필드 초기자·매개변수 없는 생성자가 되는** 것.
- **`default(T)`·배열 할당이 생성자를 건너뛰는** 것(모든 비트 0).
- **기본 `Equals` 의 시그니처가 `object` 라 박싱이 필요한** 것.
- **`record struct` 가 값 동등성·`ToString`·해체·`with` 를 만들어 주는** 것 · **`readonly` 면 `init` 전용인** 것.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **`readonly` 멤버**(C# 8 — 타입이 아니라 메서드에 붙이는 것) ·\
  **`record struct`(`readonly` 없는 것)** · **`ref struct`**(목록의 **45번 주제**) ·\
  **외부 분석기를 켠 판**(4번의 「경고 0줄」이 달라질 수 있다) · **`Equals` 두 경로의 CoreCLR 소스** ·\
  **32비트 런타임** · **서버 GC**.
- **못 잰 것** — ★★ **「구조체 복사 비용」 자체.**\
  1번이 잰 것은 **할당**이고, 8번이 잰 것은 **`Equals` 한 축**이다.\
  복사 비용은 「크기 × 대입·전달 횟수」인데 **그것을 재려면 크기를 바꿔 가며 도는 하네스**가 필요하다.\
  ★ 그래서 이 문서는 **「크면 느리다」를 수치로 말하지 않았다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번의 「경고 0줄」** — Roslyn 이 이 자리에 경고를 넣으면 **이 주제의 결론이 바뀐다.**
- ★ **5번의 IL**(`ldobj` 가 남아 있나).
- ★ **7번의 48·152** · **8번의 배수** — 런타임 최적화가 바뀌면 움직인다.
- **진단 문구와 진단 코드**(2·9번).
