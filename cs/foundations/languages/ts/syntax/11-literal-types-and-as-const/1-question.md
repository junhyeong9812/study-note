# ts/syntax/11 — 리터럴 타입과 `as const` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ 이 주제에서는 **탐침 한 줄마다 답이 하나씩** 나온다 —
> 「몇 건인가」보다 「**각 줄이 무엇이라고 답하는가**」가 문제다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. `strict` 는 **기본 `true`** 이고,
> 파일을 직접 주었으므로 `tsconfig.json` 은 읽히지 않았다.
> 모든 블록은 `--pretty false` 이고, 옵션은 배너에 적힌 것만 줬다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.** 템플릿 리터럴 타입은 백틱을 포함하므로 **겹백틱**으로 적었다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 리터럴 추론이 어디서 넓어지나 (예측)

```ts
// ex.11a.ts
// 리터럴 추론이 어디서 넓어지나 — 자리마다 컴파일러에게 캐묻는다
const cStr = "circle";
let lStr = "circle";
const cNum = 1;
let lNum = 1;
const cBool = true;
var vStr = "circle";

const obj = { a: 1, s: "circle", b: true };
const arr = [1, 2, 3];
const mixed = ["a", 1];

const annotated: "circle" = "circle";
let lAnnotated: "circle" = "circle";
const fromCall = String("circle");

const p1: null = cStr;
const p2: null = lStr;
const p3: null = cNum;
const p4: null = lNum;
const p5: null = cBool;
const p6: null = vStr;
const p7: null = obj;
const p8: null = obj.a;
const p9: null = arr;
const p10: null = mixed;
const p11: null = annotated;
const p12: null = lAnnotated;
const p13: null = fromCall;

lAnnotated = "square";
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13);
```

- 탐침 **열세 개**가 각각 무엇이라고 답하는가?
- `const cStr` 과 `let lStr` 은 왜 다른가? `var vStr` 은 어느 쪽인가?
- `const obj = { a: 1 }` 의 `obj.a` 는 `1` 인가 `number` 인가?

### 2. `as const` 를 붙이면 무엇이 달라지나 (예측)

```ts
// ex.11b.ts
// as const 가 바꾸는 것 셋 — 리터럴 고정·readonly·배열을 튜플로
const plain = { mode: "dark", retries: 3, deep: { x: 1 }, list: [1, 2] };
const frozen = { mode: "dark", retries: 3, deep: { x: 1 }, list: [1, 2] } as const;

const p1: null = plain;
const p2: null = frozen;
const p3: null = frozen.deep;
const p4: null = frozen.list;

const plainArr = [1, 2, 3];
const frozenArr = [1, 2, 3] as const;
const p5: null = plainArr;
const p6: null = frozenArr;

let lFrozen = "circle" as const;
const p7: null = lFrozen;

declare const n: number;
const partial = { a: n } as const;
const partialArr = [n] as const;
const p8: null = partial;
const p9: null = partialArr;

frozen.retries = 4;
frozenArr[0] = 9;
frozenArr.push(4);
lFrozen = "square";

const copied = [...frozenArr];
const p10: null = copied;
const spread = { ...frozen };
const p11: null = spread.mode;
console.log(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11);
```

- `frozen` 의 타입 전문은 어떻게 나오는가? **몇 가지**가 한꺼번에 바뀌는가?
- `frozenArr` 는 `readonly number[]` 인가 다른 것인가?
- 24\~27행 네 줄은 각각 어느 코드로 막히는가? 29·31행의 사본은 무엇을 잃는가?

### 3. `as const` 가 안 되는 자리는 어디인가 (예측)

```ts
// ex.11c.ts
// as const 가 안 되는 자리 — 에러 전문이 허용 목록을 통째로 읽어 준다
declare const n: number;
declare const s: string;
let v = 1;

const bad1 = n as const;
const bad2 = (1 + 2) as const;
const bad3 = (() => 1) as const;
const bad4 = v as const;

const ok1 = -1 as const;
const ok2 = `a` as const;
const ok3 = `a${s}` as const;
const ok4 = `a${1}` as const;
const ok5 = { a: n } as const;
const ok6 = [n] as const;

enum E {
    X = 1,
}
const ok7 = E.X as const;

const p1: null = ok1;
const p2: null = ok2;
const p3: null = ok3;
const p4: null = ok4;
const p5: null = ok5;
const p6: null = ok6;
const p7: null = ok7;
console.log(bad1, bad2, bad3, bad4, p1, p2, p3, p4, p5, p6, p7);
```

