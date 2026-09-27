# python/syntax/49-datetime-and-zoneinfo — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64, 시스템 tzdata `2026c`)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다. ★ **「지금 시각」은 한 번도 찍지 않았다** — 값은 전부 고정된 날짜로 만들었다.

## 정답

### 1. `TypeError` 칸 `4 / 20` — naive 대 aware 의 `-`·`<` 만 · 같은 두 행의 `==` 는 `False` · 뉴욕 12:00 과 UTC 16:00 은 같은 순간

**출력**

```python
# e49_grid.py
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
naive = datetime(2026, 3, 8, 12, 0)
ny = datetime(2026, 3, 8, 12, 0, tzinfo=NY)
utc = datetime(2026, 3, 8, 16, 0, tzinfo=timezone.utc)

PAIRS = [
    ("naive;naive", naive, naive.replace(hour=13)),
    ("aware NY;aware NY", ny, ny.replace(hour=13)),
    ("aware NY;aware UTC", ny, utc),
    ("naive;aware NY", naive, ny),
    ("aware NY;naive", ny, naive),
]
OPS = [
    ("-", lambda a, b: a - b),
    ("<", lambda a, b: a < b),
    ("==", lambda a, b: a == b),
    ("!=", lambda a, b: a != b),
]


def cell(fn, a, b):
    try:
        r = fn(a, b)
        return repr(r) if isinstance(r, bool) else str(r)
    except Exception as e:
        return "%s(%s)" % (type(e).__name__, e)


raised = total = 0
print("left;right\t" + "\t".join(op for op, _ in OPS))
for label, a, b in PAIRS:
    row = []
    for op, fn in OPS:
        c = cell(fn, a, b)
        total += 1
        if c.startswith("TypeError"):
            raised += 1
        row.append(c)
    print(label + "\t" + "\t".join(row))
print("cells that raised TypeError : %d / %d" % (raised, total))
```

```text
===== python3 - <e49_grid.py =====
left;right	-	<	==	!=
naive;naive	-1 day, 23:00:00	True	False	True
aware NY;aware NY	-1 day, 23:00:00	True	False	True
aware NY;aware UTC	0:00:00	False	True	False
naive;aware NY	TypeError(can't subtract offset-naive and offset-aware datetimes)	TypeError(can't compare offset-naive and offset-aware datetimes)	False	True
aware NY;naive	TypeError(can't subtract offset-naive and offset-aware datetimes)	TypeError(can't compare offset-naive and offset-aware datetimes)	False	True
cells that raised TypeError : 4 / 20
(exit 0)
```

**왜 그런가**

* ★★★ **뺄셈과 순서 비교는 naive 대 aware 에서 `TypeError`** — 문서의 연산 표 (3)·(5) 그대로다. 양방향 두 행 × 두 연산 = 4칸.
* ★★★ **같음 비교는 에러가 아니라 `False`** — *"Naive and aware `datetime` objects are never equal."* 3.3 부터 그렇다(*versionchanged 3.3*). 그래서 `!=` 는 `True`.
* ★★ **다른 `tzinfo` 끼리는 UTC 로 바꿔 계산한다** — 뉴욕 3월 8일 12:00 은 이미 EDT(`-04:00`)라 UTC 16:00 과 같은 순간이다. 차이 `0:00:00`, `==` `True`.
* ★ `-1 day, 23:00:00` 은 음수 1시간을 `timedelta` 가 정규화한 꼴이다(7번).

### 2. `[1]`\~`[4]` 는 에러 없이 못 찾는다(`False`·`False`·`None`·`2`) · `[5]`\~`[7]` 은 `TypeError` · 뒷면을 지우면 같다 · 해시도 다르다

**출력**

```python
# e49_mixed.py
from datetime import datetime, timezone

stored = datetime(2026, 3, 8, 16, 0)                       # naive — meant as UTC
incoming = datetime(2026, 3, 8, 16, 0, tzinfo=timezone.utc)

print("[1] incoming == stored        :", incoming == stored)
print("[2] incoming in [stored]      :", incoming in [stored])
print("[3] {stored: 'x'}.get(incoming):", {stored: "x"}.get(incoming))
print("[4] len({stored, incoming})   :", len({stored, incoming}))
for label, fn in [("[5] incoming > stored        ", lambda: incoming > stored),
                  ("[6] sorted([stored, incoming])", lambda: sorted([stored, incoming])),
                  ("[7] max(stored, incoming)    ", lambda: max(stored, incoming))]:
    try:
        print(label, ":", fn())
    except TypeError as e:
        print(label, ":", type(e).__name__, "-", e)
print("[8] incoming.replace(tzinfo=None) == stored :",
      incoming.replace(tzinfo=None) == stored)
print("[9] hash(incoming) == hash(stored) :", hash(incoming) == hash(stored))
```

