# js/syntax/28 — `String` 메서드와 템플릿 리터럴: 「치환 문자열 · 태그가 받는 것 · 자르기의 경계」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(판별 블록만) · Python 3.12.3 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> `replace` 의 두 번째 인자에 `$` 표기를 넣고 **네 가지 자리**에서 무엇이 되는지 전부 찍는다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **치환 문자열의 `$` 표기는 어느 자리에서 읽히나**
> ② **태그 함수가 받는 `strings` 는 어떤 객체인가**
> ③ **자르기·찾기 메서드가 경계 인자를 어떻게 다루나.**
>
> ★★ **예외는 타입과 메시지로만 답한다.**
>
> **선행** — [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) · [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) · [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md).
> ★★★ **04번의 서로게이트 한 쌍을 먼저 떠올려라** — `length` 는 무엇을 세었나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 2 · 3 · 4 · 5 · 6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸 하나하나를 적어라.** 마지막 줄의 수까지 세어 본다.
- ★★ **2번·6번은 「되는 것」과 「터지는 것」을 갈라서** 적어라. 터지면 종류와 문구까지.
- ★★ **3번은 `true`/`false` 를 한 줄씩** 적어라 — 같은 객체인가가 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「`replaceAll` 이 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 치환 문자열의 `$` 표기를 여러 자리에 넣으면 (예측) ★★★ 이 주제의 축

