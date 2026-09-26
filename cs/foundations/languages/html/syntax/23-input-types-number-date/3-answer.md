# html/syntax/23 — `<input>` 타입 지도 ② 숫자·날짜: `number`/`range`/`date`/`time`/`datetime-local`/`month`/`week` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [21번 주제](../21-form-submission-model/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「The input element」 절로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ⑤ 다** — 「로케일 무관」은 서버가 받은 글자로만 증명된다(A2).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `--lang` 은 아무것도 안 바꾸고, `LANGUAGE` 는 셋 다 바꾼다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --lang=de-DE --dump-dom html21b-23-lang.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
navigator.language = ko-KR
validationMessage = 이메일 주소에 '@'를 포함해 주세요. 'a'에 '@'가 없습니다.
(1234.5).toLocaleString() = 1,234.5
(exit 0)
```

```text
$ LANGUAGE=de_DE google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html21b-23-lang.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
navigator.language = de-DE
validationMessage = Die E-Mail-Adresse muss ein @-Zeichen enthalten. In der Angabe "a" fehlt ein @-Zeichen.
(1234.5).toLocaleString() = 1.234,5
(exit 0)
```

**왜 그런가**

- ★★ **플래그 판은 세 줄 다 ko-KR** — `navigator.language = ko-KR`, 한국어 문구, `1,234.5`. **환경 변수 판은 셋 다 de-DE** 다. 이 판의 리눅스 Chrome 은 **로케일을 `LANGUAGE` 에서 읽었다**(구현의 관찰 — 이유는 확인하지 않았다).
- 그래서 이 배치의 하네스는 `--lang=xx-YY` 를 받아 **`LANGUAGE=xx_YY` 로 바꿔** 브라우저를 띄운다.

### 2. 서버 값은 1 / 9 칸만 갈린다 — 그 한 칸이 사람이 친 `1,5` 다 · 화면은 7 / 9 가 갈린다

**출력**

```text
$ python3 html21b-form.py 로케일 html21b-23-locale.html ko-KR de-DE
[ko-KR]  navigator.language = ko-KR · 요청 1번
  Accept-Language  ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7
  본문  「d=2026-09-26&t=13%3A05&dt=2026-09-26T13%3A05&m=2026-09&w=2026-W39&n=1234.5&r=50&k1=15&k2=1.5」
[de-DE]  navigator.language = de-DE · 요청 1번
  Accept-Language  de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7
  본문  「d=2026-09-26&t=13%3A05&dt=2026-09-26T13%3A05&m=2026-09&w=2026-W39&n=1234.5&r=50&k1=1.5&k2=1.5」

칸   화면(ko-KR)               화면(de-DE)               서버(ko-KR)         서버(de-DE)
d    "2026. 09. 26."           "26.09.2026"              "2026-09-26"        "2026-09-26"
t    "오후 01:05"              "13:05"                   "13:05"             "13:05"
dt   "2026. 09. 26. 오후 01:05" "26.09.2026, 13:05"       "2026-09-26T13:05"  "2026-09-26T13:05"
m    "2026년 9월"              "September 2026"          "2026-09"           "2026-09"
w    "2026, 39번째 주"         "Woche 39, 2026"          "2026-W39"          "2026-W39"
n    "1234.5"                  "1234,5"                  "1234.5"            "1234.5"
r    ""                        ""                        "50"                "50"
k1   "15"                      "1,5"                     "15"                "1.5"
k2   "1.5"                     "1.5"                     "1.5"               "1.5"
화면 글자가 갈린 칸 = 7 / 9
서버 값이 갈린 칸 = 1 / 9
(exit 0)
```

**왜 그런가**

- ★★★ **날짜·시각·날짜와 시각·달·주·수·범위 일곱 칸의 서버 값이 두 로케일에서 같다** — `2026-09-26` · `13:05` · `2026-09-26T13:05` · `2026-09` · `2026-W39` · `1234.5` · `50`. 화면은 `2026. 09. 26.` 대 `26.09.2026`, `오후 01:05` 대 `13:05`, `2026년 9월` 대 `September 2026`, `2026, 39번째 주` 대 `Woche 39, 2026`, `1234.5` 대 `1234,5`.
- ★★★ **`k1`(친 글자 `1,5`)이 ko-KR 에서 `15`, de-DE 에서 `1.5`** — 서버 값이 갈린 **유일한** 칸이다. `k2`(`1.5`)는 둘 다 `1.5`.
- **`Accept-Language`** — `ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7` 대 `de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7`.

### 3. 틀린 날짜와 전화번호는 빈 문자열 · `valueAsNumber` 의 단위는 타입마다 · `number` 에 `valueAsDate` 를 쓰면 `InvalidStateError`

**출력**

```text
$ python3 html21b-form.py --lang=ko-KR page html21b-23-values.html
id   value 속성        .value                valueAsNumber   valueAsDate
d1   "2026-09-26"      "2026-09-26"          1790380800000   2026-09-26T00:00:00.000Z
d2   "2026-02-30"      ""                    NaN             null
d3   "26.09.2026"      ""                    NaN             null
t1   "13:05:30.5"      "13:05:30.5"          47130500        1970-01-01T13:05:30.500Z
dt1  "2026-09-26 13:05" "2026-09-26T13:05"    1790427900000   null
m1   "2026-09"         "2026-09"             680             2026-09-01T00:00:00.000Z
w1   "2026-W53"        "2026-W53"            1798416000000   2026-12-28T00:00:00.000Z
w2   "2026-W39"        "2026-W39"            1789948800000   2026-09-21T00:00:00.000Z
n1   "010-1234-5678"   ""                    NaN             null
n2   "01012345678"     "01012345678"         1012345678      null
n3   "1e3"             "1e3"                 1000            null
n4   " 12 "            ""                    NaN             null
속성 값이 있는데 .value 가 빈 문자열이 된 칸 = d2 · d3 · n1 · n4 → 4 / 12

