# python/syntax/04-numeric-types-and-division — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> ★ **손계산으로 유도한 수치는 하나도 없다.**
> 단 **부동소수의 자릿수·`int_max_str_digits` 한도는 기계·구현에 달렸다**(9·10번 답).

## 정답

### 1. 음수에서 갈리는 한 줄 (예측)

**출력**

```text
-3.5
-4
1
(-4, 1)
-1.0
-3
```

**왜 그런가 — 수직선 한 장으로 끝난다**

```text
   -5   -4   -3   -2   -1    0    1    2
    |    |    |    |    |    |    |    |
         ^         ^
      바닥(floor)  0 쪽으로 자르기(truncate)
      -7 // 2      int(-7 / 2)
       = -4         = -3
```

- `-7 / 2` → `-3.5`. 참된 나눗셈이라 그냥 실수다.
- `-7 // 2` → **`-4`**. 언어 레퍼런스가 정한다 — *"the result is that of mathematical division with the **'floor'** function applied to the result."*\
  `-3.5` 를 **아래로** 내리면 `-4` 다. **이름 「바닥 나눗셈」이 여기서 나온다.**
- `-7 % 2` → `1`. 문서가 정한다 — *"The modulo operator always yields a result with the same sign as its **second** operand (or zero)."*\
  몫이 한 칸 내려갔으니 나머지가 그만큼 올라온다.
- `divmod(-7, 2)` → `(-4, 1)`. 위 둘을 한 번에 준다(`divmod(x,y) == (x//y, x%y)`).
- `math.fmod(-7, 2)` → **`-1.0`**. 이쪽은 **왼쪽** 피연산자의 부호를 따른다. C 규약이다.
- `int(-7 / 2)` → `-3`. 0 쪽으로 자른다. **C·Java 의 `/` 와 같은 결과**다.

**항등식으로 검산하면 맞아떨어진다**

```python
print((-7//2)*2 + (-7%2))
```

```text
-7
```

`x == (x//y)*y + (x%y)` 가 명세의 항등식이고, **손으로 유도하지 않고 던져서 확인했다.**

**한 문장으로**

「나머지」라는 한국어 한 낱말이 **두 규약**을 가리킨다 — 파이썬의 `%`(오른쪽 부호)와 C 의 `fmod`(왼쪽 부호).\
어느 쪽이 옳으냐가 아니라 **무엇이 필요하냐**다. 문서의 말로 *"Which approach is more appropriate depends on the application."*

### 2. 부호가 반대편에 붙는다 (예측)

**출력**

```text
-4 -1 1.0
7 -1.0
-7
3.0 float
```

**왜 그런가 — 한 줄씩**

- `7 // -2` → `-4`. `-3.5` 를 아래로 내렸다. **나누는 수가 음수여도 규칙은 같다.**
- `7 % -2` → `-1`. 오른쪽(`-2`)이 음수니 나머지도 음수다.
- `math.fmod(7, -2)` → `1.0`. 왼쪽(`7`)이 양수니 양수다. **정확히 반대다.**
- `(-17) % 8` → `7`. 오른쪽이 양수니 나머지도 **언제나 0 이상**이다.
- `math.fmod(-17, 8)` → `-1.0`. 음수가 나온다.
- `(-7//2)*2 + (-7%2)` → `-7`. 항등식이 성립한다.
- `7.5 // 2` → `3.0`, 타입은 **`float`**. `//` 가 「정수 나눗셈」이 아니라는 증거다.

```text
 파이썬 %                              math.fmod (C 규약)
 부호 = 오른쪽 피연산자                 부호 = 왼쪽 피연산자
   -17 % 8  =  7                        fmod(-17, 8) = -1.0
     7 % -2 = -1                        fmod(7, -2)  =  1.0
```

**버킷 번호로 쓸 수 있는 쪽 — `%` 다**

