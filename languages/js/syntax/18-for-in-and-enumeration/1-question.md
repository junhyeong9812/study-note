# js/syntax/18 — `for...in` 과 열거: 「체인을 걷는 열거는 `for...in` 하나뿐이다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> **이 파일은 정답(출력)을 싣지 않는다** — 예측형 문항에는 소스만 있다.
>
> **환경** — node v20.19.6(nvm, 배너 `node20`) · 대조 v18.19.1(기본 PATH) · x86-64 Linux. 브라우저는 안 돌렸다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자(체인 순회 격자)다.**
> 프로퍼티 6종 × 「키를 늘어놓는 문법」 9열을 전부 대 보고 **체인 위 칸에 닿는 열이 몇 개인지** 센다.
> **1번 문항이 이 주제의 중심이고**, 5번이 보조 창(① 트랩 로그)으로 그 걷는 방식을 들여다본다.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **누가 체인까지 가나**(그리고 비열거·심볼은 누구에게 보이나)
> ② ★★★ **순서와 가리기**(13편의 세 덩어리가 체인 위에서 어떻게 이어지나 · 같은 이름이 두 칸에 있으면)
> ③ **가장자리에서 보장과 관찰 가르기**(배열 · `null` · 순회 중 변경).
>
> ★★★ **3번과 5번은 「무엇이 나오나」만 적으면 절반이다** — 줄마다 「**명세가 묶나, 이 판의 관찰인가**」를 같이 적어야 답이다.
> ★★ **예외는 타입과 메시지로만 답한다.** 그리고 **예외가 안 나는 자리**도 답이다.
> ★ **속도에 관한 답은 하나도 없다.** 「느리다」가 떠오르면 「**안 쟀다**」라고 적어라.
>
> **선행** — [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) ·
> [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) ·
> [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md).
> ★★★ **13편의 own 키 순서 세 덩어리를 먼저 떠올려라** — 1번의 `[2]` 와 8번의 답이 그 위에 선다.

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1\~5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 격자의 `o`/`.` 를 54칸 전부** 적어라. 그다음 「**상속 세 줄에 `o` 가 있는 열**」을 센다.
- ★★★ **3번은 행마다 세 칸**을 적어라 — 방문한 키 · 끝난 뒤 키 · **명세 보장 / 관찰**.
- ★★ **4번은 「던지나 안 던지나」를 먼저** 가른다. 던지면 타입까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여섯 종의 프로퍼티를 아홉 문법이 각각 보나 (예측) ★★★ 이 주제의 축