n1 에 스크립트로 넣기
  n1.value = "010-1234" 뒤 .value = ""
  n1.valueAsNumber = 101234 뒤 .value = "101234"
  n1.valueAsDate = new Date(0) → InvalidStateError 「Failed to set the 'valueAsDate' property on 'HTMLInputElement': This input element does not support Date values.」

time 요소 datetime="2026-02-30" → .dateTime = "2026-02-30"
date 입력 value="2026-02-30" → .value = ""
(exit 0)
```

**왜 그런가**

- ★★★ **빈 문자열이 된 칸 = `d2`(`2026-02-30`) · `d3`(`26.09.2026`) · `n1`(`010-1234-5678`) · `n4`(`" 12 "`)** — 넷 다 그 타입의 「유효한 문자열」이 아니라 **정화에서 비워졌다.** `n2`(`01012345678`)는 글자가 남지만 `valueAsNumber` 는 `1012345678`(앞의 0 없음).
- **`valueAsNumber`** — `date`·`week`·`datetime-local` 은 1970 UTC 부터 밀리초, `time` 은 자정부터 밀리초(`47130500`), `month` 는 달 수(`680`). **`valueAsDate`** — `datetime-local`·`number` 는 `null`.
- ★★ **`n1.valueAsDate = new Date(0)`** → `InvalidStateError 「Failed to set the 'valueAsDate' property on 'HTMLInputElement': This input element does not support Date values.」` — 명세의 「적용 안 되는 상태에서 설정하면 `InvalidStateError`」 그대로다(문구는 구현).
- ★★★ **`time` 요소의 `.dateTime` 은 `"2026-02-30"` 그대로, `d2` 의 `.value` 는 `""`** — 앞엣것은 **해석하지 않는 반영**([14번](../14-quotation-edits-and-time/3-answer.md)), 뒤엣것은 **정화가 있는 입력**이다.

### 4. `010-1234` 는 값이 없고, `0101234` 는 화살표 한 번에 `101235`

**출력**

```text
$ python3 html21b-form.py 시도 html21b-23-phone.html
[입력만 하고 읽기]
  페이지  (기록 없음)
  뒤      n1 .value="" badInput=true valueAsNumber=NaN · n2 .value="0101234" badInput=false valueAsNumber=101234 · t1 .value="010-1234" badInput=false valueAsNumber=NaN · t2 .value="0101234" badInput=false valueAsNumber=NaN
  서버    (받은 요청 없음)
[입력하고 보내기]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「n1=&n2=0101234&t1=010-1234&t2=0101234」
          필드  n1=「」 · n2=「0101234」 · t1=「010-1234」 · t2=「0101234」
