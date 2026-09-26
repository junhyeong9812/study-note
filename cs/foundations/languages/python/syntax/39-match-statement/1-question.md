# python/syntax/39-match-statement — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **`match` 뒤의 이름 값까지** 적어야 맞은 것이다.
> ★★★ 2번은 소스 넷이 **각각 실행되나, 막히나**를 먼저 가르고, 막히면 **진단 전문 — 몇 줄이고 캐럿이 있나 —** 까지 적는다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [11](../11-tuple-and-unpacking/1-question.md)(언패킹) · [21](../21-scope-legb-global-nonlocal/1-question.md)(스코프) ·
> [36](../36-dataclasses/1-question.md)(`__match_args__`) · [37](../37-enum/1-question.md)(열거형 멤버).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 상수 이름을 `case` 에 쓰면 (예측)

```python
# e39_capture.py
red = "red"
RED = "red"


class Palette:
    RED = "red"


print("① 모듈 수준에서 bare 이름 red 로 비교하려 했다")
color = "blue"
match color:
    case red:
        print("   red 갈래에 들어왔다")
print("   match 뒤의 red :", repr(red))

print("② 대문자 RED 도 똑같이 써 본다")
color = "green"
match color:
    case RED:
        print("   RED 갈래에 들어왔다")
print("   match 뒤의 RED :", repr(RED))

print("③ 점이 있는 이름 Palette.RED")
for color in ("red", "blue"):
    match color:
        case Palette.RED:
            print("   %-5s -> Palette.RED 갈래" % color)
        case _:
            print("   %-5s -> _ 갈래" % color)

print("④ 함수 안에서")
LIMIT = 10


def check(n):
    match n:
        case LIMIT:
            return "LIMIT 갈래, LIMIT=%r" % LIMIT


print("   check(3)  :", check(3))
print("   전역 LIMIT :", LIMIT)
print("   check 의 지역 이름 :", check.__code__.co_varnames)

print("⑤ 캡처에 가드를 붙이고 뒤에 case 를 하나 더")


def guarded(n):
    match n:
        case x if x == LIMIT:
            return "가드 갈래"
        case _:
            return "_ 갈래"


print("   guarded(10) :", guarded(10), "/ guarded(3) :", guarded(3))
```

### 2. ★★★ 네 소스를 각각 던지면 (예측)

```python
# e39_unreachable.py
red = "red"
color = "blue"
match color:
    case red:
        print("red 갈래")
    case "blue":
        print("blue 갈래")
```

```python
# e39_wildcard_first.py
match "blue":
    case _:
        print("_ 갈래")
    case "blue":
        print("blue 갈래")
```

```python
# e39_or_names.py
match (1, 2):
    case (a, 0) | (0, b):
        print(a, b)
```

```python
# e39_double_star_underscore.py
match {"k": 1}:
    case {"k": 1, **_}:
        print("k 갈래")
```

### 3. ★★ 대상마다 가는 갈래 (예측)

```python
# e39_kinds.py
from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    RED = 1


@dataclass
class Pt:
    x: int
    y: int


def kind(subject):
    match subject:
        case None:
            return "리터럴(None)"
        case 0 | 1:
            return "OR(리터럴 0 | 1)"
        case Color.RED:
            return "값(Color.RED)"
        case ("g"):
            return "그룹((\"g\"))"
        case [first, *rest]:
            return "시퀀스 first=%r rest=%r" % (first, rest)
        case {"op": op}:
            return "매핑 op=%r" % op
        case Pt(0, y):
            return "클래스(위치) y=%r" % y
        case Pt(x=x, y=0):
            return "클래스(키워드) x=%r" % x
        case str() as text:
            return "AS text=%r" % text
        case float(v) if v < 0:
            return "가드 v=%r" % v
        case other:
            return "캡처 other=%r" % other


subjects = [None, 1, Color.RED, "g", (7, 8, 9), {"op": "+", "z": 0},
            Pt(0, 5), Pt(4, 0), "hello", -2.5, 2.5]
for s in subjects:
    print("%-22r -> %s" % (s, kind(s)))

print("--- match 42 / case _ 뒤 ---")
match 42:
    case _:
        pass
print("'_' in globals() :", "_" in globals())
```

### 4. ★★ 시퀀스 패턴과 매핑 패턴에 여러 대상을 (예측)

```python
# e39_sequence.py
import collections.abc


class Bag:
    def __init__(self, *items):
        self.items = list(items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


class RegBag(Bag):
    pass


collections.abc.Sequence.register(RegBag)


def two(s):
    match s:
        case [a, b]:
            return "시퀀스 a=%r b=%r" % (a, b)
        case _:
            return "안 맞음"


subjects = [[1, 2], (1, 2), range(2), "ab", b"ab", bytearray(b"ab"),
            {1, 2}, iter([1, 2]), (x for x in [1, 2]), Bag(1, 2), RegBag(1, 2)]
for s in subjects:
    label = type(s).__name__
    print("%-10s abc.Sequence=%-5s -> %s"
          % (label, isinstance(s, collections.abc.Sequence), two(s)))
```

