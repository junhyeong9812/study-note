# python/syntax/37-enum — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [`enum` 레퍼런스(3.12)](https://docs.python.org/3.12/library/enum.html) — `auto` 의 값 규칙 · `StrEnum`·`ReprEnum` 의 *Added in version 3.11* ·
>   `__contains__` 의 *Changed in version 3.12* · `@unique` · `IntEnum` 이 정수처럼 쓰인다는 문장
> - [Enum HOWTO(3.12)](https://docs.python.org/3.12/howto/enum.html) — *"Enumeration members are compared by identity"* ·
>   *"Comparisons against non-enumeration values will always compare not equal"* · 별칭(alias) 문단 ·
>   `EnumType` 이 `__contains__`·`__dir__`·`__iter__` 를 준다는 문단 · 멤버가 싱글턴이라는 문단
> - [`json`](https://docs.python.org/3.12/library/json.html) — `default=` 훅
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 **둘**이다 — `python3` **3.12.3** 이 본판이고, 판 경계를 보려고 **`python3.11` 3.11.15** 로 두 블록을 더 던졌다.\
> ★ 던지는 형태는 `python3 - <파일` 하나로 고정했다(트레이스백이 `File "<stdin>", line N` 이 된다).\
> ★★★ **이 주제도 트레이스백을 한 블록도 싣지 않았다.** 던진 예외가 전부 `enum.py`·`json` 을 지나
> **절대 경로가 박히기** 때문이다. 전부 `except` 로 받아 **예외 타입과 메시지만** 찍었다
> ([36번](../36-dataclasses/2-summary.md)과 같은 처방).
> 3.11 의 `DeprecationWarning` 도 stderr 로 흘리지 않고 **`warnings.catch_warnings(record=True)` 로 잡아 stdout 에** 찍었다.\
> **버전** — `enum` 은 **3.4**(PEP 435)부터다. **`StrEnum`·`ReprEnum` 은 3.11** 신설이다.
> ★ `1 in Color` 처럼 **멤버가 아닌 값을 `in` 으로 묻는 것**이 **3.12 에서 바뀌었다**(동작 6 — 두 판을 실제로 돌렸다).\
> ★ **구현 대 언어 보장 한 줄** — **싱글턴·정의 순서 순회·별칭·`auto` 의 값 규칙까지가 모듈 계약**이고,
> **멤버가 클래스 `__dict__` 에 산다는 것·`hash(멤버) == hash(이름)`·예외 문구**는 CPython 쪽이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★ `hash()` 의 **숫자** — 문자열 해시는 실행마다 바뀐다. 그래서 **숫자를 한 번도 안 찍고 `==` 결과만** 찍었다 | ★★ 격자의 **참·거짓과 예외 종류** · 마지막 줄 **「갈린 칸 N / M」** |
> | 판이 오르면 예외 **문구**와 `EnumType` 이 가진 **던더 목록** | ★ **순회 순서** — 모듈 계약이 **정의 순서**를 보장한다 |
> | 판이 오르면 `DeprecationWarning` 의 **문구** | `auto()` 가 만든 **값** · `json.dumps` 의 결과 문자열 |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대 경로도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 전부 동일).\
> ★★ **순서가 보장 안 되는 출력은 하나도 없다** — `set` 을 한 번도 찍지 않았고, 멤버 목록은 **정의 순서가 보장되는 순회**로 찍었다.\
> **선행** — [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md)(★★ **클래스 속성 탐색 — 멤버가 어디서 찾아지나**) ·
> [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md)(★★ **`__eq__`/`__hash__` 계약의 정본**) ·
> [31-comparison-protocol-and-sortability](../31-comparison-protocol-and-sortability/2-summary.md)(정렬이 되는가) ·
> [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md)(`is` 와 `==`).

## 한눈에 — 쉽게 말하면

**`Enum` 은 「미리 찍어 둔 번호표 묶음」이다.** 번호표는 **딱 한 장씩만** 있고, 새로 찍을 수 없다.

* 내가 적는 것 — 클래스 몸통의 `이름 = 값` 몇 줄.
* 그것이 만드는 것 — **이름마다 객체 하나**(멤버). 클래스를 만들 때 **한 번에 다 만들고 끝**이다.
* 확인하는 법 — **`is`**(같은 한 장인가) · **`==`**(무엇과 같다고 답하나) · **`json.dumps`**(바깥으로 나갈 수 있나).

```text
   class Color(Enum):                      Color 클래스가 만들어질 때 한 번에
       RED = 1          ------------->     +-------------------+
       BLUE = 2                            | 멤버 RED  value=1 |  <- Color.RED · Color(1) · Color['RED']
                                           | 멤버 BLUE value=2 |     셋이 전부 이 한 장을 준다
                                           +-------------------+
   Color(1) is Color.RED      -> 참 (새로 안 만든다)
   Color.RED == 1             -> 거짓 (번호표는 숫자가 아니다)
   json.dumps(Color.RED)      -> 예외 (바깥 세계는 번호표를 모른다)

   ★ IntEnum · StrEnum 은 "번호표이면서 숫자·문자열이기도 한 것" — 그래서 셋째 줄부터 답이 바뀐다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 번호표 한 장 | 멤버(`Color.RED`) | `type(Color.RED)` 가 `Color` 다 |
| ★ 같은 번호표는 세상에 한 장뿐 | 싱글턴 | `Color(1) is Color.RED` |
| 번호표에 적힌 숫자 | `.value` | `Color.RED.value` |
| 번호표의 이름 | `.name` | `Color.RED.name` |
| ★ 번호표를 찍는 기계 | 메타클래스 `EnumType` | `type(Color)` |
| 같은 번호에 붙은 두 번째 이름 | 별칭(alias) | `Shape.BOX is Shape.SQUARE` |
| ★ 숫자 겸 번호표 | `IntEnum` | `== 1` 이 참 |
| ★ 글자 겸 번호표 | `StrEnum`(3.11) | `== "red"` 가 참 |
| 겹쳐 쥘 수 있는 번호표 | `Flag` | `R \| W` 가 새 조합 값이 된다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`Status.ACTIVE` 를 응답에 그대로 넣었더니 `json.dumps` 가 터진다**」와
「**DB 에서 읽은 `1` 을 `Status.ACTIVE` 와 `==` 로 비교했더니 거짓이다**」가 그것이다.\
둘 다 **평범한 `Enum` 의 번호표가 숫자가 아니기 때문**이고, `IntEnum` 은 그 둘을 **없애는 대신 다른 함정을 연다**(동작 2).

> **멤버(member)** — 열거형 클래스 몸통의 `이름 = 값` 한 줄이 만드는 객체.\
> 예: `Color.RED` 는 `int` 가 아니라 **`Color` 의 인스턴스**다.

> **싱글턴(singleton)** — 그 값을 가진 객체가 **하나만** 있는 것.\
> 예: `Color(1)` 을 몇 번 불러도 **새로 안 만들고** 이미 있는 `Color.RED` 를 준다.

> **믹스인 열거형** — `int`·`str` 을 함께 물려받아 **그 타입이기도 한** 열거형. `IntEnum`·`StrEnum` 이 그것이다.\
> 예: `isinstance(Level.LOW, int)` 가 참이다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 「무엇과 같다고 답하나」 격자 창이다.** 「`IntEnum` 은 정수와 비교된다」를 산문으로 적지 않고,
**네 종류 × 여섯 탐침**을 한 블록에서 돌려 **평범한 `Enum` 과 다른 칸을 스크립트가 센다.**

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **비교·직렬화 격자** | 종류마다 **`==`·`is`·정렬·`json`·해시가 어떻게 답하나** | 왜 그렇게 답하나 |
| ② ★★ **`is` / `copy` / `pickle`** | **한 장뿐인가** — 새로 만들어지는 길이 있나 | 값이 무엇인가 |
| ③ ★ **`__members__` 대 순회** | **별칭이 어디서 보이고 어디서 숨나** | — |
| ④ ★ **`vars(EnumType)`** | 메타클래스가 **직접 가로채는 연산이 무엇인가** | 가로채지 않는 연산 |
| ⑤ 예외 종류와 메시지 | **거부하는 자리** | 조용히 통과한 것 |
| ★ **부적용인 창** — 속도·메모리 측정 | — | ★ **이 문서는 속도를 한 번도 안 쟀다.** `Enum` 비교가 느리다·빠르다를 적지 않았다 |
| ★ **못 잰 것** — 3.10 이하 판 | — | ★ **이 머신에 `python3.10` 이 없다**(첫 블록이 `PATH` 를 물었다). 「3.10 에는 `StrEnum` 이 없다」는 **문서의 *Added in version 3.11* 로만** 적는다 |

★★ **④가 이 주제의 네 번째 창이다.** 「멤버 접근이 메타클래스를 거친다」로 흔히 말하는데,
**3.12 의 `EnumType` 에는 `__getattr__` 이 없고 멤버는 클래스 `__dict__` 에 그냥 산다**(동작 5).
메타클래스가 가로채는 것은 **`Color(1)` · `Color['RED']` · `for` · `in` · `len` · 대입·삭제**이지
**`Color.RED` 라는 점 접근이 아니다.** 그 목록을 `vars(EnumType)` 로 직접 뽑았다.

★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「3.12 에서 무엇이 바뀌었나」를 **릴리스 노트로 읽는 대신 3.11 을 실제로 돌려** 물었다(동작 6).
★ 바꾼 창이 못 보는 것 — **3.10 이하**다. 그 판은 이 머신에 없어 **못 잰 것**으로 남는다.

먼저 판을 박아 둔다. 이 문서의 모든 출력은 아래 두 판에서 나왔다.

```python
# e37_version.py
import enum
import shutil
import sys

print("version_info   =", sys.version_info)
print("implementation =", sys.implementation.name)
print("enum.StrEnum 이 있나  :", hasattr(enum, "StrEnum"))
print("enum.ReprEnum 이 있나 :", hasattr(enum, "ReprEnum"))
print("이 머신의 다른 판 — PATH 에 물어본다")
for exe in ("python3.10", "python3.11", "python3.13", "python3.14"):
    print("   %-11s :" % exe, shutil.which(exe) is not None)
```

```text
===== python3 - <e37_version.py =====
version_info   = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
enum.StrEnum 이 있나  : True
enum.ReprEnum 이 있나 : True
이 머신의 다른 판 — PATH 에 물어본다
   python3.10  : False
   python3.11  : True
   python3.13  : False
   python3.14  : False
(exit 0)
```

```text
===== python3.11 - <e37_version_py311.py =====
version_info   = sys.version_info(major=3, minor=11, micro=15, releaselevel='final', serial=0)
implementation = cpython
enum.StrEnum 이 있나  : True
enum.ReprEnum 이 있나 : True
이 머신의 다른 판 — PATH 에 물어본다
   python3.10  : False
   python3.11  : True
   python3.13  : False
   python3.14  : False
(exit 0)
```

★ 두 판 모두 `StrEnum`·`ReprEnum` 이 **있다**. **3.11 이 그것이 들어온 판**이므로 여기서는 「있다」만 확인된다.\
★★ **`python3.10` 이 `False`** 다 — 「3.10 에는 없다」는 **이 머신에서 못 잰 것**이고, 문서의 *Added in version 3.11* 로만 적는다.
(3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e37_version_py311.py` 다.)

