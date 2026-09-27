# ts/syntax/35 — 모듈 해석 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자·추적·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 세 판 해석 격자와 해석 격자이고, 급소는 호스트 창(`node`)이다.**\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 추적 블록의 `.` 은 `p35/src`, `..` 은 `p35` 다 — 배너의 `sed` 가 절대 경로의 앞부분을 바꿨다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 7.0.2 — `node10`·`node`·`classic` **`TS5108`**, `baseUrl` **`TS5102`**, `bundler+commonjs` 는 **`OK`**(5.9.3 은 `TS5095`) · 기본 **`Bundler`/`Node10`/`NodeJs`** · **4 / 8 · 7 / 8 · 5 / 8 · 5 / 8**

**출력**

```text
===== bash ts34b-resgrid.sh (sh exit=0) =====
행                7.0.2          5.9.3          4.9.5
node10             TS5108         OK             TS6046
node               TS5108         OK             OK
classic            TS5108         OK             OK
node16             OK             OK             OK
nodenext           OK             OK             OK
bundler            OK             OK             TS6046
bundler+commonjs   OK             TS5095         TS6046
nodenext+baseUrl   TS5102         OK             OK

아무것도 안 줬을 때 -- 7.0.2 using 'Bundler'
아무것도 안 줬을 때 -- 5.9.3 using 'Node10'
아무것도 안 줬을 때 -- 4.9.5 using 'NodeJs'

받아들인 행 -- 7.0.2 4 / 8 · 5.9.3 7 / 8 · 4.9.5 5 / 8 · 7.0.2 와 5.9.3 이 갈린 행 5 / 8
```

**왜 그런가**

- ★★★ `TS5108` 은 **값**이, `TS5102` 는 **옵션**이 제거됐다는 코드다(02편 7절). 7.0 은 `node10`·`classic` **값**을 없애고 `baseUrl` **옵션**을 없앴다.
- ★★ 4.9.5 의 `TS6046` 은 `node10` 이름·`bundler` 가 **5.0 부터**라서다.
- ★★★ 기본 해석이 **판마다 다르다** — 아무것도 안 적은 프로젝트는 7.0 에서 **조용히 `Bundler`** 가 된다(10번).

### 2. ★★★ 확장자 없음 — `nodenext` 류 **`TS2835`** · `.js` — **다섯 다 `OK`** · `.ts` — **다섯 다 `TS5097`** · 디렉토리 — **`TS2834`/`OK`/`TS2792`** · `exports` — `node10` 만 **`TS2307`** · 안 연 경로 — **다섯 다 막힘** · **13 / 30**

**출력**

```text
===== bash ts34b-spec35.sh (sh exit=0) =====
파일   import 경로                          node16   nodenext bundler  node10   classic
imp35a   "./util35"                             TS2835   TS2835   OK       OK       OK
imp35b   "./util35.js"                          OK       OK       OK       OK       OK
imp35c   "./util35.ts"                          TS5097   TS5097   TS5097   TS5097   TS5097
imp35d   "./dir35"                              TS2834   TS2834   OK       OK       TS2792
imp35e   "pkg35/feature"                        OK       OK       OK       TS2307   TS2792
imp35f   "pkg35/src/feature35.js"               TS2307   TS2307   TS2307   TS2307   TS2792

풀린 칸 13 / 30
```

**왜 그런가**

- ★★★ `node16`·`nodenext` 는 node 의 ESM 규칙 — **상대 경로는 적힌 파일 그대로**. 그래서 확장자 없음(`TS2835`)·디렉토리(`TS2834`)가 막힌다.
- ★★ `bundler`·`node10` 은 확장자와 `index` 를 **붙여 본다.** `classic` 은 **디렉토리도 패키지도** 못 찾는다(`TS2792`).
- ★★ `exports` 를 아는 셋(`node16`·`nodenext`·`bundler`)만 `pkg35/feature` 를 푼다. 안 연 경로는 그 셋이 **막고**, 나머지 둘은 **패키지를 못 찾아** 막힌다 — 같은 `TS2307` 에 까닭이 둘이다.

