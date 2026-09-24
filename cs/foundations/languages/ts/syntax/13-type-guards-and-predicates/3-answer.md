# ts/syntax/13 — 타입 가드와 타입 술어 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 2번은 **진단이 한 줄도 없는 것이 답**이다. 그런 블록을 근거로 쓰려면 **소스 전문 + 방출 전문 + 실행 출력** 셋이 다 있어야 한다 — 그렇게 실었다.\
> ★★ 3번의 38행도 「**에러가 안 난 줄**」이 답이다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **7건** — 술어와 인라인 `in` 은 같고, **감싼 함수만 끊긴다**

**출력**

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

**왜 그런가**

| 줄 | 모양 | 결과 |
|---|---|---|
| 17·19 | `isCat(p)` — **술어 함수** | `Cat` / `Dog` |
| 25·27 | `"meow" in p` — **인라인** | `Cat` / `Dog` — ★ **같다** |
| 36 | `wrapped(p): boolean` — **감싼 함수** | ★★★ **`Cat \| Dog`** — 안 좁혀진다 |
| 45 | `isCatLoose(u)` — `unknown` 을 받는 술어 | `Cat` |
| 49 | `return 1;` — 술어 함수가 숫자 반환 | **TS2322** — 「Type 'number' is not assignable to type 'boolean'.」 |

- ★★★ **17행과 36행의 차이가 이 주제의 전부다.** 두 함수의 몸통은 `"meow" in p` 로 **글자까지 같은데**,\
  반환 타입이 `p is Cat` 이냐 `boolean` 이냐로 갈린다.
- ★★ 즉 **술어 표기가 하는 일은 「무엇을 확인했는지」를 반환 타입에 실어 보내는 것**이다.\
  `boolean` 이라고 적으면 그 정보가 **호출한 쪽으로 못 넘어간다**([**12번 주제**](../12-narrowing/)의 「좁히기는 제어 흐름을 따른다」 — 함수 경계를 넘으면 흐름이 끊긴다).
- ★★★ 49행이 **컴파일러가 요구하는 것의 전부**를 보여 준다 — 「`boolean` 을 돌려주라」. **몸통의 뜻은 요구하지 않는다.**
- ★ 45행 — 매개변수가 `unknown` 이어도 된다. 6번의 관용구가 그 위에 선다.

### 2. ★★★ **진단 0건 · `tsc exit 0`** — 그리고 런타임이 터진다

**출력**

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

**왜 그런가**

| 확인 | 값 |
|---|---|
| `tsc` 종료 코드 | ★★★ **`0`** |
| 진단 건수 | ★★★ **0건** |
| `shout("hi")` | ★★★ **`문자열이 아니다`** — 진짜 문자열인데 「아니다」 |
| `shout(7)` | ★★★ **터졌다** — `v.toUpperCase is not a function` |
| `shoutHard(7)` | **터졌다** — 같은 예외 |
| `shoutHard("a")` | ★ **`A`** — 우연히 맞으면 조용하다 |

- ★★★ 컴파일러가 검사하지 않는 것은 「**몸통이 정말 그 타입을 확인하는가**」다.\
  `isString` 의 몸통은 `typeof v === "number"` 인데도 `v is string` 이라는 선언이 그대로 받아들여진다.
- ★★ 검사하는 것은 **딱 하나** — 「`boolean` 을 돌려주는가」(1번의 49행). `alwaysTrue` 의 `return true;` 도 그래서 통과한다.
- ★★★ 거짓말은 **두 얼굴**로 나타난다 —

| 얼굴 | 무엇 | 실행 출력 |
|---|---|---|
| **거짓 음성** | 맞는 값을 「아니다」로 돌려보낸다 | `shout("hi")` → `문자열이 아니다` |
| **거짓 양성** | 틀린 값을 「맞다」로 통과시킨다 | `shout(7)` → `TypeError` |

- ★★ 방출된 `.js` 를 보면 `p is string` 이 **한 글자도 안 남는다.** 남은 것은 몸통의 `typeof v === "number"` 뿐이다 —\
  **런타임에는 술어라는 개념 자체가 없다.**
