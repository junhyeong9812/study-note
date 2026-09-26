# ts/syntax/38 — 앰비언트·전역 타입 구성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출물·실행은 `tsc` **7.0.2** · `node` **v18.19.1**(5번은 **v20.19.6** 도) 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 「전역 가시성 격자」이고, 둘째 기둥은 3창(방출물 + `node` 두 판)이다.**\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `types` **키 없음** 두 행만 갈린다 — 7.0.2 `TS2304` · 5.9.3·4.9.5 `TS2322` · `[]` 는 세 판 `TS2304` · `["x38"]` 은 세 판 `TS2322` — **`2 / 6`**

**출력**

```text
===== bash ts38b-vis38.sh (sh exit=0) =====
선언의 자리       types      7.0.2    5.9.3    4.9.5
node_modules/@types    (키 없음) TS2304   TS2322   TS2322
node_modules/@types    []         TS2304   TS2304   TS2304
node_modules/@types    ["x38"]    TS2322   TS2322   TS2322
typeRoots ./types      (키 없음) TS2304   TS2322   TS2322
typeRoots ./types      []         TS2304   TS2304   TS2304
typeRoots ./types      ["x38"]    TS2322   TS2322   TS2322

칸에 나온 코드 가짓수 2 · 7.0.2 와 5.9.3 이 갈린 행 2 / 6
```

**왜 그런가**

- ★★★ 7.0.2 는 `types` 키가 없으면 **`[]` 와 같다** — 레퍼런스의 「By default `types` is set to `[]`」. 5.9.3·4.9.5 는 **보이는 `@types` 전부**를 넣었다.
- ★★ 명시한 `[]`·`["x38"]` 은 **판을 안 탄다.** `typeRoots` 는 찾는 자리만 바꿨다 — 두 묶음이 칸마다 같다(8번).
- ★ 마지막 줄의 「코드 가짓수 2」 — 칸이 전부 같거나 `TS5…` 가 들었으면 스크립트가 멈췄다(가짜 격자 방지).

### 2. ★★★ `import`·`reference` 둘 다 **`a…` 와 `b38.ts` 양쪽이 `TS2322`**(보인다) · `["*"]` 는 7.0.2 **`b38.ts` 가 봄** / 5.9.3 **`TS2688`** · 종료 코드 7.0.2 `1` · 5.9.3 `2`

**출력**

```ts
// a38i.ts
import "x38";
const probeA: null = X38_GLOBAL;
export {};
```

```ts
// a38r.ts
/// <reference types="x38" />
const probeA: null = X38_GLOBAL;
export {};
```

```ts
// b38.ts
const probeB: null = X38_GLOBAL;
export {};
```

```text
===== cd p38 && tsc --pretty false --noEmit -p <tsconfig.json · tsconfig.ref.json · tsconfig.star.json> ; 각각 "$TSC_OLD" 로도 (sh exit=0) =====
---- 7.0.2 -p tsconfig.json
a38i.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 1)
---- 5.9.3 -p tsconfig.json
a38i.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 2)
---- 7.0.2 -p tsconfig.ref.json
a38r.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 1)
---- 5.9.3 -p tsconfig.ref.json
a38r.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 2)
---- 7.0.2 -p tsconfig.star.json
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 1)
---- 5.9.3 -p tsconfig.star.json
error TS2688: Cannot find type definition file for '*'.
  The file is in the program because:
    Entry point of type library '*' specified in compilerOptions
(exit 2)
```

**왜 그런가**

- ★★★ 끌어온 전역은 **컴파일 전체**의 전역이다 — import 를 안 한 `b38.ts` 도 봤다(37편 3절).
- ★★ `/// <reference types>` 는 같은 일을 **지시 주석**으로 한다. 둘 다 `types: []` 를 **건너뛴다.**
- ★★ `types: ["*"]` 는 7.0.2 가 받는 값이고 5.9.3 에는 **없다**(`TS2688` — 「Cannot find type definition file for '*'.」). 레퍼런스의 `types` 항목에는 실려 있지 않다.

### 3. ★★★ **`require("x38");`** 가 남고, node 는 **`Error MODULE_NOT_FOUND`**

**출력**

```text
===== cd p38 && tsc --pretty false -p tsconfig.json --module commonjs --outDir e38 (tsc exit=2) =====
a38i.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
===== 방출된 e38/a38i.js =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
require("x38");
const probeA = X38_GLOBAL;
```

