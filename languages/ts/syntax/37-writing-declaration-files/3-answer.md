# ts/syntax/37 — 선언 파일 작성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출물·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 5번의 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 3창(`.d.ts` 를 믿고 방출한 `.js` + `node`)이고, 둘째 기둥은 5창(`.d.ts` 방출)이다.**\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **`(3,8) TS2322`** · **`(4,1) TS2554`** — 둘 다 `.d.mts` 의 시그니처에서 나왔다 · 몸통은 **안 읽었다**

**출력**

```ts
// use37.mts
import { total, label } from "./lib37.mjs";
console.log("[1]", total([1, 2, 3]), label(7));
total(["a"]);
label();
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext use37.mts (tsc exit=1) =====
use37.mts(3,8): error TS2322: Type 'string' is not assignable to type 'number'.
use37.mts(4,1): error TS2554: Expected 1 arguments, but got 0.
```

**왜 그런가**

- ★★ `"./lib37.mjs"` 를 풀 때 tsc 는 같은 이름의 **`lib37.d.mts`** 를 읽는다. JS 몸통은 검사 입력이 아니다.
- ★ 그래서 진단은 `.d.mts` 에 **적힌 것**만큼이다 — 2번이 그 반대쪽을 본다.

### 2. ★★★ 검사 **`exit 0`** · 방출은 **소비자 둘뿐** · node — **`[1] 1+2+3 string 1+2+31`** 과 **`SyntaxError … 'average'`**

**출력**

```ts
// useliar37a.mts
import { total } from "./liar37.mjs";
const t: number = total([1, 2, 3]);
console.log("[1]", t, typeof t, t + 1);
```

```ts
// useliar37b.mts
import { average } from "./liar37.mjs";
console.log("[2]", average([1, 2, 3]));
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext useliar37a.mts useliar37b.mts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --module nodenext --outDir e37l useliar37a.mts useliar37b.mts (tsc exit=0) =====
===== 방출된 e37l/useliar37a.mjs =====
import { total } from "./liar37.mjs";
const t = total([1, 2, 3]);
console.log("[1]", t, typeof t, t + 1);
===== 방출된 e37l/useliar37b.mjs =====
import { average } from "./liar37.mjs";
console.log("[2]", average([1, 2, 3]));
===== ls e37l =====
useliar37a.mjs
useliar37b.mjs
```

```text
===== cp liar37.mjs run37.mjs e37l/ && cd e37l && node run37.mjs (node exit=0) =====
[1] 1+2+3 string 1+2+31
./useliar37b.mjs SyntaxError The requested module './liar37.mjs' does not provide an export named 'average'
```

**왜 그런가**

- ★★★ tsc 는 `.d.mts` 를 **믿는다** — `total` 이 `number` 를 돌려주고 `average` 가 **있다**는 주장을 대조 없이 받았다.
- ★★ `liar37.mjs`(이미 JS)도 `liar37.d.mts`(선언)도 **방출 대상이 아니다** — `e37l` 에는 소비자 둘뿐이다.
- ★★★ 실제 `total` 은 `join("+")` — **문자열**이 흘러가 `t + 1` 이 `"1+2+31"`. `average` 는 없어서 ESM 링크가 멈췄다.

### 3. ★★★ **`usemod37.ts(1,13) TS2304`** 하나 · 방출은 **`useglob37.js` 하나** · node **`ReferenceError track is not defined`**

**출력**

```ts
// glob37.d.ts
declare const APP_VERSION: string;
declare function track(event: string): void;
```

```ts
// mod37.d.ts
export declare const BUILD_ID: string;
```

```ts
// useglob37.ts
try {
    track("open");
    console.log("[1]", APP_VERSION.length);
} catch (e) {
    console.log((e as Error).constructor.name, (e as Error).message);
}
```

```ts
// usemod37.ts
console.log(BUILD_ID);
export {};
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict useglob37.ts usemod37.ts glob37.d.ts mod37.d.ts (tsc exit=1) =====
usemod37.ts(1,13): error TS2304: Cannot find name 'BUILD_ID'.
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e37g useglob37.ts glob37.d.ts (tsc exit=0) =====
===== ls e37g =====
useglob37.js
===== 방출된 e37g/useglob37.js =====
"use strict";
try {
    track("open");
    console.log("[1]", APP_VERSION.length);
}
catch (e) {
    console.log(e.constructor.name, e.message);
}
```

