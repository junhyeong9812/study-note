# ts/syntax/05 — 구조적 타이핑 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출 전문·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ **이 주제에서는 「진단 목록에 없는 줄」이 근거다.** 그래서 소스 전문을 같은 자리에 실었다 — 통과한 줄을 직접 세어 보라.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 진단 **1건**(22행) — 나머지 **네 대입이 전부 통과**한다

**출력**

```ts
// ex.05a.ts
// 이름이 다른 셋이 서로 오가는지 본다
interface Point {
    x: number;
    y: number;
}
interface Vector {
    x: number;
    y: number;
}
class Coord {
    constructor(public x: number, public y: number) {}
}
type Triple = { x: number; y: number; z: number };

const p: Point = { x: 1, y: 2 };
const v: Vector = p;
const c: Coord = p;
const backToPoint: Point = new Coord(1, 2);

const triple: Triple = { x: 1, y: 2, z: 3 };
const widen: Point = triple;
const narrow: Triple = p;
console.log(v, c, backToPoint, widen, narrow);
```

```text
===== tsc --pretty false --noEmit ex.05a.ts (tsc exit=1) =====
ex.05a.ts(22,7): error TS2741: Property 'z' is missing in type 'Point' but required in type 'Triple'.
```

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| `const v: Vector = p` | 이름이 다른 두 `interface` | **통과** — 모양이 같다 |
| `const c: Coord = p` | 객체 리터럴에서 온 값 → **클래스 타입** | **통과** — `new` 로 만든 것이 아니어도 된다 |
| `const backToPoint: Point = new Coord(1,2)` | 클래스 인스턴스 → `interface` | **통과** |
| `const widen: Point = triple` | 프로퍼티가 **더 많은** 쪽 → 적은 쪽 | **통과** |
| `const narrow: Triple = p` | **모자란** 쪽 → 많은 쪽 | **TS2741** — 「Property 'z' is missing」 |

- ★★ 「이름을 지어 선언했으니 그 이름으로 만든 것만 들어온다」가 **틀렸다.** 체크리스트만 맞으면 된다.
- ★★ `Coord` 는 `class` 인데도 **객체 리터럴이 들어갔다.** 클래스에 `private`/`#` 멤버가 **없기 때문**이다(3번이 그 대비다).
- 경계는 **한 방향**이다 — 많은 쪽 → 적은 쪽은 되고, 적은 쪽 → 많은 쪽은 안 된다.

### 2. ★★★ 진단 **2건** — 통과하는 줄이 **다섯**이다

**출력**

```ts
// ex.05b.ts
// 초과 프로퍼티 검사 — 리터럴을 직접 넘길 때와 변수를 거칠 때
interface Point {
    x: number;
    y: number;
}
function take(pt: Point) {
    return pt.x;
}

const viaVar = { x: 1, y: 2, z: 3 };
const ok1: Point = viaVar;
take(viaVar);

const bad1: Point = { x: 1, y: 2, z: 3 };
take({ x: 1, y: 2, z: 3 });

const spread: Point = { ...viaVar };
const asserted: Point = { x: 1, y: 2, z: 3 } as Point;
const viaIndex: Point & Record<string, unknown> = { x: 1, y: 2, z: 3 };
console.log(ok1, bad1, spread, asserted, viaIndex);
```

```text
===== tsc --pretty false --noEmit ex.05b.ts (tsc exit=1) =====
ex.05b.ts(14,35): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
ex.05b.ts(15,20): error TS2353: Object literal may only specify known properties, and 'z' does not exist in type 'Point'.
```

**왜 그런가**

| 줄 | 형태 | 결과 |
|---|---|---|
| `const ok1: Point = viaVar` | **변수**를 넘긴다 | **통과** |
| `take(viaVar)` | **변수**를 넘긴다 | **통과** |
| `const bad1: Point = { …, z: 3 }` | **리터럴을 직접** | **TS2353** |
| `take({ …, z: 3 })` | **리터럴을 직접** | **TS2353** |
| `const spread: Point = { ...viaVar }` | 스프레드로 만든 리터럴 | **통과** |
| `const asserted: Point = { … } as Point` | 단언 | **통과** |
| `const viaIndex: Point & Record<string, unknown> = { … }` | 인덱스 시그니처 | **통과** |

