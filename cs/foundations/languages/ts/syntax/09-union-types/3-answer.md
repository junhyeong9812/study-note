# ts/syntax/09 — 유니온 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·`.d.ts` 전문·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제에서는 「**진단 목록에 없는 줄**」이 근거다. 2번은 **탐침 열 개에 진단 아홉 건**이라 빠진 하나가 답이다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **4건**(6·7·20·24행) — 들여쓴 줄이 **범인을 번갈아 짚는다**

**출력**

```ts
// ex.09a.ts
// 유니온 값에서 쓸 수 있는 멤버는 어디까지인가
type SN = string | number;
declare const v: SN;

const shared = v.toString();
const onlyNumber = v.toFixed(2);
const onlyString = v.length;

interface Bird {
    name: string;
    fly(): void;
}
interface Fish {
    name: string;
    swim(): void;
}
declare const pet: Bird | Fish;

const common = pet.name;
pet.fly();

const putString: SN = "s";
const putNumber: SN = 1;
const putBoolean: SN = true;
console.log(shared, onlyNumber, onlyString, common, putString, putNumber, putBoolean);
```

```text
===== tsc --pretty false --noEmit ex.09a.ts (tsc exit=1) =====
ex.09a.ts(6,22): error TS2339: Property 'toFixed' does not exist on type 'SN'.
  Property 'toFixed' does not exist on type 'string'.
ex.09a.ts(7,22): error TS2339: Property 'length' does not exist on type 'SN'.
  Property 'length' does not exist on type 'number'.
ex.09a.ts(20,5): error TS2339: Property 'fly' does not exist on type 'Bird | Fish'.
  Property 'fly' does not exist on type 'Fish'.
ex.09a.ts(24,7): error TS2322: Type 'boolean' is not assignable to type 'SN'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 | 들여쓴 줄이 짚는 것 |
|---|---|---|---|
| `v.toString()` | 둘 다 가진 멤버 | **통과** | — |
| `v.toFixed(2)` | `number` 에만 있다 | **TS2339** | **`'string'`** |
| `v.length` | `string` 에만 있다 | **TS2339** | **`'number'`** |
| `pet.name` | `Bird`·`Fish` 둘 다 | **통과** | — |
| `pet.fly()` | `Bird` 에만 있다 | **TS2339** | **`'Fish'`** |
| `const putString: SN = "s"` · `putNumber` | 멤버 하나 | **통과** | — |
| `const putBoolean: SN = true` | 멤버가 아니다 | **TS2322** | — |

- ★★★ **들여쓴 줄이 「어느 멤버에 없나」를 짚어 준다.** 6행은 `string` 을, 7행은 `number` 를 — **범인이 반대쪽**이다.\
  진단 첫 줄만 읽으면 「`SN` 에 없다」라 어느 쪽 탓인지 모른다.
- ★★ **방향이 반대로 넓다** — 꺼낼 때는 **모든 멤버에 있어야**(교집합), 넣을 때는 **하나만 맞으면 된다**(합집합).
- ★ 그래서 24행 `true` 만 막힌다 — `string` 도 `number` 도 아니다.

### 2. ★★★ 탐침 **10개**에 진단 **9건** — 빠진 것은 **20행(`string | any`)**

**출력**

```ts
// ex.09b.ts
// 적은 대로 남나 — 컴파일러에게 유니온의 실제 모양을 캐묻는다
declare const dup: string | number | string;
declare const withNever: string | never | number;
declare const withLiteral: "x" | "y" | string;
declare const bools: true | false;
declare const reordered: number | string;
declare const nestedUnion: (string | number) | (number | boolean);
declare const nullish: string | undefined | null;
declare const withAny: string | any;
declare const withUnknown: string | unknown;
declare const sortedLiterals: 3 | 1 | 2;

