# js/syntax/46 — `Reflect`: 「트랩과 짝이 맞나, 옛 창구와 어디서 갈리나, `receiver` 는 무엇을 바꾸나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v20.19.6(배너의 `node20`) · x86-64 Linux. ★ 이 주제의 탐침은 node 18 · Chrome 151 에서도 **한 글자도 같았다.**
>
> ★★★ **이 주제의 본체는 격자 둘이다** — 대응 표 13행 · `Object` 대 `Reflect` 19행. **1번 · 2번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`Reflect` 는 몇 개이고 트랩과 어떻게 짝이 맞나**
> ② ★★★ **같은 요청을 `Object`/연산자와 `Reflect` 로 하면 어디서 갈리나**
> ③ ★★ **`receiver` 가 바꾸는 것 — getter 의 `this` · 쓰기가 떨어지는 곳 · 트랩에서 넘길 때.**
>
> **선행** — [45](../45-proxy/2-summary.md) · [09](../09-call-apply-bind/2-summary.md) · [14](../14-property-descriptors-and-freezing/2-summary.md) · [22](../22-symbol-and-well-known-symbols/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~3)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **2번은 행마다 「왼쪽 · 오른쪽」 두 칸**만 먼저 적어도 된다 — 던지면 `throws TypeError`.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 차이는 실패 처리 때문인가, 원시값 처리 때문인가, 조회 경로 때문인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `Reflect` 를 세고, 트랩을 부른다 (예측) ★★★ 이 주제의 축

```js
// js44b-46a-reflect-and-traps.js
// [1] What Reflect owns. [2] Each Reflect function called on a proxy whose handler has every trap name
// (the list is written out below, not taken from Reflect) -- which traps fire. The traps do not forward;
// each returns a fixed answer that keeps the invariants of an ordinary extensible target.
// [3] Which Reflect function names are also own properties of Object.
const names = Object.getOwnPropertyNames(Reflect);
const fns = names.filter((n) => typeof Reflect[n] === "function");
console.log("[1] Object.getOwnPropertyNames(Reflect): " + names.length + " names · functions: " + fns.length);
console.log("  " + fns.join(" "));
console.log("  Reflect[Symbol.toStringTag] = " + String(Reflect[Symbol.toStringTag]) + " · typeof Reflect = " + typeof Reflect);

const trapNames = ["apply", "construct", "defineProperty", "deleteProperty", "get", "getOwnPropertyDescriptor",
  "getPrototypeOf", "has", "isExtensible", "ownKeys", "preventExtensions", "set", "setPrototypeOf"];
const answers = {
  apply: undefined, construct: {}, defineProperty: true, deleteProperty: true, get: undefined,
  getOwnPropertyDescriptor: undefined, getPrototypeOf: Function.prototype, has: false, isExtensible: true,
  ownKeys: ["prototype"], preventExtensions: false, set: true, setPrototypeOf: true,
};
let fired = [];
const handler = {};
for (const t of trapNames) handler[t] = () => { fired.push(t); return answers[t]; };
const target = class {};
const p = new Proxy(target, handler);
const calls = {
  apply: () => Reflect.apply(p, null, []),
  construct: () => Reflect.construct(p, []),
  defineProperty: () => Reflect.defineProperty(p, "x", { value: 1, configurable: true }),
  deleteProperty: () => Reflect.deleteProperty(p, "x"),
  get: () => Reflect.get(p, "x"),
  getOwnPropertyDescriptor: () => Reflect.getOwnPropertyDescriptor(p, "x"),
  getPrototypeOf: () => Reflect.getPrototypeOf(p),
  has: () => Reflect.has(p, "x"),
  isExtensible: () => Reflect.isExtensible(p),
  ownKeys: () => Reflect.ownKeys(p),
  preventExtensions: () => Reflect.preventExtensions(p),
  set: () => Reflect.set(p, "x", 1),
  setPrototypeOf: () => Reflect.setPrototypeOf(p, Function.prototype),
};
console.log("");
console.log("[2] Reflect.<name>(proxy, ...) -- the traps that fired");
let same = 0;
for (const n of fns) {
  fired = [];
  let r;
  try { calls[n](); r = fired.join(", "); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  if (fired.length === 1 && fired[0] === n) same++;
  console.log("  Reflect." + n.padEnd(26) + r);
}
console.log("  Reflect functions that fired exactly one trap, of the same name: " + same + " / " + fns.length);
console.log("  trap names without a Reflect function of that name: " + (trapNames.filter((t) => !fns.includes(t)).join(" ") || "none"));

console.log("");
console.log("[3] the same name as an own property of Object?");
console.log("  on Object too:  " + fns.filter((n) => Object.hasOwn(Object, n)).join(" "));
console.log("  Reflect only:   " + fns.filter((n) => !Object.hasOwn(Object, n)).join(" "));
```

