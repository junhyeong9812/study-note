# ts/syntax/06 — 초과 프로퍼티 검사 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제에서는 「**에러가 안 나는 줄**」까지 세야 답이다 —
> 「몇 건이 나는가」와 「**어느 줄이 통과하는가**」를 같이 적는다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 값을 여덟 자리에 놓으면 (예측)

```ts
// ex.06a.ts
// 같은 값이 자리에 따라 갈린다 — 리터럴을 직접 놓는 자리를 전부 모았다
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

const inArray: Point[] = [{ x: 1, y: 2, z: 3 }];
function ret(): Point {
    return { x: 1, y: 2, z: 3 };
}

interface Outer {
    inner: { a: number };
}
const nested: Outer = { inner: { a: 1, b: 2 } };

let later: Point;
later = { x: 1, y: 2, z: 3 };
console.log(ok1, bad1, inArray, ret(), nested, later);
```

- 진단은 **몇 건**이고 **어느 줄**인가?
- 배열 원소(`[{ … }]`)와 중첩 리터럴(`{ inner: { … } }`)은 각각 어느 쪽인가?

### 2. 여섯 가지 방법으로 넘기면 (예측)

```ts
// ex.06b.ts
// 빠져나가는 길 다섯과, 빠져나가지 못하는 하나
interface Point {
    x: number;
    y: number;
}
const src = { x: 1, y: 2, z: 3 };

const byVar: Point = src;
const bySpread: Point = { ...src };
const byAssert: Point = { x: 1, y: 2, z: 3 } as Point;
const byIndex: Point & Record<string, unknown> = { x: 1, y: 2, z: 3 };

function byGeneric<T extends Point>(v: T) {
    return v.x;
}
byGeneric({ x: 1, y: 2, z: 3 });

const bySatisfies = { x: 1, y: 2, z: 3 } satisfies Point;
const spreadPlus: Point = { ...src, w: 4 };
console.log(byVar, bySpread, byAssert, byIndex, bySatisfies, spreadPlus);
```

- 진단은 **몇 건**이고, 여섯 방법 중 **막히는 것**은 어느 것인가?
- `{ ...src, w: 4 }` 에서 진단이 짚는 키는 **몇 개**인가?

### 3. 프로퍼티가 전부 선택인 타입에 넘기면 (예측)

```ts
// ex.06c.ts
// 전부 선택인 타입은 변수로 넘겨도 막힌다 — 그리고 오타를 짚어 준다
interface Opts {
    color?: string;
    width?: number;
}
function draw(o: Opts) {
    return o.color;
}

const wrong = { colour: "red" };
draw(wrong);
draw({ colour: "red" });

const mixed = { colour: "red", width: 2 };
draw(mixed);

interface Half {
    id: string;
    color?: string;
}
function half(h: Half) {
    return h.id;
}
const forHalf = { id: "a", colour: "red" };
half(forHalf);
console.log(draw(mixed), half(forHalf));
```

- 진단은 **몇 건**이고, 두 진단의 **에러 코드가 같은가**?
- `draw(mixed)` 와 `half(forHalf)` 는 각각 어느 쪽인가?

### 4. 대상이 유니온이면 (예측)

```ts
// ex.06d.ts
// 유니온이 대상일 때 — 어느 타입 이름이 진단에 나오나
interface A {
    a: number;
}
interface B {
    b: number;
}
type AB = A | B;

const bothKeys: AB = { a: 1, b: 2 };
const strayKey: AB = { a: 1, c: 3 };

interface Circle {
    kind: "circle";
    r: number;
}
interface Square {
    kind: "square";
    side: number;
}
type Shape = Circle | Square;

const crossed: Shape = { kind: "circle", r: 1, side: 2 };
console.log(bothKeys, strayKey, crossed);
```

- 진단은 **몇 건**이고 `const bothKeys: AB = { a: 1, b: 2 };` 는 어느 쪽인가?
- 두 진단이 가리키는 **타입 이름**이 같은가, 다른가?

### 5. 반환 타입을 네 방법으로 적으면 (예측)

```ts
// ex.06e.ts
// 반환 자리의 비대칭 — 표기를 어디에 쓰느냐로 갈린다
interface Point {
    x: number;
    y: number;
}

function onFunction(): Point {
    return { x: 1, y: 2, z: 3 };
}
const onArrow = (): Point => ({ x: 1, y: 2, z: 3 });

const fromContext: () => Point = () => ({ x: 1, y: 2, z: 3 });
const fromContextFn: () => Point = function () {
    return { x: 1, y: 2, z: 3 };
};
console.log(onFunction(), onArrow(), fromContext(), fromContextFn());
```

- 진단은 **몇 건**이고 **어느 줄**인가?
- 네 함수는 **같은 리터럴을 같은 타입 자리에** 돌려주는데 결과가 갈리는 이유는 무엇인가?

### 6. 검사를 마친 뒤 객체에 무엇이 남나 (예측)

```ts
// ex.06f.ts
// 검사를 통과한 뒤 런타임에 여분 키가 남아 있는지 본다
interface Point {
    x: number;
    y: number;
}
function keysOf(pt: Point) {
    return Object.keys(pt);
}

const src = { x: 1, y: 2, z: 3 };
const bySpread: Point = { ...src };

console.log("변수 경유   :", keysOf(src));
console.log("단언 경유   :", keysOf({ x: 1, y: 2, z: 3 } as Point));
console.log("스프레드    :", Object.keys(bySpread));
console.log("JSON        :", JSON.stringify(bySpread));
console.log("'z' in      :", "z" in bySpread);
```

- 방출된 `ex.06f.js` 에서 `as Point` 와 `{ ...src }` 는 각각 어떻게 되는가?
- `Object.keys(bySpread)` 와 `"z" in bySpread` 는 각각 무엇인가?

### 7. 왜 리터럴만 보나 (왜)

- 「변수에 담으면 통과」가 **버그가 아니라 설계**인 이유를 한 문장으로 댈 수 있는가?

### 8. 이 검사의 성격 (경계)

- 이 검사가 **타입 시스템의 규칙이 아니라 편의 장치**라고 말할 근거를 **둘** 댈 수 있는가?

### 9. `satisfies` 와 `as` (경계)

- 둘 다 「타입을 적어 주는」 자리인데 이 검사 앞에서 **정반대로 행동한다** — 어느 쪽이 어느 쪽인가?

### 10. 약한 타입 검사의 한계 (경계)

- `TS2559` 가 **풀리는 조건**은 무엇이고, 그래서 못 잡는 실수는 어떤 모양인가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 각각 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
