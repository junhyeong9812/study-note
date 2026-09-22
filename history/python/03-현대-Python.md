# 현대 Python (3.5 ~ 3.13)

> 원본: `~/project/python-history/03-현대-Python.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·PEP 번호·Python 코드블록 23개와 「시대를 관통하는 흐름」의 표는 원문 그대로다.\
> ASCII 도식 4개, 「한눈에」의 길·포장 비유(대응표 포함), 3.10 절의 `handle` 함수의 `case` 넷을 옮긴 표 1개, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> async/await로 비동기를, 타입 힌트로 정적 분석을, f-string으로 가독성을, 그리고 마침내 GIL 제거로 진정한 병렬성을 향해 나아간 시대. "느리지만 즐거운 언어"가 "빠르고 안전하면서도 즐거운 언어"로 다시 태어나는 10년.

원문이 그 바로 아래에 이어 적은 문단은 이것이다 — 이 문서가 다루는 범위와 해마다의 테마 순서가 여기에 있다.

> 이 문서는 Python 3.5(2015)부터 3.13(2024)까지를 한 권으로 다룬다. 각 버전마다 **무엇이·언제·왜** 추가되었는지를 코드 예시와 함께 정리한다. 2008년에 등장한 Python 3는 오랫동안 "3.x 전환 고통"의 대명사였지만, 3.5를 기점으로 매년 분명한 테마(비동기 → 타입 → 문법 정제 → 패턴 매칭 → 성능 → 동시성)를 들고 빠르게 진화했다.

이 10년을 하나의 비유로 읽으면 **사람들이 밟아서 생긴 지름길을 뒤늦게 포장하는 일**이다.\
풀밭에 사람들이 자꾸 밟고 다녀 길이 나면, 나중에 그 자리를 그대로 포장해 정식 도로로 만든다.\
**현대 Python의 새 문법도 똑같은 구조다** — 원문 자신이 「시대를 관통하는 흐름 — 정리」 절에서 "새 문법은 대부분 '기존에 어색하던 패턴을 정식 문법으로 승격'한 것"이라고 적고, 그 짝을 넷 든다.

본문 흐름에 쓰는 비유는 이 길 하나뿐이다.

| 비유 | 실체 |
|------|------|
| 사람들이 밟아서 생긴 지름길 | 그 절 마지막 문단의 괄호 안에서 원문이 화살표 왼쪽에 둔 넷 — 콜백 · `%` · 보일러플레이트 · 중첩 if |
| 그 자리를 포장해 만든 정식 도로 | 같은 괄호에서 화살표 오른쪽에 있는 넷 — `async` · f-string · `dataclass` · `match` |
| 길은 그대로인데 그 위를 달리는 차가 빨라진 것 | 원문이 "코드를 한 줄도 바꾸지 않고 인터프리터 업그레이드만으로 빨라진다"고 적은 쪽(3.11~3.13의 성능 축) |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **타입 힌트를 붙여도 실행할 때 타입을 검사하지는 않는다.**\
  원문 표현으로 "런타임 강제는 없다 — 어디까지나 도구를 위한 메타데이터"이고, "인터프리터는 타입을 검사하지 않고, `mypy` 같은 외부 정적 검사기·IDE가 이를 활용한다".
- **GIL이 막는다고 원문이 적은 범위는 한정돼 있다.**\
  원문은 GIL의 대가를 "**CPU 바운드 멀티스레딩에서 멀티코어를 못 살린다**"로 적고, 바로 이어 "그래서 다들 `multiprocessing`으로 우회했다"고 덧붙인다.
- **`async`/`await`가 겨냥한 것은 I/O 대기다.**\
  원문이 적은 쓰임은 "I/O 대기(네트워크·DB)가 많은 서버에서 스레드 없이 수천 개 연결을 한 스레드로 다룰 때"이고, 진짜 CPU 병렬성은 원문이 「시대를 관통하는 흐름 — 정리」 절에서 3.13의 GIL 제거 쪽에 붙인 말이다.

## 시대적 배경 — 3.5 이전의 두 가지 압력

2014~2015년 무렵 Python은 두 방향에서 압력을 받고 있었다.

첫째, **비동기 I/O**.\
Node.js가 "단일 스레드 이벤트 루프로 수만 개 동시 연결"이라는 모델을 대중화하면서, 웹 백엔드의 동시성 처리가 화두가 됐다.\
Python에도 Twisted, gevent, 그리고 3.4의 `asyncio`(이벤트 루프 + `yield from` 기반 코루틴)가 있었지만, 콜백·제너레이터를 비튼 문법이라 진입 장벽이 높았다.

> **비동기 I/O(asynchronous I/O)** — 네트워크·파일 같은 느린 입출력을 걸어 두고, 답이 올 때까지 멈춰 기다리는 대신 그동안 다른 일을 하는 방식.\
> 예: 원문이 든 모델이 Node.js의 "단일 스레드 이벤트 루프로 수만 개 동시 연결"이다 — 연결 수만 개를 스레드 수만 개 없이 다룬다.

> **이벤트 루프(event loop)** — 할 일들을 돌아가며 조금씩 진행시키는 관리자. 원문은 3.4의 `asyncio`를 "이벤트 루프 + `yield from` 기반 코루틴"으로 적는다.\
> 예: 어느 작업이 입출력 응답을 기다리는 동안 다른 작업으로 넘어가는 그 차례 돌리기를 이 루프가 한다.

둘째, **대규모 코드베이스의 타입 안전성**.\
동적 타이핑은 빠른 프로토타이핑에는 좋지만, Dropbox·Instagram 같은 수백만 줄 코드베이스에서는 리팩토링이 공포가 됐다.\
"실행해 보기 전에는 타입 오류를 모른다"는 약점이 도구(IDE 자동완성·정적 분석)의 발목을 잡았다.

> **동적 타이핑(dynamic typing)** — 타입이 맞는지를 **실행하는 시점에** 따지는 방식. 값에 타입이 없다는 뜻이 아니라(값은 늘 타입을 가진다), 그 검사를 실행 전에 해 두지 않는다는 뜻이다.\
> 예: 원문이 적은 그 약점이 이것의 이면이다 — "실행해 보기 전에는 타입 오류를 모른다".

3.5는 이 둘에 동시에 답했다.\
이후의 모든 버전은 이 두 축(비동기·타입)을 다듬고, 거기에 **문법 정제 → 성능 → 병렬성**이라는 새 축을 더해 가는 흐름으로 읽을 수 있다.

---

## Python 3.5 (2015년 9월)

> `async`/`await` 전용 문법, `typing` 표준 모듈, 행렬 곱 `@` 연산자 — 현대 Python의 세 초석이 한꺼번에 놓인 버전.

### 릴리스 정보
- 정식 출시일: 2015년 9월 13일
- 코드 관리: CPython (python.org / PSF)
- 핵심 PEP: 492(async/await), 484(타입 힌트), 465(행렬 곱), 448(언패킹 일반화)

### async / await 전용 문법 (PEP 492)

3.4의 `asyncio`는 코루틴을 "제너레이터 + `@asyncio.coroutine` 데코레이터 + `yield from`"으로 흉내 냈다.\
비동기 코드인지 단순 제너레이터인지 문법만으로는 구분되지 않는 게 문제였다.\
3.5는 **코루틴을 1급 문법으로 승격**했다.

```python
# Before (3.4): 제너레이터를 빌린 코루틴 — 의미가 문법에 드러나지 않음
import asyncio

@asyncio.coroutine
def fetch(url):
    reader = yield from open_connection(url)
    data = yield from reader.read()
    return data
```

```python
# After (3.5): async def / await — "이것은 비동기다"가 문법에 박힘
import asyncio

async def fetch(url):
    reader = await open_connection(url)
    data = await reader.read()
    return data

async def main():
    results = await asyncio.gather(fetch("a"), fetch("b"))   # 동시 실행
    return results
```

- 위가 3.4, 아래가 3.5다 — 두 주석(`# Before (3.4): …`, `# After (3.5): …`)도 원문이 붙여 둔 것이다.
- 달라진 자리는 둘이다 — `@asyncio.coroutine` + `def`가 `async def`로, `yield from`이 `await`로.\
  (아래 블록 끝의 `async def main()` 부분은 위 블록에 대응이 없는, 원문이 덧붙인 예시다.)
