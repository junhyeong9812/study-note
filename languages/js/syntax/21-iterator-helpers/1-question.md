# js/syntax/21 — 이터레이터 헬퍼: 「배열 메서드는 단계마다 전부 돌고, 헬퍼는 한 값씩 끝까지 흘려보낸다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — ★★★ **헬퍼는 node v18.19.1 · v20.19.6 에 없다.** 그래서 `.web.js` 탐침은 전부 **Google Chrome 151 헤드리스**에서 돌렸다
> (`js20b-page.html?<파일>` 로 열고 `console.log` 를 모아 `--dump-dom` 으로 받는다 — 페이지 소스는 2-summary 머리에 있다).
> `.js` 탐침(10번)은 node20 이 기본이고 node18 로 대조했다. x86-64 Linux.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다** — 콜백과 원본 `next`/`return` 에 심은 로그.
> 배열판과 헬퍼판은 **결과가 같아서** 값으로는 못 가른다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **콜백이 언제 · 몇 번 · 어떤 순서로 불리나**(그리고 어느 모양에서 갈리나)
> ② **헬퍼는 어디에 붙어 있나**(사슬)
> ③ **헬퍼는 원본에 무엇을 하나**(소비 · 닫기 · 인자 검사 시점).
>
> ★★★ **답을 적을 때 「결과 값」만 적으면 절반도 못 맞힌 것이다.** 1·2번은 **호출 수와 순서**를, 3번은 **원본의 `next` 횟수와 `return()` 여부**를,
> 5번은 **던진 시점(만들 때 / 첫 `next()`)과 원본 로그**를 같이 적어야 답이다.
> ★★ **예외는 타입과 메시지로만 답한다.** ★ 메시지는 판마다 다를 수 있다.
>
> **선행** — [20 — 제너레이터](../20-generators/2-summary.md)(★★★ 직접 선행) · [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ `return()` 의 규칙) ·
> [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md).
> ★★★ **19번의 요약 표를 먼저 떠올려라** — `const [a, b, c] = it` 은 값이 딱 셋인데 닫았고, `[a, b, c, d]` 는 닫지 않았다. 왜였나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「무엇이 나오나」가 아니라 「무엇이 몇 번, 어떤 순서로 불리나」를 묻는다.** 두 판의 로그를 한 줄씩 먼저 적어라.
- ★★ **2번은 열 줄 중 「호출 수가 갈리는 줄」을 먼저 골라라** — 그 다음에 수를 적는다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판(node)의 사정인가**」.
- ★★★ **속도·메모리에 관한 답은 하나도 없다.** 「메모리를 아낀다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 파이프라인 두 벌의 콜백 로그 (예측) ★★★ 이 주제의 축

원본 `1..10` · `map` 은 `x * 10` · `filter` 는 20 의 배수 · 앞의 두 개. 두 벌의 **결과 · `map`/`filter` 호출 수 · 로그 순서**를 적어라.
`[2]` 는 **사슬을 만든 직후의 로그 수**도, `[3]` 은 **`next()` 마다 어느 콜백이 돌았나**도 적어라.

```js
// js20b-21a-when.web.js
// 같은 파이프라인을 두 벌로 -- 배열 메서드판과 이터레이터 헬퍼판. 콜백이 「언제 · 몇 번 · 어떤 순서로」 불리나를 로그로 찍는다.
// 원본은 1..10. map 은 x*10, filter 는 20 의 배수만, 앞의 두 개만 취한다.
const L = [];
const src = () => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const mapFn = (x) => { L.push("map(" + x + ")"); return x * 10; };
const keep = (x) => { L.push("filter(" + x + ")"); return x % 20 === 0; };
const n = (p) => L.filter((m) => m.startsWith(p)).length;

console.log("[1] array methods: arr.map(f).filter(g).slice(0, 2)");
L.length = 0;
const a = src().map(mapFn).filter(keep).slice(0, 2);
console.log("    result " + JSON.stringify(a));
console.log("    map calls " + n("map(") + " · filter calls " + n("filter("));
console.log("    order  " + L.join(" "));
const arrayCounts = [n("map("), n("filter(")];

console.log("");
console.log("[2] iterator helpers: arr.values().map(f).filter(g).take(2)");
L.length = 0;
const pipe = src().values().map(mapFn).filter(keep).take(2);
console.log("    after building the pipeline:  log entries " + L.length);
const h = pipe.toArray();
console.log("    after toArray():  result " + JSON.stringify(h));
console.log("    map calls " + n("map(") + " · filter calls " + n("filter("));
console.log("    order  " + L.join(" "));
const helperCounts = [n("map("), n("filter(")];

console.log("");
console.log("[3] the same helper pipeline, one next() at a time");
L.length = 0;
const step = src().values().map(mapFn).filter(keep).take(2);
for (let i = 1; i <= 3; i++) {
  const before = L.length;
  const r = step.next();
  console.log("    next#" + i + "  " + JSON.stringify(r).padEnd(28) + " callbacks run in this call: " + (L.slice(before).join(" ") || "(none)"));
}

console.log("");
console.log("[4] counts side by side  (array / helper)");
console.log("    map     " + arrayCounts[0] + " / " + helperCounts[0]);
console.log("    filter  " + arrayCounts[1] + " / " + helperCounts[1]);
console.log("    results equal: " + String(JSON.stringify(a) === JSON.stringify(h)));
```

