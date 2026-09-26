# csharp/syntax/05 — 기본 숫자 타입·`checked`/`unchecked`·`decimal` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — `checked`/`unchecked`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked) · [Learn — 널 허용 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-value-types) · [Learn — 널 허용 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types) · [Learn — 멤버 접근·널 조건 연산자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 첫 줄(`// cs0Nb-….cs` 꼴)도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> **읽는 법** — ★★★ **할당 바이트는 증분만 근거로 쓴다.** 절댓값(프로세스 누적)은 흔들리는 칸이고,\
> 이 문서는 **한 번도 싣지 않았다.** 더 중요한 것은 **0 이냐 아니냐**다.\
> ★ **`cc exit` 과 `run exit` 을 갈라 적었다** — 「컴파일은 됐는데 실행이 죽었다」가 이 주제에서 자주 나온다.\
> 자세한 환경과 던진 형태는 [2-summary.md](2-summary.md)의 머리말·(0)절에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 전부 감긴다 — 진단은 **0줄**이다

**출력**

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

**왜 그런가**

- ★★★ **C# 정수 산술의 기본 맥락이 `unchecked`** 이기 때문이다. 넘치는 상위 비트를 버리고 남은 것이 결과다.\
  **진단이 한 줄도 없다**(`cc exit=0`) — 이 주제가 「에러가 교재인 갈래」가 아닌 이유다.
- `int.MaxValue + 1` 은 2진으로 `0111…1 + 1 = 1000…0` 이고, 2의 보수에서 그것이 `int.MinValue` 다.
- `(byte)255` 에 `++` 하면 `256 = 1_0000_0000`(2진)인데 `byte` 는 하위 8비트만 들고 있으므로 `0` 이다.\
  ★ `b++` 이 컴파일되는 것도 눈여겨보라 — `b = b + 1` 은 **`byte + byte` 의 결과가 `int`** 라 컴파일 에러인데,\
  `++` 와 `+=` 에는 **암묵 캐스트가 들어 있다.**
- `unchecked(big + 1)` 은 **기본값을 글자로 적은 것**이라 결과가 같다.\
  쓸 일은 **주변이 `checked` 일 때 한 군데만 푸는 것**이다.
- ★★ **`(long)int.MaxValue + 1` 은 안 감긴다**(`2147483648`) — `long` 으로 넓힌 **뒤에** 더하기 때문이다.\
  **`(long)(int.MaxValue + 1)` 은 여전히 감긴다** — 괄호 안이 `int` 산술이다. **괄호 위치가 결과를 바꾼다.**

### 2. `OverflowException` · `cc exit=0` · `run exit=134` · 트레이스 **1줄**

**출력**

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

**왜 그런가**

- `checked` 맥락에서 정수 산술이 넘치면 **`System.OverflowException`** 이고 메시지는\
  `Arithmetic operation resulted in an overflow.` 다. **어느 연산이 넘쳤는지는 메시지에 없다.**
- **`cc exit=0`** 이다 — `big` 이 **변수**라 상수식이 아니고, 컴파일러는 넘침을 알 수 없다.\
  ★ 이것이 3번과 갈리는 지점이다.
- **`run exit=134`** — 처리되지 않은 예외로 죽은 .NET 프로세스의 코드다.
- 트레이스가 **`at Program.<Main>$(String[] args)` 한 줄**뿐인 것은 **`-debug` 를 안 줬기 때문**이다.\
  PDB 가 없으면 파일 경로와 줄 번호가 안 박히고, 그래서 **어느 머신에서 돌려도 같은 글자**가 나온다.

잡아서 보면 네 자리가 이렇다 — **셋은 같은 예외, 넷째만 다르다.**

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

- ★★ **`unchecked(1 / 0)` 이 `DivideByZeroException` 을 던진다.**\
  `checked`/`unchecked` 가 지배하는 것은 「**넘침**」이고, **0으로 나누기는 맥락 밖**이다.\
  ★ 「`unchecked` 면 아무것도 안 던진다」로 외우면 여기서 틀린다.
- `decimal` 도 마찬가지로 **맥락과 무관하게 던진다**(10번의 블록에 있다) — 포화할 끝값이 뜻을 갖지 않는 타입이라서다.
- 반대로 **`double`/`float` 은 맥락과 무관하게 안 던지고 `∞`·`NaN` 으로 포화**한다.

### 3. ★★ **세 줄이 막히고 마지막 줄만 통과한다**

**출력**

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

**왜 그런가**

