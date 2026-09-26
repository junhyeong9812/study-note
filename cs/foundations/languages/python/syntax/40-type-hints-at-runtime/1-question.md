# python/syntax/40-type-hints-at-runtime — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **`<평가됨: …>` 줄이 어디에 몇 줄 찍히나**까지 적어야 맞은 것이다 — 순서가 답이다.
> ★★★ 3번은 **격자의 칸을 하나씩** 채우고 마지막 줄의 숫자까지 적는다.
> ★★ 이 주제는 **「타입 검사기라면」·「3.14 라면」을 묻지 않는다** — 둘 다 이 머신에 없어 정답을 확인할 수 없다.
>
> 실행 환경: `python3` **3.12.3** · Linux(3번은 `python3.11` 3.11.15 도 함께). 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [19](../19-function-argument-rules/1-question.md)(매개변수) · [36](../36-dataclasses/1-question.md)(dataclass) ·
> [38](../38-namedtuple-and-typeddict/1-question.md)(`NamedTuple`·`TypedDict`).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 힌트와 다른 값 · 변수 어노테이션 · 평가 시각 (예측)

```python
# e40_runs.py
def f(x: int) -> str:
    return x


print("① 힌트와 다른 값을 넣고 부른다")
for arg in (5, "문자열", [1, 2]):
    r = f(arg)
    print("   f(%r) -> %r  type=%s" % (arg, r, type(r).__name__))
print("   f.__annotations__ :", f.__annotations__)

print("② 변수 어노테이션")
n: int = "숫자 아님"
print("   n =", repr(n))
m: int
print("   'm' in globals() :", "m" in globals())
print("   __annotations__  :", __annotations__)

print("③ 어노테이션 식은 언제 평가되나")


def tag(text):
    print("      <평가됨:", text + ">")
    return int


print("   def 직전")


def g(a: tag("g 의 매개변수")) -> tag("g 의 반환"):
    b: tag("g 안의 지역 변수") = 1
    return b


print("   def 직후, 호출 직전")
g(1)
print("   호출 직후")


class K:
    print("   class 몸통 시작")
    k: tag("K 의 클래스 변수")
    print("   class 몸통 끝")


print("   K.__annotations__ :", K.__annotations__)
print("   'k' in vars(K)    :", "k" in vars(K))
```

### 2. ★★★ 한 줄 차이의 두 파일 (예측)

두 소스는 **맨 윗줄 하나만** 다르다. 두 출력을 따로 적는다.

```python
# e40_default.py
import typing


def f(x: int, y: "int", z: list[int]) -> None:
    pass


print("① f.__annotations__")
for k, v in f.__annotations__.items():
    print("   %-6s %-12r type=%s" % (k, v, type(v).__name__))

print("② 정의되지 않은 이름을 힌트에 쓴 def")
try:
    def g(x: Undefined) -> None:
        pass
    print("   def 통과 — g.__annotations__ :", g.__annotations__)
except NameError as exc:
    print("   ", type(exc).__name__ + ":", exc)

print("③ typing.get_type_hints(f)")
print("   ", typing.get_type_hints(f))
```

```python
# e40_future.py
from __future__ import annotations
import typing


def f(x: int, y: "int", z: list[int]) -> None:
    pass


print("① f.__annotations__")
for k, v in f.__annotations__.items():
    print("   %-6s %-12r type=%s" % (k, v, type(v).__name__))

print("② 정의되지 않은 이름을 힌트에 쓴 def")
try:
    def g(x: Undefined) -> None:
        pass
    print("   def 통과 — g.__annotations__ :", g.__annotations__)
except NameError as exc:
    print("   ", type(exc).__name__ + ":", exc)

print("③ typing.get_type_hints(f)")
print("   ", typing.get_type_hints(f))
```

### 3. ★★★ 탐침 열 개를 두 모드로 (예측)

```text
각 칸에 값의 repr 또는 예외 종류를 적는다. 마지막 줄의 N / M 도 적는다.
같은 소스를 python3.11 로 던지면 무엇이 달라지는지도 적는다.
```