- 원문이 "문법만으로는 구분되지 않는 게 문제였다"고 적은 대상이 위쪽 `def fetch`이고, "'이것은 비동기다'가 문법에 박힘"이라고 적은 것이 아래쪽 `async def fetch`다.

> **코루틴(coroutine)** — 도중에 멈췄다가 그 자리에서 다시 이어질 수 있는 함수. 원문은 3.5가 이것을 "1급 문법으로 승격"했다고 적는다.\
> 예: 위 코드의 `async def fetch(url)`가 코루틴이고, `await open_connection(url)`이 그 안에서 멈췄다 이어지는 자리다.

> **`await`** — 그 결과가 올 때까지 **이 코루틴을** 그 자리에 멈춰 두는 표시. 멈춰 있는 동안 스레드가 노는 것이 아니라 같은 스레드가 다른 코루틴을 진행시킨다 — 원문이 이 문법의 쓰임을 "스레드 없이 수천 개 연결을 한 스레드로 다룰 때"라 적은 것이 그 뜻이다.\
> 예: 위 코드의 `await asyncio.gather(fetch("a"), fetch("b"))`에 원문이 "동시 실행"이라는 주석을 달았다 — 스레드가 둘이어서 동시인 것이 아니라, 한쪽이 응답을 기다리는 동안 다른 쪽이 진행돼서 동시다.

`async for`(비동기 이터레이터), `async with`(비동기 컨텍스트 매니저)도 함께 도입됐다.\
**언제·왜**: I/O 대기(네트워크·DB)가 많은 서버에서 스레드 없이 수천 개 연결을 한 스레드로 다룰 때.\
이 문법은 이후 FastAPI·aiohttp·httpx 같은 생태계 전체의 토대가 됐다.

### 타입 힌트와 typing 모듈 (PEP 484)

함수 인자·반환에 타입을 **주석(annotation)으로 명시**하는 표준이 확정됐다.\
핵심은 "런타임 강제는 없다 — 어디까지나 도구를 위한 메타데이터"라는 철학이다.\
인터프리터는 타입을 검사하지 않고, `mypy` 같은 외부 정적 검사기·IDE가 이를 활용한다.

바로 위 문장을 그림으로 두면 이렇다. **초보자가 오해하기 쉬운 자리라 먼저 그려 둔다.**

```text
타입 힌트를 적어 둔 코드
        |
        +---> 인터프리터(실제로 실행하는 쪽)   : 타입을 검사하지 않는다
        |
        +---> mypy 같은 외부 정적 검사기 · IDE : 이 메타데이터를 활용한다
```

- 화살표는 둘이고, 원문 한 문장을 두 갈래로 나눈 것이다 — "인터프리터는 타입을 검사하지 않고, `mypy` 같은 외부 정적 검사기·IDE가 이를 활용한다".
- 그래서 타입 힌트가 틀려도 실행은 그대로 된다. 걸러 주는 것은 실행이 아니라 아래쪽 갈래의 도구다.

```python
from typing import List, Dict, Optional

def greet(name: str, times: int = 1) -> str:
    return f"hi {name}" * times                # (f-string은 3.6부터)

def find_user(uid: int) -> Optional[Dict[str, str]]:
    ...

scores: List[int] = []
```

> **어노테이션(annotation, 주석)** — 인자·변수·반환 **자리에** 붙여 두는 "이 자리에는 이런 타입이 온다"는 표시.\
> 예: 위 코드의 `name: str`이 인자에, `-> str`이 반환에, `scores: List[int]`가 변수에 붙은 어노테이션이다.

> **정적 검사기(static type checker)** — 프로그램을 실행하지 않고 코드만 읽어 타입이 맞는지 따져 보는 도구.\
> 예: 원문이 드는 것이 `mypy`이고, 원문은 Dropbox가 "mypy를 만들며 주도했"다고 적는다.

**언제·왜**: 대규모 코드베이스에서 "이 함수에 뭘 넣고 뭐가 나오나"를 실행 없이 알기 위해.\
Dropbox가 mypy를 만들며 주도했고, 이 PEP 하나가 Python을 "동적 타입 언어이면서도 점진적 정적 타이핑(gradual typing)이 가능한 언어"로 바꿔 놓았다.\
이후 거의 모든 버전이 typing을 보강하는 PEP를 싣는다.

> **점진적 정적 타이핑(gradual typing)** — 전부 다 타입을 적거나 아예 안 적거나가 아니라, 적고 싶은 곳부터 조금씩 적어 나가는 방식(원문이 괄호로 붙인 이름 그대로다).\
> 예: 위 코드의 `greet`에는 인자와 반환에 타입이 붙어 있지만, 타입을 하나도 붙이지 않은 함수도 같은 파일에서 그대로 돌아간다 — 원문이 "동적 타입 언어이면서도"라고 적은 것이 그 뜻이다.

### 행렬 곱 연산자 @ (PEP 465)

NumPy 진영의 오랜 요청이었다.\
`A * B`는 원소별 곱, 행렬 곱은 `A.dot(B)`로 써야 해서 수식이 코드로 옮겨지면 가독성이 무너졌다.\
새 중위 연산자 `@`(`__matmul__`)가 이를 해결했다.

```python
import numpy as np
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

A * B      # 원소별 곱(element-wise)
A @ B      # 행렬 곱(matrix product) — 수식 그대로
```

> **중위 연산자(infix operator)** — 두 값 사이에 기호를 놓아 쓰는 연산자.\
> 예: 위 코드의 `A @ B`가 그것이다 — `A.dot(B)`처럼 이름을 불러 쓰지 않고 두 값 사이에 `@`를 둔다.

**언제·왜**: 선형대수가 핵심인 과학·머신러닝 코드의 가독성.\
표준 라이브러리에는 `@`를 구현한 타입이 없고, 순수하게 NumPy 등 외부 생태계를 위해 문법만 연 이례적 사례다.

### 그 외
- **추가 언패킹 일반화 (PEP 448)**: `[*a, *b]`, `{**d1, **d2}`, `f(*args1, *args2)`처럼 `*`/`**`를 여러 번·여러 곳에 쓸 수 있게 됨.
- `os.scandir()`로 디렉터리 순회 가속, `bytes % args` 포매팅 복원, `RecursionError` 신설.

> **언패킹(unpacking)** — 묶여 있는 값을 풀어서 낱개로 늘어놓는 것.\
> 예: 원문이 든 `[*a, *b]`가 리스트 `a`와 `b`를 각각 풀어 한 리스트에 이어 붙이는 모양이다.

---

## Python 3.6 (2016년 12월)

> f-string으로 문자열 포매팅의 종결자를, 변수 어노테이션으로 타입 힌트의 빈칸을 채운 "일상이 편해진" 버전.

### 릴리스 정보
- 정식 출시일: 2016년 12월 23일
- 핵심 PEP: 498(f-string), 526(변수 어노테이션), 515(숫자 리터럴 `_`), 525/530(비동기 제너레이터·컴프리헨션)

### f-string (PEP 498)

문자열 안에 표현식을 직접 박는 리터럴. `%` 포매팅, `str.format()`, `string.Template`을 한 번에 대체했다.

```python
name, age = "Ada", 36

# Before: 세 가지 방식이 난립
"%s is %d" % (name, age)
"{} is {}".format(name, age)
string.Template("$n is $a").substitute(n=name, a=age)

# After (3.6): f-string — 표현식을 그 자리에
f"{name} is {age}"
f"{name.upper()} next year is {age + 1}"
f"pi = {3.14159:.2f}"          # 포맷 스펙도 그대로
f"{age=}"                       # (3.8부터) 'age=36' 디버깅 출력
```

- 위 블록의 `# Before:` 아래 세 줄이 원문 주석이 "세 가지 방식이 난립"이라 적어 둔 자리이고, `# After (3.6):` 아래가 f-string이다.
- 마지막 줄 `f"{age=}"`에는 원문이 "(3.8부터)"라는 단서를 달아 두었다 — 3.6이 아니라 3.8에서 생긴 것이다.

> **f-string** — 문자열 앞에 `f`를 붙이고, 중괄호 안에 값이나 식을 그대로 적어 넣는 문자열(원문 정의로는 "문자열 안에 표현식을 직접 박는 리터럴").\
> 예: 위 코드의 `f"{name.upper()} next year is {age + 1}"`처럼 중괄호 안에 메서드 호출과 계산식이 그대로 들어간다.