```js
// js16b-18a-grid.js
// ★★ 체인 순회 격자 -- 프로퍼티 종류 × 열거하는 문법. 누가 무엇을 보나를 전수로 찍는다.
// 13편의 격자는 own 키만 봤다. 여기서는 체인 위(상속된) 칸을 더한다.
const symOwn = Symbol("symOwn");
const symInh = Symbol("symInh");
const proto = { inheritedEnum: 1, [symInh]: 1 };
Object.defineProperty(proto, "inheritedHidden", { value: 1, enumerable: false });
const o = Object.create(proto);
o.ownEnum = 1;
o[symOwn] = 1;
Object.defineProperty(o, "ownHidden", { value: 1, enumerable: false });

const kinds = [
  ["own enumerable", "ownEnum"],
  ["own non-enumerable", "ownHidden"],
  ["own symbol", symOwn],
  ["inherited enumerable", "inheritedEnum"],
  ["inherited non-enumerable", "inheritedHidden"],
  ["inherited symbol", symInh],
];
const forIn = (x) => { const r = []; for (const k in x) r.push(k); return r; };
const views = [
  ["for-in", (x) => forIn(x)],
  ["keys", (x) => Object.keys(x)],
  ["entries", (x) => Object.entries(x).map(([k]) => k)],
  ["JSON", (x) => Object.keys(JSON.parse(JSON.stringify(x)))],
  ["{...}", (x) => Reflect.ownKeys({ ...x })],
  ["assign", (x) => Reflect.ownKeys(Object.assign({}, x))],
  ["gOPN", (x) => Object.getOwnPropertyNames(x)],
  ["ownKeys", (x) => Reflect.ownKeys(x)],
  ["in", (x) => kinds.map(([, k]) => k).filter((k) => k in x)],
];
console.log("[1] who sees what   (o = sees it, . = does not)");
console.log(("".padEnd(26) + views.map(([n]) => n.padEnd(9)).join("")).trimEnd());
const seen = views.map(([, f]) => f(o));
for (const [label, k] of kinds) {
  console.log((label.padEnd(26) + seen.map((s) => (s.includes(k) ? "o" : ".").padEnd(9)).join("")).trimEnd());
}
console.log(("seen".padEnd(26) + seen.map((s) => (s.length + "/6").padEnd(9)).join("")).trimEnd());
console.log("columns that reach the chain: " + JSON.stringify(views.filter((_, i) => seen[i].includes("inheritedEnum")).map(([n]) => n)));

console.log("");
console.log("[2] for-in order across two links");
const p2 = { b: 1, 2: 1, a: 1, 1: 1 };
const c2 = Object.create(p2);
c2.z = 1; c2[9] = 1; c2.y = 1; c2[3] = 1;
console.log("  Object.keys(parent)  " + JSON.stringify(Object.keys(p2)));
console.log("  Object.keys(child)   " + JSON.stringify(Object.keys(c2)));
console.log("  for-in child         " + JSON.stringify(forIn(c2)));

console.log("");
console.log("[3] own NON-enumerable key, parent enumerable key, same name");
const p3 = { shared: "from parent", other: "from parent" };
const c3 = Object.create(p3);
Object.defineProperty(c3, "shared", { value: "own, hidden", enumerable: false });
console.log("  for-in c3            " + JSON.stringify(forIn(c3)));
console.log("  'shared' in c3       " + ("shared" in c3) + "   c3.shared  " + c3.shared);

console.log("");
console.log("[4] trap log -- what for-in asks each link of the chain");
const L = [];
const tap = (name, t) => new Proxy(t, {
  ownKeys(t) { L.push(name + ".ownKeys"); return Reflect.ownKeys(t); },
  getOwnPropertyDescriptor(t, k) { L.push(name + ".gopd(" + String(k) + ")"); return Reflect.getOwnPropertyDescriptor(t, k); },
  getPrototypeOf(t) { L.push(name + ".getPrototypeOf"); return Reflect.getPrototypeOf(t); },
  get(t, k, r) { L.push(name + ".get(" + String(k) + ")"); return Reflect.get(t, k, r); },
});
const top = tap("P", { p: 1 });
const leaf = tap("C", Object.create(top, { c: { value: 1, enumerable: true } }));
L.length = 0; const got = forIn(leaf);
console.log("  for-in keys " + JSON.stringify(got));
console.log("  trap log    " + JSON.stringify(L));
L.length = 0; Object.keys(leaf);
console.log("  Object.keys trap log " + JSON.stringify(L));
```

- ★★★ `[1]` 의 **54칸**을 `o`/`.` 로 채워 보라. 열마다 `seen` 칸의 **N/6** 은 얼마인가?
- ★★★ `columns that reach the chain:` 줄에는 **무엇이 몇 개** 나오는가? 그중 **목록을 돌려주는 문법**은?
- ★★ **`{...}`·`assign` 열**과 **`for-in` 열**은 개수가 같은가? 같다면 **겹치는 칸**은 몇 개인가?
- ★★ **상속 심볼**은 열거 가능한가? 그런데 `for-in` 에 나오는가?
- ★★★ `[2]` 에서 `for-in child` 의 **여덟 키 순서**를 적어라. 부모의 `"1"`·`"2"` 는 자식의 `"z"`·`"y"` 앞인가 뒤인가?
- ★★★ `[3]` 에서 `for-in c3` 은 무엇인가? `'shared' in c3` 와 `c3.shared` 는?
- ★★ `[4]` 의 `for-in` 트랩 로그에 **`get` 이 몇 줄** 있는가? `Object.keys` 트랩 로그에 **`getPrototypeOf`** 는 있는가?

### 2. 배열을 `for...in` 으로 돌리면 (예측) ★★★

