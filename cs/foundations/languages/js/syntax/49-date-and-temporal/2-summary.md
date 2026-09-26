# js/syntax/49 — `Date` 와 Temporal: 「명세가 값을 정하는 것은 ISO 형식 안쪽뿐이다 — 날짜만 쓰면 UTC, 시각을 쓰면 로컬 · 그 밖은 엔진의 휴리스틱 · 전이 시각은 tzdata · Temporal 은 이 머신에서 Chrome 151 에만 있다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 파싱 격자다** — 문자열 여섯 × 판 셋(node 18 · node 20 · Chrome 151) × `TZ` 셋(`UTC` · `Asia/Seoul` · `America/New_York`) = **54 실행 · 18 칸**, 칸마다 `getTime()` 또는 `Invalid Date`(동작 (1)). 요약 줄 둘 — 「**`TZ` 에 따라 값이 움직인 문자열 N / 6**」 · 「**세 판이 갈린 칸 N / 18**」 — 은 스크립트가 센다.
> ★★ 보조로 **① 값 읽기 로그**(0 기반 월 · 가변성 · 뉴욕 전이 — 동작 (2)\~(4)) · **판별 블록**(Temporal 이 어느 판에 있나 — 동작 (5)) · **④ 예외의 이름 + 문구**(Temporal 의 `RangeError`·`TypeError` — 동작 (6)) · **교차 갈래 한 쌍**(Python 49 의 갭 격자 — **다시 재지 않고 인용**, 동작 (4))을 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 2026 (17판)](https://262.ecma-international.org/17.0/) — 앞 배치가 받아 둔 사본에서 읽었다. 「21.4.1.32 **Date Time String Format**」 — 「a simplification of the ISO 8601 calendar date extended format」 · 날짜만의 꼴 `YYYY` · `YYYY-MM` · `YYYY-MM-DD` · 「**A string containing out-of-bounds or nonconforming elements is not a valid instance of this format.**」 · Note 1 — `00:00` 과 `24:00` 두 자정 · 「21.4.3.2 `Date.parse`」 — 「**If the String does not conform to that format the function may fall back to any implementation-specific heuristics or implementation-specific date formats.**」 · 「**When the UTC offset representation is absent, date-only forms are interpreted as a UTC time and date-time forms are interpreted as a local time.**」 · 「21.4.1.28 `MakeDay`」 — `ym = y + floor(m / 12)` · `mn = m modulo 12` · 그 달 1일에 `dt - 1` 일 · 「21.4.1.30 `MakeFullYear`」 — 0\~99 를 1900 년대로 · 「21.4.4 `setMonth`」 — 「**Set dateObject.[[DateValue]] to u**」 · 「21.4.1.26 `UTC(t)`」 — 반복되거나 건너뛴 로컬 시각은 「**t is interpreted using the time zone offset before the transition**」 · 그 Note 의 예시 「2:30 AM on 12 March 2017 in America/New_York does not exist, but it must be interpreted as 2:30 AM UTC-05 (equivalent to 3:30 AM UTC-04)」 · 「1:30 AM on 5 November 2017 … must be interpreted as 1:30 AM UTC-04」 · 「21.4.1.25 `LocalTime`」 Note 2 — 시간대 정보는 **IANA Time Zone Database** 를 쓰라(required for time zone aware implementations) · 부록 B.2.3.1 `getYear`.
> - ★★ **ECMA-262 2026 에 `Temporal` 객체는 없다** — 같은 사본에서 `Temporal` 은 문법 기호 이름(`TemporalDecimalFraction` 등)으로만 나온다.
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 앞 배치가 받아 둔 사본(2026-09-26). **Temporal 행의 「Expected Publication Year」 가 `2027`** 이고, 회의록 링크에 `2026-03 … temporal-for-stage-4` 가 있다. README 의 「ES2027」 표기는 이 표와 맞는다. ★ 이 문서는 **ES2027 판 명세 자체는 열지 않았다**(네트워크 없이 확인할 수 있는 것은 여기까지다).
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다. 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1. ★★ **모든 실행이 `TZ` 를 명시**한다(배너 또는 스크립트 안 — 이 머신의 기본은 `Asia/Seoul`). 브라우저 하네스는 `TZ`·`LANG` 을 **환경에서 그대로 받는다**(하네스 소스는 머리말 끝의 판 블록 다음). ★ **현재 시각을 읽는 칸은 없다** — `new Date()`(인자 없음)·`Date.now()`·`Temporal.Now` 를 한 번도 안 불렀다.
> ★★★ **성능은 재지 않았다.**
>
> **버전** — `Date` 의 도입 연혁은 [history/js](../../../../../../history/js/) 의 몫이다(이 문서는 **ES2026 사본만** 읽었다 — 이전 판의 문장은 확인하지 않았다) · **Temporal — README 는 ES2027**(위 표와 맞음) · 판별 — node 18 · 20 에는 **기본으로 없고** V8 플래그 `--harmony-temporal`(「in progress」)이 있으며, Chrome 151 에는 **있다**(동작 (5)).
>
> ★ 판 블록(머리말 끝)이 보이는 대로 **node 18 은 tzdata 2023c · node 20 은 2025b** 다. Chrome 의 tzdata 판은 이 하네스로 **못 읽었다**(판 문자열을 내주는 창이 없다).
>
> **★★★ 층 — 이 문서의 결론이 기대는 네 층**
>
> | 층 | 무엇 | 어디서 |
> |---|---|---|
> | ★★★ **ECMA-262** | ISO 형식 안쪽의 값 — **날짜만은 UTC · 날짜-시각은 로컬** · `24:00` · 0 기반 월과 `MakeDay` 의 넘김 · `setMonth` 가 `[[DateValue]]` 를 바꾼다 · 전이에서 **「앞」 오프셋** | 동작 (1)의 `"2026-09-26"`·`T00:00` 행 · 동작 (2) · (3) · (4)의 규칙 |
> | ★★ **엔진(V8)** | ISO 형식 **밖**의 문자열 — 슬래시 · 영문 월 · 한 자리 월 · `02-30` · 공백 판 · `"26/09/2026"` 의 `Invalid Date` | 동작 (1)의 네 행 · 동작 (1-b) |
> | ★★ **tzdata(IANA)** | 어느 도시가 **몇 시에 몇 시간** 바뀌나 — 뉴욕 2026-03-08 · 11-01 · 서울 `+9` | 동작 (1)의 `-9h`·`+4h` · 동작 (4) |
> | ★★ **제안 · 호스트의 판** | Temporal — ES2026 에 없음 · 제안 표의 발행 연도 2027 · Chrome 151 에 있음 · node 는 **개발 중 플래그** | 동작 (5)·(6) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 파싱 격자**(본체의 도구) | 6 × 3 × 3 — 「`TZ` 로 움직인 문자열 N / 6」 · 「세 판이 갈린 칸 N / 18」(동작 (1)) |
> | ★★ **① 값 읽기 로그** | 숫자 생성자 · 공유 참조 · 뉴욕 전이 열두 벽시계(동작 (2)\~(4)) — 세 판을 **한 글자 대조**해 끝에 `yes`/`no` 로 찍는다 |
> | ★★ **판별 블록** | Temporal 다섯 실행 — 플래그 유무 × node 둘 + Chrome · **종료 코드까지**(동작 (5)) |
> | ★ **④ 예외 문구** | Temporal 의 `RangeError` — Chrome 과 node 플래그 판의 문구가 갈렸다(동작 (6)) |
> | ★★ **교차 갈래 한 쌍** | Python 49 의 갭 격자 `02:30;0` — **인용만** 한다(동작 (4)) |
> | ★★★ **「못 잰 것」 이 아니라 「창을 바꿔 물었다」**(제5의 상태) | 「`Date` 파싱은 **엔진마다** 다르다」는 이 머신에서 **잴 수 없다** — 판 셋이 **전부 V8** 이다(SpiderMonkey · JavaScriptCore 없음). 그래서 같은 질문을 **명세 문장**(ISO 밖은 implementation-specific)과 **ISO 처럼 생긴 규격 밖 문자열을 V8 이 어떻게 받나**(동작 (1-b))로 다시 물었다 — ★ 바꾼 창이 못 보는 것: **다른 엔진이 실제로 무엇을 돌려주나.** 그 칸은 여전히 비어 있다 |
> | ★ **부적용 — 성능 · 메모리** | 이 주제는 값의 의미만 본다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **tzdata 판** — 동작 (1)의 `-9h`·`+4h` 와 동작 (4)의 전이 시각은 **규칙이 바뀌면 답이 바뀌는 칸**이다. 이 문서의 두 판(2023c · 2025b)에서는 같았다 — **같았을 뿐 보장이 아니다** | ★★★ 동작 (1)의 **ISO 행 둘의 규칙**(날짜만 UTC · 날짜-시각 로컬) · 동작 (2) · (3) · 동작 (4)의 「앞 오프셋」 규칙 — 명세 |
> | ★★ **엔진 판** — 동작 (1)의 휴리스틱 행 넷과 `Invalid Date` 행 · 동작 (1-b)의 규격 밖 다섯 줄 | ★★ 판별 블록의 **종료 코드**(`133`) · Temporal 의 **값**(동작 (6) — 두 구현이 값에서 한 줄도 안 갈렸다) |
> | ★ **Temporal 의 예외 문구** · node 플래그 판의 함수 목록(개발 중 구현) · 판별 블록의 판 문자열 | ★ **재대조** — 이 문서의 블록은 두 번 캡처해 **한 글자도 같았다**(흔들리는 칸도 이 두 번 사이에서는 안 움직였다) |
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(`Date` 는 **객체**다 — `typeof` 가 `"object"` · 동작 (3)의 공유 참조가 그 결과다) · [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md)(동결은 속성까지 — 동작 (3)의 `[5]`) · [33 — 동등성 세 종류](../33-equality-three-kinds/2-summary.md)(객체의 `===` 는 동일성 — 동작 (3)의 `[6]`).
> 뒤따르는 주제 — [50 — `Intl` 국제화 포맷](../50-intl-formatting/2-summary.md)(`Intl` — 날짜를 **글자로 찍는** 쪽. 이 문서는 `toISOString()` 과 `getTime()` 만 찍어 **로케일 포맷을 한 줄도 안 쓴다**).
>
> ★★ **경계** — 「언제 들어왔나」는 [history/js](../../../../../../history/js/) 의 몫이다. 이 문서는 **값의 의미**(어느 순간이 되나 · 누가 정하나)만 다룬다. 날짜 포맷(`toLocaleString`·`Intl.DateTimeFormat`)은 50번 주제로 넘긴다.
>
> ★★ **교차 갈래** — [Python 49 — `datetime` 과 `zoneinfo`](../../../python/syntax/49-datetime-and-zoneinfo/2-summary.md)(naive/aware · **갭 격자** `2026-03-08 02:30 America/New_York` — 같은 날 같은 시각을 이미 쟀다) · [Java 51 — `java.time` 타입](../../../java/syntax/51-java-time-types/2-summary.md)(Python 49 가 인용한 대로 **같은 입력을 만드는 순간 `03:30` 으로 민다**). ★ 이 문서는 두 갈래를 **다시 돌리지 않았다** — 동작 (4)에서 결과만 한 쌍으로 놓는다.

```text
===== ./js48b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  icu 74.2  tz 2023c  unicode 15.1  cldr 44.1
node 20.19.6  v8 11.3.244.8-node.33  icu 77.1  tz 2025b  unicode 16.0  cldr 47.0
Google Chrome 151.0.7922.173
```

브라우저 하네스 — 페이지와 실행 스크립트.

```html
<!-- js48b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js48b</title>
<pre id="o"></pre>
<script>
// Runs the probe scripts named after "?" in the address (comma-separated, in that order).
// A name ending in .mjs is loaded as a module script (<script type="module">), the rest as classic scripts.
// console.log is replaced: every call appends a line and rewrites <pre>, so lines printed
// after promises and timers are present when --dump-dom writes the page out.
const __lines = [];
const __render = () => {
  document.getElementById("o").textContent = "==" + "=OUT===\n" + __lines.join("\n") + "\n===END" + "===";
};
console.log = (...a) => { __lines.push(a.join(" ")); __render(); };
window.addEventListener("error", (e) => { __lines.push("uncaught " + e.message); __render(); });
window.addEventListener("unhandledrejection", (e) => { __lines.push("unhandledrejection " + String(e.reason && e.reason.message)); __render(); });
__render();
for (const f of location.search.slice(1).split(",")) {
  const t = f.endsWith(".mjs") ? ' type="module"' : "";
  document.write('<script' + t + ' src="' + f + '"><\/script>');
}
</script>
```

```sh
# js48b-browser.sh
#!/usr/bin/env bash
# Run probe scripts in headless Chrome and print what they logged.
#   usage: ./js48b-browser.sh [--gc] [--http] <script>[,<script>...]
# Default: file:// with --allow-file-access-from-files (without it a file:// script counts as cross-origin -- "muted errors").
# --http: through js48b-serve.py on 127.0.0.1 -- module scripts (.mjs) need it.
# --gc: start Chrome with --js-flags=--expose-gc, so the page has a global gc().
# Every run gets its own throwaway profile directory, so several runs can go at once.
# The page sees the TZ and LANG this script is started with.
# --dump-dom writes HTML entities, so the last sed turns them back.
set -u -o pipefail
cd "$(dirname "$0")"
flags=()
if [ "$1" = "--gc" ]; then flags=(--js-flags=--expose-gc); shift; fi
if [ "$1" = "--http" ]; then
  shift
  pf="$(mktemp -p "$PWD" .port-XXXXXX)"
  python3 js48b-serve.py "$pf" > /dev/null 2>&1 &
  srv=$!
  for _ in $(seq 100); do [ -s "$pf" ] && break; sleep 0.05; done
  url="http://127.0.0.1:$(cat "$pf")/js48b-page.html?$1"
  rm -f "$pf"
else
  srv=
  url="file://$PWD/js48b-page.html?$1"
fi
prof="$(mktemp -d -p "$PWD" .profile-XXXXXX)"
google-chrome --headless --user-data-dir="$prof" --allow-file-access-from-files "${flags[@]}" --virtual-time-budget=60000 --dump-dom "$url" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' \
  | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g'
rc=$?
rm -rf "$prof"
[ -n "$srv" ] && kill "$srv"
exit $rc
```

## 한눈에 — 쉽게 말하면

**`Date` 는 「한 줄짜리 스톱워치 숫자」(1970-01-01 UTC 부터의 밀리초)를 담은 상자다. 상자에 날짜를 적어 넣는 입구가 여럿인데, 명세가 규칙을 정해 둔 입구는 ISO 한 곳뿐이고 나머지 입구는 엔진마다 관리인이 따로 있다. 게다가 상자는 뚜껑이 열려 있어서(`setMonth`) 같은 상자를 들고 있는 사람 모두의 숫자가 바뀐다. Temporal 은 날짜 · 시각 · 시간대 · 순간을 따로 담는 봉인된 봉투들이다 — 봉투를 고치면 새 봉투가 나온다.**

- ★★★ **같은 「그날 자정」 이 입구에 따라 다른 순간이다** — `"2026-09-26"` 은 **UTC 자정**, `"2026-09-26T00:00"` 은 **로컬 자정**(서울 `-9h` · 뉴욕 `+4h`). 둘 다 **명세**다(동작 (1)).
- ★★ **ISO 밖의 입구는 엔진이 정한다** — V8 은 `"2026/09/26"` 을 로컬 자정으로, `"2026-02-30"` 을 **3월 2일**로 받았다. 다른 엔진은 이 머신에 없어 못 쟀다(동작 (1)·(1-b)).
- ★★ **월은 0 부터, 넘치면 넘긴다** — `new Date(2026, 1, 31)` 은 **3월 3일**(동작 (2)). **`setMonth` 는 원본을 바꾼다** — 공유한 이름 모두가 바뀐다(동작 (3)).
- ★★ **없는 시각은 「전이 앞」 오프셋** — 뉴욕 `02:30` 은 `07:30Z`, 읽으면 `03:30`(ES2026 의 규칙 · Python 49 `fold=0` 과 같은 답 · 동작 (4)).
- ★★ **Temporal** — 월 1 기반 · 넘침은 **깎거나(`constrain`) 거절(`reject`)** · 원본 불변 · 순간이 되려면 **시간대가 이름으로** 필요 · `<` 는 `TypeError`. 이 머신에서는 **Chrome 151 에만** 있다(동작 (5)·(6)).

```text
   같은 글자 "2026-09-26" 의 두 입구              (TZ=Asia/Seoul)

   "2026-09-26"         ── ISO 날짜만 ──▶ UTC 로 읽는다   ──▶ 2026-09-26T00:00Z   (+0h)   ← 명세
   "2026-09-26T00:00"   ── ISO 날짜-시각 ▶ 로컬로 읽는다   ──▶ 2026-09-25T15:00Z   (-9h)   ← 명세
   "2026/09/26"         ── ISO 아님 ─────▶ 엔진 휴리스틱   ──▶ 2026-09-25T15:00Z   (-9h)   ← V8 이 정함
   "26/09/2026"         ── ISO 아님 ─────▶ 엔진 휴리스틱   ──▶ Invalid Date               ← V8 이 정함
                                                  │
                                    몇 시간 차이인가는 tzdata 가 정한다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 스톱워치 숫자 | `[[DateValue]]` — UTC 1970 부터의 밀리초(`getTime()`) | 동작 (1) |
| 명세가 규칙을 정한 입구 | Date Time String Format(ISO 의 단순화) | 동작 (1)의 ISO 행 둘 |
| 엔진마다 다른 관리인 | implementation-specific heuristics | 동작 (1)의 네 행 · (1-b) |
| 뚜껑이 열린 상자 | `setMonth` 등이 `[[DateValue]]` 를 바꾼다 | 동작 (3) |
| 얼려도 열리는 뚜껑 | `Object.freeze` 는 속성만 — 내부 슬롯은 못 막는다 | 동작 (3)의 `[5]` |
| 도시의 시계 규칙 | tzdata(IANA) | 판별 블록의 `tz` · 동작 (4) |
| 봉인된 봉투 | Temporal 객체 — 바꾸는 메서드가 없다 | 동작 (6)의 `[3]` |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**서버(UTC)에서는 맞던 생일이 사용자 브라우저(서울)에서 하루 밀린다**」(날짜만 · 날짜-시각이 섞임),
「**`new Date(y, m, d)` 에 달력의 월을 그대로 넣어 한 달 뒤가 된다**」,
「**`dueDate = startDate` 로 받아 `setMonth` 했더니 시작일도 바뀌었다**」,
「**매일 02:30 예약이 3월 둘째 일요일에만 03:30 에 돈다**」가 그것이다(동작 (1)\~(4)).

> **`Date`** — 한 순간을 **UTC 1970-01-01 부터의 밀리초 하나**로 담는 객체. 로컬 시각은 그 숫자를 **읽을 때마다** 시스템 시간대로 계산한다.\
> 예: `new Date("2026-09-26T00:00Z").getTime()` → `1790380800000`.

## 이 주제가 답하려는 질문

1. **날짜 문자열 하나는 어느 순간이 되나 — 그리고 그 값은 누가 정하나**(명세 · 엔진 · tzdata)?
2. **`Date` 의 세 함정은 어디서 오나** — 0 기반 월과 넘침 · 가변성 · 서머타임 전이의 없는 시각과 두 번 있는 시각?
3. **Temporal 은 그중 무엇을 바꾸나 — 그리고 지금 어느 판에서 쓸 수 있나?**

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 파싱 격자 — 문자열 여섯 × `TZ` 셋 × 판 셋

**언제 쓰나** — API 응답·폼 입력의 날짜 문자열을 `new Date(s)` 에 넣기 전에.
★★ 한 실행은 **한 판 · 한 `TZ`** 에서 여섯 줄(문자열 · `getTime()` · `toISOString()`)을 **탭으로** 찍고, 셸 스크립트가 **칸 수(3)를 세어 어긋나면 멈춘다**(규칙 32). 칸은 세 판이 같으면 값 하나, 다르면 셋을 다 찍는다. 괄호 안은 `2026-09-26T00:00Z` 에서 몇 시간인가.

```js
// js48b-49a-parse-cell.js
// js48b-49a-parse-cell.js
// One runtime, one TZ: what does Date.parse give for each string? One line per string, tab-separated:
//   <string> TAB <getTime() or "Invalid Date"> TAB <toISOString() or "-">
const inputs = ["2026-09-26", "2026-09-26T00:00", "2026/09/26", "Sep 26 2026", "2026-9-26", "26/09/2026"];
for (const s of inputs) {
  const d = new Date(s);
  const t = d.getTime();
  console.log([s, Number.isNaN(t) ? "Invalid Date" : String(t), Number.isNaN(t) ? "-" : d.toISOString()].join("\t"));
}
```

```sh
# js48b-49a-parse-grid.sh
#!/usr/bin/env bash
# The parse grid: js48b-49a-parse-cell.js on node18, node20 and Chrome 151, each under three TZ values.
# Every run prints one tab-separated line per string (string, getTime() or "Invalid Date", toISOString() or "-");
# a line with a different number of fields stops the script.
# A cell is (string, TZ). It shows the getTime() value once if all three runtimes gave it, all three values otherwise,
# and in brackets the hours from 2026-09-26T00:00Z.
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
P=js48b-49a-parse-cell.js
TZS=(UTC Asia/Seoul America/New_York)
declare -A V
strings=()
for tz in "${TZS[@]}"; do
  for rt in node18 node20 chrome; do
    case $rt in
      node18) out="$(env TZ="$tz" LANG=C.UTF-8 "$N18" "$P")" || exit 1 ;;
      node20) out="$(env TZ="$tz" LANG=C.UTF-8 "$N20" "$P")" || exit 1 ;;
      chrome) out="$(env TZ="$tz" LANG=C.UTF-8 ./js48b-browser.sh "$P")" || exit 1 ;;
    esac
    i=0
    while IFS= read -r line; do
      n="$(printf '%s' "$line" | awk -F'\t' '{print NF}')"
      [ "$n" = 3 ] || { echo "!! $rt $tz: $n fields in: $line"; exit 2; }
      IFS=$'\t' read -r s t iso <<< "$line"
      [ "$tz" = UTC ] && [ "$rt" = node18 ] && strings+=("$s")
      [ "${strings[$i]}" = "$s" ] || { echo "!! $rt $tz: line $i is $s"; exit 2; }
      V["$i,$tz,$rt"]="$t"
      i=$((i + 1))
    done <<< "$out"
    [ "$i" = 6 ] || { echo "!! $rt $tz: $i lines"; exit 2; }
  done
