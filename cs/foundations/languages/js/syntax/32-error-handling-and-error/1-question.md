# js/syntax/32 — 오류 처리와 `Error`: 「`finally` 는 끝을 쥘 수 있나 · 원인은 어떻게 잇나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(헤드리스) · python3 3.12.3 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다. ★ **6번의 둘째 소스(`.web.js`)는 Chrome 에서만** 돌렸다 — 첫째 소스가 node 판에 그 기능이 있는지를 묻는다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> `try` 가 끝나는 세 방식 × `finally` 가 끝나는 세 방식을 전부 돌리고, 칸마다 **호출자가 받은 것**을 찍는다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`finally` 는 언제 `try` 의 끝을 버리나**
> ② **오류를 감싸 다시 던질 때 원인은 어떻게 이어지나**(`cause` · `AggregateError`)
> ③ **「이것이 오류인가」를 무엇으로 묻나**(`Error` 가 아닌 값 · 다른 realm · `stack`).
>
> ★★ **예외는 `이름 「메시지」` 꼴로 답한다.** `stack` 은 첫 줄 또는 「있나」만.
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) · [20 — 제너레이터](../20-generators/2-summary.md) · [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) · [31 — `JSON`](../31-json/2-summary.md).
> ★★★ **20번 3번의 `return()` 과 `finally` 를 먼저 떠올려라** — `finally` 안의 `yield` 와 `return "F"` 는 각각 무엇을 했나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 2 · 3 · 4 · 5 · 6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 아홉 칸을 하나씩 적고, 마지막 두 줄의 수까지 세어 본다.**
- ★★ **2번·3번은 「값」과 「예외」를 갈라서** 적어라. 예외면 종류와 메시지까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 호스트의 것인가, 이 판의 관찰인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「`try`/`catch` 는 느리다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `try` 와 `finally` 가 각각 세 가지로 끝나면 (예측) ★★★ 이 주제의 축

```js
// js32b-32a-finally-grid.js
// try 블록이 끝나는 세 방식 x finally 블록이 끝나는 세 방식 -- 호출자가 받는 것은 무엇인가.
// 칸마다: 호출자가 받은 것 / try 블록 자신의 끝(return 값 또는 던진 예외)이 호출자에게 닿았나.
const TRY = {
  "return 'T'": () => "T",
  "throw E('T')": () => { throw new Error("T"); },
  "(falls through)": () => undefined,
};
const FIN = {
  "return 'F'": "return",
  "throw E('F')": "throw",
  "(nothing)": "none",
};
const show = (r) => (r.threw ? r.value.constructor.name + " 「" + r.value.message + "」" : "value " + JSON.stringify(r.value));

function run(tryKind, finKind) {
  const log = [];
  const f = () => {
    try {
      log.push("try");
      const v = TRY[tryKind]();
      if (tryKind !== "(falls through)") return v;
    } finally {
      log.push("finally");
      if (FIN[finKind] === "return") return "F";
      if (FIN[finKind] === "throw") throw new Error("F");
    }
    log.push("after");
    return "after";
  };
  let r;
  try { r = { threw: false, value: f() }; } catch (e) { r = { threw: true, value: e }; }
  return { r, log };
}

console.log("[1] try x finally -- what the caller receives");
console.log("  " + "try ends with".padEnd(18) + "finally ends with".padEnd(19) + "try's own ending reached the caller?".padEnd(38) + "log".padEnd(24) + "caller receives");
let noAll = 0, cells = 0, noThrow = 0, throwCells = 0;
for (const t of Object.keys(TRY)) {
  for (const k of Object.keys(FIN)) {
    const { r, log } = run(t, k);
    // try 자신의 끝이 그대로 닿았나: return 'T' 면 값 "T", throw 면 메시지 "T" 인 예외, 흘러내리면 "after".
    let own;
    if (t === "return 'T'") own = !r.threw && r.value === "T";
    else if (t === "throw E('T')") own = r.threw && r.value.message === "T";
    else own = !r.threw && r.value === "after";
    cells += 1; if (!own) noAll += 1;
    if (t === "throw E('T')") { throwCells += 1; if (!own) noThrow += 1; }
    console.log("  " + t.padEnd(18) + k.padEnd(19) + (own ? "yes" : "no").padEnd(38) + log.join(" > ").padEnd(24) + show(r));
  }
}
console.log("");
console.log("rows where try threw and the caller never saw that exception: " + noThrow + " / " + throwCells);
console.log("cells where the try block's own ending did not reach the caller: " + noAll + " / " + cells);
```

