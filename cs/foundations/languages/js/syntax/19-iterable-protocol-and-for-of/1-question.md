# js/syntax/19 — 이터러블 프로토콜과 `for...of`: 「소비자는 전부 같은 계약을 부르고, 다 못 읽으면 `return()` 으로 닫는다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · x86-64 Linux. 브라우저는 **안 돌렸다.**
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> 소비자가 `Symbol.iterator`·`next`·`return` 을 **몇 번, 언제** 부르는지는 결과 값에 흔적이 없다 — **값으로는 원리상 못 가른다.**
> 그래서 그 세 자리에 로그를 심은 이터러블 하나로 소비자 17가지를 돌렸다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`return()` 이 언제 불리나**(그리고 언제 **안** 불리나)
> ② **이터러블과 이터레이터의 차이**(두 번 돌면 갈린다)
> ③ **이터러블이 아닐 때 무엇이 터지나**(그리고 대체 경로가 있나).
>
> ★★★ **답을 적을 때 「값」만 적으면 절반도 못 맞힌 것이다.** 1번은 줄마다 **`next` 횟수와 `return` 여부**를, 5번은 **누구의 예외가 올라오나**를 같이 적어야 답이다.
> ★★ **예외는 타입과 메시지로만 답한다.** ★ **메시지는 판마다 다를 수 있다** — 9번이 그 자리를 묻는다.
>
> **선행** — [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md)(★★★ 직접 선행) · [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) ·
> [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) · [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md).
> ★★★ **11번의 트랩 로그를 먼저 떠올려라** — `[...tracedIterable(2)]` 가 무엇을 몇 번 불렀나.

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1\~5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「무엇이 나오나」가 아니라 「무엇이 몇 번 불리나」를 묻는다.** 줄마다 로그를 먼저 적어라.
- ★★ **3번은 「터지는 것」과 「조용히 되는 것」을 갈라서** 적어라. 터지면 문구까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「느리다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 소비자 17가지는 세 메서드를 각각 몇 번 부르나 (예측) ★★★ 이 주제의 축

```js
// js16b-19a-protocol-log.js
// ★★★ 이 주제의 본체 -- 소비자마다 Symbol.iterator · next · return 이 「언제 몇 번」 불리나를 로그로 찍는다.
// 이터러블은 값 3개(10, 20, 30)를 내놓는다.
const L = [];
function traced(n = 3, opts = {}) {
  return {
    get [Symbol.iterator]() {
      L.push("get @@iterator");
      return function () {
        L.push("@@iterator()");
        let i = 0;
        return {
          next() {
            i++;
            if (opts.throwAt === i) { L.push("next#" + i + " throws"); throw new Error("next failed"); }
            const done = i > n;
            L.push("next#" + i + (done ? " done" : " -> " + i * 10));
            return done ? { value: undefined, done: true } : { value: i * 10, done: false };
          },
          return() { L.push("return()"); return {}; },
        };
      };
    },
  };
}
const count = (name) => L.filter((m) => m.startsWith(name)).length;
const rows = [];
function probe(label, fn) {
  L.length = 0;
  let r;
  try { r = fn(); r = r === undefined ? "" : "result " + JSON.stringify(r, (k, v) => (v === undefined ? "<undefined>" : v)); } catch (e) { r = "caught " + e.constructor.name + " " + e.message; }
  rows.push([label, count("next#"), count("return()")]);
  console.log(label);
  console.log("    " + L.join(" | ") + (r ? "   [" + r + "]" : ""));
}

console.log("[1] consumers that read to the end");
probe("for (const x of it) {}", () => { for (const x of traced()) {} });
probe("[...it]", () => [...traced()]);
probe("Array.from(it)", () => Array.from(traced()));
probe("new Set(it)", () => [...new Set(traced())]);
probe("const [a, ...rest] = it", () => { const [a, ...rest] = traced(); return [a, rest]; });
probe("Math.max(...it)", () => Math.max(...traced()));

console.log("");
console.log("[2] consumers that stop early");
probe("for-of with break at 20", () => { for (const x of traced()) if (x === 20) break; });
probe("for-of with return at 20", () => (() => { for (const x of traced()) if (x === 20) return x; })());
probe("for-of whose body throws at 20", () => { for (const x of traced()) if (x === 20) throw new Error("body threw"); });
probe("labelled continue outer, from inside", () => { outer: for (const y of [1]) { for (const x of traced()) continue outer; } });
probe("const [a] = it", () => { const [a] = traced(); return a; });
probe("const [a, b, c] = it  (exactly 3)", () => { const [a, b, c] = traced(); return [a, b, c]; });
probe("const [a, b, c, d] = it  (one more)", () => { const [a, b, c, d] = traced(); return [a, b, c, d]; });
probe("Array.from(it, mapFn throws at 20)", () => Array.from(traced(), (x) => { if (x === 20) throw new Error("map threw"); return x; }));
probe("new Map(it)  (10 is not an entry)", () => new Map(traced()));

console.log("");
console.log("[3] when next() itself throws");
probe("for-of, next#2 throws", () => { for (const x of traced(3, { throwAt: 2 })) {} });
probe("[...it], next#2 throws", () => [...traced(3, { throwAt: 2 })]);

console.log("");
console.log("[4] Promise.all -- when does it read the iterable?");
L.length = 0;
const pending = Promise.all(traced());
console.log("Promise.all(it)   right after the call:  " + L.join(" | "));
pending.then((v) => {
  console.log("                  resolved with " + JSON.stringify(v));
  console.log("");
  console.log("[5] summary  (label / next calls / return calls)");
  for (const [label, n, r] of rows) console.log("  " + label.padEnd(40) + String(n).padStart(2) + "  " + r);
  console.log("return() was called in " + rows.filter(([, , r]) => r > 0).length + " of " + rows.length + " probes");
});
```

