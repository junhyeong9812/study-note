# python/syntax/49-datetime-and-zoneinfo — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **스무 칸을 전부** 적고, 마지막 줄의 수까지 세어야 맞은 것이다. 3번·5번도 마지막 줄의 수까지.
> ★★ 이 주제는 **「지금 시각」을 한 번도 쓰지 않는다** — 값은 전부 고정된 날짜로 만든다.
>
> 실행 환경: `python3` **3.12.3** · Linux · 시간대 자료는 시스템 tzdata **`2026c`**(6번은 `python3.11` 3.11.15 도 함께). 던지는 형태는 `python3 - <파일` 이다.
> ★ 선행 — 없음. 함께 보는 곳 — [12](../12-dict-and-key-requirements/1-question.md)(키의 같음) · [Java 51](../../../java/syntax/51-java-time-types/1-question.md)(같은 갭을 Java 로).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 다섯 짝 × 네 연산 — naive 와 aware (예측)

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

### 2. ★★★ naive 로 저장한 값을 aware 로 찾으면 (예측)

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

### 3. ★★★ 뉴욕 2026-03-08 새벽의 여섯 벽시계 × 두 `fold` (예측)

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

### 4. ★★★ 뉴욕 2026-11-01 01:30 두 개 (예측)

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

### 5. ★★★ 세 시작점에 24시간을 두 방법으로 (예측)

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

### 6. ★★ ISO 문자열 아홉 개와 `utcnow` — 두 판 (예측)

```text
탐침 하나를 아래 셸 스크립트가 두 인터프리터로 던진다. 열여덟 항목마다 두 판의 값을 적고, 마지막 줄의 수를 적는다.
```

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

### 7. ★★ `timedelta` 가 들고 있는 칸 (왜)

* `timedelta(hours=-1)` 을 `str` 로 찍으면 왜 `-1:00:00` 이 아닌 꼴이 나오나 — `timedelta` 는 **무엇을 몇 칸** 들고 있나?
* `timedelta(months=1)` 이 안 되는 이유를 「단위의 길이」로 설명할 수 있나 — 그러면 `timedelta(days=1)` 은 서머타임 날에도 뜻이 하나인가?
* 마이크로초 `2.5` 를 받으면 몇이 되나 — [50번](../50-decimal-float-precision-and-round/2-summary.md)의 어느 규칙과 같은가?

### 8. ★★ 시간대 규칙은 어디서 오나 (경계)

* `ZoneInfo("America/New_York")` 가 뉴욕의 전이일을 아는 것은 **파이썬·명세·운영체제** 중 누구 덕인가 — 이 머신에서 그 출처의 판을 어떻게 찍나?
* `PYTHONTZPATH=` 로 던지고 `tzdata` 패키지도 없으면 `ZoneInfo("UTC")` 는 무엇을 하나?
* 같은 코드가 tzdata 판에 따라 **예외 없이 다른 답**을 내는 실측이 다른 갈래에 있다 — 어느 지역이었나?

### 9. ★★ `TZ` 만 바꿔 같은 naive 를 던지면 (경계)

* `naive.astimezone(timezone.utc)`·`naive.timestamp()`·`naive.astimezone()`·`fromtimestamp(0)`·`fromtimestamp(0, timezone.utc)` 중 **`TZ` 에 따라 답이 바뀌는 것**은 어느 것이고, 왜 그런가?
* `u.astimezone(SEOUL)` 과 `u.replace(tzinfo=SEOUL)` 은 각각 `u` 와 같은 순간인가?

### 10. 층 가르기 (경계)

* 「naive 대 aware 의 `==` 는 `False`」·「같은 `tzinfo` 끼리는 `fold` 를 무시하고 비교한다」·「뉴욕은 2026-03-08 02:00 에 시계를 당긴다」·「`can't compare offset-naive and offset-aware datetimes`」 —
  각각 **라이브러리 보장 · tzdata · CPython 구현** 중 어디인가?
* 「`ZoneInfo` 는 없는 시각을 만들 때 에러를 내지 않는다」를 근거로 쓸 때, 그 근거는 어느 문서 문장인가?

### 11. 이웃 주제와의 경계 (연결)

* ★ [Java 51번](../../../java/syntax/51-java-time-types/2-summary.md)은 `2026-03-08 02:30 America/New_York` 을 무엇으로 바꿨나 — 파이썬의 `fold=0`·`fold=1` 중 어느 쪽의 왕복 결과와 같은 값이고, **바뀌는 시점**은 어떻게 다른가?
* ★ [12번](../12-dict-and-key-requirements/2-summary.md)의 키 규칙으로 보면, naive 16:00 과 aware 16:00 UTC 를 한 `set` 에 넣으면 원소가 몇 개인가 — 그 까닭은 해시인가 같음인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
