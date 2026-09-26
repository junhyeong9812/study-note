# python/syntax/47-json — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`json`(3.12)](https://docs.python.org/3.12/library/json.html) —
>   `dumps` 의 주석 *"Keys in key/value pairs of JSON are always of the type str. When a dictionary is converted into JSON, all the keys of the dictionary are coerced to strings. As a result of this, if a dictionary is converted into JSON and then back into a dictionary, the dictionary may not equal the original one."* ·
>   변환표 *"list, tuple"* → array · *"int, float, int- & float-derived Enums"* → number
> - `allow_nan` — *"If True (the default), their JavaScript equivalents (NaN, Infinity, -Infinity) are used."* · `JSONEncoder` 절의 *"This behavior is not JSON specification compliant, but is consistent with most JavaScript based encoders and decoders."*
> - `object_hook` — *"will be called with the result of every JSON object decoded and its return value will be used in place of the given dict"* · *"If object_hook is also defined, the object_pairs_hook takes priority."*
> - 「Repeated Names Within an Object」 — *"By default, this module does not raise an exception; instead, it ignores all but the last name-value pair for a given name"*
> - `check_circular` — *"If False, the circular reference check for container types is skipped and a circular reference will result in a RecursionError (or worse)."*
> - `ensure_ascii` — *"If True (the default), the output is guaranteed to have all incoming non-ASCII characters escaped."* · `default` — *"A function that is called for objects that can't otherwise be serialized."*
> - 「Implementation Limitations」 — *"it is common for JSON numbers to be deserialized into IEEE 754 double precision numbers and thus subject to that representation's range and precision limitations"*
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 두 블록을 더 던졌다.\
> ★★★ **이 문서가 잰 것은 「글자」·「타입」·「같은가」·「호출 순서」·「개수」뿐이다** — 시간·메모리는 한 번도 재지 않았다. 「C 가속이 빠르다」도 **재지 않았다.**\
> **버전**(문서의 `versionadded`·`versionchanged` 표기) — `object_pairs_hook` **3.1**, int·float 파생 `Enum` 지원 **3.4**, 선택 인자 전부 키워드 전용 **3.6**, 기본 `parse_int` 의 정수 글자 길이 한도 **3.11**.\
> ★ **구현 대 언어 보장 한 줄** — 위 문서 문장들이 보장이고, **예외 문구**와 **C 가속 부품의 존재**는 CPython 의 것이다(동작 9 에서 3.11 과 3.12 의 문구가 실제로 갈렸다).\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★ 판이 오르면 **예외 문구** — `RecursionError` 문구가 3.11 과 3.12 에서 실제로 달랐다(동작 9) | ★★ 격자의 마지막 줄 **「… N / M」** · `dumps` 가 낸 **글자** |
> | — (주소·시간을 한 곳도 안 찍었다 · `set` 은 **`sorted` 를 거쳐서만** 찍었다) | `loads` 뒤 **타입 이름** · 훅이 불린 **순서와 횟수** |
>
> **선행** — [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)(★★★ **키가 되는 조건과 「`1`·`1.0`·`True` 는 한 칸」** — 12편이 「dict 키가 문자열로 바뀌는 것」을 이 주제로 넘겼다) ·
> [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md)(「set 은 JSON 으로 못 나간다」를 이 주제로 넘겼다) ·
> [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md)(`ensure_ascii` 와 `backslashreplace` 를 이 주제로 넘겼다).

## 한눈에 — 쉽게 말하면

**`json` 은 「규격 상자만 받는 택배」다.** 받는 쪽은 **상자 여섯 종류**(객체·배열·문자열·숫자·참거짓·`null`)만 안다.
파이썬 물건을 부치면 포장 담당(`dumps`)이 **가장 가까운 규격 상자**에 옮겨 담는다.

* 튜플은 **배열 상자**에 들어간다 — 되돌려 받으면(`loads`) **리스트**로 온다. 「원래 튜플이었다」를 적을 칸이 상자에 없다.
* ★ 상자의 **이름표(키)는 글자만** 된다 — `1` 이라는 이름표는 `"1"` 로 고쳐 써서 붙인다. 되돌려 받으면 `"1"` 이다.
* 규격 상자가 없는 물건(`set`·`bytes`·`Decimal`·`datetime`)은 **접수를 거절**한다(`TypeError`). `default=` 가 「이건 이렇게 싸라」는 **포장 지침**이다.
* ★★ 그런데 이 택배사는 **규격에 없는 상자 하나를 기본으로 쓴다** — `NaN`·`Infinity`. JSON 규격에는 없는 글자라서 **다른 택배사(JS)는 못 받는다.**

```text
   파이썬 쪽                  JSON 상자                   다시 파이썬 쪽
   None  True  1  0.1   ->   null true 1 0.1        ->   None True 1 0.1        그대로
   (1, 2)               ->   [1, 2]                 ->   [1, 2]                 ★ 리스트로 온다
   {1: 'a'}             ->   {"1": "a"}             ->   {'1': 'a'}             ★ 키가 글자로 온다
   {1}  b'a'  Decimal   ->   TypeError (접수 거절)
   float('nan')         ->   NaN   ★ JSON 규격 밖 글자 — allow_nan=False 면 ValueError
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 규격 상자 여섯 종류 | JSON 의 값 종류 | 되읽은 타입이 `dict`·`list`·`str`·`int`·`float`·`bool`·`NoneType` 뿐 |
| 가장 가까운 상자에 옮겨 담기 | `dumps` 의 변환표 | 튜플·`namedtuple` → 배열 |
| 되돌려 받기 | `loads(dumps(x))` | ★ **타입과 `repr` 을 원본과 견준다** |
| 이름표는 글자만 | 객체 키는 늘 `str` | `{1: 'a'}` 가 `{'1': 'a'}` 로 돌아온다 |
| 접수 거절 | `TypeError` | `set`·`bytes`·`Decimal`·`datetime` |
| 포장 지침 | `default=` | **못 싣는 값에만** 불린다 |
| 규격 밖 상자 | `NaN`·`Infinity` | `allow_nan=False` 로 걸러 본다 |
| 받는 쪽 검수원 | `object_hook` | 상자를 열 때마다 한 번 — **안쪽 상자부터** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**사용자 id 를 키로 한 캐시를 JSON 파일에 저장했다가 다시 읽었더니 `cache[42]` 가 `KeyError`**」와
「**파이썬이 보낸 응답을 브라우저가 `JSON.parse` 하다가 죽었다 — 값 하나가 `NaN` 이었다**」가 그것이다.\
앞엣것은 **이름표가 글자로 바뀐 것**이고, 뒤엣것은 **규격 밖 상자를 기본으로 보낸 것**이다.

> **직렬화(serialization)** — 메모리의 객체를 **글자나 바이트 한 줄**로 바꾸는 것. 되돌리는 것이 역직렬화.\
> 예: `json.dumps({'a': 1})` 가 `'{"a": 1}'` 을 만든다.

> **왕복(round trip)** — 바꿨다가 되돌렸을 때 **원래와 같은 것**이 돌아오는가.\
> 예: `json.loads(json.dumps((1, 2)))` 는 `[1, 2]` — 값은 비슷한데 **타입이 다르다.**

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 왕복 창이다.** 값을 `dumps` 로 내보내고 `loads` 로 되읽어 **타입 이름과 `repr` 을 원본과 견준다.** 「바뀐 행 / 거절 행」을 스크립트가 센다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **왕복 창**(`type(back) is type(x)` · `repr` 비교) | `dumps` 가 **무엇을 잃었나** | 다른 언어가 그 글자를 읽을 수 있나 |
| ② ★★★ **키 창**(키 하나짜리 dict · 겹치는 키) | 이름표가 **무엇으로 바뀌고 무엇이 사라지나** | — |
| ③ ★★ **`allow_nan=False` 창** | 그 글자가 **JSON 규격 밖**인가 | — |
| ④ ★★ **훅 호출 로그** | `object_hook` 이 **언제 · 몇 번 · 어떤 순서로** 불리나 | 시간 |
| ⑤ ★ **판 격자**(3.11 대 3.12) | 무엇이 **판을 타나** | 3.13 이후 |
| ⑥ ★ **`indent` 창** — `indent=None` 과 `indent=1` | **C 인코더와 파이썬 인코더**가 갈리는 자리 | 속도 |
| ★ **인용한 칸** — 「JS 가 그 글자를 읽나」 | — | 이 편은 JS 를 다시 돌리지 않았다 — [JS 31번](../../../js/syntax/31-json/2-summary.md) 동작 (4)·(7)의 출력을 인용했다 |
| ★ **부적용인 창** — 시간 · 메모리 바이트 | — | 「C 가속이 빠르다」·「`ensure_ascii=False` 가 작다(바이트 말고 속도)」를 **한 번도 재지 않았다** |

★★ **①이 이 주제의 네 번째 창이다.** `dumps` 는 튜플·`namedtuple`·`IntEnum`·int 하위 클래스를 **에러 없이** 받는다.
**「에러 없이 돌았다」는 아무것도 말하지 않는다** — 되읽은 값의 **타입**을 원본과 견줘야 무엇을 잃었는지 보인다.

## 이 주제가 답하려는 질문

1. ★★★ **`dumps` → `loads` 왕복에서 무엇이 그대로 돌아오고 무엇이 바뀌나** — 값 종류마다 **같다 · 바뀐다 · 거절** 중 어디인가. 그리고 **dict 키**는 무엇이 되나.
2. ★★ **파이썬 `json` 이 기본으로 하는 일 중 「JSON 규격 밖」은 무엇인가** — `NaN`·`Infinity` 를 내보내고 읽는 것, 같은 키 둘을 내보내는 것.
3. **손을 대는 자리들 — `default=`·`object_hook`·`parse_*`·`sort_keys`·`ensure_ascii` 는 언제 · 무엇에 · 어떤 순서로 불리나.**

★ 첫째가 이 주제의 인출 목표다.
**「JSON 에는 상자 여섯 종류와 글자 이름표뿐이다」라는 한 문장으로 튜플·키·`set`·`NaN` 을 전부 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 타입 매핑 격자 — 같다 · 바뀐다 · 거절

**언제 쓰나** — 「이 객체를 JSON 으로 저장했다가 다시 읽으면 그대로 오나」를 물을 때.

```text
   왕복 창 — dumps 로 내보내고, loads 로 되읽고, 원본과 견준다

   x ──dumps──▶ 글자 ──loads──▶ back          판정
                                              type(back) is type(x) 이고 repr 이 같다  -> 같다
                                              에러 없이 돌았지만 위가 거짓           -> 바뀐다
   x ──dumps──▶ TypeError                     -> 거절
