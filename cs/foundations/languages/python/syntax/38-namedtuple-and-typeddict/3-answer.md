# python/syntax/38-namedtuple-and-typeddict — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★★ **트레이스백이 한 블록도 없다.** `TypedDict` 의 `TypeError` 도 `typing.py` 를 지나 절대 경로가 박히므로 **타입과 메시지만** 찍었다.
> ★★★ **타입 검사기 쪽 답은 하나도 없다** — 이 머신에 다섯 도구가 전부 없다([2-summary.md](2-summary.md) 첫 블록 · [35번](../35-abc-and-protocol/2-summary.md)).

## 정답

### 1. `PtC` 만 메타클래스가 `_TypedDictMeta` 이고, 만든 것이 `dict` 다

**출력**

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

```text
===== python3 - <e38_identity.py =====
① 클래스 쪽 — 메타클래스와 __mro__
   PtA  type(C)=type            __mro__=['PtA', 'tuple', 'object']
   PtB  type(C)=type            __mro__=['PtB', 'tuple', 'object']
   PtC  type(C)=_TypedDictMeta  __mro__=['PtC', 'dict', 'object']
   PtD  type(C)=type            __mro__=['PtD', 'object']
② 인스턴스 쪽 — 만든 것의 type
   PtA  type(o).__name__=PtA   type(o) is C : True
   PtB  type(o).__name__=PtB   type(o) is C : True
   PtC  type(o).__name__=dict  type(o) is C : False
   PtD  type(o).__name__=PtD   type(o) is C : True
③ PtB 는 무엇을 물려받았나
   PtB.__bases__           : ['tuple']
   PtB._fields             : ('x', 'y')
   PtA 와 PtB 의 던더 차   : ['__annotations__', '__orig_bases__']
(exit 0)
```

**왜 그런가**

* ★★ **`PtB` 의 메타클래스가 `type`** 이고 `__mro__` 가 `['PtB', 'tuple', 'object']` — **`NamedTuple` 은 줄에 없다.**
  `NamedTuple` 은 **`namedtuple` 을 클래스 문법으로 만드는 장치**라 결과가 `PtA` 와 같은 모양이다.
* ★★★ **`PtC` 는 두 창이 어긋난다** — 클래스의 `__mro__` 에는 `dict` 가 있는데 **`PtC(x=1, y=2)` 는 `dict` 이고 `PtC` 가 아니다.**
* ★ **③** — `PtB` 가 `PtA` 에 더한 던더는 **`__annotations__`·`__orig_bases__` 둘뿐**이다.

### 2. `갈린 칸 12 / 30` — `NamedTuple` 0칸 · `TypedDict` 8칸 · `dataclass` 4칸

**출력**

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

```text
===== python3 - <e38_grid.py =====
probe             PtA              PtB              PtC              PtD
type(o) is C      True             True             False            True
isinstance tuple  True             True             False            False
isinstance dict   False            False            True             False
isinstance C      True             True             TypeError        True
o[0]              1                1                KeyError         TypeError
o["x"]            TypeError        TypeError        1                TypeError
o.x = 9           AttributeError   AttributeError   AttributeError   'ok'
o["x"] = 9        TypeError        TypeError        'ok'             TypeError
o == (1, 2)       True             True             False            False
C(x="a", y="b")   True             True             True             True
--- 기준: PtA 열(collections.namedtuple). 같은 행의 PtA 칸과 다른 칸을 센다 ---
   PtB : 0 칸
   PtC : 8 칸
   PtD : 4 칸
갈린 칸 12 / 30
(exit 0)
```

**왜 그런가**

* ★★★ **`NamedTuple` 은 0칸** — 런타임에서 `namedtuple` 과 **한 칸도 안 다르다.**
* ★★ **`TypedDict` 는 8칸** — 튜플의 성질이 전부 뒤집히고 `dict` 의 성질이 들어온다. ★ **`isinstance C` 가 `TypeError`** 다.
  `o[0]` 이 **`KeyError`** 인 것은 정수 `0` 을 **키**로 찾았기 때문이다.
* ★ **`dataclass` 는 4칸** — 튜플이 아니고, 인덱싱이 안 되고, **대입이 된다.**
* ★★★ **마지막 행은 네 칸 다 `True`** — `x: int` 에 문자열을 넣어도 **넷 모두 만들어진다.** **어느 구조체도 필드 타입을 확인하지 않는다.**
  ★ 그래서 이 행은 **한 칸도 안 갈렸고** — 「안 갈림」이 결론이다.

### 3. `dict` · `TypeError` 둘 · 셋 다 통과 · 키 목록은 들고 있다 · `__call__` 이 `dict`

