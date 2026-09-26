# python/syntax/37-enum — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **격자의 칸을 하나씩** 채워야 한다. 마지막 줄의 숫자까지 적는다.
> ★★ 예외가 나는 칸은 **예외 종류까지** 적어야 맞은 것이다. 「안 될 것 같다」로는 틀린 것이다.
>
> 실행 환경: `python3` **3.12.3** · Linux(5번만 `python3.11` 3.11.15 도 함께). 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [29](../29-classes-and-attribute-lookup/1-question.md)(속성 탐색) · [30](../30-repr-eq-hash-contracts/1-question.md)(`__eq__`/`__hash__`) ·
> [31](../31-comparison-protocol-and-sortability/1-question.md)(정렬). 막히면 그중 무엇이 안 잡힌 것인지부터 짚어라.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 네 종류에 여섯 가지를 물으면 (예측)

```text
각 칸에 True / False / 결과 문자열 / 예외 종류 중 하나를 적는다. 마지막 줄의 N / M 도 적는다.
```

```python
# e37_grid.py
import json
from enum import Enum, Flag, IntEnum, StrEnum, auto


class E(Enum):
    RED = 1
    BLUE = 2


class I(IntEnum):
    RED = 1
    BLUE = 2


class S(StrEnum):
    RED = auto()
    BLUE = auto()


class F(Flag):
    RED = auto()
    BLUE = auto()


def cell(fn):
    try:
        return repr(fn())
    except Exception as exc:
        return type(exc).__name__


def names(members):
    return "[" + ",".join(m.name for m in members) + "]"


columns = [
    ("== 1", lambda C: C.RED == 1),
    ('== "red"', lambda C: C.RED == "red"),
    ("C(v) is m", lambda C: C(C.RED.value) is C.RED),
    ("sorted", lambda C: names(sorted([C.RED, C.BLUE]))),
    ("json.dumps", lambda C: json.dumps(C.RED)),
    ("hash==hash(v)", lambda C: hash(C.RED) == hash(C.RED.value)),
]

print("--- 각 클래스의 __mro__ 와 __eq__ 를 처음 가진 칸 ---")
for C in (E, I, S, F):
    owner = next(k.__name__ for k in C.__mro__ if "__eq__" in vars(k))
    print("   %s  %s  __eq__ <- %s" % (C.__name__, [k.__name__ for k in C.__mro__], owner))

print("클래스  RED.value  " + " | ".join(name for name, _ in columns))
rows = {}
for C in (E, I, S, F):
    rows[C.__name__] = [cell(lambda: fn(C)) for _, fn in columns]
    print("%-6s %-10r " % (C.__name__, C.RED.value) + " | ".join(rows[C.__name__]))

print("--- 기준: E 행(평범한 Enum). 같은 열의 E 칸과 다른 칸을 센다 ---")
split = 0
total = 0
for name in ("I", "S", "F"):
    diff = [columns[i][0] for i in range(len(columns)) if rows[name][i] != rows["E"][i]]
    split += len(diff)
    total += len(columns)
    print("   %s : %d 칸 %s" % (name, len(diff), diff))
print("갈린 칸 %d / %d" % (split, total))
```

### 2. ★★★ 세 종류를 `json` 에 넘기고 되읽으면 (예측)

