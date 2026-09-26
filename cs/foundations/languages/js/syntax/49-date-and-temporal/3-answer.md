# js/syntax/49 — `Date` 와 Temporal: 「날짜만 쓰면 UTC, 시각을 쓰면 로컬 — 세 판은 한 글자도 같았지만 셋 다 V8 이다 · Temporal 은 Chrome 151 에만 제대로 있다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v18.19.1 · v20.19.6 · Google Chrome 151** · x86-64 Linux 에서 실제로 돌려 얻은 것이고, 블록은 **전부 캡처 파일에서 조립**했다. 모든 실행은 `TZ` 를 배너나 스크립트에 **명시**했다.
> ★★★ **세 판이 같았다는 것은 「V8 셋이 같았다」 이다** — 다른 엔진(SpiderMonkey · JavaScriptCore)은 이 머신에 없어 **못 쟀다**(9번).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js48b-49a-parse-cell.js` + `js48b-49a-parse-grid.sh`(1번 · 8번 · 9번) · `js48b-49b-iso-looking.js` + `js48b-49z-three-runtimes.sh`(2번 · 9번) · `js48b-49c-month-numbers.js`(3번) · `js48b-49d-shared-date.js`(4번 · 11번) · `js48b-49e-new-york-transitions.js`(5번 · 10번) · `js48b-49f-temporal-presence.js` + `.sh`(6번) · `js48b-49g-temporal-behaviour.js` + `js48b-49g-temporal-compare.sh`(7번 · 10번 · 11번).

## 정답

### 1. `"2026-09-26"` 만 세 `TZ` 모두 `+0h` · `T00:00`·슬래시·영문 월·한 자리 월 넷은 **`+0h` · `-9h` · `+4h`** · `"26/09/2026"` 은 세 칸 다 `Invalid Date` · **`4 / 6`**(세 판 다) · **`0 / 18`** ★★★

**출력**

```text
===== ./js48b-49a-parse-grid.sh (exit=0) =====
string              TZ=UTC                TZ=Asia/Seoul         TZ=America/New_York
"2026-09-26"        1790380800000 (+0h)   1790380800000 (+0h)   1790380800000 (+0h)
"2026-09-26T00:00"  1790380800000 (+0h)   1790348400000 (-9h)   1790395200000 (+4h)
"2026/09/26"        1790380800000 (+0h)   1790348400000 (-9h)   1790395200000 (+4h)
"Sep 26 2026"       1790380800000 (+0h)   1790348400000 (-9h)   1790395200000 (+4h)
"2026-9-26"         1790380800000 (+0h)   1790348400000 (-9h)   1790395200000 (+4h)
"26/09/2026"        Invalid Date          Invalid Date          Invalid Date

strings whose value changes with TZ: node18 4 / 6 · node20 4 / 6 · Chrome 4 / 6
cells (string x TZ) where the three runtimes differ: 0 / 18
```

**왜 그런가**

- ★★★ **ISO 형식의 날짜만(`YYYY-MM-DD`)은 UTC, 날짜-시각(`…T00:00`)은 로컬** — ECMA-262 가 그렇게 적었다(8번). 그래서 `"2026-09-26"` 만 `TZ` 를 안 탄다.
- ★★ `"2026/09/26"` · `"Sep 26 2026"` · `"2026-9-26"` 은 **ISO 형식이 아니다** — 명세는 이때 「**implementation-specific heuristics**」로 넘긴다. V8 은 셋을 **로컬 자정**으로 읽었다. `"26/09/2026"` 은 V8 의 휴리스틱도 못 읽었다.
- ★★★ `0 / 18` 은 **세 판이 같은 V8 계열**이라서다 — 9번.

### 2. `"2026-02-28"` → `2026-02-28T00:00Z` · `"2026-02-30"` → **`2026-03-02T00:00Z`** · `"2026-09-31"` → **`2026-10-01T00:00Z`** · `"2026-13-01"` → `Invalid Date` · `"2026-09-26T24:00Z"` → `2026-09-27T00:00Z` · `"2026-09-26 00:00"` → **`2026-09-25T15:00Z`**(로컬) · `"20260926"` → `Invalid Date` — 명세가 값을 정한 줄은 **`2026-02-28` 과 `T24:00Z` 둘뿐** ★★

**출력**

```text
===== ./js48b-49z-three-runtimes.sh Asia/Seoul js48b-49b-iso-looking.js (exit=0) =====
"2026-02-28"          2026-02-28T00:00:00.000Z
"2026-02-30"          2026-03-02T00:00:00.000Z
"2026-09-31"          2026-10-01T00:00:00.000Z
"2026-13-01"          Invalid Date
"2026-09-26T24:00Z"   2026-09-27T00:00:00.000Z
"2026-09-26 00:00"    2026-09-25T15:00:00.000Z
"20260926"            Invalid Date

