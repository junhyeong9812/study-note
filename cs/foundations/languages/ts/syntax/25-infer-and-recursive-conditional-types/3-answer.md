# ts/syntax/25 — `infer` 와 재귀 조건부 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자는 `tsc` **7.0.2** · `javac` **21.0.5** · `rustc` **1.92.0** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★★★ **그런데 답이 `never` 면 탐침이 침묵한다.** 그래서 소스마다 `IsNever` 가 끼어 있다 —
> **진단이 없는 줄도 답**이라는 것을 아래 표들이 명시한다.\
> ★★ 이 주제의 **본체 창은 4창(종료 코드 격자)이다** — 5·6번이 결론을 낸다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 다섯 자리 다 뽑힌다 — 그리고 **안 맞는 줄은 조용하다**

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 9 | `Elem<string[]>` | `string` |
| 10 | `Elem<[1, "가"]>` | **`"가" \| 1`** — 원소가 유니온으로 합쳐진다 |
| 11 | `Ret<(x: number) => string>` | `string` |
| 12 | ★★★ `Par<(x: number, y: string) => void>` | **`[x: number, y: string]`** — ★ **레이블이 살아 있다** |
| 17 | `Inst<typeof Point>` | `Point` — ★ 생성자에서 인스턴스를 도로 꺼낸다 |
| 18 | `Head<[1, 2, 3]>` | `1` |
| **20** | ★★★ `Elem<string>` | **진단이 없다** — 답이 `never` 다 |
| 21 | `IsNever<Elem<string>>` | **`"never 다"`** — 침묵을 글자로 바꾼 줄 |
| 22 | ★★ `IsNever<Elem<readonly [1, "가"]>>` | **`"never 다"`** — `readonly` 튜플은 안 맞는다 |

- ★★ **진단이 여덟 건**이다. 그런데 **탐침은 아홉 개**를 달았다 — **20행 하나가 빠졌다.**
  그 하나가 이 문항의 과녁이다.
- ★★★ 12행이 가장 뜻밖이다. 매개변수를 뽑으면 **튜플로 나오는 것까지는** 예상해도
  **`x`·`y` 라는 이름이 타입 글자에 남는다.** 이름은 타입이 아닌데 **표시에는 남는다** —
  `Parameters<T>` 를 써 본 적이 있다면 이 글자를 본 적이 있을 것이다([목록의 **28번 주제**](../28-utility-types/)).
- ★★ 17행이 [**23번 주제**](../23-typeof-type-operator/)와 만나는 자리다.
  `typeof Point` 는 **인스턴스가 아니라 생성자 쪽**이고, `new (...) => infer I` 라는 서식이
  그 생성자에서 **인스턴스 쪽을 도로 꺼낸다.** 두 주제가 **정확히 반대 방향**이다.
- ★★★ 22행이 실무에서 가장 자주 밟는 함정이다. `readonly` 튜플은 **가변 배열 서식에 안 맞는다** —
  서식을 `readonly (infer U)[]` 로 바꿔야 잡힌다.
  ★ 그리고 **틀렸다는 신호가 에러가 아니라 `never` 라서** 한참 뒤에야 드러난다.

### 2. ★★★ 공변 자리는 **유니온**, 반공변 자리는 **교차**

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 6 | ★★★ `Co<{ a: string; b: number }>` | **`string \| number`** — 공변 자리 → 유니온 |
| 7 | ★★★ `Contra<{ a: (x: {p:1})=>void; b: (x: {q:2})=>void }>` | **`{ p: 1; } & { q: 2; }`** — 반공변 자리 → 교차 |
| **10** | `Contra<{ a: (x: string)=>void; b: (x: number)=>void }>` | **진단이 없다** — `string & number` 가 `never` 다 |
| 11 | `IsNever<Clash>` | **`"never 다"`** |
| 14 | `CoSame<{ a: "가"; b: "가" }>` | **`"가"`** — 같으면 안 벌어진다 |