```text
===== cd p38 && node run38.cjs (node exit=0) =====
Error MODULE_NOT_FOUND
```

**왜 그런가**

- ★★ 부작용 import 는 **지워지지 않는다**(36편 1절). 타입을 들여오려던 줄이 **값 쪽 `require`** 로 남았다.
- ★★★ `node_modules/@types/x38` 은 **타입만** 있다 — node 가 풀 `x38` 패키지가 **없다.** 검사를 통과한 줄이 실행에서 모듈을 못 찾는다.
- ★ 검사 진단(`TS2322` 둘)이 있어도 방출은 돌았다 — `(tsc exit=2)`(02편 1절).

### 4. ★★★ `es2020` — **넷 다**(`TS2584` 둘 · `TS2550` 둘) · `es2022` 는 `.at` 이, `es2023` 은 `.toSorted` 가 풀린다 · `es2023,dom` **0건** · `(안 줌)` 은 7.0.2 **OK** / 5.9.3 **`TS2550` 둘** · **`console` 은 `dom` 이 없으면 `TS2584`**

**출력**

```ts
// lib38.ts
const el = document.body;
const last = [1, 2, 3].at(-1);
const sorted = [3, 1, 2].toSorted();
console.log(last, sorted, el);
export {};
```

```text
===== bash ts38b-lib38.sh (sh exit=0) =====
--lib        7.0.2                                    5.9.3
(안 줌)    OK                                       2:TS2550 3:TS2550
es2020       1:TS2584 2:TS2550 3:TS2550 4:TS2584      1:TS2584 2:TS2550 3:TS2550 4:TS2584
es2022       1:TS2584 3:TS2550 4:TS2584               1:TS2584 3:TS2550 4:TS2584
es2023       1:TS2584 4:TS2584                        1:TS2584 4:TS2584
es2023,dom   OK                                       OK

7.0.2 와 5.9.3 이 갈린 행 1 / 5
```

```text
===== tsc --pretty false --noEmit --lib es2020 lib38.ts (tsc exit=1) =====
lib38.ts(1,12): error TS2584: Cannot find name 'document'. Do you need to change your target library? Try changing the 'lib' compiler option to include 'dom'.
lib38.ts(2,24): error TS2550: Property 'at' does not exist on type 'number[]'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2022' or later.
lib38.ts(3,26): error TS2550: Property 'toSorted' does not exist on type 'number[]'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2023' or later.
lib38.ts(4,1): error TS2584: Cannot find name 'console'. Do you need to change your target library? Try changing the 'lib' compiler option to include 'dom'.
```

**왜 그런가**

- ★★ `lib` 는 **목록**이다 — `es2020` 만 적으면 기본 목록(`dom` 포함)을 **대체**해 `document`·`console` 이 빠진다(9번).
- ★★ `TS2550` 문구가 **필요한 `lib` 판**을 적어 준다 — `'es2022' or later` · `'es2023' or later`.
- ★★★ `(안 줌)` 은 `target` 기본값을 따라간다 — 7.0.2 는 es2025, 5.9.3 은 es5(02편). 그래서 **다섯 행 중 그 행만** 갈렸다(`1 / 5`).

### 5. ★★★ 7.0.2 검사 **0줄** · node v18 **`[1] TypeError xs.toSorted is not a function`** · node v20 **`[1] [ 1, 2, 3 ]`** · `[2]` 는 둘 다 **`[ 3, 1, 2 ]`**

**출력**

```ts
// rt38.ts
const xs = [3, 1, 2];
try {
    console.log("[1]", xs.toSorted());
} catch (e) {
    console.log("[1]", (e as Error).constructor.name, (e as Error).message);
}
console.log("[2]", xs);
```

```text
===== tsc --pretty false --noEmit rt38.ts ; 이어서 "$TSC_OLD" 로 같은 것 (sh exit=0) =====
---- 7.0.2
(exit 0)
---- 5.9.3
rt38.ts(3,27): error TS2550: Property 'toSorted' does not exist on type 'number[]'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2023' or later.
rt38.ts(5,49): error TS2339: Property 'name' does not exist on type 'Function'.
(exit 2)
```

```text
===== tsc --pretty false --outDir e38r rt38.ts (tsc exit=0) =====
===== 방출된 e38r/rt38.js =====
"use strict";
const xs = [3, 1, 2];
try {
    console.log("[1]", xs.toSorted());
}
catch (e) {
    console.log("[1]", e.constructor.name, e.message);
}
console.log("[2]", xs);
```