- ★★★ `[1]`·`[2]`·`[3]` 의 **줄마다** `next` 가 몇 번 불리고 `return()` 이 불리는지 적어라.
- ★★★ 특히 **`const [a, b, c] = it`(값이 딱 셋)** 과 **`const [a, b, c, d] = it`** 두 줄을 갈라서.
- ★★ `new Map(it)` 과 `Array.from(it, mapFn)` 줄은 **무엇으로 끝나나**?
- ★★ `[4]` — `Promise.all(it)` 이 **돌아온 바로 다음 줄**에 로그는 어디까지 차 있나?
- ★ `get @@iterator` 는 한 소비자당 몇 번 찍히나?

### 2. 같은 것을 두 번 펴면 (예측) ★★★

```js
// js16b-19b-make-your-own.js
// 이터러블을 직접 만든다 -- 그리고 「이터러블」과 「이터레이터」가 다른 물건인 자리를 찍는다.
const row = (label, v) => console.log(label.padEnd(46) + v);

console.log("[1] a class with [Symbol.iterator]()");
class Countdown {
  constructor(from) { this.from = from; }
  [Symbol.iterator]() {
    let n = this.from;
    return { next: () => (n > 0 ? { value: n--, done: false } : { value: undefined, done: true }) };
  }
}
const cd = new Countdown(3);
row("[...cd]  first time", JSON.stringify([...cd]));
row("[...cd]  second time", JSON.stringify([...cd]));

console.log("");
console.log("[2] an iterator whose [Symbol.iterator]() returns itself");
const once = cd[Symbol.iterator]();
once[Symbol.iterator] = function () { return this; };
row("[...once]  first time", JSON.stringify([...once]));
row("[...once]  second time", JSON.stringify([...once]));

console.log("");
console.log("[3] generators and built-in iterators");
function* gen() { yield 1; yield 2; }
const g = gen();
row("g[Symbol.iterator]() === g", g[Symbol.iterator]() === g);
row("[...g] then [...g]", JSON.stringify([...g]) + " then " + JSON.stringify([...g]));
const ai = [1, 2][Symbol.iterator]();
row("arrayIterator[Symbol.iterator]() === itself", ai[Symbol.iterator]() === ai);
row("[...ai] then [...ai]", JSON.stringify([...ai]) + " then " + JSON.stringify([...ai]));
const m = new Map([["k", 1]]);
row("[...m.keys()] twice from ONE keys() call", (() => { const k = m.keys(); return JSON.stringify([...k]) + " then " + JSON.stringify([...k]); })());
row("gen[Symbol.iterator]  (the function itself)", typeof gen[Symbol.iterator]);

console.log("");
console.log("[4] the value that comes with done: true");
function* withReturn() { yield "a"; return "the return value"; }
row("[...withReturn()]", JSON.stringify([...withReturn()]));
const seen = []; for (const x of withReturn()) seen.push(x);
row("for-of withReturn()", JSON.stringify(seen));
const it = withReturn();
row("manual next() x2", JSON.stringify(it.next()) + " " + JSON.stringify(it.next()));

console.log("");
console.log("[5] a result object without `done`");
let calls = 0;
const noDone = { [Symbol.iterator]() { return { next() { calls++; return calls > 3 ? { done: true } : { value: calls }; } }; } };
row("[...noDone]", JSON.stringify([...noDone]));
```