node18 prints the same as node20: yes
Chrome 151 prints the same as node20: yes
```

- ★★ ECMA-262 은 「**out-of-bounds or nonconforming elements** 를 가진 문자열은 이 형식의 올바른 사례가 아니다」라고 적고, 그런 문자열에서는 `Date.parse` 가 **휴리스틱으로 넘어갈 수 있다**(may)고 적는다. 그래서 `02-30`·`09-31`·공백 판은 **V8 이 정한 값**이다 — `02-30` 을 `03-02` 로 **넘겨 받았고**, 공백 판은 `T` 판과 달리 **UTC 가 아니라 로컬**이 됐다.
- ★ `T24:00` 은 명세가 허용한다(「하루의 끝의 자정」 note) — 다음 날 `00:00` 과 같은 순간이다.
- ★ 세 판 모두 한 글자도 같았다(블록 끝 두 줄).

### 3. `2026-10-26` · `2026-09-26` · **`2026-03-03`** · `2027-01-01` · `2025-12-01` · `2025-12-31` · `2026-02-28` · **`1926-09-26`** · `getMonth()` **`8`** · `getDay()` `6` · `getYear()` **`126`** ★★

**출력**

```text
===== ./js48b-49z-three-runtimes.sh UTC js48b-49c-month-numbers.js (exit=0) =====
new Date(2026, 9, 26)         2026-10-26
new Date(2026, 8, 26)         2026-09-26
new Date(2026, 1, 31)         2026-03-03
new Date(2026, 12, 1)         2027-01-01
new Date(2026, -1, 1)         2025-12-01
new Date(2026, 0, 0)          2025-12-31
new Date(2026, 2, 0)          2026-02-28
new Date(26, 8, 26)           1926-09-26
getMonth() of 2026-09-26      8
getDay() of 2026-09-26        6
getYear() of 2026-09-26       126

node18 prints the same as node20: yes
Chrome 151 prints the same as node20: yes
```

**왜 그런가**

- ★★ 둘째 인자는 **0 기반 월**이라 `9` 는 10월이다. 넘치는 값은 **에러가 아니라 넘김**이다 — 명세 `MakeDay` 가 `ym = y + floor(m / 12)` · `mn = m modulo 12` 로 계산하고, 날짜는 **그 달 1일에 `dt - 1` 일을 더한다.** 그래서 2월 31일은 3월 3일, `0` 일은 전달 말일이다.
- ★ 연도 `26` 은 `MakeFullYear` 가 **0\~99 를 1900 년대**로 읽는다. `getYear()` 는 부록 B 의 옛 메서드로 `연도 - 1900` 이다.

### 4. `[1]` 둘 다 `2026-01-31` · `[2]` **둘 다 `2026-03-03`** · `[3]` **`opened` 도 `2026-03-03`**, `same object true` · `[4]` `opened 2026-03-03 · copy 2026-03-01` · `[5]` **`2000-09-26 · isFrozen true`** · `[6]` **`false · false · true · true`** ★★

**출력**

```text
===== ./js48b-49z-three-runtimes.sh UTC js48b-49d-shared-date.js (exit=0) =====
[1] start 2026-01-31 · due 2026-01-31
[2] after due.setMonth(...): start 2026-03-03 · due 2026-03-03 · setMonth returned 1772496000000
[3] after renewal = nextMonth(opened): opened 2026-03-03 · renewal 2026-03-03 · same object true
[4] after copy.setDate(1) on new Date(opened.getTime()): opened 2026-03-03 · copy 2026-03-01
[5] Object.freeze(date), then setFullYear(2000): 2000-09-26 · isFrozen true
[6] x == y false · x === y false · x <= y true · x.getTime() === y.getTime() true