```js
// js16b-18b-array.js
// 배열에 for-in 을 쓰면 무엇이 나오나.
const forIn = (x) => { const r = []; for (const k in x) r.push(k); return r; };
const arr = ["a", "b", , "d"];
const show = (v) => (v === undefined ? "<undefined>" : v);

console.log("[1] what are the keys?");
for (const i in arr) { console.log("  i=" + JSON.stringify(i) + "  typeof " + typeof i + "  i + 1 = " + JSON.stringify(i + 1)); }
console.log("  for-of values  " + JSON.stringify([...arr].map(show)) + "   <- the hole at 2 is visited by for-of, skipped by for-in");

console.log("");
console.log("[2] an extra property and a prototype extension");
arr.extra = "attached";
Array.prototype.polluted = function () {};
console.log("  for-in arr          " + JSON.stringify(forIn(arr)));
console.log("  for-in []           " + JSON.stringify(forIn([])));
console.log("  for-of arr          " + JSON.stringify([...arr].map(show)));
console.log("  Object.keys(arr)    " + JSON.stringify(Object.keys(arr)));
const guarded = []; for (const k in arr) if (Object.hasOwn(arr, k)) guarded.push(k);
console.log("  for-in + hasOwn     " + JSON.stringify(guarded));
delete Array.prototype.polluted;

console.log("");
console.log("[3] the same extension, defined non-enumerable");
Object.defineProperty(Array.prototype, "quiet", { value: function () {}, enumerable: false, configurable: true, writable: true });
console.log("  for-in arr          " + JSON.stringify(forIn(arr)));
console.log("  typeof arr.quiet    " + typeof arr.quiet);
delete Array.prototype.quiet;

console.log("");
console.log("[4] built-in methods and length");
console.log("  'map' in arr        " + ("map" in arr) + "   enumerable? " + Object.getOwnPropertyDescriptor(Array.prototype, "map").enumerable);
console.log("  'length' in arr     " + ("length" in arr) + "   enumerable? " + Object.getOwnPropertyDescriptor(arr, "length").enumerable);
```

- ★★★ `[1]` 에서 `i` 의 **`typeof`** 와 `i + 1` 은 각각 무엇인가? **구멍(2번 자리)은 몇 줄** 찍히는가?
- ★★ 같은 배열을 `for-of` 로 펼치면 2번 자리에 무엇이 오는가?
- ★★★ `[2]` 의 `for-in arr` 와 **`for-in []`** 는 각각 무엇인가?
- ★★ `Object.keys(arr)` 와 **`for-in + hasOwn`** 은 같은가? `hasOwn` 가드가 **못 거르는 키**가 있는가?
- ★★ `[3]` 에서 확장을 비열거로 정의하면 `for-in arr` 는? 그런데 `typeof arr.quiet` 는?
- ★ `[4]` 의 `map`·`length` 는 `in` 으로 **있는가**? **열거 가능한가**?

### 3. 순회 도중 지우거나 더하면 (예측) ★★★

```js
// js16b-18d-mutate.js
// 순회 도중 프로퍼티를 지우거나 더하면 -- 명세가 보장하는 행과 이 판의 관찰일 뿐인 행을 본문에서 가른다.
const trial = (label, setup, onKey) => {
  const o = setup();
  const visited = [];
  for (const k in o) { visited.push(k); onKey(o, k); }
  console.log(label.padEnd(44) + "visited " + JSON.stringify(visited).padEnd(26) + "keys after " + JSON.stringify(Object.keys(o)));
};

console.log("[1] deleting during for-in");
trial("delete a not-yet-visited key (c) at a", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { if (k === "a") delete o.c; });
trial("delete the current key at each step", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { delete o[k]; });
trial("delete a parent key (p) before it comes", () => { const o = Object.create({ p: 1 }); o.a = 1; return o; },
      (o, k) => { if (k === "a") delete Object.getPrototypeOf(o).p; });

console.log("");
console.log("[2] adding during for-in");
trial("add a new own key (z) at a", () => ({ a: 1, b: 2 }), (o, k) => { if (k === "a") o.z = 26; });
trial("add a new integer key (0) at a", () => ({ a: 1, b: 2 }), (o, k) => { if (k === "a") o[0] = 0; });
trial("add a parent key (q) at a", () => { const o = Object.create({}); o.a = 1; o.b = 2; return o; },
      (o, k) => { if (k === "a") Object.getPrototypeOf(o).q = 1; });
trial("delete then re-add b at a", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { if (k === "a") { delete o.b; o.b = 2; } });

console.log("");
console.log("[3] the same delete, with Object.keys(...).forEach");
const snap = { a: 1, b: 2, c: 3 };
const seenVals = [];
Object.keys(snap).forEach((k, i) => { if (i === 0) delete snap.c; seenVals.push(k + "=" + snap[k]); });
console.log("Object.keys(snap).forEach, delete c at a    " + JSON.stringify(seenVals));
```

