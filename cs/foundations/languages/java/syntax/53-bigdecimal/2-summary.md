# java/syntax/53 — `BigDecimal`: 스케일·반올림·`equals` vs `compareTo` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Java SE 21 `BigDecimal` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html) · [`RoundingMode`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/RoundingMode.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/math/BigDecimal.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 5개를 **17.0.13 · 21.0.5 · 25.0.1** 에서 모두 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> 예외 메시지 여섯 가지는 **실제로 던져 보고** 그대로 옮겼다.
> **버전** — `BigDecimal` 은 Java 1.1, `RoundingMode` enum 과 `divide(BigDecimal, RoundingMode)` 는 **5**부터.
> 이 문서에서 버전에 갈리는 동작은 **찾지 못했다**(세 JDK 출력 동일).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> 선행: [02 수치 연산](../02-numeric-operations/).

## 한눈에 — 쉽게 말하면

**`BigDecimal` 은 숫자가 아니라 「측정 기록」이다** — 잰 값과 **어느 눈금까지 쟀는지**를 함께 들고 다닌다.\
그래서 `1.0` 과 `1.00` 은 **같은 길이인데 다른 기록**이다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 측정 기록 카드 | `BigDecimal` 객체 하나 |
| 눈금 없이 적은 정수 | `unscaledValue()` — 소수점을 없앤 정수 |
| 소수점 아래 몇 칸까지 쟀나 | `scale()` — **값의 일부다** |
| 카드 두 장이 글자까지 똑같은가 | `equals` — **스케일까지 본다** |
| 잰 길이 자체가 같은가 | `compareTo(...) == 0` — 스케일을 **안 본다** |
| 더 촘촘한 자로 다시 적기 | `setScale(n, 반올림모드)` |
| 아무리 촘촘한 자로도 딱 안 떨어지는 측정 | `1/3` 같은 무한소수 — **반올림을 지정하지 않으면 예외** |

- `1.0` 은 `[unscaled 10, scale 1]`, `1.00` 은 `[unscaled 100, scale 2]` 다.\
  **카드에 적힌 글자가 다르므로** `equals` 가 `false` 다.
- 반면 길이는 같으므로 `compareTo` 는 `0` 이다.
- 이 하나의 차이가 **`HashSet` 과 `TreeSet` 의 크기를 다르게 만든다.**

```text
new BigDecimal("1") · new BigDecimal("1.0") · new BigDecimal("1.00") 셋을 담으면

  HashSet (equals · hashCode 로 판정)        TreeSet (compareTo 로 판정)
  +---------------------------------+      +---------------------------------+
  | [1.0, 1.00, 1]                  |      | [1.0]                           |
  | size = 3                        |      | size = 1                        |
  |                                 |      |                                 |
  | contains(new BigDecimal("1.000"))|      | contains(new BigDecimal("1.000"))|
  |   -> false                      |      |   -> true                       |
  +---------------------------------+      +---------------------------------+
        셋 다 다른 값으로 센다                    셋 다 같은 값으로 센다
```

위 출력은 **실제로 돌린 결과 그대로**다.

실무에서 이게 터지는 자리는 **금액 비교와 테스트의 `assertEquals`** 다.\
DB에서 `DECIMAL(10,2)` 로 읽으면 `1000.00` 이고 코드가 만든 값은 `1000` 이라,\
값이 같은데 **테스트가 실패**하고, `Map` 조회는 **조용히 `null`** 을 돌려준다.

> **스케일(scale)** — 소수점 아래 자릿수. `BigDecimal` 에서는 **값의 일부**이지 표시 형식이 아니다.\
> 예: `1.0` 의 스케일은 1, `1.00` 의 스케일은 2다. 둘은 서로 다른 객체이고 `equals` 가 거짓이다.

> **unscaled value** — 소수점을 없앤 정수부. `값 = unscaled × 10^(-scale)`.\
> 예: `1.00` 의 unscaled 는 `100`, 스케일은 `2`. `100 × 10^-2 = 1`.