const p1: null = dup;
const p2: null = withNever;
const p3: null = withLiteral;
const p4: null = bools;
const p5: null = reordered;
const p6: null = nestedUnion;
const p7: null = nullish;
const p8: null = withAny;
const p9: null = withUnknown;
const p10: null = sortedLiterals;
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10);
```

```text
===== tsc --pretty false --noEmit ex.09b.ts (tsc exit=1) =====
ex.09b.ts(13,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.09b.ts(14,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.09b.ts(15,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.09b.ts(16,7): error TS2322: Type 'boolean' is not assignable to type 'null'.
ex.09b.ts(17,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.09b.ts(18,7): error TS2322: Type 'string | number | boolean' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.09b.ts(19,7): error TS2322: Type 'string | null | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.09b.ts(21,7): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.09b.ts(22,7): error TS2322: Type '1 | 2 | 3' is not assignable to type 'null'.
  Type '1' is not assignable to type 'null'.
```

**왜 그런가**

| 적은 것 | 탐침이 답한 것 | 무엇이 일어났나 |
|---|---|---|
| `string \| number \| string` | `string \| number` | **중복 제거** |
| `string \| never \| number` | `string \| number` | **`never` 흡수** |
| `"x" \| "y" \| string` | **`string`** | ★ **리터럴이 기반 타입에 흡수** |
| `true \| false` | **`boolean`** | 합쳐진다 |
| `number \| string` | **`string \| number`** | ★★ **순서가 바뀐다** |
| `(string \| number) \| (number \| boolean)` | `string \| number \| boolean` | **평탄화 + 중복 제거** |
| `string \| undefined \| null` | `string \| null \| undefined` | 순서 조정 |
| `string \| any` | ★★★ **진단 없음** | **`any` 가 먹었다** — `any` 는 `null` 에 들어간다 |
| `string \| unknown` | **`unknown`** | `unknown` 이 먹었다 |
| `3 \| 1 \| 2` | **`1 \| 2 \| 3`** | ★ 리터럴도 정렬된다 |

- ★★★ **진단이 안 난 20행이 가장 많은 것을 말한다.** `string | any` 가 통째로 `any` 가 됐고,\
  `any` 는 `null` 자리에 그냥 들어가므로 탐침이 아무 말도 못 한다([**04번 주제**](../04-any-unknown-never-void/)).
- ★★ 즉 유니온에 `any` 를 한 조각 섞으면 **나머지 검사가 전부 사라진다.**
- ★★ 「**리터럴 흡수**」가 실무에서 가장 위험하다 — `"x" | "y" | string` 을 적어 놓고 「두 값만 허용된다」고 믿으면 틀린다.
- ★★★ **순서가 바뀌는 것은 이 판의 관찰이지 보장이 아니다.** 대조할 것은 순서가 아니라 「**같은 집합으로 정리된다**」는 성질이다.
- ★★ 이 열 칸 중 **설정에 달린 것이 하나**다. `--strictNullChecks false` 로 다시 던지면 **19행만 답이 바뀐다.**

```text
===== tsc --pretty false --noEmit --strictNullChecks false ex.09b.ts (tsc exit=1) =====
ex.09b.ts(13,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.09b.ts(14,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.09b.ts(15,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.09b.ts(16,7): error TS2322: Type 'boolean' is not assignable to type 'null'.
ex.09b.ts(17,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.09b.ts(18,7): error TS2322: Type 'string | number | boolean' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.09b.ts(19,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.09b.ts(21,7): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.09b.ts(22,7): error TS2322: Type '1 | 2 | 3' is not assignable to type 'null'.
  Type '1' is not assignable to type 'null'.
```

- `string | undefined | null` 이 그냥 **`string`** 이 된다 — 그 플래그를 끄면 `null`·`undefined` 가 **다른 타입에 흡수**된다.\
  나머지 여덟 줄은 글자 하나까지 같다.

### 3. ★★★ `.d.ts` 는 **정규화를 안 한다** — 적은 그대로 돌려준다

**출력**

```ts
// ex.09e.ts
// 선언 방출은 유니온을 적은 대로 되돌려 준다
export type Dup = string | number | string;
export type WithNever = string | never | number;
export type Reordered = number | string;
export type Bools = true | false;
export type Literals = 3 | 1 | 2;
export const fromLiteral = "circle";
export let widened = "circle";
export const picked: "a" | "b" = "a";
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.09e.ts (tsc exit=0) =====
===== 방출된 ex.09e.d.ts =====
export type Dup = string | number | string;
export type WithNever = string | never | number;
export type Reordered = number | string;
export type Bools = true | false;
export type Literals = 3 | 1 | 2;
export declare const fromLiteral = "circle";
export declare let widened: string;
export declare const picked: "a" | "b";
```

**왜 그런가**

| 선언 | `.d.ts` | 2번의 탐침 |
|---|---|---|
| `Dup = string \| number \| string` | **그대로** | `string \| number` |
| `WithNever = string \| never \| number` | **그대로** | `string \| number` |
| `Reordered = number \| string` | **그대로** | `string \| number` |
| `Bools = true \| false` | **그대로** | `boolean` |
| `Literals = 3 \| 1 \| 2` | **그대로** | `1 \| 2 \| 3` |
| `const fromLiteral = "circle"` | `= "circle"` | — |
| `let widened = "circle"` | ★ **`: string`** | — |
| `const picked: "a" \| "b"` | 그대로 | — |

- ★★★ **같은 선언이 두 창에서 다르게 보인다.** 이것이 이 주제의 핵심 대비다.
- ★★ 선언 방출은 **소스의 타입 표기를 옮기는** 일이고, 탐침은 **계산된 타입을 찍는** 일이다.\
  그래서 「무엇을 적었나」는 `.d.ts` 가, 「무엇이 됐나」는 탐침이 답한다.
- ★ 값 쪽은 반대로 `.d.ts` 도 계산 결과를 적는다 — `const` 는 리터럴로 굳고 `let` 은 `string` 으로 넓어졌다([**03번 주제**](../03-basic-type-annotations/)).\
  **타입 별칭은 표기를 옮기고, 값 선언은 추론 결과를 적는다** — 한 파일 안에서 두 규칙이 같이 돈다.

### 4. ★★★ 진단 **4건** — `h("s")` 와 `h(1)` 이 **둘 다** 막히고 매개변수는 **`never`**

**출력**

```ts
// ex.09c.ts
// 유니온이 함수나 배열이면 — 매개변수 자리가 뒤집힌다
type Handler = ((a: string) => void) | ((a: number) => void);
declare const h: Handler;
h("s");
h(1);

declare const arr: string[] | number[];
arr.push("s");
const mapped = arr.map((x) => x);
const len = arr.length;

type Getter = (() => string) | (() => number);
declare const g: Getter;
const got: null = g();
console.log(mapped, len, got);
```

```text
===== tsc --pretty false --noEmit ex.09c.ts (tsc exit=1) =====
ex.09c.ts(4,3): error TS2345: Argument of type '"s"' is not assignable to parameter of type 'never'.
ex.09c.ts(5,3): error TS2345: Argument of type '1' is not assignable to parameter of type 'never'.
ex.09c.ts(8,10): error TS2345: Argument of type '"s"' is not assignable to parameter of type 'never'.
ex.09c.ts(14,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| `h("s")` | 함수 유니온에 인자 | **TS2345** — parameter of type **`never`** |
| `h(1)` | 〃 | **TS2345** — 같은 문구 |
| `arr.push("s")` | `string[] \| number[]` | **TS2345** — 역시 `never` |
| `arr.map((x) => x)` | 꺼내는 쪽 | ★ **통과** |
| `arr.length` | 꺼내는 쪽 | ★ **통과** |
| `const got: null = g()` | 반환 탐침 | **TS2322** — **`string \| number`** |

- ★★★ `h` 는 「`string` 을 받는 함수」**이거나** 「`number` 를 받는 함수」다. **어느 쪽인지 모른다.**\
  그러니 **둘 다에게 안전한 인자**만 받을 수 있고, 그 교집합이 `string & number` 라 **`never`** 다.
- ★★ **매개변수는 교집합, 반환은 합집합**이다 — 14행 탐침이 반환 쪽을 확인한다.
- ★ `push` 도 같은 이유로 막힌다. 반면 `map`·`length` 는 **꺼내는 쪽**이라 문제가 없다.
- ★★ 그래서 **유니온은 핸들러를 담는 그릇으로 나쁘다.** 오버로드나 판별 유니온으로 바꿔야 한다.

### 5. ★★★ 진단 **2건** — 전수 검사가 **`'Tri'`** 를 이름으로 짚는다

**출력**

```ts
// ex.09d.ts
// 판별 필드를 둔 유니온 — 분기마다 무엇이 남나
interface Circle {
    kind: "circle";
    r: number;
}
interface Square {
    kind: "square";
    side: number;
}
interface Tri {
    kind: "tri";
    base: number;
    h: number;
}
type Shape = Circle | Square | Tri;

function area(s: Shape): number {
    switch (s.kind) {
        case "circle":
            return 3 * s.r * s.r;
        case "square":
            return s.side * s.side;
        default: {
            const exhaustive: never = s;
            return exhaustive;
        }
    }
}

interface Ok {
    ok: true;
    data: string;
}
interface Err {
    ok: false;
    reason: string;
}
type Res = Ok | Err;

function read(r: Res) {
    if (r.ok) return r.data;
    return r.reason;
}
function readBad(r: Res) {
    return r.data;
}
console.log(area({ kind: "circle", r: 1 }), read({ ok: true, data: "d" }), readBad({ ok: true, data: "d" }));
```

```text
===== tsc --pretty false --noEmit ex.09d.ts (tsc exit=1) =====
ex.09d.ts(24,19): error TS2322: Type 'Tri' is not assignable to type 'never'.
ex.09d.ts(45,14): error TS2339: Property 'data' does not exist on type 'Res'.
  Property 'data' does not exist on type 'Err'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| `case "circle": s.r` · `case "square": s.side` | 판별로 좁혀졌다 | **통과** |
| `const exhaustive: never = s` | 남은 멤버가 있다 | **TS2322** — 「Type **'Tri'** is not assignable to type 'never'.」 |
| `if (r.ok) return r.data` | `true` 갈래 | ★ **통과** |
| `return r.reason` | `false` 갈래 | ★ **통과** |
| `readBad(r) { return r.data }` | 안 좁혔다 | **TS2339** — 들여쓴 줄이 **`'Err'`** 를 짚는다 |

- ★★★ 전수 검사는 「**남은 것을 `never` 자리에 넣어 보는**」 수법이다. 다 처리했으면 `s` 가 `never` 라 통과하고,\
  빠뜨렸으면 **그 멤버 이름이 진단에 나온다.** `Tri` 를 추가한 사람이 `area` 를 안 고쳤다는 것을 컴파일러가 잡아 준다.
- ★★ `if (r.ok)` 도 판별이다 — **불리언 리터럴**(`ok: true` / `ok: false`)이 판별 필드가 된다. 굳이 문자열일 필요가 없다.
- ★ `default` 에 `throw` 만 넣으면 **런타임에만** 걸린다. `never` 대입이 있어야 **컴파일 시각에** 잡힌다.
- ★ 판별 필드가 **리터럴 타입**이어야 한다 — `kind: string` 이면 `case` 로 못 좁힌다.

### 6. ★★★ `type Shape` 선언이 **통째로 없고** 남는 것은 **JS 연산자**다

**출력**

```ts
// ex.09f.ts
// 유니온은 방출에 한 글자도 안 남는다 — 갈라 쓰는 일은 JS 연산자가 한다
type Shape = { kind: "circle"; r: number } | { kind: "square"; side: number };

function area(s: Shape): number {
    if (s.kind === "circle") return 3 * s.r * s.r;
    return s.side * s.side;
}

function describe(v: string | number): string {
    return typeof v === "string" ? `문자열 ${v.length}자` : `숫자 ${v.toFixed(1)}`;
}

console.log("circle    :", area({ kind: "circle", r: 2 }));
console.log("square    :", area({ kind: "square", side: 3 }));
console.log("describe  :", describe("abc"), "/", describe(4));
console.log("런타임 구분:", typeof "abc", typeof 4);
```

```text
===== tsc --pretty false ex.09f.ts (tsc exit=0) =====
===== 방출된 ex.09f.js =====
"use strict";
function area(s) {
    if (s.kind === "circle")
        return 3 * s.r * s.r;
    return s.side * s.side;
}
function describe(v) {
    return typeof v === "string" ? `문자열 ${v.length}자` : `숫자 ${v.toFixed(1)}`;
}
console.log("circle    :", area({ kind: "circle", r: 2 }));
console.log("square    :", area({ kind: "square", side: 3 }));
console.log("describe  :", describe("abc"), "/", describe(4));
console.log("런타임 구분:", typeof "abc", typeof 4);
```

```text
===== node ex.09f.js (node exit=0) =====
circle    : 12
square    : 9
describe  : 문자열 3자 / 숫자 4.0
런타임 구분: string number
```

**왜 그런가**

| 확인 | 값 |
|---|---|
| 방출된 파일의 첫 줄 | `"use strict";` 다음이 곧장 `function area(s) {` — **`type Shape` 가 없다** |
| 좁히기를 하는 코드 | `s.kind === "circle"` · `typeof v === "string"` — **전부 JS 연산자** |
| `area({ kind: "circle", r: 2 })` | `12` |
| `area({ kind: "square", side: 3 })` | `9` |
| `describe("abc")` · `describe(4)` | 「문자열 3자」 · 「숫자 4.0」 |
| `typeof "abc"` · `typeof 4` | `string` · `number` |

- ★★★ 즉 **좁히기를 가능하게 한 코드가 곧 런타임에 도는 코드**다. 타입은 그 코드를 **읽고 따라간** 것뿐이다.
- ★★ 그래서 판별 필드는 **런타임에 실제로 있는 값**이어야 한다. 타입에만 있는 칸으로는 못 가른다([**01번 주제**](../01-what-ts-adds-and-erases/)).
- ★ 뒤집으면 **좋은 소식**이기도 하다 — 유니온을 아무리 복잡하게 써도 **번들이 한 글자도 안 커진다.**

### 7. ★★★ **값은 하나뿐이고 어느 쪽인지 모르기** 때문이다

**왜 그런가**

- `v: string | number` 라는 것은 「이 자리에 **어느 한쪽 값이 들어 있다**」는 뜻이다. **둘 다 들어 있는 게 아니다.**
- 그러니 **꺼내 쓰려면** 어느 쪽이 들어 있든 안전해야 한다 → **모든 멤버에 있는 멤버만**(교집합).
- 반대로 **넣을 때는** 「이것들 중 하나면 된다」가 이미 조건이다 → **하나만 맞으면 된다**(합집합).

```text
    꺼낸다 (읽기)                       넣는다 (쓰기)
  ┌──────────────────────┐          ┌──────────────────────┐
  │ 어느 쪽인지 모른다   │          │ 어느 쪽이든 받아 준다│
  │ → 둘 다에 있어야     │          │ → 하나만 맞으면      │
  │    안전하다          │          │    된다              │
  │   = 교집합           │          │   = 합집합           │
  └──────────────────────┘          └──────────────────────┘
```

- ★★ 한 줄로 — **「모른다」는 상태에서 안전한 연산의 집합이 교집합**이다.

### 8. ★★★ 같은 이유다 — **어느 함수인지 모르니 둘 다에게 안전한 인자만** 받는다

**왜 그런가**

- `h: ((a: string) => void) | ((a: number) => void)` 는 「**둘 중 한 함수가 들어 있다**」는 뜻이다.
- 호출은 **꺼내 쓰는 행위**다. `h(x)` 의 `x` 는 **어느 함수가 들어 있든 안전해야** 한다.
- `string` 을 넣으면 두 번째 함수일 때 터지고, `number` 를 넣으면 첫 번째 함수일 때 터진다.\
  둘 다 안전한 값의 집합이 `string & number` = **`never`** — **그런 값이 없다.**
- ★★ 4번의 진단 문구가 그것을 그대로 적는다 — 「not assignable to parameter of type 'never'」.
- ★ 반환은 반대다 — 어느 함수든 **나오는 값은 둘 중 하나**이므로 합집합(`string | number`)이다.
- ★★ [**05번 주제**](../05-structural-typing/)의 **반변**과 같은 뿌리다 — 매개변수 자리는 방향이 뒤집힌다.

### 9. ★★★ `.d.ts` 는 「**무엇을 적었나**」, 탐침은 「**무엇이 됐나**」

**왜 그런가**

| 창 | 무엇을 말하나 | 3번의 예 |
|---|---|---|
| `.d.ts` 덤프 | **소스에 적힌 타입 표기** | `type Dup = string \| number \| string` 그대로 |
| `null` 탐침 | **계산된 타입** | `string \| number` |

- ★★ 둘을 혼동하면 두 가지 실수가 난다 —

| 실수 | 결과 |
|---|---|
| `.d.ts` 를 보고 「정규화가 안 된다」고 믿는 것 | 에러 메시지가 다르게 보일 때 당황한다 |
| 탐침을 보고 「`.d.ts` 도 그렇겠다」고 믿는 것 | 라이브러리 소비자가 보는 계약을 잘못 예상한다 |

- ★ 그래서 **두 창을 같이 써야** 답이 온전해진다. 이 문서의 2번과 3번이 정확히 그 짝이다.
- ★ 값 선언은 또 다르다 — `.d.ts` 도 추론 결과를 적는다(`let widened: string`). **타입 별칭만 표기를 옮긴다.**

### 10. ★★★ 2번에서 `"x" | "y" | string` 이 **그냥 `string`** 이었다

**왜 그런가**

- 리터럴은 자기 **기반 타입**에 흡수된다. `"x"` 와 `"y"` 는 둘 다 `string` 이므로 **`string` 하나로 정리**된다.
- 그래서 `"asc" | "desc" | string` 이라고 적으면 **아무 문자열이나 들어온다.** 「두 값만 허용」이 **조용히 사라진다.**
- ★★★ 근거는 2번의 15행이다 — 탐침이 「Type **'string'** is not assignable to type 'null'.」이라고만 답했다.\
  `"x"` 도 `"y"` 도 문구에 없다. **이미 사라진 것이다.**
- ★★ 어디서 생기나 — 「자동완성은 남기고 싶어서」 유니온에 `string` 을 끼워 넣는 습관에서 생긴다.
- ★ 같은 집안의 사고가 **`string | any`** 다(2번의 20행) — 이쪽은 **진단이 아예 안 나서** 더 조용하다.
- ★ 피하는 길은 **`string` 을 안 섞는 것**이다. 자동완성을 살리는 관용구는 목록의 **11번 주제**에서 다룬다.

### 11. ★★ 조건 둘 — **모든 멤버를 처리한 갈래**와 **리터럴 판별 필드**

**왜 그런가**

| 조건 | 없으면 |
|---|---|
| **판별 필드가 리터럴 타입**이어야 한다 | `kind: string` 이면 `case` 가 못 좁혀서 `s` 가 계속 `Shape` 다 |
| **모든 갈래가 좁혀 나가야** 한다 | 한 군데라도 안 좁히면 마지막에 남는 것이 `never` 가 안 된다 |
| ★ **유니온이 닫혀 있어야** 한다 | 멤버가 `any` 를 포함하면 좁혀도 `any` 가 남는다(2번의 20행) |

- ★★ 그래서 5번이 작동한 이유는 셋이 다 갖춰졌기 때문이다 — `kind` 가 문자열 리터럴 셋이고, 두 `case` 가 각각 하나씩 걷어냈다.
- ★ `never` 대입이 **컴파일 시각의 검사**라는 점이 중요하다. `default: throw new Error()` 만 두면\
  **종류를 추가한 날이 아니라 그 종류가 실제로 들어온 날** 터진다.
- ★ 값으로도 쓸 수 있게 `return exhaustive;` 처럼 그 변수를 돌려주는 관용구를 쓴다 — 5번의 소스가 그 형태다.

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 좁히기 전에는 **모든 멤버에 있는 멤버만** 쓸 수 있다 · 유니온은 **평탄화·중복 제거·흡수**로 정규화된다 · 함수 유니온의 **매개변수는 교집합** · 판별 필드로 좁히고 `never` 대입으로 **전수 검사** · 방출에 안 남는다 |
| **설정에 달린 것** | `null`·`undefined` 가 **유니온 멤버로 분리돼 보이는 것** — `strictNullChecks`(`strict` 에 딸려 7.0 기본 `true`). **두 판을 다 던져** 2번의 19행 하나만 갈리는 것을 확인했다 |
| **이 판(7.0.2)의 관찰** | ★★ **정규화된 유니온의 멤버 순서**(`number \| string` → `string \| number`, `3 \| 1 \| 2` → `1 \| 2 \| 3`) · `.d.ts` 가 **정규화를 안 하는 것** · 진단 문구와 들여쓴 줄의 단계 수 |

- ★★★ **순서는 대조 기준으로 쓰지 않는다.** 「같은 집합으로 정리된다」는 성질만 성질로 읽는다.
- ★ 「**에러가 안 난 줄」도 이 판의 관찰이다** — 2번의 `withAny` 가 대표다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 공통 멤버 | `--noEmit ex.09a.ts` | exit 1 · `TS2339` 3건 + `TS2322` 1건 · 들여쓴 줄이 `string`·`number`·`Fish` 를 짚음 |
| 정규화 | `--noEmit ex.09b.ts` | exit 1 · 탐침 **10개에 진단 9건** · `string \| any` 만 진단 없음 |
| 〃 `strictNullChecks` 끔 | `--noEmit --strictNullChecks false ex.09b.ts` | exit 1 · **19행만** `string` 으로 바뀜 · 나머지 여덟 줄 동일 |
| 선언 방출 | `--declaration --emitDeclarationOnly ex.09e.ts` | exit 0 · **정규화 안 함** · `let widened: string` |
| 함수·배열 유니온 | `--noEmit ex.09c.ts` | exit 1 · `TS2345` 3건(전부 `never`) + `TS2322` 1건 · `map`·`length` 통과 |
| 판별·전수 검사 | `--noEmit ex.09d.ts` | exit 1 · `TS2322`(`'Tri'`) + `TS2339`(`'Err'`) **2건** |
| 방출·실행 | `tsc ex.09f.ts` + `node ex.09f.js` | tsc exit 0 · node exit 0 · `12` / `9` / 「문자열 3자」·「숫자 4.0」 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **정규화된 유니온의 멤버 순서** — 내부 타입 식별자 순이다. **이 문서의 대조 기준으로 쓰지 않는다.**
- `.d.ts` 가 타입 별칭의 표기를 그대로 옮기는 것 — 선언 방출기의 구현이다.
- 진단의 들여쓴 줄이 **어느 멤버를 대표로 짚는가** — 여러 멤버에 없을 때 어느 것을 고르는지는 구현이다.
- 진단 문구 전문 — 코드(`TS2339`·`TS2345`·`TS2322`)가 더 오래 간다.

**안 돌려 본 것**

- **유니온 크기에 따른 검사 시간** — 「더 들어가면」의 마지막 줄. **재지 않았고 수치를 적지 않았다.** 목록의 **45번 주제**에서 잰다.
- `"asc" | "desc" | (string & {})` 관용구 — 목록의 **11번 주제**에서 던진다. 여기서는 **형태만** 적었다.
