# java/syntax/02 — 수치 연산: 이항 승격·정수 오버플로·`Math.*Exact` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §4.2.2 Integer Operations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) · [§5.6 Numeric Contexts](https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html) · [§15.17 Multiplicative Operators](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html) · [§15.19 Shift Operators](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/Math.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 11개를 돌렸고, 그중 **정수 연산 5개**(승격·오버플로·나눗셈·시프트·복합 대입)는
> **17.0.13 · 21.0.5 · 25.0.1** 세 버전에서 모두 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> 단 `Math.ceilDiv`·`divideExact`·`floorDivExact` 는 **17에서 컴파일되지 않는다**(「구현 세부사항 대 언어 보장」).
> **버전** — 정수 연산 규칙 자체는 Java 1.0부터 같다. 아래 `@since` 는 JDK 21 `src.zip` 의 `Math.java` 에서 직접 읽은 것이다.\
> `addExact`·`multiplyExact`·`floorDiv`·`floorMod`·`toIntExact` = **1.8** · `absExact` = **15** ·
> `ceilDiv`·`divideExact`·`floorDivExact` = **18**(실행으로도 17에 없고 21·25에 있음을 확인).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**계산은 넓은 작업대에서 하고, 결과는 정해진 크기의 서랍에 넣는다.**\
작업대보다 큰 결과가 나오면 **서랍에 들어가는 만큼만 남고 나머지는 잘린다** — 그리고 아무도 안 알려 준다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 작업대 | 연산이 실제로 수행되는 타입 — `int` 보다 작은 타입은 없다 |
| 작업대에 올리기 전 크기를 맞추는 것 | 이항 수치 승격(binary numeric promotion) |
| 서랍 | 결과를 담는 변수의 선언 타입 (`byte`·`short`·`int`·`long`) |
| 서랍보다 큰 것을 넣을 때 잘려 나가는 것 | 정수 오버플로 — **예외도 경고도 없다** |
| 12시 다음이 1시가 되는 시계판 | 2의 보수 — `MAX_VALUE` 다음 값이 `MIN_VALUE` |
| 시계가 한 바퀴 돌면 울리는 알람 | `Math.addExact`·`multiplyExact` — 넘치면 예외를 던진다 |

- `byte` 두 개를 더하면 **작업대 위에서는 둘 다 `int` 가 된다.**\
  그래서 결과도 `int` 이고, `byte` 서랍에는 **안 들어간다**(컴파일 에러).
- `int` 끼리 곱한 결과가 `int` 서랍을 넘치면 **위쪽 비트가 통째로 잘린다.**\
  잘린 값은 시계판이 한 바퀴 돈 것처럼 **음수가 되어 조용히 흘러간다.**
- `Math.multiplyExact` 는 같은 곱셈을 하되 **넘치는 순간 `ArithmeticException` 을 던진다.**\
  값이 틀린 채 흘러가는 대신 **그 자리에서 멈춘다.**

```text
int a = 100000, b = 100000;      a * b 의 진짜 값 = 10,000,000,000

  작업대 (int 32비트)                   서랍 (int 32비트)
  +--------------------------+         +------------------+
  | 10000000000 을 계산했다   |  ---->  | 아래 32비트만     |  ---->  1410065408
  | 하지만 34비트가 필요하다   |  잘림   | 1410065408       |         (실행으로 확인)
  +--------------------------+         +------------------+
                                             |
                                             +-- 예외 없음 · 경고 없음 · 로그 없음
```

실무에서 이게 터지는 자리는 **밀리초 계산과 금액 곱셈**이다.\
`24 * 60 * 60 * 1000 * 1000` 은 하루를 마이크로초로 센 값이어야 하는데 실행하면 `500654080` 이 나온다.\
테스트가 하루치만 돌면 통과하고, 기간이 길어지는 순간 **음수 잔액**이나 **과거 시각**으로 조용히 틀린다.

> **이항 수치 승격(binary numeric promotion)** — 이항 연산자의 두 피연산자를 하나의 공통 타입으로 맞추는 변환(JLS §5.6.2).\
> 예: `byte + byte` 는 둘 다 `int` 로 올려서 계산하고, 결과도 `int` 다.

> **정수 오버플로(integer overflow)** — 결과가 그 타입이 표현할 수 있는 범위를 넘어 위쪽 비트가 버려지는 것.\
> 예: `Integer.MAX_VALUE + 1` 은 예외를 내지 않고 `-2147483648` 이 된다.