done
base=1790380800000
cell() {
  if [ "$1" = "Invalid Date" ]; then printf 'Invalid Date'
  else printf '%s (%+dh)' "$1" $(( ($1 - base) / 3600000 )); fi
}
trim() { local r="$1"; printf '%s\n' "${r%"${r##*[! ]}"}"; }
row="$(printf '%-20s' "string")"; for tz in "${TZS[@]}"; do row+="$(printf '%-22s' "TZ=$tz")"; done; trim "$row"
differ=0; cells=0
declare -A moves
for i in "${!strings[@]}"; do
  row="$(printf '%-20s' "\"${strings[$i]}\"")"
  for tz in "${TZS[@]}"; do
    a="${V[$i,$tz,node18]}"; b="${V[$i,$tz,node20]}"; c="${V[$i,$tz,chrome]}"
    cells=$((cells + 1))
    if [ "$a" = "$b" ] && [ "$b" = "$c" ]; then row+="$(printf '%-22s' "$(cell "$a")")"
    else differ=$((differ + 1)); row+="$(printf '%-22s' "$a/$b/$c")"; fi
  done
  trim "$row"
  for rt in node18 node20 chrome; do
    [ "${V[$i,UTC,$rt]}" = "${V[$i,Asia/Seoul,$rt]}" ] && [ "${V[$i,UTC,$rt]}" = "${V[$i,America/New_York,$rt]}" ] \
      || moves[$rt]=$(( ${moves[$rt]:-0} + 1 ))
  done
done
echo ""
echo "strings whose value changes with TZ: node18 ${moves[node18]:-0} / 6 · node20 ${moves[node20]:-0} / 6 · Chrome ${moves[chrome]:-0} / 6"
echo "cells (string x TZ) where the three runtimes differ: $differ / $cells"
```

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

```text
                       UTC     Asia/Seoul   America/New_York     누가 정하나
   "2026-09-26"        +0h     +0h          +0h                  명세 — 날짜만: UTC
   "2026-09-26T00:00"  +0h     -9h          +4h                  명세 — 날짜-시각: 로컬
   "2026/09/26"        +0h     -9h          +4h                  ┐
   "Sep 26 2026"       +0h     -9h          +4h                  │ V8 의 휴리스틱 (로컬로 읽었다)
   "2026-9-26"         +0h     -9h          +4h                  ┘
   "26/09/2026"        Invalid Date (세 칸)                        V8 의 휴리스틱 (못 읽었다)
                       ────────────────────────────────
                       TZ 로 움직인 문자열 4 / 6 (판마다) · 세 판이 갈린 칸 0 / 18
```

- ★★★ **`"2026-09-26"` 만 세 `TZ` 모두 `+0h`** — 날짜만의 ISO 꼴은 **UTC** 로 읽는다(명세 「date-only forms are interpreted as a UTC time」). **`T00:00` 을 붙이는 순간 로컬**이 된다(「date-time forms are interpreted as a local time」) — 같은 「그날 자정」 이 서울에서 **9시간** 갈린다.
- ★★★ **`strings whose value changes with TZ: … 4 / 6`**(세 판 다) — 움직이지 않은 둘은 `"2026-09-26"`(UTC 고정)과 `"26/09/2026"`(`Invalid Date`).
- ★★ **ISO 가 아닌 셋**(`/` · 영문 월 · 한 자리 월 `9`)은 **명세가 값을 안 정한다** — 「may fall back to any implementation-specific heuristics」. V8 은 셋 다 **로컬 자정**으로 읽었다. ★ 특히 `"2026-9-26"` 은 ISO 꼴과 **한 글자** 차이인데 **UTC 가 아니라 로컬**이다 — 월을 두 자리로 안 쓰면 입구가 바뀐다.
- ★★★ **`cells (string x TZ) where the three runtimes differ: 0 / 18`** — 그러나 이것은 「파싱이 안정적이다」의 근거가 아니다. **세 판 모두 V8** 이다(node 18 = V8 10.2 · node 20 = V8 11.3 · Chrome 151). 「엔진마다 다르다」는 이 격자로 **원리상 안 보인다** — 머리말의 제5의 상태.

### (1-b) ★★ ISO 처럼 생긴 규격 밖 문자열 — V8 은 어떻게 받나

**언제 쓰나** — 「ISO 형식이면 안전하다」고 믿고 사용자 입력을 검증 없이 넣을 때.
★ 이 블록이 제5의 상태의 **바꾼 창**이다 — 다른 엔진이 없으니, **명세가 「이 형식의 사례가 아니다」라고 한 문자열**을 V8 이 **무엇으로 받는지**를 본다. 세 판 모두 돌려 한 글자 대조한다(`TZ=Asia/Seoul`).

```js
// js48b-49b-iso-looking.js
// js48b-49b-iso-looking.js
// Strings that look like the ISO date format but are not valid instances of it (a day or month out of range,
// a space instead of T, no hyphens), next to two that are. One line per string: what new Date(s) holds.
const inputs = ["2026-02-28", "2026-02-30", "2026-09-31", "2026-13-01", "2026-09-26T24:00Z", "2026-09-26 00:00", "20260926"];
for (const s of inputs) {
  const d = new Date(s);
  console.log(JSON.stringify(s).padEnd(22) + (Number.isNaN(d.getTime()) ? "Invalid Date" : d.toISOString()));
}
```

```sh
# js48b-49z-three-runtimes.sh
#!/usr/bin/env bash
# usage: ./js48b-49z-three-runtimes.sh <TZ> <probe.js>
# Runs the probe under that TZ on node20 and prints its output, then says whether node18 and Chrome 151 printed
# exactly the same; for a runtime that did not, it prints that runtime's lines that are not in node20's output.
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
tz="$1"; p="$2"
b="$(env TZ="$tz" LANG=C.UTF-8 "$N20" "$p")" || exit 1
a="$(env TZ="$tz" LANG=C.UTF-8 "$N18" "$p")" || exit 1
c="$(env TZ="$tz" LANG=C.UTF-8 ./js48b-browser.sh "$p")" || exit 1
printf '%s\n' "$b"
echo ""
for pair in "node18:$a" "Chrome 151:$c"; do
  name="${pair%%:*}"; out="${pair#*:}"
  if [ "$out" = "$b" ]; then echo "$name prints the same as node20: yes"
  else
    echo "$name prints the same as node20: no -- its lines that node20 did not print:"
    comm -23 <(printf '%s\n' "$out" | sort) <(printf '%s\n' "$b" | sort) | sed 's/^/  /'
  fi
done
```

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

- ★★★ **`"2026-02-30"` → `2026-03-02`, `"2026-09-31"` → `2026-10-01`** — 명세는 범위 밖 요소가 있으면 「not a valid instance of this format」 이라 적는데, V8 은 **`Invalid Date` 대신 넘겨 받았다**(그리고 **UTC** 로 — 서울에서도 `T00:00Z`). `"2026-13-01"` 은 넘기지 않고 `Invalid Date`. **월은 거절하고 일은 넘긴다** — 규칙이 아니라 V8 의 휴리스틱이다.
- ★★ **`"2026-09-26 00:00"`(`T` 대신 공백) → `2026-09-25T15:00Z`** — 로컬로 읽었다. ISO 판 `T00:00` 과 **같은 값**이지만 **명세가 보장한 값이 아니다**.
- ★ `"2026-09-26T24:00Z"` → 다음 날 `00:00Z` — 이것은 **명세**다(Note 1 의 두 자정). `"20260926"`(기본 형식, 하이픈 없음) → `Invalid Date`.
- ★★ **세 판 모두 `yes`** — 이 문서가 볼 수 있는 것은 **V8 이 한결같다**는 것까지다. 다른 엔진이 `02-30` 을 거절해도 명세 위반이 아니다(명세가 may 로 열어 둔 자리 — 이 문장은 명세에서 끌어낸 것이다).

### (2) ★★ 숫자로 만든 `Date` — 0 기반 월과 넘김

**언제 쓰나** — 달력 UI 의 「9월」을 `new Date(y, m, d)` 에 넣을 때 · 「이달 말일」을 구할 때.

```js
// js48b-49c-month-numbers.js
// js48b-49c-month-numbers.js
// The Date constructor with several numbers, read back with toISOString() (run with TZ=UTC so local = UTC).
const show = (label, d) => console.log(label.padEnd(30) + (Number.isNaN(d.getTime()) ? "Invalid Date" : d.toISOString().slice(0, 10)));
show("new Date(2026, 9, 26)", new Date(2026, 9, 26));
show("new Date(2026, 8, 26)", new Date(2026, 8, 26));
show("new Date(2026, 1, 31)", new Date(2026, 1, 31));
show("new Date(2026, 12, 1)", new Date(2026, 12, 1));
show("new Date(2026, -1, 1)", new Date(2026, -1, 1));
show("new Date(2026, 0, 0)", new Date(2026, 0, 0));
show("new Date(2026, 2, 0)", new Date(2026, 2, 0));
show("new Date(26, 8, 26)", new Date(26, 8, 26));
const d = new Date("2026-09-26T00:00Z");
console.log("getMonth() of 2026-09-26".padEnd(30) + d.getMonth());
console.log("getDay() of 2026-09-26".padEnd(30) + d.getDay());
console.log("getYear() of 2026-09-26".padEnd(30) + d.getYear());
```

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

```text
   new Date(2026, 1, 31)          MakeDay: ym = 2026 + floor(1/12) = 2026 · mn = 1 (2월)
                                           2026-02-01 에 (31 - 1) 일을 더한다
                                  ──▶ 2026-03-03                 ← 에러 없이 넘긴다
   new Date(2026, 0, 0)           2026-01-01 에 (0 - 1) 일 ──▶ 2025-12-31   (전달 말일)
   new Date(2026, 12, 1)          ym = 2027 · mn = 0        ──▶ 2027-01-01
```

- ★★★ **둘째 인자 `9` 는 10월**이다 — `new Date(2026, 9, 26)` 은 `2026-10-26`. 9월 26일은 `8`. `getMonth()` 도 `8` 을 준다(`getDay()` 의 `6` 은 토요일, 일요일 = 0).
- ★★★ **넘치면 에러가 아니라 넘긴다** — 2월 31일 = **3월 3일**, 13번째 달(`12`) = 다음 해 1월, `-1` = 전해 12월, **`0` 일 = 전달 말일**(`new Date(2026, 2, 0)` 이 `2026-02-28` — 「이달 말일」 관용구가 여기서 나온다). 명세 `MakeDay` 의 계산 그대로다.
- ★ **두 자리 연도 `26` 은 `1926`** — `MakeFullYear` 가 0\~99 를 1900 년대로 읽는다. `getYear()` 는 부록 B 의 옛 메서드로 **`126`**(연도 - 1900)이다.
- ★ 세 판이 한 글자도 같았다.

### (3) ★★ 가변성 — 한 `Date` 를 여러 자리에서

**언제 쓰나** — 날짜를 함수에 넘기거나 다른 변수에 담을 때.

```js
// js48b-49d-shared-date.js
// js48b-49d-shared-date.js
// One Date object reached through two names and through a function argument (run with TZ=UTC).
const day = (d) => d.toISOString().slice(0, 10);
function nextMonth(d) {
  d.setMonth(d.getMonth() + 1);
  return d;
}
const start = new Date("2026-01-31T00:00Z");
const due = start;
console.log("[1] start " + day(start) + " · due " + day(due));
const r = due.setMonth(due.getMonth() + 1);
console.log("[2] after due.setMonth(...): start " + day(start) + " · due " + day(due) + " · setMonth returned " + r);
const opened = new Date("2026-01-31T00:00Z");
const renewal = nextMonth(opened);
console.log("[3] after renewal = nextMonth(opened): opened " + day(opened) + " · renewal " + day(renewal) + " · same object " + (opened === renewal));
const copy = new Date(opened.getTime());
copy.setDate(1);
console.log("[4] after copy.setDate(1) on new Date(opened.getTime()): opened " + day(opened) + " · copy " + day(copy));
const frozen = Object.freeze(new Date("2026-09-26T00:00Z"));
frozen.setFullYear(2000);
console.log("[5] Object.freeze(date), then setFullYear(2000): " + day(frozen) + " · isFrozen " + Object.isFrozen(frozen));
const x = new Date("2026-09-26T00:00Z"), y = new Date("2026-09-26T00:00Z");
console.log("[6] x == y " + (x == y) + " · x === y " + (x === y) + " · x <= y " + (x <= y) + " · x.getTime() === y.getTime() " + (x.getTime() === y.getTime()));
```

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

```text
   const start = new Date(1월 31일)       start ──┐
   const due = start                     due   ──┴──▶ [ Date 객체 · [[DateValue]] = 1월 31일 ]
   due.setMonth(due.getMonth() + 1)                         │ Set [[DateValue]] to u
                                                             ▼
                                                   [ [[DateValue]] = 3월 3일 ]   ← 두 이름 다 이 값
                                                   (2월 31일을 MakeDay 가 넘겼다)
```

- ★★★ **`[2]` — `start` 도 `2026-03-03`** · `[3]` — `nextMonth(opened)` 가 인자를 **그 자리에서** 바꿔 `opened` 도 바뀌었고 `same object true`. `setMonth` 는 **새 `Date` 를 돌려주지 않는다** — 반환값은 **숫자**(`1772496000000`)다.
- ★★ **「한 달 뒤」 가 3월 3일인 것은 넘김과 가변성이 겹친 것**이다 — 1월 31일의 「2월 31일」 을 `MakeDay` 가 넘겼다(동작 (2)).
- ★★ **복사는 `new Date(d.getTime())`**(`[4]` — `copy` 만 `03-01`).
- ★★★ **`[5]` — `Object.freeze` 한 `Date` 에 `setFullYear(2000)` 이 먹었다**(`2000-09-26` · `isFrozen true`). 동결은 **속성**을 막는데 `Date` 의 값은 속성이 아니라 **내부 슬롯 `[[DateValue]]`** 다(14번 — 동결이 못 닿는 자리가 하나 더 있다).
- ★ **`[6]` — `x == y` 도 `x === y` 도 `false`**(같은 순간이어도 **다른 객체** — 33번) · `x <= y` 는 `true`(`valueOf` 로 숫자 비교) · 같은 순간인지는 `getTime()` 끼리.

### (4) ★★★ 뉴욕의 두 전이 — 없는 시각 · 두 번 있는 시각 · 23시간짜리 날

**언제 쓰나** — 벽시계 시각으로 일정을 잡을 때 · 「하루 뒤」를 밀리초로 더할 때.
★ `TZ=America/New_York` · 2026년 전이 — **3월 8일 02:00 → 03:00**(앞으로) · **11월 1일 02:00 → 01:00**(뒤로). 전이 시각은 **tzdata** 가 정한다(node 18 = 2023c · node 20 = 2025b 에서 같았다).

```js
// js48b-49e-new-york-transitions.js
// js48b-49e-new-york-transitions.js
// Local wall-clock times near the two 2026 transitions in America/New_York, built with the Date constructor
// (run with TZ=America/New_York). Each line: the wall time asked for -> the instant (UTC) -> the wall time it reads back as.
const pad = (n) => String(n).padStart(2, "0");
const wall = (d) => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
const ask = (label, d) => console.log(label.padEnd(24) + d.toISOString().slice(0, 16) + "Z   reads back " + wall(d) + "   offset " + (-d.getTimezoneOffset() / 60) + "h");
console.log("[1] 2026-03-08 (clocks go from 02:00 to 03:00)");
for (const [h, m] of [[1, 59], [2, 0], [2, 30], [2, 59], [3, 0]]) ask("  " + pad(h) + ":" + pad(m), new Date(2026, 2, 8, h, m));
ask("  string 02:30", new Date("2026-03-08T02:30"));
console.log("[2] 2026-11-01 (clocks go from 02:00 back to 01:00)");
for (const [h, m] of [[0, 59], [1, 0], [1, 30], [2, 0]]) ask("  " + pad(h) + ":" + pad(m), new Date(2026, 10, 1, h, m));
console.log("[3] 2026-03-07 12:00 plus 24 hours of milliseconds, and plus one day with setDate");
const before = new Date(2026, 2, 7, 12, 0);
ask("  + 86400000 ms", new Date(before.getTime() + 86400000));
const byDate = new Date(before.getTime()); byDate.setDate(byDate.getDate() + 1);
ask("  setDate(+1)", byDate);
```

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

```text
   2026-03-08  America/New_York      벽시계                     순간(UTC)
                                     01:59  EST -05:00   ──▶   06:59Z
               02:00 ~ 02:59 은 없다  02:00  (없음)       ──▶   07:00Z  ── 읽으면 03:00   ┐ 전이 「앞」
                                     02:30  (없음)       ──▶   07:30Z  ── 읽으면 03:30   │ 오프셋 -05:00
                                     02:59  (없음)       ──▶   07:59Z  ── 읽으면 03:59   ┘ 으로 읽는다
                                     03:00  EDT -04:00   ──▶   07:00Z  ← 02:00 과 같은 순간

   2026-11-01                        01:30  (두 번 있다)  ──▶   05:30Z  (-04:00 — 먼저 오는 쪽)
```

- ★★★ **없는 시각(`02:00`\~`02:59`)은 전이 「앞」 오프셋 `-05:00` 으로 읽힌다** — `02:30` → `07:30Z` → 읽으면 **`03:30`**. ECMA-262 2026 의 `UTC(t)` 가 그렇게 **못 박았다**(「t is interpreted using the time zone offset before the transition」 · 예시가 바로 뉴욕 `2:30 AM` 이다). 문자열 `"2026-03-08T02:30"` 도 같은 값이다(날짜-시각은 로컬 — 같은 길을 탄다).
- ★★ **`02:00` 과 `03:00` 이 같은 순간 `07:00Z`** — 벽시계 둘이 한 순간에 모인다. 「벽시계 → 순간」 은 **일대일이 아니다.**
- ★★ **두 번 있는 `01:30` 은 `-4h`** — 「앞」 오프셋, 즉 **먼저 오는 쪽**(서머타임 쪽). 명세 Note 의 「1:30 AM UTC-04」 와 같다.
- ★★★ **`[3]` — 3월 7일 12:00 에서 `+ 86400000 ms` 는 `13:00`, `setDate(+1)` 은 `12:00`** — 3월 8일은 **23시간짜리 날**이다. 「하루 = 86 400 000 ms」 는 이 날 틀린다.
- ★★ **Python 49 와 한 쌍** — [Python 49](../../../python/syntax/49-datetime-and-zoneinfo/2-summary.md)의 갭 격자에서 **`02:30;0` 은 `-0500 · EST · as UTC 07:30 · back to NY 03:30 EDT`** 였다(같은 날 · 같은 도시 · 같은 시각). **답은 같고 경로가 다르다** — 파이썬은 `02:30` 을 **그대로 들고 있다가** UTC 로 갈 때 드러나고(그 편의 제5의 상태 — 만들 때 아무 말도 안 한다), `Date` 는 **만드는 순간** 한 순간값(`07:30Z`)으로 굳는다. [Java 51](../../../java/syntax/51-java-time-types/2-summary.md)도 같은 입력을 `03:30` 으로 민다(Python 49 의 인용). ★ 이 문서는 두 갈래를 **다시 돌리지 않았다.**
- ★ 세 판이 한 글자도 같았다.

### (5) ★★★ Temporal 은 어느 판에 있나 — 판별 다섯 실행

**언제 쓰나** — 「Temporal 을 써도 되나」 를 판단할 때.
★★ node 두 판은 **플래그 유무**로 두 번씩, Chrome 은 한 번. 죽는 실행은 **종료 코드**와 표준 오류의 `# ` 로 시작하는 줄(V8 의 치명 오류 머리)만 찍는다 — 나머지 표준 오류는 **주소**라 흔들린다(규칙 16 — 안 흔들리게 만드는 쪽).

```js
// js48b-49f-temporal-presence.js
// js48b-49f-temporal-presence.js
// Is there a Temporal global here, and does one small call on it finish?
console.log("typeof Temporal: " + typeof Temporal);
if (typeof Temporal === "object") {
  console.log("own names: " + Object.getOwnPropertyNames(Temporal).filter((k) => typeof Temporal[k] === "function").sort().join(" "));
  console.log("PlainDate.from('2026-09-26').add({ months: 1 }).toString(): " + Temporal.PlainDate.from("2026-09-26").add({ months: 1 }).toString());
}
console.log("reached the last line");
```

```sh
# js48b-49f-temporal-presence.sh
#!/usr/bin/env bash
# js48b-49f-temporal-presence.js on node18 and node20, each with and without the V8 flag --harmony-temporal, then Chrome 151.
# A run that dies prints its exit code and the lines of its standard error that start with "# " (the V8 fatal-error header).
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
P=js48b-49f-temporal-presence.js
ok=0; all=0
row() {
  local label="$1"; shift
  local out err rc
  err="$(mktemp -p "$PWD" .e49f-XXXXXX)"
  out="$("$@" 2>"$err")"; rc=$?
  echo "--- $label (exit=$rc)"
  printf '%s\n' "$out" | sed 's/^/  /'
  [ -s "$err" ] && grep '^# [A-Za-z]' "$err" | sed 's/^/  stderr /'
  rm -f "$err"
  all=$((all + 1))
  case $out in *".toString(): "*) ok=$((ok + 1)) ;; esac
}
row "node18" env TZ=UTC "$N18" "$P"
row "node18 --harmony-temporal" env TZ=UTC "$N18" --harmony-temporal "$P"
row "node20" env TZ=UTC "$N20" "$P"
row "node20 --harmony-temporal" env TZ=UTC "$N20" --harmony-temporal "$P"
row "Chrome 151" env TZ=UTC ./js48b-browser.sh "$P"
echo ""
echo "runs where the call on Temporal printed a value: $ok / $all"
```

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

플래그의 설명 문자열 — `node --v8-options` 에서.

```sh
# js48b-49h-v8-flags.sh
#!/usr/bin/env bash
# The V8 flags whose name ends in "temporal" that each node build lists (node --v8-options), each with its next line.
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  v="$("$n" --version)" || exit 1
  opts="$("$n" --v8-options)" || exit 1
  echo "--- node $v"
  printf '%s\n' "$opts" | grep -A1 -E '^  --[a-z-]*temporal '
done
echo "(end)"
```

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

```text
                              typeof Temporal   함수 목록   PlainDate…add…toString()   exit
   node18                     undefined         —          —                          0
   node18 --harmony-temporal  object            10 개      (엔진이 죽었다)              133
   node20                     undefined         —          —                          0
   node20 --harmony-temporal  object            10 개      2026-10-26                 0
   Chrome 151                 object             8 개      2026-10-26                 0
                              ───────────────────────────────────────
                              호출이 값을 찍은 실행 2 / 5
```

- ★★★ **기본 상태의 node 18 · 20 에는 Temporal 이 없다**(`typeof Temporal: undefined`). **Chrome 151 에는 있다.**
- ★★★ **`--harmony-temporal` 은 「지원」 이 아니다** — `node --v8-options` 스스로 「**in progress**」(node 20 은 「**in progress / experimental**」)라고 적는다. node 18 판은 `Temporal` 객체를 내놓고도 `toString()` 한 번에 **V8 치명 오류 `unimplemented code`** 로 죽었다(`exit=133`). node 20 판은 이 호출을 해냈다.
- ★★ **함수 목록이 다르다** — node 의 개발 중 구현은 **`Calendar` · `TimeZone`** 을 갖고, Chrome 151 은 **안 갖는다**(여덟 개). 개발 중 구현이 **옛 모양**을 들고 있다(그 모양이 언제 바뀌었는지 원문은 확인하지 않았다).
- ★ **요약 — `runs where the call on Temporal printed a value: 2 / 5`**. 이 문서는 **node 18 · 20 을 「Temporal 없음」 으로 센다.**

### (6) ★★ Temporal 에게 같은 질문 — 월 · 넘침 · 불변 · 시간대 · 비교

**언제 쓰나** — 동작 (2)\~(4)의 함정을 Temporal 이 어떻게 막는지 볼 때.
★ Chrome 151 이 본판이고, node 20 `--harmony-temporal` 은 **같은 위치의 줄이 다른 것만** 찍는다.

```js
// js48b-49g-temporal-behaviour.js
// js48b-49g-temporal-behaviour.js
// The same questions as the Date blocks, asked of Temporal. Each line: <label> -> <result or ExceptionName 「message」>.
const run = (label, f) => {
  let r;
  try { r = String(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log(label.padEnd(58) + r);
};
console.log("[1] month numbers");
run("new Temporal.PlainDate(2026, 9, 26).month", () => new Temporal.PlainDate(2026, 9, 26).month);
run("new Temporal.PlainDate(2026, 9, 26).toString()", () => new Temporal.PlainDate(2026, 9, 26).toString());
console.log("[2] a day that does not exist");
run("new Temporal.PlainDate(2026, 2, 31)", () => new Temporal.PlainDate(2026, 2, 31));
run("PlainDate.from({ year: 2026, month: 2, day: 31 })", () => Temporal.PlainDate.from({ year: 2026, month: 2, day: 31 }));
run("PlainDate.from({ ... }, { overflow: 'reject' })", () => Temporal.PlainDate.from({ year: 2026, month: 2, day: 31 }, { overflow: "reject" }));
run("PlainDate.from('2026-02-31')", () => Temporal.PlainDate.from("2026-02-31"));
console.log("[3] adding a month to January 31");
const jan31 = Temporal.PlainDate.from("2026-01-31");
const next = jan31.add({ months: 1 });
run("jan31.add({ months: 1 })", () => next);
run("jan31 after that call", () => jan31);
run("jan31.add({ months: 1 }, { overflow: 'reject' })", () => jan31.add({ months: 1 }, { overflow: "reject" }));
run("typeof jan31.setMonth", () => typeof jan31.setMonth);
run("Object.isFrozen(jan31)", () => Object.isFrozen(jan31));
console.log("[4] the same string, with and without a time zone");
run("Instant.from('2026-09-26T00:00')", () => Temporal.Instant.from("2026-09-26T00:00"));
run("Instant.from('2026-09-26T00:00Z').epochMilliseconds", () => Temporal.Instant.from("2026-09-26T00:00Z").epochMilliseconds);
run("PlainDateTime.from('2026-09-26T00:00')", () => Temporal.PlainDateTime.from("2026-09-26T00:00"));
run("  .toZonedDateTime('Asia/Seoul').epochMilliseconds", () => Temporal.PlainDateTime.from("2026-09-26T00:00").toZonedDateTime("Asia/Seoul").epochMilliseconds);
run("  .toZonedDateTime('America/New_York').epochMilliseconds", () => Temporal.PlainDateTime.from("2026-09-26T00:00").toZonedDateTime("America/New_York").epochMilliseconds);
console.log("[5] 2026-03-08 02:30 in America/New_York, four disambiguation values");
for (const d of ["compatible", "earlier", "later", "reject"]) {
  run("  disambiguation: '" + d + "'", () => Temporal.ZonedDateTime.from("2026-03-08T02:30[America/New_York]", { disambiguation: d }).toString());
}
run("  (no option)", () => Temporal.ZonedDateTime.from("2026-03-08T02:30[America/New_York]").toString());
console.log("[6] comparing two dates");
const d1 = Temporal.PlainDate.from("2026-09-26"), d2 = Temporal.PlainDate.from("2026-09-27");
run("d1 < d2", () => d1 < d2);
run("'' + d1", () => "" + d1);
run("Temporal.PlainDate.compare(d1, d2)", () => Temporal.PlainDate.compare(d1, d2));
run("d1.equals(Temporal.PlainDate.from('2026-09-26'))", () => d1.equals(Temporal.PlainDate.from("2026-09-26")));
```

```sh
# js48b-49g-temporal-compare.sh
#!/usr/bin/env bash
# js48b-49g-temporal-behaviour.js in Chrome 151 (Temporal shipped) and on node20 with --harmony-temporal (in progress).
# Prints Chrome's output, then node20's lines that differ from Chrome's at the same position, and counts them.
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
P=js48b-49g-temporal-behaviour.js
c="$(env TZ=UTC ./js48b-browser.sh "$P")" || exit 1
n="$(env TZ=UTC "$N20" --harmony-temporal "$P")" || exit 1
mapfile -t C <<< "$c"; mapfile -t N <<< "$n"
[ "${#C[@]}" = "${#N[@]}" ] || { echo "!! line counts differ: ${#C[@]} and ${#N[@]}"; exit 2; }
echo "--- Chrome 151"
printf '%s\n' "$c"
echo "--- node20 --harmony-temporal, lines that differ from Chrome"
d=0
for i in "${!C[@]}"; do
  if [ "${C[$i]}" != "${N[$i]}" ]; then d=$((d + 1)); printf '%s\n' "${N[$i]}"; fi
done
echo ""
echo "lines where node20 --harmony-temporal differs from Chrome 151: $d / ${#C[@]}"
```

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

```text
                        Date                                Temporal
   월 번호               0 기반 (9 = 10월)                     1 기반 (month 9)
   2월 31일              조용히 3월 3일                         from: 2월 28일 (constrain) · reject: RangeError · 생성자: RangeError
   1월 31일 + 1개월       원본이 3월 3일로 바뀐다                  새 객체 2월 28일 · 원본 1월 31일 그대로
   오프셋 없는 날짜-시각    로컬로 읽는다 (TZ 에 따라 다른 순간)       Instant: RangeError · PlainDateTime → 시간대를 이름으로 줘야 순간
   뉴욕 02:30            -05:00 으로 읽는다 (선택지 없음)          disambiguation 넷 — compatible · earlier · later · reject
   d1 < d2              valueOf 로 숫자 비교                     TypeError — compare 를 쓰라
```

- ★★★ **월은 1 기반**(`month` 가 `9`) · **없는 날짜는 기본이 깎기(`constrain` → `2026-02-28`)**, `overflow: 'reject'` 면 `RangeError`. **생성자와 문자열은 처음부터 거절**한다. `Date` 의 「조용히 넘긴다」 와 정반대다.
- ★★★ **`jan31.add({ months: 1 })` 은 `2026-02-28` 이고 `jan31` 은 그대로 `2026-01-31`** — 새 객체를 돌려준다. `setMonth` 는 **없다**(`undefined`). ★ 그런데 **`Object.isFrozen(jan31)` 은 `false`** — 불변은 동결이 아니라 **바꾸는 메서드가 없는 것**에서 온다(값은 내부 슬롯에 있다).
- ★★★ **시간대 없이는 순간이 안 된다** — `Instant.from('2026-09-26T00:00')` 이 `RangeError`(Chrome 문구 「Required fields missing from Instant string.」). 벽시계(`PlainDateTime`)에 **시간대 이름**을 주면 순간이 되고, 그 수(`1790348400000` · `1790395200000`)가 **동작 (1)의 `-9h`·`+4h` 칸과 같다.** `Date` 가 **보이지 않게** 하던 일을 **글자로 적게** 만든 것이다.
- ★★★ **뉴욕 `02:30` — `compatible`(기본) · `later` 는 `03:30-04:00`, `earlier` 는 `01:30-05:00`, `reject` 는 `RangeError`.** 기본값의 답은 `Date`(동작 (4))와 같고, **다른 답을 고를 수 있고 「없는 시각」 을 에러로 받을 수도 있다.** ★ Chrome 의 `reject` 문구는 갭인데도 「Rejecting **ambiguous** time zones.」 다(문구는 판의 것).
- ★★ **`d1 < d2` 와 `'' + d1` 이 `TypeError`** — `valueOf` 가 **일부러 던진다**(「use … compare for comparison」). `Date` 처럼 `<` 로 비교하던 코드가 **조용히 틀리지 않고 멈춘다.** 비교는 `compare` · `equals`.
- ★★ **node 20 플래그 판 — `lines … differs from Chrome 151: 6 / 31`, 여섯 줄이 전부 `RangeError` 의 문구**다(「Invalid time value for Temporal ../deps/v8/src/objects/js-temporal-objects.cc:664」 처럼 **V8 소스 파일과 줄 번호**가 박혀 있다). **값은 한 줄도 안 갈렸다.** `TypeError` 의 `valueOf` 문구는 같았다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 보장 | 어디서 봤나 |
|---|---|---|---|
| `new Date("YYYY-MM-DD")` | **UTC** 자정 | 명세 | 동작 (1) |
| `new Date("YYYY-MM-DDTHH:mm")` | **로컬** 시각 | 명세 | 동작 (1) |
| `new Date("…Z")` · `"…+09:00"` | 오프셋대로 | 명세 | 동작 (1-b) `T24:00Z` |
| `new Date("2026/09/26")` 등 ISO 밖 | 엔진의 휴리스틱 | ★ **구현** | 동작 (1) · (1-b) |
| `new Date(y, m, d, …)` | **로컬**, `m` 은 **0 기반**, 넘치면 넘김 | 명세(`MakeDay`) | 동작 (2) |
| `d.setMonth(m)` 등 `set…` | **원본의 `[[DateValue]]` 를 바꾸고** 숫자를 돌려준다 | 명세 | 동작 (3) |
| `new Date(d.getTime())` | 복사 | 명세 | 동작 (3) `[4]` |
| `Temporal.PlainDate.from(x, { overflow })` | 1 기반 월 · `constrain`/`reject` | ★ **ES2026 에 없음**(제안 표 2027) | 동작 (6) |
| `plain.add(…)` · `with(…)` | **새 객체** | 〃 | 동작 (6) `[3]` |
| `ZonedDateTime.from("…[Zone]", { disambiguation })` | 시간대를 **이름으로** · 갭/fold 선택 | 〃 | 동작 (6) `[5]` |
| `Temporal.PlainDate.compare(a, b)` | 비교 — `<` 는 `TypeError` | 〃 | 동작 (6) `[6]` |

## 어디서 틀리나

### (1) ★★★ 날짜만 쓴 문자열과 시각까지 쓴 문자열을 섞는다

`"2026-09-26"` 은 UTC, `"2026-09-26T00:00"` 은 로컬 — 서울에서 **9시간** 갈린다(동작 (1)). 생일·마감일처럼 **「날짜」 인 값**을 `Date` 로 들고 다니면 로컬로 찍는 순간 하루가 밀릴 수 있다 — 날짜는 날짜로(Temporal `PlainDate` 또는 문자열 그대로).

### (2) ★★★ 「ISO 처럼 생겼으니 안전하다」

`"2026-9-26"`(한 자리 월)은 ISO 가 아니라 **로컬**이 됐고, `"2026-02-30"` 은 **3월 2일**이 됐다(동작 (1)·(1-b)). 둘 다 **V8 의 휴리스틱** — 다른 엔진은 다를 수 있다(이 문서는 못 쟀다). 입력은 **형식을 먼저 검사**하고, 가능하면 `…Z` 나 오프셋을 붙인 꼴만 받는다.

### (3) ★★ 「세 판에서 같았다」 를 「엔진마다 같다」 로 읽는다

세 판은 **전부 V8** 이다(동작 (1)의 `0 / 18`). 규칙 3 의 「여러 버전에서 같았다는 보장이 아니다」 가 여기서는 **판이 아니라 엔진**의 문제다.

### (4) ★★ 달력의 월을 그대로 넣는다 · 넘침을 에러로 기대한다

`new Date(2026, 9, 26)` 은 10월이고, 2월 31일은 **말없이** 3월 3일이다(동작 (2)). 검증이 필요하면 만든 뒤 **`getMonth()` 를 다시 읽어** 넘쳤는지 본다 — 또는 Temporal 의 `overflow: 'reject'`.

### (5) ★★★ 받은 `Date` 에 `set…` 을 부른다

인자·공유 변수·캐시에 든 `Date` 를 `setMonth` 하면 **들고 있는 모두가 바뀐다**(동작 (3)). **복사한 뒤** 바꾸거나 새로 만든다. ★ `Object.freeze` 로도 **안 막힌다**(`[5]`).

### (6) ★★ 「하루 = 86 400 000 ms」

뉴욕 3월 8일은 **23시간**이다(동작 (4) `[3]`). 벽시계를 지키려면 `setDate(+1)`(또는 Temporal `ZonedDateTime.add({ days: 1 })`), 경과 시간이면 밀리초 — **둘을 구분**한다.

### (7) ★★ 없는 시각을 만들고 아무 말이 없기를 기대한다

`new Date(2026, 2, 8, 2, 30)` 은 **에러 없이 `03:30`** 이다(동작 (4)) — 파이썬도 그 칸에서 조용했다(Python 49). 「없는 시각이다」를 알아야 하면 Temporal `disambiguation: 'reject'`(동작 (6)).

### (8) ★★ `--harmony-temporal` 로 켜서 「node 에서 Temporal 이 된다」 고 적는다

node 18 판은 **엔진이 죽었고**, node 20 판은 문구에 V8 소스 줄 번호가 박힌 **개발 중 구현**이다(동작 (5)·(6)). 이 머신의 node 로는 **없음**으로 센다.

### (9) ★ `Date` 를 `==` 로 비교한다 · Temporal 을 `<` 로 비교한다

`Date` 의 `==` 는 **객체 동일성**이라 같은 순간이어도 `false`(동작 (3) `[6]`) · Temporal 의 `<` 는 **`TypeError`**(동작 (6) `[6]`).

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262 2026)

