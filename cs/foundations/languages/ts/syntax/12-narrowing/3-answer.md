# ts/syntax/12 — 좁히기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★ 이 주제에서는 「**진단 목록에 없는 줄**」이 근거인 자리가 둘이다 — 1번의 16·17·23행과 3번의 36행.\
> **전수 검사는 침묵이 곧 성공**이므로 진단만 세면 아무것도 안 보인다. 그래서 **모든 진단 블록 옆에 소스 전문**을 뒀다.\
> ★★★ 이 주제는 **네 파일 중 셋이 `--strict false` 에서 갈린다.** 그 세 자리는 **양쪽 판을 다 실었다.**\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 탐침 **10개**에 진단 **7건** — 침묵한 것은 **16·17·23행**

**출력**

```ts
// ex.12a.ts
// typeof 로 갈라 놓고 분기마다 무엇이 남는지 탐침으로 찍는다
type Mixed = string | number | boolean | object | null | undefined;

function byTypeof(v: Mixed) {
    if (typeof v === "string") {
        const inString: null = v;
    } else if (typeof v === "number") {
        const inNumber: null = v;
    } else if (typeof v === "boolean") {
        const inBoolean: null = v;
    } else if (typeof v === "object") {
        const inObject: null = v;
    } else if (typeof v === "undefined") {
        const inUndefined: null = v;
    } else {
        const rest: null = v;
        const exhaustive: never = v;
    }
}

function nullTrap(v: string | null) {
    if (typeof v === "object") {
        const caught: null = v;
    }
    if (v !== null) {
        const excluded: null = v;
    }
}

function noNarrow(v: string | number) {
    const t = typeof v;
    if (t === "string") {
        const notNarrowed: null = v;
    }
}
console.log(byTypeof, nullTrap, noNarrow);
```

```text
===== tsc --pretty false --noEmit ex.12a.ts (tsc exit=1) =====
ex.12a.ts(6,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12a.ts(8,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.12a.ts(10,15): error TS2322: Type 'boolean' is not assignable to type 'null'.
ex.12a.ts(12,15): error TS2322: Type 'object | null' is not assignable to type 'null'.
  Type 'object' is not assignable to type 'null'.
ex.12a.ts(14,15): error TS2322: Type 'undefined' is not assignable to type 'null'.
ex.12a.ts(26,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12a.ts(33,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 분기 | 남은 타입 |
|---|---|---|
| 6 | `typeof v === "string"` | `string` |
| 8 | `typeof v === "number"` | `number` |
| 10 | `typeof v === "boolean"` | `boolean` |
| 12 | `typeof v === "object"` | ★★★ **`object \| null`** |
| 14 | `typeof v === "undefined"` | `undefined` |
| 16 | 마지막 `else` | ★★ **침묵** → `never` |
| 17 | `const exhaustive: never = v` | ★★ **침묵** → **전수 검사 성공** |
| 23 | `string \| null` 에 `typeof v === "object"` | ★★★ **침묵** → **`null`** |
| 26 | `v !== null` | `string` |
| 33 | `const t = typeof v; if (t === "string")` | ★★ **`string \| number`** — 안 좁혀졌다 |

- ★★★ 12행이 이 주제의 대표 함정이다. **`typeof null` 이 `"object"`** 라서 `null` 이 객체 갈래에 섞인다.\
  6절의 실행 출력이 그것을 런타임에서 확인한다 — `typeof null: object`.
- ★★★ 23행이 그 함정을 **극단으로** 보여 준다. `v: string | null` 에서 `typeof v === "object"` 로 걸러낸 것이\
  **오직 `null` 하나**다. 탐침이 `null` 이라 **통과해 버린다** — 「에러가 없으니 객체겠지」가 여기서 무너진다.
- ★★ 16·17행의 침묵이 **성공의 모양**이다. 09 에서는 갈래를 하나 빼서 `'Tri'` 라는 이름이 **진단에 찍혔다.**\
  다 처리하면 반대로 **아무 말도 안 한다.**
- ★★ 33행 — **`typeof` 의 결과를 변수에 담으면 연결이 끊긴다.** 3번의 50행과 대조하라(그쪽은 좁혀진다).

### 2. ★★★ 진단 **11건** — 진릿값의 **거짓 갈래는 하나도 안 줄어든다**

**출력**

```ts
// ex.12b.ts
// typeof 말고 나머지 넷 — instanceof · in · 진릿값 · 동등성
class Dog {
    bark(): void {}
}
class Cat {
    meow(): void {}
}
function byInstance(p: Dog | Cat) {
    if (p instanceof Dog) {
        const inDog: null = p;
    } else {
        const inCat: null = p;
    }
}

