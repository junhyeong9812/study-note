# python/syntax/11-tuple-and-unpacking — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **바이트코드 명령 이름·상수 합치기·`getsizeof` 는 구현에 달린 것**이라 다른 구현·다른 판에서는 달라진다(5·6·10번 답).

## 정답

### 1. 괄호는 타입을 안 바꾸고 쉼표가 바꾼다

**출력**

```text
(1)      -> 1          int
(1,)     -> (1,)       tuple
1,       -> (1,)       tuple
1, 2     -> (1, 2)     tuple
()       -> ()         tuple
len((1)) -> TypeError object of type 'int' has no len()
1 (1,)
(1,) (1,) ((1,),) (1, 2)
```

**왜 그런가**

문서가 직접 적는다 — *"Note that **tuples are not formed by the parentheses, but rather by use of the comma**.
The exception is the empty tuple, for which parentheses are required."*

```text
  (1)   ->  괄호는 "묶어 읽어라" 일 뿐.  안에 쉼표가 없으니 그냥 1
  (1,)  ->  쉼표가 있다  ->  tuple
   1,   ->  괄호가 없어도 쉼표만 있으면 tuple
   ()   ->  ★ 쉼표를 놓을 자리가 없어서 괄호가 그 일을 한다 (유일한 예외)
```

**마지막 줄 — 호출의 쉼표는 튜플을 안 만든다**

```text
  g(1)    ->  인자 1개  ->  a = (1,)      ★ 이 (1,) 은 *a 가 "모은" 것이다
  g(1,)   ->  꼬리 쉼표는 무시된다  ->  인자 1개  ->  같은 결과
  g((1,)) ->  인자가 (1,) 이라는 튜플 1개  ->  a = ((1,),)
  g(1, 2) ->  인자 2개  ->  a = (1, 2)
```

★ **같은 쉼표가 대입에서는 튜플을 만들고 호출에서는 안 만든다.** 문법이 다른 자리다.
그래서 `g(1)` 과 `g(1,)` 이 같고, 튜플 하나를 넘기려면 **괄호를 한 겹 더** 써야 한다.

### 2. 예외가 두 종류로 갈리는 기준 — 「풀 수 있나」와 「개수가 맞나」

**출력**

```text
a, b = (1, 2, 3)     -> ValueError: too many values to unpack (expected 2)
a, b, c = (1, 2)     -> ValueError: not enough values to unpack (expected 3, got 2)
a, b, *r = (1,)      -> ValueError: not enough values to unpack (expected at least 2, got 1)
a, b = 5             -> TypeError: cannot unpack non-iterable int object
a, b = 'xyz'         -> ValueError: too many values to unpack (expected 2)
a, b = None          -> TypeError: cannot unpack non-iterable NoneType object
```

**왜 그런가**

```text
  1단계: 오른쪽이 이터러블인가?
           아니다  ->  TypeError: cannot unpack non-iterable <타입> object
           맞다    ->  2단계

  2단계: 개수가 맞나?
           많다    ->  ValueError: too many values to unpack (expected N)
           모자란다 ->  ValueError: not enough values to unpack (expected N, got M)
           별표가 있으면 "expected at least N"
```

| 무엇이 틀렸나 | 예외 | 문구의 특징 |
|---|---|---|
| **풀 수가 없다**(이터러블이 아님) | `TypeError` | 타입 이름을 말해 준다 |
| **너무 많다** | `ValueError` | `expected N` 뿐 — **몇 개였는지 안 알려 준다** |
| **모자란다** | `ValueError` | `expected N, got M` — **받은 개수까지** |
| 모자란데 **별표가 있다** | `ValueError` | `expected at least N, got M` |

★ **「너무 많다」 쪽만 받은 개수를 안 알려 준다.** N+1 번째를 보는 순간 멈추기 때문이다 — 다 세지 않는다.\
★ **`a, b = 'xyz'` 가 `TypeError` 가 아니다.** 문자열은 이터러블이라 1단계를 통과하고 개수에서 걸린다.\
★ **`None` 은 `TypeError`** 다 — 「데이터가 없을 때」의 대표 사고가 여기서 난다.

문서가 별표 규칙을 직접 정의한다 —
*"The object must be an iterable with **at least as many items as there are targets in the target list, minus one**."*

