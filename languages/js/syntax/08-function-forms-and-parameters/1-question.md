# js/syntax/08 — 함수 정의 형태와 매개변수: 「이 형태는 무엇을 가지고 무엇을 안 가지나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.** 형태 16 × 칸 7 을 **손으로 한 칸도 안 채우고** 받아 놓고 읽는다.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **형태마다 무엇이 딸려 오나** ② ★★★ **`arguments` 가 언제 매개변수와 한 몸인가** ③ **기본값은 언제 평가되나**.
> ★★★ **[07번](../07-this-binding-four-rules/2-summary.md)이 「어떤 호출식이 어떤 `this` 를 주나」였다면 여기는 「어떤 형태가 애초에 `this` 칸을 갖나」다.**
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★★ **`SyntaxError` 격자는 `new Function` 으로 두 번 컴파일해 받는다** — 파일로 던지면 진단에 경로가 박힌다.
> ★ **5번은 파이썬과 나란히 놓아야 반이 풀린다.** 같은 모양의 코드가 정반대로 동작한다.
>
> **선행** — [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) · [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md) · [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「어느 칸과 어느 칸이 따로 노는가」까지 적어야** 답이다. 반례가 둘 있다.
- ★★★ **4번은 「몇 칸이 갈렸나」를 먼저 세는 것이 답의 절반**이다.
- ★★★ **5번은 「파이썬이었다면」을 같이 적어야** 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 열여섯 형태를 한 격자에 놓으면 (예측) ★★★ 이 주제의 축

```js
// js08b-08a-forms.js
// 함수를 만드는 형태마다 무엇이 달라지나 -- 손으로 한 칸도 안 채우고 전수 격자로 받는다.
// 보는 칸: typeof / name / length / prototype 소유 / new 가능 / 그냥 호출 가능 / 브랜드 태그
function decl(a, b) { return [a, b]; }
const anon = function (a, b) { return [a, b]; };
const named = function inner(a, b) { return [a, b]; };
const arrowConcise = (a, b) => [a, b];
const arrowBlock = (a, b) => { return [a, b]; };
const obj = {
  method(a, b) { return [a, b]; },
  *gen(a, b) { yield [a, b]; },
  async am(a, b) { return [a, b]; },
};
function* genDecl(a, b) { yield [a, b]; }
async function asyncDecl(a, b) { return [a, b]; }
const asyncArrow = async (a, b) => [a, b];
class K { constructor(a, b) { this.v = [a, b]; } }
const fromCtor = new Function("a", "b", "return [a, b];");
const bound = decl.bind(null, 1);
const withDefault = function (a, b = 2, c) { return [a, b, c]; };
const withRest = function (a, ...rest) { return [a, rest]; };

const probes = [
  ["function decl", decl],
  ["anon fn expr", anon],
  ["named fn expr", named],
  ["arrow concise", arrowConcise],
  ["arrow block", arrowBlock],
  ["method shorthand", obj.method],
  ["generator method", obj.gen],
  ["async method", obj.am],
  ["generator decl", genDecl],
  ["async decl", asyncDecl],
  ["async arrow", asyncArrow],
  ["class", K],
  ["new Function", fromCtor],
  ["bound fn", bound],
  ["default param", withDefault],
  ["rest param", withRest],
];

function canNew(f) {
  try { Reflect.construct(f, []); return "yes"; }
  catch (e) { return "no:" + e.constructor.name; }
}
function canCall(f) {
  try { const r = f(1, 2); if (r && typeof r.then === "function") r.then(() => {}, () => {}); return "yes"; }
  catch (e) { return "no:" + e.constructor.name; }
}

console.log("[1] form matrix -- 16 forms x 7 columns");
console.log("  " + "form".padEnd(18) + "typeof".padEnd(10) + "name".padEnd(16) +
            "len".padEnd(5) + "proto?".padEnd(8) + "new?".padEnd(14) + "call?".padEnd(14) + "brand");
for (const [label, f] of probes) {
  console.log("  " + label.padEnd(18) +
              (typeof f).padEnd(10) +
              JSON.stringify(f.name).padEnd(16) +
              String(f.length).padEnd(5) +
              String(Object.prototype.hasOwnProperty.call(f, "prototype")).padEnd(8) +
              canNew(f).padEnd(14) +
              canCall(f).padEnd(14) +
              Object.prototype.toString.call(f));
}

console.log("");
console.log("[2] name -- where does an unnamed function get its name");
const assigned = function () {};
const arrowAssigned = () => {};
let letAssigned; letAssigned = function () {};
const o2 = { key: function () {}, arrowKey: () => {} };
const arr2 = [function () {}];
const defaulted = (function (p = function () {}) { return p; })();
const rows = [
  ["const assigned", assigned],
  ["const arrow", arrowAssigned],
  ["let then assign", letAssigned],
  ["object literal key", o2.key],
  ["object literal arrow", o2.arrowKey],
  ["array element", arr2[0]],
  ["default value", defaulted],
  ["bound", decl.bind(null)],
  ["getter", Object.getOwnPropertyDescriptor({ get g() { return 1; } }, "g").get],
];
for (const [label, f] of rows) console.log("  " + label.padEnd(22) + JSON.stringify(f.name));

console.log("");
console.log("[3] arrow has no own arguments -- it reads the enclosing function's, by identity");
function outer(a, b) {
  const arrow = () => arguments;
  return [arguments, arrow()];
}
const [outerArgs, arrowArgs] = outer(10, 20);
console.log("  " + "same object?".padEnd(22) + String(outerArgs === arrowArgs));
console.log("  " + "outer arguments".padEnd(22) + JSON.stringify([...outerArgs]));
console.log("  " + "brand".padEnd(22) + Object.prototype.toString.call(outerArgs));
console.log("  " + "Array.isArray".padEnd(22) + String(Array.isArray(outerArgs)));
console.log("  " + "has callee?".padEnd(22) + String(Object.prototype.hasOwnProperty.call(outerArgs, "callee")));
console.log("  " + "Symbol.iterator?".padEnd(22) + String(typeof outerArgs[Symbol.iterator]));
```

- 세 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 **`prototype` 칸과 `new?` 칸이 같은 답을 주지 않는 행은 몇 개**인가? 어느 행인가?
- ★★★ `[1]` 에서 **`call?` 이 `no` 인 행은 몇 개**이고 왜인가?
- ★★ 브랜드 태그는 **몇 가지**로 갈리는가? 화살표와 메서드 단축 표기는 브랜드로 갈리는가?
- ★★ `[2]` 에서 **이름이 빈 문자열인 줄은 어느 것**이고 왜 그런가?
- ★ `[3]` 에서 화살표가 돌려준 `arguments` 는 **누구의 것**인가? 무엇으로 증명했는가?

### 2. 같은 줄 위에서 부르면 (예측) ★★★

```js
// js08b-08b-hoisting.js
// 선언·표현식·화살표의 호이스팅 차이 -- 같은 탐침을 두 모드로 두 번 컴파일해 격자로 받는다.
// new Function 을 쓰는 이유: 파일로 던지면 진단에 절대 경로가 박힌다. 여기서는 값과 문구만 받는다.
const HELPERS = `
  const snap = (label, run) => {
    try { return label.padEnd(34) + " -> " + String(run()); }
    catch (e) { return label.padEnd(34) + " -> " + e.constructor.name + ": " + e.message; }
  };
  const out = [];
`;
const PROBES = [
  ["decl called before its line", `
    out.push(snap("decl()", () => decl(1)));
    function decl(a) { return "decl ran " + a; }
  `],
  ["typeof decl before its line", `
    out.push(snap("typeof decl", () => typeof decl));
    function decl(a) { return a; }
  `],
  ["var fn expr before its line", `
    out.push(snap("typeof vexpr", () => typeof vexpr));
    out.push(snap("vexpr()", () => vexpr(1)));
    var vexpr = function (a) { return "vexpr ran " + a; };
  `],
  ["const fn expr before its line", `
    out.push(snap("typeof cexpr", () => typeof cexpr));
    out.push(snap("cexpr()", () => cexpr(1)));
    const cexpr = function (a) { return "cexpr ran " + a; };
  `],
  ["arrow before its line", `
    out.push(snap("typeof arr", () => typeof arr));
    out.push(snap("arr()", () => arr(1)));
    const arr = (a) => "arr ran " + a;
  `],
  ["decl inside a block, seen outside", `
    out.push(snap("typeof blockFn before", () => typeof blockFn));
    { function blockFn() { return "block"; } }
    out.push(snap("typeof blockFn after", () => typeof blockFn));
  `],
  ["decl inside if(false)", `
    if (false) { function deadFn() { return "dead"; } }
    out.push(snap("typeof deadFn", () => typeof deadFn));
  `],
  ["two decls with the same name", `
    function dup() { return "first"; }
    function dup() { return "second"; }
    out.push(snap("dup()", () => dup()));
  `],
  ["decl and var with the same name", `
    var both = 1;
    function both() { return "fn"; }
    out.push(snap("typeof both", () => typeof both));
  `],
];

function compile(body, strict) {
  const src = (strict ? '"use strict";\n' : "") + HELPERS + body + "\n  return out.join(String.fromCharCode(10));";
  try {
    const f = new Function(src);
    return f();
  } catch (e) {
    return "COMPILE " + e.constructor.name + ": " + e.message;
  }
}

console.log("[1] hoisting -- sloppy");
for (const [label, body] of PROBES) {
  console.log("  " + label);
  for (const line of String(compile(body, false)).split(String.fromCharCode(10))) console.log("    " + line);
}

console.log("");
console.log("[2] hoisting -- strict");
for (const [label, body] of PROBES) {
  console.log("  " + label);
  for (const line of String(compile(body, true)).split(String.fromCharCode(10))) console.log("    " + line);
}

console.log("");
console.log("[3] how many of the 9 probes differ between the two modes");
let differ = 0;
for (const [label, body] of PROBES) {
  const a = String(compile(body, false));
  const b = String(compile(body, true));
  const same = a === b;
  if (!same) differ += 1;
  console.log("  " + label.padEnd(34) + (same ? "same" : "DIFFERENT"));
}
console.log("  " + "total".padEnd(34) + differ + " of " + PROBES.length + " differ");
```

- 두 모드의 출력을 각각 적으면?
- ★★★ `[3]` 에서 **두 모드가 갈린 탐침은 몇 개**인가? 어느 것인가?
- ★★ `var` 로 받은 함수 표현식과 `const` 로 받은 것은 **왜 다른 예외**를 내는가?
- ★★ `if (false)` 안의 함수 선언은 비엄격에서 왜 `undefined` 인가? 「없다」와 어떻게 다른가?
- ★ 같은 이름의 함수 선언이 둘이면 어느 쪽이 이기는가? `var` 와 겹치면?

### 3. 기명 함수 표현식을 다섯 가지로 두드리면 (예측) ★★

```js
// js08b-08c-named-fexpr.js
// 기명 함수 표현식의 이름은 어디서 보이나 -- 안쪽에서만 보이고, 그 이름은 못 바꾼다.
function show(label, run) {
  try { console.log("  " + label.padEnd(38) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(38) + " -> " + e.constructor.name + ": " + e.message); }
}

console.log("[1] the name is visible inside, not outside");
const fact = function selfName(n) { return n <= 1 ? 1 : n * selfName(n - 1); };
show("fact(5)", () => fact(5));
show("fact.name", () => fact.name);
show("typeof selfName (outside)", () => typeof selfName);
show("selfName(5) (outside)", () => selfName(5));

console.log("");
console.log("[2] a function declaration puts its name outside too");
function declFact(n) { return n <= 1 ? 1 : n * declFact(n - 1); }
show("declFact(5)", () => declFact(5));
show("typeof declFact (outside)", () => typeof declFact);

console.log("");
console.log("[3] the inner name is an immutable binding -- sloppy is silent, strict throws");
const sloppyReassign = function me() {
  me = 1;
  return typeof me;
};
const strictReassign = function me2() {
  "use strict";
  try { me2 = 1; return "assigned, typeof " + typeof me2; }
  catch (e) { return e.constructor.name + ": " + e.message; }
};
show("sloppy: me = 1 then typeof me", () => sloppyReassign());
show("strict: me2 = 1", () => strictReassign());

console.log("");
console.log("[4] the inner binding lives in its own scope -- a parameter or a var shadows it");
const shadowByParam = function me3(me3) { return "param wins: " + typeof me3; };
show("named fn expr with param of same name", () => shadowByParam(42));
const shadowByVar = function me4() { var me4 = 7; return "var wins: " + typeof me4; };
show("named fn expr with var of same name", () => shadowByVar());
const notShadowed = function me5() { return "no shadow: " + typeof me5; };
show("named fn expr, nothing shadows", () => notShadowed());

console.log("");
console.log("[5] the name survives reassignment of the outer variable");
let holder = function me6(n) { return n <= 1 ? 1 : n * me6(n - 1); };
const saved = holder;
holder = function () { return "replaced"; };
show("saved(5) after holder replaced", () => saved(5));
show("holder(5)", () => holder(5));
const anonSelf = function (n) { return n <= 1 ? 1 : n * anonSelf(n - 1); };
const savedAnon = anonSelf;
show("anon self-recursion still works", () => savedAnon(5));
let anonSelf2 = function (n) { return n <= 1 ? 1 : n * anonSelf2(n - 1); };
const savedAnon2 = anonSelf2;
anonSelf2 = null;
show("anon self-recursion after var cleared", () => savedAnon2(5));
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★ `[3]` 에서 **같은 대입이 한쪽에서는 조용하고 한쪽에서는 터진다.** 각각 무엇인가?
- ★★ `[4]` 에서 같은 이름의 매개변수·`var` 가 있으면 **어느 쪽이 이기는가**?
- ★★★ `[5]` 의 마지막 두 줄이 **왜 갈리는가**? 기명으로 쓰면 무엇이 지켜지는가?

### 4. 같은 탐침을 두 모드로 — `arguments` (예측) ★★★

```js
// js08b-08d-arguments.js
// arguments 와 매개변수의 연동 -- 비엄격에서는 이어지고 엄격에서는 끊긴다.
// 같은 탐침을 두 번 컴파일해(그대로 / "use strict"; 붙여) 격자로 받는다.
const PROBES = [
  ["write param, read arguments", `
    function f(a) { a = 99; return "arguments[0]=" + arguments[0]; }
    return f(1);
  `],
  ["write arguments, read param", `
    function f(a) { arguments[0] = 99; return "a=" + a; }
    return f(1);
  `],
  ["two params, write the second", `
    function f(a, b) { b = 99; return "arguments=" + JSON.stringify([...arguments]); }
    return f(1, 2);
  `],
  ["param not passed, then written", `
    function f(a) { a = 99; return "len=" + arguments.length + " [0]=" + arguments[0]; }
    return f();
  `],
  ["delete arguments[0], then write param", `
    function f(a) { delete arguments[0]; a = 99; return "[0]=" + arguments[0] + " a=" + a; }
    return f(1);
  `],
  ["default param present", `
    function f(a, b = 2) { a = 99; return "arguments[0]=" + arguments[0]; }
    return f(1, 2);
  `],
  ["rest param present", `
    function f(a, ...r) { a = 99; return "arguments[0]=" + arguments[0]; }
    return f(1, 2);
  `],
  ["destructuring param present", `
    function f(a, { b } = {}) { a = 99; return "arguments[0]=" + arguments[0]; }
    return f(1, { b: 2 });
  `],
  ["arguments.callee", `
    function f(a) { return "callee is f? " + (arguments.callee === f); }
    return f(1);
  `],
  ["duplicate parameter names", `
    function f(a, a) { return "a=" + a + " arguments=" + JSON.stringify([...arguments]); }
    return f(1, 2);
  `],
  ["assign to arguments itself", `
    function f(a) { arguments = 1; return "arguments=" + arguments; }
    return f(1);
  `],
  ["arguments as a parameter name", `
    function f(arguments) { return "arguments=" + arguments; }
    return f(7);
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
  const s = run(body, false);
  const t = run(body, true);
  if (s !== t) differ += 1;
  console.log("  " + label);
  console.log("    " + "sloppy".padEnd(8) + s);
  console.log("    " + "strict".padEnd(8) + t + (s === t ? "" : "   <-- DIFFERENT"));
}
console.log("");
console.log("  " + "settings-dependent cells".padEnd(30) + differ + " of " + PROBES.length);

console.log("");
console.log("[2] arguments is not an array -- what it has and what it lacks");
function probe(a, b) { return arguments; }
const args = probe(1, 2, 3);
const rows = [
  ["brand", Object.prototype.toString.call(args)],
  ["Array.isArray", String(Array.isArray(args))],
  ["length", String(args.length)],
  ["fn.length", String(probe.length)],
  ["typeof args.map", typeof args.map],
  ["typeof args[Symbol.iterator]", typeof args[Symbol.iterator]],
  ["own keys", JSON.stringify(Object.getOwnPropertyNames(args))],
  ["proto is Object.prototype?", String(Object.getPrototypeOf(args) === Object.prototype)],
  ["spread to array", JSON.stringify([...args])],
  ["Array.from", JSON.stringify(Array.from(args))],
];
for (const [k, v] of rows) console.log("  " + k.padEnd(30) + v);

console.log("");
console.log("[3] rest is a real array -- the same probe with ...r");
function probe2(a, ...r) { return r; }
const rest = probe2(1, 2, 3);
const rows2 = [
  ["brand", Object.prototype.toString.call(rest)],
  ["Array.isArray", String(Array.isArray(rest))],
  ["length", String(rest.length)],
  ["fn.length", String(probe2.length)],
  ["typeof rest.map", typeof rest.map],
  ["holds", JSON.stringify(rest)],
  ["rest only takes the leftovers", JSON.stringify(probe2(1))],
];
for (const [k, v] of rows2) console.log("  " + k.padEnd(30) + v);
```

- `[1]` 의 열두 탐침을 두 모드로 각각 적으면?
- ★★★ **설정에 달린 칸은 몇 개**인가?
- ★★★ **기본 매개변수가 있는 탐침은 두 모드가 같았다.** 그것이 무엇을 뜻하는가?
- ★★ `[2]` 에서 `arguments` 가 **배열이 아니라는 근거 세 가지**를 대면? 그런데 왜 스프레드는 되는가?
- ★★ `[3]` 의 `fn.length` 두 줄이 다르다. **무엇을 세는 값이 다른가**?
- ★ `delete arguments[0]` 뒤에 매개변수를 고치면 어떻게 되는가?

### 5. 기본값을 세 번 부르면 (예측) ★★★ ★ 파이썬과 정반대

```js
// js08b-08e-defaults.js
// 기본 매개변수 -- 호출마다 평가된다. 그리고 앞 매개변수는 보이고 뒤 매개변수는 안 보인다.
function show(label, run) {
  try { console.log("  " + label.padEnd(46) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(46) + " -> " + e.constructor.name + ": " + e.message); }
}

console.log("[1] the default expression runs on every call -- not once at definition");
let evalCount = 0;
function fresh(list = (evalCount++, [])) { list.push("x"); return JSON.stringify(list); }
show("fresh() 1st", () => fresh());
show("fresh() 2nd", () => fresh());
show("fresh() 3rd", () => fresh());
show("how many times was it evaluated", () => evalCount);
const shared = [];
function notFresh(list = shared) { list.push("x"); return JSON.stringify(list); }
show("notFresh() 1st (shared array)", () => notFresh());
show("notFresh() 2nd (shared array)", () => notFresh());
show("passing a value skips the default", () => { evalCount = 0; fresh(["given"]); return "evals=" + evalCount; });

console.log("");
console.log("[2] what triggers the default -- only undefined does");
function trig(a = "DEFAULT") { return typeof a + " " + JSON.stringify(String(a)); }
for (const [label, run] of [
  ["trig()", () => trig()],
  ["trig(undefined)", () => trig(undefined)],
  ["trig(null)", () => trig(null)],
  ["trig(0)", () => trig(0)],
  ["trig('')", () => trig("")],
  ["trig(NaN)", () => trig(NaN)],
  ["trig(false)", () => trig(false)],
  ["trig(void 0)", () => trig(void 0)],
]) show(label, run);

console.log("");
console.log("[3] length counts only the params before the first default or rest");
const lens = [
  ["(a, b, c)", function (a, b, c) {}],
  ["(a, b = 1, c)", function (a, b = 1, c) {}],
  ["(a = 1, b, c)", function (a = 1, b, c) {}],
  ["(a, ...r)", function (a, ...r) {}],
  ["(...r)", function (...r) {}],
  ["({ a }, b)", function ({ a }, b) {}],
  ["(a, { b } = {})", function (a, { b } = {}) {}],
  ["()", function () {}],
];
for (const [label, f] of lens) console.log("  " + label.padEnd(46) + " -> length " + f.length);
console.log("  " + "arguments.length is what was passed".padEnd(46) + " -> " +
            (function (a, b = 1, c) { return arguments.length; })(1, 2, 3, 4));

console.log("");
console.log("[4] a default can see the params to its left, never the ones to its right");
show("(a, b = a * 2) with f(3)", () => (function (a, b = a * 2) { return a + "," + b; })(3));
show("(a = b, b = 2) with f()", () => (function (a = b, b = 2) { return a + "," + b; })());
show("(a = b, b = 2) with f(1)", () => (function (a = b, b = 2) { return a + "," + b; })(1));
show("(a = later()) with later below", () => {
  function g(a = later()) { return a; }
  function later() { return "hoisted decl is fine"; }
  return g();
});
show("(a = a) with f()", () => (function (a = a) { return a; })());

console.log("");
console.log("[5] a non-simple parameter list gets its own scope -- var in the body does not reach it");
show("param scope: (a, b = () => a) then var a = 99", () =>
  (function (a, b = () => a) { var a = 99; return "a=" + a + " b()=" + b(); })(1));
show("simple list for comparison (no default)", () =>
  (function (a, b) { var a = 99; return "a=" + a; })(1, 2));
show("default sees the outer binding, not the body var", () => {
  var outer = "outer";
  return (function (a = outer) { var outer = "body"; return "a=" + a + " outer=" + outer; })();
});
```

같은 모양의 코드를 파이썬에서 돌리면 어떻게 되는가? 이 파일도 같이 예측한다.

```python
# js08b-08p-default-contrast.py
# 같은 모양의 함수를 파이썬에서 -- 기본값은 정의 시점에 한 번만 만들어진다.
def fresh(items=[]):
    items.append("x")
    return items

print("[1] python: default evaluated once, at definition time")
print("  fresh() 1st   ->", fresh())
print("  fresh() 2nd   ->", fresh())
print("  fresh() 3rd   ->", fresh())
print("  the object itself ->", fresh.__defaults__)

print("")
print("[2] python: None does not trigger anything -- there is no undefined rule")
def trig(a="DEFAULT"):
    return (type(a).__name__, a)

print("  trig()        ->", trig())
print("  trig(None)    ->", trig(None))
print("  trig(0)       ->", trig(0))
```

- 두 파일의 출력을 각각 적으면?
- ★★★ `fresh()` 를 세 번 부르면 **JS 와 파이썬이 각각 무엇을 돌려주는가**? 한 줄로 이유를 대면?
- ★★★ `[2]` 에서 **기본값이 걸리는 값은 몇 개**이고 무엇인가? `null` 은?
- ★★ `[3]` 의 여덟 줄에서 `length` 를 각각 적으면? **무엇을 세는 값인가**?
- ★★ `[4]` 에서 **터지는 줄은 몇 개**이고 예외는 무엇인가?
- ★★★ `[5]` 의 첫 줄이 `a=99 b()=1` 이다. **한 함수 안에서 `a` 가 둘이라는 뜻인가**?

### 6. 매개변수 목록 스무 형태 (예측) ★★

```js
// js08b-08f-param-syntax.js
// 매개변수 목록의 문법 -- 무엇이 컴파일되고 무엇이 SyntaxError 인가.
// 같은 소스를 두 번 컴파일한다: 그대로(비엄격)와 "use strict"; 를 앞에 붙여(엄격).
const FORMS = [
  ["f(a, b)", "function f(a, b) {}"],
  ["f(a, b,)  trailing comma", "function f(a, b,) {}"],
  ["f(a, a)  duplicate", "function f(a, a) {}"],
  ["f(a, a = 1)  dup + default", "function f(a, a = 1) {}"],
  ["(a, a) => {}", "var g = (a, a) => {};"],
  ["f(a = 1) { 'use strict'; }", "function f(a = 1) { 'use strict'; }"],
  ["f(a, b) { 'use strict'; }", "function f(a, b) { 'use strict'; }"],
  ["f(a, a) { 'use strict'; }", "function f(a, a) { 'use strict'; }"],
  ["f(...r)", "function f(...r) {}"],
  ["f(...r,)  comma after rest", "function f(...r,) {}"],
  ["f(...r, b)  rest not last", "function f(...r, b) {}"],
  ["f(...r = [])  rest default", "function f(...r = []) {}"],
  ["f(a = 1, b)  default first", "function f(a = 1, b) {}"],
  ["f({ a }, [b])  destructured", "function f({ a }, [b]) {}"],
  ["f(eval)", "function f(eval) {}"],
  ["f(arguments)", "function f(arguments) {}"],
  ["(arguments) => {}", "var g = (arguments) => {};"],
  ["f(a) { var arguments; }", "function f(a) { var arguments; }"],
  ["f(yield)", "function f(yield) {}"],
  ["function* f(yield) {}", "function* f(yield) {}"],
];

function compile(src, strict) {
  try { new Function((strict ? '"use strict";\n' : "") + src); return "ok"; }
  catch (e) { return e.constructor.name + ": " + e.message; }
}

console.log("[1] parameter list forms -- compiled twice");
console.log("  " + "form".padEnd(32) + "sloppy".padEnd(8) + "strict");
let differ = 0;
for (const [label, src] of FORMS) {
  const s = compile(src, false);
  const t = compile(src, true);
  if (s !== t) differ += 1;
  console.log("  " + label.padEnd(32) + (s === "ok" ? "ok" : "ERR").padEnd(8) + (t === "ok" ? "ok" : "ERR") +
              (s === t ? "" : "   <-- DIFFERENT"));
}
console.log("  " + "settings-dependent cells".padEnd(32) + differ + " of " + FORMS.length);

console.log("");
console.log("[2] the messages behind the ERR cells");
for (const [label, src] of FORMS) {
  const s = compile(src, false);
  const t = compile(src, true);
  if (s !== "ok") console.log("  " + ("sloppy " + label).padEnd(42) + s);
  if (t !== "ok" && t !== s) console.log("  " + ("strict " + label).padEnd(42) + t);
}
```

- `[1]` 의 스무 줄을 두 모드로 각각 적으면?
- ★★★ **설정에 달린 칸은 몇 개**인가?
- ★★★ **비엄격에서도 터지는 줄은 몇 개**인가? 그 줄들의 공통점은?
- ★★ `function f(a = 1) { 'use strict'; }` 는 왜 터지는가? 이것이 실무에서 무엇을 막는가?
- ★ 나머지 매개변수가 내는 두 문구는 서로 무엇이 다른가?

### 7. `length` 는 무엇을 세나 (경계) ★★

- `(a, b = 1, c)` · `(a = 1, b, c)` · `(a, ...r)` · `({ a }, b)` 의 `length` 를 각각 대면?
- ★★ `arguments.length` 와 `fn.length` 는 **각각 언제 정해지는가**?
- ★ `fn.length` 로 콜백의 arity 를 보고 분기하는 라이브러리가 있다. 그 코드는 **어떤 변경에 조용히 깨지는가**?

### 8. 화살표를 그 자리에 쓰면 무엇을 잃나 (연결) ★★

- 화살표가 **안 만드는 칸 네 가지**를 대면?
- ★★ 객체 리터럴의 메서드 자리에 화살표를 쓰면 무엇이 깨지는가? 어느 주제가 정본인가?
- ★★ 생성자 자리에 화살표를 쓰면 **어떤 예외**가 나는가?
- ★ 반대로 **화살표가 정답인 자리** 둘을 대면?

### 9. 설정에 달린 칸이 몇 개인가 (경계) ★★★ 이 갈래의 축

- 이 주제의 세 격자에서 **엄격·비엄격이 갈린 칸의 개수**를 각각 대면?
- ★★★ **`arguments` 연동을 끊는 조건은 몇 개**인가? 엄격 모드 하나인가?
- ★★ 중복 매개변수 이름을 금지하는 **조건 세 가지**를 대면?
- ★ 이 주제의 규칙 중 **모듈(ESM)로 옮기면 저절로 바뀌는 것**은 무엇인가?

### 10. 보장인가 엔진 사정인가 (연결) ★★★

- 이 주제에서 **두 판이 갈린 자리는 몇 개**였고 무엇이었는가?
- ★★★ 그 차이는 **명세인가 V8 의 사정인가**? 어떻게 아는가?
- ★★ 브라우저에 같은 줄을 던졌을 때 **호스트가 정하는 칸은 몇 개**였는가? 07번과 견주면?
- ★ 이 주제에서 **부적용인 창**은 무엇이고 왜 부적용인가?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **`this` 네 규칙** · **TDZ** · **엄격 모드 전체** · **구조 분해 매개변수** · **타입 표기** 는 각각 어느 주제가 정본인가?
- ★★★ 07번에서 **무엇을 이어받는가**? 한 문장으로.
- ★★ 파이썬 갈래의 **19번·20번**과 이 주제의 경계는 무엇인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
