# ts/syntax/15 — 제어 흐름 분석의 한계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 4번은 **진단이 한 줄도 없는 것이 답**이다. 그런 블록을 근거로 쓰려면 **소스 전문 + 방출 전문 + 실행 출력** 셋이 다 있어야 한다 — 그렇게 실었다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **11건** — 풀린 것은 **넷**이고, 즉시 실행 함수는 **안 풀린다**

**출력**

```ts
// ex.15a.ts
// 좁힘이 풀리는 자리와 안 풀리는 자리 — 1부: 경계를 넘는 여덟 모양
interface Box {
    v?: string;
}
declare function touch(): void;
declare function takeCb(f: () => void): void;

function afterCall(b: Box) {
    if (b.v) {
        touch();
        const a1: null = b.v;
    }
}
async function afterAwait(b: Box) {
    if (b.v) {
        await Promise.resolve();
        const a2: null = b.v;
    }
}
function inCallback(b: Box) {
    if (b.v) {
        takeCb(() => {
            const a3: null = b.v;
        });
    }
}
function inNestedDecl(b: Box) {
    if (b.v) {
        function inner() {
            const a4: null = b.v;
        }
        inner();
    }
}
function inIIFE(b: Box) {
    if (b.v) {
        (() => {
            const a5: null = b.v;
        })();
    }
}
function afterReassign(v: string | number) {
    if (typeof v === "string") {
        const a6: null = v;
        v = 1;
        const a7: null = v;
    }
}
function byLocalConst(b: Box) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const a8: null = v;
        });
    }
}
let mutable: string | number = "s";
function overModuleLet() {
    if (typeof mutable === "string") {
        const a9: null = mutable;
        takeCb(() => {
            const a10: null = mutable;
        });
    }
}
const frozen: string | number = "s";
function overModuleConst() {
    if (typeof frozen === "string") {
        takeCb(() => {
            const a11: null = frozen;
        });
    }
}
console.log(afterCall, afterAwait, inCallback, inNestedDecl, inIIFE, afterReassign, byLocalConst, overModuleLet, overModuleConst);
```

```text
===== tsc --pretty false --noEmit ex.15a.ts (tsc exit=1) =====
ex.15a.ts(11,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(17,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(23,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15a.ts(30,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15a.ts(38,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(44,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(46,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15a.ts(53,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(60,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(62,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15a.ts(70,19): error TS2322: Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 11 | 함수 호출 뒤 | `string` — **유지** |
| 17 | ★ `await` 뒤 | `string` — **유지** |
| 23 | ★★★ 콜백 안의 프로퍼티 | **`string \| undefined`** — 풀림 |
| 30 | 중첩 함수 선언 안 | **`string \| undefined`** — 풀림 |
| 38 | ★★★ 즉시 실행 함수 안 | `string` — **유지** |
| 44 / 46 | 재대입 전 / 후 | `string` / **`number`** |
| 53 | 지역 `const` 를 콜백에서 | `string` — **유지** ★ 고치는 법 |
| 60 / 62 | 모듈 `let` — 그 자리 / 콜백 안 | `string` / **`string \| number`** — 풀림 |
| 70 | 모듈 `const` 를 콜백에서 | `string` — **유지** |

- ★★★ 23행과 38행의 차이가 이 절의 핵심이다. 둘 다 **함수 안**인데 결과가 반대다.\
  즉시 실행 함수는 「**지금 당장 부른다**」가 문법에 보이므로 컴파일러가 흐름을 이어 준다.\
  콜백은 **언제 불릴지 모른다** — 그 사이 프로퍼티가 바뀔 수 있으니 통째로 버린다.
- ★★★ 62행과 70행은 `let` 과 `const` 하나만 다르다. `let` 은 **다시 대입될 수 있어서** 풀리고,\
  `const` 는 **못 바뀌니** 살아남는다. 다만 진짜 기준은 `const` 가 아니라 **대입의 유무**다(3번).
- ★★ 17행이 놀라운 자리다. `await` 사이에 다른 코드가 얼마든지 돌 수 있는데도 **안 풀린다** —\
  4번이 그것을 깨뜨린다.
- ★ 46행은 「풀렸다」가 아니라 「**갱신됐다**」다. `v = 1;` 이 `v` 를 `number` 로 다시 좁힌다.

### 2. ★★★ 진단 **15건** — 좁혀지지 않은 것은 **24·52·68행** 셋

**출력**

```ts
// ex.15b.ts
// 2부: 무엇을 좁혔나 — 인덱스·게터·메서드 호출·판별 유니온·this·구조 분해·readonly
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number };
declare function takeCb(f: () => void): void;