## 이 주제가 답하려는 질문

1. ★★★ **`Enum`·`IntEnum`·`StrEnum`·`Flag` 은 무엇과 같다고 답하나** — `== 1`·`== "red"`·`is`·정렬·`json.dumps`·해시.
2. ★★ **왜 평범한 `Enum` 은 `json.dumps` 에서 터지고 `IntEnum` 은 숫자로 나가나** — 그리고 되읽으면 무엇이 오나.
3. **`auto()` 는 무슨 값을 만들고, 같은 값 두 멤버는 어떻게 되나** — 별칭과 `@unique`.

★ 첫째가 이 주제의 인출 목표다.
**「네 종류 중 평범한 `Enum` 과 답이 다른 칸이 어디인가」를 격자로 댈 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 비교·직렬화 격자 — 네 종류 × 여섯 탐침

**언제 쓰나** — 이 주제의 출발점. 「`IntEnum` 을 써야 하나 그냥 `Enum` 이면 되나」를 **외우지 않고 보는 법**.

```text
   네 종류가 무엇을 물려받았나 (__mro__ 의 요지)

   Enum     :  Color  -> Enum -> object
   IntEnum  :  Level  -> IntEnum -> int -> ReprEnum -> Enum -> object
   StrEnum  :  Mode   -> StrEnum -> str -> ReprEnum -> Enum -> object
   Flag     :  Perm   -> Flag -> Enum -> object

   ★ int / str 가 줄에 끼어 있는 둘만 "숫자·글자처럼" 답한다
   ★ Flag 은 int 가 없다 — 비트 연산은 되지만 숫자와 같다고 답하지 않는다
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

```text
===== python3 - <e37_grid.py =====
--- 각 클래스의 __mro__ 와 __eq__ 를 처음 가진 칸 ---
   E  ['E', 'Enum', 'object']  __eq__ <- object
   I  ['I', 'IntEnum', 'int', 'ReprEnum', 'Enum', 'object']  __eq__ <- int
   S  ['S', 'StrEnum', 'str', 'ReprEnum', 'Enum', 'object']  __eq__ <- str
   F  ['F', 'Flag', 'Enum', 'object']  __eq__ <- object
클래스  RED.value  == 1 | == "red" | C(v) is m | sorted | json.dumps | hash==hash(v)
E      1          False | False | True | TypeError | TypeError | False
I      1          True | False | True | '[RED,BLUE]' | '1' | True
S      'red'      False | True | True | '[BLUE,RED]' | '"red"' | True
F      1          False | False | True | TypeError | TypeError | False
--- 기준: E 행(평범한 Enum). 같은 열의 E 칸과 다른 칸을 센다 ---
   I : 4 칸 ['== 1', 'sorted', 'json.dumps', 'hash==hash(v)']
   S : 4 칸 ['== "red"', 'sorted', 'json.dumps', 'hash==hash(v)']
   F : 0 칸 []
