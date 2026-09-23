# ts/syntax/04 — `any`·`unknown`·`never`·`void` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·`.d.ts` 전문·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★ **설정이 결과를 바꾸는 주제다.** 이 판은 `strict` 가 **기본 `true`** 이고, `strictNullChecks` 를 끄면 격자가 통째로 달라진다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 막히는 칸은 **넷** — `never` 행의 셋과 `void ← unknown` 하나

**출력**

```ts
// ex.04a.ts
// 네 타입 × 네 타입 = 16칸. 한 줄에 네 칸씩 늘어놓는다
declare let a: any;
declare let u: unknown;
declare let n: never;
declare let v: void;

a = a; a = u; a = n; a = v;
u = a; u = u; u = n; u = v;
n = a; n = u; n = n; n = v;
v = a; v = u; v = n; v = v;
```

```text
===== tsc --pretty false --noEmit ex.04a.ts (tsc exit=1) =====
ex.04a.ts(9,1): error TS2322: Type 'any' is not assignable to type 'never'.
ex.04a.ts(9,8): error TS2322: Type 'unknown' is not assignable to type 'never'.
ex.04a.ts(9,22): error TS2322: Type 'void' is not assignable to type 'never'.
ex.04a.ts(10,8): error TS2322: Type 'unknown' is not assignable to type 'void'.
```

**왜 그런가**

| 대상 ↓ \| 원본 → | `any` | `unknown` | `never` | `void` |
|---|---|---|---|---|
| **`any`** | O | O | O | O |
| **`unknown`** | O | O | O | O |
| **`never`** | **X** | **X** | O | **X** |
| **`void`** | O | **X** | O | O |

- 진단은 **네 줄**이다 — 9행에서 셋, 10행에서 하나.
- ★★★ **`any` 조차 `never` 에는 못 들어간다.** 「`any` 는 아무 데나 된다」의 **유일한 예외**다.
- `never` 행이 거의 다 X 인 것은 **`never` 에는 담을 값이 없기 때문**이다. `n = n` 만 된다.
- `never` **열**이 전부 O 인 것은 **바닥 타입**이라 어디로든 나갈 수 있기 때문이다.
- `unknown` **행**이 전부 O 인 것은 **꼭대기 타입**이라 무엇이든 담기기 때문이다.
- `void ← unknown` 만 X 인 이유는 `void` 가 「`undefined` 정도가 온다」는 좁은 약속이기 때문이다 — `unknown` 은 그보다 넓다.
- ★ 종료 코드가 `1` 인 것은 `--noEmit` 을 줘서 **아무것도 안 나왔기** 때문이다([**02번 주제**](../02-type-checking-vs-emit/)).

### 2. ★★★ 진단 **4건** — `TS18046` 셋 + `TS2322` 하나 · `if` 블록 셋은 **전부 통과**

**출력**

```ts
// ex.04b.ts
// unknown 은 받아 놓고 좁히기 전에는 아무것도 못 하게 한다
declare const u: unknown;

u.length;
u();
u + 1;
const s: string = u;

if (typeof u === "string") {
    console.log(u.length);
}
if (typeof u === "object" && u !== null && "id" in u) {
    console.log(u.id);
}
if (Array.isArray(u)) {
    console.log(u.length);
}
```

```text
===== tsc --pretty false --noEmit ex.04b.ts (tsc exit=1) =====
ex.04b.ts(4,1): error TS18046: 'u' is of type 'unknown'.
ex.04b.ts(5,1): error TS18046: 'u' is of type 'unknown'.
ex.04b.ts(6,1): error TS18046: 'u' is of type 'unknown'.
ex.04b.ts(7,7): error TS2322: Type 'unknown' is not assignable to type 'string'.
```

**왜 그런가**

- 좁히기 전의 `u.length`·`u()`·`u + 1` 이 전부 **`TS18046` — 「'u' is of type 'unknown'.」** 이다.\
  ★ **프로퍼티 접근·호출·연산 셋이 같은 코드**로 막힌다.
