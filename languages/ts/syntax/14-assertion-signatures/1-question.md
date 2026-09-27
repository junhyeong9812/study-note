# ts/syntax/14 — 단언 시그니처 `asserts` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 본체는 **「진단 0건」이 답인 블록**이다 —
> 단언의 몸통이 거짓말을 해도 컴파일러는 아무 말도 안 하고, **런타임이 대신 말한다.**
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> ★★ 이 주제는 **네 파일 중 하나만** `--strict false` 에서 갈린다. 그 자리는 **양쪽 판을 다 실었다.**
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. `asserts x is T` 와 `asserts x` 는 각각 어디까지 좁히나 (예측)

```ts
// ex.14a.ts
// asserts x is T 와 asserts x — 좁힘이 호출 뒤 함수 끝까지 이어진다
function assertString(v: unknown): asserts v is string {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
}
function assertTruthy(v: unknown): asserts v {
    if (!v) throw new Error("거짓값이다");
}
declare function touch(): void;

function scopeOfNarrowing(v: unknown) {
    const before: null = v;
    assertString(v);
    const after: null = v;
    touch();
    const afterCall: null = v;
    if (Math.random() > 0.5) {
        const deeper: null = v;
    }
}

function truthyOnUnion(v: string | null | undefined) {
    assertTruthy(v);
    const after: null = v;
}

function truthyKeepsFalsy(v: number | "" | null) {
    assertTruthy(v);
    const after: null = v;
}

function inBranchOnly(v: unknown) {
    if (Math.random() > 0.5) {
        assertString(v);
        const inside: null = v;
    }
    const outside: null = v;
}

function returnsNumber(v: unknown): asserts v is string {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
    return 1;
}
function returnsString(v: unknown): asserts v is string {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
    return "ok";
}
console.log(scopeOfNarrowing, truthyOnUnion, truthyKeepsFalsy, inBranchOnly, returnsNumber, returnsString);
```

- 진단은 **몇 건**이고 어느 줄인가?
- 15행 `const afterCall: null = v;` 와 36행 `const outside: null = v;` 는 어떻게 다른가?
- 41행 `return 1;` 과 45행 `return "ok";` 는 각각 무슨 코드로 막히는가? 그것이 뜻하는 **반환 타입 규칙**은 무엇인가?

### 2. 단언의 몸통이 거짓말을 하면 (예측)

```ts
// ex.14b.ts
// 컴파일러는 단언의 몸통을 검사하지 않는다 — 거짓말하는 단언을 던져서 깨뜨린다
function assertNothing(v: unknown): asserts v is string {}

function assertBackwards(v: unknown): asserts v is string {
    if (typeof v === "string") throw new Error("문자열이면 던진다");
}

function assertNeverReturns(v: unknown): asserts v is string {
    throw new Error("무조건 던진다");
}

function shoutEmpty(v: unknown): string {
    assertNothing(v);
    return v.toUpperCase();
}

function shoutBackwards(v: unknown): string {
    assertBackwards(v);
    return v.toUpperCase();
}

function shoutNever(v: unknown): string {
    assertNeverReturns(v);
    return v.toUpperCase();
}

function run(label: string, f: () => string): void {
    try {
        console.log(label, f());
    } catch (e) {
        console.log(label, "터졌다 ->", (e as Error).message);
    }
}

run("shoutEmpty('hi')    :", () => shoutEmpty("hi"));
run("shoutEmpty(7)       :", () => shoutEmpty(7));
run("shoutBackwards(7)   :", () => shoutBackwards(7));
run("shoutBackwards('hi'):", () => shoutBackwards("hi"));
run("shoutNever('hi')    :", () => shoutNever("hi"));
```

- `tsc` 의 **종료 코드와 진단 건수**는 무엇인가?
- 다섯 줄의 실행 출력은 각각 무엇인가?
- 이 주제에서 **컴파일러가 검사하지 않는 것**은 정확히 무엇인가?

### 3. 어떤 이름으로 부르면 막히나 (예측)

```ts
// ex.14c.ts
// TS2775 — 단언 호출은 「부르는 이름 전부」에 명시적 타입 표기를 요구한다
type Asserter = (v: unknown) => asserts v is string;

function declaredFn(v: unknown): asserts v is string {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
}
const bareArrow = (v: unknown): asserts v is string => {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
};
const typedArrow: Asserter = (v) => {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
};
declare const declaredConst: Asserter;
const bareObj = {
    go(v: unknown): asserts v is string {
        if (typeof v !== "string") throw new Error("문자열이 아니다");
    },
};
const typedObj: { go: Asserter } = {
    go(v: unknown): asserts v is string {
        if (typeof v !== "string") throw new Error("문자열이 아니다");
    },
};
class Guard {
    static go(v: unknown): asserts v is string {
        if (typeof v !== "string") throw new Error("문자열이 아니다");
    }
}

function useDeclaredFn(v: unknown) {
    declaredFn(v);
    const r: null = v;
}
function useBareArrow(v: unknown) {
    bareArrow(v);
    const r: null = v;
}
function useTypedArrow(v: unknown) {
    typedArrow(v);
    const r: null = v;
}
function useDeclaredConst(v: unknown) {
    declaredConst(v);
    const r: null = v;
}
function useBareObj(v: unknown) {
    bareObj.go(v);
    const r: null = v;
}
function useTypedObj(v: unknown) {
    typedObj.go(v);
    const r: null = v;
}
function useClassStatic(v: unknown) {
    Guard.go(v);
    const r: null = v;
}
console.log(useDeclaredFn, useBareArrow, useTypedArrow, useDeclaredConst, useBareObj, useTypedObj, useClassStatic);
```

