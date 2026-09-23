# python/syntax/05-truthiness-and-short-circuit — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **바이트코드 명령 이름과 `in` 의 `__eq__` 호출 순서는 구현 세부사항**이라 다른 구현·다른 버전에서는 달라질 수 있다(8·10번 답).

## 정답

### 1. `__bool__` 과 `__len__` 중 누가 먼저인가 (예측)

**출력 — 세 줄이다**

```text
  __bool__ 불림
Both: False
Neither: True
```

★ **`__len__ 불림` 이 한 줄도 안 찍혔다.** 「출력 없음」이 여기서는 가장 강한 근거다.

**왜 그런가**

문서의 한 문장이 전부다 —\
*"By default, an object is considered true unless its class defines either a `__bool__()` method that returns `False` or a `__len__()` method that returns zero, when called with the object."*

```text
 if obj:  또는 bool(obj) 를 만나면

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

**세 단계로 말하면**

1. `__bool__` 이 있으면 그 결과가 답이다. **`__len__` 은 쳐다보지 않는다.**
2. 없고 `__len__` 이 있으면 **0 이면 거짓, 아니면 참**.
3. 둘 다 없으면 **참**. 그래서 그냥 만든 객체는 언제나 참이다.

**여기서 틀리는 자리**

```python
class Box:
    def __init__(self, items): self.items = items
    def __len__(self): return len(self.items)
    def __bool__(self): return self.items is not None   # 실수로 추가

b = Box([])
print(len(b), bool(b))
```

```text
0 True
```

**길이가 0 인데 참이다.** `__bool__` 이 앞을 막았기 때문이다.\
컨테이너 클래스를 만들 때는 `__len__` 만 두는 것이 안전하다.

**반환값에도 제약이 있다**

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

`__bool__` 은 **진짜 `bool`** 이어야 한다 — `1` 도 거부된다.\
`__len__` 은 음수를 못 낸다.

### 2. 무엇이 거짓인가 (예측)

**출력**

```text
[False, False, False, False, False, False, False, False, False, False]
[True, True, True, True, True, True]
True False True
```

**왜 그런가**

문서가 거짓인 내장 객체를 목록으로 적는다.

| 갈래 | 것들 |
|---|---|
| 거짓으로 정의된 상수 | `None` · `False` |
| **모든 수 타입의 0** | `0` · `0.0` · `0j` · `Decimal(0)` · `Fraction(0, 1)` |
| 빈 시퀀스·컬렉션 | `''` · `()` · `[]` · `{}` · `set()` · `range(0)` |

```text
 거짓                                  참
  0, 0.0, 0j                            1, -1, 0.1
  "", [], (), {}, set(), range(0)       "0", "False", [0], (0,), {0:0}, range(1)
  None, False
                                       ★ 내용은 안 본다.
                                          "비어 있나" 만 본다.
```

★ **`"0"` 과 `"False"` 가 참이다.** 문자열은 **비었는지만** 본다.\
★ **`[0]` 도 참이다.** 원소가 거짓이어도 리스트는 비어 있지 않다.\
설정 파일에서 읽은 `"False"` 를 `if flag:` 로 검사하면 **언제나 참**이 되는 사고가 여기서 난다.

수 타입 쪽도 재 봤다.

```python
from decimal import Decimal
import fractions
print("Decimal('0'):", bool(Decimal("0")), " Fraction(0,5):", bool(fractions.Fraction(0,5)))
```

```text
Decimal('0'): False  Fraction(0,5): False
```

**셋째 줄이 갈리는 이유 — 다른 질문이기 때문이다**

```text
 [1] == True                          bool([1])
  "[1] 과 True 가 같은 값인가?"          "[1] 을 참으로 볼 것인가?"
  리스트와 불린은 다른 값 -> False       비어 있지 않다 -> True
