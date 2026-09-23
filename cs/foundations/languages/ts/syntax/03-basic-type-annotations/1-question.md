# ts/syntax/03 — 기본 타입 표기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ 이 주제에서 예측할 것은 「**`.d.ts` 에 무엇이 찍히나**」다 —
> 「무슨 타입인지 안다」가 아니라 **컴파일러가 뭐라고 적는지**를 글자로 적어 본다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. ★★ **`strict` 가 기본 `true`** 인 판이고,
> 옵션이 결과를 바꾸는 주제라 **배너의 옵션을 반드시 같이 읽는다**. 모든 블록은 `--pretty false` 다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 표기 없이 열 줄을 두면 (예측)

```ts
// ex.03a.ts
// 원시 타입 표기와, 표기를 안 했을 때 추론되는 것을 나란히 둔다
export const n = 42;
export let m = 42;
export const s = "circle";
export let t = "circle";
export const b = true;
export const big = 10n;
export const sym = Symbol("k");
export const nul = null;
export const und = undefined;
export const annotated: number = 42;
```

- `tsc --declaration --emitDeclarationOnly` 로 뽑은 `.d.ts` 의 **열 줄**을 그대로 적어 보라.
- `n` 과 `m` 의 줄이 **모양 자체가 다른** 이유는 무엇인가?

### 2. 배열 두 표기를 서로 넣으면 (예측)

```ts
// ex.03b.ts
// 배열 두 표기와 readonly — 표기가 다르면 타입도 다른가
export const a: number[] = [1, 2, 3];
export const b: Array<number> = a;
export const c: number[] = b;
export const nested: string[][] = [["x"], ["y"]];
export const union1: (string | number)[] = [1, "a"];
export const union2: string[] | number[] = [1, 2];
export const ro: readonly number[] = [1, 2, 3];
export const ro2: ReadonlyArray<number> = ro;
```

- 에러는 **몇 건**인가?
- `.d.ts` 에서 `b` 와 `ro2` 는 어떤 표기로 되돌아오는가?
- `union1` 과 `union2` 는 **같은 타입인가**?

### 3. `readonly` 를 네 가지로 건드리면 (예측)

```ts
// ex.03c.ts
// readonly 배열·튜플에 손대면 무엇이라고 하나
const ro: readonly number[] = [1, 2, 3];
ro.push(4);
ro[0] = 9;
const mutable: number[] = ro;

const rt: readonly [string, number] = ["a", 1];
rt[0] = "b";

const pair: [string, number] = ["a", 1];
const tooMany: [string, number] = ["a", 1, 2];
const tooFew: [string, number] = ["a"];
console.log(ro, mutable, rt, pair, tooMany, tooFew);
```

- 에러 **코드 다섯 가지**를 각각 어느 줄에 대응시킬 수 있는가?
- 배열의 인덱스 대입과 튜플의 인덱스 대입이 **다른 코드**인 이유는 무엇인가?

### 4. 튜플 네 모양을 돌리면 (예측)

```ts
// ex.03d.ts
// 튜플의 네 모양 — 고정·선택·나머지·이름표
export type Fixed = [string, number];
export type Opt = [string, number?];
export type Rest = [string, ...number[]];
export type Named = [first: string, second: number];

export const fixed: Fixed = ["a", 1];
export const opt1: Opt = ["a"];
export const opt2: Opt = ["a", 1];
export const rest1: Rest = ["a"];
export const rest2: Rest = ["a", 1, 2, 3];
export const named: Named = ["a", 1];

export function first(t: Fixed) {
    return t[0];
}
export function sum(...xs: [string, ...number[]]) {
    return xs[0] + String(xs.length);
}
```

- `opt1`·`rest1` 은 통과하는가? 에러는 **몇 건**인가?
- `.d.ts` 에서 `Named` 의 **이름표**는 살아남는가?

### 5. `as const` 를 붙이면 (예측)

```ts
// ex.03f.ts
// 표기를 안 하면 무엇이 되나 — as const 가 바꾸는 것
export const plainArr = [1, 2, 3];
export const constArr = [1, 2, 3] as const;
export const plainObj = { kind: "circle", r: 1 };
export const constObj = { kind: "circle", r: 1 } as const;
export const nested = { a: { b: [1, "x"] } } as const;
export const litConst = "circle";
export let litLet = "circle";
```

- `plainArr` 와 `constArr` 의 `.d.ts` 줄을 각각 적어 보라 — **세 가지가 한꺼번에** 바뀐다.
- `nested` 는 **안쪽까지** 바뀌는가?

### 6. 일부러 `null` 에 넣어 보면 (예측)

```ts
// ex.03g.ts
// 추론된 타입을 컴파일러에게 캐묻는다 — 일부러 null 에 넣어 본다
const plainArr = [1, 2, 3];
const constArr = [1, 2, 3] as const;
const plainObj = { kind: "circle", r: 1 };
const constObj = { kind: "circle", r: 1 } as const;
const fn = (x: number) => x.toString();

const probe1: null = plainArr;
const probe2: null = constArr;
const probe3: null = plainObj;
const probe4: null = constObj;
const probe5: null = fn;
console.log(probe1, probe2, probe3, probe4, probe5);
```

- 다섯 줄의 진단 문구에서 **타입 이름 다섯 개**를 뽑아 적어 보라.
- 이 방법이 **못 잡는 타입**이 있는가?

### 7. 표기를 빠뜨리면 어디가 꺼지나 (경계)

```ts
// ex.03h.ts
// 표기를 빠뜨리면 검사가 통째로 꺼지는 자리
function twice(n) {
    return n * 2;
}
const handlers = {};
handlers.click = 1;

const evolving = [];
evolving.push(1);
evolving.push("a");

export const exported = [];
exported.push(1);

console.log(twice(2), handlers, evolving);
```

- 진단은 **몇 건**이고, `const evolving = []` 과 `export const exported = []` 중 **에러가 나는 쪽**은 어디인가?
- `--strict false` 로 내리면 **몇 건이 남는가**?

### 8. 어디를 적고 어디를 맡기나 (경계)

- 「표기를 반드시 적어야 하는 자리」 셋과 「적으면 군더더기인 자리」 둘을 댈 수 있는가?

### 9. `readonly` 가 막는 것과 못 막는 것 (왜)

- `readonly` 를 붙인 배열이 **런타임에 정말 못 바뀌는지** 답하고, 그 근거를 [**01번 주제**](../01-what-ts-adds-and-erases/)에서 끌어올 수 있는가?

### 10. `.d.ts` 라는 창 (연결)

- `.d.ts` 덤프와 `null` 탐침 두 방법의 **대상·형식·한계**를 표로 갈라 적을 수 있는가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 각각 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
