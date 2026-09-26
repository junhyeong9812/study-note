# ts/syntax/24 — 조건부 타입과 분배 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단 전문은 `tsc` **7.0.2** 와 `javac` **21.0.5** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ `const probe: null = …` 은 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> 그러므로 이 문서의 `TS2322` 는 **에러가 아니라 출력**이다. 세지 말고 읽어라.\
> ★★★ 단 **탐침은 `never` 를 못 말한다** — 3·4번에서 `IsNever` 로 **창을 바꿔** 물었다(10번이 그 이야기다).\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 네이키드는 **`"문자" | "아님"`**, 감싼 쪽은 **`"아님"`** — 왼쪽 모양 하나 차이다

**출력**

```ts
// ex.24a.ts
// 분배를 켜고 끄는 대조 -- 같은 조건부를 네이키드로, 그리고 [T] 로 감싸서
type Naked<T> = T extends string ? "문자" : "아님";
type Wrapped<T> = [T] extends [string] ? "문자" : "아님";

const nakedUnion: null = null as unknown as Naked<string | number>;
const wrappedUnion: null = null as unknown as Wrapped<string | number>;
const nakedOne: null = null as unknown as Naked<string>;
const wrappedOne: null = null as unknown as Wrapped<string>;

type ToArr<T> = T extends unknown ? T[] : never;
type ToArrOff<T> = [T] extends [unknown] ? T[] : never;
const arrOn: null = null as unknown as ToArr<string | number>;
const arrOff: null = null as unknown as ToArrOff<string | number>;

type NotNaked<T extends unknown[]> = T[number] extends string ? "문자" : "아님";
const notNaked: null = null as unknown as NotNaked<(string | number)[]>;
console.log(nakedUnion, wrappedUnion, nakedOne, wrappedOne, arrOn, arrOff, notNaked);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.24a.ts (tsc exit=1) =====
ex.24a.ts(5,7): error TS2322: Type '"문자" | "아님"' is not assignable to type 'null'.
  Type '"문자"' is not assignable to type 'null'.
ex.24a.ts(6,7): error TS2322: Type '"아님"' is not assignable to type 'null'.
ex.24a.ts(7,7): error TS2322: Type '"문자"' is not assignable to type 'null'.
ex.24a.ts(8,7): error TS2322: Type '"문자"' is not assignable to type 'null'.
ex.24a.ts(12,7): error TS2322: Type 'string[] | number[]' is not assignable to type 'null'.
  Type 'string[]' is not assignable to type 'null'.
ex.24a.ts(13,7): error TS2322: Type '(string | number)[]' is not assignable to type 'null'.
ex.24a.ts(16,7): error TS2322: Type '"아님"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 5 | ★★★ `Naked<string \| number>` | **`"문자" \| "아님"`** — 원소마다 따로 판정했다 |
| 6 | ★★★ `Wrapped<string \| number>` | **`"아님"`** — 소포째 한 번 판정했다 |
| 7 | `Naked<string>` | `"문자"` |
| 8 | `Wrapped<string>` | `"문자"` — ★ 7행과 **같다** |
| 12 | ★★★ `ToArr<string \| number>` | **`string[] \| number[]`** |
| 13 | ★★★ `ToArrOff<string \| number>` | **`(string \| number)[]`** |
| 16 | ★★ `NotNaked<(string \| number)[]>` | `"아님"` — **감싸지 않았는데도 분배 안 됨** |

- 진단이 **일곱 건**이고 전부 탐침이다.
- ★★★ 5·6행이 이 주제의 전부다. **조건부의 몸통도 같고 인자도 같다.**\
  왼쪽이 `T` 냐 `[T]` 냐 하나만 다른데 답의 **개수**가 달라진다.
- ★★ 5행에만 **들여쓴 연쇄 설명 줄**이 붙어 있다. **유니온일 때만 나오는 줄**이라\
  그 줄이 있는지만 봐도 「답이 여럿인가」를 알 수 있다.
- ★★★ 7·8행이 **함정 방지 장치**다. 인자가 유니온이 아니면 **두 꼴의 답이 같다** —\
  즉 **유니온으로 던져 보지 않으면 분배 버그를 영원히 못 만난다.**
- ★★★ 12·13행이 **실무에서 더 아픈 쌍**이다.\
  `string[] | number[]` 는 「**문자열 배열이거나 숫자 배열이거나**」이고,\
  `(string | number)[]` 는 「**원소마다 문자열이거나 숫자**」다. **서로 다른 타입**이다.
- ★★ 16행 — `T[number]` 는 `T` 가 **인덱스 접근 아래**에 있으므로 네이키드가 아니다.\
  **감싸지 않았는데도 분배가 꺼진다**(7번이 그 정의를 묻는다).

```text
  ★★★ 두 줄을 나란히 — 이 표가 이 주제의 전부다

  왼쪽 모양          인자              결과
  ---------------    --------------    ------------------------
  T                  string | number   "문자" | "아님"      (5행)
  [T]                string | number   "아님"              (6행)
  T                  string            "문자"              (7행)
  [T]                string            "문자"              (8행)   ★ 같다
  T (ToArr)          string | number   string[] | number[] (12행)
  [T] (ToArrOff)     string | number   (string | number)[] (13행)
  T[number]          (string|number)[] "아님"              (16행)  ★ 안 감쌌는데 꺼짐
