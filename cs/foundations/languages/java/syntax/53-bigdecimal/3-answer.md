# java/syntax/53 — `BigDecimal`: 스케일·반올림·`equals` vs `compareTo` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> JDK 소스는 `lib/src.zip` 의 실파일을 그대로 옮겼다.\
> 실행 파일명은 전부 `Ex.java` 로 고정했다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ `equals` 와 `compareTo`

**출력** (JDK 21.0.5 — 17·25 동일)

```text
new BigDecimal("1")    toString=1          unscaledValue=1      scale=0
new BigDecimal("1.0")  toString=1.0        unscaledValue=10     scale=1
new BigDecimal("1.00") toString=1.00       unscaledValue=100    scale=2

a.equals(b)      = false
a.compareTo(b)   = 0
a.compareTo(b)==0= true
a.hashCode()     = 311
b.hashCode()     = 3102
```

**여섯 줄의 출력**

- `a.equals(b)` -> **false**
- `a.compareTo(b)` -> **0**
- `a.hashCode()` -> **311**
- `b.hashCode()` -> **3102**
- `a.unscaledValue() / a.scale()` -> **10 / 1**
- `b.unscaledValue() / b.scale()` -> **100 / 2**

```text
  a = 1.0                          b = 1.00
  +---------------------+          +---------------------+
  | unscaled = 10       |          | unscaled = 100      |
  | scale    = 1        |          | scale    = 2        |
  +---------------------+          +---------------------+
   값 = 10 x 10^-1 = 1              값 = 100 x 10^-2 = 1

   값은 같다 -> compareTo == 0
   카드가 다르다 -> equals == false
```

**`equals` 가 `false` 인 이유 — 구현 한 줄**

```java
// JDK 21.0.5  java.base/java/math/BigDecimal.java  3226~3232행 — 실제 소스 그대로
public boolean equals(Object x) {
    if (!(x instanceof BigDecimal xDec))
        return false;
    if (x == this)
        return true;
    if (scale != xDec.scale)
        return false;
    ...
```

- **`if (scale != xDec.scale) return false;`** 한 줄이다.
- unscaled 값을 비교하기도 전에 스케일에서 걸러진다.

**해시가 다른 이유**

```java
// JDK 21.0.5  java.base/java/math/BigDecimal.java  3291~3299행 — 실제 소스 그대로
public int hashCode() {
    if (intCompact != INFLATED) {
        long val2 = (intCompact < 0)? -intCompact : intCompact;
        int temp = (int)( ((int)(val2 >>> 32)) * 31  +
                          (val2 & LONG_MASK));
        return 31*((intCompact < 0) ?-temp:temp) + scale;
    } else
        return 31*intVal.hashCode() + scale;
}
```

- 두 반환문 모두 **`+ scale`** 로 끝난다.
- 손계산으로 대조: `a` 는 unscaled 10 이므로 `31 * 10 + 1 = 311`. `b` 는 `31 * 100 + 2 = 3102`.\
  **실행 출력과 정확히 일치한다.**

**계약 위반인가**

- **아니다.** 계약은 "`a.equals(b)` 면 `a.hashCode() == b.hashCode()`" 이고, 여기서는 `equals` 가 `false` 다.
- 해시가 다른 것은 **아무 문제가 없다.**
- 어긋나 있는 것은 `equals` 와 `compareTo` 의 관계이고, 그것은 **계약이 아니라 권고**다.\
  `Comparable` javadoc 원문(JDK 21 `src.zip`):

> It is strongly recommended (though not required) that natural orderings be consistent with equals.
> This is so because sorted sets (and sorted maps) without explicit comparators behave "strangely"
> when they are used with elements (or keys) whose natural ordering is inconsistent with equals.
> In particular, such a sorted set (or sorted map) violates the general contract for set (or map),
> which is defined in terms of the `equals` method.

- "권고이지 의무가 아니다"(though not required)라고 명시돼 있고, 대신 **어기면 문서에 밝히라**고 요구한다.\
  `BigDecimal` 은 그 요구를 지켜 javadoc에 적어 두었다(9번).
- 그리고 javadoc이 말한 "**sorted set 이 이상하게 동작한다**"가 바로 2번에서 본 `TreeSet` size 1이다.

> **계약(contract)** — 클래스가 지키겠다고 javadoc으로 약속한 성질.\
> 예: "`equals` 가 참이면 해시도 같다"는 계약이고, "`compareTo` 가 0이면 `equals` 도 참"은 권고다.

### 2. `HashSet` 과 `TreeSet` 에 같은 셋을 넣으면

**출력**

```text
HashSet.of(1, 1.0, 1.00) = [1.0, 1.00, 1]   size=3
TreeSet.of(1, 1.0, 1.00) = [1.0]   size=1
hash.contains(new BigDecimal("1.000")) = false
tree.contains(new BigDecimal("1.000")) = true

m.get(new BigDecimal("10.00")) = 만원권
m.get(new BigDecimal("10.0"))  = null
m.get(new BigDecimal("10"))    = null
```