> **`compareTo` 가 `equals` 와 일치하지 않는다(inconsistent with equals)** — 두 객체가 `compareTo` 로는 같은데 `equals` 로는 다른 것.\
> 예: `1.0` 과 `1.00` 이 그렇다. 정렬 기반 컬렉션과 해시 기반 컬렉션이 다르게 동작한다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `BigDecimal` 에서 **"같다"가 두 가지**인 이유는 무엇이고, 어느 쪽을 언제 쓰는가.
2. `double` 로 `BigDecimal` 을 만들면 **정확히 무엇이 들어가는가.**
3. 나눗셈은 왜 **가끔 예외를 던지는가** — 그리고 무엇을 지정해야 안 던지는가.

## 동작 방식

### (1) 스케일은 값의 일부다

**언제 쓰나** — `BigDecimal` 두 개를 비교하거나 `Map`·`Set` 에 넣는 모든 자리.

```text
  new BigDecimal("1.00")

  +------------------------+
  | unscaledValue = 100    |   <- 소수점을 없앤 정수
  | scale         = 2      |   <- 소수점 아래 두 칸
  +------------------------+
          값 = 100 x 10^-2 = 1
```

실행 결과 (JDK 21.0.5 — 17·25 동일):

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

그림 해설 (한 단계씩):

- 같은 값 `1` 을 세 가지 **다른 객체**로 표현할 수 있다.
- `equals` 가 `false` 인 이유는 구현이 **스케일을 먼저 비교**하기 때문이다.

```java
// JDK 21.0.5  java.base/java/math/BigDecimal.java  3226~3243행 — 실제 소스 그대로
public boolean equals(Object x) {
    if (!(x instanceof BigDecimal xDec))
        return false;
    if (x == this)
        return true;
    if (scale != xDec.scale)
        return false;
    ...
}
```

- `hashCode` 에도 스케일이 들어간다 — `311` 과 `3102` 가 다른 이유다.

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

- 두 반환문 모두 마지막이 **`+ scale`** 이다. 그래서 스케일이 다르면 해시도 다르다.
- 즉 `equals`/`hashCode` 계약은 **지켜져 있다** — 깨진 것이 아니라 **"같다"의 정의가 엄격한 것**이다.

비용 — 비교 자체는 O(자릿수). 함정은 비용이 아니라 **의미**다.

### (2) `equals` 와 `compareTo` — 자바 자신이 "불일치"라고 적어 두었다

**언제 쓰나** — 금액이 같은지 판정할 때. 거의 항상 `compareTo` 가 맞다.

```text
  a = 1.0        b = 1.00

  a.equals(b)        -> false     "카드가 다르다"
  a.compareTo(b)     -> 0         "길이는 같다"
  a.hashCode()       -> 311
  b.hashCode()       -> 3102
```

JDK 21 소스의 javadoc이 직접 말한다(원문 인용).

> Note: this class has a natural ordering that is inconsistent with equals.

그리고 `equals` 쪽에는 그 이유를 예로 적어 두었다.

> Unlike `compareTo(BigDecimal)`, this method considers two `BigDecimal` objects equal only if they
> are equal in value and scale. Therefore 2.0 is not equal to 2.00 when compared by this method since
> the former has [`BigInteger`, `scale`] components equal to [20, 1] while the latter has components
> equal to [200, 2].

같은 javadoc이 **왜 그렇게 설계했는지**까지 적는다.

> One example that shows how 2.0 and 2.00 are *not* substitutable for each other under some arithmetic
> operations are the two expressions: `new BigDecimal("2.0" ).divide(BigDecimal.valueOf(3), HALF_UP)`
> which evaluates to 0.7 and `new BigDecimal("2.00").divide(BigDecimal.valueOf(3), HALF_UP)`
> which evaluates to 0.67.

실행으로 같은 성질을 확인한 것이다:

```text
1.0.divide(3, HALF_UP)      = 0.3
1.000.divide(3, HALF_UP)    = 0.333
```

그림 해설 (한 단계씩):

- **스케일이 결과를 바꾸므로** 스케일이 다른 두 값은 진짜로 "대체 가능"하지 않다.
- 그래서 `equals` 가 스케일을 보는 것은 **일관된 설계**다.
- 대신 사람이 원하는 "금액이 같은가"는 `compareTo(...) == 0` 이다.

비용 — 없다. **판단 규칙**이다.

### (3) `double` 로 만들면 안 되는 이유

**언제 쓰나** — `new BigDecimal(...)` 을 쓸 때마다. 생성자가 `double` 을 받는다는 사실 자체가 함정이다.

