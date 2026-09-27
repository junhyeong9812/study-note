# python/syntax/41-typing-and-generic-syntax — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★★ **3.13 과 타입 검사기 쪽 실측 답은 하나도 없다** — 둘 다 이 머신에 없다([2-summary.md](2-summary.md) 첫 블록).

## 정답

### 1. `isinstance 가 값을 낸 행 5 / 10` — 유니온 넷과 진짜 클래스만

**출력**

```python
# e41_grid.py
import sys
import types
import typing

# 탐침 : (라벨, 소스). 소스는 obj 라는 이름을 남긴다.
PROBES = [
    ("int | str", "obj = int | str"),
    ("Optional[int]", "from typing import Optional\nobj = Optional[int]"),
    ("Union[int, str]", "from typing import Union\nobj = Union[int, str]"),
    ("Literal['a', 'b']", "from typing import Literal\nobj = Literal['a', 'b']"),
    ("list[int]", "obj = list[int]"),
    ("X: TypeAlias = int | str", "from typing import TypeAlias\nX: TypeAlias = int | str\nobj = X"),
    ("type X = int | str", "type X = int | str\nobj = X"),
    ("type Pair[T] = tuple[T, T]", "type Pair[T] = tuple[T, T]\nobj = Pair"),
    ("def f[T](x: T) -> T", "def f[T](x: T) -> T: return x\nobj = f"),
    ("class C[T]: ...", "class C[T]: pass\nobj = C"),
]


def run(src, _seq=[0]):
    # 탐침마다 진짜 모듈을 만들어 sys.modules 에 올린다(40편의 가짜 갈림 교훈)
    _seq[0] += 1
    mod = types.ModuleType("probe%d" % _seq[0])
    sys.modules[mod.__name__] = mod
    try:
        exec(compile(src, "<probe>", "exec"), mod.__dict__)
        return mod.__dict__["obj"], None
    except SyntaxError as exc:
        return None, "SyntaxError"
    finally:
        del sys.modules[mod.__name__]


def cell(fn):
    try:
        return repr(fn())
    except Exception as exc:
        return type(exc).__name__


print("판 :", sys.version_info[:2])
print("%-27s | %-20s | %-9s | %-16s | %-11s | %s" % (
    "탐침", "type(obj)", "origin", "get_args", "type_params", "isinstance(1, obj)"))
ok = 0
for label, src in PROBES:
    obj, err = run(src)
    if err:
        print("%-27s | %s" % (label, err))
        continue
    origin = typing.get_origin(obj)
    inst = cell(lambda: isinstance(1, obj))
    ok += inst in ("True", "False")
    print("%-27s | %-20s | %-9s | %-16s | %-11s | %s" % (
        label,
        type(obj).__name__,
        getattr(origin, "__name__", None) if origin is not None else None,
        cell(lambda: tuple(getattr(a, "__name__", a) for a in typing.get_args(obj))),
        cell(lambda: len(obj.__type_params__)),
        inst))
print("isinstance 가 값을 낸 행 %d / %d" % (ok, len(PROBES)))
```

```text
===== python3 - <e41_grid.py =====
판 : (3, 12)
탐침                          | type(obj)            | origin    | get_args         | type_params | isinstance(1, obj)
int | str                   | UnionType            | UnionType | ('int', 'str')   | AttributeError | True
Optional[int]               | _UnionGenericAlias   | Union     | ('int', 'NoneType') | AttributeError | True
Union[int, str]             | _UnionGenericAlias   | Union     | ('int', 'str')   | AttributeError | True
Literal['a', 'b']           | _LiteralGenericAlias | Literal   | ('a', 'b')       | AttributeError | TypeError
list[int]                   | GenericAlias         | list      | ('int',)         | 0           | TypeError
X: TypeAlias = int | str    | UnionType            | UnionType | ('int', 'str')   | AttributeError | True
type X = int | str          | TypeAliasType        | None      | ()               | 0           | TypeError
type Pair[T] = tuple[T, T]  | TypeAliasType        | None      | ()               | 1           | TypeError
def f[T](x: T) -> T         | function             | None      | ()               | 1           | TypeError
class C[T]: ...             | type                 | None      | ()               | 1           | False
isinstance 가 값을 낸 행 5 / 10
(exit 0)
```

