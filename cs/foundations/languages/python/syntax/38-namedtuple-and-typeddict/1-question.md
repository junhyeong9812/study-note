# python/syntax/38-namedtuple-and-typeddict — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 2번은 **격자의 칸을 하나씩** 채워야 한다. 마지막 줄의 숫자까지 적는다.
> ★★ 예외가 나는 칸은 **예외 종류까지** 적어야 맞은 것이다.
> ★★ 이 주제는 **「타입 검사기라면 무엇을 잡을까」를 묻지 않는다** — 이 머신에 검사기가 없어 정답을 확인할 수 없다.
> 묻는 것은 전부 **파이썬이 실행 중에 무엇을 하나**다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [11](../11-tuple-and-unpacking/1-question.md)(튜플) · [12](../12-dict-and-key-requirements/1-question.md)(`dict`) ·
> [36](../36-dataclasses/1-question.md)(dataclass). 막히면 그중 무엇이 안 잡힌 것인지부터 짚어라.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 네 클래스와 네 인스턴스의 정체 (예측)

```python
# e38_identity.py
from collections import namedtuple
from dataclasses import dataclass
from typing import NamedTuple, TypedDict

PtA = namedtuple("PtA", "x y")


class PtB(NamedTuple):
    x: int
    y: int


class PtC(TypedDict):
    x: int
    y: int


@dataclass
class PtD:
    x: int
    y: int


def mro(cls):
    return [k.__name__ for k in cls.__mro__]


print("① 클래스 쪽 — 메타클래스와 __mro__")
for C in (PtA, PtB, PtC, PtD):
    print("   %-4s type(C)=%-15s __mro__=%s" % (C.__name__, type(C).__name__, mro(C)))

print("② 인스턴스 쪽 — 만든 것의 type")
for C in (PtA, PtB, PtC, PtD):
    o = C(x=1, y=2)
    print("   %-4s type(o).__name__=%-5s type(o) is C : %s" % (C.__name__, type(o).__name__, type(o) is C))

print("③ PtB 는 무엇을 물려받았나")
print("   PtB.__bases__           :", [b.__name__ for b in PtB.__bases__])
print("   PtB._fields             :", PtB._fields)
print("   PtA 와 PtB 의 던더 차   :", sorted(set(vars(PtB)) - set(vars(PtA))))
```

### 2. ★★★ 네 구조체에 열 가지를 물으면 (예측)

```text
각 칸에 True / False / 값 / 'ok' / 예외 종류 중 하나를 적는다. 마지막 줄의 N / M 도 적는다.
```

```python
# e38_grid.py
from collections import namedtuple
from dataclasses import dataclass
from typing import NamedTuple, TypedDict

PtA = namedtuple("PtA", "x y")


class PtB(NamedTuple):
    x: int
    y: int


class PtC(TypedDict):
    x: int
    y: int


@dataclass
class PtD:
    x: int
    y: int


def make(cls, x, y):
    return cls(x=x, y=y)


def cell(fn):
    try:
        return repr(fn())
    except Exception as exc:
        return type(exc).__name__


def set_attr(o):
    o.x = 9
    return "ok"


def set_item(o):
    o["x"] = 9
    return "ok"


columns = [
    ("type(o) is C", lambda C, o: type(o) is C),
    ("isinstance tuple", lambda C, o: isinstance(o, tuple)),
    ("isinstance dict", lambda C, o: isinstance(o, dict)),
    ("isinstance C", lambda C, o: isinstance(o, C)),
    ("o[0]", lambda C, o: o[0]),
    ('o["x"]', lambda C, o: o["x"]),
    ("o.x = 9", lambda C, o: set_attr(o)),
    ('o["x"] = 9', lambda C, o: set_item(o)),
    ("o == (1, 2)", lambda C, o: o == (1, 2)),
    ('C(x="a", y="b")', lambda C, o: make(C, "a", "b") is not None),
]

rows = {}
for C in (PtA, PtB, PtC, PtD):
    rows[C.__name__] = [cell(lambda: fn(C, make(C, 1, 2))) for _, fn in columns]

print(("%-18s" % "probe" + " ".join("%-16s" % n for n in rows)).rstrip())
for i, (label, _) in enumerate(columns):
    print(("%-18s" % label + " ".join("%-16s" % rows[n][i] for n in rows)).rstrip())

print("--- 기준: PtA 열(collections.namedtuple). 같은 행의 PtA 칸과 다른 칸을 센다 ---")
split = 0
total = 0
for name in ("PtB", "PtC", "PtD"):
    diff = [columns[i][0] for i in range(len(columns)) if rows[name][i] != rows["PtA"][i]]
    split += len(diff)
    total += len(columns)
    print("   %s : %d 칸" % (name, len(diff)))
print("갈린 칸 %d / %d" % (split, total))
```