```text
  double 0.1 이 실제로 담고 있는 값               "0.1" 이라는 글자

  0.1000000000000000055511151231257827...      0.1
           |                                     |
           v                                     v
  new BigDecimal(0.1)                    new BigDecimal("0.1")
  그 실제 값을 "정확히" 옮긴다             글자 그대로 옮긴다
```

실행 결과 (JDK 21.0.5 — 17·25 동일, 출력 그대로):

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
```

그림 해설 (한 단계씩):

- **생성자가 틀린 게 아니다.** `double` 0.1이 진짜로 저 값이고, 생성자는 그것을 **정확히** 옮긴다.
- `2.0`·`0.5` 는 2의 거듭제곱으로 떨어지므로 **깔끔하게** 나온다 — 그래서 테스트에서 안 걸린다.
- 스케일이 **55**가 된다. 이 값으로 계산을 이어 가면 자릿수가 눈덩이처럼 불어난다.
- `BigDecimal.valueOf(0.1)` 은 다르다 — **`Double.toString(0.1)` 을 거쳐** `"0.1"` 로 만든다.

javadoc이 이것을 그대로 경고한다(JDK 21 소스 원문).

> The results of this constructor can be somewhat unpredictable. One might assume that writing
> `new BigDecimal(0.1)` in Java creates a `BigDecimal` which is exactly equal to 0.1 (an unscaled value
> of 1, with a scale of 1), but it is actually equal to
> 0.1000000000000000055511151231257827021181583404541015625. ...
> Therefore, it is generally recommended that the String constructor be used in preference to this one.

- javadoc이 적은 숫자와 **실행 출력이 한 글자도 다르지 않다.**

비용 — `new BigDecimal(double)` 은 자릿수가 폭발해 이후 모든 연산이 느려지고, 결과가 지저분해진다.

### (4) 나눗셈 — 반올림을 지정하지 않으면 던진다

**언제 쓰나** — `divide` 를 쓰는 모든 자리. 인자가 하나뿐인 `divide` 는 **위험하다.**

```text
  10 / 4 = 2.5          딱 떨어진다     -> divide(4) 가 2.5 를 돌려준다
   1 / 3 = 0.333...     안 떨어진다     -> divide(3) 이 예외를 던진다

  "정확한 값을 돌려줄 수 없으면 만들어 내지 않고 멈춘다"가 계약이다
