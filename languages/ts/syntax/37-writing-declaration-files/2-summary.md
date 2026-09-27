# ts/syntax/37 — 선언 파일 작성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Declaration Reference](https://www.typescriptlang.org/docs/handbook/declaration-files/by-example.html)(전역 변수는 `declare var`·`declare const`·`declare let` · 전역 함수는 `declare function` · 점 표기로 묶을 때는 `declare namespace`) ·
> [Handbook — Modules Reference](https://www.typescriptlang.org/docs/handbook/modules/reference.html)(`exports` 의 `types` 조건 — 35편).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> ★ 핸드북의 해당 쪽은 「전역 선언 파일과 모듈 선언 파일의 구분」을 **따로 싣지 않는다**(다른 장 — 라이브러리 구조 — 으로 넘긴다). 그 구분은 이 문서가 **던져서** 세웠다(3절).
> **실행 검증** — 본판은 아래다. ★ 5절의 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다 — 환경변수 **`TSC_OLD`·`TSC_49`**.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 3창(`.d.ts` 를 믿고 컴파일한 방출물 + `node`)이고, 둘째 기둥은 5창(`.d.ts` 방출)이다.**
> 앞 배치들에서 **부적용**이던 5창이 여기서 처음 **본체의 한쪽**이 된다 — 손으로 쓴 `.d.ts` 와 `--declaration` 이 뽑은 `.d.ts` 를 견준다(5절).
> ★★★ **37 은 33 에서 온다.** [**33번 주제**](../33-declaration-merging/)가 「**보강은 타입만 만든다** — 방출물은 `export {};` 한 줄, node 에서 `TypeError`」 · 「보이는 범위는 **함께 컴파일한 파일**」 · 「`export {}` 가 없으면 **전역 스크립트**라 파일끼리 합쳐진다」를 **이미 쟀다** — 인용한다.
> 여기는 그 「타입은 있는데 값은 없다」가 **`.d.ts` 한 장 전체**로 커진 자리다 — `.d.ts` 는 **JS 에 대한 주장**이고, tsc 는 그 주장을 **검사하지 않는다.**
> ★ [**34번 주제**](../34-namespace-place/) 4절이 `skipLibCheck` 가 옛 `.d.ts` 의 `TS1540` 을 숨기는 것을 쟀다 — 6절이 그 창을 넓힌다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)` · 탐침이 말하는 타입 | 같은 입력·같은 옵션·**같은 파일 순서**면 같은 글자다 |
| **★ 순서에 매인다** | 6절 — `skipLibCheck` 에서 **충돌한 전역 선언의 타입** | ★★★ **명령줄의 파일 순서**가 답을 바꿨다 — 결론 자체다 |
| **판에 매인다** | ★★ 5절 — `--declaration` 이 쓴 **프로퍼티 순서** | 7.0.2 와 5.9.3·4.9.5 가 **갈렸다** — 결론 자체다 |
| **판에 매인다** | 종료 코드 — ★ 7.0.2 에서 **`.d.ts` 만** 던진 `--noEmit` 이 `exit 2`(4절) | 진단 코드로 가른다 |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | 예외는 **타입과 메시지만** 찍었다 · `TS7016` 의 절대 경로는 배너의 `sed` 로 `.` 로 바꿨다 |
| **안 잰 것** | `skipLibCheck` 가 줄이는 검사 **시간** | **재지 않았다** — 이 플래그를 켜는 흔한 까닭이지만 이 문서는 **숨기는 것**만 봤다 |

## 한눈에 — 쉽게 말하면

**`.d.ts` 는 「상품 설명서」다. 설명서는 상품(JS) 옆에 붙어 있을 뿐, 상품 안을 들여다보고 쓴 것이 아니다. tsc 는 설명서만 읽고 「쓸 수 있다」를 판정하고, 실제로 상품을 쓰는 것은 node 다. 설명서가 틀리면 계산대(tsc)는 통과하고 집(node)에서 터진다.**

| 비유 | 실체 |
|---|---|
| **상품** | `lib37.mjs` — 타입이 없는 순수 JS |
| **상품 옆에 붙인 설명서** | `lib37.d.mts` — 같은 이름의 선언 파일 |
| 계산대가 **설명서만** 읽는다 | tsc 는 `.mjs` 를 안 읽는다 — `.d.mts` 로 소비자를 검사한다(1절) |
| ★★★ 설명서에 「숫자를 돌려준다」 — 실제로는 **문자열** | 2절 `total` — `exit 0`, node `1+2+3 string 1+2+31` — **에러 없이 틀린 값** |
| ★★★ 설명서에 **없는 기능**이 적혀 있다 | 2절 `average` — `exit 0`, node `SyntaxError` |
| **게시판에 붙인 공지**(누구나 본다) vs **봉투 속 편지**(뜯은 사람만) | `export` 없는 `.d.ts`(전역) vs `export` 있는 `.d.ts`(모듈)(3절) |
| 「아무거나 됩니다」 설명서 | `declare module "legacy37";` — 전부 `any`(4절) |
| ★★ 검수원이 **설명서의 오탈자를 안 본다** | `skipLibCheck` — `.d.ts` 의 진단을 건너뛴다(6절) |

- ★★★ 한 줄로 — 「**`.d.ts` 는 JS 에 대한 주장이고, tsc 는 그 주장을 검사하지 않고 믿는다. 주장이 틀리면 컴파일은 통과하고 실행이 틀린다.**」

```text
  .d.ts 의 자리 — 세 파일, 두 층

  lib37.mjs     ← node 가 실행하는 것 (tsc 는 안 읽는다)
  lib37.d.mts   ← tsc 가 읽는 것      (node 는 안 읽는다)
  use37.mts     ← 둘 다를 부른다: 검사는 .d.mts 로, 실행은 .mjs 로
                  ★ 두 파일이 서로 맞는지는 아무도 확인하지 않는다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ `.d.ts` 를 씌우면 무엇이 검사되고 무엇이 검사되지 않나** — 소비자는 검사되고(1절), `.d.ts` 와 JS 의 일치는 **검사되지 않는다**(2절).
