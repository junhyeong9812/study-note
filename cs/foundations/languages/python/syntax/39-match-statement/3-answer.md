# python/syntax/39-match-statement — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★ **`SyntaxError` 네 블록 중 캐럿이 있는 것은 하나뿐이다** — 옮겨 적다 빠뜨린 것이 아니라 **진단을 낸 단계가 다르다**(2번 답).

## 정답

### 1. 대소문자 둘 다 캡처 — 전역이 `'blue'`·`'green'` 으로 덮이고, 함수 안에서는 지역 `LIMIT` 이 생긴다

**출력**

```python
# e39_capture.py
red = "red"
RED = "red"


class Palette:
    RED = "red"


print("① 모듈 수준에서 bare 이름 red 로 비교하려 했다")
color = "blue"
match color:
    case red:
        print("   red 갈래에 들어왔다")
print("   match 뒤의 red :", repr(red))

print("② 대문자 RED 도 똑같이 써 본다")
color = "green"
match color:
    case RED:
        print("   RED 갈래에 들어왔다")
print("   match 뒤의 RED :", repr(RED))

print("③ 점이 있는 이름 Palette.RED")
for color in ("red", "blue"):
    match color:
        case Palette.RED:
            print("   %-5s -> Palette.RED 갈래" % color)
        case _:
            print("   %-5s -> _ 갈래" % color)

print("④ 함수 안에서")
LIMIT = 10


def check(n):
    match n:
        case LIMIT:
            return "LIMIT 갈래, LIMIT=%r" % LIMIT


print("   check(3)  :", check(3))
print("   전역 LIMIT :", LIMIT)
print("   check 의 지역 이름 :", check.__code__.co_varnames)

print("⑤ 캡처에 가드를 붙이고 뒤에 case 를 하나 더")


def guarded(n):
    match n:
        case x if x == LIMIT:
            return "가드 갈래"
        case _:
            return "_ 갈래"


print("   guarded(10) :", guarded(10), "/ guarded(3) :", guarded(3))
```

```text
===== python3 - <e39_capture.py =====
① 모듈 수준에서 bare 이름 red 로 비교하려 했다
   red 갈래에 들어왔다
   match 뒤의 red : 'blue'
② 대문자 RED 도 똑같이 써 본다
   RED 갈래에 들어왔다
   match 뒤의 RED : 'green'
③ 점이 있는 이름 Palette.RED
   red   -> Palette.RED 갈래
   blue  -> _ 갈래
④ 함수 안에서
   check(3)  : LIMIT 갈래, LIMIT=3
   전역 LIMIT : 10
   check 의 지역 이름 : ('n', 'LIMIT')
⑤ 캡처에 가드를 붙이고 뒤에 case 를 하나 더
   guarded(10) : 가드 갈래 / guarded(3) : _ 갈래
(exit 0)
```

**왜 그런가**

