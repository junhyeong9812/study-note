# js/syntax/10 — 구조 분해 할당: 「왼쪽은 값이 아니라 모양이다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ④ 예외의 `constructor.name` + `message` 다.**
> 구조 분해의 값은 성공했을 때가 아니라 **실패했을 때** 나온다 — **예외 문구 자체가 교재**다.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **무엇을 뜯을 수 있고 무엇을 못 뜯나** ② ★★★ **두 패턴의 실패가 왜 다른 실패인가** ③ **실제로 무엇을 부르나**.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★★★ **문구에 박히는 변수 이름은 근거가 아니다.** V8 은 그 자리의 소스 텍스트를 메시지에 넣는다 —
> 답할 때 **종류를 먼저** 적고 문구는 그 다음이다.
> ★ **3번은 로그를 심어야 보이는 문항이다.** 「무엇이 나오나」가 아니라 「**무엇을 부르나**」를 묻는다.
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 네 문항(1\~4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **2번은 「몇 칸이 터졌나」를 먼저 세는 것이 답의 절반**이다.
- ★★★ **3번은 「몇 번 불렀나」와 「언제 닫았나」를 같이** 적어야 답이다.
- ★★ **4번은 「왜 엄격을 먼저 돌렸나」까지** 답해야 한다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 묶음을 뜯으면 (예측) ★★

```js
// js08b-10a-forms.js
// 구조 분해 -- 형태마다 무엇을 꺼내는가. 왼쪽은 「모양」이고 오른쪽은 「값」이다.
function show(label, run) {
  try { console.log("  " + label.padEnd(44) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(44) + " -> " + e.constructor.name + ": " + e.message); }
}
// undefined 가 JSON 에서 사라지거나 null 로 보이는 것을 막는다 -- 이 주제는 그 자리가 답이다.
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));

console.log("[1] array pattern -- position decides");
show("const [a, b] = [1, 2]", () => { const [a, b] = [1, 2]; return J([a, b]); });
show("const [, b] = [1, 2]  hole", () => { const [, b] = [1, 2]; return J(b); });
show("const [a, , c] = [1, 2, 3]", () => { const [a, , c] = [1, 2, 3]; return J([a, c]); });
show("const [a, b, c] = [1, 2]  short", () => { const [a, b, c] = [1, 2]; return J([a, b, c]); });
show("const [a, ...r] = [1, 2, 3]", () => { const [a, ...r] = [1, 2, 3]; return J([a, r]); });
show("const [a, ...r] = [1]", () => { const [a, ...r] = [1]; return J([a, r]); });
show("const [[x], [y]] = [[1], [2]]", () => { const [[x], [y]] = [[1], [2]]; return J([x, y]); });
show("const [a, b] = 'hi'  string", () => { const [a, b] = "hi"; return J([a, b]); });
show("const [a, b] = new Set([1, 2])", () => { const [a, b] = new Set([1, 2]); return J([a, b]); });
show("const [[k, v]] = new Map([['x', 1]])", () => { const [[k, v]] = new Map([["x", 1]]); return J([k, v]); });

console.log("");
console.log("[2] object pattern -- the key decides, order does not");
show("const { a, b } = { b: 2, a: 1 }", () => { const { a, b } = { b: 2, a: 1 }; return J([a, b]); });
show("const { a: x } = { a: 1 }  rename", () => { const { a: x } = { a: 1 }; return J(x); });
show("const { a: { b } } = { a: { b: 1 } }", () => { const { a: { b } } = { a: { b: 1 } }; return J(b); });
show("const { missing } = { a: 1 }", () => { const { missing } = { a: 1 }; return J(missing); });
show("const { a, ...rest } = { a: 1, b: 2, c: 3 }", () => { const { a, ...rest } = { a: 1, b: 2, c: 3 }; return J([a, rest]); });
const key = "dyn";
show("const { [key]: v } = { dyn: 9 }  computed", () => { const { [key]: v } = { dyn: 9 }; return J(v); });
show("const { length } = 'abc'  primitive", () => { const { length } = "abc"; return J(length); });
show("const { toFixed } = 7  from prototype", () => { const { toFixed } = 7; return typeof toFixed; });
show("const { 0: first } = ['a', 'b']  index key", () => { const { 0: first } = ["a", "b"]; return J(first); });
const sym = Symbol("s");
show("const { [sym]: sv } = { [sym]: 1 }", () => { const { [sym]: sv } = { [sym]: 1 }; return J(sv); });

console.log("");
console.log("[3] what object rest copies -- and what it leaves behind");
const src = { a: 1, b: 2 };
Object.defineProperty(src, "hidden", { value: 3, enumerable: false });
src[sym] = 4;
Object.defineProperty(src, "getter", { get() { return 5; }, enumerable: true });
const proto = { inherited: 6 };
Object.setPrototypeOf(src, proto);
const { a, ...restOf } = src;
show("own enumerable string keys", () => J(Object.keys(restOf)));
show("non-enumerable 'hidden' copied?", () => Object.prototype.hasOwnProperty.call(restOf, "hidden"));
show("symbol key copied?", () => Object.prototype.hasOwnProperty.call(restOf, sym));
show("inherited 'inherited' copied?", () => Object.prototype.hasOwnProperty.call(restOf, "inherited"));
show("getter copied as a value?", () => J(Object.getOwnPropertyDescriptor(restOf, "getter")));
show("prototype of the rest object", () => String(Object.getPrototypeOf(restOf) === Object.prototype));
const nested = { inner: { n: 1 } };
const { ...shallow } = nested;
shallow.inner.n = 99;
show("rest is a shallow copy", () => J(nested));

console.log("");
console.log("[4] assignment without a declaration -- the parentheses are not optional");
show("({ a: A } = { a: 1 })", () => { let A; ({ a: A } = { a: 1 }); return J(A); });
show("[p, q] = [1, 2]  no parens needed", () => { let p, q; [p, q] = [1, 2]; return J([p, q]); });
show("swap: [p, q] = [q, p]", () => { let p = 1, q = 2; [p, q] = [q, p]; return J([p, q]); });
show("{ a: A } = { a: 1 }  without parens", () => new Function("let A; { a: A } = { a: 1 }; return A;")());
show("target can be a property", () => { const t = {}; [t.x, t.y] = [1, 2]; return J(t); });
show("target can be an index", () => { const t = []; ({ a: t[0] } = { a: 7 }); return J(t); });
```

- 네 묶음의 출력을 각각 적으면?
- ★★ `[1]` 에서 **배열이 아닌데 배열 패턴으로 뜯어진 것은 몇 개**인가?
- ★★★ `[2]` 에서 **원시값을 객체 패턴으로 뜯은 두 줄**은 무엇을 돌려주는가? 어느 주제가 그 근거인가?
- ★★★ `[3]` 의 일곱 줄에서 **객체 나머지가 안 가져오는 것 셋**을 대면? getter 는 무엇이 되는가?
- ★★ `[4]` 에서 **괄호가 없으면 왜 `SyntaxError`** 인가? 배열 패턴은 왜 안 그런가?

### 2. 값 열다섯 × 패턴 넷 (예측) ★★★ 이 주제의 축

```js
// js08b-10b-failures.js
// 구조 분해가 어디서 터지나 -- 값 12종 x 패턴 4종 전수 격자.
// 예외는 constructor.name 과 message 로만 찍는다. 이 주제의 답은 그 문구에 다 있다.
const VALUES = [
  ["{ a: 1 }", () => ({ a: 1 })],
  ["[1, 2]", () => [1, 2]],
  ["'ab'", () => "ab"],
  ["7", () => 7],
  ["0", () => 0],
  ["true", () => true],
  ["false", () => false],
  ["null", () => null],
  ["undefined", () => undefined],
  ["NaN", () => NaN],
  ["Symbol('s')", () => Symbol("s")],
  ["10n", () => 10n],
  ["function f() {}", () => function f() {}],
  ["new Set([1])", () => new Set([1])],
  ["{ length: 1 }", () => ({ length: 1 })],
];
const PATTERNS = [
  ["{ a }", (v) => { const { a } = v; return "a=" + String(a); }],
  ["{}", (v) => { const {} = v; return "ok"; }],
  ["[a]", (v) => { const [a] = v; return "a=" + String(a); }],
  ["[]", (v) => { const [] = v; return "ok"; }],
];

console.log("[1] value x pattern -- what comes out, or what is thrown");
console.log(("  " + "value".padEnd(18) + PATTERNS.map(([p]) => p.padEnd(16)).join("")).replace(/ +$/, ""));
const errs = [];
let thrown = 0;
for (const [vlabel, make] of VALUES) {
  const cells = [];
  for (const [plabel, run] of PATTERNS) {
    try { cells.push(run(make()).padEnd(16)); }
    catch (e) { thrown += 1; cells.push((e.constructor.name).padEnd(16)); errs.push([vlabel, plabel, e.constructor.name + ": " + e.message]); }
  }
  console.log("  " + vlabel.padEnd(18) + cells.join("").replace(/ +$/, ""));
}
console.log("  " + "cells thrown".padEnd(18) + thrown + " of " + VALUES.length * PATTERNS.length);

console.log("");
console.log("[2] the messages behind the thrown cells");
for (const [v, p, msg] of errs) console.log("  " + (p + " = " + v).padEnd(26) + msg);

console.log("");
console.log("[3] the same two failures are not the same failure");
const probe = [
  ["const { a } = null", () => { const { a } = null; return a; }],
  ["const [a] = null", () => { const [a] = null; return a; }],
  ["const { a } = {}", () => { const { a } = {}; return String(a); }],
  ["const [a] = {}", () => { const [a] = {}; return String(a); }],
  ["const [a] = { length: 1 }", () => { const [a] = { length: 1 }; return String(a); }],
  ["const [a] = { 0: 'x', length: 1 }", () => { const [a] = { 0: "x", length: 1 }; return String(a); }],
  ["Array.from({ 0: 'x', length: 1 })", () => JSON.stringify(Array.from({ 0: "x", length: 1 }))],
  ["const { a } = Object.create(null)", () => { const { a } = Object.create(null); return String(a); }],
];
for (const [label, run] of probe) {
  try { console.log("  " + label.padEnd(36) + " -> " + run()); }
  catch (e) { console.log("  " + label.padEnd(36) + " -> " + e.constructor.name + ": " + e.message); }
}

console.log("");
console.log("[4] a default value turns the undefined case into a value -- and only that case");
const withDefault = [
  ["const { a = 'D' } = { a: undefined }", () => { const { a = "D" } = { a: undefined }; return String(a); }],
  ["const { a = 'D' } = { a: null }", () => { const { a = "D" } = { a: null }; return String(a); }],
  ["const { a = 'D' } = {}", () => { const { a = "D" } = {}; return String(a); }],
  ["const { a = 'D' } = null", () => { const { a = "D" } = null; return String(a); }],
  ["const [a = 'D'] = [undefined]", () => { const [a = "D"] = [undefined]; return String(a); }],
  ["const [a = 'D'] = [null]", () => { const [a = "D"] = [null]; return String(a); }],
  ["const [a = 'D'] = []", () => { const [a = "D"] = []; return String(a); }],
  ["const [a = 'D'] = null", () => { const [a = "D"] = null; return String(a); }],
  ["const { a: { b } = {} } = {}", () => { const { a: { b } = {} } = {}; return String(b); }],
  ["const { a: { b } } = {}", () => { const { a: { b } } = {}; return String(b); }],
];
for (const [label, run] of withDefault) {
  try { console.log("  " + label.padEnd(40) + " -> " + run()); }
  catch (e) { console.log("  " + label.padEnd(40) + " -> " + e.constructor.name + ": " + e.message); }
}
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 60칸 중 **터진 칸은 몇 개**인가?
- ★★★ **객체 패턴이 거부하는 값은 몇 개**이고 무엇인가? **배열 패턴이 받아들이는 값은 몇 개**인가?
- ★★★ **빈 패턴(`{}` · `[]`)은 안 터질 것 같은데** 어떤가? 왜 그런가?
- ★★ `[2]` 에서 `{ a } = null` 과 `{} = null` 의 **문구가 다르다.** 무엇이 다른가?
- ★★★ `[3]` 에서 `const { a } = {}` 와 `const [a] = {}` 가 갈린다. **같은 오른쪽인데** 무엇이 가른 것인가?
- ★★★ `[4]` 에서 `{ a = 'D' } = { a: null }` 은 무엇인가? 기본값은 `null` 을 구해 주는가?
- ★★ `[4]` 의 마지막 두 줄에서 **기본값을 어디에 달았느냐**가 왜 갈리는가?

### 3. 로그를 심으면 무엇이 보이나 (예측) ★★★

```js
// js08b-10c-order.js
// 구조 분해가 실제로 무엇을 부르나 -- 추상 연산에 로그를 심어 호출 순서를 받는다.
const log = [];
function reset() { log.length = 0; }
function dump(label) { console.log("  " + label.padEnd(40) + JSON.stringify(log)); }

console.log("[1] object pattern -- the pattern's order wins, not the object's");
const src = {
  get b() { log.push("get b"); return 2; },
  get a() { log.push("get a"); return 1; },
  get c() { log.push("get c"); return 3; },
};
reset(); { const { a, b } = src; } dump("const { a, b } = src");
reset(); { const { b, a } = src; } dump("const { b, a } = src");
reset(); { const { a } = src; } dump("const { a } = src");
reset(); { const {} = src; } dump("const {} = src");
reset(); { const { ...all } = src; } dump("const { ...all } = src");
reset(); { const { a, ...rest } = src; } dump("const { a, ...rest } = src");

console.log("");
console.log("[2] a default is evaluated only when the slot is undefined");
function d(n) { log.push("default " + n); return n; }
const obj2 = { present: 1, undef: undefined, nul: null };
reset(); { const { present = d(1) } = obj2; } dump("{ present = d(1) }");
reset(); { const { undef = d(2) } = obj2; } dump("{ undef = d(2) }");
reset(); { const { nul = d(3) } = obj2; } dump("{ nul = d(3) }");
reset(); { const { missing = d(4) } = obj2; } dump("{ missing = d(4) }");
reset(); { const { absent: renamed = d(5) } = obj2; } dump("{ absent: renamed = d(5) }");

console.log("");
console.log("[3] array pattern goes through the iterator protocol, not through indexes");
function tracked(values) {
  return {
    [Symbol.iterator]() {
      let i = 0;
      log.push("Symbol.iterator");
      return {
        next() { log.push("next " + i); return i < values.length ? { value: values[i++], done: false } : { value: undefined, done: true }; },
        return(v) { log.push("return"); return { value: v, done: true }; },
      };
    },
  };
}
reset(); { const [a, b] = tracked([1, 2, 3]); } dump("const [a, b] = tracked(3 items)");
reset(); { const [a] = tracked([1, 2, 3]); } dump("const [a] = tracked(3 items)");
reset(); { const [] = tracked([1, 2, 3]); } dump("const [] = tracked(3 items)");
reset(); { const [a, ...r] = tracked([1, 2, 3]); } dump("const [a, ...r] = tracked(3 items)");
reset(); { const [a, b, c, d2] = tracked([1, 2]); } dump("const [a,b,c,d] = tracked(2 items)");
reset(); { const [, , third] = tracked([1, 2, 3]); } dump("const [, , third] = tracked(3)");

console.log("");
console.log("[4] the array's own iterator can be replaced -- destructuring follows it");
const arr = [10, 20, 30];
arr[Symbol.iterator] = function () {
  let i = arr.length;
  return { next: () => (i > 0 ? { value: arr[--i], done: false } : { value: undefined, done: true }) };
};
const [first, second] = arr;
console.log("  " + "const [first, second] = arr".padEnd(40) + JSON.stringify([first, second]));
console.log("  " + "arr[0], arr[1] are still".padEnd(40) + JSON.stringify([arr[0], arr[1]]));
const { 0: byKey, 1: byKey2 } = arr;
console.log("  " + "object pattern reads keys instead".padEnd(40) + JSON.stringify([byKey, byKey2]));

console.log("");
console.log("[5] a failing pattern still closes the iterator");
function throwing() {
  return {
    [Symbol.iterator]() {
      let i = 0;
      return {
        next() { log.push("next"); const v = i === 1 ? null : i; i += 1; return { value: v, done: false }; },
        return() { log.push("return called"); return { done: true }; },
      };
    },
  };
}
reset();
try { const [a, { b }] = throwing(); } catch (e) { log.push("threw " + e.constructor.name); }
dump("const [a, { b }] = throwing()");
reset();
try { const [a, b] = throwing(); } catch (e) { log.push("threw"); }
dump("const [a, b] = throwing()  plain");
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 `{ a, b }` 와 `{ b, a }` 의 로그가 다른가? **누구의 순서**인가?
- ★★ `{ ...all }` 은 몇 개를 읽는가? 그 순서는 누구의 것인가?
- ★★★ `[3]` 에서 `const [a, b] = it(3)` 은 `next` 를 **몇 번** 부르고 마지막에 **무엇을** 부르는가?
- ★★★ `const [a, ...r] = it(3)` 은 왜 **`return` 을 안 부르는가**?
- ★★ `const [] = it(3)` 은 아무것도 안 뜯는데 왜 **이터레이터를 얻는가**?
- ★★★ `[4]` 에서 같은 배열을 두 패턴으로 읽었더니 답이 갈렸다. **무엇을 증명하는가**?
- ★★ `[5]` 에서 예외가 나는데도 `return called` 가 찍혔다. 무엇을 보장하는 것인가?

### 4. 매개변수 자리와 설정에 달린 칸 (예측) ★★

```js
// js08b-10d-params.js
// 매개변수 자리의 구조 분해 -- 그리고 설정(엄격/비엄격)에 달린 칸.
// ★ 엄격 쪽을 먼저 돌린다. 비엄격이 먼저 돌면 암시적 전역이 만들어져 엄격 쪽이 그것을 읽는다.
const PROBES = [
  ["no declaration keyword", `
    ({ a: gObj } = { a: 1 });
    return "typeof gObj = " + typeof gObj;
  `],
  ["array target, no declaration", `
    [gArr] = [1];
    return "typeof gArr = " + typeof gArr;
  `],
  ["f({ a }) called with nothing", `
    function f({ a }) { return a; }
    return String(f());
  `],
  ["f({ a } = {}) called with nothing", `
    function f({ a } = {}) { return String(a); }
    return f();
  `],
  ["f({ a = 1 } = {}) called with nothing", `
    function f({ a = 1 } = {}) { return String(a); }
    return f();
  `],
  ["f([a, b]) called with nothing", `
    function f([a, b]) { return a; }
    return String(f());
  `],
  ["f([a, b]) called with an object", `
    function f([a, b]) { return a; }
    return String(f({}));
  `],
  ["f({ a }, { a })  same name twice", `
    function f({ a }, { a }) { return a; }
    return String(f({ a: 1 }, { a: 2 }));
  `],
  ["f(a, { a })  name reused", `
    function f(a, { a }) { return a; }
    return String(f(1, { a: 2 }));
  `],
  ["const { a, a } = { a: 1 }", `
    const { a, a } = { a: 1 };
    return String(a);
  `],
  ["var { a } = {}; var { a } = {}", `
    var { a } = { a: 1 };
    var { a } = { a: 2 };
    return String(a);
  `],
  ["f({ a }) { 'use strict'; }", `
    function f({ a }) { "use strict"; return a; }
    return String(f({ a: 1 }));
  `],
];

function run(body, strict) {
  const src = (strict ? '"use strict";\n' : "") + body;
  try { return String(new Function(src)()); }
  catch (e) { return (e instanceof SyntaxError ? "COMPILE " : "") + e.constructor.name + ": " + e.message; }
}

console.log("[1] sloppy vs strict -- same probe, compiled twice");
let differ = 0;
for (const [label, body] of PROBES) {
  const t = run(body, true), s = run(body, false);
  if (s !== t) differ += 1;
  console.log("  " + label);
  console.log("    " + "sloppy".padEnd(8) + s);
  console.log("    " + "strict".padEnd(8) + t + (s === t ? "" : "   <-- DIFFERENT"));
}
console.log("");
console.log("  " + "settings-dependent cells".padEnd(30) + differ + " of " + PROBES.length);

console.log("");
console.log("[2] length and name when the parameter is a pattern");
const fns = [
  ["function ({ a })", function ({ a }) {}],
  ["function ({ a } = {})", function ({ a } = {}) {}],
  ["function ([a, b])", function ([a, b]) {}],
  ["function (x, { a })", function (x, { a }) {}],
  ["function ({ a }, ...r)", function ({ a }, ...r) {}],
];
for (const [label, f] of fns) console.log("  " + label.padEnd(28) + "length " + f.length);

console.log("");
console.log("[3] the shapes that read well in real code");
function point({ x = 0, y = 0, label = "p" } = {}) { return label + "(" + x + "," + y + ")"; }
console.log("  " + "point()".padEnd(34) + point());
console.log("  " + "point({ x: 1 })".padEnd(34) + point({ x: 1 }));
console.log("  " + "point({ y: 2, label: 'q' })".padEnd(34) + point({ y: 2, label: "q" }));
const entries = Object.entries({ a: 1, b: 2 });
const joined = entries.map(([k, v]) => k + "=" + v).join(",");
console.log("  " + "entries.map(([k, v]) => ...)".padEnd(34) + joined);
const rows = [{ id: 1, tags: ["x", "y"] }];
const firstTag = rows.map(({ id, tags: [head] }) => id + ":" + head).join(",");
console.log("  " + "nested pattern in a callback".padEnd(34) + firstTag);
function head([first, ...rest] = []) { return String(first) + " / " + JSON.stringify(rest); }
console.log("  " + "head([1, 2, 3])".padEnd(34) + head([1, 2, 3]));
console.log("  " + "head()".padEnd(34) + head());
```

- 세 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 **설정에 달린 칸은 몇 개**인가? 어느 것인가?
- ★★★ 이 격자는 **왜 엄격 쪽을 먼저 돌려야** 하는가? 안 그러면 무엇이 나오는가?
- ★★★ `f({ a })` 와 `f({ a } = {})` 와 `f({ a = 1 } = {})` 를 인자 없이 부르면 각각?
- ★★ 중복 이름이 막히는 네 줄은 **각각 다른 이유**인가? 문구로 갈리는가?
- ★ `[2]` 에서 패턴 매개변수의 `length` 는 어떻게 세어지는가? 어느 주제의 규칙인가?

### 5. 두 패턴은 왜 다른 실패를 하나 (왜) ★★★

- 객체 패턴이 뜯기 전에 묻는 것은 무엇인가? 배열 패턴은?
- ★★★ 그래서 **`7` 은 한쪽만 통과하고 `{ length: 1 }` 도 한쪽만 통과한다.** 각각 어느 쪽인가?
- ★★ `Array.from({ 0: 'x', length: 1 })` 은 되는데 `const [a] = { 0: 'x', length: 1 }` 은 안 된다. 왜인가?

### 6. 기본값은 무엇을 막고 무엇을 못 막나 (경계) ★★★

- 기본값이 걸리는 조건은 무엇인가? **하나인가 여럿인가**?
- ★★★ `const { a = 1 } = { a: null }` 의 답과 그 실무적 결과는?
- ★★ 「바깥 기본값」과 「안쪽 기본값」은 각각 무엇을 막는가?
- ★ 이 규칙은 [08번](../08-function-forms-and-parameters/2-summary.md)의 무엇과 같은가?

### 7. 객체 나머지는 무엇을 복사하나 (경계) ★★

- **비열거 프로퍼티** · **심볼 키** · **상속된 프로퍼티** · **getter** 는 각각 어떻게 되는가?
- ★★ 복사된 것의 프로토타입은 무엇인가?
- ★★★ 「비밀 필드만 빼고 넘기기」(`const { secret, ...safe } = o`)가 **안전하지 않은 경우**가 있다. 무엇인가?

### 8. 어디서 조용히 틀리나 (경계) ★★

- 이 주제에서 **에러 없이 틀리는 자리** 셋을 대면?
- ★★ 비싼 getter 가 있는 객체에 `{ ...rest }` 를 쓰면?
- ★ 선언 키워드를 빼먹으면 비엄격에서 무엇이 생기는가?

### 9. 보장인가 엔진 사정인가 (연결) ★★★

- 이 주제에서 **두 판이 갈린 자리는 몇 개**였는가?
- ★★★ 예외 **문구**를 근거로 쓰면 안 되는 이유를 **이 주제의 출력에서** 대면?
- ★★ 브라우저에 같은 줄을 던졌을 때 **호스트가 정하는 칸은 몇 개**였는가? 문구까지 같은 이유는?
- ★ 이 주제에서 **부적용인 창**은 무엇인가?

### 10. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **이터러블 프로토콜** · **스프레드 세 자리** · **`null` 막기** · **열거 순서** · **깊은 복사** 는 각각 어느 주제가 정본인가?
- ★★★ 08번에서 **무엇을 이어받는가**? 한 문장으로.
- ★★ 파이썬의 `a, *rest = seq` 와 이 주제의 배열 패턴은 무엇이 닮고 무엇이 다른가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