갈린 칸 8 / 18
(exit 0)
```

그림 해설 — 한 행씩.

* ★ **첫 네 줄이 원인이다** — `__eq__` 를 처음 가진 칸이 E·F 는 **`object`**, I 는 **`int`**, S 는 **`str`** 이다.
  **줄에 `int`·`str` 이 끼어 있느냐**가 아래 격자의 모든 차이를 만든다([34번](../34-inheritance-mro-super/2-summary.md)의 MRO 가 곧 탐색 순서).
* ★★★ **마지막 줄이 이 문항의 결론이다 — `갈린 칸 8 / 18`.** 기준은 **평범한 `Enum` 행(E)** 이고,
  같은 열의 E 칸과 다른 칸을 **스크립트가 셌다.**
* **E 행** — `== 1` 도 `== "red"` 도 **거짓**, 정렬은 **`TypeError`**, `json.dumps` 도 **`TypeError`**.
  ★ HOWTO 의 문장 그대로다 — *"Comparisons against non-enumeration values will always compare not equal"*.
  ★ `hash(m) == hash(m.value)` 가 **거짓**이다 — 번호표의 해시는 **숫자의 해시가 아니다**(동작 5 의 ⑥).
* ★★ **I 행(`IntEnum`)** — **4칸이 갈렸다**: `== 1` 이 참 · 정렬이 된다 · `json.dumps` 가 `'1'` · 해시가 `1` 과 같다.
  **`int` 를 물려받았으니 `int` 로서 답하는 것**이다.
* ★★ **S 행(`StrEnum`)** — **역시 4칸**: `== "red"` 가 참 · 정렬 · `'"red"'` · 해시.
  ★★ **정렬 칸을 보라 — `[BLUE,RED]`** 다. 정의는 `RED` → `BLUE` 순서인데 **알파벳순**으로 섰다.
  `str` 로서 비교하니 **값의 사전식 순서**다. `IntEnum` 은 값이 `1`·`2` 라 **우연히** 정의 순서와 같았을 뿐이다.
* ★★ **F 행(`Flag`)** — **0칸**이다. **`Flag` 은 정수 값을 갖지만 `int` 가 아니다.**
  `== 1` 이 거짓이고 `json.dumps` 도 터진다 — 평범한 `Enum` 과 **답이 한 칸도 안 다르다.**
  ★ 정수처럼 굴어야 하면 **`IntFlag`** 다(격자 밖이다 — 이 문서는 넷만 돌렸다).
* **`C(v) is m` 열은 네 행이 전부 `True`** 다 — **값으로 불러도 새로 안 만든다.** 싱글턴은 네 종류 공통이다.

**비용** — 믹스인은 **편의와 안전망을 맞바꾼다.** `IntEnum` 을 쓰면 `json`·DB·`==` 가 편해지는 대신
**「번호표와 숫자를 헷갈린 코드」가 조용히 통과한다**(동작 5 의 ⑥ — 다른 열거형끼리도 같다고 답한다).

### 2. ★★★ 직렬화 함정 — `json.dumps` 가 터지는 쪽과 숫자로 나가는 쪽

**언제 쓰나** — API 응답·설정 파일·로그에 열거형을 실을 때. **가장 자주 터지는 자리다.**

```text
   json.dumps 가 아는 것 : dict list tuple str int float bool None  (+ 그 하위 클래스)

   Color.RED  (Enum)     -> 목록에 없다          -> 예외
   Level.LOW  (IntEnum)  -> int 의 하위 클래스다  -> 1        (★ 이름이 사라진다)
   Mode.FAST  (StrEnum)  -> str 의 하위 클래스다  -> "fast"

   되읽기 : json.loads("1") -> 1 (int)   ★ Level 이 아니다. Level(1) 로 되살려야 한다
```

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

```text
===== python3 - <e37_json.py =====
① 세 종류를 json.dumps 에 그대로 넘긴다
   <Color.RED: 1>   -> TypeError: Object of type Color is not JSON serializable
   <Level.LOW: 1>   -> 1
   <Mode.FAST: 'fast'> -> "fast"
② dict 의 키와 값으로 넘긴다
    {"1": "fast"}
    키가 Color.RED -> TypeError: keys must be str, int, float, bool or None, not Color
③ 되읽으면 무엇이 오나
   back['lv']        : 1 int
   Level(back['lv']) : <Level.LOW: 1>
④ 문자열로 만드는 세 길
   <Color.RED: 1>   str='Color.RED'  f='Color.RED'  name='RED'
   <Level.LOW: 1>   str='1'          f='1'          name='LOW'
   <Mode.FAST: 'fast'> str='fast'       f='fast'       name='FAST'
⑤ Enum 을 내보내는 명시적인 길
   default=값   : {"c": 1}
   default=이름 : {"c": "RED"}
(exit 0)
```

그림 해설.

* ★★★ **①의 첫 줄** — `TypeError: Object of type Color is not JSON serializable`.
  평범한 `Enum` 은 **`json` 이 아는 타입 목록에 없다.**
* ★★ **①의 둘째·셋째 줄** — `IntEnum` 은 `1`, `StrEnum` 은 `"fast"` 로 나간다.
  **`int`·`str` 의 하위 클래스라서 `json` 이 그 타입으로 본 것**이다.
  ★ 대가 — **`LOW` 라는 이름이 사라진다.** 받는 쪽은 `1` 만 본다.
* ★ **②** — `IntEnum` 은 **dict 의 키**로도 나간다(`{"1": "fast"}` — `json` 의 키는 문자열이 된다).
  평범한 `Enum` 을 키로 주면 **다른 문구의 `TypeError`** 다 — *keys must be str, int, float, bool or None, not Color*.
* ★★ **③이 왕복의 함정이다.** 되읽은 값은 **`int` 의 `1`** 이다. `Level` 이 아니다.
  **`Level(back['lv'])` 로 되살려야** 번호표가 돌아온다 — 그리고 그때 **싱글턴이 그대로 돌아온다**(동작 1 의 `C(v) is m` 열).
* ★★ **④ — 문자열로 만드는 세 길이 종류마다 다르다.**
  평범한 `Enum` 은 `str()` 도 f-string 도 **`'Color.RED'`**(클래스 이름까지 붙는다).
  `IntEnum`·`StrEnum` 은 **값**(`'1'`·`'fast'`)이다 — 이것이 3.11 에 들어온 **`ReprEnum`** 의 일이다.
  ★ 문서 문장 — *"`ReprEnum` uses the `repr()` of `Enum`, but the `str()` of the mixed-in data type"*.
  ★ 그래서 **`f"{status}"` 로 DB 에 쓰는 코드**는 평범한 `Enum` 에서 `'Status.ACTIVE'` 라는 **엉뚱한 문자열**을 넣는다 — 예외 없이.
* ★ **⑤가 고치는 법이다.** `default=` 훅에 **값을 낼지 이름을 낼지를 내가 정한다.**
  ★ 이름을 내면 **값을 바꿔도 바깥 데이터가 안 깨진다** — 자바 갈래가 `ordinal()` 을 내보내지 말라고 한 것과 같은 축이다([자바 13번](../../../java/syntax/13-enum-classes/2-summary.md)).

**비용** — 평범한 `Enum` 은 **터져서 알려 주고**, 믹스인은 **조용히 이름을 버린다.**
어느 쪽이 나은지는 **바깥에서 누가 읽느냐**에 달렸다.

### 3. ★★ `auto()` 가 만드는 값

**언제 쓰나** — 값에 의미가 없고 **이름만 중요할 때.** 값을 손으로 매기다 겹치는 사고를 막는다.

```text
   auto() 는 "앞 멤버를 보고 다음 값을 정하는 함수" 를 부른다 (_generate_next_value_)

   Enum     : 1, 2, 3            ★ 0 이 아니라 1 부터
   Enum     : X=10, auto, auto   -> 11, 12   (마지막 값 + 1)
   IntEnum  : 1, 2
   StrEnum  : ★ 이름을 소문자로   RED -> "red" · DarkBlue -> "darkblue"
   Flag     : 1, 2, 4            ★ 2 의 거듭제곱 (비트 하나씩)
