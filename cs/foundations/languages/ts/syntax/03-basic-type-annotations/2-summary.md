# ts/syntax/03 — 기본 타입 표기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html) ·
> [Handbook — Object Types](https://www.typescriptlang.org/docs/handbook/2/objects.html) ·
> [Handbook — Type Inference](https://www.typescriptlang.org/docs/handbook/type-inference.html) ·
> [TSConfig — `declaration`](https://www.typescriptlang.org/tsconfig/#declaration).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·`.d.ts` 전문은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ **`tsc` 가 7.0.2 다 — 5.x 가 아니다.** 이 주제에서 결과를 좌우하는 기본값은 **`strict` 가 켜져 있다**는 것이다(7.0 기본 `true`).
> `--strict false` 로 던진 블록은 **배너에 그렇게 적혀 있다** — 옵션이 결과를 바꾸는 갈래라 배너를 반드시 같이 읽는다.
> **버전** — 원시·배열·객체·함수 타입은 TS 1.x, 튜플의 **나머지 요소**는 3.0, **이름표 튜플**은 4.0,
> `as const` 는 3.4, `readonly` 배열 표기는 3.4 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·**`.d.ts` 전문** | 같은 입력·같은 옵션이면 같은 글자다. 10회 재실행에서 안 바뀌었다 |
| **안 흔들린다** | `.d.ts` 안의 **프로퍼티 순서** | 선언 순서를 따른다 — 해시 순회가 아니다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ **소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다** — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 한눈에 — 쉽게 말하면

**표기는 값에 붙이는 라벨이 아니라, 그 자리에 들어올 수 있는 값의 목록이다.**

| 비유 | 실체 |
|---|---|
| 택배 상자에 「깨지는 물건」 스티커 | `let x: number` — **그 자리에 올 수 있는 것**을 적어 둔 것 |
| 스티커를 안 붙여도 창고가 내용물을 보고 분류한다 | **추론** — `const n = 42` 의 타입은 적지 않아도 정해진다 |
| ★ 「이 상자」와 「이런 상자들」은 다르다 | `const n = 42` 는 **`42`**, `let m = 42` 는 **`number`** |
| 칸이 정해진 서랍장 | **튜플** — `[string, number]`. 개수와 순서가 고정 |
| 크기만 정해진 자루 | **배열** — `number[]`. 개수가 안 정해져 있다 |
| 「열어 보지 말 것」 테이프 | **`readonly`** — 검사 시각에만 막는다. **런타임에는 안 붙는다** |
| 내용물째 못 박기 | **`as const`** — 값을 리터럴 타입으로 굳히고 전부 `readonly` 로 만든다 |
| 창고에 「무엇으로 분류했니」라고 묻기 | **`.d.ts` 를 뽑아 보기** — 추론 결과가 글자로 나온다 |

- ★★ 한 줄로 — **「표기는 값을 바꾸지 않는다. 그 자리에 무엇이 올 수 있는지만 정한다.」**
- ★★ 그래서 이 주제의 창은 **`.d.ts`** 다. 추론된 타입을 **컴파일러의 글자로** 볼 수 있다.

```text
   const n = 42            let m = 42
        │                       │
        ▼                       ▼
   리터럴 타입 42          넓혀진 타입 number
   (다시 대입 못 하므로)    (다시 대입할 수 있으므로)
        │                       │
        ▼                       ▼
   .d.ts:  const n = 42    .d.ts:  let m: number

   ★ `.d.ts` 의 모양 자체가 다르다 —
     리터럴로 굳은 것은 `= 42`, 넓혀진 것은 `: number`.
```

```text
  배열과 튜플 — 같은 `[]` 인데 다른 물건
  number[]                         [string, number]
  +---+---+---+---+ ...            +--------+--------+
  | 1 | 2 | 3 | 4 |                | "a"    |   1    |
  +---+---+---+---+ ...            +--------+--------+
    길이 모름 · 전부 같은 타입        길이 2 고정 · 칸마다 타입이 다름
    arr[0] 의 타입: number           t[0] 의 타입: string
                                     t[1] 의 타입: number
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 표기가 있나** — 원시·배열·튜플·객체·함수를 쓰는 **형태**는 무엇인가.
2. **어디를 추론에 맡기고 어디를 명시하나** — 안 적어도 되는 자리와 **꼭 적어야 하는 자리**를 무엇으로 가르나.
3. **추론 결과를 어떻게 확인하나** — 「이게 무슨 타입으로 잡혔지?」를 **편집기 없이** 알아내는 방법이 있나.

★ 이 주제가 표기의 **토대**다. [**04번 주제**](../04-any-unknown-never-void/)가 그 위에서 **네 특수 타입**을, [**05번 주제**](../05-structural-typing/)가 **할당 가능성의 규칙**을 얹는다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`.d.ts` 덤프** | **추론된 타입이 글자로** 나온다 | ★ 이 주제의 고유 창 |
| ★★ **일부러 `null` 에 넣어 보기** | 진단 문구가 **그 값의 타입을 그대로 말한다** | ★ 이 주제의 고유 창 |
| **진단 전문** | 「이 자리에 이건 못 온다」 | 모든 주제 공통 |
| **방출된 `.js`** | 표기가 **한 글자도 안 남는 것** | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |

★ **앞의 둘이 이 주제의 값이다.** 「이게 무슨 타입이지」를 짐작하지 말고 **컴파일러에게 말하게 한다.**

비용 — `.d.ts` 는 `--declaration --emitDeclarationOnly` 한 번. `null` 탐침은 컴파일 한 번.

### (1) ★★ 원시 타입 — 표기한 것과 추론된 것

**언제 쓰나** — 「`const` 와 `let` 이 같은 값인데 왜 타입이 다르지?」에서 막혔을 때.

```ts
// ex.03a.ts
// 원시 타입 표기와, 표기를 안 했을 때 추론되는 것을 나란히 둔다
export const n = 42;
export let m = 42;
export const s = "circle";
export let t = "circle";
export const b = true;
export const big = 10n;
export const sym = Symbol("k");
export const nul = null;
export const und = undefined;
export const annotated: number = 42;
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.03a.ts (tsc exit=0) =====
===== 방출된 ex.03a.d.ts =====
export declare const n = 42;
export declare let m: number;
export declare const s = "circle";
export declare let t: string;
export declare const b = true;
export declare const big = 10n;
export declare const sym: unique symbol;
export declare const nul: null;
export declare const und: undefined;
export declare const annotated: number;
```

그림 해설 — 한 단계에 한 문장.

- ★★★ `const n = 42` 는 **`= 42`**, `let m = 42` 는 **`: number`** 다. 같은 값인데 `.d.ts` 의 **모양 자체가 다르다**.
- 같은 갈림이 문자열에도 있다 — `const s = "circle"` 은 `= "circle"`, `let t` 는 `: string`.
- `const b = true` 도 `= true` 로 굳었고, `const big = 10n` 은 `= 10n` 이다.
- ★ `const sym = Symbol("k")` 는 **`: unique symbol`** 이다 — 값 하나만을 가리키는 특수한 타입.
- `const nul = null` 은 `: null`, `const und = undefined` 는 `: undefined` 다 — `strictNullChecks` 가 켜져 있어 **따로 존재**한다.
- `const annotated: number = 42` 는 **표기가 이긴다** — 리터럴로 안 굳고 `: number` 다.

> **넓히기(widening)** — 리터럴 값에서 추론할 때 **다시 대입될 수 있으면** 더 넓은 타입으로 올려 잡는 것.\
> 예: `let m = 42` 는 나중에 `m = 7` 이 될 수 있으므로 `number` 로 잡는다. `const` 는 못 바꾸므로 `42` 로 굳는다.

비용 — 없음. 전부 검사 시각의 판정이다.

### (2) ★ 배열 두 표기는 **같은 타입**이다

**언제 쓰나** — `T[]` 와 `Array<T>` 중 무엇을 쓸지 고를 때.

```ts
// ex.03b.ts
// 배열 두 표기와 readonly — 표기가 다르면 타입도 다른가
export const a: number[] = [1, 2, 3];
export const b: Array<number> = a;
export const c: number[] = b;
export const nested: string[][] = [["x"], ["y"]];
export const union1: (string | number)[] = [1, "a"];
export const union2: string[] | number[] = [1, 2];
export const ro: readonly number[] = [1, 2, 3];
export const ro2: ReadonlyArray<number> = ro;
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.03b.ts (tsc exit=0) =====
===== 방출된 ex.03b.d.ts =====
export declare const a: number[];
export declare const b: Array<number>;
export declare const c: number[];
export declare const nested: string[][];
export declare const union1: (string | number)[];
export declare const union2: string[] | number[];
export declare const ro: readonly number[];
export declare const ro2: ReadonlyArray<number>;
```

그림 해설 — 한 단계에 한 문장.

- `a: number[]` 를 `b: Array<number>` 에 넣고 다시 `c: number[]` 에 넣었는데 **에러가 0건**이다 — 두 표기는 **같은 타입**이다.
- ★ 그런데 `.d.ts` 는 **적은 대로 되돌려 준다** — `b: Array<number>`, `ro2: ReadonlyArray<number>`. 표기가 보존된다.
- `union1: (string | number)[]` 과 `union2: string[] | number[]` 은 **다른 타입**이다 — 앞은 「섞인 배열」, 뒤는 「둘 중 한 종류의 배열」.
- `readonly number[]` 와 `ReadonlyArray<number>` 도 같은 타입이다.

비용 — 없음. 표기 취향의 문제다. ★ 다만 **`readonly` 는 `T[]` 꼴에만 붙는다** — `readonly Array<number>` 는 못 쓴다.

### (3) ★★ `readonly` 를 건드리면 — 네 가지 다른 진단

**언제 쓰나** — 「`readonly` 가 정확히 무엇을 막나」가 궁금할 때.

```ts
// ex.03c.ts
// readonly 배열·튜플에 손대면 무엇이라고 하나
const ro: readonly number[] = [1, 2, 3];
ro.push(4);
ro[0] = 9;
const mutable: number[] = ro;

const rt: readonly [string, number] = ["a", 1];
rt[0] = "b";

const pair: [string, number] = ["a", 1];
const tooMany: [string, number] = ["a", 1, 2];
const tooFew: [string, number] = ["a"];
console.log(ro, mutable, rt, pair, tooMany, tooFew);
```

```text
===== tsc --pretty false --noEmit ex.03c.ts (tsc exit=1) =====
ex.03c.ts(3,4): error TS2339: Property 'push' does not exist on type 'readonly number[]'.
ex.03c.ts(4,1): error TS2542: Index signature in type 'readonly number[]' only permits reading.
ex.03c.ts(5,7): error TS4104: The type 'readonly number[]' is 'readonly' and cannot be assigned to the mutable type 'number[]'.
ex.03c.ts(8,4): error TS2540: Cannot assign to '0' because it is a read-only property.
ex.03c.ts(11,7): error TS2322: Type '[string, number, number]' is not assignable to type '[string, number]'.
  Source has 3 element(s) but target allows only 2.
ex.03c.ts(12,7): error TS2322: Type '[string]' is not assignable to type '[string, number]'.
  Source has 1 element(s) but target requires 2.
```

그림 해설 — 한 단계에 한 문장.

- `ro.push(4)` 는 **`TS2339` — 프로퍼티가 없다**. `readonly number[]` 에는 `push` 라는 멤버 자체가 없다.
- `ro[0] = 9` 는 **`TS2542` — 인덱스 시그니처가 읽기만 허용한다**.
- `const mutable: number[] = ro` 는 **`TS4104`** — readonly 를 가변 타입에 못 넣는다. ★ **반대 방향은 된다.**
- `rt[0] = "b"`(readonly 튜플)는 **`TS2540` — 읽기 전용 프로퍼티**. 배열의 `TS2542` 와 **코드가 다르다**.
- 튜플 길이가 안 맞으면 `TS2322` 인데 둘째 줄 문구가 갈린다 — 「allows only 2」와 「requires 2」.
- ★★ 즉 **한 낱말 `readonly` 가 자리마다 다른 진단**을 낸다. 「읽기 전용이면 에러」로 뭉뚱그리면 못 고친다.

비용 — 검사 시각뿐이다. ★★ **런타임에는 아무것도 안 막는다** — 방출에서 `readonly` 가 사라진다([**01번 주제**](../01-what-ts-adds-and-erases/)).

### (4) ★★ 튜플 네 모양

**언제 쓰나** — 함수가 「두 개를 정해진 순서로」 돌려줄 때.

```ts
// ex.03d.ts
// 튜플의 네 모양 — 고정·선택·나머지·이름표
export type Fixed = [string, number];
export type Opt = [string, number?];
export type Rest = [string, ...number[]];
export type Named = [first: string, second: number];

export const fixed: Fixed = ["a", 1];
export const opt1: Opt = ["a"];
export const opt2: Opt = ["a", 1];
export const rest1: Rest = ["a"];
export const rest2: Rest = ["a", 1, 2, 3];
export const named: Named = ["a", 1];

export function first(t: Fixed) {
    return t[0];
}
export function sum(...xs: [string, ...number[]]) {
    return xs[0] + String(xs.length);
}
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.03d.ts (tsc exit=0) =====
===== 방출된 ex.03d.d.ts =====
export type Fixed = [string, number];
export type Opt = [string, number?];
export type Rest = [string, ...number[]];
export type Named = [first: string, second: number];
export declare const fixed: Fixed;
export declare const opt1: Opt;
export declare const opt2: Opt;
export declare const rest1: Rest;
export declare const rest2: Rest;
export declare const named: Named;
export declare function first(t: Fixed): string;
export declare function sum(...xs: [string, ...number[]]): string;
```

그림 해설 — 한 단계에 한 문장.

- `Fixed = [string, number]` — 길이 **2 고정**. 더 많아도 적어도 `TS2322`(3절 참조).
- `Opt = [string, number?]` — 둘째가 **선택**. `["a"]` 와 `["a", 1]` 이 **둘 다 통과**했다.
- `Rest = [string, ...number[]]` — 첫째만 고정이고 뒤는 **몇 개든**. `["a"]` 와 `["a",1,2,3]` 이 둘 다 통과했다.
- `Named = [first: string, second: number]` — **이름표**는 타입을 안 바꾸고 읽기만 돕는다. `.d.ts` 에 이름표가 그대로 남는다.
- ★ `function sum(...xs: [string, ...number[]])` 처럼 **나머지 매개변수를 튜플로** 적을 수 있다 — 가변 인자의 타입을 칸별로 고정하는 법이다.

```text
  [string, number]            [string, number?]        [string, ...number[]]
  +-----+-----+               +-----+ - - - +          +-----+-----+-----+ ...
  | "a" |  1  |               | "a" |   1?  |          | "a" |  1  |  2  |
  +-----+-----+               +-----+ - - - +          +-----+-----+-----+ ...
   길이 2만                    길이 1 또는 2             길이 1 이상
```

비용 — 없음. 방출에서는 그냥 배열이다.

### (5) ★★ 객체 타입과 함수 타입

**언제 쓰나** — 「`interface` 로 쓸까 `type` 으로 쓸까」 이전에, **무엇을 적어야 하나**를 정할 때.

```ts
// ex.03e.ts
// 객체 타입과 함수 타입 — 표기 자리와 추론 자리
export interface User {
    id: string;
    name: string;
    nickname?: string;
    readonly createdAt: number;
}
export type Formatter = (u: User, upper?: boolean) => string;
export type Registry = { [key: string]: User };

export const format: Formatter = (u, upper) => (upper ? u.name.toUpperCase() : u.name);

export function make(id: string, name: string): User {
    return { id, name, createdAt: 0 };
}

export const inferred = make("u-1", "준");
export const registry: Registry = { "u-1": inferred };

export function pick(u: User) {
    return { id: u.id, label: u.name };
}
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.03e.ts (tsc exit=0) =====
===== 방출된 ex.03e.d.ts =====
export interface User {
    id: string;
    name: string;
    nickname?: string;
    readonly createdAt: number;
}
export type Formatter = (u: User, upper?: boolean) => string;
export type Registry = {
    [key: string]: User;
};
export declare const format: Formatter;
export declare function make(id: string, name: string): User;
export declare const inferred: User;
export declare const registry: Registry;
export declare function pick(u: User): {
    id: string;
    label: string;
};
```

그림 해설 — 한 단계에 한 문장.

- `nickname?: string` 은 **선택 프로퍼티**, `readonly createdAt: number` 는 **읽기 전용**이다. `.d.ts` 에 그대로 보존된다.
- `Formatter = (u: User, upper?: boolean) => string` 이 **함수 타입 표기**다. 화살표 왼쪽이 매개변수, 오른쪽이 반환.
- ★ `const format: Formatter = (u, upper) => …` 에서 **매개변수에 표기를 안 썼다.** 왼쪽 표기에서 타입이 흘러 들어간다 — **문맥적 타이핑**.
- `Registry = { [key: string]: User }` 가 **인덱스 시그니처**다.
- ★ `function make(...): User` 는 **반환을 명시**했고, `const inferred = make(...)` 는 `.d.ts` 에 `: User` 로 나온다.
- ★ `function pick(u: User)` 는 반환을 **안 적었다.** `.d.ts` 가 추론 결과를 **객체 리터럴 타입 전문**으로 적어 준다.

방출을 보면 이 모든 표기가 사라진다.

```text
===== tsc --pretty false --module esnext ex.03e.ts (tsc exit=0) =====
===== 방출된 ex.03e.js =====
export const format = (u, upper) => (upper ? u.name.toUpperCase() : u.name);
export function make(id, name) {
    return { id, name, createdAt: 0 };
}
export const inferred = make("u-1", "준");
export const registry = { "u-1": inferred };
export function pick(u) {
    return { id: u.id, label: u.name };
}
```

> **문맥적 타이핑(contextual typing)** — 값이 놓인 **자리**에서 타입이 흘러 들어오는 것.\
> 예: `const format: Formatter = (u, upper) => …` 에서 `u` 는 적지 않았는데 `User` 가 된다.

비용 — 없음. 오히려 **표기를 줄여 준다.**

### (6) ★★★ `as const` 가 바꾸는 것

**언제 쓰나** — 「리터럴로 굳히고 싶다」·「이 객체를 통째로 읽기 전용으로」일 때.

```ts
// ex.03f.ts
// 표기를 안 하면 무엇이 되나 — as const 가 바꾸는 것
export const plainArr = [1, 2, 3];
export const constArr = [1, 2, 3] as const;
export const plainObj = { kind: "circle", r: 1 };
export const constObj = { kind: "circle", r: 1 } as const;
export const nested = { a: { b: [1, "x"] } } as const;
export const litConst = "circle";
export let litLet = "circle";
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.03f.ts (tsc exit=0) =====
===== 방출된 ex.03f.d.ts =====
export declare const plainArr: number[];
export declare const constArr: readonly [1, 2, 3];
export declare const plainObj: {
    kind: string;
    r: number;
};
export declare const constObj: {
    readonly kind: "circle";
    readonly r: 1;
};
export declare const nested: {
    readonly a: {
        readonly b: readonly [1, "x"];
    };
};
export declare const litConst = "circle";
export declare let litLet: string;
```

그림 해설 — 한 단계에 한 문장.

- `plainArr = [1,2,3]` 은 **`number[]`**, `constArr = [1,2,3] as const` 는 **`readonly [1, 2, 3]`** 이다.\
  ★★ **배열이 튜플이 되고, 원소가 리터럴로 굳고, `readonly` 가 붙는다 — 세 가지가 한꺼번에** 바뀐다.
- `plainObj` 는 `{ kind: string; r: number }`, `constObj` 는 `{ readonly kind: "circle"; readonly r: 1 }` 이다.
- ★ `nested` 를 보면 **재귀적으로** 들어간다 — 안쪽 배열까지 `readonly [1, "x"]` 다.
- `litConst = "circle"` 은 `as const` 없이도 `= "circle"` 로 굳는다 — `const` 선언 자체가 이미 굳힌다.
- `litLet` 은 `: string` 이다.

```text
  [1, 2, 3]                        [1, 2, 3] as const
  number[]                         readonly [1, 2, 3]
  ├ 길이 모름                       ├ 길이 3 고정  (튜플이 됐다)
  ├ 원소 타입 number                ├ 원소 타입 1 · 2 · 3  (리터럴로 굳었다)
  └ push 가능                       └ push 없음    (readonly 가 붙었다)
```

비용 — 없음. 방출에서 `as const` 는 **사라진다** — 런타임 객체가 얼지 않는다(`Object.freeze` 가 아니다).

### (7) ★★★ 추론 결과를 캐묻는 두 방법

**언제 쓰나** — 편집기 없이 「이게 무슨 타입으로 잡혔지?」를 확인할 때.

**방법 ①** — `.d.ts` 를 뽑는다. 위 절들이 전부 이 방법을 썼다.

**방법 ②** — 일부러 **`null` 에 넣어** 본다. 진단 문구가 그 값의 타입을 **그대로 말한다**.

```ts
// ex.03g.ts
// 추론된 타입을 컴파일러에게 캐묻는다 — 일부러 null 에 넣어 본다
const plainArr = [1, 2, 3];
const constArr = [1, 2, 3] as const;
const plainObj = { kind: "circle", r: 1 };
const constObj = { kind: "circle", r: 1 } as const;
const fn = (x: number) => x.toString();

const probe1: null = plainArr;
const probe2: null = constArr;
const probe3: null = plainObj;
const probe4: null = constObj;
const probe5: null = fn;
console.log(probe1, probe2, probe3, probe4, probe5);
```

```text
===== tsc --pretty false --noEmit ex.03g.ts (tsc exit=1) =====
ex.03g.ts(8,7): error TS2322: Type 'number[]' is not assignable to type 'null'.
ex.03g.ts(9,7): error TS2322: Type 'readonly [1, 2, 3]' is not assignable to type 'null'.
ex.03g.ts(10,7): error TS2322: Type '{ kind: string; r: number; }' is not assignable to type 'null'.
ex.03g.ts(11,7): error TS2322: Type '{ readonly kind: "circle"; readonly r: 1; }' is not assignable to type 'null'.
ex.03g.ts(12,7): error TS2322: Type '(x: number) => string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 다섯 줄이 각각 `number[]` · `readonly [1, 2, 3]` · `{ kind: string; r: number; }` · `{ readonly kind: "circle"; readonly r: 1; }` · `(x: number) => string` 을 **문구에 적어 준다**.
- ★ `.d.ts` 와 **같은 답**이 나왔다 — 두 창이 서로를 검증한다.
- ★★ 다만 **탐침에 한계가 있다** — `never` 는 `null` 에 **들어가므로 에러가 안 난다**. 그때는 `const x: never = v` 쪽으로 뒤집어 물어야 한다([**04번 주제**](../04-any-unknown-never-void/)).
- ★ `.d.ts` 쪽 한계도 있다 — **`export` 가 붙은 것만** 나온다. 지역 변수는 탐침 쪽이 낫다.

| | `.d.ts` 덤프 | `null` 탐침 |
|---|---|---|
| 대상 | `export` 된 것만 | **아무 표현식이나** |
| 형식 | 선언 전문 · 여러 줄 | 한 줄 문구 |
| 한계 | 지역 변수를 못 본다 | ★ `never`·`any` 는 **통과해 버려서** 못 본다 |
| 부작용 | 파일이 생긴다 | 에러가 난다(종료 코드 1) |

비용 — 둘 다 컴파일 한 번이다.

### (8) ★★ 표기를 빠뜨리면 검사가 꺼지는 자리

**언제 쓰나** — 「표기를 어디까지 생략해도 되나」의 경계를 그을 때.

```ts
// ex.03h.ts
// 표기를 빠뜨리면 검사가 통째로 꺼지는 자리
function twice(n) {
    return n * 2;
}
const handlers = {};
handlers.click = 1;

const evolving = [];
evolving.push(1);
evolving.push("a");

export const exported = [];
exported.push(1);

console.log(twice(2), handlers, evolving);
```

```text
===== tsc --pretty false --noEmit ex.03h.ts (tsc exit=1) =====
ex.03h.ts(2,16): error TS7006: Parameter 'n' implicitly has an 'any' type.
ex.03h.ts(6,10): error TS2339: Property 'click' does not exist on type '{}'.
ex.03h.ts(13,15): error TS2345: Argument of type '1' is not assignable to parameter of type 'never'.
```

`--strict false` 로 던지면 진단이 **하나로 줄어든다**.

```text
===== tsc --pretty false --noEmit --strict false ex.03h.ts (tsc exit=1) =====
ex.03h.ts(6,10): error TS2339: Property 'click' does not exist on type '{}'.
```

그림 해설 — 한 단계에 한 문장.

- `function twice(n)` 이 **`TS7006` — 암시적 `any`** 다. ★ **매개변수는 추론할 곳이 없다** — 여기가 표기 의무 자리다.
- `const handlers = {}` 뒤의 `handlers.click = 1` 은 **`TS2339`** 다. 빈 객체 리터럴은 `{}` 로 굳어 프로퍼티가 없다.
- ★★★ `const evolving = []` 은 **에러가 안 난다.** `push(1)` 과 `push("a")` 가 둘 다 통과했다 — **진화하는 `any[]`** 다.
- ★★★ 그런데 `export const exported = []` 는 **`TS2345` — `never`** 다. **`export` 가 붙으면 진화가 꺼진다.**\
  선언 파일에 적어야 하므로 그 자리에서 타입을 확정해야 하기 때문이다.
- `--strict false` 로 내리면 `TS7006` 과 `never` 진단이 **사라진다** — `TS2339` 만 남는다.
- ★ 즉 **이 절의 결과는 `strict` 설정의 함수**다. 배너를 같이 읽지 않으면 재현이 안 된다.

비용 — `noImplicitAny` 를 끄면 조용해지지만 **검사가 통째로 빠진다.**

## 문법 — 형태와 규칙

**형태** — 이 주제에서 쓴 표기를 한자리에 모으면 이렇다. 각 줄이 실제로 돌린 파일의 어느 줄인지 괄호에 적었다.

```text
원시      let x: number;  s: string;  b: boolean;  g: bigint;  y: symbol     (ex.03a.ts)
널        n: null;  u: undefined                                             (ex.03a.ts)
배열      number[]  ·  Array<number>                                         (ex.03b.ts)
읽기전용  readonly number[]  ·  ReadonlyArray<number>                         (ex.03b.ts)
튜플      [string, number]                                                   (ex.03d.ts)
  선택    [string, number?]                                                  (ex.03d.ts)
  나머지  [string, ...number[]]                                              (ex.03d.ts)
  이름표  [first: string, second: number]                                    (ex.03d.ts)
객체      { id: string; nickname?: string; readonly createdAt: number }      (ex.03e.ts)
인덱스    { [key: string]: User }                                            (ex.03e.ts)
함수      (u: User, upper?: boolean) => string                               (ex.03e.ts)
굳히기    [1, 2, 3] as const  ·  { kind: "circle" } as const                 (ex.03f.ts)
```

**규칙 불릿**

- ★ **원시 타입 이름은 전부 소문자다** — `number`·`string`·`boolean`·`bigint`·`symbol`·`null`·`undefined`.\
  대문자 `Number`·`String` 은 **래퍼 객체 타입**이라 거의 쓰지 않는다.
- ★ **배열은 `T[]` 와 `Array<T>` 두 표기가 같은 타입**이다. `readonly` 를 붙이려면 `readonly T[]` 또는 `ReadonlyArray<T>`.
- ★★ **`[]` 가 배열인지 튜플인지는 대괄호 안을 봐야 안다** — `number[]` 는 배열, `[number]` 는 **길이 1 튜플**이다.
- 튜플은 **선택 `?`** · **나머지 `...T[]`** · **이름표 `name: T`** 세 장식을 붙일 수 있다.
- 객체 타입은 `{ k: T }`, 선택은 `k?: T`, 읽기 전용은 `readonly k: T`, 인덱스 시그니처는 `[key: string]: T`.
- 함수 타입은 `(a: A, b?: B) => R`. **반환 자리에 `void`·`never` 가 올 수 있다**(→ [**04번 주제**](../04-any-unknown-never-void/)).
- ★★ **매개변수는 추론되지 않는다**(문맥적 타이핑이 걸린 자리 제외). `strict` 아래에서는 `TS7006` 이다.
- ★ **`as const` 는 표현식 뒤에** 붙는다. 선언 표기(`: T`)와 자리가 다르다.

**금지 사례** — 이 주제에서 던져 받은 것 여섯이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) readonly 배열에 push            ->  TS2339  Property 'push' does not exist …
2) readonly 배열에 인덱스 대입      ->  TS2542  Index signature … only permits reading.
3) readonly 튜플에 인덱스 대입      ->  TS2540  Cannot assign to '0' …
4) readonly 를 가변 배열에 대입     ->  TS4104  The type … is 'readonly' …
5) 튜플 길이 불일치                ->  TS2322  Source has 3 element(s) but target allows only 2.
6) 매개변수 표기 누락(strict)       ->  TS7006  Parameter 'n' implicitly has an 'any' type.
```

## 어디서 틀리나

- ★★★ **「`const` 니까 타입도 `number` 겠지」** — 아니다. `const n = 42` 의 타입은 **`42`** 다. `.d.ts` 의 `= 42` 가 근거다.
- ★★★ **「`readonly` 면 런타임에도 못 바꾸겠지」** — 못 막는다. 방출에서 사라진다. 진짜로 얼리려면 `Object.freeze` 다.
- ★★ **「`as const` 가 객체를 얼린다」** — 안 언다. **타입만** 바뀐다.
- ★★ **「빈 배열은 알아서 잘 되겠지」** — 자리가 갈린다. 지역 `const evolving = []` 은 **진화하는 `any[]`** 지만,\
  `export const exported = []` 는 **`never[]`** 라 `push(1)` 조차 `TS2345` 다.
- ★★ **`[number]` 를 「숫자 배열」로 읽는 것** — 그건 **길이 1 튜플**이다. 숫자 배열은 `number[]`.
- ★ **「`readonly` 에러는 다 같은 것」** — 넷이다(`TS2339`·`TS2542`·`TS2540`·`TS4104`). 고치는 법이 각각 다르다.
- ★ **「`string[] | number[]` 와 `(string | number)[]` 는 같은 것」** — 다르다. 앞은 **섞을 수 없다.**
- ★ **「매개변수도 추론되겠지」** — 안 된다. 문맥적 타이핑이 걸린 자리(콜백 등)만 예외다.
- ★ **「`Array<T>` 로 적었으니 `.d.ts` 에도 `T[]` 로 나오겠지」** — 적은 표기가 **그대로 보존**된다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | `T[]` 와 `Array<T>` 는 **같은 타입**이다 | 서로 오가는 대입이 에러 0건 |
| **언어 보장** | `const` 는 리터럴로 굳고 `let` 은 넓혀진다 | 핸드북의 넓히기 규칙. `.d.ts` 의 `= 42` 대 `: number` 가 그 결과다 |
| **언어 보장** | `as const` 는 **리터럴 고정 + 튜플화 + `readonly`** 를 재귀적으로 적용한다 | `.d.ts` 의 `readonly [1, 2, 3]` 과 중첩 결과 |
| **언어 보장** | `readonly` 는 **검사 시각에만** 막는다 | 방출 전문에 `readonly` 가 없다([**01번 주제**](../01-what-ts-adds-and-erases/)) |
| **설정에 달림** | `TS7006`(암시적 `any`) 과 `export const exported = []` 의 `never` | `--strict false` 로 내리면 **둘 다 사라진다**. 배너를 같이 읽어야 한다 |
| **이 판(7.0.2)의 관찰** | `.d.ts` 가 `Array<number>`·`ReadonlyArray<number>` 표기를 **보존**하는 것 | 선언 방출기의 구현이다. 「같은 타입이다」만 성질로 읽는다 |
| **이 판의 관찰** | 진단 문구의 **정확한 글자**(「Source has 3 element(s) but target allows only 2.」) | 문구는 판마다 바뀐다. 에러 **코드**가 더 오래 간다 |
| **이 판의 관찰** | 지역 `const evolving = []` 이 **진화하는 `any[]`** 인 것 | 제어 흐름 기반 추론의 구현 범위에 달렸다 |

★ **「여러 번 돌려 같았다」는 보장이 아니다.** 이 절의 대부분이 **`strict` 기본값이 `true` 인 7.0** 에서의 결과다.

## 언제 쓰고 언제 안 쓰나

| 표기한다 | 추론에 맡긴다 |
|---|---|
| ★ **함수 매개변수** — 추론할 곳이 없다 | 지역 변수 초기화 — `const n = 42` 에 `: number` 는 군더더기다 |
| ★ **모듈 경계(`export`)의 반환 타입** — 계약을 못 박고 선언 방출이 안정된다 | 지역 함수의 반환 타입 — 몸통에서 추론된다 |
| **빈 배열·빈 객체로 시작하는 변수** — `const xs: string[] = []` | 콜백 매개변수 — 문맥적 타이핑이 채운다 |
| 넓히고 싶을 때 — `const kind: string = "circle"` | 리터럴로 굳히고 싶을 때는 **오히려 표기를 빼고** `as const` |

| `as const` 를 쓴다 | 안 쓴다 |
|---|---|
| 설정 객체·상수 목록을 **유니온 타입의 원천**으로 쓸 때 | 나중에 바꿀 객체 — `readonly` 가 전부 붙어 불편해진다 |
| 판별 유니온의 `kind` 를 리터럴로 굳힐 때 | 런타임 불변을 원할 때 — 그건 `Object.freeze` 다 |

## 핵심 문장

1. **표기는 값을 바꾸지 않는다** — 그 자리에 무엇이 올 수 있는지만 정한다. 방출에서 전부 사라진다.
2. **`const` 는 리터럴로 굳고 `let` 은 넓혀진다** — `.d.ts` 의 `= 42` 와 `: number` 가 그 차이다.
3. **`[]` 안을 봐야 배열인지 튜플인지 안다** — `number[]` 는 배열, `[number]` 는 길이 1 튜플.
4. **`as const` 는 세 가지를 한꺼번에 한다** — 리터럴 고정 · 튜플화 · `readonly`, 그것도 재귀적으로.
5. **`readonly` 는 검사 시각의 약속일 뿐이다** — 자리마다 다른 네 진단을 내지만 런타임은 막지 않는다.
6. **매개변수는 추론되지 않는다** — 문맥적 타이핑이 걸린 자리만 예외다.
7. **추론 결과는 `.d.ts` 나 `null` 탐침으로 글자로 볼 수 있다** — 짐작하지 않는다.

## 관련 자료

- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 「표기가 방출에 안 남는다」는 그쪽이 정본이다. 여기서는 **무엇을 어떻게 적나**부터.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — 네 특수 타입은 그쪽이 정본. 여기서는 **원시·배열·튜플·객체·함수**까지.
- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — 「왜 이 값이 이 자리에 들어가나」의 규칙은 그쪽.
- [목록의 **06번 주제**](../06-excess-property-checks/)(초과 프로퍼티 검사) · **07번 주제**(객체 타입 세부) — 선택 프로퍼티·인덱스 시그니처의 전면 서술은 그쪽.
- [목록의 **11번 주제**](../11-literal-types-and-as-const/)(리터럴 타입과 `as const`) — `as const` 의 전면 서술은 그쪽. 여기서는 **추론을 바꾸는 도구**로서만 본다.
- 목록의 **46번 주제**(가변 튜플 타입) — 나머지 요소·이름표 튜플의 심화는 그쪽.
- `../../js/syntax/README.md` 의 **11번 주제**(스프레드와 나머지) — **런타임 의미는 JS 갈래가 정본**이다.

## 용어 풀이

> **표기(type annotation)** — 값이나 이름 뒤에 `: T` 로 타입을 적는 것.\
> 예: `let x: number;` 의 `: number`. 방출된 JS 에는 한 글자도 안 남는다.

> **추론(inference)** — 표기를 안 적었을 때 컴파일러가 초기값·문맥에서 타입을 정하는 것.\
> 예: `const n = 42` 에 아무것도 안 적었는데 타입이 `42` 가 된다.

> **넓히기(widening)** — 리터럴에서 추론할 때 **다시 대입될 수 있으면** 더 넓은 타입으로 올려 잡는 것.\
> 예: `let m = 42` 는 `number`, `const n = 42` 는 `42`.

> **리터럴 타입(literal type)** — 값 하나만 담을 수 있는 타입.\
> 예: `"circle"` 타입에는 문자열 `"circle"` 말고 아무것도 못 들어간다.

> **튜플(tuple)** — 길이와 칸별 타입이 고정된 배열 타입.\
> 예: `[string, number]` 에는 `["a", 1]` 은 되지만 `["a"]` 나 `[1, "a"]` 는 안 된다.

> **인덱스 시그니처(index signature)** — 「키가 무엇이든 값은 이 타입」을 적는 것.\
> 예: `{ [key: string]: User }` 는 `reg["아무거나"]` 가 `User` 라는 뜻이다.

> **문맥적 타이핑(contextual typing)** — 값이 놓인 자리에서 타입이 흘러 들어오는 것.\
> 예: `const f: (n: number) => string = (n) => …` 에서 `n` 을 안 적어도 `number` 가 된다.

> **선언 방출(declaration emit)** — `--declaration` 으로 `.d.ts` 를 만드는 것. **`export` 된 것만** 적는다.\
> 예: `export const n = 42` 가 `export declare const n = 42;` 로 나온다.

> **진화하는 `any[]`(evolving array)** — 빈 배열로 시작한 **지역** 변수의 타입을, 이후 `push` 들을 보고 넓혀 주는 추론.\
> 예: `const a = []; a.push(1); a.push("a");` 가 `(string | number)[]` 가 된다. ★ `export` 가 붙으면 꺼진다.

## 더 들어가면

- **`.d.ts` 는 이 갈래 내내 쓰는 도구다.** 뒤 주제에서도 「이게 무슨 타입이지」가 막힐 때마다 `--declaration --emitDeclarationOnly` 한 줄이면 답이 나온다.
- **`satisfies`(4.9)는 이 주제의 다음 수다** — 표기는 추론을 **덮어쓰지만**, `satisfies` 는 검사만 하고 추론을 **살려 둔다**([목록의 **29번 주제**](../29-satisfies/)).
- **`noUncheckedIndexedAccess`** 를 켜면 `arr[0]` 의 타입이 `number` 가 아니라 `number | undefined` 가 된다. 이 주제의 결과가 통째로 바뀌는 플래그다([목록의 **41번 주제**](../41-index-and-optional-property-strict-flags/)).
- **`tsc --init` 이 권하는 기본값**에 `noUncheckedIndexedAccess` 와 `exactOptionalPropertyTypes` 가 **켜져 있다**(이 판에서 확인). 하지만 **명령줄에서 파일을 직접 주면 그 설정이 안 읽힌다** — 이 문서의 결과는 전부 그 상태다.
