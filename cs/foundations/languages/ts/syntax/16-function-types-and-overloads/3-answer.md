# ts/syntax/16 — 함수 타입과 오버로드 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·`.d.ts` 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 4번과 6번은 **진단이 0줄인 것이 결론**이다. 그 블록도 **명령과 종료 코드까지** 캡처했다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **4건** — 함수의 타입에 **시그니처가 둘뿐**이다

**출력**

```ts
// ex.16a.ts
// 오버로드 시그니처와 구현 시그니처 — 구현 시그니처는 밖에서 안 보인다
function len(x: string): number;
function len(x: unknown[]): number;
function len(x: string | unknown[]): number {
    return x.length;
}

const byString = len("abc");
const byArray = len([1, 2]);
const p1: null = byString;

declare const either: string | unknown[];
const byUnion = len(either);

function overloadCount(x: string): 1;
function overloadCount(x: number): 2;
function overloadCount(x: boolean): 3;
function overloadCount(x: string | number | boolean): 1 | 2 | 3 {
    if (typeof x === "string") return 1;
    if (typeof x === "number") return 2;
    return 3;
}
const p2: null = overloadCount(true);
const p3: null = len;
console.log(byArray, byUnion, p1, p2, p3);
```

```text
===== tsc --pretty false --noEmit ex.16a.ts (tsc exit=1) =====
ex.16a.ts(10,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.16a.ts(13,21): error TS2769: No overload matches this call.
  The last overload gave the following error.
    Argument of type 'string | unknown[]' is not assignable to parameter of type 'unknown[]'.
      Type 'string' is not assignable to type 'unknown[]'.
ex.16a.ts(23,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.16a.ts(24,7): error TS2322: Type '{ (x: string): number; (x: unknown[]): number; }' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 10 | `len("abc")` | `number` — 오버로드가 골라졌다 |
| 13 | ★★★ `len(either)` — `either: string \| unknown[]` | **TS2769** — 「No overload matches this call.」 |
| 23 | `overloadCount(true)` | `3` — 리터럴 타입까지 보존된다 |
| 24 | ★★★ 함수 자체를 탐침에 | **`{ (x: string): number; (x: unknown[]): number; }`** |

- ★★★ 13행이 놀라운 자리다. `either` 의 타입은 구현 시그니처의 매개변수와 **글자까지 같다.**\
  그런데도 막힌다 — 진단이 「The last overload gave the following error.」라고 말한다.\
  **컴파일러가 시도한 후보는 오버로드 둘뿐**이었고, 구현 시그니처는 **후보에 없었다.**
- ★★★ 24행이 결정적 증거다. 탐침이 뱉은 타입에 **시그니처가 둘**이다 — `(x: string)` 과 `(x: unknown[])`.\
  `(x: string | unknown[])` 는 **없다.**
- ★★ 즉 오버로드된 함수의 타입은 **오버로드 시그니처만 모은 것**이다.\
  구현 시그니처는 **몸통을 검사할 때만** 쓰이고 그 뒤로는 사라진다.
- ★ 고치려면 **그 꼴의 오버로드를 하나 더 내걸면** 된다 — `function len(x: string | unknown[]): number;`.

### 2. ★★★ **`"넓은 쪽"` 과 `"좁은 쪽"`** — 몸통이 같아도 **적은 순서**가 답을 가른다

**출력**

```ts
// ex.16b.ts
// 오버로드 해석은 선언 순서다 — 같은 몸통을 순서만 바꿔 둘로 둔다
function wideFirst(x: string | number): "넓은 쪽";
function wideFirst(x: string): "좁은 쪽";
function wideFirst(x: string | number): string {
    return typeof x === "string" ? "좁은 쪽" : "넓은 쪽";
}
function narrowFirst(x: string): "좁은 쪽";
function narrowFirst(x: string | number): "넓은 쪽";
function narrowFirst(x: string | number): string {
    return typeof x === "string" ? "좁은 쪽" : "넓은 쪽";
}
const r1: null = wideFirst("a");
const r2: null = narrowFirst("a");