```python
# e37_json.py
import json
from enum import Enum, IntEnum, StrEnum


class Color(Enum):
    RED = 1


class Level(IntEnum):
    LOW = 1


class Mode(StrEnum):
    FAST = "fast"


print("① 세 종류를 json.dumps 에 그대로 넘긴다")
for m in (Color.RED, Level.LOW, Mode.FAST):
    try:
        print("   %-16r -> %s" % (m, json.dumps(m)))
    except TypeError as exc:
        print("   %-16r -> %s: %s" % (m, type(exc).__name__, exc))

print("② dict 의 키와 값으로 넘긴다")
print("   ", json.dumps({Level.LOW: Mode.FAST}))
try:
    json.dumps({Color.RED: 1})
except TypeError as exc:
    print("    키가 Color.RED ->", type(exc).__name__ + ":", exc)

print("③ 되읽으면 무엇이 오나")
back = json.loads(json.dumps({"lv": Level.LOW}))
print("   back['lv']        :", repr(back["lv"]), type(back["lv"]).__name__)
print("   Level(back['lv']) :", repr(Level(back["lv"])))

print("④ 문자열로 만드는 세 길")
for m in (Color.RED, Level.LOW, Mode.FAST):
    print("   %-16r str=%-12r f=%-12r name=%r" % (m, str(m), f"{m}", m.name))

print("⑤ Enum 을 내보내는 명시적인 길")
print("   default=값   :", json.dumps({"c": Color.RED}, default=lambda o: o.value))
print("   default=이름 :", json.dumps({"c": Color.RED}, default=lambda o: o.name))
```

### 3. `auto()` 가 매기는 값 (예측)

```python
# e37_auto.py
from enum import Enum, Flag, IntEnum, StrEnum, auto


class A(Enum):
    X = auto()
    Y = auto()
    Z = auto()


class B(Enum):
    X = 10
    Y = auto()
    Z = auto()


class C(IntEnum):
    X = auto()
    Y = auto()


class D(StrEnum):
    RED = auto()
    DarkBlue = auto()


class G(Flag):
    R = auto()
    W = auto()
    X = auto()


for cls in (A, B, C, D, G):
    print("%-2s %s" % (cls.__name__, [(m.name, m.value) for m in cls]))

print("G.R | G.W        :", repr(G.R | G.W))
print("(G.R | G.W).value:", (G.R | G.W).value)
print("G.R in (G.R|G.W) :", G.R in (G.R | G.W))
```

### 4. ★★ 같은 값 두 멤버와 다시 묶기 시도 (예측)

```python
# e37_alias.py
from enum import Enum, EnumType, unique


class Shape(Enum):
    SQUARE = 2
    CIRCLE = 3
    BOX = 2


print("① 같은 값 두 멤버")
print("   Shape.BOX              :", repr(Shape.BOX))
print("   Shape.BOX is SQUARE    :", Shape.BOX is Shape.SQUARE)
print("   Shape(2)               :", repr(Shape(2)))
print("   list(Shape)            :", [m.name for m in Shape])
print("   __members__ 의 키      :", list(Shape.__members__))

print("② @unique 를 붙인다")
try:
    @unique
    class Shape2(Enum):
        SQUARE = 2
        CIRCLE = 3
        BOX = 2
except ValueError as exc:
    print("   ", type(exc).__name__ + ":", exc)

print("③ 멤버는 어디에 사나")
print("   type(Shape)                    :", type(Shape).__name__)
print("   Shape.__dict__['SQUARE'] is m  :", Shape.__dict__["SQUARE"] is Shape.SQUARE)
print("   '__getattr__' in vars(EnumType):", "__getattr__" in vars(EnumType))
hooks = ("__call__", "__getitem__", "__iter__", "__contains__", "__len__", "__setattr__", "__delattr__")
print("   EnumType 이 직접 가진 것       :", [h for h in hooks if h in vars(EnumType)])

print("④ 다시 묶기 시도")
try:
    Shape.SQUARE = 9
except AttributeError as exc:
    print("   Shape.SQUARE = 9       ->", type(exc).__name__ + ":", exc)
try:
    Shape.SQUARE.value = 9
except AttributeError as exc:
    print("   Shape.SQUARE.value = 9 ->", type(exc).__name__ + ":", exc)
try:
    Shape()
except TypeError as exc:
    print("   Shape()                ->", type(exc).__name__ + ":", exc)

print("⑤ 사본을 만든다")
import copy
import pickle
print("   copy.deepcopy(m) is m  :", copy.deepcopy(Shape.CIRCLE) is Shape.CIRCLE)
print("   pickle 왕복 is m       :", pickle.loads(pickle.dumps(Shape.CIRCLE)) is Shape.CIRCLE)

print("⑥ 값이 같은 다른 두 열거형")
from enum import IntEnum


class Fruit(Enum):
    APPLE = 2


class Size(IntEnum):
    SMALL = 2


class Rank(IntEnum):
    LOW = 2


print("   Shape.SQUARE == Fruit.APPLE :", Shape.SQUARE == Fruit.APPLE)
print("   Size.SMALL == Rank.LOW      :", Size.SMALL == Rank.LOW)
print("   hash(Shape.SQUARE) == hash('SQUARE') :", hash(Shape.SQUARE) == hash("SQUARE"))
```

