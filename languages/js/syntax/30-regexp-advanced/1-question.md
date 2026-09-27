# js/syntax/30 — 정규식 심화: 「그룹·둘러보기·유니코드·엔진」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(헤드리스) · go1.27.1 · Python 3.12.3 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다. 배너가 `./js28b-30?-….sh` 인 블록은 **셸 탐침**이다 — `timeout`·`go`·`python3` 을 부르고 결과를 참/거짓으로 거른다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.** 5번(입력 길이 × 엔진의 「2초 안에 끝났나」)과 6번(V8 이 센 되돌이 수)이 중심이다.
> ★★★ **이 파일의 어느 답에도 경과 시간은 없다** — 블록이 시간을 한 숫자도 찍지 않는다. 「몇 초 걸린다」가 떠오르면 「**블록에 없다**」라고 적어라.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **그룹과 둘러보기는 매치 결과에 무엇을 남기나**
> ② **`u`·`v` 는 서로게이트와 문자 집합을 어떻게 보나**
> ③ ★★★ **같은 패턴이 엔진에 따라 끝나나 안 끝나나 — 그리고 명세와 엔진의 몫은 어디서 갈리나.**
>
> ★★ **예외는 타입과 메시지로만 답한다.**
>
> **선행** — [29 — 정규식 기본](../29-regexp-basics/2-summary.md) · [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) · [28 — `String` 메서드와 템플릿 리터럴](../28-string-methods-and-template-literals/2-summary.md) · [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md).
> ★★★ **04번의 쪼개기 그림을 먼저 떠올려라** — BMP 밖 이모지 하나를 `split('')` 으로 자르면 몇 조각이었나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번·2번은 매치 배열을 칸마다 적어라** — `<undefined>` 인 칸이 어디인가.
- ★★★ **3번은 줄마다 세 칸(플래그 없음 · `u` · `v`)을 적고, 마지막 줄의 수까지 세어 본다.**
- ★★★ **5번은 칸마다 yes/no 를 적어라.** 끝난 칸은 답(`true`/`false`)도.
- ★★★ **6번은 표의 모양을 적어라** — 비율 칸이 어디로 가나, 두 번째 패턴은 어떤가.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 캡처·비캡처·명명 그룹이 매치 결과에 남기는 것 (예측) ★★★

