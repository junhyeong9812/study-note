# ts/syntax/19 — 제네릭 기본 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 본체는 둘이다 —
> 「**추론이 배열·객체 리터럴에서 넓어진다**」(21 이 고칠 고장)와 「**런타임에 타입 인자가 없다**」.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
>
> ★★★ **추론된 타입을 눈으로 보는 법** — 블록에 `const probe: null = …` 이 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> 그 줄의 `TS2322` 는 **에러가 아니라 출력**이다 — 세지 말고 읽어라.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 인자 `3` 을 세 가지로 부르면 (예측)

```ts
// ex.19a.ts
// 타입 매개변수는 호출마다 채워진다 -- 추론과 명시 둘 다, 그리고 any 와 무엇이 다른가
function identity<T>(x: T): T {
    return x;
}

const inferred = identity(3);
const explicit = identity<number>(3);
const widened = identity<string | number>(3);
const p1: null = inferred;
const p2: null = explicit;
const p3: null = widened;

function anyIdentity(x: any): any {
    return x;
}
const p4: null = anyIdentity(3);

function pair<A, B>(a: A, b: B): [A, B] {
    return [a, b];
}
const p5: null = pair("가", 1);

function firstOf<T>(xs: T[]): T {
    return xs[0]!;
}
const p6: null = firstOf([1, "가"]);

identity<number>("가");
console.log(p1, p2, p3, p4, p5, p6);
```

- 9·10·11행의 탐침은 각각 무엇을 뱉는가?
- 16행 `anyIdentity(3)` 에는 왜 진단이 없는가?
- 21행 `pair("가", 1)` 은 `["가", 1]` 인가 `[string, number]` 인가?

### 2. 무엇이 좁혀지고 무엇이 넓어지나 (예측)

```ts
// ex.19b.ts
// 추론은 리터럴로 좁혀지지 않는다 -- 21 의 const 타입 매개변수가 고칠 고장을 여기서 먼저 본다
function firstOf<T>(xs: T[]): T {
    return xs[0]!;
}
const p1: null = firstOf(["가", "나"]);

function keep<T>(x: T): T {
    return x;
}
const p2: null = keep("가");
const p3: null = keep(["가", "나"]);
const p4: null = keep({ mode: "auto" });

const asConst = keep(["가", "나"] as const);
const p5: null = asConst;

let mutable = "가";
const p6: null = keep(mutable);

function pickMode<T extends string>(mode: T): T {
    return mode;
}
const p7: null = pickMode("auto");
console.log(p1, p2, p3, p4, p5, p6, p7);
```

- 10행 `keep("가")` 와 11행 `keep(["가","나"])` 의 답은 **같은 모양인가**?
- 12행 `keep({ mode: "auto" })` 는 무엇을 뱉는가?
- 15행과 23행은 각각 **무엇이** 답을 좁혔는가?

### 3. 꺾쇠를 어디에 다느냐 (예측)

```ts
// ex.19c.ts
// 제네릭 함수 타입과 제네릭 인터페이스 -- 타입 매개변수가 어디에 붙느냐가 다르다
export interface GenericFn {
    <T>(x: T): T;
}

export interface FnOfT<T> {
    (x: T): T;
}

export type ArrowGeneric = <T>(x: T) => T;

export const g1: GenericFn = (x) => x;
export const g2: FnOfT<string> = (x) => x;
export const g3: ArrowGeneric = (x) => x;

const p1: null = g1(3);
const p2: null = g2("가");
const p3: null = g3(true);

export const bad: FnOfT<string> = (x: number) => x;
export declare const notFilled: FnOfT;
console.log(p1, p2, p3);
```

- 16·17·18행은 각각 무엇을 뱉는가? 셋이 같은가?
- 21행 `FnOfT` 를 인자 없이 쓰면 무슨 코드가 나오는가?
- 20행의 연쇄 설명 줄은 **어느 쪽**을 짚는가?

