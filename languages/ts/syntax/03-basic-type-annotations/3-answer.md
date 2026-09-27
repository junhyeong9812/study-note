# ts/syntax/03 — 기본 타입 표기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·`.d.ts` 전문·방출 전문은 `tsc` **7.0.2** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★ **옵션이 결과를 바꾸는 주제다.** 배너에 적힌 옵션이 곧 그 블록의 전제다 — `strict` 는 이 판에서 **기본 `true`** 다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `const` 는 `= 42`, `let` 은 `: number` — **모양 자체가 다르다**

**출력**

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

**왜 그런가**

- ★★★ `const n = 42` → `export declare const n = 42;` 다. **리터럴 타입 `42`** 로 굳었다.\
  `let m = 42` → `export declare let m: number;` 다. **넓혀졌다.**
- 이유는 **다시 대입될 수 있느냐**다. `let` 은 나중에 `m = 7` 이 될 수 있으므로 `number` 여야 한다.
- 같은 갈림이 문자열에도 있다 — `s` 는 `= "circle"`, `t` 는 `: string`.
- `b = true` 는 `= true`, `big = 10n` 은 `= 10n` 으로 굳었다.
- ★ `sym` 은 **`: unique symbol`** 이다 — 그 심볼 하나만 가리키는 특수 타입이라 `= …` 꼴로 못 적는다.
- `nul: null` 과 `und: undefined` 가 **따로** 있다 — `strictNullChecks` 가 켜져 있기 때문이다.
- `annotated: number = 42` 는 **표기가 이겨서** `: number` 다. 표기를 적으면 굳지 않는다.

### 2. ★★ 에러 **0건** · `.d.ts` 는 **적은 표기를 보존한다** · `union1` 과 `union2` 는 **다른 타입**

**출력**

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

**왜 그런가**

- `number[]` → `Array<number>` → `number[]` 로 두 번 오갔는데 **에러가 0건**이다. 두 표기는 **같은 타입**이다.
- ★ 그런데 `.d.ts` 는 `b: Array<number>`, `ro2: ReadonlyArray<number>` 로 **적은 대로** 되돌려 준다 — 표기가 보존된다.
- `union1: (string | number)[]` 은 「**원소마다** 문자열이거나 숫자인 한 배열」이다.
- `union2: string[] | number[]` 은 「**통째로** 문자열 배열이거나 숫자 배열」이다. `[1, "a"]` 는 여기 못 들어간다.
- ★ `readonly` 는 `T[]` 꼴에만 붙는다 — `readonly Array<number>` 라는 표기는 없다.

### 3. ★★★ 코드는 다섯 — `TS2339` · `TS2542` · `TS4104` · `TS2540` · `TS2322`

**출력**

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

**왜 그런가**

| 줄 | 무엇을 했나 | 코드 | 왜 |
|---|---|---|---|
| `ro.push(4)` | readonly 배열에 `push` | **TS2339** | `readonly number[]` 에는 `push` 라는 **멤버가 아예 없다** |
| `ro[0] = 9` | readonly 배열에 인덱스 대입 | **TS2542** | 배열의 인덱스는 **인덱스 시그니처**라 「읽기만 허용」이라고 말한다 |
| `const mutable: number[] = ro` | readonly → 가변 | **TS4104** | 방향이 막혀 있다. ★ **반대 방향은 된다** |
| `rt[0] = "b"` | readonly 튜플에 인덱스 대입 | **TS2540** | 튜플의 칸은 **이름 있는 프로퍼티**(`0`·`1`)라 「읽기 전용 프로퍼티」라고 말한다 |
| `tooMany` · `tooFew` | 튜플 길이 불일치 | **TS2322** | 둘째 줄 문구가 갈린다 — 「allows only 2」와 「requires 2」 |

- ★★ 배열과 튜플이 **다른 코드**인 이유는 **모델이 다르기 때문**이다 — 배열의 칸은 인덱스 시그니처, 튜플의 칸은 고정된 프로퍼티다.
- ★ 「readonly 에러」를 한 덩어리로 외우면 고치는 법을 못 고른다. 다섯은 각각 처방이 다르다.

