# python/syntax/37-enum — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)과 `python3.11` **3.11.15** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★★ **트레이스백이 한 블록도 없다.** 던진 예외가 전부 `enum.py`·`json` 을 지나 **절대 경로가 박히기** 때문에
> 전부 `except` 로 받아 **예외 타입과 메시지만** 찍었다. 3.11 의 경고도 **잡아서 stdout 에** 찍었다.

## 정답

### 1. `갈린 칸 8 / 18` — `IntEnum`·`StrEnum` 이 4칸씩, `Flag` 은 0칸

**출력**

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

**왜 그런가**

* ★★★ **기준은 E 행(평범한 `Enum`)** 이다. `== 1`·`== "red"` 가 **거짓**, 정렬과 `json.dumps` 가 **`TypeError`**, 해시가 값과 **다르다**.
  ★ HOWTO — *"Comparisons against non-enumeration values will always compare not equal"*.
* ★★ **I 행은 4칸이 갈렸다** — `== 1` · 정렬 · `json`(`'1'`) · 해시. **`int` 를 물려받아 `int` 로서 답한 것**이다.
* ★★ **S 행도 4칸** — `== "red"` · 정렬 · `json`(`'"red"'`) · 해시.
  ★★ **정렬 결과가 `[BLUE,RED]`** 다 — 정의는 `RED` 가 먼저인데 **값의 알파벳순**으로 섰다(8번 답).
* ★★ **F 행은 0칸** — **`Flag` 은 `int` 가 아니다.** 값이 `1` 이어도 `== 1` 이 거짓이고 `json` 도 터진다.
* ★ **`C(v) is m` 열은 넷 다 `True`** — **값으로 불러도 새로 안 만든다.** 싱글턴은 네 종류 공통이다.
* ★ **해시 열을 `==` 로만 찍은 이유** — 문자열 해시는 **실행마다 바뀌는 숫자**라 머리말의 「흔들리는 칸」이다.
  **안 흔들리는 참·거짓으로 바꿔 찍었다.**

### 2. `Color` 는 `TypeError`, `IntEnum` 은 `1`, `StrEnum` 은 `"fast"` — 되읽으면 `int` 의 `1`

**출력**

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

**왜 그런가**

* ★★★ **①** — `TypeError: Object of type Color is not JSON serializable`. 평범한 `Enum` 은 **`json` 이 아는 타입 목록에 없다.**
  `IntEnum`·`StrEnum` 은 **`int`·`str` 의 하위 클래스**라 그 타입으로 나간다 — ★ **이름 `LOW` 는 사라진다.**
* ★ **②** — `IntEnum` 은 **키**로도 된다(`{"1": "fast"}`). 평범한 `Enum` 키는 **다른 문구의 `TypeError`** 다.
* ★★ **③** — 되읽은 값은 **`int`** 다. **`Level(1)` 로 되살려야** 멤버가 돌아온다(그리고 **같은 한 장**이 돌아온다).
* ★★ **④** — 평범한 `Enum` 의 `str()`·f-string 은 **`'Color.RED'`**, 믹스인은 **값**이다.
  ★ 3.11 의 **`ReprEnum`** 이 믹스인의 `str` 을 **믹스인 타입의 것**으로 바꿨기 때문이다.
  ★ 그래서 `f"{status}"` 를 DB 에 쓰면 평범한 `Enum` 에서 **`'Status.ACTIVE'` 가 조용히 들어간다.**
* **⑤가 고치는 법** — `default=` 로 **값이냐 이름이냐를 내가 정한다.**

### 3. `A` 는 1·2·3, `B` 는 10·11·12, `D` 는 `'red'`·`'darkblue'`, `G` 는 1·2·4

**출력**

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

**왜 그런가**

* ★ **`Enum` 의 `auto()` 는 1 부터**다(0 이 아니다). 문서 — *"starting with `1`"*.
* **`B`** — 손으로 준 `10` 다음은 **마지막 값 + 1** 이다.
* ★★ **`StrEnum` 은 이름의 소문자**다. `DarkBlue` 가 **`'darkblue'`** — **밑줄을 넣어 주지 않는다.**
* ★ **`Flag` 은 2 의 거듭제곱**이라 `G.R | G.W` 가 **`3`** 인 새 조합 `<G.R|W: 3>` 이 되고,
  `G.R in (G.R | G.W)` 는 「**그 비트가 들어 있나**」를 물어 **`True`** 다.

### 4. `BOX` 는 `SQUARE` 의 별칭 · `@unique` 는 `ValueError` · 막는 층이 셋 · 다른 두 `IntEnum` 은 같다

**출력**

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

**왜 그런가**

* ★★ **①** — 같은 값의 두 번째 이름은 **새 멤버가 아니라 별칭**이다. `repr` 이 `<Shape.SQUARE: 2>` 이고 `is` 가 참이다.
  **순회에서는 숨고 `__members__` 에서는 보인다.**