**언제·왜**: 거의 모든 문자열 조립에서.\
변수가 표현식 바로 옆에 있어 가독성이 높고, 다른 방식보다 빠르다(컴파일 타임에 파싱).\
도입 즉시 사실상 표준 포매팅이 됐다.

### 변수 어노테이션 (PEP 526)

3.5는 *함수* 시그니처에만 타입을 달 수 있었다. 3.6은 **변수·클래스 속성**에도 문법을 열었다.

```python
from typing import ClassVar

count: int = 0
names: list           # 값 없이 타입만 선언하는 것도 가능

class Point:
    x: int             # 인스턴스 속성 어노테이션
    y: int
    origin: ClassVar[bool] = False
```

**언제·왜**: 클래스 속성에 타입을 명시해 IDE·정적 검사기가 이해하게 하려고.\
이 문법이 없었다면 다음 해의 `dataclasses`(3.7)는 불가능했다 — 데이터클래스는 바로 이 인스턴스 속성 어노테이션을 읽어 필드를 만든다.

- 다음 절(3.7)의 `dataclass`가 읽는 것이 위 코드의 `x: int` / `y: int` 같은 모양이다.

### 그 외
- **숫자 리터럴 언더스코어 (PEP 515)**: `1_000_000`, `0x_FF_FF`처럼 자릿수 구분.
- **비동기 제너레이터·컴프리헨션 (PEP 525/530)**: `async def` 안에서 `yield`, `[x async for x in gen()]`.
- **dict 순서 보존**: 구현 디테일로서 삽입 순서를 유지하기 시작(3.7에서 언어 보장으로 승격).
- **`__init_subclass__`·`__set_name__`**: 클래스 커스터마이즈 훅 추가.

---

## Python 3.7 (2018년 6월)

> `dataclasses`로 보일러플레이트를, 모듈 `__getattr__`로 API 진화를 해결한 "라이브러리 저자가 행복해진" 버전.

### 릴리스 정보
- 정식 출시일: 2018년 6월 27일
- 핵심 PEP: 557(dataclasses), 562(모듈 `__getattr__`), 563(어노테이션 지연 평가), 567(컨텍스트 변수)

### dataclasses (PEP 557)

데이터를 담는 클래스를 만들 때마다 `__init__`, `__repr__`, `__eq__`를 손으로 쓰던 보일러플레이트를 데코레이터 하나로 자동 생성한다.\
필드는 3.6의 변수 어노테이션으로 선언한다.

```python
# Before: 반복되는 보일러플레이트
class Point:
    def __init__(self, x, y=0):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point(x={self.x!r}, y={self.y!r})"
    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)
```

```python
# After (3.7): 어노테이션만 선언하면 끝
from dataclasses import dataclass, field

@dataclass(frozen=True, order=True)   # 불변·비교가능 옵션
class Point:
    x: int
    y: int = 0
    tags: list = field(default_factory=list)   # 가변 기본값은 factory로

p = Point(1, 2)
print(p)          # Point(x=1, y=2)  ← __repr__ 자동
Point(1, 2) == Point(1, 2)            # True  ← __eq__ 자동
```

- 위 블록에서 손으로 쓴 `__init__`·`__repr__`·`__eq__` 셋이, 아래 블록에서는 `@dataclass` 한 줄로 바뀌었다.
- 아래 블록 주석의 "← `__repr__` 자동"·"← `__eq__` 자동"이 원문이 그 대응을 직접 적어 둔 자리다.
- 아래 블록의 `x: int` / `y: int = 0`이 3.6에서 열린 그 변수 어노테이션이다.

> **보일러플레이트(boilerplate)** — 내용은 거의 같은데 클래스마다 매번 다시 적어야 하는 판박이 코드.\
> 예: 위 「Before」 블록의 `__init__`·`__repr__`·`__eq__` 셋이 그것이고, 원문은 이것을 "손으로 쓰던 보일러플레이트"라 적는다.

> **데이터클래스(dataclass)** — 필드만 어노테이션으로 선언하면 그 판박이 메서드들을 자동으로 만들어 주는 데코레이터.\
> 예: 위 「After」 블록의 `@dataclass(frozen=True, order=True)`가 그것이고, 원문은 이 둘을 묶어 "불변·비교가능 옵션"이라 주석해 두었다.

**언제·왜**: DTO·설정 객체·값 객체처럼 "데이터 + 약간의 동작"인 클래스에서.\
`namedtuple`보다 유연하고(가변·상속·기본값·메서드), 외부 라이브러리(attrs) 없이 표준만으로 해결된다.

### 모듈 수준 __getattr__ (PEP 562)

모듈에 `__getattr__(name)`을 정의하면 **존재하지 않는 모듈 속성 접근을 가로챌 수 있다**.\
주된 용도는 "지연 임포트(lazy import)"와 "부드러운 deprecation 경고".

```python
# mylib/__init__.py
import warnings

def __getattr__(name):
    if name == "old_api":
        warnings.warn("old_api는 폐기 예정, new_api를 쓰세요", DeprecationWarning)
        return new_api
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

- 위 코드에서 가로채는 자리는 `if name == "old_api"` 한 줄이다. 그 이름이면 경고를 띄우고 `new_api`를 대신 돌려준다.
- 없는 이름은 어느 것이든 이 함수가 일단 불린다. 그 밖의 이름은 마지막 줄의 `raise AttributeError(...)`로 가서, 가로챈 뒤 `AttributeError`를 스스로 던져 원래와 같은 결과를 낸다.

> **deprecation(폐기 예정)** — 아직 동작은 하지만 앞으로 없앨 예정이라고 알려 두는 것.\
> 예: 위 코드의 `warnings.warn("old_api는 폐기 예정, new_api를 쓰세요", DeprecationWarning)`가 그 알림이고, 그러면서도 `return new_api`로 동작은 계속 시켜 준다.

**언제·왜**: 라이브러리가 공개 API를 깨지 않고 진화시킬 때.\
무거운 하위 모듈을 실제로 쓸 때까지 임포트를 미뤄 import 시간을 줄이는 데도 쓴다.

### 그 외
- **dict 순서 보존을 언어 차원에서 보장**: 이제 삽입 순서 유지는 구현 디테일이 아니라 공식 명세.
- **`from __future__ import annotations` (PEP 563)**: 어노테이션을 문자열로 지연 평가 → 순환 참조·전방 참조 해소, import 비용 절감.
- **컨텍스트 변수 `contextvars` (PEP 567)**: async 환경에서 스레드 로컬을 대체하는 컨텍스트 인지 상태.
- **`time.perf_counter_ns()` 등 나노초 시간 함수**, **`breakpoint()`** 내장 디버거 진입점.

---

## Python 3.8 (2019년 10월)

> 대입식 `:=`(바다코끼리)와 위치 전용 매개변수 `/` — 표현식과 함수 시그니처를 더 정밀하게 다듬은 버전.

### 릴리스 정보
- 정식 출시일: 2019년 10월 14일
- 핵심 PEP: 572(대입식 `:=`), 570(위치 전용 매개변수), 591(`Final`), 589(`TypedDict`)
- 비고: 채택 과정의 논쟁(PEP 572)이 귀도 반 로섬의 BDFL 은퇴를 촉발한 것으로도 유명하다.

### 대입식 — 바다코끼리 연산자 := (PEP 572)

**표현식 안에서 변수에 값을 대입**한다.\
모양이 바다코끼리의 눈·엄니를 닮았다 해서 walrus operator라 불린다.\
"계산 → 검사 → 재사용"의 중복을 없앤다.

```python
# Before: 같은 값을 두 번 계산하거나, 루프 밖에서 한 번 더 써야 함
data = f.read(1024)
while data:
    process(data)
    data = f.read(1024)

n = len(a)
if n > 10:
    print(f"리스트가 깁니다: {n}개")
```

```python
# After (3.8): 대입과 사용을 한 표현식에
while (data := f.read(1024)):
    process(data)

if (n := len(a)) > 10:
    print(f"리스트가 깁니다: {n}개")