```

- `1 == True` 는 `True` 다 — `bool` 이 `int` 의 하위 클래스라서([04번](../04-numeric-types-and-division/2-summary.md)).
- `[1] == True` 는 `False` 다 — 리스트에 `int` 와의 동등 비교가 없다.
- `bool([1])` 은 `True` 다 — **진릿값 판정은 `==` 와 다른 규칙**이다.

**그래서 `if x == True:` 를 쓰지 않는다.** `if x:` 를 쓴다.

### 3. `and`/`or` 가 돌려주는 것 (예측)

**출력**

```text
2
2
''
''
int bool
```

**왜 그런가**

문서의 표가 답이다.

| 연산 | 결과 |
|---|---|
| `x or y` | if *x* is true, then *x*, else *y* |
| `x and y` | if *x* is false, then *x*, else *y* |
| `not x` | if *x* is false, then `True`, else `False` |

그리고 Truth Value Testing 절이 따로 못을 박는다 —\
*"(Important exception: the Boolean operations `or` and `and` always return **one of their operands**.)"*

```text
 1 and 2                              0 or 2
  1 이 참 -> 뒤를 봐야 한다              0 이 거짓 -> 뒤를 봐야 한다
  -> 2 를 돌려준다                      -> 2 를 돌려준다

 'a' and 'b' and '' and 'd'           None or 0 or ''
  첫 거짓 '' 에서 멈춘다                 전부 거짓이면
  -> ''  ('d' 는 보지도 않았다)          -> 마지막 것 '' 를 돌려준다
```

**`and`/`or` 와 `not` 이 갈리는 지점**

| 연산자 | 돌려주는 것 | 타입 |
|---|---|---|
| `and` · `or` | **피연산자 중 하나** | 피연산자의 타입 그대로 |
| `not` | 판정 결과 | 언제나 `bool` |
| `any` · `all` | 판정 결과 | 언제나 `bool` |

`type(1 and 2)` 가 `int`, `type(not 1)` 이 `bool` 인 것이 그 증거다.

**여기서 틀리는 자리**

```python
flag = "" or []
print(flag, type(flag).__name__)
import json
print(json.dumps({"ok": 1 and 2}))
```

```text
[] list
{"ok": 2}
```

JSON 에 `true` 가 아니라 `2` 가 실린다. **API 응답으로 나가면 클라이언트가 타입 오류를 본다.**\
불린으로 고정하려면 `bool(...)` 을 명시한다.

### 4. `x or 기본값` 은 언제 배신하나 (예측)

**출력**

```text
None 기본값 '기본값'
0 기본값 0
'' 기본값 ''
[] 기본값 []
'값' 값 '값'
5 5 5
```

**갈리는 줄 — 가운데 셋(`0`·`''`·`[]`)이다**

```text
 x        or 관용구      is not None 판
 ------   -----------   --------------
 None     '기본값'        '기본값'        <- 같다 (의도대로)
 0        '기본값'        0              <- 갈린다 ★
 ''       '기본값'        ''             <- 갈린다 ★
 []       '기본값'        []             <- 갈린다 ★
 '값'      '값'           '값'            <- 같다
 5        5             5              <- 같다
```

**왜 그런가 — 질문이 다르다**

```text
 의도                                  or 관용구가 실제로 묻는 것
 "값이 주어지지 않았으면 기본값"          "값이 거짓이면 기본값"
        |                                      |
        v                                      v
   None 만 걸러야 한다                    0, "", [], 0.0 까지 다 걸린다
```

- 수량 `0` 을 일부러 넣었는데 기본값 `1` 이 된다.
- 이름을 빈 문자열로 **지웠는데** 옛 이름이 살아난다.
- 필터 목록을 `[]`(전부 해제)로 보냈는데 기본 필터가 다시 켜진다.

```python
def order(qty=None):
    qty = qty or 1
    return qty
print(order(0))
```

```text
1
```

**질문을 바꾸는 것이 고치는 법**

```text
 배신하는 판                            고친 판
  return x or 기본값                    return x if x is not None else 기본값
   "거짓인가" 를 묻는다                   "None 인가" 를 묻는다
```

★ `None` 자체가 유효한 값인 API 라면 `None` 으로도 부족하다 — **센티널**을 만든다.

```python
MISSING = object()
def f(x=MISSING):
    return "기본값" if x is MISSING else x