### 3. ★★★ `Movie` 로 만들고, 묻고, 어기면 (예측)

```python
# e38_typeddict.py
import typing
from typing import NotRequired, TypedDict


class Movie(TypedDict):
    title: str
    year: int
    memo: NotRequired[str]


print("① 만든 것")
m = Movie(title="Up", year=2009)
print("   m               :", m)
print("   type(m) is dict :", type(m) is dict)
print("   m == dict(title='Up', year=2009) :", m == dict(title="Up", year=2009))

print("② isinstance 로 물으면")
try:
    isinstance(m, Movie)
except TypeError as exc:
    print("   ", type(exc).__name__ + ":", exc)
try:
    issubclass(dict, Movie)
except TypeError as exc:
    print("   ", type(exc).__name__ + ":", exc)

print("③ 계약을 어긴 호출들")
for kwargs in ({}, {"title": 1, "year": "x"}, {"title": "Up", "year": 2009, "extra": True}):
    print("   Movie(**%r) -> %r" % (kwargs, Movie(**kwargs)))

print("④ 클래스가 들고 있는 것")
print("   __required_keys__ :", sorted(Movie.__required_keys__))
print("   __optional_keys__ :", sorted(Movie.__optional_keys__))
print("   __total__         :", Movie.__total__)
print("   is_typeddict      :", typing.is_typeddict(Movie))

print("⑤ 부르면 어디로 가나")
print("   type(Movie).__name__         :", type(Movie).__name__)
print("   type(Movie).__call__ is dict :", type(Movie).__call__ is dict)

print("⑥ get_type_hints 로 읽으면")
print("   기본               :", typing.get_type_hints(Movie))
print("   include_extras=True:", typing.get_type_hints(Movie, include_extras=True))
```

### 4. ★★ 모양이 같은 두 쌍 (예측)

```python
# e38_equality.py
from dataclasses import dataclass
from typing import NamedTuple


class Point(NamedTuple):
    x: float
    y: float


class LatLon(NamedTuple):
    lat: float
    lon: float


@dataclass(frozen=True)
class DPoint:
    x: float
    y: float


@dataclass(frozen=True)
class DLatLon:
    lat: float
    lon: float


p = Point(37.5, 127.0)
g = LatLon(37.5, 127.0)
print("① 모양이 같은 두 NamedTuple")
print("   p == g              :", p == g)
print("   p == (37.5, 127.0)  :", p == (37.5, 127.0))
print("   hash(p) == hash(g)  :", hash(p) == hash(g))
print("   len({p: 'P', g: 'G'}) :", len({p: "P", g: "G"}))
print("   {p: 'P', g: 'G'}[p] :", {p: "P", g: "G"}[p])

print("② 같은 모양의 두 frozen dataclass")
d = DPoint(37.5, 127.0)
e = DLatLon(37.5, 127.0)
print("   d == e              :", d == e)
print("   len({d: 'D', e: 'E'}) :", len({d: "D", e: "E"}))

print("③ 튜플 연산들")
print("   Point(1, 5) < Point(2, 0) :", Point(1, 5) < Point(2, 0))
print("   sorted([Point(2, 0), LatLon(1, 9)]) :", sorted([Point(2, 0), LatLon(1, 9)]))
x, y = p
print("   x, y = p            :", x, y)
print("   list(p)             :", list(p))
print("   p + (1,)            :", p + (1,))
print("   type(p + (1,))      :", type(p + (1,)).__name__)
print("   p._replace(x=0)     :", p._replace(x=0))
```