```text
===== node e38r/rt38.js ; 이어서 "$NODE20" 로 같은 것 (sh exit=0) =====
---- node v18.19.1
[1] TypeError xs.toSorted is not a function
[2] [ 3, 1, 2 ]
(exit 0)
---- node v20.19.6
[1] [ 1, 2, 3 ]
[2] [ 3, 1, 2 ]
(exit 0)
```

**왜 그런가**

- ★★★ `lib` 는 **호스트에 대한 약속**이다 — tsc 는 그 약속을 믿고 `toSorted` 를 통과시켰고, **node v18 에는 그 메서드가 없다.** 37편 2절의 「`.d.ts` 는 주장이다」의 `lib` 판이다.
- ★★ 방출물은 `xs.toSorted()` 를 **그대로** 둔다 — 폴리필도 바꿔 쓰기도 없다.
- ★ 5.9.3 의 `TS2339`(`name`)는 기본 `lib` 가 **es5** 라서다 — 이 질문의 본선은 아니다.

### 6. ★★ 셋을 함께 — **`TS2322` 둘**(`number` — 둘 다 보인다) · `useg38.ts` 혼자 — **`TS2304` 둘** · `scrg38.ts` 혼자 — **`TS2669`**

**출력**

```ts
// modg38.ts
declare global {
    var FROM_MODULE: number;
}
export {};
```

```ts
// scrg38.ts
declare global {
    var FROM_SCRIPT: number;
}
```

```ts
// scrv38.ts
declare var FROM_PLAIN: number;
```

```ts
// useg38.ts
const p1: null = FROM_MODULE;
const p2: null = FROM_PLAIN;
export {};
```

```text
===== tsc --pretty false --noEmit <useg38.ts modg38.ts scrv38.ts · useg38.ts 혼자 · scrg38.ts 혼자> (sh exit=0) =====
---- useg38.ts modg38.ts scrv38.ts
useg38.ts(1,7): error TS2322: Type 'number' is not assignable to type 'null'.
useg38.ts(2,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
---- useg38.ts
useg38.ts(1,18): error TS2304: Cannot find name 'FROM_MODULE'.
useg38.ts(2,18): error TS2304: Cannot find name 'FROM_PLAIN'.
(exit 1)
---- scrg38.ts
scrg38.ts(1,9): error TS2669: Augmentations for the global scope can only be directly nested in external modules or ambient module declarations.
(exit 1)
```

**왜 그런가**

- ★★ 모듈 안 `declare global { var … }` 와 스크립트의 맨 `declare var` 는 **둘 다 전역**에 놓인다 — 컴파일에 들어 있을 때만(혼자면 `TS2304`).
- ★★★ `export` 가 없는 `scrg38.ts` 는 **이미 전역 스크립트**라 `declare global` 로 감쌀 자리가 없다 — `TS2669`(「Augmentations for the global scope can only be directly nested in external modules or ambient module declarations.」).

### 7. ★★★ 1번의 **「키 없음」 행** — 7.0.2 에서 `[]` 가 되어 `@types` 가 **하나도 안 들어온다** · 고치는 한 줄은 **`"types": ["node", "jest"]` 처럼 이름을 적는 것**

- ★★★ 5.9.3 은 「키 없음 = 보이는 `@types` 전부」였고 7.0.2 는 「키 없음 = `[]`」다 — 1번 격자의 **갈린 두 행**이 그것이다.
- ★★ 명시한 `["x38"]` 행은 **세 판이 같다.** 목록을 적으면 판을 안 탄다.
- ★ 14편 6절의 `TS2591` 문구가 「… add 'node' to the types field in your tsconfig」라고 **고칠 자리를 적어 준다**(11번).

### 8. ★★ **칸마다 같다** — `typeRoots` 는 **찾는 디렉토리**, `types` 는 **넣을 목록**이다

- ★★ `typeRoots: ["./types"]` 는 `@types` 를 `node_modules/@types` 대신 `./types` 에서 찾게 했을 뿐이다.
- ★★★ 넣을지는 여전히 `types` 가 정했다 — 7.0.2 에서 `typeRoots` 만 주고 `types` 를 안 적으면 **아무것도 안 들어온다**(둘째 묶음의 「키 없음」 칸이 `TS2304`).