```js
// js28b-28a-dollar-grid.js
// String.prototype.replace -- how the replacement string is read, in four settings.
// Input "abc", the part being replaced is "b". The script prints every cell, then counts.
const J = (x) => JSON.stringify(x);
const templates = ["[$&]", "[$`]", "[$']", "[$$]", "[$1]", "[$01]", "[$10]", "[$9]", "[$0]", "[$<g>]", "[$<x>]"];
const settings = [
  ["string pattern", (t) => "abc".replace("b", t)],
  ["/(b)/", (t) => "abc".replace(/(b)/, t)],
  ["/(?<g>b)/", (t) => "abc".replace(/(?<g>b)/, t)],
  ["/(?<g>b)/ + fn", (t) => "abc".replace(/(?<g>b)/, () => t)],
];

console.log("[1] replacement  " + settings.map(([n]) => n.padEnd(17)).join("").trimEnd());
let changed = 0, total = 0;
for (const t of templates) {
  const literal = "a" + t + "c";
  const cells = settings.map(([, f]) => f(t));
  for (const c of cells) { total += 1; if (c !== literal) changed += 1; }
  console.log(("    " + t.padEnd(13) + cells.map((c) => J(c).padEnd(17)).join("")).trimEnd());
}

console.log("");
console.log("[2] the same template through replaceAll and split-join");
console.log("    'a.b.c'.replaceAll('.', '$&$&')     " + J("a.b.c".replaceAll(".", "$&$&")));
console.log("    'a.b.c'.split('.').join('$&$&')     " + J("a.b.c".split(".").join("$&$&")));

console.log("");
console.log("[3] a replacement that comes from outside -- a price string");
const price = "$5";
console.log("    'cost: X'.replace('X', price)        " + J("cost: X".replace("X", price)));
const price2 = "$&0";
console.log("    'cost: X'.replace('X', '$&0')        " + J("cost: X".replace("X", price2)));
console.log("    'cost: X'.replace('X', () => '$&0')  " + J("cost: X".replace("X", () => price2)));

console.log("");
console.log("cells where the output differs from the plain text of the template: " + changed + " / " + total);
```

- ★★★ `[1]` 열한 줄 × 네 열을 전부 적어라. 특히 **넷째 열**.
- ★★★ `[$1]` · `[$10]` · `[$9]` 줄은 둘째 열에서 각각 무엇인가?
- ★★★ `[$<g>]` · `[$<x>]` 줄은 셋째 열에서 각각 무엇인가?
- ★★ `[2]` 두 줄 — `replaceAll` 과 `split().join()` 은 같은 결과인가?
- ★★★ `[3]` 세 줄 — 가격 문자열은 그대로 들어가는가?
- ★ 마지막 줄 「N / M」의 N 과 M 은?

### 2. `replace` 와 `replaceAll` 에 같은 패턴을 주면 (예측) ★★★

```js
// js28b-28b-replace-all.js
// replace and replaceAll -- how many places, and what each accepts as the pattern.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(38) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(38) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] a string pattern");
show("'a-b-c'.replace('-', '+')", () => "a-b-c".replace("-", "+"));
show("'a-b-c'.replaceAll('-', '+')", () => "a-b-c".replaceAll("-", "+"));
show("'a-b-c'.split('-').join('+')", () => "a-b-c".split("-").join("+"));

console.log("");
console.log("[2] a regexp pattern, with and without g");
show("'a-b-c'.replace(/-/, '+')", () => "a-b-c".replace(/-/, "+"));
show("'a-b-c'.replace(/-/g, '+')", () => "a-b-c".replace(/-/g, "+"));
show("'a-b-c'.replaceAll(/-/g, '+')", () => "a-b-c".replaceAll(/-/g, "+"));
show("'a-b-c'.replaceAll(/-/, '+')", () => "a-b-c".replaceAll(/-/, "+"));

console.log("");
console.log("[3] the empty string as the pattern");
show("'abc'.replace('', '-')", () => "abc".replace("", "-"));
show("'abc'.replaceAll('', '-')", () => "abc".replaceAll("", "-"));

console.log("");
console.log("[4] overlapping candidates -- 'aaa' with 'aa'");
show("'aaa'.replaceAll('aa', 'X')", () => "aaa".replaceAll("aa", "X"));
show("'aaa'.split('aa')", () => "aaa".split("aa"));

console.log("");
console.log("[5] what the replacer function receives for a string pattern");
const calls = [];
"x-y-z".replaceAll("-", (...args) => { calls.push(args); return "+"; });
show("calls", () => calls);

console.log("");
console.log("[6] the pattern is not a string or a regexp");
show("'a1b1'.replaceAll(1, '_')", () => "a1b1".replaceAll(1, "_"));
show("'anullb'.replace(null, '_')", () => "anullb".replace(null, "_"));
show("'a.b'.replaceAll('.', undefined)", () => "a.b".replaceAll(".", undefined));
```

- ★★★ `[1]`·`[2]` 일곱 줄 — 몇 곳이 바뀌나? 터지는 줄이 있으면 문구까지.
- ★★ `[3]` 빈 문자열 패턴 두 줄은?
- ★★ `[4]` `'aaa'` 에서 `'aa'` 를 찾으면 몇 곳인가?
- ★★ `[5]` 콜백은 몇 번, 무슨 인자로 불리나?
- ★ `[6]` 세 줄.

### 3. 태그 함수가 받는 것과 그 동일성 (예측) ★★★

```js
// js28b-28c-tagged.js
// Tagged templates -- what the tag function receives, and whether it is the same object each time.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(48) + f()); }
  catch (e) { console.log("  " + label.padEnd(48) + e.constructor.name + " 「" + e.message + "」"); }
};
const keep = (strings, ...subs) => ({ strings, subs });
const T = (v) => (typeof v === "string" ? "[" + v + "]" : String(v));   // text in brackets, no JSON escaping

console.log("[1] what the tag receives");
const r = keep`a${1}b${"two"}c`;
show("strings", () => J(r.strings));
show("strings.raw", () => J(r.strings.raw));
show("subs", () => J(r.subs));
show("strings.length vs subs.length", () => r.strings.length + " vs " + r.subs.length);
show("Array.isArray(strings)", () => Array.isArray(r.strings));
show("Object.isFrozen(strings)", () => Object.isFrozen(r.strings));
show("Object.isFrozen(strings.raw)", () => Object.isFrozen(r.strings.raw));
show("keep`${1}`.strings", () => J(keep`${1}`.strings));