- `[1]` 과 `[2]` 의 `order` 줄은 어떻게 다른가?
- `[3]` 의 `next#3` 은 콜백을 몇 개 부르나?

### 2. 열 벌의 격자 — 어느 줄의 호출 수가 갈리나 (예측) ★★★

원본은 언제나 `1..10`. 줄마다 **배열판 값 · 헬퍼판 값 · 호출 수 두 개**를 적고, 마지막 두 줄의 **N / 10** 을 적어라.

```js
// js20b-21b-grid.web.js
// 격자 -- 파이프라인 여러 벌을 배열판 / 헬퍼판으로 돌려 「결과 값」과 「콜백 호출 수」를 칸마다 견준다.
// 원본은 언제나 1..10. 콜백은 전부 한 계수기를 올린다.
let calls = 0;
const f = (fn) => (...args) => { calls++; return fn(...args); };
const arr = () => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const it = () => arr().values();
const cases = [
  ["map(x*2) then first 3", () => arr().map(f((x) => x * 2)).slice(0, 3), () => it().map(f((x) => x * 2)).take(3).toArray()],
  ["filter(odd) then first 2", () => arr().filter(f((x) => x % 2)).slice(0, 2), () => it().filter(f((x) => x % 2)).take(2).toArray()],
  ["skip 3, then map, first 2", () => arr().slice(3).map(f((x) => -x)).slice(0, 2), () => it().drop(3).map(f((x) => -x)).take(2).toArray()],
  ["find(x > 3)", () => arr().find(f((x) => x > 3)), () => it().find(f((x) => x > 3))],
  ["some(x === 2)", () => arr().some(f((x) => x === 2)), () => it().some(f((x) => x === 2))],
  ["every(x < 4)", () => arr().every(f((x) => x < 4)), () => it().every(f((x) => x < 4))],
  ["map then find(x > 30)", () => arr().map(f((x) => x * 10)).find(f((x) => x > 30)), () => it().map(f((x) => x * 10)).find(f((x) => x > 30))],
  ["flatMap([x, x]) then first 3", () => arr().flatMap(f((x) => [x, x])).slice(0, 3), () => it().flatMap(f((x) => [x, x])).take(3).toArray()],
  ["reduce(sum)", () => arr().reduce(f((s, x) => s + x), 0), () => it().reduce(f((s, x) => s + x), 0)],
  ["map then reduce(sum)", () => arr().map(f((x) => x * 2)).reduce(f((s, x) => s + x), 0), () => it().map(f((x) => x * 2)).reduce(f((s, x) => s + x), 0)],
];
const run = (fn) => { calls = 0; const v = fn(); return [JSON.stringify(v), calls]; };
let valueDiff = 0, callDiff = 0;
console.log("pipeline".padEnd(32) + "array value".padEnd(16) + "helper value".padEnd(16) + "calls array / helper");
for (const [label, A, H] of cases) {
  const [va, ca] = run(A);
  const [vh, ch] = run(H);
  if (va !== vh) valueDiff++;
  if (ca !== ch) callDiff++;
  console.log(label.padEnd(32) + va.padEnd(16) + vh.padEnd(16) + String(ca).padStart(2) + " / " + String(ch).padStart(2) + (ca !== ch ? "   <- differs" : ""));
}
console.log("");
console.log("value cells that differ " + valueDiff + " / " + cases.length);
console.log("call-count cells that differ " + callDiff + " / " + cases.length);
```