### 3. 봉지는 언제나 `list` 이고 별표는 한 번뿐

**출력**

```text
1 [2, 3, 4] list
[1, 2, 3] 4
1 []
1 [2, 3] list
k ['j']
a, *b, *c = [1,2,3]  -> SyntaxError: multiple starred expressions in assignment
*a, *b = [1,2]       -> SyntaxError: multiple starred expressions in assignment
```

**왜 그런가**

```text
 a, *rest = [1, 2, 3, 4]

   [ 1 | 2 | 3 | 4 ]
     ^   \_______/
     a      rest      ->  list  [2, 3, 4]

 a, *r = [1]      ->  r = []        빈 리스트. 에러가 아니다
 a, *r = (1,2,3)  ->  r = [2, 3]    ★ 원본이 튜플이어도 list
 a, *r = dict     ->  dict 를 돌면 "키" 가 나온다
```

★ **원본이 무엇이든 봉지는 `list`** 다. 문서가 *"**A list** of the remaining items in the iterable is then assigned to the starred target"* 라고 적는다.

**별표가 한 번뿐인 이유 — 나눌 방법이 없다**

```text
 a, *b, *c = [1, 2, 3]

   1 을 a 에 주고 나면 [2, 3] 이 남는다.
   b 가 [2] 인지 [2,3] 인지 [] 인지 정할 근거가 없다.
   -> 그래서 문법 단계에서 막는다.  SyntaxError
```

★ **`SyntaxError` 라 실행 전에 걸린다.** 다른 언패킹 오류(`ValueError`)와 달리 **테스트를 안 돌려도** 드러난다.\
★ **호출에서는 `*` 를 여러 번 써도 된다**(4번 답) — 거기서는 「푸는」 것이라 나눌 일이 없기 때문이다.

### 4. 모으는 쪽은 `tuple`, 대입에서 남는 쪽은 `list`

**출력**

```text
a=1 b=2 c=3 kw={}
a=x b=y c=0 kw={}
((1, 2), {'k': 3})
((1, 2, 3), {})
TypeError keywords must be strings
[1, 2, 3] (1, 2, 3) {'a': 1, 'b': 2}
```

**왜 그런가 — `*` 는 자리마다 다른 일을 한다**

```text
  ┌ 대입 왼쪽 ─ a, *rest = x        "모은다"   rest 는 list.  ★ 한 번만
  ├ 시그니처 ── def f(*args)        "모은다"   args 는 tuple
  ├ 호출 인자 ── f(*seq)            "푼다"     ★ 여러 번 써도 된다
  └ 리터럴 안 ── [*a, *b] {**d1,**d2}  "푼다"   3.5+ (PEP 448)
```

| 자리 | 무엇을 하나 | 만들어지는 타입 | 몇 번 |
|---|---|---|---|
| `a, *rest = x` | 모은다 | **`list`** | **한 번** |
| `def f(*args)` | 모은다 | **`tuple`** | 한 번 |
| `def f(**kw)` | 모은다 | **`dict`** | 한 번 |
| `f(*seq)` | 푼다 | — | 여러 번 |
| `f(**mapping)` | 푼다 | — | 여러 번 |

★ **3번 문항의 `rest` 는 `list` 인데 여기 `gather` 의 첫 덩어리는 `tuple`** 이다.
둘 다 `*` 인데 **만들어 주는 타입이 다르다** — 이것이 이 주제에서 가장 자주 틀리는 자리다.

- `show(*(1, 2), 3)` — 푼 뒤에 값을 **더 붙일 수 있다.**
- `show(*"xy")` — 문자열도 이터러블이라 글자가 인자가 된다.
- `show(**{1: 2})` — **키가 문자열이 아니면** `keywords must be strings` 다. 키워드는 이름이어야 하기 때문이다.
- `[*t, 3]`·`(*t, 3)`·`{**d, ...}` 는 **3.5(PEP 448)** 부터다.

### 5. 2개는 `SWAP`, 4개는 `BUILD_TUPLE`

**출력**

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (b)
              4 LOAD_NAME                1 (a)
              6 SWAP                     2
              8 STORE_NAME               1 (a)
             10 STORE_NAME               0 (b)
             12 RETURN_CONST             0 (None)