2. **★★★ 전역 선언과 모듈 선언은 어떻게 가르나** — `export` 한 줄이 가른다(3절 · 33편). 타입 없는 패키지는 `declare module "x"` 로(4절).
3. **★★ 손으로 쓴 `.d.ts` 와 뽑은 `.d.ts` 는 무엇이 다르고, `skipLibCheck` 는 무엇을 숨기나** — 5·6절.

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **3창 — `.d.ts` 를 믿고 방출한 `.js` + `node`** | 선언이 **약속한 것**과 JS 가 **가진 것**의 차이 | 실행 결과 | **본체**(2·3절) |
| ★★★ **5창 — `.d.ts` 방출(`--declaration`)** | 컴파일러가 **쓴** 선언 · 세 판 대조 | 방출물 · `diff` | **둘째 기둥**(5절) |
| ★★ **「함께 컴파일한 파일」 대조** | 같은 소비자를 **동반 `.d.ts` 를 바꿔** 세 번 · 파일 **순서를 바꿔** 두 번 | 진단 대조 | 3·4·6절 |
| ★★ **2창 — `null` 탐침** | `skipLibCheck` 아래에서 **어느 타입이 이겼나** | 계산된 것 | 6절 |
| ★ **부적용 — 4창(종료 코드 격자)** | 한계를 칠 것이 이 주제에 없다 | — | — |

비용 — 파일 스물넷의 검사·방출·`node`(정답 파일 「실행 검증」 표) + 세 판 선언 방출.

```text
  이 주제의 축 — 「누가 무엇을 믿나」

  소비자 .ts        ← tsc 가 .d.ts 를 믿고 검사한다           (1절 — 여기서는 검사가 돈다)
  .d.ts ↔ .js       ← 아무도 대조하지 않는다                  (2절 — 거짓말이 통과한다)
  .d.ts 자체의 오류  ← tsc 가 검사한다 — skipLibCheck 면 안 한다 (6절)
  export 유무        ← 전역에 붙나, 파일 안에 갇히나            (3절)
```

### (1) ★★ `.d.ts` 를 씌우면 — 소비자는 검사된다

**언제 쓰나** — 타입 없는 JS 파일(옛 코드·생성된 코드)을 TS 에서 부를 때.

```js
// lib37.mjs
export function total(xs) {
    return xs.reduce((a, b) => a + b, 0);
}
export function label(n) {
    return "#" + n;
}
```

```ts
// lib37.d.mts
export declare function total(xs: number[]): number;
export declare function label(n: number): string;
```

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

그림 해설 — 한 단계에 한 문장.

- ★★ `use37.mts` 는 `"./lib37.mjs"` 를 import 했는데, tsc 는 **옆의 `lib37.d.mts`** 를 읽었다(35편 3절 — `.js` 를 떼고 선언 파일을 찾는 같은 길).
- ★★ **`(3,8) TS2322`**(「Type 'string' is not assignable to type 'number'.」) — `total(["a"])` 의 원소가 막혔다. **`(4,1) TS2554`**(「Expected 1 arguments, but got 0.」) — `label()`.
- ★★ **`.mjs` 의 몸통은 한 줄도 안 읽었다** — 진단은 전부 `.d.mts` 의 **시그니처**에서 나왔다. 2절이 그것을 뒤집어 본다.

비용 — `.d.ts` 는 **손으로 유지하는 두 번째 소스**다. JS 가 바뀌면 같이 고쳐야 한다(2절).

### (2) ★★★ `.d.ts` 가 거짓말하면 — 컴파일은 통과하고 node 에서 드러난다

**언제 쓰나** — 「타입이 있으니 맞겠지」를 믿기 전에.

```js
// liar37.mjs
export function total(xs) {
    return xs.join("+");
}
```

```ts
// liar37.d.mts
export declare function total(xs: number[]): number;
export declare function average(xs: number[]): number;
```

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

