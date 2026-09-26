# python/syntax/41-typing-and-generic-syntax — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`typing`(3.12)](https://docs.python.org/3.12/library/typing.html) — `TypeAlias` 의 *"Deprecated since version 3.12 … in favor of the `type` statement"* 문단 ·
>   `TypeAliasType.__value__` 가 *"lazily evaluated"* 라는 문단 · `Literal` 의 *"At runtime, an arbitrary value is allowed as type argument"* 문단 ·
>   `TypeVar` 절의 *"At runtime, `isinstance(x, T)` will raise `TypeError`"*
> - [실행 모델 — Lazy evaluation(3.12)](https://docs.python.org/3.12/reference/executionmodel.html#lazy-evaluation) —
>   *"The values of type aliases created through the `type` statement are lazily evaluated. The same applies to the bounds and constraints of type variables"*
> - [`typing`(3.13) — `TypeIs`](https://docs.python.org/3.13/library/typing.html#typing.TypeIs) · [What's New In Python 3.13](https://docs.python.org/3.13/whatsnew/3.13.html) —
>   *"PEP 696: Type parameters … now support defaults"* · *"PEP 742: `typing.TypeIs` provides more intuitive type narrowing behavior"*.
>   ★ **이 판은 이 머신에 없다 — 문서로만 적는다.**
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 **둘** — `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 넷을 더 던졌다(파일 이름에 `_py311` 이 붙은 것).\
> ★★★ **3.13 은 이 머신에 없다** — 첫 블록이 `PATH` 에서 `python3.13` 을 찾아 **`None`** 을 받았고, `hasattr(typing, "TypeIs")` 가 **`False`** 였다.
> 그래서 `TypeIs` 와 타입 매개변수 기본값의 **3.13 동작은 못 잰 것**이다.\
> ★★★ **타입 검사기도 이 머신에 없다** — 첫 블록이 `mypy`·`pyright` 를 물어 **`None`**, [35번](../35-abc-and-protocol/2-summary.md)·[38번](../38-namedtuple-and-typeddict/2-summary.md)이 다섯 도구를 물어 **전부 `None`** 이었다.
> 이 주제의 대부분은 **「검사기만 보는 것」** 이다 — 이 문서는 **런타임에 남는 것**만 재고, 검사기가 무엇을 잡는지는 **한 줄도 주장하지 않는다.**\
> ★ 던지는 형태는 `python3 - <파일` 하나로 고정했다. 예외를 끝까지 흘린 블록은 넷뿐이고(`SyntaxError` 셋 · `TypeError` 하나), 나머지는 `except` 로 받아 **타입과 메시지만** 찍었다.\
> **버전** — `X | Y` 는 **3.10**(PEP 604), `Literal` 은 **3.8**(PEP 586), `TypeAlias` 는 **3.10**(PEP 613, 3.12 에서 폐기 예고),
> `type` 문과 `def f[T]`·`class C[T]` 는 **3.12**(PEP 695), 타입 매개변수 기본값은 **3.13**(PEP 696), `TypeIs` 는 **3.13**(PEP 742).\
> ★ **구현 대 언어 보장 한 줄** — **`type` 문의 값이 늦게 평가된다 · `isinstance(x, T)` 가 `TypeError` 다**까지가 문서가 정한 것이고,
> **`__value__` 가 한 번만 평가되고 기억된다 · 3.12 의 모든 클래스에 `__type_params__` 가 있다**는 이 판(CPython 3.12.3)에서 본 것이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 판이 오르면 예외 **문구**(`TypeVar(default=)` 의 문구가 3.11 과 3.12 에서 **이미 다르다**) | ★★ 격자의 칸 · 마지막 줄 **「… N / M」** |
> | ★ 판이 오르면 **3.13 칸 전부**(못 잰 것) | `<평가됨: …>` 줄이 **찍히느냐 안 찍히느냐**와 그 **순서** |
> | — (주소·시간을 한 곳도 안 찍었다) | `SyntaxError` 의 줄·캐럿 위치 |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대 경로도 한 곳도 안 찍힌다.** 재대조 전부 동일.\
> **선행** — [40-type-hints-at-runtime](../40-type-hints-at-runtime/2-summary.md)(★★★ **「힌트는 실행을 안 바꾸고 `__annotations__` 에 남는다」 — 이 주제는 그 위에 선다**) ·
> [35-abc-and-protocol](../35-abc-and-protocol/2-summary.md)(★ `Protocol` 과 검사기 부재 판정) ·
> [39-match-statement](../39-match-statement/2-summary.md)(★ `Literal` 값을 런타임에 가르는 쪽).

## 한눈에 — 쉽게 말하면

**`typing` 의 문법들은 「설계도에 쓰는 기호」다.** 시공 현장(인터프리터)은 기호를 **해석하지 않고** 건물을 짓는다.
그런데 기호 중 **어떤 것은 현장에 표지판으로 남고**(런타임 객체), 어떤 것은 **설계도에만 있다**(검사기만 읽는다).

* 기호를 쓰는 곳 — `int | str` · `Literal["r", "w"]` · `type Pair[T] = tuple[T, T]` · `def first[T](xs: list[T]) -> T`.
* 현장에 남는 표지판 — `UnionType`·`TypeAliasType`·`TypeVar` 객체, 그리고 `__type_params__`·`__value__` 속성.
* 표지판을 **검사에 쓸 수 있는** 것은 일부뿐 — `isinstance(1, int | str)` 은 되고 `isinstance(1, list[int])` 는 **`TypeError`**.

```text
   소스                               런타임에 남는 것                    isinstance(1, 그것)
   int | str                   ->    UnionType 객체                  ->  된다 (True)
   Literal["a", "b"]           ->    _LiteralGenericAlias            ->  TypeError
   list[int]                   ->    GenericAlias                    ->  TypeError
   type X = int | str  (3.12)  ->    TypeAliasType  (값은 아직 안 봄)   ->  TypeError
   def f[T](x: T)      (3.12)  ->    f.__type_params__ == (T,)       ->  (함수라 TypeError)
   X: TypeAlias = int | str    ->    ★ 그냥 UnionType — 별칭이라는 흔적이 없다

   ★ 전부 "실행을 바꾸지 않는다" 는 40편의 결론 위에 있다
   ★ 검사기가 이 기호로 무엇을 잡나 — 이 머신에 검사기가 없어 못 잰 것
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 설계도의 기호 | `typing` 의 형태들(유니온·리터럴·제네릭) | 소스 |
| 기호를 해석하지 않고 짓는 현장 | 인터프리터 | `first("문자열")` 이 그냥 돈다 |
| 현장에 남은 표지판 | 런타임 객체(`UnionType`·`TypeAliasType`·`TypeVar`) | `type(obj)` · `get_args` · `__type_params__` |
| ★ 표지판을 **출입 검사**에 쓰기 | `isinstance(x, 그 타입)` | 되는 것은 유니온과 진짜 클래스뿐 |
| ★ **나중에 펼쳐 보는** 봉투 | `type X = …` 의 값 | `X.__value__` 를 읽을 때 평가된다 |
| 설계도만 읽는 감리 | 타입 검사기 | ★ **이 머신에 없다**(못 잰 것) |
| 다음 판 설계도의 새 기호 | `TypeIs` · `[T = int]` (3.13) | ★ **이 머신에 없다**(문서만) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`mode: Literal["r", "w"]` 라고 썼는데 `"x"` 가 들어와 아래에서 터진다**」와
「**`isinstance(v, list[int])` 로 검사하려다 `TypeError` 가 난다**」가 그것이다.\
앞엣것은 **기호를 감리로 착각한 것**이고, 뒤엣것은 **설계도에만 있는 기호를 출입 검사에 쓰려 한 것**이다.

> **유니온(union)** — 「이 타입 **또는** 저 타입」. `int | str` 이나 `Union[int, str]` 로 쓴다.\
> 예: `int | None` 은 「정수 또는 `None`」.

> **제네릭(generic)** — 타입을 **매개변수로 받는** 함수·클래스. 매개변수를 **타입 변수**(`T`)라 한다.\
> 예: `def first[T](xs: list[T]) -> T` 는 「`T` 의 리스트를 받아 `T` 를 돌려준다」.

> **타입 별칭(type alias)** — 타입 식에 **이름을 붙인 것**.\
> 예: `type Pair = tuple[int, int]` 뒤로는 `Pair` 가 그 식을 가리킨다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 「런타임에 무엇이 남나」 격자 창이다.** 형태 열 개를 만들어 **`type(obj)`·`get_origin`·`get_args`·`__type_params__`·`isinstance(1, obj)`** 다섯 창으로 묻고,
**같은 격자를 3.11 에 한 번 더** 먹여 **판이 갈린 행을 스크립트가 센다.**

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **「런타임에 무엇이 남나」 격자** | 형태마다 **어떤 객체가 남고 무엇을 물을 수 있나** | 검사기가 그 형태를 어떻게 읽나 |
| ② ★★★ **판 격자**(3.11 대 3.12) | 같은 소스가 **판에 따라 어디서 갈리나** | 3.13 |
| ③ ★★ **평가 시각 창**(부르면 한 줄 찍는 함수) | `type` 문의 값·경계가 **언제·몇 번** 평가되나 | — |
| ④ ★★ **`SyntaxError` 전문** | 그 판의 파서가 **문법을 아는가** | — |
| ★ **제5의 상태** — 3.13 기능을 **백포트로** 물었다 | `typing_extensions` 의 `TypeIs`·`TypeVar(default=)` 가 **런타임에 무엇을 남기나** | ★ **3.13 표준 `typing` 의 동작** — 백포트는 다른 코드다 |
| ★ **못 잰 것** — 3.13 기능 · 타입 검사기의 판정 | — | ★★★ `python3.13`·`mypy`·`pyright` 가 전부 `None` |
| ★ **부적용인 창** — 속도·메모리 | — | 「제네릭이 느리다」를 **한 번도 재지 않았다** |

★★ **③이 이 주제의 네 번째 창이다.** 값 창(①)은 「**무엇이 담겼나**」 만 말하고 「**언제 평가됐나**」 는 말하지 않는다 —
[40번](../40-type-hints-at-runtime/2-summary.md)이 어노테이션 평가 시각을 잡은 **같은 장치**(부르면 `<평가됨: …>` 을 찍는 함수)를 `type` 문의 값 자리에 넣었다.

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「3.13 의 `TypeIs` 는 런타임에 무엇인가」를 **3.13 으로 물을 수 없어서**, 이 머신에 깔린 **`typing_extensions` 4.10.0 의 백포트**에 물었다(동작 6).
★ 바꾼 창이 못 보는 것 — **3.13 표준 라이브러리의 실제 객체.** 첫 줄 `te.TypeIs is typing 의 것 : False` 가 **다른 객체**라는 것을 스스로 말한다.

먼저 판을 박아 둔다.

```python
# e41_version.py
import shutil
import sys
import typing

print("version_info =", sys.version_info)
for name in ["TypeAliasType", "TypeIs", "ReadOnly", "NoDefault", "TypeGuard", "TypeAlias", "Literal"]:
    print("hasattr(typing, %-15r) : %s" % (name, hasattr(typing, name)))
try:
    typing.TypeVar("T", default=int)
    print("TypeVar(default=) : 받았다")
except TypeError as exc:
    print("TypeVar(default=) ->", type(exc).__name__ + ":", exc)
for exe in ["python3.13", "python3.14", "mypy", "pyright"]:
    print("PATH 의 %-10s : %s" % (exe, shutil.which(exe)))
```

```text
===== python3 - <e41_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
hasattr(typing, 'TypeAliasType') : True
hasattr(typing, 'TypeIs'       ) : False
hasattr(typing, 'ReadOnly'     ) : False
hasattr(typing, 'NoDefault'    ) : False
hasattr(typing, 'TypeGuard'    ) : True
hasattr(typing, 'TypeAlias'    ) : True
hasattr(typing, 'Literal'      ) : True
TypeVar(default=) -> TypeError: 'default' is an invalid keyword argument for typevar()
PATH 의 python3.13 : None
PATH 의 python3.14 : None
PATH 의 mypy       : None
PATH 의 pyright    : None
(exit 0)
```

```text
===== python3.11 - <e41_version_py311.py =====
version_info = sys.version_info(major=3, minor=11, micro=15, releaselevel='final', serial=0)
hasattr(typing, 'TypeAliasType') : False
hasattr(typing, 'TypeIs'       ) : False
hasattr(typing, 'ReadOnly'     ) : False
hasattr(typing, 'NoDefault'    ) : False
hasattr(typing, 'TypeGuard'    ) : True
hasattr(typing, 'TypeAlias'    ) : True
hasattr(typing, 'Literal'      ) : True
TypeVar(default=) -> TypeError: TypeVar.__init__() got an unexpected keyword argument 'default'
PATH 의 python3.13 : None
PATH 의 python3.14 : None
PATH 의 mypy       : None
PATH 의 pyright    : None
(exit 0)
```

(3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e41_version_py311.py` 다.)

* ★★★ **두 판 모두 `TypeIs`·`ReadOnly`·`NoDefault` 가 없고**, `python3.13`·`mypy`·`pyright` 가 **`None`** 이다 — 3.13 쪽과 검사기 쪽은 **못 잰 것**이다.
* ★★ **`TypeAliasType` 은 3.12 에만 있다** — `type` 문이 만드는 객체의 클래스다.
* ★ **`TypeVar(default=)` 는 두 판 다 `TypeError`** 인데 **문구가 다르다** — 3.12 는 `typevar()`(C 로 옮겨진 구현), 3.11 은 `TypeVar.__init__()`. **종류는 같고 문구는 판에 매인다.**

## 이 주제가 답하려는 질문

1. ★★★ **이 문법들은 런타임에 무엇을 남기나** — 형태 열 개 × 다섯 창. 그리고 **`isinstance` 에 쓸 수 있는 것은 어느 것인가.**
2. ★★ **PEP 695(3.12) 의 `type` 문과 `[T]` 는 무엇이 새로운가** — 3.11 에서는 `SyntaxError`, 그리고 **값이 늦게 평가된다.**
3. **3.13 의 `TypeIs`·기본값은 어디까지 말할 수 있나** — 이 머신에서는 **문서와 백포트까지**다.

★ 첫째가 이 주제의 인출 목표다.
**「검사기만 읽는 기호」와 「런타임이 들고 있는 객체」를 격자 한 장으로 가를 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 「런타임에 무엇이 남나」 격자 — 이 주제의 본체

**언제 쓰나** — 실행 중에 타입을 다루는 코드(검증·직렬화·디스패치)를 짤 때. **「이 기호로 무엇을 물을 수 있나」** 가 막힐 때.

```text
                           type(obj)          get_origin   get_args      __type_params__   isinstance(1, obj)
   int | str              UnionType           UnionType    (int, str)    -                 ★ 된다
   Optional[int]          _UnionGenericAlias  Union        (int, None)   -                 ★ 된다
   Literal['a', 'b']      _LiteralGenericAlias Literal     ('a', 'b')    -                 TypeError
   list[int]              GenericAlias        list         (int,)        () (3.12)         TypeError
   X: TypeAlias = …       ★ 오른쪽 식 그대로 — 별칭이라는 흔적 없음
   type X = …             TypeAliasType       None         ()            ()                TypeError
   def f[T] / class C[T]  function / type     None         ()            (T,)              (함수) TypeError / (클래스) False
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

그림 해설.

* ★★★ **마지막 줄 — `isinstance 가 값을 낸 행 5 / 10`.** 유니온 셋(`int | str`·`Optional`·`Union`)과 **`TypeAlias` 로 이름 붙인 유니온**, 그리고 **진짜 클래스 `C`** 만 답했다.
  나머지 다섯은 **`TypeError`** — 설계도에만 있는 기호다.
* ★★★ **`X: TypeAlias = int | str` 은 `int | str` 행과 한 칸도 다르지 않다.** `TypeAlias` 는 **대입문의 어노테이션**일 뿐이라
  `X` 에는 **오른쪽 식의 값이 그대로** 들어간다([40번](../40-type-hints-at-runtime/2-summary.md) 동작 1 — 어노테이션은 실행을 안 바꾼다).
  「이것이 별칭이다」는 **검사기만 아는 사실**이다.
* ★★ **`type X = int | str` 은 다르다** — **`TypeAliasType`** 이라는 **새 객체**가 남는다. `get_args` 는 **빈 튜플**이고 `isinstance` 는 **`TypeError`** 다 —
  유니온을 **봉투에 넣어** 이름을 붙였으므로 겉에서는 유니온이 안 보인다(동작 2 에서 봉투를 연다).
* ★★ **`Optional[int]` 과 `int | None` 은 `type` 이 다르다**(`_UnionGenericAlias` 대 `UnionType`) — 그런데 **`==` 는 참**이다(동작 5).
* ★ **`__type_params__`** — `type Pair[T]`·`def f[T]`·`class C[T]` 가 **`(T,)`** 로 타입 변수를 **들고 있다.** 런타임에 **남는다**
  ([TS 19번](../../../ts/syntax/19-generics-basics/2-summary.md)의 「런타임에 타입 인자는 없다」와 반대 — 동작 7).
* ★ **`list[int]` 의 `__type_params__` 가 `0`** — 3.12 에서 **모든 클래스**가 `__type_params__ = ()` 를 얻었고 `GenericAlias` 가 그 속성을 `list` 로 넘겨 준 것이다.
  이 칸이 **판 격자에서 갈린다**(동작 3).

**비용** — 유니온만 `isinstance` 가 되므로 **「타입 기호 하나로 정적 검사와 런타임 검사를 다 한다」는 유니온에서만** 성립한다.
`list[int]`·`Literal` 을 실행 중에 검사하려면 **직접 풀어야** 한다(`get_origin`·`get_args` — 동작 4).

### 2. ★★★ `type` 문 — 값은 봉투 안에서 늦게 평가된다

**언제 쓰나** — 아직 정의 안 된 이름·**서로를 가리키는 타입**을 별칭으로 쓰고 싶을 때. 「`type` 과 `TypeAlias` 가 뭐가 다르지」가 막힐 때.

```text
   type Later = list[Undefined]      <-- ★ 통과. 값 식은 아직 안 돈다
   Later.__value__                   <-- 여기서 처음 평가 -> NameError (Undefined 가 없다)
   Undefined = str
   Later.__value__                   <-- 다시 읽으면 list[str]

   Eager: TypeAlias = list[Missing]  <-- ★ 대입문이라 오른쪽이 곧바로 돈다 -> NameError

   type Tagged = tag(...)            평가 횟수 0
   Tagged.__value__ ; Tagged.__value__   평가 횟수 1   <-- 두 번 읽어도 한 번 (이 판의 관찰)
```

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

그림 해설.

* ★★★ **`[1]`** — `type Later = list[Undefined]` 가 **통과**했다. `Undefined` 는 그 줄에서 **정의돼 있지 않다.**
  **`Later.__value__` 를 읽는 순간** `NameError: name 'Undefined' is not defined` 가 났고, 이름을 만든 뒤 다시 읽자 **`list[str]`** 이 나왔다.
  ★ 문서 — *"they are not evaluated when the type alias or type variable is created. Instead, they are only evaluated when doing so is necessary to resolve an attribute access."*
* ★★★ **`[2]`** — **같은 값을 `TypeAlias` 로** 쓰면 대입 자리에서 곧바로 **`NameError`** 다. `TypeAlias` 는 **보통 대입문**이기 때문이다.
  ★ **둘을 가르는 것은 이름이 아니라 「언제 평가하나」다.**
* ★★ **`[3]`이 네 번째 창이다** — `type 문 직전`·`직후` 사이에 **`<평가됨>` 줄이 없다**(평가 횟수 `0`).
  `__value__` 를 **두 번** 읽었는데 `<평가됨>` 은 **한 번**, 횟수 `1` — 처음 한 번 평가하고 **기억해 둔다.** ★ 이 「한 번」은 **이 판의 관찰**이다 — 문서는 「늦게」까지만 말한다.
* ★★ **`[4]`** — `Expr` 이 `Pair` 를, `Pair` 가 `Expr` 을 가리키는데 **둘 다 선언이 통과**하고 `__value__` 도 나온다. 늦게 평가하니 **서로 가리키는 별칭**이 된다(문서의 예도 이 모양이다).
* ★★ **`[5]`** — `def pick[T: tag("T 의 경계")]` 의 **경계도** `def` 때는 안 돌고(`1` 그대로), **`T.__bound__` 를 읽을 때** 돈다(`2`).

**비용** — 늦은 평가의 대가는 **오타가 정의 자리에서 안 드러난다**는 것이다. `type X = list[Usr]` 는 조용히 통과하고,
**`__value__` 를 읽는 쪽**(런타임 검증 라이브러리·`get_type_hints`)에서 처음 터진다 — [40번](../40-type-hints-at-runtime/2-summary.md)의 `__future__` 와 같은 모양의 대가다.

### 3. ★★★ 판 격자 — 3.11 은 파서가 모른다

**언제 쓰나** — 라이브러리가 여러 판을 지원할 때. **「이 문법을 쓰면 몇 판부터 되나」** 가 막힐 때.

| | 3.11 | 3.12 | ★ 3.13 |
|---|---|---|---|
| `int \| str` · `Optional` · `Literal` · `TypeAlias` | 된다 | 된다 | 된다(문서) |
| `type X = …` · `def f[T]` · `class C[T]` | ★ **`SyntaxError`** | 된다 | 된다(문서) |
| 모든 클래스의 `__type_params__` | ★ 없다(`AttributeError`) | `()` | — |
| `typing.TypeAliasType` | 없다 | 있다 | 있다(문서) |
| **`[T = int]`**(타입 매개변수 기본값, PEP 696) | `SyntaxError` | ★ **`SyntaxError`** | ★ 된다(문서) |
| `TypeVar(…, default=)` | `TypeError` | `TypeError` | ★ 된다(문서) |
| `typing.TypeIs`(PEP 742) | 없다 | ★ **없다** | ★ 있다(문서) |
| **근거** | 실측 | 실측 | ★★ **문서만 — 이 머신에 3.13 이 없다** |

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

(3.11 블록의 소스는 동작 1 의 격자와 **한 글자도 같다** — 파일 이름만 `e41_grid_py311.py` 다.)

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

그림 해설.

* ★★★ **마지막 줄 — `판이 갈린 행 5 / 10`.** 갈린 다섯은 **PEP 695 네 행**(3.11 에서 `SyntaxError`)과 **`list[int]`** 다.
* ★★ **`list[int]` 이 갈린 이유는 `__type_params__` 한 칸** — 3.11 은 `AttributeError`, 3.12 는 `0`. **문법이 안 바뀌어도 판이 칸을 바꾼다.**
* ★ 3.11 은 `isinstance 가 값을 낸 행 4 / 10` — 3.12 의 5 에서 **`class C[T]` 한 행**이 빠졌다(만들어지지도 않았으므로).
* ★★ 3.13 열은 **한 칸도 실측이 아니다.** What's New 문장 — *"PEP 696: Type parameters (`typing.TypeVar`, `typing.ParamSpec`, and `typing.TypeVarTuple`) now support defaults."*

`SyntaxError` 전문 — 3.11 이 `type` 문과 `[T]` 를 만났을 때, 그리고 **3.12 가 3.13 문법(`[T = int]`)을 만났을 때.**

```python
# e41_stmt_py311.py
type Pair = tuple[int, int]
```

```text
===== python3.11 - <e41_stmt_py311.py =====
  File "<stdin>", line 1
    type Pair = tuple[int, int]
         ^^^^
SyntaxError: invalid syntax
(exit 1)
```

```python
# e41_generic_py311.py
def first[T](xs: list[T]) -> T:
    return xs[0]
```

```text
===== python3.11 - <e41_generic_py311.py =====
  File "<stdin>", line 1
    def first[T](xs: list[T]) -> T:
             ^
SyntaxError: expected '('
(exit 1)
```

```python
# e41_default.py
def first[T = int](xs: list[T]) -> T:
    return xs[0]
```

```text
===== python3 - <e41_default.py =====
  File "<stdin>", line 1
    def first[T = int](xs: list[T]) -> T:
             ^
SyntaxError: expected '('
(exit 1)
```

* ★★ **`SyntaxError` 는 캐럿이 있다**(파서가 잡으므로 — 규칙 16). 3.11 은 `type` 문의 **이름 자리**(`Pair`)를, `[T]` 는 **여는 대괄호**를 가리킨다.
* ★★★ **3.12 의 `[T = int]` 오류가 3.11 의 `[T]` 오류와 한 글자도 같다** — `expected '('`, 캐럿도 같은 열(대괄호). 3.12 파서는 **기본값이 붙은 대괄호를 통째로 모른다.**
  「3.12 에 `[T]` 가 있으니 기본값도 되겠지」가 **한 글자 차이로 파서 밖**이다.

**비용** — PEP 695 문법을 **한 줄이라도** 쓰면 그 파일은 **3.11 에서 import 자체가 안 된다**(파서가 파일 전체를 거부한다). 판 지원이 곧 문법 선택이다.

### 4. ★★ `isinstance` 가 되는 것과 안 되는 것 — 그리고 `Literal` 을 런타임에 쓰려면

**언제 쓰나** — 「타입 힌트로 적은 것을 그대로 실행 중 검사에 쓰고 싶다」가 막힐 때.

```text
   isinstance(1, int | str)        True       유니온 객체는 isinstance 가 받는다 (3.10+)
   isinstance(None, int | None)    True
   isinstance(1, list[int])        TypeError  「parameterized generic」 — 원소 타입까지는 안 본다
   isinstance("x", Literal[…])     TypeError
                                             -> 값 목록은 get_args 로 꺼내서 in 으로 본다
```

```python
# e41_isinstance.py
import sys

print(isinstance(1, int | str), file=sys.stderr)
print(isinstance(None, int | None), file=sys.stderr)
print(isinstance(1, list[int]), file=sys.stderr)
```

```text
===== python3 - <e41_isinstance.py =====
True
True
Traceback (most recent call last):
  File "<stdin>", line 5, in <module>
TypeError: isinstance() argument 2 cannot be a parameterized generic
(exit 1)
```

* ★★★ `True` 두 줄 뒤 **`TypeError: isinstance() argument 2 cannot be a parameterized generic`** — **원소 타입이 붙은 제네릭**은 `isinstance` 가 거부한다.
  ★ 앞 두 줄은 **`sys.stderr` 로** 찍었다 — 트레이스백과 **같은 흐름**이어야 순서가 고정된다(규칙 18).
* ★ 트레이스백에 **소스 줄도 캐럿도 없다** — 실행 중 예외이기 때문이다(`<stdin>` 형태, 규칙 16).

`Literal` 은 `isinstance` 가 안 되니 **값 목록을 꺼내서** 쓴다 — 그리고 [39번](../39-match-statement/2-summary.md)의 `match` 가 그 값들을 가른다.

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

* ★★★ **`[1]`** — `mode: Mode`(`Literal["r", "w"]`) 인 함수에 **`"x"` 가 그대로 들어갔다.** `Literal` 은 **검사하지 않는다.**
* ★★ **`[2]`** — `get_args(Mode.__value__)` 로 **`('r', 'w')`** 를 꺼냈다. ★ `Mode` 가 `type` 문이라 **`__value__` 로 봉투를 먼저 열어야** 한다(동작 2).
  이 튜플로 **`in` 검사**를 하면 런타임 검사가 된다 — **내가 쓴 검사**이지 `Literal` 이 해 준 것이 아니다.
* ★★ **`[3]`** — [39번](../39-match-statement/2-summary.md)의 **리터럴 패턴 `case "r" | "w":`** 가 값을 가르고, 나머지는 **캡처 `case other:`** 로 받았다. `Literal` 과 `match` 는 **같은 값 목록을 두 번 적는 관계**다.
* ★ **`[4]`** — **`Literal[1] == Literal[True]` 는 `False`**, 그런데 **`1 == True` 는 `True`**. `Literal` 은 값뿐 아니라 **타입까지 같아야** 같다고 본다([12번](../12-dict-and-key-requirements/2-summary.md)의 `1`·`True` 가 한 키인 것과 반대).

**비용** — 런타임 검사가 필요하면 **기호와 검사가 두 벌**이 된다(`Literal` + `get_args`/`match`). 한쪽만 고치면 어긋난다.

### 5. ★★ 두 표기 — `Optional[int]` 과 `int | None`, 그리고 문자열 전방 참조

**언제 쓰나** — 옛 코드(`Optional`·`Union`)와 새 코드(`|`)가 섞일 때. 전방 참조 문자열을 유니온에 넣을 때.

```text
   Optional[int] == (int | None)    True          같다고 답한다
   type 둘                          _UnionGenericAlias / UnionType    그런데 다른 객체다

   Union[int, 'Node']               ForwardRef('Node') 로 싸 준다
   int | 'Node'                     TypeError      type 과 str 사이의 | 가 없다
   'int | Node'                     문자열 하나로   <- 통째로 따옴표에 넣는다
```

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

* ★★ **`[1]`** — `==` 는 참이고 **`type` 은 다르다.** `type(x) is types.UnionType` 같은 검사는 **옛 표기를 놓친다.**
* ★★★ **`[2]`** — **`int | 'Node'` 는 `TypeError: unsupported operand type(s) for |: 'type' and 'str'`.** `|` 는 **실행되는 연산자**라서 `type` 과 `str` 사이에 정의가 없으면 터진다.
  `Union[int, 'Node']` 는 문자열을 **`ForwardRef` 로 싸 주므로** 통과한다. ★ 전방 참조를 섞을 때는 **식 전체를 따옴표로** 싸거나(`'int | Node'`) `type` 문(동작 2)을 쓴다.
* ★ **3.11 도 한 글자도 같았다**(`python3.11 - <e41_pitfalls.py` 를 던져 확인 — 블록은 싣지 않았다).

### 6. ★★ 3.13 의 `TypeIs`·기본값 — 문서, 그리고 백포트에게 물은 것

**언제 쓰나** — 「`TypeIs` 를 쓰면 런타임에 좁혀 주나」가 막힐 때.

★★★ **3.13 은 이 머신에 없다.** 문서가 말하는 것 — *"`TypeIs` can be used to annotate the return type of a user-defined type predicate function. … At runtime, functions marked this way should return a boolean"*,
그리고 목적은 *"type narrowing — a technique used by static type checkers"* 다. **좁히기는 검사기의 일**이라고 문서가 스스로 적는다.

그 말을 **다른 창으로** 확인했다 — 이 머신에 깔린 **`typing_extensions`** 백포트다.

```python
# e41_backport.py
import importlib.metadata
import typing

import typing_extensions as te

print("typing_extensions 판 :", importlib.metadata.version("typing_extensions"))
print("te.TypeIs is typing 의 것 :", getattr(typing, "TypeIs", None) is te.TypeIs)


def is_str(x: object) -> te.TypeIs[str]:
    return isinstance(x, str)


print("[1] 부르면 :", is_str("a"), is_str(1), "| 반환 타입 :", type(is_str(1)).__name__)
print("[2] 어노테이션 :", is_str.__annotations__["return"])


def check2(x: object) -> te.TypeIs[str]:
    return True


print("[3] check2(1) :", check2(1))

T = te.TypeVar("T", default=int)
print("[4] TypeVar(default=int).__default__ :", T.__default__)
print("    type(T) :", type(T).__module__ + "." + type(T).__name__)
```

```text
===== python3 - <e41_backport.py =====
typing_extensions 판 : 4.10.0
te.TypeIs is typing 의 것 : False
[1] 부르면 : True False | 반환 타입 : bool
[2] 어노테이션 : typing_extensions.TypeIs[str]
[3] check2(1) : True
[4] TypeVar(default=int).__default__ : <class 'int'>
    type(T) : typing.TypeVar
(exit 0)
```

* ★★★ **`[1]`** — `TypeIs[str]` 로 표시한 함수는 **그냥 `bool` 을 돌려주는 함수**다. 런타임은 **아무것도 좁히지 않는다.**
* ★★ **`[3]`** — **몸통이 늘 `True` 인 판별 함수**도 `check2(1)` 이 **`True`** 를 돌려준다. 이 거짓말을 잡는 것은 **검사기의 몫이고 — 이 머신에서는 못 잰 것**이다.
  ★ [TS 13번](../../../ts/syntax/13-type-guards-and-predicates/2-summary.md)(2)가 TS 에서 같은 것을 보였다 — **컴파일러도 술어의 몸통을 믿는다.**
* ★ **`[4]`** — 백포트의 `TypeVar("T", default=int)` 는 **`__default__` 에 `int`** 를 들고 있다. **`type(T)` 는 표준 `typing.TypeVar`** — 백포트가 표준 객체에 속성을 얹은 모양이다.
* ★★ **선** — 이 블록은 **`typing_extensions` 4.10.0 의 관찰**이다. **3.13 의 `typing.TypeIs` 가 같은 객체라는 근거는 없다**(첫 줄 `False` 는 3.12 에 `typing.TypeIs` 가 없어서 `None` 과 견준 것이다).

### 7. ★★ 제네릭 함수·클래스 — 런타임에 무엇을 들고 있나

**언제 쓰나** — `def f[T]`·`class C[T]` 를 처음 쓸 때. 「`T` 는 어디 사나」가 막힐 때.

```text
   def first[T](xs: list[T]) -> T          first.__type_params__ == (T,)       T 는 TypeVar 객체
                                           first([1, 'a']) -> 1   (T 가 무엇이든 검사 없음)
   class Box[T]: ...                       Box.__mro__ = Box, Generic, object   ★ Generic 을 안 썼는데 들어온다
                                           Box[int]  -> _GenericAlias           Box[int](…) 의 __orig_class__

   ★ T 는 모듈 전역에 없다 ('T' in globals() -> False)  — 주석 스코프(annotation scope)에 산다
   ★ first 의 T 와 second 의 T 는 다른 객체다
```

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

* ★★★ **`[1]`** — `first('문자열')` 이 **`'문'`** 을, `Box[int]('문자열')` 이 **문자열을 그대로** 받았다. **`T` 는 검사하지 않는다**([40번](../40-type-hints-at-runtime/2-summary.md) 동작 1 과 같은 결론).
* ★★ **`[2]`** — `__type_params__` 가 **`(T,)`** 이고 그 `T` 는 **`TypeVar`**. `__annotations__` 에도 `list[T]`·`T` 로 **남아 있다.**
  ★★ **`Box.__mro__` 에 `Generic` 이 있다** — `class Box[T]:` 라고만 썼는데 **`typing.Generic` 을 암묵적으로 물려받는다.**
  ★ `Box[int](1)` 로 만든 인스턴스는 **`__orig_class__`** 에 `Box[int]` 를 기억한다 — 런타임에 **타입 인자가 남는** 자리다(TS 19번은 방출물에서 **안 남는** 것을 보였다).
* ★★ **`[3]`·`[4]`** — **함수마다 `T` 가 따로** 만들어지고(`is` 가 `False`), **모듈 전역에 `T` 라는 이름이 안 생긴다.**
  PEP 695 이전의 `T = TypeVar("T")` 는 **모듈 전역 이름**이었다 — 이것이 새 문법이 바꾼 것이다.
* ★ **`[5]`** — `[N: (int, float)]` 의 **제약**이 `__constraints__` 에 남지만 `clamp('s')` 는 **통과**한다.

**비용** — 새 문법은 **`T` 선언 줄을 없앤** 대신, `T` 를 **밖에서 꺼내려면 `__type_params__` 로** 가야 한다.

### 8. ★★ TS 와 견주면 — 누가 보고 무엇이 남나

```text
                         유니온·리터럴·제네릭을 보는 쪽           실행 중 남는 것                  런타임 검사
   TypeScript            tsc (이 저장소 머신에 있다)           ★ 방출된 .js 에 없다             없다 (읽을 게 없다)
   Python 3.12           검사기 (이 머신에 없다 — 못 잰 것)      UnionType · TypeAliasType ·     유니온만 isinstance
                                                               __type_params__                  나머지는 get_args 로 손수
```

* ★★★ **TS 는 컴파일러가 보고 지운다**([TS 09번](../../../ts/syntax/09-union-types/2-summary.md) — 유니온은 방출에 한 글자도 안 남는다 ·
  [TS 19번](../../../ts/syntax/19-generics-basics/2-summary.md) (6) — 런타임에 타입 인자는 없다).
  **파이썬은 이 머신에서 아무도 안 보고, 객체로 남긴다.**
* ★★ **그래서 파이썬에만 「기호를 런타임에 꺼내 쓰는」 길이 있다**(동작 4 의 `get_args` · 동작 7 의 `__orig_class__`). 대신 **검사는 사람이 쓴다.**
* ★ TS 의 `satisfies`·`as const` 처럼 **검사기에게만 뜻이 있는 문법**은 파이썬 쪽에서 **대응을 재지 않았다** — 비교할 검사기가 없다.

## 문법 — 형태와 규칙

**형태**

```text
x: int | str                         # 유니온 (3.10+)          Optional[int] == int | None
mode: Literal["r", "w"]              # 리터럴 (3.8+)           값 목록은 get_args 로
Old: TypeAlias = list[int]           # 명시 별칭 (3.10+)       ★ 3.12 에서 폐기 예고 — type 문으로

type Pair[T] = tuple[T, T]           # type 문 (3.12+)         값·경계는 늦게 평가된다
def first[T](xs: list[T]) -> T: ...  # 제네릭 함수 (3.12+)      T 는 __type_params__ 에
class Box[T]: ...                    # 제네릭 클래스 (3.12+)    Generic 을 암묵적으로 물려받는다
def clamp[N: (int, float)](x: N): .. # 제약 튜플               [N: int] 는 경계(bound)

def first[T = int](...)              # ★ 3.13+ (PEP 696) — 3.12 에서는 SyntaxError
def is_str(x) -> TypeIs[str]: ...    # ★ 3.13+ (PEP 742) — 3.12 typing 에는 없다
```

규칙 열.

1. ★★★ **어느 기호도 실행을 검사하지 않는다** — `Literal`·`T`·`TypeIs` 전부(동작 4·6·7).
2. ★★★ **`isinstance` 는 유니온과 진짜 클래스만** 받는다 — `list[int]`·`Literal`·`type` 별칭은 `TypeError`(동작 1 — 5 / 10).
3. ★★★ **`type` 문의 값과 타입 매개변수의 경계·제약은 늦게 평가된다** — `__value__`·`__bound__` 를 읽을 때(동작 2).
4. ★★ **`TypeAlias` 는 대입문이다** — 오른쪽이 곧바로 평가되고, 남는 것은 **그 값 자체**다.
5. ★★ **PEP 695 문법은 3.12 부터** — 3.11 에서는 파일째 `SyntaxError`(동작 3).
6. ★★ **`int | 'Node'` 는 `TypeError`** — 전방 참조는 식 전체를 따옴표로(동작 5).
7. ★ **`[T]` 의 `T` 는 모듈 전역에 안 생긴다** — 함수·클래스마다 따로(동작 7).
8. ★ **3.13 기능(`TypeIs`·기본값)은 이 머신에서 못 잰 것** — 문서와 백포트까지만 말한다.

## 어디서 틀리나

### (1) ★★★ 「`Literal["r", "w"]` 라고 썼으니 `"x"` 는 못 들어온다」

**들어온다**(동작 4 의 `[1]`). 막는 것은 **검사기**이고 **이 머신에 없어 무엇을 잡는지 못 쟀다.** 런타임에 막으려면 `get_args` + `in`, 또는 `match`.

### (2) ★★★ `isinstance(v, list[int])` 로 원소 타입까지 검사하려 한다

**`TypeError`** 다(동작 4). `isinstance(v, list)` 로 겉만 보고 원소는 따로 돈다.

### (3) ★★★ `type X = …` 와 `X: TypeAlias = …` 를 같은 것으로 안다

**평가 시각이 다르고 남는 객체가 다르다**(동작 1·2) — 앞은 `TypeAliasType`(늦게), 뒤는 **값 그 자체**(곧바로).

### (4) ★★ `type` 별칭에 `get_args`·`isinstance` 를 바로 쓴다

**빈 튜플 · `TypeError`** 다(동작 1). 봉투를 **`__value__` 로 먼저 연다**(동작 4 의 `[2]`).

### (5) ★★ `type X = list[Usr]` 의 오타가 정의 자리에서 안 드러난다

**늦은 평가라서 통과한다**(동작 2 의 `[1]`). `__value__` 를 읽는 쪽에서 처음 `NameError`.

### (6) ★★ `int | 'Node'`

**`TypeError`**(동작 5). `Union[int, 'Node']` 는 되고 `|` 는 안 된다 — 연산자가 **실행되기** 때문이다.

### (7) ★★ 3.12 에 `[T]` 가 있으니 `[T = int]` 도 되겠지

**`SyntaxError`** 다 — 그것도 3.11 의 `[T]` 와 **한 글자도 같은 오류**다(동작 3).

### (8) ★★ 「`TypeIs` 를 쓰면 런타임에 좁혀 준다」

**좁히기는 검사기의 일**이다(문서). 백포트로 물으니 **그냥 `bool` 을 돌려주는 함수**였고 거짓말하는 몸통도 통과했다(동작 6).

### (9) ★ `type(x) is types.UnionType` 로 유니온을 가린다

**`Optional[int]` 을 놓친다** — `==` 는 참인데 `type` 이 다르다(동작 5).

### (10) ★ 「`Literal[1]` 과 `Literal[True]` 는 같다」

**다르다**(동작 4 의 `[4]`) — `1 == True` 와 달리 **타입까지** 본다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스·PEP·`typing` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 문서가 말하지 않는 객체의 모양 | 실행 |
| **이 판(3.12.3 · 3.11.15)의 관찰** | 이 판에서 그랬을 뿐 | 예외 문구 |
| ★ **못 잰 것** | 3.13 의 실제 동작 · 타입 검사기의 판정 | ★★★ 판·도구가 없다 |
| ★ **다른 창** | `typing_extensions` 4.10.0 의 백포트 | 실행 — 3.13 이 아니다 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `type` 문의 값, 타입 매개변수의 경계·제약은 **늦게 평가된다** | 실행 모델 — Lazy evaluation |
| `isinstance(x, T)`(타입 변수)는 **`TypeError`** | `typing` 문서 `TypeVar` 절 |
| `Literal[...]` 의 인자는 **런타임에 아무 값이나 받는다** — 검사기가 거부할 수 있을 뿐 | `typing` 문서 `Literal` 절 |
| `TypeAlias` 는 **3.12 에서 폐기 예고**, 제거 계획은 없다 | `typing` 문서 `TypeAlias` 절 |
| PEP 695 문법은 **3.12** 부터 | What's New 3.12 · 실행(3.11 `SyntaxError`) |
| `TypeIs`·타입 매개변수 기본값은 **3.13** 부터 | What's New 3.13 — ★ 이 머신에서는 **못 잰 것** |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★ `__value__` 는 **한 번 평가하고 기억한다** | 실행(동작 2 의 `[3]` — 두 번 읽고 평가 1회) |
| ★ 3.12 에서 **모든 클래스**가 `__type_params__ = ()` 를 가진다 | 실행(동작 1·3 — `list[int]` 칸) |
| ★ `class C[T]` 가 **`Generic` 을 암묵적으로** 물려받는다 | 실행(동작 7) |
| `Optional[int]` 과 `int \| None` 이 **다른 클래스** | 실행(동작 5) |
| `TypeVar(default=)` 오류 **문구**가 3.11·3.12 에서 다르다 | 실행(첫 블록) |

### 그래서 이렇게 적으면 틀린다

* ✗ 「타입 힌트를 `Literal` 로 좁혀 두면 잘못된 값이 막힌다」\
  ○ **런타임은 안 막는다.** 막는 것은 검사기(이 머신에서 못 잰 것)이거나 **내가 쓴 검사**다.
* ✗ 「`type X = …` 는 `X: TypeAlias = …` 의 새 표기일 뿐이다」\
  ○ **평가 시각과 남는 객체가 다르다**(동작 2).
* ✗ 「3.13 에서 `TypeIs` 는 이렇게 동작한다(실행해 보니)」\
  ○ ★ **못 잰 것**이다. 백포트의 관찰은 **다른 창**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 3.10+ 만 지원 | `int \| None` | `Optional` 과 `==` 이고 `isinstance` 도 된다 |
| **3.12+ 만** 지원 | `type` 문 · `def f[T]` | 전방 참조·상호 참조가 자유롭고 `T` 선언 줄이 없다 |
| 3.11 을 지원 | `TypeAlias` · `T = TypeVar("T")` | ★ PEP 695 는 **파일째 `SyntaxError`** |
| 값 목록을 **실행 중에도** 검사 | `Literal` + `get_args`, 또는 `match` | 런타임은 `Literal` 을 **안 본다** |
| 원소 타입까지 실행 중 검사 | 직접 순회 · 검증 라이브러리 | `isinstance(v, list[int])` 는 `TypeError` |
| `TypeIs`·기본값 | ★ 3.13+ (또는 `typing_extensions`) | 3.12 표준에는 없다 |

## 핵심 문장

1. **`typing` 의 기호는 실행을 검사하지 않는다** — `Literal`·`T`·`TypeIs` 전부. 막는 것은 검사기이고, 이 머신에서는 못 잰 것이다.
2. **런타임에 남는 것은 객체다** — `isinstance` 가 받는 것은 **유니온과 진짜 클래스뿐**(격자 5 / 10).
3. **`type` 문의 값은 봉투 안에서 늦게 평가된다** — `__value__` 를 읽을 때. `TypeAlias` 는 곧바로 평가되는 보통 대입문이다.
4. **PEP 695 는 3.12 부터** — 3.11 은 파일째 `SyntaxError`, 판 격자에서 **5 / 10** 이 갈렸다. 3.12 는 3.13 의 `[T = int]` 를 **같은 오류로** 거부한다.
5. **3.13 의 `TypeIs`·기본값은 문서와 백포트까지만** 말할 수 있다.

## 관련 자료

* 선행: [40-type-hints-at-runtime](../40-type-hints-at-runtime/2-summary.md) — ★★★ **경계**: 어노테이션이 **언제 평가되고 어디 담기나**는 그쪽,
  여기는 **그 자리에 쓰는 기호가 무엇으로 남나**부터. 그 편이 예고한 「`'Node | None'` 은 문자열이라 어느 판에서든 통과」가 동작 5 의 `'int | Node'` 행이다.
* 선행: [35-abc-and-protocol](../35-abc-and-protocol/2-summary.md) — `Protocol`·`runtime_checkable` 과 **검사기 부재 판정의 정본.** 제네릭 `Protocol` 은 여기서 다루지 않았다.
* 선행: [39-match-statement](../39-match-statement/2-summary.md) — 리터럴 패턴·캡처 패턴. 동작 4 의 `[3]` 이 이음매다.
* 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — `1`·`True` 가 한 키. `Literal` 은 반대로 가른다.
* 이어지는 곳: [목록의 **45번 주제**](../45-functools/)(`functools`) — `singledispatch` 가 **유니온 어노테이션**으로 등록되는지는 그쪽에서 잰다.
* 대비: [TS 09번 — 유니온](../../../ts/syntax/09-union-types/2-summary.md) · [TS 11번 — 리터럴 타입](../../../ts/syntax/11-literal-types-and-as-const/2-summary.md) ·
  [TS 13번 — 타입 술어](../../../ts/syntax/13-type-guards-and-predicates/2-summary.md) · [TS 19번 — 제네릭](../../../ts/syntax/19-generics-basics/2-summary.md) ·
  [TS 20번 — 제약과 기본값](../../../ts/syntax/20-generic-constraints-and-defaults/2-summary.md) —
  **경계**: 검사기(`tsc`)의 판정과 방출물 실측은 전부 그쪽이고, 여기서는 **파이썬 쪽 런타임 객체**만 쟀다.
* 공식 문서: [`typing`(3.12)](https://docs.python.org/3.12/library/typing.html) · [실행 모델 — Lazy evaluation](https://docs.python.org/3.12/reference/executionmodel.html#lazy-evaluation) ·
  [`type` 문](https://docs.python.org/3.12/reference/simple_stmts.html#type) · [What's New 3.13](https://docs.python.org/3.13/whatsnew/3.13.html) ·
  [PEP 604](https://peps.python.org/pep-0604/) · [PEP 695](https://peps.python.org/pep-0695/) · [PEP 696](https://peps.python.org/pep-0696/) · [PEP 742](https://peps.python.org/pep-0742/)

## 용어 풀이

* **유니온(union)**: 「A 또는 B」 타입. `int | str`(3.10+) · `Union[int, str]` · `Optional[int]`(= `int | None`).
* **`UnionType`**: `int | str` 이 만드는 런타임 객체. `isinstance` 의 두 번째 인자로 쓸 수 있다.
* **`Literal`**: 특정 **값**만 허용한다고 적는 기호. 런타임은 **검사하지 않는다.**\
  예: `Literal["r", "w"]` 의 값 목록은 `get_args` 로 `('r', 'w')`.
* **타입 별칭(type alias)**: 타입 식에 붙인 이름. `TypeAlias` 는 **대입문의 어노테이션**, `type` 문은 **`TypeAliasType` 객체**를 만든다.
* **`TypeAliasType`**(3.12+): `type` 문이 만드는 객체. 값은 **`__value__`** 로 읽고, 그때 **늦게 평가**된다.
* **늦은 평가(lazy evaluation)**: 만들 때가 아니라 **꺼낼 때** 식을 평가하는 것.\
  예: `type Later = list[Undefined]` 는 통과하고 `Later.__value__` 에서 `NameError`.
* **타입 변수(`TypeVar`)**: 제네릭의 매개변수 `T`. `[T]` 문법(3.12+)이면 **함수·클래스마다 따로** 만들어진다.
* **`__type_params__`**(3.12+): 제네릭 함수·클래스·별칭이 들고 있는 **타입 변수 튜플**.
* **경계(bound) / 제약(constraints)**: `[T: int]` 는 「`int` 의 하위 타입」, `[T: (int, str)]` 는 「이 중 하나」. 둘 다 **늦게 평가**된다.
* **`get_origin` / `get_args`**: 기호를 **바깥 틀**과 **안의 인자**로 쪼개는 함수. `list[int]` → `list` · `(int,)`.
* **`TypeIs`**(3.13, PEP 742): 판별 함수의 반환에 적어 **검사기에게 좁히기를 알리는** 기호. ★ **이 머신에서 못 잰 것.**
* **백포트(backport)**: 새 판의 기능을 옛 판에서 쓰게 만든 **별도 패키지**. 여기서는 `typing_extensions`.

## 더 들어가면

* ★ **`ParamSpec`·`TypeVarTuple`** — `[**P]`·`[*Ts]` 도 PEP 695 문법으로 쓴다. 이 문서는 **`T` 하나만** 쟀다.
* ★ **변성(variance)** — PEP 695 는 `[T]` 의 공변·반변을 **검사기가 추론**하게 했다. 검사기가 없어 **이 문서의 창으로는 원리상 안 보인다.**
* ★ **3.13 을 설치하게 되면 다시 돌릴 것** — 첫 블록(`hasattr`)과 동작 3 의 판 격자, 그리고 `e41_default.py`. 문서대로면 `[T = int]` 가 통과하고 `T.__default__` 가 `int` 가 된다 —
  ★ **이것은 예측이지 측정이 아니다.**
