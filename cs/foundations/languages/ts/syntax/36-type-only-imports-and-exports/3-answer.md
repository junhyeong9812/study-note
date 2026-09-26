# ts/syntax/36 — 타입 전용 import·export — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 3창(방출된 `.js` + `node`) — 방출 격자다.**\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 끔과 갈린 칸 — **isolatedModules 1 / 8 · verbatimModuleSyntax 4 / 8 · erasableSyntaxOnly 0 / 8**

**출력**

```text
===== bash ts34b-emit36.sh (sh exit=0) =====
[i36a] import { Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 import { Shape } from "./lib36.mjs"; · 진단 (1,10) TS1484 · node SyntaxError: The requested module './lib36.mjs' does not provide an export named 'Shape'
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36b] import type { Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 export {}; · 진단 OK · node (출력 없음)
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36c] import { type Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 import {} from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36d] import "./lib36.mjs";
    끔                    줄 import "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    isolatedModules        줄 import "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    verbatimModuleSyntax   줄 import "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    erasableSyntaxOnly     줄 import "./lib36.mjs"; · 진단 OK · node lib36 evaluated
[i36e] export type { Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 export {}; · 진단 OK · node (출력 없음)
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36f] export { Shape } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 (1,10) TS1205 · node (출력 없음)
    verbatimModuleSyntax   줄 export { Shape } from "./lib36.mjs"; · 진단 (1,10) TS1205 · node SyntaxError: The requested module './lib36.mjs' does not provide an export named 'Shape'
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36g] import { version } from "./lib36.mjs";
    끔                    줄 export {}; · 진단 OK · node (출력 없음)
    isolatedModules        줄 export {}; · 진단 OK · node (출력 없음)
    verbatimModuleSyntax   줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    erasableSyntaxOnly     줄 export {}; · 진단 OK · node (출력 없음)
[i36h] import { type Shape, version } from "./lib36.mjs";
    끔                    줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    isolatedModules        줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    verbatimModuleSyntax   줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated
    erasableSyntaxOnly     줄 import { version } from "./lib36.mjs"; · 진단 OK · node lib36 evaluated

끔과 갈린 칸 -- isolatedModules 1 / 8 · verbatimModuleSyntax 4 / 8 · erasableSyntaxOnly 0 / 8
```

**왜 그런가**

- ★★★ 기본·`isolatedModules`·`erasableSyntaxOnly` 는 **쓰임새로** 지운다 — 타입만 쓰인 `i36a`·`i36c`, 안 쓰인 값 `i36g` 까지 `export {};` 가 됐다.
- ★★★ `verbatimModuleSyntax` 는 **`type` 딱지로만** 지운다 — 갈린 넷(`i36a`·`i36c`·`i36f`·`i36g`)이 전부 「딱지 없는데 기본 설정이 지우던」 칸이다.
- ★★ `isolatedModules` 의 1칸은 `i36f` 의 **진단**(`TS1205`)뿐 — 방출은 끔과 같다. `erasableSyntaxOnly` 는 **검사만** 해 한 칸도 안 바꿨다.

### 2. ★★★ **`import {} from "./lib36.mjs";`** · node **`lib36 evaluated`** — 기본 설정에서는 **줄째 사라지고** 출력 없음

**출력** — 1번 격자의 `[i36c]` 네 줄이 답이다.

**왜 그런가**

- ★★★ `verbatimModuleSyntax` 는 **이름** `Shape` 만 지우고 **문장**(`import … from "./lib36.mjs"`)은 남긴다 — TSConfig 문서의 「`import {} from "a"` 로 다시 쓰인다」 그대로다.
- ★★ ESM 에서 빈 import 도 **모듈을 평가한다** — `lib36` 의 `console.log` 가 돈다. 부작용이 **싫으면** `import type { Shape }`(줄 전체 딱지)로 적는다 — `i36b` 는 모든 설정에서 사라졌다.

### 3. ★★★ 기본 — **실행 안 됨**(줄이 지워졌다) · `verbatimModuleSyntax` — **실행됨**(`lib36 evaluated`)

**출력** — 1번 격자의 `[i36g]` 네 줄이 답이다.

**왜 그런가**