print(f(), f(None), f(0))
```

```text
기본값 None 0
```

이 관용구의 정본은 [20-mutable-default-args](../20-mutable-default-args/2-summary.md) 다.

**왜 테스트가 통과하나**

테스트에 쓰는 값은 대개 `"test"`·`42` 같은 **참인 값**이다.\
`0`·`""`·`[]` 가 유효한 입력인 도메인(수량·검색어·필터)에서만 터진다. **그래서 늦게 발견된다.**

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 주문 수량 `0` 이 기본값 `1` 로 바뀌어도 로그가 안 남는다. 재고가 하나 빠진 뒤에야 안다.

### 5. 단축 평가가 건너뛰는 것 (예측)

**출력 — 다섯 줄이다**

```text
A: False
B: True
  C 평가됨
C: C결과
D: False
```

★ **`A 평가됨`·`B 평가됨` 이 없다.** 네 줄이 아니라 다섯 줄인 이유가 「C 만 찍혔기」 때문이다.

**왜 그런가**

```text
 False and loud(...)                  True or loud(...)
  앞이 거짓 -> 답이 정해졌다             앞이 참 -> 답이 정해졌다
  -> loud 는 호출조차 안 된다            -> loud 는 호출조차 안 된다
  -> 안의 print 도 안 돈다

 True and loud(...)
  앞이 참 -> 뒤를 봐야 한다  -> loud 가 호출된다
```

문서가 주석으로 적는다 — *"This is a short-circuit operator, so it only evaluates the second argument if the first one is false / true."*

2번 절의 `dis` 가 그 구현이다 — `POP_JUMP_IF_FALSE` 가 `LOAD_NAME b` 를 **건너뛰어** `STORE_NAME` 으로 바로 간다.

**D 줄이 안 터지는 이유**

```python
a = None
print("D:", a is not None and len(a))
```

```text
D: False
```

- `a is not None` 이 `False` 다 → **답이 정해졌으니 `len(a)` 를 호출하지 않는다.**
- `len(None)` 은 `TypeError: object of type 'NoneType' has no len()` 인데 **그 코드가 실행되지 않았다.**
- 이것이 단축 평가에 기댄 **가장 흔한 방어 관용구**다.

★ 그리고 이 줄의 값이 `False` 이지 `0` 이 아니다 — 3번 답의 성질이 여기서도 작동한다.\
`and` 가 **거짓인 앞 피연산자**(`a is not None` 의 결과 `False`)를 그대로 돌려준 것이다.

**여기서 틀리는 자리**

```python
logged = []
def log(msg):
    logged.append(msg)
    return True

ok = False and log("검사 시작")
print(logged)
```

```text
[]
```

**로그가 안 남았다.** 「로그는 항상 남겠지」가 틀린다 — 단축 평가는 부작용까지 건너뛴다.\
부작용이 있는 호출은 `and`/`or` 뒤에 두지 않는다.

### 6. 비교 체이닝 (예측)

**출력 — 여섯 줄이다**

```text
  b 평가됨
 결과: True
  b 평가됨
  b 평가됨
 결과: True
True
False False
```

★ **체이닝은 `b 평가됨` 이 한 번, `and` 판은 두 번이다.**

**왜 그런가**

문서가 정의한다 —\
*"Comparisons can be chained arbitrarily, e.g., `x < y <= z` is equivalent to `x < y and y <= z`, **except that `y` is evaluated only once** (but in both cases `z` is not evaluated at all when `x < y` is found to be false)."*

```text
 3 < loud(5) < 100                    3 < loud(5) and loud(5) < 100
  loud 를 한 번만 부른다                 loud 를 두 번 부른다
  (부작용이 한 번만 일어난다)             (두 번 일어난다)
```

★ **이 실험은 앞이 거짓이면 결론이 안 선다.** `1 < loud(0) < 100` 으로 재면 `and` 판도 **단축 평가로 한 번만** 찍혀 두 판이 같아 보인다.

```text
 1 < loud(0) < 100          -> b 평가됨 1회, False
 1 < loud(0) and loud(0)<100 -> b 평가됨 1회, False   <- 여기서는 구별 안 된다
