# ts/syntax/25 — `infer` 와 재귀 조건부 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html) ·
> [Handbook — Indexed Access Types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html) ·
> [Handbook — Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html).
> 위는 **규칙 확인용 링크**이고, 본문의 진단·출력은 **전부 이 판에서 직접 던져 받은 것**이다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version · javac -version · rustc --version (sh exit=0) =====
Version 7.0.2
v18.19.1
javac 21.0.5
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 4창(종료 코드 격자)이다.**
> 값은 2창(`null` 탐침)으로 읽지만 이 주제의 결론은 「**`TS2589` 가 나느냐 안 나느냐**」이고,
> 그것을 말하는 것은 탐침이 아니라 **종료 코드**다. 5·6절이 그 자리다.
> ★★★ **22 → 24 → 25 는 한 사슬이고 여기가 급소다.**
> [**22번 주제**](../22-keyof-and-indexed-access-types/)가 타입에서 **키를 꺼내는 법**을 주고,
> [**24번 주제**](../24-conditional-types-and-distribution/)가 **조건부와 분배**를 주고,
> 25 가 그 조건부 안에 **빈칸을 하나 뚫는다**. 그 빈칸이 `infer` 다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> **버전** — 조건부 타입과 `infer` 는 TS **2.8**, **꼬리 재귀 꼴의 완화는 TS 4.5**, `infer X extends …` 는 TS **4.8** 이다.
> ★ 그 세 버전이 **7.0.2 에서 그대로 도는지는 외우지 않고 던져서 확인했다** — 아래 블록이 그 결과다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## ★★★ 이 주제가 쓰는 탐침 — 그리고 탐침이 말을 못 하는 자리

**계산된 타입은 눈에 안 보인다.** 그래서 이 갈래는 **일부러 틀린 주석을 달아 컴파일러가 답을 뱉게** 한다.

```text
  const probe: null = null as unknown as X;
                                         └─ 이 자리의 타입이 X 라면

  TS2322  「Type 'X' is not assignable to type 'null'.」
                       ↑ 여기서 X 를 읽는다
```

- ★★ 이 문서의 `TS2322 … is not assignable to type 'null'` 은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
- ★★★ **그런데 이 주제에서는 탐침이 자주 침묵한다.**
  `infer` 는 **모양이 안 맞으면 `never` 를 낸다.** 그리고 `never` 는 **모든 타입에 할당된다** —
  `const probe: null = … as never` 는 **진단이 아예 안 난다.**
  「답이 `never` 다」와 「내가 안 물어봤다」가 **출력에서 구분되지 않는다.**

> ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**\
> 못 잰 것(3의 상태)도 아니고 잴 것이 없는 것(4의 상태)도 아니다. **창을 바꿔 답을 얻은 것**이다.\
> 이 주제는 `type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다"` 를 끼워 넣어
> **침묵을 글자로 바꿔** 물었다. 1·2·3절의 소스에 그 줄이 들어 있는 이유다.\
> ★ **바꾼 창이 못 보는 것** — `IsNever` 는 「never 인가」만 답하지 **무엇인지는** 말하지 않는다.
> 그래서 **두 줄을 나란히** 둔다 — 침묵하는 탐침 한 줄과 `IsNever` 한 줄.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`·`E0308`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | 유니온 원소의 **표시 순서** | 5회 재실행 md5 **가짓수 1**(9절) — **관찰이지 보장이 아니다** |
| **안 흔들린다** | 6절 격자의 **`OK` / `TS2589` 배치** | 종료 코드라 참/거짓이다 |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 한 글자도 같다** | 9절에 대조 블록이 있다 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — 방출기가 **계산하지 않는다** | 0절에 근거 블록 |
| **★ 부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** — `infer` 도 재귀 조건부도 **전부 타입 층**이다 | 이 문서에 `.js` 블록이 **하나도 없다** |
| **★ 부적용 — 여러 번 돌려 보기** | 난수·시각·순서 비보장이 **한 칸도 없다** | 그래도 9절에서 5회 확인했다 |
| **★ 구현 층 — 다시 재야 하는 칸** | ★★★ 5·6절의 **경계 길이** | tsc 7.0.2 의 계수 규칙이다. **판이 오르면 다시 재라** |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 | **재지 않았다.** 그래서 이 문서에 **빠르다·느리다는 말이 한 줄도 없다** |

★ `--strict` 결과가 [**21번 주제**](../21-inference-control-const-and-noinfer/)와 다르다 — 거기서는 여섯 파일 중 하나가 갈렸다.
**이 주제는 다섯 중 하나도 안 갈렸다.**

## 한눈에 — 쉽게 말하면

**`infer` 는 조건부 타입의 「모양 맞추기」에 빈칸을 하나 뚫어 놓고, 맞으면 그 빈칸에 들어간 것을 받아 오는 것이다.**

| 비유 | 실체 |
|---|---|
| **빈칸이 뚫린 서식지**를 서류 위에 겹쳐 댄다 | `T extends (infer U)[] ? U : never` |
| 서식이 맞으면 **빈칸으로 비치는 글자**를 읽는다 | `U` 가 뽑힌다 |
| ★★★ 안 맞으면 **아무 말 없이** 빈손으로 돌려준다 | `never` — **진단이 안 난다**(1절) |
| 빈칸이 **둘인데 글자가 다르면** 둘 다 적는다 | 공변 자리 → **유니온**(2절) |
| ★★ 그런데 **도장 찍는 칸**에서는 둘을 **겹쳐** 찍는다 | 반공변 자리 → **교차**(2절) |
| 한 겹 벗기고 **남은 서류에 또 댄다** | 재귀 조건부(4절) |
| ★★★ 벗길 때마다 **앞의 것을 전부 옮겨 적으면** 수십 겹에서 막힌다 | 튜플 스프레드 → `TS2589`(6절) |
| 벗기기만 하고 **안 옮겨 적으면** 천 겹을 넘긴다 | 스프레드 없는 꼴(6절) |

- ★★★ 한 줄로 — 「**`infer` 는 모양에서 이름을 꺼내는 낱말이고, 재귀는 그 모양을 한 겹씩 벗기는 일이다.**」
- ★★★ 그리고 이 주제의 급소 한 줄 — 「**한계를 정하는 것은 「몇 겹이냐」가 아니라 「겹마다 무엇을 쌓느냐」다.**」

```text
  infer 는 빈칸이다

       T = string[]                         T = string
          │                                    │
          ▼                                    ▼
   ┌──────────────────┐                 ┌──────────────────┐
   │  ( ____ ) [ ]    │  서식           │  ( ____ ) [ ]    │  같은 서식
   └──────────────────┘                 └──────────────────┘
          │ 맞는다                             │ 안 맞는다
          ▼                                    ▼
      U = string                           never
      탐침이 'string' 이라고 말한다        ★ 탐침이 아무 말도 안 한다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **`infer` 는 어디에 놓을 수 있고, 안 맞으면 무엇이 나오나** — 다섯 자리에 놓아 던지고, 안 맞는 자리도 함께 던진다(1절).
2. **같은 `infer` 이름이 두 자리에 있으면 무엇으로 합쳐지나** — 공변 자리와 반공변 자리를 **나란히** 던진다(2절).
3. **★★★ 재귀는 어디서 멈추나** — 길이를 올려 가며 `TS2589` 를 **직접 받는다**(5절), 그리고 **무엇이 한계를 정하는지**를 격자로 가른다(6절).