```

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

```text
===== python3 - <e37_auto.py =====
A  [('X', 1), ('Y', 2), ('Z', 3)]
B  [('X', 10), ('Y', 11), ('Z', 12)]
C  [('X', 1), ('Y', 2)]
D  [('RED', 'red'), ('DarkBlue', 'darkblue')]
G  [('R', 1), ('W', 2), ('X', 4)]
G.R | G.W        : <G.R|W: 3>
(G.R | G.W).value: 3
G.R in (G.R|G.W) : True
(exit 0)
```

그림 해설.

* ★ **A** — `auto()` 는 **1 부터**다. 문서 문장 — *"results in integers of increasing value, starting with `1`"*.
  ★ `0` 부터가 아닌 이유는 **`0` 이 거짓**이기 때문이다 — 모든 멤버가 참이 되게 한 것이다.
* **B** — 앞에 `10` 을 손으로 주면 그 뒤는 **`11`·`12`** 다. **마지막 값 + 1** 이다.
* ★★ **D(`StrEnum`)** — **이름의 소문자**다. `DarkBlue` 가 **`'darkblue'`** 가 됐다 —
  **밑줄을 넣어 주지 않는다**(`dark_blue` 가 아니다). 문서 문장 — *"results in the lower-cased member name as the value"*.
* ★ **G(`Flag`)** — **`1`·`2`·`4`**. 비트 하나씩이라 `G.R | G.W` 가 **`3`** 인 **새 조합**(`<G.R|W: 3>`)이 된다.
  `G.R in (G.R | G.W)` 가 **참** — `Flag` 의 `in` 은 「**비트가 들어 있나**」다.

**비용** — `auto()` 를 쓰면 **값이 정의 순서에 묶인다.** 가운데 멤버를 끼우면 **뒤 멤버의 값이 전부 밀린다** —
그 값을 **바깥에 저장했다면** 동작 2 의 ⑤처럼 **이름으로 내보내야** 안전하다.

### 4. ★★ 같은 값 두 멤버 — 별칭과 `@unique`

**언제 쓰나** — 옛 이름을 남겨 두고 싶을 때(의도한 별칭). 또는 **복사·붙여넣기로 값이 겹쳤을 때**(사고).

```text
   class Shape(Enum):
       SQUARE = 2      -> 멤버 SQUARE 를 만든다
       CIRCLE = 3      -> 멤버 CIRCLE 을 만든다
       BOX = 2         -> ★ 새로 안 만든다. SQUARE 를 가리키는 두 번째 이름이 된다

   Shape.BOX          -> <Shape.SQUARE: 2>
   list(Shape)        -> [SQUARE, CIRCLE]            ★ 순회에서는 숨는다
   Shape.__members__  -> SQUARE, CIRCLE, BOX         ★ 여기서는 보인다
   @unique            -> class 문에서 ValueError     ★ 별칭이 하나라도 있으면
```

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

```text
===== python3 - <e37_alias.py =====
① 같은 값 두 멤버
   Shape.BOX              : <Shape.SQUARE: 2>
   Shape.BOX is SQUARE    : True
   Shape(2)               : <Shape.SQUARE: 2>
   list(Shape)            : ['SQUARE', 'CIRCLE']
   __members__ 의 키      : ['SQUARE', 'CIRCLE', 'BOX']
② @unique 를 붙인다
    ValueError: duplicate values found in <enum 'Shape2'>: BOX -> SQUARE
③ 멤버는 어디에 사나
   type(Shape)                    : EnumType
   Shape.__dict__['SQUARE'] is m  : True
   '__getattr__' in vars(EnumType): False
   EnumType 이 직접 가진 것       : ['__call__', '__getitem__', '__iter__', '__contains__', '__len__', '__setattr__', '__delattr__']
④ 다시 묶기 시도
   Shape.SQUARE = 9       -> AttributeError: cannot reassign member 'SQUARE'
   Shape.SQUARE.value = 9 -> AttributeError: <enum 'Enum'> cannot set attribute 'value'
   Shape()                -> TypeError: EnumType.__call__() missing 1 required positional argument: 'value'
⑤ 사본을 만든다
   copy.deepcopy(m) is m  : True
   pickle 왕복 is m       : True
⑥ 값이 같은 다른 두 열거형
   Shape.SQUARE == Fruit.APPLE : False
   Size.SMALL == Rank.LOW      : True
   hash(Shape.SQUARE) == hash('SQUARE') : True
(exit 0)
```

그림 해설 — 이 블록은 동작 4·5 가 같이 쓴다. ①·②가 이 절이다.

* ★★ **①** — `Shape.BOX` 의 `repr` 이 **`<Shape.SQUARE: 2>`** 다. **`BOX` 라는 멤버는 없다** — 이름만 있다.
  `Shape.BOX is Shape.SQUARE` 가 **참**이다.
* ★ **순회는 별칭을 숨기고 `__members__` 는 보인다.** 문서가 순회를 *"canonical (i.e. non-alias) members in definition order"* 라 적는다.
  ★ 그래서 **「멤버가 몇 개인가」를 `len(Shape)` 로 세면 별칭이 빠진다** — 둘 중 무엇을 셀지 정해야 한다.
* ★★ **②** — `@unique` 가 **`class` 문에서** 막는다. 메시지가 **어느 이름이 어느 멤버의 별칭인지**를 댄다(`BOX -> SQUARE`).
  ★ **`@unique` 가 없으면 에러도 경고도 없다.** 값이 겹친 사고가 **조용히 별칭이 된다.**

**비용** — 별칭은 공짜다(새 객체가 없다). 대가는 **사고와 의도가 같은 모양**이라는 것 — 그래서 `@unique` 를 기본으로 붙이는 코드베이스가 많다.

### 5. ★★ 멤버는 어디에 살고 무엇이 막히나 — 메타클래스가 가로채는 자리

**언제 쓰나** — 「`Color.RED = 5` 는 왜 막히나」·「`Color(1)` 은 왜 새로 안 만드나」가 막힐 때.

```text
   Color.RED  (점 접근)                       Color(1) · Color['RED'] · for · in · len
        |                                              |
        v                                              v
   type.__getattribute__                       EnumType.__call__ / __getitem__ /
   -> Color.__dict__['RED'] 를 찾는다                     __iter__ / __contains__ / __len__
      (29번의 평범한 클래스 속성 탐색)          ★ 메타클래스가 직접 가로챈다

   Color.RED = 5   -> EnumType.__setattr__ 가 막는다
   Color.RED.value = 5 -> value 는 쓰기 불가 속성이다

   ★ 3.12 의 EnumType 에는 __getattr__ 이 없다 (3.11 에는 있었다 — 동작 6)