- `find(x > 3)` · `some(x === 2)` · `every(x < 4)` 의 배열판 호출 수는?
- `reduce(sum)` 두 줄은?

### 3. 원본에 로그를 심고 헬퍼·종단 메서드 열네 가지를 돌리면 (예측) ★★★

원본은 값 **다섯**(1\~5). 줄마다 **원본 `next` 횟수**와 **`return()` 이 불리나**를 적어라. 특히 `take(2)` · `take(5)` · `take(9)` 세 줄.

```js
// js20b-21g-close.web.js
// 원본 이터레이터에 next / return 로그를 심고, 헬퍼와 종단 메서드가 원본의 return() 을 부르는 자리를 찍는다.
const L = [];
function traced(n = 5) {
  let i = 0;
  const it = Object.create(Iterator.prototype);
  it.next = () => { i++; const done = i > n; L.push(done ? "next#" + i + " done" : "next#" + i); return done ? { value: undefined, done: true } : { value: i, done: false }; };
  it.return = () => { L.push("return()"); return { value: undefined, done: true }; };
  return it;
}
const rows = [];
function probe(label, fn) {
  L.length = 0;
  let r;
  try { r = "result " + JSON.stringify(fn()); } catch (e) { r = "caught " + e.constructor.name + " 「" + e.message + "」"; }
  rows.push([label, L.filter((m) => m.startsWith("next#")).length, L.filter((m) => m === "return()").length]);
  console.log(label);
  console.log("    " + (L.join(" | ") || "(nothing)") + "   [" + r + "]");
}
console.log("[1] helpers and terminals over a 5-value source");
probe("take(2).toArray()", () => traced().take(2).toArray());
probe("take(5).toArray()", () => traced().take(5).toArray());
probe("take(9).toArray()", () => traced().take(9).toArray());
probe("drop(2).toArray()", () => traced().drop(2).toArray());
probe("find(x => x === 2)", () => traced().find((x) => x === 2));
probe("some(x => x === 2)", () => traced().some((x) => x === 2));
probe("every(x => x < 2)", () => traced().every((x) => x < 2));
probe("find(x => x === 99)", () => traced().find((x) => x === 99));
probe("forEach(x => {})", () => traced().forEach((x) => {}));
probe("reduce((s, x) => s + x)", () => traced().reduce((s, x) => s + x));
console.log("");
console.log("[2] when a callback throws, or the consumer leaves");
probe("map(throws at 2).toArray()", () => traced().map((x) => { if (x === 2) throw new Error("mapper threw"); return x; }).toArray());
probe("for (x of map(f)) break at 2", () => { for (const x of traced().map((v) => v)) if (x === 2) break; });
probe("const [a] = map(f)", () => { const [a] = traced().map((v) => v); return a; });
probe("flatMap(x => [x, x]).take(3).toArray()", () => traced().flatMap((x) => [x, x]).take(3).toArray());
console.log("");
console.log("[3] summary  (label / source next calls / source return calls)");
for (const [label, n, r] of rows) console.log("  " + label.padEnd(40) + String(n).padStart(2) + "  " + r);
console.log("return() was called in " + rows.filter(([, , r]) => r > 0).length + " of " + rows.length + " probes");
```

- `take(5)` 는 여섯째 `next` 를 부르나?
- `for (x of map(f)) break` 는 **원본**의 `return()` 까지 닿나?

### 4. 같은 헬퍼 · 같은 원본을 두 번 쓰면 (예측) ★★★

