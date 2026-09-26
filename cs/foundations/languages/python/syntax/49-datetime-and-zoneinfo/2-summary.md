# python/syntax/49-datetime-and-zoneinfo — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`datetime` — Aware and Naive Objects(3.12)](https://docs.python.org/3.12/library/datetime.html#aware-and-naive-objects) — *"A **naive** object does not contain enough information to unambiguously locate itself relative to other date/time objects."*
> - [`datetime` 객체의 연산 표(3.12)](https://docs.python.org/3.12/library/datetime.html#datetime-objects) — 덧셈 *"Note that no time zone adjustments are done even if the input is an aware object."* ·
>   뺄셈 *"If one is aware and the other is naive, `TypeError` is raised."* · *"If both are naive, or both are aware and have the same `tzinfo` attribute, the `tzinfo` attributes are ignored"* ·
>   같음 *"Naive and aware `datetime` objects are never equal."* · 순서 *"Order comparison between naive and aware `datetime` objects … raises `TypeError`."* ·
>   *"If both comparands are aware, and have the same `tzinfo` attribute, the `tzinfo` and `fold` attributes are ignored and the base datetimes are compared."* ·
>   *"`datetime` instances in a repeated interval are never equal to `datetime` instances in other time zone."* · *versionchanged 3.3* — *"Equality comparisons between aware and naive `datetime` instances don't raise `TypeError`."*
> - [`datetime.fold`](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.fold) — *"The values 0 and 1 represent, respectively, the earlier and later of the two moments with the same wall time representation."*(3.6)
> - [`datetime.fromisoformat`](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.fromisoformat) — *versionchanged 3.11* — *"Previously, this method only supported formats that could be emitted by `date.isoformat` or `datetime.isoformat`."*
> - [`datetime.utcnow`](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow) — *deprecated 3.12* — *"Use `datetime.now` with `UTC` instead."* · [`datetime.UTC`](https://docs.python.org/3.12/library/datetime.html#datetime.UTC)(3.11)
> - [`timedelta`](https://docs.python.org/3.12/library/datetime.html#timedelta-objects) — *"Only days, seconds and microseconds are stored internally."* · *"… their sum is rounded to the nearest microsecond using round-half-to-even tiebreaker."*
> - [`zoneinfo`(3.9+)](https://docs.python.org/3.12/library/zoneinfo.html) — *"By default, `zoneinfo` uses the system's time zone data if available; if no system time zone data is available, the library will fall back to using the first-party `tzdata` package"* ·
>   *"the offset from before the transition is used when `fold=0`, and the offset after the transition is used when `fold=1`"* · *"To set the system to ignore the system data and use the tzdata package instead, set `PYTHONTZPATH=""`."*
> - [PEP 495 — Local Time Disambiguation](https://peps.python.org/pep-0495/) — *"If the `utcoffset()`, `tzname()` or `dst()` method is called on a local time that falls in a gap, the rules in effect before the transition should be used if `fold=0`."* · [PEP 615](https://peps.python.org/pep-0615/)(`zoneinfo`)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 판 격자 한 블록(동작 7)을 더 던졌다. 서드파티 대비로 `pytz` **2024.1** · `dateutil` **2.8.2** 한 블록(「더 들어가면」).\
> ★★★ **「지금 시각」을 한 번도 찍지 않았다** — 모든 값은 `datetime(2026, 3, 8, 12, 0)` 처럼 **고정된 값을 만들어서** 계산했다. `utcnow()` 는 부르되 **경고와 `tzinfo` 만** 찍었다(동작 7).\
> ★★ **시간대 자료는 이 머신의 시스템 tzdata(`/usr/share/zoneinfo`, 판 `2026c`)** 다 — `tzdata` 패키지는 깔려 있지 않다(동작 8).\
> **버전** — `fold` **3.6**(PEP 495) · `zoneinfo` **3.9**(PEP 615) · `fromisoformat` 확장·`datetime.UTC` **3.11** · `utcnow`·`utcfromtimestamp` 폐기 경고 **3.12** · naive 대 aware `==` 가 에러 대신 `False` **3.3**.\
> ★ **구현 대 언어 보장 한 줄** — naive/aware 연산 규칙·`fold` 의 뜻은 **라이브러리 보장**, 예외 **문구**는 CPython 의 것, **어느 지역이 어느 날 몇 시간 차이인가는 파이썬도 명세도 아니고 IANA tzdata 가 정한다**(이 머신의 판 `2026c` 의 관찰).\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★★ **tzdata 판이 바뀌면** — `available_timezones()` 개수 · 지역별 오프셋(동작 8 의 `America/Asuncion`·`America/Coyhaique` 행) | ★★ 격자 마지막 줄 **「… N / M」** 전부 |
> | 머신의 `TZ`·`/etc/localtime` 이 바뀌면 **naive 를 지역 시각으로 읽는 칸**(그래서 동작 9 는 `TZ=` 를 **행마다 명시**했다) | 예외 **타입** · `(exit N)` · `fold` 값 |
> | 판이 오르면 예외 **문구**와 폐기 경고 **메시지** | naive/aware 연산표의 칸(3.3 이후 문서가 정한 것) |
> | — (주소·시간·「지금 시각」·`set` 출력을 한 곳도 안 찍었다) | 2026년 뉴욕 전이 시각(3월 8일 · 11월 1일) — ★ 단 이것도 tzdata 의 것이지 파이썬의 것이 아니다 |
>
> **선행** — 없음(README 선행 칸 `—`). ★ 함께 보면 좋은 곳 — [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)(키의 같음 — naive 와 aware 가 **dict 의 다른 키**가 되는 자리, 동작 2) ·
> [50-decimal-float-precision-and-round](../50-decimal-float-precision-and-round/2-summary.md)(짝수 반올림 — `timedelta` 의 마이크로초 반올림이 같은 규칙이다, 동작 6).

## 한눈에 — 쉽게 말하면

**`datetime` 은 「벽시계 사진」이고, `tzinfo` 는 그 사진 뒷면에 적힌 「어느 도시의 벽시계인가」 메모다.**

* **naive** — 뒷면이 **빈 사진.** 12:00 이라는 것은 보이는데 서울의 12:00 인지 뉴욕의 12:00 인지 **사진만으로는 모른다.**
* **aware** — 뒷면에 **도시가 적힌 사진.** 그래서 다른 도시 사진과 「**어느 쪽이 먼저 찍혔나**」를 가릴 수 있다.
* ★ **빈 사진과 적힌 사진을 나란히 놓고 「누가 먼저냐」 물으면 파이썬은 답을 거부한다**(`TypeError`). 그런데 **「같은 순간이냐」 물으면 거부하지 않고 「아니다」라고 답한다**(`False`) — 여기가 함정이다.
* **`timedelta` 를 더하는 것은 「사진 속 시곗바늘을 돌리는 것」** 이다. 뒷면 메모는 그대로 두고 바늘만 24시간 돌린다 — 그 사이에 그 도시가 **시계를 한 시간 당겼어도** 모른다.
* **도시마다 「언제 시계를 당기고 되돌리나」 달력(tzdata)** 은 파이썬이 아니라 **운영체제가 들고 있다.**

```text
   같은 12:00 — 뒷면 메모가 있나 없나

   naive  : [ 12:00 | 뒷면 빈칸 ]          aware : [ 12:00 | 뒷면 "America/New_York" ]
                  |                                        |
                  |      naive - aware   -> TypeError      |
                  +----- naive < aware   -> TypeError -----+
                         naive == aware  -> False  (에러가 아니다)

   aware + 24시간  = 바늘만 24칸 돌린다 (뒷면 그대로)
      03-07 12:00 EST  --(+24h)-->  03-08 12:00 EDT      실제로 흐른 시간은 23시간
                                   ^ 그 사이 뉴욕이 시계를 1시간 당겼다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 벽시계 사진 | `datetime` 값(연·월·일·시·분·초·마이크로초) | `repr` |
| 뒷면이 빈 사진 | **naive** — `tzinfo is None` | `d.utcoffset()` 이 `None` |
| 뒷면에 도시가 적힌 사진 | **aware** — `tzinfo` 가 오프셋을 준다 | `d.utcoffset()` 이 `timedelta` |
| 「누가 먼저냐」 거부 | naive 대 aware 의 `-`·`<` 가 `TypeError` | naive/aware 격자(동작 1) |
| 「같은 순간이냐」에 「아니다」 | naive 대 aware 의 `==` 가 **`False`** | 같은 격자 · 조용한 누락(동작 2) |
| 바늘만 돌린다 | aware `+ timedelta` 는 **벽시계 산술** | 24시간 격자(동작 5) |
| 없는 시각에 찍힌 사진 | DST 가 시작될 때 **건너뛴 시각**(gap) | 갭 격자(동작 3) |
| 같은 시각에 두 번 찍힌 사진 | DST 가 끝날 때 **되풀이되는 시각**(fold) — `fold=0`/`1` | fold 덤프(동작 4) |
| 도시별 시계 달력 | IANA tzdata(이 머신 `2026c`) | 환경 덤프(동작 8) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**DB 에서 읽은 시각(naive)과 API 에서 받은 시각(aware)을 비교했더니 조건이 한 번도 참이 안 된다**」·
「**매일 같은 시각에 돌리려고 `+ timedelta(days=1)` 을 했는데 서머타임 날만 한 시간 어긋난다**」·
「**`02:30` 에 예약한 작업이 3월 둘째 일요일에만 이상한 시각에 돈다**」가 그것이다.\
첫째는 **`==` 가 에러 없이 `False`** 인 것이고, 둘째는 **aware 덧셈이 벽시계 산술**인 것이고, 셋째는 **그 도시에 02:30 이 없는 날**이다.

> **naive** — `tzinfo` 가 없는(또는 `utcoffset()` 이 `None` 인) `datetime`. 어느 시간대의 시각인지는 **프로그램이 알아서 정한다**.\
> 예: `datetime(2026, 3, 8, 12, 0)`.

> **aware** — `tzinfo` 가 오프셋을 돌려주는 `datetime`. 다른 aware 값과 **같은 순간인지·어느 쪽이 먼저인지**를 가릴 수 있다.\
> 예: `datetime(2026, 3, 8, 12, 0, tzinfo=ZoneInfo("America/New_York"))`.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① naive/aware 연산 격자다.** 다섯 짝(naive끼리 · 같은 시간대 aware끼리 · 다른 시간대 aware끼리 · naive 대 aware 양방향) × 네 연산(`-`·`<`·`==`·`!=`)을 한 표로 찍고, **`TypeError` 가 난 칸을 스크립트가 센다.**
그리고 ② **UTC 창**(`astimezone(timezone.utc)` 로 바꿔 다시 계산하기)이 **벽시계 산술이 감춘 실제 경과 시간**을 드러낸다 — 이것이 이 주제의 네 번째 창이다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **naive/aware 연산 격자** | 어느 짝·연산이 **에러 / `False` / 값**인가 | — |
| ② ★★★ **UTC 창**(UTC 로 바꿔 빼기·더하기) | 벽시계 차이와 **실제 경과**가 갈리는가 | — |
| ③ ★★★ **갭·fold 격자**(`fold=0`/`1` × 전이 앞뒤 시각) | 없는 시각·두 번 있는 시각을 **파이썬이 어떻게 읽나** | — |
| ④ ★★ **환경 창**(tzdata 판 · `TZPATH` · `PYTHONTZPATH=`) | 시간대 규칙이 **어디서 오나** · 없으면 무엇이 나나 | 윈도의 시스템 자료 |
| ⑤ ★★ **`TZ` 격자**(`TZ=` 를 행마다 바꿔 던지기) | naive 를 **지역 시각으로 읽는** 메서드가 어느 것인가 | — |
| ⑥ ★ **판 격자**(3.11 대 3.12) | `fromisoformat` 입력 · 폐기 경고 | 3.10 이전 |
| ★ **제5의 상태** — 「없는 시각이다」 | `ZoneInfo` 는 **`02:30` 을 만들 때 아무 말도 안 한다** — 그래서 같은 질문을 **UTC 로 갔다 돌아와 벽시계가 바뀌나**로 물었다(동작 3) | ★ 그 창은 **「왜 없나」(tzdata 의 규칙)** 는 못 본다 — 전이 시각은 tzdata 가 정한다 |
| ★ **못 잰 것** — 3.10 이전의 `fromisoformat` | — | 이 머신의 가장 낮은 판이 3.11 이다 — 문서 인용만 |
| ★ **부적용** — 시간 측정·「지금 시각」 | — | 한 번도 재지도 찍지도 않았다 |

★★ **②가 이 주제의 네 번째 창이다.** 같은 시간대 aware 두 값을 빼면 파이썬은 `tzinfo` 를 **무시하고** 벽시계끼리 뺀다 — 그래서 서머타임이 낀 하루도 `1 day, 0:00:00` 이 나온다.
**UTC 로 바꾼 뒤 빼야** `23:00:00` 이 보인다(동작 5 — `rows where the two differences differ : 4 / 6`).

## 이 주제가 답하려는 질문

1. ★★★ **naive 와 aware 를 섞으면 무엇이 되나** — 빼기·순서 비교·같음 비교가 각각 에러인가, 값인가. 그리고 에러가 안 나는 쪽이 왜 더 위험한가.
2. ★★★ **서머타임 경계에서 `datetime` 은 무엇을 하나** — 없는 시각(`02:30`) · 두 번 있는 시각(`01:30`) · `fold` · `+ timedelta(hours=24)` 가 실제로 몇 시간인가.
3. ★★ **시간대 규칙과 문자열은 어디서 오고 어디로 가나** — tzdata · `TZ` 환경 · `fromisoformat`/`isoformat` · 3.11 과 3.12 의 경계.

★ 첫째와 둘째가 이 주제의 인출 목표다.
**「naive 대 aware 는 `-`·`<` 가 에러이고 `==` 는 `False` 다 · 같은 시간대 aware 의 산술은 벽시계 산술이다 · 실제 경과는 UTC 로 바꿔 잰다」 세 문장으로 격자 두 개의 갈린 칸을 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ naive/aware 연산 격자 — 다섯 짝 × 네 연산

**언제 쓰나** — 두 `datetime` 을 빼거나 비교할 때마다. 특히 **출처가 다른** 두 값(DB · API · 사용자 입력)을 만날 때.

```text
   다섯 짝 — 왼쪽 값 ; 오른쪽 값

   naive ; naive              12:00 (빈 뒷면)       ; 13:00 (빈 뒷면)
   aware NY ; aware NY        12:00 뉴욕            ; 13:00 뉴욕          (같은 tzinfo 객체)
   aware NY ; aware UTC       12:00 뉴욕(EDT -4)    ; 16:00 UTC           (같은 순간, 다른 tzinfo)
   naive ; aware NY           12:00 (빈 뒷면)       ; 12:00 뉴욕
   aware NY ; naive           (위를 뒤집은 것)

   각 짝에 네 연산  a - b   a < b   a == b   a != b   → 결과 또는 예외 이름(메시지)
```

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

그림 해설.

* ★★★ **마지막 줄 — `TypeError` 가 난 칸 `4 / 20`.** 전부 **naive 대 aware 두 행의 `-`·`<` 칸**이다.
  문서 — 뺄셈 *"If one is aware and the other is naive, `TypeError` is raised."* · 순서 *"Order comparison between naive and aware `datetime` objects … raises `TypeError`."*
* ★★★ **같은 두 행의 `==` 는 `False`, `!=` 는 `True`** — 에러가 아니다. 문서 — *"Naive and aware `datetime` objects are never equal."*
  ★ 이 칸은 **3.3 에서 바뀌었다** — *"Equality comparisons between aware and naive `datetime` instances don't raise `TypeError`."* 그 전에는 여기서도 에러였다(이 머신의 판으로는 못 잰다 — 문서 인용).
* ★★ **`aware NY ; aware UTC` 행은 `-` 가 `0:00:00`, `==` 가 `True`** — 뉴욕 12:00(EDT)과 UTC 16:00 은 **같은 순간**이다. 다른 `tzinfo` 끼리는 **UTC 로 바꿔서** 계산한다(문서의 (3)·(4)).
* ★ **`-1 day, 23:00:00`** 은 「마이너스 1시간」이다 — `timedelta` 는 음수를 **「-1일 + 23시간」** 으로 정규화해 들고 있다(동작 6).

**비용** — 에러가 나는 칸은 **싸다** — 바로 드러난다. **비싼 것은 `==` 칸**이다. 같은 순간을 가리키는 두 값이 `False` 로 나와도 아무도 모른다(동작 2).

### 2. ★★★ `==` 가 `False` 인 칸이 조용히 새는 자리 — `in` · `dict` · `set`

**언제 쓰나** — naive 로 저장된 값을 aware 값으로 찾을 때. 「DB 는 UTC 로 저장했다(단, naive 로)」는 코드가 전형이다.

```text
   stored   = 16:00 (빈 뒷면 — 「UTC 라고 생각하고」 저장)
   incoming = 16:00 UTC (뒷면 "UTC")

   ==, in, dict.get, set    →  같음 비교를 쓴다   →  에러 없이 「다르다」
   >, sorted, max           →  순서 비교를 쓴다   →  TypeError
```

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

그림 해설.

* ★★★ **`[1]`\~`[4]` 가 전부 에러 없이 「못 찾았다」** — `in` 은 `False`, `dict.get` 은 `None`, `set` 은 **두 원소**. 모두 **같음 비교**를 쓰기 때문이다.
  ★ `set` 이 2 인 것 — 이 판에서는 **해시부터 다르다**(`[9]` `False`). 해시가 우연히 같더라도 `==` 가 `False` 면 다른 원소다([12번](../12-dict-and-key-requirements/2-summary.md)의 키 규칙 그대로) — 근거는 **같음 쪽**이다(해시 값은 CPython 의 것이고 문서는 「같으면 해시가 같다」만 요구한다).
* ★★ **`[5]`\~`[7]` 은 에러다** — `sorted`·`max` 는 **순서 비교(`<`)** 를 쓴다. 같은 두 값인데 **어느 연산을 거치느냐로 에러 / 침묵이 갈린다.**
* ★ **`[8]`** — `replace(tzinfo=None)` 으로 **뒷면을 지우면** 같아진다. 거꾸로 naive 쪽에 `replace(tzinfo=timezone.utc)` 를 붙이는 것이 보통의 처방이다 — 단 **그 naive 가 정말 UTC 였을 때만** 맞다(동작 9).

### 3. ★★★ 없는 시각 — 2026-03-08 02:30 뉴욕 (갭)

**언제 쓰나** — 사용자가 입력한 벽시계 시각에 시간대를 붙일 때. 예약·배치 시각.

```text
   America/New_York 의 2026-03-08 (tzdata 2026c)

   벽시계  01:30  01:59 | 03:00  03:30
   ----------------------+ |
                         | +--------------
                  -05:00 | -04:00
                     EST | EDT
                         ^
               02:00 ~ 02:59 는 이 날 벽시계에 없다 (gap)

   datetime(2026,3,8,2,30,tzinfo=NY)  → 만들어진다(예외 없음)
      fold=0 → 전이 「앞」 규칙으로 읽는다 (-05:00)  → UTC 07:30 → 돌아오면 03:30 EDT
      fold=1 → 전이 「뒤」 규칙으로 읽는다 (-04:00)  → UTC 06:30 → 돌아오면 01:30 EST
```

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

그림 해설.

* ★★★ **`02:30` 은 예외 없이 만들어진다** — `ZoneInfo` 는 「없는 시각」을 막지 않는다. 그래서 이 칸은 **세 창(만들기 · 오프셋 · 이름)이 전부 정상**이다 — 제5의 상태.
  같은 질문을 **UTC 로 갔다 돌아오기**로 물으니 갈렸다 — **`rows whose round trip changes the wall : 6 / 12`**, 정확히 `02:00`·`02:30`·`02:59` 세 벽시계 × `fold` 두 값.
* ★★★ **`fold=0` 은 전이 앞 오프셋(`-0500`), `fold=1` 은 전이 뒤 오프셋(`-0400`)** — PEP 495 의 규칙 그대로다: *"the rules in effect before the transition should be used if `fold=0`. Otherwise, the rules in effect after the transition should be used."*
  ★ 그래서 **기본값(`fold=0`)의 `02:30` 은 돌아오면 `03:30`** — 한 시간 **앞으로** 밀린다. `fold=1` 은 `01:30` 으로 **뒤로** 간다.
* ★★ **Java 는 같은 입력을 「앞으로 민다」고 javadoc 이 못 박는다** — [Java 51번](../../../java/syntax/51-java-time-types/2-summary.md)의 동작 (3)이 **같은 날 같은 시각**(`2026-03-08 02:30 America/New_York`)으로 `03:30` 을 얻었다.
  파이썬 기본(`fold=0`)의 왕복 결과와 **같은 값**이지만 경로가 다르다 — Java 는 **만드는 순간** 옮기고, 파이썬은 **값을 그대로 두고** UTC 로 갈 때 드러난다.
* ★ **`01:30` 은 `fold` 가 무엇이든 `-0500`**, `03:00` 이후는 `-0400` — 전이에서 먼 칸은 `fold` 가 뜻이 없다.

> **갭(gap)** — 시계를 앞으로 당겨 **그 지역 벽시계에서 사라진 구간**. PEP 495 의 말로 그 안의 시각은 *missing*.\
> 예: 뉴욕의 2026-03-08 02:00\~02:59.

### 4. ★★★ 두 번 있는 시각 — 2026-11-01 01:30 뉴욕 (fold)

**언제 쓰나** — 서머타임이 끝나는 날의 로그·예약. **같은 벽시계가 두 번 흐르는** 한 시간.

```text
   America/New_York 의 2026-11-01

   UTC     04:30   05:30   06:30   07:30
   뉴욕    00:30   01:30   01:30   02:30
           EDT     EDT     EST     EST
                   fold=0  fold=1          ← 같은 벽시계, 다른 순간(1시간 차)

   a = 01:30 fold=0 (EDT)     b = 01:30 fold=1 (EST)     (tzinfo 는 같은 NY 객체)
      a == b ?  a 와 b 를 빼면 ?  a 를 UTC 로 바꾼 값과 a 는 같은가 ?
```

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

그림 해설.

* ★★★ **`[5] a == b` 가 `True`, `[6] b - a` 가 `0:00:00`** — UTC 로는 **한 시간 떨어진**(`[3]`·`[4]`) 두 순간인데. 같은 `tzinfo` 끼리는 **`fold` 를 무시하고 벽시계를 비교**한다.
  문서 — *"If both comparands are aware, and have the same `tzinfo` attribute, the `tzinfo` and `fold` attributes are ignored and the base datetimes are compared."*
* ★★★ **`[8]`·`[9]` — `a == a.astimezone(UTC)` 가 `False`.** **자기 자신을 UTC 로 바꾼 값과 같지 않다.** 되풀이 구간 밖의 `c`(03:30)는 `True`(`[10]`).
  문서가 이것을 따로 적는다 — *"`datetime` instances in a repeated interval are never equal to `datetime` instances in other time zone."*
  ★ 이 규칙이 있는 까닭(★ 추론 — 문서는 이유를 적지 않는다) — 같은 `tzinfo` 끼리는 `a == b` 가 `True` 인데 `a`·`b` 가 UTC 의 다른 두 값과 각각 같으면 **같음이 추이적이지 않게** 된다. 문서는 그것을 막으려 되풀이 구간 쪽의 교차 같음을 전부 `False` 로 둔다.
* ★★ **`[11]` — UTC 에서 뉴욕으로 올 때는 `fold` 가 알아서 붙는다**(`06:30 UTC -> 01:30 EST fold=1`). 문서 — *"When converting from another time zone, the fold will be set to the correct value"*.
* ★ **`[7]`** — 실제 경과는 **UTC 로 바꿔 빼야** `1:00:00` 이다. 동작 5 의 네 번째 창과 같은 처방.

> **fold** — 벽시계가 되돌아가 **같은 시각이 두 번** 오는 구간에서 **앞의 것(0)** 과 **뒤의 것(1)** 을 가르는 속성(3.6+, PEP 495).\
> 예: 뉴욕 2026-11-01 01:30 `fold=0` 은 EDT, `fold=1` 은 EST.

### 5. ★★★ `+ timedelta(hours=24)` 는 벽시계 산술 — 실제로는 23 · 25시간

**언제 쓰나** — 「내일 같은 시각」 · 「24시간 뒤 만료」를 계산할 때. 두 요구는 **서머타임 날에만** 다른 답을 낸다.

```text
   세 시작점 × 두 방법

   시작 03-07 12:00 EST (갭 전날)  /  10-31 12:00 EDT (fold 전날)  /  06-01 12:00 EDT (전이 없음)

   start + 24h       벽시계 바늘을 24칸 → 다음날 12:00 (오프셋은 그 날의 것)
   via UTC + 24h     UTC 로 가서 24시간 → 다시 뉴욕으로

   각 결과에 두 차이 : result - start (같은 tzinfo — 벽시계 차)   /   UTC 로 바꿔 뺀 것 (실제 경과)
```

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

그림 해설.

* ★★★ **`start + 24h` 는 세 시작점 모두 「다음날 12:00」** — 3월에는 **실제 경과 `23:00:00`**, 10월 말에는 **`1 day, 1:00:00`**(25시간). 6월만 24시간이다.
  문서 — *"Note that no time zone adjustments are done even if the input is an aware object."* 바늘만 돌리고 오프셋은 **도착한 날의 것**을 새로 읽는다.
* ★★★ **`result - start` 는 벽시계 차를 준다** — `start + 24h` 행은 세 번 다 `1 day, 0:00:00`. 3월 행은 실제로 23시간인데 **빼기가 그것을 감춘다.**
  마지막 줄 **`rows where the two differences differ : 4 / 6`** — 두 차이가 갈린 칸이 **서머타임이 낀 네 행**이다.
* ★★ **「정확히 24시간 뒤」가 필요하면 UTC 에서 더한다** — `via UTC + 24h` 행은 실제 경과가 늘 `1 day, 0:00:00` 이고, 대신 뉴욕 벽시계가 `13:00`·`11:00` 으로 **한 시간 어긋난다.**
  ★ 둘 중 무엇이 맞는지는 **요구가 정한다** — 「매일 12시 알림」은 벽시계 쪽, 「토큰 24시간 만료」는 UTC 쪽.
* ★ 공식 문서의 예제도 같은 성질을 보인다 — `ZoneInfo` 문서의 `dt + timedelta(days=1)` 가 `-07:00` 에서 `-08:00` 으로 넘어가며 **벽시계 12:00 을 지킨다**(*"handle daylight saving time transitions with no further intervention"*).

> **벽시계 산술(wall-clock arithmetic)** — 오프셋 변화를 무시하고 **표시된 날짜·시각 숫자**끼리 더하고 빼는 것. 같은 `tzinfo` 를 가진 aware 값의 `+`·`-` 가 이것이다.\
> 예: 뉴욕 03-07 12:00 + 24시간 = 03-08 12:00(실제 23시간).

### 6. ★★ `timedelta` — 세 칸만 들고 있고, 달(月)은 모른다

**언제 쓰나** — 기간을 만들고 나누고 비교할 때.

```text
   timedelta 가 들고 있는 것  ─  days · seconds(0 ≤ s < 86400) · microseconds

   timedelta(hours=-1)   →  days=-1, seconds=82800     「-1일 + 23시간」 = -1시간
   timedelta(minutes=90) →  seconds=5400
   timedelta(months=1)   →  그런 칸이 없다
```

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

그림 해설.

* ★★ **`[1]`\~`[4]`** — 음수 기간은 `days` 만 음수이고 `seconds` 는 늘 0 이상이다. 그래서 `str` 이 **`-1 day, 23:00:00`** 이다. 뜻을 읽을 때는 **`total_seconds()`**(`-3600.0`).
* ★★ **`[6]`\~`[8]`** — `timedelta` 끼리 나누면 `float`, `//` 는 `int`, `%` 는 `timedelta`. 「하루는 몇 시간인가」는 `timedelta(days=1) / timedelta(hours=1)` 로 묻는다.
* ★★ **`[9]` — 마이크로초의 반쪽은 짝수로 반올림**(`0.5→0` · `1.5→2` · `2.5→2` · `3.5→4`). 문서 — *"rounded to the nearest microsecond using round-half-to-even tiebreaker"*. [50번](../50-decimal-float-precision-and-round/2-summary.md)의 `round` 와 같은 규칙이다.
* ★★★ **`[10]`\~`[11]` — 달은 없다.** `months=` 는 `TypeError`, `replace(month=2)` 로 흉내 내면 1월 31일에서 `ValueError`. **달 산술은 표준 라이브러리 밖**이다(「더 들어가면」의 `relativedelta`).
* ★ **`[12]`** — `datetime - date` 도 `TypeError` — `datetime` 은 `date` 의 하위 클래스인데도 섞어 빼지 못한다.

### 7. ★★ 판 격자 — `fromisoformat` 입력 아홉 개 · 폐기 경고 · `datetime.UTC`

**언제 쓰나** — ISO 문자열을 읽거나, 3.11 이전·3.12 이후를 함께 지원하는 코드를 쓸 때.

```text
   탐침 하나를 두 판(python3.11 · python3)으로 던져 줄마다 나란히 놓는다

   fromisoformat('...')      → 파싱된 값의 isoformat() 또는 ValueError
   utcnow() · utcfromtimestamp(0) · now(timezone.utc)
                             → 값은 안 찍는다. tzinfo · 잡힌 경고의 범주 · 메시지만
   마지막 줄                 → 두 판이 갈린 줄 N / M
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

그림 해설.

* ★★★ **마지막 줄 — `rows that differ between 3.11 and 3.12 : 4 / 18`.** 갈린 넷은 전부 **폐기 경고**다 — `utcnow()`·`utcfromtimestamp(0)` 의 경고 범주와 메시지.
  ★ 두 판 모두 결과의 **`tzinfo` 는 `None`** — 이름은 「UTC」인데 **naive 를 준다.** 그것이 폐기의 이유다(메시지 — *"Use timezone-aware objects to represent datetimes in UTC"*).
* ★★ **`fromisoformat` 아홉 칸은 두 판이 한 글자도 같다** — `Z` 접미사 · `20260308T120000`(기본 형식) · 공백 구분 · 주 날짜(`2026-W10-7`) · `+0900` 이 **3.11 에서도 다 된다.**
  넓어진 것은 3.11 **부터**이기 때문이다(*versionchanged 3.11*). **3.10 이전에서 `Z` 가 거절되던 것은 이 머신에서 못 잰다** — 가장 낮은 판이 3.11 이다. 문서의 *"Previously, this method only supported formats that could be emitted by `date.isoformat` or `datetime.isoformat`"* 만이 근거다.
* ★ **`2026-03` 은 두 판 다 `ValueError`** — 문서가 적은 예외 목록 그대로(*"Reduced precision dates are not currently supported"*).
* ★ **`hasattr(datetime, 'UTC')` 가 3.11 에서 `True`** — `datetime.UTC` 는 3.11 부터다.

### 8. ★★ 시간대 규칙은 어디서 오나 — tzdata 판 · `TZPATH` · 자료가 없으면

**언제 쓰나** — 서버·컨테이너·윈도에 배포할 때. **코드는 같은데 답이 다른** 자리다.

```text
   ZoneInfo("America/New_York") 가 찾는 순서

   TZPATH 의 디렉토리들  ──있으면──▶  그 파일(이 머신: /usr/share/zoneinfo, 판 2026c)
        │ 없으면
        ▼
   tzdata 패키지(PyPI)  ──있으면──▶  그 안의 자료
        │ 없으면                      (이 머신: 안 깔려 있다)
        ▼
   ZoneInfoNotFoundError
```

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

그림 해설.

* ★★★ **첫 블록의 위 네 줄이 이 문서 전체의 전제다** — 시스템 tzdata **`2026c`**, `tzdata` 패키지 **없음**(`ModuleNotFoundError`), 시간대 **498** 개. **이 칸들은 머신과 판이 바뀌면 흔들린다**(머리말 표).
* ★★ **둘째 블록 — `PYTHONTZPATH=` 로 시스템 자료를 끄면 `UTC` 조차 `ZoneInfoNotFoundError`.** 문서가 말한 「`tzdata` 패키지로 대신한다」는 **그 패키지가 있을 때의 이야기**이고, 이 머신에는 없으니 **아무것도 안 남는다.**
  ★ 윈도는 시스템에 IANA 자료가 없다 — 문서가 *"it is recommended to declare a dependency on tzdata"* 라고 적는 까닭(이 머신에서 못 잰다).
* ★★ **`America/Asuncion` 의 1월·7월이 둘 다 `-0300`** — 이 판에서는 **서머타임 전이가 없다.** [Java 51번](../../../java/syntax/51-java-time-types/2-summary.md)의 「tzdb 판이 갈렸다」 절이 **`2024a` 에서는 2026년 전이 넷, `2025b` 에서는 없음**을 찍었다 — 같은 지역 이름에 **답만 바뀐** 사례다. 이 머신(`2026c`)은 뒤쪽과 같은 모양이다.
  ★ `America/Coyhaique` 도 `2024a` 에는 없던 이름인데(같은 Java 편) 이 판에서는 된다.
* ★ **`Asia/Seoul` 1988-06-01 은 `+1000 KDT`** — 한국에도 서머타임이 있던 해다. 이것도 **tzdata 가 들고 있는 역사**다.

> **tzdata(IANA time zone database)** — 세계 각 지역의 **UTC 오프셋과 서머타임 전이의 역사·규칙** 을 모은 자료. 판 번호(`2026c`)가 있고 정치적 결정에 따라 자주 바뀐다.\
> 예: 리눅스는 `/usr/share/zoneinfo` 에, 파이썬 패키지로는 `tzdata` 에 있다.

### 9. ★★ naive 를 「지역 시각」으로 읽는 메서드 — `TZ` 격자

**언제 쓰나** — naive 값을 `astimezone`·`timestamp()` 에 넘길 때. **개발 머신과 서버의 `TZ` 가 다르면** 답이 바뀐다.

```text
   같은 naive 12:00 을 TZ 환경변수만 바꿔 세 번

   TZ=UTC             TZ=Asia/Seoul          TZ=America/New_York
   naive 를 00 오프셋  naive 를 +09:00 으로    naive 를 -04:00 으로   ← 메서드가 알아서 가정한다
```

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

그림 해설.

* ★★★ **마지막 줄 — `rows that change with TZ : 4 / 5`.** 안 바뀐 한 줄은 **`fromtimestamp(0, timezone.utc)`** — 시간대를 **인자로 준** 호출뿐이다.
* ★★★ **`naive.astimezone(timezone.utc)`·`naive.timestamp()` 는 naive 를 「이 머신의 지역 시각」으로 가정한다** — 같은 값이 `12:00`·`03:00`·`16:00` UTC 로 갈린다. 에러도 경고도 없다.
  문서의 `utcnow` 경고가 바로 이 말이다 — *"Because naive `datetime` objects are treated by many `datetime` methods as local times, it is preferred to use aware datetimes to represent times in UTC."*
* ★ **`fromtimestamp(0)` 도 naive 지역 시각을 준다** — 서울에서는 `09:00`, 뉴욕에서는 **전날** `19:00`.
* ★ 그래서 이 블록은 **`TZ=` 를 행마다 명시**해 던졌다 — 아무것도 안 주면 이 머신의 `/etc/localtime` 이 답을 고른다(흔들리는 칸).

## 문법 — 형태와 규칙

```text
   aware 값을 만드는 세 형태 — 결과가 다르다

   datetime(Y,M,D,h,m, tzinfo=Z)   이 벽시계 숫자를 Z 의 시각으로 「만든다」
   d.astimezone(Z)                 같은 순간을 Z 의 벽시계로 「바꿔 본다」   (값이 같다)
   d.replace(tzinfo=Z)             벽시계 숫자는 그대로 두고 뒷면만 「갈아 끼운다」 (다른 순간)
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

* ★★ **`astimezone` 은 같은 순간(`[4]` `True`), `replace(tzinfo=)` 는 다른 순간(`[5]` `False`)** — `03:00 UTC` 에 서울 뒷면을 끼우면 `03:00+09:00`, 즉 **9시간 전**이 된다.
* **aware 판정** — `d.tzinfo is not None and d.utcoffset() is not None`(문서의 정의). naive 는 `utcoffset()` 이 `None`(`[7]`).
* **UTC 는 `timezone.utc`**(또는 3.11+ 의 `datetime.UTC`) — `ZoneInfo("UTC")` 와 같은 순간을 주지만 **다른 객체**다.
* **시간대 이름은 IANA 키로** — `ZoneInfo("America/New_York")`. `EST`·`KST` 같은 약어는 **이름**(`tzname()`)이지 키가 아니다.
* **고정 오프셋이 필요하면 `timezone(timedelta(hours=-5))`** — 서머타임이 없다(아래 (5)).
* **문자열** — 읽기 `datetime.fromisoformat(s)` · 쓰기 `d.isoformat(timespec=…)` · 자유 형식 `strftime`/`strptime`.
* ★ **금지 사례** — 코드 펜스가 아니라 표로 적는다(규칙 28).

  | 쓴 꼴 | 결과 | 어느 절 |
  |---|---|---|
  | `naive - aware` · `naive < aware` | `TypeError` | 동작 1 |
  | `timedelta(months=1)` | `TypeError`(그런 키워드 없음) | 동작 6 |
  | `datetime - date` | `TypeError` | 동작 6 |
  | `fromisoformat('2026-03')` | `ValueError` | 동작 7 |
  | `ZoneInfo(k)`(자료 없음) | `ZoneInfoNotFoundError` | 동작 8 |

## 어디서 틀리나

### (1) ★★★ naive 와 aware 를 `==` 로 비교하고 결과를 믿는다

에러가 안 나니 **통과한 것처럼 보인다.** 같은 순간이어도 `False`(동작 1·2) — `in`·`dict`·`set` 이 전부 조용히 못 찾는다. 처방은 **경계에서 전부 aware 로 바꾸는 것**이다.

### (2) ★★★ 「비교에서 에러가 나니 섞이면 알아챈다」고 믿는다

**순서 비교만** 에러다. 같음은 에러가 아니다 — **3.3 부터**(동작 1). 같은 두 값이 `sorted` 에서는 터지고 `in` 에서는 조용하다(동작 2).

### (3) ★★★ 「내일 같은 시각」과 「24시간 뒤」를 같은 식으로 계산한다

같은 `tzinfo` 의 `+ timedelta(hours=24)` 는 **벽시계 산술**이라 서머타임 날에 실제로 23·25시간이다(동작 5). 「정확히 24시간」은 **UTC 에서 더한다.**

### (4) ★★★ 같은 시간대 aware 둘을 빼서 경과 시간이라 믿는다

`result - start` 는 **벽시계 차**다 — 3월 행이 `1 day, 0:00:00` 인데 실제로는 23시간(동작 5). 되풀이 구간의 `b - a` 는 **`0:00:00`**(동작 4). 경과는 **UTC 로 바꿔서 뺀다.**

### (5) ★★ 고정 오프셋 `timezone(timedelta(hours=-5))` 을 「뉴욕」으로 쓴다

1월에는 맞고 7월에는 한 시간 틀린다. 그리고 **`isoformat` 문자열을 다시 읽으면 시간대 이름이 아니라 오프셋만 남는다** — 뉴욕 1월 값을 왕복시킨 뒤 180일을 더하면 `-0500` 그대로다.

```python
# e49_fixed.py
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
MINUS5 = timezone(timedelta(hours=-5))

print("month;ZoneInfo NY;timezone(-5h)")
for month in (1, 7):
    a = datetime(2026, month, 15, 12, tzinfo=NY)
    b = datetime(2026, month, 15, 12, tzinfo=MINUS5)
    print("%02d;%s %s;%s %s" % (month, a.strftime("%H:%M%z"), a.tzname(),
                                 b.strftime("%H:%M%z"), b.tzname()))

w = datetime(2026, 1, 15, 12, tzinfo=MINUS5)
print("[1] Jan -5h value + 180 days  :", (w + timedelta(days=180)).strftime("%m-%d %H:%M%z"))
print("[2] same, zone NY             :", (w.replace(tzinfo=NY) + timedelta(days=180)).strftime("%m-%d %H:%M%z"))
print("[3] ZoneInfo(k) is ZoneInfo(k):", ZoneInfo("America/New_York") is ZoneInfo("America/New_York"))
print("[4] ZoneInfo.no_cache(k) is ZoneInfo(k):", ZoneInfo.no_cache("America/New_York") is ZoneInfo("America/New_York"))
u1 = datetime(2026, 3, 8, 12, tzinfo=timezone.utc)
u2 = datetime(2026, 3, 8, 12, tzinfo=ZoneInfo("UTC"))
print("[5] timezone.utc vs ZoneInfo('UTC') == :", u1 == u2)
print("[6] str(tzinfo)                 :", u1.tzinfo, "/", u2.tzinfo)
print("[7] isoformat NY                :", datetime(2026, 3, 8, 12, tzinfo=NY).isoformat())
print("[8] isoformat(timespec='minutes'):", datetime(2026, 3, 8, 12, 5, 7, 250000, tzinfo=NY).isoformat(timespec="minutes"))
print("[9] strftime %Y-%m-%d %H:%M %Z %z:", datetime(2026, 3, 8, 12, tzinfo=NY).strftime("%Y-%m-%d %H:%M %Z %z"))
print("[10] naive isoformat             :", datetime(2026, 3, 8, 12).isoformat())
p = datetime.fromisoformat(datetime(2026, 1, 15, 12, tzinfo=NY).isoformat())
print("[11] parsed back tzinfo          :", repr(p.tzinfo))
print("[12] parsed + 180 days           :", (p + timedelta(days=180)).strftime("%m-%d %H:%M%z"))
```

```text
===== python3 - <e49_fixed.py =====
month;ZoneInfo NY;timezone(-5h)
01;12:00-0500 EST;12:00-0500 UTC-05:00
07;12:00-0400 EDT;12:00-0500 UTC-05:00
[1] Jan -5h value + 180 days  : 07-14 12:00-0500
[2] same, zone NY             : 07-14 12:00-0400
[3] ZoneInfo(k) is ZoneInfo(k): True
[4] ZoneInfo.no_cache(k) is ZoneInfo(k): False
[5] timezone.utc vs ZoneInfo('UTC') == : True
[6] str(tzinfo)                 : UTC / UTC
[7] isoformat NY                : 2026-03-08T12:00:00-04:00
[8] isoformat(timespec='minutes'): 2026-03-08T12:05-04:00
[9] strftime %Y-%m-%d %H:%M %Z %z: 2026-03-08 12:00 EDT -0400
[10] naive isoformat             : 2026-03-08T12:00:00
[11] parsed back tzinfo          : datetime.timezone(datetime.timedelta(days=-1, seconds=68400))
[12] parsed + 180 days           : 07-14 12:00-0500
(exit 0)
```

* ★★ **`[11]`·`[12]`** — ISO 8601 문자열에는 **도시가 없다.** 「어느 도시의 벽시계인가」를 지키려면 **키(`America/New_York`)를 따로 저장**해야 한다.
* ★ **`[3]`·`[4]`** — `ZoneInfo(k)` 는 캐시에서 **같은 객체**를 준다(`is` 가 `True`). `no_cache` 는 새 객체다. 같은 `tzinfo` **객체**냐가 동작 4 의 비교 규칙을 가르므로 이 차이가 뜻이 있다.

### (6) ★★★ `02:30` 에 시간대를 붙이면 에러가 날 것이라 믿는다

**안 난다**(동작 3). `ZoneInfo` 는 없는 시각을 그대로 들고 있다가, UTC 로 갈 때 `fold=0` 이면 **한 시간 앞으로** 밀린 순간이 된다. 없는 시각을 막고 싶으면 **UTC 왕복 뒤 벽시계가 바뀌었나**로 스스로 검사해야 한다.

### (7) ★★ 되풀이 구간의 두 `01:30` 이 `==` 로 갈릴 것이라 믿는다

같은 `tzinfo` 면 **`fold` 를 무시한다**(동작 4 `[5]` `True`). 그리고 그 값은 **자기 UTC 표현과 같지 않다**(`[8]` `False`).

### (8) ★★ naive 를 「UTC 라고 약속했으니」 `astimezone`·`timestamp()` 에 넘긴다

메서드는 그 약속을 모른다 — **이 머신의 지역 시각**으로 읽는다(동작 9, `4 / 5` 줄이 `TZ` 로 갈린다). 약속이 있으면 **`replace(tzinfo=timezone.utc)` 로 코드에 적는다.**

### (9) ★★ `utcnow()` 가 aware UTC 를 준다고 믿는다

**naive** 를 준다(`tzinfo None`). 3.12 부터 `DeprecationWarning`(동작 7). `datetime.now(timezone.utc)` 로 바꾼다.

### (10) ★ `timedelta(months=1)` 로 한 달을 더한다

그런 칸이 없다(`TypeError`). `replace(month=…)` 는 31일에서 `ValueError`(동작 6). 달은 **「며칠인가」가 달마다 다른 단위**라 `timedelta` 가 들 수 없다. 서드파티 `relativedelta` 는 된다(「더 들어가면」).

### (11) ★ 「시간대 자료는 파이썬에 들어 있다」고 믿는다

**운영체제의 것**이다(동작 8). 컨테이너 최소 이미지·윈도에서 없으면 `ZoneInfoNotFoundError` — `tzdata` 패키지를 의존성으로 둔다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `datetime`·`zoneinfo` 문서와 PEP 495 가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 예외 문구 · 폐기 경고 메시지 · `ZoneInfo` 캐시가 같은 객체를 주는 것의 구체적 모양 | 실행 |
| ★★ **tzdata(IANA)** | **어느 지역이 언제 몇 시간 차이인가** — 뉴욕의 2026 전이일 · 서울의 1988 서머타임 · 아순시온의 전이 없음 | 이 머신의 시스템 자료 `2026c` |
| **이 판(3.12.3 · 3.11.15)·이 머신의 관찰** | 이 판·이 머신에서 그랬을 뿐 | 출력 |
| ★ **못 잰 것** | 3.10 이전의 `fromisoformat` · 3.3 이전의 `==` · 윈도의 시간대 자료 | 판·플랫폼이 없다 |
| ★ **부적용** | 시간 측정 · 「지금 시각」 | 재지도 찍지도 않았다 |

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| naive 대 aware 의 뺄셈·순서 비교는 `TypeError` | `datetime` 연산 표 (3)·(5) |
| naive 대 aware 는 **같지 않다**(에러 아님, 3.3+) | 같은 표 (4) · *versionchanged 3.3* |
| aware `+ timedelta` 는 오프셋을 조정하지 않는다 | 표 (1) — *"no time zone adjustments are done even if the input is an aware object"* |
| 같은 `tzinfo` 끼리의 빼기·비교는 `tzinfo`·`fold` 를 무시한다 | 표 (3)·(4)·(5) |
| 다른 `tzinfo` 끼리는 UTC 로 바꾼 것처럼 계산한다 | 표 (3)·(4)·(5) |
| 되풀이 구간의 값은 다른 시간대의 값과 **결코 같지 않다** | 표 (4) |
| 갭에서 `fold=0` 은 전이 앞 규칙, `fold=1` 은 뒤 규칙 | PEP 495 *Mind the Gap* · `zoneinfo` 문서(fold) |
| `timedelta` 는 days·seconds·microseconds 만 들고, 반쪽 마이크로초는 짝수 반올림 | `timedelta` 절 |
| `zoneinfo` 는 시스템 자료 → `tzdata` 패키지 순으로 찾는다 · 둘 다 없으면 `ZoneInfoNotFoundError` | `zoneinfo` 문서 Data sources |
| `fromisoformat` 이 3.11 에서 넓어졌다 · `utcnow` 는 3.12 폐기 | 해당 절의 *versionchanged*·*deprecated* |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 예외 **문구** — `can't subtract offset-naive and offset-aware datetimes` · `can't compare …` · `'months' is an invalid keyword argument for __new__()` · `No time zone found with key UTC` | 실행 |
| 폐기 경고 **메시지** 전문(3.12.3) | 실행(동작 7) |
| `timedelta` 의 `repr` 꼴(`datetime.timedelta(days=-1, seconds=82800)`) · `str` 꼴(`-1 day, 23:00:00`) | 실행 — ★ `str` 꼴은 문서의 표에도 있다 |

### 이 판(3.12.3)의 관찰

- **tzdata `2026c` · 시간대 498 개 · `tzdata` 패키지 없음** — 이 머신의 것이다(동작 8).
- **뉴욕의 2026 전이가 3월 8일 02:00 · 11월 1일 02:00** 인 것 — tzdata 의 규칙을 이 판이 읽은 결과다(동작 3·4).
- **`fromisoformat` 아홉 칸이 3.11 과 3.12 에서 같았던 것**(판 격자에서 갈린 넷은 전부 경고).
- **이 머신의 `/etc/localtime`** 은 이 문서의 어떤 블록도 쓰지 않았다 — 동작 9 는 `TZ=` 를 줬다.

### 그래서 이렇게 적으면 틀린다

* ✗ 「naive 와 aware 를 비교하면 `TypeError`」\
  ○ **순서 비교만.** `==` 는 `False` 다(3.3+).
* ✗ 「aware 값에 24시간을 더하면 24시간 뒤다」\
  ○ **같은 `tzinfo` 안에서는 벽시계 24칸**이다 — 뉴욕 3월 7일 → 8일은 **실제 23시간**. UTC 에서 더해야 24시간.
* ✗ 「`ZoneInfo` 는 없는 시각을 거절한다」\
  ○ **만들어진다.** `fold=0` 이면 전이 앞 오프셋으로 읽혀 UTC 에서는 한 시간 뒤 순간이 된다.
* ✗ 「같은 순간이면 `==` 는 `True`」\
  ○ **되풀이 구간은 예외**다 — `a == a.astimezone(UTC)` 가 `False`.
* ✗ 「서머타임 날짜는 파이썬이 안다」\
  ○ **tzdata 가 안다** — 판이 바뀌면 같은 코드의 답이 바뀐다(Java 51번의 아순시온).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 저장·전송·비교할 순간 | **aware UTC**(`timezone.utc`) | 전이가 없어 산술이 곧 경과다 |
| 사용자에게 보일 시각 | aware UTC 를 `astimezone(ZoneInfo(키))` | 표시 직전에 바꾼다 |
| 「매일 9시」 같은 벽시계 규칙 | 지역 `ZoneInfo` 에서 `+ timedelta(days=1)` | 벽시계 산술이 바로 그 요구다 — **단 갭·fold 날을 따로 검사** |
| 「정확히 N 시간 뒤」 | UTC 에서 더하고 표시할 때 바꾼다 | 서머타임 날에도 N 시간 |
| 경과 시간 | 두 값을 UTC 로 바꿔 뺀다 | 같은 `tzinfo` 빼기는 벽시계 차다 |
| 날짜만(생일·마감일) | `date` | 시각·시간대가 없다 — 섞지 않는다 |
| 시간대 **이름**을 지켜야 한다 | ISO 문자열 + **키를 따로** 저장 | ISO 에는 오프셋만 남는다 |
| 서머타임 없는 고정 오프셋 | `timezone(timedelta(...))` | 뜻이 정말 「늘 -5시간」일 때만 |
| 현재 시각 | `datetime.now(timezone.utc)` | `utcnow()` 는 naive · 3.12 폐기 |
| 윈도·최소 컨테이너 배포 | `tzdata` 패키지 의존성 | 시스템 자료가 없을 수 있다 |

## 핵심 문장

1. **naive 대 aware 는 `-`·`<` 가 `TypeError` 이고 `==` 는 `False`** — 격자에서 에러 칸 **4 / 20**, 같음 칸은 조용하다(3.3+).
2. **같은 `tzinfo` 끼리의 산술·비교는 벽시계 숫자로 한다** — 뉴욕 `+ 24h` 가 실제 23·25시간, 두 차이가 갈린 칸 **4 / 6**.
3. **실제 경과는 UTC 로 바꿔 잰다** — 이 주제의 네 번째 창이다.
4. **없는 시각은 막히지 않고, `fold=0` 이면 전이 앞 규칙으로 읽힌다** — 왕복해 벽시계가 바뀐 칸 **6 / 12**. 되풀이 구간의 값은 **자기 UTC 표현과도 같지 않다.**
5. **시간대 규칙은 tzdata 의 것이다** — 이 머신은 시스템 `2026c`, 자료를 끄면 `UTC` 도 없다.

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **49번**
* 함께 보는 곳: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — ★ **경계**: 해시·같음이 키를 정하는 규칙은 그쪽이 정본. 여기는 **naive 와 aware 가 그 규칙 아래서 다른 키가 되는 자리**(동작 2)만.
* 함께 보는 곳: [50-decimal-float-precision-and-round](../50-decimal-float-precision-and-round/2-summary.md) — 짝수 반올림의 정본. 여기는 `timedelta` 의 마이크로초 반올림 한 줄(동작 6).
* 다른 갈래: [Java 51 — `java.time`](../../../java/syntax/51-java-time-types/2-summary.md) — ★ **같은 날 같은 시각의 갭**(2026-03-08 02:30 뉴욕)을 Java 가 「앞으로 민다」로 푸는 것 · **tzdb 판이 갈려 아순시온의 답이 바뀐** 실측은 그쪽이 정본. 여기는 **파이썬이 같은 입력을 `fold` 로 어떻게 읽나**.
* 다른 갈래: Go 갈래 [README](../../../go/syntax/README.md) 의 48번 행(`time` — `Time`·`Duration`·단조 시계) — 아직 폴더가 없다. 경과 시간을 재는 시계(단조 시계)는 이 편의 범위 밖이다.
* 공식 문서: [`datetime`](https://docs.python.org/3.12/library/datetime.html) · [`zoneinfo`](https://docs.python.org/3.12/library/zoneinfo.html) · [PEP 495](https://peps.python.org/pep-0495/) · [PEP 615](https://peps.python.org/pep-0615/) · [IANA Time Zone Database](https://www.iana.org/time-zones)

## 용어 풀이

* **naive / aware**: `tzinfo` 가 오프셋을 **안 주는 / 주는** `datetime`. aware 만 다른 값과 순간을 견줄 수 있다.\
  예: `datetime(2026,3,8,12)` 는 naive.
* **`tzinfo`**: `datetime` 에 붙는 시간대 객체. `utcoffset()`·`tzname()`·`dst()` 를 답한다.\
  예: `timezone.utc` · `ZoneInfo("Asia/Seoul")`.
* **UTC 오프셋(UTC offset)**: 그 지역 벽시계가 UTC 보다 얼마나 앞서거나 뒤진가.\
  예: 뉴욕 여름 `-04:00`, 서울 `+09:00`.
* **서머타임(DST, daylight saving time)**: 여름 동안 시계를 한 시간 당기는 제도. 갭과 fold 의 원인이다.\
  예: 뉴욕은 3월 둘째 일요일에 당기고 11월 첫째 일요일에 되돌린다(tzdata 의 규칙).
* **갭(gap)**: 시계를 당겨 **벽시계에서 사라진** 구간. 그 안의 시각은 *missing*(PEP 495).\
  예: 뉴욕 2026-03-08 02:00\~02:59.
* **fold**: 시계를 되돌려 **같은 벽시계가 두 번** 오는 구간, 그리고 그 둘을 가르는 속성(0 = 앞, 1 = 뒤).\
  예: 뉴욕 2026-11-01 01:30.
* **벽시계 산술(wall-clock arithmetic)**: 오프셋 변화를 무시하고 표시된 숫자끼리 계산하는 것.\
  예: 같은 `tzinfo` 의 `+ timedelta`.
* **`timedelta`**: 두 순간 사이의 기간. days·seconds·microseconds 세 칸만 든다.\
  예: `timedelta(hours=-1)` 는 `days=-1, seconds=82800`.
* **IANA 키**: `Area/Location` 꼴의 시간대 이름.\
  예: `America/New_York` · `Asia/Seoul`.
* **tzdata**: 세계 시간대 규칙 자료(IANA). 운영체제 또는 같은 이름의 파이썬 패키지로 온다.\
  예: 이 머신의 판 `2026c`.
* **ISO 8601**: 날짜·시각 문자열 표준 형식.\
  예: `2026-03-08T12:00:00-04:00` — 오프셋은 있고 도시 이름은 없다.
* **`TZPATH`**: `zoneinfo` 가 시간대 파일을 찾는 디렉토리 목록. `PYTHONTZPATH` 로 바꾼다.\
  예: 빈 값을 주면 시스템 자료를 안 본다.

## 더 들어가면

* ★ **서드파티 둘 — 이 머신의 `python3` 에 `pytz`·`dateutil` 이 깔려 있어 한 번 던졌다**(표준 라이브러리 밖이라 본문의 근거로는 쓰지 않는다).

```python
# e49_thirdparty.py
from datetime import date, datetime

import dateutil
import pytz
from dateutil.relativedelta import relativedelta

print("[1] pytz, OLSON_VERSION, dateutil:", pytz.__version__, pytz.OLSON_VERSION, dateutil.__version__)
tz = pytz.timezone("America/New_York")
print("[2] datetime(..., tzinfo=pytz tz):", datetime(2026, 1, 15, 12, tzinfo=tz).strftime("%H:%M%z %Z"))
print("[3] tz.localize(naive)           :", tz.localize(datetime(2026, 1, 15, 12)).strftime("%H:%M%z %Z"))
print("[4] date(2026,1,31) + relativedelta(months=1):", date(2026, 1, 31) + relativedelta(months=1))
print("[5] date(2026,1,31) + relativedelta(months=2):", date(2026, 1, 31) + relativedelta(months=2))
```

```text
===== python3 - <e49_thirdparty.py =====
[1] pytz, OLSON_VERSION, dateutil: 2024.1 2026c 2.8.2
[2] datetime(..., tzinfo=pytz tz): 12:00-0456 LMT
[3] tz.localize(naive)           : 12:00-0500 EST
[4] date(2026,1,31) + relativedelta(months=1): 2026-02-28
[5] date(2026,1,31) + relativedelta(months=2): 2026-03-31
(exit 0)
```

  ★★ **`[2]` — `pytz` 시간대를 `tzinfo=` 로 바로 붙이면 `-0456 LMT`**(1883년 이전의 지방 평균시)가 나온다. `pytz` 는 **`localize` 를 거쳐야** `EST` 다(`[3]`). `zoneinfo` 는 `tzinfo=` 로 바로 붙인다 — 그 절차가 없어진 것이 `zoneinfo` 로 옮기는 까닭 하나다.
  ★ `[1]` 의 `OLSON_VERSION` 이 `2026c` — 이 머신의 `pytz` 는 **시스템 자료와 같은 판**을 본다(이 머신의 설치본에 대한 관찰 — `pytz` 판 `2024.1` 인데 자료 판은 `2026c` 다).
  ★ **`[4]`·`[5]` — 달 산술** — `relativedelta(months=1)` 는 1월 31일을 **2월 28일로 자른다.** 동작 6 에서 표준 라이브러리가 못 한 일이다.
* ★ **없는 시각 검사 관용구** — `d.astimezone(timezone.utc).astimezone(d.tzinfo).replace(tzinfo=None) != d.replace(tzinfo=None)` 가 동작 3 의 판정 그대로다. 되풀이 구간 검사는 `d.replace(fold=0).utcoffset() != d.replace(fold=1).utcoffset()`.
* ★ **단조 시계** — 경과 시간을 **재는** 일은 `datetime` 이 아니라 `time.monotonic()` 의 몫이다. 벽시계는 NTP·사람이 바꿀 수 있다. 이 문서는 그것을 재지 않았다.
* ★ **tzdata 판이 오르면 다시 돌릴 것** — 동작 8 의 첫 블록 전체, 그리고 동작 3·4·5 의 뉴욕 전이일(미국이 규칙을 바꾸면 움직인다 — ★ **예측이지 측정이 아니다**).