```python
# e40_grid.py
import sys
import types

HEADER = "from __future__ import annotations\n"

PROBES = [
    ("f.__annotations__['x']", """
def f(x: int): pass
out = f.__annotations__['x']
"""),
    ("정의 안 된 이름 힌트", """
def f(x: Undefined): pass
out = 'def 통과'
"""),
    ("def 때 힌트 식 평가 횟수", """
calls = []
def f(x: calls.append(1) or int): pass
out = len(calls)
"""),
    ("class 몸통 a: int", """
class C:
    a: int
out = C.__annotations__['a']
"""),
    ("dataclass Field.type", """
from dataclasses import dataclass, fields
@dataclass
class D:
    a: int
out = fields(D)[0].type
"""),
    ("dataclass ClassVar 제외", """
from dataclasses import dataclass, fields
from typing import ClassVar
@dataclass
class D:
    a: int
    b: ClassVar[int] = 0
out = [f.name for f in fields(D)]
"""),
    ("NamedTuple __annotations__", """
from typing import NamedTuple
class N(NamedTuple):
    a: int
out = N.__annotations__['a']
"""),
    ("singledispatch 지역 클래스", """
import functools
def build():
    class Local: pass
    @functools.singledispatch
    def s(x): return 'base'
    @s.register
    def _(x: Local): return 'Local'
    return s(Local())
out = build()
"""),
    ("get_type_hints(f)['x']", """
import typing
def f(x: int): pass
out = typing.get_type_hints(f)['x']
"""),
    ("f('s') 반환", """
def f(x: int) -> int: return x
out = f('s')
"""),
]


def run(src, _seq=[0]):
    # 탐침마다 진짜 모듈을 만들어 sys.modules 에 올린다 — dataclass 가 cls.__module__ 로 모듈을 찾는다
    _seq[0] += 1
    mod = types.ModuleType("probe%d" % _seq[0])
    sys.modules[mod.__name__] = mod
    try:
        exec(compile(src, "<probe>", "exec"), mod.__dict__)
        return repr(mod.__dict__["out"])
    except Exception as exc:
        return type(exc).__name__
    finally:
        del sys.modules[mod.__name__]


print("판 :", sys.version_info[:2])
print("%-28s | %-22s | %s" % ("탐침", "기본", "from __future__"))
split = 0
for label, body in PROBES:
    a = run(body)
    b = run(HEADER + body)
    split += a != b
    print("%-28s | %-22s | %s" % (label, a, b))
print("갈린 칸 %d / %d" % (split, len(PROBES)))
```

### 4. ★★ 어노테이션을 지우면 (예측)

```python
# e40_exceptions.py
import functools
from dataclasses import dataclass, fields
from enum import Enum
from typing import NamedTuple, TypedDict


def cell(fn):
    try:
        return repr(fn())
    except Exception as exc:
        return type(exc).__name__


def dc_with():
    @dataclass
    class D:
        a: int = 1
    return [f.name for f in fields(D)]


def dc_without():
    @dataclass
    class D:
        a = 1
    return [f.name for f in fields(D)]


def nt_with():
    class N(NamedTuple):
        a: int = 1
    return N._fields


def nt_without():
    class N(NamedTuple):
        a = 1
    return N._fields


def td_with():
    class T(TypedDict):
        a: int
    return sorted(T.__required_keys__)


def td_without():
    class T(TypedDict):
        pass
    return sorted(T.__required_keys__)


def sd_with():
    @functools.singledispatch
    def s(x):
        return "base"

    @s.register
    def _(x: int):
        return "int"
    return s(1)


def sd_without():
    @functools.singledispatch
    def s(x):
        return "base"

    @s.register
    def _(x):
        return "int"
    return s(1)


def enum_with():
    class E(Enum):
        A = 1
        b: int
    return [m.name for m in E]


def enum_without():
    class E(Enum):
        A = 1
    return [m.name for m in E]


def plain_with():
    class P:
        a: int = 1
    return P().a


def plain_without():
    class P:
        a = 1
    return P().a


rows = [
    ("dataclass", dc_with, dc_without),
    ("NamedTuple", nt_with, nt_without),
    ("TypedDict", td_with, td_without),
    ("singledispatch", sd_with, sd_without),
    ("Enum", enum_with, enum_without),
    ("보통 class", plain_with, plain_without),
]
print("%-15s | %-12s | %s" % ("장치", "힌트 있음", "힌트 없음"))
changed = 0
for name, with_, without in rows:
    a = cell(with_)
    b = cell(without)
    changed += a != b
    print("%-15s | %-12s | %s" % (name, a, b))
print("힌트가 결과를 바꾼 칸 %d / %d" % (changed, len(rows)))
```