- ★★★ 기본 설정은 `version` 을 **값으로 안 쓰니** import 를 지운다. 그 모듈의 **부작용까지** 함께 사라진다.
- ★★ 부작용이 목적이면 **`import "./lib36.mjs";`**(`i36d`) — 모든 설정에서 남았다.

### 4. ★★ ESM 타입 전용 셋 **`OK`** · `import =`·`import type =`·`export =` **`TS1294`** · 4.9.5 **전부 `TS5023`** · **3 / 6**

**출력**

```text
===== bash ts34b-erase36.sh (sh exit=0) =====
탐침                       7.0.2            5.9.3            4.9.5
import-type-named            OK               OK               TS5023
import-inline-type           OK               OK               TS5023
export-type                  OK               OK               TS5023
import-equals-require        (1,1) TS1294     (1,1) TS1294     TS5023
import-type-equals-require   (1,1) TS1294     (1,1) TS1294     TS5023
export-equals                (1,14) TS1294    (1,14) TS1294    TS5023

7.0.2 에서 TS1294 가 난 탐침 3 / 6
```

**왜 그런가**

- ★★ `import type {…}`·`import { type … }`·`export type {…}` 는 **지우면 끝**인 ESM 꼴이다.
- ★★★ `import x = require()`·`export =` 은 **TS 전용 문법** — `require` 호출·`module.exports` 대입을 **만들어야** 한다. `import type x = require()` 도 같은 꼴이라 막혔다(5번).
- ★ 4.9.5 는 플래그 자체가 없다(5.8 부터).

### 5. ★★★ 방출물에 **흔적이 없다**(`let b;` 만) · `--erasableSyntaxOnly` 는 **`(1,1) TS1294`**

**출력**

```ts
// eqtype36.cts
import type Box = require("./box36.cjs");
let b: Box | undefined;
export {};
```

```text
===== tsc --pretty false -t es2022 --strict --module nodenext --outDir e36q eqtype36.cts (tsc exit=0) =====
===== 방출된 e36q/eqtype36.cjs =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
let b;
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext --erasableSyntaxOnly eqtype36.cts (tsc exit=1) =====
eqtype36.cts(1,1): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
```

**왜 그런가**

- ★★★ `import type` 이라 **값을 안 만든다** — 방출물에 `require` 가 없다.
- ★★★ 그래도 막혔다 — 이 플래그는 **방출물이 아니라 꼴**(`import … = require(…)`)을 보고 판정한다(9번).

### 6. ★★ `importsNotUsedAsValues`·`preserveValueImports` — **4.9.5 `OK` · 5.9.3 `TS5102` · 7.0.2 `TS5023`** · 새 셋은 4.9.5 만 `TS5023` · `isolatedModules` 는 세 판 `OK` · **5 / 6**

**출력**

```text
===== bash ts34b-flags36.sh (sh exit=0) =====
플래그                          7.0.2      5.9.3      4.9.5
isolatedModules                    OK         OK         OK
importsNotUsedAsValues             TS5023     TS5102     OK
preserveValueImports               TS5023     TS5102     OK
verbatimModuleSyntax               OK         OK         TS5023
erasableSyntaxOnly                 OK         OK         TS5023
rewriteRelativeImportExtensions    OK         OK         TS5023

세 판이 한 답이 아닌 행 5 / 6
```

```ts
// lib36.mts
console.log("lib36 evaluated");
export interface Shape {
    area: number;
}
export const version = 1;
```

```text
===== node "$TSC_OLD" --pretty false --noEmit --module nodenext --importsNotUsedAsValues <remove · preserve> lib36.mts (sh exit=0) =====
---- remove
(exit 0)
---- preserve
error TS5102: Option 'importsNotUsedAsValues' has been removed. Please remove it from your configuration.
  Use 'verbatimModuleSyntax' instead.
(exit 2)
```

**왜 그런가**

- ★★★ 5.9.3 은 「**제거됐다 — `verbatimModuleSyntax` 를 써라**」(`TS5102`), 7.0.2 는 「**모른다**」(`TS5023`). 제거 **안내**까지 사라졌다.
- ★★ 5.9.3 은 **기본값(`remove`)을 주면 조용히** 받는다 — 제거가 **기본값과 다른 값에서만** 드러난다.

