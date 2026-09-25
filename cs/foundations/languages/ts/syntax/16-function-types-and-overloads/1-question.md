# ts/syntax/16 — 함수 타입과 오버로드 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 본체는 「**구현 시그니처는 밖에서 안 보인다**」이고,
> 그것을 **탐침이 뱉은 타입 글자**와 **`.d.ts` 전문** 둘로 접지했다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> ★★ 이 주제는 **네 파일 전부** `--strict false` 에서 **글자 하나까지 같다.** 그 대조도 블록으로 실었다.
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 오버로드된 함수의 타입은 무엇인가 (예측)

```ts
// ex.16a.ts
// 오버로드 시그니처와 구현 시그니처 — 구현 시그니처는 밖에서 안 보인다
function len(x: string): number;
function len(x: unknown[]): number;
function len(x: string | unknown[]): number {
    return x.length;
}

const byString = len("abc");
const byArray = len([1, 2]);
const p1: null = byString;

declare const either: string | unknown[];
const byUnion = len(either);

function overloadCount(x: string): 1;
function overloadCount(x: number): 2;
function overloadCount(x: boolean): 3;
function overloadCount(x: string | number | boolean): 1 | 2 | 3 {
    if (typeof x === "string") return 1;
    if (typeof x === "number") return 2;
    return 3;
}
const p2: null = overloadCount(true);
const p3: null = len;
console.log(byArray, byUnion, p1, p2, p3);
```

- 진단은 **몇 건**이고 어느 줄인가?
- 13행 `len(either)` 는 통과하는가? 무슨 코드가 나오는가?
- 24행 `const p3: null = len;` 이 뱉는 타입 글자에 **몇 개의 시그니처**가 들어 있는가?

### 2. 어느 오버로드가 골라지나 (예측)

```ts
// ex.16b.ts
// 오버로드 해석은 선언 순서다 — 같은 몸통을 순서만 바꿔 둘로 둔다
function wideFirst(x: string | number): "넓은 쪽";
function wideFirst(x: string): "좁은 쪽";
function wideFirst(x: string | number): string {
    return typeof x === "string" ? "좁은 쪽" : "넓은 쪽";
}
function narrowFirst(x: string): "좁은 쪽";
function narrowFirst(x: string | number): "넓은 쪽";
function narrowFirst(x: string | number): string {
    return typeof x === "string" ? "좁은 쪽" : "넓은 쪽";
}
const r1: null = wideFirst("a");
const r2: null = narrowFirst("a");

// 인자 개수로 갈리는 오버로드
function make(): "인자 없음";
function make(a: number): "하나";
function make(a: number, b: number): "둘";
function make(a?: number, b?: number): string {
    if (a === undefined) return "인자 없음";
    if (b === undefined) return "하나";
    return "둘";
}
const r3: null = make();
const r4: null = make(1);
const r5: null = make(1, 2);

// 선택 매개변수가 있는 하나짜리 시그니처와 비교
function make2(a?: number, b?: number): "하나로 다 받는다" {
    return "하나로 다 받는다";
}
const r6: null = make2();
console.log(r1, r2, r3, r4, r5, r6);
```

- 12행과 13행은 각각 무슨 리터럴 타입을 뱉는가?
- 두 함수는 몸통이 같은데 왜 다른 답이 나오는가?
- 24·25·26행과 32행을 견주면 **오버로드와 선택 매개변수**는 무엇이 다른가?

### 3. 구현 시그니처가 오버로드를 못 덮으면 (예측)

```ts
// ex.16c.ts
// 구현 시그니처는 모든 오버로드를 덮어야 한다 — 그리고 바로 뒤에 붙어야 한다
function notCovered(x: string): number;
function notCovered(x: boolean): number;
function notCovered(x: string): number {
    return 1;
}
function returnNotCovered(x: string): string;
function returnNotCovered(x: number): number;
function returnNotCovered(x: string | number): string {
    return String(x);
}
function covered(x: string): string;
function covered(x: number): number;
function covered(x: string | number): string | number {
    return x;
}
function interrupted(x: string): number;
const between = 1;
function interrupted(x: number): string;
function interrupted(x: string | number): string | number {
    return x;
}
console.log(notCovered, returnNotCovered, covered, interrupted, between);
```

- 진단은 **몇 건**이고 **코드 두 가지**는 무엇인가?
- 3행과 8행은 각각 **매개변수**와 **반환 타입** 중 무엇이 문제인가?
- 17행은 왜 다른 코드가 나오는가?

### 4. `.d.ts` 에 무엇이 실리나 (예측)