console.log("");
console.log("[2] the strings object across calls");
const site = () => keep`same ${0} text`.strings;
show("site() === site()", () => site() === site());
const other = () => keep`same ${0} text`.strings;
show("site() === other()   (same text, other place)", () => site() === other());
const seen = [];
for (let i = 0; i < 3; i++) seen.push(keep`loop ${i}`.strings);
show("three loop turns, same object?", () => seen[0] === seen[1] && seen[1] === seen[2]);
const viaFn = () => new Function("keep", "return keep`same ${0} text`.strings")(keep);
show("new Function each time: equal?", () => viaFn() === viaFn());
show("writing strings[0]", () => { "use strict"; const s = site(); s[0] = "changed"; return J(s[0]); });

console.log("");
console.log("[3] String.raw");
show("String.raw`a\\nb`.length", () => String.raw`a\nb`.length);
show("`a\\nb`.length", () => `a\nb`.length);
show("String.raw`C:\\dir\\${'x'}`", () => T(String.raw`C:\dir\${"x"}`));
show("String.raw({ raw: ['x', 'y', 'z'] }, 1, 2, 3)", () => T(String.raw({ raw: ["x", "y", "z"] }, 1, 2, 3)));
show("String.raw({ raw: 'abc' }, '-', '-')", () => T(String.raw({ raw: "abc" }, "-", "-")));

console.log("");
console.log("[4] an escape that is not a valid escape");
const bad = "\\" + "unicode and \\" + "xZ";
show("tag receives -- cooked", () => T(new Function("keep", "return keep`" + bad + "`.strings[0]")(keep)));
show("tag receives -- raw", () => T(new Function("keep", "return keep`" + bad + "`.strings.raw[0]")(keep)));
show("the same text without a tag", () => T(new Function("return `" + bad + "`")()));
show("String.raw with it", () => T(new Function("return String.raw`" + bad + "`")()));
```

- ★★★ `[1]` 여덟 줄 — `strings` 와 `subs` 의 길이 관계는? 얼어 있나?
- ★★★ `[2]` 다섯 줄을 `true`/`false` 로 — 무엇이 「같은 객체」를 정하나?
- ★★ `[2]` 마지막 줄 — 쓰기는 통과하나?
- ★★★ `[3]` 다섯 줄 — 특히 셋째 줄의 `${"x"}` 는 치환되나?
- ★★★ `[4]` 네 줄 — 태그가 있을 때와 없을 때 각각 무엇을 내놓나?

### 4. `slice`·`substring`·`substr`·`at` 에 같은 인자를 주면 (예측) ★★★

```js
// js28b-28d-slice-substring.js
// slice / substring / substr on the same string and the same arguments. The script counts the cells.
const s = "abcdef";
const J = (x) => (x === undefined ? "undefined" : JSON.stringify(x));
const args = [[2], [-2], [2, 4], [4, 2], [-3, -1], [2, -1], [-1, 2], [NaN, 3], [undefined, 3], [2, 100]];
const fmt = (a) => "(" + a.map((v) => (v === undefined ? "undefined" : String(v))).join(", ") + ")";

console.log("[1] 'abcdef' -- slice / substring / substr");
console.log("  args            slice      substring  substr");
let differ = 0;
for (const a of args) {
  const sl = s.slice(...a), su = s.substring(...a), sb = s.substr(...a);
  if (sl !== su) differ += 1;
  console.log("  " + fmt(a).padEnd(16) + J(sl).padEnd(11) + J(su).padEnd(11) + J(sb));
}

console.log("");
console.log("[2] at and bracket access");
for (const i of [0, 5, 6, -1, -6, -7, 1.7, "1"]) {
  console.log("  " + ("i = " + J(i)).padEnd(12) + "at " + J(s.at(i)).padEnd(12) + "s[i] " + J(s[i]));
}