**다섯 줄의 출력**

- `hash.size()` -> **3**
- `tree.size()` -> **1**
- `hash.contains(new BigDecimal("1.000"))` -> **false**
- `tree.contains(new BigDecimal("1.000"))` -> **true**
- `m.get(new BigDecimal("10.0"))` -> **null**

```text
  HashSet — equals·hashCode 로 판정        TreeSet — compareTo 로 판정
  +---------------------------------+     +---------------------------------+
  | 1   (해시 ...)  -> 버킷 A       |     | 1 과 1.0 을 비교 -> 0           |
  | 1.0 (해시 311)  -> 버킷 B       |     | 이미 있는 원소로 보고 안 넣는다  |
  | 1.00(해시 3102) -> 버킷 C       |     |                                 |
  | size = 3                        |     | size = 1                        |
  +---------------------------------+     +---------------------------------+
     TreeSet 은 첫 원소 1.0 만 남았다 — 넣은 순서가 결과를 정한다
```

- `TreeSet` 에 남은 것이 `1` 이 아니라 **`1.0`** 인 점에 주목한다.\
  `List.of(a, b, c)` 의 순서가 `1.0`·`1.00`·`1` 이었고, **먼저 들어간 것이 이긴다.**
- 같은 이유로 **입력 순서를 바꾸면 남는 표현이 달라진다.** 조용한 비결정성이다.

**마지막 줄이 예외인가 `null` 인가**

- **`null` 이다.** 예외가 아니다.
- **그것이 더 나쁘다** — 예외였다면 그 줄에서 멈췄을 것이다.\
  `null` 은 "그런 키가 없다"와 구분이 안 되므로, 호출자는 **정상적으로 "없음" 경로**를 탄다.
- 그리고 `hashCode` 가 다르니 **버킷 자체가 달라 `equals` 까지 가지도 못한다.**\
  디버거로 `equals` 에 중단점을 걸어도 안 걸린다.

**금액을 `HashMap` 키로 쓰려면**

1. **스케일을 정규화한다** — 넣을 때도 찾을 때도 `setScale(2, RoundingMode.HALF_UP)` 을 거친다.
2. 또는 **`TreeMap` 을 쓴다** — `compareTo` 기준이라 `10`·`10.0`·`10.00` 이 같은 키가 된다.\
   단 그 순간 `Map` 의 "equals 기준" 계약과 다른 동작을 받아들이는 것이다.
3. 가장 안전한 것은 **애초에 금액을 키로 쓰지 않는 것**이다.\
   키는 식별자(상품 ID 등)로 두고 금액은 값에 둔다.

### 3. `double` 로 만들면 무엇이 들어가는가

**출력** (출력 그대로)

```text
new BigDecimal(0.1)        = 0.1000000000000000055511151231257827021181583404541015625
  scale                    = 55
  precision                = 55
new BigDecimal("0.1")      = 0.1
BigDecimal.valueOf(0.1)    = 0.1

new BigDecimal(0.1+0.2)    = 0.3000000000000000444089209850062616169452667236328125
new BigDecimal(2.0)        = 2
new BigDecimal(0.5)        = 0.5
new BigDecimal(1.1)        = 1.100000000000000088817841970012523233890533447265625

  Double.toString(0.1)     = 0.1
  valueOf(1.0)             = 1.0   scale=1
```

**여섯 줄의 출력**

- `new BigDecimal(0.1)` -> **0.1000000000000000055511151231257827021181583404541015625**
- `new BigDecimal(0.1).scale()` -> **55**
- `new BigDecimal("0.1")` -> **0.1**
- `BigDecimal.valueOf(0.1)` -> **0.1**
- `new BigDecimal(2.0)` -> **2**
- `BigDecimal.valueOf(1.0).scale()` -> **1**

**생성자의 버그인가**

- **아니다.** 생성자는 **정확히 맞게** 동작한다.
- `double` 0.1이 **진짜로** 0.1000000000000000055511151231257827021181583404541015625 이고,
  생성자는 그 값을 **손실 없이** 10진수로 옮긴다.
- javadoc이 그 숫자를 그대로 적어 두었다(JDK 21 소스 원문).

> The results of this constructor can be somewhat unpredictable. One might assume that writing
> `new BigDecimal(0.1)` in Java creates a `BigDecimal` which is exactly equal to 0.1 (an unscaled value
> of 1, with a scale of 1), but it is actually equal to
> 0.1000000000000000055511151231257827021181583404541015625. This is because 0.1 cannot be represented
> exactly as a `double` ... Therefore, it is generally recommended that the String constructor be used
> in preference to this one.