```

**앞을 참으로 만들어야 갈린다.** 그래서 `3 < loud(5) < 100` 으로 던졌다.

**`dis` 가 절약되는 것을 보여 준다**

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

- 체이닝 쪽은 `LOAD_NAME b` 가 **한 번**(오프셋 4)이다. `COPY 2` 로 쟁여 두고 재사용한다.
- `and` 쪽은 **두 번**(오프셋 4 와 16)이다.
- ★ 그런데 체이닝 쪽은 `SWAP`·`COPY` 가 늘고 **분기 끝이 둘**이다(오프셋 30 이하의 스택 정리).\
  **「명령이 적다」가 아니라 「`b` 를 한 번만 본다」가 체이닝의 값**이다.

**셋째 줄이 어느 괄호와도 같지 않은 이유**

```text
 False == False in [False]
  ==  와  in  이 둘 다 비교 연산자다  ->  체이닝된다
  = (False == False) and (False in [False])
  =      True        and      True
  = True

 괄호를 치면 체이닝이 깨진다
  (False == False) in [False]   ->  True in [False]     ->  False
  False == (False in [False])   ->  False == True       ->  False
```

**체이닝은 괄호로 재현할 수 없는 제3의 해석**이다.\
`==`·`!=`·`<`·`>`·`in`·`not in`·`is`·`is not` 이 전부 대상이라 의도하지 않은 결합이 생긴다.

체이닝은 방향이 섞여도 된다.

```python
print("1 < 2 < 3  :", 1 < 2 < 3)
print("1 < 3 > 2  :", 1 < 3 > 2, " <- 같은 방향이 아니어도 된다")
```

```text
1 < 2 < 3  : True
1 < 3 > 2  : True  <- 같은 방향이 아니어도 된다
```

**서로 다른 비교를 한 줄에 이을 때는 괄호를 명시한다.**

### 7. `dis` 가 보여 주는 것 (왜)

**답: `bool` 로 바꾸는 명령이 **없다**는 사실이다.**

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

**두 경로 어디에도 변환이 없다**

```text
 a 가 거짓인 경로:  LOAD a -> COPY -> 점프 -> STORE r      저장되는 것은 a
 a 가 참인 경로:    LOAD a -> COPY -> POP -> LOAD b -> STORE r   저장되는 것은 b
```

- `POP_JUMP_IF_FALSE` 는 **판정만** 하고 그 결과를 스택에 남기지 않는다.\
  스택에 남는 것은 `COPY 1` 이 쟁여 둔 **원래 값**이다.
- 그래서 `r` 에는 `a` 나 `b` 가 **그대로** 들어간다.

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

**두 가지를 한 출력으로 증명한다**

1. **반환값** — 변환 명령이 없으니 피연산자가 그대로 나온다(3번 답).
2. **단축 평가** — 점프가 `LOAD_NAME b` 를 통째로 건너뛴다(5번 답).

★ 명령 **이름**은 3.12 의 것이라 판마다 바뀐다. **외울 것은 「변환 명령이 없다」는 성질**이다.

### 8. `in` 은 무엇을 먼저 보나 (경계)

**언제 멈추나 — 찾으면 즉시**

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

- `b in box` — 0번에서 `==` 가 한 번 불리고 실패, 1번에서 **`is` 로 맞아** 끝난다. 비교는 **한 번**이다.
- `c in box` — 0·1번에서 두 번 불리고, 2번에서 `is` 로 맞는다.
- 언어 레퍼런스가 규정한다 — 컨테이너에서 `x in y` 는 `any(x is e or x == e for e in y)` 와 같다.\
  **`is` 를 먼저 보므로** 같은 객체면 `__eq__` 가 아예 안 불린다([02번](../02-is-vs-eq-interning/2-summary.md) 정본).

**어느 쪽 `__eq__` 가 불리나 — 던져서 확인했다**

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

**리스트 원소의 `__eq__` 가 불린다.** 즉 이 구현은 `e == x` 로 평가한다 — 문서의 동등식(`x == e`)과 **좌우가 반대**다.

```text
 문서의 동등식                          이 구현의 실제 호출
  any(x is e or x == e for e in y)      e == x  로 평가한다
  -> 왼쪽이 찾는 값                      -> 왼쪽이 리스트 원소