### 4. ★★ `opt1`·`rest1` **둘 다 통과** · 에러 **0건** · 이름표는 `.d.ts` 에 **살아남는다**

**출력**

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

**왜 그런가**

- `Opt = [string, number?]` 라서 `["a"]` 와 `["a", 1]` 이 **둘 다** 맞다.
- `Rest = [string, ...number[]]` 라서 `["a"]` 와 `["a",1,2,3]` 이 **둘 다** 맞다 — 나머지는 0개여도 된다.
- 에러가 0건이고 종료 코드가 `0` 이다.
- ★ `.d.ts` 의 `export type Named = [first: string, second: number];` 에 **이름표가 그대로** 남았다.\
  이름표는 타입을 안 바꾸고 **읽기와 도구 힌트**만 돕는다.
- ★ `function sum(...xs: [string, ...number[]]): string` 처럼 **나머지 매개변수를 튜플로** 적을 수 있다 — 가변 인자의 칸별 타입을 고정하는 법이다.

### 5. ★★★ `number[]` → `readonly [1, 2, 3]` — **세 가지가 한꺼번에** 바뀌고 **안쪽까지** 간다

**출력**

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

**왜 그런가**

- `plainArr` 는 `number[]`, `constArr` 는 **`readonly [1, 2, 3]`** 이다. 바뀐 것이 셋이다.

```text
  [1, 2, 3]                        [1, 2, 3] as const
  number[]                         readonly [1, 2, 3]
  ├ 길이 모름                       ├ 길이 3 고정   ← ① 배열이 튜플이 됐다
  ├ 원소 타입 number                ├ 원소 1 · 2 · 3 ← ② 리터럴로 굳었다
  └ push 가능                       └ push 없음     ← ③ readonly 가 붙었다
```

- `plainObj` 는 `{ kind: string; r: number }`, `constObj` 는 `{ readonly kind: "circle"; readonly r: 1 }` 이다.
- ★ `nested` 가 `{ readonly a: { readonly b: readonly [1, "x"] } }` 다 — **재귀적으로** 들어간다.
- `litConst = "circle"` 은 `as const` 없이도 `= "circle"` 이다. **`const` 선언 자체가 이미 굳힌다** — `as const` 가 필요한 것은 **객체·배열의 속**이다.
- ★★ 방출에서 `as const` 는 사라진다. **런타임 객체가 어는 게 아니다**(`Object.freeze` 가 아니다).

### 6. ★★★ 다섯 타입이 문구에 그대로 나온다 — 단 **`never`·`any` 는 못 잡는다**

**출력**

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

**왜 그런가**

- 진단 문구가 타입을 그대로 말한다 — `number[]` · `readonly [1, 2, 3]` · `{ kind: string; r: number; }` · `{ readonly kind: "circle"; readonly r: 1; }` · `(x: number) => string`.
- ★ 5번의 `.d.ts` 와 **같은 답**이다. 두 창이 서로를 검증한다.
- ★★ **못 잡는 타입이 있다** — `never` 는 **모든 타입에 대입되므로** `null` 에도 들어가 **에러가 안 난다**.\
  `any` 도 마찬가지다. 그때는 방향을 뒤집어 `const x: never = v` 로 묻는다([**04번 주제**](../04-any-unknown-never-void/)의 완전성 검사가 그 형태다).
- ★ `.d.ts` 쪽 한계는 **`export` 된 것만** 나온다는 것이다. 지역 변수는 탐침이 낫다.

| | `.d.ts` 덤프 | `null` 탐침 |
|---|---|---|
| 대상 | `export` 된 것만 | **아무 표현식이나** |
| 형식 | 선언 전문 · 여러 줄 | 한 줄 문구 |
| 한계 | 지역 변수를 못 본다 | ★ `never`·`any` 는 **통과해 버린다** |
| 부작용 | 파일이 생긴다 | 종료 코드 1 |

### 7. ★★★ 진단 **3건** · 에러가 나는 쪽은 **`export const exported = []`** · `--strict false` 면 **1건**

**출력**

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