```

```python
# e47_grid.py
import collections
import datetime
import decimal
import enum
import fractions
import json
import math


class Level(enum.IntEnum):
    LOW = 1


class Color(str, enum.Enum):
    RED = "red"


class Num(int):
    pass


Point = collections.namedtuple("Point", "x y")

rows = [
    ("None", None),
    ("True", True),
    ("1", 1),
    ("10 ** 20", 10 ** 20),
    ("0.1", 0.1),
    ("-0.0", -0.0),
    ("float('nan')", math.nan),
    ("float('inf')", math.inf),
    ("-inf", -math.inf),
    ("chr(0xAC00)", chr(0xAC00)),
    ("[1, 'a']", [1, "a"]),
    ("(1, 2)", (1, 2)),
    ("Point(1, 2)", Point(1, 2)),
    ("{'a': 1}", {"a": 1}),
    ("{1: 'a'}", {1: "a"}),
    ("{1}", {1}),
    ("frozenset({1})", frozenset({1})),
    ("b'a'", b"a"),
    ("bytearray(b'a')", bytearray(b"a")),
    ("Decimal('1.5')", decimal.Decimal("1.5")),
    ("Fraction(1, 3)", fractions.Fraction(1, 3)),
    ("1 + 2j", 1 + 2j),
    ("date(2026, 9, 26)", datetime.date(2026, 9, 26)),
    ("Level.LOW (IntEnum)", Level.LOW),
    ("Color.RED (str, Enum)", Color.RED),
    ("Num(5) (int subclass)", Num(5)),
]


def cell(label, value):
    try:
        text = json.dumps(value)
    except TypeError as ex:
        return [label, "TypeError", "-", "거절", type(ex).__name__]
    back = json.loads(text)
    same = type(back) is type(value) and repr(back) == repr(value)
    try:
        json.dumps(value, allow_nan=False)
        strict = "통과"
    except ValueError as ex:
        strict = type(ex).__name__
    return [label, text, type(back).__name__, "같다" if same else "바뀐다", strict]


print("값 ; dumps 결과 ; loads 뒤 타입 ; 왕복 ; allow_nan=False 이면")
counts = collections.Counter()
strict_refused = 0
for label, value in rows:
    c = cell(label, value)
    if len(c) != 5 or any(";" in x for x in c):
        raise SystemExit("칸 수가 어긋났다: %r" % c)
    counts[c[3]] += 1
    strict_refused += c[4] == "ValueError"
    print(" ; ".join(c))

m = len(rows)
print()
print("같다 %d / %d · 바뀐다 %d / %d · 거절 %d / %d" % (
    counts["같다"], m, counts["바뀐다"], m, counts["거절"], m))
print("allow_nan=False 에서 ValueError 가 되는 행 : %d / %d" % (strict_refused, m))
print("왕복이 같은 값·같은 타입으로 안 돌아오는 행 : %d / %d" % (
    counts["바뀐다"] + counts["거절"], m))
```

```text
===== python3 - <e47_grid.py =====
값 ; dumps 결과 ; loads 뒤 타입 ; 왕복 ; allow_nan=False 이면
None ; null ; NoneType ; 같다 ; 통과
True ; true ; bool ; 같다 ; 통과
1 ; 1 ; int ; 같다 ; 통과
10 ** 20 ; 100000000000000000000 ; int ; 같다 ; 통과
0.1 ; 0.1 ; float ; 같다 ; 통과
-0.0 ; -0.0 ; float ; 같다 ; 통과
float('nan') ; NaN ; float ; 같다 ; ValueError
float('inf') ; Infinity ; float ; 같다 ; ValueError
-inf ; -Infinity ; float ; 같다 ; ValueError
chr(0xAC00) ; "\uac00" ; str ; 같다 ; 통과
[1, 'a'] ; [1, "a"] ; list ; 같다 ; 통과
(1, 2) ; [1, 2] ; list ; 바뀐다 ; 통과
Point(1, 2) ; [1, 2] ; list ; 바뀐다 ; 통과
{'a': 1} ; {"a": 1} ; dict ; 같다 ; 통과
{1: 'a'} ; {"1": "a"} ; dict ; 바뀐다 ; 통과
{1} ; TypeError ; - ; 거절 ; TypeError
frozenset({1}) ; TypeError ; - ; 거절 ; TypeError
b'a' ; TypeError ; - ; 거절 ; TypeError
bytearray(b'a') ; TypeError ; - ; 거절 ; TypeError
Decimal('1.5') ; TypeError ; - ; 거절 ; TypeError
Fraction(1, 3) ; TypeError ; - ; 거절 ; TypeError
1 + 2j ; TypeError ; - ; 거절 ; TypeError
date(2026, 9, 26) ; TypeError ; - ; 거절 ; TypeError
Level.LOW (IntEnum) ; 1 ; int ; 바뀐다 ; 통과
Color.RED (str, Enum) ; "red" ; str ; 바뀐다 ; 통과
Num(5) (int subclass) ; 5 ; int ; 바뀐다 ; 통과

같다 12 / 26 · 바뀐다 6 / 26 · 거절 8 / 26
allow_nan=False 에서 ValueError 가 되는 행 : 3 / 26
왕복이 같은 값·같은 타입으로 안 돌아오는 행 : 14 / 26
(exit 0)
```

그림 해설.

* ★★★ **마지막 줄 — 왕복이 같은 값·같은 타입으로 안 돌아오는 행 `14 / 26`.** 그 가운데 **바뀐다 6** 은 **에러가 없었다.**
  튜플·`namedtuple` → `list`, `{1: 'a'}` → 키가 `str`, `IntEnum`·`(str, Enum)`·int 하위 클래스 → **바탕 타입**(`int`·`str`)으로 돌아왔다.
  ★ 문서의 변환표가 *"list, tuple"* 를 한 칸(array)에 적는다 — 되읽을 때는 array 가 `list` 하나로만 간다(`json-to-py` 표). **돌아오는 길이 하나라 튜플을 되살릴 수 없다.**
* ★★★ **`float('nan')`·`inf`·`-inf` 는 왕복이 「같다」인데 `allow_nan=False` 에서 `ValueError`** (`3 / 26`) — **파이썬끼리는 되돌아오지만 JSON 규격 밖 글자**(`NaN`·`Infinity`)를 냈다는 뜻이다.
  ★ 그 글자를 JS 의 `JSON.parse('NaN')` 은 `SyntaxError` 로 거절한다 — [JS 31번](../../../js/syntax/31-json/2-summary.md) 동작 (4)의 출력이다(이 편은 JS 를 다시 돌리지 않았다).
* ★★ **거절 8** — `set`·`frozenset`·`bytes`·`bytearray`·`Decimal`·`Fraction`·`complex`·`date`. 전부 **`TypeError`** 다. JS 31번이 **JS 는 `set` 을 `{}` 로 조용히 바꾼다**고 적은 자리를 파이썬은 **시끄럽게** 거절한다.
* ★ **`-0.0` 은 부호째 돌아왔다**(`-0.0`). **`10 ** 20` 도 자릿수 그대로**다 — 파이썬 `int` 는 크기 한도가 없고 `json` 은 글자를 그대로 쓴다.
* ★ **`chr(0xAC00)`(「가」) 는 `"\uac00"` 로 나갔다** — `ensure_ascii` 기본값(동작 6).

같은 소스를 `python3.11` 에 먹였다(파일 이름만 `e47_grid_py311.py` — 소스는 한 글자도 같다).

```text
===== python3.11 - <e47_grid_py311.py =====
값 ; dumps 결과 ; loads 뒤 타입 ; 왕복 ; allow_nan=False 이면
None ; null ; NoneType ; 같다 ; 통과
True ; true ; bool ; 같다 ; 통과
1 ; 1 ; int ; 같다 ; 통과
10 ** 20 ; 100000000000000000000 ; int ; 같다 ; 통과
0.1 ; 0.1 ; float ; 같다 ; 통과
-0.0 ; -0.0 ; float ; 같다 ; 통과
float('nan') ; NaN ; float ; 같다 ; ValueError
float('inf') ; Infinity ; float ; 같다 ; ValueError
-inf ; -Infinity ; float ; 같다 ; ValueError
chr(0xAC00) ; "\uac00" ; str ; 같다 ; 통과
[1, 'a'] ; [1, "a"] ; list ; 같다 ; 통과
(1, 2) ; [1, 2] ; list ; 바뀐다 ; 통과
Point(1, 2) ; [1, 2] ; list ; 바뀐다 ; 통과
{'a': 1} ; {"a": 1} ; dict ; 같다 ; 통과
{1: 'a'} ; {"1": "a"} ; dict ; 바뀐다 ; 통과
{1} ; TypeError ; - ; 거절 ; TypeError
frozenset({1}) ; TypeError ; - ; 거절 ; TypeError
b'a' ; TypeError ; - ; 거절 ; TypeError
bytearray(b'a') ; TypeError ; - ; 거절 ; TypeError
Decimal('1.5') ; TypeError ; - ; 거절 ; TypeError
Fraction(1, 3) ; TypeError ; - ; 거절 ; TypeError
1 + 2j ; TypeError ; - ; 거절 ; TypeError
date(2026, 9, 26) ; TypeError ; - ; 거절 ; TypeError
Level.LOW (IntEnum) ; 1 ; int ; 바뀐다 ; 통과
Color.RED (str, Enum) ; "red" ; str ; 바뀐다 ; 통과
Num(5) (int subclass) ; 5 ; int ; 바뀐다 ; 통과

