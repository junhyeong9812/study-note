# js/syntax/27 — `Object` 정적 메서드: 「복사·나열·묶기 — 결과가 같아 보여도 부르는 것이 다르다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(헤드리스) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다. ★ **6번(`Object.groupBy`·`Map.groupBy`)은 Chrome 에서만** 돌렸다 — 두 node 판에는 그 메서드가 없다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `Object.assign` 은 결과 객체만 보면 스프레드와 구별이 안 된다. **원본의 getter 와 대상의 setter 에 로그를 심어** 무엇이 몇 번, 어떤 순서로 불리는지를 찍는다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`assign` 은 원본과 대상에게 무엇을 부르나** — 그리고 도중에 실패하면 대상에 무엇이 남나
> ② **`keys`·`values`·`entries` 가 무엇을 세고 어떤 순서로 내나**
> ③ **`groupBy` 가 돌려주는 객체는 어떤 객체인가**(그리고 `Map.groupBy` 와 무엇이 다른가).
>
> ★★ **예외는 타입과 메시지로만 답한다.**
>
> **선행** — [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) ·
> [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) · [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md).
> ★★★ **11번의 `[4]` 블록을 먼저 떠올려라** — 대상에 setter 가 있을 때 스프레드는 몇 번, `Object.assign` 은 몇 번 불렀나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 2 · 3 · 4 · 5 · 6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 로그 배열을 한 칸씩 적어라** — 무엇이 먼저 불리나, `hidden` 의 getter 는 불리나.
- ★★★ **2번은 칸 하나하나에 y/n 을 적고, 마지막 줄의 수까지 세어 본다.**
- ★★ **3번·5번·6번은 「되는 것」과 「터지는 것」을 갈라서** 적어라. 터지면 종류와 문구까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.
- ★★★ **속도·메모리에 관한 답은 하나도 없다.** 「`assign` 이 스프레드보다 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `Object.assign` 이 원본과 대상에게 무엇을 부르나 (예측) ★★★ 이 주제의 축

```js
// js24b-27a-assign-log.js
// Object.assign(target, ...sources) -- which getters and setters run, and in what order?
const log = [];
const J = (x) => JSON.stringify(x);

const makeSource = (tag) => {
  const s = {};
  for (const k of ["p", "q"]) {
    Object.defineProperty(s, k, {
      get() { log.push("get " + tag + "." + k); return tag + k; },
      enumerable: true, configurable: true,
    });
  }
  Object.defineProperty(s, "hidden", {
    get() { log.push("get " + tag + ".hidden"); return 0; },
    enumerable: false,
  });
  s[Symbol("sym")] = tag + "sym";
  return s;
};
const makeTarget = () => {
  const t = {};
  let store = "initial";
  Object.defineProperty(t, "q", {
    get() { log.push("get target.q"); return store; },
    set(v) { log.push("set target.q <- " + v); store = v; },
    enumerable: true, configurable: true,
  });
  return t;
};

console.log("[1] one source, a target with a setter on q");
log.length = 0;
const t1 = makeTarget();
const r1 = Object.assign(t1, makeSource("A"));
console.log("  log                  " + J(log));
console.log("  returns the target?  " + (r1 === t1));
console.log("  own keys of target   " + J(Reflect.ownKeys(t1).map(String)));
console.log("  target.q descriptor  " + J(Object.keys(Object.getOwnPropertyDescriptor(t1, "q"))));
console.log("  target.p descriptor  " + J(Object.getOwnPropertyDescriptor(t1, "p")));

console.log("");
console.log("[2] two sources, left to right");
log.length = 0;
const t2 = makeTarget();
Object.assign(t2, makeSource("A"), makeSource("B"));
console.log("  log                  " + J(log));
log.length = 0;
console.log("  t2.p  t2.q           " + J([t2.p, t2.q]));

console.log("");
console.log("[3] the same source spread into an object literal (compare [1])");
log.length = 0;
const lit = { ...makeTarget(), ...makeSource("A") };
console.log("  log                  " + J(log));
console.log("  lit.q descriptor     " + J(Object.keys(Object.getOwnPropertyDescriptor(lit, "q"))));

console.log("");
console.log("[4] a source getter throws in the middle");
log.length = 0;
const t4 = {};
const bad = {
  get first() { log.push("get first"); return 1; },
  get second() { log.push("get second"); throw new Error("from getter"); },
  get third() { log.push("get third"); return 3; },
};
try { Object.assign(t4, bad); console.log("  no exception"); }
catch (e) { console.log("  " + e.constructor.name + " 「" + e.message + "」"); }
console.log("  log                  " + J(log));
console.log("  target afterwards    " + J(t4));

console.log("");
console.log("[5] sources that are not plain objects");
console.log("  null, undefined      " + J(Object.assign({}, null, undefined)));
console.log("  'ab'                 " + J(Object.assign({}, "ab")));
console.log("  5, true              " + J(Object.assign({}, 5, true)));
console.log("  [7, 8]               " + J(Object.assign({}, [7, 8])));
try { Object.assign(null, { a: 1 }); console.log("  target null: no exception"); }
catch (e) { console.log("  target null          " + e.constructor.name + " 「" + e.message + "」"); }
```