```text
===== tsc --pretty false --noEmit --strict false ex.03h.ts (tsc exit=1) =====
ex.03h.ts(6,10): error TS2339: Property 'click' does not exist on type '{}'.
```

**왜 그런가**

- `function twice(n)` → **`TS7006`**. ★ **매개변수는 추론할 곳이 없다.** 여기가 표기 의무 자리다.
- `handlers.click = 1` → **`TS2339`**. `const handlers = {}` 가 `{}` 로 굳어 프로퍼티가 하나도 없다.
- ★★★ `const evolving = []` 은 **에러가 안 난다.** `push(1)` 과 `push("a")` 가 둘 다 통과했다 — **진화하는 `any[]`** 다.
- ★★★ 그런데 `export const exported = []` 뒤의 `exported.push(1)` 은 **`TS2345` — `never`** 다.\
  `export` 가 붙으면 **선언 파일에 적어야 하므로** 그 자리에서 타입을 확정해야 하고, 그래서 진화가 꺼져 `never[]` 가 된다.
- `--strict false` 로 내리면 `TS7006` 과 `never` 진단이 **사라지고 `TS2339` 만 남는다** — 앞의 둘은 `noImplicitAny` 계열에 딸려 있고, 뒤는 **strict 와 무관한 구조 검사**이기 때문이다.
- ★★ 그래서 이 절의 답은 **설정 없이는 성립하지 않는다.** 배너를 같이 읽어야 한다.

### 8. ★★ 적는 자리 셋 · 맡기는 자리 둘

**왜 그런가**

| 반드시 적는다 | 왜 |
|---|---|
| ★ **함수 매개변수** | 추론할 근거가 없다. `strict` 아래에서 `TS7006` 이다 |
| ★ **모듈 경계(`export`)의 반환 타입** | 계약을 못 박고, 선언 방출이 안쪽 구현에 끌려다니지 않는다 |
| **빈 배열·빈 객체로 시작하는 변수** | 7번이 그 반례다 — `[]` 는 `never[]` 가 되기도 하고 `any[]` 가 되기도 한다 |

| 맡긴다 | 왜 |
|---|---|
| 지역 변수 초기화 | `const n: number = 42` 의 `: number` 는 군더더기다. 게다가 **리터럴 고정을 없앤다** |
| 콜백 매개변수 | 문맥적 타이핑이 채운다 — `ids.forEach((n) => …)` 의 `n` 은 적을 필요가 없다 |

- ★ 역설 하나 — **리터럴로 굳히고 싶으면 표기를 빼야 한다.** `const kind: string = "circle"` 은 `string` 으로 넓어지고, `const kind = "circle"` 은 `"circle"` 로 굳는다.

### 9. ★★★ 못 바꾼다는 보장이 없다 — **방출에서 사라지기 때문**이다

**왜 그런가**

- [**01번 주제**](../01-what-ts-adds-and-erases/)에서 본 대로 **타입 표기는 방출에서 한 글자도 안 남는다.** `readonly` 도 표기다.
- 그러니 `readonly number[]` 로 선언한 배열도 **런타임에는 그냥 배열**이다. `(ro as number[]).push(4)` 한 줄이면 들어간다.
- ★ `readonly` 가 막는 것은 **이 코드베이스 안에서의 실수**다 — 세 가지 진단(`TS2339`·`TS2542`·`TS2540`)과 대입 방향(`TS4104`).
- ★★ 진짜 런타임 불변이 필요하면 **`Object.freeze`** 다. 그건 JS 쪽 장치이고 `../../js/syntax/README.md` 의 **14번 주제**가 정본이다.
- 같은 이야기가 `as const` 에도 그대로 간다 — 타입만 바뀌고 객체는 안 언다.

### 10. ★★ 두 창의 대상·형식·한계

**왜 그런가**