```text
===== node e37g/useglob37.js (node exit=0) =====
ReferenceError track is not defined
```

**왜 그런가**

- ★★★ `glob37.d.ts` 는 `export` 가 없어 **전역** — 컴파일에 든 모든 파일이 본다. `mod37.d.ts` 는 `export` 가 있어 **모듈** — import 없이는 안 보인다.
- ★★ `.d.ts` 는 방출물이 없다. `track` 은 **선언만** 있고 값은 아무도 싣지 않았다.

### 4. ★★ `useplain37` — **`TS7016`** · `uselegacy37` — 혼자 **`TS2307` 둘** / `ambient37` 와 **`TS2345` 하나** / `short37` 와 **`(exit 0)`** · `rel37` — **`TS2436`** · 종료 코드 **`2`**

**출력**

```ts
// useplain37.mts
import { hello } from "./plain37.mjs";
console.log(hello(1));
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext useplain37.mts | sed "s#$PWD#.#g" (tsc exit=1) =====
useplain37.mts(1,23): error TS7016: Could not find a declaration file for module './plain37.mjs'. './plain37.mjs' implicitly has an 'any' type.
```

```ts
// uselegacy37.mts
import { greet } from "legacy37";
import theme from "./theme37.css";
console.log(greet("kim"), theme.primary);
greet(1);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext uselegacy37.mts [ · + ambient37.d.ts · + short37.d.ts ] (sh exit=0) =====
---- uselegacy37.mts (혼자)
uselegacy37.mts(1,23): error TS2307: Cannot find module 'legacy37' or its corresponding type declarations.
uselegacy37.mts(2,19): error TS2307: Cannot find module './theme37.css' or its corresponding type declarations.
(exit 1)
---- uselegacy37.mts ambient37.d.ts
uselegacy37.mts(4,7): error TS2345: Argument of type 'number' is not assignable to parameter of type 'string'.
(exit 1)
---- uselegacy37.mts short37.d.ts
(exit 0)
```

```ts
// rel37.d.ts
declare module "./rel37.mjs" {
    export const a: number;
}
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict rel37.d.ts (tsc exit=2) =====
rel37.d.ts(1,16): error TS2436: Ambient module declaration cannot specify relative module name.
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext broken37.d.mts ; 이어서 같은 플래그로 usebroken37.mts (sh exit=0) =====
broken37.d.mts(1,33): error TS2304: Cannot find name 'Confg'.
(exit 2)
broken37.d.mts(1,33): error TS2304: Cannot find name 'Confg'.
usebroken37.mts(3,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
```

**왜 그런가**

- ★★ `TS7016` 은 **JS 파일은 찾았는데 선언이 없다**, `TS2307` 은 **아무것도 못 찾았다** — 코드가 두 상태를 가른다.
- ★★★ `declare module "legacy37" { … }` 는 **시그니처**를 줘서 `greet(1)` 을 막고, 줄임 선언은 **전부 `any`** 라 막지 않는다.
- ★★ 앰비언트 모듈 선언은 **상대 경로를 못 받는다**(`TS2436`) — 상대 경로의 JS 에는 옆에 같은 이름의 `.d.ts` 를 둔다.
- ★★ 종료 코드 — `.d.mts` 만 던지면 `2`, `.mts` 가 들면 `1`(같은 `TS2304` 인데도). 7.0.2 의 관찰이고 까닭은 확인하지 못했다.

### 5. ★★★ `secret` **없음** · `Up` **적은 그대로**(`Uppercase<"ab">`) · `double` **`: number` 가 붙음** · `pick` **양쪽에 `?: undefined`** · `Counter` **`#private;`·`private count;`** · 옛 두 판과 **`n?: undefined` 의 자리만** 다르다

**출력**

```text
===== bash ts34b-dts37.sh (sh exit=0) =====
tsc 종료 코드 -- 7.0.2 0 · 5.9.3 0 · 4.9.5 0
---- 7.0.2 가 쓴 calc37.d.mts ----
export declare const LIMIT = 10;
export declare let current: number;
export type Up = Uppercase<"ab">;
export declare function double(n: number): number;
export declare function pick(flag: boolean): {
    kind: string;
    n: number;
    s?: undefined;
} | {
    n?: undefined;
    kind: string;
    s: string;
};
export declare class Counter {
    #private;
    private count;
    inc(): number;
}
---- diff 7.0.2 5.9.3 ----
10d9
<     n?: undefined;
12a12
>     n?: undefined;
---- diff 7.0.2 4.9.5 ----
10d9
<     n?: undefined;
12a12
>     n?: undefined;
```

