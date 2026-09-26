# ts/syntax/34 — `namespace` 의 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 판 격자이고, 급소는 3창(방출된 `.js` + `node`)이다.**\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 식별자 이름의 `module` 다섯 꼴이 **7.0.2 에서만 `TS1540`** · `namespace`·`declare namespace`·`declare module "foo"` 는 세 판 다 **`OK`** · **5 / 8 · 5 / 8**

**출력**

```text
===== bash ts34b-modkw.sh (sh exit=0) =====
탐침                       7.0.2            5.9.3            4.9.5
module-value                 TS1540           OK               OK
module-dotted                TS1540 TS1540    OK               OK
module-types-only            TS1540           OK               OK
declare-module-id            TS1540           OK               OK
declare-module-id-dts        TS1540           OK               OK
namespace-value              OK               OK               OK
declare-namespace-dts        OK               OK               OK
declare-module-string-dts    OK               OK               OK

7.0.2 에서 진단이 난 탐침 5 / 8 · 7.0.2 와 5.9.3 이 갈린 탐침 5 / 8
```

**왜 그런가**

- ★★★ 7.0.2 는 **이름이 식별자인** `module` 선언을 전부 `TS1540` 으로 막는다 — 값이 있든(`module-value`) 타입만 있든(`module-types-only`) `declare` 든 `.d.ts` 든.
- ★★ `module-dotted` 는 **이름 조각마다** 하나씩 — `TS1540` 둘.
- ★★★ 5.9.3 · 4.9.5 는 같은 꼴에 **한 줄도 안 낸다.** 그래서 갈린 다섯이 **정확히** 막힌 다섯이다. 릴리스 글의 「6.0 hard deprecation」은 **6.0 이 없어 못 봤다.**
- ★★ `declare module "foo"` 는 **따옴표 이름** — 앰비언트 모듈 선언이라 대상이 아니다(6번).

### 2. ★★★ `Shapes` 는 **흔적이 없다** · `Geo.Units` 는 **IIFE 두 겹** · `scale` 은 **IIFE 의 지역 `const`** · `[3]` 은 **`[ 'meter', 'km' ]`** · `--erasableSyntaxOnly` 는 **9행 하나(열 11·15)**

**출력**

```ts
// ex.34a.ts
// 타입만 든 namespace 와 값이 든 namespace -- 방출물에 무엇이 남나
namespace Shapes {
    export interface Point {
        x: number;
        y: number;
    }
    export type Id = string;
}
namespace Geo.Units {
    export const meter = 1;
    export function km(n: number): number {
        return n * 1000 * meter;
    }
    const scale = 3;
}
const p: Shapes.Point = { x: 1, y: 2 };
console.log("[1]", p);
console.log("[2]", Geo.Units.km(2));
console.log("[3]", Object.keys(Geo.Units));
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.34a.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.34a.ts (tsc exit=1) =====
ex.34a.ts(9,11): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.34a.ts(9,15): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e34a ex.34a.ts (tsc exit=0) =====
===== 방출된 e34a/ex.34a.js =====
"use strict";
var Geo;
(function (Geo) {
    var Units;
    (function (Units) {
        Units.meter = 1;
        function km(n) {
            return n * 1000 * Units.meter;
        }
        Units.km = km;
        const scale = 3;
    })(Units = Geo.Units || (Geo.Units = {}));
})(Geo || (Geo = {}));
const p = { x: 1, y: 2 };
console.log("[1]", p);
console.log("[2]", Geo.Units.km(2));
console.log("[3]", Object.keys(Geo.Units));
```

```text
===== node e34a/ex.34a.js (node exit=0) =====
[1] { x: 1, y: 2 }
[2] 2000
[3] [ 'meter', 'km' ]
```

**왜 그런가**

- ★★★ 타입만 든 namespace 는 **지울 것만** 있다 — 방출물 0줄. 값이 든 namespace 는 **전역 변수 + 즉시 실행 함수**가 된다.
- ★★ 점 이름 `Geo.Units` 는 `(Units = Geo.Units || (Geo.Units = {}))` — **바깥 객체에 안쪽 객체를 다는** 중첩이다.
- ★★ `--erasableSyntaxOnly` 의 `TS1294` 는 **값이 든 9행에만**, 그것도 **이름 조각마다**(열 11 `Geo` · 열 15 `Units`). 2행 `Shapes` 는 안 걸렸다.

### 3. ★★ 방출 **0 · 4 · 7 · 0 · 0 · 1줄** · 방출 줄이 있는 셋이 7.0.2·5.9.3 에서 **`TS1294`**, 4.9.5 는 전부 **`TS5023`** · **6 / 6**

**출력**