-----
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (d)
              4 LOAD_NAME                1 (c)
              6 LOAD_NAME                2 (b)
              8 LOAD_NAME                3 (a)
             10 BUILD_TUPLE              4
             12 UNPACK_SEQUENCE          4
             16 STORE_NAME               3 (a)
             18 STORE_NAME               2 (b)
             20 STORE_NAME               1 (c)
             22 STORE_NAME               0 (d)
             24 RETURN_CONST             0 (None)
-----
  0           0 RESUME                   0

  1           2 LOAD_CONST               0 ((1, 2, 3))
              4 STORE_NAME               0 (x)
              6 RETURN_CONST             1 (None)
```

**왜 그런가**

```text
 2개(그리고 3개까지)   ->  스택 위에서 자리만 바꾸면 된다.  SWAP
                          ★ 튜플을 아예 만들지 않는다

 4개부터              ->  BUILD_TUPLE 4  로 묶었다가
                          UNPACK_SEQUENCE 4  로 다시 푼다
```

★ **「스왑은 튜플을 만들었다가 푼다」는 설명이 작은 개수에서는 사실이 아니다.**
★ 그리고 이것은 **컴파일러의 최적화이지 언어 보장이 아니다** — 3개까지 줄인 것은 이 구현의 선택이다.

세 번째 블록은 **상수뿐인 튜플**이다 — `BUILD_TUPLE` 조차 없이 `LOAD_CONST ((1, 2, 3))` 한 번이다.
컴파일 때 이미 만들어져 코드 객체 안에 들어 있다.

스왑이 **되는 이유**(오른쪽을 먼저 다 평가한다)는 [01번](../01-object-and-name-binding/2-summary.md)이 정본이다.
여기서 보탠 것은 **「그다음에 무엇으로 나눠 주나」**뿐이다.

### 6. 문서가 약속한 것은 `tuple(t) is t` 하나뿐

**출력**

```text
True (None, (1, 2, 3))
True True False
```

**왜 그런가**

```text
 f 의 co_consts 에 (1, 2, 3) 이 "하나" 들어 있다.
   a = (1,2,3)  ->  그 상수를 가리킨다
   b = (1,2,3)  ->  같은 상수를 가리킨다
   a is b       ->  True
```

★ 이것은 [02번](../02-is-vs-eq-interning/2-summary.md)의 **기계 ①(한 컴파일 단위 안의 상수 합치기)** 이 튜플에도 걸린 것이다.
**모듈이 다르면 합쳐지지 않는다** — 그쪽이 정본이다.

**세 `is` 의 층이 다르다**

| 식 | 이 판의 결과 | 어느 층 |
|---|---|---|
| `tuple(t0) is t0` | `True` | ★ **언어 보장** — *"If iterable is already a tuple, **it is returned unchanged**."* |
| `t0[:] is t0` | `True` | **CPython 구현** — 문서에 없다. [09번](../09-sequence-ops-and-slicing/2-summary.md)에서 **`range` 가 반례**였다 |
| `list(t0) is t0` | `False` | 타입이 다르니 당연 |
| `a is b`(상수 튜플) | `True` | **CPython 구현** — 컴파일 단위 안에서만 |

★ **겉보기가 같은 두 사실(`tuple(t) is t` / `t[:] is t`)이 다른 층이다.**
「불변이면 사본이 자기 자신」은 **규칙이 아니다** — [03번](../03-mutability-and-copying/2-summary.md)에서 `frozenset` 이,
[09번](../09-sequence-ops-and-slicing/2-summary.md)에서 `range` 가 반례였다.

### 7. 튜플이 지키는 것은 「어느 칸이 어느 객체를 가리키나」뿐

**출력**

```python
t = (1, [2, 3])
t[1].append(4)
print("t[1].append(4) ->", t)
try:
    t[0] = 9
except TypeError as e:
    print("t[0] = 9       ->", type(e).__name__, e)
try:
    hash(t)
except TypeError as e:
    print("hash(t)        ->", type(e).__name__, e)
