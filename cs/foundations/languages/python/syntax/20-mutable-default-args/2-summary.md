# python/syntax/20-mutable-default-args — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [8.8. Function definitions](https://docs.python.org/3.12/reference/compound_stmts.html#function-definitions) — 기본값 평가 시점과 가변 기본값 주의
> - [`dataclasses.field`](https://docs.python.org/3.12/library/dataclasses.html#dataclasses.field) — `default_factory`
> - [3.2. The standard type hierarchy — Callable types](https://docs.python.org/3.12/reference/datamodel.html#the-standard-type-hierarchy) — 함수 객체의 `__defaults__`·`__kwdefaults__`
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — Python 3 전체 공통. `dataclasses` 의 가변 기본값 거부는 3.7+(dataclasses 도입 시점부터).
> **구현 대 명세** — 이 주제는 **전부 언어 보장**이다. 언어 레퍼런스가 동작과 해법까지 명시한다(02번 주제와 대조적).

## 한눈에 — 쉽게 말하면

**함수에 꿰매 붙은 주머니.**

- `def f(x, bag=[]):` 를 쓰면, **`def` 문이 실행되는 그 순간** 빈 리스트 하나가 만들어져 **함수에 꿰매 붙는다.**
- 그 뒤로 `f(1)` 을 백 번 부르든 천 번 부르든, 파이썬은 **꿰매 둔 그 주머니를 그대로 건넨다.**\
  새 주머니를 만들어 주지 않는다.
- 주머니가 리스트·딕셔너리처럼 **안을 고칠 수 있는 것**이면, 호출마다 넣은 물건이 **계속 쌓인다.**

```text
def f(x, bag=[]):  를 실행한 직후

   함수 객체 f
   +---------------------+          +--------+
   | __defaults__  ------+--------> |   []   |   <- 딱 하나 만들어져 꿰매졌다
   +---------------------+          +--------+

   f("사과") 호출        ->  이 주머니를 그대로 넘긴다  -> ['사과']
   f("배")   호출        ->  같은 주머니를 또 넘긴다     -> ['사과', '배']
   f("감")   호출        ->  같은 주머니를 또 넘긴다     -> ['사과', '배', '감']
```

이 주머니가 **똑같은 구조로** `함수객체.__defaults__` 다.\
실무에서 이것이 물리는 자리는 늘 같다 — **"인자를 안 주면 빈 리스트로 시작하겠지"** 라고 가정한 함수·`__init__`·설정 병합 함수.

> **가변(mutable) 객체** — 만든 뒤에 안을 고칠 수 있는 객체.\
> 예: 리스트·딕셔너리·집합. 반대로 숫자·문자열·튜플은 불변이라 고치려면 새 객체를 만들어야 한다.

> **기본 인자(default argument)** — 호출할 때 그 인자를 생략하면 대신 쓰이는 값.\
> 예: `def f(x, bag=[])` 에서 `[]` 가 기본 인자다.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. `def` 문을 실행할 때 기본값이 한 번 만들어진다

**언제 쓰나** — 기본값이 있는 함수를 정의할 때. 항상.

```text
파이썬이 def 문을 만나면 이 순서로 한다

  1. 기본값 식을 왼쪽에서 오른쪽으로 **지금 평가한다**   <- 여기가 핵심
  2. 함수 객체를 만든다
  3. 평가된 기본값들을 함수 객체에 __defaults__ 로 붙인다
  4. 이름(f)을 그 함수 객체에 바인딩한다

  ★ 함수 몸통은 아직 한 줄도 안 돌았다
```

문서가 그대로 적는다 — "**Default parameter values are evaluated from left to right when the function definition is executed.**"

눈으로 확인하는 실험이다.

```python
def side():
    print("   side() 실행됨")
    return []

print("def 문 실행 전")
def g(x, acc=side()):
    acc.append(x)
    return acc
print("def 문 실행 끝")
print(g(1))
print(g(2))
```

```text
def 문 실행 전
   side() 실행됨
def 문 실행 끝
[1]
[1, 2]
```

그림 해설.

- `side()` 가 **`def` 문 실행 중에** 딱 한 번 찍혔다. 호출할 때 찍힌 것이 아니다.
- `g(1)`, `g(2)` 를 불러도 `side()` 가 다시 안 찍혔다 → **기본값은 다시 계산되지 않는다.**
- 그래서 `[1]` 다음에 `[1, 2]` 가 나온다. 같은 리스트다.

**비용** — 기본값을 한 번만 계산하므로 호출이 빠르다.\
대신 **기본값이 가변이면 호출 사이에 상태가 새어 흐른다**는 값을 치른다.

### 2. 호출마다 같은 주머니가 건네진다

**언제 쓰나** — 기본값이 리스트·dict·set 인 함수를 두 번 이상 호출할 때.

```text
def add_item(item, bag=[]):
    bag.append(item)
    return bag

 호출 전                          add_item("사과") 후
   __defaults__ -> [ ]              __defaults__ -> ['사과']
                                          ^
                                   반환된 리스트와 같은 상자

 add_item("배") 후                 add_item("감") 후
   __defaults__ -> ['사과','배']    __defaults__ -> ['사과','배','감']
```

```python
def add_item(item, bag=[]):
    bag.append(item)
    return bag

print(add_item("사과"))
print(add_item("배"))
print(add_item("감"))
```

```text
['사과']
['사과', '배']
['사과', '배', '감']
```

주머니가 정말 하나인지는 `__defaults__` 를 들여다보면 끝난다.

```python
print(add_item.__defaults__)
print(id(add_item.__defaults__[0]))
add_item("귤")
print(add_item.__defaults__)
print(id(add_item.__defaults__[0]))
```

```text
(['사과', '배', '감'],)
133723085001280
(['사과', '배', '감', '귤'],)
133723085001280
```

그림 해설.

- `__defaults__` 는 **함수 객체에 달린 튜플**이다. 기본값들이 거기 들어 있다.
- 호출 뒤에 내용이 늘었는데 **`id` 는 그대로다** → 새 리스트로 갈아 끼운 게 아니라 **같은 리스트를 고친 것**이다.\
  (`id` 값 자체는 실행할 때마다 다르다. 중요한 것은 **두 번이 같다**는 것이다.)
- 함수 바깥에서 그 리스트를 들여다볼 수 있다는 것이 이 함정의 정체다 — **함수의 「기본값」이 사실상 전역 상태**다.

**비용** — 없다. 이것은 최적화가 아니라 **평가 시점의 필연적 결과**다.\
`def` 문이 실행될 때 기본값을 계산해 붙여 두는 설계를 고른 이상, 호출마다 새로 만들 방법이 없다.

### 3. 명시로 넘기면 그 호출만 갈라진다

**언제 쓰나** — 이 함정을 디버깅할 때. 증상이 "가끔만 난다"로 보이는 이유가 여기 있다.

```text
add_item("포도", [])              add_item("수박")
  새 리스트를 넘겼다                 꿰매 둔 주머니를 쓴다
        +----------+                  +------------------------------+
        | ['포도'] |                  | ['사과','배','감','귤','수박'] |
        +----------+                  +------------------------------+
   __defaults__ 는 안 건드림          __defaults__ 가 또 늘었다
```

```python
print(add_item("포도", []))
print(add_item("수박"))
```

```text
['포도']
['사과', '배', '감', '귤', '수박']
```

그림 해설.

- 인자를 **주면** 기본값은 아예 쓰이지 않는다. 그 호출은 깨끗하다.
- 인자를 **안 주는 호출만** 오염된다.
- 그래서 테스트가 늘 인자를 넘기면 이 버그는 **영원히 안 잡힌다.**\
  운영 코드의 "기본으로 부르는 한 군데"에서만 터진다.

**비용** — 없음. 다만 **증상이 간헐적으로 보인다**는 진단 비용이 크다.

### 4. `None` 센티널로 고친다

**언제 쓰나** — 가변 기본값이 필요한 모든 함수. 예외 없는 표준 관용구다.

```text
고장난 형태                             고친 형태
def f(item, bag=[]):                    def f(item, bag=None):
    bag.append(item)                        if bag is None:
    return bag                                  bag = []
                                            bag.append(item)
                                            return bag

 __defaults__ -> [ ]  (하나, 공유됨)     __defaults__ -> (None,)  (불변)
 호출마다 그 상자에 쌓인다                호출마다 함수 안에서 새 상자를 만든다

        +----------+                           +----+   +----+   +----+
  f(1)  | [1]      |                     f(1)->| [1]|   | [2]|<-f(2)  ...
  f(2)  | [1, 2]   |                           +----+   +----+
        +----------+                     매 호출이 자기 상자를 갖는다
```

```python
def add_item_fixed(item, bag=None):
    if bag is None:
        bag = []
    bag.append(item)
    return bag

print(add_item_fixed("사과"))
print(add_item_fixed("배"))
print(add_item_fixed.__defaults__)
```

```text
['사과']
['배']
(None,)
```

그림 해설.

- `None` 은 **불변 싱글턴**이라 아무리 공유돼도 상할 것이 없다.
- 새 리스트를 만드는 일이 **`def` 시점에서 호출 시점으로 옮겨졌다.** 그것이 고침의 전부다.
- 판정은 `== None` 이 아니라 **`is None`** 으로 한다 — 이유는 [02번 주제](../02-is-vs-eq-interning/2-summary.md)에 있다.
- 문서도 같은 해법을 적는다 — "기본값으로 `None` 을 쓰고 함수 몸통에서 명시적으로 검사하라".

**비용** — 호출마다 리스트를 새로 만든다. `if` 한 줄과 객체 생성 한 번이 늘어난다.\
그 대신 **호출 사이에 상태가 새지 않는다.** 언제나 이쪽이 맞는 거래다.

### 5. `None` 자체가 유효한 값일 때

**언제 쓰나** — "인자를 안 준 것"과 "`None` 을 준 것"을 구분해야 할 때.

```text
문제                                   해법 — 나만 아는 표식을 만든다
def setting(key, default=None):        MISSING = object()
    if default is None:                def setting(key, default=MISSING):
        ...                                if default is MISSING:
                                               ...
 "안 줬다" 와 "None 을 줬다" 가
 구분되지 않는다                        MISSING 은 내가 하나만 만들었으므로
                                       바깥에서 우연히 같은 것이 올 수 없다
```

```python
MISSING = object()

def setting(key, default=MISSING):
    if default is MISSING:
        return f"{key}: 기본값 없음"
    return f"{key}: {default!r}"

print(setting("a"))
print(setting("a", None))
```

```text
a: 기본값 없음
a: None
```

그림 해설.

- `object()` 는 아무 속성도 없는 **빈 객체 하나**다. 오직 정체로만 구분된다.
- 그래서 `is` 로 판정한다. 값 비교가 아니라 "그 표식 바로 그것인가"를 묻는 것이다.
- 이 패턴이 표준 라이브러리에도 쓰인다 — `dataclasses.MISSING` 이 같은 물건이다.

**비용** — 모듈 수준 객체 하나가 는다.\
대신 API 가 "생략"과 "`None` 전달"을 구분할 수 있게 된다.

## 문법 — 형태와 규칙

```python
def f(a, b=[], *, c={}):      # b, c 가 기본 인자
    ...

f.__defaults__                # 위치 기본값 튜플  -> ([], )
f.__kwdefaults__              # 키워드 전용 기본값 dict -> {'c': {}}
```

규칙 넷.

1. **기본값 식은 `def` 문을 실행할 때 왼쪽에서 오른쪽으로 한 번 평가된다.**\
   `lambda` 도 똑같다. `lambda x, acc=[]: ...` 도 같은 함정이다.
2. **평가된 값은 함수 객체에 붙는다** — `__defaults__` / `__kwdefaults__`.
3. **인자를 넘기면 기본값은 아예 쓰이지 않는다.**
4. **키워드 전용(`*` 뒤)으로 옮겨도 달라지지 않는다.** 위치냐 키워드냐는 상관없다.

> **`__defaults__`** — 함수 객체에 달린, 위치 인자 기본값들의 튜플.\
> 예: `f.__defaults__[0]` 을 `append` 하면 앞으로의 모든 기본 호출이 그 결과를 본다.

## 어디서 틀리나

### (1) `__init__` 도 똑같다 — 인스턴스끼리 상태가 섞인다

```python
class Logger:
    def __init__(self, lines=[]):
        self.lines = lines
    def log(self, msg):
        self.lines.append(msg)

a = Logger(); b = Logger()
a.log("a 의 로그")
print("a.lines =", a.lines)
print("b.lines =", b.lines)
print("a.lines is b.lines ->", a.lines is b.lines)
```

```text
a.lines = ['a 의 로그']
b.lines = ['a 의 로그']
a.lines is b.lines -> True
```

**서로 남남인 두 인스턴스가 같은 리스트를 쓴다.**\
실무에서 가장 아프게 물리는 형태다 — 사용자 A 의 장바구니에 사용자 B 의 물건이 들어간다.

### (2) `def` 시점의 바깥 값이 그대로 박힌다

```python
LIMIT = 10
def clamp(v, top=LIMIT):
    return min(v, top)

LIMIT = 100
print(clamp(50))
print(clamp.__defaults__)
```

```text
10
(10,)
```

가변성과 무관한 쌍둥이 함정이다.\
`LIMIT` 을 바꿔도 `clamp` 는 **`def` 때 복사해 간 10** 을 계속 쓴다.\
설정을 늦게 읽고 싶으면 `def clamp(v, top=None): top = LIMIT if top is None else top` 처럼 **호출 시점에** 읽어야 한다.

### (3) 불변 기본값은 티가 안 난다 — 그래서 규칙이 필요하다

```python
def tag(name, suffix=""):
    return name + suffix

print(tag("a"), tag("b"))
print(tag.__defaults__)
```

```text
a b
('',)
```

`""` 도 똑같이 공유된다. 다만 **고칠 수 없어서 증상이 안 난다.**\
「공유되지 않는다」가 아니라 「공유되지만 상할 게 없다」가 맞는 이해다.\
그래서 판정 기준은 "이 기본값이 **가변인가**" 하나다.

### (4) `dataclasses` 는 아예 거부한다

```python
from dataclasses import dataclass, field

@dataclass
class Cart:
    items: list = []
```

```text
ValueError: mutable default <class 'list'> for field items is not allowed: use default_factory
```

`dataclasses` 가 이 함정을 **에러로 승격**시켰다. 고치는 법은 `default_factory` 다.

```python
@dataclass
class CartOK:
    items: list = field(default_factory=list)

c1 = CartOK(); c2 = CartOK()
c1.items.append("사과")
print(c1.items, c2.items)
```

```text
['사과'] []
```

`default_factory=list` 는 "기본값" 이 아니라 "**기본값을 만드는 방법**"을 등록한다 — 인스턴스마다 `list()` 를 새로 부른다.\
이것이 `None` 센티널과 같은 해법의 다른 표현이다.

다만 이 방어는 **부분적**이다. 막는 기준이 "해시할 수 없는 기본값"이라 `__hash__` 가 살아 있는 내 가변 클래스는 그냥 통과한다(3.12 에서 확인).

### (5) 일부러 쓰는 경우도 있다 — 그러나 드물다

```python
def fib(n, memo={}):
    if n in memo:
        return memo[n]
    r = n if n < 2 else fib(n - 1, memo) + fib(n - 2, memo)
    memo[n] = r
    return r

print(fib(30))
print(len(fib.__defaults__[0]))
```

```text
832040
31
```

호출 사이에 남는 성질을 **캐시로 쓴** 것이다. 동작한다.\
그래도 권하지 않는다 — 캐시가 **함수 시그니처에 노출**되고, 크기 제한·초기화 수단이 없고, 읽는 사람이 함정과 구별하지 못한다.\
같은 일을 `functools.lru_cache`(목록의 45번 주제)가 명시적으로 한다.

## 언제 쓰고 언제 안 쓰나

| 기본값 | 판정 |
|---|---|
| `None`, 숫자, 문자열, `True`/`False`, 튜플, `frozenset` | **그대로 써도 된다** — 불변이라 공유돼도 상하지 않는다 |
| 리스트 `[]`, dict `{}`, set `set()` | **쓰지 않는다** — `None` 센티널로 |
| 함수를 불러 만드는 값(`time.now()`, `uuid4()`, 파일 읽기) | **쓰지 않는다** — `def` 때 한 번 고정된다 |
| 바깥 변수(`top=LIMIT`) | 그 값이 **다시는 안 바뀔 때만**. 아니면 호출 시점에 읽는다 |
| 클래스 필드 | `dataclasses.field(default_factory=...)` |

한 줄 규칙: **기본값 자리에는 「안 변하고, 지금 계산해도 되는 것」만 둔다.**

## 구현 세부사항 대 언어 보장

02번 주제와 정확히 반대다. **여기는 전부 언어 보장이다.**

| 사실 | 지위 |
|---|---|
| 기본값 식은 `def` 실행 시점에 왼쪽→오른쪽으로 평가된다 | **언어 보장** — 언어 레퍼런스 8.8 |
| 그 값이 호출마다 재사용된다 | **언어 보장** — 같은 절의 명시 |
| 가변 기본값을 고치면 기본값 자체가 바뀐다 | **언어 보장** — 같은 절이 "generally not what was intended" 라고 경고한다 |
| `None` 센티널이 권장 해법이다 | **문서가 권하는 관용구** |
| `dataclasses` 가 가변 기본값을 `ValueError` 로 거부한다 | **문서화된 동작** (3.7+) |
| `__defaults__` 가 튜플이고 거기에 담긴다 | **언어 보장** — 데이터 모델 |

즉 **「파이썬은 이렇다」라고 적어도 되는 주제**다.\
「CPython 이 그렇다」가 아니라 **어떤 파이썬 구현에서도 이렇게 동작해야 한다.**\
이 구분 자체가 02번과 짝을 이루는 인출 거리다 — 어떤 것이 구현이고 어떤 것이 명세인지 구별할 수 있어야 한다.

## 핵심 문장

- `def` 문은 선언이 아니라 **실행되는 문장**이다. 그 실행 중에 기본값이 계산돼 함수 객체에 붙는다.
- 그래서 기본값은 **함수당 하나**이고 호출마다 새로 생기지 않는다. 가변이면 호출 사이에 상태가 새어 흐른다.
- 고침은 「새로 만드는 일을 `def` 시점에서 호출 시점으로 옮기는 것」이다 — `None` 센티널, 또는 `default_factory`.
- 인자를 넘긴 호출은 멀쩡하므로 **증상이 간헐적으로 보인다.** 테스트가 늘 인자를 넘기면 영영 안 잡힌다.
- 이 주제는 전부 **언어가 보장하는 동작**이다. 02번의 인터닝과 달리 구현이 바뀌어도 그대로다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **20번**
- 선행: 목록의 **03번** 「가변·불변과 얕은 복사·깊은 복사」, **19번** 「함수 인자 규칙」(폴더 아직 없음)
- 함께 보는 곳: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — `is None` / `is MISSING` 을 `==` 로 쓰면 안 되는 이유
- 이어지는 곳: 목록의 **36번** 「`dataclasses`」, **45번** 「`functools`」(폴더 아직 없음)
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/README.md) — 리스트가 가변이라는 것과 `append` 사용법은 그쪽에 있다.\
  이 주제는 그 위에서 **「그 가변성이 함수 기본값 자리에 오면 무엇이 깨지나」**만 다룬다.
- 공식 문서: [8.8. Function definitions](https://docs.python.org/3.12/reference/compound_stmts.html#function-definitions) · [`dataclasses.field`](https://docs.python.org/3.12/library/dataclasses.html#dataclasses.field)

## 용어 풀이

- **기본 인자(default argument)**: 호출할 때 생략하면 대신 쓰이는 값.\
  `def f(x, bag=[])` 의 `[]` 가 그것이다.
- **가변(mutable) / 불변(immutable)**: 만든 뒤에 안을 고칠 수 있는가.\
  리스트·dict·set 은 가변, 숫자·문자열·튜플·frozenset 은 불변이다.
- **`__defaults__`**: 함수 객체에 달린, 위치 인자 기본값들의 튜플.\
  `f.__defaults__[0]` 을 고치면 앞으로의 모든 기본 호출이 그 결과를 본다.
- **`__kwdefaults__`**: 키워드 전용 인자(`*` 뒤에 선언한 것)의 기본값 딕셔너리.
- **평가 시점(evaluation time)**: 어떤 식이 실제로 계산되는 시점.\
  기본값 식의 평가 시점은 **호출 때가 아니라 `def` 문 실행 때**다.
- **센티널(sentinel)**: "값이 없음"을 나타내려고 일부러 만든 표식 객체.\
  `None` 을 쓰고, `None` 자체가 유효한 값이면 `MISSING = object()` 를 만든다.
- **`object()`**: 아무 속성도 없는 가장 단순한 객체 하나.\
  값으로 비교할 것이 없어서 오직 `is` 로만 판정된다 — 센티널에 딱 맞는 성질이다.
- **팩토리(factory)**: 값을 직접 주는 대신 **값을 만드는 함수**를 주는 것.\
  `field(default_factory=list)` 는 "빈 리스트" 가 아니라 "`list` 를 불러라"를 등록한다.
- **메모이제이션(memoization)**: 한 번 계산한 결과를 저장해 두고 다시 물으면 꺼내 쓰는 최적화.\
  `fib(n, memo={})` 가 기본 인자를 그 저장소로 (일부러) 쓴 예다.
- **조용한 실패(silent failure)**: 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
  기본 인자에 쌓인 값은 예외를 내지 않고 결과만 오염시킨다.
