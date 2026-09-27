# js/syntax/05 — `var`·`let`·`const` 와 TDZ: 「이 이름은 언제부터 쓸 수 있나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **선언 전에 건드리면 `undefined` 냐 `ReferenceError` 냐** ② **TDZ 가 어디서 시작해 어디서 끝나나**
> ③ **`const` 가 고정하는 것이 이름이냐 값이냐**.
> ★★★ **「버그처럼 보이는데 명세가 보장하는 것」과 「호스트가 정하는 것」을 가르는 것**이 이 갈래의 축이다 — 9번이 그 문항이다.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★ **6번은 Node 로만 풀면 반쪽이다.** 브라우저에 같은 줄을 던져야 답이 선다.
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md).
> ★★ 거기서 **`typeof` 가 TDZ 에서 터지는 것**을 이미 봤다. 이 주제는 그것을 **여섯 줄 격자로 넓힌다.**

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「열두 칸 중 몇 칸이 터지나」를 세는 것이 답의 절반**이다.
- ★★★ **2번은 「같은 함수가 왜 앞뒤로 다른 답을 내나」까지 적어야** 답이다.
- ★★ **4번은 「어느 조합이 통과하고, 통과한 것이 무엇을 만들었나」 둘 다** 적어야 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여섯 선언을 두 가지 방법으로 건드리면 (예측) ★★★ 이 주제의 축

```js
// js05b-05a-hoisting-grid.js
// 선언 여섯 가지를 「선언문 앞」에서 두 가지 방법으로 건드려 본다.
// 라벨은 전부 ASCII 다 — 한글을 padEnd 격자에 넣으면 칸이 어긋난다.
function fmt(v) {
  if (typeof v === "function") return "[Function: " + (v.name || "anonymous") + "]";
  if (v === undefined) return "undefined";
  return JSON.stringify(v);
}
function probe(read) {
  try { return fmt(read()); }
  catch (e) { return e.constructor.name + ": " + e.message; }
}

const rows = [
  ["var v",        () => { const a = probe(() => v),    b = probe(() => typeof v);    var v = 1;      return [a, b]; }],
  ["let l",        () => { const a = probe(() => l),    b = probe(() => typeof l);    let l = 1;      return [a, b]; }],
  ["const c",      () => { const a = probe(() => c),    b = probe(() => typeof c);    const c = 1;    return [a, b]; }],
  ["function f",   () => { const a = probe(() => f),    b = probe(() => typeof f);    function f() {} return [a, b]; }],
  ["class K",      () => { const a = probe(() => K),    b = probe(() => typeof K);    class K {}      return [a, b]; }],
  ["(undeclared)", () => { const a = probe(() => nope), b = probe(() => typeof nope);                 return [a, b]; }],
];

console.log("decl".padEnd(14) + "read it".padEnd(56) + "typeof it");
console.log("-".repeat(14) + "-".repeat(56) + "-".repeat(46));
for (const [label, run] of rows) {
  const [a, b] = run();
  console.log(label.padEnd(14) + a.padEnd(56) + b);
}

console.log("");
console.log("[함수 선언은 이름만이 아니라 본문까지 이미 있다]");
function early() { const s = f(1); function f(x) { return x + 1; } return s; }
console.log("  calling f(1) before its declaration -> " + early());
```

- 열두 칸(여섯 줄 × 두 칸)을 각각 적으면?
- ★★★ **터지는 칸은 몇 개**이고 어느 것인가?
- ★★★ **두 칸의 답이 어긋나는 줄**은 어느 것이고 **왜** 어긋나는가?
- ★★ `ReferenceError` 의 **문구가 두 가지**다 — 무엇이 무엇을 뜻하는가?
- ★★ 「`let` 은 호이스팅이 안 된다」를 이 출력으로 **반박하면**?
- ★ 마지막 줄이 보이는 것은 무엇인가? `var` 로 만든 함수 표현식도 그런가?

### 2. 블록에 들어선 순간과 선언문이 실행되는 순간 (예측) ★★★

