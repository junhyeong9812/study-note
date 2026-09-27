# ts/syntax/15 — 제어 흐름 분석의 한계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 본체는 **좁힘이 풀리는 자리와 안 풀리는 자리를 전수로 재는 표**다 —
> [**12번 주제**](../12-narrowing/)가 일곱 자리를 쟀고 여기서 **서른셋**으로 넓힌다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> ★★ 이 주제는 **네 파일 중 셋**이 `--strict false` 에서 갈린다. 그 자리는 **양쪽 판을 다 실었다.**
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 경계를 넘는 열한 자리 (예측)

```ts
// ex.15a.ts
// 좁힘이 풀리는 자리와 안 풀리는 자리 — 1부: 경계를 넘는 여덟 모양
interface Box {
    v?: string;
}
declare function touch(): void;
declare function takeCb(f: () => void): void;

function afterCall(b: Box) {
    if (b.v) {
        touch();
        const a1: null = b.v;
    }
}
async function afterAwait(b: Box) {
    if (b.v) {
        await Promise.resolve();
        const a2: null = b.v;
    }
}
function inCallback(b: Box) {
    if (b.v) {
        takeCb(() => {
            const a3: null = b.v;
        });
    }
}
function inNestedDecl(b: Box) {
    if (b.v) {
        function inner() {
            const a4: null = b.v;
        }
        inner();
    }
}
function inIIFE(b: Box) {
    if (b.v) {
        (() => {
            const a5: null = b.v;
        })();
    }
}
function afterReassign(v: string | number) {
    if (typeof v === "string") {
        const a6: null = v;
        v = 1;
        const a7: null = v;
    }
}
function byLocalConst(b: Box) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const a8: null = v;
        });
    }
}
let mutable: string | number = "s";
function overModuleLet() {
    if (typeof mutable === "string") {
        const a9: null = mutable;
        takeCb(() => {
            const a10: null = mutable;
        });
    }
}
const frozen: string | number = "s";
function overModuleConst() {
    if (typeof frozen === "string") {
        takeCb(() => {
            const a11: null = frozen;
        });
    }
}
console.log(afterCall, afterAwait, inCallback, inNestedDecl, inIIFE, afterReassign, byLocalConst, overModuleLet, overModuleConst);
```

- 진단은 **몇 건**이고, 그중 **좁힘이 풀린 것은 몇 개**인가?
- 23행(콜백)과 38행(즉시 실행 함수)은 왜 갈리는가?
- 62행과 70행은 `let` 과 `const` 하나만 다른데 결과가 어떻게 되는가?

### 2. 무엇을 좁혔나 — 열다섯 자리 (예측)

```ts
// ex.15b.ts
// 2부: 무엇을 좁혔나 — 인덱스·게터·메서드 호출·판별 유니온·this·구조 분해·readonly
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number };
declare function takeCb(f: () => void): void;

function byIndexParam(xs: (string | number)[], i: number) {
    if (typeof xs[i] === "string") {
        const b1: null = xs[i];
    }
}
function byIndexLiteral(xs: (string | number)[]) {
    if (typeof xs[0] === "string") {
        const b2: null = xs[0];
    }
}
function byGetter(o: { get v(): string | number }) {
    if (typeof o.v === "string") {
        const b3: null = o.v;
    }
}
function byMethodCall(o: { v(): string | number }) {
    if (typeof o.v() === "string") {
        const b4: null = o.v();
    }
}
function duAfterCall(s: Shape, f: () => void) {
    if (s.kind === "circle") {
        f();
        const b5: null = s.r;
    }
}
function duInCallback(s: Shape) {
    if (s.kind === "circle") {
        takeCb(() => {
            const b6: null = s.r;
        });
    }
}
class Holder {
    v: string | number = "s";
    afterCall(f: () => void) {
        if (typeof this.v === "string") {
            const b7: null = this.v;
            f();
            const b8: null = this.v;
        }
    }
    inCallback() {
        if (typeof this.v === "string") {
            takeCb(() => {
                const b9: null = this.v;
            });
        }
    }
}
function byDestructure(b: { v?: string }) {
    const { v } = b;
    if (v) {
        takeCb(() => {
            const b10: null = v;
        });
    }
}
function byReadonlyProp(o: { readonly v: string | number }) {
    if (typeof o.v === "string") {
        takeCb(() => {
            const b11: null = o.v;
        });
    }
}
function inLoopBody(b: { v?: string }) {
    if (b.v) {
        for (let i = 0; i < 1; i++) {
            const b12: null = b.v;
        }
    }
}
function inTryFinally(b: { v?: string }) {
    if (b.v) {
        try {
            const b13: null = b.v;
        } finally {
            const b14: null = b.v;
        }
    }
}
function viaOptionalChain(b: { inner?: { v?: string } }) {
    if (b.inner?.v) {
        const b15: null = b.inner.v;
    }
}
console.log(byIndexParam, byIndexLiteral, byGetter, byMethodCall, duAfterCall, duInCallback, Holder, byDestructure, byReadonlyProp, inLoopBody, inTryFinally, viaOptionalChain);
```