```text
===== python3 - <e49_mixed.py =====
[1] incoming == stored        : False
[2] incoming in [stored]      : False
[3] {stored: 'x'}.get(incoming): None
[4] len({stored, incoming})   : 2
[5] incoming > stored         : TypeError - can't compare offset-naive and offset-aware datetimes
[6] sorted([stored, incoming]) : TypeError - can't compare offset-naive and offset-aware datetimes
[7] max(stored, incoming)     : TypeError - can't compare offset-naive and offset-aware datetimes
[8] incoming.replace(tzinfo=None) == stored : True
[9] hash(incoming) == hash(stored) : False
(exit 0)
```

**왜 그런가**

* ★★★ **`in`·`dict.get`·`set` 은 같음을 쓴다** — 같음이 `False` 이니 **조용히 못 찾는다.** 에러가 안 나서 가장 늦게 드러난다.
* ★★ **`>`·`sorted`·`max` 는 순서를 쓴다** — 그래서 같은 두 값이 여기서는 터진다. **어느 연산을 지나느냐로 침묵과 에러가 갈린다.**
* ★ `[8]` — `replace(tzinfo=None)` 으로 뒷면을 지우면 같다. 보통은 거꾸로 naive 쪽을 `replace(tzinfo=timezone.utc)` 로 **aware 로 올린다**(그 naive 가 정말 UTC 였을 때만).
* ★ `[9]` — 이 판에서는 해시도 다르다. 그러나 `set` 이 2 인 **근거는 같음**이다 — 문서가 요구하는 것은 「같으면 해시가 같다」뿐이다.

### 3. 없는 벽시계 `02:00`·`02:30`·`02:59` 가 예외 없이 만들어지고, 왕복하면 바뀐다(`6 / 12`) — `fold=0` 은 `-0500` 으로 읽혀 `03:30 EDT` 로 · `fold=1` 은 `-0400` 으로 읽혀 `01:30 EST` 로

**출력**

```python
# e49_gap.py
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = timezone.utc

moved = rows = 0
print("wall;fold\toffset\ttzname\tas UTC\tback to NY\tround trip same wall?")
for h, m in [(1, 30), (2, 0), (2, 30), (2, 59), (3, 0), (3, 30)]:
    for fold in (0, 1):
        d = datetime(2026, 3, 8, h, m, tzinfo=NY, fold=fold)
        u = d.astimezone(UTC)
        back = u.astimezone(NY)
        same = back.replace(tzinfo=None) == d.replace(tzinfo=None)
        rows += 1
        moved += not same
        print("%02d:%02d;%d\t%s\t%s\t%s\t%s\t%s" % (
            h, m, fold, d.strftime("%z"), d.tzname(),
            u.strftime("%H:%M"), back.strftime("%H:%M %Z"), same))
print("rows whose round trip changes the wall : %d / %d" % (moved, rows))
```

```text
===== python3 - <e49_gap.py =====
wall;fold	offset	tzname	as UTC	back to NY	round trip same wall?
01:30;0	-0500	EST	06:30	01:30 EST	True
01:30;1	-0500	EST	06:30	01:30 EST	True
02:00;0	-0500	EST	07:00	03:00 EDT	False
02:00;1	-0400	EDT	06:00	01:00 EST	False
02:30;0	-0500	EST	07:30	03:30 EDT	False
02:30;1	-0400	EDT	06:30	01:30 EST	False
02:59;0	-0500	EST	07:59	03:59 EDT	False
02:59;1	-0400	EDT	06:59	01:59 EST	False
03:00;0	-0400	EDT	07:00	03:00 EDT	True
03:00;1	-0400	EDT	07:00	03:00 EDT	True
03:30;0	-0400	EDT	07:30	03:30 EDT	True
03:30;1	-0400	EDT	07:30	03:30 EDT	True
rows whose round trip changes the wall : 6 / 12
(exit 0)
```

**왜 그런가**

* ★★★ **`ZoneInfo` 는 없는 시각을 거절하지 않는다** — 만드는 것도, 오프셋을 묻는 것도, 이름을 묻는 것도 정상이다. 드러나는 곳은 **UTC 로 갔다 돌아올 때**뿐이다(제5의 상태).
* ★★★ **PEP 495 의 규칙** — 갭 안의 시각은 `fold=0` 이면 **전이 앞 규칙**(EST `-0500`), `fold=1` 이면 **전이 뒤 규칙**(EDT `-0400`)으로 읽는다. 그래서 `02:30` 기본값은 UTC `07:30` = `03:30 EDT`.
* ★ 전이에서 먼 `01:30`·`03:00`·`03:30` 은 `fold` 가 무엇이든 같은 오프셋이고 왕복해도 그대로다.
* ★ 이 날짜와 02:00 이라는 시각은 **tzdata(`2026c`)의 것**이다 — 파이썬이 정하지 않는다.

### 4. `a == b` 가 `True` · `b - a` 가 `0:00:00`(UTC 로는 1시간) · `a == a.astimezone(UTC)` 가 `False` · 되풀이 밖의 `c` 는 `True` · UTC 에서 오면 `fold` 가 붙는다

**출력**