- ★★★ 그래서 **술어는 `as` 와 같은 등급의 탈출구**다(목록의 **30번 주제**). 다만 `as` 는 한 줄만 속이고,\
  술어는 **그 함수를 부르는 모든 자리**를 속인다 — 더 넓다.
- ★ `shoutHard("a")` 가 `A` 인 것이 왜 늦게 발견되는지 설명한다. **우연히 맞는 입력에서는 아무 일도 안 일어난다.**

### 3. ★★ 진단 **5건** — `TS2775` 하나만 종류가 다르고, **38행은 침묵한다**

**출력**

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

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| 11 | `assertString(v)` 뒤 | **`string`** — `if` 없이 좁혀졌다 |
| 16 | `assertDefined<T>(v)` 뒤 | **`string`** — 제네릭 단언도 된다 |
| 23 | `assertArrow(v)` — `const` 화살표, **타입 표기 없음** | ★★★ **TS2775** |
| 24 | 그 뒤의 `v` | ★★ **`unknown`** — 좁히기가 **아예 안 일어났다** |
| 30 | `assertTyped(v)` — **타입을 명시한 `const`** | **`string`** — 통과 |
| 38 | `assertNothing(v)` 뒤의 `const after: string = v` | ★★★ **침묵** — 몸통이 `return;` 뿐인데 통과 |

- ★★★ **23행과 29행의 차이는 변수에 타입을 적었느냐 하나**다 —

```text
  const assertArrow = (v: unknown): asserts v is string => { … };
        └─ 타입 표기 없음        ->  TS2775  부를 수 없다

  const assertTyped: (v: unknown) => asserts v is string = assertArrow;
        └─ 타입 표기 있음        ->  통과. v 가 string 이 된다
```

- ★★ 왜 그런가 — 단언 함수는 **호출만으로 제어 흐름을 바꾼다.** 컴파일러가 그 사실을 알려면\
  **호출 대상의 타입이 선언 자리에서 확정**돼 있어야 한다. 추론에 맡긴 `const` 는 그 조건을 못 채운다.
- ★★ 24행이 그 대가다. `TS2775` 는 **에러를 내고 끝**이 아니라 **좁히기까지 없앤다** — `v` 가 `unknown` 그대로다.
- ★★★ 38행이 2번과 같은 이야기다. `assertNothing` 은 아무것도 안 던지는데 **그 뒤의 `v` 가 `string` 으로 통한다.**\
  **단언도 검사되지 않는다.** 술어보다 위험한 이유는 「아니면 던진다」는 약속까지 사람 몫이기 때문이다.

### 4. ★★★ **돈다** — 추론된 타입 술어(5.5)가 7.0.2 에서 그대로 작동한다

**출력**

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

**왜 그런가**

| 줄 | 모양 | 결과 |
|---|---|---|
| 9·11 | `function isStr(v)` — **술어 표기 없음** | ★★★ `string` / `number` — **좁힌다** |
| 17 | `const isStrArrow = (v) => typeof v === "string"` | `string` — 화살표도 된다 |
| 26 | `[1, null, 2].filter(notNull)` | ★★★ **`number[]`** |
| 27 | `[1, null, 2].filter((v) => v !== null)` | ★★★ **`number[]`** — 인라인도 된다 |
| 34·36 | `negated` (`typeof v !== "string"`) | ★★ `number` / `string` — **뒤집혀 붙는다** |

- ★★★ **「5.5 기능이니 7.0 에서는 다르겠지」는 틀렸다.** 던져 보니 **그대로 돈다.**\
  이 문서가 그 확인을 **외우지 않고 실행으로** 한 이유다.
- ★★★ 26·27행이 실무에서 가장 큰 이득이다. 5.5 이전에는 `filter((v): v is number => v !== null)` 처럼\
  **술어를 손으로 적어야** `number[]` 가 나왔다. 이제는 그냥 `filter(notNull)` 로 된다.
- ★★ 34·36행 — `!==` 로 적으면 **참 갈래가 `number`** 다. 컴파일러가 **부정까지 따라간다.**
- ★ 제네릭도 된다(`notNull<T>`). 다만 **조건이 까다롭다** — 5번이 그 경계다.