interface Bird {
    fly(): void;
}
interface Fish {
    swim(): void;
}
function byIn(p: Bird | Fish) {
    if ("fly" in p) {
        const inBird: null = p;
    } else {
        const inFish: null = p;
    }
}

function byTruth(v: string | number | null | undefined) {
    if (v) {
        const truthy: null = v;
    } else {
        const falsy: null = v;
    }
}

function byEquality(a: string | number, b: string | boolean) {
    if (a === b) {
        const inA: null = a;
        const inB: null = b;
    }
}

function byLiteral(v: "up" | "down" | 1) {
    if (v === "up") {
        const up: null = v;
    } else {
        const rest: null = v;
    }
}

function unknownIn(u: unknown) {
    if (typeof u === "object" && u !== null && "x" in u) {
        const shaped: null = u;
    }
}
console.log(byInstance, byIn, byTruth, byEquality, byLiteral, unknownIn);
```

```text
===== tsc --pretty false --noEmit ex.12b.ts (tsc exit=1) =====
ex.12b.ts(10,15): error TS2322: Type 'Dog' is not assignable to type 'null'.
ex.12b.ts(12,15): error TS2322: Type 'Cat' is not assignable to type 'null'.
ex.12b.ts(24,15): error TS2322: Type 'Bird' is not assignable to type 'null'.
ex.12b.ts(26,15): error TS2322: Type 'Fish' is not assignable to type 'null'.
ex.12b.ts(32,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12b.ts(34,15): error TS2322: Type 'string | number | null | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.12b.ts(40,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12b.ts(41,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12b.ts(47,15): error TS2322: Type '"up"' is not assignable to type 'null'.
ex.12b.ts(49,15): error TS2322: Type '"down" | 1' is not assignable to type 'null'.
  Type '"down"' is not assignable to type 'null'.
ex.12b.ts(55,15): error TS2322: Type 'object & Record<"x", unknown>' is not assignable to type 'null'.
```

**왜 그런가**

| 수단 | 참 갈래 | 거짓 갈래 |
|---|---|---|
| `p instanceof Dog` | `Dog` | `Cat` |
| `"fly" in p` | `Bird` | `Fish` |
| ★★★ `if (v)` (`string \| number \| null \| undefined`) | **`string \| number`** | ★★★ **`string \| number \| null \| undefined`** — **그대로** |
| `a === b` (`string \| number` 대 `string \| boolean`) | ★ **둘 다 `string`** | — |
| `v === "up"` (`"up" \| "down" \| 1`) | `"up"` | `"down" \| 1` |
| `typeof u === "object" && u !== null && "x" in u` | ★★ **`object & Record<"x", unknown>`** | — |

- ★★★ **덜 좁혀지는 쪽은 거짓 갈래**다. `if (v)` 의 `else` 에서 `null`·`undefined` 조차 안 빠진다.\
  이유는 `""` 와 `0` 도 거짓이기 때문이다 — 타입 시스템에 「빈 문자열이 아닌 `string`」을 적을 수 없으니 **`string` 이 그대로 남을 수밖에 없다.**
- ★★ 그래서 **「값이 없다」를 물을 때 `if (v)` 를 쓰면 안 된다.** `if (v == null)` 이나 `if (v === undefined)` 를 써야 거짓 갈래가 쓸모 있어진다.
- ★ `a === b` 가 **양쪽을 동시에** 좁히는 것에 주의하라. 두 유니온의 공통이 `string` 하나이기 때문이다.
- ★★★ 55행의 `&` 는 [**10번 주제**](../10-intersection-types/)에서 온다. 검사 세 개를 `&&` 로 이으면\
  각 검사의 결과가 **교차로 합쳐진다** — `object`(typeof) `&` `Record<"x", unknown>`(`in`). **좁히기가 교차를 만드는 자리**다.
- ★ `in` 을 쓴 이유는 **인터페이스에 `instanceof` 를 못 쓰기** 때문이다. 6절이 그 이유를 보여 준다 — `interface` 는 방출에 안 남는다.

### 3. ★★★ 탐침 **8개**에 진단 **7건** — `const` 는 좁히고 `let` 은 안 좁힌다

**출력**

```ts
// ex.12c.ts
// 조건을 변수에 담아도 좁혀지나 — const 와 let 이 갈린다
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number }
    | { kind: "tri"; base: number; h: number };

