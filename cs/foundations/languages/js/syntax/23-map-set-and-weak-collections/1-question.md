# js/syntax/23 — `Map`·`Set` 과 약한 컬렉션: 「키는 `-0` 을 `+0` 으로 접은 뒤 같은 값으로 찾고, 약한 쪽은 수명을 들여다볼 창을 아예 안 준다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(헤드리스) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다. ★ **6번(집합 연산)과 7번(Upsert)은 Chrome 에서만** 돌렸다 — 두 node 판에는 그 메서드가 없다.
> ★ 5번·8번 소스는 `node --expose-gc` 로 돈다 — `gc()` 는 언어 기능이 아니라 V8 플래그가 여는 함수다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 「두 값이 같은 키인가」를 **값의 짝 여덟 개 × 비교 자리 여덟 곳**에 전부 들이대고, `Map` 키 열과 **갈린 칸을 스크립트가 센다.** **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **무엇이 같은 키인가**(`NaN` · `-0` · 강제 변환 · 문자열화)
> ② **`Map` 과 객체를 무엇으로 고르나**
> ③ **약한 컬렉션이 보장하는 것과 보장하지 않는 것**(그리고 왜 들여다볼 창이 없나).
>
> ★★★ **5번은 「불렸나」를 판 수로 답한다.** 그리고 그 수 가운데 **어느 것이 명세 보장이고 어느 것이 이 판의 관찰인지**를 같이 적어야 답이다.
> ★★ **예외는 타입과 메시지로만 답한다.** ★ **메시지는 판마다 다를 수 있다** — 12번이 그 자리를 묻는다.
>
> **선행** — [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) · [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) ·
> [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) · [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md).
> ★★★ **19번의 `Map`·`Set` 순서 블록을 먼저 떠올려라** — 넣은 순서 · 지웠다 넣으면 · 순회 중에 넣으면.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 3 · 4 · 5 · 6 · 7)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸 하나하나에 y/n 을 적고, 마지막 줄의 수까지 세어 본다.** 행 이름만 보고 짐작하지 마라.
- ★★ **4번·6번은 「되는 것」과 「터지는 것」을 갈라서** 적어라. 터지면 종류와 문구까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.
- ★★★ **속도·메모리에 관한 답은 하나도 없다.** 「`Map` 이 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 값의 짝 여덟 개를 비교 자리 여덟 곳에 들이대면 (예측) ★★★ 이 주제의 축

```js
// js20b-23a-key-equality-grid.js
// 두 값 a, b 를 「같은 것」으로 보나 -- 비교 자리 여덟 곳 x 값의 짝 여덟 개.
// 칸마다 y(같다고 본다) / n(다르다고 본다) 를 찍는다. 기준 열은 Map key.
const shape1 = { a: 1 };
const shape2 = { a: 1 };
const pairs = [
  ["NaN, NaN", NaN, NaN],
  ["0, -0", 0, -0],
  ["'1', 1", "1", 1],
  ["1, 1.0", 1, 1.0],
  ["true, 1", true, 1],
  ["null, undefined", null, undefined],
  ["{a:1}, {a:1}  (two objects)", shape1, shape2],
  ["o, o  (one object)", shape1, shape1],
];
const cols = [
  ["Map key", (a, b) => new Map([[a, "x"]]).has(b)],
  ["Set", (a, b) => new Set([a, b]).size === 1],
  ["===", (a, b) => a === b],
  ["==", (a, b) => a == b],
  ["Object.is", (a, b) => Object.is(a, b)],
  ["object key", (a, b) => { const o = {}; o[a] = "x"; return Object.hasOwn(o, b); }],
  ["includes", (a, b) => [a].includes(b)],
  ["indexOf", (a, b) => [a].indexOf(b) !== -1],
];
const W = 30;
console.log("[1] the grid  (y = treated as the same, n = treated as different)");
console.log(("".padEnd(W) + cols.map(([n]) => n.padEnd(11)).join("")).trimEnd());
let cells = 0, apart = 0;
const perCol = cols.map(() => 0);
for (const [label, a, b] of pairs) {
  const ans = cols.map(([, f]) => (f(a, b) ? "y" : "n"));
  ans.forEach((v, i) => { if (i > 0) { cells++; if (v !== ans[0]) { apart++; perCol[i]++; } } });
  console.log((label.padEnd(W) + ans.map((v) => v.padEnd(11)).join("")).trimEnd());
}
console.log("");
console.log("[2] per column, cells whose answer differs from the Map-key column:");
cols.forEach(([n], i) => { if (i > 0) console.log("  " + n.padEnd(12) + perCol[i] + " / " + pairs.length); });
console.log("cells whose answer differs from the Map-key column: " + apart + " / " + cells);

```

