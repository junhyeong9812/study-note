# ts/syntax/08 — `interface` 대 `type` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제에서는 「**에러가 안 나는 줄**」이 가장 센 근거다 —
> 「몇 건이 나는가」와 「**어느 선언이 조용히 통과하는가**」를 같이 적는다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 이름을 두 번씩 선언하면 (예측)

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

- 진단은 **몇 건**이고 **어느 줄**인가?
- `interface Merged` 를 **세 번** 선언했는데 11행은 통과하는가?
- `interface Overloaded` 를 두 번 선언하면 `ov(1)` 과 `ov("s")` 는 어떻게 되는가?

### 2. 확장과 교차가 같은 충돌을 만나면 (예측)

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

- 진단은 **몇 건**이고 **어느 줄**인가?
- `type Crossed = { p: string } & { p: number };` 선언 자체는 진단이 나는가?
- `const asString: string = c.p;` 와 `const asNumber: number = c.p;` 는 각각 어느 쪽인가?

### 3. 같은 모양을 `Record` 자리에 넘기면 (예측)

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

- 진단은 **몇 건**이고, `interface` 쪽과 `type` 쪽 중 **어느 쪽**인가?
- 진단의 들여쓴 줄은 뭐라고 하는가?

### 4. `interface` 가 확장할 수 있는 것의 경계 (예측)

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

- 진단은 **몇 건**이고, 세 `extends`(튜플·유니온·원시) 중 **통과하는 것**은 어느 것인가?
- `interface CallSignature { (a: number): string }` 은 통과하는가?

### 5. 같은 실수에 진단의 모양 (예측)

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

- 두 진단의 **에러 코드**가 같은가?
- 한쪽만 **들여쓴 줄**이 붙는다 — 어느 쪽이고 거기 어떤 이름이 나오는가?

### 6. 방출과 선언 방출 (예측)

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

- `.d.ts` 에서 두 번 선언한 `interface Shape` 는 **한 덩어리로 합쳐져** 나오는가?
- 방출된 `.js` 에 둘 중 무엇이 남는가?

### 7. `interface` 에 암묵 인덱스 시그니처가 없는 이유 (왜)

- 같은 모양인데 한쪽만 막히는 이유를 **1번의 성질**에 기대어 말할 수 있는가?

### 8. 교차가 더 위험한 자리 (경계)

- 「`&` 는 `extends` 의 다른 표기법」이 깨지는 지점을 **진단이 나는 시점**으로 설명할 수 있는가?

### 9. 둘 다 되는 것 (경계)

- 「`type` 만 된다」로 자주 오해되지만 **둘 다 되는 것** 둘을 댈 수 있는가?

### 10. 무엇을 기준으로 고르나 (연결)

- 취향이 아닌 **판별 기준 둘**을 대고, 각각 이 문서의 어느 실행 결과에 기대는지 말할 수 있는가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **이 판(7.0.2)의 관찰** · **설정에 달린 것** · **안 잰 것**에 각각 해당하는 항목을 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