### 3. ★★★ `nodenext` — **`Directory './util35' does not exist, skipping all lookups in it.`** → 안 풀림 · `bundler` — **`File './util35.ts' exists`** · `imp35b` — **`.js` 를 떼고 `./util35.ts`** 로 · `imp35e` — **`types` 조건** → `./src/feature35.ts`

**출력**

```ts
// imp35a.ts
export { util as v } from "./util35";
```

```text
===== cd p35/src && tsc --pretty false --noEmit --module nodenext --traceResolution imp35a.ts | sed "s#$PWD#.#g; s#${PWD%/*}#..#g" (tsc exit=1) =====
======== Resolving module './util35' from './imp35a.ts'. ========
Module resolution kind is not specified, using 'NodeNext'.
Resolving in ESM mode with conditions 'import', 'types', 'node'.
Loading module as file / folder, candidate module location './util35', target file types: TypeScript, JavaScript, Declaration, JSON.
Directory './util35' does not exist, skipping all lookups in it.
======== Module name './util35' was not resolved. ========
imp35a.ts(1,27): error TS2835: Relative import paths need explicit file extensions in ECMAScript imports when '--moduleResolution' is 'node16' or 'nodenext'. Did you mean './util35.js'?
```

```text
===== cd p35/src && tsc --pretty false --noEmit --module esnext --moduleResolution bundler --traceResolution imp35a.ts | sed "s#$PWD#.#g; s#${PWD%/*}#..#g" (tsc exit=0) =====
======== Resolving module './util35' from './imp35a.ts'. ========
Explicitly specified module resolution kind: 'Bundler'.
Resolving in CJS mode with conditions 'import', 'types'.
Loading module as file / folder, candidate module location './util35', target file types: TypeScript, JavaScript, Declaration, JSON.
File './util35.ts' exists - use it as a name resolution result.
======== Module name './util35' was successfully resolved to './util35.ts'. ========
```

```ts
// imp35b.ts
export { util as v } from "./util35.js";
```

```text
===== cd p35/src && tsc --pretty false --noEmit --module nodenext --traceResolution imp35b.ts | sed "s#$PWD#.#g; s#${PWD%/*}#..#g" (tsc exit=0) =====
======== Resolving module './util35.js' from './imp35b.ts'. ========
Module resolution kind is not specified, using 'NodeNext'.
Resolving in ESM mode with conditions 'import', 'types', 'node'.
Loading module as file / folder, candidate module location './util35.js', target file types: TypeScript, JavaScript, Declaration, JSON.
File name './util35.js' has a '.js' extension - stripping it.
File './util35.ts' exists - use it as a name resolution result.
======== Module name './util35.js' was successfully resolved to './util35.ts'. ========
```

```ts
// imp35e.ts
export { feature as v } from "pkg35/feature";
```

```text
===== cd p35/src && tsc --pretty false --noEmit --module nodenext --traceResolution imp35e.ts | sed "s#$PWD#.#g; s#${PWD%/*}#..#g" (tsc exit=0) =====
======== Resolving module 'pkg35/feature' from './imp35e.ts'. ========
Module resolution kind is not specified, using 'NodeNext'.
Resolving in ESM mode with conditions 'import', 'types', 'node'.
File './package.json' does not exist according to earlier cached lookups.
File '../package.json' exists according to earlier cached lookups.
Entering conditional exports.
Matched 'exports' condition 'types'.
Using 'exports' subpath './feature' with target './src/feature35.ts'.
File './feature35.ts' exists - use it as a name resolution result.
Resolved under condition 'types'.
Exiting conditional exports.
======== Module name 'pkg35/feature' was successfully resolved to './feature35.ts'. ========
```

**왜 그런가**