> **2의 보수(two's complement)** — 음수를 표현하는 방식. 최상위 비트가 1이면 음수다.\
> 예: `int` 의 비트가 전부 1이면 `-1` 이다. **표현 방식 자체는 [`data-representation/`](../../../../data-representation/) 가 정본**이고,
> 여기서는 "자바 연산자가 그 표현 위에서 무엇을 하나"만 다룬다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `byte + byte` 는 왜 `byte` 가 아닌가 — **연산은 어느 타입에서 일어나는가.**
2. 계산 결과가 타입 범위를 넘으면 무엇이 일어나는가 — **누가 알려 주고 누가 안 알려 주는가.**
3. 나눗셈과 시프트는 **음수에서 어느 방향으로 가는가** — 그리고 그 방향을 내가 고를 수 있는가.

## 동작 방식

### (1) 이항 수치 승격 — 작업대에는 `int` 보다 작은 것이 없다

**언제 쓰나** — `+ - * / % < > == & | ^` 같은 이항 연산자를 쓸 때마다. 즉 거의 모든 계산에서.

```text
byte b1 = 10;  byte b2 = 20;        b1 + b2

  소스가 말하는 것                      작업대 위에서 실제로 일어나는 것
  +------------------+                +----------------------------------+
  | byte + byte      |  ---- 승격 --> | int(10) + int(20)                |
  | (8비트 + 8비트)   |                | (32비트 + 32비트) -> int(30)      |
  +------------------+                +----------------------------------+
                                                     |
                                      byte 서랍(8비트)에 넣으려면 ---+
                                                                   v
                                          error: possible lossy conversion
                                                 from int to byte
```

실행 결과 — 결과 타입을 박싱해 `getClass()` 로 물어본 것이다(JDK 21.0.5).

```text
byte  + byte  -> Integer
short + short -> Integer
char  + char  -> Integer
byte  + int   -> Integer
int   + long  -> Long
long  + float -> Float
float + double-> Double
char  + int   -> Integer
```

그림 해설 (한 단계씩):

- `byte`·`short`·`char` 는 **연산 전에 전부 `int` 로 올라간다.**\
  JVM에는 `badd`(byte 덧셈) 같은 명령이 아예 없다 — 바이트코드는 `iadd` 하나뿐이다.
- 한쪽이 `long`·`float`·`double` 이면 **더 넓은 쪽으로** 맞춘다.\
  순서는 `double` > `float` > `long` > `int` 다.
- 그래서 **결과 타입은 피연산자 중 가장 넓은 타입이거나, 둘 다 `int` 보다 작으면 `int`** 다.

`javap -c` 로 본 `byte + byte` (출력 그대로):

```text
  static int addBytes(byte, byte);
    Code:
       0: iload_0
       1: iload_1
       2: iadd
       3: ireturn
```

`iload`(int 로 읽기) · `iadd`(int 덧셈) · `ireturn`(int 반환) — **소스의 `byte` 는 흔적도 없다.**

비용 — 없다. 승격은 컴파일 타임 결정이고 바이트코드에는 변환 명령조차 안 나온다(`byte`/`short` 는 스택에 이미 int 로 올라간다).

### (2) 정수 오버플로 — 자바는 잘라 내기로 **명세에 못박았다**

**언제 쓰나** — `int`·`long` 산술의 결과가 범위를 넘을 때. 즉 "설마 넘치겠어"라고 생각하는 모든 자리.

```text
Integer.MAX_VALUE = 2147483647                  ... 시계판을 한 칸 더 돌리면

   -2147483648 ...... 0 ...... 2147483647
        ^                           |
        |                           | +1
        +---------------------------+
          여기로 돌아온다 (예외 없음)
```

실행 결과 (JDK 21.0.5 — 17·25 동일):

```text
Integer.MAX_VALUE     = 2147483647
max + 1               = -2147483648
Integer.MIN_VALUE - 1 = 2147483647
-Integer.MIN_VALUE    = -2147483648
Math.abs(MIN_VALUE)   = -2147483648
24*60*60*1000         = 86400000
24*60*60*1000*1000    = 500654080
24L*60*60*1000*1000   = 86400000000
(long)(24*60*60*1000*1000) = 500654080
Long.MAX_VALUE + 1    = -9223372036854775808
```

그림 해설 (한 단계씩):

- `max + 1` 이 **`MIN_VALUE` 로 감긴다.** 오류가 아니라 **명세가 시킨 동작**이다.
- `-Integer.MIN_VALUE` 와 `Math.abs(Integer.MIN_VALUE)` 가 **음수 그대로다.**\
  `int` 범위가 비대칭(`-2^31` ~ `2^31-1`)이라 `MIN_VALUE` 의 절댓값은 `int` 에 없다.
- 마지막 두 줄이 이 절의 핵심이다 — `(long)(24*60*60*1000*1000)` 은 **이미 잘린 뒤에 `long` 으로 늘린다.**\
  `long` 으로 만들려면 **곱셈이 시작되기 전에** 한쪽을 `long` 으로 만들어야 한다(`24L * ...`).

`javap -c` 로 본 두 형태 (출력 그대로):

```text
  static long mulInt(int, int);          static long mulLong(int, int);
    Code:                                  Code:
       0: iload_0                             0: iload_0
       1: iload_1                             1: i2l          <- 먼저 long 으로
       2: imul        <- int 곱셈             2: iload_1
       3: i2l         <- 그 다음 long          3: i2l
       4: lreturn                             4: lmul         <- long 곱셈
                                              5: lreturn
```

- 왼쪽은 `imul`(int 곱셈) 뒤에 `i2l` — **잘린 값을 늘린다.**
- 오른쪽은 `i2l` 두 번 뒤에 `lmul` — **안 잘린 값을 곱한다.**
- 실행 결과: `mulInt(100000,100000) = 1410065408` / `mulLong(100000,100000) = 10000000000`.

비용 — `long` 산술은 64비트라 32비트 환경에서 더 비싸지만, **틀린 값보다 싸다.**

### (3) `Math.*Exact` — 같은 계산에 알람을 단다

**언제 쓰나** — 넘치면 **값이 틀리는 것보다 멈추는 게 나은** 계산. 금액·수량·기간 누적.

```text
같은 곱셈, 다른 결말

  a * b                                Math.multiplyExact(a, b)
  +---------------------------+        +---------------------------+
  | 34비트 결과를 32비트에     |        | 34비트가 필요한 걸 감지    |
  | 잘라 넣는다               |        | 하고 던진다                |
  | -> 1410065408 (틀린 값)   |        | -> ArithmeticException     |
  | 프로그램은 계속 돈다       |        | 프로그램이 그 줄에서 멈춘다 |
  +---------------------------+        +---------------------------+
```

실행 결과 — **던져 본 것 그대로다**(JDK 21.0.5).

```text
addExact      -> java.lang.ArithmeticException: integer overflow
multiplyExact -> java.lang.ArithmeticException: integer overflow
negateExact   -> java.lang.ArithmeticException: integer overflow
toIntExact    -> java.lang.ArithmeticException: integer overflow
absExact      -> java.lang.ArithmeticException: Overflow to represent absolute value of Integer.MIN_VALUE
Math.addExact(1L, 2L) = 3
```

잡지 않고 그대로 터뜨리면 이렇게 나온다(`long` 판, 실행 출력 그대로).

```text
Exception in thread "main" java.lang.ArithmeticException: long overflow
	at java.base/java.lang.Math.addExact(Math.java:931)
	at Ex.main(Ex.java:4)
```

그림 해설 (한 단계씩):

- 메시지가 **`integer overflow` 와 `long overflow` 로 갈린다** — 어느 오버로드가 불렸는지 메시지로 알 수 있다.
- `absExact` 만 메시지가 다르다 — 넘치는 이유가 하나뿐이라 그 이유를 적어 준다.
- `toIntExact(long)` 도 같은 계열이다 — **넓은 타입을 좁은 타입에 넣을 때** 쓴다.

비용 — 오버플로 검사 한 번. `addExact` 는 부호 비트 비교 몇 줄이라 사실상 공짜이고,
JIT가 하드웨어 오버플로 플래그로 낮춰 컴파일할 수 있다. *(비용의 실제 수치는 안 재 봤다.)*

### (4) 정수 나눗셈 — 0 쪽으로 자른다, 그리고 `%` 는 그 방향을 따라간다

**언제 쓰나** — `/` 와 `%` 를 음수가 섞일 수 있는 값에 쓸 때. 배열 인덱스·요일 계산·페이지 계산.

```text
        -7 / 2 의 진짜 값은 -3.5

  -4 <---------- -3.5 ----------> -3
   ^                               ^
   |                               |
 floorDiv                          / (자바의 나눗셈)
 "아래로 내린다"                    "0 쪽으로 자른다"
```

실행 결과 (JDK 21.0.5, 출력 그대로):

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

그림 해설 (한 단계씩):

- `/` 는 **0 쪽으로 자른다**(truncation toward zero) — `-7/2` 가 `-4` 가 아니라 `-3` 이다.
- `%` 의 부호는 **왼쪽 피연산자를 따라간다** — `-7 % 2` 가 `-1` 이다. `1` 이 아니다.
- `Math.floorDiv` 는 **아래로 내리고**, `Math.floorMod` 는 **오른쪽 피연산자의 부호를 따라간다.**
- 마지막 행이 실무에서 가장 자주 물리는 자리다 — `-1 % 3` 은 `-1`, `Math.floorMod(-1, 3)` 은 `2`.\
  링 버퍼 인덱스·요일 계산에 `%` 를 쓰면 **음수 인덱스**가 나온다.

0으로 나눌 때도 정수와 부동소수가 갈린다(실행 출력 그대로).

```text
5.0 / 0   = Infinity
-5.0 / 0  = -Infinity
0.0 / 0.0 = NaN
5.5 % 2   = 1.5
-5.5 % 2  = -1.5
5 / 0     -> java.lang.ArithmeticException: / by zero
5 % 0     -> java.lang.ArithmeticException: / by zero
```

- **정수만 던진다.** 부동소수는 `Infinity`·`NaN` 이라는 값으로 흘러간다 — 예외가 없으니 **조용히 번진다.**
- `%` 도 같은 메시지 `/ by zero` 를 쓴다 — 메시지만 보고 `/` 인 줄 알면 엉뚱한 줄을 본다.

비용 — 정수 나눗셈은 곱셈보다 훨씬 비싸다(하드웨어 나눗셈). `floorDiv` 는 그 위에 보정 한 줄이다.

### (5) 시프트 — `>>` 는 부호를 끌고 가고 `>>>` 는 0을 채운다

**언제 쓰나** — 비트 마스크·해시 섞기·`(low+high)/2` 같은 중간값 계산.

```text
int n = -8                                     11111111111111111111111111111000

  n >> 1  (산술 시프트 — 맨 왼쪽 비트를 복제)      11111111111111111111111111111100  = -4
  n >>> 1 (논리 시프트 — 맨 왼쪽에 0)             01111111111111111111111111111100  = 2147483644
```

실행 결과 (JDK 21.0.5, 출력 그대로):

```text
n        = -8  11111111111111111111111111111000
n >> 1   = -4  11111111111111111111111111111100
n >>> 1  = 2147483644  01111111111111111111111111111100
p >> 1   = 4   00000000000000000000000000000100
p >>> 1  = 4   00000000000000000000000000000100

1 << 31  = -2147483648  10000000000000000000000000000000
1 << 32  = 1           00000000000000000000000000000001
1 << 33  = 2           00000000000000000000000000000010
1L << 32 = 4294967296
-1 >>> 28= 15
```

그림 해설 (한 단계씩):

- 양수면 `>>` 와 `>>>` 가 **같다.** 갈리는 것은 음수뿐이다.
- `1 << 32` 가 `0` 이 아니라 **`1`** 이다 — 시프트 거리는 `int` 면 하위 5비트(`& 31`), `long` 이면 하위 6비트(`& 63`)만 쓴다.\
  `32 & 31 == 0` 이라 **아무것도 안 민 것**이 된다. 이것도 JLS §15.19가 못박은 규칙이다.
- `1L << 32` 는 `long` 이므로 정상적으로 `4294967296` 이다 — **왼쪽 피연산자의 타입**이 거리 마스크를 정한다.

비용 — 시프트는 CPU 명령 하나다. 하지만 `x / 2` 를 `x >> 1` 로 바꾸는 "최적화"는 **음수에서 답이 달라진다**
(`-7 / 2 = -3` 이지만 `-7 >> 1 = -4`). JIT가 알아서 하니 직접 쓰지 않는다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 승격이 일어나지 않는 유일한 자리 — 상수 식

```java
byte b1 = 10, b2 = 20;
byte b3 = b1 + b2;          // error
byte fb = 10 + 20;          // OK — 컴파일 타임에 30 으로 접힌다
final char fc = 'A';
char c2 = fc + 1;           // OK — fc 가 상수 변수라 'B' 로 접힌다
char c = 'A';
char c3 = c + 1;            // error — c 는 상수 변수가 아니다
```

컴파일 에러는 이렇게 나온다(`javac` 출력 그대로, 21·25 동일).

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

> **상수 변수(constant variable)** — `final` 이고 컴파일 타임 상수로 초기화된 변수(JLS §4.12.4).\
> 예: `final int X = 10;` 은 상수 변수이고, `final int Y = args.length;` 는 아니다.

### 복합 대입 `+=` 에는 **보이지 않는 캐스트**가 들어 있다

```java
byte b = 100;
b += 300;      // 컴파일된다. 결과는 -112
byte c = 100;
c *= 2;        // 컴파일된다. 결과는 -56
```

실행 결과 (JDK 21.0.5):

```text
byte b=100; b += 300; -> -112
byte c=100; c *= 2;   -> -56
char ch='A'; ch += 1; -> B
int i=5; i /= 2;      -> 2
```

`javap -c` 가 그 캐스트를 보여 준다(출력 그대로).

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

- `E1 op= E2` 는 `E1 = (T)(E1 op E2)` 와 같다(JLS §15.26.2) — **`(T)` 캐스트가 언어 규칙으로 들어 있다.**
- 그래서 `b = b + 300` 은 컴파일 에러인데 `b += 300` 은 **컴파일되고 조용히 틀린다.**
- 축약형이 더 안전해 보이지만 **정반대다.**

### 연산자별 규칙 요약

| 식 | 결과 타입 | 주의할 점 |
|---|---|---|
| `byte`·`short`·`char` 끼리의 산술 | `int` | 원래 타입 변수에 다시 못 넣는다 |
| `int op int` | `int` | 넘치면 조용히 감긴다 |
| `int op long` | `long` | `int` 쪽이 먼저 `long` 으로 승격된다 |
| `int / int` | `int` | **0 쪽으로 절단**. `7/2 = 3`, `-7/2 = -3` |
| `int % int` | `int` | 부호는 **왼쪽** 피연산자를 따른다 |
| `int / 0` | — | `ArithmeticException: / by zero` |
| `double / 0` | `double` | `Infinity` — **예외 없음** |
| `x << n` / `x >> n` | `x` 의 승격 타입 | 거리는 `int` 면 `n & 31`, `long` 이면 `n & 63` |
| `x >>> n` | 〃 | `byte`·`short` 에 쓰면 **`int` 로 승격된 뒤** 밀린다 |
| `'A' + 1` | `int` | `char` 로 되돌리려면 캐스트가 필요하다 |
| `"" + 'A' + 'B'` | `String` | 왼쪽부터 평가 — `"AB"`. `'A' + 'B'` 는 `131` |

`char` 의 산술과 문자열 연결이 갈리는 자리 (실행 출력 그대로):

```text
'A' + 1      = 66
(char)('A'+1)= B
'A' + 'B'    = 131
"" + 'A' + 'B' = AB
1 + 2 + "x"  = 3x
"x" + 1 + 2  = x12
```

`byte` 에 `>>>` 를 쓰면 의도가 깨진다 (실행 출력 그대로):

```text
byte -8 >>> 1 = 2147483644
(byte)(sb >>> 1) = -4
```

- `byte` 가 먼저 `int` 로 **부호 확장**되어 `0xFFFFFFF8` 이 된 다음 논리 시프트가 걸린다.
- "바이트의 위쪽 비트를 0으로 채우고 싶다"면 `(b & 0xFF) >>> 1` 처럼 **마스크를 먼저** 씌워야 한다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 다 **에러 없이, 또는 엉뚱한 줄에서 터진다.**

### 1. 리터럴 곱셈이 `int` 에서 넘친다

```text
왼쪽 — 하루치                             오른쪽 — 하루를 마이크로초로
+---------------------------------+      +---------------------------------+
| long ms = 24*60*60*1000;        |      | long us = 24*60*60*1000*1000;   |
|                                 |      |                                 |
| 86400000  (int 에 들어간다)      |      | 진짜 값 86400000000             |
| -> 맞다                         |      | int 서랍에 잘려 500654080       |
| 테스트 초록                      |      | 그 뒤에 long 으로 늘려도 그대로  |
+---------------------------------+      +---------------------------------+
```

- 왼쪽 변수가 `long` 이어도 소용없다 — **곱셈은 이미 `int` 작업대에서 끝났다.**
- 고치는 법은 **한쪽을 `long` 리터럴로** 만드는 것뿐이다: `24L * 60 * 60 * 1000 * 1000`.
- 실행으로 확인: `24L*60*60*1000*1000 = 86400000000` / `(long)(24*60*60*1000*1000) = 500654080`.

### 2. 이진 탐색의 중간값

```java
int mid = (low + high) / 2;          // low, high 가 크면 넘친다
int safe1 = low + (high - low) / 2;  // 안전
int safe2 = (low + high) >>> 1;      // 안전 (감긴 비트를 논리 시프트로 되살린다)
```

실행 결과 (`big1 = big2 = 2_000_000_000`):

```text
(big1+big2)/2 = -147483648
(big1+big2)>>>1 = 2000000000
big1+(big2-big1)/2 = 2000000000
```

- `(low+high)/2` 가 **음수 인덱스**를 낸다 — 그 다음 줄에서 `ArrayIndexOutOfBoundsException` 이 나고,
  스택트레이스는 **배열 접근 줄**을 가리킨다. 진짜 원인은 그 윗줄이다.
- `>>>` 로 고치는 방법이 먹히는 이유는 **비트가 하나도 안 잘렸기 때문**이다.\
  `2,000,000,000 + 2,000,000,000 = 4,000,000,000` 은 32비트에 다 들어간다 — 다만 **최상위 비트가 1이라 `int` 가 부호로 읽어** 음수가 된다.\
  `>>>` 는 그 비트를 부호로 읽지 않고 그냥 밀어 내리므로 원래 합의 절반이 복원된다.\
  실행으로 확인: `4000000000` 의 이진수는 **32비트**(`11101110011010110010100000000000`)이고, `(big1+big2) = -294967296` 의 비트열과 같다.

### 3. `Math.abs` 가 음수를 돌려준다

```text
Math.abs(Integer.MIN_VALUE)   = -2147483648
```

- 절댓값 함수가 **음수를 반환한다.** 버그가 아니라 `int` 범위의 비대칭 때문이다.
- `Math.abs(hash) % buckets` 같은 코드는 **해시가 `MIN_VALUE` 일 때 음수 버킷**을 낸다.
- `Math.absExact` 를 쓰면 던진다: `ArithmeticException: Overflow to represent absolute value of Integer.MIN_VALUE`.
- `Math.floorMod(hash, buckets)` 로 바꾸면 **항상 양수**가 나온다.

### 4. 음수의 `%` 로 인덱스를 만든다

```text
왼쪽 — 양수만 들어올 때                   오른쪽 — 음수가 섞일 때
+---------------------------------+      +---------------------------------+
| int i = (cur + 1) % 3;          |      | int i = (cur - 1) % 3;          |
| cur = 2 -> i = 0                |      | cur = 0 -> i = -1               |
| 링 버퍼가 잘 돈다                |      | arr[-1] -> 예외                  |
| 테스트 초록                      |      | 운영에서만 터진다                |
+---------------------------------+      +---------------------------------+
```

- `%` 는 **왼쪽 부호를 따라가므로** 음수 입력에서 음수를 낸다.
- `Math.floorMod(cur - 1, 3)` 은 `2` 를 돌려준다 — **오른쪽 부호를 따라간다.**
- 실행으로 확인: `-1 % 3 = -1`, `Math.floorMod(-1, 3) = 2`.

### 5. `double` 로 돈을 센다

```text
0.1 + 0.2        = 0.30000000000000004
1.03 - 0.42      = 0.6100000000000001
0.1 + 0.2 == 0.3 = false
```

- 이것은 자바의 버그가 아니라 **2진 부동소수에 0.1이 정확히 없어서**다(표현 자체는
  [`data-representation/`](../../../../data-representation/) 가 정본).
- `==` 로 비교한 테스트가 통과했다면 **우연히 같은 오차가 난 것**이다.
- 금액은 `BigDecimal` 또는 **최소 단위 정수**(원 단위 `long`)로 센다 — [`../53-bigdecimal/`](../53-bigdecimal/).
- 다만 최소 단위 정수로 세면 **이 주제의 오버플로가 돌아온다** — `long` 이라도 무한하지 않다.

## 구현 세부사항 대 언어 보장

"이건 JVM 마음인가, 언어가 못박은 건가"를 가르는 절이다.

```text
     언어가 못박은 것                        구현이 고를 수 있는 것
  +---------------------------+          +---------------------------+
  | 정수는 2의 보수            |          | Math.sin·cos·pow 의        |
  | 오버플로는 감긴다(예외 없음)|          | 마지막 자리 (1 ulp 이내)   |
  | / 는 0 쪽으로 절단         |          |                           |
  | % 의 부호는 왼쪽을 따름     |          | Math 가 네이티브 명령을    |
  | 시프트 거리는 & 31 / & 63  |          | 쓸지 StrictMath 를 부를지  |
  +---------------------------+          +---------------------------+
   같은 소스는 어느 JVM 에서도             같은 소스가 CPU 에 따라
   같은 값을 낸다                          마지막 비트가 다를 수 있다
```

**언어 보장** — JLS §4.2.2 는 정수 연산에 대해 이렇게 쓴다(원문 인용).

> The integer operators do not indicate overflow or underflow in any way.

- 오버플로를 **알리지 않는 것이 명세**다. C의 부호 있는 정수 오버플로가 *정의되지 않은 동작*인 것과 다르다.\
  자바는 **감긴 값이 무엇인지까지** 정해 놓았으므로, 위의 `-2147483648` 은 모든 JVM에서 같다.
- 나눗셈의 절단 방향도 §15.17.2가 한 문장으로 못박았다 — 구현 재량이 아니다.

> Integer division rounds toward 0.

- `Integer.MIN_VALUE / -1` 이 예외를 안 내는 것까지 §15.17.2가 **특례로 적어 두었다**(원문 인용).

> There is one special case that does not satisfy this rule: if the dividend is the negative integer
> of largest possible magnitude for its type, and the divisor is `-1`, then integer overflow occurs
> and the result is equal to the dividend. Despite the overflow, no exception is thrown in this case.

  실행으로 확인: `Integer.MIN_VALUE / -1 = -2147483648` · `Integer.MIN_VALUE % -1 = 0`.

- 시프트 거리의 마스크도 §15.19가 값까지 적어 두었다 — `int` 면 `0x1f`, `long` 이면 `0x3f`.
- 그래서 **17·21·25에서 이 문서의 정수 출력이 한 글자도 다르지 않았다.** 실제로 셋 다 돌려 확인했다.

**구현 재량** — `Math` 클래스 javadoc이 스스로 밝힌다(JDK 21 소스 `Math.java` 원문).

> Unlike some of the numeric methods of class `StrictMath`, all implementations of the equivalent
> functions of class `Math` are not defined to return the bit-for-bit same results. This relaxation
> permits better-performing implementations where strict reproducibility is not required.

- `Math.sin` 등의 초월 함수는 **1 ulp 이내·준단조**까지만 요구한다.\
  비트까지 같아야 하면 `StrictMath` 를 쓴다.
- 반면 `Math.addExact`·`floorDiv`·`abs` 같은 **정수 메서드에는 이 재량이 없다** — 결과가 하나뿐이다.

> **ulp (unit in the last place)** — 부동소수 값의 마지막 비트 하나가 바뀔 때의 간격.\
> 예: "1 ulp 이내의 오차"는 정답 바로 옆 칸까지는 허용한다는 뜻이다.

**버전에 갈리는 것 두 가지** — 둘 다 실제로 확인했다.

1. **부동소수의 엄격 평가.** `strictfp` 로 선언하고 컴파일하면 세 JDK 모두 이렇게 경고한다(출력 그대로).

```text
Ex.java:1: warning: [strictfp] as of release 17, all floating-point expressions are evaluated strictly and 'strictfp' is not required
```

   컴파일러 자신이 "**릴리스 17부터는 모든 부동소수 식이 엄격하게 평가된다**"고 말한다.\
   17 이전에는 `strictfp` 없는 코드가 플랫폼에 따라 더 넓은 정밀도로 계산될 수 있었다.

2. **새 `Math` 메서드는 17에 없다.** 같은 소스가 17에서만 컴파일에 실패한다(출력 그대로).

```text
Ex.java:3: error: cannot find symbol
        System.out.println("Math.ceilDiv(7, 2)       = " + Math.ceilDiv(7, 2));
                                                               ^
  symbol:   method ceilDiv(int,int)
  location: class Math
```

   21·25에서는 돈다: `Math.ceilDiv(7,2) = 4` · `Math.ceilDiv(-7,2) = -3` ·
   `Math.divideExact(Integer.MIN_VALUE, -1) -> ArithmeticException: integer overflow`.\
   `MIN_VALUE / -1` 은 **연산자로는 조용히 감기지만**(`-2147483648`) `divideExact` 로는 던진다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 그냥 연산자 | `Math.*Exact` | `long`·`BigDecimal` |
|---|---|---|---|
| 루프 카운터·배열 인덱스 | 쓴다 | 과하다 | 과하다 |
| 금액·수량 누적 | 위험하다 | **쓴다** | 단위가 크면 `long` |
| 외부 입력을 곱하는 계산 | 위험하다 | **쓴다** | — |
| 밀리초·나노초 기간 | `int` 면 위험 | — | **`long` 을 쓴다** |
| 소수점이 있는 금액 | 못 쓴다 | — | **`BigDecimal`** |
| 해시 섞기·비트 마스크 | 쓴다 (감기는 게 정상) | 쓰면 안 된다 | — |
| 음수가 섞인 나머지 연산 | `%` 는 위험 | — | `Math.floorMod` |

판단 규칙 세 줄.

- **"이 값이 넘칠 리 없다"고 말할 수 있으면 연산자, 말 못 하면 `Math.*Exact`.**
- **감기는 것이 의도인 코드**(해시·체크섬·비트 연산)에는 `*Exact` 를 쓰면 안 된다 — 정상 동작이 예외가 된다.
- **음수가 들어올 수 있는 `%` 는 전부 `Math.floorMod` 후보다.**

## 핵심 문장

- `byte`·`short`·`char` 는 **연산 전에 `int` 로 승격**되고, 그래서 결과를 원래 타입 변수에 다시 넣을 수 없다.
- 정수 오버플로는 **예외도 경고도 없이 감긴다** — 그리고 그것이 JLS가 못박은 동작이다.
- `(long)(a * b)` 는 **이미 잘린 값을 늘린다.** 넓히려면 곱셈 전에 `(long) a * b` 로 해야 한다.
- `/` 는 0 쪽으로 자르고 `%` 는 왼쪽 부호를 따라간다 — 아래로 내리고 싶으면 `Math.floorDiv`/`floorMod`.
- `+=` 에는 언어 규칙으로 **축소 캐스트가 들어 있어서**, `b = b + 300` 은 에러인데 `b += 300` 은 조용히 틀린다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 02번)
- [`../../../../data-representation/`](../../../../data-representation/) — 진수·2의 보수·IEEE 754.\
  **경계: 그쪽은 「비트가 값을 어떻게 표현하나」까지, 여기는 「자바 연산자가 그 표현 위에서 무엇을 하나」부터다.**\
  `-8` 의 비트 패턴이 왜 `111...1000` 인지는 거기, `-8 >> 1` 이 왜 `-4` 인지는 여기.
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — 기본형과 래퍼.\
  **경계: 박싱·`Integer` 캐시·`==` 의 의미는 거기, 산술 연산의 타입 규칙은 여기.**\
  단 「이항 승격」의 정본은 이 문서다(01이 그렇게 넘겼다).