```python
import math
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

- `%` 는 나누는 수가 양수면 **언제나 0 이상**을 낸다 → 리스트 인덱스로 바로 쓸 수 있다.
- `math.fmod` 는 음수를 낸다 → 인덱스로 쓰면 뒤에서부터 세거나 `IndexError` 가 난다.
- ★ 문자열 해시는 음수가 흔하다([03번](../03-mutability-and-copying/2-summary.md)의 다섯 판 중 하나가 음수였다). **이 성질이 파이썬에서는 공짜로 안전하다.**

**여기서 틀리는 자리**

C 습관으로 `((h % n) + n) % n` 을 쓰면 **불필요하다**(결과는 맞지만 군더더기다).\
반대로 C 와 맞추려고 `math.fmod` 를 쓰면 **진짜로 음수 버킷이 나온다.**

### 3. 무한한 `int` 와 그 한도 (예측)

**출력**

```text
4300
16610
ValueError: Exceeds the limit (4300 digits) for integer string conversio
4155
```

**왜 그런가 — 연산과 표시가 갈린다**

```text
 연산: 제한 없다 (언어 보장)            10진 문자열 변환: 제한 있다 (구현)
   10**5000 계산 OK                     str(10**5000)  -> ValueError
   bit_length() -> 16610                int("1"*5000)  -> ValueError
   hex(...) -> 길이 4155 OK             기본 한도 4300 자리
```

- `10**5000` 을 **만드는 것은 된다.** 언어 레퍼런스가 *"numbers in an unlimited range, subject to available (virtual) memory only"* 라고 정한다.
- 막히는 것은 **10진 문자열로 바꾸는 것**뿐이다. 3.11 에서 들어온 **구현의 방어 장치**다 —\
  `int()` 문서의 변경 이력이 *"int string inputs and string representations can be limited to help avoid denial of service attacks"* 라고 적는다.
- `hex` 는 안 막힌다. 2의 거듭제곱 진법은 변환이 선형이라 공격 소재가 안 되기 때문이다.

**「무제한」과 「ValueError」가 양립하는 이유 — 두 가지가 다른 것이다**

| 무엇 | 지위 | 제한 |
|---|---|---|
| 정수 **값**의 범위 | **언어 보장** | 메모리뿐 |
| 정수 ↔ **10진 문자열** 변환 | **CPython 3.11+ 의 방어 장치** | 기본 4300자리 |

**한도를 바꾸는 세 방법 — 전부 던져서 확인했다**

```python
# $ python3 -X int_max_str_digits=0 -c "..."
```

```text
0 = 0 (제한 해제)
str(10**5000) 길이: 5001
```

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
try:
    str(10**800)
except ValueError as e:
    print("ValueError:", str(e)[:60])
```

```text
런타임 설정: 700
ValueError: Exceeds the limit (700 digits) for integer string conversion
```

**★ 던져 봐야만 나오는 출력 — 하한이 640 이다**

```python
# $ python3 -X int_max_str_digits=100 -c "print('여기까지 안 온다')"
```

```text
Fatal Python error: config_init_int_max_str_digits: -X int_max_str_digits: invalid limit; must be >= 640 or 0 for unlimited.
Python runtime state: preinitialized
```

`ValueError` 도 `SystemExit` 도 아니라 **`Fatal Python error`** 다 — 인터프리터가 뜨기도 전(`preinitialized`)에 죽는다.\
잡을 수 있는 예외가 아니다.

### 4. 큰 정수를 `/` 로 나누면 (예측)

**출력**

```text
576460752303423489
576460752303423488
False
2.0 float
```

**왜 그런가**

```text
 int: 자릿수 제한 없음                 float: 가수 53비트
  2**60 + 3 을 정확히 담는다            2**60 + 3 을 담으려면 61비트 필요
        |                                     |
        v                                     v
  m // 2 는 정확하다                     m / 2 는 이미 반올림된 값
   576460752303423489                    -> int() 를 씌워도 ...488
```

