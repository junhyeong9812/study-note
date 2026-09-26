# ts/syntax/14 — 단언 시그니처 `asserts` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 2번은 **진단이 한 줄도 없는 것이 답**이다. 그런 블록을 근거로 쓰려면 **소스 전문 + 방출 전문 + 실행 출력** 셋이 다 있어야 한다 — 그렇게 실었다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **10건** — 호출 뒤부터 **함수 끝까지** 좁혀지고, 반환 타입은 **`void`** 여야 한다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 11 | 단언을 부르기 **전** | `unknown` |
| 13 | 부른 **직후** | `string` |
| 15 | ★★★ **다른 함수를 부른 뒤** | `string` — **안 풀린다** |
| 17 | 안쪽 블록 | `string` |
| 23 | `asserts v` 를 `string \| null \| undefined` 에 | `string` |
| 28 | ★ `asserts v` 를 `number \| "" \| null` 에 | **`number`** — `0` 은 못 뗀다 |
| 34 / 36 | `if` **안** / `if` **밖** | `string` / **`unknown`** |
| 41 | `return 1;` | **TS2322** — 「Type 'number' is not assignable to type 'void'.」 |
| 45 | `return "ok";` | **TS2322** — 「Type 'string' is not assignable to type 'void'.」 |

- ★★★ 15행이 술어와 갈리는 첫 자리다. `assertString(v)` 뒤에 **`touch()` 를 불러도** `v` 가 `string` 그대로다.\
  [**15번 주제**](../15-control-flow-analysis-limits/)가 재는 「함수 호출 뒤에는 안 풀린다」가 단언에도 그대로 적용된다.
- ★★ 36행이 그 범위의 **끝**을 보여 준다. 단언을 **분기 안에서** 부르면 분기 밖으로는 못 나간다 —\
  **단언도 제어 흐름을 벗어나지 못한다.**
- ★★ 28행이 `asserts x`(불리언 단언)의 경계다. 「참인 값이다」는 [**12번 주제**](../12-narrowing/)의 진릿값 좁히기와 같아서,\
  `""` 는 리터럴 타입이라 떨어져 나가지만 **`0` 은 `number` 안에 숨어 있어 못 뗀다.**
- ★★★ 41·45행이 **반환 타입 규칙**이다 — `asserts` 함수의 반환 타입은 **`void`** 다. 값을 돌려주면 막힌다.

### 2. ★★★ **진단 0건 · `tsc exit 0`** — 그리고 다섯 줄 중 넷이 예상과 다르다

**출력**

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

**왜 그런가**

| 호출 | 출력 | 왜 |
|---|---|---|
| `shoutEmpty("hi")` | `HI` | ★ **우연히 맞았다** — 조용히 지나간다 |
| `shoutEmpty(7)` | 터졌다 → `v.toUpperCase is not a function` | 몸통이 아무것도 안 하는데 타입은 `string` 을 믿는다 |
| `shoutBackwards(7)` | 터졌다 → `v.toUpperCase is not a function` | 검사가 **뒤집혀** 숫자를 통과시킨다 |
| `shoutBackwards("hi")` | 터졌다 → `문자열이면 던진다` | ★★ **타입이 믿는 것과 정반대**로 동작한다 |
| `shoutNever("hi")` | 터졌다 → `무조건 던진다` | 정상 반환 경로가 아예 없다 |

- ★★★ **`tsc` 종료 코드가 `0` 이고 진단이 한 줄도 없다.** 세 단언이 전부 거짓인데도 그렇다.
- ★★★ 컴파일러가 검사하지 **않는** 것은 정확히 이것이다 — 「**몸통이 정말로 그 조건을 확인하고,\
  아니면 정말로 중단하는가**」. 요구 조건은 「반환 타입이 `void` 다」 하나뿐이다.
- ★★ 방출된 `.js` 를 보면 `asserts` 표기가 **한 글자도 안 남는다.** 런타임에 남는 것은 **몸통이 하는 일뿐**이다.
- ★ 첫 줄이 가장 무섭다. **거짓 단언이 늘 터지지는 않는다** — 맞는 값이 들어오는 동안은 조용하다.

