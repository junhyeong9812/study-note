# ts/syntax/09 — 유니온 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Everyday Types: Union Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#union-types) ·
> [Handbook — Narrowing: Discriminated Unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions) ·
> [Handbook — Narrowing: Exhaustiveness checking](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking) ·
> [TSConfig — `strictNullChecks`](https://www.typescriptlang.org/tsconfig/#strictNullChecks).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·`.d.ts` 전문·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`) — 그 안의 `strictNullChecks` 때문에 `null`·`undefined` 가 **유니온 멤버로 분리**돼 보인다.
> `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로 이 블록들은 설정 파일 없이도 그대로 재현된다.
> **버전** — 유니온은 TS 1.4, 판별 유니온은 2.0, `never` 를 쓴 전수 검사는 2.0 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·**`.d.ts` 전문**·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★ 진단이 **정규화해서 찍어 주는 유니온의 멤버 순서** | 이 판에서 재실행해도 같았다. 다만 **보장이 아니라 관찰**이다(아래 표) |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 이 주제는 진단 문구에 `|` 가 많이 나온다. 표 안에서는 `\|` 로 이스케이프했다 — **본문의 뜻은 `|` 다.**

## 한눈에 — 쉽게 말하면

**유니온은 「둘 중 하나」가 아니라 「둘 다일 수 있는 상태」다.**

| 비유 | 실체 |
|---|---|
| 상자에 「신발 **또는** 모자」라고 적혀 있다 | **유니온 `A \| B`** — 열기 전에는 어느 쪽인지 모른다 |
| 열기 전에 할 수 있는 일은 **둘 다에 되는 것**뿐 | **공통 멤버만** 쓸 수 있다 — 아니면 `TS2339` |
| 라벨에 「신발 3켤레」를 덧붙여 둔다 | **판별 필드** — `kind: "circle"` 처럼 갈라 주는 칸 |
| 라벨을 읽으면 그때부터 한 종류로 다룬다 | **좁히기** — 분기 안에서 멤버 하나로 줄어든다 |
| ★ 라벨을 다 읽고 나면 남는 게 **없어야** 한다 | **`never` 전수 검사** — 빠뜨린 종류를 이름으로 짚어 준다 |
| 라벨은 **상자에만** 붙어 있고 내용물에는 없다 | 유니온은 **방출에 한 글자도 안 남는다** — `typeof` 로 다시 물어야 한다 |

- ★★★ 한 줄로 — 「**유니온은 좁히기 전에는 교집합만 쓸 수 있고, 좁히는 일은 런타임 연산자가 한다.**」
- ★★ 그리고 **적은 대로 남지 않는다** — 중복·`never`·리터럴·중첩이 **정규화**된다. 그 결과를 컴파일러에게 캐물어 전수로 실었다.

```text
  string | number
        │
        ├── .toString()  둘 다 있다      -> 통과
        ├── .toFixed()   string 에 없다  -> TS2339
        │                                    "Property 'toFixed' does not exist on type 'string'."
        └── typeof v === "string" 으로 갈라야 각각을 쓸 수 있다
                 │
                 ▼  이 갈라 주는 일은 **JS 연산자**가 한다
```

```text
  적은 대로 남지 않는다 — 정규화

  string | number | string        ->  string | number      (중복 제거)
  string | never | number         ->  string | number      (never 흡수)
  "x" | "y" | string              ->  string               (리터럴 흡수)
  true | false                    ->  boolean              (합쳐진다)
  (string|number)|(number|boolean)->  string | number | boolean  (평탄화)
  number | string                 ->  string | number      ★ 순서가 바뀐다
  3 | 1 | 2                       ->  1 | 2 | 3            ★ 순서가 바뀐다
  string | any                    ->  any                  (any 가 먹는다)
  string | unknown                ->  unknown              (unknown 이 먹는다)
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **좁히기 전에 무엇을 쓸 수 있나** — 「공통 멤버만」이 정확히 무슨 뜻이고, 진단이 **어느 멤버를 짚어 주나**.
2. **적은 대로 남나** — 중복·`never`·리터럴·중첩·순서가 어떻게 되는지 **컴파일러에게 캐물어** 확인한다.
3. **갈라 쓰는 일은 누가 하나** — 판별 필드와 전수 검사, 그리고 **방출된 JS 에 무엇이 남나**.

★ [**04번 주제**](../04-any-unknown-never-void/)가 「위아래 끝의 네 타입」을 세웠다면, 여기는 **그 사이의 타입을 이어 붙이는 연산**을 본다. `never` 와 `any` 가 유니온에서 어떻게 구는지가 두 주제를 잇는다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`null` 탐침** | **정규화된 유니온**을 컴파일러가 글자로 적어 준다 | [**03번 주제**](../03-basic-type-annotations/)에서 이어받음 |
| ★★ **진단의 들여쓴 줄** | 「**어느 멤버**에 그 프로퍼티가 없나」 | ★ 이 주제의 고유 창 |
| ★★ **`.d.ts` 덤프** | 선언 방출은 **정규화를 안 한다** — 탐침과 대비된다 | ★ 이 주제의 고유 창 |
| ★★★ **방출된 `.js` + `node`** | 유니온이 **한 글자도 안 남는 것** | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |

★ **첫째와 셋째가 서로 다른 답을 준다는 것**이 이 주제의 값이다. 「적은 것」과 「계산된 것」이 다르다.

비용 — 컴파일 한 번.

### (1) ★★★ 좁히기 전에는 공통 멤버만

**언제 쓰나** — 「분명히 있는 메서드인데 왜 없다고 하지」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 건**이다 — 6·7·20·24행. **5행과 19행은 통과했다.**
- 5행 `v.toString()` 은 통과한다 — `string` 에도 `number` 에도 있다.
- ★★ 6행 `v.toFixed(2)` 가 `TS2339` 인데, **들여쓴 줄이 누구 탓인지 짚어 준다** — 「Property 'toFixed' does not exist on type 'string'.」
- 7행 `v.length` 도 같다. 이번에는 들여쓴 줄이 **`number`** 를 짚는다 — **범인이 반대쪽**이다.
- 19행 `pet.name` 은 통과했다 — `Bird` 와 `Fish` 둘 다 갖고 있다.
- 20행 `pet.fly()` 가 `TS2339` 이고 들여쓴 줄이 **`Fish`** 를 짚는다.
- ★ 22·23행은 통과하고 24행 `const putBoolean: SN = true` 만 `TS2322` 다 — **넣는 방향은** 「**멤버 중 하나면 된다**」로 느슨하다.

```text
  꺼내 쓰는 방향 (좁다)                    넣는 방향 (넓다)
  ┌────────────────────────────┐          ┌────────────────────────────┐
  │ string | number 에서       │          │ string | number 자리에     │
  │   쓸 수 있는 것 =          │          │   넣을 수 있는 것 =        │
  │   **둘 다 가진 멤버**      │          │   **둘 중 하나면 된다**    │
  │   (교집합)                 │          │   (합집합)                 │
  └────────────────────────────┘          └────────────────────────────┘
```

> **유니온 타입(union type)** — `A | B` 처럼 「이 값은 이것들 중 하나」를 적는 타입.\
> 예: `string | number`. 좁히기 전에는 **양쪽에 다 있는 멤버만** 쓸 수 있다.

비용 — 없음. 다만 **쓰는 자리마다 좁혀야** 한다 — 그것이 다음다음 절의 판별 필드다.

### (2) ★★★ 적은 대로 남지 않는다 — 정규화를 캐묻는다

**언제 쓰나** — 「내가 적은 유니온이 실제로 무엇이 됐나」가 궁금할 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **아홉 건**인데 탐침은 **열 개**다. ★★★ **20행(`withAny`)만 진단이 없다** — `string | any` 가 **`any`** 가 되어 `null` 에 그냥 들어갔다.
- 13·14행 — `string | number | string` 과 `string | never | number` 가 **둘 다 `string | number`** 다. **중복과 `never` 가 사라진다.**
- ★★ 15행 — `"x" | "y" | string` 이 그냥 **`string`** 이다. **리터럴이 자기 기반 타입에 흡수된다.**
- 16행 — `true | false` 가 **`boolean`** 이다.
- ★★★ 17행 — `number | string` 이라고 적었는데 진단은 **`string | number`** 라고 답한다. **순서가 바뀐다.**
- 18행 — `(string | number) | (number | boolean)` 이 **`string | number | boolean`** 이다. **평탄화 + 중복 제거.**
- 19행 — `string | undefined | null` 이 **`string | null | undefined`** 다. 역시 순서가 조정됐다.
- 21행 — `string | unknown` 이 **`unknown`** 이다.
- ★★ 22행 — `3 | 1 | 2` 가 **`1 | 2 | 3`** 이다. 리터럴도 정렬된다.

> **정규화(normalization)** — 유니온을 만들 때 컴파일러가 **평탄화·중복 제거·흡수**를 해서 내부 표현을 정리하는 것.\
> 예: `(string \| number) \| (number \| boolean)` 이 `string \| number \| boolean` 이 된다.

- ★★★ **순서가 바뀌는 것은 「보장」이 아니라 「이 판의 관찰」이다.** 내부 타입 식별자 순으로 정리된 결과이고,\
  판이 바뀌면 달라질 수 있다. **대조할 것은 순서가 아니라 「같은 집합으로 정리된다」는 성질**이다.

★★ 이 격자 중 **설정에 달린 칸이 하나** 있다. 같은 파일을 `--strictNullChecks false` 로 다시 던졌다.

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

- ★★★ **19행만 답이 바뀐다** — `string | undefined | null` 이 `string | null | undefined` 가 아니라 그냥 **`string`** 이다.\
  `strictNullChecks` 를 끄면 `null`·`undefined` 가 **다른 타입에 흡수**되기 때문이다([**04번 주제**](../04-any-unknown-never-void/)).
- ★ 나머지 여덟 줄은 **글자 하나까지 같다.** 중복 제거·리터럴 흡수·평탄화·정렬은 그 플래그와 무관하다.

비용 — 없음. 다만 **에러 메시지가 내가 적은 것과 다르게 보인다** — 그 사실을 알고 읽어야 한다.

### (3) ★★ 선언 방출은 정규화를 안 한다

**언제 쓰나** — 2절의 결과를 「그럼 `.d.ts` 도 그렇겠지」로 넘기기 전에.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ `.d.ts` 가 **적은 그대로** 돌려준다 — `string | number | string` 도, `string | never | number` 도, `3 | 1 | 2` 도 손대지 않았다.
- ★★ 2절의 탐침과 **정반대 답**이다. 같은 선언인데 **창에 따라 다르게 보인다.**
- ★ 왜 갈리나 — 선언 방출은 **소스에 적힌 타입 표기를 그대로 옮기는** 일이고, 탐침은 **계산된 타입을 문자열로 찍는** 일이다.
- ★ 값 쪽은 다르다 — `export const fromLiteral = "circle"` 이 **`= "circle"`**, `export let widened = "circle"` 이 **`: string`** 이다([**03번 주제**](../03-basic-type-annotations/)).
- ★ `export const picked: "a" | "b"` 는 표기를 적었으니 그대로 보존된다.

```text
  같은 선언, 두 창이 다른 답을 준다

  type Dup = string | number | string
        │
        ├── .d.ts 덤프   ->  string | number | string   (적은 그대로)
        └── null 탐침    ->  string | number            (계산된 것)

  ★ 「무엇을 적었나」와 「무엇이 됐나」를 가르는 자리다.
```

비용 — 없음. 두 창을 **같이** 써야 답이 온전해진다.

### (4) ★★★ 함수와 배열의 유니온 — 매개변수가 `never` 가 된다

**언제 쓰나** — 「핸들러 유니온을 만들었는데 아무것도 못 넣는다」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 건**이다 — 4·5·8·14행.
- ★★★ `h("s")` 와 `h(1)` 이 **둘 다** `TS2345` 다. 문구가 「not assignable to parameter of type **`never`**」다.
- ★★ 왜 그런가 — `h` 는 「`string` 을 받는 함수」이거나 「`number` 를 받는 함수」다. **어느 쪽인지 모르므로**\
  둘 다에게 안전한 인자만 받아야 한다 — 그 교집합이 `string & number` 라 **`never`** 다.
- 8행 `arr.push("s")` 도 같다. `string[] | number[]` 의 `push` 매개변수가 `never` 다.
- ★ 9·10행은 통과했다 — `arr.map((x) => x)` 와 `arr.length` 는 **꺼내는 쪽**이라 문제가 없다.
- ★ 14행 탐침이 반환 쪽을 확인한다 — `(() => string) | (() => number)` 를 호출한 결과는 **`string | number`** 다.\
  **매개변수는 교집합, 반환은 합집합**이다.

```text
  ((a: string) => void) | ((a: number) => void)
                  │
                  ▼  어느 쪽인지 모르니 둘 다에게 안전해야 한다
          매개변수:  string & number  =  never     ← 아무것도 못 넣는다
          반환:      void | void      =  void

  (() => string) | (() => number)
          반환:      string | number                ← 둘 중 하나가 나온다
```

비용 — **유니온은 핸들러를 담는 그릇으로는 나쁘다.** 오버로드나 판별 유니온이 낫다.

### (5) ★★★ 판별 필드와 전수 검사

**언제 쓰나** — 종류가 여럿인 데이터를 다룰 때. **이 절이 유니온의 본 용도다.**

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **두 건**이다 — 24행과 45행. **나머지는 전부 통과했다.**
- `case "circle"` 안에서 `s.r` 이 통과한다 — 판별 필드 `kind` 가 멤버를 **하나로 좁혔다.**
- ★★★ 24행 `const exhaustive: never = s` 가 `TS2322` — 「Type **'Tri'** is not assignable to type 'never'.」\
  **빠뜨린 종류를 이름으로 짚어 준다.** 케이스를 다 적었다면 `s` 는 `never` 가 되어 이 줄이 통과한다.
- ★★ `if (r.ok)` 도 판별이다 — **불리언 리터럴**(`true`/`false`)이 판별 필드가 되어 `r.data` 와 `r.reason` 이 각 갈래에서 통과한다.
- 45행 `readBad` 는 좁히지 않고 `r.data` 를 읽어 `TS2339` 다. 들여쓴 줄이 **`Err`** 를 짚는다.
- ★ 즉 **전수 검사는 「타입을 `never` 자리에 넣어 본다」는 수법**이다 — [**04번 주제**](../04-any-unknown-never-void/)의 `never` 를 도구로 쓴 것이다.

```text
  switch (s.kind) {
    case "circle": ─▶  s 가 Circle 로 좁혀진다   -> s.r 통과
    case "square": ─▶  s 가 Square 로 좁혀진다   -> s.side 통과
    default:       ─▶  남은 것 = Tri
                       const exhaustive: never = s
                              ▼
                       TS2322  Type 'Tri' is not assignable to type 'never'.
                                      ↑ 빠뜨린 종류를 **이름으로** 알려 준다
  }
```

> **판별 유니온(discriminated union)** — 멤버마다 **리터럴 타입인 공통 칸**을 둬서 그 값으로 종류를 가르게 만든 유니온.\
> 예: `kind: "circle"` · `ok: true`. 그 칸을 읽는 것만으로 좁히기가 된다.

> **전수 검사(exhaustiveness checking)** — 모든 갈래를 처리했는지 컴파일러에게 확인시키는 수법.\
> 예: `const exhaustive: never = s;` — 남은 멤버가 있으면 그 이름이 진단에 나온다.

비용 — 멤버마다 판별 칸을 **하나 더** 들고 다녀야 한다. 대신 종류가 늘 때 **안 고친 자리를 컴파일러가 세어 준다.**

### (6) ★★★ 유니온은 방출에 한 글자도 안 남는다

**언제 쓰나** — 「타입으로 갈랐으니 런타임에도 갈리겠지」를 의심할 때.

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

그림 해설 — 한 단계에 한 문장.

- 방출된 파일에 `type Shape` 선언이 **통째로 없다.** `function area(s)` 로 시작한다.
- ★★★ 남은 것은 **JS 연산자뿐**이다 — `s.kind === "circle"` 과 `typeof v === "string"`.
- 즉 좁히기를 **가능하게 한 코드가 곧 런타임에 도는 코드**다. 타입은 그것을 **읽고 따라간** 것뿐이다.
- 실행 결과가 그것을 확인한다 — `area` 가 `12` 와 `9`, `describe` 가 「문자열 3자」와 「숫자 4.0」.
- ★★ 마지막 줄 `typeof "abc"` 와 `typeof 4` 가 `string number` 다 — **런타임이 종류를 가르는 유일한 수단**이다.
- ★ 그래서 판별 필드는 **런타임에 실제로 있는 값**이어야 한다. 타입에만 있는 칸으로는 못 가른다([**01번 주제**](../01-what-ts-adds-and-erases/)).

비용 — 0. 방출에 한 글자도 안 남는다. **갈라 쓰는 일은 전부 JS 가 한다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  type SN = string | number                     기본형
  type Shape = Circle | Square | Tri            판별 유니온
  type Res = Ok | Err                           불리언 리터럴 판별
  type Handler = ((a: string) => void) | ((a: number) => void)   ★ 매개변수가 never

  switch (s.kind) { case "circle": … }          판별 필드로 좁히기
  if (r.ok) … else …                            불리언 리터럴로 좁히기
  const exhaustive: never = s;                  ★ 전수 검사

  const probe: null = v;                        ★ 정규화 결과를 캐묻는 탐침
```

**규칙 불릿**

- ★★★ **꺼내는 쪽은 교집합, 넣는 쪽은 합집합**이다. 좁히기 전에는 **모든 멤버에 있는 멤버만** 쓸 수 있다(`TS2339`).
- ★★ **진단의 들여쓴 줄이 범인을 짚어 준다** — 「does not exist on type **'string'**」처럼 **어느 멤버**인지 말한다.
- ★★★ **적은 대로 남지 않는다** — 중복 제거 · `never` 흡수 · 리터럴 흡수 · `true | false` → `boolean` · 평탄화 · `any`/`unknown` 흡수 · **순서 조정**.
- ★★ **`.d.ts` 는 정규화를 안 한다.** 같은 선언이 두 창에서 다르게 보인다 — 「적은 것」과 「계산된 것」이다.
- ★★ **함수 유니온의 매개변수는 교집합이라 `never` 가 되기 쉽다.** 반환은 합집합이다.
- ★★★ **판별 필드는 리터럴 타입이어야 한다** — 문자열 리터럴이든 `true`/`false` 든.
- ★★ **전수 검사는 `never` 자리에 넣어 보는 것**이고, 진단이 **빠뜨린 멤버 이름**을 알려 준다.
- ★★ **방출에 한 글자도 안 남는다.** 좁히기를 실제로 하는 것은 `===`·`typeof` 같은 **JS 연산자**다.

**금지 사례** — 이 주제에서 던져 받은 것 셋이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 좁히지 않고 멤버 접근   ->  TS2339  Property 'toFixed' does not exist on type 'SN'.
                                 Property 'toFixed' does not exist on type 'string'.
2) 함수 유니온에 인자      ->  TS2345  Argument of type '"s"' is not assignable to parameter of type 'never'.
3) 전수 검사 실패          ->  TS2322  Type 'Tri' is not assignable to type 'never'.
```

## 어디서 틀리나

- ★★★ 「**유니온이면 양쪽 메서드를 다 쓸 수 있다**」 — 반대다. **둘 다 가진 것만** 쓸 수 있다.
- ★★★ 「**적은 대로 남는다**」 — 안 남는다. `"x" | "y" | string` 은 그냥 `string` 이 되고 순서도 바뀐다.
- ★★ 「**`.d.ts` 를 보면 계산된 타입을 알 수 있다**」 — `.d.ts` 는 **적은 그대로**다. 계산 결과는 **탐침**으로 물어야 한다.
- ★★ 「**핸들러를 유니온으로 묶으면 둘 다 받는다**」 — **아무것도 못 받는다.** 매개변수가 `never` 가 된다.
- ★★ 「**`string | any` 는 그래도 `string` 쪽 검사가 남겠지**」 — 통째로 `any` 다. 탐침에 **진단이 아예 안 난다**.
- ★ 「**`true | false` 는 `boolean` 과 다른 것**」 — 같다. 정규화에서 합쳐진다.
- ★ 「**전수 검사는 `default` 에 `throw` 만 넣으면 된다**」 — 그러면 **컴파일 시각에 못 잡는다.** `never` 대입이 있어야 이름을 짚어 준다.
- ★ 「**판별 필드는 아무 타입이나 된다**」 — **리터럴 타입**이어야 좁혀진다. `kind: string` 이면 못 가른다.
- ★ 「**타입으로 갈랐으니 런타임에도 갈린다**」 — 방출에 한 글자도 없다. `typeof`·`===` 가 없으면 아무 일도 안 일어난다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 좁히기 전에는 **모든 멤버에 있는 멤버만** 쓸 수 있다 | 핸드북 「Union Types」. `TS2339` 의 들여쓴 줄이 그 규칙이다 |
| **언어 보장** | 유니온은 **평탄화·중복 제거·흡수**로 정규화된다 | 탐침 열 개의 결과. `never`·`any`·`unknown` 의 거동이 [**04번 주제**](../04-any-unknown-never-void/)와 맞는다 |
| **언어 보장** | 함수 유니온의 **매개변수는 교집합** | `TS2345` 가 「parameter of type 'never'」라고 말한다 |
| **언어 보장** | 판별 필드로 좁히기 · `never` 대입으로 **전수 검사** | 핸드북 「Discriminated Unions」·「Exhaustiveness checking」. `TS2322` 가 빠뜨린 이름을 짚는다 |
| **언어 보장** | 유니온은 **방출에 안 남는다** | `ex.09f.js` 전문과 `node` 출력 |
| **설정에 달림** | `null`·`undefined` 가 **유니온 멤버로 분리돼 보이는 것** | `strictNullChecks`(`strict` 에 딸려 7.0 기본 `true`) |
| **이 판(7.0.2)의 관찰** | ★★ **정규화된 유니온의 멤버 순서**(`number \| string` → `string \| number`) | 내부 타입 식별자 순이다. **대조할 것은 순서가 아니라 「같은 집합으로 정리된다」는 성질**이다 |
| **이 판의 관찰** | `.d.ts` 가 **정규화를 안 하는 것** | 선언 방출기의 구현이다. 「적은 그대로 옮긴다」만 성질로 읽는다 |
| **이 판의 관찰** | 진단 문구와 들여쓴 줄의 단계 수 | 문구는 판마다 바뀐다. 코드(`TS2339`·`TS2345`·`TS2322`)가 더 오래 간다 |

★ 「**에러가 안 난 줄」도 근거다** — 2절의 `withAny` 가 대표다. **진단이 없다는 것이 `any` 가 됐다는 증거**다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| 종류가 정해진 데이터 — **판별 필드를 둔 유니온** | 판별 칸 없는 객체 유니온 — 좁힐 방법이 없다 |
| 결과 타입 `Ok \| Err` — 성공·실패를 값으로 다룬다 | 예외로 충분한 자리에 억지로 결과 유니온을 만드는 것 |
| `string \| null` 처럼 「없을 수도 있다」 | `string \| any` — 통째로 `any` 가 된다 |
| 리터럴 유니온 `"asc" \| "desc"` — 값의 집합을 좁힌다 | `"asc" \| "desc" \| string` — **`string` 에 흡수돼** 검사가 사라진다 |
| 반환 타입의 유니온 | **콜백·핸들러의 유니온** — 매개변수가 `never` 가 된다 |

## 핵심 문장

1. **꺼내는 쪽은 교집합, 넣는 쪽은 합집합이다** — `TS2339` 가 어느 멤버 탓인지 짚어 준다.
2. **적은 대로 남지 않는다** — 중복·`never`·리터럴이 사라지고 순서도 바뀐다.
3. **`.d.ts` 와 탐침이 다른 답을 준다** — 「적은 것」과 「계산된 것」을 가르는 자리다.
4. **함수 유니온의 매개변수는 `never` 가 되기 쉽다** — 유니온은 핸들러 그릇으로 나쁘다.
5. **판별 필드는 리터럴이어야 하고, 전수 검사는 `never` 대입이다** — 빠뜨린 멤버를 이름으로 알려 준다.
6. **방출에 한 글자도 안 남는다** — 갈라 쓰는 일은 `typeof`·`===` 가 한다.

## 관련 자료

- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — `never`·`any`·`unknown` 의 성질은 그쪽이 정본이다. 여기서는 **유니온에서 어떻게 구는지**만.
- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) — `null` 탐침과 `.d.ts` 덤프의 **두 창**은 그쪽에서 세웠다.
- [**06번 주제** — 초과 프로퍼티 검사](../06-excess-property-checks/) — 대상이 유니온일 때 그 검사가 **키의 합집합**으로 도는 것은 그쪽.
- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 「방출에 안 남는다」의 근거는 그쪽.
- [목록의 **10번 주제**](../10-intersection-types/)(인터섹션 타입) — `&` 는 그쪽. 여기서는 **함수 매개변수가 교집합이 되는 자리**에서만 스친다.
- [목록의 **11번 주제**](../11-literal-types-and-as-const/)(리터럴 타입과 `as const`) — 리터럴 유니온이 넓어지는 자리는 그쪽. 여기서는 **흡수 규칙**까지.
- [목록의 **12번 주제**](../12-narrowing/)(좁히기) — `typeof`·`in`·`instanceof` 의 전면 서술은 그쪽. 여기서는 **판별 필드**까지.
- [목록의 **24번 주제**](../24-conditional-types-and-distribution/)(조건부 타입과 분배) — 유니온이 조건부 타입에서 **분배**되는 규칙은 그쪽.
- `../../js/syntax/README.md` 의 **01번 주제**(값의 종류와 `typeof`) — `typeof` 의 **런타임 의미는 JS 갈래가 정본**이다.