- ★★★ **상수식의 기본 맥락은 `checked`** 다 — 실행 시점 기본값(`unchecked`)과 **정반대**다.\
  그래서 3번 줄 `int a = int.MaxValue + 1;` 에 `checked` 라는 글자가 없는데도 **`CS0220`** 이 난다.
- 4번 줄은 `checked` 를 명시했고 **같은 에러**다. **3번과 4번은 사실상 같은 코드**다.
- 5번 줄 `byte c = 300;` 은 **`CS0031`** 이다 — 이것은 산술 넘침이 아니라 **상수 변환**이 걸린 것이라\
  에러 번호가 다르다. ★ **번호가 두 가지를 가른다.**
- ★★ 6번 줄 `int d = unchecked(int.MaxValue + 1);` 은 **통과했다.**\
  **진단이 3줄뿐이고 6번 줄이 없다**는 것이 그 근거다 — 상수식의 검사도 `unchecked` 로 명시해 끌 수 있다.
- 실무에서 이것이 나오는 자리는 **`const` 로 계산한 상한·비트마스크**다.\
  「런타임이면 감겼을 것」이 **빌드에서 먼저 막힌다.**

### 4. ★★ 출력이 갈린다 — `run exit=0` 대 `run exit=134`

**출력** — 같은 소스를 플래그만 바꿔 두 번 던졌다.

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

**왜 그런가**

- **`-checked+`** 가 MSBuild 의 **`<CheckForOverflowUnderflow>true</CheckForOverflowUnderflow>`** 가 컴파일러에 주는 플래그다.\
  기본값은 꺼짐이다.
- ★★★ **소스가 한 글자도 안 바뀌었는데 결과가 갈렸다.**\
  그래서 **「이 코드는 감긴다」는 소스만 보고 말할 수 없다** — 빌드 설정을 같이 봐야 한다.
- 이 플래그는 **비상수식만** 바꾼다. 상수식은 3번에서 본 대로 **언제나 `checked`** 라 영향을 안 받는다.
- ★★ **참조하는 라이브러리 안쪽에는 안 미친다.** 오버플로 검사는 **컴파일 시점에 IL 명령으로 박히므로**(8번),\
  남의 어셈블리는 **그 어셈블리를 빌드한 설정**을 그대로 들고 있다.\
  ★ 내가 `-checked+` 를 켜도 `list.Sum()` 안쪽은 여전히 감길 수 있다.

### 5. ★★★ 첫 호출은 **안 터지고**(`-2`) 둘째만 터진다

**출력**

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

**왜 그런가**

- ★★★ **`checked` 의 효력 범위는** 「**그 블록의 글자 안쪽**」이다(어휘적 범위).\
  `Multiply` 의 **본문은 블록 바깥에 적혀 있으므로** 그 안의 `a * b` 는 여전히 `unchecked` 다.
- 두 호출을 가르는 것은 **식이 어디에 적혀 있나**다.\
  `factor * int.MaxValue` 는 **인자 자리에 적힌 식**이라 블록의 글자 안쪽이고, 그래서 터진다.
- 「`checked` 로 감쌌으니 그 안의 계산은 전부 안전하다」는 **거짓**이다.\
  ★ **메서드 경계를 넘는 보장을 원하면 4번의 컴파일러 플래그**라야 하고, 그것도 **내가 컴파일한 코드까지**다.
- ★ 이 성질은 `unchecked` 에도 똑같이 적용된다 — `unchecked { Helper(); }` 가 `Helper` 안쪽을 풀어 주지 않는다.

### 6. ★★★ `double` 은 `0.30000000000000004`, `decimal` 은 `0.3` — 그런데 나눗셈은 뒤집힌다

**출력**

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

**왜 그런가**

- `double` 은 **2진 부동소수점**이라 `0.1`·`0.2`·`0.3` 을 **정확히 담지 못한다.**\
  담기는 것은 가장 가까운 2진 근사값이고, 근사의 방향이 달라 `0.1 + 0.2 != 0.3` 이 된다.
- ★★ **`0.3` 자체도 이미 틀려 있다** — `G17` 로 찍으면 `0.29999999999999999` 다.\
  「`0.1 + 0.2` 가 틀린 것」이 아니라 **세 숫자가 전부 근사값**이다.
- `decimal` 은 **96비트 정수 × 10의 거듭제곱**이라 `0.1m` 이 `1 × 10^-1` 로 **정확히** 담긴다.\
  그래서 덧셈이 정확하고, **10번 누산해도 `1.0`** 이다(`double` 은 `0.99999999999999989`).