```js
// js05b-05b-tdz-boundary.js
// TDZ 는 어디서 시작하고 어디서 끝나는가 — 같은 클로저를 두 번 불러 가른다.
function probe(label, read) {
  let r;
  try { r = JSON.stringify(read()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(30) + " -> " + r);
}

let v = "outer";
console.log("[1] TDZ 는 선언문 줄이 아니라 블록 진입에서 시작한다");
console.log("  (바깥에 v = \"outer\" 가 있다 — 그것이 보이는지를 본다)");
{
  probe("block entered", () => v);
  const peek = () => v;
  probe("peek() before the let", peek);
  let v = "inner";
  probe("after the let stmt", () => v);
  probe("the same peek() again", peek);
}

console.log("");
console.log("[2] 끝나는 것은 선언문이 놓인 줄이 아니라 그 문장이 실행되는 순간이다");
function late(flag) {
  const read = () => w;
  if (flag) probe("read() with flag=true", read);
  let w = 1;
  probe("read() after the let ran", read);
}
late(true);

console.log("");
console.log("[3] 초기화자가 없어도 TDZ 는 있다");
{ probe("before `let u;`", () => u); let u; probe("after  `let u;`", () => u); }

console.log("");
console.log("[4] 매개변수 기본값에도 TDZ 가 있고 왼쪽에서 오른쪽이다");
function ok(a = 1, b = a + 1) { return [a, b]; }
function bad(a = b, b = 2) { return [a, b]; }
probe("ok()  -- b sees a", () => ok());
probe("bad() -- a sees b", () => bad());

console.log("");
console.log("[5] class 선언도 TDZ 에 들어가고 function 선언은 안 들어간다");
probe("new K() before class K", () => new K());
probe("g() before function g", () => g());
class K {}
function g() { return "g ran"; }
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 **바깥에 `v = "outer"` 가 있는데도** 왜 그것이 안 읽히는가? 이것이 무엇을 증명하는가?
- ★★★ `[2]` 의 **같은 클로저**가 앞뒤로 다른 답을 낸다 — 무엇이 바뀐 것인가?
- ★★ `[3]` 의 두 줄은 **어떤 두 상태**를 가르는가?
- ★★ `[4]` 에서 되는 것과 안 되는 것을 가르는 규칙을 **한 문장으로**?
- ★ `[5]` 에서 `class` 와 `function` 이 갈리는 이유는?

### 3. `const` 로 묶어 두면 무엇이 안 되나 (예측) ★★★

```js
// js05b-05d-const.js
// const 는 무엇을 고정하는가 — 이름이냐 값이냐.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(34) + " -> " + r);
}

console.log("[1] const 가 고정하는 것은 이름이지 그 뒤의 값이 아니다");
probe("const n = 1; n = 2", () => { const n = 1; n = 2; return n; });
probe("const o = {}; o.k = 1", () => { const o = {}; o.k = 1; return o; });
probe("const a = []; a.push(1)", () => { const a = []; a.push(1); return a; });
probe("const o = {}; o = {}", () => { const o = {}; o = {}; return o; });

console.log("");
console.log("[2] 값까지 고정하고 싶으면 그것은 다른 도구다");
probe("frozen.k = 1 (sloppy)", () => { const o = Object.freeze({ k: 0 }); o.k = 1; return o; });
probe("frozen.k = 1 (strict)", () => { "use strict"; const o = Object.freeze({ k: 0 }); o.k = 1; return o; });
probe("freeze is shallow", () => { const o = Object.freeze({ inner: { k: 0 } }); o.inner.k = 1; return o; });

console.log("");
console.log("[3] const 는 초기화자가 있어야 하고 let 은 없어도 된다");
for (const src of ["const c;", "let l;", "const c = 1;"]) {
  let r; try { new Function(src); r = "parsed ok"; }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + src.padEnd(34) + " -> " + r);
}

console.log("");
console.log("[4] 루프의 const — for-of 는 회차마다 새 이름, for(;;) 는 아니다");
probe("for (const x of [1,2,3])", () => { const seen = []; for (const x of [1, 2, 3]) seen.push(x); return seen; });
probe("for (const k in {a:1,b:2})", () => { const seen = []; for (const k in { a: 1, b: 2 }) seen.push(k); return seen; });
probe("for (const i=0; i<3; i++)", () => new Function("for (const i = 0; i < 3; i++) {} return 'ran';")());