### 5. ★ 같은 소스를 두 판에서 (예측)

아래 소스를 `python3`(3.12)와 `python3.11` 로 **각각** 던진다. 두 출력을 따로 적는다.

```python
# e37_boundary.py
import sys
import warnings
from enum import Enum, EnumType


class Color(Enum):
    RED = 1


print("판 :", sys.version_info[:2])
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    for text, probe in (("1 in Color", lambda: 1 in Color),
                        ("'x' in Color", lambda: "x" in Color),
                        ("Color.RED in Color", lambda: Color.RED in Color)):
        try:
            print("   %-20s -> %r" % (text, probe()))
        except TypeError as exc:
            print("   %-20s -> %s: %s" % (text, type(exc).__name__, exc))
print("잡힌 경고 수 :", len(caught))
for w in caught:
    print("   ", w.category.__name__ + ":", str(w.message).replace("\n", " "))
print("'__getattr__' in vars(EnumType) :", "__getattr__" in vars(EnumType))
```

### 6. ★★ 평범한 `Enum` 은 `== 1` 이 거짓인데 `IntEnum` 은 참이다 (왜)

* `__mro__` 의 **어느 칸 하나**가 이 차이를 만드는가?
* 그렇다면 `Flag` 이 **`== 1` 에서 어느 쪽으로 답할지** 무엇을 보고 알 수 있는가?

### 7. ★★ `Color.RED` 라는 점 접근은 누가 처리하나 (경계)

* 3.12 에서 `Color.RED` 를 찾을 때 **`EnumType` 의 갈고리가 불리는가**, 아니면 평범한 클래스 속성 탐색인가 — **무엇으로 확인하나**?
* 그러면 메타클래스가 **직접 가로채는 연산**은 무엇무엇인가?

### 8. ★ `StrEnum` 의 정렬 (왜)

* `sorted()` 가 `StrEnum` 멤버를 **정의 순서로 세우지 않는 이유**는?
* 정의 순서가 필요하면 무엇을 쓰고, 그 순서는 **누가 보장**하나?

### 9. 층 가르기 (경계)

* 「멤버는 싱글턴이다」·「`hash(멤버) == hash(이름)`」·「멤버가 클래스 `__dict__` 에 산다」 — 셋은 각각 **모듈 계약인가 CPython 구현인가**?
* ★ 이 문서가 `hash()` 의 **숫자**를 한 번도 안 찍은 이유는?
* ★ 「3.10 에는 `StrEnum` 이 없다」를 이 문서는 **어떤 상태로** 적었나 — 확인한 것인가?

### 10. 이웃 주제와의 경계 (연결)

* [30번](../30-repr-eq-hash-contracts/2-summary.md)의 `__eq__` 계약이 **다른 두 `IntEnum`** 의 비교에 어떻게 걸리는가?
* ★ [자바 13번](../../../java/syntax/13-enum-classes/2-summary.md)의 `ordinal()` 경고와 이 주제의 **`auto()` 값을 저장하지 말라**는 경고는 어떻게 같은가?
* ★ [39번](../39-match-statement/2-summary.md)에서 `case Color.RED:` 와 `case RED:` 는 어떻게 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