console.log("");
console.log("[3] the same calls on a string with a code point outside the BMP (built with fromCodePoint)");
const e = "a" + String.fromCodePoint(0x1F600) + "b";
const hex = (t) => [...Array(t.length).keys()].map((i) => t.charCodeAt(i).toString(16)).join(" ");
console.log("  length " + e.length + "   code units " + hex(e));
console.log("  slice(0, 2)  code units " + hex(e.slice(0, 2)) + "   isWellFormed " + (typeof e.isWellFormed === "function" ? e.slice(0, 2).isWellFormed() : "(no method)"));
console.log("  at(1)        code units " + hex(e.at(1)));
console.log("  at(-2)       code units " + hex(e.at(-2)));

console.log("");
console.log("rows where slice and substring disagree: " + differ + " / " + args.length);
```

- ★★★ `[1]` 열 줄 × 세 열을 적어라. 특히 `(-2)` · `(4, 2)` · `(2, -1)` 줄.
- ★★ `[2]` 여덟 줄 — `i` 마다 `at(i)` 와 `s[i]` 를 견주면?
- ★★★ `[3]` 네 줄 — `slice(0, 2)` 와 `at(1)`·`at(-2)` 는 각각 어떤 코드 유닛인가?
- ★ `[3]` 둘째 줄의 `isWellFormed` 칸은 두 node 판에서 같은가?
- ★ 마지막 줄 「N / M」은?

### 5. `split` 에 정규식을 주면 (예측) ★★

```js
// js28b-28e-split.js
// split -- a string separator, a regexp separator, and a regexp with capture groups.
const J = (x) => JSON.stringify(x, (k, v) => (v === undefined ? "<undefined>" : v));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(36) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(36) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] separators");
show("'a1b22c'.split('2')", () => "a1b22c".split("2"));
show("'a1b22c'.split(/\\d/)", () => "a1b22c".split(/\d/));
show("'a1b22c'.split(/\\d+/)", () => "a1b22c".split(/\d+/));
show("'a1b22c'.split(/(\\d)/)", () => "a1b22c".split(/(\d)/));
show("'a1b22c'.split(/(\\d)+/)", () => "a1b22c".split(/(\d)+/));
show("'a1b-c'.split(/(\\d)|(-)/)", () => "a1b-c".split(/(\d)|(-)/));
show("'a1b-c'.split(/(?:\\d|-)/)", () => "a1b-c".split(/(?:\d|-)/));

console.log("");
console.log("[2] ends, empties and limits");
show("',a,,b,'.split(',')", () => ",a,,b,".split(","));
show("''.split(',')", () => "".split(","));
show("''.split('')", () => "".split(""));
show("'abc'.split('')", () => "abc".split(""));
show("'abc'.split()", () => "abc".split());
show("'a,b,c'.split(',', 2)", () => "a,b,c".split(",", 2));
show("'a1b2c'.split(/(\\d)/, 2)", () => "a1b2c".split(/(\d)/, 2));
show("'abc'.split(/(?:)/)", () => "abc".split(/(?:)/));

console.log("");
console.log("[3] does split look at lastIndex or the g flag?");
const g = /,/g;
g.lastIndex = 3;
show("'a,b,c'.split(/,/g)  lastIndex=3", () => "a,b,c".split(g));
show("  g.lastIndex afterwards", () => g.lastIndex);
```

- ★★★ `[1]` 일곱 줄 — 괄호가 있는 구분자와 없는 구분자에서 결과 배열은 어떻게 다른가?
- ★★ `/(\d)|(-)/` 줄에 `<undefined>` 가 있나? 있으면 몇 개인가?
- ★★ `[2]` 여덟 줄 — 특히 `''.split(',')` 와 `'a1b2c'.split(/(\d)/, 2)`.
- ★★ `[3]` 두 줄 — `split` 은 `lastIndex` 를 쓰나, 바꾸나?

### 6. 채우기 · 다듬기 · 찾기의 경계 인자 (예측) ★★

```js
// js28b-28f-pad-trim-search.js
// padStart / trim / includes / startsWith / indexOf -- the edge arguments.
const J = (x) => (x === undefined ? "undefined" : JSON.stringify(x));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] padStart / padEnd");
show("'7'.padStart(3, '0')", () => "7".padStart(3, "0"));
show("'7'.padStart(6, 'ab')", () => "7".padStart(6, "ab"));
show("'1234'.padStart(3, '0')", () => "1234".padStart(3, "0"));
show("'7'.padStart(3, '')", () => "7".padStart(3, ""));
show("'7'.padStart(3)", () => "7".padStart(3));
show("'7'.padEnd(3, 'xyz')", () => "7".padEnd(3, "xyz"));