**왜 그런가**

* ★★★ **`isinstance` 가 답한 다섯** — `int | str`·`Optional[int]`·`Union[int, str]`·`X: TypeAlias = int | str`(→ `True`), `class C[T]`(→ `False`, 진짜 클래스다).
  나머지 다섯은 **`TypeError`** — `Literal`·`list[int]`·`type` 별칭 둘·함수.
* ★★★ **`TypeAlias` 행이 `int | str` 행과 한 칸도 다르지 않다** — `TypeAlias` 는 대입문의 어노테이션이라 **값만 남는다.**
* ★★ **`type` 문 행은 `TypeAliasType`** — `get_args` 가 `()` 이고 `isinstance` 가 `TypeError` 다. 유니온이 **봉투 안**에 있다.
* ★★ `__type_params__` — `Pair`·`f`·`C` 가 **`1`**(`(T,)`), `type X` 와 **`list[int]` 가 `0`**, 유니온·`Literal` 은 `AttributeError`.
  ★ `list[int]` 의 `0` 은 3.12 에서 **모든 클래스가 `__type_params__ = ()` 를 얻은** 결과다(3번에서 갈린다).
* ★ `Optional[int]` 의 `type` 은 **`_UnionGenericAlias`**, `int | str` 은 **`UnionType`** — 다른 객체다(5번).

### 2. 정의는 통과 · 읽을 때 `NameError` · `TypeAlias` 는 대입 자리에서 `NameError` · 평가는 `0 → 1`(두 번 읽어도) · 경계도 읽을 때

**출력**

```python
# e41_lazy.py
calls = []


def tag(label):
    calls.append(label)
    print("  <평가됨:", label + ">")
    return int


print("[1] type 문 — 정의 안 된 이름을 값에 쓴다")
type Later = list[Undefined]
print("  type 문 다음 줄 :", Later)
try:
    Later.__value__
except NameError as exc:
    print("  Later.__value__ ->", type(exc).__name__ + ":", exc)
Undefined = str
print("  이름을 만든 뒤 :", Later.__value__)

print("[2] TypeAlias — 같은 값")
try:
    from typing import TypeAlias
    Eager: TypeAlias = list[Missing]
    print("  대입 다음 줄")
except NameError as exc:
    print("  대입 ->", type(exc).__name__ + ":", exc)

print("[3] 평가는 언제 · 몇 번")
print("  type 문 직전")
type Tagged = tag("type 문의 값")
print("  type 문 직후 · 평가 횟수", len(calls))
Tagged.__value__
Tagged.__value__
print("  __value__ 두 번 읽은 뒤 · 평가 횟수", len(calls))

print("[4] 서로를 가리키는 두 별칭")
type Expr = int | Pair
type Pair = tuple[Expr, Expr]
print("  Expr.__value__ :", Expr.__value__)
print("  Pair.__value__ :", Pair.__value__)

print("[5] 타입 매개변수의 경계")
def pick[T: tag("T 의 경계")](x: T) -> T:
    return x
print("  def 직후 · 평가 횟수", len(calls))
T = pick.__type_params__[0]
print("  T.__bound__ :", T.__bound__, "· 평가 횟수", len(calls))
```

```text
===== python3 - <e41_lazy.py =====
[1] type 문 — 정의 안 된 이름을 값에 쓴다
  type 문 다음 줄 : Later
  Later.__value__ -> NameError: name 'Undefined' is not defined
  이름을 만든 뒤 : list[str]
[2] TypeAlias — 같은 값
  대입 -> NameError: name 'Missing' is not defined
[3] 평가는 언제 · 몇 번
  type 문 직전
  type 문 직후 · 평가 횟수 0
  <평가됨: type 문의 값>
  __value__ 두 번 읽은 뒤 · 평가 횟수 1
[4] 서로를 가리키는 두 별칭
  Expr.__value__ : int | Pair
  Pair.__value__ : tuple[Expr, Expr]
[5] 타입 매개변수의 경계
  def 직후 · 평가 횟수 1
  <평가됨: T 의 경계>
  T.__bound__ : <class 'int'> · 평가 횟수 2
(exit 0)
```