### 3. ★★★ `TS2775` **2건** — 막히는 것은 **표기 없는 `const`** 와 **표기 없는 객체**다

**출력**

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

**왜 그런가**

| 부르는 이름 | 결과 | 왜 |
|---|---|---|
| `declaredFn(v)` — 함수 선언 | ✓ `string` (32행) | 선언 자체가 시그니처다 |
| `bareArrow(v)` — 표기 없는 `const` | ★ **TS2775** (35행) · 이후 `unknown` (36행) | 타입이 **추론**된 이름이다 |
| `typedArrow(v)` — 표기 있는 `const` | ✓ `string` (40행) | `const t: Asserter = …` |
| `declaredConst(v)` — `declare const` | ✓ `string` (44행) | 표기로 선언됐다 |
| `bareObj.go(v)` — 표기 없는 객체 | ★ **TS2775** (47행) · 이후 `unknown` (48행) | ★★ 막힌 이름은 **`bareObj`** 다 |
| `typedObj.go(v)` — 표기 있는 객체 | ✓ `string` (52행) | 객체 쪽에 표기가 있다 |
| `Guard.go(v)` — 클래스 정적 메서드 | ✓ `string` (56행) | 클래스 선언이 곧 표기다 |

- ★★★ 기준은 「**호출 대상 경로에 등장하는 모든 이름**이 **추론이 아니라 선언**으로 타입을 갖고 있는가」다.\
  에러 문구가 그대로 그렇게 말한다 — 「every name in the call target」.
- ★★★ 그래서 `bareObj.go(v)` 가 막히는 것은 **`go` 때문이 아니라 `bareObj` 때문**이다.\
  `typedObj` 는 똑같은 메서드를 갖고도 통과한다 — **객체 쪽 표기 하나가 갈랐다.**
- ★★ 막힌 자리의 대가가 크다. 36·48행에서 `v` 는 **`unknown` 그대로**다 — 에러만 나는 게 아니라 **좁히기가 아예 안 일어난다.**
- ★ 함수 선언과 클래스 선언이 통과하는 이유는 같다 — **둘 다 그 자체가 타입 선언**이라 추론을 기다릴 필요가 없다.

### 4. ★★ 진단 **8건** — 술어는 **분기 안**, 단언은 **그 뒤 전부**

**출력**

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

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 14 | 제네릭 단언 `asserts v is NonNullable<T>` 뒤 | `string` |
| 17 / 19 | `asserts this` **전** / **후** | `string \| null` / **`string`** |
| 31 / 33 | 술어 `if` **안** / **밖** | `string` / **`unknown`** |
| 37 | 단언 호출 **뒤** | `string` — `if` 가 없다 |
| 43 / 45 | 단언 뒤 / **재대입 뒤** | `string` / **`unknown`** |

- ★★★ 31·33행과 37행의 대비가 **술어와 단언의 유일한 실질적 차이**다.\
  술어는 `if` 를 **써야** 좁혀지고 그 `if` 를 나오면 풀린다. 단언은 **`if` 없이** 그 뒤 전부를 좁힌다.
- ★★ 17·19행 — `asserts this is { data: string }` 는 **자기 객체의 프로퍼티**를 좁힌다.\
  「아직 로드 안 됨」 같은 상태를 메서드 하나로 잘라 낼 때 쓴다.
- ★ 45행 — 단언도 **재대입은 못 이긴다.** `v = 1;` 뒤의 `v` 가 선언 타입인 `unknown` 으로 돌아간다.\
  [**15번 주제**](../15-control-flow-analysis-limits/)의 1절이 같은 것을 유니온에서 잰다.
- ★★ 이 파일이 **네 파일 중 유일하게** `--strict false` 에서 갈린다.

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

- ★★★ **17행의 글자만 바뀐다.** `string | null` 에서 **`string`** 이 된다 —\
  `strictNullChecks` 가 꺼져 `null` 이 흡수되면 **「좁히기 전」이 탐침에 안 보인다.**