### 5. 필드 이름과 기본값 (예측)

```python
# e38_api.py
from collections import namedtuple
from typing import NamedTuple

print("① namedtuple 의 필드 이름 규칙")
for spec, kw in (("x y", {}), ("x, y", {}), ("x class", {}), ("x class", {"rename": True}),
                 ("x _y", {}), ("x x", {})):
    try:
        T = namedtuple("T", spec, **kw)
        print("   %-10r %-16s -> _fields=%r" % (spec, kw or "", T._fields))
    except ValueError as exc:
        print("   %-10r %-16s -> %s: %s" % (spec, kw or "", type(exc).__name__, exc))

print("② NamedTuple 의 기본값과 메서드")


class Money(NamedTuple):
    amount: int
    currency: str = "KRW"

    def double(self):
        return self._replace(amount=self.amount * 2)


print("   Money(100)             :", Money(100))
print("   Money._field_defaults  :", Money._field_defaults)
print("   Money(100).double()    :", Money(100).double())
print("   Money(100)._asdict()   :", Money(100)._asdict())

print("③ 가변 기본값을 준 NamedTuple")


class Cart(NamedTuple):
    items: list = []


a = Cart()
b = Cart()
a.items.append("사과")
print("   b.items                :", b.items)
print("   a.items is b.items     :", a.items is b.items)

print("④ 밑줄로 시작하는 필드")
try:
    class Bad(NamedTuple):
        _secret: int
except Exception as exc:
    print("   ", type(exc).__name__ + ":", exc)
```

### 6. ★★★ `isinstance(m, Movie)` 가 거짓을 주지 않고 예외를 내는 이유 (왜)

* 런타임에 `m` 이라는 객체에는 **`Movie` 와 연결된 흔적이 있나**? 무엇으로 확인하나?
* 그렇다면 「이 dict 가 `Movie` 인가」를 가르려면 **무엇을 봐야** 하고, 그 일은 누구의 몫인가?

### 7. ★★ 클래스 쪽 창과 인스턴스 쪽 창 (경계)

* `TypedDict` 클래스의 `__mro__` 에 `dict` 가 있다. 그런데 **만든 것의 `type`** 은 무엇인가 — 두 창이 왜 다른 답을 주나?
* `NamedTuple` 클래스의 `__mro__` 에 **`NamedTuple` 이 있나**?

### 8. ★★ 어노테이션을 누가 읽나 (경계)

* `NamedTuple` 의 **필드 이름**, **필드 타입**, `TypedDict` 의 **필수 키 목록** — 셋을 「런타임이 쓴다 / 들고만 있다」로 가르면?
* ★ 「값이 그 타입인가」를 확인하는 칸을 이 문서는 **어떤 상태로** 적었나 — 왜 그렇게 적었나?

### 9. 층 가르기 (경계)

* 「`TypedDict` 인스턴스는 평범한 `dict` 다」와 「`type(Movie).__call__ is dict`」는 각각 **모듈 계약인가 CPython 구현인가**?
* ★ `__orig_bases__` 를 이 문서가 **이름만** 찍은 이유는?

### 10. 이웃 주제와의 경계 (연결)

* ★ [36번](../36-dataclasses/2-summary.md)의 dataclass 와 이 주제의 `NamedTuple` 은 **가변 기본값**에서 어떻게 다르게 구나?
* ★ [37번](../37-enum/2-summary.md)의 `IntEnum` 과 이 주제의 `NamedTuple` 은 **어떤 함정을 공유**하나?
* ★ [TS 01번](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md)의 `interface` 와 `TypedDict` 는 「런타임에 남는가」에서 어떻게 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