- ★★★ 6행과 7행이 이 문항의 전부다. **소스의 모양은 거의 같고 `infer U` 가 놓인 자리만 다르다.**
  `{ a: infer U }` 의 `a` 는 **값을 내주는 자리**, `(x: infer U) => void` 의 `x` 는 **값을 받는 자리**다.
- ★★★ **왜 방향이 갈리는가** — 내주는 쪽에서 둘을 합치면 「**둘 중 하나가 나온다**」라 유니온이 맞고,
  받는 쪽에서 둘을 합치면 「**둘 다 받을 수 있어야 한다**」라 교차가 맞다.
  ★ 이것은 [**17번 주제**](../17-variance-and-parameter-compatibility/)의 변성 규칙과 앞뒤가 맞는다 —
  **그쪽이 정본이고 여기서는 `infer` 가 그 규칙을 따른다는 사실까지**다.
- ★★ 10행이 다시 침묵한다. 반공변 합치기가 **교차를 만드는데**, `string & number` 는
  **양립할 수 없어 `never` 로 무너진다**([**10번 주제**](../10-intersection-types/)).
  그러면 또 진단이 사라진다 — **같은 함정이 두 번째다.**
- ★★ 그래서 **반공변 자리에 같은 이름을 두 번 쓰는 것은 조용히 죽는 길**을 하나 더 만드는 일이다.
  두 자리가 **원시 타입**이면 거의 항상 `never` 가 된다.
- ★ 14행 — 두 자리가 같으면 **합치기가 일어나도 결과가 안 벌어진다**. 「여러 자리 = 항상 벌어짐」이 아니다.

### 3. ★★ `extends` 한 조각이 **글자를 숫자로** 바꾼다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 7 | ★★★ `NumOf<"42">` | **`42`** — 숫자 리터럴 |
| 8 | `NumOfPlain<"42">` | **`"42"`** — 문자열 리터럴 |
| 9 | `IsNever<NumOf<"가">>` | **`"never 다"`** |
| 10 | `FirstChar<"가나다">` | **`"가"`** |
| 13 | `HeadStr<["가", 1]>` | **`"가"`** |
| 14 | `IsNever<HeadStr<[1, "가"]>>` | **`"never 다"`** |

- ★★★ 7행과 8행의 **입력이 글자까지 같다.** 다른 것은 `extends number` 한 조각뿐인데
  답이 **`42`** 와 **`"42"`** 로 갈린다. 앞의 것은 **숫자 리터럴 타입**이라
  `Add`·`Compare` 같은 것을 이어 쓸 수 있고, 뒤의 것은 못 쓴다.
- ★★ 9행 — `"가"` 는 숫자로 못 좁히므로 **조건 전체가 거짓**이 되어 `never` 다.
  ★★★ 「뽑기는 성공하고 좁히기만 실패」 같은 **중간 상태가 없다** — **거르면서 뽑는다.**
- ★★ 13·14행이 그 성질을 튜플에서 다시 보인다. 머리가 `string` 이 아니면
  **머리만 버리는 게 아니라 조건 전체가 거짓**이다. 그래서 14행이 `never` 다.
- ★ 10행 — 템플릿 서식은 **앞에서부터** 맞춘다. `${infer C}${string}` 의 `C` 는 첫 글자 하나다.
  ★ 「첫 글자」가 **코드 포인트 하나인지 코드 유닛 하나인지**는 [목록의 **27번 주제**](../27-template-literal-types/)의 몫이다 —
  **이 문서는 한글 한 글자만 던졌고 그 경계는 안 던졌다.**

### 4. ★★ 재귀는 **한 겹씩 벗겨** 끝까지 간다 — 그리고 왕복이 맞는다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 11 | `Split<"가.나.다", ".">` | **`["가", "나", "다"]`** |
| 12 | `Rev<[1, 2, 3, 4]>` | **`[4, 3, 2, 1]`** |
| 13 | `Join<["가","나","다"], "-">` | **`"가-나-다"`** |
| 14 | ★★★ `Join<Split<"가.나.다", ".">, "-">` | **`"가-나-다"`** — 13행과 **같은 글자** |
| 16 | `MyAwaited<Promise<Promise<number>>>` | **`number`** |
| 17 | `Awaited<Promise<Promise<Promise<string>>>>` | **`string`** |
| 18 | `Awaited<number>` | **`number`** — 감싼 것이 없으면 그대로 |