- ★★★ 64칸의 y/n 을 전부 적어라. 특히 **`NaN, NaN` 행과 `0, -0` 행**.
- ★★ `Map` 키 열과 **한 칸도 안 갈리는 열**은 어느 것인가?
- ★ 마지막 줄 「N / M」의 N 과 M 은?

### 2. `Map` 에 `-0` 을 넣고 꺼낸 키는 무엇인가 — 명세는 왜 키를 바꿔 넣나 (왜) ★★★

- ★★★ `new Map([[-0, "x"]])` 의 첫 키에 `Object.is(k, -0)` 을 물으면? `m.get(0)` 은?
- ★★ 최신 초안은 `Map.prototype.set` 의 비교를 **「SameValueZero」라고 적지 않는다.** 대신 **어느 연산 두 개**를 차례로 쓰나?
- ★ `NaN` 을 **네 가지 방법으로** 만들어 `Set` 에 넣으면 크기는?

### 3. 같은 일을 `Map` 과 평범한 객체에 시키면 (예측) ★★★

```js
// js20b-23c-map-vs-object.js
// 같은 일을 Map 과 평범한 객체에 시킨다 -- 키 타입 · 크기 · 물려받은 이름 · "__proto__" · JSON.
const row = (label, v) => console.log("  " + label.padEnd(58) + v);
const J = JSON.stringify;

console.log("[1] two different objects as keys");
const u1 = { id: 1 }, u2 = { id: 2 };
const om = {}; om[u1] = "first"; om[u2] = "second";
const mm = new Map([[u1, "first"], [u2, "second"]]);
row("object: Object.keys(om)", J(Object.keys(om)));
row("object: om[u1]", om[u1]);
row("Map:    mm.size / mm.get(u1) / mm.get(u2)", mm.size + " / " + mm.get(u1) + " / " + mm.get(u2));
row("Map:    mm.get({ id: 1 })", String(mm.get({ id: 1 })));

console.log("");
console.log("[2] the size of each");
const o3 = { a: 1, b: 2, c: 3 };
const m3 = new Map(Object.entries(o3));
row("object: o3.size", String(o3.size));
row("object: Object.keys(o3).length", Object.keys(o3).length);
row("Map:    m3.size", m3.size);

console.log("");
console.log("[3] names that come from Object.prototype");
const counts = {};
const cm = new Map();
for (const w of ["toString", "constructor", "hasOwnProperty"]) {
  row("object: '" + w + "' in {}  /  typeof {}['" + w + "']", String(w in counts) + "  /  " + typeof counts[w]);
  row("Map:    new Map().has('" + w + "')", cm.has(w));
}
const tally = {};
for (const w of ["a", "constructor", "a"]) tally[w] = (tally[w] || 0) + 1;
row("object: tally of a, constructor, a", J(tally));
const tm = new Map();
for (const w of ["a", "constructor", "a"]) tm.set(w, (tm.get(w) || 0) + 1);
row("Map:    tally of a, constructor, a", J([...tm]));

console.log("");
console.log("[4] the string key \"__proto__\"");
const po = {};
po["__proto__"] = "plain string";
row("object: after po['__proto__'] = 'plain string'", "keys " + J(Object.keys(po)) + "  typeof po.__proto__ " + typeof po.__proto__);
const po2 = {};
po2["__proto__"] = { injected: true };
row("object: after po2['__proto__'] = { injected: true }", "keys " + J(Object.keys(po2)) + "  po2.injected " + po2.injected);
const pm = new Map();
pm.set("__proto__", { injected: true });
row("Map:    after set('__proto__', { injected: true })", "size " + pm.size + "  keys " + J([...pm.keys()]) + "  pm.injected " + pm.injected);
const parsed = JSON.parse('{"__proto__": {"injected": true}}');
row("JSON.parse('{\"__proto__\": ...}')", "keys " + J(Object.keys(parsed)) + "  parsed.injected " + parsed.injected);

console.log("");
console.log("[5] JSON");
const jm = new Map([["a", 1], ["b", 2]]);
row("JSON.stringify(map)", J(jm));
row("JSON.stringify([...map])", J([...jm]));
row("JSON.stringify(Object.fromEntries(map))", J(Object.fromEntries(jm)));
row("new Map(JSON.parse(JSON.stringify([...map]))).get('b')", new Map(JSON.parse(J([...jm]))).get("b"));
row("JSON.stringify(new Set([1, 2]))", J(new Set([1, 2])));
row("JSON.stringify({ m: map })", J({ m: jm }));

console.log("");
console.log("[6] a Set: add again, delete then add");
const st = new Set(["x", "y", "z"]);
st.add("x");
row("add('x') again -> order", J([...st]));
st.delete("x"); st.add("x");
row("delete('x'), add('x') -> order", J([...st]));
row("st.add('w') returns the set itself?", st.add("w") === st);
```

