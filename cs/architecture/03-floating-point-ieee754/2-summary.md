# architecture/03-floating-point-ieee754 — IEEE 754 부동소수: 부호·지수·가수, ε, 특수값(NaN·Inf·−0) — 정리 (힌트)

## 해결하는 문제

실수는 끝없이 많다. 64비트로는 2⁶⁴개의 비트 패턴밖에 못 만든다.\
그래서 실수 대부분은 **가장 가까운 표현 가능한 값**으로 반올림돼 저장된다. 또 0으로 나누기·음수의 제곱근처럼 답이 없는 연산에도 결과를 내야 한다.

쉬운 예: 유효숫자 3자리 과학 계산기.

```text
  1/3        → 3.33 × 10⁻¹          (0.000333… 만큼 버림)
  1000 + 1   → 1.00 × 10³            (1 이 자리에 못 들어가 사라짐)
  큰 수는 듬성듬성, 작은 수는 촘촘하게 표현된다
```

똑같은 구조다.\
`double`은 2진수 유효숫자 53자리 계산기다. 10진수 0.1은 2진수로 끝나지 않아 저장하는 순간 반올림된다.

실무 예:
- `0.1 + 0.2 == 0.3`이 `false`라 테스트가 깨진다.
- 정렬 키에 `NaN`이 섞이자 리스트가 정렬되지 않은 채 남는다. 비교자 기반 `TreeSet`에서 `NaN`이 조용히 사라진다(아래 실험).
- 4.35달러를 `(long)(price * 100)`으로 센트로 바꿨더니 434센트가 저장된다(아래 실험).
- JSON으로 내려간 64비트 ID의 끝자리가 바뀐다([api-design/29](../../api-design/29-api-incidents/2-summary.md)).

## 동작·원리

### 1. 필드 세 개 — 부호·지수·가수

```text
  binary64 (Java double, C double — C는 IEC 60559 부록 F를 따르는 구현, 예: x86-64 gcc)
  ┌─┬───────────┬────────────────────────────────────────────────────┐
  │s│  e (11)   │                     f (52)                         │
  └─┴───────────┴────────────────────────────────────────────────────┘
  63 62       52 51                                                  0

  정규수 값 = (−1)ˢ × 1.f₂ × 2^(e − 1023)
              맨 앞 1 은 저장하지 않는다 (숨은 비트) → 유효숫자 53비트

  binary32 (float): s 1 · e 8 · f 23, 바이어스 127, 유효숫자 24비트
```

- *지수 바이어스(bias)*: 지수를 부호 없이 저장하려고 더해 두는 값. binary64는 1023, binary32는 127(Goldberg 1991, "biased representation").
- *숨은 비트(hidden bit)*: 정규수는 맨 앞자리가 1로 정해져 있어 저장하지 않는다. binary32는 23비트로 24비트 정밀도를 얻는다(Goldberg).
- 실제 값 `0.1`을 분해한 것(실험):

```text
  0.1   0x3FB999999999999A   s=0  e=01111111011 (1019)  f=1001 1001 1001 … 1010
        → 1.1001100110011…₂ × 2^(1019 − 1023) = 1.6 × 2⁻⁴ 근처
  −2.5  0xC004000000000000   s=1  e=10000000000 (1024)  f=0100 0…
        → −1.01₂ × 2¹ = −2.5
```

- 0.1의 가수 마지막이 `…1001 1010`으로 끝난다. 무한 반복 `1001 1001…`을 52비트에서 반올림해 올림이 일어났다.
- 원고 [foundations/data-representation](../../foundations/data-representation/README.md) §2.1(단정도·배정도 비트 수), §2.3(8비트 부동소수 저장·복구 손실 예), §2.7(0.1의 비트 분해)에 같은 분해가 Python으로 있다. 여기서는 Java 실험으로 특수값까지 넓힌다.
- 이 영역의 근거 교재는 CS:APP 3판 2.4.2 "IEEE Floating-Point Representation", 2.4.3 "Example Numbers"다.

### 2. 지수 칸의 끝값 두 개가 특수값이다

