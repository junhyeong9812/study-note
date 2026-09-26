# js/syntax/29 — 정규식 기본: 「정규식 객체의 상태 · `match` 의 모양 · 리터럴의 동일성」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(판별 블록만) · Python 3.12.3 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> 같은 정규식 객체로 같은 입력을 여러 번 검사하고, **호출 전과 후의 `lastIndex`** 를 매번 찍는다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`lastIndex` 는 누가 읽고 누가 쓰나**
> ② **`match`·`matchAll`·`replace` 콜백은 무엇을 돌려주고 무엇을 받나**
> ③ **정규식 객체는 언제 새로 만들어지나.**
>
> ★★ **예외는 타입과 메시지로만 답한다.**
>
> **선행** — [28 — `String` 메서드와 템플릿 리터럴](../28-string-methods-and-template-literals/2-summary.md) · [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) · [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md).
> ★★★ **28번의 `split` 블록 `[3]` 을 먼저 떠올려라** — `lastIndex = 3` 인 `g` 정규식으로 나눴을 때 결과와 `lastIndex` 는 무엇이었나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 2 · 3 · 4 · 5 · 6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 줄마다 `lastIndex` 두 칸과 `test` 한 칸을 적어라** — 값 하나라도 틀리면 답이 아니다.
- ★★★ **2번은 칸 하나하나를 적고, 마지막 줄의 수까지 세어 본다.**
- ★★ **3번·6번은 「되는 것」과 「터지는 것」을 갈라서** 적어라. 터지면 종류와 문구까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「리터럴을 밖으로 빼면 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `g` 정규식 하나로 같은 입력을 거듭 검사하면 (예측) ★★★ 이 주제의 축

```js
// js28b-29a-lastindex.js
// A regexp object with the g flag carries state between calls. Watch lastIndex around each call.
const step = (label, re, input) => {
  const before = re.lastIndex;
  const r = re.test(input);
  console.log("  " + label.padEnd(28) + "lastIndex " + String(before).padEnd(3) + "-> test " + String(r).padEnd(6) + "-> lastIndex " + re.lastIndex);
};

console.log("[1] one regexp /a/g, the same input 'a', four calls");
const g = /a/g;
for (let i = 1; i <= 4; i++) step("call " + i + "  test('a')", g, "a");

console.log("");
console.log("[2] the same without g");
const plain = /a/;
for (let i = 1; i <= 3; i++) step("call " + i + "  test('a')", plain, "a");

console.log("");
console.log("[3] /a/g on the input 'aa', four calls");
const g2 = /a/g;
for (let i = 1; i <= 4; i++) step("call " + i + "  test('aa')", g2, "aa");

console.log("");
console.log("[4] a validator shared across a list -- filter(s => re.test(s))");
const valid = /^[a-z]+$/g;
const words = ["one", "two", "three", "four"];
const kept = words.filter((w) => valid.test(w));
console.log("  input  " + JSON.stringify(words));
console.log("  kept   " + JSON.stringify(kept));
const kept2 = words.filter((w) => /^[a-z]+$/.test(w));
console.log("  kept, literal without g inside the callback  " + JSON.stringify(kept2));

console.log("");
console.log("[5] setting lastIndex by hand, and an input shorter than lastIndex");
const g3 = /a/g;
g3.lastIndex = 5;
step("lastIndex = 5, test('aaa')", g3, "aaa");
g3.lastIndex = 1;
step("lastIndex = 1, test('ab')", g3, "ab");
step("then test('ba')", g3, "ba");
```

- ★★★ `[1]` 네 줄의 `lastIndex` → `test` → `lastIndex` 를 적어라.
- ★★ `[2]` 세 줄은 `[1]` 과 무엇이 다른가?
- ★★★ `[3]` 입력 `'aa'` 네 줄 — `test` 의 참/거짓 순서는?
- ★★★ `[4]` `kept` 에는 무엇이 남나? 마지막 줄은?
- ★★ `[5]` 세 줄 — 특히 셋째 줄의 `lastIndex` 는 몇이 되나?

