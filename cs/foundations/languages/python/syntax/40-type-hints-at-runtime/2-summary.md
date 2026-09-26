# python/syntax/40-type-hints-at-runtime — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [`typing`(3.12)](https://docs.python.org/3.12/library/typing.html) — *"The Python runtime does not enforce function and variable type annotations."* ·
>   `get_type_hints` 가 문자열로 적힌 전방 참조를 평가한다는 문단
> - [Annotations Best Practices(3.12)](https://docs.python.org/3.12/howto/annotations.html) — `from __future__ import annotations` 가 어노테이션을 **문자열로 바꾼다**(*"stringized"*)는 문단 ·
>   이미 문자열인 어노테이션은 *"quoted twice"* 가 된다는 예 · 3.10+ 에서는 `inspect.get_annotations()` 가 권장이라는 문단
> - [What's New In Python 3.14](https://docs.python.org/3.14/whatsnew/3.14.html) — PEP 649·749 절:
>   *"annotations are no longer evaluated eagerly … evaluated only when necessary (except if `from __future__ import annotations` is used)"* ·
>   새 모듈 `annotationlib` 과 세 형식 `VALUE`·`FORWARDREF`·`STRING`. ★ **이 판은 이 머신에 없다 — 문서로만 적는다.**
> - [`functools.singledispatch`](https://docs.python.org/3.12/library/functools.html#functools.singledispatch) — 첫 인자의 어노테이션으로 등록하는 `register`
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 **둘** — `python3` **3.12.3** 이 본판이고, **판 격자**를 위해 `python3.11` **3.11.15** 로 두 블록을 더 던졌다.\
> ★★★ **3.14 는 이 머신에 없다** — 첫 블록이 `PATH` 에서 `python3.14` 를 찾아 **`None`** 을 받았고, **`import annotationlib` 이 `ModuleNotFoundError`** 였다.
> 그래서 3.14 의 지연 평가는 **못 잰 것**이고, 판 격자의 3.14 열은 **문서 문장만** 싣는다.\
> ★★★ **타입 검사기도 이 머신에 없다** — [35번](../35-abc-and-protocol/2-summary.md)과 [38번](../38-namedtuple-and-typeddict/2-summary.md)이 다섯 도구를 물어 **전부 `None`** 이었다.
> 이 주제의 과녁은 **「검사기만 보는 것」과 「런타임이 보는 것」을 가르는 것**인데, 검사기 쪽은 **전부 못 잰 것**이다.\
> ★ 던지는 형태는 `python3 - <파일` 하나로 고정했다. **`from __future__` 는 파일 맨 위에만 올 수 있으므로** 기본 판과 `__future__` 판을 **파일을 따로** 만들었다.
> ★ 트레이스백은 한 블록도 안 실었다 — `NameError` 도 `except` 로 받아 **타입과 메시지만** 찍었다(`typing.py` 를 지나는 것이 있어 한 형식으로 맞췄다).\
> **버전** — 함수 어노테이션은 **3.0**(PEP 3107), 변수 어노테이션은 **3.6**(PEP 526), `from __future__ import annotations` 는 **3.7**(PEP 563),
> `inspect.get_annotations` 는 **3.10**, 지연 평가는 **3.14**(PEP 649·749) 부터다.\
> ★ **구현 대 언어 보장 한 줄** — **「런타임은 어노테이션을 강제하지 않는다」·평가 시각·`__future__` 의 문자열화까지가 언어 보장**이고,
> **`dataclass`·`NamedTuple`·`singledispatch` 가 어노테이션을 어떻게 읽느냐**는 각 모듈의 계약이며,
> 그 모듈들이 `__future__` 아래에서 **무엇을 받느냐**(`'int'` 인가 `ForwardRef('int')` 인가)는 CPython 쪽이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★ 판이 오르면 **`__annotations__` 가 담는 것 자체** — 3.14 에서 바뀐다고 문서가 적는다(못 잰 것) | ★★ 격자의 칸 · 마지막 줄 **「갈린 칸 N / M」** — **3.11 과 3.12 에서 한 글자도 같았다** |
> | 판이 오르면 예외 **문구** | `<평가됨: …>` 줄이 **찍히느냐 안 찍히느냐**와 그 **순서** |
> | — (주소·시간을 한 곳도 안 찍었다) | `get_type_hints` 가 되살린 값 |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대 경로도 한 곳도 안 찍힌다.** 재대조 전부 동일.\
> **선행** — [19-function-argument-rules](../19-function-argument-rules/2-summary.md)(★ **매개변수 자리 — 어노테이션이 붙는 곳**) ·
> [36-dataclasses](../36-dataclasses/2-summary.md)(★★★ **「어노테이션을 읽지만 값 타입은 안 본다」 — 이 주제의 예외 격자 첫 행**) ·
> [38-namedtuple-and-typeddict](../38-namedtuple-and-typeddict/2-summary.md)(★★ **「런타임이 들고만 있다」**) ·
> [35-abc-and-protocol](../35-abc-and-protocol/2-summary.md)(★ **검사기 부재 판정의 정본**).

## 한눈에 — 쉽게 말하면

**타입 힌트는 「택배 상자에 붙인 내용물 메모」다.** 배송 기사(인터프리터)는 메모를 **읽지 않고** 상자를 나른다.
메모는 상자에 **붙은 채로 남아** 있어서 **누구든 떼어 읽을 수는** 있다.

* 메모를 쓰는 곳 — `def f(x: int) -> str`·`n: int = 0`·클래스 몸통의 `a: int`.
* 메모가 남는 곳 — **`__annotations__`** 라는 dict.
* 메모를 읽는 사람 — **타입 검사기**(이 머신에 없다)와 **몇몇 라이브러리**(`dataclass`·`NamedTuple`·`singledispatch`).

```text
   def f(x: int) -> str:            인터프리터                       __annotations__
       return x                          |                          {'x': int, 'return': str}
                                         v                                ^
   f("문자열")          ------->  메모를 안 읽고 실행한다  --------------+   메모는 남아 있다
                                  -> "문자열" 을 돌려준다                    (누구든 읽을 수 있다)

   ★ 실행은 한 글자도 안 바뀐다. 바뀌는 곳은 "메모를 읽는 라이브러리" 뿐이다
   ★ TS 는 메모를 배송 전에 떼어 버린다 (방출된 .js 에 없다). 파이썬은 붙인 채 보낸다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 내용물 메모 | 어노테이션(타입 힌트) | 소스의 `: int`·`-> str` |
| 메모를 안 읽고 나르는 기사 | 인터프리터 | `f("문자열")` 이 그냥 돈다 |
| 상자에 붙은 채 남은 메모 | `__annotations__` | 딕셔너리로 읽힌다 |
| ★ 메모를 **글씨 그대로** 붙이기 | `from __future__ import annotations` | 값이 **문자열**이 된다 |
| 글씨로 붙은 메모를 **해독**하기 | `typing.get_type_hints` · `inspect.get_annotations(eval_str=True)` | 문자열을 **평가해** 되살린다 |
| ★ 메모를 읽고 **포장을 바꾸는** 창고 | `dataclass`·`NamedTuple`·`singledispatch` | 어노테이션이 **있고 없음**으로 결과가 바뀐다 |
| 메모를 보고 틀린 상자를 골라내는 검수원 | 타입 검사기 | ★ **이 머신에 없다**(못 잰 것) |
| 메모를 **꺼낼 때 비로소 쓰는** 방식 | 3.14 지연 평가 | ★ **이 머신에 없다**(문서만) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`def save(user_id: int)` 인데 문자열 `"42"` 가 들어와 DB 에서 터진다**」와
「**`from __future__ import annotations` 를 한 줄 넣었더니 `singledispatch` 등록이 `NameError` 로 깨진다**」가 그것이다.\
앞엣것은 **메모를 검수원으로 착각한 것**이고, 뒤엣것은 **메모를 읽는 창고가 글씨를 해독하다 실패한 것**이다.

> **어노테이션(annotation)** — `:` 뒤나 `->` 뒤에 붙이는 식. **타입 힌트**라고도 부른다.\
> 예: `def f(x: int) -> str` 의 `int` 와 `str`.

> **`__annotations__`** — 함수·클래스·모듈이 어노테이션을 담아 두는 **dict**.\
> 예: `f.__annotations__` 는 `{'x': <class 'int'>, 'return': <class 'str'>}`.

> **문자열화(stringized) 어노테이션** — 식을 **평가하지 않고 소스 글자 그대로** 담은 것.\
> 예: `from __future__ import annotations` 아래에서 `f.__annotations__['x']` 는 `'int'`.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 「기본 대 `__future__`」 격자 창이다.** 같은 탐침 열 개를 **두 모드로 컴파일해** 돌리고
**갈린 칸을 스크립트가 센다.** 그리고 **같은 격자를 3.11 에서 한 번 더** 돌려 판 격자의 두 열을 채운다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **기본 대 `__future__` 격자** | 모드가 **무엇을 바꾸나** — `__annotations__`·`NameError`·라이브러리 | 3.14 |
| ② ★★★ **평가 시각 창**(부작용 있는 어노테이션) | 어노테이션 식이 **언제 도나 · 도나 안 도나** | 값이 무엇인가 |
| ③ ★★ **`get_type_hints` / `inspect.get_annotations`** | 문자열을 **되살릴 수 있나** | — |
| ④ ★★ **「힌트 있음 / 없음」 격자** | 어노테이션이 **실행을 바꾸는 자리** | 검사기의 판정 |
| ★ **못 잰 것** — 3.14 지연 평가 | — | ★★★ `python3.14` 가 `None` · `annotationlib` 이 `ModuleNotFoundError` |
| ★ **못 잰 것** — 타입 검사기 판정 | — | ★★★ 다섯 도구 전부 없음([35번](../35-abc-and-protocol/2-summary.md)·[38번](../38-namedtuple-and-typeddict/2-summary.md)) |
| ★ **부적용인 창** — 속도 | — | 「힌트가 느리게 한다·빠르게 한다」를 **한 번도 재지 않았다** |

★★ **②가 이 주제의 네 번째 창이다.** 값 창(①③)은 **「무엇이 담겼나」** 만 말하고 **「언제 평가됐나」** 는 말하지 않는다.
어노테이션 자리에 **부르면 한 줄을 찍는 함수**를 넣으면 **평가 시각이 출력 순서로** 드러난다.
★ 그 창이 「**지역 변수 어노테이션은 아예 평가되지 않는다**」를 잡았다(동작 1 의 ③) — 값 창으로는 원리상 안 보인다(담기지도 않으므로).

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「3.14 에서는 어노테이션이 언제 평가되나」를 **실행으로 물을 수 없어서**, **이 판에 그 장치가 있나**를 물었다 —
`import annotationlib` 이 **`ModuleNotFoundError`** 이고 `__future__.annotations` 의 **의무 판이 `None`** 이다(첫 블록).
★ 바꾼 창이 못 보는 것 — **3.14 의 실제 동작 전부.** 판 격자의 3.14 열은 **문서 문장**이지 실측이 아니다.

먼저 판을 박아 둔다.

```python
# e40_version.py
import __future__
import shutil
import sys

print("version_info   =", sys.version_info)
print("implementation =", sys.implementation.name)
feat = __future__.annotations
print("__future__.annotations 선택 판   :", feat.getOptionalRelease())
print("__future__.annotations 의무 판   :", feat.getMandatoryRelease())
try:
    import annotationlib
    print("annotationlib 을 import 했다")
except ImportError as exc:
    print("import annotationlib ->", type(exc).__name__ + ":", exc)
print("PATH 의 python3.14 :", shutil.which("python3.14"))
```

```text
===== python3 - <e40_version.py =====
version_info   = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
__future__.annotations 선택 판   : (3, 7, 0, 'beta', 1)
__future__.annotations 의무 판   : None
import annotationlib -> ModuleNotFoundError: No module named 'annotationlib'
PATH 의 python3.14 : None
(exit 0)
```

```text
===== python3.11 - <e40_version_py311.py =====
version_info   = sys.version_info(major=3, minor=11, micro=15, releaselevel='final', serial=0)
implementation = cpython
__future__.annotations 선택 판   : (3, 7, 0, 'beta', 1)
__future__.annotations 의무 판   : None
import annotationlib -> ModuleNotFoundError: No module named 'annotationlib'
PATH 의 python3.14 : None
(exit 0)
```

★★ **두 판 모두 `annotationlib` 이 없고 `python3.14` 도 없다** — 3.14 쪽은 **못 잰 것**이다.\
★ `__future__.annotations` 의 **선택 판**(쓸 수 있게 된 판)은 `3.7.0b1`, **의무 판**(기본이 되는 판)은 **`None`** — **「언젠가 기본이 된다」가 아니라 「정해지지 않았다」** 다.
(3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e40_version_py311.py` 다.)

## 이 주제가 답하려는 질문

1. ★★★ **힌트는 정말 실행을 안 바꾸나** — 무엇이 안 바뀌고, **바뀌는 예외 자리**는 어디인가.
2. ★★ **`__annotations__` 는 무엇을 담나** — 기본 판 / `from __future__ import annotations` 판 / 3.14. 그리고 **언제** 담나.
3. **문자열이 된 어노테이션을 어떻게 되살리나** — `get_type_hints` 와 `inspect.get_annotations`, 그리고 되살릴 수 없을 때.

★ 첫째가 이 주제의 인출 목표다.
**「실행은 안 바뀐다」와 「어노테이션을 읽는 라이브러리의 결과는 바뀐다」를 격자 두 장으로 가를 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 힌트는 실행을 안 바꾼다 — 그리고 언제 평가되나

**언제 쓰나** — 이 주제의 출발점. 「`x: int` 라고 썼는데 왜 문자열이 들어오지」가 막힐 때.

```text
   def g(a: tag("매개변수")) -> tag("반환"):     <-- def 문이 실행될 때 두 식이 돈다
       b: tag("지역 변수") = 1                   <-- ★ 한 번도 안 돈다 (지역 변수 어노테이션)
       return b

   class K:
       k: tag("클래스 변수")                      <-- class 몸통이 실행될 때 돈다
                                                     그런데 K.k 라는 속성은 안 생긴다

   n: int = "숫자 아님"                          <-- 값은 그대로 들어간다
   m: int                                       <-- ★ 이름 m 은 안 생긴다 (어노테이션만)
```

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

그림 해설.

* ★★★ **①** — `x: int` 인 함수에 `5`·`'문자열'`·`[1, 2]` 를 넣어 **전부 그대로 돌아왔다.** `-> str` 도 확인되지 않는다.
  ★ 문서 문장 — *"The Python runtime does not enforce function and variable type annotations."*
* ★★ **②** — `n: int = "숫자 아님"` 이 **그대로 들어갔다.** 그리고 **값 없이 `m: int` 만 쓰면 이름 `m` 이 생기지 않는다**
  (`'m' in globals()` 가 `False`). 그런데 모듈의 **`__annotations__` 에는 `'m'` 이 있다** — **메모만 붙고 상자는 없다.**
* ★★★ **③이 네 번째 창이다** — 출력 순서를 읽는다.
  `def 직전` 과 `def 직후` 사이에 **`매개변수`·`반환` 두 줄**이 찍혔다 — **`def` 문이 실행될 때 평가된다.**
  ★★ **`g 안의 지역 변수` 는 끝까지 한 번도 안 찍혔다** — `g(1)` 을 불렀는데도. **지역 변수 어노테이션은 평가되지 않는다.**
  ★ `class 몸통 시작` 과 `끝` 사이에 `K 의 클래스 변수` 가 찍혔다 — 클래스 어노테이션은 **몸통이 실행될 때** 평가된다.
  그런데 **`'k' in vars(K)` 가 `False`** — 값이 없으니 **속성은 안 생겼고 `__annotations__` 에만** 있다.

**비용** — 기본 판에서는 **`def` 할 때마다 어노테이션 식이 평가된다.** 그 비용과 **「아직 정의 안 된 이름을 못 쓴다」** 가
`from __future__ import annotations`(동작 2)와 3.14 지연 평가(동작 3)가 나온 이유다. ★ 이 비용의 크기는 **재지 않았다.**

### 2. ★★★ `from __future__ import annotations` — 전부 문자열이 된다

**언제 쓰나** — 아직 정의 안 된 클래스를 힌트에 쓰고 싶을 때(전방 참조). 그리고 「한 줄 넣었더니 뭐가 깨졌지」가 막힐 때.

```text
   기본 판                                  from __future__ import annotations 판

   def f(x: int, y: "int", z: list[int])     (같은 소스 + 맨 위 한 줄)
   x -> <class 'int'>        (평가된 값)      x -> 'int'          (글자 그대로)
   y -> 'int'                (원래 문자열)     y -> "'int'"        ★ 따옴표가 한 겹 더
   z -> list[int]            (평가된 값)      z -> 'list[int]'
   def g(x: Undefined)  -> NameError         -> 통과 ('Undefined' 가 담긴다)

   get_type_hints(f)  -> 두 판 모두 같은 값으로 되살린다
```

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

그림 해설.

* ★★★ **①** — 기본 판은 **평가된 객체**(`int` 클래스 · `list[int]` 라는 `GenericAlias`)를 담고, `__future__` 판은 **전부 `str`** 이다.
  ★★ **`y: "int"` 는 `"'int'"`** 가 됐다 — 이미 문자열인 것을 **한 번 더 문자열로** 싼다. 문서가 *"quoted twice"* 라 적은 그대로다.
* ★★★ **②** — **정의 안 된 이름 `Undefined`** 를 힌트에 쓴 `def` 가 기본 판은 **`NameError: name 'Undefined' is not defined`**,
  `__future__` 판은 **통과**해 `'Undefined'` 를 담는다. **`def` 할 때 평가를 안 하니 이름이 없어도 모른다.**
* ★★ **③** — `get_type_hints(f)` 는 **두 판 모두 같은 값**을 준다. `__future__` 판의 **문자열을 평가해 되살린 것**이다(동작 5).
  ★ `'return': None` 이 **`<class 'NoneType'>`** 으로 바뀌어 나오는 것도 두 판 공통이다 — `get_type_hints` 가 `None` 을 **타입으로** 바꿔 준다.

**비용** — `__future__` 는 **정의 시점의 평가 비용과 전방 참조 문제를 없애는** 대신,
**어노테이션을 실행 중에 읽는 코드에 문자열을 넘긴다** — 그 코드가 되살리지 못하면 깨진다(동작 4).

### 3. ★★★ 판 격자 — 3.11 · 3.12 는 재고, 3.14 는 문서로

**언제 쓰나** — 라이브러리가 여러 판을 지원할 때. **「이 판에서 `__annotations__` 가 무엇을 주나」** 가 판에 달렸다.

| | 3.11 기본 | 3.11 `__future__` | 3.12 기본 | 3.12 `__future__` | ★ 3.14 기본(PEP 649) |
|---|---|---|---|---|---|
| 어노테이션 식을 **`def` 때** 평가 | 한다(1회) | 안 한다(0회) | 한다(1회) | 안 한다(0회) | ★ **안 한다 — 필요할 때** (문서) |
| **정의 안 된 이름** 힌트의 `def` | `NameError` | 통과 | `NameError` | 통과 | ★ 통과 (문서 — 전방 참조에 따옴표 불필요) |
| `__annotations__['x']` | `int` 클래스 | `'int'` | `int` 클래스 | `'int'` | ★ **못 잰 것** |
| 되살리는 도구 | `get_type_hints` 등 | 같음 | 같음 | 같음 | ★ `annotationlib` 의 `VALUE`·`FORWARDREF`·`STRING` (문서) |
| **근거** | 실측(아래 둘째 블록) | 실측 | 실측(아래 첫 블록) | 실측 | ★★ **문서만 — 이 머신에 3.14 가 없다** |

★★★ **3.14 열은 한 칸도 실측이 아니다.** What's New 문장 — *"annotations are no longer evaluated eagerly. Instead, annotations are stored in special-purpose annotate functions and evaluated only when necessary (except if `from __future__ import annotations` is used)."*
★ 같은 문서가 **`__annotations__` 를 읽는 코드가 영향을 받을 수 있다**고 적고 이식 절로 넘긴다 — 그 칸을 「못 잰 것」으로 둔 이유다.

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

그림 해설.

* ★★★ **마지막 줄 — `갈린 칸 7 / 10`**, 그리고 **3.11 과 3.12 가 한 글자도 같다.**
  (3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e40_grid_py311.py` 다.)
  ★ 그래서 판 격자에서 **3.11 과 3.12 는 같은 열 둘**이다 — 판이 갈리는 자리는 **3.14** 다.
* ★★ **갈린 일곱** — `__annotations__` 값(`int` ↔ `'int'`) · 정의 안 된 이름(`NameError` ↔ 통과) · 평가 횟수(`1` ↔ `0`) ·
  클래스 몸통 · **dataclass 의 `Field.type`**(`int` ↔ `'int'`) · **`NamedTuple` 의 `__annotations__`**(`int` ↔ **`ForwardRef('int')`**) ·
  **`singledispatch` 지역 클래스**(`'Local'` ↔ **`NameError`**).
* ★★ **안 갈린 셋** — dataclass 의 **`ClassVar` 제외**(두 모드 다 `['a']`) · `get_type_hints` · **`f('s')` 가 `'s'` 를 돌려주는 것.**
  ★★★ **마지막 행이 이 주제의 결론이다 — 모드를 바꿔도 실행은 안 바뀐다.** 바뀌는 것은 **어노테이션을 읽는 쪽**뿐이다.
* ★ **`NamedTuple` 은 문자열을 `ForwardRef` 로 싸서** 담는다 — 같은 모드에서 **dataclass 는 문자열 그대로**다.
  **라이브러리마다 받는 모양이 다르다**(CPython 구현).
* ★★ **dataclass 의 `ClassVar` 제외가 `__future__` 에서도 됐다** — 문자열 `'ClassVar[int]'` 을 **글자로 알아보는** 처리가 있다는 뜻이다 — 설치본 `dataclasses.py` 의 `_is_type` 이 **정규식으로 모듈 이름과 `ClassVar` 를 읽는다**(CPython 구현).

> ★★ **격자를 만들다 생긴 가짜 갈림 — 기록해 둔다.** 처음 판은 탐침을 `exec(…, 빈 dict)` 로 돌렸는데,
> `__future__` 쪽 dataclass 두 칸이 **`AttributeError`** 로 나왔다. dataclass 가 문자열 어노테이션을 읽을 때
> **`sys.modules.get(cls.__module__).__dict__`** 로 모듈을 찾는데(설치본 `dataclasses.py`), 빈 dict 로 만든 탐침은 **그 모듈이 `sys.modules` 에 없어 `None.__dict__` 가 됐다.**
> 탐침마다 **진짜 모듈 객체를 만들어 `sys.modules` 에 올리자** 두 칸이 `'int'`·`['a']` 로 바뀌었고 **갈린 칸이 8 에서 7 로** 줄었다.
> 실제 파일로 던진 `e40_future.py` 는 처음부터 문제가 없었다 — **탐침 도구가 만든 갈림**이었다. **값도 그럴듯하고 예외도 그럴듯해서 격자 숫자만 보면 안 걸린다.**

**비용** — 판이 오르면 **`__annotations__` 를 직접 읽는 코드가 먼저 깨진다.** 문서가 3.10+ 에서 **`inspect.get_annotations()`** 를 권하는 이유다.

### 4. ★★★ 힌트가 실행을 바꾸는 예외 자리 — 어노테이션을 읽는 장치들

**언제 쓰나** — 「힌트는 실행을 안 바꾼다」를 믿고 어노테이션을 지웠더니 **동작이 바뀌었을 때.**

```text
   같은 몸통에서 어노테이션만 지운다

   @dataclass class D: a: int = 1   ->   a = 1        필드 ['a']  ->  []      ★ 필드가 사라진다
   class N(NamedTuple): a: int = 1  ->   a = 1        ('a',)     ->  ()
   class T(TypedDict): a: int       ->   (비움)        ['a']      ->  []
   @s.register def _(x: int)        ->   def _(x)     'int'      ->  TypeError  ★ 등록이 안 된다
   class E(Enum): A = 1; b: int     ->   A = 1        ['A']      ->  ['A']      (멤버에 안 끼친다)
   class P: a: int = 1              ->   a = 1        1          ->  1          (아무 일도 없다)
```

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

그림 해설.

* ★★★ **마지막 줄 — `힌트가 결과를 바꾼 칸 4 / 6`.** 여섯 장치 중 **넷**에서 어노테이션이 **있고 없음**이 결과를 바꿨다.
* ★★★ **dataclass** — 어노테이션을 지우면 **필드가 사라진다**(`['a']` → `[]`). `a = 1` 은 **그냥 클래스 변수**다.
  ★★ [36번](../36-dataclasses/2-summary.md)이 먼저 적은 「**절반만 예외**」가 이것이다 — **구조를 만드는 데는 어노테이션을 쓰고, 값을 검사하는 데는 안 쓴다**
  (동작 3 의 격자에서 `f('s')` 처럼 dataclass 도 `x: int` 에 문자열을 받는다 — [38번](../38-namedtuple-and-typeddict/2-summary.md)의 격자 마지막 행).
* ★★ **`NamedTuple`·`TypedDict`** — 필드·키 목록이 **어노테이션에서** 온다. 지우면 빈다.
* ★★ **`singledispatch`** — `@s.register` 가 **첫 인자의 어노테이션을 읽어** 어느 타입에 등록할지 정한다. 지우면 **`TypeError`** 다.
  ★ 그래서 **동작 3 의 격자에서 `__future__` 가 `singledispatch` 를 깨뜨렸다** — 문자열 `'Local'` 을 되살리려는데 **지역 클래스는 모듈 전역에 없어서** `NameError`.
* ★ **`Enum`** — 몸통의 `b: int` 는 **멤버가 아니다**(`['A']` 그대로). **보통 클래스**는 아무 일도 없다.

**비용** — 이 장치들은 **어노테이션을 설정 파일처럼** 쓴다. 대가는 **「힌트는 주석과 같다」가 이 코드에서는 틀린 말**이 된다는 것 —
그리고 **`__future__`·3.14 처럼 어노테이션의 모양을 바꾸는 판·모드에 민감해진다**(동작 3).

### 5. ★★ 문자열을 되살리기 — `get_type_hints` 와 `inspect.get_annotations`

**언제 쓰나** — 실행 중에 힌트를 읽는 코드를 쓸 때. **`__annotations__` 를 직접 읽지 말고** 이 둘 중 하나를 쓴다.

```text
   __annotations__                    {'items': 'list[Node]', 'limit': None, 'return': 'int'}   글자 그대로
        |
        +-- inspect.get_annotations(f)               -> 같다 (평가 안 함)
        +-- inspect.get_annotations(f, eval_str=True) -> 문자열만 평가. None 은 None 그대로
        +-- typing.get_type_hints(f)                  -> 문자열 평가 + None 을 NoneType 으로

   'Missing' 처럼 되살릴 이름이 없으면  -> 둘 다 NameError
```

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

그림 해설.

* ★ **①** — `__annotations__` 는 **적힌 그대로**다. 문자열로 적은 것은 문자열, `None` 은 `None`.
* ★★ **②** — `get_type_hints` 는 문자열 `'list[Node]'`·`'Node | None'` 을 **평가해** 실제 객체로 되살린다.
  ★ 그리고 **`None` 을 `NoneType` 으로** 바꾼다(`'limit': <class 'NoneType'>`).
* ★★ **③** — `inspect.get_annotations` 는 기본이 **평가 안 함**, `eval_str=True` 라야 문자열을 평가한다.
  ★ **`None` 은 `None` 그대로 둔다** — 두 함수가 **같은 일을 하지 않는다.** 이 한 칸이 그 차이다.
* ★★★ **④** — 되살릴 이름이 없으면 **둘 다 `NameError: name 'Missing' is not defined`**.
  ★ 그런데 **`broken('아무거나')` 는 그냥 돈다** — 어노테이션이 틀려도 **실행은 안 바뀐다.** 깨지는 것은 **읽는 쪽**뿐이다.

**비용** — 되살리기는 **`eval` 이다.** 모듈 전역에서 이름을 찾으므로 **지역에만 있는 이름은 못 찾는다**(동작 4 의 `singledispatch`).

### 6. ★★ TS 와 견주면 — 사라지나 남나

```text
                         실행 중 힌트             실행이 바뀌나            힌트를 읽는 코드
   TypeScript            ★ 방출된 .js 에 없다      안 바뀐다                 없다 (읽을 게 없다)
   Python (기본)          __annotations__ 에 객체    안 바뀐다                 dataclass · singledispatch …
   Python (__future__)    __annotations__ 에 문자열  안 바뀐다                 되살려서 읽는다
```

* ★★★ **TS 는 사라지고 파이썬은 남는다.** [TS 01번](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md)이 **방출된 `.js` 전문**으로
  `: User`·`: string`·`interface`·`as User` 가 **한 글자도 안 남는 것**을 보였다(TS [19번](../../../ts/syntax/19-generics-basics/2-summary.md)·[23번](../../../ts/syntax/23-typeof-type-operator/2-summary.md)도 방출물로 같은 것을 확인했다).
  파이썬은 **`__annotations__` 라는 dict 로 남긴다**(동작 1).
* ★★ **그래서 파이썬에만 「힌트를 읽어 동작을 바꾸는 코드」가 있다**(동작 4). TS 는 **읽을 것이 없어서** 그런 코드가 원리상 없다 —
  TS 01번은 그 대신 **데코레이터 메타데이터**를 방출하게 하는 옵션(`emitDecoratorMetadata`)을 **TS 갈래 목록의 47번**으로 넘겨 두었다.
* ★ **공통점** — 두 언어 모두 **실행은 안 바뀐다.** TS 는 **지워서**, 파이썬은 **안 읽어서**.

## 문법 — 형태와 규칙

**형태**

```text
def f(x: int, *args: str, key: "Node" = None, **kw: float) -> list[int]: ...
#      매개변수         가변 위치       문자열(전방 참조)   가변 키워드       반환

n: int = 0          # 모듈·클래스: 평가되고 __annotations__ 에 담긴다. 값이 없으면 이름은 안 생긴다
class C:
    a: int          # 클래스 __annotations__ 에 담긴다. 속성은 안 생긴다
def g():
    b: int = 1      # ★ 지역 변수 어노테이션 — 평가도 저장도 안 된다

from __future__ import annotations    # ★ 파일 맨 위에만. 그 파일의 어노테이션이 전부 문자열이 된다
```

```text
진단 — 어노테이션을 읽는 세 길

f.__annotations__                         적힌 그대로 (기본 판은 객체, __future__ 판은 문자열)
inspect.get_annotations(f, eval_str=True) 3.10+ 권장. 문자열만 평가한다
typing.get_type_hints(f)                  문자열 평가 + None -> NoneType · Annotated 를 벗긴다
```

규칙 열.

1. ★★★ **런타임은 어노테이션을 강제하지 않는다** — `x: int` 에 무엇이든 들어간다.
2. ★★ **기본 판에서 매개변수·반환 어노테이션은 `def` 가 실행될 때** 평가된다.
3. ★★ **지역 변수 어노테이션은 평가되지 않는다** — 담기지도 않는다.
4. ★ **값 없는 `m: int`** 는 이름을 만들지 않는다 — `__annotations__` 에만 남는다.
5. ★★★ **`from __future__ import annotations`** 는 그 파일의 어노테이션을 **전부 문자열**로 만든다. 이미 문자열이면 **따옴표가 한 겹 더**.
6. ★★ 그 아래에서는 **정의 안 된 이름**을 힌트에 써도 `def` 가 통과한다.
7. ★★ **`get_type_hints`·`inspect.get_annotations(eval_str=True)`** 가 문자열을 되살린다 — 이름이 없으면 `NameError`.
8. ★★★ **어노테이션을 읽는 장치**(`dataclass`·`NamedTuple`·`TypedDict`·`singledispatch`)에서는 **힌트가 결과를 바꾼다**(4 / 6).
9. ★★ **`__future__` 는 그 장치들이 받는 모양을 바꾼다** — `'int'` · `ForwardRef('int')` · 되살리기 실패(`NameError`).
10. ★ **3.14 는 기본이 지연 평가**다(문서) — ★ **이 머신에서 못 잰 것.**

## 어디서 틀리나

### (1) ★★★ 「타입 힌트를 달았으니 틀린 타입은 막힌다」

**안 막힌다**(동작 1 의 ①). 막는 것은 **타입 검사기**이고, **이 머신에 없어 무엇을 잡는지 못 쟀다.**

### (2) ★★★ 「힌트는 주석과 같아서 지워도 된다」

**어노테이션을 읽는 장치에서는 아니다**(동작 4 — 4 / 6). dataclass 필드가 사라지고 `singledispatch` 등록이 `TypeError` 가 된다.

### (3) ★★★ `from __future__ import annotations` 를 「안전한 한 줄」로 넣는다

**어노테이션을 실행 중에 읽는 코드에 문자열이 간다**(동작 3 — 7 / 10). 되살리지 못하면 **`NameError`**(지역 클래스의 `singledispatch`).

### (4) ★★ `__annotations__` 를 직접 읽는다

판·모드에 따라 **객체**일 수도 **문자열**일 수도 있고, 3.14 에서는 **또 달라진다**고 문서가 적는다.\
★ 3.10+ 에서는 **`inspect.get_annotations()`** 가 문서의 권장이다.

### (5) ★★ `get_type_hints` 와 `inspect.get_annotations(eval_str=True)` 를 같은 것으로 안다

**`None` 을 다르게 준다**(동작 5 의 ②·③) — 앞은 `NoneType`, 뒤는 `None`.

### (6) ★ 지역 변수 어노테이션으로 무언가를 기록하려 한다

**평가도 저장도 안 된다**(동작 1 의 ③).

### (7) ★ `m: int` 만 쓰고 `m` 을 읽는다

**`NameError`** 다 — 이름이 안 생겼다(동작 1 의 ②).

### (8) ★★ 「3.14 에서는 이렇게 된다」를 확인한 것처럼 적는다

★ **이 머신에서 못 잰 것**이다. 판 격자의 3.14 열은 **문서 문장**이다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스·PEP·`typing` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **모듈 계약** | `dataclasses`·`typing`·`functools` 가 어노테이션을 어떻게 쓰나 | 문서 · 실행 |
| **CPython 구현** | 그 모듈들이 문자열을 **어떤 모양으로** 받나 | 실행 |
| **이 판(3.12.3 · 3.11.15)의 관찰** | 이 판에서 그랬을 뿐 | 예외 문구 |
| ★ **못 잰 것** | 3.14 의 실제 동작 · 타입 검사기의 판정 | ★★★ 도구·판이 없다 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 런타임은 어노테이션을 **강제하지 않는다** | `typing` 첫머리 |
| `from __future__ import annotations` 는 어노테이션을 **문자열로** 담는다 | PEP 563 · Annotations HOWTO |
| 이미 문자열이면 **두 번 따옴표** | HOWTO — *"quoted twice"* |
| 지역 변수 어노테이션은 **평가되지 않는다** | PEP 526 |
| 3.14 기본은 **지연 평가** | What's New 3.14 — ★ 이 머신에서는 **못 잰 것** |
| `from __future__` 는 **파일 맨 위**에만 | 레퍼런스(future 문) |

### 모듈 계약

| 사실 | 근거 |
|---|---|
| dataclass 는 **어노테이션 있는 이름만** 필드로 모은다 | `dataclasses` 문서 · [36번](../36-dataclasses/2-summary.md) |
| `NamedTuple`·`TypedDict` 의 필드·키는 **어노테이션에서** 온다 | `typing` 문서 |
| `singledispatch.register` 는 **첫 인자의 어노테이션**을 읽는다 | `functools` 문서 |
| `get_type_hints` 는 **문자열을 평가하고 `None` 을 `NoneType` 으로** | `typing` 문서 |
| `inspect.get_annotations(eval_str=True)` 가 **문자열만** 평가한다 | `inspect` 문서 · HOWTO |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★ `__future__` 아래 `NamedTuple` 이 **`ForwardRef('int')`** 로 담는다 | 실행(격자) |
| ★ `__future__` 아래 dataclass 는 **`'int'` 문자열 그대로** 담는다 | 실행(격자) |
| ★ dataclass 가 문자열 어노테이션을 읽을 때 **`sys.modules.get(cls.__module__)`** 로 모듈을 찾는다 | 실행 — 가짜 갈림이 그것을 드러냈다(동작 3 의 인용 블록) |
| `__future__.annotations` 의 **의무 판이 `None`** | 실행(첫 블록) |

### 그래서 이렇게 적으면 틀린다

* ✗ 「타입 힌트는 실행을 절대 안 바꾼다」\
  ○ **힌트를 읽는 장치에서는 바꾼다**(4 / 6). 안 바뀌는 것은 **힌트를 받은 함수의 실행**이다.
* ✗ 「`from __future__ import annotations` 는 언젠가 기본이 된다」\
  ○ **의무 판이 `None`** 이다(이 판의 `__future__` 모듈). 그리고 3.14 는 **다른 방식(지연 평가)** 을 기본으로 했다(문서).
* ✗ 「3.14 에서 확인했다」\
  ○ ★ **못 잰 것**이다. `python3.14` 가 이 머신에 없다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 문서·IDE·검사기를 위한 힌트 | ★ 그냥 쓴다 | 실행은 안 바뀐다 |
| 전방 참조가 많다 | 따옴표로 감싼 문자열 힌트 · 또는 `__future__` | 기본 판에서 `NameError` 를 피한다 |
| **dataclass·`singledispatch`·런타임 검증 라이브러리**를 쓰는 파일 | ★ `__future__` 를 넣기 전에 **격자로 확인** | 받는 모양이 바뀐다(동작 3) |
| 실행 중에 힌트를 읽는 코드를 쓴다 | `inspect.get_annotations` 또는 `get_type_hints` | `__annotations__` 를 직접 읽지 않는다 |
| 값이 정말 그 타입인지 **실행 중에** 보장해야 한다 | 직접 쓴 검사 · 검증 라이브러리 | 런타임은 **안 본다** |

## 핵심 문장

1. **힌트는 실행을 안 바꾼다** — `x: int` 에 무엇이 와도 함수는 돈다. `from __future__` 를 넣어도 이 행은 안 갈렸다.
2. **힌트는 사라지지 않는다** — `__annotations__` 에 남아, **읽는 장치**(dataclass·`NamedTuple`·`TypedDict`·`singledispatch`)에서는 결과를 바꾼다(4 / 6).
3. **기본 판은 `def` 때 평가하고, `__future__` 판은 문자열로 담는다** — 지역 변수 어노테이션은 어느 쪽이든 평가되지 않는다.
4. **`__future__` 는 읽는 쪽이 받는 모양을 바꾼다** — 격자 **7 / 10** 이 갈렸고 **3.11 과 3.12 가 한 글자도 같았다.**
5. **3.14 의 지연 평가와 타입 검사기의 판정은 이 머신에서 못 잰 것이다** — 문서 문장으로만 적었다.

## 관련 자료

* 선행: [19-function-argument-rules](../19-function-argument-rules/2-summary.md) — ★ **경계**: 매개변수 종류는 그쪽, 여기는 **그 자리에 붙은 어노테이션이 언제 평가되나**만.
* 선행: [36-dataclasses](../36-dataclasses/2-summary.md) — ★★★ **「어노테이션을 읽지만 값은 안 본다」의 실측이 그쪽**이고, 이 주제의 예외 격자 첫 행이 그것이다.
  그 편이 「더 들어가면」에서 **`__future__` 를 쓰면 `f.type` 이 문자열이 된다**고 예고했다 — 동작 3 의 격자가 **3.11·3.12 에서 실측**했다.
* 선행: [38-namedtuple-and-typeddict](../38-namedtuple-and-typeddict/2-summary.md) — 「런타임이 **쓴다 / 들고만 있다 / 검사기만 쓴다**」 세 칸의 표가 그쪽이다.
* 선행: [35-abc-and-protocol](../35-abc-and-protocol/2-summary.md) — 검사기 부재 판정.
* 이어지는 곳: 목록의 **41번 주제** 「`typing` 과 제네릭 신문법」 — `X | Y`·PEP 695 `type` 문.
  ★ 동작 5 의 `'Node | None'` 은 **문자열로 적었기에** 어느 판에서든 `def` 가 통과했다.
* 대비: [TS 01번 — 더하는 것과 지우는 것](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md) ·
  [TS 19번](../../../ts/syntax/19-generics-basics/2-summary.md) · [TS 23번](../../../ts/syntax/23-typeof-type-operator/2-summary.md) —
  **경계**: 방출물 실측은 전부 그쪽이고 여기서는 인용만 했다.
* 공식 문서: [`typing`](https://docs.python.org/3.12/library/typing.html) ·
  [Annotations Best Practices](https://docs.python.org/3.12/howto/annotations.html) ·
  [What's New 3.14 — PEP 649·749](https://docs.python.org/3.14/whatsnew/3.14.html) ·
  [PEP 563](https://peps.python.org/pep-0563/) · [PEP 526](https://peps.python.org/pep-0526/) · [PEP 649](https://peps.python.org/pep-0649/)

## 용어 풀이

* **어노테이션(annotation)** / **타입 힌트**: `:`·`->` 뒤에 붙이는 식. 런타임은 **강제하지 않는다.**
* **`__annotations__`**: 어노테이션을 담는 dict. 함수·클래스·모듈에 있다.\
  예: 값 없는 `m: int` 도 모듈의 `__annotations__` 에는 들어간다.
* **즉시 평가(eager evaluation)**: `def`·`class` 가 실행될 때 어노테이션 식을 **곧바로** 평가하는 것. 3.13 까지의 기본.
* **문자열화(stringized)**: 식을 평가하지 않고 **소스 글자**로 담는 것. `from __future__ import annotations` 의 효과.\
  예: `x: int` → `'int'`.
* **전방 참조(forward reference)**: **아직 정의되지 않은 이름**을 힌트에 쓰는 것.\
  예: 클래스 안에서 자기 클래스를 `"Node"` 로 적는 것.
* **`ForwardRef`**: 전방 참조를 담는 `typing` 의 객체.\
  예: `__future__` 아래 `NamedTuple` 의 `__annotations__['a']` 가 `ForwardRef('int')`.
* **`get_type_hints`**: 어노테이션을 **평가해 되살려** 주는 `typing` 함수. `None` 을 `NoneType` 으로 바꾼다.
* **`inspect.get_annotations`**(3.10+): 어노테이션을 읽는 **권장** 함수. `eval_str=True` 로 문자열만 평가한다.
* **지연 평가(deferred evaluation)**(3.14, PEP 649): 어노테이션을 **필요할 때** 평가하는 방식. ★ **이 머신에서 못 잰 것.**
* **`annotationlib`**(3.14): 지연된 어노테이션을 `VALUE`·`FORWARDREF`·`STRING` 세 형식으로 꺼내는 모듈. ★ **이 판에는 없다**(`ModuleNotFoundError`).
* **`singledispatch`**: 첫 인자의 **타입**에 따라 다른 함수를 부르는 장치. `register` 가 **어노테이션을 읽어** 타입을 정한다.

## 더 들어가면

* ★ **`typing.Annotated[int, "메타데이터"]`** — 타입에 **임의의 메타데이터**를 붙인다. `get_type_hints` 는 기본적으로 벗기고
  `include_extras=True` 면 남긴다 — [38번](../38-namedtuple-and-typeddict/2-summary.md)의 `NotRequired` 가 같은 규칙을 탔다(그 편 동작 3 의 ⑥).
* ★ **런타임 검증 라이브러리**는 전부 **어노테이션을 읽는 장치**다 — 동작 4 의 표에 한 줄 더 붙는 쪽이다.
  「런타임은 안 본다」의 예외가 아니라 **그 빈자리를 채우는 제3자**다([38번](../38-namedtuple-and-typeddict/2-summary.md)과 같은 말).
* ★ **3.14 를 설치하게 되면 다시 돌릴 것** — 동작 1 의 ③(평가 시각 창)과 동작 3 의 격자. 문서대로면 **기본 열의 `def` 때 평가 횟수가 0 이 되고 `NameError` 칸이 통과**가 된다 —
  ★ **이것은 예측이지 측정이 아니다.** 그때 이 절을 실측으로 바꾼다.
