# js/syntax/43 — CJS 와 ESM 상호운용: 「CommonJS 는 명세 밖의 node 규약이다 — 누가 누구를 부르나, 파일이 무엇으로 읽히나, 값이 복사되나를 node 판이 정한다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — 격자가 둘이다. ① **상호운용 격자 16행**(CJS → CJS · CJS → ESM · ESM → CJS · 확장자 없는 지정자 · 디렉토리)의 「**막힌 행 N / 16**」과 「**node 18 과 node 20 이 갈린 행 N / 16**」(동작 (1)) · ② **`"type"` 필드 × 확장자 × 내용 18칸**의 「**막힌 칸 N / 18**」(동작 (2)). 둘 다 스크립트가 마지막 줄로 찍는다.
> ★★ 보조로 **① 로그 심기**(CommonJS 의 복사 대 ESM 의 라이브 — 동작 (3) · 한 지정자가 두 파일로 갈리는 것 — 동작 (6))와 **④ 예외의 이름 + 문구**(`ERR_REQUIRE_ESM` · `ERR_MODULE_NOT_FOUND` · `Named export 'a' not found` — 동작 (5))를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [Node.js v20 — Modules: CommonJS · 「Loading ECMAScript modules using `require()`」](https://nodejs.org/docs/latest-v20.x/api/modules.html) — 이력 「**v20.17.0 추가** · **v20.19.0 에서 `--experimental-require-module` 플래그 없이** · v20.19.0 부터 **실험 경고를 기본으로 안 낸다**」 · 「**이름공간 객체를 돌려준다**」 · 「최상위 `await` 가 있으면 **`ERR_REQUIRE_ASYNC_MODULE`**」
> - [Node.js v20 — Modules: ECMAScript modules](https://nodejs.org/docs/latest-v20.x/api/esm.html) — 「**`import` 로 상대·절대 지정자를 해석할 때는 파일 확장자를 반드시 적어야 한다** · 디렉토리 색인도 끝까지 적어야 한다」 · 「`require`·`exports`·`module.exports` 없음 · `__filename`·`__dirname` 없음 → `import.meta.filename`·`import.meta.dirname`(**v20.11.0 추가**)」 · 「CommonJS 의 이름 있는 내보내기는 **cjs-module-lexer 정적 분석**으로 정한다 — **라이브 갱신이나 나중에 더한 내보내기는 감지하지 않는다**」 · `import.meta.resolve` **v20.6.0 에서 플래그 없이**
> - [Node.js v20 — Modules: Packages](https://nodejs.org/docs/latest-v20.x/api/packages.html) — 「`.mjs` · `"type": "module"` 인 `.js` 는 ES 모듈 / `.cjs` · `"type": "commonjs"` 인 `.js` 는 CommonJS」 · 「**`type` 이 없으면 `.js` 는 CommonJS**」 · 「**Syntax detection — v20.10.0 추가 · v20.19.0 에서 기본으로 켜짐**: `type` 이 없는 `.js` 에 ES 모듈 문법(`import`·`export` 문 · `import.meta` · 최상위 `await` …)이 있으면 ES 모듈로 다룬다」
>
> ★★★ **CommonJS 는 ECMA-262 에 없다.** `require`·`module.exports`·`"type"` 필드·확장자 규칙·`import.meta` 의 **속성**은 전부 **node 의 것**이다. 이 문서의 「보장」은 **node 문서의 문장**이고, 그것도 **판마다 바뀐다**(이 문서의 판 격자가 그 증거다).
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다. `cd <디렉토리> && node20 <파일>` 꼴 배너는 **그 디렉토리 안에서 상대 경로로** 던졌다. 격자는 **칸마다 새 디렉토리 · 새 프로세스**다.
> ★★ **node 의 에러 문구에는 절대 경로가 박힌다** — 그 블록은 스크립트 안에서 **`sed "s#$PWD#<dir>#g"`** 로 지웠다.
> ★ **Chrome 은 이 주제에 부적용이다** — 브라우저에는 CommonJS 도 `"type"` 필드도 없다(판별 블록의 `host require … no`).
> ★★★ **성능은 재지 않았다** — 「`require` 가 빠르다/느리다」를 **쓰지 않는다.**
>
> **버전 — 층이 넷이다**
>
> | 층 | 무엇 | 판 | 이 머신에서 |
> |---|---|---|---|
> | 언어(ECMA-262) | `import`/`export` · `import()` · `import.meta` 문법 | ES2015 · **ES2020** · **ES2020** | 42번 |
> | ★★★ **Node 호스트 — 모듈 판정** | `.mjs`/`.cjs`/`"type"` · **`type` 없는 `.js` 의 문법 감지** | 감지는 **v20.19.0 에서 기본**(문서) | ★★ **node 18 은 `export {}` 가 든 `.js` 를 거절, node 20 은 ES 모듈로 돌렸다**(동작 (2)) |
> | ★★★ **Node 호스트 — 상호운용** | `require(esm)` | **v20.19.0 에서 플래그 없이**(문서) | ★★★ **node 18 `ERR_REQUIRE_ESM`, node 20 은 됐다**(동작 (1)) |
> | Node 호스트 — `import.meta` 속성 | `dirname`·`filename` | **v20.11.0**(문서) | node 18 `undefined`, node 20 `string`(동작 (4)) |
>
> ★★ **README 43행은 판을 적지 않는다.** 위 node 판은 **v20 문서의 이력**에서 뗐고, 판별은 **두 판 격자**로 했다. 브리핑의 「node 20.19 에서 `require(esm)` 이 풀렸다」는 **v20 문서 이력과 일치**했다(22 계열은 이 머신에 없어 **돌리지 않았다**).
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 상호운용 16행 「`blocked rows N / 16`」 · 「`differ N / 16`」(동작 (1)) · `type` × 확장자 × 내용 18칸 「`blocked cells N / 18`」(동작 (2)) |
> | ★★ **① 로그 심기** | CommonJS 의 값 복사 · ESM 의 이름 있는 가져오기가 **CommonJS 를 가져올 때는 복사**가 되는 것(동작 (3)) · 한 지정자가 두 파일로 갈려 **상태가 둘**이 되는 것(동작 (6)) |
> | ★★ **④ 예외의 이름 + 문구** | `Error [ERR_…]` 의 코드 · `SyntaxError: Named export …` 전문(동작 (5)) |
> | ★ **부적용 — ③ 브랜드 태그** | `require(esm)` 이 돌려준 것이 이름공간 객체인지는 `[Symbol.toStringTag]` 대신 **node 문서 문장 + 키 목록**으로 봤다 — 이 주제는 객체의 종류보다 **「막혔나」** 가 본체다 |
> | ★ **부적용 — Chrome** | 브라우저에는 CommonJS 가 없다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 · 에러 문구의 **절대 경로**(블록 안에서 `<dir>` 로 지웠다) | ★★★ 격자의 모든 칸 · 에러 **코드**(`ERR_…`) · 종료 코드 · 로그 값 |
> | ★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) | ★★★ **두 node 판 사이의 차이는 흔들림이 아니라 판의 차이**다 — 그것이 이 주제의 절반이다 |
>
> **선행** — [42 — ESM 모듈](../42-esm-modules/2-summary.md)(직접 선행 — ★★★ **라이브 바인딩 `0 → 1 → 2` 대 CommonJS `0`** 이 거기 동작 (1)에 있다 · 이 문서는 그 **CommonJS 쪽**을 넓힌다) ·
> [36 — 이벤트 루프](../36-event-loop-and-microtasks/2-summary.md)(★★★ **CJS 대 ESM 의 첫 증거** — 같은 파일에서 `nextTick` 이 **CommonJS 에서 4위, ES 모듈에서 9위** · 「`nextTick` 은 마이크로태스크보다 먼저」는 **CommonJS 에서만** 참이었다) ·
> [39 — `async`/`await`](../39-async-await/2-summary.md)(최상위 `await` 는 `.mjs` 가 아니라 **모듈 코드인가**가 기준 — `--input-type=module` 로도 돈다) ·
> [35 — 엄격 모드](../35-strict-mode/2-summary.md)(모듈은 늘 엄격 — **같은 파일을 `.mjs` 와 CommonJS 로** 돌려 증명했다).
>
> ★★ **경계 — 연혁** — README 는 이 주제의 정본을 [`history/js/03-Node-런타임.md`](../../../../../../history/js/03-Node-런타임.md) 로 적는다. ★★ **그 문서에는 상호운용 절이 없다** — CommonJS 는 **「1. Node.js의 탄생 (2009)」 의 「핵심 아이디어: 이벤트 루프와 논블로킹 I/O」** 안에서 한 문단(「**후일 ES Modules `import`/`export` 와 공존하게 된다**」)과 용어 한 줄로만 나온다.
> 상호운용의 연혁은 [`history/js/05-빌드-생태계.md`](../../../../../../history/js/05-빌드-생태계.md) 의 **「1.2 CommonJS — 서버의 동기 모듈 (2009)」** 과 **「1.4 ESM — ES2015 표준의 수렴점 (2015)」** 이 더 가깝다 — 뒤 절이 「**CommonJS 와 ESM 은 한동안 어색하게 공존했고(`.mjs` 확장자, `"type": "module"`, dual package hazard 같은 상처가 그 흔적이다)**」라고 적는다. **그쪽은 그 상처의 연혁까지**, 여기는 **그 상처가 지금 두 node 판에서 어느 칸에 나나**부터다(동작 (1)·(2)·(6)). 두 문서 모두 고치지 않았다.

```text
===== ./js40b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           no
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           no
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             yes
Google Chrome 151.0.7922.173
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           yes
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             no
```

세 판 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 3 · differs 3 · node only 3`

## 한눈에 — 쉽게 말하면

**CommonJS 와 ESM 은 「같은 건물에 있는 두 우편 체계」다. CommonJS 는 부르면 그 자리에서 소포를 뜯어 주는 창구(`require` — 동기 함수 호출)이고, ESM 은 입주 전에 주소록을 다 맞춰 두는 체계(`import` — 연결 후 평가)다. 건물 관리인(node)이 어느 방이 어느 체계인지(확장자·`"type"`)를 정하고, 두 체계 사이의 통로를 판마다 조금씩 넓혀 왔다.**

- ★★★ **ESM → CommonJS 는 늘 열려 있었다** — `import d from "./x.cjs"` 는 `module.exports` 를 준다. 단 **이름 있는 가져오기는 관리인이 소포 겉면을 훑어 찾은 이름만**(cjs-module-lexer) 된다.
- ★★★ **CommonJS → ESM 은 판이 정한다** — `require("./x.mjs")` 는 **node 18 에서 막혔고 node 20.19 에서 열렸다.** 최상위 `await` 가 있는 방은 **node 20 에서도 막힌다.** `import()` 는 **늘** 된다.
- ★★ **CommonJS 는 사진을 준다** — `module.exports` 에 담긴 **그때의 값**이다. ESM 이 CommonJS 를 이름으로 가져와도 **사진**이다(평가가 끝난 순간의 값).
- ★★ **ESM 방에는 CommonJS 의 비품이 없다** — `require`·`__dirname`·`module` 이 없다. 주소는 **끝까지 적어야** 한다(확장자 없는 `./lib` 는 못 찾는다).

```text
                          누가 부르나 ─▶
                          CommonJS (.cjs · type 없음/commonjs 인 .js)        ESM (.mjs · type: module 인 .js)
   불리는 쪽 ▼
   CommonJS               require(): 됨                                     import d: 됨 (module.exports)
                                                                            import { a }: lexer 가 찾은 이름만
                                                                            require(): 없음 (createRequire 로만)
   ESM                    require(): node 18 ✕ · node 20.19 ○ (TLA 면 ✕)      import: 됨 — 확장자 필수 · 디렉토리 ✕
                          import(): 됨 (Promise)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 그 자리에서 뜯어 주는 창구 | `require()` — 동기 함수 호출, 그 줄에서 평가 | 42번 동작 (4) · 동작 (1) |
| 입주 전에 맞춘 주소록 | ESM 의 연결 → 평가 | 42번 |
| 어느 방이 어느 체계인가 | 확장자(`.mjs`/`.cjs`) · `package.json` 의 `"type"` · `type` 없는 `.js` 의 **문법 감지**(node 20.19) | 동작 (2) |
| 소포 겉면을 훑는 관리인 | **cjs-module-lexer** — CommonJS 소스를 **실행하지 않고** 훑어 이름 있는 내보내기를 고른다 | 동작 (1)의 `import { a }` 다섯 행 |
| 사진 | CommonJS 쪽 값의 복사(구조 분해 · ESM 의 이름 있는 가져오기) | 동작 (3) |
| 통로가 넓어진다 | `require(esm)`(v20.19.0) · 문법 감지(v20.19.0) · `import.meta.dirname`(v20.11.0) | 동작 (1)·(2)·(4) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**라이브러리를 ESM 전용으로 바꾸자 CommonJS 사용자에게 `ERR_REQUIRE_ESM`**」,
「**`import { foo } from 'cjs-lib'` 이 `Named export 'foo' not found`**」,
「**`.js` 를 `.mjs` 처럼 쓰다 `import './util'` 이 `ERR_MODULE_NOT_FOUND`**」,
「**같은 패키지를 `import` 와 `require` 로 부르자 상태가 둘로 갈렸다**」가 그것이다(동작 (1)·(5)·(6)).

> **CommonJS** — `require()` 로 가져오고 `module.exports`(또는 `exports.x`)로 내보내는 **node 의 모듈 규약**. ECMA-262 에는 없다.\
> 예: `const { a } = require("./lib.cjs");` · `module.exports = { a };`

## 이 주제가 답하려는 질문

1. **CommonJS 와 ESM 은 서로를 어떻게 부르고, 어디서 막히나** — `require(esm)` · `import cjs` 의 기본·이름 있는 가져오기 · 확장자 없는 지정자 · 디렉토리, 그리고 **node 18 과 20 은 어느 행에서 갈리나**?
2. **한 파일은 무엇으로 읽히나** — `"type"` 필드 × 확장자 × 내용(ES 모듈 문법이 있나)의 18칸에서?
3. **CommonJS 의 값은 복사인가** — ESM 이 CommonJS 를 가져올 때는? ESM 에 없는 CommonJS 비품(`require`·`__dirname`)은 무엇으로 대신하나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 상호운용 격자 — 16행 × 두 판

**언제 쓰나** — CommonJS 프로젝트에서 ESM 라이브러리를 쓰거나 그 반대일 때 · 라이브러리의 모듈 형식을 바꿀 때.
★★★ 행마다 **새 디렉토리**에 파일을 쓰고 **이 node 로** 진입 파일을 돌린다. 막히면 표준 오류에서 **에러 이름과 코드**만 뗀다(경로가 박힌 문구는 동작 (5)에서 따로).

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

```sh
# js40b-43a-interop.sh
#!/usr/bin/env bash
# The interop grid (js40b-43a-interop-grid.js) on node20, then on node18 -- and the rows whose answers differ.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
a="$("$N20" js40b-43a-interop-grid.js)"
b="$("$N18" js40b-43a-interop-grid.js)"
echo "--- node20"; printf '%s\n' "$a"
echo "--- node18"; printf '%s\n' "$b"
rows="$(printf '%s\n' "$a" | grep -c '^[CE][JS][SM]  ' || true)"
d="$(diff <(printf '%s\n' "$a" | grep '^[CE][JS][SM]  ') <(printf '%s\n' "$b" | grep '^[CE][JS][SM]  ') | grep -c '^<' || true)"
echo ""
echo "rows where node18 and node20 differ: $d / $rows"
```

```text
===== ./js40b-43a-interop.sh (exit=0) =====
--- node20
CJS  require('./lib.cjs')                                     ok cjs-a
CJS  require('./lib.mjs')                                     ok esm-a · esm-default
CJS  require('./lib.mjs') -- lib uses top-level await         blocked Error ERR_REQUIRE_ASYNC_MODULE
CJS  import('./lib.mjs')                                      ok esm-a · esm-default
ESM  import d from './lib.cjs'                                ok {"a":"cjs-a"}
ESM  import { a } -- exports.a = ...                          ok cjs-a
ESM  import { a } -- module.exports = { a: ... }              blocked SyntaxError -
ESM  import { a } -- const a = ...; module.exports = { a }    ok cjs-a
ESM  import { a } -- module.exports = obj                     blocked SyntaxError -
ESM  import { a } -- exports["a" + ""] = ...                  blocked SyntaxError -
ESM  require('./lib.cjs')                                     blocked ReferenceError -
ESM  createRequire(import.meta.url)('./lib.cjs')              ok cjs-a
ESM  import './lib' (lib.mjs exists)                          blocked Error ERR_MODULE_NOT_FOUND
CJS  require('./lib') (lib.js exists)                         ok cjs-a
ESM  import './dir' (dir/index.js exists)                     blocked Error ERR_UNSUPPORTED_DIR_IMPORT
CJS  require('./dir') (dir/index.js exists)                   ok cjs-a

blocked rows: 7 / 16
--- node18
CJS  require('./lib.cjs')                                     ok cjs-a
CJS  require('./lib.mjs')                                     blocked Error ERR_REQUIRE_ESM
CJS  require('./lib.mjs') -- lib uses top-level await         blocked Error ERR_REQUIRE_ESM
CJS  import('./lib.mjs')                                      ok esm-a · esm-default
ESM  import d from './lib.cjs'                                ok {"a":"cjs-a"}
ESM  import { a } -- exports.a = ...                          ok cjs-a
ESM  import { a } -- module.exports = { a: ... }              blocked SyntaxError -
ESM  import { a } -- const a = ...; module.exports = { a }    ok cjs-a
ESM  import { a } -- module.exports = obj                     blocked SyntaxError -
ESM  import { a } -- exports["a" + ""] = ...                  blocked SyntaxError -
ESM  require('./lib.cjs')                                     blocked ReferenceError -
ESM  createRequire(import.meta.url)('./lib.cjs')              ok cjs-a
ESM  import './lib' (lib.mjs exists)                          blocked Error ERR_MODULE_NOT_FOUND
CJS  require('./lib') (lib.js exists)                         ok cjs-a
ESM  import './dir' (dir/index.js exists)                     blocked Error ERR_UNSUPPORTED_DIR_IMPORT
CJS  require('./dir') (dir/index.js exists)                   ok cjs-a

blocked rows: 8 / 16

rows where node18 and node20 differ: 2 / 16
```

- ★★★ **마지막 줄 — `rows where node18 and node20 differ: 2 / 16`**, 막힌 행은 **node 20 이 `7 / 16`, node 18 이 `8 / 16`** 이다.
  갈린 둘은 **`require('./lib.mjs')`** — node 18 **`ERR_REQUIRE_ESM`**, node 20 **`ok esm-a · esm-default`** — 와 **최상위 `await` 가 든 `require('./lib.mjs')`** — node 18 **`ERR_REQUIRE_ESM`**, node 20 **`ERR_REQUIRE_ASYNC_MODULE`**(여전히 막히지만 **이유가 바뀌었다**)다.
- ★★★ **`import()` 는 두 판 다 됐다** — CommonJS 에서 ESM 을 쓰는 **판을 안 타는** 길이다. 대신 결과가 **프라미스**다(42번 동작 (5)).
- ★★★ **ESM 에서 CommonJS 의 이름 있는 가져오기 — 다섯 행 중 둘만 됐다.** `exports.a = …` 와 `const a = …; module.exports = { a }`(단축 속성)는 **됐고**, `module.exports = { a: "…" }`(값이 문자열인 속성) · `module.exports = obj`(변수) · `exports["a" + ""]`(계산된 이름)는 **`SyntaxError`**. **기본 가져오기**(`import d`)는 **늘 된다** — `{"a":"cjs-a"}`, 곧 `module.exports` 다.
  ★ **`{ a: "…" }` 가 막힌 것**은 예상 밖이었다 — lexer 는 CommonJS 를 **실행하지 않고 훑기만** 하므로 **어떤 모양을 알아보나**는 lexer 의 규칙이다. node 문서가 적는 것은 「정적 분석으로 정한다」까지다.
- ★★ **ESM 안의 `require` 는 `ReferenceError`**, **`createRequire(import.meta.url)` 로 만든 `require` 는 된다.**
- ★★ **확장자 없는 `import './lib'` 은 `ERR_MODULE_NOT_FOUND`**, 같은 모양의 **`require('./lib')` 는 된다**(`lib.js` 를 찾아냈다) · **디렉토리 `import './dir'` 은 `ERR_UNSUPPORTED_DIR_IMPORT`**, **`require('./dir')` 은 `index.js` 를 찾아 됐다.** node 문서의 「**확장자를 반드시 적어야 한다 · 디렉토리 색인도 끝까지**」 그대로다.

```text
   CommonJS 소스를 ESM 이 이름으로 가져올 때 — lexer 가 「찾은」 모양 (두 node 판 같음)

   exports.a = "…"                     ○  import { a } 됨
   const a = "…"; module.exports = { a } ○
   module.exports = { a: "…" }          ✕  SyntaxError (Named export 'a' not found)
   module.exports = obj                 ✕
   exports["a" + ""] = "…"              ✕
   ─────────────────────────────────────────────────────────────
   어느 모양이든  import d from "./lib.cjs"  →  d === module.exports   (늘 된다)
```

### (2) ★★★ `"type"` × 확장자 × 내용 — 18칸 × 두 판

**언제 쓰나** — `package.json` 에 `"type": "module"` 을 넣을지 · `.js`/`.mjs`/`.cjs` 중 무엇으로 쓸지 정할 때.
★★ 파일은 **`typeof require`** 로 자기가 무엇으로 읽혔나를 찍는다. 「esm syntax」 칸은 **`export {};` 한 줄**만 더한다 — 다른 것은 안 바꾼다.

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

```sh
# js40b-43b-type.sh
#!/usr/bin/env bash
# The "type" x extension x content grid (js40b-43b-type-grid.js) on node20, then on node18 -- and the cells that differ.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
a="$("$N20" js40b-43b-type-grid.js)"
b="$("$N18" js40b-43b-type-grid.js)"
echo "--- node20"; printf '%s\n' "$a"
echo "--- node18"; printf '%s\n' "$b"
d="$(diff <(printf '%s\n' "$a" | sed -n '2,10p') <(printf '%s\n' "$b" | sed -n '2,10p') | grep -c '^<' || true)"
echo ""
echo "rows (of 9) where node18 and node20 differ: $d"
```

```text
===== ./js40b-43b-type.sh (exit=0) =====
--- node20
package.json        file    plain                             esm syntax
no package.json     .js     CommonJS                          ES module
no package.json     .mjs    ES module                         ES module
no package.json     .cjs    CommonJS                          blocked SyntaxError 「Unexpected token 'export'」
"type": "module"    .js     ES module                         ES module
"type": "module"    .mjs    ES module                         ES module
"type": "module"    .cjs    CommonJS                          blocked SyntaxError 「Unexpected token 'export'」
"type": "commonjs"  .js     CommonJS                          blocked SyntaxError 「Unexpected token 'export'」
"type": "commonjs"  .mjs    ES module                         ES module
"type": "commonjs"  .cjs    CommonJS                          blocked SyntaxError 「Unexpected token 'export'」

blocked cells: 4 / 18
--- node18
package.json        file    plain                             esm syntax
no package.json     .js     CommonJS                          blocked SyntaxError 「Unexpected token 'export'」
no package.json     .mjs    ES module                         ES module
no package.json     .cjs    CommonJS                          blocked SyntaxError 「Unexpected token 'export'」
"type": "module"    .js     ES module                         ES module
"type": "module"    .mjs    ES module                         ES module
"type": "module"    .cjs    CommonJS                          blocked SyntaxError 「Unexpected token 'export'」
"type": "commonjs"  .js     CommonJS                          blocked SyntaxError 「Unexpected token 'export'」
"type": "commonjs"  .mjs    ES module                         ES module
"type": "commonjs"  .cjs    CommonJS                          blocked SyntaxError 「Unexpected token 'export'」

blocked cells: 5 / 18

rows (of 9) where node18 and node20 differ: 1
```

```text
                       plain(typeof require 만)          esm syntax(export {}; 한 줄 더)
   .mjs                ES module  (type 무관)             ES module
   .cjs                CommonJS   (type 무관)             ✕ SyntaxError 「Unexpected token 'export'」
   .js · type:module   ES module                          ES module
   .js · type:commonjs CommonJS                           ✕ SyntaxError
   .js · type 없음      CommonJS                           node 20: ES module   ← 문법 감지 (v20.19.0 기본)
                                                          node 18: ✕ SyntaxError
```

- ★★★ **확장자가 `type` 을 이긴다** — `.mjs` 는 `type` 이 무엇이든 **ES module**, `.cjs` 는 **CommonJS** 다. `type` 이 가르는 것은 **`.js` 뿐**이다.
- ★★★ **판이 갈린 칸은 하나**(`rows (of 9) … differ: 1`) — **`type` 없는 `.js` 에 `export {};`** 가 들면 **node 20 은 `ES module` 로 돌렸고, node 18 은 `SyntaxError`** 였다(막힌 칸 node 20 `4 / 18` · node 18 `5 / 18`). node 문서의 「**Syntax detection — v20.19.0 에서 기본으로 켜짐**」이다.
- ★★ **같은 `plain` 파일은 `type` 없는 `.js` 에서 두 판 다 `CommonJS`** — 감지는 **ES 모듈 문법이 있을 때만** 모듈로 바꾼다. 「`type` 이 없으면 `.js` 는 CommonJS」가 기본값인 것은 그대로다.
- ★ **CommonJS 로 정해진 파일의 `export` 는 `SyntaxError 「Unexpected token 'export'」`** — CommonJS 는 **스크립트 문법**으로 파싱된다(35번의 「스크립트」 쪽).

### (3) ★★★ CommonJS 의 복사 · ESM 이 CommonJS 를 가져올 때 — 42번과 한 쌍

**언제 쓰나** — CommonJS 모듈이 **상태**를 내보낼 때 · 그것을 ESM 에서 가져올 때.
★★ 카운터가 `inc()` 마다 **`exports.n` 에 새 값을 다시 써 넣는다**(42번의 `counter42a.cjs` 는 안 써 넣었다 — 그래서 `0` 이었다).

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

```text
===== cd js40b-43c && node20 main43c.cjs (exit=0) =====
after inc()  m.n = 1 · destructured n = 0
```

```js
// main43c.mjs
// From an ES module: the default import (module.exports) and the named import n, after inc().
import m, { n, inc } from "./state43c.cjs";
import * as ns from "./state43c.cjs";
inc();
console.log("after inc()  m.n = " + m.n + " · named n = " + n + " · ns.n = " + ns.n + " · ns.default === m " + (ns.default === m));
```

```text
===== cd js40b-43c && node20 main43c.mjs (exit=0) =====
after inc()  m.n = 1 · named n = 0 · ns.n = 0 · ns.default === m true
```

```text
   state43c.cjs 가 끝난 순간      exports = { n: 0, inc }
                                      │
   ─ CommonJS 쪽 ─                    │                   ─ ESM 쪽 ─
   m = require(…)   ─ 같은 객체 ──────┤──── 같은 객체 ─── import m (default) = module.exports
   { n } = m        ─ 지금의 0 복사    │                   import { n }  ─ lexer 가 찾은 이름을 「평가가 끝난 순간」 복사 = 0
                                      ▼
   inc()  ─▶ exports.n = 1           m.n = 1              m.n = 1 · named n = 0 · ns.n = 0

   42번의 ESM(counter42a.mjs):  import { n } ─▶ 바인딩 자체 ─▶ 0 → 1 → 2
```

- ★★★ **CommonJS — `m.n = 1 · destructured n = 0`.** 객체 `m` 은 **같은 `exports`** 라 새 값을 보지만, 구조 분해한 `n` 은 **그 순간의 값**이다.
- ★★★ **ESM 이 CommonJS 를 가져오면 — `m.n = 1 · named n = 0 · ns.n = 0`.** 기본 가져오기 `m` 은 `module.exports` 객체라 새 값을 보지만, **이름 있는 가져오기 `n` 은 `0` 에 멈췄다** — node 문서의 「**라이브 갱신은 감지하지 않는다**」다. `ns.default === m true`.
- ★★ **42번과 한 쌍** — **ESM → ESM 은 바인딩**(`0 → 1 → 2`), **CommonJS 는 어느 쪽에서 봐도 값**(객체의 속성을 매번 읽을 때만 새 값)이다. 같은 `import { n }` 글자가 **상대가 ESM 이냐 CommonJS 냐**로 뜻이 갈린다.

### (4) ★★ ESM 에 없는 CommonJS 비품 — `require` · `__dirname` · 그리고 `import.meta`

**언제 쓰나** — CommonJS 스크립트를 `.mjs` 로 옮길 때 · 모듈 파일의 위치가 필요할 때.
★ 경로는 **찍지 않고 비교만** 한다(절대 경로가 문서로 새지 않게).

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

```text
===== cd js40b-43d && node20 meta43d.mjs (exit=0) =====
[1] typeof  require undefined · module undefined · exports undefined · __filename undefined · __dirname undefined
[2] reading __dirname: ReferenceError 「__dirname is not defined」
[3] calling require: ReferenceError 「require is not defined」
[4] Object.keys(import.meta) ["dirname","filename","resolve","url"]
[5] import.meta.url starts with file:/// true
[6] typeof import.meta.dirname string · equals dirname(fileURLToPath(import.meta.url)) true
[7] typeof import.meta.resolve function
```

```text
===== cd js40b-43d && node18 meta43d.mjs (exit=0) =====
[1] typeof  require undefined · module undefined · exports undefined · __filename undefined · __dirname undefined
[2] reading __dirname: ReferenceError 「__dirname is not defined」
[3] calling require: ReferenceError 「require is not defined」
[4] Object.keys(import.meta) ["resolve","url"]
[5] import.meta.url starts with file:/// true
[6] typeof import.meta.dirname undefined · equals dirname(fileURLToPath(import.meta.url)) false
[7] typeof import.meta.resolve function
```

```js
// meta43d.cjs
// The same first question in CommonJS.
console.log("[1] typeof  require " + typeof require + " · module " + typeof module + " · exports " + typeof exports + " · __filename " + typeof __filename + " · __dirname " + typeof __dirname);
console.log("[2] this === module.exports " + (this === module.exports));
```

```text
===== cd js40b-43d && node20 meta43d.cjs (exit=0) =====
[1] typeof  require function · module object · exports object · __filename string · __dirname string
[2] this === module.exports true
```

```text
   CommonJS 에 있던 것        ESM 에서 (두 node 판)                           판을 안 타는 길
   require                   ReferenceError                                   import · import() · createRequire(import.meta.url)
   module · exports           ReferenceError                                   export
   __filename                ReferenceError  → import.meta.filename (20.11+)   fileURLToPath(import.meta.url)
   __dirname                 ReferenceError  → import.meta.dirname  (20.11+)   dirname(fileURLToPath(import.meta.url))
   this (= module.exports)   undefined
```

- ★★★ **ESM 에서 `require`·`module`·`exports`·`__filename`·`__dirname` 은 전부 `typeof … undefined`**, 읽으면 **`ReferenceError`** — CommonJS 에서는 전부 있다(`function · object · object · string · string`). node 문서가 이것들을 「**CommonJS 래퍼 변수**(wrapper variables)」라 부른다 — CommonJS 쪽에만 있는 이름이다.
- ★★★ **`import.meta.dirname` — node 20 `string`(그리고 `dirname(fileURLToPath(import.meta.url))` 과 같다), node 18 `undefined`.** 키 목록도 node 20 은 `["dirname","filename","resolve","url"]`, node 18 은 `["resolve","url"]` 이다(문서 — **v20.11.0 추가**). **판을 타지 않는 길**은 `fileURLToPath(import.meta.url)` 이다.
- ★★ **CommonJS 최상위의 `this` 는 `module.exports`**(`true`) — ESM 은 `undefined` 였다(42번 동작 (2)).
- ★ **잡힌 `ReferenceError` 의 문구는 `require is not defined`** 인데, **잡히지 않고 node 가 찍을 때는** `require is not defined in ES module scope, you can use import instead` 로 **안내가 붙었다**(동작 (5)) — 같은 에러를 node 가 **찍으면서 덧붙인** 것이다.

### (5) ★★ 막힐 때의 문구 — 전문(경로만 `<dir>`)

**언제 쓰나** — 위 격자의 `blocked` 행이 실제로 무엇을 말하는지 볼 때.
★★ 표준 오류를 **에러 이름이 나오는 줄부터 첫 스택 줄 전까지** 잘랐다(자르는 명령과 경로 치환은 스크립트 안에 있다).

```js
// lib43e.mjs
// An ES module with one named export.
export const a = "esm-a";
```

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

```sh
# js40b-43e-messages.sh
#!/usr/bin/env bash
# The error texts of four blocked loads (files in js40b-43e/), on node20 and node18.
# Standard error is cut to the part that explains the error: from the line that names it down to the first stack line ("    at ").
# This directory's absolute path is replaced by <dir>.
set -u -o pipefail
cd "$(dirname "$0")/js40b-43e"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for f in noext43e.mjs reqesm43e.mjs named43e.mjs reqmjs43e.cjs; do
  for v in 20 18; do
    [ $v = 18 ] && n="$N18" || n="$N20"
    echo "--- node$v $f"
    out="$("$n" "$f" 2>/dev/null)"
    err="$("$n" "$f" 2>&1 >/dev/null)"
    e=$?
    printf '%s\n' "$err" | sed "s#$PWD#<dir>#g" | sed -n '/^[A-Za-z]*Error/,/^    at /p' | sed '$d'
    echo "(exit $e · standard output: $(printf '%s' "$out" | grep -c '' || true) lines)"
  done
done
```

```text
===== ./js40b-43e-messages.sh (exit=0) =====
--- node20 noext43e.mjs
Error [ERR_MODULE_NOT_FOUND]: Cannot find module '<dir>/lib43e' imported from <dir>/noext43e.mjs
(exit 1 · standard output: 0 lines)
--- node18 noext43e.mjs
Error [ERR_MODULE_NOT_FOUND]: Cannot find module '<dir>/lib43e' imported from <dir>/noext43e.mjs
(exit 1 · standard output: 0 lines)
--- node20 reqesm43e.mjs
ReferenceError: require is not defined in ES module scope, you can use import instead
(exit 1 · standard output: 1 lines)
--- node18 reqesm43e.mjs
ReferenceError: require is not defined in ES module scope, you can use import instead
(exit 1 · standard output: 1 lines)
--- node20 named43e.mjs
SyntaxError: Named export 'a' not found. The requested module './obj43e.cjs' is a CommonJS module, which may not support all module.exports as named exports.
CommonJS modules can always be imported via the default export, for example using:

import pkg from './obj43e.cjs';
const { a } = pkg;

(exit 1 · standard output: 0 lines)
--- node18 named43e.mjs
SyntaxError: Named export 'a' not found. The requested module './obj43e.cjs' is a CommonJS module, which may not support all module.exports as named exports.
CommonJS modules can always be imported via the default export, for example using:

import pkg from './obj43e.cjs';
const { a } = pkg;

(exit 1 · standard output: 0 lines)
--- node20 reqmjs43e.cjs
(exit 0 · standard output: 1 lines)
--- node18 reqmjs43e.cjs
Error [ERR_REQUIRE_ESM]: require() of ES Module <dir>/lib43e.mjs not supported.
Instead change the require of <dir>/lib43e.mjs to a dynamic import() which is available in all CommonJS modules.
(exit 1 · standard output: 0 lines)
```

- ★★★ **확장자 없는 `import` — `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '<dir>/lib43e' imported from <dir>/noext43e.mjs`** — 두 판 같았고, **`lib43e.mjs` 가 옆에 있다는 힌트는 없었다.** 메시지는 **확장자를 붙이지 않은 그 글자 그대로의 경로**를 찾았다고만 말한다.
- ★★★ **CommonJS 의 이름을 못 찾으면 — `SyntaxError: Named export 'a' not found. … is a CommonJS module, which may not support all module.exports as named exports.`** 그리고 **고치는 법을 코드로** 내준다 — `import pkg from './obj43e.cjs'; const { a } = pkg;`. 표준 출력 0 줄 — **연결 단계**에서 막혔다(42번 동작 (5)의 없는 이름과 같은 단계).
- ★★ **ESM 안의 `require` — `ReferenceError: require is not defined in ES module scope, you can use import instead`** · 표준 출력 **1 줄**(첫 줄은 찍고 **실행 중에** 막혔다 — 연결이 아니라 평가).
- ★★ **`require(esm)` — node 18 은 `Error [ERR_REQUIRE_ESM]: require() of ES Module <dir>/lib43e.mjs not supported.` + 「`import()` 로 바꾸라」**, node 20 은 **에러 없이 1 줄**.

### (6) ★★ 한 지정자가 두 파일로 — 상태가 둘이 된다

**언제 쓰나** — 패키지가 `import` 용과 `require` 용 파일을 따로 낼 때(`"exports"`/`"imports"` 의 조건).
★ `node_modules` 없이 같은 모양을 보이려고 **`package.json` 의 `"imports"`**(`#` 로 시작하는 지정자)를 썼다 — 같은 조건 규칙이다.

```text
===== cat js40b-43f/package.json (exit=0) =====
{
  "imports": {
    "#counter": { "import": "./counter43f.mjs", "require": "./counter43f.cjs" }
  }
}
```

```js
// counter43f.mjs
// The ES module side of one "package": a counter.
console.log("counter43f.mjs: body runs");
export let count = 0;
export function bump() { count++; }
```

```js
// counter43f.cjs
// The CommonJS side of the same "package": a counter of its own.
console.log("counter43f.cjs: body runs");
let count = 0;
module.exports = { bump() { count++; }, get count() { return count; } };
```

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

```text
===== cd js40b-43f && node20 main43f.mjs (exit=0) =====
counter43f.mjs: body runs
counter43f.cjs: body runs
after two bump() through import: import side count = 2 · require side count = 0
```

```text
                       "#counter"
                     ┌─────┴──────┐
        import 조건 ─▶ counter43f.mjs      require 조건 ─▶ counter43f.cjs
                     count (라이브)                      count (자기 것)
   bump() × 2  ─▶     2                                  0        ← 같은 「패키지」, 두 벌의 상태
```

- ★★★ **`#counter` 한 글자가 `import` 로는 `counter43f.mjs`, `require` 로는 `counter43f.cjs`** 가 됐고 — **두 본문이 다 돌았고**, `bump()` 두 번 뒤 **`import side count = 2 · require side count = 0`** 이다. 같은 「패키지」가 **두 벌의 상태**를 가졌다.
- ★★ 연혁 문서가 「상처」로 적은 **dual package hazard** 의 모양이 이것이다 — 두 node 판이 같았다. **실제 `node_modules` 패키지로는 돌리지 않았다**(브리핑의 금지).

### (7) ★ 같은 파일, 다른 이벤트 루프 순서 — 36번 인용

★★★ **36번이 이미 쟀다** — **같은 파일**을 CommonJS 로 돌리면 `process.nextTick` 이 **4위**(모든 마이크로태스크 앞), ES 모듈로 돌리면 **9위**(마이크로태스크 뒤)였다. **확장자나 `"type"` 하나를 바꾸면 말없이 순서가 바뀐다** — 동작 (2)의 판정 규칙이 **실행 순서**까지 건드리는 예다. 다시 재지 않았다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다. **전부 node 의 규칙이다.**

| 형태 | 하는 일 | node 판 | 어디서 봤나 |
|---|---|---|---|
| `require("./x.cjs")` · `module.exports = …` · `exports.a = …` | CommonJS — 그 줄에서 평가 · 값을 돌려준다 | 전부 | 동작 (1)·(3) |
| `require("./x.mjs")` | ESM 의 **이름공간 객체**를 동기로 · TLA 면 `ERR_REQUIRE_ASYNC_MODULE` | **v20.19.0 부터 플래그 없이** | 동작 (1) |
| `import("./x.mjs")` (CommonJS 안) | ESM 을 프라미스로 | 전부 | 동작 (1) |
| `import d from "./x.cjs"` | `d` = `module.exports` | 전부 | 동작 (1)·(3) |
| `import { a } from "./x.cjs"` | **lexer 가 찾은 이름만** · 평가 끝의 값 복사 | 전부 | 동작 (1)·(3) |
| `createRequire(import.meta.url)` | ESM 안에서 `require` 를 만든다 | 전부 | 동작 (1) |
| `import.meta.dirname` · `.filename` | 모듈 파일의 경로 | **v20.11.0** | 동작 (4) |
| `.mjs` / `.cjs` / `"type"` / (`.js` 의 문법 감지) | 파일을 무엇으로 읽나 — **확장자 > `type` > 감지** | 감지 **v20.19.0 기본** | 동작 (2) |
| `"imports": { "#x": { "import": …, "require": … } }` | 조건에 따라 다른 파일 | 전부 | 동작 (6) |

- **ESM 의 상대 지정자는 확장자까지** — `./lib` ✕ · `./lib.mjs` ○ · 디렉토리 ✕.
- **CommonJS 에서 ESM 을 쓰는 판-무관 길은 `import()`.**

## 어디서 틀리나

### (1) ★★★ 「CommonJS 에서는 ESM 을 `require` 못 한다」로 외운다

**node 판이 정한다** — node 18 은 `ERR_REQUIRE_ESM`, **node 20.19 는 됐다.** 단 **최상위 `await` 가 있으면 node 20 에서도** `ERR_REQUIRE_ASYNC_MODULE`(동작 (1)).

### (2) ★★★ CommonJS 라이브러리의 이름을 `import { … }` 로 가져오면 다 된다고 믿는다

**lexer 가 찾은 모양만** 된다 — `module.exports = { a: "…" }` 도 막혔다(동작 (1)). 막히면 **기본 가져오기**로 받고 구조 분해한다(node 가 그렇게 안내한다 — 동작 (5)).

### (3) ★★★ ESM 에서 확장자를 뺀다

**`ERR_MODULE_NOT_FOUND`** — 옆에 `lib43e.mjs` 가 있어도 **힌트 없이** 못 찾았다(동작 (5)). 디렉토리도 `ERR_UNSUPPORTED_DIR_IMPORT`.

### (4) ★★★ `"type": "module"` 이면 `.cjs` 도 ESM 이 된다고 믿는다

**확장자가 이긴다** — `.cjs` 는 `type` 이 무엇이든 CommonJS, `.mjs` 는 ES module(동작 (2)).

### (5) ★★ `type` 없는 `.js` 는 어느 판에서나 CommonJS 라 믿는다

**node 20.19 는 ES 모듈 문법이 있으면 ES 모듈로 돌렸다** — node 18 은 `SyntaxError`(동작 (2)). 같은 파일이 **판에 따라** 다르게 읽힌다.

### (6) ★★ ESM 이 CommonJS 를 이름으로 가져오면 라이브라고 믿는다

**평가가 끝난 순간의 값**이다(`named n = 0` · 동작 (3)). 새 값은 **기본 가져오기 객체의 속성**(`m.n = 1`)으로 읽는다.

### (7) ★★ `.mjs` 로 옮긴 뒤에도 `__dirname` 을 쓴다

**`ReferenceError`** — `import.meta.dirname`(node 20.11+) 또는 `fileURLToPath(import.meta.url)` 로 바꾼다(동작 (4)).

### (8) ★ 같은 패키지를 `import` 와 `require` 로 섞어 쓴다

**조건이 두 파일로 가르면 상태가 둘**이 된다(`2` 대 `0` — 동작 (6)).

## 구현 세부사항 대 언어 보장

### 언어(ECMA-262)

- ★★ `import`/`export`·`import()`·`import.meta` 의 **문법과 연결 규칙**(42번). **CommonJS 는 없다.** `import.meta` 의 **속성**은 호스트가 채운다 — 두 node 판의 키 목록이 달랐다(동작 (4)).

### ★★★ Node 호스트 — 이 주제의 거의 전부

- ★★★ **모듈 판정** — 확장자 > `"type"` > (v20.19.0+) `type` 없는 `.js` 의 문법 감지(동작 (2)).
- ★★★ **상호운용** — `require(esm)` 은 v20.19.0 부터 플래그 없이 · TLA 면 `ERR_REQUIRE_ASYNC_MODULE` · `import cjs` 의 이름은 **cjs-module-lexer** 가 고르고 **라이브가 아니다**(동작 (1)·(3)).
- ★★ **해석** — ESM 은 확장자·디렉토리 색인을 **안 채워 준다**, CommonJS 의 `require` 는 채워 준다(동작 (1)).
- ★★ **`import.meta.dirname`·`filename`** — v20.11.0. **`import.meta.resolve`** — 두 판 다 `function`.
- ★ **문구** — `Named export … not found` 는 고치는 법까지 내주고, 잡히지 않은 `ReferenceError` 에는 `in ES module scope, you can use import instead` 가 붙었다.

### 이 판의 관찰

- ★★ **lexer 가 `module.exports = { a: "…" }` 를 못 찾았다** — 두 판 같았다. lexer 의 규칙은 node 문서에 적혀 있지 않다(「정적 분석으로」까지).
- ★ 22 계열 node 는 이 머신에 없어 **돌리지 않았다.**

### 그래서 이렇게 적으면 틀린다

- ✗ 「CommonJS 는 JavaScript 의 모듈 방식 중 하나다」 → ○ 「**node 의 규약**이다 — 언어 명세에는 ESM 만 있다」
- ✗ 「`require(esm)` 은 안 된다」 → ○ 「**node 18 은 안 되고 node 20.19 는 된다** — 최상위 `await` 가 있으면 여전히 안 된다」
- ✗ 「`import { x } from 'cjs'` 는 `module.exports.x` 를 가리킨다」 → ○ 「**평가 끝의 값 복사**이고, **lexer 가 찾은 이름만** 있다」
- ✗ 「`"type": "module"` 이면 모든 파일이 ESM」 → ○ 「**`.js` 만** — `.cjs` 는 CommonJS 로 남는다」

## 언제 쓰고 언제 안 쓰나

- **ESM 에서 CommonJS 라이브러리** — **기본 가져오기**(`import pkg from …`)가 판·lexer 를 안 탄다.
- **CommonJS 에서 ESM 라이브러리** — 여러 node 판을 받아야 하면 **`import()`**. node 20.19+ 만이면 `require(esm)` 도 된다(TLA 없을 때).
- **새 파일의 형식** — 판을 가리지 않게 하려면 **`.mjs`/`.cjs` 로 확장자에 박는다**(감지·`type` 에 기대지 않는다).
- **파일 위치** — `fileURLToPath(import.meta.url)` 가 판을 안 탄다. node 20.11+ 만이면 `import.meta.dirname`.
- ★ **안 쓰는 자리** — 확장자 없는 ESM 지정자 · `import`/`require` 로 같은 상태 패키지를 섞기 · lexer 가 못 찾을 모양에 이름 있는 가져오기.

## 핵심 문장

1. ★★★ **CommonJS 는 명세 밖의 node 규약**이고, 상호운용 규칙은 **node 판이 정한다** — 16행 격자에서 **두 판이 갈린 행 `2 / 16`**(`require(esm)` 두 행), 막힌 행 node 20 `7 / 16` · node 18 `8 / 16`.
2. ★★★ ESM → CommonJS 는 **기본 가져오기가 늘 되고**, 이름 있는 가져오기는 **lexer 가 찾은 모양만** — 다섯 모양 중 둘. 그리고 그 이름은 **평가 끝의 값 복사**다(`named n = 0` · `m.n = 1`).
3. ★★★ 파일의 형식은 **확장자 > `"type"` > 문법 감지** — 18칸에서 판이 갈린 것은 **`type` 없는 `.js` + `export {}`** 한 칸(node 20 ES module · node 18 `SyntaxError`).
4. ★★★ ESM 의 상대 지정자는 **확장자까지** — `import './lib'` 은 `ERR_MODULE_NOT_FOUND`(힌트 없음), `require('./lib')` 는 된다.
5. ★★ ESM 에는 `require`·`__dirname` 이 **없다** — `import.meta.dirname` 은 node 20.11+ · 같은 지정자가 조건으로 두 파일이 되면 **상태가 둘**이다 · 같은 파일의 `nextTick` 순서도 형식이 바꾼다(36번).

## 관련 자료

- [Node.js v20 — Modules: CommonJS](https://nodejs.org/docs/latest-v20.x/api/modules.html) · [ECMAScript modules](https://nodejs.org/docs/latest-v20.x/api/esm.html) · [Packages](https://nodejs.org/docs/latest-v20.x/api/packages.html)
- [`history/js/03-Node-런타임.md`](../../../../../../history/js/03-Node-런타임.md) — README 가 가리키는 정본. ★ **경계**: 그쪽은 **CommonJS 가 Node 의 규약이 된 연혁**(한 문단)까지. [`history/js/05-빌드-생태계.md`](../../../../../../history/js/05-빌드-생태계.md) — 「1.2 CommonJS」·「1.4 ESM」 이 **공존의 상처**(`.mjs` · `"type"` · dual package hazard)를 연혁으로 적는다. 여기는 **그 상처가 지금 두 판의 어느 칸에 나나**부터.
- [42 — ESM 모듈](../42-esm-modules/2-summary.md) — 라이브 바인딩 · 연결과 평가. [36](../36-event-loop-and-microtasks/2-summary.md) — `nextTick` 4위 대 9위. [39](../39-async-await/2-summary.md) · [35](../35-strict-mode/2-summary.md).
- [Python 42 — 모듈·패키지·import](../../../python/syntax/42-modules-packages-and-import/2-summary.md) — CommonJS 순환의 `f>g>undefined` + 경고(7절).

## 용어 풀이

- **CommonJS(CJS)** — `require`/`module.exports` 로 잇는 node 의 모듈 규약. `require`·`module`·`exports`·`__filename`·`__dirname` 을 node 문서는 「CommonJS 래퍼 변수」라 부른다.
- **ESM** — 언어 표준 모듈(42번).
- **`"type"` 필드** — `package.json` 의 `"module"`/`"commonjs"`. **`.js` 파일**을 무엇으로 읽을지 정한다.
- **문법 감지(syntax detection)** — `type` 이 없는 `.js` 에 ES 모듈 문법이 있으면 ES 모듈로 다루는 node 의 규칙(v20.19.0 기본).
- **`require(esm)`** — CommonJS 의 `require` 로 ES 모듈을 동기로 불러 이름공간 객체를 받는 것(node v20.19.0 플래그 없이).
- **cjs-module-lexer** — CommonJS 소스를 **실행하지 않고** 훑어 이름 있는 내보내기를 고르는 node 의 분석기.
- **`createRequire`** — ESM 안에서 `require` 함수를 만드는 node API.
- **`import.meta.dirname`** — 모듈 파일이 있는 디렉토리의 경로(node v20.11.0).
- **조건부 내보내기/가져오기** — `package.json` 의 `"exports"`/`"imports"` 에서 `"import"`·`"require"` 조건으로 다른 파일을 고르는 것.
- **dual package hazard** — 같은 패키지가 `import` 와 `require` 로 **두 벌 적재되어** 상태가 갈리는 위험(연혁 문서의 말).

## 더 들어가면

- **node 22 계열의 `require(esm)`·`"module.exports"` 내보내기 상호운용** — 이 머신에 22 가 없어 돌리지 않았다. v20 문서 이력에 「v20.19.0 — `'module.exports'` interop export 지원」이 있다.
- **`"exports"` 필드와 `node_modules` 패키지** — 이 문서는 `"imports"` 로만 조건 규칙을 보였다.
- **TypeScript 의 `module`/`moduleResolution`** — 컴파일러가 같은 규칙을 흉내 내는 자리. TS 갈래의 몫이다.