- ★★★ `[1]` 의 두 수와 `typeof Reflect` 는?
- ★★★ `[2]` 에서 각 함수가 부른 트랩은? 마지막 두 줄은?
- ★★ `[3]` 두 줄에 각각 몇 개가 들어가나?

### 2. 같은 요청 · 두 창구 (예측) ★★★

```js
// js44b-46b-object-vs-reflect.js
"use strict";
// The same request made with an Object method or an operator (left) and with Reflect (right).
// A cell is the value the call returned, or the name of the exception it threw.
// The last lines count the rows where only one side threw, and the rows where both returned but different values.
const fixed = () => Object.defineProperty({}, "x", { value: 1, writable: false, configurable: false, enumerable: true });
const sealed = () => Object.preventExtensions({ x: 1 });
const withSymbol = () => { const o = { a: 1, [Symbol("s")]: 2 }; Object.defineProperty(o, "hidden", { value: 3, enumerable: false }); return o; };
const f = function (a, b) { return a + b; };
const shadowed = Object.assign(function (a, b) { return a + b; }, { apply: () => "own apply property" });
class C { constructor(v) { this.v = v; } }
const show = (v) => {
  if (typeof v === "string") return JSON.stringify(v);
  if (v === Number.prototype) return "Number.prototype";
  if (v === Object.prototype) return "Object.prototype";
  if (Array.isArray(v)) return "[" + v.map(String).join(", ") + "]";
  if (v instanceof C) return "C { v: " + v.v + " }";
  if (v && typeof v === "object" && "writable" in v) return "descriptor { value: " + v.value + ", writable: " + v.writable + " }";
  return String(v);
};
const out = (g) => { try { return show(g()); } catch (e) { return "throws " + e.constructor.name; } };
const rows = [
  ["defineProperty -- change x's value (x fixed)", () => Object.defineProperty(fixed(), "x", { value: 2 }) && "the object", () => Reflect.defineProperty(fixed(), "x", { value: 2 })],
  ["defineProperty -- add y (not extensible)", () => Object.defineProperty(sealed(), "y", { value: 2 }) && "the object", () => Reflect.defineProperty(sealed(), "y", { value: 2 })],
  ["getOwnPropertyDescriptor('str', 'length')", () => Object.getOwnPropertyDescriptor("str", "length"), () => Reflect.getOwnPropertyDescriptor("str", "length")],
  ["getPrototypeOf(1)", () => Object.getPrototypeOf(1), () => Reflect.getPrototypeOf(1)],
  ["setPrototypeOf -- not extensible, to {}", () => Object.setPrototypeOf(sealed(), {}) && "the object", () => Reflect.setPrototypeOf(sealed(), {})],
  ["setPrototypeOf -- not extensible, to the same", () => Object.setPrototypeOf(sealed(), Object.prototype) && "the object", () => Reflect.setPrototypeOf(sealed(), Object.prototype)],
  ["preventExtensions(1)", () => Object.preventExtensions(1), () => Reflect.preventExtensions(1)],
  ["isExtensible(1)", () => Object.isExtensible(1), () => Reflect.isExtensible(1)],
  ["keys vs ownKeys -- symbol and non-enumerable key", () => Object.keys(withSymbol()), () => Reflect.ownKeys(withSymbol())],
  ["keys vs ownKeys -- on 1", () => Object.keys(1), () => Reflect.ownKeys(1)],
  ["delete o.x vs deleteProperty (x fixed)", () => delete fixed().x, () => Reflect.deleteProperty(fixed(), "x")],
  ["o.x = 2 vs set (x fixed)", () => { fixed().x = 2; return "assigned"; }, () => Reflect.set(fixed(), "x", 2)],
  ["o.x vs get", () => fixed().x, () => Reflect.get(fixed(), "x")],
  ["'x' in o vs has", () => "x" in fixed(), () => Reflect.has(fixed(), "x")],
  ["'x' in 1 vs has(1, 'x')", () => "x" in 1, () => Reflect.has(1, "x")],
  ["f.apply(null, [1, 2]) vs apply", () => f.apply(null, [1, 2]), () => Reflect.apply(f, null, [1, 2])],
  ["g.apply(...) -- g has its own apply property", () => shadowed.apply(null, [1, 2]), () => Reflect.apply(shadowed, null, [1, 2])],
  ["f.apply(null) vs apply(f, null) -- no list", () => f.apply(null), () => Reflect.apply(f, null)],
  ["new C(1) vs construct(C, [1])", () => new C(1), () => Reflect.construct(C, [1])],
];
console.log("  " + "request".padEnd(50) + "Object / operator".padEnd(42) + "Reflect");
let oneThrows = 0, bothReturn = 0;
for (const [label, left, right] of rows) {
  const l = out(left), r = out(right);
  const lt = l.startsWith("throws"), rt = r.startsWith("throws");
  let mark = "  ";
  if (lt !== rt) { oneThrows++; mark = "* "; }
  else if (!lt && l !== r) { bothReturn++; mark = "~ "; }
  console.log(mark + label.padEnd(50) + l.padEnd(42) + r);
}
console.log("");
console.log("rows where only one side threw (*): " + oneThrows + " / " + rows.length);
console.log("rows where both returned, different values (~): " + bothReturn + " / " + rows.length);
console.log("rows that differ: " + (oneThrows + bothReturn) + " / " + rows.length);
```

