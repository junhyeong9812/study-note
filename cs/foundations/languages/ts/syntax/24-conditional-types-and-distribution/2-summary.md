# ts/syntax/24 — 조건부 타입과 분배 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html) ·
> [Handbook — Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html).
> 위 링크는 **규칙 확인용**이고, 본문의 진단 전문은 **전부 이 판에서 직접 던져서 받은 것**이다.
> 핸드북 문장을 옮기거나 번역한 자리는 **한 군데도 없다.**
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version · javac -version · rustc --version (sh exit=0) =====
Version 7.0.2
v18.19.1
javac 21.0.5
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 2창(`null` 탐침)이고, 그중에서도 「대조쌍」이다.**
> **같은 조건부를 네이키드로 한 번, `[T]` 로 감싸서 한 번** 던져 **두 줄을 나란히 놓는 것**이 이 주제의 전부다.
> 1절의 5행/6행, 12행/13행이 그 쌍이고, 이 문서는 그 짝을 **끝까지 붙여서** 보여 준다.
>
> ★★ **2창이 무엇인가** — 조건부 타입의 결과는 눈에 안 보인다. 그래서 **일부러 틀린 주석**을 달아
> 컴파일러가 답을 뱉게 한다.

```text
  const probe: null = 무엇인가;
                      └─ 이 자리의 타입이 X 라면

  error TS####: Type 'X' is not assignable to type 'null'.   <- 실제 코드는 TS2322
                      ↑ 여기서 X 를 읽는다
```

> ★★ 이 문서의 `TS2322 … is not assignable to type 'null'` 은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
> ★★★ **2창에는 눈 먼 구석이 하나 있다** — `never` 를 못 말한다. 3절에서 창을 바꾼다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> **버전** — 조건부 타입과 `Exclude`·`Extract`·`NonNullable` 은 **TS 2.8** 이다(릴리스 이력 기준).
> **7.0.2 에서 그 규칙대로 도는가는 외우지 않고 던져서 확인했다** — 아래가 그 결과다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | 유니온 원소의 **표시 순서** | 8절 — 5회 md5 **가짓수 1**. ★ **관찰이지 보장이 아니다** |
| **안 흔들린다** | 들여쓴 **연쇄 설명 줄** | 유니온일 때만 딸려 나온다 — 그 자체가 단서다(1절) |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 한 글자도 같다** | 8절. ★ [**21번 주제**](../21-inference-control-const-and-noinfer/)와 다르다 |
| **★ 부적용 — 5창(`.d.ts`)** | **잴 것이 없다** — 조건부를 **적은 그대로** 남긴다 | 8절 |
| **★ 부적용 — 3창(방출된 `.js`)** | **잴 것이 없다** — 조건부는 **전부 타입 층**이다 | 0절 |
| **부적용 — 여러 번 돌려 보기** | 같은 입력에 tsc 는 결정적이다 | 그래도 8절에서 **5회** 확인했다 |
| **안 잰 것** | 검사 **시간**·메모리 | ★★★ **재지 않았다.** 조건부의 비용은 목록의 **45번 주제**가 정본이다 |

## 한눈에 — 쉽게 말하면

**조건부 타입은 세관 검사다. 문제는 「무엇을 검사대에 올리느냐」다 — 소포를 통째로 올리느냐, 안의 물건을 하나씩 꺼내 올리느냐.**

소포 하나에 물건이 여럿 들었다고 하자.\
세관원이 **소포째** 저울에 올리면 판정이 **하나** 나온다.\
물건을 **하나씩 꺼내** 올리면 판정이 **물건 수만큼** 나오고, 그 판정들을 다시 한 상자에 담아 돌려준다.

**타입에서도 똑같은 구조다.** 유니온이 소포이고, 조건부 타입이 세관이다.\
`T` 를 **혼자** 왼쪽에 두면 컴파일러가 소포를 풀어 원소마다 검사한다 — 이것이 **분배**다.\
`[T]` 처럼 **무엇으로든 감싸면** 소포째 검사한다 — 분배가 꺼진다.

| 비유 | 실체 |
|---|---|
| 소포 | 유니온 타입 |
| 소포 안의 물건 하나 | 유니온의 원소 |
| 소포를 풀어 하나씩 검사 | **네이키드** `T extends U ? X : Y` — 분배 |
| 소포째 저울에 올림 | `[T] extends [U] ? X : Y` — 분배 끄기 |
| 판정들을 도로 한 상자에 담기 | 결과가 다시 **유니온으로 합쳐지는** 것 |
| ★★★ **빈 소포** | `never` — 원소가 **0개**인 유니온 |
| 열어 보니 물건이 **둘**이던 소포 | `boolean` — 속은 `true \| false` 다 |
| 소포가 아니라 **컨테이너에 실린 것** | `T[number]` — 네이키드가 아니다 |

