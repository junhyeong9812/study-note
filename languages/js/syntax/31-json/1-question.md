# js/syntax/31 — `JSON`: 「같은 값을 어디에 놓느냐가 무엇을 바꾸나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(헤드리스) · python3 3.12.3 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다. ★ **6번의 둘째 소스(`.web.js`)는 Chrome 에서만** 돌렸다 — 첫째 소스가 두 node 판에 그 기능이 있는지를 묻는다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 값 하나를 **객체의 속성 · 배열의 원소 · 최상위** 세 자리에 놓고 `JSON.stringify` 한 결과를 칸마다 찍는다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`JSON.stringify` 는 값을 무엇으로 바꾸나** — 그리고 자리가 그 답에 끼어드나
> ② **`toJSON`·`replacer`·`reviver` 는 어떤 순서로, 누구를 `this` 로 불리나**
> ③ **JSON 왕복을 깊은 복사로 쓰면 무엇이 남나.**
>
> ★★ **예외는 타입과 메시지로만 답한다.** 여러 줄 메시지는 탐침이 줄마다 `| ` 를 붙여 찍는다.
>
> **선행** — [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md) · [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) ·
> [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) · [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md).
> ★★★ **27번 2번의 복사 격자를 먼저 떠올려라** — 복사 도구 넷은 어느 행에서 갈렸나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 2 · 3 · 4 · 5 · 6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸 하나하나를 적고, 마지막 줄의 수까지 세어 본다.** 「(key gone)」·「(undefined)」·예외 이름 가운데 무엇이 들어가나.
- ★★★ **3번과 4번은 로그를 한 줄씩 순서대로** 적어라 — 누가 먼저, 어느 키부터.
- ★★ **2번·4번·6번은 「되는 것」과 「터지는 것」을 갈라서** 적어라. 터지면 종류와 문구까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 호스트의 것인가, 이 판의 관찰인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「JSON 왕복이 더 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 값을 여러 자리에 놓으면 (예측) ★★★ 이 주제의 축

```js
// js28b-31a-type-grid.js
// JSON.stringify -- the same value in three places: as an object property, as an array element, at the top level.
// Each cell prints what that value became. The script counts the rows at the end.
const cell = (f) => {
  try {
    const r = f();
    return r === undefined ? "(undefined)" : r;
  } catch (e) { return e.constructor.name; }
};
const asProp = (v) => cell(() => {
  const s = JSON.stringify({ k: v });
  return s === "{}" ? "(key gone)" : s.slice(5, -1);
});
const asElem = (v) => cell(() => JSON.stringify([v]).slice(1, -1));
const asTop = (v) => cell(() => JSON.stringify(v));

const bare = Object.create(null); bare.a = 1;
const values = [
  ["null", null],
  ["'s'", "s"],
  ["undefined", undefined],
  ["() => 1", () => 1],
  ["Symbol('s')", Symbol("s")],
  ["NaN", NaN],
  ["Infinity", Infinity],
  ["-0", -0],
  ["1n", 1n],
  ["new Date(0)", new Date(0)],
  ["new Map([[1, 2]])", new Map([[1, 2]])],
  ["new Set([1])", new Set([1])],
  ["Object.create(null) + a:1", bare],
  ["new Boolean(false)", new Boolean(false)],
];

console.log("[1] value" + " ".repeat(22) + "as property".padEnd(28) + "as array element".padEnd(28) + "top level");
let differ = 0;
for (const [label, v] of values) {
  const row = [asProp(v), asElem(v), asTop(v)];
  if (new Set(row).size > 1) differ += 1;
  console.log(("  " + label.padEnd(28) + row.map((c) => c.padEnd(28)).join("")).trimEnd());
}

console.log("");
console.log("[2] a hole in a sparse array, next to an explicit undefined");
console.log("  JSON.stringify([1, , 3])          " + JSON.stringify([1, , 3]));
console.log("  JSON.stringify([1, undefined, 3]) " + JSON.stringify([1, undefined, 3]));
console.log("  JSON.stringify(new Array(2))      " + JSON.stringify(new Array(2)));

console.log("");
console.log("[3] keys that are not plain strings");
const sym = Symbol("key");
console.log("  { [sym]: 1, a: 2 }        " + JSON.stringify({ [sym]: 1, a: 2 }));
console.log("  { 2: 'x', 1: 'y', b: 0 }  " + JSON.stringify({ 2: "x", 1: "y", b: 0 }));
const hidden = Object.defineProperty({ a: 1 }, "h", { value: 2, enumerable: false });
console.log("  non-enumerable h          " + JSON.stringify(hidden));
class P { constructor() { this.own = 1; } }
P.prototype.inherited = 2;
console.log("  class instance            " + JSON.stringify(new P()));

console.log("");
console.log("rows whose three positions do not all agree: " + differ + " / " + values.length);
```