- ★★★ `[1]` 과 `[2]` 의 **두 번째 줄**은 각각 무엇인가?
- ★★ `[3]` 의 세 가지(제너레이터 객체 · 배열 이터레이터 · `m.keys()`)는 어느 쪽인가? `typeof gen[Symbol.iterator]` 는?
- ★★★ `[4]` — `"the return value"` 는 **어느 줄에** 보이나?
- ★ `[5]` — `done` 이 없는 결과 객체를 주면 스프레드는 무엇을 모으나?

### 3. 이터러블이 아닌 것을 들이대면 (예측) ★★★

```js
// js16b-19c-errors.js
// 이터러블이 아닌 것을 들이대면 -- 문마다 에러 문구가 같은가. 유사 배열에 대체 경로가 있나.
const run = (label, fn) => {
  let r;
  try { r = "-> " + fn(); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(44) + r);
};
const J = (v) => JSON.stringify(v);
const plain = { a: 1 };
const arrayLike = { length: 2, 0: "x", 1: "y" };
const id = (...xs) => xs;

console.log("[1] a plain object in six places");
run("for (const v of plain)", () => { for (const v of plain) {} return "ok"; });
run("[...plain]", () => J([...plain]));
run("id(...plain)", () => J(id(...plain)));
run("const [v] = plain", () => { const [v] = plain; return J(v); });
run("new Set(plain)", () => J([...new Set(plain)]));
run("Array.from(plain)", () => J(Array.from(plain)));

console.log("");
console.log("[2] an array-like { length: 2, 0: 'x', 1: 'y' } -- is there a fallback?");
run("for (const v of arrayLike)", () => { const r = []; for (const v of arrayLike) r.push(v); return J(r); });
run("[...arrayLike]", () => J([...arrayLike]));
run("Array.from(arrayLike)", () => J(Array.from(arrayLike)));
run("Array.prototype.slice.call(arrayLike)", () => J(Array.prototype.slice.call(arrayLike)));
run("id.apply(null, arrayLike)", () => J(id.apply(null, arrayLike)));
arrayLike[Symbol.iterator] = Array.prototype[Symbol.iterator];
run("after borrowing Array's @@iterator: [...]", () => J([...arrayLike]));

console.log("");
console.log("[3] null and undefined");
run("for (const v of null)", () => { for (const v of null) {} return "ok"; });
run("for (const v of undefined)", () => { for (const v of undefined) {} return "ok"; });
run("[...undefined]", () => J([...undefined]));

console.log("");
console.log("[4] a broken protocol -- each step checks its own contract");
run("@@iterator is not a function", () => J([...{ [Symbol.iterator]: 1 }]));
run("@@iterator returns a primitive", () => J([...{ [Symbol.iterator]() { return 1; } }]));
run("next() returns a primitive", () => J([...{ [Symbol.iterator]() { return { next() { return 1; } }; } }]));
run("iterator has no next", () => J([...{ [Symbol.iterator]() { return {}; } }]));
run("return() returns a primitive (on break)", () => {
  const it = { [Symbol.iterator]() { return { next: () => ({ value: 1, done: false }), return: () => 1 }; } };
  for (const v of it) break;
  return "ok";
});
```

- ★★★ `[1]` 여섯 줄 — **터지는 줄과 안 터지는 줄**을 가르고, 터지는 줄은 **문구가 몇 가지**인지 세라.
- ★★★ `[2]` — 유사 배열에 **무엇이 되고 무엇이 안 되나**? 마지막 줄(빌려 붙인 뒤)은?
- ★★ `[3]` — `for (const v of null)` 은?
- ★★ `[4]` — 다섯 줄의 문구. **같은 문구가 두 번 나오는 쌍**이 있다면 무엇인가?

### 4. 문자열 길이 둘과 `Map` 의 키 순서 (예측) ★★