```js
// run37.mjs
// 방출된 두 소비자를 차례로 부른다 -- 링크 단계의 오류는 import() 가 받는다
for (const f of ["./useliar37a.mjs", "./useliar37b.mjs"]) {
    try {
        await import(f);
    } catch (e) {
        console.log(f, e.constructor.name, e.message);
    }
}
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

그림 해설 — 한 단계에 한 문장.

- ★★★ **검사 — 진단 0줄, `exit 0`.** `.d.mts` 는 `total` 이 **`number`** 를 돌려준다고, `average` 가 **있다**고 적었다. tsc 는 **그 주장을 믿었다.**
- ★★ **방출 — 소비자 둘만 나왔다**(`ls e37l`). `liar37.mjs` 도 `liar37.d.mts` 도 **방출 대상이 아니다** — 하나는 이미 JS 이고 하나는 선언이다. 배너의 `cp` 가 JS 를 옆에 가져다 놓았다.
- ★★★ **`[1] 1+2+3 string 1+2+31`** — `t` 의 타입은 `number` 인데 **실제 값은 문자열 `"1+2+3"`** 이고 `t + 1` 은 **문자열 이어 붙이기**(`"1+2+31"`)가 됐다. **에러도 경고도 없이 틀린 값**이다 — 이 문서에서 가장 조용한 칸이다.
- ★★★ **`./useliar37b.mjs SyntaxError The requested module './liar37.mjs' does not provide an export named 'average'`** — ESM 링크 단계에서 **한 줄도 실행되기 전에** 멈췄다. 33편 6절 `extra` 와 **같은 문구**다.
- ★★ 두 거짓말의 **깨지는 모양이 다르다** — 없는 이름은 **시끄럽게**(링크 에러), 틀린 반환 타입은 **조용히**(틀린 값이 흘러간다).

```text
  .d.ts 의 두 거짓말 — 같은 exit 0, 다른 결말

  주장                              실제(liar37.mjs)            node
  total(xs): number                 xs.join("+")  → 문자열      [1] 1+2+3 string 1+2+31   ← 조용히 틀린 값
  average(xs): number               (없다)                      SyntaxError … 'average'   ← 링크에서 멈춤
                                    ★ 33편의 「타입은 있는데 값은 없다」 — 여기서는 「값은 있는데 타입이 틀렸다」까지
```

비용 — `.d.ts` 의 오류는 **소비자의 버그로 보인다.** `t + 1` 이 `"1+2+31"` 인 것을 소비자 코드에서 아무리 봐도 원인이 안 나온다.

### (3) ★★★ 전역 선언 대 모듈 선언 — `export` 한 줄이 가른다

**언제 쓰나** — `<script>` 로 싣는 라이브러리(전역 변수를 만드는 것)의 타입을 쓸 때 · `.d.ts` 에 `export` 를 넣을지 말지 정할 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **`useglob37.ts` — 진단 0줄.** import 한 줄 없이 `track`·`APP_VERSION` 이 보였다. `glob37.d.ts` 에는 `export` 가 없다 — **전역 스크립트**라 그 선언이 **컴파일 전체의 전역**에 놓인다.
- ★★★ **`usemod37.ts(1,13) TS2304`**(「Cannot find name 'BUILD_ID'.」) — `mod37.d.ts` 는 `export` 가 있어 **모듈**이다. 그 선언은 **import 해야만** 보인다. 같은 컴파일에 들어 있어도 안 보인다.
- ★★ 33편 5절의 `set33a`/`set33c` 와 **같은 기제**다 — 거기서는 `.ts` 의 `interface` 가, 여기서는 `.d.ts` 의 `declare` 가 **`export` 유무로** 전역과 파일로 갈렸다.

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

- ★★ 방출 — **`useglob37.js` 하나**(`ls e37g`). `glob37.d.ts` 는 **아무것도 안 만든다.**
- ★★★ `node` — **`ReferenceError track is not defined`**. 선언은 「어딘가에 `track` 이 **있다**」는 주장이었고, 그것을 실제로 만드는 `<script>` 는 **아무도 싣지 않았다.** 33편 4절의 `TypeError`(보강한 메서드)와 같은 모양 — 여기는 **전역 이름 자체**가 없다.
- ★ `APP_VERSION.length` 까지 가지 못했다 — `try` 블록의 **첫 줄**에서 멈췄다.

```text
  export 한 줄이 가르는 두 선언 파일

  glob37.d.ts   declare const APP_VERSION …        (export 없음) → 전역 — 컴파일의 모든 파일이 본다
  mod37.d.ts    export declare const BUILD_ID …    (export 있음) → 모듈 — import 한 파일만 본다
                ★ 전역 쪽은 import 없이 보이는 대신, 그 값을 누가 싣는지 타입은 모른다 → ReferenceError
