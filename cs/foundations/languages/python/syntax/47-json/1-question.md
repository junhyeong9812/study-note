# python/syntax/47-json — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **행마다 네 칸**(나간 글자 · 되읽은 타입 · 왕복 · `allow_nan=False`)과 **마지막 세 줄의 수**까지 적어야 맞은 것이다.
> ★★ 이 주제는 **속도·메모리 바이트를 묻지 않는다** — 한 번도 재지 않았다.
>
> 실행 환경: `python3` **3.12.3** · Linux(1번·10번은 `python3.11` 3.11.15 도 함께). 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [12](../12-dict-and-key-requirements/1-question.md)(dict 키 요건) · [13](../13-set-and-frozenset/1-question.md)(set) · [06](../06-strings-bytes-unicode/1-question.md)(인코딩).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 여러 값을 내보내고 되읽으면 (예측)

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

### 2. ★★★ 키 하나짜리 dict · 같은 글자가 되는 두 키 (예측)

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

### 3. ★★ `sort_keys` 와 키의 종류 (예측)

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

### 4. ★★★ 읽는 쪽 훅 (예측)

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

### 5. ★★ 숫자 글자를 쓰고 읽기 (예측)

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

### 6. ★★ 순환 · 공유 · `check_circular` · `default` (예측)

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

### 7. ★★★ `NaN` 을 기본으로 내보내는 것 (왜)

* 파이썬끼리는 `NaN` 이 왕복되는데 왜 이것이 사고가 되나 — **누가** 그 글자를 못 읽나?
* 문서는 이 기본값을 무엇이라 부르나 — 그리고 **어느 인자**로, **쓰는 쪽과 읽는 쪽 각각** 막나?

### 8. ★★ `ensure_ascii` 와 06편의 `backslashreplace` (경계)

* 두 방법이 **같은 글자를 내는 자리와 다른 글자를 내는 자리**는 어디인가 — `é`·「가」·이모지로 답하라.
* 이모지가 JSON 에서 **`\u` 네 자리 두 개**로 나가는 이유는?

### 9. ★★ `default=` 가 불리는 자리 (경계)

* `default` 는 **어떤 값에** 불리고 **어떤 값에** 안 불리나 — 그리고 **키 자리**에서는?
* `default=str` 로 내보낸 `datetime` 을 되읽으면 무엇인가 — 되살리는 것은 누구의 몫인가?

### 10. 층 가르기 (경계)

* 「키는 늘 `str`」·「`object_hook` 은 안쪽 객체부터」·「`Circular reference detected`」·「`indent` 를 주면 다른 인코더가 돈다」 —
  각각 **라이브러리 보장 · CPython 구현 · 이 판의 관찰** 중 어디인가?
* ★ 이 주제에서 **3.11 과 3.12 가 갈린 칸**은 무엇이었나 — 무엇은 안 갈렸나?

### 11. JS 31편과의 경계 (연결)

* ★ [JS 31번](../../../js/syntax/31-json/2-summary.md)의 `reviver` 와 4번의 `object_hook` 은 **순서의 어느 점이 같고 어느 점이 다른가**?
* ★ 같은 순환을 JS 와 파이썬에 주면 **예외가 말해 주는 것**이 어떻게 다른가 — 그리고 5번의 큰 정수를 JS 가 읽으면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