```

위 블록(`e37_alias.py`)의 ③~⑥이 이 절이다.

* ★★★ **③** — `Shape.__dict__['SQUARE'] is Shape.SQUARE` 가 **참**이다.
  **멤버는 클래스 `__dict__` 에 그냥 산다** — `Shape.SQUARE` 는 [29번](../29-classes-and-attribute-lookup/2-summary.md)의 **평범한 클래스 속성 탐색**으로 찾아진다.
  ★ **`'__getattr__' in vars(EnumType)` 가 `False`** 다. **점 접근을 메타클래스가 가로채지 않는다.**
* ★★ **③의 마지막 줄이 메타클래스가 가로채는 목록이다** —
  `__call__`·`__getitem__`·`__iter__`·`__contains__`·`__len__`·`__setattr__`·`__delattr__` 일곱이 **`EnumType` 자신의 칸**에 있다.
  ★ HOWTO 문장 — *"The `EnumType` metaclass is responsible for providing the `__contains__()`, `__dir__()`, `__iter__()` and other methods …"*.
* ★ **④** — `Shape.SQUARE = 9` 는 **`cannot reassign member 'SQUARE'`**(메타클래스 `__setattr__`),
  `Shape.SQUARE.value = 9` 는 **`cannot set attribute 'value'`**(멤버 쪽 속성),
  `Shape()` 는 **`value` 인자가 없다는 `TypeError`**(메타클래스 `__call__` 이 값을 요구한다). **막는 층이 셋 다 다르다.**
* ★★ **⑤** — `copy.deepcopy` 도 `pickle` 왕복도 **같은 한 장**을 돌려준다. 문서가 **싱글턴**이라 부르는 것이 이것이다 —
  *"EnumType creates them all while it is creating the enum class itself … returning only the existing member instances."*
  ★ 그래서 HOWTO 가 *"Enumeration members are compared by identity"* 라 적고 **`is` 로 비교해도 된다.**
* ★★ **⑥이 [30번](../30-repr-eq-hash-contracts/2-summary.md)과 만나는 자리다.**
  값이 `2` 로 같은 **다른 두 평범한 `Enum`** 은 `==` 가 **거짓**이다(`Shape.SQUARE == Fruit.APPLE`).
  그런데 **다른 두 `IntEnum`** 은 **참**이다(`Size.SMALL == Rank.LOW`) — **둘 다 `int` 의 `2` 로서 비교**했기 때문이다.
  ★★ **「크기 SMALL」과 「등급 LOW」가 같다고 답한다** — `IntEnum` 이 여는 함정이 이것이다.
* ★ **⑥의 마지막 줄** — `hash(Shape.SQUARE) == hash('SQUARE')` 가 **참**이다. **멤버의 해시는 이름의 해시**다(CPython 구현).
  그래서 동작 1 의 격자에서 평범한 `Enum` 의 해시가 **값의 해시와 달랐다.** 숫자 자체는 실행마다 바뀌므로 **한 번도 안 찍었다.**

**비용** — 싱글턴과 불변은 **클래스 생성 때 한 번** 치른다. 대가는 **`is` 비교가 되는 대신 멤버를 동적으로 못 늘린다는 것**이다.

### 6. ★★ 판 경계 — 3.11 과 3.12 를 실제로 돌렸다

**언제 쓰나** — 「`value in Color` 가 되나」가 판마다 다르다. **라이브러리가 두 판을 지원해야 할 때.**

```text
                         3.11                          3.12
   1 in Color       TypeError + DeprecationWarning      True
   'x' in Color     TypeError + DeprecationWarning      False
   Color.RED in Color       True                        True
   EnumType.__getattr__     있다                         없다

   ★ 3.11 의 경고 문구가 3.12 의 동작을 예고한다
```

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

```text
===== python3 - <e37_boundary.py =====
판 : (3, 12)
   1 in Color           -> True
   'x' in Color         -> False
   Color.RED in Color   -> True
잡힌 경고 수 : 0
'__getattr__' in vars(EnumType) : False
(exit 0)
```

```text
===== python3.11 - <e37_boundary_py311.py =====
판 : (3, 11)
   1 in Color           -> TypeError: unsupported operand type(s) for 'in': 'int' and 'EnumType'
   'x' in Color         -> TypeError: unsupported operand type(s) for 'in': 'str' and 'EnumType'
   Color.RED in Color   -> True
잡힌 경고 수 : 2
    DeprecationWarning: in 3.12 __contains__ will no longer raise TypeError, but will return True or False depending on whether the value is a member or the value of a member
    DeprecationWarning: in 3.12 __contains__ will no longer raise TypeError, but will return True or False depending on whether the value is a member or the value of a member
'__getattr__' in vars(EnumType) : True
(exit 0)
```

그림 해설.

* ★★★ **같은 소스가 두 판에서 다른 답을 낸다.** 3.12 는 `1 in Color` 가 **`True`**, 3.11 은 **`TypeError`** 다.
  (3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e37_boundary_py311.py` 다.)
* ★ **3.11 의 경고가 3.12 를 예고했다** — *in 3.12 __contains__ will no longer raise TypeError, but will return True or False …*.
  문서의 *Changed in version 3.12* 와 **실행이 같은 말**을 한다.
* ★ **`Color.RED in Color` 는 두 판 모두 `True`** 다 — 바뀐 것은 **멤버가 아닌 값을 물을 때**뿐이다.
* ★★ **`EnumType.__getattr__` 이 3.11 에는 있고 3.12 에는 없다.** 동작 5 의 「점 접근을 메타클래스가 안 가로챈다」는
  **3.12 의 사실**이다. ★ 다만 3.11 의 그것도 **`__getattr__`** 이라 **찾기에 실패했을 때만** 불리는 갈고리다 —
  [29번](../29-classes-and-attribute-lookup/2-summary.md)의 탐색 순서상 **`Color.__dict__` 에서 먼저 찾아지므로** 멤버 접근에는 안 끼어든다.