- ★★★ `[1]` 의 `log` 배열을 순서대로 적어라. `hidden` 의 getter 는 그 안에 있나?
- ★★ `[1]` 에서 `target.q` 의 디스크립터 키 넷은 무엇인가 — 대입 뒤에도 접근자인가?
- ★★★ `[2]` 두 원본일 때 `log` 와 `t2.p`·`t2.q` 는?
- ★★★ `[3]` 스프레드의 `log` 에 `set target.q` 가 있나? 첫 항목은 무엇인가?
- ★★ `[4]` 예외 한 줄과 `target afterwards` 는?
- ★ `[5]` 다섯 줄.

### 2. 복사 도구 넷을 같은 원본에 들이대면 (예측) ★★★

```js
// js24b-27b-copy-grid.js
// Four ways to copy an object -- what does each one keep? The script counts the cells.
const J = (x) => JSON.stringify(x);
const yn = (b) => (b ? "y" : "n");

class Point { constructor() { this.x = 1; } }
const make = () => {
  let reads = 0;
  const src = new Point();
  src.inner = { deep: 1 };
  Object.defineProperty(src, "counter", { get() { reads += 1; return reads; }, enumerable: true });
  Object.defineProperty(src, "hidden", { value: "h", enumerable: false });
  src[Symbol("tag")] = "s";
  return { src, reads: () => reads };
};

const tools = [
  ["Object.assign({}, src)", "assign", (s) => Object.assign({}, s)],
  ["{ ...src }", "spread", (s) => ({ ...s })],
  ["fromEntries(entries(src))", "entries", (s) => Object.fromEntries(Object.entries(s))],
  ["structuredClone(src)", "clone", (s) => structuredClone(s)],
];
const questions = [
  ["inner is the same object", (c, s) => c.inner === s.inner],
  ["counter is still a getter", (c) => typeof Object.getOwnPropertyDescriptor(c, "counter")?.get === "function"],
  ["symbol key copied", (c) => Object.getOwnPropertySymbols(c).length === 1],
  ["non-enumerable key copied", (c) => Object.hasOwn(c, "hidden")],
  ["prototype is Point.prototype", (c) => Object.getPrototypeOf(c) === Point.prototype],
  ["copy !== src", (c, s) => c !== s],
];

console.log("[1] grid -- y/n per cell");
console.log(("  " + "".padEnd(30) + tools.map(([, c]) => c.padEnd(8)).join(" ")).trimEnd());
const table = questions.map(([q, test]) => tools.map(([, , f]) => {
  const { src } = make();
  return test(f(src), src);
}));
questions.forEach(([q], i) => console.log(("  " + q.padEnd(30) + table[i].map((b) => yn(b).padEnd(8)).join(" ")).trimEnd()));

console.log("");
console.log("[2] how many times was the getter read during the copy?");
for (const [n, , f] of tools) {
  const { src, reads } = make();
  f(src);
  console.log("  " + n.padEnd(30) + reads());
}

console.log("");
console.log("[3] writing through the copy");
const { src } = make();
const shallow = Object.assign({}, src);
shallow.inner.deep = 99;
shallow.x = 2;
console.log("  src.inner.deep  " + src.inner.deep);
console.log("  src.x           " + src.x);

let differ = 0, total = 0;
for (const row of table) for (let j = 1; j < row.length; j++) { total += 1; if (row[j] !== row[0]) differ += 1; }
console.log("");
console.log("cells whose answer differs from the Object.assign column: " + differ + " / " + total);
```