- ★★★ **마지막 세 줄이 이 문항의 핵심이다** — **`1.0 / 3.0 * 3.0` 이 `1`** 이고\
  **`1m / 3m * 3m` 은 `0.9999999999999999999999999999`** 다. **뒤집혔다.**
  - `double` 은 유효 자릿수가 약 15자리라 `0.333…3 × 3` 의 오차가 **반올림에 먹혀 `1.0` 으로 되돌아왔다.**
  - `decimal` 은 28자리를 충실히 들고 있어 **`0.999…9` 가 그대로 남았다.**
- ★★★ **그래서 「`decimal` 이 더 정확하다」는 문장은 좁혀야 한다** —\
  `decimal` 이 보장하는 것은 「**10진으로 쓴 리터럴과 그 덧·뺄·곱셈이 자릿수 안에서 정확하다**」는 것이지\
  「**모든 산술이 수학적으로 정확하다**」가 아니다. 나눗셈은 어느 쪽도 못 맞춘다.

### 7. ★ 16바이트 · 박싱 **+32** · 배율은 **10의 거듭제곱** · 자릿수가 값에 남는다

**출력**

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

**왜 그런가**

- `decimal` 은 **16바이트**다(`double` 의 두 배). 배열·구조체 필드에 넣으면 그대로 두 배가 된다.
- 박싱은 **`int`·`double` 이 +24, `decimal` 이 +32** 다.\
  x64 CoreCLR 의 **객체 헤더 16바이트** 위에 값이 얹히고, **최소 객체 크기가 24바이트**라\
  4바이트짜리 `int` 도 8바이트짜리 `double` 도 24로 같다. 16바이트인 `decimal` 만 32로 넘어간다([03번](../03-boxing-and-unboxing/)).
- ★★★ **`decimal.GetBits(0.1m)` 이 `[1, 0, 0, 65536]`** 이다.\
  앞 세 칸이 **96비트 정수 `1`**, 마지막 칸이 **플래그(부호 + 배율)** 인데 `65536 = 1 << 16` 이므로 **배율이 1**, 즉 `1 × 10^-1` 이다.\
  ★ **2의 지수가 어디에도 없다.** 이것이 「`decimal` 은 부동소수점이 아니다」의 가장 짧은 근거다.
- ★★ **`1.10m` 과 `1.1m` 은 비트가 다르다** — `[110, 0, 0, 131072]` 대 `[11, 0, 0, 65536]`(배율 2 대 1).\
  그런데 **`==` 도 `True`, `GetHashCode()` 도 같고, `ToString()` 만 `1.10` 과 `1.1` 로 갈린다.**
- **기능인 자리** — 회계·청구서에서 「5,000원」과 「5,000.00원」을 **입력 그대로 출력**해야 할 때다.\
  ★ 반대로 **로그 비교나 문자열 기반 테스트에서는 함정**이 된다 — 값이 같은데 문자열이 다르다.

### 8. ★★★ `add` · **`add.ovf`** · `add` · **`call System.Decimal::op_Addition`** · `conv.i4` · **`conv.ovf.i4`**

**출력**

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

**왜 그런가**

| 소스 | IL | 읽는 법 |
|---|---|---|
| `a + b` (`int`) | `add` | 넘침을 **안 본다** |
| `checked(a + b)` (`int`) | ★★★ **`add.ovf`** | 명령이 **한 글자 다르다** |
| `a + b` (`double`) | `add` | ★ `int` 와 **같은 명령**이다 |
| `a + b` (`decimal`) | ★★★ **`call System.Decimal::op_Addition`** | **명령이 아니라 메서드 호출**이다 |
| `(int)a` (`double`→`int`) | `conv.i4` | 잘라 담는다 |
| `checked((int)a)` | **`conv.ovf.i4`** | 변환에도 `.ovf` 판이 있다 |

- ★★ **`checked` 는 런타임 설정이 아니라 컴파일 시점의 명령 선택이다.**\
  그래서 4번에서 본 대로 **라이브러리 경계를 못 넘는다** — 남의 어셈블리에는 이미 `add` 가 박혀 있다.
- **`AddDouble` 이 `AddInt` 와 같은 `add`** 인 것은 IL 이 **스택 위 값의 타입**으로 동작을 정하기 때문이다.\
  정수 `add` 와 실수 `add` 가 같은 옵코드다.
