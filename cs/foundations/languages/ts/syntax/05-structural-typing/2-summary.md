# ts/syntax/05 — 구조적 타이핑 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Type Compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) ·
> [Handbook — Object Types: Excess Property Checks](https://www.typescriptlang.org/docs/handbook/2/objects.html#excess-property-checks) ·
> [Handbook — More on Functions: Function Type Compatibility](https://www.typescriptlang.org/docs/handbook/2/functions.html) ·
> [TSConfig — `strictFunctionTypes`](https://www.typescriptlang.org/tsconfig/#strictFunctionTypes).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ **`tsc` 가 7.0.2 다 — 5.x 가 아니다.** 이 주제에서 결과를 좌우하는 기본값은 **`strict` 가 켜져 있다**는 것이다(7.0 기본 `true`).
> 그래서 `strictFunctionTypes` 도 켜져 있다 — **끈 판을 따로 던져 두 결과를 나란히 실었다.**
> **버전** — 구조적 타이핑은 TS 1.x 부터, `strictFunctionTypes` 는 2.6, JS 의 `#` 비공개 필드는 TS 3.8 부터 쓸 수 있다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드·문구·**들여쓴 이유 줄**·`(행,열)`·종료 코드·방출 전문·`node` 출력 | 같은 입력·같은 옵션이면 같은 글자다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌·요약 줄 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ 이 주제의 진단은 **여러 줄**이다. 들여쓴 줄이 **왜 안 되는지**를 단계별로 적는다 — **그 줄까지가 한 블록**이다.
> ★ **소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다** — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 한눈에 — 쉽게 말하면

**타입 이름은 명찰이 아니라 체크리스트다.**

| 비유 | 실체 |
|---|---|
| 「운전면허증 지참」이 아니라 「사진·이름·생년월일이 있을 것」 | **구조적 타이핑** — 이름이 아니라 **모양**으로 받아들인다 |
| 체크리스트를 다 만족하면 **어느 서류든** 통과 | `interface Point` 자리에 `Vector`·`Coord` 가 다 들어간다 |
| 항목이 더 많은 서류도 통과 | **여분 프로퍼티는 문제가 아니다** — 변수를 거치면 통과 |
| ★ 단 **창구에 직접 내밀 때만** 「이건 뭐죠?」라고 묻는다 | **초과 프로퍼티 검사** — **객체 리터럴을 직접 넘길 때만** 걸린다 |
| 도장이 하나 찍힌 서류는 그 기관 것만 인정 | **`private`/`#` 멤버** — 하나만 있어도 **명목**이 된다 |
| 위조 방지 워터마크를 일부러 찍는다 | **브랜드 타입** — 타입만으로 이름을 흉내 낸다 |

- ★★ 한 줄로 — **「이름이 같아서 되는 게 아니라 모양이 맞아서 된다. 그리고 그 규칙을 깨는 자리가 셋 있다.」**
- ★★ 규칙을 깨는 셋 — **초과 프로퍼티 검사** · **`private`/`#` 멤버** · **함수 매개변수의 방향**.

```text
  명목 타이핑 (Java·C#)                구조적 타이핑 (TypeScript)
  +---------------------------+        +---------------------------+
  | class Point implements … |        | interface Point { x; y }  |
  |                           |        | interface Vector { x; y } |
  | Vector 를 Point 자리에    |        | Vector 를 Point 자리에    |
  | 넣으려면 **선언**이 필요  |        | 넣는다 — **모양이 같으니** |
  +---------------------------+        +---------------------------+
    「나는 Point 다」라고 적어야        체크리스트만 맞으면 된다
```

```text
  같은 값인데 자리에 따라 갈린다 — 초과 프로퍼티 검사
                                 { x: 1, y: 2, z: 3 }
                                          │
              ┌───────────────────────────┴───────────────────────────┐
              ▼                                                       ▼
   변수에 담았다가 넘긴다                                  리터럴을 직접 넘긴다
   const v = { x, y, z };                                 take({ x, y, z })
   take(v);                                                        │
              │                                                     ▼
              ▼                                              TS2353 — 'z' 가 없다
            통과
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **무엇이 할당 가능성을 정하나** — 타입의 **이름**인가 **모양**인가. 그 근거는 무엇인가.
2. **그 규칙이 깨지는 자리는 어디인가** — 초과 프로퍼티 검사 · `private` 멤버 · 함수 매개변수의 방향.
3. **이름으로 구분해야 할 때는 어떻게 하나** — `UserId` 와 `OrderId` 를 섞지 못하게 만드는 법.

★ [**03번 주제**](../03-basic-type-annotations/)가 표기를, [**04번 주제**](../04-any-unknown-never-void/)가 위아래 끝의 네 타입을 다뤘다면, 여기는 **그 사이의 모든 타입에 적용되는 할당 규칙**이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **여러 줄 진단의 들여쓴 이유 줄** | 「왜 안 되는지」를 **컴파일러가 단계별로** 적어 준다 | ★ 이 주제의 고유 창 |
| ★★ **같은 파일을 옵션만 바꿔 두 번** | `strictFunctionTypes` 로 **갈리는 칸**을 가려낸다 | ★ 이 주제의 고유 창 |
| **진단 유무의 전수 대조** | 「되는 칸」이 어디인지 — **에러가 안 난 줄**도 근거다 | 모든 주제 공통 |
| **방출된 `.js` + `node`** | 브랜드가 **런타임에 아무것도 아닌 것** | [**01번 주제**](../01-what-ts-adds-and-erases/)에서 이어받음 |

★ **「에러가 안 난 줄」이 근거라는 점**이 이 주제의 특징이다. 진단 목록에 **없는 줄**을 세는 것이 절반이다.

비용 — 컴파일 한 번.

### (1) ★★★ 이름이 아니라 모양

**언제 쓰나** — 「내 `interface` 자리에 왜 남의 객체가 들어가지?」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **한 건**뿐이다. **나머지 네 줄이 전부 통과했다.**
- `const v: Vector = p` — 이름이 다른 두 `interface` 가 **모양이 같아서** 통과했다.
- `const c: Coord = p` — **객체 리터럴에서 온 값이 클래스 타입 자리에** 들어갔다. `new` 로 만든 것이 아닌데 통과한다.
- `const backToPoint: Point = new Coord(1, 2)` — 반대 방향도 통과했다.
- `const widen: Point = triple` — **프로퍼티가 더 많은 쪽**은 적은 쪽 자리에 들어간다.
- ★★ 막힌 것은 `const narrow: Triple = p` **하나**다 — `TS2741`, 「Property 'z' is missing」. **모자란 쪽**은 못 들어간다.

```text
  Triple { x, y, z }   ──────▶   Point { x, y }      통과 (더 많아도 된다)
  Point  { x, y }      ──╳───▶   Triple { x, y, z }  TS2741 (모자라면 안 된다)
```

비용 — 없음. 다만 **의도치 않은 호환**이 생긴다 — 그것이 3·5절의 주제다.

### (2) ★★★ 초과 프로퍼티 검사는 **리터럴에만** 걸린다

**언제 쓰나** — 「같은 값인데 변수에 담으면 통과하고 직접 넘기면 에러」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **두 건**이고 둘 다 **객체 리터럴을 직접 쓴 줄**이다 — `const bad1: Point = { …, z: 3 }` 과 `take({ …, z: 3 })`.
- ★★★ **같은 값을 변수에 담아 넘긴 `ok1`·`take(viaVar)` 는 통과했다.** 값이 같은데 **문법 형태로 갈린다.**
- ★ `const spread: Point = { ...viaVar }` 도 **통과했다** — 스프레드로 만든 객체는 이 검사에 안 걸린다.
- ★ `as Point` 단언을 붙인 줄도 통과했다 — 단언은 검사를 끈다.
- ★ `Point & Record<string, unknown>` 으로 받은 줄도 통과했다 — 인덱스 시그니처가 여분 키를 받아 준다.

> **초과 프로퍼티 검사(excess property check)** — **객체 리터럴을 타입이 정해진 자리에 직접 놓을 때만** 도는 추가 검사.\
> 예: `take({ x: 1, y: 2, z: 3 })` 은 `TS2353` 인데, 같은 객체를 변수에 담아 `take(v)` 로 넘기면 통과한다.

- ★★ 왜 이렇게 만들었나 — **리터럴을 직접 적었다는 것은 「이 자리에 맞추려고 방금 쓴 것」이라는 뜻**이다.\
  거기 오타(`colour` 대신 `color`)가 있으면 **잡아 주는 게 맞다.** 반면 이미 있는 변수는 다른 용도로도 쓰이므로 여분이 정상일 수 있다.
- ★★★ 그래서 이 검사는 **타입 시스템의 규칙이 아니라 편의 장치**다. **구멍이 넷**(변수·스프레드·단언·인덱스 시그니처)이나 있는 이유다.

비용 — 없음. 다만 **이 검사에 기대면 안 된다** — 구멍이 많다.

### (3) ★★★ `private` 멤버 하나가 명목으로 바꾼다

**언제 쓰나** — 「모양이 같은데 왜 이 클래스는 안 들어가지?」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- `const fromB: A = new B(1)` 이 **`TS2322`** 다. 들여쓴 줄이 이유를 적는다 — 「Types have separate declarations of a private property 'secret'.」\
  ★★ **모양이 완전히 같은데** 막혔다. `private` 이 **선언 자리**로 구별되기 때문이다.
- `const fromLiteral: A = { x: 1, secret: 1 }` 도 막힌다 — 「Property 'secret' is private in type 'A' but not in type …」.
- ★ `const fromC: A = new C(1)` 은 **통과했다.** `class C extends A` 라 **같은 선언을 물려받았다** — 상속은 예외다.
- JS 의 `#` 도 같다 — `const fromE: D = new E(1)` 이 `TS2322` 이고, 이유 줄이 「refers to a different member that cannot be accessed from within type 'D'」다.
- ★★ 즉 **`private` 이나 `#` 멤버가 하나라도 있으면 그 클래스는 구조적 타이핑에서 빠져나온다.**

```text
  class A { private secret; x }        class B { private secret; x }
        │                                     │
        └────────── 모양 동일 ────────────────┘
                     하지만 TS2322
                「선언이 서로 다르다」

  class C extends A {}   ──────▶  A 자리에 통과  (같은 선언을 물려받았다)
```

비용 — 명목이 되는 대신 **테스트 더블·목 객체를 만들기 어려워진다.** 그게 대가다.

### (4) ★★★ 함수 매개변수는 방향이 뒤집힌다

**언제 쓰나** — 「콜백 타입이 왜 이쪽만 되지?」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- `const wide: FnDog = takeAnimal` 이 **통과했다.** `FnDog` 는 「`Dog` 를 받는 함수」 자리인데 **더 넓은 `Animal` 을 받는 함수**가 들어갔다.\
  ★ 호출자는 `Dog` 를 줄 텐데 받는 쪽이 `Animal` 만 쓰면 **아무 문제가 없다.**
- `const narrowFn: FnAnimal = takeDog` 은 **`TS2322`** 다 — 들여쓴 줄이 「Types of parameters 'd' and 'a' are incompatible.」, 그 아래가 「Property 'bark' is missing in type 'Animal' …」.\
  ★ 호출자가 그냥 `Animal` 을 줄 수 있는데 받는 쪽은 `bark()` 를 부르려 한다 — **실제로 터진다.**
- ★★★ `const asMethod: WithMethod = { handle: takeDog }` 은 **통과했다.** `WithMethod.handle` 이 **메서드 문법**(`handle(a: Animal): void`)이기 때문이다.
- `const asProp: WithProp = { handle: takeDog }` 은 **막힌다.** 같은 시그니처인데 **프로퍼티 문법**(`handle: (a: Animal) => void`)이다.
- 매개변수 **개수**는 또 다른 규칙이다 — `fewer`(적게 받는 함수를 많이 받는 자리에)는 통과하고, `more`(많이 받는 함수를 적게 받는 자리에)는 `TS2322` 다.

같은 파일을 `--strictFunctionTypes false` 로 던지면 **두 칸이 통과로 바뀐다**.

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

- ★★ 남은 진단이 **`more` 한 건**뿐이다 — 17행과 26행이 사라졌다.
- ★★★ 즉 `strictFunctionTypes` 가 가르는 것은 「**함수 타입 표기의 매개변수 방향**」이고,\
  **메서드 문법은 그 플래그와 무관하게 늘 양방향**(bivariant)이며, **매개변수 개수 규칙은 아예 다른 축**이다.

| | `strictFunctionTypes` 켜짐(기본) | 꺼짐 |
|---|---|---|
| 함수 타입 `(a: Animal) => void` 에 `(d: Dog) => void` | **TS2322** | 통과 |
| 메서드 `handle(a: Animal): void` 에 `(d: Dog) => void` | **통과** | 통과 |
| 매개변수 개수가 많은 함수를 적은 자리에 | **TS2322** | **TS2322** |

> **반변(contravariance)** — 매개변수 자리에서 방향이 뒤집히는 것. 「더 넓은 것을 받는 함수」가 「더 좁은 것을 받는 자리」에 들어간다.\
> 예: `Animal` 을 받는 함수는 `Dog` 를 받는 자리에 쓸 수 있다.

> **양변(bivariance)** — 양쪽 방향이 다 허용되는 것. 안전하지 않지만 실용성 때문에 **메서드 문법**에 남아 있다.\
> 예: 배열의 `push`·DOM 이벤트 핸들러가 이 규칙에 기대고 있다.

비용 — 메서드 문법의 양변은 **안전하지 않다.** 대신 표준 라이브러리 전체가 그 위에 서 있다.

### (5) ★★ 브랜드 타입으로 명목을 흉내 낸다

**언제 쓰나** — `UserId` 와 `OrderId` 가 둘 다 `string` 이라 섞이는 것을 막고 싶을 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **네 건**이다 — `mixed`(UserId → OrderId) · `fromPlain`(string → UserId) · `findUser("u-1")` · `findUser(o)`.
- ★ 들여쓴 줄이 이유를 **세 단계**로 적는다 — 「`__brand` 가 안 맞는다」 → 「`"UserId"` 를 `"OrderId"` 에 못 넣는다」.
- ★★ `const asPlainString: string = u` 는 **통과했다** — 브랜드가 붙어도 **여전히 `string`** 이다.\
  그래서 `u.toUpperCase()` 같은 문자열 메서드가 그대로 쓰인다.
- ★ 관문이 `asUserId` 하나로 좁혀진다 — 그 함수 안의 `as UserId` 가 **유일한 탈출구**다.

```text
  type UserId  = string & { readonly __brand: "UserId"  }
  type OrderId = string & { readonly __brand: "OrderId" }
                    │                   │
          string 의 모든 메서드          서로를 가르는 유일한 칸
          그대로 쓸 수 있다              (런타임에는 없는 칸이다)
```

비용 — **단언 한 번**이 필요하다. 그 단언을 한 함수에 몰아넣는 것이 설계다.

### (6) ★★ 브랜드는 런타임에 아무것도 아니다

**언제 쓰나** — 「`__brand` 프로퍼티가 진짜로 붙나?」가 궁금할 때.

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

그림 해설 — 한 단계에 한 문장.

- 방출된 파일에서 `asUserId` 가 **`(s) => s`** 다 — `as UserId` 가 사라져 **아무 일도 안 한다**.
- 실행 결과가 그것을 확인한다 — `typeof` 가 `string` 이고, `__brand` 프로퍼티가 **`undefined`** 이며, `"u-1"` 과 `===` 가 **`true`** 다.
- ★★ 즉 브랜드는 **검사 시각에만 있는 칸**이다. 런타임 검사·직렬화에는 아무 영향이 없다.
- ★ 그래서 **경계 밖에서 온 문자열을 브랜드로 믿으면 안 된다** — `as` 는 검사를 끄는 것이지 확인이 아니다([**01번 주제**](../01-what-ts-adds-and-erases/)).

비용 — 0. 방출에 한 글자도 안 남는다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 쓴 것
  interface Point { x: number; y: number }        구조로만 비교된다
  class A { private secret = 1 }                   ★ 명목이 된다
  class D { #hidden = 1 }                          ★ 명목이 된다 (JS 비공개 필드)
  interface M { handle(a: Animal): void }          메서드 문법 — 양변
  interface P { handle: (a: Animal) => void }      프로퍼티 문법 — strictFunctionTypes 적용
  type UserId = string & { readonly __brand: "UserId" }    브랜드
```

**규칙 불릿**

- ★★★ **할당 가능성은 모양으로 정해진다.** 「대상이 요구하는 멤버를 원본이 전부 갖고 있나」가 기준이다.
- ★ **더 많은 쪽은 적은 쪽 자리에 들어간다.** 모자라면 `TS2741`.
- ★★ **객체 리터럴을 직접 놓을 때만 초과 프로퍼티 검사가 돈다**(`TS2353`). 변수·스프레드·단언·인덱스 시그니처로 **전부 빠져나간다**.
- ★★ **`private` 이나 `#` 멤버가 하나라도 있으면 그 클래스는 명목이 된다.** 단 **상속은 예외**다.
- ★★ **함수 매개변수는 반변**이다 — 넓게 받는 함수를 좁게 받는 자리에 쓸 수 있다. 반대는 `strictFunctionTypes` 가 막는다.
- ★★ **메서드 문법은 그 플래그와 무관하게 양변**이다. 같은 시그니처라도 **`handle(a)` 와 `handle: (a) => …` 가 다르게 검사된다.**
- ★ **매개변수 개수**는 별개 축이다 — 적게 받는 함수는 되고, **많이 받는 함수는 안 된다**(`TS2322`, 「provides too few arguments」).

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 모자란 모양을 넣기        ->  TS2741  Property 'z' is missing in type 'Point' …
2) 리터럴에 여분 프로퍼티     ->  TS2353  Object literal may only specify known properties …
3) private 이 다른 클래스     ->  TS2322  Types have separate declarations of a private property …
4) 좁게 받는 함수를 넓은 자리에 ->  TS2322  Types of parameters 'd' and 'a' are incompatible.
```

## 어디서 틀리나

- ★★★ **「내 `interface` 로 선언했으니 남의 객체는 안 들어온다」** — 들어온다. **모양만 맞으면** 된다.
- ★★★ **「초과 프로퍼티 검사가 여분을 막아 준다」** — **리터럴에만** 건다. 변수·스프레드·단언·인덱스 시그니처로 **넷 다 빠져나간다**.
- ★★ **「같은 코드인데 왜 여기선 되고 저기선 안 되지」** — 값이 아니라 **문법 형태**가 다른 것이다(리터럴인가 변수인가).
- ★★ **「`private` 은 소거되니 타입에도 영향이 없겠지」** — 방출에서는 사라지지만 **검사에서는 명목을 만든다.** 두 층을 갈라 읽는다.
- ★★ **「메서드로 쓰든 프로퍼티로 쓰든 같겠지」** — 다르다. **메서드 문법만 양변**이라 `strictFunctionTypes` 를 켜도 안 걸린다.
- ★ **「`strictFunctionTypes` 를 켜면 모든 함수 할당이 엄격해진다」** — 메서드 문법은 **그대로다.** 이 배치에서 옵션을 껐을 때 갈린 것은 **두 칸**뿐이다.
- ★ **「브랜드를 붙였으니 런타임에도 구분된다」** — 안 된다. `__brand` 는 **`undefined`** 이고 `===` 가 `true` 다.
- ★ **「매개변수를 더 받는 함수도 되겠지」** — 안 된다. **적게 받는 쪽만** 된다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 할당 가능성은 **모양**으로 정해진다 | 핸드북 「Type Compatibility」. 이 판에서 네 줄이 통과한 것이 그 결과다 |
| **언어 보장** | 초과 프로퍼티 검사는 **객체 리터럴을 직접 놓을 때만** 돈다 | 핸드북 「Excess Property Checks」. 같은 값이 변수 경유로 통과 |
| **언어 보장** | `private`/`#` 멤버는 **선언 자리로** 비교된다(상속은 예외) | 진단의 들여쓴 이유 줄이 그 규칙을 그대로 말한다 |
| **언어 보장** | 매개변수는 반변, **메서드 문법은 양변** | `strictFunctionTypes` 를 껐을 때 갈린 칸이 **둘**뿐인 것 |
| **설정에 달림** | 함수 타입 프로퍼티의 매개변수 방향 검사 | `strictFunctionTypes`(`strict` 에 딸려 기본 `true`). **두 판을 다 실었다** |
| **이 판(7.0.2)의 관찰** | 진단 문구와 **들여쓴 이유 줄의 단계 수** | 문구는 판마다 바뀐다. 코드(`TS2741`·`TS2353`·`TS2322`)가 더 오래 간다 |
| **이 판의 관찰** | 스프레드(`{ ...v }`)가 초과 프로퍼티 검사를 **통과**하는 것 | 이 판에서 직접 확인했다. 판이 오르면 다시 던진다 |
| **런타임** | 브랜드·`private` 이 **방출에 안 남는 것** | `ex.05f.js` 전문과 `node` 출력 |

★ **「에러가 안 난 줄」도 근거다.** 이 주제에서는 **진단 목록에 없는 줄**을 세는 것이 절반이다 — 그래서 소스 전문을 같은 자리에 실었다.

## 언제 쓰고 언제 안 쓰나

| 구조로 두기 | 명목으로 만들기 |
|---|---|
| 데이터 모양만 맞으면 되는 것 — DTO·설정 객체·좌표 | ★ **식별자**(`UserId`·`OrderId`) — 브랜드 타입 |
| 목·테스트 더블을 쉽게 만들고 싶을 때 | 단위가 다른 수치(`Meters`·`Seconds`) — 브랜드 타입 |
| 라이브러리 경계에서 남의 타입과 호환되게 | 캡슐화가 필요한 클래스 — `private`/`#` |

| 쓴다 | 안 쓴다 |
|---|---|
| `#`(JS 비공개) — **런타임에도** 감춰진다 | `private` 만 믿고 비밀을 담는 것 — 방출에 이름이 남는다 |
| 메서드 문법 — 표준 라이브러리와 호환된다 | 안전이 중요한 콜백에 메서드 문법 — **양변이라 안 걸린다** |
| 브랜드 — 관문 함수 하나에 `as` 를 몰아넣는다 | 브랜드를 런타임 검증으로 여기는 것 |

## 핵심 문장

1. **이름이 아니라 모양이다** — 이름이 다른 두 `interface` 가 서로 오가고, 객체 리터럴이 클래스 타입 자리에 들어간다.
2. **더 많은 쪽은 되고 모자란 쪽은 안 된다** — `TS2741` 이 그 경계다.
3. **초과 프로퍼티 검사는 리터럴 전용 편의 장치다** — 구멍이 넷(변수·스프레드·단언·인덱스 시그니처)이다.
4. **`private`/`#` 멤버 하나가 그 클래스를 명목으로 만든다** — 상속만 예외다.
5. **매개변수는 반변이고 메서드 문법은 양변이다** — `strictFunctionTypes` 는 앞쪽만 건드린다.
6. **브랜드 타입은 검사 시각에만 있는 칸이다** — `__brand` 는 런타임에 `undefined` 다.

## 관련 자료

- [**03번 주제** — 기본 타입 표기](../03-basic-type-annotations/) — 객체 타입·함수 타입의 **표기 형태**는 그쪽. 여기서는 **할당 규칙**만.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — 위아래 끝의 네 타입은 그쪽. 여기서는 **그 사이의 모든 타입**.
- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 「브랜드·`private` 이 방출에 안 남는다」의 근거는 그쪽.
- [목록의 **06번 주제**](../06-excess-property-checks/)(초과 프로퍼티 검사) — 전면 서술은 그쪽. 여기서는 **구조적 타이핑의 예외**로서만 본다.
- [목록의 **17번 주제**](../17-variance-and-parameter-compatibility/)(변성과 매개변수 양립성) — 반변·양변의 전면 서술은 그쪽. 여기서는 **`strictFunctionTypes` 로 갈리는 칸**까지.
- 목록의 **30번 주제**(타입 단언과 non-null `!`) — `as` 의 위험은 그쪽. 브랜드의 관문 함수가 그 위에 서 있다.
- 목록의 **32번 주제**(클래스의 타입 측면) — `private` 대 `#` 의 전면 비교는 그쪽.
- `../../js/syntax/README.md` 의 **16번 주제**(`class` 문법) — `#` 비공개 필드의 **런타임 의미는 JS 갈래가 정본**이다.

## 용어 풀이

> **구조적 타이핑(structural typing)** — 타입의 **이름**이 아니라 **멤버 구성**으로 호환을 판정하는 방식.\
> 예: `interface Vector { x; y }` 의 값이 `interface Point { x; y }` 자리에 그대로 들어간다.

> **명목 타이핑(nominal typing)** — 「이 타입이라고 **선언한** 것」만 그 자리에 넣어 주는 방식.\
> 예: Java 의 `implements`. TS 에서는 `private` 멤버나 브랜드로 **흉내**만 낸다.

> **초과 프로퍼티 검사(excess property check)** — 객체 리터럴을 타입이 정해진 자리에 **직접** 놓을 때만 도는 추가 검사.\
> 예: `take({ x: 1, y: 2, z: 3 })` 은 `TS2353`, 같은 객체를 변수로 넘기면 통과.

> **반변(contravariance)** — 매개변수 자리에서 방향이 뒤집히는 것.\
> 예: `Animal` 을 받는 함수를 `Dog` 를 받는 자리에 쓸 수 있다.

> **양변(bivariance)** — 양쪽 방향이 다 허용되는 것. 안전하지 않지만 메서드 문법에 남아 있다.\
> 예: `handle(a: Animal): void` 자리에 `(d: Dog) => void` 가 들어간다.

> **브랜드 타입(branded type)** — 실제로는 없는 칸을 타입에만 붙여 **같은 모양을 갈라 놓는** 수법.\
> 예: `type UserId = string & { readonly __brand: "UserId" }`. 방출에는 한 글자도 안 남는다.

> **관문 함수(smart constructor)** — 브랜드를 붙이는 **단언 한 곳**을 함수로 모아 둔 것.\
> 예: `const asUserId = (s: string) => s as UserId;` — `as` 가 이 함수 안에만 있다.

## 더 들어가면

- **초과 프로퍼티 검사가 왜 「규칙」이 아닌가** — 타입 시스템의 할당 가능성은 이미 「더 많아도 된다」로 정해져 있고, 이 검사는 그 위에 덧붙인 **오타 잡이**다. 그래서 구멍이 많고, 그것이 설계 의도대로다.
- **브랜드를 `unique symbol` 로** — `declare const brand: unique symbol;` 를 키로 쓰면 `__brand` 라는 이름조차 충돌하지 않는다. [목록의 **23번 주제**](../23-typeof-type-operator/)와 엮인다.
- **`satisfies`(4.9)와의 궁합** — 브랜드 객체를 만들 때 `as` 대신 `satisfies` 를 쓰면 추론을 살리면서 검사만 할 수 있다. 목록의 **29번 주제**.
- **양변이 남은 이유** — `Array<T>.push`·DOM 이벤트 핸들러처럼 **양변을 전제로 쓰이던 코드**가 너무 많아, 메서드 문법에만 예외를 남겼다. `strictFunctionTypes` 문서가 그 사정을 적는다.