**비용** — 두 판을 지원하는 코드는 **`in` 대신 `try: Color(v)`** 로 써야 한다 — 없는 값이면 `ValueError` 가 나는 것은 **두 판 공통의 계약**이다.

### 7. ★★ 다른 언어와 견주면 — 번호표가 객체인가 정수인가

```text
                    멤버의 정체                          근거
   Python Enum      클래스의 인스턴스 · 싱글턴             이 문서 동작 5
   Python IntEnum   int 이기도 한 인스턴스                 이 문서 동작 1
   Java enum        java.lang.Enum 을 상속한 클래스의 필드  자바 13번 실측
   C# enum          정수 위의 얇은 껍데기                  C# 목록 20번 (폴더 없음)
   Rust enum        태그 + 변형마다 데이터                  Rust 17번 실측

   ★ 이 표는 "정체" 한 칸만 비교한다 — 다른 언어의 동작은 그 갈래가 잰 것만 인용한다
```

* ★ **자바 쪽** — [자바 13번](../../../java/syntax/13-enum-classes/2-summary.md)이 **`enum` 은 `java.lang.Enum` 을 상속한 진짜 클래스이고 상수는 `<clinit>` 이 한 번 만드는 필드**라고 실측했다.
  **파이썬 `Enum` 과 같은 쪽**(객체·싱글턴)이다.
  ★ 다른 점 — 자바는 **`ordinal()` 을 늘 갖고**, 파이썬은 **`value` 가 내가 준 값**이다.
* ★ **C# 쪽** — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **20번** 이 「열거형이 정수 위의 얇은 껍데기」다.
  **파이썬 `IntEnum` 에 가까운 쪽**이다. ★ 아직 폴더가 없어 인용할 실측은 없다.
* ★ **Rust 쪽** — [Rust 17번](../../../rust/syntax/17-enums-and-data-carrying-variants/2-summary.md)이 **변형마다 데이터를 싣는 열거형**을 다룬다.
  파이썬 `Enum` 은 **데이터를 싣지 못한다**(값 하나뿐) — 그 자리는 [39번](../39-match-statement/2-summary.md)의 클래스 패턴과 dataclass 가 맡는다.
* ★ **TS 쪽** — [TS 01번](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md)이 `const enum` 은 **선언이 사라지고 값이 박힌다**고 실측했다 —
  파이썬 `Enum` 은 **런타임에 클래스로 남는다**(동작 5 의 `type(Shape)` 가 `EnumType`).

## 문법 — 형태와 규칙

**형태**

```text
from enum import Enum, IntEnum, StrEnum, Flag, auto, unique

@unique                          # ★ 값이 겹치면 class 문에서 ValueError
class Status(Enum):
    ACTIVE = 1                   # 멤버 = 이름 + 값
    PAUSED = auto()              # 앞 값 + 1 -> 2
    # 멤버가 아닌 것: _로 시작하는 이름 · 메서드 · 디스크립터

class Level(IntEnum):  LOW = 1   # int 이기도 하다 — == 1 이 참, json 에 숫자로 나간다
class Mode(StrEnum):   FAST = auto()   # 3.11+ · 값은 "fast" (이름의 소문자)
class Perm(Flag):      R = auto(); W = auto()   # 1, 2 — R | W 가 새 조합

Status(1)        Status['ACTIVE']      Status.ACTIVE      # ★ 셋 다 같은 한 장
m.name  m.value  list(Status)  Status.__members__        # 순회는 정의 순서 · 별칭 제외
```

규칙 열.

1. ★★ **멤버는 싱글턴이다.** `Color(1) is Color.RED` · `copy`·`pickle` 도 같은 한 장을 준다.
2. ★★ **평범한 `Enum` 은 값과 같다고 답하지 않는다.** `Color.RED == 1` 이 거짓이다.
3. ★★ **`IntEnum`·`StrEnum` 은 `int`·`str` 로서 답한다** — `==`·정렬·`json`·해시가 전부 바뀐다(격자 8 / 18).
4. ★ **`StrEnum` 의 정렬은 값의 사전식 순서**다. 정의 순서가 아니다.
5. ★ **`Flag` 은 `int` 가 아니다.** 평범한 `Enum` 과 격자 답이 한 칸도 안 다르다. 정수처럼 쓰려면 `IntFlag`.
6. ★★★ **평범한 `Enum` 은 `json.dumps` 에서 `TypeError`** 다. 믹스인은 **값으로 나가고 이름을 잃는다.**
7. ★ **되읽은 값은 원시 타입**이다. `Level(v)` 로 되살린다.
8. ★ **`auto()` 는 1 부터** · `StrEnum` 은 **이름의 소문자** · `Flag` 은 **2 의 거듭제곱**.
9. ★★ **같은 값 두 멤버는 별칭**이다 — 에러가 없다. **`@unique` 를 붙여야** 막힌다.
10. ★ **`value in Color`** 는 **3.12 부터** 참·거짓을 준다. 3.11 은 `TypeError` 다.

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

| 쓴 꼴 | 무슨 일이 나나 | 어디서 드러나나 |
|---|---|---|
| `json.dumps({"s": Status.ACTIVE})` | `TypeError` | ★ 즉시(시끄럽다) |
| `f"{status}"` 를 DB 에 쓴다 (평범한 `Enum`) | `'Status.ACTIVE'` 가 들어간다 | ★ 에러 없음. 읽는 쪽에서 |
| `if row["status"] == Status.ACTIVE:` (평범한 `Enum`, `row` 는 `1`) | **항상 거짓** | ★ 에러 없음. 분기가 안 탄다 |
| `class Size(IntEnum)` 와 `class Rank(IntEnum)` 을 섞어 비교 | **값이 같으면 참** | ★ 에러 없음 |
| `sorted(StrEnum 멤버들)` 로 「정의 순서」를 기대 | 알파벳순 | ★ 에러 없음 |
| 값을 손으로 매기다 둘이 겹침 (`@unique` 없음) | 두 번째가 **별칭**이 된다 | ★ 에러 없음. `len()` 이 하나 적다 |
| `auto()` 멤버 가운데에 새 멤버를 끼움 | **뒤 멤버의 값이 전부 밀린다** | ★ 저장된 값과 어긋날 때 |

★ **시끄러운 것은 첫 줄 하나뿐이다.** 나머지 여섯이 **아무 말이 없다.**

## 어디서 틀리나

### (1) ★★★ 「`Enum` 을 `json.dumps` 에 그냥 넣으면 값이 나간다」로 안다

**평범한 `Enum` 은 `TypeError` 다**(동작 2 의 ①). 값이 나가는 것은 **`IntEnum`·`StrEnum`** 뿐이다.\
★ 고치는 법은 **`default=` 훅에서 값이냐 이름이냐를 내가 정하는 것**이다.

### (2) ★★★ DB 에서 읽은 `1` 을 평범한 `Enum` 멤버와 `==` 로 비교한다

**항상 거짓**이다. 예외가 안 나서 **분기가 조용히 안 탄다.**\
★ `Status(row["status"])` 로 **먼저 되살려서** 비교한다. 없는 값이면 `ValueError` 로 시끄럽게 알려 준다.

