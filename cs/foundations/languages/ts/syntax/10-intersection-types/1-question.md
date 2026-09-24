# ts/syntax/10 — 인터섹션 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제에서는 「**에러가 안 나는 줄**」이 가장 센 근거다 —
> 교차가 만든 `never` 는 **탐침을 통과해 버려서** 진단이 나지 않는다. 그때는 **역방향으로** 물어야 한다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 이 주제는 진단 문구에 `|` 와 `&` 가 많다. 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 교차한 값에서 쓸 수 있는 멤버는 어디까지인가 (예측)

```ts
// ex.10a.ts
// 교차는 「둘 다」다 — 꺼내는 쪽이 넓어지고 넣는 쪽이 좁아진다
interface Named {
    name: string;
}
interface Aged {
    age: number;
}
type Person = Named & Aged;
declare const p: Person;

const useName = p.name;
const useAge = p.age;
const useNone = p.email;

const putBoth: Person = { name: "a", age: 1 };
const putOne: Person = { name: "a" };
const putExtra: Person = { name: "a", age: 1, email: "e" };

declare const onlyNamed: Named;
const widen: Named = p;
const narrow: Person = onlyNamed;

const probe: null = p;
const probeName: null = p.name;
console.log(useName, useAge, useNone, putBoth, putOne, putExtra, widen, narrow, probe, probeName);
```

- 진단은 **몇 건**이고 **어느 줄**인가?
- `const widen: Named = p;` 와 `const narrow: Person = onlyNamed;` 는 각각 어느 쪽인가?
- 객체 리터럴에 `email` 을 끼우면 어느 코드가 나오는가?

### 2. 충돌한 자리를 컴파일러에게 캐물으면 (예측)

```ts
// ex.10b.ts
// 충돌은 두 종류다 — 타입 전체가 never 가 되는 것과 칸 하나만 never 가 되는 것
type PrimClash = string & number;
declare const prim: PrimClash;

const probePrim: null = prim;
const asString: string = prim;
const asNumber: number = prim;
const putPrim: PrimClash = "x";

type PropClash = { p: string } & { p: number };
declare const obj: PropClash;

const probeObj: null = obj;
const probeProp: null = obj.p;
const propAsString: string = obj.p;
const propAsNumber: number = obj.p;
const putObj: PropClash = { p: "x" };

type OptClash = { q?: string } & { q: number };
declare const opt: OptClash;
const probeOpt: null = opt.q;
const putOpt: OptClash = { q: 1 };

type Narrowing = { r: string } & { r: "lit" };
declare const nar: Narrowing;
const probeNar: null = nar.r;
console.log(prim, asString, asNumber, putPrim, obj, propAsString, propAsNumber, putObj, opt, putOpt, nar);
```

- 탐침·역방향 대입이 **열두 줄**인데 진단은 **몇 건**인가? **침묵한 줄**은 어디인가?
- `const probePrim: null = prim;` 이 아무 말도 안 하는 이유는 무엇인가?
- `PrimClash` 와 `PropClash` 중 **타입 자체가 `never`** 인 것은 어느 쪽인가?

### 3. 교차도 적은 대로 남나 (예측)

```ts
// ex.10c.ts
// 교차도 적은 대로 남나 — 09 의 유니온과 같은 질문을 교차에 던진다
interface A {
    a: string;
}
interface B {
    b: number;
}
interface C {
    c: boolean;
}

declare const dup: A & A;
declare const withNever: A & never;
declare const withAny: A & any;
declare const withUnknown: A & unknown;
declare const nested: (A & B) & C;
declare const reordered: B & A;
declare const litBase: "a" & string;
declare const litClash: "a" & "b";
declare const objPrim: A & string;

const p1: null = dup;
const p2: null = withNever;
const p3: null = withAny;
const p4: null = withUnknown;
const p5: null = nested;
const p6: null = reordered;
const p7: null = litBase;
const p8: null = litClash;
const p9: null = objPrim;

const back2: A & never = { a: "x" };
const back3: A & any = "A 가 아닌 것";
const back8: "a" & "b" = "a";
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, back2, back3, back8);
```

- `A & A` · `A & never` · `A & any` · `A & unknown` 은 각각 무엇으로 답하는가?
- `B & A` 는 **순서가 바뀌는가**? 09 의 유니온과 같은가 다른가?
- `"a" & string` 과 `A & string` 은 각각 무엇이 되는가?

### 4. 함수를 교차하면 무엇이 되나 (예측)