// 인자 개수로 갈리는 오버로드
function make(): "인자 없음";
function make(a: number): "하나";
function make(a: number, b: number): "둘";
function make(a?: number, b?: number): string {
    if (a === undefined) return "인자 없음";
    if (b === undefined) return "하나";
    return "둘";
}
const r3: null = make();
const r4: null = make(1);
const r5: null = make(1, 2);

// 선택 매개변수가 있는 하나짜리 시그니처와 비교
function make2(a?: number, b?: number): "하나로 다 받는다" {
    return "하나로 다 받는다";
}
const r6: null = make2();
console.log(r1, r2, r3, r4, r5, r6);
```

```text
===== tsc --pretty false --noEmit ex.16b.ts (tsc exit=1) =====
ex.16b.ts(12,7): error TS2322: Type '"넓은 쪽"' is not assignable to type 'null'.
ex.16b.ts(13,7): error TS2322: Type '"좁은 쪽"' is not assignable to type 'null'.
ex.16b.ts(24,7): error TS2322: Type '"인자 없음"' is not assignable to type 'null'.
ex.16b.ts(25,7): error TS2322: Type '"하나"' is not assignable to type 'null'.
ex.16b.ts(26,7): error TS2322: Type '"둘"' is not assignable to type 'null'.
ex.16b.ts(32,7): error TS2322: Type '"하나로 다 받는다"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 호출 | 결과 |
|---|---|---|
| 12 | `wideFirst("a")` — 넓은 꼴을 먼저 적음 | **`"넓은 쪽"`** |
| 13 | `narrowFirst("a")` — 좁은 꼴을 먼저 적음 | **`"좁은 쪽"`** |
| 24 / 25 / 26 | `make()` / `make(1)` / `make(1, 2)` | `"인자 없음"` / `"하나"` / `"둘"` |
| 32 | `make2()` — 선택 매개변수 하나짜리 | `"하나로 다 받는다"` |

- ★★★ 두 함수는 **몸통이 글자까지 같다.** 다른 것은 **오버로드를 적은 순서 하나**뿐이다.
- ★★★ `wideFirst("a")` 에서 컴파일러는 첫 오버로드 `(x: string | number)` 를 보고 **맞으므로 거기서 멈춘다.**\
  더 잘 맞는 `(x: string)` 을 **보지 않는다.** 「가장 잘 맞는 것」이 아니라 「**먼저 맞는 것**」이다.
- ★★ 그러므로 실무 규칙은 하나다 — **좁은 꼴부터 적어라.** 오버로드를 앞에 끼워 넣으면\
  **호출한 쪽의 타입이 조용히 바뀐다.**
- ★ 24·25·26행과 32행의 대비가 **오버로드가 필요한지**를 판단하는 기준이다.\
  `make` 는 **개수에 따라 반환이 갈리므로** 오버로드가 값을 내지만,\
  `make2` 는 늘 같은 것을 주므로 **선택 매개변수 하나면 충분**하다.

### 3. ★★ 진단 **3건** — `TS2394` 둘(**매개변수**와 **반환 타입**) · `TS2391` 하나

**출력**

```ts
// ex.16c.ts
// 구현 시그니처는 모든 오버로드를 덮어야 한다 — 그리고 바로 뒤에 붙어야 한다
function notCovered(x: string): number;
function notCovered(x: boolean): number;
function notCovered(x: string): number {
    return 1;
}
function returnNotCovered(x: string): string;
function returnNotCovered(x: number): number;
function returnNotCovered(x: string | number): string {
    return String(x);
}
function covered(x: string): string;
function covered(x: number): number;
function covered(x: string | number): string | number {
    return x;
}
function interrupted(x: string): number;
const between = 1;
function interrupted(x: number): string;
function interrupted(x: string | number): string | number {
    return x;
}
console.log(notCovered, returnNotCovered, covered, interrupted, between);
```

```text
===== tsc --pretty false --noEmit ex.16c.ts (tsc exit=1) =====
ex.16c.ts(3,10): error TS2394: This overload signature is not compatible with its implementation signature.
ex.16c.ts(8,10): error TS2394: This overload signature is not compatible with its implementation signature.
ex.16c.ts(17,10): error TS2391: Function implementation is missing or not immediately following the declaration.
```

