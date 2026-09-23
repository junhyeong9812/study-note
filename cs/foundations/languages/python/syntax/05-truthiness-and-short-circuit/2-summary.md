# python/syntax/05-truthiness-and-short-circuit — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [Truth Value Testing](https://docs.python.org/3.12/library/stdtypes.html#truth-value-testing) — 무엇이 거짓인가, `__bool__`/`__len__` 규칙
> - [Boolean Operations — and, or, not](https://docs.python.org/3.12/library/stdtypes.html#boolean-operations-and-or-not) — `and`/`or` 가 **피연산자를 돌려준다**는 규정
> - [6.10. Comparisons](https://docs.python.org/3.12/reference/expressions.html#comparisons) — 비교 체이닝의 정의
> - [`any()`](https://docs.python.org/3.12/library/functions.html#any) · [`all()`](https://docs.python.org/3.12/library/functions.html#all)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — 진릿값·단축 평가 규칙은 Python 3 전체 공통. 바이트코드 명령 이름(`POP_JUMP_IF_FALSE` 등)은 **3.12 의 것**이다.
> **선행** — [목록의 **04번 주제**](../04-numeric-types-and-division/) — `bool` 이 `int` 의 하위 클래스라는 사실이 여기로 이어진다.

## 한눈에 — 쉽게 말하면

**`and`·`or` 는 참·거짓을 돌려주는 게 아니라, 마지막으로 들여다본 값을 그대로 내민다.**

```text
 사람이 기대하는 것                     실제로 일어나는 것
  "1 and 2 는 참이니까 True"            1 and 2  ->  2      (마지막으로 본 값)
  "0 or 2 는 참이니까 True"             0 or 2   ->  2
  "1 or 2 는 참이니까 True"             1 or 2   ->  1      (여기서 멈췄으니까)

 문서의 표현: "the Boolean operations or and and
 always return one of their operands."
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 줄 서서 확인하는 검표원 | 단축 평가 | 뒤 피연산자가 **아예 안 돈다** |
| 검표원이 멈춘 자리의 표 | `and`/`or` 의 반환값 | `type(1 and 2)` 가 `int` |
| 「비어 있으면 거짓」 규칙 | `__len__` | 빈 리스트·빈 문자열이 거짓 |
| 「내가 직접 답하겠다」 | `__bool__` | 있으면 `__len__` 보다 **먼저** 불린다 |
| 아무 규칙도 없으면 참 | 기본값 | 그냥 만든 객체는 참이다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리는 하나로 굳어 있다.\
**`x or 기본값`** 이라는 관용구가 `x` 가 `0`·`""`·`[]` 일 때 **배신한다.**\
사용자가 수량 `0` 을 입력했는데 기본값 `1` 이 들어가고, 이름을 빈 문자열로 지웠는데 옛 이름이 살아난다.\
전부 「**0 과 빈 것도 거짓이다**」와 「**`or` 는 피연산자를 돌려준다**」 둘의 결합이다.

> **진릿값(truth value)** — `if` 나 `while` 이 그 객체를 참으로 볼지 거짓으로 볼지.\
> 예: 빈 리스트는 `False` 가 아니지만 `if []:` 는 안 들어간다. **같은 것이 아니다.**

> **단축 평가(short-circuit)** — 앞만 보고 답이 정해지면 뒤를 **아예 실행하지 않는** 것.\
> 예: `False and f()` 에서 `f()` 는 호출조차 안 된다. 그 안의 `print` 도 안 찍힌다.

## 이 주제가 답하려는 질문

1. **무엇이 거짓인가** — `0`·`""`·`[]` 가 거짓인 것과, 내가 만든 클래스가 거짓이 되게 하는 법.
2. **`and`/`or` 가 무엇을 돌려주나** — `bool` 이 아니면 무엇이고, 그 성질에 기댄 `x or 기본값` 은 언제 배신하나.
3. **무엇이 안 돌아가나** — 단축 평가·비교 체이닝이 건너뛰는 것을 `dis` 로 어떻게 확인하나.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. 진릿값 판정 — `__bool__` 이 `__len__` 보다 먼저다

**언제 쓰나** — `if obj:` 라고 쓸 때마다. 직접 만든 클래스에서 특히.

문서의 규정 한 문장이 전부다 —\
*"By default, an object is considered true unless its class defines either a `__bool__()` method that returns `False` or a `__len__()` method that returns zero, when called with the object."*

```text
 if obj:  를 만나면

   obj 의 클래스에 __bool__ 이 있나?
        |
        +-- 예 --> 그것을 부른다. 끝. (__len__ 은 안 본다)
        |
        +-- 아니오 --> __len__ 이 있나?
                          |
                          +-- 예 --> 0 이면 거짓, 아니면 참
                          |
                          +-- 아니오 --> 참  (기본값)
```

```python
class Both:
    def __bool__(self):
        print("  __bool__ 불림"); return False
    def __len__(self):
        print("  __len__ 불림"); return 10

class OnlyLen:
    def __len__(self):
        print("  __len__ 불림"); return 0

class Neither:
    pass

print("Both:", bool(Both()))
print("OnlyLen:", bool(OnlyLen()))
print("Neither:", bool(Neither()))
```

```text
  __bool__ 불림
Both: False
  __len__ 불림
OnlyLen: False
Neither: True
```

그림 해설.

- `Both` 에서 **`__len__` 이 한 번도 안 찍혔다.** `__bool__` 이 있으면 `__len__` 은 쳐다보지도 않는다.\
  「길이가 10 이니 참이겠지」가 틀린다.
- `Neither` 는 아무 규칙이 없으니 **참**이다. 그래서 그냥 만든 객체는 언제나 참이다.
- 이 순서를 모르면, 컨테이너 클래스에 `__bool__` 을 실수로 달았을 때 **비어 있지 않은데 거짓**이 된다.

**거짓인 것들은 문서가 목록으로 적는다**

```python
print("빈 것들:", [bool(v) for v in (0, 0.0, 0j, "", [], (), {}, set(), frozenset(), range(0), None, False)])
print("참인 것들:", [bool(v) for v in (1, -1, 0.1, "0", "False", [0], (0,), {0:0}, {0}, range(1))])
```

```text
빈 것들: [False, False, False, False, False, False, False, False, False, False, False, False]
참인 것들: [True, True, True, True, True, True, True, True, True, True]
```

★ **`"0"` 과 `"False"` 가 참이다.** 빈 문자열만 거짓이다 — 내용은 보지 않는다.\
★ **`[0]` 도 참이다.** 원소가 거짓이어도 「비어 있지 않음」이니 참이다.

```python
from decimal import Decimal
import fractions
print("Decimal('0'):", bool(Decimal("0")), " Fraction(0,5):", bool(fractions.Fraction(0,5)))
```

```text
Decimal('0'): False  Fraction(0,5): False
```

문서가 목록에 `Decimal(0)`·`Fraction(0, 1)` 을 직접 적어 두었다 — 「**어떤 수 타입이든 0**」이 거짓이다.

**반환값이 잘못되면 예외가 난다**

```python
class Bad:
    def __bool__(self): return 1
try:
    bool(Bad())
except TypeError as e:
    print("TypeError:", e)

class Len:
    def __len__(self): return -1
try:
    bool(Len())
except ValueError as e:
    print("ValueError:", e)
```

```text
TypeError: __bool__ should return bool, returned int
ValueError: __len__() should return >= 0
```

`__bool__` 은 **진짜 `bool`** 이어야 하고(`1` 도 거부된다), `__len__` 은 **음수를 못 낸다.**

**비용** — `if obj:` 한 줄로 「비었나」를 묻는 관용구가 공짜로 생긴다.\
대신 **`if obj:` 와 `if obj is not None:` 이 다른 질문**이 된다 — 이 차이가 이 주제의 값 전부다.

### 2. `and`/`or` 는 불린을 안 돌려준다

**언제 쓰나** — 조건을 이을 때마다. 그리고 `x or 기본값` 관용구를 쓸 때.

문서의 표는 이렇다.

| 연산 | 결과 |
|---|---|
| `x or y` | if *x* is true, then *x*, else *y* |
| `x and y` | if *x* is false, then *x*, else *y* |
| `not x` | if *x* is false, then `True`, else `False` |

**`not` 만 불린을 돌려준다.** 앞의 둘은 **피연산자 자체**를 돌려준다.

```text
 x or y                                x and y
  x 가 참이면 x 를 준다                   x 가 거짓이면 x 를 준다
  아니면 y 를 준다                        아니면 y 를 준다

  1 or 2   ->  1   (x 가 참)             1 and 2  ->  2   (x 가 참이라 y)
  0 or 2   ->  2   (x 가 거짓이라 y)      0 and 2  ->  0   (x 가 거짓)
```

```python
print("1 and 2 =", 1 and 2)
print("0 and 2 =", 0 and 2)
print("1 or 2  =", 1 or 2)
print("0 or 2  =", 0 or 2)
print("[] or {} =", [] or {}, type([] or {}).__name__)
print("'a' and 'b' and '' and 'd' =", repr('a' and 'b' and '' and 'd'))
print("None or 0 or '' =", repr(None or 0 or ''))
print("type(1 and 2):", type(1 and 2).__name__, " -- bool 이 아니다")
print("not 은 bool 을 돌려준다:", type(not 1).__name__, not 1, not 0)
```

```text
1 and 2 = 2
0 and 2 = 0
1 or 2  = 1
0 or 2  = 2
[] or {} = {} dict
'a' and 'b' and '' and 'd' = ''
None or 0 or '' = ''
type(1 and 2): int  -- bool 이 아니다
not 은 bool 을 돌려준다: bool False True
```

그림 해설.

- `'a' and 'b' and '' and 'd'` 가 `''` 다 — **첫 거짓에서 멈추고 그것을 돌려준다.** `'d'` 는 보지도 않았다.
- `None or 0 or ''` 가 `''` 다 — **전부 거짓이면 마지막 것**을 돌려준다.
- `type(1 and 2)` 가 `int` 다. **`bool` 로 바꾸고 싶으면 `bool(...)` 을 명시해야 한다.**

**★ `dis` 가 「돌려준다」를 눈으로 보여 준다**

```python
import dis
dis.dis(compile("r = a and b", "<and>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (a)
              4 COPY                     1
              6 POP_JUMP_IF_FALSE        2 (to 12)
              8 POP_TOP
             10 LOAD_NAME                1 (b)
        >>   12 STORE_NAME               2 (r)
             14 RETURN_CONST             0 (None)
```

```text
 명령                     무슨 일인가
 ----------------------  -------------------------------------------
 LOAD_NAME a             a 를 스택에 올린다
 COPY 1                  a 를 한 벌 더 쌓는다  <- "돌려줄 값" 을 남겨 두는 것
 POP_JUMP_IF_FALSE -> 12 거짓이면 a 를 남긴 채 STORE 로 건너뛴다
 POP_TOP                 참이면 a 를 버리고
 LOAD_NAME b             b 를 올린다
 STORE_NAME r            스택 맨 위를 r 에 저장
```

**`bool` 로 바꾸는 명령이 어디에도 없다.** `a` 나 `b` 중 하나가 그대로 저장된다.\
`or` 는 점프 조건만 반대다.

```python
dis.dis(compile("r = a or b", "<or>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (a)
              4 COPY                     1
              6 POP_JUMP_IF_TRUE         2 (to 12)
              8 POP_TOP
             10 LOAD_NAME                1 (b)
        >>   12 STORE_NAME               2 (r)
             14 RETURN_CONST             0 (None)
```

**비용** — 조건 이음과 기본값 지정을 한 연산자로 겸할 수 있다.\
대신 **반환 타입이 피연산자 타입**이라, 불린을 기대한 코드가 조용히 틀린 타입을 받는다.

### 3. `x or 기본값` 이 배신하는 자리

**언제 쓰나** — 「값이 없으면 기본값」을 쓰려 할 때. 이 주제에서 값이 가장 몰리는 자리다.

```text
 의도                                  실제 판정 기준
 "값이 주어지지 않았으면 기본값"          "값이 거짓이면 기본값"
        |                                      |
        v                                      v
   None 만 걸러야 한다                    0, "", [], 0.0 까지 다 걸린다
```

```python
def default_bad(x):
    return x or "기본값"
def default_good(x):
    return x if x is not None else "기본값"

for v in (None, 0, "", [], "값", 5):
    print(f"x={v!r:6} or 관용구 -> {default_bad(v)!r:10} is not None 판 -> {default_good(v)!r}")
```

```text
x=None   or 관용구 -> '기본값'      is not None 판 -> '기본값'
x=0      or 관용구 -> '기본값'      is not None 판 -> 0
x=''     or 관용구 -> '기본값'      is not None 판 -> ''
x=[]     or 관용구 -> '기본값'      is not None 판 -> []
x='값'    or 관용구 -> '값'        is not None 판 -> '값'
x=5      or 관용구 -> 5          is not None 판 -> 5
```

그림 해설.

- **`None` 줄만 두 판의 답이 같다.** 나머지 세 줄(`0`·`""`·`[]`)에서 갈린다.
- `x=0` 일 때 `or` 관용구는 `'기본값'` 을 준다 — **사용자가 일부러 넣은 0 이 사라졌다.**
- `x=''` 도 마찬가지다 — **이름을 지운 것이 「안 바꿨다」로 읽힌다.**
- 고치는 법은 **질문을 바꾸는 것**이다 — 「거짓인가」가 아니라 「**`None` 인가**」를 묻는다.

```text
 배신하는 판                            고친 판
  return x or 기본값                    return x if x is not None else 기본값
   "거짓이면" 기본값                      "None 이면" 기본값
```

**테스트가 통과하는 이유**

테스트에 쓰는 값은 대개 `"test"`·`42` 같은 **참인 값**이다.\
`0`·`""`·`[]` 가 유효한 입력인 도메인(수량·검색어·필터 목록)에서만 터진다.

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 주문 수량 `0` 이 기본값 `1` 로 바뀌어도 아무 로그가 안 남는다. 재고가 하나 빠진 뒤에야 안다.

**비용** — `x or 기본값` 은 짧고 읽기 좋다. 참·거짓으로 판정하는 것이 **정말 의도일 때**는 옳은 코드다.\
대신 **「없음」과 「비어 있음」을 구별해야 하면 못 쓴다.**

### 4. 단축 평가는 부작용까지 건너뛴다

**언제 쓰나** — `and`/`or` 뒤에 함수 호출을 둘 때. 방어 코드의 관용구다.

```text
 False and f()                         True or f()
   앞이 거짓이면 답이 정해졌다             앞이 참이면 답이 정해졌다
   -> f() 는 호출조차 안 된다             -> f() 는 호출조차 안 된다
   -> f 안의 print 도 안 찍힌다
```

```python
def loud(name, ret):
    print(f"  {name} 평가됨")
    return ret

print("False and loud:", False and loud("A", True))
print("True or loud:", True or loud("B", True))
print("True and loud:", True and loud("C", "C결과"))
```

```text
False and loud: False
True or loud: True
  C 평가됨
True and loud: C결과
```

그림 해설.

- 첫 두 줄에서 **`평가됨` 이 안 찍혔다.** 「출력 없음」이 여기서는 **가장 강한 근거**다.
- 셋째 줄에서만 찍혔다 — 앞이 참이라 뒤를 봐야 했기 때문이다.
- 2번 절의 `dis` 에 답이 있다. `POP_JUMP_IF_FALSE` 가 **`LOAD_NAME b` 를 건너뛰어** `STORE_NAME` 으로 바로 간다.

**그래서 방어 코드가 성립한다**

```python
a = None
print("a is not None and len(a):", a is not None and len(a))
```

```text
a is not None and len(a): False
```

`len(None)` 은 `TypeError` 인데 **호출되지 않았다.** 이것이 단축 평가에 기댄 가장 흔한 관용구다.\
★ 그리고 이 코드의 반환값은 `False`(`a is not None` 의 결과)이지 `0` 이 아니다 — 2번 절의 성질이 여기서도 작동한다.

**비용** — 비싼 검사·안전하지 않은 호출을 조건 뒤로 미룰 수 있다.\
대신 **부작용이 있는 함수를 `and`/`or` 뒤에 두면 실행될 때와 안 될 때가 생긴다.** 로그·카운터가 조용히 빠진다.

### 5. 비교 체이닝 — `a < b < c` 는 `b` 를 한 번만 본다

**언제 쓰나** — 범위 검사를 쓸 때. 그리고 그것이 안전한지 물을 때.

문서가 정의한다 —\
*"Comparisons can be chained arbitrarily, e.g., `x < y <= z` is equivalent to `x < y and y <= z`, **except that `y` is evaluated only once** (but in both cases `z` is not evaluated at all when `x < y` is found to be false)."*

```text
 a < b < c                             a < b and b < c
  b 를 한 번만 평가한다                   b 를 두 번 평가한다
  (부작용이 있으면 한 번만 일어난다)        (두 번 일어난다)
```

```python
def loud(name, v):
    print(f"  {name} 평가됨")
    return v

print("체이닝 1 < loud < 100:")
print(" 결과:", 1 < loud("b", 0) < 100)
print()
print("and 로 쓰면 b 가 두 번:")
print(" 결과:", 1 < loud("b", 0) and loud("b", 0) < 100)
```

```text
체이닝 1 < loud < 100:
  b 평가됨
 결과: False

and 로 쓰면 b 가 두 번:
  b 평가됨
 결과: False
```

★ **이 실험은 여기서 결론이 안 선다.** `1 < 0` 이 거짓이라 `and` 판도 **단축 평가로 한 번만** 찍혔다.\
갈리는 자리를 찾아 앞을 참으로 만들어야 한다.

```python
print("체이닝 3 < loud(5) < 100:")
print(" 결과:", 3 < loud("b", 5) < 100)
print()
print("and 판:")
print(" 결과:", 3 < loud("b", 5) and loud("b", 5) < 100)
```

```text
체이닝 3 < loud(5) < 100:
  b 평가됨
 결과: True

and 판:
  b 평가됨
  b 평가됨
 결과: True
```

**여기서 갈렸다** — 체이닝은 한 번, `and` 판은 두 번이다.

**`dis` 로 보면 무엇이 절약되는지 보인다**

```python
import dis
dis.dis(compile("r = a < b < c", "<chain>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (a)
              4 LOAD_NAME                1 (b)
              6 SWAP                     2
              8 COPY                     2
             10 COMPARE_OP               2 (<)
             14 COPY                     1
             16 POP_JUMP_IF_FALSE        6 (to 30)
             18 POP_TOP
             20 LOAD_NAME                2 (c)
             22 COMPARE_OP               2 (<)
             26 STORE_NAME               3 (r)
             28 RETURN_CONST             0 (None)
        >>   30 SWAP                     2
             32 POP_TOP
             34 STORE_NAME               3 (r)
             36 RETURN_CONST             0 (None)
```

```python
dis.dis(compile("r = a < b and b < c", "<and>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (a)
              4 LOAD_NAME                1 (b)
              6 COMPARE_OP               2 (<)
             10 COPY                     1
             12 POP_JUMP_IF_FALSE        5 (to 24)
             14 POP_TOP
             16 LOAD_NAME                1 (b)
             18 LOAD_NAME                2 (c)
             20 COMPARE_OP               2 (<)
        >>   24 STORE_NAME               3 (r)
             26 RETURN_CONST             0 (None)
```

- 체이닝 쪽은 `LOAD_NAME b` 가 **한 번**이다. `COPY 2` 로 스택에 쟁여 두고 재사용한다.
- `and` 쪽은 `LOAD_NAME b` 가 **두 번**(오프셋 4 와 16)이다.
- ★ 그런데 체이닝 쪽은 **`SWAP`·`COPY` 가 늘고 분기 끝이 둘**이다 — 스택 정리(`SWAP 2; POP_TOP`)가 필요하기 때문이다.\
  **「더 짧다」가 아니라 「`b` 를 한 번만 본다」가 체이닝의 값**이다.

**★ 체이닝이 함정이 되는 자리**

```python
print("False == False in [False]   =", False == False in [False])
print("(False == False) in [False] =", (False == False) in [False])
print("False == (False in [False]) =", False == (False in [False]))
```

```text
False == False in [False]   = True
(False == False) in [False] = False
False == (False in [False]) = False
```

`==` 와 `in` 이 **둘 다 비교 연산자라 체이닝된다.**\
`False == False in [False]` 는 `(False == False) and (False in [False])` 이고 둘 다 참이라 `True` 다.\
괄호를 어떻게 치든 그 값이 안 나온다 — **체이닝은 괄호로 대체할 수 없는 제3의 해석**이다.

체이닝은 방향이 섞여도 된다.

```python
print("1 < 2 < 3  :", 1 < 2 < 3)
print("3 > 2 > 1  :", 3 > 2 > 1)
print("1 < 3 > 2  :", 1 < 3 > 2, " <- 같은 방향이 아니어도 된다")
```

```text
1 < 2 < 3  : True
3 > 2 > 1  : True
1 < 3 > 2  : True  <- 같은 방향이 아니어도 된다
```

**비용** — 범위 검사를 수학 표기 그대로 쓸 수 있고 중간 값을 한 번만 평가한다.\
대신 **`==`·`in`·`is` 까지 체이닝되므로** 의도하지 않은 결합이 생긴다.

### 6. `in` 도 단축한다 — 그리고 `is` 를 먼저 본다

**언제 쓰나** — 리스트에서 값을 찾을 때. `__eq__` 가 비싼 객체면 차이가 크다.

```python
class Loud:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        print(f"  {self.n} 과 == 비교")
        return self.n == getattr(other, "n", None)
    def __repr__(self): return f"L{self.n}"

a, b, c = Loud(1), Loud(2), Loud(3)
box = [a, b, c]
print("b in box:", b in box)
print()
print("c in box:", c in box)
```

```text
  1 과 == 비교
b in box: True

  1 과 == 비교
  2 과 == 비교
c in box: True
```

그림 해설.

- `b in box` 에서 비교가 **한 번**만 찍혔다. 0번 원소에서 실패하고 1번에서 **`is` 로 맞았기 때문**이다.\
  언어 레퍼런스가 규정한다 — 컨테이너에서 `x in y` 는 `any(x is e or x == e for e in y)` 와 같다([02번](../02-is-vs-eq-interning/2-summary.md) 정본).
- `c in box` 는 두 번 찍히고 셋째에서 `is` 로 맞았다.
- **찾으면 즉시 멈춘다.** 뒤 원소는 건드리지 않는다.

**★ 여기서 브리핑 전제 하나가 뒤집혔다 — 어느 쪽 `__eq__` 가 불리나**

```python
class Elem:
    def __eq__(self, other):
        print("  원소(리스트 안)의 __eq__ 가 불렸다"); return False
class Probe:
    def __eq__(self, other):
        print("  찾는 값의 __eq__ 가 불렸다"); return False

print("Probe() in [Elem()] :", Probe() in [Elem()])
print()
print("tuple 에서도:", Probe() in (Elem(),))
```

```text
  원소(리스트 안)의 __eq__ 가 불렸다
Probe() in [Elem()] : False

  원소(리스트 안)의 __eq__ 가 불렸다
tuple 에서도: False
```

문서의 동등식은 `x == e` 라고 적지만, **이 구현은 `e == x` 로 평가한다** — 리스트 **원소**의 `__eq__` 가 먼저 불린다.\
`__eq__` 가 대칭이면 결과가 같으므로 드러나지 않는다. **비대칭 `__eq__` 를 쓸 때만 갈린다.**\
★ 이것은 **CPython 의 관찰**이지 명세가 아니다. 문서의 동등식은 「결과가 같다」는 뜻이지 「호출 순서가 같다」는 뜻이 아니다.

**비용** — 찾으면 멈추므로 평균 비용이 절반이다.\
대신 **`__eq__` 가 부작용을 가지면** 몇 번 불릴지 예측이 안 된다.

### 7. `all([])` 이 `True` 인 이유

**언제 쓰나** — 검증 함수를 `all(...)` 로 쓸 때. **빈 입력이 들어오는 날**.

```text
 any: "하나라도 참인 게 있나?"          all: "거짓인 게 하나도 없나?"
   빈 것에서 찾을 게 없다                빈 것에는 거짓도 없다
   -> False                            -> True

 문서 표현:  any  "If the iterable is empty, return False."
             all  "If the iterable is empty, return True."
```

```python
print("all([]) =", all([]), "  any([]) =", any([]))
print("all 은 bool 을 돌려준다:", type(all([1,2])).__name__, all([1,2]))
print("any 결과도 bool:", type(any([3])).__name__, any([3]))
```

```text
all([]) = True   any([]) = False
all 은 bool 을 돌려준다: bool True
any 결과도 bool: bool True
```

★ **`any`/`all` 은 `and`/`or` 와 달리 진짜 `bool` 을 돌려준다.** 헷갈리기 쉬운 자리다.

둘 다 단축 평가한다.

```python
def gen(name):
    for v in [0, 0, 1, 0]:
        print(f"  {name}: {v} 꺼냄")
        yield v
print("any:", any(gen("any")))
print("all:", all(gen("all")))
```

```text
  any: 0 꺼냄
  any: 0 꺼냄
  any: 1 꺼냄
any: True
  all: 0 꺼냄
all: False
```

- `any` 는 **첫 참**에서 멈춘다 — 네 개 중 셋만 꺼냈다.
- `all` 은 **첫 거짓**에서 멈춘다 — 하나만 꺼냈다.
- 제너레이터를 넘기면 남은 원소는 **만들어지지도 않는다**([17-generators-yield](../17-generators-yield/2-summary.md)).

그림 해설.

- `all([])` 이 참인 것은 규약이 아니라 **정의에서 따라 나온다** — 「반례가 하나도 없다」가 참이기 때문이다.
- 그래서 **「검증 통과」와 「검증할 것이 없었다」가 구별되지 않는다.** 입력이 비었는지 따로 확인해야 한다.

```python
items = []
print("검증 통과?", all(x > 0 for x in items))
print("검증할 게 있었나?", bool(items))
```

```text
검증 통과? True
검증할 게 있었나? False
```

**비용** — 단축 평가 덕에 큰 입력에서 싸다.\
대신 **빈 입력이 `all` 을 무조건 통과시킨다.** 권한 검사·유효성 검사에서 실제 사고가 난다.

## 문법 — 형태와 규칙

```python
if obj: ...             # 진릿값 판정 — __bool__ -> __len__ -> 참
if obj is not None: ... # "없음" 판정 — 이쪽이 다른 질문이다
x or default            # x 가 "거짓" 이면 default  (None 만이 아니다)
x if x is not None else default   # x 가 None 일 때만 default
a and b                 # a 가 거짓이면 a, 아니면 b  (bool 이 아니다)
not a                   # 언제나 bool
a < b < c               # a < b and b < c, 단 b 는 한 번만 평가
x in seq                # any(x is e or x == e for e in seq) — is 를 먼저 본다
any(it) / all(it)       # bool 을 돌려준다. 빈 것은 False / True

class C:
    def __bool__(self): return False   # 반드시 bool 을 돌려줘야 한다
    def __len__(self): return 0        # 음수를 돌려주면 ValueError
```

규칙은 여섯이다.

1. **진릿값 판정 순서는 `__bool__` → `__len__` → 참**이다. 앞이 있으면 뒤는 안 본다.
2. **거짓인 것은 `None`·`False`·모든 수 타입의 0·빈 시퀀스와 컬렉션**뿐이다.\
   `"0"`·`"False"`·`[0]` 은 **참**이다.
3. **`and`/`or` 는 피연산자를 돌려준다.** `not`·`any`·`all` 만 `bool` 을 돌려준다.
4. **단축 평가는 뒤 피연산자를 아예 실행하지 않는다.** 부작용도 안 일어난다.
5. **비교는 체이닝된다.** `==`·`<`·`in`·`is` 가 전부 대상이라 의도하지 않은 결합이 생긴다.\
   중간 피연산자는 **한 번만** 평가된다.
6. **`all([])` 은 `True`, `any([])` 는 `False`** 다. 빈 입력을 따로 확인해야 한다.

## 어디서 틀리나

### (1) `x or 기본값` 이 `0` 과 `""` 를 삼킨다

```python
def order(qty=None):
    qty = qty or 1
    return qty
print(order(0))     # 1   <- 0 을 넣었는데 1 이 됐다
```

**이 주제 최대의 자리다.** 고치는 법은 `qty if qty is not None else 1`.

### (2) `and`/`or` 의 결과를 불린으로 믿는다

```python
flag = "" or []
print(flag, type(flag).__name__)      # [] list
import json
print(json.dumps({"ok": 1 and 2}))    # {"ok": 2}   <- true 가 아니다
```

API 응답·JSON 에 그대로 실리면 **클라이언트가 타입 오류를 본다.** `bool(...)` 로 감싼다.

### (3) `if x == True:` 로 검사한다

```python
print(1 == True, [1] == True, bool([1]))    # True False True
```

`[1]` 은 **참인데** `== True` 는 거짓이다. 진릿값 판정과 `==` 는 다른 질문이다.\
`if x:` 를 쓴다.

### (4) `__bool__` 을 달아 놓고 `__len__` 이 작동할 거라 믿는다

```python
class Box:
    def __init__(self, items): self.items = items
    def __len__(self): return len(self.items)
    def __bool__(self): return self.items is not None   # 실수로 추가

b = Box([])
print(len(b), bool(b))     # 0 True   <- 비었는데 참이다
```

`__bool__` 이 있으면 `__len__` 은 **쳐다보지도 않는다.**

### (5) `all()` 로 검증했는데 입력이 비어 있었다

```python
def all_positive(nums):
    return all(n > 0 for n in nums)
print(all_positive([]))      # True   <- 검증할 게 없었는데 통과다
```

「통과」와 「검증 대상 없음」이 같은 값으로 나온다. **`nums` 가 비었는지 따로 본다.**

### (6) 비교 체이닝이 의도하지 않게 붙는다

```python
print(False == False in [False])      # True
print(1 in [1] == True)               # False
```

`in` 과 `==` 가 체이닝돼 **괄호로는 재현 안 되는 해석**이 된다.\
서로 다른 비교를 한 줄에 이을 때는 **괄호를 명시**한다.

### (7) 단축 평가 뒤에 부작용을 둔다

```python
logged = []
def log(msg):
    logged.append(msg)
    return True

ok = False and log("검사 시작")
print(logged)     # []   <- 로그가 안 남았다
```

「로그는 항상 남겠지」가 틀린다. **출력 없음도 출력이다.**

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 거의 전부다** — 진릿값과 단축 평가는 명세가 촘촘하게 정한다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `dis` 로 확인 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 기본적으로 객체는 참이며, `__bool__` 이 `False` 를 내거나 `__len__` 이 0 을 낼 때만 거짓 | Truth Value Testing |
| 거짓인 내장 객체 목록 — `None`·`False`·모든 수 타입의 0·빈 시퀀스와 컬렉션 | Truth Value Testing |
| **`or` 와 `and` 는 언제나 피연산자 중 하나를 돌려준다** | Truth Value Testing (Important exception) |
| `x or y` 는 x 가 참이면 x, 아니면 y. `x and y` 는 x 가 거짓이면 x, 아니면 y | Boolean Operations 표 |
| `or`·`and` 는 **단축 연산자**다 — 필요할 때만 둘째 인자를 평가한다 | Boolean Operations 주 1·2 |
| `not` 은 `True`/`False` 를 돌려주고, 비불린 연산자보다 우선순위가 낮다 | Boolean Operations 주 3 |
| `x < y <= z` 는 `x < y and y <= z` 와 같되 **`y` 는 한 번만 평가**된다 | 언어 레퍼런스 6.10 |
| 컨테이너의 `x in y` 는 `any(x is e or x == e for e in y)` 와 같다 | 언어 레퍼런스 6.10.2 |
| `any` 는 빈 이터러블에서 `False`, `all` 은 `True` | `any()` / `all()` |
| 불린 결과를 내는 연산·내장 함수는 `0`/`False` 또는 `1`/`True` 를 돌려준다 | Truth Value Testing |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `a and b` 가 `COPY 1` + `POP_JUMP_IF_FALSE` 로 컴파일된다 | `dis` 출력 — **`bool` 변환 명령이 없다** |
| `a < b < c` 가 `SWAP`·`COPY 2` 로 중간 값을 쟁여 둔다 | `dis` 출력 |
| `x in [..]` 가 **리스트 원소의 `__eq__`** 를 먼저 부른다(`e == x`) | 비대칭 `__eq__` 두 클래스로 확인 |
| `__bool__` 반환 오류 문구가 `__bool__ should return bool, returned int` | 실행 |
| `__len__` 음수 오류가 `ValueError: __len__() should return >= 0` | 실행 |
| `__len__` 이 인덱스 크기를 넘으면 `OverflowError` | `2**63` 을 돌려주게 해서 확인 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| 명령 이름 `POP_JUMP_IF_FALSE`·`POP_JUMP_IF_TRUE`·`COMPARE_OP 2 (<)` | 판마다 이름·번호가 바뀐다 |
| 체이닝의 분기 끝이 둘(`SWAP 2; POP_TOP`)이라 명령 수가 더 많다 | 컴파일러 최적화에 달렸다 |
| 오류 메시지 문구 전부 | 예외 종류는 명세지만 문구는 아니다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`and`/`or` 는 `True`/`False` 를 돌려준다」\
  → **피연산자를 돌려준다.** 문서가 *"Important exception"* 으로 따로 못 박는다.
- ✗ 「`x or 기본값` 은 값이 없을 때 기본값을 쓴다」\
  → **거짓일 때** 쓴다. `0`·`""`·`[]` 가 전부 걸린다.
- ✗ 「`__len__` 이 0 이면 언제나 거짓이다」\
  → `__bool__` 이 있으면 **`__len__` 은 안 본다.**
- ✗ 「`all([])` 이 `True` 인 건 파이썬의 이상한 규약이다」\
  → **정의에서 따라 나온다.** 문서가 명시적으로 적는다.
- ✗ 「`x in y` 는 `x.__eq__(e)` 를 부른다」\
  → **이 구현은 `e == x` 로 평가한다.** 문서의 동등식은 결과에 대한 것이지 호출 순서에 대한 것이 아니다.

**판정 기준 한 줄**: **「참인가」와 「있는가」는 다른 질문이다.** 코드가 둘을 섞고 있으면 그 자리가 버그 후보다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `if x:` | 「비어 있나 / 0 인가」를 **정말로** 묻고 싶을 때 |
| `if x is not None:` | 「값이 주어졌나」를 물을 때. **`0`·`""` 가 유효한 값이면 언제나 이쪽** |
| `x or 기본값` | 거짓 값 전부를 기본값으로 바꾸는 게 **의도일 때**만 |
| `x if x is not None else 기본값` | 그 밖의 전부 |
| `a is not None and f(a)` | 안전하지 않은 호출을 조건 뒤로 미룰 때 |
| `lo <= x <= hi` | 범위 검사. 중간 값이 비싸면 특히 이득 |
| `any(...)` / `all(...)` | 여러 조건을 모을 때. **`all` 은 빈 입력을 따로 확인** |
| `bool(...)` | API·JSON 으로 나갈 값을 불린으로 고정할 때 |

**안 쓰는 자리**는 둘이다.\
**`x or 기본값` 을 습관으로 쓰지 마라** — `None` 만 걸러야 하면 다른 표현이 필요하다.\
**`and`/`or` 뒤에 부작용 있는 호출을 두지 마라** — 실행될 때와 안 될 때가 생긴다.

## 핵심 문장

- 진릿값 판정은 **`__bool__` → `__len__` → 참** 순서다. 앞이 있으면 뒤는 쳐다보지 않는다.
- 거짓인 것은 `None`·`False`·**모든 수 타입의 0**·빈 시퀀스와 컬렉션뿐이다. `"0"`·`[0]` 은 참이다.
- **`and`/`or` 는 불린을 안 돌려준다** — 마지막으로 평가한 피연산자를 준다. `dis` 에 `bool` 변환 명령이 아예 없다.
- 그래서 **`x or 기본값` 은 `x` 가 `0`·`""`·`[]` 일 때 배신한다.** 고치는 법은 질문을 바꾸는 것 — `x if x is not None else 기본값`.
- 단축 평가는 **부작용까지 건너뛴다.** 「출력 없음」이 그 증거다.
- 비교는 체이닝된다 — `a < b < c` 는 `b` 를 **한 번만** 평가하고, `==`·`in` 까지 체이닝돼 **괄호로 재현 안 되는 해석**을 만든다.
- **`all([])` 은 `True`** 다. 「통과」와 「검증할 것이 없었다」가 같은 값으로 나온다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **05번**
- 선행: [목록의 **04번 주제**](../04-numeric-types-and-division/) 「숫자 타입과 나눗셈 연산자」 — `bool` 이 `int` 의 하위 클래스라는 것이 거기 정본이다. 여기서는 **진릿값 판정이 그것과 다른 규칙**임을 다룬다.
- 이어지는 곳: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — `in` 이 `is` 를 먼저 본다는 규정과 `True == 1` 의 정본.
- 이어지는 곳: [17-generators-yield](../17-generators-yield/2-summary.md) — `any`/`all` 에 제너레이터를 넘겼을 때 남은 원소가 만들어지지도 않는 것.
- 이어지는 곳: [목록의 **03번 주제**](../03-mutability-and-copying/) — 빈 컨테이너가 거짓이라는 성질이 「가변 기본값을 `None` 으로 바꾸는」 관용구와 맞물린다.
- 이어지는 곳: 목록의 **30번 주제** 「`__repr__`·`__eq__`·`__hash__` 계약」 — 비대칭 `__eq__` 가 `in` 에서 무엇을 만드는지.
- 이어지는 곳: 목록의 **32번 주제** 「컨테이너 프로토콜」 — `__len__`·`__contains__` 를 직접 구현할 때의 계약.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 연산자·제어문 소개.\
  **경계**: 그쪽은 「이렇게 쓴다」까지, 여기는 「**`and`/`or` 가 무엇을 돌려주고 어디서 배신하나**」부터다.
- 연혁은 여기가 아니다: [`history/python/`](../../../../../../history/python/)
- 공식 문서: [Truth Value Testing](https://docs.python.org/3.12/library/stdtypes.html#truth-value-testing) · [Boolean Operations](https://docs.python.org/3.12/library/stdtypes.html#boolean-operations-and-or-not) · [6.10. Comparisons](https://docs.python.org/3.12/reference/expressions.html#comparisons)

## 용어 풀이

- **진릿값(truth value)**: `if`·`while` 이 그 객체를 참으로 볼지 거짓으로 볼지.\
  객체가 `True`/`False` **인** 것과 다르다 — `[1] == True` 는 거짓이지만 `bool([1])` 은 참이다.
- **`__bool__`**: 객체가 자기 진릿값을 직접 정하는 메서드.\
  **반드시 `bool` 을 돌려줘야 한다.** `1` 을 돌려주면 `TypeError` 다.
- **`__len__`**: 길이를 돌려주는 메서드. `__bool__` 이 없을 때 진릿값 판정에도 쓰인다.\
  음수를 돌려주면 `ValueError` 다.
- **단축 평가(short-circuit)**: 앞만 보고 답이 정해지면 뒤를 **아예 실행하지 않는** 것.\
  뒤에 있던 함수 호출·출력·로그가 전부 안 일어난다.
- **피연산자(operand)**: 연산자가 받는 값. `1 and 2` 에서 `1` 과 `2`.\
  `and`/`or` 는 **연산 결과가 아니라 이 피연산자 중 하나**를 돌려준다.
- **비교 체이닝(chained comparison)**: `a < b < c` 처럼 비교를 잇는 문법.\
  `a < b and b < c` 와 같되 `b` 를 한 번만 평가한다. `==`·`in`·`is` 도 대상이다.
- **`any` / `all`**: 이터러블의 진릿값을 모으는 내장 함수.\
  **`bool` 을 돌려준다**(`and`/`or` 와 다르다). 빈 입력에서 각각 `False`/`True`.
- **센티널(sentinel)**: 「값이 없음」을 나타내려고 일부러 만든 표식.\
  `None` 자체가 유효한 값일 때 `MISSING = object()` 를 만들어 `is` 로 판정한다([20번](../20-mutable-default-args/2-summary.md)).
- **조용한 실패(silent failure)**: 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
  `x or 기본값` 이 `0` 을 삼키는 것이 대표다.
- **`POP_JUMP_IF_FALSE`**: 스택 맨 위가 거짓이면 지정 위치로 건너뛰는 바이트코드 명령(3.12).\
  단축 평가가 이 한 줄로 구현된다.

## 더 들어가면

- **`operator.truth(x)`** 가 `bool(x)` 와 같은 일을 한다 — 함수로 넘겨야 할 때 쓴다.
- **`if x:` 와 `if len(x):` 는 성능이 다를 수 있다.** 앞엣것은 `__bool__`/`__len__` 을 직접 부르고, 뒤엣것은 정수를 만든 뒤 다시 판정한다. 의미도 다르다 — `__bool__` 이 있는 객체에서 갈린다.
- **`numpy` 배열은 `__bool__` 이 예외를 던진다.** 원소가 여럿인 배열에 `if arr:` 를 쓰면 *"The truth value of an array with more than one element is ambiguous"* 가 난다. 이 갈래의 규칙을 라이브러리가 **일부러 거부한** 사례다(이 문서에서는 실행 검증하지 않았다 — 이 환경에 `numpy` 가 없다).
- **`match` 문의 패턴은 진릿값 판정을 쓰지 않는다.** 구조 분해와 `==` 로 동작한다(목록의 **39번 주제**).