node18 prints the same as node20: yes
Chrome 151 prints the same as node20: yes
```

**왜 그런가**

- ★★ `const due = start` 는 **같은 객체를 가리키는 이름 둘**이다(01번 — `Date` 는 객체). `setMonth` 는 그 객체의 `[[DateValue]]` 를 **바꾼다** — 명세 단계 「**Set dateObject.[[DateValue]] to u**」.
- ★★ 1월 31일에 `setMonth(1)` 은 **2월 31일 = 3월 3일**이 된다 — 3번의 넘침이 가변성과 겹친 것이다.
- ★ `new Date(d.getTime())` 이 복사다(`[4]`). `==`·`===` 는 **객체 동일성**이라 같은 순간이어도 `false`, `<=` 는 `valueOf` 로 숫자를 비교해 `true` 다.

### 5. `[1]` — `01:59` → `06:59Z`(그대로) · **`02:00` → `07:00Z` → `03:00`** · **`02:30` → `07:30Z` → `03:30`** · `02:59` → `07:59Z` → `03:59` · `03:00` → **`07:00Z`**(`02:00` 과 같은 순간) · 문자열 `02:30` → `07:30Z` → `03:30` · `[2]` `01:30` 은 **`-4h`** · `[3]` **다르다** — `+ 86400000 ms` 는 `13:00`, `setDate(+1)` 은 `12:00` ★★★

**출력**

```text
===== ./js48b-49z-three-runtimes.sh America/New_York js48b-49e-new-york-transitions.js (exit=0) =====
[1] 2026-03-08 (clocks go from 02:00 to 03:00)
  01:59                 2026-03-08T06:59Z   reads back 2026-03-08 01:59   offset -5h
  02:00                 2026-03-08T07:00Z   reads back 2026-03-08 03:00   offset -4h
  02:30                 2026-03-08T07:30Z   reads back 2026-03-08 03:30   offset -4h
  02:59                 2026-03-08T07:59Z   reads back 2026-03-08 03:59   offset -4h
  03:00                 2026-03-08T07:00Z   reads back 2026-03-08 03:00   offset -4h
  string 02:30          2026-03-08T07:30Z   reads back 2026-03-08 03:30   offset -4h
[2] 2026-11-01 (clocks go from 02:00 back to 01:00)
  00:59                 2026-11-01T04:59Z   reads back 2026-11-01 00:59   offset -4h
  01:00                 2026-11-01T05:00Z   reads back 2026-11-01 01:00   offset -4h
  01:30                 2026-11-01T05:30Z   reads back 2026-11-01 01:30   offset -4h
  02:00                 2026-11-01T07:00Z   reads back 2026-11-01 02:00   offset -5h
[3] 2026-03-07 12:00 plus 24 hours of milliseconds, and plus one day with setDate
  + 86400000 ms         2026-03-08T17:00Z   reads back 2026-03-08 13:00   offset -4h
  setDate(+1)           2026-03-08T16:00Z   reads back 2026-03-08 12:00   offset -4h

