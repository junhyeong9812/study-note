# js/syntax/50 — `Intl` 국제화 포맷: 「같은 포맷 호출이 판마다 같은 글자를 내나 — 갈린다면 어느 층에서인가」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(시스템 ICU 74.2) · v20.19.6(ICU 77.1) · Google Chrome 151 · x86-64 Linux. 블록마다 `TZ`·`LANG`·`LC_ALL` 을 배너 또는 `.sh` 에 적었다.
>
> ★★★ **이 주제의 본체는 포맷 격자다** — 42칸 × 판 셋의 출력 문자열과 「판이 갈린 칸 N / M」. **2번 · 3번 · 7번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **어느 칸이 판마다 갈리나 · 갈린 것은 명세의 몫인가 데이터 판의 몫인가**
> ② ★★★ **눈에 같은 문자열이 `===` 에서 갈리는 자리**
> ③ ★★ **손으로 쓴 포맷 · 인자 없는 호출 · 거절되는 인자.**
>
> **선행** — [49](../49-date-and-temporal/2-summary.md) · [03](../03-numbers-and-bigint/2-summary.md) · [04](../04-strings-and-utf16/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **2번은 칸마다 글자를 다 맞히려 하지 마라** — 먼저 「**세 판이 같을까 다를까**」만 칸마다 적고, 다르다고 본 칸에 **무엇이** 다를지 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 글자가 다음 판에서 바뀌면 누구의 잘못인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 런타임은 어떤 로케일 데이터를 싣고 있나 (예측) ★★

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

- ★★ `[2]` 의 두 줄은 여덟 태그 중 무엇을 돌려주나? 세 판이 같은가?
- ★★★ `[3]` 에서 `zz-ZZ` · `de-ZZ` · `x-nope` 는 각각 무엇이 되나?
- ★ `[4]` 두 줄을 보고 small-icu 인지 full-icu 인지 말할 수 있나?

### 2. 포맷 격자 (예측) ★★★ 이 주제의 축

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

- ★★★ 마지막 줄 `cells where the runtimes differ: N / 42` 의 N 은? 갈리는 칸은 어느 행인가?
- ★★ `NumberFormat` 여섯 행 · `compact` 네 행의 글자는?
- ★★ `sort()` · `Collator de` · `Collator sv` 세 행의 순서는?

### 3. 포맷 결과와 손으로 친 문자열 (예측) ★★★

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

- ★★★ node 20 에서 `[1]`\~`[3]` 의 `=== typed` 와 `every \s -> U+0020, ===` 는 각각? Chrome 151 에서는?
- ★★ `[4]` 에서 literal 조각 넷의 코드 포인트는?

### 4. 손으로 만든 천 단위 구분 (예측) ★★

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

- ★★ 여덟 행에서 `by hand` 열과 `en-US` 열이 갈리는 행은? 마지막 줄의 수는?
- ★ `en-IN` 열의 `12345678.9` 는?

### 5. 인자 없는 호출과 환경 (예측) ★★

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

- ★★ `LANG` 네 줄의 `locale` · `toLocaleString` · `sort` 열은? `LC_ALL=C.UTF-8` 줄은?
- ★ `TZ` 두 줄의 마지막 열은? node 20 과 Chrome 은 어느 열에서 갈리나?

### 6. 거절되는 인자 (예측) ★

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

- ★ 열 줄 각각 예외가 나는가? 난다면 **이름**은? (문구는 판마다 다를 수 있다 — 이름만 적어도 된다)

### 7. 층을 가른다 (경계) ★★★

- ★★★ 2번 격자의 한 칸(예 — `currency de-DE EUR`)에서 **ECMA-402 가 정하는 것**과 **데이터 판이 정하는 것**을 갈라라. 이 문서가 ECMA-402 에 대해 「보장」이라고 쓰지 않는 이유는?

### 8. 같은 ICU 인데 두 메서드가 갈렸다 (왜) ★★

- ★★ node 에서 같은 포맷터의 `format()` 은 U+0020, `formatRange()` 는 U+202F 를 냈다. 이 차이를 **데이터가 아니라 그 위층**의 것으로 읽는 근거는 무엇인가? 그 읽기의 한계는?

### 9. 비교 함수 없는 `sort()` (왜) ★★

- ★★ 비교 함수 없는 `sort()` 에서 `ä` 가 `z` 뒤로 가는 이유를 ECMA-262 의 비교 연산으로 설명하라. `Collator sv` 가 우연히 같은 순서를 낸 것은 왜 우연인가?

### 10. 포맷 결과를 테스트에 박는다 (연결) ★★

- ★★ 스냅샷 테스트에 `formatRange` 결과를 문자열로 박았다. node 를 올리거나 브라우저에서 돌릴 때 무엇이 깨질 수 있나(3번 · 2번)? 무엇으로 비교해야 판이 올라도 덜 깨지나?

### 11. 시각과 글자 (연결) ★

- ★ 49번의 `Date` 와 견주어, `new Date(T).toLocaleString()`(5번)은 **무엇을** 환경에서 읽나? 서버 로그에 쓸 시각은 무엇으로 적어야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