```js
// js28b-30a-groups.js
// Capturing, non-capturing and named groups -- what does the match object hold?
const J = (x) => JSON.stringify(x);
const U = (a) => [...a].map((v) => (v === undefined ? "<undefined>" : v));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(46) + f()); }
  catch (e) { console.log("  " + label.padEnd(46) + e.constructor.name + " 「" + e.message + "」"); }
};
const s = "2026-09-26";

console.log("[1] the same date, grouped three ways");
show("/(\\d+)-(\\d+)-(\\d+)/.exec(s)", () => J(U(/(\d+)-(\d+)-(\d+)/.exec(s))));
show("/(?:\\d+)-(\\d+)-(?:\\d+)/.exec(s)", () => J(U(/(?:\d+)-(\d+)-(?:\d+)/.exec(s))));
const m = /(?<y>\d{4})-(?<mo>\d{2})-(?<d>\d{2})/.exec(s);
show("named -- the array part", () => J(U(m)));
show("named -- m.groups", () => J(m.groups));
show("named -- m.groups.mo", () => m.groups.mo);

console.log("");
console.log("[2] the groups object itself");
show("Object.getPrototypeOf(m.groups) === null", () => Object.getPrototypeOf(m.groups) === null);
show("'toString' in m.groups", () => "toString" in m.groups);
show("String(m.groups)", () => String(m.groups));
show("JSON.stringify(m.groups)", () => J(m.groups));
show("groups when the pattern has no named group", () => String(/(\d+)/.exec(s).groups));
show("key order of /(?<b>x)(?<a>y)/", () => J(Object.keys(/(?<b>x)(?<a>y)/.exec("xy").groups)));

console.log("");
console.log("[3] an optional group -- /(?<a>a)?(?<b>b)/.exec('b')");
const opt = /(?<a>a)?(?<b>b)/.exec("b");
show("array", () => J(U(opt)));
show("Object.keys(groups)", () => J(Object.keys(opt.groups)));
show("groups.a", () => String(opt.groups.a));
show("'a' in groups", () => "a" in opt.groups);

console.log("");
console.log("[4] a group inside a quantifier");
show("/(\\w)+/.exec('abc')", () => J(U(/(\w)+/.exec("abc"))));
show("/(?:(a)|b)+/.exec('ab')", () => J(U(/(?:(a)|b)+/.exec("ab"))));
show("/(?:(a)|(b))+/.exec('ab')", () => J(U(/(?:(a)|(b))+/.exec("ab"))));

console.log("");
console.log("[5] referring back to a group");
show("/(?<q>['\"]).*?\\k<q>/.exec(`say \"hi\" 'yo'`)", () => J(U(/(?<q>['"]).*?\k<q>/.exec(`say "hi" 'yo'`))));
show("/(a)|\\1b/.exec('b')", () => J(U(/(a)|\1b/.exec("b"))));
show("s.replace(named, '$<d>.$<mo>.$<y>')", () => s.replace(/(?<y>\d{4})-(?<mo>\d{2})-(?<d>\d{2})/, "$<d>.$<mo>.$<y>"));
show("callback -- typeof the last argument", () => {
  let last;
  s.replace(/(?<y>\d{4})/, (...args) => { last = args[args.length - 1]; return ""; });
  return typeof last + " " + J(last);
});

console.log("");
console.log("[6] \\k and group names at the edges");
show("new RegExp('\\\\k<z>').test('k<z>')", () => new RegExp("\\k<z>").test("k<z>"));
show("new RegExp('\\\\k<z>', 'u')", () => String(new RegExp("\\k<z>", "u")));
show("new RegExp('(?<a>x)\\\\k<z>')", () => String(new RegExp("(?<a>x)\\k<z>")));
show("new RegExp('(?<a>x)(?<a>y)')", () => String(new RegExp("(?<a>x)(?<a>y)")));
show("new RegExp('(?<1a>x)')", () => String(new RegExp("(?<1a>x)")));
```

- ★★ `[1]` 다섯 줄 — 비캡처 쪽의 배열은 몇 칸인가? 명명 그룹 쪽의 배열 부분은?
- ★★★ `[2]` 여섯 줄 — `groups` 의 프로토타입은? `String(m.groups)` 는 무엇을 내놓나?
- ★★ `[2]` 명명 그룹이 없는 패턴의 `groups` 는 무엇인가?
- ★★ `[3]` `Object.keys(groups)` 와 `'a' in groups` 는?
- ★★★ `[4]` 세 줄 — 특히 `/(?:(a)|b)+/.exec('ab')` 의 1번 칸은 무엇인가?
- ★★ `[5]` `/(a)|\1b/.exec('b')` 는 무엇을 내놓나? 콜백의 마지막 인자는 무엇인가?
- ★★★ `[6]` 다섯 줄 — `\k<z>` 는 어느 줄에서 통과하고 어느 줄에서 막히나? 막히면 문구까지.

### 2. 둘러보기가 보는 것, 먹는 것, 읽는 방향 (예측) ★★★

```js
// js28b-30b-lookaround.js
// Lookahead and lookbehind -- what they match, what they consume, and which direction they read.
const J = (x) => JSON.stringify(x);
const U = (a) => (a === null ? null : [...a].map((v) => (v === undefined ? "<undefined>" : v)));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + f()); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};
const t = "30 USD, 45 EUR, $12, 7";

console.log("[1] four lookarounds on t = " + J(t));
show("t.match(/\\d+(?= USD)/g)", () => J(t.match(/\d+(?= USD)/g)));
show("t.match(/\\b\\d+\\b(?! USD)/g)", () => J(t.match(/\b\d+\b(?! USD)/g)));
show("t.match(/(?<=\\$)\\d+/g)", () => J(t.match(/(?<=\$)\d+/g)));
show("t.match(/(?<!\\$)\\b\\d+/g)", () => J(t.match(/(?<!\$)\b\d+/g)));

console.log("");
console.log("[2] how much does a lookaround consume?");
const z = /(?=b)/.exec("abc");
show("/(?=b)/.exec('abc') -- index, [0]", () => z.index + " " + J(z[0]));
show("'abc'.replace(/(?=b)/, '|')", () => "abc".replace(/(?=b)/, "|"));
show("'1234567'.replace(/\\B(?=(\\d{3})+$)/g, ',')", () => "1234567".replace(/\B(?=(\d{3})+$)/g, ","));
show("/(?=(a+))/.exec('baaa')", () => J(U(/(?=(a+))/.exec("baaa"))));

console.log("");
console.log("[3] lookbehind of varying length");
show("/(?<=\\$\\d+\\.)\\d+/.exec('cost $12.50')", () => J(U(/(?<=\$\d+\.)\d+/.exec("cost $12.50"))));
show("/(?<=^a+)b/.test('aaaab')", () => /(?<=^a+)b/.test("aaaab"));
show("/(?<=a|bc)x/g on 'ax bcx cx'", () => J("ax bcx cx".match(/(?<=a|bc)x/g)));

console.log("");
console.log("[4] groups inside a lookbehind -- '1053'");
show("/(?<=(\\d+)(\\d+))$/.exec('1053')", () => J(U(/(?<=(\d+)(\d+))$/.exec("1053"))));
show("/(?<=(\\d+?)(\\d+))$/.exec('1053')", () => J(U(/(?<=(\d+?)(\d+))$/.exec("1053"))));
show("/((\\d+)(\\d+))$/.exec('1053')", () => J(U(/((\d+)(\d+))$/.exec("1053"))));

console.log("");
console.log("[5] several conditions on one string: /^(?=.*\\d)(?=.*[a-z])\\S{6,}$/");
const rule = /^(?=.*\d)(?=.*[a-z])\S{6,}$/;
for (const w of ["abc123", "abcdef", "123456", "ab1", "ABC123", "abc 123"]) show(J(w), () => rule.test(w));
```

- ★★ `[1]` 네 줄의 배열을 적어라. `(?! USD)` 줄에 `30` 이 있나?
- ★★★ `[2]` `(?=b)` 의 `index` 와 `[0]`, 그리고 `replace` 두 줄의 결과는?
- ★★ `[2]` `/(?=(a+))/.exec('baaa')` 는 몇 칸이고 각 칸은?
- ★★★ `[3]` 세 줄 — 길이가 정해지지 않은 룩비하인드를 이 엔진은 받는가?
- ★★★ `[4]` 세 줄 — 같은 `(\d+)(\d+)` 가 룩비하인드 안과 밖에서 각각 무엇을 잡나?
- ★ `[5]` 여섯 입력 중 `true` 는 어느 것인가?

### 3. 한 글자를 세 가지 플래그로 (예측) ★★★

```js
// js28b-30c-unicode.js
// One astral character against a regexp -- without a flag, with u, with v.
// The character is built at run time and printed only as code units, so this file holds no astral text.
const J = (x) => JSON.stringify(x);
const units = (s) => (s === null || s === undefined ? String(s)
  : "[" + Array.from({ length: s.length }, (_, i) => s.charCodeAt(i).toString(16)).join(" ") + "]");
const mk = (src, flags) => { try { return new RegExp(src, flags); } catch (e) { return e; } };
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + f()); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};
const face = String.fromCodePoint(0x1f600);
const hi = face.slice(0, 1);
let rows = 0, split = 0;
const test3 = (src, input) => {
  const cells = ["", "u", "v"].map((fl) => {
    const r = mk(src, fl);
    return r instanceof Error ? r.constructor.name : String(r.test(input));
  });
  rows += 1; if (cells[0] !== cells[1]) split += 1;
  return ["-", "u", "v"].map((fl, i) => fl + ":" + cells[i]).join("  ");
};