node18 prints the same as node20: yes
Chrome 151 prints the same as node20: yes
```

**왜 그런가**

- ★★★ **없는 시각은 전이 「앞」 오프셋(`-05:00`)으로 읽는다** — ECMA-262 2026 의 `UTC(t)` 단계 note 「**t is interpreted using the time zone offset before the transition**」과 예시 「2:30 AM … does not exist, but it must be interpreted as 2:30 AM UTC-05 (equivalent to 3:30 AM UTC-04)」 그대로다. 그래서 `02:30` 은 `07:30Z` 이고 읽어 오면 `03:30` 이다.
- ★★ **두 번 있는 시각도 「앞」 오프셋** — `01:30` 은 `-04:00`(서머타임 쪽, 먼저 오는 쪽). 같은 note 의 「1:30 AM … must be interpreted as 1:30 AM UTC-04」.
- ★★ `[3]` — 3월 8일은 **23시간짜리 날**이다. 밀리초로 24시간을 더하면 벽시계가 한 시간 밀리고, `setDate` 는 벽시계를 지킨다.
- ★ 세 판이 같았다 — 전이 시각 자체는 **tzdata** 가 정한다(node 18 은 2023c, node 20 은 2025b — 이 두 판에서 2026 뉴욕 규칙은 같았다).

### 6. node18 · node20 — **`typeof Temporal: undefined`**, `exit=0` · node18 `--harmony-temporal` — 객체는 있고 함수 열 개를 찍은 뒤 **`exit=133`**(`# Fatal error` · `# unimplemented code`) · node20 `--harmony-temporal` — 함수 열 개 · **`2026-10-26`** · `exit=0` · Chrome 151 — 함수 **여덟** 개 · `2026-10-26` · **`2 / 5`** ★★★

**출력**

```text
===== ./js48b-49f-temporal-presence.sh (exit=0) =====
--- node18 (exit=0)
  typeof Temporal: undefined
  reached the last line
--- node18 --harmony-temporal (exit=133)
  typeof Temporal: object
  own names: Calendar Duration Instant PlainDate PlainDateTime PlainMonthDay PlainTime PlainYearMonth TimeZone ZonedDateTime
  stderr # Fatal error in , line 0
  stderr # unimplemented code
--- node20 (exit=0)
  typeof Temporal: undefined
  reached the last line
--- node20 --harmony-temporal (exit=0)
  typeof Temporal: object
  own names: Calendar Duration Instant PlainDate PlainDateTime PlainMonthDay PlainTime PlainYearMonth TimeZone ZonedDateTime
  PlainDate.from('2026-09-26').add({ months: 1 }).toString(): 2026-10-26
  reached the last line
--- Chrome 151 (exit=0)
  typeof Temporal: object
  own names: Duration Instant PlainDate PlainDateTime PlainMonthDay PlainTime PlainYearMonth ZonedDateTime
  PlainDate.from('2026-09-26').add({ months: 1 }).toString(): 2026-10-26
  reached the last line

runs where the call on Temporal printed a value: 2 / 5
```

플래그가 무엇이라 적혀 있나 — `node --v8-options` 에서.

```text
===== ./js48b-49h-v8-flags.sh (exit=0) =====
--- node v18.19.1
  --trace-temporal (trace temporal code)
        type: bool  default: --notrace-temporal
--
  --harmony-temporal (enable "Temporal" (in progress))
        type: bool  default: --noharmony-temporal
--- node v20.19.6
  --trace-temporal (trace temporal code)
        type: bool  default: --no-trace-temporal
--
  --harmony-temporal (enable "Temporal" (in progress / experimental))
        type: bool  default: --no-harmony-temporal
(end)
```

**왜 그런가**

- ★★★ **기본 상태의 node 18 · 20 에는 Temporal 이 없다.** V8 플래그 `--harmony-temporal` 은 `node --v8-options` 가 「**in progress**」(node 20 은 「in progress / experimental」)로 적는 **개발 중 구현**이다 — node 18 판은 `toString` 한 번에 **엔진이 죽었다**(`exit=133`).
- ★★ 함수 목록도 다르다 — node 쪽 개발 중 구현은 **`Calendar`·`TimeZone`** 이 있고 Chrome 151 에는 없다. 개발 중 구현이 **옛 모양**을 들고 있는 것이다(이 문서는 그 이력의 원문은 확인하지 않았다).
- ★ 「플래그로 켜진다」는 **지원이 아니다** — 이 문서는 node 18 · 20 을 **Temporal 없음**으로 센다.

