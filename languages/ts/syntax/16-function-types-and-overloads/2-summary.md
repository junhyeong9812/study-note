# ts/syntax/16 — 함수 타입과 오버로드 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — More on Functions: Function Overloads](https://www.typescriptlang.org/docs/handbook/2/functions.html#function-overloads) ·
> [Handbook — More on Functions: Call Signatures](https://www.typescriptlang.org/docs/handbook/2/functions.html#call-signatures) ·
> [Handbook — Declaration Files](https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·방출 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 이 문서의 블록은 **옵션을 배너에 적힌 것만** 준 결과이고,
> 그때 `strict` 는 **켜져 있다**(7.0 기본 `true`). `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시**하므로
> 이 블록들은 설정 파일 없이도 그대로 재현된다.
> ★★ 이 주제는 **네 파일 전부** `--strict false` 에서 **글자 하나까지 같다** — 7절의 대조가 그것이다.
> ★★★ **`.d.ts` 는 타입 별칭을 정규화하지 않는다** — 적은 그대로 싣는다. 그래서 4절은 **「적은 것」의 창**이고,
> 탐침은 **「계산된 것」의 창**이다. 둘이 다른 답을 주면 **어느 쪽이 계산된 것인지부터** 갈라야 한다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·방출 전문·`.d.ts` 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 탐침이 뱉는 **타입 글자**(`{ (x: string): number; … }`) | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | ★★ `.d.ts` 의 **들여쓰기 4칸** | 방출기의 고정 형식이다 |
| **★ 설정에 달렸다** | 없다 | ★ 네 파일 전부 `--strict false` 와 **같다**(7절) |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **안 잰 것** | 오버로드가 많을 때의 **검사 시간** | 재지 않았다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 6절의 `ex.16f.ts` 는 **진단이 0줄**이다 — 그 블록도 **명령과 종료 코드까지** 캡처했다.

## 한눈에 — 쉽게 말하면

**오버로드는 「밖에 내건 간판 여러 장」이고, 구현 시그니처는 「안쪽 작업대」다. 손님은 간판만 본다.**

| 비유 | 실체 |
|---|---|
| 가게 앞에 **간판 여러 장** | 오버로드 시그니처 — 호출할 수 있는 꼴들 |
| 안쪽의 **작업대 하나** | 구현 시그니처 — 몸통이 실제로 받는 꼴 |
| ★★★ 손님은 **작업대를 못 쓴다** | 구현 시그니처로는 **호출할 수 없다**(`TS2769`) |
| 간판은 **위에서부터** 읽는다 | 해석 순서 = **선언 순서** |
| 작업대가 **모든 간판을 감당**해야 한다 | 못 덮으면 `TS2394` |
| 포장지(`.d.ts`)에는 **간판만** 찍힌다 | 구현 시그니처는 `.d.ts` 에 **안 실린다** |
| 방출된 JS 에는 **간판이 아예 없다** | 갈래는 몸통이 직접 판다 |

- ★★★ 한 줄로 — 「**오버로드는 타입 쪽에만 있는 것이다. 런타임에는 함수 하나뿐이다.**」
- ★★ 그래서 오버로드의 값은 「**호출한 쪽이 더 정확한 반환 타입을 받는 것**」 하나에 있다.

```text
  간판과 작업대

  function len(x: string): number;          ← 간판 ①
  function len(x: unknown[]): number;       ← 간판 ②
  function len(x: string | unknown[]) { … } ← 작업대 (밖에서 안 보인다)

  len 의 타입 = { (x: string): number; (x: unknown[]): number; }
                 └─ 간판 둘뿐. 작업대는 없다.
```

```text
  세 층으로 나눠 보면

  ① 소스        오버로드 N + 구현 1
        │
        ▼  --declaration
  ② .d.ts       오버로드 N 만            ← 구현은 사라진다
        │
        ▼  방출
  ③ .js         함수 1 (시그니처 0)       ← 간판이 통째로 사라진다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **구현 시그니처는 왜 안 보이나** — 던져서 `TS2769` 를 받고, 탐침으로 **함수의 진짜 타입 글자**를 꺼낸다.
2. **어느 오버로드가 골라지나** — 몸통이 같고 **순서만 다른** 두 함수를 나란히 던진다.
3. **어디까지가 타입 쪽 이야기인가** — `.d.ts` 와 방출 `.js` 를 둘 다 꺼내 **무엇이 남고 무엇이 사라지는지** 가른다.

★ [**03번 주제**](../03-basic-type-annotations/)가 함수 타입 표기를 세웠다면 여기는 **그 표기가 갈라지는 세 꼴**과 **오버로드**다.
★★ 6절의 **메서드 문법 대 프로퍼티 문법**이 [**17번 주제**](../17-variance-and-parameter-compatibility/)의 입구다 — **같은 뜻이 아니다.**

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 성질 |
|---|---|---|
| ★★ **`null` 탐침** | 컴파일러가 **계산한** 타입 글자 | ★ **계산된 것** |
| ★★★ **`--declaration` 의 `.d.ts`** | 추론 결과를 글자로 | ★ **적은 것** — **정규화하지 않는다** |
| ★ **방출 `.js` + `node` 실행** | 런타임에 **무엇이 남는가** | 사실 |

★★★ 셋이 다른 답을 주면 **어느 쪽이 「적은 것」이고 어느 쪽이 「계산된 것」인지부터 갈라라.**
이 주제에서는 1절 24행(탐침)과 4절(`.d.ts`)이 **같은 사실을 다른 형식으로** 말한다 — 구현 시그니처가 **둘 다에 없다.**

비용 — 컴파일 두 번 + 실행 한 번.

### (1) ★★★ 구현 시그니처는 밖에서 안 보인다

**언제 쓰나** — 「내가 적은 매개변수 타입으로 부르는데 에러가 난다」에서 막힐 때.

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

```text
===== tsc --pretty false --noEmit ex.16a.ts (tsc exit=1) =====
ex.16a.ts(10,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.16a.ts(13,21): error TS2769: No overload matches this call.
  The last overload gave the following error.
    Argument of type 'string | unknown[]' is not assignable to parameter of type 'unknown[]'.
      Type 'string' is not assignable to type 'unknown[]'.
ex.16a.ts(23,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.16a.ts(24,7): error TS2322: Type '{ (x: string): number; (x: unknown[]): number; }' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 건**이다 — 10·13·23·24행.
- 10행 — `len("abc")` 가 **`number`** 다. 오버로드가 골라졌다.
- ★★★ 13행이 이 절의 별이다. `either` 의 타입은 `string | unknown[]` 로 **구현 시그니처의 매개변수와 글자까지 같은데** 막힌다.\
  「No overload matches this call.」 뒤에 「The last overload gave the following error.」가 붙는다 —\
  **컴파일러가 시도한 것은 오버로드 둘뿐**이고 구현 시그니처는 후보에 없었다.
- ★★ 23행 — 오버로드 셋짜리도 같다. `overloadCount(true)` 가 **`3`** 이라는 리터럴 타입을 준다.
- ★★★ 24행이 **결정적인 증거**다. 함수 자체를 탐침에 넣으면 타입이\
  `{ (x: string): number; (x: unknown[]): number; }` 다 — **시그니처가 둘뿐**이고 구현 시그니처가 **없다.**
- ★ 즉 오버로드된 함수의 타입은 **오버로드 시그니처만 모은 것**이다. 구현 시그니처는 **몸통을 검사할 때만** 쓰인다.

> **오버로드 시그니처(overload signature)** — 몸통 없이 나열하는 호출 가능한 꼴들.\
> **구현 시그니처(implementation signature)** — 몸통에 붙은 마지막 시그니처. **밖에서는 호출할 수 없다.**

비용 — **유니온으로 부르고 싶으면 그 꼴의 오버로드를 따로 적어야** 한다.

### (2) ★★★ 해석 순서는 선언 순서다

**언제 쓰나** — 「오버로드를 추가했더니 엉뚱한 반환 타입이 나온다」일 때.

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

```text
===== tsc --pretty false --noEmit ex.16b.ts (tsc exit=1) =====
ex.16b.ts(12,7): error TS2322: Type '"넓은 쪽"' is not assignable to type 'null'.
ex.16b.ts(13,7): error TS2322: Type '"좁은 쪽"' is not assignable to type 'null'.
ex.16b.ts(24,7): error TS2322: Type '"인자 없음"' is not assignable to type 'null'.
ex.16b.ts(25,7): error TS2322: Type '"하나"' is not assignable to type 'null'.
ex.16b.ts(26,7): error TS2322: Type '"둘"' is not assignable to type 'null'.
ex.16b.ts(32,7): error TS2322: Type '"하나로 다 받는다"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **여섯 건**이다 — 12·13·24·25·26·32행.
- ★★★ 12행과 13행이 이 절의 전부다. **몸통이 글자까지 같은 두 함수**인데 답이 다르다.\
  `wideFirst("a")` 가 **`"넓은 쪽"`**, `narrowFirst("a")` 가 **`"좁은 쪽"`** 이다.
- ★★ 차이는 **오버로드를 적은 순서** 하나뿐이다. `wideFirst` 는 `(x: string | number)` 를 먼저 적었고,\
  `"a"` 는 그 꼴에 **맞으므로 거기서 멈춘다.** 더 잘 맞는 뒤쪽 후보를 보지 않는다.
- ★★★ 즉 「**가장 잘 맞는 것**」이 아니라 「**먼저 맞는 것**」이다. **좁은 것부터 적어야** 한다.
- 24·25·26행 — 인자 개수로 갈리는 오버로드는 각각 `"인자 없음"`·`"하나"`·`"둘"` 을 준다.
- ★ 32행이 그 대안이다. 선택 매개변수 하나짜리 시그니처는 **개수와 무관하게 같은 반환 타입**을 준다 —\
  `make2()` 도 `make2(1)` 도 `"하나로 다 받는다"` 다. **인자에 따라 반환이 갈리지 않으면 오버로드가 필요 없다.**

```text
  해석은 위에서부터 — 「먼저 맞는 것」이다

  wideFirst("a")                     narrowFirst("a")
  ─────────────────────              ─────────────────────
  ① (x: string | number)  맞다 ✓     ① (x: string)          맞다 ✓
  ② (x: string)           안 본다     ② (x: string | number)  안 본다
        ▼                                   ▼
     "넓은 쪽"                           "좁은 쪽"
```

비용 — **순서가 곧 의미**다. 오버로드를 추가·재배치하면 **호출한 쪽의 타입이 조용히 바뀐다.**

### (3) ★★ 구현 시그니처가 모든 오버로드를 덮어야 한다

**언제 쓰나** — 「오버로드를 하나 더 적었더니 구현 줄에 빨간 줄이 뜬다」일 때.

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

```text
===== tsc --pretty false --noEmit ex.16c.ts (tsc exit=1) =====
ex.16c.ts(3,10): error TS2394: This overload signature is not compatible with its implementation signature.
ex.16c.ts(8,10): error TS2394: This overload signature is not compatible with its implementation signature.
ex.16c.ts(17,10): error TS2391: Function implementation is missing or not immediately following the declaration.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이고 코드가 **`TS2394` 둘 · `TS2391` 하나**다.
- ★★★ 3행 — 「This overload signature is not compatible with its implementation signature.」\
  `notCovered(x: boolean)` 을 내걸었는데 구현은 `x: string` 만 받는다. **매개변수가 안 덮인다.**
- ★★★ 8행 — 같은 코드인데 이번엔 **반환 타입**이다. `returnNotCovered(x: number): number` 를 내걸었는데\
  구현의 반환 타입이 `string` 이다. **`TS2394` 는 매개변수와 반환 양쪽을 다 본다.**
- ★★ `covered` 는 조용하다 — 구현이 `(x: string | number): string | number` 라 **둘 다 덮는다.**
- ★★★ 17행만 다른 코드다. 「Function implementation is missing or not immediately following the declaration.」 —\
  오버로드 사이에 **다른 선언(`const between = 1;`)이 끼면** 그 앞의 시그니처가 **고아**가 된다.
- ★ 즉 오버로드 묶음은 **연속이어야** 한다. 주석은 괜찮지만 **선언은 못 낀다.**

> **`TS2394`** — 「This overload signature is not compatible with its implementation signature.」\
> 구현 시그니처가 그 오버로드를 **매개변수와 반환 타입 양쪽에서** 덮지 못할 때.

비용 — **구현 시그니처가 넓어질수록 몸통 안에서 좁히기가 늘어난다**([**12번 주제**](../12-narrowing/)).

### (4) ★★★ `.d.ts` 에는 간판만 실린다

**언제 쓰나** — 라이브러리로 내보낼 때 **소비자가 무엇을 보게 되는지** 확인할 때.

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

```text
===== tsc --pretty false --declaration --emitDeclarationOnly ex.16d.ts (tsc exit=0) =====
===== 방출된 ex.16d.d.ts =====
export declare function len(x: string): number;
export declare function len(x: unknown[]): number;
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
export declare const arrow: (x: string) => number;
export declare const asCallSig: CallSignature;
export declare class Holder {
    run(x: string): number;
    run(x: number): string;
}
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 종료 코드가 **`0`** 이다. 그리고 `.d.ts` 에 **구현 시그니처가 없다** —\
  `export declare function len(x: string): number;` 와 `…(x: unknown[]): number;` 두 줄뿐이다.
- ★★★ `class Holder` 도 같다. `run(x: string)`·`run(x: number)` 두 줄만 남고 **구현 줄은 사라진다.**
- ★★ 함수 타입 표기 **세 꼴**이 `.d.ts` 에 **적은 모양 그대로** 실린다 —\
  `type ArrowStyle = (x: string) => number;` · `interface CallSignature { (x: string): number; … }` ·\
  `interface MethodStyle { run(x: string): number; }`.
- ★★★ **메서드 문법과 프로퍼티 문법이 구별돼서 실린다** — `run(x: string): number` 와 `run: (x: string) => number` 가\
  **다른 줄**로 남는다. **`.d.ts` 는 이 둘을 같은 것으로 합치지 않는다.**\
  [**17번 주제**](../17-variance-and-parameter-compatibility/)가 그 차이의 값을 잰다.
- ★ `export const arrow` 는 `(x: string) => number` 로 **추론된 타입이 글자로** 찍힌다.\
  `asCallSig` 는 `CallSignature` 라는 **이름 그대로** 남는다 — **`.d.ts` 는 별칭을 펴지 않는다.**

> **`.d.ts`(선언 파일)** — 타입만 담은 방출물. **구현 시그니처는 안 실린다.**\
> ★ 타입 별칭을 **정규화하지 않는다** — 적은 이름 그대로 남긴다.

비용 — `--declaration` 이 필요하다. 오버로드가 많으면 `.d.ts` 도 그만큼 길어진다.

### (5) ★★ 오버로드 대 유니온 매개변수

**언제 쓰나** — 「오버로드를 쓸까 유니온 하나로 끝낼까」를 고를 때.

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

```text
===== tsc --pretty false --noEmit ex.16e.ts (tsc exit=1) =====
ex.16e.ts(10,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.16e.ts(11,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.16e.ts(37,7): error TS2322: Type '{ (x: string): string; (x: number): number; }' is not assignable to type 'WrongShape'.
  Types of parameters 'x' and 'x' are incompatible.
    Type 'boolean' is not assignable to type 'string'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이다 — 10·11·37행.
- ★★★ 10행과 11행이 이 절의 전부다. `overloaded("a")` 는 **`string`**,\
  `unioned("a")` 는 **`string | number`** 다. **인자에 따라 반환이 갈리면 오버로드가 값을 낸다.**
- ★★ 26·27행(메서드 ↔ 프로퍼티)과 30·31행(호출 시그니처 ↔ 화살표)은 **조용하다.**\
  **모양이 같으면 서로 대입된다** — 표기 꼴이 다르다고 다른 타입이 되는 것은 아니다.
- ★★★ 다만 **같은 것은 아니다.** 17 이 재는 **변성**에서 갈린다 — 여기서는 **매개변수 타입이 같아서** 안 드러났다.
- 35행 `const x5: OneShape = overloaded;` 는 통과한다 — 첫 오버로드가 그 꼴을 만족한다.
- ★ 37행 — 안 맞는 꼴(`(x: boolean) => boolean`)에 담으면 `TS2322` 이고,\
  에러 문구가 다시 `{ (x: string): string; (x: number): number; }` 를 보여 준다 — **구현 시그니처가 없다**(1절 24행).

비용 — 오버로드는 **선언이 길어지고 순서에 의존**한다. 반환이 안 갈리면 **유니온 하나가 낫다.**

### (6) ★★★ 방출된 JS 에는 오버로드가 한 글자도 안 남는다

**언제 쓰나** — 「런타임에 어느 오버로드가 골라지나」라는 질문을 지울 때.

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

```text
===== tsc --pretty false ex.16f.ts (tsc exit=0) =====
===== 방출된 ex.16f.js =====
"use strict";
function format(x) {
    if (typeof x === "string")
        return `문자열 ${x}`;
    if (typeof x === "number")
        return `숫자 ${x.toFixed(1)}`;
    return `날짜 ${x.toISOString().slice(0, 10)}`;
}
class Repo {
    find(key) {
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

```text
===== node ex.16f.js (node exit=0) =====
format('a')  : 문자열 a
format(1.5)  : 숫자 1.5
format(날짜) : 날짜 1970-01-01
find(7)      : #7
find('준')   : @준
```

그림 해설 — 한 단계에 한 문장.

- ★★★ `tsc` 종료 코드가 **`0`** 이고 **진단이 0줄**이다. 명령과 종료 코드까지 블록에 찍혀 있다.
- ★★★ 방출된 `.js` 에 `function format(x) { … }` **하나**뿐이다. 오버로드 세 줄은 **사라졌다.**
- ★★ `class Repo` 도 마찬가지다 — `find(key) { … }` 하나만 남는다.
- ★★★ 그러므로 **런타임에 「어느 오버로드」라는 것은 없다.** 갈래는 몸통의 `typeof` 가 직접 판다 —\
  [**12번 주제**](../12-narrowing/)의 좁히기가 그 자리에 그대로 있다.
- ★ 실행 출력 다섯 줄이 그 사실을 확인한다 — `문자열 a`·`숫자 1.5`·`날짜 1970-01-01`·`#7`·`@준`.\
  **타입이 고른 것이 아니라 몸통이 고른 것**이다.

비용 — 없음. 다만 **오버로드와 몸통의 갈래가 어긋나도 아무도 안 잡아 준다** — 구현 시그니처 검사는 **타입만** 본다.

### (7) ★ `strict` 를 꺼도 전부 같다

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.16a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.16b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.16c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.16e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★ 네 파일 **전부** 종료 코드도 출력도 **글자 하나까지 같다.**
- ★ 오버로드 해석·구현 시그니처 규칙·`.d.ts` 방출은 **`strict` 와 무관**하다. **이 주제에는 설정에 달린 칸이 없다.**

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  function len(x: string): number;          ★ 오버로드 시그니처 (몸통 없음)
  function len(x: unknown[]): number;       ★ 위에서부터 읽는다
  function len(x: string | unknown[]) { … } ★ 구현 시그니처 — 밖에서는 못 부른다

  type ArrowStyle = (x: string) => number;          ① 화살표 꼴
  interface CallSignature { (x: string): number; }  ② 호출 시그니처
  interface MethodStyle { run(x: string): number; } ③ 메서드 문법
  interface PropStyle  { run: (x: string) => number; }  ★ ③과 같지 않다 (17번 주제)
```

**규칙 불릿**

- ★★★ **구현 시그니처로는 호출할 수 없다**(`TS2769`). 함수의 타입은 **오버로드 시그니처만 모은 것**이다(1절 24행).
- ★★★ **해석 순서는 선언 순서**다 — 「가장 잘 맞는 것」이 아니라 「**먼저 맞는 것**」(2절 12·13행).
- ★★ **구현 시그니처는 모든 오버로드를 덮어야 한다**(`TS2394`) — **매개변수와 반환 타입 양쪽**을 본다(3절 3·8행).
- ★★ **오버로드 묶음은 연속이어야 한다** — 사이에 선언이 끼면 `TS2391`(3절 17행).
- ★★★ **`.d.ts` 에는 오버로드만 실린다.** 구현 시그니처는 안 실린다(4절).
- ★★ **`.d.ts` 는 별칭을 정규화하지 않는다** — `CallSignature` 를 편 모양이 아니라 **그 이름 그대로** 남긴다.
- ★★★ **방출된 JS 에는 오버로드가 한 글자도 안 남는다**(6절). 갈래는 몸통이 직접 판다.
- ★ **메서드 문법과 프로퍼티 문법은 `.d.ts` 에서 구별돼 실린다** — 같은 뜻이 아니다([**17번 주제**](../17-variance-and-parameter-compatibility/)).
- ★ **인자에 따라 반환 타입이 갈리지 않으면 오버로드가 필요 없다**(5절 10·11행 · 2절 32행).

**금지 사례** — 이 주제에서 던져 받은 것 셋이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 구현 시그니처의 꼴로 호출       ->  TS2769  No overload matches this call.
2) 구현이 오버로드를 못 덮음        ->  TS2394  This overload signature is not compatible with its
                                                implementation signature.
3) 오버로드 사이에 다른 선언        ->  TS2391  Function implementation is missing or not immediately
                                                following the declaration.
```

## 어디서 틀리나

- ★★★ 「**구현 시그니처도 부를 수 있겠지**」 — 없다. 함수의 타입에 **애초에 안 들어 있다**(1절 24행).
- ★★★ 「**가장 잘 맞는 오버로드가 골라지겠지**」 — **먼저 맞는 것**이다(2절). **좁은 것부터 적어라.**
- ★★ 「**오버로드를 뒤에 추가하는 건 안전하겠지**」 — 앞에 넣으면 **호출한 쪽 타입이 조용히 바뀐다.**
- ★★ 「**`TS2394` 는 매개변수 얘기겠지**」 — **반환 타입도** 본다(3절 8행).
- ★★ 「**오버로드 사이에 변수 하나쯤은 괜찮겠지**」 — `TS2391` 이다(3절 17행).
- ★★ 「**`.d.ts` 를 보면 구현 시그니처도 있겠지**」 — 없다(4절).
- ★ 「**메서드 문법과 프로퍼티 문법은 같은 말이겠지**」 — `.d.ts` 가 **구별해서 싣는다**(4절). 변성이 갈린다([**17번 주제**](../17-variance-and-parameter-compatibility/)).
- ★ 「**런타임이 오버로드를 보고 고르겠지**」 — 방출물에 **한 글자도 없다**(6절).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 구현 시그니처로는 **호출할 수 없다** | 1절 13행 `TS2769` · 24행 탐침 |
| **언어 보장** | 해석 순서는 **선언 순서**다 | 2절 12·13행 |
| **언어 보장** | 구현이 **모든 오버로드**를 덮어야 한다 | 3절 3·8행 `TS2394` |
| **언어 보장** | 오버로드 묶음은 **연속**이어야 한다 | 3절 17행 `TS2391` |
| **언어 보장** | 메서드 문법과 프로퍼티 문법은 **다른 것**이다 | 4절 `.d.ts` 전문 · [**17번 주제**](../17-variance-and-parameter-compatibility/) |
| **`.d.ts` 방출** | 오버로드만 실린다 · **별칭을 정규화하지 않는다** | 4절 전문 |
| **방출된 JS** | ★★★ 오버로드는 **한 글자도 안 남는다** | 6절 방출 전문 |
| **방출된 JS** | ★ 갈래는 **몸통의 `typeof` 가 판다** | 6절 실행 출력 |
| **★ 설정에 달림** | ★ **없다** — 네 파일 전부 `--strict false` 와 같다 | 7절 |
| **이 판(7.0.2)의 관찰** | 진단 문구 전문 | 코드(`TS2769`·`TS2394`·`TS2391`)가 더 오래 간다 |
| **이 판의 관찰** | ★ `TS2769` 가 「**The last overload gave…**」만 보여 주는 것 | 보고기의 요약 방식이다 |
| **이 판의 관찰** | `.d.ts` 의 들여쓰기·줄 순서 | 방출기의 형식이다 |
| **안 잰 것** | 오버로드가 많을 때의 **검사 시간** | 재지 않았다 |

★★★ 「**진단 0줄」이 결론인 블록이 둘**이다(4·6절). 그 블록들도 **명령과 종료 코드까지** 캡처했다.
★ **설정에 달린 칸은 0개**다 — 이 갈래에서 드문 일이라 7절에 대조를 남겨 뒀다.

## 언제 쓰고 언제 안 쓰나

| 오버로드를 쓴다 | 안 쓴다 |
|---|---|
| **인자에 따라 반환 타입이 갈릴 때** | 반환이 늘 같을 때 — 유니온 매개변수 하나(5절) |
| 인자 **개수**로 의미가 갈릴 때 | 개수만 다르고 의미가 같을 때 — 선택 매개변수(2절 32행) |
| 공개 API — 소비자가 **정확한 반환**을 받아야 할 때 | 내부 도우미 — 유니온이 읽기 쉽다 |
| 좁은 꼴을 **먼저** 적을 수 있을 때 | 순서를 지키기 어려운 조합 — 조건부 타입이 낫다([목록의 **24번 주제**](../24-conditional-types-and-distribution/)) |
| 구현이 **모든 꼴을 정말 감당**할 때 | 구현이 억지로 넓어져 몸통이 `as` 투성이가 될 때 |

## 핵심 문장

1. **구현 시그니처는 밖에서 안 보인다** — 함수의 타입은 오버로드 시그니처만 모은 것이다.
2. **해석 순서는 선언 순서다** — 가장 잘 맞는 것이 아니라 먼저 맞는 것이다.
3. **구현은 모든 오버로드를 매개변수와 반환 양쪽에서 덮어야 한다** — 아니면 `TS2394`.
4. **`.d.ts` 에는 오버로드만 실리고 별칭은 펴지지 않는다** — 「적은 것」의 창이다.
5. **방출된 JS 에는 오버로드가 한 글자도 안 남는다** — 갈래는 몸통이 판다.
6. **메서드 문법과 프로퍼티 문법은 다른 것이다** — 그 차이의 값은 17 이 잰다.

## 관련 자료

- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) — 함수 타입 표기의 기본은 그쪽.
- [**17번 주제** — 변성과 매개변수 양립성](../17-variance-and-parameter-compatibility/) — 4절의 **메서드 대 프로퍼티**가 그쪽의 입구다. **16 → 17 은 한 사슬**이다.
- [**13번 주제** — 타입 가드와 타입 술어](../13-type-guards-and-predicates/) — 술어(`x is T`)도 반환 타입 자리의 표기다. 오버로드와 섞을 때의 규칙은 **안 던졌다.**
- [**12번 주제** — 좁히기](../12-narrowing/) — 구현 몸통 안에서 갈래를 나누는 수단은 전부 그쪽.
- [**08번 주제** — `interface` 대 `type`](../08-interface-vs-type/) — 호출 시그니처를 `interface` 에 담는 것과 `type` 에 담는 것의 차이는 그쪽.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — 6절의 「방출에 안 남는다」는 그쪽 규칙이다.
- [목록의 **24번 주제**](../24-conditional-types-and-distribution/)(조건부 타입과 분배) — 「인자에 따라 반환이 갈린다」를 오버로드 대신 조건부 타입으로 쓰는 길.
- [목록의 **37번 주제**](../37-writing-declaration-files/)(선언 파일 작성) — 4절의 `.d.ts` 를 손으로 쓰는 쪽은 그쪽.
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **08번** — 함수 정의 형태와 매개변수의 런타임 의미는 그쪽이 정본이다.

## 용어 풀이

> **오버로드 시그니처(overload signature)** — 몸통 없이 나열하는 호출 가능한 꼴들.\
> 예: `function len(x: string): number;`. **해석은 위에서부터** 한다.

> **구현 시그니처(implementation signature)** — 몸통에 붙은 마지막 시그니처.\
> **밖에서는 호출할 수 없고** `.d.ts` 에도 안 실린다. 모든 오버로드를 덮어야 한다.

> **호출 시그니처(call signature)** — `interface F { (x: string): number }` 처럼 객체 타입 안에 적는 호출 가능 표기.\
> 프로퍼티를 같이 가질 수 있다는 점이 화살표 꼴과 다르다.

> **메서드 문법 / 프로퍼티 문법** — `run(x: T): U` 와 `run: (x: T) => U`.\
> `.d.ts` 에 **구별돼서 실리고**, 변성에서 갈린다([**17번 주제**](../17-variance-and-parameter-compatibility/)).

## 더 들어가면

- **왜 구현 시그니처를 감추나** — 구현 시그니처는 **모든 오버로드를 감당하려고 넓어진 꼴**이다. 그것을 밖에 열어 주면 `len("a" as string | unknown[])` 같은 호출이 통과하고, 반환 타입도 뭉뚱그려진다. **오버로드를 쓰는 이유가 사라진다.** 그래서 TS 는 구현 시그니처를 **몸통 검사 전용**으로 둔다 — 1절 24행의 탐침이 그 결과를 글자로 보여 준다.
- **왜 「먼저 맞는 것」인가** — 「가장 잘 맞는 것」을 고르려면 **후보 전부를 비교할 순서**를 정의해야 한다. 매개변수가 여럿이고 서로 부분 순서만 있는 경우 그 비교는 모호해진다. TS 는 그 모호함을 피해 **적은 순서를 그대로 쓴다** — 대신 **작성자가 순서를 책임진다.**
- **조건부 타입이라는 대안** — 「인자에 따라 반환이 갈린다」는 조건부 타입으로도 쓸 수 있다. 오버로드는 **읽기 쉽고 순서에 취약**하고, 조건부 타입은 **순서에 안 취약하고 읽기 어렵다.** [목록의 **24번 주제**](../24-conditional-types-and-distribution/)에서 다룬다 — **이 배치에서는 안 던졌다.**
- **`.d.ts` 가 정규화하지 않는 것** — 4절의 `asCallSig` 가 `CallSignature` 라는 **이름 그대로** 남는다. 그래서 `.d.ts` 를 「컴파일러가 계산한 최종 타입」으로 읽으면 **틀린다.** 탐침이 뱉는 글자가 계산된 쪽이다 — **둘이 다르면 그 차이 자체가 정보**다.
- **오버로드와 술어·단언의 조합** — `function f(x: string): x is "a";` 같은 모양은 **이 배치에서 안 던졌다.** [**13번 주제**](../13-type-guards-and-predicates/)·[**14번 주제**](../14-assertion-signatures/)와 함께 다시 볼 자리다.
