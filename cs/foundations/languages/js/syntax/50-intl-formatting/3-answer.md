# js/syntax/50 — `Intl` 국제화 포맷: 「42칸 중 3칸이 갈렸고 node 두 판은 한 칸도 안 갈렸다 — 그리고 node 의 `formatRange` 는 눈에 안 보이는 U+202F 를 넣었다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6 · v18.19.1 · Google Chrome 151** · x86-64 Linux 에서 실제로 돌려 얻은 것이고, 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **출력의 글자는 전부 로케일 데이터 판에 묶여 있다** — 이 판들에서 재실행하면 한 글자도 같았지만, ICU·CLDR 이 오르면 바뀔 수 있는 칸이다(7번).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js48b-50a-locale-data.js` + `.sh`(1번) · `js48b-50b-format-cells.js` + `js48b-50b-format-grid.sh`(2번 · 7번 · 9번) · `js48b-50c-lookalike-space.js`(3번 · 8번 · 10번) · `js48b-50d-hand-format.js`(4번) · `js48b-50e-default-locale.js` + `.sh`(5번 · 11번) · `js48b-50f-rejected-options.js`(6번).

## 정답

### 1. `[2]` 두 줄 다 **`zz-ZZ` 를 뺀 일곱**(세 판 같음) · `zz-ZZ` → **`en-US`** · `de-ZZ` → **`de`** · `x-nope` → **`RangeError`** · `[4]` 가 **`1.234,5`** 라 **full-icu**(세 판 다) ★★

**출력**

```text
===== ./js48b-50a-locale-data.sh (exit=0) =====
--- node18
[1] build
  process.versions.icu                          74.2
  typeof Intl.DurationFormat                    undefined
[2] supportedLocalesOf -- which of these has data?
  DateTimeFormat                                ko-KR de-DE sv-SE fr-FR en-IN ja-JP ar-EG
  NumberFormat                                  ko-KR de-DE sv-SE fr-FR en-IN ja-JP ar-EG
[3] the locale actually used -- resolvedOptions().locale
  new Intl.NumberFormat("ko-KR")                ko-KR
  new Intl.NumberFormat("de-DE")                de-DE
  new Intl.NumberFormat("sv")                   sv
  new Intl.NumberFormat("en-IN")                en-IN
  new Intl.NumberFormat("zz-ZZ")                en-US
  new Intl.NumberFormat("de-ZZ")                de
  new Intl.NumberFormat("x-nope")               RangeError 「Incorrect locale information provided」
  new Intl.NumberFormat()   (no argument)       en-US
  new Intl.DateTimeFormat().timeZone            UTC
[4] one German number -- data present or English fallback?
  new Intl.NumberFormat("de-DE").format(1234.5) 1.234,5
  (1234.5).toLocaleString()   (no argument)     1,234.5
--- node20
[1] build
  process.versions.icu                          77.1
  typeof Intl.DurationFormat                    undefined
[2] supportedLocalesOf -- which of these has data?
  DateTimeFormat                                ko-KR de-DE sv-SE fr-FR en-IN ja-JP ar-EG
  NumberFormat                                  ko-KR de-DE sv-SE fr-FR en-IN ja-JP ar-EG
[3] the locale actually used -- resolvedOptions().locale
  new Intl.NumberFormat("ko-KR")                ko-KR
  new Intl.NumberFormat("de-DE")                de-DE
  new Intl.NumberFormat("sv")                   sv
  new Intl.NumberFormat("en-IN")                en-IN
  new Intl.NumberFormat("zz-ZZ")                en-US
  new Intl.NumberFormat("de-ZZ")                de
  new Intl.NumberFormat("x-nope")               RangeError 「Incorrect locale information provided」
  new Intl.NumberFormat()   (no argument)       en-US
  new Intl.DateTimeFormat().timeZone            UTC
[4] one German number -- data present or English fallback?
  new Intl.NumberFormat("de-DE").format(1234.5) 1.234,5
  (1234.5).toLocaleString()   (no argument)     1,234.5
--- Chrome 151
[1] build
  process.versions.icu                          (no process object)
  typeof Intl.DurationFormat                    function
[2] supportedLocalesOf -- which of these has data?
  DateTimeFormat                                ko-KR de-DE sv-SE fr-FR en-IN ja-JP ar-EG
  NumberFormat                                  ko-KR de-DE sv-SE fr-FR en-IN ja-JP ar-EG
[3] the locale actually used -- resolvedOptions().locale
  new Intl.NumberFormat("ko-KR")                ko-KR
  new Intl.NumberFormat("de-DE")                de-DE
  new Intl.NumberFormat("sv")                   sv
  new Intl.NumberFormat("en-IN")                en-IN
  new Intl.NumberFormat("zz-ZZ")                en-US
  new Intl.NumberFormat("de-ZZ")                de
  new Intl.NumberFormat("x-nope")               RangeError 「Invalid language tag: x-nope」
  new Intl.NumberFormat()   (no argument)       en-US
  new Intl.DateTimeFormat().timeZone            UTC
[4] one German number -- data present or English fallback?
  new Intl.NumberFormat("de-DE").format(1234.5) 1.234,5
  (1234.5).toLocaleString()   (no argument)     1,234.5
```