console.log("");
console.log("[2] trim -- the first character's general category, and the code units (hex) before and after");
const hex = (t) => [...Array(t.length).keys()].map((i) => t.charCodeAt(i).toString(16).padStart(4, "0")).join(" ");
const cases = [
  ["space tab newline", " \t\nx\n"],
  ["U+00A0 no-break space", String.fromCharCode(0xa0) + "x"],
  ["U+3000 ideographic space", String.fromCharCode(0x3000) + "x"],
  ["U+FEFF byte order mark", String.fromCharCode(0xfeff) + "x"],
  ["U+200B zero width space", String.fromCharCode(0x200b) + "x"],
  ["U+2028 line separator", String.fromCharCode(0x2028) + "x"],
];
const cat = (t) => ["Zs", "Zl", "Cf", "Cc"].find((c) => new RegExp("^\\p{" + c + "}", "u").test(t)) || "-";
for (const [name, t] of cases) console.log("  " + name.padEnd(26) + "category " + cat(t).padEnd(4) + "before " + hex(t).padEnd(26) + "after trim " + hex(t.trim()));
show("'  x  '.trimStart()", () => "  x  ".trimStart());
show("'  x  '.trimEnd()", () => "  x  ".trimEnd());

console.log("");
console.log("[3] includes / startsWith / endsWith / indexOf");
show("'abc'.includes('')", () => "abc".includes(""));
show("'abc'.indexOf('')", () => "abc".indexOf(""));
show("'abc'.indexOf('', 10)", () => "abc".indexOf("", 10));
show("'abc'.startsWith('b', 1)", () => "abc".startsWith("b", 1));
show("'abc'.endsWith('b', 2)", () => "abc".endsWith("b", 2));
show("'abc'.includes('A')", () => "abc".includes("A"));
show("'a.c'.includes('.')", () => "a.c".includes("."));
show("'abc'.includes(/b/)", () => "abc".includes(/b/));
show("'abc'.startsWith(/a/)", () => "abc".startsWith(/a/));
const r = /b/;
r[Symbol.match] = false;
show("'/b/'.includes(r)  r[Symbol.match]=false", () => "/b/".includes(r));
show("'abc'.includes(undefined)", () => "abc".includes(undefined));
show("'undefined'.includes()", () => "undefined".includes());
```

- ★★ `[1]` 여섯 줄.
- ★★★ `[2]` 여섯 줄 — 글자마다 `trim` 뒤에 남나, 지워지나? 분류(`category`) 칸과 맞춰 보라.
- ★★ `[3]` 빈 문자열을 찾는 세 줄은?
- ★★★ `[3]` 정규식을 넘긴 두 줄은 통과하나? 그다음 `Symbol.match` 줄은?
- ★ `[3]` 마지막 두 줄.

### 7. 치환 문자열과 치환 함수는 명세에서 어떻게 갈리나 (왜) ★★★

- ★★★ 명세 `replace` 는 두 번째 인자가 문자열일 때 **어떤 추상 연산**으로 결과를 만드나? 함수일 때는?
- ★★ 그 연산이 받는 **캡처 목록과 명명 캡처 객체**는 패턴이 문자열일 때 무엇인가?
- ★ 그래서 바깥에서 온 문자열을 넣을 때의 처방은 무엇인가?

### 8. 태그 함수가 받는 `strings` 는 명세에서 어디서 오나 (왜) ★★★

- ★★★ 명세는 그 배열을 **어느 연산**으로 만들고 **어디에** 보관하나? 키는 무엇인가?
- ★★ 3번 `[2]` 의 `new Function` 줄은 그 키로 어떻게 설명되나?
- ★★ 3번 `[4]` 의 결과는 **어느 판**부터이고, 그때 `cooked` 칸에는 무엇이 들어가나?

### 9. 파이썬 `str.replace`·`re.sub` 에 같은 질문을 던지면 (연결) ★★

```sh
# js28b-28g-python.sh
#!/usr/bin/env bash
# 같은 질문을 파이썬에 던진다 -- replace 가 몇 곳을 바꾸나 · 치환 문자열의 특수 표기 · 자르기의 음수 인자.
set -u -o pipefail
python3 - <<'PY'
import re
def show(label, f):
    try:
        print("  " + label.ljust(44) + repr(f()))
    except Exception as e:
        print("  " + label.ljust(44) + type(e).__name__ + " 「" + str(e) + "」")