```text
===== bash ts34b-erase34.sh (sh exit=0) =====
탐침             방출줄 7.0.2                      5.9.3                      4.9.5
types-only         0        OK                         OK                         TS5023
value              4        (1,11) TS1294              (1,11) TS1294              TS5023
dotted-value       7        (1,11) TS1294 (1,13) TS1294 (1,11) TS1294 (1,13) TS1294 TS5023
empty              0        OK                         OK                         TS5023
declare            0        OK                         OK                         TS5023
alias-of-declare   1        (1,42) TS1294              (1,42) TS1294              TS5023

「방출 줄이 있다」와 「7.0.2 에서 TS1294」가 같은 답을 낸 탐침 6 / 6
```

**왜 그런가**

- ★★★ `value`·`dotted-value` 는 IIFE, `alias-of-declare` 는 `var V = N.v;` 한 줄 — **셋 다 지우기만 해서는 JS 가 안 된다.** 나머지 셋은 **지우면 끝**이다.
- ★★ `alias-of-declare` 의 진단 자리(열 42)는 **`import`** — `declare namespace` 자체는 걸리지 않는다.
- ★★ 4.9.5 `TS5023` — 플래그가 **5.8** 부터라 「모르는 옵션」이다(31편 3절과 같은 칸).
- ★ 7.0.2 와 5.9.3 이 여섯 칸 다 같다.

### 4. ★★★ 7.0.2 — **`old34.d.ts(1,16) TS1540`** + 탐침 `TS2322` · `--skipLibCheck` — **`TS1540` 이 사라지고** 탐침만 남는다

**출력**

```ts
// old34.d.ts
declare module Legacy {
    const a: number;
}
```

```ts
// useold34.ts
const probe: null = Legacy.a;
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict useold34.ts old34.d.ts ; 이어서 --skipLibCheck 를 붙여 한 번 더 (sh exit=0) =====
old34.d.ts(1,16): error TS1540: A 'namespace' declaration should not be declared using the 'module' keyword. Please use the 'namespace' keyword instead.
useold34.ts(1,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
useold34.ts(1,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
```

**왜 그런가**

- ★★ 1절과 같은 표기라 `.d.ts` 안에서도 `TS1540`. 탐침 `TS2322` 가 `'number'` 를 말하므로 **선언은 쓰였다.**
- ★★★ `skipLibCheck` 는 **`.d.ts` 의 진단을 통째로** 건너뛴다 — 옛 표기의 `TS1540` 도 그 안에 든다. 그래서 의존성의 옛 선언이 **7.0 에서도 조용히** 넘어간다.

### 5. ★★★ 하나만 던져도 **진단 0줄** · 목록은 **`./ref34a.ts` · `./ref34b.ts`** · 방출은 **두 파일** · `node` 는 **`ReferenceError App is not defined`**

**출력**

```ts
// ref34a.ts
namespace App {
    export const name = "app34";
}
```

```ts
// ref34b.ts
/// <reference path="ref34a.ts" />
try {
    console.log("[1]", App.name);
} catch (e) {
    console.log((e as Error).constructor.name, (e as Error).message);
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ref34b.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --listFilesOnly ref34b.ts | grep -v '/lib\.' | sed "s#$PWD#.#" (tsc exit=0) =====
./ref34a.ts
./ref34b.ts
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e34r ref34b.ts (tsc exit=0) =====
===== 방출된 e34r/ref34a.js =====
"use strict";
var App;
(function (App) {
    App.name = "app34";
})(App || (App = {}));
===== 방출된 e34r/ref34b.js =====
"use strict";
/// <reference path="ref34a.ts" />
try {
    console.log("[1]", App.name);
}
catch (e) {
    console.log(e.constructor.name, e.message);
}
```

```text
===== node e34r/ref34b.js (node exit=0) =====
ReferenceError App is not defined
```

**왜 그런가**

- ★★ `/// <reference path>` 는 **컴파일 목록에 파일을 더한다** — 그래서 `App` 이 보였다.
- ★★★ 방출된 `ref34b.js` 에는 그 지시문이 **주석으로** 남는다. node 에게 주석은 **아무 뜻이 없다** — `ref34a.js` 를 먼저 실어 주는 이가 없으니 `App` 은 없다.

### 6. ★★ **이름의 따옴표**다 — 식별자면 namespace 의 옛 표기, 문자열이면 **앰비언트 모듈 선언**

- ★★ `declare module Foo { … }` 는 `declare namespace Foo { … }` 와 **같은 뜻**이라 7.0.2 가 표기를 막는다(`TS1540`).
- ★★★ `declare module "foo" { … }` 는 「**"foo" 라는 모듈이 있다**」는 선언이다 — 대체할 다른 표기가 없으므로 막을 까닭이 없다. 세 판 다 `OK`. [목록의 **37번 주제**](../37-writing-declaration-files/)가 이 꼴의 본체다.