- ★★★ `[1]` 열네 행 × 세 열을 전부 적어라. 특히 **`undefined` · `() => 1` · `Symbol('s')`** 의 세 칸.
- ★★★ 최상위 칸에 `(undefined)` 가 나오는 행이 있다면, 그것은 `"undefined"` 라는 글자인가?
- ★★ `NaN`·`Infinity`·`-0` 은 각각 무엇이 되나? 속성 자리에서 키는 남나?
- ★★ `new Date(0)` · `Map` · `Set` · `Object.create(null)` · `new Boolean(false)` 은?
- ★★★ `[2]` 세 줄 — 구멍과 `undefined` 를 결과 글자로 가를 수 있나?
- ★★ `[3]` 네 줄 — 심볼 키 · 정수 키 · 비열거 키 · 상속된 키는 각각?
- ★ 마지막 줄 「N / M」의 N 과 M 은?

### 2. 고리가 있는 객체와 `BigInt` 를 넣으면 (예측) ★★★

```js
// js28b-31b-throws.js
// What JSON.stringify refuses -- the exception type and the whole message.
// A message can span several lines; each line is printed with a "| " prefix so nothing is trimmed.
const show = (label, f) => {
  try { console.log("  " + label.padEnd(32) + "returned " + f()); }
  catch (e) {
    console.log("  " + label.padEnd(32) + e.constructor.name);
    for (const line of e.message.split("\n")) console.log("    | " + line);
  }
};

console.log("[1] cycles");
const self = {}; self.me = self;
show("self.me = self", () => JSON.stringify(self));
const a = { name: "a", b: { c: {} } }; a.b.c.back = a;
show("a.b.c.back = a", () => JSON.stringify(a));
const arr = [1, [2]]; arr[1].push(arr);
show("arr[1][1] = arr", () => JSON.stringify(arr));
class Node2 { constructor() { this.next = null; } }
const n1 = new Node2(); const n2 = new Node2(); n1.next = n2; n2.next = n1;
show("class instances, n1 <-> n2", () => JSON.stringify(n1));

console.log("");
console.log("[2] one object reached through two keys");
const shared = { v: 1 };
show("{ x: shared, y: shared }", () => JSON.stringify({ x: shared, y: shared }));

console.log("");
console.log("[3] BigInt");
show("1n", () => JSON.stringify(1n));
show("{ id: 10n }", () => JSON.stringify({ id: 10n }));
show("replacer: bigint -> toString()", () => JSON.stringify({ id: 10n }, (k, v) => (typeof v === "bigint" ? v.toString() : v)));
BigInt.prototype.toJSON = function () { return this.toString() + "n"; };
show("BigInt.prototype.toJSON set", () => JSON.stringify({ id: 10n }));
delete BigInt.prototype.toJSON;

console.log("");
console.log("[4] a.b.c.back = a again, with a WeakSet replacer");
const seen = new WeakSet();
show("WeakSet replacer", () => JSON.stringify(a, (k, v) => {
  if (typeof v === "object" && v !== null) { if (seen.has(v)) return "[seen]"; seen.add(v); }
  return v;
}));
```

- ★★★ `[1]` 네 경우에 각각 무엇이 나오나? 예외면 **메시지를 줄 단위로** 적어라 — 메시지가 몇 줄이고, 어느 키 이름이 나오나?
- ★★ `arr[1][1] = arr` 과 클래스 인스턴스 쪽은 메시지의 **어느 낱말**이 객체 쪽과 다른가?
- ★★★ `[2]` 한 객체를 두 키가 가리키면 무엇이 나오나?
- ★★★ `[3]` 네 줄 — `BigInt` 가 속성 안에 있으면 어떻게 되나? `BigInt.prototype.toJSON` 을 달면?
- ★★ `[4]` `back` 자리에는 무엇이 들어가나?