- ★ 나머지 일곱 줄은 글자 하나까지 같다. **단언의 규칙 자체는 플래그와 무관**하다.

### 5. ★★ 진단 **4건** — 전부 `TS1xxx` 다. 타입 오류가 아니라 **문법 오류**다

**출력**

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

**왜 그런가**

- 코드가 **`TS1144`·`TS1434`·`TS1228`·`TS1434`** 다. `TS2xxx` 가 **하나도 없다.**
- ★★★ `TS1xxx` 는 **파서가 내는 코드**다. 타입 검사기는 이 줄까지 오지도 못했다.
- `TS1228` 이 이유를 말한다 — 「A type predicate is only allowed in return type position for functions and methods.」\
  파서는 `asserts o` 까지 읽고 시그니처가 끝났다고 보고, `.v is string` 을 **엉뚱한 토큰**으로 읽는다.
- ★★ 그래서 **한 줄의 실수가 네 줄의 진단**이 된다. 이런 모양이면 **타입이 아니라 문법을 의심**해야 한다.
- ★ 고치는 법은 두 가지다 — 객체 자체를 단언하거나(`asserts o is { v: string }`) `asserts this` 로 옮긴다(4번).

### 6. ★★★ 선언이 없으면 `TS2591` — 있으면 **`null` 만** 떨어져 나간다

**출력**

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

```text
===== tsc --pretty false --noEmit --module commonjs ex.14f.ts (tsc exit=1) =====
ex.14f.ts(2,25): error TS2591: Cannot find name 'node:assert'. Do you need to install type definitions for node? Try `npm i --save-dev @types/node` and then add 'node' to the types field in your tsconfig.
ex.14f.ts(5,11): error TS2322: Type 'string | number | null' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.14f.ts(7,11): error TS2322: Type 'string | number | null' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

```text
===== tsc --pretty false --noEmit --module commonjs node-assert.d.ts ex.14f.ts (tsc exit=1) =====
ex.14f.ts(5,11): error TS2322: Type 'string | number | null' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.14f.ts(7,11): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

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

```text
===== 같은 파일을 --noEmit 으로 한 번, 방출하며 한 번 =====
tsc --pretty false --noEmit --module commonjs node-assert.d.ts ex.14f.ts   -> exit 1
tsc --pretty false --module commonjs node-assert.d.ts ex.14f.ts            -> exit 2
```

**왜 그런가**

| 무엇 | 결과 |
|---|---|
| 선언 없이 `import assert = require("node:assert")` | ★ **TS2591** — 「Cannot find name 'node:assert'. …」 |
| 그때의 5·7행 탐침 | 둘 다 `string \| number \| null` — **좁히기가 안 일어난다** |
| 선언과 함께 던진 5행 / 7행 | `string \| number \| null` / **`string \| number`** |
| `assert(1)` | 통과 |
| `assert(0)` | 던졌다 → 「The expression evaluated to a falsy value:」 + `assert(0)` |
| `assert("")` · `assert(null)` | 던졌다 → 메시지 인자 그대로 |
| `--noEmit` / 방출 | ★★★ **exit 1 / exit 2** |

- ★★★ 서명이 **`asserts value`** 다 — **`is T` 가 없다.** 그래서 「참인 값이다」까지만 말하고,\
  1번 28행과 같은 이유로 **`0` 과 `""` 는 타입에서 못 떨어져 나간다.** 여기서 사라진 것은 **`null` 뿐**이다.
- ★★★ 실행 출력이 이 주제의 다른 절과 **정반대**다 — `node:assert` 는 **런타임 검사를 진짜로 한다.**\
  `asserts` 표기는 「이 함수는 실패하면 던진다」는 **사실을 타입 쪽에 알려 줄 뿐**이다.
- ★★ 종료 코드가 갈리는 것은 이 주제의 규칙이 아니라 **갈래 전체의 규칙**이다 —\
  **에러가 있는데 산출물을 냈으면 `2`**([**02번 주제**](../02-type-checking-vs-emit/)).