console.log("");
console.log("[5] 섀도잉은 재선언이 아니다 — 안쪽 블록은 같은 이름을 다시 쓸 수 있다");
probe("inner block shadows outer", () => {
  const n = "outer";
  let inner;
  { const n = "inner"; inner = n; }
  return [n, inner];
});
probe("same block twice", () => new Function("const n = 1; const n = 2; return n;")());
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 **터지는 둘과 안 터지는 둘**을 가르는 기준은 무엇인가?
- ★★ `[2]` 의 첫 두 줄이 **왜 다른가**? 「에러가 안 났다」가 「먹혔다」인가?
- ★★ `[3]` 은 **런타임 에러인가 파싱 에러인가**? 그것이 왜 중요한가?
- ★★ `[4]` 에서 `for (const x of ...)` 는 되고 `for (const i = 0; ...)` 는 안 된다 — **왜**인가?
- ★ `[5]` 의 두 줄이 가르는 두 낱말은?

### 4. 같은 이름을 두 번 쓰면 (예측) ★★★

```js
// js05b-05f-redeclare.js
// 같은 이름을 두 번 선언하면 — SyntaxError 는 잡을 수 없으므로 new Function 으로 파싱만 시킨다.
// ★ new Function 을 쓰는 이유: 파일을 던지면 진단에 절대 경로가 박힌다. 여기서는 타입과 문구만 받는다.
function parse(src) {
  try { new Function(src); return "parsed ok"; }
  catch (e) { return e.constructor.name + ": " + e.message; }
}

const cases = [
  "var a = 1; var a = 2;",
  "let a = 1; let a = 2;",
  "const a = 1; const a = 2;",
  "var a = 1; let a = 2;",
  "let a = 1; var a = 2;",
  "let a = 1; const a = 2;",
  "function a() {} function a() {}",
  "let a = 1; function a() {}",
  "var a = 1; function a() {}",
  "let a = 1; { let a = 2; }",
  "let a = 1; function f(a) {}",
  "function f(a, a) { return a; }",
  "'use strict'; function f(a, a) { return a; }",
];

console.log("source".padEnd(46) + "result");
console.log("-".repeat(46) + "-".repeat(52));
for (const src of cases) console.log(src.padEnd(46) + parse(src));

console.log("");
console.log("[통과한 것이 실제로 무엇을 만들었나 — 통과도 출력이다]");
console.log("  var a=1; var a=2 -> a is " + new Function("var a = 1; var a = 2; return a;")());
console.log("  function a twice -> a() is " + new Function("function a(){return 1} function a(){return 2} return a();")());
console.log("  sloppy dup param -> f(1,2) is " + new Function("function f(a, a) { return a; } return f(1, 2);")());
```

- 열세 줄의 결과를 각각 적으면?
- ★★★ **통과하는 줄은 몇 개**이고 어느 것인가?
- ★★★ 통과한 것들이 **실제로 무엇을 만들었나**? (마지막 묶음)
- ★★ 마지막 두 줄은 **무엇이 답을 바꿨나**?
- ★★ 이 에러는 **언제 나는가**? 그 파일의 다른 코드는 도는가?
- ★ `let a = 1; { let a = 2; }` 가 통과하는 이유는? 그것을 부르는 이름은?

### 5. 루프가 끝난 뒤, 그리고 루프가 만든 함수들 (예측) ★★