### 2. `match` 가 돌려주는 모양 (예측) ★★★

```js
// js28b-29b-match-shape.js
// String.prototype.match -- what comes back, with and without the g flag. The script counts the cells.
const J = (x) => (x === undefined ? "undefined" : JSON.stringify(x));
const input = "a1b22";
const columns = [
  ["/(\\d)/", () => input.match(/(\d)/)],
  ["/(\\d)/g", () => input.match(/(\d)/g)],
  ["/(?<n>\\d)/", () => input.match(/(?<n>\d)/)],
  ["/(?<n>\\d)/g", () => input.match(/(?<n>\d)/g)],
  ["/x/", () => input.match(/x/)],
  ["/x/g", () => input.match(/x/g)],
];
const rows = [
  ["returned", (m) => (m === null ? "null" : Array.isArray(m) ? "array" : typeof m)],
  ["length", (m) => (m === null ? "-" : J(m.length))],
  ["[0]", (m) => (m === null ? "-" : J(m[0]))],
  ["[1]", (m) => (m === null ? "-" : J(m[1]))],
  ["index", (m) => (m === null ? "-" : J(m.index))],
  ["input", (m) => (m === null ? "-" : J(m.input))],
  ["groups", (m) => (m === null ? "-" : J(m.groups))],
];

console.log("[1] '" + input + "'.match(re)");
console.log(("  " + "".padEnd(10) + columns.map(([n]) => n.padEnd(14)).join("")).trimEnd());
const results = columns.map(([, f]) => f());
const table = rows.map(([, read]) => results.map(read));
rows.forEach(([name], i) => console.log(("  " + name.padEnd(10) + table[i].map((c) => c.padEnd(14)).join("")).trimEnd()));

console.log("");
console.log("[2] the same regexps through exec, for comparison");
const e1 = /(\d)/.exec(input), e2 = /(\d)/g.exec(input);
console.log("  /(\\d)/.exec    " + J([...e1]) + "  index " + e1.index);
console.log("  /(\\d)/g.exec   " + J([...e2]) + "  index " + e2.index);

console.log("");
console.log("[3] match with a string argument");
console.log("  'a.c'.match('.')    " + J([..."a.c".match(".")]) + "  index " + "a.c".match(".").index);
console.log("  'abc'.match()       " + J([..."abc".match()]));

let differ = 0, total = 0;
for (const row of table) for (const [a, b] of [[0, 1], [2, 3], [4, 5]]) { total += 1; if (row[a] !== row[b]) differ += 1; }
console.log("");
console.log("cells where the g column differs from its pair without g: " + differ + " / " + total);
```

- ★★★ `[1]` 일곱 행 × 여섯 열을 전부 적어라. 특히 `length` · `[1]` · `index` · `groups` 행.
- ★★ `[2]` 두 줄 — `exec` 는 `g` 에 따라 모양이 바뀌나?
- ★★ `[3]` 두 줄 — `'a.c'.match('.')` 는 무엇을 찾나?
- ★ 마지막 줄 「N / M」의 N 과 M 은?

### 3. `matchAll` 이 받는 것 · 돌려주는 것 · 넘긴 정규식에 하는 것 (예측) ★★★