- ★★★ **값은 같은데 문법 형태로 갈린다.** `{ x: 1, y: 2, z: 3 }` 이 변수를 거치면 통과하고 직접 놓으면 `TS2353` 이다.
- 왜 그런가 — **리터럴을 직접 적었다는 것은 「이 자리에 맞추려고 방금 쓴 것」이라는 뜻**이다. 거기 오타가 있으면 잡아 주는 게 맞다.\
  이미 있는 변수는 다른 데서도 쓰이므로 여분이 정상일 수 있다.
- ★★ 그래서 **빠져나가는 길이 넷**이다 — 변수 · 스프레드 · 단언 · 인덱스 시그니처.

### 3. ★★★ 진단 **3건** — 통과하는 것은 **`fromC`** 하나다

**출력**

```ts
// ex.05c.ts
// private 멤버 하나가 구조적 타이핑을 명목 타이핑으로 바꾼다
class A {
    private secret = 1;
    constructor(public x: number) {}
}
class B {
    private secret = 1;
    constructor(public x: number) {}
}
class C extends A {}

const fromB: A = new B(1);
const fromLiteral: A = { x: 1, secret: 1 };
const fromC: A = new C(1);

class D {
    #hidden = 1;
    constructor(public x: number) {}
}
class E {
    #hidden = 1;
    constructor(public x: number) {}
}
const fromE: D = new E(1);
console.log(fromB, fromLiteral, fromC, fromE);
```

```text
===== tsc --pretty false --noEmit ex.05c.ts (tsc exit=1) =====
ex.05c.ts(12,7): error TS2322: Type 'B' is not assignable to type 'A'.
  Types have separate declarations of a private property 'secret'.
ex.05c.ts(13,7): error TS2322: Type '{ x: number; secret: number; }' is not assignable to type 'A'.
  Property 'secret' is private in type 'A' but not in type '{ x: number; secret: number; }'.
ex.05c.ts(24,7): error TS2322: Type 'E' is not assignable to type 'D'.
  Property '#hidden' in type 'E' refers to a different member that cannot be accessed from within type 'D'.
```

**왜 그런가**

| 줄 | 결과 | 들여쓴 이유 줄 |
|---|---|---|
| `const fromB: A = new B(1)` | **TS2322** | 「Types have separate declarations of a private property 'secret'.」 |
| `const fromLiteral: A = { x: 1, secret: 1 }` | **TS2322** | 「Property 'secret' is private in type 'A' but not in type '{ x: number; secret: number; }'.」 |
| `const fromC: A = new C(1)` | **통과** | — `class C extends A` 라 **같은 선언**을 물려받았다 |
| `const fromE: D = new E(1)` | **TS2322** | 「Property '#hidden' in type 'E' refers to a different member that cannot be accessed from within type 'D'.」 |

- ★★★ `A` 와 `B` 는 **모양이 완전히 같다.** 그런데 막혔다 — `private` 은 **어느 선언에서 왔나**로 비교되기 때문이다.
- ★ 두 번째 진단의 문구가 다르다 — 객체 리터럴 쪽은 「한쪽에만 `private` 이 있다」고 말한다.
- ★★ **상속은 예외**다. `C` 는 `A` 의 선언을 그대로 물려받았으므로 「같은 `secret`」이다.
- JS 의 `#` 도 같은 성질이다. 문구만 다르다 — 「다른 멤버를 가리킨다」.
- ★★ 즉 **`private`/`#` 멤버 하나가 그 클래스를 구조적 타이핑에서 빼낸다.** 1번의 `Coord` 가 통과한 것과 정확히 대비된다.

### 4. ★★★ 진단 **3건**(17·26·29행) — `asMethod` 와 `asProp` 은 **같은 시그니처인데 갈린다**

**출력**

```ts
// ex.05d.ts
// 함수끼리의 할당 — 매개변수 자리에서만 방향이 뒤집힌다
interface Animal {
    name: string;
}
interface Dog extends Animal {
    name: string;
    bark(): void;
}

declare function takeAnimal(a: Animal): void;
declare function takeDog(d: Dog): void;

type FnDog = (a: Dog) => void;
type FnAnimal = (a: Animal) => void;

const wide: FnDog = takeAnimal;
const narrowFn: FnAnimal = takeDog;

interface WithMethod {
    handle(a: Animal): void;
}
interface WithProp {
    handle: (a: Animal) => void;
}
const asMethod: WithMethod = { handle: takeDog };
const asProp: WithProp = { handle: takeDog };

const fewer: (a: number, b: number) => number = (a: number) => a;
const more: (a: number) => number = (a: number, b: number) => a + b;
console.log(wide, narrowFn, asMethod, asProp, fewer, more);
```