- ★★★ **`AddDecimal` 만 `call` 이다.** CPU 에 「10진 덧셈」 명령이 없으므로 `decimal` 산술은 **전부 BCL 메서드**다.\
  ★ 이것이 「`decimal` 이 부동소수점이 아니다」의 두 번째 근거다 — **`float`·`double` 은 하드웨어가 아는 타입이고 `decimal` 은 라이브러리 타입**이다.
- ★★ **이 문서는 「`decimal` 이 느리다」를 한 번도 적지 않았다** — **시간을 안 쟀기 때문**이다.\
  적은 것은 「**명령 하나가 아니라 호출 하나다**」라는 사실뿐이다.

### 9. ★ 경고가 **먼저** 나고, `==` 와 `Equals` 가 `NaN` 에서 갈린다

**출력**

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

**왜 그런가**

- ★★ **`CS1718` 경고가 두 줄 났다** — 「같은 변수끼리 비교하는데 의도한 게 맞나」다.\
  ★ **경고도 출력이다.** 이 경고가 있다는 것 자체가 「이 비교는 보통 실수다」라는 언어의 신호다.
- **`nan == nan` 은 `False`** — IEEE 754 가 그렇게 정했다. `NaN` 은 자기 자신과도 같지 않다.
- **`nan.Equals(nan)` 은 `True`** — BCL 의 `Equals` 는 **반사성**(자기 자신과 같아야 한다)을 지켜야\
  사전·집합이 동작하므로 `NaN` 을 특수 처리한다. **연산자와 메서드가 어긋난다.**
- ★★ 그래서 **`Array.IndexOf(new[]{nan}, nan)` 이 `0`** 이다 — `IndexOf` 는 `Equals` 를 쓴다.\
  **`==` 로는 못 찾는 값을 컬렉션은 찾아낸다.** 사전 키·`Contains`·`Distinct` 가 전부 이쪽이다.
- **`0.0 == -0.0` 도 `True`, `Equals` 도 `True`** 인데 **`1.0 / -0.0` 은 `-∞`** 다.\
  「같은 값」인데 **나눗셈의 부호가 갈린다.**
- ★★ **`(double)0.1f != 0.1`** — `0.10000000149011612` 대 `0.10000000000000001`.\
  `float` → `double` 은 **정보를 더해 주지 않는다.** 이미 잃은 정밀도는 안 돌아온다.\
  ★ 「넓히니까 안전하겠지」가 틀리는 자리다.
- **처방** — `Math.Abs(a - b) < 허용오차` 로 비교하고 허용오차를 값의 크기에 비례시킨다.\
  ★ 그리고 **`==` 가 성립해야 하는 값이면 애초에 `decimal` 이나 정수(원 단위)를 쓴다.**

### 10. ★★★ **포화한다**(`2147483647`) — 그런데 그것은 **언어 보장이 아니다**

**출력**

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

**왜 그런가**

- ★★★ [Learn 의 `checked`/`unchecked` 문서](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked)는\
  `int b = unchecked((int)double.MaxValue);` 의 출력을 **`-2147483648`** 로 적어 두었다.\
  **이 판은 `2147483647`** 이다 — **감기지 않고 포화한다.**
- ★★★ **어느 쪽도 틀리지 않았다.** `unchecked` 맥락에서 부동소수점을 정수로 변환할 때\
  범위를 넘으면 **결과가 언어로 규정돼 있지 않다.** 런타임이 정하고, **실제로 바뀌었다.**
- 일곱 줄이 전부 같은 규칙이다 — **범위 밖은 가장 가까운 끝값**, **`NaN` 은 `0`**, **`±Inf` 는 `int` 의 양끝**.
- `checked((int)double.MaxValue)` 는 **`OverflowException`** 이다 — 이쪽은 **언어가 보장한다.**
- ★★★ **「Learn 문서에 이렇게 적혀 있다」는 근거가 못 된다.**\
  문서는 「무엇이 옳은가」를 말하고, **실행은** 「**지금 무엇이 되는가**」를 말한다.\
  ★ 이 문서가 그 문장을 **직접 던져서** 뒤집었다 — 그것이 이 갈래가 하는 일이다.
- **처방** — 범위를 넘을 수 있는 변환에는 **`checked` 를 명시**하거나 `Math.Clamp` 로 **직접 좁혀라.**\
  기본값에 의존하면 런타임 판이 바뀔 때 조용히 값이 달라진다.

### 11. 돈에는 `decimal` 또는 **정수(원 단위)** · 해시에는 `unchecked` · 과학 계산에 `decimal` 금지

