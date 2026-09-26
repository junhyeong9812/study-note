# js/syntax/43 — CJS 와 ESM 상호운용: 「`require(esm)` 은 node 20.19 에서 열렸고 · 이름 있는 가져오기는 lexer 가 찾은 것만 · 확장자가 `type` 을 이기고 · CommonJS 쪽 값은 복사다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **이 주제는 두 node 판의 차이가 본체의 절반이다** — 상호운용 `2 / 16` · 판정 격자 `1 / 9` 행 · `import.meta.dirname` · `require(esm)` 의 문구.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(두 판을 돌리는 `.sh` 는 [2-summary.md](2-summary.md) 동작 (1)·(2)·(5), `package.json` 과 두 카운터는 동작 (6)).
> `js40b-43a-interop-grid.js` + `js40b-43a-interop.sh`(1번 · 7번) · `js40b-43b-type-grid.js` + `js40b-43b-type.sh`(2번 · 6번) · `js40b-43c/`(3번 · 7번 · 10번) · `js40b-43d/`(4번 · 8번) · `js40b-43e/` + `js40b-43e-messages.sh`(5번) · `js40b-43f/`(9번).

## 정답

### 1. node 20 — **막힌 행 `7 / 16`**(TLA 가 든 `require(esm)` · 이름 있는 가져오기 셋 · ESM 의 `require` · 확장자 없는 `import` · 디렉토리 `import`) · node 18 — **`8 / 16`**(`require(esm)` 도 막힘) · 갈린 행 **`2 / 16`** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`require(esm)` 은 node v20.19.0 에서 플래그 없이** 됐다(node 문서 이력) — node 18 은 `ERR_REQUIRE_ESM`. 최상위 `await` 가 든 모듈은 동기로 끝낼 수 없어 node 20 에서도 **`ERR_REQUIRE_ASYNC_MODULE`** — 막힌 이유가 **바뀐** 행이다.
- ★★ ESM → CommonJS 의 **기본 가져오기는 늘 `module.exports`**, 이름 있는 가져오기는 **lexer 가 찾은 모양만**(7번).
- ★★ ESM 의 지정자는 **확장자·디렉토리 색인을 채워 주지 않는다** — CommonJS 의 `require` 는 채워 준다(`lib.js` · `dir/index.js`).

### 2. `.mjs` 는 **늘 `ES module`**, `.cjs` 는 **늘 `CommonJS`**(`export` 가 들면 `SyntaxError`) · `.js` 는 **`type` 을 따르고**, `type` 이 없으면 `plain` 은 **`CommonJS`**, `export {}` 가 들면 **node 20 `ES module` · node 18 `SyntaxError`** — 막힌 칸 **node 20 `4 / 18` · node 18 `5 / 18`** ★★★

**출력**

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

**왜 그런가**

- ★★★ node 문서의 판정 규칙 — **`.mjs`·`.cjs` 는 확장자로**, `.js` 는 **가장 가까운 `package.json` 의 `"type"`** 으로, **없으면 CommonJS**. 그 「없으면」 칸에 **v20.19.0 부터 문법 감지**가 끼어 ES 모듈 문법이 있으면 ES 모듈로 돌린다.
- ★★ CommonJS 로 정해진 파일은 **스크립트 문법**이라 `export` 에서 `SyntaxError 「Unexpected token 'export'」` 다.

### 3. CommonJS — **`m.n = 1 · destructured n = 0`** · ESM — **`m.n = 1 · named n = 0 · ns.n = 0 · ns.default === m true`** — 42번의 ESM → ESM 은 **바인딩**(`0 → 1 → 2`), 여기서는 **상대가 CommonJS 라 복사** ★★★

**출력**

```text
===== cd js40b-43c && node20 main43c.cjs (exit=0) =====
after inc()  m.n = 1 · destructured n = 0
```

```text
===== cd js40b-43c && node20 main43c.mjs (exit=0) =====
after inc()  m.n = 1 · named n = 0 · ns.n = 0 · ns.default === m true
```

**왜 그런가**

- ★★★ CommonJS 가 주는 것은 **객체**(`module.exports`)다 — 객체의 속성을 **매번 읽으면** 새 값이 보이고, 구조 분해로 **꺼내 두면** 그때의 값이다.
- ★★★ ESM 이 CommonJS 를 이름으로 가져오면 node 는 **CommonJS 평가가 끝난 순간의 값**으로 이름공간을 채운다 — node 문서 「**라이브 갱신은 감지하지 않는다**」. 그래서 `named n` 과 `ns.n` 이 둘 다 `0` 이다.

### 4. node 20 — **다섯 비품 `undefined` · 읽으면 `ReferenceError` · 키 `["dirname","filename","resolve","url"]` · `true` · `string … true` · `function`** — node 18 은 **`[4]`·`[6]`** 이 다르다(`["resolve","url"]` · `undefined … false`) · CommonJS 는 **`function · object · object · string · string`** 과 **`this === module.exports true`** ★★

