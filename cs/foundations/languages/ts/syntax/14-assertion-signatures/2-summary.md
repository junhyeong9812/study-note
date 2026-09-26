# ts/syntax/14 — 단언 시그니처 `asserts` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Narrowing: Assertion functions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) ·
> [TypeScript 3.7 릴리스 노트 — Assertion Functions](https://devblogs.microsoft.com/typescript/announcing-typescript-3-7/) ·
> [Node.js — `assert`](https://nodejs.org/docs/latest-v18.x/api/assert.html).
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
> **버전** — `asserts x is T` 와 `asserts x` 는 둘 다 **TS 3.7** 에 들어왔다.
> ★★ `@types/node` 는 **없다.** 7.0 의 `types` 기본값이 `[]` 이기도 하고, 이 배치는 `node_modules` 를 만들지 않았다 —
> 그래서 6절은 **필요한 만큼만 직접 선언한 `.d.ts` 한 장**을 함께 던졌다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ **2절의 「진단 0건」** — 이 주제의 본체다 | 소스 전문을 옆에 뒀으니 다시 던질 수 있다 |
| **안 흔들린다** | ★ 런타임 예외 문구 `v.toUpperCase is not a function` | `node` v18 의 메시지다. **판이 오르면 문구가 바뀔 수 있다** |
| **안 흔들린다** | ★★ `node:assert` 의 실패 메시지 전문 | `node` v18 의 것이다. 코드가 아니라 **문구**라 더 잘 바뀐다 |
| **★ 설정에 달렸다** | 4절 탐침 **한 칸**(17행의 표시) | `strictNullChecks`. 양쪽을 다 실었다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다. 예외도 `message` 만 찍어 **스택을 안 남겼다** |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★★ **2절은 진단이 한 줄도 없다.** 그러므로 **소스 전문과 실행 출력이 곧 근거**다 — 셋을 나란히 실었다.

## 한눈에 — 쉽게 말하면

**단언은 「아니면 여기서 끝난다」는 약속이다. 컴파일러는 약속만 읽고 지켜졌는지는 안 본다.**

| 비유 | 실체 |
|---|---|
| 검표원이 표를 보고 **아니면 들여보내지 않는다** | `asserts v is string` — 통과했다면 그 타입이다 |
| 통과한 뒤로는 **문 안쪽 전부**가 승객이다 | 호출 **뒤부터 함수 끝까지** 좁혀진다 |
| 검표원이 **아무도 안 막아도** 규정상으론 막은 것 | ★★★ 몸통이 비어 있어도 **진단 0건** |
| 표가 가짜면 **자리에 앉을 때** 문제가 터진다 | `v.toUpperCase is not a function` |
| ★ 검표원은 **이름표를 달아야** 일할 수 있다 | `TS2775` — 부르는 이름마다 명시적 타입 표기 |
| 검표원은 **아무것도 돌려주지 않는다** | 반환 타입이 **`void`** 여야 한다 |
| 표준 라이브러리의 검표원도 있다 | `node:assert` — **런타임 검사는 진짜로 한다** |

- ★★★ 한 줄로 — 「**술어는 「참이면 T」, 단언은 「돌아오면 T」다.**」
- ★★ 범위가 넓은 만큼 **틀렸을 때의 값도 크다** — 술어는 `if` 안만, 단언은 그 뒤 전부를 오염시킨다.

```text
  술어와 단언이 갈리는 자리

  if (isString(v)) {          asserts:  assertString(v);
      v 는 string              │        v 는 string
  }                            │        …
  v 는 다시 unknown            │        여기도 string
                               ▼        함수 끝까지
  ★ 술어는 분기 안             ★ 단언은 호출 뒤 전부
```

```text
  세 층으로 나눠 보면

  ① 내장 가드        typeof · instanceof · in · 진릿값 · ===     ← 12번 주제
  ② 술어 함수        function isX(v): v is X                     ← 13번 주제
  ③ 단언 함수        function assertX(v): asserts v is X         ← 이 주제
        │
        ▼  ①은 컴파일러가 뜻을 안다. ②·③은 **사람 말을 믿는다.**
           그중 ③이 **가장 넓게** 믿는다 — 호출 뒤 전부다.
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **단언은 어디까지 좁히나** — 호출 뒤·함수 호출 건너편·분기 밖을 **탐침으로 각각** 찍는다.
2. **몸통을 컴파일러가 보나** — **안 본다.** 거짓말하는 단언 셋을 던져 런타임에 깨뜨린다. **이 주제의 본체다.**
3. **왜 아무 이름으로나 못 부르나** — `TS2775` 가 걸리는 자리와 안 걸리는 자리를 **일곱 칸 격자**로 재 본다.

★ [**13번 주제**](../13-type-guards-and-predicates/)가 `x is T` 를 세웠다면 여기는 **`asserts` 의 전면 서술**이다. 13 의 3절이 남겨 둔 것을 여기서 끝낸다.
★★ [**15번 주제**](../15-control-flow-analysis-limits/)와도 이어진다 — 단언이 만든 좁힘도 **같은 한계를 받는다**(11번 답).

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★ **분기마다 박은 `null` 탐침** | 단언이 실제로 좁혔는지 | [**12번 주제**](../12-narrowing/)에서 이어받음 |
| ★★★ **방출 `.js` + `node` 실행** | **컴파일러가 안 잡은 것을 런타임이 잡는 것** | ★ 이 주제의 본체 |
| ★ **같은 파일을 `--strict false` 로 다시** | 탐침이 갈리는 칸을 가르려고 | [**12번 주제**](../12-narrowing/)에서 이어받음 |

★★★ **`never`·`any` 는 탐침을 통과한다** — `const x: null = v;` 가 조용하면 `v` 가 `null` 이거나 `never` 이거나 `any` 다.
이 문서는 그런 자리를 만들지 않았고(모든 탐침이 진단을 냈다), 필요하면 **역방향 대입**으로 다시 묻는다.

비용 — 컴파일 한 번 + 실행 한 번.

### (1) ★★★ 두 꼴과 좁힘의 범위

**언제 쓰나** — 「`if` 없이 그 뒤로 쭉 좁혀진 채로 쓰고 싶다」일 때.

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

```text
===== tsc --pretty false --noEmit ex.14a.ts (tsc exit=1) =====
ex.14a.ts(11,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.14a.ts(13,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14a.ts(15,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14a.ts(17,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14a.ts(23,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14a.ts(28,11): error TS2322: Type 'number' is not assignable to type 'null'.
ex.14a.ts(34,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14a.ts(36,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.14a.ts(41,5): error TS2322: Type 'number' is not assignable to type 'void'.
ex.14a.ts(45,5): error TS2322: Type 'string' is not assignable to type 'void'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **열 건**이다 — 11·13·15·17·23·28·34·36·41·45행.
- 11행 — 단언을 부르기 **전**의 `v` 는 **`unknown`** 이다. 13행 — 부른 **뒤**는 **`string`** 이다.
- ★★★ 15행이 이 절의 별이다. **`touch()` 를 부른 뒤에도 `string` 이 그대로다** —\
  단언이 만든 좁힘은 **함수 호출을 건너서도 살아남는다**([**15번 주제**](../15-control-flow-analysis-limits/)의 1절과 같은 규칙이다).
- 17행 — 안쪽 블록으로 들어가도 유지된다.
- ★★ 23행 — `asserts v`(`is T` 가 없는 꼴)도 좁힌다. `string | null | undefined` 가 **`string`** 이 된다.\
  「참인 값이다」만 주장하므로 [**12번 주제**](../12-narrowing/)의 **진릿값 좁히기와 같은 결과**다.
- ★ 28행이 그 경계다. `number | "" | null` 에 `asserts v` 를 걸면 **`number`** 다 —\
  `0` 은 거짓값이지만 **타입으로는 `number` 에서 떼어낼 수 없다.** 빈 문자열만 사라진다.
- ★★★ 34·36행이 술어와 갈리는 자리다. `if` **안에서** 단언을 부르면 34행은 `string` 인데,\
  **분기를 나오면 36행은 다시 `unknown`** 이다. **단언도 제어 흐름을 벗어나지는 못한다.**
- ★★ 41·45행 — `return 1;` 이 「Type 'number' is not assignable to type 'void'.」, `return "ok";` 가 「Type 'string' is not assignable to type 'void'.」\
  **`asserts` 함수의 반환 타입은 `void` 다.** 값을 돌려주는 순간 막힌다.

> **단언 시그니처(assertion signature)** — `asserts x is T` 또는 `asserts x` 를 반환 타입 자리에 적어\
> 「**정상 반환하면 그 조건이 참이다**」를 선언하는 표기(TS 3.7). 반환 타입은 **`void`** 다.

비용 — 없음. 다만 **본문이 맞는지는 아무도 안 본다** — 다음 절이 그 대가다.

### (2) ★★★ 컴파일러는 단언의 몸통을 검사하지 않는다

**언제 쓰나** — 「타입이 맞는데 런타임에 터졌다」의 원인을 찾을 때. **이 절이 이 주제의 본체다.**

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

```text
===== tsc --pretty false ex.14b.ts (tsc exit=0) =====
===== 방출된 ex.14b.js =====
"use strict";
// 컴파일러는 단언의 몸통을 검사하지 않는다 — 거짓말하는 단언을 던져서 깨뜨린다
function assertNothing(v) { }
function assertBackwards(v) {
    if (typeof v === "string")
        throw new Error("문자열이면 던진다");
}
function assertNeverReturns(v) {
    throw new Error("무조건 던진다");
}
function shoutEmpty(v) {
    assertNothing(v);
    return v.toUpperCase();
}
function shoutBackwards(v) {
    assertBackwards(v);
    return v.toUpperCase();
}
function shoutNever(v) {
    assertNeverReturns(v);
    return v.toUpperCase();
}
function run(label, f) {
    try {
        console.log(label, f());
    }
    catch (e) {
        console.log(label, "터졌다 ->", e.message);
    }
}
run("shoutEmpty('hi')    :", () => shoutEmpty("hi"));
run("shoutEmpty(7)       :", () => shoutEmpty(7));
run("shoutBackwards(7)   :", () => shoutBackwards(7));
run("shoutBackwards('hi'):", () => shoutBackwards("hi"));
run("shoutNever('hi')    :", () => shoutNever("hi"));
```

```text
===== node ex.14b.js (node exit=0) =====
shoutEmpty('hi')    : HI
shoutEmpty(7)       : 터졌다 -> v.toUpperCase is not a function
shoutBackwards(7)   : 터졌다 -> v.toUpperCase is not a function
shoutBackwards('hi'): 터졌다 -> 문자열이면 던진다
shoutNever('hi')    : 터졌다 -> 무조건 던진다
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **진단이 한 줄도 없다. 종료 코드가 `0` 이다.** 세 단언 함수가 전부 거짓말인데도 그렇다.
- `assertNothing` 은 **몸통이 비어 있다.** `assertBackwards` 는 **검사가 뒤집혀** 있다. `assertNeverReturns` 는 **무조건 던진다.**
- 방출된 `.js` 에 `asserts` 표기가 **한 글자도 안 남는다** — `function assertNothing(v) { }` 뿐이다.
- ★★ 첫 줄 `shoutEmpty('hi')` 가 **`HI`** 다. **우연히 맞으면 조용히 지나간다** — 그래서 더 늦게 발견된다.
- ★★★ 둘째 줄 `shoutEmpty(7)` 이 **터진다** — 「`v.toUpperCase is not a function`」.\
  몸통이 아무것도 안 하는데 컴파일러는 그 뒤의 `v` 를 `string` 으로 믿었다.
- ★★ 셋째 줄 — 뒤집힌 검사도 **숫자를 그냥 통과시킨다.** 넷째 줄은 반대로 **문자열에서 던진다** —\
  「문자열이면 던진다」는 **몸통이 정말로 하는 일**이고, 타입 쪽은 **정반대**를 믿고 있다.
- ★ 다섯째 줄 — 무조건 던지는 단언은 **뒤 코드에 영원히 닿지 않는다.** 그것도 진단이 없다.

```text
  컴파일 시각                          런타임
  ───────────────────────────────────────────────────────────
  assertNothing(v): asserts v is string   몸통이 비어 있다
        │                                      │
        ▼                                      ▼
  v 는 string 이다 (믿는다)            7 이 그대로 흘러간다
  v.toUpperCase() 통과                 7.toUpperCase()
        │                                      │
        ▼                                      ▼
  tsc exit 0 · 진단 0건                node 가 대신 말한다
```

> **거짓 단언** — 몸통이 실제로 확인·중단하지 않는데 `asserts` 를 적은 함수.\
> **컴파일러는 검사하지 않는다.** 요구 조건은 「반환 타입이 `void` 다」 하나뿐이다.

비용 — ★★★ **단언 하나가 그 함수 나머지 전부의 안전을 책임진다.** 술어(`x is T`)보다 **범위가 넓다.**

### (3) ★★ `TS2775` — 부르는 이름에 타입 표기가 필요하다

**언제 쓰나** — 「단언 함수를 만들었는데 호출하는 자리에서 빨간 줄이 뜬다」에서 막힐 때.

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

```text
===== tsc --pretty false --noEmit ex.14c.ts (tsc exit=1) =====
ex.14c.ts(32,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14c.ts(35,5): error TS2775: Assertions require every name in the call target to be declared with an explicit type annotation.
ex.14c.ts(36,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.14c.ts(40,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14c.ts(44,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14c.ts(47,5): error TS2775: Assertions require every name in the call target to be declared with an explicit type annotation.
ex.14c.ts(48,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.14c.ts(52,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14c.ts(56,11): error TS2322: Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **아홉 건**이고 그중 **`TS2775` 가 둘**(35·47행)이다. 나머지 일곱은 탐침이다.
- ★★★ 35행 — `const bareArrow = (v: unknown): asserts v is string => { … }` 를 부르면 막힌다.\
  「Assertions require every name in the call target to be declared with an explicit type annotation.」
- ★★ 36행이 그 대가다. 막힌 뒤의 `v` 는 **`unknown`** 그대로다 — **좁히기가 아예 안 일어난다.**
- ★★★ 47행이 같은 함정의 다른 얼굴이다. `bareObj.go(v)` 도 막힌다.\
  **`bareObj` 라는 이름에 타입 표기가 없기 때문**이다 — 메서드 쪽이 아니라 **객체 쪽**이 문제다.
- ★★ 통과하는 다섯 자리가 그 규칙을 거꾸로 말해 준다 — 32행 `declaredFn`(함수 선언) · 40행 `typedArrow`(표기 있는 `const`) ·\
  44행 `declaredConst`(`declare const`) · 52행 `typedObj`(표기 있는 객체) · 56행 `Guard.go`(클래스 정적 메서드).
- ★ 즉 「**호출 대상 경로에 등장하는 모든 이름**이 추론이 아니라 **선언**으로 타입을 갖고 있어야 한다」가 규칙이다.\
  함수 선언과 클래스 선언은 그 자체가 선언이라 통과하고, `const` 는 **표기를 붙여야** 통과한다.

```text
  TS2775 가 걸리는 자리 — 이 판에서 던진 일곱 칸

  ✓ function declaredFn(v): asserts v is string   함수 선언
  ✗ const bareArrow = (v): asserts v is string    표기 없는 const          ← TS2775
  ✓ const typedArrow: Asserter = (v) => …         표기 있는 const
  ✓ declare const declaredConst: Asserter         declare const
  ✗ bareObj.go(v)   (const bareObj = { go… })     표기 없는 객체           ← TS2775
  ✓ typedObj.go(v)  (const typedObj: {go: …})     표기 있는 객체
  ✓ Guard.go(v)     (class Guard { static go… })  클래스 정적 메서드
```

> **`TS2775`** — 「Assertions require every name in the call target to be declared with an explicit type annotation.」\
> 단언 호출의 **대상 경로에 있는 모든 이름**이 명시적 타입 표기를 가져야 한다는 제약.

비용 — **표기를 하나 더 적어야 한다.** 대신 **막히면 좁히기가 아예 안 되므로** 조용히 틀리지는 않는다.

### (4) ★★ `asserts this` · 제네릭 단언 · 술어와의 대비

**언제 쓰나** — 「객체 자신의 상태를 단언하고 싶다」거나 「술어로 할까 단언으로 할까」를 고를 때.

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

```text
===== tsc --pretty false --noEmit ex.14d.ts (tsc exit=1) =====
ex.14d.ts(14,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(17,11): error TS2322: Type 'string | null' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.14d.ts(19,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(31,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(33,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.14d.ts(37,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(43,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(45,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **여덟 건**이다 — 14·17·19·31·33·37·43·45행.
- 14행 — 제네릭 단언 `assertDefined<T>(v: T): asserts v is NonNullable<T>` 뒤의 `v` 가 **`string`** 이다.
- ★★★ 17·19행이 `asserts this` 다. `box.assertLoaded()` 를 부르기 전 `box.data` 는 **`string | null`**,\
  부른 뒤는 **`string`** 이다. **메서드가 자기 객체의 상태를 좁힌다.**
- ★★ 31·33행이 술어 쪽이다 — `if (isString(v))` **안**은 `string`, **밖**은 `unknown` 으로 돌아간다.
- ★★★ 37행이 단언 쪽이다 — `if` 가 없는데도 그 뒤가 `string` 이다. **이것이 둘의 유일한 실질적 차이**다.
- ★ 43·45행 — 단언 뒤라도 **재대입하면 풀린다.** `v = 1;` 뒤의 `v` 가 **`unknown`** 이다(선언 타입으로 돌아간다).

★★ 이 파일이 **네 파일 중 유일하게** `--strict false` 에서 갈린다. 같은 파일을 다시 던졌다.

```text
===== tsc --pretty false --noEmit --strict false ex.14d.ts (tsc exit=1) =====
ex.14d.ts(14,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(17,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(19,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(31,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(33,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.14d.ts(37,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(43,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.14d.ts(45,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
```

- ★★★ **17행의 글자만 바뀐다.** `string | null` 에서 **`string`** 으로 줄었다 —\
  `strictNullChecks` 가 꺼지면 `null` 이 모든 타입에 흡수되어 **탐침이 「좁히기 전」을 못 보여 준다.**
- ★★ 나머지 일곱 줄은 **글자 하나까지 같다.** 45행(재대입 뒤)도 양쪽 다 `unknown` 이다.
- ★ 교훈 — **플래그를 끄면 이 주제의 실험 자체가 안 보인다.** 탐침을 짤 때 `null` 을 쓴 것이 그래서 중요하다.

> **`asserts this is T`** — 메서드의 반환 타입 자리에 적어 **`this` 의 타입을 좁히는** 단언(TS 3.7).\
> 예: `assertLoaded(): asserts this is { data: string }`.

비용 — `asserts this` 는 **클래스 필드의 선언 타입을 바꾸지 않는다.** 좁힘은 호출한 흐름 안에서만 산다.

### (5) ★ 단언 대상은 매개변수 이름이나 `this` 여야 한다

**언제 쓰나** — 「`asserts o.v is string` 을 적었더니 이상한 에러가 쏟아진다」일 때.

```ts
// ex.14e.ts
// 단언 대상은 매개변수 이름이나 this 여야 한다 — 프로퍼티는 문법이 아니다
function assertProp(o: { v: unknown }): asserts o.v is string {
    if (typeof o.v !== "string") throw new Error("문자열이 아니다");
}
```

```text
===== tsc --pretty false --noEmit ex.14e.ts (tsc exit=1) =====
ex.14e.ts(2,50): error TS1144: '{' or ';' expected.
ex.14e.ts(2,51): error TS1434: Unexpected keyword or identifier.
ex.14e.ts(2,53): error TS1228: A type predicate is only allowed in return type position for functions and methods.
ex.14e.ts(2,56): error TS1434: Unexpected keyword or identifier.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 건**이고 코드가 **`TS1144`·`TS1434`·`TS1228`·`TS1434`** 다.
- ★★★ `TS2xxx` 가 **하나도 없다.** `TS1xxx` 는 **파서가 내는 코드**다 — 타입 오류가 아니라 **문법 오류**다.
- `TS1228` 이 이유를 말한다 — 「A type predicate is only allowed in return type position for functions and methods.」\
  파서는 `asserts o` 까지 읽고 **거기서 시그니처가 끝났다고 본다.** `.v is string` 은 그 뒤의 쓰레기다.
- ★★ 그래서 **한 줄의 실수가 네 줄의 진단**이 된다. 이런 모양을 보면 **타입이 아니라 문법을 의심**해야 한다.
- ★ 고치는 법은 **객체 자체를 단언**하는 것이다 — `asserts o is { v: string }`. 또는 4절처럼 `asserts this` 를 쓴다.

비용 — 없음. 다만 **파스 에러는 파일의 나머지 진단을 가린다** — 한 번에 하나씩 고쳐야 한다.

### (6) ★★★ `node:assert` — 표준 라이브러리의 단언

**언제 쓰나** — 「`assert(x)` 를 부르면 타입도 좁혀지나」를 확인할 때.

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

먼저 **선언 없이** 던진다.

```text
===== tsc --pretty false --noEmit --module commonjs ex.14f.ts (tsc exit=1) =====
ex.14f.ts(2,25): error TS2591: Cannot find name 'node:assert'. Do you need to install type definitions for node? Try `npm i --save-dev @types/node` and then add 'node' to the types field in your tsconfig.
ex.14f.ts(5,11): error TS2322: Type 'string | number | null' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.14f.ts(7,11): error TS2322: Type 'string | number | null' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

- ★★★ `TS2591` 이 나온다 — 「Cannot find name 'node:assert'. Do you need to install type definitions for node? …」\
  **`@types/node` 가 없으면 `node:assert` 는 타입이 없다.** 7.0 의 `types` 기본값이 `[]` 인 것과 겹친다.
- ★★ 그 상태에서는 **5행과 7행이 똑같이 `string | number | null`** 이다 — 좁히기가 **아예 안 일어난다.**

이제 **직접 쓴 선언 한 장**을 같이 준다.

```text
===== tsc --pretty false --noEmit --module commonjs node-assert.d.ts ex.14f.ts (tsc exit=1) =====
ex.14f.ts(5,11): error TS2322: Type 'string | number | null' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.14f.ts(7,11): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 5행이 `string | number | null`, 7행이 **`string | number`** 다. **`assert(v)` 가 `null` 을 떼어냈다.**
- ★★ 서명이 **`asserts value`** 다 — `is T` 가 **없다.** 그래서 [**12번 주제**](../12-narrowing/)의 **진릿값 좁히기와 같은 결과**만 준다.\
  `""` 와 `0` 은 **타입에서 못 떼어낸다**(1절 28행과 같은 이유다).
- ★ 이 선언은 **이 배치가 쓰는 만큼만** 적은 것이다. 진짜 `@types/node` 는 훨씬 넓다.

방출하고 실제로 돌린다.

```text
===== tsc --pretty false --module commonjs node-assert.d.ts ex.14f.ts (tsc exit=2) =====
ex.14f.ts(5,11): error TS2322: Type 'string | number | null' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.14f.ts(7,11): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
===== 방출된 ex.14f.js =====
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
// node:assert 는 asserts value 다 — is T 가 없고, 검사는 런타임이 진짜로 한다
const assert = require("node:assert");
function widen(v) {
    const before = v;
    assert(v);
    const after = v;
}
function run(label, f) {
    try {
        f();
        console.log(label, "통과");
    }
    catch (e) {
        console.log(label, "던졌다 ->", e.message);
    }
}
run("assert(1)    :", () => assert(1));
run("assert(0)    :", () => assert(0));
run("assert('')   :", () => assert("", "빈 문자열이다"));
run("assert(null) :", () => assert(null, "널이다"));
console.log(widen);
```

```text
===== node ex.14f.js (node exit=0) =====
assert(1)    : 통과
assert(0)    : 던졌다 -> The expression evaluated to a falsy value:

  assert(0)

assert('')   : 던졌다 -> 빈 문자열이다
assert(null) : 던졌다 -> 널이다
[Function: widen]
```

- ★★★ `assert(0)` 과 `assert(null)` 이 **정말로 던진다.** 14 의 다른 절과 정반대다 —\
  **표준 라이브러리의 `assert` 는 런타임 검사를 진짜로 한다.** `asserts` 표기는 그 사실을 **타입 쪽에 알려 줄 뿐**이다.
- ★★ `assert(0)` 의 메시지가 **소스 그대로를 인용**한다 — 「The expression evaluated to a falsy value:」 뒤에 `assert(0)`.
- ★ 방출된 `.js` 에는 `require("node:assert")` 만 남는다. **선언 파일은 방출물에 아무 흔적도 안 남긴다.**

★★ 이 파일은 **종료 코드가 갈리는 자리**이기도 하다 — 탐침이 에러를 내는 채로 던졌기 때문이다.

```text
===== 같은 파일을 --noEmit 으로 한 번, 방출하며 한 번 =====
tsc --pretty false --noEmit --module commonjs node-assert.d.ts ex.14f.ts   -> exit 1
tsc --pretty false --module commonjs node-assert.d.ts ex.14f.ts            -> exit 2
```

- ★★★ **같은 입력인데 `--noEmit` 은 `1`, 방출하면 `2`** 다. 「에러가 있는데 산출물을 냈다」가 **다른 코드**로 보고된다.
- ★ 이것은 이 주제의 규칙이 아니라 **이 갈래 전체의 규칙**이다([**02번 주제**](../02-type-checking-vs-emit/)).

> **`node:assert`** — Node 표준 모듈. `assert(value)` 는 값이 거짓이면 `AssertionError` 를 던진다.\
> 타입 쪽 서명은 `asserts value` 이고 **`is T` 가 없다** — 「참인 값이다」까지만 말한다.

비용 — **타입 정의가 따로 필요하다.** 7.0 기본 설정에서는 `types` 가 `[]` 라 **설정도 손봐야 한다.**

### (7) ★ `strict` 를 꺼도 대부분 같다

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.14a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.14c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.14d.ts    exit 1 / exit 1 · ★ 다르다
ex.14e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★ 네 파일 중 **`ex.14d.ts` 하나만** 갈린다(4절). 나머지 셋은 **종료 코드도 출력도 글자 하나까지 같다.**
- ★ 단언의 **문법과 신뢰 모델**은 `strict` 와 무관하다. 갈리는 것은 **탐침이 보여 주는 글자**뿐이다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  function assertString(v: unknown): asserts v is string { … }   ★ 단언 시그니처 (3.7)
  function assertTruthy(v: unknown): asserts v { … }             ★ is T 가 없는 꼴
  assertLoaded(): asserts this is { data: string }               ★ this 단언
  function assertDefined<T>(v: T): asserts v is NonNullable<T>   ★ 제네릭 단언

  const at: (v: unknown) => asserts v is string = fn             ★ 이 표기가 있어야 부를 수 있다
  const bad = (v: unknown): asserts v is string => { … }         ✗ 부르면 TS2775
  function f(o: {v: unknown}): asserts o.v is string             ✗ 문법 오류 (TS1228)
```

**규칙 불릿**

- ★★★ **`asserts` 함수의 반환 타입은 `void` 다.** 값을 돌려주면 `TS2322` 로 막힌다(1절 41·45행).
- ★★★ **몸통은 검사되지 않는다.** 비어 있어도·뒤집혀 있어도·무조건 던져도 **진단 0건**이다(2절).
- ★★★ **좁힘은 호출 뒤부터 그 흐름 끝까지** 간다 — 함수 호출을 건너서도 살아남는다(1절 15행).
- ★★ 다만 **분기 안에서 부르면 분기 밖으로는 못 나간다**(1절 34·36행). **재대입하면 풀린다**(4절 45행).
- ★★ **`asserts x`** 는 진릿값 좁히기와 같은 결과다 — `0` 과 `""` 중 `0` 은 **타입에서 못 뗀다**(1절 28행).
- ★★ **호출 대상 경로의 모든 이름**에 명시적 타입 표기가 필요하다(`TS2775`). 없으면 **좁히기가 아예 안 일어난다**.
- ★ **단언 대상은 매개변수 이름이나 `this` 뿐**이다. 프로퍼티를 적으면 **문법 오류**다(`TS1228`).
- ★ **`node:assert`** 는 `asserts value` 꼴이고, **런타임 검사는 진짜로 한다.** 타입은 `@types/node` 가 있어야 붙는다.

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) asserts 함수가 값을 반환        ->  TS2322  Type 'number' is not assignable to type 'void'.
2) 표기 없는 const 로 단언 호출     ->  TS2775  Assertions require every name in the call target to be
                                                declared with an explicit type annotation.
3) 단언 대상에 프로퍼티            ->  TS1228  A type predicate is only allowed in return type position
                                                for functions and methods.
4) ★ 거짓 단언                     ->  진단 없음. tsc exit 0. 런타임에 TypeError
```

## 어디서 틀리나

- ★★★ 「**`asserts` 를 적으면 컴파일러가 몸통을 확인해 준다**」 — **안 한다.** 2절이 진단 0건으로 통과하고 런타임에 터진다.
- ★★★ 「**단언은 술어보다 안전하다**」 — 더 위험하다. **좁힘의 범위가 넓어 오염 범위도 넓다**(9번 답).
- ★★ 「**화살표 함수로 만들어도 똑같겠지**」 — `const` 에 담으면 `TS2775` 이고 **좁히기가 아예 안 된다**(3절).
- ★★ 「**객체에 담아 `obj.assert(v)` 로 부르면 되겠지**」 — **객체 이름에도** 표기가 필요하다(3절 47행).
- ★★ 「**`asserts v` 는 `null`·`0`·`""` 를 다 떼어 준다**」 — `0` 은 **`number` 에서 못 뗀다**(1절 28행).
- ★ 「**`asserts` 함수도 `true` 를 돌려주면 되겠지**」 — 반환 타입이 `void` 라 `TS2322` 다.
- ★ 「**`asserts o.v is T` 로 프로퍼티를 좁히면 되겠지**」 — **문법이 아니다**(5절).
- ★ 「**`assert` 를 import 하면 바로 좁혀지겠지**」 — `@types/node` 가 없으면 `TS2591` 이고 **좁히기가 안 일어난다**(6절).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | `asserts x is T` 는 **호출 뒤부터** 좁힌다 | 1절 13·15·17행 |
| **언어 보장** | 반환 타입은 **`void`** 여야 한다 | 1절 41·45행 `TS2322` |
| **언어 보장** | ★★★ **몸통은 검사되지 않는다** | 2절 — 진단 0건 · `tsc exit 0` · 런타임 `TypeError` |
| **언어 보장** | 호출 대상 경로의 **모든 이름**에 타입 표기가 필요하다 | 3절 35·47행 `TS2775` |
| **언어 보장** | 단언 대상은 **매개변수 이름이나 `this`** 뿐이다 | 5절 `TS1228` |
| **언어 보장** | `asserts this is T` 는 **`this` 를 좁힌다** | 4절 17·19행 |
| **방출된 JS** | `asserts` 표기는 **한 글자도 안 남는다** | 2절 방출 전문 |
| **방출된 JS** | ★ 런타임 검사는 **몸통이 하는 것뿐**이다 | 2절 실행 출력 · 6절 `node:assert` |
| **★ 설정에 달림** | 4절 탐침 **한 칸**(17행의 표시) | `strictNullChecks`. **양쪽 판을 다 실었다** |
| **★ 설정에 달림** | `node:assert` 의 타입 유무 | `types`·`@types/node`. 7.0 기본값이 `[]` |
| **이 판(7.0.2)의 관찰** | 진단 문구 전문 | 코드(`TS2775`·`TS1228`·`TS2591`)가 더 오래 간다 |
| **이 판의 관찰** | ★ `TS2591` 의 문구가 「Cannot find **name**」이다 | 모듈 지정자인데 「이름」이라 한다. **판이 오르면 바뀔 수 있다** |
| **이 판의 관찰** | `node:assert` 의 실패 메시지 전문 | `node` v18 의 것이다 |
| **안 잰 것** | 단언이 많을 때의 **검사 시간** | 재지 않았다 |

★★★ 「**진단 0건」이 근거인 블록이 하나**다(2절). 그 블록은 **소스 전문 + 방출 전문 + 실행 출력** 셋을 다 실어야 근거가 된다.
★ **설정에 달린 것은 둘**이다 — 4절 탐침의 **한 칸**(`strictNullChecks`)과 `node:assert` 의 타입 유무(`types`).

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| 「**아니면 더 갈 수 없다**」가 정말 참인 자리 | 되돌릴 수 있는 분기 — 술어(`x is T`)가 맞다 |
| 초기화·설정 검사 — 부르고 나면 **그 뒤 전부**가 안전 | 루프 안에서 매번 — 예외 비용이 붙는다 |
| `asserts this` 로 **객체의 준비 상태**를 좁히기 | 필드 타입 자체를 바꿔야 하는 설계 — 판별 유니온이 낫다 |
| 몸통이 **정말로 검사하고 던지는** 단언 | 편의를 위해 몸통을 비운 단언 — `as` 와 같다 |
| 함수 선언·클래스 정적 메서드로 두기 | 표기 없는 `const` 화살표 — `TS2775` 로 막힌다 |

## 핵심 문장

1. **술어는 「참이면 T」, 단언은 「돌아오면 T」다** — 범위가 넓은 만큼 위험도 크다.
2. **몸통은 검사되지 않는다** — 비어 있어도 진단 0건이고 런타임이 대신 말한다.
3. **반환 타입은 `void` 다** — 값을 돌려주면 `TS2322`.
4. **호출 대상 경로의 모든 이름에 타입 표기가 필요하다** — 없으면 `TS2775` 이고 좁히기가 아예 안 된다.
5. **단언 대상은 매개변수 이름이나 `this` 뿐**이다 — 프로퍼티는 문법이 아니다.
6. **`node:assert` 는 런타임 검사를 진짜로 한다** — `asserts` 표기는 그 사실을 타입 쪽에 알릴 뿐이다.

## 관련 자료

- [**13번 주제** — 타입 가드와 타입 술어](../13-type-guards-and-predicates/) — `x is T` 의 전면 서술은 그쪽. **13 → 14 는 한 사슬**이다.
- [**15번 주제** — 제어 흐름 분석의 한계](../15-control-flow-analysis-limits/) — 단언이 만든 좁힘도 **같은 한계를 받는다**(11번 답).
- [**12번 주제** — 좁히기](../12-narrowing/) — `asserts v` 가 주는 결과는 **진릿값 좁히기와 같다.**
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — 반환 타입 `void` 의 뜻과 `unknown` 입구 설계는 그쪽.
- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — 6절의 **종료 코드 1 대 2** 는 그쪽 규칙이다.
- [목록의 **30번 주제**](../30-type-assertions-and-non-null/)(타입 단언과 non-null `!`) — 거짓 단언이 `as` 와 **같은 등급의 탈출구**라는 것은 그쪽과 함께 읽는다.
- [목록의 **38번 주제**](../38-ambient-global-types-configuration/)(앰비언트·전역 타입 구성) — 6절의 `types` 기본값 `[]` 와 `@types/node` 는 그쪽.
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **32번** — `throw`/`try`/`catch` 의 런타임 의미는 그쪽이 정본이다.

## 용어 풀이

> **단언 시그니처(assertion signature)** — `asserts x is T` 또는 `asserts x` 를 반환 타입 자리에 적는 표기(TS 3.7).\
> 「정상 반환하면 그 조건이 참이다」를 선언한다. 반환 타입은 **`void`** 다.

> **`asserts x`(불리언 단언)** — `is T` 가 없는 꼴. 「`x` 가 참인 값이다」만 주장한다.\
> 결과는 진릿값 좁히기와 같다 — `""` 는 떨어져 나가지만 `0` 은 `number` 에 남는다.

> **`asserts this is T`** — 메서드의 반환 타입 자리에 적어 **`this` 를 좁히는** 단언.\
> 예: `assertLoaded(): asserts this is { data: string }`.

> **`TS2775`** — 단언 호출의 대상 경로에 있는 **모든 이름**이 명시적 타입 표기를 가져야 한다는 제약.\
> 막히면 **좁히기가 아예 안 일어난다.**

> **거짓 단언** — 몸통이 실제로 확인·중단하지 않는데 `asserts` 를 적은 함수.\
> **컴파일러는 검사하지 않는다.**

## 더 들어가면

- **왜 `TS2775` 가 필요한가** — 좁히기는 **호출한 자리에서 대상 함수의 시그니처를 알아야** 일어난다. 그런데 `const` 에 담긴 값의 타입은 **초기화식에서 추론**되므로, 그 추론을 끝내려면 그 식을 검사해야 하고 — 단언은 그 검사 결과에 다시 영향을 준다. TS 는 그 고리를 끊으려고 「**표기로 미리 고정된 이름만 단언으로 부를 수 있다**」는 제약을 둔다. 3절의 격자가 그 선을 그대로 그린다.
- **왜 반환 타입이 `void` 인가** — 단언은 「돌아왔다」는 **사건 자체**가 정보다. 값을 돌려주면 「값이 참이면」과 「돌아오면」이 섞여 술어와 구별이 안 된다. 그래서 값 반환을 막는다 — 1절 41·45행이 그 경계다.
- **단언을 안전하게 쓰는 수** — 몸통을 [**12번 주제**](../12-narrowing/)의 내장 가드만으로 짜고, **`throw` 가 모든 실패 경로를 덮는지** 눈으로 확인한다. 2절의 세 함수가 각각 그 확인을 빠뜨린 모습이다.
- **왜 프로퍼티를 단언할 수 없나** — 좁히기의 대상은 **참조(reference)** 이고, `o.v` 같은 프로퍼티 참조는 **호출 사이에 바뀔 수 있다.** [**15번 주제**](../15-control-flow-analysis-limits/)가 그 자리를 전수로 잰다. 문법에서 막은 것은 그 어려움을 **시그니처 단계에서 잘라 낸** 것이다.
- **`@types/node` 를 쓰면** — 6절의 선언 한 장 대신 진짜 정의가 붙고, `assert.ok`·`assert.strictEqual` 같은 멤버도 `asserts` 로 선언돼 있다. **이 배치에서는 안 던졌다** — `node_modules` 를 만들지 않았기 때문이다.
