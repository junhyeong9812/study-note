# python/syntax/40-type-hints-at-runtime — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★★ **3.14 와 타입 검사기 쪽 답은 하나도 없다** — 둘 다 이 머신에 없다([2-summary.md](2-summary.md) 첫 블록 · [35번](../35-abc-and-protocol/2-summary.md)).

## 정답

### 1. 세 호출이 다 돈다 · `m` 은 안 생긴다 · 매개변수·반환은 `def` 때, 지역 변수는 한 번도, 클래스 변수는 몸통에서

**출력**

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

```text
===== python3 - <e40_runs.py =====
① 힌트와 다른 값을 넣고 부른다
   f(5) -> 5  type=int
   f('문자열') -> '문자열'  type=str
   f([1, 2]) -> [1, 2]  type=list
   f.__annotations__ : {'x': <class 'int'>, 'return': <class 'str'>}
② 변수 어노테이션
   n = '숫자 아님'
   'm' in globals() : False
   __annotations__  : {'n': <class 'int'>, 'm': <class 'int'>}
③ 어노테이션 식은 언제 평가되나
   def 직전
      <평가됨: g 의 매개변수>
      <평가됨: g 의 반환>
   def 직후, 호출 직전
   호출 직후
   class 몸통 시작
      <평가됨: K 의 클래스 변수>
   class 몸통 끝
   K.__annotations__ : {'k': <class 'int'>}
   'k' in vars(K)    : False
(exit 0)
```

**왜 그런가**

* ★★★ **①** — `5`·`'문자열'`·`[1, 2]` 가 **그대로 돌아왔다.** 런타임은 어노테이션을 **강제하지 않는다.**
* ★★ **②** — `n` 에 문자열이 그대로 들어갔고, **값 없는 `m: int` 는 이름을 안 만든다**(`False`). 그런데 **모듈 `__annotations__` 에는 `m` 이 있다.**
* ★★★ **③** — `def 직전` 과 `def 직후` 사이에 **두 줄**(매개변수·반환) — **`def` 때 평가.**
  ★★ **`g 안의 지역 변수` 는 한 번도 안 찍혔다** — `g(1)` 을 불렀는데도.
  ★ 클래스 변수 어노테이션은 **몸통이 실행될 때** 평가됐고, **`'k' in vars(K)` 는 `False`**(속성은 안 생긴다).

### 2. 기본 판은 객체 · `NameError` / `__future__` 판은 전부 문자열 · 통과 — `get_type_hints` 는 두 판 같다

**출력**

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

```text
===== python3 - <e40_default.py =====
① f.__annotations__
   x      <class 'int'> type=type
   y      'int'        type=str
   z      list[int]    type=GenericAlias
   return None         type=NoneType
② 정의되지 않은 이름을 힌트에 쓴 def
    NameError: name 'Undefined' is not defined
③ typing.get_type_hints(f)
    {'x': <class 'int'>, 'y': <class 'int'>, 'z': list[int], 'return': <class 'NoneType'>}
(exit 0)
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

```text
===== python3 - <e40_future.py =====
① f.__annotations__
   x      'int'        type=str
   y      "'int'"      type=str
   z      'list[int]'  type=str
   return 'None'       type=str
② 정의되지 않은 이름을 힌트에 쓴 def
   def 통과 — g.__annotations__ : {'x': 'Undefined', 'return': 'None'}
③ typing.get_type_hints(f)
    {'x': <class 'int'>, 'y': <class 'int'>, 'z': list[int], 'return': <class 'NoneType'>}