## 용어 풀이

> **유니온 타입(union type)** — `A | B` 처럼 「이 값은 이것들 중 하나」를 적는 타입.\
> 예: `string | number`. 좁히기 전에는 양쪽에 다 있는 멤버만 쓸 수 있다.

> **정규화(normalization)** — 유니온을 만들 때 컴파일러가 평탄화·중복 제거·흡수를 해서 정리하는 것.\
> 예: `"x" | "y" | string` 이 그냥 `string` 이 된다.

> **흡수** — 더 넓은 멤버가 있으면 좁은 멤버가 사라지는 것.\
> 예: 리터럴이 기반 타입에, `never` 가 아무 타입에, `string` 이 `any`·`unknown` 에 흡수된다.

> **좁히기(narrowing)** — 제어 흐름을 따라가며 그 자리에서 가능한 타입을 줄이는 것.\
> 예: `if (typeof v === "string")` 안에서 `string | number` 가 `string` 이 된다.

> **판별 유니온(discriminated union)** — 멤버마다 **리터럴 타입인 공통 칸**을 둬서 그 값으로 종류를 가르는 유니온.\
> 예: `kind: "circle"` · `ok: true`.

> **판별 필드(discriminant)** — 그 종류를 가르는 리터럴 타입 프로퍼티.\
> 예: `kind` · `ok`. 런타임에 실제로 있는 값이어야 한다.