```python
# e49_fold.py
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = timezone.utc

a = datetime(2026, 11, 1, 1, 30, tzinfo=NY, fold=0)
b = datetime(2026, 11, 1, 1, 30, tzinfo=NY, fold=1)

print("[1] a            :", a, a.tzname(), "fold", a.fold)
print("[2] b            :", b, b.tzname(), "fold", b.fold)
print("[3] a as UTC     :", a.astimezone(UTC))
print("[4] b as UTC     :", b.astimezone(UTC))
print("[5] a == b       :", a == b)
print("[6] b - a        :", b - a)
print("[7] b.astimezone(UTC) - a.astimezone(UTC) :",
      b.astimezone(UTC) - a.astimezone(UTC))
print("[8] a == a.astimezone(UTC) :", a == a.astimezone(UTC))
print("[9] b == b.astimezone(UTC) :", b == b.astimezone(UTC))
c = datetime(2026, 11, 1, 3, 30, tzinfo=NY)
print("[10] c == c.astimezone(UTC):", c == c.astimezone(UTC))
print("[11] four UTC times seen in NY:")
for hh in (4, 5, 6, 7):
    u = datetime(2026, 11, 1, hh, 30, tzinfo=UTC)
    t = u.astimezone(NY)
    print("     %s UTC -> %s %s fold=%d" % (u.strftime("%H:%M"), t.strftime("%H:%M"), t.tzname(), t.fold))
```

```text
===== python3 - <e49_fold.py =====
[1] a            : 2026-11-01 01:30:00-04:00 EDT fold 0
[2] b            : 2026-11-01 01:30:00-05:00 EST fold 1
[3] a as UTC     : 2026-11-01 05:30:00+00:00
[4] b as UTC     : 2026-11-01 06:30:00+00:00
[5] a == b       : True
[6] b - a        : 0:00:00
[7] b.astimezone(UTC) - a.astimezone(UTC) : 1:00:00
[8] a == a.astimezone(UTC) : False
[9] b == b.astimezone(UTC) : False
[10] c == c.astimezone(UTC): True
[11] four UTC times seen in NY:
     04:30 UTC -> 00:30 EDT fold=0
     05:30 UTC -> 01:30 EDT fold=0
     06:30 UTC -> 01:30 EST fold=1
     07:30 UTC -> 02:30 EST fold=0
(exit 0)
```

**왜 그런가**

* ★★★ **같은 `tzinfo` 끼리는 `fold` 를 무시한다** — *"the `tzinfo` and `fold` attributes are ignored and the base datetimes are compared."* 벽시계 `01:30` 끼리라 같고, 차이는 `0:00:00`.
* ★★★ **되풀이 구간의 값은 다른 시간대의 값과 결코 같지 않다** — *"`datetime` instances in a repeated interval are never equal to `datetime` instances in other time zone."* 그래서 **자기 UTC 표현과도** `False` 다. 되풀이 밖의 `03:30` 은 `True`.
* ★★ **UTC → 뉴욕 변환은 `fold` 를 알맞게 붙인다** — `05:30 UTC` 는 `fold=0`(EDT), `06:30 UTC` 는 `fold=1`(EST).
* ★ 실제 경과는 UTC 로 바꿔 빼야 `1:00:00` 이다(`[7]`).

### 5. `start + 24h` 는 세 번 다 다음날 `12:00` — 실제 경과는 3월 `23:00:00` · 10월 `1 day, 1:00:00` · 6월 24시간 · 두 차이가 갈린 칸 `4 / 6` · UTC 에서 더하면 벽시계가 `13:00`·`11:00`

**출력**

```python
# e49_add24.py
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = timezone.utc
DAY = timedelta(hours=24)

split = rows = 0
print("start (NY)\tway\tresult (NY)\tresult - start\telapsed via UTC")
for start in (datetime(2026, 3, 7, 12, 0, tzinfo=NY),
              datetime(2026, 10, 31, 12, 0, tzinfo=NY),
              datetime(2026, 6, 1, 12, 0, tzinfo=NY)):
    wall = start + DAY
    absolute = (start.astimezone(UTC) + DAY).astimezone(NY)
    for way, r in (("start + 24h", wall), ("via UTC + 24h", absolute)):
        rows += 1
        split += (r - start) != (r.astimezone(UTC) - start.astimezone(UTC))
        print("%s\t%s\t%s\t%s\t%s" % (
            start.strftime("%m-%d %H:%M%z"), way, r.strftime("%m-%d %H:%M%z"),
            r - start, r.astimezone(UTC) - start.astimezone(UTC)))
print("rows where the two differences differ : %d / %d" % (split, rows))
```

```text
===== python3 - <e49_add24.py =====
start (NY)	way	result (NY)	result - start	elapsed via UTC
03-07 12:00-0500	start + 24h	03-08 12:00-0400	1 day, 0:00:00	23:00:00
03-07 12:00-0500	via UTC + 24h	03-08 13:00-0400	1 day, 1:00:00	1 day, 0:00:00
10-31 12:00-0400	start + 24h	11-01 12:00-0500	1 day, 0:00:00	1 day, 1:00:00
10-31 12:00-0400	via UTC + 24h	11-01 11:00-0500	23:00:00	1 day, 0:00:00
06-01 12:00-0400	start + 24h	06-02 12:00-0400	1 day, 0:00:00	1 day, 0:00:00
06-01 12:00-0400	via UTC + 24h	06-02 12:00-0400	1 day, 0:00:00	1 day, 0:00:00
rows where the two differences differ : 4 / 6
(exit 0)
```

