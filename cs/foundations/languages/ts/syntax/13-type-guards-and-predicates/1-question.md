# ts/syntax/13 — 타입 가드와 타입 술어 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 본체는 **「진단 0건」이 답인 블록**이다 —
> 술어가 거짓말을 해도 컴파일러는 아무 말도 안 하고, **런타임이 대신 말한다.**
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> ★★ 이 주제는 **네 파일 중 하나만** `--strict false` 에서 갈린다. 그 자리는 **양쪽 판을 다 실었다.**
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. `x is T` 는 `in` 을 그대로 쓰는 것과 무엇이 다른가 (예측)

```ts
// ex.13a.ts
// x is T 술어 함수 — in 연산자로 좁히는 것과 무엇이 다른가
interface Cat {
    kind: string;
    meow(): void;
}
interface Dog {
    kind: string;
    bark(): void;
}

function isCat(p: Cat | Dog): p is Cat {
    return "meow" in p;
}

function byPredicate(p: Cat | Dog) {
    if (isCat(p)) {
        const inCat: null = p;
    } else {
        const inDog: null = p;
    }
}

function byInInline(p: Cat | Dog) {
    if ("meow" in p) {
        const inCat: null = p;
    } else {
        const inDog: null = p;
    }
}

function wrapped(p: Cat | Dog): boolean {
    return "meow" in p;
}
function byWrapped(p: Cat | Dog) {
    if (wrapped(p)) {
        const notNarrowed: null = p;
    }
}

function isCatLoose(p: unknown): p is Cat {
    return typeof p === "object" && p !== null && "meow" in p;
}
declare const u: unknown;
if (isCatLoose(u)) {
    const fromUnknown: null = u;
}

function returnsNumber(p: Cat | Dog): p is Cat {
    return 1;
}
console.log(byPredicate, byInInline, byWrapped, returnsNumber);
```

- 진단은 **몇 건**이고 어느 줄인가?
- 36행 `const notNarrowed: null = p;` 는 좁혀지는가? 17행과 무엇이 다른가?
- 49행 `return 1;` 은 어느 코드로 막히는가? 컴파일러가 술어 함수에 **요구하는 것**은 무엇인가?

### 2. 술어가 거짓말을 하면 (예측)

```ts
// ex.13b.ts
// 술어가 거짓말을 해도 컴파일러는 믿는다 — 던져서 런타임에 깨뜨린다
type Unknowable = unknown;

function isString(v: Unknowable): v is string {
    return typeof v === "number";
}
function alwaysTrue(v: Unknowable): v is string {
    return true;
}

function shout(v: Unknowable): string {
    if (isString(v)) {
        return v.toUpperCase();
    }
    return "문자열이 아니다";
}

function shoutHard(v: Unknowable): string {
    if (alwaysTrue(v)) {
        return v.toUpperCase();
    }
    return "닿지 않는다";
}

function run(label: string, f: () => string): void {
    try {
        console.log(label, f());
    } catch (e) {
        console.log(label, "터졌다 ->", (e as Error).message);
    }
}

run("shout('hi')  :", () => shout("hi"));
run("shout(7)     :", () => shout(7));
run("shoutHard(7) :", () => shoutHard(7));
run("shoutHard('a'):", () => shoutHard("a"));
```

- `tsc` 의 **종료 코드와 진단 건수**는 무엇인가?
- `shout("hi")` 는 무엇을 찍는가? `shout(7)` 은?
- 이 주제에서 **컴파일러가 검사하지 않는 것**은 정확히 무엇인가?

### 3. `asserts x is T` 는 어디서 걸리나 (예측)

```ts
// ex.13c.ts
// asserts x is T — 돌아오면 좁혀져 있다. 다만 부르는 이름에 조건이 붙는다
function assertString(v: unknown): asserts v is string {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
}
function assertDefined<T>(v: T): asserts v is NonNullable<T> {
    if (v === null || v === undefined) throw new Error("없다");
}

function useDeclared(v: unknown) {
    assertString(v);
    const after: null = v;
}

function useGeneric(v: string | null | undefined) {
    assertDefined(v);
    const after: null = v;
}

const assertArrow = (v: unknown): asserts v is string => {
    if (typeof v !== "string") throw new Error("문자열이 아니다");
};
function useArrow(v: unknown) {
    assertArrow(v);
    const after: null = v;
}

const assertTyped: (v: unknown) => asserts v is string = assertArrow;
function useTyped(v: unknown) {
    assertTyped(v);
    const after: null = v;
}

function assertNothing(v: unknown): asserts v is string {
    return;
}
function useLying(v: unknown) {
    assertNothing(v);
    const after: string = v;
}
console.log(useDeclared, useGeneric, useArrow, useTyped, useLying);
```

- 진단은 **몇 건**이고, 그중 **`TS2322` 가 아닌 것**은 무엇인가?
- 23행 `assertArrow(v);` 와 29행 `assertTyped(v);` 는 왜 다른가?
- 38행 `const after: string = v;` 는 통과하는가?

### 4. 술어를 안 적어도 좁혀지나 (예측)