- ★★ 11행 — `` `${infer H}${D}${infer R}` `` 서식이 **머리와 꼬리를 한 번에** 갈라 준다.
  꼬리를 자기에게 다시 넘기고, 구분자가 없어지면 **종료 가지 `[S]`** 로 끝난다.
- ★★★ 13행과 14행이 **한 글자도 같다.** 쪼갠 것을 도로 붙였더니 원본이 나왔다 —
  **두 재귀가 서로의 역함수**임이 출력 한 쌍으로 증명된다.
  ★ 이런 **왕복 검사**는 재귀 타입을 짤 때 가장 싼 자기 검증이다.
- ★★ 16·17행 — 직접 만든 `MyAwaited` 와 표준 `Awaited` 가 **같은 일을 한다.**
  17행은 **세 겹**을 벗겼다. ★ **`Awaited` 가 재귀 조건부라는 사실**이 여기서 드러난다 —
  한 겹만 벗기는 도구라면 `Promise<Promise<string>>` 이 나와야 했다.
- ★ 18행이 **종료 가지**다. `Promise` 가 아니면 **그대로 돌려준다.**
  ★★ 종료 가지가 없는 재귀가 어떻게 되는지는 5번이 답한다.

```text
  왕복이 맞는다 — 13행과 14행

  "가.나.다"  ──Split──▶  ["가","나","다"]  ──Join──▶  "가-나-다"
                                                          ║
  "가.나.다"  ───────────────Join<Split<…>>──────────▶  "가-나-다"
                                                     ★ 같은 글자다
```

### 5. ★★★ 한 칸 차이로 `TS2589` — 그리고 **종료 가지가 없으면 다른 진단**

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 6 | `Count<[], 999>` | **끝까지 돌았다** — 탐침이 길이를 말한다 |
| 8 | ★★★ `Count<[], 1000>` | **`TS2589`** 「Type instantiation is excessively deep and possibly infinite.」 |
| **9** | ★★ `TooDeep["length"]` | **진단이 없다** — 앞 줄이 죽어 뒤가 조용해졌다 |
| 11 | ★★★ `Endless<T> = Endless<[...T, 1]>` | **`TS2456`** 「circularly references itself」 + **`TS2315`** |
| 12 | `Endless<[]>` 사용처 | **`TS2315`** 「is not generic」 |

- ★★★ 6행과 8행은 **한 칸 차이**다. 한쪽은 끝까지 돌아 답을 내고, 다른 쪽은 벽에 닿는다.
  ★★ **그 경계 길이를 외우지 마라** — 6번이 왜인지 답한다.
- ★★★ **9행에 진단이 없는 것**이 실무에서 위험하다. `TooDeep` 이 이미 실패했으므로
  **그 타입을 쓰는 뒤쪽이 전부 조용해진다.** 「에러가 하나뿐이니 나머지는 멀쩡하겠지」로 읽으면
  **고치고 나서 새 에러가 우수수 나온다.**
- ★★★ 11·12행이 **완전히 다른 진단**이다. 종료 가지가 **아예 없는** 재귀는
  **돌려 보기 전에** 순환 정의로 잡힌다(`TS2456`). 그리고 그 별칭이 망가졌으므로
  쓰는 자리마다 `TS2315` 가 따라붙는다.
  ★ 즉 **`TS2589` 를 만났다면 종료 가지는 있는 것**이다 — 없었으면 `TS2456` 이 먼저 떴다.