**왜 그런가**

* ★★★ **`[1]`** — `type` 문은 값 식을 **만들 때 평가하지 않는다.** `Later.__value__` 를 읽는 순간 평가되어 `NameError`, 이름을 만든 뒤 다시 읽으면 `list[str]`.
* ★★★ **`[2]`** — `TypeAlias` 는 **보통 대입문**이라 오른쪽이 곧바로 평가된다 → `NameError: name 'Missing' is not defined`.
* ★★ **`[3]`** — `type 문 직전`·`직후` 사이에 `<평가됨>` 이 **없다**(`0`). `__value__` 를 두 번 읽었는데 `<평가됨>` 은 **한 줄**, 횟수 `1`.
  ★ 「늦게」는 문서의 말, 「**한 번만**」은 **이 판의 관찰**이다.
* ★★ **`[4]`** — 서로를 가리키는 두 별칭이 **둘 다 선언되고** `__value__` 도 나온다.
* ★★ **`[5]`** — 경계 `tag("T 의 경계")` 는 `def` 때 안 돌고(`1` 그대로) **`T.__bound__` 를 읽을 때** 돈다(`2`).

### 3. `판이 갈린 행 5 / 10` — PEP 695 네 행과 `list[int]`

**출력**

```python
# e41_versions.py
import subprocess

# 같은 격자 소스를 두 판에 먹여 행마다 견준다
src = open("e41_grid.py").read()
out = {}
for exe in ["python3.11", "python3"]:
    r = subprocess.run([exe, "-"], input=src, capture_output=True, text=True)
    out[exe] = r.stdout.splitlines()[2:-1]   # 판 줄 · 머리 줄 · 마지막 줄을 뺀 탐침 행
split = 0
for a, b in zip(out["python3.11"], out["python3"]):
    label = a[:27].strip()   # 격자의 첫 칸 폭이 27 이다
    same = a == b
    split += not same
    print("%-27s : %s" % (label, "같다" if same else "갈렸다"))
print("판이 갈린 행 %d / %d" % (split, len(out["python3"])))
```

```text
===== python3 - <e41_versions.py =====
int | str                   : 같다
Optional[int]               : 같다
Union[int, str]             : 같다
Literal['a', 'b']           : 같다
list[int]                   : 갈렸다
X: TypeAlias = int | str    : 같다
type X = int | str          : 갈렸다
type Pair[T] = tuple[T, T]  : 갈렸다
def f[T](x: T) -> T         : 갈렸다
class C[T]: ...             : 갈렸다
판이 갈린 행 5 / 10
(exit 0)
```

3.11 쪽 격자 전문 —

```text
===== python3.11 - <e41_grid_py311.py =====
판 : (3, 11)
탐침                          | type(obj)            | origin    | get_args         | type_params | isinstance(1, obj)
int | str                   | UnionType            | UnionType | ('int', 'str')   | AttributeError | True
Optional[int]               | _UnionGenericAlias   | Union     | ('int', 'NoneType') | AttributeError | True
Union[int, str]             | _UnionGenericAlias   | Union     | ('int', 'str')   | AttributeError | True
Literal['a', 'b']           | _LiteralGenericAlias | Literal   | ('a', 'b')       | AttributeError | TypeError
list[int]                   | GenericAlias         | list      | ('int',)         | AttributeError | TypeError
X: TypeAlias = int | str    | UnionType            | UnionType | ('int', 'str')   | AttributeError | True
type X = int | str          | SyntaxError
type Pair[T] = tuple[T, T]  | SyntaxError
def f[T](x: T) -> T         | SyntaxError
class C[T]: ...             | SyntaxError
isinstance 가 값을 낸 행 4 / 10
(exit 0)
```