### 5. ★★★ 여덟 모양 중 **둘**만 좁힌다 — `--strict false` 에서는 **하나**

**출력**

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

**왜 그런가**

| 줄 | 모양 | 기본값 | `--strict false` | 왜 |
|---|---|---|---|---|
| 32 | `explicitBool(v): boolean` | ✗ | ✗ | **적은 것이 이긴다** |
| 35 | `multiReturn` — `return` 이 둘 | ✗ | ✗ | **반환이 하나**여야 한다 |
| 38 | `reassigned` — 매개변수 재대입 | ✗ | ✗ | 재대입하면 무엇을 좁혔는지 알 수 없다 |
| 41 | `viaOther` — `const w = v` 를 좁힘 | ✗ | ✗ | ★ **매개변수 자신**을 좁혀야 한다 |
| 44 | `withExtraTest` — `&& v.length > 0` | ✗ | ✗ | ★ `&&` 의 **모든 항이 좁히기 검사**여야 한다 |
| 47 | `viaConstAlias` — `const ok = …; return ok` | ★ **✓** | ★ **✓** | 별칭 조건([**12번 주제**](../12-narrowing/)) |
| 50 | `viaAnd` — `v !== null && typeof v === "string"` | ★ **✓** | ★★★ **✗** | 두 항이 다 좁히기 검사다 |
| 53 | `declaredOnly` — 몸통 없는 선언 | ✗ | ✗ | 뽑아낼 몸통이 없다 |

- ★★★ **41행과 47행의 갈림이 가장 미묘하다.** 둘 다 `const` 를 하나 두었는데 —

| 담은 것 | 결과 |
|---|---|
| `const w = v` — **값**을 담고 그것을 좁힘 | ✗ **안 붙는다** |
| `const ok = typeof v === "string"` — **검사 결과**를 담고 반환 | ★ **붙는다** |

- ★★★ **50행이 설정에 달린 한 칸**이다. `--strict false` 에서는 `w: string | number | null` 이 **`string | number`** 가 되고,\
  그러면 `v !== null` 이 **좁히지 않는 검사**가 된다. `&&` 의 한 항이 좁히기가 아니게 되어 **44행과 같은 이유로** 추론이 꺼진다.
- ★★ 나머지 일곱 줄은 양쪽 판에서 **글자 하나까지 같다.**
- ★★ 그래서 **공개 API 에는 술어를 직접 적는 편이 낫다.** 조건이 미묘해서 **리팩터링 한 줄에 조용히 꺼진다** —\
  꺼져도 에러가 아니라 「그냥 안 좁혀짐」이라 눈치채기 어렵다.

### 6. ★★★ 종료 코드 **0** — 그리고 다섯 입력 중 **하나만** 통과한다

**출력**

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

**왜 그런가**

| 입력 | 출력 | 어느 검사에 걸렸나 |
|---|---|---|
| `{"id":1,"name":"준"}` | ★ **`안녕 준(#1)`** | 전부 통과 |
| `{"id":1}` | `모르는 모양이다` | `"name" in v` |
| `{"id":"1","name":"준"}` | `모르는 모양이다` | `typeof (v as …).id === "number"` |
| `null` | `모르는 모양이다` | ★ `v !== null` — **`typeof null === "object"`** 이라 이것이 필요하다 |
| `[1,2]` | `모르는 모양이다` | `"id" in v` — **배열도 `typeof` 는 `"object"`** 다 |

- ★★★ 2번과 대비하라. **똑같이 진단 0건인데 여기서는 몸통이 진짜로 일한다.**\
  차이는 코드가 아니라 **사람이 제대로 적었는가**에 있다 — 그것이 이 주제의 결론이다.
- ★★ `null` 과 배열이 걸리는 것이 중요하다. 둘 다 `typeof` 가 `"object"` 이므로\
  **`typeof v === "object"` 하나로는 못 막는다**([**12번 주제**](../12-narrowing/)의 함정).