```text
  e (11비트)             f          뜻                         예 (비트 패턴)
  ───────────────────────────────────────────────────────────────────────────────
  000…0 (0)              0          ±0                         0x0000000000000000 /  0x8000000000000000
  000…0 (0)              ≠ 0        비정규수(subnormal)         Double.MIN_VALUE = 0x0000000000000001 = 4.9E-324
  1 … 2046               아무거나    정규수                      1.0 = 0x3FF0000000000000
  111…1 (2047)           0          ±무한대                     0x7FF0000000000000
  111…1 (2047)           ≠ 0        NaN                        Java Double.NaN = 0x7FF8000000000000
```

- 이 표는 Goldberg 1991 Table D-2 "IEEE 754 Special Values"를 binary64의 지수 값으로 옮긴 것이다. 비트 패턴은 실험 출력이다.
- *비정규수(subnormal)*: 지수가 최소일 때 숨은 비트를 0으로 보고 0까지의 간격을 메우는 값. 0 근처에서 정밀도를 조금씩 잃으며 내려간다(점진적 언더플로, JLS §4.2.3·§4.2.4 예제).
- *무한대(Inf)*: 넘침(`1e308 * 10`)과 0으로 나누기(`1/0.0`)의 결과.
- *NaN(Not a Number)*: 답이 없는 연산(`0.0/0.0`, `Inf − Inf`)의 결과. 비트 패턴이 여럿이다. f가 0이 아니면 다 NaN이다.
- *부호 있는 0*: `+0.0`과 `−0.0`은 비트가 다르다. `1/+0.0 = +Inf`, `1/−0.0 = −Inf`(JLS §4.2.3, 실험).

### 3. 수직선 — 간격이 2배씩 커진다

```text
  0  subnormal   [2⁻¹⁰²²,2⁻¹⁰²¹) … [1,2)     [2,4)      [4,8)  …  [2⁵³, 2⁵⁴)
  |··············|·····|·····|·· … |·|·|·|·|·|  ·  ·  ·  ·|   ·   ·  … |  2   2   2
                                   간격 2⁻⁵²   간격 2⁻⁵¹               간격 2 → 홀수 정수 표현 불가
```

- 정규수 구간 [2ᵏ, 2ᵏ⁺¹) 안에는 값이 2⁵²개 고르게 있다. 구간이 오른쪽으로 갈수록 간격이 2배가 된다. 비정규수 구간(2⁻¹⁰²² 미만)은 간격이 2⁻¹⁰⁷⁴로 일정하다(`Math.ulp(Double.MIN_NORMAL/2)` = 4.9E-324).
- 그래서 **상대 오차**는 거의 일정하고 **절대 오차**는 수의 크기에 비례한다.
- 2⁵³ = 9,007,199,254,740,992 이상에서는 간격이 2 이상이라 홀수 정수를 담지 못한다([2⁵³, 2⁵⁴)에서 2, [2⁵⁴, 2⁵⁵)에서 4, … — `Math.ulp` 실험). `(long)(double) 9007199254740993L`은 …992가 된다(실험).
- 간격(ulp)과 누적 오차·Kahan 합은 [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md)에 자세히 있다. 여기서는 다시 다루지 않는다.

### 4. 반올림과 ε — "1 다음 수"와 "1에 더해서 티가 나는 가장 작은 수"는 다르다

```text
  1.0                    1 + 2⁻⁵³ (정확히 가운데)          1 + 2⁻⁵² = nextUp(1.0)
   |──────────────────────────┼──────────────────────────────|
   ◀── 이 구간의 x 는 1+x → 1.0          이 구간의 x 는 1+x → 1+2⁻⁵² ──▶
                 가운데(2⁻⁵³)는 짝수 쪽 = 1.0 (가수 끝 비트 0)
```