```

**이것은 구현 관찰이지 언어 보장이 아니다**

| 무엇 | 지위 |
|---|---|
| `x in y` 의 **결과**가 `any(x is e or x == e ...)` 와 같다 | **언어 보장** |
| 그 안에서 **어느 쪽 `__eq__` 가 먼저 불리나** | **CPython 의 관찰** |

- 문서의 동등식은 「**결과**가 같다」는 뜻이지 「호출 순서가 같다」는 뜻이 아니다.
- `__eq__` 가 **대칭**이면 이 차이가 드러나지 않는다. **비대칭 `__eq__`·부작용 있는 `__eq__`** 에서만 갈린다.
- ★ 그래서 「`in` 은 내 객체의 `__eq__` 를 부른다」는 전제로 짠 코드(호출 횟수를 세거나 로그를 남기는)는 **여기서 어긋난다.**

### 9. `all([])` 이 `True` 인 것 (경계)

**출력**

```text
all([]) = True   any([]) = False
```

**정의에서 유도하면**

```text
 any: "참인 것이 하나라도 있나?"        all: "거짓인 것이 하나도 없나?"
   빈 것에는 찾을 게 없다                빈 것에는 반례도 없다
   -> 하나도 못 찾았다 -> False          -> 반례가 없다 -> True
```

문서도 그대로 적는다 — `any`: *"If the iterable is empty, return False."* · `all`: *"If the iterable is empty, return True."*

수학의 「공허참」과 같은 구조다 — 「이 빈 상자 안의 모든 사과는 빨갛다」는 참이다. 반박할 사과가 없기 때문이다.

★ **`any`/`all` 은 진짜 `bool` 을 돌려준다** — `and`/`or` 와 다르다.

```python
print("all 은 bool 을 돌려준다:", type(all([1,2])).__name__, all([1,2]))
print("any 결과도 bool:", type(any([3])).__name__, any([3]))
```

```text
all 은 bool 을 돌려준다: bool True
any 결과도 bool: bool True
```

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

`any` 는 **첫 참**에서, `all` 은 **첫 거짓**에서 멈춘다. 제너레이터를 넘기면 남은 원소는 **만들어지지도 않는다**([17-generators-yield](../17-generators-yield/2-summary.md)).

**검증 코드에서 무엇이 위험한가**

```python
def all_positive(nums):
    return all(n > 0 for n in nums)