- `const s: string = u` 는 **`TS2322`** — 대입은 할당 가능성 문제라 코드가 다르다.
- ★★ `if` 블록 **셋은 진단이 없다** — `typeof u === "string"` · `typeof u === "object" && u !== null && "id" in u` · `Array.isArray(u)` 세 가지 좁히기가 전부 먹혔다.
- ★ 즉 `unknown` 은 **못 쓰게 만드는 타입이 아니라 좁히기를 강제하는 타입**이다.

### 3. ★★★ 종료 코드 **0** — 진단이 **한 건도** 없다 · 같은 `c` 가 `string` 과 `number` **둘 다**에 들어간다

**출력**

```ts
// ex.04c.ts
// any 는 옆으로 번진다 — unknown 은 그 자리에서 멈춘다
declare const a: any;
export const b = a.foo.bar;
export const c = b + 1;
export const asString: string = c;
export const asNumber: number = c;

declare const u: unknown;
export const d = u;
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.04c.ts (tsc exit=0) =====
===== 방출된 ex.04c.d.ts =====
export declare const b: any;
export declare const c: any;
export declare const asString: string;
export declare const asNumber: number;
export declare const d: unknown;
```

**왜 그런가**

- `const b = a.foo.bar` 가 **`any`** 다. 없는 프로퍼티를 **두 번** 타고 들어갔는데 아무 말이 없다.
- `const c = b + 1` 도 **`any`** 다 — `any` 와의 연산 결과도 `any` 다.
- ★★★ 그래서 `.d.ts` 에 `asString: string` 과 `asNumber: number` 가 **동시에** 있다. **같은 값이 두 타입에 다 들어갔다.**
- 종료 코드 **0** — 이 파일에는 에러가 한 건도 없다. **검사가 아예 안 도는 것이나 마찬가지**다.
- 반면 `const d = u`(unknown)는 `.d.ts` 에 **`unknown`** 그대로다. 번지지 않는다.

같은 대입을 `unknown` 으로 하면 **한 줄에서 멈춘다**.

```ts
// ex.04d.ts
// unknown 으로 받으면 이 줄이 걸린다
declare const u: unknown;
const asString: string = u;
console.log(asString);
```

```text
===== tsc --pretty false --noEmit ex.04d.ts (tsc exit=1) =====
ex.04d.ts(3,7): error TS2322: Type 'unknown' is not assignable to type 'string'.
```

- ★★ 그래서 `any` 의 비용은 「**그 줄**」이 아니라 「**그 값이 흘러간 모든 줄**」이다.

### 4. ★★★ `arrow` 는 **`() => never`**, `declared` 는 **`void`** — **같은 몸통인데 갈린다**

**출력**

```ts
// ex.04e.ts
// never 가 생기는 네 자리를 한 파일에 모았다
export function fail(msg: string): never {
    throw new Error(msg);
}
export const arrow = () => {
    throw new Error("x");
};
export function declared() {
    throw new Error("x");
}
export type Both = { a: string } & { a: number };
export type Empty = Extract<"a" | "b", "c">;
export const emptyArr: never[] = [];

export function narrow(v: string | number) {
    if (typeof v === "string") return "문자열";
    if (typeof v === "number") return "숫자";
    return v;
}
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.04e.ts (tsc exit=0) =====
===== 방출된 ex.04e.d.ts =====
export declare function fail(msg: string): never;
export declare const arrow: () => never;
export declare function declared(): void;
export type Both = {
    a: string;
} & {
    a: number;
};
export type Empty = Extract<"a" | "b", "c">;
export declare const emptyArr: never[];
export declare function narrow(v: string | number): "문자열" | "숫자";
```

**왜 그런가**

- `export declare const arrow: () => never;` 와 `export declare function declared(): void;` 다.\
  ★★★ 몸통이 둘 다 `throw new Error("x")` **하나뿐인데 갈렸다.**
- 규칙은 **함수 선언은 `void` 로, 함수 표현식·화살표는 `never` 로** 추론하는 것이다.\
  함수 선언은 나중에 몸통이 바뀔 수 있는 「이름 붙은 API」로 다루기 때문이다.
