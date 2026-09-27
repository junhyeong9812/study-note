# ts/syntax/19 — 제네릭 기본 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html) ·
> [Handbook — More on Functions: Generic Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html#generic-functions) ·
> [Handbook — Type Inference](https://www.typescriptlang.org/docs/handbook/type-inference.html).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·방출 전문·`.d.ts` 전문·실행 출력은 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version (sh exit=0) =====
Version 7.0.2
v18.19.1
```

> ★★★ 「**`tsc` 가 7.0.2 다 — 5.x 가 아니다.**」 블록은 **옵션을 배너에 적힌 것만** 준 결과다.
> 이 배치는 `-t es2022 --strict` 를 **전부 명시**했다 — 7.0 의 기본값에 기대지 않고 배너만 보고 다시 던질 수 있게 했다.
> **버전** — 제네릭은 TS **초판(1.0)** 부터다. 이 주제에는 최신 기능이 없다 —
> 다만 **8절의 `--strict` 대조**는 이 판의 기본값(`true`)을 전제로 읽는다.
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
- ★★★ 창이 하나 더 있다 — **`--declaration` 으로 뽑은 `.d.ts`**(7절). **여러 줄을 한 번에 훑을 때** 그쪽이 낫다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 방출된 `.js` 전문 · `node` 출력 | 이 주제에 난수·시각이 한 칸도 없다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | ★★ 유니온 원소의 **순서**(`'"가" \| "나"'`) | 같은 입력이면 같다 — 5회 재실행 동일 |
| **★ 설정에 달렸다** | ★ **없다** — 다섯 파일 전부 `--strict false` 와 같다(8절) | 제네릭 추론은 `strict` 와 무관했다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **★ 부적용** | 「여러 번 돌려 본다」 | 난수·시각·순서 비보장이 **한 칸도 없다** |
| **안 잰 것** | 타입 매개변수 개수가 **검사 시간**에 주는 영향 | 재지 않았다 |

> ★ 「**소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다**」 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 6·7절의 `tsc` 는 **진단이 0줄**이다 — 그 블록도 **명령과 종료 코드까지** 캡처했다.

## 한눈에 — 쉽게 말하면

**타입 매개변수는 「부를 때 채워지는 빈칸」이다. `any` 는 빈칸을 없애 버리고, 제네릭은 빈칸을 기억한다.**

| 비유 | 실체 |
|---|---|
| 택배 상자의 **「내용물」 칸** | 타입 매개변수 `T` |
| 보낼 때 그 칸을 **적는다** | `identity<number>(3)` — 명시 |
| 안 적으면 **내용물을 보고 적어 준다** | `identity(3)` — 추론 |
| ★★ 그런데 **「사과 3개」가 아니라 「과일」이라고 적힌다** | 배열·객체 안의 리터럴이 넓어진다(2절) |
| `any` 는 **칸을 아예 안 적는 것** | 들어간 것도 나온 것도 모른다 |
| 상자는 **뜯는 순간 칸이 사라진다** | 방출물에 타입 인자가 한 글자도 없다(6절) |

- ★★★ 한 줄로 — 「**제네릭은 입력과 출력을 잇는다. `any` 는 그 줄을 끊는다.**」
- ★★ 그리고 이 주제의 **고장 하나**가 [**21번 주제**](../21-inference-control-const-and-noinfer/)의 과녁이다 — 2절이 그것이다.

```text
  같은 호출, 세 가지 적는 법

  function identity<T>(x: T): T { … }

    identity(3)                   T <- 3        추론 (인자에서 온다)
    identity<number>(3)           T <- number   명시
    identity<string|number>(3)    T <- string|number  명시가 추론을 이긴다

  ★ 세 줄의 반환 타입이 전부 다르다 — 3 · number · string | number
```

```text
  any 와 무엇이 다른가

  function identity<T>(x: T): T      function anyIdentity(x: any): any
          │                                   │
          ▼  T 가 기억된다                     ▼  기억할 것이 없다
     identity(3)  ->  3                  anyIdentity(3)  ->  any
          │                                   │
          ▼                                   ▼
     그 뒤로 number 로만 쓴다            그 뒤로 아무거나 쓴다 (검사가 꺼진다)
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **타입 인자는 어디서 오나** — 추론과 명시를 **나란히 던져** 반환 타입이 어떻게 갈리는지 본다(1절).
2. **추론이 어디까지 좁히나** — ★★★ **배열·객체 리터럴에서 넓어진다.** [**21번 주제**](../21-inference-control-const-and-noinfer/)가 고칠 고장을 **여기서 먼저 본다**(2절).
3. **런타임에 타입 인자가 있나** — 방출된 `.js` 를 꺼내 **직접 확인**하고 Java·Kotlin 과 견준다(6절).

★ [**18번 주제**](../18-this-parameter-types/)가 함수 시그니처의 **첫 칸**을 다뤘다면 여기는 **꺾쇠 안의 칸**이다.
★★ **19 → 20 → 21 은 한 사슬**이다 — 여기서 **고장**을 보고, [**20번 주제**](../20-generic-constraints-and-defaults/)에서 **제약**을 걸고, [**21번 주제**](../21-inference-control-const-and-noinfer/)에서 **고친다.**

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 성질 |
|---|---|---|
| ★★★ **`null` 탐침** | 컴파일러가 **계산한** 타입 인자 | **계산된 것** |
| ★★ **`--declaration` 의 `.d.ts`** | 추론 결과를 **여러 줄 한꺼번에** | **적은 것** — 정규화하지 않는다 |
| ★★★ **방출 `.js` + `node` 실행** | 런타임에 **무엇이 남는가** | 사실 |
| ★ **진단 전문** | 어디서 막히나 — `TS2558`·`TS2314`·`TS2302` | 사실 |

★★ 7절에서 앞의 두 창이 **같은 사실을 다른 형식으로** 말한다 — 그리고 **한 자리에서 글자가 갈린다.**

비용 — 컴파일 세 번 + 실행 한 번.

### (1) ★★ 타입 인자는 인자에서 오거나 꺾쇠에서 온다

**언제 쓰나** — 「`any` 를 쓰지 말라는데 그럼 뭘 쓰나」에서 막힐 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **여섯 건**이고 그중 다섯이 탐침이다.
- ★★★ 9·10·11행이 이 절의 전부다. **같은 인자 `3`** 인데 반환 타입이 셋 다 다르다 —\
  추론은 **`3`**, `<number>` 는 **`number`**, `<string | number>` 는 **`string | number`** 다.
- ★★ 즉 **명시가 추론을 이긴다.** 꺾쇠를 적으면 인자는 **검사만** 받는다 — 28행이 그 증거로 `TS2345` 다.
- ★★★ 16행 `anyIdentity(3)` 은 **진단이 없다.** `any` 는 `null` 에도 들어가므로 탐침이 안 걸린다 —\
  **「아무 데나 들어간다」가 곧 `any` 의 정의**다([**04번 주제**](../04-any-unknown-never-void/)).
- ★ 21행 — 타입 매개변수가 둘이면 각각 따로 추론된다. `pair("가", 1)` 이 **`[string, number]`** 다.\
  ★★ 여기서 **`"가"` 가 아니라 `string`** 인 것이 2절의 예고다 — 튜플 자리에서 넓어졌다.
- ★ 26행 — 배열의 원소가 섞이면 **유니온**으로 합쳐진다. `firstOf([1, "가"])` 가 `string | number` 다.

> **타입 매개변수(type parameter)** — 선언 쪽의 빈칸(`<T>`).\
> **타입 인자(type argument)** — 호출 쪽에서 그 칸을 채우는 실제 타입(`<number>`).

비용 — 명시하면 **인자 쪽 추론을 포기**하게 된다. 4절의 「전부 아니면 전무」와 이어진다.

### (2) ★★★ 추론은 리터럴로 좁혀지지 않는다 — 21 이 고칠 고장

**언제 쓰나** — 「배열을 넘겼더니 리터럴 유니온이 아니라 `string[]` 이 나온다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ 이 절은 **고장을 전시하는 절**이다. [**21번 주제**](../21-inference-control-const-and-noinfer/)가 이 줄들을 하나씩 고친다.
- ★★★ 10행과 11행을 나란히 읽어라. **같은 함수 `keep`** 인데\
  `keep("가")` 는 **`"가"`**(리터럴이 살아남는다)이고 `keep(["가","나"])` 는 **`string[]`**(원소가 넓어진다)이다.
- ★★★ 그러므로 「**제네릭 추론은 리터럴을 안 지킨다**」는 **틀린 요약**이다.\
  정확히는 「**스칼라 인자는 지키고, 배열·객체 리터럴의 속은 넓어진다**」다 — 12행도 `{ mode: string; }` 이다.
- ★★ 5행 — `firstOf(["가","나"])` 는 원소 타입을 뽑으므로 **`string`** 이다. 같은 고장의 다른 얼굴이다.
- ★★ 15행이 **호출자 쪽 고침**이다. `as const` 를 붙이면 `readonly ["가", "나"]` 가 된다 —\
  ★ 다만 **호출자가 매번 적어야** 한다([**11번 주제**](../11-literal-types-and-as-const/)).
- ★ 18행 — `let` 에 담아 넘기면 **`string`** 이다. 변수에 담는 순간 이미 넓어져 있다.
- ★★★ 23행이 절반의 고침이다. `T extends string` 으로 제약을 걸면 **`"auto"`** 가 살아남는다 —\
  **제약이 추론을 좁힌다.** 그 규칙 전체는 [**20번 주제**](../20-generic-constraints-and-defaults/)다.

```text
  무엇이 좁혀지고 무엇이 넓어지나 (실측)

  keep("가")              ->  "가"          ★ 스칼라는 지켜진다
  keep(["가","나"])       ->  string[]      ★ 배열의 속이 넓어진다
  keep({ mode: "auto" })  ->  { mode: string }   ★ 객체의 속도
  keep(["가","나"] as const) -> readonly ["가","나"]  ← 호출자가 고친다 (11번)
  pickMode("auto")        ->  "auto"        ← 제약이 고친다 (20번)
                                             ← 정의자가 고치는 법은 21번
```

비용 — **호출자가 `as const` 를 잊으면 조용히 넓어진다.** 이 「조용함」이 21 의 존재 이유다.

### (3) ★★ 제네릭 함수 타입과 제네릭 인터페이스

**언제 쓰나** — 「`<T>` 를 인터페이스 이름에 다나, 호출 시그니처에 다나」를 고를 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **다섯 건**이다 — 16·17·18·20·21행.
- ★★★ 16·17·18행이 차이를 보인다. `GenericFn`(호출 시그니처에 `<T>`)은 **부를 때마다** 채워져\
  `g1(3)` 이 **`3`**, `g3(true)` 가 **`true`** 다.\
  `FnOfT<string>`(이름에 `<T>`)은 **타입을 쓸 때** 채워져 `g2("가")` 가 **`string`** 으로 고정된다.
- ★★ 20행 — 이미 `string` 으로 고정된 자리에 `(x: number) => number` 를 넣으면 `TS2322` 다.\
  연쇄 설명이 「Types of parameters 'x' and 'x' are incompatible.」로 **매개변수 쪽**을 짚는다([**17번 주제**](../17-variance-and-parameter-compatibility/)).
- ★★★ 21행이 결정적이다. `FnOfT` 를 **인자 없이** 쓰면 `TS2314` — 「Generic type 'FnOfT<T>' requires 1 type argument(s).」\
  **이름에 단 `<T>` 는 반드시 채워야 한다.** 호출 시그니처에 단 `<T>` 는 그럴 필요가 없다.
- ★ `type ArrowGeneric = <T>(x: T) => T;` 는 `GenericFn` 과 **같은 뜻**이다 — 표기만 다르다.

```text
  꺾쇠를 어디에 다느냐

  interface GenericFn { <T>(x: T): T }      ★ 호출마다 채워진다  — GenericFn 으로 쓴다
  interface FnOfT<T>  { (x: T): T }         ★ 타입 쓸 때 채운다  — FnOfT<string> 으로 쓴다
                                                              FnOfT 만 쓰면 TS2314
```

비용 — 이름에 달면 **쓰는 자리마다 인자를 적어야** 한다. 기본 타입 인자로 덜 수 있다([**20번 주제**](../20-generic-constraints-and-defaults/)).

### (4) ★★ 타입 인자는 전부 적거나 하나도 안 적거나다

**언제 쓰나** — 「하나만 적고 나머지는 추론시키고 싶다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **세 건**이다 — 8·13·14행.
- ★★★ 8행 — `pair<string>("가", 1)` 이 **`TS2558`** 다. 「Expected 2 type arguments, but got 1.」\
  **부분 추론은 없다.** 하나를 적는 순간 **나머지도 전부** 적어야 한다.
- ★★ 6·7행은 조용하다 — **전부 적거나**(`pair<string, number>`) **하나도 안 적거나**(`pair("가", 1)`)는 둘 다 된다.
- ★★★ 13·14행이 **빠져나가는 길**이다. `B` 에 **기본 타입 인자**가 있으면 `withDefault<string>` 이 통과한다 —\
  단 `B` 가 추론되지 않고 **기본값 `boolean` 으로 고정**된다. 그래서 `1` 을 넘긴 13행이 `TS2345` 이고\
  14행 탐침이 **`[string, boolean]`** 이다.
- ★ 즉 기본값은 「**부분 추론**」이 아니라 「**부분 고정**」이다. 규칙은 [**20번 주제**](../20-generic-constraints-and-defaults/)에서 본다.

비용 — 타입 매개변수를 늘릴수록 **명시 호출이 길어진다.** 그래서 추론이 되게 설계하는 쪽이 낫다.

### (5) ★★ 제네릭 클래스 — 인스턴스마다 채워지고 `static` 에는 못 온다

**언제 쓰나** — 컨테이너를 만들 때.

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

그림 해설 — 한 단계에 한 문장.

- 진단이 **다섯 건**이다 — 9·15·16·17·19행.
- ★★★ 9행 — `static empty: T;` 가 **`TS2302`** 다. 「Static members cannot reference class type parameters.」\
  **`T` 는 인스턴스마다 정해지는데 `static` 은 클래스에 하나뿐**이라 채울 값이 없다.
- 15·16행 — `new Box("가")` 는 추론으로 **`Box<string>`**, `new Box<number>(1)` 은 명시로 **`Box<number>`** 다.\
  생성자 인자에서 추론된다는 점이 함수와 같다.
- ★★ 17행 — `b1.map((s) => s.length)` 가 **`Box<number>`** 다. 메서드의 `<U>` 는 **메서드 호출마다** 따로 채워진다.\
  `s` 가 `string` 으로 들어온 것은 **클래스의 `T` 가 이미 `string`** 이기 때문이다.
- ★ 19행 — `new Box<number>("가")` 는 `TS2345` 다. 명시한 인자가 **검사 기준**이 된다(1절 28행과 같다).

비용 — `static` 자리에는 타입 매개변수를 못 쓴다. 필요하면 **정적 메서드에 따로 `<U>` 를 단다.**

### (6) ★★★ 런타임에 타입 인자는 없다

**언제 쓰나** — 「`T` 로 `new T()` 를 하거나 `if (x instanceof T)` 를 쓰고 싶다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ `tsc` 종료 코드가 **`0`** 이고 진단이 **0줄**이다.
- ★★★ 방출된 `.js` 에 `class Box { … }` 하나뿐이다 — **`<T>` 가 한 글자도 없다.** `firstOf(xs)` 도 마찬가지다.
- ★★★ 실행 출력 1번 줄이 **`true`** 다. `Box<string>` 과 `Box<number>` 의 **생성자가 같은 객체**다 —\
  **런타임에는 `Box` 하나뿐**이고 타입 인자는 존재하지 않는다.
- ★★ 4번 줄이 그 사실을 **소스 글자로** 보여 준다. `firstOf.toString()` 이 `function firstOf(xs) { … }` 다 —\
  꺾쇠가 **없다.**
- ★ 5번 줄 — 인스턴스의 키는 `value` 뿐이다. **타입 흔적을 담는 숨은 필드가 없다.**
- ★★★ 이것은 [**01번 주제**](../01-what-ts-adds-and-erases/)의 결론이 제네릭에 적용된 것이다 — **타입은 지워진다.**

```text
  세 언어의 같은 질문 — "런타임에 T 가 있나"

  TypeScript   방출물에 <T> 가 아예 없다          ★ 이 절의 실측
  Java         컴파일은 하되 소거한다             Java 갈래 19번 (소거·브리지 메서드)
  Kotlin       inline + reified 면 남는다         Kotlin 갈래 12번
```

- ★★ **Java 와 TS 는 「지운다」는 점이 같고 지우는 방식이 다르다** — Java 는 바이트코드에 **시그니처를 남기고**\
  TS 는 **파일 자체가 JS** 라 남길 자리가 없다.
- ★★★ **Kotlin 만 뚫는 길이 있다** — `inline fun <reified T>` 는 **호출 자리에 코드를 펼쳐** `T` 를 실제 클래스로 박는다.\
  TS 에는 그런 장치가 **없다.** 필요하면 **값을 하나 더 받는 수밖에 없다**(생성자·태그 문자열).

비용 — `new T()`·`instanceof T` 를 못 쓴다. 그래서 TS 의 제네릭은 **검사 전용**이다.

### (7) ★★ 두 번째 창 — `.d.ts` 가 추론 결과를 한 번에 적어 준다

**언제 쓰나** — 탐침을 줄줄이 달기 번거로울 때. **여러 줄을 한 번에** 보고 싶을 때.

```ts
// ex.19g.ts
// 두 번째 창 -- 추론 결과를 .d.ts 가 글자로 적어 준다
export function keep<T>(x: T): T {
    return x;
}

export const fromScalar = keep("가");
export const fromArray = keep(["가", "나"]);
export const fromObject = keep({ mode: "auto", retry: 3 });
export const fromAsConst = keep(["가", "나"] as const);

export function pair<A, B>(a: A, b: B): [A, B] {
    return [a, b];
}
export const mixed = pair("가", 1);

export class Box<T> {
    constructor(public value: T) {}
}
export const boxed = new Box("가");
export const mapped = new Box(1).value;
```

```text
===== tsc --pretty false -t es2022 --strict --declaration --emitDeclarationOnly --outDir d19g ex.19g.ts (tsc exit=0) =====
===== 방출된 ex.19g.d.ts =====
export declare function keep<T>(x: T): T;
export declare const fromScalar = "\uAC00";
export declare const fromArray: string[];
export declare const fromObject: {
    mode: string;
    retry: number;
};
export declare const fromAsConst: readonly ["가", "나"];
export declare function pair<A, B>(a: A, b: B): [A, B];
export declare const mixed: [string, number];
export declare class Box<T> {
    value: T;
    constructor(value: T);
}
export declare const boxed: Box<string>;
export declare const mapped: number;
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 종료 코드가 **`0`** 이고 진단이 **0줄**인데도 **추론 결과가 전부 글자로** 나왔다 — 탐침이 한 줄도 없다.\
  **이것이 `.d.ts` 창의 값**이다.
- ★★ 결과가 2절과 **한 글자도 같은 이야기**다 — `fromArray` 는 `string[]`, `fromObject` 는 `{ mode: string; retry: number; }`,\
  `fromAsConst` 만 `readonly ["가", "나"]` 다.
- ★★★ **그런데 한 자리에서 글자가 갈린다.** `fromScalar` 가 **`"가"`** 로 적혀 있다 —\
  탐침은 같은 것을 **`"가"`** 라고 답했다(2절 10행). **`.d.ts` 방출기가 `const` 초기자를 이스케이프한 것**이다.
- ★ 같은 파일 안의 `readonly ["가", "나"]` 는 **이스케이프되지 않았다.** 자리에 따라 다르다.
- ★★ 그래서 판정은 「**값을 읽을 때는 탐침, 목록을 훑을 때는 `.d.ts`**」다.\
  `.d.ts` 는 **적은 것**이고 탐침은 **계산된 것**이다 — 둘이 다르면 **탐침이 기준**이다.
- ★ `boxed` 가 `Box<string>` 으로 적힌 것도 `.d.ts` 의 성질이다 — **별칭·제네릭 이름을 펴지 않는다**([**16번 주제**](../16-function-types-and-overloads/)).

비용 — `--declaration` 이 필요하고 **오류가 있는 파일에서는 신뢰하기 어렵다.**

### (8) ★ `strict` 를 꺼도 전부 같다

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.19a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.19b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.19c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.19d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.19e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★ 다섯 파일 **전부** 종료 코드도 출력도 **글자 하나까지 같다.**
- ★ 제네릭의 **추론 규칙·부분 추론 금지·`static` 제약**은 `strict` 와 **무관**하다. **이 주제에는 설정에 달린 칸이 없다.**
- ★★★ 다만 [**21번 주제**](../21-inference-control-const-and-noinfer/)에서는 **갈리는 파일이 나온다** — 같은 대조를 그쪽에서 다시 돌렸다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  function identity<T>(x: T): T { … }          ★ 함수의 타입 매개변수
  function pair<A, B>(a: A, b: B): [A, B] { … } ★ 둘 이상
  interface GenericFn { <T>(x: T): T }          ★ 호출마다 채워진다
  interface FnOfT<T>  { (x: T): T }             ★ 타입 쓸 때 채운다 (안 채우면 TS2314)
  type ArrowGeneric = <T>(x: T) => T;           ★ GenericFn 과 같은 뜻
  class Box<T> { constructor(public value: T) {} }  ★ 인스턴스마다
  class Box<T> { static empty: T }              ✗ TS2302

  identity(3)            T <- 3            추론
  identity<number>(3)    T <- number       명시 (인자는 검사만 받는다)
  pair<string>("가", 1)  ✗ TS2558          부분 추론은 없다
```

**규칙 불릿**

- ★★★ **명시가 추론을 이긴다** — 꺾쇠를 적으면 인자는 **검사만** 받는다(1절 11·28행).
- ★★★ **스칼라 인자의 리터럴은 살아남고, 배열·객체 리터럴의 속은 넓어진다**(2절 10·11·12행). **21 의 과녁**이다.
- ★★ **제약이 있으면 리터럴이 살아남는다** — `T extends string` 은 `"auto"` 를 준다(2절 23행). 규칙은 [**20번 주제**](../20-generic-constraints-and-defaults/).
- ★★ **타입 인자는 전부 아니면 전무**다 — 하나만 적으면 `TS2558`(4절 8행).
- ★★ **기본 타입 인자는 「부분 추론」이 아니라 「부분 고정」** 이다(4절 13·14행).
- ★★ **이름에 단 `<T>` 는 반드시 채워야 한다** — 안 채우면 `TS2314`(3절 21행).
- ★★ **`static` 멤버는 클래스 타입 매개변수를 못 쓴다** — `TS2302`(5절 9행).
- ★★★ **런타임에 타입 인자는 없다** — 방출물에 **한 글자도** 없고 `Box<string>` 과 `Box<number>` 의 **생성자가 같다**(6절).
- ★ **`any` 는 탐침에도 안 걸린다** — 아무 데나 들어가는 것이 정의다(1절 16행).
- ★ **`.d.ts` 는 `const` 초기자의 비ASCII 를 이스케이프한다** — `"가"`(7절). **적은 것**이지 계산된 것이 아니다.

**금지 사례** — 이 주제에서 던져 받은 것 넷이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 타입 인자를 일부만 적음     ->  TS2558  Expected 2 type arguments, but got 1.
2) 제네릭 타입을 인자 없이 씀  ->  TS2314  Generic type 'FnOfT<T>' requires 1 type argument(s).
3) static 에 T 를 씀           ->  TS2302  Static members cannot reference class type parameters.
4) 명시한 인자와 안 맞는 값    ->  TS2345  Argument of type 'string' is not assignable to
                                           parameter of type 'number'.