**왜 그런가**

* ★★★ **PEP 695 네 행**(`type X`·`type Pair[T]`·`def f[T]`·`class C[T]`)은 3.11 파서가 **모르는 문법**이라 `SyntaxError` 다.
* ★★ **`list[int]` 는 문법이 같은데 갈렸다** — `type_params` 칸 하나가 3.11 `AttributeError`, 3.12 `0`. **판이 객체의 속성을 바꾼다.**
* ★ 나머지 다섯(유니온 셋·`Literal`·`TypeAlias`)은 **한 글자도 같다** — 3.10 부터 있던 것들이다.
* ★ 3.11 의 마지막 줄은 `4 / 10` — `class C[T]` 가 만들어지지 않아 한 행이 빠졌다.

### 4. `"x"` 도 들어간다 · 값 목록은 `('r', 'w')` · `match` 가 가른다 · `Literal[1] != Literal[True]`

**출력**

```python
# e41_literal.py
from typing import Literal, get_args

type Mode = Literal["r", "w"]


def open_mode(mode: Mode) -> str:
    return "mode=" + mode


print("[1]", open_mode("r"), "|", open_mode("x"))

print("[2] 런타임에 남은 값들")
allowed = get_args(Mode.__value__)
print("  get_args(Mode.__value__) :", allowed)
print("  'x' in allowed           :", "x" in allowed)


def describe(mode: str) -> str:
    match mode:
        case "r" | "w":
            return "알려진 " + mode
        case other:
            return "모름 " + other


print("[3]", describe("r"), "|", describe("x"))
print("[4] Literal[1] 과 Literal[True]")
print("  Literal[1] == Literal[True] :", Literal[1] == Literal[True])
print("  1 == True                   :", 1 == True)
```

```text
===== python3 - <e41_literal.py =====
[1] mode=r | mode=x
[2] 런타임에 남은 값들
  get_args(Mode.__value__) : ('r', 'w')
  'x' in allowed           : False
[3] 알려진 r | 모름 x
[4] Literal[1] 과 Literal[True]
  Literal[1] == Literal[True] : False
  1 == True                   : True
(exit 0)
```

**왜 그런가**

* ★★★ **`[1]`** — `Literal` 은 **검사하지 않는다.** `open_mode("x")` 가 `mode=x`.
* ★★ **`[2]`** — `Mode` 가 `type` 별칭이라 **`Mode.__value__`** 로 봉투를 연 뒤에야 `get_args` 가 `('r', 'w')` 를 준다. 그 튜플의 `in` 이 **내가 쓰는 검사**다.
* ★★ **`[3]`** — 리터럴 패턴 `"r" | "w"` 가 `r` 을, 캡처 패턴 `other` 가 `x` 를 받았다.
* ★ **`[4]`** — `Literal` 은 **타입까지** 비교한다. `1 == True` 와 반대다.

### 5. `==` 는 참인데 `type` 은 다르다 · `int | 'Node'` 만 `TypeError`

**출력**

```python
# e41_pitfalls.py
from typing import Optional, Union

print("[1] 두 표기를 == 로")
print("  Optional[int] == (int | None)   :", Optional[int] == (int | None))
print("  Union[int, str] == (int | str)  :", Union[int, str] == (int | str))
print("  type 둘                          :", type(Optional[int]).__name__, "/", type(int | None).__name__)

print("[2] 문자열 전방 참조를 섞으면")
for label, make in [
    ("Optional['Node']", lambda: Optional["Node"]),
    ("Union[int, 'Node']", lambda: Union[int, "Node"]),
    ("int | 'Node'", lambda: int | "Node"),
    ("'int | Node'", lambda: "int | Node"),
]:
    try:
        print("  %-20s -> %r" % (label, make()))
    except TypeError as exc:
        print("  %-20s -> %s: %s" % (label, type(exc).__name__, exc))
```