```text
  ★★★ 한 그림 — 같은 조건부, 인자도 같다. 왼쪽 모양만 다르다

  Naked<T>   = T extends string ? "문자" : "아님"        <- T 가 혼자 있다
  Wrapped<T> = [T] extends [string] ? "문자" : "아님"    <- T 가 대괄호에 들었다

       둘 다에 string | number 를 넣으면

  Naked   ->  "문자" | "아님"      원소마다 따로 판정했다
  Wrapped ->  "아님"              소포째 한 번 판정했다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **같은 조건부인데 왜 답이 둘인가** — 네이키드와 `[T]` 를 나란히 던진다(1·2절).
2. **`never` 를 넣으면 왜 답이 사라지나** — ★★★ 이 주제에서 **가장 헷갈리는 자리**다(3절).
3. **표준 유틸리티는 무엇 위에 서 있나** — `Exclude` 를 손으로 다시 만들고, 분배를 꺼 **무너뜨려 본다**(5절).

★★★ **22 → 24 → 25 는 한 사슬이고 25 가 급소다.**\
[**22번 주제**](../22-keyof-and-indexed-access-types/)가 **타입에서 키를 꺼내는 법**을 주고,\
여기가 **꺼낸 것을 조건으로 가르는 법**을 주고,\
[**25번 주제**](../25-infer-and-recursive-conditional-types/)가 **가르면서 이름을 붙이고 되풀이하는 법**을 준다.\
★ [**23번 주제**](../23-typeof-type-operator/)는 **다른 축**이다 — 그쪽은 「값 공간 / 타입 공간」을 다룬다.

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **2창 — `null` 탐침** | 컴파일러가 **계산한** 조건부의 결과 | **계산된 것** | **본체.** 그중에서도 **대조쌍** |
| ★★ **2창의 변형 — `IsNever<T>`** | 「그게 `never` 인가」 | 계산된 것 | ★ **제5의 상태**(3절) |
| **1창 — 멤버십 대입** | 그 값이 그 타입에 드느냐 | 에러가 나느냐 | 이 주제에서는 **안 썼다** |
| ★ **부적용 — 3창(방출된 `.js`)** | — | **잴 것이 없다** | 조건부는 **전부 타입 층**이다 |
| ★ **부적용 — 5창(`.d.ts`)** | — | **적은 것**(계산 안 함) | 8절이 근거다 |
| **부적용 — 4창(종료 코드 격자)** | — | — | 한계를 치는 것은 [**25번 주제**](../25-infer-and-recursive-conditional-types/)의 몫 |

★★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**\
**2창은 `never` 를 못 말한다.** `const p: null = null as unknown as never` 는 **진단이 아예 안 난다** —\
`never` 는 모든 타입에 할당되기 때문이다. 「답이 `never`」와 「그 줄에 아무 일도 없었다」가 **구분되지 않는다.**\
그래서 3절부터 `type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다"` 로 **바꿔 물었다.**\
★ 바꾼 창이 못 보는 것 — `IsNever` 는 「`never` 인가」만 답하지 **무엇인지는** 안 말한다.

비용 — 컴파일 여덟 번(TypeScript 다섯 · Java 한 번 · 설정 대조 한 번 · 반복 실행 한 번).

### (1) ★★★ 분배 켜기와 끄기 — 두 줄을 나란히

**언제 쓰나** — 「조건부에 유니온을 넣었더니 예상과 다른 것이 나온다」일 때. 이 절이 그 전부다.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **5행과 6행을 나란히 읽어라.** 조건부의 몸통도 같고 인자도 `string | number` 로 같다.\
  네이키드 쪽은 **`"문자" | "아님"`**, 감싼 쪽은 **`"아님"`** 이다.\
  차이는 왼쪽이 `T` 냐 `[T]` 냐 **하나뿐**이다.
- ★★ 5행에만 **들여쓴 연쇄 설명 줄**이 딸려 있다(`Type '"문자"' is not assignable …`).\
  **유니온일 때만 나오는 줄**이라, 그 줄이 있다는 것 자체가 「답이 여럿」이라는 단서다.
- ★★★ **12행과 13행이 실무에서 더 아픈 쌍이다.** `ToArr<string | number>` 는 **`string[] | number[]`**,\
  `ToArrOff<…>` 는 **`(string | number)[]`** 다.\
  앞엣것은 「**문자열 배열이거나 숫자 배열이거나**」이고 뒤엣것은 「**원소마다 문자열이거나 숫자**」다.\
  ★ **섞인 배열이 통과하느냐가 갈린다** — 유틸리티 타입을 쓰다 「왜 이 배열이 안 들어가지」를 만나면 대개 여기다.
- ★ 8절이 말하듯 **유니온 원소의 표시 순서는 5회 동일**했다. **관찰이지 보장이 아니다.**

```text
  ★★★ 분배 전개 — 세로로 한 단계에 한 줄

  Naked<string | number>
        │
        │ ① 소포를 푼다 (유니온을 원소로 쪼갠다)
        v
  Naked<string>  ,  Naked<number>
        │
        │ ② 원소마다 따로 판정한다
        v
     "문자"      ,     "아님"
        │
        │ ③ 판정들을 도로 한 상자에 담는다
        v
     "문자" | "아님"                 <- 5행


  Wrapped<string | number>
        │
        │ ① 소포를 안 푼다. [T] 가 통째로 하나다
        v
  [string | number] extends [string] ?     -> 거짓
        │
        v
     "아님"                          <- 6행
```

비용 — 분배를 켜면 **결과가 유니온으로 벌어진다.** 받는 쪽이 그 유니온을 감당해야 한다(7절).

### (2) ★★ 「네이키드」가 정확히 무엇인가 — 세 자리로 못 박는다

**언제 쓰나** — 「내 조건부는 왜 분배가 안 되지」를 따질 때.

1절의 같은 블록을 다시 읽는다. 세 자리가 이미 그 안에 있다.

- ★★★ **7행과 8행** — 인자가 `string` 하나면 네이키드 쪽도 감싼 쪽도 **둘 다 `"문자"`** 다.\
  **분배는 유니온일 때만 눈에 보인다.** 원소가 하나면 쪼개나 안 쪼개나 결과가 같다.\
  ★ 그래서 **유니온으로 던져 보지 않으면 버그를 못 찾는다.**
- ★★★ **16행이 세 번째 자리다.** `NotNaked<T extends unknown[]> = T[number] extends string ? …` 에\
  `(string | number)[]` 를 줬는데 답이 **`"아님"`** 이다.\
  `T[number]` 는 `string | number` 이지만 **`T` 가 혼자 있는 것이 아니라 인덱스 접근 아래에 있다** —\
  그래서 **분배가 안 된다.** 감싸지 않았는데도 꺼진 것이다.
- ★★ 즉 「네이키드」는 「감싸지 않았다」가 아니라 **타입 매개변수가 `extends` 왼쪽에 그 자체로 서 있다**는 뜻이다.\
  `T[number]`·`T["k"]` 같은 것은 **이미 계산된 타입**이라 네이키드가 아니다.