**답**

| 쓸 것 | 언제 | 대가 |
|---|---|---|
| **`int`** | 기본값 — 셈·인덱스·개수 | 21억을 넘으면 조용히 감긴다 |
| **`long`** | 바이트 수·타임스탬프·누적·ID | 8바이트 |
| **`double`** | 과학·통계·물리·그래픽 | `==` 를 못 쓴다((9)) |
| **`decimal`** | ★★ 돈·수량·세율 | 크기 2배 · 범위 `10^28` · 연산이 메서드 호출((7)·(8)) |
| ★★ **정수(원·센트 단위)** | 돈 — `decimal` 의 **대안 정답** | **나눗셈이 들어오면 반올림 규칙을 내가 정해야 한다** |
| **`byte`/`short`** | ★ 바이트 스트림·프로토콜 필드처럼 **폭이 규정된 것** | ★ 「메모리를 아끼려고」는 **틀린 이유**다 — 산술이 `int` 로 승격되고 정렬 때문에 공간도 대개 안 준다 |

- **해시 함수에 `unchecked` 를 명시하는 이유** — 해시 결합은 **넘침이 기능**이다.\
  `-checked+` 를 켠 코드베이스에서 `hash = hash * 31 + x` 가 **`OverflowException` 으로 죽지 않게** 못 박는 것이다.
- **`decimal` 을 쓰면 안 되는 계산** — 범위가 `10^28` 에서 끝나므로 **과학·천문·확률 곱** 같은 큰/작은 지수.\
  그리고 **나눗셈이 반복되는 계산**((6)) — `decimal` 이 더 낫다는 보장이 없다.

### 12. 다른 주제와 잇기

- **「박싱이 24바이트인 것」** — [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/)이 정본이다.\
  이 주제는 그 계산 위에 `decimal` 의 32바이트만 얹었다.
- **「2진 부동소수점이 왜 0.1 을 못 담나」** — [`foundations/data-representation/`](../../../../data-representation/)가 정본이다.\
  ★ 여기는 **그 사실 위에서 무엇을 고르나**만 다룬다.
- **`System.Decimal::op_Addition`** — 목록의 **49번 주제**(연산자 오버로딩과 변환 연산자).\
  `operator +` 를 정의하면 IL 에 `op_Addition` 이라는 **정적 메서드**가 생긴다.
- **C 갈래**([C 의 정수 승격 편](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)) — 결정적으로 다르다.\
  ★★ **C 에서 부호 있는 정수 오버플로는 미정의 동작**이라 컴파일러가 「일어나지 않는다」고 가정하고\
  **주변 코드를 지워 버릴 수 있다.** C# 은 **정의된 감김**이라 그 부류의 사고가 없다 — 값만 틀릴 뿐이다.
- **Java** — [숫자 연산 편](../../../java/syntax/02-numeric-operations/).\
  ★ **Java 에는 `checked` 문법이 없다.** `Math.addExact(a, b)` 같은 메서드를 직접 불러야 하고,\
  10진 계산은 `BigDecimal` 인데 그것은 **참조 타입(객체)** 이라 `decimal` 과 성격이 다르다([01번](../01-value-types-and-reference-types/)).
