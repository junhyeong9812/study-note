# ts/syntax/20 — 제네릭 제약과 기본 타입 인자 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Generics: Generic Constraints](https://www.typescriptlang.org/docs/handbook/2/generics.html#generic-constraints) ·
> [Handbook — More on Functions: Constraints](https://www.typescriptlang.org/docs/handbook/2/functions.html#constraints) ·
> [Handbook — Generics: Generic Parameter Defaults](https://www.typescriptlang.org/docs/handbook/2/generics.html#generic-parameter-defaults).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단 전문은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version (sh exit=0) =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 블록은 **옵션을 배너에 적힌 것만** 준 결과다.
> 이 배치는 `-t es2022 --strict` 를 **전부 명시**했다.
> ★★ 6절은 **Rust** 로 같은 질문을 던졌다 — `rustc` 는 **1.92.0 (ded5c06cf 2025-12-08)** 이다(블록 배너 참조).
> **버전** — `extends` 제약은 TS **1.x**, **기본 타입 인자는 TS 2.3** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## ★★★ 이 배치가 쓰는 탐침 — 「컴파일러가 타입을 말하게 하는 법」

**추론된 타입은 눈에 안 보인다.** 그래서 이 갈래는 **일부러 틀린 주석을 달아 컴파일러가 답을 뱉게** 한다.

```text
  const probe: null = 무엇인가;
                      └─ 이 자리의 타입이 X 라면

  error TS####: Type 'X' is not assignable to type 'null'.   <- 실제 코드는 TS2322
                      ↑ 여기서 X 를 읽는다
```

- ★★ 이 문서의 `TS2322 … is not assignable to type 'null'` 은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
- ★ 단 **3절만은 다르다** — 거기서는 `TS2322` 가 **진짜 에러**이고 그것이 절의 주제다. 문구로 가른다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`·`E0277`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | ★★ `keyof` 가 뱉는 키의 **정렬 순서**(`"admin" \| "age" \| "name"`) | 실측에서 **사전순**이었다 — 5회 재실행 동일 |
| **안 흔들린다** | ★★ `rustc` 의 캐럿 위치와 `note:` 줄 | 소스를 그대로 실었으니 다시 던질 수 있다 |
| **★ 설정에 달렸다** | ★★ 4절의 **`ex.20d.ts` 한 파일** — `strictNullChecks` | 7절에 양쪽을 다 실었다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **★ 부적용** | 「여러 번 돌려 본다」 | 난수·시각·순서 비보장이 **한 칸도 없다** |
| **안 잰 것** | 재귀 제약의 **검사 시간·깊이 한계** | 재지 않았다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ Rust 블록의 파일명은 `ex.20f.rs` 이고 **크레이트 이름을 따로 줬다**(`--crate-name ex20f`) — 점이 든 파일명을 `rustc` 가 거부한다.

## 한눈에 — 쉽게 말하면

**제약은 「이 칸에는 최소한 이 모양이 와야 한다」는 문패다. 문패는 들어올 것을 거르지만, 안에서 그 문패를 도로 쓸 수는 없다.**

| 비유 | 실체 |
|---|---|
| 놀이기구의 **「키 120cm 이상」 표지** | `T extends { length: number }` |
| 표지가 있어야 **탈 사람을 거른다** | 제약 없으면 멤버를 하나도 못 쓴다(1절) |
| ★★★ 그런데 **「딱 120cm 인 사람」을 만들어 낼 수는 없다** | 제약 타입의 값을 안에서 못 만든다(3절) |
| 표를 안 내면 **기본 표**를 준다 | 기본 타입 인자 `<T = string>` |
| 기본 표도 **키 제한을 지켜야** 한다 | 기본값이 제약을 어기면 `TS2344` |

- ★★★ 한 줄로 — 「**제약은 상한이 아니라 하한이다.**」 `T extends Point` 는 「`Point` 다」가 아니라 「**`Point` 이상**」이다.
- ★★ 3절의 함정이 전부 거기서 나온다 — **하한만 알지 정확히 무엇인지는 모른다.**

```text
  제약은 하한이다

  function f<T extends Point>(p: T): T

      T 가 될 수 있는 것          Point · Point3(x,y,z) · { x, y, 아무거나 } …
                                     ▲
      Point 는 그중 가장 넓은 것 ────┘

      p.x 를 읽는다        ✓  모든 후보가 x 를 갖는다
      { x: 0, y: 0 } 를    ✗  Point3 일 수도 있으므로 z 가 없다
      T 로 돌려준다             TS2322 — "could be instantiated with a different subtype"
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **제약을 걸면 무엇이 되고 무엇이 안 되나** — ★★★ **읽기는 되고 만들기는 안 된다**(1·3절).
2. **기본 타입 인자는 추론인가 고정인가** — [**19번 주제**](../19-generics-basics/) 4절의 답을 규칙으로 정리한다(4절).
3. **다른 언어는 어디서 막나** — **Rust 로 같은 것을 던져** 본다(6절). Java 는 형제 문서와 견준다.

★★ **19 → 20 → 21 은 한 사슬**이다. [**19번 주제**](../19-generics-basics/) 2절의 고장을 **제약이 절반 고치고**([**19번**](../19-generics-basics/) 2절 23행),
나머지는 [**21번 주제**](../21-inference-control-const-and-noinfer/)가 고친다.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 성질 |
|---|---|---|
| ★★★ **진단 전문** | 어디서 막히나 — `TS2339`·`TS2344`·`TS2322` | 사실 |
| ★★ **`null` 탐침** | 컴파일러가 **계산한** 타입 | **계산된 것** |
| ★★ **다른 컴파일러(`rustc`)** | 같은 질문의 **다른 답** | 사실 |
| ★ **부적용 — 방출 `.js`** | ★★ **잴 것이 없다** | 제약은 **전부 타입 층**이라 방출물에 아무 자국도 없다 |

★★★ 마지막 줄이 이 주제의 성질이다 — [**18번**](../18-this-parameter-types/)·[**19번**](../19-generics-basics/)이 `.js` 로 결론을 낸 자리가 여기서는 「**잴 것이 없다**」다.
「재 봤더니 같았다」가 아니라 **제약은 방출에 아무것도 더하지 않는다** — 그래서 이 문서에는 `.js` 블록이 **하나도 없다.**

비용 — 컴파일 여섯 번(TS 다섯 + Rust 한 번).

### (1) ★★★ 제약이 없으면 멤버를 하나도 못 쓴다

**언제 쓰나** — 「`T` 에 `.length` 를 썼더니 없다고 한다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **일곱 건**이고 그중 다섯이 탐침이다.
- ★★★ 3행 — 제약 없는 `T` 에 `.length` 를 쓰면 **`TS2339`** 다. 「Property 'length' does not exist on type 'T'.」\
  **제약이 없으면 `T` 는 아무것도 아니다** — `unknown` 과 같은 취급이다.
- ★★ **그 진단은 정의 자리에 난다**(3행). 부르는 자리가 아니다 — **몸통이 정의 시점에 검사된다.**
- ★★★ 14행 — `lenOf(3)` 은 `TS2345` 다. **제약이 걸러 낸다.** 이쪽은 **사용 자리**의 진단이다.
- ★★ 즉 **두 자리에서 각각 막는다** — 몸통은 정의 자리에서, 인자는 사용 자리에서.
- ★ 12행 — `{ length: 3, extra: true }` 도 통과한다. **제약은 하한**이므로 더 가져도 된다.
- ★★★ 22행이 **구조적 타이핑의 얼굴**이다. `class Rope` 는 `HasLen` 을 **`implements` 하지 않았는데** 통과한다 —\
  **모양만 맞으면 된다**([**05번 주제**](../05-structural-typing/)). 6절에서 Rust 와 갈리는 지점이 정확히 여기다.

> **제약(constraint)** — `T extends U` 는 「`T` 는 **`U` 이상**」이라는 **하한** 선언이다.\
> 상한이 아니다 — 그래서 `T` 를 만들어 낼 수는 없다(3절).

비용 — 제약을 좁히면 **받을 수 있는 인자가 줄어든다.** 넓히면 **몸통에서 쓸 수 있는 멤버가 줄어든다.**

### (2) ★★ `keyof` 제약 — `get(obj, key)` 관용구

**언제 쓰나** — 「키를 문자열로 받으면 오타가 안 잡힌다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **일곱 건**이다.
- ★★★ 8·9·10행이 관용구의 값이다. **같은 함수**인데 키마다 답이 다르다 —\
  `get(user,"name")` 은 **`string`**, `"age"` 는 **`number`**, `"admin"` 은 **`boolean`** 이다.\
  **키가 값 타입을 정한다.**
- ★★ 12행 — 없는 키를 주면 `TS2345` 이고 **허용되는 키 목록이 진단에 찍힌다** —\
  `'"admin" | "age" | "name"'`. ★ 실측에서 **사전순**이었다(관찰이지 보장이 아니다).
- ★★★ 15행이 경계다. **`string` 타입 변수**를 키로 주면 막힌다 — 런타임에 무슨 값일지 모르기 때문이다.\
  **`keyof` 제약은 「키가 컴파일 타임에 알려져 있을 때」만 쓸 수 있다.**
- ★ 20행 — 제약을 포기한 `getLoose` 는 `unknown` 을 준다. **오타도 안 잡고 타입도 안 준다.**
- ★ 24행 — `keyof typeof user` 자체가 리터럴 유니온이다. 그 규칙은 목록의 **22번 주제**.

```text
  키가 값 타입을 정한다

  function get<O, K extends keyof O>(obj: O, key: K): O[K]
                     └──┬──┘              └┬┘   └─┬─┘
                    키를 좁힌다         받은 키   그 키의 값 타입

    get(user, "name")   ->  string
    get(user, "age")    ->  number
    get(user, "nope")   ->  TS2345  허용 키 목록이 찍힌다
    get(user, 변수)      ->  TS2345  ★ 컴파일 타임에 모르면 못 쓴다
```

비용 — 키가 **동적이면 못 쓴다.** 그때는 `Record` 로 받고 좁히는 쪽이 정직하다.

### (3) ★★★ 제약이 있어도 그 타입의 값을 안에서 못 만든다 — 유명한 함정

**언제 쓰나** — 「제약을 `Point` 로 걸었는데 `{x:0,y:0}` 을 반환하면 에러가 난다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ 진단이 **두 건**뿐이고 8행이 이 주제 전체의 급소다.\
  「Type '{ x: number; y: number; }' is not assignable to type 'T'.」\
  연쇄 설명이 이유를 **한 줄로 적어 준다** —\
  「'{ x: number; y: number; }' is assignable to the constraint of type 'T', **but 'T' could be instantiated with a different subtype of constraint 'Point'**.」
- ★★★ 그 문장이 제약의 정의다. **`T` 는 `Point` 「이상」** 이므로 `Point3`(x·y·z)일 수도 있다.\
  그런데 함수는 `{x:0,y:0}` 만 만들었다 — **`z` 가 없다.** 호출자가 `Point3` 을 기대했다면 거짓말이 된다.
- ★★ **12행 `readOnly` 는 조용하다.** 읽는 것은 언제나 안전하다 — 모든 후보가 `x`·`y` 를 가진다.
- ★★ **16행 `returnsConstraint` 도 조용하다.** 반환 타입을 `T` 가 아니라 **`Point` 로 낮추면** 만들 수 있다.\
  대신 호출자는 `Point` 만 돌려받는다.
- ★★★ 20행이 **진짜 고침**이다. `{ ...p, x: 0 }` 는 통과한다 —\
  25행 탐침이 그 이유를 말한다. 그 식의 타입이 **`T & { x: number; }`** 라서 `T` 에 대입된다.\
  **스프레드는 「받은 것을 그대로 두고 덮어쓰기」** 라서 `z` 가 보존된다.
- ★ 32행이 그 결과다 — `spreadIn(point3)` 가 **`Point3` 로 그대로** 돌아온다.

```text
  같은 "만들기"인데 갈리는 세 길

  ① return { x: 0, y: 0 };              T 자리   ->  TS2322  ★ z 를 잃는다
  ② return { x: 0, y: 0 };              Point 자리 -> 통과    ★ 대신 T 를 잃는다
  ③ return { ...p, x: 0 };              T 자리   ->  통과    ★ T & { x: number } 라서
                                                            ★ z 가 보존된다
```

비용 — 스프레드는 **얕은 복사**다. 중첩 객체는 공유된다.

### (4) ★★ 기본 타입 인자 — 안 적으면 그것이 쓰인다

**언제 쓰나** — 제네릭 타입을 쓸 때마다 인자를 적기 번거로울 때([**19번 주제**](../19-generics-basics/) 3절 `TS2314`).

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **여덟 건**이고 그중 여섯이 탐침이다.
- 8·9행 — `BoxDefault` 는 **`BoxDefault<string>`** 이 되고, 적으면 그것이 쓰인다.\
  ★ [**19번 주제**](../19-generics-basics/) 3절의 `TS2314` 가 **사라진다** — 기본값이 있으면 인자를 안 적어도 된다.
- 15행 — 제약과 기본값을 **같이** 달 수 있다. `Bounded` 가 `Bounded<{ id: number; name: string; }>` 이다.
- ★★★ 17행이 규칙이다. **기본값도 제약을 지켜야** 한다 — `T extends number = string` 은 **`TS2344`** 다.\
  「Type 'string' does not satisfy the constraint 'number'.」
- ★★ 24·25행 — 함수에도 기본 타입 인자를 달 수 있다. 인자를 안 주면 **`boolean`** 으로 고정되고,\
  주면 추론이 **이긴다**(`string`). ★ 즉 함수의 기본값은 **「추론이 실패했을 때의 대비책」** 이다.
- ★★ 32행 — 기본값이 **앞의 타입 매개변수를 참조**할 수 있다. `Ordered<A, B = A>` 에 `<number>` 만 주면 `Ordered<number, number>` 다.
- ★★★ 34행이 그 한계다. **뒤에 올 것은 못 참조한다** — `TS2744`, 「Type parameter defaults can only reference previously declared type parameters.」

비용 — 기본값을 두면 **`TS2314` 로 잡히던 실수가 조용히 기본값으로 흘러간다**([**19번 주제**](../19-generics-basics/) 4절의 「부분 고정」).

### (5) ★★ 재귀적 제약 — `T` 가 자기를 가리킨다

**언제 쓰나** — 트리·JSON 처럼 **자기 자신을 품는** 구조를 제약으로 적을 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **여섯 건**이다.
- 8·9행 — `T extends Record<string, T>` 는 **성립한다.** `Tree` 타입도, 빈 객체 `{}` 도 통과한다.
- ★★ 11행 — `treeOf({ a: 1 })` 은 막힌다. 진단이 `Type 'number' is not assignable to type '{ a: number; }'` 다 —\
  **`T` 가 `{ a: number }` 로 추론된 뒤 그 값이 다시 `T` 여야 한다**는 요구가 안 맞는다. 재귀가 실제로 작동한다.
- ★★★ 25행이 더 쓸모 있는 꼴이다. `T extends Comparable<T>` — **자기를 비교할 수 있는 것만** 받는다.\
  Java 의 `<T extends Comparable<T>>` 와 **글자까지 닮았다**(Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번**).
- ★★ 27행 — `maxOf(1, 2)` 는 막힌다. 진단이 `Comparable<1 | 2>` 라고 **추론 결과를 그대로 보여 준다** —\
  ★ 여기서도 [**19번 주제**](../19-generics-basics/) 2절의 규칙이 보인다. 스칼라 둘이 **리터럴 유니온**으로 모였다.
- ★ 29행 — `type Json = … | Json[] | { [k: string]: Json }` 처럼 **타입 별칭의 재귀**는 제약 없이도 된다. 깊이 한계는 **안 쟀다.**

비용 — 재귀 제약은 **추론이 어려워진다.** 진단 문구도 길어진다.

### (6) ★★ Rust 는 어디서 막나 — 같은 질문, 다른 답

**언제 쓰나** — 「TS 의 제약이 다른 언어의 바운드와 같은 것인가」를 가를 때.

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

그림 해설 — 한 단계에 한 문장.

- 에러가 **세 건**이고 각각 TS 의 다른 자리와 짝이 된다.
- ★★ 15행 `E0277` — 바운드 없는 `T` 를 `format!` 에 쓰면 **정의 자리**에서 막힌다.\
  **TS 의 1절 3행 `TS2339` 와 같은 자리**다 — 둘 다 **몸통을 정의 시점에 검사**한다.\
  ★ 「Rust 는 정의 자리, TS 는 사용 자리」는 **틀린 요약**이다. 둘 다 **양쪽에서** 막는다.
- ★★★ 28행 `E0277` 이 **진짜 차이**다. `struct Loud` 에는 `fmt` 라는 메서드가 **있는데도** 막힌다 —\
  「the trait `std::fmt::Display` is not implemented for `Loud`」.\
  **Rust 의 바운드는 이름으로 걸린다**(nominal) — 어딘가에 `impl Display for Loud` 가 **선언돼 있어야** 한다.
- ★★★ TS 는 정반대다. 1절 22행의 `class Rope` 는 **아무것도 `implements` 하지 않았는데** `{ length: number }` 제약을 통과했다.\
  **TS 의 제약은 모양으로 걸린다**(structural, [**05번 주제**](../05-structural-typing/)).
- ★★★ 22행이 두 번째 차이다. **Rust 는 함수에 기본 타입 인자를 못 단다** —\
  「defaults for generic parameters are not allowed here」. TS 는 **함수에도 달 수 있다**(4절 24행).
- ★ 그리고 Rust 는 그 진단을 **`deny(future_incompatible)` 경고 문맥**으로 낸다 — 옛날에는 받아 줬다는 뜻이다.

```text
  같은 질문, 세 언어

                     바운드/제약이 걸리는 기준     기본 타입 인자를 함수에
  TypeScript         ★ 모양 (structural)          ★ 된다
  Rust               ★ 이름 (impl 선언 필요)       ✗ "not allowed here"
  Java               이름 (implements/extends)     ✗ 문법 자체가 없다
```

- ★★ **Java 쪽은 이 배치에서 안 던졌다** — 이 머신에 `javac` 가 없다. 형제 문서가 정본이다:\
  Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번**(제네릭 선언)·**18번**(와일드카드와 PECS).
- ★ 그래서 이 절의 Java 행은 **형제 문서를 근거로 한 것**이고 **이 배치의 실측이 아니다.** 갈라 적는다.

비용 — 구조적 제약은 **편하지만 우연히 맞는 모양도 통과**시킨다. 명목 구분이 필요하면 브랜드 타입을 쓴다([**05번 주제**](../05-structural-typing/)).

### (7) ★ `strict` 대조 — 한 파일만 갈린다

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.20a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.20b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.20c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.20d.ts    exit 1 = exit 1 · ★ 출력이 다르다
ex.20e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict false ex.20d.ts (tsc exit=1) =====
ex.20d.ts(8,7): error TS2322: Type 'BoxDefault<string>' is not assignable to type 'null'.
ex.20d.ts(9,7): error TS2322: Type 'BoxDefault<number>' is not assignable to type 'null'.
ex.20d.ts(15,7): error TS2322: Type 'Bounded<{ id: number; name: string; }>' is not assignable to type 'null'.
ex.20d.ts(17,41): error TS2344: Type 'string' does not satisfy the constraint 'number'.
ex.20d.ts(24,7): error TS2322: Type '{ value: boolean; }' is not assignable to type 'null'.
ex.20d.ts(25,7): error TS2322: Type '{ value: string; }' is not assignable to type 'null'.
ex.20d.ts(32,7): error TS2322: Type 'Ordered<number, number>' is not assignable to type 'null'.
ex.20d.ts(34,25): error TS2744: Type parameter defaults can only reference previously declared type parameters.
```

- ★★ 다섯 파일 중 **`ex.20d.ts` 하나만** 갈린다. 나머지 넷은 **글자 하나까지 같다.**
- ★★★ 갈린 자리는 **제약·기본값과 무관**하다. 24·25행의 탐침이 `{ value: boolean \| undefined; }` 대 `{ value: boolean; }` 다 —\
  선택 매개변수 `value?: T` 의 `undefined` 가 **`strictNullChecks` 에만 달려 있다**(목록의 **40번 주제**).
- ★ 즉 **제약·기본 타입 인자의 규칙 자체는 `strict` 와 무관**하다. 갈린 것은 **곁다리**다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  function f<T extends { length: number }>(x: T): number { … }  ★ 하한 선언
  function get<O, K extends keyof O>(o: O, k: K): O[K] { … }    ★ 키가 값 타입을 정한다
  interface Box<T = string> { value: T }                        ★ 기본 타입 인자 (2.3)
  interface B<T extends { id: number } = { id: number; name: string }> { … }  ★ 둘 다
  interface Ordered<A, B = A> { … }                             ★ 앞의 것을 참조
  interface Backwards<A = B, B = number> { … }                  ✗ TS2744
  interface Bad<T extends number = string> { … }                ✗ TS2344
  function tree<T extends Record<string, T>>(t: T): T { … }     ★ 재귀 제약
  function max<T extends Comparable<T>>(a: T, b: T): T { … }    ★ 자기 참조 바운드
```

**규칙 불릿**

- ★★★ **제약은 하한이다** — `T extends Point` 는 「`Point` 이상」이지 「`Point` 다」가 아니다.
- ★★★ **제약이 없으면 멤버를 하나도 못 쓴다** — `TS2339`(1절 3행). **정의 자리**에 난다.
- ★★★ **제약이 있어도 그 타입의 값을 안에서 못 만든다** — `TS2322` + 「could be instantiated with a different subtype」(3절 8행).
- ★★ **고치는 길 셋** — 반환 타입을 제약으로 낮추거나 · **스프레드**(`{ ...p, x: 0 }` → `T & { x: number }`) · 호출자가 값을 주게 하거나(3절).
- ★★ **`keyof` 제약은 키가 컴파일 타임에 알려져 있을 때만** 쓴다 — `string` 변수는 `TS2345`(2절 15행).
- ★★★ **기본값도 제약을 지켜야 한다** — `TS2344`(4절 17행).
- ★★ **기본값은 앞의 타입 매개변수만 참조할 수 있다** — `TS2744`(4절 34행).
- ★★ **함수의 기본 타입 인자는 「추론 실패 시의 대비책」** 이다 — 추론이 되면 추론이 이긴다(4절 24·25행).
- ★★ **제약은 구조적**이다 — `implements` 없이 모양만 맞으면 통과한다(1절 22행). **Rust 는 이름으로 건다**(6절).
- ★ **재귀 제약은 작동한다** — `T extends Record<string, T>` 도 `T extends Comparable<T>` 도(5절).

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 제약 없는 T 의 멤버 사용   ->  TS2339  Property 'length' does not exist on type 'T'.
2) T 자리에 리터럴을 만듦      ->  TS2322  … 'T' could be instantiated with a different
                                           subtype of constraint 'Point'.
3) 기본값이 제약을 어김        ->  TS2344  Type 'string' does not satisfy the constraint 'number'.
4) 기본값이 뒤의 매개변수 참조 ->  TS2744  Type parameter defaults can only reference previously
                                           declared type parameters.
