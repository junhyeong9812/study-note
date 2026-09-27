# ts/syntax/12 — 좁히기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제에서는 **분기마다 탐침을 하나씩 박아** 두었다 —
> 「**각 분기에서 무엇이 남는가**」를 글자로 답할 수 있어야 한다.
> ★★ 「**에러가 안 난 줄**」도 근거다 — `never` 로 좁혀지면 탐침이 침묵한다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> ★★ 이 주제는 **세 파일이 `--strict false` 에서 답이 갈린다.** 그 세 자리는 **양쪽 판을 다 실었다.**
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. `typeof` 사다리의 분기마다 무엇이 남나 (예측)

```ts
// ex.12a.ts
// typeof 로 갈라 놓고 분기마다 무엇이 남는지 탐침으로 찍는다
type Mixed = string | number | boolean | object | null | undefined;

function byTypeof(v: Mixed) {
    if (typeof v === "string") {
        const inString: null = v;
    } else if (typeof v === "number") {
        const inNumber: null = v;
    } else if (typeof v === "boolean") {
        const inBoolean: null = v;
    } else if (typeof v === "object") {
        const inObject: null = v;
    } else if (typeof v === "undefined") {
        const inUndefined: null = v;
    } else {
        const rest: null = v;
        const exhaustive: never = v;
    }
}

function nullTrap(v: string | null) {
    if (typeof v === "object") {
        const caught: null = v;
    }
    if (v !== null) {
        const excluded: null = v;
    }
}

function noNarrow(v: string | number) {
    const t = typeof v;
    if (t === "string") {
        const notNarrowed: null = v;
    }
}
console.log(byTypeof, nullTrap, noNarrow);
```

- 탐침이 **열 개**인데 진단은 **몇 건**인가? 침묵한 줄은 어디이고 왜인가?
- 12행 `const inObject: null = v;` 는 무엇이라고 답하는가?
- 23행 `const caught: null = v;` 는 어느 쪽인가? 33행은 왜 안 좁혀지는가?

### 2. `typeof` 말고 나머지 넷은 (예측)

```ts
// ex.12b.ts
// typeof 말고 나머지 넷 — instanceof · in · 진릿값 · 동등성
class Dog {
    bark(): void {}
}
class Cat {
    meow(): void {}
}
function byInstance(p: Dog | Cat) {
    if (p instanceof Dog) {
        const inDog: null = p;
    } else {
        const inCat: null = p;
    }
}

interface Bird {
    fly(): void;
}
interface Fish {
    swim(): void;
}
function byIn(p: Bird | Fish) {
    if ("fly" in p) {
        const inBird: null = p;
    } else {
        const inFish: null = p;
    }
}

function byTruth(v: string | number | null | undefined) {
    if (v) {
        const truthy: null = v;
    } else {
        const falsy: null = v;
    }
}

function byEquality(a: string | number, b: string | boolean) {
    if (a === b) {
        const inA: null = a;
        const inB: null = b;
    }
}

function byLiteral(v: "up" | "down" | 1) {
    if (v === "up") {
        const up: null = v;
    } else {
        const rest: null = v;
    }
}

function unknownIn(u: unknown) {
    if (typeof u === "object" && u !== null && "x" in u) {
        const shaped: null = u;
    }
}
console.log(byInstance, byIn, byTruth, byEquality, byLiteral, unknownIn);
```

- `if (v)` 의 **참 갈래와 거짓 갈래**는 각각 무엇인가? 둘 중 **덜 좁혀지는 쪽**은 어디인가?
- `a === b` 로 두 값이 **동시에** 좁혀지는가?
- 55행 `const shaped: null = u;` 가 답하는 타입에 **`&` 가 왜 나오는가**?

### 3. 조건을 변수에 담으면 (예측)

```ts
// ex.12c.ts
// 조건을 변수에 담아도 좁혀지나 — const 와 let 이 갈린다
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number }
    | { kind: "tri"; base: number; h: number };

function byConstAlias(v: string | number) {
    const isStr = typeof v === "string";
    if (isStr) {
        const narrowed: null = v;
    }
}

function byLetAlias(v: string | number) {
    let isStr = typeof v === "string";
    if (isStr) {
        const notNarrowed: null = v;
    }
}

function bySwitch(s: Shape) {
    switch (s.kind) {
        case "circle": {
            const inCircle: null = s;
            return;
        }
        case "square": {
            const inSquare: null = s;
            return;
        }
        case "tri": {
            const inTri: null = s;
            return;
        }
        default: {
            const exhaustive: never = s;
            return exhaustive;
        }
    }
}

function afterEarlyReturn(s: Shape) {
    if (s.kind === "circle") return;
    const rest: null = s;
}

function byDiscriminantAlias(s: Shape) {
    const k = s.kind;
    if (k === "circle") {
        const viaAlias: null = s;
    }
}
console.log(byConstAlias, byLetAlias, bySwitch, afterEarlyReturn, byDiscriminantAlias);
```