```

비용 — 전역 `.d.ts` 는 **컴파일에 든 모든 파일**의 이름 공간을 채운다(33편 4절 — 범위는 import 가 아니라 컴파일 목록). 이름이 겹치면 **다른 `.d.ts` 와 충돌**한다 — 6절이 그 충돌을 `skipLibCheck` 가 숨기는 것을 본다.

### (4) ★★ 타입 없는 모듈 — `TS7016` · `declare module "x"` · 줄임 선언

**언제 쓰나** — `.d.ts` 가 없는 JS 파일·패키지를 import 할 때.

```js
// plain37.mjs
export function hello(n) { return "hi " + n; }
```

```ts
// useplain37.mts
import { hello } from "./plain37.mjs";
console.log(hello(1));
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext useplain37.mts | sed "s#$PWD#.#g" (tsc exit=1) =====
useplain37.mts(1,23): error TS7016: Could not find a declaration file for module './plain37.mjs'. './plain37.mjs' implicitly has an 'any' type.
```

- ★★ **`TS7016`**(「Could not find a declaration file for module './plain37.mjs'. … implicitly has an 'any' type.」) — JS 파일은 **찾았는데** 선언이 없다. `--strict` 가 켜는 `noImplicitAny` 가 이것을 **에러**로 올린다.
- ★ 문구의 경로는 원래 **절대 경로**다 — 배너의 `sed` 가 `.` 으로 바꿨다.

```ts
// uselegacy37.mts
import { greet } from "legacy37";
import theme from "./theme37.css";
console.log(greet("kim"), theme.primary);
greet(1);
```

```ts
// ambient37.d.ts
declare module "legacy37" {
    export function greet(name: string): string;
}
declare module "*.css" {
    const classes: Record<string, string>;
    export default classes;
}
```

```ts
// short37.d.ts
declare module "legacy37";
declare module "*.css";
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

그림 해설 — 한 단계에 한 문장.

- ★★ **혼자** — `legacy37` · `./theme37.css` 둘 다 **`TS2307`**(「Cannot find module …」). 이번에는 JS 파일조차 **없다** — `TS7016` 과 다른 코드다.
- ★★★ **`+ ambient37.d.ts`** — `TS2307` 이 둘 다 사라지고 **`(4,7) TS2345`**(「Argument of type 'number' …」)만 남는다. `declare module "legacy37"` 가 **시그니처까지** 주었으니 `greet(1)` 이 막혔다.
  `declare module "*.css"` 는 **와일드카드** — 상대 경로 `./theme37.css` 에도 맞았다.
- ★★★ **`+ short37.d.ts`**(줄임 선언 `declare module "legacy37";`) — **`(exit 0)`**. 몸통 없는 선언은 모듈의 **모든 것을 `any`** 로 만든다 — `greet(1)` 도 통과했다.
- ★★ 셋 다 **값은 하나도 안 만든다** — `legacy37` 이라는 패키지는 이 머신 어디에도 **없다.** 방출해 node 로 돌렸다면 모듈을 못 찾았을 것으로 읽히지만 **던지지 않았다**(`node_modules` 를 만들지 않았다).

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

- ★★ **`declare module "./rel37.mjs"`**(상대 경로) → **`TS2436`**(「Ambient module declaration cannot specify relative module name.」). 앰비언트 모듈 선언은 **패키지 이름·와일드카드**용이다 — 상대 경로의 파일에는 **옆에 같은 이름의 `.d.ts`** 를 둔다(1절).
- ★★ **종료 코드가 `2`** — `--noEmit` 인데. 02편은 「`--noEmit` 은 0 또는 1」이라 적었다. 같은 판에서 한 번 더 갈라 봤다:

```text
===== tsc --pretty false --noEmit -t es2022 --strict --module nodenext broken37.d.mts ; 이어서 같은 플래그로 usebroken37.mts (sh exit=0) =====
broken37.d.mts(1,33): error TS2304: Cannot find name 'Confg'.
(exit 2)
broken37.d.mts(1,33): error TS2304: Cannot find name 'Confg'.
usebroken37.mts(3,7): error TS2322: Type 'number' is not assignable to type 'null'.
(exit 1)
```

- ★★★ **`.d.mts` 하나만** 던지면 `(exit 2)`, 그 선언을 부르는 **`.mts` 를 던지면**(같은 `TS2304` 가 나는데도) `(exit 1)`. 7.0.2 는 **입력에 방출할 파일이 없을 때** `--noEmit` 에서도 `2` 를 낸다고 읽힌다 — 까닭은 확인하지 못했다. **종료 코드로 가르지 않는 까닭**이 하나 더 생겼다.

```text
  타입 없는 모듈을 부를 때 — 이 판의 코드

  JS 파일은 있는데 .d.ts 가 없다        TS7016   (strict 의 noImplicitAny)
  파일도 선언도 없다                    TS2307
  declare module "x" { 시그니처 }       검사된다 — 틀리면 TS2345
  declare module "x";  (몸통 없음)      전부 any — 틀려도 exit 0
  declare module "./상대경로" { … }     TS2436
```

비용 — **줄임 선언은 「타입 없음」을 「타입 있음」처럼 보이게** 한다. `TS7016`·`TS2307` 은 사라지지만 검사도 같이 사라진다.

### (5) ★★★ 5창 — `--declaration` 이 쓴 `.d.ts` 와 손으로 쓴 것