★★ 3번이 이 주제의 급소다. **「깊이 한계」라는 이름이 오해를 부른다**는 것이 6절의 결론이다.

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **4창 — 종료 코드 격자** | `TS2589` 가 나느냐 | 참/거짓 | **본체**(5·6절) |
| ★★ **2창 — `null` 탐침** | 컴파일러가 **계산한** 타입 | 계산된 것 | 조연(1\~4절) · ★ `never` 앞에서 **침묵한다** |
| ★★ **2창 + `IsNever`** | 침묵을 글자로 바꾼 것 | **제5의 상태** | 1·2·3절 |
| **1창 — 멤버십 대입** | 값이 그 타입에 드느냐 | 에러가 나느냐 | 이 주제에서는 **안 썼다** |
| ★ **부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** | 방출기가 **적은 그대로** 남긴다 | 아래 블록이 근거 |
| ★ **부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** | `infer` 는 **전부 타입 층**이다 | `.js` 블록이 **하나도 없다** |

**5창이 왜 부적용인가** — 방출기는 **계산하지 않는다.** 적은 것을 적은 그대로 남긴다.

```text
===== tsc --pretty false -t es2022 --strict --declaration --emitDeclarationOnly --outDir d22f ex.22f.ts (tsc exit=0) =====
===== 방출된 d22f/ex.22f.d.ts =====
interface User {
    id: number;
    name: string;
}
export type Keys = keyof User;
export declare const oneKey: keyof User;
export type Cond = string extends string ? "가" : "나";
export declare const frozen: readonly ["가", "나"];
export type Elem = (typeof frozen)[number];
export {};
```

- ★★★ `export type Cond = string extends string ? "가" : "나";` 가 **풀리지 않은 채** 그대로 나왔다.
  조건부가 참인 것이 뻔한데도 방출기는 **안 푼다.**
- ★★ `export type Elem = (typeof frozen)[number];` 도 마찬가지다. **인덱스 접근이 그대로 남는다.**
- ★ 그러므로 이 주제에서 `.d.ts` 로 답을 읽을 수 없다 — 「재 봤더니 같았다」가 아니라 **잴 것이 없다.**
  값을 정확히 읽는 창은 **탐침**이고, 결론을 내는 창은 **종료 코드**다.

비용 — 컴파일 열두 번, `javac` 한 번, `rustc` 한 번, 격자 한 판(스무 번).

### (1) ★★★ `infer` 로 뽑기 — 다섯 자리, 그리고 안 맞을 때의 침묵

**언제 쓰나** — 「이 타입 안에 든 것만 꺼내 쓰고 싶다」일 때. 배열의 원소, 함수의 반환, 생성자의 인스턴스가 대표다.

```ts
// ex.25a.ts
// infer 로 뽑기 -- 요소 · 반환 · 매개변수 · 생성자, 그리고 안 맞으면 조용히 never
type Elem<T> = T extends (infer U)[] ? U : never;
type Ret<T> = T extends (...args: never[]) => infer R ? R : never;
type Par<T> = T extends (...args: infer P) => unknown ? P : never;
type Inst<T> = T extends new (...args: never[]) => infer I ? I : never;
type Head<T> = T extends [infer H, ...unknown[]] ? H : never;
type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

const fromArray: null = null as unknown as Elem<string[]>;
const fromTuple: null = null as unknown as Elem<[1, "가"]>;
const fromReturn: null = null as unknown as Ret<(x: number) => string>;
const fromParams: null = null as unknown as Par<(x: number, y: string) => void>;

class Point {
    constructor(public x: number) {}
}
const fromCtor: null = null as unknown as Inst<typeof Point>;
const fromHead: null = null as unknown as Head<[1, 2, 3]>;

const silent: null = null as unknown as Elem<string>;
const silentNamed: null = null as unknown as IsNever<Elem<string>>;
const readonlyTuple: null = null as unknown as IsNever<Elem<readonly [1, "가"]>>;
console.log(fromArray, fromTuple, fromReturn, fromParams, fromCtor, fromHead, silent, silentNamed, readonlyTuple);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.25a.ts (tsc exit=1) =====
ex.25a.ts(9,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.25a.ts(10,7): error TS2322: Type '"가" | 1' is not assignable to type 'null'.
  Type '"가"' is not assignable to type 'null'.
ex.25a.ts(11,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.25a.ts(12,7): error TS2322: Type '[x: number, y: string]' is not assignable to type 'null'.
ex.25a.ts(17,7): error TS2322: Type 'Point' is not assignable to type 'null'.
ex.25a.ts(18,7): error TS2322: Type '1' is not assignable to type 'null'.
ex.25a.ts(21,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
ex.25a.ts(22,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 9행 — `Elem<string[]>` 이 **`string`** 이다. `(infer U)[]` 라는 서식에 `string[]` 을 대면 빈칸이 `string` 으로 채워진다.
- ★★ 10행 — 튜플도 배열 서식에 맞는다. `Elem<[1, "가"]>` 가 **`"가" | 1`** 이다 —
  **원소 타입이 유니온으로 합쳐져** 나온다. ★ 순서가 소스와 다른데 **표시 순서는 9절에서 5회 확인한 칸**이다.
- ★★★ 12행이 뜻밖이다. `Par<(x: number, y: string) => void>` 가 **`[x: number, y: string]`** 이다 —
  튜플로 나오는 것까지는 예상해도 **매개변수 이름(레이블)이 살아 있다.** 이름은 타입이 아닌데 **타입 글자에 남는다.**
- ★★ 17행 — `Inst<typeof Point>` 가 **`Point`** 다. 여기가 [**23번 주제**](../23-typeof-type-operator/)와 만나는 자리다 —
  `typeof Point` 는 **생성자 쪽**이고, `new (...) => infer I` 서식이 그 생성자에서 **인스턴스 쪽**을 도로 꺼낸다.
- ★★★ **20행이 이 절의 급소다.** `Elem<string>` 은 **진단이 없다.**
  `string` 은 `(infer U)[]` 에 안 맞으니 답이 `never` 이고, `never` 는 `null` 에도 할당되므로 **탐침이 침묵한다.**
- ★★★ 21행이 그 침묵을 글자로 바꾼 줄이다 — `IsNever<Elem<string>>` 가 **`"never 다"`**.
  **같은 질문을 다른 창으로 물은 것**이고, 그래야 「답이 `never`」와 「내가 안 물음」이 갈린다.
- ★★ 22행이 **흔한 함정**이다. `Elem<readonly [1, "가"]>` 도 **`never`** 다 —
  `readonly` 튜플은 **가변 배열 서식 `(infer U)[]` 에 안 맞는다.** 서식을 `readonly (infer U)[]` 로 바꿔야 잡힌다.

```text
  같은 낱말, 다섯 자리

  (infer U)[]                   → 원소를 꺼낸다          9·10행
  (...args: never[]) => infer R → 반환을 꺼낸다          11행
  (...args: infer P) => unknown → 매개변수를 꺼낸다      12행   ★ 레이블이 산다
  new (...) => infer I          → 인스턴스를 꺼낸다      17행   ★ 23 과 만난다
  [infer H, ...unknown[]]       → 첫 원소를 꺼낸다       18행

  서식이 안 맞으면 → never → ★ 탐침이 침묵한다           20행
                            → IsNever 로 바꿔 묻는다     21행
```

비용 — 서식이 안 맞았을 때의 답이 **조용한 `never`** 라서, **실수한 자리가 에러로 안 드러난다.** 진단이 아니라 **엉뚱한 타입**으로 번진다.

### (2) ★★ `infer` 가 여러 자리에 있으면 — 자리에 따라 합치는 법이 다르다

**언제 쓰나** — 같은 이름의 `infer` 를 두 군데 이상 쓸 때. 「둘 다 받으면 어느 쪽이 이기나」가 질문이다.

```ts
// ex.25b.ts
// infer 가 여러 자리에 있으면 -- 공변 자리는 유니온, 반공변 자리는 교차
type Co<T> = T extends { a: infer U; b: infer U } ? U : never;
type Contra<T> = T extends { a: (x: infer U) => void; b: (x: infer U) => void } ? U : never;
type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