- [`../53-bigdecimal/`](../53-bigdecimal/) — `double` 로 돈을 세면 안 되는 이유의 정본
- [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/) — `'A' + 'B'` 가 `131` 이고 `"" + 'A' + 'B'` 가 `"AB"` 인 이유(문자열 연결)
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·JVM 내부. **나눗셈이 실제로 몇 사이클인지는 거기**
- [**05번 주제**](../05-arrays/)(배열) — 음수 인덱스가 실제로 터지는 자리

## 용어 풀이

- **이항 수치 승격** — 이항 연산의 두 피연산자를 공통 타입으로 맞추는 변환. `int` 보다 작은 타입은 전부 `int` 가 된다.
- **확대 변환(widening)** — 좁은 타입을 넓은 타입으로 바꾸는 것(`int` → `long`). 자동으로 일어난다.
- **축소 변환(narrowing)** — 넓은 타입을 좁은 타입으로 바꾸는 것(`int` → `byte`). 캐스트를 써야 하고 값이 잘릴 수 있다.
- **정수 오버플로** — 결과가 타입 범위를 넘어 위쪽 비트가 버려지는 것. 자바에서는 예외 없이 감긴다.
- **2의 보수** — 음수 표현 방식. `MAX_VALUE + 1` 이 `MIN_VALUE` 가 되는 이유.
- **절단(truncation)** — 나눗셈 결과의 소수부를 버리는 것. 자바는 **0 쪽으로** 버린다.
- **바닥 나눗셈(floor division)** — 결과를 **아래쪽으로** 내리는 나눗셈. `Math.floorDiv` 가 그것이다.
- **산술 시프트 `>>`** — 오른쪽으로 밀되 **맨 왼쪽 비트(부호)를 복제**해 채운다.
- **논리 시프트 `>>>`** — 오른쪽으로 밀되 **맨 왼쪽에 0**을 채운다. 자바에만 있는 연산자다.
- **상수 식·상수 변수** — 컴파일 타임에 값이 확정되는 식·변수. 축소 대입이 예외적으로 허용되는 조건.
- **복합 대입 연산자** — `+=`·`*=` 등. 언어 규칙상 **축소 캐스트를 포함**한다.
- **ulp** — 부동소수의 마지막 비트 한 칸의 간격. `Math` 의 오차 허용치 단위.
- **`i2l`·`i2b`·`iadd`·`imul`·`lmul`** — JVM 바이트코드 명령. `i`=int, `l`=long, `2`=to. 승격과 캐스트가 여기서 드러난다.