```text
  TS2589 를 만났을 때 보는 순서

  ① 종료 가지가 있나?          없으면 TS2456 이 먼저 뜬다 → 여기 아니다
        │ 있다
        ▼
  ② 겹마다 튜플을 다시 펼치나?  [...X<R>, H] 꼴이면 여기다  → 6번의 A
        │ 아니다
        ▼
  ③ 그제야 꼬리 꼴을 생각한다    ★ ①②보다 먼저 하면 헛수고일 수 있다
```

### 6. ★★★ 먼저 막히는 것은 **A 하나** — 갈리는 축은 「꼬리냐」가 아니었다

**출력**

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

**왜 그런가**

| 꼴 | 모양 | 꼬리 재귀인가 | 격자에서 |
|---|---|---|---|
| **A** | `[...A<R>, H]` — 튜플 스프레드 | 아니다 | ★★★ **가장 먼저 막힌다** |
| **B** | `B<R, [H, ...Acc]>` — 누산기 | **맞다** | 훨씬 멀리 가지만 **끝내 막힌다** |
| **C** | `[C<R>, H]` — 스프레드 없음 | **아니다** | ★★★ **다섯 길이 전부 통과** |
| **E** | `{ n: E<R> }` — 객체로 감쌈 | **아니다** | ★★★ **다섯 길이 전부 통과** |

- ★★★ **C 가 반례다.** A 와 C 는 **점 세 개 차이**뿐이고 둘 다 꼬리 재귀가 아니다.
  그런데 A 만 막힌다. 그러므로 **「꼬리 재귀로 바꾸면 한계가 풀린다」는 이 판에서 틀린 요약**이다.
- ★★★ **E 도 같은 말을 한다.** 결과를 객체로 감싸기만 해도 끝까지 간다 —
  **겹 수는 그대로인데** 결과가 달라진다.
- ★★★ 그래서 결론은 「**한계를 정하는 것은 겹 수가 아니라 겹마다 쌓는 것이다**」이고,
  A 와 B 의 공통점은 **둘 다 튜플 스프레드를 한다**는 것이다.
- ★★ **주장은 성질까지만** 한다 — 「**스프레드를 쌓는 꼴은 수십에서 막히고, 안 쌓는 꼴은 천을 넘겨도 산다 — 스무 배가 넘는 차이**」.
  정확한 길이는 **블록 안에 있고 본문은 그것을 주장으로 쓰지 않는다.**
- ★★★ **그 경계 길이는 구현(tsc 7.0.2) 층이다.** 명세가 정한 수가 아니고, **판이 오르면 다시 재야 한다.**
  스크립트가 이 문서의 블록에 그대로 실려 있으니 **길이 목록만 바꿔 다시 돌리면 된다.**
- ★★ **왜 스프레드가 비싼지는 안 물었다.** 컴파일러 내부의 계수 규칙이고 **공개 문서에 정리돼 있지 않다.**
  이 문서가 말할 수 있는 것은 「**갈린다**」까지다.
- ★★★ **시간은 재지 않았다.** 그래서 이 문서 어디에도 **「느리다」는 말이 없다** —
  검사 비용은 [목록의 **45번 주제**](../45-type-level-performance/)의 몫이다.

### 7. ★★★ 뽑기는 「맞았을 때만」 뜻이 있어서 — 안 맞으면 거짓 가지로 간다

**왜 그런가**

- ★★★ `infer` 는 **조건부의 `extends` 오른쪽에서만** 산다. 그 자리는 애초에
  **「맞나 안 맞나」를 묻는 자리**이고, 안 맞았을 때 갈 곳이 **거짓 가지**로 이미 있다.
  그러니 **에러를 낼 이유가 없다** — 문법이 그 경우를 이미 처리하고 있다.
- ★★ 뒤집어 말하면 **`type Elem<T> = infer U` 같은 꼴은 애초에 없다.**
  안 맞았을 때 `U` 가 무엇인지 정할 수 없으므로 **거짓 가지가 반드시 짝으로 있어야** 문법이 닫힌다.
- ★★★ 대가는 1번 20행이다 — **틀린 서식이 에러가 아니라 `never` 로 번진다.**
  그리고 `never` 는 **아무 데나 할당되므로** 한참 뒤의 엉뚱한 자리에서 증상이 나온다.