- ★★★ **ISO 꼴 — 날짜만은 UTC · 날짜-시각은 로컬 · 오프셋이 있으면 그대로** · `24:00` 은 다음 날 `00:00`.
- ★★★ **숫자 생성자와 `set…` — 0 기반 월 · `MakeDay` 의 넘김 · `MakeFullYear` 의 0\~99 → 1900 년대 · `[[DateValue]]` 를 바꾼다.**
- ★★★ **로컬 → UTC 에서 반복·건너뛴 시각은 「전이 앞」 오프셋**(`UTC(t)`) — 뉴욕 `02:30` 은 `-05:00`. ★ 이 문서는 **ES2026 사본의 문장**만 확인했다 — 이 규칙이 몇 판부터 있었는지는 확인하지 않았다.
- ★★ **ISO 밖 · 범위 밖 요소는 「이 형식의 사례가 아니다」 → 휴리스틱으로 넘어갈 수 있다(may)** — 즉 **값은 보장되지 않는다.**

### 엔진(V8) · 이 판의 관찰

- ★★★ 슬래시 · 영문 월 · 한 자리 월 · 공백 판을 **로컬**로 읽음 · `02-30`·`09-31` 을 **넘겨 UTC** 로 읽음 · `13` 월과 `"26/09/2026"`·`"20260926"` 은 `Invalid Date` — **세 판이 같았다**(동작 (1)·(1-b)).
- ★★ **Temporal** — Chrome 151 에 있음 · node 18 · 20 은 개발 중 플래그뿐 · 예외 **문구**(Chrome 「Temporal error: …」 · node 20 플래그 판 「Invalid time value for Temporal …cc:N」).

