# ts/syntax/02 — 타입 검사와 코드 방출의 분리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·종료 코드·산출물 유무·방출 전문은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)`·`(node exit=N)` 도 스크립트가 찍은 값이고, 「산출물」 칸도 스크립트가 고정 목록으로 확인한 것이다.\
> ★ `--pretty false` 를 고정했다. 기본값이 `true` 라 **터미널에서는 색·소스 발췌·요약 줄이 더 붙어 보인다**.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 종료 코드 **2** · `.js` 는 **생긴다** · `node` 는 **`42 42`** 를 찍고 **0** 으로 끝난다

**출력**

```ts
// ex.02a.ts
// 타입 에러가 한 줄 있지만 나머지는 멀쩡히 돌아가는 코드다
export function twice(n: number): number {
    return n * 2;
}
const label: string = 42;
console.log(twice(21), label);
```

```text
===== tsc --pretty false ex.02a.ts (tsc exit=2) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- 산출물 -----
ex.02a.js      생김
ex.02a.d.ts    없음
```

```text
===== node ex.02a.js (node exit=0) =====
42 42
```

**왜 그런가**

- 진단은 한 건이다 — `const label: string = 42` 가 `TS2322`.
- ★★★ **그런데 `ex.02a.js` 가 생겼다.** 배너의 `tsc exit=2` 와 「산출물」 칸을 **같이** 읽어야 이 사건이 보인다.
- 종료 코드 **2** 의 뜻이 정확히 「진단이 있었고 산출물도 만들었다」다.
- 실행하면 `42 42` 다 — `twice(21)` 이 42, 그리고 `label` 자리에 **숫자 42가 그대로** 들어 있다.\
  `: string` 을 떼면 `const label = 42;` 이고, 그것은 **완벽하게 유효한 JS** 다.
- ★ `node` 종료 코드가 `0` 인 것도 중요하다 — **실행이 성공했다.** 타입 에러는 실행을 막지 않는다.

### 2. ★★★ 네 판의 세 칸

**출력**

같은 `ex.02a.ts` 를 옵션만 바꿔 네 번 더 던진다(파일은 한 글자도 안 바꿨다).

```ts
// ex.02a.ts
// 타입 에러가 한 줄 있지만 나머지는 멀쩡히 돌아가는 코드다
export function twice(n: number): number {
    return n * 2;
}
const label: string = 42;
console.log(twice(21), label);
```

```text
===== tsc --pretty false --noEmitOnError ex.02a.ts (tsc exit=1) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- 산출물 -----
ex.02a.js      없음
ex.02a.d.ts    없음
```

```text
===== tsc --pretty false --noEmit ex.02a.ts (tsc exit=1) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- 산출물 -----
ex.02a.js      없음
ex.02a.d.ts    없음
```

이어지는 두 판도 같은 파일이다.

```ts
// ex.02a.ts
// 타입 에러가 한 줄 있지만 나머지는 멀쩡히 돌아가는 코드다
export function twice(n: number): number {
    return n * 2;
}
const label: string = 42;
console.log(twice(21), label);
```

```text
===== tsc --pretty false --noCheck ex.02a.ts (tsc exit=0) =====
----- 산출물 -----
ex.02a.js      생김
ex.02a.d.ts    없음
```

```text
===== tsc --pretty false --declaration ex.02a.ts (tsc exit=2) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- 산출물 -----
ex.02a.js      생김
ex.02a.d.ts    생김
```

**왜 그런가**

| 플래그 | 진단 | 종료 코드 | 산출물 |
|---|---|---|---|
| (없음) | `TS2322` 1건 | **2** | `ex.02a.js` **생김** |
| `--noEmitOnError` | `TS2322` 1건 | **1** | 없음 |
| `--noEmit` | `TS2322` 1건 | **1** | 없음 |
| `--noCheck` | **0건** | **0** | `ex.02a.js` **생김** |
| `--declaration` | `TS2322` 1건 | **2** | `ex.02a.js` **와** `ex.02a.d.ts` 둘 다 |

- **진단이 아예 안 나오는 것은 `--noCheck`** 하나다. 검사 패스를 통째로 껐기 때문이다.
- ★★ `--noEmitOnError` 와 `--noEmit` 의 출력이 **글자 하나까지 같다.** 이 파일만으로는 구별할 수 없다.\
  차이는 **에러가 없을 때** 드러난다 — `--noEmit` 은 그때도 안 쓰고, `--noEmitOnError` 는 쓴다.
