# ts/syntax/08 — `interface` 대 `type` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·`.d.ts` 전문·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제에서는 「**진단 목록에 없는 선언**」이 가장 센 근거다 — 교차의 충돌이 그렇다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **3건**(13·16·24행) — `interface` 는 **세 번 선언해도 조용하다**

**출력**

```ts
// ex.08a.ts
// 같은 이름을 두 번 선언하면 — 한쪽은 합쳐지고 한쪽은 막힌다
interface Merged {
    a: number;
}
interface Merged {
    b: string;
}
interface Merged {
    run(): void;
}
const m: Merged = { a: 1, b: "x", run() {} };

type Aliased = {
    a: number;
};
type Aliased = {
    b: string;
};

interface Clashing {
    p: number;
}
interface Clashing {
    p: string;
}

interface Overloaded {
    (x: number): string;
}
interface Overloaded {
    (x: string): string;
}
declare const ov: Overloaded;
console.log(m, ov(1), ov("s"));
```

```text
===== tsc --pretty false --noEmit ex.08a.ts (tsc exit=1) =====
ex.08a.ts(13,6): error TS2300: Duplicate identifier 'Aliased'.
ex.08a.ts(16,6): error TS2300: Duplicate identifier 'Aliased'.
ex.08a.ts(24,5): error TS2717: Subsequent property declarations must have the same type.  Property 'p' must be of type 'number', but here has type 'string'.
```

**왜 그런가**

| 선언 | 결과 |
|---|---|
| `interface Merged` × **3** + `const m: Merged = { a, b, run }` | ★★★ **전부 통과** — 셋이 하나로 합쳐졌다 |
| `type Aliased` × 2 | **TS2300** × 2 — 「Duplicate identifier 'Aliased'.」 **두 줄 다** 난다 |
| `interface Clashing { p: number }` + `{ p: string }` | **TS2717** — 「Subsequent property declarations must have the same type.」 |
| `interface Overloaded` × 2 + `ov(1)`·`ov("s")` | ★ **전부 통과** — 호출 시그니처는 **오버로드로 쌓인다** |

- ★★★ `interface` 는 **열려 있다.** 같은 이름을 몇 번이든 쓸 수 있고 컴파일러가 합친다.
- ★★ 다만 **무조건 합치는 것이 아니다** — 같은 이름의 프로퍼티는 **같은 타입**이어야 한다(`TS2717`).
- ★ 호출 시그니처만 예외적으로 **쌓인다.** 그래서 남의 함수 타입에 오버로드를 덧붙일 수 있다.
- ★★ `type` 은 **닫혀 있다.** 이름 하나에 정의 하나다 — 이 성질이 3번의 차이를 만든다.

### 2. ★★★ 진단 **3건**(5·15·22행) — **교차의 충돌 선언에는 진단이 없다**

**출력**

```ts
// ex.08b.ts
// 확장과 교차가 충돌을 만났을 때 — 한쪽은 말하고 한쪽은 침묵한다
interface Base {
    p: string;
}
interface Extended extends Base {
    p: number;
}

type TBase = { p: string };
type Crossed = TBase & { p: number };
declare const c: Crossed;

const asString: string = c.p;
const asNumber: number = c.p;
const putBack: Crossed = { p: "x" };

interface Narrowed extends Base {
    p: "literal";
}
type CrossedOk = TBase & { p: "literal" };
declare const ok: CrossedOk;
const okProbe: null = ok.p;
console.log(asString, asNumber, putBack, okProbe);
```