### tzdata(IANA)

- ★★★ **어느 도시가 언제 몇 시간** — 서울 `+9` · 뉴욕 2026-03-08 · 11-01. 명세는 「IANA 를 쓰라」 까지만 말한다(`LocalTime` Note 2). 판이 다르면(2023c · 2025b) **규칙이 바뀐 지역에서 답이 바뀐다** — 이 문서의 칸에서는 안 바뀌었다.

### 제안 · 호스트의 판

- ★★ **Temporal 은 ES2026 에 없다** · TC39 finished proposals 의 발행 예정 연도 **2027**(README 의 ES2027). ★ 시간대 이름을 받는 `ZonedDateTime` 도 **tzdata** 에 기댄다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`Date` 는 ISO 문자열을 UTC 로 읽는다」 → ○ 「**날짜만의 ISO 꼴**은 UTC, **날짜-시각 꼴은 로컬**이다」
- ✗ 「`new Date("2026/09/26")` 은 로컬 자정이다」 → ○ 「**V8 이** 로컬 자정으로 읽었다 — 명세는 값을 안 정한다」
- ✗ 「`Date` 파싱은 node · Chrome 에서 같으니 안전하다」 → ○ 「**셋 다 V8** 이다 — 엔진이 다르면 모른다」
- ✗ 「없는 시각은 `Invalid Date` 가 된다」 → ○ 「**전이 앞 오프셋으로 읽혀** 한 시간 뒤의 벽시계가 된다(명세)」
- ✗ 「node 20 에 Temporal 이 있다」 → ○ 「**개발 중 플래그**가 있다 — 기본으로는 없다」
- ✗ 「Temporal 객체는 `Object.freeze` 돼 있다」 → ○ 「`isFrozen` 은 `false` — **바꾸는 메서드가 없다**」

