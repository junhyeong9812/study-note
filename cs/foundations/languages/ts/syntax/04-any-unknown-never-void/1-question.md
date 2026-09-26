# ts/syntax/04 — `any`·`unknown`·`never`·`void` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ 이 주제에서 예측할 것은 「**어느 칸이 막히나**」다 —
> 「막힌다」가 아니라 「**몇 칸이 막히고 어느 칸인가**」까지 적어야 답이다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. ★★ **`strict` 가 기본 `true`** 인 판이다 —
> `strictNullChecks` 가 꺼지면 아래 격자가 통째로 달라진다. 모든 블록은 `--pretty false` 다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 타입을 서로 대입하면 (예측)

```ts
// ex.04a.ts
// 네 타입 × 네 타입 = 16칸. 한 줄에 네 칸씩 늘어놓는다
declare let a: any;
declare let u: unknown;
declare let n: never;
declare let v: void;

a = a; a = u; a = n; a = v;
u = a; u = u; u = n; u = v;
n = a; n = u; n = n; n = v;
v = a; v = u; v = n; v = v;
```

- 16칸 중 **막히는 칸은 몇이고 어디**인가? 표를 채워 보라.
- 진단은 **몇 줄**로 나오는가?

### 2. 좁히기 전과 후 (예측)

```ts
// ex.04b.ts
// unknown 은 받아 놓고 좁히기 전에는 아무것도 못 하게 한다
declare const u: unknown;

u.length;
u();
u + 1;
const s: string = u;

if (typeof u === "string") {
    console.log(u.length);
}
if (typeof u === "object" && u !== null && "id" in u) {
    console.log(u.id);
}
if (Array.isArray(u)) {
    console.log(u.length);
}
```

- 진단은 **몇 건**이고 **에러 코드**는 무엇인가?
- `if` 블록 **셋** 중 진단이 나는 것이 있는가?

### 3. 한 줄에서 시작한 값이 어디까지 가나 (예측)

```ts
// ex.04c.ts
// any 는 옆으로 번진다 — unknown 은 그 자리에서 멈춘다
declare const a: any;
export const b = a.foo.bar;
export const c = b + 1;
export const asString: string = c;
export const asNumber: number = c;

declare const u: unknown;
export const d = u;
```

- 이 파일의 **종료 코드**는 몇인가?
- `.d.ts` 에서 `b`·`c`·`asString`·`asNumber`·`d` 다섯 줄을 적어 보라 — **한 값이 두 타입에 다 들어가는 자리**가 있는가?

### 4. `never` 가 붙는 다섯 자리 (예측)

```ts
// ex.04e.ts
// never 가 생기는 네 자리를 한 파일에 모았다
export function fail(msg: string): never {
    throw new Error(msg);
}
export const arrow = () => {
    throw new Error("x");
};
export function declared() {
    throw new Error("x");
}
export type Both = { a: string } & { a: number };
export type Empty = Extract<"a" | "b", "c">;
export const emptyArr: never[] = [];

export function narrow(v: string | number) {
    if (typeof v === "string") return "문자열";
    if (typeof v === "number") return "숫자";
    return v;
}
```

- `.d.ts` 에서 `arrow` 와 `declared` 의 반환 타입은 각각 무엇인가 — **같은 몸통인데 갈리는가**?
- `narrow` 의 반환 타입은 무엇인가?

### 5. 갈래를 하나 더하면 (예측)

```ts
// ex.04f.ts
// 판별 유니온의 완전성 검사 — 한 갈래를 더하면 어디가 깨지나
type Shape = { kind: "circle"; r: number } | { kind: "square"; s: number };
type Shape2 = Shape | { kind: "tri"; b: number; h: number };

function area(sh: Shape): number {
    switch (sh.kind) {
        case "circle":
            return 3 * sh.r * sh.r;
        case "square":
            return sh.s * sh.s;
        default: {
            const rest: never = sh;
            return rest;
        }
    }
}

function area2(sh: Shape2): number {
    switch (sh.kind) {
        case "circle":
            return 3 * sh.r * sh.r;
        case "square":
            return sh.s * sh.s;
        default: {
            const rest: never = sh;
            return rest;
        }
    }
}

console.log(area({ kind: "circle", r: 1 }), area2({ kind: "tri", b: 1, h: 2 }));
```

- 두 함수 중 **진단이 나는 쪽**은 어디이고, 문구가 **무엇을 알려 주는가**?
- 왜 이 관용구를 `const rest: null = sh;` 로는 만들 수 없는가?

### 6. `void` 반환 콜백에 값을 돌려주면 (예측)

```ts
// ex.04g.ts
// void 가 반환 위치에서만 느슨해지는 자리
type Cb = () => void;

const cb: Cb = () => 42;
const got = cb();

function direct(): void {
    return 42;
}

const names: string[] = [];
const ids = [1, 2, 3];
ids.forEach((n) => names.push(String(n)));

console.log("cb() 의 정적 타입은 void, 실제 값은:", got);
console.log("names:", names, "| direct:", typeof direct);
```

- 진단은 **몇 건**이고 **어느 줄**인가 — `const cb: Cb = () => 42;` 는 통과하는가?
- `node` 로 돌리면 `cb()` 의 값이 무엇으로 찍히는가?

### 7. 방출에는 무엇이 남나 (경계)

- `: any`·`: unknown`·`: never`·`: void` 중 방출된 `.js` 에 **흔적을 남기는 것**이 있는가?
- 그렇다면 `typeof` 로 네 타입을 구별할 수 있는가?

### 8. `any` 와 `unknown` (왜)

- 둘 다 「무엇이든 받는다」인데 **왜 `unknown` 을 권하는지** 한 문장으로 답하고, 그 근거를 3번의 `.d.ts` 에서 댈 수 있는가?

### 9. `void` 와 `undefined` (경계)

- 둘 사이의 대입은 **양방향인가 한 방향인가**? 어느 쪽이 되는가?
- `function ret(): void {}` 의 결과를 `const got: undefined = ret();` 에 담을 수 있는가?

### 10. `never` 를 확인하는 법 (경계)

- [**03번 주제**](../03-basic-type-annotations/)의 `null` 탐침으로 `never` 를 확인할 수 있는가? 안 된다면 대신 무엇을 쓰는가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 각각 해당하는 항목을 하나씩 댈 수 있는가?

### 12. 어디에 무엇을 쓰나 (연결)

- 경계에서 들어오는 값 · 완전성 검사 · 콜백 반환 세 자리에 네 타입 중 무엇을 쓸지 고르고 이유를 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