**출력**

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

```text
===== python3 - <e38_typeddict.py =====
① 만든 것
   m               : {'title': 'Up', 'year': 2009}
   type(m) is dict : True
   m == dict(title='Up', year=2009) : True
② isinstance 로 물으면
    TypeError: TypedDict does not support instance and class checks
    TypeError: TypedDict does not support instance and class checks
③ 계약을 어긴 호출들
   Movie(**{}) -> {}
   Movie(**{'title': 1, 'year': 'x'}) -> {'title': 1, 'year': 'x'}
   Movie(**{'title': 'Up', 'year': 2009, 'extra': True}) -> {'title': 'Up', 'year': 2009, 'extra': True}
④ 클래스가 들고 있는 것
   __required_keys__ : ['title', 'year']
   __optional_keys__ : ['memo']
   __total__         : True
   is_typeddict      : True
⑤ 부르면 어디로 가나
   type(Movie).__name__         : _TypedDictMeta
   type(Movie).__call__ is dict : True
⑥ get_type_hints 로 읽으면
   기본               : {'title': <class 'str'>, 'year': <class 'int'>, 'memo': <class 'str'>}
   include_extras=True: {'title': <class 'str'>, 'year': <class 'int'>, 'memo': typing.NotRequired[str]}
(exit 0)
```

**왜 그런가**

* ★★ **①** — `type(m) is dict` 가 참. 같은 키의 `dict` 와 `==` 도 참.
* ★★★ **②** — `TypeError: TypedDict does not support instance and class checks`. `issubclass` 도 같은 문구다(6번 답).
* ★★★ **③** — 필수 키 없음 · 타입 틀림 · 없는 키, **셋 다 그대로 dict 가 만들어진다.**
  문서 — *"The Python runtime does not enforce function and variable type annotations."*
* ★ **④** — 필수 키 `title`·`year`, 선택 키 `memo`. **들고만 있다** — ③의 `{}` 가 그 증거다.
* ★ **⑤** — `type(Movie).__call__ is dict`. **부르면 `dict` 가 불린다**(CPython 구현, 9번 답).
* ★ **⑥** — `get_type_hints` 는 **`NotRequired` 를 벗겨** `memo` 를 `str` 로 준다. `include_extras=True` 면 남는다.

### 4. `Point == LatLon` 이 참이고 dict 키가 하나 · frozen dataclass 는 거짓이고 키가 둘

**출력**

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

```text
===== python3 - <e38_equality.py =====
① 모양이 같은 두 NamedTuple
   p == g              : True
   p == (37.5, 127.0)  : True
   hash(p) == hash(g)  : True
   len({p: 'P', g: 'G'}) : 1
   {p: 'P', g: 'G'}[p] : G
② 같은 모양의 두 frozen dataclass
   d == e              : False
   len({d: 'D', e: 'E'}) : 2
③ 튜플 연산들
   Point(1, 5) < Point(2, 0) : True
   sorted([Point(2, 0), LatLon(1, 9)]) : [LatLon(lat=1, lon=9), Point(x=2, y=0)]
   x, y = p            : 37.5 127.0
   list(p)             : [37.5, 127.0]
   p + (1,)            : (37.5, 127.0, 1)
   type(p + (1,))      : tuple
   p._replace(x=0)     : Point(x=0, y=127.0)
(exit 0)
```

**왜 그런가**

* ★★★ **①** — 튜플의 `==` 는 **원소만 순서대로** 본다. 클래스 이름도 필드 이름도 안 본다.
  **해시도 같아** dict 에서 **한 키**로 겹치고, 값은 **나중에 넣은 `'G'`** 가 남는다.
* ★★ **②** — dataclass 의 `__eq__` 는 **클래스가 같을 때만** 비교한다([36번](../36-dataclasses/2-summary.md)). 그래서 거짓이고 키가 둘이다.
* ★ **③** — 사전식 비교 · **다른 클래스끼리 섞여 정렬** · 언패킹 · `list()`.
  ★ **`p + (1,)` 은 `tuple`** 이다 — 튜플 연산은 이름표를 떨어뜨린다. **`_replace` 만 `Point` 를 준다.**

### 5. 필드 이름 오류 셋 + `rename` · 기본값·메서드 · ★ 가변 기본값을 공유한다

**출력**

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