(exit 0)
```

**왜 그런가**

* ★★★ **①** — 기본 판은 **평가된 객체**(`int` · `list[int]` · `None`), `__future__` 판은 **전부 `str`**.
  ★★ **`y: "int"` 가 `"'int'"`** — 이미 문자열인 것을 **한 번 더** 싼다(HOWTO 의 *"quoted twice"*).
* ★★★ **②** — 정의 안 된 `Undefined` 가 기본 판은 **`NameError`**, `__future__` 판은 **통과**. **`def` 때 평가를 안 하기** 때문이다.
* ★★ **③** — `get_type_hints` 는 **두 판 모두 같은 값**을 준다(문자열을 평가해 되살림). `None` 은 **`NoneType`** 이 된다.

### 3. `갈린 칸 7 / 10` — 3.11 도 한 글자도 같다

**출력**

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

```text
===== python3 - <e40_grid.py =====
판 : (3, 12)
탐침                           | 기본                     | from __future__
f.__annotations__['x']       | <class 'int'>          | 'int'
정의 안 된 이름 힌트                 | NameError              | 'def 통과'
def 때 힌트 식 평가 횟수             | 1                      | 0
class 몸통 a: int              | <class 'int'>          | 'int'
dataclass Field.type         | <class 'int'>          | 'int'
dataclass ClassVar 제외        | ['a']                  | ['a']
NamedTuple __annotations__   | <class 'int'>          | ForwardRef('int')
singledispatch 지역 클래스        | 'Local'                | NameError
get_type_hints(f)['x']       | <class 'int'>          | <class 'int'>
f('s') 반환                    | 's'                    | 's'
갈린 칸 7 / 10
(exit 0)
```

```text
===== python3.11 - <e40_grid_py311.py =====
판 : (3, 11)
탐침                           | 기본                     | from __future__
f.__annotations__['x']       | <class 'int'>          | 'int'
정의 안 된 이름 힌트                 | NameError              | 'def 통과'
def 때 힌트 식 평가 횟수             | 1                      | 0
class 몸통 a: int              | <class 'int'>          | 'int'
dataclass Field.type         | <class 'int'>          | 'int'
dataclass ClassVar 제외        | ['a']                  | ['a']
NamedTuple __annotations__   | <class 'int'>          | ForwardRef('int')
singledispatch 지역 클래스        | 'Local'                | NameError
get_type_hints(f)['x']       | <class 'int'>          | <class 'int'>
f('s') 반환                    | 's'                    | 's'
갈린 칸 7 / 10
(exit 0)
```

**왜 그런가**

* (3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e40_grid_py311.py` 다.)
* ★★★ **갈린 일곱** — `__annotations__`·클래스 몸통·dataclass `Field.type` 이 **`int` → `'int'`**, 정의 안 된 이름이 **`NameError` → 통과**,
  평가 횟수 **`1` → `0`**, `NamedTuple` 이 **`int` → `ForwardRef('int')`**, `singledispatch` 지역 클래스가 **`'Local'` → `NameError`**.
* ★★ **안 갈린 셋** — dataclass `ClassVar` 제외 · `get_type_hints` · **`f('s')` 가 `'s'`**.
  ★★★ **마지막 행이 결론이다 — 모드를 바꿔도 실행은 안 바뀐다.** 바뀌는 것은 **어노테이션을 읽는 쪽**뿐이다.
* ★★ **3.11 이 한 글자도 같다** — 판이 갈리는 곳은 **3.14**(문서)이지 3.11 ↔ 3.12 가 아니다.
* ★ `NamedTuple` 은 **`ForwardRef` 로 싸고** dataclass 는 **문자열 그대로** — **읽는 쪽마다 받는 모양이 다르다.**

### 4. `힌트가 결과를 바꾼 칸 4 / 6` — dataclass·`NamedTuple`·`TypedDict`·`singledispatch`

**출력**

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

```text
===== python3 - <e40_exceptions.py =====
장치              | 힌트 있음        | 힌트 없음
dataclass       | ['a']        | []
NamedTuple      | ('a',)       | ()
TypedDict       | ['a']        | []
singledispatch  | 'int'        | TypeError
Enum            | ['A']        | ['A']
보통 class        | 1            | 1
힌트가 결과를 바꾼 칸 4 / 6
(exit 0)
```

**왜 그런가**

* ★★★ **dataclass** — 어노테이션을 지우면 **필드가 사라진다**. `a = 1` 은 그냥 클래스 변수다.
* ★★ **`NamedTuple`·`TypedDict`** — 필드·키 목록이 **어노테이션에서** 온다. 지우면 빈다.
* ★★ **`singledispatch`** — `register` 가 **첫 인자의 어노테이션**을 읽는다. 없으면 **`TypeError`**.
  ★ 그 예외 메시지에는 **함수 객체의 `repr`(주소)** 이 들어 있어서 **예외 종류만** 찍었다.
* ★ **`Enum`**(몸통의 `b: int` 는 멤버가 아니다)과 **보통 클래스**는 **안 바뀐다.**
* ★★ **「힌트는 실행을 안 바꾼다」의 정확한 뜻** — **힌트를 받은 함수**의 실행은 안 바뀐다(3번 마지막 행).
  **힌트를 읽는 장치**의 결과는 바뀐다(이 격자).

### 5. 적힌 그대로 · 되살림 + `NoneType` · `eval_str` 은 `None` 을 그대로 · 되살릴 이름이 없으면 둘 다 `NameError`

**출력**

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

```text
===== python3 - <e40_hints.py =====
① size.__annotations__
    {'items': 'list[Node]', 'limit': None, 'return': 'int'}
② typing.get_type_hints
    {'items': list[__main__.Node], 'limit': <class 'NoneType'>, 'return': <class 'int'>}
    {'other': <class '__main__.Node'>, 'return': __main__.Node | None}
③ inspect.get_annotations — 기본과 eval_str=True
    {'items': 'list[Node]', 'limit': None, 'return': 'int'}
    {'items': list[__main__.Node], 'limit': None, 'return': <class 'int'>}
④ 'Missing' 을 적은 함수
    get_type_hints -> NameError: name 'Missing' is not defined
    get_annotations(eval_str=True) -> NameError: name 'Missing' is not defined
    broken('아무거나') -> None
(exit 0)
```