**왜 그런가**

- ★★★ **없는 로케일은 대체**(예외 없음), **틀린 태그는 거절**(`RangeError`)이다. 대체를 보는 창은 `resolvedOptions().locale` 하나다.
- ★★ small-icu 면 `de-DE` 도 영어 데이터로 적혔을 것이다 — ★ 이 머신에 small-icu 빌드가 없어 **그 대조는 못 잰 것**이다. 여기서 근거는 「**독일어 글씨가 왔다**」 쪽이다.
- ★ 판이 갈린 것은 `[1]`(판 문자열 · `DurationFormat` — Chrome 만 `function`)과 `x-nope` 의 **문구**뿐이다.

### 2. **`3 / 42`** — `de-CH`(Chrome 만 `'`) · `formatRange en-US`(Chrome 만 U+0020) · `typeof Intl.DurationFormat`(Chrome 만 `function`) · `a o z ä ö` / `a ä o ö z` / `a o z ä ö` ★★★

**출력**

```text
===== ./js48b-50b-format-grid.sh (exit=0) =====
NumberFormat ko-KR          N         1,234,567.891
NumberFormat en-US          N         1,234,567.891
NumberFormat de-DE          N         1.234.567,891
NumberFormat fr-FR          N         1<U+202F>234<U+202F>567,891
NumberFormat de-CH          N         1’234’567.891
                                        node20: =   Chrome: 1'234'567.891
NumberFormat en-IN          N         12,34,567.891
currency ko-KR KRW          N         ₩1,234,568
currency en-US KRW          N         ₩1,234,568
currency de-DE EUR          N         1.234.567,89<U+00A0>€
currency en-US EUR         -N         -€1,234,567.89
currency en-IN INR         -N         -₹12,34,567.89
compact ko-KR               N         123만
compact en-US               N         1.2M
compact de-DE               N         1,2<U+00A0>Mio.
compact en-IN               N         12L
percent de-DE           0.256         26<U+00A0>%
DateTimeFormat en-US  time short      3:04 PM
DateTimeFormat ko-KR  time short      오후 3:04
DateTimeFormat en-US  medium/medium   Sep 26, 2026, 3:04:05 PM
DateTimeFormat ko-KR  full/short      2026년 9월 26일 토요일 오후 3:04
DateTimeFormat de-DE  medium/short    26.09.2026, 15:04
DateTimeFormat en-GB  medium/short    26 Sept 2026, 15:04
DateTimeFormat ko-KR  (no options)    2026. 9. 26.
formatRange en-US  time short         3:04<U+2009>–<U+2009>4:05<U+202F>PM
                                        node20: =   Chrome: 3:04 – 4:05 PM
formatRange ko-KR  time short         오후 3:04~4:05
ListFormat en  conjunction            a, b, and c
ListFormat en  disjunction            a, b, or c
ListFormat ko  conjunction            a, b 및 c
ListFormat de  conjunction            a, b und c
RelativeTimeFormat en auto  -1 day    yesterday
RelativeTimeFormat ko auto  -1 day    어제
RelativeTimeFormat ko       -1 day    1일 전
RelativeTimeFormat de auto  -2 day    vorgestern
RelativeTimeFormat en       3 month   in 3 months
PluralRules en  1 2 3 22 (cardinal)   one other other other
PluralRules en  1 2 3 22 (ordinal)    one two few two
PluralRules ko  1 2 (cardinal)        other other
sort()                 W              a o z ä ö
Collator de            W              a ä o ö z
Collator sv            W              a o z ä ö
DisplayNames ko region DE             독일
typeof Intl.DurationFormat            undefined
                                        node20: =   Chrome: function
cells where the runtimes differ: 3 / 42
```