```text
===== tsc --pretty false --noEmit ex.05d.ts (tsc exit=1) =====
ex.05d.ts(17,7): error TS2322: Type '(d: Dog) => void' is not assignable to type 'FnAnimal'.
  Types of parameters 'd' and 'a' are incompatible.
    Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.05d.ts(26,28): error TS2322: Type '(d: Dog) => void' is not assignable to type '(a: Animal) => void'.
  Types of parameters 'd' and 'a' are incompatible.
    Property 'bark' is missing in type 'Animal' but required in type 'Dog'.
ex.05d.ts(29,7): error TS2322: Type '(a: number, b: number) => number' is not assignable to type '(a: number) => number'.
  Target signature provides too few arguments. Expected 2 or more, but got 1.
```

**왜 그런가**

| 줄 | 무엇 | 결과 |
|---|---|---|
| `const wide: FnDog = takeAnimal` | 넓게 받는 함수 → 좁게 받는 자리 | **통과**(반변) |
| `const narrowFn: FnAnimal = takeDog` | 좁게 받는 함수 → 넓게 받는 자리 | **TS2322** |
| `const asMethod: WithMethod = { handle: takeDog }` | **메서드 문법** 자리 | ★★ **통과** |
| `const asProp: WithProp = { handle: takeDog }` | **프로퍼티 문법** 자리 | **TS2322** |
| `const fewer: (a,b)=>number = (a)=>a` | 매개변수를 **적게** 받는 함수 | **통과** |
| `const more: (a)=>number = (a,b)=>a+b` | 매개변수를 **많이** 받는 함수 | **TS2322** |

- ★ `wide` 가 통과하는 이유 — 호출자는 `Dog` 를 줄 텐데 받는 쪽이 `Animal` 만 쓰면 **아무 문제가 없다**.
- ★ `narrowFn` 이 막히는 이유 — 호출자가 그냥 `Animal` 을 줄 수 있는데 받는 쪽은 `bark()` 를 부르려 한다. **실제로 터진다.**\
  진단이 그 경로를 두 단계로 적는다 — 「Types of parameters 'd' and 'a' are incompatible.」 → 「Property 'bark' is missing in type 'Animal' …」.
- ★★★ `asMethod` 와 `asProp` 은 **시그니처가 글자까지 같다**(`(a: Animal) => void`). 갈리는 것은 **선언 문법**이다 —\
  `handle(a: Animal): void` 는 메서드라 **양변**이고, `handle: (a: Animal) => void` 는 프로퍼티라 **`strictFunctionTypes` 가 적용**된다.
- 매개변수 **개수**는 또 다른 축이다 — 적게 받는 쪽은 되고, 많이 받는 쪽은 「Target signature provides too few arguments.」로 막힌다.

### 5. ★★★ **1건**으로 줄고 `more`(29행)만 살아남는다

**출력**

같은 `ex.05d.ts` 를 옵션만 바꿔 다시 던진다(파일은 한 글자도 안 바꿨다).

```ts
// ex.05d.ts
// 함수끼리의 할당 — 매개변수 자리에서만 방향이 뒤집힌다
interface Animal {
    name: string;
}
interface Dog extends Animal {
    name: string;
    bark(): void;
}

declare function takeAnimal(a: Animal): void;
declare function takeDog(d: Dog): void;

type FnDog = (a: Dog) => void;
type FnAnimal = (a: Animal) => void;

const wide: FnDog = takeAnimal;
const narrowFn: FnAnimal = takeDog;

interface WithMethod {
    handle(a: Animal): void;
}
interface WithProp {
    handle: (a: Animal) => void;
}
const asMethod: WithMethod = { handle: takeDog };
const asProp: WithProp = { handle: takeDog };

const fewer: (a: number, b: number) => number = (a: number) => a;
const more: (a: number) => number = (a: number, b: number) => a + b;
console.log(wide, narrowFn, asMethod, asProp, fewer, more);
```

```text
===== tsc --pretty false --noEmit --strictFunctionTypes false ex.05d.ts (tsc exit=1) =====
ex.05d.ts(29,7): error TS2322: Type '(a: number, b: number) => number' is not assignable to type '(a: number) => number'.
  Target signature provides too few arguments. Expected 2 or more, but got 1.
```

