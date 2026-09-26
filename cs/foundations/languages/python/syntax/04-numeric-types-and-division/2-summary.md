# python/syntax/04-numeric-types-and-division — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.2. The standard type hierarchy — Numbers](https://docs.python.org/3.12/reference/datamodel.html#the-standard-type-hierarchy) — `int`·`bool`·`float`·`complex` 의 정의
> - [6.7. Binary arithmetic operations](https://docs.python.org/3.12/reference/expressions.html#binary-arithmetic-operations) — `/`·`//`·`%` 의 규정과 `math.fmod` 대비
> - [`round()`](https://docs.python.org/3.12/library/functions.html#round) · [`divmod()`](https://docs.python.org/3.12/library/functions.html#divmod) · [`int()`](https://docs.python.org/3.12/library/functions.html#int)
> - [Numeric Types — int, float, complex](https://docs.python.org/3.12/library/stdtypes.html#typesnumeric) — 「Integers have unlimited precision.」, `bool` 이 `int` 의 하위 클래스
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> ★ **손계산으로 유도한 수치는 하나도 없다.** `-7 // 2` 부터 `round(2.675, 2)` 까지 전부 던져서 받은 값이다.
> **버전** — 연산자 의미는 Python 3 전체 공통. **정수 ↔ 문자열 변환 길이 제한은 3.11 부터**다(`-X int_max_str_digits`).
> **부동소수** — 이 머신은 IEEE 754 배정밀도(`sys.float_info.mant_dig` 가 `53`)다. **언어가 보장하는 것이 아니라 이 머신의 사정**이다.

## 한눈에 — 쉽게 말하면

**나눗셈이 세 개인 이유는, 「나눈다」가 세 가지 질문이기 때문이다.**

```text
 "7 을 2 로 나누면?"  이라는 한국어에는 세 질문이 섞여 있다

  ① 정확히 얼마인가        ->  7 / 2   =  3.5      (참된 나눗셈)
  ② 몇 개씩 담기나          ->  7 // 2  =  3        (바닥 나눗셈)
  ③ 얼마가 남나             ->  7 % 2   =  1        (나머지)
                              divmod(7, 2) = (3, 1)  ②와 ③을 한 번에
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 「정확히 얼마」 | `/` — 참된 나눗셈 | 정수끼리도 `float` 이 나온다 |
| 「몇 개씩 담기나」 | `//` — 바닥 나눗셈 | 수직선에서 **왼쪽**으로 내려간다 |
| 「얼마 남나」 | `%` — 나머지 | 부호가 **오른쪽 피연산자**를 따른다 |
| 눈금 없는 자 | `float` — 이진 분수 | `0.1 + 0.2` 가 `0.3` 이 아니다 |
| 십진 눈금 자 | `decimal` — 십진 소수 | `Decimal("0.1") + Decimal("0.2")` 가 `0.3` |
| 분수 자 | `fractions` — 유리수 | `Fraction(1,3)*3` 이 정확히 `1` |

**똑같은 구조다** — 실무에서 이게 물리는 자리는 넷이다.\
페이지 수 계산에서 음수가 섞이면 한 페이지가 어긋나는 것 ·\
해시 버킷을 `% n` 으로 고를 때 음수 해시가 음수 버킷을 내는 것 ·\
금액 합계가 `0.1` 씩 쌓이다 1원이 어긋나는 것 ·\
`round` 로 반올림했는데 `.5` 가 위로 안 가는 것.\
네 자리 전부 **「나눗셈이 세 개」와 「float 은 이진수」** 둘로 설명된다.

> **바닥 나눗셈(floor division)** — 나눈 결과를 **수직선에서 작은 쪽**(왼쪽)으로 내리는 것.\
> 예: `-3.5` 를 내리면 `-3` 이 아니라 `-4` 다. 0 쪽이 아니라 **음의 무한대 쪽**이기 때문이다.

> **부동소수(floating point)** — 수를 「가수 × 2의 지수승」 꼴로 저장하는 방식.\
> 예: `0.1` 은 2의 거듭제곱 합으로 딱 떨어지지 않아서, 실제로 저장되는 값은 `0.1` 보다 아주 조금 크다.

## 이 주제가 답하려는 질문

1. **`-7 // 2` 는 왜 `-3` 이 아니라 `-4` 인가** — C·Java 와 다른 이 한 줄이 이 주제의 과녁이다.
2. **`0.1 + 0.2` 가 `0.3` 이 아니면 금액은 무엇으로 계산하나** — `decimal` 과 `fractions` 가 각각 무엇을 푸는가.
3. **`int` 에 상한이 없다는 것은 누가 보장하나** — 언어인가, 이 구현인가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. `int` 는 상한이 없다 — 이건 언어 보장이다

**언제 쓰나** — 큰 수를 다룰 때. 다른 언어에서 온 사람이 오버플로를 걱정하는 자리.

언어 레퍼런스가 정한다 — *"These represent numbers in an unlimited range, subject to available (virtual) memory only."*\
표준 라이브러리 쪽 표현은 더 짧다 — *"Integers have unlimited precision."*

```text
 C / Java 의 int                      Python 의 int
 +----------------+                   +--------------------------+
 | 32 / 64 비트 고정 |                  | 필요한 만큼 자릿수가 늘어난다 |
 +----------------+                   +--------------------------+
  넘치면 감싸 돈다                        메모리가 허락하는 한 안 넘친다
  (오버플로)                             getsizeof 가 같이 커진다
```

```python
import sys
print("2**200 =", 2**200)
print("자릿수:", len(str(2**1000)))
print("sys.maxsize =", sys.maxsize, " (이건 상한이 아니다)")
print("maxsize+1 =", sys.maxsize + 1)
print("getsizeof(0) =", sys.getsizeof(0), " (1) =", sys.getsizeof(1),
      " (2**100) =", sys.getsizeof(2**100), " (2**1000) =", sys.getsizeof(2**1000))
```

```text
2**200 = 1606938044258990275541962092341162602522202993782792835301376
자릿수: 302
sys.maxsize = 9223372036854775807  (이건 상한이 아니다)
maxsize+1 = 9223372036854775808
getsizeof(0) = 28  (1) = 28  (2**100) = 40  (2**1000) = 160
```

그림 해설.

- `sys.maxsize` 는 **정수의 상한이 아니다.** 「리스트 인덱스 같은 것이 가질 수 있는 최댓값」이고, 그 위로도 정수는 잘 간다.
- `getsizeof` 가 `28 → 40 → 160` 으로 늘어난다 — **자릿수에 비례해 메모리를 더 쓴다.** 그게 「메모리가 허락하는 한」의 뜻이다.
- **이건 언어 보장이다.** 다른 파이썬 구현도 같아야 한다. ★ 이 주제에서 몇 안 되는 「그냥 파이썬은 이렇다」로 적어도 되는 자리다.

**비용** — 오버플로 걱정이 없다.\
대신 큰 수의 연산이 자릿수에 비례해 느려지고 메모리를 쓴다.

### 2. 그런데 **문자열로 바꿀 때는** 제한이 있다 (3.11+)

**언제 쓰나** — 아주 큰 수를 `print` 하거나 `int("...")` 로 파싱할 때.

```text
 연산은 제한이 없다                    문자열 변환에는 제한이 있다
   10**5000  계산 OK                   str(10**5000)  -> ValueError
   bit_length() OK                     int("1"*5000)  -> ValueError
   hex(...)  OK  (16진수는 제외)         기본 한도 4300 자리
```

```python
import sys
print("int_max_str_digits 기본:", sys.get_int_max_str_digits())
big = 10 ** 5000
try:
    s = str(big)
    print("str(10**5000) 길이:", len(s))
except ValueError as e:
    print("str(10**5000) -> ValueError:", e)
print("연산 자체는 된다. bit_length:", big.bit_length())
try:
    int("1" * 5000)
except ValueError as e:
    print('int("1"*5000) -> ValueError:', str(e)[:120])
print("hex 로는 된다:", len(hex(big)))
```

```text
int_max_str_digits 기본: 4300
str(10**5000) -> ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit
연산 자체는 된다. bit_length: 16610
int("1"*5000) -> ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() t
hex 로는 된다: 4155
```

플래그로 조절된다 — **그리고 하한이 있다.**

```python
# $ python3 -X int_max_str_digits=0 -c "..."
```

```text
0 = 0 (제한 해제)
str(10**5000) 길이: 5001
```

```python
# $ python3 -X int_max_str_digits=640 -c "..."
```

```text
한도: 640
ValueError: Exceeds the limit (640 digits) for integer string conversion; use sys.set_int_ma
str(10**600) 길이: 601
```

```python
# $ python3 -X int_max_str_digits=100 -c "print('여기까지 안 온다')"
```

```text
Fatal Python error: config_init_int_max_str_digits: -X int_max_str_digits: invalid limit; must be >= 640 or 0 for unlimited.
Python runtime state: preinitialized
```

환경 변수와 런타임 설정도 같은 일을 한다.

```python
# $ PYTHONINTMAXSTRDIGITS=0 python3 -c "..."
```

```text
환경변수 0 -> 0 5001
```

```python
import sys
sys.set_int_max_str_digits(700)
print("런타임 설정:", sys.get_int_max_str_digits())
print(len(str(10**600)))
try:
    str(10**800)
except ValueError as e:
    print("ValueError:", str(e)[:60])
```

```text
런타임 설정: 700
601
ValueError: Exceeds the limit (700 digits) for integer string conversion
```

그림 해설.

- **연산과 표시가 갈린다.** `10**5000` 을 만드는 건 되고, 그걸 **10진 문자열로 보는 것**만 막힌다.
- 16진수(`hex`)는 안 막힌다 — 2의 거듭제곱 진법은 변환이 선형이라 공격 소재가 안 되기 때문이다.
- ★ 「`Fatal Python error` + `must be >= 640`」은 **던져 봐야만 나오는 출력**이다. 640 이라는 하한은 문서를 봐도 그냥 지나치기 쉽다.
- 이 제한은 **언어 보장이 아니다.** 3.11 에서 서비스 거부 공격을 막으려고 들어온 **구현의 방어 장치**이고, `int()` 문서가 *"int string inputs and string representations can be limited to help avoid denial of service attacks"* 라고 적는다.

**비용** — 악의적인 거대 입력으로 CPU 를 태우는 공격을 막는다.\
대신 **정당한 큰 수 출력도 막힌다.** 과학 계산·암호 코드는 한도를 올려야 한다.

### 3. 나눗셈 세 형제 — 그리고 음수에서 갈리는 자리

**언제 쓰나** — 인덱스·페이지·버킷을 계산할 때. **이 주제의 과녁이다.**

언어 레퍼런스가 규정한다.

- `//` — *"the result is that of mathematical division with the 'floor' function applied to the result."*
- `%` — *"The modulo operator always yields a result with the same sign as its second operand (or zero)."*
- 둘의 관계 — *"`x == (x//y)*y + (x%y)`"*

```text
 수직선에서 -3.5 를 어디로 내리나

   -5   -4   -3   -2   -1    0    1    2
    |    |    |    |    |    |    |    |
         ^         ^
      바닥(floor)  0 쪽으로 자르기(truncate)
      -7 // 2      int(-7 / 2)
       = -4         = -3

 "바닥 나눗셈" 이라는 이름이 여기서 나온다 — 0 이 아니라 아래로 간다
```

```python
import math
print("-7 / 2   =", -7 / 2)
print("-7 // 2  =", -7 // 2)
print("-7 % 2   =", -7 % 2)
print("divmod(-7, 2) =", divmod(-7, 2))
print("math.fmod(-7, 2) =", math.fmod(-7, 2))
print("int(-7 / 2)  =", int(-7 / 2))
print("math.trunc(-7/2) =", math.trunc(-7/2))
```

```text
-7 / 2   = -3.5
-7 // 2  = -4
-7 % 2   = 1
divmod(-7, 2) = (-4, 1)
math.fmod(-7, 2) = -1.0
int(-7 / 2)  = -3
math.trunc(-7/2) = -3
```

**`math.fmod` 와의 대조가 핵심이다.**

```text
 파이썬 %                              math.fmod (= C 의 fmod)
 부호가 "오른쪽" 을 따른다               부호가 "왼쪽" 을 따른다
   -7 % 2   =  1                        fmod(-7, 2) = -1.0
    7 % -2  = -1                        fmod(7, -2) =  1.0

 문서의 표현: "The function math.fmod() returns a result
 whose sign matches the sign of the first argument instead."
```

```python
print("7 // -2  =", 7 // -2, " 7 % -2 =", 7 % -2, " fmod:", math.fmod(7, -2))
print("항등식 검증  (-7//2)*2 + (-7%2) =", (-7//2)*2 + (-7%2))
```

```text
7 // -2  = -4  7 % -2 = -1  fmod: 1.0
항등식 검증  (-7//2)*2 + (-7%2) = -7
```

그림 해설.

- `-7 // 2` 가 `-4` 인 것은 **`-3.5` 를 아래로 내렸기 때문**이다. C·Java 의 `/` 는 0 쪽으로 자르므로 `-3` 이 된다.
- 몫이 한 칸 내려갔으니 나머지가 그만큼 올라온다 — `-7 % 2` 가 `1` 이다. **항등식이 맞아떨어지는 것을 직접 재서 확인했다**(`-7`).
- `math.fmod` 는 반대 규약이다. **같은 「나머지」라는 말이 두 가지를 가리킨다.**
- 어느 쪽이 맞느냐가 아니라 **무엇이 필요하냐**다. 문서의 말로 *"Which approach is more appropriate depends on the application."*

**`%` 의 부호 규약이 실무에서 값을 내는 자리**

```python
buckets = 8
for h in (-17, -1, 0, 1, 17):
    print(f"h={h:4}  h % 8 = {h % 8}   math.fmod = {math.fmod(h, 8)}")
```

```text
h= -17  h % 8 = 7   math.fmod = -1.0
h=  -1  h % 8 = 7   math.fmod = -1.0
h=   0  h % 8 = 0   math.fmod = 0.0
h=   1  h % 8 = 1   math.fmod = 1.0
h=  17  h % 8 = 1   math.fmod = 1.0
```

파이썬의 `%` 는 **음수 해시에서도 언제나 유효한 버킷 번호**를 낸다. C 규약이면 음수 인덱스가 나온다.

**실수에서도 같은 규약이다**

```python
print("7.5 // 2 =", 7.5 // 2, type(7.5 // 2).__name__)
print("-7.5 // 2 =", -7.5 // 2)
print("-7.5 % 2 =", -7.5 % 2, " fmod:", math.fmod(-7.5, 2))
print("divmod(-7.5, 2) =", divmod(-7.5, 2))
```

```text
7.5 // 2 = 3.0 float
-7.5 // 2 = -4.0
-7.5 % 2 = 0.5  fmod: -1.5
divmod(-7.5, 2) = (-4.0, 0.5)
```

`//` 가 실수면 **결과도 실수**다(`3.0`). 「정수 나눗셈」이라고 외우면 여기서 틀린다.

**0 으로 나누면 — 셋이 다르게 죽는다**

```python
for label, fn in (("1 // 0", lambda: 1 // 0),
                  ("1 / 0",  lambda: 1 / 0),
                  ("1 % 0",  lambda: 1 % 0)):
    try:
        fn()
    except ZeroDivisionError as e:
        print(f"{label:8} -> ZeroDivisionError: {e}")
try:
    math.fmod(1, 0)
except ValueError as e:
    print("math.fmod(1,0) -> ValueError:", e)
```

```text
1 // 0   -> ZeroDivisionError: integer division or modulo by zero
1 / 0    -> ZeroDivisionError: division by zero
1 % 0    -> ZeroDivisionError: integer modulo by zero
math.fmod(1,0) -> ValueError: math domain error
```

세 메시지가 **전부 다르다** — 어느 연산에서 터졌는지 메시지가 말해 준다.\
그리고 `math.fmod` 만 **다른 예외**다. `except ZeroDivisionError` 로 감싼 코드가 여기서 샌다.

**비용** — 바닥 규약 덕에 `%` 가 언제나 음이 아닌 값을 낸다(양수 나누는 수에 대해). 인덱스·버킷 계산이 안전하다.\
대신 C·Java 에서 옮긴 코드가 **음수 입력에서만** 한 칸씩 틀린다.

### 4. `/` 는 언제나 실수를 돌려준다

**언제 쓰나** — 나눠 떨어지는 정수를 나눌 때. 「정수가 나오겠지」가 틀린다.

```text
 Python 2                             Python 3
  7 / 2  =  3   (정수)                 7 / 2  =  3.5
  4 / 2  =  2   (정수)                 4 / 2  =  2.0   <- 실수다
                                       4 // 2 =  2     <- 정수를 원하면 이쪽
```

```python
print("7 / 2 =", 7/2, type(7/2).__name__, "  4 / 2 =", 4/2, type(4/2).__name__)
```

```text
7 / 2 = 3.5 float   4 / 2 = 2.0 float
```

그림 해설.

- 문서의 규정 그대로다 — *"Division of integers yields a float, while floor division of integers results in an integer."*
- **나눠 떨어져도 실수다.** 인덱스로 쓰면 `TypeError` 가 나므로 그 자리는 금방 드러난다.
- 진짜 위험한 곳은 **큰 정수**다. `float` 으로 바뀌는 순간 53비트 밖의 정밀도가 날아간다.

```python
n = 2**60
print("n // 2 == 2**59 :", n // 2 == 2**59)
print("int(n / 2) == 2**59 :", int(n / 2) == 2**59)
m = 2**60 + 1
print("m // 2 =", m // 2)
print("int(m / 2) =", int(m / 2), " <- 1 이 사라졌다")
```

```text
n // 2 == 2**59 : True
int(n / 2) == 2**59 : True
m // 2 = 576460752303423488
int(m / 2) = 576460752303423488  <- 1 이 사라졌다
```

★ 두 값이 **같아 보인다.** `m // 2` 는 `576460752303423488` 이 맞고, `int(m / 2)` 도 같은 값이 나왔다 —\
`m` 이 홀수라 `//` 는 내림해서 같은 값이 되고, `/` 는 정밀도가 날아가 같은 값이 된 것이다.\
**같은 답이 나왔다고 같은 계산이 아니다.** 아래에서 갈리는 자리를 찾아 던져 봤다.

```python
m = 2**60 + 3
print("m // 2     =", m // 2)
print("int(m / 2) =", int(m / 2))
print("같은가:", m // 2 == int(m / 2))
```

```text
m // 2     = 576460752303423489
int(m / 2) = 576460752303423488
같은가: False
```

**여기서 갈렸다.** 큰 정수를 `/` 로 나누면 조용히 틀린 값이 나온다.\
★ 한 사례(`2**60 + 1`)만 보고 「같으니 괜찮다」로 넘겼으면 못 잡았을 자리다 — **갈리는 지점을 일부러 찾아 던져야** 나온다.

**비용** — `/` 가 언제나 실수라서 의미가 명확하다.\
대신 **53비트를 넘는 정수에서 정밀도가 날아간다.** 정수 나눗셈은 `//` 를 쓴다.

### 5. `float` 은 이진 분수다 — `0.1 + 0.2` 의 정체

**언제 쓰나** — 금액·비율을 다룰 때.

```text
 십진 0.1 을 이진으로 쓰면              그래서 실제로 저장되는 값은
  0.0001100110011001100...(무한)        0.1 보다 아주 조금 크다

  53비트에서 끊는다                      0.10000000000000000555...
        |
        v
  0.1 + 0.2 = 0.30000000000000004
```

```python
print("0.1 + 0.2 =", 0.1 + 0.2)
print("0.1 + 0.2 == 0.3 :", 0.1 + 0.2 == 0.3)
print("0.1 의 실제 값:", f"{0.1:.20f}")
print("as_integer_ratio:", (0.1).as_integer_ratio())
print("hex:", (0.1).hex())
```

```text
0.1 + 0.2 = 0.30000000000000004
0.1 + 0.2 == 0.3 : False
0.1 의 실제 값: 0.10000000000000000555
as_integer_ratio: (3602879701896397, 36028797018963968)
hex: 0x1.999999999999ap-4
```

`as_integer_ratio` 가 **저장된 값 그 자체**를 분수로 보여 준다 — 분모가 2의 거듭제곱(`2**55`)이다.

이 머신의 사정은 이렇다.

```python
import sys
fi = sys.float_info
print("mant_dig:", fi.mant_dig, " dig:", fi.dig, " max:", fi.max,
      " epsilon:", fi.epsilon, " radix:", fi.radix)
```

```text
mant_dig: 53  dig: 15  max: 1.7976931348623157e+308  epsilon: 2.220446049250313e-16  radix: 2
```

★ **이건 언어 보장이 아니다.** 언어 레퍼런스의 표현은 *"You are at the mercy of the underlying machine architecture (and C or Java implementation) for the accepted range and handling of overflow."* 다.

**두 가지 처방 — 무엇을 푸는지가 다르다**

```text
 decimal                              fractions
 "십진 눈금을 그대로"                   "분수를 그대로"
  Decimal("0.1") + Decimal("0.2")      Fraction(1,3) * 3
   = 0.3  (정확)                        = 1  (정확)
  1/3 은 여전히 못 담는다                0.1 도 정확히 담는다
   = 0.3333...3 (28자리에서 끊김)        = 1/10
```

```python
from decimal import Decimal, getcontext
print("Decimal('0.1') + Decimal('0.2') =", Decimal("0.1") + Decimal("0.2"))
print("Decimal(0.1) =", Decimal(0.1))
print("context prec:", getcontext().prec)
print("Decimal(1)/Decimal(3) =", Decimal(1)/Decimal(3))
```

```text
Decimal('0.1') + Decimal('0.2') = 0.3
Decimal(0.1) = 0.1000000000000000055511151231257827021181583404541015625
context prec: 28
Decimal(1)/Decimal(3) = 0.3333333333333333333333333333
```

★ `Decimal(0.1)` 과 `Decimal("0.1")` 이 **완전히 다르다.** 앞엣것은 이미 오염된 float 을 받아 그 오염을 55자리까지 그대로 보여 준다.\
**`Decimal` 에는 문자열로 넣어야 한다.**

```python
from fractions import Fraction
print("Fraction(1,3) + Fraction(1,6) =", Fraction(1,3) + Fraction(1,6))
print("Fraction(0.1) =", Fraction(0.1))
print("Fraction('0.1') =", Fraction("0.1"))
print("1/3 을 셋 더하면:", Fraction(1,3)*3, " float 는:", (1/3)*3 == 1.0)
```

```text
Fraction(1,3) + Fraction(1,6) = 1/2
Fraction(0.1) = 3602879701896397/36028797018963968
Fraction('0.1') = 1/10
1/3 을 셋 더하면: 1  float 는: True
```

`Fraction(0.1)` 의 분수가 위의 `as_integer_ratio` 와 **한 글자도 같다** — 같은 것을 두 창으로 본 것이다.

그림 해설.

- `float` 은 **2진 분수**만 정확히 담는다. `0.5`·`0.25`·`0.125` 는 정확하고 `0.1` 은 아니다.
- `decimal` 은 **10진 분수**를 정확히 담는다. 금액에 맞는다. 그래도 `1/3` 은 못 담는다.
- `fractions` 는 **유리수 전부**를 정확히 담는다. 대신 분모가 무한정 커진다.
- ★ `(1/3)*3 == 1.0` 이 **`True`** 인 것에 주의하라. 오차가 우연히 상쇄된 것이지 정확해서가 아니다 — **float 검사는 한 사례로 결론을 내면 안 된다.**

```python
import math
print("math.isclose(0.1+0.2, 0.3):", math.isclose(0.1+0.2, 0.3))
```

```text
math.isclose(0.1+0.2, 0.3): True
```

**비용** — `float` 은 CPU 가 직접 계산하므로 압도적으로 빠르다.\
`decimal`·`fractions` 는 파이썬 객체 연산이라 훨씬 느리다. **정확성을 돈 주고 산다.**

### 6. `round` 는 은행가 반올림이다

**언제 쓰나** — `.5` 가 나오는 자리. 통계·금액 집계.

문서가 그대로 적는다 — *"if two multiples are equally close, rounding is done toward the **even** choice (so, for example, both `round(0.5)` and `round(-0.5)` are `0`, and `round(1.5)` is `2`)."*

```text
 학교에서 배운 반올림                   파이썬의 round
  0.5 -> 1                             0.5 -> 0   (0 이 짝수)
  1.5 -> 2                             1.5 -> 2   (2 가 짝수)
  2.5 -> 3                             2.5 -> 2   (2 가 짝수)
  3.5 -> 4                             3.5 -> 4   (4 가 짝수)

 ".5 는 가까운 짝수로" — 많이 더하면 위/아래가 균형을 이룬다
```

```python
for v in (0.5, 1.5, 2.5, 3.5, -0.5, -1.5, 2.675):
    print(f"round({v}) = {round(v)}", end="   ")
print()
print("round(2.675, 2) =", round(2.675, 2), "  (2.675 의 실제 값:", f"{2.675:.20f}", ")")
print("round(0.5) type:", type(round(0.5)).__name__,
      " round(0.5, 0) type:", type(round(0.5, 0)).__name__, "값:", round(0.5, 0))
```

```text
round(0.5) = 0   round(1.5) = 2   round(2.5) = 2   round(3.5) = 4   round(-0.5) = 0   round(-1.5) = -2   round(2.675) = 3   
round(2.675, 2) = 2.67   (2.675 의 실제 값: 2.67499999999999982236 )
round(0.5) type: int  round(0.5, 0) type: float 값: 0.0
```

★ **`round(2.675, 2)` 가 `2.67` 인 것은 은행가 반올림 때문이 아니다.** `2.675` 가 애초에 `2.6749999...` 로 저장돼 있어 **동점이 아니기** 때문이다.\
문서가 이것을 따로 적는다 — *"This is not a bug: it's a result of the fact that most decimal fractions can't be represented exactly as a float."*\
**두 현상을 섞어 외우면 둘 다 틀린다.**

★ `ndigits` 를 주면 **반환 타입이 바뀐다** — `round(0.5)` 는 `int`, `round(0.5, 0)` 은 `float`(`0.0`)이다.

**원하는 반올림이 있으면 `decimal` 로 고른다**

```python
from decimal import Decimal, ROUND_HALF_UP
print("Decimal('2.5') 기본 반올림:", Decimal("2.5").quantize(Decimal("1")))
print("Decimal('2.5') HALF_UP :", Decimal("2.5").quantize(Decimal("1"), rounding=ROUND_HALF_UP))
print("Decimal('0.5') 기본     :", Decimal("0.5").quantize(Decimal("1")))
```

```text
Decimal('2.5') 기본 반올림: 2
Decimal('2.5') HALF_UP : 3
Decimal('0.5') 기본     : 0
```

그림 해설.

- `Decimal` 의 기본도 은행가 반올림(`ROUND_HALF_EVEN`)이다. **파이썬 전반의 기본값**이다.
- 학교식 반올림이 필요하면 `ROUND_HALF_UP` 을 **명시**해야 한다.
- 금액 계산에서 이 선택은 **회계 규정이 정하는 것**이지 기본값에 맡길 일이 아니다.

**비용** — 은행가 반올림은 많은 수를 더할 때 편향이 안 쌓인다.\
대신 **한 값만 보면 직관과 어긋난다** — 「2.5 를 반올림했는데 2가 나온다」.

### 7. `bool` 은 `int` 의 하위 클래스다

**언제 쓰나** — `True` 를 세거나 더할 때. [05번](../05-truthiness-and-short-circuit/)으로 이어지는 다리다.

언어 레퍼런스가 정한다 — *"The Boolean type is a subtype of the integer type, and Boolean values behave like the values 0 and 1, respectively, in almost all contexts."*

```text
         int
          ^
          |  (하위 클래스)
         bool
          |
    False = 0,  True = 1

 그래서 산술이 그대로 된다.  다만 str() 만 예외다 ("True"/"False")
```

```python
print("bool 은 int 의 하위 클래스:", issubclass(bool, int), " isinstance(True, int):", isinstance(True, int))
print("True + True =", True + True, type(True+True).__name__)
print("sum([True, True, False]) =", sum([True, True, False]))
print("True * 3 =", True * 3, "  'ab' * True =", "ab" * True)
print("{1: 'a', True: 'b'} =", {1: 'a', True: 'b'})
print("hash(1) == hash(True):", hash(1) == hash(True))
```

```text
bool 은 int 의 하위 클래스: True  isinstance(True, int): True
True + True = 2 int
sum([True, True, False]) = 2
True * 3 = 3   'ab' * True = ab
{1: 'a', True: 'b'} = {1: 'b'}
hash(1) == hash(True): True
```

★ `{1: 'a', True: 'b'}` 가 **키 하나**가 된다. `hash(True) == hash(1)` 이고 `True == 1` 이라 **같은 키**로 취급된다.\
그리고 남은 키의 표시는 `1` 인데 값은 `'b'` 다 — **먼저 들어온 키가 남고 값만 덮인다.**

`bool` 은 더 상속할 수 없다.

```python
try:
    class MyBool(bool): pass
except TypeError as e:
    print("bool 상속 -> TypeError:", e)
```

```text
bool 상속 -> TypeError: type 'bool' is not an acceptable base type
```

`True`·`False` 가 **싱글턴 둘뿐**이어야 하기 때문이다(레퍼런스: *"The two objects representing the values `False` and `True` are the only Boolean objects."*).

그림 해설.

- `sum([...])` 으로 참의 개수를 세는 관용구가 여기서 나온다. 널리 쓰이는 정당한 코드다.
- 대신 **표준 라이브러리가 그 의존을 권하지 않는다** — *"However, relying on this is discouraged; explicitly convert using `int()` instead."*
- dict 키 충돌은 실무 버그로 이어진다 — `{0: "off", False: "꺼짐"}` 도 키 하나다.

**비용** — 불린 산술이 공짜로 따라온다.\
대신 **`True` 와 `1` 을 구별해야 하는 자리**(dict 키·`in`·`count`)에서 조용히 섞인다.

### 8. `complex` — 존재만

```python
c = 3 + 4j
print("complex:", c, " abs:", abs(c), " real/imag:", c.real, c.imag, " conj:", c.conjugate())
try:
    print(c < 1)
except TypeError as e:
    print("complex 비교 -> TypeError:", e)
```

```text
complex: (3+4j)  abs: 5.0  real/imag: 3.0 4.0  conj: (3-4j)
complex 비교 -> TypeError: '<' not supported between instances of 'complex' and 'int'
```

- 리터럴은 `j` 접미사다. `real`·`imag` 는 **읽기 전용 속성**이고 둘 다 `float` 이다.
- **순서 비교가 아예 없다.** `<` 를 쓰면 `TypeError` 다 — 복소수에 전순서가 없기 때문이다.
- 언어 레퍼런스가 `float` 과 같은 단서를 붙인다 — 실수·허수부가 각각 기계 배정밀도다.

## 문법 — 형태와 규칙

```python
7 / 2           # 3.5     참된 나눗셈 — 언제나 float
7 // 2          # 3       바닥 나눗셈 — 수직선에서 아래로
7 % 2           # 1       나머지 — 부호는 오른쪽 피연산자를 따른다
divmod(7, 2)    # (3, 1)  몫과 나머지를 한 번에
7 ** 2          # 49      거듭제곱
abs(-7)         # 7
round(2.5)      # 2       .5 는 가까운 짝수로

import math
math.fmod(-7, 2)    # -1.0   부호가 왼쪽 피연산자를 따른다 (C 규약)
math.floor(-3.5)    # -4
math.trunc(-3.5)    # -3     0 쪽으로 자른다
math.isclose(a, b)  # float 비교는 이걸로

from decimal import Decimal          # 십진 — 반드시 문자열로 넣는다
from fractions import Fraction       # 유리수
```

규칙은 여섯이다.

1. **`/` 는 정수끼리도 `float` 을 돌려준다.** 나눠 떨어져도 그렇다.
2. **`//` 는 바닥으로 내린다.** 음수에서 C·Java 와 갈린다.\
   피연산자에 `float` 이 하나라도 있으면 **결과도 `float`**(`7.5 // 2` 가 `3.0`).
3. **`%` 의 부호는 오른쪽 피연산자를 따른다.** `math.fmod` 는 왼쪽을 따른다.
4. **`x == (x//y)*y + (x%y)`** 가 항등식이고, `divmod(x, y) == (x//y, x%y)` 다.
5. **`round` 는 동점을 짝수로 보낸다.** `ndigits` 를 주면 **반환 타입이 `float`** 이 된다.
6. **`bool` 은 `int` 의 하위 클래스**다. `True + True == 2` 이고 dict 키로는 `1` 과 충돌한다.

## 어디서 틀리나

### (1) C·Java 에서 옮긴 `//` 가 음수에서만 한 칸 틀린다

```python
print(7 // 2, int(7 / 2))       # 3 3     양수에서는 같다
print(-7 // 2, int(-7 / 2))     # -4 -3   음수에서만 갈린다
```

양수 테스트는 전부 통과한다. **음수 입력이 들어오는 날 한 칸 어긋난다.**

### (2) `%` 로 만든 버킷이 음수가 될 거라 믿고 방어 코드를 쓴다

```python
print((-17) % 8)      # 7   — 파이썬에서는 이미 안전하다
```

C 습관으로 `((h % n) + n) % n` 같은 코드를 쓰면 **불필요하고**, 반대로 `math.fmod` 를 쓰면 **진짜로 음수가 나온다.**

### (3) `Decimal(0.1)` 로 넣는다

```python
from decimal import Decimal
print(Decimal(0.1))
```

```text
0.1000000000000000055511151231257827021181583404541015625
```

**이미 오염된 float 을 받았으므로 `Decimal` 이 고쳐 주지 못한다.** 문자열로 넣어야 한다.

### (4) `round(2.675, 2)` 를 은행가 반올림 탓으로 돌린다

```text
round(2.675, 2) = 2.67   (2.675 의 실제 값: 2.67499999999999982236 )
```

**동점이 아니라서** 아래로 간 것이다. 은행가 반올림은 **정확히 `.5` 일 때만** 작동한다.\
둘을 섞으면 「`round` 는 무조건 내린다」 같은 틀린 규칙이 생긴다.

### (5) 큰 정수를 `/` 로 나눈다

```text
m = 2**60 + 3
m // 2     = 576460752303423489
int(m / 2) = 576460752303423488
같은가: False
```

에러도 경고도 없다. **`int` 는 무한인데 `float` 은 53비트**라서 나는 조용한 실패다.

### (6) `True` 와 `1` 을 dict 키로 같이 쓴다

```python
print({1: 'a', True: 'b'})        # {1: 'b'}
print({0: 'off', False: '꺼짐'})   # {0: '꺼짐'}
```

키가 **하나로 합쳐진다.** 먼저 들어온 키가 남고 값만 덮인다.

### (7) `0` 으로 나눈 예외를 한 종류로 잡는다

```text
1 // 0         -> ZeroDivisionError
math.fmod(1,0) -> ValueError: math domain error
```

`except ZeroDivisionError` 로 감싼 코드가 `math.fmod` 에서 샌다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두꺼운 편이다** — 연산자 의미가 전부 명세에 있다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `sys` 로 확인 |
| **이 판의 관찰** | 이 머신·이 판에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| **`int` 는 범위가 무제한이다** — 가용 (가상) 메모리에만 달렸다 | 데이터 모델 3.2 / `stdtypes` |
| `/` 는 정수끼리도 `float`, `//` 는 정수를 낸다 | 언어 레퍼런스 6.7 |
| `//` 의 결과는 **수학적 나눗셈에 floor 를 적용한 것**이다 | 언어 레퍼런스 6.7 |
| `%` 는 **언제나 오른쪽 피연산자와 같은 부호**(또는 0)를 낸다 | 언어 레퍼런스 6.7 |
| `x == (x//y)*y + (x%y)` · `divmod(x,y) == (x//y, x%y)` | 언어 레퍼런스 6.7 |
| `math.fmod` 는 **왼쪽 피연산자의 부호**를 따른다 | 언어 레퍼런스 6.7 |
| 0 으로 나누면 `ZeroDivisionError` | 언어 레퍼런스 6.7 |
| `round` 는 동점을 **짝수 쪽**으로 보낸다. `ndigits` 가 없으면 `int` 를 돌려준다 | `round()` 문서 |
| `round(2.675, 2)` 가 `2.67` 인 것은 **버그가 아니라 float 표현의 결과**다 | `round()` 문서 Note |
| `bool` 은 `int` 의 하위 클래스이고, `True`·`False` 가 **유일한 불린 객체**다 | 데이터 모델 3.2 |
| 표준 라이브러리는 그 의존을 **권하지 않는다**(`int()` 로 명시 변환하라) | `stdtypes` |
| `complex` 는 실수부·허수부가 각각 기계 배정밀도다 | 데이터 모델 3.2 |

### 언어가 보장하지 **않는** 것 — 문서가 직접 물러선 자리

| 사실 | 문서의 표현 |
|---|---|
| `float` 의 범위·오버플로 처리 | *"You are at the mercy of the underlying machine architecture (and C or Java implementation)"* |
| `float` 이 C 의 `double` 이다 | *"usually implemented using double in C"* — **"usually"** 가 붙어 있다 |

★ 그래서 **「파이썬 float 은 IEEE 754 배정밀도다」는 언어 사실이 아니다.** 이 머신의 사정이고, `sys.float_info` 로 확인해야 한다.

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 정수 ↔ 10진 문자열 변환에 **4300자리 기본 한도**가 있다(3.11+) | `sys.get_int_max_str_digits()` 가 `4300` |
| 그 한도를 `-X int_max_str_digits` · `PYTHONINTMAXSTRDIGITS` · `sys.set_int_max_str_digits` 로 바꾼다 | 셋 다 던져서 확인 |
| 한도의 하한이 **640**(또는 0 = 무제한)이다 | `-X int_max_str_digits=100` 이 `Fatal Python error` 로 죽는다 |
| 16진수 변환은 한도에 안 걸린다 | `hex(10**5000)` 이 통과 |
| `sys.getsizeof(0)` 이 `28`, `2**1000` 이 `160` | 내부 표현의 크기 |
| `sys.maxsize` 가 `9223372036854775807` | 64비트 빌드의 값 |
| 작은 정수 객체가 미리 만들어져 재사용된다 | [02번](../02-is-vs-eq-interning/2-summary.md) 정본 |

### 이 판·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `mant_dig` 가 `53`, `dig` 가 `15`, `max` 가 `1.797...e+308` | 기계·빌드에 달렸다 |
| `0.1` 이 `0.10000000000000000555` 로 저장된다 | 위와 같은 이유 |
| `Decimal` 의 기본 `prec` 가 `28` | 컨텍스트 설정. 바꿀 수 있다 |
| `(1/3)*3 == 1.0` 이 `True` | **오차가 우연히 상쇄된 것**이다. 다른 값에서는 안 그렇다 |
| `ValueError` · `Fatal Python error` 의 문구 | 판마다 바뀐다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「파이썬은 `int` 가 무한이라 오버플로가 없다 — CPython 얘기다」\
  → **아니다. 이건 언어 보장이다.** 데이터 모델이 *"unlimited range"* 라고 적는다. ★ 이 주제에서 드물게 **「파이썬은 이렇다」로 적어도 되는** 자리다.
- ✗ 「파이썬 `float` 은 IEEE 754 배정밀도다」\
  → **이 머신의 사정이다.** 문서는 *"usually implemented using double in C"* 이고 *"at the mercy of the underlying machine architecture"* 라고 적는다.
- ✗ 「정수는 얼마든지 커서 출력도 문제없다」\
  → **3.11 부터 10진 문자열 변환이 4300자리에서 막힌다.** 연산은 되고 표시가 안 된다.
- ✗ 「`round(2.675, 2)` 가 `2.67` 인 것은 은행가 반올림 때문이다」\
  → **동점이 아니라서**다. 두 현상이 다르다.
- ✗ 「`-7 // 2` 는 CPython 이 그렇게 구현한 것이다」\
  → **언어 레퍼런스가 floor 를 적용하라고 정했다.** 어느 구현에서도 `-4` 여야 한다.

**판정 기준 한 줄**: **연산자의 의미는 명세에 있고, 수의 표현은 기계에 있다.** 「왜 이 값이 나오나」가 연산자 규칙이면 보장, 자릿수·정밀도·메모리면 구현·기계다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `//` · `%` · `divmod` | 인덱스·페이지·버킷·시분초 분해. **음수 입력을 반드시 시험한다** |
| `/` | 「정확히 얼마인가」를 물을 때. **큰 정수에는 쓰지 않는다** |
| `math.fmod` | C·다른 언어와 **같은 나머지 규약**이 필요할 때만 |
| `float` | 과학 계산·비율·그래픽. **`==` 로 비교하지 않는다**(`math.isclose`) |
| `decimal` | **금액.** 문자열로 넣고, 반올림 모드를 명시한다 |
| `fractions` | 유리수 연산이 정확해야 할 때 — 비율 누적·기어비·악보 |
| `round` | 표시용. **회계 반올림에는 `Decimal.quantize`** 를 쓴다 |
| `sum(조건들)` | 참의 개수 세기. 표준 라이브러리는 `int()` 명시를 권한다 |

**안 쓰는 자리**는 둘이다.\
**금액을 `float` 으로 다루지 마라** — 더할수록 어긋난다.\
**큰 정수를 `/` 로 나누지 마라** — 에러 없이 틀린다.

## 핵심 문장

- 「나눈다」는 세 질문이다 — `/`(정확히 얼마) · `//`(몇 개씩) · `%`(얼마 남나). `divmod` 가 뒤 둘을 한 번에 준다.
- `-7 // 2` 가 `-4` 인 것은 **수직선에서 아래로 내리기 때문**이다. 그래서 이름이 「바닥 나눗셈」이고, C·Java 의 「0 쪽으로 자르기」와 갈린다.
- `%` 의 부호는 **오른쪽 피연산자**를 따르고 `math.fmod` 는 **왼쪽**을 따른다. 「나머지」라는 한 낱말이 두 규약을 가리킨다.
- `int` 는 **언어가 보장하는 무제한**이고, `float` 은 **문서가 기계에 맡긴** 것이다. 두 문장을 뒤집어 적으면 둘 다 틀린다.
- `0.1 + 0.2` 문제는 `decimal`(십진)·`fractions`(유리수)로 푼다. `Decimal` 에는 **문자열로** 넣어야 한다.
- `round` 는 동점을 짝수로 보낸다. 그러나 `round(2.675, 2)` 가 `2.67` 인 것은 **동점이 아니라서**다 — 두 현상을 섞지 마라.
- `bool` 은 `int` 의 하위 클래스다. `True + True == 2` 이고 dict 키로는 `1` 과 합쳐진다 — [05번](../05-truthiness-and-short-circuit/)으로 이어진다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **04번**
- 이어지는 곳: [목록의 **05번 주제**](../05-truthiness-and-short-circuit/) 「진릿값과 단축 평가」 — `bool` 이 `int` 의 하위 클래스라는 사실이 **거기서 진릿값 판정으로 이어진다.**
- 이어지는 곳: 목록의 **50번 주제** 「`decimal`·float 정밀도·`round`」 — **`Decimal` 의 컨텍스트·반올림 모드·금액 설계는 그쪽이 정본**이다. 여기서는 「연산자가 무슨 값을 내나」까지만 다룬다.
- 이어지는 곳: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — `True == 1` 인데 `True is 1` 이 아닌 것, `nan` 의 어긋남.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 연산자 사용법 소개.\
  **경계**: 그쪽은 「이렇게 쓴다」까지, 여기는 「**음수와 큰 수에서 무엇이 틀리나**」부터다.
- 기존 노트: [`cs/foundations/data-representation/`](../../../../data-representation/) — 부동소수 표현의 원리.\
  **경계**: 「왜 이진 분수인가」는 그쪽이 정본이고, 여기는 「**그래서 파이썬 코드에서 무엇을 쓰나**」만 다룬다.
- 연혁은 여기가 아니다: [`history/python/`](../../../../../../history/python/)
- 공식 문서: [6.7. Binary arithmetic operations](https://docs.python.org/3.12/reference/expressions.html#binary-arithmetic-operations) · [`round()`](https://docs.python.org/3.12/library/functions.html#round) · [Numeric Types](https://docs.python.org/3.12/library/stdtypes.html#typesnumeric) · [Floating-Point Arithmetic](https://docs.python.org/3.12/tutorial/floatingpoint.html)

## 용어 풀이

- **참된 나눗셈(true division)**: `/`. 정수끼리 나눠도 `float` 을 돌려준다.\
  Python 3 에서 `/` 의 의미가 이것으로 고정됐다.
- **바닥 나눗셈(floor division)**: `//`. 결과를 수직선에서 **작은 쪽**으로 내린다.\
  `-3.5` 는 `-4` 가 된다. 0 쪽이 아니라 음의 무한대 쪽이다.
- **자르기(truncation)**: 소수부를 그냥 버려 **0 쪽으로** 가는 것. `int()`·`math.trunc()` 가 한다.\
  양수에서는 바닥 나눗셈과 같고 음수에서만 갈린다.
- **나머지(modulo)**: `%`. 파이썬에서는 **오른쪽 피연산자와 같은 부호**를 낸다.\
  그래서 `(-17) % 8` 이 `7` 이고, 버킷 번호로 바로 쓸 수 있다.
- **`math.fmod`**: C 규약의 나머지. **왼쪽 피연산자의 부호**를 따른다.\
  `fmod(-7, 2)` 가 `-1.0` 이다. 0 으로 나누면 `ValueError` 다(`ZeroDivisionError` 가 아니다).
- **부동소수(floating point)**: 수를 「가수 × 2의 지수승」으로 저장하는 방식.\
  10진 소수 대부분이 정확히 안 담긴다.
- **가수 비트(mantissa)**: 유효 숫자를 담는 비트 수. 이 머신은 `sys.float_info.mant_dig` 가 `53` 이다.\
  그래서 `2**53` 을 넘는 정수는 `float` 으로 정확히 못 담는다.
- **`decimal`**: 10진 소수를 정확히 담는 표준 모듈.\
  금액에 쓴다. **문자열로 넣어야** 의미가 있다.
- **`fractions`**: 유리수를 분자/분모로 정확히 담는 표준 모듈.\
  `Fraction("0.1")` 은 정확히 `1/10` 이다.
- **은행가 반올림(banker's rounding)**: 동점(`.5`)을 **가까운 짝수**로 보내는 반올림.\
  파이썬 `round` 와 `Decimal` 의 기본값이다. 많이 더할 때 편향이 안 쌓인다.
- **`int_max_str_digits`**: 정수를 10진 문자열로 바꿀 때의 자릿수 한도(3.11+, 기본 4300).\
  서비스 거부 공격을 막는 **구현의 방어 장치**다. 하한은 640, `0` 은 무제한.
- **`sys.maxsize`**: 인덱스가 가질 수 있는 최댓값. **정수의 상한이 아니다.**
- **`math.isclose`**: 두 실수가 「충분히 가까운가」를 판정하는 함수.\
  `float` 끼리는 `==` 대신 이것을 쓴다.

## 더 들어가면

- **`int` 는 `__index__` 를 가진 객체까지 받는다.** 그래서 `numpy` 정수나 `IntEnum` 이 인덱스 자리에 그냥 들어간다(목록의 **37번 주제**).
- **`float` 에도 `is_integer()`·`as_integer_ratio()`·`hex()`/`fromhex()` 가 있다.** 저장된 값을 **정확히** 들여다보는 세 창이다.
- **`decimal` 의 컨텍스트는 스레드별이다.** `getcontext()` 가 돌려주는 것이 현재 스레드의 것이고, `localcontext()` 로 블록 단위 설정이 가능하다 — 정본은 목록의 **50번 주제**.
- **`complex` 에는 순서 비교가 없다.** 정렬·`min`/`max` 에 넣으면 `TypeError` 가 난다. 정렬 가능성 일반은 [목록의 **31번 주제**](../31-comparison-protocol-and-sortability/).