- `const isStr` 과 `let isStr` 은 각각 좁히는가?
- `default` 의 `const exhaustive: never = s;` 는 진단이 나는가?
- 50행 `const viaAlias: null = s;` 는 1번의 33행과 **같은가 다른가**?

### 4. 좁히기가 어디서 풀리나 (예측)

```ts
// ex.12d.ts
// 좁히기가 어디서 풀리나 — 함수 호출 뒤·클로저 안·재대입 뒤를 각각 던진다
interface Box {
    v?: string;
}
declare function touch(): void;

function afterCall(b: Box) {
    if (b.v) {
        touch();
        const stillNarrow: null = b.v;
    }
}

function insideClosure(b: Box) {
    if (b.v) {
        const cb = () => {
            const inClosure: null = b.v;
        };
        cb();
    }
}

function fixedByLocal(b: Box) {
    const v = b.v;
    if (v) {
        const cb = () => {
            const inClosure: null = v;
        };
        cb();
    }
}

function afterReassign(v: string | number) {
    if (typeof v === "string") {
        const before: null = v;
        v = 1;
        const after: null = v;
    }
}

let outer: string | number = "s";
function overLet() {
    if (typeof outer === "string") {
        const here: null = outer;
        const cb = () => {
            const inClosure: null = outer;
        };
        cb();
    }
}

function byIndex(xs: (string | number)[], i: number) {
    if (typeof xs[i] === "string") {
        const elem: null = xs[i];
    }
}

function byGetter(o: { get v(): string | number }) {
    if (typeof o.v === "string") {
        const got: null = o.v;
    }
}
console.log(afterCall, insideClosure, fixedByLocal, afterReassign, overLet, byIndex, byGetter);
```

- 10행(함수 호출 뒤)·17행(클로저 안)·27행(지역 변수로 고친 뒤)은 각각 무엇인가?
- 46행(모듈 `let` 을 클로저에서)은 44행과 왜 다른가?
- 54행(배열 인덱스)·60행(게터)은 좁혀지는가?

### 5. `strict` 를 끄면 어느 줄이 바뀌나 (예측)

- 위 네 파일을 `--strict false` 로 다시 던지면 **몇 파일이 갈리는가**?
- 1번의 12·14행은 어떻게 바뀌는가?

### 6. 방출된 JS 에는 무엇이 남나 (예측)

```ts
// ex.12e.ts
// 좁히기는 방출에 한 글자도 안 남는다 — 남는 것은 JS 연산자뿐이다
type Shape = { kind: "circle"; r: number } | { kind: "square"; side: number };

class Dog {
    bark(): string {
        return "왈";
    }
}
class Cat {
    meow(): string {
        return "야옹";
    }
}

function describe(v: string | number | null): string {
    if (typeof v === "string") return `문자열 ${v.length}자`;
    if (typeof v === "number") return `숫자 ${v.toFixed(1)}`;
    return "null";
}

function area(s: Shape): number {
    if (s.kind === "circle") return 3 * s.r * s.r;
    return s.side * s.side;
}

function speak(p: Dog | Cat): string {
    if (p instanceof Dog) return p.bark();
    return p.meow();
}

console.log("describe  :", describe("abc"), "/", describe(4), "/", describe(null));
console.log("area      :", area({ kind: "circle", r: 2 }), "/", area({ kind: "square", side: 3 }));
console.log("speak     :", speak(new Dog()), "/", speak(new Cat()));
console.log("typeof null:", typeof null);
```

- 좁히기를 실제로 하는 코드는 무엇으로 남는가?
- `typeof null` 은 무엇을 찍는가?

### 7. 왜 좁히기는 제어 흐름을 따라가나 (왜)

- 「같은 변수가 줄마다 다른 타입」이 모순이 아닌 이유를 한 문장으로 댈 수 있는가?

### 8. 왜 클로저 안에서는 풀리나 (왜)

- 4번의 17행과 27행의 차이를 **언제 실행되는가**로 설명할 수 있는가?

### 9. 좁혀졌는데도 안전하지 않은 자리 (경계)

- 4번의 10·54·60행 중 **컴파일러가 믿어 주지만 런타임에 깨질 수 있는** 것을 고르고 이유를 댈 수 있는가?

### 10. `typeof` 의 구멍 (경계)

- `typeof` 로 가를 수 **없는** 것을 두 가지 대고, 그때 무엇을 쓰는가?

### 11. 09·10 과 잇기 (연결)

- 판별 유니온의 좁히기(09)와 교차의 분배(10)가 이 주제에서 어떻게 만나는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