```text
  ★★ 왼쪽에 무엇이 서 있나 — 이것만 보면 된다

  T          extends U ? X : Y      네이키드   -> 분배한다     ( 5행)
  [T]        extends [U] ? X : Y    감쌌다     -> 안 한다      ( 6행)
  T[number]  extends U ? X : Y      계산됐다   -> 안 한다      (16행)

  ★ 셋 다 이 판에서 던져서 확인한 것이다. 왼쪽 모양만 보면 갈린다.
```

비용 — 없다. 다만 **끄는 법이 둘**이라는 것을 알아야 남의 코드를 읽을 수 있다.

### (3) ★★★ `never` — 가장 헷갈리는 자리

**언제 쓰나** — 「분명히 조건을 맞췄는데 결과가 `never` 로 사라진다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **6행이 이 절의 한가운데다.** `Naked<never>` 를 `IsNever` 로 물었더니 **`"never 다"`** 가 나왔다 —\
  즉 **결과가 `never` 로 사라졌다.**\
  `never` 는 **원소가 0개인 유니온**이라, 소포를 풀었더니 **꺼낼 물건이 하나도 없었던** 것이다.\
  판정을 **한 번도 안 하고** 빈 상자를 돌려준다.
- ★★★ **7행이 정반대다.** 같은 인자에 감싼 쪽을 던지면 **`"문자"`** 가 나온다.\
  `[never] extends [string]` 은 **참**이다 — `never` 는 모든 타입에 할당되기 때문이다.\
  **두 줄이 정반대 답을 낸다.** 1절의 쌍은 「벌어지느냐 마느냐」였는데, 여기서는 **참/거짓이 뒤집힌다.**
- ★★ **10행 — 조건이 항상 참이어도 그렇다.** `Always<T> = T extends unknown ? "항상" : "절대"` 는\
  무엇을 넣어도 참인데, `never` 를 넣으면 **`"항상"` 이 아니라 `never`** 다.\
  ★ **조건을 보기 전에 이미 끝난다** — 돌 원소가 없으니 조건이 실행되지 않는다.
- ★★★ **13행이 그 함정의 실전판이다.** `BadIsNever<T> = T extends never ? …` 로 `never` 를 잡으려 하면\
  **영원히 못 잡는다.** `never` 를 넣으면 분배가 돌지 않아 **결과가 `never`** 이고(13행),\
  `never` 가 아닌 것을 넣으면 당연히 거짓이다(14행 — `"never 가 아니다"`).\
  **참이 나오는 입력이 없다.** 그래서 `IsNever` 는 **반드시 `[T] extends [never]`** 로 써야 한다.
- ★★ **16행 — `never` 는 유니온에 들어가기도 전에 사라진다.** `Naked<string | never>` 가 **`"문자"`** 다.\
  `string | never` 는 타입이 만들어지는 순간 이미 `string` 이다. **분배 이전의 일**이다.

```text
  ★★★ 빈 소포 — 쪼갤 것이 없다

  Naked<string | number>            Naked<never>
        │                                 │
        │ 원소 2개로 쪼갠다                 │ 원소 0개로 쪼갠다
        v                                 v
  Naked<string>, Naked<number>      (아무것도 없음)
        │                                 │
        │ 2번 판정                        │ 0번 판정
        v                                 v
    "문자" | "아님"                     (빈 유니온) = never

  ★ 조건이 참이든 거짓이든 상관없다 — 판정 자체를 안 한다.
```

```text
  ★★ never 를 잡는 법 — 왜 감싸야 하나

  BadIsNever<never>   T extends never ?      -> 분배가 0번 돈다 -> never   (13행)
  BadIsNever<string>  string extends never ? -> 거짓            -> "아니다" (14행)
                      ★ 참이 나오는 입력이 없다

  IsNever<never>      [never] extends [never] ? -> 참           -> "never 다"
                      ★ 감싸면 분배가 안 돌아 조건이 실제로 실행된다
```

비용 — `IsNever` 를 쓰면 **「`never` 인가」만 안다.** 무엇인지는 여전히 안 보인다.

### (4) ★★ `boolean` 과 `any` — 쪼개지는 것과 양쪽이 다 나오는 것

**언제 쓰나** — 「불리언 하나 넣었는데 답이 둘이다」·「`any` 를 넣었더니 아무 말이나 다 나온다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **8행 — `IsTrue<boolean>` 이 `"거짓" | "참"`** 이다. `boolean` 은 속이 **`true | false`** 인 유니온이라\
  네이키드 자리에서 **둘로 쪼개진다.** 9행의 감싼 쪽은 **`"거짓"`** 하나다.
- ★★★ **7행을 8행과 갈라 읽어야 한다.** `Naked<boolean>` 은 **`"아님"`** 하나뿐이다.\
  ★ 이것은 **분배가 안 된 것이 아니다** — 쪼개서 두 번 판정했는데 **`true` 도 `false` 도 `"아님"`** 이라\
  결과 유니온이 **하나로 합쳐진** 것이다.\
  ★★ **「답이 하나면 분배가 안 됐다」는 틀린 추론**이다. 2절 7·8행과 같은 함정이고, 여기서는 더 잘 숨는다.\
  **갈리는 조건으로 다시 던져야** 보인다 — 그것이 8행이다.
- ★★ **11행 — `Naked<any>` 가 `"문자" | "아님"`** 이다. **양쪽 가지가 다 나온다.**\
  `any` 는 「무엇이든 될 수 있다」이므로 참 가지도 거짓 가지도 가능한 답이다.
- ★★ **12행 — `Wrapped<any>` 는 `"문자"`** 다. 감싸면 **참 쪽으로 정해진다.**\
  ★ 여기서도 두 줄이 **정반대 성격**이다 — 네이키드는 답을 **둘로 벌리고**, 감싼 쪽은 **하나로 좁힌다.**
- ★ **13행 — `Naked<unknown>` 은 `"아님"`** 이다. `any` 와 `unknown` 이 **여기서 갈린다.**\
  `unknown` 은 유니온이 아니고 `string` 도 아니므로 **거짓 가지 하나**다.