```js
// js20b-21f-consume.web.js
// 헬퍼는 원본을 「소비」하나 -- 같은 헬퍼 · 같은 원본을 두 번 쓰면 무엇이 남나.
const J = JSON.stringify;
console.log("[1] one helper, two toArray() calls");
const m = [1, 2, 3].values().map((x) => x * 2);
console.log("  first  toArray()  " + J(m.toArray()));
console.log("  second toArray()  " + J(m.toArray()));

console.log("");
console.log("[2] the source after a helper has been drained");
const src = [1, 2, 3].values();
const doubled = src.map((x) => x * 2);
console.log("  doubled.toArray()   " + J(doubled.toArray()));
console.log("  src.next()          " + J(src.next()));

console.log("");
console.log("[3] two helpers built on one source, pulled in turn");
const shared = [1, 2, 3, 4, 5, 6].values();
const a = shared.map((x) => "a" + x);
const b = shared.map((x) => "b" + x);
const got = [];
for (let k = 0; k < 4; k++) got.push(String(a.next().value), String(b.next().value));
console.log("  a, b, a, b, ...     " + J(got));

console.log("");
console.log("[4] the array, by contrast");
const arr = [1, 2, 3];
const d = arr.map((x) => x * 2);
console.log("  arr.map twice       " + J(d) + " " + J(arr.map((x) => x * 2)));
console.log("  arr after           " + J(arr));

console.log("");
console.log("[5] h[Symbol.iterator]() === h, and two spreads of h");
const h = [1, 2].values().map((x) => x);
console.log("  h[Symbol.iterator]() === h   " + String(h[Symbol.iterator]() === h));
console.log("  [...h] then [...h]           " + J([...h]) + " " + J([...h]));

console.log("");
console.log("[6] callback arguments, and the methods a helper object has");
console.log("  map((v, i) => v + ':' + i)       " + J([10, 20, 30].values().map((v, i) => v + ":" + i).toArray()));
console.log("  reduce((s, v, i) => s + i, '')   " + J([10, 20, 30].values().reduce((s, v, i) => s + i, "")));
const hh = [1].values().map((x) => x);
console.log("  typeof next / return / throw     " + typeof hh.next + " / " + typeof hh.return + " / " + typeof hh.throw);
```

- `[1]` 두 번째 `toArray()` 는?
- `[3]` 여덟 칸에는 무엇이 들어가나?
- `[6]` `typeof … throw` 는?

### 5. 인자를 잘못 주면 — 무엇이, 언제 던지나 (예측) ★★

줄마다 **「만들 때(build)」인가 「첫 `next()`」인가**, 예외의 **타입**, 그리고 **원본 로그**를 적어라.

```js
// js20b-21h-args.web.js
// 인자를 잘못 주면 -- 무엇이 · 언제 던지나. 원본에 로그를 심어 「헬퍼를 만든 순간」과 「첫 next()」를 가른다.
const L = [];
function traced() {
  let i = 0;
  const it = Object.create(Iterator.prototype);
  it.next = () => { i++; L.push("next#" + i); return i <= 3 ? { value: i, done: false } : { value: undefined, done: true }; };
  it.return = () => { L.push("return()"); return {}; };
  return it;
}
function probe(label, build) {
  L.length = 0;
  let stage = "build";
  let r;
  try { const h = build(traced()); stage = "first next()"; r = "ok " + JSON.stringify(h.next()); }
  catch (e) { r = "at " + stage + ": " + e.constructor.name + " 「" + e.message + "」"; }
  console.log(label.padEnd(34) + r);
  console.log("".padEnd(34) + "source log: " + (L.join(" | ") || "(nothing)"));
}
probe("take(-1)", (s) => s.take(-1));
probe("take(NaN)", (s) => s.take(NaN));
probe("take('2')", (s) => s.take("2"));
probe("take(Infinity)", (s) => s.take(Infinity));
probe("drop(-1)", (s) => s.drop(-1));
probe("map('not a function')", (s) => s.map("not a function"));
probe("filter(undefined)", (s) => s.filter(undefined));
probe("flatMap(x => 'ab')", (s) => s.flatMap((x) => "ab"));
probe("flatMap(x => [x, x])", (s) => s.flatMap((x) => [x, x]));
probe("flatMap(x => x)", (s) => s.flatMap((x) => x));
console.log("");
const t = (label, fn) => { let r; try { r = JSON.stringify(fn()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; } console.log(label.padEnd(44) + r); };
t("[].values().reduce((s, x) => s + x)", () => [].values().reduce((s, x) => s + x));
t("[].values().reduce((s, x) => s + x, 0)", () => [].values().reduce((s, x) => s + x, 0));
t("Iterator.prototype.map.call(1, x => x)", () => Iterator.prototype.map.call(1, (x) => x));
t("Iterator.prototype.toArray.call({})", () => Iterator.prototype.toArray.call({}));
```