[n2·t2 에서 위쪽 화살표 한 번]
  페이지  (기록 없음)
  뒤      n1 .value="" badInput=true valueAsNumber=NaN · n2 .value="101235" badInput=false valueAsNumber=101235 · t1 .value="010-1234" badInput=false valueAsNumber=NaN · t2 .value="0101234" badInput=false valueAsNumber=NaN
  서버    (받은 요청 없음)
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`n1`(`010-1234`) — `.value=""` · `badInput=true` · `NaN`**, 서버에는 **`n1=「」`**. 칸에는 친 글자가 보이는데 **값으로 못 바꿨다.**
- ★★★ **`n2`(`0101234`) — `.value="0101234"` · `valueAsNumber=101234`**, 서버에는 `0101234`. 그런데 **위 화살표 뒤 `"101235"`** — 스핀 단추가 **수로 더해** 앞의 0 을 잃었다.
- **`tel` 두 칸은 친 글자 그대로**이고 화살표로 **안 바뀐다.**

### 5. `range` 는 50·5·2·50·50·100·10 — 깃발은 `number`·`date`·`time` 쪽에만 켜진다 · `value` 속성이 눈금의 출발점이 된다

**출력**

```text
$ python3 html21b-form.py --lang=ko-KR page html21b-23-range.html
id  속성                                                .value        켜진 validity 깃발
r1  type="range"                                        "50"          (없음)
r2  type="range" min="0" max="10"                       "5"           (없음)
r3  type="range" min="0" max="5" step="2"               "2"           (없음)
r4  type="range" value=""                               "50"          (없음)
r5  type="range" value="abc"                            "50"          (없음)
r6  type="range" value="200"                            "100"         (없음)
r7  type="range" min="10" max="0"                       "10"          (없음)
a1  type="number" min="0" max="10" value="11"           "11"          rangeOverflow
a2  type="number" step="0.5" value="1.3"                "1.3"         (없음)
a2s type="number" step="0.5"                            "1.3"         stepMismatch
a3  type="number" value="1.5"                           "1.5"         (없음)
a4  type="date" min="2026-01-01" value="2025-12-31"     "2025-12-31"  rangeUnderflow
a5  type="date" step="7" min="2026-09-07" value="2026-09-10" "2026-09-10"  stepMismatch
a6  type="time" step="900" value="13:07"                "13:07"       (없음)
a6s type="time" step="900"                              "13:07"       stepMismatch

validationMessage 전문 (비어 있지 않은 것만)
  a1  값은 10 이하여야 합니다.
  a2s  유효한 값을 입력해 주세요. 가장 근접한 유효 값 2개는 1 및 1.5입니다.
  a4  값은 2026. 01. 01. 이후여야 합니다.
  a5  유효한 값을 입력해 주세요. 가장 근접한 유효 값 2개는 2026. 09. 07. 및 2026. 09. 14.입니다.
  a6s  유효한 값을 입력해 주세요. 가장 근접한 유효 값 2개는 오후 1:00 및 오후 1:15입니다.

a2 와 a2s · a6 와 a6s 는 값이 같다 — 차이는 속성으로 넣었나 스크립트로 넣었나
  a2 stepMismatch = false · a2s stepMismatch = true
  a6 stepMismatch = false · a6s stepMismatch = true

range 에서 .value 가 빈 문자열인 칸 = 0 / 7
(exit 0)
```

**왜 그런가**

- ★★★ **`range` 일곱 칸 = `50` · `5` · `2` · `50` · `50` · `100` · `10`** — 빈 값 **0 / 7**, 깃발도 **전부 없음.** 기본은 **최솟값 + 절반**, 눈금이 비껴가면 가까운 눈금, 넘치면 **최댓값**, `max < min` 이면 **최솟값**.
- **켜진 깃발** — `a1` `rangeOverflow`(값은 `11` 그대로) · `a2s` `stepMismatch` · `a4` `rangeUnderflow` · `a5` `stepMismatch` · `a6s` `stepMismatch`. **`a2`·`a3`·`a6` 은 없음.**
- ★★★ **`a2`(속성 `1.3`)와 `a2s`(스크립트 `1.3`)는 값이 같은데 깃발이 갈렸다** — `a6`/`a6s` 도 같다. 가른 것은 경로가 아니라 **step base**(`min` → `value` 속성 → 기본 기준 → 0)다 — `a2`·`a6` 은 `value` 속성이 출발점이라 눈금 위, `a2s`·`a6s` 는 출발점 0 이라 눈금 밖. **명세대로의 동작**이다(A9 · [28번](../28-validation-attributes/2-summary.md)의 (2)). `a3`(`step` 없음 = 기본 1, 값 `1.5`)도 같은 이유로 깃발이 없다 — `value="1.5"` 가 출발점이다(스크립트 판은 던지지 않았다).