print("[1] str.replace")
show("'a-b-c'.replace('-', '+')", lambda: "a-b-c".replace("-", "+"))
show("'a-b-c'.replace('-', '+', 1)", lambda: "a-b-c".replace("-", "+", 1))
show("'abc'.replace('', '-')", lambda: "abc".replace("", "-"))
show("'abc'.replace('b', '[$&]')", lambda: "abc".replace("b", "[$&]"))

print("")
print("[2] re.sub -- the replacement template")
show("re.sub('(b)', r'[\\1]', 'abc')", lambda: re.sub("(b)", r"[\1]", "abc"))
show("re.sub('(?P<g>b)', r'[\\g<g>]', 'abc')", lambda: re.sub("(?P<g>b)", r"[\g<g>]", "abc"))
show("re.sub('(b)', '[$1]', 'abc')", lambda: re.sub("(b)", "[$1]", "abc"))
show("re.sub('(b)', r'[\\9]', 'abc')", lambda: re.sub("(b)", r"[\9]", "abc"))
show("re.sub('b', lambda m: r'[\\1]', 'abc')", lambda: re.sub("b", lambda m: r"[\1]", "abc"))

print("")
print("[3] slicing with negative and reversed bounds")
s = "abcdef"
show("s[-2:]", lambda: s[-2:])
show("s[4:2]", lambda: s[4:2])
show("s[2:-1]", lambda: s[2:-1])
PY
```

- ★★★ `'a-b-c'.replace('-', '+')` 는 두 언어에서 같은 결과인가?
- ★★ 파이썬의 치환 표기는 무엇이고, `$1` 은 파이썬에서 무엇인가?
- ★★★ 없는 그룹 번호를 쓰면 두 언어는 각각 어떻게 하나?
- ★ 음수 자르기에서 파이썬 `s[-2:]` 와 같은 것은 JS 의 어느 메서드인가?

### 10. 04번의 코드 유닛과 이 주제의 인덱스 메서드 (연결) ★★

- ★★ 04번은 서로게이트 한 쌍을 가운데서 자르면 무엇이 된다고 쟀나? 4번 `[3]` 은 어느 메서드로 같은 일을 했나?
- ★★ `at` 은 코드 포인트 단위인가 코드 유닛 단위인가? 그 근거가 되는 줄은?
- ★ 「사람이 보는 한 글자」 단위로 자르려면 04번의 어느 도구가 필요한가?

### 11. 어디까지가 이 주제인가 — 22번 · 29번과의 경계 (경계) ★★

- ★★ `` `${x}` `` 와 `x + ''` 가 부르는 hint 는 각각 무엇이었나? 어느 주제가 쟀나?
- ★★ 정규식 `replace` 의 콜백이 받는 인자(캡처·위치·`groups`)는 어느 주제가 정본인가?
- ★ `includes` 가 정규식을 거절할 때 묻는 잘 알려진 심볼은 무엇이고, 그 심볼의 전수는 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
