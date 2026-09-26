# ts/syntax/37 — 선언 파일 작성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **37 은 33 에서 온다** — [**33번 주제**](../33-declaration-merging/)가 「보강은 타입만 만든다」 · 「보이는 범위는 함께 컴파일한 파일」 · 「`export {}` 가 없으면 전역 스크립트」를 이미 쟀다.
> 여기서는 그것이 **`.d.ts` 한 장**으로 커진 자리 — 타입 없는 JS 에 씌운 선언이 **JS 와 어긋나면** 무엇이 일어나는지를 가른다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 5번의 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★★ 이 주제는 **파일이 여럿**이다 — **어느 파일을 함께 컴파일했는가**(와 그 **순서**)가 답을 바꾼다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 타입 없는 JS 에 선언 파일을 씌우면 (예측)

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

- `tsc --noEmit --module nodenext use37.mts` 는 어느 줄에 무엇을 내는가? tsc 는 `lib37.mjs` 의 몸통을 읽었는가?

### 2. 선언 파일과 JS 가 다를 때 (예측)

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

- 두 소비자를 함께 `--noEmit` 하면? `--outDir e37l` 로 방출하면 `e37l` 에 무엇이 생기는가?
- `cp liar37.mjs run37.mjs e37l/ && cd e37l && node run37.mjs` 는 무엇을 찍는가?

### 3. `export` 가 있는 선언 파일과 없는 선언 파일 (예측)

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

- 네 파일을 함께 `--noEmit` 하면 어느 파일에 무엇이 나는가?
- `useglob37.ts glob37.d.ts` 를 `--outDir e37g` 로 방출하면 파일이 몇 개 나오고, `node e37g/useglob37.js` 는 무엇을 찍는가?

### 4. 타입 없는 모듈을 부를 때 (예측)

```js
// plain37.mjs
export function hello(n) { return "hi " + n; }
```

```ts
// useplain37.mts
import { hello } from "./plain37.mjs";
console.log(hello(1));
```

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

```ts
// rel37.d.ts
declare module "./rel37.mjs" {
    export const a: number;
}
```

- `useplain37.mts` 는 무엇으로 막히는가?
- `uselegacy37.mts` 를 혼자 · `ambient37.d.ts` 와 · `short37.d.ts` 와 던지면 각각?
- `rel37.d.ts` 를 혼자 `--noEmit` 하면 무슨 코드가 나고, 종료 코드는?

### 5. 컴파일러가 쓴 선언 파일 (예측)

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

- 7.0.2 가 쓴 `calc37.d.mts` 에 `secret`·`Up`·`double`·`pick`·`Counter` 는 각각 어떻게 적히는가? 옛 두 판과 견주면?

### 6. `skipLibCheck` 를 켜고 끄면 (예측)

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

- `usebroken37.mts` — `--skipLibCheck` 없이 · 있이 각각 무엇이 남는가? 탐침 `p1` 에는 진단이 나는가?
- `usedup37.ts` — 플래그 없이 `dup37a dup37b` 순서 · `--skipLibCheck` 로 같은 순서 · `--skipLibCheck` 로 **뒤바꾼** 순서 — 탐침의 타입은 각각?

### 7. 두 거짓말의 결말 (왜)

- 2번의 두 소비자는 둘 다 `exit 0` 인데, node 에서 하나는 **값을 찍고** 하나는 **아무것도 실행하지 못했다.** 무엇이 둘을 가르는가?

### 8. import 없이 보이는 이름 (왜)

- 3번의 `useglob37.ts` 는 import 한 줄 없이 `track` 을 썼다. 무엇 때문에 보였고, 무엇 때문에 node 에서 없었는가?

### 9. 진단을 없애는 두 방법 (경계)

- 4번의 줄임 선언(`short37.d.ts`)과 6번의 `--skipLibCheck` 는 둘 다 진단을 없앴다. **어느 쪽의 진단**을 없애는지, 그리고 소비자 쪽 검사가 남는지로 둘을 갈라 보라.

### 10. 선언 파일의 글자 (경계)

- 5번의 판 대조는 「뽑은 `.d.ts` 를 저장소에 두고 변경을 `diff` 로 본다」는 관행에 무엇을 말하는가? 「내용이 같다」와 「글자가 같다」를 갈라 답하라.

### 11. 33·34·26 과 잇기 (연결)

- 3번의 `ReferenceError` 는 33편 4절의 어느 결과와 같은 모양인가?
- 6번이 끈 진단 목록에 34편 4절의 어느 코드가 더해지는가?
- 5번의 `Up` 과 `double` 두 줄은 26편 0절의 「방출기는 계산하지 않는다」에 무엇을 더하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