- ★ 방출된 `.js` 에는 `require("node:assert")` 만 남는다. **선언 파일은 방출물에 아무 흔적도 안 남긴다.**

### 7. ★★★ **단언은 「돌아왔다」는 사건이 정보이기 때문**이다

**왜 그런가**

- 술어는 「**돌려준 값이 참이면** T」다. 단언은 「**돌아오기만 하면** T」다 — 값이 아니라 **제어 흐름**이 정보다.
- ★★ 값을 돌려줄 수 있게 두면 두 뜻이 섞인다. 「`true` 를 돌려줬다」와 「돌아왔다」가 같은 자리에서 다투게 된다.
- ★★★ 그래서 TS 는 반환 타입을 **`void`** 로 고정한다. 1번 41·45행이 그 경계다 —\
  `return 1;` 도 `return "ok";` 도 같은 `TS2322` 로 막히고, 문구가 「**not assignable to type 'void'**」다.
- ★ 뒤집으면 **`return;`(값 없는 반환)은 막지 않는다.** 2번의 `assertNothing` 이 그 모양이고, **그것도 통과한다.**
- ★ 즉 `void` 는 「아무것도 안 돌려준다」는 뜻이지 「반드시 던진다」는 뜻이 아니다. **후자는 검사되지 않는다.**

### 8. ★★★ **좁히기와 타입 추론이 서로를 기다리는 고리를 끊으려고** 그렇다

**왜 그런가**

- 호출한 자리에서 좁히려면 컴파일러가 **대상의 시그니처를 이미 알고 있어야** 한다.
- ★★ 그런데 `const f = (v) => …` 처럼 표기가 없으면 그 타입은 **초기화식을 검사해야** 정해진다.\
  검사에는 좁히기가 끼어 있고, 좁히기는 다시 그 타입을 필요로 한다 — **고리가 생긴다.**
- ★★★ TS 는 그 고리를 **문법 단계에서 잘라 낸다** — 「**표기로 이미 고정된 이름만 단언으로 부를 수 있다**」.\
  3번의 격자가 그 선을 그대로 그린다. 통과한 다섯은 전부 **표기 또는 선언**으로 타입이 정해진 이름이다.
- ★★ 그래서 막힌 자리에서 **좁히기가 「부분적으로」 되지 않고 아예 안 된다.** 컴파일러가 애초에 시도하지 않는다.
- ★ 실무의 교훈은 하나다 — **단언 함수는 `function` 선언으로 두거나, `const` 에 담을 땐 타입을 적어라.**

### 9. ★★ **단언이 더 위험하다** — 좁힘의 범위가 넓기 때문이다

**왜 그런가**

| | 술어 `x is T` (13번 주제) | 단언 `asserts x is T` (이 주제) |
|---|---|---|
| 무엇을 선언하나 | 「`true` 면 `T` 다」 | 「**정상 반환하면** `T` 다」 |
| 사람이 지킬 약속 | 하나 — 판정이 맞을 것 | ★ **둘** — 판정이 맞을 것 **+ 아니면 던질 것** |
| 좁히는 범위 | `if` **분기 안** | ★★★ 호출 **뒤부터 흐름 끝까지** |
| 호출 형태 제약 | 없다 | ★ **모든 이름에 표기 필요**(`TS2775`) |
| 반환 타입 | `boolean` | **`void`** |
| 검사되나 | ★ **안 된다** | ★ **안 된다** |

- ★★★ 범위가 넓은 만큼 **틀렸을 때 오염되는 코드도 넓다.** 술어가 틀리면 그 `if` 안만, 단언이 틀리면 **그 뒤 전부**다.
- ★★ 게다가 「아니면 던진다」는 약속은 **코드를 읽어도 잘 안 보인다.** 2번의 `assertNothing` 이 그 예다 —\
  몸통이 비어 있는데 아무도 막지 않는다.