console.log("[1] the input");
show("face = String.fromCodePoint(0x1f600)", () => "length " + face.length + "  units " + units(face));

console.log("");
console.log("[2] the same pattern, three flag settings (no flag / u / v)");
show("^.$ on face", () => test3("^.$", face));
show("^..$ on face", () => test3("^..$", face));
show("^[face]$ on face", () => test3("^[" + face + "]$", face));
show("^face{2}$ on face+face", () => test3("^" + face + "{2}$", face + face));
show("^\\S$ on face", () => test3("^\\S$", face));
show("high half alone, on face", () => test3(hi, face));
show("^.$ on the high half alone", () => test3("^.$", hi));
console.log("  rows where no-flag and u differ: " + split + " / " + rows);

console.log("");
console.log("[3] what did . take?");
show("face.match(/./)[0]", () => units(face.match(/./)[0]));
show("face.match(/./u)[0]", () => units(face.match(/./u)[0]));
show("(face + 'x').match(/./g).length", () => (face + "x").match(/./g).length);
show("(face + 'x').match(/./gu).length", () => (face + "x").match(/./gu).length);
show("face.split(/(?:)/)", () => face.split(/(?:)/).map(units).join(" "));
show("face.split(/(?:)/u)", () => face.split(/(?:)/u).map(units).join(" "));