**왜 그런가**

| 줄 | 무엇이 문제인가 | 코드 |
|---|---|---|
| 3 | `notCovered(x: boolean)` — 구현은 `x: string` 만 받는다 | **TS2394** — **매개변수** |
| 8 | `returnNotCovered(x: number): number` — 구현의 반환이 `string` | **TS2394** — **반환 타입** |
| 12\~16 | `covered` — 구현이 `(x: string \| number): string \| number` | ★ 조용하다 |
| 17 | 오버로드 사이에 `const between = 1;` 이 낌 | **TS2391** |

- ★★★ 3행과 8행이 같은 코드인 것이 요점이다. **`TS2394` 는 매개변수와 반환 타입 양쪽을 본다.**\
  「덮는다」는 것은 「그 오버로드로 부른 결과를 구현이 감당할 수 있다」는 뜻이고, 반환도 거기 포함된다.
- ★★ `covered` 가 조용한 이유는 구현이 **양쪽을 다 유니온으로 넓혀** 두었기 때문이다.\
  대가는 **몸통 안에서 좁히기가 늘어나는 것**이다([**12번 주제**](../12-narrowing/)).
- ★★★ 17행만 다른 코드다 — 「Function implementation is missing or not immediately following the declaration.」\
  오버로드 묶음 사이에 **다른 선언이 끼면** 그 앞의 시그니처가 **고아**가 된다. **주석은 괜찮지만 선언은 못 낀다.**
- ★ 17행 하나만 보고되고 그 뒤의 `function interrupted(x: number)` + 구현은 **정상 묶음**으로 처리된다.\
  즉 **끊긴 앞쪽만** 고아가 된다.

### 4. ★★★ 종료 코드 **0** — `.d.ts` 에서 **구현 시그니처가 사라진다**

**출력**

```ts
// ex.16d.ts
// 함수 타입 표기 세 꼴 + .d.ts 에 오버로드가 어떻게 실리나
export function len(x: string): number;
export function len(x: unknown[]): number;
export function len(x: string | unknown[]): number {
    return x.length;
}

export type ArrowStyle = (x: string) => number;
export interface CallSignature {
    (x: string): number;
    (x: number): string;
}
export interface MethodStyle {
    run(x: string): number;
}
export interface PropertyStyle {
    run: (x: string) => number;
}
export interface Overloaded {
    run(x: string): number;
    run(x: number): string;
}
export const arrow = (x: string): number => x.length;
export const asCallSig: CallSignature = ((x: string | number) =>
    typeof x === "string" ? x.length : String(x)) as CallSignature;

export class Holder {
    run(x: string): number;
    run(x: number): string;
    run(x: string | number): string | number {
        return typeof x === "string" ? x.length : String(x);
    }
}
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.16d.ts (tsc exit=0) =====
===== 방출된 ex.16d.d.ts =====
export declare function len(x: string): number;
export declare function len(x: unknown[]): number;
export type ArrowStyle = (x: string) => number;
export interface CallSignature {
    (x: string): number;
    (x: number): string;
}
export interface MethodStyle {
    run(x: string): number;
}
export interface PropertyStyle {
    run: (x: string) => number;
}
export interface Overloaded {
    run(x: string): number;
    run(x: number): string;
}
export declare const arrow: (x: string) => number;
export declare const asCallSig: CallSignature;
export declare class Holder {
    run(x: string): number;
    run(x: number): string;
}
```

**왜 그런가**

| 소스에 있던 것 | `.d.ts` 에서 |
|---|---|
| `len` 의 오버로드 둘 | ★ **그대로 둘** |
| `len` 의 구현 시그니처 | ★★★ **사라진다** |
| `Holder.run` 의 오버로드 둘 | 그대로 둘 |
| `Holder.run` 의 구현 | ★★★ **사라진다** |
| `type ArrowStyle = (x: string) => number` | 그대로 |
| `interface CallSignature { (x)…; (x)…; }` | 그대로 — **호출 시그니처 둘** |
| `interface MethodStyle { run(x: string): number }` | ★★ **메서드 문법 그대로** |
| `interface PropertyStyle { run: (x: string) => number }` | ★★ **프로퍼티 문법 그대로** |
| `const arrow = (x: string): number => …` | `declare const arrow: (x: string) => number` |
| `const asCallSig: CallSignature = …` | ★ `declare const asCallSig: CallSignature` — **이름 그대로** |

