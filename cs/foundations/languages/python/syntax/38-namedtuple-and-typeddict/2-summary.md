# python/syntax/38-namedtuple-and-typeddict — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [`typing`(3.12)](https://docs.python.org/3.12/library/typing.html) — 첫머리의 *"The Python runtime does not enforce function and variable type annotations."* ·
>   `NamedTuple` 이 *"Typed version of `collections.namedtuple()`"* 라는 문단 · `TypedDict` 가 런타임에 평범한 `dict` 이고
>   `isinstance()`·`issubclass()` 에 못 쓴다는 문단
> - [`collections.namedtuple`](https://docs.python.org/3.12/library/collections.html#collections.namedtuple) — 필드 이름 규칙 · `rename` · `_replace`·`_asdict`·`_fields`·`_field_defaults`
> - CPython 3.12 의 `typing.py`(설치본 `/usr/lib/python3.12/typing.py`) — `_TypedDictMeta` 의 `__call__ = dict` 한 줄과
>   `__instancecheck__` 가 무조건 `TypeError` 를 던지는 몸통. ★ **이것은 구현이지 계약이 아니다**(구현 세부사항 절).
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태는 `python3 - <파일` 하나로 고정했다.\
> ★★★ **트레이스백을 한 블록도 싣지 않았다.** `isinstance(x, Movie)` 의 `TypeError` 도 **`typing.py` 를 지나 절대 경로가 박히므로**
> `except` 로 받아 **예외 타입과 메시지만** 찍었다.\
> ★★★ **타입 검사기가 이 머신에 없다** — [35번](../35-abc-and-protocol/2-summary.md)이 `shutil.which` 로 다섯 도구를 물어 **전부 `None`** 을 받았고,
> 이 문서도 **첫 블록에서 다시 물었다**(같은 답). 그래서 이 문서의 어떤 문장도 「검사기가 이렇게 잡아 준다」로 적지 않는다.\
> **버전** — `collections.namedtuple` 은 **2.6**, 클래스 문법 `typing.NamedTuple` 은 **3.6**, `TypedDict` 는 **3.8**(PEP 589),
> `NotRequired`/`Required` 는 **3.11**(PEP 655) 부터다.\
> ★ **구현 대 언어 보장 한 줄** — **`NamedTuple` 이 튜플이고 `TypedDict` 인스턴스가 평범한 `dict` 라는 것까지가 문서의 계약**이고,
> **`_TypedDictMeta` 라는 이름과 그 `__call__` 이 `dict` 라는 것**은 CPython 쪽이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★ `__orig_bases__` 의 `repr` — 함수 객체라 **주소가 박힌다**. 그래서 **이름만 찍었다**(동작 1 의 ③) | ★★ 격자의 **참·거짓과 예외 종류** · 마지막 줄 **「갈린 칸 N / M」** |
> | ★ `frozenset` 의 `repr` 순서 — `__required_keys__` 는 **`sorted()` 로 찍었다** | `__mro__` 의 **이름 목록** · `_fields` 의 순서 |
> | 판이 오르면 예외 **문구**와 **메타클래스 이름** | `==`·`hash` 비교의 **참·거짓**(해시 숫자는 안 찍었다) |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대 경로도 한 곳도 안 찍힌다.** 재대조 전부 동일.\
> **선행** — [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md)(★★ **튜플의 `==`·언패킹·불변**) ·
> [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)(★★ **`dict` 와 키 요건**) ·
> [36-dataclasses](../36-dataclasses/2-summary.md)(★★ **격자의 넷째 열 — 보통 클래스 쪽 대비**) ·
> [35-abc-and-protocol](../35-abc-and-protocol/2-summary.md)(★ **런타임이 안 막는 것 · 검사기 부재 판정**).

## 한눈에 — 쉽게 말하면

**넷은 「라벨을 붙인 상자」인데 상자의 재질이 다르다.**

* `namedtuple`·`NamedTuple` — **튜플 상자에 칸 이름표를 붙인 것.** 상자는 여전히 튜플이다.
* `TypedDict` — **상자가 아니라 상자에 붙이는 설명서.** 만들면 **그냥 `dict`** 가 나온다.
* `dataclass` — **새 재질의 상자.** 튜플도 `dict` 도 아니다([36번](../36-dataclasses/2-summary.md)).

```text
   class PtB(NamedTuple):          class PtC(TypedDict):            @dataclass class PtD:
       x: int                          x: int                           x: int
       y: int                          y: int                           y: int
          |                               |                                |
          v                               v                                v
   PtB(x=1, y=2)                   PtC(x=1, y=2)                    PtD(x=1, y=2)
   -> PtB 인스턴스                  -> ★ dict 인스턴스                -> PtD 인스턴스
      (tuple 의 하위)                  type(o) is PtC 가 거짓            (object 의 하위)

   o[0] 된다 · == (1,2) 참          o["x"] 된다 · isinstance 예외     o.x 된다 · 대입 된다

   ★ 셋 다 x: int 라고 적었지만 런타임은 그 int 를 한 번도 확인하지 않는다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 칸에 이름표가 붙은 튜플 상자 | `namedtuple`·`NamedTuple` 인스턴스 | `isinstance(o, tuple)` 가 참 |
| ★ 상자에 붙이는 설명서 | `TypedDict` 클래스 | `type(PtC(x=1, y=2)) is dict` |
| 설명서를 보고 상자를 검사해 주는 사람 | 타입 검사기 | ★ **이 머신에 없다**(못 잰 것) |
| 설명서에 적힌 칸 목록 | `__annotations__`·`__required_keys__` | 런타임이 **들고만 있다** |
| 새 재질의 상자 | `dataclass` 인스턴스 | `isinstance(o, tuple)`·`dict` 둘 다 거짓 |
| 상자 모양만 보고 같다고 하는 것 | 튜플의 `==` | 다른 두 `NamedTuple` 이 같다고 답한다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**API 응답을 `TypedDict` 로 선언했으니 키가 빠지면 에러가 날 것이다**」와
「**`Point` 와 `LatLon` 을 dict 키로 같이 썼더니 하나가 사라졌다**」가 그것이다.\
앞엣것은 **설명서를 검사관으로 착각한 것**이고, 뒤엣것은 **튜플 상자가 이름표를 안 보고 내용만 비교하는 것**이다.

> **런타임 정체** — 그 객체가 **실행 중에 실제로 무엇인가.** `type()`·`isinstance`·`__mro__` 로 묻는다.\
> 예: `TypedDict` 로 만든 것의 런타임 정체는 **`dict`** 다.

> **타입 검사기(type checker)** — 코드를 **실행하지 않고** 어노테이션을 읽어 모순을 찾는 별도 도구(mypy·pyright 등).\
> 예: `Movie(title=1)` 을 잡아 주는 것은 파이썬이 아니라 **이 도구**다 — 그리고 이 머신에는 없다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 「런타임 정체」 격자 창이다.** 「`TypedDict` 는 그냥 `dict` 다」를 산문으로 적지 않고,
**네 구조체 × 열 탐침**을 한 블록에서 돌려 **`collections.namedtuple` 과 다른 칸을 스크립트가 센다.**

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **런타임 정체 격자** | `isinstance`·인덱싱·대입·`==` 가 **어떻게 답하나** | 타입 검사기가 뭐라 할지 |
| ② ★★ **`type(C)` · `__mro__` · `type(o)`** | 클래스가 **무엇을 물려받았고** 만든 것이 **무엇인가** | — |
| ③ ★ **`==` / `hash` / dict 키** | 다른 두 구조체가 **같다고 답하나** | — |
| ④ ★ **클래스가 들고 있는 메타데이터**(`__annotations__`·`__required_keys__`·`_fields`) | 런타임이 **무엇을 기억하나** | 그것을 **쓰나 안 쓰나** |
| ★ **못 잰 것** — 타입 검사기 출력 | — | ★★★ **이 머신에 다섯 도구가 전부 없다**(첫 블록 · [35번](../35-abc-and-protocol/2-summary.md)과 같은 답) |
| ★ **부적용인 창** — 속도·메모리 | — | 이 문서는 **한 번도 안 쟀다**. 「튜플이 가볍다」를 적지 않았다 |

★★ **②가 이 주제의 네 번째 창이고 두 칸이 갈린다.**
`TypedDict` 클래스의 `__mro__` 는 **`['PtC', 'dict', 'object']`** 라 「`PtC` 는 `dict` 의 하위 클래스」처럼 보이는데,
**만든 것의 `type` 은 `PtC` 가 아니라 `dict`** 다(동작 1 의 ①·②). **클래스 쪽 창과 인스턴스 쪽 창이 다른 답을 준다.**

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「`TypedDict` 가 키 누락·잘못된 타입을 잡나」를 **타입 검사기로 물을 수 없으니**, **계약을 일부러 어긴 호출을 그냥 돌리는 창**으로 바꿔 물었다(동작 2 의 ③).
답은 「**세 번 다 통과한다**」이고, ★ **그 통과가 곧 「런타임은 안 본다」의 증거**다.
★ 바꾼 창이 못 보는 것 — **검사기가 그 셋 중 무엇을 잡을지는 이 문서가 모른다.** 「잡을 것이다」로 적지 않았다.

먼저 판을 박아 둔다. 이 문서의 모든 출력은 아래 판에서 나왔고, **검사기 유무도 여기서 다시 물었다.**

```python
# e38_version.py
import shutil
import sys
import typing

print("version_info   =", sys.version_info)
print("implementation =", sys.implementation.name)
print("typing.NamedTuple · TypedDict · NotRequired 가 있나 :",
      [hasattr(typing, n) for n in ("NamedTuple", "TypedDict", "NotRequired")])
print("이 머신에 타입 검사기가 있나 — PATH 를 직접 물어본다")
for tool in ("mypy", "pyright", "pyre", "pytype", "basedpyright"):
    print("   %-13s :" % tool, shutil.which(tool))
```

```text
===== python3 - <e38_version.py =====
version_info   = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
typing.NamedTuple · TypedDict · NotRequired 가 있나 : [True, True, True]
이 머신에 타입 검사기가 있나 — PATH 를 직접 물어본다
   mypy          : None
   pyright       : None
   pyre          : None
   pytype        : None
   basedpyright  : None
(exit 0)
```

★★★ **다섯이 전부 `None`** 이다 — [35번](../35-abc-and-protocol/2-summary.md)의 판정과 같다.
규칙대로 **「없다」고 적기 전에 `PATH` 를 직접 물은 블록**을 남겼다(`shutil.which` 는 `PATH` 를 실제로 훑는다).

## 이 주제가 답하려는 질문

1. ★★★ **넷의 런타임 정체는 무엇인가** — 튜플인가 `dict` 인가 새 클래스인가. `isinstance`·인덱싱·대입·`==` 가 어떻게 답하나.
2. ★★ **`TypedDict` 는 런타임에 무엇을 하나** — 그리고 **무엇을 안 하나**(키 누락·잘못된 타입·남는 키·`isinstance`).
3. **`NamedTuple` 이 튜플이라서 생기는 일** — 모양이 같은 다른 구조체와의 `==`·해시·정렬.

★ 첫째가 이 주제의 인출 목표다.
**「어노테이션을 적었다」와 「런타임이 확인한다」를 격자의 마지막 행 하나로 가를 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 런타임 정체 — `type(C)` · `__mro__` · `type(o)`

**언제 쓰나** — 이 주제의 출발점. 「이것은 실행 중에 무엇인가」를 **외우지 않고 보는 법**.

```text
   클래스 쪽 (무엇을 물려받았나)              인스턴스 쪽 (만든 것이 무엇인가)

   PtA  type=type            [PtA, tuple, object]      PtA(x=1,y=2)  -> PtA
   PtB  type=type            [PtB, tuple, object]      PtB(x=1,y=2)  -> PtB
   PtC  type=_TypedDictMeta  [PtC, dict, object]       PtC(x=1,y=2)  -> ★ dict
   PtD  type=type            [PtD, object]             PtD(x=1,y=2)  -> PtD

   ★ PtC 만 두 창이 어긋난다 — 클래스는 dict 의 하위처럼 보이는데 만든 것은 PtC 가 아니다
```

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

그림 해설.

* ★★ **①에서 `PtB` 의 메타클래스가 그냥 `type`** 이다. `class PtB(NamedTuple)` 이라고 썼지만
  **`NamedTuple` 을 물려받은 클래스가 아니다** — `__mro__` 에 `NamedTuple` 이 없고 **`tuple` 만** 있다.
  ★ 문서 문장 — `NamedTuple` 은 *"Typed version of `collections.namedtuple()`"*. **클래스 문법으로 `namedtuple` 을 만드는 장치**다.
* ★★★ **①·②에서 `PtC` 가 어긋난다.** 메타클래스가 `_TypedDictMeta` 이고 `__mro__` 에 `dict` 가 있는데,
  **`PtC(x=1, y=2)` 로 만든 것은 `type(o) is PtC` 가 거짓**이고 `type(o).__name__` 이 **`dict`** 다.
  ★ 문서 문장 — `TypedDict` 는 런타임에 **평범한 `dict`** 다(동작 2 의 ⑤가 그 기전).
* ★ **③ — `PtB` 와 `PtA` 의 차이는 던더 둘뿐**이다: `__annotations__`·`__orig_bases__`.
  **런타임에 `NamedTuple` 이 `namedtuple` 에 더한 것은 「어노테이션을 기억한다」는 것 하나**다.
  ★ `__orig_bases__` 의 **값**은 함수 객체라 `repr` 에 **주소가 박힌다** — 그래서 **이름만** 찍었다.

**비용** — `NamedTuple` 은 `namedtuple` 에 **런타임 비용을 더하지 않는다**(같은 클래스가 나온다).
대가는 **어노테이션을 적어도 튜플의 성질을 그대로 진다는 것**이다(동작 3).

### 2. ★★★ 격자 — 네 구조체 × 열 탐침

**언제 쓰나** — 「튜플로 쓸 건가 `dict` 로 쓸 건가 객체로 쓸 건가」를 고를 때. **무엇이 되고 무엇이 막히나를 한눈에.**

```text
                     namedtuple   NamedTuple   TypedDict    dataclass
   isinstance tuple      ●            ●            -            -
   isinstance dict       -            -            ●            -
   isinstance C          ●            ●          예외           ●
   o[0]                  ●            ●          KeyError     TypeError
   o["x"]              TypeError    TypeError       ●         TypeError
   o.x = 9             막힘          막힘          막힘           ●
   o["x"] = 9          TypeError    TypeError       ●         TypeError
   C(x="a", y="b")       ●            ●            ●            ●      ★ 네 칸 다 통과

   ● = 된다 / 참
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

그림 해설.

* ★★★ **마지막 줄 — `갈린 칸 12 / 30`.** 기준은 **`collections.namedtuple` 열(PtA)** 이고 같은 행의 PtA 칸과 다른 칸을 **스크립트가 셌다.**
* ★★★ **PtB(`NamedTuple`)는 0칸** 이다. **런타임에서 `namedtuple` 과 한 칸도 안 다르다** — 동작 1 이 말한 「같은 것」의 실행 증거다.
* ★★ **PtC(`TypedDict`)는 8칸** — 튜플 쪽 성질이 전부 뒤집히고 `dict` 의 성질이 들어온다.
  ★ **`isinstance C` 칸이 `TypeError`** 다 — **거짓이 아니라 예외**다(동작 3 의 ②).
  ★ `o[0]` 이 **`KeyError`** 인 것도 `dict` 라서다 — 정수 `0` 을 **키**로 찾았다.
* ★ **PtD(`dataclass`)는 4칸** — `isinstance tuple` 이 거짓 · `o[0]` 이 `TypeError` · **`o.x = 9` 가 된다** · `== (1, 2)` 가 거짓.
* ★★★ **마지막 행 `C(x="a", y="b")` 는 네 열이 전부 `True`** 다. **`x: int` 라고 적은 칸에 문자열이 네 구조체 모두에 들어갔다.**
  **네 구조체 중 어느 것도 필드 타입을 확인하지 않는다.** 그래서 이 행은 **한 칸도 안 갈렸다** — 「안 갈림」이 결론이다.
  ★ [36번](../36-dataclasses/2-summary.md)이 dataclass 에 대해 먼저 적은 「**읽기는 하는데 값은 안 본다**」가 넷 전부의 사실이다.

**비용** — 튜플 쪽은 **인덱싱·언패킹·불변을 공짜로** 얻는 대신 **튜플의 비교 규칙**을 진다(동작 4).
`TypedDict` 는 **JSON 과 바로 오가는** 대신 **런타임 보호가 0** 이다.

### 3. ★★★ `TypedDict` 는 그냥 `dict` 다 — 무엇을 안 하나

**언제 쓰나** — JSON·API 응답의 **모양을 적어 둘 때.** 그리고 「왜 키가 빠졌는데 에러가 안 나지」가 막힐 때.

```text
   Movie(title="Up", year=2009)
        |
        v   type(Movie).__call__ 이 dict 다  (★ CPython 3.12 의 typing.py 한 줄: __call__ = dict)
   dict(title="Up", year=2009)        -> {'title': 'Up', 'year': 2009}

   Movie()                            -> {}                       ★ 필수 키가 없다
   Movie(title=1, year="x")           -> {'title': 1, ...}        ★ 타입이 틀렸다
   Movie(title=..., extra=True)       -> {..., 'extra': True}     ★ 없는 키다
   isinstance(m, Movie)               -> TypeError                 ★ 물어볼 수조차 없다
```

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

그림 해설.

* ★★ **①** — `type(m) is dict` 가 **참**이고, 같은 키의 `dict` 와 `==` 가 **참**이다. 문서의 예가 바로 이 비교다.
* ★★★ **②** — `isinstance(m, Movie)` 가 **`TypeError: TypedDict does not support instance and class checks`** 다.
  `issubclass(dict, Movie)` 도 **같은 문구**다. **거짓을 주는 게 아니라 질문 자체를 거부한다.**
  ★ 이유 — 런타임 정체가 `dict` 뿐이라 **「이 dict 가 Movie 인가」를 가를 정보가 객체에 없다.**
  키를 다 훑어 타입까지 보는 것은 **검사기의 일**이라 런타임이 그 질문을 안 받는다.
* ★★★ **③이 이 절의 결론이다 — 계약을 어긴 호출 셋이 전부 통과했다.**
  **필수 키 없음**(`{}`) · **타입 틀림**(`title` 에 `1`) · **없는 키**(`extra`). 에러도 경고도 없다.
  ★ 문서 첫머리 — *"The Python runtime does not enforce function and variable type annotations."*
* ★ **④ — 런타임이 들고는 있다.** `__required_keys__` 에 `title`·`year`, `__optional_keys__` 에 `memo`(`NotRequired`).
  ★★ **들고만 있고 안 쓴다** — ③의 `Movie()` 가 필수 키 없이 통과했다. **메타데이터와 검사는 다른 일**이다.
  ★ `frozenset` 은 순서가 보장 안 되므로 **`sorted()` 로 찍었다.**
* ★ **⑥ — `get_type_hints` 는 `NotRequired` 를 벗겨** `memo` 를 그냥 `str` 로 준다. `include_extras=True` 라야 표시가 남는다.
  ★ 「빠져도 되는 키인가」는 **값의 타입이 아니라 키에 붙은 표시**라서 기본 읽기에서 사라진다.
* ★ **⑤가 ①의 기전이다** — `type(Movie).__call__ is dict` 가 **참**. `Movie(...)` 를 부르면 **메타클래스의 `__call__` 이 곧 `dict`** 라
  **`dict(...)` 를 부른 것과 같다.** ★ 이것은 **CPython 의 `typing.py` 구현**이다 — 계약은 「평범한 `dict` 다」까지다.

**비용** — **런타임 비용 0, 런타임 보호 0.** 보호가 필요하면 **검증 코드를 직접 쓰거나 검증 라이브러리**를 둔다 —
그리고 **그 둘은 이 문서의 창 밖**이다.

### 4. ★★ `NamedTuple` 이 튜플이라서 생기는 일 — `==` 는 이름표를 안 본다

**언제 쓰나** — 좌표·키 같은 **작은 값 묶음**을 `NamedTuple` 로 만들었을 때. **dict 키·정렬·비교**에서 물린다.

```text
   Point(37.5, 127.0)          LatLon(37.5, 127.0)
          \                          /
           \   tuple.__eq__ 로 비교  /     ★ 클래스 이름·필드 이름을 안 본다
            v                      v
             (37.5, 127.0) == (37.5, 127.0)  -> 참

   {p: 'P', g: 'G'}  -> 키 하나 {p: 'G'}    ★ 같다고 답하고 해시도 같으니 겹친다

   frozen dataclass 두 개 -> 거짓 (36번 — 클래스가 같을 때만 비교한다)
```

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

그림 해설.

* ★★★ **①** — `Point` 와 `LatLon` 은 **이름도 필드도 다른데 `==` 가 참**이다. 튜플 `(37.5, 127.0)` 과도 참이다.
  **해시도 같아서** dict 에 넣으면 **키가 하나로 겹치고**, 값은 **나중에 넣은 `'G'`** 가 남는다.
  ★ [11번](../11-tuple-and-unpacking/2-summary.md)의 튜플 비교 규칙 그대로 — **원소를 순서대로 비교할 뿐**이다.
* ★★ **②가 대비다** — 같은 모양의 **frozen dataclass 둘은 `==` 가 거짓**이고 키도 **둘**이다.
  [36번](../36-dataclasses/2-summary.md)의 생성된 `__eq__` 가 **클래스가 같을 때만** 비교하기 때문이다.
* ★ **③ — 튜플의 성질 전부.** `Point(1, 5) < Point(2, 0)` 이 **참**(첫 원소부터 사전식) ·
  **`Point` 와 `LatLon` 이 섞여 정렬된다** · 언패킹·`list()` 가 된다.
  ★ `p + (1,)` 의 결과는 **`tuple`** 이다 — **`Point` 가 아니다.** 튜플 연산은 **이름표를 떨어뜨린다.**
  `_replace` 만이 **같은 클래스를 돌려준다.**

**비용** — 튜플의 비교·해시·정렬이 **공짜로** 온다. 대가는 **「다른 종류인데 같다고 답한다」** 이다 —
단위·좌표계가 다른 값을 dict 키로 섞으면 **조용히 겹친다.**

### 5. ★ `namedtuple` API 와 `NamedTuple` 의 자리 — 필드 이름·기본값·가변 기본값

**언제 쓰나** — 필드 이름을 문자열로 받거나(`namedtuple`), 기본값·메서드를 붙일 때(`NamedTuple`).

```text
   namedtuple("T", "x class")              -> ValueError (키워드)
   namedtuple("T", "x class", rename=True) -> _fields = ('x', '_1')   ★ 위치 번호로 바꿔 준다
   namedtuple("T", "x _y")                 -> ValueError (밑줄 시작)

   class Cart(NamedTuple):
       items: list = []          ★ 막지 않는다 — 두 인스턴스가 같은 리스트를 나눠 쓴다
                                   (36번의 dataclass 는 이 자리에서 ValueError)
```

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

그림 해설.

* ★ **①** — 필드 이름 규칙이 **셋**(키워드 · 밑줄 시작 · 중복)이고 전부 **`ValueError`** 다.
  `rename=True` 면 **거부 대신 `_1` 같은 위치 이름**으로 바꾼다(`class` → `_1`). 바깥 데이터의 열 이름으로 만들 때 쓴다.
* ★ **②** — `NamedTuple` 은 **기본값과 메서드**를 클래스 문법으로 붙인다. `_field_defaults` 에 기본값이 **있는 것만** 들어 있다.
* ★★★ **③이 이 절의 함정이다** — `items: list = []` 가 **그냥 통과**하고, 두 인스턴스가 **같은 리스트**를 쓴다(`is` 가 참).
  **튜플이 불변이어도 담긴 리스트는 가변**이다([11번](../11-tuple-and-unpacking/2-summary.md)).
  ★★ [36번](../36-dataclasses/2-summary.md)의 dataclass 는 **같은 자리에서 `ValueError`** 로 막았다 — **같은 모양인데 한쪽만 막는다.**
  정본은 [20번](../20-mutable-default-args/2-summary.md)의 가변 기본 인자다.
* ★ **④** — `_secret` 같은 **밑줄 필드는 `NamedTuple` 에서도 `ValueError`** 다. `_replace`·`_fields` 같은 **API 이름과 안 겹치게** 막는 것이다.

**비용** — `NamedTuple` 은 **가변 기본값을 막아 주지 않는다.** 필요하면 `None` 센티널을 쓴다([20번](../20-mutable-default-args/2-summary.md)).

### 6. ★★ 런타임이 보는 것 대 타입 검사기만 보는 것

**언제 쓰나** — 「이 어노테이션은 누가 읽나」를 가를 때. [40번](../40-type-hints-at-runtime/2-summary.md)으로 이어지는 축이다.

```text
                                   런타임이 쓴다            런타임이 들고만 있다       검사기만 쓴다 (못 잰 것)
   NamedTuple 의 필드 이름            ● _fields 를 만든다
   NamedTuple 의 필드 타입                                    ● __annotations__
   TypedDict 의 키 목록                                       ● __required_keys__
   TypedDict 의 NotRequired                                   ● __optional_keys__
   값이 그 타입인가                                                                     ?  (이 머신에 검사기 없음)
   키가 빠졌나 · 남았나                                                                 ?
```

* ★★ **「런타임이 쓴다」는 한 칸** — `NamedTuple` 의 **필드 이름**만 실제 구조(`_fields`·`__match_args__`)를 만든다.
* ★ **「들고만 있다」** — 타입·필수 키 목록은 **클래스 속성으로 남지만 어떤 호출도 그것을 확인하지 않는다**(동작 2 의 마지막 행 · 동작 3 의 ③).
* ★★★ **「검사기만 쓴다」 칸은 전부 물음표다.** 이 머신에 검사기가 없어 **무엇을 잡는지 한 칸도 못 쟀다.**
  ★ 여기에 「mypy 가 이것을 잡는다」를 적으면 **돌려 보지 않은 결과**다 — 그래서 비워 뒀다.

## 문법 — 형태와 규칙

**형태**

```text
from collections import namedtuple
from typing import NamedTuple, TypedDict, NotRequired

PtA = namedtuple("PtA", "x y", defaults=[0])          # 문자열로 필드 — 런타임에 만들기 좋다

class PtB(NamedTuple):                                 # 클래스 문법 — 어노테이션이 곧 필드
    x: int
    y: int = 0                                         # 기본값 (★ 가변 기본값을 안 막는다)
    def norm(self): return (self.x ** 2 + self.y ** 2) ** 0.5

class Movie(TypedDict):                                # 키 목록 — ★ 만들면 평범한 dict
    title: str
    year: int
    memo: NotRequired[str]                             # 3.11+ — 빠져도 되는 키

class Opt(TypedDict, total=False):                     # 전부 빠져도 되는 키
    page: int
```

```text
진단 — 런타임 정체를 묻는 세 창

type(C)                 메타클래스 (NamedTuple 은 type, TypedDict 는 _TypedDictMeta)
[k.__name__ for k in C.__mro__]
type(C(...)) is C       ★ TypedDict 만 거짓
typing.is_typeddict(C)  isinstance 대신 "이 클래스가 TypedDict 인가" 를 묻는 길
C._fields · C._field_defaults · C.__required_keys__ · C.__optional_keys__
```

규칙 열.

1. ★★ **`NamedTuple` 은 `namedtuple` 이다** — 런타임 격자에서 **0칸** 갈렸다. 더한 것은 `__annotations__` 뿐이다.
2. ★★ **`NamedTuple` 인스턴스는 튜플이다** — 인덱싱·언패킹·불변·튜플의 `==`.
3. ★★★ **`TypedDict` 로 만든 것은 평범한 `dict` 다** — `type(o) is dict`.
4. ★★★ **`isinstance(o, TypedDict 클래스)` 는 `TypeError`** 다. 거짓이 아니다.
5. ★★★ **`TypedDict` 는 키 누락·잘못된 타입·없는 키를 안 막는다.**
6. ★★ **넷 모두 필드 타입을 확인하지 않는다** — `x: int` 에 문자열이 들어간다.
7. ★★ **다른 두 `NamedTuple` 이 값만 같으면 `==` 가 참**이고 해시도 같다.
8. ★ **튜플 연산의 결과는 `tuple`** 이다 — `p + (1,)` 은 `Point` 가 아니다. `_replace` 는 같은 클래스를 준다.
9. ★ **`NamedTuple` 은 가변 기본값을 막지 않는다** — dataclass 와 반대다.
10. ★ **필드 이름**은 키워드·밑줄 시작·중복이 `ValueError` 다(`rename=True` 로 우회).

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

| 쓴 꼴 | 무슨 일이 나나 | 어디서 드러나나 |
|---|---|---|
| `if isinstance(data, Movie):` | `TypeError` | ★ 즉시(시끄럽다) |
| `Movie(**json.loads(body))` 로 「검증했다」고 여김 | **아무것도 확인 안 한다** | ★ 에러 없음 |
| `Point` 와 `LatLon` 을 한 dict 의 키로 | 값이 같으면 **겹친다** | ★ 에러 없음 |
| `class Cart(NamedTuple): items: list = []` | 인스턴스끼리 **리스트 공유** | ★ 에러 없음 |
| `p + (z,)` 로 필드를 늘렸다고 여김 | 결과는 **`tuple`** | ★ `.x` 를 쓸 때 `AttributeError` |
| `for v in record:` 를 실수로 | 필드를 **값으로 순회**한다 | ★ 에러 없음 |

★ **시끄러운 것은 첫 줄 하나뿐이다.**

## 어디서 틀리나

### (1) ★★★ 「`TypedDict` 로 선언했으니 틀린 dict 는 에러가 난다」

**런타임은 아무것도 안 본다**(동작 3 의 ③ — 세 번 다 통과). `Movie(...)` 는 **`dict(...)` 와 같다.**\
★ **검사기가 무엇을 잡는지는 이 문서가 못 쟀다** — 이 머신에 없다. 「검사기가 잡는다」도 **확인한 말이 아니다.**

### (2) ★★★ `isinstance(x, Movie)` 로 분기한다

**`TypeError`** 다(동작 3 의 ②). 클래스 쪽 질문이 필요하면 **`typing.is_typeddict(Movie)`**(인스턴스가 아니라 **클래스**를 묻는다).\
★ 인스턴스가 모양에 맞는지는 **키와 값을 직접 보는 코드**로만 알 수 있다.

### (3) ★★ 「`NamedTuple` 은 튜플과 다른 새 타입이다」

**`namedtuple` 과 한 칸도 안 다르다**(격자 0칸). `__mro__` 에 **`tuple` 만** 있다.

### (4) ★★ 모양이 같은 두 `NamedTuple` 을 섞어 쓴다

**`==` 가 참이고 해시가 같다**(동작 4 의 ①). dict 키로 섞으면 **하나가 사라진다.**\
★ 종류까지 같아야 같은 값이면 **frozen dataclass** 다.

### (5) ★ 「`frozen` 한 튜플이니 안전하다」

**담긴 리스트는 바뀐다** — 그리고 **가변 기본값은 인스턴스끼리 공유**된다(동작 5 의 ③).

### (6) ★ 튜플 연산 뒤에도 필드 이름이 남는다고 믿는다

`p + (1,)`·슬라이스·`sorted()` 는 **`tuple`/`list`** 를 준다. **이름표가 떨어진다.**

### (7) ★ `__required_keys__` 가 있으니 런타임이 필수 키를 확인한다고 믿는다

**들고만 있다**(동작 3 의 ④ · `Movie()` 가 `{}` 로 통과).

### (8) ★ 「검사기가 없는데 검사기 결과를 적는다」

★ 이 문서의 규칙 — **못 잰 것은 못 잰 것으로 적는다.** 「mypy 는 이것을 에러로 본다」는 **이 머신에서 한 번도 돌지 않은 문장**이다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ 이 주제도 **`typing`·`collections` 모듈의 계약**으로 읽는다.
★★ 그리고 **네 번째 층이 따로 있다 — 「타입 검사기의 판정」.** 그 층은 **이 머신에서 못 잰 것**이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **모듈 계약(언어 보장에 해당)** | `typing`·`collections` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 · `typing.py` 소스 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 예외 문구 |
| ★ **타입 검사기의 판정** | mypy·pyright 가 무엇을 잡나 | ★★★ **못 잰 것** — 도구가 없다 |

### 모듈 계약

| 사실 | 근거 |
|---|---|
| 런타임은 어노테이션을 **강제하지 않는다** | `typing` 첫머리 — *"does not enforce function and variable type annotations"* |
| `NamedTuple` 은 **`namedtuple` 의 타입 붙은 판** | `typing` — *"Typed version of `collections.namedtuple()`"* |
| `TypedDict` 는 런타임에 **평범한 `dict`** | `typing` — 문서 예가 `Point2D(...) == dict(...)` |
| `TypedDict` 는 **`isinstance`·`issubclass` 에 못 쓴다** | `typing` |
| 필드 이름은 키워드·밑줄 시작·중복이 안 된다 | `collections` |
| `_replace`·`_asdict`·`_fields`·`_field_defaults` | `collections` |
| `NotRequired` 는 **3.11** 신설 | `typing`(PEP 655) |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★★ `type(Movie).__call__ is dict` | 실행 · `typing.py` 의 `__call__ = dict` 한 줄 |
| `TypedDict` 클래스의 메타클래스가 **`_TypedDictMeta`** | 실행 — 밑줄로 시작하는 내부 이름 |
| ★ `TypedDict` 클래스의 `__mro__` 에 **`dict` 가 있다** | 실행 — 그런데 인스턴스는 그 클래스가 아니다 |
| `NamedTuple` 클래스의 메타클래스가 **`type`** | 실행 |
| `NamedTuple` 이 `namedtuple` 에 **`__annotations__`·`__orig_bases__` 만** 더한다 | 실행 — 던더 집합 차 |
| 예외 **문구** 전부 | 실행 |

### 이 판의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `TypedDict does not support instance and class checks` 라는 **문구** | 종류(`TypeError`)는 계약, 문구는 아니다 |
| `namedtuple` 의 필드 이름 오류 **문구** 셋 | 같다 |

### 그래서 이렇게 적으면 틀린다

* ✗ 「`TypedDict` 는 `dict` 의 하위 클래스를 만든다」\
  ○ **클래스의 `__mro__` 에는 `dict` 가 있지만 만든 것은 평범한 `dict`** 다. 두 창이 다른 답을 준다.
* ✗ 「`NamedTuple` 은 필드 타입을 확인한다」\
  ○ **안 한다.** 격자의 마지막 행이 네 열 다 통과다.
* ✗ 「타입 검사기가 `Movie()` 를 잡는다」\
  ○ ★ **이 머신에서 못 잰 것**이다. 검사기 쪽 판정은 이 문서가 한 칸도 확인하지 않았다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 작은 **불변 값 묶음**, 튜플로도 쓰고 싶다(언패킹·`csv` 행) | `NamedTuple` | 튜플이 그대로 필요할 때만. **다른 종류와 `==` 가 겹치는 것**을 감수한다 |
| 필드 이름이 **실행 중에 정해진다** | `collections.namedtuple` | 문자열로 필드를 받는다 · `rename=True` |
| **JSON 의 모양**을 적어 두고 싶다 | `TypedDict` | 런타임 비용 0. ★ **검증은 따로** 써야 한다 |
| 종류까지 같아야 같은 값 · 가변 기본값을 막고 싶다 | ★ **dataclass** | [36번](../36-dataclasses/2-summary.md) — 클래스가 다르면 `==` 가 거짓 |
| 들어온 dict 를 **검증**하고 싶다 | 직접 쓴 검사 코드 | 넷 중 **어느 것도 값을 확인하지 않는다** |

## 핵심 문장

1. **`NamedTuple` 은 `namedtuple` 이다** — 런타임 격자에서 **0칸** 갈렸고, 더한 것은 `__annotations__` 뿐이다.
2. **`TypedDict` 로 만든 것은 평범한 `dict` 다** — `isinstance` 로 물으면 **거짓이 아니라 `TypeError`** 다.
3. **네 구조체 중 어느 것도 필드 타입을 확인하지 않는다** — 격자 마지막 행이 네 칸 다 통과였다.
4. **`NamedTuple` 의 `==` 는 튜플의 `==`** 다 — 이름이 다른 두 구조체도 값만 같으면 같고, dict 키로 겹친다.
5. **어노테이션을 누가 읽나를 가르면** — 런타임이 **쓰는 것**(필드 이름), **들고만 있는 것**(타입·필수 키), **검사기만 쓰는 것**(이 머신에서 못 잰 것)이 갈린다.

## 관련 자료

* 선행: [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md) —
  ★ **경계**: 튜플의 비교·언패킹·불변은 그쪽이 정본이고, 여기는 **그 성질이 `NamedTuple` 에 그대로 온다**는 것만.
* 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — `TypedDict` 인스턴스가 **그 `dict`** 다.
* 선행: [36-dataclasses](../36-dataclasses/2-summary.md) — ★ **경계**: 생성되는 메서드는 그쪽, 여기는 **런타임 정체 격자의 넷째 열**로만 썼다.
* 선행: [35-abc-and-protocol](../35-abc-and-protocol/2-summary.md) — ★★ **타입 검사기 부재 판정의 정본**이 그쪽이고 여기서 다시 물어 같은 답을 받았다.
  ★ `Protocol` 이 **런타임에 안 막는다**는 것과 `TypedDict` 가 **안 막는다**는 것이 **같은 축**이다.
* 선행: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — 동작 5 의 ③.
* 이어지는 곳: [37-enum](../37-enum/2-summary.md) — ★ **「값이 같으면 다른 종류끼리도 같다」가 거기서는 `IntEnum` 으로** 나왔다.
* 이어지는 곳: [39-match-statement](../39-match-statement/2-summary.md) — `NamedTuple` 도 **`__match_args__`** 를 가져 클래스 패턴에 쓰인다.
* 이어지는 곳: [40-type-hints-at-runtime](../40-type-hints-at-runtime/2-summary.md) — ★★ **「런타임이 들고만 있다」의 정본**이 그쪽이다.
* 대비: [TS 01번](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md) — TS 의 `interface` 는 **방출에서 통째로 사라진다**.
  파이썬 `TypedDict` 는 **클래스로 남아 키 목록까지 들고 있지만 확인은 안 한다** — **남되 안 쓴다**.
* 공식 문서: [`typing.NamedTuple`](https://docs.python.org/3.12/library/typing.html#typing.NamedTuple) ·
  [`typing.TypedDict`](https://docs.python.org/3.12/library/typing.html#typing.TypedDict) ·
  [`collections.namedtuple`](https://docs.python.org/3.12/library/collections.html#collections.namedtuple) ·
  [PEP 589](https://peps.python.org/pep-0589/) · [PEP 655](https://peps.python.org/pep-0655/)

## 용어 풀이

* **`namedtuple`**: 필드 이름을 붙인 **튜플의 하위 클래스**를 만드는 공장 함수.\
  예: `namedtuple("PtA", "x y")`.
* **`NamedTuple`**: 같은 것을 **클래스 문법과 어노테이션**으로 만드는 장치.\
  예: 만든 클래스의 `__mro__` 에 `NamedTuple` 은 없고 **`tuple`** 이 있다.
* **`TypedDict`**: **키와 값 타입의 목록**을 선언하는 장치. 만든 것은 **평범한 `dict`**.\
  예: `type(Movie(title="Up", year=2009)) is dict`.
* **`total` / `NotRequired`**: 키가 **빠져도 되는지**를 적는 표시. 런타임은 **목록만 들고 있다**.\
  예: `__optional_keys__` 에 `memo` 가 있다.
* **`__required_keys__`**: `TypedDict` 클래스가 들고 있는 **필수 키 목록**(`frozenset`).
* **런타임 정체**: 실행 중에 그 객체가 **실제로 무엇인가.**\
  예: `type()`·`isinstance`·`__mro__` 로 묻는다.
* **메타클래스**: **클래스를 만드는 클래스.**\
  예: `TypedDict` 클래스의 메타클래스는 `_TypedDictMeta`, `NamedTuple` 클래스의 것은 그냥 `type`.
* **타입 검사기**: 실행하지 않고 어노테이션을 읽어 모순을 찾는 **별도 도구**.\
  예: mypy·pyright — ★ **이 머신에 없다.**
* **`_replace`**: 필드 하나를 바꾼 **같은 클래스의 새 인스턴스**를 준다.\
  예: `p._replace(x=0)` 은 `Point`, `p + (1,)` 은 `tuple`.
* **`rename=True`**: 쓸 수 없는 필드 이름을 **`_1` 같은 위치 이름**으로 바꿔 주는 옵션.
* **`is_typeddict`**: 「이 **클래스**가 `TypedDict` 인가」를 묻는 함수. `isinstance` 가 막힌 자리의 대안이다.

## 더 들어가면

* ★ **`typing.get_type_hints(Movie)`** 는 `NotRequired[...]` 를 **벗겨** `str` 만 주고, `include_extras=True` 면 **남긴다**(동작 3 의 ⑥).
  어노테이션을 되살려 읽는 함수의 정본은 [40번](../40-type-hints-at-runtime/2-summary.md)이다.
* ★ **런타임에 모양을 검사해 주는 라이브러리**들은 전부 **어노테이션을 읽어 스스로 검사하는** 쪽이다 —
  「런타임은 안 본다」의 **예외가 아니라, 그 빈자리를 채우는 제3자**다.