- ★★★ `[1]` 에서 `Object.keys(om)` 과 `om[u1]` 은?
- ★★★ `[3]` 의 단어 세기에서 객체 쪽 `constructor` 칸에는 **무엇이** 들어가나?
- ★★ `[4]` 의 네 줄 — 각각 자기 키가 생기나, 프로토타입이 바뀌나?
- ★★ `[5]` 의 여섯 줄.

### 4. 약한 쪽에 넣을 수 있는 것 · 없는 것 (예측) ★★★

```js
// js20b-23d-weak-keys.js
// 무엇이 WeakMap 의 키 · WeakSet 의 원소 · WeakRef 의 대상이 될 수 있나 -- 그리고 WeakMap 에 무엇이 없나.
const row = (label, v) => console.log("  " + label.padEnd(50) + v);
const attempt = (label, run) => {
  try { row(label, "ok " + String(run())); }
  catch (e) { row(label, e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] candidate keys for WeakMap.prototype.set");
const candidates = [
  ["{}", {}],
  ["[]", []],
  ["function () {}", function () {}],
  ["1", 1],
  ["'str'", "str"],
  ["null", null],
  ["undefined", undefined],
  ["1n", 1n],
  ["Symbol('local')", Symbol("local")],
  ["Symbol.for('registered')", Symbol.for("registered")],
  ["Symbol.iterator", Symbol.iterator],
];
for (const [label, key] of candidates) attempt("new WeakMap().set(" + label + ", 1)", () => new WeakMap().set(key, 1).has(key));

console.log("");
console.log("[2] the same primitive in the other weak holders");
attempt("new WeakSet().add(1)", () => new WeakSet().add(1));
attempt("new WeakRef(1)", () => new WeakRef(1));
attempt("new WeakRef(Symbol('local')).deref()", () => typeof new WeakRef(Symbol("local")).deref());
attempt("new WeakRef(Symbol.for('registered'))", () => new WeakRef(Symbol.for("registered")));
attempt("new FinalizationRegistry(f).register(1, 'h')", () => new FinalizationRegistry(() => {}).register(1, "h"));
const t = {};
attempt("registry.register(t, t)  (held value = target)", () => new FinalizationRegistry(() => {}).register(t, t));
attempt("new WeakMap([[1, 'x']])", () => new WeakMap([[1, "x"]]));
attempt("new WeakMap().get(1)", () => new WeakMap().get(1));
attempt("new WeakMap().has(1)", () => new WeakMap().has(1));

console.log("");
console.log("[3] what each prototype has");
const names = ["size", "keys", "values", "entries", "forEach", "clear", "get", "set", "has", "delete"];
const show = (C) => names.map((n) => (n in C.prototype ? n : "-".repeat(n.length))).join(" ");
row("Map.prototype", show(Map));
row("WeakMap.prototype", show(WeakMap));
row("Symbol.iterator in Map.prototype", Symbol.iterator in Map.prototype);
row("Symbol.iterator in WeakMap.prototype", Symbol.iterator in WeakMap.prototype);
attempt("[...new WeakMap()]", () => [...new WeakMap()]);
attempt("for (const x of new WeakSet()) {}", () => { for (const x of new WeakSet()) {} return "done"; });
row("JSON.stringify(new WeakMap([[t, 1]]))", JSON.stringify(new WeakMap([[t, 1]])));
```