```

실행 결과 — **던져 본 것 그대로다**(JDK 21.0.5 — 17·25 동일).

```text
1.divide(3)                 -> java.lang.ArithmeticException: Non-terminating decimal expansion; no exact representable decimal result.
1.divide(0)                 -> java.lang.ArithmeticException: Division by zero
0.divide(0)                 -> java.lang.ArithmeticException: Division undefined
1.5.setScale(0)             -> java.lang.ArithmeticException: Rounding necessary
1.5.setScale(0,UNNECESSARY) -> java.lang.ArithmeticException: Rounding necessary
1.divide(3,UNNECESSARY)     -> java.lang.ArithmeticException: Rounding necessary
```

그림 해설 (한 단계씩):

- **메시지가 네 가지로 갈린다** — 무엇이 문제인지 메시지가 말해 준다.\
  `Non-terminating decimal expansion` = 무한소수 · `Division by zero` = 0으로 나눔 ·
  `Division undefined` = `0/0` · `Rounding necessary` = 반올림이 필요한데 안 정했음.
- **`0/0` 만 메시지가 다르다** — 정수 `0/0` 이 `/ by zero` 인 것과 대비된다([02번](../02-numeric-operations/)).
- `setScale(0)`(모드 없는 판)은 **`UNNECESSARY` 와 같은 뜻**이다 — 둘 다 같은 메시지를 낸다.
- 이 예외들은 전부 `ArithmeticException`(unchecked)이라 **안 잡아도 컴파일된다.**

반올림을 주면 답이 나온다(실행 출력 그대로).

```text
1.divide(3, 5, HALF_UP)     = 0.33333
1.divide(3, MathContext(5)) = 0.33333
1.divide(3, DECIMAL32)      = 0.3333333
1.0.divide(3, HALF_UP)      = 0.3
1.000.divide(3, HALF_UP)    = 0.333
10.divide(4)                = 2.5
```

- `divide(divisor, scale, mode)` — **스케일을 내가 정한다.** 가장 예측 가능하다.
- `divide(divisor, mathContext)` — **유효숫자 개수**를 정한다. 스케일이 아니다.
- `divide(divisor, mode)` — **왼쪽 값의 스케일을 그대로 쓴다.**\
  그래서 `1.0` 이면 0.3, `1.000` 이면 0.333 이 된다 — 위 javadoc이 말한 그 성질이다.

비용 — 임의 정밀도 연산이라 `long` 산술보다 훨씬 비싸다. 다만 **금액 계산에서 그 비용은 문제가 아니다.**

### (5) 반올림 모드 — `HALF_UP` 이 기본이 아니다

**언제 쓰나** — `setScale`·`divide` 에 모드를 고를 때.

실행 결과 — `setScale(0, mode)` 를 여덟 값 × 일곱 모드로 돌린 표다(출력 그대로).

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

그림 해설 (한 단계씩):

- **`HALF_UP`** — 0.5는 **절댓값이 커지는 쪽**. 사람이 학교에서 배운 반올림이다(`-0.5 -> -1`).
- **`HALF_EVEN`** — 0.5는 **짝수 쪽**. `0.5 -> 0`, `1.5 -> 2`, `2.5 -> 2`, `3.5 -> 4`.\
  여러 번 반올림해도 **한쪽으로 쏠리지 않는다**. 회계·통계에서 쓴다(은행가 반올림).\
  실행으로 확인: 네 값을 더하면 원래 합이 `8.0` 인데 `HALF_UP` 합은 `10`, `HALF_EVEN` 합은 `8` 이다.
- **`UP`/`DOWN`** — 절댓값 기준. `DOWN` 은 `int` 나눗셈의 절단과 같다.
- **`CEILING`/`FLOOR`** — 부호 기준. `FLOOR` 는 `Math.floorDiv` 와 같은 방향이다.
- 음수 세 행이 모드를 가르는 지점이다 — **양수만 테스트하면 `HALF_UP` 과 `UP` 이 구분되지 않는다.**

`Math.round` 와 비교하면 **또 다르다**(실행 출력 그대로).

```text
Math.round(0.5)  = 1   Math.round(-0.5) = 0
Math.round(1.5)  = 2   Math.round(2.5)  = 3
```

- javadoc이 정의를 한 줄로 적는다 — "Returns the closest `long` to the argument,
  **with ties rounding to positive infinity**"(JDK 21 `Math.java` 원문).\
  0.5로 끝나면 **언제나 큰 쪽(양의 무한대 방향)** 이라는 뜻이다. 그래서 `-0.5` 가 `-1` 이 아니라 **`0`** 이다.
- 즉 `Math.round` 는 `HALF_UP` 이 아니다. **`RoundingMode.HALF_UP` 은 절댓값 기준이고, `Math.round` 는 부호 기준**이다.\
  `RoundingMode` 로 옮기면 **`HALF_CEILING`** 에 해당하는데, 그런 모드는 enum 에 없다.
- 금액 반올림을 `Math.round` 로 하면 **음수(환불·차감)에서 규칙이 달라진다.**

비용 — 없다. **정책을 고르는 일**이고, 도메인이 답해야 한다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 만드는 세 가지 방법

```java
new BigDecimal("0.1")        // 문자열 — 언제나 이것을 쓴다
BigDecimal.valueOf(0.1)      // double -> Double.toString 경유
BigDecimal.valueOf(100L)     // long — 스케일 0
new BigDecimal(0.1)          // 쓰지 말 것
```

실행 결과:

```text
Double.toString(0.1)     = 0.1
valueOf(1.0)             = 1.0   scale=1
valueOf(100L)            = 100  scale=0
new BigDecimal(100)      = 100  scale=0
```

- `valueOf(1.0)` 의 스케일이 **1**이다 — `"1.0"` 이라는 글자를 거치기 때문이다.
- 상수는 `BigDecimal.ZERO`·`ONE`·`TEN` 을 쓴다. **전부 스케일 0**이다.

### 연산이 스케일을 어떻게 정하는가

실행 결과 (출력 그대로):

```text
1.0 + 2.00             toString=3.00       unscaledValue=300    scale=2
1.0 - 2.00             toString=-1.00      unscaledValue=-100   scale=2
1.5 * 2.00             toString=3.000      unscaledValue=3000   scale=3
10 / 2 (divide)        toString=5          unscaledValue=5      scale=0
1.00 / 2 (divide)      toString=0.50       unscaledValue=50     scale=2
2.50.stripTrailingZeros toString=2.5        unscaledValue=25     scale=1
100.stripTrailingZeros toString=1E+2       unscaledValue=1      scale=-2
1.0.negate()           toString=-1.0       unscaledValue=-10    scale=1
```

| 연산 | 결과 스케일 |
|---|---|
| `add` · `subtract` | 두 스케일 중 **큰 쪽** |
| `multiply` | 두 스케일의 **합** (1 + 2 = 3) |
| `divide`(정확히 떨어질 때) | 결과를 표현하는 **최소 스케일** |
| `negate` · `abs` | 그대로 |
| `stripTrailingZeros` | 뒤쪽 0을 없앤 만큼 줄어든다 — **음수가 될 수 있다** |

- `multiply` 의 스케일이 합이라 **곱셈을 이어 가면 스케일이 계속 커진다.**\
  금액 계산에서는 곱한 직후 `setScale` 로 정리한다.
- `100.stripTrailingZeros()` 가 **`1E+2`**(스케일 -2)가 되는 것이 함정이다.\
  `toString()` 이 지수 표기를 쓰므로 화면·로그·DB에 `1E+2` 가 찍힌다.\
  평범하게 보이려면 **`toPlainString()`** 을 쓴다(실행으로 확인: `100`).

### `0` 을 판정하는 법

```text
BigDecimal.ZERO.equals(new BigDecimal("0.0")) = false
BigDecimal.ZERO.compareTo(new BigDecimal("0.0")) = 0
new BigDecimal("0.00").signum() = 0
```

- **`equals(BigDecimal.ZERO)` 는 쓰면 안 된다** — `0.0`·`0.00` 을 놓친다.
- `compareTo(BigDecimal.ZERO) == 0` 또는 **`signum() == 0`** 을 쓴다.
- `signum()` 은 `-1`·`0`·`1` 을 돌려주므로 부호 판정에도 쓴다.

### 되돌아갈 때

```text
v.intValue()          = 1000
v.doubleValue()       = 1000.0
new BigDecimal("1.5").intValue()      = 1
new BigDecimal("1.5").intValueExact() -> java.lang.ArithmeticException: Rounding necessary
new BigDecimal("1e20").intValueExact() -> java.lang.ArithmeticException: Overflow
new BigDecimal("1e20").intValue()     = 1661992960
```

- **`intValue()` 는 조용히 자르고 조용히 넘친다** — `1e20` 이 `1661992960` 이 된다.\
  [02번 주제](../02-numeric-operations/)의 정수 오버플로가 그대로 돌아온다.
- **`intValueExact()`** 는 두 경우를 나눠 던진다 — `Rounding necessary`(소수부가 있음) / `Overflow`(범위 초과).
- 그래서 변환에는 항상 `*Exact` 계열을 쓴다. `Math.addExact` 와 같은 철학이다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다.

### 1. `equals` 로 금액을 비교한다

```text
왼쪽 — 코드가 만든 값끼리                 오른쪽 — DB에서 읽은 값과 비교
+---------------------------------+      +---------------------------------+
| new BigDecimal("1000")          |      | DB DECIMAL(10,2) -> 1000.00     |
|   .equals(new BigDecimal("1000"))|      | code            -> 1000        |
|                                 |      |                                 |
| -> true                         |      | equals    -> false              |
| 테스트 초록                      |      | compareTo -> 0                  |
+---------------------------------+      +---------------------------------+
```

- **`assertEquals(new BigDecimal("1000"), actual)` 이 실패한다.** 값은 맞는데 스케일이 다르다.
- 실행으로 확인: `expected.equals(actual) = false`, `expected.compareTo(actual) = 0`.
- 고치는 법 둘: `assertThat(actual).isEqualByComparingTo("1000")` 또는 `expected.setScale(2)`.\
  실행으로 확인: `expected.setScale(2).equals(actual) = true`.
- 어느 쪽이든 **"스케일까지 맞출 것인가"를 의식적으로 정한 것**이어야 한다.

### 2. `HashMap` 키로 `BigDecimal` 을 쓴다

```text
m.get(new BigDecimal("10.00")) = 만원권
m.get(new BigDecimal("10.0"))  = null
m.get(new BigDecimal("10"))    = null
```

- **예외가 없다. 조용히 `null` 이다.**
- `hashCode` 에 스케일이 들어가므로 **버킷 자체가 다르다** — `equals` 까지 가지도 못한다.
- 금액을 키로 쓰려면 **스케일을 정규화**(`setScale(2)`)하고 넣고 찾아야 한다.
- 아니면 `TreeMap` 을 쓴다 — `compareTo` 기준이라 `10`·`10.0`·`10.00` 이 같은 키가 된다.\
  단 그 순간 **`Map` 의 `equals` 계약과 어긋나는 동작**을 받아들이는 것이다.

### 3. `double` 로 만들고 반올림한다

```text
p = 1.005   p.setScale(2,HALF_UP) = 1.01
double 로 같은 것: Math.round(1.005*100)/100.0 = 1.0
  (1.005 의 double 실제 값 = 1.00499999999999989341858963598497211933135986328125)