- `fail` 은 **명시**해서 `never` 다.
- `emptyArr: never[]` — 빈 배열에 표기를 주면 원소 타입이 `never` 다.
- ★ `narrow` 의 반환은 **`"문자열" \| "숫자"`** 다. 마지막 `return v` 의 `v` 가 **`never`** 라 유니온에 아무것도 안 보탰다 — **`never` 는 유니온에서 사라진다.**
- `Both`·`Empty` 는 `.d.ts` 에 **적은 모양 그대로** 남는다. `never` 로 접히는 것은 **꺼내 쓸 때**다.

`never` 가 생기는 자리를 모으면 다섯이다.

```text
  ① 명시           function fail(msg: string): never
  ② 화살표/함수 표현식이 정상 종료하지 않음   const arrow = () => { throw … }
  ③ 빈 배열에 표기  const emptyArr: never[] = []
  ④ 교차가 모순     { a: string } & { a: number } 의 a
  ⑤ 좁히기가 다 소진 switch 를 전부 다룬 뒤의 default
```

### 5. ★★★ `area2` 만 진단 · 문구가 **빠뜨린 갈래의 이름**을 적어 준다

**출력**

```ts
// ex.04f.ts
// 판별 유니온의 완전성 검사 — 한 갈래를 더하면 어디가 깨지나
type Shape = { kind: "circle"; r: number } | { kind: "square"; s: number };
type Shape2 = Shape | { kind: "tri"; b: number; h: number };

function area(sh: Shape): number {
    switch (sh.kind) {
        case "circle":
            return 3 * sh.r * sh.r;
        case "square":
            return sh.s * sh.s;
        default: {
            const rest: never = sh;
            return rest;
        }
    }
}

function area2(sh: Shape2): number {
    switch (sh.kind) {
        case "circle":
            return 3 * sh.r * sh.r;
        case "square":
            return sh.s * sh.s;
        default: {
            const rest: never = sh;
            return rest;
        }
    }
}

console.log(area({ kind: "circle", r: 1 }), area2({ kind: "tri", b: 1, h: 2 }));
```

```text
===== tsc --pretty false --noEmit ex.04f.ts (tsc exit=1) =====
ex.04f.ts(25,19): error TS2322: Type '{ kind: "tri"; b: number; h: number; }' is not assignable to type 'never'.
```

**왜 그런가**

- `area`(두 갈래 전부 다룸)는 **진단이 없다.** `default` 에 도달했을 때 `sh` 가 이미 `never` 다.
- `area2`(세 갈래 중 둘만 다룸)는 `TS2322` 이고 문구가 **`{ kind: "tri"; b: number; h: number; }`** 를 그대로 적는다.\
  ★★ **무엇을 빠뜨렸는지 컴파일러가 이름을 말해 준다.** 이것이 이 관용구의 값이다.
- ★★★ `const rest: null = sh;` 로는 안 된다 — **`never` 는 `null` 에도 대입되므로** 다 다뤘을 때 에러가 안 나야 하는데,\
  `null` 탐침은 **다 다룬 경우에도** 에러를 낸다. 방향이 반대라 관용구가 성립하지 않는다.
- ★ 즉 **`never` 를 대상 자리에 두는 것**이 핵심이다. 「여기 도달하면 안 된다」는 주장을 **타입으로** 적은 것이다.

### 6. ★★★ 진단 **1건**(8행 `direct`) — `const cb: Cb = () => 42;` 는 **통과한다** · `node` 는 **`42`** 를 찍는다

**출력**

```ts
// ex.04g.ts
// void 가 반환 위치에서만 느슨해지는 자리
type Cb = () => void;

const cb: Cb = () => 42;
const got = cb();

function direct(): void {
    return 42;
}

const names: string[] = [];
const ids = [1, 2, 3];
ids.forEach((n) => names.push(String(n)));

console.log("cb() 의 정적 타입은 void, 실제 값은:", got);
console.log("names:", names, "| direct:", typeof direct);
```

```text
===== tsc --pretty false --noEmit ex.04g.ts (tsc exit=1) =====
ex.04g.ts(8,5): error TS2322: Type 'number' is not assignable to type 'void'.
```