```

```text
t[1].append(4) -> (1, [2, 3, 4])
t[0] = 9       -> TypeError 'tuple' object does not support item assignment
hash(t)        -> TypeError unhashable type: 'list'
```

**왜 그런가**

```text
  t = (1, [2, 3])

   +-----+-----+
   |  *  |  *  |          <- 튜플이 지키는 것은 이 두 화살표뿐
   +--|--+--|--+
      v     v
      1   [2, 3]          <- 이 리스트 안까지는 안 지킨다

  t[0] = 9        화살표를 바꾸려는 것   ->  거부된다
  t[1].append(4)  화살표가 가리키는 곳을 바꾸는 것  ->  된다
```

정본은 [03번](../03-mutability-and-copying/2-summary.md)이다. 여기서 이어받을 결론은 둘이다.

- ★ **「불변이다」와 「해시 가능하다」가 다른 말**이다. 뒤엣것은 **내용에 달렸다.**
- ★ **오류가 `tuple` 이 아니라 `list` 를 가리킨다** — 튜플이 안쪽에게 해시를 물어보다 거기서 터진 것이다.
  이 사슬이 [12번](../12-dict-and-key-requirements/2-summary.md)의 「키 요건」으로 그대로 이어진다.

### 8. 셋을 한 집합에 넣으면 하나가 남는다

**출력**

```python
from collections import namedtuple
from typing import NamedTuple
Point = namedtuple("Point", "x y")
class TPoint(NamedTuple):
    x: int
    y: int
p, q = Point(1, 2), TPoint(1, 2)
print(isinstance(p, tuple), isinstance(q, tuple))
print(p == (1, 2), q == (1, 2), p == q)
print(hash(p) == hash((1, 2)) == hash(q))
print({p, q, (1, 2)})
print(type(p) is type(q))
```

```text
True True
True True True
True
{Point(x=1, y=2)}
False
```

**왜 그런가 — 둘 다 `tuple` 의 서브클래스이고 `==`·`hash` 를 물려받는다**

```text
  MRO:  Point  -> tuple -> object
        TPoint -> tuple -> object

  ==  도 hash 도 tuple 의 것을 그대로 쓴다
   -> Point(1,2) == TPoint(1,2) == (1,2)
   -> hash 도 셋이 같다
   -> 집합·dict 가 보기에는 "같은 것" 이다   ->  하나만 남는다
```

★ **남은 것은 `Point(x=1, y=2)`** 다 — **처음 들어간 것**이 키로 남는다.
[12번](../12-dict-and-key-requirements/2-summary.md)의 「`1`·`1.0`·`True` 가 한 키」와 **정확히 같은 규칙**이다.

- **타입은 다르다**(`type(p) is type(q)` 가 `False`)는데 **값은 같다.** 타입으로 구분하려던 설계가 여기서 무너진다.
- 그래서 `namedtuple` 은 **「이름이 붙은 튜플」**이지 「새 타입」이 아니다.
- 셋 중 무엇을 고를지는 목록의 **38번 주제**가 정본이다.

### 9. 봉지가 `list` 라서 키가 안 된다

**출력**

```python
a, *rest = (1, 2, 3)
print(type(rest).__name__)
try:
    {rest: "값"}
except TypeError as e:
    print("{rest: '값'} ->", type(e).__name__, e)