print(all_positive([]))
```

```text
True
```

**「검증 통과」와 「검증할 것이 없었다」가 같은 값으로 나온다.**

```python
items = []
print("검증 통과?", all(x > 0 for x in items))
print("검증할 게 있었나?", bool(items))
```

```text
검증 통과? True
검증할 게 있었나? False
```

실제 사고가 나는 자리는 셋이다.

| 자리 | 빈 입력이 들어오면 |
|---|---|
| 권한 검사 — `all(user.has(p) for p in required)` | 필요한 권한 목록이 비면 **누구나 통과** |
| 유효성 검사 — `all(validate(f) for f in fields)` | 필드 목록이 비면 **검증 없이 통과** |
| 서명 검증 — `all(verify(s) for s in signatures)` | 서명이 하나도 없으면 **통과** |

**고치는 법**: `items and all(...)` 또는 `len(items) > 0 and all(...)` 로 **비었는지 따로 확인**한다.\
★ 앞엣것은 3번 답 때문에 `[]` 를 돌려줄 수 있다 — 불린이 필요하면 `bool(items) and all(...)`.

### 10. 세 층 가르기 (경계)

**① 언어 보장** — 레퍼런스가 정한 것. ★ **이 주제는 거의 전부가 여기에 속한다.**

| 사실 | 근거 |
|---|---|
| 기본적으로 객체는 참이며, `__bool__` 이 `False` 를 내거나 `__len__` 이 0 을 낼 때만 거짓 | Truth Value Testing |
| 거짓인 내장 객체 목록 — `None`·`False`·모든 수 타입의 0·빈 시퀀스와 컬렉션 | Truth Value Testing |
| **`or` 와 `and` 는 언제나 피연산자 중 하나를 돌려준다** | Truth Value Testing (Important exception) |
| `x or y` 는 x 가 참이면 x, 아니면 y. `x and y` 는 x 가 거짓이면 x, 아니면 y | Boolean Operations 표 |
| `or`·`and` 는 **단축 연산자**다 | Boolean Operations 주 1·2 |
| `not` 은 `True`/`False` 를 돌려주고 비불린 연산자보다 우선순위가 낮다 | Boolean Operations 주 3 |
| `x < y <= z` 는 `x < y and y <= z` 와 같되 **`y` 는 한 번만 평가**된다 | 언어 레퍼런스 6.10 |
| 컨테이너의 `x in y` 는 **결과가** `any(x is e or x == e for e in y)` 와 같다 | 언어 레퍼런스 6.10.2 |
| `any` 는 빈 이터러블에서 `False`, `all` 은 `True` | `any()` / `all()` |
| 불린 결과를 내는 연산·내장 함수는 `0`/`False` 또는 `1`/`True` 를 돌려준다 | Truth Value Testing |

**② CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| `a and b` 가 `COPY 1` + `POP_JUMP_IF_FALSE` 로 컴파일된다 — **`bool` 변환 명령이 없다** | `dis` 출력 |
| `a < b < c` 가 `SWAP`·`COPY 2` 로 중간 값을 쟁여 둔다 | `dis` 출력 |
| **`x in [..]` 가 리스트 원소의 `__eq__` 를 먼저 부른다**(`e == x`) | 비대칭 `__eq__` 두 클래스로 확인 |
| `__bool__` 반환 오류 문구가 `__bool__ should return bool, returned int` | 실행 |
| `__len__` 음수 오류가 `ValueError: __len__() should return >= 0` | 실행 |

**③ 이 판(3.12.3)의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| 명령 이름 `POP_JUMP_IF_FALSE`·`POP_JUMP_IF_TRUE`·`COMPARE_OP 2 (<)` | 판마다 이름·번호가 바뀐다 |
| 체이닝의 분기 끝이 둘이라 명령 수가 `and` 판보다 많다 | 컴파일러 최적화에 달렸다 |
| 오류 메시지 문구 전부 | 예외 종류는 명세지만 문구는 아니다 |

**그래서 이렇게 적으면 틀린다**

- ✗ 「`and`/`or` 는 `True`/`False` 를 돌려준다」\
  ○ **피연산자를 돌려준다.** 문서가 *"Important exception"* 으로 따로 못 박는다.
- ✗ 「`x or 기본값` 은 값이 없을 때 기본값을 쓴다」\
  ○ **거짓일 때** 쓴다. `0`·`""`·`[]` 가 전부 걸린다.
- ✗ 「`__len__` 이 0 이면 언제나 거짓이다」\
  ○ `__bool__` 이 있으면 **`__len__` 은 안 본다.**
- ✗ 「`all([])` 이 `True` 인 건 파이썬의 이상한 규약이다」\
  ○ **정의에서 따라 나오고**, 문서가 명시적으로 적는다.
- ✗ 「`x in y` 는 찾는 값의 `__eq__` 를 부른다」\
  ○ **이 구현은 리스트 원소의 `__eq__` 를 부른다.** 문서의 동등식은 결과에 대한 것이다.

> **구현 세부사항(implementation detail)** — 언어 명세가 보장하지 않고 특정 구현이 그렇게 만들어 둔 것.\
> 예: `in` 이 어느 쪽 `__eq__` 를 먼저 부르는지는 문서가 정하지 않는다. 결과만 정한다.

**판정 기준 한 줄**

**「참인가」와 「있는가」는 다른 질문이다.** 코드가 둘을 섞고 있으면 그 자리가 버그 후보다.

### 11. 「참인가」와 「있는가」 (연결)

**세 검사가 묻는 것**

```text
 if x:                     if x is not None:           if x == True:
  "참으로 볼 것인가"           "값이 주어졌나"              "True 와 같은 값인가"
  __bool__ -> __len__        정체 비교 하나               __eq__ 를 부른다
  0, "", [] 도 걸린다         0, "", [] 는 통과한다        [1] 은 거짓이 된다
