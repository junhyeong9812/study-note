# ts/syntax/13 — 타입 가드와 타입 술어 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Narrowing: Using type predicates](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates) ·
> [Handbook — Narrowing: Assertion functions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) ·
> [TypeScript 5.5 릴리스 노트 — Inferred Type Predicates](https://devblogs.microsoft.com/typescript/announcing-typescript-5-5/).
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
> **버전** — `x is T` 술어는 TS 1.6, `asserts x is T` 는 3.7, **추론된 타입 술어는 5.5** 다.
> ★★★ 「5.5 기능이 7.0 에서도 도는가」는 **외우지 않고 던져서 확인했다** — 4·5절이 그 결과다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·`(행,열)`·종료 코드·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ **2절의 「진단 0건」** — 이 주제의 본체다 | 소스 전문을 옆에 뒀으니 다시 던질 수 있다 |
| **안 흔들린다** | ★ 런타임 예외 문구 `v.toUpperCase is not a function` | `node` v18 의 메시지다. **판이 오르면 문구가 바뀔 수 있다** |
| **★ 설정에 달렸다** | 5절 격자의 **한 칸**(`viaAnd`) | `strictNullChecks`. 양쪽을 다 실었다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다. 예외도 `message` 만 찍어 **스택을 안 남겼다** |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★★ **2절은 진단이 한 줄도 없다.** 그러므로 **소스 전문과 실행 출력이 곧 근거**다 — 셋을 나란히 실었다.

## 한눈에 — 쉽게 말하면

**타입 술어는 「내가 확인했다」는 도장이다. 컴파일러는 도장을 믿고 안을 안 본다.**

| 비유 | 실체 |
|---|---|
| 상자를 열어 보고 **「신발 맞음」 도장**을 찍는다 | **`p is Cat`** — 반환 타입 자리에 적는 술어 |
| 다음 사람은 **도장만 보고** 신발로 다룬다 | 호출한 쪽에서 **좁혀진다** |
| ★★★ 도장은 **찍은 사람이 책임진다** | 본문이 틀려도 **컴파일러는 아무 말도 안 한다** |
| 도장이 거짓이면 **물건을 꺼낼 때** 터진다 | `v.toUpperCase is not a function` |
| 「아니면 **돌아오지 않는다**」는 도장도 있다 | **`asserts v is string`** — 부르고 나면 좁혀져 있다 |
| ★ 요즘은 **도장을 안 찍어도** 알아봐 준다 | **추론된 타입 술어**(5.5) — 조건이 맞으면 자동 |
| 다만 알아봐 주는 **조건이 까다롭다** | 여덟 모양 중 **둘만** 통과했다 |

- ★★★ 한 줄로 — 「**술어는 검사가 아니라 선언이다. 검사는 사람이 한다.**」
- ★★ 그래서 이 주제의 값은 「어떻게 쓰나」가 아니라 「**어디까지 믿어도 되나**」에 있다.

```text
  술어가 하는 일

  function isCat(p: Cat | Dog): p is Cat {
      return "meow" in p;     ←─ 컴파일러는 이 줄의 **뜻**을 안 본다
  }                                  요구하는 것은 "boolean 을 돌려준다" 하나뿐

  if (isCat(p)) { … }         ←─ 여기서는 p 가 Cat 이라고 **믿는다**
```

```text
  세 층으로 나눠 보면

  ① 내장 가드        typeof · instanceof · in · 진릿값 · ===     ← 12번 주제
  ② 술어 함수        function isX(v): v is X                     ← 이 주제
  ③ 단언 함수        function assertX(v): asserts v is X         ← 이 주제 + 14번 주제
        │
        ▼  ①은 컴파일러가 뜻을 안다. ②·③은 **사람 말을 믿는다.**
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **술어를 적으면 무엇이 달라지나** — `in` 을 그대로 쓰는 것·함수로 감싸는 것과 **셋을 나란히** 던진다.
2. **틀린 술어를 컴파일러가 잡나** — **잡지 않는다.** 던져서 런타임에 깨뜨린다. **이 주제의 본체다.**
3. **안 적어도 되나** — 5.5 의 추론된 타입 술어가 이 판에서 도는지, **어떤 조건에서** 붙는지 격자로 확인한다.

★ [**12번 주제**](../12-narrowing/)가 좁히기 수단을 세웠다면 여기는 **그 수단을 함수로 포장**하는 법이다. **12 → 13 은 한 사슬**이다.
[**04번 주제**](../04-any-unknown-never-void/)의 「`unknown` 으로 받아 좁히기를 강제한다」는 설계가 6절에서 완성된다.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★ **분기마다 박은 `null` 탐침** | 술어가 실제로 좁혔는지 | [**12번 주제**](../12-narrowing/)에서 이어받음 |
| ★★★ **방출 `.js` + `node` 실행** | **컴파일러가 안 잡은 것을 런타임이 잡는 것** | ★ 이 주제의 본체 |
| ★ **같은 파일을 `--strict false` 로 다시** | 추론 조건 한 칸이 설정에 달린 것임을 | [**12번 주제**](../12-narrowing/)에서 이어받음 |

★★★ 둘째 창이 이 주제의 고유한 자리다. **진단이 0건인 블록을 근거로 쓰려면 실행 출력이 꼭 있어야 한다.**

비용 — 컴파일 한 번 + 실행 한 번.

### (1) ★★★ 술어 · 인라인 `in` · 감싼 함수 — 셋을 나란히

**언제 쓰나** — 「검사를 함수로 빼냈더니 좁히기가 사라졌다」에서 막힐 때.

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

```text
===== tsc --pretty false --noEmit ex.13a.ts (tsc exit=1) =====
ex.13a.ts(17,15): error TS2322: Type 'Cat' is not assignable to type 'null'.
ex.13a.ts(19,15): error TS2322: Type 'Dog' is not assignable to type 'null'.
ex.13a.ts(25,15): error TS2322: Type 'Cat' is not assignable to type 'null'.
ex.13a.ts(27,15): error TS2322: Type 'Dog' is not assignable to type 'null'.
ex.13a.ts(36,15): error TS2322: Type 'Cat | Dog' is not assignable to type 'null'.
  Type 'Cat' is not assignable to type 'null'.
ex.13a.ts(45,11): error TS2322: Type 'Cat' is not assignable to type 'null'.
ex.13a.ts(49,5): error TS2322: Type 'number' is not assignable to type 'boolean'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **일곱 건**이다 — 17·19·25·27·36·45·49행.
- 17·19행 — 술어 함수 `isCat` 을 쓰면 `Cat` 과 `Dog` 로 깔끔하게 갈린다.
- 25·27행 — `"meow" in p` 를 **인라인으로** 써도 **같은 결과**다. 술어는 그 검사를 **옮겨 담은 것**이다.
- ★★★ 36행이 이 절의 별이다. `wrapped(p): boolean` 은 몸통이 `"meow" in p` 로 **똑같은데** 좁히지 못한다 —\
  `p` 가 **`Cat | Dog`** 그대로다. **반환 타입을 `boolean` 이라고 적는 순간 「무엇을 확인했는지」가 사라진다.**
- ★★ 즉 술어 표기가 하는 일은 **그 정보를 반환 타입에 실어 보내는 것**이다.
- 45행 — `isCatLoose(u)` 는 `unknown` 도 좁힌다. **받는 매개변수 타입은 아무거나 돼도 된다.**
- ★ 49행만 다른 코드다. `return 1;` 이 `TS2322`, 「Type 'number' is not assignable to type 'boolean'.」 —\
  **컴파일러가 술어 함수에 요구하는 것은 「`boolean` 을 돌려준다」 하나뿐**이다.

> **타입 술어(type predicate)** — 반환 타입 자리에 적는 `매개변수 is 타입` 표기(TS 1.6).\
> 예: `function isCat(p: Cat \| Dog): p is Cat`. 호출한 쪽에서 좁히기가 일어난다.

비용 — 없음. 다만 **본문이 맞는지는 아무도 안 본다** — 다음 절이 그 대가다.

### (2) ★★★ 술어가 거짓말을 해도 컴파일러는 믿는다

**언제 쓰나** — 「타입이 맞는데 런타임에 터졌다」의 원인을 찾을 때. **이 절이 이 주제의 본체다.**

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

```text
===== tsc --pretty false ex.13b.ts (tsc exit=0) =====
===== 방출된 ex.13b.js =====
"use strict";
function isString(v) {
    return typeof v === "number";
}
function alwaysTrue(v) {
    return true;
}
function shout(v) {
    if (isString(v)) {
        return v.toUpperCase();
    }
    return "문자열이 아니다";
}
function shoutHard(v) {
    if (alwaysTrue(v)) {
        return v.toUpperCase();
    }
    return "닿지 않는다";
}
function run(label, f) {
    try {
        console.log(label, f());
    }
    catch (e) {
        console.log(label, "터졌다 ->", e.message);
    }
}
run("shout('hi')  :", () => shout("hi"));
run("shout(7)     :", () => shout(7));
run("shoutHard(7) :", () => shoutHard(7));
run("shoutHard('a'):", () => shoutHard("a"));
```

```text
===== node ex.13b.js (node exit=0) =====
shout('hi')  : 문자열이 아니다
shout(7)     : 터졌다 -> v.toUpperCase is not a function
shoutHard(7) : 터졌다 -> v.toUpperCase is not a function
shoutHard('a'): A
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **진단이 한 줄도 없다. 종료 코드가 `0` 이다.** `isString` 의 몸통은 `typeof v === "number"` 인데도 그렇다.
- `alwaysTrue` 는 아예 `return true;` 다. 그것도 통과한다 — **요구 조건은 `boolean` 하나뿐**이기 때문이다(1절 49행).
- 방출된 `.js` 에는 술어 표기가 **한 글자도 안 남는다.** `function isString(v) { return typeof v === "number"; }` 뿐이다.
- ★★★ 실행 결과의 첫 줄이 **거짓말의 첫 얼굴**이다 — `shout("hi")` 가 **`문자열이 아니다`** 를 돌려준다.\
  진짜 문자열을 넣었는데 「아니다」라고 한다. `isString("hi")` 가 `typeof "hi" === "number"` 라서 **`false`** 이기 때문이다.
- ★★★ 둘째 줄이 **두 번째 얼굴**이다 — `shout(7)` 이 **터진다**. 「`v.toUpperCase is not a function`」.\
  `isString(7)` 이 `true` 를 돌려주었고, 컴파일러는 그 안에서 `v` 를 `string` 으로 믿어 `v.toUpperCase()` 를 통과시켰다.
- 셋째 줄 — `alwaysTrue` 는 **항상** 참이니 `shoutHard(7)` 도 같은 예외다.
- ★ 넷째 줄 `shoutHard("a")` 가 `A` 인 것이 **거짓 술어가 늘 터지지는 않는다**는 것을 보여 준다.\
  **우연히 맞을 때는 조용히 지나간다** — 그래서 더 늦게 발견된다.

```text
  컴파일 시각                        런타임
  ─────────────────────────────────────────────────────────
  isString(v): v is string           isString(7) -> true   ← 몸통이 거짓말
        │                                  │
        ▼                                  ▼
  v 는 string 이다 (믿는다)          7.toUpperCase()
  v.toUpperCase() 통과               TypeError
        │                                  │
        ▼                                  ▼
  tsc exit 0 · 진단 0건              node 가 대신 말한다
```

> **거짓 술어** — 몸통이 실제로 확인하지 않는데 `x is T` 를 적은 함수.\
> **컴파일러는 검사하지 않는다.** 요구 조건은 「`boolean` 을 돌려준다」 하나뿐이다.

비용 — ★★★ **술어 하나가 그 타입의 안전을 통째로 책임진다.** 단언(`as`)과 같은 등급의 탈출구다(목록의 **30번 주제**).

### (3) ★★ `asserts x is T` — 돌아오면 좁혀져 있다

**언제 쓰나** — 「검사에 실패하면 던지고, 통과하면 그 뒤로 계속 좁혀진 채로」가 필요할 때.

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

```text
===== tsc --pretty false --noEmit ex.13c.ts (tsc exit=1) =====
ex.13c.ts(11,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.13c.ts(16,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.13c.ts(23,5): error TS2775: Assertions require every name in the call target to be declared with an explicit type annotation.
ex.13c.ts(24,11): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.13c.ts(30,11): error TS2322: Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **다섯 건**이고 그중 **`TS2775` 하나만** 종류가 다르다.
- 11행 — `assertString(v)` 를 부른 **뒤부터** `v` 가 **`string`** 이다. `if` 가 없어도 좁혀진다.
- 16행 — 제네릭 단언도 된다. `assertDefined<T>(v): asserts v is NonNullable<T>` 뒤의 `v` 가 **`string`** 이다.
- ★★★ 23행이 이 절의 함정이다. **화살표 함수를 `const` 에 담아 쓰면 `TS2775` 로 막힌다** —\
  「Assertions require every name in the call target to be declared with an explicit type annotation.」
- ★★ 24행이 그 대가를 보여 준다 — 막힌 뒤의 `v` 는 **`unknown`** 그대로다. **좁히기가 아예 안 일어난다.**
- ★★ 29·30행이 고치는 법이다. `const assertTyped: (v: unknown) => asserts v is string = assertArrow;` 처럼\
  **변수에 타입을 명시**하면 통과하고 `v` 가 `string` 이 된다.
- ★★★ 38행이 침묵한다 — `assertNothing` 의 몸통은 `return;` 뿐인데 그 뒤의 `const after: string = v;` 가 **통과한다.**\
  **단언도 2절과 똑같이 검사되지 않는다.** 술어보다 더 위험하다 — 「아니면 던진다」는 약속까지 사람 몫이기 때문이다.

> **단언 시그니처(assertion signature)** — `asserts x is T` 로 적어, **정상 반환 = 그 타입임**을 선언하는 표기(TS 3.7).\
> 예: `function assertString(v: unknown): asserts v is string`. **부르는 이름에 명시적 타입이 필요하다**(`TS2775`).

비용 — **호출 형태에 제약이 붙는다.** 전면 서술은 [목록의 **14번 주제**](../14-assertion-signatures/)다.

### (4) ★★★ 술어를 안 적어도 좁혀진다 — 5.5 기능이 이 판에서 돈다

**언제 쓰나** — 「`filter` 로 `null` 을 걸렀는데 타입에 `null` 이 남는다」에서 막힐 때.

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

```text
===== tsc --pretty false --noEmit ex.13d.ts (tsc exit=1) =====
ex.13d.ts(9,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.13d.ts(11,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.13d.ts(17,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.13d.ts(26,7): error TS2322: Type 'number[]' is not assignable to type 'null'.
ex.13d.ts(27,7): error TS2322: Type 'number[]' is not assignable to type 'null'.
ex.13d.ts(34,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.13d.ts(36,15): error TS2322: Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **일곱 건**이다 — 9·11·17·26·27·34·36행.
- ★★★ 9·11행 — `function isStr(v: string | number) { return typeof v === "string"; }` 에 **술어를 안 적었는데**\
  호출한 쪽이 `string` 과 `number` 로 갈린다. **추론된 타입 술어가 이 판에서 돈다.**
- 17행 — 화살표 함수도 같다.
- ★★★ 26·27행이 실무에서 가장 많이 쓰이는 자리다. `[1, null, 2].filter(notNull)` 이 **`number[]`** 다 —\
  `(number | null)[]` 가 아니다. 인라인 화살표(`(v) => v !== null`)도 **같은 결과**다.
- ★★ 34·36행 — `negated` 는 `typeof v !== "string"` 이라 **뒤집힌 술어**가 추론된다.\
  참 갈래가 **`number`**, 거짓 갈래가 **`string`** 이다.
- ★ 5.5 이전에는 이 자리마다 `(v): v is number => v !== null` 처럼 **술어를 손으로 적어야** 했다.

> **추론된 타입 술어(inferred type predicate)** — 술어를 적지 않아도 함수 몸통에서 술어를 뽑아내는 기능(TS 5.5).\
> 예: `function isStr(v: string \| number) { return typeof v === "string"; }`. **조건이 까다롭다**(다음 절).

비용 — 없음. 다만 **언제 붙는지 모르면 「왜 어떤 건 되고 어떤 건 안 되지」로 헤맨다.**

### (5) ★★ 추론이 붙는 조건 — 여덟 모양 중 둘

**언제 쓰나** — 4절을 믿고 술어 표기를 다 지우기 전에.

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

```text
===== tsc --pretty false --noEmit ex.13e.ts (tsc exit=1) =====
ex.13e.ts(32,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(35,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(38,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(41,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(44,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(47,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.13e.ts(50,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.13e.ts(53,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 탐침이 **여덟 개**이고 진단도 여덟 건이다. 읽을 것은 「몇 건」이 아니라 「**무엇이라고**」다.
- ★★★ **좁혀진 것은 47행(`viaConstAlias`)과 50행(`viaAnd`) 둘뿐**이다. 나머지 여섯은 **`string | number`** 그대로다.
- 32행 `explicitBool` — **반환 타입을 `boolean` 이라고 적으면 추론이 꺼진다.** 적은 것이 이긴다.
- 35행 `multiReturn` — `if (…) return true; return false;` 는 **안 붙는다.** **반환이 하나여야 한다.**
- 38행 `reassigned` — 몸통에서 **매개변수를 재대입**하면 안 붙는다.
- ★★ 41행 `viaOther` — `const w = v; return typeof w === "string";` 는 **안 붙는다.**\
  **좁히는 대상이 매개변수 자신**이어야 한다.
- ★★ 44행 `withExtraTest` — `typeof v === "string" && v.length > 0` 은 **안 붙는다.**\
  `&&` 의 **모든 항이 좁히기 검사**여야 한다 — `v.length > 0` 은 값 비교다.
- ★★★ 47행 `viaConstAlias` — `const ok = typeof v === "string"; return ok;` 는 **붙는다.**\
  [**12번 주제**](../12-narrowing/)의 **별칭 조건**(4.4)이 여기서도 그대로 쓰인다.
- 50행 `viaAnd` — `v !== null && typeof v === "string"` 은 **붙는다.** 두 항이 다 좁히기 검사다.
- 53행 `declaredOnly` — **몸통이 없는 선언**에는 뽑아낼 것이 없다.

★★ 이 격자 중 **설정에 달린 칸이 하나** 있다. 같은 파일을 `--strict false` 로 다시 던졌다.

```text
===== tsc --pretty false --noEmit --strict false ex.13e.ts (tsc exit=1) =====
ex.13e.ts(32,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(35,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(38,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(41,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(44,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(47,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.13e.ts(50,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.13e.ts(53,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

- ★★★ **50행만 답이 바뀐다** — `viaAnd` 가 더는 좁히지 못한다.
- ★★ 플래그를 끄면 `w: string | number | null` 이 **`string | number`** 가 되어 `v !== null` 이 **좁히지 않는 검사**가 된다.\
  그러면 `&&` 의 한 항이 좁히기가 아니게 되고, 44행 `withExtraTest` 와 **같은 이유로** 추론이 꺼진다.
- ★ 나머지 일곱 줄은 글자 하나까지 같다.

```text
  추론된 타입 술어가 붙는 조건 — 이 판에서 던진 여덟 모양

  ✗ 반환 타입을 boolean 으로 적음          explicitBool
  ✗ return 이 여러 개                      multiReturn
  ✗ 몸통에서 매개변수를 재대입             reassigned
  ✗ 매개변수가 아닌 값을 좁힘              viaOther
  ✗ && 에 좁히기가 아닌 항이 섞임          withExtraTest
  ✓ 검사 결과를 const 에 담아 반환          viaConstAlias
  ✓ && 의 모든 항이 좁히기 검사            viaAnd   ★ strictNullChecks 를 끄면 ✗
  ✗ 몸통이 없는 선언                       declaredOnly
```

비용 — 없음. 다만 **공개 API 에는 술어를 직접 적는 편이 낫다** — 조건이 미묘해 리팩터링 한 줄에 조용히 꺼진다.

### (6) ★★★ `unknown` 을 받아 좁히는 관용구

**언제 쓰나** — 바깥에서 들어온 값(JSON·`fetch`·`localStorage`)을 다룰 때. **04 의 설계가 여기서 완성된다.**

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

```text
===== tsc --pretty false ex.13f.ts (tsc exit=0) =====
===== 방출된 ex.13f.js =====
"use strict";
function isUser(v) {
    return (typeof v === "object" &&
        v !== null &&
        "id" in v &&
        typeof v.id === "number" &&
        "name" in v &&
        typeof v.name === "string");
}
function greet(raw) {
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

```text
===== node ex.13f.js (node exit=0) =====
정상      : 안녕 준(#1)
필드 빠짐  : 모르는 모양이다
타입 어긋남: 모르는 모양이다
null      : 모르는 모양이다
배열      : 모르는 모양이다
```

그림 해설 — 한 단계에 한 문장.

- ★★★ `tsc` 종료 코드가 **`0`** 이다 — 진단이 없다. 다만 2절과 달리 **여기서는 몸통이 진짜로 검사한다.**
- 몸통이 네 가지를 차례로 본다 — `typeof v === "object"` · `v !== null` · `"id" in v` · `typeof (v as …).id === "number"`.\
  [**12번 주제**](../12-narrowing/)의 수단이 그대로 쓰였다.
- ★★ `(v as { id: unknown }).id` 라는 단언이 필요한 이유는 `in` 만으로는 **그 칸의 타입까지는** 안 좁혀지기 때문이다.
- 방출된 `.js` 에서 그 단언이 **사라진다** — `typeof v.id === "number"` 만 남는다. **검사는 그대로 돌고 표기만 지워진다.**
- ★★★ 실행 결과 다섯 줄이 **몸통이 진짜로 일한다는 증거**다 — 정상만 통과하고 필드 빠짐·타입 어긋남·`null`·배열이 전부 걸린다.
- ★ 특히 `null` 과 배열이 걸리는 것이 중요하다. `typeof null === "object"` 이고 `typeof [] === "object"` 라서\
  **`typeof` 검사 하나로는 못 막는다**([**12번 주제**](../12-narrowing/)).

> **`unknown` 으로 받아 좁히기** — 외부 입력을 `any` 가 아니라 `unknown` 으로 받아 **술어를 통과해야만** 쓰게 하는 설계.\
> `any` 로 받으면 검사 없이 아무 멤버나 쓸 수 있다([**04번 주제**](../04-any-unknown-never-void/)).

비용 — **검사 코드를 사람이 다 적어야 한다.** 필드가 많으면 스키마 검증 라이브러리로 간다 — 이 배치에서는 **안 던졌다.**

### (7) ★ `strict` 를 꺼도 대부분 같다

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.13a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.13c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.13d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.13e.ts    exit 1 / exit 1 · ★ 다르다
```

- ★★ 네 파일 중 **`ex.13e.ts` 하나만** 갈린다(5절). 나머지 셋은 **종료 코드도 출력도 글자 하나까지 같다.**
- ★ 술어·단언의 **문법과 신뢰 모델**은 `strict` 와 무관하다. 갈리는 것은 **추론 조건 한 칸**뿐이다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  function isCat(p: Cat | Dog): p is Cat { … }          ★ 타입 술어 (1.6)
  function isCatLoose(p: unknown): p is Cat { … }        unknown 도 받는다
  function assertString(v: unknown): asserts v is string ★ 단언 시그니처 (3.7)
  const at: (v: unknown) => asserts v is string = fn     ★ 이 표기가 있어야 부를 수 있다

  function isStr(v: string | number) {                   ★ 추론된 타입 술어 (5.5)
      return typeof v === "string";                        — 술어를 안 적어도 붙는다
  }
  [1, null, 2].filter((v) => v !== null)                 -> number[]
```

**규칙 불릿**

- ★★★ **컴파일러가 술어 함수에 요구하는 것은 「`boolean` 을 돌려준다」 하나뿐**이다(`TS2322`). **몸통의 뜻은 안 본다.**
- ★★★ **거짓 술어는 진단 0건으로 통과하고 런타임에 터진다.** 단언(`as`)과 같은 등급의 탈출구다.
- ★★ **반환 타입을 `boolean` 으로 적으면** 검사를 그대로 옮겨 담아도 **좁히기가 끊긴다**(1절 36행).
- ★★ **`asserts x is T` 는 부르는 이름에 명시적 타입이 필요하다**(`TS2775`). 없으면 **좁히기가 아예 안 일어난다.**
- ★★ **단언도 검사되지 않는다** — 몸통이 `return;` 뿐이어도 통과한다(3절 38행).
- ★★★ **추론된 타입 술어(5.5)가 이 판에서 돈다** — `filter(notNull)` 이 `number[]` 다.
- ★★ **추론 조건은 다섯**이다 — 반환 타입 미기재 · `return` 하나 · 매개변수 재대입 없음 · **매개변수 자신**을 좁힘 · `&&` 의 **모든 항이 좁히기 검사**.
- ★ **`unknown` 으로 받아 술어로 좁히는 것**이 외부 입력을 다루는 정석이다([**04번 주제**](../04-any-unknown-never-void/)).

**금지 사례** — 이 주제에서 던져 받은 것 셋이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 술어 함수가 boolean 이 아닌 값 반환  ->  TS2322  Type 'number' is not assignable to type 'boolean'.
2) 타입 표기 없는 const 로 단언 함수 호출 ->  TS2775  Assertions require every name in the call target to be
                                                     declared with an explicit type annotation.
3) ★ 거짓 술어                          ->  진단 없음. tsc exit 0. 런타임에 TypeError
```

## 어디서 틀리나

- ★★★ 「**`x is T` 를 적으면 컴파일러가 몸통을 확인해 준다**」 — **안 한다.** 2절이 진단 0건으로 통과하고 런타임에 터진다.
- ★★★ 「**검사를 함수로 빼도 좁히기는 그대로**」 — 반환 타입이 `boolean` 이면 **끊긴다**(1절 36행).
- ★★ 「**5.5 기능이니 7.0 에서는 다르겠지**」 — 이 판에서 **그대로 돈다**(4절). 다만 **외우지 말고 던져서 확인하라.**
- ★★ 「**추론된 술어가 있으니 표기는 필요 없다**」 — 여덟 모양 중 **둘만** 붙었다. 공개 API 에는 적는 편이 낫다.
- ★★ 「**`asserts` 는 그냥 부르면 된다**」 — 화살표를 `const` 에 담으면 `TS2775` 다. 게다가 **좁히기가 아예 안 일어난다.**
- ★ 「**`asserts` 는 술어보다 안전하다**」 — 더 위험하다. 「아니면 던진다」까지 사람 몫이고 **그것도 검사되지 않는다**(3절 38행).
- ★ 「**`return true;` 는 에러겠지**」 — 통과한다. 요구 조건은 `boolean` 하나뿐이다.
- ★ 「**거짓 술어는 곧 터진다**」 — **우연히 맞으면 조용하다**(2절 넷째 줄 `shoutHard("a")` 가 `A`).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | `x is T` 는 호출한 쪽에서 **좁힌다** | 핸드북 「Using type predicates」. 1절 17·19·45행 |
| **언어 보장** | 요구 조건은 **`boolean` 반환** 하나뿐 | 1절 49행 `TS2322` |
| **언어 보장** | ★★★ **몸통은 검사되지 않는다** | 2절 — 진단 0건 · `tsc exit 0` · 런타임 `TypeError` |
| **언어 보장** | `asserts x is T` 는 **정상 반환 = 그 타입** | 3절 11·16행 |
| **언어 보장** | 단언 호출은 **명시적 타입 표기**를 요구한다 | 3절 23행 `TS2775` |
| **언어 보장** | **추론된 타입 술어**가 조건을 만족하면 붙는다 | 4·5절. `filter(notNull)` 이 `number[]` |
| **★ 설정에 달림** | 5절 격자의 **한 칸**(`viaAnd`) | `strictNullChecks`. **양쪽 판을 다 실었다** |
| **이 판(7.0.2)의 관찰** | ★★ **추론 조건의 세부**(단일 `return`·`&&` 의 모든 항) | 5.5 의 구현이다. **판이 오르면 넓어질 수 있다** — 다시 던져라 |
| **이 판의 관찰** | 런타임 예외 문구 `v.toUpperCase is not a function` | `node` v18 의 메시지다 |
| **이 판의 관찰** | 진단 문구 전문 | 코드(`TS2322`·`TS2775`)가 더 오래 간다 |
| **안 잰 것** | 술어가 많을 때의 **검사 시간** | 재지 않았다 |

★★★ 「**진단 0건」이 근거인 블록이 하나**다(2절). 그 블록은 **소스 전문 + 방출 전문 + 실행 출력** 셋을 다 실어야 근거가 된다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| 검사를 **여러 곳에서 재사용** — 술어 함수 | 한 곳에서만 쓰는 검사 — 인라인 `typeof`·`in` 이 더 안전하다 |
| 외부 입력 — **`unknown` 을 받아 술어로** | `any` 로 받는 것 — 검사가 아예 안 걸린다 |
| `filter` 로 `null` 걸러내기 — **추론에 맡겨도 된다** | 공개 API 의 술어를 추론에 맡기는 것 — 조건이 미묘하다 |
| 「없으면 더 갈 수 없다」 — **`asserts`** | 되돌릴 수 있는 분기에 `asserts` — 예외가 과하다 |
| 몸통이 **정말로 확인하는** 술어 | 편의를 위해 `return true` 로 때우는 술어 — `as` 와 같다 |

## 핵심 문장

1. **술어는 검사가 아니라 선언이다** — 요구 조건은 `boolean` 반환 하나뿐이다.
2. **거짓 술어는 진단 0건으로 통과한다** — 컴파일러는 도장을 믿고 안을 안 본다.
3. **반환 타입을 `boolean` 으로 적으면 좁히기가 끊긴다** — 술어 표기가 정보를 실어 나른다.
4. **`asserts` 는 부르는 이름에 타입 표기를 요구한다** — 없으면 좁히기가 아예 안 일어난다.
5. **추론된 타입 술어가 이 판에서 돈다** — 다만 여덟 모양 중 둘만 붙었다.
6. **`unknown` 으로 받아 술어로 좁히는 것**이 외부 입력의 정석이다.

## 관련 자료

- [**12번 주제** — 좁히기](../12-narrowing/) — 술어의 **몸통에 들어가는 수단**은 전부 그쪽이다. **12 → 13 은 한 사슬**이다.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — 「`unknown` 으로 받아 좁히기를 강제한다」는 설계는 그쪽. 6절이 그것을 완성한다.
- [**09번 주제** — 유니온 타입](../09-union-types/) — 술어가 좁히는 대상은 대개 유니온이다.
- [**10번 주제** — 인터섹션 타입](../10-intersection-types/) — 검사를 `&&` 로 이으면 결과가 교차로 합쳐진다.
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — 판별 칸이 리터럴이어야 하는 이유는 그쪽.
- [목록의 **14번 주제**](../14-assertion-signatures/)(단언 시그니처 `asserts`) — 3절의 전면 서술은 그쪽. 여기서는 **`TS2775` 와 「검사되지 않는다」까지**.
- [목록의 **16번 주제**](../16-function-types-and-overloads/)(함수 타입과 오버로드) — 술어 함수를 오버로드에 섞을 때의 규칙은 그쪽.
- 목록의 **30번 주제**(타입 단언과 non-null `!`) — 거짓 술어가 `as` 와 **같은 등급의 탈출구**라는 것은 그쪽과 함께 읽는다.
- [목록의 **19번 주제**](../19-generics-basics/)(제네릭 기본) — 4절의 `notNull<T>` 가 제네릭 술어의 맛보기다.

## 용어 풀이

> **타입 가드(type guard)** — 좁히기를 일으키는 검사. `typeof`·`instanceof`·`in` 같은 내장 가드와 **술어 함수**가 있다.

> **타입 술어(type predicate)** — 반환 타입 자리에 적는 `매개변수 is 타입` 표기(TS 1.6).\
> 예: `function isCat(p: Cat \| Dog): p is Cat`.

> **단언 시그니처(assertion signature)** — `asserts x is T` 로 적어 **정상 반환 = 그 타입임**을 선언하는 표기(TS 3.7).\
> 예: `function assertString(v: unknown): asserts v is string`.

> **추론된 타입 술어(inferred type predicate)** — 술어를 안 적어도 몸통에서 뽑아내는 기능(TS 5.5).\
> 조건이 까다롭다 — 5절의 격자를 보라.

> **거짓 술어** — 몸통이 실제로 확인하지 않는데 `x is T` 를 적은 함수.\
> **컴파일러는 검사하지 않는다.**

## 더 들어가면

- **왜 몸통을 검사하지 않나** — 「이 몸통이 정말 `T` 임을 증명하는가」는 **일반적으로 판정 불가능**하다. 임의의 검사 코드의 의미를 타입 시스템이 알 수는 없다. 그래서 TS 는 **선언으로 두고 책임을 사람에게 넘긴다** — `as` 와 같은 자리다.
- **술어를 안전하게 쓰는 수** — 몸통을 **내장 가드만으로** 짜고(12번 주제) 다른 함수를 부르지 않으면 실수할 여지가 준다. 6절의 `isUser` 가 그 모양이다.
- **스키마 검증 라이브러리** — 필드가 많아지면 술어를 손으로 적는 것이 한계다. 검증기가 술어를 만들어 주는 방식이 흔하다. **이 배치에서는 안 던졌고 이름도 적지 않는다.**
- **추론 조건이 넓어질 가능성** — 5절의 다섯 조건은 **5.5 구현의 경계**다. 판이 오르면 넓어질 수 있다 — **외우지 말고 다시 던져라.** 이 문서가 그 격자를 남겨 둔 이유다.