- ★★★ `[1]` 열한 줄 — 되나, 터지나? 심볼 셋은 **서로 같은 답**인가?
- ★★ `[2]` 에서 **던지지 않는** 줄은?
- ★★ `[3]` 에서 `WeakMap.prototype` 줄은 어떻게 찍히나?
- ★ 이 소스는 **node 18 과 node 20 에서 같은 출력**을 낼까?

### 5. `gc()` 를 부른 뒤 — 콜백은 불렸나, `deref()` 는 무엇을 주나 (예측) ★★★

```js
// js20b-23e-reclaim-gc.js
// gc() 를 부른 뒤 FinalizationRegistry 콜백이 「불렸나」 와 WeakRef.deref() 의 답을 센다 -- 조건 여섯 x 20판.
// 판마다 새 객체를 만들고, gc() 를 부르고, 매크로태스크를 최대 WAIT 번 넘기며 콜백을 기다린다.
// ★ 이 블록은 「몇 판 중 몇」 만 찍는다. 「몇 번째 틱에 불렸나」 는 js20b-23f-timing-gc.js 가 따로 찍는다.
const ROUNDS = 20, WAIT = 20;
const tick = () => new Promise((r) => setTimeout(r, 0));
const strongMap = new Map();
const weakMap = new WeakMap();

// 조건마다: 대상을 만들고, 조건에 맞게 붙잡거나 놓는다. 대상 자체는 이 함수 밖으로 새지 않는다.
const conditions = {
  "dropped (no reference left)": () => ({}),
  "kept in a local that stays alive": () => { const o = {}; keep.push(o); return o; },
  "key of a Map": () => { const o = {}; strongMap.set(o, "v"); return o; },
  "key of a WeakMap": () => { const o = {}; weakMap.set(o, "v"); return o; },
  "WeakMap key whose value points back at it": () => { const o = {}; weakMap.set(o, { back: o }); return o; },
  "unregistered before gc": null,
};
const keep = [];

async function round(name, make) {
  let called = 0;
  const reg = new FinalizationRegistry(() => { called++; });
  let ref;
  const token = {};
  (() => {
    const target = make ? make() : {};
    reg.register(target, "held", token);
    ref = new WeakRef(target);
  })();
  if (!make) reg.unregister(token);
  const sameJob = ref.deref() !== undefined;
  gc();
  const sameJobAfterGc = ref.deref() !== undefined;
  await tick();
  gc();
  for (let i = 0; i < WAIT && called === 0; i++) await tick();
  return { sameJob, sameJobAfterGc, alive: ref.deref() !== undefined, called: called > 0 };
}

(async () => {
  console.log("condition".padEnd(46) + "callback  deref() after  deref() in the job");
  console.log("".padEnd(46) + "ran       a later gc     right after gc()");
  for (const [name, make] of Object.entries(conditions)) {
    let ran = 0, alive = 0, sameJobAfterGc = 0;
    for (let r = 0; r < ROUNDS; r++) {
      const o = await round(name, make);
      if (o.called) ran++;
      if (o.alive) alive++;
      if (o.sameJobAfterGc) sameJobAfterGc++;
    }
    console.log(name.padEnd(46) + (ran + "/" + ROUNDS).padEnd(10) + ("object " + alive + "/" + ROUNDS).padEnd(15) + "object " + sameJobAfterGc + "/" + ROUNDS);
  }
})();
```

- ★★★ 여섯 조건 × 세 열 — 각 칸의 「N/20」을 적어라.
- ★★★ **「key of a Map」 과 「key of a WeakMap」** 은 어떻게 갈리나? 값이 키를 되가리키는 행은?
- ★★ 맨 오른쪽 열(같은 잡 안에서 `gc()` 직후)은? 왜 탐침이 `await tick()` 뒤에 `gc()` 를 한 번 더 부르나?
- ★★★ 네 답 가운데 **명세가 보장하는 칸**은 어느 것이고 **이 판의 관찰**은 어느 것인가?