**왜 그런가**

* ★★★ **aware `+ timedelta` 는 벽시계 산술** — *"no time zone adjustments are done even if the input is an aware object."* 숫자 12:00 에 24시간을 더해 다음날 12:00 을 만들고, 오프셋은 **그 날의 것**을 읽는다.
* ★★★ **같은 `tzinfo` 끼리의 빼기도 벽시계 차** — `result - start` 가 `start + 24h` 행에서 늘 `1 day, 0:00:00`. **UTC 로 바꿔 빼야** 23시간·25시간이 보인다.
* ★★ **UTC 에서 더하면 실제 경과는 24시간이고 대신 뉴욕 벽시계가 한 시간 어긋난다.** 무엇이 맞는지는 요구가 정한다(알림 = 벽시계 · 만료 = UTC).

### 6. `fromisoformat` 아홉 칸은 두 판이 같다(`Z`·기본 형식·주 날짜·`+0900` 다 됨, `2026-03` 은 둘 다 `ValueError`) · 갈린 넷은 전부 폐기 경고(`4 / 18`) · `utcnow()` 의 `tzinfo` 는 두 판 다 `None`

**출력**

```python
# e49_ver_probe.py
import datetime as dt
import warnings

CASES = [
    "2026-03-08T12:00:00",
    "2026-03-08T12:00:00+09:00",
    "2026-03-08T12:00:00Z",
    "20260308T120000",
    "2026-03-08 12:00",
    "2026-W10-7",
    "2026-03-08T12:00:00.5",
    "2026-03-08T12:00:00+0900",
    "2026-03",
]
for s in CASES:
    try:
        r = dt.datetime.fromisoformat(s)
        out = r.isoformat()
    except ValueError as e:
        out = "ValueError"
    print("fromisoformat(%r);%s" % (s, out))

print("hasattr(datetime, 'UTC');%s" % hasattr(dt, "UTC"))
for name, call in [("utcnow()", lambda: dt.datetime.utcnow()),
                   ("utcfromtimestamp(0)", lambda: dt.datetime.utcfromtimestamp(0)),
                   ("now(timezone.utc)", lambda: dt.datetime.now(dt.timezone.utc))]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = call()
    kinds = ",".join(w.category.__name__ for w in caught) or "-"
    print("%s tzinfo;%s" % (name, r.tzinfo))
    print("%s warnings;%s" % (name, kinds))
    for w in caught:
        print("%s message;%s" % (name, w.message))
```

```sh
# e49_ver_grid.sh
# 같은 탐침을 두 판으로 던져 줄마다 나란히 놓고, 갈린 줄을 센다
python3.11 - <e49_ver_probe.py >a.txt
python3 - <e49_ver_probe.py >b.txt
python3.11 -c 'import sys; print("python3.11;" + sys.version.split()[0])'
python3 -c 'import sys; print("python3;" + sys.version.split()[0])'
python3 - <<'PY'
a = open("a.txt").read().splitlines()
b = open("b.txt").read().splitlines()
ka = dict(l.split(";", 1) for l in a)
kb = dict(l.split(";", 1) for l in b)
keys = list(dict.fromkeys([l.split(";", 1)[0] for l in a + b]))
diff = 0
for k in keys:
    x, y = ka.get(k, "(none)"), kb.get(k, "(none)")
    diff += x != y
    print("%s\n    3.11 : %s\n    3.12 : %s" % (k, x, y))
print("rows that differ between 3.11 and 3.12 : %d / %d" % (diff, len(keys)))
PY
```

```text
===== cd e49_ver && bash e49_ver_grid.sh =====
python3.11;3.11.15
python3;3.12.3
fromisoformat('2026-03-08T12:00:00')
    3.11 : 2026-03-08T12:00:00
    3.12 : 2026-03-08T12:00:00
fromisoformat('2026-03-08T12:00:00+09:00')
    3.11 : 2026-03-08T12:00:00+09:00
    3.12 : 2026-03-08T12:00:00+09:00
fromisoformat('2026-03-08T12:00:00Z')
    3.11 : 2026-03-08T12:00:00+00:00
    3.12 : 2026-03-08T12:00:00+00:00
fromisoformat('20260308T120000')
    3.11 : 2026-03-08T12:00:00
    3.12 : 2026-03-08T12:00:00
fromisoformat('2026-03-08 12:00')
    3.11 : 2026-03-08T12:00:00
    3.12 : 2026-03-08T12:00:00
fromisoformat('2026-W10-7')
    3.11 : 2026-03-08T00:00:00
    3.12 : 2026-03-08T00:00:00
fromisoformat('2026-03-08T12:00:00.5')
    3.11 : 2026-03-08T12:00:00.500000
    3.12 : 2026-03-08T12:00:00.500000
fromisoformat('2026-03-08T12:00:00+0900')
    3.11 : 2026-03-08T12:00:00+09:00
    3.12 : 2026-03-08T12:00:00+09:00
fromisoformat('2026-03')
    3.11 : ValueError
    3.12 : ValueError
hasattr(datetime, 'UTC')
    3.11 : True
    3.12 : True
utcnow() tzinfo
    3.11 : None
    3.12 : None
utcnow() warnings
    3.11 : -
    3.12 : DeprecationWarning
utcfromtimestamp(0) tzinfo
    3.11 : None
    3.12 : None
utcfromtimestamp(0) warnings
    3.11 : -
    3.12 : DeprecationWarning
now(timezone.utc) tzinfo
    3.11 : UTC
    3.12 : UTC
now(timezone.utc) warnings
    3.11 : -
    3.12 : -
utcnow() message
    3.11 : (none)
    3.12 : datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
utcfromtimestamp(0) message
    3.11 : (none)
    3.12 : datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
rows that differ between 3.11 and 3.12 : 4 / 18
(exit 0)
```