- ★★★ `[1]` 세 행의 **`visited`** 와 **`keys after`** 를 적어라.
- ★★★ `[2]` 네 행의 **`visited`** 와 **`keys after`** 를 적어라. 특히 **정수 키 `0`** 을 더한 행과 **지웠다 다시 넣은 `b`** 행.
- ★★★ 일곱 행 각각이 **명세가 묶은 결과**인가 **이 판의 관찰**인가? 근거 문장(또는 제약)을 대라.
- ★★ **윗칸의 `p` 를 지운 행**은 어느 칸인가? 명세 문장이 **무엇에 대해** 말하고 있는지를 따져 보라.
- ★★★ `[3]` 에서 `Object.keys(snap).forEach` 는 지운 `c` 를 **방문하는가**? 방문한다면 값은?

### 4. `hasOwnProperty` 세 객체와 `for...in` 에 넘긴 이상한 값 (예측) ★★★

```js
// js16b-18c-hasown.js
// hasOwnProperty 대 Object.hasOwn(ES2022) -- 그리고 for-in 이 받는 이상한 값들.
const run = (label, fn) => {
  let r;
  try { r = "-> " + String(fn()); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(66) + r);
};
const forIn = (x) => { const r = []; for (const k in x) r.push(k); return JSON.stringify(r); };

console.log("[1] three unusual objects, three ways to ask own-ness");
const bare = Object.create(null); bare.k = 1;
const liar = { k: 1, hasOwnProperty() { return false; } };
const shadowed = { k: 1, hasOwnProperty: 42 };
for (const [name, o] of [["Object.create(null)", bare], ["own hasOwnProperty() {return false}", liar], ["own hasOwnProperty: 42", shadowed]]) {
  run(name + "  o.hasOwnProperty('k')", () => o.hasOwnProperty("k"));
  run(name + "  Object.hasOwn(o, 'k')", () => Object.hasOwn(o, "k"));
  run(name + "  Object.prototype.hasOwnProperty.call", () => Object.prototype.hasOwnProperty.call(o, "k"));
}

console.log("");
console.log("[2] for-in over Object.create(null)");
const bare2 = Object.create(null); bare2.x = 1; bare2.y = 2;
run("for-in bare2", () => forIn(bare2));

console.log("");
console.log("[3] a symbol key and for-in");
const withSym = { visible: 1, [Symbol("hidden")]: 2 };
run("for-in withSym", () => forIn(withSym));
run("Object.getOwnPropertySymbols(withSym).length", () => Object.getOwnPropertySymbols(withSym).length);

console.log("");
console.log("[4] for-in over primitives, null and undefined");
run("for-in 'ab'", () => forIn("ab"));
run("for-in 42", () => forIn(42));
run("for-in true", () => forIn(true));
run("for-in null", () => forIn(null));
run("for-in undefined", () => forIn(undefined));
run("Object.keys(null)  (for contrast)", () => Object.keys(null));
```

- ★★★ `[1]` **아홉 줄** 각각이 값인가 예외인가? 예외라면 **타입**은?
- ★★ **자기 `hasOwnProperty()` 를 가진 객체**에서 `o.hasOwnProperty('k')` 는 무엇을 답하는가? 그것은 참인가?
- ★★ `[2]` `Object.create(null)` 에 `for-in` 은 **되는가**?
- ★★★ `[4]` 에서 **던지는 줄은 몇 개**인가? `for-in null` 과 `Object.keys(null)` 은 각각 무엇인가?
- ★ `for-in 'ab'` 과 `for-in 42` 는?

### 5. 명세 알고리즘을 손으로 옮겨 V8 과 나란히 돌리면 (예측) ★★