```ts
// ex.10d.ts
// 함수의 교차는 오버로드가 된다 — 09 의 함수 유니온과 정반대다
type CrossFn = ((a: string) => string) & ((a: number) => number);
declare const cross: CrossFn;

const fromString: null = cross("s");
const fromNumber: null = cross(1);
cross(true);

interface OverFn {
    (a: string): string;
    (a: number): number;
}
declare const over: OverFn;
const overString: null = over("s");
over(true);

type UnionFn = ((a: string) => string) | ((a: number) => number);
declare const union: UnionFn;
union("s");

const asStringFn: (a: string) => string = cross;
const asNumberFn: (a: number) => number = cross;
const asBoolFn: (a: boolean) => boolean = cross;
console.log(fromString, fromNumber, overString, asStringFn, asNumberFn, asBoolFn);
```

- `cross("s")` 와 `cross(1)` 은 각각 통과하는가? 반환 타입은 무엇인가?
- `cross(true)` 의 에러 코드와 문구는 손으로 적은 오버로드와 **같은가**?
- 같은 파일의 `union("s")` 는 어느 코드로 막히는가?

### 5. 유니온을 끼워 교차하면 (예측)

```ts
// ex.10e.ts
// (A | B) & C 는 분배된다 — 진단의 들여쓴 줄이 그 조각 이름을 부른다
interface Circle {
    kind: "circle";
    r: number;
}
interface Square {
    kind: "square";
    side: number;
}
interface Tagged {
    id: string;
}

declare const shape: (Circle | Square) & Tagged;

const probeAll: null = shape;
const probeKind: null = shape.kind;
const probeId: null = shape.id;
shape.r;

declare const spelled: (Circle & Tagged) | (Square & Tagged);
const probeSpelled: null = spelled;

const putOk: (Circle | Square) & Tagged = { kind: "circle", r: 1, id: "x" };
const putNoTag: (Circle | Square) & Tagged = { kind: "circle", r: 1 };
const putMixed: (Circle | Square) & Tagged = { kind: "circle", r: 1, side: 2, id: "x" };

function split(s: (Circle | Square) & Tagged) {
    if (s.kind === "circle") {
        const inCircle: null = s;
    } else {
        const inSquare: null = s;
    }
}
console.log(probeAll, probeKind, probeId, probeSpelled, putOk, putNoTag, putMixed, split);
```

- `shape.kind` 는 무엇으로 답하고, `shape.r` 의 진단이 **들여쓴 줄에 부르는 이름**은 무엇인가?
- `if (s.kind === "circle")` 안팎에서 `s` 는 각각 무엇인가?
- 초과 프로퍼티 검사는 **어느 타입 이름**을 대고 막는가?

### 6. 두 방출에는 교차가 어떻게 남나 (예측)

```ts
// ex.10f.ts
// 선언 방출은 교차를 적은 그대로 돌려준다 — 09 의 유니온과 같다
export interface A {
    a: string;
}
export interface B {
    b: number;
}
export type Dup = A & A;
export type WithNever = A & never;
export type PrimClash = string & number;
export type Nested = (A & B) & B;
export type Reordered = B & A;
export type CrossFn = ((a: string) => string) & ((a: number) => number);
export declare const merged: A & B;
export const made = { a: "x", b: 1 } as A & B;
```

```ts
// ex.10g.ts
// 교차는 방출에 한 글자도 안 남는다 — 합치는 일은 JS 스프레드가 한다
interface A {
    a: string;
}
interface B {
    b: number;
}
type Both = A & B;

function merge(x: A, y: B): Both {
    return { ...x, ...y };
}

const both: Both = merge({ a: "hi" }, { b: 7 });
console.log("merge     :", JSON.stringify(both));
console.log("a / b     :", both.a, "/", both.b);
console.log("런타임 구분:", typeof both, Object.keys(both).join(","));
```

- `.d.ts` 가 `A & A` 와 `string & number` 를 **정규화해서** 적는가?
- 방출된 `.js` 에서 `type Both` 는 어떻게 되고, 합치는 일은 무엇이 하는가?

### 7. 왜 꺼내는 쪽이 넓어지나 (왜)

- 유니온과 **정확히 반대 방향**으로 넓어지는 이유를 한 문장으로 댈 수 있는가?

### 8. 왜 함수 교차는 오버로드가 되나 (왜)

- 7번의 이유로 **함수 교차는 오버로드, 함수 유니온은 `never`** 가 되는 것을 설명할 수 있는가?

### 9. 탐침이 침묵하는 자리 (경계)

- `null` 탐침이 아무 말도 안 할 때 **그 타입이 무엇일 수 있는지** 두 가지를 대고, 둘을 **어떻게 가르는가**?

### 10. 두 창이 다른 답을 주는 자리 (경계)

- `.d.ts` 덤프와 `null` 탐침이 교차에서 갈리는 지점을 09 의 유니온과 같은 말로 설명할 수 있는가?

### 11. 09 와의 쌍대성 (연결)

- 「꺼내는 쪽·넣는 쪽·매개변수·반환」 네 칸에서 유니온과 교차가 어떻게 뒤집히는지 표로 채울 수 있는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