- ★★★ 아홉 행 각각에서 `caller receives` 칸에는 무엇이 들어가나?
- ★★★ `try's own ending reached the caller?` 열이 `yes` 인 행은 어느 것인가?
- ★★ `log` 열에 `after` 가 찍히는 행은?
- ★★ 마지막 두 줄의 N 과 M 은?

### 2. `finally` 가 흐름에 끼어드는 다른 자리들 (예측) ★★★

```js
// js32b-32b-finally-details.js
// finally 가 흐름에 끼어드는 자리 넷 -- 반환값이 정해지는 시점 · 루프의 break · catch 와의 순서 · 바꿔치기된 예외에 남는 것.
const show = (f) => {
  try { return "value " + JSON.stringify(f()); }
  catch (e) { return e.constructor.name + " 「" + e.message + "」"; }
};
const row = (label, v) => console.log("  " + label.padEnd(46) + v);

console.log("[1] return x, then finally changes x");
row("primitive: return n; finally n = 2", show(() => { let n = 1; try { return n; } finally { n = 2; } }));
row("object: return o; finally o.v = 2", show(() => { const o = { v: 1 }; try { return o; } finally { o.v = 2; } }));
row("order of evaluation", show(() => {
  const log = [];
  const val = () => { log.push("return expr"); return "R"; };
  try { return val(); } finally { log.push("finally"); console.log("    log: " + log.join(" > ")); }
}));

console.log("[2] break / continue inside finally, with an exception in flight");
row("for: try throw; finally break", show(() => {
  for (let i = 0; i < 1; i++) { try { throw new Error("T"); } finally { break; } }
  return "after loop";
}));
row("for: try throw; finally continue", show(() => {
  let n = 0;
  for (let i = 0; i < 3; i++) { try { n++; throw new Error("T"); } finally { continue; } }
  return "after loop, n=" + n;
}));
row("label: try return; finally break out", show(() => {
  out: { try { return "T"; } finally { break out; } }
  return "after block";
}));

console.log("[3] catch and finally together");
const order = [];
row("try throw; catch returns; finally logs", show(() => {
  try { order.push("try"); throw new Error("T"); }
  catch (e) { order.push("catch"); return "C"; }
  finally { order.push("finally"); }
}));
row("  order", order.join(" > "));
row("try throw; catch throws; finally returns", show(() => {
  try { throw new Error("T"); } catch (e) { throw new Error("C"); } finally { return "F"; }
}));
row("try throw; catch throws; finally (nothing)", show(() => {
  try { throw new Error("T"); } catch (e) { throw new Error("C"); } finally { }
}));

console.log("[4] the replacing exception -- does it point back to the one it replaced?");
let caught;
try { try { throw new Error("T"); } finally { throw new Error("F"); } } catch (e) { caught = e; }
row("caught.message", caught.message);
row("'cause' in caught", "cause" in caught);
row("own keys of caught", JSON.stringify(Reflect.ownKeys(caught)));
```

- ★★★ `[1]` 원시값과 객체 두 줄은 각각 무엇을 돌려주나? `log:` 줄의 순서는?
- ★★★ `[2]` 세 줄 — 날아가던 예외는 어디로 갔나? `n=` 뒤의 수는?
- ★★ `[3]` `order` 줄과, `catch` 가 던진 두 줄의 결과는?
- ★★★ `[4]` 잡힌 예외의 `message` 는? 그 안에 원래 예외를 가리키는 것이 있나?

### 3. 감싼 오류의 사슬을 끝까지 따라가면 (예측) ★★★