- `take(-1)` 은 원본을 한 번이라도 당기나? 원본의 `return()` 은?
- `flatMap(x => 'ab')` 와 `flatMap(x => [x, x])` 는 무엇이 다른가?

### 6. `Iterator.from` 이 돌려주는 것 (예측) ★★

```js
// js20b-21e-from.web.js
// Iterator.from -- 무엇을 받고, 무엇을 돌려주나. 돌려준 것이 넘긴 것과 같은 객체인지도 찍는다.
const t = (label, fn) => { let r; try { r = String(fn()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; } console.log("  " + label.padEnd(58) + r); };
let i = 0;
const bare = { next() { i++; return i <= 3 ? { value: i, done: false } : { value: undefined, done: true }; } };
const arrIt = [7, 8].values();
const iterableObj = { [Symbol.iterator]() { let k = 0; return { next: () => (k++ < 2 ? { value: "v" + k, done: false } : { done: true }) }; } };

console.log("[1] what comes back");
t("from(bare { next }) === bare", () => Iterator.from(bare) === bare);
t("typeof from(bare).map", () => typeof Iterator.from(bare).map);
t("from(bare).map(x => x * 100).toArray()", () => JSON.stringify(Iterator.from(bare).map((x) => x * 100).toArray()));
t("from([7, 8].values()) === that iterator", () => Iterator.from(arrIt) === arrIt);
t("from([1, 2, 3])  -> toArray()", () => JSON.stringify(Iterator.from([1, 2, 3]).toArray()));
t("from(iterable object) -> toArray()", () => JSON.stringify(Iterator.from(iterableObj).toArray()));
t("from('ab') -> toArray()", () => JSON.stringify(Iterator.from("ab").toArray()));

console.log("");
console.log("[2] other arguments");
t("from(42)", () => Iterator.from(42));
t("from(null)", () => Iterator.from(null));
t("typeof from({})  (the call alone)", () => typeof Iterator.from({}));
t("from({}).toArray()", () => Iterator.from({}).toArray());
t("from({ a: 1 }).next()", () => Iterator.from({ a: 1 }).next());

console.log("");
console.log("[3] a bare { next } object: typeof map, and map borrowed with call");
let j = 0;
const bare2 = { next() { j++; return j <= 2 ? { value: j, done: false } : { done: true }; } };
t("typeof bare2.map", () => typeof bare2.map);
t("Iterator.prototype.map.call(bare2, x => -x).toArray()", () => JSON.stringify(Iterator.prototype.map.call(bare2, (x) => -x).toArray()));
```

- `from(bare) === bare` 와 `from([7, 8].values()) === that iterator` 는 각각?
- `from({})` 는 **부르는 순간** 던지나, 나중에 던지나?

### 7. 제너레이터 · `Map` 이터레이터 · 문자열 이터레이터에 모두 `.map` 이 있는데 손으로 만든 `{ next }` 에는 없는 이유 (왜) ★★★