### 7. Chrome 151 — `[1]` **`9`** · `2026-09-26` · `[2]` 생성자 **`RangeError`** · `from` 은 **`2026-02-28`**(constrain) · `overflow: 'reject'` **`RangeError`** · 문자열 `'2026-02-31'` **`RangeError`** · `[3]` **`2026-02-28` · `jan31` 은 그대로 `2026-01-31`** · `reject` 는 `RangeError` · `setMonth` 없음 · **`isFrozen false`** · `[4]` 오프셋 없는 `Instant` **`RangeError`** · `1790380800000` · `2026-09-26T00:00:00` · `1790348400000` · `1790395200000` · `[5]` `compatible`·`later`·(없음) **`03:30-04:00`** · `earlier` **`01:30-05:00`** · `reject` `RangeError` · `[6]` **`<` 와 `'' +` 둘 다 `TypeError`** · `-1` · `true` · node20 플래그 판은 **`RangeError` 문구 여섯 줄만** 달랐다 — **`6 / 31`** ★★

**출력**

```text
===== ./js48b-49g-temporal-compare.sh (exit=0) =====
--- Chrome 151
[1] month numbers
new Temporal.PlainDate(2026, 9, 26).month                 9
new Temporal.PlainDate(2026, 9, 26).toString()            2026-09-26
[2] a day that does not exist
new Temporal.PlainDate(2026, 2, 31)                       RangeError 「Temporal error: Invalid ISO date.」
PlainDate.from({ year: 2026, month: 2, day: 31 })         2026-02-28
PlainDate.from({ ... }, { overflow: 'reject' })           RangeError 「Temporal error: day value is not in a valid range.」
PlainDate.from('2026-02-31')                              RangeError 「Temporal error: Parsed day value not in a valid range.」
[3] adding a month to January 31
jan31.add({ months: 1 })                                  2026-02-28
jan31 after that call                                     2026-01-31
jan31.add({ months: 1 }, { overflow: 'reject' })          RangeError 「Temporal error: not a valid ISO date.」
typeof jan31.setMonth                                     undefined
Object.isFrozen(jan31)                                    false
[4] the same string, with and without a time zone
Instant.from('2026-09-26T00:00')                          RangeError 「Temporal error: Required fields missing from Instant string.」
Instant.from('2026-09-26T00:00Z').epochMilliseconds       1790380800000
PlainDateTime.from('2026-09-26T00:00')                    2026-09-26T00:00:00
  .toZonedDateTime('Asia/Seoul').epochMilliseconds        1790348400000
  .toZonedDateTime('America/New_York').epochMilliseconds  1790395200000
[5] 2026-03-08 02:30 in America/New_York, four disambiguation values
  disambiguation: 'compatible'                            2026-03-08T03:30:00-04:00[America/New_York]
  disambiguation: 'earlier'                               2026-03-08T01:30:00-05:00[America/New_York]
  disambiguation: 'later'                                 2026-03-08T03:30:00-04:00[America/New_York]
  disambiguation: 'reject'                                RangeError 「Temporal error: Rejecting ambiguous time zones.」
  (no option)                                             2026-03-08T03:30:00-04:00[America/New_York]
[6] comparing two dates
d1 < d2                                                   TypeError 「Do not use Temporal.PlainDate.prototype.valueOf; use Temporal.PlainDate.prototype.compare for comparison.」
'' + d1                                                   TypeError 「Do not use Temporal.PlainDate.prototype.valueOf; use Temporal.PlainDate.prototype.compare for comparison.」
Temporal.PlainDate.compare(d1, d2)                        -1
d1.equals(Temporal.PlainDate.from('2026-09-26'))          true
--- node20 --harmony-temporal, lines that differ from Chrome
new Temporal.PlainDate(2026, 2, 31)                       RangeError 「Invalid time value for Temporal ../deps/v8/src/objects/js-temporal-objects.cc:664」
PlainDate.from({ ... }, { overflow: 'reject' })           RangeError 「Invalid time value for Temporal ../deps/v8/src/objects/js-temporal-objects.cc:9574」
PlainDate.from('2026-02-31')                              RangeError 「Invalid time value for Temporal ../deps/v8/src/objects/js-temporal-objects.cc:3518」
jan31.add({ months: 1 }, { overflow: 'reject' })          RangeError 「Invalid time value for Temporal ../deps/v8/src/objects/js-temporal-objects.cc:9574」
Instant.from('2026-09-26T00:00')                          RangeError 「Invalid time value for Temporal ../deps/v8/src/objects/js-temporal-objects.cc:3644」
  disambiguation: 'reject'                                RangeError 「Invalid time value for Temporal ../deps/v8/src/objects/js-temporal-objects.cc:1801」

lines where node20 --harmony-temporal differs from Chrome 151: 6 / 31
```