**언제 쓰나** — `.d.ts` 를 손으로 쓸지, TS 소스에서 뽑을지 정할 때.

```ts
// calc37.mts
const secret = 42;
export const LIMIT = 10;
export let current = LIMIT;
export type Up = Uppercase<"ab">;
export function double(n: number) {
    return n * 2;
}
export function pick(flag: boolean) {
    return flag ? { kind: "a", n: 1 } : { kind: "b", s: "x" };
}
export class Counter {
    private count = 0;
    #hidden = 1;
    inc(): number {
        return ++this.count + this.#hidden + secret;
    }
}
```

```bash
# ts34b-dts37.sh
#!/usr/bin/env bash
# calc37.mts 의 선언 방출을 세 판으로 -- 7.0.2 판을 싣고 옛 두 판은 diff 로 견준다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
fl=(--pretty false -t es2022 --strict --module nodenext --declaration --emitDeclarationOnly)
tsc "${fl[@]}" --outDir "$D/v7" calc37.mts; r7=$?
node "$OLD" "${fl[@]}" --outDir "$D/v5" calc37.mts; r5=$?
node "$V49" "${fl[@]}" --outDir "$D/v4" calc37.mts; r4=$?
echo "tsc 종료 코드 -- 7.0.2 $r7 · 5.9.3 $r5 · 4.9.5 $r4"
echo "---- 7.0.2 가 쓴 calc37.d.mts ----"
cat "$D/v7/calc37.d.mts"
for v in v5 v4; do
  case $v in v5) name=5.9.3 ;; v4) name=4.9.5 ;; esac
  if cmp -s "$D/v7/calc37.d.mts" "$D/$v/calc37.d.mts"; then
    echo "---- 7.0.2 와 $name -- 한 글자도 같다"
  else
    echo "---- diff 7.0.2 $name ----"
    diff "$D/v7/calc37.d.mts" "$D/$v/calc37.d.mts"
  fi
done
exit 0
```

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **적지 않은 것은 추론해서 적었다** — `double` 의 반환 **`: number`**, `current` 의 **`: number`**, `pick` 의 반환 유니온. 소스에는 **없는** 타입 글자다.
- ★★★ **적은 것은 적은 그대로다** — `type Up = Uppercase<"ab">` 는 `"AB"` 로 **계산하지 않고** 그대로 남았다. [**26번 주제**](../26-mapped-types/) 0절의 「방출기는 **계산하지 않는다**」와 같은 칸이다.
  ★ 두 줄을 합치면 — 방출기는 **적힌 타입은 옮기고, 안 적힌 자리만 추론 결과로 채운다.** 26편의 문장은 **적힌 타입** 쪽의 관찰이다.
- ★★ **`export const LIMIT = 10`** → `export declare const LIMIT = 10;` — `const` 의 리터럴은 **값째** 남는다(타입은 `10`). `let current = LIMIT` 은 **`number`** 로 넓어졌다([**11번 주제**](../11-literal-types-and-as-const/)의 넓히기).
- ★★ **`pick` 의 두 갈래에 `s?: undefined`·`n?: undefined` 가 붙었다** — 소스에 없는 프로퍼티다. 객체 리터럴 유니온을 **서로 맞춰** 적었다.
- ★★ **클래스** — `private count = 0` 은 **`private count;`**(타입 없이 이름만), `#hidden` 은 **`#private;`** 한 줄로 **뭉개졌다.** 모듈 지역 `secret` 은 **없다.**
- ★★★ **판 대조 — 7.0.2 와 5.9.3·4.9.5 가 갈렸다.** `diff` 가 **둘째 갈래의 `n?: undefined` 자리**만 가리킨다 — 7.0.2 는 `kind` **앞**, 옛 두 판은 `s` **뒤**. 내용은 같고 **순서만** 다르다.
  **선언 방출의 글자는 판에 매인다** — `.d.ts` 를 저장소에 커밋해 두고 `diff` 로 보는 흐름이라면 tsc 판을 올릴 때 **의미 없는 변경**이 생긴다.

```text
  손으로 쓴 .d.ts (2절 liar37)            뽑은 .d.ts (calc37)
  ──────────────────────────             ─────────────────────────────
  JS 를 보고 사람이 적는다                 TS 소스를 보고 컴파일러가 적는다
  JS 와 어긋나도 아무도 모른다              소스와 어긋날 수 없다(소스에서 나왔다)
  모양은 사람 마음대로                      적은 것은 그대로 · 안 적은 것은 추론
                                          ★ 글자는 판에 매인다(프로퍼티 순서)
```

비용 — 뽑은 `.d.ts` 는 **소스가 TS 일 때만** 쓸 수 있다. 1·2절처럼 **소스가 JS 뿐**이면 손으로 쓰거나 `allowJs` + JSDoc 으로 뽑는다([목록의 **48번 주제**](../48-js-file-type-checking/) — 던지지 않았다).

### (6) ★★★ `skipLibCheck` — `.d.ts` 의 오류를 숨긴다