- ★★★ `nodenext` 는 **확장자를 붙여 보지 않는다** — 적힌 이름의 파일·디렉토리만 본다. `bundler` 는 **`.ts` 를 붙여** 찾았다.
- ★★★ `imp35b` — `has a '.js' extension - stripping it.` 다음 `File './util35.ts' exists`. tsc 는 **방출 뒤의 이름(`.js`)을 방출 전의 파일(`.ts`)로 되돌려** 찾는다.
- ★★ `imp35e` — `Matched 'exports' condition 'types'`. tsc 는 **타입을 찾는 쪽**이라 `types` 를 먼저 맞춘다(핸드북). node 는 `default` 로 간다(4번).

### 4. ★★★ **`nodenext` 는 node 와 6 / 6**, **`bundler` 는 4 / 6** — 어긋난 둘은 `imp35a`(**`ERR_MODULE_NOT_FOUND`**) · `imp35d`(**`ERR_UNSUPPORTED_DIR_IMPORT`**)

**출력**

```text
===== bash ts34b-pair35.sh (sh exit=0) =====
파일   nodenext   bundler    node(v18)
imp35a   TS2835     OK         error ERR_MODULE_NOT_FOUND
imp35b   OK         OK         value util35
imp35c   TS5097     TS5097     error ERR_MODULE_NOT_FOUND
imp35d   TS2834     OK         error ERR_UNSUPPORTED_DIR_IMPORT
imp35e   OK         OK         value feature35
imp35f   TS2307     TS2307     error ERR_PACKAGE_PATH_NOT_EXPORTED

node 와 같은 판정 -- nodenext 6 / 6 · bundler 4 / 6
```

**왜 그런가**

- ★★★ tsc 는 import 경로를 **한 글자도 안 바꿔** 방출한다. 그래서 node 가 푸느냐는 **node 의 규칙**만이 정한다 — 그 규칙을 흉내 낸 `nodenext` 가 6 / 6 이다.
- ★★ `imp35e` 는 tsc 가 `types`(`./src/feature35.ts`), node 가 `default`(`./out/feature35.js`)로 갔다 — **다른 파일, 같은 판정**.
- ★★ `imp35f` — tsc `TS2307` ↔ node `ERR_PACKAGE_PATH_NOT_EXPORTED`. `imp35c` — `TS5097` 이어도 **방출은 됐고**, node 가 `.ts` 파일을 `out/` 에서 못 찾았다.

### 5. ★★★ `node16`·`node18` **`TS1479`** · `node20` **`OK`** · `nodenext` — 4.9.5 **`TS1479`**, 5.9.3·7.0.2 **`OK`** · **3 / 4** · node v18 — **`Error ERR_REQUIRE_ESM`**

**출력**

```ts
// c35.cts
import { util } from "./util35.js";
console.log("[1]", util);
```

```text
===== bash ts34b-cjs35.sh (sh exit=0) =====
--module     7.0.2      5.9.3      4.9.5
node16       TS1479     TS1479     TS1479
node18       TS1479     TS1479     TS6046
node20       OK         OK         TS6046
nodenext     OK         OK         TS1479

7.0.2 와 4.9.5 가 갈린 행 3 / 4
```

```text
===== cd p35 && tsc --pretty false -t es2022 --module nodenext --rootDir src --outDir oc35 src/c35.cts src/util35.ts (tsc exit=0) =====
===== 방출된 oc35/c35.cjs =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const util35_js_1 = require("./util35.js");
console.log("[1]", util35_js_1.util);
```

```text
===== cd p35 && node run35c.cjs (node exit=0) =====
Error ERR_REQUIRE_ESM
```

**왜 그런가**

- ★★★ `nodenext` 는 **그 tsc 판이 아는 가장 새 node** 를 흉내 낸다. 5.9.3·7.0.2 의 `nodenext` 는 `node20` 과 같은 답(ESM 을 `require` 로 부를 수 있는 node)이고, 4.9.5 의 `nodenext` 는 `node16` 과 같은 답이다.
- ★★★ 이 머신의 node 는 **v18** — `require("./util35.js")` 가 ESM 을 만나 `ERR_REQUIRE_ESM`. **`--module node18` 이었다면 tsc 가 `TS1479` 로 미리 막았다.**