**왜 그런가**

- ★★★ **node 18 과 node 20 은 42칸 전부 같았다** — ICU 74.2 와 77.1 인데도. 갈린 셋은 **전부 node 대 Chrome** 이다. ★ 「판을 올려도 안 바뀐다」는 결론이 아니다 — **이 42칸이 안 움직인 것**이다.
- ★★ 숫자 여섯 행 — `1,234,567.891`(ko · en-US) · `1.234.567,891`(de) · `1<U+202F>234<U+202F>567,891`(fr) · `1’234’567.891`(de-CH, node) · **`12,34,567.891`**(en-IN). `compact` — `123만` · `1.2M` · `1,2<U+00A0>Mio.` · `12L`.
- ★★ `sort()` 는 코드 유닛 순(9번), `Collator de` 는 ä 를 a 곁에, `Collator sv` 는 ä·ö 를 알파벳 끝에 둔다.

### 3. node 20 — `[1]` **`true` · `true`** · `[2]` **`false` · `true`** · `[3]` **`false` · `true`** · Chrome — `[1]` `true` · `true` · `[2]` **`true` · `true`** · `[3]` **`false` · `true`** · `[4]` node — `(ASCII)` · **`U+2009 U+2013 U+2009`** · `(ASCII)` · **`U+202F`** ★★★

**출력**

```text
===== TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 node20 js48b-50c-lookalike-space.js (exit=0) =====
[1] time.format(T)
    formatted                    3:04 PM
    its non-ASCII code points    (none)
    === typed                    true
    every \s -> U+0020, ===      true
[2] time.formatRange(T, T2)
    formatted                    3:04 – 4:05 PM
    its non-ASCII code points    U+2009 U+2013 U+2009 U+202F
    === typed                    false
    every \s -> U+0020, ===      true
[3] fr-FR NumberFormat 1234567.891
    formatted                    1 234 567,891
    its non-ASCII code points    U+202F U+202F
    === typed                    false
    every \s -> U+0020, ===      true
[4] the literal parts of formatRangeToParts(T, T2)
    literal ":"     (ASCII)   source startRange
    literal " – "   U+2009 U+2013 U+2009   source shared
    literal ":"     (ASCII)   source endRange
    literal " "     U+202F   source shared
```

Chrome 151 — 같은 파일.

```text
===== TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 ./js48b-browser.sh js48b-50c-lookalike-space.js (exit=0) =====
[1] time.format(T)
    formatted                    3:04 PM
    its non-ASCII code points    (none)
    === typed                    true
    every \s -> U+0020, ===      true
[2] time.formatRange(T, T2)
    formatted                    3:04 – 4:05 PM
    its non-ASCII code points    U+2013
    === typed                    true
    every \s -> U+0020, ===      true
[3] fr-FR NumberFormat 1234567.891
    formatted                    1 234 567,891
    its non-ASCII code points    U+202F U+202F
    === typed                    false
    every \s -> U+0020, ===      true
[4] the literal parts of formatRangeToParts(T, T2)
    literal ":"     (ASCII)   source startRange
    literal " – "   U+2013   source shared
    literal ":"     (ASCII)   source endRange
    literal " "     (ASCII)   source shared
```

