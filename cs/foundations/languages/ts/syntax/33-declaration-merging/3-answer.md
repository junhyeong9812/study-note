# ts/syntax/33 — 선언 병합 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 2번의 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 병합 규칙 격자이고, 급소는 3창(방출된 `.js` + `node`)이다.**\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 막히는 짝은 **`type+type`·`interface+type`·`class+class`(`TS2300`)** · `[interface+class]` 는 **`"a" | "b"` 와 `[1,"undefined"]`** · enum 짝은 **`"A" | "b"`** · **5 / 8**

**출력**

```text
===== bash ts30b-mergegrid.sh (sh exit=0) =====
[interface+interface]
    진단   OK
    탐침   "a" | "b"
[interface+class]
    진단   OK
    탐침   "a" | "b"
    node   [1,"undefined"]
[namespace+function]
    진단   OK
    탐침   "b"
    node   [1,"x"]
[namespace+enum]
    진단   OK
    탐침   "A" | "b"
    node   [0,"x"]
[namespace+class]
    진단   OK
    탐침   "b" | "prototype"
    node   [1,"x"]
[type+type]
    진단   (1,6) TS2300 (2,6) TS2300
    탐침   "a"
[interface+type]
    진단   (1,11) TS2300 (2,6) TS2300
    탐침   "a"
[class+class]
    진단   (1,7) TS2300 (2,7) TS2300
    탐침   "a"

진단 없이 합쳐진 짝 5 / 8
```

**왜 그런가**

- ★★★ `[interface+class]` — 타입에는 `b` 가 **붙었고**(탐침), 값에는 **없다**(`typeof new Thing().b` 가 `"undefined"`). `interface` 는 **타입 공간만** 채운다.
- ★★ namespace 짝 셋은 방출물에서 **대상 객체에 멤버를 다는 코드**가 되어 `node` 에서 값이 **실제로** 나온다.
- ★★ `TS2300` 은 **두 줄 다**에 나고, 탐침은 **첫 선언**(`"a"`)을 본다.

### 2. ★★★ 15행 **`"from-block-2"`** · 16행 **`"from-block-1"`** — 다르다 · 17·18행은 **한 글자도 같다** · 28 **`"literal-in-block-1"`** · 29 **`"string-in-block-2"`** · 세 판 **같다**

**출력**

```ts
// ex.33a.ts
// 같은 이름의 메서드가 두 인터페이스 블록에 -- 부르면 어느 쪽이 잡히나
interface Merged {
    pick(x: string): "from-block-1";
}
interface Merged {
    pick(x: string | number): "from-block-2";
}
type Single = {
    pick(x: string): "from-block-1";
    pick(x: string | number): "from-block-2";
};
declare const m: Merged;
declare const s: Single;

const p1: null = m.pick("a");
const p2: null = s.pick("a");
const p3: null = null as unknown as Merged["pick"];
const p4: null = null as unknown as Single["pick"];

interface Lit {
    tag(x: "on"): "literal-in-block-1";
    tag(x: string): "string-in-block-1";
}
interface Lit {
    tag(x: string): "string-in-block-2";
}
declare const l: Lit;
const p5: null = l.tag("on");
const p6: null = l.tag("off");
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.33a.ts (tsc exit=1) =====
ex.33a.ts(15,7): error TS2322: Type '"from-block-2"' is not assignable to type 'null'.
ex.33a.ts(16,7): error TS2322: Type '"from-block-1"' is not assignable to type 'null'.
ex.33a.ts(17,7): error TS2322: Type '{ (x: string): "from-block-1"; (x: string | number): "from-block-2"; }' is not assignable to type 'null'.
ex.33a.ts(18,7): error TS2322: Type '{ (x: string): "from-block-1"; (x: string | number): "from-block-2"; }' is not assignable to type 'null'.
ex.33a.ts(28,7): error TS2322: Type '"literal-in-block-1"' is not assignable to type 'null'.
ex.33a.ts(29,7): error TS2322: Type '"string-in-block-2"' is not assignable to type 'null'.
```

```text
===== bash ts30b-cmp33.sh (sh exit=0) =====
tsc Version 7.0.2 · OLD Version 5.9.3 · V49 Version 4.9.5
7.0.2 = 5.9.3 · 진단 출력 한 글자도 같다
7.0.2 = 4.9.5 · 진단 출력 한 글자도 같다
```

**왜 그런가**