- ★★★ **14행에는 진단이 없다.** `IsTrue<never>` 의 답이 `never` 라서 **2창이 침묵한** 것이다 —\
  3절에서 말한 **제5의 상태**가 이 블록에도 그대로 나온다. **목록의 공백이 답이다.**
- ★ **17행 — 분배는 결과가 문자열일 때만 보이는 것이 아니다.** `Box<boolean>` 이\
  **`{ v: false; } | { v: true; }`** 로 **객체 두 개의 유니온**이 됐다.

```text
  ★★ boolean 은 속이 둘이다 — 그런데 답이 같으면 하나로 합쳐진다

  Naked<boolean>                     IsTrue<boolean>
        │                                  │
        v                                  v
  true, false 로 쪼갬                 true, false 로 쪼갬
        │                                  │
        v                                  v
  "아님" , "아님"                     "참" , "거짓"
        │                                  │
        v                                  v
  "아님"        (합쳐졌다, 7행)       "거짓" | "참"   (안 합쳐졌다, 8행)

  ★ 왼쪽만 보고 "분배가 안 됐다"고 읽으면 틀린다.
```

비용 — `any` 가 섞이면 **조건부의 답이 유니온으로 벌어져** 뒤쪽 계산이 전부 두 갈래가 된다.

### (5) ★★★ `Exclude`·`Extract`·`NonNullable` — 손으로 다시 만들고, 꺼서 무너뜨린다

**언제 쓰나** — 표준 유틸리티가 무엇 위에 서 있는지 확인할 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **8행과 9행이 글자까지 같다.** 손으로 쓴 `MyExclude` 와 표준 `Exclude` 가 둘 다 **`"빨강" | "파랑"`** 이다.\
  10·11행(`Extract`)도, 12·13행(`NonNullable`)도 마찬가지다.\
  ★ **유틸리티는 마법이 아니다** — 한 줄짜리 조건부이고, 이 절의 세 줄이 그 전부다.
- ★★ **10·11행의 답이 `Color` 라고 찍혔다.** 남은 원소가 마침 `Color` 와 같아서 tsc 가 **별칭 이름으로** 보여 준 것이다.\
  들여쓴 연쇄 설명 줄이 `"노랑"` 을 집어 **유니온임을 드러낸다.**\
  ★ 이 성질은 [**22번 주제**](../22-keyof-and-indexed-access-types/)에서 `keyof` 가 이름으로 찍히는 것과 **같은 집안**이다.
- ★★★ **16행이 이 절의 결론이다.** `NoDistr<Color, "노랑">` 은 `[T] extends [U]` 로 분배를 껐더니\
  **`Color` 를 통째로** 돌려준다 — 아무것도 걸러지지 않았다.\
  `["빨강" | "노랑" | "파랑"] extends ["노랑"]` 은 거짓이므로 **`T` 전체가 그대로** 나온다.\
  ★★ 즉 **`Exclude` 는 분배 위에 서 있다.** 분배를 끄면 **기능 자체가 없어진다.**
- ★ **19행 — 전부 빼면 `never`** 다. `MyExclude<Color, Color>` 를 `IsNever` 로 물어 **`"never 다"`** 를 받았다.\
  ★ 여기서도 2창이 아니라 **`IsNever` 로 바꿔 물어야** 답이 나온다(3절).

```text
  ★★★ Exclude 는 분배 위에 서 있다 — 켜짐/꺼짐 나란히

  MyExclude<Color, "노랑">                 NoDistr<Color, "노랑">
  = T extends U ? never : T                = [T] extends [U] ? never : T
        │                                        │
        v                                        v
  "빨강" -> never? 아니오 -> "빨강"          [빨강|노랑|파랑] extends [노랑]?
  "노랑" -> never? 예     -> never                   -> 거짓
  "파랑" -> never? 아니오 -> "파랑"                   │
        │                                            v
        v                                        Color  (통째로, 16행)
  "빨강" | "파랑"   (8행)

  ★ 왼쪽은 원소마다 물었고, 오른쪽은 소포째 한 번 물었다.
```

비용 — 직접 만들 이유는 **없다.** 표준 것을 쓰고, **왜 그렇게 도는지만** 이 절로 이해한다.

### (6) ★★ 조건부가 지연된다 — 제네릭 안에서는 아직 안 풀린다

**언제 쓰나** — 「제네릭 함수 안에서 조건부 타입에 값을 못 넣겠다」일 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **5행이 핵심이다.** 제네릭 안에서 `IsStr<T>` 를 탐침에 물었더니 **`IsStr<T>` 라고 그대로** 답한다 —\
  `T` 가 아직 안 정해졌으니 **조건을 판정할 수 없다.**\
  ★ 그 아래 **들여쓴 줄**이 가능한 답 `"문자" | "아님"` 을 알려 준다. **두 줄을 같이 읽어야** 뜻이 선다.
- ★★★ **6행이 그 대가다.** `const cannotFill: IsStr<T> = "문자";` 가 **`TS2322`** 로 막힌다 —\
  「`"문자"` 를 `IsStr<T>` 에 넣을 수 없다」.\
  **아직 어느 가지인지 모르므로 어느 쪽 값도 못 넣는다.** 제네릭 안에서 조건부 반환값을 만들 때\
  `as` 가 필요해지는 이유가 이것이다(9행이 그렇게 썼다).
- ★★ **10·11행 — 바깥에서 부르면 그제야 갈린다.** `inside("가")` 는 **`"문자"`**, `inside(1)` 은 **`"아님"`** 이다.\
  **호출 자리에서 `T` 가 채워지는 순간 조건이 풀린다.**
- ★ **14행과 16행을 견줘라.** `Deep<string>` 은 **`"안쪽도 문자"`** 로 끝까지 풀리는데,\
  같은 별칭을 제네릭 안에서 물으면 **`Deep<T>`** 로 남는다(16행 — 들여쓴 줄에 `"아님" | "안쪽도 문자"`).\
  **조건부 안에 조건부가 있어도 지연은 바깥까지 번진다.**