```js
// js05b-05e-loop-scope.js
// for 루프의 var 와 let — 블록 스코프와 함수 스코프의 차이가 가장 크게 벌어지는 자리.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(30) + " -> " + r);
}

console.log("[1] 루프가 끝난 뒤에 그 이름이 남아 있나");
probe("var: read i after loop", () => { for (var i = 0; i < 3; i++) {} return i; });
probe("let: read i after loop", () => { for (let i = 0; i < 3; i++) {} return i; });

console.log("");
console.log("[2] 루프 안에서 만든 함수 셋을 나중에 부르면");
function withVar() { const fns = []; for (var i = 0; i < 3; i++) fns.push(() => i); return fns.map((f) => f()); }
function withLet() { const fns = []; for (let i = 0; i < 3; i++) fns.push(() => i); return fns.map((f) => f()); }
probe("var", withVar);
probe("let", withLet);

console.log("");
console.log("[3] 블록 하나로도 갈린다 — if 블록 안의 선언");
probe("var inside if block", () => { if (true) { var a = 1; } return typeof a; });
probe("let inside if block", () => { if (true) { let b = 1; } return typeof b; });

console.log("");
console.log("[4] var 는 블록을 몇 겹이든 빠져나오지만 함수는 못 빠져나온다");
probe("var out of nested blocks", () => { { { var q = 7; } } return q; });
probe("let out of nested blocks", () => { { { let q = 7; } } return typeof q; });
probe("var out of a function", () => { function inner() { var deep = 7; } inner(); return typeof deep; });
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ `[2]` 의 두 줄을 **「나중에 읽어서」로 설명하면 어디가 부족한가**?
- ★★ `[4]` 의 세 줄로 **「함수 스코프」를 한 문장으로** 정의하면?
- ★★ `var` 를 `let` 으로 일괄 치환하면 **어느 줄이 깨지는가**?
- ★ 이 출력에서 **06번 주제가 이어받을 칸**은 무엇인가?

### 6. 이 파일의 최상위는 전역인가 (예측) ★★★

```js
// js05b-05c-globalthis.js
// 「전역 var 는 globalThis 에 붙는다」 — 어디까지 참인가.
// 이 파일 자체는 Node 의 CommonJS 모듈이다. 그 사실이 답의 절반이다.
const vm = require("vm");   // Node 내장 — 진짜 전역 스코프에서 스크립트를 돌린다
function line(label, value) { console.log("  " + label.padEnd(38) + " -> " + JSON.stringify(value)); }
const desc = (k) => Object.getOwnPropertyDescriptor(globalThis, k);

var topVar = 1;
let topLet = 2;

console.log("[1] 이 파일은 Node 가 감싼 모듈이라 최상위가 전역 스코프가 아니다");
line("typeof module", typeof module);
line("this === module.exports", this === module.exports);
line("top-level arrow arguments.length", (() => arguments.length)());
line("what those 5 arguments are", Array.from(arguments, (a) => typeof a));
line("globalThis.topVar", globalThis.topVar);
line("globalThis.topLet", globalThis.topLet);

console.log("");
console.log("[2] 진짜 전역 스코프의 스크립트 — vm.runInThisContext");
vm.runInThisContext("var sv = 1; let sl = 2; const sc = 3; function sf(){}");
line("globalThis.sv", globalThis.sv);
line("descriptor of sv", desc("sv"));
line("'sl' in globalThis", "sl" in globalThis);
line("'sc' in globalThis", "sc" in globalThis);
line("descriptor of sf", desc("sf"));

console.log("");
console.log("[3] let/const 도 거기 있다 — 다만 프로퍼티가 아닐 뿐이다");
line("a later script reading sl", vm.runInThisContext("sl"));
line("a later script reading sc", vm.runInThisContext("sc"));

console.log("");
console.log("[4] var 가 만든 전역 프로퍼티는 못 지우고 그냥 대입한 것은 지워진다");
line("delete globalThis.sv", vm.runInThisContext("delete globalThis.sv"));
line("globalThis.sv after delete", globalThis.sv);
globalThis.plain = 1;
line("delete globalThis.plain", delete globalThis.plain);
(0, eval)("var ev = 1;");
line("descriptor of an eval-made var", desc("ev"));

console.log("");
console.log("[5] 전역 let 은 두 번째 선언을 거부한다 — 스크립트가 달라도");
for (const src of ["let sl = 9;", "var sl = 9;", "var sv = 9;"]) {
  let r; try { vm.runInThisContext(src); r = "ok"; }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + src.padEnd(38) + " -> " + r);
}
```

그리고 같은 것을 브라우저에 던진다 — 호스트 페이지는 네 줄이다.

```text
<!doctype html><meta charset="utf-8"><title>this in a browser</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js05b-07g-browser.js"></script>
```

```js
// js05b-07g-browser.js
var declaredVar = "on window";
let declaredLet = "not on window";

function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis (window)";
  if (typeof t === "object" || typeof t === "function") return Object.prototype.toString.call(t);
  return typeof t + " " + String(t);
}
function loose() { return tag(this); }
function tight() { "use strict"; return tag(this); }
const obj = { name: "obj", hello() { return "hi " + this.name; } };
const detached = obj.hello;