console.log("");
console.log("[4] the escape \\u{1F600}");
show("/\\u{1F600}/u.test(face)", () => /\u{1F600}/u.test(face));
show("/\\u{1F600}/.test(face)", () => /\u{1F600}/.test(face));
show("/\\u{1F600}/.test('u{1F600}')", () => /\u{1F600}/.test("u{1F600}"));
show("/^\\u{3}$/.test('uuu')", () => /^\u{3}$/.test("uuu"));

console.log("");
console.log("[5] unicode property escapes \\p{...}");
const hangul = String.fromCharCode(0xd55c);
const eAcute = String.fromCharCode(0xe9);
show("/\\p{L}/u on 'a' / e-acute / hangul / '1'", () => ["a", eAcute, hangul, "1"].map((c) => /\p{L}/u.test(c)).join(" "));
show("/\\p{Script=Hangul}/u on hangul / 'a'", () => [hangul, "a"].map((c) => /\p{Script=Hangul}/u.test(c)).join(" "));
show("/\\p{L}/ (no flag) on 'p{L}' / 'a'", () => ["p{L}", "a"].map((c) => /\p{L}/.test(c)).join(" "));
show("new RegExp('\\\\p{Nope}', 'u')", () => String(new RegExp("\\p{Nope}", "u")));
show("/^\\p{Emoji}$/u on face / '1'", () => [face, "1"].map((c) => /^\p{Emoji}$/u.test(c)).join(" "));
```

- ★★★ `[2]` 일곱 줄마다 세 칸(`-` · `u` · `v`)을 적어라. 마지막 줄의 N / M 은?
- ★★ `[2]` 끝에서 두 줄(`high half alone, on face` · `^.$ on the high half alone`)은 각각?
- ★★ `[3]` 여섯 줄 — `.` 이 가져간 코드 유닛과 개수 두 줄.
- ★★★ `[4]` 네 줄 — 플래그 없는 `\u{1F600}` 과 `\u{3}` 은 각각 무엇으로 읽히나?
- ★★★ `[5]` `/\p{L}/`(플래그 없음) 줄은 무엇을 내놓나? 모르는 속성 이름은?
- ★ 이 블록을 node18 로 돌려도 같은가?

### 4. `v` 플래그를 `u` 와 나란히 (예측) ★★

```js
// js28b-30d-vflag.js
// The v flag -- set operations, strings inside a class, and what v refuses that u accepts.
// Every v pattern is built with new RegExp so that an engine without v still runs the whole file.
const units = (s) => "[" + Array.from({ length: s.length }, (_, i) => s.charCodeAt(i).toString(16)).join(" ") + "]";
const show = (label, f) => {
  try { console.log("  " + label.padEnd(46) + f()); }
  catch (e) { console.log("  " + label.padEnd(46) + e.constructor.name + " 「" + e.message + "」"); }
};
const eAcute = String.fromCharCode(0xe9);
const hangul = String.fromCharCode(0xd55c);
const face = String.fromCodePoint(0x1f600);
const family = String.fromCodePoint(0x1f468, 0x200d, 0x1f469, 0x200d, 0x1f467);
const on = (src, flags, inputs) => { const r = new RegExp(src, flags); return inputs.map((c) => r.test(c)).join(" "); };