```js
// js28b-29c-matchall.js
// matchAll -- what it returns, what it needs, and what it does to the regexp it was given.
const J = (x) => (x === undefined ? "undefined" : JSON.stringify(x));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + f()); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};
const input = "a1b22";

console.log("[1] the argument");
show("matchAll(/\\d/g)  first match", () => J([...[...input.matchAll(/\d/g)][0]]));
show("matchAll(/\\d/)", () => J([...input.matchAll(/\d/)].length));
show("matchAll('\\\\d')", () => J([...input.matchAll("\\d")].map((m) => m[0])));
show("matchAll('.')", () => J([..."a.c".matchAll(".")].map((m) => m[0])));

console.log("");
console.log("[2] what comes back");
const it = input.matchAll(/(\d)/g);
show("Object.prototype.toString.call(it)", () => Object.prototype.toString.call(it));
show("Array.isArray(it)", () => Array.isArray(it));
show("typeof it.next / it.return", () => typeof it.next + " / " + typeof it.return);
show("it[Symbol.iterator]() === it", () => it[Symbol.iterator]() === it);
show("each element", () => J([...it].map((m) => ({ all: m[0], one: m[1], index: m.index }))));
show("spread the same iterator again", () => J([...it]));

console.log("");
console.log("[3] the regexp object that was passed in");
const re = /\d/g;
re.lastIndex = 2;
const it2 = input.matchAll(re);
show("re.lastIndex right after matchAll()", () => re.lastIndex);
show("first match from the iterator", () => J(it2.next().value[0]));
show("re.lastIndex after pulling one", () => re.lastIndex);
show("remaining", () => J([...it2].map((m) => m[0])));

console.log("");
console.log("[4] when does the search run, and on which object? (RegExp.prototype.exec wrapped with a counter)");
const calls = [];
const origExec = RegExp.prototype.exec;
const passed = /\d/g;
RegExp.prototype.exec = function (s) { calls.push(this === passed ? "passed object" : "another object"); return origExec.call(this, s); };
const it3 = input.matchAll(passed);
show("exec calls after matchAll()", () => J(calls));
it3.next();
show("exec calls after one next()", () => J(calls));
[...it3];
show("exec calls after spreading the rest", () => J(calls));
RegExp.prototype.exec = origExec;
```

- ★★★ `[1]` 네 줄 — 통과하나, 터지나? 터지면 문구까지.
- ★★★ `[2]` 여섯 줄 — 태그는 무엇이고, `return` 은 있나? 두 번째 펼치기는?
- ★★★ `[3]` 네 줄 — 첫 매치는 몇 번 위치의 무엇인가? `re.lastIndex` 는 바뀌나?
- ★★★ `[4]` 세 줄 — `exec` 는 언제, 몇 번, 어느 객체로 불리나?

### 4. `replace` 콜백이 받는 인자 (예측) ★★

```js
// js28b-29d-replace-callback.js
// The arguments a replace callback receives -- by position, for four kinds of pattern.
const J = (x) => JSON.stringify(x, (k, v) => (v === undefined ? "<undefined>" : v));
const spy = (label, run) => {
  const calls = [];
  const out = run((...args) => { calls.push(args); return "_"; });
  console.log("  " + label);
  calls.forEach((args, i) => console.log("    call " + (i + 1) + "  " + args.length + " args  " + J(args)));
  console.log("    result " + J(out));
};

console.log("[1] a string pattern");
spy("'x1y2'.replace('1', fn)", (fn) => "x1y2".replace("1", fn));

console.log("");
console.log("[2] a regexp with no groups, g flag");
spy("'x1y2'.replace(/\\d/g, fn)", (fn) => "x1y2".replace(/\d/g, fn));

console.log("");
console.log("[3] two numbered groups, the second optional");
spy("'x1a y2'.replace(/(\\d)([a-z])?/g, fn)", (fn) => "x1a y2".replace(/(\d)([a-z])?/g, fn));

console.log("");
console.log("[4] the same with a named group");
spy("'x1a y2'.replace(/(\\d)(?<L>[a-z])?/g, fn)", (fn) => "x1a y2".replace(/(\d)(?<L>[a-z])?/g, fn));

console.log("");
console.log("[5] what the callback returns");
const back = (v) => "x1y2".replace(/\d/g, () => v);
for (const [label, v] of [["undefined", undefined], ["null", null], ["42", 42], ["{ toString: () => 'T' }", { toString: () => "T" }], ["'$&'", "$&"]]) {
  console.log("    returns " + label.padEnd(24) + "-> " + J(back(v)));
}
```

- ★★★ `[1]` 부터 `[4]` 까지 — 호출마다 인자 수와 인자 배열을 적어라.
- ★★ `[3]`·`[4]` 의 둘째 호출에서 선택 그룹 자리에는 무엇이 들어가나?
- ★★ `[5]` 다섯 줄 — 콜백이 돌려준 `'$&'` 는 읽히나?

### 5. 정규식 리터럴의 동일성과 `search` (예측) ★★★