- ★★ `(v as { id: unknown }).id` 라는 단언이 필요한 이유 — `"id" in v` 는 **키가 있다**까지만 좁히고\
  **그 칸의 타입**은 안 준다. 방출된 `.js` 를 보면 그 단언이 **사라지고** `typeof v.id === "number"` 만 남는다.
- ★ 이것이 [**04번 주제**](../04-any-unknown-never-void/)의 설계를 완성한 모습이다 — **`unknown` 으로 받으면 술어를 통과하기 전에는 아무것도 못 쓴다.**\
  `any` 로 받았다면 이 검사들이 **하나도 안 걸렸을** 것이다.

### 7. ★★★ **「이 몸통이 정말 `T` 임을 증명하는가」는 일반적으로 판정 불가능하기** 때문이다

**왜 그런가**

- 술어의 몸통에는 **임의의 JS 코드**가 올 수 있다. 다른 함수를 부르고, 네트워크를 타고, 정규식을 돌릴 수 있다.
- 타입 시스템이 그 코드의 **의미**를 알아내 「이 조건이 참이면 정말 `Cat` 인가」를 판정하는 것은 **일반적으로 불가능**하다.
- ★★ 그래서 TS 는 **판정을 포기하고 선언으로 둔다.** 대신 요구 조건을 최소로 잡는다 — 「`boolean` 을 돌려주라」.
- ★★★ 이것은 게으름이 아니라 **`as` 와 같은 설계 선택**이다. 「내가 책임진다」고 적는 자리를 **명시적으로** 만들어 둔 것이다.
- ★ 뒤집으면 **술어를 쓸 때마다 코드 리뷰의 대상이 하나 늘어난다.** 몸통을 [**12번 주제**](../12-narrowing/)의 내장 가드만으로 짜면 실수할 여지가 준다.
- ★ 5.5 의 **추론된 타입 술어**가 이 문제의 한쪽 답이다 — **컴파일러가 스스로 뽑아낸 술어는 거짓말을 할 수 없다.**\
  그래서 조건이 까다로운 것이기도 하다(5번).

### 8. ★★★ **좁히기는 제어 흐름을 따르는데 함수 경계에서 흐름이 끊기기** 때문이다

**왜 그런가**

- [**12번 주제**](../12-narrowing/)의 결론이 「좁히기는 **이 줄에 오기까지의 경로**를 읽는다」였다.
- `wrapped(p)` 를 부른 자리에서 컴파일러가 아는 것은 「**`boolean` 하나가 돌아왔다**」뿐이다.\
  그 `boolean` 이 **`p` 에 대한 무엇**을 뜻하는지는 반환 타입에 안 적혀 있다.
- ★★ 그래서 **술어 표기가 필요한 것**이다 — 함수 경계를 넘어 「무엇을 확인했는지」를 **실어 나르는 통로**가 그것이다.
- ★★★ 같은 이유로 [**12번 주제**](../12-narrowing/)의 **클로저**에서도 좁히기가 풀렸다. **경계를 넘으면 흐름 정보가 끊긴다**는 한 가지 규칙이다.
- ★ 5.5 의 추론된 술어는 그 통로를 **컴파일러가 대신 놓아 주는** 것이다. 놓아 줄 수 있는 모양이 제한적이라 조건이 붙는다.

### 9. ★★ **`asserts` 가 더 위험하다** — 약속이 하나 더 많기 때문이다

**왜 그런가**

| | 술어 `x is T` | 단언 `asserts x is T` |
|---|---|---|
| 무엇을 선언하나 | 「`true` 면 `T` 다」 | 「**정상 반환하면** `T` 다」 |
| 사람이 지킬 약속 | 하나 — 판정이 맞을 것 | ★ **둘** — 판정이 맞을 것 **+ 아니면 던질 것** |
| 좁히는 범위 | `if` **분기 안** | ★ 호출 **뒤 전부** |
| 호출 형태 제약 | 없다 | ★ **명시적 타입 표기 필요**(`TS2775`) |
| 검사되나 | ★ **안 된다**(2번) | ★ **안 된다**(3번 38행) |