- ★★ 대신 단언에는 술어에 없는 **안전장치가 하나** 있다 — `TS2775` 다. **호출 형태를 강제**해서\
  「어디서 좁혀졌는지」를 추적 가능하게 만든다. 술어에는 그런 제약이 없다.
- ★ 고르는 기준 — 「**여기서 아니면 더 갈 수 없다**」가 참이면 단언, **되돌릴 수 있으면 술어**다.

### 10. ★★ 표준 `assert` 는 **런타임**을, `asserts` 표기는 **타입**을 책임진다

**왜 그런가**

| | `node:assert` 의 `assert(v)` | 타입 시스템의 `asserts v` |
|---|---|---|
| 무엇을 하나 | **실제로 검사하고 던진다** | 컴파일러에게 **그렇다고 말한다** |
| 런타임에 남나 | ★ **남는다** — `require("node:assert")` | ★ **한 글자도 안 남는다** |
| 틀리면 | `AssertionError` 가 즉시 난다 | ★★ **아무 일도 안 난다** — 나중에 터진다 |
| 타입을 좁히나 | 서명에 `asserts value` 가 있어야 좁힌다 | 그 서명이 바로 이 표기다 |

- ★★★ 6번의 실행 출력이 그 분업을 그대로 보여 준다 — `assert(0)` 이 **정말로 던졌다.**\
  2번의 `assertNothing` 은 **안 던졌다.** 둘 다 타입 쪽 서명은 `asserts` 로 같다.
- ★★ 그래서 좋은 단언 함수는 **`node:assert` 같은 것을 몸통에서 쓰는 것**이다 —\
  검사는 표준 라이브러리에 맡기고, `asserts` 표기로 그 사실을 타입 쪽에 실어 보낸다.
- ★ 이 판에서는 `@types/node` 가 없어 **선언 한 장을 직접 써야** 했다(`TS2591`). 7.0 의 `types` 기본값이 `[]` 인 것도 겹친다.

### 11. ★★ **그대로 받는다** — 단언은 「좁힘을 만드는 법」일 뿐 「좁힘을 지키는 법」이 아니다

**왜 그런가**

| 자리 | 단언이 만든 좁힘 | 근거 |
|---|---|---|
| 다른 함수를 부른 뒤 | ★ **살아남는다** | 1번 15행 |
| 안쪽 블록 | 살아남는다 | 1번 17행 |
| `if` 분기를 나오면 | ★ **풀린다** | 1번 34·36행 |
| 재대입 뒤 | ★ **풀린다** | 4번 43·45행 |
| ★★ 프로퍼티를 단언하고 콜백 안에서 | **풀린다** | [**15번 주제**](../15-control-flow-analysis-limits/)의 5절 |

- ★★★ 마지막 줄이 중요하다. [**15번 주제**](../15-control-flow-analysis-limits/)에서 `assertDefined(b.v)` 뒤의 `b.v` 는 곧바로 `string` 인데,\
  **콜백 안으로 들어가면 다시 `string | undefined`** 다. **단언은 「고치는 법」이 아니다.**
- ★★ 단언이 만든 좁힘도 결국 **같은 제어 흐름 분석 위에** 얹힌다 — 만드는 수단이 다를 뿐 **지켜지는 규칙은 하나**다.
- ★ 고치는 법은 15 의 결론과 같다 — **지역 `const` 하나**에 담는 것이다.

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | `asserts x is T` 는 **호출 뒤부터** 좁힌다 · 반환 타입은 **`void`**(`TS2322`) · ★★★ **몸통은 검사되지 않는다** · 호출 대상 경로의 **모든 이름**에 표기가 필요하다(`TS2775`) · 단언 대상은 **매개변수 이름이나 `this`** 뿐이다(`TS1228`) · `asserts this is T` 는 `this` 를 좁힌다 |
| **설정에 달린 것** | ★ **두 칸**. ① 4번 탐침의 **한 칸**(17행) — `strictNullChecks`(`strict` 에 딸려 7.0 기본 `true`). **양쪽 판을 다 실었다** ② `node:assert` 의 타입 유무 — `types`(7.0 기본 `[]`)와 `@types/node` |
| **이 판(7.0.2)의 관찰** | 진단 문구 전문 — 코드(`TS2775`·`TS1228`·`TS2591`)가 더 오래 간다 · ★ `TS2591` 이 모듈 지정자에 「Cannot find **name**」이라고 말하는 것 · `node:assert` 의 실패 메시지 전문(`node` v18) · 파스 에러 한 줄이 **네 줄의 진단**으로 퍼지는 모양 |