**언제 쓰나** — 거의 모든 프로젝트가 켠다(검사 시간 — **재지 않았다**). 무엇을 대가로 치르는지 볼 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★ 그냥 — **`broken37.d.mts(1,33) TS2304`**(「Cannot find name 'Confg'.」 — `Config` 의 오타) + 탐침 `p2` 의 `TS2322`(`number`).
- ★★★ **탐침 `p1: null = load()` 에는 진단이 없다** — 반환 타입 `Confg` 가 **풀리지 않아** 소비자 쪽에서는 **아무 타입이나 되는 것처럼** 굴었다. 소비자가 받는 신호는 **`.d.mts` 쪽의 `TS2304` 하나뿐**이다.
- ★★★ **`--skipLibCheck`** — 그 `TS2304` 가 **사라졌다.** 남은 것은 `p2` 의 `TS2322` 하나. 이제 `load()` 의 반환이 **망가졌다는 신호가 어디에도 없다.**

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

그림 해설 — 한 단계에 한 문장.

- ★★ 그냥 — **`dup37b.d.ts(1,13) TS2403`**(「Subsequent variable declarations must have the same type. Variable 'APP_MODE' must be of type 'string', but here has type 'number'.」) — 전역 `.d.ts` 둘이 **같은 이름을 다른 타입**으로 선언했다(3절의 충돌). 탐침은 **`string`**.
- ★★★ **`--skipLibCheck`** — `TS2403` 이 **사라지고** 탐침은 여전히 **`string`**.
- ★★★ **`--skipLibCheck` + 파일 순서만 바꿔서**(`dup37b.d.ts dup37a.d.ts`) — 탐침이 **`number`** 가 됐다. **먼저 나온 선언이 이긴다** — 그리고 그 사실을 알려 주던 진단은 **꺼져 있다.**
  「어느 `.d.ts` 가 먼저 컴파일 목록에 드나」는 `tsconfig.json` 의 `include`·`types`·의존성 설치 순서가 정한다 — **소스 한 글자 안 바꾸고 타입이 바뀔 수 있다.**
- ★ 34편 4절 — 같은 플래그가 옛 `.d.ts` 의 **`TS1540`** 도 숨겼다. `skipLibCheck` 는 **`.d.ts` 의 진단 전부**를 끈다.

```text
  skipLibCheck 가 끄는 것 — 이 문서에서 본 셋

  broken37.d.mts   반환 타입 오타          TS2304  → 꺼짐 → load() 가 조용히 아무 타입
  dup37a/b.d.ts    전역 이름 충돌          TS2403  → 꺼짐 → ★ 파일 순서가 타입을 정한다(string ↔ number)
  old34.d.ts       7.0 에서 막힌 옛 표기    TS1540  → 꺼짐 (34편 4절)
                   ★ 소비자(.ts) 쪽의 진단은 그대로 남는다 — p2 의 TS2322
```

비용 — `skipLibCheck` 는 **남이 쓴 `.d.ts` 의 오류로 내 빌드가 깨지는 것**을 막아 주는 대신, **그 오류가 내 타입을 조용히 바꾸는 것**도 가린다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  a.mjs 옆의 a.d.mts                    import "./a.mjs" 가 이 선언을 쓴다           (1·2절)
  declare const X: T;  declare function f(): T;    export 없는 .d.ts — 전역       (3절)
  export declare const X: T;            export 있는 .d.ts — 모듈(import 해야 보임)     (3절)
  declare module "pkg" { export … }     타입 없는 패키지에 시그니처                    (4절)
  declare module "*.css" { … }          와일드카드 — 상대 경로에도 맞는다               (4절)
  declare module "pkg";                 줄임 선언 — 전부 any                           (4절)
  tsc --declaration --emitDeclarationOnly    TS 소스에서 .d.ts 를 뽑는다                (5절)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| `.d.ts` 의 시그니처와 안 맞는 호출 | `TS2322` · `TS2554` · `TS2345` | 1·4절 |
| `export` 있는 `.d.ts` 의 이름을 import 없이 | `TS2304` | 3절 |
| `.d.ts` 없는 JS 파일을 import(`strict`) | `TS7016` | 4절 |
| 파일도 선언도 없는 모듈 | `TS2307` | 4절 |
| `declare module "./상대경로"` | `TS2436` | 4절 |
| `.d.ts` 안의 없는 타입 이름 | `TS2304` — ★ `skipLibCheck` 면 **안 난다** | 6절 |
| 전역 `.d.ts` 둘이 같은 `var` 를 다른 타입으로 | `TS2403` — ★ `skipLibCheck` 면 **안 난다** | 6절 |

**규칙 불릿**

- ★★★ **tsc 는 `.d.ts` 를 믿는다** — JS 와의 일치는 검사하지 않는다(2절).
- ★★★ **`export` 가 없는 `.d.ts` 는 전역, 있으면 모듈**이다(3절 · 33편 5절).
- ★★ **몸통 없는 `declare module "x";` 는 전부 `any`** 다(4절).
- ★★ **`--declaration` 은 적힌 타입은 옮기고, 안 적힌 자리를 추론으로 채운다** — 글자는 판에 매인다(5절).
- ★★★ **`skipLibCheck` 는 `.d.ts` 의 진단을 전부 끈다** — 오타·충돌·옛 표기(6절 · 34편 4절).