- ★★★ **범위가 넓은 만큼 실수의 값도 크다.** 술어가 틀리면 그 `if` 안만 오염되지만,\
  단언이 틀리면 **그 함수의 나머지 전부**가 잘못된 타입으로 돈다.
- ★★ 게다가 「아니면 던진다」는 약속은 **코드를 읽어도 잘 안 보인다.** 3번의 `assertNothing` 이 그 예다 —\
  몸통이 `return;` 하나인데 아무도 막지 않는다.
- ★ 그래서 `asserts` 는 「**여기서 아니면 더 갈 수 없다**」가 정말 참인 자리에만 쓴다. 되돌릴 수 있는 분기에는 술어가 맞다.
- ★ 전면 서술은 목록의 **14번 주제**다.

### 10. ★★ **공개 API 와 「조건이 미묘한 자리」에는 직접 적는다**

**왜 그런가**

| 자리 | 추론에 맡겨도 되나 | 왜 |
|---|---|---|
| `filter((v) => v !== null)` 같은 **한 줄 인라인** | ★ **된다** | 모양이 단순해 조건을 벗어날 일이 적다 |
| 파일 안에서만 쓰는 **작은 도우미** | 된다 | 깨지면 그 파일에서 바로 드러난다 |
| **공개 API·라이브러리 경계** | ★★ **아니다** | 리팩터링 한 줄에 꺼지고, **꺼져도 에러가 안 난다** |
| 몸통에 **검사 아닌 조건이 섞일** 자리 | ★★ 아니다 | 5번 44행처럼 조용히 꺼진다 |
| **`return` 이 여러 개**가 될 자리 | 아니다 | 5번 35행 |

- ★★★ 핵심은 「**꺼져도 에러가 아니다**」라는 점이다. 추론이 안 붙으면 그냥 **안 좁혀질 뿐**이고,\
  그 결과는 호출하는 쪽에서 다른 에러로 나타난다 — 원인을 찾기 어렵다.
- ★★ 5번의 격자에서 **여덟 중 둘만** 붙었다는 사실이 그 위험을 재 준다. **대부분의 모양은 안 붙는다.**
- ★ 그리고 `--strict false` 에서 한 칸이 더 꺼졌다 — **설정에도 달려 있다.**
- ★ 반대로 **추론이 붙은 술어는 거짓말을 못 한다**는 큰 장점이 있다(7번). 둘을 저울질해서 고른다.

### 11. ★★ `unknown` 이 **입구**를 막고, 12 의 수단이 **몸통**을 채운다

**왜 그런가**

| 층 | 무엇 | 어디서 |
|---|---|---|
| **입구** | 외부 값을 `any` 가 아니라 **`unknown`** 으로 받는다 | [**04번 주제**](../04-any-unknown-never-void/) |
| **몸통** | `typeof`·`!==`·`in` 으로 **실제로 확인**한다 | [**12번 주제**](../12-narrowing/) |
| **통로** | 확인 결과를 `v is User` 로 **반환 타입에 싣는다** | 이 주제 |
| **출구** | 호출한 쪽이 좁혀진 타입을 쓴다 | 6번의 `raw.name`·`raw.id` |

- ★★★ 6번의 `isUser` 가 그 넷을 한 함수에 담은 모습이다. **어느 한 층이라도 빠지면 안전이 무너진다** —\
  입구를 `any` 로 열면 몸통이 있어도 아무도 안 부르고, 몸통이 비면 2번처럼 거짓말이 된다.