**왜 그런가**

- ★★ **월은 1 기반**(`month` 가 `9`) · **넘침은 기본이 `constrain`(말일로 깎기), `reject` 로 바꾸면 던진다** · 생성자와 문자열은 **처음부터 거절**한다. `Date` 의 「조용히 넘긴다」(3번)와 정반대다.
- ★★ **`add` 는 새 객체를 돌려주고 원본은 그대로**다 — 1월 31일 + 1개월이 **2월 28일**(Date 는 3월 3일 — 4번).
- ★★ **시간대가 없으면 순간이 안 된다** — `Instant.from('…T00:00')` 이 던지고, 벽시계(`PlainDateTime`)를 순간으로 바꾸려면 **시간대를 이름으로** 줘야 한다. 그 결과는 1번 격자의 `-9h`·`+4h` 칸과 같은 수다.
- ★★ `[6]` — `valueOf` 가 **일부러 던진다**(문구가 `compare` 를 쓰라고 한다). `Date` 처럼 `<` 로 비교하던 코드가 **조용히 틀리지 않고 멈춘다.**
- ★ node20 플래그 판과 **갈린 여섯 줄은 전부 `RangeError` 의 문구**다 — 값은 한 줄도 안 갈렸다 — 문구에 V8 소스 파일 이름과 줄 번호가 박혀 있다(개발 중 구현).

### 8. 「**When the UTC offset representation is absent, date-only forms are interpreted as a UTC time and date-time forms are interpreted as a local time.**」 ★★

- ★★ 오프셋이 없을 때 **날짜만 쓴 꼴은 UTC, 시각까지 쓴 꼴은 로컬** — 그래서 같은 「그날 자정」이 서울에서는 `-9h` 로 갈린다. 둘 다 **ISO 형식 안의 규칙**이라 명세 보장이다(2번의 휴리스틱과 다르다).

### 9. **답할 수 없다** — 세 판이 **모두 V8** 이라 「엔진마다 다른 휴리스틱」이 원리상 안 보인다 · 대신 **명세 문장**(ISO 형식 밖은 implementation-specific)과 **ISO 처럼 생긴 규격 밖 문자열을 V8 이 어떻게 받나**(2번)로 물었다 ★★★

- ★★★ `0 / 18` 은 「V8 10.2 · 11.3 · Chrome 151 이 같다」까지다. 다른 엔진은 이 머신에 없어 **못 쟀다** — 그래서 2번의 `02-30 → 03-02` 같은 값은 **다른 엔진에서 `Invalid Date` 여도 명세 위반이 아니다**(명세가 may 로 열어 둔 자리). 이 문장은 명세에서 끌어낸 것이지 다른 엔진을 돌려 본 것이 아니다.
- ★ 이것이 머리말의 「창을 바꿔 물었다」(제5의 상태)다 — 바꾼 창은 **다른 엔진의 실제 답**을 못 본다.