**왜 그런가**

- ★★★ 방출기는 **적힌 타입은 옮기고**(`Up`), **안 적힌 자리는 추론 결과로 채운다**(`double`·`current`·`pick`).
- ★★ `private` 멤버는 **이름만**, `#` 멤버는 **`#private;` 한 줄**로 — 바깥에서 쓸 수 없는 것의 **존재만** 남긴다.
- ★★★ 7.0.2 는 둘째 갈래의 `n?: undefined` 를 **앞에**, 5.9.3·4.9.5 는 **뒤에** 적었다 — **같은 타입, 다른 글자**.

### 6. ★★★ `usebroken37` — 없이 **`TS2304` + `TS2322`**, 있이 **`TS2322` 만** · `p1` 은 **양쪽 다 진단 없음** · `usedup37` — **`TS2403` + `string`** / **`string`** / **`number`**

**출력**

```ts
// broken37.d.mts
export declare function load(): Confg;
export declare function size(): number;
```

```ts
// usebroken37.mts
import { load, size } from "./broken37.mjs";
const p1: null = load();
const p2: null = size();
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext usebroken37.mts ; 이어서 --skipLibCheck 를 붙여 한 번 더 (sh exit=0) =====
broken37.d.mts(1,33): error TS2304: Cannot find name 'Confg'.
usebroken37.mts(3,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
usebroken37.mts(3,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
```

```ts
// dup37a.d.ts
declare var APP_MODE: string;
```

```ts
// dup37b.d.ts
declare var APP_MODE: number;
```

```ts
// usedup37.ts
const probe: null = APP_MODE;
export {};
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict [--skipLibCheck] usedup37.ts <두 .d.ts 를 이 순서로> (sh exit=0) =====
---- (플래그 없음) usedup37.ts dup37a.d.ts dup37b.d.ts
dup37b.d.ts(1,13): error TS2403: Subsequent variable declarations must have the same type.  Variable 'APP_MODE' must be of type 'string', but here has type 'number'.
usedup37.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 1)
---- --skipLibCheck usedup37.ts dup37a.d.ts dup37b.d.ts
usedup37.ts(1,7): error TS2322: Type 'string' is not assignable to type 'null'.
(exit 1)
---- --skipLibCheck usedup37.ts dup37b.d.ts dup37a.d.ts
usedup37.ts(1,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
```

**왜 그런가**

- ★★★ `skipLibCheck` 는 **`.d.ts` 의 진단**(`TS2304`·`TS2403`)만 끈다. 소비자 `.mts`·`.ts` 의 `TS2322` 는 남는다.
- ★★★ `load()` 의 반환 `Confg` 는 **풀리지 않은 타입**이라 `p1: null` 대입에 아무 말이 없다 — 그 사실을 알리던 유일한 신호가 `.d.mts` 의 `TS2304` 였다.
- ★★★ 충돌한 전역 `var` 는 **먼저 나온 선언**의 타입이 된다 — `TS2403` 이 꺼지면 **파일 순서가 조용히** 타입을 정한다.

### 7. ★★★ **없는 이름은 ESM 링크 단계에서 잡히고, 틀린 타입은 아무 데서도 안 잡힌다**

- ★★ `useliar37b` 의 `import { average }` 는 node 가 **실행 전에** 모듈의 export 목록과 맞춘다 — 없으니 `SyntaxError`.
- ★★★ `useliar37a` 의 `total` 은 **있다** — 링크는 통과하고, 돌려준 값의 **타입은 런타임이 검사하지 않는다.** 그래서 틀린 값이 `t + 1` 까지 흘렀다(33편의 「타입은 있는데 값은 없다」에 「**값은 있는데 타입이 틀렸다**」가 더해진다).

### 8. ★★★ **`export` 없는 `glob37.d.ts` 가 전역 선언이고 같은 컴파일에 들었기 때문**에 보였고, **그 값을 만드는 코드를 아무도 싣지 않았기 때문**에 없었다

- ★★ 전역 선언이 닿는 범위는 import 가 아니라 **컴파일 목록**이다(33편 4절).
- ★★ `declare` 는 「어딘가에 있다」는 주장이다. `<script>` 로 라이브러리를 먼저 싣는 **HTML** 이 그 「어딘가」인데, node 로 파일 하나만 돌리면 그 자리가 비어 있다.