* ★ **②** — `@unique` 가 **`class` 문에서** `ValueError` 를 낸다. 없으면 **에러도 경고도 없다.**
* ★★★ **③** — **멤버는 클래스 `__dict__` 에 그냥 산다.** 3.12 `EnumType` 에는 **`__getattr__` 이 없다**(7번 답).
  메타클래스가 직접 가진 것은 **일곱** — 호출·인덱싱·순회·포함·길이·대입·삭제.
* ★ **④에서 막는 층이 셋 다 다르다** — 다시 묶기는 **메타클래스 `__setattr__`**, `.value` 대입은 **멤버 쪽 쓰기 불가 속성**,
  `Shape()` 는 **메타클래스 `__call__` 이 값 인자를 요구**해서다.
* ★★ **⑤** — `deepcopy` 도 `pickle` 왕복도 **같은 한 장**이다. 그래서 `is` 로 비교해도 된다.
* ★★★ **⑥이 이 문항의 함정이다.** 평범한 `Enum` 둘은 값이 같아도 **거짓**, **`IntEnum` 둘은 참**이다 —
  둘 다 **`int` 의 `2` 로서** 비교했기 때문이다. 「크기 SMALL」과 「등급 LOW」가 같다고 답한다.
  ★ 마지막 줄 — 멤버의 해시는 **이름의 해시**다(CPython 구현, 9번 답).

### 5. 3.12 는 `True`·`False`, 3.11 은 `TypeError` 둘 + 경고 둘 — `__getattr__` 도 3.11 에만 있다

**출력**

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

**왜 그런가**