```ts
// ex.16d.ts
// 함수 타입 표기 세 꼴 + .d.ts 에 오버로드가 어떻게 실리나
export function len(x: string): number;
export function len(x: unknown[]): number;
export function len(x: string | unknown[]): number {
    return x.length;
}

export type ArrowStyle = (x: string) => number;
export interface CallSignature {
    (x: string): number;
    (x: number): string;
}
export interface MethodStyle {
    run(x: string): number;
}
export interface PropertyStyle {
    run: (x: string) => number;
}
export interface Overloaded {
    run(x: string): number;
    run(x: number): string;
}
export const arrow = (x: string): number => x.length;
export const asCallSig: CallSignature = ((x: string | number) =>
    typeof x === "string" ? x.length : String(x)) as CallSignature;

export class Holder {
    run(x: string): number;
    run(x: number): string;
    run(x: string | number): string | number {
        return typeof x === "string" ? x.length : String(x);
    }
}
```

- `tsc` 의 종료 코드는 무엇인가?
- `.d.ts` 에서 **사라지는 것**은 무엇인가?
- 메서드 문법(`run(x): number`)과 프로퍼티 문법(`run: (x) => number`)은 `.d.ts` 에서 어떻게 되는가?

### 5. 오버로드와 유니온 매개변수 (예측)

```ts
// ex.16e.ts
// 오버로드 대 유니온 매개변수 — 무엇이 갈리나. 그리고 세 표기가 서로 대입되나
function overloaded(x: string): string;
function overloaded(x: number): number;
function overloaded(x: string | number): string | number {
    return x;
}
function unioned(x: string | number): string | number {
    return x;
}
const o1: null = overloaded("a");
const u1: null = unioned("a");

interface MethodStyle {
    run(x: string): number;
}
interface PropertyStyle {
    run: (x: string) => number;
}
interface CallSignature {
    (x: string): number;
}
type ArrowStyle = (x: string) => number;

declare const ms: MethodStyle;
declare const ps: PropertyStyle;
const x1: PropertyStyle = ms;
const x2: MethodStyle = ps;
declare const cs: CallSignature;
declare const ar: ArrowStyle;
const x3: ArrowStyle = cs;
const x4: CallSignature = ar;

// 오버로드된 함수를 한 꼴짜리 타입에 담으면
type OneShape = (x: string) => string;
const x5: OneShape = overloaded;
type WrongShape = (x: boolean) => boolean;
const x6: WrongShape = overloaded;
console.log(o1, u1, x1, x2, x3, x4, x5, x6);
```

- 진단은 **몇 건**이고 어느 줄인가?
- 10행과 11행이 뱉는 타입은 어떻게 다른가?
- 26·27행(메서드 대 프로퍼티)과 30·31행(호출 시그니처 대 화살표)은 통과하는가?

### 6. 방출된 JS 에 무엇이 남나 (예측)

```ts
// ex.16f.ts
// 방출된 JS 에 오버로드는 한 글자도 안 남는다 — 갈래는 몸통이 직접 판다
function format(x: string): string;
function format(x: number): string;
function format(x: Date): string;
function format(x: string | number | Date): string {
    if (typeof x === "string") return `문자열 ${x}`;
    if (typeof x === "number") return `숫자 ${x.toFixed(1)}`;
    return `날짜 ${x.toISOString().slice(0, 10)}`;
}

class Repo {
    find(id: number): string;
    find(name: string): string;
    find(key: number | string): string {
        return typeof key === "number" ? `#${key}` : `@${key}`;
    }
}

console.log("format('a')  :", format("a"));
console.log("format(1.5)  :", format(1.5));
console.log("format(날짜) :", format(new Date(0)));
const repo = new Repo();
console.log("find(7)      :", repo.find(7));
console.log("find('준')   :", repo.find("준"));
```

- 방출된 `.js` 에 오버로드 시그니처는 **몇 줄** 남는가?
- 다섯 줄의 실행 출력은 각각 무엇인가?

### 7. 왜 구현 시그니처는 호출 가능하지 않나 (왜)

- 1번 13행과 24행을 근거로 **한 문장**으로 댈 수 있는가?

### 8. 왜 해석 순서가 선언 순서인가 (왜)

- 2번을 근거로 「**왜 가장 잘 맞는 것을 고르지 않는가**」를 설명할 수 있는가?

### 9. 오버로드와 유니온의 경계 (경계)

- 언제 오버로드를 쓰고 언제 유니온 매개변수 하나로 끝내는가?

### 10. 메서드 문법과 프로퍼티 문법의 경계 (경계)

- `.d.ts` 가 둘을 **다르게 싣는다**는 사실이 [**17번 주제**](../17-variance-and-parameter-compatibility/)에서 무엇을 뜻하는가?

### 11. 03·13·17 과 잇기 (연결)

- 함수 타입 표기 세 꼴이 [**03번 주제**](../03-basic-type-annotations/)·[**13번 주제**](../13-type-guards-and-predicates/)·[**17번 주제**](../17-variance-and-parameter-compatibility/)와 어떻게 이어지는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