같다 12 / 26 · 바뀐다 6 / 26 · 거절 8 / 26
allow_nan=False 에서 ValueError 가 되는 행 : 3 / 26
왕복이 같은 값·같은 타입으로 안 돌아오는 행 : 14 / 26
(exit 0)
```

★ **두 판의 출력이 배너 줄을 빼고 한 글자도 같다** — 이 격자는 **판을 타지 않았다**(3.11 대 3.12, 갈린 칸 `0 / 26`).

**비용** — 왕복을 지키려면 **타입 정보를 글자 안에 직접 적어야** 한다(`{"__tuple__": [1, 2]}` 같은 약속 + `object_hook` 으로 되살리기). JSON 에는 그런 칸이 **원래 없다.**

### 2. ★★★ 키는 글자만 — 되읽으면 원래 타입으로 안 돌아오고, 겹치면 사라진다

**언제 쓰나** — 정수 id·`None`·`True` 를 키로 가진 dict 를 JSON 으로 저장할 때.

```text
   {1: 'a', '1': 'b'}          파이썬 dict — 1 과 '1' 은 다른 키 (hash 도 == 도 다르다)
        │ dumps — 키를 전부 글자로
        ▼
   {"1": "a", "1": "b"}        ★ 같은 이름표 둘 — dumps 는 막지 않는다
        │ loads — 같은 이름은 마지막 것만
        ▼
   {'1': 'b'}                  ★ 'a' 가 사라졌다. len 2 -> 1
```

```python
# e47_keys.py
import decimal
import enum
import json
import math


class Level(enum.IntEnum):
    LOW = 1


print("[1] 키 하나짜리 dict — 나간 키 · 되읽은 키 · 원본과 같은가")
singles = [
    ("'a'", "a"), ("1", 1), ("1.5", 1.5), ("-0.0", -0.0), ("True", True), ("False", False),
    ("None", None), ("float('nan')", math.nan), ("float('inf')", math.inf),
    ("10 ** 20", 10 ** 20), ("Level.LOW", Level.LOW),
    ("(1, 2)", (1, 2)), ("Decimal('1')", decimal.Decimal("1")), ("b'k'", b"k"),
]
changed = refused = 0
for label, key in singles:
    try:
        text = json.dumps({key: "v"})
    except TypeError as ex:
        print("   %-14s ; TypeError 「%s」" % (label, ex))
        refused += 1
        continue
    back = json.loads(text)
    (k2,) = back
    same = back == {key: "v"}
    changed += not same
    print("   %-14s ; %-26s ; %-24r ; %s" % (label, text, k2, same))
print("   원본과 다른 dict 로 돌아온 행 : %d / %d · TypeError : %d / %d" % (
    changed, len(singles) - refused, refused, len(singles)))

print("[2] 나가면 같은 글자가 되는 두 키")
pairs = [
    ("{1: 'a', '1': 'b'}", {1: "a", "1": "b"}),
    ("{'1': 'b', 1: 'a'}", {"1": "b", 1: "a"}),
    ("{True: 'a', 'true': 'b'}", {True: "a", "true": "b"}),
    ("{None: 'a', 'null': 'b'}", {None: "a", "null": "b"}),
    ("{1.0: 'a', '1.0': 'b'}", {1.0: "a", "1.0": "b"}),
]
lost = 0
for label, d in pairs:
    text = json.dumps(d)
    back = json.loads(text)
    lost += len(back) < len(d)
    print("   %-26s ; len %d ; %-24s ; loads %-12r ; len %d" % (label, len(d), text, back, len(back)))
print("   되읽으면 키가 줄어든 행 : %d / %d" % (lost, len(pairs)))

print("[3] 파이썬 dict 안에서 먼저 한 칸이 된 세 키")
d = {1: "정수", 1.0: "실수", True: "불리언"}
print("   len(d) :", len(d), "·", d)
print("   dumps  :", json.dumps(d, ensure_ascii=False))

print("[4] skipkeys=True")
print("   ", json.dumps({(1, 2): "t", "a": 1, b"k": 2}, skipkeys=True))
```

```text
===== python3 - <e47_keys.py =====
[1] 키 하나짜리 dict — 나간 키 · 되읽은 키 · 원본과 같은가
   'a'            ; {"a": "v"}                 ; 'a'                      ; True
   1              ; {"1": "v"}                 ; '1'                      ; False
   1.5            ; {"1.5": "v"}               ; '1.5'                    ; False
   -0.0           ; {"-0.0": "v"}              ; '-0.0'                   ; False
   True           ; {"true": "v"}              ; 'true'                   ; False
   False          ; {"false": "v"}             ; 'false'                  ; False
   None           ; {"null": "v"}              ; 'null'                   ; False
   float('nan')   ; {"NaN": "v"}               ; 'NaN'                    ; False
   float('inf')   ; {"Infinity": "v"}          ; 'Infinity'               ; False
   10 ** 20       ; {"100000000000000000000": "v"} ; '100000000000000000000'  ; False
   Level.LOW      ; {"1": "v"}                 ; '1'                      ; False
   (1, 2)         ; TypeError 「keys must be str, int, float, bool or None, not tuple」
   Decimal('1')   ; TypeError 「keys must be str, int, float, bool or None, not decimal.Decimal」
   b'k'           ; TypeError 「keys must be str, int, float, bool or None, not bytes」
   원본과 다른 dict 로 돌아온 행 : 10 / 11 · TypeError : 3 / 14
[2] 나가면 같은 글자가 되는 두 키
   {1: 'a', '1': 'b'}         ; len 2 ; {"1": "a", "1": "b"}     ; loads {'1': 'b'}   ; len 1
   {'1': 'b', 1: 'a'}         ; len 2 ; {"1": "b", "1": "a"}     ; loads {'1': 'a'}   ; len 1
   {True: 'a', 'true': 'b'}   ; len 2 ; {"true": "a", "true": "b"} ; loads {'true': 'b'} ; len 1
   {None: 'a', 'null': 'b'}   ; len 2 ; {"null": "a", "null": "b"} ; loads {'null': 'b'} ; len 1
   {1.0: 'a', '1.0': 'b'}     ; len 2 ; {"1.0": "a", "1.0": "b"} ; loads {'1.0': 'b'} ; len 1
   되읽으면 키가 줄어든 행 : 5 / 5
[3] 파이썬 dict 안에서 먼저 한 칸이 된 세 키
   len(d) : 1 · {1: '불리언'}
   dumps  : {"1": "불리언"}
[4] skipkeys=True
    {"a": 1}
(exit 0)
```

그림 해설.

* ★★★ **`[1]` — 원본과 다른 dict 로 돌아온 행 `10 / 11`.** `str` 키 하나만 그대로 왔다. `1` → `'1'`, `1.5` → `'1.5'`, **`True` → `'true'`**, **`None` → `'null'`**, `nan` → `'NaN'`.
  ★ 키를 글자로 바꾸는 법이 **값 자리와 같다** — `True` 는 `"True"` 가 아니라 JSON 식의 **`"true"`** 다. 12편이 이 주제로 넘긴 자리가 이것이다.
  ★ 문서 — *"all the keys of the dictionary are coerced to strings … the dictionary may not equal the original one."*
* ★★ **`(1, 2)`·`Decimal`·`bytes` 키는 `TypeError`** — 문구가 받는 키 목록을 그대로 말한다(`keys must be str, int, float, bool or None`). **값 자리에서는 튜플이 되는데 키 자리에서는 안 된다.**
* ★★★ **`[2]` — 되읽으면 키가 줄어든 행 `5 / 5`.** `dumps` 는 **같은 이름 둘**을 그대로 냈고(JS 31번 동작 (7)이 이미 본 글자다), **`loads` 가 마지막 것만 남겼다.**
  ★ **어느 쪽이 남나는 dict 의 삽입 순서가 정한다** — `{1: 'a', '1': 'b'}` 는 `'b'`, 순서를 뒤집은 `{'1': 'b', 1: 'a'}` 는 `'a'`.
  ★ 문서 — *"it ignores all but the last name-value pair for a given name"*.
* ★★ **`[3]` — 파이썬 안에서 이미 한 칸**이다. `{1: …, 1.0: …, True: …}` 는 **`len` 1**(12편 동작 3 — 키는 처음 것 `1`, 값은 나중 것 `'불리언'`). 그래서 `dumps` 에는 키가 **하나**(`"1"`)만 나간다.
  ★ **`[2]` 와 방향이 반대다** — `[3]` 은 **파이썬이 먼저 합치고**, `[2]` 는 **JSON 이 나중에 합친다.**
* ★ **`[4]` — `skipkeys=True`** 는 못 쓰는 키를 **말없이 뺀다.** 에러가 사라지는 대신 **데이터가 사라진다.**

**비용** — 정수 키를 되살리려면 **`object_hook` 으로 직접** 바꿔야 한다(동작 4 의 `[5]`). 그런데 그 훅은 **`'1'` 이 원래 `1` 이었는지 `'1'` 이었는지 모른다.**

### 3. ★★ `sort_keys` 는 바꾸기 전의 키로 정렬한다

**언제 쓰나** — 회귀 테스트·캐시 키처럼 **같은 dict 가 늘 같은 글자**가 되길 바랄 때(문서가 `sort_keys` 를 그 용도로 든다).

```text
   {10: 'b', 2: 'a'}   sort_keys=True
        정렬 키 = 원래 키 10, 2  (정수)     -> 2 < 10     -> {"2": "a", "10": "b"}
   {'10': 'b', '2': 'a'}
        정렬 키 = '10', '2'     (글자)     -> '10' < '2'  -> {"10": "b", "2": "a"}
   {2: 'a', 'b': 1}
        정수와 글자를 < 로 견줘야 한다      -> TypeError
```

```python
# e47_sortkeys.py
import json


def show(label, d):
    try:
        print("   %-28s -> %s" % (label, json.dumps(d, sort_keys=True)))
    except TypeError as ex:
        print("   %-28s -> TypeError 「%s」" % (label, ex))