- 기본 반올림은 "가장 가까운 값, 동률이면 끝 비트가 0인 쪽"이다(JLS §15.4 round to nearest = IEEE 754 roundTiesToEven).
- *기계 엡실론(1 다음 수와의 간격)*: binary64에서 2⁻⁵² ≈ 2.22×10⁻¹⁶. Java `Math.ulp(1.0)`, Python `sys.float_info.epsilon`.
- *"1 + x ≠ 1인 가장 작은 x"*: 2⁻⁵³ 바로 위의 값(≈ 1.11×10⁻¹⁶)이다. 2⁻⁵²가 아니다.
  - 실험: `1 + 2⁻⁵³ == 1`은 `true`(가운데라 짝수 쪽), `1 + nextUp(2⁻⁵³) == 1`은 `false`이고 결과가 `1.0000000000000002`다. 이때 x = `1.1102230246251568E-16`.
  - 흔한 오해: "엡실론은 1에 더해서 1이 아닌 결과가 나오는 가장 작은 수다." 반올림 때문에 그 경계는 엡실론의 절반 근처다.
- 참고: 원고 §2.2(98행) 뒷부분의 "1.0+epsilon != 1.0이 성립하는 가장 작은 값"은 위 실험처럼 맞지 않는다. 2⁻⁵³보다 조금 큰 값도 성립한다. 원고 §2.4의 "1.0과 그 다음으로 표현 가능한 수 사이의 간격"이 바른 정의다.
- IEEE 754(1985판을 설명한 Goldberg 1991)는 기본 반올림 외에 0 쪽·+∞ 쪽·−∞ 쪽 반올림을 요구하고, 예외가 나면 끈적한(sticky) 상태 플래그를 세우고 사용자가 읽을 수 있게 하라고 정한다.
  - 표준 요구 vs 구현: C는 `<fenv.h>`로 반올림 모드와 플래그를 노출한다(아래 실험 — 같은 `0.1+0.2`가 모드에 따라 위·아래 이웃으로 갈린다). Java는 JLS §15.4가 "두 가지 반올림 정책"(산술은 round to nearest, 정수 변환·나머지는 round toward zero)만 정의하고, JLS 4·15장에서 상태 플래그를 읽는 수단은 찾지 못했다.

### 5. 비교 — `==`와 `equals`/`compare`는 다른 관계다

```text
                  NaN == NaN    +0.0 == −0.0    정렬에서 NaN 자리       −0.0 vs +0.0
  == , <, >       false         true            비교 불가(모두 false)   같음
  Double.equals   true          false           —                      다름
  Double.compare  0 (같음)      1 (+0 이 큼)    가장 큼(+Inf 보다 큼)   −0.0 < +0.0
```

- `==`·`<`는 IEEE 754 수치 비교다. NaN은 순서가 없어서 NaN이 끼면 `<`·`<=`·`>`·`>=`·`==`가 모두 `false`, `!=`만 `true`다. `x != x`는 x가 NaN일 때만 참이다(JLS §4.2.3, §15.20.1).
  - 그래서 `==`는 동치 관계가 아니다. 반사성(x == x)이 NaN에서 깨진다(Java 21 `Double` Javadoc "Floating-point Equality, Equivalence, and Comparison").
- `Double.equals`·`Double.compare`는 `doubleToLongBits` 기준의 *표현 동치*다. 원시 비트가 아니라 모든 NaN 패턴을 하나로 모은 비트다(Javadoc "representation equivalence" — 원시 비트 비교는 `doubleToRawLongBits`). 그래서 NaN끼리 같고, +0.0과 −0.0은 다르며, 전체 순서(−0.0 < +0.0, NaN이 가장 큼)를 정한다. 같은 Javadoc은 이 덕분에 NaN을 `HashSet` 원소·`HashMap` 키로, `SortedSet`·`SortedMap`에 쓸 수 있다고 적는다.
- 손으로 쓴 비교자 `(p, q) -> p < q ? -1 : (p > q ? 1 : 0)`는 NaN을 **어떤 값과도 같다**고 답한다. 추이성이 깨진다(1 = NaN, NaN = 2인데 1 < 2).
- `Math.min(0.0, -0.0)`은 −0.0이다. `Math.min`·`max`는 −0.0을 +0.0보다 작게 본다(JLS §15.20.1).

### 6. 돈과 10진 소수

```text
  4.35 (10진)  →  저장: 4.3499999999999996447286321199499070644378662109375
  × 100        →  434.99999999999994
  (long)       →  434     (0 쪽으로 버림)       Math.round → 435
```