```

- 같은 "1.005를 소수 둘째 자리로 반올림"인데 **답이 다르다.**
- `double` 쪽이 틀린 것이 아니다 — `double` 1.005가 **진짜로 1.00499...** 라서 내림이 맞다.
- 이것이 `double` 로 금액을 다루면 안 되는 이유의 결정판이다.\
  **버그가 아니라 입력이 이미 틀려 있다.**
- 그리고 `new BigDecimal(1.005)` 로 만들면 `BigDecimal` 을 써도 **같은 오차를 그대로 물려받는다.**

### 4. `divide` 에 반올림을 안 준다

```text
1.divide(3) -> java.lang.ArithmeticException: Non-terminating decimal expansion; no exact representable decimal result.
```

- **테스트 데이터가 전부 딱 떨어지면 안 보인다.** `10/4 = 2.5` 는 멀쩡히 돈다.
- 운영에서 나눗수가 3이나 7이 되는 순간 **런타임에 터진다.**
- 규칙: **인자 하나짜리 `divide` 는 쓰지 않는다.** 항상 스케일과 모드를 준다.
- 역설적으로 이 예외는 **좋은 설계**다 — 조용히 잘라서 돈이 새는 대신 멈춘다.

### 5. `stripTrailingZeros` 뒤에 `toString` 을 쓴다

```text
100.stripTrailingZeros toString=1E+2   unscaledValue=1   scale=-2
  100.stripTrailingZeros().toPlainString() = 100