- **`enum` 이 정수 위의 껍데기인 것** — 목록의 **20번 주제**. `checked` 는 `enum` 산술에도 적용된다.
- **서식·문화권** — 목록의 **48번 주제**. `ToString("G17")` 과 `1.10m` 의 출력이 거기 축이다.

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64** 에서\
캡처 스크립트로 받았다. **제출 직전에 전부 다시 돌려 정규화 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs05b-env.cs` | 런타임 판·`IntPtr.Size`·GC 모드 | `csc` + 실행 |
| `cs05b-sizes.cs` | 크기·범위 13종 | 〃 |
| `cs05b-wrap.cs` | ★★★ 감김 6줄 · **진단 0줄** | 〃 |
| `cs05b-checked.cs` | `OverflowException` 전문 · `run exit=134` | 〃 |
| `cs05b-catch.cs` | 같은 예외 3자리 + **`DivideByZeroException`** | 〃 |
| `cs05b-const.cs` | ★★ `CS0220` ×2 · `CS0031` · **6번 줄 통과** | `csc` 만(`cc exit=1`) |
| `cs05b-flag.cs` | ★★★ 같은 소스, `-checked+` 로 `run exit` 이 0 → 134 | `csc` ×2 + 실행 |
| `cs05b-textual.cs` | ★★★ `checked` 의 어휘적 범위(`-2` 대 예외) | `csc` + 실행 |
| `cs05b-convert.cs` | ★★★ **포화 변환 7줄** · `decimal` 은 `unchecked` 여도 던짐 | 〃 |
| `cs05b-money.cs` | ★★★ `0.1+0.2` · 누산 · **`1m/3m*3m` 이 1 이 아님** | 〃 |
| `cs05b-cost.cs` | 16바이트 · 박싱 +24/+24/+32 · `GetBits` · `1.10m` | 〃 |
| `cs05b-il.cs` | ★★★ `add` · `add.ovf` · `op_Addition` · `conv.ovf.i4` | `csc -r:il.dll` + 실행 |
| `cs05b-eq.cs` | `CS1718` ×2 · `NaN` 의 `==`/`Equals` 어긋남 · `-0.0` | `csc` + 실행 |

**구현 의존 항목** — 다음은 **이 환경(.NET 10.0.12 · CoreCLR · x64 linux)에서만** 그렇다.

- ★★★ **범위를 넘는 `double`→`int` 변환이 포화하는 것**(10번). **공식 문서의 예제와 갈렸다.**\
  ★ **언어가 값을 규정하지 않는 자리**이므로 판이 바뀌면 또 바뀔 수 있다.
- ★★ **박싱 +24·+32** — 객체 헤더 16바이트와 최소 객체 크기 24바이트가 x64 CoreCLR 의 값이다.
- ★ **IL 명령 열** — Roslyn 10.0.401 의 코드 생성이다. `-optimize` 를 켜면 `nop` 이 사라진다(**이 문서는 안 켰다**).
- ★ **예외 메시지 문구**·**종료 코드 134**·**`∞`·`NaN` 의 출력 문자열**.
- ★ **`decimal` 의 유효 자릿수 28자리** — 이것은 타입 정의라 안 바뀌지만, `1m/3m` 의 **마지막 자리**는 구현이 정한다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **정수 산술의 실행 시점 기본 맥락이 `unchecked`** 이고 **상수식의 기본 맥락이 `checked`** 인 것.
- **`checked`/`unchecked` 의 효력이 「글자 그대로 안쪽」에만 미치는 것** — 호출한 메서드 본문에 안 간다.
- **`checked` 넘침 = `OverflowException`**, **상수식 넘침 = 컴파일 에러**인 것.
- **0으로 나누기가 맥락과 무관하게 `DivideByZeroException`** 인 것.
- **`decimal` 이 10의 거듭제곱 배율을 쓰고, 넘침에 맥락과 무관하게 던지는 것.**
- **`decimal` 과 `double`/`float` 사이에 암묵 변환이 없는 것.**
- **`byte + byte` 의 결과 타입이 `int`** 인 것.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **`nint`/`nuint`**(C# 9) · **`Half`**(.NET 5) · **`Int128`**(.NET 7) ·\
  **사용자 정의 `checked` 연산자**(C# 11 — Learn 이 「`checked` 맥락에서도 안 던질 수 있다」고 못 박은 자리) ·\
  **`MidpointRounding` 의 각 모드** · **32비트 런타임**(포화 동작이 거기서 같은지 **확인 안 했다**) ·\
  **`-optimize` 를 켠 IL** · **옛 .NET 판**(포화 이전 동작을 직접 못 봤다 — 문서의 값으로만 안다).
- **못 잰 것** — ★★ **「`decimal` 이 얼마나 느린가」.**\
  이 문서가 잰 것은 **바이트와 명령**이고 **시간이 아니다.** 재려면 워밍업·JIT 계층·반복 하네스가 필요한데\
  그것은 이 갈래의 축이 아니다. ★ 그래서 **「느리다」를 한 번도 적지 않았다** — 적은 것은 「**호출 하나다**」뿐이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **10번의 포화 변환 일곱 줄** — **언어가 규정하지 않는 값**이라 가장 먼저 움직인다.
- ★★ **7번의 +24·+32** — 객체 레이아웃이 바뀌면 움직인다. **증분이 0 이냐 아니냐**는 안 움직인다.
- ★ **8번의 IL 명령 열** — Roslyn 이 바뀌면 움직인다. **`add` 대 `add.ovf` 의 대비**는 언어가 요구하는 것이라 안 움직인다.
- ★ **6번의 `1m / 3m` 마지막 자리** — 28자리 나눗셈의 반올림은 구현이다.