print("고치는 법 :", {tuple(rest): "값"})
```

```text
list
{rest: '값'} -> TypeError unhashable type: 'list'
고치는 법 : {(2, 3): '값'}
```

- 오른쪽이 **튜플이었는데도** 봉지는 `list` 다(3번 답).
- **고치는 법은 `tuple(rest)`** 로 얼리는 것이다([12번](../12-dict-and-key-requirements/2-summary.md)).
- ★ 이것이 **조용하지 않은** 실패라는 점이 다행이다 — 키로 쓰는 순간 바로 `TypeError` 다.
  조용한 쪽은 「`rest` 가 튜플인 줄 알고 `==` 로 비교하는」 자리다(`[2,3] == (2,3)` 은 **`False`**).

```python
print([2, 3] == (2, 3))
```

```text
False
```

★ **`list` 와 `tuple` 은 내용이 같아도 `==` 가 거짓**이다 — 이쪽은 에러 없이 틀린다.

### 10. 세 층 가르기

**언어 보장**

| 사실 | 근거 |
|---|---|
| **괄호가 아니라 쉼표가 튜플을 만든다.** 빈 튜플만 괄호가 필수 | 6.2.3 Parenthesized forms |
| 쉼표가 하나라도 있는 식 목록은 튜플 · **한 원소에는 꼬리 쉼표 필수** | 6.15 Expression lists |
| 별표 대상은 **「대상 수 − 1」개 이상**을 요구하고 남은 것을 **`list`** 로 받는다 | 7.2 Assignment statements |
| 별표 없는 대상 목록은 **개수가 정확히** 같아야 한다 | 〃 |
| 대입은 **오른쪽을 먼저** 평가한다 | 6.16 Evaluation order |
| **`tuple(t)` 는 `t` 가 이미 튜플이면 그대로 돌려준다** | Tuples |
| 빈 튜플이 **같은 객체일 수도 아닐 수도 있다** | 6.2.3 |
| 리터럴·호출 안의 `*`/`**` 확장은 **3.5(PEP 448)** | 6.15 |
| `namedtuple`·`NamedTuple` 은 **`tuple` 의 서브클래스** | collections · typing |

**CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| **2·3개 스왑은 `SWAP`, 4개부터 `BUILD_TUPLE`+`UNPACK_SEQUENCE`** | `dis` |
| 상수뿐인 튜플은 **`LOAD_CONST` 한 번** | `dis` · `co_consts` |
| 같은 코드 객체 안의 같은 상수 튜플이 **한 객체** | `a is b` 가 `True` |
| **`t[:] is t`** 가 참 | 문서에 없다. `range` 가 반례([09번](../09-sequence-ops-and-slicing/2-summary.md)) |
| 예외·경고 **문구** 전부 | 실행 |

**이 판(3.12.3)·이 머신의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof` — `(1,2,3)`=64 · `[1,2,3]`=88 · `()`=40 · `[]`=56 | 빌드·비트 폭에 달렸다 |
| `namedtuple` 인스턴스와 평범한 2-튜플의 `getsizeof` 가 둘 다 56 | 구현 몫 |
| `SWAP`·`UNPACK_EX`·`BUILD_TUPLE` 같은 명령 이름 | 판마다 바뀐다 |
| `SyntaxError` 문구 `multiple starred expressions in assignment` | 문구는 판마다 바뀐다 |

```python
import sys
from collections import namedtuple
Point = namedtuple("Point", "x y")
print(sys.getsizeof((1, 2, 3)), sys.getsizeof([1, 2, 3]), sys.getsizeof(()), sys.getsizeof([]))
print(sys.getsizeof(Point(1, 2)), sys.getsizeof((1, 2)))
```

```text
64 88 40 56
56 56
```

**그래서 이렇게 적으면 틀린다**

- ✗ 「괄호가 튜플을 만든다」 → **쉼표**가 만든다. **빈 튜플만 예외**다.
- ✗ 「언패킹 실패는 언제나 `ValueError`」 → **이터러블이 아니면 `TypeError`** 다.
- ✗ 「`a, *rest` 의 `rest` 는 튜플」 → **`list`** 다(문서가 정한다).
- ✗ 「`*` 는 어디서나 한 번만」 → **호출에서는 여러 번** 된다.
- ✗ 「스왑은 튜플을 만들었다 푼다」 → 2·3개는 **`SWAP`** 으로 끝난다(구현).
- ✗ 「`t[:] is t` 니까 불변은 사본이 자기 자신」 → `frozenset`·`range` 가 반례다.
- ✗ 「`namedtuple` 은 새 타입이라 구분된다」 → **`==`·`hash` 가 평범한 튜플과 같다.**

### 11. 조용한 실패 두 자리

| 자리 | 무엇이 조용히 틀리나 | 무엇으로 막나 |
|---|---|---|
| **한 원소 튜플의 쉼표** | `("X")` 가 문자열이라 **글자 단위로 순회**된다. 에러 없음 | `("X",)` · 만든 직후 `isinstance(x, tuple)` |
| **`list` 와 `tuple` 의 `==`** | `[2,3] == (2,3)` 이 **`False`** 인데 예외가 없다 | 비교 전에 타입을 맞춘다(`tuple(...)`) |
| (보태기) **`_` 가 값을 받는다** | `*_` 가 큰 리스트를 통째로 만든다 | 정말 버릴 것이면 슬라이스로 |
| (보태기) **`None` 언패킹** | 조용하지 않다 — `TypeError` 로 바로 터진다 | 실패 시 빈 튜플을 돌려주게 |

