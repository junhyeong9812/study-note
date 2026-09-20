# java/syntax/02 — 수치 연산: 이항 승격·정수 오버플로·`Math.*Exact` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 바이트코드는 `javap -c` 출력을, JDK 소스는 `lib/src.zip` 의 실파일을, JLS는 원문을 그대로 옮겼다.\
> 실행 파일명은 전부 `Ex.java` 로 고정했다 — 예외 트레이스에 그 이름이 박힌다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌려 **정수 출력이 전부 동일**함을 확인했다(다른 점은 9번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 네 줄 중 어느 것이 컴파일되는가

**출력** (`javac Ex.java`, JDK 21.0.5 — 25.0.1 동일)

```text
Ex.java:4: error: incompatible types: possible lossy conversion from int to byte
        byte b3 = b1 + b2;
                     ^
Ex.java:6: error: incompatible types: possible lossy conversion from int to short
        short s3 = s1 + s2;
                      ^
Ex.java:8: error: incompatible types: possible lossy conversion from int to char
        char c2 = c + 1;
                    ^
3 errors
```

**컴파일되는 것과 안 되는 것**

| 줄 | 결과 | 이유 |
|---|---|---|
| (A) `byte b3 = b1 + b2;` | **에러** | `b1 + b2` 가 `int` 이고 `b1`·`b2` 가 상수 변수가 아니다 |
| (B) `byte b4 = 10 + 20;` | **된다** | `10 + 20` 이 상수 식이라 컴파일 타임에 `30` 으로 접힌다 |
| (C) `char c2 = c + 1;` | **에러** | `c` 가 상수 변수가 아니라 `c + 1` 이 상수 식이 아니다 |
| (D) `char c3 = fc + 1;` | **된다** | `fc` 가 `final` + 컴파일 타임 상수 = 상수 변수 |

**가르는 한 가지 조건**

- **식 전체가 상수 식인가.**
- 상수 식이고 값이 대상 타입 범위에 들어가면, **대입문에서 축소 변환이 예외적으로 허용**된다(JLS §5.2).
- 그래서 `final` 한 글자를 붙이는 것만으로 (C)가 (D)가 된다.

실행으로 확인한 (B)·(D)의 값:

```text
상수 식은 좁혀 대입된다: B 30
```

> **상수 식(constant expression)** — 컴파일 타임에 값이 확정되는 식(JLS §15.29).\
> 예: `10 + 20` 은 상수 식이고, `b1 + b2` 는 `b1`·`b2` 가 `final` 상수가 아니면 상수 식이 아니다.

**`b1 + b2` 의 타입과 바이트코드 확인법**

```text
  static int addBytes(byte, byte);
    Code:
       0: iload_0
       1: iload_1
       2: iadd
       3: ireturn
```

- 타입은 **`int`** 다.
- `javap -c` 에 `iload`·`iadd`·`ireturn` 이 나온다 — 전부 `i`(int) 계열이다.
- JVM에는 `badd`·`sadd` 같은 명령이 **없다.** `byte`·`short`·`char` 산술은 명령 수준에서 존재하지 않는다.
- 런타임에 확인하는 다른 방법: `((Object)(b1 + b2)).getClass().getSimpleName()` 이 `Integer` 를 낸다(실행으로 확인).

### 2. 하루를 마이크로초로 세면 무엇이 나오는가

**출력** (JDK 21.0.5 — 17·25 동일)

```text
24*60*60*1000         = 86400000
24*60*60*1000*1000    = 500654080
24L*60*60*1000*1000   = 86400000000
(long)(24*60*60*1000*1000) = 500654080
```

**네 값**

- `a` = **86400000** (맞다 — `int` 범위 안)
- `b` = **500654080** (틀리다 — 진짜 값은 86,400,000,000)
- `c` = **86400000000** (맞다)
- `d` = **500654080** (틀리다)

**`b` 와 `d` 가 같은 이유**

```text
b : 24*60*60*1000*1000 을 int 로 계산  -> 잘려서 500654080  -> long 변수에 대입
d : 24*60*60*1000*1000 을 int 로 계산  -> 잘려서 500654080  -> (long) 캐스트

           둘 다 "잘린 다음"에 long 이 된다. 캐스트가 시간을 되돌리지 못한다.
```

- 캐스트는 **이미 끝난 계산의 결과**에 걸린다.
- 리터럴은 전부 `int` 이므로 곱셈은 `int` 작업대에서 일어나고, 32비트를 넘는 순간 위쪽이 버려진다.\
  진짜 값 86,400,000,000 은 이진수로 **37비트**다(실행으로 확인) — 32비트에 다섯 비트가 모자란다.

**변수를 `long` 으로 선언했는데도 안 통하는 이유**

- 대입은 **계산이 다 끝난 뒤**에 일어난다. 왼쪽 타입은 오른쪽 식의 계산 타입을 바꾸지 않는다.
- 고치는 유일한 방법은 **곱셈이 시작되기 전에** 한쪽을 `long` 으로 만드는 것이다 — `24L * 60 * 60 * 1000 * 1000`.
- `L` 하나가 첫 곱셈부터 `lmul` 을 쓰게 만든다.

```text
  static long mulInt(int, int);          static long mulLong(int, int);
       0: iload_0                             0: iload_0
       1: iload_1                             1: i2l
       2: imul       <- int 곱셈              2: iload_1
       3: i2l        <- 잘린 뒤 확대           3: i2l
       4: lreturn                             4: lmul      <- long 곱셈
                                              5: lreturn
```

실행으로 확인: `mulInt(100000,100000) = 1410065408` / `mulLong(100000,100000) = 10000000000`.

**`Math.multiplyExact` 로 바꾸면**

```text
multiplyExact -> java.lang.ArithmeticException: integer overflow
```

- 틀린 값 대신 **그 줄에서 멈춘다.**
- 이것이 이 주제가 권하는 방어다 — 잘못된 값이 아래로 흘러가지 못하게 한다.

### 3. 절댓값이 음수가 되는 자리

**출력**

```text
Math.abs(MIN_VALUE)   = -2147483648
-Integer.MIN_VALUE    = -2147483648
absExact      -> java.lang.ArithmeticException: Overflow to represent absolute value of Integer.MIN_VALUE
```

**반환값과 그 이유**

```text
int 의 범위는 대칭이 아니다

  -2147483648 .................. 0 .......... 2147483647
       ^                                            ^
       |                                            |
  음수가 하나 더 많다                     |MIN_VALUE| = 2147483648 은
                                          이 범위에 없다
```

- `Math.abs(x)` 는 `x < 0 ? -x : x` 이고, `-(-2147483648)` 은 다시 `-2147483648` 이다.
- 절댓값 2147483648을 담을 `int` 자리가 **없기 때문**이다. 버그가 아니라 범위의 비대칭이다.

**`Math.abs(hash) % buckets` 가 깨지는 때**

- `hash` 가 정확히 `Integer.MIN_VALUE` 일 때.
- `Math.abs` 가 음수를 돌려주고 `%` 도 왼쪽 부호를 따라가므로 **음수 버킷 인덱스**가 나온다.
- 그 다음 줄의 배열 접근에서 `ArrayIndexOutOfBoundsException` 이 터진다 — **원인 줄과 터지는 줄이 다르다.**
- 확률은 42억분의 1이 아니다. 문자열 해시는 구조적으로 특정 값에 몰릴 수 있고, 공격자가 입력을 고를 수 있으면 확률 이야기가 아니다.

**한 줄로 고치는 메서드**

- **`Math.floorMod(hash, buckets)`.**
- 오른쪽 피연산자의 부호를 따라가므로 `buckets` 가 양수면 결과도 항상 0 이상이다.
- 실행으로 확인: `Math.floorMod(-1, 3) = 2`.

**`absExact` 의 메시지가 다른 이유**

- 다른 `*Exact` 는 전부 `integer overflow` / `long overflow` 로 통일돼 있다.
- `absExact` 만 `Overflow to represent absolute value of Integer.MIN_VALUE` 다.
- 넘칠 수 있는 입력이 **`MIN_VALUE` 하나뿐**이라 그 값을 메시지에 박아 둔 것이다.

### 4. 음수가 섞인 나눗셈과 나머지

**출력** (표 형태로 돌린 것, JDK 21.0.5 — 17·25 동일)

```text
   a    b |    a/b    a%b | floorDiv  floorMod
   7    2 |      3      1 |         3         1
  -7    2 |     -3     -1 |        -4         1
   7   -2 |     -3      1 |        -4        -1
  -7   -2 |      3     -1 |         3        -1
   6    3 |      2      0 |         2         0
  -6    3 |     -2      0 |        -2         0
  -1    3 |      0     -1 |        -1         2
```

**여섯 줄의 출력**

- `-7 / 2` -> **-3**
- `-7 % 2` -> **-1**
- `Math.floorDiv(-7, 2)` -> **-4**
- `Math.floorMod(-7, 2)` -> **1**
- `-1 % 3` -> **-1**
- `Math.floorMod(-1, 3)` -> **2**

**`/` 가 자르는 방향과 이름**

```text
        -3.5 라는 진짜 몫

  -4 <---------- -3.5 ----------> -3
   ^                               ^
 floorDiv                         자바의 /
 "아래로"                       "0 쪽으로"
```

- **0 쪽으로 자른다**(truncation toward zero).
- JLS §15.17.2 원문: "Integer division rounds toward 0."
- 양수에서는 "버림"과 같아서 차이가 안 보인다. **갈리는 것은 음수뿐이다.**

**`%` 의 부호**

- **왼쪽(피제수)을 따라간다.**
- `a % b` 가 `a - (a / b) * b` 로 정의되기 때문이다 — `/` 가 0 쪽으로 자르니 나머지도 `a` 쪽 부호가 된다.
- 반대로 `Math.floorMod` 는 `Math.floorDiv` 로 정의되므로 **오른쪽(제수)의 부호**를 따라간다.

**링 버퍼에서 터지는 것**

```text
int i = (cur - 1) % 3;

  cur = 0 -> (0 - 1) % 3 = -1 % 3 = -1
                                     |
                                     v
                          arr[-1] -> ArrayIndexOutOfBoundsException
```

- 앞으로 도는 `(cur + 1) % n` 은 멀쩡한데 **뒤로 도는 순간** 깨진다.
- 테스트가 앞으로만 돌면 초록이다.
- 고치는 법: `Math.floorMod(cur - 1, n)`.

### 5. 시프트 세 줄

**출력** (JDK 21.0.5 — 17·25 동일)

```text
n        = -8  11111111111111111111111111111000
n >> 1   = -4  11111111111111111111111111111100
n >>> 1  = 2147483644  01111111111111111111111111111100
1 << 32  = 1           00000000000000000000000000000001
byte -8 >>> 1 = 2147483644
```

**네 줄의 출력**

- `n >> 1` -> **-4**
- `n >>> 1` -> **2147483644**
- `1 << 32` -> **1**
- `sb >>> 1` (`byte sb = -8`) -> **2147483644**

**`1 << 32` 가 `0` 이 아닌 이유**

```text
소스가 시킨 것            JVM 이 실제로 민 거리
  1 << 32      ---->      32 & 0x1f = 0
                          -> 하나도 안 민다 -> 1
```

- 시프트 거리는 **왼쪽 피연산자의 승격 타입**에 따라 마스크된다.
- `int` 면 하위 5비트(`& 0x1f`), `long` 이면 하위 6비트(`& 0x3f`).
- JLS §15.19가 마스크 값까지 적어 두었다 — 구현 재량이 아니라 **언어 규칙**이다.
- 실행으로 확인: `1 << 33 = 2`(33 & 31 = 1), `1L << 32 = 4294967296`.

**`byte` 에 `>>>` 를 썼는데 큰 양수가 나온 이유**

```text
byte sb = -8                       11111000  (8비트)
        ↓ 단항 수치 승격 (부호 확장)
int      -8                        11111111111111111111111111111000
        ↓ >>> 1
int      2147483644                01111111111111111111111111111100
```

- **시프트 전에 `int` 로 승격**되면서 왼쪽이 1로 채워진다(부호 확장).
- 그 상태에서 논리 시프트를 하니 "0으로 채운다"가 32비트 기준이 된다.
- 의도가 "바이트의 8비트만 밀기"였다면 **마스크를 먼저** 씌워야 한다: `(sb & 0xFF) >>> 1`.
- 참고로 `(byte)(sb >>> 1)` 은 `-4` 다 — 잘라 내려 봐야 이미 늦었다(실행으로 확인).

**`x / 2` 를 `x >> 1` 로 바꾸면**

- **음수에서 답이 달라진다.** `-7 / 2 = -3` 이지만 `-7 >> 1 = -4` 다.
- `>>` 는 바닥 나눗셈(`floorDiv`)이고 `/` 는 0 쪽 절단이라, 음수 홀수에서 1 차이가 난다.
- 성능 목적이라면 하지 않는다 — JIT가 이미 한다. 그리고 **틀린 값으로 바꾸는 최적화는 최적화가 아니다.**

### 6. 축약형이 더 안전해 보이는 함정

**출력**

```text
byte b=100; b += 300; -> -112
byte c=100; c *= 2;   -> -56
char ch='A'; ch += 1; -> B
int i=5; i /= 2;      -> 2
```

**어느 쪽이 컴파일되는가**

- **(A) `b = b + 300;` 은 컴파일 에러다.** `int` 를 `byte` 에 넣을 수 없다.
- **(B) `b += 300;` 은 컴파일된다.**

**컴파일되는 쪽의 출력**

- **`-112`.**
- 손계산: `100 + 300 = 400`. `400 & 0xFF = 0x90 = 144`. `byte` 는 부호 있는 8비트이므로 `144 - 256 = -112`.\
  실행 결과와 일치한다.

**갈리는 이유 — 언어 명세의 어느 규칙**

- JLS §15.26.2 **복합 대입 연산자** 규칙이다.
- `E1 op= E2` 는 `E1 = (T)(E1 op E2)` 와 같다 — `T` 는 `E1` 의 타입이고, **캐스트가 규칙에 포함돼 있다.**
- 즉 `b += 300` 은 내가 안 쓴 `(byte)` 캐스트를 **언어가 넣어 준다.**
- 그래서 **긴 쪽이 안전하고 짧은 쪽이 위험하다** — 직관과 반대다.

**`javap -c` 에서 보이는 흔적**

```text
  static byte addAssign(byte, byte);
    Code:
       0: iload_0
       1: iload_1
       2: iadd
       3: i2b        <- 소스에 없는 축소 변환
       4: istore_0
       5: iload_0
       6: ireturn
```

- **`i2b`**(int to byte)가 그 캐스트다.
- `char` 면 `i2c`, `short` 면 `i2s` 가 같은 자리에 나온다.
- 소스에는 `(byte)` 라는 글자가 없는데 클래스 파일에는 변환 명령이 있다.

### 7. 넘치는 순간 던지게 만들기

**출력** — 앞의 셋은 잡아서 찍은 것이고, 마지막은 잡지 않고 터뜨린 것이다.

```text
addExact      -> java.lang.ArithmeticException: integer overflow
multiplyExact -> java.lang.ArithmeticException: integer overflow
toIntExact    -> java.lang.ArithmeticException: integer overflow
```

```text
Exception in thread "main" java.lang.ArithmeticException: long overflow
	at java.base/java.lang.Math.addExact(Math.java:931)
	at Ex.main(Ex.java:4)
```

**클래스와 메시지**

| 호출 | 예외 | 메시지 |
|---|---|---|
| `Math.addExact(Integer.MAX_VALUE, 1)` | `ArithmeticException` | `integer overflow` |
| `Math.multiplyExact(86400000, 1000)` | `ArithmeticException` | `integer overflow` |
| `Math.toIntExact(Long.MAX_VALUE)` | `ArithmeticException` | `integer overflow` |
| `Math.addExact(Long.MAX_VALUE, 1L)` | `ArithmeticException` | `long overflow` |

- 전부 `RuntimeException` 계열이라 **검사 예외가 아니다** — 안 잡아도 컴파일된다.
- 그래서 "`*Exact` 를 썼으니 안전하다"가 아니라, **터졌을 때 무엇을 할지**까지 정해야 방어가 완성된다.

**`int` 판과 `long` 판의 메시지 차이**

- `integer overflow` 대 `long overflow` — **오버로드가 갈린 것이 메시지로 드러난다.**
- 값이 `int` 인 줄 알았는데 메시지가 `long overflow` 면, 어딘가에서 이미 승격이 일어난 것이다.
- 반대로 `toIntExact(long)` 은 입력이 `long` 인데 메시지가 `integer overflow` 다 — **넣으려는 그릇이 `int`** 이기 때문이다.

JDK 21 소스의 구현이 그 메시지를 어디서 내는지 그대로 보여 준다.

```java
// JDK 21.0.5  java.base/java/lang/Math.java  907~914행 — 실제 소스 그대로
public static int addExact(int x, int y) {
    int r = x + y;
    // HD 2-12 Overflow iff both arguments have the opposite sign of the result
    if (((x ^ r) & (y ^ r)) < 0) {
        throw new ArithmeticException("integer overflow");
    }
    return r;
}
```

- **먼저 더하고**(이미 감긴 값), 부호 비트로 감겼는지 판정한다.
- 그래서 비용은 XOR·AND·비교 세 줄이다.

**`Math.*Exact` 를 쓰면 안 되는 코드**

- **감기는 것이 의도인 코드.** 해시 섞기·체크섬·의사난수·비트 연산.
- `String.hashCode` 의 `31 * h + c` 는 **넘치라고 만든 식**이다. 여기에 `multiplyExact` 를 넣으면 정상 입력에서 예외가 난다.
- 판단 기준: **"넘친 값이 결과로 의미가 있나?"** 있으면 연산자, 없으면 `*Exact`.

### 8. 0으로 나누면

**출력**

```text
5.0 / 0   = Infinity
-5.0 / 0  = -Infinity
0.0 / 0.0 = NaN
5 / 0     -> java.lang.ArithmeticException: / by zero
5 % 0     -> java.lang.ArithmeticException: / by zero
```

**`5 / 0` 과 `5.0 / 0`**

```text
정수 나눗셈                              부동소수 나눗셈
+---------------------------+          +---------------------------+
| 표현할 값이 없다           |          | Infinity 라는 값이 있다    |
| -> 예외를 던진다           |          | -> 값으로 돌려준다         |
| 그 줄에서 멈춘다           |          | 계속 계산된다              |
+---------------------------+          +---------------------------+
   시끄럽게 실패한다                      조용히 번진다
```

- 정수는 **던진다** — 그래서 금방 잡힌다.
- 부동소수는 **값을 준다** — `Infinity` 가 이후 계산을 전부 오염시키고, 로그에는 아무것도 안 남는다.

**`5 % 0` 의 메시지**

- 메시지가 **`/ by zero`** 다. `%` 인데 `/` 라고 적혀 있다.
- 나머지 연산이 나눗셈으로 정의돼 있어서 같은 메시지를 공유한다.
- 헷갈리는 이유: 스택트레이스 줄 번호를 보고 `/` 를 찾다가 `%` 를 지나치게 된다. **줄 번호를 믿고 그 줄 전체를 봐야 한다.**

**`0.0 / 0.0` 과 그 뒤**

- **`NaN`**(Not a Number)이다.
- `NaN` 은 **자기 자신과도 `==` 가 `false`** 다. 그래서 `if (x == x)` 가 거짓이 되는 유일한 값이다.
- `NaN` 이 들어간 모든 산술은 `NaN` 을 낳고, 비교는 전부 `false` 가 된다 —\
  정렬에 넣으면 순서가 무너지고, 임계값 비교(`x > limit`)는 **항상 거짓**이 되어 경보가 안 울린다.
- 검사법은 `Double.isNaN(x)` 다. `x == Double.NaN` 은 **언제나 `false`** 라 검사가 안 된다.\
  *(이 문단의 `NaN` 비교 동작은 안 돌려 봤다 — 실행으로 확인한 것은 `0.0/0.0 = NaN` 까지다.)*

### 9. 누가 보장하고 누가 안 보장하는가

**정수 오버플로의 결과값은 누가 정하는가**

- **언어 명세가 정한다.** JVM 구현 재량이 아니다.
- JLS §4.2.2 원문: "The integer operators do not indicate overflow or underflow in any way."
- 값까지 정해져 있다 — 정수는 2의 보수이고 연산은 모듈러 연산이다.\
  그래서 `Integer.MAX_VALUE + 1` 은 **어느 JVM에서도** `-2147483648` 이다.
- 이것이 C와 갈리는 지점이다. C의 부호 있는 정수 오버플로는 *정의되지 않은 동작*이라 컴파일러가 마음대로 해도 된다.

**`Math.sin` 의 마지막 자리**

- **달라도 된다.** 근거는 `Math` 클래스 javadoc 자신이다(JDK 21 소스 원문).

> Unlike some of the numeric methods of class `StrictMath`, all implementations of the equivalent
> functions of class `Math` are not defined to return the bit-for-bit same results. This relaxation
> permits better-performing implementations where strict reproducibility is not required.

- 각 메서드에는 "The computed result must be within 1 ulp of the exact result. Results must be semi-monotonic." 가 붙어 있다.
- 즉 **정답 옆 칸까지 허용**하고, 단조성만 지키면 된다.

**비트까지 같아야 하면**

- **`StrictMath`** 를 쓴다. 이름 그대로 재현성을 보장한다.
- 단 정수 메서드(`addExact`·`floorDiv`·`floorMod`)에는 애초에 재량이 없다 — 답이 하나뿐이다.

**JDK 17에서 컴파일조차 안 되는 것**

```text
Ex.java:3: error: cannot find symbol
        System.out.println("Math.ceilDiv(7, 2)       = " + Math.ceilDiv(7, 2));
                                                               ^
  symbol:   method ceilDiv(int,int)
  location: class Math
```

- `Math.ceilDiv`·`Math.divideExact`·`Math.floorDivExact` 가 17에 **없다**. 21·25에는 있다.\
  JDK 21 `src.zip` 의 `Math.java` 에서 셋 다 **`@since 18`** 임을 확인했다\
  (18·19·20 JDK는 이 머신에 없어 **그 버전들에서는 안 돌려 봤다**).
- 21·25에서의 출력: `Math.ceilDiv(7,2) = 4` · `Math.ceilDiv(-7,2) = -3` ·
  `Math.divideExact(Integer.MIN_VALUE,-1) -> ArithmeticException: integer overflow`.
- 한편 `strictfp` 를 붙이면 **세 JDK 모두** 이렇게 경고한다 — 컴파일러가 직접 버전 경계를 말해 준다.

```text
Ex.java:1: warning: [strictfp] as of release 17, all floating-point expressions are evaluated strictly and 'strictfp' is not required
```

### 10. 이진 탐색의 중간값

**출력** (`big1 = big2 = 2_000_000_000`)

```text
(big1+big2)/2 = -147483648
(big1+big2)>>>1 = 2000000000
big1+(big2-big1)/2 = 2000000000
```

**언제 깨지는가**

- `low + high` 가 `Integer.MAX_VALUE`(21억)를 넘을 때.
- 배열 길이가 10억을 넘는 경우 — 또는 **인덱스가 아니라 값**(타임스탬프·금액·ID)에 이진 탐색을 할 때.
- 실행으로 확인한 값: `(2_000_000_000 + 2_000_000_000) / 2 = -147483648`.

**스택트레이스가 가리키는 줄**

```text
int mid = (low + high) / 2;      <- 진짜 원인 (조용히 음수를 만든다)
if (arr[mid] < key) { ... }      <- 터지는 줄 (ArrayIndexOutOfBoundsException)
```

- 트레이스는 **배열 접근 줄**을 가리킨다.
- 그 줄만 보면 "인덱스 계산이 잘못됐나" 정도로 보이고, **위쪽 덧셈이 넘쳤다**는 생각까지 가기 어렵다.
- 예외 메시지에 인덱스가 찍히는데 그 값이 **음수**라면 거의 항상 오버플로다.

**`>>> 1` 이 고쳐 주는 이유**

실행 출력 그대로 (JDK 21.0.5):

```text
4000000000 의 이진수     = 11101110011010110010100000000000
big1+big2 (int)      = -294967296  11101110011010110010100000000000
(big1+big2) >>> 1    = 2000000000  01110111001101011001010000000000
(big1+big2) >> 1     = -147483648
(big1+big2) / 2      = -147483648
```

```text
2,000,000,000 + 2,000,000,000 = 4,000,000,000

  4,000,000,000 의 비트   11101110011010110010100000000000   <- 정확히 32비트
  int 에 들어간 비트       11101110011010110010100000000000   <- 한 비트도 안 잘렸다
                          ^
                          최상위 비트가 1 -> int 는 이것을 부호로 읽는다 -> -294967296

  >>> 1 로 밀면           01110111001101011001010000000000  = 2,000,000,000
  /  2 로 나누면          음수 -294967296 을 반으로 -> -147483648
```

- **비트는 하나도 안 잘렸다.** 32비트에 딱 들어갔고, 다만 **최상위 비트가 부호로 읽힌 것**이다.\
  (`int` 가 담는 양수는 31비트까지다 — 32번째 비트는 부호 자리다.)
- `>>>` 는 그 비트열을 **부호 없이 읽고** 한 칸 민다 — 그래서 원래 합의 절반이 그대로 나온다.
- `>>` 를 쓰면 안 된다. 부호 비트를 복제하므로 음수인 채로 밀려 `/ 2` 와 같은 답이 된다(위 출력 확인).
- 합이 2^32 를 넘으면(예: `Integer.MAX_VALUE` 두 개가 아니라 더 큰 `long` 값) 그때는 진짜로 비트가 잘리므로 `>>>` 도 못 고친다.

**둘 중 어느 쪽을 고르겠는가**

- **`low + (high - low) / 2`** 를 고른다.
- 이유: **읽는 사람이 검산할 수 있다.** "낮은 값에서 차이의 절반만큼 간다"는 문장이 그대로 코드다.
- `>>> 1` 은 맞지만 **왜 맞는지가 비트 수준 논증**이라, 나중에 누가 `>> 1` 로 "정리"할 위험이 있다.
- 단 `low` 가 음수일 수 있으면 `high - low` 쪽이 넘칠 수 있으므로, 그때는 `>>> 1` 이나 `long` 으로 간다.

### 11. 다른 주제와 잇기

**`Integer a = 127, b = 127; a == b` 와 이항 승격**

- `a == b` 는 **둘 다 참조 타입**이라 이항 수치 승격이 **적용되지 않는다** — 참조 비교다([01번 주제](../01-primitives-and-wrappers/)).
- 반면 `a == 127` 처럼 **한쪽이 기본형**이면 이항 수치 승격이 적용되고, 승격은 **언박싱을 포함**한다(JLS §5.6.2).
- 그래서 이 주제의 규칙이 01의 규칙을 설명한다: "한쪽이라도 기본형이면 값 비교"는
  **"이항 수치 승격이 걸리면 값 비교"의 다른 표현**이다.
- `Integer x = 1; Integer y = 2; x + y` 도 같은 이유로 언박싱된다 — `+` 가 이항 수치 승격을 요구한다.

**금액을 `long` 원 단위로 바꾸면**

| | 사라지는 위험 | 남는 위험 |
|---|---|---|
| `double` -> `long` 원 단위 | 0.1 의 표현 오차, `==` 비교 실패 | 오버플로(`long` 도 유한하다) |
| | 반올림 오차 누적 | 나눗셈의 절단 — **1원이 사라진다** |

- `long` 은 약 9.2×10^18 까지다. 원 단위 금액이라면 현실적으로 안 넘치지만,\
  **중간 계산에서 곱셈이 겹치면** 넘칠 수 있다(단가 × 수량 × 세율 보정 배수).
- 더 자주 물리는 것은 **나눗셈의 절단**이다 — `10000 / 3` 이 `3333` 이고 셋을 합쳐도 `9999` 다.\
  남는 1원을 누가 갖는지는 코드가 정해야 한다.
- 소수점이 있는 요율·이자가 섞이면 `long` 으로는 안 되고 [`../53-bigdecimal/`](../53-bigdecimal/) 로 간다.

**`'A' + 'B'` 가 `131` 인데 `"" + 'A' + 'B'` 가 `"AB"` 인 이유**

```text
'A' + 'B'                          "" + 'A' + 'B'
  둘 다 char -> 이항 수치 승격        왼쪽부터 평가한다
  int(65) + int(66) = 131            ("" + 'A') -> "A"      <- 한쪽이 String 이면 문자열 연결
                                     ("A" + 'B') -> "AB"
```

- `+` 는 **한쪽이 `String` 이면 문자열 연결**, 아니면 산술 덧셈이다(JLS §15.18).
- 결합 방향이 **왼쪽부터**라서 `"" + 'A'` 가 먼저 문자열이 되고, 그 뒤는 전부 연결이 된다.
- 그래서 `1 + 2 + "x"` 는 `"3x"` 이고 `"x" + 1 + 2` 는 `"x12"` 다(실행으로 확인).
- 문자열 연결이 실제로 어떤 바이트코드가 되는지는 [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/).

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex`(02-promo) | 이항 승격의 결과 타입 8종, 상수 식 축소 대입, `char` 산술, 문자열 연결 순서 | 17 · 21 · 25 (동일) |
| `Ex`(02-promoerr) `javac` | `byte`/`short`/`char` 축소 대입 컴파일 에러 3종 | 21 · 25 (동일) |
| `Ex`(02-overflow) | `MAX_VALUE+1`, `Math.abs(MIN_VALUE)`, 마이크로초 곱셈, `*Exact` 5종 메시지 | 17 · 21 · 25 (동일) |
| `Ex`(02-longexact) | 잡지 않은 `long overflow` 스택트레이스 | 21 |
| `Ex`(02-div) | `/`·`%`·`floorDiv`·`floorMod` 7행 표, 0 나눗셈, `MIN_VALUE / -1` | 17 · 21 · 25 (동일) |
| `Ex`(02-shift) | `>>`/`>>>`, 시프트 거리 마스크, `byte >>> `, 이진 탐색 중간값 | 17 · 21 · 25 (동일) |
| `Ex`(02-compound) `javap -c` | `+=` 의 `i2b`, `imul`+`i2l` 대 `i2l`+`lmul`, `iadd` | 17 · 21 · 25 (동일) |
| `Ex`(02-newmath) | `ceilDiv`·`divideExact`·`floorDivExact` | 17 **컴파일 실패** · 21 · 25 (동일) |
| `Ex`(02-strictfp) `javac` | `strictfp` 경고 문구 | 17 · 21 · 25 (동일) |
| `Ex`(02-mid) | 이진 탐색 중간값의 비트 패턴 — `>>> 1` 대 `>> 1` 대 `/ 2` | 21 |
| `Ex`(02-bits) | 오버플로 예제들의 실제 비트 폭(34·32·37비트)과 `(int)` 캐스트 결과 | 21 |
| `src.zip` 열람 | `Math.addExact` 구현과 `Math` 클래스 javadoc | 21 |
| JLS 원문 | §4.2.2 오버플로 · §15.17.2 절단과 `MIN_VALUE/-1` 특례 · §15.19 시프트 마스크 | — |

**구현에 의존하는 항목** — 이 주제에는 거의 없다.\
정수 연산은 전부 언어 보장이고, 구현 재량은 `Math` 의 **초월 함수 마지막 자리**(1 ulp)뿐이다.

**버전이 오르면 다시 돌려야 할 것**

- `Math` 에 새 메서드가 들어왔는지(`ceilDiv` 계열이 17→21 사이에 들어온 전례가 있다).
- `*Exact` 의 **예외 메시지 문구** — 메시지는 명세가 아니라 구현이다.
- 나머지 정수 출력은 명세가 못박았으므로 바뀌면 그것이 버그다.

## 안 돌려 본 것

- `Integer.divideUnsigned`·`compareUnsigned`·`toUnsignedLong` — 「더 들어가면」에서 이름만 들었다.
- `NaN` 의 비교 동작(`x == x` 가 `false`, `Double.isNaN`) — `0.0/0.0 = NaN` 까지만 돌렸다.
- `Math.ceilDiv` 계열을 **18·19·20 JDK에서** — 이 머신에 없다. `@since 18` 은 소스에서 읽었고 17/21/25만 돌렸다.
- `Math.addExact` 의 실제 비용(JIT가 하드웨어 플래그로 낮추는지) — 측정하지 않았다.
- `StrictMath` 와 `Math` 의 결과가 이 머신에서 실제로 갈리는지 — **안 돌려 봤다.**