```text
===== tsc --pretty false --noEmit ex.08b.ts (tsc exit=1) =====
ex.08b.ts(5,11): error TS2430: Interface 'Extended' incorrectly extends interface 'Base'.
  Types of property 'p' are incompatible.
    Type 'number' is not assignable to type 'string'.
ex.08b.ts(15,28): error TS2322: Type 'string' is not assignable to type 'never'.
ex.08b.ts(22,7): error TS2322: Type '"literal"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| `interface Extended extends Base { p: number }` | 확장 충돌 | **TS2430** — 들여쓴 줄 **두 단계** |
| `type Crossed = { p: string } & { p: number }` | 교차 충돌 | ★★★ **진단 없음** |
| `const asString: string = c.p` | `never` 를 `string` 에 | ★★ **통과** |
| `const asNumber: number = c.p` | `never` 를 `number` 에 | ★★ **통과** |
| `const putBack: Crossed = { p: "x" }` | 값을 넣으려 한다 | **TS2322** — 「… not assignable to type 'never'.」 |
| `interface Narrowed extends Base { p: "literal" }` | **좁히는** 확장 | ★ **통과** |
| `const okProbe: null = ok.p` | 탐침 | **TS2322** — 타입이 **`"literal"`** |

- ★★★ **실수는 10행에서 했는데 진단은 15행에서 난다.** 문구도 「`string` 을 `never` 에 못 넣는다」라 원인을 안 가리킨다.
- ★★ `c.p` 의 타입이 `never` 인 것이 13·14행의 **통과**로 증명된다 — `never` 는 어디로든 들어간다([**04번 주제**](../04-any-unknown-never-void/)).\
  ★ 즉 **탐침이 안 통하는 자리**다. `const probe: null = c.p` 도 통과해 버리므로 **역방향 대입**으로 물어야 한다.
- ★★ `extends` 는 **선언 자리에서** 말한다. 들여쓴 줄이 이유를 두 단계로 적는다 — 「Types of property 'p' are incompatible.」 → 「Type 'number' is not assignable to type 'string'.」
- ★ **좁히는 확장은 둘 다 된다** — `p: "literal"` 은 `p: string` 과 충돌이 아니다. 22행 탐침이 결과가 `"literal"` 임을 확인한다.

### 3. ★★★ 진단 **2건** — **둘 다 `interface` 쪽**이다

**출력**

```ts
// ex.08c.ts
// 암묵 인덱스 시그니처 — interface 에는 없고 type 별칭에는 있다
interface AsInterface {
    a: string;
}
type AsAlias = {
    a: string;
};
declare const i: AsInterface;
declare const t: AsAlias;

const fromInterface: Record<string, unknown> = i;
const fromAlias: Record<string, unknown> = t;

function send(payload: Record<string, unknown>) {
    return Object.keys(payload).length;
}
send(i);
send(t);

const fixed: Record<string, unknown> = i as unknown as Record<string, unknown>;
console.log(fromInterface, fromAlias, fixed);
```

```text
===== tsc --pretty false --noEmit ex.08c.ts (tsc exit=1) =====
ex.08c.ts(11,7): error TS2322: Type 'AsInterface' is not assignable to type 'Record<string, unknown>'.
  Index signature for type 'string' is missing in type 'AsInterface'.
ex.08c.ts(17,6): error TS2345: Argument of type 'AsInterface' is not assignable to parameter of type 'Record<string, unknown>'.
  Index signature for type 'string' is missing in type 'AsInterface'.
```

**왜 그런가**

| 줄 | 결과 |
|---|---|
| `const fromInterface: Record<string, unknown> = i` | **TS2322** |
| `const fromAlias: Record<string, unknown> = t` | ★★ **통과** |
| `send(i)` | **TS2345** — 인자 자리도 같다 |
| `send(t)` | ★★ **통과** |
| `i as unknown as Record<string, unknown>` | **통과** — 단언으로 뚫었다 |

- 들여쓴 줄이 규칙을 그대로 말한다 — 「Index signature for type 'string' is missing in type 'AsInterface'.」
- ★★★ `interface AsInterface { a: string }` 과 `type AsAlias = { a: string }` 은 **글자 하나 안 다르다.** 그래도 갈린다.
- ★★ 이유는 1번의 성질이다 — **`interface` 는 병합될 수 있어서** 지금 키가 `a` 뿐이어도\
  다른 파일이 키를 더할 수 있다. 그러면 「이 타입의 모든 값이 `unknown` 이다」를 **컴파일러가 약속할 수 없다.**
- ★ `type` 은 닫혀 있어 키 목록이 확정이므로 약속할 수 있다 — **암묵 인덱스 시그니처**가 생긴다.
- ★ JSON 을 다루는 코드에서 자주 부딪힌다. 제대로 고치는 법은 **인덱스 시그니처를 직접 적거나** `type` 으로 바꾸는 것이다.

### 4. ★★ 진단 **3건** — 튜플만 통과하고 **유니온·원시는 `TS2312`**

**출력**

```ts
// ex.08d.ts
// type 별칭만 되는 것들과, interface 가 확장할 수 있는 것의 경계
type Union = string | number;
type Primitive = string;
type Tuple = [string, number];
type Fn = (a: number) => string;
type Conditional<T> = T extends string ? "yes" : "no";
type Mapped<T> = { [K in keyof T]: T[K] };
type Template = `id-${number}`;