### 6. 집합 연산의 결과 순서 · 인자 검사 · 인자에게 무엇을 묻나 (예측) ★★

```js
// js20b-23g-set-methods.web.js
// 집합 연산 일곱 개(ES2025) -- 결과와 그 순서 · 인자로 무엇을 받나 · 인자의 무엇을 부르나(로그).
const row = (label, v) => console.log("  " + label.padEnd(56) + v);
const J = (s) => "[" + [...s].map(String).join(",") + "]";
const attempt = (label, run) => {
  try { row(label, String(run())); }
  catch (e) { row(label, e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] a = {1,2,3,4}, b = {5,3,1} -- results in iteration order");
const a = new Set([1, 2, 3, 4]);
const b = new Set([5, 3, 1]);
row("a.union(b)", J(a.union(b)));
row("b.union(a)", J(b.union(a)));
row("a.intersection(b)", J(a.intersection(b)));
row("b.intersection(a)", J(b.intersection(a)));
row("a.difference(b)", J(a.difference(b)));
row("a.symmetricDifference(b)", J(a.symmetricDifference(b)));
row("a.isSubsetOf(b) / isSupersetOf(b) / isDisjointFrom(b)", [a.isSubsetOf(b), a.isSupersetOf(b), a.isDisjointFrom(b)].join(" / "));
row("new Set([1,3]).isSubsetOf(a)", new Set([1, 3]).isSubsetOf(a));
row("a after all of the above", J(a));
row("a.union(b) === a", a.union(b) === a);

console.log("");
console.log("[2] what can be the argument");
attempt("a.union([5, 6])", () => J(a.union([5, 6])));
attempt("a.union(new Map([[9, 'x']]))", () => J(a.union(new Map([[9, "x"]]))));
attempt("a.union({ size: 1, has: () => true })", () => J(a.union({ size: 1, has: () => true })));
attempt("a.union({ has() {}, keys() {} })  (no size)", () => J(a.union({ has() {}, keys() {} })));
attempt("a.union({ size: -1, has() {}, keys() {} })", () => J(a.union({ size: -1, has() {}, keys() {} })));
attempt("a.union('abc')", () => J(a.union("abc")));
attempt("new Set([NaN, 0]).intersection(new Set([NaN, -0]))", () => J(new Set([NaN, 0]).intersection(new Set([NaN, -0]))));

console.log("");
console.log("[3] a set-like argument with logging -- which of size / has / keys each method calls");
function setLike(values, log) {
  return {
    get size() { log.push("size"); return values.length; },
    has(v) { log.push("has(" + v + ")"); return values.includes(v); },
    keys() {
      log.push("keys()");
      let i = 0;
      return { next() { log.push("next"); return i < values.length ? { value: values[i++], done: false } : { value: undefined, done: true }; } };
    },
  };
}
const three = new Set([1, 2, 3]);
for (const m of ["union", "intersection", "difference", "symmetricDifference", "isSubsetOf", "isSupersetOf", "isDisjointFrom"]) {
  for (const other of [[2, 9], [2, 9, 8, 7, 6]]) {
    const log = [];
    const r = three[m](setLike(other, log));
    const shown = r instanceof Set ? J(r) : String(r);
    console.log("  {1,2,3}." + m + "(size " + other.length + ")  -> " + shown);
    console.log("      " + log.join(" "));
  }
}
```

- ★★★ `[1]` 에서 `a.intersection(b)` 의 순서는 **a 의 순서**인가 **b 의 순서**인가?
- ★★ `[2]` 일곱 줄 — 통과하나, 터지나? 터지면 종류(`TypeError`·`RangeError`)까지.
- ★★★ `[3]` — `intersection` 과 `difference` 는 인자 크기 2 와 5 에서 **같은 것을 부르나**?
- ★ `isSubsetOf(size 2)` 의 로그는 몇 낱말인가?

### 7. `getOrInsertComputed` 는 콜백을 언제 부르나 (예측) ★★