```js
// js32b-32c-cause-chain.js
// Error 의 두 번째 인자 { cause } -- 무엇이 붙고, 사슬을 끝까지 따라가면 무엇이 보이나.
const name = (e) => (e instanceof Error ? e.constructor.name + " 「" + e.message + "」" : typeof e + " " + JSON.stringify(e));
const row = (label, v) => console.log("  " + label.padEnd(56) + v);

console.log("[1] three layers, each wrapping the one below");
function readConfig() { throw new SyntaxError("Unexpected token } in config.json"); }
function loadSettings() {
  try { return readConfig(); } catch (e) { throw new Error("settings could not be loaded", { cause: e }); }
}
function startApp() {
  try { return loadSettings(); } catch (e) { throw new TypeError("app failed to start", { cause: e }); }
}
let top;
try { startApp(); } catch (e) { top = e; }
let depth = 0;
for (let e = top; e !== undefined; e = e.cause) {
  console.log("  " + "  ".repeat(depth) + "depth " + depth + "  " + name(e));
  depth += 1;
  if (!(e instanceof Error)) break;
}

console.log("[2] what the option actually creates");
const d = (o, k) => JSON.stringify(Object.getOwnPropertyDescriptor(o, k));
row("new Error('m', { cause: 1 }) -> cause", d(new Error("m", { cause: 1 }), "cause"));
row("hasOwn(new Error('m'), 'cause')", Object.hasOwn(new Error("m"), "cause"));
row("hasOwn(new Error('m', {}), 'cause')", Object.hasOwn(new Error("m", {}), "cause"));
row("hasOwn(new Error('m', { cause: undefined }), 'cause')", Object.hasOwn(new Error("m", { cause: undefined }), "cause"));
row("new Error('m', 'text').cause", String(new Error("m", "text").cause));
row("JSON.stringify(new Error('m', { cause: 1 }))", JSON.stringify(new Error("m", { cause: 1 })));

console.log("[3] how the constructor reads the option (a Proxy logs every trap)");
const log = [];
const opts = new Proxy({ cause: "c" }, {
  has(t, k) { log.push("has " + String(k)); return Reflect.has(t, k); },
  get(t, k, r) { log.push("get " + String(k)); return Reflect.get(t, k, r); },
});
new RangeError("m", opts);
row("traps", log.join(" > "));

console.log("[4] a cause that is not an Error, and a cause chain that loops");
const s = new Error("outer", { cause: "just a string" });
row("typeof s.cause", typeof s.cause);
const a = new Error("a"), b = new Error("b", { cause: a });
a.cause = b;
const seen = new Set();
const walk = [];
for (let e = b; e instanceof Error; e = e.cause) {
  if (seen.has(e)) { walk.push("(seen before: " + e.message + ")"); break; }
  seen.add(e); walk.push(e.message);
}
row("walk with a seen-set", walk.join(" -> "));
```

- ★★★ `[1]` 몇 줄이 찍히고, 층마다 생성자 이름과 메시지는?
- ★★★ `[2]` `cause` 의 서술자 · `hasOwn` 세 줄 · 문자열 옵션 · `JSON.stringify` 결과는?
- ★★ `[3]` 트랩 로그는 몇 개이고 어떤 순서인가?
- ★★ `[4]` 두 줄은?

### 4. 언어가 스스로 던지는 오류와 그 가족 (예측) ★★

```js
// js32b-32d-hierarchy.js
// Error 계층 -- 언어가 스스로 던지는 종류는 무엇이고, 무엇이 이어져 있나.
const row = (label, v) => console.log("  " + label.padEnd(40) + v);
const tag = (v) => Object.prototype.toString.call(v);
const catchIt = (f) => { try { f(); return "(no throw)"; } catch (e) { return e; } };

console.log("[1] which constructor the language itself picks");
const cases = [
  ["null.x", () => null.x],
  ["new Array(-1)", () => new Array(-1)],
  ["JSON.parse('{')", () => JSON.parse("{")],
  ["notDeclaredAnywhere", () => notDeclaredAnywhere],
  ["decodeURIComponent('%')", () => decodeURIComponent("%")],
  ["(1).toFixed(101)", () => (1).toFixed(101)],
  ["Symbol() + ''", () => Symbol() + ""],
  ["new Function('return (')", () => new Function("return (")],
];
for (const [label, f] of cases) {
  const e = catchIt(f);
  row(label, e.constructor.name.padEnd(16) + "instanceof Error " + (e instanceof Error));
}

console.log("[2] the family tree");
const ctors = [TypeError, RangeError, SyntaxError, ReferenceError, EvalError, URIError, AggregateError];
for (const C of ctors) {
  row(C.name, "proto of ctor: " + Object.getPrototypeOf(C).name + "   name on prototype: " + Object.hasOwn(C.prototype, "name") + "   tag " + tag(new C(C === AggregateError ? [] : undefined)));
}

console.log("[3] message, name, and String(e)");
row("new Error().message", JSON.stringify(new Error().message));
row("hasOwn(new Error(), 'message')", Object.hasOwn(new Error(), "message"));
row("new Error(42).message", JSON.stringify(new Error(42).message));
row("String(new TypeError('bad'))", String(new TypeError("bad")));
row("String(new TypeError())", String(new TypeError()));
class NotFound extends Error {}
row("new NotFound('x').name", new NotFound("x").name);
class NotFound2 extends Error { constructor(m, o) { super(m, o); this.name = new.target.name; } }
row("new NotFound2('x').name", new NotFound2("x").name);
row("String(new NotFound2('x'))", String(new NotFound2("x")));
row("new NotFound2('x', { cause: 1 }).cause", new NotFound2("x", { cause: 1 }).cause);

console.log("[4] AggregateError -- one error holding several");
const ag = new AggregateError([new RangeError("r"), new TypeError("t", { cause: "deep" })], "two failed", { cause: "top" });
row("ag.message", ag.message);
row("ag.errors.length", ag.errors.length);
row("ag.errors kinds", ag.errors.map((e) => e.constructor.name).join(", "));
row("ag.errors[1].cause", ag.errors[1].cause);
row("ag.cause", ag.cause);
row("Array.isArray(ag.errors)", Array.isArray(ag.errors));
row("descriptor of errors", JSON.stringify(Object.getOwnPropertyDescriptor(ag, "errors"), (k, v) => (k === "value" ? "[...]" : v)));
const src = [1, 2];
const ag2 = new AggregateError(src);
src.push(3);
row("errors copied from the iterable?", ag2.errors.length + " (source now " + src.length + ")");
Promise.any([Promise.reject(new Error("a")), Promise.reject("b")]).catch((e) => {
  row("Promise.any rejects with", e.constructor.name + " 「" + e.message + "」");
  row("  its errors", JSON.stringify(e.errors.map((x) => (x instanceof Error ? "Error " + x.message : x))));
});
```