console.log("[1] set operations -- inputs 'a' / e-acute / hangul / '1'");
const four = ["a", eAcute, hangul, "1"];
show("^[\\p{L}--\\p{ASCII}]$  v", () => on("^[\\p{L}--\\p{ASCII}]$", "v", four));
show("^[\\p{L}&&\\p{ASCII}]$  v", () => on("^[\\p{L}&&\\p{ASCII}]$", "v", four));
show("^[\\p{L}--\\p{ASCII}]$  u", () => on("^[\\p{L}--\\p{ASCII}]$", "u", four));
show("^[[a-z]--[aeiou]]+$  v   on 'rhythm' / 'rain'", () => on("^[[a-z]--[aeiou]]+$", "v", ["rhythm", "rain"]));

console.log("");
console.log("[2] strings in a class -- family = " + units(family) + "  (length " + family.length + ")");
show("^\\p{RGI_Emoji}$  v   on family / face", () => on("^\\p{RGI_Emoji}$", "v", [family, face]));
show("^\\p{Emoji}$      u   on family / face", () => on("^\\p{Emoji}$", "u", [family, face]));
show("^\\p{RGI_Emoji}$  u", () => on("^\\p{RGI_Emoji}$", "u", [family]));
show("^[\\q{abc|d}]$    v   on 'abc' / 'd' / 'a'", () => on("^[\\q{abc|d}]$", "v", ["abc", "d", "a"]));
show("family.match(v)[0]  for [\\p{RGI_Emoji}]", () => units(family.match(new RegExp("[\\p{RGI_Emoji}]", "v"))[0]));

console.log("");
console.log("[3] the same source under u and under v");
let total = 0, onlyU = 0;
for (const src of ["[(]", "[a-]", "[|]", "[a&&&b]", "[\\-]"]) {
  const r = (fl) => { try { new RegExp(src, fl); return "ok"; } catch (e) { return e.constructor.name; } };
  total += 1; if (r("u") === "ok" && r("v") !== "ok") onlyU += 1;
  show(src, () => "u:" + r("u") + "  v:" + r("v"));
}
console.log("  sources accepted under u but not under v: " + onlyU + " / " + total);
show("new RegExp('[(]', 'v') -- message", () => String(new RegExp("[(]", "v")));
show("new RegExp('a', 'uv')", () => String(new RegExp("a", "uv")));

console.log("");
console.log("[4] the flag's properties");
show("new RegExp('a', 'v').unicodeSets / .unicode", () => { const r = new RegExp("a", "v"); return r.unicodeSets + " / " + r.unicode; });
show("new RegExp('a', 'v').flags", () => new RegExp("a", "v").flags);
```

- ★★ `[1]` 네 줄 — 셋째 줄(`u` 로 같은 집합 연산)은 무엇을 내놓나?
- ★★★ `[2]` 가족 이모지에 `\p{RGI_Emoji}`(`v`)와 `\p{Emoji}`(`u`)는 각각?
- ★★ `[2]` `\p{RGI_Emoji}` 를 `u` 로 쓰면?
- ★★★ `[3]` 다섯 소스마다 `u:` · `v:` 두 칸, 그리고 마지막 줄의 N / M 은?
- ★ `[4]` `unicode` 와 `unicodeSets` 는 각각?

### 5. 입력을 늘려 가며 2초 제한을 걸면 (예측) ★★★ 이 주제의 축

```js
// js28b-30-h-explode.js
// 인자 n 과 플래그로 /^(a+)+$/ 를 "a" * n + "!" 에 한 번 던진다. js28b-30x-explode.sh 가 시간 제한을 걸고 부른다.
const n = Number(process.argv[2]);
const flags = process.argv[3] || "";
console.log(new RegExp("^(a+)+$", flags).test("a".repeat(n) + "!"));
```

```go
// js28b-30-h-re2.go
// 인자 n 으로 같은 패턴을 Go 의 regexp(RE2)에 한 번 던진다. js28b-30x-explode.sh 가 빌드해서 부른다.
package main