```text
===== tsc --pretty false ex.04g.ts (tsc exit=2) =====
ex.04g.ts(8,5): error TS2322: Type 'number' is not assignable to type 'void'.
===== 방출된 ex.04g.js =====
"use strict";
const cb = () => 42;
const got = cb();
function direct() {
    return 42;
}
const names = [];
const ids = [1, 2, 3];
ids.forEach((n) => names.push(String(n)));
console.log("cb() 의 정적 타입은 void, 실제 값은:", got);
console.log("names:", names, "| direct:", typeof direct);
```

```text
===== node ex.04g.js (node exit=0) =====
cb() 의 정적 타입은 void, 실제 값은: 42
names: [ '1', '2', '3' ] | direct: function
```

**왜 그런가**

- ★★★ `const cb: Cb = () => 42;` 가 **통과했다.** `Cb = () => void` 인데 숫자를 돌려주는 함수가 들어갔다.
- ★★★ `function direct(): void { return 42; }` 는 **`TS2322`** 다 — **반환 타입을 직접 적은 자리**에서는 막힌다.
- 두 줄의 차이는 「**`void` 반환 함수 타입에 대입**」 대 「**반환 타입을 `void` 로 선언**」이다.\
  앞은 「**돌려주든 말든 안 본다**」는 약속이고, 뒤는 「**돌려줄 것이 없다**」는 선언이다.
- `ids.forEach((n) => names.push(String(n)))` 도 같은 규칙으로 통과한다 — `push` 는 **길이(숫자)를 돌려준다.**
- ★★ 실행 출력이 결정적이다 — `cb() 의 정적 타입은 void, 실제 값은: 42`.\
  **값이 없어지는 게 아니라 타입이 안 보겠다고 하는 것**이다.
- 방출된 파일에는 `void` 라는 글자가 없다 — `const cb = () => 42;` 그대로다.

### 7. ★★ 흔적이 **하나도 없다** — `typeof` 로 구별할 수 없다

**출력**

```ts
// ex.04h.ts
// 네 타입은 전부 타입일 뿐이다 — 방출된 JS 에 무엇이 남나
function fail(msg: string): never {
    throw new Error(msg);
}
function ping(): void {
    console.log("ping");
}
function take(u: unknown, a: any) {
    return [typeof u, typeof a];
}

ping();
console.log(take("x", 1));
try {
    fail("끝");
} catch (e) {
    console.log("잡았다:", (e as Error).message);
}
```

```text
===== tsc --pretty false ex.04h.ts (tsc exit=0) =====
===== 방출된 ex.04h.js =====
"use strict";
// 네 타입은 전부 타입일 뿐이다 — 방출된 JS 에 무엇이 남나
function fail(msg) {
    throw new Error(msg);
}
function ping() {
    console.log("ping");
}
function take(u, a) {
    return [typeof u, typeof a];
}
ping();
console.log(take("x", 1));
try {
    fail("끝");
}
catch (e) {
    console.log("잡았다:", e.message);
}
```

```text
===== node ex.04h.js (node exit=0) =====
ping
[ 'string', 'number' ]
잡았다: 끝
```

**왜 그런가**

- `: never`·`: void`·`u: unknown`·`a: any` 표기가 **전부 사라졌다.** `(e as Error)` 의 `as` 도 사라져 `e.message` 가 됐다.
- 동작은 그대로다 — `fail` 은 여전히 던지고, `ping` 은 여전히 찍는다. 실행이 `ping` / `[ 'string', 'number' ]` / `잡았다: 끝` 셋을 찍는다.
- ★ `typeof` 가 돌려주는 것은 **런타임 값의 종류**(`"string"`·`"number"`)다. 네 타입은 **컴파일 시각의 개념**이라 거기 안 나온다.
- ★★ 그래서 「`unknown` 인지 검사한다」 같은 말은 성립하지 않는다 — [**01번 주제**](../01-what-ts-adds-and-erases/)의 결론 그대로다.

### 8. ★★★ `any` 는 **검사를 끄고** `unknown` 은 **검사를 미룬다**