### 6. ★★★ 7.0.2 **`exit 0`** · 방출물의 경로는 **`"@src/util35g.js"` 그대로** · node **`ERR_MODULE_NOT_FOUND`** · 5.9.3·4.9.5 **`(exit 0)`** · 파일을 직접 주면 7.0.2 **`TS5112`**, 5.9.3·4.9.5 **`TS2307`**

**출력**

```text
===== cd p35g && tsc --pretty false -p tsconfig.json (tsc exit=0) =====
===== 방출된 outg/imp35g.js =====
export { util as v } from "@src/util35g.js";
```

```text
===== cd p35g && node run35g.mjs (node exit=0) =====
Error ERR_MODULE_NOT_FOUND
```

```text
===== cd p35g && node "$TSC_OLD" --pretty false --noEmit -p tsconfig.json ; 이어서 "$TSC_49" 로 같은 것 (sh exit=0) =====
(exit 0)
(exit 0)
```

```ts
// imp35g.ts
export { util as v } from "@src/util35g.js";
```

```text
===== cd p35g/src && tsc --pretty false --noEmit imp35g.ts ; 이어서 "$TSC_OLD" · "$TSC_49" 로 같은 것 (sh exit=0) =====
error TS5112: tsconfig.json is present but will not be loaded if files are specified on commandline. Use '--ignoreConfig' to skip this error.
(exit 1)
imp35g.ts(1,27): error TS2307: Cannot find module '@src/util35g.js' or its corresponding type declarations.
(exit 2)
imp35g.ts(1,27): error TS2307: Cannot find module '@src/util35g.js' or its corresponding type declarations.
(exit 2)
```

**왜 그런가**

- ★★★ `paths` 는 **tsc 에게만 주는 별칭**이다 — 검사 때 `./src/util35g.ts` 로 풀고, 방출물의 지정자는 **그대로** 둔다. node 는 `@src` 를 모른다.
- ★★ `baseUrl` 없는 `paths` 는 **옛 판에서도** 됐다. 7.0 이 뺀 것은 `baseUrl` 뿐이다.
- ★★★ 7.0.2 는 **위쪽 디렉토리에 `tsconfig.json` 이 있는데** 파일을 직접 주면 `TS5112` 로 **검사를 거부한다.** 옛 두 판은 설정을 무시하고 파일만 검사해, `paths` 가 없으니 `TS2307`.

### 7. ★★★ tsc 가 **`.js` 를 떼고 `.ts` 로 바꿔** 찾기 때문 — 「`File name './util35.js' has a '.js' extension - stripping it.`」

- ★★ `.js` 로 적으면 **방출 뒤에도 맞는 이름**이다(방출물의 `util35.js` 가 실제로 생긴다). tsc 는 검사 때 그 이름을 **원본으로 되돌려** 찾는다 — 그래서 다섯 방식이 다 받는다.
- ★ `.ts` 로 적으면 방출 뒤에 **없는 파일**을 가리키게 되므로 `TS5097` 로 막는다(4번 `imp35c` 의 node 결과가 그것이다).

### 8. ★★★ **tsc 가 이름을 「붙여 보고」 찾은 칸** — 확장자(`imp35a`)와 디렉토리 `index`(`imp35d`) · node 와 같은 일을 한 쪽은 **`nodenext` 추적**(붙여 보지 않았다)

- ★★ `bundler` 추적은 `./util35` 에 `.ts` 를 **붙여** 찾았다. node 의 ESM 해석은 **붙이지 않는다** — 적힌 파일이 없으면 끝이다.
- ★ 번들러를 거치면 번들러가 **실행 전에 붙여 준다.** `bundler` 판정은 그 전제 위에서만 맞다.

### 9. ★★★ **tsc 의 판**이다 — 호스트 node 와 맞추려면 **판을 박은 값**(`node18`·`node20`)을 고른다