- **javadoc의 숫자와 실행 출력이 한 글자도 다르지 않다.**
- 문제는 생성자가 아니라 **생성자에 `double` 을 넘긴 코드**다. 0.1이라고 쓴 순간 이미 틀렸다.

**`valueOf(0.1)` 이 `"0.1"` 을 내는 이유**

```text
  new BigDecimal(0.1)                 BigDecimal.valueOf(0.1)
        |                                    |
        v                                    v
  double 의 비트를 그대로             Double.toString(0.1) -> "0.1"
  10진수로 전개                              |
        |                                    v
        v                             new BigDecimal("0.1")
  0.10000000000000000555...                  |
                                             v
                                           0.1
```

- **`Double.toString` 을 한 번 거친다.** 실행으로 확인: `Double.toString(0.1) = 0.1`.
- `Double.toString` 은 "그 `double` 을 되살릴 수 있는 **가장 짧은 10진수**"를 낸다.\
  그래서 사람이 쓴 `0.1` 로 되돌아온다.
- javadoc도 이것을 명시한다 — "To get that result, use the `static` `valueOf(double)` method."
- 다만 **`valueOf` 도 완벽하지 않다** — 이미 오차가 섞인 `double`(예: `0.1 + 0.2`)을 넘기면
  `Double.toString` 이 `0.30000000000000004` 를 내므로 그 값이 그대로 들어온다.\
  **문자열 생성자가 유일하게 안전한 입구**다.

**`new BigDecimal(2.0)` 이 깔끔한 이유와 위험**

- `2.0`·`0.5`·`0.25` 처럼 **2의 거듭제곱으로 떨어지는 값**은 `double` 에 정확히 들어간다.
- 그래서 `new BigDecimal(2.0)` 이 그냥 `2` 다.
- **그것이 위험한 이유**: 테스트 데이터가 `1.0`·`2.0`·`0.5` 뿐이면 **이 문제가 절대 안 드러난다.**\
  운영에서 `0.1`·`1.1`·`0.07` 같은 값이 들어오는 순간 자릿수가 55개로 터진다.
- 테스트에 **`0.1` 을 반드시 넣는다.**

### 4. `divide` 와 `setScale` 이 던지는 네 가지

**출력** — 전부 실제로 던져 본 것이다.

```text
1.divide(3)                 -> java.lang.ArithmeticException: Non-terminating decimal expansion; no exact representable decimal result.
1.divide(0)                 -> java.lang.ArithmeticException: Division by zero
0.divide(0)                 -> java.lang.ArithmeticException: Division undefined
1
1.5.setScale(0)             -> java.lang.ArithmeticException: Rounding necessary
1.5.setScale(0,UNNECESSARY) -> java.lang.ArithmeticException: Rounding necessary
1.divide(3,UNNECESSARY)     -> java.lang.ArithmeticException: Rounding necessary
```

(네 번째 줄의 `1` 은 `new BigDecimal("1").setScale(0)` 의 결과다 — 이미 스케일 0이라 안 던진다.)

```text
10.divide(4)                = 2.5
```

**다섯 줄**

| 식 | 결과 |
|---|---|
| `new BigDecimal("1").divide(new BigDecimal("3"))` | 예외 — `Non-terminating decimal expansion; no exact representable decimal result.` |
| `new BigDecimal("1").divide(BigDecimal.ZERO)` | 예외 — `Division by zero` |
| `BigDecimal.ZERO.divide(BigDecimal.ZERO)` | 예외 — `Division undefined` |
| `new BigDecimal("1.5").setScale(0)` | 예외 — `Rounding necessary` |
| `new BigDecimal("10").divide(new BigDecimal("4"))` | **`2.5`** (딱 떨어진다) |

**메시지가 갈리는 이유**

```text
  1 / 3      값은 있는데 유한한 10진수로 못 적는다  -> Non-terminating decimal expansion
  1 / 0      수학적으로 정의되지 않는다            -> Division by zero
  0 / 0      "부정" — 어떤 값도 답이 될 수 있다     -> Division undefined
  1.5 -> 0자리  값은 있는데 버릴지 올릴지 안 정했다  -> Rounding necessary
```

- **문제의 종류가 넷이고 메시지도 넷**이다. 로그만 보고 원인을 가를 수 있게 만든 설계다.
- 넷 다 `ArithmeticException`(unchecked)이라 **컴파일러가 강제하지 않는다.**

**정수 `0 / 0` 과의 차이**

| | 정수 | `BigDecimal` |
|---|---|---|
| `1 / 0` | `ArithmeticException: / by zero` | `ArithmeticException: Division by zero` |
| `0 / 0` | `ArithmeticException: / by zero` (같은 메시지) | `ArithmeticException: Division undefined` |