# 컴프리헨션에서 특히 강력 — 비싼 계산을 한 번만
results = [y for x in data if (y := f(x)) is not None]
```

- 위 블록에서 `data = f.read(1024)`가 루프 앞과 루프 안에 두 번 적혀 있고, 아래 블록에서는 `while (data := f.read(1024)):` 한 줄이 그 둘을 대신한다.
- `n = len(a)`와 `if n > 10:` 두 줄도 아래 블록에서 `if (n := len(a)) > 10:` 한 줄이 됐다.

> **대입식(assignment expression, `:=`)** — 값을 변수에 넣는 일을 문장이 아니라 식 안에서 하는 것. 그래서 넣는 동시에 그 값을 조건 검사에 쓸 수 있다.\
> 예: 위 아래 블록의 `if (n := len(a)) > 10:`이 `len(a)`의 결과를 `n`에 넣으면서 동시에 10과 비교한다.

**언제·왜**: while 루프의 read 패턴, if 조건의 결과 재사용, 컴프리헨션에서 비싼 함수 호출을 한 번만 하고 싶을 때.\
남용하면 가독성을 해치므로 "중복을 줄이는 곳"에만.

### 위치 전용 매개변수 / (PEP 570)

함수 시그니처에 `/`를 두면, 그 앞의 매개변수는 **키워드로 호출할 수 없는 위치 전용**이 된다(이미 C 구현 내장 함수들은 그렇게 동작했지만, 순수 Python에선 표현할 문법이 없었다).

```python
def f(a, b, /, c, d, *, e, f):
    ...
#       ^^^^         ^^^
#   a,b는 위치 전용   e,f는 키워드 전용  (c,d는 둘 다 가능)

f(1, 2, 3, d=4, e=5, f=6)     # OK
f(a=1, b=2, ...)               # 에러: a, b는 키워드로 못 줌
```

> **위치 전용 / 키워드 전용 매개변수** — 순서로만 넘길 수 있는 인자 / 이름을 붙여야만 넘길 수 있는 인자.\
> 예: 위 코드에 원문이 직접 표시해 두었다 — `/` 앞의 `a,b`는 위치 전용, `*` 뒤의 `e,f`는 키워드 전용, 그 사이의 `c,d`는 둘 다 가능이다.

**언제·왜**: 라이브러리 저자가 매개변수 이름을 공개 계약에서 빼고 싶을 때 — 이름을 나중에 자유롭게 바꿔도 호출자가 깨지지 않는다.

### 그 외
- **f-string `=` 디버깅 (`f"{x=}"`)**: `x=42`처럼 변수명과 값을 함께 출력.
- **`typing.TypedDict` (PEP 589)·`Literal`·`Final` (PEP 591)·`Protocol` (PEP 544)**: 타입 시스템 대폭 강화 — dict의 키별 타입, 리터럴 값, 재대입 금지, 구조적 서브타이핑.
- **`importlib.metadata`**, **`math.prod`**, **`functools.cached_property`**.

---

## Python 3.9 (2020년 10월)

> dict 병합 `|` 연산자와 내장 제네릭(`list[int]`) — 자잘하지만 매일 쓰는 곳을 매끄럽게 만든 버전.

### 릴리스 정보
- 정식 출시일: 2020년 10월 5일
- 핵심 PEP: 584(dict `|` 연산자), 585(내장 컬렉션 제네릭), 614(데코레이터 문법 완화), 615(zoneinfo)

### dict 병합·갱신 연산자 | / |= (PEP 584)

set에는 `|`(합집합)가 있는데 dict에는 없어서, 두 dict를 합치려면 `{**a, **b}`나 `a.copy(); a.update(b)`를 써야 했다.\
직관적인 연산자가 추가됐다.

```python
defaults = {"theme": "dark", "lang": "en"}
user     = {"lang": "ko"}

# Before
merged = {**defaults, **user}          # 가능하지만 의도가 덜 드러남

# After (3.9)
merged = defaults | user               # {'theme': 'dark', 'lang': 'ko'} — 오른쪽 우선
defaults |= user                       # 제자리 갱신
```

- 두 dict에 모두 있는 키는 `lang` 하나이고, 결과에 남은 값은 원문 주석대로 `'ko'` — 오른쪽 `user`의 값이다.
- 원문이 이것을 "오른쪽 우선"이라 적었다.

**언제·왜**: 기본 설정 위에 사용자 설정을 덮어쓰는 패턴처럼 dict를 합칠 때. set과 일관된 연산자라 직관적이다.

### 내장 컬렉션의 제네릭 (PEP 585)

타입 힌트에 `typing.List`, `typing.Dict`를 임포트해 쓰던 것을, **내장 타입에 직접** `list[int]`, `dict[str, int]`로 쓸 수 있게 됐다.

```python
# Before (3.8): typing에서 대문자 별칭을 임포트
from typing import List, Dict
def f(items: List[int]) -> Dict[str, int]: ...

# After (3.9): 내장 타입이 곧 제네릭
def f(items: list[int]) -> dict[str, int]: ...   # 임포트 불필요
```

> **제네릭(generic)** — "무엇을 담는 무엇"처럼, 담기는 타입을 괄호 안에 끼워 적는 타입.\
> 예: 위 코드의 `list[int]`가 "정수를 담는 리스트", `dict[str, int]`가 "문자열 키에 정수 값인 딕셔너리"다.

**언제·왜**: 타입 힌트를 쓰는 모든 곳에서 import 보일러플레이트가 사라진다. `typing.List` 등은 이후 deprecated 경로로 들어간다.

### 그 외
- **`zoneinfo` (PEP 615)**: IANA 타임존 DB를 표준 라이브러리로 — `ZoneInfo("Asia/Seoul")`. 더 이상 `pytz` 외부 의존이 필수가 아니다.
- **`str.removeprefix()` / `removesuffix()` (PEP 616)**: `"foobar".removeprefix("foo")` → `"bar"`. `strip`의 흔한 오용(문자 집합 제거)을 피한다.
- **데코레이터 문법 완화 (PEP 614)**: `@`에 임의 표현식 허용.

---

## Python 3.10 (2021년 10월)

> 구조적 패턴 매칭 `match`/`case` — 다른 언어의 강력한 분기 문법을 Python답게 들여온, 이 시대의 최대 문법 변화.

### 릴리스 정보
- 정식 출시일: 2021년 10월 4일
- 핵심 PEP: 634/635/636(구조적 패턴 매칭), 604(`X | Y` 유니언), 612·613(타입 보강), 친절한 에러 메시지

### 구조적 패턴 매칭 match / case (PEP 634)

단순한 switch가 아니다.\
**값의 구조를 분해(destructure)하면서 분기**한다 — 시퀀스·매핑·클래스·리터럴을 패턴으로 매칭하고, 동시에 내부 값을 변수로 캡처한다.

```python
def handle(command):
    match command.split():
        case ["go", direction]:                 # 2-요소 시퀀스, 둘째를 캡처
            move(direction)
        case ["drop", *items]:                   # 가변 길이 캡처
            for item in items:
                drop(item)
        case ["quit" | "exit"]:                  # OR 패턴
            sys.exit()
        case _:                                  # 와일드카드(기본값)
            print("알 수 없는 명령")

# 클래스 패턴 — 속성을 분해하며 매칭
def where(point):
    match point:
        case Point(x=0, y=0):
            return "원점"
        case Point(x=0, y=y):                    # y를 캡처
            return f"y축 위 {y}"
        case Point() if point.x == point.y:      # 가드(guard) 조건
            return "대각선"
        case _:
            return "기타"
```

위 `handle` 함수의 네 `case`가 각각 무엇을 잡고 무엇을 꺼내는지를 표로 옮기면 이렇다.

| `case` 줄 | 원문이 단 주석 | 꺼내지는 이름 |
|---|---|---|
| `case ["go", direction]:` | "2-요소 시퀀스, 둘째를 캡처" | `direction` |
| `case ["drop", *items]:` | "가변 길이 캡처" | `items` |
| `case ["quit" \| "exit"]:` | "OR 패턴" | (원문 주석에 캡처 언급 없음) |
| `case _:` | "와일드카드(기본값)" | (원문 주석에 캡처 언급 없음) |

*(가운데 칸은 원문이 그 줄에 달아 둔 주석 그대로이고, 오른쪽 칸은 그 주석이 "캡처"라 부른 이름을 `case` 줄에서 그대로 옮긴 것이다. 아래쪽 `where` 함수의 `case`들은 이 표에 넣지 않았다 — 원문이 그쪽 주석을 두 줄에만 달았다.)*

> **분해(destructure)와 캡처(capture)** — 값의 모양을 쪼개 보면서, 그 안에 든 조각을 변수에 담는 것.\
> 예: 위 코드의 `case ["go", direction]:`이 두 칸짜리 리스트인지 보면서 둘째 칸을 `direction`이라는 이름에 담는다 — 원문 주석대로 "2-요소 시퀀스, 둘째를 캡처"다.

> **가드(guard)** — 패턴에 걸린 뒤에 한 번 더 검사하는 조건.\
> 예: 위 코드의 `case Point() if point.x == point.y:`에서 `if` 뒤가 그것이고, 원문이 "가드(guard) 조건"이라 표시해 두었다.

**언제·왜**: 중첩된 if/elif로 자료구조의 모양을 검사·분해하던 코드 — 인터프리터·파서·이벤트 처리·JSON 같은 트리형 데이터 처리에서.\
단순 동등 비교라면 if가 낫지만, "모양에 따라 분기 + 값 추출"이 섞이면 패턴 매칭이 압도적으로 읽기 쉽다.

### X | Y 유니언 타입 (PEP 604)

`Optional[int]`, `Union[int, str]`을 `int | None`, `int | str`로 간결하게.

```python
# Before
from typing import Optional, Union
def f(x: Optional[int]) -> Union[int, str]: ...

