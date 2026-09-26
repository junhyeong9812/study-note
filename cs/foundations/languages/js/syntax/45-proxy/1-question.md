# js/syntax/45 — `Proxy`: 「트랩은 어디까지 말을 지어낼 수 있고, 대리인은 대상의 무엇을 못 빌리나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v20.19.6(배너의 `node20`) · x86-64 Linux. ★ 이 주제의 탐침은 node 18 · Chrome 151 에서도 **한 글자도 같았다.**
>
> ★★★ **이 주제의 본체는 불변식 격자다** — 트랩 8개 × 대상 상태 3개 = 24칸. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **트랩이 대상과 다른 답을 하면 언제 `TypeError` 인가**
> ② ★★ **트랩의 `false` 는 엄격과 비엄격에서 무엇이 다른가**
> ③ ★★ **대리인은 대상의 무엇을 빌리고 무엇을 못 빌리나 — 내부 슬롯 · `typeof` · 배열 판별 · 취소 뒤.**
>
> **선행** — [14](../14-property-descriptors-and-freezing/2-summary.md) · [15](../15-prototype-chain/2-summary.md) · [35](../35-strict-mode/2-summary.md) · [16](../16-class-syntax/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸마다 `ok …` / `TypeError` 하나**만 먼저 적어도 된다 — 표 `[1]` 이 24칸, 표 `[2]` 가 24칸이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 `TypeError` 는 불변식 검사가 낸 것인가, 호출한 쪽이 `false` 를 바꾼 것인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 트랩 8개 × 대상 상태 3개 (예측) ★★★ 이 주제의 축

```js
// js44b-45a-invariant-grid.js
// Eight traps x three states of the target. In each cell the handler has one trap, and the probe runs one operation on the proxy.
// Sloppy-mode script on purpose: an assignment or a delete that fails does not throw here, so what throws comes from the proxy.
// Table [1]: the trap reports something the target does not hold (column "what the trap returns").
// Table [2]: the same trap hands the call on with Reflect.<the same name>(...arguments),
//            and each cell is compared with the same operation on the bare target (no proxy).
// [3]: the message of every exception in table [1].
// A cell prints "ok " + what the operation gave, or the name of the exception it threw.
const states = [
  ["ordinary", () => ({ x: "real" })],
  ["x non-writable+non-configurable", () => Object.defineProperty({}, "x", { value: "real", writable: false, configurable: false, enumerable: true })],
  ["preventExtensions", () => Object.preventExtensions({ x: "real" })],
];
const desc = (d) => (d === undefined ? undefined : d.value + " w:" + d.writable + " c:" + d.configurable);
const traps = [
  ["get", "'lie'", () => "lie", (p) => p.x],
  ["set", "true (writes nothing)", () => true, (p) => { p.x = "new"; return p.x; }],
  ["has", "false", () => false, (p) => "x" in p],
  ["deleteProperty", "true (deletes nothing)", () => true, (p) => delete p.x],
  ["defineProperty", "true (defines nothing)", () => true, (p) => { Object.defineProperty(p, "x", { value: "new" }); return p.x; }],
  ["getOwnPropertyDescriptor", "undefined", () => undefined, (p) => desc(Object.getOwnPropertyDescriptor(p, "x"))],
  ["ownKeys", "[]", () => [], (p) => Object.keys(p)],
  ["getPrototypeOf", "a new {}", () => ({}), (p) => Object.getPrototypeOf(p) === Object.prototype],
];
const messages = [];
const run = (subject, op, where) => {
  try { return "ok " + JSON.stringify(op(subject)); }
  catch (e) { if (where) messages.push(where + ": " + e.message); return e.constructor.name; }
};
const head = () => console.log("  " + "trap".padEnd(25) + "what the trap returns".padEnd(34) + states.map(([s]) => s.padEnd(33)).join("").trimEnd());
const row = (name, second, cells) => console.log("  " + name.padEnd(25) + second.padEnd(34) + cells.map((c) => c.padEnd(33)).join("").trimEnd());

console.log("[1] the trap returns what is in the second column");
head();
let thrown = 0;
for (const [name, lie, trap, op] of traps) {
  const cells = states.map(([s, make]) => run(new Proxy(make(), { [name]: trap }), op, name + " / " + s));
  thrown += cells.filter((c) => !c.startsWith("ok")).length;
  row(name, lie, cells);
}
console.log("  cells that threw: " + thrown + " / " + traps.length * states.length);

console.log("");
console.log("[2] the trap forwards with Reflect");
head();
let thrown2 = 0, differ = 0;
for (const [name, , , op] of traps) {
  const cells = states.map(([, make]) => {
    const viaProxy = run(new Proxy(make(), { [name]: (...args) => Reflect[name](...args) }), op);
    if (viaProxy !== run(make(), op)) differ++;
    if (!viaProxy.startsWith("ok")) thrown2++;
    return viaProxy;
  });
  row(name, "Reflect." + name, cells);
}
console.log("  cells that threw: " + thrown2 + " / " + traps.length * states.length);
console.log("  cells where the bare target gave a different answer: " + differ + " / " + traps.length * states.length);

console.log("");
console.log("[3] messages of the exceptions in [1]");
for (const m of messages) console.log("  " + m);
```

- ★★★ 표 `[1]` 의 24칸 각각 — `ok …` 인가 `TypeError` 인가? 마지막 줄의 `N / 24` 는?
- ★★ 표 `[2]` 에서 던지는 칸은? 「맨 대상과 다른 답」은 몇 칸인가?

### 2. `false` 를 돌려주는 트랩 (예측) ★★

```js
// js44b-45c-falsish.js
// A set trap and a deleteProperty trap that return false -- the same statement in a strict function and in a sloppy one.
// Strict first (rule 22), then sloppy, then the Reflect calls that report the same result as a value.
const p = new Proxy({}, { set: () => false, deleteProperty: () => false });
const run = (f) => { try { return "no exception · " + f(); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };
function strictSet() { "use strict"; p.x = 1; return "p.x = " + p.x; }
function sloppySet() { p.x = 1; return "p.x = " + p.x; }
function strictDelete() { "use strict"; return "delete gave " + delete p.x; }
function sloppyDelete() { return "delete gave " + delete p.x; }
console.log("[1] strict  p.x = 1     -> " + run(strictSet));
console.log("[2] sloppy  p.x = 1     -> " + run(sloppySet));
console.log("[3] strict  delete p.x  -> " + run(strictDelete));
console.log("[4] sloppy  delete p.x  -> " + run(sloppyDelete));
console.log("[5] Reflect.set(p, 'x', 1) -> " + Reflect.set(p, "x", 1) + " · Reflect.deleteProperty(p, 'x') -> " + Reflect.deleteProperty(p, "x"));
```

- ★★ `[1]`\~`[5]` 다섯 줄은?

### 3. 내장 객체와 프라이빗 필드를 감싸면 (예측) ★★

```js
// js44b-45d-internal-slots.js
// Built-in methods called with this = a Proxy whose target is the built-in object (empty handler: every trap is missing).
const run = (label, f) => {
  let r;
  try { r = "ok " + JSON.stringify(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(64) + r);
};
console.log("[1] empty handler");
run("new Proxy(new Map([[1, 'a']]), {}).get(1)", () => new Proxy(new Map([[1, "a"]]), {}).get(1));
run("new Proxy(new Map([[1, 'a']]), {}).size", () => new Proxy(new Map([[1, "a"]]), {}).size);
run("new Proxy(new Set([1]), {}).has(1)", () => new Proxy(new Set([1]), {}).has(1));
run("new Proxy(new Date(0), {}).getTime()", () => new Proxy(new Date(0), {}).getTime());
run("new Proxy([1, 2], {}).push(3)", () => new Proxy([1, 2], {}).push(3));
run("new Proxy({ n: 1, twice() { return this.n * 2; } }, {}).twice()", () => new Proxy({ n: 1, twice() { return this.n * 2; } }, {}).twice());
class C { #x = 1; getX() { return this.#x; } }
run("new Proxy(new C(), {}).getX()   (C has a private #x)", () => new Proxy(new C(), {}).getX());
console.log("[2] a get trap that binds functions to the target");
const bound = {
  get(t, k) {
    const v = Reflect.get(t, k);
    return typeof v === "function" ? v.bind(t) : v;
  },
};
run("new Proxy(new Map([[1, 'a']]), bound).get(1)", () => new Proxy(new Map([[1, "a"]]), bound).get(1));
run("new Proxy(new Map([[1, 'a']]), bound).size", () => new Proxy(new Map([[1, "a"]]), bound).size);
run("new Proxy(new C(), bound).getX()", () => new Proxy(new C(), bound).getX());
```

- ★★ `[1]` 의 일곱 줄 — 어느 것이 `ok` 이고 어느 것이 `TypeError` 인가?
- ★ `[2]` 의 세 줄은?

### 4. 겉모습 — 그리고 취소 뒤 (예측) ★★

```js
// js44b-45e-what-a-proxy-looks-like.js
// What typeof, Array.isArray, Object.prototype.toString and JSON.stringify say about a Proxy -- and a revoked one.
const run = (label, f) => {
  let r;
  try { r = "ok " + String(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(52) + r);
};
const tag = (v) => Object.prototype.toString.call(v);
console.log("[1] a live proxy");
const t = {};
run("new Proxy(t, {}) === t", () => new Proxy(t, {}) === t);
run("typeof new Proxy({}, {})", () => typeof new Proxy({}, {}));
run("typeof new Proxy(function () {}, {})", () => typeof new Proxy(function () {}, {}));
run("typeof new Proxy(class {}, {})", () => typeof new Proxy(class {}, {}));
run("Array.isArray(new Proxy([], {}))", () => Array.isArray(new Proxy([], {})));
run("toString tag of new Proxy([], {})", () => tag(new Proxy([], {})));
run("toString tag of new Proxy(new Map(), {})", () => tag(new Proxy(new Map(), {})));
run("JSON.stringify(new Proxy([1, 2], {}))", () => JSON.stringify(new Proxy([1, 2], {})));
run("new Proxy({}, {}) instanceof Proxy", () => new Proxy({}, {}) instanceof Proxy);
run("Proxy({}, {})   (without new)", () => Proxy({}, {}));
console.log("[2] Proxy.revocable, then revoke()");
const o = Proxy.revocable({ a: 1 }, {});
const arr = Proxy.revocable([], {});
const fn = Proxy.revocable(function () {}, {});
run("proxy.a before revoke()", () => o.proxy.a);
o.revoke(); arr.revoke(); fn.revoke();
run("proxy.a", () => o.proxy.a);
run("'a' in proxy", () => "a" in o.proxy);
run("typeof proxy", () => typeof o.proxy);
run("typeof (a revoked proxy of a function)", () => typeof fn.proxy);
run("Array.isArray(a revoked proxy of [])", () => Array.isArray(arr.proxy));
run("revoke() a second time", () => o.revoke());
```

- ★★ `[1]` 열 줄과 `[2]` 일곱 줄은?

### 5. 불변식 검사는 무엇과 무엇을 대조하나 (왜) ★★★

- ★★★ 1번 표 `[1]` 의 「보통」 열의 결과를 그 대조로 설명하라.
- ★★ `getPrototypeOf` 행의 세 칸은 왜 그렇게 갈리나?

### 6. 두 종류의 `TypeError` (왜) ★★

- ★★ 1번의 `[3]` 문구와 2번의 `[1]` 문구를 견주면, 두 `TypeError` 는 각각 누가 낸 것인가?

### 7. 투명한 대리인 (경계) ★★

- ★★ 빈 `handler` 의 Proxy 가 대상과 **구분되는** 자리를 이 문서에서 셋 들어라. 반대로 구분이 **안 되는** 자리는?

### 8. `typeof` 와 취소 (경계) ★

- ★ 4번 `[2]` 의 `typeof` 줄과 `Array.isArray` 줄의 결과를 각각 무엇으로 설명하나? `revoke()` 를 두 번 부르면?

### 9. 14번과 이어 보기 (연결) ★★

- ★★ 14번의 「비엄격에서는 막힌 쓰기가 조용히 버려진다」가 이 주제의 어느 두 곳에 다시 나오나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