interface FromTuple extends Tuple {}
interface FromUnion extends Union {}
interface FromPrimitive extends Primitive {}

interface CallSignature {
    (a: number): string;
}
declare const t: Tuple;
declare const cond: Conditional<string>;
declare const tmpl: Template;
const probe: null = cond;
console.log(t, tmpl, probe);
```

```text
===== tsc --pretty false --noEmit ex.08d.ts (tsc exit=1) =====
ex.08d.ts(11,29): error TS2312: An interface can only extend an object type or intersection of object types with statically known members.
ex.08d.ts(12,33): error TS2312: An interface can only extend an object type or intersection of object types with statically known members.
ex.08d.ts(20,7): error TS2322: Type '"yes"' is not assignable to type 'null'.
```

**왜 그런가**

| 선언 | 결과 |
|---|---|
| `type` 여덟 개(유니온·원시·튜플·함수·조건부·매핑·템플릿) | **전부 통과** |
| `interface FromTuple extends Tuple {}` | ★ **통과** — 튜플은 **객체 타입**이다 |
| `interface FromUnion extends Union {}` | **TS2312** |
| `interface FromPrimitive extends Primitive {}` | **TS2312** |
| `interface CallSignature { (a: number): string }` | ★ **통과** — 함수는 **호출 시그니처**로 적는다 |
| `const probe: null = cond` | **TS2322** — `Conditional<string>` 이 **`"yes"`** |

- ★★ `TS2312` 의 문구가 경계를 그대로 말한다 — 「An interface can only extend an object type or intersection of object types with **statically known members**.」
- ★★ 그래서 「`type` 만 되는 것」은 **유니온 · 원시 · 조건부 · 매핑 · 템플릿 리터럴**이다.\
  **튜플과 함수는 아니다** — 자주 오해되는 자리다.
- ★ 탐침이 조건부 타입이 실제로 계산됐음을 확인해 준다 — 선언만 통과한 게 아니라 값이 `"yes"` 로 잡혔다.

### 5. ★★ 코드가 **다르다** — `TS2739` 는 **한 줄**, `TS2322` 는 **`TBase` 를 짚는 들여쓴 줄**

**출력**

```ts
// ex.08e.ts
// 같은 실수에 진단의 모양이 갈린다
interface IBase {
    a: number;
    b: number;
    c: number;
}
interface IExt extends IBase {
    d: number;
}

type TBase = {
    a: number;
    b: number;
    c: number;
};
type TExt = TBase & { d: number };

declare const empty: {};
const toInterface: IExt = empty;
const toAlias: TExt = empty;
console.log(toInterface, toAlias);
```

```text
===== tsc --pretty false --noEmit ex.08e.ts (tsc exit=1) =====
ex.08e.ts(19,7): error TS2739: Type '{}' is missing the following properties from type 'IExt': d, a, b, c
ex.08e.ts(20,7): error TS2322: Type '{}' is not assignable to type 'TExt'.
  Type '{}' is missing the following properties from type 'TBase': a, b, c
```

**왜 그런가**

| 대상 | 코드 | 모양 |
|---|---|---|
| `interface IExt extends IBase` | **TS2739** | 한 줄 — 「missing the following properties from type 'IExt': d, a, b, c」 |
| `type TExt = TBase & { d: number }` | **TS2322** | 두 줄 — `TExt` 를 말한 뒤 들여쓴 줄에서 **`TBase`** 를 짚는다 |

- ★★ `extends` 쪽은 상속한 것까지 **합쳐서 한 번에** 나열한다. 이름은 `IExt` **하나**만 나온다.
- ★★ 교차 쪽은 **조각마다** 보고한다. 그래서 **어느 조각에서 왔는지**가 드러난다 — 여기서는 `a, b, c` 가 `TBase` 에서 왔다는 것.
- ★ 어느 쪽이 나은지는 상황에 달렸다 —

| | 장점 | 단점 |
|---|---|---|
| `TS2739`(확장) | 한눈에 다 보인다 | **어느 조각에서 왔는지**를 잃는다 |
| `TS2322`(교차) | 조각 이름이 드러난다 | 교차가 깊으면 들여쓴 줄이 **계단처럼 쌓인다** |

- ★ 나열 순서(`d, a, b, c`)는 **선언 순서**다 — 자기 멤버 먼저, 상속한 것이 뒤다. 이 판의 관찰이다.

### 6. ★★ `.d.ts` 는 **두 덩어리 그대로** · `.js` 에는 **둘 다 없다**

**출력**

```ts
// ex.08f.ts
// 둘 다 방출에 한 글자도 안 남는다 — 선언 방출에서만 갈린다
export interface Shape {
    kind: string;
}
export interface Shape {
    area(): number;
}
export type Alias = {
    kind: string;
    area(): number;
};