**왜 그런가**

- 켠 판의 세 건 중 **17행과 26행이 사라졌다.** 남은 것은 `more` 한 건이다.
- ★★★ 그래서 `strictFunctionTypes` 가 가르는 것은 정확히 **「함수 타입 표기의 매개변수 방향 검사」** 하나다.

| | 켜짐(기본) | 꺼짐 |
|---|---|---|
| 함수 타입 `(a: Animal) => void` 에 `(d: Dog) => void` | **TS2322** | 통과 |
| 메서드 `handle(a: Animal): void` 에 `(d: Dog) => void` | **통과** | 통과 |
| 매개변수 개수가 많은 함수를 적은 자리에 | **TS2322** | **TS2322** |

- ★★ **메서드 문법은 플래그와 무관하게 늘 양변**이다. 「엄격 모드를 켜면 다 잡힌다」가 여기서 깨진다.
- ★ 매개변수 **개수** 규칙은 아예 다른 축이라 플래그가 안 건드린다.
- ★ 왜 메서드에 예외를 남겼나 — `Array<T>.push`·DOM 이벤트 핸들러처럼 **양변을 전제로 쓰이던 코드가 너무 많았다.**

### 6. ★★ 진단 **4건** · `asPlainString` 은 **통과** · 이유 줄은 **최대 세 단계**

**출력**

```ts
// ex.05e.ts
// 모양이 같아 섞이는 두 문자열을 브랜드로 갈라 놓는다
type UserId = string & { readonly __brand: "UserId" };
type OrderId = string & { readonly __brand: "OrderId" };

const asUserId = (s: string) => s as UserId;
const asOrderId = (s: string) => s as OrderId;

const u = asUserId("u-1");
const o = asOrderId("o-9");

function findUser(id: UserId) {
    return id.toUpperCase();
}

console.log(findUser(u));
const mixed: OrderId = u;
const fromPlain: UserId = "u-1";
findUser("u-1");
findUser(o);
const asPlainString: string = u;
console.log(mixed, fromPlain, asPlainString);
```

```text
===== tsc --pretty false --noEmit ex.05e.ts (tsc exit=1) =====
ex.05e.ts(16,7): error TS2322: Type 'UserId' is not assignable to type 'OrderId'.
  Type 'UserId' is not assignable to type '{ readonly __brand: "OrderId"; }'.
    Types of property '__brand' are incompatible.
      Type '"UserId"' is not assignable to type '"OrderId"'.
ex.05e.ts(17,7): error TS2322: Type 'string' is not assignable to type 'UserId'.
  Type 'string' is not assignable to type '{ readonly __brand: "UserId"; }'.
ex.05e.ts(18,10): error TS2345: Argument of type 'string' is not assignable to parameter of type 'UserId'.
  Type 'string' is not assignable to type '{ readonly __brand: "UserId"; }'.
ex.05e.ts(19,10): error TS2345: Argument of type 'OrderId' is not assignable to parameter of type 'UserId'.
  Type 'OrderId' is not assignable to type '{ readonly __brand: "UserId"; }'.
    Types of property '__brand' are incompatible.
      Type '"OrderId"' is not assignable to type '"UserId"'.
```

**왜 그런가**

| 줄 | 결과 |
|---|---|
| `console.log(findUser(u))` | **통과** — 제대로 만든 `UserId` |
| `const mixed: OrderId = u` | **TS2322** — `"UserId"` 를 `"OrderId"` 에 못 넣는다 |
| `const fromPlain: UserId = "u-1"` | **TS2322** — 맨 문자열은 못 들어간다 |
| `findUser("u-1")` | **TS2345** — 인자 자리도 같다 |
| `findUser(o)` | **TS2345** — `OrderId` 를 `UserId` 자리에 |
| `const asPlainString: string = u` | ★★ **통과** — 브랜드가 붙어도 여전히 `string` 이다 |

- ★ 첫째·넷째 진단이 **세 단계**로 이유를 적는다 — 「`UserId` 를 `{ readonly __brand: "OrderId" }` 에 못 넣는다」 → 「`__brand` 가 안 맞는다」 → 「`"UserId"` 를 `"OrderId"` 에 못 넣는다」.
- ★★ `asPlainString` 이 통과하는 것이 이 수법의 **장점**이다 — `u.toUpperCase()` 같은 문자열 메서드를 그대로 쓸 수 있다.
- ★ 탈출구는 `asUserId` 안의 `as UserId` **하나**로 좁혀졌다. 그것이 이 설계의 전부다.