```js
// js20b-23h-upsert.web.js
// getOrInsert / getOrInsertComputed (ES2026 Upsert) -- 무엇을 돌려주나 · 콜백을 언제 부르나(로그).
const row = (label, v) => console.log("  " + label.padEnd(58) + v);
const J = JSON.stringify;
const attempt = (label, run) => {
  try { row(label, String(run())); }
  catch (e) { row(label, e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] getOrInsert(key, value)");
const m = new Map([["a", 1]]);
row("m.getOrInsert('a', 99)", m.getOrInsert("a", 99));
row("m.getOrInsert('b', 2)", m.getOrInsert("b", 2));
row("m entries", J([...m]));
let evaluated = 0;
const mk = () => { evaluated++; return []; };
m.getOrInsert("a", mk());
row("argument expression evaluated for an existing key?", "times " + evaluated);

console.log("");
console.log("[2] getOrInsertComputed(key, callback) with a logging callback");
const log = [];
const cb = (k) => { log.push("callback(" + String(k) + ")"); return "made-" + String(k); };
const c = new Map([["a", "old"]]);
row("c.getOrInsertComputed('a', cb)", c.getOrInsertComputed("a", cb) + "   log " + J(log));
log.length = 0;
row("c.getOrInsertComputed('b', cb)", c.getOrInsertComputed("b", cb) + "   log " + J(log));
log.length = 0;
row("c.getOrInsertComputed('b', cb)  (again)", c.getOrInsertComputed("b", cb) + "   log " + J(log));
log.length = 0;
row("c.getOrInsertComputed(-0, cb) -> key passed to cb", c.getOrInsertComputed(-0, (k) => { log.push(Object.is(k, -0) ? "-0" : "+0"); return "zero"; }) + "   log " + J(log));
row("c entries", J([...c].map(([k, v]) => [String(k), v])));

console.log("");
console.log("[3] the callback writes the same key before returning");
const w = new Map();
const r = w.getOrInsertComputed("k", () => { w.set("k", "set inside"); return "returned"; });
row("return value", r);
row("w.get('k') afterwards", w.get("k"));
row("w.size", w.size);

console.log("");
console.log("[4] the callback throws");
const t = new Map();
attempt("t.getOrInsertComputed('k', () => { throw ... })", () => t.getOrInsertComputed("k", () => { throw new Error("from callback"); }));
row("t.has('k') afterwards", t.has("k"));
attempt("t.getOrInsertComputed('k', 'not a function')", () => t.getOrInsertComputed("k", "not a function"));
attempt("new Map([['k', 1]]).getOrInsertComputed('k', 42)", () => new Map([["k", 1]]).getOrInsertComputed("k", 42));

console.log("");
console.log("[5] the WeakMap versions");
const wm = new WeakMap();
const key = {};
row("wm.getOrInsert(key, 1) then (key, 2)", wm.getOrInsert(key, 1) + " then " + wm.getOrInsert(key, 2));
attempt("wm.getOrInsert(1, 'x')", () => wm.getOrInsert(1, "x"));
log.length = 0;
attempt("wm.getOrInsertComputed(1, cb)  -> cb log", () => wm.getOrInsertComputed(1, cb) + "   log " + J(log));
row("  cb log after that attempt", J(log));
row("typeof Set.prototype.getOrInsert", typeof Set.prototype.getOrInsert);

console.log("");
console.log("[6] the older idiom next to it -- a Map subclass that logs its own has / get / set");
const calls = [];
class Counted extends Map {
  has(k) { calls.push("has"); return super.has(k); }
  get(k) { calls.push("get"); return super.get(k); }
  set(k, v) { calls.push("set"); return super.set(k, v); }
}
const old = new Counted();
if (!old.has("x")) old.set("x", []);
old.get("x").push(1);
row("if (!has) set; get(...).push  -> calls", J(calls));
calls.length = 0;
old.getOrInsert("y", []).push(1);
row("getOrInsert(...).push          -> calls", J(calls));
```

- ★★★ `[2]` 세 번 부를 때마다 로그는? `-0` 으로 부르면 콜백은 무엇을 받나?
- ★★ `[1]` 의 `times` 는 0 인가 1 인가?
- ★★ `[3]` — 콜백 안의 `set` 과 콜백의 반환값 중 무엇이 남나?
- ★★★ `[4]` 둘째·셋째 줄의 **예외 문구**를 적어라. 그 문구는 원인을 맞게 가리키나?
- ★ `[6]` 두 줄의 호출 기록은?