**왜 그런가**

- ★★★ node 의 `formatRange` 는 **얇은 공백(U+2009)** 과 **좁은 줄바꿈 없는 공백(U+202F)** 을 넣었다 — 키보드의 U+0020 과 **다른 글자**다. Chrome 은 같은 호출에 U+0020 을 냈다. **같은 테스트가 node 에서만 깨진다.**
- ★★★ **fr-FR 숫자 묶음은 세 판 다 U+202F** — 여기는 어느 판에서도 `false` 다.
- ★★ `\s` 는 U+2009·U+202F 를 잡으므로 **접은 뒤 비교**는 여섯 칸 다 `true`. ★ 화면에 내보낼 문자열에서는 지우지 않는다.

### 4. **`1234.5678`**(`1,234.5,678`) · **`1e21`**(`1e+21`) · **`1.005`**(`1.00` 대 `1.01`) — **`3 / 8`** · en-IN `1,23,45,678.9` ★★

**출력**

```text
===== TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 node20 js48b-50d-hand-format.js (exit=0) =====
  value        digits  by hand                   en-US                         en-IN
  1234.5       2       1,234.50                  1,234.50                      1,234.50
  -1234.5      2       -1,234.50                 -1,234.50                     -1,234.50
  1234.5678    4       1,234.5,678               1,234.5678                    1,234.5678
  -0.001       2       -0.00                     -0.00                         -0.00
  1.005        2       1.00                      1.01                          1.01
  2 ** 53 + 2  0       9,007,199,254,740,994     9,007,199,254,740,994         9,00,71,99,25,47,40,994
  1e21         0       1e+21                     1,000,000,000,000,000,000,000 1,00,00,00,00,00,00,00,00,00,000
  12345678.9   1       12,345,678.9              12,345,678.9                  1,23,45,678.9
rows where by hand and en-US differ: 3 / 8
```

**왜 그런가**

- ★★★ 정규식은 **점 뒤의 숫자에도** 걸린다(넷째 자리부터) · `toFixed` 는 10²¹ 이상에서 **지수 표기**를 돌려준다 · `1.005` 는 저장된 값이 `1.00499…` 라 `toFixed(2)` 가 `1.00`(03번 동작 (5)) — **`NumberFormat` 은 같은 값을 `1.01`** 로 적었다(관찰).
- ★★ **음수는 멀쩡했다** — `-1,234.50`. `\B` 는 `-` 와 `1` 사이를 경계로 보지 않는다.
- ★ 세 판이 한 글자도 같았다(2-summary 동작 (6) 끝의 대조기).

### 5. `C.UTF-8` → `en-US` `1,234.5` `aäz` · `de_DE` → **`de-DE` `1.234,5` `aäz`** · `sv_SE` → **`sv-SE` `1<U+00A0>234,5` `azä`** · `ko_KR` → `ko-KR` `1,234.5` `aäz` · `LC_ALL=C.UTF-8` → **`en-US`** · `TZ` — **`9/27/2026, 12:04:05 AM`**(서울) · `9/26/2026, 11:04:05 AM`(뉴욕) · 갈린 열 — **`locale`**(Chrome 은 `de`·`sv`·`ko`) ★★

**출력**