- ★★★ `[1]` 여섯 행 × 네 열의 y/n 을 전부 적어라. 특히 **첫 행과 셋째 행**.
- ★★ `[2]` getter 는 도구마다 몇 번 읽혔나?
- ★★ `[3]` 두 줄 — 복사본을 고쳤을 때 원본의 어느 쪽이 바뀌나?
- ★ 마지막 줄 「N / M」의 N 과 M 은?

### 3. 쓰기를 거부하는 대상에 `Object.assign` 을 하면 (예측) ★★★

```js
// js24b-27c-readonly-target.js
// Object.assign into a target that refuses some writes -- in sloppy and in strict code.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { f(); console.log("  " + label.padEnd(42) + "no exception"); }
  catch (e) { console.log("  " + label.padEnd(42) + e.constructor.name + " 「" + e.message + "」"); }
};

function sloppyAssign(t, s) { return Object.assign(t, s); }
function sloppyWrite(t) { t.a = 2; }
function strictAssign(t, s) { "use strict"; return Object.assign(t, s); }
function strictWrite(t) { "use strict"; t.a = 2; }

console.log("[1] a frozen target");
show("sloppy   Object.assign(frozen, { a: 2 })", () => sloppyAssign(Object.freeze({ a: 1 }), { a: 2 }));
show("sloppy   frozen.a = 2", () => sloppyWrite(Object.freeze({ a: 1 })));
show("strict   Object.assign(frozen, { a: 2 })", () => strictAssign(Object.freeze({ a: 1 }), { a: 2 }));
show("strict   frozen.a = 2", () => strictWrite(Object.freeze({ a: 1 })));

console.log("");
console.log("[2] the target has one read-only key, b -- the source writes a, b, c");
const t = {};
Object.defineProperty(t, "b", { value: "old", writable: false, enumerable: true });
show("Object.assign(t, { a: 1, b: 2, c: 3 })", () => strictAssign(t, { a: 1, b: 2, c: 3 }));
console.log("  t afterwards                              " + J(t));

console.log("");
console.log("[3] a frozen source, an ordinary target");
const fs = Object.freeze({ a: 1, inner: { deep: 1 } });
const copy = Object.assign({}, fs);
copy.a = 2;
copy.inner.deep = 2;
console.log("  copy is frozen?     " + Object.isFrozen(copy));
console.log("  fs.a  fs.inner.deep " + J([fs.a, fs.inner.deep]));
```

- ★★★ `[1]` 네 줄 — 비엄격 함수와 엄격 함수에서 각각 던지나? 던지면 문구까지.
- ★★★ `[2]` 예외 뒤 `t afterwards` 에는 무엇이 들어 있나? `c` 는?
- ★★ `[3]` 복사본은 얼어 있나? `fs.inner.deep` 은?

### 4. `keys`·`values`·`entries` 가 내는 순서와 묻는 것 (예측) ★★★