function byConstAlias(v: string | number) {
    const isStr = typeof v === "string";
    if (isStr) {
        const narrowed: null = v;
    }
}

function byLetAlias(v: string | number) {
    let isStr = typeof v === "string";
    if (isStr) {
        const notNarrowed: null = v;
    }
}

function bySwitch(s: Shape) {
    switch (s.kind) {
        case "circle": {
            const inCircle: null = s;
            return;
        }
        case "square": {
            const inSquare: null = s;
            return;
        }
        case "tri": {
            const inTri: null = s;
            return;
        }
        default: {
            const exhaustive: never = s;
            return exhaustive;
        }
    }
}

function afterEarlyReturn(s: Shape) {
    if (s.kind === "circle") return;
    const rest: null = s;
}

function byDiscriminantAlias(s: Shape) {
    const k = s.kind;
    if (k === "circle") {
        const viaAlias: null = s;
    }
}
console.log(byConstAlias, byLetAlias, bySwitch, afterEarlyReturn, byDiscriminantAlias);
```

```text
===== tsc --pretty false --noEmit ex.12c.ts (tsc exit=1) =====
ex.12c.ts(10,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12c.ts(17,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12c.ts(24,19): error TS2322: Type '{ kind: "circle"; r: number; }' is not assignable to type 'null'.
ex.12c.ts(28,19): error TS2322: Type '{ kind: "square"; side: number; }' is not assignable to type 'null'.
ex.12c.ts(32,19): error TS2322: Type '{ kind: "tri"; base: number; h: number; }' is not assignable to type 'null'.
ex.12c.ts(44,11): error TS2322: Type '{ kind: "square"; side: number; } | { kind: "tri"; base: number; h: number; }' is not assignable to type 'null'.
  Type '{ kind: "square"; side: number; }' is not assignable to type 'null'.
ex.12c.ts(50,15): error TS2322: Type '{ kind: "circle"; r: number; }' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 모양 | 좁혀졌나 |
|---|---|---|
| 10 | `const isStr = typeof v === "string"; if (isStr)` | ★★★ **좁힌다** — `string` |
| 17 | `let isStr = typeof v === "string"; if (isStr)` | ★★★ **안 좁힌다** — `string \| number` |
| 24·28·32 | `switch (s.kind)` 세 갈래 | 각각 한 멤버로 |
| 36 | `default` 의 `const exhaustive: never = s` | ★★ **침묵** — **전수 검사 성공** |
| 44 | 이른 `return` 뒤 | `{ kind: "square" … } \| { kind: "tri" … }` |
| 50 | `const k = s.kind; if (k === "circle")` | ★★★ **좁힌다** — `{ kind: "circle"; r: number; }` |

- ★★★ **10행과 17행의 차이는 선언 키워드 하나**다. `let` 은 재대입될 수 있으니 `if (isStr)` 시점에 그 조건이 아직 참인지\
  컴파일러가 보장 못 한다. `const` 는 그 값이 그대로라 **검사 자체를 기억해 둘 수 있다**(TS 4.4 별칭 조건).
- ★★ **같은 `const`/`let` 갈림이 [**11번 주제**](../11-literal-types-and-as-const/)의 넓히기에도 있었다.** 뿌리가 같다 — **재대입 가능성**이다.
- ★★★ 50행과 1번의 33행이 **다르다.** 둘 다 `const` 에 담았는데 —

| 담은 것 | 결과 | 왜 |
|---|---|---|
| `const k = s.kind`(**판별 프로퍼티**) | ★ **좁힌다** | 판별 칸의 값을 담은 것으로 인정된다 |
| `const t = typeof v`(**`typeof` 의 결과**) | ★ **안 좁힌다** | 「검사」가 아니라 「검사의 재료」다 |
| `const ok = typeof v === "string"`(**검사 결과**) | ★ **좁힌다** | 별칭 조건 |

- ★★ 36행의 침묵이 09 와 뒤집힌 모양이다. 09 에서는 갈래를 빼서 **`'Tri'` 라는 이름이 진단에** 찍혔다.\
  여기서는 다 적었으니 **아무 말도 안 한다.** 전수 검사는 **침묵이 성공**이다.

### 4. ★★★ 진단 **9건** — **클로저 안에서만 풀린다**

**출력**

```ts
// ex.12d.ts
// 좁히기가 어디서 풀리나 — 함수 호출 뒤·클로저 안·재대입 뒤를 각각 던진다
interface Box {
    v?: string;
}
declare function touch(): void;

function afterCall(b: Box) {
    if (b.v) {
        touch();
        const stillNarrow: null = b.v;
    }
}

function insideClosure(b: Box) {
    if (b.v) {
        const cb = () => {
            const inClosure: null = b.v;
        };
        cb();
    }
}

function fixedByLocal(b: Box) {
    const v = b.v;
    if (v) {
        const cb = () => {
            const inClosure: null = v;
        };
        cb();
    }
}

function afterReassign(v: string | number) {
    if (typeof v === "string") {
        const before: null = v;
        v = 1;
        const after: null = v;
    }
}

let outer: string | number = "s";
function overLet() {
    if (typeof outer === "string") {
        const here: null = outer;
        const cb = () => {
            const inClosure: null = outer;
        };
        cb();
    }
}

function byIndex(xs: (string | number)[], i: number) {
    if (typeof xs[i] === "string") {
        const elem: null = xs[i];
    }
}

function byGetter(o: { get v(): string | number }) {
    if (typeof o.v === "string") {
        const got: null = o.v;
    }
}
console.log(afterCall, insideClosure, fixedByLocal, afterReassign, overLet, byIndex, byGetter);
```

```text
===== tsc --pretty false --noEmit ex.12d.ts (tsc exit=1) =====
ex.12d.ts(10,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(17,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.12d.ts(27,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(35,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(37,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.12d.ts(44,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(46,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12d.ts(54,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(60,15): error TS2322: Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 타입 | 좁힘이 |
|---|---|---|---|
| 10 | `touch()` **호출 뒤**의 `b.v` | **`string`** | ★★★ **살아 있다** |
| 17 | **클로저 안**의 `b.v` | **`string \| undefined`** | ★★★ **풀렸다** |
| 27 | `const v = b.v` 로 담은 뒤 **클로저 안** | **`string`** | ★★ **살아 있다** — 이것이 고치는 법 |
| 35 | 재대입 전 | `string` | 살아 있다 |
| 37 | `v = 1` 재대입 뒤 | `number` | 당연히 바뀐다 |
| 44 | 모듈 `let outer` 를 **그 자리에서** | `string` | 살아 있다 |
| 46 | 모듈 `let outer` 를 **클로저 안에서** | **`string \| number`** | ★★ **풀렸다** |
| 54 | `typeof xs[i] === "string"` 뒤의 `xs[i]` | **`string`** | ★ **살아 있다** |
| 60 | 게터 `o.v` | **`string`** | ★ **살아 있다** |

- ★★★ **「함수를 부르면 좁히기가 풀린다」는 이 판에서 틀렸다.** 10행이 `string` 이다.\
  풀리는 것은 **클로저 안**이고, 이유는 8번에 있다.
- ★★ 고치는 법은 **하나뿐**이다 — 27행처럼 **`const` 지역 변수에 담아 두는 것.** 담은 값은 아무도 못 바꾸므로 좁힘이 따라간다.
- ★★★ 10·54·60행이 **안전선을 낮춘 자리**다. `touch()` 가 `b.v` 를 지울 수도, 다른 코드가 `xs[i]` 를 바꿀 수도,\
  게터가 부를 때마다 다른 값을 줄 수도 있는데 **컴파일러가 믿어 준다.** 「보장」이 아니라 「**믿어 준다**」로 읽어야 한다.
- ★ 44행과 46행의 짝이 **위치가 아니라 문맥**이 기준임을 보여 준다. 같은 변수인데 클로저 경계를 넘자마자 풀린다.

### 5. ★★★ **네 파일 중 셋**이 갈린다

**출력**

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.12a.ts    exit 1 / exit 1 · ★ 다르다
ex.12b.ts    exit 1 / exit 1 · ★ 다르다
ex.12c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.12d.ts    exit 1 / exit 1 · ★ 다르다
```

```text
===== tsc --pretty false --noEmit --strict false ex.12a.ts (tsc exit=1) =====
ex.12a.ts(6,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12a.ts(8,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.12a.ts(10,15): error TS2322: Type 'boolean' is not assignable to type 'null'.
ex.12a.ts(12,15): error TS2322: Type 'object' is not assignable to type 'null'.
ex.12a.ts(26,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12a.ts(33,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

```text
===== tsc --pretty false --noEmit --strict false ex.12b.ts (tsc exit=1) =====
ex.12b.ts(10,15): error TS2322: Type 'Dog' is not assignable to type 'null'.
ex.12b.ts(12,15): error TS2322: Type 'Cat' is not assignable to type 'null'.
ex.12b.ts(24,15): error TS2322: Type 'Bird' is not assignable to type 'null'.
ex.12b.ts(26,15): error TS2322: Type 'Fish' is not assignable to type 'null'.
ex.12b.ts(32,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12b.ts(34,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12b.ts(40,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12b.ts(41,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12b.ts(47,15): error TS2322: Type '"up"' is not assignable to type 'null'.
ex.12b.ts(49,15): error TS2322: Type '"down" | 1' is not assignable to type 'null'.
  Type '"down"' is not assignable to type 'null'.
ex.12b.ts(55,15): error TS2322: Type 'object & Record<"x", unknown>' is not assignable to type 'null'.
```

```text
===== tsc --pretty false --noEmit --strict false ex.12d.ts (tsc exit=1) =====
ex.12d.ts(10,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(17,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(27,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(35,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(37,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.12d.ts(44,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(46,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.12d.ts(54,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.12d.ts(60,15): error TS2322: Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 파일 | 갈린 줄 | 기본값(`strict`) | `--strict false` |
|---|---|---|---|
| `ex.12a.ts` | 12 | **`object \| null`** | ★ **`object`** — 함정이 사라진다 |
| 〃 | 14 | `undefined` | ★★★ **진단 자체가 없다** — `never` 로 좁혀졌다 |
| `ex.12b.ts` | 34 | `string \| number \| null \| undefined` | **`string \| number`** |
| `ex.12c.ts` | — | — | ★ **한 글자도 같다** |
| `ex.12d.ts` | 17 | `string \| undefined` | **`string`** |

- ★★★ **끄면 `null`·`undefined` 가 다른 타입에 흡수된다**([**04번 주제**](../04-any-unknown-never-void/)). 그래서 —\
  ① `typeof v === "object"` 의 함정이 **안 보이고** ② `undefined` 갈래가 **`never` 가 되어 탐침이 침묵하고**\
  ③ 클로저에서 잃을 `undefined` 자체가 **없어진다**.
- ★★ ③이 특히 위험하다. **4절의 사고가 사라진 것이 아니라 안 보이게 된 것**이다. 런타임에는 그대로 `undefined` 가 온다.
- ★ `ex.12c.ts` 만 같다 — 그 파일의 주제(별칭 조건·판별 유니온·전수 검사)는 `null` 과 무관하기 때문이다.
- ★★ 이것이 [**10번**](../10-intersection-types/)·[**11번 주제**](../11-literal-types-and-as-const/)와 갈리는 지점이다. 그 둘은 **설정에 달린 칸이 0개**였다.

### 6. ★★★ 남는 것은 **JS 연산자뿐**이고 `typeof null` 은 `object` 다

**출력**

```ts
// ex.12e.ts
// 좁히기는 방출에 한 글자도 안 남는다 — 남는 것은 JS 연산자뿐이다
type Shape = { kind: "circle"; r: number } | { kind: "square"; side: number };

class Dog {
    bark(): string {
        return "왈";
    }
}
class Cat {
    meow(): string {
        return "야옹";
    }
}

function describe(v: string | number | null): string {
    if (typeof v === "string") return `문자열 ${v.length}자`;
    if (typeof v === "number") return `숫자 ${v.toFixed(1)}`;
    return "null";
}

function area(s: Shape): number {
    if (s.kind === "circle") return 3 * s.r * s.r;
    return s.side * s.side;
}

function speak(p: Dog | Cat): string {
    if (p instanceof Dog) return p.bark();
    return p.meow();
}

console.log("describe  :", describe("abc"), "/", describe(4), "/", describe(null));
console.log("area      :", area({ kind: "circle", r: 2 }), "/", area({ kind: "square", side: 3 }));
console.log("speak     :", speak(new Dog()), "/", speak(new Cat()));
console.log("typeof null:", typeof null);
```

```text
===== tsc --pretty false ex.12e.ts (tsc exit=0) =====
===== 방출된 ex.12e.js =====
"use strict";
class Dog {
    bark() {
        return "왈";
    }
}
class Cat {
    meow() {
        return "야옹";
    }
}
function describe(v) {
    if (typeof v === "string")
        return `문자열 ${v.length}자`;
    if (typeof v === "number")
        return `숫자 ${v.toFixed(1)}`;
    return "null";
}
function area(s) {
    if (s.kind === "circle")
        return 3 * s.r * s.r;
    return s.side * s.side;
}
function speak(p) {
    if (p instanceof Dog)
        return p.bark();
    return p.meow();
}
console.log("describe  :", describe("abc"), "/", describe(4), "/", describe(null));
console.log("area      :", area({ kind: "circle", r: 2 }), "/", area({ kind: "square", side: 3 }));
console.log("speak     :", speak(new Dog()), "/", speak(new Cat()));
console.log("typeof null:", typeof null);
```

```text
===== node ex.12e.js (node exit=0) =====
describe  : 문자열 3자 / 숫자 4.0 / null
area      : 12 / 9
speak     : 왈 / 야옹
typeof null: object
```

**왜 그런가**

| 확인 | 값 |
|---|---|
| `type Shape` 선언 | 방출에 **없다** |
| `class Dog`·`class Cat` | **남는다** — 값이기 때문이다 |
| 좁히기를 하는 코드 | `typeof v === "string"` · `s.kind === "circle"` · `p instanceof Dog` — ★★★ **전부 JS 연산자** |
| `describe("abc")` · `describe(4)` · `describe(null)` | `문자열 3자` · `숫자 4.0` · `null` |
| `area(circle)` · `area(square)` | `12` · `9` |
| `speak(new Dog())` · `speak(new Cat())` | `왈` · `야옹` |
| `typeof null` | ★★★ **`object`** |

- ★★★ **좁히기를 가능하게 한 코드가 곧 런타임에 도는 코드**다. 타입은 그것을 **읽고 따라간** 것뿐이다.
- ★★ 그래서 `interface` 는 `instanceof` 로 못 가른다 — **방출에 한 글자도 안 남기** 때문이다([**01번 주제**](../01-what-ts-adds-and-erases/)).\
  `class` 는 남으므로 `instanceof` 가 된다. **좁히기 수단의 선택은 「런타임에 무엇이 남나」가 정한다.**
- ★★ 마지막 줄이 1번 12·23행의 함정을 **런타임에서** 확인한다. 타입 쪽의 `object | null` 은 **JS 의 이 버그를 그대로 옮긴 것**이다.
- ★ 좁히기는 방출을 **한 글자도 안 늘린다** — 좁히려고 적은 `if` 는 어차피 필요한 코드다.

### 7. ★★★ **같은 변수라도 「이 줄에 오기까지의 경로」가 다르기** 때문이다

**왜 그런가**

- 타입 주석은 「이 변수가 **가질 수 있는 값 전체**」를 적는다. 좁히기는 「**이 줄에 도달했다면** 그중 어디까지 가능한가」를 계산한다.
- `if (typeof v === "string")` 안에 도달했다는 것은 **그 검사가 참이었다는 뜻**이다. 그 사실을 쓰지 않을 이유가 없다.
- ★★ 그래서 좁히기는 **위치가 아니라 경로**를 따른다 — 같은 줄이라도 다른 분기에서 왔으면 다른 타입이다.
- ★ 4번의 44행과 46행이 그 예다. 소스에서 두 줄 차이인데 **클로저 경계를 넘자 경로 정보가 끊긴다.**
- ★★ 모순이 아닌 이유 — **선언된 타입은 한 번도 바뀌지 않는다.** 바뀌는 것은 「이 자리에서 컴파일러가 아는 것」이다.

### 8. ★★★ **클로저는 언제 실행될지 모르기** 때문이다

**왜 그런가**

- 직선 코드는 순서가 정해져 있다. `if` 다음 줄은 **그 검사 직후**에 실행된다.
- 클로저는 **나중에** 실행될 수 있다 — 콜백으로 넘겨지거나, 이벤트에 붙거나, 한참 뒤에 불린다.\
  그 사이에 `b.v` 가 지워졌을 수 있으므로 컴파일러는 **좁힘을 못 믿는다.**
- ★★ 27행이 통하는 이유가 여기 있다. `const v = b.v` 로 **값을 복사해 두면** 그 지역 변수는 아무도 못 바꾼다.\
  좁힌 것이 「객체의 칸」이 아니라 「**내 변수**」가 되므로 클로저 안에서도 유효하다.
- ★★★ 뒤집으면 **10행이 왜 안 풀리는지**가 설명되지 않는다 — `touch()` 도 `b.v` 를 지울 수 있기 때문이다.\
  그래서 10행은 **원칙이 아니라 실용적 타협**이다. 9번이 그 자리를 짚는다.

### 9. ★★★ **10·54·60행 전부**가 그렇다 — 셋 다 「믿어 주는」 자리다

**왜 그런가**

| 줄 | 무엇이 깨질 수 있나 |
|---|---|
| 10 `touch()` 뒤의 `b.v` | `touch()` 가 같은 객체의 `v` 를 **지울 수 있다** |
| 54 `xs[i]` | 검사와 사용 사이에 **배열이 바뀔 수 있다** |
| 60 게터 `o.v` | 게터는 **부를 때마다 다른 값**을 줄 수 있다 |

- ★★★ 셋 다 **컴파일러가 좁힘을 유지해 준다.** 안전해서가 아니라 **그러지 않으면 실무 코드가 에러투성이**가 되기 때문이다.
- ★★ 그래서 이 세 자리는 「**언어 보장**」이 아니라 「**이 판의 설계 선택**」으로 읽어야 한다.
- ★★ 실제로 깨뜨리려면 `touch()` 가 `b.v = undefined` 를 하면 된다. 그때 `b.v.length` 가 런타임에 터진다 —\
  **이 배치에서는 그 시나리오를 실행해 보지 않았다.** 여기서는 **타입 쪽 답만** 확인했다.
- ★ 반대로 **클로저는 풀어 준다**(17·46행). 같은 위험인데 한쪽만 막는 것이 **타협의 증거**다.

### 10. ★★ 둘 — **객체끼리**와 **`null`**

**왜 그런가**

| `typeof` 가 못 가르는 것 | 왜 | 대신 쓰는 것 |
|---|---|---|
| **객체끼리**(클래스·인터페이스·배열·`null`) | 전부 **`"object"`** 다 | `instanceof`(클래스) · `in`(프로퍼티) · `Array.isArray`(배열) · 판별 칸 |
| **`null`** | ★★★ `typeof null === "object"` | `v === null` · `v == null` · `v !== null` |

- ★★★ 1번의 12행이 그 둘을 한 줄에 보여 준다 — `typeof v === "object"` 분기가 **`object | null`** 이다.
- ★★ **인터페이스에는 `instanceof` 를 못 쓴다**(방출에 안 남으므로). 그래서 `in` 이나 **판별 칸**이 필요하다.
- ★ `typeof` 가 잘 가르는 것은 **원시 타입 여섯**(`string`·`number`·`bigint`·`boolean`·`symbol`·`undefined`)과 **`function`** 이다.\
  이 문서는 그중 넷을 던졌다 — `bigint`·`symbol`·`function` 은 **안 던졌다.**
- ★ 더 복잡한 모양을 가르려면 **술어 함수**로 포장한다([**13번 주제**](../13-type-guards-and-predicates/)).

### 11. ★★ **판별 칸을 읽는 일**과 **교차를 만드는 일**로 만난다

**왜 그런가**

| 어디서 | 무엇 | 이 문서의 자리 |
|---|---|---|
| [**09번**](../09-union-types/) → 12 | 판별 유니온의 `switch` 와 `never` 전수 검사 | 3번의 24·28·32·36행 |
| [**10번**](../10-intersection-types/) → 12 | `(A \| B) & C` 가 분배되고, 좁히면 **`A & C`** 가 나온다 | 10번 주제의 5절 30·32행 |
| 12 → [**10번**](../10-intersection-types/) | 검사를 `&&` 로 이으면 결과가 **교차**로 합쳐진다 | 2번의 55행 `object & Record<"x", unknown>` |

- ★★★ 세 주제가 **같은 기계의 세 면**이다. 유니온은 갈래를 만들고, 좁히기는 갈래를 고르고, 교차는 **고른 결과를 합친다.**
- ★★ 그래서 2번의 55행을 읽을 때 **`&` 가 왜 나오는지 놀라지 않아야 한다** — 검사 하나가 조각 하나를 더한 것이다.
- ★ 판별 칸이 **리터럴 타입**이어야 하는 이유는 [**11번 주제**](../11-literal-types-and-as-const/)다. `kind: string` 이면 `===` 로 못 가른다.

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | `typeof`·`instanceof`·`in`·진릿값·`===` 가 분기 안에서 타입을 줄인다 · `typeof null === "object"` 라서 그 분기에 `null` 이 섞인다 · 진릿값의 **거짓 갈래는 거의 안 줄어든다** · **`const` 별칭 조건**(4.4) · `never` 대입 **전수 검사** · 좁히기는 **방출에 JS 연산자로** 남는다 |
| **설정에 달린 것** | ★★★ **네 파일 중 셋**. `null`·`undefined` 가 분기에 남는가 — `strictNullChecks`(`strict` 에 딸려 7.0 기본 `true`). **양쪽 판을 다 실었다**(5번) |
| **이 판(7.0.2)의 관찰** | ★★ **함수 호출 뒤에 프로퍼티 좁힘이 살아남는 것** · **인덱스 접근과 게터가 좁혀지는 것** — 셋 다 「믿어 준다」이지 「안전하다」가 아니다 · 좁혀진 유니온의 **멤버 순서** · 진단 문구 전문 |

- ★★★ 「**에러가 안 난 줄」이 근거인 자리가 둘**이다 — 1번의 16·17·23행, 3번의 36행. **전수 검사는 침묵이 성공**이다.
- ★ **멤버 순서는 대조 기준으로 쓰지 않는다.** 「같은 집합으로 줄어든다」는 성질만 읽는다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| `typeof` 사다리 | `--noEmit ex.12a.ts` | exit 1 · 탐침 10개에 **7건** · 12행 `object \| null` · 16·17·23행 **침묵** |
| 〃 `strict` 끔 | `--noEmit --strict false ex.12a.ts` | exit 1 · **12행이 `object`** · **14행 진단 사라짐** · 나머지 동일 |
| 나머지 네 수단 | `--noEmit ex.12b.ts` | exit 1 · **11건** · 거짓 갈래가 **안 줄어듦** · 55행 `object & Record<"x", unknown>` |
| 〃 `strict` 끔 | `--noEmit --strict false ex.12b.ts` | exit 1 · **34행만** `string \| number` 로 바뀜 |
| 별칭 조건·전수 검사 | `--noEmit ex.12c.ts` | exit 1 · 탐침 8개에 **7건** · 36행 **침묵**(성공) · `const`/`let` 갈림 |
| 〃 `strict` 끔 | `--noEmit --strict false ex.12c.ts` | exit 1 · ★ **한 글자도 같다** |
| 풀리는 자리 | `--noEmit ex.12d.ts` | exit 1 · **9건** · 클로저만 풀림 · 함수 호출·인덱스·게터는 살아남음 |
| 〃 `strict` 끔 | `--noEmit --strict false ex.12d.ts` | exit 1 · **17행이 `string`** — 잃을 `undefined` 가 없다 |
| 방출·실행 | `tsc ex.12e.ts` + `node ex.12e.js` | tsc exit 0 · node exit 0 · `typeof null: object` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ **함수 호출 뒤에 프로퍼티 좁힘이 살아남는 것**(4번 10행) — 실용적 타협이다. **안전 보장으로 읽지 않는다.**
- ★★ **인덱스 접근(`xs[i]`)과 게터가 좁혀지는 것**(4번 54·60행) — 같은 성질이다.
- 좁혀진 유니온을 진단이 찍을 때의 **멤버 순서** — 09 의 정렬과 같다.
- 진단 문구 전문 — 코드(`TS2322`)가 더 오래 간다.

**안 돌려 본 것**

- **좁힘이 실제로 깨지는 시나리오** — `touch()` 가 `b.v` 를 지우게 해서 런타임에 터뜨리는 실험은 **안 했다**(9번). 타입 쪽 답만 확인했다.
- **`typeof` 의 나머지 결과** — `bigint`·`symbol`·`function` 은 **안 던졌다.**
- **`Array.isArray`** — 수단 목록에 **형태만** 적었고 던지지 않았다. 술어 함수 자체는 [**13번 주제**](../13-type-guards-and-predicates/)에서 던진다.
- **`asserts` 단언 시그니처** — [목록의 **14번 주제**](../14-assertion-signatures/). 이 문서에서는 **안 던졌다.**
- **분기가 많을 때의 검사 시간** — **재지 않았고 수치를 적지 않았다.** 목록의 **45번 주제**에서 잰다.
