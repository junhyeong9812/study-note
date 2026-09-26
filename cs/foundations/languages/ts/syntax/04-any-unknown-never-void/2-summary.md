# ts/syntax/04 — `any`·`unknown`·`never`·`void` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Everyday Types: `any`](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any) ·
> [Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) ·
> [Handbook — More on Functions: Return type `void`](https://www.typescriptlang.org/docs/handbook/2/functions.html#return-type-void) ·
> [TSConfig — `strict`](https://www.typescriptlang.org/tsconfig/#strict).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·`.d.ts` 전문은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ **`tsc` 가 7.0.2 다 — 5.x 가 아니다.** 이 주제의 결과를 좌우하는 기본값은 **`strict` 가 켜져 있다**는 것이다(7.0 기본 `true`).
> `strictNullChecks` 가 꺼지면 이 문서의 격자가 통째로 달라진다 — **설정 없이 실린 결과는 재현이 안 된다.**
> **버전** — `any`·`void`·`never` 는 TS 1.x\~2.0, **`unknown` 은 3.0**, `useUnknownInCatchVariables` 는 4.4 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·`.d.ts` 전문·방출 전문 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | `node` 출력 | 난수·시각을 안 썼다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ **소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다** — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 한눈에 — 쉽게 말하면

**네 타입은 「값의 종류」가 아니라 「문을 어느 방향으로 여는가」다.**

| 비유 | 실체 |
|---|---|
| 양쪽으로 다 열린 문 — 아무나 들고 나간다 | **`any`** — 넣을 수도 있고 어디에나 꺼내 쓸 수도 있다. **검사를 끈다** |
| 들어오는 문만 열린 상자 — 꺼내려면 확인해야 한다 | **`unknown`** — 아무거나 넣을 수 있지만 **좁히기 전엔 못 쓴다** |
| 문이 아예 없는 방 | **`never`** — 어떤 값도 못 들어간다. 대신 **어디로든 나갈 수는 있다** |
| 「돌려줄 게 없다」는 반환 표시 | **`void`** — 반환 자리 전용. ★ **반환 자리에서만 느슨해진다** |
| ★ 「가져온 물건은 안 볼 테니 알아서 버려라」 | `() => void` 에 **값을 돌려주는 함수를 넣을 수 있다** |

- ★★★ 한 줄로 — **「`any` 는 검사를 끄고, `unknown` 은 검사를 미루고, `never` 는 도달 불가를 말하고, `void` 는 반환값을 무시한다.」**
- ★★ 그래서 이 주제의 창은 **16칸 할당 격자**다. 「어느 방향으로 되나」를 **전부 컴파일해서** 채운다.

```text
  넷을 「넓이」로 세우면
                       any
                  (검사를 끈 자리)
                        │
      unknown  ────────────────────  모든 타입의 꼭대기
         │                            아무거나 담기지만 꺼내 쓰려면 좁혀야 한다
         │
    string · number · … · void
         │
       never  ────────────────────  바닥. 어떤 값도 없다
                                     그래서 **어디로든** 대입된다

  ★ any 는 이 그림 밖에 있다 — 위아래 양쪽으로 다 통한다.
```

```text
  16칸 격자 — 「대상 = 원본」이 되나
             원본 →   any    unknown   never    void
  대상 ↓
  any                  O        O        O       O
  unknown              O        O        O       O
  never                X        X        O       X
  void                 O        X        O       O

  ★ 유일하게 X 가 섞인 두 행이 never 와 void 다.
  ★ any 조차 never 에는 못 들어간다.
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **네 타입이 할당 방향에서 어떻게 다른가** — 16칸을 **외워서가 아니라 던져서** 채울 수 있나.
2. **`unknown` 으로 받으면 무엇이 강제되나** — `any` 와 무엇이 달라지나.
3. **`never` 는 어디서 생기고, `void` 는 왜 반환 자리에서만 느슨한가.**

★ [**03번 주제**](../03-basic-type-annotations/)가 표기의 토대라면, 여기는 **그 표기 체계의 위아래 끝**이다. [**05번 주제**](../05-structural-typing/)가 그 사이의 **할당 규칙**을 다룬다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **16칸 격자** | 「되나 안 되나」를 **전수로** 채운다 | ★ 이 주제의 고유 창 |
| ★★ **`.d.ts` 덤프** | `never` 가 **어디서 생기는지** 글자로 | [**03번 주제**](../03-basic-type-annotations/)에서 이어받음 |
| **진단 전문** | 어느 칸이 왜 막혔는지 | 모든 주제 공통 |
| **방출된 `.js` + `node`** | 네 타입이 **런타임에 아무것도 아닌 것** | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |

★ **전수로 던지는 것이 이 주제의 값이다.** 「`any` 는 아무 데나 들어간다」 같은 어림짐작이 **`never` 한 칸에서 깨진다.**

비용 — 컴파일 한 번. 16칸이 진단 네 줄로 요약된다.

### (1) ★★★ 16칸 할당 격자

**언제 쓰나** — 「이 값을 저기에 넣어도 되나」가 막힐 때. **전부 한 파일에 적어 던진다.**

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 줄**이다. 16칸 중 **12칸이 통과**했다는 뜻이다.
- 9행(`n = …`)에서 **셋**이 걸렸다 — `any`·`unknown`·`void` 가 `never` 에 못 들어간다.
- ★★★ **`any` 조차 `never` 에는 못 들어간다.** 「`any` 는 아무 데나 된다」의 **유일한 예외**가 이 칸이다.
- 10행(`v = …`)에서 **하나** 걸렸다 — `unknown` 만 `void` 에 못 들어간다.
- 그래서 `n = n` 과 `v = a`·`v = n`·`v = v` 는 통과했다.

| 대상 ↓ \| 원본 → | `any` | `unknown` | `never` | `void` |
|---|---|---|---|---|
| **`any`** | O | O | O | O |
| **`unknown`** | O | O | O | O |
| **`never`** | **X** TS2322 | **X** TS2322 | O | **X** TS2322 |
| **`void`** | O | **X** TS2322 | O | O |

- ★ 읽는 법 — **`unknown` 행이 전부 O 인 것**이 「모든 타입의 꼭대기」라는 뜻이고,\
  **`never` 열이 전부 O 인 것**이 「바닥이라 어디로든 나간다」는 뜻이다.

비용 — 없음. 전부 검사 시각이다.

### (2) ★★★ `unknown` 으로 받으면 무엇이 강제되나

**언제 쓰나** — 경계 밖에서 온 값(`JSON.parse`·`fetch`·`catch`)을 받을 때.

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

그림 해설 — 한 단계에 한 문장.

- 좁히기 **전**의 세 줄(`u.length`·`u()`·`u + 1`)이 전부 **`TS18046` — 「'u' is of type 'unknown'.」** 이다.
- `const s: string = u` 는 **`TS2322`** — 대입도 막힌다.
- ★★ 그런데 **`if` 로 좁힌 뒤의 세 블록은 진단이 없다** — `typeof u === "string"` 안에서 `u.length` 가 통과했고,\
  `typeof u === "object" && u !== null && "id" in u` 안에서 `u.id` 가 통과했고, `Array.isArray(u)` 안에서 `u.length` 가 통과했다.
- ★ 즉 `unknown` 은 **못 쓰게 만드는 타입이 아니라 좁히기를 강제하는 타입**이다.

```text
  any 로 받으면                        unknown 으로 받으면
  +---------------------------+        +---------------------------+
  | const x: any = 들어온 값  |        | const u: unknown = 들어온 값|
  | x.length     -> 통과      |        | u.length     -> TS18046   |
  | x()          -> 통과      |        | u()          -> TS18046   |
  | x + 1        -> 통과      |        | u + 1        -> TS18046   |
  +---------------------------+        +---------------------------+
    실행에서 터진다                       if (typeof u === "string") {
                                            u.length  -> 통과
                                          }
```

> **좁히기(narrowing)** — 제어 흐름을 보고 그 분기 안에서 타입을 더 구체적으로 읽어 주는 것.\
> 예: `if (typeof u === "string")` 안에서 `u` 는 `string` 으로 읽힌다. 전면 서술은 [목록의 **12번 주제**](../12-narrowing/).

비용 — 검사만 는다. 런타임 비용은 **가드를 실제로 쓸 때만** 생긴다.

### (3) ★★★ `any` 는 번지고 `unknown` 은 멈춘다

**언제 쓰나** — 「`any` 하나쯤이야」를 의심할 때.

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

그림 해설 — 한 단계에 한 문장.

- `const b = a.foo.bar` 가 **`any`** 다 — `any` 의 프로퍼티는 `any` 다. 없는 프로퍼티를 두 번 타고 들어갔는데도 진단이 없다.
- `const c = b + 1` 도 **`any`** 다 — `any` 와의 연산 결과도 `any` 다.
- ★★★ 그래서 **같은 `c` 가 `string` 에도 `number` 에도 들어간다.** `.d.ts` 의 `asString: string` 과 `asNumber: number` 가 동시에 있다.
- 종료 코드가 **0** 이다 — **진단이 한 건도 없다.**
- 반면 `const d = u`(unknown)는 `.d.ts` 에 **`unknown`** 그대로다. 번지지 않는다.

같은 대입을 `unknown` 으로 하면 그 줄에서 멈춘다.

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

- ★ 한 줄짜리 파일인데 **에러가 난다.** `unknown` 은 **대입 한 번에서** 걸린다.
- ★★ 즉 `any` 의 비용은 「그 줄」이 아니라 **그 값이 흘러간 모든 줄**이다.

비용 — `any` 를 쓰면 **그 아래 전부**가 검사 밖으로 나간다. 그것이 이 절의 결론이다.

### (4) ★★ `never` 가 생기는 자리

**언제 쓰나** — 「이 함수 반환이 왜 `never` 지?」·「왜 이 타입이 `never` 가 됐지?」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- `function fail(msg: string): never` — **명시한 자리.** 정상 반환이 없는 함수다.
- ★★★ `const arrow = () => { throw … }` 는 **`() => never`** 로 추론됐다.\
  그런데 `function declared() { throw … }` 는 **`void`** 다 — **같은 몸통인데 갈린다.**\
  함수 **선언**은 `void` 로, 함수 **표현식·화살표**는 `never` 로 추론하는 규칙이다.
- `type Both = { a: string } & { a: number }` 는 `.d.ts` 에 **교차 그대로** 남는다 — 하지만 `Both["a"]` 를 꺼내면 `string & number` 라 값이 없다.
- `type Empty = Extract<"a" | "b", "c">` 도 그대로 남는다 — 실제로 꺼내면 `never` 다.
- `const emptyArr: never[] = []` — 빈 배열에 표기를 주면 `never[]` 가 된다([**03번 주제**](../03-basic-type-annotations/)의 `export const exported = []` 와 같은 자리다).
- `function narrow(v: string \| number)` 의 반환이 **`"문자열" \| "숫자"`** 다 — 마지막 `return v` 의 `v` 는 **`never`** 라 유니온에 아무것도 안 보탰다.

비용 — 없음. `never` 는 값이 없다는 **사실의 이름**이다.

### (5) ★★★ 완전성 검사 — 갈래를 더하면 어디가 깨지나

**언제 쓰나** — 판별 유니온에 갈래를 추가했을 때 **고칠 곳을 컴파일러가 알려 주게** 하고 싶을 때.

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

그림 해설 — 한 단계에 한 문장.

- `area`(두 갈래를 다 다룬 쪽)는 **진단이 없다.** `default` 에 도달했을 때 `sh` 가 이미 `never` 이기 때문이다.
- `area2`(세 갈래인데 둘만 다룬 쪽)는 **`TS2322`** 다 — 문구가 **빠뜨린 갈래를 그대로 적어 준다**.\
  「Type '{ kind: "tri"; b: number; h: number; }' is not assignable to type 'never'.」
- ★★★ 즉 `const rest: never = sh;` 한 줄이 **「여기 도달하면 안 된다」는 주장을 컴파일러가 검사하게** 만든다.
- ★ 이것이 [**03번 주제**](../03-basic-type-annotations/)의 `null` 탐침이 **못 하는 일**이다 — `never` 는 `null` 에도 들어가므로 그쪽으로는 안 잡힌다. **방향을 뒤집어야** 한다.

```text
  switch (sh.kind) {
    case "circle": …        ← 여기서 circle 이 빠진다
    case "square": …        ← 여기서 square 가 빠진다
    default:
      const rest: never = sh;
                       ↑
        남은 것이 없으면 never  -> 통과
        남은 것이 있으면 그 타입 -> TS2322 로 이름을 말해 준다
  }
```

비용 — 한 줄. 갈래가 늘 때마다 **컴파일이 깨져서** 고칠 곳을 알려 준다.

### (6) ★★★ `void` 는 반환 자리에서만 느슨하다

**언제 쓰나** — 「`() => void` 인데 왜 값을 돌려주는 함수가 들어가지?」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ `const cb: Cb = () => 42;` 는 **통과했다.** `Cb = () => void` 인데 숫자를 돌려주는 함수가 들어갔다.
- ★★★ 그런데 `function direct(): void { return 42; }` 는 **`TS2322`** 다. **직접 선언한 자리에서는 안 된다.**
- ★ 두 줄의 차이는 「**반환 타입을 직접 적었나**」 대 「**`void` 반환 함수 타입에 대입했나**」다.
- `ids.forEach((n) => names.push(String(n)))` 도 같은 규칙으로 통과한다 — `push` 는 **숫자를 돌려주는데** `forEach` 의 콜백은 `void` 를 받는다.

방출과 실행을 보면 그 이유가 보인다.

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

- ★★ `cb()` 의 **정적 타입은 `void` 인데 실제 값은 `42`** 다. 「없다」가 아니라 「**보지 않겠다**」는 뜻이다.
- 방출된 파일에는 `void` 라는 글자가 없다 — `const cb = () => 42;` 그대로다.

`void` 와 `undefined` 는 **한 방향으로만** 오간다.

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

- `v = u`(undefined → void)는 **통과**하고 `u = v`(void → undefined)는 **`TS2322`** 다.
- ★ 그래서 `const got: undefined = ret();` 도 막힌다 — `void` 는 「`undefined` 가 온다」는 약속이 **아니다**.

비용 — 없음. 오히려 이 느슨함 덕분에 `forEach(arr.push…)` 같은 코드가 돈다.

### (7) ★ 방출에는 무엇이 남나

**언제 쓰나** — 네 타입이 런타임에 **아무것도 아니라는 것**을 확인할 때.

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

그림 해설 — 한 단계에 한 문장.

- `: never`·`: void`·`u: unknown`·`a: any` 표기가 **전부 사라졌다**.
- `fail` 은 여전히 `throw` 하고, `ping` 은 여전히 `console.log` 한다 — **동작은 그대로**다.
- `(e as Error).message` 의 `as` 도 사라져 `e.message` 가 됐다.
- ★ 즉 네 타입은 **런타임 개념이 아니다.** `typeof` 로 구별할 수 있는 것이 아니다.

비용 — 없음.

## 문법 — 형태와 규칙

```text
형태 — 네 타입이 오는 자리
  let x: any;                  아무 자리
  let u: unknown;              아무 자리
  function f(): void {}        ★ 주로 반환 자리
  function g(): never {}       ★ 반환 자리 (정상 종료가 없는 함수)
  const xs: never[] = [];      빈 배열의 원소 타입
  const rest: never = sh;      ★ 완전성 검사의 관용구
  catch (e) { }                ★ strict 아래에서 e 는 unknown (4.4+)
```

**규칙 불릿**

- ★★★ **`any` 는 위아래 양방향으로 다 통한다** — 단 **`never` 로는 못 간다**(격자의 유일한 예외).
- ★★ **`unknown` 은 모든 타입의 꼭대기**다 — 아무거나 담기지만, 꺼내 쓰려면 **좁혀야** 한다.
- ★★ **`never` 는 바닥**이다 — 어떤 값도 없으므로 **어디로든** 대입된다. 반대로 **아무것도 `never` 에 못 들어간다**.
- ★★ **`void` 는 반환 자리 전용**으로 읽는다. 변수 타입으로 쓰면 `undefined` 만 넣을 수 있는 이상한 타입이 된다.
- ★★★ **`void` 반환 함수 타입에는 값을 돌려주는 함수가 들어간다.** 단 **반환 타입을 직접 `void` 로 적은 함수 몸통에서는 `return 값` 이 막힌다.**
- ★ **`undefined` → `void` 는 되고 `void` → `undefined` 는 안 된다.**
- ★ `never` 추론은 **함수 선언과 함수 표현식에서 갈린다** — 선언은 `void`, 표현식·화살표는 `never`.

**금지 사례** — 이 주제에서 던져 받은 것 다섯이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) any·unknown·void 를 never 에 대입   ->  TS2322  Type 'any' is not assignable to type 'never'.
2) unknown 을 void 에 대입             ->  TS2322  Type 'unknown' is not assignable to type 'void'.
3) 좁히기 전에 unknown 을 사용          ->  TS18046 'u' is of type 'unknown'.
4) void 반환 함수 몸통에서 return 값    ->  TS2322  Type 'number' is not assignable to type 'void'.
5) 완전성 검사에서 남은 갈래           ->  TS2322  Type '{ kind: "tri"; … }' is not assignable to type 'never'.
```

## 어디서 틀리나

- ★★★ **「`any` 는 아무 데나 들어간다」** — `never` 한 칸이 예외다(`TS2322`). 격자를 던져 보면 바로 보인다.
- ★★★ **「`() => void` 니까 값을 안 돌려줘야지」** — 아니다. **돌려줘도 된다.** 다만 **그 값을 읽으면 정적 타입이 `void`** 다.
- ★★★ **「`any` 한 줄쯤이야」** — 그 값이 흘러간 **모든 줄**이 검사 밖으로 나간다. `.d.ts` 의 `asString: string` 과 `asNumber: number` 가 동시에 성립하는 것이 그 증거다.
- ★★ **「`unknown` 은 못 쓰는 타입」** — 아니다. **좁히면 쓸 수 있다.** 좁히기를 **강제**하는 것이 목적이다.
- ★★ **「`void` 는 `undefined` 의 다른 이름」** — 아니다. **한 방향으로만** 오간다(`undefined` → `void` 만).
- ★★ **「`throw` 만 있는 함수는 `never` 로 추론되겠지」** — **함수 선언은 `void`** 다. 화살표·함수 표현식만 `never` 다.
- ★ **「`never` 를 `null` 탐침으로 확인하자」** — 안 잡힌다. `never` 는 `null` 에도 들어간다. **`const x: never = v` 로 뒤집어** 묻는다.
- ★ **「`catch (e)` 의 `e` 는 `any`」** — `strict` 아래에서는 **`unknown`** 이다(4.4+, 이 판은 `strict` 기본 `true`).
- ★ **「`never[]` 는 쓸모없다」** — 빈 배열의 올바른 타입이다. 문제는 **거기에 `push` 하려 할 때**다([**03번 주제**](../03-basic-type-annotations/)).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 16칸 격자의 **O/X 배치** | 핸드북의 할당 가능성 규칙. 이 판의 진단 네 줄이 그 결과다 |
| **언어 보장** | `unknown` 은 **좁히기 전에 아무 연산도 허용하지 않는다** | `TS18046` 세 건 |
| **언어 보장** | `any` 의 프로퍼티·연산 결과는 `any` 다 | `.d.ts` 의 `b: any`·`c: any` |
| **언어 보장** | `void` 반환 함수 타입은 **반환값을 무시한다** | 핸드북의 「Return type void」 절. `const cb: Cb = () => 42` 가 통과 |
| **언어 보장** | `never` 대입으로 **완전성**을 검사할 수 있다 | `TS2322` 가 빠뜨린 갈래의 이름을 적는다 |
| **설정에 달림** | `null`·`undefined` 가 따로 있는 것, `catch` 변수가 `unknown` 인 것 | `strictNullChecks`·`useUnknownInCatchVariables`. 이 판은 `strict` 기본 `true` |
| **이 판(7.0.2)의 관찰** | `arrow` 가 `() => never`, `declared` 가 `void` 로 갈리는 것 | 추론 규칙의 구현이다. 결론(갈린다)은 안정적이지만 **직접 던져 확인**했다 |
| **이 판의 관찰** | 진단 문구의 정확한 글자 | 코드(`TS18046`·`TS2322`)가 더 오래 간다 |
| **런타임** | 네 타입 **전부** 방출에 안 남는다 | `ex.04h.js` 전문 |

★ **`strictNullChecks` 를 끄면 이 문서의 격자가 통째로 달라진다.** 그래서 모든 블록의 배너에 옵션을 적었다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| ★ **`unknown`** — 경계에서 들어오는 모든 값(`JSON.parse`·`fetch`·`catch`) | ★ **`any`** — 「일단 통과시키자」로 쓰면 그 아래 전부가 검사 밖으로 나간다 |
| **`never`** — 완전성 검사 · 「정상 종료가 없다」를 계약으로 적을 때 | `never` 를 변수 타입으로 — 값을 넣을 수 없어 쓸 데가 없다 |
| **`void`** — 반환값을 안 쓰는 콜백 타입 | `void` 를 변수 타입으로 — `undefined` 만 담기는 이상한 타입이 된다 |
| `any` 를 **경계 한 줄에만** 쓰고 즉시 좁히기 | `any` 를 공용 API 의 매개변수·반환에 — **호출자 전부**로 번진다 |

## 핵심 문장

1. **네 타입은 값의 종류가 아니라 「문이 어느 방향으로 열리는가」다** — 16칸 격자가 그 전부다.
2. **`any` 조차 `never` 에는 못 들어간다** — 격자의 유일한 예외이자 「`any` 는 아무 데나」의 반례.
3. **`any` 는 번지고 `unknown` 은 멈춘다** — `any` 의 비용은 그 줄이 아니라 그 값이 흘러간 모든 줄이다.
4. **`unknown` 은 못 쓰게 만드는 타입이 아니라 좁히기를 강제하는 타입이다.**
5. **`never` 대입 한 줄이 완전성 검사를 만든다** — 갈래가 늘면 컴파일이 깨지고 빠뜨린 이름을 알려 준다.
6. **`void` 반환 함수 타입에는 값을 돌려주는 함수가 들어간다** — 「없다」가 아니라 「보지 않겠다」다.
7. **네 타입 전부 방출에 안 남는다** — 런타임에는 존재하지 않는다.

## 관련 자료

- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) — 원시·배열·튜플·객체·함수 표기는 그쪽이 정본. 여기서는 **위아래 끝의 네 타입**만.
- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — 「왜 이 값이 이 자리에 들어가나」의 **일반 규칙**은 그쪽.
- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 「방출에 안 남는다」의 근거는 그쪽.
- [목록의 **09번 주제**](../09-union-types/)(유니온 타입) · **12번 주제**(좁히기) — 판별 유니온과 좁히기의 전면 서술은 그쪽. 여기서는 **완전성 검사 관용구**만.
- [목록의 **13번 주제**](../13-type-guards-and-predicates/)(타입 가드와 타입 술어) — `v is T` 의 전면 서술은 그쪽.
- 목록의 **42번 주제**(암시적 `any` 와 catch 변수) — `noImplicitAny`·`useUnknownInCatchVariables` 는 그쪽.
- `../../js/syntax/README.md` 의 **01번 주제**(값의 종류와 `typeof`) — `undefined` 의 **런타임 의미는 JS 갈래가 정본**이다.

## 용어 풀이

> **할당 가능성(assignability)** — 「이 타입의 값을 저 타입의 자리에 넣어도 되나」의 판정.\
> 예: `let s: string = 1;` 이 막히는 것이 이 판정이다. 이 주제의 16칸이 전부 이것이다.

> **꼭대기 타입(top type)** — 모든 값을 담을 수 있는 타입.\
> 예: `unknown` 에는 무엇이든 대입된다. 대신 꺼내 쓰려면 좁혀야 한다.

> **바닥 타입(bottom type)** — 값이 하나도 없는 타입.\
> 예: `never`. 값이 없으므로 **어느 자리에든** 대입될 수 있다(넣을 값이 애초에 없으니 모순이 안 난다).

> **좁히기(narrowing)** — 제어 흐름을 보고 분기 안에서 타입을 더 구체적으로 읽는 것.\
> 예: `if (typeof u === "string")` 안에서 `u` 가 `string` 이 된다.

> **완전성 검사(exhaustiveness check)** — 모든 갈래를 다뤘는지 컴파일러에게 검사시키는 관용구.\
> 예: `default` 에서 `const rest: never = sh;` — 남은 갈래가 있으면 그 이름을 진단에 적어 준다.

> **판별 유니온(discriminated union)** — 공통 리터럴 필드로 갈래를 가르는 유니온.\
> 예: `{ kind: "circle"; r: number } \| { kind: "square"; s: number }` 의 `kind` 가 판별 필드다.

> **전염(contagion)** — `any` 가 닿은 표현식이 줄줄이 `any` 가 되는 현상.\
> 예: `a.foo.bar + 1` 이 `any` 라, 그 결과를 `string` 에도 `number` 에도 넣을 수 있게 된다.

## 더 들어가면

- **`unknown` 을 API 경계에 두는 설계** — 라이브러리의 `parse(raw: unknown)` 는 호출자에게 **좁히기를 강제**한다. `any` 로 받으면 그 의무가 사라진다.
- **`never` 의 다른 얼굴** — 조건부 타입에서 `never` 는 **유니온에서 빠지는 것**을 뜻한다(`Exclude` 가 그렇게 구현돼 있다). [목록의 **24번 주제**](../24-conditional-types-and-distribution/).
- **`void` 를 변수 타입으로 쓰는 경우** — 드물지만 `Promise<void>` 처럼 **타입 인자**로는 자주 쓴다. 그때도 뜻은 「반환값을 안 본다」다.
- **`catch` 변수** — 이 판은 `strict` 가 기본 `true` 라 `catch (e)` 의 `e` 가 `unknown` 이다. 그래서 `e.message` 를 바로 못 읽고 `(e as Error).message` 나 `instanceof Error` 가 필요하다(`ex.04h.ts` 가 그 형태다).
