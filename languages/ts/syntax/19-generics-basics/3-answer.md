# ts/syntax/19 — 제네릭 기본 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·`.d.ts` 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 6번의 `tsc` 는 **진단이 0줄인 것이 결론**이다. 그 블록도 **명령과 종료 코드까지** 캡처했다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`3` · `number` · `string | number`** — 명시가 추론을 이긴다

**출력**

```ts
// ex.19a.ts
// 타입 매개변수는 호출마다 채워진다 -- 추론과 명시 둘 다, 그리고 any 와 무엇이 다른가
function identity<T>(x: T): T {
    return x;
}

const inferred = identity(3);
const explicit = identity<number>(3);
const widened = identity<string | number>(3);
const p1: null = inferred;
const p2: null = explicit;
const p3: null = widened;

function anyIdentity(x: any): any {
    return x;
}
const p4: null = anyIdentity(3);

function pair<A, B>(a: A, b: B): [A, B] {
    return [a, b];
}
const p5: null = pair("가", 1);

function firstOf<T>(xs: T[]): T {
    return xs[0]!;
}
const p6: null = firstOf([1, "가"]);

identity<number>("가");
console.log(p1, p2, p3, p4, p5, p6);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.19a.ts (tsc exit=1) =====
ex.19a.ts(9,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.19a.ts(10,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.19a.ts(11,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.19a.ts(21,7): error TS2322: Type '[string, number]' is not assignable to type 'null'.
ex.19a.ts(26,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.19a.ts(28,18): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 9 | `identity(3)` — 추론 | **`3`** |
| 10 | `identity<number>(3)` — 명시 | **`number`** |
| 11 | `identity<string \| number>(3)` — 명시 | **`string \| number`** |
| 16 | ★★★ `anyIdentity(3)` | **진단 없음** — `any` 는 `null` 에도 들어간다 |
| 21 | `pair("가", 1)` | **`[string, number]`** — ★ `"가"` 가 아니다 |
| 26 | `firstOf([1, "가"])` | `string \| number` — 원소가 **유니온**으로 합쳐진다 |
| 28 | `identity<number>("가")` | `TS2345` — **명시한 인자가 검사 기준**이 된다 |

- ★★★ 9·10·11행이 이 문항의 전부다. **인자는 셋 다 `3`** 인데 반환 타입이 다르다 — 꺾쇠를 적으면 **그것이 답**이고,\
  인자는 **검사만** 받는다(28행이 그 증거다).
- ★★★ 16행에 진단이 없는 것이 `any` 의 얼굴이다. **`any` 는 아무 데나 들어가므로 탐침을 통과한다** —\
  즉 `any` 를 반환하는 함수를 쓰면 **그 뒤로 검사가 꺼진다**([**04번 주제**](../04-any-unknown-never-void/)).
- ★★ 21행이 2번의 예고다. `pair("가", 1)` 이 `["가", 1]` 이 아니라 **`[string, number]`** 다 —\
  **튜플 자리에서 리터럴이 넓어졌다.**

### 2. ★★★ **스칼라는 `"가"`, 배열은 `string[]`** — 넓어지는 것은 **속**이다

**출력**

```ts
// ex.19b.ts
// 추론은 리터럴로 좁혀지지 않는다 -- 21 의 const 타입 매개변수가 고칠 고장을 여기서 먼저 본다
function firstOf<T>(xs: T[]): T {
    return xs[0]!;
}
const p1: null = firstOf(["가", "나"]);

function keep<T>(x: T): T {
    return x;
}
const p2: null = keep("가");
const p3: null = keep(["가", "나"]);
const p4: null = keep({ mode: "auto" });

const asConst = keep(["가", "나"] as const);
const p5: null = asConst;

let mutable = "가";
const p6: null = keep(mutable);

