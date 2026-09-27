# ts/syntax/20 — 제네릭 제약과 기본 타입 인자 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ 이 주제의 급소는 「**제약이 있어도 그 타입의 값을 안에서 못 만든다**」이고,
> 그 이유가 진단의 **연쇄 설명 줄 한 줄에 적혀 있다.**
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · `rustc` **1.92.0**. 옵션은 **배너에 적힌 것만** 줬다.
>
> ★★★ **추론된 타입을 눈으로 보는 법** — 블록에 `const probe: null = …` 이 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★ 단 **3번만은 다르다** — 거기서는 `TS2322` 가 **진짜 에러**이고 그것이 문제의 핵심이다.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 제약이 없으면 몸통에서 무엇을 할 수 있나 (예측)

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

- 3행은 통과하는가? 무슨 코드이고 **어느 자리**(정의 대 사용)에 나는가?
- 12행 `lenOf({ length: 3, extra: true })` 는 통과하는가?
- 22행 `class Rope` 는 아무것도 `implements` 하지 않았다. 통과하는가?

### 2. 키가 값 타입을 정한다 (예측)

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

- 8·9·10행의 탐침은 각각 무엇을 뱉는가?
- 12행의 진단에 **무엇이 찍히는가**?
- 15행은 `string` 타입 변수를 키로 준다. 통과하는가?

### 3. 제약 타입의 값을 안에서 만들면 (예측)

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

- 진단은 **몇 건**이고 어느 줄인가?
- 8행의 연쇄 설명 줄은 **무엇이라고 말하는가**?
- 12·16·20행 중 **막히지 않는 것**은 어느 것이고 왜인가? 25행 탐침이 그 답을 준다.

### 4. 기본 타입 인자의 규칙 (예측)

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

- 17행 `interface BadDefault<T extends number = string>` 은 통과하는가?
- 24행 `makeBox()` 와 25행 `makeBox("가")` 의 답이 같은가?
- 34행 `interface Backwards<A = B, B = number>` 는 통과하는가?

### 5. 재귀적 제약 (예측)

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

- 8·9행은 통과하는가?
- 11행 `treeOf({ a: 1 })` 의 진단은 무엇을 말하는가?
- 27행 `maxOf(1, 2)` 의 진단에 찍히는 타입은 무엇인가?

### 6. Rust 는 어디서 막나 (예측)

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

- 에러는 **몇 건**인가?
- `struct Loud` 에는 `fmt` 메서드가 있다. `show(Loud { n: 1 })` 은 통과하는가?
- `fn defaulted<T = i32>` 는 통과하는가? TS 에서는 어떤가?

### 7. 왜 제약 타입의 값을 못 만드나 (왜)

- 3번 8행의 연쇄 설명을 근거로 **한 문장**으로 댈 수 있는가?

### 8. 왜 스프레드는 통과하나 (왜)

- 3번 25행의 탐침을 근거로 설명할 수 있는가?

### 9. 제약을 걸 자리와 안 걸 자리 (경계)

- 언제 제약을 걸고 언제 `unknown` 으로 받는가?

### 10. 기본 타입 인자를 둘 자리와 안 둘 자리 (경계)

- 기본값을 두면 [**19번 주제**](../19-generics-basics/)의 어떤 진단이 사라지는가? 그 대가는 무엇인가?

### 11. Rust·Java 와 잇기 (연결)

- 「바운드가 **모양**으로 걸리나 **이름**으로 걸리나」를 세 언어로 갈라 말할 수 있는가?

### 12. 19·21 로 잇기 (연결)

- [**19번 주제**](../19-generics-basics/) 2절의 고장을 이 주제의 제약이 **어디까지** 고치는가? 남은 것은 [**21번 주제**](../21-inference-control-const-and-noinfer/)의 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
