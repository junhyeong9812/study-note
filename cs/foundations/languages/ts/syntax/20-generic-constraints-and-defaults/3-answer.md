# ts/syntax/20 — 제네릭 제약과 기본 타입 인자 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단 전문은 `tsc` **7.0.2** 와 `rustc` **1.92.0** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★ 단 **3번의 `TS2322` 는 진짜 에러**다. 문구로 가른다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **7건** — 제약이 없으면 `T` 는 아무것도 아니다

**출력**

```ts
// ex.20a.ts
// extends 제약 -- 제약이 없으면 아무 멤버도 못 쓴다. 제약은 "이 모양 이상"이라는 뜻이다
function lenNone<T>(x: T): number {
    return x.length;
}

function lenOf<T extends { length: number }>(x: T): number {
    return x.length;
}

const p1: null = lenOf("가나다");
const p2: null = lenOf([1, 2]);
const p3: null = lenOf({ length: 3, extra: true });

lenOf(3);

interface HasLen {
    length: number;
}
class Rope {
    length = 10;
}
const p4: null = lenOf(new Rope());
declare const shaped: HasLen;
const p5: null = lenOf(shaped);
console.log(p1, p2, p3, p4, p5);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.20a.ts (tsc exit=1) =====
ex.20a.ts(3,14): error TS2339: Property 'length' does not exist on type 'T'.
ex.20a.ts(10,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.20a.ts(11,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.20a.ts(12,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.20a.ts(14,7): error TS2345: Argument of type 'number' is not assignable to parameter of type '{ length: number; }'.
ex.20a.ts(22,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.20a.ts(24,7): error TS2322: Type 'number' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 3 | ★★★ 제약 없는 `T` 의 `.length` | **`TS2339`** — ★ **정의 자리**에 난다 |
| 10·11·12 | `lenOf("가나다")`·`lenOf([1,2])`·`lenOf({length:3, extra:true})` | 전부 **`number`** — 통과한다 |
| 14 | `lenOf(3)` | `TS2345` — ★ **사용 자리**에 난다 |
| 22 | ★★★ `lenOf(new Rope())` | **`number`** — `implements` 가 없는데 통과한다 |
| 24 | `lenOf(shaped)` | `number` |

- ★★★ 3행과 14행이 **다른 자리의 진단**이다. **몸통은 정의 시점에**, **인자는 호출 시점에** 검사된다.\
  이 구별은 6번에서 Rust 와 견줄 때 결정적이다.
- ★★ 12행이 「하한」을 보여 준다 — `{ length: 3, extra: true }` 는 제약보다 **더 가졌는데** 통과한다.\
  제약은 「정확히 이 모양」이 아니라 「**이 모양 이상**」이다.
- ★★★ 22행이 TS 제약의 성질이다. `class Rope` 는 `HasLen` 을 **`implements` 하지 않았다.**\
  그래도 `length: number` 를 가졌으므로 통과한다 — **구조적 타이핑**([**05번 주제**](../05-structural-typing/)).\
  6번에서 Rust 가 **바로 이 자리에서** 막는다.

### 2. ★★ **`string` · `number` · `boolean`** — 키가 값 타입을 정한다

**출력**

```ts
// ex.20b.ts
// keyof 제약 -- get(obj, key) 관용구. 키가 값 타입을 정한다
function get<O, K extends keyof O>(obj: O, key: K): O[K] {
    return obj[key];
}

const user = { name: "준", age: 30, admin: false };

const p1: null = get(user, "name");
const p2: null = get(user, "age");
const p3: null = get(user, "admin");

get(user, "nope");

declare const dynamicKey: string;
get(user, dynamicKey);

function getLoose<O>(obj: O, key: string): unknown {
    return (obj as Record<string, unknown>)[key];
}
const p4: null = getLoose(user, "nope");