- `m // 2` 는 **정수 연산**이라 정확하다.
- `m / 2` 는 먼저 `float` 으로 바꾸는데, `2**60 + 3` 은 53비트 가수에 안 들어간다. **거기서 값이 이미 뭉개졌다.**
- `4 / 2` 가 `2.0` 인 것도 같은 규칙이다 — *"Division of integers yields a float"* 이라 **나눠 떨어져도 실수**다.

**에러도 경고도 없는 이유**

**`float` 으로의 변환이 정상 동작이기 때문이다.** 넘치지도 않았고 예외 조건도 아니다 —\
그냥 **가까운 표현 가능한 값으로 반올림**됐을 뿐이다. 그게 부동소수의 정의다.

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 주문 번호나 타임스탬프를 `/` 로 나누면 작은 값에서는 맞고 53비트를 넘는 순간부터 1씩 어긋난다.

**★ 한 사례만 보면 못 잡는다**

```python
m = 2**60 + 1
print("m // 2 =", m // 2)
print("int(m / 2) =", int(m / 2))
```

```text
m // 2 = 576460752303423488
int(m / 2) = 576460752303423488
```

**여기서는 같다.** `m` 이 홀수라 `//` 가 내림하고, `/` 는 정밀도가 날아가 같은 값이 됐다.\
`+3` 으로 바꿔야 갈린다 — **갈리는 지점을 일부러 찾아 던져야 나온다.**

**고치는 법**

정수 나눗셈에는 **언제나 `//`**. 실수가 필요하면 그때만 `/`.

### 5. `0.1 + 0.2` 와 세 가지 자 (예측)

**출력**

```text
0.30000000000000004
0.3
0.1000000000000000055511151231257827021181583404541015625
1/10 3602879701896397/36028797018963968
```

**왜 그런가**

```text
 float: 2진 분수만 정확          decimal: 10진 분수 정확     fractions: 유리수 전부 정확
  0.1 = 0.0001100110011...(무한)  Decimal("0.1") = 0.1       Fraction("0.1") = 1/10
  53비트에서 끊는다               1/3 은 여전히 못 담는다      1/3 도 정확
  -> 0.1 + 0.2 = 0.30000000000000004
```

- `0.1 + 0.2` → `0.30000000000000004`. 두 값이 이미 조금씩 크게 저장돼 있고 그 오차가 더해졌다.
- `Decimal("0.1") + Decimal("0.2")` → `0.3`. **10진으로 저장하니 정확하다.**
- `Decimal(0.1)` → 55자리 숫자. ★ **이미 오염된 `float` 을 받아** 그 오염을 전부 보여 준 것이다.
- `Fraction("0.1")` → `1/10` 정확. `Fraction(0.1)` → `3602879701896397/36028797018963968` — **float 이 실제로 담고 있는 값**이다.

**`Decimal(0.1)` 과 `Decimal("0.1")` 이 갈리는 이유 — 무엇을 받았나**

```text
 Decimal("0.1")                       Decimal(0.1)
  문자열 "0.1" 을 받는다                이미 만들어진 float 을 받는다
  -> 10진으로 그대로 해석                -> 그 float 이 담고 있는 값을 그대로 옮긴다
  -> 0.1                               -> 0.1000000000000000055511151231257827021181583404541015625
```

**`Decimal` 은 고쳐 주는 도구가 아니다.** 오염되기 전에 받아야 한다.\
`Fraction(0.1)` 의 분수가 `(0.1).as_integer_ratio()` 와 한 글자도 같은 것이 그 증거다.

```python
print("as_integer_ratio:", (0.1).as_integer_ratio())
print("0.1 의 실제 값:", f"{0.1:.20f}")
```

```text
as_integer_ratio: (3602879701896397, 36028797018963968)
0.1 의 실제 값: 0.10000000000000000555
```

**셋을 언제 고르나**

| 도구 | 정확히 담는 것 | 못 담는 것 | 쓰는 자리 |
|---|---|---|---|
| `float` | 2진 분수(`0.5`·`0.25`) | 대부분의 10진 소수 | 과학 계산·비율. **빠르다** |
| `decimal` | 10진 소수 | `1/3` | **금액.** 문자열로 넣는다 |
| `fractions` | 유리수 전부 | 무리수 | 비율 누적. 분모가 커진다 |