**왜 그런가**

* ★ **①** — `__annotations__` 는 **적힌 그대로** — 문자열은 문자열, `None` 은 `None`.
* ★★ **②** — `get_type_hints` 는 문자열을 평가하고 **`None` 을 `NoneType`** 으로 바꾼다. `'Node | None'` 도 되살아났다.
* ★★ **③** — `inspect.get_annotations` 는 기본이 **평가 안 함**, `eval_str=True` 라야 평가하고 **`None` 은 그대로** 둔다.
  **두 함수가 같은 일을 하지 않는다.**
* ★★★ **④** — `'Missing'` 은 **둘 다 `NameError`**. 그런데 **`broken('아무거나')` 는 그냥 `None` 을 돌려준다** — 깨지는 것은 **읽는 쪽**뿐이다.

### 6. 담기지도 않으니 값 창에는 안 보인다 — 부르면 한 줄 찍는 함수를 어노테이션 자리에 넣었다

**왜 그런가**

* ★★ 지역 변수 어노테이션은 **평가도 저장도 안 된다.** 그래서 `__annotations__` 를 아무리 찍어도 **「없다」와 「평가됐는데 안 담겼다」를 가를 수 없다** — 둘 다 빈칸이다.
* ★★★ 바꾼 창 — **`tag("…")` 처럼 부르면 `<평가됨: …>` 을 찍고 `int` 를 돌려주는 함수**를 어노테이션 자리에 넣었다.
  그러면 **평가 시각이 출력 순서로** 드러난다 — `def 직전`/`직후` 사이, `class 몸통 시작`/`끝` 사이.
  **`g(1)` 을 부른 뒤에도 `g 안의 지역 변수` 줄이 없다**는 것이 「평가되지 않는다」의 증거다(1번 ③).
* ★ 이 창이 [2-summary.md](2-summary.md)의 **네 번째 창**이다.

### 7. 전부 문서만 — `python3.14` 가 `None` · `annotationlib` 이 `ModuleNotFoundError` · 의무 판은 「정해지지 않았다」

**왜 그런가**

* ★★★ 3.14 열은 **못 잰 것**이다. 근거가 된 두 줄(요약 첫 블록) — **`PATH 의 python3.14 : None`** 과
  **`import annotationlib -> ModuleNotFoundError: No module named 'annotationlib'`**. 3.11 판도 같았다.
* ★★ 그래서 3.14 칸은 **What's New 문장**만 옮겼다 — *"annotations are no longer evaluated eagerly … evaluated only when necessary"*.
  「3.14 에서 확인했다」로 적으면 **틀린다.**
* ★ **의무 판 `None`** — `__future__` 의 각 기능은 **「언제부터 쓸 수 있나」(선택 판)** 와 **「언제 기본이 되나」(의무 판)** 를 들고 있다.
  `annotations` 의 의무 판이 **`None`** 이라는 것은 **기본이 될 판이 정해져 있지 않다**는 뜻이다 — 이 판(3.11·3.12)의 `__future__` 모듈이 그렇게 답했다.

### 8. 되살리기가 **모듈 전역**에서 이름을 찾는데 지역 클래스는 거기 없다 — `int` 는 내장이라 찾아진다

**왜 그런가**

* ★★★ `__future__` 아래에서 `register` 는 첫 인자의 어노테이션을 **문자열 `'Local'`** 로 받는다.
  그것을 타입으로 되살리려고 **평가**하는데, 평가는 **함수가 정의된 모듈의 전역 이름공간**에서 이름을 찾는다.
  `Local` 은 `build()` **안의 지역 클래스**라 전역에 없다 → **`NameError`**.
* ★★ 기본 판은 **`def` 때 이미 평가**해서 `Local` **클래스 객체 자체**를 담으므로 되살릴 일이 없다 → `'Local'`.
* ★ `get_type_hints(f)['x']` 는 **`'int'` 를 되살리는데 `int` 가 내장 이름이라** 어디서든 찾아진다 → 안 깨졌다.
* ★ 그래서 **`__future__` 가 위험한 자리는 「지역에서 정의한 이름을 힌트에 쓰고 그 힌트를 실행 중에 읽는 코드」** 다.