# After (3.10)
def f(x: int | None) -> int | str: ...

isinstance(x, int | str)        # isinstance에서도 동작
```

> **유니언 타입(union type)** — "이 타입이거나 저 타입"이라고 적어 두는 것.\
> 예: 위 코드의 `int | None`이 "정수이거나 없음", `int | str`이 "정수이거나 문자열"이다.

### 그 외
- **훨씬 친절한 에러 메시지**: SyntaxError가 정확한 위치와 원인(닫지 않은 괄호 등)을 짚어 주고, `AttributeError`/`NameError`에 "혹시 이걸 의도했나요?(did you mean)" 제안 추가.
- **`zip(strict=True)`**: 길이가 다른 이터러블을 zip하면 에러.
- 패턴 매칭 도입을 위해 CPython 파서가 LL(1)에서 **PEG 파서**로 교체됨(3.9에서 전환, 3.10에서 본격 활용).

> **파서(parser)** — 소스 코드의 글자를 읽어 문법 구조로 해석하는 부분.\
> 예: 원문이 적은 대로 CPython의 이 부분이 "LL(1)에서 **PEG 파서**로 교체됨"이라 적었고, 그래야 `match`/`case` 같은 문법을 들일 수 있었다.

---

## Python 3.11 (2022년 10월)

> "Faster CPython"의 첫 결실 — **3.10 대비 평균 1.25배, 최대 10~60% 빠른** 인터프리터. 동시에 예외 그룹으로 동시성 에러 처리를 정비.

### 릴리스 정보
- 정식 출시일: 2022년 10월 24일
- 핵심 PEP: 654(예외 그룹·`except*`), 657(정밀 에러 위치), 678(예외 노트), 646(가변 제네릭)
- 핵심 프로젝트: **Faster CPython**(Microsoft 후원, 마크 섀넌 주도)

### 성능 — Faster CPython (10~60% 속도 향상)

3.11은 언어 문법보다 **속도**가 헤드라인이다.\
표준 벤치마크 스위트에서 3.10 대비 평균 **1.25배** 빠르고, 워크로드에 따라 10~60% 향상된다.\
주된 기법은 세 가지다.

- **Adaptive Specializing Interpreter (PEP 659)**: 실행 중 자주 도는 바이트코드를 관찰해, 타입이 안정적이면 더 빠른 특화(specialized) 명령으로 교체한다(인라인 캐싱). 예컨대 `a + b`가 매번 int면 일반 `BINARY_OP` 대신 int 전용 연산으로 바꾼다.
- **Zero-cost exceptions**: `try` 블록 진입 비용을 없앴다. 예외가 발생하지 않는 한 `try`는 공짜에 가깝고, 예외 처리 자체도 약 10% 빨라졌다.
- **더 빠른 함수 호출**: 프레임 객체를 경량화하고 파이썬→파이썬 호출에서 C 스택 재귀를 제거.

첫 번째 불릿이 원문이 든 예(`a + b`)로 어떻게 돌아가는지를 세로로 펴면 이렇다.

```text
같은 a + b 줄을 여러 번 실행하는 동안

처음      일반 BINARY_OP 로 실행        어떤 타입이 올지 정해지지 않은 명령
  |
  |       (실행 중 관찰 — a + b 가 매번 int)
  v
그 뒤     int 전용 연산으로 교체        원문 표현으로 "더 빠른 특화 명령"
```

- 화살표는 하나이고, 원문 문장의 "관찰해 … 교체한다"가 그 한 걸음이다.
- 칸 안의 `BINARY_OP`·`int 전용 연산`·`a + b`는 전부 원문이 든 이름이다.
- 원문은 이 교체를 "타입이 안정적이면"이라는 조건 아래 적는다 — 늘 일어나는 것이 아니라 관찰 결과에 달려 있다.

> **바이트코드(bytecode)** — 인터프리터가 실제로 읽어 돌리는 명령 목록. 소스 코드가 글자 그대로 실행되는 게 아니라 이 형태를 한 번 거친다(원문은 바이트코드를 정의하지 않고 실행·관찰의 대상으로만 쓴다 — 이 한 줄 설명은 원문 밖에서 보탠 것이다).\
> 예: 원문이 "실행 중 자주 도는 바이트코드를 관찰해"라고 할 때 관찰되는 것이 이것이고, 위 그림의 `BINARY_OP`가 그 명령 하나다.

> **인라인 캐싱(inline caching)** — 방금 본 결과를 그 명령 자리에 기억해 두었다가 다음번에 곧장 쓰는 것(원문이 괄호로 붙인 이름 그대로다).\
> 예: 위 그림에서 `a + b`가 매번 int였다는 관찰 결과가 그 자리에 남아, 다음 실행부터 int 전용 연산이 쓰인다.

```python
# 같은 코드인데 그냥 더 빠르다 — 재작성이 필요 없는 게 핵심
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
```

**언제·왜**: 코드를 한 줄도 바꾸지 않고 인터프리터 업그레이드만으로 빨라진다.\
CPython이 "느리다"는 오랜 약점에 본격적으로 대응하기 시작한 전환점이며, 이 흐름은 3.12·3.13으로 이어진다.

### 예외 그룹과 except* (PEP 654)

여러 개의 **서로 무관한 예외를 동시에** 발생·처리한다.\
동기 코드에선 드물지만, `asyncio.gather`처럼 여러 작업을 병렬 실행하면 동시에 여러 예외가 터질 수 있는데 기존 `except`로는 하나밖에 못 잡았다.

```python
# 여러 예외를 묶어서 던지고, except* 로 종류별로 골라 잡는다
try:
    raise ExceptionGroup("동시 작업 실패", [
        ValueError("잘못된 값"),
        TypeError("타입 오류"),
        KeyError("없는 키"),
    ])
except* ValueError as eg:
    print("값 오류 처리:", eg.exceptions)
except* (TypeError, KeyError) as eg:
    print("타입/키 오류 처리:", eg.exceptions)
```

위 코드의 예외 셋이 `except*` 둘에 어떻게 갈리는지를 그리면 이렇다.

```text
ExceptionGroup("동시 작업 실패")
  |
  +-- ValueError("잘못된 값") ----> except* ValueError
  |
  +-- TypeError("타입 오류") -----> except* (TypeError, KeyError)
  |                                 (같은 곳)
  +-- KeyError("없는 키") --------> except* (TypeError, KeyError)