막는 코드는 이렇게 생겼다.

```python
HEADERS = ("Content-Type",)          # 쉼표를 빼면 문자열이 된다
assert isinstance(HEADERS, tuple) and len(HEADERS) == 1

def parse(line):
    name, _, rest = line.partition("=")   # 개수가 늘 3이라 언패킹이 안 터진다
    return name, rest

def first_and_rest(xs):
    head, *tail = xs
    return head, tuple(tail)             # 봉지를 튜플로 얼려서 내보낸다
```

## 실행 검증

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys; print(sys.implementation.name)"
cpython
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | 괄호·쉼표 **5형태** + `len((1))` + 겹괄호 2형태 + 호출 4형태 | 각 1회 |
| 2 | 언패킹 실패 **8형태**(개수 4 · 비이터러블 2 · 문자열 1 · 별표 2) | 각 1회 |
| 3 | 별표 언패킹 **8형태**(list·str·tuple·range·dict·빈 봉지), `SyntaxError` 3형태 | 각 1회 |
| 4 | 호출의 `*`/`**` **8형태**, 리터럴 안 `*` 5형태, 실패 2형태 | 각 1회 |
| 5 | `dis` — 스왑 **2·3·4개**, `a, b = f()`, `a, *b = f()`, 상수 튜플, 변수 섞인 튜플 | 각 1회 |
| 6 | `co_consts`, `is` **3형태** | 각 1회 |
| 7 | 튜플 안의 리스트 3형태(`append`·대입·`hash`) | 각 1회 |
| 8 | `namedtuple`/`NamedTuple` **12항목**(MRO·`==`·`hash`·집합·언패킹·`_asdict`·`_replace`·어노테이션) | 각 1회 |
| 10 | `getsizeof` 6종 | 각 1회 |

**★ 한 판으로 결론이 안 나는 것을 여러 판 던진 자리**

- **5번** — **2개만** 재면 「스왑은 `SWAP` 이다」로 끝난다. **3개·4개**를 던져야 4개부터 `BUILD_TUPLE` 이 나온다.
  ★ 「스왑은 튜플을 만들었다 푼다」는 흔한 설명이 여기서 반증됐다.
- **2번** — `a, b = (1,2,3)` 하나만 재면 「언패킹 실패는 `ValueError`」로 결론이 선다.
  **`5`·`None`** 을 던져야 `TypeError` 가 나오고, **`'xyz'`** 를 던져야 「문자열은 `ValueError` 쪽」이 드러난다.
- **3번** — **리스트**로만 재면 봉지가 리스트인 게 당연해 보인다.
  **튜플·문자열·`range`·`dict`** 를 던져야 「원본이 무엇이든 `list`」가 드러난다.
- **8번** — `isinstance(p, tuple)` 만 보면 「튜플이구나」로 끝난다.
  **집합에 셋을 같이 넣어 봐야** 「값으로는 구분이 안 된다」가 드러난다.

**「에러가 안 난 것」이 근거인 자리**

- 1번 — `("X")` 가 **예외 없이** 문자열이 되는 것이 「괄호는 튜플을 안 만든다」의 증거다.
- 9번 — `[2,3] == (2,3)` 이 **예외 없이 `False`** 인 것이 조용한 실패의 증거다.
- 3번 — `a, *r = [1]` 에서 **예외가 없는 것**이 「봉지는 비어도 된다」의 증거다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 5번의 스왑 명령과 **갈리는 개수**(3 ↔ 4) | 컴파일러 최적화다 |
| 6번의 `a is b`(상수 튜플) | 컴파일 단위 상수 합치기는 구현 |
| 6번의 `t0[:] is t0` | 문서가 약속하지 않는다 |
| 10번의 `getsizeof` 값 전부 | 빌드·비트 폭에 달렸다 |
| 예외·경고 **문구** 전부 | 예외 종류는 명세지만 문구는 아니다 |

나머지(쉼표가 튜플을 만든다는 것, 빈 튜플의 예외, 별표 봉지가 `list` 라는 것, 별표가 한 번뿐인 것,
`tuple(t) is t`, `namedtuple` 이 `tuple` 의 서브클래스라는 것)는 **언어 보장**이므로 어떤 구현에서도 같아야 한다.