```text
===== python3 - <e41_pitfalls.py =====
[1] 두 표기를 == 로
  Optional[int] == (int | None)   : True
  Union[int, str] == (int | str)  : True
  type 둘                          : _UnionGenericAlias / UnionType
[2] 문자열 전방 참조를 섞으면
  Optional['Node']     -> typing.Optional[ForwardRef('Node')]
  Union[int, 'Node']   -> typing.Union[int, ForwardRef('Node')]
  int | 'Node'         -> TypeError: unsupported operand type(s) for |: 'type' and 'str'
  'int | Node'         -> 'int | Node'
(exit 0)
```

**왜 그런가**

* ★★ **`[1]`** — 두 표기는 **같다고 답하지만 다른 클래스**다. `type` 으로 가르면 한쪽을 놓친다.
* ★★★ **`[2]`** — `|` 는 **실행되는 연산자**다. `type` 과 `str` 사이에 정의가 없어 `TypeError`.
  `Optional['Node']`·`Union[int, 'Node']` 는 문자열을 **`ForwardRef` 로 싸 준다.** 식 전체를 문자열로 쓰면(`'int | Node'`) **그냥 문자열**이다.
* ★ 3.11 도 한 글자도 같았다([2-summary.md](2-summary.md) 동작 5).

### 6. 검사 없음 · `(T,)` 와 `Generic` 과 `__orig_class__` · 함수마다 다른 `T` · 전역에 `T` 없음

**출력**

```python
# e41_generic.py
def first[T](xs: list[T]) -> T:
    return xs[0]


class Box[T]:
    def __init__(self, item: T) -> None:
        self.item = item


print("[1] 부르면")
print("  first([1, 'a'])  :", first([1, "a"]))
print("  first('문자열')   :", first("문자열"))
print("  Box[int]('문자열').item :", Box[int]("문자열").item)

print("[2] 남는 것")
tp = first.__type_params__[0]
print("  first.__type_params__ :", first.__type_params__, type(tp).__name__)
print("  first.__annotations__ :", first.__annotations__)
print("  Box.__type_params__   :", Box.__type_params__)
print("  Box.__mro__           :", [c.__name__ for c in Box.__mro__])
print("  Box[int]              :", Box[int], type(Box[int]).__name__)
b = Box[int](1)
print("  b.__orig_class__      :", b.__orig_class__)

print("[3] 두 함수의 T")
def second[T](xs: list[T]) -> T:
    return xs[1]
print("  first 의 T is second 의 T :", first.__type_params__[0] is second.__type_params__[0])

print("[4] 모듈 전역의 이름 T")
print("  'T' in globals() :", "T" in globals())

print("[5] 경계와 제약")
def clamp[N: (int, float)](x: N) -> N:
    return x
print("  제약 :", clamp.__type_params__[0].__constraints__, "| clamp('s') :", clamp("s"))
```

```text
===== python3 - <e41_generic.py =====
[1] 부르면
  first([1, 'a'])  : 1
  first('문자열')   : 문
  Box[int]('문자열').item : 문자열
[2] 남는 것
  first.__type_params__ : (T,) TypeVar
  first.__annotations__ : {'xs': list[T], 'return': T}
  Box.__type_params__   : (T,)
  Box.__mro__           : ['Box', 'Generic', 'object']
  Box[int]              : __main__.Box[int] _GenericAlias
  b.__orig_class__      : __main__.Box[int]
[3] 두 함수의 T
  first 의 T is second 의 T : False
[4] 모듈 전역의 이름 T
  'T' in globals() : False
[5] 경계와 제약
  제약 : (<class 'int'>, <class 'float'>) | clamp('s') : s
(exit 0)
```

**왜 그런가**