```text
===== python3 - <e38_api.py =====
① namedtuple 의 필드 이름 규칙
   'x y'                       -> _fields=('x', 'y')
   'x, y'                      -> _fields=('x', 'y')
   'x class'                   -> ValueError: Type names and field names cannot be a keyword: 'class'
   'x class'  {'rename': True} -> _fields=('x', '_1')
   'x _y'                      -> ValueError: Field names cannot start with an underscore: '_y'
   'x x'                       -> ValueError: Encountered duplicate field name: 'x'
② NamedTuple 의 기본값과 메서드
   Money(100)             : Money(amount=100, currency='KRW')
   Money._field_defaults  : {'currency': 'KRW'}
   Money(100).double()    : Money(amount=200, currency='KRW')
   Money(100)._asdict()   : {'amount': 100, 'currency': 'KRW'}
③ 가변 기본값을 준 NamedTuple
   b.items                : ['사과']
   a.items is b.items     : True
④ 밑줄로 시작하는 필드
    ValueError: Field names cannot start with an underscore: '_secret'
(exit 0)
```

**왜 그런가**

* ★ **①** — 키워드·밑줄 시작·중복이 전부 **`ValueError`**. `rename=True` 면 `class` 가 **`_1`** 로 바뀐다.
* ★ **②** — `_field_defaults` 에는 **기본값이 있는 필드만** 있다. 메서드도 붙는다.
* ★★★ **③** — `items: list = []` 가 **그냥 통과**하고 두 인스턴스가 **같은 리스트**를 쓴다(`is` 가 참).
  [36번](../36-dataclasses/2-summary.md)의 dataclass 는 **같은 자리에서 `ValueError`** 였다(10번 답).
* ★ **④** — 밑줄 필드는 `NamedTuple` 에서도 **`ValueError`**. `_replace`·`_fields` 같은 **API 이름과의 충돌**을 막는다.

### 6. 객체에 흔적이 없다 — 가르려면 키와 값을 전부 봐야 하고 그것은 검사기의 몫이다

**왜 그런가**

* ★★★ **흔적이 없다** — `type(m) is dict` 가 참이다(3번 ①). `m` 은 **어느 클래스로 만들었는지 기억하지 않는다.**
  `Movie(...)` 는 **`dict(...)` 를 부른 것**과 같다(3번 ⑤).
* ★★ 그러므로 「이 dict 가 `Movie` 인가」는 **키가 다 있는지 · 남는 키가 없는지 · 값 타입이 맞는지**를 **전부 훑어야** 답이 나온다.
  ★ 런타임은 그 질문을 **받지 않기로** 했다 — **거짓을 주면 「아니다」라는 틀린 확신**을 주기 때문이다.
  설치본 `typing.py` 의 `__instancecheck__` 가 **무조건 `TypeError`** 를 던지는 몸통이다(구현).
* ★ **클래스 쪽 질문**은 된다 — `typing.is_typeddict(Movie)` 가 참(3번 ④).
* ★★ 값의 모양을 확인하는 일은 **타입 검사기**(정적으로) 또는 **직접 쓴 검증 코드**(실행 중에)의 몫이다.
  ★ 검사기가 그 일을 **어떻게** 하는지는 **이 머신에 도구가 없어 못 쟀다.**

### 7. 만든 것은 `dict` — 메타클래스의 `__call__` 이 `dict` 이기 때문 · `NamedTuple` 은 `__mro__` 에 없다

**왜 그런가**

* ★★ 클래스 쪽 창(`__mro__`)은 **클래스 객체가 무엇을 물려받았나**를 말한다 — `PtC` 는 `dict` 를 바탕으로 만들어졌다.
* ★★ 인스턴스 쪽 창(`type(o)`)은 **부를 때 무엇이 만들어지나**를 말한다 — **메타클래스의 `__call__`** 이 정한다.
  `_TypedDictMeta.__call__` 이 **`dict`** 라서 클래스를 부르면 **`PtC.__new__` 가 아니라 `dict` 가 돈다.**
* ★ 그래서 **두 창이 갈리는 것 자체가 기전의 증거**다. 한쪽만 봤으면 「`TypedDict` 는 `dict` 의 하위 클래스를 만든다」로 틀렸다.
* ★ `NamedTuple` 클래스의 `__mro__` 는 `['PtB', 'tuple', 'object']` — **`NamedTuple` 이 없다**(1번).

### 8. 필드 이름만 「쓴다」, 타입·필수 키는 「들고만 있다」 · 값 확인은 「못 잰 것」

**왜 그런가**

| 칸 | 누가 읽나 | 근거 |
|---|---|---|
| `NamedTuple` 의 **필드 이름** | ★ **런타임이 쓴다** — `_fields`·`__match_args__` 를 만든다([39번](../39-match-statement/2-summary.md)) | 1번 ③ · 2번 |
| `NamedTuple` 의 **필드 타입** | **들고만 있다** — `__annotations__` | 2번 마지막 행이 통과 |
| `TypedDict` 의 **필수 키 목록** | **들고만 있다** — `__required_keys__` | 3번 ③의 `{}` 가 통과 |
| 「값이 그 타입인가」 | ★ **검사기만** — **못 잰 것** | 이 머신에 검사기 없음 |