```js
// js16b-19d-strings-maps.js
// 내장 이터러블 둘 -- 문자열은 「무엇 단위로」 도나, Map·Set 은 「어떤 순서로」 도나.
const row = (label, v) => console.log(label.padEnd(44) + v);
const hex = (c) => c.codePointAt(0).toString(16).toUpperCase();

console.log("[1] a string with one astral character (built from a code point, so this file stays ASCII)");
const s = "a" + String.fromCodePoint(0x1f600) + "b";
row("s.length  (UTF-16 code units)", s.length);
row("[...s].length  (for-of units)", [...s].length);
row("[...s] as code points", JSON.stringify([...s].map(hex)));
row("s.split('') as code units", JSON.stringify(s.split("").map((c) => c.charCodeAt(0).toString(16).toUpperCase())));
const units = []; for (let i = 0; i < s.length; i++) units.push(s[i].length);
row("for (let i...) s[i].length each", JSON.stringify(units));
const cps = []; for (const ch of s) cps.push(ch.length);
row("for (const ch of s) ch.length each", JSON.stringify(cps));

console.log("");
console.log("[2] Map and Set order, with integer-like keys");
const m = new Map([["b", 1], [2, 1], ["a", 1], [1, 1]]);
const obj = { b: 1, 2: 1, a: 1, 1: 1 };
row("[...map.keys()]", JSON.stringify([...m.keys()]));
row("Object.keys(same keys as an object)", JSON.stringify(Object.keys(obj)));
m.delete("b"); m.set("b", 1);
row("after delete b, set b  -> keys", JSON.stringify([...m.keys()]));
m.set(2, "overwritten");
row("after set(2, ...) again -> keys", JSON.stringify([...m.keys()]));
const st = new Set(["z", 3, "y", 1]);
row("[...set]", JSON.stringify([...st]));

console.log("");
console.log("[3] changing a Map / Set / Array during for-of");
const live = new Set([1, 2]);
const visited = [];
for (const v of live) { visited.push(v); if (v === 1) live.add(3); if (v === 2) live.delete(1); }
row("add 3 at 1, delete 1 at 2", "visited " + JSON.stringify(visited) + "   final " + JSON.stringify([...live]));
const lm = new Map([["a", 1], ["b", 2]]);
const lv = [];
for (const [k] of lm) { lv.push(k); if (k === "a") lm.delete("b"); }
row("Map: delete b at a", "visited " + JSON.stringify(lv));
const arr = [1, 2];
const av = [];
for (const v of arr) { av.push(v); if (v === 1) arr.push(3); }
row("Array: push 3 at 1", "visited " + JSON.stringify(av));
```

- ★★★ `s.length` 와 `[...s].length` 는 각각 얼마인가? 줄마다 `ch.length` 는?
- ★★★ `[...map.keys()]` 와 `Object.keys(obj)` — **같은 키를 넣었는데** 순서가 같은가?
- ★★ `delete` 뒤 다시 `set` 한 키, 이미 있는 키에 `set` 한 뒤의 순서는?
- ★★ `[3]` — 도는 중에 넣은 값과 지운 키는 방문되나? 배열의 `push` 는?

### 5. `return()` 이 없을 때 · 틀렸을 때 · 몸통이 먼저 던졌을 때 (예측) ★★

```js
// js16b-19f-close-and-helpers.js
// return() 쪽 계약을 더 찍는다 -- 그리고 이터레이터 헬퍼(ES2025)가 이 두 판에 있나를 묻는다.
const run = (label, fn) => {
  let r;
  try { r = "-> " + fn(); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(48) + r);
};
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
function closer(ret) {
  return { [Symbol.iterator]() { return { next: () => ({ value: 1, done: false }), return: ret }; } };
}

console.log("[1] what return() may be -- on a break");
run("no return at all", () => { for (const v of closer(undefined)) break; return "ok"; });
run("return: 1  (not callable)", () => { for (const v of closer(1)) break; return "ok"; });
run("return() throws", () => { for (const v of closer(() => { throw new Error("from return"); })) break; return "ok"; });

console.log("");
console.log("[2] when the body already threw, whose error wins?");
run("body throws, return() throws too", () => { for (const v of closer(() => { throw new Error("from return"); })) throw new Error("from body"); });
run("body throws, return() gives a primitive", () => { for (const v of closer(() => 1)) throw new Error("from body"); });

console.log("");
console.log("[3] the value that comes with done: true -- three more consumers");
function* withReturn() { yield "a"; return "R"; }
run("Array.from(withReturn())", () => J(Array.from(withReturn())));
run("const [x, y] = withReturn()", () => { const [x, y] = withReturn(); return J([x, y]); });
run("new Set(withReturn()).size", () => new Set(withReturn()).size);

console.log("");
console.log("[4] iterator helpers (ES2025) -- present in this node?");
run("typeof globalThis.Iterator", () => typeof globalThis.Iterator);
run("typeof [].values().map", () => typeof [].values().map);
run("typeof [].values().toArray", () => typeof [].values().toArray);

console.log("");
console.log("[5] arguments -- array-like; is it also iterable?");
run("typeof arguments[Symbol.iterator]", function () { return typeof arguments[Symbol.iterator]; });
run("[...arguments]  (called with 1, 2)", () => (function () { return J([...arguments]); })(1, 2));

console.log("");
console.log("[6] an endless iterator -- does const [a] stop after one value?");
let nexts = 0, closes = 0;
const endless = { [Symbol.iterator]() { return { next: () => ({ value: ++nexts, done: false }), return: () => { closes++; return {}; } }; } };
run("const [a] = endless", () => { const [a] = endless; return J({ a, nexts, closes }); });

console.log("");
console.log("[7] e followed by a combining mark (U+0301)");
const e = "e" + String.fromCodePoint(0x301);
run("e + U+0301  .length / [...].length", () => e.length + " / " + [...e].length);
```