* ★★★ **①** — `color` 가 `"blue"` 인데 `red` 갈래에 들어오고, **`red` 가 `'blue'` 로 덮였다.** `case red:` 는 **`red = color`** 다.
* ★★★ **②** — **대문자 `RED` 도 똑같다**(`'green'` 으로 덮임). **대소문자가 아니라 점이 가른다**(7번 답).
* ★★ **③** — `Palette.RED` 는 **점이 있어 값 패턴**이다. `"red"` 만 맞고 `"blue"` 는 `_` 로 간다.
* ★★ **④** — 함수 안에서는 **지역 이름 `LIMIT`** 이 생겨 `check(3)` 이 **`LIMIT=3`** 을 돌려주고 **전역은 `10` 그대로**다.
  `co_varnames` 가 `('n', 'LIMIT')` — 캡처는 **대입**이라 [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 규칙대로 지역이 된다.
* ★ **⑤** — **가드**가 붙으면 반박 가능해져 뒤에 `case _:` 를 둘 수 있다.
* ★★ **①·②·④ 가 전부 컴파일을 통과했다** — 캡처가 **마지막 `case`** 였기 때문이다(8번 답).

### 2. 넷 다 `SyntaxError` · `(exit 1)` — 앞 셋은 두 줄뿐, `**_` 만 소스 줄과 캐럿이 있다

**출력**

```python
# e39_unreachable.py
red = "red"
color = "blue"
match color:
    case red:
        print("red 갈래")
    case "blue":
        print("blue 갈래")
```

```text
===== python3 - <e39_unreachable.py =====
  File "<stdin>", line 4
SyntaxError: name capture 'red' makes remaining patterns unreachable
(exit 1)
```

```python
# e39_wildcard_first.py
match "blue":
    case _:
        print("_ 갈래")
    case "blue":
        print("blue 갈래")
```

```text
===== python3 - <e39_wildcard_first.py =====
  File "<stdin>", line 2
SyntaxError: wildcard makes remaining patterns unreachable
(exit 1)
```

```python
# e39_or_names.py
match (1, 2):
    case (a, 0) | (0, b):
        print(a, b)
```

```text
===== python3 - <e39_or_names.py =====
  File "<stdin>", line 2
SyntaxError: alternative patterns bind different names
(exit 1)
```

```python
# e39_double_star_underscore.py
match {"k": 1}:
    case {"k": 1, **_}:
        print("k 갈래")
```

```text
===== python3 - <e39_double_star_underscore.py =====
  File "<stdin>", line 2
    case {"k": 1, **_}:
                    ^
SyntaxError: invalid syntax
(exit 1)
```

**왜 그런가**

* ★★★ **첫 블록** — `name capture 'red' makes remaining patterns unreachable`, **`line 4`**(`case red:`). **한 줄도 실행되지 않았다.**
* ★★ **둘째 블록** — `wildcard makes remaining patterns unreachable`. 같은 규칙(반박 불가는 마지막에만)의 다른 문구.
* ★★ **셋째 블록** — `alternative patterns bind different names`. OR 의 갈래가 **다른 이름**을 묶으면 **맞은 갈래에 따라 없는 이름**이 생긴다.
* ★★ **넷째 블록** — `invalid syntax` + **소스 줄 + 캐럿**. `**_` 는 **문법에 없다**(`**rest` 는 된다).
* ★★★ **캐럿 유무가 단계를 말한다** — 앞 셋은 **파서를 통과한 뒤 컴파일 단계**가 잡아 소스 줄도 캐럿도 없고,
  넷째만 **파서**가 잡아 캐럿이 있다. ★ 넷 다 **실행 전**이라 `print` 가 한 줄도 안 나왔다.

### 3. 열한 대상이 열한 종류로 한 번씩 — `'hello'` 는 시퀀스가 아니라 AS 로

**출력**

```python
# e39_kinds.py
from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    RED = 1


@dataclass
class Pt:
    x: int
    y: int


def kind(subject):
    match subject:
        case None:
            return "리터럴(None)"
        case 0 | 1:
            return "OR(리터럴 0 | 1)"
        case Color.RED:
            return "값(Color.RED)"
        case ("g"):
            return "그룹((\"g\"))"
        case [first, *rest]:
            return "시퀀스 first=%r rest=%r" % (first, rest)
        case {"op": op}:
            return "매핑 op=%r" % op
        case Pt(0, y):
            return "클래스(위치) y=%r" % y
        case Pt(x=x, y=0):
            return "클래스(키워드) x=%r" % x
        case str() as text:
            return "AS text=%r" % text
        case float(v) if v < 0:
            return "가드 v=%r" % v
        case other:
            return "캡처 other=%r" % other


subjects = [None, 1, Color.RED, "g", (7, 8, 9), {"op": "+", "z": 0},
            Pt(0, 5), Pt(4, 0), "hello", -2.5, 2.5]
for s in subjects:
    print("%-22r -> %s" % (s, kind(s)))

print("--- match 42 / case _ 뒤 ---")
match 42:
    case _:
        pass
print("'_' in globals() :", "_" in globals())
```

```text
===== python3 - <e39_kinds.py =====
None                   -> 리터럴(None)
1                      -> OR(리터럴 0 | 1)
<Color.RED: 1>         -> 값(Color.RED)
'g'                    -> 그룹(("g"))
(7, 8, 9)              -> 시퀀스 first=7 rest=[8, 9]
{'op': '+', 'z': 0}    -> 매핑 op='+'
Pt(x=0, y=5)           -> 클래스(위치) y=5
Pt(x=4, y=0)           -> 클래스(키워드) x=4
'hello'                -> AS text='hello'
-2.5                   -> 가드 v=-2.5
2.5                    -> 캡처 other=2.5
--- match 42 / case _ 뒤 ---
'_' in globals() : False
(exit 0)
```

**왜 그런가**

* ★ **`None`** 은 리터럴(`is`), **`1`** 은 OR, **`Color.RED`** 는 값 패턴(`==`), **`"g"`** 는 그룹.
* ★ **`(7, 8, 9)`** 는 시퀀스 — `rest` 는 **리스트** `[8, 9]` 로 모인다(튜플이 대상이어도).
* ★ **`{"op": "+", "z": 0}`** 는 **남는 키 `z` 가 있어도** 매핑에 맞았다.
* ★ **`Pt(0, 5)`** 는 위치 패턴 — dataclass 의 **`__match_args__`** 덕. **`Pt(4, 0)`** 은 첫 클래스 패턴(`x` 가 0)에 떨어지고 키워드 패턴에 맞았다.
* ★★ **`'hello'`** 는 `[first, *rest]` 에 **안 맞았다** — 문자열은 시퀀스 패턴에서 **빠진다.** 그래서 AS 로 갔다.
* ★ **`-2.5`** 는 가드(`v < 0`)에 맞고, **`2.5`** 는 가드에서 떨어져 **마지막 캡처**로 갔다.
* ★ **`'_' in globals()` 가 `False`** — `_` 는 이름을 **안 묶는다.**

### 4. `str`·`bytes`·`bytearray`·`Bag` 이 안 맞고 `RegBag` 은 맞는다 · 남는 키 허용 · `defaultdict` 에 키가 안 생긴다

**출력**

```python
# e39_sequence.py
import collections.abc


class Bag:
    def __init__(self, *items):
        self.items = list(items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


class RegBag(Bag):
    pass


collections.abc.Sequence.register(RegBag)


def two(s):
    match s:
        case [a, b]:
            return "시퀀스 a=%r b=%r" % (a, b)
        case _:
            return "안 맞음"


subjects = [[1, 2], (1, 2), range(2), "ab", b"ab", bytearray(b"ab"),
            {1, 2}, iter([1, 2]), (x for x in [1, 2]), Bag(1, 2), RegBag(1, 2)]
for s in subjects:
    label = type(s).__name__
    print("%-10s abc.Sequence=%-5s -> %s"
          % (label, isinstance(s, collections.abc.Sequence), two(s)))
```

```text
===== python3 - <e39_sequence.py =====
list       abc.Sequence=True  -> 시퀀스 a=1 b=2
tuple      abc.Sequence=True  -> 시퀀스 a=1 b=2
range      abc.Sequence=True  -> 시퀀스 a=0 b=1
str        abc.Sequence=True  -> 안 맞음
bytes      abc.Sequence=True  -> 안 맞음
bytearray  abc.Sequence=True  -> 안 맞음
set        abc.Sequence=False -> 안 맞음
list_iterator abc.Sequence=False -> 안 맞음
generator  abc.Sequence=False -> 안 맞음
Bag        abc.Sequence=False -> 안 맞음
RegBag     abc.Sequence=True  -> 시퀀스 a=1 b=2
(exit 0)
```

```python
# e39_mapping.py
from collections import defaultdict


def pick(m):
    match m:
        case {"id": i, **rest}:
            return "id=%r rest=%r" % (i, rest)
        case _:
            return "안 맞음"


print("① 남는 키")
print("   ", pick({"id": 1}))
print("   ", pick({"id": 1, "name": "a", "tags": []}))
print("   ", pick({"name": "a"}))

print("② defaultdict 에 없는 키를 물으면")
d = defaultdict(list, {"name": "a"})
print("   ", pick(d))
print("    match 뒤의 키 목록 :", sorted(d))
print("    d['id'] 로 직접 읽은 뒤 :", d["id"], sorted(d))

print("③ 키 개수로 끊고 싶으면")


def exactly_id(m):
    match m:
        case {"id": i, **rest} if not rest:
            return "id 하나뿐 i=%r" % i
        case _:
            return "안 맞음"


print("   ", exactly_id({"id": 1}), "/", exactly_id({"id": 1, "x": 0}))
```

```text
===== python3 - <e39_mapping.py =====
① 남는 키
    id=1 rest={}
    id=1 rest={'name': 'a', 'tags': []}
    안 맞음
② defaultdict 에 없는 키를 물으면
    안 맞음
    match 뒤의 키 목록 : ['name']
    d['id'] 로 직접 읽은 뒤 : [] ['id', 'name']
③ 키 개수로 끊고 싶으면
    id 하나뿐 i=1 / 안 맞음
(exit 0)
```

**왜 그런가**

* ★★★ **시퀀스** — 문자열 셋은 **`abc.Sequence` 가 참인데도** 레퍼런스가 이름으로 뺀다.
  ★★ **`Bag` 은 `__len__`·`__getitem__` 이 있는데 안 맞고, `Sequence.register` 한 `RegBag` 은 맞는다** — 보는 것은 **프로토콜이 아니라 명부**다.
  ★ `set`·이터레이터·제너레이터는 명부에 없다.
* ★★ **매핑 ①** — **적은 키만** 본다. 남는 키는 `rest` 로.
* ★★ **매핑 ②** — `defaultdict` 에 없는 `id` 를 물어도 **안 맞고 키도 안 생겼다.** 직접 `d['id']` 로 읽어야 `[]` 가 생긴다.
* ★ **매핑 ③** — 「키가 정확히 이것뿐」은 **`**rest` + 가드 `not rest`**.

### 5. `Plain(a, b)` 만 `TypeError` · `True` 는 `int(n)` · `1` 은 `case True` 에 안 맞는다 · `IntEnum` 값 패턴은 `1`·`1.0` 을 받는다

**출력**

```python
# e39_class.py
from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class DPt:
    x: int
    y: int


class NPt(NamedTuple):
    x: int
    y: int


class Plain:
    def __init__(self, x, y):
        self.x = x
        self.y = y


print("① __match_args__")
print("   DPt  :", DPt.__match_args__)
print("   NPt  :", NPt.__match_args__)
print("   Plain:", getattr(Plain, "__match_args__", "없음"))

print("② 위치 부분 패턴")
for obj in (DPt(1, 2), NPt(1, 2), Plain(1, 2)):
    try:
        match obj:
            case DPt(a, b) | NPt(a, b) | Plain(a, b):
                print("   %-5s a=%r b=%r" % (type(obj).__name__, a, b))
    except TypeError as exc:
        print("   %-5s %s: %s" % (type(obj).__name__, type(exc).__name__, exc))

print("③ 키워드 부분 패턴")
match Plain(1, 2):
    case Plain(x=1, y=b):
        print("   Plain(x=1, y=b) b=%r" % b)

print("④ 내장 타입 하나짜리 위치 패턴")
for v in (5, 5.0, True, "5"):
    match v:
        case int(n):
            print("   %-5r -> int(n) n=%r" % (v, n))
        case float(n):
            print("   %-5r -> float(n) n=%r" % (v, n))
        case _:
            print("   %-5r -> _" % (v,))

print("⑤ 리터럴 1 과 True")
for v in (1, 1.0, True):
    match v:
        case True:
            print("   %-5r -> case True" % (v,))
        case 1:
            print("   %-5r -> case 1" % (v,))

print("⑥ 순서를 바꿔 case 1 을 위에")
for v in (1, True):
    match v:
        case 1:
            print("   %-5r -> case 1" % (v,))
        case True:
            print("   %-5r -> case True" % (v,))

print("⑦ 값 패턴에 IntEnum 멤버")
from enum import IntEnum


class Level(IntEnum):
    LOW = 1


for v in (1, 1.0, Level.LOW):
    match v:
        case Level.LOW:
            print("   %-12r -> case Level.LOW" % (v,))
        case _:
            print("   %-12r -> _" % (v,))
```

```text
===== python3 - <e39_class.py =====
① __match_args__
   DPt  : ('x', 'y')
   NPt  : ('x', 'y')
   Plain: 없음
② 위치 부분 패턴
   DPt   a=1 b=2
   NPt   a=1 b=2
   Plain TypeError: Plain() accepts 0 positional sub-patterns (2 given)
③ 키워드 부분 패턴
   Plain(x=1, y=b) b=2
④ 내장 타입 하나짜리 위치 패턴
   5     -> int(n) n=5
   5.0   -> float(n) n=5.0
   True  -> int(n) n=True
   '5'   -> _
⑤ 리터럴 1 과 True
   1     -> case 1
   1.0   -> case 1
   True  -> case True
⑥ 순서를 바꿔 case 1 을 위에
   1     -> case 1
   True  -> case 1
⑦ 값 패턴에 IntEnum 멤버
   1            -> case Level.LOW
   1.0          -> case Level.LOW
   <Level.LOW: 1> -> case Level.LOW
(exit 0)
```

**왜 그런가**

* ★ **①** — dataclass·`NamedTuple` 은 `__match_args__` 가 **자동**이고 손으로 쓴 `Plain` 은 **없다.**
* ★★ **②** — `Plain() accepts 0 positional sub-patterns (2 given)` — **`SyntaxError` 가 아니라 실행 중 `TypeError`** 다. 그 `case` 에 **닿을 때** 난다.
* ★ **③** — 키워드 부분 패턴은 `__match_args__` 없이도 된다.
* ★★ **④** — `int(n)` 은 **대상 전체**를 묶는다. **`True` 는 `int` 의 하위**라 `int(n)` 으로 갔다.
* ★★★ **⑤** — `1.0` 은 `case 1` 에 맞고(`==`), **`1` 은 `case True` 에 안 맞는다**(`is`).
* ★★ **⑥** — 순서를 바꾸면 **`True` 도 `case 1` 에 걸린다** — `True == 1` 이기 때문이다.
* ★ **⑦** — 값 패턴 `Level.LOW` 가 **`1`·`1.0` 도 받는다.** `==` 로 견주고 `IntEnum` 은 `int` 로서 답한다([37번](../37-enum/2-summary.md)).

### 6. `YELLOW -> None` · 경고 0 · `(exit 0)`

**출력**

```python
# e39_exhaust.py
import warnings
from enum import Enum


class Light(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3


def action(light):
    match light:
        case Light.RED:
            return "정지"
        case Light.GREEN:
            return "진행"


with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    for light in Light:
        print("%-12s -> %r" % (light.name, action(light)))
print("잡힌 경고 수 :", len(caught))
```

```text
===== python3 - <e39_exhaust.py =====
RED          -> '정지'
YELLOW       -> None
GREEN        -> '진행'
잡힌 경고 수 : 0
(exit 0)
```

**왜 그런가**

* ★★★ 어느 `case` 에도 안 맞으면 **`match` 는 그냥 지나간다.** 함수가 끝까지 가서 **암묵적 `None`**.
* ★★★ **「잡힌 경고 수 : 0」·`(exit 0)`** — **침묵이 결론**이다. 멤버 **셋 중 하나**가 조용히 빠졌다.
* ★ 처방 — **`case _: raise ValueError(light)`** 를 마지막에 둔다.

### 7. 점이다 — 대소문자는 관계없다 · 상수를 클래스·열거형·모듈 속성으로 옮긴다

**왜 그런가**

* ★★★ 레퍼런스 문법에서 캡처 패턴은 **점 없는 이름**, 값 패턴은 **점 있는 이름**(*"`NAME1.NAME2` will succeed only if `<subject> == NAME1.NAME2`"*)이다.
  **대소문자 조건은 문법 어디에도 없다** — 1번의 ②가 실행 증거다.
* ★★ 모듈 상수를 값 패턴으로 쓰는 법 — **점을 만든다.**
  클래스 속성(`Palette.RED`) · 열거형 멤버(`Color.RED`) · **다른 모듈의 속성**(`import config` 후 `config.DEFAULT`).
* ★ 흔한 설명 「소문자 이름이 캡처가 된다」는 **소문자 변수가 흔해서 생긴 말**일 뿐, 규칙은 아니다.

### 8. 「반박 불가 `case` 는 하나, 마지막에만」 — 마지막은 「그 밖 전부」라는 정당한 쓰임이다

**왜 그런가**

* ★★★ 레퍼런스 — *"A match statement may have at most one irrefutable case block, and it must be last."*
  이 한 문장이 2번의 **앞 두 블록**을 만든다.
* ★★ **못 막는 자리** — 캡처가 **마지막 `case`** 일 때(1번의 ①·②·④) · 캡처에 **가드**가 붙었을 때(1번의 ⑤).
* ★★ **안 막는 것이 옳은 이유** — 마지막 캡처(`case other:`)는 「**나머지 전부를 받아 이름을 붙인다**」는 **정상 문법**이다(3번의 마지막 `case other:`).
  컴파일러는 **`case LIMIT:` 이 비교를 의도한 것인지 나머지를 받으려는 것인지** 모양만으로 가를 수 없다.
  ★ 그래서 **점을 쓰는 습관**만이 이 자리를 막는다.

### 9. 새 변수가 되고 에러 하나 + 경고 다섯 · 함정은 같고 안전망 두께가 다르다

**왜 그런가**

* ★★ [Rust 18번](../../../rust/syntax/18-match-and-exhaustiveness/2-summary.md)의 실측 — `Event::` 를 빼먹은 **`Click =>`** 이 **새 변수를 묶는 팔**이 됐고,
  **E0170**(``pattern binding `Click` is named the same as one of the variants``, 기본 deny 라 **에러**) 하나와
  **경고 다섯**(`unreachable pattern` 둘 · `unused variable` · `dead_code` · `non_snake_case`)이 나왔다.
  ★ 그 편이 「**대문자 이름도 변수 패턴이다**」라고 적었다 — **파이썬과 같은 함정**이다.
* ★★★ **같은 점** — 두 언어 모두 **경로 없는 맨 이름은 무엇이든 받는 바인딩**이다. 대소문자가 아니라 **경로(`.`·`::`)** 가 가른다.
* ★★★ **다른 점 둘**
  ① Rust 는 **변형 이름과 같은 바인딩을 에러**(E0170)로 막는다 — 파이썬은 **마지막 자리면 아무 말이 없다.**
  ② Rust 는 **완결성**을 센다(E0004) — 파이썬은 **안 센다**(6번 — 경고 0).
* ★ Rust 쪽 예외도 그 편이 적었다 — **`use Event::*;`** 로 변형을 열어 두면 E0170 이 안 난다(진짜 변형을 짚은 것이 되므로).

### 10. 앞은 보장 · 뒤 둘은 구현 — 전문을 실은 이유는 절대 경로가 안 박히기 때문

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| 반박 불가 `case` 는 **하나, 마지막에만** | **언어 보장** | 레퍼런스 |
| ★ 그 위반이 **컴파일 단계**에서 잡혀 **캐럿이 없다** | **CPython 구현**(이 판의 관찰) | 실행 — 판이 오르면 바뀔 수 있다 |
| ★ 매핑 패턴이 **`defaultdict` 의 기본값 공장을 안 부른다** | **CPython 구현** | 실행(4번 ②) |

* ★★ **전문을 실은 이유** — `match` 의 규칙 위반은 **실행 전 `SyntaxError`** 라 **스택 프레임이 없다.**
  `File "<stdin>", line N` 만 나오고 **표준 라이브러리 경로가 안 박힌다** — 재대조에서 **한 글자도 안 흔들린다.**
* ★ 형제 편들(36·37·38)은 예외가 **`dataclasses.py`·`enum.py`·`typing.py` 를 지나며** 절대 경로가 박혀서 **타입과 메시지만** 찍었다.
  **같은 규칙(흔들리는 칸을 안 싣는다)을 지킨 결과가 반대로 나온 것**이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 판 + 소프트 키워드 | `python3 - <e39_version.py` | 2(캡처 + 재대조) | 3.12.3 · `match`·`case` 소프트 키워드 |
| 캡처 함정 | `python3 - <e39_capture.py` | 2 | 대소문자 둘 다 덮어씀 · 함수 안은 지역 |
| 컴파일러가 막는 자리 | `python3 - <e39_unreachable.py` · `<e39_wildcard_first.py` · `python3.11 - <e39_unreachable_py311.py` | 2씩 | `SyntaxError` · 캐럿 없음 · `(exit 1)` · 두 판 같음 |
| OR 이름 불일치 · `**_` | `python3 - <e39_or_names.py` · `<e39_double_star_underscore.py` | 2씩 | 앞은 캐럿 없음 · **뒤는 캐럿 있음** |
| 패턴 종류 전수 | `python3 - <e39_kinds.py` | 2 | 열한 대상 → 열한 갈래 |
| 시퀀스·매핑 | `python3 - <e39_sequence.py` · `<e39_mapping.py` | 2씩 | 문자열 셋·`Bag` 제외 · 남는 키 허용 |
| 클래스·리터럴 | `python3 - <e39_class.py` | 2 | `Plain` 만 `TypeError` · `True` 는 `is` |
| 완결성 | `python3 - <e39_exhaust.py` | 2 | `YELLOW -> None` · 경고 0 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★ 컴파일 단계 `SyntaxError` 에 **캐럿이 없는 것** | 판이 오르면 붙을 수 있다 |
| 진단 **문구** 넷 | 문구는 계약이 아니다 |
| 매핑 패턴과 `defaultdict` | 구현이 키를 어떻게 읽느냐의 일이다 |

★ **안 흔들리는 칸** — 골라진 `case` · 캡처된 값 · `SyntaxError` 의 종류와 `line N` · 「잡힌 경고 수」 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **속도**(부적용) · **타입 검사기가 빠진 `case` 를 잡는지**(도구 없음 — 못 잰 것).