export const asInterface: Shape = { kind: "c", area: () => 1 };
export const asAlias: Alias = { kind: "c", area: () => 1 };
console.log(asInterface.area(), asAlias.area());
```

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.08f.ts (tsc exit=0) =====
===== 방출된 ex.08f.d.ts =====
export interface Shape {
    kind: string;
}
export interface Shape {
    area(): number;
}
export type Alias = {
    kind: string;
    area(): number;
};
export declare const asInterface: Shape;
export declare const asAlias: Alias;
```

```text
===== tsc --pretty false --module commonjs ex.08f.ts (tsc exit=0) =====
===== 방출된 ex.08f.js =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.asAlias = exports.asInterface = void 0;
exports.asInterface = { kind: "c", area: () => 1 };
exports.asAlias = { kind: "c", area: () => 1 };
console.log(exports.asInterface.area(), exports.asAlias.area());
```

```text
===== node ex.08f.js (node exit=0) =====
1 1
```

**왜 그런가**

| 산출물 | 내용 |
|---|---|
| `.d.ts` | `interface Shape` 가 ★★ **두 덩어리 그대로** · `type Alias` 는 한 덩어리 · 값 둘은 `declare const` |
| `.js` | ★★★ 타입이 **한 글자도 없다.** `exports.asInterface`·`exports.asAlias` 두 값뿐 |
| `node` | `1 1` — 두 값이 똑같이 돈다 |

- ★★ `.d.ts` 가 병합된 `interface` 를 **안 합치고 그대로** 싣는 이유 — **병합 가능성 자체가 계약의 일부**다.\
  합쳐서 내보내면 소비자가 「이건 원래 한 덩어리였다」로 읽게 되고, 자기 쪽에서 또 덧붙일 때의 규칙이 흐려진다.
- ★★★ `.js` 에는 둘 다 안 남는다 — 그래서 **번들 크기·런타임 비용은 고르는 기준이 아니다.**
- ★ 이 판에서는 `--module commonjs` 로 방출해 `node` 로 돌렸다. 기본값(`esnext`)으로 뽑은 ESM 은 `.js` 확장자로는 `node` 가 못 읽는다.

### 7. ★★★ **`interface` 는 나중에 키가 늘 수 있기 때문이다**

**왜 그런가**

- `Record<string, unknown>` 은 「**이 객체의 모든 키가 `unknown` 이다**」는 약속이다.
- `type AsAlias = { a: string }` 은 **닫혀 있다.** 키가 `a` 뿐임이 확정이므로 그 약속을 지킬 수 있다 — 컴파일러가 **암묵 인덱스 시그니처**를 준다.
- ★★★ `interface AsInterface` 는 **1번에서 본 대로 열려 있다.** 지금 이 파일에서 키가 `a` 뿐이어도\
  **다른 파일이 `interface AsInterface { b: () => void }` 를 더할 수 있다.** 그러면 약속이 깨진다.
- ★★ 그래서 컴파일러는 **약속을 아예 안 해 준다.** 진단의 들여쓴 줄이 그것을 그대로 적는다.
- ★ 한 줄로 — **1번의 이득(병합)이 3번에서 대가를 치른다.** 두 사실은 같은 성질의 앞뒷면이다.

### 8. ★★★ **진단이 나는 시점이 다르다** — 선언 자리인가, 한참 뒤인가

**왜 그런가**