* ★★★ **「못 잰 것」으로 적은 이유** — 돌려 볼 도구가 **없어서**다. **안 돌려 본 것이 아니라 돌릴 수 없는 것**이다(제3의 상태).
  ★ 그 판정 자체가 틀리지 않게 **`shutil.which` 로 `PATH` 를 물은 블록**을 남겼다.
  「mypy 가 이것을 잡는다」를 적으면 **이 머신에서 한 번도 돌지 않은 결과**가 된다.

### 9. 앞은 계약 · 뒤는 구현 · `__orig_bases__` 에는 주소가 박힌다

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| `TypedDict` 인스턴스가 **평범한 `dict`** | **모듈 계약** | `typing` 문서 — 예가 `== dict(...)` 비교다 |
| `isinstance`·`issubclass` 에 못 쓴다 | **모듈 계약** | `typing` 문서 |
| `NamedTuple` 이 `namedtuple` 의 타입 붙은 판 | **모듈 계약** | `typing` 문서 |
| ★ `type(Movie).__call__ is dict` | **CPython 구현** | 실행 · `typing.py` 한 줄 |
| ★ 메타클래스 이름 `_TypedDictMeta` | **CPython 구현** | 밑줄 내부 이름 |
| 예외 **문구** | **이 판의 관찰** | 실행 |

* ★ **`__orig_bases__` 의 값은 `NamedTuple`·`TypedDict` 라는 함수 객체**라 `repr` 에 **주소가 박힌다.**
  주소는 머리말의 「흔들리는 칸」이므로 **이름만** 찍어 안 흔들리게 만들었다.

### 10. dataclass 는 막고 `NamedTuple` 은 안 막는다 · 「값만 같으면 다른 종류끼리도 같다」 · TS 는 사라지고 파이썬은 남는다

**왜 그런가**

* ★★ **가변 기본값** — dataclass 는 `class` 문에서 **`ValueError`**([36번](../36-dataclasses/2-summary.md)), `NamedTuple` 은 **통과하고 공유**한다(5번 ③).
  **같은 어노테이션 문법인데 한쪽만 막는다.**
* ★★ **공유하는 함정** — [37번](../37-enum/2-summary.md)의 **다른 두 `IntEnum`** 이 값만 같으면 `==` 가 참이었고,
  이 주제의 **다른 두 `NamedTuple`** 도 값만 같으면 참이다(4번 ①). 둘 다 **`int`·`tuple` 의 비교를 물려받아서**다.
* ★ **TS 와의 대비** — [TS 01번](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md)이 `interface` 가 **방출된 `.js` 에서 통째로 사라진다**고 실측했다.
  `TypedDict` 는 **클래스 객체로 남고 키 목록까지 들고 있다**(3번 ④). ★ **그래도 확인은 안 한다** — **사라지느냐 남느냐는 다른데, 안 본다는 결과는 같다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 판 + 검사기 유무 | `python3 - <e38_version.py` | 2(캡처 + 재대조) | 3.12.3 · **다섯 도구 전부 `None`** |
| 런타임 정체 | `python3 - <e38_identity.py` | 2 | `PtC` 만 `dict` · `NamedTuple` 은 `__mro__` 에 없음 |
| 런타임 정체 격자 | `python3 - <e38_grid.py` | 2 | **갈린 칸 12 / 30** · `NamedTuple` 0칸 |
| `TypedDict` 의 한계 | `python3 - <e38_typeddict.py` | 2 | `TypeError` 둘 · 위반 셋 통과 · `__call__ is dict` |
| 튜플의 `==` | `python3 - <e38_equality.py` | 2 | 다른 `NamedTuple` 끼리 참 · dict 키 하나 |
| `namedtuple` API | `python3 - <e38_api.py` | 2 | 이름 오류 셋 · 가변 기본값 공유 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★ `type(Movie).__call__ is dict` | `typing.py` 의 구현 한 줄이다 |
| 메타클래스 이름 `_TypedDictMeta` | 내부 이름이다 |
| `NamedTuple` 이 더하는 던더 목록 | 판마다 바뀔 수 있다 |
| 예외 **문구** 전부 | 종류는 계약, 문구는 아니다 |

★ **안 흔들리는 칸** — 격자의 참·거짓·예외 종류 · **「갈린 칸 12 / 30」** · `__mro__` 이름 목록 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **타입 검사기의 판정**(도구 없음 — 못 잰 것) · **속도·메모리**(부적용).