- ★★ `[1]` 여덟 식은 각각 어느 생성자의 오류를 던지나?
- ★★ `[2]` 일곱 줄의 세 칸은 서로 다른가?
- ★★★ `[3]` `new NotFound('x').name` 과 `new NotFound2('x').name` 은?
- ★★ `[4]` `errors` 의 길이 · 원본에 `push` 한 뒤 · `Promise.any` 가 거부한 값은?

### 5. `Error` 가 아닌 값을 던지면 (예측) ★★

```js
// js32b-32e-thrown-values.js
// throw 는 아무 값이나 던진다 -- catch 가 받는 것, 그리고 stack 이 있나(첫 줄만 찍는다 -- 나머지 줄에는 경로가 박힌다).
const row = (label, v) => console.log("  " + label.padEnd(34) + v);
const firstLine = (s) => (typeof s === "string" ? JSON.stringify(s.split("\n")[0]) : String(s));

console.log("[1] what catch receives");
const values = [
  ["throw 'disk full'", () => { throw "disk full"; }],
  ["throw 404", () => { throw 404; }],
  ["throw { code: 'E1' }", () => { throw { code: "E1" }; }],
  ["throw null", () => { throw null; }],
  ["throw undefined", () => { throw undefined; }],
  ["throw new Error('disk full')", () => { throw new Error("disk full"); }],
];
for (const [label, f] of values) {
  try { f(); } catch (e) {
    const kind = e === null ? "null" : typeof e;
    let st;
    try { st = firstLine(e.stack); } catch (x) { st = x.constructor.name + " 「" + x.message + "」"; }
    row(label, "typeof " + kind.padEnd(10) + "e.stack -> " + st);
  }
}

console.log("[2] where stack lives on a real Error (V8)");
const e = new Error("m");
const d = Object.getOwnPropertyDescriptor(e, "stack");
row("hasOwn(e, 'stack')", Object.hasOwn(e, "stack"));
row("descriptor kind", d ? ("value" in d ? "data" : "accessor") + ", enumerable " + d.enumerable : "(none)");
row("'stack' in Error.prototype", "stack" in Error.prototype);
row("typeof Error.captureStackTrace", typeof Error.captureStackTrace);
row("Error.stackTraceLimit", Error.stackTraceLimit);
const plain = { message: "not an error" };
Error.captureStackTrace(plain);
row("after captureStackTrace(plain)", firstLine(plain.stack));
```

```sh
# js32b-32i-uncaught.sh
#!/usr/bin/env bash
# 아무도 안 받은 throw -- node 가 표준 오류에 무엇을 적나. 문자열 · 평범한 객체 · Error 셋.
# (node -e 로 던지면 경로 대신 [eval] 이 찍힌다. 이 블록은 표준 오류만 받는다.)
set -u -o pipefail
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for src in 'throw "disk full"' 'throw { code: "E1" }' 'throw new Error("disk full")'; do
  echo "--- node20 -e '$src'"
  "$N20" -e "$src" 2>&1 >/dev/null
  echo "(exit $?)"
done
```