## 언제 쓰고 언제 안 쓰나

- **`Date`** — **순간**(타임스탬프)을 담고 주고받을 때. 들어올 때는 **`…Z`·오프셋이 붙은 ISO** 나 **밀리초 숫자**로, 나갈 때는 `toISOString()`. 로컬 벽시계 계산은 이 머신의 `TZ` 에 달려 있다는 것을 전제로 둔다.
- **Temporal** — 날짜(`PlainDate`)·벽시계(`PlainDateTime`)·시간대가 붙은 시각(`ZonedDateTime`)·순간(`Instant`)을 **타입으로 가를** 때. ★ 이 머신에서는 **Chrome 151 에서만** 된다 — node 에서 쓰려면 폴리필이 필요하다(이 문서는 폴리필을 돌리지 않았다 — npm 설치 금지).
- ★ **안 쓰는 자리** — ISO 밖의 사람 글자(`"26/09/2026"`)를 `new Date` 에 바로 넣기 · 받은 `Date` 에 `set…` · 「하루 = 86 400 000 ms」.

## 핵심 문장

1. ★★★ **날짜만의 ISO 꼴은 UTC, 날짜-시각 꼴은 로컬** — 같은 「그날 자정」 이 서울 `-9h` · 뉴욕 `+4h` 로 갈린다. `TZ` 로 움직인 문자열 **`4 / 6`**.
2. ★★★ **ISO 밖은 엔진의 휴리스틱** — V8 은 한 자리 월도 로컬로, `02-30` 도 3월 2일로 받았다. 세 판이 갈린 칸 **`0 / 18`** 은 **셋 다 V8** 이라서다 — 엔진 차이는 이 머신에서 못 쟀다.
3. ★★ **0 기반 월과 넘김**(2월 31일 = 3월 3일) · **`set…` 은 원본을 바꾼다**(공유 이름 모두 · `Object.freeze` 로도 못 막음).
4. ★★★ **없는 시각은 전이 앞 오프셋**(ES2026) — 뉴욕 `02:30` → `07:30Z` → `03:30`. Python 49 `fold=0` 과 같은 답, 다른 경로. 3월 8일은 23시간.
5. ★★★ **Temporal** — 1 기반 월 · `constrain`/`reject` · 새 객체 · 시간대를 이름으로 · `<` 는 `TypeError`. **ES2026 에 없고**(제안 표 2027), 이 머신에서는 **Chrome 151 에만** 있다 — node 의 `--harmony-temporal` 은 개발 중(18 은 `exit=133`).