function pickMode<T extends string>(mode: T): T {
    return mode;
}
const p7: null = pickMode("auto");
console.log(p1, p2, p3, p4, p5, p6, p7);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.19b.ts (tsc exit=1) =====
ex.19b.ts(5,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.19b.ts(10,7): error TS2322: Type '"가"' is not assignable to type 'null'.
ex.19b.ts(11,7): error TS2322: Type 'string[]' is not assignable to type 'null'.
ex.19b.ts(12,7): error TS2322: Type '{ mode: string; }' is not assignable to type 'null'.
ex.19b.ts(15,7): error TS2322: Type 'readonly ["가", "나"]' is not assignable to type 'null'.
ex.19b.ts(18,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.19b.ts(23,7): error TS2322: Type '"auto"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 | 무엇이 벌어졌나 |
|---|---|---|---|
| 5 | `firstOf(["가","나"])` | `string` | 원소 타입이 넓어진 뒤 뽑힘 |
| 10 | ★★★ `keep("가")` | **`"가"`** | 스칼라 리터럴은 **살아남는다** |
| 11 | ★★★ `keep(["가","나"])` | **`string[]`** | 배열의 **속**이 넓어진다 |
| 12 | `keep({ mode: "auto" })` | `{ mode: string; }` | 객체의 **속**도 |
| 15 | `keep([…] as const)` | `readonly ["가", "나"]` | ★ **호출자**가 고쳤다 |
| 18 | `keep(mutable)` — `let` 변수 | `string` | 변수에 담길 때 이미 넓어졌다 |
| 23 | ★★★ `pickMode("auto")` — `T extends string` | **`"auto"`** | ★ **제약**이 고쳤다 |

- ★★★ 10행과 11행이 이 문항의 핵심이고, **브리핑 수준의 요약이 틀리는 자리**다.\
  「제네릭 추론은 리터럴을 안 지킨다」는 **반만 맞다** — **스칼라는 지킨다.**\
  넓어지는 것은 **배열·객체 리터럴의 속**이다.
- ★★ 15행과 23행은 **서로 다른 고침**이다. `as const` 는 **호출자가 매번** 적어야 하고([**11번 주제**](../11-literal-types-and-as-const/)),\
  제약은 **정의자가 한 번** 적는다([**20번 주제**](../20-generic-constraints-and-defaults/)).
- ★★★ **정의자가 배열·객체까지 통째로 고치는 길**이 [**21번 주제**](../21-inference-control-const-and-noinfer/)의 `const` 타입 매개변수다.\
  그 주제의 1절이 이 블록의 11·12행을 **그대로 다시 던져** 고친다.
- ★ 18행이 조용한 함정이다 — **변수에 한 번 담으면** `as const` 를 쓸 기회조차 사라진다.

### 3. ★★★ **`3` · `string` · `true`** — 채워지는 **시점**이 다르다

**출력**

```ts
// ex.19c.ts
// 제네릭 함수 타입과 제네릭 인터페이스 -- 타입 매개변수가 어디에 붙느냐가 다르다
export interface GenericFn {
    <T>(x: T): T;
}

export interface FnOfT<T> {
    (x: T): T;
}

export type ArrowGeneric = <T>(x: T) => T;

export const g1: GenericFn = (x) => x;
export const g2: FnOfT<string> = (x) => x;
export const g3: ArrowGeneric = (x) => x;

const p1: null = g1(3);
const p2: null = g2("가");
const p3: null = g3(true);

export const bad: FnOfT<string> = (x: number) => x;
export declare const notFilled: FnOfT;
console.log(p1, p2, p3);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.19c.ts (tsc exit=1) =====
ex.19c.ts(16,7): error TS2322: Type '3' is not assignable to type 'null'.
ex.19c.ts(17,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.19c.ts(18,7): error TS2322: Type 'true' is not assignable to type 'null'.
ex.19c.ts(20,14): error TS2322: Type '(x: number) => number' is not assignable to type 'FnOfT<string>'.
  Types of parameters 'x' and 'x' are incompatible.
    Type 'string' is not assignable to type 'number'.
ex.19c.ts(21,33): error TS2314: Generic type 'FnOfT<T>' requires 1 type argument(s).
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 16 | `g1(3)` — `GenericFn`(호출 시그니처에 `<T>`) | **`3`** — 호출마다 채워진다 |
| 17 | `g2("가")` — `FnOfT<string>`(이름에 `<T>`) | **`string`** — 타입 쓸 때 이미 고정됐다 |
| 18 | `g3(true)` — `ArrowGeneric` | **`true`** — `GenericFn` 과 같은 뜻 |
| 20 | `FnOfT<string>` 자리에 `(x: number) => number` | `TS2322` — 연쇄가 **매개변수 쪽**을 짚는다 |
| 21 | ★★★ `FnOfT` 를 인자 없이 | **`TS2314`** — 「requires 1 type argument(s)」 |

- ★★★ 16·17·18행의 답이 다른 이유는 **꺾쇠를 어디에 달았느냐** 하나다.\
  호출 시그니처에 달면 **부를 때** 채워지고, 이름에 달면 **타입을 쓸 때** 채워진다.
- ★★ 그래서 17행은 `"가"` 가 아니라 **`string`** 이다 — `FnOfT<string>` 로 이미 못 박혔으므로 추론할 것이 없다.
- ★★★ 21행 `TS2314` 가 이름에 단 `<T>` 의 대가다 — **쓰는 자리마다 인자를 적어야** 한다.\
  덜어 주는 장치가 **기본 타입 인자**이고 [**20번 주제**](../20-generic-constraints-and-defaults/)에서 본다.
- ★ 20행의 연쇄가 「Types of parameters 'x' and 'x' are incompatible.」인 것은 **매개변수가 반공변**이기 때문이다([**17번 주제**](../17-variance-and-parameter-compatibility/)).

### 4. ★★★ **`TS2558`** — 전부 아니면 전무다

**출력**

```ts
// ex.19d.ts
// 타입 인자는 전부 적거나 하나도 안 적거나다 -- 부분 추론은 없다
function pair<A, B>(a: A, b: B): [A, B] {
    return [a, b];
}

const all = pair<string, number>("가", 1);
const none = pair("가", 1);
const partial = pair<string>("가", 1);

function withDefault<A, B = boolean>(a: A, b: B): [A, B] {
    return [a, b];
}
const oneOfTwo = withDefault<string>("가", 1);
const p1: null = oneOfTwo;
console.log(all, none, partial, p1);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.19d.ts (tsc exit=1) =====
ex.19d.ts(8,22): error TS2558: Expected 2 type arguments, but got 1.
ex.19d.ts(13,43): error TS2345: Argument of type 'number' is not assignable to parameter of type 'boolean'.
ex.19d.ts(14,7): error TS2322: Type '[string, boolean]' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 6 | `pair<string, number>("가", 1)` | 통과 — **전부 적었다** |
| 7 | `pair("가", 1)` | 통과 — **하나도 안 적었다** |
| 8 | ★★★ `pair<string>("가", 1)` | **`TS2558`** — 「Expected 2 type arguments, but got 1.」 |
| 13 | `withDefault<string>("가", 1)` | `TS2345` — `B` 가 **`boolean` 으로 고정**됐다 |
| 14 | 그 결과 | `[string, boolean]` |

- ★★★ 8행이 규칙이다. **하나를 적는 순간 나머지도 전부 적어야** 한다.
- ★★★ 13·14행이 **빠져나가는 길이자 함정**이다. `B = boolean` 이라는 **기본 타입 인자**가 있으면\
  `withDefault<string>` 이 문법적으로 통과한다 — 그런데 `B` 는 **추론되지 않고 기본값으로 고정**된다.\
  그래서 `1` 을 넘긴 13행이 `TS2345` 이고 결과가 `[string, boolean]` 이다.
- ★★ 즉 기본값은 「**부분 추론**」이 아니라 「**부분 고정**」이다. 이 구별을 놓치면 20 에서 기본값을 오용한다.

### 5. ★★ 진단 **5건** — `static` 에는 `T` 를 못 쓴다

**출력**

```ts
// ex.19e.ts
// 제네릭 클래스 -- 타입 인자는 인스턴스마다 정해지고 static 자리에는 못 온다
export class Box<T> {
    constructor(public value: T) {}

    map<U>(f: (x: T) => U): Box<U> {
        return new Box(f(this.value));
    }

    static empty: T;
}

const b1 = new Box("가");
const b2 = new Box<number>(1);
const b3 = b1.map((s) => s.length);
const p1: null = b1;
const p2: null = b2;
const p3: null = b3;

const wrong = new Box<number>("가");
console.log(p1, p2, p3, wrong);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.19e.ts (tsc exit=1) =====
ex.19e.ts(9,19): error TS2302: Static members cannot reference class type parameters.
ex.19e.ts(15,7): error TS2322: Type 'Box<string>' is not assignable to type 'null'.
ex.19e.ts(16,7): error TS2322: Type 'Box<number>' is not assignable to type 'null'.
ex.19e.ts(17,7): error TS2322: Type 'Box<number>' is not assignable to type 'null'.
ex.19e.ts(19,31): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
```

**왜 그런가**

| 줄 | 자리 | 결과 |
|---|---|---|
| 9 | ★★★ `static empty: T;` | **`TS2302`** — 「Static members cannot reference class type parameters.」 |
| 15 | `new Box("가")` | `Box<string>` — 생성자 인자에서 추론 |
| 16 | `new Box<number>(1)` | `Box<number>` — 명시 |
| 17 | `b1.map((s) => s.length)` | **`Box<number>`** — 메서드의 `<U>` 가 따로 채워진다 |
| 19 | `new Box<number>("가")` | `TS2345` — 명시한 인자가 검사 기준 |

- ★★★ 9행의 이유는 한 문장으로 선다 — **`T` 는 인스턴스마다 정해지는데 `static` 은 클래스에 하나뿐**이다.\
  `Box<string>.empty` 와 `Box<number>.empty` 가 같은 칸을 가리키게 되므로 채울 값이 없다.
- ★★ 17행에서 `s` 가 `string` 인 것은 **클래스의 `T` 가 이미 `string` 으로 채워져** 있기 때문이다.\
  그 위에서 메서드의 `<U>` 가 **`s.length` 의 타입에서** `number` 로 따로 추론된다 — **두 층이 겹쳐 있다.**
- ★ 필요하면 **정적 메서드에 따로 `<U>` 를 단다** — 정적 메서드는 자기 타입 매개변수를 가질 수 있다. 이 배치에서는 **안 던졌다.**

### 6. ★★★ 진단 **0줄 · exit 0** — 생성자가 **같다**(`true`)

**출력**

```ts
// ex.19f.ts
// 런타임에 타입 인자는 없다 -- 방출물에 한 글자도 안 남는다
class Box<T> {
    constructor(public value: T) {}
}

function firstOf<T>(xs: T[]): T {
    return xs[0]!;
}

const sBox = new Box<string>("가");
const nBox = new Box<number>(1);
console.log("1) 두 Box 의 생성자가 같은가 :", sBox.constructor === nBox.constructor);
console.log("2) Box 의 이름               :", Box.name);
console.log("3) firstOf 의 매개변수 개수  :", firstOf.length);
console.log("4) firstOf 를 문자열로       :", firstOf.toString());
console.log("5) 인스턴스에 타입 흔적이 있나:", Object.keys(sBox).join(","));
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e19f ex.19f.ts (tsc exit=0) =====
===== 방출된 ex.19f.js =====
"use strict";
// 런타임에 타입 인자는 없다 -- 방출물에 한 글자도 안 남는다
class Box {
    value;
    constructor(value) {
        this.value = value;
    }
}
function firstOf(xs) {
    return xs[0];
}
const sBox = new Box("가");
const nBox = new Box(1);
console.log("1) 두 Box 의 생성자가 같은가 :", sBox.constructor === nBox.constructor);
console.log("2) Box 의 이름               :", Box.name);
console.log("3) firstOf 의 매개변수 개수  :", firstOf.length);
console.log("4) firstOf 를 문자열로       :", firstOf.toString());
console.log("5) 인스턴스에 타입 흔적이 있나:", Object.keys(sBox).join(","));
```

```text
===== node e19f/ex.19f.js (node exit=0) =====
1) 두 Box 의 생성자가 같은가 : true
2) Box 의 이름               : Box
3) firstOf 의 매개변수 개수  : 1
4) firstOf 를 문자열로       : function firstOf(xs) {
    return xs[0];
}
5) 인스턴스에 타입 흔적이 있나: value
```

**왜 그런가**

| 실행 출력 | 값 | 무엇을 증명하나 |
|---|---|---|
| 1 | ★★★ `true` | `Box<string>` 과 `Box<number>` 의 **생성자가 같은 객체**다 |
| 2 | `Box` | 런타임의 이름에 타입 인자가 **안 붙는다** |
| 3 | `1` | `firstOf` 의 인자는 **하나**다 |
| 4 | ★★ `function firstOf(xs) { … }` | 소스 글자에 **꺾쇠가 없다** |
| 5 | `value` | 인스턴스에 **타입 흔적 필드가 없다** |

- ★★★ `tsc` 종료 코드가 **`0`** 이고 진단이 **0줄**이다. 방출된 `.js` 에 `<T>` 가 **한 글자도** 없다.
- ★★★ 1번 줄이 결정적이다. **런타임에는 `Box` 라는 클래스 하나뿐**이고 `Box<string>`·`Box<number>` 라는 것은 **존재하지 않는다.**\
  그래서 `new T()`·`x instanceof T` 를 **쓸 수 없다.**
- ★★ 4번 줄은 같은 사실을 **엔진이 들고 있는 소스 글자**로 보여 준다 — 「지워졌다」가 아니라 **애초에 안 실렸다.**
- ★★★ 세 언어 대비 —

| 언어 | 런타임에 `T` 가 | 근거 |
|---|---|---|
| **TypeScript** | ★ **없다** — 방출물이 곧 JS 다 | 이 절의 실측 |
| **Java** | 소거된다 — 바이트코드에 **시그니처만** 남는다 | Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번** |
| **Kotlin** | ★★ `inline` + `reified` 면 **남는다** | Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **12번** |

- ★★★ **Kotlin 만 뚫는 길이 있다** — 호출 자리에 코드를 펼쳐 `T` 를 실제 클래스로 박는다.\
  **TS 에는 그런 장치가 없다.** 필요하면 값을 하나 더 받는 수밖에 없다.

### 7. ★★ 추론 **순서가 정의되지 않기** 때문이다

**왜 그런가**

- 타입 매개변수끼리 서로를 제약할 수 있다(`<A, B extends A>`). 그러면 「적힌 것부터 채우고 나머지를 푼다」가\
  **일반적으로 잘 정의되지 않는다** — 어느 것부터 푸느냐에 따라 답이 갈린다.
- ★★ TS 는 그 모호함을 피해 **전부 아니면 전무**로 못 박았다(`TS2558`).
- ★★ 대신 **기본 타입 인자**라는 우회로를 뒀다 — 4번 13·14행. 다만 그것은 **추론이 아니라 고정**이다.
- ★ 「뒤쪽만 추론시키고 싶다」를 진짜로 푸는 길은 **함수를 둘로 쪼개 커링**하는 것이다. 이 배치에서는 **안 던졌다.**

### 8. ★★★ **넓히기의 기준이 「앞으로 바뀔 수 있는가」** 이기 때문이다

**왜 그런가**

- 리터럴 타입의 **넓히기(widening)** 는 그 값이 **변경 가능한 자리**에 있는지를 본다.
- ★★ 배열·객체 리터럴은 **원소·속성을 나중에 바꿀 수 있는 자리**이므로 속이 넓어진다 —\
  `["가","나"]` 에 `push("다")` 를 할 수 있으니 `readonly ["가","나"]` 로 두면 거짓이 된다.
- ★★ 스칼라 인자는 **그 자리에서 끝나므로** 넓힐 이유가 없다 — 그래서 `keep("가")` 가 `"가"` 다.
- ★★★ 그러므로 고치는 방법도 **「변경 불가」를 선언하는 것**이다 —\
  `as const` 는 **호출자가**([**11번 주제**](../11-literal-types-and-as-const/)), `const` 타입 매개변수는 **정의자가** 선언한다([**21번 주제**](../21-inference-control-const-and-noinfer/)).
- ★ 2번 18행이 그 기준의 다른 얼굴이다 — `let` 변수는 **바뀔 수 있으므로** 담기는 순간 넓어진다.

### 9. ★★★ `any` 는 **줄을 끊고** 제네릭은 **줄을 잇는다**

**왜 그런가**

- 1번 16행이 근거다. `anyIdentity(3)` 은 **탐침조차 통과**한다 — `any` 는 `null` 에도 들어간다.
- ★★ 즉 `any` 를 돌려받는 순간 **그 값에 대한 검사가 전부 꺼진다.** 제네릭은 반대로 **호출 지점의 타입을 그대로 들고 나온다.**
- ★★★ 「**타입을 모르겠으면 `T`, 진짜 모르면 `unknown`**」이다. `unknown` 은 **받을 수는 있지만 쓰려면 좁혀야** 하므로\
  검사를 끄지 않는다([**04번 주제**](../04-any-unknown-never-void/)).
- ★ `any` 가 정당한 자리는 **점진 도입 중인 경계**뿐이다.

### 10. ★★ **타입 매개변수가 두 자리 이상에 나오는가**로 가른다

**왜 그런가**

| 제네릭을 쓴다 | 안 쓴다 |
|---|---|
| 입력과 출력이 이어질 때(`(x: T) => T`) | ★★ `T` 가 **한 자리에만** 나올 때 — 그 자리에 **그냥 그 타입을 적어라** |
| 컨테이너·컬렉션 | 늘 한 타입만 쓰는 자리 |
| 여러 자리를 묶어야 할 때(`pair<A, B>`) | 런타임 동작이 타입마다 달라야 할 때 — **`T` 로는 못 한다**(6번) |
| 리터럴 보존이 필요할 때 — **제약이나 [21](../21-inference-control-const-and-noinfer/)과 함께** | 제약 없이 리터럴을 기대할 때 — **조용히 넓어진다**(2번) |

- ★★ 한 자리에만 나오는 `<T>` 는 **아무것도 안 잇는다.** `function f<T>(x: T): void` 는 `function f(x: unknown): void` 와 같다.

### 11. ★★★ 셋 다 **지우는데**, 하나만 뚫는 길이 있다

**왜 그런가**

| 언어 | 무엇이 남나 | 뚫는 길 |
|---|---|---|
| **TypeScript** | ★ **아무것도** — 방출물이 JS 다 | **없다.** 값을 하나 더 받는 수밖에 |
| **Java** | 바이트코드의 **시그니처** — 리플렉션으로 일부 읽힌다 | `Class<T>` 토큰을 넘기는 관용구 |
| **Kotlin** | ★★ `inline fun <reified T>` 면 **실제 클래스** | 호출 자리에 **코드를 펼친다** |

- ★★★ Kotlin 의 길이 통하는 이유는 **인라인**이다 — 함수 몸통이 호출 자리에 복사되므로 그 자리의 `T` 가 **상수처럼 박힌다.**\
  TS 에는 인라인이 없고, 있어도 **박을 클래스 객체 자체가 없다.**
- ★★ Java 와 TS 는 「지운다」가 같고 **지우는 방식**이 다르다 — Java 는 **남길 자리(바이트코드)가 있는데 안 남기는 것**이고,\
  TS 는 **남길 자리 자체가 없다.**
- ★ 그래서 TS 의 제네릭은 **처음부터 끝까지 검사 전용**이다.

### 12. ★★★ 20 은 **좁히고**, 21 은 **막는다**

**왜 그런가**

| 주제 | 2번의 고장에 무엇을 하나 | 근거 줄 |
|---|---|---|
| 이 주제(19) | 고장을 **전시**한다 | 11·12행 — `string[]` · `{ mode: string; }` |
| [**20번**](../20-generic-constraints-and-defaults/) | ★ `T extends string` 으로 **스칼라를 좁힌다** | 2번 23행 — `"auto"` |
| [**21번**](../21-inference-control-const-and-noinfer/) | ★★★ `<const T>` 로 **배열·객체까지** 좁힌다 | 21 의 1절이 11·12행을 그대로 다시 던진다 |
| [**21번**](../21-inference-control-const-and-noinfer/) | ★★★ `NoInfer<T>` 로 **추론 자리를 죽인다** | 19 에는 그 고장이 아직 안 나온다 |

- ★★★ **19 → 20 → 21 은 한 사슬**이고 **21 이 급소**다 — 「언제 추론을 막나」가 거기서 답해진다.
- ★★ 순서를 지켜 읽어라. 20 의 **제약**을 모르면 21 의 `const T extends …` 가 무엇과 싸우는지 안 보인다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 추론 대 명시 | `--noEmit ex.19a.ts` | exit 1 · **6건** · `3` · `number` · `string \| number` |
| 넓어지는 자리 | `--noEmit ex.19b.ts` | exit 1 · **7건** · ★ `keep("가")` = `"가"` · `keep([…])` = `string[]` |
| 제네릭 인터페이스 | `--noEmit ex.19c.ts` | exit 1 · **5건** · 21행 `TS2314` |
| 부분 추론 | `--noEmit ex.19d.ts` | exit 1 · **3건** · 8행 `TS2558` |
| 제네릭 클래스 | `--noEmit ex.19e.ts` | exit 1 · **5건** · 9행 `TS2302` |
| 방출과 실행 | `tsc --outDir ex.19f.ts` + `node` | ★ **tsc exit 0 · 진단 0줄** · 생성자 대조 **`true`** |
| `.d.ts` 창 | `--declaration --emitDeclarationOnly ex.19g.ts` | ★ **exit 0** · ★★ `fromScalar` 가 **`"가"`** |
| `strict` 대조 | 다섯 파일을 `--strict false` 로 재실행 | ★★ **전부 글자 하나까지 같다** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ `.d.ts` 방출기가 `const` 초기자의 비ASCII 를 **`"가"`** 로 이스케이프하는 것 — 같은 파일의 `readonly ["가","나"]` 는 **안 한다.**
- ★★ 진단 **문구** 전문 — `TS2558`·`TS2314`·`TS2302`·`TS2345` 라는 **코드**가 더 오래 간다.
- ★★ 유니온 원소의 **순서**(`string | number`) — 5회 재실행에서 같았지만 **관찰이지 보장이 아니다.**
- `.d.ts` 의 들여쓰기 4칸·줄 순서 — 방출기의 형식이다.
- 방출된 `.js` 의 클래스 필드 표기(`value;`) — `-t es2022` 에 달렸다.

**안 돌려 본 것**

- **제네릭 오버로드** — 오버로드 시그니처에 `<T>` 를 다는 꼴은 **안 던졌다.** [**16번 주제**](../16-function-types-and-overloads/).
- **정적 메서드의 자체 타입 매개변수** — **안 던졌다.**
- **커링으로 부분 추론을 흉내 내는 관용구** — **안 던졌다.**
- **소거를 뚫는 우회로 셋**(생성자 토큰·타입 술어·판별 유니온) — **안 던졌다.**
- **타입 매개변수 개수가 검사 시간에 주는 영향** — **재지 않았고 수치를 적지 않았다.**