**출력**

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

```text
===== cd js40b-43d && node20 meta43d.cjs (exit=0) =====
[1] typeof  require function · module object · exports object · __filename string · __dirname string
[2] this === module.exports true
```

**왜 그런가**

- ★★ `require`·`module`·`exports`·`__filename`·`__dirname` 은 node 문서가 말하는 **CommonJS 래퍼 변수**다 — ESM 에는 없다.
- ★★ `import.meta.dirname`·`filename` 은 **node v20.11.0** 에서 더해졌다(문서). 판을 안 타려면 `fileURLToPath(import.meta.url)`.

### 5. 확장자 없음 — **`ERR_MODULE_NOT_FOUND` · 0 줄 · 힌트 없음** · ESM 의 `require` — **`ReferenceError … in ES module scope, you can use import instead` · 1 줄** · 이름 없음 — **`SyntaxError: Named export 'a' not found …` + 고치는 코드 · 0 줄** · `require(esm)` — node 20 **에러 없이 1 줄**, node 18 **`ERR_REQUIRE_ESM`** ★★

```js
// named43e.mjs
// A named import from that CommonJS module.
import { a } from "./obj43e.cjs";
console.log(a);
```

**출력**

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

**왜 그런가**

- ★★ **0 줄**인 둘(확장자 없음 · 이름 없음)은 **연결 단계**에서 막혔고, **1 줄**인 `require` 는 **평가 중에** 막혔다(42번의 연결 → 평가).
- ★ 확장자 없는 문구는 **적힌 글자 그대로의 경로**(`<dir>/lib43e`)만 댄다 — 옆의 `lib43e.mjs` 를 가리키지 않았다.

### 6. **확장자 > `"type"` > 문법 감지** — 감지는 **`type` 없는 `.js`(와 확장자 없는 파일)** 에만, **v20.19.0** 에서 기본 ★★★

- ★★★ 2번 격자에서 `.mjs`·`.cjs` 줄은 `type` 셋이 전부 같았다 — 확장자가 이긴다. `type` 이 있으면 `.js` 는 **그것을 따르고 감지는 안 한다**(`type: commonjs` · `.js` · `export {}` 가 `SyntaxError`).
- ★★ node 문서가 감지 대상을 「**`.js` 이거나 확장자가 없고, 제어하는 `package.json` 이 없거나 `type` 이 없는** 파일」로 적는다.

### 7. node 는 **CommonJS 소스를 실행하지 않고 훑는다**(cjs-module-lexer) — ESM 의 연결은 **평가 전**이라 실행해 볼 수 없다 · 그래서 **훑어서 알아본 모양만** 되고(다섯 중 둘), 이름의 값은 **평가 끝의 복사**다 ★★

- ★★ ESM 의 이름은 **연결 단계**에서 정해져야 한다(42번 — 없는 이름은 본문 전에 `SyntaxError`). CommonJS 는 **실행해야** 무엇을 내보내는지 안다 — 그 사이를 lexer 의 **정적 추측**이 메운다(이 문장은 이 문서의 해석이다 — node 문서는 「정적 분석으로 정한다」까지 적는다).
- ★ 추측이라 **모양에 민감**하다 — `{ a }` 는 찾고 `{ a: "…" }` 는 못 찾았다(1번). 값은 CommonJS 평가가 끝난 뒤 한 번 채워 넣으니 **라이브가 아니다**(3번).

### 8. `import()` 문법만 **ECMA-262** — `require`·`module.exports`·`"type"`·`import.meta.dirname`(의 속성)은 전부 **node** · 브라우저에는 **CommonJS 가 없어 부적용** ★★

- ★★ `import.meta` 라는 **문법**은 ECMA-262(ES2020)지만 그 **속성**은 호스트가 채운다 — node 18 과 20 의 키 목록이 달랐다(4번).
- ★ Chrome 판별 블록 — `host require (this script's scope) no`.

### 9. **`2` 와 `0`** — 두 본문은 **각각 한 번** 돈다(`counter43f.mjs: body runs` · `counter43f.cjs: body runs`) ★★

```text
===== cd js40b-43f && node20 main43f.mjs (exit=0) =====
counter43f.mjs: body runs
counter43f.cjs: body runs
after two bump() through import: import side count = 2 · require side count = 0
```

- ★★ 조건 `"import"`/`"require"` 가 **다른 파일**을 고르니 **다른 모듈 두 벌**이다 — 상태가 갈린다. 연혁 문서의 「dual package hazard」 모양이다.

### 10. 36번 — **CommonJS 4위 · ES 모듈 9위** — **파일 형식 판정**(2번)이 실행 순서까지 바꾼다 · 42번과 한 쌍은 **ESM → ESM 은 바인딩, CommonJS 가 끼면 복사** ★★