**★ 한 사례로 결론을 내면 안 된다**

```python
print("1/3 을 셋 더하면 float:", (1/3)*3 == 1.0)
import math
print("math.isclose(0.1+0.2, 0.3):", math.isclose(0.1+0.2, 0.3))
```

```text
1/3 을 셋 더하면 float: True
math.isclose(0.1+0.2, 0.3): True
```

`(1/3)*3 == 1.0` 이 **`True`** 다 — 오차가 우연히 상쇄된 것이지 정확해서가 아니다.\
「이건 맞네」 한 판으로 「float 은 괜찮다」를 결론내면 여기서 속는다.

### 6. `.5` 는 어디로 가나 (예측)

**출력**

```text
0 2 2 4
0 -2
2.67
int float
```

**왜 그런가**

문서가 정한다 — *"if two multiples are equally close, rounding is done toward the **even** choice (so, for example, both `round(0.5)` and `round(-0.5)` are `0`, and `round(1.5)` is `2`)."*

```text
 학교식 반올림                        파이썬의 round (은행가 반올림)
  0.5 -> 1                            0.5 -> 0   (0 이 짝수)
  1.5 -> 2                            1.5 -> 2   (2 가 짝수)
  2.5 -> 3                            2.5 -> 2   (2 가 짝수)   <- 여기서 갈린다
  3.5 -> 4                            3.5 -> 4   (4 가 짝수)
 -0.5 -> -1                          -0.5 -> 0
 -1.5 -> -2                          -1.5 -> -2

 많이 더하면 위/아래가 균형을 이뤄 편향이 안 쌓인다
```

**★ 셋째 줄만 원인이 다르다**

```python
print("round(2.675, 2) =", round(2.675, 2), "  (2.675 의 실제 값:", f"{2.675:.20f}", ")")
```

```text
round(2.675, 2) = 2.67   (2.675 의 실제 값: 2.67499999999999982236 )
```

- `2.675` 는 **애초에 `2.6749999...` 로 저장돼 있다.** 동점이 아니다.
- 그러니 은행가 반올림이 개입할 일이 없다 — **그냥 더 가까운 쪽(`2.67`)으로 간 것**이다.
- 문서가 이것을 따로 적는다 — *"This is not a bug: it's a result of the fact that most decimal fractions can't be represented exactly as a float."*

```text
 원인 두 가지를 갈라 보면

  round(2.5) = 2       <- 동점이다. 짝수 규칙이 작동했다   (은행가 반올림)
  round(2.675, 2) = 2.67 <- 동점이 아니다. 그냥 가까운 쪽   (float 표현)

 섞어 외우면 "round 는 무조건 내린다" 같은 틀린 규칙이 생긴다
```

**넷째 줄 — `ndigits` 가 타입을 바꾼다**

- `round(0.5)` → `int` (`0`). *"The return value is an integer if ndigits is omitted or None."*
- `round(0.5, 0)` → `float` (`0.0`). *"Otherwise, the return value has the same type as number."*

같은 값처럼 보이는데 타입이 다르다. JSON 직렬화나 문자열 포맷에서 드러난다.

**원하는 반올림을 고르려면**

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

`Decimal` 의 기본도 은행가 반올림이다 — **파이썬 전반의 기본값**이다.\
학교식이 필요하면 `ROUND_HALF_UP` 을 **명시**한다. 금액에서는 회계 규정이 정할 일이지 기본값에 맡길 일이 아니다.

### 7. `bool` 이 `int` 라는 것 (왜)

**왜 `True + True == 2` 인가**

언어 레퍼런스가 정한다 — *"The Boolean type is a **subtype of the integer type**, and Boolean values behave like the values 0 and 1, respectively, in almost all contexts, the exception being that when converted to a string, the strings `"False"` or `"True"` are returned."*