### (3) ★★ 「`IntEnum` 이면 안전하다」로 안다

**다른 두 `IntEnum` 이 값만 같으면 같다고 답한다**(동작 5 의 ⑥).\
★ 문서가 *"can be used anywhere that an integer can be used"* 라 적는다 — **정수가 쓰이는 곳이면 다 된다는 것이 곧 함정**이다.

### (4) ★★ `f"{member}"` 로 문자열을 만든다

평범한 `Enum` 은 **`'Color.RED'`**, 믹스인은 **값**이다(동작 2 의 ④). **같은 코드가 종류에 따라 다른 문자열**을 낸다.\
★ 바깥으로 내보낼 문자열은 **`.name` 이나 `.value` 를 명시**한다.

### (5) ★ `StrEnum` 을 정렬하면 정의 순서가 나온다고 믿는다

**값의 알파벳순**이다(동작 1 의 S 행 — `[BLUE,RED]`).\
★ 정의 순서가 필요하면 **`list(Mode)`** 를 쓴다 — 순회 순서는 **모듈 계약이 정의 순서를 보장**한다.

### (6) ★ `Flag` 을 정수처럼 비교한다

`Perm.R == 1` 은 **거짓**이다(동작 1 의 F 행). **`IntFlag`** 이 따로 있다.

### (7) ★★ 값이 겹쳤는데 아무 말이 없다

**별칭이 된다**(동작 4). `len(Shape)` 가 하나 적고, `list(Shape)` 에서 하나가 사라진다.\
★ **`@unique` 를 기본으로 붙인다.** 의도한 별칭이 필요할 때만 뗀다.

### (8) ★ `auto()` 로 매긴 값을 바깥에 저장한다

멤버를 끼우면 **값이 밀린다**(동작 3). ★ 저장은 **이름**으로 한다.

### (9) ★ 「멤버 접근은 메타클래스가 가로챈다」로 안다

**3.12 에서 `Color.RED` 는 평범한 클래스 속성 탐색**이다(동작 5 의 ③). 메타클래스가 가로채는 것은
**`Color(v)`·`Color[name]`·`for`·`in`·`len`·대입·삭제**다.\
★ 그래서 `Color.RED` 를 **`getattr(Color, name)`** 으로 찾을 수도 있지만, **이름으로 찾는 계약은 `Color[name]`** 이다.

### (10) ★ `value in Color` 를 두 판에서 같이 쓴다

**3.11 은 `TypeError`, 3.12 는 참·거짓**이다(동작 6).

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제의 「언어 보장」은 표준 라이브러리 문서가 정한 것**이다 —
`enum` 은 문법이 아니라 **모듈**이므로 「**이 모듈의 계약**」으로 읽는다([36번](../36-dataclasses/2-summary.md)과 같은 처지).

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **모듈 계약(언어 보장에 해당)** | `enum` 문서·HOWTO 가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 · `vars()` · 내부 이름 |
| **이 판(3.12.3 · 3.11.15)의 관찰** | 이 판에서 그랬을 뿐 | 예외 문구 · 경고 문구 |

### 모듈 계약

| 사실 | 근거 |
|---|---|
| 멤버는 **싱글턴**이다 | HOWTO — *"they are singletons"* |
| 멤버는 **`is` 로 비교된다** | HOWTO — *"Enumeration members are compared by identity"* |
| 비(非)열거형 값과는 **항상 같지 않다**(`IntEnum` 제외) | HOWTO |
| 순회는 **정의 순서**이고 **별칭을 뺀다** | 레퍼런스 — *"canonical (i.e. non-alias) members in definition order"* |
| 같은 값 두 멤버는 **별칭** | HOWTO |
| `@unique` 는 별칭이 있으면 **`ValueError`** | 레퍼런스 |
| `auto()` 는 **1 부터** · `StrEnum` 은 **이름의 소문자** | 레퍼런스 |
| `IntEnum` 은 **정수가 쓰이는 곳이면 어디든** 쓰인다 | 레퍼런스 |
| `ReprEnum` 은 **`repr` 은 `Enum` 것, `str` 은 믹스인 것** | 레퍼런스(*Added in version 3.11*) |
| `StrEnum`·`ReprEnum` 은 **3.11** 신설 | 레퍼런스 |
| 멤버 아닌 값의 `in` 이 **3.12 부터** `TypeError` 가 아니다 | 레퍼런스(*Changed in version 3.12*) |
| `EnumType` 이 `__contains__`·`__dir__`·`__iter__` 등을 준다 | HOWTO |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★★ 멤버가 **클래스 `__dict__` 에 그냥 산다** | 실행 — `Shape.__dict__['SQUARE'] is Shape.SQUARE` |
| ★ 3.12 `EnumType` 에 **`__getattr__` 이 없다**(3.11 에는 있다) | 실행 — `vars(EnumType)` 를 두 판에서 |
| `EnumType` 이 **직접 가진 던더 일곱** | 실행 — `vars(EnumType)` |
| ★ 멤버의 해시가 **이름의 해시**다 | 실행 — `hash(m) == hash(m.name)`(숫자는 안 찍었다) |
| 예외·경고 **문구** 전부 | 실행 |

### 이 판의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `cannot reassign member 'SQUARE'` 같은 **문구** | 종류(`AttributeError`)는 안정, 문구는 아니다 |
| 3.11 경고 문구 *in 3.12 __contains__ will no longer raise TypeError …* | 그 판에만 있다 |
| `EnumType` 이 가진 던더 | 판마다 바뀐다(3.11 → 3.12 에서 `__getattr__` 이 빠졌다 — 동작 6) |

### 그래서 이렇게 적으면 틀린다

* ✗ 「`Enum` 멤버는 값과 비교된다」\
  ○ **평범한 `Enum` 은 아니다.** `IntEnum`·`StrEnum` 만 그렇다.
* ✗ 「`Enum` 멤버 접근은 메타클래스를 거친다」\
  ○ ★ **3.12 에서 점 접근은 평범한 클래스 속성 탐색이다.** 메타클래스는 **호출·인덱싱·순회·포함·길이·대입**을 가로챈다.
* ✗ 「멤버의 해시는 값의 해시다」\
  ○ **평범한 `Enum` 은 아니다**(격자의 해시 열). **이름의 해시**라는 것은 CPython 구현이다.
* ✗ 「`StrEnum` 은 3.11+, 그러니 3.10 에서 안 된다를 확인했다」\
  ○ ★ **이 머신에 3.10 이 없어 못 잰 것**이다. 문서의 *Added in version 3.11* 로만 말한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 내부 상태·선택지 | ★ **평범한 `Enum` + `@unique`** | 숫자·문자열과 **헷갈릴 길이 없다.** 바깥으로 낼 때 터져서 알려 준다 |