### 9. ★★★ **`lib.dom`** — `@types/node` 가 없으니 `console` 을 대 주는 것은 **DOM 선언뿐**이었고, `es2020` 만 적어 그것이 빠졌다

- ★★ 4번 `es2020`·`es2022`·`es2023` 행의 **`4:TS2584`** 가 그 줄이다 — 문구도 「… to include 'dom'」.
- ★ `es2023,dom` 에서 풀렸다. node 용 프로젝트라면 `console` 은 보통 `@types/node` 가 대 주는데, **7.0 에서는 `types` 에 적어야** 들어온다(1·7번).

### 10. ★★★ **둘 다 못 한다** — 들어온 전역은 **컴파일 전체**가 본다 · 값 쪽에서 `import "x38"` 은 **`require("x38")` 을 남긴다**

- ★★★ 2번의 `b38.ts` 가 증거다 — 두 설정 모두 import·reference 를 **안 한 파일**도 `TS2322`(보인다).
- ★★ 3번 — `import "x38"` 은 방출물에 줄이 남아 node 가 `MODULE_NOT_FOUND`. 같은 플래그로 `reference` 쪽을 방출하면 —

```text
===== cd p38 && tsc --pretty false -p tsconfig.ref.json --module commonjs --outDir e38 (tsc exit=2) =====
a38r.ts(2,7): error TS2322: Type 'string' is not assignable to type 'null'.
b38.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
===== 방출된 e38/a38r.js =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
/// <reference types="x38" />
const probeA = X38_GLOBAL;
```

- ★★★ **`require` 가 없다** — 지시 주석은 **주석째** 남았다. 값 쪽에서 두 줄은 이렇게 갈린다.

### 11. ★★ 37편 3절 「`export` 없는 `.d.ts` 는 **컴파일 전체**의 전역」 · 1번의 **`["x38"]` 칸**(목록에 이름을 적는 것) · 36편 1절 「**`import "…"` 는 늘 남는다**」

- ★★ [**37번 주제**](../37-writing-declaration-files/) 3절 — `glob37.d.ts` 의 `track`·`APP_VERSION` 이 import 없이 보였다. 2번은 그 `.d.ts` 가 `import`·`reference` 로 **컴파일에 끌려 들어온** 경우다.
- ★★ [**14번 주제**](../14-assertion-signatures/) 6절 — `TS2591` 이 `types` 필드를 가리킨다. 1번에서 판을 안 탄 행이 **이름을 적은 행**이다.
- ★★ [**36번 주제**](../36-type-only-imports-and-exports/) 1절 — 부작용 import 는 어느 설정에서도 지워지지 않는다. 3번의 `require("x38");`.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `"$NODE20" --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `v20.19.6` · `Python 3.12.3` |
| ★★★ 전역 가시성 격자 | `bash ts38b-vis38.sh` — 여섯 칸 × 세 판, 칸마다 디렉토리 | 갈린 행 **`2 / 6`** · 코드 가짓수 2 |
| ★★ `types` 를 건너뛰는 길 | `-p` 설정 셋 × 두 판 | 전부 `b38.ts` 가 봄 · 5.9.3 의 `"*"` 만 `TS2688` |
| ★★ 부작용 import 의 방출·실행 | 방출 둘 · `node run38.cjs` | `require("x38")` · `MODULE_NOT_FOUND` · `reference` 쪽은 주석만 |
| ★★ `lib` 격자 | `bash ts38b-lib38.sh` — 다섯 × 두 판 | 갈린 행 **`1 / 5`** |
| ★★★ `lib` 와 호스트 | `--noEmit` × 두 판 · 방출 · node v18 · v20 | 0줄 · `TypeError` · `[ 1, 2, 3 ]` |
| ★★ `declare global` | 세 조합 | `TS2322` 둘 · `TS2304` 둘 · `TS2669` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **`types` 키 없음의 뜻**(1번) — 이미 판마다 달랐다.
- ★★ **`types: ["*"]`**(2번) — 7.0.2 에만 있다.
- ★★ **`lib` 를 안 줬을 때의 목록**(4번) — `target` 기본값을 따라간다.
- ★★★ **node 판**(5번) — `toSorted` 가 v18 과 v20 에서 갈렸다.

**안 돌려 본 것**

- ★★ **진짜 `@types` 패키지**(`npm install`) — 손으로 만든 디렉토리 하나로 흉내 냈다.
- ★ **`types: []` 의 검사 시간** — 재지 않았다.