```

- `"1E+2"` 가 로그·CSV·API 응답에 그대로 나간다.
- 받는 쪽이 문자열로 파싱하면 **깨지거나 다른 값이 된다.**
- 출력용으로는 **`toPlainString()`** 을, 표시 형식이 필요하면 `DecimalFormat`·`String.format` 을 쓴다.\
  *(`DecimalFormat` 은 안 돌려 봤다.)*
- 스케일이 **음수가 될 수 있다**는 사실 자체가 이 함정의 뿌리다.

## 구현 세부사항 대 언어 보장

이 주제는 **거의 전부가 API 계약**이다 — JLS가 아니라 javadoc이 정본이다.

```text
     API 계약(javadoc)이 정하는 것                구현이 고르는 것
  +----------------------------------+      +----------------------------------+
  | equals 는 값과 스케일을 본다      |      | 내부 표현 (long 압축 vs BigInteger)|
  | compareTo 는 값만 본다            |      | toString 의 지수 표기 경계는       |
  | hashCode 에 스케일이 들어간다     |      |  javadoc 이 정의한다 -> 계약이다   |
  | divide 는 정확한 결과가 없으면    |      | 예외 "메시지" 문구                |
  |  ArithmeticException 을 던진다    |      |                                  |
  | 각 RoundingMode 의 결과           |      |                                  |
  +----------------------------------+      +----------------------------------+