- ★★★ 「**진단 0건」이 답인 블록이 하나**다(2번). 그래서 이 문서는 **소스 전문·방출 전문·실행 출력**을 나란히 실었다 —\
  셋이 있어야 침묵이 근거가 된다.
- ★ **진단 문구는 외우지 말고 코드로 기억하라.** 격자(3번)와 범위(1번)는 **다시 던져서** 확인한다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 두 꼴과 좁힘 범위 | `--noEmit ex.14a.ts` | exit 1 · **10건** · 15행 **안 풀림** · 36행 `unknown` · 41·45행 `void` |
| ★ 거짓 단언 | `tsc ex.14b.ts` + `node ex.14b.js` | ★★★ **tsc exit 0 · 진단 0건** · node exit 0 · 다섯 줄 중 **넷이 터졌다** |
| `TS2775` 격자 | `--noEmit ex.14c.ts` | exit 1 · **9건** · `TS2775` **2건**(35·47행) · 막힌 뒤 `unknown` |
| `asserts this`·제네릭·대비 | `--noEmit ex.14d.ts` | exit 1 · **8건** · 31·33행(술어) 대 37행(단언) |
| 〃 `strict` 끔 | `--noEmit --strict false ex.14d.ts` | exit 1 · **17행만** 글자가 바뀜 |
| 문법 경계 | `--noEmit ex.14e.ts` | exit 1 · **4건** · 전부 `TS1xxx` |
| `node:assert` 선언 없이 | `--noEmit --module commonjs ex.14f.ts` | exit 1 · **`TS2591`** · 좁히기 안 일어남 |
| 〃 선언과 함께 | `--noEmit --module commonjs node-assert.d.ts ex.14f.ts` | exit 1 · 7행이 **`string \| number`** |
| 〃 방출·실행 | `tsc --module commonjs …` + `node ex.14f.js` | ★ **tsc exit 2** · node exit 0 · `assert(0)`·`assert(null)` 이 **던졌다** |
| 종료 코드 대조 | 같은 입력을 `--noEmit` 과 방출로 | ★★★ **exit 1 / exit 2** |
| `strict` 대조 | 네 파일을 `--strict false` 로 재실행 | ★ **`ex.14d.ts` 하나만** 갈림 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ `TS2591` 의 문구가 모듈 지정자에 「**Cannot find name**」이라고 말하는 것 — 7.0.2 의 보고 방식이다.
- ★★ `node:assert` 의 실패 메시지 전문(소스 인용 포함) — `node` v18 의 것이다.
- 런타임 예외 문구 `v.toUpperCase is not a function` — `node` v18 의 메시지다.
- `TS2775`·`TS1228` 의 문구 전문 — 코드가 더 오래 간다.
- 파스 에러 하나가 **네 줄로 퍼지는** 모양 — 파서의 복구 전략이다.

**안 돌려 본 것**

- **`@types/node` 를 실제로 설치한 판** — `node_modules` 를 만들지 않았다. 6번의 선언은 **직접 쓴 한 장**이다.
- **`assert.ok`·`assert.strictEqual` 같은 멤버** — **안 던졌다.**
- **`asserts` 와 오버로드의 조합** — [**16번 주제**](../16-function-types-and-overloads/). **안 던졌다.**
- **단언 함수를 제네릭 제약과 섞는 깊은 예** — [목록의 **20번 주제**](../20-generic-constraints-and-defaults/). **안 던졌다.**
- **단언이 많을 때의 검사 시간** — **재지 않았고 수치를 적지 않았다.**