- 6번의 표가 그 답이다. 요점은 셋이다.
- ★ **`.d.ts` 는 「모듈이 밖에 약속하는 것」을 보여 준다** — 그래서 지역 변수가 안 나오고, 대신 **계약이 의도대로 잡혔나**를 검토하기에 좋다.
- ★ **`null` 탐침은 「지금 이 표현식」을 보여 준다** — 지역 변수·중간 결과·좁혀진 타입에 쓴다.
- ★★ **둘 다 못 보는 것이 있다** — `never`·`any` 는 탐침을 통과하고, 지역 변수는 `.d.ts` 에 없다. 그럴 때는 **방향을 뒤집어** `const x: never = v` 처럼 묻는다.
- ★ 두 창이 **같은 답을 내는지 대조하는 것** 자체가 검증이다. 이 주제에서 5번과 6번이 그렇게 맞물린다.

### 11. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | `T[]` 와 `Array<T>` 는 같은 타입 · `const` 는 굳고 `let` 은 넓혀진다 · `as const` 는 **리터럴 고정 + 튜플화 + `readonly`** 를 재귀 적용한다 · `readonly` 는 **검사 시각에만** 막는다 |
| **설정에 달린 것** | `TS7006`(암시적 `any`) · `export const exported = []` 의 `never` — **둘 다 `--strict false` 면 사라진다** · `noUncheckedIndexedAccess` 를 켜면 `arr[0]` 의 타입부터 달라진다 |
| **이 판(7.0.2)의 관찰** | `.d.ts` 가 `Array<number>`·`ReadonlyArray<number>` 표기를 **보존**하는 것 · 진단 문구의 정확한 글자 · 지역 `const evolving = []` 이 **진화하는 `any[]`** 인 것 · `Symbol("k")` 가 `unique symbol` 로 잡히는 것 |

- ★ **에러 코드가 문구보다 오래 간다.** 인용할 때 코드를 먼저 적는 이유다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 원시 추론 | `--declaration --emitDeclarationOnly ex.03a.ts` | exit 0 · `.d.ts` 10줄 · `const n = 42` 대 `let m: number` |
| 배열 두 표기 | `--declaration --emitDeclarationOnly ex.03b.ts` | exit 0 · **에러 0건** · 표기 보존 |
| `readonly` | `--noEmit ex.03c.ts` | exit 1 · `TS2339`·`TS2542`·`TS4104`·`TS2540`·`TS2322` **6건** |
| 튜플 네 모양 | `--declaration --emitDeclarationOnly ex.03d.ts` | exit 0 · **에러 0건** · 이름표 보존 |
| 객체·함수 타입 | `--declaration --emitDeclarationOnly ex.03e.ts` · `--module esnext ex.03e.ts` | exit 0 · 선택·`readonly` 보존 · 방출에 표기 없음 |
| `as const` | `--declaration --emitDeclarationOnly ex.03f.ts` | exit 0 · `readonly [1, 2, 3]` · 중첩까지 `readonly` |
| `null` 탐침 | `--noEmit ex.03g.ts` | exit 1 · **5건** · 문구에 타입 5개 |
| 표기 누락 | `--noEmit ex.03h.ts` | exit 1 · **3건**(`TS7006`·`TS2339`·`TS2345`) |
| 같은 파일 비엄격 | `--noEmit --strict false ex.03h.ts` | exit 1 · **1건**(`TS2339`만) |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- `.d.ts` 가 `Array<T>`·`ReadonlyArray<T>` 표기를 보존하는 것 — 선언 방출기의 구현이다.
- 진단 문구의 정확한 글자 — 코드(`TS2542` 등)가 더 오래 간다.
- 지역 `const evolving = []` 의 진화 추론 범위.
- `strict` 기본값이 `true` 라는 것 — **7.0 에서 바뀐 것**이다. 6.x 이하에서 이 문서를 재현하려면 `--strict` 를 명시해야 한다.

**안 돌려 본 것**

- `noUncheckedIndexedAccess`·`exactOptionalPropertyTypes` 를 켠 판 — `tsc --init` 이 그 둘을 권하는 것은 확인했지만(이 판), 이 주제의 블록은 전부 **명령줄로 파일을 직접 준 기본 설정**이다. 그 플래그의 효과는 [목록의 **41번 주제**](../41-index-and-optional-property-strict-flags/)에서 던진다.