print("[1] 키가 전부 문자열")
show("{'10': 'b', '2': 'a'}", {"10": "b", "2": "a"})
print("[2] 키가 전부 정수")
show("{10: 'b', 2: 'a'}", {10: "b", 2: "a"})
print("[3] 정수와 문자열이 섞이면")
show("{2: 'a', 'b': 1}", {2: "a", "b": 1})
show("{True: 1, 'a': 2}", {True: 1, "a": 2})
show("{None: 1, 'a': 2}", {None: 1, "a": 2})
print("[4] 정수와 실수만 섞이면")
show("{2: 'a', 1.5: 'b'}", {2: "a", 1.5: "b"})
print("[5] 나간 글자를 다시 sort_keys 로")
once = json.dumps({10: "b", 2: "a"}, sort_keys=True)
print("   한 번 :", once)
print("   두 번 :", json.dumps(json.loads(once), sort_keys=True))
```

```text
===== python3 - <e47_sortkeys.py =====
[1] 키가 전부 문자열
   {'10': 'b', '2': 'a'}        -> {"10": "b", "2": "a"}
[2] 키가 전부 정수
   {10: 'b', 2: 'a'}            -> {"2": "a", "10": "b"}
[3] 정수와 문자열이 섞이면
   {2: 'a', 'b': 1}             -> TypeError 「'<' not supported between instances of 'str' and 'int'」
   {True: 1, 'a': 2}            -> TypeError 「'<' not supported between instances of 'str' and 'bool'」
   {None: 1, 'a': 2}            -> TypeError 「'<' not supported between instances of 'str' and 'NoneType'」
[4] 정수와 실수만 섞이면
   {2: 'a', 1.5: 'b'}           -> {"1.5": "b", "2": "a"}
[5] 나간 글자를 다시 sort_keys 로
   한 번 : {"2": "a", "10": "b"}
   두 번 : {"10": "b", "2": "a"}
(exit 0)
```

그림 해설.

* ★★ **`[2]` 는 `"2"` 가 `"10"` 보다 앞**, **`[1]` 은 `"10"` 이 앞**이다 — 나간 글자는 둘 다 `"10"`·`"2"` 인데 순서가 반대다. **정렬이 글자로 바꾸기 전의 키 위에서** 일어났다는 증거다.
* ★★ **`[3]` — 정수·`bool`·`None` 키가 문자열 키와 섞이면 `TypeError`** — 파이썬의 `<` 가 그 둘을 못 견준다([31번](../31-comparison-protocol-and-sortability/2-summary.md)). 섞인 dict 는 `sort_keys` 없이는 잘 나가다가 **켜는 순간 터진다.**
* ★ **`[5]` — 같은 dict 를 한 번 나갔다 들어와 다시 `sort_keys` 하면 글자가 바뀐다.** 「같은 데이터면 같은 글자」가 **첫 번째 저장과 두 번째 저장 사이에서** 깨진다.

**비용** — `sort_keys` 를 쓸 거면 **키를 먼저 전부 `str` 로 맞춘다.** 그래야 정렬 순서와 나간 글자의 순서가 같은 규칙을 따른다.

### 4. ★★★ `object_hook` — 안쪽 객체부터, 객체에만

**언제 쓰나** — 읽으면서 날짜를 되살리거나 키를 고칠 때. JS 의 `reviver` 자리다.

```text
   '{"a": {"b": 1, "c": [2, {"e": 5}]}, "d": 4}'

   파이썬 object_hook — 객체(dict)가 다 만들어질 때마다 한 번        JS reviver (31번 동작 (4))
     1. {'e': 5}                                                       1. "b"=1   2. "0"=2   3. "1"=3
     2. {'b': 1, 'c': [...]}                                            4. "c"   5. "a"   6. "d"=4
     3. {'a': ..., 'd': 4}      ★ 뿌리가 마지막                          7. ""  (뿌리)  ★ 뿌리가 마지막
     숫자·배열에는 안 불린다 — 3 번                                    값 하나하나에 불린다 — 7 번
```

```python
# e47_hooks.py
import json

text = '{"a": {"b": 1, "c": [2, {"e": 5}]}, "d": 4}'

print("[1] object_hook 이 불린 순서")
log = []


def hook(d):
    log.append(sorted(d))
    return d


json.loads(text, object_hook=hook)
for i, keys in enumerate(log, 1):
    print("   %d. 키 %s" % (i, keys))
print("   불린 횟수 :", len(log), "· 글 안의 { 개수 :", text.count("{"))

print("[2] 돌려준 것이 dict 자리를 차지한다")
print("   ", json.loads(text, object_hook=lambda d: "<%d keys>" % len(d)))
print("   ", json.loads("[1, [2, 3], {}]", object_hook=lambda d: "H"))

print("[3] 같은 키가 둘인 글")
dup = '{"x": 1, "x": 2}'
print("   loads                   :", json.loads(dup))
print("   object_hook 이 받는 것   :", json.loads(dup, object_hook=lambda d: ("hook", d)))
print("   object_pairs_hook 이 받는 것 :", json.loads(dup, object_pairs_hook=lambda p: ("pairs", p)))
print("   둘 다 주면              :", json.loads(dup, object_pairs_hook=lambda p: ("pairs", p),
                                                object_hook=lambda d: ("hook", d)))


def no_dup(pairs):
    seen = [k for k, _ in pairs]
    if len(seen) != len(set(seen)):
        raise ValueError("duplicate key: %s" % sorted(k for k in set(seen) if seen.count(k) > 1))
    return dict(pairs)


print("[4] 중복을 거절하는 pairs 훅")
try:
    json.loads(dup, object_pairs_hook=no_dup)
except ValueError as ex:
    print("   ValueError 「%s」" % ex)

print("[5] 숫자 모양의 키를 int 로 바꾸는 훅")


def int_keys(d):
    return {int(k) if k.lstrip("-").isdigit() else k: v for k, v in d.items()}