```text
  interface Extended extends Base { p: number }
        ▼  바로 그 줄에서
     TS2430  Interface 'Extended' incorrectly extends interface 'Base'.
       Types of property 'p' are incompatible.

  type Crossed = { p: string } & { p: number }
        ▼  (아무 말 없음)
     c.p 의 타입이 조용히 never 가 된다
        ▼  값을 넣으려 할 때, 다섯 줄 뒤에
     TS2322  Type 'string' is not assignable to type 'never'.
```

- ★★★ 2번에서 **13·14행이 둘 다 통과**한 것이 결정적 증거다. `never` 는 `string` 에도 `number` 에도 들어가므로\
  **읽는 코드는 전부 통과하고, 쓰는 코드만 터진다.**
- ★★ 그래서 큰 코드베이스에서는 **조각을 `&` 로 겹친 지점과 터지는 지점이 멀어진다.** 원인 추적이 어렵다.
- ★ `extends` 는 덜 유연하다 — 좁히는 것 말고는 재선언을 못 한다. 그 대신 **틀린 순간에 말한다.**
- ★ 교차를 꼭 써야 하면 **`extends` 로 한 번 받아 보는** 것이 싼 검사다. 충돌이 있으면 `TS2430` 이 먼저 말해 준다.
- ★★ 이것이 `strict` 때문인지도 던져서 확인했다 — `--strict false` 로 줘도 **세 건이 글자 하나까지 같다.**

```text
===== tsc --pretty false --noEmit --strict false ex.08b.ts (tsc exit=1) =====
ex.08b.ts(5,11): error TS2430: Interface 'Extended' incorrectly extends interface 'Base'.
  Types of property 'p' are incompatible.
    Type 'number' is not assignable to type 'string'.
ex.08b.ts(15,28): error TS2322: Type 'string' is not assignable to type 'never'.
ex.08b.ts(22,7): error TS2322: Type '"literal"' is not assignable to type 'null'.
```

### 9. ★★ **튜플**과 **함수 타입** — 둘 다 된다

**왜 그런가**

| 오해 | 실제 |
|---|---|
| 「튜플은 `type` 만」 | ★ `interface FromTuple extends Tuple {}` 이 **통과**한다 — 튜플은 객체 타입이다 |
| 「함수 타입은 `type` 만」 | ★ `interface CallSignature { (a: number): string }` — **호출 시그니처**로 적는다 |

- ★★ `interface` 가 못 하는 것은 **유니온과 원시**다(`TS2312`). 문구의 「statically known members」가 그 경계다.\
  유니온은 「어느 쪽이냐에 따라 멤버가 다르다」라 정적으로 정해지지 않고, 원시는 멤버를 적을 대상이 아니다.
- ★ 여기에 **조건부 타입과 매핑 타입**이 더해진다 — 둘 다 「계산해 봐야 멤버가 나오는」 것이라 같은 이유로 안 된다.
- ★ 그래서 외울 것은 목록이 아니라 성질 하나다 — **「멤버가 지금 정해져 있나」**.

### 10. ★★★ 기준 둘 — **덧붙일 여지가 필요한가** · **객체가 아닌 것을 적어야 하나**

**왜 그런가**

| 기준 | 어느 실행 결과에 기대나 | 결론 |
|---|---|---|
| **덧붙일 여지가 필요한가** | 1번 — `interface` 3회 선언이 통과, `type` 은 `TS2300` | 공개 API·라이브러리 타입은 `interface` |
| **객체가 아닌 것을 적어야 하나** | 4번 — 유니온·원시가 `TS2312` | 유니온·원시·조건부·매핑은 `type` |

- ★★ 여기에 **실무에서 먼저 부딪히는 세 번째 기준**이 붙는다 — 3번의 `Record` 벽.\
  JSON 처럼 「키가 열린 자리」에 넘겨야 하면 `type` 이 마찰이 적다.
- ★★ **고르는 기준에서 빼도 되는 축**도 실행으로 확인했다 —

| 축 | 왜 빼나 |
|---|---|
| 번들 크기·런타임 비용 | 6번 — `.js` 에 **둘 다 한 글자도 안 남는다** |
| 검사 속도 | ★ 이 배치에서 **재지 않았다.** 재려면 타입 수백 개짜리 코드베이스가 필요하다 |

- ★ 한 줄로 — **「나중에 누가 덧붙일 것인가」와 「적어야 할 모양이 객체인가」**. 나머지는 취향이다.

