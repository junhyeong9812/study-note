# python/syntax/47-json — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다. ★ **시간·메모리 바이트는 한 번도 재지 않았다.** JS 쪽 사실은 [JS 31번](../../../js/syntax/31-json/2-summary.md)의 출력을 인용했다(다시 돌리지 않았다).

## 정답

### 1. 같다 12 · 바뀐다 6 · 거절 8 — 왕복이 깨진 행 `14 / 26` · `NaN`·`inf`·`-inf` 는 왕복되지만 `allow_nan=False` 에서 `ValueError`(`3 / 26`)

**출력**

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

(3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e47_grid_py311.py` 다. 출력도 배너 줄을 빼고 같다.)

**왜 그런가**

* ★★★ JSON 의 값은 **여섯 종류**다. 튜플·`namedtuple` 은 배열로 나가고 **배열은 `list` 로만** 돌아온다 — 튜플이었다는 사실을 적을 칸이 없다.
* ★★★ **`IntEnum`·`(str, Enum)`·int 하위 클래스는 에러 없이** 바탕 타입(`int`·`str`)으로 돌아온다. `Level.LOW == 1` 이라 **`==` 로 견주면 못 잡는다** — 타입까지 견줘야 「바뀐다」가 보인다.
* ★★ `{1: 'a'}` 는 **키가 `'1'`** 로 돌아온다(2번).
* ★★ 규격 상자가 없는 8 타입은 **`TypeError`** — JS 는 `set` 을 `{}` 로 조용히 바꾸는 자리다(JS 31번).
* ★★★ `NaN`·`Infinity`·`-Infinity` 는 **파이썬끼리는 왕복**되지만 **JSON 규격 밖 글자**다 — `allow_nan=False` 가 바로 그것을 `ValueError` 로 만든다.

### 2. 원본과 다른 dict 로 돌아온 행 `10 / 11`(`True` → `'true'` · `None` → `'null'`) · 튜플·`Decimal`·`bytes` 키는 `TypeError` · 겹치는 키는 되읽으면 줄어든다 `5 / 5` · 파이썬 안의 `1`·`1.0`·`True` 는 이미 한 칸

**출력**

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

**왜 그런가**

* ★★★ JSON 의 객체 키는 **글자뿐**이다. `dumps` 가 키를 **값 자리와 같은 규칙으로** 글자로 바꾼다 — `True` 는 `"true"`, `None` 은 `"null"`, `nan` 은 `"NaN"`. 되읽으면 **그 글자가 그대로 `str` 키**다.
* ★★★ `{1: 'a', '1': 'b'}` 는 파이썬에서는 다른 두 키지만 **나가면 같은 이름 `"1"` 둘**이다. `dumps` 는 막지 않고, `loads` 는 **마지막 것만** 남긴다 — **삽입 순서가 승자를 정한다**(`'b'` 대 뒤집은 판의 `'a'`).
* ★★ `[3]` 은 방향이 반대다 — **파이썬 dict 가 먼저** `1`·`1.0`·`True` 를 한 칸으로 합쳤다([12번](../12-dict-and-key-requirements/2-summary.md) 동작 3). 그래서 나가는 키가 하나다.
* ★ 키 자리의 튜플은 **값 자리와 달리** 거절이다. `skipkeys=True` 는 그 키를 **말없이 뺀다.**

### 3. 정수 키는 수 순서 `"2"` → `"10"` · 문자열 키는 글자 순서 `"10"` → `"2"` · 섞이면 `TypeError` · 한 번 나갔다 온 것을 다시 정렬하면 순서가 바뀐다

**출력**

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

**왜 그런가**

* ★★ **정렬은 글자로 바꾸기 전의 키 위에서** 일어난다 — 정수 `2 < 10` 이라 `"2"` 가 앞이다. 문자열 `'10' < '2'` 라 `[1]` 은 거꾸로다.
* ★★ 그래서 **정수와 문자열이 섞이면** 파이썬의 `<` 가 못 견줘 `TypeError`([31번](../31-comparison-protocol-and-sortability/2-summary.md)). `bool`·`None` 도 같다. 정수와 실수만 섞이면 된다(`1.5 < 2`).
* ★ `[5]` — 첫 저장은 정수 키라 `"2"` 가 앞, 되읽은 dict 는 **문자열 키**라 둘째 저장은 `"10"` 이 앞 — **같은 데이터가 두 번째 저장에서 다른 글자**가 된다.

### 4. `object_hook` 은 `['e']` → `['b', 'c']` → `['a', 'd']`(안쪽부터 · 3 번) · 돌려준 것이 그 자리를 차지 · 같은 키는 `object_pairs_hook` 만 본다 · 둘 다 주면 pairs 만 · 숫자 키 훅은 원본을 못 되살린다

**출력**

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

**왜 그런가**

* ★★★ 훅은 **객체 하나가 다 만들어질 때마다** 불린다 — 가장 안쪽 `{"e": 5}` 가 먼저 끝나고 뿌리가 마지막이다. **객체에만** 불려 횟수가 `{` 개수와 같은 3 이다.
* ★★ 돌려준 값이 **dict 자리를 차지**한다 — 빈 `{}` 에도 불렸다.
* ★★★ `object_hook` 이 받는 것은 **이미 마지막 값만 남은** dict 다. 짝 목록을 받는 `object_pairs_hook` 이라야 `('x', 1)` 을 본다 — 문서가 *"the object_pairs_hook takes priority"* 라고 적은 대로 둘 다 주면 pairs 만 불렸다.
* ★★ `[5]` — 글자 `"1"` 둘 중 하나는 **훅이 불리기 전에** 사라졌다. 훅은 남은 `'1'` 이 원래 `1` 이었는지 모르고 `int` 로 바꾼다.

### 5. float 왕복 `7 / 7`(`1e16 + 1` 은 가기 전에 이미 `1e16`) · int 는 자릿수 그대로 · `.0` 이 붙으면 float · `1e400` 은 `inf` · `-0` 은 `0` · `Decimal('2.50')` · `parse_constant` 는 `NaN`·`-Infinity` 만 · 4301 자리는 `ValueError`

**출력**

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

**왜 그런가**

* ★★ 파이썬 `json` 은 float 를 **`repr` 과 같은 최단 글자**로 쓴다 — 되읽으면 **같은 float** 다. `1e16 + 1` 의 1 은 **float 덧셈에서** 이미 사라졌다.
* ★★ int 는 **글자 그대로** 쓰고 읽는다 — `2 ** 53 + 1` 도 정확하다. 받는 타입은 **글자에 점·지수가 있나**가 정한다(`1E2` → `100.0`).
* ★★ 읽는 쪽도 조용히 바꾼다 — **`1e400` → `inf`**, 정수 글자 **`-0` → `0`**.
* ★ `parse_constant` 는 **`NaN`·`Infinity`·`-Infinity` 글자에만** 불린다(3.1 부터 `null`·`true`·`false` 에는 안 불린다 — 문서).
* ★ 4301 자리 — 3.11 에서 들어온 **정수 글자 길이 한도**. `parse_int=Decimal` 은 그 길을 안 탄다.

### 6. 세 순환 모두 한 글자도 같은 `ValueError 「Circular reference detected」` · 공유는 세 번 나간다 · `check_circular=False` 는 `RecursionError` · `default` 가 자기를 돌려주면 순환 에러

**출력**

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

**왜 그런가**

* ★★★ 검사는 「**내려가는 길 위에 같은 컨테이너가 또 나왔나**」다. 나오면 한 줄 문구만 던진다 — **어디서 닫혔는지는 안 적는다**(`args` 도 한 줄).
* ★★ 같은 `x` 를 세 번 넣은 것은 **길 위에 겹치지 않으므로** 순환이 아니다 — 세 번 그대로 나가고, 되읽으면 **따로 된 리스트 셋**이다.
* ★★ `check_circular=False` 는 검사를 빼므로 끝없이 내려가 **`RecursionError`**(문서 — *"(or worse)"*).
* ★ `default` 가 받은 객체를 돌려주면 인코더가 **그 객체 아래로 다시** 들어가 같은 객체를 만난다 — 순환 구조가 없어도 순환 에러다(이유는 추론, 보인 것은 에러 종류).

### 7. JS 의 `JSON.parse` 가 `SyntaxError` 로 못 읽는다 — 문서는 「JSON 규격 비준수」라 부른다 · 쓰는 쪽 `allow_nan=False` · 읽는 쪽 `parse_constant`

**출력** — 1번 출력의 `float('nan')`·`float('inf')`·`-inf` 행(`NaN`·`Infinity`·`-Infinity` · 왕복 `같다` · `allow_nan=False` 이면 `ValueError`)과 5번 `[4]` 의 `parse_constant` 가 받은 것(`['NaN', '-Infinity']`).

**왜 그런가**

* ★★★ JSON 규격(RFC)에는 **`NaN`·`Infinity` 가 없다.** 파이썬 `json` 은 **기본으로 쓰고, 기본으로 읽는다** — 그래서 파이썬끼리는 문제가 안 보인다.
  받는 쪽이 규격을 지키는 파서면 터진다 — JS `JSON.parse('NaN')` 은 **`SyntaxError`**([JS 31번](../../../js/syntax/31-json/2-summary.md) 동작 (4)의 `[4]`). JS `JSON.stringify(NaN)` 은 반대로 **`null`** 을 쓴다(같은 편 동작 (7)의 표).
* ★★ 문서 — *"This behavior is not JSON specification compliant, but is consistent with most JavaScript based encoders and decoders."* · 「Infinite and NaN Number Values」 절 — *"the results are not valid JSON"*.
* ★★ 막는 자리 — **쓸 때 `allow_nan=False`**(`ValueError 「Out of range float values are not JSON compliant: nan」` — JS 31번 동작 (7)의 출력), **읽을 때 `parse_constant`** 에서 예외를 던진다(문서 — *"This can be used to raise an exception if invalid JSON numbers are encountered."*).

### 8. 「가」만 같고 `é`·이모지는 다르다(`2 / 3`) — JSON 에는 `\x` 가 없고, `\u` 가 네 자리뿐이라 이모지는 UTF-16 대리 쌍 두 개

**출력**

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

**왜 그런가**

* ★★ JSON 의 문자열 이스케이프는 **`\u` + 16진 네 자리** 하나뿐이다(`\t` 같은 짧은 것 몇 개를 빼면). 그래서 `é` 도 `\x` 가 아니라 **`\u` 네 자리**로, U+FFFF 너머인 이모지는 **대리 쌍 두 개**로 적는다.
* ★★ 06편의 `backslashreplace` 는 **파이썬 문자열 리터럴 식** — `\xhh`·`\uxxxx`·`\Uxxxxxxxx` 세 길이를 쓴다. **BMP 안 U+0100 이상**(「가」)에서만 두 방법의 글자가 같다.
* ★ 목적은 같다 — **ASCII 밖 글자를 ASCII 로 적는다.** 되읽으면 셋 다 원래 글자다.

### 9. 못 싣는 값(`datetime`·`Decimal`·`set`)에만 · 기본 타입에는 안 불린다 · 키 자리에는 호출 0 번에 `TypeError` · 되읽으면 `str` — 되살리기는 읽는 쪽(`object_hook`) 몫

**출력**

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

**왜 그런가**

* ★★ 인코더는 **자기가 싣는 법을 아는 타입이면** `default` 를 부르지 않는다. 모를 때만 부르고 **돌려받은 것을 다시 인코딩**한다.
* ★★ 키 자리에는 그 길이 없다 — 키는 `str`·`int`·`float`·`bool`·`None` 만 받고 나머지는 **바로 `TypeError`**(호출 0 번).
* ★★★ `default` 는 **나가는 길만** 고친다 — 되읽은 JSON 에는 「원래 `datetime` 이었다」가 없다. 되살리려면 **양쪽이 약속**(키 이름·형식)하고 읽는 쪽이 `object_hook` 으로 바꾼다.
* ★ `Decimal` 을 `float` 로 실으면 `0.1` — 끝의 0 이 사라진다. `str` 로 실으면 `"0.10"` 이지만 **숫자가 아니라 글자**로 나간다.

### 10. 보장 · 관찰 · 구현(문구) · 구현 — 3.11 과 3.12 는 파이썬 인코더의 `RecursionError` 문구 한 칸에서만 갈렸다

**출력**

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

(3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e47_impl_py311.py` 다.)

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| 키는 **늘 `str`** | **라이브러리 보장** | `dumps` 의 주석 |
| `object_hook` 이 **안쪽 객체부터** | **이 판의 관찰** | 문서는 *"every JSON object decoded"* 까지 — 순서는 안 적는다 |
| `Circular reference detected` | **CPython 구현**(문구) | 실행 — 문서는 `check_circular` 의 뜻만 적는다 |
| `indent` 를 주면 **파이썬 인코더** | **CPython 구현** | 설치본 `json/encoder.py` 247\~248행의 조건 + 문구가 갈린 실행 |

* ★★ **갈린 칸** — `indent=1` + `check_circular=False` 의 `RecursionError` 문구(3.11 `while calling a Python object` · 3.12 문구 없음). **C 인코더 쪽 문구**(`while encoding a JSON object`)와 **`Circular reference detected`** 는 두 판이 같았다.
* ★ **안 갈린 것** — 1번의 타입 격자 전체(배너 줄을 빼고 한 글자도 같다).
* ★ 「C 인코더가 빠르다」는 **재지 않았다**(부적용) — 잰 것은 **어느 경로가 도나**뿐이다.

### 11. 후위 순서(뿌리가 마지막)는 같다 · 파이썬은 객체에만(3 번) JS 는 값마다(7 번) / 파이썬은 경로 없는 한 줄, V8 은 닫힌 경로까지 · 큰 정수는 JS 가 double 로 뭉갠다

**왜 그런가**

* ★★★ [JS 31번](../../../js/syntax/31-json/2-summary.md) 동작 (4)의 `reviver` 는 `"b"` → `"0"` → `"1"` → `"c"` → `"a"` → `"d"` → `""`(뿌리) — **안쪽부터, 뿌리가 마지막**. 4번의 `object_hook` 도 **안쪽부터, 뿌리가 마지막**이다.
  다른 점은 **불리는 대상** — `reviver` 는 **모든 키·값**(숫자·배열 원소까지)에, `object_hook` 은 **객체에만**. 그리고 `reviver` 는 `undefined` 를 돌려 **키를 지울 수** 있지만 `object_hook` 은 **dict 를 통째로 바꾼다.**
* ★★★ 순환 — V8 은 `--> starting at object … property 'b' -> … --- property 'back' closes the circle` 로 **길을 적는다**(JS 31번 동작 (2)). 파이썬은 `Circular reference detected` 한 줄뿐이다(6번).
* ★★ 5번의 `9007199254740993` 은 파이썬이 **정확히** 쓰고 읽는다. JS `JSON.parse` 는 숫자를 double 로 읽어 **끝자리를 바꾼다** — JS 31번 동작 (6)에서 `12345678901234567890` 이 `12345678901234567000` 이 됐다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 타입 매핑 격자 | `python3 - <e47_grid.py` · `python3.11 - <e47_grid_py311.py` | 3씩(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **14 / 26** · `allow_nan` **3 / 26** · 두 판 같음 |
| 키 | `python3 - <e47_keys.py` | 3 | **10 / 11** · 겹치는 키 **5 / 5** |
| `sort_keys` | `python3 - <e47_sortkeys.py` | 3 | 수 순서 · `TypeError` |
| 훅 | `python3 - <e47_hooks.py` | 3 | 안쪽부터 3 번 |
| 숫자 | `python3 - <e47_numbers.py` | 3 | **7 / 7** · 4301 자리 `ValueError` |
| `ensure_ascii` | `python3 - <e47_ascii.py` | 3 | **2 / 3** |
| 순환 | `python3 - <e47_cycle.py` | 3 | 한 줄 문구 |
| `default` | `python3 - <e47_default.py` | 3 | 세 타입 · 키 0 번 |
| 구현 | `python3 - <e47_impl.py` · `python3.11 - <e47_impl_py311.py` | 3씩 | 파이썬 인코더 문구만 갈림 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★ 예외 **문구** 전부 | 구현이다 — `RecursionError` 문구는 이미 판을 탔다 |
| `object_hook` 순서 · DEL 이스케이프 | 문서가 적지 않은 관찰이다 |
| 인코더 선택 조건(`indent`) | 설치본 소스의 조건이다 |

★ **안 흔들리는 칸** — 격자의 **「14 / 26」·「3 / 26」·「10 / 11」·「5 / 5」·「7 / 7」·「2 / 3」** · `dumps` 글자 · 훅 순서 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **시간·메모리 바이트**(부적용) · **JS 쪽 읽기**(JS 31번 인용).