function byIndexParam(xs: (string | number)[], i: number) {
    if (typeof xs[i] === "string") {
        const b1: null = xs[i];
    }
}
function byIndexLiteral(xs: (string | number)[]) {
    if (typeof xs[0] === "string") {
        const b2: null = xs[0];
    }
}
function byGetter(o: { get v(): string | number }) {
    if (typeof o.v === "string") {
        const b3: null = o.v;
    }
}
function byMethodCall(o: { v(): string | number }) {
    if (typeof o.v() === "string") {
        const b4: null = o.v();
    }
}
function duAfterCall(s: Shape, f: () => void) {
    if (s.kind === "circle") {
        f();
        const b5: null = s.r;
    }
}
function duInCallback(s: Shape) {
    if (s.kind === "circle") {
        takeCb(() => {
            const b6: null = s.r;
        });
    }
}
class Holder {
    v: string | number = "s";
    afterCall(f: () => void) {
        if (typeof this.v === "string") {
            const b7: null = this.v;
            f();
            const b8: null = this.v;
        }
    }
    inCallback() {
        if (typeof this.v === "string") {
            takeCb(() => {
                const b9: null = this.v;
            });
        }
    }
}
function byDestructure(b: { v?: string }) {
    const { v } = b;
    if (v) {
        takeCb(() => {
            const b10: null = v;
        });
    }
}
function byReadonlyProp(o: { readonly v: string | number }) {
    if (typeof o.v === "string") {
        takeCb(() => {
            const b11: null = o.v;
        });
    }
}
function inLoopBody(b: { v?: string }) {
    if (b.v) {
        for (let i = 0; i < 1; i++) {
            const b12: null = b.v;
        }
    }
}
function inTryFinally(b: { v?: string }) {
    if (b.v) {
        try {
            const b13: null = b.v;
        } finally {
            const b14: null = b.v;
        }
    }
}
function viaOptionalChain(b: { inner?: { v?: string } }) {
    if (b.inner?.v) {
        const b15: null = b.inner.v;
    }
}
console.log(byIndexParam, byIndexLiteral, byGetter, byMethodCall, duAfterCall, duInCallback, Holder, byDestructure, byReadonlyProp, inLoopBody, inTryFinally, viaOptionalChain);
```

```text
===== tsc --pretty false --noEmit ex.15b.ts (tsc exit=1) =====
ex.15b.ts(9,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(14,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(19,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(24,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15b.ts(30,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15b.ts(36,19): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15b.ts(44,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(46,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(52,23): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15b.ts(61,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(68,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15b.ts(75,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(82,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(84,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15b.ts(90,15): error TS2322: Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 무엇을 좁혔나 | 결과 |
|---|---|---|
| 9 / 14 | `xs[i]`(매개변수 `i`) / `xs[0]` | `string` / `string` — **좁혀진다** |
| 19 | ★ 게터 `o.v` | `string` — **좁혀진다** |
| 24 | ★★★ 호출식 `o.v()` | **`string \| number`** — 애초에 안 좁혀진다 |
| 30 | 판별 유니온, 함수 호출 뒤 | `number` — 유지 |
| 36 | ★★★ 판별 유니온, **콜백 안** | `number` — **유지** |
| 44 / 46 | `this.v`, 호출 전 / 후 | `string` / `string` — 유지 |
| 52 | ★★★ `this.v`, **콜백 안** | **`string \| number`** — 풀림 |
| 61 | 구조 분해한 `const`, 콜백 안 | `string` — 유지 |
| 68 | ★★ `readonly o.v`, 콜백 안 | **`string \| number`** — 풀림 |
| 75 / 82 / 84 / 90 | 루프 몸통 / `try` / `finally` / 옵셔널 체이닝 뒤 | 전부 `string` — 유지 |

- ★★★ 36행과 52행이 **이 주제의 분기점**이다. 둘 다 콜백 안인데 하나는 살고 하나는 죽는다.\
  36행이 좁힌 것은 **매개변수 `s` 자신**이고(판별 유니온은 객체 전체를 좁힌다), 52행이 좁힌 것은 **프로퍼티 `this.v`** 다.\
  **변수는 「대입이 없으면」 살고, 프로퍼티는 언제나 죽는다.**
- ★★★ 68행이 흔한 착각을 깬다. **`readonly` 는 좁힘을 지켜 주지 않는다.**\
  `readonly` 는 「이 타입을 통해 쓰지 말라」는 표기일 뿐 **런타임 불변이 아니다**([**07번 주제**](../07-object-type-details/)).\
  다른 참조가 같은 객체를 바꿀 수 있으니 컴파일러는 믿지 않는다.
- ★★ 24행은 「풀렸다」가 아니다. **호출식은 참조가 아니라** 처음부터 좁힐 자리가 없다.\
  `o.v()` 는 부를 때마다 다른 값을 줄 수 있는 **식**이다.
- ★ 19행과 24행을 나란히 보면 이상하다 — 게터도 부를 때마다 다를 수 있는데 **좁혀진다.**\
  4번이 그 대가를 실물로 보여 준다.

### 3. ★★★ 풀린 것은 **셋**(25·40·54행) — 기준은 `const` 가 아니라 **대입의 유무**다

**출력**

```ts
// ex.15c.ts
// let 대 const 가 아니라 「어딘가에서 대입되는가」가 기준이다
declare function takeCb(f: () => void): void;
type Tagged = { kind: "a"; x: number } | { kind: "b" };

function constLocal(b: { v?: string }) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const c1: null = v;
        });
    }
}
function letNeverAssigned(b: { v?: string }) {
    let v = b.v;
    if (v) {
        takeCb(() => {
            const c2: null = v;
        });
    }
}
function letAssignedLater(b: { v?: string }) {
    let v = b.v;
    if (v) {
        takeCb(() => {
            const c3: null = v;
        });
    }
    v = undefined;
}
function paramNeverAssigned(s: Tagged) {
    if (s.kind === "a") {
        takeCb(() => {
            const c4: null = s.x;
        });
    }
}
function paramAssignedLater(s: Tagged) {
    if (s.kind === "a") {
        takeCb(() => {
            const c5: null = s.kind;
        });
    }
    s = { kind: "b" };
}
function indexByConstIndex(xs: (string | number)[]) {
    const i = 0;
    if (typeof xs[i] === "string") {
        const c6: null = xs[i];
    }
}
function indexByAssignedIndex(xs: (string | number)[]) {
    let i = 0;
    if (typeof xs[i] === "string") {
        const c7: null = xs[i];
    }
    i = 1;
}
console.log(constLocal, letNeverAssigned, letAssignedLater, paramNeverAssigned, paramAssignedLater, indexByConstIndex, indexByAssignedIndex);
```

```text
===== tsc --pretty false --noEmit ex.15c.ts (tsc exit=1) =====
ex.15c.ts(9,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(17,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(25,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15c.ts(33,19): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15c.ts(40,19): error TS2322: Type '"a" | "b"' is not assignable to type 'null'.
  Type '"a"' is not assignable to type 'null'.
ex.15c.ts(48,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(54,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 모양 | 결과 |
|---|---|---|
| 9 | `const v = b.v` | `string` — 유지 |
| 17 | ★★★ `let v = b.v` — **대입 없음** | `string` — **유지** |
| 25 | ★★★ `let v = b.v` — 뒤에서 `v = undefined` | **`string \| undefined`** — 풀림 |
| 33 | 매개변수 `s` — 대입 없음 | `number` — 유지 |
| 40 | 매개변수 `s` — 뒤에서 `s = { kind: "b" }` | **`"a" \| "b"`** — 풀림 |
| 48 | `xs[i]` — `const i = 0` | `string` — 유지 |
| 54 | ★★ `xs[i]` — `let i = 0` 뒤에서 `i = 1` | **`string \| number`** — 풀림 |

- ★★★ 17행과 25행이 **이 번의 전부**다. 둘 다 `let` 이고 선언식도 같은데 결과가 반대다.\
  다른 점은 **함수 끝에 `v = undefined;` 가 있느냐** 하나뿐이다.
- ★★★ 그 대입은 **콜백보다 뒤에 있는데도** 영향을 준다. 분석은 줄 순서가 아니라 **함수 전체를 보고**\
  「이 이름이 어디서든 대입되는가」를 판단한다. 대입이 하나라도 있으면 **콜백 안에서는 못 믿는다.**
- ★★ 48행과 54행이 같은 규칙을 인덱스에서 보여 준다. **인덱스 변수도 참조의 일부**라\
  `i` 가 대입되면 `xs[i]` 라는 참조 자체를 못 믿게 된다.
- ★ 그러므로 「`const` 로 바꾸면 된다」는 **틀린 설명은 아니지만 이유가 틀렸다.**\
  `const` 는 「대입이 없다」를 **문법으로 보장하는 지름길**일 뿐이다.

★★ 이 파일은 `--strict false` 에서 갈린다.

```text
===== tsc --pretty false --noEmit --strict false ex.15c.ts (tsc exit=1) =====
ex.15c.ts(9,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(17,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(25,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(33,19): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15c.ts(40,19): error TS2322: Type '"a" | "b"' is not assignable to type 'null'.
  Type '"a"' is not assignable to type 'null'.
ex.15c.ts(48,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(54,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

- ★★★ **25행만 `string` 으로 바뀐다.** 규칙이 바뀐 것이 아니라 **탐침이 차이를 못 보여 주게** 된 것이다.
- ★ `strictNullChecks` 가 꺼지면 `undefined` 가 모든 타입에 흡수된다 — 6번이 그것을 넓게 본다.

### 4. ★★★ **진단 0건 · `tsc exit 0`** — 그리고 **세 줄 다 터진다.** 보장이 아니다

**출력**

```ts
// ex.15d.ts
// 분석이 「믿어 주는」 자리 — 보장이 아니라는 것을 던져서 깨뜨린다
interface Box {
    v?: string;
}
function wipe(b: Box): void {
    delete b.v;
}
function afterCall(b: Box): string {
    if (b.v) {
        wipe(b);
        return b.v.toUpperCase();
    }
    return "없다";
}

let flip = 0;
const spy = {
    get v(): string | number {
        flip += 1;
        return flip % 2 === 1 ? "문자열" : 42;
    },
};
function afterGetter(): string {
    if (typeof spy.v === "string") {
        return spy.v.toUpperCase();
    }
    return "숫자다";
}

const shared: Box = { v: "안녕" };
async function afterAwait(): Promise<string> {
    if (shared.v) {
        await Promise.resolve();
        return shared.v.toUpperCase();
    }
    return "없다";
}

function run(label: string, f: () => string): void {
    try {
        console.log(label, f());
    } catch (e) {
        console.log(label, "터졌다 ->", (e as Error).message);
    }
}
run("afterCall  :", () => afterCall({ v: "안녕" }));
run("afterGetter:", () => afterGetter());
afterAwait().then(
    (r) => console.log("afterAwait :", r),
    (e) => console.log("afterAwait : 터졌다 ->", (e as Error).message),
);
shared.v = undefined;
```

```text
===== tsc --pretty false ex.15d.ts (tsc exit=0) =====
===== 방출된 ex.15d.js =====
"use strict";
function wipe(b) {
    delete b.v;
}
function afterCall(b) {
    if (b.v) {
        wipe(b);
        return b.v.toUpperCase();
    }
    return "없다";
}
let flip = 0;
const spy = {
    get v() {
        flip += 1;
        return flip % 2 === 1 ? "문자열" : 42;
    },
};
function afterGetter() {
    if (typeof spy.v === "string") {
        return spy.v.toUpperCase();
    }
    return "숫자다";
}
const shared = { v: "안녕" };
async function afterAwait() {
    if (shared.v) {
        await Promise.resolve();
        return shared.v.toUpperCase();
    }
    return "없다";
}
function run(label, f) {
    try {
        console.log(label, f());
    }
    catch (e) {
        console.log(label, "터졌다 ->", e.message);
    }
}
run("afterCall  :", () => afterCall({ v: "안녕" }));
run("afterGetter:", () => afterGetter());
afterAwait().then((r) => console.log("afterAwait :", r), (e) => console.log("afterAwait : 터졌다 ->", e.message));
shared.v = undefined;
```

```text
===== node ex.15d.js (node exit=0) =====
afterCall  : 터졌다 -> Cannot read properties of undefined (reading 'toUpperCase')
afterGetter: 터졌다 -> spy.v.toUpperCase is not a function
afterAwait : 터졌다 -> Cannot read properties of undefined (reading 'toUpperCase')
```

**왜 그런가**

| 호출 | 출력 | 왜 |
|---|---|---|
| `afterCall` | 터졌다 → `Cannot read properties of undefined (reading 'toUpperCase')` | `wipe(b)` 가 그 프로퍼티를 **지웠다** |
| `afterGetter` | 터졌다 → `spy.v.toUpperCase is not a function` | 게터가 **두 번째 호출에 다른 값**을 줬다 |
| `afterAwait` | 터졌다 → `Cannot read properties of undefined (reading 'toUpperCase')` | `await` 사이에 **다른 코드가 지웠다** |

- ★★★ **`tsc` 종료 코드가 `0` 이고 진단이 한 줄도 없다.** 1번 11·17행과 2번 19행이 「유지된다」고 한 바로 그 자리다.
- ★★★ 그러므로 정확한 표현은 「**안 풀린다**」가 아니라 「**분석이 믿어 준다**」다.\
  안전해서 믿는 것이 아니라, **매 호출마다 다시 의심하면 쓸 수 있는 코드가 거의 없어지기 때문**이다.
- ★★ `afterGetter` 가 가장 조용한 종류다. `if (typeof spy.v === "string")` 이 참이었는데도\
  `return spy.v.toUpperCase()` 에서 **게터가 다시 불려** 숫자가 돌아왔다. **같은 표현식이 두 번 다른 값**이었다.
- ★★ `afterAwait` 는 1번 17행의 값이다. `await` 는 **다른 코드에 제어를 넘긴다** —\
  그 사이 무슨 일이든 일어날 수 있다. 여기서는 마지막 줄의 `shared.v = undefined;` 가 그 일이다.
- ★ 방출된 `.js` 에는 타입 관련 글자가 **하나도 없다.** 남는 것은 `if (b.v)` 라는 **JS 조건문뿐**이고,\
  좁힘을 지켜 주는 장치는 **어디에도 없다.**

### 5. ★★★ 진단 **9건** — 고침은 **지역 `const` 하나**이고, **단언은 고치는 법이 아니다**

**출력**

```ts
// ex.15e.ts
// 고치는 법 — 지역 const 하나. 같은 코드를 고치기 전과 뒤로 나란히 둔다
interface Box {
    v?: string;
}
type Shape =
    | { kind: "circle"; r: number }
    | { kind: "square"; side: number };
declare function takeCb(f: () => void): void;
declare function assertDefined<T>(v: T): asserts v is NonNullable<T>;

function brokenByProperty(b: Box) {
    if (b.v) {
        takeCb(() => {
            const e1: null = b.v;
        });
    }
}
function fixedByLocalConst(b: Box) {
    const v = b.v;
    if (v) {
        takeCb(() => {
            const e2: null = v;
        });
    }
}
function fixedByDestructure(b: Box) {
    const { v } = b;
    if (v) {
        takeCb(() => {
            const e3: null = v;
        });
    }
}
function fixedByAssertion(b: Box) {
    assertDefined(b.v);
    const e4: null = b.v;
    takeCb(() => {
        const e5: null = b.v;
    });
}
function brokenIndex(xs: (string | number)[]) {
    let i = 0;
    if (typeof xs[i] === "string") {
        const e6: null = xs[i];
    }
    i = 1;
}
function fixedIndex(xs: (string | number)[]) {
    let i = 0;
    const x = xs[i];
    if (typeof x === "string") {
        const e7: null = x;
    }
    i = 1;
}
function brokenDiscriminant(s: Shape) {
    if (s.kind === "circle") {
        takeCb(() => {
            const e8: null = s.kind;
        });
    }
    s = { kind: "square", side: 1 };
}
function fixedDiscriminant(s: Shape) {
    const shape = s;
    if (shape.kind === "circle") {
        takeCb(() => {
            const e9: null = shape.r;
        });
    }
    s = { kind: "square", side: 1 };
}
console.log(brokenByProperty, fixedByLocalConst, fixedByDestructure, fixedByAssertion, brokenIndex, fixedIndex, brokenDiscriminant, fixedDiscriminant);
```

```text
===== tsc --pretty false --noEmit ex.15e.ts (tsc exit=1) =====
ex.15e.ts(14,19): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15e.ts(22,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(30,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(36,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(38,15): error TS2322: Type 'string | undefined' is not assignable to type 'null'.
  Type 'undefined' is not assignable to type 'null'.
ex.15e.ts(44,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15e.ts(52,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(59,19): error TS2322: Type '"circle" | "square"' is not assignable to type 'null'.
  Type '"circle"' is not assignable to type 'null'.
ex.15e.ts(68,19): error TS2322: Type 'number' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 모양 | 결과 |
|---|---|---|
| 14 | 고치기 전 — 콜백 안의 `b.v` | **`string \| undefined`** |
| 22 | ★★★ `const v = b.v` 로 고침 | `string` |
| 30 | `const { v } = b` 로 고침 | `string` |
| 36 | `assertDefined(b.v)` **직후** | `string` |
| 38 | ★★★ 같은 단언 뒤의 **콜백 안** | **`string \| undefined`** — 안 고쳐졌다 |
| 44 / 52 | 인덱스 — 고치기 전 / `const x = xs[i]` 로 고침 | `string \| number` / `string` |
| 59 / 68 | 판별 유니온 — 고치기 전 / `const shape = s` 로 고침 | `"circle" \| "square"` / `number` |

- ★★★ 36행과 38행이 이 번의 별이다. **단언은 좁힘을 만들지만 지키지는 못한다.**\
  [**14번 주제**](../14-assertion-signatures/)의 `asserts` 가 프로퍼티를 좁혀도, 그 좁힘은 **여전히 프로퍼티 좁힘**이라 콜백에서 풀린다.
- ★★★ 고침 넷의 공통점은 하나다 — 「**다시 읽지 않아도 되게 한 번만 읽어 손에 쥔다.**」\
  `const v = b.v` · `const { v } = b` · `const x = xs[i]` · `const shape = s` 가 전부 같은 동작이다.
- ★★ 인덱스는 **인덱스 변수를 `const` 로 바꾸는 것만으로도** 되지만(3번 48행),\
  값을 꺼내는 편이 더 넓게 통한다 — 배열 자체가 바뀌는 경우까지 막아 준다.
- ★ 고침에는 **의미의 변화**가 따른다. 원본이 바뀌어도 손에 쥔 값은 안 바뀐다 —\
  그것이 안전의 값이자, **정말 최신 값을 원했다면 버그**다. 무엇을 원하는지부터 정해야 한다.

### 6. ★★ 1번은 **두 줄**, 3번은 **한 줄**, 5번은 **두 줄**이 바뀐다 — 그리고 **실험이 안 보이게 된다**

**출력**

```text
===== tsc --pretty false --noEmit --strict false ex.15a.ts (tsc exit=1) =====
ex.15a.ts(11,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(17,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(23,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(30,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(38,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(44,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(46,15): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15a.ts(53,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(60,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15a.ts(62,19): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15a.ts(70,19): error TS2322: Type 'string' is not assignable to type 'null'.
```

```text
===== tsc --pretty false --noEmit --strict false ex.15c.ts (tsc exit=1) =====
ex.15c.ts(9,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(17,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(25,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(33,19): error TS2322: Type 'number' is not assignable to type 'null'.
ex.15c.ts(40,19): error TS2322: Type '"a" | "b"' is not assignable to type 'null'.
  Type '"a"' is not assignable to type 'null'.
ex.15c.ts(48,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15c.ts(54,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

```text
===== tsc --pretty false --noEmit --strict false ex.15e.ts (tsc exit=1) =====
ex.15e.ts(14,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(22,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(30,19): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(36,11): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(38,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(44,15): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.15e.ts(52,15): error TS2322: Type 'string' is not assignable to type 'null'.
ex.15e.ts(59,19): error TS2322: Type '"circle" | "square"' is not assignable to type 'null'.
  Type '"circle"' is not assignable to type 'null'.
ex.15e.ts(68,19): error TS2322: Type 'number' is not assignable to type 'null'.
```

```text
===== 같은 파일을 기본값과 --strict false 로 각각 던져 글자 단위로 대조한다 =====
ex.15a.ts    exit 1 / exit 1 · ★ 다르다
ex.15b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.15c.ts    exit 1 / exit 1 · ★ 다르다
ex.15e.ts    exit 1 / exit 1 · ★ 다르다
```

**왜 그런가**

- ★★★ 1번 파일에서 **23·30행의 글자가 `string`** 이 된다. 11·17행(안 풀린 자리)과 **같은 글자**가 된다.
- ★ 62행은 `string | number` 로 남는다 — 그 유니온에는 `null`·`undefined` 가 없어서 플래그와 무관하다.
- ★★★ 3번 파일에서는 **25행 하나**만 바뀌고, 5번 파일에서는 **14·38행 둘**이 바뀐다. 역시 「풀렸다」가 **안 보이게** 된다.
- ★★ 특히 5번 38행(단언 뒤 콜백)이 고쳐진 자리와 **구별되지 않게** 되는 것이 위험하다.
- ★★ 즉 `--strict false` 가 바꾸는 것은 **규칙이 아니라 탐침의 해상도**다.\
  `strictNullChecks` 가 꺼지면 `undefined` 가 모든 타입에 흡수돼 **차이가 사라진다.**
- ★★★ 그러므로 **이 주제를 실험하려면 `strictNullChecks` 가 켜져 있어야 한다.**\
  7.0 의 `strict` 기본값이 `true` 라 별도로 켤 일은 없다.
- ★ 네 파일 중 **셋이 갈리고**, 갈리는 방향은 **전부 같다.**

### 7. ★★★ **콜백은 언제 불릴지 모르기 때문**이다

**왜 그런가**

- 콜백은 **즉시 불릴 수도, 한참 뒤에 불릴 수도, 여러 번 불릴 수도, 아예 안 불릴 수도** 있다.\
  `setTimeout`·이벤트 핸들러·`Promise.then` 이 전부 그렇다.
- ★★ 그 사이에 **프로퍼티가 바뀔 수 있다.** 같은 객체를 가리키는 다른 참조가 얼마든지 있을 수 있다.\
  그래서 **프로퍼티 좁힘은 통째로 버린다** — 1번 23행 · 2번 52·68행.
- ★★★ 반대로 **변수는 지킬 수 있다.** 「이 함수 안에서 이 이름에 누가 대입하는가」는\
  **컴파일러가 소스만 보고 확인할 수 있다.** 대입이 하나도 없으면 값이 바뀔 길이 없다 — 3번의 격자가 그 확인 결과다.
- ★★ 즉시 실행 함수가 예외인 이유도 같다 — 「**지금 부른다**」가 문법에 보이면 **사이에 낄 코드가 없다.**
- ★ 중첩 **함수 선언**이 콜백과 같은 취급을 받는 것은 호이스팅 때문이다. 이름이 블록 전체에서 보이므로\
  **어디서든 불릴 수 있다**(1번 30행).

### 8. ★★★ **안전해서가 아니라, 버리면 쓸 수 있는 코드가 거의 없어지기 때문**이다

**왜 그런가**

- 호출 뒤에 좁힘을 버리면 `if (x) { log(); x.f(); }` 같은 **가장 흔한 모양**이 전부 에러가 난다.\
  로그 한 줄, 길이 계산 한 번마다 다시 체크해야 한다.
- ★★ 그래서 TS 는 **의도적으로 unsound 한 선택**을 했다. 「함수가 내 지역 상태를 바꾸지는 않겠지」를 **가정**한다.
- ★★★ 4번이 그 가정이 깨지는 모습이다 — `wipe(b)` 가 바로 그 프로퍼티를 지웠고, **컴파일은 통과했다.**\
  「안 풀린다」는 **분석의 정책**이지 **런타임의 보장이 아니다.**
- ★★ 같은 이유로 `await` 뒤도 안 풀린다(1번 17행). 그쪽은 **다른 코드가 끼어드는 것이 확실한데도** 그렇다 —\
  4번의 `afterAwait` 가 그 대가다.
- ★ 실무의 교훈 — **프로퍼티를 지우거나 갈아 끼우는 함수**가 있는 코드에서는\
  「컴파일이 통과했다」를 안전의 근거로 쓰지 마라. **사람이 한 번 더 본다.**

### 9. ★★ **좁힌 것이 「이름」이냐 「남의 주머니 속」이냐**가 기준이다

**왜 그런가**

| | 변수 이름 `v` | 프로퍼티 `b.v` |
|---|---|---|
| 누가 바꿀 수 있나 | ★ **이 함수 안의 대입뿐** | 같은 객체를 가리키는 **모든 참조** |
| 컴파일러가 확인 가능한가 | ★★ **가능하다** — 소스를 훑으면 된다 | ★★ **불가능하다** — 객체가 어디로 갔는지 모른다 |
| 콜백 안에서 | 대입이 없으면 **산다** | ★ **언제나 풀린다** |
| `readonly` 를 붙이면 | — | ★★ **여전히 풀린다**(2번 68행) |

- ★★★ 한 문장으로 — 「**컴파일러가 「아무도 안 바꾼다」를 스스로 증명할 수 있으면 살고, 아니면 죽는다.**」
- ★★ 판별 유니온이 콜백에서도 사는 것(2번 36행)은 좁혀진 것이 **매개변수 이름 `s`** 이기 때문이다.\
  같은 객체의 **프로퍼티를 좁혔다면** 죽었을 것이다.
- ★★ `readonly` 가 못 막는 이유도 같다. **다른 참조가 같은 객체를 바꿀 수 있고**, 그 참조에는 `readonly` 가 없다.
- ★ `this.v` 는 생김새가 변수 같아도 **프로퍼티 접근**이다(2번 52행). 헷갈리기 쉬운 자리다.

### 10. ★★ 판별 유니온은 **객체 자체를 좁힐 때 안전**하고, **그 객체 이름이 대입되면 풀린다**

**왜 그런가**

| 자리 | 결과 | 근거 |
|---|---|---|
| 함수 호출 뒤 | ★ 유지 | 2번 30행 |
| 콜백 안, 매개변수 대입 없음 | ★★★ **유지** | 2번 36행 |
| 콜백 안, 매개변수가 뒤에서 대입됨 | ★ **풀림** | 3번 40행 |
| 고침 — `const shape = s` | 유지 | 5번 68행 |

- ★★★ 판별 유니온은 **다른 좁히기보다 콜백에 강하다.** `s.kind === "circle"` 이 좁히는 것은\
  `s.kind` 가 아니라 **`s` 자신**이기 때문이다 — 변수 좁힘이라 9번의 규칙을 그대로 받는다.
- ★★ 그래서 실무에서 판별 유니온이 편한 것이다. 「필드 하나를 검사했더니 **객체 전체의 타입**이 정해진다」가\
  콜백 경계까지 따라온다.
- ★★ 다만 **그 매개변수에 다시 대입하면 무너진다**(3번 40행). 인자를 재활용해 다른 값을 넣는 코드가 그 예다.
- ★ 고치는 법도 같다 — **`const` 로 한 번 못 박는다**(5번 68행).
- ★ 판별 칸만 변수에 뽑는 것(`const k = s.kind;`)은 **도움이 안 된다.** `k` 와 `s` 의 연결이 끊겨\
  `s` 는 여전히 유니온이다([**12번 주제**](../12-narrowing/)의 별칭 조건과 함께 읽는다).

### 11. ★★ **그대로 받는다** — 만드는 수단이 달라도 **지켜지는 규칙은 하나**다

**왜 그런가**

| 좁힘을 만든 수단 | 콜백 안에서 | 근거 |
|---|---|---|
| 내장 가드 `if (b.v)` — 프로퍼티 | 풀린다 | 1번 23행 |
| 내장 가드 `if (typeof v === …)` — 변수 | 대입 없으면 산다 | 3번 17행 |
| 술어 `isX(v)` ([**13번 주제**](../13-type-guards-and-predicates/)) — 변수 | 대입 없으면 산다 | 3번의 규칙과 같다 |
| ★★★ 단언 `assertDefined(b.v)` ([**14번 주제**](../14-assertion-signatures/)) — 프로퍼티 | **풀린다** | 5번 38행 |

- ★★★ 5번 38행이 그 증거다. `asserts` 는 **좁힘의 범위를 넓히는** 수단이지(호출 뒤 전부),\
  **좁힘의 성질을 바꾸는** 수단이 아니다. 프로퍼티를 좁혔으면 여전히 **프로퍼티 좁힘**이다.
- ★★ 술어도 같다. `if (isString(b.v)) { cb(() => b.v) }` 는 콜백에서 풀린다 —\
  술어가 한 일은 **어떤 검사인지를 반환 타입에 실어 보낸 것**뿐이고, 좁힘 자체는 같은 분석이 한다.
- ★★ 그래서 세 주제가 한 사슬이다 — [**12번 주제**](../12-narrowing/)가 **수단**, [**13번 주제**](../13-type-guards-and-predicates/)·[**14번 주제**](../14-assertion-signatures/)가 **포장**,\
  이 주제가 **수명**이다.
- ★ 고치는 법도 하나다 — **지역 `const`**. 어떤 수단으로 좁혔든 마찬가지다.

### 12. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 좁힘은 **참조**에 붙고 호출식에는 안 붙는다 · 콜백 안에서 **프로퍼티 좁힘은 풀린다** · 재대입은 좁힘을 **갱신**한다 · 좁힘은 방출된 JS 에 **한 글자도 안 남는다** |
| **설정에 달린 것** | ★ **다섯 칸**(1절 둘 · 3절 하나 · 5절 둘). 탐침의 표시 — `strictNullChecks`(`strict` 에 딸려 7.0 기본 `true`). 끄면 **차이가 안 보이게 된다**(규칙이 바뀌는 것이 아니다). **양쪽 판을 다 실었다** · `noUncheckedIndexedAccess` 를 켜면 인덱스 칸이 달라진다 — **안 켰다** |
| **이 판(7.0.2)의 관찰** | ★★★ **「대입이 없으면 콜백에서도 산다」는 조건**(3번) — 구현의 경계다 · 즉시 실행 함수에서 유지되는 것(1번 38행) · 인덱스 접근이 좁혀지는 조건(2번 9·14행) · 진단 문구 전문 · 런타임 예외 문구 두 가지(`node` v18) |

- ★★★ 「**진단 0건」이 답인 블록이 하나**다(4번). 그래서 이 문서는 **소스 전문·방출 전문·실행 출력**을 나란히 실었다.
- ★★ 이 주제는 **에러 코드가 거의 없다.** 「타입이 안 줄었다」로만 나타나므로 **탐침 없이는 관찰 자체가 안 된다.**
- ★ **격자는 외우지 말고 다시 던져라.** 이 문서가 파일 셋(`ex.15a`·`ex.15c`·`ex.15e`)을 남겨 둔 이유다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 경계를 넘는 열한 자리 | `--noEmit ex.15a.ts` | exit 1 · **11건** · 풀린 것 **4개** · 즉시 실행 함수는 **유지** |
| 〃 `strict` 끔 | `--noEmit --strict false ex.15a.ts` | exit 1 · **23·30행** 글자가 바뀜 |
| 무엇을 좁혔나 열다섯 자리 | `--noEmit ex.15b.ts` | exit 1 · **15건** · 안 좁혀진 것 **3개**(24·52·68행) |
| `let` 대 `const` 일곱 칸 | `--noEmit ex.15c.ts` | exit 1 · **7건** · 풀린 것 **3개**(25·40·54행) |
| 〃 `strict` 끔 | `--noEmit --strict false ex.15c.ts` | exit 1 · **25행만** 바뀜 |
| ★ 믿어 주는 자리 | `tsc ex.15d.ts` + `node ex.15d.js` | ★★★ **tsc exit 0 · 진단 0건** · node exit 0 · **세 줄 다 터짐** |
| 고치는 법 | `--noEmit ex.15e.ts` | exit 1 · **9건** · 고침 4개 성공 · ★ **38행(단언 + 콜백)은 안 고쳐짐** |
| 〃 `strict` 끔 | `--noEmit --strict false ex.15e.ts` | exit 1 · **14·38행** 글자가 바뀜 |
| `strict` 대조 | 네 파일을 `--strict false` 로 재실행 | ★ **셋이 갈림** — 전부 같은 방향 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **「그 함수 안에서 대입이 없으면 콜백에서도 산다」는 조건**(3번) — **구현의 경계**다.\
  이 문서의 격자는 **이 판의 관찰**이지 언어 보장이 아니다.
- ★★ **즉시 실행 함수 안에서 유지되는 것**(1번 38행) — 같은 이유로 판마다 다시 던져라.
- ★★ **인덱스 접근이 좁혀지는 조건**(2번 9·14행 · 3번 48·54행).
- ★ 런타임 예외 문구 `Cannot read properties of undefined (reading 'toUpperCase')` 와\
  `spy.v.toUpperCase is not a function` — `node` v18 의 메시지다.
- 진단의 들여쓴 줄이 **어느 조각을 대표로** 짚는가 — 보고기의 구현이다.

**안 돌려 본 것**

- **`noUncheckedIndexedAccess` 를 켠 판** — 2절의 인덱스 칸이 달라진다. **안 켰다** — [목록의 **41번 주제**](../41-index-and-optional-property-strict-flags/).
- **`exactOptionalPropertyTypes` 를 켠 판** — 선택 프로퍼티의 모양이 달라진다. **안 켰다.**
- **제너레이터·`for await...of` 안에서의 좁힘** — **안 던졌다.**
- **클래스 필드를 `#private` 로 두었을 때** — **안 던졌다.** [목록의 **32번 주제**](../32-class-type-aspects/).
- **제어 흐름 분석의 검사 시간** — **재지 않았고 수치를 적지 않았다.**