| 줄 | 무엇 | 답 |
|---|---|---|
| 15 | 두 블록의 `Merged` 를 부른다 | ★★★ **`"from-block-2"`** — 뒤 블록이 먼저 |
| 16 | 한 블록의 `Single` 을 부른다 | `"from-block-1"` — 적은 순서대로 |
| 17·18 | 두 타입의 표시 | ★★★ **같은 글자** — 표시는 선언 순서 |
| 28 | `l.tag("on")` | ★★ `"literal-in-block-1"` — 단일 문자열 리터럴이 **맨 위로** |
| 29 | `l.tag("off")` | `"string-in-block-2"` — 다시 뒤 블록 먼저 |

### 3. ★★ 진단 **0줄** · 두 namespace 는 **대상에 멤버를 다는 IIFE** · `[3]` 은 **`[ '0', '1', 'Red', 'Blue', 'parse' ]`** · `--erasableSyntaxOnly` 는 **5·8·12행**

**출력**

```ts
// ex.33b.ts
// 함수와 namespace, enum 과 namespace -- 방출물과 node
function greet(name: string): string {
    return greet.prefix + name;
}
namespace greet {
    export const prefix = "hi ";
}
enum Color {
    Red,
    Blue,
}
namespace Color {
    export function parse(s: string): Color | undefined {
        return s === "red" ? Color.Red : s === "blue" ? Color.Blue : undefined;
    }
}
console.log("[1]", greet("kim"));
console.log("[2]", Color.parse("blue"));
console.log("[3]", Object.keys(Color));
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.33b.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e33n ex.33b.ts (tsc exit=0) =====
===== 방출된 e33n/ex.33b.js =====
"use strict";
// 함수와 namespace, enum 과 namespace -- 방출물과 node
function greet(name) {
    return greet.prefix + name;
}
(function (greet) {
    greet.prefix = "hi ";
})(greet || (greet = {}));
var Color;
(function (Color) {
    Color[Color["Red"] = 0] = "Red";
    Color[Color["Blue"] = 1] = "Blue";
})(Color || (Color = {}));
(function (Color) {
    function parse(s) {
        return s === "red" ? Color.Red : s === "blue" ? Color.Blue : undefined;
    }
    Color.parse = parse;
})(Color || (Color = {}));
console.log("[1]", greet("kim"));
console.log("[2]", Color.parse("blue"));
console.log("[3]", Object.keys(Color));
```

```text
===== node e33n/ex.33b.js (node exit=0) =====
[1] hi kim
[2] 1
[3] [ '0', '1', 'Red', 'Blue', 'parse' ]
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.33b.ts (tsc exit=1) =====
ex.33b.ts(5,11): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.33b.ts(8,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.33b.ts(12,11): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
```

**왜 그런가**

- ★★★ `(function (greet) { greet.prefix = "hi "; })(greet || (greet = {}));` — **이미 있는 함수 객체**에 프로퍼티를 단다. `Color` 쪽도 같은 모양으로 `Color.parse = parse;`.
- ★★★ 그래서 `Object.keys(Color)` 에 **`parse` 가 섞인다.** 숫자 enum 의 역매핑 넷 + 함수 하나.
- ★★ `TS1294` 는 **값을 만드는 선언 셋**(namespace 둘 · enum 하나)에만. `function greet` 는 안 걸린다.

### 4. ★★★ 함께 — **`exit 0`** · 하나만 — **`TS2339`** · `node` — **`TypeError [1,2,3].total is not a function`** · `noexp33` — **`TS2669`**

**출력**

```ts
// aug33.ts
declare global {
    interface Array<T> {
        total(): number;
    }
}
export {};
```

```ts
// user33.ts
try {
    console.log("total", [1, 2, 3].total());
} catch (e) {
    console.log((e as Error).constructor.name, (e as Error).message);
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict aug33.ts user33.ts ; 이어서 user33.ts 하나만 (sh exit=0) =====
(exit 0)
user33.ts(2,36): error TS2339: Property 'total' does not exist on type 'number[]'.
(exit 1)
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e33 aug33.ts user33.ts (tsc exit=0) =====
===== 방출된 e33/aug33.js =====
export {};
===== 방출된 e33/user33.js =====
"use strict";
try {
    console.log("total", [1, 2, 3].total());
}
catch (e) {
    console.log(e.constructor.name, e.message);
}
```

```text
===== node e33/user33.js (node exit=0) =====
TypeError [1,2,3].total is not a function
```

```ts
// noexp33.ts
declare global {
    interface Array<T> {
        other(): number;
    }
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict noexp33.ts (tsc exit=1) =====
noexp33.ts(1,9): error TS2669: Augmentations for the global scope can only be directly nested in external modules or ambient module declarations.
```

**왜 그런가**

- ★★★ 방출된 `aug33.js` 는 **`export {};` 한 줄** — `declare global` 은 값을 **하나도** 안 만든다. 컴파일은 통과했고 실행은 `TypeError`.
- ★★ `declare global` 은 **모듈 파일 안에서만** — `export {}` 를 빼면 `TS2669`.