**왜 그런가**

* ★★ **`fromisoformat` 은 3.11 에서 넓어졌다** — 그래서 3.11 과 3.12 는 같다. 3.10 이전에 `Z` 가 거절되던 것은 **이 머신에서 못 잰다**(가장 낮은 판이 3.11) — 문서의 *versionchanged 3.11* 만이 근거다.
* ★★★ **`utcnow()`·`utcfromtimestamp()` 는 3.12 부터 `DeprecationWarning`** — 경고를 `warnings.catch_warnings(record=True)` 로 잡아 stdout 에 찍었다. 두 판 다 **naive(`tzinfo None`)** 를 준다 — 그것이 폐기 이유다(메시지가 `datetime.now(datetime.UTC)` 로 가라고 한다).
* ★ `now(timezone.utc)` 는 두 판 다 경고 없이 aware(`UTC`)다. `datetime.UTC` 는 3.11 부터 있다.

### 7. 음수는 「-1일 + 23시간」으로 든다 · 달은 길이가 달마다 달라 칸이 없다 · `2.5` 마이크로초는 `2`(짝수 반올림)

**출력**

```python
# e49_timedelta.py
from datetime import date, datetime, timedelta

d = timedelta(hours=-1)
print("[1] timedelta(hours=-1)       :", repr(d))
print("[2] str                        :", str(d))
print("[3] .days .seconds             :", d.days, d.seconds)
print("[4] .total_seconds()           :", d.total_seconds())
print("[5] timedelta(minutes=90)      :", repr(timedelta(minutes=90)))
print("[6] timedelta(days=1) / timedelta(hours=1) :", timedelta(days=1) / timedelta(hours=1))
print("[7] timedelta(days=1) // timedelta(hours=7):", timedelta(days=1) // timedelta(hours=7))
print("[8] timedelta(days=1) % timedelta(hours=7) :", timedelta(days=1) % timedelta(hours=7))
for us in (0.5, 1.5, 2.5, 3.5):
    print("[9] timedelta(microseconds=%s)  :" % us, timedelta(microseconds=us).microseconds)
for label, fn in [
    ("[10] timedelta(months=1)       ", lambda: timedelta(months=1)),
    ("[11] date(2026,1,31).replace(month=2)", lambda: date(2026, 1, 31).replace(month=2)),
    ("[12] datetime - date           ", lambda: datetime(2026, 3, 8) - date(2026, 3, 7)),
]:
    try:
        print(label, ":", repr(fn()))
    except Exception as e:
        print(label, ":", type(e).__name__, "-", e)
print("[13] date(2026,3,31) - date(2026,1,31):", date(2026, 3, 31) - date(2026, 1, 31))
```

```text
===== python3 - <e49_timedelta.py =====
[1] timedelta(hours=-1)       : datetime.timedelta(days=-1, seconds=82800)
[2] str                        : -1 day, 23:00:00
[3] .days .seconds             : -1 82800
[4] .total_seconds()           : -3600.0
[5] timedelta(minutes=90)      : datetime.timedelta(seconds=5400)
[6] timedelta(days=1) / timedelta(hours=1) : 24.0
[7] timedelta(days=1) // timedelta(hours=7): 3
[8] timedelta(days=1) % timedelta(hours=7) : 3:00:00
[9] timedelta(microseconds=0.5)  : 0
[9] timedelta(microseconds=1.5)  : 2
[9] timedelta(microseconds=2.5)  : 2
[9] timedelta(microseconds=3.5)  : 4
[10] timedelta(months=1)        : TypeError - 'months' is an invalid keyword argument for __new__()
[11] date(2026,1,31).replace(month=2) : ValueError - day is out of range for month
[12] datetime - date            : TypeError - unsupported operand type(s) for -: 'datetime.datetime' and 'datetime.date'
[13] date(2026,3,31) - date(2026,1,31): 59 days, 0:00:00
(exit 0)
```

**왜 그런가**