```js
// js28b-29e-literal-identity.js
// A regexp literal -- one object per evaluation? And where lastIndex state can live.
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + String(f())); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] identity");
const make = () => /a/g;
show("make() === make()", () => make() === make());
const seen = [];
for (let i = 0; i < 2; i++) seen.push(/a/g);
show("the literal in two loop turns: same object?", () => seen[0] === seen[1]);
const r = /a/g;
show("RegExp(r) === r", () => RegExp(r) === r);
show("new RegExp(r) === r", () => new RegExp(r) === r);
show("RegExp(r, 'g') === r", () => RegExp(r, "g") === r);

console.log("");
console.log("[2] a regexp at module level vs a literal inside the function");
const SHARED = /a/g;
const hasShared = (s) => SHARED.test(s);
const hasLocal = (s) => /a/g.test(s);
show("hasShared('a') x3", () => [hasShared("a"), hasShared("a"), hasShared("a")].join(" "));
show("hasLocal('a')  x3", () => [hasLocal("a"), hasLocal("a"), hasLocal("a")].join(" "));

console.log("");
console.log("[3] copying a regexp -- does lastIndex come along?");
const src = /a/g;
src.lastIndex = 3;
show("new RegExp(src).lastIndex", () => new RegExp(src).lastIndex);
show("new RegExp(src).flags", () => new RegExp(src).flags);
show("new RegExp(src, 'i').flags", () => new RegExp(src, "i").flags);

console.log("");
console.log("[4] search -- given a g regexp with lastIndex set");
const b = /b/g;
b.lastIndex = 3;
show("'abcb'.search(b)", () => "abcb".search(b));
show("b.lastIndex afterwards", () => b.lastIndex);
show("b.exec('abcb').index   (for comparison)", () => { b.lastIndex = 3; return b.exec("abcb").index; });
```

- ★★★ `[1]` 다섯 줄을 `true`/`false` 로.
- ★★★ `[2]` 두 줄 — 세 번씩 부른 결과는?
- ★★ `[3]` 세 줄 — 복사하면 `lastIndex` 와 `flags` 는 어떻게 되나?
- ★★★ `[4]` 세 줄 — `search` 는 몇 번 위치를 주고, `lastIndex` 는 어떻게 되나?

### 6. 플래그 글자를 하나씩 · 여럿 · 잘못 주면 (예측) ★★

```js
// js28b-29f-flags.js
// The flags -- each letter, its property name, and what the constructor accepts.
const show = (label, f) => {
  try { console.log("  " + label.padEnd(36) + String(f())); }
  catch (e) { console.log("  " + label.padEnd(36) + e.constructor.name + " 「" + e.message + "」"); }
};
const props = ["hasIndices", "global", "ignoreCase", "multiline", "dotAll", "unicode", "unicodeSets", "sticky"];

console.log("[1] one letter at a time -- .flags and the property that turns true");
for (const f of ["g", "i", "m", "s", "u", "y", "d", "v"]) {
  show("new RegExp('a', '" + f + "')", () => {
    const re = new RegExp("a", f);
    return re.flags.padEnd(4) + props.filter((p) => re[p] === true).join(",");
  });
}

console.log("");
console.log("[2] several letters -- the order of .flags");
show("new RegExp('a', 'ymgi').flags", () => new RegExp("a", "ymgi").flags);
show("/a/yigm.flags", () => /a/yigm.flags);
show("new RegExp('a', 'dgimsuy').flags", () => new RegExp("a", "dgimsuy").flags);

console.log("");
console.log("[3] letters the constructor may refuse");
show("new RegExp('a', 'gg')", () => new RegExp("a", "gg").flags);
show("new RegExp('a', 'x')", () => new RegExp("a", "x").flags);
show("new RegExp('a', 'uv')", () => new RegExp("a", "uv").flags);
show("new RegExp('a', 'G')", () => new RegExp("a", "G").flags);

console.log("");
console.log("[4] what four of them change -- i, m, s, y");
show("/B/.test('abc')  /B/i.test('abc')", () => /B/.test("abc") + "  " + /B/i.test("abc"));
show("'a\\nb'.match(/^b/)  /^b/m", () => String("a\nb".match(/^b/)) + "  " + String("a\nb".match(/^b/m)));
show("/a.b/.test('a\\nb')  /a.b/s", () => /a.b/.test("a\nb") + "  " + /a.b/s.test("a\nb"));
const y = /b/y, g = /b/g;
show("/b/y.test('ab')  /b/g.test('ab')", () => y.test("ab") + "  " + g.test("ab"));
y.lastIndex = 1;
show("/b/y lastIndex=1 .test('ab')", () => y.test("ab"));

console.log("");
console.log("[5] a subclass whose flags getter returns 'gi'");
class Loud extends RegExp { get flags() { return "gi"; } }
show("new Loud('a').flags", () => new Loud("a").flags);
show("new Loud('a').global", () => new Loud("a").global);
show("new RegExp(new Loud('a')).flags", () => new RegExp(new Loud("a")).flags);
```

