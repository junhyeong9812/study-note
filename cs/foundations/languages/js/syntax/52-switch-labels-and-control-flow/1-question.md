# js/syntax/52 — `switch`·라벨·흐름 제어 세부: 「`case` 는 무엇으로 견주고, 몸통은 어떤 순서로 도나 — 라벨은 어디까지 뛰나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1 · v20.19.6 · Google Chrome 151 · x86-64 Linux. 세 판의 출력이 한 글자도 같았다.
>
> ★★★ **이 주제의 본체는 64칸 전수 격자다** — 판별식 여덟 × `case` 값 여덟을 `Object.is`·SameValueZero 와 견준다. **1번 · 2번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`case` 의 비교 — 그리고 `case` 가 줄지어 있을 때 어느 것이 이기나**
> ② ★★★ **`case` 식의 평가 순서 · 몸통의 순서 · `default` 의 자리**
> ③ ★★ **`switch` 블록의 스코프 · 라벨이 뛸 수 있는 범위.**
>
> **선행** — [32](../32-error-handling-and-error/2-summary.md) · [33](../33-equality-three-kinds/2-summary.md) · [05](../05-var-let-const-and-tdz/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번의 `[2]` 는 칸마다 `y`/`.` 만** 적어도 된다 — 그리고 **`Object.is` 라면 어느 칸이 달라지나**를 옆에 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 답은 명세 본문의 것인가, Annex B 의 것인가, 엔진 문구인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 판별식과 `case` 값의 격자 (예측) ★★★ 이 주제의 축

```js
// js48b-52a-case-grid.js
// js48b-52a-case-grid.js
// [1] One switch with nine case clauses and a default. For each discriminant: which clause does the switch enter,
//     and which clause would a search with Object.is (and with SameValueZero) pick from the same list?
// [2] Every discriminant against every case value, one clause at a time (a 8 x 8 matrix):
//     is the clause selected? The last lines count the cells where the switch answer differs from Object.is / SameValueZero.
const objA = { a: 1 };
const objB = { a: 1 };
const names = ["1", "'1'", "NaN", "-0", "0", "objA {a:1}", "null", "undefined"];
const values = [1, "1", NaN, -0, 0, objA, null, undefined];
const caseNames = ["1", "'1'", "NaN", "0", "-0", "objB {a:1}", "null", "undefined", "objA"];
const caseValues = [1, "1", NaN, 0, -0, objB, null, undefined, objA];
function enter(x) {
  switch (x) {
    case caseValues[0]: return caseNames[0];
    case caseValues[1]: return caseNames[1];
    case caseValues[2]: return caseNames[2];
    case caseValues[3]: return caseNames[3];
    case caseValues[4]: return caseNames[4];
    case caseValues[5]: return caseNames[5];
    case caseValues[6]: return caseNames[6];
    case caseValues[7]: return caseNames[7];
    case caseValues[8]: return caseNames[8];
    default: return "default";
  }
}
const sameValueZero = (a, b) => [a].includes(b);
const pick = (x, eq) => {
  const i = caseValues.findIndex((c) => eq(x, c));
  return i === -1 ? "default" : caseNames[i];
};
console.log("[1] case list in source order: " + caseNames.join(" | ") + " | default");
console.log("  " + "switch (x)".padEnd(14) + "switch enters".padEnd(16) + "Object.is picks".padEnd(18) + "SameValueZero picks");
for (let i = 0; i < values.length; i++) {
  console.log("  " + names[i].padEnd(14) + enter(values[i]).padEnd(16) + pick(values[i], Object.is).padEnd(18) + pick(values[i], sameValueZero));
}
console.log("");
console.log("[2] one clause at a time: y = the clause is selected (rows: discriminant, columns: case value)");
const colValues = values.slice();
colValues[5] = objB;
const colNames = names.slice();
colNames[5] = "objB";
const selected = (x, c) => { switch (x) { case c: return true; default: return false; } };
console.log("  " + "".padEnd(12) + colNames.map((n) => n.padEnd(10)).join("").trimEnd());
let cells = 0, vsIs = 0, vsZero = 0;
const diffIs = [];
for (let i = 0; i < values.length; i++) {
  let line = "  " + names[i].padEnd(12);
  for (let j = 0; j < colValues.length; j++) {
    const s = selected(values[i], colValues[j]);
    cells += 1;
    if (s !== Object.is(values[i], colValues[j])) { vsIs += 1; diffIs.push(names[i] + " / " + colNames[j]); }
    if (s !== sameValueZero(values[i], colValues[j])) vsZero += 1;
    line += (s ? "y" : ".").padEnd(10);
  }
  console.log(line.trimEnd());
}
console.log("  cells that differ from Object.is: " + diffIs.join(" · "));
console.log("cells where switch differs from Object.is: " + vsIs + " / " + cells + " · from SameValueZero: " + vsZero + " / " + cells);
```

- ★★★ `[1]` 여덟 줄에서 `switch enters` 열은? `Object.is picks`·`SameValueZero picks` 와 다른 줄은 어디인가?
- ★★★ `[2]` 64칸 가운데 `y` 인 칸은? 마지막 줄의 두 `N / 64` 는?

### 2. `case` 식에 심은 로그 (예측) ★★★

```js
// js48b-52b-clause-order.js
// js48b-52b-clause-order.js
// The order in which a switch tests case expressions and runs clause bodies.
// test(name, v) logs "test <name>" and returns v, so every evaluated case expression leaves a trace.
// Source order of the clauses in both switches: case A (1) · default · case B (2) · case C (3).
let log;
const test = (name, v) => { log.push("test " + name); return v; };
function noBreak(x) {
  log = [];
  switch (x) {
    case test("A", 1): log.push("body A");
    default: log.push("body default");
    case test("B", 2): log.push("body B");
    case test("C", 3): log.push("body C");
  }
  return log.join(" > ");
}
function withBreak(x) {
  log = [];
  switch (x) {
    case test("A", 1): log.push("body A"); break;
    default: log.push("body default"); break;
    case test("B", 2): log.push("body B"); break;
    case test("C", 3): log.push("body C"); break;
  }
  return log.join(" > ");
}
console.log("[1] no break anywhere");
for (const x of [1, 2, 3, 9]) console.log("  x = " + x + "   " + noBreak(x));
console.log("[2] break at the end of every clause");
for (const x of [1, 2, 3, 9]) console.log("  x = " + x + "   " + withBreak(x));
console.log("[3] two clauses with the same value");
function twice(x) {
  log = [];
  switch (x) {
    case test("first 1", 1): log.push("body first"); break;
    case test("second 1", 1): log.push("body second"); break;
  }
  return log.join(" > ");
}
console.log("  x = 1   " + twice(1));
console.log("[4] where the discriminant is evaluated");
function once() {
  log = [];
  switch (test("discriminant", 3)) {
    case test("A", 1): break;
    case test("B", 2): break;
    case test("C", 3): log.push("body C"); break;
  }
  return log.join(" > ");
}
console.log("  " + once());
```

- ★★★ `[1]` 네 줄(`x = 1 · 2 · 3 · 9`)의 로그는? `[2]` 네 줄은?
- ★★ `[3]`·`[4]` 의 로그는?

### 3. `case` 안의 선언 (예측) ★★

```js
// js48b-52c-switch-scope.js
// js48b-52c-switch-scope.js
// Declarations inside the clauses of a switch. Each snippet is compiled with new Function and then called,
// so a SyntaxError (at compile time) and an error thrown while running are told apart.
const run = (label, body) => {
  let f;
  try { f = new Function(body); } catch (e) { console.log("  " + label.padEnd(44) + "compile: " + e.constructor.name + " 「" + e.message + "」"); return; }
  try { console.log("  " + label.padEnd(44) + "run: " + String(f())); }
  catch (e) { console.log("  " + label.padEnd(44) + "run: " + e.constructor.name + " 「" + e.message + "」"); }
};
console.log("[1] let with the same name in two clauses");
run("case 0: let a · case 1: let a", "switch (1) { case 0: let a = 'zero'; return a; case 1: let a = 'one'; return a; }");
run("the same, each clause in braces", "switch (1) { case 0: { let a = 'zero'; return a; } case 1: { let a = 'one'; return a; } }");
run("case 0: var a · case 1: var a", "switch (1) { case 0: var a = 'zero'; return a; case 1: var a = 'one'; return a; }");
run("case 0: let a · case 1: var a", "switch (1) { case 0: let a = 'zero'; return a; case 1: var a = 'one'; return a; }");
console.log("[2] a let declared in one clause, used in another");
run("case 0: let a · case 1: return a", "switch (1) { case 0: let a = 'zero'; case 1: return a; }");
run("case 0: let a · case 1: a = 'one'", "switch (1) { case 0: let a = 'zero'; case 1: a = 'one'; return a; }");
run("case 0: let a · case 1: typeof a", "switch (1) { case 0: let a = 'zero'; case 1: return typeof a; }");
run("case 0: let a · x = 0 falls into case 1", "switch (0) { case 0: let a = 'zero'; case 1: return a; }");
run("case 0: var a · case 1: return a", "switch (1) { case 0: var a = 'zero'; case 1: return a; }");
console.log("[3] const and function declarations");
run("case 0: const c · case 1: const c", "switch (1) { case 0: const c = 0; break; case 1: const c = 1; return c; }");
run("case 0: function g · case 1: g()", "switch (1) { case 0: function g() { return 'g'; } case 1: return g(); }");
run("the same, 'use strict'", "'use strict'; switch (1) { case 0: function g() { return 'g'; } case 1: return g(); }");
run("case 0: function h · case 1: function h", "switch (1) { case 0: function h() { return 0; } case 1: function h() { return 1; } } return h();");
run("the same, 'use strict'", "'use strict'; switch (1) { case 0: function h() { return 0; } case 1: function h() { return 1; } }");
run("case 0: class K · case 1: new K", "switch (1) { case 0: class K {} case 1: return typeof new K(); }");
```

- ★★ 줄마다 `compile:` 인가 `run:` 인가? `run:` 이면 값인가 예외인가?

### 4. 라벨 — 실행되는 부분 (예측) ★★

```js
// js48b-52d-labels.js
// js48b-52d-labels.js
// Labels with break and continue. [1]-[3] run; [4] compiles snippets with new Function and prints what happens.
const out = [];
console.log("[1] nested loops, break and continue with and without the label");
outer: for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (j === 1) continue outer;
    out.push(i + "" + j);
  }
}
console.log("  continue outer at j === 1   " + out.join(" "));
out.length = 0;
outer2: for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (i === 1 && j === 1) break outer2;
    out.push(i + "" + j);
  }
}
console.log("  break outer2 at i,j === 1,1 " + out.join(" "));
out.length = 0;
for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (i === 1 && j === 1) break;
    out.push(i + "" + j);
  }
}
console.log("  plain break at i,j === 1,1  " + out.join(" "));

console.log("[2] a label on a block that is not a loop");
out.length = 0;
block: {
  out.push("a");
  if (out.length === 1) break block;
  out.push("b");
}
out.push("after");
console.log("  " + out.join(" > "));

console.log("[3] break and continue inside a switch that sits in a loop");
out.length = 0;
for (let i = 0; i < 4; i++) {
  switch (i) {
    case 1: out.push("case 1 break"); break;
    case 2: out.push("case 2 continue"); continue;
    default: out.push("default " + i);
  }
  out.push("end of body " + i);
}
console.log("  " + out.join(" > "));

console.log("[4] compiled with new Function");
const compile = (label, body) => {
  let r;
  try { r = "compiles, returns " + String(new Function(body)()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(40) + r);
};
compile("break nope   (no such label)", "for (;;) { break nope; }");
compile("blk: { continue blk; }", "blk: { continue blk; }");
compile("blk: { break blk; }", "blk: { break blk; } return 'ok';");
compile("break outside any loop or switch", "break;");
compile("continue in a switch, no loop", "switch (1) { case 1: continue; }");
compile("a: a: ;   (the same label twice)", "a: a: ;");
compile("break outer inside a callback", "outer: for (const x of [1]) { [1].forEach(() => { break outer; }); }");
compile("lbl: function f() {}", "lbl: function f() {} return typeof f;");
compile("'use strict'; lbl: function f() {}", "'use strict'; lbl: function f() {}");
```

- ★★ `[1]` 세 줄 · `[2]` 한 줄 · `[3]` 한 줄은?

### 5. 라벨 — `new Function` 으로 컴파일한 조각 (예측) ★★

- ★★ 4번 소스의 `[4]` 줄 가운데 **컴파일되는 것**은? 나머지는 각각 무슨 예외로 막히나?

### 6. `NaN` 을 거르는 `switch` (왜) ★★★

- ★★★ `case NaN:` 은 왜 어떤 판별식에도 안 걸리나? 명세 연산 이름으로 답하고, `NaN` 을 `switch` 모양으로 거르려면 어떻게 쓰나?

### 7. `default` 의 자리 (경계) ★★★

- ★★★ `default` 가 목록 중간에 있을 때, 아무 `case` 도 안 맞는 값은 **어느 `case` 식을 평가한 뒤** `default` 에 들어가고, 그 뒤에 **어느 몸통**이 도나? 명세 `CaseBlockEvaluation` 의 어느 단계가 그것을 정하나?

### 8. `case` 식의 부작용 (왜) ★★

- ★★ `case` 식에 부작용이 있는 호출을 쓰면 왜 「값마다 평가 개수가 다르다」 가 되나? `switch (true) { case 조건: … }` 관용구는 그 성질의 어느 쪽에 기대나?

### 9. Annex B 에 기대는 칸 (경계) ★★

- ★★ 3번·5번의 줄 가운데 **엄격 모드에서만 결과가 달라지는** 줄은? 그 줄들은 왜 ECMA-262 본문이 아니라 Annex B 의 층인가? 그 줄의 예외 문구를 근거로 쓰면 왜 안 되나?

### 10. Go 의 `switch` 와 견주면 (연결) ★★

- ★★ Go 15번과 견주어, 「흘러내림」 이 **기본값인가 · 적어야 하는가 · 다음 `case` 의 조건을 보나** 세 가지를 JS·Go·Java(화살표) 로 갈라라.

### 11. `finally` 와 라벨 (연결) ★

- ★ 32번의 `out: { try { return "T"; } finally { break out; } }` 는 무엇을 돌려주었나? 이 문서의 라벨 블록 `break` 와 그 결과를 이어서 설명하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