```

**계약** — 이 문서가 인용한 세 곳 전부 javadoc이다.

- `compareTo` — "Note: this class has a natural ordering that is inconsistent with equals."
- `equals` — "considers two `BigDecimal` objects equal only if they are equal in value and scale.
  Therefore 2.0 is not equal to 2.00"
- `BigDecimal(double)` — "The results of this constructor can be somewhat unpredictable. ...
  it is generally recommended that the String constructor be used in preference to this one."

이 셋은 **버전이 올라도 안 바뀐다.** 바뀌면 호환성 파기다.\
실제로 17·21·25에서 이 문서의 모든 출력이 동일했다.

**구현 세부**

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

- 값이 `long` 에 들어가면 `intCompact` 에 담고, 넘치면 `BigInteger`(`intVal`)로 "부풀린다"(inflate).
- **성능 최적화이고 관측 가능한 동작을 안 바꾼다** — `equals` 의 결과는 어느 경로든 같다.
- 마찬가지로 `hashCode` 의 **구체적인 값**(311·3102)은 구현이다.\
  계약은 "같은 객체면 같은 해시"까지이고, **그 숫자를 코드가 의존하면 안 된다.**

**예외 메시지는 계약이 아니다.**

- 이 문서는 메시지 여섯 가지를 그대로 실었지만, **테스트에서 문구로 단언하면 안 된다.**
- [35번 주제](../35-string/)에서 `substring` 의 메시지가 17→21에 실제로 바뀐 전례가 있다.
- `BigDecimal` 쪽은 세 JDK에서 안 바뀌었지만, **안 바뀐 것과 보장된 것은 다르다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓰는 것 | 왜 |
|---|---|---|
| 금액·수량·세율 | `BigDecimal` (문자열 생성자) | 10진 소수를 정확히 표현한다 |
| 원 단위처럼 소수가 없는 금액 | `long` | 훨씬 싸다. 단 오버플로는 [02번](../02-numeric-operations/) |
| 과학 계산·그래픽·통계 | `double` | 정확성보다 속도·범위가 중요하다 |
| 값이 같은지 판정 | `compareTo(...) == 0` | `equals` 는 스케일까지 본다 |
| `0` 인지 판정 | `signum() == 0` | `equals(ZERO)` 는 `0.00` 을 놓친다 |
| 나눗셈 | `divide(d, scale, mode)` | 인자 하나짜리는 예외를 던질 수 있다 |
| 정렬·범위 조회 | `TreeMap`/`TreeSet` | `compareTo` 기준 |
| 해시 기반 조회 | **정규화 후** `HashMap` | 스케일이 다르면 못 찾는다 |
| 화면·로그 출력 | `toPlainString()` | `toString()` 은 지수 표기를 쓸 수 있다 |

판단 규칙 세 줄.

- **`BigDecimal` 에 `equals` 가 보이면 의심한다.** 스케일까지 같아야 하는 자리인지 확인한다.
- **`new BigDecimal(double)` 은 리뷰에서 무조건 지적한다.** 문자열이나 `valueOf` 로 바꾼다.
- **`divide` 는 인자 하나로 부르지 않는다.**

## 핵심 문장

- `BigDecimal` 의 **스케일은 값의 일부**다 — `1.0` 과 `1.00` 은 다른 객체이고 해시도 다르다.
- `equals` 는 **값과 스케일**을, `compareTo` 는 **값만** 본다. javadoc이 "inconsistent with equals"라고 직접 적어 두었다.
- `new BigDecimal(0.1)` 은 `0.1000000000000000055511151231257827021181583404541015625` 다 — 생성자가 틀린 게 아니라 `double` 0.1이 그 값이다.
- `divide` 는 **정확한 결과가 없으면 던진다**(`Non-terminating decimal expansion`) — 조용히 자르지 않는 것이 이 클래스의 설계다.
- `Math.round` 는 `HALF_UP` 이 아니다 — `Math.round(-0.5)` 가 `0` 이라 **음수에서 규칙이 갈린다.**

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 53번)
- [`../../../../data-representation/`](../../../../data-representation/) — 진수·IEEE 754 부동소수점.\
  **경계: 그쪽은 「0.1이 왜 2진수로 정확히 표현되지 않나」까지, 여기는 「그래서 자바에서 무엇을 쓰고 무엇을 조심하나」부터다.**\
  `0.1000000000000000055511...` 이라는 비트 패턴의 유래는 거기, 그 값을 출력해 보고 무엇을 결정하는지는 여기.
- [`../02-numeric-operations/`](../02-numeric-operations/) — **경계: 정수 오버플로·나눗셈 절단·`Math.*Exact` 는 거기,
  임의 정밀도 10진 연산은 여기.**\
  `intValueExact()` 가 던지는 이유는 거기의 `toIntExact` 와 같은 철학이다.
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — `Double` 에 캐시가 없는 이유, `==` 와 `equals`
- [`../35-string/`](../35-string/) — `toString`·`toPlainString` 이 돌려주는 `String` 자체
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **경계: `equals`/`hashCode` 계약 일반은 거기,
  「계약은 지켰는데 `compareTo` 와 어긋나는」 사례는 여기.**
- [**28번 주제**](../28-comparable-comparator/)(`Comparable`/`Comparator`) — "natural ordering inconsistent with equals" 가 정본으로 다뤄지는 곳
- 목록의 **51·52번 주제**(`java.time`) — 같은 "값 타입 설계"의 다른 사례

## 용어 풀이

- **스케일(scale)** — 소수점 아래 자릿수. `BigDecimal` 에서는 **값의 일부**다. 음수도 될 수 있다.
- **unscaled value** — 소수점을 없앤 정수. `값 = unscaled × 10^(-scale)`.
- **정밀도(precision)** — 유효숫자 개수. `MathContext` 가 다루는 단위이고 스케일과 다르다.
- **`MathContext`** — 유효숫자 개수 + 반올림 모드를 묶은 것. `DECIMAL32`·`DECIMAL64` 같은 상수가 있다.
- **`RoundingMode`** — 반올림 정책 enum. `HALF_UP`·`HALF_EVEN`·`UP`·`DOWN`·`CEILING`·`FLOOR`·`UNNECESSARY`.
- **`HALF_EVEN`(은행가 반올림)** — 0.5를 짝수 쪽으로 보내는 정책. 반복 반올림에서 편향을 없앤다.
- **`UNNECESSARY`** — "반올림이 필요 없다고 내가 단언한다"는 모드. 틀리면 `ArithmeticException` 을 던진다.
- **무한소수(non-terminating decimal expansion)** — 10진 소수로 유한하게 못 적는 값. `1/3` 이 그렇다.
- **natural ordering inconsistent with equals** — `compareTo` 가 0인데 `equals` 가 거짓인 상태. `BigDecimal` 이 대표 사례다.
- **`toPlainString()`** — 지수 표기 없이 그대로 쓰는 문자열. 스케일이 음수일 때 `toString()` 과 갈린다.
- **`signum()`** — 부호를 `-1`·`0`·`1` 로 돌려준다. 스케일과 무관하게 0을 판정할 수 있다.

## 더 들어가면

- **`BigDecimal` 에는 오버플로가 없다** — 임의 정밀도이기 때문이다(실행으로 확인).

```text
Long.MAX_VALUE       = 9223372036854775807
그 값 + 1 (long)     = -9223372036854775808
그 값 + 1 (BigDecimal)= 9223372036854775808
그 값 * 그 값         = 85070591730234615847396907784232501249
```

  [02번 주제](../02-numeric-operations/)의 `Math.addExact` 가 필요 없는 세계다.\
  대신 **메모리와 시간이 자릿수에 비례**하고, 스케일이 커지면 그만큼 느려진다.

- **"1인당 얼마" 계산에서 남는 돈은 코드가 정해야 한다**(실행으로 확인).

```text
1인당(버림)   = 3333   3명 합 = 9999   남는 돈 = 1
1인당(반올림) = 3333   3명 합 = 9999   차액 = 1
```

  `BigDecimal` 은 **1원이 남는다는 사실을 알려 줄 뿐** 누가 가질지는 안 정해 준다.\
  이런 "요구사항에 안 들어 있는 결정"은 반드시 명시적으로 처리한다.

- **`0.1` 을 열 번 더하면** `double` 은 `0.9999999999999999` 이고 `BigDecimal` 은 `1.0` 이다(실행으로 확인).\
  그런데 그 `1.0` 도 `BigDecimal.ONE` 과 `equals` 가 **`false`** 다 — 스케일이 1 대 0이기 때문이다.\
  **정확한 계산과 정확한 비교는 별개의 문제**라는 것을 한 줄로 보여 주는 예다.

- **`BigDecimal` 은 불변**이다. `setScale`·`add` 는 전부 새 객체를 반환한다 —\
  [35번 주제](../35-string/)의 `String` 과 같은 설계이고, 같은 실수(반환값을 안 받는 것)가 나온다.