- ★★★ `.d.ts` 는 **「밖에서 보이는 것」의 정본**이다. 구현 시그니처가 없는 것이 1번 24행의 탐침과 **같은 사실**이다 —\
  창이 둘인데 **답이 같다.**
- ★★★ 메서드 문법과 프로퍼티 문법이 **다른 줄로 남는다.** `.d.ts` 는 이 둘을 **합치지 않는다** —\
  같은 뜻이 아니기 때문이다. [**17번 주제**](../17-variance-and-parameter-compatibility/)가 그 차이의 값을 잰다.
- ★★ `asCallSig` 가 `CallSignature` 라는 **이름 그대로** 남는 것이 중요하다.\
  **`.d.ts` 는 타입 별칭을 정규화하지 않는다** — 「적은 것」을 싣지 「계산한 것」을 싣지 않는다.
- ★ 그러므로 `.d.ts` 를 「컴파일러의 최종 판단」으로 읽으면 틀린다. **탐침이 계산된 쪽**이고,\
  **둘이 다르면 그 차이 자체가 정보**다.

### 5. ★★★ 진단 **3건** — 오버로드는 **`string`**, 유니온은 **`string | number`**

**출력**

```ts
// ex.16e.ts
// 오버로드 대 유니온 매개변수 — 무엇이 갈리나. 그리고 세 표기가 서로 대입되나
function overloaded(x: string): string;
function overloaded(x: number): number;
function overloaded(x: string | number): string | number {
    return x;
}
function unioned(x: string | number): string | number {
    return x;
}
const o1: null = overloaded("a");
const u1: null = unioned("a");

interface MethodStyle {
    run(x: string): number;
}
interface PropertyStyle {
    run: (x: string) => number;
}
interface CallSignature {
    (x: string): number;
}
type ArrowStyle = (x: string) => number;

declare const ms: MethodStyle;
declare const ps: PropertyStyle;
const x1: PropertyStyle = ms;
const x2: MethodStyle = ps;
declare const cs: CallSignature;
declare const ar: ArrowStyle;
const x3: ArrowStyle = cs;
const x4: CallSignature = ar;

// 오버로드된 함수를 한 꼴짜리 타입에 담으면
type OneShape = (x: string) => string;
const x5: OneShape = overloaded;
type WrongShape = (x: boolean) => boolean;
const x6: WrongShape = overloaded;
console.log(o1, u1, x1, x2, x3, x4, x5, x6);
```

```text
===== tsc --pretty false --noEmit ex.16e.ts (tsc exit=1) =====
ex.16e.ts(10,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.16e.ts(11,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.16e.ts(37,7): error TS2322: Type '{ (x: string): string; (x: number): number; }' is not assignable to type 'WrongShape'.
  Types of parameters 'x' and 'x' are incompatible.
    Type 'boolean' is not assignable to type 'string'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 10 | `overloaded("a")` | **`string`** |
| 11 | `unioned("a")` | **`string \| number`** |
| 26 / 27 | 메서드 ↔ 프로퍼티 서로 대입 | ★ 둘 다 **조용하다** |
| 30 / 31 | 호출 시그니처 ↔ 화살표 서로 대입 | ★ 둘 다 **조용하다** |
| 35 | 오버로드를 한 꼴짜리 타입에 | 통과 — 첫 오버로드가 만족한다 |
| 37 | 안 맞는 꼴에 | **TS2322** — 다시 `{ (x: string): string; (x: number): number; }` |

- ★★★ 10행과 11행의 차이가 **오버로드를 쓰는 유일한 이유**다. 몸통은 같은 일을 하지만\
  호출한 쪽이 받는 반환 타입이 다르다. **반환이 안 갈리면 오버로드는 값을 내지 않는다.**
- ★★ 26·27·30·31행이 조용한 것은 **모양이 같기 때문**이다. 표기 꼴이 다르다고 다른 타입이 되지는 않는다.\
  ★★★ 다만 **같은 것도 아니다** — 여기서는 매개변수 타입이 같아서 차이가 안 드러났을 뿐이고,\
  [**17번 주제**](../17-variance-and-parameter-compatibility/)가 매개변수를 서로 다르게 두어 그 차이를 끄집어낸다.
- ★ 37행의 에러 문구가 다시 **오버로드 둘짜리 타입**을 보여 준다 — 1번 24행과 같은 사실의 세 번째 얼굴이다.

### 6. ★★★ 오버로드 시그니처는 **0줄** — 그리고 다섯 줄이 전부 **몸통의 판단**이다

**출력**

```ts
// ex.16f.ts
// 방출된 JS 에 오버로드는 한 글자도 안 남는다 — 갈래는 몸통이 직접 판다
function format(x: string): string;
function format(x: number): string;
function format(x: Date): string;
function format(x: string | number | Date): string {
    if (typeof x === "string") return `문자열 ${x}`;
    if (typeof x === "number") return `숫자 ${x.toFixed(1)}`;
    return `날짜 ${x.toISOString().slice(0, 10)}`;
}