type UserKeys = keyof typeof user;
declare const k: UserKeys;
const p5: null = k;
console.log(p1, p2, p3, p4, p5);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.20b.ts (tsc exit=1) =====
ex.20b.ts(8,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.20b.ts(9,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.20b.ts(10,7): error TS2322: Type 'boolean' is not assignable to type 'null'.
ex.20b.ts(12,11): error TS2345: Argument of type '"nope"' is not assignable to parameter of type '"admin" | "age" | "name"'.
ex.20b.ts(15,11): error TS2345: Argument of type 'string' is not assignable to parameter of type '"admin" | "age" | "name"'.
ex.20b.ts(20,7): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.20b.ts(24,7): error TS2322: Type '"admin" | "age" | "name"' is not assignable to type 'null'.
  Type '"admin"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 8 | `get(user, "name")` | **`string`** |
| 9 | `get(user, "age")` | **`number`** |
| 10 | `get(user, "admin")` | **`boolean`** |
| 12 | `get(user, "nope")` | `TS2345` — ★ **허용 키 목록이 찍힌다**: `'"admin" \| "age" \| "name"'` |
| 15 | ★★★ `get(user, dynamicKey)` — `string` 변수 | `TS2345` — **막힌다** |
| 20 | `getLoose(user, "nope")` | `unknown` — 오타도 안 잡고 타입도 안 준다 |
| 24 | `keyof typeof user` | `"admin" \| "age" \| "name"` |

- ★★★ 8·9·10행이 이 관용구의 값이다. **함수는 하나인데 반환 타입이 키마다 다르다** —\
  `O[K]` 가 「받은 키의 값 타입」을 그대로 계산한다.
- ★★ 12행의 진단에 **허용 키 목록이 통째로 찍히는** 것이 실용적으로 크다. 오타를 고칠 후보가 에러에 들어 있다.\
  ★ 순서는 실측에서 **사전순**이었다(5회 재실행 동일) — **관찰이지 보장이 아니다.**
- ★★★ 15행이 경계다. `dynamicKey: string` 은 **런타임에 무슨 값일지 모르므로** `keyof` 제약을 못 만족한다.\
  **`keyof` 제약은 키가 컴파일 타임에 알려져 있을 때만** 쓸 수 있다.
- ★ 20행이 그때의 대안이고 **대가가 크다** — `unknown` 을 받아 좁혀야 한다.

### 3. ★★★ 진단 **2건** — 「could be instantiated with a different subtype」

**출력**

```ts
// ex.20c.ts
// 제약이 있어도 그 제약 타입의 값을 안에서 만들 수는 없다 -- 유명한 함정
interface Point {
    x: number;
    y: number;
}

function makeOrigin<T extends Point>(): T {
    return { x: 0, y: 0 };
}

function readOnly<T extends Point>(p: T): number {
    return p.x + p.y;
}

function returnsConstraint<T extends Point>(p: T): Point {
    return { x: 0, y: 0 };
}

function spreadIn<T extends Point>(p: T): T {
    return { ...p, x: 0 };
}

function spreadProbe<T extends Point>(p: T): void {
    const q = { ...p, x: 0 };
    const probe: null = q;
    console.log(probe);
}

interface Point3 extends Point {
    z: number;
}
declare const point3: Point3;
const got: Point3 = spreadIn(point3);
console.log(makeOrigin, readOnly, returnsConstraint, spreadProbe, got);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.20c.ts (tsc exit=1) =====
ex.20c.ts(8,5): error TS2322: Type '{ x: number; y: number; }' is not assignable to type 'T'.
  '{ x: number; y: number; }' is assignable to the constraint of type 'T', but 'T' could be instantiated with a different subtype of constraint 'Point'.
ex.20c.ts(25,11): error TS2322: Type 'T & { x: number; }' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 8 | ★★★ `return { x: 0, y: 0 };` — 반환이 `T` | **`TS2322`** + 연쇄 설명 |
| 12 | `return p.x + p.y;` — 읽기만 | **통과** |
| 16 | `return { x: 0, y: 0 };` — 반환이 `Point` | **통과** |
| 20 | ★★★ `return { ...p, x: 0 };` — 반환이 `T` | **통과** |
| 25 | 그 스프레드의 탐침 | **`T & { x: number; }`** |

- ★★★ 8행의 연쇄 설명이 이 주제 전체의 답이다 —\
  「'{ x: number; y: number; }' is assignable to the constraint of type 'T', **but 'T' could be instantiated with a different subtype of constraint 'Point'**.」\
  **`T` 는 `Point` 「이상」** 이므로 `Point3`(x·y·z)일 수 있다. 함수가 만든 `{x:0,y:0}` 에는 **`z` 가 없다.**
- ★★ 12행이 비대칭의 다른 쪽이다 — **읽기는 언제나 안전하다.** 모든 후보가 `x`·`y` 를 가진다.
- ★★ 16행이 첫 번째 고침이다 — 반환 타입을 **제약으로 낮추면** 만들 수 있다. 대신 **호출자가 `T` 를 잃는다.**
- ★★★ 20·25행이 **진짜 고침**이다. `{ ...p, x: 0 }` 의 타입이 **`T & { x: number; }`** 이고,\
  교차는 `T` 의 **부분 타입**이므로 `T` 자리에 들어간다. `z` 가 있었으면 **`T` 안에 그대로 있다.**\
  즉 「새로 만든 것」이 아니라 「**받은 것에 덧칠한 것**」이다.
- ★ 32행이 그 결과다 — `spreadIn(point3)` 가 `Point3` 로 **그대로** 돌아온다.

### 4. ★★★ `TS2344` · **다르다** · `TS2744`

**출력**

```ts
// ex.20d.ts
// 기본 타입 인자 -- 안 적으면 그것이 쓰인다. 기본값도 제약을 지켜야 한다
interface BoxDefault<T = string> {
    value: T;
}

declare const d1: BoxDefault;
declare const d2: BoxDefault<number>;
const p1: null = d1;
const p2: null = d2;

interface Bounded<T extends { id: number } = { id: number; name: string }> {
    value: T;
}
declare const d3: Bounded;
const p3: null = d3;

interface BadDefault<T extends number = string> {
    value: T;
}

function makeBox<T = boolean>(value?: T): { value: T | undefined } {
    return { value };
}
const p4: null = makeBox();
const p5: null = makeBox("가");

interface Ordered<A, B = A> {
    a: A;
    b: B;
}
declare const d4: Ordered<number>;
const p6: null = d4;

interface Backwards<A = B, B = number> {
    a: A;
    b: B;
}
console.log(p1, p2, p3, p4, p5, p6);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.20d.ts (tsc exit=1) =====
ex.20d.ts(8,7): error TS2322: Type 'BoxDefault<string>' is not assignable to type 'null'.
ex.20d.ts(9,7): error TS2322: Type 'BoxDefault<number>' is not assignable to type 'null'.
ex.20d.ts(15,7): error TS2322: Type 'Bounded<{ id: number; name: string; }>' is not assignable to type 'null'.
ex.20d.ts(17,41): error TS2344: Type 'string' does not satisfy the constraint 'number'.
ex.20d.ts(24,7): error TS2322: Type '{ value: boolean | undefined; }' is not assignable to type 'null'.
ex.20d.ts(25,7): error TS2322: Type '{ value: string | undefined; }' is not assignable to type 'null'.
ex.20d.ts(32,7): error TS2322: Type 'Ordered<number, number>' is not assignable to type 'null'.
ex.20d.ts(34,25): error TS2744: Type parameter defaults can only reference previously declared type parameters.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 8·9 | `BoxDefault` · `BoxDefault<number>` | `BoxDefault<string>` · `BoxDefault<number>` — ★ `TS2314` 가 **사라졌다** |
| 15 | `Bounded`(제약 + 기본값) | `Bounded<{ id: number; name: string; }>` |
| 17 | ★★★ `BadDefault<T extends number = string>` | **`TS2344`** — 「does not satisfy the constraint」 |
| 24 | `makeBox()` | `{ value: boolean \| undefined; }` — **기본값으로 고정** |
| 25 | ★★ `makeBox("가")` | `{ value: string \| undefined; }` — **추론이 이긴다** |
| 32 | `Ordered<number>` — `<A, B = A>` | `Ordered<number, number>` |
| 34 | ★★★ `Backwards<A = B, B = number>` | **`TS2744`** — 앞의 것만 참조할 수 있다 |

- ★★★ 17행이 규칙이다. 기본값은 **인자를 안 줬을 때 그대로 쓰이므로** 제약을 어기면 그 순간 깨진다.\
  그래서 **선언 자리에서** 막는다.
- ★★ 24행과 25행이 다른 것이 함수 기본값의 성질이다 — **추론이 되면 추론이 이기고, 안 되면 기본값**이다.\
  즉 함수의 기본 타입 인자는 「**추론 실패 시의 대비책**」이다.\
  ★ [**19번 주제**](../19-generics-basics/) 4절의 `withDefault<string>` 은 **꺾쇠를 적었기 때문에** 추론이 아예 시도되지 않은 경우다 —\
  같은 기능의 두 얼굴이니 헷갈리지 마라.
- ★★ 32행 — 기본값이 **앞의 매개변수를 참조**하면 뒤쪽이 앞쪽을 따라온다. 자주 쓰는 꼴이다.
- ★★★ 34행 — **뒤의 것은 못 참조한다.** 선언이 왼쪽부터 처리되기 때문이다.

### 5. ★★ 재귀 제약은 **실제로 작동한다**

**출력**

```ts
// ex.20e.ts
// 재귀적 제약 -- 타입 매개변수가 자기 자신을 제약에 쓴다
function treeOf<T extends Record<string, T>>(t: T): T {
    return t;
}

type Tree = { [k: string]: Tree };
declare const tree: Tree;
const p1: null = treeOf(tree);
const p2: null = treeOf({});

treeOf({ a: 1 });

interface Comparable<U> {
    compareTo(other: U): number;
}
function maxOf<T extends Comparable<T>>(a: T, b: T): T {
    return a.compareTo(b) >= 0 ? a : b;
}
class Money implements Comparable<Money> {
    constructor(public won: number) {}
    compareTo(other: Money): number {
        return this.won - other.won;
    }
}
const p3: null = maxOf(new Money(1), new Money(2));

maxOf(1, 2);

type Json = string | number | boolean | null | Json[] | { [k: string]: Json };
declare const json: Json;
const p4: null = json;
console.log(p1, p2, p3, p4);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.20e.ts (tsc exit=1) =====
ex.20e.ts(8,7): error TS2322: Type 'Tree' is not assignable to type 'null'.
ex.20e.ts(9,7): error TS2322: Type '{}' is not assignable to type 'null'.
ex.20e.ts(11,10): error TS2322: Type 'number' is not assignable to type '{ a: number; }'.
ex.20e.ts(25,7): error TS2322: Type 'Money' is not assignable to type 'null'.
ex.20e.ts(27,7): error TS2345: Argument of type 'number' is not assignable to parameter of type 'Comparable<1 | 2>'.
ex.20e.ts(31,7): error TS2322: Type 'Json' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 8·9 | `treeOf(tree)` · `treeOf({})` | `Tree` · `{}` — **성립한다** |
| 11 | ★★ `treeOf({ a: 1 })` | `Type 'number' is not assignable to type '{ a: number; }'` |
| 25 | `maxOf(new Money(1), new Money(2))` | `Money` — `T extends Comparable<T>` 가 돈다 |
| 27 | ★★ `maxOf(1, 2)` | `TS2345` — **`Comparable<1 \| 2>`** 가 찍힌다 |
| 31 | `Json` 별칭 | `Json` — 별칭의 재귀는 제약 없이도 된다 |

- ★★ 11행이 재귀가 **진짜로 도는** 증거다. `T` 가 `{ a: number }` 로 추론되면 제약이 `Record<string, { a: number }>` 가 되고,\
  그러면 값 `1` 이 그 자리에 안 맞는다. **자기 참조가 한 바퀴 돌아 인자를 검사한다.**
- ★★★ 25행의 `T extends Comparable<T>` 는 **Java 의 `<T extends Comparable<T>>` 와 글자까지 닮았다**\
  (Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번**). 「자기를 비교할 수 있는 것만」이라는 같은 관용구다.
- ★★ 27행의 진단이 덤으로 [**19번 주제**](../19-generics-basics/) 2절을 다시 보여 준다 —\
  스칼라 인자 둘이 **`1 | 2` 라는 리터럴 유니온**으로 모였다. **스칼라는 리터럴이 살아남는다.**
- ★ 깊이 한계와 검사 시간은 **안 쟀다.**

### 6. ★★★ 에러 **3건** — Rust 는 **이름**으로 걸고 함수 기본값을 **금지**한다

**출력**

```rust
// ex.20f.rs
// Rust 대비 -- 바운드는 이름으로 걸리고, 몸통은 정의 자리에서 검사되고, 함수에는 기본 타입 인자를 못 단다
use std::fmt::Display;

struct Loud {
    n: i32,
}

impl Loud {
    fn fmt(&self) -> String {
        format!("{}", self.n)
    }
}

fn no_bound<T>(x: T) -> String {
    format!("{}", x)
}

fn show<T: Display>(x: T) -> String {
    format!("{}", x)
}

fn defaulted<T = i32>(x: T) -> T {
    x
}

fn main() {
    println!("{}", show(3));
    println!("{}", show(Loud { n: 1 }));
    println!("{}", defaulted(1));
    println!("{}", no_bound(1));
}
```

```text
===== rustc --edition 2021 --crate-name ex20f ex.20f.rs (rustc exit=1) =====
error: defaults for generic parameters are not allowed here
  --> ex.20f.rs:22:14
   |
22 | fn defaulted<T = i32>(x: T) -> T {
   |              ^^^^^^^
   |
   = warning: this was previously accepted by the compiler but is being phased out; it will become a hard error in a future release!
   = note: for more information, see issue #36887 <https://github.com/rust-lang/rust/issues/36887>
   = note: `#[deny(invalid_type_param_default)]` (part of `#[deny(future_incompatible)]`) on by default

error[E0277]: `T` doesn't implement `std::fmt::Display`
  --> ex.20f.rs:15:19
   |
15 |     format!("{}", x)
   |              --   ^ `T` cannot be formatted with the default formatter
   |              |
   |              required by this formatting parameter
   |
   = note: in format strings you may be able to use `{:?}` (or {:#?} for pretty-print) instead
   = note: this error originates in the macro `$crate::__export::format_args` which comes from the expansion of the macro `format` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider restricting type parameter `T` with trait `Display`
   |
14 | fn no_bound<T: std::fmt::Display>(x: T) -> String {
   |              +++++++++++++++++++

error[E0277]: `Loud` doesn't implement `std::fmt::Display`
  --> ex.20f.rs:28:25
   |
28 |     println!("{}", show(Loud { n: 1 }));
   |                    ---- ^^^^^^^^^^^^^ unsatisfied trait bound
   |                    |
   |                    required by a bound introduced by this call
   |
help: the trait `std::fmt::Display` is not implemented for `Loud`
  --> ex.20f.rs:4:1
   |
 4 | struct Loud {
   | ^^^^^^^^^^^
note: required by a bound in `show`
  --> ex.20f.rs:18:12
   |
18 | fn show<T: Display>(x: T) -> String {
   |            ^^^^^^^ required by this bound in `show`

error: aborting due to 3 previous errors

For more information about this error, try `rustc --explain E0277`.
```

**왜 그런가**

| 줄 | 자리 | Rust 의 답 | TS 의 같은 자리 |
|---|---|---|---|
| 15 | 바운드 없는 `T` 를 `format!` 에 | `E0277` — **정의 자리** | ★ **같다** — 1번 3행 `TS2339` |
| 28 | ★★★ `show(Loud { n: 1 })` | `E0277` — **`impl Display` 가 없다** | ★★★ **다르다** — 1번 22행은 **통과한다** |
| 22 | ★★ `fn defaulted<T = i32>` | **금지** — 「not allowed here」 | ★★ **된다** — 4번 24행 |

- ★★★ 28행이 **진짜 차이**다. `struct Loud` 에는 `fmt` 라는 메서드가 **있는데도** 막힌다 —\
  진단이 「the trait `std::fmt::Display` is not implemented for `Loud`」라고 **이름을 짚는다.**\
  **Rust 의 바운드는 명목**이다 — 어딘가에 `impl Display for Loud` 가 **선언돼 있어야** 한다.
- ★★★ TS 는 1번 22행에서 정반대였다. `class Rope` 는 아무것도 `implements` 하지 않았는데 통과했다 —\
  **TS 의 제약은 구조적**이다([**05번 주제**](../05-structural-typing/)).
- ★★★ 15행이 **브리핑 수준의 요약을 뒤집는 자리**다.\
  「Rust 는 정의 자리에서 막고 TS 는 사용 자리에서 막는다」는 **틀렸다** —\
  **둘 다 양쪽에서 막는다.** 몸통은 정의 자리(Rust 15행 ↔ TS 1번 3행),\
  인자는 사용 자리(Rust 28행 ↔ TS 1번 14행)다. **갈리는 축은 자리가 아니라 「모양이냐 이름이냐」다.**
- ★★ 22행 — Rust 는 **함수에 기본 타입 인자를 못 단다.** `struct`·`enum`·`type`·`trait` 에만 허용된다.\
  진단이 `deny(future_incompatible)` 문맥으로 나오는 것은 **옛날에는 받아 줬다**는 뜻이다.
- ★ **Java 는 이 배치에서 안 던졌다** — 이 머신에 `javac` 가 없다.\
  Java 행은 형제 문서(Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번**·**18번**·**19번**)를 근거로 적은 것이고 **이 배치의 실측이 아니다.**

### 7. ★★★ `T` 가 **제약보다 좁을 수 있기** 때문이다

**왜 그런가**

- 3번 8행의 연쇄가 그대로 답이다 — 「'T' could be instantiated with a different subtype of constraint 'Point'」.
- ★★ 호출자가 `Point3`(x·y·z)을 넘겼다면 함수는 `Point3` 을 돌려줘야 한다.\
  그런데 함수가 만든 `{x:0,y:0}` 에는 **`z` 가 없다** — 돌려주면 **호출자가 잃어버린 `z` 를 찾다 터진다.**
- ★★★ 그래서 TS 는 `T` 를 **끝까지 미지수로 둔다.** 읽기는 허용하고 만들기는 막는 **비대칭**이 거기서 나온다.
- ★ 같은 비대칭이 [**17번 주제**](../17-variance-and-parameter-compatibility/)의 변성에도 있다 — **받는 자리와 주는 자리가 반대 방향**이다.

### 8. ★★★ 스프레드의 타입이 **`T & { x: number }`** 이기 때문이다

**왜 그런가**

- 3번 25행의 탐침이 답이다. `{ ...p, x: 0 }` 는 `{ x: number; y: number }` 가 **아니라** `T & { x: number; }` 다.
- ★★ 교차 타입은 `T` 의 **부분 타입**이므로 `T` 자리에 들어간다. `z` 가 있었으면 **`T` 안에 그대로** 들어 있다.
- ★★★ 즉 「**새로 만든 것**」과 「**받은 것에 덧칠한 것**」이 타입 층에서 갈린다.\
  7번의 걱정(잃어버린 `z`)이 스프레드에서는 **원리상 생기지 않는다.**
- ★ 대가는 **얕은 복사**다. 중첩 객체는 원본과 공유된다.

### 9. ★★ 「**몸통에서 멤버를 쓰는가**」로 가른다

**왜 그런가**

| 제약을 건다 | 안 건다 |
|---|---|
| 몸통에서 멤버를 써야 할 때 — 안 걸면 `TS2339`(1번 3행) | `T` 를 **그대로 돌려주기만** 할 때 |
| 호출자의 실수를 **인자 자리에서** 막고 싶을 때 | 아무거나 받아야 할 때 — 그때는 `unknown`([**04번 주제**](../04-any-unknown-never-void/)) |
| 리터럴을 살리고 싶을 때(`T extends string`) | 배열·객체 리터럴까지 살려야 할 때 — **[21](../21-inference-control-const-and-noinfer/)의 `const` 가 맞다** |
| 키 안전한 접근(`K extends keyof O`) | 키가 **동적**일 때 — 2번 15행이 막힌다 |

- ★★ 제약을 좁히면 **받을 수 있는 인자가 줄고**, 넓히면 **몸통에서 쓸 수 있는 멤버가 준다.** 늘 그 사이에서 고른다.

### 10. ★★ `TS2314` 가 사라지고, 대신 **실수가 조용해진다**

**왜 그런가**

- [**19번 주제**](../19-generics-basics/) 3절 21행이 `TS2314`(「requires 1 type argument(s)」)였다.\
  기본값을 두면 **그 진단이 사라진다** — 4번 8행이 그 증거다.
- ★★★ 대가는 [**19번 주제**](../19-generics-basics/) 4절의 「**부분 고정**」이다.\
  `withDefault<string>("가", 1)` 이 문법적으로 통과한 뒤 `B` 가 **기본값으로 굳어** 엉뚱한 자리에서 터진다.
- ★★ 그래서 기본값은 **「대부분의 호출이 한 타입일 때」** 만 둔다. 의견이 갈리는 자리에는 두지 않는다.
- ★ 그리고 기본값도 **제약을 지켜야** 하고(`TS2344`) **앞의 매개변수만** 참조할 수 있다(`TS2744`).

### 11. ★★★ 갈리는 축은 **모양이냐 이름이냐**다

**왜 그런가**

| 언어 | 무엇으로 거나 | 함수에 기본 타입 인자 | 근거 |
|---|---|---|---|
| **TypeScript** | ★ **모양**(structural) — `implements` 불필요 | ★ **된다** | 1번 22행 · 4번 24행 |
| **Rust** | ★ **이름**(nominal) — `impl Trait for T` 가 있어야 | ✗ 「not allowed here」 | 6번 28·22행 |
| **Java** | 이름 — `implements`/`extends` | ✗ 문법 자체가 없다 | ★ 형제 문서(Java 17·18) — **이 배치의 실측 아님** |

- ★★★ **자리(정의 대 사용)는 갈리는 축이 아니다.** TS 도 Rust 도 **몸통은 정의 자리, 인자는 사용 자리**에서 막는다(6번).
- ★★ 구조적 제약의 대가는 **우연히 모양이 맞는 것까지 통과**시키는 것이다.\
  명목 구분이 필요하면 브랜드 타입을 쓴다([**05번 주제**](../05-structural-typing/)) — **이 배치에서는 안 던졌다.**
- ★ Java 에는 **와일드카드**(`? extends`/`? super`)라는 축이 하나 더 있고 TS 에는 **없다** —\
  TS 는 제약과 변성([**17번 주제**](../17-variance-and-parameter-compatibility/))으로 같은 일을 나눠 한다.

### 12. ★★★ 제약은 **스칼라까지**, `const` 는 **배열·객체까지**

**왜 그런가**

| 고장([**19번**](../19-generics-basics/) 2절) | 제약(이 주제) | [**21번**](../21-inference-control-const-and-noinfer/) |
|---|---|---|
| `keep("가")` → `"가"` | 이미 괜찮다 | — |
| `pickMode("auto")` — `T extends string` | ★ **`"auto"` 로 좁힌다** | — |
| `keep(["가","나"])` → `string[]` | ✗ 제약으로는 못 고친다 | ★★★ `<const T>` 가 고친다 |
| `keep({ mode: "auto" })` → `{ mode: string }` | ✗ | ★★★ `<const T>` 가 고친다 |
| 기본값이 엉뚱한 자리에서 추론됨 | ✗ 제약과 무관 | ★★★ `NoInfer<T>` 가 고친다 |

- ★★★ 그러므로 사슬의 역할 분담은 이렇다 —\
  **19 가 고장을 보이고, 20 이 하한을 걸어 스칼라를 좁히고, 21 이 정의 쪽에서 통째로 막는다.**
- ★★ 그리고 21 에는 **이 주제와 싸우는 자리**가 있다 — `const T extends string[]` 처럼\
  **제약이 `readonly` 가 아니면** `const` 가 어떻게 되는지가 거기서 갈린다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 제약 없는 `T` | `--noEmit ex.20a.ts` | exit 1 · **7건** · 3행 `TS2339`(정의 자리) · ★ 22행 `implements` 없이 **통과** |
| `keyof` 제약 | `--noEmit ex.20b.ts` | exit 1 · **7건** · 12행에 **허용 키 목록** · 15행 `string` 변수 **막힘** |
| ★★★ 리터럴 못 만듦 | `--noEmit ex.20c.ts` | exit 1 · **2건** · 8행 `TS2322` + 「different subtype」 · ★ 스프레드는 **통과**(25행 `T & { x: number; }`) |
| 기본 타입 인자 | `--noEmit ex.20d.ts` | exit 1 · **8건** · 17행 `TS2344` · 34행 `TS2744` |
| 재귀 제약 | `--noEmit ex.20e.ts` | exit 1 · **6건** · 27행 `Comparable<1 \| 2>` |
| Rust 대비 | `rustc --edition 2021 --crate-name ex20f ex.20f.rs` | exit 1 · **3건** · `E0277` 둘 + 함수 기본값 **금지** |
| `strict` 대조 | 다섯 파일을 `--strict false` 로 재실행 | ★ `ex.20d.ts` **하나만** 갈림(`strictNullChecks` — 제약과 무관) |
| 반복 실행 | 같은 명령 **5회** | ★★ md5 **동일** — 유니온·`keyof` 순서가 안 흔들렸다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ `keyof` 키 목록의 **사전순** 정렬 — 5회 동일했지만 **관찰이지 보장이 아니다.**
- ★★ `TS2322` 의 연쇄 설명 문구(「could be instantiated with a different subtype of constraint 'Point'」) — **코드가 더 오래 간다.**
- ★★ 스프레드가 `T & { x: number; }` 가 되는 것 — TS 3.2 이후의 규칙이고 **이 판에서 던져 확인했다.**
- ★★ `rustc` 1.92.0 의 캐럿·`help:`·`note:` 줄 배치와 **`--explain E0277`** 안내 줄.
- 진단 **문구** 전문 — `TS2339`·`TS2344`·`TS2744`·`E0277` 이라는 **코드**가 더 오래 간다.

**안 돌려 본 것**

- **Java 로 같은 것을 던지는 것** — 이 머신에 **`javac` 가 없다.** 형제 문서가 근거다(Java 17·18·19).
- **와일드카드에 해당하는 관용구 비교** — **안 던졌다.**
- **브랜드 타입으로 명목 구분 흉내 내기** — **안 던졌다.** [**05번 주제**](../05-structural-typing/).
- **재귀 제약의 깊이 한계** — **안 쟀다.** 목록의 **25번 주제**·목록의 **45번 주제**.
- **제약이 검사 시간에 주는 영향** — **재지 않았고 수치를 적지 않았다.**