### 3. `toJSON` 과 `replacer` 의 호출 로그 (예측) ★★★

```js
// js28b-31c-tojson-replacer.js
// JSON.stringify(value, replacer) -- who is called first for each key, toJSON or the replacer?
// And what does the replacer see: the key, the value, and `this`.
const log = [];
const J = JSON.stringify;
const t = (v) => (v === null ? "null" : Array.isArray(v) ? "array" : typeof v);

const inner = {
  x: 1,
  toJSON(key) { log.push("toJSON(key=" + J(key) + ")"); return { swapped: true }; },
};
const root = { a: inner, b: [10, new Date(0)] };

function replacer(key, value) {
  const holder = this === root ? "root" : this === inner ? "inner" : Array.isArray(this) ? "array" :
    J(Object.keys(this)) === '[""]' ? '{"": root}' : "{" + Object.keys(this).join(",") + "}";
  log.push("replacer(key=" + J(key) + ", value:" + t(value) + ", this=" + holder + ")");
  return value;
}

console.log("[1] call log");
const out = J(root, replacer);
for (const line of log) console.log("  " + line);
console.log("  result " + out);

console.log("");
console.log("[2] toJSON on the root object itself");
log.length = 0;
const r2 = J({ toJSON(k) { log.push("root toJSON(key=" + J(k) + ")"); return 42; } }, (k, v) => { log.push("replacer(key=" + J(k) + ", value " + J(v) + ")"); return v; });
for (const line of log) console.log("  " + line);
console.log("  result " + r2);

console.log("");
console.log("[3] what the replacer returns");
console.log("  undefined for key b        " + J({ a: 1, b: 2 }, (k, v) => (k === "b" ? undefined : v)));
console.log("  undefined for key \"\"       " + J({ a: 1 }, (k, v) => (k === "" ? undefined : v)));
console.log("  undefined for index 1      " + J([1, 2, 3], (k, v) => (k === "1" ? undefined : v)));
console.log("  typeof key for an index    " + (() => { let seen; J([7], function (k, v) { if (k !== "") seen = typeof k; return v; }); return seen; })());

console.log("");
console.log("[4] replacer as an array -- an allow-list of keys");
const deep = { id: 1, name: "n", meta: { id: 2, secret: "s", name: "m" }, list: [{ id: 3, x: 0 }] };
console.log("  ['id', 'meta']             " + J(deep, ["id", "meta"]));
console.log("  ['id', 'meta', 'list']     " + J(deep, ["id", "meta", "list"]));
console.log("  [1, 'id', 'id']            " + J({ 1: "one", id: 1 }, [1, "id", "id"]));
console.log("  ['0'] on an array          " + J(["a", "b"], ["0"]));

console.log("");
console.log("[5] the space argument");
const sp = (s) => J(J({ a: [1] }, null, s));
console.log("  2          " + sp(2));
console.log("  10         " + sp(10));
console.log("  20         " + sp(20));
console.log("  -1         " + sp(-1));
console.log("  '--'       " + sp("--"));
console.log("  'abcdefghijklmnop'  " + sp("abcdefghijklmnop"));
console.log("  length of the indent for 20         " + J({ a: 1 }, null, 20).split("\n")[1].indexOf('"'));
```

- ★★★ `[1]` 로그 일곱 줄을 순서대로 적어라. `toJSON` 은 몇 번째 줄인가? 넷째 줄의 `key` 는?
- ★★★ `[1]` 마지막 줄에서 `replacer` 가 받은 `value` 의 타입은 무엇인가?
- ★★ `[1]` 첫 줄의 `this` 는 무엇인가?
- ★★ `[2]` 세 줄.
- ★★★ `[3]` 넷째 줄까지 — `replacer` 가 `undefined` 를 돌려주면 자리마다 어떻게 되나?
- ★★★ `[4]` 네 줄 — 허용 목록은 `meta` 안의 키에도 적용되나? 배열의 인덱스에는?
- ★★ `[5]` `10` 과 `20` 의 줄은 같은가? 마지막 줄의 수는?