```text
  ★★ 언제 풀리나 — 인자가 채워지는 순간

  function inside<T>(x: T): IsStr<T>
                              │
        T 가 아직 없다 ────────┤  -> IsStr<T> 그대로 (5행)
                              │     값도 못 넣는다 -> TS2322 (6행)
                              │
        inside("가")  ────────┤  -> T = "가"  -> "문자"  (10행)
        inside(1)     ────────┘  -> T = 1     -> "아님"  (11행)
```

비용 — 지연된 조건부는 **할당을 못 받는다.** 구현 안에서는 `as` 로 넘기고, **계약은 시그니처가 지킨다.**

### (7) ★ 교차 갈래 — Java 에는 분배할 유니온이 없다

**언제 쓰나** — 「다른 언어는 이걸 어떻게 하나」가 궁금할 때.

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

그림 해설 — 한 단계에 한 문장.

- ★★★ **진단 셋이 전부 4행 한 줄에서 났다.** `List<String | Integer>` 는 **파서에서 죽는다** —\
  「`>` 나 `,` 가 와야 한다」가 첫 진단이다. **의미 검사까지 가지도 못한다.**
- ★★ **같은 파일 9행에는 진단이 없다.** `<T extends CharSequence & Comparable<T>>` 는 **통과한다.**\
  ★ 즉 Java 에는 **`&` 는 있는데 `|` 가 없다.** 교차는 되고 합집합은 안 된다.
- ★★★ **분배할 유니온이 없으니 「분배」라는 개념 자체가 없다.**\
  Java 가 「여럿 중 하나」를 적는 방법은 **봉인 계층**이다 —\
  `` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **15번**([`sealed` (17+) — `permits`·허용 계층의 조건](../../../java/syntax/15-sealed-classes/)) ``.\
  ★ 그런데 그것은 **이름 붙은 타입들의 계층**이지 **아무 타입이나 묶은 유니온**이 아니다.
- ★★ 앞 배치가 이미 실측한 것을 **다시 재지 않고 인용한다** —\
  TypeScript 와 Rust 의 진짜 축은 「정의 자리냐 사용 자리냐」가 아니라 **모양이냐 이름이냐**다.\
  TS 의 조건부는 **모양**을 묻고(`T extends { length: number }`), Java·Rust 는 **이름**을 묻는다(`implements`·`impl`).\
  4행의 파서 에러가 그 축의 **가장 짧은 증거**다.

```text
  ★★ 무엇으로 "여럿 중 하나"를 적나

  TypeScript   "빨강" | "노랑" | "파랑"        아무 타입이나 묶는다  -> 분배가 성립한다
  Java         sealed interface Color          이름 붙은 계층만      -> 분배할 것이 없다
               permits Red, Yellow, Blue

  ★ Java 는 <T extends A & B> 로 교차는 적는다(9행은 통과). 합집합만 없다.
```

비용 — 없다. **대비가 목적**이고, Java 쪽 정본은 위 15번이다.

### (8) ★★ 설정·판·창 — 세 가지 대조

**언제 쓰나** — 「이 결과가 내 설정 때문인가」를 가를 때.

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.24a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.24b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.24c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.24d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.24e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

- ★★★ **다섯 파일이 전부 한 글자도 같다.** `--strict` 를 꺼도 이 주제의 결론은 **하나도 안 바뀐다.**\
  ★ 이것은 [**21번 주제**](../21-inference-control-const-and-noinfer/)와 **다르다** — 거기서는 여섯 파일 중 **하나가 갈렸다.**\
  **조건부 타입은 `strict` 아래의 기능이 아니라 타입 계산 자체**이기 때문이다.

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.22a.ts    5회 md5 가짓수 1
ex.24a.ts    5회 md5 가짓수 1
ex.25b.ts    5회 md5 가짓수 1
```

- ★★ 유니온 원소의 **표시 순서**를 5회 돌려 md5 를 견줬다. **가짓수 1** — 안 흔들렸다.\
  ★★★ 그래도 **관찰이지 보장이 아니다.** 근거로 쓸 때는 **원소 목록**까지만 쓰고 **순서에 기대지 마라.**

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

- ★★★ **5창(`.d.ts`)이 왜 부적용인가** — 이 블록의 `export type Cond = string extends string ? "가" : "나";` 를 보라.\
  **조건이 뻔한데도 풀지 않고 적은 그대로** 남겼다. `keyof User` 도, `(typeof frozen)[number]` 도 그렇다.\
  ★★ **`.d.ts` 는 계산하지 않는다.** 그러므로 조건부 타입의 답을 읽는 창으로 **쓸 수 없다.**\
  「재 봤더니 같았다」가 아니라 **잴 것이 없다.**
- ★ **3창(방출된 `.js`)도 부적용**이다. 이 문서에는 `.js` 블록이 **하나도 없다** —\
  조건부 타입은 **전부 타입 층**이라 방출물에 자국이 없기 때문이다.\
  ★ 그 축의 정본은 [**23번 주제**](../23-typeof-type-operator/)다.

비용 — 없다. **무엇을 근거로 쓸 수 있는지**를 미리 선언해 두는 절이다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  type Naked<T>   = T extends string ? "문자" : "아님";        ★ 2.8 -- 네이키드, 분배한다
  type Wrapped<T> = [T] extends [string] ? "문자" : "아님";    ★ 감싸면 안 한다

  type ToArr<T>    = T extends unknown ? T[] : never;          -> string[] | number[]
  type ToArrOff<T> = [T] extends [unknown] ? T[] : never;      -> (string | number)[]

  type NotNaked<T extends unknown[]> = T[number] extends string ? … ;  ★ 이것도 네이키드가 아니다

  type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";   ★ 반드시 감싼다

  type MyExclude<T, U>    = T extends U ? never : T;           ★ 분배가 곧 기능이다
  type MyExtract<T, U>    = T extends U ? T : never;
  type MyNonNullable<T>   = T extends null | undefined ? never : T;
```