- ★★★ 첫 소스 `[1]` 여섯 줄 — `e.stack` 은 각각? 읽다가 던지는 줄이 있나?
- ★★ 첫 소스 `[2]` — `stack` 은 데이터인가 접근자인가? `Error.prototype` 에 있나?
- ★★★ 둘째 소스의 세 경우 — 표준 오류의 **던진 값 아래**는 서로 어떻게 다른가? 종료 코드는?

### 6. 다른 realm 에서 만든 오류 (예측) ★★★

```js
// js32b-32g-iserror-node.js
// Error.isError(ES2026) 가 이 node 판에 있나 -- 그리고 다른 realm 에서 만든 오류를 무엇으로 가리나.
const vm = require("node:vm");
const util = require("node:util");
const row = (label, v) => console.log("  " + label.padEnd(44) + v);

row("typeof Error.isError", typeof Error.isError);
try { Error.isError(new Error("x")); } catch (e) { row("Error.isError(new Error('x'))", e.constructor.name + " 「" + e.message + "」"); }

const other = vm.runInNewContext("new TypeError('from another realm')");
row("other instanceof Error", other instanceof Error);
row("other instanceof TypeError", other instanceof TypeError);
row("other.constructor === TypeError", other.constructor === TypeError);
row("Object.prototype.toString.call(other)", Object.prototype.toString.call(other));
row("util.types.isNativeError(other)  (host)", util.types.isNativeError(other));
row("other.name / other.message", other.name + " / " + other.message);
```

```js
// js32b-32h-iserror.web.js
// Error.isError(ES2026) -- 무엇을 오류로 보나. 다른 realm(iframe)에서 만든 오류 · 흉내 낸 객체 · Proxy · 호스트의 DOMException.
const row = (label, v) => console.log("  " + label.padEnd(50) + v);
const frame = document.createElement("iframe");
document.body.appendChild(frame);
const W = frame.contentWindow;

console.log("[1] one question, three ways to ask it");
const cands = [
  ["new Error('x')", new Error("x")],
  ["new (class E2 extends Error {})()", new (class E2 extends Error {})()],
  ["new AggregateError([])", new AggregateError([])],
  ["iframe: new W.TypeError('x')", new W.TypeError("x")],
  ["Object.create(Error.prototype)", Object.create(Error.prototype)],
  ["{ name: 'Error', message: 'x' }", { name: "Error", message: "x" }],
  ["{ [Symbol.toStringTag]: 'Error' }", { [Symbol.toStringTag]: "Error" }],
  ["new Proxy(new Error('x'), {})", new Proxy(new Error("x"), {})],
  ["new DOMException('x')  (host)", new DOMException("x")],
];
console.log("  " + "".padEnd(50) + "Error.isError  instanceof Error  toString");
for (const [label, v] of cands) {
  row(label, String(Error.isError(v)).padEnd(15) + String(v instanceof Error).padEnd(18) + Object.prototype.toString.call(v));
}

console.log("[2] non-objects");
row("Error.isError('Error: x') / (null) / ()", Error.isError("Error: x") + " / " + Error.isError(null) + " / " + Error.isError());

console.log("[3] where stack lives on a real Error (this V8)");
const e = new Error("m");
const d = Object.getOwnPropertyDescriptor(e, "stack");
row("hasOwn(e, 'stack')", Object.hasOwn(e, "stack"));
row("descriptor kind", d ? ("value" in d ? "data" : "accessor") + ", enumerable " + d.enumerable : "(none)");
row("'stack' in Error.prototype", "stack" in Error.prototype);
row("first line of e.stack", JSON.stringify(e.stack.split("\n")[0]));
```

- ★★★ 첫 소스를 node 20 에서 돌리면 여덟 줄은?
- ★★★ 둘째 소스 `[1]` 아홉 행 × 세 열 — `Error.isError` 와 `instanceof Error` 가 다른 답을 내는 행은?
- ★★ `Proxy` · `DOMException` · 브랜드를 위조한 객체 행은?
- ★ `[3]` Chrome 151 의 `stack` 은 데이터인가 접근자인가?

### 7. 1번 격자는 명세의 어느 한 문장에서 오나 (왜) ★★★