```text
===== ./js48b-50e-default-locale.sh (exit=0) =====
  runtime TZ                LANG         LC_ALL    locale  time zone          toLocaleString  sort  Date toLocaleString
  node20  UTC               C.UTF-8      -         en-US   UTC                1,234.5         aäz   9/26/2026, 3:04:05 PM
  node20  UTC               de_DE.UTF-8  -         de-DE   UTC                1.234,5         aäz   26.9.2026, 15:04:05
  node20  UTC               sv_SE.UTF-8  -         sv-SE   UTC                1<U+00A0>234,5  azä   2026-09-26 15:04:05
  node20  UTC               ko_KR.UTF-8  -         ko-KR   UTC                1,234.5         aäz   2026. 9. 26. 오후 3:04:05
  node20  UTC               de_DE.UTF-8  C.UTF-8   en-US   UTC                1,234.5         aäz   9/26/2026, 3:04:05 PM
  node20  Asia/Seoul        C.UTF-8      -         en-US   Asia/Seoul         1,234.5         aäz   9/27/2026, 12:04:05 AM
  node20  America/New_York  C.UTF-8      -         en-US   America/New_York   1,234.5         aäz   9/26/2026, 11:04:05 AM
  Chrome  UTC               C.UTF-8      -         en-US   UTC                1,234.5         aäz   9/26/2026, 3:04:05 PM
  Chrome  UTC               de_DE.UTF-8  -         de      UTC                1.234,5         aäz   26.9.2026, 15:04:05
  Chrome  UTC               sv_SE.UTF-8  -         sv      UTC                1<U+00A0>234,5  azä   2026-09-26 15:04:05
  Chrome  UTC               ko_KR.UTF-8  -         ko      UTC                1,234.5         aäz   2026. 9. 26. 오후 3:04:05
  Chrome  UTC               de_DE.UTF-8  C.UTF-8   en-US   UTC                1,234.5         aäz   9/26/2026, 3:04:05 PM
  Chrome  Asia/Seoul        C.UTF-8      -         en-US   Asia/Seoul         1,234.5         aäz   9/27/2026, 12:04:05 AM
  Chrome  America/New_York  C.UTF-8      -         en-US   America/New_York   1,234.5         aäz   9/26/2026, 11:04:05 AM
```

**왜 그런가**

- ★★★ 인자 없는 호출은 **`LC_ALL`, 없으면 `LANG`** 에서 로케일을, **`TZ`** 에서 시간대를 읽었다(두 런타임 같음). `LC_ALL` 이 있으면 `LANG` 은 무시됐다.
- ★★ Chrome 은 태그를 **언어만** 남겼고 출력 글자는 node 와 같았다 — 기본 로케일을 문자열로 비교하는 코드만 갈린다.

### 6. 여덟 줄이 예외 — **`RangeError`**: `x-nope` · `en_US` · `EURO` · `money` · `Mars/Olympus` · `fortnight` / **`TypeError`**: `style: "currency"` 만 · `timeStyle` + `timeZoneName` · 예외 없음 — **`zz-ZZ`**(`en-US`) · **`XYZ`**(`XYZ<U+00A0>1.00`) ★

**출력**

```text
===== TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 node20 js48b-50f-rejected-options.js (exit=0) =====
  NumberFormat("x-nope")                                            RangeError 「Incorrect locale information provided」
  NumberFormat("en_US")                                             RangeError 「Incorrect locale information provided」
  NumberFormat("zz-ZZ")                                             ok en-US
  NumberFormat("en", { style: "currency" })                         TypeError 「Currency code is required with currency style.」
  NumberFormat("en", { style: "currency", currency: "EURO" })       RangeError 「Invalid currency code : EURO」
  NumberFormat("en", { style: "currency", currency: "XYZ" })        ok XYZ<U+00A0>1.00
  NumberFormat("en", { style: "money" })                            RangeError 「Value money out of range for Intl.NumberFormat options property style」
  DateTimeFormat("en", { timeZone: "Mars/Olympus" })                RangeError 「Invalid time zone specified: Mars/Olympus」
  DateTimeFormat("en", { timeStyle: "long", timeZoneName: "short" })TypeError 「Can't set option timeZoneName when timeStyle is used」
  RelativeTimeFormat("en").format(1, "fortnight")                   RangeError 「Invalid unit argument for Intl.RelativeTimeFormat.prototype.format() 'fortnight'」
```