* (3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e37_boundary_py311.py` 다.)
* ★★★ **같은 소스가 판마다 다른 답을 낸다.** 문서의 *Changed in version 3.12* —
  *"Before Python 3.12, a `TypeError` is raised if a non-Enum-member is used in a containment check."*
* ★ **3.11 의 경고가 3.12 의 동작을 예고한다** — 경고가 두 번 잡힌 것은 **멤버가 아닌 값을 두 번** 물었기 때문이다.
  `Color.RED in Color` 는 두 판 모두 **`True`** 이고 경고도 없다.
* ★ **`__getattr__` 은 3.11 에만 있다.** 다만 **찾기에 실패했을 때만** 불리는 갈고리라 멤버 접근에는 안 끼어든다(7번 답).

### 6. `__mro__` 에 `int` 가 끼어 있느냐 — `Flag` 에는 없다

**왜 그런가**

* ★★ **1번 출력의 첫 네 줄이 답이다.** `I` 의 `__mro__` 는 `I → IntEnum → int → ReprEnum → Enum → object` 이고
  **`__eq__` 를 처음 가진 칸이 `int`** 다 — 그래서 **정수로서 비교**한다.
* 평범한 `Enum` 은 줄에 `int` 가 없고 **`Enum` 자신도 `__eq__` 를 안 가져서** `__eq__ <- object`, 곧 **동일성 비교**로 떨어진다 — 그래서 `== 1` 이 거짓이다.
* ★ **`Flag` 의 줄에도 `int` 가 없다**(`F → Flag → Enum → object`, `__eq__ <- object`). 그래서 **값이 정수여도 평범한 `Enum` 처럼 답한다**(1번 답의 F 행 0칸).
  정수로서 답하는 것은 **`IntFlag`** 다.
* ★ 이것은 [34번](../34-inheritance-mro-super/2-summary.md)의 **MRO 가 곧 탐색 순서**라는 규칙 그대로다.

### 7. 평범한 클래스 속성 탐색이다 — 메타클래스가 가로채는 것은 호출·인덱싱·순회·포함·길이·대입·삭제

**왜 그런가**

* ★★★ **확인하는 법** — `Shape.__dict__['SQUARE'] is Shape.SQUARE` 가 **참**이고(멤버가 클래스 칸에 산다),
  `'__getattr__' in vars(EnumType)` 가 **거짓**이다(3.12). 둘 다 4번 출력의 ③에 있다.
* 그러므로 `Color.RED` 는 [29번](../29-classes-and-attribute-lookup/2-summary.md)의 **평범한 클래스 속성 탐색**으로 찾아진다.
* ★★ **메타클래스가 직접 가로채는 것** — `vars(EnumType)` 에서 뽑은 일곱:
  `__call__`(`Color(1)`) · `__getitem__`(`Color['RED']`) · `__iter__`(`for`) · `__contains__`(`in`) · `__len__` · `__setattr__` · `__delattr__`.
* ★ 흔한 설명 「멤버 접근이 메타클래스를 거친다」는 **점 접근에 대해서는 3.12 기준으로 틀린 말**이고,
  **값·이름으로 찾는 접근**(`Color(1)`·`Color['RED']`)에 대해서는 맞는 말이다.

### 8. `str` 로서 비교하니 값의 사전식 순서다 — 정의 순서는 `list(Mode)`

**왜 그런가**

* ★ `StrEnum` 은 `str` 을 물려받아 `<` 가 **`str.__lt__`** 다. `'blue' < 'red'` 라 `BLUE` 가 앞에 선다.
* ★ `IntEnum` 이 정의 순서처럼 보인 것은 **값을 `1`·`2` 로 매겼기 때문**일 뿐이다. 값이 `2`·`1` 이었으면 뒤집힌다.
* ★★ **정의 순서가 필요하면 `list(Mode)`** 다. 모듈 문서가 순회를 **정의 순서**로 보장한다 —
  *"canonical (i.e. non-alias) members in definition order"*.

### 9. 싱글턴은 계약 · 해시·`__dict__` 는 구현 · 3.10 은 못 잰 것

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| 멤버는 **싱글턴**이다 | **모듈 계약** | HOWTO — *"they are singletons"* |
| `is` 로 비교해도 된다 | **모듈 계약** | HOWTO — *"compared by identity"* |
| 순회는 **정의 순서**, 별칭 제외 | **모듈 계약** | 레퍼런스 |
| ★ `hash(멤버) == hash(이름)` | **CPython 구현** | 실행(4번 ⑥) — 문서는 해시가 무엇인지 적지 않는다 |
| ★ 멤버가 **클래스 `__dict__` 에 산다** | **CPython 구현** | 실행(4번 ③) |
| 3.12 `EnumType` 에 `__getattr__` 이 없다 | **CPython 구현** | 실행(5번) |
| 예외·경고 **문구** | **이 판의 관찰** | 실행 |

* ★ **`hash()` 숫자를 안 찍은 이유** — 문자열 해시는 **`PYTHONHASHSEED` 로 실행마다 바뀐다.**
  찍으면 재대조에서 매번 불일치가 난다. **정규화 규칙을 늘리는 대신 `==` 결과로 바꿔 찍었다.**
* ★★ **「3.10 에는 `StrEnum` 이 없다」는 못 잰 것이다.** 이 머신의 `PATH` 에 `python3.10` 이 **없다**(요약 첫 블록).
  문서의 *Added in version 3.11* 로만 적었다 — **「확인했다」로 적으면 틀린다.**

### 10. `int` 의 계약을 물려받는다 · 둘 다 「바깥에 순번을 내보내지 마라」 · 점이 있느냐

**왜 그런가**

* ★★ [30번](../30-repr-eq-hash-contracts/2-summary.md)의 계약은 「`==` 가 참이면 해시도 같아야 한다」다.
  **`IntEnum` 은 `int` 의 `__eq__`·`__hash__` 를 함께 물려받으므로 계약은 지켜진다** —
  그 결과 **다른 두 `IntEnum` 이 값만 같으면 `==` 도 해시도 같아** dict 의 **한 키**로 겹친다.
  ★ 계약을 지켰기 때문에 생기는 함정이다.
* ★ **자바의 `ordinal()`** 과 파이썬의 **`auto()` 값**은 둘 다 **정의 순서에서 나온 번호**다.
  멤버 하나를 가운데 끼우면 **뒤 번호가 전부 밀리고 에러가 없다.** 처방도 같다 — **이름으로 저장한다.**
* ★★ [39번](../39-match-statement/2-summary.md) — `case Color.RED:` 는 **점이 있어 값 패턴**이고 `==` 로 비교한다.
  `case RED:` 는 **점이 없어 캡처 패턴**이라 **무엇이든 매치하고 `RED` 를 덮어쓴다.** 대소문자가 아니라 **점**이 가른다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 판 + `StrEnum`·`ReprEnum` 유무 + 다른 판 | `python3 - <e37_version.py` · `python3.11 - <e37_version_py311.py` | 2씩(캡처 + 재대조) | 두 판 모두 있다 · **3.10 은 없다(못 잰 것)** |
| 비교·직렬화 격자 | `python3 - <e37_grid.py` | 2 | **갈린 칸 8 / 18** · `Flag` 0칸 |
| `json` 직렬화와 왕복 | `python3 - <e37_json.py` | 2 | `Color` 만 `TypeError` · 되읽으면 `int` |
| `auto()` 값 | `python3 - <e37_auto.py` | 2 | 1부터 · 소문자 이름 · 2 의 거듭제곱 |
| 별칭·메타클래스·싱글턴 | `python3 - <e37_alias.py` | 2 | 별칭 · `__getattr__` 없음 · 다른 `IntEnum` 끼리 참 |
| 판 경계 | `python3 - <e37_boundary.py` · `python3.11 - <e37_boundary_py311.py` | 2씩 | 3.11 `TypeError`+경고 둘 · 3.12 참·거짓 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★ `EnumType` 이 가진 던더 목록 | 3.11 → 3.12 에서 `__getattr__` 이 빠졌다 |
| ★ 멤버의 해시가 이름의 해시인 것 | 문서가 정하지 않는다 |
| 멤버가 클래스 `__dict__` 에 사는 것 | 구현이 멤버를 어디에 두느냐의 일이다 |
| 예외·경고 **문구** 전부 | 종류는 계약, 문구는 아니다 |

★ **안 흔들리는 칸** — 격자의 참·거짓·예외 종류 · **「갈린 칸 8 / 18」** · 순회 순서 · `auto()` 값 · `json.dumps` 결과 문자열 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **속도.** 그리고 **3.10 이하 판**(도구 없음 — 못 잰 것).