- ★ 세 판 모두 **진단 줄이 동일**하다. 플래그는 **방출만** 끄지 검사를 안 바꾼다.
- ★★ `--noCheck` 의 종료 코드 `0` 은 **통과가 아니라 안 본 것**이다. 이 표에서 `0` 이 두 뜻을 갖는 유일한 자리다.

### 3. ★★ 진단 **일곱 건** · `.js` 는 **생기고** 내용은 `"use strict";` 한 줄 · 종료 코드는 1번과 **같은 2**

**출력**

```ts
// ex.02b.ts
// 괄호가 안 닫힌 구문 에러 — 타입 에러보다 앞 단계에서 걸린다
function twice(n: number {
    return n * 2;
}
```

```text
===== tsc --pretty false ex.02b.ts (tsc exit=2) =====
ex.02b.ts(2,26): error TS1005: ',' expected.
ex.02b.ts(3,12): error TS1005: ':' expected.
ex.02b.ts(3,14): error TS1005: ',' expected.
ex.02b.ts(3,16): error TS1003: Identifier expected.
ex.02b.ts(3,17): error TS1138: Parameter declaration expected.
ex.02b.ts(4,1): error TS1138: Parameter declaration expected.
ex.02b.ts(5,1): error TS1005: ')' expected.
===== 방출된 ex.02b.js =====
"use strict";
```

**왜 그런가**

- 파서가 `(n: number {` 에서 막히고 **복구를 시도하면서** 진단 일곱 건을 냈다(`TS1005`·`TS1003`·`TS1138`).
- ★★ **그런데도 파일이 나왔다.** 방출 패스는 파싱된 만큼만 적는데, 남은 것이 `"use strict";` 뿐이었다.
- 종료 코드는 **2** — 「진단 있음 + 산출물 있음」. **에러의 종류로도 방출이 갈리지 않는다.**
- ★★★ 이 자리가 가장 위험하다. 내용이 빈 파일은 **실행해도 아무 일이 안 일어나고 에러도 안 난다** — 조용한 실패다.

### 4. ★★ 진단은 **stdout** 으로 온다 — `2>` 로 받으면 빈 파일이 된다

**출력**

```text
===== tsc --pretty false ex.02a.ts 1>split.stdout 2>split.stderr (tsc exit=2) =====
----- split.stdout (1줄) -----
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
----- split.stderr (0줄) -----
```

**왜 그런가**

- `1>` 쪽에 진단 한 줄이 들어왔고 `2>` 쪽은 **0줄**이다.
- ★ 이 배치에서 돌린 `tsc` 실행 **전부**(30여 판)에서 stderr 가 **0바이트**였다. 캡처 스크립트가 매 판 stderr 바이트 수를 따로 기록해 확인했다.
- 그래서 `tsc ... 2>log.txt` 는 **빈 파일**을 만든다. `> log.txt` 또는 `2>&1 | tee` 로 받아야 한다.
- ★ 덕분에 이 갈래는 「한 블록에서 stdout 과 stderr 가 섞여 순서가 뒤집히는」 사고에서 자유롭다 — `tsc` 는 한쪽으로만 쓰고, `console.log` 는 **다른 프로그램**(`node`)이 찍는다.

### 5. ★★ 두 줄은 `import { origin } …` 과 `export const start …` · 켜면 `TS1205`

**출력**

```ts
// ex.02c-types.ts
// 타입 하나와 값 하나를 같이 내보낸다
export interface Point {
    x: number;
    y: number;
}
export const origin: Point = { x: 0, y: 0 };
```

```ts
// ex.02c.ts
// 타입인지 값인지는 다른 파일을 봐야 안다 — isolatedModules 가 막는 자리
import { Point, origin } from "./ex.02c-types.js";

export { Point };
export const start = origin;
```

```text
===== tsc --pretty false --module esnext ex.02c.ts ex.02c-types.ts (tsc exit=0) =====
===== 방출된 ex.02c.js =====
// 타입인지 값인지는 다른 파일을 봐야 안다 — isolatedModules 가 막는 자리
import { origin } from "./ex.02c-types.js";
export const start = origin;
```

```text
===== tsc --pretty false --module esnext --isolatedModules --noEmit ex.02c.ts ex.02c-types.ts (tsc exit=1) =====
ex.02c.ts(4,10): error TS1205: Re-exporting a type when 'isolatedModules' is enabled requires using 'export type'.
```

**왜 그런가**