| 바깥 프로토콜이 **정수**를 쓴다(HTTP 상태·DB 코드) | `IntEnum` | `json`·`==` 가 편하다. **다른 `IntEnum` 과 섞지 않기**만 지킨다 |
| 바깥 프로토콜이 **문자열**을 쓴다 | `StrEnum`(3.11+) | 값이 곧 문자열이다. **정렬이 알파벳순**인 것만 기억한다 |
| 권한처럼 **조합**이 필요하다 | `Flag`(정수처럼 쓰려면 `IntFlag`) | `R \| W` 가 새 값이 된다 |
| 멤버마다 **다른 데이터**를 싣고 싶다 | ★ `Enum` 이 아니라 **dataclass + `match`** | `Enum` 은 값 하나뿐이다 — [39번](../39-match-statement/2-summary.md) |

## 핵심 문장

1. **`Enum` 멤버는 싱글턴이다** — 값으로 부르든 이름으로 부르든 `copy`·`pickle` 을 거치든 **같은 한 장**이다.
2. **평범한 `Enum` 은 값과 같다고 답하지 않는다** — 그래서 `== 1` 이 거짓이고 `json.dumps` 가 터진다.
3. **`IntEnum`·`StrEnum` 은 `int`·`str` 로서 답한다** — 네 종류 격자에서 **8 / 18 칸**이 갈렸고, `Flag` 은 **0칸**이었다.
4. 믹스인은 **편의를 주고 이름을 버린다** — `json` 에 값으로 나가고, 되읽으면 원시 타입이며, **다른 열거형과도 같다고 답한다.**
5. **같은 값 두 멤버는 에러가 아니라 별칭**이다. `@unique` 가 막는다.

## 관련 자료

* 선행: [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md) —
  ★ **경계**: 속성 탐색 순서는 그쪽이 정본이고, 여기는 **멤버가 그 탐색으로 찾아진다**는 것만 확인했다.
* 선행: [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md) —
  ★ **경계**: `__eq__`/`__hash__` 계약은 그쪽, 여기는 **`IntEnum` 이 `int` 의 계약을 물려받아 다른 열거형과도 같아지는 것**만.
* 선행: [31-comparison-protocol-and-sortability](../31-comparison-protocol-and-sortability/2-summary.md) — 평범한 `Enum` 은 **순서 비교가 없다**(격자의 정렬 열).
* 선행: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — `is` 를 써도 되는 **드문 자리**가 여기다.
* 이어지는 곳: [38-namedtuple-and-typeddict](../38-namedtuple-and-typeddict/2-summary.md) — ★ **「값이 같으면 다른 타입끼리도 같다」가 거기서 또 나온다**(`NamedTuple` 이 튜플이라서).
* 이어지는 곳: [39-match-statement](../39-match-statement/2-summary.md) — ★★ **`case Color.RED:` 는 값 비교, `case RED:` 는 캡처**다. 이 주제의 멤버를 `match` 로 가를 때의 함정이 그쪽이다.
* 대비: [자바 13번 — `enum` 클래스](../../../java/syntax/13-enum-classes/2-summary.md) ·
  C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **20번** ·
  [Rust 17번](../../../rust/syntax/17-enums-and-data-carrying-variants/2-summary.md) ·
  [Kotlin 24번](../../../kotlin/syntax/24-enum-class-vs-sealed/2-summary.md)(열거형과 `sealed` 선택).
  **경계**: 그쪽 실측은 전부 그쪽이고 여기서는 인용만 했다.
* 공식 문서: [`enum`](https://docs.python.org/3.12/library/enum.html) · [Enum HOWTO](https://docs.python.org/3.12/howto/enum.html) ·
  [PEP 435](https://peps.python.org/pep-0435/)

## 용어 풀이

* **열거형(enumeration)**: 이름 붙은 값들의 **닫힌 집합**을 클래스로 만든 것.\
  예: `class Color(Enum): RED = 1`.
* **멤버(member)**: 열거형 몸통의 `이름 = 값` 한 줄이 만드는 **그 클래스의 인스턴스**.\
  예: `type(Color.RED)` 가 `Color` 다.
* **싱글턴(singleton)**: 그 값을 가진 객체가 **하나만** 있는 것.\
  예: `Color(1) is Color.RED`.
* **`EnumType`**: 열거형 클래스를 만드는 **메타클래스**. 3.11 전 이름은 `EnumMeta`.\
  예: `type(Color)` 가 `EnumType` 이다.
* **메타클래스(metaclass)**: **클래스를 만드는 클래스.** 클래스에 대한 연산(`Color(1)`·`for m in Color`)을 가로챈다.\
  예: `for m in Color` 가 도는 것은 `EnumType.__iter__` 덕이다.
* **별칭(alias)**: 이미 있는 멤버와 **값이 같은 두 번째 이름.** 새 객체가 아니다.\
  예: `Shape.BOX is Shape.SQUARE`.
* **`@unique`**: 별칭이 하나라도 있으면 `class` 문에서 `ValueError` 를 내는 데코레이터.
* **`auto()`**: 값을 **대신 정해 달라**는 표시. 종류마다 규칙이 다르다.\
  예: `Enum` 은 1부터, `StrEnum` 은 이름의 소문자.
* **믹스인(mixin) 열거형**: `int`·`str` 을 함께 물려받아 **그 타입이기도 한** 열거형.\
  예: `IntEnum`·`StrEnum`·`IntFlag`.
* **`ReprEnum`**(3.11): `repr` 은 열거형 것, **`str` 은 믹스인 타입 것**을 쓰게 하는 바탕 클래스.\
  예: `str(Level.LOW)` 가 `'1'` 이다.
* **`Flag`**: 멤버를 **비트 연산으로 조합**할 수 있는 열거형. `int` 는 아니다.\
  예: `Perm.R | Perm.W`.
* **직렬화(serialization)**: 객체를 **바깥 형식**(JSON 등)으로 바꾸는 것.\
  예: `json.dumps(Level.LOW)` 가 `'1'`.

## 더 들어가면

* ★ **`_missing_` 갈고리** — `Color(99)` 처럼 없는 값을 받았을 때 **`ValueError` 대신 무엇을 줄지** 정할 수 있다.
  바깥 데이터에 모르는 값이 섞여 올 때 「알 수 없음」 멤버로 떨어뜨리는 데 쓴다.
* ★ **멤버에 메서드와 속성을 붙일 수 있다** — `Enum` 도 클래스이므로 몸통에 `def` 를 쓰면 **멤버가 아니라 메서드**가 된다.
  무엇이 멤버가 되고 무엇이 안 되는지는 `enum` 문서의 *"supported `_sunder_` names"* 와 멤버 규칙 절이 정한다.
* ★ **`enum.property`** — `name`·`value` 가 **쓰기 불가**인 이유다(동작 5 의 ④). 멤버 이름과 속성 이름이 겹칠 때도 이것이 처리한다.
* ★ **`pickle` 은 기본이 「값으로」** 다 — HOWTO 가 *"The default method is by-value"* 라 적는다.
  **값을 바꾸면 옛 피클이 다른 멤버로 풀린다.** `enum.pickle_by_enum_name` 으로 이름 기준으로 바꿀 수 있다.