* ★★★ **`[1]`** — `T` 는 **검사하지 않는다.** `first('문자열')` 은 `'문'`, `Box[int]('문자열').item` 은 문자열 그대로.
* ★★ **`[2]`** — `__type_params__` 가 `(T,)`(`TypeVar`) · `__annotations__` 에 `list[T]`·`T` · **`Box.__mro__` 에 `Generic`** · `Box[int]` 는 `_GenericAlias` ·
  인스턴스의 **`__orig_class__`** 가 `Box[int]`.
* ★★ **`[3]`·`[4]`** — `[T]` 는 **함수마다 새 `TypeVar`** 를 만들고 **모듈 전역에 이름을 남기지 않는다.**
* ★ **`[5]`** — 제약 `(int, float)` 는 **`__constraints__` 에 남지만** `clamp('s')` 는 통과.

### 7. 원소를 안 보기 때문 — `get_origin`/`get_args` 로 풀어서 직접 돈다 · 실행 중 예외라 캐럿이 없다 · 같은 흐름이어야 순서가 고정된다

**왜 그런가**

* ★★ `isinstance` 는 **객체의 클래스**만 본다. `list[int]` 의 `int` 는 **원소마다** 봐야 하는 조건이라 `isinstance` 한 번으로는 답할 수 없다 —
  그래서 거부한다(`isinstance() argument 2 cannot be a parameterized generic`).
  실행 중에 원소까지 보려면 `get_origin(tp)` 로 `list` 를, `get_args(tp)` 로 `(int,)` 를 꺼내 **직접 돈다**(또는 검증 라이브러리).
* ★ 트레이스백에 소스 줄·캐럿이 없는 것은 **`<stdin>` 으로 던진 실행 중 예외**이기 때문이다 — `SyntaxError` 만 캐럿이 있다(3번의 `e41_*_py311` 블록들).
* ★★ 앞의 `True` 두 줄을 **`sys.stderr`** 로 찍은 이유 — stdout 은 파이프에서 **블록 버퍼**라 트레이스백(stderr)과 **순서가 받는 쪽에 달린다.** 같은 흐름으로 보내면 순서가 고정된다.

### 8. `expected '('`·캐럿 위치까지 한 글자도 같다 — 백포트는 「그 패키지의 객체」까지만 말한다

**왜 그런가**

* ★★★ 3.12 의 `[T = int]` 와 3.11 의 `[T]` 가 **같은 문구 `SyntaxError: expected '('`**, 캐럿이 **같은 열(여는 대괄호)** 이다.
  **3.12 파서는 기본값 붙은 대괄호를 통째로 모른다** — 한 판 앞의 파서가 `[T]` 를 통째로 모르던 것과 같은 모양이다.
* ★★ 백포트 블록이 **말해 주는 것** — `typing_extensions` 4.10.0 의 `TypeIs[str]` 로 표시한 함수가 **그냥 `bool` 을 돌려주고**, 몸통이 거짓이어도 **통과**하며,
  `TypeVar(default=int)` 가 `__default__` 를 들고 있다는 것.
* ★★★ **못 말하는 것** — **3.13 표준 `typing` 의 객체가 그렇게 동작하는지.** 첫 줄 `te.TypeIs is typing 의 것 : False` 는
  3.12 에 `typing.TypeIs` 가 **없어서**(`None`) 백포트 객체와 다르다는 뜻이다 — **「다른 코드에 물었다」를 블록이 스스로 적는다.** 그래서 이 블록은 「못 잰 것」을 대신하지 않고 **제5의 상태(창을 바꿔 물었다)** 로 적었다.

### 9. 보장 · 구현 · 보장 · 관찰 — 검사기는 이 머신에 없다

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| `type` 문의 값은 **늦게 평가된다** | **언어 보장** | 실행 모델 — Lazy evaluation |
| `__value__` 는 **두 번 읽어도 한 번** 평가 | **CPython 구현** | 실행(2번 `[3]`) — 문서는 「늦게」까지만 말한다 |
| `isinstance(x, T)` 는 **`TypeError`** | **언어 보장** | `typing` 문서 `TypeVar` 절 |
| `TypeVar(default=)` 의 **오류 문구** | **이 판의 관찰** | 3.11(`TypeVar.__init__()`)과 3.12(`typevar()`)가 이미 다르다 |