```python
# e39_mapping.py
from collections import defaultdict


def pick(m):
    match m:
        case {"id": i, **rest}:
            return "id=%r rest=%r" % (i, rest)
        case _:
            return "안 맞음"


print("① 남는 키")
print("   ", pick({"id": 1}))
print("   ", pick({"id": 1, "name": "a", "tags": []}))
print("   ", pick({"name": "a"}))

print("② defaultdict 에 없는 키를 물으면")
d = defaultdict(list, {"name": "a"})
print("   ", pick(d))
print("    match 뒤의 키 목록 :", sorted(d))
print("    d['id'] 로 직접 읽은 뒤 :", d["id"], sorted(d))

print("③ 키 개수로 끊고 싶으면")


def exactly_id(m):
    match m:
        case {"id": i, **rest} if not rest:
            return "id 하나뿐 i=%r" % i
        case _:
            return "안 맞음"


print("   ", exactly_id({"id": 1}), "/", exactly_id({"id": 1, "x": 0}))
```

### 5. ★ 클래스 패턴과 리터럴 `1`·`True` (예측)

```python
# e39_class.py
from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class DPt:
    x: int
    y: int


class NPt(NamedTuple):
    x: int
    y: int


class Plain:
    def __init__(self, x, y):
        self.x = x
        self.y = y


print("① __match_args__")
print("   DPt  :", DPt.__match_args__)
print("   NPt  :", NPt.__match_args__)
print("   Plain:", getattr(Plain, "__match_args__", "없음"))

print("② 위치 부분 패턴")
for obj in (DPt(1, 2), NPt(1, 2), Plain(1, 2)):
    try:
        match obj:
            case DPt(a, b) | NPt(a, b) | Plain(a, b):
                print("   %-5s a=%r b=%r" % (type(obj).__name__, a, b))
    except TypeError as exc:
        print("   %-5s %s: %s" % (type(obj).__name__, type(exc).__name__, exc))

print("③ 키워드 부분 패턴")
match Plain(1, 2):
    case Plain(x=1, y=b):
        print("   Plain(x=1, y=b) b=%r" % b)

print("④ 내장 타입 하나짜리 위치 패턴")
for v in (5, 5.0, True, "5"):
    match v:
        case int(n):
            print("   %-5r -> int(n) n=%r" % (v, n))
        case float(n):
            print("   %-5r -> float(n) n=%r" % (v, n))
        case _:
            print("   %-5r -> _" % (v,))

print("⑤ 리터럴 1 과 True")
for v in (1, 1.0, True):
    match v:
        case True:
            print("   %-5r -> case True" % (v,))
        case 1:
            print("   %-5r -> case 1" % (v,))

print("⑥ 순서를 바꿔 case 1 을 위에")
for v in (1, True):
    match v:
        case 1:
            print("   %-5r -> case 1" % (v,))
        case True:
            print("   %-5r -> case True" % (v,))

print("⑦ 값 패턴에 IntEnum 멤버")
from enum import IntEnum


class Level(IntEnum):
    LOW = 1


for v in (1, 1.0, Level.LOW):
    match v:
        case Level.LOW:
            print("   %-12r -> case Level.LOW" % (v,))
        case _:
            print("   %-12r -> _" % (v,))
```

### 6. ★★ 신호등 셋을 흘려 보내면 (예측)

```python
# e39_exhaust.py
import warnings
from enum import Enum


class Light(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3


def action(light):
    match light:
        case Light.RED:
            return "정지"
        case Light.GREEN:
            return "진행"


with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    for light in Light:
        print("%-12s -> %r" % (light.name, action(light)))
print("잡힌 경고 수 :", len(caught))
```

### 7. ★★★ `case RED:` 와 `case Palette.RED:` 를 가르는 것 (왜)

* 레퍼런스 문법에서 **캡처 패턴과 값 패턴을 가르는 표지**는 무엇인가? 대소문자는 관계가 있나?
* 그렇다면 **모듈 수준의 상수**를 값 패턴으로 쓰려면 코드를 어떻게 바꾸나?

### 8. ★★★ 캡처 함정을 컴파일러가 막는 자리와 못 막는 자리 (경계)

* 레퍼런스의 **어느 한 문장**이 막는 규칙의 전부인가?
* **못 막는 자리**는 어디이고, 거기서 막지 **않는 것이 옳은** 이유는?

### 9. ★★ Rust 18번과 같은 함정인가 (연결)

* [Rust 18번](../../../rust/syntax/18-match-and-exhaustiveness/2-summary.md)에서 경로를 빼먹은 이름은 **무엇이 되었고**, 컴파일러는 **무엇을 몇 개** 냈나?
* 파이썬과 Rust 에서 **함정은 같은데 안전망이 다른** 곳을 둘 대라.

### 10. 층 가르기 (경계)

* 「반박 불가 `case` 는 마지막에만」·「그 위반이 컴파일 단계에서 잡혀 캐럿이 없다」·「매핑 패턴이 `defaultdict` 의 기본값 공장을 안 부른다」 — 각각 **언어 보장인가 CPython 구현인가**?
* ★ 이 문서가 `SyntaxError` 를 **줄이지 않고 전문으로** 실은 이유는? 다른 형제 편들은 왜 트레이스백을 안 실었나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