```text
         int
          ^
          |  (하위 클래스)
         bool
          |
    False = 0,  True = 1

 그래서 산술이 그대로 된다.  예외는 str() 하나뿐이다.
```

```python
print("issubclass(bool, int):", issubclass(bool, int), " isinstance(True, int):", isinstance(True, int))
print("True + True =", True + True, type(True+True).__name__)
print("sum([True, True, False]) =", sum([True, True, False]))
print("True * 3 =", True * 3, "  'ab' * True =", "ab" * True)
```

```text
issubclass(bool, int): True  isinstance(True, int): True
True + True = 2 int
sum([True, True, False]) = 2
True * 3 = 3   'ab' * True = ab
```

**왜 dict 키가 하나가 되는가**

```python
print("hash(1) == hash(True):", hash(1) == hash(True), " 1 == True:", 1 == True)
print({1: 'a', True: 'b'})
print({0: 'off', False: '꺼짐'})
```

```text
hash(1) == hash(True): True  1 == True: True
{1: 'b'}
{0: '꺼짐'}
```

dict 키의 동일성 판정은 **해시가 같고 `==` 가 참이면 같은 키**다. 둘 다 성립하므로 합쳐진다.\
★ **먼저 들어온 키 객체가 남고 값만 덮인다** — 표시가 `1` 이고 값이 `'b'` 인 것이 그 증거다.

**왜 권하지 않는가**

표준 라이브러리가 직접 적는다 — *"However, relying on this is discouraged; explicitly convert using `int()` instead."*

세 가지 이유로 읽힌다.

1. **읽는 사람이 헷갈린다** — `total = True * price` 는 의도가 안 보인다.
2. **구별해야 하는 자리에서 조용히 섞인다** — dict 키·`in`·`count`·`index` 가 전부 `==` 를 쓴다.
3. **`bool` 은 더 상속할 수 없다.** `True`·`False` 가 유일한 불린 객체여야 하기 때문이다.

```python
try:
    class MyBool(bool): pass
except TypeError as e:
    print("bool 상속 -> TypeError:", e)
```

```text
bool 상속 -> TypeError: type 'bool' is not an acceptable base type
```

**05번으로 이어진다**

`bool` 이 `int` 라서 `True` 가 `1` 처럼 굴지만, **진릿값 판정은 그것과 다른 규칙**이다 —\
`__bool__`/`__len__` 이 그 자리다([목록의 **05번 주제**](../05-truthiness-and-short-circuit/)).

### 8. 0 으로 나누는 네 가지 (경계)

**출력**

```text
1 // 0   -> ZeroDivisionError: integer division or modulo by zero
1 / 0    -> ZeroDivisionError: division by zero
1 % 0    -> ZeroDivisionError: integer modulo by zero
math.fmod(1,0) -> ValueError: math domain error
```

**세 메시지가 전부 다르다**

| 연산 | 예외 | 메시지 |
|---|---|---|
| `1 // 0` | `ZeroDivisionError` | `integer division or modulo by zero` |
| `1 / 0` | `ZeroDivisionError` | `division by zero` |
| `1 % 0` | `ZeroDivisionError` | `integer modulo by zero` |
| `math.fmod(1, 0)` | **`ValueError`** | `math domain error` |

- 앞의 셋은 언어 레퍼런스가 정한다 — *"Division by zero raises the ZeroDivisionError exception."*
- **메시지 문구가 갈린다는 것 자체가 정보다** — 로그만 봐도 어느 연산에서 터졌는지 알 수 있다.

**어디서 새나**

```python
def safe(a, b):
    try:
        return a % b
    except ZeroDivisionError:
        return 0

import math
def safe_c(a, b):
    try:
        return math.fmod(a, b)     # <- 여기서 샌다
    except ZeroDivisionError:
        return 0
```

`math.fmod` 는 **`ValueError`** 를 던지므로 `except ZeroDivisionError` 를 그냥 통과해 나간다.\
C 규약이 필요해서 `%` 를 `math.fmod` 로 바꾸는 리팩토링을 하면 **예외 처리가 조용히 무력화된다.**

