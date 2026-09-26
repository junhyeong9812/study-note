# csharp/syntax/05 — 기본 숫자 타입·`checked`/`unchecked`·`decimal` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> MSBuild 를 안 쓰고 Roslyn `csc` 를 직접 부른다(`-debug` 없음 — 트레이스에 줄 번호가 없다).
> ★★ **이 주제에는 컴파일 진단이 세 자리에만 난다** — 3번(상수식) · 9번(같은 변수 비교 경고) · 문법 절의 금지 사례.
> 나머지는 **실행 출력 · 예외 전문 · IL · 할당 바이트**가 근거다.
> ★★★ **6번을 외우려 하지 마라** — 「`decimal` 이 더 정확하다」가 **거기서 뒤집힌다.** 던져서 확인하는 것이 답이다.
> ★ **10번은 공식 문서와 이 판이 갈린 자리**다. 「문서에 적힌 값」을 답으로 쓰면 틀린다.
> 선행 — [01번](../01-value-types-and-reference-types/) · [03번](../03-boxing-and-unboxing/) ·
> [`foundations/data-representation/`](../../../../data-representation/)(2진 표현 자체는 거기).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 여섯 줄을 던지면 (예측)

```csharp
// cs05b-wrap.cs
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
```

- 여섯 줄의 출력을 **각각** 맞힐 수 있는가?
- 이 소스의 **컴파일 진단은 몇 줄**인가?
- `unchecked(big + 1)` 이 윗줄과 **같은가 다른가** — 왜인가?
- `(long)int.MaxValue + 1` 과 `(long)(int.MaxValue + 1)` 은 **같은가**?

### 2. `checked` 를 붙이면 무엇이 나오나 (예측)

```csharp
// cs05b-checked.cs
using System;

int big = int.MaxValue;
int boom = checked(big + 1);
Console.WriteLine(boom);
```

- 예외 **타입 이름**과 **메시지 전문**을 적을 수 있는가?
- **`cc exit` 과 `run exit`** 은 각각 몇인가?
- 트레이스가 **몇 줄**인가 — 왜 그 길이인가?
- ★ `unchecked(1 / 0)` 은 **무엇을 하는가** — `checked` 가 지배하는 범위 밖인가 안인가?
- `unchecked(decimal.MaxValue + 1m)` 은? `double` 이 넘치면 무엇이 되는가?

### 3. ★★ 네 줄 중 몇 줄이 컴파일을 통과하나 (예측)

```csharp
// cs05b-const.cs
using System;

int a = int.MaxValue + 1;
const int b = checked(int.MaxValue + 1);
byte c = 300;
int d = unchecked(int.MaxValue + 1);
Console.WriteLine($"{a} {b} {c} {d}");
```

- **진단이 몇 줄** 나오고, 각각 **몇 번 줄**에 대한 것인가?
- `int a = int.MaxValue + 1;` 에는 `checked` 가 **없는데** 왜 걸리는가?
- 5번 줄(`byte c = 300;`)의 에러 **번호가 다른** 이유는?
- 6번 줄은 **왜 통과했는가**?

### 4. ★★ 같은 소스, 플래그만 다르면 (예측)

```csharp
// cs05b-flag.cs
using System;

int big = int.MaxValue;
Console.WriteLine($"int.MaxValue + 1 = {big + 1}");
```

- `csc -out:ex.dll …` 로 던진 것과 `csc -checked+ -out:ex.dll …` 로 던진 것의 **출력과 `run exit`** 은?
- MSBuild 에서 이 플래그를 켜는 **속성 이름**은?
- 이 플래그는 **상수식**에도 영향을 주는가?
- 내가 `-checked+` 로 빌드한 프로젝트가 **참조하는 라이브러리** 안쪽은 어떻게 되는가?

### 5. ★★★ `checked` 블록 안에서 부른 메서드는 (예측)

```csharp
// cs05b-textual.cs
using System;

int factor = 2;

try {
    checked { Console.WriteLine($"Multiply(factor, int.MaxValue) = {Multiply(factor, int.MaxValue)}"); }
} catch (OverflowException e) { Console.WriteLine($"  터짐: {e.Message}"); }

try {
    checked { Console.WriteLine(Multiply(factor, factor * int.MaxValue)); }
} catch (OverflowException e) { Console.WriteLine($"  인자 계산에서 터짐: {e.Message}"); }

static int Multiply(int a, int b) => a * b;
```