class Repo {
    find(id: number): string;
    find(name: string): string;
    find(key: number | string): string {
        return typeof key === "number" ? `#${key}` : `@${key}`;
    }
}

console.log("format('a')  :", format("a"));
console.log("format(1.5)  :", format(1.5));
console.log("format(날짜) :", format(new Date(0)));
const repo = new Repo();
console.log("find(7)      :", repo.find(7));
console.log("find('준')   :", repo.find("준"));
```

```text
===== tsc --pretty false ex.16f.ts (tsc exit=0) =====
===== 방출된 ex.16f.js =====
"use strict";
function format(x) {
    if (typeof x === "string")
        return `문자열 ${x}`;
    if (typeof x === "number")
        return `숫자 ${x.toFixed(1)}`;
    return `날짜 ${x.toISOString().slice(0, 10)}`;
}
class Repo {
    find(key) {
        return typeof key === "number" ? `#${key}` : `@${key}`;
    }
}
console.log("format('a')  :", format("a"));
console.log("format(1.5)  :", format(1.5));
console.log("format(날짜) :", format(new Date(0)));
const repo = new Repo();
console.log("find(7)      :", repo.find(7));
console.log("find('준')   :", repo.find("준"));
```

```text
===== node ex.16f.js (node exit=0) =====
format('a')  : 문자열 a
format(1.5)  : 숫자 1.5
format(날짜) : 날짜 1970-01-01
find(7)      : #7
find('준')   : @준
```

**왜 그런가**

| 소스 | 방출된 `.js` |
|---|---|
| `format` 오버로드 **3줄** | ★★★ **0줄** |
| `format` 구현 | `function format(x) { … }` **하나** |
| `Repo.find` 오버로드 **2줄** | ★★★ **0줄** |
| `Repo.find` 구현 | `find(key) { … }` 하나 |

| 호출 | 출력 |
|---|---|
| `format("a")` | `문자열 a` |
| `format(1.5)` | `숫자 1.5` |
| `format(new Date(0))` | `날짜 1970-01-01` |
| `repo.find(7)` | `#7` |
| `repo.find("준")` | `@준` |

- ★★★ `tsc` 종료 코드가 **`0`** 이고 **진단이 0줄**이다. 그 사실도 배너의 명령과 종료 코드로 캡처했다.
- ★★★ **런타임에 「어느 오버로드」라는 것은 없다.** 갈래는 몸통의 `typeof x === "string"` 이 직접 판다 —\
  [**12번 주제**](../12-narrowing/)의 좁히기가 그 자리에 그대로 있다.
- ★★ 그러므로 **오버로드와 몸통의 갈래가 어긋나도 런타임은 모른다.**\
  구현 시그니처 검사(`TS2394`)는 **타입만** 보지 몸통의 `if` 를 보지 않는다.