```js
// js24b-27d-keys-values-entries.js
// Object.keys / values / entries -- order, what they ask the object, and what a getter can change mid-way.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(30) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(30) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] order -- keys inserted as b, 2, a, 1, Symbol");
const o = {};
o.b = "B"; o[2] = "two"; o.a = "A"; o[1] = "one"; o[Symbol("s")] = "S";
show("Object.keys", () => Object.keys(o));
show("Object.values", () => Object.values(o));
show("Object.entries", () => Object.entries(o));
show("Reflect.ownKeys", () => Reflect.ownKeys(o).map(String));

console.log("");
console.log("[2] what each one asks a Proxy (two keys, one of them non-enumerable)");
const target = {};
Object.defineProperty(target, "x", { value: 1, enumerable: true, configurable: true });
Object.defineProperty(target, "y", { value: 2, enumerable: false, configurable: true });
const log = [];
const traced = new Proxy(target, {
  ownKeys(t) { log.push("ownKeys"); return Reflect.ownKeys(t); },
  getOwnPropertyDescriptor(t, k) { log.push("gopd " + String(k)); return Reflect.getOwnPropertyDescriptor(t, k); },
  get(t, k, r) { log.push("get " + String(k)); return Reflect.get(t, k, r); },
});
for (const [n, f] of [["keys", Object.keys], ["values", Object.values], ["entries", Object.entries]]) {
  log.length = 0;
  f(traced);
  console.log("  " + n.padEnd(10) + J(log));
}

console.log("");
console.log("[3] a getter that deletes a later key and adds a new one");
const m = {
  get first() { delete this.second; this.added = "new"; return "F"; },
  second: "S",
  third: "T",
};
show("Object.entries(m)", () => Object.entries(m));
show("Object.keys(m) afterwards", () => Object.keys(m));

console.log("");
console.log("[4] non-objects");
show("Object.keys('ab')", () => Object.keys("ab"));
show("Object.entries(5)", () => Object.entries(5));
show("Object.values([7, , 9])", () => Object.values([7, , 9]));
show("Object.keys(null)", () => Object.keys(null));
```

- ★★★ `[1]` 네 줄의 순서. 심볼은 어느 줄에 나오나?
- ★★★ `[2]` 세 줄의 트랩 로그 — `keys` 는 `get` 을 부르나? 비열거 `y` 의 값은 읽히나?
- ★★ `[3]` getter 가 도중에 `second` 를 지우고 `added` 를 넣으면 `entries` 결과에 무엇이 남나?
- ★ `[4]` 네 줄.

### 5. `Object.fromEntries` 가 받는 것과 `Map` 왕복 (예측) ★★

```js
// js24b-27e-fromentries.js
// Object.fromEntries -- what it accepts, what the keys become, and a round trip through a Map.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(40) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(40) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] inputs");
show("fromEntries([['a', 1], ['b', 2]])", () => Object.fromEntries([["a", 1], ["b", 2]]));
show("fromEntries(new Map([['a', 1]]))", () => Object.fromEntries(new Map([["a", 1]])));
show("fromEntries([['k', 1], ['k', 2]])", () => Object.fromEntries([["k", 1], ["k", 2]]));
show("fromEntries([['a']])  keys, String(a)", () => { const r = Object.fromEntries([["a"]]); return [Object.keys(r), String(r.a)]; });
show("fromEntries(['ab'])", () => Object.fromEntries(["ab"]));
show("fromEntries([1])", () => Object.fromEntries([1]));
show("fromEntries({ a: 1 })", () => Object.fromEntries({ a: 1 }));

console.log("");
console.log("[2] Map -> object -> Map");
const key = { id: 1 };
const map = new Map([[1, "number one"], ["1", "string one"], [key, "object"], [true, "bool"]]);
const obj = Object.fromEntries(map);
console.log("  map.size                  " + map.size);
console.log("  Object.keys(obj)          " + J(Object.keys(obj)));
console.log("  obj['1']                  " + J(obj["1"]));
const back = new Map(Object.entries(obj));
console.log("  back.size                 " + back.size);
console.log("  back.get(1)               " + String(back.get(1)));
console.log("  back.get('1')             " + String(back.get("1")));
console.log("  back.get(key)             " + String(back.get(key)));

console.log("");
console.log("[3] object -> entries -> transform -> object");
const prices = { apple: 3, pear: 5 };
const doubled = Object.fromEntries(Object.entries(prices).map(([k, v]) => [k, v * 2]));
console.log("  doubled                   " + J(doubled));

console.log("");
console.log("[4] the key \"__proto__\" -- fromEntries and assign side by side");
const pair = JSON.parse('{"__proto__": {"marker": true}}');
console.log("  own keys of the JSON source       " + J(Object.keys(pair)));
const viaEntries = Object.fromEntries([["__proto__", { marker: true }]]);
const viaAssign = Object.assign({}, pair);
for (const [n, r] of [["fromEntries", viaEntries], ["Object.assign", viaAssign]]) {
  console.log("  " + n.padEnd(14) + "own keys " + J(Object.keys(r)).padEnd(15) +
    "marker " + String(r.marker).padEnd(10) + "prototype changed " + (Object.getPrototypeOf(r) !== Object.prototype));
}
```