```js
// js16b-18f-refimpl.js
// 명세의 CreateForInIterator 알고리즘(%ForInIteratorPrototype%.next 의 단계)을 손으로 옮긴 생성기로
// 같은 두 칸 Proxy 체인을 걸어 본다 -- 18a [4] 의 V8 로그와 나란히 놓기 위한 것이다.
// ★ 이 생성기는 명세의 참고 코드를 옮긴 것이 아니라 알고리즘 단계를 이 문서가 직접 JS 로 적은 것이다(검증 대상이지 정본이 아니다).
const L = [];
const tap = (name, t) => new Proxy(t, {
  ownKeys(t) { L.push(name + ".ownKeys"); return Reflect.ownKeys(t); },
  getOwnPropertyDescriptor(t, k) { L.push(name + ".gopd(" + String(k) + ")"); return Reflect.getOwnPropertyDescriptor(t, k); },
  getPrototypeOf(t) { L.push(name + ".getPrototypeOf"); return Reflect.getPrototypeOf(t); },
  get(t, k, r) { L.push(name + ".get(" + String(k) + ")"); return Reflect.get(t, k, r); },
});
function* specForIn(start) {
  let obj = start;
  const visited = [];
  while (obj !== null) {
    const remaining = Reflect.ownKeys(obj).filter((k) => typeof k === "string");
    for (const key of remaining) {
      if (visited.includes(key)) continue;
      const desc = Reflect.getOwnPropertyDescriptor(obj, key);
      if (desc !== undefined) {
        visited.push(key);
        if (desc.enumerable) yield key;
      }
    }
    obj = Reflect.getPrototypeOf(obj);
  }
}
const top = tap("P", { p: 1 });
const leaf = tap("C", Object.create(top, { c: { value: 1, enumerable: true } }));

console.log("[1] the same two-link Proxy chain, walked two ways");
L.length = 0; const a = [...specForIn(leaf)]; const logA = L.slice();
console.log("spec algorithm keys  " + JSON.stringify(a));
console.log("spec algorithm log   " + JSON.stringify(logA) + "  (" + logA.length + " entries)");
L.length = 0; const b = []; for (const k in leaf) b.push(k); const logB = L.slice();
console.log("V8 for-in keys       " + JSON.stringify(b));
console.log("V8 for-in log        " + JSON.stringify(logB) + "  (" + logB.length + " entries)");
console.log("same keys? " + (JSON.stringify(a) === JSON.stringify(b)) + "   same log? " + (JSON.stringify(logA) === JSON.stringify(logB)));

console.log("");
console.log("[2] the 18d mutation rows, walked by the hand-ported spec algorithm and by V8's for-in");
const rows = [
  ["delete a not-yet-visited key (c) at a", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { if (k === "a") delete o.c; }],
  ["delete the current key at each step", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { delete o[k]; }],
  ["delete a parent key (p) before it comes", () => { const o = Object.create({ p: 1 }); o.a = 1; return o; },
   (o, k) => { if (k === "a") delete Object.getPrototypeOf(o).p; }],
  ["add a new own key (z) at a", () => ({ a: 1, b: 2 }), (o, k) => { if (k === "a") o.z = 26; }],
  ["add a new integer key (0) at a", () => ({ a: 1, b: 2 }), (o, k) => { if (k === "a") o[0] = 0; }],
  ["add a parent key (q) at a", () => { const o = Object.create({}); o.a = 1; o.b = 2; return o; },
   (o, k) => { if (k === "a") Object.getPrototypeOf(o).q = 1; }],
  ["delete then re-add b at a", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { if (k === "a") { delete o.b; o.b = 2; } }],
];
for (const [label, setup, onKey] of rows) {
  const o1 = setup(); const s = []; for (const k of specForIn(o1)) { s.push(k); onKey(o1, k); }
  const o2 = setup(); const v = []; for (const k in o2) { v.push(k); onKey(o2, k); }
  console.log(label.padEnd(42) + "spec " + JSON.stringify(s).padEnd(18) + "V8 " + JSON.stringify(v).padEnd(18) +
    (JSON.stringify(s) === JSON.stringify(v) ? "same" : "DIFFERENT"));
}
```

- ★★ `[1]` 두 방식의 **키 목록**은 같은가? **트랩 로그 줄 수**는 각각 몇인가?
- ★★★ 두 로그의 **모양**은 어떻게 다른가 — 어느 쪽이 「칸마다 끝내고 올라가고」, 어느 쪽이 「먼저 끝까지 모으는」가?
- ★★★ 로그가 다른데 **둘 다 적법**할 수 있는가? 어느 명세 문장 때문인가?
- ★★★ `[2]` 일곱 행 중 **`DIFFERENT`** 는 몇 행이고 어느 행인가? 그 행이 3번에서 **어느 칸**이었는지와 맞춰 보라.