```

- 그림 안의 예외 셋과 `except*` 둘은 전부 위 코드에 있는 것이다. 셋과 둘이라는 개수도 코드에서 센 것이다.
- 화살표 셋은 "종류별로 골라 잡는다"는 원문 주석을 예외 하나씩으로 편 것이다.
- 원문이 "기존 `except`로는 하나밖에 못 잡았다"고 적은 것은 **묶음 문법이 없던 때** 얘기다 — `asyncio.gather`로 여러 작업을 돌릴 때 동시에 터진 예외 중 하나만 손에 쥐던 옛 상황을 가리킨다. 위 그림처럼 묶어 던지고 종류별로 갈라 잡는 일 자체가 `except*`가 생기고 나서 가능해진 것이다.

> **예외 그룹(ExceptionGroup)** — 서로 무관한 예외 여러 개를 하나로 묶어 함께 던지는 것.\
> 예: 위 코드의 `ExceptionGroup("동시 작업 실패", [...])`가 `ValueError`·`TypeError`·`KeyError` 셋을 한 묶음으로 던진다.

> **`except*`** — 그 묶음에서 내가 잡을 종류만 골라 잡는 문법.\
> 예: 위 코드의 `except* (TypeError, KeyError)`가 묶음 안에서 그 두 종류만 골라 받고, `ValueError`는 앞의 `except* ValueError`가 받는다.

함께 도입된 `asyncio.TaskGroup`이 이 위에서 동작한다 — 그룹 안 여러 태스크의 실패를 ExceptionGroup으로 모아 준다.

```python
async def main():
    async with asyncio.TaskGroup() as tg:       # 3.11 신설
        tg.create_task(fetch("a"))
        tg.create_task(fetch("b"))
    # 블록을 벗어나면 모든 태스크 완료 보장, 실패는 ExceptionGroup으로
```

### 그 외
- **정밀 에러 위치 (PEP 657)**: 트레이스백이 줄뿐 아니라 그 줄에서 **정확히 어느 표현식**이 터졌는지 `^^^^`로 가리킨다.
- **예외 노트 `add_note()` (PEP 678)**: 발생한 예외에 문맥 정보를 덧붙여 다시 던지기.
- **`typing.Self`·`LiteralString`·가변 제네릭(PEP 646)**, **`tomllib`**(TOML 파서 표준 탑재).

> **트레이스백(traceback)** — 예외가 났을 때 어디를 거쳐 그 지점까지 왔는지 보여 주는 목록.\
> 예: 원문이 적은 3.11의 개선이 이것이다 — "줄뿐 아니라 그 줄에서 **정확히 어느 표현식**이 터졌는지 `^^^^`로 가리킨다".

---

## Python 3.12 (2023년 10월)

> f-string의 마지막 제약을 풀고(PEP 701), 제네릭·타입 별칭을 위한 전용 문법(PEP 695)을 들인 "타입과 문자열의 완성도" 버전.

### 릴리스 정보
- 정식 출시일: 2023년 10월 2일
- 핵심 PEP: 701(f-string 정식 문법화), 695(타입 매개변수 문법), 698(`@override`), 709(컴프리헨션 인라인)

### f-string 문법 정식화 (PEP 701)

3.6의 f-string은 파서에 특수 처리된 "반쪽 문법"이라 제약이 많았다.\
같은 종류의 따옴표 재사용 불가, 백슬래시 불가, 여러 줄·주석 불가.\
3.12는 f-string을 **정식 문법으로 끌어올려** 이 모든 제약을 없앴다.

```python
# Before (~3.11): 안쪽에서 같은 따옴표를 못 써서 우회해야 함
data = {"name": "Ada"}
f"{data['name']}"          # OK지만 바깥이 작은따옴표면 충돌
# f"{data["name"]}"        # SyntaxError

# After (3.12): 따옴표 재사용·여러 줄·주석·백슬래시 모두 허용
f"{data["name"]}"                       # 같은 따옴표 OK
f"{ '\n'.join(items) }"                 # 백슬래시 OK
f"""{
    value                               # 여러 줄 + 주석 OK
}"""
```

- 원문이 든 제약 셋이 「After」 블록의 주석 셋과 그대로 맞물린다 — "같은 따옴표 OK", "백슬래시 OK", "여러 줄 + 주석 OK".
- 같은 `f"{data["name"]}"`가 「Before」에서는 주석 처리된 채 `# SyntaxError`로 적혀 있고, 「After」에서는 살아 있는 줄이다.

### 타입 매개변수 문법 (PEP 695)

제네릭 클래스·함수와 타입 별칭을 위한 **전용 문법**이 생겼다. 기존에는 `TypeVar`를 따로 선언하고 `Generic`을 상속해야 했다.

```python
# Before: TypeVar 선언 + Generic 상속, 별칭은 명시적 TypeAlias
from typing import TypeVar, Generic, TypeAlias
T = TypeVar("T")
class Stack(Generic[T]):
    def push(self, item: T) -> None: ...
Vector: TypeAlias = list[float]

# After (3.12): 대괄호로 타입 매개변수를 그 자리에 선언
class Stack[T]:                         # TypeVar·Generic 불필요
    def push(self, item: T) -> None: ...

def first[T](items: list[T]) -> T:      # 제네릭 함수
    return items[0]

type Vector = list[float]               # type 문 — 1급 타입 별칭
```

- 「Before」의 `T = TypeVar("T")`와 `Generic[T]` 상속 두 가지가, 「After」에서는 `class Stack[T]:`의 대괄호 하나로 줄었다 — 원문 주석이 그 자리에 "TypeVar·Generic 불필요"라고 적어 둔 그대로다.
- `Vector: TypeAlias = list[float]`는 `type Vector = list[float]`가 됐다.

> **타입 별칭(type alias)** — 긴 타입 표기에 짧은 이름을 붙여 두는 것.\
> 예: 위 코드의 `type Vector = list[float]`가 `list[float]`에 `Vector`라는 이름을 붙인 것이고, 원문은 이 `type` 문을 "1급 타입 별칭"이라 적는다.

**언제·왜**: 제네릭을 쓰는 라이브러리에서 보일러플레이트(TypeVar 선언)를 없애고, 스코프 규칙도 명확해진다.\
다른 정적 타입 언어(TypeScript·Java)와 비슷한 모양이 되어 진입 장벽이 낮아졌다.

### 그 외
- **Per-interpreter GIL (PEP 684)**: 서브인터프리터마다 독립 GIL을 가질 수 있는 기반(C-API 수준) — 3.13의 동시성 작업으로 이어지는 토대.
- **`@override` 데코레이터 (PEP 698)**: 부모 메서드를 오버라이드한다는 의도를 명시 → 오타나 시그니처 변경 시 정적 검사기가 잡음.
- **컴프리헨션 인라인화 (PEP 709)**: 리스트/딕트/셋 컴프리헨션이 별도 함수 프레임 없이 인라인 실행 → 최대 2배 빠름.
- **개선된 에러 메시지**: `import` 오타, `self.` 누락 등에 구체적 제안.

---

## Python 3.13 (2024년 10월)

> **GIL 제거(experimental free-threading)와 JIT 컴파일러** — Python의 30년 숙원 두 개에 동시에 손댄, 이 시대의 정점이자 다음 시대의 문.

### 릴리스 정보
- 정식 출시일: 2024년 10월 7일
- 핵심 PEP: 703(free-threaded·GIL 비활성화), 744(JIT 컴파일러), 667(`locals()` 의미 명확화)
- 비고: free-threading과 JIT 모두 **실험적(experimental)** — 기본 빌드에는 꺼져 있고, 별도 빌드/옵션으로 활성화한다.

### GIL 제거 — Free-Threaded CPython (PEP 703, 실험적)

**GIL**(Global Interpreter Lock)은 "한 번에 한 스레드만 바이트코드를 실행"하게 강제하는 락으로, CPython이 메모리 관리를 단순·안전하게 유지해 온 장치다.\
대가로 **CPU 바운드 멀티스레딩에서 멀티코어를 못 살린다**는 게 30년 묵은 약점이었다(그래서 다들 `multiprocessing`으로 우회했다).

3.13은 GIL을 **끌 수 있는** 특수 빌드(`python3.13t`, free-threaded build)를 실험적으로 제공한다.

```python
import sys
# free-threaded 빌드인지 확인
print(sys._is_gil_enabled())     # free-threaded 빌드에선 False

from concurrent.futures import ThreadPoolExecutor

def cpu_heavy(n):
    return sum(i * i for i in range(n))

# GIL 없는 빌드에서는 이 스레드들이 진짜로 여러 코어에서 병렬 실행된다
with ThreadPoolExecutor(max_workers=8) as ex:
    results = list(ex.map(cpu_heavy, [10_000_000] * 8))
```

두 빌드를 나란히 놓으면 이렇다.

```text
GIL 이 켜진 기본 빌드                free-threaded 빌드 (python3.13t)
+------------------------------+     +------------------------------+
| 한 번에 한 스레드만          |     | 이 스레드들이 진짜로         |
| 바이트코드를 실행            |     | 여러 코어에서 병렬 실행      |
+------------------------------+     +------------------------------+
 CPU 바운드 멀티스레딩에서            sys._is_gil_enabled() 가
 멀티코어를 못 살린다                 False 인 빌드
 (그래서 다들 multiprocessing
  으로 우회했다)
```