```ts
// ex.13d.ts
// 술어를 안 적어도 좁혀지나 — 5.5 의 추론된 타입 술어를 이 판에 던진다
function isStr(v: string | number) {
    return typeof v === "string";
}
const isStrArrow = (v: string | number) => typeof v === "string";

function useDeclared(v: string | number) {
    if (isStr(v)) {
        const inThen: null = v;
    } else {
        const inElse: null = v;
    }
}

function useArrow(v: string | number) {
    if (isStrArrow(v)) {
        const inThen: null = v;
    }
}

function notNull<T>(v: T | null) {
    return v !== null;
}
const filtered = [1, null, 2].filter(notNull);
const inline = [1, null, 2].filter((v) => v !== null);
const p1: null = filtered;
const p2: null = inline;

function negated(v: string | number) {
    return typeof v !== "string";
}
function useNegated(v: string | number) {
    if (negated(v)) {
        const inThen: null = v;
    } else {
        const inElse: null = v;
    }
}
console.log(useDeclared, useArrow, p1, p2, useNegated);
```

- TS 5.5 의 **추론된 타입 술어**가 이 판(7.0.2)에서 **도는가**?
- `[1, null, 2].filter(notNull)` 은 무엇으로 답하는가?
- `negated` 의 참·거짓 갈래는 각각 무엇인가?

### 5. 추론은 언제 붙고 언제 안 붙나 (예측)

```ts
// ex.13e.ts
// 추론은 언제 붙고 언제 안 붙나 — 여덟 모양을 나란히 던진다
function explicitBool(v: string | number): boolean {
    return typeof v === "string";
}
function multiReturn(v: string | number) {
    if (typeof v === "string") return true;
    return false;
}
function reassigned(v: string | number) {
    if (typeof v === "string") return true;
    v = 1;
    return false;
}
function viaOther(v: string | number) {
    const w = v;
    return typeof w === "string";
}
function withExtraTest(v: string | number) {
    return typeof v === "string" && v.length > 0;
}
function viaConstAlias(v: string | number) {
    const ok = typeof v === "string";
    return ok;
}
function viaAnd(v: string | number | null) {
    return v !== null && typeof v === "string";
}
declare function declaredOnly(v: string | number): boolean;

function use(v: string | number, w: string | number | null) {
    if (explicitBool(v)) {
        const a: null = v;
    }
    if (multiReturn(v)) {
        const b: null = v;
    }
    if (reassigned(v)) {
        const c: null = v;
    }
    if (viaOther(v)) {
        const d: null = v;
    }
    if (withExtraTest(v)) {
        const e: null = v;
    }
    if (viaConstAlias(v)) {
        const f: null = v;
    }
    if (viaAnd(w)) {
        const g: null = w;
    }
    if (declaredOnly(v)) {
        const h: null = v;
    }
}
console.log(use);
```

- 여덟 모양 중 **좁혀지는 것은 몇 개**이고 어느 것인가?
- `viaOther` 와 `viaConstAlias` 는 왜 갈리는가?
- 같은 파일을 `--strict false` 로 던지면 **어느 줄이 바뀌는가**?

### 6. `unknown` 을 받아 좁히면 (예측)

```ts
// ex.13f.ts
// unknown 을 받아 좁히는 관용구 — 술어의 본문이 곧 런타임 검사다
interface User {
    id: number;
    name: string;
}

function isUser(v: unknown): v is User {
    return (
        typeof v === "object" &&
        v !== null &&
        "id" in v &&
        typeof (v as { id: unknown }).id === "number" &&
        "name" in v &&
        typeof (v as { name: unknown }).name === "string"
    );
}

function greet(raw: unknown): string {
    if (isUser(raw)) {
        return `안녕 ${raw.name}(#${raw.id})`;
    }
    return "모르는 모양이다";
}

console.log("정상      :", greet(JSON.parse('{"id":1,"name":"준"}')));
console.log("필드 빠짐  :", greet(JSON.parse('{"id":1}')));
console.log("타입 어긋남:", greet(JSON.parse('{"id":"1","name":"준"}')));
console.log("null      :", greet(null));
console.log("배열      :", greet(JSON.parse("[1,2]")));
```

- `tsc` 의 종료 코드는 무엇인가?
- 다섯 가지 입력(정상·필드 빠짐·타입 어긋남·`null`·배열)에 각각 무엇을 찍는가?

### 7. 왜 컴파일러는 술어를 검사하지 않나 (왜)

- 본문을 검사하지 **않는** 것이 게으름이 아니라 **설계**인 이유를 한 문장으로 댈 수 있는가?

### 8. 왜 `in` 을 함수로 감싸면 좁히기가 끊기나 (왜)

- 1번의 36행과 [**12번 주제**](../12-narrowing/)의 「좁히기는 제어 흐름을 따른다」를 이어 설명할 수 있는가?

### 9. 술어 함수와 `asserts` 의 경계 (경계)

- 둘이 **무엇을 다르게 하고** 어느 쪽이 더 위험한가?

### 10. 추론된 술어를 믿어도 되는 자리 (경계)

- 5번의 격자를 근거로 「**술어 표기를 언제 직접 적어야 하는가**」를 말할 수 있는가?

### 11. 04·12 와 잇기 (연결)

- `unknown` 으로 받아 좁히는 설계(04)와 좁히기 수단(12)이 여기서 어떻게 합쳐지는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