import (
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"
)

func main() {
	n, _ := strconv.Atoi(os.Args[1])
	re := regexp.MustCompile(`^(a+)+$`)
	fmt.Println(re.MatchString(strings.Repeat("a", n) + "!"))
}
```

```python
# js28b-30-h-re.py
# 인자 n 으로 같은 패턴을 파이썬 re 에 한 번 던진다. js28b-30x-explode.sh 가 시간 제한을 걸고 부른다.
import re
import sys

n = int(sys.argv[1])
print(re.search(r"^(a+)+$", "a" * n + "!") is not None)
```

```sh
# js28b-30x-explode.sh
#!/usr/bin/env bash
# /^(a+)+$/ 를 "a" * n + "!" 에 -- 엔진마다 n 을 늘려 「2초 안에 끝났나」만 참거짓으로 적는다.
# ★ 경과 시간은 찍지 않는다. 끝난 칸은 답(매치 여부)도 함께 확인한다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
GO="$HOME/.local/opt/go/bin/go"
LIMIT=2
BIN="$PWD/build-30"
mkdir -p "$BIN"
"$GO" build -o "$BIN/re2" js28b-30-h-re2.go || { echo "go build failed"; exit 1; }

cols=("node18" "node20" "node20 l-flag" "node20 fallback" "go RE2" "python3 re")
run() {   # run <열 번호> <n>
  case $1 in
    0) timeout "$LIMIT" "$N18" js28b-30-h-explode.js "$2" ;;
    1) timeout "$LIMIT" "$N20" js28b-30-h-explode.js "$2" ;;
    2) timeout "$LIMIT" "$N20" --enable-experimental-regexp-engine js28b-30-h-explode.js "$2" l ;;
    3) timeout "$LIMIT" "$N20" --enable-experimental-regexp-engine-on-excessive-backtracks js28b-30-h-explode.js "$2" ;;
    4) timeout "$LIMIT" "$BIN/re2" "$2" ;;
    5) timeout "$LIMIT" python3 js28b-30-h-re.py "$2" ;;
  esac
}
NS="10 20 30 40 1000"
printf '  %-6s' "n"; for c in "${cols[@]}"; do printf '%-17s' "$c"; done; echo
declare -A first
done_cells=0; cut_cells=0; wrong=0
for n in $NS; do
  printf '  %-6s' "$n"
  for i in 0 1 2 3 4 5; do
    out="$(run "$i" "$n" 2>&1)"; rc=$?
    if [ "$rc" -eq 124 ]; then cell="no"; cut_cells=$((cut_cells + 1)); [ -z "${first[$i]:-}" ] && first[$i]="$n"
    elif [ "$rc" -eq 0 ]; then cell="yes ($out)"; done_cells=$((done_cells + 1)); case $out in false|False) ;; *) wrong=$((wrong + 1)) ;; esac
    else cell="exit $rc"; fi
    printf '%-17s' "$cell"
  done
  echo