### 6. 「표시 형식은 제출 형식과 독립」 — 입력 해석까지 무관하게 만들지는 않는다 · 근거는 `k1`

- 명세(비규범) — 「날짜·시간·숫자 칸에서 **사용자에게 보여 주는 형식은 폼 제출에 쓰이는 형식과 독립**이다. 브라우저는 입력 요소의 **언어**나 사용자의 **선호 로케일** 관례를 따르는 UI 를 쓰라고 권한다」.
- ★★★ **입력 해석은 무관하지 않다** — A2 의 **`k1`** 이 근거다. 같은 키 `1,5` 가 ko-KR 에서 `15`, de-DE 에서 `1.5` 로 **제출 값이 갈렸다.** 「로케일 무관」은 **값이 적히는 꼴**(점 소수·ISO 날짜)에 대한 약속이다.

### 7. 「수가 아닌 숫자열」 — 카드 번호·우편번호 · 기준은 「스핀 박스가 말이 되나」 · 대안은 `text` + `inputmode`·`pattern`

- 명세 — 「`type=number` 는 **숫자로만 이루어졌지만 엄밀히 말해 수가 아닌** 입력에 알맞지 않다. 예컨대 **신용카드 번호나 미국 우편번호**」. 판단 기준 — 「입력 칸에 **스핀 박스(위아래 화살표)** 가 말이 되는가」. 카드 번호를 1 틀리는 것은 사소한 실수가 아니다.
- 대안 — 「**`type=text`** 가 아마 맞다(필요하면 **`inputmode`** 나 **`pattern`** 과 함께)」. A4 의 `101235` 가 그 기준이 틀린 칸에서 무슨 일이 나는지 보인다.

### 8. 기본값은 가운데 · 넘치면 최댓값으로 「바꿔야 한다」 — `number` 는 깃발만 켠다

- 명세 — `range` 의 기본값은 「**최솟값 + (최댓값 − 최솟값)의 절반**, 최댓값이 최솟값보다 작으면 최솟값」, 값이 유효한 수가 아니면 **기본값으로 정화**. 넘치면 「UA 는 값을 **최댓값을 나타내는 수로 바꿔야 한다**」, 모자라면 최솟값으로.
- **`number`** 는 값을 바꾸지 않고 **`rangeOverflow` 깃발**만 켠다(A5 의 `a1` — `11` 그대로). 제출 때 검증이 막는다 — `novalidate` 면 그대로 간다.

### 9. 명세와 갈린 자리는 없다 — `stepMismatch` 의 「속성 대 스크립트」는 step base 로 설명된다 · 화면 형식은 사용자 로케일을 따랐고 그것은 구현의 선택이다

- ★★★ **갈린 자리는 없다** — A5 의 `a2`/`a2s`·`a6`/`a6s` 는 경로 때문이 아니다. 명세의 step mismatch 줄 — 「허용 눈금이 있고, 값을 수로 바꾼 것이 **step base 에서** 정수배가 아니면 step mismatch」 — 에는 값의 출처 조건이 없고, **step base 가 `min` → `value` 속성 → 기본 기준 → 0** 이라 `value` 속성으로 준 값은 `min` 이 없으면 자기 자신이 출발점이다. `date` 의 `a5` 는 `min` 이 출발점이라 켜졌다. 경로를 바꿔 다시 잰 격자는 [28번](../28-validation-attributes/2-summary.md)의 (2).
- **화면 형식** — 페이지가 `lang="ko"` 인데 de-DE 판이 독일식이었다 → **사용자 로케일을 따랐다**(A2). 명세는 「입력 요소의 언어 **또는** 사용자 선호 로케일」을 **권할 뿐**(비규범)이므로 **어느 쪽을 고르나는 구현**이다.

### 10. 접근성 트리의 글자로 물었다(제5의 상태) — 모양·색은 못 본다 · 선택 창과 휠은 페이지 밖 UI 다

- 날짜 칸의 화면 글자는 UA 의 그림자 트리 안에 있어 DOM 으로 안 닿는다. CDP 트리의 **`spinbutton` 과 `StaticText` 를 순서대로 이어** 물었다 — **제5의 상태**(같은 질문을 다른 창으로). ★ 그 창이 못 보는 것 — **글꼴·자리 배치·색**, 트리에 없는 **그림 요소**.
- **달력 선택 창** — 트리에는 「날짜 선택도구 표시」 **단추**까지만 있고 창은 **페이지 밖 UI** 다. **모바일 날짜 휠** — 입력기가 이 환경에 없다. 둘 다 **「못 잰 것」**(제3의 상태)이다.