src = {1: "a", "1": "b", 2: "c"}
back = json.loads(json.dumps(src), object_hook=int_keys)
print("   원본 :", src)
print("   훅 뒤 :", back)
```

```text
===== python3 - <e47_hooks.py =====
[1] object_hook 이 불린 순서
   1. 키 ['e']
   2. 키 ['b', 'c']
   3. 키 ['a', 'd']
   불린 횟수 : 3 · 글 안의 { 개수 : 3
[2] 돌려준 것이 dict 자리를 차지한다
    <2 keys>
    [1, [2, 3], 'H']
[3] 같은 키가 둘인 글
   loads                   : {'x': 2}
   object_hook 이 받는 것   : ('hook', {'x': 2})
   object_pairs_hook 이 받는 것 : ('pairs', [('x', 1), ('x', 2)])
   둘 다 주면              : ('pairs', [('x', 1), ('x', 2)])
[4] 중복을 거절하는 pairs 훅
   ValueError 「duplicate key: ['x']」
[5] 숫자 모양의 키를 int 로 바꾸는 훅
   원본 : {1: 'a', '1': 'b', 2: 'c'}
   훅 뒤 : {1: 'b', 2: 'c'}
(exit 0)
```

그림 해설.

* ★★★ **`[1]` — 순서가 `['e']` → `['b', 'c']` → `['a', 'd']`** — **안쪽 객체가 먼저, 뿌리가 마지막**이다. 이 점은 JS `reviver` 와 **같다**(후위 순서).
  ★★ **다른 점** — 불린 횟수가 **3**, 글 안의 `{` 개수와 같다. **객체에만** 불리고 숫자·배열·문자열에는 안 불린다. JS 의 `reviver` 는 **값마다**(그 예에서 7 번) 불린다 — [JS 31번](../../../js/syntax/31-json/2-summary.md) 동작 (4)의 `[1]`.
  ★ 문서는 *"called with the result of every JSON object decoded"* 라고만 적는다 — **순서는 적지 않는다.** 안쪽이 먼저인 것은 **이 판의 관찰**이다(안쪽 객체가 다 만들어져야 바깥 dict 의 값이 되므로 자연스럽긴 하다 — 그 설명은 추론이다).
* ★★ **`[2]`** — 훅이 돌려준 것이 **그 dict 자리를 통째로 차지한다**(`<2 keys>` · `[1, [2, 3], 'H']` — 빈 `{}` 에도 불렸다).
* ★★★ **`[3]` — 같은 키 둘**: `object_hook` 은 **이미 합쳐진** `{'x': 2}` 를 받는다. **`object_pairs_hook` 만** 짝 목록 `[('x', 1), ('x', 2)]` 을 본다. 둘 다 주면 **pairs 쪽만** 불렸다(문서 — *"the object_pairs_hook takes priority"*).
* ★★ **`[4]`** — 그래서 **중복 키를 거절**하려면 `object_pairs_hook` 에서 검사한다. 기본 `loads` 는 거절하지 않는다(동작 2).
* ★★ **`[5]` — 숫자 모양 키를 `int` 로 바꾸는 훅을 달아도 원본이 안 돌아온다** — `{1: 'a', '1': 'b', 2: 'c'}` 가 `{1: 'b', 2: 'c'}`. 글자 `"1"` 둘 중 **하나는 이미 `loads` 가 버렸고**, 남은 것이 원래 `1` 이었는지 `'1'` 이었는지 **훅은 모른다.**

**비용** — 훅은 **객체 하나마다** 한 번 불린다. 날짜처럼 **문자열 값**을 되살리려 해도 **그 문자열을 담은 dict** 단위로 받아서 안을 뒤져야 한다.

### 5. ★★ 숫자 — 파이썬끼리는 되돌아온다, 받는 쪽이 double 이면 아니다

**언제 쓰나** — 금액·큰 id·과학 값을 JSON 으로 주고받을 때.

```text
   파이썬 float  ──dumps──▶  repr 과 같은 최단 글자  ──loads──▶  같은 float     (7 / 7)
   파이썬 int    ──dumps──▶  자릿수 전부               ──loads──▶  같은 int       10 ** 16 + 1 도 그대로
                                                     ★ JS JSON.parse 는 double 로 읽는다 -> 끝자리가 뭉개진다 (31번 동작 (6))

   1e16 + 1   ★ 이 값은 JSON 에 가기 전에 이미 1e16 이다 — float 가 1 을 못 담는다 (json 의 잘못이 아니다)
```

```python
# e47_numbers.py
import decimal
import json
import sys

print("[1] float 를 내보내고 되읽으면")
floats = [("0.1", 0.1), ("0.1 + 0.2", 0.1 + 0.2), ("1 / 3", 1 / 3), ("1e16 + 1", 1e16 + 1),
          ("2.0 ** 53 + 1", 2.0 ** 53 + 1), ("1e-7", 1e-7), ("1e22", 1e22)]
ok = 0
for label, f in floats:
    text = json.dumps(f)
    back = json.loads(text)
    ok += back == f
    print("   %-14s ; dumps %-22s ; 되읽은 값이 같은가 %s" % (label, text, back == f))
print("   같은 값으로 돌아온 행 : %d / %d" % (ok, len(floats)))

print("[2] int 는 자릿수 그대로")
print("   dumps(10 ** 16 + 1)    :", json.dumps(10 ** 16 + 1))
print("   dumps(2 ** 53 + 1)     :", json.dumps(2 ** 53 + 1))

print("[3] loads 가 숫자 글자를 무엇으로 읽나")
for t in ["9007199254740993", "9007199254740993.0", "1.0", "1E2", "-0", "-0.0", "1e400", "-1e400"]:
    v = json.loads(t)
    print("   %-20s -> %-22r %s" % (t, v, type(v).__name__))

print("[4] parse_float · parse_int · parse_constant")
print("   parse_float=Decimal   :", repr(json.loads("[0.1, 2.50, 3]", parse_float=decimal.Decimal)))
print("   parse_int=str         :", repr(json.loads("[1, 2.5]", parse_int=str)))
seen = []


def constant(name):
    seen.append(name)
    return name


print("   parse_constant        :", repr(json.loads("[NaN, -Infinity, null, true]", parse_constant=constant)))
print("   parse_constant 이 받은 것 :", seen)

print("[5] 정수 글자 길이 한도")
print("   sys.get_int_max_str_digits() :", sys.get_int_max_str_digits())
for n in (4300, 4301):
    try:
        v = json.loads("7" * n)
        print("   %d 자리 -> int, 자릿수 %d" % (n, len(str(v))))
    except ValueError as ex:
        print("   %d 자리 -> ValueError 「%s」" % (n, ex))
print("   parse_int=Decimal 로 4301 자리 :", type(json.loads("7" * 4301, parse_int=decimal.Decimal)).__name__)
```

```text
===== python3 - <e47_numbers.py =====
[1] float 를 내보내고 되읽으면
   0.1            ; dumps 0.1                    ; 되읽은 값이 같은가 True
   0.1 + 0.2      ; dumps 0.30000000000000004    ; 되읽은 값이 같은가 True
   1 / 3          ; dumps 0.3333333333333333     ; 되읽은 값이 같은가 True
   1e16 + 1       ; dumps 1e+16                  ; 되읽은 값이 같은가 True
   2.0 ** 53 + 1  ; dumps 9007199254740992.0     ; 되읽은 값이 같은가 True
   1e-7           ; dumps 1e-07                  ; 되읽은 값이 같은가 True
   1e22           ; dumps 1e+22                  ; 되읽은 값이 같은가 True
   같은 값으로 돌아온 행 : 7 / 7
[2] int 는 자릿수 그대로
   dumps(10 ** 16 + 1)    : 10000000000000001
   dumps(2 ** 53 + 1)     : 9007199254740993
[3] loads 가 숫자 글자를 무엇으로 읽나
   9007199254740993     -> 9007199254740993       int
   9007199254740993.0   -> 9007199254740992.0     float
   1.0                  -> 1.0                    float
   1E2                  -> 100.0                  float
   -0                   -> 0                      int
   -0.0                 -> -0.0                   float
   1e400                -> inf                    float
   -1e400               -> -inf                   float
[4] parse_float · parse_int · parse_constant
   parse_float=Decimal   : [Decimal('0.1'), Decimal('2.50'), 3]
   parse_int=str         : ['1', 2.5]
   parse_constant        : ['NaN', '-Infinity', None, True]
   parse_constant 이 받은 것 : ['NaN', '-Infinity']
[5] 정수 글자 길이 한도
   sys.get_int_max_str_digits() : 4300
   4300 자리 -> int, 자릿수 4300
   4301 자리 -> ValueError 「Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit」
   parse_int=Decimal 로 4301 자리 : Decimal
(exit 0)
```

그림 해설.

* ★★ **`[1]` — 같은 값으로 돌아온 행 `7 / 7`.** `0.1 + 0.2` 는 `0.30000000000000004` 로 **보이는 그대로** 나가고 그대로 돌아온다.
  ★ **`1e16 + 1` 이 `1e+16`** 인 것은 **`json` 이 잃은 것이 아니다** — 그 덧셈 결과가 이미 `1e16` 이다([04번](../04-numeric-types-and-division/2-summary.md)·목록의 **50번 주제**).
* ★★ **`[2]`·`[3]` — `int` 는 자릿수 그대로** 나가고 **`9007199254740993`(`2 ** 53 + 1`)도 `int` 로 정확히** 돌아온다. 같은 글자 뒤에 **`.0` 을 붙이면 `float` 로 읽혀 `...992.0`** — 받는 타입은 **글자에 점이 있나**가 정한다.
  ★ JS 는 숫자를 전부 double 로 읽는다 — [JS 31번](../../../js/syntax/31-json/2-summary.md) 동작 (6)에서 20자리 id 가 `12345678901234567000` 으로 뭉개졌다. **파이썬이 정확히 낸 큰 정수를 JS 가 조용히 바꾼다.**
* ★★ **`[3]` — `1e400` 은 에러 없이 `inf`**, **`-0`(정수 글자)은 `0`**(부호가 사라진다), **`-0.0` 은 `-0.0`**. 읽는 쪽도 **조용히 값을 바꾼다.**
* ★★ **`[4]` — `parse_float=Decimal`** 은 `2.50` 을 **`Decimal('2.50')`** 로 — 끝의 0 까지 살린다(금액). `parse_int=str` 은 정수 글자를 **글자째** 받는다.
  **`parse_constant` 는 `NaN`·`-Infinity` 에만 불렸다** — `null`·`true` 에는 안 불린다(문서 3.1 표기 — *"parse_constant doesn't get called on 'null', 'true', 'false' anymore"*).
* ★ **`[5]` — 4301 자리 정수 글자는 `ValueError`** — 3.11 에서 들어온 **정수 글자 길이 한도**(`4300`)다. `parse_int=Decimal` 로 주면 통과했다.

**비용** — 정밀도가 중요한 값(금액)은 **숫자가 아니라 글자로** 보내거나 `parse_float=Decimal` 로 받는다. 어느 쪽이든 **양쪽이 약속해야** 한다.

### 6. ★★ `ensure_ascii` — 기본값은 한글을 이스케이프로, 그런데 06편의 `backslashreplace` 와는 다르다

**언제 쓰나** — 한글이 든 JSON 을 파일·로그에 쓸 때.

```text
   글자          ensure_ascii=True(기본)     ensure_ascii=False    06편 backslashreplace
   é  U+00E9     "\u00e9"                    "é"                   \xe9         ★ 다르다
   가 U+AC00     "\uac00"                    "가"                  \uac00       같다
   😀 U+1F600    "\ud83d\ude00"  (대리 쌍)   "😀"                  \U0001f600   ★ 다르다
```

```python
# e47_ascii.py
import json

samples = [("chr(0xE9)", chr(0xE9)), ("chr(0xAC00)", chr(0xAC00)), ("chr(0x1F600)", chr(0x1F600))]

print("[1] ensure_ascii 기본값 · False · 06편의 backslashreplace")
split = 0
for label, s in samples:
    a = json.dumps(s)
    b = json.dumps(s, ensure_ascii=False)
    c = s.encode("ascii", "backslashreplace").decode("ascii")
    same = a[1:-1] == c
    split += not same
    print("   %-13s ; 기본 %-16s ; False %s ; backslashreplace %-12s ; 기본과 같은가 %s"
          % (label, a, b, c, same))
print("   기본값과 backslashreplace 가 다른 글자 : %d / %d" % (split, len(samples)))

print("[2] 길이 — dumps 결과의 글자 수 · UTF-8 바이트 수")
word = chr(0xD55C) + chr(0xAE00)
for flag in (True, False):
    t = json.dumps(word, ensure_ascii=flag)
    print("   ensure_ascii=%-5s ; 글자 %2d ; UTF-8 바이트 %2d" % (flag, len(t), len(t.encode("utf-8"))))

print("[3] 되읽으면")
for label, s in samples:
    print("   %-13s ; 기본으로 쓴 것 %s ; False 로 쓴 것 %s"
          % (label, json.loads(json.dumps(s)) == s, json.loads(json.dumps(s, ensure_ascii=False)) == s))

print("[4] ASCII 안의 제어 문자와 기호")
print("   ", json.dumps(chr(0) + chr(0x1F) + chr(0x7F) + "/" + chr(9) + "<&>"))
```

```text
===== python3 - <e47_ascii.py =====
[1] ensure_ascii 기본값 · False · 06편의 backslashreplace
   chr(0xE9)     ; 기본 "\u00e9"         ; False "é" ; backslashreplace \xe9         ; 기본과 같은가 False
   chr(0xAC00)   ; 기본 "\uac00"         ; False "가" ; backslashreplace \uac00       ; 기본과 같은가 True
   chr(0x1F600)  ; 기본 "\ud83d\ude00"   ; False "😀" ; backslashreplace \U0001f600   ; 기본과 같은가 False
   기본값과 backslashreplace 가 다른 글자 : 2 / 3
[2] 길이 — dumps 결과의 글자 수 · UTF-8 바이트 수
   ensure_ascii=True  ; 글자 14 ; UTF-8 바이트 14
   ensure_ascii=False ; 글자  4 ; UTF-8 바이트  8
[3] 되읽으면
   chr(0xE9)     ; 기본으로 쓴 것 True ; False 로 쓴 것 True
   chr(0xAC00)   ; 기본으로 쓴 것 True ; False 로 쓴 것 True
   chr(0x1F600)  ; 기본으로 쓴 것 True ; False 로 쓴 것 True
[4] ASCII 안의 제어 문자와 기호
    "\u0000\u001f\u007f/\t<&>"
(exit 0)
```

그림 해설.

* ★★★ **`[1]` — 기본값과 `backslashreplace` 가 다른 글자 `2 / 3`.** 같은 것은 **「가」 하나**뿐이다.
  `é` 는 JSON 쪽이 **`\u00e9`**(JSON 에는 `\x` 표기가 없다), 이모지는 JSON 쪽이 **UTF-16 대리 쌍 두 개**(`\ud83d\ude00` — JSON 의 `\u` 는 네 자리뿐이다).
  ★ 06편이 「`ensure_ascii` 가 `backslashreplace` 와 같은 일을 한다」고 넘긴 것은 **「ASCII 밖을 ASCII 로 적는다」는 목적**까지만 맞다 — **글자는 셋 중 둘이 다르다.**
* ★★ **`[2]` — 「한글」 두 글자가 기본값으로는 14 글자(14 바이트), `False` 로는 4 글자(8 바이트).** ★ 이것은 **길이**이지 속도가 아니다.
* ★ **`[3]`** — 어느 쪽으로 써도 **되읽으면 같은 글자**다. `ensure_ascii` 는 **보이는 모양**을 바꿀 뿐 값을 바꾸지 않는다.
* ★ **`[4]`** — ASCII 안의 제어 문자는 **`ensure_ascii` 와 상관없이** 이스케이프된다(`\u0000`·`\u001f` · 탭은 `\t`). **`\u007f`(DEL) 도 이스케이프됐다** — 관찰이다. `/`·`<`·`&` 는 그대로다.

**비용** — `ensure_ascii=False` 로 쓴 글자를 파일에 쓰면 **그 파일의 인코딩**이 문제가 된다(`open(..., encoding=...)` — [48번](../48-pathlib-and-file-io/2-summary.md)).

### 7. ★★★ 순환 참조 — 파이썬은 경로를 말하지 않는다

**언제 쓰나** — 부모·자식이 서로 가리키는 구조를 내보낼 때.

```text
   a = {'b': {'c': {'back': a}}}

   JS  JSON.stringify(a)  (31번 동작 (2))             파이썬 json.dumps(a)
   TypeError 「Converting circular structure to JSON」 ValueError 「Circular reference detected」
       ▸ starting at object with constructor ...         (args 도 그 한 줄뿐 — 어디서 닫혔는지 없음)
       |     property 'b' -> ...
       |     property 'c' -> ...
       --- property 'back' closes the circle
```

```python
# e47_cycle.py
import json


def show(label, f):
    try:
        print("   %-26s -> %s" % (label, f()))
    except (ValueError, RecursionError) as ex:
        print("   %-26s -> %s 「%s」 · args %r" % (label, type(ex).__name__, ex, ex.args))


print("[1] 순환 셋 — JS 31편 동작 (2)와 같은 모양")
me = {}
me["me"] = me
a = {"b": {"c": {}}}
a["b"]["c"]["back"] = a
arr = [1, [2]]
arr[1].append(arr)
show("me['me'] = me", lambda: json.dumps(me))
show("a.b.c.back = a", lambda: json.dumps(a))
show("arr[1][1] = arr", lambda: json.dumps(arr))

print("[2] 같은 객체를 두 번 넣었지만 순환은 아닌 것")
x = [1]
show("[x, x, {'k': x}]", lambda: json.dumps([x, x, {"k": x}]))

print("[3] check_circular=False")
show("me, check_circular=False", lambda: json.dumps(me, check_circular=False))
show("[x, x], check_circular=False", lambda: json.dumps([x, x], check_circular=False))

print("[4] default 가 받은 객체를 그대로 돌려주면")


class Box:
    pass


show("default=lambda o: o", lambda: json.dumps(Box(), default=lambda o: o))
show("default=lambda o: [o]", lambda: json.dumps(Box(), default=lambda o: [o]))
```

```text
===== python3 - <e47_cycle.py =====
[1] 순환 셋 — JS 31편 동작 (2)와 같은 모양
   me['me'] = me              -> ValueError 「Circular reference detected」 · args ('Circular reference detected',)
   a.b.c.back = a             -> ValueError 「Circular reference detected」 · args ('Circular reference detected',)
   arr[1][1] = arr            -> ValueError 「Circular reference detected」 · args ('Circular reference detected',)
[2] 같은 객체를 두 번 넣었지만 순환은 아닌 것
   [x, x, {'k': x}]           -> [[1], [1], {"k": [1]}]
[3] check_circular=False
   me, check_circular=False   -> RecursionError 「maximum recursion depth exceeded while encoding a JSON object」 · args ('maximum recursion depth exceeded while encoding a JSON object',)
   [x, x], check_circular=False -> [[1], [1]]
[4] default 가 받은 객체를 그대로 돌려주면
   default=lambda o: o        -> ValueError 「Circular reference detected」 · args ('Circular reference detected',)
   default=lambda o: [o]      -> ValueError 「Circular reference detected」 · args ('Circular reference detected',)
(exit 0)
```

그림 해설.

* ★★★ **`[1]` — 세 순환이 전부 한 글자도 같은 `Circular reference detected`**, `args` 도 그 한 줄이다. JS 31번 동작 (2)의 V8 은 **`property 'b' -> … 'back' closes the circle`** 로 **경로를 말했다.** 파이썬 쪽에서 어디가 닫혔는지는 **직접 찾아야** 한다.
* ★★ **`[2]` — 같은 리스트를 세 번 넣은 것은 순환이 아니다** — 그대로 세 번 나간다. 검사는 「**지금 내려가는 길 위에** 같은 객체가 있나」이지 「본 적이 있나」가 아니다.
  ★ 되읽으면 **세 개의 따로 된 리스트**다 — 「같은 객체」라는 사실은 JSON 에 안 남는다.
* ★★ **`[3]` — `check_circular=False`** 면 순환에서 **`RecursionError`** — 문서가 *"(or worse)"* 까지 적어 두었다. 순환이 없으면 결과는 같다.
* ★★ **`[4]` — `default` 가 받은 객체를 그대로(또는 리스트에 싸서) 돌려주면 `Circular reference detected`** 다. 순환 구조를 만든 적이 없는데 순환 에러가 난다 — 인코더가 `default` 의 결과를 **같은 객체 아래로 다시 내려가** 인코딩하기 때문이다(메시지로 보인 것은 에러 종류뿐이고, 이 설명은 추론이다).

**비용** — 순환을 끊으려면 **내보내기 전에 구조를 바꾼다**(부모 참조를 id 로). JS 의 `WeakSet` replacer(31번 동작 (2) `[4]`) 같은 자리는 파이썬에서는 **`default` 가 아니라 미리 변환**이다 — `default` 는 **못 싣는 값에만** 불리기 때문이다(동작 8).

### 8. ★★ `default=` — 못 싣는 값에만, 키에는 안 불린다

**언제 쓰나** — `datetime`·`Decimal`·`set` 을 내보낼 때.

```text
   json.dumps(doc, default=fallback)

   값을 만날 때마다       싣는 법을 아나?  ── 안다(dict·list·str·int·float·bool·None) ──▶ 그대로
                            │ 모른다
                            ▼
                      fallback(값) ──▶ 돌려준 것을 다시 인코딩     ★ 키 자리는 이 길을 안 탄다 -> TypeError
```

```python
# e47_default.py
import datetime
import decimal
import json

calls = []


def fallback(o):
    calls.append(type(o).__name__)
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if isinstance(o, decimal.Decimal):
        return str(o)
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    raise TypeError("no rule for %s" % type(o).__name__)


doc = {
    "when": datetime.datetime(2026, 9, 26, 12, 30),
    "price": decimal.Decimal("0.10"),
    "tags": {"b", "a"},
    "n": 1,
    "items": [1, 2.5, "s", None],
}

print("[1] default= 가 불린 대상")
print("   ", json.dumps(doc, default=fallback))
print("    불린 순서 :", calls)

print("[2] 되읽으면 — 무엇이 원래 타입으로 돌아오나")
back = json.loads(json.dumps(doc, default=fallback))
for k in ("when", "price", "tags"):
    print("   %-6s %-16s -> %-10s %r" % (k, type(doc[k]).__name__, type(back[k]).__name__, back[k]))

print("[3] default 가 TypeError 를 던지면")
try:
    json.dumps({"z": 1 + 2j}, default=fallback)
except TypeError as ex:
    print("    TypeError 「%s」" % ex)

print("[4] 키 자리의 Decimal 과 default=")
calls.clear()
try:
    json.dumps({decimal.Decimal("1"): "x"}, default=fallback)
except TypeError as ex:
    print("    TypeError 「%s」 · default 호출 %d 번" % (ex, len(calls)))

print("[5] JSONEncoder 하위 클래스로")


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)


print("   ", json.dumps({"price": decimal.Decimal("0.10")}, cls=Encoder))
try:
    json.dumps({"when": datetime.date(2026, 9, 26)}, cls=Encoder)
except TypeError as ex:
    print("    TypeError 「%s」" % ex)
```

```text
===== python3 - <e47_default.py =====
[1] default= 가 불린 대상
    {"when": "2026-09-26T12:30:00", "price": "0.10", "tags": ["a", "b"], "n": 1, "items": [1, 2.5, "s", null]}
    불린 순서 : ['datetime', 'Decimal', 'set']
[2] 되읽으면 — 무엇이 원래 타입으로 돌아오나
   when   datetime         -> str        '2026-09-26T12:30:00'
   price  Decimal          -> str        '0.10'
   tags   set              -> list       ['a', 'b']
[3] default 가 TypeError 를 던지면
    TypeError 「no rule for complex」
[4] 키 자리의 Decimal 과 default=
    TypeError 「keys must be str, int, float, bool or None, not decimal.Decimal」 · default 호출 0 번
[5] JSONEncoder 하위 클래스로
    {"price": 0.1}
    TypeError 「Object of type date is not JSON serializable」
(exit 0)
```

그림 해설.

* ★★ **`[1]` — `default` 는 세 번, `datetime`·`Decimal`·`set` 에만** 불렸다. 정수·실수·문자열·`None` 이 든 리스트에는 안 불렸다. JS 31번 동작 (7)이 `set` 하나로 본 것(`['set']`)을 **세 타입**으로 넓혀도 같다.
  ★ 문서 — *"A function that is called for objects that can't otherwise be serialized."*
* ★★★ **`[2]` — 되읽으면 셋 다 원래 타입이 아니다** — `datetime` → `str`, `Decimal` → `str`, `set` → `list`. **`default` 는 나가는 길만** 고친다. 되살리는 것은 **읽는 쪽이 약속을 알고** `object_hook` 으로 해야 한다.
* ★ **`[3]`** — `default` 가 모르는 것은 **`TypeError` 를 던져** 거절한다(문서가 그렇게 하라고 적는다).
* ★★ **`[4]` — 키 자리의 `Decimal` 은 `default` 호출 0 번에 `TypeError`.** 키는 동작 2 의 목록(`str`·`int`·`float`·`bool`·`None`)만 받는다.
* ★ **`[5]` — `JSONEncoder` 하위 클래스**의 `default` 도 같은 자리다. `float(Decimal('0.10'))` 로 싣으면 **`0.1`** — 끝의 0 이 사라진다(`str` 로 싣은 `[1]` 은 `"0.10"`).

**비용** — `default` 한 곳에 타입 분기가 몰린다. **나가는 규칙과 되살리는 규칙이 두 곳**에 따로 산다.

### 9. ★ 구현 — C 인코더와 파이썬 인코더, 그리고 판마다 다른 문구

**언제 쓰나** — 예외 **문구**를 근거로 코드를 짜려 할 때(짜지 마라).

```text
   json.dumps(obj)            indent=None  ─▶ C 인코더 (c_make_encoder)   ← encoder.py 247~248행의 조건
   json.dumps(obj, indent=1)  indent 있음  ─▶ 파이썬 인코더 (_make_iterencode)

   같은 순환 + check_circular=False
        C 인코더        RecursionError 「… while encoding a JSON object」        3.11 · 3.12 같다
        파이썬 인코더    3.11 「… while calling a Python object」  /  3.12 「maximum recursion depth exceeded」
```

```python
# e47_impl.py
import json
import json.decoder
import json.encoder
import json.scanner
import sys

print("[1] C 가속 부품이 들어와 있나")
print("   json.encoder.c_make_encoder :", json.encoder.c_make_encoder is not None)
print("   json.scanner.c_make_scanner :", json.scanner.c_make_scanner is not None)
print("   json.decoder.c_scanstring   :", json.decoder.c_scanstring is not None)

print("[2] 같은 순환을 indent 없이 · indent=1 로 — check_circular=False")
me = {}
me["me"] = me
for kw in ({}, {"indent": 1}):
    try:
        json.dumps(me, check_circular=False, **kw)
    except RecursionError as ex:
        print("   %-14s RecursionError 「%s」" % (kw or "{}", ex))

print("[3] 같은 순환 — check_circular=True(기본)")
for kw in ({}, {"indent": 1}):
    try:
        json.dumps(me, **kw)
    except ValueError as ex:
        print("   %-14s ValueError 「%s」" % (kw or "{}", ex))

print("[4] 판", sys.version_info[:2])
```

```text
===== python3 - <e47_impl.py =====
[1] C 가속 부품이 들어와 있나
   json.encoder.c_make_encoder : True
   json.scanner.c_make_scanner : True
   json.decoder.c_scanstring   : True
[2] 같은 순환을 indent 없이 · indent=1 로 — check_circular=False
   {}             RecursionError 「maximum recursion depth exceeded while encoding a JSON object」
   {'indent': 1}  RecursionError 「maximum recursion depth exceeded」
[3] 같은 순환 — check_circular=True(기본)
   {}             ValueError 「Circular reference detected」
   {'indent': 1}  ValueError 「Circular reference detected」
[4] 판 (3, 12)
(exit 0)
```

같은 소스를 `python3.11` 에(파일 이름만 `e47_impl_py311.py`).

```text
===== python3.11 - <e47_impl_py311.py =====
[1] C 가속 부품이 들어와 있나
   json.encoder.c_make_encoder : True
   json.scanner.c_make_scanner : True
   json.decoder.c_scanstring   : True
[2] 같은 순환을 indent 없이 · indent=1 로 — check_circular=False
   {}             RecursionError 「maximum recursion depth exceeded while encoding a JSON object」
   {'indent': 1}  RecursionError 「maximum recursion depth exceeded while calling a Python object」
[3] 같은 순환 — check_circular=True(기본)
   {}             ValueError 「Circular reference detected」
   {'indent': 1}  ValueError 「Circular reference detected」
[4] 판 (3, 11)
(exit 0)
```

그림 해설.

* ★ **`[1]` — C 가속 부품 셋이 다 들어와 있다.** 문서는 이것을 약속하지 않는다 — **CPython 구현**이다.
* ★★ **`[2]` — `indent` 하나로 `RecursionError` 문구가 갈렸다.** 설치본 `json/encoder.py` 의 247\~248행이 **`_one_shot and c_make_encoder is not None and self.indent is None`** 일 때만 C 인코더를 쓴다 — `indent=1` 이면 파이썬으로 짠 인코더가 돈다.
  ★★ 그리고 **파이썬 인코더 쪽 문구는 3.11 과 3.12 가 다르다**(`while calling a Python object` 대 문구 없음). **예외 문구는 판과 경로를 탄다** — 이 주제에서 판이 갈린 유일한 칸이다.
* ★ **`[3]`** — `check_circular=True`(기본)의 `Circular reference detected` 는 **두 경로·두 판에서 같았다** — 관찰이다.

**비용** — 없다(알고만 있으면 된다). ★ 「C 인코더가 빠르다」는 **재지 않았다.**

## 문법 — 형태와 규칙

**형태**

```text
import json

json.dumps(obj, *, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True,
           cls=None, indent=None, separators=None, default=None, sort_keys=False)
json.loads(s, *, cls=None, object_hook=None, parse_float=None, parse_int=None,
           parse_constant=None, object_pairs_hook=None)
json.dump(obj, fp, ...) / json.load(fp, ...)            # 파일 객체 판 — 인자는 같다

json.dumps(x, allow_nan=False)                          # ★ 규격 밖 NaN·Infinity 를 막는다
json.dumps(x, ensure_ascii=False)                       # 한글을 그대로
json.dumps(x, default=str)                              # 못 싣는 값을 글자로 (되읽으면 str)
json.loads(s, parse_float=decimal.Decimal)              # 금액
json.loads(s, object_pairs_hook=검사함수)                 # 중복 키 거절
```

규칙 열.

1. ★★★ **JSON 의 값은 여섯 종류, 키는 글자뿐이다** — 왕복이 깨진 행 `14 / 26`, 키가 바뀐 행 `10 / 11`.
2. ★★★ **튜플·`namedtuple`·`IntEnum`·int 하위 클래스는 에러 없이 바탕 타입으로 바뀐다** — 「돌았다」는 아무것도 말하지 않는다.
3. ★★★ **`NaN`·`Infinity` 를 기본으로 내보낸다** — JSON 규격 밖이다. **`allow_nan=False`** 로 막는다.
4. ★★ **같은 글자가 되는 키 둘은 `dumps` 가 둘 다 내고 `loads` 가 마지막 것만 남긴다** — 삽입 순서가 승자를 정한다.
5. ★★ **`sort_keys` 는 바꾸기 전 키로 정렬한다** — 정수와 문자열 키가 섞이면 `TypeError`.
6. ★★ **`object_hook` 은 객체에만, 안쪽부터** — 같은 키를 보려면 `object_pairs_hook`.
7. ★★ **`default` 는 못 싣는 값에만, 키에는 안 불린다** — 되살리기는 읽는 쪽 몫이다.
8. ★ **순환은 `ValueError` 한 줄** — 경로는 안 말한다.

## 어디서 틀리나

### (1) ★★★ 정수 키 dict 를 JSON 으로 저장했다가 `d[42]` 로 읽는다

**`KeyError`** — 키는 `'42'` 로 돌아온다(동작 2). 에러는 **읽을 때** 난다 — 저장할 때는 아무 일도 없었다.

### (2) ★★★ 파이썬이 만든 JSON 을 다른 언어가 읽을 거라 믿는다

**`NaN`·`Infinity` 가 섞이면 JS 가 `SyntaxError`**(동작 1 — JS 31번 인용). 기본값이 규격 밖이다. **`allow_nan=False`** 로 쓰기 시점에 막는다.

### (3) ★★★ `loads(dumps(x)) == x` 를 테스트로 쓴다

튜플이 리스트로 돌아와 **`(1, 2) == [1, 2]` 는 `False`** — 반대로 `IntEnum` 은 `Level.LOW == 1` 이라 **통과하는데 타입이 바뀌었다.** **`==` 가 아니라 타입까지** 견준다(동작 1 의 판정).

### (4) ★★ 겹치는 키를 가진 dict 를 내보낸다

`{1: 'a', '1': 'b'}` 가 **같은 이름 둘**인 JSON 이 되고, 되읽으면 **하나가 조용히 사라진다**(동작 2 — `5 / 5`).

### (5) ★★ `sort_keys=True` 를 나중에 켠다

**섞인 키에서 `TypeError`** — 켜기 전에는 잘 돌던 코드가 터진다(동작 3).

### (6) ★★ `object_hook` 으로 중복 키를 잡으려 한다

**이미 합쳐진 dict** 를 받는다 — `object_pairs_hook` 이라야 짝이 보인다(동작 4 `[3]`).

### (7) ★★ `default=str` 로 `datetime` 을 내보내고 끝낸다

되읽으면 **`str`** 이다(동작 8 `[2]`). 되살리는 규칙이 읽는 쪽에 없으면 날짜가 영원히 글자다.

### (8) ★ `ensure_ascii` 를 「`backslashreplace` 와 같은 것」으로 안다

**셋 중 둘이 다른 글자**다(`é`·이모지 — 동작 6).

### (9) ★ 순환 에러 메시지로 어디가 순환인지 찾으려 한다

**경로가 없다**(동작 7). JS 의 V8 과 다르다.

### (10) ★ 예외 문구로 분기한다

**`RecursionError` 문구가 `indent` 와 판에 따라 셋**이었다(동작 9). 예외 **타입**으로 분기한다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `json` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | C 가속 부품 · 인코더 선택 조건 · 예외 문구 | 실행 + 설치본 `encoder.py` |
| **이 판(3.12.3 · 3.11.15)의 관찰** | 이 판에서 그랬을 뿐 | 출력 |
| ★ **인용한 칸** | JS 가 그 글자를 어떻게 읽나 | JS 31번의 출력 |
| ★ **부적용** | 시간·메모리 바이트 | 재지 않았다 |

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| 객체 키는 **늘 `str`** 로 바뀌고 되읽은 dict 가 **원본과 다를 수 있다** | `dumps` 의 주석 |
| 튜플은 **array** 로 · array 는 **`list`** 로 | 두 변환표 |
| int·float 파생 `Enum` 은 **number** 로(3.4+) | `JSONEncoder` 변환표 |
| `NaN`·`Infinity` 를 **기본으로 쓰고 읽는다** — 규격 밖 | `allow_nan` · 「Infinite and NaN Number Values」 |
| 같은 이름은 **마지막 것만** | 「Repeated Names Within an Object」 |
| `object_pairs_hook` 이 **`object_hook` 보다 우선** | `JSONDecoder` 절 |
| `check_circular=False` 의 순환은 **`RecursionError`(or worse)** | `check_circular` 절 |
| `default` 는 **못 싣는 객체에** 불린다 | `default` 절 |
| 기본 `parse_int` 에 **정수 글자 길이 한도**(3.11+) | `load` 의 `versionchanged` |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **C 가속 부품**(`c_make_encoder`·`c_make_scanner`·`c_scanstring`)이 있다 | 실행(동작 9 `[1]`) |
| `indent` 가 있으면 **파이썬 인코더**가 돈다 | 설치본 `json/encoder.py` 247\~248행 + 문구가 갈린 실행 |
| 예외 **문구 전부** — `Circular reference detected` · `keys must be str, int, float, bool or None, not tuple` · `Object of type set is not JSON serializable` · `RecursionError` 문구 | 실행 |
| `sort_keys` 가 **바꾸기 전 키로** 정렬한다 | 실행(동작 3) — 문서는 *"sorted by key"* 까지만 적는다 |

### 이 판(3.12.3)의 관찰

| 사실 | 왜 관찰인가 |
|---|---|
| `object_hook` 이 **안쪽 객체부터** 불린다 | 문서가 순서를 적지 않는다 |
| DEL(`0x7F`)도 이스케이프된다 | 문서는 *"non-ASCII characters"* 만 적는다 |
| 타입 격자가 3.11 과 **한 글자도 같다** | 두 판에서 본 것뿐이다 |
| 파이썬 인코더의 `RecursionError` 문구가 **3.11 과 다르다** | 문구는 약속이 아니다 |

### 그래서 이렇게 적으면 틀린다

* ✗ 「`json` 으로 저장하고 불러오면 원래 객체가 돌아온다」\
  ○ **`14 / 26`** 이 같은 값·같은 타입으로 안 돌아왔다 — 그중 6 은 **에러가 없었다.**
* ✗ 「파이썬 `json` 은 표준 JSON 만 쓴다」\
  ○ **`NaN`·`Infinity` 를 기본으로 쓴다** — 문서가 *"not JSON specification compliant"* 라고 적는다.
* ✗ 「`object_hook` 은 JS `reviver` 와 같다」\
  ○ **후위 순서는 같지만 객체에만 불린다**(3 번 대 7 번).
* ✗ 「C 가속 덕에 `json` 이 빠르다(재 봤다)」\
  ○ **시간은 재지 않았다.** 잰 것은 **어느 경로가 도나**(문구가 갈린 것)뿐이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 다른 언어와 주고받는다 | `allow_nan=False` | 규격 밖 글자를 쓰는 시점에 막는다 |
| 사람이 읽을 파일 · 한글 | `ensure_ascii=False, indent=2` | 인코딩은 파일 쪽이 정한다([48번](../48-pathlib-and-file-io/2-summary.md)) |
| 정수 키 | 키를 `str` 로 두고 쓰는 쪽에서 `int()` | 되읽으면 어차피 `str` |
| 금액 | 글자로 보내거나 `parse_float=Decimal` | 끝의 0·정밀도 |
| 중복 키 거절 | `object_pairs_hook` | `object_hook` 은 합쳐진 뒤다 |
| 같은 데이터 → 같은 글자 | `sort_keys=True` + **키를 전부 `str`** | 섞이면 `TypeError`, 두 번째 저장에서 순서가 바뀐다 |
| 파이썬 객체를 그대로 보관(튜플·`set`·클래스) | JSON 이 아니다 — `pickle` 등 | JSON 에는 그 칸이 없다(`pickle` 은 이 문서가 재지 않았다) |

## 핵심 문장

1. **JSON 은 상자 여섯 종류와 글자 이름표뿐이다** — 26 값 중 **14** 가 같은 값·같은 타입으로 안 돌아왔고 그중 **6 은 에러가 없었다.**
2. **키는 늘 `str` 로 돌아온다** — `True` 는 `"true"`, `None` 은 `"null"`. 같은 글자가 되는 키 둘은 **되읽으면 하나가 사라진다**(`5 / 5`).
3. **파이썬은 `NaN`·`Infinity` 를 기본으로 내보낸다** — JSON 규격 밖이라 JS 가 못 읽는다. `allow_nan=False`.
4. **`object_hook` 은 안쪽 객체부터 · 객체에만** — 같은 키를 보려면 `object_pairs_hook`.
5. **순환 메시지는 경로를 말하지 않는다** — 그리고 예외 문구는 판과 인코더 경로를 탄다. 시간은 한 번도 재지 않았다.

## 관련 자료

* 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — ★★★ **경계**: 키가 되는 조건(해시·`==`)과 「`1`·`1.0`·`True` 는 한 칸」은 그쪽이 정본. 여기는 **그 키가 JSON 으로 나갔다 들어올 때**부터다(동작 2 의 `[3]` 이 그 결론을 인용했다).
* 선행: [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md) — `set` 이 JSON 으로 못 나가는 것을 이 주제가 받았다(동작 1 — `TypeError`, 동작 8 — `default` 로 `sorted`).
* 선행: [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md) — 동작 5 의 오류 처리기 표. **경계**: 인코딩·오류 처리기는 그쪽, 여기는 **`ensure_ascii` 가 그것과 셋 중 둘에서 다르다**는 것만(동작 6).
* 이웃: [31-comparison-protocol-and-sortability](../31-comparison-protocol-and-sortability/2-summary.md) — `sort_keys` 가 섞인 키에서 터지는 이유(`<` 가 없다).
* 이웃: [04-numeric-types-and-division](../04-numeric-types-and-division/2-summary.md) — `1e16 + 1` 이 이미 `1e16` 인 이유는 float 쪽이다. 금액은 목록의 **50번 주제**.
* 이어지는 곳: [48번](../48-pathlib-and-file-io/2-summary.md) 「`pathlib` 와 파일 I/O」 — `json.dump(obj, fp)` 의 `fp` 를 **어떤 인코딩으로 열었나**.
* 대비: [JS 31번 — `JSON`](../../../js/syntax/31-json/2-summary.md) — ★★★ **경계**: JS 의 자리별 매핑 격자(`3 / 14`)·`toJSON`/replacer 순서·`reviver` 순서·순환 메시지의 경로·깊은 복사 손실, 그리고 **파이썬에 같은 질문을 던진 동작 (7)**(`NaN`·중복 키·tuple 키·`set`·순환·`default`·`loads('NaN')`)은 그쪽이다.
  여기는 그 위에서 **왕복 격자 · 키 왕복 손실 · `sort_keys` · `object_hook` 순서 · `default` 의 키 자리 · `ensure_ascii` · 인코더 경로와 판**을 더 갔다.
* 공식 문서: [`json`(3.12)](https://docs.python.org/3.12/library/json.html) · [RFC 7159](https://www.rfc-editor.org/rfc/rfc7159)(문서가 가리키는 판)

## 용어 풀이

* **직렬화(serialization) / 역직렬화**: 객체 ↔ 글자·바이트. `dumps`/`loads` 가 글자, `dump`/`load` 가 파일 객체 판.
* **왕복(round trip)**: 바꿨다 되돌렸을 때 원래와 같은 것이 오는가. 이 문서는 **타입과 `repr`** 로 판정했다.
* **변환표**: 파이썬 타입 ↔ JSON 값 종류의 대응. 나가는 표와 들어오는 표가 **따로** 있고, 들어오는 표에는 `tuple` 이 없다.
* **`allow_nan`**: `NaN`·`Infinity` 를 쓸지. 기본 `True` — 규격 밖 글자를 쓴다. `False` 면 `ValueError`.
* **`ensure_ascii`**: ASCII 밖 글자를 `\uXXXX` 로 적을지. 기본 `True`.
* **대리 쌍(surrogate pair)**: U+FFFF 너머 글자를 UTF-16 코드 단위 두 개로 적는 법. JSON 의 `\u` 가 네 자리뿐이라 이모지가 이렇게 나간다.
* **`default`**: 못 싣는 **값**을 만났을 때 불리는 함수. 키에는 안 불린다.
* **`object_hook` / `object_pairs_hook`**: 읽을 때 **객체 하나가 다 만들어질 때마다** 불리는 함수. 앞은 합쳐진 dict, 뒤는 짝 목록을 받는다.
* **`parse_float`·`parse_int`·`parse_constant`**: 숫자 글자·`NaN`/`Infinity` 글자를 무엇으로 읽을지 정하는 함수.
* **`check_circular`**: 내려가는 길에 같은 컨테이너가 다시 나오는지 검사할지. 끄면 순환에서 `RecursionError`.
* **C 가속(C accelerator)**: CPython 이 `json` 의 핵심을 C 로 따로 구현해 둔 것(`_json`). 문서의 약속이 아니다.

## 더 들어가면

* ★ **`json.tool`**(명령줄 정렬·검사)과 **`raw_decode`**(글 앞부분의 JSON 하나만 읽고 끝 위치를 준다) — 이 문서는 재지 않았다.
* ★ **`loads` 는 `bytes` 도 받는다**(3.6+ — UTF-8·16·32 를 알아본다, 문서) — 재지 않았다. 파일에서 읽는 이야기는 [48번](../48-pathlib-and-file-io/2-summary.md).
* ★ **`strict=False`** 는 문자열 안의 제어 문자(탭·줄바꿈)를 허락한다(문서) — 재지 않았다.
* ★ **왕복을 지키는 약속**(`{"__type__": "tuple", …}` + `object_hook`)은 흔한 관용구지만 **표준이 아니다** — 받는 쪽이 같은 약속을 알아야 한다.