### 10. Python `02:30;0` — **`-0500` · UTC `07:30` · 돌아오면 `03:30 EDT`** · `Date` 도 **`07:30Z` → `03:30`** · Temporal `(no option)` 도 **`03:30-04:00`** — 세 답이 같다 · 경로 — **파이썬은 값을 그대로 두고 UTC 로 갈 때** 드러나고, **`Date` 는 만드는 순간** 순간값으로 굳고, **Temporal 은 선택지(`disambiguation`)로 드러내 놓고 고르게** 한다 ★★

- ★★ 파이썬 `fold=0` 은 「전이 앞 규칙」(PEP 495), `Date` 는 명세 `UTC(t)` 의 「전이 앞 오프셋」, Temporal 의 기본 `compatible` 은 갭에서 `later` 와 같은 답을 냈다(7번 `[5]`) — 셋이 **같은 벽시계**(`03:30`)에 떨어진다.
- ★ Temporal 만 **`reject` 로 「없는 시각이다」를 에러로 받을 수 있다.** 파이썬은 그 칸에서 **아무 말도 안 했다**(Python 49 의 제5의 상태) — `Date` 도 그렇다(5번).

### 11. `Object.freeze` 는 **속성**을 얼린다 — `Date` 의 값은 속성이 아니라 **내부 슬롯 `[[DateValue]]`** 라 `setFullYear` 가 그대로 바꿨다 · Temporal 은 **`isFrozen false` 인데도 원본이 안 바뀐다** — 불변은 동결이 아니라 **바꾸는 메서드가 아예 없는 것**(`setMonth` 없음 · `add`/`with` 는 새 객체)에서 온다 ★★

- ★ [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md)(동결은 얕다)과 같은 집안이지만 층이 다르다 — 동결이 못 닿는 곳이 **중첩 객체**가 아니라 **내부 슬롯**이다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js48b-49a-parse-cell.js` + `js48b-49a-parse-grid.sh` | ★★★ 6 문자열 × 3 `TZ` × 3 판 = 54 실행 · 「`4 / 6`」 · 「`0 / 18`」 | node18 · node20 · Chrome 151 |
| `js48b-49b-iso-looking.js` | ★★ 규격 밖 문자열을 V8 이 받는 법 | 세 판(같음) · `TZ=Asia/Seoul` |
| `js48b-49c-month-numbers.js` | ★★ 0 기반 월 · 넘침 · 두 자리 연도 | 세 판(같음) · `TZ=UTC` |
| `js48b-49d-shared-date.js` | ★★ 가변성 · 동결 · 비교 | 세 판(같음) · `TZ=UTC` |
| `js48b-49e-new-york-transitions.js` | ★★★ 갭 · fold · 23시간짜리 날 | 세 판(같음) · `TZ=America/New_York` |
| `js48b-49f-temporal-presence.js` + `.sh` | ★★★ Temporal 판별 — 「`2 / 5`」 · node18 플래그의 `exit=133` | node18 · node20 각각 플래그 유무 · Chrome 151 |
| `js48b-49g-temporal-behaviour.js` + `js48b-49g-temporal-compare.sh` | ★★ Temporal 의 월 · 넘침 · 불변 · 시간대 · 비교 · 「`6 / 31`」 | Chrome 151 · node20 `--harmony-temporal` |
| `js48b-49h-v8-flags.sh` | ★ 플래그 설명 문자열(`in progress`) | node18 · node20 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — ★★★ **1번의 휴리스틱 행 넷과 `Invalid Date` 행 · 2번의 규격 밖 다섯 줄**(엔진이 정한다) · **5번의 전이 시각**(tzdata 판 — 규칙이 바뀌면 칸이 움직인다) · **6번 전체**(node 가 Temporal 을 싣는 판이 오면 바뀐다) · 7번의 예외 **문구**. 명세 보장 칸(1번의 `"2026-09-26"`·`T00:00` 행 · 3번 · 4번 · 5번의 「전이 앞 오프셋」 규칙)은 판이 올라도 같아야 한다.