- 첫 번째 `Multiply` 호출의 출력은? **터지는가 안 터지는가**?
- 두 번째는? **무엇이 두 호출을 가르는가**?
- 「`checked` 를 블록으로 감쌌으니 그 안의 계산은 전부 안전하다」는 참인가?

### 6. ★★★ `double` 과 `decimal` 을 나란히 던지면 (예측)

```csharp
// cs05b-money.cs
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
```

- 열한 줄의 출력을 **각각** 맞힐 수 있는가?
- `0.3.ToString("G17")` 이 **`0.3` 이 아닌 것**을 예상했는가 — 그것이 뜻하는 바는?
- ★★ **마지막 세 줄** — `1m / 3m * 3m` 과 `1.0 / 3.0 * 3.0` 중 **어느 쪽이 `1` 인가**?
- 그 결과가 「`decimal` 이 더 정확하다」라는 문장에 무엇을 하는가?

### 7. ★ `decimal` 의 대가 (왜)

```csharp
// cs05b-cost.cs
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
```

- `Unsafe.SizeOf` 세 줄과 박싱 세 줄의 숫자는?
- `decimal.GetBits(0.1m)` 의 네 칸이 각각 **무엇**인가 — **2의 지수는 어디 있는가**?
- `1.10m` 과 `1.1m` 은 `==` 가 참인가? `GetHashCode()` 는? **`ToString()` 은**?
- 그 차이가 **기능인 자리**를 하나 댈 수 있는가?

### 8. ★★★ IL 여섯 벌 (왜)

```csharp
// cs05b-il.cs
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
```

- `AddInt` 와 `AddIntChecked` 의 **명령 이름**은 각각 무엇인가?
- `AddDouble` 은 `AddInt` 와 **같은 명령인가 다른 명령인가**?
- ★★ `AddDecimal` 에는 무엇이 나오는가 — **명령인가 호출인가**?
- `ToInt` 와 `ToIntChecked` 는?
- 이 여섯 벌이 「`decimal` 이 부동소수점이 아니다」를 어떻게 증명하는가?

### 9. ★ `==` 가 위험한 자리 (경계)

```csharp
// cs05b-eq.cs
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
```

- **컴파일 진단이 나오는가** — 난다면 몇 번 코드이고 무엇을 묻는가?
- `nan == nan` 과 `nan.Equals(nan)` 은 **같은가**?
- 그렇다면 `Array.IndexOf(new[]{nan}, nan)` 은 **몇**인가?
- `0.0 == -0.0` 은? 그런데 `1.0 / -0.0` 은?
- `(double)0.1f == 0.1` 은 참인가 — 왜인가?

### 10. ★★★ 공식 문서가 적어 둔 값과 이 판의 값 (경계)

- `unchecked((int)double.MaxValue)` 는 무엇인가 — **감기는가 포화하는가**?
- `unchecked((int)double.NaN)` 은?
- ★★ 둘 중 **어느 쪽이 언어 보장이고 어느 쪽이 런타임 구현**인가?
- 「Learn 문서에 이렇게 적혀 있다」가 **근거가 되는가**?

### 11. 무엇을 고르나 (경계)

- 돈을 담는 타입으로 **`decimal` 말고 다른 정답**이 있는가 — 그 대가는?
- 해시 함수를 짤 때 **`unchecked` 를 명시하는 이유**는?
- `decimal` 을 **쓰면 안 되는** 계산은?
- `byte`/`short` 를 고르는 **올바른 이유**와 **틀린 이유**는?

### 12. 다른 주제와 잇기 (연결)

- 「박싱이 24바이트인 것」의 정본은 목록의 몇 번인가?
- 「2진 부동소수점이 왜 0.1 을 못 담나」의 정본은 어느 폴더인가?
- `System.Decimal::op_Addition` 이 무엇인지의 정본은 목록의 몇 번인가?
- C 갈래에서 정수 오버플로가 이것과 **결정적으로 다른** 점은?
- Java 에는 `checked` 에 해당하는 **문법이 있는가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