- 기본 컴파일은 `ex.02c-types.ts` 를 **같이 읽어서** `Point` 가 타입임을 알아냈고, 그래서 `export { Point };` 를 **통째로 지웠다**.
- ★★ **파일 하나만 보는 도구는 그 판단을 못 한다.** `ex.02c.ts` 안에는 `Point` 가 타입인지 값인지 적혀 있지 않다.
- 지우면 값 재수출이 사라지고, 안 지우면 없는 값을 재수출한다 — **어느 쪽도 안전하지 않다.**
- 그래서 `--isolatedModules` 가 `TS1205` 로 **미리 막는다**. 고치는 법은 `export type { Point };`.
- ★ 이 진단은 **방출 결과를 바꾸는 게 아니라 코드를 바꾸게 하는 것**이다 — 어떤 변환기에 태워도 같은 결과가 나오게 만든다.

### 6. ★★★ 종료 코드 **2** · 첫 줄에 `Shape` 가 **그대로 남는다** · `node` 는 **`SyntaxError`** 로 **1** 에 죽는다

**출력**

```ts
// ex.02d-lib.ts
// 타입과 값을 같이 내보내는 모듈
export interface Shape {
    area(): number;
}
export class Circle implements Shape {
    constructor(public r: number) {}
    area() {
        return 3 * this.r * this.r;
    }
}
```

```ts
// ex.02d.ts
// verbatimModuleSyntax 를 켜면 타입 이름이 import 목록에 그대로 남는다
import { Shape, Circle } from "./ex.02d-lib.js";

const s: Shape = new Circle(2);
console.log(s.area());
```

```text
===== tsc --pretty false --module esnext --verbatimModuleSyntax ex.02d.ts ex.02d-lib.ts (tsc exit=2) =====
ex.02d.ts(2,10): error TS1484: 'Shape' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
===== 방출된 ex.02d.js =====
// verbatimModuleSyntax 를 켜면 타입 이름이 import 목록에 그대로 남는다
import { Shape, Circle } from "./ex.02d-lib.js";
const s = new Circle(2);
console.log(s.area());
```

```text
===== node ex.02d.js 2>&1 | sed -E "s#^file://.*/(ex\.02d\.js)#file:…/\1#" (node exit=1) =====
file:…/ex.02d.js:2
import { Shape, Circle } from "./ex.02d-lib.js";
         ^^^^^
SyntaxError: The requested module './ex.02d-lib.js' does not provide an export named 'Shape'
    at ModuleJob._instantiate (node:internal/modules/esm/module_job:123:21)
    at async ModuleJob.run (node:internal/modules/esm/module_job:191:5)
    at async ModuleLoader.import (node:internal/modules/esm/loader:336:24)
    at async loadESM (node:internal/process/esm_loader:34:7)
    at async handleMainPromise (node:internal/modules/run_main:106:12)

Node.js v18.19.1
```

**왜 그런가**

- 진단은 `TS1484` 한 건 — 「타입은 `import type` 으로 가져오라」.
- **그런데 파일이 나왔고**, 그 파일의 첫 import 줄이 `import { Shape, Circle } from "./ex.02d-lib.js";` 다.\
  `verbatimModuleSyntax` 가 **「적힌 그대로 방출」** 이라 `Shape` 를 안 지운 것이다.
- `ex.02d-lib.js` 에는 `Shape` 라는 export 가 **없다**. 인터페이스는 [**01번 주제**](../01-what-ts-adds-and-erases/)에서 본 대로 소거됐다.
- 그래서 `node` 가 모듈을 잇는 단계에서 **`SyntaxError: The requested module … does not provide an export named 'Shape'`** 로 죽는다.
- ★★★ **`tsc` 가 낸 파일이 유효한 JS 라는 보장은 없다.** 이 주제에서 가장 센 증거다.
- 종료 코드는 `tsc` 쪽 **2**, `node` 쪽 **1** — **둘을 갈라 적어야** 사건이 보인다.
- ★ `--noEmitOnError` 를 같이 켜면 이 파일은 애초에 안 나온다. 그것이 처방이다.

### 7. ★★★ 종료 코드 세 값

| 코드 | 진단 | 산출물 | 이 배치에서 본 자리 |
|---|---|---|---|
| **0** | 없음 | 있음 | 정상 컴파일 · ★ **`--noCheck`**(검사를 끈 것) |
| **1** | 있음 | **없음** | `--noEmit` · `--noEmitOnError` |
| **2** | 있음 | **있음** | 기본값 · `--declaration` · 구문 에러 · 설정 에러 · `verbatimModuleSyntax` |

**왜 그런가**

- ★★ 두 축이 **진단 유무**와 **산출물 유무**다. 「에러가 났다」만으로는 어느 쪽인지 모른다.
- ★★★ **종료 코드 `0` 이 두 뜻을 갖는 자리는 `--noCheck`** 다 — 「검사가 통과했다」와 「검사를 안 했다」가 같은 값으로 나온다.
- ★ 그래서 CI 에서는 `--noCheck` 를 쓰지 않는다. 쓰려면 **검사를 하는 다른 단계**가 반드시 있어야 한다.