- **정수는 둘을 구분하지 않고 `BigDecimal` 은 구분한다.**
- 정수 쪽 출력은 [02번 주제](../02-numeric-operations/)에서 확인한 것이다.
- `double` 은 또 다르다 — `5.0/0 = Infinity`, `0.0/0.0 = NaN` 으로 **예외 없이 값을 준다.**\
  같은 "0으로 나누기"가 세 타입에서 세 가지로 갈린다.

**안전하게 쓰는 형태**

```java
a.divide(b, 2, RoundingMode.HALF_UP)   // 스케일과 모드를 내가 정한다 — 가장 예측 가능
a.divide(b, new MathContext(10))       // 유효숫자 개수로 정한다
a.divide(b, RoundingMode.HALF_UP)      // 왼쪽 값의 스케일을 쓴다 — 스케일이 결과를 바꾼다
```

실행으로 확인한 차이:

```text
1.divide(3, 5, HALF_UP)     = 0.33333
1.divide(3, MathContext(5)) = 0.33333
1.divide(3, DECIMAL32)      = 0.3333333
1.0.divide(3, HALF_UP)      = 0.3
1.000.divide(3, HALF_UP)    = 0.333
```

- 맨 아래 두 줄이 **왜 스케일이 값의 일부인지**를 보여 준다 — 같은 `1/3` 인데 결과가 다르다.
- 규칙: **인자 하나짜리 `divide` 는 쓰지 않는다.**

### 5. 반올림 모드

**출력** — `setScale(0, mode)` 를 여덟 값 × 일곱 모드로 돌린 표(출력 그대로).

```text
       값    HALF_UP  HALF_DOWN  HALF_EVEN         UP       DOWN    CEILING      FLOOR
     0.5          1          0          0          1          0          1          0
     1.5          2          1          2          2          1          2          1
     2.5          3          2          2          3          2          3          2
    -0.5         -1          0          0         -1          0          0         -1
    -1.5         -2         -1         -2         -2         -1         -1         -2
    -2.5         -3         -2         -2         -3         -2         -2         -3
     1.4          1          1          1          2          1          2          1
     1.6          2          2          2          2          1          2          1
```

**`0.5`·`1.5`·`2.5` 의 `HALF_UP` 과 `HALF_EVEN`**

| 값 | `HALF_UP` | `HALF_EVEN` |
|---|---|---|
| 0.5 | **1** | **0** |
| 1.5 | **2** | **2** |
| 2.5 | **3** | **2** |

- `HALF_UP` 은 **언제나 올린다**(절댓값 기준).
- `HALF_EVEN` 은 **짝수 쪽으로** 간다 — 0.5는 0(짝수), 1.5는 2(짝수), 2.5도 2(짝수).

**`-0.5` 의 `HALF_UP` 과 `CEILING`**

- `HALF_UP` -> **-1** (절댓값이 커지는 쪽)
- `CEILING` -> **0** (수직선에서 큰 쪽)
- **여기가 두 모드를 가르는 지점이다.** 양수 `0.5` 에서는 둘 다 `1` 이라 구분이 안 된다.
- 그래서 **반올림 테스트에는 음수를 반드시 넣는다.**

**`HALF_EVEN` 을 회계에서 쓰는 이유**

실행 결과 — 네 값을 각각 반올림해 합쳐 본 것이다(JDK 21.0.5, 17·25 동일, 출력 그대로).

```text
     값    HALF_UP  HALF_EVEN
   0.5          1          0
   1.5          2          2
   2.5          3          2
   3.5          4          4
원래 합      = 8.0
HALF_UP 합   = 10
HALF_EVEN 합 = 8
```