### 11. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | `interface` 는 **병합**되고 `type` 은 중복 선언이 안 된다 · 병합은 **같은 이름 같은 타입** · `extends` 는 호환되지 않는 재선언을 막는다 · 교차는 프로퍼티를 교차해 `never` 를 만든다 · `interface` 에는 **암묵 인덱스 시그니처가 없다** · 둘 다 방출에 안 남는다 |
| **이 판(7.0.2)의 관찰** | 진단의 **모양**(`TS2739` 한 줄 대 `TS2322` + 중첩 줄) · `TS2739` 가 나열하는 **프로퍼티 순서**(`d, a, b, c`) · `.d.ts` 가 병합된 `interface` 를 **덩어리 그대로** 싣는 것 · 진단 문구 전문 |
| **설정에 달린 것** | ★ **없다.** 다섯 파일을 `--strict false` 로 다시 던져 **출력과 종료 코드가 전부 같은 것**을 확인했다 |
| **안 잰 것** | ★ **검사 속도.** 재는 방법 자체가 전제를 요구한다 — 타입 수백 개짜리 코드베이스 · 같은 의미의 두 벌 · 잡음보다 큰 차이. 이 주제의 여섯 파일로는 성립하지 않아 **손으로 유도하지 않고 빈칸으로 남겼다**. 목록의 **45번 주제**에서 잰다 |

- ★ 이 주제에는 **「설정에 달린 것」이 없다.** [**07번 주제**](../07-object-type-details/)와 정반대다 — 거기는 그 칸이 본체였다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 병합·중복 | `--noEmit ex.08a.ts` | exit 1 · `TS2300` 2건 + `TS2717` 1건 · `interface` 3회 선언·오버로드 통과 |
| 확장 대 교차 | `--noEmit ex.08b.ts` | exit 1 · `TS2430`·`TS2322`·`TS2322` **3건** · **교차 선언 자체는 조용** · 좁히는 확장 통과 |
| 암묵 인덱스 시그니처 | `--noEmit ex.08c.ts` | exit 1 · `TS2322`·`TS2345` **2건** · **둘 다 `interface` 쪽** |
| `extends` 의 경계 | `--noEmit ex.08d.ts` | exit 1 · `TS2312` 2건 + 탐침 1건 · **튜플·호출 시그니처 통과** |
| 진단의 모양 | `--noEmit ex.08e.ts` | exit 1 · `TS2739` 1건(한 줄) · `TS2322` 1건(+ `TBase` 줄) |
| 선언 방출 | `--declaration --emitDeclarationOnly ex.08f.ts` | exit 0 · `interface Shape` 가 **두 덩어리** |
| 방출·실행 | `--module commonjs ex.08f.ts` + `node ex.08f.js` | tsc exit 0 · node exit 0 · `.js` 에 타입 없음 · `1 1` |
| `strict` 끔 | 다섯 파일 전부 `--strict false` 로 재실행 | **전부 같다** — 문서에는 `ex.08b.ts` 블록을 실었다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- 진단의 **모양**(`TS2739` 한 줄 대 `TS2322` + 중첩 줄) — 보고기의 구현이다. 「조각 이름이 드러나는가」만 성질로 읽는다.
- `TS2739` 가 나열하는 **프로퍼티 순서** — 이 판에서 `d, a, b, c` 였다.
- `.d.ts` 가 병합된 `interface` 를 덩어리 그대로 싣는 것 — 선언 방출기의 구현이다.
- 진단 문구 전문 — 코드(`TS2300`·`TS2717`·`TS2430`·`TS2312`·`TS2739`)가 더 오래 간다.

**안 돌려 본 것 · 안 잰 것**

- ★ **검사 속도** — 위 표의 셋째 층 그대로다. **재지 않았고 수치를 적지 않았다.**
- **모듈 보강**(남의 모듈의 `interface` 에 멤버를 더하는 것) — 파일 여럿과 모듈 해석이 얽혀 이 주제의 범위를 넘는다. 목록의 **33번 주제**에서 던진다.
- `--strict false` 판 — **다섯 파일 전부 던져서 기본값 판과 대조했고 출력·종료 코드가 같았다.** 문서에는 대표로 `ex.08b.ts` 의 블록을 실었다.