const covariant: null = null as unknown as Co<{ a: string; b: number }>;
const contravariant: null = null as unknown as Contra<{ a: (x: { p: 1 }) => void; b: (x: { q: 2 }) => void }>;

type Clash = Contra<{ a: (x: string) => void; b: (x: number) => void }>;
const clashSilent: null = null as unknown as Clash;
const clashNamed: null = null as unknown as IsNever<Clash>;

type CoSame<T> = T extends { a: infer U; b: infer U } ? U : never;
const coSame: null = null as unknown as CoSame<{ a: "가"; b: "가" }>;
console.log(covariant, contravariant, clashSilent, clashNamed, coSame);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.25b.ts (tsc exit=1) =====
ex.25b.ts(6,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.25b.ts(7,7): error TS2322: Type '{ p: 1; } & { q: 2; }' is not assignable to type 'null'.
ex.25b.ts(11,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
ex.25b.ts(14,7): error TS2322: Type '"가"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 6행 — `Co<{ a: string; b: number }>` 가 **`string | number`** 다.
  `a` 와 `b` 는 **값을 내주는 자리**(공변)이고, 그런 자리의 후보는 **유니온으로 합쳐진다.**
- ★★★ 7행 — `Contra<…>` 가 **`{ p: 1; } & { q: 2; }`** 다.
  `(x: infer U) => void` 의 `x` 는 **값을 받아들이는 자리**(반공변)이고, 그런 자리의 후보는 **교차로 합쳐진다.**
- ★★ 10행이 다시 침묵한다. `Contra<{ a: (x: string) => void; b: (x: number) => void }>` 는
  `string & number` 라 **`never`** 이고, **진단이 안 난다.**
- ★★★ 11행이 그 침묵을 글자로 바꿨다 — **`"never 다"`**. ★ **교차가 `never` 로 무너지는 것**은
  [**10번 주제**](../10-intersection-types/)가 정본이다. 여기서는 **`infer` 가 그 규칙을 따른다**까지만 본다.
- ★★ 14행 — 두 자리의 타입이 같으면 그대로다(**`"가"`**). 합치기가 일어나도 **결과가 안 벌어진다.**

```text
  같은 이름의 infer 가 두 자리에 — 무엇으로 합치나

  공변 자리 (값을 내준다)                반공변 자리 (값을 받는다)
  { a: infer U; b: infer U }             { a: (x: infer U)=>void; b: (x: infer U)=>void }
        │                                      │
   후보  string , number                  후보  {p:1} , {q:2}
        │                                      │
        ▼  유니온                              ▼  교차
   string | number                        {p:1} & {q:2}

   왜 — 내주는 쪽은 "둘 중 하나가 나온다"     왜 — 받는 쪽은 "둘 다 받을 수 있어야 한다"
```

> **공변(covariant)** — 담긴 타입이 넓어지면 담는 타입도 같은 방향으로 넓어지는 자리.\
> 예: `string` 을 내주는 자리에 `string | number` 를 넣으면 **더 넓어진다**(받는 쪽이 더 많은 경우를 봐야 한다).

> **반공변(contravariant)** — 담긴 타입이 넓어지면 담는 타입은 **거꾸로 좁아지는** 자리.\
> 예: `(x: string) => void` 보다 `(x: string | number) => void` 가 **더 쓸모가 넓다** — 인자 자리가 그렇다.

★★ 변성 자체의 정본은 [**17번 주제**](../17-variance-and-parameter-compatibility/)다 —
**그쪽은 「어느 함수가 어느 함수에 할당되나」까지, 여기는 「`infer` 가 그 규칙을 따른다」부터**다.

비용 — 반공변 자리에 같은 이름을 두 번 쓰면 **교차가 `never` 로 무너져** 조용히 죽는 길이 생긴다(10·11행).

### (3) ★ `infer X extends …` — 뽑으면서 좁힌다

**언제 쓰나** — 문자열에서 숫자를 꺼내고 싶을 때처럼, **뽑은 것을 곧바로 다른 타입으로 쓰고 싶을** 때.

```ts
// ex.25c.ts
// infer X extends -- 뽑으면서 좁힌다
type NumOf<S> = S extends `${infer N extends number}` ? N : never;
type NumOfPlain<S> = S extends `${infer N}` ? N : never;
type FirstChar<S> = S extends `${infer C}${string}` ? C : never;
type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

const narrowed: null = null as unknown as NumOf<"42">;
const notNarrowed: null = null as unknown as NumOfPlain<"42">;
const notANumber: null = null as unknown as IsNever<NumOf<"가">>;
const firstChar: null = null as unknown as FirstChar<"가나다">;

type HeadStr<T> = T extends [infer H extends string, ...unknown[]] ? H : never;
const headOk: null = null as unknown as HeadStr<["가", 1]>;
const headNo: null = null as unknown as IsNever<HeadStr<[1, "가"]>>;
console.log(narrowed, notNarrowed, notANumber, firstChar, headOk, headNo);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.25c.ts (tsc exit=1) =====
ex.25c.ts(7,7): error TS2322: Type '42' is not assignable to type 'null'.
ex.25c.ts(8,7): error TS2322: Type '"42"' is not assignable to type 'null'.
ex.25c.ts(9,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
ex.25c.ts(10,7): error TS2322: Type '"가"' is not assignable to type 'null'.
ex.25c.ts(13,7): error TS2322: Type '"가"' is not assignable to type 'null'.
ex.25c.ts(14,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 7행과 8행을 나란히 읽어라. **같은 문자열 `"42"`** 인데
  `NumOf` 는 **`42`**(숫자 리터럴), `NumOfPlain` 은 **`"42"`**(문자열 리터럴)다.
  차이는 **`extends number` 한 조각**뿐이다.
- ★★ 9행 — `NumOf<"가">` 는 좁히기에 실패해 **`never`** 다. 여기서도 탐침이 침묵하므로 `IsNever` 로 물었다.
- ★ 10행 — `FirstChar<"가나다">` 가 **`"가"`**. 템플릿 리터럴 서식은 **앞에서부터** 맞춘다.
- ★★ 13·14행 — 튜플의 머리에도 같은 조각을 붙일 수 있다.
  `HeadStr<["가", 1]>` 는 **`"가"`**, `HeadStr<[1, "가"]>` 는 **`never`**.
  ★ **머리가 제약을 어기면 조건 전체가 거짓**이 된다 — 「뽑고 나서 거른다」가 아니라 **「거르면서 뽑는다」**.

```text
  extends 한 조각이 무엇을 바꾸나

  `${infer N}`                  "42"  →  "42"     문자열 리터럴    8행
  `${infer N extends number}`   "42"  →   42      숫자 리터럴      7행
                                "가"  →  never    ★ 조건이 거짓    9행
```

비용 — 좁히기에 실패하면 **조건 전체가 거짓**이 되어 `else` 가지로 간다. 「뽑기는 했는데 좁히기만 실패」 같은 중간 상태가 없다.

### (4) ★★ 재귀 조건부 — 한 겹씩 벗긴다

**언제 쓰나** — 문자열을 구분자로 쪼개거나, 튜플을 뒤집거나, 감싼 것을 끝까지 벗길 때.

```ts
// ex.25d.ts
// 재귀 조건부 -- 문자열 쪼개기 · 튜플 뒤집기 · Awaited · 템플릿 리터럴
type Split<S extends string, D extends string> =
    S extends `${infer H}${D}${infer R}` ? [H, ...Split<R, D>] : [S];
type Rev<T extends readonly unknown[]> = T extends [infer H, ...infer R] ? [...Rev<R>, H] : [];
type Join<T extends readonly string[], D extends string> =
    T extends [infer H extends string, ...infer R extends string[]]
        ? R extends [] ? H : `${H}${D}${Join<R, D>}`
        : "";
type MyAwaited<T> = T extends Promise<infer U> ? MyAwaited<U> : T;

const split: null = null as unknown as Split<"가.나.다", ".">;
const reversed: null = null as unknown as Rev<[1, 2, 3, 4]>;
const joined: null = null as unknown as Join<["가", "나", "다"], "-">;
const roundTrip: null = null as unknown as Join<Split<"가.나.다", ".">, "-">;

const mine: null = null as unknown as MyAwaited<Promise<Promise<number>>>;
const stock: null = null as unknown as Awaited<Promise<Promise<Promise<string>>>>;
const notPromise: null = null as unknown as Awaited<number>;
console.log(split, reversed, joined, roundTrip, mine, stock, notPromise);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.25d.ts (tsc exit=1) =====
ex.25d.ts(11,7): error TS2322: Type '["가", "나", "다"]' is not assignable to type 'null'.
ex.25d.ts(12,7): error TS2322: Type '[4, 3, 2, 1]' is not assignable to type 'null'.
ex.25d.ts(13,7): error TS2322: Type '"가-나-다"' is not assignable to type 'null'.
ex.25d.ts(14,7): error TS2322: Type '"가-나-다"' is not assignable to type 'null'.
ex.25d.ts(16,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.25d.ts(17,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.25d.ts(18,7): error TS2322: Type 'number' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 11행 — `Split<"가.나.다", ".">` 가 **`["가", "나", "다"]`** 다.
  서식 `` `${infer H}${D}${infer R}` `` 이 **머리와 꼬리를 한 번에** 갈라 주고, 꼬리를 다시 자기에게 넘긴다.
- ★★ 12행 — `Rev<[1, 2, 3, 4]>` 가 **`[4, 3, 2, 1]`** 이다. 머리를 떼어 **뒤에 붙이는** 것을 반복한다.
- ★★★ 13·14행이 짝이다. `Join<["가","나","다"], "-">` 가 **`"가-나-다"`** 이고,
  **`Join<Split<…>>` 왕복도 같은 글자**다. 쪼갠 것을 도로 붙이면 원본이 나온다 —
  **두 재귀가 서로의 역함수**임이 한 줄로 보인다.
- ★★ 16·17행 — 직접 만든 `MyAwaited<Promise<Promise<number>>>` 가 **`number`**,
  표준 `Awaited<Promise<Promise<Promise<string>>>>` 가 **`string`**.
  ★ **`Awaited` 가 재귀 조건부라는 사실**이 이 두 줄로 드러난다 — 세 겹을 **끝까지** 벗겼다.
- ★ 18행 — `Awaited<number>` 는 **`number`** 다. 감싼 것이 없으면 **그대로 돌려준다**(종료 가지).

```text
  한 겹씩 벗긴다 — Split<"가.나.다", ".">

  "가.나.다"
     │  `${infer H}${"."}${infer R}`  →  H="가"  R="나.다"
     ▼
  ["가", ...Split<"나.다", ".">]
     │  H="나"  R="다"
     ▼
  ["가", "나", ...Split<"다", ".">]
     │  "." 이 없다 → 종료 가지 [S]
     ▼
  ["가", "나", "다"]
```

> **종료 가지(base case)** — 서식이 더는 안 맞을 때 가는 `else` 쪽.\
> 예: `Split` 은 구분자가 없으면 `[S]` 를, `MyAwaited` 는 `Promise` 가 아니면 `T` 를 그대로 돌려준다.

★★ 템플릿 리터럴 타입 자체의 정본은 [목록의 **27번 주제**](../27-template-literal-types/)이고,
`Awaited`·`ReturnType` 같은 표준 도구의 정본은 [목록의 **28번 주제**](../28-utility-types/)다.
**여기는 「그것들이 재귀 조건부로 만들어져 있다」까지**다.

비용 — 종료 가지를 빠뜨리면 **끝없이 돈다.** 그 끝이 5·6절이다.

### (5) ★★★ 어디서 멈추나 — `TS2589` 를 직접 받는다

**언제 쓰나** — 재귀 타입을 실제 코드에 넣기 전에 **한계가 어디쯤인지** 알아 두고 싶을 때.

```ts
// ex.25e.ts
// 재귀가 어디서 멈추나 -- 길이를 올려 가며 TS2589 를 직접 받는다
type Count<N extends readonly unknown[], Stop extends number> =
    N["length"] extends Stop ? N : Count<[...N, 1], Stop>;

type Ok = Count<[], 999>;
const okLen: null = null as unknown as Ok["length"];

type TooDeep = Count<[], 1000>;
const deepLen: null = null as unknown as TooDeep["length"];

type Endless<T extends readonly unknown[]> = Endless<[...T, 1]>;
type Never = Endless<[]>;
console.log(okLen, deepLen, null as unknown as Never);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.25e.ts (tsc exit=1) =====
ex.25e.ts(6,7): error TS2322: Type '999' is not assignable to type 'null'.
ex.25e.ts(8,16): error TS2589: Type instantiation is excessively deep and possibly infinite.
ex.25e.ts(11,6): error TS2456: Type alias 'Endless' circularly references itself.
ex.25e.ts(11,46): error TS2315: Type 'Endless' is not generic.
ex.25e.ts(12,14): error TS2315: Type 'Endless' is not generic.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 6행 — `Count<[], 999>` 는 **끝까지 돌아** 탐침이 `999` 라고 답했다. **길이를 세는 재귀가 실제로 완주했다.**
- ★★★ 8행이 이 절의 과녁이다 — **`TS2589` 「Type instantiation is excessively deep and possibly infinite.」**
  `Count<[], 1000>` 한 글자 차이로 **벽에 닿았다.**
- ★★★ 9행에 **진단이 없다.** `TooDeep` 이 이미 실패했으므로 그 뒤의 탐침은 **아무 말도 안 한다** —
  ★ **한계에 닿은 자리의 뒤는 조용해진다.** 「에러가 하나뿐이니 괜찮겠지」로 읽으면 안 된다.
- ★★★ 11·12행이 **다른 진단**이다. `Endless<T> = Endless<[...T, 1]>` 는 `TS2589` 가 아니라
  **`TS2456`**(circularly references itself) + **`TS2315`** 두 건이다.
  ★ **종료 가지가 아예 없는 것**은 **깊이 문제가 아니라 순환 정의 문제**로 잡힌다 — 컴파일러가 **돌려 보기 전에** 거른다.

```text
  두 가지 실패는 다른 진단이다

  종료 가지가 있는데 너무 깊다          종료 가지가 아예 없다
  ─────────────────────────────         ─────────────────────────────
  Count<[], 1000>                       Endless<T> = Endless<[...T,1]>
        │ 돌다가 벽에 닿는다                   │ 돌기 전에 걸린다
        ▼                                     ▼
     TS2589                                TS2456 (+ TS2315)
  "너무 깊고 무한일 수 있다"            "자기 자신을 순환 참조한다"
```

비용 — 한계에 닿으면 그 타입은 **에러 타입이 되어 뒤의 검사가 조용해진다**(9행). 한 진단이 **여러 자리를 가린다.**

### (6) ★★★ 격자 — 갈리는 축은 「꼬리냐」가 아니라 「무엇을 쌓느냐」다

**언제 쓰나** — 「재귀를 꼬리 꼴로 바꾸면 한계가 늘어난다」는 말을 **확인해 보고 싶을** 때.

```bash
# ts22b-depth.sh
#!/usr/bin/env bash
# 재귀 조건부의 한계를 격자로 친다 -- 네 가지 꼴 x 다섯 가지 길이
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
tup() { local n=$1 i; printf '['; for ((i=1;i<=n;i++)); do printf '1'; ((i<n)) && printf ', '; done; printf ']'; }
decl_A='type A<T extends readonly unknown[]> = T extends [infer H, ...infer R] ? [...A<R>, H] : [];'
decl_B='type B<T extends readonly unknown[], Acc extends readonly unknown[] = []> = T extends [infer H, ...infer R] ? B<R, [H, ...Acc]> : Acc;'
decl_C='type C<T extends readonly unknown[]> = T extends [infer H, ...infer R] ? [C<R>, H] : [];'
decl_E='type E<T extends readonly unknown[]> = T extends [unknown, ...infer R] ? { n: E<R> } : null;'
echo 'A  꼬리 아님 + 튜플 스프레드    type A<T> = T extends [infer H, ...infer R] ? [...A<R>, H] : [];'
echo 'B  꼬리 + 누산기 스프레드      type B<T, Acc = []> = T extends [infer H, ...infer R] ? B<R, [H, ...Acc]> : Acc;'
echo 'C  꼬리 아님 + 스프레드 없음   type C<T> = T extends [infer H, ...infer R] ? [C<R>, H] : [];'
echo 'E  꼬리 아님 + 객체로 감쌈     type E<T> = T extends [unknown, ...infer R] ? { n: E<R> } : null;'
echo
echo '길이 |       A       |       B       |       C       |       E'
echo '-----+---------------+---------------+---------------+---------------'
for n in 48 49 500 999 1000; do
  row=$(printf '%4s |' "$n")
  for k in A B C E; do
    eval "d=\$decl_$k"
    { echo "$d"; echo "type Deep = $k<$(tup "$n")>;"; echo 'declare const p: Deep;'; echo 'export { p };'; } > "$D/probe.ts"
    out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/probe.ts" 2>&1); rc=$?
    case "$out" in *TS2589*) mark="TS2589 exit=$rc";; '') mark="OK     exit=$rc";; *) mark="OTHER  exit=$rc";; esac
    row="$row $(printf '%-14s' "$mark")|"
  done
  echo "${row%|}" | sed "s/ *$//"
done
```

```text
===== bash ts22b-depth.sh (sh exit=0) =====
A  꼬리 아님 + 튜플 스프레드    type A<T> = T extends [infer H, ...infer R] ? [...A<R>, H] : [];
B  꼬리 + 누산기 스프레드      type B<T, Acc = []> = T extends [infer H, ...infer R] ? B<R, [H, ...Acc]> : Acc;
C  꼬리 아님 + 스프레드 없음   type C<T> = T extends [infer H, ...infer R] ? [C<R>, H] : [];
E  꼬리 아님 + 객체로 감쌈     type E<T> = T extends [unknown, ...infer R] ? { n: E<R> } : null;

길이 |       A       |       B       |       C       |       E
-----+---------------+---------------+---------------+---------------
  48 | OK     exit=0 | OK     exit=0 | OK     exit=0 | OK     exit=0
  49 | TS2589 exit=1 | OK     exit=0 | OK     exit=0 | OK     exit=0
 500 | TS2589 exit=1 | OK     exit=0 | OK     exit=0 | OK     exit=0
 999 | TS2589 exit=1 | OK     exit=0 | OK     exit=0 | OK     exit=0
1000 | TS2589 exit=1 | TS2589 exit=1 | OK     exit=0 | OK     exit=0
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **A 만 일찍 막힌다.** 꼬리 재귀가 아니고 **튜플 스프레드 `[...A<R>, H]`** 로 결과를 쌓는 꼴이다.
- ★★ **B 는 훨씬 멀리 간다.** 꼬리 꼴로 바꾸고 누산기에 쌓는다 — 그래도 **끝에는 막힌다.**
- ★★★ **여기서 전제가 뒤집혔다 — C 를 보라.** `[C<R>, H]` 는 **꼬리 재귀가 아니다.**
  그런데 **A 가 막힌 길이의 스무 배가 넘는 자리에서도 통과**한다.
  A 와 C 의 차이는 **꼬리냐 아니냐가 아니라 점 세 개**뿐이다.
- ★★★ **E 도 마찬가지다.** 꼬리가 아닌데 결과를 **객체로 감싸기만** 하면 끝까지 통과한다.
- ★★★ 그러므로 **「꼬리 재귀로 바꾸면 한계가 풀린다」는 이 판에서 틀린 요약**이다.
  갈리는 축은 「**겹마다 튜플 스프레드를 하느냐**」다. B 가 멀리 가는 것도 「꼬리라서」가 아니라
  **B 역시 스프레드를 하기 때문에 끝내 막힌다**는 쪽으로 읽어야 앞뒤가 맞는다.

```text
  같은 깊이, 다른 쌓기 — 겹마다 무엇이 만들어지나

  A: [...A<R>, H]   스프레드           C: [C<R>, H]   스프레드 없음
  ──────────────────────────           ──────────────────────────
   1겹  []                              1겹  []
   2겹  [x]                             2겹  [[], x]
   3겹  [x, x]                          3겹  [[[], x], x]
   4겹  [x, x, x]                       4겹  [[[[], x], x], x]
        ↑ 겹마다 앞의 것을 전부              ↑ 겹은 깊어져도
          펼쳐 새 튜플을 만든다                 튜플 칸 수는 늘 둘이다

   수십 겹에서 TS2589                    천 겹을 넘겨도 통과
```

★★★ **수를 어떻게 읽을 것인가** — 격자의 정확한 길이는 **블록 안에 있고, 본문은 성질만 주장한다**:
「**스프레드를 쌓는 꼴은 수십에서 막히고, 안 쌓는 꼴은 천을 넘겨도 산다 — 스무 배가 넘는 차이**」.
★★ **그 경계 길이는 명백히 구현(tsc 7.0.2) 층이다.** 명세가 정한 수가 아니고, **판이 오르면 다시 재야 한다.**
★★★ **그리고 이 절에 「느리다」는 말이 없다** — **시간을 재지 않았다.**
검사 비용이 궁금하면 [목록의 **45번 주제**](../45-type-level-performance/)(타입 수준 성능)가 그 자리다.

비용 — 한계를 「깊이」로만 기억하면 **고치는 수를 잘못 고른다.** 꼬리 꼴로 바꾸는 것보다 **쌓는 것을 줄이는 쪽**이 먼저다.

### (7) ★★ Java 의 `infer` — 와일드카드 포획

**언제 쓰나** — 「다른 언어는 이름 없는 타입을 어떻게 꺼내나」를 견줄 때.

```java
// Capture.java
import java.util.List;

public class Capture {
    static void copyFirstBack(List<?> xs) {
        xs.set(0, xs.get(0));
    }

    static <T> void copyFirstBackNamed(List<T> xs) {
        xs.set(0, xs.get(0));
    }

    static void addToBounded(List<? extends CharSequence> xs) {
        xs.add("가");
    }
}
```

```text
===== javac -d jout Capture.java (javac exit=1) =====
Capture.java:5: error: incompatible types: Object cannot be converted to CAP#1
        xs.set(0, xs.get(0));
                        ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Object from capture of ?
Capture.java:13: error: incompatible types: String cannot be converted to CAP#1
        xs.add("가");
               ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends CharSequence from capture of ? extends CharSequence
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
2 errors
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`CAP#1 is a fresh type-variable: CAP#1 extends Object from capture of ?`** 가 이 블록의 전부다.
  javac 는 `List<?>` 의 `?` 에 **임시 이름을 붙인다.** 그것이 **Java 의 `infer`** 다.
- ★★ 그런데 **그 이름을 프로그래머가 쓸 수 없다.** 5행은 꺼낸 것을 도로 넣는 것뿐인데 막힌다 —
  `get` 이 준 것과 `set` 이 받을 것이 **같은 `CAP#1` 이라는 보장을 못 적기** 때문이다.
- ★★★ **9행에는 진단이 없다.** 같은 몸통인데 **제네릭 헬퍼 `<T>` 로 감싼 쪽은 통과한다** —
  **포획한 타입에 이름을 주려고 메서드를 하나 더 만든 것**이 Java 의 관용구다.
- ★★ 13행은 경계가 붙은 포획이다. `? extends CharSequence` 에서도 **넣기는 막힌다** —
  `CAP#1` 이 `String` 이라는 보장이 없기 때문이다.
- ★ 꼬리의 `Note:` 줄과 `2 errors` 까지가 이 명령의 전체 출력이다. **한 글자도 손대지 않았다.**

```text
  이름 없는 타입에 이름을 주는 법

  TS      T extends (infer U)[] ? U : never
                      └─ 낱말 하나로 그 자리에서 이름이 생긴다

  Java    static void f(List<?> xs)          → CAP#1 이 생기지만 적을 수 없다
          static <T> void g(List<T> xs)      → ★ 메서드를 하나 더 만들어 이름을 준다
```

★ 이 대비의 정본은
`` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **18번**([와일드카드와 PECS — `? extends`/`? super`](../../../java/syntax/18-wildcards-pecs/)) ``이다.
**그쪽은 「어느 방향에 무엇을 쓰나」까지, 여기는 「포획한 타입에 이름을 주는 방법이 다르다」까지**다.

비용 — Java 는 **이름을 주려고 메서드를 하나 더 만들어야** 하고, TS 는 `infer U` 한 낱말로 끝난다.

### (8) ★ Rust — 모양이 아니라 이름으로 뽑는다

**언제 쓰나** — 「TS 의 `infer` 에 해당하는 것이 Rust 에 있나」를 견줄 때.

```rust
// assoc.rs
// 이름으로 뽑는다 -- Rust 는 트레이트가 미리 선언한 연관 타입만 꺼낼 수 있다
trait Source {
    type Item;
    fn get(&self) -> Self::Item;
}

struct Counter;

impl Source for Counter {
    type Item = u32;
    fn get(&self) -> u32 {
        7
    }
}

fn pull<S: Source>(s: &S) -> S::Item {
    s.get()
}

fn main() {
    let c = Counter;
    let probe: u8 = pull(&c);
    println!("{}", probe);
}
```

```text
===== rustc --crate-name assoc --edition 2021 assoc.rs (rustc exit=1) =====
error[E0308]: mismatched types
  --> assoc.rs:22:21
   |
22 |     let probe: u8 = pull(&c);
   |                --   ^^^^^^^^ expected `u8`, found `u32`
   |                |
   |                expected due to this
   |
help: you can convert a `u32` to a `u8` and panic if the converted value doesn't fit
   |
22 |     let probe: u8 = pull(&c).try_into().unwrap();
   |                             ++++++++++++++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

그림 해설 — 한 단계에 한 문장.

- ★★ **같은 탐침 수법이 rustc 에서도 통한다.** 일부러 `u8` 이라 적으니
  **`expected u8, found u32`** 로 **실제 타입을 말해 준다.** 창의 이름만 다르고 쓰는 법은 같다.
- ★★★ 그런데 **꺼내는 방식이 다르다.** `S::Item` 은 **트레이트가 미리 선언한 이름**이다 —
  `trait Source { type Item; }` 에 **그 이름이 적혀 있어야** 꺼낼 수 있다.
- ★★★ TS 의 `infer` 는 **아무 모양에서나** 꺼낸다. 남이 만든 타입이든, 이름이 없는 타입이든 **서식만 맞으면** 된다.
- ★★ 그래서 진짜 축은 「정의 자리냐 사용 자리냐」가 아니라 「**모양이냐 이름이냐**」다.
  이것은 [**20번 주제**](../20-generic-constraints-and-defaults/)가 이미 실측한 축이고, 여기서는 **인용한다.**

```text
  무엇을 근거로 꺼내나

  TS      모양     T extends (infer U)[] ? U : never
                   ★ 상대가 아무 약속도 안 해 뒀어도 꺼낸다

  Rust    이름     trait Source { type Item; }   ← 미리 선언해 둬야
                   fn pull<S: Source>(s:&S) -> S::Item
                   ★ 선언에 없는 것은 못 꺼낸다
```

★ 정본은
`` Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**([트레이트 정의·구현·기본 메서드·연관 타입](../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/)) ``이다.

비용 — 모양으로 꺼내면 **남의 타입에서도 꺼낼 수 있지만**, 상대가 모양을 바꾸면 **조용히 `never` 가 된다**(1절 20행).

### (9) ★ 설정 대조와 표시 순서 — 근거로 쓸 칸을 먼저 못 박는다

**언제 쓰나** — 본문의 숫자·글자를 근거로 쓰기 전에, **무엇이 흔들리지 않는지** 선언할 때.

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.25a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.25b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.25c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.25d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.25e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.22a.ts    5회 md5 가짓수 1
ex.24a.ts    5회 md5 가짓수 1
ex.25b.ts    5회 md5 가짓수 1
```

그림 해설 — 한 단계에 한 문장.

- ★★★ `--strict` 를 꺼도 **다섯 파일이 한 글자도 안 갈렸다.** 이 주제의 결론은 **설정과 무관**하다.
- ★★ [**21번 주제**](../21-inference-control-const-and-noinfer/)와 다른 자리다 — 거기서는 여섯 중 하나가 갈렸다.
  **「추론」은 설정을 타고 「계산」은 안 탄다**고 읽을 수 있지만, 그것은 **다섯 파일에서 본 것**이지 규칙이 아니다.
- ★★ 같은 명령을 5회 돌려 md5 **가짓수가 1** 이다 — 유니온 원소의 **표시 순서가 안 흔들렸다.**
  ★ **관찰이지 보장이 아니다.** 순서를 근거로 삼는 문장은 이 문서에 없다.

비용 — 없다. 이 절은 **뒤의 모든 인용이 딛고 설 바닥**을 깐다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  T extends (infer U)[] ? U : never                     원소            (1절)
  T extends (...args: never[]) => infer R ? R : never   반환            (1절)
  T extends (...args: infer P) => unknown ? P : never   매개변수 튜플   (1절)
  T extends new (...args: never[]) => infer I ? I : never   인스턴스    (1절)
  T extends [infer H, ...infer R] ? … : …               머리와 꼬리     (4절)
  S extends `${infer H}${D}${infer R}` ? … : …          문자열 쪼개기   (4절)
  S extends `${infer N extends number}` ? N : never     뽑으면서 좁히기 (3절)   ★ 4.8
  [T] extends [never] ? "그렇다" : "아니다"              never 를 묻는다 (제5의 상태)
```

**금지 사례** — 이 주제에서 던져 받은 것 셋이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 너무 깊은 재귀          ->  TS2589  「Type instantiation is excessively deep and
                                        possibly infinite.」                  (5절 8행)
2) 종료 가지가 없는 재귀   ->  TS2456  「Type alias 'Endless' circularly
                                        references itself.」                  (5절 11행)
   그 뒤에 딸려 나오는 것  ->  TS2315  「Type 'Endless' is not generic.」      (5절 11·12행)
3) Java 의 포획 자리에 값  ->  javac   「incompatible types: String cannot be
                                        converted to CAP#1」                  (7절 13행)
```

**규칙 불릿**

- ★★★ **`infer` 는 조건부의 `extends` 오른쪽에서만 쓴다** — 서식 안의 **빈칸**이다.
- ★★★ **서식이 안 맞으면 `never` 이고, 탐침은 그것을 말하지 못한다** — `IsNever` 로 바꿔 묻는다(1절 20·21행).
- ★★ **`readonly` 튜플은 `(infer U)[]` 에 안 맞는다**(1절 22행).
- ★★ **매개변수를 뽑으면 레이블까지 딸려 온다**(1절 12행).
- ★★★ **같은 이름이 공변 자리에 둘이면 유니온, 반공변 자리에 둘이면 교차다**(2절 6·7행).
- ★★ **교차가 `never` 로 무너지면 또 조용해진다**(2절 10·11행).
- ★ **`infer X extends …` 는 좁히면서 거른다** — 실패하면 조건 전체가 거짓이다(3절 9·14행).
- ★★ **재귀는 종료 가지가 있어야 한다** — 없으면 `TS2589` 가 아니라 `TS2456` 이다(5절 11행).
- ★★★ **한계를 정하는 것은 겹 수가 아니라 겹마다 쌓는 것이다**(6절). ★ 그 **경계 길이는 구현 층**이다.
- ★ **`Awaited` 는 재귀 조건부다** — 여러 겹을 끝까지 벗긴다(4절 17행).

## 어디서 틀리나

- ★★★ 「**서식이 안 맞으면 에러가 나겠지**」 — **안 난다.** 조용히 `never` 가 되고 **탐침도 침묵한다**(1절 20행).
  이 주제에서 가장 비싼 오해다.
- ★★★ 「**꼬리 재귀로 바꾸면 한계가 풀리겠지**」 — 갈리는 축이 **그게 아니다.**
  꼬리가 아닌 C·E 가 **A 의 스무 배가 넘는 자리에서도 통과**한다(6절).
- ★★★ 「**깊이 한계니까 겹 수만 세면 되겠지**」 — **겹마다 무엇을 쌓느냐**가 정한다(6절).
- ★★ 「**종료 가지가 없으면 `TS2589` 가 나겠지**」 — **`TS2456`** 이다. 진단이 아예 다르다(5절 11행).
- ★★ 「**`readonly` 튜플도 배열이니 `(infer U)[]` 에 맞겠지**」 — **안 맞는다**(1절 22행).
- ★★ 「**같은 이름의 `infer` 는 늘 유니온이겠지**」 — **반공변 자리에서는 교차**다(2절 7행).
- ★ 「**`infer N` 이면 숫자로 나오겠지**」 — `extends number` 를 안 붙이면 **문자열**이다(3절 8행).
- ★ 「**에러가 하나뿐이니 나머지는 괜찮겠지**」 — 한계에 닿은 타입의 **뒤가 조용해진다**(5절 9행).
- ★ 「**재귀 조건부는 느리겠지**」 — **이 문서는 시간을 재지 않았다.** 근거 없이 말하지 마라.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(2.8)** | `infer` 가 조건부의 `extends` 오른쪽에서 타입을 뽑는다 | 1절 |
| **언어 보장(2.8)** | 서식이 안 맞으면 거짓 가지로 간다 | 1절 20행 · 3절 9행 |
| **언어 보장(4.8)** | `infer X extends …` 가 **뽑으면서 좁힌다** | 3절 7·8행 |
| **★ 이 판(7.0.2)의 관찰** | ★★ 공변 자리는 **유니온**, 반공변 자리는 **교차** | 2절 6·7행 — **던져서** 얻었다 |
| **★ 이 판의 관찰** | 매개변수를 뽑으면 **레이블이 딸려 온다** | 1절 12행 |
| **★ 이 판의 관찰** | 종료 가지가 없으면 `TS2589` 가 아니라 **`TS2456`** | 5절 11행 |
| **★★★ 구현(tsc 7.0.2) 층** | ★★★ **`TS2589` 의 경계 길이** | 5·6절 — **명세가 정한 수가 아니다.** 판이 오르면 **다시 재라** |
| **★★★ 구현 층** | ★★★ **갈리는 축이 「쌓기」라는 것** | 6절 격자 — **왜 그런지는 공개 문서에 없다.** 「갈린다」만 확인했다 |
| **이 판의 관찰** | 유니온 원소의 **표시 순서** | 9절 — 5회 md5 가짓수 1. **관찰이지 보장이 아니다** |
| **이 판의 관찰** | 진단 **문구** 전문 | 코드(`TS2589`·`TS2456`·`TS2322`)가 더 오래 간다 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — 방출기가 **계산하지 않는다** | 0절 |
| **★ 부적용 — 3창(`.js`)** | ★★ **잴 것이 없다** — 전부 타입 층이다 | `.js` 블록이 **하나도 없다** |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 같다** | 9절 |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 | **재지 않았다.** [목록의 **45번 주제**](../45-type-level-performance/)로 넘긴다 |

★★★ **이 주제는 「구현 층」 칸이 유난히 무겁다.** 그리고 그 칸이 **문서의 결론을 이룬다** —
그래서 **경계 길이를 본문의 주장으로 쓰지 않고 블록에만 두었다.**

## 언제 쓰고 언제 안 쓰나

| `infer` 를 쓴다 | 안 쓴다 |
|---|---|
| 남이 만든 타입에서 **속을 꺼내야** 할 때(반환·원소·인스턴스) | 내가 만든 타입이라 **처음부터 타입 매개변수로 받을 수 있을** 때 |
| 서식이 **한 가지로 고정**될 때 | 서식이 여러 가지라 **안 맞으면 조용히 `never`** 가 될 때 — 그때는 `IsNever` 로 막아라 |
| 표준 도구(`ReturnType`·`Awaited`)로 **모자랄** 때 | 표준 도구가 이미 있을 때 — [목록의 **28번 주제**](../28-utility-types/) |

| 재귀 조건부를 쓴다 | 안 쓴다 |
|---|---|
| 문자열 경로·튜플처럼 **길이가 정해진 것**을 다룰 때 | 길이가 **입력에 따라 커지는** 것 — 6절의 벽에 닿는다 |
| 겹마다 **쌓지 않는** 꼴로 쓸 수 있을 때 | 겹마다 **튜플을 다시 펼쳐야** 하는 꼴일 때 |
| 종료 가지가 **한눈에 보이는** 모양일 때 | 종료 가지를 못 적겠을 때 — `TS2456` 이 기다린다 |

## 핵심 문장

1. **`infer` 는 서식에 뚫은 빈칸이다** — 맞으면 이름이 생기고, 안 맞으면 조용한 `never` 다.
2. **탐침은 `never` 앞에서 침묵한다** — `IsNever` 로 바꿔 물어야 「답」과 「안 물음」이 갈린다.
3. **같은 이름이 두 자리면 자리가 합치는 법을 정한다** — 공변은 유니온, 반공변은 교차.
4. **재귀는 종료 가지로 산다** — 없으면 깊이 문제가 아니라 순환 정의 문제로 잡힌다.
5. **★★★ 한계를 정하는 것은 겹 수가 아니라 겹마다 쌓는 것이다** — 꼬리 재귀는 축이 아니었다.
6. **그 경계는 구현 층이다** — 수를 외우지 말고 **자기 판에서 다시 재라**.

## 관련 자료

- [**24번 주제** — 조건부 타입과 분배](../24-conditional-types-and-distribution/) — ★★★ **선행.** `infer` 는 그 조건부 안에 사는 낱말이다. **먼저 읽어라.**
- [**22번 주제** — `keyof` 와 인덱스 접근 타입](../22-keyof-and-indexed-access-types/) — 사슬의 시작. 4절의 `T["length"]` 가 그쪽 문법이다.
- [**23번 주제** — `typeof` 타입 연산자](../23-typeof-type-operator/) — 1절 17행의 `typeof Point` 가 **생성자 쪽**이라는 사실은 그쪽이 정본이다.
- [**17번 주제** — 변성과 매개변수 양립성](../17-variance-and-parameter-compatibility/) — ★★ 2절의 「왜 자리에 따라 갈리나」는 그쪽이 정본. 여기는 **`infer` 가 그 규칙을 따른다**까지.
- [**10번 주제** — 인터섹션 타입](../10-intersection-types/) — 교차가 `never` 로 무너지는 것은 그쪽.
- [**16번 주제** — 함수 타입과 오버로드](../16-function-types-and-overloads/) — 1절이 뽑는 반환·매개변수의 모양은 그쪽.
- [**19번 주제** — 제네릭 기본](../19-generics-basics/) — 타입 매개변수가 채워지는 기제. `infer` 는 **그 반대 방향**이다.
- [**20번 주제** — 제네릭 제약과 기본 타입 인자](../20-generic-constraints-and-defaults/) — 8절의 「모양이냐 이름이냐」 축을 **그쪽에서 인용**했다.
- [**21번 주제** — 추론 제어](../21-inference-control-const-and-noinfer/) — 9절의 `--strict` 대조가 **그쪽과 다른 결과**다.
- [목록의 **27번 주제**](../27-template-literal-types/)(템플릿 리터럴 타입) — 3·4절의 `` `${…}` `` 서식은 그쪽이 정본. 여기는 **`infer` 와 만나는 자리**까지.
- [목록의 **28번 주제**](../28-utility-types/)(유틸리티 타입) — `Awaited`·`ReturnType`·`Parameters` 의 정본. 여기는 **그것들이 재귀 조건부라는 사실**까지.
- [목록의 **45번 주제**](../45-type-level-performance/)(타입 수준 성능) — ★★★ **검사 시간은 그쪽이다.** 이 문서는 **재지 않았다.**
- 목록의 **46번 주제**(가변 튜플 타입) — 6절의 `[...A<R>, H]` 문법이 그쪽이다.
- `` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **18번**([와일드카드와 PECS — `? extends`/`? super`](../../../java/syntax/18-wildcards-pecs/)) `` — 7절의 정본.
- `` Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**([트레이트 정의·구현·기본 메서드·연관 타입](../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/)) `` — 8절의 정본.

## 용어 풀이

> **`infer`** — 조건부 타입의 `extends` **오른쪽**에서만 쓰는 낱말. 그 자리에 들어온 타입에 **이름을 붙인다**.\
> 예: `T extends (infer U)[] ? U : never` 에서 `T` 가 `string[]` 이면 `U` 는 `string` 이다.

> **서식 맞추기(pattern matching)** — 타입을 **모양으로** 견주어 맞는지 보는 것.\
> 예: `(infer U)[]` 는 「무언가의 배열」이라는 모양이고, `string` 은 그 모양이 아니라 안 맞는다.

> **종료 가지(base case)** — 재귀가 더는 안 맞을 때 가는 `else` 쪽. 재귀는 이것으로 멈춘다.\
> 예: `Split` 은 구분자가 없으면 `[S]` 를 돌려주고 거기서 끝난다.

> **꼬리 재귀 꼴(tail-recursive form)** — 재귀 호출의 결과를 **다른 것으로 감싸지 않고 그대로** 돌려주는 모양.\
> 예: `B<R, [H, ...Acc]>` 는 꼬리 꼴이고, `[...A<R>, H]` 는 결과를 다시 튜플에 넣으므로 아니다.

> **누산기(accumulator)** — 재귀가 지나가며 결과를 모아 두는 **여벌 타입 매개변수**.\
> 예: `type B<T, Acc = []>` 의 `Acc` — 호출자는 안 적고 재귀가 채운다.

> **튜플 스프레드** — `[...X, H]` 처럼 **기존 튜플을 펼쳐 새 튜플을 만드는** 문법.\
> 예: `[...[1,2], 3]` 은 `[1,2,3]` 이다. 겹마다 하면 **앞의 것을 매번 다시 펼친다**.

> **`TS2589`** — 「Type instantiation is excessively deep and possibly infinite.」\
> 예: 종료 가지가 있는데도 너무 깊으면 난다(5절 8행). **깊이가 아니라 쌓기가 부른다**(6절).

> **`TS2456`** — 「Type alias … circularly references itself.」\
> 예: `Endless<T> = Endless<[...T,1]>` 처럼 **종료 가지가 아예 없을** 때 난다(5절 11행).

> **포획(capture conversion)** — Java 가 `List<?>` 의 `?` 에 **임시 이름**(`CAP#1`)을 붙이는 것.\
> 예: `xs.set(0, xs.get(0))` 이 막히는 것은 두 `CAP#1` 이 같다는 보장을 **적을 수 없기** 때문이다(7절).

> **연관 타입(associated type)** — Rust 에서 트레이트가 **미리 선언해 둔** 타입 이름.\
> 예: `trait Source { type Item; }` 의 `Item` — 선언에 없는 것은 `S::Item` 으로 못 꺼낸다(8절).

> **에러 타입** — 검사에 실패한 타입이 그 뒤 검사에서 **아무 말도 안 하게 되는** 상태.\
> 예: 5절 9행 — `TooDeep` 이 `TS2589` 로 죽은 뒤 그 탐침은 **진단이 없다**.

## 더 들어가면

- **왜 `infer` 가 조건부 안에만 사는가** — 뽑기는 **「맞았을 때만」** 뜻이 있다.
  안 맞았을 때 `U` 가 무엇인지는 정할 수가 없으므로, **거짓 가지가 반드시 짝으로 있어야** 문법이 닫힌다.
  그래서 `type Elem<T> = infer U` 같은 꼴은 애초에 없다. 1절 20행의 **조용한 `never`** 는 그 설계의 대가다.
- **왜 반공변 자리에서 교차가 되는가** — 2절의 그림이 답이다. 내주는 자리는 「둘 중 하나가 나온다」라
  **유니온**이 맞고, 받는 자리는 「둘 다 받아야 한다」라 **교차**가 맞다.
  ★ 다만 **이것을 명세 문장으로 확인하지 않았다** — 6·7행의 출력에서 **읽은 것**이다.
  [**17번 주제**](../17-variance-and-parameter-compatibility/)의 규칙과 앞뒤가 맞는다는 것까지가 이 문서의 주장이다.
- **6절의 격자를 더 밀면 무엇이 나오나** — C·E 가 **어디서 막히는지는 안 찾았다.**
  다섯 길이만 던졌고 그 위는 **안 던졌다.** 「C·E 는 한계가 없다」가 아니라 「**이 다섯 자리에서 안 막혔다**」가
  이 문서가 말할 수 있는 전부다. 상한을 알고 싶으면 격자의 길이 목록을 늘려 다시 돌려라 — 스크립트가 그 자리에 있다.
- **`TS2589` 를 만나면 무엇부터 보나** — 순서는 ① **종료 가지가 있나**(없으면 `TS2456` 이 먼저 뜬다)
  ② **겹마다 튜플을 다시 펼치고 있나**(6절의 A 꼴) ③ 그다음에야 꼬리 꼴을 생각한다.
  ★ 흔한 처방인 「꼬리 재귀로 바꿔라」를 **①②보다 먼저 쓰면 헛수고**가 될 수 있다 — 6절의 C 가 그 반례다.
- **탐침의 침묵을 아예 없앨 수 있나** — `IsNever` 말고도 길은 있다.
  거짓 가지를 `never` 대신 **눈에 띄는 리터럴**(`"안 맞음"`)로 두면 탐침이 말을 한다.
  ★ 이 배치에서는 **표준 유틸리티의 모양을 그대로 흉내 내려고** `never` 를 유지했다.
  실무에서 자기 타입을 만들 때는 **거짓 가지를 리터럴로 두고 디버깅한 뒤 `never` 로 바꾸는** 쪽이 싸다. **안 던져 봤다.**