- ★★★ 19행 각각의 두 칸은? 마지막 세 줄의 `N / 19` 는?

### 3. `receiver` (예측) ★★

```js
// js44b-46c-receiver.js
// The receiver argument: whom a getter or setter sees as this, and where a data write lands.
const base = {
  name: "base",
  get who() { return this.name; },
  set who(v) { this.written = v; },
};
const other = { name: "other" };
console.log("[1] base.who                              " + base.who);
console.log("[2] Reflect.get(base, 'who')              " + Reflect.get(base, "who"));
console.log("[3] Reflect.get(base, 'who', other)       " + Reflect.get(base, "who", other));
console.log("[4] Reflect.set(base, 'who', 1, other)    " + Reflect.set(base, "who", 1, other) +
  " · other.written " + other.written + " · base.written " + base.written);
const plain = { x: 1 };
const into = {};
console.log("[5] Reflect.set(plain, 'x', 2, into)      " + Reflect.set(plain, "x", 2, into) +
  " · plain.x " + plain.x + " · into.x " + into.x + " · own x in into " + Object.hasOwn(into, "x"));

// [6] Two proxies over the same target with a getter, used as the prototype of an object named "child".
// The first get trap reads target[key]; the second hands on the receiver with Reflect.get(target, key, receiver).
const target = { name: "target", get who() { return this.name; } };
const readsTarget = new Proxy(target, { get(t, k) { return t[k]; } });
const passesReceiver = new Proxy(target, { get(t, k, r) { return Reflect.get(t, k, r); } });
const child1 = Object.create(readsTarget); child1.name = "child";
const child2 = Object.create(passesReceiver); child2.name = "child";
console.log("[6] child.who through get(t, k) { return t[k] }                     " + child1.who);
console.log("    child.who through get(t, k, r) { return Reflect.get(t, k, r) }  " + child2.who);

// [7] A set trap that forwards with Reflect.set(t, k, v, r), and two more traps that only log. p.x = 1 -- which traps fire?
const fired = [];
const p = new Proxy({}, {
  set(t, k, v, r) { fired.push("set"); return Reflect.set(t, k, v, r); },
  getOwnPropertyDescriptor(t, k) { fired.push("getOwnPropertyDescriptor"); return Reflect.getOwnPropertyDescriptor(t, k); },
  defineProperty(t, k, d) { fired.push("defineProperty"); return Reflect.defineProperty(t, k, d); },
});
p.x = 1;
console.log("[7] p.x = 1 fired: " + fired.join(" -> "));
fired.length = 0;
Reflect.set(p, "y", 1, {});
console.log("    Reflect.set(p, 'y', 1, {}) fired: " + fired.join(" -> "));
```

- ★★ `[1]`\~`[5]` 다섯 줄은?
- ★★★ `[6]` 두 줄 — `target` 인가 `child` 인가?
- ★★ `[7]` 두 줄에서 불린 트랩은?

### 4. 2번의 차이를 두 규칙으로 (왜) ★★★

- ★★★ 2번에서 「한쪽만 던진」 행들을 규칙 두 개로 묶어라. 각 규칙은 명세의 어느 단계인가?

### 5. 트랩을 넘기는 표준 형태 (왜) ★★★

- ★★★ Proxy 트랩에서 넘길 때 `Reflect.<같은 이름>(...arguments)` 가 표준인 이유를 45번의 격자 한 줄과 3번의 `[6]` 으로 설명하라.

### 6. 1번에서 트랩을 넘기지 않은 까닭 (경계) ★★

- ★★ 1번의 handler 가 `Reflect` 로 넘기지 않고 고정 답을 돌려준 이유는 무엇인가? 3번 `[7]` 과 이어서 답하라.

### 7. `apply` 두 행 (경계) ★★

- ★★ 2번의 `apply` 세 행은 각각 무엇 때문에 같거나 다른가? 09번의 `apply(t, null)` 과 견주면?

### 8. 층을 가른다 (경계) ★

- ★ 2번 격자의 칸들 중 엔진이나 호스트에 달린 것이 있나? `getOwnPropertyNames(Reflect)` 의 순서는?

### 9. 14번 · 22번과 이어 보기 (연결) ★★

- ★★ 2번 탐침이 엄격 모드여야 했던 이유를 14번으로, `keys` 대 `ownKeys` 행을 22번으로 설명하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