- 진단은 **몇 건**이고, 에러 코드와 **문구 전문**은 무엇인가?
- 6\~9행 중 막히는 것과 11\~16행 중 통과하는 것을 가르는 기준은 무엇인가?
- `` `a${s}` as const `` 는 무엇이 되는가? `` `a${1}` as const `` 와 어떻게 다른가?

### 4. 템플릿 리터럴 타입은 무엇을 만드나 (예측)

```ts
// ex.11d.ts
// 템플릿 리터럴 타입 맛보기 — 리터럴 유니온이 곱해진다
type Dir = "up" | "down";
type Handler = `on${Capitalize<Dir>}`;
type CssVar = `--${string}`;
type Pair = `${Dir}-${Dir}`;

declare const h: Handler;
declare const c: CssVar;
declare const pr: Pair;

const p1: null = h;
const p2: null = c;
const p3: null = pr;

const okHandler: Handler = "onUp";
const badHandler: Handler = "onup";
const okCss: CssVar = "--brand";
const badCss: CssVar = "brand";
const okPair: Pair = "up-down";
const badPair: Pair = "up-left";

declare const s: string;
const built = `on${s}` as const;
const p4: null = built;
const putBuilt: CssVar = built;
console.log(p1, p2, p3, p4, okHandler, badHandler, okCss, badCss, okPair, badPair, putBuilt);
```

- `Handler`·`Pair` 는 각각 **몇 개의 리터럴**로 펼쳐지는가? `CssVar` 는 왜 다른가?
- 16행 `badHandler` 의 에러 코드는 다른 줄들과 **다른가**?
- 25행 `const putBuilt: CssVar = built;` 는 통과하는가?

### 5. 방출된 JS 에 `as const` 가 남나 (예측)

```ts
// ex.11e.ts
// as const 는 방출에 한 글자도 안 남는다 — readonly 도 런타임에는 없다
type Dir = "up" | "down";

const dir = "up" as const;
const conf = { mode: "dark", retries: 3 } as const;
const list = [1, 2, 3] as const;

function move(d: Dir): string {
    return `move ${d}`;
}

console.log("move      :", move(dir));
console.log("conf      :", conf.mode, conf.retries);
console.log("list      :", list.length, list[0]);

const escaped = list as unknown as number[];
escaped.push(9);
console.log("push 뒤   :", list.join(","));
console.log("frozen?   :", Object.isFrozen(conf), Object.isFrozen(list));
```

- `as const` 는 방출에 **몇 글자** 남는가?
- `Object.isFrozen(conf)` 은 무엇을 찍는가? `escaped.push(9)` 뒤 `list` 는 어떻게 되는가?

### 6. `.d.ts` 는 리터럴을 어떻게 적나 (예측)

```ts
// ex.11f.ts
// 선언 방출은 값 쪽 추론 결과를 적는다 — 여기서는 as const 가 글자로 드러난다
export const cStr = "circle";
export let lStr = "circle";
export const frozen = { mode: "dark", retries: 3 } as const;
export const plain = { mode: "dark", retries: 3 };
export const frozenArr = [1, 2, 3] as const;
export const plainArr = [1, 2, 3];
export type Handler = `on${Capitalize<"up" | "down">}`;
export const picked: "a" | "b" = "a";
```

- `const cStr` 과 `let lStr` 은 `.d.ts` 에서 어떻게 갈리는가?
- `Handler` 는 **펼쳐져서** 나오는가, 적은 그대로 나오는가?

### 7. 왜 `let` 은 넓어지나 (왜)

- 「리터럴 넓히기」가 **재대입 가능성**과 이어져 있다는 것을 한 문장으로 댈 수 있는가?

### 8. 왜 `as const` 는 아무 식에나 못 붙나 (왜)

- 3번 진단의 허용 목록이 **왜 그 목록인지** 설명할 수 있는가?

### 9. 넓히기를 막는 세 수단의 차이 (경계)

- 타입 주석 · `as const` · [목록의 **29번 주제**](../29-satisfies/)(`satisfies`)가 각각 **무엇을 고정하고 무엇을 남기는가**?

### 10. `readonly` 가 지키는 것과 못 지키는 것 (경계)

- 5번의 실행 출력에 기대어 `readonly` 의 경계를 말할 수 있는가?

### 11. 09 의 리터럴 흡수와 잇기 (연결)

- `"asc" | "desc" | string` 이 무너지는 것과 이 주제의 **넓히기**는 같은 일인가 다른 일인가?

### 12. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **설정에 달린 것** · **이 판(7.0.2)의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
