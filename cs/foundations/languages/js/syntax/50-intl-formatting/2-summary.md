# js/syntax/50 — `Intl` 국제화 포맷: 「API 의 모양은 ECMA-402 가 정하고 글자는 로케일 데이터 판이 정한다 — 세 판은 42칸 중 3칸에서 갈렸고, 그중 하나는 눈에 안 보이는 공백이었다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 포맷 격자다** — 포맷터 × 입력 × 로케일 **42칸**을 **node 18 · node 20 · Chrome 151** 에서 돌려 **출력 문자열**을 나란히 놓고, 판이 갈린 칸을 스크립트가 센다(동작 (2) — 마지막 줄 `cells where the runtimes differ: N / M`).
> ★★★ 그 격자를 읽는 법은 **층 가르기**다 — 같은 칸 안에서도 **어떤 메서드·옵션이 있고 무엇을 거절하나**(ECMA-402)와 **어떤 글자가 나오나**(로케일 데이터 — CLDR·ICU 의 판)는 다른 층이다. 문서의 결론 줄마다 어느 층인지 붙인다(아래 「층」 표).
> ★★ 보조로 **① 로케일 데이터 판별**(small-icu 인가 full-icu 인가 — 동작 (1)) · **③ 코드 포인트 덤프**(눈에 같은 두 문자열 — 동작 (3)) · **④ 예외의 이름 + 문구**(동작 (6)) · **⑤ 환경 격자**(`LANG`·`LC_ALL`·`TZ` — 동작 (5))를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 2026 (17판)](https://262.ecma-international.org/17.0/) — 이 배치가 받아 둔 사본에서 확인했다. `Number.prototype.toLocaleString` 절 「**An ECMAScript implementation that includes the ECMA-402 Internationalization API must implement this method as specified in the ECMA-402 specification.** If an ECMAScript implementation does not include the ECMA-402 API … formatted according to the conventions of the host environment's current locale. This method is **implementation-defined**」 · `CompareArrayElements` — 비교 함수가 없으면 두 값을 `ToString` 한 뒤 **`IsLessThan`(문자열 비교 — 코드 유닛 순)** 으로 가른다.
> - ★★★ [ECMA-402](https://tc39.es/ecma402/) — ★ **이 배치는 ECMA-402 본문을 열지 않았다**(외부 네트워크 없이 작성). 그래서 이 문서가 ECMA-402 에 대해 하는 말은 **「ECMA-262 가 그쪽으로 위임한다」는 위 문장**과 **세 판에서 같게 나온 것(관찰)** 두 가지뿐이다. 「ECMA-402 가 이렇게 적었다」 는 문장은 **쓰지 않는다.**
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1(Ubuntu 패키지 — **시스템 ICU 를 링크**한다). 하네스는 44번의 것을 복사해 **실행마다 새 프로필 디렉토리**를 쓰고 **`TZ`·`LANG` 을 그대로 페이지에 넘기게** 고친 판이다(소스는 아래 머리말 끝).
> ★★★ **블록마다 `TZ`·`LANG`·`LC_ALL` 을 배너에 적었다** — 이 주제의 출력은 **환경이 입력**이다(동작 (5)). 날짜는 전부 **고정 시각** `Date.UTC(2026, 8, 26, 15, 4, 5)` 이고 포맷터마다 `timeZone: "UTC"` 를 준다.
> ★★★ **눈에 안 보이는 공백을 블록에서 지우지 않았다** — 동작 (3)의 node 블록에는 **U+202F · U+2009 가 그대로** 들어 있고, 바로 옆 줄에 **코드 포인트 덤프**가 있다. 격자(동작 (2))는 세 판을 글자로 견주기 위해 그 글자들을 `<U+XXXX>` 로 적는다(아래 창 표의 제5의 상태).
> ★★★ **성능은 재지 않았다.** 「`Intl.NumberFormat` 을 재사용하면 빠르다」 같은 문장은 이 문서에 없다.
>
> **버전** — `process.versions` 로 읽은 판(판별 블록). **Chrome 은 ICU·CLDR 판을 페이지에서 물을 창이 없다**(못 잰 것 — `process` 가 없다). 기능 판별은 실행으로 했다 — **`Intl.DurationFormat` 만 두 node 판에 없고 Chrome 151 에 있다**(동작 (1)). ECMA-402 의 몇 판에 어느 생성자가 들어왔는지는 **이 문서가 확인하지 않았다.**
>
> **★★★ 층 — 이 문서의 결론이 기대는 네 층**
>
> | 층 | 무엇 | 어디서 |
> |---|---|---|
> | ★★ **ECMA-262** | `toLocaleString` 은 **ECMA-402 로 위임**(없으면 implementation-defined) · 비교 함수 없는 `sort()` 는 **코드 유닛 순** · `toFixed` | 기준 소스 · 동작 (2)의 `sort()` 행 · 동작 (4) |
> | ★★★ **ECMA-402**(관찰로만 본 몫) | 어떤 생성자·옵션이 있나 · 무엇을 **거절하나**(예외의 **종류**) · 없는 로케일을 **무엇으로 대체**했나(`resolvedOptions().locale`) | 동작 (1) · 동작 (6) — 세 판이 **예외 이름은 한 번도 안 갈렸다** |
> | ★★★ **로케일 데이터(CLDR·ICU 판)** | **어떤 글자가 나오나** — 구분자 · 어순 · 단어 · 공백의 종류 | 동작 (2)의 42칸 전부 · 흔들리는 칸으로 선언 |
> | ★★ **엔진·호스트** | 기본 로케일을 **어디서 읽나**(`LC_ALL` → `LANG`) · 예외 **문구** · 같은 ICU 인데 `format()` 과 `formatRange()` 의 공백이 다른 것 | 동작 (3) · (5) · (6) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 포맷 격자**(본체의 도구) | 42칸 × 판 셋 — 「`cells where the runtimes differ: 3 / 42`」(동작 (2)) |
> | ★★ **① 로케일 데이터 판별** | `supportedLocalesOf` · `resolvedOptions().locale` · 독일어 숫자 하나 — 세 판 다 **full-icu**(동작 (1)) |
> | ★★★ **③ 코드 포인트 덤프** | 눈에 같은 두 문자열 — `=== typed` 가 `false` 인 자리(동작 (3)) |
> | ★★ **⑤ 환경 격자** | `LANG` 넷 · `LC_ALL` 하나 · `TZ` 둘 — 인자 없는 호출의 답(동작 (5)) |
> | ★ **④ 예외 이름 + 문구** | 거절 열 가지 — 이름은 세 판이 같고 문구는 Chrome 만 둘이 달랐다(동작 (6)) |
> | ★★★ **제5의 상태 — 「창을 바꿔 물었다」** | **눈은 U+0020 과 U+202F 를 못 가른다** → 같은 질문(「같은 문자열인가」)을 `===` 와 코드 포인트로 다시 물었다(동작 (3)). ★ 또 하나 — **Chrome 하네스의 `--dump-dom` 은 U+00A0 을 `&nbsp;` 로 적는다**(하네스의 `sed` 는 `&lt;`·`&gt;`·`&quot;`·`&amp;` 만 되돌린다). 그대로 두면 Chrome 칸이 **가짜로** 갈리므로 격자는 비슷한 공백을 **페이지 안에서** `<U+XXXX>` 로 바꿔 찍는다. ★ 바꾼 창이 못 보는 것 — `<U+XXXX>` 표기는 **목록에 넣은 공백류만** 드러낸다(U+00A0 · U+1680 · U+2000\~U+200F · U+2028\~U+202F · U+205F · U+3000 · U+FEFF). 다른 비슷한 글자(예 — U+2019 따옴표)는 글자 그대로 나온다 |
> | ★ **못 잰 것** | Chrome 의 ICU·CLDR 판 — 페이지에서 물을 API 가 없다 |
> | ★ **부적용 — 「옳은 포맷」** | 어느 칸의 글자가 **그 언어로 맞나**는 이 창들이 답하지 않는다 — 데이터 판이 무엇을 담았나만 본다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **데이터 판이 오르면 바뀔 수 있는 칸** — 동작 (2)의 **42칸의 글자 전부** · 동작 (3)의 공백 종류 · 동작 (5)의 `Date toLocaleString` 열 · 동작 (6)의 **문구**. 이 판들에서는 재실행해도 한 글자도 같았다 — **그래서 흔들리지 않는 것이 아니라 판에 묶인 것이다** | ★★★ 칸의 **개수와 판이 갈렸다는 사실**(`3 / 42`) · 예외의 **이름** · `=== typed` 의 참거짓(그 판에서) · 동작 (4)의 **손으로 만든 열**(ECMA-262 의 `toFixed` 와 정규식 — 로케일 데이터를 안 읽는다) |
> | 판별 블록의 판 문자열 | 동작 (1)의 대체 방향(`zz-ZZ` → `en-US` · `de-ZZ` → `de`) — 세 판 같음 |
>
> **선행** — [49 — `Date` 와 Temporal](../49-date-and-temporal/2-summary.md)(직접 선행 — `Date` 의 시각과 시간대. 여기는 그 시각을 **글자로 적는 쪽**만) ·
> [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md)(★ **이미 쟀다** — `(1.005).toFixed(2)` 가 `1.00` 인 것은 **저장된 값이 `1.00499999999999989342`** 이기 때문 — 거기 동작 (5). 여기는 **같은 값을 `NumberFormat` 이 `1.01` 로 적는 것**만 더한다) ·
> [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)(`Intl.Segmenter` — **글자 경계는 거기**, 여기는 포맷터만).
>
> ★★ **경계** — 시간대 규칙(DST·`zoneinfo`)은 49번과 [Python 49 — `datetime`·`zoneinfo`](../../../python/syntax/49-datetime-and-zoneinfo/2-summary.md)의 몫이다. 이 문서의 날짜 칸은 전부 **`timeZone: "UTC"` 로 시간대를 뺀 뒤의 「어떻게 적나」** 다.

```text
===== ./js48b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  icu 74.2  tz 2023c  unicode 15.1  cldr 44.1
node 20.19.6  v8 11.3.244.8-node.33  icu 77.1  tz 2025b  unicode 16.0  cldr 47.0
Google Chrome 151.0.7922.173
```

하네스 — 44번의 것을 복사해 두 줄을 고쳤다(프로필 · 환경).

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

## 한눈에 — 쉽게 말하면

**`Intl` 은 「번역소에 맡기는 서식 주문서」다. 주문서 양식(어떤 칸이 있고 무엇을 적으면 돌려보내나)은 표준이 정하고, 실제로 어떤 글씨로 써 오나는 번역소가 가진 사전(CLDR·ICU 데이터)의 판이 정한다. 그래서 같은 주문서를 세 번역소에 보내면 대개 같은 글씨가 오지만, 사전 판이 다르면 가끔 다르게 온다 — 그리고 가끔은 눈으로는 똑같아 보이는 다른 공백이 끼어 온다.**

- ★★★ **판이 갈린 칸은 42칸 중 3칸**(동작 (2)) — `de-CH` 의 천 단위 구분 기호(`’` 대 `'`) · `en-US` 의 `formatRange` 공백 · `Intl.DurationFormat` 의 유무.
- ★★★ **node 18(ICU 74.2)과 node 20(ICU 77.1)은 42칸이 한 글자도 같았다** — 갈린 셋은 전부 **node 대 Chrome** 이다.
- ★★★ **`=== "3:04 – 4:05 PM"` 이 node 에서는 `false`** — 사이에 **U+2009 · U+202F** 가 끼어 있다. 같은 포맷터의 `format()` 은 U+0020 이었다(동작 (3)).
- ★★ **손으로 만든 천 단위 구분은 음수에서는 안 깨졌다** — 깨진 자리는 **소수 넷째 자리 · `1e21` · `1.005`** 였고, 인도식 묶음은 원리상 못 만든다(동작 (4)).

```text
   new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(1234567.891)

   ┌─ 주문서(ECMA-402) ─────────────────┐     ┌─ 사전(CLDR·ICU 판) ───────────┐
   │ 로케일 협상: de-DE 있나? → de-DE    │     │ de 의 숫자: 묶음 "." 소수 ","  │
   │ 옵션 검사:  currency 없으면 TypeError│ ──▶ │ 통화 자리: 숫자 뒤 + U+00A0   │
   │ 반올림:     소수 2자리              │     │ EUR 의 기호: €                │
   └────────────────────────────────────┘     └──────────────┬──────────────┘
                                                             ▼
                                          "1.234.567,89" + U+00A0 + "€"
                                     (판이 바뀌면 오른쪽 상자의 글자만 바뀐다)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 서식 주문서 | `new Intl.NumberFormat(locale, options)` 류 생성자 | 동작 (2) |
| 주문서 양식 · 돌려보내는 규칙 | ECMA-402 — 옵션 · `RangeError`/`TypeError` | 동작 (6) |
| 번역소의 사전 | CLDR 데이터 + ICU(node 는 `process.versions` 로 판을 안다) | 판별 블록 · 동작 (1) |
| 사전에 없는 언어를 주문하면 | 로케일 대체 — `resolvedOptions().locale` | 동작 (1) `[3]` |
| 주문서에 언어를 안 적으면 | 기본 로케일 — **`LC_ALL` → `LANG`** 에서 온다 | 동작 (5) |
| 눈에 똑같은 다른 공백 | U+00A0 · U+202F · U+2009 | 동작 (3) |
| 손으로 쓴 서식 | `toFixed` + 쉼표 정규식 | 동작 (4) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**테스트에 `"3:04 – 4:05 PM"` 을 박았더니 로컬(node)에서는 깨지고 브라우저에서는 통과한다**」,
「**Node 를 올렸더니 스냅샷 테스트의 날짜 문자열이 전부 깨졌다**」(데이터 판이 오른 것),
「**서버에서 만든 금액 문자열과 브라우저에서 만든 금액 문자열이 `!==`**」가 그것이다(동작 (2)·(3)).

> **`Intl`** — ECMA-402 가 정하는 국제화 API 의 이름공간. `NumberFormat`·`DateTimeFormat`·`ListFormat`·`RelativeTimeFormat`·`PluralRules`·`Collator` 등.\
> 예: `new Intl.NumberFormat("ko-KR", { style: "currency", currency: "KRW" }).format(1234567.891)`

## 이 주제가 답하려는 질문

1. **같은 포맷 호출이 판마다 같은 문자열을 내나** — 어느 칸이 갈리고, 갈린 것은 어느 층(주문서 양식 / 사전 판 / 엔진)인가?
2. **포맷된 문자열을 문자열로 비교해도 되나** — 눈에 같은 두 문자열이 `===` 에서 갈리는 자리는 어디인가?
3. **손으로 쓴 포맷은 어디서 깨지고, 인자를 안 준 호출은 무엇에 달려 있나** — `toFixed` + 정규식 · 기본 로케일 · 기본 시간대?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★ 로케일 데이터 판별 — small-icu 인가 full-icu 인가

**언제 쓰나** — 「이 런타임에서 `ko-KR` 포맷이 제대로 나오나」를 믿기 전에.
★ small-icu 빌드는 **영어 데이터만** 싣는다 — 그러면 `de-DE` 를 주문해도 영어 글씨가 온다. 그래서 **네 가지로 묻는다** — 판 문자열 · `supportedLocalesOf` · 대체된 로케일 · 독일어 숫자 하나.

```js
// js48b-50a-locale-data.js
// Which locale data does this runtime carry, and what does it pick when the asked-for locale is missing?
// Run under a fixed TZ / LANG / LC_ALL (see the banner). Every value is a fixed number -- no current time.
const show = (label, f) => {
  let r;
  try { r = String(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(46) + r);
};
console.log("[1] build");
show("process.versions.icu", () => (typeof process === "object" ? process.versions.icu : "(no process object)"));
show("typeof Intl.DurationFormat", () => typeof Intl.DurationFormat);
console.log("[2] supportedLocalesOf -- which of these has data?");
const asked = ["ko-KR", "de-DE", "sv-SE", "fr-FR", "en-IN", "ja-JP", "ar-EG", "zz-ZZ"];
show("DateTimeFormat", () => Intl.DateTimeFormat.supportedLocalesOf(asked).join(" "));
show("NumberFormat", () => Intl.NumberFormat.supportedLocalesOf(asked).join(" "));
console.log("[3] the locale actually used -- resolvedOptions().locale");
for (const tag of ["ko-KR", "de-DE", "sv", "en-IN", "zz-ZZ", "de-ZZ", "x-nope"]) {
  show("new Intl.NumberFormat(" + JSON.stringify(tag) + ")", () => new Intl.NumberFormat(tag).resolvedOptions().locale);
}
show("new Intl.NumberFormat()   (no argument)", () => new Intl.NumberFormat().resolvedOptions().locale);
show("new Intl.DateTimeFormat().timeZone", () => new Intl.DateTimeFormat().resolvedOptions().timeZone);
console.log("[4] one German number -- data present or English fallback?");
show("new Intl.NumberFormat(\"de-DE\").format(1234.5)", () => new Intl.NumberFormat("de-DE").format(1234.5));
show("(1234.5).toLocaleString()   (no argument)", () => (1234.5).toLocaleString());
```

```sh
# js48b-50a-locale-data.sh
#!/usr/bin/env bash
# js48b-50a-locale-data.js on node18, node20 and Chrome 151, all under TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8.
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
E=(env TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8)
echo "--- node18"; "${E[@]}" "$N18" js48b-50a-locale-data.js || exit 1
echo "--- node20"; "${E[@]}" "$N20" js48b-50a-locale-data.js || exit 1
echo "--- Chrome 151"; "${E[@]}" ./js48b-browser.sh js48b-50a-locale-data.js || exit 1
```

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

```text
   주문한 태그      사전에 있나            resolvedOptions().locale
   ko-KR · de-DE    있다                  그대로
   sv · en-IN       있다                  그대로
   de-ZZ            de 는 있고 ZZ 는 없다   de            ← 뒤를 떼어 낸다
   zz-ZZ            없다                   en-US         ← 기본 로케일(이 블록은 LANG=C.UTF-8)
   x-nope           태그 자체가 틀렸다       RangeError    ← 대체가 아니라 거절
```

- ★★★ **세 판 다 full-icu 다** — `supportedLocalesOf` 가 여덟 중 **`zz-ZZ` 를 뺀 일곱**을 전부 돌려주고, `de-DE` 숫자가 **`1.234,5`** 다(small-icu 면 영어 데이터로 `1,234.5` 가 되었을 것이다 — ★ 이 문장의 괄호 안은 **small-icu 빌드를 돌려 보지 않은** 설명이다. 이 머신에 small-icu 빌드가 없다).
- ★★ **node 18 은 시스템 ICU 74.2**, node 20 은 **77.1**(판별 블록). 사전 판이 다른데 이 블록은 **한 글자도 안 갈렸다** — 갈린 것은 `[1]` 의 판 문자열 · `DurationFormat` · `x-nope` 의 **문구**뿐이다.
- ★★★ **없는 로케일은 조용히 대체된다** — `zz-ZZ` 는 **예외 없이 `en-US`**, `de-ZZ` 는 **`de`**. **`resolvedOptions().locale` 을 읽지 않으면 대체된 줄 모른다.** 반면 **문법이 틀린 태그**(`x-nope`)는 `RangeError` 다 — 「없는 것」과 「틀린 것」은 다른 대답이다.
- ★ **`new Intl.NumberFormat()`(인자 없음)은 `en-US`** — 이 블록이 `LANG=C.UTF-8` 이라서다. 환경을 바꾸면 이 줄이 바뀐다(동작 (5)).

### (2) ★★★ 포맷 격자 — 42칸 × 판 셋

**언제 쓰나** — 서버(node)와 브라우저가 **같은 문자열**을 낼 거라고 기대할 때 · 런타임을 올리기 전.
★★ 한 줄 = 한 칸 = `<라벨> TAB <출력>`. `.sh` 가 세 판의 출력을 줄 단위로 붙이고, **줄마다 칸 수(6)와 라벨이 같은지** 확인한 뒤 어긋나면 멈춘다(규칙 32 — 출력 안에 TAB 이 들어오면 칸이 조용히 잘린다). node 20 · Chrome 열은 node 18 과 같으면 `=` 이고, 다를 때만 둘째 줄에 적는다.

```js
// js48b-50b-format-cells.js
// One line per cell: <label> TAB <output>. The same script runs on node18, node20 and Chrome;
// js48b-50b-format-grid.sh lines the three up. Every date is the fixed instant T; every formatter names its time zone.
// Characters that look like a space but are not U+0020 are written as <U+XXXX>, so the three runtimes
// can be compared as plain text (and so Chrome's --dump-dom cannot turn U+00A0 into "&nbsp;").
const T = Date.UTC(2026, 8, 26, 15, 4, 5);   // 2026-09-26 15:04:05 UTC
const T2 = Date.UTC(2026, 8, 26, 16, 5, 0);  // an hour later
const N = 1234567.891;
const W = ["a", "z", "ä", "o", "ö"];   // the words the sort / Collator rows put in order
const lookalike = (n) => n === 0xA0 || n === 0x1680 || (n >= 0x2000 && n <= 0x200F) || (n >= 0x2028 && n <= 0x202F) ||
  n === 0x205F || n === 0x3000 || n === 0xFEFF;
const shown = (s) => [...s].map((c) => (lookalike(c.codePointAt(0))
  ? "<U+" + c.codePointAt(0).toString(16).toUpperCase().padStart(4, "0") + ">" : c)).join("");
const nf = (loc, o) => (x) => new Intl.NumberFormat(loc, o).format(x);
const dtf = (loc, o) => new Intl.DateTimeFormat(loc, { timeZone: "UTC", ...o });
const cells = [
  ["NumberFormat ko-KR          N", () => nf("ko-KR")(N)],
  ["NumberFormat en-US          N", () => nf("en-US")(N)],
  ["NumberFormat de-DE          N", () => nf("de-DE")(N)],
  ["NumberFormat fr-FR          N", () => nf("fr-FR")(N)],
  ["NumberFormat de-CH          N", () => nf("de-CH")(N)],
  ["NumberFormat en-IN          N", () => nf("en-IN")(N)],
  ["currency ko-KR KRW          N", () => nf("ko-KR", { style: "currency", currency: "KRW" })(N)],
  ["currency en-US KRW          N", () => nf("en-US", { style: "currency", currency: "KRW" })(N)],
  ["currency de-DE EUR          N", () => nf("de-DE", { style: "currency", currency: "EUR" })(N)],
  ["currency en-US EUR         -N", () => nf("en-US", { style: "currency", currency: "EUR" })(-N)],
  ["currency en-IN INR         -N", () => nf("en-IN", { style: "currency", currency: "INR" })(-N)],
  ["compact ko-KR               N", () => nf("ko-KR", { notation: "compact" })(N)],
  ["compact en-US               N", () => nf("en-US", { notation: "compact" })(N)],
  ["compact de-DE               N", () => nf("de-DE", { notation: "compact" })(N)],
  ["compact en-IN               N", () => nf("en-IN", { notation: "compact" })(N)],
  ["percent de-DE           0.256", () => nf("de-DE", { style: "percent" })(0.256)],
  ["DateTimeFormat en-US  time short", () => dtf("en-US", { timeStyle: "short" }).format(T)],
  ["DateTimeFormat ko-KR  time short", () => dtf("ko-KR", { timeStyle: "short" }).format(T)],
  ["DateTimeFormat en-US  medium/medium", () => dtf("en-US", { dateStyle: "medium", timeStyle: "medium" }).format(T)],
  ["DateTimeFormat ko-KR  full/short", () => dtf("ko-KR", { dateStyle: "full", timeStyle: "short" }).format(T)],
  ["DateTimeFormat de-DE  medium/short", () => dtf("de-DE", { dateStyle: "medium", timeStyle: "short" }).format(T)],
  ["DateTimeFormat en-GB  medium/short", () => dtf("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(T)],
  ["DateTimeFormat ko-KR  (no options)", () => dtf("ko-KR", {}).format(T)],
  ["formatRange en-US  time short", () => dtf("en-US", { timeStyle: "short" }).formatRange(T, T2)],
  ["formatRange ko-KR  time short", () => dtf("ko-KR", { timeStyle: "short" }).formatRange(T, T2)],
  ["ListFormat en  conjunction", () => new Intl.ListFormat("en").format(["a", "b", "c"])],
  ["ListFormat en  disjunction", () => new Intl.ListFormat("en", { type: "disjunction" }).format(["a", "b", "c"])],
  ["ListFormat ko  conjunction", () => new Intl.ListFormat("ko").format(["a", "b", "c"])],
  ["ListFormat de  conjunction", () => new Intl.ListFormat("de").format(["a", "b", "c"])],
  ["RelativeTimeFormat en auto  -1 day", () => new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(-1, "day")],
  ["RelativeTimeFormat ko auto  -1 day", () => new Intl.RelativeTimeFormat("ko", { numeric: "auto" }).format(-1, "day")],
  ["RelativeTimeFormat ko       -1 day", () => new Intl.RelativeTimeFormat("ko").format(-1, "day")],
  ["RelativeTimeFormat de auto  -2 day", () => new Intl.RelativeTimeFormat("de", { numeric: "auto" }).format(-2, "day")],
  ["RelativeTimeFormat en       3 month", () => new Intl.RelativeTimeFormat("en").format(3, "month")],
  ["PluralRules en  1 2 3 22 (cardinal)", () => [1, 2, 3, 22].map((n) => new Intl.PluralRules("en").select(n)).join(" ")],
  ["PluralRules en  1 2 3 22 (ordinal)", () => [1, 2, 3, 22].map((n) => new Intl.PluralRules("en", { type: "ordinal" }).select(n)).join(" ")],
  ["PluralRules ko  1 2 (cardinal)", () => [1, 2].map((n) => new Intl.PluralRules("ko").select(n)).join(" ")],
  ["sort()                 W", () => [...W].sort().join(" ")],
  ["Collator de            W", () => [...W].sort(new Intl.Collator("de").compare).join(" ")],
  ["Collator sv            W", () => [...W].sort(new Intl.Collator("sv").compare).join(" ")],
  ["DisplayNames ko region DE", () => new Intl.DisplayNames("ko", { type: "region" }).of("DE")],
  ["typeof Intl.DurationFormat", () => typeof Intl.DurationFormat],
];
for (const [label, f] of cells) {
  let r;
  try { r = String(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log(label + "\t" + shown(r));
}
```

```sh
# js48b-50b-format-grid.sh
#!/usr/bin/env bash
# The format grid: js48b-50b-format-cells.js on node18, node20 and Chrome 151 (TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8),
# one row per cell. The node20 and Chrome columns print "=" when they match node18.
# Each input line must hold exactly one TAB and the three runs must list the same labels in the same order;
# otherwise the script stops (a separator inside the data would cut a cell short without any error).
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
E=(env TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8)
a="$("${E[@]}" "$N18" js48b-50b-format-cells.js)" || exit 1
b="$("${E[@]}" "$N20" js48b-50b-format-cells.js)" || exit 1
c="$("${E[@]}" ./js48b-browser.sh js48b-50b-format-cells.js)" || exit 1
paste <(printf '%s\n' "$a") <(printf '%s\n' "$b") <(printf '%s\n' "$c") | awk -F'\t' '
  NF != 6 { print "!! line " NR " has " NF " fields, not 6"; bad = 1; exit 1 }
  $1 != $3 || $1 != $5 { print "!! line " NR ": labels differ"; bad = 1; exit 1 }
  { n++; x = ($4 == $2) ? "=" : $4; y = ($6 == $2) ? "=" : $6
    if (x != "=" || y != "=") d++
    printf "%-37s %s\n", $1, $2
    if (x != "=" || y != "=") printf "%-37s   node20: %s   Chrome: %s\n", "", x, y }
  END { if (!bad) print "cells where the runtimes differ: " d+0 " / " n }'
```

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

```text
   42칸
    ├─ node18 = node20 = Chrome ─────────────────── 39칸
    │    (ICU 74.2 와 77.1 이 이 42칸에서는 한 글자도 같았다)
    └─ 갈린 칸 ─────────────────────────────────── 3칸
         de-CH 의 천 단위        node ’ (U+2019)       Chrome ' (U+0027)     ← 데이터 판
         formatRange en-US      node <U+2009>–<U+2009> … <U+202F>PM
                                Chrome 전부 U+0020                          ← 엔진(동작 (3))
         Intl.DurationFormat    node 두 판 undefined   Chrome function      ← 기능의 유무
```

- ★★★ **`cells where the runtimes differ: 3 / 42`** — 이 수 자체가 결론이다. **대부분은 같다**, 그러나 **같다는 보장은 없다** — ECMA-262 는 `toLocaleString` 을 ECMA-402 로 넘기고, 없으면 **implementation-defined** 로 둔다(기준 소스). 글자는 데이터 판의 것이다.
- ★★★ **node 18 과 node 20 은 42칸 전부 `=`** 였다 — ICU 가 74.2 → 77.1 로 세 판 올랐는데도. ★ **「판이 올라도 안 바뀐다」로 읽지 마라** — 이 42칸이 **우연히 안 움직인 칸**이었을 뿐이다(판에 묶인 칸 — 머리말 표).
- ★★ **로케일이 무엇을 바꾸나** — 같은 `1234567.891` 이 `1,234,567.891`(en-US · ko-KR) · `1.234.567,891`(de-DE) · **`1<U+202F>234<U+202F>567,891`**(fr-FR) · `1’234’567.891`(de-CH, node) · **`12,34,567.891`**(en-IN — 셋째 자리 뒤로는 **두 자리씩**) 이 되었다.
- ★★ **통화는 로케일과 통화 코드가 따로다** — `ko-KR KRW` 와 `en-US KRW` 가 같은 `₩1,234,568`(원은 소수 자리가 없어 반올림), `de-DE EUR` 은 **숫자 뒤 + `<U+00A0>`**, `en-US EUR` 음수는 `-€1,234,567.89`(부호가 기호 앞).
- ★★ **`compact` 는 언어마다 단위가 다르다** — `123만`(ko) · `1.2M`(en-US) · `1,2<U+00A0>Mio.`(de) · `12L`(en-IN — 라크).
- ★★ **`numeric: "auto"`** 는 `-1 day` 를 `yesterday` · `어제` 로, 독일어 `-2 day` 는 **`vorgestern`** 으로 적는다. 옵션이 없으면 `1일 전`.
- ★★ **`PluralRules`** — 영어 서수 `1 2 3 22` 는 `one two few two`(22nd), 기수는 `one other other other`, 한국어는 1 도 `other` 다 — **「1 이면 단수」를 코드에 박으면 한국어에서 틀린다.**
- ★★★ **`sort()` 는 `a o z ä ö`** — ä(U+00E4)가 z(U+007A) **뒤**로 간다. 비교 함수가 없으면 **코드 유닛 순**이기 때문이다(ECMA-262 `CompareArrayElements`). **`Collator de` 는 `a ä o ö z`**(ä 를 a 곁에), **`Collator sv` 는 `a o z ä ö`** — 스웨덴어는 ä·ö 가 **알파벳 끝의 별개 글자**다. ★ **`sort()` 와 `Collator sv` 가 같은 순서**인 것은 우연이다 — 한쪽은 코드 유닛, 한쪽은 스웨덴어 사전.

### (3) ★★★ 눈에 같은 두 문자열 — `===` 와 코드 포인트로 다시 묻는다

**언제 쓰나** — 포맷 결과를 **테스트 기댓값 · 캐시 키 · 파싱 입력**으로 쓸 때.
★★ 비교 대상 문자열은 **키보드로 친 것**이다 — 공백은 전부 U+0020 이고, 가운데 줄표만 `–`(U+2013)다. ★ 블록 안의 포맷 결과에는 **보이지 않는 글자가 그대로** 들어 있다 — 바로 아래 줄의 코드 포인트가 그것을 읽어 준다.

```js
// js48b-50c-lookalike-space.js
// A formatted string compared with a string typed on a keyboard (every space in the typed strings is U+0020).
// Prints the formatted string as it is, its code points (non-ASCII only), and the comparisons.
const T = Date.UTC(2026, 8, 26, 15, 4, 5), T2 = Date.UTC(2026, 8, 26, 16, 5, 0);
const points = (s) => [...s].filter((c) => c.codePointAt(0) > 0x7e)
  .map((c) => "U+" + c.codePointAt(0).toString(16).toUpperCase().padStart(4, "0")).join(" ");
const time = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", timeStyle: "short" });
const probes = [
  ["[1] time.format(T)", time.format(T), "3:04 PM"],
  ["[2] time.formatRange(T, T2)", time.formatRange(T, T2), "3:04 – 4:05 PM"],
  ["[3] fr-FR NumberFormat 1234567.891", new Intl.NumberFormat("fr-FR").format(1234567.891), "1 234 567,891"],
];
for (const [label, got, typed] of probes) {
  console.log(label);
  console.log("    formatted                    " + got);
  console.log("    its non-ASCII code points    " + (points(got) || "(none)"));
  console.log("    === typed                    " + (got === typed));
  console.log("    every \\s -> U+0020, ===      " + (got.replace(/\s/g, " ") === typed));
}
console.log("[4] the literal parts of formatRangeToParts(T, T2)");
for (const p of time.formatRangeToParts(T, T2)) {
  if (p.type === "literal") console.log("    literal " + JSON.stringify(p.value).padEnd(8) + (points(p.value) || "(ASCII)") + "   source " + p.source);
}
```

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

```text
                              node 18 · node 20                     Chrome 151
   [1] format(T)              "3:04 PM"   U+0020  → === true         U+0020  → === true
   [2] formatRange(T, T2)     U+2009 – U+2009 … U+202F PM → false    U+0020 – U+0020 … U+0020 → true
   [3] fr-FR 숫자              U+202F 두 개 → false                   U+202F 두 개 → false
                              ────────── \s 를 U+0020 으로 바꾸면 여섯 칸 전부 true ──────────
```

- ★★★ **`[2]` 가 사고의 자리다** — node 두 판에서 `formatRange` 는 **U+2009(얇은 공백) – U+2009 … U+202F(좁은 줄바꿈 없는 공백) PM** 을 냈고 `=== typed` 가 **`false`** 다. **Chrome 151 은 같은 호출이 전부 U+0020** 이라 `true` 다. **같은 테스트가 node 에서만 깨진다.**
- ★★★ **같은 포맷터의 `format()`(`[1]`)은 node 에서도 U+0020** 이었다. 같은 ICU 를 쓰는 **한 객체의 두 메서드**가 갈렸으니, 이 차이는 **데이터가 아니라 그 위층**(엔진이 결과를 손보는 자리)에서 났다고 읽는다 — ★ **V8·node 소스는 읽지 않았다**(관찰에서 끌어낸 층 배정).
- ★★★ **`[3]` fr-FR 의 천 단위 구분은 세 판 다 U+202F** 다 — 이쪽은 엔진이 손대지 않았다. **숫자 쪽에도 같은 사고가 있다.**
- ★★ **`[4]` `formatRangeToParts`** 가 공백의 출처를 보여 준다 — `" – "` 와 `" "` 둘 다 **`source shared`** 인 literal 조각이다. ★ **비교는 조각의 `type`·`value` 로 하라** — 문자열 전체를 박으면 이런 글자까지 박힌다.
- ★★ **처방** — 기댓값을 같은 포맷터로 만들거나, **`\s` 를 U+0020 으로 접어서** 비교한다(`every \s -> U+0020` 여섯 칸 전부 `true` — `\s` 가 U+2009·U+202F 를 잡는다). ★ 접는 것은 **비교할 때만**이다 — 화면에 내보낼 문자열에서 지우면 줄바꿈 방지가 깨진다.

### (4) ★★ 손으로 만든 천 단위 구분 — `toFixed` + 쉼표 정규식 대 `NumberFormat`

**언제 쓰나** — `x.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")` 같은 한 줄을 금액 표시에 쓰려 할 때.

```js
// js48b-50d-hand-format.js
// A hand-written thousands formatter (toFixed + a comma regex) next to Intl.NumberFormat, row by row.
// The script counts, at the end, the rows where the hand-written column and the en-US column differ.
const byHand = (x, digits) => x.toFixed(digits).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
const en = (x, digits) => new Intl.NumberFormat("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(x);
const inr = (x, digits) => new Intl.NumberFormat("en-IN", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(x);
const rows = [
  ["1234.5", 1234.5, 2],
  ["-1234.5", -1234.5, 2],
  ["1234.5678", 1234.5678, 4],
  ["-0.001", -0.001, 2],
  ["1.005", 1.005, 2],
  ["2 ** 53 + 2", 2 ** 53 + 2, 0],
  ["1e21", 1e21, 0],
  ["12345678.9", 12345678.9, 1],
];
console.log("  " + "value".padEnd(13) + "digits  " + "by hand".padEnd(26) + "en-US".padEnd(30) + "en-IN");
let differ = 0;
for (const [label, x, d] of rows) {
  const h = byHand(x, d), e = en(x, d);
  if (h !== e) differ++;
  console.log("  " + label.padEnd(13) + String(d).padEnd(8) + h.padEnd(26) + e.padEnd(30) + inr(x, d));
}
console.log("rows where by hand and en-US differ: " + differ + " / " + rows.length);
```

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

```text
   손으로 만든 열 = toFixed(ECMA-262) → 정규식 — 로케일 데이터를 한 번도 안 읽는다

   1234.5678  toFixed(4) "1234.5678" ─ 정규식이 소수 쪽 "5678" 에도 걸린다 ─▶ "1,234.5,678"
   1e21       toFixed(0) "1e+21"     ─ 10^21 이상은 지수 표기가 돌아온다 ────▶ "1e+21"
   1.005      toFixed(2) "1.00"      ─ 저장된 값이 1.00499…(03번)           NumberFormat "1.01"
   en-IN      세 자리마다 쉼표라는 가정 자체가 틀린다 ──────────────────────▶ 12,34,567.891 을 못 만든다
```

- ★★★ **`rows where by hand and en-US differ: 3 / 8`** — `1234.5678`(**`1,234.5,678`** — 정규식이 소수부까지 묶었다) · `1e21`(**`1e+21`** — `toFixed` 가 10²¹ 이상에서 지수 표기를 돌려준다) · `1.005`(**`1.00` 대 `1.01`**).
- ★★★ **음수는 안 깨졌다** — `-1234.5` 가 두 열 다 `-1,234.50`. 정규식의 `\B` 가 부호와 첫 자리 사이를 **경계로 보기 때문**이다. ★ **「음수에서 깨진다」 는 이 정규식에서는 틀린 전제**였다(브리핑이 확인해 보라고 준 자리다).
- ★★ **`-0.001` 은 두 열 다 `-0.00`** — `NumberFormat` 도 음의 영을 부호째 적었다(이 판들의 관찰).
- ★★ **`1.005`** — 03번이 이미 잰 대로 `toFixed(2)` 는 `1.00` 이고(저장된 값이 `1.00499999999999989342`), **`NumberFormat` 은 같은 값을 `1.01`** 로 적었다. ★ 둘 중 어느 쪽이 「맞나」는 이 문서가 판정하지 않는다 — **두 도구의 반올림 입력이 다르다**는 것만 관찰이다.
- ★★ **en-IN 열** — `1,23,45,678.9` · `9,00,71,99,25,47,40,994` — 세 자리 뒤로 **두 자리씩** 묶는다. 「세 자리마다 쉼표」 정규식으로는 **원리상** 못 만든다.
- ★ 세 판이 **한 글자도 같았다**(아래 대조기) — 이 블록은 node 20 판 하나만 싣는다.

### (5) ★★ 인자 없는 호출은 환경을 읽는다 — `LANG` · `LC_ALL` · `TZ`

**언제 쓰나** — `toLocaleString()` 을 **인자 없이** 부른 코드가 서버·CI·개발자 노트북에서 다른 답을 낼 때.
★★ `LANG` 넷은 **`LC_ALL` 을 지운 채**(그래야 `LANG` 이 정한다) · 그다음 **`LANG=de_DE` + `LC_ALL=C.UTF-8`** 한 줄 · 그다음 `TZ` 둘.

```js
// js48b-50e-default-locale.js
// The calls that name no locale and no time zone. One line: default locale · time zone · three results.
// Look-alike spaces are written as <U+XXXX> (as in js48b-50b-format-cells.js).
const T = Date.UTC(2026, 8, 26, 15, 4, 5);
const lookalike = (n) => n === 0xA0 || (n >= 0x2000 && n <= 0x200F) || (n >= 0x2028 && n <= 0x202F);
const shown = (s) => [...s].map((c) => (lookalike(c.codePointAt(0))
  ? "<U+" + c.codePointAt(0).toString(16).toUpperCase().padStart(4, "0") + ">" : c)).join("");
const o = new Intl.DateTimeFormat().resolvedOptions();
console.log([
  o.locale.padEnd(6),
  o.timeZone.padEnd(17),
  shown((1234.5).toLocaleString()).padEnd(14),
  ["a", "z", "ä"].sort((x, y) => x.localeCompare(y)).join("").padEnd(4),
  shown(new Date(T).toLocaleString()),
].join("  "));
```

```sh
# js48b-50e-default-locale.sh
#!/usr/bin/env bash
# js48b-50e-default-locale.js on node20 and Chrome 151 under different environments:
#   four LANG values with LC_ALL unset (so LANG decides) and TZ=UTC · then LANG=de_DE.UTF-8 with LC_ALL=C.UTF-8 ·
#   then two TZ values with LANG=C.UTF-8.
# Columns: default locale · default time zone · (1234.5).toLocaleString() · sort by localeCompare · new Date(T).toLocaleString()
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
run() {   # run <runtime> <TZ> <LANG> <LC_ALL or -> 
  local out e
  if [ "$4" = - ]; then e=(env -u LC_ALL TZ="$2" LANG="$3"); else e=(env TZ="$2" LANG="$3" LC_ALL="$4"); fi
  if [ "$1" = node20 ]; then out="$("${e[@]}" "$N20" js48b-50e-default-locale.js)" || exit 1
  else out="$("${e[@]}" ./js48b-browser.sh js48b-50e-default-locale.js)" || exit 1; fi
  printf '  %-7s %-17s %-12s %-8s  %s\n' "$1" "$2" "$3" "$4" "$out"
}
echo "  runtime TZ                LANG         LC_ALL    locale  time zone          toLocaleString  sort  Date toLocaleString"
for r in node20 Chrome; do
  for l in C.UTF-8 de_DE.UTF-8 sv_SE.UTF-8 ko_KR.UTF-8; do run "$r" UTC "$l" -; done
  run "$r" UTC de_DE.UTF-8 C.UTF-8
  for z in Asia/Seoul America/New_York; do run "$r" "$z" C.UTF-8 -; done
done
```

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

```text
   환경 변수 ──▶ 기본 로케일 ──▶ toLocaleString() · localeCompare · Date#toLocaleString()
   LC_ALL 이 있으면 LC_ALL      ← LANG=de_DE 여도 LC_ALL=C.UTF-8 이면 en-US
   없으면 LANG
   TZ ──────▶ 기본 시간대 ──▶ 같은 T 가 9/26 3:04 PM · 9/27 12:04 AM · 9/26 11:04 AM
```

- ★★★ **같은 소스 · 같은 판 · 같은 시각인데 일곱 줄이 전부 다르다** — 인자 없는 호출은 **환경이 입력**이다.
- ★★★ **`LC_ALL` 이 `LANG` 을 이긴다** — `LANG=de_DE.UTF-8` 이어도 `LC_ALL=C.UTF-8` 이면 두 런타임 다 `en-US`.
- ★★ **`localeCompare` 도 기본 로케일을 탄다** — `sv_SE` 에서만 `azä`, 나머지는 `aäz`(동작 (2)의 `Collator sv` 와 같은 사전).
- ★★ **Chrome 은 태그를 `de`·`sv`·`ko` 로 줄였고** node 는 `de-DE`·`sv-SE`·`ko-KR` 이었다 — **출력 글자는 같았다.** 기본 로케일을 **문자열로 비교하는 코드**는 여기서 갈린다.
- ★★ **`TZ` 는 날짜 열만 바꾼다** — `Asia/Seoul` 에서는 **날짜가 9/27** 로 넘어갔다. 시간대 규칙 자체는 49번의 몫이다.
- ★ 스웨덴어 숫자의 묶음은 **`<U+00A0>`**(동작 (2)의 프랑스어 U+202F 와 다른 글자).

### (6) ★ 거절되는 인자 — 예외 이름은 같고 문구는 판마다

**언제 쓰나** — 사용자 입력(로케일 태그 · 통화 코드 · 시간대 이름)을 포맷터에 그대로 넘길 때.

```js
// js48b-50f-rejected-options.js
// Constructor calls with an argument the formatter may refuse: exception name and message, or the resolved value.
// Look-alike spaces are written as <U+XXXX> (as in js48b-50b-format-cells.js).
const lookalike = (n) => n === 0xA0 || (n >= 0x2000 && n <= 0x200F) || (n >= 0x2028 && n <= 0x202F);
const shown = (s) => [...s].map((c) => (lookalike(c.codePointAt(0))
  ? "<U+" + c.codePointAt(0).toString(16).toUpperCase().padStart(4, "0") + ">" : c)).join("");
const run = (label, f) => {
  let r;
  try { r = "ok " + f(); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(66) + shown(r));
};
run('NumberFormat("x-nope")', () => new Intl.NumberFormat("x-nope").resolvedOptions().locale);
run('NumberFormat("en_US")', () => new Intl.NumberFormat("en_US").resolvedOptions().locale);
run('NumberFormat("zz-ZZ")', () => new Intl.NumberFormat("zz-ZZ").resolvedOptions().locale);
run('NumberFormat("en", { style: "currency" })', () => new Intl.NumberFormat("en", { style: "currency" }).format(1));
run('NumberFormat("en", { style: "currency", currency: "EURO" })', () => new Intl.NumberFormat("en", { style: "currency", currency: "EURO" }).format(1));
run('NumberFormat("en", { style: "currency", currency: "XYZ" })', () => new Intl.NumberFormat("en", { style: "currency", currency: "XYZ" }).format(1));
run('NumberFormat("en", { style: "money" })', () => new Intl.NumberFormat("en", { style: "money" }).format(1));
run('DateTimeFormat("en", { timeZone: "Mars/Olympus" })', () => new Intl.DateTimeFormat("en", { timeZone: "Mars/Olympus" }).format(0));
run('DateTimeFormat("en", { timeStyle: "long", timeZoneName: "short" })', () => new Intl.DateTimeFormat("en", { timeStyle: "long", timeZoneName: "short" }).format(0));
run('RelativeTimeFormat("en").format(1, "fortnight")', () => new Intl.RelativeTimeFormat("en").format(1, "fortnight"));
```

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

- ★★★ **예외 이름은 열 줄 모두 세 판이 같다** — 태그 문법 오류 · 통화 코드 형식 오류 · 값 범위 밖 · 없는 시간대 · 없는 단위는 **`RangeError`**, 필요한 옵션 없음 · 같이 못 쓰는 옵션은 **`TypeError`**.
- ★★ **문구는 Chrome 만 두 줄이 달랐다** — 태그 오류(`Invalid language tag: x-nope` 대 `Incorrect locale information provided`)와 `timeStyle` + `timeZoneName`(**`Invalid option : option`** — 무엇이 틀렸는지 말하지 않는다). **문구를 근거로 분기하지 마라**(규칙 27).
- ★★★ **`en_US`(밑줄)는 `RangeError`** — BCP 47 태그는 **하이픈**이다. 환경 변수 `LANG` 의 모양(`ko_KR.UTF-8`)을 그대로 넘기면 여기서 막힌다.
- ★★★ **`currency: "XYZ"` 는 통과한다** — `XYZ<U+00A0>1.00`. 형식(영문 세 글자)만 보고 **그런 통화가 있는지는 안 본다.** `"EURO"`(네 글자)만 거절됐다.
- ★ `zz-ZZ` 는 예외가 아니라 **대체**(동작 (1)).

세 판 대조기 — 한 번씩 싣는 블록(동작 (3)·(4)·(6))이 세 판에서 같았나.

```sh
# js48b-50g-three-runtimes.sh
#!/usr/bin/env bash
# The single-run probes of this topic (js48b-50c, 50d, 50f) on node18, node20 and Chrome 151,
# all under TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8: is the output identical?
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
E=(env TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8)
same=0; differ=0
for f in js48b-50c-lookalike-space.js js48b-50d-hand-format.js js48b-50f-rejected-options.js; do
  a="$("${E[@]}" "$N18" "$f")" || exit 1
  b="$("${E[@]}" "$N20" "$f")" || exit 1
  c="$("${E[@]}" ./js48b-browser.sh "$f")" || exit 1
  [ "$a" = "$b" ] && x=identical || x=DIFFERS
  [ "$b" = "$c" ] && y=identical || y=DIFFERS
  for r in $x $y; do if [ $r = identical ]; then same=$((same + 1)); else differ=$((differ + 1)); fi; done
  printf '%-32s node18/node20 %-10s node20/Chrome %s\n' "$f" "$x" "$y"
done
echo "pairs identical $same · differ $differ"
```

```text
===== ./js48b-50g-three-runtimes.sh (exit=0) =====
js48b-50c-lookalike-space.js     node18/node20 identical  node20/Chrome DIFFERS
js48b-50d-hand-format.js         node18/node20 identical  node20/Chrome identical
js48b-50f-rejected-options.js    node18/node20 identical  node20/Chrome DIFFERS
pairs identical 4 · differ 2
```

- ★★ **node 18 과 node 20 은 세 파일 모두 `identical`** · Chrome 은 `50c`(공백)와 `50f`(문구)만 `DIFFERS` — 그래서 그 둘만 Chrome 블록을 따로 실었다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 층 | 어디서 봤나 |
|---|---|---|---|
| `new Intl.NumberFormat(loc, { style, currency, notation })` | 숫자 · 통화 · 퍼센트 · 단위 · `compact` | API ECMA-402 · 글자 데이터 판 | 동작 (2) |
| `new Intl.DateTimeFormat(loc, { dateStyle, timeStyle, timeZone })` | 시각을 글자로 — `format` · `formatRange` · `formatToParts` · `formatRangeToParts` | 〃 | 동작 (2)·(3) |
| `new Intl.ListFormat(loc, { type })` | `a, b, and c` · `a, b 및 c` | 〃 | 동작 (2) |
| `new Intl.RelativeTimeFormat(loc, { numeric })` | `-1, "day"` → `어제` · `1일 전` | 〃 | 동작 (2) |
| `new Intl.PluralRules(loc, { type })` | 수 → `one`·`two`·`few`·`other` 범주 | 〃 | 동작 (2) |
| `new Intl.Collator(loc).compare` | 언어의 사전 순 비교 — `sort` 에 넘긴다 | 〃 | 동작 (2) |
| `x.resolvedOptions().locale` | **실제로 쓰인** 로케일 — 대체를 드러내는 유일한 창 | ECMA-402 | 동작 (1) |
| `Intl.X.supportedLocalesOf([...])` | 그 중 데이터가 있는 태그 | ECMA-402 · 판 | 동작 (1) |
| 인자 없는 `toLocaleString()` · `localeCompare` | **기본 로케일**(환경) · 기본 시간대(`TZ`) | 호스트 | 동작 (5) |

## 어디서 틀리나

### (1) ★★★ 포맷 결과를 손으로 친 문자열과 `===` 로 비교한다

node 에서 `formatRange` 는 **U+2009 · U+202F**, fr-FR 숫자는 세 판 다 **U+202F** 였다(동작 (3)). 눈으로는 절대 안 보인다 — **코드 포인트를 찍어라.**

### (2) ★★★ 「판을 올려도 포맷은 같다」 · 「서버와 브라우저가 같은 글자를 낸다」

이 42칸에서는 node 두 판이 같았고 node 대 Chrome 이 3칸 갈렸다(동작 (2)). **같았던 것은 관찰이지 보장이 아니다** — ECMA-262 는 이 메서드를 ECMA-402 에 넘기고, 글자는 데이터 판의 것이다.

### (3) ★★★ 없는 로케일이 에러를 낼 거라고 믿는다

`zz-ZZ` 는 **조용히 `en-US`**, `de-ZZ` 는 **`de`**(동작 (1)). 대체를 알려면 `resolvedOptions().locale` 을 읽어야 한다.

### (4) ★★ `sort()` 로 이름을 정렬한다

코드 유닛 순이라 `ä` 가 `z` 뒤로 간다(동작 (2)). 언어의 순서는 `Intl.Collator` — 그리고 **언어마다 다르다**(de 는 a 곁, sv 는 끝).

### (5) ★★ `toFixed` + 쉼표 정규식

소수 넷째 자리 · `1e21` · `1.005` 에서 갈렸고 인도식 묶음은 못 만든다(동작 (4)). ★ 음수는 이 정규식에서 **안 깨졌다.**

### (6) ★★ 인자 없는 `toLocaleString()`

**`LC_ALL` → `LANG`** 과 `TZ` 가 답을 정한다(동작 (5)) — CI 와 개발자 노트북에서 다른 문자열이 나온다. 로케일과 `timeZone` 을 **명시**하라.

### (7) ★ `LANG` 값(`ko_KR.UTF-8`)을 로케일 태그로 넘긴다 · 통화 코드를 믿는다

밑줄 태그는 `RangeError`, 그런데 **`XYZ` 같은 없는 통화는 통과**한다(동작 (6)).

### (8) ★ 「1 이면 단수」를 코드에 박는다

한국어 `PluralRules` 는 1 도 `other`, 영어 서수는 22 가 `two` 다(동작 (2)).

## 구현 세부사항 대 언어 보장

### ECMA-262 보장

- ★★ `Number.prototype.toLocaleString` 은 **ECMA-402 를 구현하면 그쪽 명세를 따른다** · 아니면 **implementation-defined**(기준 소스).
- ★★ 비교 함수 없는 `sort()` 는 **코드 유닛 순**(`CompareArrayElements` → `IsLessThan`).
- ★ `toFixed` 의 결과(동작 (4)의 손으로 만든 열)는 로케일 데이터를 안 읽는다.

### ECMA-402(이 문서는 본문을 열지 않았다 — 관찰로 본 몫)

- ★★★ 세 판이 **같게** 낸 것 — 생성자와 옵션의 모양 · **예외의 종류**(`RangeError`/`TypeError`) · 없는 로케일의 **대체 방향** · `resolvedOptions()`.
- ★ 이것을 「ECMA-402 의 보장」으로 적으려면 그 명세의 절을 열어 확인해야 한다 — 이 문서는 그 단계를 하지 않았다.

### 로케일 데이터(CLDR · ICU 판)

- ★★★ **모든 출력 글자** — 구분자 · 공백의 종류 · 단어(`vorgestern` · `및`) · 어순 · `compact` 의 단위.
- ★★ 판 — node 18 ICU 74.2 / CLDR 44.1 · node 20 ICU 77.1 / CLDR 47.0 · Chrome 은 **못 잰 것.**

### 엔진 · 호스트 · 이 판의 관찰

- ★★★ **같은 ICU 인데 `format()` 은 U+0020, `formatRange()` 는 U+2009·U+202F**(node 두 판) · Chrome 은 둘 다 U+0020 — 엔진 층으로 읽는다(소스 미확인).
- ★★ 기본 로케일을 **`LC_ALL` → `LANG`** 에서 읽는 것 · Chrome 이 태그를 `de` 로 줄이는 것.
- ★ 예외 **문구**.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`Intl.NumberFormat` 은 어디서나 같은 문자열을 낸다」 → ○ 「**API 모양은 같고 글자는 데이터 판에 달렸다** — 이 42칸에서는 3칸이 갈렸다」
- ✗ 「시각 포맷에는 U+202F 가 들어간다」 → ○ 「**이 판들에서는** node 의 `formatRange` 에만 들어갔고 `format()` 과 Chrome 에는 없었다 · fr-FR 숫자 묶음은 세 판 다 U+202F」
- ✗ 「없는 로케일을 주면 `RangeError`」 → ○ 「**틀린 태그**는 `RangeError`, **없는 로케일**은 조용히 대체된다」
- ✗ 「`toFixed` + 정규식은 음수에서 깨진다」 → ○ 「이 정규식은 음수에서 멀쩡했고 **소수 넷째 자리 · `1e21`** 에서 깨졌다」

## 언제 쓰고 언제 안 쓰나

- **`Intl.*`** — 사람에게 보여 줄 숫자 · 금액 · 날짜 · 목록 · 상대 시간. **로케일과 `timeZone` 을 명시**하고, 대체가 걱정되면 `resolvedOptions().locale` 을 읽는다.
- **`Intl.Collator`** — 사람에게 보여 줄 목록의 정렬. ★ **기계용 키**(맵 키 · 이진 탐색의 기준)에는 코드 유닛 순이 맞다 — 로케일마다 순서가 바뀌면 안 되는 자리다.
- **`formatToParts` · `formatRangeToParts`** — 테스트 · 스타일링 · 파싱처럼 **조각이 필요한** 자리. 문자열 전체를 박지 않는다.
- ★ **안 쓰는 자리** — 기계가 다시 읽을 문자열(로그 · CSV · API 응답) — 거기는 ISO 8601 · 소수점 `.` 같은 **고정 형식**이다. 포맷 결과를 **다시 파싱**하는 설계도 피한다(동작 (3)의 공백이 그대로 들어온다).

## 핵심 문장

1. ★★★ **API 모양은 ECMA-402, 글자는 데이터 판** — 세 판의 42칸 중 **3칸**이 갈렸고, node 18(ICU 74.2)과 node 20(ICU 77.1)은 **한 칸도** 안 갈렸다(관찰).
2. ★★★ **node 의 `formatRange` 는 U+2009·U+202F 를 넣었고 같은 객체의 `format()` 은 U+0020** · fr-FR 숫자 묶음은 세 판 다 U+202F — **`=== typed` 가 `false`** 인 자리다. 코드 포인트로 확인하고 `formatToParts` 로 비교하라.
3. ★★★ **없는 로케일은 조용히 대체되고 틀린 태그만 `RangeError`** — `resolvedOptions().locale` 이 대체를 보는 유일한 창이다.
4. ★★ **`toFixed` + 쉼표 정규식은 소수 넷째 자리 · `1e21` · `1.005` 에서 갈리고 인도식 묶음을 못 만든다** — 음수에서는 멀쩡했다.
5. ★★ **인자 없는 호출은 환경이 입력이다** — `LC_ALL` → `LANG` 이 로케일을, `TZ` 가 날짜를 바꿨다.

## 관련 자료

- [ECMA-402](https://tc39.es/ecma402/)(이 문서는 본문을 열지 않았다) · [ECMA-262 2026](https://262.ecma-international.org/17.0/)
- [49 — `Date` 와 Temporal](../49-date-and-temporal/2-summary.md) — ★ **경계**: 시각 · 시간대 · 파싱은 거기. 여기는 **정해진 시각을 글자로 적는 것**.
- [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md) — `toFixed` 의 반올림과 저장된 값(거기 동작 (5)). [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) — `Intl.Segmenter` · 코드 유닛.
- [Python 49 — `datetime`·`zoneinfo`](../../../python/syntax/49-datetime-and-zoneinfo/2-summary.md) — 시간대 규칙의 교차 갈래 대비.

## 용어 풀이

- **ECMA-402** — ECMAScript 국제화 API 명세. `Intl` 이름공간과 `toLocaleString` 류의 동작을 정한다.
- **CLDR** — Unicode Common Locale Data Repository. 로케일마다 구분자 · 단어 · 어순을 담은 데이터.
- **ICU** — International Components for Unicode. CLDR 데이터를 읽어 실제로 포맷하는 라이브러리(V8 이 쓴다).
- **small-icu / full-icu** — ICU 데이터를 영어만 싣느냐 전부 싣느냐. 이 머신의 세 판은 모두 full(동작 (1)).
- **로케일 태그(BCP 47)** — `ko-KR` 처럼 하이픈으로 잇는 언어-지역 표기. 밑줄(`ko_KR`)은 POSIX 로케일의 모양이다.
- **로케일 대체(fallback)** — 데이터가 없는 태그를 받으면 더 짧은 태그나 기본 로케일로 내려가는 것.
- **U+00A0 / U+202F / U+2009** — 줄바꿈 없는 공백 · 좁은 줄바꿈 없는 공백 · 얇은 공백. 셋 다 눈에는 공백이고 `===` 에서는 U+0020 과 다르다. 정규식 `\s` 는 셋 다 잡는다.
- **`resolvedOptions()`** — 포맷터가 **실제로 고른** 로케일 · 옵션을 돌려주는 메서드.
- **기본 로케일** — 인자 없는 호출이 쓰는 로케일. 이 머신에서는 **`LC_ALL`, 없으면 `LANG`** 에서 왔다(동작 (5)).

## 더 들어가면

- **`Intl.DurationFormat`** — Chrome 151 에만 있다(동작 (1)). 두 node 판에서는 돌릴 수 없다.
- **node 대 Chrome 의 공백 차이가 어느 소스에서 나오나** — V8 · Chromium 소스는 읽지 않았다(층 배정은 관찰).
- **small-icu 빌드의 실제 출력** — 이 머신에 그런 빌드가 없어 **못 잰 것**이다(동작 (1)의 괄호).