- 진단은 **몇 건**이고, 그중 **좁혀지지 않은 것은 어느 줄**인가?
- 36행(판별 유니온을 콜백에서)과 52행(`this.v` 를 콜백에서)은 왜 갈리는가?
- 68행의 `readonly` 는 좁힘을 지켜 주는가?

### 3. `let` 대 `const` 의 진짜 기준 (예측)

```ts
// ex.15c.ts
// let 대 const 가 아니라 「어딘가에서 대입되는가」가 기준이다
declare function takeCb(f: () => void): void;
type Tagged = { kind: "a"; x: number } | { kind: "b" };

function constLocal(b: { v?: string }) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const c1: null = v;
        });
    }
}
function letNeverAssigned(b: { v?: string }) {
    let v = b.v;
    if (v) {
        takeCb(() => {
            const c2: null = v;
        });
    }
}
function letAssignedLater(b: { v?: string }) {
    let v = b.v;
    if (v) {
        takeCb(() => {
            const c3: null = v;
        });
    }
    v = undefined;
}
function paramNeverAssigned(s: Tagged) {
    if (s.kind === "a") {
        takeCb(() => {
            const c4: null = s.x;
        });
    }
}
function paramAssignedLater(s: Tagged) {
    if (s.kind === "a") {
        takeCb(() => {
            const c5: null = s.kind;
        });
    }
    s = { kind: "b" };
}
function indexByConstIndex(xs: (string | number)[]) {
    const i = 0;
    if (typeof xs[i] === "string") {
        const c6: null = xs[i];
    }
}
function indexByAssignedIndex(xs: (string | number)[]) {
    let i = 0;
    if (typeof xs[i] === "string") {
        const c7: null = xs[i];
    }
    i = 1;
}
console.log(constLocal, letNeverAssigned, letAssignedLater, paramNeverAssigned, paramAssignedLater, indexByConstIndex, indexByAssignedIndex);
```

- 일곱 자리 중 **풀린 것은 몇 개**이고 어느 것인가?
- 17행과 25행은 둘 다 `let` 인데 왜 갈리는가?
- 48행과 54행은 무엇 하나가 달라서 갈리는가?

### 4. 「믿어 주는」 자리를 깨뜨리면 (예측)

```ts
// ex.15d.ts
// 분석이 「믿어 주는」 자리 — 보장이 아니라는 것을 던져서 깨뜨린다
interface Box {
    v?: string;
}
function wipe(b: Box): void {
    delete b.v;
}
function afterCall(b: Box): string {
    if (b.v) {
        wipe(b);
        return b.v.toUpperCase();
    }
    return "없다";
}

let flip = 0;
const spy = {
    get v(): string | number {
        flip += 1;
        return flip % 2 === 1 ? "문자열" : 42;
    },
};
function afterGetter(): string {
    if (typeof spy.v === "string") {
        return spy.v.toUpperCase();
    }
    return "숫자다";
}

const shared: Box = { v: "안녕" };
async function afterAwait(): Promise<string> {
    if (shared.v) {
        await Promise.resolve();
        return shared.v.toUpperCase();
    }
    return "없다";
}

function run(label: string, f: () => string): void {
    try {
        console.log(label, f());
    } catch (e) {
        console.log(label, "터졌다 ->", (e as Error).message);
    }
}
run("afterCall  :", () => afterCall({ v: "안녕" }));
run("afterGetter:", () => afterGetter());
afterAwait().then(
    (r) => console.log("afterAwait :", r),
    (e) => console.log("afterAwait : 터졌다 ->", (e as Error).message),
);
shared.v = undefined;
```