Chrome 151 — 같은 파일.

```text
===== TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8 ./js48b-browser.sh js48b-50f-rejected-options.js (exit=0) =====
  NumberFormat("x-nope")                                            RangeError 「Invalid language tag: x-nope」
  NumberFormat("en_US")                                             RangeError 「Invalid language tag: en_US」
  NumberFormat("zz-ZZ")                                             ok en-US
  NumberFormat("en", { style: "currency" })                         TypeError 「Currency code is required with currency style.」
  NumberFormat("en", { style: "currency", currency: "EURO" })       RangeError 「Invalid currency code : EURO」
  NumberFormat("en", { style: "currency", currency: "XYZ" })        ok XYZ<U+00A0>1.00
  NumberFormat("en", { style: "money" })                            RangeError 「Value money out of range for Intl.NumberFormat options property style」
  DateTimeFormat("en", { timeZone: "Mars/Olympus" })                RangeError 「Invalid time zone specified: Mars/Olympus」
  DateTimeFormat("en", { timeStyle: "long", timeZoneName: "short" })TypeError 「Invalid option : option」
  RelativeTimeFormat("en").format(1, "fortnight")                   RangeError 「Invalid unit argument for Intl.RelativeTimeFormat.prototype.format() 'fortnight'」
```

- ★★ 이름은 세 판이 같고, 문구는 Chrome 만 두 줄이 달랐다(`Invalid language tag: …` · `Invalid option : option`). node 18 은 node 20 과 같았다(2-summary 동작 (6) 끝의 대조기).
- ★★ **`XYZ` 는 통과**한다 — 통화 코드는 **모양**(영문 세 글자)만 검사됐다.

### 7. ECMA-402 몫 — **생성자와 옵션의 모양 · `currency` 가 없으면 `TypeError` · 반올림 자리(통화의 소수 자리) · 로케일 협상** / 데이터 판 몫 — **`.` 과 `,` 의 역할 · 기호가 숫자 뒤 · 그 사이의 U+00A0 · `€`** · 「보장」이라 안 쓰는 이유 — **이 문서가 ECMA-402 본문을 열지 않았기 때문**(세 판이 같게 낸 것은 관찰일 뿐이다) ★★★

- ★★★ 같은 칸이라도 「**무엇을 주문할 수 있나 · 무엇을 돌려보내나**」와 「**어떤 글씨로 써 오나**」가 층이 다르다. 판이 오를 때 바뀌는 쪽은 뒤쪽이다.
- ★★ ECMA-262 는 `toLocaleString` 을 ECMA-402 로 **넘긴다는 것**까지만 말한다(2-summary 기준 소스) — 그 너머를 보장으로 적으려면 ECMA-402 의 절을 열어 인용해야 한다.
- ★ 통화의 소수 자리가 ECMA-402 의 몫인지 데이터의 몫인지도 이 문서는 **가르지 못했다** — 가르려면 그 명세가 필요하다.

### 8. 근거 — **같은 ICU(같은 판 · 같은 프로세스)를 쓰는 한 객체의 두 메서드**가 갈렸다 · Chrome 은 두 메서드 다 U+0020 · fr-FR 숫자의 U+202F 는 세 판 다 그대로 · 한계 — **V8·node 소스를 읽지 않은 관찰의 층 배정**이다 ★★

- ★★ 데이터가 원인이면 `format()` 의 `PM` 앞에도 같은 글자가 와야 자연스럽다 — 그런데 node 에서 `format()` 은 U+0020 이었다. 그래서 「**엔진이 `format()` 결과만 손본다**」로 읽었다.
- ★ 이 읽기가 틀릴 수 있는 자리 — `format()` 과 `formatRange()` 가 **ICU 안에서 다른 데이터 경로**를 탈 가능성을 이 문서는 배제하지 못했다.