### 9. 보장 · 구현 · 모듈 계약 — 가짜 갈림은 탐침 도구가 `sys.modules` 에 모듈을 안 올려서

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| 런타임은 어노테이션을 **강제하지 않는다** | **언어 보장** | `typing` 첫머리 |
| ★ `__future__` 아래 `NamedTuple` 이 **`ForwardRef('int')`** 를 담는다 | **CPython 구현** | 실행(3번) — 같은 모드의 dataclass 는 `'int'` |
| `get_type_hints` 가 **`None` 을 `NoneType`** 으로 준다 | **모듈 계약** | `typing` 문서 · 실행(5번) |

* ★★ **가짜 갈림** — 처음 격자는 탐침을 **빈 dict 로 `exec`** 했다. dataclass 가 문자열 어노테이션을 읽을 때
  **`sys.modules.get(cls.__module__).__dict__`** 로 모듈을 찾는데, 그 모듈이 `sys.modules` 에 **없어서** `__future__` 쪽 dataclass 두 칸이 **`AttributeError`** 였다.
  탐침마다 **진짜 모듈을 만들어 올리자** 사라졌고 **8 / 10 이 7 / 10** 이 됐다.
* ★★★ **왜 숫자만 봐서는 안 걸렸나** — `AttributeError` 도 **그럴듯한 갈림**이고, **실제로 갈리는 칸(`Field.type`)이 바로 옆**에 있었다.
  **「`__future__` 가 dataclass 를 깨뜨린다」로 읽힐 뻔했다.** 실제 파일로 던진 2번의 `e40_future.py` 와 대조해서 드러났다 —
  **같은 질문을 도구 없이 한 번 더 물은 것**이 잡았다.

### 10. TS 는 지우고 파이썬은 남긴다 — 둘 다 실행은 안 바뀐다 · 4번 격자 첫 행 · 「쓴다」

**왜 그런가**

* ★★★ [TS 01번](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md)은 방출된 `.js` 에서 `: User`·`interface`·`as User` 가 **한 글자도 안 남는 것**을 보였다.
  파이썬은 **`__annotations__` 로 남긴다**(1번). **실행은 둘 다 안 바뀐다** — TS 는 **지워서**, 파이썬은 **안 읽어서**.
  ★ 그래서 **힌트를 읽어 동작을 바꾸는 코드**(4번)는 **파이썬에만** 있다.
* ★★ [36번](../36-dataclasses/2-summary.md)의 「절반만 예외」 — **4번 격자의 dataclass 행**(어노테이션이 필드를 만든다)이 **예외인 절반**이고,
  [38번](../38-namedtuple-and-typeddict/2-summary.md) 격자의 마지막 행(**`x: int` 에 문자열이 들어간다**)이 **예외가 아닌 절반**이다.
* ★ `singledispatch` 는 **「런타임이 쓴다」** 칸이다 — 어노테이션을 읽어 **어느 함수를 부를지** 정한다.
  「들고만 있다」가 아니다. ★ 다만 **값이 그 타입인지 검사하는 것**이 아니라 **값의 타입으로 갈래를 고르는 것**이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 판 + `annotationlib`·3.14 유무 | `python3 - <e40_version.py` · `python3.11 - <e40_version_py311.py` | 2씩(캡처 + 재대조) | 두 판 모두 없음 · **3.14 는 못 잰 것** |
| 실행은 안 바뀐다 · 평가 시각 | `python3 - <e40_runs.py` | 2 | 세 호출 통과 · **지역 변수 어노테이션 미평가** |
| 기본 판 대 `__future__` 판 | `python3 - <e40_default.py` · `<e40_future.py` | 2씩 | 객체 ↔ 문자열 · `NameError` ↔ 통과 |
| 두 모드 격자 | `python3 - <e40_grid.py` · `python3.11 - <e40_grid_py311.py` | 2씩 | **갈린 칸 7 / 10** · 두 판 동일 |
| 힌트가 바꾸는 자리 | `python3 - <e40_exceptions.py` | 2 | **4 / 6** |
| 되살리기 | `python3 - <e40_hints.py` | 2 | `None` 처리가 둘이 다르다 · `NameError` |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★★ **1번 ③과 3번 격자 전부** | 3.14 는 기본이 지연 평가다(문서) — **평가 횟수·`NameError` 칸이 바뀔 것으로 문서가 적는다** |
| `NamedTuple` 의 `ForwardRef` · dataclass 의 문자열 | 받는 모양은 구현이다 |
| 예외 **문구** | 종류는 계약, 문구는 아니다 |

★ **안 흔들리는 칸** — 격자 칸 · **「갈린 칸 7 / 10」·「4 / 6」** · `<평가됨>` 줄의 유무와 순서 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **3.14**(판 없음) · **타입 검사기**(도구 없음) — 둘 다 못 잰 것 · **속도**(부적용).