- ★★ `[1]` 여덟 줄 — 글자마다 켜지는 프로퍼티 이름은? 두 node 판에서 다른 줄이 있나?
- ★★ `[2]` 세 줄의 `flags` 글자 순서는?
- ★★★ `[3]` 네 줄은 통과하나?
- ★★ `[4]` 다섯 줄 — 특히 `y` 두 줄.
- ★ `[5]` 세 줄.

### 7. `lastIndex` 는 명세에서 누가 읽고 누가 쓰나 (왜) ★★★

- ★★★ `exec`·`test` 가 공통으로 부르는 명세 연산은 무엇이고, 그 연산은 **어떤 플래그일 때** `lastIndex` 를 읽나?
- ★★★ 그 연산이 `lastIndex` 에 **무엇을 쓰는** 경우는 몇 가지인가?
- ★★ `search` 와 `split` 은 `lastIndex` 를 어떻게 다루나? 28번의 `split` 블록과 맞춰 보라.
- ★ 리터럴이 **평가마다** 새 객체라는 것은 **어느 판**부터이고, 그것이 1번의 `[4]` 와 무슨 상관인가?

### 8. 같은 패턴을 리터럴과 `new RegExp` 로 적으면 (왜) ★★

```js
// js28b-29h-literal-vs-constructor.js
// A literal and the constructor -- the same pattern written two ways, and when a bad pattern is reported.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(40) + f()); }
  catch (e) { console.log("  " + label.padEnd(40) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] backslashes in a literal and in a string");
show("/\\d/.source", () => /\d/.source);
show("new RegExp('\\\\d').source", () => new RegExp("\\d").source);
show("new RegExp('\\d').source", () => new RegExp("\d").source);
show("new RegExp('\\d').test('7')", () => new RegExp("\d").test("7"));
show("new RegExp('\\d').test('d')", () => new RegExp("\d").test("d"));
show("new RegExp(String.raw`\\d`).test('7')", () => new RegExp(String.raw`\d`).test("7"));

console.log("");
console.log("[2] source and toString");
show("new RegExp('a/b').source", () => new RegExp("a/b").source);
show("String(new RegExp('a/b', 'g'))", () => String(new RegExp("a/b", "g")));
show("new RegExp('').source", () => new RegExp("").source);
show("new RegExp('\\n').source", () => J(new RegExp("\n").source));

console.log("");
console.log("[3] a user string used as a pattern");
const user = "1+1";
show("new RegExp(user).test('1+1')", () => new RegExp(user).test("1+1"));
show("new RegExp(user).test('11')", () => new RegExp(user).test("11"));
show("new RegExp('(').test('(')", () => new RegExp("(").test("("));

console.log("");
console.log("[4] a bad pattern in a literal -- when is it reported?");
show("new Function('return 1; /(/')", () => { new Function("return 1; /(/"); return "compiled"; });
show("new Function('if (false) /[/;')", () => { new Function("if (false) /[/;"); return "compiled"; });
```