- ★ 처방 — 자기 타입을 만들 때는 **거짓 가지를 `never` 말고 눈에 띄는 리터럴**(`"안 맞음"`)로 두고
  디버깅한 뒤 바꾸는 쪽이 싸다. ★★ **이 배치에서는 표준 유틸리티의 모양을 흉내 내려고 `never` 를 유지했고,
  리터럴 쪽은 안 던져 봤다.**

### 8. ★★★ `never` 는 모든 타입에 할당되므로 — `IsNever` 로 창을 바꿨다

**왜 그런가**

- ★★★ 탐침은 「**이 타입은 `null` 에 할당될 수 없다**」는 에러를 이용한다.
  그런데 `never` 는 **모든 타입의 부분 타입**이라 `null` 에도 할당된다 —
  그래서 `const probe: null = null as unknown as never;` 는 **통과한다.**
- ★★★ 그러면 **「답이 `never` 다」와 「내가 안 물어봤다」가 출력에서 구분되지 않는다.**
  침묵이 두 가지를 뜻하게 된다.
- ★★ 그래서 창을 바꿨다 — `type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다"`.
  `[T]` 로 감싸는 것이 핵심이고, **그 이유는 [24번 주제](../24-conditional-types-and-distribution/)에 있다**
  (네이키드로 두면 `never` 가 분배에서 사라져 결과가 `never` 가 된다).
- ★★ 이것이 **제5의 상태**다 — 「못 잰 것」도 「잴 것이 없는 것」도 아니고 **창을 바꿔 답한 것**이다.
- ★ **바꾼 창이 못 보는 것** — `IsNever` 는 「never 인가」만 답하고 **무엇인지는 말하지 않는다.**
  그래서 소스마다 **침묵하는 탐침 한 줄과 `IsNever` 한 줄을 나란히** 두었다(1번 20·21행 · 2번 10·11행).

### 9. ★★ `TS2589` 는 「깊다」, `TS2456` 은 「끝이 없다」

**왜 그런가**

| 진단 | 언제 | 무엇이 잘못됐나 |
|---|---|---|
| **`TS2589`** | 종료 가지가 **있는데** 너무 깊을 때 | 겹마다 쌓는 것이 많다(6번) |
| **`TS2456`** | 종료 가지가 **아예 없을** 때 | 정의가 자기를 순환 참조한다 |
| **`TS2315`** | `TS2456` 뒤에 따라온다 | 망가진 별칭을 **쓰는 자리마다** |

- ★★★ 갈리는 지점은 「**돌려 보기 전에 걸리느냐, 돌다가 걸리느냐**」다.
  `TS2456` 은 정의만 보고도 알 수 있어 **돌리기 전에** 잡히고,
  `TS2589` 는 **실제로 돌다가** 한계에 닿아 잡힌다.
- ★★★ **`TS2589` 를 만났다면 종료 가지는 있는 것**이다. 그러니 확인 순서는
  ① 종료 가지 → ② 겹마다 튜플을 다시 펼치나 → ③ 그제야 꼬리 꼴이다(5번의 그림).
- ★★ **흔한 처방인 「꼬리 재귀로 바꿔라」를 ①②보다 먼저 쓰면 헛수고가 될 수 있다** —
  6번의 C 가 그 반례다. 꼬리가 아닌데도 끝까지 간다.
- ★ 그리고 `TS2589` 가 뜬 뒤에는 **그 타입을 쓰는 자리가 조용해지므로**(5번 9행)
  「에러 하나만 고치면 끝」이 아니다.

### 10. ★★ 길이가 입력에 따라 커지면 벽이 기다린다 — 경계를 외우면 안 되는 이유

**왜 그런가**

