# js/syntax/44 — 동적 `import`·최상위 `await`·import attributes: 「본문은 언제 도나, 누가 누구를 기다리나, 딱지는 어느 판에서 읽히나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(로컬 HTTP 서버) · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 평가 순서 로그다** — 모듈 본문 첫 줄에 로그를 심고 **줄의 순서**로 읽는다. 보조로 import attributes **판 격자** 12행 × 세 판. **1번 · 2번 · 4번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`import()` 는 언제 상대 본문을 돌리나 · 두 번 부르면**
> ② ★★★ **최상위 `await` 는 누구를 기다리게 하나**
> ③ ★★★ **import attributes 는 세 판의 어느 칸에서 막히나 · 실패한 `import()` 는 무엇으로 거부되나.**
>
> **선행** — [42](../42-esm-modules/2-summary.md) · [43](../43-cjs-and-esm-interop/2-summary.md) · [39](../39-async-await/2-summary.md) · [31](../31-json/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **4번은 행마다 `ok`/`blocked` 하나 · 판마다 하나**만 먼저 적어도 된다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 ECMA-262 인가, 호스트인가, 엔진이 남겨 둔 옛 제안인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 정적 `import` 하나와 `import()` 셋 (예측) ★★★ 이 주제의 축

```js
// stat44a.mjs
// Imported statically by main44a.mjs. Prints when its body runs.
console.log("stat44a.mjs: body runs");
export const v = "stat";
```

```js
// dyn44a.mjs
// Only reached through import(). Prints when its body runs.
console.log("dyn44a.mjs: body runs");
export const v = "dyn";
```

```js
// main44a.mjs
// One static import, then import() twice for the same file and once for the statically imported one.
import * as stat from "./stat44a.mjs";
console.log("main44a.mjs: first line");
const p1 = import("./dyn44a.mjs");
const p2 = import("./dyn44a.mjs");
console.log("main44a.mjs: two import() calls made · p1 === p2 " + (p1 === p2));
const [a, b] = await Promise.all([p1, p2]);
console.log("namespace from p1 === namespace from p2 " + (a === b) + " · v = " + a.v);
console.log("import('./stat44a.mjs') === the static namespace " + ((await import("./stat44a.mjs")) === stat));
console.log("main44a.mjs: last line");
```

- ★★★ `node20 main44a.mjs` 의 일곱 줄은 어떤 순서로 나오나?
- ★★ `p1 === p2` 는? 두 이름공간은 같은 객체인가? `dyn44a.mjs: body runs` 는 몇 번 찍히나?

### 2. 최상위 `await` 가 있는 모듈과 그 형제 (예측) ★★★

```js
// tla44b.mjs
// A module with top-level await: it waits 50 ms in the middle of its body.
console.log("tla44b.mjs: before await");
await new Promise((r) => setTimeout(r, 50));
console.log("tla44b.mjs: after await");
export const s = "tla";
```

```js
// dep44b.mjs
// Imports tla44b.mjs itself.
import { s } from "./tla44b.mjs";
console.log("dep44b.mjs: body · s = " + s);
```

```js
// plain44b.mjs
// No top-level await, no imports.
console.log("plain44b.mjs: body");
```

```js
// main44b.mjs
// Imports three modules in this order: tla44b (top-level await), dep44b (imports tla44b), plain44b.
import "./tla44b.mjs";
import "./dep44b.mjs";
import "./plain44b.mjs";
console.log("main44b.mjs: body");
```

- ★★★ 다섯 줄은 어떤 순서로 나오나?
- ★★ `plain44b` 는 50 ms 를 기다리나? `dep44b` 는?

### 3. 실패한 `import()` 두 가지 (예측) ★★

```js
// broken44c.mjs
// A module with a syntax error on its second line.
console.log("broken44c.mjs: body runs");
export const x = ;
```

```js
// throws44c.mjs
// A module whose body throws while it is evaluated. It counts its own runs on globalThis.
globalThis.runs44c = (globalThis.runs44c || 0) + 1;
console.log("throws44c.mjs: body runs");
throw new RangeError("thrown while evaluating");
```

```js
// main44c.mjs
// import() of a module that does not parse, and twice of a module that throws.
const show = (e) => e.constructor.name + " 「" + e.message + "」";
try { await import("./broken44c.mjs"); } catch (e) { console.log("[1] import('./broken44c.mjs') rejected: " + show(e)); }
let first;
try { await import("./throws44c.mjs"); } catch (e) { first = e; console.log("[2] import('./throws44c.mjs') rejected: " + show(e)); }
try { await import("./throws44c.mjs"); } catch (e) { console.log("[3] again: " + show(e) + " · same error object " + (e === first)); }
console.log("[4] throws44c.mjs body ran " + globalThis.runs44c + " time(s)");
```

- ★★ `[1]`\~`[4]` 네 줄과, 그 사이에 끼는 본문 줄은? `broken44c.mjs: body runs` 는 찍히나?
- ★★ `[3]` 의 `same error object` 는? `[4]` 의 횟수는?

### 4. import attributes — 세 판 (예측) ★★★

```js
// js44b-44d-attributes-grid.js
// Import attributes, one row per cell: a fresh directory holding data.json ({"k": 1}), code.mjs and the row's main.mjs,
// run by this node binary. Prints one line per row: number <TAB> label <TAB> cell.
// cell = "ok " + what main.mjs printed (+ " + warning" if standard error was not empty),
//     or "blocked " + error name + (the [code], or for an error without a code its message).
// A row that printed a warning adds a line: "warning" <TAB> number <TAB> the warning without "(node:<pid>) ".
// The cell directory's file:// URL is replaced by <dir> in every message.
// Also writes js44b-44d-cells/rows.json, so the browser run (js44b-44d-attributes.web.js) loads the same cells.
const fs = require("fs"), path = require("path"), { spawnSync } = require("child_process");
const show = 'console.log(JSON.stringify(d));\n';
const rows = [
  ["static  with { type: 'json' }", 'import d from "./data.json" with { type: "json" };\n' + show],
  ["static  assert { type: 'json' }", 'import d from "./data.json" assert { type: "json" };\n' + show],
  ["static  no attributes", 'import d from "./data.json";\n' + show],
  ["static  with { type: 'css' }", 'import d from "./data.json" with { type: "css" };\n' + show],
  ["static  with { type: 'json', mode: 'x' }", 'import d from "./data.json" with { type: "json", mode: "x" };\n' + show],
  ["static  import { k } ... with { type: 'json' }", 'import { k } from "./data.json" with { type: "json" };\nconsole.log(k);\n'],
  ["static  code.mjs with { type: 'json' }", 'import d from "./code.mjs" with { type: "json" };\n' + show],
  ["import(..., { with: { type: 'json' } })", 'const d = (await import("./data.json", { with: { type: "json" } })).default;\n' + show],
  ["import(..., { assert: { type: 'json' } })", 'const d = (await import("./data.json", { assert: { type: "json" } })).default;\n' + show],
  ["import(...) with no options", 'const d = (await import("./data.json")).default;\n' + show],
  ["static  with { type: 'json', type: 'json' }", 'import d from "./data.json" with { type: "json", type: "json" };\n' + show],
  ["static and import() of the same JSON", 'import a from "./data.json" with { type: "json" };\nconst b = (await import("./data.json", { with: { type: "json" } })).default;\nconsole.log("same object " + (a === b));\n'],
];
const root = path.join(__dirname, "js44b-44d-cells");
fs.rmSync(root, { recursive: true, force: true });
rows.forEach(([label, main], i) => {
  const dir = path.join(root, String(i + 1));
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "data.json"), '{"k": 1}\n');
  fs.writeFileSync(path.join(dir, "code.mjs"), 'export default "code";\n');
  fs.writeFileSync(path.join(dir, "main.mjs"), main);
  const r = spawnSync(process.execPath, ["main.mjs"], { cwd: dir, encoding: "utf8" });
  const err = r.stderr.split("file://" + dir).join("<dir>");
  let cell;
  if (r.status === 0) cell = "ok " + r.stdout.trim() + (err ? " + warning" : "");
  else {
    const m = err.match(/^(\w*Error)(?: \[(\w+)\])?: (.*)$/m);
    cell = "blocked " + (m ? m[1] + " " + (m[2] || "「" + m[3] + "」") : "?");
  }
  console.log(i + 1 + "\t" + label + "\t" + cell);
  if (r.status === 0 && err) console.log("warning\t" + (i + 1) + "\t" + err.split("\n")[0].replace(/^\(node:\d+\) /, ""));
});
fs.writeFileSync(path.join(root, "rows.json"), JSON.stringify(rows.map((r) => r[0])) + "\n");
```

- ★★★ 12행 각각 — node 20 에서 `ok` 인가 `blocked` 인가? 막히면 무슨 이름·코드인가?
- ★★★ node 18.19.1 에서 달라지는 행은? Chrome 151 에서는? 세 판이 **다 같이 통과하는** 행이 있나?

### 5. 끝내 안 풀리는 최상위 `await` (경계) ★★

```js
// pending44b.mjs
// Top-level await on a promise that never settles.
console.log("pending44b.mjs: before await");
await new Promise(() => {});
console.log("pending44b.mjs: after await");
```

```js
// importer44b.mjs
// Imports pending44b.mjs.
import "./pending44b.mjs";
console.log("importer44b.mjs: body");
```

- ★★ `node20 importer44b.mjs` 는 무엇을 찍고 어떤 종료 코드로 끝나나? 경고가 나오나?

### 6. 2번의 순서를 가른 것 (왜) ★★★

- ★★★ 2번에서 `plain44b` 와 `dep44b` 의 자리를 가른 것은 무엇인가? 명세는 「기다려야 하는 모듈」을 무엇으로 세나?

### 7. 딱지는 누가 읽나 (왜) ★★★

- ★★★ 4번의 속성 없는 JSON 행(3·10)의 결과는 명세가 요구한 것인가? 아니면 누구의 선택인가?
- ★★ 모르는 키 `mode` 행(5)에서 Chrome 과 node 20 의 결과를 견주면, 명세가 정한 모양은 어느 쪽인가?

### 8. 층을 가른다 (경계) ★★

- ★★ `with { … }` 문법 · `assert { … }` · `type` 만 받는 것 · 종료 코드 13 · 형제를 안 기다리는 평가 순서 — 각각 ECMA-262 인가, 호스트인가, 엔진인가?

### 9. 다시 부르면 (경계) ★★

- ★★ 3번 `[3]`·`[4]` 줄을 모듈 레코드의 무엇으로 설명하나? 같은 지정자로 몇 번을 더 불러도 같은가?

### 10. 42번 · 43번과 이어 보기 (연결) ★★

- ★★ 42번이 이미 잰 `import()` 의 성질 둘은 무엇이고, 이 주제는 거기서 무엇을 넓혔나?
- ★ 43번에서 최상위 `await` 가 든 ESM 을 CommonJS 가 `require` 하면 두 node 판은 각각 무엇을 냈나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