- ★★★ `TryStatement : try Block Finally` 의 평가에서 `B` 와 `F` 는 무엇이고, `F` 가 무엇일 때 `B` 가 나가나?
- ★★ 「예외를 삼킨다」는 따로 있는 규칙인가, 위 규칙의 뒷면인가?
- ★★ `catch` 가 있으면 `B` 자리에 무엇이 들어가나? 그래서 2번 `[3]` 셋째 줄은 왜 그렇게 되나?
- ★ `return n` 의 값이 `finally` 의 `n = 2` 를 못 보는 까닭은?

### 8. `cause` 와 `stack` 은 누가 정하나 (왜) ★★

- ★★★ `InstallErrorCause` 는 `options` 에 무엇을 먼저 묻고 무엇을 나중에 읽나? 그래서 `{ cause: undefined }` 는?
- ★★ `cause`·`message`·`errors` 가 비열거인 것은 로그에 어떤 결과를 내나?
- ★★★ `stack` 은 ECMA-262 에 있나? node 20 과 Chrome 151 의 모양은 같았나?

### 9. 파이썬과 자바에 같은 질문을 던지면 (연결) ★★

```sh
# js32b-32f-python-contrast.sh
#!/usr/bin/env bash
# 파이썬과 같은 질문 -- 이 머신의 파이썬 판들, 그리고 finally 의 return 에 경고가 나는가(-W error 로 경고를 예외로 올린다).
set -u -o pipefail
for p in python3.14 python3.13 python3.12 python3.11; do
  if command -v "$p" >/dev/null; then echo "$p: $("$p" --version)"; else echo "$p: not found"; fi
done
echo "--- python3.12 -W error - < js32b-32-h-pyerr.py"
python3.12 -W error - < js32b-32-h-pyerr.py 2>&1
echo "(exit $?)"
```

```python
# js32b-32-h-pyerr.py
# 같은 질문을 파이썬 3 에 -- raise ... from 의 사슬 · finally 가 예외를 바꿔치기할 때 남는 것 · finally 의 return.
def name(e):
    return type(e).__name__ + " 「" + str(e) + "」"

print("[1] raise ... from e -- walk __cause__ to the end")
def read_config():
    raise SyntaxError("Unexpected token } in config.json")
def load_settings():
    try:
        read_config()
    except SyntaxError as e:
        raise RuntimeError("settings could not be loaded") from e
def start_app():
    try:
        load_settings()
    except RuntimeError as e:
        raise TypeError("app failed to start") from e
try:
    start_app()
except TypeError as top:
    e, depth = top, 0
    while e is not None:
        print("  " + "  " * depth + "depth", depth, name(e))
        e, depth = e.__cause__, depth + 1

print("[2] finally raises while another exception is in flight")
try:
    try:
        raise ValueError("T")
    finally:
        raise KeyError("F")
except KeyError as caught:
    print("  caught        ", name(caught))
    print("  __cause__     ", caught.__cause__)
    print("  __context__   ", name(caught.__context__))

print("[3] return inside finally, with an exception in flight")
def swallow():
    try:
        raise ValueError("T")
    finally:
        return "F"
print("  swallow() ->", repr(swallow()))
```

- ★★★ 파이썬 `[2]` 의 `__context__` 는 무엇이고, JS 는 같은 자리에 무엇을 남겼나(2번 `[4]`)?
- ★★ `finally` 의 `return` 에 파이썬 3.12 는 경고를 냈나? 3.14 는 쟀나?
- ★★ 자바는 이 자리를 누가 알려 주나(Java 25 편)?
- ★ Go 의 `%w` 사슬을 걷는 창과 JS 의 `cause` 사슬을 걷는 루프는 어떻게 대응하나? 「사슬 안에 이것이 있나」를 묻는 표준 함수가 JS 에 있나?

### 10. 어디까지가 이 주제인가 — 판 경계와 이웃 (경계) ★★

- ★★★ `AggregateError` · `cause` · `Error.isError` 는 각각 몇 년 판인가? 이 머신의 세 엔진 중 어디에 있나?
- ★★ 프로미스 거부와 `await` 의 `try`/`catch` 는 목록의 몇 번 주제가 정본인가?
- ★★ realm·프로토타입 조작에서 어느 판정이 깨지나는 어느 편이 정본인가?
- ★ 정리 중 던진 예외를 원래 예외와 함께 담는 장치는 무엇이고, 어느 주제의 몫인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