```

### 2. ★★★ `Naked<never>` 는 **사라지고**(`"never 다"`), `Wrapped<never>` 는 **통과한다**(`"문자"`)

**출력**

```ts
// ex.24b.ts
// never 가 분배에서 사라진다 -- 빈 유니온이기 때문이다
type Naked<T> = T extends string ? "문자" : "아님";
type Wrapped<T> = [T] extends [string] ? "문자" : "아님";
type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

const nakedNever: null = null as unknown as IsNever<Naked<never>>;
const wrappedNever: null = null as unknown as Wrapped<never>;

type Always<T> = T extends unknown ? "항상" : "절대";
const alwaysNever: null = null as unknown as IsNever<Always<never>>;

type BadIsNever<T> = T extends never ? "never 다" : "never 가 아니다";
const badOnNever: null = null as unknown as IsNever<BadIsNever<never>>;
const badOnString: null = null as unknown as BadIsNever<string>;

const swallowed: null = null as unknown as Naked<string | never>;
console.log(nakedNever, wrappedNever, alwaysNever, badOnNever, badOnString, swallowed);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.24b.ts (tsc exit=1) =====
ex.24b.ts(6,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
ex.24b.ts(7,7): error TS2322: Type '"문자"' is not assignable to type 'null'.
ex.24b.ts(10,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
ex.24b.ts(13,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
ex.24b.ts(14,7): error TS2322: Type '"never 가 아니다"' is not assignable to type 'null'.
ex.24b.ts(16,7): error TS2322: Type '"문자"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 6 | ★★★ `IsNever<Naked<never>>` | **`"never 다"`** — 결과가 `never` 로 사라졌다 |
| 7 | ★★★ `Wrapped<never>` | **`"문자"`** — 참 가지로 통과했다 |
| 10 | ★★ `IsNever<Always<never>>` | `"never 다"` — 조건이 **항상 참**인데도 |
| 13 | ★★★ `IsNever<BadIsNever<never>>` | `"never 다"` — 잡으려던 것이 또 `never` 다 |
| 14 | `BadIsNever<string>` | `"never 가 아니다"` |
| 16 | ★★ `Naked<string \| never>` | `"문자"` — `never` 가 **이미 사라진 뒤**다 |

- 진단이 **여섯 건**이다.
- ★★★ **6행** — `never` 는 **원소가 0개인 유니온**이다. 분배는 「원소마다 돈다」이므로 **0번 돈다.**\
  판정을 한 번도 안 했으니 결과도 0개 — **다시 `never`** 다.
- ★★★ **7행이 정반대다.** 감싸면 분배가 안 돌고 **할당 가능성 판정이 그대로** 나온다.\
  `never` 는 **모든 타입에 할당 가능**하므로 `[never] extends [string]` 이 **참**이다.\
  ★★ 같은 성질(**값이 없다**)이 **네이키드에서는 사라짐**으로, **감싼 쪽에서는 통과**로 나타난다.
- ★★ **10행이 오해를 못 박는다.** `Always<T> = T extends unknown ? "항상" : "절대"` 는 **무엇을 넣어도 참**인데\
  `never` 를 넣으면 `"항상"` 이 아니라 **`never`** 다.\
  ★ **조건을 보기 전에 끝난다** — 돌 원소가 없으면 조건식이 **실행되지 않는다.**
- ★★★ **13·14행을 같이 읽어야** 8번의 답이 나온다. `BadIsNever<T> = T extends never ? …` 는\
  `never` 를 넣으면 **분배가 0번 돌아 결과가 `never`**(13행),\
  `never` 가 아닌 것을 넣으면 **거짓**(14행)이다. **참이 나오는 입력이 없다.**
- ★★ **16행** — `string | never` 는 타입이 만들어지는 순간 이미 `string` 이다.\
  **분배 이전에** 흡수된다.

```text
  ★★★ 빈 소포 — 조건을 보기도 전에 끝난다

  Naked<string | number>          Naked<never>            Wrapped<never>
        │                               │                       │
   원소 2개로 쪼갬                 원소 0개로 쪼갬          안 쪼갠다
        │                               │                       │
   2번 판정                        0번 판정                [never] extends [string]?
        │                               │                       │  -> 참
        v                               v                       v
   "문자" | "아님"                  (빈 유니온) = never       "문자"
                                     (6행)                    (7행)

  ★ 왼쪽 둘은 "조건이 무엇이냐"와 무관하다. 오른쪽만 조건을 실제로 본다.
```

### 3. ★★ `boolean` 은 **쪼개지고**(`"거짓" | "참"`), `any` 는 **양쪽 다** 나온다 — 그리고 14행은 침묵한다

**출력**

```ts
// ex.24c.ts
// boolean 은 true | false 로 분배되고, any 는 양쪽이 다 나온다
type Naked<T> = T extends string ? "문자" : "아님";
type Wrapped<T> = [T] extends [string] ? "문자" : "아님";
type IsTrue<T> = T extends true ? "참" : "거짓";
type IsTrueOff<T> = [T] extends [true] ? "참" : "거짓";

const boolNaked: null = null as unknown as Naked<boolean>;
const boolSplit: null = null as unknown as IsTrue<boolean>;
const boolOff: null = null as unknown as IsTrueOff<boolean>;

const anyNaked: null = null as unknown as Naked<any>;
const anyWrapped: null = null as unknown as Wrapped<any>;
const unknownNaked: null = null as unknown as Naked<unknown>;
const neverArg: null = null as unknown as IsTrue<never>;

type Box<T> = T extends unknown ? { v: T } : never;
const boxed: null = null as unknown as Box<boolean>;
console.log(boolNaked, boolSplit, boolOff, anyNaked, anyWrapped, unknownNaked, neverArg, boxed);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.24c.ts (tsc exit=1) =====
ex.24c.ts(7,7): error TS2322: Type '"아님"' is not assignable to type 'null'.
ex.24c.ts(8,7): error TS2322: Type '"거짓" | "참"' is not assignable to type 'null'.
  Type '"거짓"' is not assignable to type 'null'.
ex.24c.ts(9,7): error TS2322: Type '"거짓"' is not assignable to type 'null'.
ex.24c.ts(11,7): error TS2322: Type '"문자" | "아님"' is not assignable to type 'null'.
  Type '"문자"' is not assignable to type 'null'.
ex.24c.ts(12,7): error TS2322: Type '"문자"' is not assignable to type 'null'.
ex.24c.ts(13,7): error TS2322: Type '"아님"' is not assignable to type 'null'.
ex.24c.ts(17,7): error TS2322: Type '{ v: false; } | { v: true; }' is not assignable to type 'null'.
  Type '{ v: false; }' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 7 | ★★★ `Naked<boolean>` | `"아님"` — **쪼갰는데 답이 같아 합쳐졌다** |
| 8 | ★★★ `IsTrue<boolean>` | **`"거짓" \| "참"`** — 갈리는 조건이라 둘이 남았다 |
| 9 | `IsTrueOff<boolean>` | `"거짓"` — 감쌌다 |
| 11 | ★★ `Naked<any>` | **`"문자" \| "아님"`** — 양쪽 가지가 다 나온다 |
| 12 | ★★ `Wrapped<any>` | `"문자"` — 감싸면 **참 쪽** |
| 13 | `Naked<unknown>` | `"아님"` — ★ `any` 와 갈린다 |
| 14 | ★★★ `IsTrue<never>` | **진단 없음** — 답이 `never` 라 탐침이 침묵한다 |
| 17 | `Box<boolean>` | `{ v: false; } \| { v: true; }` |

- 진단이 **일곱 건**이고, 소스의 탐침은 **여덟 개**다. **하나가 침묵했다**(14행).
- ★★★ **7행과 8행을 갈라 읽는 것이 이 문항의 값이다.**\
  `boolean` 은 속이 `true | false` 라 **둘 다 쪼개진다.**\
  7행은 `true` 도 `false` 도 `"아님"` 이라 **결과 유니온이 하나로 합쳐진** 것이고,\
  8행은 갈리는 조건이라 **둘이 그대로 남은** 것이다.\
  ★★ 「**답이 하나면 분배가 안 됐다**」는 틀린 추론이다 — 7행이 그 반례다.
- ★★ **11행** — `any` 는 「무엇이든」이므로 `string` 일 수도, 아닐 수도 있다.\
  네이키드 자리에서는 **두 가능성을 모두 답**으로 내놓는다.
- ★★ **12행** — 감싸면 `[any] extends [string]` 이 **참**이 되어 하나로 좁혀진다.\
  ★ 여기서도 네이키드는 **벌리고** 감싼 쪽은 **좁힌다.**
- ★ **13행** — `unknown` 은 유니온도 아니고 `string` 도 아니다. **거짓 가지 하나**다.\
  ★★ **`any` 와 `unknown` 이 조건부에서 갈리는 자리**가 여기다.
- ★★★ **14행에 진단이 없는 것이 답이다.** `IsTrue<never>` 는 `never` 이고,\
  `never` 는 `null` 에도 할당되므로 **탐침이 아무 말도 안 한다**(10번).
- ★ **17행** — 분배의 결과가 문자열일 필요는 없다. **객체 두 개의 유니온**도 같은 기제다.

```text
  ★★ 쪼갰는데 합쳐진 것 / 안 쪼갠 것 — 결과만 보면 구분이 안 된다

  Naked<boolean>   ->  true, false 로 쪼갬  ->  "아님", "아님"  ->  "아님"      (7행)
  IsTrue<boolean>  ->  true, false 로 쪼갬  ->  "참", "거짓"    ->  "거짓"|"참" (8행)
  IsTrueOff<bool>  ->  안 쪼갬              ->  한 번 판정      ->  "거짓"      (9행)

  ★ 7행과 9행은 "답이 하나"라는 점이 같다. 8행처럼 갈리는 조건으로 다시 던져야 가른다.
```

### 4. ★★★ 손으로 쓴 것과 내장이 **글자까지 같고**, 분배를 끄면 **무너진다**

**출력**

```ts
// ex.24d.ts
// Exclude · Extract · NonNullable 을 직접 다시 만들어 본다
type MyExclude<T, U> = T extends U ? never : T;
type MyExtract<T, U> = T extends U ? T : never;
type MyNonNullable<T> = T extends null | undefined ? never : T;

type Color = "빨강" | "노랑" | "파랑";

const mineExclude: null = null as unknown as MyExclude<Color, "노랑">;
const stockExclude: null = null as unknown as Exclude<Color, "노랑">;
const mineExtract: null = null as unknown as MyExtract<Color | 1 | 2, string>;
const stockExtract: null = null as unknown as Extract<Color | 1 | 2, string>;
const mineNonNull: null = null as unknown as MyNonNullable<string | null | undefined>;
const stockNonNull: null = null as unknown as NonNullable<string | null | undefined>;

type NoDistr<T, U> = [T] extends [U] ? never : T;
const brokenExclude: null = null as unknown as NoDistr<Color, "노랑">;

type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";
const allGone: null = null as unknown as IsNever<MyExclude<Color, Color>>;
console.log(mineExclude, stockExclude, mineExtract, stockExtract, mineNonNull, stockNonNull, brokenExclude, allGone);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.24d.ts (tsc exit=1) =====
ex.24d.ts(8,7): error TS2322: Type '"빨강" | "파랑"' is not assignable to type 'null'.
  Type '"빨강"' is not assignable to type 'null'.
ex.24d.ts(9,7): error TS2322: Type '"빨강" | "파랑"' is not assignable to type 'null'.
  Type '"빨강"' is not assignable to type 'null'.
ex.24d.ts(10,7): error TS2322: Type 'Color' is not assignable to type 'null'.
  Type '"노랑"' is not assignable to type 'null'.
ex.24d.ts(11,7): error TS2322: Type 'Color' is not assignable to type 'null'.
  Type '"노랑"' is not assignable to type 'null'.
ex.24d.ts(12,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.24d.ts(13,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.24d.ts(16,7): error TS2322: Type 'Color' is not assignable to type 'null'.
  Type '"노랑"' is not assignable to type 'null'.
ex.24d.ts(19,7): error TS2322: Type '"never 다"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 8·9 | ★★★ `MyExclude` · `Exclude` | **둘 다 `"빨강" \| "파랑"`** |
| 10·11 | `MyExtract` · `Extract` | 둘 다 `Color` — ★ 별칭 이름으로 찍혔다 |
| 12·13 | `MyNonNullable` · `NonNullable` | 둘 다 `string` |
| 16 | ★★★ `NoDistr<Color, "노랑">` | **`Color`** — 아무것도 안 걸러졌다 |
| 19 | `IsNever<MyExclude<Color, Color>>` | `"never 다"` |

- 진단이 **여덟 건**이다.
- ★★★ **세 쌍이 전부 같은 답**이다. 표준 유틸리티는 **한 줄짜리 조건부**이고,\
  이 파일의 2\~4행이 그 전부다. **마법이 아니다.**
- ★★ **10·11행의 답이 `Color`** 로 찍혔다. 남은 원소가 마침 `Color` 와 같아서\
  tsc 가 **별칭 이름으로** 보여 준 것이다 — 들여쓴 연쇄 설명 줄이 `"노랑"` 을 집어 **유니온임을 드러낸다.**\
  ★ [**22번 주제**](../22-keyof-and-indexed-access-types/)에서 `keyof` 가 이름으로 찍히는 것과 **같은 집안**이다.
- ★★★ **16행이 이 문항의 결론이다.** `[Color] extends ["노랑"]` 은 **거짓**이므로 `T` **전체**가 나온다.\
  걸러진 것이 **하나도 없다** — **`Exclude` 는 분배 위에 서 있다.**\
  ★★ 분배를 끄면 성능도 안전도 아니라 **기능 자체가 없어진다.**
- ★ **19행** — 전부 빼면 `never` 다. 여기서도 **탐침이 침묵하므로** `IsNever` 로 바꿔 물었다(10번).

```text
  ★★★ 켜짐 / 꺼짐 — 같은 인자, 같은 목적, 다른 결과

  MyExclude<Color, "노랑">              NoDistr<Color, "노랑">
  T extends U ? never : T               [T] extends [U] ? never : T
        │                                       │
   "빨강" -> 아니오 -> "빨강"            [빨강|노랑|파랑] extends [노랑]?
   "노랑" -> 예     -> never                    -> 거짓
   "파랑" -> 아니오 -> "파랑"                    │
        │                                       v
        v                                   Color  (통째로)
   "빨강" | "파랑"  (8행)                   (16행)
```

### 5. ★★★ 제네릭 안에서는 **`IsStr<T>` 그대로** 남고, **값도 못 넣는다**

**출력**

```ts
// ex.24e.ts
// 조건부가 지연된다 -- 제네릭 안에서는 아직 안 풀린다
type IsStr<T> = T extends string ? "문자" : "아님";

function inside<T>(x: T): IsStr<T> {
    const stillOpen: null = null as unknown as IsStr<T>;
    const cannotFill: IsStr<T> = "문자";
    console.log(stillOpen, cannotFill);
    return x as IsStr<T>;
}
const outsideStr: null = inside("가");
const outsideNum: null = inside(1);

type Deep<T> = IsStr<T> extends "문자" ? "안쪽도 문자" : "아님";
const deepKnown: null = null as unknown as Deep<string>;
function nested<T>(): Deep<T> {
    const stillOpen: null = null as unknown as Deep<T>;
    console.log(stillOpen);
    return null as unknown as Deep<T>;
}
console.log(outsideStr, outsideNum, deepKnown, nested);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.24e.ts (tsc exit=1) =====
ex.24e.ts(5,11): error TS2322: Type 'IsStr<T>' is not assignable to type 'null'.
  Type '"문자" | "아님"' is not assignable to type 'null'.
    Type '"문자"' is not assignable to type 'null'.
ex.24e.ts(6,11): error TS2322: Type '"문자"' is not assignable to type 'IsStr<T>'.
ex.24e.ts(10,7): error TS2322: Type '"문자"' is not assignable to type 'null'.
ex.24e.ts(11,7): error TS2322: Type '"아님"' is not assignable to type 'null'.
ex.24e.ts(14,7): error TS2322: Type '"안쪽도 문자"' is not assignable to type 'null'.
ex.24e.ts(16,11): error TS2322: Type 'Deep<T>' is not assignable to type 'null'.
  Type '"아님" | "안쪽도 문자"' is not assignable to type 'null'.
    Type '"아님"' is not assignable to type 'null'.
```

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 5 | ★★★ 제네릭 안의 `IsStr<T>` | **`IsStr<T>`** — 안 풀렸다. 들여쓴 줄이 `"문자" \| "아님"` 을 알려 준다 |
| 6 | ★★★ `const cannotFill: IsStr<T> = "문자";` | **`TS2322`** — 지연된 조건부에는 **값을 못 넣는다** |
| 10 | `inside("가")` | `"문자"` |
| 11 | `inside(1)` | `"아님"` |
| 14 | `Deep<string>` | `"안쪽도 문자"` — 끝까지 풀린다 |
| 16 | 제네릭 안의 `Deep<T>` | `Deep<T>` — 들여쓴 줄에 `"아님" \| "안쪽도 문자"` |

- 진단이 **여섯 건**이다.
- ★★★ **5행** — `T` 가 아직 안 채워졌으니 **조건을 판정할 수 없다.**\
  tsc 는 억지로 고르지 않고 **`IsStr<T>` 라는 미해결 상태 그대로** 들고 있는다.\
  ★ 그 아래 **들여쓴 줄**이 「어느 쪽이든 `"문자" | "아님"` 안이다」를 알려 준다. **두 줄을 같이 읽어라.**
- ★★★ **6행이 그 대가다.** 어느 가지인지 모르므로 **어느 쪽 값도** 넣을 수 없다.\
  ★ 컴파일러는 「아직 모른다」를 「아무거나 된다」로 읽지 않는다.\
  그래서 9행처럼 **구현 안에서는 `as` 로 넘기고 계약은 시그니처가 지킨다.**
- ★★ **10·11행** — **호출 자리에서 `T` 가 채워지는 순간** 조건이 풀려 `"문자"`/`"아님"` 으로 갈린다.\
  **달라진 것은 오직 `T` 를 알게 됐다는 것 하나**다.
- ★ **14행과 16행을 견줘라.** 같은 `Deep` 별칭인데 인자를 알면 끝까지 풀리고(14행),\
  제네릭 안에서는 **`Deep<T>`** 로 남는다(16행). **조건부 안의 조건부여도 지연은 바깥까지 번진다.**

### 6. ★ Java 는 **4행 한 줄에서 파서가 죽고**, 9행의 `&` 는 **통과한다**

**출력**

```java
// Union.java
import java.util.List;

public class Union {
    static List<String | Integer> mixed() {
        return null;
    }

    static <T extends CharSequence & Comparable<T>> T bothBounds(T x) {
        return x;
    }
}
```

```text
===== javac -d jout Union.java (javac exit=1) =====
Union.java:4: error: > or ',' expected
    static List<String | Integer> mixed() {
                       ^
Union.java:4: error: <identifier> expected
    static List<String | Integer> mixed() {
                                ^
Union.java:4: error: invalid method declaration; return type required
    static List<String | Integer> mixed() {
                                  ^
3 errors
```

**왜 그런가**

- ★★★ 진단 **셋이 전부 4행**에서 났고 마지막 줄이 `3 errors` 다.\
  첫 진단이 「`>` 나 `,` 가 와야 한다」 — **파서 단계**다. **의미 검사까지 가지도 못한다.**\
  ★ 「미지원」이 아니라 **문법이 아예 없다.**
- ★★ **9행에는 진단이 없다.** `<T extends CharSequence & Comparable<T>>` 는 통과한다 —\
  Java 에 **`&` 는 있는데 `|` 가 없다.** 교차는 적을 수 있고 합집합은 못 적는다.
- ★★★ **분배할 유니온이 없으니 「분배」라는 개념 자체가 없다.**\
  Java 가 「여럿 중 하나」를 적는 법은 **봉인 계층**이다 —\
  `` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **15번**([`sealed` (17+) — `permits`·허용 계층의 조건](../../../java/syntax/15-sealed-classes/)) ``.\
  ★ 그러나 그것은 **이름 붙은 타입들의 계층**이지 **아무 타입이나 묶은 유니온**이 아니다.
- ★★ 앞 배치의 실측을 **다시 재지 않고 인용한다** — TypeScript 와 Rust·Java 의 진짜 축은\
  「정의 자리냐 사용 자리냐」가 아니라 **모양이냐 이름이냐**다.\
  TS 의 조건부는 **모양**을 묻고, Java 는 **이름**을 묻는다. 4행의 파서 에러가 그 축의 **가장 짧은 증거**다.

### 7. ★★★ 네이키드 = 「타입 매개변수가 `extends` 왼쪽에 **그 자체로** 서 있다」

**왜 그런가**

- 한 문장 — 「`extends` 왼쪽이 타입 매개변수 **그 자체**일 때만 분배한다.」
- ★ 그러므로 조건은 「**감쌌느냐**」가 아니라 「**네이키드냐**」다. 이 문서는 **꺼지는 두 꼴**을 던져 봤다.

| 왼쪽 모양 | 네이키드인가 | 분배 | 근거 |
|---|---|---|---|
| `T` | ★ 그렇다 | 한다 | 1번 5행 |
| `[T]` | 아니다 — **튜플 타입**이다 | 안 한다 | 1번 6행 |
| `T[number]` | 아니다 — **인덱스 접근으로 계산된 타입**이다 | 안 한다 | 1번 16행 |

- ★★★ 1번 16행이 핵심 반례다. `T[number]` 는 **감싸지 않았는데도** 분배가 안 된다.\
  「대괄호가 없으면 분배된다」로 외우면 **여기서 틀린다.**
- ★★ 실무 처방 — **왼쪽만 보라.** `T` 가 혼자면 분배, 무엇과든 엮여 있으면 아니다.
- ★ 이 문서는 `[T]` 와 `T[number]` **두 꼴만** 던졌다. 다른 감싸는 꼴은 **안 던졌다.**

### 8. ★★★ `T extends never` 는 **참이 나오는 입력이 없다**

**왜 그런가**

- ★★★ 두 줄을 같이 읽어야 한다 — 2번 **13행과 14행**이다.

| 입력 | 무슨 일이 일어나나 | 답 |
|---|---|---|
| `never` | 네이키드 자리라 **분배가 0번 돈다** — 조건식이 **실행되지 않는다** | 결과가 `never` (13행) |
| `never` 가 아닌 것 | 조건이 **거짓** | 거짓 가지 (14행) |

- ★★★ **참 가지에 도달하는 길이 없다.** `never` 를 넣으면 조건을 **보지도 못하고** 끝나고,\
  `never` 가 아닌 것을 넣으면 **거짓**이다.
- ★★ 그래서 관용구는 반드시 **`[T] extends [never]`** 다. 감싸면 분배가 안 돌아\
  **조건식이 실제로 실행되고**, `[never] extends [never]` 가 **참**이 된다.
- ★ 이것이 2번 7행(`Wrapped<never>` 가 `"문자"`)과 **같은 성질의 다른 얼굴**이다 —\
  감싸면 `never` 의 **할당 가능성**이 그대로 판정에 쓰인다.

```text
  ★★ 두 길이 다 막혀 있다

  BadIsNever<never>    T extends never ?     분배 0번 -> 조건 미실행 -> never
  BadIsNever<string>   string extends never ?  거짓   -> "never 가 아니다"
                                                        ★ 참이 없다

  IsNever<never>       [never] extends [never] ?  참   -> "never 다"
                                                        ★ 감싸야 조건이 돈다
```

### 9. ★★ 대가는 **기능이 사라지는 것** — 그리고 `never` 에서 **판정이 뒤집히는 것**

**왜 그런가**

- ★★★ **첫째 대가 — 걸러지지 않는다.** 4번 16행이 그 증거다.\
  `NoDistr<Color, "노랑">` 은 **`Color` 를 통째로** 돌려준다.\
  「원소마다 빼기」가 목적인 연산에서 분배를 끄면 **연산 자체가 없어진다.**
- ★★★ **둘째 대가 — `never` 에서 답이 뒤집힌다.** 2번 7행이 그 증거다.\
  네이키드 쪽은 `never` 에서 **사라지는데**, 감싼 쪽은 **참으로 통과한다**(`"문자"`).\
  ★★ 「안전하게 감싸 뒀다」고 생각한 자리가 **`never` 입력에서 조용히 참이 된다.**
- ★★ 그러므로 **감싸는 것은 기본값이 아니다.** 감싸는 자리는 둘뿐이다 —\
  ① 유니온 **전체**를 한 덩어리로 판정해야 할 때 ② **`never` 인지 물을 때**(`IsNever`).
- ★ 셋째로, 1번 12·13행처럼 **결과의 모양**도 달라진다(`string[] | number[]` 대 `(string | number)[]`).\
  ★ 두 타입에 **섞인 배열을 실제로 대입해 보지는 않았다**(아래 「안 돌려 본 것」).

### 10. ★★★ 답이 `never` 면 탐침이 침묵한다 — `IsNever` 로 바꿔 묻는다

**왜 그런가**

- ★★★ **왜 침묵하나** — 탐침은 `const p: null = … as X` 가 **틀리기를** 기대하고 `X` 를 읽는 장치다.\
  그런데 `never` 는 **모든 타입에 할당 가능**하므로 `null` 에도 들어간다. **틀리지 않는다.**\
  그래서 **진단이 아예 안 난다** — 3번 14행이 그 자리다.
- ★★★ **무엇이 나쁜가** — 「답이 `never`」와 「그 줄에 아무 일도 없었다」가 **구분되지 않는다.**\
  **목록의 공백**을 답으로 읽으려면 **몇 개를 물었고 몇 개가 답했는지**를 알아야 한다 —\
  3번은 탐침 **여덟 개** 중 **일곱 개**가 답했고 **하나가 침묵했다.**
- ★★ **바꿔 묻는 법** — `type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다"`.\
  이 배치에서 2번 6·10·13행, 4번 19행이 전부 그렇게 물은 것이다.
- ★★★ **바꾼 창이 못 보는 것** — `IsNever` 는 「`never` 인가」에 **예/아니오만** 답한다.\
  **무엇인지는 여전히 안 말한다.** `never` 가 아니라는 답을 받으면 **다시 탐침으로** 돌아가야 한다.
- ★ 같은 일이 [**22번 주제**](../22-keyof-and-indexed-access-types/)에서는 **다른 모양**으로 일어난다 —\
  거기서는 탐침이 침묵하는 게 아니라 **답을 잘라서** 준다. **창을 바꾸는 이유가 주제마다 다르다.**

### 11. ★★ 22 가 **재료**를, 24 가 **가르는 법**을, 25 가 **이름과 되풀이**를 준다

**왜 그런가**

| 주제 | 이 사슬에서 맡은 것 | 이 주제와 만나는 자리 |
|---|---|---|
| [**22번**](../22-keyof-and-indexed-access-types/) | 타입에서 **키와 값을 꺼낸다**(`keyof T`·`T[K]`) | 꺼낸 유니온이 **여기서 분배된다**. 1번 16행의 `T[number]` 가 그쪽 문법이다 |
| **24 (여기)** | 꺼낸 것을 **조건으로 가른다** | `Exclude`·`Extract` 가 4번 |
| [**25번**](../25-infer-and-recursive-conditional-types/) | 가르면서 **이름을 붙이고**(`infer`) **되풀이한다** | ★★★ **급소.** 같은 조건부 문법에 두 가지가 더 붙는다 |

- ★★★ **세 주제가 같은 문법 위에 쌓인다** — `T extends U ? X : Y` 한 줄이 셋을 관통한다.\
  22 는 `U` 자리에 넣을 **재료**를 주고, 24 는 그 **가르는 규칙**을 주고, 25 는 `X` 자리에서 **뽑아 쓰는 법**을 준다.
- ★★★ **[23번 주제](../23-typeof-type-operator/)가 왜 사슬에 없나** — 축이 다르다.\
  22·24·25 는 전부 **타입을 계산하는** 이야기인데,\
  23 은 「**값 공간 / 타입 공간**」이라는 **다른 축**이다 — 「어느 세계에 사는 이름인가」를 묻는다.\
  ★ 그래서 23 만 **3창(방출된 `.js`)이 본체**이고, 이 셋은 **`.js` 가 부적용**이다.
- ★ 실무 순서도 그 사슬대로다 — 키를 꺼내고(`keyof`), 거르고(`Exclude`), 뽑는다(`infer`).

### 12. ★★ 세 층

**왜 그런가**

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장(2.8)** | 네이키드에서 분배 · 감싸면 꺼짐 · `never` 는 원소 0개의 유니온 · `boolean` 의 속은 `true \| false` · `Exclude`·`Extract`·`NonNullable` 의 정의 · 제네릭 안에서의 지연 |
| **★ 이 판(7.0.2)의 관찰** | ★★★ `T[number]` 가 **네이키드가 아닌 것**(1번 16행) · `any` 가 **양쪽 가지를 다 내는 것**(3번 11행) · 답이 같으면 **합쳐져 분배가 안 보이는 것**(3번 7행) · 유니온을 **별칭 이름으로** 찍는 것(4번 10행) · 유니온 원소의 **표시 순서** · 진단 **문구**와 **연쇄 설명 줄** |
| **★ 부적용 — 3창(방출된 `.js`)** | **잴 것이 없다** — 조건부는 전부 타입 층이다. 이 문서에 `.js` 블록이 **하나도 없다** |
| **★ 부적용 — 5창(`.d.ts`)** | **잴 것이 없다** — 조건부를 **적은 그대로** 남긴다(아래 블록) |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 한 글자도 같다**(아래 블록) |
| **★★★ 안 잰 것** | **검사 시간·메모리** — **재지 않았다.** [목록의 **45번 주제**](../45-type-level-performance/)가 정본이다 |

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.24a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.24b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.24c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.24d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.24e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★★ **다섯 파일이 전부 같다.** 조건부 타입은 `strict` **아래의 기능이 아니라 타입 계산 자체**다.\
  ★ [**21번 주제**](../21-inference-control-const-and-noinfer/)에서는 여섯 중 **하나가 갈렸다** — **그쪽과 다른 자리**다.

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

- ★★★ `export type Cond = string extends string ? "가" : "나";` 를 보라. **조건이 뻔한데도 안 푼다.**\
  `keyof User` 도, `(typeof frozen)[number]` 도 **적은 그대로**다.\
  **`.d.ts` 는 계산하지 않는다** — 그래서 조건부의 답을 읽는 창으로 **쓸 수 없다.**\
  ★ 「재 봤더니 같았다」가 아니라 **잴 것이 없다.**

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.22a.ts    5회 md5 가짓수 1
ex.24a.ts    5회 md5 가짓수 1
ex.25b.ts    5회 md5 가짓수 1
```

- ★★ 유니온 원소의 **표시 순서**를 5회 돌려 md5 를 견줬다 — **가짓수 1**.\
  ★★★ 그래도 **관찰이지 보장이 아니다.** 근거로 쓸 때는 **원소 목록**까지만 쓰고 **순서에 기대지 마라.**

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `javac -version` · `rustc --version` | `Version 7.0.2` · `v18.19.1` · `javac 21.0.5` · `rustc 1.92.0` |
| ★★★ 분배 켜기/끄기 | `--noEmit ex.24a.ts` | exit 1 · **7건** · 5행 **`"문자" \| "아님"`** 대 6행 **`"아님"`** |
| ★★★ `never` | `--noEmit ex.24b.ts` | exit 1 · **6건** · 6행 **`"never 다"`** 대 7행 **`"문자"`** |
| `boolean`·`any` | `--noEmit ex.24c.ts` | exit 1 · **7건** · ★ 탐침 **8개 중 1개 침묵**(14행) |
| 유틸리티 재구현 | `--noEmit ex.24d.ts` | exit 1 · **8건** · 8·9행 **같음** · ★ 16행 `Color` **통째로** |
| 조건부 지연 | `--noEmit ex.24e.ts` | exit 1 · **6건** · 5행 `IsStr<T>` · 6행 `TS2322` |
| 교차 갈래(Java) | `javac -d jout Union.java` | exit 1 · **3 errors** · 전부 **4행**(파서) · ★ 9행은 **통과** |
| ★ 5창 부적용 | `--declaration --emitDeclarationOnly ex.22f.ts` | **exit 0 · 진단 0줄** · 조건부를 **안 푼다** |
| `strict` 대조 | 다섯 파일을 `--strict false` 로 재실행 | ★★★ **다섯 전부 한 글자도 같다**(21 과 다르다) |
| 반복 실행 | 같은 명령 **5회** · md5 가짓수 | ★★ **가짓수 1** — 유니온 순서가 안 흔들렸다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ `T[number]` 가 **네이키드가 아닌 것**(1번 16행) — **던져서** 얻은 관찰이다.
- ★★★ `any` 가 **양쪽 가지를 다 내는 것**과 감싸면 **참 쪽**인 것(3번 11·12행).
- ★★ 유니온을 **별칭 이름으로** 찍는 것(4번 10·11행의 `Color`) — **표시 방식**이지 타입이 아니다.
- ★★ 유니온 원소의 **표시 순서**(`"빨강" | "파랑"`·`"거짓" | "참"`) — 5회 동일했지만 **관찰이지 보장이 아니다.**
- ★★ **연쇄 설명 줄이 붙는 조건**(유니온일 때만) — 진단 형식이다.
- ★ 진단 **문구** 전문 — 코드(`TS2322`)가 더 오래 간다.
- ★ `javac` 의 파서 진단 문구와 `3 errors` 집계 줄 — 판본에 매인다.

**안 돌려 본 것**

- ★★★ **조건부의 검사 시간·메모리** — **재지 않았고 수치를 한 개도 적지 않았다.** [목록의 **45번 주제**](../45-type-level-performance/).
- **섞인 배열을 `string[] \| number[]` 와 `(string \| number)[]` 에 각각 대입해 보는 것** — **안 던졌다.**\
  1번 12·13행의 두 타입이 **다르다**는 것까지만 실측이고, 그 차이가 대입에서 어떻게 드러나는지는 안 봤다.
- **`[T]` 말고 다른 꼴로 감싸 보는 것**(객체·함수로 감싸기) — **안 던졌다.** `[T]` 와 `T[number]` 두 꼴만 봤다.
- **`infer` 를 붙인 조건부** — **안 던졌다.** [**25번 주제**](../25-infer-and-recursive-conditional-types/).
- **매핑 타입과 함께 쓰는 것** — **안 던졌다.** [목록의 **26번 주제**](../26-mapped-types/).
- **Java 의 `sealed` 로 같은 것을 적어 보는 것** — **안 던졌다.** `` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **15번**([`sealed` (17+) — `permits`·허용 계층의 조건](../../../java/syntax/15-sealed-classes/)) ``.
- **Rust 로 같은 질문을 던지는 것** — **안 던졌다.** 앞 배치의 「모양이냐 이름이냐」를 **인용만** 했다.