## 어디서 틀리나

- ★★★ 「**`.d.ts` 가 있으니 그 라이브러리는 그렇게 동작한다**」 — `.d.ts` 는 **주장**이다. 틀린 반환 타입은 **조용히** 틀린 값을 흘린다(2절 `1+2+31`).
- ★★★ 「**컴파일이 통과했으니 import 한 이름은 있다**」 — `.d.ts` 에만 있으면 ESM 링크 단계의 `SyntaxError`(2절).
- ★★★ 「**`.d.ts` 에 적은 전역은 어디서든 쓸 수 있다**」 — **타입만** 어디서든 보인다. 값은 누가 `<script>` 로 실어야 한다 — 아니면 `ReferenceError`(3절).
- ★★ 「**`.d.ts` 에 `export` 를 하나 넣어도 나머지는 전역이다**」 — `export` 가 하나라도 있으면 **파일 전체가 모듈**이다(3절 · 33편 5절).
- ★★ 「**`declare module "x";` 로 급히 막아 두면 나중에 타입이 생긴다**」 — **전부 `any`** 라 틀린 호출도 통과한다(4절).
- ★★ 「**`--declaration` 은 소스의 타입을 그대로 옮긴다**」 — **안 적은 자리는 추론해서** 적는다. 그리고 판마다 글자가 다를 수 있다(5절).
- ★★★ 「**`skipLibCheck` 는 검사 시간만 줄인다**」 — `.d.ts` 의 오류를 숨겨 **파일 순서가 타입을 바꾸는** 것도 가린다(6절).

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(핸드북)** | 전역 변수는 `declare var/const/let`, 전역 함수는 `declare function`, 점 표기는 `declare namespace` | Declaration Reference |
| **컴파일러 동작** | `.d.ts` 는 **검사 입력**이고 JS 와 대조하지 않는다 · `.d.ts` 는 **방출하지 않는다** | 2절 — 방출물에 소비자만 |
| **컴파일러 동작** | `export` 유무가 선언 파일을 전역/모듈로 가른다 | 3절 · 33편 5절 |
| **★ 이 판(7.0.2)의 관찰** | 풀리지 않는 반환 타입(`Confg`)을 받은 소비자 탐침에 **진단 없음** | 6절 `p1` |
| **★ 이 판의 관찰** | `skipLibCheck` 에서 충돌한 전역의 타입이 **파일 순서**로 정해진다 | 6절 — 두 순서를 던졌다 |
| **★ 판 격자** | `--declaration` 의 **프로퍼티 순서**가 7.0.2 와 5.9.3·4.9.5 에서 다르다 | 5절 `diff` |
| **★ 이 판의 관찰** | `.d.ts` 만 던진 `--noEmit` 이 `exit 2` — `.mts` 가 들면 `exit 1` | 4절 — 02편의 「0 또는 1」과 어긋난다 |
| **호스트(node v18)** | 없는 export 는 ESM 링크 단계 `SyntaxError` · 없는 전역은 `ReferenceError` | 2·3절 |
| **★ 부적용 — 4창(종료 코드 격자)** | 한계를 칠 것이 없다 | — |
| **안 잰 것** | `skipLibCheck` 의 검사 시간 절약 · 없는 패키지를 node 가 부르는 결과 | **재지 않았다** · `node_modules` 를 만들지 않았다 |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★★ **손으로 쓴 `.d.ts`** — 소스가 **JS 뿐**이고 바꿀 수 없을 때 · **JS 와 같이 고칠** 사람이 있을 때 | JS 와 따로 노는 `.d.ts` — 2절의 두 거짓말 |
| ★★★ **`--declaration`** — 소스가 TS 면 **뽑는다**. 소스와 어긋날 수 없다 | 뽑은 `.d.ts` 의 **글자**에 기대는 비교 — 판이 오르면 순서가 바뀐다(5절) |
| ★★ **전역 `.d.ts`(export 없음)** — `<script>` 로 싣는 라이브러리 · 빌드 도구가 주입하는 상수 | 모듈 라이브러리를 전역으로 적기 — 값이 어디서 오는지 타입이 모른다(3절) |
| ★ **`declare module "x" { 시그니처 }`** — 타입 없는 패키지 | **줄임 선언 `declare module "x";`** — 임시로만, 검사가 사라진다(4절) |
| **`skipLibCheck`** — 의존성의 `.d.ts` 오류로 빌드가 막힐 때(대가를 알고) | ★★★ **자기가 쓴 `.d.ts`** 가 있는 프로젝트에서 끄지 않고 두기 — 그 파일의 오류가 **안 보인다**(6절). 가끔 끄고 한 번 던져 본다 |

## 핵심 문장