★ 같은 실수를 다른 곳에서도 한다 — `math` 모듈은 대체로 **`ValueError`(math domain error)** 로 정의역 위반을 알린다.\
`math.sqrt(-1)`·`math.log(0)` 도 같은 계열이다.

**메시지 문구는 관찰이다**

예외의 **종류**는 명세지만 **문구**는 아니다. 판이 바뀌면 문구가 바뀔 수 있으므로,\
문구로 분기하는 코드를 쓰면 안 된다.

### 9. 무엇이 언어 보장인가 (경계)

**답: 「`int` 는 범위가 무제한이다」가 언어 보장이다.**

| 명제 | 지위 | 문서의 표현 |
|---|---|---|
| `int` 는 범위가 무제한 | **언어 보장** | *"These represent numbers in an **unlimited range**, subject to available (virtual) memory only."* / *"Integers have unlimited precision."* |
| `float` 은 IEEE 754 배정밀도 | **보장 아님** | *"You are **at the mercy of the underlying machine architecture** (and C or Java implementation) for the accepted range and handling of overflow."* |
| `float` 이 C 의 `double` 이다 | **보장 아님** | *"Floating-point numbers are **usually** implemented using double in C"* — **"usually"** 가 붙어 있다 |

```text
 int                                 float
  명세가 "unlimited" 라고 말한다        명세가 "기계에 달렸다" 고 말한다
  -> 어느 구현에서도 같아야 한다         -> 이 머신에서 재야 한다
  -> "파이썬은 이렇다" 로 적어도 된다     -> "이 머신에서는 이렇다" 로 적어야 한다
```

★ **이 갈래에서 드물게 「파이썬은 이렇다」로 적어도 되는 자리가 `int` 의 무제한이다.**\
반대로 「파이썬 float 은 64비트 double 이다」는 **틀린 문장**이다.

**그래서 float 쪽은 재서 적는다**

```python
import sys
fi = sys.float_info
print("mant_dig:", fi.mant_dig, " dig:", fi.dig, " max:", fi.max,
      " epsilon:", fi.epsilon, " radix:", fi.radix)
```

```text
mant_dig: 53  dig: 15  max: 1.7976931348623157e+308  epsilon: 2.220446049250313e-16  radix: 2
```

이 다섯 값이 **이 머신의 사정**이다. 다른 머신·다른 구현에서는 다시 찍어야 한다.

**한 줄 판정기**

**연산자의 의미는 명세에 있고, 수의 표현은 기계에 있다.**\
「왜 이 값이 나오나」가 연산자 규칙이면 보장이고, 자릿수·정밀도·메모리면 구현·기계다.

### 10. 세 층 가르기 (경계)

**① 언어 보장** — 레퍼런스가 정한 것.

| 사실 | 근거 |
|---|---|
| `int` 는 범위가 무제한 — 가용 (가상) 메모리에만 달렸다 | 데이터 모델 3.2 / `stdtypes` |
| `/` 는 정수끼리도 `float`, `//` 는 정수를 낸다 | 언어 레퍼런스 6.7 |
| `//` 의 결과는 수학적 나눗셈에 **floor** 를 적용한 것 | 언어 레퍼런스 6.7 |
| `%` 는 언제나 **오른쪽 피연산자와 같은 부호**(또는 0) | 언어 레퍼런스 6.7 |
| `x == (x//y)*y + (x%y)` · `divmod(x,y) == (x//y, x%y)` | 언어 레퍼런스 6.7 |
| `math.fmod` 는 **왼쪽 피연산자의 부호**를 따른다 | 언어 레퍼런스 6.7 |
| 0 으로 나누면 `ZeroDivisionError` | 언어 레퍼런스 6.7 |
| `round` 는 동점을 **짝수 쪽**으로. `ndigits` 없으면 `int` 반환 | `round()` |
| `round(2.675, 2) == 2.67` 은 **버그가 아니라 float 표현의 결과** | `round()` Note |
| `bool` 은 `int` 의 하위 클래스, `True`/`False` 가 **유일한 불린 객체** | 데이터 모델 3.2 |
| 그 성질에 기대는 것은 **권장되지 않는다** | `stdtypes` |
| `complex` 는 실·허수부가 각각 기계 배정밀도 | 데이터 모델 3.2 |

**② CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| 정수 ↔ 10진 문자열 변환에 **4300자리 기본 한도**(3.11+) | `sys.get_int_max_str_digits()` 가 `4300` |
| `-X int_max_str_digits` · `PYTHONINTMAXSTRDIGITS` · `sys.set_int_max_str_digits` 로 바꾼다 | 셋 다 던져서 확인 |
| 한도의 **하한이 640**(또는 0 = 무제한) | `=100` 이 `Fatal Python error` 로 죽는다 |
| 16진수 변환은 한도에 안 걸린다 | `hex(10**5000)` 이 통과 |
| `sys.getsizeof(0)` = `28`, `2**1000` = `160` | 내부 표현의 크기 |
| `sys.maxsize` = `9223372036854775807` | 64비트 빌드의 값 |

**③ 이 머신·이 판의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| `mant_dig` `53` · `dig` `15` · `max` `1.797...e+308` | 기계·빌드에 달렸다 |
| `0.1` 이 `0.10000000000000000555` 로 저장된다 | 위와 같은 이유 |
| `Decimal` 의 기본 `prec` 가 `28` | 컨텍스트 설정. 바꿀 수 있다 |
| `(1/3)*3 == 1.0` 이 `True` | **오차가 우연히 상쇄된 것**이다 |
| `ZeroDivisionError`·`ValueError`·`Fatal Python error` 의 **문구** | 예외 종류는 명세지만 문구는 아니다 |

**그래서 이렇게 적으면 틀린다**

- ✗ 「`int` 가 무한인 건 CPython 얘기다」 → **아니다. 언어 보장이다.**
- ✗ 「파이썬 `float` 은 IEEE 754 배정밀도다」 → **이 머신의 사정이다.**
- ✗ 「정수는 얼마든지 커서 출력도 문제없다」 → **3.11 부터 10진 출력이 4300자리에서 막힌다.**
- ✗ 「`round(2.675, 2)` 가 `2.67` 인 건 은행가 반올림 때문」 → **동점이 아니라서**다.
- ✗ 「`-7 // 2` 는 CPython 이 그렇게 구현한 것」 → **명세가 floor 를 적용하라고 정했다.**

> **구현 세부사항(implementation detail)** — 언어 명세가 보장하지 않고 특정 구현이 그렇게 만들어 둔 것.\
> 예: `int_max_str_digits` 는 3.11 에서 CPython 이 공격 방어용으로 넣은 것이지 언어의 성질이 아니다.

### 11. 무엇으로 계산할 것인가 (연결)

| 자리 | 고르는 것 | 왜 |
|---|---|---|
| **금액 합계** | `decimal.Decimal`, **문자열로 입력**, 반올림 모드 명시 | `float` 은 10진 소수를 정확히 못 담아 더할수록 어긋난다. `Decimal(0.1)` 은 이미 오염된 값을 받으므로 안 된다 |
| **페이지 수·분할** | `int` 와 `//`·`-(-a // b)` (올림) | 정확하고 오버플로가 없다. **음수 입력을 반드시 시험한다** — `//` 가 C 와 다르다 |
| **해시 버킷** | `int` 와 `%` | 파이썬 `%` 는 나누는 수가 양수면 **언제나 0 이상**이라 인덱스로 바로 쓴다. `math.fmod` 는 음수를 낸다 |
| **과학 계산·비율** | `float` 과 `math.isclose` | CPU 가 직접 계산해 압도적으로 빠르다. **`==` 로 비교하지 않는다** |

