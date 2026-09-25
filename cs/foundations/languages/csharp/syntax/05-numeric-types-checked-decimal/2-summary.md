# csharp/syntax/05 — 기본 숫자 타입·`checked`/`unchecked`·`decimal` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — `checked`/`unchecked`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked) · [Learn — 널 허용 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-value-types) · [Learn — 널 허용 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types) · [Learn — 멤버 접근·널 조건 연산자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 첫 줄(`// cs0Nb-….cs` 꼴)도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **진단 언어를 영어로 고정했다.** 안 주면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 01\~04 가 실측으로 받은 한국어 판이 ``error CS0029: 암시적으로 'string' 형식을 'int' 형식으로 변환할 수 없습니다.`` 였다.\
> 고정하는 법은 둘을 같이 거는 것이다 — 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`**.
> **던진 형태** — MSBuild(`dotnet build`·`dotnet run`)를 **안 썼다.** Roslyn 컴파일러를 **직접** 부른다 —\
> 그래야 `bin/`·`obj/` 가 원리상 안 생기고, 진단 경로가 **절대 경로가 아니라 파일명**으로 나오며, 한 판이 0.3초 안에 끝난다.\
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
>           -preferreduilang:en-US -langversion:latest "$@"; }
> ```
>
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.\
> 그래서 이 문서의 트레이스는 ``at Program.<Main>$(String[] args)`` 에서 끝나고, 어느 머신에서 돌려도 같다.\
> **IL 덤프는 `-optimize` 없이**(기본 디버그) 낸 것이라 `nop` 이 섞여 있고 소스 구조가 그대로 보인다.\
> IL 을 찍는 `cs-il.cs`(82줄, 외부 도구 없이 BCL 만 쓴다)의 전문은 [03번](../03-boxing-and-unboxing/2-summary.md)의 (0)절에 있다.
> **버전** — 정수·부동소수점 타입과 `checked`/`unchecked` 는 **C# 1.0부터**. `decimal` 도 **C# 1.0부터**다.\
> `nint`/`nuint`(네이티브 정수)는 **C# 9부터**, `Half` 는 **.NET 5부터**, 사용자 정의 `checked` 연산자는 **C# 11부터**다.\
> 이 문서는 그중 **C# 1.0부터 있는 것만** 다룬다 — 20년 넘게 안 바뀐 기본값이라 오히려 잊기 쉽다.
> **경계** — 「2진 표현이 어떻게 생겼나」·「IEEE 754 가 왜 0.1을 못 담나」의 정본은\
> [`foundations/data-representation/`](../../../../data-representation/)다. **여기는 그것이 아니라** 「**C# 에서 무엇을 고르나**」다 —\
> 같은 사실 위에서 갈래가 다르다. 저기는 **비트가 어떻게 놓이나**, 여기는 **`double` 과 `decimal` 중 무엇을 쓰고 그 대가가 무엇인가**.\
> 값 타입이 무엇인지는 [01번](../01-value-types-and-reference-types/), 박싱은 [03번](../03-boxing-and-unboxing/)이 정본이다.\
> `enum` 이 정수 위의 껍데기라는 것은 목록의 **20번 주제**, 서식·문화권은 목록의 **48번 주제**다.\
> C 의 정수 승격·미정의 동작과는 **축이 다르다** — 그쪽은 C 갈래의 [정수 승격 편](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)이고,\
> 거기서는 **부호 있는 오버플로가 미정의 동작**인데 여기서는 **정의된 감김**이다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조는 이 표를 기준으로 판정한다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **`GC.GetAllocatedBytesForCurrentThread()` 의 절댓값**(프로세스 시작부터의 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | 시간·CPU 상태 — 이 문서는 **시간을 한 번도 안 쟀다** | **진단 코드**(`CS0220`·`CS8602` 류) · **진단 문구** · **`(행,열)`** |
> | 객체 주소 · `GetHashCode()` 의 참조형 값 | **`cc exit` 와 `run exit`**(갈라 적었다) |
> | `dotnet` 패치 버전이 오르면 달라질 수 있는 것 | **IL 명령어 열**(`add` · `add.ovf` · `box` · `brtrue.s` · `initobj`) |
> | — | **할당 바이트의 증분값**(24 · 32 · 0) · **타입 크기**(`Unsafe.SizeOf`) |

## 한눈에 — 쉽게 말하면

**C# 의 숫자 타입은 「자동차 주행거리계」와 「금전출납부」 두 부류로 갈린다.**

주행거리계는 999999 다음에 **000000 으로 조용히 돌아간다.** 경보음도 없고 기록도 안 남는다 —
정수 타입이 딱 그렇다. `int.MaxValue + 1` 이 **`int.MinValue` 가 되고, 아무 일도 안 일어난 것처럼 넘어간다.**

금전출납부는 다르다. 칸이 모자라면 **적을 수가 없으니 손이 멈춘다** — 그게 `checked` 다.
그리고 금전출납부는 **소수를 10진으로 적는다.** 「0.1」을 적으면 0.1 이지 0.1000000000000000055 가 아니다 — 그게 `decimal` 이다.

| 비유 | 실체 |
|---|---|
| **주행거리계가 한 바퀴 돈다** | `int.MaxValue + 1 == int.MinValue` — 예외도 경고도 없다((1)) |
| **「칸이 모자라면 멈춰라」라고 적어 둔다** | `checked(a + b)` → `OverflowException`((2)) |
| **인쇄된 장부에 애초에 못 적는다** | 상수식은 **컴파일 에러**다 — 실행까지 못 간다((3)) |
| **회사 규정으로 「항상 멈춤」을 건다** | `csc -checked+`(MSBuild 의 `CheckForOverflowUnderflow`)((4)) |
| ★★ **자로 잰 값 대 손으로 적은 값** | `double` 은 2진 근사, `decimal` 은 **10진 그대로**((6)) |
| ★ **장부는 칸이 넓고 쓰기 느리다** | `decimal` 은 16바이트 · 연산이 **명령이 아니라 메서드 호출**((7)·(8)) |

- ★★★ **이 주제의 한 줄** — C# 의 산술은 **기본이** 「**조용히 감기는 것**」이고,\
  「멈추는 것」은 **내가 켜야 켜진다.** 켜는 자리가 셋이다 — `checked` 식·`checked` 블록·컴파일러 플래그.
- ★★ **`decimal` 은 부동소수점이 아니다** — 지수가 2의 거듭제곱이 아니라 **10의 거듭제곱**이라\
  `0.1m` 이 오차 없이 담긴다((6)). 대신 **범위가 좁고(10^28 대 10^308) 크기가 두 배**다((7)).
- ★ **`decimal` 이 「항상 더 정확하다」는 아니다** — 나눗셈은 못 맞춘다((6)의 마지막 세 줄).

```text
   C# 산술의 기본값 한 장

   a + b  (a, b 는 정수)
     │
     ├─ 결과가 타입에 들어가나?  ──예──> 그 값
     │
     └─ 안 들어간다 ──> 지금 어느 맥락인가?
            │
            ├─ unchecked (★ 기본값)  ──> 넘치는 상위 비트를 버린다. 예외 없음. 경고 없음.
            │
            ├─ checked                ──> OverflowException
            │
            └─ 상수식 (컴파일 시점에 값이 정해짐)
                     └─ ★ 기본이 checked 다 ──> error CS0220 (실행까지 못 간다)
```

```text
   0.1 을 담는 두 가지 방법

   double  (2진 부동소수점, 8바이트)          decimal  (10진, 16바이트)
   ┌──────┬──────────┬──────────────┐        ┌────────────────────────────┬──────┐
   │ 부호 │ 지수 2^n │   가수(52비트) │        │        96비트 정수         │ 배율 │
   └──────┴──────────┴──────────────┘        └────────────────────────────┴──────┘
      0.1 = 1.6 × 2^-4  ← 2진으로 딱 안 떨어진다     0.1 = 1 × 10^-1  ← 딱 떨어진다
      실제로 담기는 값: 0.1000000000000000055…       실제로 담기는 값: 0.1

   0.1 + 0.2 == 0.3  →  False                0.1m + 0.2m == 0.3m  →  True
```

> **오버플로(overflow)** — 연산 결과가 그 타입이 담을 수 있는 범위를 벗어나는 것.\
> C# 의 정수는 기본적으로 **넘치는 상위 비트를 버리고** 남은 것을 결과로 삼는다(「감긴다」).

> **`checked` / `unchecked`** — 오버플로 검사 맥락을 지정하는 키워드.\
> 식(`checked(a + b)`)으로도 블록(`checked { … }`)으로도 쓴다. **기본은 `unchecked`** 다.

> **`decimal`** — 96비트 정수와 **10의 거듭제곱 배율**로 이루어진 16바이트 값 타입.\
> 「소수점 이하 자릿수」를 **값의 일부로 들고 다닌다** — `1.10m` 과 `1.1m` 은 같은 값인데 표기가 다르다((7)).

> **감김(wrap-around)** — 최댓값 다음이 최솟값으로 돌아가는 것.\
> 2의 보수 표현에서 상위 비트를 버리면 자연히 이렇게 된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **정수가 넘치면 무슨 일이 일어나나** — 그리고 **그 기본값을 어디서 뒤집을 수 있나**((1)\~(5)).
2. **돈을 `double` 로 담으면 무엇이 틀리나** — 그리고 `decimal` 이 그것을 어떻게 고치고 **무엇을 대가로 받나**((6)\~(8)).
3. **`==` 를 언제 믿으면 안 되나** — `double` 과 `decimal` 에서 각각 다른 이유로 걸린다((9)).

## 동작 방식

### (0) 이 주제가 쓰는 다섯 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| **실행 출력** | 감긴 값 · 자릿수 · 변환 결과 | (1)·(6)·(7)·(9) |
| **컴파일 진단** | ★★ **상수식은 실행까지 못 간다**(`CS0220`·`CS0031`) | (3) |
| **예외 전문** | `checked` 가 실제로 무엇을 던지나 | (2)·(5) |
| ★★★ **IL** | ★★★ **`add` 대 `add.ovf` 대 메서드 호출** — 소스만 봐서는 안 보이는 것 | (8) |
| **할당 바이트** | `decimal` 을 `object` 에 담을 때의 대가 | (7) |

★★★ **이 주제의 중심은 IL 이다.** C# 은 에러가 교재인 언어가 아니라서\
「`checked` 가 무엇을 바꾸나」를 소스만 봐서는 알 수 없다 — **명령어가 한 글자 바뀐다**(`add` → `add.ovf`).
**`decimal` 이 부동소수점이 아니라는 것**도 IL 이 한 줄로 말한다 — `add` 가 아니라 `call System.Decimal::op_Addition` 이다((8)).

★ **이 판이 무엇인지부터 찍어 둔다** — 아래 수치는 전부 이 판의 것이다.

```text
===== dotnet --version =====
10.0.401
```

```text
===== 소스: cs05b-env.cs =====
using System;
using System.Runtime;
using System.Runtime.InteropServices;

Console.WriteLine($"FrameworkDescription : {RuntimeInformation.FrameworkDescription}");
Console.WriteLine($"RuntimeIdentifier    : {RuntimeInformation.RuntimeIdentifier}");
Console.WriteLine($"OSArchitecture       : {RuntimeInformation.OSArchitecture}");
Console.WriteLine($"IntPtr.Size          : {IntPtr.Size}");
Console.WriteLine($"IsServerGC           : {GCSettings.IsServerGC}");
Console.WriteLine($"BitConverter.IsLittleEndian : {BitConverter.IsLittleEndian}");
===== csc -out:ex.dll cs05b-env.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
FrameworkDescription : .NET 10.0.12
RuntimeIdentifier    : linux-x64
OSArchitecture       : X64
IntPtr.Size          : 8
IsServerGC           : False
BitConverter.IsLittleEndian : True
```

| 칸 | 값 | 이 문서에서 |
|---|---|---|
| `dotnet --version` | **`10.0.401`**(SDK) | 컴파일러 판 |
| `FrameworkDescription` | **`.NET 10.0.12`** | 런타임 판 — ★ 부동소수점→정수 변환 결과가 여기 달렸다 |
| 타겟 프레임워크 | **`net10.0`** | `ex.runtimeconfig.json` 의 `tfm` |
| `IntPtr.Size` | ★ **8** | ★ **x64** — (7)의 할당 바이트가 여기 달렸다 |
| `IsLittleEndian` | **`True`** | `decimal.GetBits` 를 읽을 때의 전제((7)) |

### (1) ★★★ 정수 오버플로는 기본으로 조용하다

**언제 쓰나** — 이 주제에서 **가장 먼저 무는 자리.** 「터지겠지」라고 생각한 곳이 안 터진다.

```text
===== 소스: cs05b-wrap.cs =====
using System;

int big = int.MaxValue;
int wrapped = big + 1;
Console.WriteLine($"int.MaxValue      = {big}");
Console.WriteLine($"int.MaxValue + 1  = {wrapped}      ← 예외도 경고도 없다");

byte b = 255;
b++;
Console.WriteLine($"(byte)255  에 ++   = {b}");

short s = short.MinValue;
s--;
Console.WriteLine($"short.MinValue-- = {s}");

uint u = 0;
u--;
Console.WriteLine($"(uint)0 에 --      = {u}");

int explicitly = unchecked(big + 1);
Console.WriteLine($"unchecked(…+1)    = {explicitly}  ← 기본값을 글자로 적은 것뿐이다");

long widened = (long)big + 1;
Console.WriteLine($"(long)int.MaxValue + 1 = {widened}  ← 타입을 넓히면 감기지 않는다");
===== csc -out:ex.dll cs05b-wrap.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int.MaxValue      = 2147483647
int.MaxValue + 1  = -2147483648      ← 예외도 경고도 없다
(byte)255  에 ++   = 0
short.MinValue-- = 32767
(uint)0 에 --      = 4294967295
unchecked(…+1)    = -2147483648  ← 기본값을 글자로 적은 것뿐이다
(long)int.MaxValue + 1 = 2147483648  ← 타입을 넓히면 감기지 않는다
```

- ★★★ **여섯 줄 전부 예외도 경고도 없다.** 컴파일러는 한 글자도 말하지 않았다 —\
  `cc exit=0` 이고 진단이 **0줄**이다. 「**에러가 교재인 언어**」와 정반대인 자리다.
- **`(byte)255` 에 `++` 가 `0`** 인 것이 그 성질을 가장 짧게 보인다. 255 + 1 = 256 = `1_0000_0000`(2진) 인데\
  `byte` 가 하위 8비트만 들고 있으므로 `0000_0000` 이 남는다.
- ★ **`unchecked(…)` 를 적는 것은 기본값을 글자로 적은 것뿐**이다 — 결과가 같다.\
  쓸 일은 **주변이 `checked` 일 때 한 군데만 풀 때**다.
- ★★ **타입을 넓히면 감기지 않는다** — `(long)int.MaxValue + 1` 은 `2147483648` 이다.\
  ★ 여기서 순서가 중요하다. `(long)(int.MaxValue + 1)` 은 **`int` 로 더한 뒤 넓히므로 여전히 감긴다.**

### (2) `checked` 가 바꾸는 것 — 예외 전문

**언제 쓰나** — 「조용히 틀린 값」보다 「시끄럽게 멈추는 것」이 나은 자리(금액·수량·인덱스 계산).

```text
===== 소스: cs05b-checked.cs =====
using System;

int big = int.MaxValue;
int boom = checked(big + 1);
Console.WriteLine(boom);
===== csc -out:ex.dll cs05b-checked.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.OverflowException: Arithmetic operation resulted in an overflow.
   at Program.<Main>$(String[] args)
```

- **`OverflowException`** 하나뿐이고 메시지는 `Arithmetic operation resulted in an overflow.` 다.\
  ★ **어느 연산이 넘쳤는지는 메시지에 없다** — `-debug` 를 안 줬으므로 줄 번호도 없다.
- ★ **종료 코드가 134 다** — 처리되지 않은 예외로 죽은 .NET 프로세스의 코드다(01\~04 와 같다).
- 잡아서 보면 타입·메시지가 이렇다. **세 자리에서 같은 예외가 나고, 넷째 줄만 다른 예외다.**

```text
===== 소스: cs05b-catch.cs =====
using System;

int big = int.MaxValue;
try { int boom = checked(big + 1); Console.WriteLine(boom); }
catch (OverflowException e) {
    Console.WriteLine($"타입    : {e.GetType().FullName}");
    Console.WriteLine($"메시지  : {e.Message}");
}

try { checked { int a = big; int c = a * 2; Console.WriteLine(c); } }
catch (OverflowException e) { Console.WriteLine($"checked 블록: {e.Message}"); }

byte bb = 255;
try { bb = checked((byte)(bb + 1)); Console.WriteLine(bb); }
catch (OverflowException e) { Console.WriteLine($"checked 캐스트: {e.Message}"); }

int z = 0;
try { Console.WriteLine(unchecked(1 / z)); }
catch (DivideByZeroException e) { Console.WriteLine($"unchecked(1 / 0) → {e.GetType().Name}: {e.Message}"); }
===== csc -out:ex.dll cs05b-catch.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
타입    : System.OverflowException
메시지  : Arithmetic operation resulted in an overflow.
checked 블록: Arithmetic operation resulted in an overflow.
checked 캐스트: Arithmetic operation resulted in an overflow.
unchecked(1 / 0) → DivideByZeroException: Attempted to divide by zero.
```

- ★★ **마지막 줄이 갈래가 다르다** — `1 / 0` 은 **`unchecked` 인데도 던진다.**\
  `checked` 가 지배하는 것은 「**넘침**」이고, **0 으로 나누기는 맥락과 무관하게 `DivideByZeroException`** 이다.\
  ★ 「`unchecked` 면 아무것도 안 던진다」로 외우면 여기서 틀린다.

### (3) ★★ 상수식은 실행까지 가지도 못한다

**언제 쓰나** — 「던져 보면 알겠지」가 안 통하는 자리. **컴파일러가 먼저 잡는다.**

```text
===== 소스: cs05b-const.cs =====
using System;

int a = int.MaxValue + 1;
const int b = checked(int.MaxValue + 1);
byte c = 300;
int d = unchecked(int.MaxValue + 1);
Console.WriteLine($"{a} {b} {c} {d}");
===== csc -out:ex.dll cs05b-const.cs (cc exit=1) =====
cs05b-const.cs(3,9): error CS0220: The operation overflows at compile time in checked mode
cs05b-const.cs(4,23): error CS0220: The operation overflows at compile time in checked mode
cs05b-const.cs(5,10): error CS0031: Constant value '300' cannot be converted to a 'byte'
```

- ★★★ **3번 줄에는 `checked` 라는 글자가 없는데도 `CS0220` 이 났다.**\
  **상수식의 기본 맥락은 `checked`** 이기 때문이다 — 실행 시점 기본값(`unchecked`)과 **정반대**다.
- **4번 줄**은 `checked` 를 명시했고 같은 에러가 난다. **3번과 4번이 같은 코드**인 셈이다.
- **5번 줄** `byte c = 300;` 은 에러 번호가 다르다 — **`CS0031`**(상수 변환). 넘침이 아니라 **변환**으로 잡힌 것이다.
- ★★ **6번 줄 `int d = unchecked(int.MaxValue + 1);` 은 통과했다.**\
  진단이 3줄뿐이고 6번 줄이 없는 것이 그 근거다 — **상수식의 검사도 명시적으로 끌 수 있다.**

### (4) ★ 프로젝트 기본값을 바꾸는 플래그

**언제 쓰나** — 「우리 코드베이스는 전부 멈추게 하자」를 결정할 때. MSBuild 에서는\
`<CheckForOverflowUnderflow>true</CheckForOverflowUnderflow>` 이고, 그것이 `csc` 에 주는 것이 **`-checked+`** 다.

**같은 소스를 플래그만 바꿔 두 번 던졌다.**

```text
===== 소스: cs05b-flag.cs =====
using System;

int big = int.MaxValue;
Console.WriteLine($"int.MaxValue + 1 = {big + 1}");
===== csc -out:ex.dll cs05b-flag.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int.MaxValue + 1 = -2147483648
```

```text
===== 소스: cs05b-flag.cs =====
using System;

int big = int.MaxValue;
Console.WriteLine($"int.MaxValue + 1 = {big + 1}");
===== csc -checked+ -out:ex.dll cs05b-flag.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.OverflowException: Arithmetic operation resulted in an overflow.
   at Program.<Main>$(String[] args)
```

- ★★ **소스가 한 글자도 안 바뀌었는데 결과가 갈렸다** — `run exit=0` 대 `run exit=134`.
- ★★★ **그래서 「이 코드는 감긴다」는 소스만 보고는 말할 수 없다.** 빌드 설정을 같이 봐야 한다.\
  **라이브러리를 쓸 때 특히 위험하다** — 내 프로젝트가 `-checked+` 여도 **남의 어셈블리 안쪽은 그 어셈블리를 빌드한 설정**을 따른다.
- ★ 이 플래그는 **비상수식만** 바꾼다. 상수식은 (3)에서 본 대로 **언제나 `checked`** 다.

### (5) `checked` 의 범위는 「글자 그대로 안쪽」이다

**언제 쓰나** — `checked` 블록으로 감쌌는데 안 터질 때. **가장 자주 오해하는 자리다.**

```text
===== 소스: cs05b-textual.cs =====
using System;

int factor = 2;

try {
    checked { Console.WriteLine($"Multiply(factor, int.MaxValue) = {Multiply(factor, int.MaxValue)}"); }
} catch (OverflowException e) { Console.WriteLine($"  터짐: {e.Message}"); }

try {
    checked { Console.WriteLine(Multiply(factor, factor * int.MaxValue)); }
} catch (OverflowException e) { Console.WriteLine($"  인자 계산에서 터짐: {e.Message}"); }

static int Multiply(int a, int b) => a * b;
===== csc -out:ex.dll cs05b-textual.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Multiply(factor, int.MaxValue) = -2
  인자 계산에서 터짐: Arithmetic operation resulted in an overflow.
```

- ★★★ **첫 줄이 `-2` 다.** `checked` 블록 **안에서 부른** `Multiply` 가 **안 터졌다.**\
  `checked` 는 **호출 스택을 따라 전파되지 않는다** — `Multiply` 의 본문은 그 블록의 **글자 바깥**이기 때문이다.
- **둘째 줄은 터졌다.** `factor * int.MaxValue` 는 **인자 계산식이라 블록의 글자 안쪽**이다.
- ★ 이것이 (4)의 플래그가 필요한 이유다 — **메서드 경계를 넘는 보장은 블록으로는 못 만든다.**

### (6) ★★★ `decimal` 은 부동소수점이 아니다

**언제 쓰나** — 돈·수량·비율처럼 **사람이 10진으로 쓴 값을 그대로 보존해야 하는** 자리.

```text
===== 소스: cs05b-money.cs =====
using System;

double d = 0.1 + 0.2;
decimal m = 0.1m + 0.2m;
Console.WriteLine($"0.1  + 0.2   (double)  = {d}");
Console.WriteLine($"0.1m + 0.2m  (decimal) = {m}");
Console.WriteLine($"0.1  + 0.2  == 0.3     : {d == 0.3}");
Console.WriteLine($"0.1m + 0.2m == 0.3m    : {m == 0.3m}");
Console.WriteLine($"(0.1 + 0.2).ToString(\"G17\") = {d.ToString("G17")}");
Console.WriteLine($"     0.3   .ToString(\"G17\") = {(0.3).ToString("G17")}");
Console.WriteLine();

double ds = 0;  for (int k = 0; k < 10; k++) ds += 0.1;
decimal ms = 0; for (int k = 0; k < 10; k++) ms += 0.1m;
Console.WriteLine($"0.1  을 10번 더하기 = {ds.ToString("G17")}  == 1.0  ? {ds == 1.0}");
Console.WriteLine($"0.1m 을 10번 더하기 = {ms}                 == 1.0m ? {ms == 1.0m}");
Console.WriteLine();

Console.WriteLine($"1m / 3m          = {1m / 3m}");
Console.WriteLine($"1m / 3m * 3m     = {1m / 3m * 3m}   ← decimal 도 나눗셈은 못 맞춘다");
Console.WriteLine($"1.0 / 3.0 * 3.0  = {1.0 / 3.0 * 3.0}                              ← double 은 여기서 되돌아온다");
===== csc -out:ex.dll cs05b-money.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
0.1  + 0.2   (double)  = 0.30000000000000004
0.1m + 0.2m  (decimal) = 0.3
0.1  + 0.2  == 0.3     : False
0.1m + 0.2m == 0.3m    : True
(0.1 + 0.2).ToString("G17") = 0.30000000000000004
     0.3   .ToString("G17") = 0.29999999999999999

0.1  을 10번 더하기 = 0.99999999999999989  == 1.0  ? False
0.1m 을 10번 더하기 = 1.0                 == 1.0m ? True

1m / 3m          = 0.3333333333333333333333333333
1m / 3m * 3m     = 0.9999999999999999999999999999   ← decimal 도 나눗셈은 못 맞춘다
1.0 / 3.0 * 3.0  = 1                              ← double 은 여기서 되돌아온다
```

- ★★★ **첫 두 줄이 이 주제의 그림이다.** 같은 산술인데 `double` 은 `0.30000000000000004`, `decimal` 은 `0.3` 이다.
- ★★ **`0.3` 자체가 이미 틀렸다** — `G17` 로 찍은 `0.3` 이 `0.29999999999999999` 다.\
  「`0.1 + 0.2` 가 틀린 것」이 아니라 **세 숫자가 전부 근사값**이고, 근사의 방향이 달라 `==` 가 깨진 것이다.
- **누산은 더 나쁘다** — `0.1` 을 10번 더하면 `0.99999999999999989` 다. **오차가 쌓인다.**
- ★★★ **마지막 세 줄이 반증이다.** 「`decimal` 이 더 정확하다」는 **나눗셈에서 뒤집힌다** —\
  `1m / 3m * 3m` 은 `0.9999999999999999999999999999` 인데 `1.0 / 3.0 * 3.0` 은 **`1`** 이다.\
  `double` 은 자릿수가 적어서 **반올림이 원래 값으로 되돌려 준** 것이고, `decimal` 은 28자리를 충실히 들고 있어 **되돌아오지 못한** 것이다.\
  ★ **`decimal` 이 고치는 것은 「10진 리터럴의 보존」이지 「모든 산술의 정확성」이 아니다.**

### (7) ★ `decimal` 의 대가 — 크기·할당·자릿수

**언제 쓰나** — 「그럼 전부 `decimal` 쓰면 되지 않나」에 답할 때.

```text
===== 소스: cs05b-cost.cs =====
using System;
using System.Runtime.CompilerServices;

Warm();

double d = 1.5;
decimal m = 1.5m;
int i = 1;

long a0 = GC.GetAllocatedBytesForCurrentThread();
object o1 = i;
long a1 = GC.GetAllocatedBytesForCurrentThread();
object o2 = d;
long a2 = GC.GetAllocatedBytesForCurrentThread();
object o3 = m;
long a3 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"Unsafe.SizeOf<int>()      = {Unsafe.SizeOf<int>(),2}바이트");
Console.WriteLine($"Unsafe.SizeOf<double>()   = {Unsafe.SizeOf<double>(),2}바이트");
Console.WriteLine($"Unsafe.SizeOf<decimal>()  = {Unsafe.SizeOf<decimal>(),2}바이트");
Console.WriteLine($"object o = int      : +{a1 - a0} 바이트");
Console.WriteLine($"object o = double   : +{a2 - a1} 바이트");
Console.WriteLine($"object o = decimal  : +{a3 - a2} 바이트");
Console.WriteLine($"({o1} {o2} {o3})");
Console.WriteLine();

Console.WriteLine($"decimal.GetBits(0.1m)   = [{string.Join(", ", decimal.GetBits(0.1m))}]");
Console.WriteLine($"decimal.GetBits(1.10m)  = [{string.Join(", ", decimal.GetBits(1.10m))}]");
Console.WriteLine($"decimal.GetBits(1.1m)   = [{string.Join(", ", decimal.GetBits(1.1m))}]");
Console.WriteLine($"1.10m == 1.1m           : {1.10m == 1.1m}");
Console.WriteLine($"1.10m.ToString()        : {1.10m}      ← 값은 같은데 자릿수는 남는다");
Console.WriteLine($"1.10m.GetHashCode() == 1.1m.GetHashCode() : {1.10m.GetHashCode() == 1.1m.GetHashCode()}");

static void Warm() {
    object w1 = 1; object w2 = 1.0; object w3 = 1m;
    GC.KeepAlive(w1); GC.KeepAlive(w2); GC.KeepAlive(w3);
    GC.GetAllocatedBytesForCurrentThread();
}
===== csc -out:ex.dll cs05b-cost.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Unsafe.SizeOf<int>()      =  4바이트
Unsafe.SizeOf<double>()   =  8바이트
Unsafe.SizeOf<decimal>()  = 16바이트
object o = int      : +24 바이트
object o = double   : +24 바이트
object o = decimal  : +32 바이트
(1 1.5 1.5)

decimal.GetBits(0.1m)   = [1, 0, 0, 65536]
decimal.GetBits(1.10m)  = [110, 0, 0, 131072]
decimal.GetBits(1.1m)   = [11, 0, 0, 65536]
1.10m == 1.1m           : True
1.10m.ToString()        : 1.10      ← 값은 같은데 자릿수는 남는다
1.10m.GetHashCode() == 1.1m.GetHashCode() : True
```

- **크기가 두 배다** — `double` 8바이트, `decimal` 16바이트. 배열·구조체에 넣으면 그대로 두 배가 된다.
- ★ **박싱하면 +24 대 +32 바이트**다((03번)의 박싱과 같은 계산 — 객체 헤더 16 + 값).\
  ★★ `double` 이 8바이트인데도 +24 인 것은 **최소 객체 크기** 때문이다. `decimal` 은 16바이트라 32로 넘어갔다.
- ★★★ **`decimal.GetBits` 가 구조를 드러낸다** — `0.1m` 은 `[1, 0, 0, 65536]` 이다.\
  앞 세 칸이 **96비트 정수 `1`**, 마지막 칸이 **배율(`65536` = `1 << 16`, 즉 10^-1)** 이다. **2의 지수가 어디에도 없다.**
- ★★ **`1.10m` 과 `1.1m` 은 값이 같은데 비트가 다르다** — `[110, 0, 0, 131072]` 대 `[11, 0, 0, 65536]`.\
  `==` 도 `True`, `GetHashCode()` 도 같은데 **`ToString()` 이 `1.10` 과 `1.1` 로 갈린다.**\
  ★ **자릿수가 값의 일부로 살아 있다** — 「5,000원」과 「5,000.00원」을 구분해 찍어야 하는 회계에서 이게 기능이다.

### (8) ★★★ IL — `checked` 와 `decimal` 이 명령으로 드러난다

**언제 쓰나** — 「소스만 봐서는 안 보이는 것」을 볼 때. **이 절이 이 주제의 중심이다.**

```text
===== 소스: cs05b-il.cs =====
Il.Dump(typeof(Probe), "AddInt");
Il.Dump(typeof(Probe), "AddIntChecked");
Il.Dump(typeof(Probe), "AddDouble");
Il.Dump(typeof(Probe), "AddDecimal");
Il.Dump(typeof(Probe), "ToInt");
Il.Dump(typeof(Probe), "ToIntChecked");

public static class Probe {
    public static int     AddInt(int a, int b)             => a + b;
    public static int     AddIntChecked(int a, int b)      => checked(a + b);
    public static double  AddDouble(double a, double b)    => a + b;
    public static decimal AddDecimal(decimal a, decimal b) => a + b;
    public static int     ToInt(double a)                  => (int)a;
    public static int     ToIntChecked(double a)           => checked((int)a);
}
===== csc -r:il.dll -out:ex.dll cs05b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.AddInt ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: add
  IL_0003: ret
--- Probe.AddIntChecked ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: add.ovf
  IL_0003: ret
--- Probe.AddDouble ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: add
  IL_0003: ret
--- Probe.AddDecimal ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: call System.Decimal::op_Addition
  IL_0007: ret
--- Probe.ToInt ---
  IL_0000: ldarg.0
  IL_0001: conv.i4
  IL_0002: ret
--- Probe.ToIntChecked ---
  IL_0000: ldarg.0
  IL_0001: conv.ovf.i4
  IL_0002: ret
```

| 소스 | IL | 읽는 법 |
|---|---|---|
| `a + b` (`int`) | `add` | 넘침을 **안 본다** |
| `checked(a + b)` (`int`) | ★★★ **`add.ovf`** | 명령이 **한 글자 다르다.** 넘치면 CPU 플래그를 보고 던진다 |
| `a + b` (`double`) | `add` | ★ `int` 와 **같은 명령**이다 — 피연산자 타입이 동작을 정한다 |
| `a + b` (`decimal`) | ★★★ **`call System.Decimal::op_Addition`** | **명령이 아니라 메서드 호출**이다 |
| `(int)a` (`double`→`int`) | `conv.i4` | 잘라 담는다 |
| `checked((int)a)` | ★ **`conv.ovf.i4`** | 변환에도 `.ovf` 판이 따로 있다 |

- ★★★ **`decimal` 줄이 이 주제의 결론이다.** CPU 에 「10진 덧셈」 명령이 없으므로\
  `decimal` 의 산술은 **전부 BCL 메서드 호출**이다. **「느리다」를 주장하지 않는다** —\
  이 문서는 **시간을 한 번도 재지 않았다.** 대신 「**명령 하나가 아니라 호출 하나다**」라는 사실만 싣는다.
- ★★ **`add` 와 `add.ovf` 가 같은 자리에 오는 것**이 (4)의 플래그가 하는 일을 설명한다 —\
  컴파일러가 **어느 명령을 찍을지 고르는 것**이지, 런타임이 설정을 읽는 것이 아니다.

### (9) ★ `==` 를 언제 믿으면 안 되나

**언제 쓰나** — 부동소수점 비교가 걸린 코드를 리뷰할 때.

```text
===== 소스: cs05b-eq.cs =====
using System;

double a = 0.1 + 0.2;
double b = 0.3;
Console.WriteLine($"a == b            : {a == b}");
Console.WriteLine($"a - b             : {(a - b).ToString("E3")}");
Console.WriteLine($"Math.Abs(a-b) < 1e-9 : {Math.Abs(a - b) < 1e-9}");
Console.WriteLine();

double nan = 0.0 / 0.0;
Console.WriteLine($"nan == nan        : {nan == nan}");
Console.WriteLine($"nan != nan        : {nan != nan}");
Console.WriteLine($"double.IsNaN(nan) : {double.IsNaN(nan)}");
Console.WriteLine($"nan.Equals(nan)   : {nan.Equals(nan)}   ← 연산자와 어긋난다");
Console.WriteLine($"Array.IndexOf(new[]{{nan}}, nan) = {Array.IndexOf(new[]{ nan }, nan)}");
Console.WriteLine();

double zp = 0.0, zm = -0.0;
Console.WriteLine($"0.0 == -0.0       : {zp == zm}");
Console.WriteLine($"0.0.Equals(-0.0)  : {zp.Equals(zm)}");
Console.WriteLine($"1.0 / -0.0        : {1.0 / zm}");
Console.WriteLine();

float f = 0.1f;
double widened = f;
Console.WriteLine($"(double)0.1f      : {widened.ToString("G17")}");
Console.WriteLine($"       0.1        : {(0.1).ToString("G17")}");
Console.WriteLine($"(double)0.1f == 0.1 : {widened == 0.1}");
===== csc -out:ex.dll cs05b-eq.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs05b-eq.cs(11,42): warning CS1718: Comparison made to same variable; did you mean to compare something else?
cs05b-eq.cs(12,42): warning CS1718: Comparison made to same variable; did you mean to compare something else?
a == b            : False
a - b             : 5.551E-017
Math.Abs(a-b) < 1e-9 : True

nan == nan        : False
nan != nan        : True
double.IsNaN(nan) : True
nan.Equals(nan)   : True   ← 연산자와 어긋난다
Array.IndexOf(new[]{nan}, nan) = 0

0.0 == -0.0       : True
0.0.Equals(-0.0)  : True
1.0 / -0.0        : -∞

(double)0.1f      : 0.10000000149011612
       0.1        : 0.10000000000000001
(double)0.1f == 0.1 : False
```

- ★★ **컴파일러가 `CS1718` 로 먼저 경고했다** — `nan == nan` 을 보고 「같은 변수끼리 비교하는데 의도한 게 맞나」라고 묻는다.\
  ★ **경고도 출력이다.** 이 경고가 있다는 것 자체가 「이 비교가 이상하다」는 언어의 신호다.
- **`nan == nan` 은 `False`, `nan.Equals(nan)` 은 `True`** — **연산자와 메서드가 어긋난다.**\
  ★ 그래서 `Array.IndexOf(new[]{nan}, nan)` 이 **`0`** 이다(`IndexOf` 는 `Equals` 를 쓴다).\
  ★★ **`==` 로는 못 찾는 값을 컬렉션은 찾아낸다** — 사전·집합에서 조용히 갈리는 자리다.
- **`0.0 == -0.0` 도 `True` 이고 `Equals` 도 `True`** 인데 **`1.0 / -0.0` 은 `-∞`** 다.\
  ★ 「같은 값」인데 **나눗셈의 부호가 갈린다.**
- ★★ **`(double)0.1f != 0.1`** — `float` 을 `double` 로 넓히는 것은 **정보를 더해 주지 않는다.**\
  `0.10000000149011612` 대 `0.10000000000000001`. ★ 「넓히니까 안전하겠지」가 틀리는 자리다.
- **처방** — 부동소수점은 `Math.Abs(a - b) < 허용오차` 로 비교하고, 허용오차는 **값의 크기에 비례**시킨다.\
  ★ 그리고 **애초에 `==` 가 성립해야 하는 값이면 `decimal` 이나 정수(원 단위)를 쓴다.**

## 문법 — 형태와 규칙

**크기와 범위 — 열세 종을 한 번에 찍어 둔다**

```text
===== 소스: cs05b-sizes.cs =====
using System;

Row("sbyte",   sizeof(sbyte),   sbyte.MinValue.ToString(),   sbyte.MaxValue.ToString());
Row("byte",    sizeof(byte),    byte.MinValue.ToString(),    byte.MaxValue.ToString());
Row("short",   sizeof(short),   short.MinValue.ToString(),   short.MaxValue.ToString());
Row("ushort",  sizeof(ushort),  ushort.MinValue.ToString(),  ushort.MaxValue.ToString());
Row("int",     sizeof(int),     int.MinValue.ToString(),     int.MaxValue.ToString());
Row("uint",    sizeof(uint),    uint.MinValue.ToString(),    uint.MaxValue.ToString());
Row("long",    sizeof(long),    long.MinValue.ToString(),    long.MaxValue.ToString());
Row("ulong",   sizeof(ulong),   ulong.MinValue.ToString(),   ulong.MaxValue.ToString());
Row("char",    sizeof(char),    ((int)char.MinValue).ToString(), ((int)char.MaxValue).ToString());
Row("bool",    sizeof(bool),    "false",                     "true");
Console.WriteLine();
Row("float",   sizeof(float),   float.MinValue.ToString(),   float.MaxValue.ToString());
Row("double",  sizeof(double),  double.MinValue.ToString(),  double.MaxValue.ToString());
Row("decimal", sizeof(decimal), decimal.MinValue.ToString(), decimal.MaxValue.ToString());
Console.WriteLine();
Console.WriteLine($"float   유효 자릿수 약 {7,2}  지수 표기 {float.Epsilon}");
Console.WriteLine($"double  유효 자릿수 약 {15,2}  지수 표기 {double.Epsilon}");
Console.WriteLine($"decimal 유효 자릿수 약 {28,2}  지수 표기 없음 — 배율이 10의 거듭제곱");

static void Row(string name, int size, string min, string max)
    => Console.WriteLine($"{name,-8}{size,3}바이트  {min,-31}{max}");
===== csc -out:ex.dll cs05b-sizes.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
sbyte     1바이트  -128                           127
byte      1바이트  0                              255
short     2바이트  -32768                         32767
ushort    2바이트  0                              65535
int       4바이트  -2147483648                    2147483647
uint      4바이트  0                              4294967295
long      8바이트  -9223372036854775808           9223372036854775807
ulong     8바이트  0                              18446744073709551615
char      2바이트  0                              65535
bool      1바이트  false                          true

float     4바이트  -3.4028235E+38                 3.4028235E+38
double    8바이트  -1.7976931348623157E+308       1.7976931348623157E+308
decimal  16바이트  -79228162514264337593543950335 79228162514264337593543950335

float   유효 자릿수 약  7  지수 표기 1E-45
double  유효 자릿수 약 15  지수 표기 5E-324
decimal 유효 자릿수 약 28  지수 표기 없음 — 배율이 10의 거듭제곱
```

- ★ **`decimal` 만 줄이 다르게 읽힌다** — 16바이트인데 범위가 `double` 보다 **훨씬 좁다**(`10^28` 대 `10^308`).\
  크기를 정밀도에 쓰고 범위를 포기한 것이다.
- ★ **`char` 가 숫자 타입처럼 나온다** — C# 의 `char` 는 **UTF-16 코드 단위**이고 정수와 산술이 된다.\
  `checked` 도 `char` 산술에 적용된다.
- ★★ **`float.Epsilon` 이 `1E-45` 인 것을 「정밀도」로 읽지 마라** — 그것은 **0 다음으로 작은 값**이지\
  「이만큼의 오차까지 정확하다」가 아니다. 비교 허용오차로 쓰면 틀린다.

**형태** — 던져서 확인한 것만 싣는다.

```text
===== 소스: cs05b-form.cs =====
using System;
using System.Runtime.CompilerServices;

// 리터럴 접미사 — 안 붙이면 int 또는 double 이다
var i  = 1;          // int
var l  = 1L;         // long   (U / UL 도 있다)
var d  = 1.0;        // double
var f  = 1.0f;       // float
var m  = 1.0m;       // decimal  ★ m 을 빼면 double 리터럴이 되어 오차가 먼저 생긴다
var hx = 0x_FF;      // 16진 + 자릿수 구분자(_ 는 C# 7.0부터)
var bn = 0b_1010;    // 2진 리터럴(C# 7.0부터)

Console.WriteLine($"1    → {i.GetType().Name,-8} 1L   → {l.GetType().Name}");
Console.WriteLine($"1.0  → {d.GetType().Name,-8} 1.0f → {f.GetType().Name}   1.0m → {m.GetType().Name}");
Console.WriteLine($"0x_FF = {hx}   0b_1010 = {bn}");

// 오버플로 검사 맥락 — 식 · 블록 · 컴파일러 플래그 셋이다
int x = int.MaxValue, y = 1;
Console.WriteLine($"unchecked 식   : {unchecked(x + y)}");
unchecked { Console.WriteLine($"unchecked 블록 : {x + y}"); }
try { checked { Console.WriteLine(x + y); } }
catch (OverflowException) { Console.WriteLine($"checked 블록   : OverflowException"); }

// 암묵 변환은 정보를 안 잃는 방향으로만 — 단 long → float 은 예외적으로 암묵인데 잃는다
long big = 123456789012345678L;
float lossy = big;
Console.WriteLine($"(float)(long)123456789012345678 = {lossy:F0}   ← 암묵 변환인데 값이 달라졌다");

// byte + byte 의 결과 타입은 int 다
byte b1 = 1, b2 = 2;
Console.WriteLine($"byte + byte 의 타입 : {(b1 + b2).GetType().Name}");
byte b3 = 255; b3++;
Console.WriteLine($"그래도 ++ 와 += 는 된다 : {b3}   (암묵 캐스트가 들어 있다)");

// 크기는 내장 타입만 unsafe 없이 물어볼 수 있다
Console.WriteLine($"sizeof(int)={sizeof(int)}  Unsafe.SizeOf<decimal>()={Unsafe.SizeOf<decimal>()}");
===== csc -out:ex.dll cs05b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
1    → Int32    1L   → Int64
1.0  → Double   1.0f → Single   1.0m → Decimal
0x_FF = 255   0b_1010 = 10
unchecked 식   : -2147483648
unchecked 블록 : -2147483648
checked 블록   : OverflowException
(float)(long)123456789012345678 = 123456790519087104   ← 암묵 변환인데 값이 달라졌다
byte + byte 의 타입 : Int32
그래도 ++ 와 += 는 된다 : 0   (암묵 캐스트가 들어 있다)
sizeof(int)=4  Unsafe.SizeOf<decimal>()=16
```

- ★★ **`(float)(long)123456789012345678` 이 `123456790519087104`** 이다 — **암묵 변환인데 값이 달라졌다.**\
  암묵 변환은 「**정보를 안 잃는 방향**」이라고 흔히 설명하는데, **`long → float` 은 예외**다.\
  언어가 「크기」가 아니라 「범위」를 기준으로 삼았기 때문이다 — `float` 은 `long` 보다 **넓지만 성기다**.
- ★ **`byte + byte` 의 결과 타입이 `Int32`** 다. 그래서 `b = b + 1` 은 컴파일 에러이고,\
  `b++`·`b += 1` 은 **암묵 캐스트가 들어 있어** 통과한다(그리고 **감긴다** — `255` 다음이 `0`).

**금지 사례 — 던져서 받은 여섯**

```text
===== 소스: cs05b-forbid.cs =====
using System;

decimal a = 0.1;            // double 리터럴을 decimal 에
int     b = 3.0;            // double 을 int 에 암묵으로
decimal c = 1m + 1.0;       // decimal 과 double 을 섞어서
byte    d = 300;            // 상수 범위 초과
int     e = int.MaxValue + 1;   // 상수식 넘침
byte    f = 1; f = f + 1;   // byte + byte 는 int 다
Console.WriteLine($"{a} {b} {c} {d} {e} {f}");
===== csc -out:ex.dll cs05b-forbid.cs (cc exit=1) =====
cs05b-forbid.cs(3,13): error CS0664: Literal of type double cannot be implicitly converted to type 'decimal'; use an 'M' suffix to create a literal of this type
cs05b-forbid.cs(4,13): error CS0266: Cannot implicitly convert type 'double' to 'int'. An explicit conversion exists (are you missing a cast?)
cs05b-forbid.cs(5,13): error CS0019: Operator '+' cannot be applied to operands of type 'decimal' and 'double'
cs05b-forbid.cs(6,13): error CS0031: Constant value '300' cannot be converted to a 'byte'
cs05b-forbid.cs(7,13): error CS0220: The operation overflows at compile time in checked mode
cs05b-forbid.cs(8,20): error CS0266: Cannot implicitly convert type 'int' to 'byte'. An explicit conversion exists (are you missing a cast?)
```

| 쓴 것 | 진단 | 무엇을 말하나 |
|---|---|---|
| `decimal a = 0.1;` | ``error CS0664`` | ★★ **`m` 접미사를 빼면 `double` 리터럴**이라 오차가 먼저 생긴다. 언어가 문법으로 막는다 |
| `int b = 3.0;` | ``error CS0266`` | 정보를 잃는 방향에는 암묵 변환이 없다 |
| `decimal c = 1m + 1.0;` | ``error CS0019`` | ★★ **`decimal` 과 `double` 은 섞이지 않는다** — 돈 계산에 `double` 이 새는 것을 막는 장치다 |
| `byte d = 300;` | ``error CS0031`` | 상수 변환 범위 초과 |
| `int e = int.MaxValue + 1;` | ``error CS0220`` | ★ **상수식은 기본이 `checked`** 다((3)) |
| `f = f + 1;`(`byte f`) | ``error CS0266`` | ★ `byte + byte` 의 결과가 `int` 라서다 |

**규칙**

- **암묵 변환은 「정보를 안 잃는 방향」으로만** 있다 — `int → long → float → double` 은 되고 거꾸로는 안 된다.\
  ★ **`long → float` 은 예외적으로 암묵인데 정밀도를 잃는다** — 언어가 「크기」를 기준으로 삼았기 때문이다.
- **`decimal` 은 `double`·`float` 과 암묵 변환이 **양방향 모두 없다**.** 섞어 쓰려면 명시 캐스트를 해야 한다.\
  ★ 이것이 언어가 거는 **실수 방지 장치**다 — 돈 계산에 `double` 이 새어 들어오는 것을 문법이 막는다.
- **정수 산술은 `int` 아래로 안 내려간다** — `byte + byte` 의 결과 타입이 **`int`** 다.\
  그래서 `b = b + 1` 은 에러이고 `b += 1` 과 `b++` 은 된다(복합 대입에 암묵 캐스트가 들어 있다).
- **`checked`/`unchecked` 가 지배하는 것은 「정수 산술과 정수로의 변환」뿐**이다.\
  `decimal` 은 맥락과 무관하게 던지고, `double`/`float` 은 맥락과 무관하게 **무한대·NaN 으로 포화**한다(「구현 세부사항 대 언어 보장」절의 블록).

## 어디서 틀리나

1. ★★★ **「넘치면 터지겠지」** — 안 터진다((1)). C# 의 기본은 `unchecked` 다.\
   **조용히 음수가 된 값이 인덱스나 금액으로 흘러가는 것**이 이 주제의 진짜 사고다.
2. ★★★ **`checked` 블록이 메서드 안까지 간다고 생각하는 것** — 안 간다((5)). **글자 그대로 안쪽**뿐이다.
3. ★★ **`(long)(a + b)` 와 `(long)a + b` 를 같게 보는 것** — 앞엣것은 **`int` 로 더한 뒤** 넓힌다((1)).
4. ★★ **돈을 `double` 로 담는 것** — `0.1 + 0.2 != 0.3` 이고, 누산하면 오차가 쌓인다((6)).\
   ★ **`0.1` 을 `decimal` 변수에 넣을 때 `m` 을 빼는 것**도 같은 사고다 — `double` 리터럴이 먼저 오차를 만든다(컴파일러가 `CS0664` 로 막아 준다).
5. ★★ **「`decimal` 은 항상 정확하다」** — 나눗셈은 못 맞춘다((6)). `1m/3m*3m` 이 `1m` 이 아니다.
6. ★ **`decimal` 의 범위를 `double` 만큼이라고 생각하는 것** — `10^28` 대 `10^308` 이다.\
   과학 계산·큰 지수에는 `decimal` 이 **못 담는다.**
7. ★★ **`==` 로 부동소수점을 비교하는 것** — 그리고 **`Equals` 와 `==` 가 `NaN` 에서 갈리는 것**((9)).
8. ★ **`float` 을 `double` 로 넓히면 정확해진다고 믿는 것** — 안 그렇다((9)).
9. ★ **`1.10m` 과 `1.1m` 을 출력에서 같다고 가정하는 것** — 값은 같고 **표기가 다르다**((7)).\
   로그·비교 테스트가 여기서 조용히 갈린다.
10. ★★ **라이브러리 경계** — `-checked+` 는 **내가 컴파일한 어셈블리에만** 박힌다((4)).\
    남의 `Sum()` 안쪽은 내 설정과 무관하다.

## 구현 세부사항 대 언어 보장

★★★ **이 절의 대표 사례가 하나 있다 — 공식 문서의 예제 출력이 이 판에서 뒤집혔다.**

[Learn 의 `checked`/`unchecked` 문서](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked)는
`int b = unchecked((int)double.MaxValue);` 의 출력을 **`-2147483648`** 로 적어 두었다.
**이 판에서는 `2147483647` 이다**(아래 블록의 둘째 줄).

```text
===== 소스: cs05b-convert.cs =====
using System;

double[] vals  = { double.MaxValue, double.MinValue, 1e10, -1e10, double.NaN,
                   double.PositiveInfinity, double.NegativeInfinity };
string[] names = { "double.MaxValue", "double.MinValue", "1e10", "-1e10", "NaN", "+Inf", "-Inf" };

Console.WriteLine($"int.MaxValue = {int.MaxValue}   int.MinValue = {int.MinValue}");
for (int i = 0; i < vals.Length; i++)
    Console.WriteLine($"unchecked((int){names[i],-15}) = {unchecked((int)vals[i]),12}");

double huge = double.MaxValue;
try { Console.WriteLine(checked((int)huge)); }
catch (OverflowException e) { Console.WriteLine($"checked((int)double.MaxValue) → {e.GetType().Name}: {e.Message}"); }

decimal dm = decimal.MaxValue;
try { Console.WriteLine(unchecked(dm + 1m)); }
catch (OverflowException e) { Console.WriteLine($"unchecked(decimal.MaxValue + 1m)  → {e.GetType().Name}: {e.Message}"); }

try { Console.WriteLine(unchecked((int)dm)); }
catch (OverflowException e) { Console.WriteLine($"unchecked((int)decimal.MaxValue)  → {e.GetType().Name}: {e.Message}"); }

Console.WriteLine($"double  : 1.0 / 0.0 = {1.0 / 0.0}   0.0 / 0.0 = {0.0 / 0.0}");
Console.WriteLine($"float   : float.MaxValue * 2f = {float.MaxValue * 2f}");
===== csc -out:ex.dll cs05b-convert.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int.MaxValue = 2147483647   int.MinValue = -2147483648
unchecked((int)double.MaxValue) =   2147483647
unchecked((int)double.MinValue) =  -2147483648
unchecked((int)1e10           ) =   2147483647
unchecked((int)-1e10          ) =  -2147483648
unchecked((int)NaN            ) =            0
unchecked((int)+Inf           ) =   2147483647
unchecked((int)-Inf           ) =  -2147483648
checked((int)double.MaxValue) → OverflowException: Arithmetic operation resulted in an overflow.
unchecked(decimal.MaxValue + 1m)  → OverflowException: Value was either too large or too small for a Decimal.
unchecked((int)decimal.MaxValue)  → OverflowException: Value was either too large or too small for an Int32.
double  : 1.0 / 0.0 = ∞   0.0 / 0.0 = NaN
float   : float.MaxValue * 2f = ∞
```

- ★★★ **일곱 줄이 전부 「포화(saturating)」다** — 범위를 넘으면 **가장 가까운 끝값**이 되고 `NaN` 은 `0` 이다.\
  **감기지 않는다.** 예전 판에서는 감기는 결과(`-2147483648`)가 나왔다.
- ★★★ **어느 쪽도 틀리지 않았다** — **언어가 이 값을 정해 주지 않기 때문**이다.\
  `unchecked` 맥락에서 부동소수점을 정수로 변환할 때 범위를 넘으면 **결과가 규정돼 있지 않다.**\
  그래서 **런타임이 바뀌면 값이 바뀔 수 있고, 실제로 바뀌었다.**
- ★★ **여기서 배울 것은 값이 아니라 태도다** — 「문서에 이렇게 적혀 있다」는 **돌려 본 것이 아니다.**\
  ★ 이 문서는 그 문장을 **직접 던져서** 뒤집었다.

| 층 | 무엇을 말하나 | 이 주제의 예 |
|---|---|---|
| **언어 명세(ECMA-334)** | 무엇이 **언제나** 참인가 | 정수 오버플로의 기본 맥락이 `unchecked` 인 것 · 상수식이 `checked` 인 것 · `decimal` 이 10진인 것 · `checked` 의 범위가 **어휘적**인 것 |
| **런타임(CoreCLR) 구현** | 이 판이 **지금** 그렇게 하는 것 | ★★★ **범위를 넘는 `double`→`int` 변환이 포화하는 것** · 박싱이 24·32바이트인 것 · 예외 메시지 문구 · 종료 코드 134 |
| **이 판의 관찰** | 돌려 봤더니 이랬다는 것 | IL 명령 열(Roslyn 10.0.401 의 코드 생성) · `decimal.GetBits` 의 배율 칸 값 · `CS1718` 경고가 나는 자리 |

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **정수 산술의 기본 맥락이 `unchecked`** 이고, **상수식의 기본 맥락이 `checked`** 인 것.
- **`checked`/`unchecked` 의 효력 범위가** 「**그 괄호·블록의 글자 안쪽**」인 것 — 호출된 메서드 본문에 안 미친다.
- **`checked` 에서 넘치면 `OverflowException`**, **상수식에서 넘치면 컴파일 에러**인 것.
- **`decimal` 이 10의 거듭제곱 배율을 쓰는 것**과 **`double`/`float` 과 암묵 변환이 없는 것**.
- **`decimal` 이 맥락과 무관하게 넘침에 던지는 것**(포화가 뜻이 없는 타입이라서).
- **정수 나눗셈의 `0` 이 맥락과 무관하게 `DivideByZeroException`** 인 것.

**구현에 달린 것**(판이 바뀌면 움직인다)

- ★★★ **범위를 넘는 부동소수점 → 정수 변환의 결과값**(포화 대 감김). **문서와 이 판이 갈린 자리다.**
- **박싱 바이트 24·32** — x64 CoreCLR 의 객체 헤더 크기에 달렸다.
- **IL 명령 열** — Roslyn 의 코드 생성이 바뀌면 움직인다.
- **예외 메시지 문구**·**종료 코드 134**·**`∞` 를 그렇게 찍는 것**(`ToString` 의 `PositiveInfinitySymbol`).

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 언제 |
|---|---|
| **`int`** | 기본값. 셈·인덱스·개수. 범위가 21억이면 충분한 곳 전부 |
| **`long`** | 21억을 넘을 수 있는 것 — 바이트 수·타임스탬프·누적 카운터 · **ID** |
| **`double`** | 과학·통계·물리·그래픽 — **오차가 허용되고 범위가 넓어야 하는** 계산 |
| **`decimal`** | ★★ **돈·수량·세율·비율** — 사람이 10진으로 쓴 값을 그대로 보존해야 하는 것 |
| **`byte`/`short`** | ★ 「메모리를 아끼려고」가 아니라 **바이트 스트림·프로토콜 필드처럼 폭이 규정된 것** |
| **`checked` 블록** | 넘침이 **버그이지 기능이 아닌** 계산 — 금액 합계·용량 계산 |
| **`unchecked` 블록** | 넘침이 **기능인** 계산 — 해시 결합·체크섬·의사난수 |
| **`-checked+`** | 팀 전체가 「넘침은 언제나 버그」로 합의한 코드베이스 |

- ★★★ **돈에 `double` 을 쓰지 마라**는 이 주제의 유일한 절대 규칙이다. 나머지는 상황에 달렸다.
- ★★ **「돈을 `int` 로(원·센트 단위 정수)」도 정답이다** — `decimal` 보다 빠르고 작으며 `==` 가 안전하다.\
  대가는 **세율·이자 같은 나눗셈이 들어오는 순간 직접 반올림 규칙을 정해야 하는 것**이다.
- ★ **`decimal` 을 과학 계산에 쓰지 마라** — 범위가 `10^28` 에서 끝나고, (6)에서 본 대로 나눗셈이 더 나쁘다.
- ★ **해시 함수에 `unchecked` 를 명시**하는 것은 관용구다. `-checked+` 를 켠 코드베이스에서 해시가 터지는 것을 막는다.

## 핵심 문장

1. ★★★ **C# 정수 산술의 기본은 「조용히 감기는 것」이다** — 예외도 경고도 없다. **멈추는 것은 내가 켠다.**
2. ★★★ **상수식만은 반대다** — 기본이 `checked` 라 **실행까지 못 가고 `CS0220` 으로 막힌다.**
3. ★★ **`checked` 의 범위는 글자 그대로 안쪽뿐이다** — 호출한 메서드 안까지 가지 않는다.
4. ★★ **`decimal` 은 부동소수점이 아니라** 「**10진 정수 + 10의 거듭제곱 배율**」이다 — 그래서 `0.1m + 0.2m == 0.3m` 이다.
5. ★★ **`decimal` 이 고치는 것은 10진 리터럴의 보존이지 모든 산술의 정확성이 아니다** — 나눗셈은 `double` 보다 나쁠 수 있다.
6. ★ **IL 이 셋을 갈라 보여 준다** — `add` · `add.ovf` · `call System.Decimal::op_Addition`.
7. ★ **범위를 넘는 `double`→`int` 변환의 값은 언어가 정해 주지 않는다** — 공식 문서의 예제와 이 판이 실제로 갈렸다.

## 관련 자료

- [`foundations/data-representation/`](../../../../data-representation/) — **2진 표현과 IEEE 754 의 원리는 거기까지**,\
  여기는 **그 위에서 C# 이 무엇을 고르게 하나부터**다.
- [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/) — 숫자 타입이 전부 `struct` 라는 것의 정본.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — (7)의 +24·+32 바이트 계산의 정본.
- 목록의 **20번 주제**(`enum` 과 `[Flags]`) — 열거형이 정수 위의 껍데기라는 것.
- 목록의 **48번 주제**(문자열 서식·문화권) — `ToString("G17")`·`1.10m` 의 출력 형식.
- 목록의 **49번 주제**(연산자 오버로딩) — `System.Decimal::op_Addition` 이 무엇인지.
- C 갈래의 [정수 승격 편](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/) — **C 에서는 부호 있는 정수 오버플로가 미정의 동작**이라\
  컴파일러가 「안 일어난다」고 가정하고 최적화한다. **C# 은 정의된 감김**이라 그 부류의 사고가 없다.
- Java 의 [숫자 연산 편](../../../java/syntax/02-numeric-operations/) — Java 에는 **`checked` 가 없다.**\
  `Math.addExact` 같은 메서드를 직접 불러야 하고, `BigDecimal` 은 `decimal` 과 달리 **객체**다.

## 용어 풀이

- **오버플로(overflow)** — 연산 결과가 타입의 범위를 벗어나는 것. C# 정수는 기본적으로 상위 비트를 버린다.
- **`checked` 맥락** — 오버플로에 `OverflowException` 을 던지는 맥락. 식·블록·컴파일러 플래그로 켠다.
- **`unchecked` 맥락** — 넘치는 비트를 버리는 맥락. **C# 의 실행 시점 기본값**이다.
- **상수식(constant expression)** — 컴파일 시점에 값이 정해지는 식. **기본 맥락이 `checked`** 다.
- **2의 보수(two's complement)** — 음수를 표현하는 방식. 상위 비트를 버리면 자연히 「감김」이 된다.
- **`decimal`** — 96비트 정수와 10의 거듭제곱 배율로 된 16바이트 값 타입. 유효 자릿수 약 28자리.
- **배율(scale)** — `decimal` 이 들고 다니는 「소수점 이하 자릿수」. `1.10m` 과 `1.1m` 을 가르는 것.
- **포화(saturating)** — 범위를 넘으면 가장 가까운 끝값이 되는 것. 이 판의 부동소수점→정수 변환이 그렇다.
- **`add.ovf`** — 넘침을 검사하는 IL 덧셈 명령. `checked` 가 찍게 만드는 것.
- **`CheckForOverflowUnderflow`** — MSBuild 속성. `csc` 의 `-checked+` 로 전달된다.

## 더 들어가면

- **`nint`/`nuint`**(C# 9) — 포인터 크기를 따르는 정수. 이 머신에서는 8바이트다. **이 문서는 안 던졌다.**
- **`Half`**(.NET 5) — 2바이트 부동소수점. 기계 학습·그래픽에서 쓴다. **이 문서는 안 던졌다.**
- **`System.Int128`/`UInt128`**(.NET 7) — 16바이트 정수. **이 문서는 안 던졌다.**
- **사용자 정의 `checked` 연산자**(C# 11) — `public static int operator checked +(…)`.\
  ★ Learn 이 「사용자 정의 연산자는 `checked` 맥락에서도 안 던질 수 있다」고 못 박은 자리다. **이 문서는 안 던졌다.**
- **`Math.BigMul`·`Math.DivRem`** — 넘침 없이 곱·나눗셈을 얻는 BCL 도구.
- **`System.Numerics.BigInteger`** — 임의 정밀도 정수. **값 타입인데 내부에 배열을 든다.**
- **`MidpointRounding`** — `decimal` 반올림 규칙. 금융에서 `ToEven`(은행가 반올림)과 `AwayFromZero` 가 갈린다.
- ★ **왜 `decimal` 은 `float`/`double` 과 암묵 변환이 없나** — 언어 설계가 「섞이면 사고가 난다」를 **문법으로 막은** 것이다.\
  같은 결정을 `bool` 과 정수 사이에서도 했다(C 와 달리 `if (1)` 이 안 된다).