### 8. ★★ 나온다 — 그런데 **에러가 난 선언은 안 들어간다**

**출력**

소스는 1번과 같은 파일이다.

```ts
// ex.02a.ts
// 타입 에러가 한 줄 있지만 나머지는 멀쩡히 돌아가는 코드다
export function twice(n: number): number {
    return n * 2;
}
const label: string = 42;
console.log(twice(21), label);
```

```text
===== tsc --pretty false --declaration ex.02a.ts (tsc exit=2) =====
ex.02a.ts(5,7): error TS2322: Type 'number' is not assignable to type 'string'.
===== 방출된 ex.02a.d.ts =====
export declare function twice(n: number): number;
```

**왜 그런가**

- `--declaration` 판의 종료 코드가 **2** 이고 `ex.02a.d.ts` 가 **생겼다**(2번의 「산출물」 칸).
- ★ 그 `.d.ts` 에는 `export declare function twice(n: number): number;` **한 줄뿐**이다.
- 에러가 난 `const label` 은 **`export` 가 안 붙었다** — 선언 방출은 **모듈 밖으로 나가는 것**만 적으므로 애초에 대상이 아니다.
- ★★ 그래서 「`.d.ts` 가 나왔으니 타입이 맞다」도 **틀린 추론**이다. 선언 방출도 검사를 기다리지 않는다.

### 9. ★★★ 타입이 런타임에 없으므로 방출은 **타입의 정합성을 알 필요가 없다**

**왜 그런가**

- [**01번 주제**](../01-what-ts-adds-and-erases/)의 결론이 「타입은 컴파일 시각에만 있다」였다.
- 그러면 방출이 하는 일은 「**타입에만 속한 조각을 떼고 나머지를 JS 로 적는 것**」이다.
- 그 일에 **타입이 맞는지는 필요 없다.** `const label: string = 42` 에서 `: string` 을 떼면 `const label = 42;` 이고 유효한 JS 다.
- ★ 설계 의도는 **점진성**이다 — JS 프로젝트에 TS 를 얹는 도중에도, 타입이 아직 안 맞아도 **코드를 돌려 보며** 고칠 수 있게 하는 것이다.
- ★★ 그 대가가 「**빌드가 됐다 ≠ 타입이 맞다**」이고, 그래서 **종료 코드를 보는 습관**이 이 주제의 실무 결론이다.

### 10. ★★ `TS5108` 두 건 · **`tsconfig.json` 의 좌표**를 가리킨다 · 산출물은 **나온다** · 파일을 직접 주면 **안 읽힌다**

**출력**

```json
// tsconfig.02e.json
{
    "compilerOptions": {
        "target": "es5",
        "moduleResolution": "node10"
    },
    "files": ["ex.02e.ts"]
}
```

```ts
// ex.02e.ts
// tsconfig.json 으로 컴파일하는 판 — 7.0 에서 사라진 옵션 둘을 넣어 뒀다
export const n: number = "문자열";
```

```text
===== tsc --pretty false (tsc exit=2) =====
tsconfig.json(3,19): error TS5108: Option 'target=ES5' has been removed. Please remove it from your configuration.
tsconfig.json(4,29): error TS5108: Option 'moduleResolution=node10' has been removed. Please remove it from your configuration.
----- 산출물 -----
ex.02e.js      생김
```

**왜 그런가**

- 진단 두 줄이 `tsconfig.json(3,19)` 과 `tsconfig.json(4,29)` 를 가리킨다 — **소스가 아니라 설정 파일**이다.
- `target: "es5"` 와 `moduleResolution: "node10"` 이 **7.0 에서 제거된 값**이다(`TS5108`).
- ★ **그런데도 `ex.02e.js` 가 생겼다.** 설정 에러여도 방출은 돈다 — 종료 코드 **2**.
- ★★ `tsc ex.ts` 처럼 **파일을 직접 주면 `tsconfig.json` 을 무시한다.** `tsc --help` 가 「Ignoring tsconfig.json, compiles the specified files with default compiler options.」라고 적는다.\
  그래서 이 문서의 다른 블록들은 설정 파일과 무관하게 재현된다.
- ★ `TS5102` 와 `TS5108` 은 다르다 — 전자는 **옵션 이름**이 없어진 것(`outFile`·`downlevelIteration`), 후자는 **고를 수 있는 값**이 줄어든 것.