done
echo ""
for i in 0 1 2 3 4 5; do printf '  %-17s first n that did not finish: %s\n' "${cols[$i]}" "${first[$i]:-none}"; done
echo ""
echo "finished within ${LIMIT}s: $done_cells / $((done_cells + cut_cells))   ·   finished with a wrong answer: $wrong"
```

- ★★★ 다섯 행 × 여섯 열의 yes/no 를 전부 적어라. 끝난 칸의 답은?
- ★★★ 열마다 「처음 끝나지 않은 n」은? 그 값을 **몇 자리 수까지** 말할 수 있나?
- ★★ 마지막 줄의 두 수는?
- ★★ Go 쪽은 왜 `go run` 이 아니라 `go build` 한 실행 파일에 `timeout` 을 거나?
- ★ 이 블록으로 「n 이 하나 늘면 몇 배 느려지나」를 말할 수 있나?

### 6. V8 의 되돌이 한도 K 를 이분 탐색하면 (예측) ★★★

```js
// js28b-30-h-steps.js
// 인자 (패턴, n) -- 패턴을 "a" * n + "!" 에 한 번 던진다. js28b-30y-steps.sh 가 V8 의 되돌이 한도 플래그를 걸고 부른다.
console.log(new RegExp(process.argv[2]).test("a".repeat(Number(process.argv[3])) + "!"));
```

```sh
# js28b-30y-steps.sh
#!/usr/bin/env bash
# 시간 대신 「스텝」 -- V8 에게 「되돌이(backtrack)를 K 번 넘기면 선형 엔진으로 갈아타라」고 시키고,
# 갈아탔다는 추적 줄이 나왔나(참거짓)만 본다. K 를 이분 탐색해 「갈아타지 않는 가장 작은 K」를 n 마다 찾는다.
# ★ 추적 줄에는 주소가 박히므로 줄 자체는 싣지 않는다 -- 나왔나/안 나왔나만 쓴다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
fell_back() {   # fell_back <node> <K> <패턴> <n>  -> 0 이면 갈아탔다
  local out
  out="$("$1" --enable-experimental-regexp-engine-on-excessive-backtracks --regexp-backtracks-before-fallback="$2" \
         --trace-experimental-regexp-engine js28b-30-h-steps.js "$3" "$4" 2>&1)"
  case $out in *"Experimental execution"*) return 0 ;; *) return 1 ;; esac
}
smallest_k() {  # smallest_k <node> <패턴> <n>   (1 .. 2^22 범위)
  local lo=0 hi=4194304 mid
  while [ $((hi - lo)) -gt 1 ]; do
    mid=$(((lo + hi) / 2))
    if fell_back "$1" "$mid" "$2" "$3"; then lo=$mid; else hi=$mid; fi
  done
  echo "$hi"
}
table() {       # table <node> <패턴> <n 목록>
  local prev="" k
  printf '  %-7s %-28s %s\n' "n" "smallest K with no fallback" "ratio to the row above"
  for n in $3; do
    k="$(smallest_k "$1" "$2" "$n")"
    if [ -n "$prev" ]; then r="$(awk -v a="$k" -v b="$prev" 'BEGIN { printf "%.2f", a / b }')"; else r="-"; fi
    printf '  %-7s %-28s %s\n' "$n" "$k" "$r"
    prev="$k"
  done
}
echo "[1] node20  /^(a+)+\$/"
t20="$(table "$N20" '^(a+)+$' "1 2 3 4 5 6 7 8 9 10 11 12")"; printf '%s\n' "$t20"
echo ""
echo "[2] node20  /^a+\$/  (the same language, no nested quantifier)"
table "$N20" '^a+$' "1 10 100 1000 10000"
echo ""
echo "[3] node18  /^(a+)+\$/ -- is the table the same as [1]?"
t18="$(table "$N18" '^(a+)+$' "1 2 3 4 5 6 7 8 9 10 11 12")"
if [ "$t18" = "$t20" ]; then echo "  identical to [1]"; else printf '%s\n' "$t18"; fi
echo ""
echo "[4] K = 1000, 10000, 100000, 1000000 -- the first n (1..30) that falls back, node20  /^(a+)+\$/"
for K in 1000 10000 100000 1000000; do
  f="none"
  for n in $(seq 1 30); do if fell_back "$N20" "$K" '^(a+)+$' "$n"; then f="$n"; break; fi; done
  printf '  K = %-9s first n = %s\n' "$K" "$f"