```text
 "정확해야 하나?"
     |
     +-- 아니오 --> float  (빠르다, isclose 로 비교)
     |
     +-- 예 --> "10진 소수인가?"
                    |
                    +-- 예 (금액) --> Decimal("...")
                    |
                    +-- 아니오 --> "정수로 표현되나?"
                                       |
                                       +-- 예 --> int 와 // %
                                       |
                                       +-- 아니오 --> Fraction
```

**올림 나눗셈 관용구 — 바닥 규약을 이용한다**

```python
a, b = 7, 3
print("올림:", -(-a // b))
print("음수도:", -(-(-7) // 3))
import math
print("math.ceil 판:", math.ceil(a / b))
```

```text
올림: 3
음수도: -2
math.ceil 판: 3
```

`-(-a // b)` 는 **정수만으로** 올림을 낸다 — `math.ceil(a / b)` 는 중간에 `float` 을 거치므로 큰 수에서 4번의 함정에 걸린다.

**한 문장으로**

**정확성이 필요한 곳에는 `float` 을 두지 않는다.** 그 원칙 하나로 네 자리의 선택이 전부 결정된다.\
더 깊은 금액 설계는 목록의 **50번 주제** 「`decimal`·float 정밀도·`round`」 가 정본이다.

---

## 실행 검증

이 파일에 실린 출력은 전부 아래 환경에서 직접 돌려 얻었다.

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys; print(sys.float_info.mant_dig, sys.float_info.radix)"
53 2
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1·2 | `/`·`//`·`%`·`divmod`·`math.fmod`·`int()` 를 음수 조합으로, 항등식 검산, 버킷 5값 | 각 1회 |
| 3 | `get_int_max_str_digits`, `str(10**5000)`, `int("1"*5000)`, `hex`, **`-X` 플래그 3판**(0·640·100), 환경 변수, 런타임 설정 | 각 1회 |
| 4 | `2**60 + 1` 과 `2**60 + 3` **두 사례**, `4 / 2` 의 타입 | 각 1회 |
| 5 | `0.1 + 0.2`, `Decimal` 두 형태, `Fraction` 두 형태, `as_integer_ratio`, `isclose`, `(1/3)*3` | 각 1회 |
| 6 | `round` 7값, `round(2.675, 2)` 와 그 실제 값, 반환 타입 2종, `Decimal.quantize` 3판 | 각 1회 |
| 7 | `issubclass`·`isinstance`·산술 4종·dict 키 2판·`hash` 비교·`bool` 상속 | 각 1회 |
| 8 | 0 나눗셈 4종 | 각 1회 |
| 9 | `sys.float_info` | 1회 |
| 11 | `-(-a // b)` 3판 | 각 1회 |

**★ 한 판으로 결론이 안 나는 것을 두 판 이상 던진 자리**

- **4번** — `2**60 + 1` 에서는 `//` 와 `int(/)` 가 **같았다.** `+3` 으로 바꿔서야 갈렸다.\
  한 사례만 보고 「괜찮다」로 넘겼으면 못 잡았다.
- **5번** — `(1/3)*3 == 1.0` 이 `True` 다. **오차가 우연히 상쇄된 것**이지 float 이 정확해서가 아니다.
- **3번** — `-X int_max_str_digits` 를 0·640·100 세 값으로 던져야 **하한 640** 이 드러났다.

**구현 의존 항목 — 버전·머신이 바뀌면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 5·9번의 부동소수 자릿수 전부 | 기계에 달렸다(문서가 명시) |
| 3번의 `4300`·`640` 과 `Fatal Python error` 문구 | 3.11 에서 들어온 구현 장치다 |
| 8번의 예외 **문구** | 예외 종류는 명세지만 문구는 아니다 |
| `sys.getsizeof`·`sys.maxsize` 값 | 빌드에 달렸다 |

나머지(`/`·`//`·`%`·`divmod` 의 값, 항등식, `round` 의 짝수 규칙, `bool` 이 `int` 의 하위 클래스)는 **언어 보장**이므로 어떤 구현에서도 같아야 한다.