1. **`.d.ts` 는 JS 에 대한 주장이고, tsc 는 그 주장을 검사하지 않고 믿는다** — 틀린 반환 타입은 `1+2+31` 같은 **조용히 틀린 값**을, 없는 이름은 링크 단계 `SyntaxError` 를 낳는다.
2. **`export` 한 줄이 선언 파일을 전역과 모듈로 가른다** — 전역은 import 없이 보이지만 **값을 누가 싣는지 모른다**(`ReferenceError`).
3. **`--declaration` 은 적힌 타입은 옮기고 안 적힌 자리를 추론으로 채운다** — 그 글자는 판에 매인다(7.0.2 와 옛 두 판의 프로퍼티 순서).
4. **`skipLibCheck` 는 `.d.ts` 의 진단을 전부 끈다** — 오타는 조용한 `any` 로, 충돌은 **파일 순서가 정하는 타입**으로 남는다.

## 관련 자료

- [**33번 주제** — 선언 병합](../33-declaration-merging/) — ★★★ **README 의 선행.** 보강은 타입만 만든다 · 보이는 범위는 함께 컴파일한 파일 · `export {}` 가 없으면 전역 스크립트 — 그쪽 4·5·6절이 정본이다. **여기는 그것을 `.d.ts` 한 장으로 넓힌 데서부터.**
- [**34번 주제** — `namespace` 의 자리](../34-namespace-place/) — `declare namespace` 와 `skipLibCheck` 가 `TS1540` 을 숨기는 칸(4절).
- [**35번 주제** — 모듈 해석](../35-module-resolution/) — `"./lib37.mjs"` 가 `lib37.d.mts` 로 가는 길(`.js` 를 떼고 찾는다) · `exports` 의 `types` 조건.
- [**26번 주제** — 매핑 타입](../26-mapped-types/) — 「방출기는 계산하지 않는다」(0절). 5절이 그 문장의 **짝**(안 적힌 자리는 추론한다)을 더했다.
- [목록의 **38번 주제**](../38-ambient-global-types-configuration/)(앰비언트·전역 타입 구성) — 사슬의 다음. `types`·`typeRoots`·`lib` 가 **어느 전역 `.d.ts` 를 컴파일에 넣나**(6절의 「순서」를 정하는 쪽).
- [목록의 **44번 주제**](../44-project-references-and-declaration-emit/)(프로젝트 참조와 선언 방출) · **48번 주제**(JS 파일 타입 검사) — `isolatedDeclarations` · JSDoc 에서 `.d.ts` 뽑기.

## 용어 풀이

> **선언 파일(`.d.ts`·`.d.mts`·`.d.cts`)** — 타입만 적는 파일. 방출물이 없다. 같은 이름의 JS 옆에 두면 tsc 가 그 JS 대신 읽는다.\
> 예: 1절 `lib37.d.mts`.

> **`declare`** — 「이 이름은 **어딘가에** 있다 — 여기서 만들지 않는다」. 값을 만들지 않는 선언.\
> 예: 3절 `declare const APP_VERSION: string;`.

> **전역 선언 파일** — `import`·`export` 가 없는 `.d.ts`. 선언이 컴파일 전체의 전역에 놓인다.\
> 예: 3절 `glob37.d.ts`.

> **모듈 선언 파일** — `export` 가 있는 `.d.ts`. import 해야 보인다.\
> 예: 3절 `mod37.d.ts` — `TS2304`.

> **앰비언트 모듈 선언** — `declare module "이름" { … }`. 파일이 아니라 **이름**에 타입을 붙인다. 상대 경로는 안 된다(`TS2436`).\
> 예: 4절 `ambient37.d.ts`.

> **줄임 선언(shorthand ambient module)** — 몸통 없는 `declare module "x";`. 그 모듈의 모든 것이 `any`.\
> 예: 4절 `short37.d.ts`.

> **`skipLibCheck`** — 선언 파일(`.d.ts`)의 타입 검사를 건너뛴다. 소비자 쪽 검사는 그대로다.\
> 예: 6절.

> **`TS7016`** — 「Could not find a declaration file for module '…'. '…' implicitly has an 'any' type.」\
> 예: 4절 `useplain37.mts`.

> **`TS2403`** — 「Subsequent variable declarations must have the same type. …」 같은 `var` 를 다른 타입으로 두 번.\
> 예: 6절 `dup37b.d.ts`.

## 더 들어가면

- **`.d.ts` 와 JS 의 일치를 검사하는 법** — 이 문서는 「tsc 는 안 한다」까지다. 소스가 JS 면 `allowJs` + `checkJs` + `--declaration` 으로 **JS 에서 뽑는** 길이 있다([목록의 **48번 주제**](../48-js-file-type-checking/)). **던지지 않았다.**
- **`declare global` 을 모듈 `.d.ts` 안에서** — 모듈 선언 파일이면서 전역을 보강하는 꼴. 33편 4절이 `.ts` 쪽을 쟀다 — `.d.ts` 쪽은 **던지지 않았다.**
- **`typesVersions`·`exports` 의 `types` 조건으로 패키지에 `.d.ts` 싣기** — 35편 3절의 추적이 `types` 조건을 보였다. 패키지 배포 자체는 **던지지 않았다.**