### 7. ★★★ `isolatedModules` 는 「**파일 하나만 보고 변환할 수 있는 코드만 써라**」(검사 약속), `verbatimModuleSyntax` 는 「**적힌 그대로 방출한다**」(방출 약속)

- ★★ `export { Shape }` 는 파일 하나만 보면 `Shape` 가 타입인지 모른다 — 두 플래그 다 **`TS1205`** 로 「`export type` 을 쓰라」고 한다.
- ★★★ 그 뒤가 다르다. `isolatedModules` 는 **방출 규칙은 기본 그대로**라 tsc 가 (다른 파일을 보고) 지운다. `verbatimModuleSyntax` 는 **적힌 그대로** 남긴다 → node `SyntaxError`.

### 8. ★★★ **끔의 `i36a` 와 `i36b`** — 둘 다 `export {};` 로 **같다** → 기본 설정에서는 **거짓** · **`verbatimModuleSyntax` 에서만** 참(`i36a` 는 남고 `i36b` 는 지워진다)

- ★★ 기본 설정은 타입만 쓰인 일반 import 를 **이미** 지운다. `import type` 은 **그 판단을 표시로 굳힐** 뿐이다.
- ★★★ 「번들이 줄어든다」는 **이 문서가 재지 않은 주장**이다 — 잰 것은 방출물의 줄이고, 기본 설정에서 그 줄 수는 **안 줄었다.**

### 9. ★★★ **반례다** — 방출 0줄인데 `TS1294`. 이 플래그는 **TS 전용 꼴**(`import =`·`export =`·값 있는 `namespace`·`enum`·매개변수 프로퍼티)을 보고 막는다

- ★★ [**34번 주제**](../34-namespace-place/) 3절의 6 / 6 은 **그 여섯 칸의 관찰**이다 — 거기서도 「규칙은 꼴」이라고 적어 두었다.
- ★ 방출물의 유무로 예측하면 5번에서 틀린다. 「**이 문법이 JS 에 있나**」로 예측하는 편이 맞는다.

### 10. ★★ 02편 6절의 **`ex.02d.ts`**(`import { Shape, Circle }` + `TS1484` + node `SyntaxError`) · 31편 4절의 「**`--erasableSyntaxOnly` 는 방출을 `(없음)` 판과 같게 둔다 — 검사만 한다**」

- ★★ [**02번 주제**](../02-type-checking-vs-emit/) 6절 — `TS1484` 한 건, 방출물에 `Shape` 가 남고 node 가 `does not provide an export named 'Shape'`. 1번 `i36a` 가 **같은 모양**이다.
- ★★ [**31번 주제**](../31-enum-pitfalls/) 4절 — `const enum` 격자에서 이 플래그의 방출은 플래그 없는 판과 같았다. 1번의 **0 / 8** 이 import 쪽에서 본 같은 성질이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ 방출 격자 | `bash ts34b-emit36.sh` (파일 여덟 × 플래그 넷, node 32회) | **1 / 8 · 4 / 8 · 0 / 8** |
| ★★ `erasableSyntaxOnly` 판 격자 | `bash ts34b-erase36.sh` (꼴 여섯 × 세 판) | **3 / 6** |
| ★★ `import type = require` | 방출 · `--erasableSyntaxOnly` | 흔적 없음 · `TS1294` |
| ★★ 플래그 판 격자 | `bash ts34b-flags36.sh` · 5.9.3 기본값 대조 | **5 / 6** · `remove` 는 `(exit 0)` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ `import { type T }` 의 빈 import(2번) — 문서가 적은 동작이지만 **방출물로** 다시 확인한다.
- ★★ 기본 설정의 **안 쓰인 값 import 지우기**(3번).
- ★★ `import type X = require()` 의 `TS1294`(5번).
- ★ 옛 두 옵션의 진단 코드(6번) — 5.9.3 `TS5102` → 7.0.2 `TS5023`.

**안 돌려 본 것**

- ★★ **CJS 출력의 `verbatimModuleSyntax`** · **번들러의 빈 import 처리** · **번들 크기** — 던지지 않았다.