- ★★ `[1]` 일곱 줄 — 통과하나, 터지나? 터지면 문구까지.
- ★★★ `[2]` `Object.keys(obj)` 와 `back.size`, 그리고 `back.get(1)` 은?
- ★★★ `[4]` 두 행 — `"__proto__"` 가 자기 키가 되나, 프로토타입이 바뀌나?

### 6. `Object.groupBy` 가 돌려주는 객체와 `Map.groupBy` (예측) ★★★

```js
// js24b-27f-groupby.web.js
// Object.groupBy and Map.groupBy -- what comes back, and what the callback sees.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(42) + f()); }
  catch (e) { console.log("  " + label.padEnd(42) + e.constructor.name + " 「" + e.message + "」"); }
};
const items = [
  { name: "a", kind: "fruit", n: 3 },
  { name: "b", kind: "herb", n: 10 },
  { name: "c", kind: "fruit", n: 2 },
];

console.log("[1] Object.groupBy -- the returned object");
const g = Object.groupBy(items, (it) => it.kind);
show("JSON.stringify", () => J(g));
show("Object.getPrototypeOf(g) === null", () => Object.getPrototypeOf(g) === null);
show("'toString' in g", () => "toString" in g);
show("g.toString()", () => g.toString());
show("String(g)", () => String(g));
show("`${g}`", () => `${g}`);
show("Object.prototype.toString.call(g)", () => Object.prototype.toString.call(g));
show("g.fruit[0] === items[0]", () => g.fruit[0] === items[0]);
show("Array.isArray(g.fruit)", () => Array.isArray(g.fruit));
show("g.vegetable", () => String(g.vegetable));

console.log("");
console.log("[2] the callback -- arguments and call count");
const calls = [];
Object.groupBy(["x", "y", "z"], (v, i, ...rest) => { calls.push([v, i, rest.length]); return "k"; });
show("calls", () => J(calls));

console.log("");
console.log("[3] the keys -- returned values of different types");
const byType = Object.groupBy([1, 2, 3, 4], (n) => [n % 2, "odd", { id: 1 }, true][n - 1]);
show("Object.keys", () => J(Object.keys(byType)));
const numeric = Object.groupBy(["p", "q", "r"], (v) => ({ p: "z", q: "10", r: "2" })[v]);
show("keys for 'z', '10', '2' (in that order)", () => J(Object.keys(numeric)));

console.log("");
console.log("[4] Map.groupBy on the same kind of input");
const k1 = { id: 1 };
const k2 = { id: 1 };
const mg = Map.groupBy([1, 2, 3, 4, 5], (n) => [k1, k2, k1, -0, 0][n - 1]);
show("mg instanceof Map", () => mg instanceof Map);
show("mg.size", () => mg.size);
show("mg.get(k1)", () => J(mg.get(k1)));
show("mg.get(k2)", () => J(mg.get(k2)));
show("mg.get({ id: 1 })", () => String(mg.get({ id: 1 })));
show("mg.get(0)", () => J(mg.get(0)));
show("Object.is(zero key, -0)", () => Object.is([...mg.keys()][2], -0));

console.log("");
console.log("[5] inputs that are not arrays");
show("Object.groupBy(new Set([1, 2, 3]))", () => J(Object.groupBy(new Set([1, 2, 3]), (n) => (n > 1 ? "big" : "small"))));
show("Object.groupBy('aba')", () => J(Object.groupBy("aba", (ch) => ch)));
show("Object.groupBy({ length: 2 })", () => J(Object.groupBy({ length: 2, 0: "a", 1: "b" }, (v) => v)));
show("typeof [].groupBy", () => typeof [].groupBy);

console.log("");
console.log("[6] group keys named like Object.prototype members -- a hand-written version into {} and groupBy");
const words = ["toString", "__proto__", "plain"];
const byHand = (list) => {
  const acc = {};
  for (const w of list) (acc[w] ??= []).push(w);
  return acc;
};
for (const w of words) {
  show("by hand into {}   key " + J(w), () => J(Object.keys(byHand([w]))));
  show("Object.groupBy    key " + J(w), () => J(Object.keys(Object.groupBy([w], (x) => x))));
}
```