### 5. ★★★ 따로 둔 스크립트 둘 — **두 파일 다 `TS2741`**(합쳐졌다) · `export {}` 를 붙인 둘 — **`exit 0`**

**출력**

```ts
// set33a.ts
interface Settings {
    port: number;
}
const first: Settings = { port: 80 };
```

```ts
// set33b.ts
interface Settings {
    host: string;
}
const second: Settings = { host: "h" };
```

```ts
// set33c.ts
interface Settings {
    port: number;
}
const first: Settings = { port: 80 };
export {};
```

```ts
// set33d.ts
interface Settings {
    host: string;
}
const second: Settings = { host: "h" };
export {};
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict set33a.ts set33b.ts ; 이어서 set33c.ts set33d.ts (sh exit=0) =====
set33a.ts(4,7): error TS2741: Property 'host' is missing in type '{ port: number; }' but required in type 'Settings'.
set33b.ts(4,7): error TS2741: Property 'port' is missing in type '{ host: string; }' but required in type 'Settings'.
(exit 1)
(exit 0)
```

**왜 그런가**

- ★★★ import·export 가 없는 파일은 **전역 스크립트**다. 두 파일의 `interface Settings` 가 **전역에서 합쳐져** `{ port; host }` 가 됐고, 각 파일의 객체가 **상대 파일의 멤버**를 빠뜨려 `TS2741`.
- ★★ `export {};` 한 줄로 파일이 **모듈**이 되어 선언이 갇혔다.

### 6. ★★★ 진단이 **원래 라이브러리 `lib33.mts`** 에서도 난다(`TS2741`) · `aug33b` 는 **`exit 0`** — 실행은 **`SyntaxError … does not provide an export named 'extra'`**

**출력**

```ts
// lib33.mts
export interface Plugin {
    name: string;
}
export function make(name: string): Plugin {
    return { name };
}
```

```ts
// aug33a.mts
import { make } from "./lib33.mjs";
declare module "./lib33.mjs" {
    interface Plugin {
        version: number;
    }
}
declare module "./lib33-typo.mjs" {
    interface Plugin {
        typo: number;
    }
}
console.log(make("x").version);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict lib33.mts aug33a.mts (tsc exit=1) =====
aug33a.mts(7,16): error TS2664: Invalid module name in augmentation, module './lib33-typo.mjs' cannot be found.
lib33.mts(5,5): error TS2741: Property 'version' is missing in type '{ name: string; }' but required in type 'Plugin'.
```

```ts
// aug33b.mts
import { make, extra } from "./lib33.mjs";
declare module "./lib33.mjs" {
    interface Plugin {
        version?: number;
    }
    function extra(): string;
}
console.log("version", make("x").version);
console.log("extra", extra());
```

```js
// run33.mjs
try {
    await import("./aug33b.mjs");
} catch (e) {
    console.log(e.constructor.name, e.message);
}
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e33b lib33.mts aug33b.mts (tsc exit=0) =====
===== 방출된 e33b/aug33b.mjs =====
import { make, extra } from "./lib33.mjs";
console.log("version", make("x").version);
console.log("extra", extra());
```

```text
===== cp run33.mjs e33b/ && cd e33b && node run33.mjs (node exit=0) =====
SyntaxError The requested module './lib33.mjs' does not provide an export named 'extra'
```

**왜 그런가**

- ★★★ 모듈 보강은 **원래 모듈의 `Plugin`** 을 바꾼다 — `lib33` 의 `make()` 가 돌려주는 `{ name }` 이 `version` 을 빠뜨려 **그 파일에서** `TS2741`. 오타 모듈은 `TS2664`.
- ★★★ `aug33b` 의 `function extra(): string;` 은 **타입만** 만든다. 방출물에 `import { make, extra }` 가 남고, ESM 링크 단계에서 **없는 export** 라 `SyntaxError`.

### 7. ★★ 「**병합된 함수 멤버는 뒤에 선언된 블록의 시그니처가 먼저 해결되고, 표시는 선언 순서로 된다**」

- ★★★ 핸드북 — 「뒤의 인터페이스 선언이 **더 높은 우선순위**를 가진다.」 15행이 그것이다.
- ★★ 표시(17·18행)가 선언 순서인 것은 **이 판의 관찰**이다. 그래서 `Single` 과 **글자가 같은데** 고른 것이 다르다.

### 8. ★★★ 「**컴파일은 깨끗하고 실행에서 없는 값을 만난다**」 — 컴파일러는 **타입 공간만** 보고, 방출물에는 병합·보강이 **값을 하나도 안 남기기** 때문