- 10진 소수 대부분(0.1, 0.29, 4.35 …)은 2진으로 끝나지 않아 저장 시점에 이미 오차가 있다. `new BigDecimal(double)`은 그 저장값을 그대로 10진으로 보여 준다(Java 21 `BigDecimal(double)` 문서가 0.1 예로 경고하고 `String` 생성자를 권한다).
- 금액은 정수 최소 단위(`long` 센트·원) 또는 `BigDecimal("4.35")`(문자열에서)로 둔다. 반올림 모드·배분은 [domain-modeling/14](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md).

### 실험: 필드·특수값·비교·돈·반올림 모드

- 환경: i7-13700HX, Linux 7.0.0-34. OpenJDK 21.0.12+8-LTS(`eclipse-temurin:21-jdk`, Docker `--cpus=2 --network none`), gcc 13.3.0, Python 3.12.3(호스트). 2026-10-07. 결정적 출력(2회 실행 같음).
- Java(`Fp.java`) 핵심:

```java
long b = Double.doubleToRawLongBits(d);                         // 필드 분해
naive.sort((p, q) -> p < q ? -1 : (p > q ? 1 : 0));            // NaN 을 "같다"고 보는 비교자
right.sort(Double::compare);
new TreeSet<Double>((p, q) -> p < q ? -1 : (p > q ? 1 : 0)).addAll(List.of(1.0, NaN, 2.0, 3.0));
m.put(0.0, "zero"); m.put(-0.0, "negzero");                     // HashMap 키
```

- 출력(발췌):

```text
1.0        0x3FF0000000000000  s=0 e=01111111111(1023) f=000000000000...
0.1        0x3FB999999999999A  s=0 e=01111111011(1019) f=100110011001...
-0.0       0x8000000000000000  s=1 e=00000000000(   0) f=000000000000...
4.9E-324   0x0000000000000001  s=0 e=00000000000(   0) f=000000000000...
Infinity   0x7FF0000000000000  s=0 e=11111111111(2047) f=000000000000...
NaN        0x7FF8000000000000  s=0 e=11111111111(2047) f=100000000000...
0.1+0.2 = 0.30000000000000004, == 0.3 ? false, 0.1f+0.2f == 0.3f ? true
new BigDecimal(0.1)   = 0.1000000000000000055511151231257827021181583404541015625
BigDecimal.valueOf(0.1) = 0.1
Math.ulp(1.0) = 2.220446049250313E-16 (2^-52), Math.nextUp(1.0) = 1.0000000000000002
1 + 2^-53 == 1 ? true   (정확히 가운데 -> 짝수 쪽 1.0)
1 + nextUp(2^-53) == 1 ? false, 값 = 1.0000000000000002, x = 1.1102230246251568E-16
1e308*10 = Infinity, 1/0.0 = Infinity, 1/-0.0 = -Infinity, 0.0/0.0 = NaN, Inf-Inf = NaN
NaN == NaN ? false, NaN != NaN ? true, NaN < 1 ? false, NaN > 1 ? false
Double.compare(NaN, NaN) = 0, Double.compare(NaN, +Inf) = 1, Double.valueOf(NaN).equals(NaN) = true
0.0 == -0.0 ? true, Double.compare(0.0, -0.0) = 1, Double.valueOf(0.0).equals(-0.0) = false, Math.min(0.0,-0.0) = -0.0
손 비교자 정렬   = [3.0, NaN, 1.0, 2.0, NaN, 0.5, 4.0]
Double::compare = [0.5, 1.0, 2.0, 3.0, 4.0, NaN, NaN]
손 비교자 TreeSet(1,NaN,2,3) = [1.0, 2.0, 3.0]  size=3
자연 순서 TreeSet = [1.0, 2.0, 3.0, NaN], contains(NaN)=true
HashMap 키 0.0 과 -0.0 -> 2개 {0.0=zero, -0.0=negzero}
2^53 + 1 = 9007199254740992, (long)(double)9007199254740993L = 9007199254740992
```