- ★★★ `[1]` 의 `new RegExp('\d')` 줄이 `'7'` 에 무엇을 답하는지, 그리고 그 이유를 **두 단계**(문자열 → 패턴)로 설명해 보라.
- ★★ `[2]` 의 `source` 는 어떤 꼴로 적히나? 빈 패턴은?
- ★★ `[3]` 사용자 문자열 `"1+1"` 로 만든 정규식은 무엇을 찾나?
- ★★★ `[4]` 두 줄 — 실행되지 않는 자리의 잘못된 리터럴은 언제 드러나나?

### 9. 파이썬 `re` 에 같은 질문을 던지면 (연결) ★★

```sh
# js28b-29g-python.sh
#!/usr/bin/env bash
# 같은 질문을 파이썬 re 에 던진다 -- 어디서부터 찾나 · 같은 패턴 객체를 여러 번 쓰면 · 명명 그룹 문법.
set -u -o pipefail
python3 - <<'PY'
import re
def show(label, f):
    try:
        print("  " + label.ljust(40) + repr(f()))
    except Exception as e:
        print("  " + label.ljust(40) + type(e).__name__ + " 「" + str(e) + "」")

print("[1] match / search / fullmatch on 'xa'")
show("re.match('a', 'xa')", lambda: re.match("a", "xa"))
show("re.search('a', 'xa').span()", lambda: re.search("a", "xa").span())
show("re.fullmatch('x', 'xa')", lambda: re.fullmatch("x", "xa"))

print("")
print("[2] one compiled pattern, the same input, three calls")
p = re.compile("a")
show("p.search('a') x3", lambda: [bool(p.search("a")) for _ in range(3)])
show("hasattr(p, 'lastIndex')", lambda: hasattr(p, "lastIndex"))
show("p.search('aa', 1).span()", lambda: p.search("aa", 1).span())

print("")
print("[3] findall / finditer -- the counterparts of match(/g/) and matchAll")
show("re.findall(r'\\d', 'a1b22')", lambda: re.findall(r"\d", "a1b22"))
show("re.findall(r'(\\d)(\\d)?', 'a1b22')", lambda: re.findall(r"(\d)(\d)?", "a1b22"))
it = re.finditer(r"\d", "a1b22")
show("[m.group() for m in it]", lambda: [m.group() for m in it])
show("the same iterator again", lambda: [m.group() for m in it])

print("")
print("[4] named groups")
show("re.search('(?P<n>\\d)', 'a1').group('n')", lambda: re.search(r"(?P<n>\d)", "a1").group("n"))
show("re.search('(?<n>\\d)', 'a1')", lambda: re.search(r"(?<n>\d)", "a1"))
PY
```

- ★★★ `re.match` 와 `re.search` 는 JS 의 무엇과 짝이 맞나?
- ★★★ 파이썬 패턴 객체를 같은 입력에 세 번 쓰면? JS 의 1번 `[1]` 과 무엇이 다른가?
- ★★ `findall` 은 그룹이 있으면 무엇을 주나? 참여 안 한 그룹은?
- ★ JS 의 명명 그룹 문법을 파이썬에 주면?

### 10. `matchAll` 의 이터레이터와 19·21번 (연결) ★★

- ★★ 19번의 계약에서 **소비자가 `return()` 을 부르는 자리**가 있었다. `matchAll` 의 이터레이터에 `for...of` 도중 `break` 하면 무엇이 불리나?
- ★★ 21번이 본 「한 번 소비」와 3번 `[2]` 의 마지막 줄은 어떻게 이어지나?
- ★ `[Symbol.iterator]() === it` 은 19번의 어느 규칙인가?

### 11. 어디까지가 이 주제인가 — 28번 · 30번 · 알고리즘 25번 (경계) ★★

- ★★ 치환 문자열의 `$1`·`$<g>` 와 **치환 함수의 인자**는 각각 어느 주제가 정본인가?
- ★★ 명명 그룹의 **문법**과 `u`/`v` 플래그의 **뜻**은 어느 주제인가?
- ★★ 「본문에서 패턴을 어떻게 빨리 찾나」는 어느 갈래의 몇 번인가? 명세는 그것을 정하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