- ★ `format(new Date(0))` 이 `날짜 1970-01-01` 인 것은 `toISOString()` 이 UTC 기준이기 때문이다 —\
  타입과 무관한 런타임 사실이다.

### 7. ★★★ **구현 시그니처를 열어 주면 오버로드를 쓰는 이유가 사라지기** 때문이다

**왜 그런가**

- 구현 시그니처는 **모든 오버로드를 감당하려고 억지로 넓힌 꼴**이다 — 1번의 `(x: string | unknown[])` 이 그렇다.
- ★★ 그것을 밖에 열어 주면 **아무 유니온으로나 부를 수 있게** 되고, 반환 타입도 **뭉뚱그려진다.**\
  그러면 5번 10·11행의 차이가 사라진다 — **오버로드가 없는 것과 같아진다.**
- ★★★ 그래서 TS 는 구현 시그니처를 **몸통 검사 전용**으로 둔다. 1번 24행의 탐침과 4번의 `.d.ts` 가\
  **같은 사실을 두 창으로** 보여 준다 — 함수의 타입에도, 선언 파일에도 **구현 시그니처가 없다.**
- ★★ 뒤집으면 **구현 시그니처는 작성자만 보는 것**이다. 넓게 잡아도 소비자에게는 안 새어 나간다 —\
  대신 **몸통 안에서 좁히기를 다 해야** 한다.
- ★ 그 꼴로도 부르고 싶으면 **그 꼴을 오버로드로 하나 더 내걸면** 된다. 감춰진 것이지 막힌 것이 아니다.

### 8. ★★★ **「가장 잘 맞는 것」을 정의하려면 후보 사이의 순서가 필요한데 그것이 모호하기** 때문이다

**왜 그런가**

- 매개변수가 여럿이면 후보 사이에 **부분 순서만** 생긴다 — `(string, number)` 와 `(number, string)` 중\
  어느 쪽이 「더 잘 맞는가」를 일반적으로 정할 수 없다.
- ★★ 그 모호함을 피하려면 규칙이 복잡해지고, 복잡한 규칙은 **작성자가 예측할 수 없게** 된다.
- ★★★ TS 는 그 대신 **가장 단순한 규칙**을 쓴다 — **적은 순서대로 보고 처음 맞는 것에서 멈춘다.**\
  2번의 두 함수가 그 규칙을 그대로 보여 준다.
- ★★ 값은 **예측 가능성**이다. 오버로드 목록을 보면 **어느 것이 골라질지 위에서부터 읽어 알 수 있다.**\
  비용은 **작성자가 순서를 책임져야** 하는 것이다 — **좁은 것부터.**
- ★ 그리고 이 규칙 때문에 **오버로드 추가가 파괴적 변경이 될 수 있다.**\
  앞에 끼워 넣으면 기존 호출의 반환 타입이 **조용히** 바뀐다 — 에러가 아니라 **다른 타입**이 된다.

### 9. ★★ **인자에 따라 반환 타입이 갈리면 오버로드**, 아니면 **유니온 하나**다

**왜 그런가**

| 상황 | 고르는 것 | 근거 |
|---|---|---|
| 인자 타입에 따라 반환이 갈린다 | ★★★ **오버로드** | 5번 10·11행 |
| 인자 **개수**에 따라 의미가 갈린다 | 오버로드 | 2번 24\~26행 |
| 반환이 늘 같다 | ★ **유니온 매개변수 하나** | 5번 11행 |
| 개수만 다르고 의미가 같다 | ★ **선택 매개변수** | 2번 32행 |
| 조합이 많아 순서를 지키기 어렵다 | 조건부 타입 | 목록의 **24번 주제**. **안 던졌다** |

- ★★★ 판단 기준은 하나다 — 「**호출한 쪽이 더 좁은 타입을 받아야 하는가.**」\
  그렇지 않으면 오버로드는 **선언만 길어지고 순서 위험만 늘린다.**
- ★★ 오버로드의 숨은 비용은 **구현 시그니처가 넓어지는 것**이다. 3번의 `covered` 처럼 유니온으로 넓히면\
  몸통 안에서 좁히기를 다시 해야 하고, 그 좁히기가 오버로드와 **어긋나도 아무도 안 잡는다**(6번).