### 5. ★★ 되살리는 세 길 (예측)

```python
# e40_hints.py
import inspect
import typing


class Node:
    def link(self, other: "Node") -> "Node | None":
        return None


def size(items: "list[Node]", limit: None = None) -> "int":
    return 0


print("① size.__annotations__")
print("   ", size.__annotations__)

print("② typing.get_type_hints")
print("   ", typing.get_type_hints(size))
print("   ", typing.get_type_hints(Node.link))

print("③ inspect.get_annotations — 기본과 eval_str=True")
print("   ", inspect.get_annotations(size))
print("   ", inspect.get_annotations(size, eval_str=True))

print("④ 'Missing' 을 적은 함수")


def broken(x: "Missing") -> None:
    pass


for label, call in (("get_type_hints", lambda: typing.get_type_hints(broken)),
                    ("get_annotations(eval_str=True)",
                     lambda: inspect.get_annotations(broken, eval_str=True))):
    try:
        print("   ", label, "->", call())
    except NameError as exc:
        print("   ", label, "->", type(exc).__name__ + ":", exc)
print("    broken('아무거나') ->", broken("아무거나"))
```

### 6. ★★ 지역 변수 어노테이션이 평가되지 않는다는 것을 무엇으로 보였나 (왜)

* `__annotations__` 를 찍는 창으로는 **왜 원리상 안 보이나**?
* 이 문서가 바꿔 쓴 창은 무엇이고, 그 창이 **무엇을 출력 순서로** 드러내나?

### 7. ★★★ 판 격자의 3.14 열 (경계)

* 3.14 열의 칸들은 **어떤 상태**로 적혔나 — 그 판정의 근거가 된 출력 두 줄은?
* `__future__.annotations` 의 **의무 판이 `None`** 이라는 것은 무슨 뜻인가?

### 8. ★★ `singledispatch` 가 `__future__` 아래서 깨진 이유 (왜)

* 3번 격자에서 `singledispatch 지역 클래스` 칸이 **`__future__` 쪽에서만** 예외가 난 이유는?
* 같은 격자의 **`get_type_hints(f)['x']`** 칸은 왜 안 깨졌나?

### 9. 층 가르기 (경계)

* 「런타임은 어노테이션을 강제하지 않는다」·「`__future__` 아래 `NamedTuple` 이 `ForwardRef('int')` 를 담는다」·「`get_type_hints` 가 `None` 을 `NoneType` 으로 준다」 —
  각각 **언어 보장 · 모듈 계약 · CPython 구현** 중 어디인가?
* ★ 3번 격자를 처음 만들 때 생긴 **가짜 갈림**은 무엇이었고, 왜 숫자만 봐서는 안 걸렸나?

### 10. 이웃 주제와의 경계 (연결)

* ★ [TS 01번](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md)의 방출물과 파이썬의 `__annotations__` — **사라지나 남나**, 그리고 **실행이 바뀌나**?
* ★ [36번](../36-dataclasses/2-summary.md)이 「절반만 예외」라 부른 것은 이 주제의 **어느 격자 어느 행**인가?
* ★ [38번](../38-namedtuple-and-typeddict/2-summary.md)의 「쓴다 / 들고만 있다 / 검사기만 쓴다」 세 칸에 **`singledispatch`** 는 어디에 들어가나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
