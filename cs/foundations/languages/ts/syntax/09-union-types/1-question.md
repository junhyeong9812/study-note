# ts/syntax/09 — 유니온 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제에서는 「**에러가 안 나는 줄**」까지 세야 답이다 —
> 탐침 열 개에 진단이 아홉 건인 블록이 있고, **빠진 하나가 답**이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 좁히지 않고 멤버를 부르면 (예측)

```ts
// ex.09a.ts
// 유니온 값에서 쓸 수 있는 멤버는 어디까지인가
type SN = string | number;
declare const v: SN;

const shared = v.toString();
const onlyNumber = v.toFixed(2);
const onlyString = v.length;

interface Bird {
    name: string;
    fly(): void;
}
interface Fish {
    name: string;
    swim(): void;
}
declare const pet: Bird | Fish;

const common = pet.name;
pet.fly();

const putString: SN = "s";
const putNumber: SN = 1;
const putBoolean: SN = true;
console.log(shared, onlyNumber, onlyString, common, putString, putNumber, putBoolean);
```

- 진단은 **몇 건**이고 **어느 줄**인가?
- 세 `TS2339` 의 **들여쓴 줄**이 각각 어느 타입 이름을 짚는가?
- `const putBoolean: SN = true;` 는 어느 쪽인가?

### 2. 열 가지 유니온을 컴파일러에게 캐물으면 (예측)

```ts
// ex.09b.ts
// 적은 대로 남나 — 컴파일러에게 유니온의 실제 모양을 캐묻는다
declare const dup: string | number | string;
declare const withNever: string | never | number;
declare const withLiteral: "x" | "y" | string;
declare const bools: true | false;
declare const reordered: number | string;
declare const nestedUnion: (string | number) | (number | boolean);
declare const nullish: string | undefined | null;
declare const withAny: string | any;
declare const withUnknown: string | unknown;
declare const sortedLiterals: 3 | 1 | 2;

const p1: null = dup;
const p2: null = withNever;
const p3: null = withLiteral;
const p4: null = bools;
const p5: null = reordered;
const p6: null = nestedUnion;
const p7: null = nullish;
const p8: null = withAny;
const p9: null = withUnknown;
const p10: null = sortedLiterals;
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10);
```

- 탐침이 **열 개**인데 진단은 **몇 건**인가? 빠진 것은 어느 줄이고 왜인가?
- `"x" | "y" | string` · `true | false` · `3 | 1 | 2` 는 각각 무엇으로 답하는가?
- `number | string` 은 적은 순서 그대로 답하는가?

### 3. 같은 선언을 `.d.ts` 로 뽑으면 (예측)

```ts
// ex.09e.ts
// 선언 방출은 유니온을 적은 대로 되돌려 준다
export type Dup = string | number | string;
export type WithNever = string | never | number;
export type Reordered = number | string;
export type Bools = true | false;
export type Literals = 3 | 1 | 2;
export const fromLiteral = "circle";
export let widened = "circle";
export const picked: "a" | "b" = "a";
```

- `.d.ts` 가 `string | number | string` 을 **정규화해서** 적는가?
- `export let widened = "circle";` 는 어떻게 나오는가?

### 4. 함수와 배열을 유니온으로 묶으면 (예측)

```ts
// ex.09c.ts
// 유니온이 함수나 배열이면 — 매개변수 자리가 뒤집힌다
type Handler = ((a: string) => void) | ((a: number) => void);
declare const h: Handler;
h("s");
h(1);

declare const arr: string[] | number[];
arr.push("s");
const mapped = arr.map((x) => x);
const len = arr.length;

type Getter = (() => string) | (() => number);
declare const g: Getter;
const got: null = g();
console.log(mapped, len, got);
```

- 진단은 **몇 건**이고 `h("s")` 와 `h(1)` 은 각각 어느 쪽인가?
- 진단이 말하는 **매개변수 타입**은 무엇인가?
- `const got: null = g();` 이 말하는 반환 타입은 무엇인가?

### 5. 판별 필드를 두고 한 갈래를 빠뜨리면 (예측)

```ts
// ex.09d.ts
// 판별 필드를 둔 유니온 — 분기마다 무엇이 남나
interface Circle {
    kind: "circle";
    r: number;
}
interface Square {
    kind: "square";
    side: number;
}
interface Tri {
    kind: "tri";
    base: number;
    h: number;
}
type Shape = Circle | Square | Tri;

function area(s: Shape): number {
    switch (s.kind) {
        case "circle":
            return 3 * s.r * s.r;
        case "square":
            return s.side * s.side;
        default: {
            const exhaustive: never = s;
            return exhaustive;
        }
    }
}

interface Ok {
    ok: true;
    data: string;
}
interface Err {
    ok: false;
    reason: string;
}
type Res = Ok | Err;

function read(r: Res) {
    if (r.ok) return r.data;
    return r.reason;
}
function readBad(r: Res) {
    return r.data;
}
console.log(area({ kind: "circle", r: 1 }), read({ ok: true, data: "d" }), readBad({ ok: true, data: "d" }));
```

- 진단은 **몇 건**이고, `const exhaustive: never = s;` 의 진단은 **무엇을 이름으로** 짚는가?
- `if (r.ok)` 로 갈린 두 갈래에서 `r.data` 와 `r.reason` 은 각각 통과하는가?

### 6. 방출된 JS 에 유니온이 남나 (예측)

```ts
// ex.09f.ts
// 유니온은 방출에 한 글자도 안 남는다 — 갈라 쓰는 일은 JS 연산자가 한다
type Shape = { kind: "circle"; r: number } | { kind: "square"; side: number };

function area(s: Shape): number {
    if (s.kind === "circle") return 3 * s.r * s.r;
    return s.side * s.side;
}

function describe(v: string | number): string {
    return typeof v === "string" ? `문자열 ${v.length}자` : `숫자 ${v.toFixed(1)}`;
}

console.log("circle    :", area({ kind: "circle", r: 2 }));
console.log("square    :", area({ kind: "square", side: 3 }));
console.log("describe  :", describe("abc"), "/", describe(4));
console.log("런타임 구분:", typeof "abc", typeof 4);
```

- 방출된 파일에서 `type Shape` 선언은 어떻게 되는가?
- 좁히기를 실제로 하는 코드는 무엇으로 남는가?

### 7. 왜 교집합만 쓸 수 있나 (왜)

- 꺼내는 방향과 넣는 방향이 **반대로** 넓은 이유를 한 문장으로 댈 수 있는가?

### 8. 함수 유니온이 못 쓰이는 이유 (왜)

- 매개변수가 `never` 가 되는 것을 **7번의 이유**로 설명할 수 있는가?

### 9. 두 창이 다른 답을 주는 자리 (경계)

- `.d.ts` 덤프와 `null` 탐침이 **다른 답**을 줄 때, 각각이 무엇을 말하는 것인가?

### 10. 리터럴 유니온이 조용히 무너지는 자리 (경계)

- `"asc" | "desc" | string` 이 왜 위험한지, 어느 실행 결과에 기대어 말할 수 있는가?

### 11. 전수 검사의 조건 (연결)

- `never` 전수 검사가 **작동하려면** 유니온 쪽에 무엇이 있어야 하는가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 각각 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