### 4. 타입 인자를 하나만 적으면 (예측)

```ts
// ex.19d.ts
// 타입 인자는 전부 적거나 하나도 안 적거나다 -- 부분 추론은 없다
function pair<A, B>(a: A, b: B): [A, B] {
    return [a, b];
}

const all = pair<string, number>("가", 1);
const none = pair("가", 1);
const partial = pair<string>("가", 1);

function withDefault<A, B = boolean>(a: A, b: B): [A, B] {
    return [a, b];
}
const oneOfTwo = withDefault<string>("가", 1);
const p1: null = oneOfTwo;
console.log(all, none, partial, p1);
```

- 8행은 통과하는가? 무슨 코드인가?
- 13행은 왜 걸리는가?
- 14행 탐침은 무엇을 뱉는가?

### 5. 제네릭 클래스에서 막히는 자리 (예측)

```ts
// ex.19e.ts
// 제네릭 클래스 -- 타입 인자는 인스턴스마다 정해지고 static 자리에는 못 온다
export class Box<T> {
    constructor(public value: T) {}

    map<U>(f: (x: T) => U): Box<U> {
        return new Box(f(this.value));
    }

    static empty: T;
}

const b1 = new Box("가");
const b2 = new Box<number>(1);
const b3 = b1.map((s) => s.length);
const p1: null = b1;
const p2: null = b2;
const p3: null = b3;

const wrong = new Box<number>("가");
console.log(p1, p2, p3, wrong);
```

- 9행 `static empty: T;` 는 통과하는가?
- 17행 `b1.map((s) => s.length)` 는 무엇을 뱉는가? `s` 의 타입은 어디서 왔는가?
- 진단은 모두 몇 건인가?

### 6. 컴파일하면 `<T>` 는 어떻게 되나 (예측)

```ts
// ex.19f.ts
// 런타임에 타입 인자는 없다 -- 방출물에 한 글자도 안 남는다
class Box<T> {
    constructor(public value: T) {}
}

function firstOf<T>(xs: T[]): T {
    return xs[0]!;
}

const sBox = new Box<string>("가");
const nBox = new Box<number>(1);
console.log("1) 두 Box 의 생성자가 같은가 :", sBox.constructor === nBox.constructor);
console.log("2) Box 의 이름               :", Box.name);
console.log("3) firstOf 의 매개변수 개수  :", firstOf.length);
console.log("4) firstOf 를 문자열로       :", firstOf.toString());
console.log("5) 인스턴스에 타입 흔적이 있나:", Object.keys(sBox).join(","));
```

- `tsc` 의 진단은 몇 줄이고 종료 코드는 무엇인가?
- 실행 출력 1번 줄은 `true` 인가 `false` 인가?
- 4번 줄 `firstOf.toString()` 에 꺾쇠가 보이는가?

### 7. 왜 부분 추론이 없나 (왜)

- 4번을 근거로 「**하나만 적으면 왜 나머지를 추론해 주지 않는가**」를 설명할 수 있는가?

### 8. 왜 배열의 속만 넓어지나 (왜)

- 2번 10행과 11행의 차이를 **넓히기(widening)** 로 설명할 수 있는가?

### 9. `any` 와 제네릭의 경계 (경계)

- 1번 16행을 근거로 둘의 차이를 한 문장으로 댈 수 있는가? 「모르겠으면 `unknown`」은 어느 자리인가?

### 10. 제네릭을 쓸 자리와 안 쓸 자리 (경계)

- 타입 매개변수가 **한 자리에만** 나오면 무엇을 해야 하는가?

### 11. Java·Kotlin 과 잇기 (연결)

- 6번의 결론을 Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번**·Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **12번** 과 견줄 수 있는가?

### 12. 20·21 로 잇기 (연결)

- 2번에서 본 고장을 [**20번 주제**](../20-generic-constraints-and-defaults/)와 [**21번 주제**](../21-inference-control-const-and-noinfer/)가 **각각 어떻게** 건드리는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