### 4. `JSON.parse` 에 `reviver` 를 주면 — 그리고 문법의 가장자리 (예측) ★★★

```js
// js28b-31d-parse-reviver.js
// JSON.parse(text, reviver) -- in which order is the reviver called, and what can it change?
const J = JSON.stringify;
const text = '{"a":{"b":1,"c":[2,3]},"d":4}';

console.log("[1] call order");
const log = [];
JSON.parse(text, function (key, value) {
  log.push(J(key) + (typeof value === "object" && value !== null ? " (object)" : " = " + J(value)));
  return value;
});
log.forEach((l, i) => console.log("  " + String(i + 1).padStart(2) + ". " + l));

console.log("");
console.log("[2] returning undefined, and returning something else");
console.log("  drop key b       " + J(JSON.parse(text, (k, v) => (k === "b" ? undefined : v))));
console.log("  drop index 0     " + J(JSON.parse(text, (k, v) => (k === "0" ? undefined : v))));
console.log("  double numbers   " + J(JSON.parse(text, (k, v) => (typeof v === "number" ? v * 2 : v))));
console.log("  drop key \"\"      " + String(JSON.parse(text, (k, v) => (k === "" ? undefined : v))));
const iso = '{"when":"1970-01-01T00:00:00.000Z"}';
const plain = JSON.parse(iso);
const revived = JSON.parse(iso, (k, v) => (k === "when" ? new Date(v) : v));
console.log("  without reviver  typeof when = " + typeof plain.when);
console.log("  with reviver     when instanceof Date = " + (revived.when instanceof Date));

console.log("");
console.log("[3] the key \"__proto__\" in JSON text, next to the same key in an object literal");
const fromText = JSON.parse('{"__proto__": {"marker": 1}}');
const fromLiteral = { "__proto__": { marker: 1 } };
for (const [n, o] of [["JSON.parse", fromText], ["object literal", fromLiteral]]) {
  console.log("  " + n.padEnd(16) + "own keys " + J(Object.keys(o)).padEnd(16) +
    "o.marker " + String(o.marker).padEnd(11) + "prototype is Object.prototype " + (Object.getPrototypeOf(o) === Object.prototype));
}

console.log("");
console.log("[4] texts at the edge of the grammar");
const bad = ["{'a': 1}", '{"a": 1,}', "[1, 2,]", "{a: 1}", "NaN", "undefined", "01", ""];
for (const s of bad) {
  try { console.log("  " + J(s).padEnd(18) + "-> " + J(JSON.parse(s))); }
  catch (e) { console.log("  " + J(s).padEnd(18) + "-> " + e.constructor.name + " 「" + e.message + "」"); }
}
console.log("  " + J(' [1] ').padEnd(18) + "-> " + J(JSON.parse(" [1] ")));
console.log("  " + J('{"a":1,"a":2}').padEnd(18) + "-> " + J(JSON.parse('{"a":1,"a":2}')));
```

- ★★★ `[1]` 일곱 줄의 순서를 적어라. 첫 줄과 마지막 줄의 키는?
- ★★★ `[2]` 여섯 줄 — `drop index 0` 의 배열은 몇 칸인가?
- ★★★ `[3]` 두 행 — `own keys` · `o.marker` · 프로토타입이 각각 무엇인가?
- ★★ `[4]` 앞의 여덟 줄은 각각 값인가 예외인가? 마지막 두 줄은?
- ★ `[4]` 의 문구는 두 node 판에서 같을까?

### 5. JSON 왕복과 `structuredClone` 을 같은 값에 (예측) ★★★