- `HALF_UP` 은 0.5를 **언제나 한쪽으로** 보내므로 **누적하면 편향**이 생긴다 — 합이 2만큼 커졌다.
- `HALF_EVEN` 은 위아래로 번갈아 보내 **상쇄**된다 — 합이 원래와 같다.\
  그래서 은행가 반올림(banker's rounding)이라 부른다.
- 다만 **한국의 금액 처리는 `HALF_UP` 을 쓰는 경우가 많다** — 도메인·법령이 정하는 문제이고,
  이 문서가 정할 수 있는 것이 아니다. 중요한 것은 **아무 모드나 고르지 않는 것**이다.

**`Math.round(-0.5)` 와 그 모드**

```text
Math.round(0.5)  = 1   Math.round(-0.5) = 0
Math.round(1.5)  = 2   Math.round(2.5)  = 3
```

- **`0` 이다.** `-1` 이 아니다.
- javadoc의 정의는 "Returns the closest `long` to the argument, **with ties rounding to positive infinity**"다.\
  0.5로 끝나면 **언제나 양의 무한대 쪽**이다.
- 이것은 **`RoundingMode` 에 없는 모드**다 — 굳이 이름을 붙이면 `HALF_CEILING` 이고, enum에 그런 상수는 없다.
- 함의: **`Math.round` 로 금액을 반올림하면 환불·차감 같은 음수에서 규칙이 달라진다.**\
  같은 금액을 더할 때와 뺄 때 다르게 처리되어 1원 차이가 쌓인다.

### 6. 연산이 스케일을 어떻게 정하는가

**출력** (출력 그대로)

```text
1.0 + 2.00             toString=3.00       unscaledValue=300    scale=2
1.0 - 2.00             toString=-1.00      unscaledValue=-100   scale=2
1.5 * 2.00             toString=3.000      unscaledValue=3000   scale=3
10 / 2 (divide)        toString=5          unscaledValue=5      scale=0
1.00 / 2 (divide)      toString=0.50       unscaledValue=50     scale=2
2.50.stripTrailingZeros toString=2.5        unscaledValue=25     scale=1
100.stripTrailingZeros toString=1E+2       unscaledValue=1      scale=-2
  100.stripTrailingZeros().toPlainString() = 100
1.0.negate()           toString=-1.0       unscaledValue=-10    scale=1
```

**다섯 식의 값과 스케일**

| 식 | 값 | 스케일 |
|---|---|---|
| `1.0.add(2.00)` | **3.00** | 2 (큰 쪽) |
| `1.5.multiply(2.00)` | **3.000** | 3 (1 + 2) |
| `"2.50".stripTrailingZeros()` | **2.5** | 1 |
| `"100".stripTrailingZeros()` | **1E+2** | **-2** |
| `"100".stripTrailingZeros().toPlainString()` | **"100"** | (문자열) |

**`multiply` 의 스케일 규칙과 그 위험**

```text
  1.5 (scale 1)  x  2.00 (scale 2)  =  3.000 (scale 3)

  세율 곱하기를 이어 가면

  10000 (0) x 0.1 (1) = 1000.0 (1)
           x 0.1 (1) = 100.00 (2)
           x 0.1 (1) = 10.000 (3)
                            ^ 스케일이 계속 커진다
```

- **스케일은 두 스케일의 합**이다.
- 곱셈을 이어 가면 스케일이 **선형으로 증가**하고, 자릿수가 늘어 계산이 느려지고 출력이 지저분해진다.
- `new BigDecimal(0.1)` 처럼 스케일 55짜리를 곱하면 한 번에 폭발한다.\
  실행으로 확인: `new BigDecimal(0.1).multiply(new BigDecimal(3)) = 0.3000000000000000166533453693773481063544750213623046875`.
- 방어: **곱한 직후 `setScale(n, mode)` 로 정리**한다. 언제 정리할지가 도메인 결정이다.

**네 번째 줄이 `100` 이 아닌 이유**

```text
  "100"                     unscaled 100, scale 0
      |  stripTrailingZeros()
      v
  뒤쪽 0 두 개를 없애면      unscaled 1,   scale -2
                                            ^^^ 음수 스케일

  값 = 1 x 10^(-(-2)) = 1 x 10^2 = 100      값은 그대로다
  toString() 은 음수 스케일을 지수 표기로 쓴다 -> "1E+2"
```

- **스케일이 음수가 될 수 있다.** `stripTrailingZeros` 는 소수점 아래만이 아니라 **정수부의 0도 떼어 낸다.**
- 값은 바뀌지 않았다 — `toString()` 의 표현만 바뀌었다.

**로그에 그대로 찍으면**

- `"1E+2"` 라는 글자가 로그·CSV·JSON에 나간다.
- 받는 쪽이 `Integer.parseInt("1E+2")` 하면 **`NumberFormatException`**,\
  문자열로 비교하면 `"100"` 과 **다른 값**이 된다.
- 금액 비교·정산 대사에서 이런 표기 차이가 **없는 차이를 만들어 낸다.**
- 출력에는 **`toPlainString()`** 을 쓴다(실행으로 확인: `100`).
- 더 일반적으로: **`BigDecimal` 을 문자열로 내보내는 모든 경계에서 표기를 정해 둔다.**

### 7. `0` 인지 판정하기

**출력**

```text
BigDecimal.ZERO.equals(new BigDecimal("0.0")) = false
BigDecimal.ZERO.compareTo(new BigDecimal("0.0")) = 0
signum() 으로 0 판정: new BigDecimal("0.00").signum() = 0
```

**`BigDecimal.ZERO.equals(new BigDecimal("0.0"))`**

- **`false`.** `ZERO` 는 스케일 0이고 `"0.0"` 은 스케일 1이다.
- 즉 **`equals(BigDecimal.ZERO)` 로 0을 판정하면 `0.0`·`0.00` 을 전부 놓친다.**
- DB의 `DECIMAL(10,2)` 컬럼에서 읽은 0은 `0.00` 이므로 **실무에서 거의 항상 놓친다.**

**두 가지 방법**

1. **`x.compareTo(BigDecimal.ZERO) == 0`**
2. **`x.signum() == 0`**

- 둘 다 스케일을 무시한다.
- `signum()` 쪽이 짧고 의도가 드러난다.

**`signum()` 의 범위**

- **`-1`, `0`, `1`** 셋이다.
- `compareTo` 와 같은 관례다(음수·0·양수).

**음수 판정에 무엇을 쓰겠는가**

- **`signum() < 0`** 을 쓴다.
- 이유: `compareTo(BigDecimal.ZERO) < 0` 은 **`BigDecimal.ZERO` 라는 피연산자가 한 번 더 등장**해
  읽는 사람이 "0의 스케일이 뭐였지"를 잠깐 생각하게 된다.
- `signum()` 은 그 생각 자체가 필요 없다 — **부호만 묻는 함수**다.
- 단 `x.compareTo(limit) < 0` 처럼 **0이 아닌 값과 비교**할 때는 `compareTo` 말고 방법이 없다.\
  `<`·`>` 연산자는 `BigDecimal` 에 쓸 수 없다(자바에 연산자 오버로딩이 없다).

### 8. 되돌아갈 때 무엇이 조용히 틀리는가

**출력**

```text
v.intValue()          = 1000
v.doubleValue()       = 1000.0
new BigDecimal("1.5").intValue()      = 1
new BigDecimal("1.5").intValueExact() -> java.lang.ArithmeticException: Rounding necessary
new BigDecimal("1e20").intValueExact() -> java.lang.ArithmeticException: Overflow
new BigDecimal("1e20").intValue()     = 1661992960
```

**`new BigDecimal("1.5").intValue()`**

- **`1`.** 소수부를 **조용히 버린다**(0 쪽 절단).
- `1.9` 였어도 `1` 이다. 반올림이 아니라 절단이다.

**`new BigDecimal("1e20").intValue()`**

- **`1661992960`.**
- `1e20` 은 `int` 범위(약 21억)를 훨씬 넘는데 **예외가 없다.**
- 넘치는 비트를 버리고 남은 하위 32비트를 부호 있는 정수로 읽은 값이다 —\
  [02번 주제](../02-numeric-operations/)의 정수 오버플로가 그대로 재현된다.
- **금액을 `int` 로 되돌리는 코드가 조용히 엉뚱한 값을 만든다.**

**`intValueExact()` 의 두 메시지**

| 입력 | 메시지 | 뜻 |
|---|---|---|
| `1.5` | `Rounding necessary` | 소수부가 있어 정수로 정확히 못 바꾼다 |
| `1e20` | `Overflow` | 값이 `int` 범위를 넘는다 |

- **두 실패 원인을 나눠서 알려 준다.** `intValue()` 는 둘 다 조용히 지나간다.

**02번의 어떤 메서드와 같은 철학인가**

- **`Math.toIntExact(long)`** 이다.
- 둘 다 "넓은 것을 좁은 것에 넣을 때 **손실이 생기면 던진다**"는 같은 원칙이다.
- 더 넓게는 `Math.addExact`·`multiplyExact` 와 같은 계열이다 —\
  **틀린 값이 조용히 흘러가는 대신 그 자리에서 멈춘다.**
- 규칙: **`BigDecimal` 에서 기본형으로 돌아갈 때는 `*ValueExact()` 를 쓴다.**\
  `intValue`·`longValue`·`doubleValue` 는 전부 조용한 손실의 통로다.

### 9. 계약인가 구현인가

**`equals` 가 스케일을 본다는 사실은 어디에**

- **javadoc** 이다. JLS가 아니다 — `BigDecimal` 은 언어가 아니라 라이브러리다.

> Unlike `compareTo(BigDecimal)`, this method considers two `BigDecimal` objects equal only if they
> are equal in value and scale. Therefore 2.0 is not equal to 2.00 when compared by this method since
> the former has [`BigInteger`, `scale`] components equal to [20, 1] while the latter has components
> equal to [200, 2].

- **계약이므로 버전이 올라도 안 바뀐다.** 바꾸면 호환성 파기다.
- 실제로 17·21·25에서 이 문서의 모든 출력이 동일했다.

**"natural ordering that is inconsistent with equals"라고 적은 이유**

> Note: this class has a natural ordering that is inconsistent with equals.

- `Comparable` javadoc이 **"그런 클래스는 그 사실을 문서에 밝히라"** 고 요구하기 때문이다.
- 왜 필요하냐면, **정렬 기반 컬렉션(`TreeSet`·`TreeMap`)이 `equals` 대신 `compareTo` 를 쓰기** 때문이다.\
  2번에서 본 `HashSet` size 3 / `TreeSet` size 1 이 바로 그 결과다.
- 즉 이 한 줄이 **"컬렉션마다 결과가 다를 것"이라는 경고**다.

**javadoc이 보여 주는 대체 불가능성의 예**

> One example that shows how 2.0 and 2.00 are *not* substitutable for each other under some arithmetic
> operations are the two expressions: `new BigDecimal("2.0" ).divide(BigDecimal.valueOf(3), HALF_UP)`
> which evaluates to 0.7 and `new BigDecimal("2.00").divide(BigDecimal.valueOf(3), HALF_UP)`
> which evaluates to 0.67.

- **같은 나눗셈인데 결과가 0.7과 0.67로 다르다.**
- 스케일이 결과에 **실제로 영향을 주므로**, 스케일이 다른 두 값을 "같다"고 하면 거짓말이 된다.
- 그래서 `equals` 가 엄격한 것은 **일관된 설계**이지 실수가 아니다.
- 같은 성질을 다른 값으로 확인했다: `1.0.divide(3, HALF_UP) = 0.3`, `1.000.divide(3, HALF_UP) = 0.333`.

**`311`·`3102` 를 코드가 의존해도 되는가**

- **안 된다.**
- 계약은 "`equals` 가 참이면 해시가 같다"까지이고, **구체적인 숫자는 구현**이다.
- 실제로 `hashCode` 구현은 값이 `long` 에 들어가는지(`intCompact`)에 따라 **다른 경로**를 탄다.

```java
// JDK 21.0.5  java.base/java/math/BigDecimal.java  equals() 안 — 실제 소스 그대로
long s = this.intCompact;
long xs = xDec.intCompact;
if (s != INFLATED) {
    if (xs == INFLATED)
        xs = compactValFor(xDec.intVal);
    return xs == s;
} else if (xs != INFLATED)
    return xs == compactValFor(this.intVal);
return this.inflated().equals(xDec.inflated());
```

- `long` 에 담을 수 있으면 압축해 두고, 넘치면 `BigInteger` 로 "부풀린다"(inflate).
- **성능 최적화이고 관측 가능한 결과는 같다** — 어느 경로든 `equals` 의 답은 동일하다.

**예외 메시지를 테스트에서 단언해도 되는가**

- **안 된다.**
- 이 문서는 메시지 여섯 가지를 그대로 실었지만, 그것은 **학습용 근거**이지 테스트 기준이 아니다.
- 전례가 있다 — [35번 주제](../35-string/)에서 `substring` 의 예외 메시지가 **17→21에 실제로 바뀌었다.**
- `BigDecimal` 쪽은 세 JDK에서 안 바뀌었지만, **안 바뀐 것과 보장된 것은 다르다.**
- 단언할 것은 **예외 클래스**(`ArithmeticException`)와, 필요하면 던져졌다는 사실 자체다.

### 10. 다른 주제와 잇기

**`0.1` 을 열 번 더하면**

```text
double      : 0.9999999999999999   == 1.0 ? false
BigDecimal  : 1.0   scale=1   equals(ONE)? false   compareTo(ONE)==0? true
```

- `double` -> **0.9999999999999999** (1.0이 아니다)
- `BigDecimal` -> **1.0** (정확하다)

**그 결과가 `BigDecimal.ONE` 과 `equals` 인가**

- **아니다. `false` 다.**
- 누적 결과의 스케일이 **1**(`"0.1"` 을 더했으므로)이고 `BigDecimal.ONE` 의 스케일은 **0**이다.
- `compareTo(ONE) == 0` 은 **`true`** 다.
- 이 한 줄이 이 주제 전체를 요약한다 — **정확하게 계산하는 것과 정확하게 비교하는 것은 다른 문제다.**\
  `BigDecimal` 로 바꿔서 계산은 고쳤는데 `equals` 를 그대로 쓰면 **버그가 비교 쪽으로 이사했을 뿐**이다.

**오버플로가 없는 대신 치르는 것**

```text
Long.MAX_VALUE       = 9223372036854775807
그 값 + 1 (long)     = -9223372036854775808
그 값 + 1 (BigDecimal)= 9223372036854775808
그 값 * 그 값         = 85070591730234615847396907784232501249
```

- **임의 정밀도**라 오버플로 자체가 없다 — [02번](../02-numeric-operations/)의 `Math.addExact` 가 필요 없다.
- 대신 치르는 것:
  1. **메모리와 시간이 자릿수에 비례**한다. `long` 산술의 몇십 배다. *(배수는 안 재 봤다.)*
  2. **객체다.** 연산마다 새 객체가 생긴다(불변이므로).
  3. **`+`·`<` 연산자를 못 쓴다.** `add`·`compareTo` 를 써야 해 식이 길어진다.
- 그래서 **소수가 없는 금액은 `long` 원 단위**가 여전히 좋은 선택이다 — 단 오버플로를 스스로 막아야 한다.

**10000원을 3명이 나눌 때 `BigDecimal` 이 안 정해 주는 것**

```text
1인당(버림)   = 3333   3명 합 = 9999   남는 돈 = 1
1인당(반올림) = 3333   3명 합 = 9999   차액 = 1
```

- **남는 1원을 누가 갖는가.**
- `BigDecimal` 은 "1원이 남는다"는 사실만 정확히 알려 준다. **분배 정책은 도메인이 정한다.**
- 흔한 정책 셋: 첫 사람이 더 낸다 · 마지막 사람이 덜 낸다 · 주최자가 흡수한다.
- 이것이 **"한 줄 요구사항에 안 들어 있는 결정"** 의 전형이다 —\
  명시하지 않으면 구현자가 아무거나 고르고, 나중에 정산이 안 맞는다.
- 반올림을 써도 안 사라진다는 점에 주목한다 — `3333 × 3 = 9999` 로 똑같다.

**`0.1000000000000000055511...` 의 유래**

- **[`../../../../data-representation/`](../../../../data-representation/)** 가 정본이다.
- 그쪽은 「0.1이 왜 2진 부동소수로 정확히 표현되지 않나」(IEEE 754의 가수·지수 구조)까지 다룬다.
- 이 문서는 **그 값을 출력해 보고 그래서 코드에서 무엇을 쓰는지**만 다룬다.
- 중간 고리는 [02번 주제](../02-numeric-operations/)다 — `0.1 + 0.2 != 0.3` 이라는 관측.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex`(53-double) | `new BigDecimal(0.1)` 의 실제 값·스케일·정밀도, `valueOf` 와의 차이, `2.0`·`0.5`·`1.1` | 17 · 21 · 25 (동일) |
| `Ex`(53-scale) | `unscaledValue`/`scale`, `equals` 대 `compareTo`, 해시, `HashSet`/`TreeSet`/`HashMap`, 연산별 스케일, `stripTrailingZeros`, `signum` | 17 · 21 · 25 (동일) |
| `Ex`(53-divide) | 예외 6종 메시지, `divide` 4형태, **반올림 모드 7종 × 값 8종 표**, `Math.round` 대비, `1.005` 반올림 | 17 · 21 · 25 (동일) |
| `Ex`(53-money) | 0.1 열 번 더하기, 3인 분할, 부가세, `assertEquals` 함정, 오버플로 없음, `intValue`/`intValueExact` | 17 · 21 · 25 (동일) |
| `Ex`(53-bias) | `HALF_UP` 과 `HALF_EVEN` 의 누적 편향 (0.5·1.5·2.5·3.5 합계) | 17 · 21 · 25 (동일) |
| `src.zip` 열람 | `equals`·`hashCode` 구현, `compareTo`·`equals`·`BigDecimal(double)` javadoc, `Math.round` javadoc | 21 |

**구현에 의존하는 항목**

| 항목 | 무엇에 의존하나 |
|---|---|
| `hashCode()` 의 구체적인 값(311·3102) | `BigDecimal.hashCode` 구현 — 계약이 아니다 |
| 예외 **메시지 문구** | JDK 구현. 35번에서 바뀐 전례가 있다 |
| `intCompact` / `BigInteger` 이중 표현 | 내부 최적화 — 관측 가능한 결과는 같다 |
| `TreeSet` 에 남는 표현(`1.0`) | **입력 순서**에 달려 있다 |
| `divide` 의 성능 | 자릿수에 비례 |

**계약이라 바뀌지 않을 것**

- `equals` 가 값과 스케일을 본다.
- `compareTo` 가 값만 본다(natural ordering inconsistent with equals).
- `divide` 가 정확한 결과를 못 내면 `ArithmeticException` 을 던진다.
- 각 `RoundingMode` 의 결과.
- `BigDecimal` 이 불변이다.

**버전이 오르면 다시 돌려야 할 것**

- 예외 메시지 문구(문서에 실었으므로).
- 새 메서드·새 `RoundingMode`.
- 나머지는 계약이라 바뀌면 그것이 호환성 파기다.

## 안 돌려 본 것

- `DecimalFormat`·`NumberFormat` 으로 표시 형식 맞추기 — `toPlainString()` 까지만 돌렸다.
- `MathContext.UNLIMITED` 와 `precision` 이 0일 때의 동작.
- `BigDecimal` 연산이 `long` 산술보다 **몇 배** 느린지 — 측정하지 않았다.
- `BigInteger` 쪽 API(`BigDecimal.toBigInteger`·`toBigIntegerExact`).
- 더 큰 표본(수천 개 값)에서 `HALF_EVEN` 의 편향이 실제로 0에 수렴하는지 — 네 값으로만 확인했다.
- `String.join`·직렬화 등에서 `BigDecimal` 표기가 어떻게 나가는지.