- ★★ 36번의 `N1` 이 같은 파일에서 4위와 9위로 갈렸다 — 확장자나 `"type"` 한 글자로 파일 형식이 바뀌면 **`nextTick` 과 마이크로태스크의 순서가 말없이** 바뀐다.
- ★ 42번 동작 (1)의 `0 → 1 → 2` 대 `0 · 0 · 0`, 그리고 이 문서 3번의 `named n = 0` — **라이브는 ESM 끼리만**이다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js40b-43a-interop-grid.js` + `js40b-43a-interop.sh` | ★★★ 16행 · 「`blocked 7 / 16`·`8 / 16`」 · 「`differ 2 / 16`」 | node20 · node18 행마다 새 프로세스 1벌 |
| `js40b-43b-type-grid.js` + `js40b-43b-type.sh` | ★★★ 18칸 · 「`4 / 18`·`5 / 18`」 · 갈린 행 1 | node20 · node18 칸마다 새 프로세스 1벌 |
| `js40b-43c/*` | ★★★ CommonJS 의 복사 · ESM 이 CJS 를 가져올 때의 복사 | node20 1벌 + node18 대조 |
| `js40b-43d/*` | ★★ CommonJS 래퍼 변수 · `import.meta` 키 | node20 1벌 + node18 1벌(갈렸다) |
| `js40b-43e/*` + `js40b-43e-messages.sh` | ★★ 막힐 때의 문구 전문 | node20 · node18 각 1벌 |
| `js40b-43f/*` | ★★ 한 지정자 · 두 파일 · 두 상태 | node20 1벌 + node18 대조 |

세 판 대조기(이 묶음 전체의 plain 탐침). 이 주제의 줄은 `43a`·`43b` 둘이고 **둘 다 `DIFFERS`**(node 판 차이 — 1번 · 2번) · Chrome 부적용이다.

```sh
# js40b-vdiff.sh
#!/usr/bin/env bash
# Every plain probe of this batch (js40b-4NX-*.js, not *.web.js), run on node18, node20 and Chrome 151.
# A probe that uses a node-only API (process.* or require) is compared between the two node versions only.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
s18=0; d18=0; sw=0; dw=0; skip=0
for f in js40b-4[0123]?-*.js; do
  [ -e "$f" ] || continue
  case $f in *.web.js) continue ;; esac
  a="$("$N18" "$f" 2>&1)"; b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then r18=identical; s18=$((s18 + 1)); else r18=DIFFERS; d18=$((d18 + 1)); fi
  if grep -q 'process\.\|require(' "$f"; then rw="(node only)"; skip=$((skip + 1))
  else
    w="$(./js40b-browser.sh "$f")"
    if [ "$w" = "$b" ]; then rw=identical; sw=$((sw + 1)); else rw=DIFFERS; dw=$((dw + 1)); fi
  fi
  printf '%-34s node18/node20 %-10s node20/Chrome %s\n' "$f" "$r18" "$rw"
done
echo ""
echo "node18 vs node20: identical $s18 · differs $d18   ·   node20 vs Chrome 151: identical $sw · differs $dw · node only $skip"
```

```text
===== ./js40b-vdiff.sh (exit=0) =====
js40b-40a-close-grid.js            node18/node20 identical  node20/Chrome DIFFERS
js40b-40c-which-protocol.js        node18/node20 identical  node20/Chrome identical
js40b-40d-yield-and-ticks.js       node18/node20 identical  node20/Chrome identical
js40b-41a-abort-mid-job.js         node18/node20 identical  node20/Chrome DIFFERS
js40b-41b-reasons.js               node18/node20 identical  node20/Chrome DIFFERS
js40b-41c-signal-tree.js           node18/node20 identical  node20/Chrome identical
js40b-42c-cycle-grid.js            node18/node20 identical  node20/Chrome (node only)
js40b-43a-interop-grid.js          node18/node20 DIFFERS    node20/Chrome (node only)
js40b-43b-type-grid.js             node18/node20 DIFFERS    node20/Chrome (node only)

node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 3 · differs 3 · node only 3
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — ★★★ **이 주제는 전부다**(node 의 규칙이다).

- ★★★ `require(esm)` · 문법 감지 · `import.meta.dirname` — node 판마다 1번 · 2번 · 4번을 다시 돌린다. 22 계열은 이 머신에 없어 돌리지 않았다.
- ★★ **lexer 가 알아보는 모양**(1번의 이름 있는 가져오기 다섯 행) — node 가 lexer 판을 올리면 바뀔 수 있는 자리다.
- ★ 문구 — `Named export 'a' not found …` · `require is not defined in ES module scope …` · `require() of ES Module … not supported.`