## 관련 자료

- [ECMA-262 2026 (17판)](https://262.ecma-international.org/17.0/) — Date Time String Format · `Date.parse` · `MakeDay` · `UTC(t)` · `LocalTime` · 부록 B `getYear` · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — Temporal 행.
- [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) · [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) · [33 — 동등성 세 종류](../33-equality-three-kinds/2-summary.md).
- [Python 49 — `datetime` 과 `zoneinfo`](../../../python/syntax/49-datetime-and-zoneinfo/2-summary.md) — ★ **경계**: naive/aware · `fold` · 갭 격자의 **정본은 그쪽**이다. 여기는 **JS `Date` 가 같은 칸에서 무엇을 하나**만 한 쌍으로 놓는다. [Java 51 — `java.time`](../../../java/syntax/51-java-time-types/2-summary.md).
- [50 — `Intl` 국제화 포맷](../50-intl-formatting/2-summary.md)(`Intl`) — ★ **경계**: 날짜를 **로케일 글자로 찍는 것**은 그쪽. 여기는 `getTime()`·`toISOString()` 만 쓴다.
- [history/js](../../../../../../history/js/) — 도입 연혁.

## 용어 풀이

- **`[[DateValue]]`** — `Date` 객체의 내부 슬롯. UTC 1970-01-01 부터의 밀리초(시간 값). `getTime()` 이 이것을 읽는다.
- **Date Time String Format** — 명세가 정한 ISO 8601 의 단순화 꼴(`YYYY-MM-DDTHH:mm:ss.sssZ` 와 그 줄임). 이 꼴만 값이 보장된다.
- **휴리스틱(implementation-specific heuristics)** — ISO 꼴이 아닌 문자열을 엔진이 **자기 방식**으로 읽는 것. 명세는 허용만 한다(may).
- **날짜만의 꼴 / 날짜-시각 꼴** — `YYYY-MM-DD` 까지만 쓴 것 / 뒤에 `THH:mm…` 을 붙인 것. 오프셋이 없으면 앞은 UTC, 뒤는 로컬.
- **`MakeDay`** — 연·월·일을 날짜 수로 바꾸는 명세 연산. 월을 12 로 나눠 연에 올리고, 일은 1일에서 더한다 — 그래서 넘친다.
- **tzdata(IANA Time Zone Database)** — 지역마다 언제 몇 시간 차이인지를 적은 데이터베이스. 판(`2023c`·`2025b`)이 있다.
- **갭(gap) / fold** — 시계를 앞으로 당겨 **사라진** 벽시계 구간 / 뒤로 돌려 **두 번 있는** 구간(Python 49 의 말).
- **Temporal** — 날짜·시각을 타입별로 가른 불변 객체 묶음(TC39 제안 · 발행 예정 2027).
- **`overflow`** — Temporal 에서 없는 날짜를 **깎을지(`constrain`) 거절할지(`reject`)** 고르는 선택지.
- **`disambiguation`** — Temporal 에서 갭·fold 의 벽시계를 **어느 순간으로 읽을지** 고르는 선택지(`compatible`·`earlier`·`later`·`reject`).
- **`--harmony-temporal`** — V8 의 개발 중 Temporal 을 켜는 플래그. node 18 · 20 이 「in progress」 로 적는다.

## 더 들어가면

- **다른 엔진의 파싱** — SpiderMonkey · JavaScriptCore 는 이 머신에 없어 **못 쟀다**(동작 (1-b)의 바꾼 창이 못 보는 칸).
- **`Date` 의 「전이 앞」 규칙이 들어온 판** — ES2026 사본의 문장만 확인했다. 이전 판은 열지 않았다.
- **Temporal 의 달력(`calendar`)** — 이 문서는 ISO 달력만 썼다.
- **폴리필** — npm 설치 금지라 돌리지 않았다.