- 일곱 자리 중 **`TS2775` 로 막히는 것은 몇 개**이고 어느 것인가?
- 막힌 자리에서 `v` 는 무슨 타입이 되는가?
- `bareObj.go(v)` 는 막히는데 `Guard.go(v)` 는 통과한다 — 그 기준은 무엇인가?

### 4. `asserts this` 와 술어의 대비 (예측)

```ts
// ex.14d.ts
// asserts this is T · 제네릭 단언 · 술어와의 대비
function assertDefined<T>(v: T): asserts v is NonNullable<T> {
    if (v === null || v === undefined) throw new Error("없다");
}
class Loaded {
    data: string | null = null;
    assertLoaded(): asserts this is { data: string } {
        if (this.data === null) throw new Error("아직 없다");
    }
}

function useGeneric(v: string | null | undefined) {
    assertDefined(v);
    const r: null = v;
}
function useThis(box: Loaded) {
    const before: null = box.data;
    box.assertLoaded();
    const after: null = box.data;
}

// 같은 검사를 술어로 · 단언으로 — 무엇이 갈리나
function isString(v: unknown): v is string {
    return typeof v === "string";
}
function assertString(v: unknown): asserts v is string {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
}
function byPredicate(v: unknown) {
    if (isString(v)) {
        const inside: null = v;
    }
    const outside: null = v;
}
function byAssertion(v: unknown) {
    assertString(v);
    const after: null = v;
}

// 단언 뒤 재대입하면 좁힘이 풀린다
function afterReassign(v: unknown) {
    assertString(v);
    const before: null = v;
    v = 1;
    const after: null = v;
}
console.log(useGeneric, useThis, byPredicate, byAssertion, afterReassign);
```

- 진단은 **몇 건**인가?
- 31행(술어)과 37행(단언)은 **좁힘의 범위**가 어떻게 다른가?
- 45행 `const after: null = v;` 는 무슨 타입인가?

### 5. 단언 대상에 프로퍼티를 적으면 (예측)

```ts
// ex.14e.ts
// 단언 대상은 매개변수 이름이나 this 여야 한다 — 프로퍼티는 문법이 아니다
function assertProp(o: { v: unknown }): asserts o.v is string {
    if (typeof o.v !== "string") throw new Error("문자열이 아니다");
}
```

- 진단은 **몇 건**이고, **`TSxxxx` 코드 네 개**는 무엇인가?
- 이것은 타입 오류인가 **문법 오류**인가?

### 6. `node:assert` 는 어떤 꼴인가 (예측)

```ts
// node-assert.d.ts
// @types/node 가 없으므로 이 배치가 쓰는 만큼만 직접 선언한다
declare module "node:assert" {
    function assert(value: unknown, message?: string): asserts value;
    export = assert;
}
```

```ts
// ex.14f.ts
// node:assert 는 asserts value 다 — is T 가 없고, 검사는 런타임이 진짜로 한다
import assert = require("node:assert");

function widen(v: string | number | null) {
    const before: null = v;
    assert(v);
    const after: null = v;
}

function run(label: string, f: () => void): void {
    try {
        f();
        console.log(label, "통과");
    } catch (e) {
        console.log(label, "던졌다 ->", (e as Error).message);
    }
}
run("assert(1)    :", () => assert(1));
run("assert(0)    :", () => assert(0));
run("assert('')   :", () => assert("", "빈 문자열이다"));
run("assert(null) :", () => assert(null, "널이다"));
console.log(widen);
```

- 선언 파일 없이 던지면 **무슨 코드**가 나오는가?
- 5행과 7행의 탐침은 각각 무슨 타입을 말하는가?
- 같은 입력을 `--noEmit` 으로 한 번, 방출하며 한 번 던지면 **종료 코드가 어떻게 갈리는가**?

### 7. 왜 `asserts` 의 반환 타입은 `void` 여야 하나 (왜)

- 1번의 41·45행이 낸 진단을 근거로 **한 문장**으로 댈 수 있는가?

### 8. 왜 `TS2775` 라는 제약이 있나 (왜)

- 3번의 격자를 근거로 「**왜 이름에 타입 표기를 요구하는가**」를 설명할 수 있는가?

### 9. 술어와 단언의 경계 (경계)

- [**13번 주제**](../13-type-guards-and-predicates/)의 `x is T` 와 견주어 **무엇이 더 위험하고 왜 그런가**?

### 10. `node:assert` 와 `asserts` 의 경계 (경계)

- 「표준 라이브러리의 `assert`」와 「타입 시스템의 `asserts`」가 각각 **무엇을 책임지는가**?

### 11. 13·15 와 잇기 (연결)

- 단언이 만든 좁힘도 [**15번 주제**](../15-control-flow-analysis-limits/)의 한계를 그대로 받는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