* ★★ **`timedelta` 는 days·seconds·microseconds 세 칸만** 들고, `seconds` 는 늘 `0 ≤ s < 86400` 이다(문서). 그래서 −1시간이 `days=-1, seconds=82800` 이고 `str` 이 `-1 day, 23:00:00`. 뜻은 `total_seconds()` 로 읽는다.
* ★★ **달은 28\~31일로 길이가 달라** 고정 길이 칸에 담을 수 없다 — `months=` 는 `TypeError`. `timedelta(days=1)` 은 **늘 86400초**이지만, 같은 `tzinfo` 의 aware 값에 더하면 **벽시계 하루**로 읽힌다(5번) — 뜻이 하나라는 말은 기간 쪽의 이야기다.
* ★ **반쪽 마이크로초는 짝수 쪽으로** — `0.5→0`·`1.5→2`·`2.5→2`·`3.5→4`. [50번](../50-decimal-float-precision-and-round/2-summary.md)의 `round` 와 같은 은행가 반올림이다(문서 — *"round-half-to-even tiebreaker"*).

### 8. 운영체제의 tzdata(이 머신 `2026c`) · 자료를 끄면 `UTC` 도 `ZoneInfoNotFoundError` · 다른 갈래 실측은 Java 51번의 `America/Asuncion`

**출력**

```python
# e49_tz_probe.py
import zoneinfo
from datetime import datetime

with open("/usr/share/zoneinfo/tzdata.zi") as f:
    print("tzdata.zi first line   :", f.readline().rstrip())
print("zoneinfo.TZPATH        :", zoneinfo.TZPATH)
try:
    import tzdata
    print("tzdata package         : importable")
except ImportError as e:
    print("tzdata package         :", type(e).__name__)
print("available_timezones()  :", len(zoneinfo.available_timezones()))

for key, when in [("America/Coyhaique", datetime(2026, 7, 15, 12)),
                  ("America/Asuncion", datetime(2026, 1, 15, 12)),
                  ("America/Asuncion", datetime(2026, 7, 15, 12)),
                  ("Asia/Seoul", datetime(1988, 6, 1, 12)),
                  ("Asia/Seoul", datetime(2026, 6, 1, 12))]:
    try:
        d = when.replace(tzinfo=zoneinfo.ZoneInfo(key))
        print("%-18s %s : %s %s" % (key, when.date(), d.strftime("%z"), d.tzname()))
    except Exception as e:
        print("%-18s %s : %s - %s" % (key, when.date(), type(e).__name__, e))
```

```text
===== cd e49_tz && python3 - <e49_tz_probe.py =====
tzdata.zi first line   : # version 2026c
zoneinfo.TZPATH        : ('/usr/share/zoneinfo', '/usr/lib/zoneinfo', '/usr/share/lib/zoneinfo', '/etc/zoneinfo')
tzdata package         : ModuleNotFoundError
available_timezones()  : 498
America/Coyhaique  2026-07-15 : -0300 -03
America/Asuncion   2026-01-15 : -0300 -03
America/Asuncion   2026-07-15 : -0300 -03
Asia/Seoul         1988-06-01 : +1000 KDT
Asia/Seoul         2026-06-01 : +0900 KST
(exit 0)
```

```python
# e49_tz_empty.py
import zoneinfo

print("zoneinfo.TZPATH :", zoneinfo.TZPATH)
for key in ("UTC", "America/New_York"):
    try:
        zoneinfo.ZoneInfo(key)
        print(key, ": ok")
    except Exception as e:
        print(key, ":", type(e).__name__, "-", e)
```

```text
===== cd e49_tz && PYTHONTZPATH= python3 - <e49_tz_empty.py =====
zoneinfo.TZPATH : ()
UTC : ZoneInfoNotFoundError - 'No time zone found with key UTC'
America/New_York : ZoneInfoNotFoundError - 'No time zone found with key America/New_York'
(exit 0)
```

**왜 그런가**

* ★★★ **전이일은 파이썬도 명세도 아니고 IANA tzdata 가 정한다** — `zoneinfo` 는 *"uses the system's time zone data if available"*. 이 머신은 `/usr/share/zoneinfo`(판 `2026c`), `tzdata` 패키지는 없다.
* ★★ **`PYTHONTZPATH=` 는 시스템 자료를 끈다** — 문서는 「그러면 `tzdata` 패키지를 쓴다」고 하지만, 패키지가 없으니 `UTC` 까지 `ZoneInfoNotFoundError` 다. `timezone.utc` 는 자료가 필요 없다.
* ★★ **[Java 51번](../../../java/syntax/51-java-time-types/2-summary.md)의 「tzdb 판이 갈렸다」** — `America/Asuncion` 이 `2024a` 에서는 2026년 전이 넷, `2025b` 에서는 없음. **예외 없이 답만 바뀐다.** 이 머신(`2026c`)의 파이썬도 1월·7월 모두 `-0300` 으로 뒤쪽 모양이다.

### 9. `fromtimestamp(0, timezone.utc)` 한 줄만 안 바뀐다(`4 / 5`) — naive 를 받는 메서드는 이 머신의 지역 시각으로 가정한다 · `astimezone` 은 같은 순간, `replace(tzinfo=)` 는 다른 순간

**출력**