> **전수 검사(exhaustiveness checking)** — 모든 갈래를 처리했는지 컴파일러에게 확인시키는 수법.\
> 예: `const exhaustive: never = s;` — 남은 멤버가 있으면 그 이름이 진단에 나온다.

## 더 들어가면

- **왜 매개변수가 교집합인가** — 「어느 함수인지 모른다」는 전제에서 나온다. 둘 다에게 안전한 인자만 받아야 하므로 매개변수 타입을 교차한다. [**05번 주제**](../05-structural-typing/)의 **반변**과 같은 뿌리다.
- **판별 칸이 없으면** — `in` 연산자로 가르는 길이 있다(`"fly" in pet`). [목록의 **12번 주제**](../12-narrowing/)에서 던진다.
- **리터럴 흡수를 피하는 법** — `"asc" | "desc" | (string & {})` 처럼 적으면 편집기 자동완성은 살리고 흡수는 막는 관용구가 있다. [목록의 **11번 주제**](../11-literal-types-and-as-const/)와 엮인다.
- **유니온이 커지면 검사가 느려진다** — 멤버 수에 따라 할당 가능성 판정이 곱으로 늘어난다. 이 배치에서는 **재지 않았다** — [목록의 **45번 주제**](../45-type-level-performance/)에서 잰다.