| 재귀 조건부를 쓴다 | 안 쓴다 |
|---|---|
| 경로 문자열·튜플처럼 **길이가 소스에 적혀 있는** 것 | 길이가 **입력 데이터에 따라 커지는** 것 |
| 겹마다 **쌓지 않는** 꼴로 쓸 수 있을 때 | 겹마다 **튜플을 다시 펼쳐야** 하는 꼴일 때 |
| 종료 가지가 **한눈에 보이는** 모양일 때 | 종료 가지를 못 적겠을 때 — `TS2456` 이 기다린다 |

- ★★★ **경계 길이를 외우면 안 되는 이유는 셋**이다.
  ① 그 수는 **명세가 아니라 구현(tsc 7.0.2)이 정한 것**이라 판이 오르면 바뀔 수 있다.
  ② **꼴마다 다르다** — 6번 격자에서 같은 겹 수인데 A 는 막히고 C·E 는 통과했다.
  ③ ★★ **같은 꼴이라도 다른 타입과 섞이면 계수가 달라질 수 있다** — 이 문서는 **격자 밖은 안 던졌다.**
- ★★ 그러므로 실무 규칙은 **수가 아니라 모양**이다 — 「겹마다 튜플을 다시 펼치는 꼴을 피한다」.
- ★ 그리고 **자기 판에서 다시 재는 것**이 답이다. 격자 스크립트가 6번 블록에 통째로 실려 있다 —
  길이 목록만 바꿔 다시 돌리면 된다.
- ★ 한계 자체를 넓히고 싶은 것이 아니라 **검사 비용이 궁금한 것**이라면 [목록의 **45번 주제**](../45-type-level-performance/)가 그 자리다.
  **이 문서는 시간을 재지 않았다.**

### 11. ★★★ `CAP#1` 은 Java 의 `infer` 다 — 다만 **그 이름을 적을 수 없다**

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| Java 5 | `List<?>` 에서 꺼내 도로 넣기 | **막힌다** — `CAP#1` 이 둘 다 같다는 보장을 못 적는다 |
| **Java 9** | ★★★ 제네릭 헬퍼 `<T>` 로 감싼 같은 몸통 | **진단이 없다** — 이름이 생겼다 |
| Java 13 | `? extends CharSequence` 에 넣기 | **막힌다** — `CAP#1` 이 `String` 이라는 보장이 없다 |
| Rust 22 | `let probe: u8 = pull(&c);` | **`expected u8, found u32`** — 탐침이 통한다 |

- ★★★ javac 가 **`CAP#1 is a fresh type-variable: CAP#1 extends Object from capture of ?`** 라고
  말한다. **이름 없는 타입에 임시 이름을 붙인 것** — 하는 일이 TS 의 `infer` 와 같다.
- ★★★ **다른 것은 그 이름을 쓸 수 있느냐**다. Java 는 `CAP#1` 을 **소스에 적을 수 없다.**
  그래서 5행은 꺼낸 것을 도로 넣는 것뿐인데 막힌다 — 두 `CAP#1` 이 같다고 **말할 방법이 없다.**
- ★★★ **9행에 진단이 없는 것**이 답의 절반이다. 몸통이 5행과 **글자까지 같은데** 통과한다 —
  `<T>` 로 감싸 **이름을 줬기** 때문이다. 이것이 Java 의 「capture helper」 관용구다.
  ★ 즉 **Java 는 포획한 타입에 이름을 주려고 메서드를 하나 더 만들고, TS 는 `infer U` 한 낱말로 끝낸다.**
- ★★ 13행은 경계가 붙은 포획이다. `? extends CharSequence` 라도 **넣기는 막힌다** —
  꺼내기만 되는 자리다. 그 규칙(PECS)의 정본은
  `` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **18번**([와일드카드와 PECS — `? extends`/`? super`](../../../java/syntax/18-wildcards-pecs/)) ``이다.
- ★★ Rust 쪽은 **같은 탐침 수법이 통한다**는 것이 첫째다 — 일부러 `u8` 이라 적으니 `u32` 라고 말해 준다.
  ★★★ 둘째가 더 중요하다 — `S::Item` 은 **트레이트가 미리 선언한 이름**이라야 꺼낼 수 있다.
  `trait Source { type Item; }` 에 **그 줄이 없으면** 꺼낼 길이 없다.