```js
// js28b-31e-deep-copy.js
// JSON.parse(JSON.stringify(x)) as a deep copy, next to structuredClone(x) -- what comes back for each kind of value?
// structuredClone is a host API (HTML), not ECMA-262. The script counts the rows at the end.
const J = JSON.stringify;
const viaJSON = (x) => JSON.parse(JSON.stringify(x));
const viaClone = (x) => structuredClone(x);
const run = (copy, make, test) => {
  try { return test(copy(make())); } catch (e) { return e.constructor.name; }
};

class Point { constructor() { this.x = 1; } }
const rows = [
  ["Date", () => ({ v: new Date(0) }), (c) => (c.v instanceof Date ? "Date" : typeof c.v)],
  ["Map", () => ({ v: new Map([["k", 1]]) }), (c) => (c.v instanceof Map ? "Map size " + c.v.size : J(c.v))],
  ["Set", () => ({ v: new Set([1]) }), (c) => (c.v instanceof Set ? "Set size " + c.v.size : J(c.v))],
  ["undefined property", () => ({ v: undefined }), (c) => ("v" in c ? "key kept" : "key gone")],
  ["NaN", () => ({ v: NaN }), (c) => String(c.v)],
  ["-0", () => ({ v: -0 }), (c) => (Object.is(c.v, -0) ? "-0" : String(c.v))],
  ["BigInt", () => ({ v: 1n }), (c) => typeof c.v],
  ["RegExp", () => ({ v: /a/g }), (c) => (c.v instanceof RegExp ? "RegExp " + c.v : J(c.v))],
  ["class instance", () => new Point(), (c) => (c instanceof Point ? "Point" : "plain " + J(c))],
  ["function property", () => ({ v: () => 1 }), (c) => typeof c.v],
  ["same object twice", () => { const s = {}; return { a: s, b: s }; }, (c) => (c.a === c.b ? "still one object" : "two objects")],
  ["cycle", () => { const o = {}; o.me = o; return o; }, (c) => (c.me === c ? "cycle kept" : "?")],
  ["getter", () => ({ get v() { return 1; } }), (c) => (typeof Object.getOwnPropertyDescriptor(c, "v").get === "function" ? "getter" : "data " + c.v)],
];

console.log("[1] kind of value            " + "JSON round trip".padEnd(24) + "structuredClone");
let differ = 0;
for (const [label, make, test] of rows) {
  const a = run(viaJSON, make, test);
  const b = run(viaClone, make, test);
  if (a !== b) differ += 1;
  console.log("  " + label.padEnd(26) + a.padEnd(24) + b);
}

console.log("");
console.log("[2] the two exceptions -- constructor, name, and the first line of the message");
for (const [n, f] of [["JSON round trip   cycle", () => viaJSON((() => { const o = {}; o.me = o; return o; })())],
                      ["structuredClone   function", () => viaClone({ v: () => 1 })]]) {
  try { f(); console.log("  " + n + "   no exception"); }
  catch (e) { console.log("  " + n.padEnd(28) + e.constructor.name + " (name " + e.name + ") 「" + e.message.split("\n")[0] + "」"); }
}

console.log("");
console.log("rows where the two columns differ: " + differ + " / " + rows.length);
```

- ★★★ `[1]` 열세 행 × 두 열을 적어라. 특히 `Date` · `Map` · `same object twice` · `cycle` 행.
- ★★ `class instance` 와 `getter` 행은 두 열이 같은가?
- ★★ `function property` 행의 두 칸은?
- ★★ `[2]` 두 줄 — 생성자 이름과 `name` 은 같은가?
- ★ 마지막 줄 「N / M」의 N 과 M 은?

### 6. 20자리 숫자를 읽고 쓰기 — 원문 접근 (예측) ★★