### 11. 정본 경계

- **`time` 요소의 `datetime`** — [14번 주제](../14-quotation-edits-and-time/2-summary.md). 여기서는 **같은 `2026-02-30` 을 `input type=date` 가 빈 문자열로 정화한다**는 것과 대비했다(A3).
- **`min`/`max`/`step` 의 눈금 규칙** — [28번 주제](../28-validation-attributes/2-summary.md). 여기는 그 깃발과 문구가 어떻게 보이나까지.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 하네스는 [21번](../21-form-submission-model/3-answer.md)의 `html21b-form.py`·`html21b-cdp.py` 그대로다.

**로케일** — ★★ **브리핑의 계획(`--lang=ko-KR` 대 `--lang=de-DE`)은 이 환경에서 성립하지 않았다** — A1 의 두 블록. 하네스는 `--lang=xx-YY` 를 받아 **환경 변수 `LANGUAGE=xx_YY`** 로 바꿔 넘긴다. `로케일` 모드는 **로케일마다 브라우저와 서버를 새로 띄운다**(한 프로세스 안에서 로케일이 섞이지 않게).
**화면 글자** — `로케일` 모드의 `화면글자()` 가 CDP `Accessibility.getFullAXTree` 에서 그 입력의 자손 `StaticText` 를 트리 순서로 잇고 **`button` 아래는 뺀다**(선택도구 단추).

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌렸다. 이 주제의 블록은 **세 판이 한 글자도 같았다.** `valueAsDate` 는 `toISOString()`(UTC)으로 찍어 **기계의 시간대에 안 탄다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`--lang` 플래그 대 `LANGUAGE`** | 3 | 동작 방식 (1) · A1 |
| **두 로케일 × 아홉 칸 × 화면·서버** | 3 | 동작 방식 (1) · A2 |
| **날짜 칸의 트리** | 3 | 동작 방식 (1) |
| **열두 칸의 `.value`·`valueAs*`** | 3 | 동작 방식 (2) · A3 |
| **`number`·`tel` 에 친 전화번호 · 화살표** | 3 | 동작 방식 (3) · A4 |
| **`range` 일곱 칸 + 깃발 여덟 칸** | 3 | 동작 방식 (4) · A5 |
| **demo 검증** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `min` 없이 `value` 속성으로 넣은 `number`·`time` 값의 `stepMismatch` | **꺼져 있다** | 명세대로(step base = `value` 속성) — 판이 올라도 같아야 한다 · [28번](../28-validation-attributes/2-summary.md)의 (2) |
| ko-KR 에서 친 `1,5` | `15` | 입력 해석은 구현이다 |
| 화면 형식의 기준 | 사용자 로케일 | 명세는 권고만 |
| 리눅스 Chrome 의 로케일 원천 | `LANGUAGE` | 플래그가 안 먹는다 |
| 날짜 칸의 트리 역할 이름 | `Date`·`InputTime`·`DateTime` | HTML-AAM 은 대응 역할 없음 |

**안 돌려 본 것** — ① **달력 선택 창을 여는 것**(단추 클릭). ② **ko-KR·de-DE 밖의 로케일.** ③ **날짜 칸에 키로 한 칸씩 치는 것**(값은 속성으로 넣었다). ④ **`step="any"` 밖의 `number` 에 친 소수** — (1) 의 `k1`·`k2` 는 `step="any"` 다.

**못 잰 것** — ① **달력·시각 선택 창의 모양.** ② **모바일 날짜 휠·숫자 자판.** ③ **스크린리더의 날짜 칸 읽기.**

**부적용인 창** — **창 ③ · ④ · ⑥.** — **잴 것이 없다.**

## 용어 풀이

- **표시 형식 / 제출 형식** — 사람에게 보이는 꼴 / `.value` 와 서버가 받는 꼴. 명세가 둘을 독립으로 둔다.
- **입력 해석** — 사람이 친 글자를 값으로 바꾸는 것. 로케일을 탄다.
- **`badInput`** — 보이는 글자를 값으로 못 바꿀 때 참.
- **스핀 박스** — 위아래 화살표. 값을 수로 다룬다.
- **`LANGUAGE`** — 리눅스 프로그램이 읽는 선호 언어 환경 변수. 이 판의 Chrome 은 여기서 로케일을 골랐다.