```python
# e49_local.py
from datetime import datetime, timezone

n = datetime(2026, 3, 8, 12, 0)
print("naive.astimezone(timezone.utc);%s" % n.astimezone(timezone.utc))
print("naive.timestamp();%s" % n.timestamp())
print("naive.astimezone();%s" % n.astimezone())
print("fromtimestamp(0);%s" % datetime.fromtimestamp(0))
print("fromtimestamp(0, timezone.utc);%s" % datetime.fromtimestamp(0, timezone.utc))
```

```sh
# e49_local_grid.sh
# 같은 naive 값을 TZ 환경변수만 바꿔 세 번 던지고, TZ 에 따라 갈린 줄을 센다
for z in UTC Asia/Seoul America/New_York; do
  TZ=$z python3 - <e49_local.py >"out_${z//\//_}.txt"
done
python3 - <<'PY'
names = ["UTC", "Asia/Seoul", "America/New_York"]
cols = [dict(l.split(";", 1) for l in open("out_%s.txt" % z.replace("/", "_")).read().splitlines())
        for z in names]
diff = 0
for k in cols[0]:
    vals = [c[k] for c in cols]
    diff += len(set(vals)) > 1
    print(k)
    for z, v in zip(names, vals):
        print("    TZ=%-16s : %s" % (z, v))
print("rows that change with TZ : %d / %d" % (diff, len(cols[0])))
PY
```

```text
===== cd e49_local && bash e49_local_grid.sh =====
naive.astimezone(timezone.utc)
    TZ=UTC              : 2026-03-08 12:00:00+00:00
    TZ=Asia/Seoul       : 2026-03-08 03:00:00+00:00
    TZ=America/New_York : 2026-03-08 16:00:00+00:00
naive.timestamp()
    TZ=UTC              : 1772971200.0
    TZ=Asia/Seoul       : 1772938800.0
    TZ=America/New_York : 1772985600.0
naive.astimezone()
    TZ=UTC              : 2026-03-08 12:00:00+00:00
    TZ=Asia/Seoul       : 2026-03-08 12:00:00+09:00
    TZ=America/New_York : 2026-03-08 12:00:00-04:00
fromtimestamp(0)
    TZ=UTC              : 1970-01-01 00:00:00
    TZ=Asia/Seoul       : 1970-01-01 09:00:00
    TZ=America/New_York : 1969-12-31 19:00:00
fromtimestamp(0, timezone.utc)
    TZ=UTC              : 1970-01-01 00:00:00+00:00
    TZ=Asia/Seoul       : 1970-01-01 00:00:00+00:00
    TZ=America/New_York : 1970-01-01 00:00:00+00:00
rows that change with TZ : 4 / 5
(exit 0)
```

```python
# e49_forms.py
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SEOUL = ZoneInfo("Asia/Seoul")
u = datetime(2026, 3, 8, 3, 0, tzinfo=timezone.utc)

print("[1] made with tzinfo=        :", datetime(2026, 3, 8, 12, 0, tzinfo=SEOUL))
print("[2] u.astimezone(SEOUL)      :", u.astimezone(SEOUL))
print("[3] u.replace(tzinfo=SEOUL)  :", u.replace(tzinfo=SEOUL))
print("[4] [2] == u                 :", u.astimezone(SEOUL) == u)
print("[5] [3] == u                 :", u.replace(tzinfo=SEOUL) == u)
print("[6] u.tzinfo, .utcoffset()   :", u.tzinfo, u.utcoffset())
print("[7] naive .tzinfo, .utcoffset():", datetime(2026, 3, 8).tzinfo, datetime(2026, 3, 8).utcoffset())
```

```text
===== python3 - <e49_forms.py =====
[1] made with tzinfo=        : 2026-03-08 12:00:00+09:00
[2] u.astimezone(SEOUL)      : 2026-03-08 12:00:00+09:00
[3] u.replace(tzinfo=SEOUL)  : 2026-03-08 03:00:00+09:00
[4] [2] == u                 : True
[5] [3] == u                 : False
[6] u.tzinfo, .utcoffset()   : UTC 0:00:00
[7] naive .tzinfo, .utcoffset(): None None
(exit 0)
```

**왜 그런가**

* ★★★ **naive 는 「어느 시간대인지 프로그램이 정한다」 — 그런데 `astimezone`·`timestamp()` 는 그것을 「지역 시각」으로 정해 버린다.** 문서의 경고 — *"naive `datetime` objects are treated by many `datetime` methods as local times"*. 그래서 `TZ` 만 바꿔도 같은 값이 UTC 로 `12:00`·`03:00`·`16:00`.
* ★★ **시간대를 인자로 준 호출만 `TZ` 와 무관하다** — `fromtimestamp(0, timezone.utc)`.
* ★★ **`astimezone(Z)` 는 「같은 순간을 다른 벽시계로」**(`[4]` `True`), **`replace(tzinfo=Z)` 는 「벽시계는 두고 뒷면만 바꾸기」**(`[5]` `False` — 9시간 다른 순간).

### 10. 보장 · 보장 · tzdata · CPython 구현 — 「없는 시각을 막지 않는다」의 근거는 PEP 495 의 갭 규칙