### 11. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 방출은 검사 결과를 **보지 않는다**(핸드북 「Emitting with Errors」) · `noEmit`·`noEmitOnError` 는 **방출만** 끈다(세 판의 진단이 글자까지 같다) · `isolatedModules` 는 **파일 단위로 모호한 문법**을 금지한다(`TS1205`) |
| **이 판(7.0.2)의 관찰** | 종료 코드가 **정확히 0·1·2** 라는 것 · 진단이 **stdout** 으로 나가는 것(30여 판 전수) · 구문 에러 판의 진단이 **일곱 건**이라는 것(파서 복구 전략에 달렸다) · 구문 에러 판의 산출물이 `"use strict";` **한 줄**이라는 것 |
| **7.0 에서 바뀐 것** | `target=ES5`·`moduleResolution=node10` 제거(`TS5108`) · `outFile`·`downlevelIteration` 제거(`TS5102`) · `strict` 기본 `true` · ★ **도움말에는 제거된 옵션이 아직 실려 있다** |

- ★ **「30여 판 전부 stdout 이었다」는 보장이 아니라 관찰이다.** 판이 오르면 다시 갈라 받는다.

### 12. ★★★ `tsc --noEmit` 을 별도 단계로 두고 **종료 코드로만** 판정한다

**왜 그런가**

- 판정 기준은 **`echo $?` 가 `0` 인가** 하나다. 산출물의 존재·`.d.ts` 의 존재는 **근거가 못 된다**(1·8번이 그 반례다).
- `--noEmit` 을 쓰면 종료 코드가 **0 아니면 1** 뿐이라 애매함이 없다 — 기본값의 `2` 는 「에러인데 파일도 나옴」이라 스크립트에서 읽기 나쁘다.
- 빌드 단계에서 산출물을 만들어야 한다면 **`--noEmitOnError`** 를 붙인다. 깨진 파일이 다음 단계로 흘러가지 않는다.
- ★ **`--noCheck` 는 쓰지 않는다.** 종료 코드 `0` 이 통과를 뜻하지 않게 되기 때문이다.
- ★ 로그를 남긴다면 **stdout 을 받는다** — `tsc --noEmit > tsc.log; echo $?`.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 에러 + 방출 | `tsc --pretty false ex.02a.ts` | **exit 2** · `TS2322` 1건 · `ex.02a.js` 생김 |
| 방출물 실행 | `node ex.02a.js` | **exit 0** · `42 42` |
| 방출 끄기 | `--noEmitOnError` / `--noEmit` | 둘 다 **exit 1** · 진단 동일 · 산출물 없음 |
| 검사 끄기 | `--noCheck` | **exit 0** · **진단 0건** · 산출물 생김 |
| 선언 방출 | `--declaration` | **exit 2** · `.js` 와 `.d.ts` 둘 다 · `.d.ts` 는 `twice` 한 줄 |
| 구문 에러 | `tsc --pretty false ex.02b.ts` | **exit 2** · 진단 7건 · `"use strict";` 한 줄 방출 |
| 출력 통로 | `tsc … 1>split.stdout 2>split.stderr` | stdout **1줄** · stderr **0줄**. ★ 배치 전체 30여 판에서 stderr **0바이트** |
| isolatedModules | `--module esnext --isolatedModules --noEmit` | **exit 1** · `TS1205` 1건 |
| verbatimModuleSyntax | `--module esnext --verbatimModuleSyntax` | **exit 2** · `TS1484` 1건 · `Shape` 가 import 에 남음 |
| 그 파일 실행 | `node ex.02d.js` | **exit 1** · `SyntaxError` |
| 7.0 설정 제거 | `tsconfig.json` 에 `target: es5` · `moduleResolution: node10` | **exit 2** · `TS5108` 2건 · 산출물은 생김 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- 구문 에러 판의 **진단 건수(7)** 와 산출물 내용 — 파서 복구 전략에 달렸다. 「그래도 방출된다」만 성질이다.
- 진단이 **stdout** 으로 나가는 것 — 이 판의 관찰이다.
- `TS5102`·`TS5108` 에 걸리는 **옵션 목록** — 7.0 기준이다. ★ `--help --all` 은 제거된 옵션을 아직 싣고 있으므로 **던져서** 확인한다.
- `node` 의 `SyntaxError` 문구·스택 프레임 — `v18.19.1` 기준이다.

**안 돌려 본 것**

- 프로젝트 참조(`tsc -b`)의 종료 코드 — 이 배치의 범위 밖이다(목록의 **44번 주제**). 그래서 「종료 코드는 0·1·2 셋뿐」이라고 적지 않고 「**이 배치에서 본 것이 셋**」이라고만 적었다.