```

## 어디서 틀리나

- ★★★ 「**제약을 걸었으니 그 타입의 값을 만들어 돌려주면 되겠지**」 — 안 된다(3절 8행). **이 주제의 급소다.**
- ★★★ 「**제약은 `T` 가 정확히 그 타입이라는 뜻이겠지**」 — **하한**이다. 더 넓은 것도, 더 많은 필드를 가진 것도 들어온다.
- ★★ 「**스프레드도 똑같이 막히겠지**」 — **통과한다.** `T & { x: number }` 가 되기 때문이다(3절 20·25행).
- ★★ 「**`keyof` 제약이면 아무 문자열이나 받겠지**」 — `string` 변수는 `TS2345` 다(2절 15행).
- ★★★ 「**기본값은 아무거나 둬도 되겠지**」 — 제약을 어기면 `TS2344` 다(4절 17행).
- ★★ 「**기본값이 있으면 부분 추론이 되겠지**」 — **부분 고정**이다([**19번 주제**](../19-generics-basics/) 4절).
- ★★ 「**Rust 는 정의 자리에서만 막고 TS 는 사용 자리에서만 막겠지**」 — **둘 다 양쪽에서 막는다**(6절 15·28행).\
  진짜 차이는 **모양이냐 이름이냐**다.
- ★★ 「**Rust 처럼 함수에 기본 타입 인자를 못 달겠지**」 — TS 는 **달 수 있다**(4절 24행 · 6절 22행).
- ★ 「**제약을 걸면 방출물이 달라지겠지**」 — **잴 것이 없다.** 제약은 전부 타입 층이다(0절).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 제약 없는 `T` 는 멤버가 없다(`TS2339`) | 1절 3행 |
| **언어 보장** | ★★★ 제약 타입의 값을 `T` 자리에 **못 만든다**(`TS2322`) | 3절 8행 |
| **언어 보장** | 스프레드는 `T & {…}` 가 되어 **통과한다** | 3절 20·25행 |
| **언어 보장** | 기본값도 **제약을 지켜야** 한다(`TS2344`) | 4절 17행 |
| **언어 보장** | 기본값은 **앞의 것만** 참조한다(`TS2744`) | 4절 34행 |
| **언어 보장** | 제약은 **구조적**이다 | 1절 22행 — `implements` 없음 |
| **★ 부적용 — 방출된 JS** | ★★ **잴 것이 없다** — 제약은 방출에 아무것도 더하지 않는다 | 0절 |
| **★ 설정에 달림** | ★ `ex.20d.ts` 한 파일 — **`strictNullChecks`**(제약과 무관한 곁다리) | 7절 |
| **다른 언어(rustc 1.92.0)** | Rust 는 **이름으로** 건다 · 함수에 기본 타입 인자 **금지** | 6절 28·22행 |
| **★ 이 배치의 실측이 아님** | ★★ **Java 행** — `javac` 가 이 머신에 없다 | 형제 문서(Java 17·18·19)가 근거다 |
| **이 판(7.0.2)의 관찰** | 진단 **문구** 전문 | 코드(`TS2339`·`TS2322`·`TS2344`·`TS2744`)가 더 오래 간다 |
| **이 판의 관찰** | ★ `keyof` 키 목록의 **사전순** 정렬 | 5회 재실행에서 같았다 — **관찰이지 보장이 아니다** |
| **안 잰 것** | 재귀 제약의 **깊이 한계·검사 시간** | 재지 않았다 |

★★★ **이 주제에는 「진단 0줄」 블록이 하나도 없다** — 던진 여섯 파일이 전부 무언가를 말했다.
[**18번**](../18-this-parameter-types/)·[**19번**](../19-generics-basics/)과 다른 점이고, **제약이 순수 타입 층**이라 `.js` 창이 부적용인 것과 짝이 된다.

## 언제 쓰고 언제 안 쓰나

| 제약을 건다 | 안 건다 |
|---|---|
| 몸통에서 **멤버를 써야** 할 때 | `T` 를 **그대로 돌려주기만** 할 때 |
| 호출자의 실수를 **인자 자리에서** 막고 싶을 때 | 아무거나 받아야 할 때 — 그때는 `unknown` |
| ★ **리터럴을 살리고 싶을 때**(`T extends string`) | 배열·객체 리터럴까지 살려야 할 때 — **[21](../21-inference-control-const-and-noinfer/)의 `const` 가 맞다** |
| 키 안전한 접근(`K extends keyof O`) | 키가 **동적**일 때 — `Record` 로 받고 좁혀라 |

| 기본 타입 인자를 둔다 | 안 둔다 |
|---|---|
| 대부분의 호출이 **한 타입**일 때 | 어느 타입이 기본인지 **의견이 갈릴 때** |
| 제네릭 타입을 **자주 이름으로** 쓸 때(`TS2314` 를 줄인다) | ★ 실수가 **조용히 기본값으로 흐르면 곤란할 때** |
| 뒤쪽 매개변수가 앞쪽에서 **따라오는** 구조(`<A, B = A>`) | 함수에서 **추론을 기대**할 때 — 기본값은 대비책일 뿐이다 |

## 핵심 문장

1. **제약은 상한이 아니라 하한이다** — `T extends Point` 는 「`Point` 이상」이다.
2. **제약 없는 `T` 는 아무 멤버도 없고, 그 진단은 정의 자리에 난다.**
3. **제약이 있어도 그 타입의 값을 `T` 자리에 만들어 낼 수는 없다** — 이 주제의 급소다.
4. **스프레드는 예외다** — `{ ...p, x: 0 }` 는 `T & { x: number }` 라서 통과한다.
5. **기본 타입 인자도 제약을 지켜야 하고, 앞의 매개변수만 참조할 수 있다.**
6. **TS 의 제약은 모양으로 걸리고 Rust 의 바운드는 이름으로 걸린다** — 둘 다 정의·사용 양쪽에서 막는다.

## 관련 자료

- [**19번 주제** — 제네릭 기본](../19-generics-basics/) — **19 → 20 → 21 은 한 사슬**이다. 그쪽 2절의 고장을 **제약이 절반 고친다.**
- [**21번 주제** — 추론 제어](../21-inference-control-const-and-noinfer/) — ★★★ 나머지 절반. `const T extends …` 가 **이 주제의 제약과 싸우는** 자리가 거기다.
- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — 1절 22행과 6절의 **모양 대 이름**은 그쪽이 정본이다.
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — 「제약이 리터럴을 살린다」의 반대쪽 길.
- [**16번 주제** — 함수 타입과 오버로드](../16-function-types-and-overloads/) · [**17번 주제** — 변성과 매개변수 양립성](../17-variance-and-parameter-compatibility/) — 시그니처 표기와 대입 방향은 그쪽.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번** — [제네릭 선언 — 타입 파라미터·바운드](../../../java/syntax/17-generic-declarations/). ★★ 5절의 `T extends Comparable<T>` 가 **글자까지 닮았다.**
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **18번** — [와일드카드와 PECS](../../../java/syntax/18-wildcards-pecs/). TS 에는 와일드카드가 **없다** — 대신 제약과 [**17번 주제**](../17-variance-and-parameter-compatibility/)의 변성으로 푼다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번** — [트레이트 정의·구현](../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/). 6절의 `impl Display for …` 가 **왜 필요한지**는 그쪽.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **31번**(제네릭과 트레이트 경계·`where`·단형화) — 아직 폴더가 없다.
- 목록의 **22번 주제**(`keyof` 와 인덱스 접근 타입) — 2절의 `keyof O`·`O[K]` 는 그쪽이 정본이다. 여기서는 **제약으로 쓰는 것**까지만.
- 목록의 **40번 주제**(`strictNullChecks` 의 파급) — 7절에서 갈린 칸의 원인.

## 용어 풀이

> **제약(constraint)** — `T extends U`. 「`T` 는 **`U` 이상**」이라는 **하한** 선언이다.\
> 몸통에서 `U` 의 멤버를 쓸 수 있게 되고, 인자 자리에서 `U` 가 아닌 것을 막는다.

> **`TS2339`** — 「Property 'x' does not exist on type 'T'.」\
> **제약이 없어서** 아무 멤버도 없는 `T` 에 접근했을 때. **정의 자리**에 난다.

> **「could be instantiated with a different subtype」** — `TS2322` 의 연쇄 설명 줄.\
> 「`T` 가 제약보다 **더 좁은 것**일 수도 있다」는 뜻이고, 그래서 제약 타입의 값을 `T` 자리에 못 넣는다.

> **기본 타입 인자(generic parameter default)** — `<T = string>`(TS 2.3).\
> 인자를 안 적으면 그것이 쓰인다. **제약을 지켜야 하고**(`TS2344`) **앞의 매개변수만** 참조할 수 있다(`TS2744`).

> **명목 대 구조(nominal vs structural)** — 「이름이 맞아야 하나, 모양이 맞으면 되나」.\
> **Rust·Java 는 명목**(선언이 있어야 한다), **TS 는 구조**([**05번 주제**](../05-structural-typing/)).

## 더 들어가면

- **왜 「하한」인가** — 제약을 **상한**으로 읽으면 `T` 를 `Point` 로 취급해도 안전해야 한다. 그런데 호출자는 `Point3` 을 넘길 수 있고, 함수가 `Point` 를 만들어 돌려주면 **호출자가 잃어버린 `z` 를 찾다 터진다.** 그래서 TS 는 `T` 를 **끝까지 미지수로 둔다** — 읽기만 허용하고 만들기는 막는 3절의 비대칭이 거기서 나온다. 같은 비대칭이 [**17번 주제**](../17-variance-and-parameter-compatibility/)의 변성에도 있다.
- **스프레드가 왜 통과하나** — `{ ...p, x: 0 }` 의 타입은 **`T & { x: number }`** 다(3절 25행). 교차는 `T` 의 **부분 타입**이므로 `T` 자리에 들어간다 — `z` 가 있었으면 `T` 안에 그대로 있다. 즉 「새로 만든 것」이 아니라 「**받은 것에 덧칠한 것**」이라서 통과한다. 이 규칙은 TS 3.2 의 제네릭 스프레드 지원 이후의 것이고, **이 판에서 던져서 확인했다.**
- **와일드카드가 없는 대신** — Java 의 `? extends T`·`? super T` 에 해당하는 표기가 TS 에는 없다. 대신 ① **제약**(`<T extends U>`)으로 읽기 쪽을, ② **변성**([**17번 주제**](../17-variance-and-parameter-compatibility/))과 `readonly` 로 쓰기 쪽을 가른다. 어느 쪽이 나은지는 이 배치에서 **논증하지 않았다** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **18번** 과 나란히 읽을 자리다.
- **재귀 제약의 한계** — `T extends Record<string, T>` 가 실제로 도는 것은 5절에서 봤지만 **깊이 한계와 검사 시간은 안 쟀다.** 조건부 타입의 재귀 한계는 목록의 **25번 주제**, 타입 수준 성능은 목록의 **45번 주제**다.
- **명목 구분이 필요할 때** — 1절 22행처럼 **우연히 모양이 맞는 것**까지 통과시키는 것이 곤란하면 브랜드 타입을 쓴다([**05번 주제**](../05-structural-typing/)). Rust 처럼 「선언이 있어야 한다」를 흉내 내는 수다 — **이 배치에서는 안 던졌다.**
