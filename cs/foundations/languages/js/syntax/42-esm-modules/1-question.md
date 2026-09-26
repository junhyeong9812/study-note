# js/syntax/42 — ESM 모듈: 「`import` 는 무엇을 받고, 언제 돌고, 순환에서 무엇을 보나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(헤드리스 · 로컬 HTTP 서버) · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 순환 의존 격자다** — 내보내는 모양 × 가져오는 순서 × 읽는 때. **3번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **가져온 이름은 값인가 이름인가 — 바꾸면 보이나, 대입하면**
> ② ★★★ **순환에서 무엇이 `ReferenceError` 이고 무엇이 `undefined` 이고 무엇이 멀쩡한가**
> ③ **`import` 는 언제 도나 — 파일 중간 · 평가 순서 · 블록 안 · 없는 이름 · `import()`.**
>
> **선행** — [35](../35-strict-mode/2-summary.md) · [05](../05-var-let-const-and-tdz/2-summary.md) · [36](../36-event-loop-and-microtasks/2-summary.md) · [Python 42](../../../python/syntax/42-modules-packages-and-import/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **3번은 칸마다 `A` / `undefined` / `ReferenceError` 셋 중 하나**만 적어도 된다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 ECMA-262 가 정하나, 호스트(node·브라우저)가 정하나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 카운터를 ESM 과 CommonJS 로 (예측) ★★★

```js
// counter42a.mjs
// A module that owns a counter and changes it itself.
export let n = 0;
export function inc() { n++; }
```

```js
// main42a.mjs
// Reads the counter by name, through the namespace object, and after inc() changed it inside its own module.
import { n, inc } from "./counter42a.mjs";
import * as ns from "./counter42a.mjs";
console.log("[1] before inc()  n = " + n + " · ns.n = " + ns.n);
inc();
console.log("[2] after inc()   n = " + n + " · ns.n = " + ns.n);
inc();
console.log("[3] after inc()   n = " + n + " · ns.n = " + ns.n);
```

```js
// counter42a.cjs
// The same counter as a CommonJS module.
let n = 0;
function inc() { n++; }
module.exports = { n, inc };
```

```js
// main42a.cjs
// The same reads, through require().
const { n, inc } = require("./counter42a.cjs");
const m = require("./counter42a.cjs");
console.log("[1] before inc()  n = " + n + " · m.n = " + m.n);
inc();
console.log("[2] after inc()   n = " + n + " · m.n = " + m.n);
inc();
console.log("[3] after inc()   n = " + n + " · m.n = " + m.n);
```

- ★★★ `main42a.mjs` 와 `main42a.cjs` 각각의 세 줄은?

### 2. 가져온 이름과 이름공간 객체에 쓰기 (예측) ★★★

```js
// value42b.mjs
// A module with one mutable export.
export let v = 1;
export function setV(x) { v = x; }
```

```js
// main42b.mjs
// Writes to an imported binding and to the namespace object -- and asks what kind of object the namespace is.
import { v, setV } from "./value42b.mjs";
import * as ns from "./value42b.mjs";
const show = (e) => e.constructor.name + " 「" + e.message + "」";
const tryIt = (label, f) => { let r; try { r = "ok " + JSON.stringify(f()); } catch (e) { r = show(e); } console.log("  " + label.padEnd(34) + r); };
console.log("[1] writes");
tryIt("v = 2", () => { v = 2; return v; });
tryIt("ns.v = 2", () => { ns.v = 2; return ns.v; });
tryIt("ns.w = 2 (a new property)", () => { ns.w = 2; return ns.w; });
tryIt("delete ns.v", () => delete ns.v);
tryIt("setV(3), then read v", () => { setV(3); return v; });
console.log("[2] the namespace object");
tryIt("Object.prototype.toString.call(ns)", () => Object.prototype.toString.call(ns));
tryIt("ns[Symbol.toStringTag]", () => ns[Symbol.toStringTag]);
tryIt("Object.getPrototypeOf(ns)", () => Object.getPrototypeOf(ns));
tryIt("Object.isExtensible(ns)", () => Object.isExtensible(ns));
tryIt("Object.isFrozen(ns)", () => Object.isFrozen(ns));
tryIt("descriptor of v", () => Object.getOwnPropertyDescriptor(ns, "v"));
tryIt("this at the top level", () => String(this));
```

- ★★★ `[1]` 다섯 줄 각각 — `ok` 인가, 무엇을 던지나?
- ★★ `[2]` 일곱 줄 각각의 값은?

### 3. 순환 의존 격자 (예측) ★★★ 이 주제의 축

```js
// js40b-42c-cycle-grid.js
// Circular import grid: a.mjs <-> b.mjs. b reads a's export X twice -- at its own top level, and later inside a function.
//   8 ways a exports X  x  2 import orders in main.mjs  x  2 moments of reading  = 32 cells
// Each (form, order) pair is a fresh directory and a fresh node process (this same node binary).
// A cell prints the value read, or the exception as constructor.name 「message」.
const fs = require("fs"), path = require("path"), { execFileSync } = require("child_process");
const forms = [
  ["export let X", 'export let X = "A";', "{ X }", "X"],
  ["export const X", 'export const X = "A";', "{ X }", "X"],
  ["export var X", 'export var X = "A";', "{ X }", "X"],
  ["export function X", 'export function X() { return "A"; }', "{ X }", "X()"],
  ["export class X", 'export class X { static v = "A"; }', "{ X }", "X.v"],
  ["export default expression", 'export default "A";', "X", "X"],
  ["export default function", 'export default function () { return "A"; }', "X", "X()"],
  ["export default class", 'export default class { static v = "A"; }', "X", "X.v"],
];
const orders = { "a first": 'import "./a.mjs";\nimport { atTop, later } from "./b.mjs";', "b first": 'import { atTop, later } from "./b.mjs";\nimport "./a.mjs";' };
const guard = (expr) => '(() => { try { return String(' + expr + '); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } })()';
const root = path.join(__dirname, "js40b-42c-cells");
fs.rmSync(root, { recursive: true, force: true });
let broken = 0, total = 0, i = 0;
console.log("form".padEnd(28) + "main imports".padEnd(14) + "b reads at its top level".padEnd(60) + "b reads later, inside a function");
for (const [label, exportLine, importClause, read] of forms) {
  for (const [order, mainText] of Object.entries(orders)) {
    const dir = path.join(root, String(++i));
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, "a.mjs"), 'import "./b.mjs";\n' + exportLine + "\n");
    fs.writeFileSync(path.join(dir, "b.mjs"), "import " + importClause + ' from "./a.mjs";\nexport const atTop = ' + guard(read) + ";\nexport function later() { return " + guard(read) + "; }\n");
    fs.writeFileSync(path.join(dir, "main.mjs"), mainText + '\nconsole.log(atTop + "\\n" + later());\n');
    const [top, late] = execFileSync(process.execPath, ["main.mjs"], { cwd: dir, encoding: "utf8" }).trimEnd().split("\n");
    for (const v of [top, late]) { total++; if (v !== "A") broken++; }
    console.log(label.padEnd(28) + order.padEnd(14) + top.padEnd(60) + late);
  }
}
console.log("");
console.log("cells that did not read \"A\": " + broken + " / " + total);
```

- ★★★ 32칸 각각 — `A` / `undefined` / `ReferenceError` 중 무엇인가?
- ★★ 마지막 줄의 `N / 32` 는?

### 4. 파일 중간의 `import` · 평가 순서 (예측) ★★★

```js
// dep42d.mjs
// Prints when its body runs.
console.log("dep42d.mjs: body runs");
export const x = "x";
```

```js
// main42d.mjs
// An import statement in the middle of the file.
console.log("main42d.mjs: first line");
import { x } from "./dep42d.mjs";
console.log("main42d.mjs: line after the import · x = " + x);
```

```js
// dep42d.cjs
// Prints when its body runs.
console.log("dep42d.cjs: body runs");
exports.x = "x";
```

```js
// main42d.cjs
// A require() call in the middle of the file.
console.log("main42d.cjs: first line");
const { x } = require("./dep42d.cjs");
console.log("main42d.cjs: line after the require · x = " + x);
```

```js
// top42d.mjs
// top imports left and right; left imports right as well. Each body prints once it runs.
import "./left42d.mjs";
import "./right42d.mjs";
console.log("top42d.mjs: body");
```

```js
// left42d.mjs
import "./right42d.mjs";
console.log("left42d.mjs: body");
```

```js
// right42d.mjs
console.log("right42d.mjs: body");
```

- ★★★ `main42d.mjs` · `main42d.cjs` 각각 — 세 줄의 순서는?
- ★★ `top42d.mjs` 를 돌리면 세 줄의 순서는? `right42d.mjs: body` 는 몇 번 찍히나?

### 5. 블록 안 · 없는 이름 · `import()` (예측) ★★

```js
// has42e.mjs
// Exports one name.
console.log("has42e.mjs: body runs");
export const yes = 1;
```

```js
// inblock42e.mjs
// An import statement inside a block.
console.log("inblock42e.mjs: first line");
if (true) {
  import { yes } from "./has42e.mjs";
}
```

```js
// missing42e.mjs
// Imports a name the other module does not export.
console.log("missing42e.mjs: first line");
import { nope } from "./has42e.mjs";
console.log(nope);
```

```js
// dynamic42e.mjs
// import() as an expression: inside a block, twice, and for a file that does not exist.
console.log("dynamic42e.mjs: first line");
if (true) {
  const p = import("./has42e.mjs");
  console.log("import() returned " + p.constructor.name);
  const ns = await p;
  console.log("yes = " + ns.yes + " · same namespace object the second time: " + (ns === (await import("./has42e.mjs"))));
}
try { await import("./nothing-here42e.mjs"); } catch (e) { console.log("missing file: rejected with " + e.constructor.name + " · code " + e.code); }
```

- ★★ `inblock42e.mjs` · `missing42e.mjs` 각각 — 무슨 에러이고, 표준 출력은 몇 줄인가? `has42e.mjs: body runs` 는 찍히나?
- ★★ `dynamic42e.mjs` 의 다섯 줄은? 없는 파일은 node 와 Chrome 에서 각각 무엇으로 거부되나?

### 6. `InitializeEnvironment` 가 만드는 세 모양 (왜) ★★★

- ★★★ 모듈의 본문이 돌기 전에 `var` 이름 · 렉시컬 선언 · 함수 선언은 각각 어떤 상태로 준비되나?
- ★★ 그것이 3번 격자의 어느 칸들을 설명하나?

### 7. 읽는 때를 바꾸면 (경계) ★★

- ★★ 3번에서 `b first` 열과 「나중에 읽기」 열이 어떻게 나왔나? 05번의 「TDZ 는 줄이 아니라 시간이다」와 어떻게 이어지나?
- ★ 순환 에러를 없애려 `let` 을 `var` 로 바꾸면 무엇이 되나?

### 8. 파이썬 42번 · Go 와 나란히 (연결) ★★

- ★★ 파이썬 42번 격자의 깨진 칸은 몇이었고, 무엇으로 깨졌나? 이 문서의 격자와 **축이 어떻게 다른가**?
- ★★ 두 언어가 공통으로 「전부 통과」한 열은 무엇인가? Go 는 순환 import 를 어디서 막나?

### 9. 「정적 구조」가 실행에서 보이는 것 (경계) ★★

- ★★ 연혁 문서가 「정적 구조」에서 끌어낸 인과는 무엇이고, 이 문서는 그것을 쟀나?
- ★ 이 문서가 실행으로 보인 「정적」의 증거 둘은?

### 10. 층을 가른다 (경계) ★

- ★ 「`./m.mjs` 가 어느 파일인가」·「이 파일이 모듈인가」·「없는 이름은 `SyntaxError`」·「가져온 이름은 불변」 — 각각 언어인가 호스트인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