### 8. 「불렸나」 와 「언제」 를 왜 두 블록으로 갈랐나 (왜) ★★★

```js
// js20b-23f-timing-gc.js
// 「언제」 를 찍는다 -- gc() 뒤 몇 번째 매크로태스크에서 콜백이 돌았나, gc() 를 안 부르면 돌았나.
// ★ 명세가 묶지 않는 칸이다. 이 블록은 흔들려도 되는 블록으로 선언해 둔다(js20b-23e 와 쪼갠 이유).
const ROUNDS = 20, WAIT = 20;
const tick = () => new Promise((r) => setTimeout(r, 0));

let beforeReturn = 0;
async function round(callGc) {
  let at = -1, n = 0;
  const reg = new FinalizationRegistry(() => { at = n; });
  (() => { reg.register({}, "held"); })();
  await tick();
  if (callGc) { gc(); if (at >= 0) beforeReturn++; }
  for (n = 0; n < WAIT && at < 0; n++) await tick();
  return at;
}

(async () => {
  const withGc = [];
  for (let r = 0; r < ROUNDS; r++) withGc.push(await round(true));
  console.log("[1] gc() called -- macrotask index at which the callback ran, per round (-1 = not within " + WAIT + ")");
  console.log("  ticks: " + withGc.join(" "));
  console.log("  rounds where it had run before gc() returned: " + beforeReturn + "/" + ROUNDS);
  const withoutGc = [];
  for (let r = 0; r < ROUNDS; r++) withoutGc.push(await round(false));
  console.log("[2] gc() not called -- the same, per round");
  console.log("  ticks: " + withoutGc.join(" "));
})();
```

- ★★★ 명세의 목표 절은 GC 에 대해 **무엇을 보장하지 않는다**고 첫 문장에 적나?
- ★★ 이 블록의 어느 줄이 **흔들리는 칸**으로 선언돼 있나? 5번 블록과 섞으면 재대조가 어떻게 되나?
- ★★ `gc()` 를 안 부른 `[2]` 가 20판 모두 `-1` 이었다면, 그것을 「**안 불린다**」로 적어도 되나?

### 9. 파이썬 `dict` 의 「같은 키」 와 JS `Map` 의 「같은 키」 (연결) ★★★

- ★★★ 파이썬 갈래 12번에서 `1` · `1.0` · `True` 는 몇 칸이었나? JS `Map` 에서 `1` · `1.0` · `true` 는?
- ★★★ `nan` 두 개는 파이썬에서 몇 칸이었나? JS 에서 `NaN` 네 개는?
- ★★ 두 언어는 **어느 방향으로** 반대인가 — 한 문장으로.

### 10. `WeakMap` 에는 왜 `size` 도 순회도 없나 (왜) ★★★

- ★★★ 명세 `WeakMap` 절 머리말은 구현이 **무엇을 제공하면 안 된다**고 적나?
- ★★ 그것이 없으면 **무엇이 프로그램에 새어 나오나**? 명세가 그것을 무엇이라 부르나?
- ★ 그래서 이 문서는 수명을 **어느 창으로 바꿔** 물었나? 그 창이 **못 보는 것**은?

### 11. `Map` 과 객체를 고르는 기준 — 그리고 해시 테이블은 어디까지가 이 주제인가 (경계) ★★

- ★★ 키 타입 · 순서 · 크기 · 물려받은 이름 · `"__proto__"` · JSON 여섯 기준에서 각각 무엇이 갈리나?
- ★★ 「`Map` 이 더 빠르다」는 이 문서에서 어느 칸에 들어가나?
- ★ `cs/data-structure/05-hashmap/` 이 **끝내는 것**과 이 주제가 **시작하는 것**을 한 줄씩.

### 12. 두 node 판이 갈린 블록 — 무엇이 갈렸나 (연결) ★★

- ★★★ 이 주제에서 v18 과 v20 이 **갈린 탐침은 어느 것**이고, 갈린 줄은 **두 종류**인가?
- ★★ 한 종류는 **판 경계(ES2023)** 이고 한 종류는 **문구**다. 각각 어느 줄인가?
- ★ 그래서 무엇을 근거로 쓰고 무엇을 근거로 안 쓰나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