**왜 그런가**

- 근거는 3번의 `.d.ts` 다 — `any` 에서 출발한 `c` 가 **`asString: string` 과 `asNumber: number` 둘 다**에 들어갔고, 그 파일의 **종료 코드가 0** 이었다.
- 같은 자리를 `unknown` 으로 바꾸면 **대입 한 줄에서** `TS2322` 가 난다.
- ★ 즉 `unknown` 은 **「지금은 모른다」를 타입으로 적는 것**이고, `any` 는 「**묻지 마라**」다.
- ★★ 실무 규칙 한 줄 — **경계에서는 `unknown` 으로 받고, 좁힌 뒤에 구체 타입으로 넘긴다.**\
  `any` 를 쓴다면 **그 한 줄에서 끝내고 즉시 좁힌다.**

### 9. ★★ **한 방향**이다 — `undefined` → `void` 만 된다

**출력**

```ts
// ex.04i.ts
// void 와 undefined 는 서로 오가나 — 양방향으로 던져 본다
declare let v: void;
declare let u: undefined;
declare let a: any;
declare let n: never;

v = u;
u = v;

function ret(): void {}
const got: undefined = ret();

type Cb = () => void;
const cb: Cb = () => 42;
const r: undefined = cb();

declare const arr: number[];
const mapped: void[] = arr.map((x) => {
    console.log(x);
});
console.log(v, u, a, n, got, r, mapped);
```

```text
===== tsc --pretty false --noEmit ex.04i.ts (tsc exit=1) =====
ex.04i.ts(8,1): error TS2322: Type 'void' is not assignable to type 'undefined'.
ex.04i.ts(11,7): error TS2322: Type 'void' is not assignable to type 'undefined'.
ex.04i.ts(15,7): error TS2322: Type 'void' is not assignable to type 'undefined'.
```

**왜 그런가**

- `v = u`(undefined → void)는 **통과**했고 `u = v`(void → undefined)는 **`TS2322`** 다.
- 그래서 `const got: undefined = ret();` 도 막힌다(11행). `ret()` 의 타입은 `void` 이지 `undefined` 가 아니다.
- `const r: undefined = cb();` 도 같은 이유로 막힌다(15행).
- ★ **`void` 는 「`undefined` 가 온다」는 약속이 아니다.** 「**무엇이 오든 안 본다**」는 약속이다 — 6번의 `cb()` 가 실제로 `42` 였다.
- ★ `arr.map((x) => { … })` 의 결과가 `void[]` 로 통과한 것도 같은 이유다 — 콜백이 아무것도 안 돌려줘도 `void` 다.

### 10. ★★ 안 된다 — **방향을 뒤집어** `const x: never = v` 로 묻는다

**왜 그런가**

- [**03번 주제**](../03-basic-type-annotations/)의 탐침은 `const probe: null = 값;` 이었다. 진단 문구가 그 값의 타입을 말해 주는 방식이다.
- ★ 그런데 **`never` 는 `null` 에 대입된다**(1번 격자의 `never` 열이 전부 O). 그래서 **에러가 안 나고 문구도 안 나온다.**
- 같은 이유로 `any` 도 안 잡힌다 — `any` 는 `null` 에 들어간다.
- 그래서 `never` 는 **대상 자리**에 둔다 — `const x: never = v;`. 그러면 `v` 가 `never` 가 아닐 때 그 타입 이름을 문구에 적어 준다(5번이 그 형태다).
- ★ 정리하면 **탐침은 두 방향으로 쓴다** — 「이게 무슨 타입이지」는 `: null`, 「여기 도달하면 안 되는데」는 `: never`.