### 7. ★★ **IIFE 의 함수 스코프** — `export` 한 멤버만 **객체에 대입**되고, 나머지는 **함수의 지역**으로 남는다

- ★★ 방출물 — `Units.meter = 1;` · `Units.km = km;` 는 객체의 프로퍼티, `const scale = 3;` 은 **대입이 없는 지역 선언**이다.
- ★ 지역은 **같은 IIFE 안의 코드만** 본다(클로저). `Object.keys(Geo.Units)` 가 보는 것은 **객체**다.

### 8. ★★★ **안 된다** — 여섯 칸의 관찰일 뿐이다. **규칙은 문법 꼴로 판정한다**는 반례가 36번에 있다

- ★★ 3번은 **이 여섯 꼴에서** 방출 유무와 `TS1294` 가 어긋나지 않았다는 것까지다. 탐침 수가 곧 주장의 한계다.
- ★★★ [목록의 **36번 주제**](../36-type-only-imports-and-exports/) — `import type X = require(…)` 는 **방출 0줄인데 `TS1294`** 다(거기서 던졌다). 「꼴이 `import =` 이면 막는다」가 더 맞는 설명이다.
- ★ 일반화하려면 **방출 0줄이면서 막히는 꼴**과 **방출이 있는데 안 막히는 꼴**을 찾아 던져 봐야 한다 — 반증이 확증보다 강하다.

### 9. ★★★ 「**`.ts` 쪽에 막힌 표기가 없다**」는 말하지만, `skipLibCheck` 가 켜져 있으면 **`.d.ts` 쪽은 아무것도 말하지 않는다**

- ★★ 4번 — 같은 컴파일에서 `--skipLibCheck` 하나로 `TS1540` 이 **사라졌다.** 「진단 없음」은 「**안 봤음**」과 구분되지 않는다.
- ★ 확인하려면 **`skipLibCheck` 를 끄고 한 번** 던져 본다 — 쏟아지는 진단 중 `TS1540` 만 추리면 옛 표기의 자리가 나온다.

### 10. ★★ 33편은 **`var` 줄이 없고** 여기는 **`var Geo;` 가 먼저** — 33편은 이미 있는 함수·enum 에 멤버를 달았다 · 7.0 이전에는 **`outFile` 로 한 파일에 이어 붙이기**가 실행 순서를 받쳤다 — 02편 7절 **`TS5102`**

- ★★ [**33번 주제**](../33-declaration-merging/) 3절 — `(function (greet) { … })(greet || (greet = {}));` 는 **`function greet` 가 이미 선언한 이름**을 받는다. 2번은 받을 것이 없으니 `var Geo;` 를 **새로 만든다.**
- ★★ 핸드북 — namespace 는 「`outFile` 로 이어 붙일 수 있다」. 한 파일로 이으면 `ref34a` 의 IIFE 가 **먼저** 실행된다.
- ★★★ [**02번 주제**](../02-type-checking-vs-emit/) 7절 — 7.0 에서 `outFile` 은 **`TS5102`**(옵션 제거). 그래서 파일을 건너는 namespace 는 **받쳐 줄 도구가 사라졌다.**

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ `module` 키워드 판 격자 | `bash ts34b-modkw.sh` (꼴 여덟 × 세 판) | **5 / 8 · 5 / 8** |
| ★★ namespace 방출 | `--noEmit`·`--outDir e34a`·`node`·`--erasableSyntaxOnly` | 0줄 · IIFE 두 겹 · `[ 'meter', 'km' ]` · `TS1294` 둘 |
| ★★ 방출 줄 × `--erasableSyntaxOnly` | `bash ts34b-erase34.sh` (꼴 여섯) | **6 / 6** · 4.9.5 `TS5023` |
| ★★ 옛 `.d.ts` | 그대로 / `--skipLibCheck` | `TS1540` / 사라짐 |
| ★ `/// <reference>` | `--noEmit` · `--listFilesOnly` · 방출 · `node` | 0줄 · 두 파일 · 두 파일 · `ReferenceError` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ `TS1540` 이 **7.0.2 에서 에러**인 것(1번) — 5.9.3 은 조용했다. 6.0 의 중간 단계는 **못 봤다.**
- ★★ `skipLibCheck` 가 `TS1540` 을 숨기는 것(4번).
- ★ 3번의 **6 / 6** — 탐침을 늘리면 깨질 수 있다(8번).

**안 돌려 본 것**

- ★★ **6.0** — 이 머신에 없다.
- ★ **`export namespace`** · **namespace 와 번들러의 트리 셰이킹** — 캡처하지 않았다.