- 관찰 1: 손 비교자 정렬은 입력 순서 `[3.0, NaN, 1.0, 2.0, NaN, 0.5, 4.0]`을 **한 칸도 바꾸지 못했다**. 예외도 없었다(원소 7개라 `TimSort`의 계약 위반 검사까지 가지 않았다 — 해석, [algorithm/09](../../algorithm/09-sorting-in-practice/2-summary.md) 장애 절 참고).
- 관찰 2: 손 비교자 `TreeSet`은 NaN을 "1.0과 같다"고 보고 넣지 않았다. 원소가 조용히 하나 사라졌다.
- 관찰 3: `0.1f + 0.2f == 0.3f`는 `true`다. `float`에서는 반올림이 우연히 맞아떨어진다. "0.1 + 0.2 ≠ 0.3"은 `double` 한정의 사실이다.
- Java(`Money.java`) 출력:

```text
4.35*100 = 434.99999999999994, (long)(4.35*100) = 434, Math.round = 435
0.29*100 = 28.999999999999996, (int) = 28
new BigDecimal(4.35) = 4.3499999999999996447286321199499070644378662109375
new BigDecimal("4.35").movePointRight(2) = 435
BigDecimal 2.675 HALF_UP 2자리 = 2.68, new BigDecimal(2.675) HALF_UP = 2.67
```

- C(`fenv.c`, gcc `-O0 -lm`, 피연산자 `volatile`) 출력 — 반올림 모드에 따라 결과와 출력이 달라지고, 예외가 플래그로 남는다:

```text
TONEAREST  0.1+0.2 = 0.30000000000000004
UPWARD     0.1+0.2 = 0.30000000000000005
DOWNWARD   0.1+0.2 = 0.29999999999999998
TOWARDZERO 0.1+0.2 = 0.29999999999999998
after 0.1+0.2: FE_INEXACT=1
after 1/0.0  : FE_DIVBYZERO=1 (result inf)
after 0/0    : FE_INVALID=1 (result -nan)
after 1e308*10: FE_OVERFLOW=1 (result inf)
```