### 6. own 비열거가 부모의 같은 이름을 가리는 이유 (왜) ★★★

- ★★★ 명세의 어느 문장이 이것을 정하는가? 그 문장이 **판정에서 빼는 것**은 무엇인가?
- ★★ 「처리했다」와 「내놓았다」는 어떻게 다른가? own 비열거 키는 어느 쪽인가?
- ★★ 같은 키가 **조회**에서는 보인다. 열거와 조회가 갈리는 이유를 15편과 이어 설명하라.

### 7. 명세가 「순회 중 추가」를 끝내 보장하지 않는 이유 (왜) ★★★

- ★★★ 순회 중 변경에 관한 명세 문장은 **두 겹**이다. 각 겹이 **어느 객체에** 걸리고 **무엇을** 묶는가?
- ★★★ 둘째 겹의 제약을 **푸는 사건 넷**은? 그 목록에 **빠진 것** 하나가 3번의 두 행을 묶는다 — 무엇인가?
- ★★ 명세의 노트는 제약 예외 목록을 **왜 그렇게 골랐다**고 적는가?
- ★ 그렇다면 순회 중 구조를 바꿔야 할 때 **무엇을 먼저** 하나?

### 8. 13편의 세 덩어리 순서는 체인 위에서 어떻게 이어지나 (연결) ★★

- ★★★ 세 덩어리는 **체인 전체에** 걸리는가, **칸마다** 걸리는가? 1번 `[2]` 의 어느 두 키가 그 증거인가?
- ★★ 13편이 인용한 판 경계 둘 — **`Object.keys` 순서**와 **`for...in` 순서** — 는 각각 어느 판인가?
- ★ `for...in` 순서의 보장에는 **조건**이 붙는다. 무엇인가?

### 9. 클래스 메서드는 왜 `for...in` 에 안 나오나 (연결) ★★

- ★★★ 16편이 찍은 표에서 **비열거인 멤버**와 **열거 가능인 멤버**를 갈라 보라.
- ★★ 생성자 함수 + `Old.prototype.method = function` 을 `class` 로 옮기면 인스턴스의 `for...in` 결과가 **어떻게 바뀌는가**? 그것은 실측인가 추론인가?
- ★ 프로토타입에 무언가 붙여야 할 때 **`for...in` 을 안 바꾸는 방법**은?

### 10. 배열에는 `for...in` 대신 무엇을 쓰나 (경계) ★★

- ★★★ `for...in` 과 `for...of` 는 **무엇을 도는가**가 다르다. 각각 한 마디로?
- ★★ **구멍**에서 둘이 어떻게 갈리는가? 구멍은 「값이 `undefined` 인 칸」과 같은가?
- ★★ `hasOwn` 가드로 배열 `for-in` 이 **고쳐지는가**? 무엇이 남는가?
- ★ `for...of` 의 규칙은 **어느 주제**가 정본인가?

### 11. 보장인가 엔진 사정인가 — 창 가르기 (연결) ★★★

- 이 주제에서 **두 판이 갈린 블록**은 몇 개였는가?
- ★★★ **명세 보장**과 **V8 관찰**을 각각 셋씩 대라. 트랩 로그의 **종류**와 **순서**는 각각 어느 쪽인가?
- ★★ 이 주제에서 **부적용인 창** 둘과 **안 돌린 창** 둘은? 「부적용」과 「안 돌렸다」는 어떻게 다른가?
- ★★★ 「`for...in` 은 느리다」에 대해 이 문서는 무엇이라고 적는가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **own 키 순서 세 덩어리** · **`enumerable` 플래그 바꾸기** · **조회가 체인을 타는 규칙** · **`for...of`** ·
  **`Object.keys`/`assign` 의 쓰임** · **`Proxy` 트랩 계약** 은 각각 어느 주제가 정본인가?
- ★★★ 15편이 책임진 것과 **이 주제가 더한 것 하나**는?
- ★ 이 주제가 **끝까지 책임지는 것** 셋을 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