```js
// js20b-21d-chain.web.js
// 헬퍼는 어디에 붙어 있나 -- 이터레이터마다 프로토타입 사슬을 따라가며 Iterator.prototype 을 몇 단계 위에서 만나는지 찍는다.
const IP = Iterator.prototype;
const name = (p) => {
  if (p === null) return "null";
  if (p === IP) return "Iterator.prototype";
  if (p === Object.prototype) return "Object.prototype";
  if (p === gen.prototype) return "gen.prototype";
  const tag = Object.prototype.hasOwnProperty.call(p, Symbol.toStringTag) ? p[Symbol.toStringTag] : "?";
  return "(" + tag + " proto)";
};
const chain = (o) => { const out = []; let p = Object.getPrototypeOf(o); while (p !== null) { out.push(name(p)); p = Object.getPrototypeOf(p); } return out.join(" -> "); };
function* gen() { yield 1; }
const samples = [
  ["[1].values()", [1].values()],
  ["new Map([[1, 2]]).entries()", new Map([[1, 2]]).entries()],
  ["new Set([1]).values()", new Set([1]).values()],
  ["'ab'[Symbol.iterator]()", "ab"[Symbol.iterator]()],
  ["'a-b'.matchAll(/-/g)", "a-b".matchAll(/-/g)],
  ["gen()", gen()],
  ["{ next() {...} }  (hand-written)", { next() { return { done: true }; } }],
];
console.log("[1] prototype chain of each iterator");
for (const [label, o] of samples) console.log("  " + label.padEnd(34) + chain(o));

console.log("");
console.log("[2] typeof o.map / typeof o.toArray");
for (const [label, o] of samples) console.log("  " + label.padEnd(34) + typeof o.map + " / " + typeof o.toArray);

console.log("");
console.log("[3] own properties of Iterator.prototype (names, sorted)");
console.log("  " + Reflect.ownKeys(IP).map(String).sort().join(" "));

console.log("");
console.log("[4] Iterator itself");
const t = (label, fn) => { let r; try { r = String(fn()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; } console.log("  " + label.padEnd(56) + r); };
t("typeof Iterator", () => typeof Iterator);
t("new Iterator()", () => new Iterator());
t("class C extends Iterator; new C() instanceof Iterator", () => { class C extends Iterator { next() { return { done: true }; } } return new C() instanceof Iterator; });
t("[1].values() instanceof Iterator", () => [1].values() instanceof Iterator);
t("gen() instanceof Iterator", () => gen() instanceof Iterator);
```

15번의 조회 규칙으로 답하라. 「이터레이터다」와 「헬퍼가 있다」는 같은 질문인가?

### 8. 끝없는 제너레이터에 `.take(5)` 는 되는데 배열 메서드로는 같은 일을 못 하는 이유 (왜) ★★

```js
// js20b-21c-endless.web.js
// 끝이 없는 제너레이터에 헬퍼를 건다. 원본이 몇 번 불렸나를 센다.
let pulled = 0;
function* naturals() { let i = 1; while (true) { pulled++; yield i++; } }

const show = (label, fn) => {
  pulled = 0;
  let r;
  try { r = JSON.stringify(fn()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log(label.padEnd(46) + r.padEnd(22) + "values pulled " + pulled);
};
show("naturals().take(5).toArray()", () => naturals().take(5).toArray());
show("naturals().map(x => x * x).take(4).toArray()", () => naturals().map((x) => x * x).take(4).toArray());
show("naturals().filter(x => x % 7 === 0).take(3)", () => naturals().filter((x) => x % 7 === 0).take(3).toArray());
show("naturals().drop(100).take(2).toArray()", () => naturals().drop(100).take(2).toArray());
show("naturals().find(x => x * x > 50)", () => naturals().find((x) => x * x > 50));
show("naturals().some(x => x === 3)", () => naturals().some((x) => x === 3));
show("naturals().every(x => x < 5)", () => naturals().every((x) => x < 5));
show("naturals().map(x => x)  (no terminal)", () => { naturals().map((x) => x); return "built"; });
show("naturals().take(0).toArray()", () => naturals().take(0).toArray());
```

`filter(x => x % 7 === 0).take(3)` 과 `drop(100).take(2)` 은 원본을 몇 번 당기나? 그리고 `[...naturals()]` 는 왜 이 문서에서 돌리지 않았나?

### 9. `take(5)` 가 값이 딱 다섯인데 닫는 것은 19번의 어느 줄과 같은 모양인가 (연결) ★★★

19번 요약 표의 `[a, b, c]` · `[a, b, c, d]` 두 줄과 3번의 `take(5)` · `take(9)` 두 줄을 **한 규칙**으로 묶어라.

### 10. node 18/20 에서 헬퍼는 — 그리고 같은 질문을 무엇으로 바꿔 물었나 (연결) ★★