### 11. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 16칸 격자의 O/X 배치 · `unknown` 은 좁히기 전 아무 연산도 허용 안 함(`TS18046`) · `any` 의 프로퍼티·연산 결과는 `any` · `void` 반환 함수 타입은 **반환값을 무시**한다 · `never` 대입으로 완전성 검사 |
| **설정에 달린 것** | `null`·`undefined` 가 **따로 있는 것**(`strictNullChecks`) · `catch (e)` 의 `e` 가 `unknown` 인 것(`useUnknownInCatchVariables`, 4.4+) — 이 판은 `strict` 기본 `true` |
| **이 판(7.0.2)의 관찰** | `arrow` 는 `() => never`, `declared` 는 `void` 로 **갈리는 것** · 진단 문구의 정확한 글자 · `Symbol`·`Extract` 같은 것이 `.d.ts` 에 **적은 모양 그대로** 남는 것 |

- ★ **`strictNullChecks` 를 끄면 격자가 통째로 달라진다.** 그래서 모든 블록의 배너에 옵션을 적었다.

### 12. ★★ 세 자리의 선택

| 자리 | 고르는 것 | 왜 |
|---|---|---|
| 경계에서 들어오는 값(`JSON.parse`·`fetch`·`catch`) | ★ **`unknown`** | 좁히기를 **강제**한다. `any` 로 받으면 그 의무가 호출자에게서 사라진다 |
| 완전성 검사(`switch` 의 `default`) | ★ **`never`** | 빠뜨린 갈래의 **이름을 진단이 적어 준다** |
| 반환값을 안 쓰는 콜백 타입 | ★ **`void`** | 「돌려주든 말든 안 본다」 — `forEach(x => arr.push(x))` 같은 코드가 돈다 |
| (안 고르는 것) | `any` | 그 값이 흘러간 **모든 줄**이 검사 밖으로 나간다 |

- ★ 한 줄 요약 — **`unknown` 으로 받고, `never` 로 막고, `void` 로 무시하고, `any` 는 쓰지 않는다.**

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 16칸 격자 | `--noEmit ex.04a.ts` | exit 1 · `TS2322` **4건**(9행 3 · 10행 1) |
| `unknown` 좁히기 | `--noEmit ex.04b.ts` | exit 1 · `TS18046` 3건 + `TS2322` 1건 · **`if` 셋은 통과** |
| `any` 전염 | `--declaration --emitDeclarationOnly ex.04c.ts` | **exit 0** · `b`·`c` 가 `any` · `string` 과 `number` 둘 다 통과 |
| `unknown` 차단 | `--noEmit ex.04d.ts` | exit 1 · `TS2322` 1건 |
| `never` 추론 | `--declaration --emitDeclarationOnly ex.04e.ts` | exit 0 · `arrow: () => never` 대 `declared(): void` |
| 완전성 검사 | `--noEmit ex.04f.ts` | exit 1 · `TS2322` **1건**(`area2` 만) · 문구에 빠뜨린 갈래 |
| `void` 콜백 | `--noEmit ex.04g.ts` · `tsc ex.04g.ts` + `node` | exit 1 / exit 2 · `TS2322` **1건**(`direct` 만) · 실행 `… 실제 값은: 42` |
| `void` 대 `undefined` | `--noEmit ex.04i.ts` | exit 1 · `TS2322` **3건** — 전부 `void` → `undefined` 방향 |
| 방출 | `tsc ex.04h.ts` + `node ex.04h.js` | exit 0 · 표기 전부 사라짐 · 실행 3줄 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- `arrow` 와 `declared` 가 갈리는 추론 규칙 — 결론은 안정적이지만 **직접 던져** 확인했다.
- 진단 문구의 정확한 글자 — 코드(`TS18046`·`TS2322`)가 더 오래 간다.
- `strict` 기본값이 `true` 라는 것 — **7.0 에서 바뀐 것**이다. 6.x 이하에서 재현하려면 `--strict` 를 명시해야 한다.
- `.d.ts` 가 `Extract<"a" \| "b", "c">` 를 **접지 않고 그대로** 적는 것 — 선언 방출기의 구현이다.

**안 돌려 본 것**

- `--strictNullChecks false` 로 던진 16칸 격자 — 이 주제의 결론이 「`strict` 가 켜진 판의 격자」이므로 그 한 가지만 실었다. 끈 판의 격자는 목록의 **40번 주제**에서 던진다. **그래서 이 문서의 어느 줄에도 「끄면 이렇게 된다」를 단정하지 않았다.**