- ★★★ 그래서 가르는 한 낱말은 「**근거**」다 — TS 는 **모양**에서 꺼내고 Rust 는 **이름**으로 꺼낸다.
  ★ 이 축은 [**20번 주제**](../20-generic-constraints-and-defaults/)가 이미 실측한 것이고 여기서는 **인용했다.**
  정본은 `` Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**([트레이트 정의·구현·기본 메서드·연관 타입](../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/)) ``이다.
- ★ 대가 — 모양으로 꺼내면 **남이 만든 타입에서도 꺼낼 수 있지만**, 상대가 모양을 바꾸면 **조용히 `never`** 가 된다.

### 12. ★★ 세 층 — 그리고 이 문서에 「느리다」가 없는 이유

**왜 그런가**

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장(2.8·4.8)** | `infer` 가 조건부의 `extends` 오른쪽에서 타입을 뽑는다 · 서식이 안 맞으면 거짓 가지로 간다 · `infer X extends …` 가 뽑으면서 좁힌다 |
| **★★★ 구현(tsc 7.0.2) 층** | ★★★ **`TS2589` 의 경계 길이**(5·6번) · ★★★ **갈리는 축이 「쌓기」라는 것**(6번) · 종료 가지가 없을 때 `TS2456` 이 먼저 뜨는 것 |
| **★ 이 판의 관찰** | 공변 → 유니온 · 반공변 → 교차(2번) · 매개변수 레이블이 살아 있는 것(1번 12행) · 유니온 **표시 순서** · 진단 **문구** 전문 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — 방출기가 **계산하지 않는다** |
| **★ 부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** — `infer` 도 재귀도 전부 타입 층이다. 이 문서에 `.js` 블록이 **하나도 없다** |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 한 글자도 같다** |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 |

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

- ★★★ **이 주제는 「구현 층」 칸이 결론을 이룬다.** 그래서 **경계 길이를 본문의 주장으로 쓰지 않고**
  블록에만 두고, 본문은 **성질**만 말했다.
- ★★★ **「느리다」가 한 줄도 없는 이유는 안 쟀기 때문**이다. `TS2589` 는 **참/거짓**이고 **시간이 아니다.**
  「막힌다」와 「느리다」는 **다른 주장**이고, 이 문서는 앞의 것만 근거가 있다.
  ★★ 재지 않은 성능 주장은 **그럴듯해서 더 위험하다** — 「재귀 조건부는 컴파일을 느리게 한다」는
  자주 들리지만 **이 문서는 그 말을 뒷받침할 근거를 하나도 갖고 있지 않다.**
- ★★ `--strict` 대조가 [**21번 주제**](../21-inference-control-const-and-noinfer/)와 다르다 —
  거기서는 여섯 중 하나가 갈렸고 **여기서는 다섯 중 하나도 안 갈렸다.**
  「추론은 설정을 타고 계산은 안 탄다」로 읽고 싶지만, 그것은 **다섯 파일에서 본 것**이지 규칙이 아니다.