```

## 어디서 틀리나

- ★★★ 「**제네릭은 리터럴을 안 지킨다**」 — 반만 맞다. **스칼라는 지킨다**(`keep("가")` → `"가"`).\
  **배열·객체 리터럴의 속만** 넓어진다(2절 10·11행). 이 구별을 놓치면 21 에서 엉뚱한 곳을 고친다.
- ★★★ 「**하나만 적고 나머지는 추론시키면 되겠지**」 — `TS2558` 이다(4절).
- ★★ 「**기본 타입 인자를 두면 부분 추론이 되겠지**」 — 되는 게 아니라 **고정**된다(4절 13·14행).
- ★★ 「**`interface F<T>` 와 `interface F { <T>… }` 는 같은 말이겠지**」 — 채워지는 **시점**이 다르다(3절).
- ★★ 「**`static` 에도 `T` 를 쓸 수 있겠지**」 — `TS2302` 다(5절 9행).
- ★★★ 「**런타임에 `T` 로 뭔가 할 수 있겠지**」 — 방출물에 **한 글자도 없다**(6절). `new T()` 도 `instanceof T` 도 없다.
- ★★ 「**Kotlin 처럼 `reified` 가 있겠지**」 — **없다.** 값을 하나 더 받는 수밖에 없다(6절).
- ★ 「**`any` 로 써도 비슷하겠지**」 — `any` 는 **입력과 출력을 잇는 줄을 끊는다**(1절 16행).
- ★ 「**`.d.ts` 가 계산된 타입을 보여 주겠지**」 — **적은 것**이다. `"가"` 이 그 증거다(7절).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 명시가 추론을 **이긴다** | 1절 11·28행 |
| **언어 보장** | 타입 인자는 **전부 아니면 전무**(`TS2558`) | 4절 8행 |
| **언어 보장** | 이름에 단 `<T>` 는 **채워야 한다**(`TS2314`) | 3절 21행 |
| **언어 보장** | `static` 은 클래스 타입 매개변수를 **못 쓴다**(`TS2302`) | 5절 9행 |
| **언어 보장** | ★★★ 타입 인자는 **런타임에 없다** | 6절 방출 전문 · 실행 출력 1·4·5번 |
| **★ 추론 규칙(명세라기보다 규칙)** | ★★ 스칼라는 리터럴 유지 · 배열·객체 속은 **넓어짐** | 2절 10·11·12행 — **던져서** 확인했다 |
| **`.d.ts` 방출** | 추론 결과를 **적어** 준다 · 별칭을 **정규화하지 않는다** | 7절 전문 |
| **★ 이 판(7.0.2)의 관찰** | ★★ `.d.ts` 가 `const` 초기자를 **`"가"`** 로 이스케이프 | 7절 — 탐침은 `"가"` 라고 답했다 |
| **이 판의 관찰** | 진단 **문구** 전문 | 코드(`TS2558`·`TS2314`·`TS2302`)가 더 오래 간다 |
| **이 판의 관찰** | `.d.ts` 의 들여쓰기 4칸과 줄 순서 | 방출기의 형식이다 |
| **★ 설정에 달림** | ★ **없다** — 다섯 파일 전부 `--strict false` 와 같다 | 8절 |
| **안 잰 것** | 타입 매개변수 개수가 검사 시간에 주는 영향 | 재지 않았다 |

★★ 「**진단 0줄」이 결론인 블록이 둘**이다(6·7절). 둘 다 **명령과 종료 코드까지** 캡처했다.

## 언제 쓰고 언제 안 쓰나

| 제네릭을 쓴다 | 안 쓴다 |
|---|---|
| **입력과 출력이 이어질 때**(`(x: T) => T`) | 타입 매개변수가 **한 자리에만** 나올 때 — 그냥 그 타입을 적어라 |
| 컨테이너·컬렉션을 만들 때 | 실제로는 늘 한 타입만 쓰는 자리 |
| 호출자가 **정확한 타입을 돌려받아야** 할 때 | `unknown` 으로 받아 좁히는 편이 안전한 입력([**04번 주제**](../04-any-unknown-never-void/)) |
| 여러 자리의 타입을 **묶어야** 할 때(`pair<A, B>`) | 런타임 동작이 타입마다 달라야 할 때 — **`T` 로는 못 한다**(6절) |
| ★ 리터럴을 보존해야 할 때 — **제약이나 [21](../21-inference-control-const-and-noinfer/)과 함께** | 제약 없이 리터럴을 기대할 때 — **조용히 넓어진다**(2절) |

## 핵심 문장

1. **타입 매개변수는 호출마다 채워지는 빈칸이다** — 인자에서 추론되거나 꺾쇠로 명시된다.
2. **명시가 추론을 이긴다** — 적는 순간 인자는 검사만 받는다.
3. **스칼라 리터럴은 살아남고 배열·객체 리터럴의 속은 넓어진다** — 이것이 21 의 과녁이다.
4. **타입 인자는 전부 아니면 전무다** — 부분 추론은 없다(`TS2558`).
5. **런타임에 타입 인자는 없다** — `Box<string>` 과 `Box<number>` 의 생성자가 같다.
6. **`any` 는 줄을 끊고 제네릭은 줄을 잇는다** — 그것이 둘의 유일한 차이다.

## 관련 자료

- [**18번 주제** — `this` 매개변수 타입](../18-this-parameter-types/) — **같은 배치의 앞 주제.** 「컴파일 타임에만 있는 것」이라는 축이 같다.
- [**20번 주제** — 제네릭 제약과 기본 타입 인자](../20-generic-constraints-and-defaults/) — **19 → 20 → 21 은 한 사슬**이다. 2절 23행과 4절 13행이 그쪽 입구다.
- [**21번 주제** — 추론 제어](../21-inference-control-const-and-noinfer/) — ★★★ **2절의 고장을 고치는 주제**다.
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — 2절 15행의 **호출자 쪽 고침**은 그쪽이 정본이다.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — 1절 16행이 `any` 인 이유는 그쪽.
- [**01번 주제** — TS 가 더하는 것과 지우는 것](../01-what-ts-adds-and-erases/) — 6절은 그 결론이 제네릭에 적용된 것이다.
- [**16번 주제** — 함수 타입과 오버로드](../16-function-types-and-overloads/) — 3절의 호출 시그니처 표기와 `.d.ts` 의 성질은 그쪽.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번** — [제네릭 선언](../../../java/syntax/17-generic-declarations/). 타입 파라미터·바운드의 **같은 질문을 Java 로**.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번** — [타입 소거](../../../java/syntax/19-type-erasure/). ★★ 6절의 **직접 대비**다.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **12번** — [`reified` 타입 파라미터](../../../kotlin/syntax/12-reified-type-parameters/). ★★ **TS 에는 없는 길**이다.
- [목록의 **22번 주제**](../22-keyof-and-indexed-access-types/)(`keyof` 와 인덱스 접근 타입) · [목록의 **46번 주제**](../46-variadic-tuple-types/)(가변 튜플 타입) — 제네릭이 더 깊어지는 자리.

## 용어 풀이

> **타입 매개변수(type parameter)** — 선언 쪽의 빈칸. `function f<T>(x: T)` 의 `T`.

> **타입 인자(type argument)** — 그 칸을 채우는 실제 타입. `f<number>(3)` 의 `number`.\
> **안 적으면 인자에서 추론**된다.

> **`TS2558`** — 「Expected N type arguments, but got M.」\
> **부분 추론이 없다**는 규칙의 얼굴이다.

> **`TS2314`** — 「Generic type 'X<T>' requires 1 type argument(s).」\
> 이름에 `<T>` 를 단 타입을 **인자 없이** 썼을 때.

> **타입 소거(type erasure)** — 타입 정보가 방출물에 남지 않는 것.\
> TS 는 **아예 JS 로 나가므로** 남길 자리 자체가 없다. Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번** 과 견주어 읽는다.

## 더 들어가면

- **왜 부분 추론이 없나** — 일부만 적었을 때 **나머지를 어느 순서로 추론할지**가 정해져 있지 않다. 타입 매개변수끼리 서로를 제약할 수 있어서(`<A, B extends A>`) 「적힌 것부터 채우고 나머지를 푼다」가 일반적으로 잘 정의되지 않는다. TS 는 그 모호함을 피해 **전부 아니면 전무**로 못 박았다 — 대신 **기본 타입 인자**라는 우회로를 뒀다(4절 13행, [**20번 주제**](../20-generic-constraints-and-defaults/)).
- **왜 배열의 속만 넓어지나** — 리터럴 타입의 **넓히기(widening)** 는 「이 값이 앞으로 바뀔 수 있는가」를 기준으로 한다. 배열·객체 리터럴은 **변경 가능한 자리**로 취급되므로 원소·속성이 넓어진다. 스칼라 인자는 그 자리에서 끝나므로 유지된다. **`as const` 는 「변경 불가」를 선언해 그 기준을 바꾸는 것**이고([**11번 주제**](../11-literal-types-and-as-const/)), [**21번 주제**](../21-inference-control-const-and-noinfer/)의 `const` 타입 매개변수는 **그 선언을 정의 쪽으로 옮기는 것**이다.
- **`any` 와 제네릭의 진짜 차이** — 1절 16행이 보여 주듯 `any` 는 **탐침조차 통과한다.** 즉 `any` 를 반환하는 함수를 쓰면 **그 뒤로 검사가 전부 꺼진다.** 제네릭은 반대로 **호출 지점의 타입을 그대로 들고 나온다.** 「타입을 모르겠으면 `any`」가 아니라 「**타입을 모르겠으면 `T`, 진짜 모르면 `unknown`**」이다([**04번 주제**](../04-any-unknown-never-void/)).
- **소거를 뚫는 세 가지 우회로** — TS 에는 `reified` 가 없으므로 ① **값을 하나 더 받는다**(생성자 `new () => T`·태그 문자열) ② **타입 술어를 쓴다**([**13번 주제**](../13-type-guards-and-predicates/)) ③ **판별 필드를 둔 유니온**([**09번 주제**](../09-union-types/))이다. 이 배치에서는 **셋 다 안 던졌다.**
- **제네릭 오버로드** — 오버로드 시그니처에 타입 매개변수를 다는 꼴은 [**16번 주제**](../16-function-types-and-overloads/)에서도 **안 던졌고** 여기서도 **안 던졌다.**