- ★★★ `[1]` 열 줄. 특히 `g.toString()` · `String(g)` · `Object.prototype.toString.call(g)` 세 줄.
- ★★ `[2]` 콜백이 받는 인자는 몇 개이고, 몇 번 불리나?
- ★★★ `[3]` 둘째 줄의 키 순서는 **넣은 순서**인가?
- ★★★ `[4]` `mg.size` · `mg.get(k2)` · `mg.get({ id: 1 })` · 마지막 줄.
- ★ `[5]` 넷째 줄은?
- ★★★ `[6]` 여섯 줄 — 손으로 짠 쪽과 `groupBy` 는 어느 키에서 갈리나? 갈리면 문구까지.

### 7. `Object.assign` 의 대입 한 번은 명세에서 무엇인가 (왜) ★★★

- ★★★ 명세 `Object.assign` 은 키마다 어떤 추상 연산을 **어떤 인자로** 부르나?
- ★★ 그 인자는 **호출한 코드가 엄격 모드인가**와 어떤 관계인가? `t.a = 2` 는 같은 연산을 어떤 인자로 부르나?
- ★ 명세 알고리즘에 **되돌리는 단계**가 있나? 3번의 `[2]` 와 맞춰 보라.

### 8. 11번의 setter 한 줄과 이 문서 1번의 로그는 어떻게 이어지나 (연결) ★★★

- ★★★ 11번 `[4]` 에서 setter 호출이 스프레드 **몇 회**, `Object.assign` **몇 회**였나?
- ★★ 이 문서 1번의 `[3]` 로그 첫 항목 `get target.q` 는 **누가** 부른 것인가?
- ★ 대상 객체에 setter 가 없으면 둘의 결과가 갈리는 자리가 남나?

### 9. `Object.groupBy` 의 결과 객체는 명세에서 어떻게 만들어지나 — 그리고 왜 (왜) ★★

- ★★ 명세는 결과 객체를 **어느 연산으로** 만드나? note 는 그 결과를 무엇이라 적나?
- ★★★ 묶음 키가 `"toString"`·`"__proto__"` 라면, 결과가 보통 객체(`{}`)였을 때 무엇이 꼬이나? 6번의 `[6]` 과 맞춰 보라.
- ★ 6번 `[1]` 의 줄 가운데 15번의 `Object.create(null)` 블록과 **같은 문구**가 나온 줄은?

### 10. 파이썬 `dict` 병합과 JS `Object.assign` — 자리와 값은 어디서 오나 (연결) ★★

- ★★★ 파이썬 갈래 12번의 `b | a` 에서 `y` 는 몇 번째 자리에 무슨 값이었나? JS `Object.assign({}, b, a)` 는?
- ★★ 정수처럼 생긴 키가 섞이면 **어느 언어만** 순서를 바꾸나?
- ★ 파이썬 `a | [...]` 는 `TypeError` 였다. JS `Object.assign({}, [7, 8])` 은?

### 11. 깊은 복사 · 동결은 어디까지가 이 주제인가 (경계) ★★

- ★★ 2번 격자에서 `structuredClone` 열이 `assign` 열과 **다른 행**은 무엇이고, 그래도 잃는 것은 무엇인가?
- ★★ `Object.freeze` 한 원본을 `assign` 으로 복사하면 **얼음이 따라오나**? 14번의 「동결은 얕다」와 어떻게 이어지나?
- ★ 깊은 복사 수단 비교는 목록의 몇 번 주제가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