- `tsc` 의 **종료 코드와 진단 건수**는 무엇인가?
- 세 줄의 실행 출력은 각각 무엇인가?
- 「함수 호출 뒤에는 안 풀린다」는 **보장인가 아닌가**?

### 5. 고치는 법 (예측)

```ts
// ex.15e.ts
// 고치는 법 — 지역 const 하나. 같은 코드를 고치기 전과 뒤로 나란히 둔다
interface Box {
    v?: string;
}
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number };
declare function takeCb(f: () => void): void;
declare function assertDefined<T>(v: T): asserts v is NonNullable<T>;

function brokenByProperty(b: Box) {
    if (b.v) {
        takeCb(() => {
            const e1: null = b.v;
        });
    }
}
function fixedByLocalConst(b: Box) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const e2: null = v;
        });
    }
}
function fixedByDestructure(b: Box) {
    const { v } = b;
    if (v) {
        takeCb(() => {
            const e3: null = v;
        });
    }
}
function fixedByAssertion(b: Box) {
    assertDefined(b.v);
    const e4: null = b.v;
    takeCb(() => {
        const e5: null = b.v;
    });
}
function brokenIndex(xs: (string | number)[]) {
    let i = 0;
    if (typeof xs[i] === "string") {
        const e6: null = xs[i];
    }
    i = 1;
}
function fixedIndex(xs: (string | number)[]) {
    let i = 0;
    const x = xs[i];
    if (typeof x === "string") {
        const e7: null = x;
    }
    i = 1;
}
function brokenDiscriminant(s: Shape) {
    if (s.kind === "circle") {
        takeCb(() => {
            const e8: null = s.kind;
        });
    }
    s = { kind: "square", side: 1 };
}
function fixedDiscriminant(s: Shape) {
    const shape = s;
    if (shape.kind === "circle") {
        takeCb(() => {
            const e9: null = shape.r;
        });
    }
    s = { kind: "square", side: 1 };
}
console.log(brokenByProperty, fixedByLocalConst, fixedByDestructure, fixedByAssertion, brokenIndex, fixedIndex, brokenDiscriminant, fixedDiscriminant);
```

- 진단은 **몇 건**이고, 고쳐진 자리는 어느 줄인가?
- 36행과 38행은 같은 단언 뒤인데 왜 갈리는가?
- 인덱스를 고치려면 무엇을 지역 변수에 담아야 하는가?

### 6. `--strict false` 로 던지면 (예측)

- 1번과 3번의 파일을 `--strict false` 로 다시 던지면 **어느 줄이 바뀌는가**?
- 그때 이 주제의 **실험 자체**에 무슨 일이 일어나는가?

### 7. 왜 콜백 안에서 풀리나 (왜)

- 콜백이 **언제 불릴지 모른다**는 사실과 이어서 설명할 수 있는가?

### 8. 왜 함수 호출 뒤에는 안 풀리나 (왜)

- 이것이 **안전해서**인가 아니면 **다른 이유**인가?

### 9. 프로퍼티와 변수의 경계 (경계)

- `b.v` 와 `v` 가 콜백 안에서 갈리는 기준을 한 문장으로 댈 수 있는가?

### 10. 판별 유니온이 풀리는 자리 (경계)

- 판별 유니온은 언제 안전하고 언제 풀리는가?

### 11. 12·13·14 와 잇기 (연결)

- 술어([**13번 주제**](../13-type-guards-and-predicates/))와 단언([**14번 주제**](../14-assertion-signatures/))이 만든 좁힘도 같은 한계를 받는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