### 7. ★★ `asUserId` 가 **`(s) => s`** 가 된다 · `string` · `undefined` · `true`

**출력**

```ts
// ex.05f.ts
// 브랜드가 방출된 JS 에 남는지 본다
type UserId = string & { readonly __brand: "UserId" };

const asUserId = (s: string) => s as UserId;
const u: UserId = asUserId("u-1");

console.log("값:", u);
console.log("typeof:", typeof u);
console.log("__brand 프로퍼티:", (u as unknown as Record<string, unknown>).__brand);
console.log("그냥 문자열과 === :", (u as string) === "u-1");
```

```text
===== tsc --pretty false ex.05f.ts (tsc exit=0) =====
===== 방출된 ex.05f.js =====
"use strict";
const asUserId = (s) => s;
const u = asUserId("u-1");
console.log("값:", u);
console.log("typeof:", typeof u);
console.log("__brand 프로퍼티:", u.__brand);
console.log("그냥 문자열과 === :", u === "u-1");
```

```text
===== node ex.05f.js (node exit=0) =====
값: u-1
typeof: string
__brand 프로퍼티: undefined
그냥 문자열과 === : true
```

**왜 그런가**

- 방출된 `asUserId` 가 **`(s) => s`** 다 — `as UserId` 가 사라져 **아무 일도 안 하는 항등 함수**가 됐다.
- 실행 결과가 셋을 확인한다 — `typeof: string` · `__brand 프로퍼티: undefined` · `그냥 문자열과 === : true`.
- ★★ 즉 브랜드는 **검사 시각에만 있는 칸**이다. 직렬화·런타임 검사·로그에는 아무 흔적이 없다.
- ★ 그래서 **경계 밖에서 온 문자열을 `asUserId` 로 통과시키면 그냥 통과한다** — `as` 는 확인이 아니라 검사를 끄는 것이다([**01번 주제**](../01-what-ts-adds-and-erases/)).\
  진짜로 확인하려면 관문 함수 안에 **런타임 검사**를 같이 넣어야 한다.

### 8. ★★ 이득 둘 · 대가 둘

**왜 그런가**

| 이득 | 근거 |
|---|---|
| **남의 타입과 공짜로 호환된다** | `interface Vector` 를 `Point` 자리에 그대로 쓴다. 어댑터·선언이 필요 없다 |
| **테스트 더블을 쉽게 만든다** | `const c: Coord = { x: 1, y: 2 }` 가 통과한다 — 클래스를 `new` 할 필요가 없다 |

| 대가 | 근거 |
|---|---|
| ★ **의도치 않은 호환이 생긴다** | `UserId` 와 `OrderId` 가 둘 다 `string` 이면 **서로 섞인다**(6번 없이는 안 막힌다) |
| ★ **캡슐화를 타입으로 못 지킨다** | 그래서 `private`/`#` 라는 **예외 장치**가 따로 필요하다(3번) |

- ★ 한 줄로 — **JS 가 원래 그런 언어**이기 때문이다. JS 에는 「이 객체는 Point 다」라는 표시가 없고, TS 는 그 위에 얹힌 층이다.

### 9. ★★★ **구멍이 넷이나 되고**, 통과 여부가 **값이 아니라 문법 형태**로 갈린다

**왜 그런가**

- 근거 ① — 2번에서 **같은 값**이 변수 경유로는 통과하고 리터럴로는 `TS2353` 이었다.\
  타입 시스템의 규칙이라면 **값이 같으면 결과도 같아야** 한다.
- 근거 ② — 빠져나가는 길이 넷이다.

```text
  ① 변수에 담았다가 넘긴다        const v = { x, y, z };  take(v);
  ② 스프레드로 만든다             const s: Point = { ...v };
  ③ 단언을 붙인다                 { x, y, z } as Point
  ④ 인덱스 시그니처를 섞는다      Point & Record<string, unknown>
```