- ★ 유니온 **표시 순서**는 5회 md5 가짓수가 1 이다 — **관찰이지 보장이 아니다.**
  이 문서에 순서를 근거로 삼는 문장은 **없다.**

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `javac -version` · `rustc --version` | `Version 7.0.2` · `v18.19.1` · `javac 21.0.5` · `rustc 1.92.0` |
| `infer` 다섯 자리 | `--noEmit ex.25a.ts` | exit 1 · **8건** · ★ 탐침 9개 중 **1개가 침묵**(20행) |
| 공변·반공변 | `--noEmit ex.25b.ts` | exit 1 · **4건** · `string \| number` 대 `{ p: 1; } & { q: 2; }` |
| `infer X extends` | `--noEmit ex.25c.ts` | exit 1 · **6건** · `42` 대 `"42"` |
| 재귀 조건부 | `--noEmit ex.25d.ts` | exit 1 · **7건** · ★ 13·14행 **왕복이 같은 글자** |
| ★★★ 깊이 한계 | `--noEmit ex.25e.ts` | exit 1 · **5건** · `TS2589` 1건 · `TS2456` 1건 · `TS2315` 2건 |
| ★★★ 격자 | `bash ts22b-depth.sh` (네 꼴 × 다섯 길이 = **20회 컴파일**) | exit 0 · ★ **A 만 일찍 막힌다** · C·E 는 **다섯 길이 전부 통과** |
| Java 포획 | `javac -d jout Capture.java` | exit 1 · **2건** · ★ 제네릭 헬퍼 쪽은 **진단 없음** |
| Rust 연관 타입 | `rustc --crate-name assoc --edition 2021 assoc.rs` | exit 1 · **`E0308`** · `expected u8, found u32` |
| `strict` 대조 | 다섯 파일을 `--strict false` 로 재실행 | ★ **하나도 안 갈림** — 21 과 다르다 |
| 반복 실행 | 같은 명령 **5회** | ★★ md5 **가짓수 1** — 유니온 순서가 안 흔들렸다 |
| 5창 부적용 | `--declaration --emitDeclarationOnly` | ★ 조건부가 **안 풀린 채** 방출된다 — **잴 것이 없다** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **`TS2589` 의 경계 길이**(5·6번) — **명세가 정한 수가 아니다.** tsc 7.0.2 의 계수 규칙이다.
  ★ 그래서 **본문은 그 수를 주장으로 쓰지 않았고** 블록 안에만 두었다. 판이 바뀌면 **격자를 다시 돌려라.**
- ★★★ **갈리는 축이 「튜플 스프레드를 쌓느냐」라는 것**(6번) — **왜 그런지는 공개 문서에 없다.**
  이 문서가 확인한 것은 「**갈린다**」까지다.
- ★★ **공변 → 유니온 · 반공변 → 교차**(2번) — 출력에서 읽은 것이고, 그 규칙이
  [**17번 주제**](../17-variance-and-parameter-compatibility/)와 앞뒤가 맞는다는 것까지가 주장이다.
- ★★ 매개변수를 뽑을 때 **레이블이 딸려 오는 것**(1번 12행) — 표시 형식이다.
- ★★ 유니온 원소의 **표시 순서** — 5회 동일했지만 **관찰이지 보장이 아니다.**
- ★ 진단 **문구** 전문 — `TS2589`·`TS2456`·`TS2315`·`TS2322`·`E0308` 이라는 **코드**가 더 오래 간다.
- ★ javac 의 `CAP#1` 이라는 **이름 형식**과 `Note:` 요약 줄 — 판본에 매인다.

**안 돌려 본 것**

- ★★★ **검사 시간·메모리** — **재지 않았고 수치를 한 줄도 적지 않았다.** [목록의 **45번 주제**](../45-type-level-performance/)의 몫이다.
- ★★ **C·E 가 어디서 막히는지** — 격자의 다섯 길이 위는 **안 던졌다.**
  「한계가 없다」가 아니라 「**이 다섯 자리에서 안 막혔다**」가 이 문서가 말할 수 있는 전부다.
- ★★ **거짓 가지를 `never` 말고 리터럴로 두는 디버깅 수법** — **안 던졌다**(7번).
- ★ **`infer` 를 매핑 타입·템플릿 리터럴과 더 깊이 엮는 것** — [목록의 **26번 주제**](../26-mapped-types/)·[목록의 **27번 주제**](../27-template-literal-types/).
- ★ **첫 글자 뽑기가 코드 포인트 단위인지 코드 유닛 단위인지** — 한글 한 글자만 던졌다.
  경계(서로게이트 쌍)는 **안 던졌다**. [목록의 **27번 주제**](../27-template-literal-types/).
- ★ **`--noUncheckedIndexedAccess` 등 다른 플래그와의 조합** — `--strict` 온·오프만 대조했다.