- ★★ 특히 몸통에서 **`typeof v === "object"` 만으로 끝내지 않은 것**이 중요하다. `null` 과 배열이 그 검사를 통과하기 때문이다(6번 표).
- ★ 좁힌 결과가 교차(`&`)로 쌓이는 것은 [**10번 주제**](../10-intersection-types/)와 [**12번 주제**](../12-narrowing/)의 2절에서 이미 봤다.

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | `x is T` 는 호출한 쪽에서 좁힌다 · 요구 조건은 **`boolean` 반환 하나**(`TS2322`) · ★★★ **몸통은 검사되지 않는다** · `asserts x is T` 는 정상 반환 = 그 타입 · 단언 호출은 **명시적 타입 표기**를 요구한다(`TS2775`) · **추론된 타입 술어**가 조건을 만족하면 붙는다 |
| **설정에 달린 것** | ★ **한 칸**. 5번 격자의 `viaAnd` — `strictNullChecks`(`strict` 에 딸려 7.0 기본 `true`). **양쪽 판을 다 실었다** |
| **이 판(7.0.2)의 관찰** | ★★ **추론 조건의 세부**(단일 `return` · `&&` 의 모든 항 · 매개변수 자신) — 5.5 구현의 경계다. **판이 오르면 넓어질 수 있으니 다시 던져라** · 런타임 예외 문구 `v.toUpperCase is not a function`(`node` v18) · 진단 문구 전문 |

- ★★★ 「**진단 0건」이 답인 블록이 하나**(2번)이고, 「**에러가 안 난 줄**」이 답인 자리가 하나 더 있다(3번 38행).\
  그래서 이 문서는 **소스 전문·방출 전문·실행 출력**을 나란히 실었다 — 셋이 있어야 침묵이 근거가 된다.
- ★ **추론 조건은 외우지 말고 다시 던져라.** 이 문서가 5번의 격자를 파일 하나로 남겨 둔 이유다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 술어 대 인라인 대 감싼 함수 | `--noEmit ex.13a.ts` | exit 1 · **7건** · 36행만 **안 좁혀짐** · 49행 `TS2322` |
| ★ 거짓 술어 | `tsc ex.13b.ts` + `node ex.13b.js` | ★★★ **tsc exit 0 · 진단 0건** · node exit 0 · `shout("hi")` → `문자열이 아니다` · `shout(7)` → **TypeError** |
| `asserts` | `--noEmit ex.13c.ts` | exit 1 · **5건** · 23행 `TS2775` · 24행 `unknown` · **38행 침묵** |
| 추론된 타입 술어 | `--noEmit ex.13d.ts` | exit 1 · **7건** · ★ **5.5 기능이 7.0.2 에서 돈다** · `filter(notNull)` → `number[]` |
| 추론 조건 격자 | `--noEmit ex.13e.ts` | exit 1 · **8건** · 여덟 중 **둘만** 좁힘(47·50행) |
| 〃 `strict` 끔 | `--noEmit --strict false ex.13e.ts` | exit 1 · **50행만** 바뀜 — 좁히지 않는다 |
| `unknown` 관용구 | `tsc ex.13f.ts` + `node ex.13f.js` | tsc exit 0 · node exit 0 · 다섯 입력 중 **정상만 통과** |
| `strict` 대조 | 네 파일을 `--strict false` 로 재실행 | ★ **`ex.13e.ts` 하나만** 갈림 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **추론된 타입 술어가 붙는 조건**(5번의 여덟 모양) — **5.5 구현의 경계**다. 판이 오르면 넓어질 수 있다.\
  이 문서의 격자는 **이 판의 관찰**이지 언어 보장이 아니다.
- ★★ 런타임 예외 문구 `v.toUpperCase is not a function` — `node` v18 의 메시지다.
- `TS2775` 의 문구 전문 — 코드가 더 오래 간다.
- 진단의 들여쓴 줄이 **어느 조각을 대표로** 짚는가 — 보고기의 구현이다.

**안 돌려 본 것**

- **거짓 단언(`asserts`)의 런타임 파괴** — 3번의 38행은 **타입 쪽만** 확인했다. `assertNothing` 을 통과한 값을 실제로 써서 터뜨리는 실험은 **안 했다.**
- **`asserts` 의 전면 서술** — `asserts this is T`·`asserts x`(불리언만) 같은 변형은 **안 던졌다.** 목록의 **14번 주제**.
- **술어와 오버로드의 조합** — 목록의 **16번 주제**. **안 던졌다.**
- **스키마 검증 라이브러리** — 이름도 적지 않았다. **안 던졌다.**
- **술어가 많을 때의 검사 시간** — **재지 않았고 수치를 적지 않았다.**