### 9. ★★★ 줄임 선언은 **소비자 쪽** 진단(`TS2307`·`TS2345`)을 없애고 **검사도 없앤다**(전부 `any`) · `skipLibCheck` 는 **`.d.ts` 쪽** 진단을 없애고 **소비자 검사는 남긴다**

- ★★ 4번 — `short37.d.ts` 와 함께면 `greet(1)` 도 `(exit 0)`. 소비자가 **틀려도** 통과한다.
- ★★ 6번 — `--skipLibCheck` 에서도 `p2` 의 `TS2322` 는 남았다. 끈 것은 **선언 파일 안**의 진단이다. 대신 그 파일이 망가져 있으면 소비자가 받는 타입이 **조용히** 달라진다(`p1`·순서).

### 10. ★★★ **내용이 같아도 글자는 판마다 다를 수 있다** — tsc 판을 올리면 **의미 없는 `diff`** 가 생긴다

- ★★ 5번 — `n?: undefined` 한 줄이 **자리만** 옮겼다. 타입으로는 같다(프로퍼티 순서는 객체 타입의 뜻을 안 바꾼다).
- ★★ 「`.d.ts` 의 `diff` = 공개 API 의 변경」으로 읽으면 **판 변경이 API 변경처럼** 보인다. 비교는 **판을 고정한 뒤**에 한다.

### 11. ★★ 33편 4절 **`TypeError [1,2,3].total is not a function`**(보강한 메서드에 값이 없다) · 34편 4절 **`TS1540`** · 「**안 적힌 자리는 추론해서 적는다**」

- ★★ [**33번 주제**](../33-declaration-merging/) 4절 — `declare global` 로 더한 `total()` 이 **타입만** 있어 `TypeError`. 3번은 **전역 이름 자체**가 없어 `ReferenceError`.
- ★★ [**34번 주제**](../34-namespace-place/) 4절 — `--skipLibCheck` 가 옛 `.d.ts` 의 `TS1540` 을 숨겼다. 6번의 `TS2304`·`TS2403` 와 같은 줄에 선다.
- ★★ [**26번 주제**](../26-mapped-types/) 0절은 **적힌 타입**(`Uppercase<"ab">`)이 그대로 남는 것을 봤다. 5번의 `double` 은 **안 적힌 반환 타입**을 방출기가 **추론해서** 적은 칸이다 — 둘은 모순이 아니라 **한 규칙의 두 면**이다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★ `.d.ts` 로 검사 | `--noEmit use37.mts` | `TS2322` · `TS2554` |
| ★★★ `.d.ts` 의 거짓말 | `--noEmit` · 방출 · `node run37.mjs` | `exit 0` · 소비자 둘 · `1+2+31` · `SyntaxError` |
| ★★★ 전역 대 모듈 | 네 파일 `--noEmit` · 방출 · `node` | `TS2304`(모듈 쪽) · 파일 하나 · `ReferenceError` |
| ★★ 타입 없는 모듈 | `useplain37` · `uselegacy37` × 3 · `rel37` · 종료 코드 대조 | `TS7016` · `TS2307`/`TS2345`/0 · `TS2436` · `2`/`1` |
| ★★★ 선언 방출 | `bash ts34b-dts37.sh` (세 판) | 추론 · 그대로 · **`n?: undefined` 자리만 다르다** |
| ★★★ `skipLibCheck` | `usebroken37` × 2 · `usedup37` × 3 | `TS2304` 꺼짐 · `TS2403` 꺼짐 · **순서로 `string`↔`number`** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **`--declaration` 의 프로퍼티 순서**(5번) — 이미 판마다 달랐다.
- ★★ **풀리지 않는 타입을 받은 소비자의 침묵**(6번 `p1`).
- ★★ **`.d.ts` 만의 `--noEmit` 종료 코드 `2`**(4번).
- ★ `skipLibCheck` 아래 **먼저 나온 선언이 이기는 것**(6번) — 규칙으로 문서화된 것을 확인하지 못했다.

**안 돌려 본 것**

- ★★ **없는 패키지(`legacy37`)를 node 가 부르는 결과** — `node_modules` 를 만들지 않았다.
- ★ **`allowJs`·`checkJs` 로 JS 에서 `.d.ts` 뽑기** · **모듈 `.d.ts` 안의 `declare global`** · **`skipLibCheck` 의 시간 절약** — 던지지 않았다.