- ★★★ `[1]` 세 줄과 `[2]` 두 줄 — **누구의 예외가 올라오나**? 아무것도 안 올라오는 줄은?
- ★★ `[3]` — 세 소비자가 `"R"` 을 보나?
- ★★ `[4]` — 이 두 판에 이터레이터 헬퍼가 있나?
- ★★ `[5]`·`[6]`·`[7]` — `arguments` 는 펴지나? 끝없는 이터레이터에 `const [a]` 는 멈추나? 결합 문자를 붙인 `e` 의 두 길이는?

### 6. `[a, b, c]` 는 값이 딱 셋인데 왜 `return()` 을 부르나 (왜) ★★★

- ★★★ 소비자 쪽에서 보면 **셋째 값을 받은 순간 무엇을 모르나**?
- ★★ `[a, b, c, d]` 가 **안 닫는** 이유와 한 문장으로 묶어라.
- ★ 그 규칙이 **끝없는 이터레이터**에서는 무엇을 가능하게 하나?

### 7. `next()` 가 던지면 왜 `return()` 을 안 부르나 (왜) ★★★

- ★★★ 「닫기」는 **누구에게 무엇을 알리는 일**인가? 그 상대가 고장 났다면?
- ★★ 명세에서 그 차이는 **어느 기호 하나**로 드러나나?
- ★ 정리 코드를 `return()` 에만 두면 **어느 경로**에서 새나?

### 8. `done: true` 와 함께 온 값은 왜 아무도 안 쓰나 (왜) ★★

- ★★ 소비자는 결과 객체의 **무엇을 먼저 읽고**, 그것이 참이면 **무엇을 안 읽나**?
- ★★ 그 값을 **보려면** 어느 창으로 바꿔 물어야 하나?
- ★ `done` 이 **아예 없는** 결과는 끝인가 아닌가? 근거가 되는 추상 연산은?

### 9. 두 판이 갈린 줄은 11번과 같은 자리인가 (연결) ★★★

- ★★★ 이 주제에서 v18 과 v20 이 **갈린 줄은 어디**이고, 두 문구는 무엇인가?
- ★★ 11번의 `f(...obj)` 와 **같은 자리인가**? 배열 자리 `[...plain]` 은 갈렸나?
- ★ 그래서 무엇을 근거로 쓰고 무엇을 근거로 안 쓰나?

### 10. 파이썬 32번의 `__getitem__` 대체 경로가 JS 에 있나 (연결) ★★★

- ★★★ 파이썬은 `__iter__` 가 없을 때 `for` 가 무엇으로 떨어지나? JS 의 `for...of` 는?
- ★★ 이것은 「잴 것이 없다」인가 「재 봤더니 없다」인가? 근거가 된 줄은?
- ★ JS 에서 **두 번째 문**을 가진 것은 무엇인가? 끝 신호는 두 언어가 어떻게 다른가?

### 11. `for...of null` 과 18번의 `for-in null` (경계) ★★

- ★★ 둘은 각각 무엇을 하나 — 예외인가 0회인가?
- ★★ 명세의 **어느 추상 연산 한 곳**이 그 둘을 가르나?
- ★ 이 차이가 **실무에서 어느 쪽을 더 위험하게** 만드나?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **「세 자리의 문」** · **제너레이터의 `yield`/`next(값)` 흐름** · **이터레이터 헬퍼** · **`for await...of`** · **`Map` 의 키 비교** 는 각각 어느 주제가 정본인가?
- ★★★ 11번이 **끝낸 것**과 이 주제가 **시작하는 것**을 한 줄씩.
- ★ 이 주제가 **끝까지 책임지는 것** 셋을 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
