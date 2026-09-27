# ts/syntax/05 — 구조적 타이핑 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제에서는 **「에러가 안 나는 줄」까지 세야 답이다** —
> 「몇 건이 나는가」와 「**어느 줄이 통과하는가**」를 같이 적는다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. ★★ **`strict` 가 기본 `true`** 라 `strictFunctionTypes` 도 켜져 있다.
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 이름이 다른 넷을 서로 넣으면 (예측)

```ts
// ex.05a.ts
// 이름이 다른 셋이 서로 오가는지 본다
interface Point {
    x: number;
    y: number;
}
interface Vector {
    x: number;
    y: number;
}
class Coord {
    constructor(public x: number, public y: number) {}
}
type Triple = { x: number; y: number; z: number };

const p: Point = { x: 1, y: 2 };
const v: Vector = p;
const c: Coord = p;
const backToPoint: Point = new Coord(1, 2);

const triple: Triple = { x: 1, y: 2, z: 3 };
const widen: Point = triple;
const narrow: Triple = p;
console.log(v, c, backToPoint, widen, narrow);
```

- 진단은 **몇 건**이고 **어느 줄**인가?
- `const c: Coord = p;` 처럼 **객체 리터럴에서 온 값을 클래스 타입 자리에** 넣는 것은 통과하는가?

### 2. 같은 값을 두 가지 방법으로 넘기면 (예측)

```ts
// ex.05b.ts
// 초과 프로퍼티 검사 — 리터럴을 직접 넘길 때와 변수를 거칠 때
interface Point {
    x: number;
    y: number;
}
function take(pt: Point) {
    return pt.x;
}

const viaVar = { x: 1, y: 2, z: 3 };
const ok1: Point = viaVar;
take(viaVar);

const bad1: Point = { x: 1, y: 2, z: 3 };
take({ x: 1, y: 2, z: 3 });

const spread: Point = { ...viaVar };
const asserted: Point = { x: 1, y: 2, z: 3 } as Point;
const viaIndex: Point & Record<string, unknown> = { x: 1, y: 2, z: 3 };
console.log(ok1, bad1, spread, asserted, viaIndex);
```

- 진단은 **몇 건**이고, 열 줄 중 **통과하는 줄은 어느 것들**인가?
- `{ ...viaVar }` 와 `as Point` 와 `Point & Record<string, unknown>` 은 각각 어느 쪽인가?

### 3. `private` 을 한 줄 넣으면 (예측)

```ts
// ex.05c.ts
// private 멤버 하나가 구조적 타이핑을 명목 타이핑으로 바꾼다
class A {
    private secret = 1;
    constructor(public x: number) {}
}
class B {
    private secret = 1;
    constructor(public x: number) {}
}
class C extends A {}

const fromB: A = new B(1);
const fromLiteral: A = { x: 1, secret: 1 };
const fromC: A = new C(1);

class D {
    #hidden = 1;
    constructor(public x: number) {}
}
class E {
    #hidden = 1;
    constructor(public x: number) {}
}
const fromE: D = new E(1);
console.log(fromB, fromLiteral, fromC, fromE);
```

- 진단은 **몇 건**이고, 네 대입(`fromB`·`fromLiteral`·`fromC`·`fromE`) 중 **통과하는 것**은 어느 것인가?
- 세 진단의 **들여쓴 이유 줄**이 각각 뭐라고 하는가?

### 4. 함수끼리 서로 넣으면 (예측)

```ts
// ex.05d.ts
// 함수끼리의 할당 — 매개변수 자리에서만 방향이 뒤집힌다
interface Animal {
    name: string;
}
interface Dog extends Animal {
    name: string;
    bark(): void;
}

declare function takeAnimal(a: Animal): void;
declare function takeDog(d: Dog): void;

type FnDog = (a: Dog) => void;
type FnAnimal = (a: Animal) => void;

const wide: FnDog = takeAnimal;
const narrowFn: FnAnimal = takeDog;

interface WithMethod {
    handle(a: Animal): void;
}
interface WithProp {
    handle: (a: Animal) => void;
}
const asMethod: WithMethod = { handle: takeDog };
const asProp: WithProp = { handle: takeDog };

const fewer: (a: number, b: number) => number = (a: number) => a;
const more: (a: number) => number = (a: number, b: number) => a + b;
console.log(wide, narrowFn, asMethod, asProp, fewer, more);
```

- 진단은 **몇 건**이고 **어느 줄**인가?
- `asMethod` 와 `asProp` 은 **같은 시그니처**인데 결과가 갈리는가?

### 5. 같은 파일을 `strictFunctionTypes` 끄고 던지면 (예측)

- 위 파일을 `--strictFunctionTypes false` 로 던지면 진단이 **몇 건**으로 줄고, **어느 줄이 살아남는가**?
- 그래서 그 플래그가 **정확히 무엇을 가르는지** 한 문장으로 말할 수 있는가?

### 6. 브랜드를 붙이면 (예측)

```ts
// ex.05e.ts
// 모양이 같아 섞이는 두 문자열을 브랜드로 갈라 놓는다
type UserId = string & { readonly __brand: "UserId" };
type OrderId = string & { readonly __brand: "OrderId" };

const asUserId = (s: string) => s as UserId;
const asOrderId = (s: string) => s as OrderId;

const u = asUserId("u-1");
const o = asOrderId("o-9");

function findUser(id: UserId) {
    return id.toUpperCase();
}

console.log(findUser(u));
const mixed: OrderId = u;
const fromPlain: UserId = "u-1";
findUser("u-1");
findUser(o);
const asPlainString: string = u;
console.log(mixed, fromPlain, asPlainString);
```

- 진단은 **몇 건**이고, `const asPlainString: string = u;` 는 통과하는가?
- 진단의 들여쓴 줄이 **몇 단계**로 이유를 적는가?

### 7. 브랜드가 런타임에 남나 (경계)

```ts
// ex.05f.ts
// 브랜드가 방출된 JS 에 남는지 본다
type UserId = string & { readonly __brand: "UserId" };

const asUserId = (s: string) => s as UserId;
const u: UserId = asUserId("u-1");

console.log("값:", u);
console.log("typeof:", typeof u);
console.log("__brand 프로퍼티:", (u as unknown as Record<string, unknown>).__brand);
console.log("그냥 문자열과 === :", (u as string) === "u-1");
```

- 방출된 `asUserId` 는 어떻게 생겼는가?
- `typeof u` · `u.__brand` · `u === "u-1"` 세 값은 각각 무엇인가?

### 8. 왜 이름이 아니라 모양인가 (왜)

- 구조적 타이핑이 주는 **이득 둘**과 **대가 둘**을 댈 수 있는가?

### 9. 초과 프로퍼티 검사의 성격 (경계)

- 이 검사가 **타입 시스템의 규칙이 아니라 편의 장치**라고 말할 수 있는 근거는 무엇인가?
- 빠져나가는 길 **넷**을 댈 수 있는가?

### 10. 명목이 필요한 자리 (연결)

- `UserId` 와 `OrderId` 를 섞이지 않게 만드는 방법 **둘**을 대고, 각각의 대가를 말할 수 있는가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 각각 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