* ★★★ 첫 블록이 `mypy`·`pyright` 를 물어 **`None`**, [35번](../35-abc-and-protocol/2-summary.md)·[38번](../38-namedtuple-and-typeddict/2-summary.md)이 다섯 도구를 물어 **전부 `None`** 이었다.
  **검사기가 `Literal` 에서 `"x"` 를 잡는다**는 문장은 이 머신에서 **확인할 수단이 없는 주장**이라 쓰지 않았다.

### 10. `first('문자열')`·`open_mode("x")`·`clamp('s')` — 믿는 쪽은 `tsc` 와 (파이썬에서는) 아무도 — `case other:`

**왜 그런가**

* ★★ [40번](../40-type-hints-at-runtime/2-summary.md)의 결론이 **다시 확인되는 줄** — 6번 `[1]` 의 `first('문자열')`·`Box[int]('문자열')`, 4번 `[1]` 의 `open_mode("x")`, 6번 `[5]` 의 `clamp('s')`. 전부 **그냥 돈다.**
* ★★ [TS 13번](../../../ts/syntax/13-type-guards-and-predicates/2-summary.md)에서 거짓 술어를 믿는 것은 **컴파일러 `tsc`** 다 — 믿고 좁힌 뒤 **실행 중에 터진다.**
  파이썬 백포트 블록 `[3]` 에서는 **믿을 주체조차 없다** — 런타임은 좁히지 않고 `True` 를 돌려줄 뿐이다. 검사기가 믿는지는 **못 잰 것**이다.
* ★ 캡처 패턴은 4번 소스의 **`case other:`** 줄이다. 그 줄이 없으면 [39번](../39-match-statement/2-summary.md) 동작 7 이 보인 대로 **`match` 는 빠진 경우를 알려 주지 않고** 함수가 끝까지 내려가 **`None`** 을 돌려준다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 판 + `TypeIs`·3.13·검사기 유무 | `python3 - <e41_version.py` · `python3.11 - <e41_version_py311.py` | 3씩(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | 두 판 모두 없음 · **3.13·검사기는 못 잰 것** |
| 런타임에 남는 것 격자 | `python3 - <e41_grid.py` · `python3.11 - <e41_grid_py311.py` | 3씩 | **5 / 10** · 3.11 은 4 / 10 |
| 판 격자 | `python3 - <e41_versions.py` | 3 | **판이 갈린 행 5 / 10** |
| 늦은 평가 | `python3 - <e41_lazy.py` | 3 | 정의 통과 · 읽을 때 `NameError` · 평가 1회 |
| `SyntaxError` 셋 | `python3.11 - <e41_stmt_py311.py` · `<e41_generic_py311.py` · `python3 - <e41_default.py` | 3씩 | 3.12 의 `[T = int]` 가 3.11 의 `[T]` 와 같은 오류 |
| `isinstance` 전문 | `python3 - <e41_isinstance.py` | 3 | `TypeError` |
| 리터럴·두 표기·제네릭 | `python3 - <e41_literal.py` · `<e41_pitfalls.py` · `<e41_generic.py` | 3씩 | 검사 없음 |
| 백포트 | `python3 - <e41_backport.py` | 3 | `typing_extensions` 4.10.0 — **3.13 이 아니다** |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★★ 첫 블록 · 판 격자 · `e41_default.py` | 3.13 에서 `TypeIs`·기본값이 들어온다(문서) |
| `__value__` 1회 평가 · 모든 클래스의 `__type_params__` | 구현이다 |
| 예외 **문구** | 종류는 계약, 문구는 아니다 |

★ **안 흔들리는 칸** — 격자 칸 · **「5 / 10」 둘** · `<평가됨>` 줄의 유무와 순서 · `SyntaxError` 의 줄·캐럿 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **3.13**(판 없음) · **타입 검사기**(도구 없음) — 둘 다 못 잰 것 · **속도**(부적용).