**규칙 불릿**

- ★★★ **`extends` 왼쪽에 타입 매개변수가 그 자체로 서 있으면 분배한다**(1절 5행).
- ★★★ **무엇으로든 감싸면 분배가 꺼진다**(1절 6행). `[T]` 가 관용구다.
- ★★★ **감싸지 않아도 네이키드가 아닐 수 있다** — `T[number]` 처럼 **계산된 자리**(2절 16행).
- ★★ **인자가 유니온이 아니면 두 꼴의 답이 같다**(2절 7·8행) — **유니온으로 던져야 보인다.**
- ★★★ **`never` 는 원소 0개의 유니온이라 분배가 0번 돈다 — 결과가 `never`** 다(3절 6·10행).
- ★★★ **`[never] extends [string]` 은 참이다** — 감싼 쪽은 정반대로 통과한다(3절 7행).
- ★★★ **`T extends never ? …` 로는 `never` 를 못 잡는다**(3절 13행). `[T] extends [never]` 를 써라.
- ★★ **`never` 는 유니온에 들어가기 전에 사라진다**(3절 16행).
- ★★ **`boolean` 은 `true \| false` 로 쪼개진다**(4절 8행). ★ 답이 같으면 **하나로 합쳐져** 안 쪼개진 것처럼 보인다(4절 7행).
- ★★ **`any` 는 네이키드 자리에서 양쪽 가지를 다 낸다**(4절 11행). 감싸면 **참 쪽**이다(4절 12행).
- ★ **`unknown` 은 `any` 와 다르다** — 거짓 가지 하나다(4절 13행).
- ★★★ **`Exclude`·`Extract`·`NonNullable` 은 분배 위에 서 있다** — 끄면 무너진다(5절 16행).
- ★★ **제네릭 안에서 조건부는 지연되고, 지연된 조건부에는 값을 못 넣는다**(6절 5·6행).

**금지 사례** — 이 주제에서 던져 받은 것 셋이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 지연된 조건부에 값 넣기   ->  TS2322  Type '"문자"' is not assignable to type 'IsStr<T>'.
                                          (6절 6행)
2) Java 에 유니온 타입       ->  javac   "> or ',' expected"  -- 파서가 먼저 죽는다
                                          (7절 4행)
3) never 를 T extends never  ->  진단 없음. 결과가 never 라 2창이 침묵한다
                                          (3절 13행 -- IsNever 로 바꿔 물어야 보인다)
