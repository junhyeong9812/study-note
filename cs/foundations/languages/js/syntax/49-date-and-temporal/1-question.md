# js/syntax/49 — `Date` 와 Temporal: 「같은 날짜 문자열이 시간대에 따라 다른 순간이 되나 — 월 번호·넘침·가변성·없는 시각은 누가 정하나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(ICU 74.2 · tzdata 2023c) · v20.19.6(ICU 77.1 · tzdata 2025b) · Google Chrome 151 · x86-64 Linux. ★ 모든 블록은 `TZ` 를 **명시**하고 돌렸다(이 머신의 기본은 `Asia/Seoul`).
>
> ★★★ **이 주제의 본체는 파싱 격자다** — 문자열 여섯 × 판 셋 × `TZ` 셋. **1번 · 9번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **문자열 하나가 어느 순간이 되나 — 누가 정하나**(명세의 ISO 형식 / 엔진의 휴리스틱 / 시간대)
> ② ★★ **`Date` 의 세 함정** — 0 기반 월과 넘침 · 가변성 · 서머타임 전이의 없는 시각·두 번 있는 시각
> ③ ★★ **Temporal 이 무엇을 바꾸나 — 그리고 지금 어느 판에 있나.**
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(`Date` 는 원시가 아니라 **객체**다 — 4번 · 11번의 전제).

## 이 파일을 푸는 법

- ★★ **예측형 문항은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸마다 「UTC 자정에서 몇 시간」(`+0h` · `-9h` · `+4h`)이나 `Invalid Date` 만** 먼저 적어도 된다 — 13자리 숫자를 외울 필요는 없다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 값은 명세가 정했나, 엔진이 정했나, tzdata 가 정했나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 문자열 여섯 × 시간대 셋 × 판 셋 (예측) ★★★ 이 주제의 축

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

- ★★★ 여섯 문자열 × 세 `TZ` 의 열여덟 칸은 각각 `+?h` 인가 `Invalid Date` 인가?
- ★★★ 마지막 두 줄의 `N / 6` 과 `N / 18` 은?

### 2. ISO 형식처럼 생긴 문자열 일곱 (경계) ★★

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

- ★★ `TZ=Asia/Seoul` 에서 일곱 줄은 각각 무엇이 되나? 그중 **ECMA-262 가 값을 정해 둔 줄**은 어느 것이고, 나머지는 누가 정했나?

### 3. 숫자로 만든 `Date` (예측) ★★

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

- ★★ `TZ=UTC` 에서 여덟 날짜와 마지막 세 숫자는?

### 4. 한 `Date` 를 여러 자리에서 (예측) ★★

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

- ★★ `[1]`\~`[6]` 여섯 줄은?

### 5. 뉴욕의 2026년 두 전이 (예측) ★★★

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

- ★★★ `[1]` 의 여섯 줄 — 각 벽시계는 몇 시 `Z` 가 되고 몇 시로 읽혀 돌아오나?
- ★★ `[2]` 의 `01:30` 은 오프셋이 몇 시간인가? `[3]` 의 두 줄은 같은가?

### 6. Temporal 은 어느 판에 있나 (예측) ★★★

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

- ★★★ 다섯 번의 실행은 각각 무엇을 찍고 어떤 종료 코드로 끝나나? 마지막 줄의 `N / 5` 는?

### 7. Temporal 에게 같은 질문 (예측) ★★

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

- ★★ Chrome 151 의 `[1]`\~`[6]` 은? 특히 `[2]` 의 네 줄 · `[3]` 의 `jan31` 두 줄 · `[5]` 의 다섯 줄 · `[6]` 의 앞 두 줄.
- ★ node20 `--harmony-temporal` 은 어느 줄에서 Chrome 과 갈리나 — 값인가, 문구인가?

### 8. 날짜만 쓴 문자열과 시각까지 쓴 문자열 (왜) ★★

- ★★ 1번에서 `"2026-09-26"` 과 `"2026-09-26T00:00"` 의 칸이 `TZ` 에 따라 **어떻게 움직였든**, 두 문자열을 가르는 규칙을 ECMA-262 의 한 문장으로 설명하라.

### 9. 요약 줄을 어디까지 믿나 (경계) ★★★

- ★★★ 1번 마지막 줄의 `N / 18` 이 무엇이었든, 그 줄 하나로 「`Date` 파싱이 판에 따라 흔들리는가」에 답할 수 있나? 이 격자가 **못 보는 것**은 무엇이고, 그 대신 무엇으로 물을 수 있나?

### 10. 파이썬 `fold` · `Date` · Temporal 의 `02:30` (연결) ★★

- ★★ [Python 49](../../../python/syntax/49-datetime-and-zoneinfo/2-summary.md)의 갭 격자에서 `02:30;0` 은 무엇이었나? 5번의 `Date` 와 7번의 Temporal `(no option)` 은 그것과 같은 답인가 — 같다면 **경로**는 어떻게 다른가?

### 11. `Object.freeze` 와 날짜 객체 (왜) ★★

- ★★ 4번 `[5]` 의 결과를 `Date` 가 값을 어디에 두는지로 설명하라. 7번 `[3]` 의 `jan31` 두 줄과 `Object.isFrozen(jan31)` 줄을 함께 놓으면 무엇을 알 수 있나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