## 더 들어가면

- **`Math.floorMod` 는 `Math.floorDiv` 로 정의된다.** `a - floorDiv(a,b) * b` 와 같은 값이고,
  그래서 `floorMod` 의 부호가 `b` 를 따라간다.
- **`>>>` 가 자바에만 있는 이유**는 자바에 부호 없는 정수 타입이 없기 때문이다.\
  C는 `unsigned int` 를 `>>` 하면 논리 시프트가 되므로 연산자가 하나면 된다.\
  자바 8부터 `Integer.divideUnsigned`·`compareUnsigned`·`toUnsignedLong` 으로 부호 없는 해석을 **메서드로** 제공한다. *(이 메서드들은 안 돌려 봤다.)*
- **`Integer.MIN_VALUE / -1` 은 하드웨어 예외를 일으킬 수 있는 연산**이다(x86의 `idiv` 는 여기서 트랩을 낸다).\
  그런데 자바는 `-2147483648` 을 돌려주도록 명세돼 있어서, JVM이 그 경우를 따로 처리한다.\
  실행으로 확인: `Integer.MIN_VALUE / -1 = -2147483648`, `Integer.MIN_VALUE % -1 = 0`.
- **오버플로를 검사 없이 감지하는 관용구**로 `if (((x ^ r) & (y ^ r)) < 0)` 이 있다 —
  `Math.addExact` 의 JDK 구현이 실제로 이 형태다. 직접 쓸 이유는 없고, **`Math.addExact` 를 읽을 때 알아보면 된다.**