```

## 어디서 틀리나

- ★★★ 「**감싸지만 않으면 분배되겠지**」 — **`T[number]` 는 감싸지 않았는데도 안 된다**(2절 16행).
- ★★★ 「**답이 하나면 분배가 안 된 것이겠지**」 — `Naked<boolean>` 이 **`"아님"`** 하나다(4절 7행).\
  **쪼갰는데 답이 같아 합쳐진 것**이다. 갈리는 조건으로 다시 던져라(4절 8행).
- ★★★ 「**`never` 를 넣으면 거짓 가지가 나오겠지**」 — **아무 가지도 안 나온다.** 결과가 `never` 다(3절 6행).
- ★★★ 「**`[T]` 로 감싸면 안전하겠지**」 — `never` 에서는 **감싼 쪽이 참으로 통과한다**(3절 7행). 안전한 쪽이 뒤집힌다.
- ★★★ 「**`T extends never` 로 `never` 를 잡겠지**」 — **참이 나오는 입력이 없다**(3절 13·14행).
- ★★ 「**`Exclude` 는 내장이라 특별하겠지**」 — **한 줄짜리 조건부**이고 **분배를 끄면 무너진다**(5절 8·16행).
- ★★ 「**`any` 는 아무 가지나 하나 고르겠지**」 — **둘 다 낸다**(4절 11행).
- ★★ 「**`string[] \| number[]` 와 `(string \| number)[]` 는 같은 것이겠지**」 — **다르다**(1절 12·13행).\
  분배를 켰느냐가 그 차이를 만든다.
- ★★ 「**탐침에 진단이 없으면 아무 일도 없는 것이겠지**」 — **답이 `never` 라 침묵한 것**일 수 있다(4절 14행).
- ★ 「**제네릭 안에서도 조건부가 풀리겠지**」 — **안 풀린다.** 값도 못 넣는다(6절 5·6행).
- ★ 「**`strict` 를 끄면 뭔가 달라지겠지**」 — **다섯 파일이 한 글자도 같다**(8절).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 이 판이 보여 준 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(2.8)** | 네이키드 타입 매개변수에서 유니온이 **분배**된다 | 1절 5행 — ★ 규칙으로 알려진 것이고 **이 판에서 던져 확인했다** |
| **언어 보장(2.8)** | 감싸면 분배가 **꺼진다** | 1절 6행 |
| **언어 보장** | `never` 는 **원소 0개의 유니온**이므로 분배가 0번 돈다 | 3절 6·10행 |
| **언어 보장** | `boolean` 의 속은 `true \| false` 다 | 4절 8행 |
| **언어 보장(2.8)** | `Exclude`·`Extract`·`NonNullable` 의 정의 | 5절 8\~13행 — 손으로 쓴 것과 **글자까지 같다** |
| **언어 보장** | 제네릭 안에서 조건부는 **지연**된다 | 6절 5·6행 |
| **★ 이 판(7.0.2)의 관찰** | ★★★ `T[number]` 가 **네이키드가 아니다** | 2절 16행 — **던져서** 얻었다 |
| **★ 이 판의 관찰** | ★★★ `any` 가 **양쪽 가지를 다 내는** 것 · 감싸면 **참 쪽**인 것 | 4절 11·12행 |
| **★ 이 판의 관찰** | ★★ 답이 같으면 **유니온이 하나로 합쳐져** 분배가 안 보이는 것 | 4절 7행 |
| **★ 이 판의 관찰** | 유니온을 **별칭 이름으로** 찍는 것(`Color`) | 5절 10·11행 — 표시 방식이지 타입이 아니다 |
| **이 판의 관찰** | 유니온 원소의 **표시 순서** | 8절 — 5회 md5 가짓수 1. **관찰이지 보장이 아니다** |
| **이 판의 관찰** | 진단 **문구** 전문 · **연쇄 설명 줄**이 붙는 조건 | 코드(`TS2322`)가 더 오래 간다 |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 같다** | 8절 |
| **★ 부적용 — 5창(`.d.ts`)** | **잴 것이 없다** — 조건부를 계산하지 않는다 | 8절 |
| **★ 부적용 — 3창(`.js`)** | **잴 것이 없다** — 조건부는 전부 타입 층이다 | 0절 |
| **안 잰 것** | 조건부의 **검사 시간**·메모리 | ★★★ **재지 않았다.** 목록의 **45번 주제**가 정본이다 |

★★★ **이 주제의 함정은 거의 전부 「이 판의 관찰」 칸이 아니라 「언어 보장」 칸에 있다** —
규칙은 단순한데 **`never`·`boolean`·`any` 라는 세 경계에서 직관이 무너진다.**
**규칙을 외우는 것보다 그 셋을 각각 던져 보는 쪽이 빠르다.**

## 언제 쓰고 언제 안 쓰나

| 분배를 **켠다**(네이키드) | **끈다**(감싼다) |
|---|---|
| 유니온을 **원소마다** 걸러야 할 때(`Exclude`·`Extract`) | 유니온 **전체**를 한 덩어리로 판정할 때 |
| 원소마다 다른 타입으로 **바꿔야** 할 때(1절 `ToArr`) | `never` 인지 **물어야** 할 때 — 반드시 감싼다(3절) |
| 결과가 유니온으로 벌어져도 **괜찮을** 때 | 결과를 **하나로** 고정하고 싶을 때 |
| ★ 유니온 배열이 아니라 **배열의 유니온**이 필요할 때(1절 12행) | ★ **섞인 배열**을 받아야 할 때(1절 13행) |

| 조건부 타입을 **쓴다** | **안 쓴다** |
|---|---|
| 입력 타입에 따라 **출력 타입이 갈릴** 때 | 오버로드로 충분할 때 — [**16번 주제**](../16-function-types-and-overloads/) 쪽이 읽기 쉽다 |
| 유틸리티 타입을 **직접 만들** 때 | 표준 `Exclude`·`Extract` 로 되는 일 — **다시 만들지 마라**(5절) |
| 유니온을 **가공**해야 할 때 | ★ 제네릭 안에서 **값을 만들어야** 할 때 — 지연 때문에 `as` 가 는다(6절) |

## 핵심 문장

1. **조건부 타입의 질문은 「참이냐 거짓이냐」가 아니라 「무엇을 검사대에 올렸느냐」다.**
2. **`extends` 왼쪽에 타입 매개변수가 혼자 서 있으면 분배한다** — 감싸도, 계산해도 꺼진다.
3. **`never` 는 원소 0개의 유니온이라 분배가 0번 돈다** — 그래서 답이 사라진다.
4. **그런데 감싸면 `never` 가 참으로 통과한다** — 두 꼴이 `never` 에서 정반대다.
5. **답이 하나라고 분배가 안 된 것은 아니다** — 합쳐졌을 수 있다.
6. **`Exclude` 는 분배 위에 서 있다** — 끄면 기능 자체가 없어진다.
7. **제네릭 안에서 조건부는 지연되고, 지연된 조건부에는 값을 못 넣는다.**

## 관련 자료

- [**22번 주제** — `keyof` 와 인덱스 접근 타입](../22-keyof-and-indexed-access-types/) — ★★★ **사슬의 앞**이고 README 의 선행이다. 여기 조건의 재료가 그쪽에서 온다.
- [**25번 주제** — `infer` 와 재귀 조건부 타입](../25-infer-and-recursive-conditional-types/) — ★★★ **사슬의 급소.** 같은 조건부에 **이름 붙이기와 되풀이**가 붙는다.
- [**23번 주제** — `typeof` 타입 연산자](../23-typeof-type-operator/) — ★ **다른 축**이다(값 공간 / 타입 공간). 3창의 정본은 그쪽.
- [**09번 주제** — 유니온 타입](../09-union-types/) — 분배될 **소포**가 무엇인지는 그쪽이 정본. 여기는 **그 소포를 어떻게 푸느냐**부터.
- [**10번 주제** — 인터섹션 타입](../10-intersection-types/) — 7절의 `&` 대비. 교차는 분배되지 않는다.
- [**04번 주제** — `any`·`unknown`·`never`·`void`](../04-any-unknown-never-void/) — ★★ **`never` 의 정본.** 3·4절의 함정이 전부 그 성질에서 나온다.
- [**19번 주제** — 제네릭 기본](../19-generics-basics/) — 6절의 지연은 **타입 매개변수가 언제 채워지나**의 이야기다.
- [**21번 주제** — 추론 제어](../21-inference-control-const-and-noinfer/) — 8절의 `--strict` 대조가 **그쪽과 갈린 자리**다.
- 목록의 **26번 주제**(매핑 타입) — `in keyof` 로 도는 것과 조건부로 가르는 것은 다른 도구다.
- 목록의 **28번 주제**(유틸리티 타입) — ★ 5절의 세 유틸리티는 **거기가 정본**이고, 여기서는 **분배 위에 서 있다는 사실**까지만.
- 목록의 **45번 주제**(타입 수준 성능) — ★★★ **비용·시간은 전부 그쪽이다. 이 문서는 재지 않았다.**
- `` Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **15번**([`sealed` (17+) — `permits`·허용 계층의 조건](../../../java/syntax/15-sealed-classes/)) `` — 7절의 대비. Java 가 「여럿 중 하나」를 적는 법.

## 용어 풀이

> **조건부 타입(conditional type)** — `T extends U ? X : Y`. 타입 자리에 쓰는 삼항 연산자다.\
> 예: `type IsStr<T> = T extends string ? "문자" : "아님"` 은 문자열이면 `"문자"`, 아니면 `"아님"`.

> **분배(distribution)** — 유니온을 **원소마다 쪼개** 조건부를 따로 돌린 뒤 결과를 **다시 유니온으로** 합치는 것.\
> 예: `Naked<string | number>` 가 `"문자" | "아님"` 이 되는 것(1절 5행).

> **네이키드 타입 매개변수(naked type parameter)** — `extends` 왼쪽에 타입 매개변수가 **그 자체로** 서 있는 것.\
> 예: `T extends U` 는 네이키드이고, `[T] extends [U]`·`T[number] extends U` 는 아니다(2절).

> **분배 끄기** — 양쪽을 같은 모양으로 **감싸** 하나의 타입으로 만드는 것.\
> 예: `[T] extends [U]`. 대괄호가 아니어도 되지만 **튜플이 관용구**다.

> **빈 유니온** — 원소가 **0개**인 유니온. TypeScript 에서 그 이름이 `never` 다.\
> 예: `Naked<never>` 는 판정을 **0번** 하므로 결과도 `never` 다(3절 6행).

> **`IsNever<T>`** — `[T] extends [never] ? … : …`. `never` 인지 **물어보는 관용구**다.\
> 예: 이 배치에서 **2창이 침묵하는 자리**마다 이것으로 바꿔 물었다(3·4·5절).

> **지연된 조건부(deferred conditional type)** — 타입 매개변수가 아직 안 채워져 **판정을 미룬** 조건부.\
> 예: 제네릭 함수 안의 `IsStr<T>` 는 `IsStr<T>` 그대로 찍히고 값도 못 받는다(6절 5·6행).

> **연쇄 설명 줄** — 진단 아래 **들여써서** 딸려 나오는 줄. 유니온의 **어느 원소가 걸렸는지**를 알려 준다.\
> 예: 1절 5행 아래의 `Type '"문자"' is not assignable …` — 그 줄이 있으면 답이 **여럿**이다.

> **별칭 이름으로 찍기** — 계산 결과가 어떤 별칭과 같으면 tsc 가 **그 이름으로** 보여 주는 것.\
> 예: 5절 10행의 `Color` — 실제로는 세 원소의 유니온이다.

> **봉인 계층(sealed hierarchy)** — 허용된 하위 타입을 **이름으로** 못 박은 계층. Java 의 `sealed`.\
> 예: 7절의 대비 — 유니온과 달리 **아무 타입이나** 묶을 수 없다.

## 더 들어가면

- **왜 감싸는 것으로 분배가 꺼지나** — 분배는 「**네이키드 타입 매개변수**」라는 **자리 조건**에 걸려 있다.\
  `[T]` 로 감싸면 왼쪽이 더 이상 타입 매개변수가 아니라 **튜플 타입**이라 그 조건이 깨진다.\
  ★ 그래서 **대괄호일 필요가 없다** — 조건은 「감쌌다」가 아니라 「네이키드가 아니다」이고,\
  2절 16행의 `T[number]` 가 그 증거다. **이 문서에서는 `[T]` 와 `T[number]` 두 꼴만 던졌다.**
- **`never` 가 왜 유니온인가** — 유니온은 「이것들 중 하나」다. 후보가 **0개**면 「어느 것도 아니다」가 되고,\
  그 타입에는 **값이 하나도 없다.** 그것이 `never` 다.\
  분배는 「원소마다 돈다」이므로 원소가 0개면 **0번 돈다.** 결과도 0개 — 다시 `never` 다.\
  ★ 3절 10행이 이것을 가장 짧게 보여 준다. **조건이 항상 참이어도 결과는 `never`** 다.
- **`[never] extends [string]` 은 왜 참인가** — `never` 는 **모든 타입에 할당 가능**하다(값이 없으므로).\
  감싸면 분배가 안 도니 **할당 가능성 판정이 그대로** 나오고, 그래서 참이다(3절 7행).\
  ★★ 이 두 사실(**분배는 0번 돈다** · **할당은 항상 된다**)이 **같은 성질의 두 얼굴**이다.\
  네이키드 쪽에서는 사라지고, 감싼 쪽에서는 통과한다.
- **`any` 가 왜 양쪽 다인가** — `any` 는 「무엇이든」이므로 `string` 일 수도, 아닐 수도 있다.\
  네이키드 자리에서는 **두 가능성을 모두 답**으로 내놓고(4절 11행), 감싼 자리에서는 **참 쪽**으로 정해진다(4절 12행).\
  ★ 실무에서 `any` 가 섞이면 **조건부의 하류가 전부 두 갈래로 벌어진다** — `unknown` 을 쓰면 안 그렇다(4절 13행).
- **왜 `Exclude` 를 직접 만들면 안 되나** — 만들 수 있고 **글자까지 같은 답**이 나온다(5절 8·9행).\
  그런데 표준을 쓰면 **분배를 끌 일이 없다.** 직접 만든 것은 나중에 누군가 `[T]` 를 씌워 **조용히 무너뜨린다**(5절 16행).\
  ★ 이 절의 값은 「만드는 법」이 아니라 「**무너뜨려 본 것**」에 있다.
- **지연이 왜 `as` 를 부르나** — 6절 6행이 답이다. 조건이 안 풀렸으니 **어느 가지의 값도 받을 수 없다.**\
  컴파일러는 「아직 모른다」를 「아무거나 된다」로 읽지 않는다.\
  ★ 그래서 구현 안에서는 `as` 로 넘기고 **계약은 시그니처가 지킨다** — 이 위험은 목록의 **30번 주제** 쪽 이야기다.
- **이 주제에서 안 던진 것** — 매핑 타입과 함께 쓰기(목록의 **26번 주제**) · `infer` 를 붙인 조건부([**25번 주제**](../25-infer-and-recursive-conditional-types/)) ·\
  조건부의 **검사 비용**(목록의 **45번 주제**). ★★★ **비용은 재지 않았으므로 이 문서에 수치가 한 개도 없다.**