### 9. 비교 함수가 없으면 `CompareArrayElements` 가 두 값을 `ToString` 한 뒤 **`IsLessThan` 으로 코드 유닛을 견준다** — `ä` 는 U+00E4, `z` 는 U+007A 라 **뒤** · `Collator sv` 는 **스웨덴어 사전**이 ä·ö 를 알파벳 끝에 둬서 같은 순서가 나왔을 뿐, 이유가 다르다 ★★

- ★★ 증거 — `Collator de` 는 같은 다섯 글자를 `a ä o ö z` 로 두었다(2번). 코드 유닛 순이 「어떤 언어의 순서」였다면 언어를 바꿀 때 안 갈려야 한다.

### 10. 깨지는 것 — **보이지 않는 공백**(node 의 `formatRange` · fr-FR 숫자 — 3번) · **판마다 다른 글자**(`de-CH` 의 `’`/`'` · `DurationFormat` — 2번) · 판이 오를 때의 데이터 변화 · 비교 — **`formatToParts`·`formatRangeToParts` 의 `type` 과 숫자 조각**, 또는 **`\s` 를 접은 뒤** · 기댓값을 **같은 포맷터로 만들기** ★★

- ★ 가장 튼튼한 쪽은 **포맷 전의 값**(숫자 · 시각)을 검사하고 포맷은 한두 개의 대표 칸만 보는 것이다(이 문장은 이 문서의 권고다 — 측정이 아니다).

### 11. **기본 로케일**(`LC_ALL` → `LANG`)과 **기본 시간대**(`TZ`) · 서버 로그 — **`toISOString()` 같은 고정 형식**(UTC · 로케일 무관) ★

- ★ 5번의 일곱 줄이 같은 `T` 를 **일곱 가지 글자**로 적었다 — 로그를 다른 기계에서 다시 읽으면 파싱이 흔들린다. 시간대 규칙은 49번의 몫이다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js48b-50a-locale-data.js` + `.sh` | ★★ 로케일 데이터 판별 · 대체 방향 | node18 · node20 · Chrome 151 — `TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8` |
| `js48b-50b-format-cells.js` + `js48b-50b-format-grid.sh` | ★★★ 42칸 × 판 셋 · 「`3 / 42`」 | 〃 · 줄마다 칸 수 6 · 라벨 일치 검사 |
| `js48b-50c-lookalike-space.js` | ★★★ U+2009 · U+202F · `=== typed` | node20 · Chrome 151 · node18(node20 과 같음) |
| `js48b-50d-hand-format.js` | ★★ 손으로 만든 포맷 「`3 / 8`」 | 세 판 같음 |
| `js48b-50e-default-locale.js` + `.sh` | ★★ `LANG` 넷 · `LC_ALL` · `TZ` 둘 | node20 · Chrome 151 |
| `js48b-50f-rejected-options.js` | ★ 예외 이름 · 문구 | node20 · Chrome 151(문구 둘 다름) · node18(같음) |

세 판 대조기 — 한 번씩 싣는 블록이 세 판에서 같았나.

```text
===== ./js48b-50g-three-runtimes.sh (exit=0) =====
js48b-50c-lookalike-space.js     node18/node20 identical  node20/Chrome DIFFERS
js48b-50d-hand-format.js         node18/node20 identical  node20/Chrome identical
js48b-50f-rejected-options.js    node18/node20 identical  node20/Chrome DIFFERS
pairs identical 4 · differ 2
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — ★★★ **2번 격자 전체**(ICU·CLDR 이 오르면 글자가 바뀔 수 있다 · 특히 공백의 종류) · 3번(node 의 공백 · Chrome 의 공백) · 6번의 문구 · 5번의 Chrome 태그 모양(`de` 대 `de-DE`). 손으로 만든 열(4번)은 로케일 데이터를 안 읽으므로 판이 올라도 같아야 한다.