- ★★ 1번 `undefined` · 4번 `TypeError` · 6번 `SyntaxError` — 셋 다 **`tsc` 가 진단 없이 통과시킨** 줄이다.
- ★★★ 선언 병합과 보강은 **「이 이름에는 이런 멤버가 있다」는 약속**이다. 약속을 지키는 코드(믹스인 구현·폴리필·실제 export)는 **다른 곳에서** 와야 하고, 컴파일러는 그것이 **로드되는지** 모른다.

### 9. ★★★ **함께 컴파일한 파일 목록**이다 — 경계는 파일이 아니라 **프로그램(컴파일 단위)**

- ★★★ 같은 `user33.ts` 가 `aug33.ts` 와 함께면 통과, 혼자면 `TS2339`. import 는 **한 줄도** 없다.
- ★★ `tsconfig.json` 의 `include`·`files` 가 그 목록을 정한다 — **넓게 잡을수록** 전역 보강이 닿는 범위도 넓다. `tsconfig.json` 자체는 **던지지 않았다.**

### 10. ★★ **첫 선언** — 공통인 것은 **둘 다 이름 공간을 「통째로」 차지하는 선언**이라는 것

- ★★ 세 짝 모두 탐침이 `"a"`. 두 번째 선언은 **무시**되고 두 줄 다에 `TS2300`.
- ★★ `type` 은 **별칭 하나**를, `class` 는 **값과 타입 하나씩**을 통째로 만든다 — 덧붙일 틈이 없다. `interface` 와 `namespace` 는 **덧붙이는** 선언이라 합쳐진다.

### 11. ★★ 08편 1절 `Merged` 세 번 선언 · 31편 1절 **`keys` 열** · 핸드북 문장과 **어긋난다**

- ★★ [**08번 주제**](../08-interface-vs-type/) 1절 — `interface Merged` 세 번이 **진단 없이** 하나가 됐다. 1번 `[interface+interface]` 의 `"a" | "b"` 와 같은 답이다.
- ★★ [**31번 주제**](../31-enum-pitfalls/) 1절 `keys` — 숫자 enum 의 `Object.keys` 가 **넷**이었다. namespace 를 붙이자 **다섯**(`parse`).
- ★★★ 핸드북 「보강은 **새 최상위 선언**을 만들 수 없다」 — 7.0.2 는 `function extra(): string;` 을 **진단 없이** 받았다. 규칙이 바뀐 것인지·문서가 낡은 것인지·이 모양이 해당하지 않는 것인지는 **확인하지 못했다.**

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.33a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.33b.ts    exit 0 = exit 0 · 출력 한 글자도 같다
```

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ 병합 규칙 격자 | `bash ts30b-mergegrid.sh` (짝 여덟) | exit 0 · **5 / 8** |
| ★★ 오버로드 순서 | `--noEmit ex.33a.ts` · `bash ts30b-cmp33.sh` | exit 1 · 탐침 6건 · **세 판 같다** |
| namespace 병합 | `--noEmit`·`--outDir e33n`·`node`·`--erasableSyntaxOnly` | 진단 0줄 · IIFE 둘 · `[3]` 에 `parse` · `TS1294` 셋 |
| ★★★ 전역 보강 | 두 파일 / 한 파일 · 방출 · `node` | `exit 0` / `TS2339` · `export {};` · `TypeError` |
| `export {}` 유무 | 두 쌍 | `TS2741` × 2 / `exit 0` |
| ★★★ 모듈 보강 | `lib33 + aug33a` · `lib33 + aug33b` · `node run33.mjs` | `TS2664`·`TS2741`(원래 모듈) · `exit 0` · `SyntaxError` |
| `strict` 대조 | 두 파일을 `--strict false` 로 재실행 | **하나도 안 갈림** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ 보강 안의 **새 함수 선언**이 통과하는 것(6번) — 핸드북 문장과 어긋난다.
- ★★ 병합된 오버로드의 **표시 순서**(2번 17·18행).
- ★ ESM 의 없는 export 가 **`SyntaxError`** 인 것 — 엔진·모듈 방식에 매인다(CJS 라면 `undefined` 가 된다 — **던지지 않았다**).

**안 돌려 본 것**

- ★★ **`tsconfig.json` 의 `include` 로 보강 범위를 바꾸는 것** — 명령줄 파일 목록으로만 보였다.
- ★★ **스크립트 파일의 맨 `interface Array<T>`** · **default export 보강** · **import 없는 `declare module`** — 목록의 [**37**](../37-writing-declaration-files/)·[**38**](../38-ambient-global-types-configuration/)번 주제로 넘긴다.