done
```

- ★★★ `[1]` 비율 칸은 n 이 커질수록 어느 값으로 가나?
- ★★★ `[2]` `/^a+$/` 의 K 는 n 이 1 에서 10000 이 되는 동안 어떻게 되나?
- ★★ `[3]` node18 의 표는?
- ★★★ `[4]` K 가 열 배씩 늘 때 첫 n 은 어떻게 늘어나나?
- ★ 이 창은 왜 시간이 아니라 「되돌이 수」인가 — 그 차이가 재현성에 무엇을 주나?

### 7. `d` 플래그의 숫자는 무엇을 센 것인가 (연결) ★★

- ★★ `/(?<k>\w+)=(?<v>\w+)/d.exec("a=1; key=val")` 의 `indices` 와 `indices.groups` 는 어떤 모양인가?
- ★★★ 앞에 `String.fromCodePoint(0x1f600)` 을 붙이면 `x` 의 시작은 몇인가? `du` 로 바꾸면?
- ★★ 그것은 04번의 `length` 와 같은 단위인가?
- ★ `d` 가 없는 매치에 `indices` 는 있나?

### 8. ES2025 의 세 가지를 없는 판과 있는 판에 (경계) ★★

- ★★ `RegExp.escape` · 다른 갈래의 같은 이름 · `(?i:…)` 를 node 두 판에 던지면 각각 어떤 예외가 나오나?
- ★★★ 그 예외 문구가 「기능이 없다」를 말하나, 다른 것을 말하나?
- ★★ Chrome 151 에서 `RegExp.escape("a.b*c")` 의 첫 글자는 어떻게 바뀌나?
- ★ 같은 갈래 안에서 같은 이름을 두 번 쓰면 ES2025 에서는?

### 9. 명세는 매칭을 어디까지 정하나 (왜) ★★★

- ★★★ ECMA-262 가 정하는 것은 **어느 답을 찾을지**인가, **어떻게 찾을지**인가?
- ★★★ 명세의 매처·연속 서술이 「백트래킹처럼 보이는」 이유는? 그런데 왜 그것이 알고리즘 강제가 아닌가?
- ★★ 그래서 5번의 no 칸은 명세 위반인가, 명세 밖의 일인가?
- ★ 룩비하인드 안의 캡처 방향은 어느 층(명세·엔진·판)의 사실인가?

### 10. 세 엔진이 받는 문법 (경계) ★★★

- ★★★ 같은 열두 패턴을 V8(`u`)·Go `regexp`·파이썬 `re` 에 컴파일시켰을 때 **셋이 다 받은 것**은?
- ★★★ Go 쪽이 거절한 것들의 공통점은? 그것이 5번의 Go 열과 어떻게 이어지나?
- ★★ 명명 그룹 문법은 엔진마다 어떻게 갈리나?
- ★ 백트래킹을 끊는 문법(`a++`·`(?>…)`)을 받은 것은?

### 11. V8 의 `l` 플래그 (경계) ★★

- ★★ 두 node 판의 `--v8-options` 에 어떤 스위치가 있었나?
- ★★★ 스위치 없이 `/x/l` 은? 스위치를 켜면 열한 패턴 중 몇이 통과하나?
- ★★★ 켜도 거절되는 것은 무엇이고, 문구는?
- ★ 이 엔진은 명세의 것인가, V8 의 것인가? 그래서 실무의 처방은?

### 12. 파이썬 `re`·Go `regexp` 와의 대비 (연결) ★★

- ★★ 5번에서 파이썬 열은 어느 쪽(node 열 · Go 열)과 같았나?
- ★★★ 가변 길이 룩비하인드에서 JS 와 파이썬은 어떻게 갈리나? 문구까지.
- ★★ `\p{L}` 을 받지 않는 쪽은?
- ★ Rust 는 왜 이 대비에 없나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