```js
// js28b-31x-node-rawjson.js
// The same two features asked of node -- do they exist on this build?
const J = JSON.stringify;
console.log("typeof JSON.rawJSON      " + typeof JSON.rawJSON);
console.log("typeof JSON.isRawJSON    " + typeof JSON.isRawJSON);
let args;
JSON.parse("12345678901234567890", function (k, v, ctx) { args = arguments.length; return v; });
console.log("reviver arguments.length " + args);
try { J({ id: JSON.rawJSON("1") }); console.log("JSON.rawJSON('1')        no exception"); }
catch (e) { console.log("JSON.rawJSON('1')        " + e.constructor.name + " 「" + e.message + "」"); }
```
```js
// js28b-31f-rawjson.web.js
// JSON.rawJSON and the reviver's third argument (source text access) -- Chrome only; node probe is js28b-31x-node-rawjson.js.
const J = JSON.stringify;
const show = (label, f) => {
  try { console.log("  " + label.padEnd(46) + f()); }
  catch (e) { console.log("  " + label.padEnd(46) + e.constructor.name + " 「" + e.message + "」"); }
};
const big = "12345678901234567890";

console.log("[1] a number with more digits than a double holds");
show("JSON.parse(big)", () => String(JSON.parse(big)));
show("reviver: value, context.source", () => {
  let seen;
  JSON.parse(big, (k, v, ctx) => { seen = [String(v), J(ctx)]; return v; });
  return seen.join("   ");
});
show("reviver returns BigInt(context.source)", () => String(JSON.parse(big, (k, v, ctx) => BigInt(ctx.source))) + "n");

console.log("");
console.log("[2] which keys get a source");
JSON.parse('{"n": 1.50, "s": "x", "o": {"t": true}, "a": [null]}', (k, v, ctx) => {
  console.log("  key " + J(k).padEnd(6) + "context " + J(ctx));
  return v;
});

console.log("");
console.log("[3] JSON.rawJSON");
show("JSON.stringify({ id: JSON.rawJSON(big) })", () => J({ id: JSON.rawJSON(big) }));
show("JSON.stringify({ id: 12345678901234567890 })", () => J({ id: 12345678901234567890 }));
show("JSON.stringify({ n: JSON.rawJSON('1.50') })", () => J({ n: JSON.rawJSON("1.50") }));
show("JSON.isRawJSON(JSON.rawJSON('1'))", () => JSON.isRawJSON(JSON.rawJSON("1")));
show("Object.isFrozen(JSON.rawJSON('1'))", () => Object.isFrozen(JSON.rawJSON("1")));
show("Object.getPrototypeOf(JSON.rawJSON('1'))", () => String(Object.getPrototypeOf(JSON.rawJSON("1"))));
show("JSON.rawJSON('{}')", () => J(JSON.rawJSON("{}")));
show("JSON.rawJSON(' 1')", () => J(JSON.rawJSON(" 1")));
show("JSON.rawJSON('abc')", () => J(JSON.rawJSON("abc")));
show("replacer returns rawJSON for a BigInt", () => J({ id: 10n ** 20n }, (k, v) => (typeof v === "bigint" ? JSON.rawJSON(v.toString()) : v)));
```

- ★★★ 첫 소스를 node 20 에서 돌리면 네 줄은?
- ★★★ 둘째 소스 `[1]` 세 줄 — 그냥 파싱한 값과 `context.source` 는 같은 글자인가?
- ★★ `[2]` 일곱 줄 — `context` 에 `source` 가 있는 키는 어느 것인가? `"1.50"` 은 어떻게 나오나?
- ★★ `[3]` 열 줄 — `JSON.rawJSON` 이 받지 않는 입력은?

### 7. 1번 격자의 행들을 명세 연산으로 읽으면 (왜) ★★★

- ★★★ `SerializeJSONProperty` 가 `undefined` 를 돌려주는 값은 무엇인가?
- ★★★ 그 `undefined` 를 `SerializeJSONObject` 와 `SerializeJSONArray` 는 각각 어떻게 처리하나?
- ★★ 최상위는 어느 쪽 처리도 안 받는다 — 그 이유는 감싸개 `{"": v}` 와 어떻게 이어지나?
- ★ `NaN` 이 `undefined` 와 다른 갈래로 가는 까닭은?

### 8. 3번과 4번의 순서는 명세의 어떤 모양에서 오나 (왜) ★★★

- ★★★ `SerializeJSONProperty` 안에서 `toJSON` 과 `replacer` 는 몇 번째 단계인가?
- ★★★ `InternalizeJSONProperty` 는 자식과 자기 이름 중 무엇을 먼저 처리하나?
- ★★ 그래서 `reviver` 가 부모 객체를 받는 순간, 그 안의 자식은 어떤 상태인가?
- ★ 순환 참조를 알아내는 명세의 장치는 무엇이고, 2번 `[2]` 가 그 장치에 안 걸리는 이유는?

### 9. 파이썬 `json` 에 같은 질문을 던지면 (연결) ★★