```

```python
print(1 == True, [1] == True, bool([1]))
```

```text
True False True
```

`[1]` 은 **참인데** `== True` 는 거짓이다. 세 번째 검사는 **거의 언제나 틀린 도구**다.

**어디에 무엇을 쓰나**

| 자리 | 쓰는 것 | 왜 |
|---|---|---|
| 「리스트가 비었나」 | `if not items:` | 진릿값 판정이 바로 그 질문이다 |
| 「인자가 주어졌나」 | `if x is not None:` | `0`·`""` 가 유효한 값일 수 있다 |
| 「`None` 도 유효한 값일 때」 | `MISSING = object()` 센티널 + `is` | [20번](../20-mutable-default-args/2-summary.md) |
| 「불린 플래그가 켜졌나」 | `if flag:` | `== True` 를 쓰지 않는다 |
| 「API 로 불린을 내보낼 때」 | `bool(...)` 로 감싼다 | `and`/`or` 결과는 `bool` 이 아니다 |
| 「거짓 값 전부를 기본값으로」 | `x or 기본값` | 그게 **정말 의도일 때만** |

**판정 순서 한 장**

```text
 "0, "", [] 가 유효한 값일 수 있나?"
     |
     +-- 예 --> is not None (또는 센티널)
     |
     +-- 아니오 --> "비었나 / 0 인가" 를 묻는 게 맞나?
                       |
                       +-- 예 --> if x:
                       |
                       +-- 아니오 --> 조건을 다시 쓴다
```

**한 문장으로**

**`if x:` 는 「비었나」를 묻고 `if x is not None:` 은 「없나」를 묻는다.**\
파이썬에서 이 둘이 자주 같은 답을 내기 때문에, **다른 답을 내는 날 조용히 틀린다.**

---

## 실행 검증

이 파일에 실린 출력은 전부 아래 환경에서 직접 돌려 얻었다.

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys; print(sys.implementation.name)"
cpython
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | `Both`/`OnlyLen`/`Neither` 판정, `Box` 반례, `__bool__`·`__len__` 반환 오류 2종 | 각 1회 |
| 2 | 거짓 10종·참 6종 판정, `Decimal`/`Fraction` 의 0, `[1] == True` | 각 1회 |
| 3 | `and`/`or` 5식, 타입 2종, `json.dumps` | 각 1회 |
| 4 | `bad`/`good` 6값 대조, `order(0)`, `MISSING` 센티널 | 각 1회 |
| 5 | `loud` 3판 + `a is not None and len(a)`, `logged` 부작용 | 각 1회 |
| 6 | 체이닝 대 `and` **두 조합**(앞이 거짓일 때 / 참일 때), `dis` 2판, `==`/`in` 체이닝 3식 | 각 1회 |
| 7 | `a and b` · `a or b` 의 `dis` | 각 1회 |
| 8 | `Loud` 3원소 탐색 2판, 비대칭 `__eq__` 2클래스(list·tuple) | 각 1회 |
| 9 | `any`/`all` 빈 입력, 타입, 제너레이터 단축, `all_positive([])` | 각 1회 |

**★ 한 판으로 결론이 안 나는 것을 두 판 이상 던진 자리**

- **6번** — `1 < loud(0) < 100` 으로 재면 체이닝과 `and` 판이 **둘 다 한 번**이라 구별이 안 된다.\
  앞을 참으로 만든 `3 < loud(5) < 100` 에서야 **1회 대 2회**로 갈렸다.
- **8번** — 대칭 `__eq__` 로는 어느 쪽이 불리는지 안 드러난다.\
  **비대칭 `__eq__` 두 클래스**를 따로 만들어야 `e == x` 라는 것이 보였다.

**「출력 없음」이 근거인 자리**

- 1번 — `__len__ 불림` 이 **안 찍힌 것**이 「`__bool__` 이 먼저」의 증거다.
- 5번 — `A 평가됨`·`B 평가됨` 이 **안 찍힌 것**이 단축 평가의 증거다.
- 5번 — `logged` 가 **빈 리스트인 것**이 부작용까지 건너뛴다는 증거다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 6·7번의 `dis` 출력 | 명령 이름·번호는 판마다 바뀐다 |
| 8번의 `__eq__` 호출 순서 | 문서가 결과만 정한다 |
| 1번의 오류 메시지 문구 | 예외 종류는 명세지만 문구는 아니다 |

나머지(진릿값 판정 순서, 거짓인 것들의 목록, `and`/`or` 의 반환값, 단축 평가, 체이닝의 1회 평가, `any`/`all` 의 빈 입력 결과)는 **언어 보장**이므로 어떤 구현에서도 같아야 한다.
