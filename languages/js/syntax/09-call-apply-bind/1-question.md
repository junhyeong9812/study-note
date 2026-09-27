# js/syntax/09 — `call`·`apply`·`bind`: 「`this` 와 인자를 손으로 건넨다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ③ 브랜드 태그다.** 세 메서드가 `this` 자리에 무엇을 넣었는지는
> **값으로는 안 갈리고 `Object.prototype.toString.call` 로만 갈린다.**
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **셋이 `this` 를 정하는 규칙이 같은가** ② ★★★ **`bind` 가 만든 함수는 어떤 물건인가** ③ **`apply` 가 안 받는 것을 어떻게 알리나**.
> ★★★ **[07번](../07-this-binding-four-rules/2-summary.md)이 「어느 규칙이 이기나」까지였다면 여기는 그 명시적 바인딩의 API 세부다.**
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★★★ **인자 개수의 경계는 자릿수로만 답한다** — 정확한 수는 흔들린다.
> ★ **4번은 실무 문항이다.** 「고쳤다」로 끝내지 말고 **그 대가**까지 적어야 답이다.
>
> **선행** — [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 네 문항(1\~4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「값으로는 왜 안 갈리나」까지 적어야** 답이다.
- ★★★ **2번은 「되돌릴 수 있나」를 다섯 경로로 각각** 답해야 한다.
- ★★ **3번은 「터지는 것과 조용한 것」을 갈라야** 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 값을 셋으로 건네면 (예측) ★★★ 이 주제의 축

```js
// js08b-09a-three-methods.js
// call.apply.bind -- 셋이 this 를 어떻게 정하나. 답은 브랜드 태그로만 갈린다.
function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}
function looseWho() { return tag(this); }
function strictWho() { "use strict"; return tag(this); }

const THIS_VALUES = [
  ["object", { mark: "given" }],
  ["number 7", 7],
  ["string s", "s"],
  ["boolean true", true],
  ["null", null],
  ["undefined", undefined],
  ["array", []],
  ["function", function named() {}],
];

console.log("[1] same this value through call / apply / bind -- sloppy callee");
console.log("  " + "this given".padEnd(16) + "call".padEnd(28) + "apply".padEnd(28) + "bind()()");
for (const [label, v] of THIS_VALUES) {
  console.log("  " + label.padEnd(16) +
              looseWho.call(v).padEnd(28) +
              looseWho.apply(v).padEnd(28) +
              looseWho.bind(v)());
}

console.log("");
console.log("[2] the same grid with a strict callee -- how many cells change");
let differ = 0;
console.log("  " + "this given".padEnd(16) + "call".padEnd(28) + "apply".padEnd(28) + "bind()()");
for (const [label, v] of THIS_VALUES) {
  const a = strictWho.call(v), b = strictWho.apply(v), c = strictWho.bind(v)();
  if (a !== looseWho.call(v)) differ += 1;
  if (b !== looseWho.apply(v)) differ += 1;
  if (c !== looseWho.bind(v)()) differ += 1;
  console.log("  " + label.padEnd(16) + a.padEnd(28) + b.padEnd(28) + c);
}
console.log("  " + "settings-dependent cells".padEnd(30) + differ + " of " + (THIS_VALUES.length * 3));

console.log("");
console.log("[3] how the arguments are handed over");
function args3(a, b, c) { return "a=" + String(a) + " b=" + String(b) + " c=" + String(c) + " n=" + arguments.length; }
const SHAPES = [
  ["call(t, 1, 2, 3)", () => args3.call(null, 1, 2, 3)],
  ["apply(t, [1, 2, 3])", () => args3.apply(null, [1, 2, 3])],
  ["apply(t, undefined)", () => args3.apply(null, undefined)],
  ["apply(t, null)", () => args3.apply(null, null)],
  ["apply(t, [])", () => args3.apply(null, [])],
  ["apply(t, arguments-like)", () => args3.apply(null, { 0: 1, 1: 2, length: 2 })],
  ["apply(t, { length: 3 })", () => args3.apply(null, { length: 3 })],
  ["apply(t, 'abc')", () => args3.apply(null, "abc")],
  ["apply(t, new Set([1, 2]))", () => args3.apply(null, new Set([1, 2]))],
  ["apply(t, 7)", () => args3.apply(null, 7)],
  ["apply(t, true)", () => args3.apply(null, true)],
  ["call(t) with no args", () => args3.call(null)],
  ["Reflect.apply(f, t, [1, 2])", () => Reflect.apply(args3, null, [1, 2])],
  ["Reflect.apply(f, t, 'ab')", () => Reflect.apply(args3, null, "ab")],
  ["f(...[1, 2, 3]) spread", () => args3(...[1, 2, 3])],
];
for (const [label, run] of SHAPES) {
  try { console.log("  " + label.padEnd(30) + run()); }
  catch (e) { console.log("  " + label.padEnd(30) + e.constructor.name + ": " + e.message); }
}
```

- 세 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 **`call`·`apply`·`bind()()` 세 열이 다른 줄은 몇 개**인가?
- ★★★ `[1]` 과 `[2]` 를 견주면 **설정에 달린 칸은 몇 개**인가? 어느 행들인가?
- ★★★ `this` 로 `7` 을 줬을 때 비엄격의 답을 **`String(this)` 로 찍었다면 무엇이 나왔겠는가**? 왜 브랜드 태그로 찍는가?
- ★★ `[3]` 의 열다섯 모양 중 **터지는 것은 몇 개**인가? 무엇이 공통인가?
- ★★★ `apply(t, new Set([1, 2]))` 는 왜 **에러도 안 나고 인자도 안 들어가는가**?
- ★ `apply(t, { length: 3 })` 은 무엇을 넘기는가?

### 2. `bind` 가 만든 함수는 무엇인가 (예측) ★★★

```js
// js08b-09b-bind.js
// bind 가 만든 함수는 무엇인가 -- 원본이 아니라 한 겹 덧씌운 새 함수다.
function show(label, run) {
  try { console.log("  " + label.padEnd(40) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(40) + " -> " + e.constructor.name + ": " + e.message); }
}
function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}

function orig(a, b, c) { return tag(this) + " args=" + [a, b, c].map(String).join(","); }
const A = { mark: "A" }, B = { mark: "B" };
const bound1 = orig.bind(A, 1);

console.log("[1] the bound function is a different object");
show("bound1 === orig", () => bound1 === orig);
show("orig.name", () => JSON.stringify(orig.name));
show("bound1.name", () => JSON.stringify(bound1.name));
show("orig.length", () => orig.length);
show("bound1.length", () => bound1.length);
show("orig has prototype?", () => Object.prototype.hasOwnProperty.call(orig, "prototype"));
show("bound1 has prototype?", () => Object.prototype.hasOwnProperty.call(bound1, "prototype"));
show("proto of bound1 is orig?", () => Object.getPrototypeOf(bound1) === orig);
show("proto of bound1 is Function.prototype?", () => Object.getPrototypeOf(bound1) === Function.prototype);
show("bound1 own keys", () => JSON.stringify(Object.getOwnPropertyNames(bound1)));
show("String(bound1)", () => String(bound1));

console.log("");
console.log("[2] you cannot rebind it -- the first bind wins");
show("bound1(2, 3)", () => bound1(2, 3));
show("bound1.call(B, 2, 3)", () => bound1.call(B, 2, 3));
show("bound1.apply(B, [2, 3])", () => bound1.apply(B, [2, 3]));
show("bound1.bind(B)(2, 3)", () => bound1.bind(B)(2, 3));
show("bound1.bind(B, 9)(3)", () => bound1.bind(B, 9)(3));
show("({ mark: 'host', m: bound1 }).m(2, 3)", () => ({ mark: "host", m: bound1 }).m(2, 3));
show("Reflect.apply(bound1, B, [2, 3])", () => Reflect.apply(bound1, B, [2, 3]));

console.log("");
console.log("[3] new beats bind -- but the bound arguments stay");
function Ctor(a, b) { this.got = [a, b]; this.mark = "ctor"; }
Ctor.prototype.kind = "Ctor.prototype";
const BoundCtor = Ctor.bind({ mark: "ignored" }, 1);
const made = new BoundCtor(2);
show("new BoundCtor(2).got", () => JSON.stringify(made.got));
show("made instanceof Ctor", () => made instanceof Ctor);
show("made instanceof BoundCtor", () => made instanceof BoundCtor);
show("made.kind (from prototype chain)", () => made.kind);
show("proto of made is Ctor.prototype?", () => Object.getPrototypeOf(made) === Ctor.prototype);
show("BoundCtor.prototype", () => String(BoundCtor.prototype));
show("new (bound arrow)", () => { const ba = ((x) => x).bind(null, 1); return new ba(); });

console.log("");
console.log("[4] bind on an arrow changes nothing about this -- but still fixes arguments");
const outerThis = { mark: "outer" };
const arrowFn = function () { return (a, b) => tag(this) + " args=" + [a, b].map(String).join(","); }.call(outerThis);
show("arrowFn(1, 2)", () => arrowFn(1, 2));
show("arrowFn.call(B, 1, 2)", () => arrowFn.call(B, 1, 2));
show("arrowFn.bind(B)(1, 2)", () => arrowFn.bind(B)(1, 2));
show("arrowFn.bind(B, 9)(2)", () => arrowFn.bind(B, 9)(2));
show("arrowFn.bind(B).length", () => arrowFn.bind(B).length);
show("arrowFn.bind(B, 9).length", () => arrowFn.bind(B, 9).length);

console.log("");
console.log("[5] borrowing a method -- the classic uses");
const arrayLike = { 0: "a", 1: "b", length: 2 };
show("slice.call(arrayLike)", () => JSON.stringify(Array.prototype.slice.call(arrayLike)));
show("join.call(arrayLike, '-')", () => Array.prototype.join.call(arrayLike, "-"));
const hasOwn = Function.prototype.call.bind(Object.prototype.hasOwnProperty);
show("uncurried hasOwn({ x: 1 }, 'x')", () => hasOwn({ x: 1 }, "x"));
show("uncurried hasOwn({ x: 1 }, 'y')", () => hasOwn({ x: 1 }, "y"));
const toStr = Function.prototype.call.bind(Object.prototype.toString);
show("uncurried toString([])", () => toStr([]));
show("Math.max.apply(null, [3, 1, 2])", () => Math.max.apply(null, [3, 1, 2]));
show("Math.max(...[3, 1, 2])", () => Math.max(...[3, 1, 2]));

console.log("");
console.log("[6] how many wrappers does bind add");
let f = orig;
const depths = [];
for (let i = 0; i < 4; i += 1) {
  depths.push("depth " + i + " name=" + JSON.stringify(f.name) + " length=" + f.length);
  f = f.bind(A);
}
for (const d of depths) console.log("  " + d);
show("4-deep bound call", () => f());
```

- 여섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 `bound1` 의 **이름·`length`·`prototype`·프로토타입**을 각각 적으면? 왜 그 값인가?
- ★★★ `[2]` 의 다섯 경로 중 **`this` 를 되돌린 것은 몇 개**인가? **인자는 어떻게 되는가**?
- ★★★ `[3]` 에서 `BoundCtor.prototype` 은 `undefined` 인데 `made instanceof BoundCtor` 는 무엇인가? 왜인가?
- ★★ `[4]` 에서 화살표에 `bind` 를 걸면 **무엇이 바뀌고 무엇이 안 바뀌는가**?
- ★ `[6]` 에서 네 겹으로 감싼 함수의 이름과 `length` 는 각각 어떻게 되는가?

### 3. 인자 개수의 한계와 `thisArg` (예측) ★★

```js
// js08b-09c-limits.js
// 명세가 보장하는 것과 엔진이 정하는 것 -- 인자 개수의 한계는 어느 쪽인가.
function count() { return arguments.length; }

function firstFailure(call) {
  // 2의 거듭제곱으로 올려 처음 터지는 구간을 잡고, 그 구간을 이분해 경계를 찾는다.
  let lo = 1, hi = 1;
  for (;;) {
    try { call(hi); lo = hi; hi *= 2; if (hi > (1 << 30)) return ["no fail", lo, ""]; }
    catch (e) { break; }
  }
  let err = "";
  while (lo + 1 < hi) {
    const mid = Math.floor((lo + hi) / 2);
    try { call(mid); lo = mid; }
    catch (e) { hi = mid; err = e.constructor.name + ": " + e.message; }
  }
  return ["last ok", lo, err];
}

const CASES = [
  ["f.apply(null, arr)", (n) => count.apply(null, new Array(n))],
  ["Reflect.apply(f, null, arr)", (n) => Reflect.apply(count, null, new Array(n))],
  ["f(...arr)  spread", (n) => count(...new Array(n))],
  ["f.bind(null, ...arr)()", (n) => count.bind(null, ...new Array(n))()],
  ["new Array(n) itself", (n) => new Array(n)],
];
console.log("[1] where does each call form stop accepting arguments");
for (const [label, call] of CASES) {
  const [kind, at, err] = firstFailure(call);
  // 경계의 정확한 수는 그 순간 스택이 얼마나 차 있는지에 달려 흔들린다.
  // 흔들리지 않는 것은 자릿수와 예외의 종류다 -- 그 둘만 찍는다.
  console.log(("  " + label.padEnd(30) + kind.padEnd(10) +
              (at > 0 ? String(at).length + "-digit" : "n/a").padEnd(10) + err).replace(/ +$/, ""));
}

console.log("");
console.log("[2] what the spec fixes -- these are not engine numbers");
const rows = [
  ["Function.prototype.call.length", Function.prototype.call.length],
  ["Function.prototype.apply.length", Function.prototype.apply.length],
  ["Function.prototype.bind.length", Function.prototype.bind.length],
  ["Reflect.apply.length", Reflect.apply.length],
  ["call is a function?", typeof Function.prototype.call],
  ["Math.max.length", Math.max.length],
  ["Math.max() with no args", Math.max()],
  ["[].reduce.length", Array.prototype.reduce.length],
];
for (const [k, v] of rows) console.log("  " + k.padEnd(34) + String(v));

console.log("");
console.log("[3] thisArg on built-ins -- which ones take one");
const takesThisArg = [
  ["map", (o) => [1].map(function () { return this.mark; }, o)],
  ["filter", (o) => [1].filter(function () { return this.mark; }, o).length],
  ["forEach", (o) => { let r; [1].forEach(function () { r = this.mark; }, o); return r; }],
  ["some", (o) => [1].some(function () { return this.mark; }, o)],
  ["every", (o) => [1].every(function () { return this.mark; }, o)],
  ["find", (o) => [1].find(function () { return this.mark; }, o)],
  ["flatMap", (o) => [1].flatMap(function () { return this.mark; }, o)],
  ["reduce", (o) => [1, 2].reduce(function () { return this.mark; }, 0, o)],
  ["sort", (o) => [2, 1].sort(function () { return this.mark ? -1 : 1; }, o)],
  ["Array.from", (o) => Array.from([1], function () { return this.mark; }, o)],
];
const host = { mark: "HOST" };
for (const [label, run] of takesThisArg) {
  try { console.log("  " + label.padEnd(14) + JSON.stringify(run(host))); }
  catch (e) { console.log("  " + label.padEnd(14) + e.constructor.name + ": " + e.message); }
}
```

- 세 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 네 호출 형태는 **어디서 멈추는가**? 그 수는 **명세인가 엔진인가**?
- ★★★ `new Array(n)` 자체는 왜 안 터지는가? **무엇이 막는 것인가**?
- ★★ `[2]` 의 `length` 값들은 왜 `[1]` 의 수치와 성격이 다른가?
- ★★★ `[3]` 의 열 줄 중 **`thisArg` 를 안 받는 것은 몇 개**인가? **그때 무슨 일이 일어나는가**?

### 4. 떼어 낸 메서드를 고치는 네 가지 (예측) ★★

```js
// js08b-09d-fixes.js
// 떼어 낸 메서드를 고치는 네 가지 -- 무엇이 this 를 지키고 무엇이 「같은 함수」인가.
// 07번이 「왜 깨지나」였다면 여기는 「무엇으로 고치고 그 대가가 무엇인가」다.
function show(label, run) {
  try { console.log("  " + label.padEnd(34) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(34) + " -> " + e.constructor.name + ": " + e.message); }
}

const counter = {
  mark: "counter",
  n: 0,
  inc() { this.n += 1; return this.mark + " n=" + this.n; },
};

console.log("[1] four ways to hand the method to someone else");
const detached = counter.inc;
const bound = counter.inc.bind(counter);
const wrapped = () => counter.inc();
const viaCall = function () { return counter.inc.call(counter); };
show("detached()", () => detached());
show("bound()", () => bound());
show("wrapped()", () => wrapped());
show("viaCall()", () => viaCall());
show("counter.n after those calls", () => counter.n);

console.log("");
console.log("[2] are two fixes the same function object");
const rows = [
  ["counter.inc === counter.inc", counter.inc === counter.inc],
  ["bind twice gives the same fn?", counter.inc.bind(counter) === counter.inc.bind(counter)],
  ["arrow twice gives the same fn?", (() => counter.inc()) === (() => counter.inc())],
  ["a saved bound fn === itself", (() => { const b = counter.inc.bind(counter); return b === b; })()],
];
for (const [k, v] of rows) console.log("  " + k.padEnd(38) + String(v));
console.log("  " + "why it matters".padEnd(38) + "removeEventListener needs the same object");

console.log("");
console.log("[3] a fake listener registry shows what that costs");
const registry = new Set();
function on(fn) { registry.add(fn); return registry.size; }
function off(fn) { const had = registry.delete(fn); return "deleted=" + had + " left=" + registry.size; }
show("on(counter.inc.bind(counter))", () => on(counter.inc.bind(counter)));
show("off(counter.inc.bind(counter))", () => off(counter.inc.bind(counter)));
const saved = counter.inc.bind(counter);
show("on(saved)", () => on(saved));
show("off(saved)", () => off(saved));

console.log("");
console.log("[4] what each fix keeps and drops");
const probes = [
  ["original", counter.inc],
  ["bound", counter.inc.bind(counter)],
  ["arrow wrapper", () => counter.inc()],
  ["bound with an arg", counter.inc.bind(counter, 1)],
];
console.log("  " + "fix".padEnd(18) + "name".padEnd(16) + "length".padEnd(8) + "proto?".padEnd(8) + "new?");
for (const [label, f] of probes) {
  let canNew;
  try { Reflect.construct(f, []); canNew = "yes"; }
  catch (e) { canNew = "no:" + e.constructor.name; }
  console.log("  " + label.padEnd(18) +
              JSON.stringify(f.name).padEnd(16) +
              String(f.length).padEnd(8) +
              String(Object.prototype.hasOwnProperty.call(f, "prototype")).padEnd(8) +
              canNew);
}
function takesTwo(a, b) { return "got " + String(a) + "," + String(b); }
const holder = { mark: "holder", takesTwo };
show("bound forwards later args", () => takesTwo.bind(holder)(1, 2));
show("arrow wrapper with no params", () => ((...args) => takesTwo.apply(holder, args))(1, 2));
show("arrow wrapper that drops args", () => (() => takesTwo.call(holder))(1, 2));
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 `detached()` 는 왜 **예외를 안 내고** 이상한 값을 돌려주는가?
- ★★★ `[2]` 에서 `bind` 를 두 번 하면 같은 함수인가? **그것이 무엇을 못 하게 만드는가**?
- ★★ `[3]` 의 `deleted=false` 는 무엇을 뜻하는가? 고치는 법은?
- ★★★ `[4]` 의 마지막 세 줄에서 **인자를 잃는 고침은 어느 것**인가?

### 5. `call` 과 `apply` 중 무엇을 고르나 (경계) ★★

- 인자가 **배열**에 있을 때 오늘날의 정답은 무엇인가? 왜 `apply` 가 아닌가?
- ★★★ **스프레드로 대신할 수 없는 자리**가 하나 있다. 무엇인가?
- ★★ `apply` 의 둘째 인자로 `null` 을 주면? `7` 을 주면? 두 답이 왜 다른가?
- ★ `Reflect.apply` 는 `apply` 와 무엇이 같고 무엇이 다른가?

### 6. `bind` 를 두 번 걸면 (왜) ★★

- 왜 안쪽이 이기는가? **한 문장**으로.
- ★★ 두 번째 `bind` 가 **완전히 무의미한 것은 아니다.** 무엇은 되는가?
- ★ `length` 는 두 번째 `bind` 에서 어떻게 되는가?

### 7. `new` 와 `bind` 가 만나면 (왜) ★★★

- `new (f.bind(A, 1))(2)` 에서 `this` 와 인자는 각각 무엇이 되는가?
- ★★★ `instanceof` 가 **두 함수 모두에 `true`** 인 이유는?
- ★★ 화살표를 `bind` 한 뒤 `new` 하면 무엇이 나는가? **08번 격자의 어느 칸**과 이어지는가?

### 8. 화살표에 세 메서드를 쓰면 (연결) ★★

- `this` 는 바뀌는가? **무엇은 바뀌는가**?
- ★★ 그래서 이 조합이 **위험한 이유**는 무엇인가?
- ★ 어느 주제가 이 사실의 정본인가?

### 9. 설정에 달린 칸이 몇 개인가 (경계) ★★★ 이 갈래의 축

- 1번 격자에서 **엄격·비엄격이 갈린 칸의 개수**를 대면?
- ★★★ 갈린 칸들의 **공통점**은 무엇인가? 객체를 줬을 때는 왜 안 갈리는가?
- ★★ 모듈(ESM)에서 이 격자를 돌리면 어느 쪽 답이 나오는가?

### 10. 보장인가 호스트인가 엔진 사정인가 (연결) ★★★

- 이 주제에서 **두 판이 갈린 자리는 몇 개**였는가? 08번과 견주면?
- ★★★ 브라우저에 같은 줄을 던졌을 때 **호스트가 정하는 칸은 몇 개**였고 무엇인가?
- ★★★ **인자 개수의 상한**은 세 층(명세·엔진·이 판) 중 어디에 속하는가? 어떻게 아는가?
- ★ 이 주제에서 **부적용인 창**은 무엇인가? 성능은 왜 여기 없는가?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **`this` 네 규칙** · **스프레드 문법** · **`Reflect` 전체** · **`Object.prototype.toString` 을 타입 검사로 쓰기** 는 각각 어느 주제가 정본인가?
- ★★★ 07번에서 **무엇을 이어받는가**? 한 문장으로.
- ★★ 08번 격자의 어느 행이 이 주제 전체로 펼쳐진 것인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