- ★ 공개 API 에서는 오버로드 쪽이 낫다. 소비자가 받는 타입이 정확해지고, `.d.ts` 에 **간판만** 실리므로\
  구현이 얼마나 넓은지도 안 새어 나간다(4번).

### 10. ★★ **`.d.ts` 가 둘을 합치지 않는다는 것**이 곧 「**다른 타입이다**」라는 뜻이다

**왜 그런가**

| | 메서드 문법 `run(x: T): U` | 프로퍼티 문법 `run: (x: T) => U` |
|---|---|---|
| `.d.ts` 에 | ★ **그 꼴 그대로** 실린다(4번) | ★ **그 꼴 그대로** 실린다 |
| 모양이 같을 때 서로 대입 | ★ **된다**(5번 26·27행) | 된다 |
| 매개변수 타입이 다를 때 | ★★★ **bivariant** — 양방향으로 통과한다 | ★★★ **contravariant** — 한 방향만 |
| `strictFunctionTypes` 가 걸리나 | ★★ **안 걸린다** | ★★ **걸린다** |

- ★★★ 5번에서 둘이 조용했던 것은 **매개변수 타입이 같아서** 차이가 드러날 자리가 없었기 때문이다.\
  [**17번 주제**](../17-variance-and-parameter-compatibility/)가 매개변수를 **부모·자식으로 다르게** 두어 그 차이를 끄집어낸다.
- ★★★ 요점은 이것이다 — **`strictFunctionTypes` 를 켜도 메서드 문법은 여전히 bivariant 다.**\
  안전하지 않은 방향의 대입이 **메서드로 적으면 통과**하고 **프로퍼티로 적으면 막힌다.**
- ★★ 그래서 `.d.ts` 가 둘을 구별해 싣는 것은 **형식의 문제가 아니라 의미의 문제**다.\
  선언 파일을 손으로 고칠 때 메서드를 프로퍼티로 바꾸면 **소비자 쪽 검사 결과가 바뀐다.**
- ★ 실무 규칙 — **콜백을 받는 자리는 프로퍼티 문법**으로 적으면 더 엄하게 검사된다.

### 11. ★★ **03 이 표기를 세우고, 16 이 갈래를 내고, 13·17 이 그 위에 얹힌다**

**왜 그런가**

| 주제 | 이 주제와의 관계 |
|---|---|
| [**03번 주제**](../03-basic-type-annotations/) | 함수 타입 표기의 **기본형**. 여기서 **세 꼴**로 갈라진다 |
| 이 주제 | 화살표 꼴 · 호출 시그니처 · 메서드 문법 + **오버로드** |
| [**13번 주제**](../13-type-guards-and-predicates/) | 반환 타입 자리에 **`x is T`** 를 적는 것 — 같은 자리의 다른 쓰임 |
| [**14번 주제**](../14-assertion-signatures/) | 반환 타입 자리에 **`asserts x is T`** — 반환 타입이 `void` 여야 한다 |
| [**17번 주제**](../17-variance-and-parameter-compatibility/) | 세 꼴이 **대입 가능성에서 갈리는** 지점 |

- ★★★ 반환 타입 자리 하나에 **네 가지**가 온다 — 보통 타입(`number`) · 술어(`x is T`) ·\
  단언(`asserts x is T`) · 그리고 **오버로드로 여러 개**. 16 은 그중 **마지막 축**이다.
- ★★ 호출 시그니처(`interface F { (x): U }`)가 화살표 꼴과 갈리는 자리는 **프로퍼티를 같이 가질 때**다.\
  함수이면서 `F.cache` 같은 필드를 갖는 모양은 화살표 꼴로 못 쓴다([**08번 주제**](../08-interface-vs-type/)).