- ★★ 그래서 이 검사는 **오타 잡이**로 읽는다 — 「이 자리에 맞추려고 방금 쓴 리터럴」의 실수를 잡는 것.
- ★ **여분 프로퍼티를 진짜로 막고 싶으면** 이 검사에 기대면 안 된다. 런타임 검증(스키마 검사)이나 명목 수법이 필요하다.

### 10. ★★ 방법 둘 — **브랜드 타입**과 **`private` 을 가진 클래스**

**왜 그런가**

| 방법 | 형태 | 대가 |
|---|---|---|
| **브랜드 타입** | `type UserId = string & { readonly __brand: "UserId" }` | ★ **단언(`as`)이 필요하다** — 관문 함수 하나에 몰아넣어야 한다 · 런타임 보호는 **0** |
| **`private` 을 가진 클래스** | `class UserId { private brand; constructor(public value: string) {} }` | ★ **값이 객체가 된다** — 직렬화·비교·문자열 메서드를 못 쓴다 · 런타임 비용이 생긴다 |

- ★★ 브랜드는 **런타임에 0 원**이고(7번), 클래스는 **진짜 객체**라 비용이 있다.
- ★ 문자열·숫자처럼 **원시 값**을 가를 때는 브랜드가 거의 항상 낫다 — `toUpperCase()` 같은 메서드가 그대로 살기 때문이다(6번의 `asPlainString`).
- ★ 단위가 다른 수치(`Meters` 대 `Seconds`)도 같은 수법으로 가른다.

### 11. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 할당 가능성은 **모양**으로 정해진다 · 초과 프로퍼티 검사는 **리터럴을 직접 놓을 때만** 돈다 · `private`/`#` 는 **선언 자리로** 비교된다(상속은 예외) · 매개변수는 반변이고 **메서드 문법은 양변** |
| **설정에 달린 것** | **함수 타입 프로퍼티**의 매개변수 방향 검사 — `strictFunctionTypes`(`strict` 에 딸려 기본 `true`). **두 판을 다 실었다** |
| **이 판(7.0.2)의 관찰** | 진단 문구와 **들여쓴 이유 줄의 단계 수** · 스프레드 `{ ...v }` 가 초과 프로퍼티 검사를 **통과**하는 것 · `TS2741` 대 `TS2353` 대 `TS2322` 의 코드 배정 |

- ★ **「에러가 안 난 줄」도 이 판의 관찰이다.** 그래서 소스 전문을 같은 자리에 실어 누구나 다시 던질 수 있게 했다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 구조적 호환 | `--noEmit ex.05a.ts` | exit 1 · `TS2741` **1건**(22행) · 나머지 4대입 통과 |
| 초과 프로퍼티 | `--noEmit ex.05b.ts` | exit 1 · `TS2353` **2건**(14·15행) · 변수·스프레드·단언·인덱스는 통과 |
| `private`·`#` | `--noEmit ex.05c.ts` | exit 1 · `TS2322` **3건**(12·13·24행) · `fromC` 통과 |
| 함수 대입(엄격) | `--noEmit ex.05d.ts` | exit 1 · `TS2322` **3건**(17·26·29행) |
| 함수 대입(비엄격) | `--noEmit --strictFunctionTypes false ex.05d.ts` | exit 1 · `TS2322` **1건**(29행만) |
| 브랜드 | `--noEmit ex.05e.ts` | exit 1 · `TS2322` 2건 + `TS2345` 2건 · `asPlainString` 통과 |
| 브랜드 방출·실행 | `tsc ex.05f.ts` + `node ex.05f.js` | exit 0 · `(s) => s` · `string` / `undefined` / `true` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- 진단 문구와 **들여쓴 이유 줄의 단계 수** — 코드(`TS2741`·`TS2353`·`TS2322`·`TS2345`)가 더 오래 간다.
- 스프레드 `{ ...v }` 가 초과 프로퍼티 검사를 통과하는 것 — 이 판에서 직접 확인했다.
- `strict` 기본값이 `true` 라는 것 — **7.0 에서 바뀐 것**이다. 6.x 이하에서 재현하려면 `--strict` 를 명시해야 한다.

**안 돌려 본 것**

- `private` 을 가진 클래스로 명목을 만드는 판(10번 표의 둘째 행) — **형태만 적고 돌리지 않았다.** 그 줄에는 결과를 단정하지 않았고, 대가만 원리에서 적었다.
- `unique symbol` 을 키로 쓴 브랜드 — 목록의 **23번 주제**에서 던진다.