* **라이브러리 보장** — naive 대 aware `==` 가 `False`(연산 표 (4) · 3.3) · 같은 `tzinfo` 끼리 `fold` 무시(표 (4)·(5)).
* **tzdata** — 뉴욕이 2026-03-08 02:00 에 당기는 것. 판이 바뀌면 움직일 수 있다.
* **CPython 구현** — 예외 문구 `can't compare offset-naive and offset-aware datetimes`.
* ★ **「없는 시각이 만들어진다」의 근거** — PEP 495 가 갭 안의 시각에 대해 **`utcoffset()` 이 무엇을 돌려야 하는지를 정한다**(*"the rules in effect before the transition should be used if `fold=0`"*). 돌려줄 값이 정해져 있다는 것 자체가 **그 값을 만들 수 있다**는 뜻이다. 실행(3번)이 그대로였다.

### 11. Java 는 `03:30` 으로 바꿨다 — 파이썬 `fold=0` 왕복 결과와 같은 값, Java 는 만드는 순간 · 파이썬은 UTC 로 갈 때 / `set` 은 2개 — 근거는 같음

* ★★ **[Java 51번](../../../java/syntax/51-java-time-types/2-summary.md) 동작 (3)** — `atZone` 이 `2026-03-08T03:30-04:00[America/New_York]` 을 돌려줬다(javadoc — *"shifted forwards by the length of the Gap"*).
  파이썬은 `datetime(2026,3,8,2,30,tzinfo=NY)` 가 **`02:30` 인 채로 남고**, UTC 로 갔다 돌아올 때 `fold=0` 이면 `03:30 EDT`(같은 값), `fold=1` 이면 `01:30 EST` 가 된다(3번).
  ★ Java 의 `ofStrict` 처럼 **엄격하게 거절하는 생성자는 `zoneinfo` 에 없다** — 검사는 스스로 해야 한다(요약의 「더 들어가면」).
* ★ **[12번](../12-dict-and-key-requirements/2-summary.md)** — `set` 원소는 **2개**(2번 `[4]`). 이 판에서는 해시도 달랐지만(`[9]`), 해시가 같더라도 `==` 가 `False` 면 다른 원소이므로 **근거는 같음 쪽**이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| naive/aware 격자 | `python3 - <e49_grid.py` | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **4 / 20** 이 `TypeError` · `==` 는 `False` |
| 섞인 값 찾기 | `python3 - <e49_mixed.py` | 3 | `in` `False` · `set` 2 · `sorted` `TypeError` |
| 갭 | `python3 - <e49_gap.py` | 3 | 왕복해 벽시계가 바뀐 칸 **6 / 12** |
| fold | `python3 - <e49_fold.py` | 3 | `a == b` `True` · `a == a.astimezone(UTC)` `False` |
| 24시간 | `python3 - <e49_add24.py` | 3 | 두 차이가 갈린 칸 **4 / 6** |
| `timedelta` | `python3 - <e49_timedelta.py` | 3 | `-1 day, 23:00:00` · 짝수 반올림 |
| 판 격자 | `cd e49_ver && bash e49_ver_grid.sh`(`python3.11`·`python3`) | 3 | **4 / 18** — 전부 폐기 경고 |
| 환경 | `cd e49_tz && python3 - <e49_tz_probe.py` · `PYTHONTZPATH= python3 - <e49_tz_empty.py` | 3씩 | tzdata `2026c` · `ZoneInfoNotFoundError` |
| `TZ` 격자 | `cd e49_local && bash e49_local_grid.sh` | 3 | **4 / 5** 줄이 `TZ` 로 갈림 |
| 만드는 형태 | `python3 - <e49_forms.py` | 3 | `astimezone` `True` · `replace` `False` |
| 고정 오프셋·ISO 왕복 | `python3 - <e49_fixed.py` | 3 | 7월 `-0500` · 왕복 뒤 오프셋만 남음 |
| 서드파티 | `python3 - <e49_thirdparty.py` | 3 | `pytz` `tzinfo=` 는 `LMT` · `relativedelta` 2월 28일 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★★ **tzdata 판**(환경 블록 · 전이일이 걸린 모든 블록) | 지역 규칙은 IANA 가 바꾼다 — Java 51번의 아순시온처럼 **예외 없이 답만** 바뀐다 |
| ★★ 판 격자 | `utcnow` 는 *"scheduled for removal in a future version"* — 없어지면 그 행이 `AttributeError` 가 될 것이다(★ 예측이지 측정이 아니다) |
| 예외 **문구** · 경고 **메시지** | 구현이다 |
| ★ `TZ` 격자 | `TZ` 를 행마다 줬으므로 머신의 지역 설정과는 무관하다 — 윈도는 이 머신에 없어 못 잰 것 |

★ **안 흔들리는 칸** — 격자의 **「4 / 20」·「6 / 12」·「4 / 6」·「4 / 18」·「4 / 5」** · 예외 타입 · `fold` 값 · `(exit N)`.
★★ **이 주제가 한 번도 안 찍은 것** — **「지금 시각」**(부적용 — 값을 전부 만들어 썼다) · **3.10 이전 · 윈도**(판·플랫폼 없음 — 못 잰 것).