- ★ 그리고 이 셋 전부가 **방출에 한 글자도 안 남는다**(6번) — [**01번 주제**](../01-what-ts-adds-and-erases/)·[**02번 주제**](../02-type-checking-vs-emit/)의 결론 그대로다.

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 구현 시그니처로는 **호출할 수 없다**(`TS2769`) · 해석 순서는 **선언 순서** · 구현이 **모든 오버로드**를 매개변수와 반환 양쪽에서 덮어야 한다(`TS2394`) · 오버로드 묶음은 **연속**이어야 한다(`TS2391`) · `.d.ts` 에는 **오버로드만** 실린다 · 방출된 JS 에는 **한 글자도 안 남는다** |
| **설정에 달린 것** | ★ **없다.** 네 파일 전부 `--strict false` 와 **글자 하나까지 같다**(7절). 이 갈래에서 드문 일이라 대조를 블록으로 남겼다 |
| **이 판(7.0.2)의 관찰** | 진단 문구 전문 — 코드가 더 오래 간다 · ★ `TS2769` 가 **마지막 오버로드의 에러만** 보여 주는 요약 방식 · `.d.ts` 의 들여쓰기 4칸과 줄 순서 · 탐침이 뱉는 타입 글자의 **공백·세미콜론 배치** |

- ★★★ 「**진단 0줄」이 결론인 블록이 둘**이다(4·6번). 그 블록도 **명령과 종료 코드까지** 캡처해야 근거가 된다.
- ★★ 이 주제의 **창 셋이 같은 답을 준다** — 탐침(계산된 것) · `.d.ts`(적은 것) · 방출 `.js`(사실).\
  셋이 일치하는 것 자체가 「구현 시그니처는 밖에 없다」의 **세 겹 증거**다.
- ★ **설정에 달린 칸이 0개**인 것은 이 갈래에서 드물다. 그래서 7절의 대조를 **빼지 않고 실었다.**

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 구현 시그니처의 가시성 | `--noEmit ex.16a.ts` | exit 1 · **4건** · 13행 `TS2769` · ★ 24행이 **시그니처 둘짜리 타입** |
| 해석 순서 | `--noEmit ex.16b.ts` | exit 1 · **6건** · 12행 `"넓은 쪽"` · 13행 `"좁은 쪽"` |
| 구현이 덮어야 하는 것 | `--noEmit ex.16c.ts` | exit 1 · **3건** · `TS2394` **2**(매개변수·반환) · `TS2391` **1** |
| `.d.ts` 방출 | `--declaration --emitDeclarationOnly ex.16d.ts` | ★ **exit 0** · 구현 시그니처 **없음** · 메서드/프로퍼티 **구별 유지** |
| 오버로드 대 유니온 | `--noEmit ex.16e.ts` | exit 1 · **3건** · 10행 `string` · 11행 `string \| number` |
| 방출과 실행 | `tsc ex.16f.ts` + `node ex.16f.js` | ★ **tsc exit 0 · 진단 0줄** · node exit 0 · 오버로드 **0줄** |
| `strict` 대조 | 네 파일을 `--strict false` 로 재실행 | ★★ **전부 글자 하나까지 같다** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ `TS2769` 가 **마지막 오버로드의 에러만** 인용하는 요약 방식 — 7.0.2 의 보고기 구현이다.
- ★★ 탐침이 뱉는 타입 글자의 **공백과 세미콜론 배치**(`{ (x: string): number; (x: unknown[]): number; }`).
- `.d.ts` 의 들여쓰기 4칸·줄 순서 — 방출기의 형식이다.
- `TS2394`·`TS2391` 의 문구 전문 — 코드가 더 오래 간다.
- `format(new Date(0))` 의 `1970-01-01` — `toISOString()` 이 UTC 기준인 런타임 사실이다.

**안 돌려 본 것**

- **오버로드와 술어·단언의 조합**(`function f(x: string): x is "a";`) — **안 던졌다.**
- **제네릭 오버로드** — 타입 매개변수가 붙은 오버로드는 **안 던졌다.** 목록의 **19번 주제**.
- **조건부 타입으로 같은 일을 하는 판** — 목록의 **24번 주제**. **안 던졌다.**
- **`this` 매개변수가 붙은 시그니처** — 목록의 **18번 주제**. **안 던졌다.**
- **오버로드가 많을 때의 검사 시간** — **재지 않았고 수치를 적지 않았다.**