const rows = [
  ["top-level this in a classic script", tag(this)],
  ["sloppy f()", loose()],
  ["strict f()", tight()],
  ["globalThis === window", String(globalThis === window)],
  ["window.name is", JSON.stringify(window.name)],
  ["obj.hello()", obj.hello()],
  ["detached hello() -- the silent one", detached()],
  ["window.declaredVar", String(window.declaredVar)],
  ["window.declaredLet", String(window.declaredLet)],
  ["declaredLet read by name", String(declaredLet)],
  ["top-level arrow: arguments?", (() => { try { return String(arguments.length); } catch (e) { return e.constructor.name + ": " + e.message; } })()],
];

setTimeout(function () {
  rows.push(["setTimeout(fn) this", tag(this)]);
  document.getElementById("out").textContent =
    rows.map(([k, v]) => k.padEnd(38) + " : " + v).join("\n");
}, 0);
```

- 두 블록의 출력을 각각 적으면?
- ★★★ `[1]` 에서 **최상위 화살표의 `arguments.length` 가 왜 `5`** 인가? 브라우저에서는 무엇이 되는가?
- ★★★ 「전역 `var` 는 `globalThis` 에 붙는다」는 **어디까지 참인가**?
- ★★ `sl`·`sc` 가 `globalThis` 에 없는데 **다음 스크립트는 왜 읽을 수 있나**?
- ★★ `var` 가 만든 전역 프로퍼티 · 그냥 대입한 프로퍼티 · `eval` 이 만든 것 — **셋이 어떻게 다른가**?
- ★ 브라우저 출력에서 `window.name` 이 `""` 인 것은 **어느 주제로 이어지는가**?

### 7. `typeof` 의 특권과 그 구멍 (왜) ★★

- ★★★ `typeof` 가 안 터지는 자리는 **정확히 어디**인가? 한 문장으로.
- ★★★ TDZ 에서 `typeof` 가 **터져야 하는 이유**를 「칸」의 말로 설명하면?
- ★★ `typeof x === "undefined"` 가 **참이 되는 상태가 몇 개**인가?
- ★★ 「`typeof` 로 방어한다」는 관용구가 **어느 코드에서 정확히 깨지는가**?
- ★ 이 사실의 **정본은 어느 주제**이고 이 주제는 무엇을 더했는가?

### 8. 세 가지 「아직 없음」 (경계) ★★

- **「칸이 없다」·「칸이 잠겼다」·「칸에 `undefined` 가 있다」** 셋을 각각 무엇으로 가리는가?
- ★★ 이 셋 중 **`ReferenceError` 가 나는 것은 몇 개**인가?
- ★★ 셋을 가르는 **유일한 근거가 예외 문구**라는 것이 왜 문제인가?
- ★ `let u;` 와 `let u = undefined;` 는 구분되는가?
- ★ 「호이스팅이 안 된다」가 맞는 상태는 셋 중 어느 것인가?

### 9. 보장인가 호스트인가 사정인가 (연결) ★★★ 이 갈래의 축

- ★★★ 이 주제에서 **명세 보장** 칸에 들어가는 것 다섯을 대면?
- ★★★ **호스트가 정하는** 칸에는 무엇이 들어가는가? ECMA-262 가 안 정하는 것은 무엇인가?
- ★★★ 「전역 `var` 가 `globalThis` 에 붙는다」는 **어느 칸**인가?
- ★★ 예외의 **종류**와 **문구**는 같은 칸인가? 이 주제에서 그것이 왜 특히 아픈가?
- ★★ 「두 판에서 같았다」는 어느 칸의 근거가 되는가? 어느 칸은 못 되는가?
- ★ 이 주제에서 **가장 얇은 칸**은 어느 것인가?

### 10. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **클로저** · **`this`** · **엄격 모드** · **모듈의 최상위** 는 각각 어느 주제가 정본인가?
- ★★★ 06번이 이 주제에서 **무엇을 이어받는가**? 한 문장으로.
- ★★ 파이썬에는 **블록 스코프가 없다** — 그쪽 갈래와 어떻게 갈리는가?
- ★ 「`let` 이 언제 들어왔나」는 왜 이 주제가 아닌가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
