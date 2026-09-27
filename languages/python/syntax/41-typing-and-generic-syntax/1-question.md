# python/syntax/41-typing-and-generic-syntax — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **격자의 칸을 하나씩** 채우고 마지막 줄의 숫자까지 적는다.
> ★★★ 2번은 **`<평가됨: …>` 줄이 어디에 몇 줄 찍히나**까지 적어야 맞은 것이다 — 순서가 답이다.
> ★★ 이 주제는 **「타입 검사기라면」·「3.13 이라면」을 예측형으로 묻지 않는다** — 둘 다 이 머신에 없어 정답을 확인할 수 없다.
>
> 실행 환경: `python3` **3.12.3** · Linux(3번은 `python3.11` 3.11.15 도 함께). 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [40](../40-type-hints-at-runtime/1-question.md)(힌트의 런타임 의미) · [39](../39-match-statement/1-question.md)(`match`) ·
> [35](../35-abc-and-protocol/1-question.md)(`Protocol`·검사기 부재).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 형태 열 개 × 다섯 창 (예측)

```text
각 행의 다섯 칸(type(obj) 의 이름 · origin · get_args · type_params · isinstance(1, obj))을 적는다.
예외가 나는 칸은 예외 종류만 적는다. 마지막 줄의 N / M 도 적는다.
```

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

### 2. ★★★ `type` 문과 `TypeAlias` 에 같은 값 (예측)

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

### 3. ★★★ 같은 격자를 두 판에 (예측)

```text
1번의 격자 소스(e41_grid.py)를 python3.11 과 python3 에 각각 먹인다.
행마다 "같다 / 갈렸다" 를 적고, 갈린 행은 왜 갈렸는지도 한 줄씩 적는다.
```

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

### 4. ★★ 리터럴과 `match` (예측)

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

### 5. ★★ 두 표기와 문자열 (예측)

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

### 6. ★★ 제네릭 함수와 클래스가 들고 있는 것 (예측)

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

### 7. ★★ `isinstance` 의 두 번째 인자 (왜)

* 1번 격자의 `list[int]` 행에서 `isinstance(1, obj)` 칸이 그렇게 나온 이유는? `list` 의 **원소까지** 실행 중에 검사하려면 무엇을 쓰나?
* `isinstance(1, list[int])` 를 **`<stdin>` 으로 던져 예외를 끝까지 흘리면** 트레이스백에 소스 줄과 캐럿이 나오나? 그 앞의 `print` 는 **어느 흐름으로** 찍어야 순서가 고정되나?

### 8. ★★★ 3.13 기능은 어디까지 말할 수 있나 (경계)

* 3.12 에 `def first[T = int](...)` 를 던지면 무엇이 나오나 — 3.11 에 `def first[T](...)` 를 던진 출력과 **견주어** 적어라.
* `typing_extensions` 백포트로 물은 블록은 **무엇을 말해 주고 무엇을 못 말하나**? 그 블록의 첫 줄이 어떻게 그 한계를 스스로 드러내나?

### 9. 층 가르기 (경계)

* 「`type` 문의 값은 늦게 평가된다」·「`__value__` 를 여러 번 읽을 때의 평가 횟수」·「`isinstance(x, T)` 는 `TypeError`」·「`TypeVar(default=)` 의 오류 문구」 —
  각각 **언어 보장 · CPython 구현 · 이 판의 관찰** 중 어디인가?
* ★ 이 문서가 검사기에 대해 **한 줄도 주장하지 않는** 이유는?

### 10. 이웃 주제와의 경계 (연결)

* ★ [40번](../40-type-hints-at-runtime/2-summary.md)의 「힌트는 실행을 안 바꾼다」는 이 주제의 **어느 블록 어느 줄**에서 다시 확인되나(둘 이상)?
* ★ [TS 13번](../../../ts/syntax/13-type-guards-and-predicates/2-summary.md)의 「술어가 거짓말을 해도 컴파일러는 믿는다」와 이 주제의 백포트 블록 `[3]` — **믿는 쪽이 각각 누구**인가?
* ★ [39번](../39-match-statement/2-summary.md)의 캡처 패턴은 4번 소스의 **어느 줄**에 있고, 그 줄이 없으면 `describe("x")` 는 무엇을 돌려주나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