- 두 칸의 대립축은 원문의 대립축 그대로다 — **GIL이 켜져 있느냐, 끌 수 있는 빌드냐**.
- 칸 안과 아래의 문구는 원문에서 왔다. 왼쪽 두 덩어리는 이 절 첫 문단의 문장이고, 오른쪽 위는 원문 코드의 주석("GIL 없는 빌드에서는 이 스레드들이 진짜로 여러 코어에서 병렬 실행된다")이다.\
  오른쪽 아래 한 줄만 원문 코드의 `print(sys._is_gil_enabled())` 줄과 그 주석("free-threaded 빌드에선 False")을 합쳐 적은 것이다.
- 왼쪽 아래 괄호가 중요하다. 원문이 GIL의 약점을 **CPU 바운드 멀티스레딩**으로 한정하고, 그 우회책으로 `multiprocessing`을 들었다는 뜻이다.
- 이 그림은 두 빌드를 대비할 뿐, 어느 쪽이 다른 쪽으로 넘어간다는 화살표를 그리지 않았다 — 원문은 free-threaded를 "특수 빌드"로 적지 기본 빌드를 대체한다고 적지 않는다.

> **GIL(Global Interpreter Lock)** — 원문 정의 그대로 "한 번에 한 스레드만 바이트코드를 실행"하게 강제하는 락. CPython이 메모리 관리를 단순·안전하게 유지해 온 장치다.\
> 예: 원문이 든 그 대가가 "CPU 바운드 멀티스레딩에서 멀티코어를 못 살린다"이고, 그래서 "다들 `multiprocessing`으로 우회했다".

> **CPU 바운드 / I/O 대기** — 계산하느라 CPU를 계속 쓰는 일 / 네트워크·디스크의 답을 기다리는 일.\
> 예: 위 코드의 `cpu_heavy(n)`이 앞쪽이고, 3.5 절의 `await open_connection(url)`이 뒤쪽이다 — 원문이 GIL의 약점을 앞쪽에, `async`의 쓰임을 뒤쪽에 붙여 적었다.

> **`multiprocessing`** — 스레드가 아니라 프로세스를 여러 개 띄워 일을 나누는 표준 모듈.\
> 예: 원문이 적은 대로 GIL 때문에 "다들 `multiprocessing`으로 우회했다" — 3.13이 하려는 것은 그 우회 없이 스레드로 하는 것이다.

**언제·왜**: CPU 바운드 작업(수치 계산·이미지 처리)을 프로세스 분리 없이 스레드로 병렬화하고 싶을 때.

**대가는 무엇인가** — 원문이 같은 문단에서 비용으로 적은 문장은 이것이다.

> 다만 단일 스레드 성능은 다소 떨어지고, C 확장 호환성·생태계 대응이 남아 있어 **아직 실험적**이다.

원문은 그 바로 뒤에 의의를 덧붙인다(손실이 아니라 평가다) — **그럼에도 "Python에서 GIL은 영원하다"는 통념을 깬, 방향을 바꾼 사건이다.**

### JIT 컴파일러 (PEP 744, 실험적)

자주 실행되는 코드 경로를 런타임에 기계어로 컴파일하는 **JIT**(Just-In-Time)가 처음 들어왔다.\
**copy-and-patch** 방식의 가벼운 JIT으로, 3.11의 특화 인터프리터가 만든 마이크로옵 추적을 기반으로 한다.

```python
# 코드 변경 없음 — 핫 루프를 런타임에 기계어로 컴파일
# 빌드 시 --enable-experimental-jit 로 켠다
def hot_loop():
    total = 0
    for i in range(10_000_000):
        total += i * i
    return total
```

> **JIT(Just-In-Time)** — 원문 정의 그대로 "자주 실행되는 코드 경로를 런타임에 기계어로 컴파일하는" 것.\
> 예: 위 코드의 `for i in range(10_000_000):` 루프가 원문 주석이 말하는 "핫 루프"이고, 그 부분이 돌아가는 도중에 기계어로 바뀐다.

**언제·왜**: 3.13 시점의 성능 향상은 **미미하다(modest)** — 당장의 속도보다, 앞으로 몇 개 버전에 걸쳐 키워 갈 **인프라의 첫 삽**이라는 의미가 크다. 기본 비활성·옵트인.

### 새 대화형 인터프리터 (REPL)

PyPy의 코드를 기반으로 REPL을 새로 썼다.\
**여러 줄 편집·히스토리 보존·컬러 출력·블록 단위 들여쓰기**를 지원한다 — 이전엔 여러 줄 함수 정의를 위로 올려 고쳐 다시 실행하는 게 불가능했다.

> **REPL(대화형 인터프리터)** — 한 줄 치면 바로 실행해 결과를 보여 주는 대화창.\
> 예: 원문이 적은 3.13의 개선이 그 안에서의 편집 경험이다 — "여러 줄 편집·히스토리 보존·컬러 출력·블록 단위 들여쓰기".

### 그 외
- **개선된 에러 메시지**에 컬러 트레이스백, **`locals()` 의미 명확화 (PEP 667)**.
- **타입 보강**: `typing.TypeIs` (PEP 742, 타입 좁히기), 제네릭 타입 매개변수의 **기본값** (PEP 696), `warnings.deprecated` 데코레이터 (PEP 702).
- **점진적 표준 라이브러리 정리 (PEP 594, "dead batteries")**: 오래된 모듈 다수 제거.

---

## 시대를 관통하는 흐름 — 정리

*(이 편의 「남긴 것」에 해당한다 — 아래 표·세 물줄기·마지막 문단은 전부 원문의 것이다.\
표의 3.9·3.10 행에 든 `` `|` ``는 표가 칸으로 잘리지 않도록 `` \| ``로 이스케이프했다 — 렌더링만 바뀌고 글자는 원문 그대로다.)*

| 버전 | 연도 | 한 줄 테마 | 대표 기능 |
|------|------|-----------|-----------|
| 3.5 | 2015 | 비동기·타입의 초석 | `async`/`await`, `typing`, `@` |
| 3.6 | 2016 | 일상 가독성 | f-string, 변수 어노테이션 |
| 3.7 | 2018 | 보일러플레이트 제거 | `dataclasses`, 모듈 `__getattr__` |
| 3.8 | 2019 | 문법 정밀화 | 바다코끼리 `:=`, 위치 전용 `/` |
| 3.9 | 2020 | 매끄러운 다듬기 | dict `\|`, 내장 제네릭 `list[int]` |
| 3.10 | 2021 | 구조적 분기 | `match`/`case`, `X \| Y` 유니언 |
| 3.11 | 2022 | 속도 | Faster CPython(+10~60%), 예외 그룹 |
| 3.12 | 2023 | 타입·문자열 완성 | f-string 정식화, `class C[T]` |
| 3.13 | 2024 | 병렬성의 문 | GIL 제거(실험), JIT(실험), 새 REPL |

세 개의 큰 물줄기가 보인다.

1. **타입 시스템의 점진적 완성** (3.5 → 3.13): `typing` 도입(3.5) → 변수 어노테이션(3.6) → 내장 제네릭(3.9) → `X | Y`(3.10) → 전용 문법 `class C[T]`(3.12) → 제네릭 기본값(3.13). "동적 타입이지만 원하면 정적으로 검증되는" 언어로 일관되게 진화했다.
2. **비동기 → 동시성의 완성** (3.5 → 3.13): `async`/`await`(3.5) → 예외 그룹·TaskGroup(3.11) → GIL 제거(3.13). I/O 동시성에서 시작해 마침내 진짜 CPU 병렬성까지.
3. **성능의 부상** (3.11 →): Faster CPython(3.11) → 컴프리헨션 인라인(3.12) → JIT(3.13). "Python은 느리다"는 명제에 정면으로 답하기 시작했다.

읽는 사람이 가져갈 핵심: **새 문법은 대부분 "기존에 어색하던 패턴을 정식 문법으로 승격"한 것**이다(콜백→`async`, `%`→f-string, 보일러플레이트→`dataclass`, 중첩 if→`match`). 그래서 "이 기능을 왜 쓰나"는 거의 항상 "그 전에 무엇이 불편했나"를 보면 답이 나온다.

## 용어 풀이