```sh
# js28b-31g-python-contrast.sh
#!/usr/bin/env bash
# 파이썬 json 에 같은 질문을 던진다 -- 소스는 js28b-31-h-pyjson.py 에 있다.
set -u -o pipefail
python3 js28b-31-h-pyjson.py
```
```python
# js28b-31-h-pyjson.py
# Python json.dumps / json.loads asked the same questions as the JS probes -- exceptions print as name 「message」.
import json, math

def show(label, f):
    try:
        print("  " + label.ljust(44) + repr(f()))
    except Exception as e:
        print("  " + label.ljust(44) + type(e).__name__ + " 「" + str(e) + "」")

print("[1] the values of the JS grid, and dict keys")
show("json.dumps(float('nan'))", lambda: json.dumps(float("nan")))
show("json.dumps(math.inf)", lambda: json.dumps(math.inf))
show("json.dumps(nan, allow_nan=False)", lambda: json.dumps(float("nan"), allow_nan=False))
show("json.dumps(None)", lambda: json.dumps(None))
show("json.dumps({'k': None})", lambda: json.dumps({"k": None}))
show("json.dumps(-0.0)", lambda: json.dumps(-0.0))
show("json.dumps({1: 'a', 2: 'b'})", lambda: json.dumps({1: "a", 2: "b"}))
show("json.dumps({1: 'a', '1': 'b'})", lambda: json.dumps({1: "a", "1": "b"}))
show("json.dumps({(1, 2): 'a'})", lambda: json.dumps({(1, 2): "a"}))
show("json.dumps({1, 2})", lambda: json.dumps({1, 2}))
show("json.dumps(10 ** 20)", lambda: json.dumps(10 ** 20))
show("json.dumps(lambda: 1)", lambda: json.dumps(lambda: 1))

print()
print("[2] cycle")
d = {}
d["me"] = d
show("d['me'] = d", lambda: json.dumps(d))

print()
print("[3] default= -- when is it called?")
calls = []
def default(o):
    calls.append(type(o).__name__)
    return sorted(o) if isinstance(o, set) else str(o)
show("dumps({'s': {2, 1}, 'n': 1}, default=...)", lambda: json.dumps({"s": {2, 1}, "n": 1}, default=default))
print("  default called for                          " + repr(calls))

print()
print("[4] loads")
show("json.loads('NaN')", lambda: json.loads("NaN"))
show("json.loads('12345678901234567890')", lambda: json.loads("12345678901234567890"))
show("json.loads('{\"a\":1,\"a\":2}')", lambda: json.loads('{"a":1,"a":2}'))
show("json.loads('[1,]')", lambda: json.loads("[1,]"))
```

- ★★★ `NaN` · 집합 · 함수 · 순환에서 파이썬과 JS 는 각각 무엇을 하나?
- ★★ `default=` 는 몇 번, 무엇에 불렸나? JS `replacer` 와 무엇이 다른가?
- ★★ 파이썬이 쓴 `NaN` 을 JS `JSON.parse` 가 읽으면?
- ★ `{1: 'a', '1': 'b'}` 의 결과를 JS 가 읽으면 어느 값이 남나?

### 10. 13·22·23·27번의 결과와 어디서 만나나 (연결) ★★

- ★★★ 27번 복사 격자의 네 도구 곁에 JSON 왕복을 다섯째로 세우면, **얕음** 행에서 무엇이 다른가?
- ★★ 27번 `[4]` 의 `"__proto__"` 실험과 4번 `[3]` 은 어떻게 이어지나?
- ★★ 23번에서 `Map` 을 JSON 으로 옮긴 두 우회로는 무엇이었나?
- ★ 22번의 hint 표에서 `JSON.stringify(x)` 줄은 무엇이었나?

### 11. 깊은 복사와 판 경계 — 어디까지가 이 주제인가 (경계) ★★

- ★★ `structuredClone` 은 누가 정하는 API 인가? 그 예외 이름은?
- ★★ 깊은 복사 수단 비교는 목록의 몇 번 주제가 정본인가?
- ★★★ `JSON.rawJSON`·`context.source` 는 몇 년 판인가? 이 머신의 세 엔진 중 어디에 있나?
- ★ JSON 모듈(`import … with { type: "json" }`)은 어느 주제의 몫인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
