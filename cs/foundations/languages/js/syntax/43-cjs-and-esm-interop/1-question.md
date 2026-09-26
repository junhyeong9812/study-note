# js/syntax/43 — CJS 와 ESM 상호운용: 「누가 누구를 부를 수 있고, 파일은 무엇으로 읽히고, 값은 복사되나 — 그리고 node 판은 어디서 갈리나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다. **브라우저는 부적용**(CommonJS 가 없다).
>
> ★★★ **이 주제의 본체는 격자 둘이다** — 누가 누구를 부르나 16행 · `"type"` × 확장자 × 내용 18칸, 각각 두 node 판. **1번 · 2번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **CommonJS 와 ESM 은 서로를 어떻게 부르고 어디서 막히나 — node 18 과 20 은 어느 행에서 갈리나**
> ② ★★★ **파일은 무엇으로 읽히나 — 확장자 · `"type"` · 내용**
> ③ **값은 복사되나 · ESM 에 없는 CommonJS 비품 · 막힐 때의 문구.**
>
> **선행** — [42](../42-esm-modules/2-summary.md) · [36](../36-event-loop-and-microtasks/2-summary.md) · [39](../39-async-await/2-summary.md) · [35](../35-strict-mode/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 행마다 `ok`/`blocked` 하나 · 판마다 하나**만 먼저 적어도 된다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 ECMA-262 인가, node 인가 — node 라면 몇 판부터인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 누가 누구를 부르나 — 두 판 (예측) ★★★ 이 주제의 축

```js
// js40b-43a-interop-grid.js
// Who can load whom? One row = a fresh directory with the files below + one run of this node binary.
// A row prints what the entry file printed ("ok ..."), or "blocked" + the error named on standard error (name [code]).
const fs = require("fs"), path = require("path"), { spawnSync } = require("child_process");
const ESM = 'export const a = "esm-a"; export default "esm-default";\n';
const rows = [
  ["CJS  require('./lib.cjs')", { "lib.cjs": 'exports.a = "cjs-a";\n', "main.cjs": 'console.log(require("./lib.cjs").a);\n' }],
  ["CJS  require('./lib.mjs')", { "lib.mjs": ESM, "main.cjs": 'const m = require("./lib.mjs"); console.log(m.a + " · " + m.default);\n' }],
  ["CJS  require('./lib.mjs') -- lib uses top-level await", { "lib.mjs": "await 0;\n" + ESM, "main.cjs": 'console.log(require("./lib.mjs").a);\n' }],
  ["CJS  import('./lib.mjs')", { "lib.mjs": ESM, "main.cjs": 'import("./lib.mjs").then((m) => console.log(m.a + " · " + m.default));\n' }],
  ["ESM  import d from './lib.cjs'", { "lib.cjs": 'exports.a = "cjs-a";\n', "main.mjs": 'import d from "./lib.cjs"; console.log(JSON.stringify(d));\n' }],
  ["ESM  import { a } -- exports.a = ...", { "lib.cjs": 'exports.a = "cjs-a";\n', "main.mjs": 'import { a } from "./lib.cjs"; console.log(a);\n' }],
  ["ESM  import { a } -- module.exports = { a: ... }", { "lib.cjs": 'module.exports = { a: "cjs-a" };\n', "main.mjs": 'import { a } from "./lib.cjs"; console.log(a);\n' }],
  ["ESM  import { a } -- const a = ...; module.exports = { a }", { "lib.cjs": 'const a = "cjs-a";\nmodule.exports = { a };\n', "main.mjs": 'import { a } from "./lib.cjs"; console.log(a);\n' }],
  ["ESM  import { a } -- module.exports = obj", { "lib.cjs": 'const obj = { a: "cjs-a" };\nmodule.exports = obj;\n', "main.mjs": 'import { a } from "./lib.cjs"; console.log(a);\n' }],
  ["ESM  import { a } -- exports[\"a\" + \"\"] = ...", { "lib.cjs": 'exports["a" + ""] = "cjs-a";\n', "main.mjs": 'import { a } from "./lib.cjs"; console.log(a);\n' }],
  ["ESM  require('./lib.cjs')", { "lib.cjs": 'exports.a = "cjs-a";\n', "main.mjs": 'console.log(require("./lib.cjs").a);\n' }],
  ["ESM  createRequire(import.meta.url)('./lib.cjs')", { "lib.cjs": 'exports.a = "cjs-a";\n', "main.mjs": 'import { createRequire } from "module";\nconsole.log(createRequire(import.meta.url)("./lib.cjs").a);\n' }],
  ["ESM  import './lib' (lib.mjs exists)", { "lib.mjs": ESM, "main.mjs": 'import { a } from "./lib"; console.log(a);\n' }],
  ["CJS  require('./lib') (lib.js exists)", { "lib.js": 'exports.a = "cjs-a";\n', "main.cjs": 'console.log(require("./lib").a);\n' }],
  ["ESM  import './dir' (dir/index.js exists)", { "dir/index.js": 'exports.a = "cjs-a";\n', "main.mjs": 'import d from "./dir"; console.log(d.a);\n' }],
  ["CJS  require('./dir') (dir/index.js exists)", { "dir/index.js": 'exports.a = "cjs-a";\n', "main.cjs": 'console.log(require("./dir").a);\n' }],
];
const root = path.join(__dirname, "js40b-43a-cells");
fs.rmSync(root, { recursive: true, force: true });
let blocked = 0;
rows.forEach(([label, files], i) => {
  const dir = path.join(root, String(i + 1));
  for (const [name, text] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(dir, name)), { recursive: true });
    fs.writeFileSync(path.join(dir, name), text);
  }
  const entry = Object.keys(files).find((f) => f.startsWith("main."));
  const r = spawnSync(process.execPath, [entry], { cwd: dir, encoding: "utf8" });
  let cell;
  if (r.status === 0) cell = "ok " + r.stdout.trim();
  else {
    blocked++;
    const m = r.stderr.match(/^(\w*Error)(?: \[(\w+)\])?:/m);
    const code = (r.stderr.match(/code: '(\w+)'/) || [])[1];
    cell = "blocked " + (m ? m[1] : "?") + " " + (m && m[2] ? m[2] : code || "-");
  }
  console.log(label.padEnd(62) + cell);
});
console.log("");
console.log("blocked rows: " + blocked + " / " + rows.length);
```

- ★★★ 16행 각각 — node 20 에서 `ok` 인가 `blocked` 인가? 막히면 무슨 이름·코드인가?
- ★★★ node 18 과 답이 다른 행은 어느 것인가? 마지막 두 줄의 `N / 16` 은?

### 2. `"type"` × 확장자 × 내용 (예측) ★★★

```js
// js40b-43b-type-grid.js
// Which module system runs a file? package.json "type" x file extension x file content = 18 cells.
// The file prints which one it got: typeof require is "function" only in CommonJS.
// "esm syntax" adds one line, export {}; -- it changes nothing else.
const fs = require("fs"), path = require("path"), { spawnSync } = require("child_process");
const probe = 'console.log(typeof require === "function" ? "CommonJS" : "ES module");\n';
const types = { "no package.json": null, '"type": "module"': "module", '"type": "commonjs"': "commonjs" };
const contents = { plain: probe, "esm syntax": "export {};\n" + probe };
const root = path.join(__dirname, "js40b-43b-cells");
fs.rmSync(root, { recursive: true, force: true });
let blocked = 0, total = 0, i = 0;
console.log("package.json".padEnd(20) + "file".padEnd(8) + "plain".padEnd(34) + "esm syntax");
for (const [tlabel, type] of Object.entries(types)) {
  for (const ext of [".js", ".mjs", ".cjs"]) {
    const cells = [];
    for (const text of Object.values(contents)) {
      const dir = path.join(root, String(++i));
      fs.mkdirSync(dir, { recursive: true });
      if (type) fs.writeFileSync(path.join(dir, "package.json"), JSON.stringify({ type }) + "\n");
      fs.writeFileSync(path.join(dir, "probe" + ext), text);
      const r = spawnSync(process.execPath, ["probe" + ext], { cwd: dir, encoding: "utf8" });
      total++;
      if (r.status === 0) cells.push(r.stdout.trim() + (r.stderr ? " + a warning" : ""));
      else { blocked++; const m = r.stderr.match(/^(\w*Error)(?: \[(\w+)\])?: (.*)$/m); cells.push("blocked " + (m ? m[1] + " 「" + m[3] + "」" : "?")); }
    }
    console.log(tlabel.padEnd(20) + ext.padEnd(8) + cells[0].padEnd(34) + cells[1]);
  }
}
console.log("");
console.log("blocked cells: " + blocked + " / " + total);
```

- ★★★ 18칸 각각 — `CommonJS` / `ES module` / `blocked` 중 무엇인가(node 20)?
- ★★ node 18 에서 다른 칸은? 막힌 칸의 수는 두 판에서 각각 몇인가?

### 3. CommonJS 의 카운터를 두 쪽에서 (예측) ★★★

```js
// state43c.cjs
// A CommonJS counter that writes its new value back to exports.n on every inc().
let n = 0;
exports.n = n;
exports.inc = () => { n++; exports.n = n; };
```

```js
// main43c.cjs
// From CommonJS: read exports.n through the object, and through a name taken out of it before inc().
const m = require("./state43c.cjs");
const { n } = m;
m.inc();
console.log("after inc()  m.n = " + m.n + " · destructured n = " + n);
```

```js
// main43c.mjs
// From an ES module: the default import (module.exports) and the named import n, after inc().
import m, { n, inc } from "./state43c.cjs";
import * as ns from "./state43c.cjs";
inc();
console.log("after inc()  m.n = " + m.n + " · named n = " + n + " · ns.n = " + ns.n + " · ns.default === m " + (ns.default === m));
```

- ★★★ 두 파일 각각의 한 줄은?
- ★★ 42번의 `main42a.mjs` 와 견주면 같은 `import { n }` 글자가 무엇이 다른가?

### 4. ESM 에 없는 것 · `import.meta` (예측) ★★

```js
// meta43d.mjs
// What an ES module has in place of CommonJS's wrapper variables. Paths are compared, never printed.
import { dirname } from "path";
import { fileURLToPath } from "url";
const show = (e) => e.constructor.name + " 「" + e.message + "」";
console.log("[1] typeof  require " + typeof require + " · module " + typeof module + " · exports " + typeof exports + " · __filename " + typeof __filename + " · __dirname " + typeof __dirname);
try { console.log(__dirname); } catch (e) { console.log("[2] reading __dirname: " + show(e)); }
try { console.log(require("path").sep); } catch (e) { console.log("[3] calling require: " + show(e)); }
console.log("[4] Object.keys(import.meta) " + JSON.stringify(Object.keys(import.meta)));
console.log("[5] import.meta.url starts with file:/// " + import.meta.url.startsWith("file:///"));
console.log("[6] typeof import.meta.dirname " + typeof import.meta.dirname + " · equals dirname(fileURLToPath(import.meta.url)) " + (import.meta.dirname === dirname(fileURLToPath(import.meta.url))));
console.log("[7] typeof import.meta.resolve " + typeof import.meta.resolve);
```

```js
// meta43d.cjs
// The same first question in CommonJS.
console.log("[1] typeof  require " + typeof require + " · module " + typeof module + " · exports " + typeof exports + " · __filename " + typeof __filename + " · __dirname " + typeof __dirname);
console.log("[2] this === module.exports " + (this === module.exports));
```

- ★★ `meta43d.mjs` 의 일곱 줄은 node 20 에서? node 18 에서 달라지는 줄은?
- ★ `meta43d.cjs` 의 두 줄은?

### 5. 막힐 때의 문구 (예측) ★★

```js
// noext43e.mjs
// A relative import without the file extension.
import { a } from "./lib43e";
console.log(a);
```

```js
// reqesm43e.mjs
// require inside an ES module, not caught.
console.log("reqesm43e.mjs: first line");
const p = require("path");
```

```js
// obj43e.cjs
// A CommonJS module that assigns an object held in a variable.
const obj = { a: "cjs-a" };
module.exports = obj;
```

```js
// named43e.mjs
// A named import from that CommonJS module.
import { a } from "./obj43e.cjs";
console.log(a);
```

```js
// reqmjs43e.cjs
// require() of an ES module from CommonJS.
console.log(require("./lib43e.mjs").a);
```

- ★★ 네 파일 각각 — node 20 에서 무슨 에러이고, 표준 출력은 몇 줄인가? node 18 에서 달라지는 파일은?
- ★ 확장자 없는 `import` 의 문구는 옆의 `lib43e.mjs` 를 가리켜 주나?

### 6. 판정 규칙의 우선순위 (왜) ★★★

- ★★★ `.mjs` · `.cjs` · `"type"` · 문법 감지 — 무엇이 무엇을 이기나?
- ★★ 문법 감지는 어떤 파일에만 적용되고, 몇 판에서 기본으로 켜졌나?

### 7. lexer 가 하는 일과 못 하는 일 (왜) ★★

- ★★ ESM 이 CommonJS 를 **이름으로** 가져올 때 node 는 그 이름을 어떻게 아나? 왜 「실행해 보고」가 아닌가?
- ★ 그 방식이 1번의 이름 있는 가져오기 다섯 행과 3번의 `named n` 을 각각 어떻게 설명하나?

### 8. 층을 가른다 (경계) ★★

- ★★ `require` · `module.exports` · `"type"` · `import.meta.dirname` · `import()` 문법 — 각각 ECMA-262 인가 node 인가?
- ★ 브라우저에서 이 주제의 격자를 돌릴 수 있나?

### 9. 같은 패키지를 두 길로 (경계) ★★

```js
// main43f.mjs
// One specifier, "#counter", loaded by import and by require. package.json maps the two conditions to two files.
import { count, bump } from "#counter";
import { createRequire } from "module";
const viaRequire = createRequire(import.meta.url)("#counter");
bump();
bump();
console.log("after two bump() through import: import side count = " + count + " · require side count = " + viaRequire.count);
```

- ★★ `package.json` 의 `"imports"` 가 `#counter` 를 조건마다 다른 파일로 가르면, 두 `bump()` 뒤의 두 숫자는? 두 본문은 각각 몇 번 도나?

### 10. 36번 · 42번과 이어 보기 (연결) ★★

- ★★ 36번에서 같은 파일의 `nextTick` 순위는 CommonJS 와 ES 모듈에서 각각 몇 위였나? 그것은 이 주제의 어느 규칙과 이어지나?
- ★ 42번의 라이브 바인딩과 이 주제의 3번은 무엇이 한 쌍인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