```js
// js20b-21x-node-absent.js
// 이 판(node)에서 헬퍼를 부르면 어떻게 되나 -- 그리고 제너레이터로 손수 만든 파이프라인은 어떤 로그를 내나.
const L = [];
const mapFn = (x) => { L.push("map(" + x + ")"); return x * 10; };
const keep = (x) => { L.push("filter(" + x + ")"); return x % 20 === 0; };
const src = () => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

console.log("[1] the helper call on this node");
try { src().values().map(mapFn); console.log("  no error"); }
catch (e) { console.log("  " + e.constructor.name + " 「" + e.message + "」"); }
console.log("  typeof globalThis.Iterator  " + typeof globalThis.Iterator);

console.log("");
console.log("[2] a hand-rolled pipeline with generator functions");
function* map(it, f) { for (const x of it) yield f(x); }
function* filter(it, p) { for (const x of it) if (p(x)) yield x; }
function* take(it, n) { if (n <= 0) return; for (const x of it) { yield x; if (--n === 0) return; } }
L.length = 0;
const out = [...take(filter(map(src(), mapFn), keep), 2)];
console.log("  result " + JSON.stringify(out));
console.log("  map calls " + L.filter((m) => m.startsWith("map(")).length + " · filter calls " + L.filter((m) => m.startsWith("filter(")).length);
console.log("  order  " + L.join(" "));
```
```sh
# js20b-vdiff.sh
#!/usr/bin/env bash
# 두 node 판이 갈린 탐침이 몇 개인가 -- 스크립트가 직접 센다(브라우저 탐침 *.web.js 는 대상이 아니다).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js20b-2[0-3]?-*.js; do
  case $f in *.web.js) continue ;; esac
  flags=""; case $f in *-gc.js) flags="--expose-gc" ;; esac
  a="$("$N18" $flags "$f" 2>&1)"
  b="$("$N20" $flags "$f" 2>&1)"
  if [ "$a" = "$b" ]; then
    printf '%-36s identical\n' "$f"; same=$((same + 1))
  else
    printf '%-36s DIFFERS\n' "$f"; diffn=$((diffn + 1))
    diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | sed 's/^/    /'
  fi
done
echo ""
echo "identical $same  ·  differs $diffn  ·  total $((same + diffn))"
```

`[1]` 은 무엇을 던지나? `[2]` 의 로그는 1번의 어느 줄과 같은가? 그 같음은 **「헬퍼의 성질」** 인가 **「무엇의 성질」** 인가?

### 11. 파이썬 · Rust · Kotlin 에서 같은 지연 파이프라인은 어디에 있나 (연결) ★★

Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **15번** · **16번** · **44번**,
Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **36번**,
Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **47번**과 견주어라.
**「기본이 즉시냐 지연이냐」** 와 **「언제 표준에 들어왔나」** 두 축으로. ★ JS 헬퍼에 없는 **갈래 복제**는 어느 쪽에 있나?

### 12. `Iterator.concat` 은 어느 판이고, 무엇을 받나 — 그리고 이 주제가 재지 않은 것 (경계) ★★

```js
// js20b-21i-concat.web.js
// Iterator.concat -- 판별 블록에서 Chrome 151 에 있다고 나온 것. 무엇을 받고 언제 여나를 로그로 찍는다.
const L = [];
const tracedIterable = (tag, vals) => ({
  [Symbol.iterator]() { L.push(tag + " @@iterator()"); let i = 0; return { next: () => (i < vals.length ? { value: vals[i++], done: false } : { value: undefined, done: true }) }; },
});
const t = (label, fn) => { let r; try { r = JSON.stringify(fn()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; } console.log("  " + label.padEnd(40) + r); };
console.log("[1] concat of two iterables");
L.length = 0;
const c = Iterator.concat(tracedIterable("A", [1, 2]), tracedIterable("B", [3]));
console.log("  after the call      log " + JSON.stringify(L));
console.log("  next()              " + JSON.stringify(c.next()) + "  log " + JSON.stringify(L));
console.log("  rest                " + JSON.stringify(c.toArray()) + "  log " + JSON.stringify(L));
console.log("");
console.log("[2] other arguments");
t("Iterator.concat([1], 'ab')", () => Iterator.concat([1], "ab").toArray());
t("Iterator.concat([1], { next() {} })", () => Iterator.concat([1], { next() {} }).toArray());
t("Iterator.concat([1], [2].values())", () => Iterator.concat([1], [2].values()).toArray());
```

`Iterator.concat` 이 ES2025 에 있나, ES2026 에 있나? 각 인자의 `Symbol.iterator` 는 **언제** 불리나?
그리고 「헬퍼는 메모리를 아낀다」 · 「헬퍼가 배열보다 빠르다」에 이 주제는 무엇을 근거로 답하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