- **비동기 I/O(asynchronous I/O)** — 느린 입출력을 걸어 두고 답을 기다리는 동안 다른 일을 하는 방식. 3.5 이전의 두 압력 중 하나다.
- **이벤트 루프(event loop)** — 할 일들을 돌아가며 조금씩 진행시키는 관리자. 3.4의 `asyncio`가 이것과 `yield from` 기반 코루틴으로 돼 있었다.
- **코루틴(coroutine)** — 도중에 멈췄다 그 자리에서 이어지는 함수. 3.5가 이것을 1급 문법으로 승격했다.
- **`async` / `await`** — 코루틴을 정의하고(`async def`), 그 안에서 결과가 올 때까지 **그 코루틴만** 멈춰 두는(`await`) 문법. 멈춘 동안 같은 스레드는 다른 코루틴을 진행시킨다. 원문이 적은 쓰임은 I/O 대기가 많은 서버다.
- **동적 타이핑(dynamic typing)** — 타입이 맞는지를 실행하는 시점에 따지는 방식(값이 타입을 안 가진다는 뜻이 아니다 — 실행 전에 검사하지 않는다는 뜻이다). "실행해 보기 전에는 타입 오류를 모른다"가 그 약점이다.
- **타입 힌트 / 어노테이션(annotation)** — 인자·반환·변수에 타입을 적어 두는 표시. **런타임 강제는 없다.**
- **정적 검사기(static type checker)** — 실행하지 않고 코드만 읽어 타입을 따지는 도구. `mypy`가 그것이다.
- **점진적 정적 타이핑(gradual typing)** — 적고 싶은 곳부터 조금씩 타입을 적어 나가는 방식.
- **제네릭(generic)** — 담기는 타입을 괄호 안에 끼워 적는 타입. 3.9부터 `list[int]`처럼 내장 타입에 직접 쓴다.
- **유니언 타입(union type)** — "이 타입이거나 저 타입". 3.10부터 `int | None`으로 쓴다.
- **타입 별칭(type alias)** — 긴 타입 표기에 짧은 이름을 붙인 것. 3.12의 `type Vector = list[float]`가 그 문법이다.
- **중위 연산자(infix operator)** — 두 값 사이에 기호를 놓는 연산자. 3.5의 행렬 곱 `@`가 그렇게 들어왔다.
- **언패킹(unpacking)** — 묶인 값을 풀어 낱개로 늘어놓는 것. 3.5의 PEP 448이 이것을 여러 번·여러 곳에 쓸 수 있게 했다.
- **f-string** — 중괄호 안에 식을 그대로 적어 넣는 문자열. 3.6에 들어와 3.12에서 정식 문법이 됐다.
- **보일러플레이트(boilerplate)** — 매번 다시 적어야 하는 판박이 코드. 3.7의 `dataclasses`가 겨냥한 것이다.
- **데이터클래스(dataclass)** — 어노테이션으로 선언한 필드에서 `__init__`·`__repr__`·`__eq__`를 자동 생성하는 데코레이터.
- **deprecation(폐기 예정)** — 아직 동작하지만 앞으로 없앤다고 알려 두는 것. 3.7의 모듈 `__getattr__`의 주된 용도 중 하나다.
- **대입식(`:=`, 바다코끼리)** — 식 안에서 변수에 값을 넣는 것. 3.8에 들어왔고, 그 논쟁이 BDFL 은퇴를 촉발했다.
- **위치 전용 / 키워드 전용 매개변수** — 순서로만 넘기는 인자 / 이름을 붙여야 넘기는 인자. 그 경계가 `/`(3.8이 들인 것)와 `*`다.
- **구조적 패턴 매칭(`match`/`case`)** — 값의 구조를 분해하면서 분기하는 문법. 3.10의 최대 문법 변화다.
- **분해(destructure) / 캡처(capture)** — 값의 모양을 쪼개 보는 것 / 그 조각을 변수에 담는 것.
- **가드(guard)** — 패턴에 걸린 뒤 한 번 더 보는 조건. `case Point() if point.x == point.y:`의 `if` 뒤다.
- **파서(parser)** — 소스의 글자를 문법 구조로 해석하는 부분. 패턴 매칭을 위해 LL(1)에서 PEG 파서로 교체됐다.
- **바이트코드(bytecode)** — 인터프리터가 실제로 읽어 돌리는 명령 목록. 3.11의 특화도 GIL의 제약도 이것을 대상으로 한다.
- **Adaptive Specializing Interpreter / 인라인 캐싱** — 자주 도는 바이트코드를 관찰해 타입이 안정적이면 더 빠른 특화 명령으로 바꾸는 것.
- **Zero-cost exceptions** — 예외가 안 나는 한 `try` 진입이 공짜에 가깝도록 만든 3.11의 기법.
- **예외 그룹(ExceptionGroup) / `except*`** — 무관한 예외 여럿을 한 묶음으로 던지는 것 / 그 묶음에서 종류별로 골라 잡는 문법.
- **트레이스백(traceback)** — 예외가 어디를 거쳐 왔는지 보여 주는 목록. 3.11부터 터진 표현식을 `^^^^`로 짚는다.
- **GIL(Global Interpreter Lock)** — 한 번에 한 스레드만 바이트코드를 실행하게 강제하는 락. 대가는 CPU 바운드 멀티스레딩에서 멀티코어를 못 살리는 것이다.
- **free-threaded build (`python3.13t`)** — GIL을 끌 수 있는 3.13의 특수 빌드. 실험적이다.
- **CPU 바운드 / I/O 대기** — 계산하느라 CPU를 계속 쓰는 일 / 네트워크·디스크의 답을 기다리는 일.
- **`multiprocessing`** — 프로세스를 여러 개 띄워 일을 나누는 모듈. GIL을 우회하던 표준 수단이다.
- **JIT(Just-In-Time)** — 자주 실행되는 코드 경로를 런타임에 기계어로 컴파일하는 것. 3.13에 실험적으로 들어왔다.
- **REPL(대화형 인터프리터)** — 치면 바로 실행해 보여 주는 대화창. 3.13이 PyPy 코드를 기반으로 새로 썼다.

---

## 참고 출처

### 공식 What's New
- [What's New In Python 3.5 (docs.python.org)](https://docs.python.org/3/whatsnew/3.5.html)
- [What's New In Python 3.6](https://docs.python.org/3/whatsnew/3.6.html)
- [What's New In Python 3.7](https://docs.python.org/3/whatsnew/3.7.html)
- [What's New In Python 3.8](https://docs.python.org/3/whatsnew/3.8.html)
- [What's New In Python 3.9](https://docs.python.org/3/whatsnew/3.9.html)
- [What's New In Python 3.10](https://docs.python.org/3/whatsnew/3.10.html)
- [What's New In Python 3.11](https://docs.python.org/3/whatsnew/3.11.html)
- [What's New In Python 3.12](https://docs.python.org/3/whatsnew/3.12.html)
- [What's New In Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)

### 핵심 PEP
- [PEP 492 – Coroutines with async and await syntax](https://peps.python.org/pep-0492/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [PEP 465 – A dedicated infix operator for matrix multiplication](https://peps.python.org/pep-0465/)
- [PEP 498 – Literal String Interpolation (f-strings)](https://peps.python.org/pep-0498/)
- [PEP 526 – Syntax for Variable Annotations](https://peps.python.org/pep-0526/)
- [PEP 557 – Data Classes](https://peps.python.org/pep-0557/)
- [PEP 562 – Module __getattr__ and __dir__](https://peps.python.org/pep-0562/)
- [PEP 572 – Assignment Expressions (walrus)](https://peps.python.org/pep-0572/)
- [PEP 570 – Python Positional-Only Parameters](https://peps.python.org/pep-0570/)
- [PEP 584 – Add Union Operators To dict](https://peps.python.org/pep-0584/)
- [PEP 585 – Type Hinting Generics In Standard Collections](https://peps.python.org/pep-0585/)
- [PEP 634 – Structural Pattern Matching: Specification](https://peps.python.org/pep-0634/)
- [PEP 604 – Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [PEP 654 – Exception Groups and except*](https://peps.python.org/pep-0654/)
- [PEP 659 – Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/)
- [PEP 701 – Syntactic formalization of f-strings](https://peps.python.org/pep-0701/)
- [PEP 695 – Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [PEP 703 – Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)
- [PEP 744 – JIT Compilation](https://peps.python.org/pep-0744/)