- 관찰 4-1(판정 재실험 `fenvbits.c`, 같은 gcc 13.3 `-O0`): 위 출력의 십진 차이가 모두 덧셈 결과 비트의 차이는 아니다. 덧셈 비트는 TONEAREST·UPWARD가 둘 다 `0x3fd3333333333334`, DOWNWARD·TOWARDZERO가 둘 다 `0x3fd3333333333333`이었다. 저장된 0.1과 0.2의 정확한 합이 두 이웃 값의 정확히 가운데라(Python `fractions`로 확인) 짝수 쪽(…34)과 +∞ 쪽이 같은 값이 된다. UPWARD의 `…05`는 printf의 십진 변환도 현재 반올림 모드를 따른 결과다. 같은 비트를 TONEAREST로 되돌려 찍으면 `…04`다.
- 관찰 4: gcc 13.3은 `-Wall`에서 `#pragma STDC FENV_ACCESS ON`을 무시한다는 경고(`-Wunknown-pragmas`)를 냈다. 최적화가 켜지면 모드 변경이 무시될 수 있어 `-O0`과 `volatile`로 돌렸다.
- 관찰 5: x86-64에서 `0/0`의 NaN은 부호 비트가 켜진 패턴이라 glibc가 `-nan`으로 찍었다. Java `Double.NaN`(0x7FF8…)과 비트가 다르지만 둘 다 NaN이다.
- Python 3.12.3: `sys.float_info`의 `mant_dig=53, epsilon=2.220446049250313e-16, rounds=1`. `struct.pack('<d', 0.1).hex()` = `9a9999999999b93f`(리틀 엔디안), `'>d'` = `3fb999999999999a` — 바이트 순서는 [06](../06-byte-order-and-alignment/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **반올림 모드**(🔧): 기본 roundTiesToEven, 방향 반올림(구간 산술), 정수 변환의 0 쪽 버림. 돈의 반올림 모드(`RoundingMode.HALF_EVEN` 등)는 [domain-modeling/14](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md).
- **Kahan 보상 합·쌍별 합**(🔧): 누적 오차를 줄이는 합산 → [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md) 4절.
- **전체 순서 비교자**: `Double.compare`가 NaN·−0.0까지 순서를 정해 정렬·`TreeMap`·이진 탐색이 성립한다 → [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md).
- **비트 수준 정렬 키**: `doubleToLongBits` 뒤 부호에 따라 비트를 뒤집으면 바이트 사전순이 수치 순서와 같아진다(정렬 가능한 키 인코딩 — [06](../06-byte-order-and-alignment/2-summary.md)의 부호 비트 뒤집기와 같은 생각).
- **해시**: `Double.hashCode`는 `doubleToLongBits` 기반이라 0.0과 −0.0이 다른 키가 된다(실험의 `HashMap` 2개).

## 적용 — 풀어나가는 법

### 1. 증상 → 원인

| 증상 | 의심 |
|---|---|
| 같아야 할 두 값의 `==`가 `false`, 끝자리 …0004 | 10진 소수의 2진 반올림 |
| 정렬·중복 제거·최댓값이 이상하다, 원소가 사라진다 | `NaN`과 손 비교자, `<`로 쓴 비교 |
| 집계 키에 `0.0`과 `-0.0` 두 줄 | 부호 있는 0 + `equals`·해시 |
| 센트·원 변환에서 1 모자람 | `(long)(x * 100)`의 0 쪽 버림 |
| 큰 정수 ID·카운터의 끝자리 변형, 1을 더해도 안 변함 | 2⁵³ 초과 정수(JSON·JS `Number` 포함) |
| 결과가 `Infinity`·`NaN`으로 퍼짐 | 넘침, 0으로 나누기, `0/0`, `Inf − Inf`의 전파 |

### 2. 확인하는 법

- 저장된 정확한 값을 본다: Java `new BigDecimal(d)`, `Double.toHexString(d)`, `Long.toHexString(Double.doubleToRawLongBits(d))`. Python `float.hex()`, `decimal.Decimal(x)`.
- NaN의 출처 찾기: 사칙연산에서 NaN은 연산 사슬을 따라 전파된다. 일부 수학 함수는 예외다(`Math.hypot(NaN, ∞)` = ∞, `Math.pow(NaN, 0)` = 1 — Java 21 `Math` Javadoc, 실험). 입력 단계마다 `Double.isNaN`·`Double.isFinite`를 단언해 처음 생긴 곳을 좁힌다.
- C에서는 `fetestexcept(FE_INVALID | FE_DIVBYZERO | FE_OVERFLOW)`로 어느 단계에서 예외 조건이 생겼는지 플래그로 본다(실험).

### 3. 코드로 고정한다 (Java 21)

```java
list.sort(Double::compare);                                // 손 비교자 대신
boolean close = Math.abs(a - b) <= 1e-9 * Math.max(Math.abs(a), Math.abs(b)); // 상대 허용 오차(예시 값)
long cents = new BigDecimal(text).movePointRight(2).longValueExact();          // 문자열 → 정확한 센트
if (!Double.isFinite(x)) throw new IllegalArgumentException("non-finite: " + x); // 경계에서 NaN/Inf 차단
double key = (x == 0.0) ? 0.0 : x;                         // 집계 키에서 −0.0 을 +0.0 으로 정규화
```

- 허용 오차 비교의 상수는 업무 정밀도에서 정한다. 0 근처에서는 상대 오차가 무의미해 절대 허용 오차를 함께 둔다.

## 장애 시나리오와 대처

### 1. `0.1 + 0.2 != 0.3` — 대사 실패·테스트 깨짐 (⚠ 커리큘럼)

- **현상**: 합계 검증 `if (sum == expected)`가 가끔 실패한다. 스냅샷 테스트의 기대값 `0.3`이 `0.30000000000000004`와 다르다.
- **보이는 형태**: 예외 없음. 로그의 `…0000004`, `…9999998` 꼬리.
- **원인**: 0.1·0.2·0.3이 각각 반올림돼 저장되고, 합도 반올림된다(4절, 실험).
- **대처**: 금액·수량은 정수·`BigDecimal`. 측정값은 허용 오차 비교. 출력은 필요한 자리에서 반올림해 표시한다.

### 2. `NaN != NaN` — 정렬·집합 붕괴 (⚠ 커리큘럼)

- **현상**: 점수 정렬 결과가 섞여 있다. `TreeSet`·`TreeMap` 기반 중복 제거 뒤 원소 수가 줄었다. 최댓값 계산이 NaN 위치에 따라 달라진다.
- **보이는 형태**: 예외 없이 틀린 순서(작은 입력). 입력이 32개 이상이면 `IllegalArgumentException: Comparison method violates its general contract!`가 날 수 있다([algorithm/09](../../algorithm/09-sorting-in-practice/2-summary.md)).
- **원인**: `<`·`>`로 쓴 비교자는 NaN을 어떤 값과도 "같다"고 답해 추이성을 깨뜨린다(5절, 실험: 정렬이 입력 그대로, `TreeSet`에서 NaN 소실).
- **대처**: `Double::compare`·`Comparator.comparingDouble`. 그보다 먼저 NaN이 들어온 경계(0/0, 빈 집합의 평균, 파싱)를 막는다.

### 3. 돈을 `double`로 — 원 단위 불일치 (⚠ 커리큘럼)

- **현상**: 4.35달러 결제가 434센트로 저장된다. 정산 리포트가 PG사 금액과 1원·1센트씩 어긋난다.
- **보이는 형태**: 대사 배치의 "차액 0.01" 행. `new BigDecimal(double)`로 만든 값의 긴 꼬리(`4.3499999999999996…`).
- **원인**: 4.35가 4.3499…로 저장되고, 곱한 뒤 `(long)`이 0 쪽으로 버린다(6절, 실험). `new BigDecimal(2.675)`를 HALF_UP으로 2자리 반올림하면 2.68이 아니라 2.67이다(실험).
- **대처**: 입력(문자열·DB `DECIMAL`)에서 바로 `BigDecimal(String)`이나 정수 최소 단위로. `double`을 거치는 변환을 금지 규칙으로 둔다([math/15](../../math/15-numerical-stability/2-summary.md) 장애 1, [domain-modeling/14](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md)).

### 4. `−0.0` — 같은 값이 두 키로 집계

- **현상**: 온도·잔차 집계표에 `0.0`과 `-0.0` 행이 따로 나온다. 캐시 키가 둘로 갈려 적중률이 떨어진다.
- **원인**: `-1e-300 * 1e-300` 같은 언더플로, `x > 0`일 때 `-x * 0`이 −0.0을 만든다. `==`로는 같지만 `Double.equals`·`hashCode`는 다르다(5절, 실험의 `HashMap` 2개).
- **대처**: 키로 쓰기 전에 `x == 0.0 ? 0.0 : x`로 정규화. 표시용 포맷에서 `-0` 처리.

### 5. 2⁵³을 넘는 정수 — ID 끝자리 변형

- **현상**: 64비트 ID가 프런트엔드나 `double`을 거치면 다른 ID로 바뀐다.
- **원인**: binary64 유효숫자가 53비트라 2⁵³ 이상에서 간격이 2 이상이다(3절, 실험 `9007199254740993 → …992`). JSON 숫자를 `double`로 읽는 파서·JS `Number`도 같다.
- **대처**: ID는 문자열로 직렬화. 상세 사건은 [api-design/29-api-incidents](../../api-design/29-api-incidents/2-summary.md).

## 핵심 문장

- binary64는 부호 1·지수 11·가수 52비트이고, 숨은 비트 덕에 유효숫자는 53비트다.
- 지수 칸이 전부 0이면 0과 비정규수, 전부 1이면 무한대와 NaN이다.
- 표현 가능한 값의 간격은 크기에 비례해 2배씩 커진다. 2⁵³을 넘으면 홀수 정수를 못 담는다.
- 기계 엡실론(2⁻⁵²)은 1 다음 수와의 간격이다. "1 + x ≠ 1인 가장 작은 x"는 반올림 때문에 그 절반 근처다.
- `==`는 NaN에서 반사성이 깨지고 +0.0과 −0.0을 같다고 본다. 정렬·집합·해시는 `Double.compare`/`equals`의 전체 순서를 써야 한다.
- 돈은 2진 부동소수로 셀 수 없다. 문자열에서 바로 정수 최소 단위나 `BigDecimal`로 간다.

## 관련 주제·근거

- 선행: [01-number-systems-twos-complement](../01-number-systems-twos-complement/2-summary.md)
- 원고: [foundations/data-representation](../../foundations/data-representation/README.md) §2(부동소수점 — 단정도·배정도, `sys.float_info`, 8비트 예, 엡실론, 0.1+0.2, 2⁵³, 0.1의 비트 분해)
- 이 영역: [02-integer-overflow-and-truncation](../02-integer-overflow-and-truncation/2-summary.md)(부동소수 → 정수 변환), [06-byte-order-and-alignment](../06-byte-order-and-alignment/2-summary.md)(double의 바이트 순서)
- 연결
  - [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md) — ulp, 합산 오차, Kahan 합, 파국적 상쇄
  - [domain-modeling/14-money-arithmetic-rounding-allocation](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md) — 금액 표현·반올림·배분
  - [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md) — 비교자 계약, NaN
  - [api-design/29-api-incidents](../../api-design/29-api-incidents/2-summary.md) — 2⁵³ 넘는 ID의 정밀도 손실
  - [languages/c/syntax/04-floating-point-types-and-conversions](../../../languages/c/syntax/04-floating-point-types-and-conversions/2-summary.md) — C의 부동소수 타입·`-ffast-math`
- 근거
  - D. Goldberg, "What Every Computer Scientist Should Know About Floating-Point Arithmetic", ACM Computing Surveys, 1991년 3월 — 숨은 비트, 바이어스(127/1023), Table D-2 특수값, Signed Zero(+0 = −0 비교), 반올림 모드(기본 nearest + 세 방향), 상태 플래그(sticky, 읽기·쓰기 제공 요구) <https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html>. 표준 본문 IEEE 754-2019는 유료라 열지 않았다.
  - CS:APP 3판 — 2.4.2 IEEE Floating-Point Representation, 2.4.3 Example Numbers, 2.4.4 Rounding, 2.4.6 Floating Point in C(절 번호: <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf> 목차)
  - JLS SE 21 §4.2.3(binary32/64 대응, 비정규수, ±0, NaN 무순서), §15.4(반올림 정책 두 가지, roundTiesToEven), §15.20.1(비교, `Math.min`/`max`의 −0.0) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html>
  - Java SE 21 API `Double`("Floating-point Equality, Equivalence, and Comparison", `compareTo`의 전체 순서), `BigDecimal(double)` 주의 문단 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Double.html>
  - Python 3 `sys.float_info` 문서 <https://docs.python.org/3/library/sys.html#sys.float_info>
- 실험 목록
  - `Fp.java` — 필드 분해(0.1·1.0·−2.5·±0·MIN_VALUE·MAX_VALUE·Inf·NaN), 0.1+0.2(double/float), `BigDecimal(0.1)`, ε 경계(1 + 2⁻⁵³, nextUp), 특수값 연산, NaN·±0 비교, 손 비교자 vs `Double::compare` 정렬·`TreeSet`, `HashMap` ±0 키, 2⁵³. OpenJDK 21.0.12, Docker `--cpus=2 --network none`.
  - `Money.java` — 4.35·0.29 센트 변환, `BigDecimal(double)` vs `String`, 2.675 HALF_UP. 같은 환경.
  - `fenv.c` — 반올림 모드 4종의 0.1+0.2, `FE_INEXACT`·`FE_DIVBYZERO`·`FE_INVALID`·`FE_OVERFLOW` 플래그. gcc 13.3.0 `-O0 -lm`, 호스트.
  - Python 3.12.3 `sys.float_info`, `struct.pack` 0.1 바이트. 호스트.
  - (2차 리뷰 판정 재실험) `fenvbits.c` — 모드별 0.1+0.2의 결과 비트와 모드별 printf 출력, Python `fractions`로 정확한 합이 이웃 두 값의 가운데임을 확인. gcc 13.3.0 `-O0 -lm`, 호스트. `NanProp.java` — `Math.hypot(NaN, ∞)`·`Math.pow(NaN, 0)`, `Math.ulp`(2⁵³·2⁵⁴·비정규수), 다른 NaN 패턴의 `equals`·`compare`. OpenJDK 21, Docker `--cpus=2 --network none`. 파일 위치: scratchpad `arch/adj-01/`.
  - 파일 위치: scratchpad `arch/01/e03/`.