- ★★ 5번 — 같은 `nodenext` 가 4.9.5 `TS1479`, 7.0.2 `OK`. 바뀐 것은 **tsc** 뿐이다.
- ★★★ tsc 는 **어느 node 에서 돌지 모른다.** 배포 환경이 v18 이면 `node18` 이 그 호스트의 규칙이다 — 이 판에서 `TS1479` 로 미리 막았다.

### 10. ★★★ **기본 해석 방식이 `Node10` → `Bundler` 로 바뀐 것** — 진단이 없다 · `--traceResolution` 의 둘째 줄(「`Module resolution kind is not specified, using '…'`」)을 찍어 본다

- ★★ 1번 마지막 세 줄이 그 방법이다 — 판마다 **`using '…'`** 이 다르다.
- ★★ 사라진 값·옵션은 `TS5108`·`TS5102` 로 **시끄럽게** 알린다. 기본값 변화는 **조용하다** — 2번 격자에서 옛 기본(`node10`, 5.9.3)과 새 기본(`bundler`, 7.0.2)이 갈린 칸은 **`imp35e` 하나**(`TS2307` → `OK`)다. 칸이 하나뿐이라 더 눈에 안 띈다.

### 11. ★★ 02편 7절 「**`tsc` 에 파일을 직접 주면 `tsconfig.json` 을 무시한다**」 — 7.0.2 는 **`TS5112` 로 거부**한다 · 파이썬은 **실행기 하나 안에서 기준(`__package__`)이 달라서**, TS 는 **검사기와 실행기가 다른 규칙이라서** 어긋난다

- ★★ [**02번 주제**](../02-type-checking-vs-emit/) 7절의 문장은 `tsc --help` 문구에서 왔다. 02편 블록들은 **설정 파일 없는 디렉토리**에서 던져 이 칸을 안 밟았다.
- ★★ [파이썬 42편](../../../python/syntax/42-modules-packages-and-import/) 5절 — `python3 pkg/mod.py` 는 `__package__ = None` 이라 상대 import 가 `ImportError`, `-m` 은 된다. **푸는 이는 하나**이고 기준이 두 실행 방식에서 다르다.
- ★★★ TS 는 **푸는 이가 둘**이다 — tsc(검사)와 node(실행). 둘이 **같은 규칙을 쓰게 맞추는 것**이 `moduleResolution` 을 고르는 일이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ 세 판 해석 격자 | `bash ts34b-resgrid.sh` (여덟 행 × 세 판 + 기본값) | **4 / 8 · 7 / 8 · 5 / 8 · 5 / 8** |
| ★★★ 해석 격자 | `bash ts34b-spec35.sh` (여섯 × 다섯) | **13 / 30** |
| ★★ 추적 | `--traceResolution` 넷 | `skipping all lookups` · `exists` · `stripping it` · `types` 조건 |
| ★★★ tsc 대 node | `bash ts34b-pair35.sh` | **nodenext 6 / 6 · bundler 4 / 6** |
| ★★★ CJS → ESM | `bash ts34b-cjs35.sh` · 방출 · `node run35c.cjs` | **3 / 4** · `ERR_REQUIRE_ESM` |
| ★★ `paths` | `tsc -p` · `node run35g.mjs` · 옛 두 판 · 파일 직접 | `exit 0` · `ERR_MODULE_NOT_FOUND` · `(exit 0)` 둘 · `TS5112`/`TS2307` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **`nodenext` 의 뜻**(5번) — tsc 판이 오르면 움직인다. **node 판이 오르면** node 칸이 바뀐다(v18 → 새 판에서 `require(esm)`).
- ★★ **기본 해석**(1번) · **`bundler`+`commonjs`** 가 7.0.2 에서 풀린 것.
- ★★ **`TS5112`**(6번) — 7.0.2 에서 처음 본 코드다.
- ★ `bundler` 추적의 「CJS mode」 문구(3번).

**안 돌려 본 것**

- ★★ **6.0** · **새 node(v20+)** — 이 머신에 없다.
- ★ **`--rewriteRelativeImportExtensions` 의 방출** · **`package.json` 의 `imports`** · **실제 번들러** — 던지지 않았다.
