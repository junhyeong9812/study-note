# ts/syntax/22 — `keyof` 와 인덱스 접근 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Keyof Type Operator](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html) ·
> [Handbook — Indexed Access Types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html) ·
> [Handbook — Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html).
> 위 링크는 **규칙 확인용**이고, 본문의 모든 출력은 **이 판에서 직접 던져 받은 것**이다. 핸드북 문장을 옮기지 않았다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version · javac -version · rustc --version (sh exit=0) =====
Version 7.0.2
v18.19.1
javac 21.0.5
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

> ★★★ **이 주제의 본체는 2창(`null` 탐침)이다.** `keyof` 가 무엇으로 펼쳐지는지는 **탐침이 아니면 안 보인다** —
> 소스에는 `keyof User` 라고만 적혀 있고 그 안에 무엇이 들었는지는 한 글자도 안 적혀 있다.
> ★★ **탐침이란** — 일부러 틀린 주석 `const p: null = …` 을 달아
> `TS2322 … is not assignable to type 'null'` 로 **컴파일러가 타입을 말하게** 하는 수다.
> 이 문서의 `TS2322` 는 대부분 **에러가 아니라 출력**이다. 세지 말고 읽어라.
> ★★★ **그런데 이 주제의 탐침에는 조수가 하나 필요하다** — 1절을 보라.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 **대조용 배너**다. 실파일에는 없고, **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> **버전** — `keyof` 와 인덱스 접근 타입은 **TS 2.1** 부터다. 이 판은 **7.0.2** 다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | ★★ 키 유니온의 **표시 순서**(`'"active" \| "id" \| "name"'`) | 8절 — 5회 md5 **가짓수 1**. **관찰이지 보장이 아니다** |
| **★ 구현 층** | ★★★ `keyof User` 를 **별칭 이름으로 찍느냐 펼쳐 찍느냐** | 1절 — 「표시」의 문제다. `& {}` 가 펼치게 만든다 |
| **★ 구현 층** | ★★ 긴 유니온을 `... 18 more ...` 로 **자르는 것** | 2절 — 그래서 **창을 바꿔 물었다** |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 한 글자도 같다** | 8절의 `--strict` 대조 블록 |
| **★ 부적용 — 3창(`.js`)** | **잴 것이 없다** — `keyof` 도 `T[K]` 도 **전부 타입 층**이다 | 이 문서에 `.js` 블록이 **하나도 없다** |
| **★ 부적용 — 5창(`.d.ts`)** | **잴 것이 없다** — `.d.ts` 는 **계산하지 않는다** | 6절 — `keyof User` 를 **적은 그대로** 남긴다 |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 색·소스 발췌 | 기본값이 **`true`** 다. 모든 블록을 **`--pretty false`** 로 고정했다 |
| **부적용 — 여러 번 돌려 보기** | 난수·시각·순서 비보장이 **한 칸도 없다** | 그래도 8절에서 5회 확인했다 |
| **안 잰 것** | 거대한 키 유니온의 **검사 시간**·메모리 | **재지 않았다.** 수치를 적지 않는다 |

★★ `--strict` 결과가 [**21번 주제**](../21-inference-control-const-and-noinfer/)와 **다르다** —
거기서는 여섯 파일 중 하나가 갈렸는데, **여기서는 다섯 중 하나도 안 갈렸다.**
`keyof` 는 **플래그를 안 탄다.**

## 한눈에 — 쉽게 말하면

**`keyof` 는 「이 서랍장에 달린 손잡이 이름을 전부 모은 목록」이고, `T[K]` 는 「그 손잡이를 당겼을 때 나오는 물건」이다.**

| 비유 | 실체 |
|---|---|
| 서랍장에 달린 **손잡이 이름표 목록** | `keyof User` → `"active" \| "id" \| "name"` |
| 손잡이를 **당겨서 꺼낸 물건** | `User["name"]` → `string` |
| 손잡이를 **전부 당겨** 나온 물건들 | `User[keyof User]` → `string \| number \| boolean` |
| ★★★ 서랍에 「**아무 이름이나 받는 칸**」이 하나 있으면 목록이 무너진다 | 인덱스 시그니처 → `string \| number`(1절) |
| ★ 손잡이가 **안쪽에만 달린 것**은 목록에 없다 | `private`·`#` 필드(3절) |
| ★★ 없는 손잡이를 당기면 **당기기 전에** 막힌다 | `TS2345` — 런타임이 아니라 컴파일 타임(5절) |

- ★★★ 한 줄로 — 「**`keyof` 는 키를 값이 아니라 타입으로 만든다.**」
  `Object.keys(o)` 는 **런타임 배열**이고 `keyof T` 는 **컴파일 타임 유니온**이다. 둘은 만나지 않는다(7절).
- ★★ 그래서 값이 이 둘이다 — **오타를 컴파일 타임에 잡는 것**과 **키마다 값 타입이 달라지는 것**(5절).

```text
  keyof 와 T[K] -- 목록과 꺼내기

     interface User { id: number; name: string; active: boolean }

                  keyof User
                      │
        ┌─────────────┼─────────────┐
     "id"          "name"        "active"       <- 키의 유니온 (타입이다)
        │             │             │
        │  User["id"] │ User["name"]│ User["active"]
        ▼             ▼             ▼
     number        string        boolean        <- 그 키의 값 타입

     User[keyof User]  =  string | number | boolean     <- 전부 당긴 것
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **`keyof T` 는 정확히 무엇으로 펼쳐지나** — 인터페이스·인덱스 시그니처·배열·클래스·`any` 를 **전부 던져** 본다(1\~3절).
2. **`T[K]` 로 무엇까지 꺼낼 수 있나** — 하나·여럿·전부·없는 키·튜플·중첩(4절).
3. **`obj[key]` 는 어떻게 안전해지나** — ★★★ **세 단계를 나란히 놓고** 무엇이 갈리는지 본다(5절).

★★★ **22 → 24 → 25 는 한 사슬이고 25 가 급소다.**
여기서 만든 **키 유니온**이 [**24번 주제**](../24-conditional-types-and-distribution/)에서 **분배되고**,
[**25번 주제**](../25-infer-and-recursive-conditional-types/)에서 **`infer` 로 되뽑힌다.**
★★ [**23번 주제**](../23-typeof-type-operator/)는 **다른 축**이다 — 사슬이 아니라 「값 공간 / 타입 공간」이라는 직교하는 축이고,
**`keyof typeof x` 에서 딱 한 번 만난다**(3절 24행 · 4절).

## 동작 방식

### (0) 이 주제가 쓰는 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **2창 — `null` 탐침** | 컴파일러가 **계산한** 키 유니온 | **본체.** 1·3·4·5절 |
| ★★ **1창 — 멤버십 대입** | 그 낱낱의 값이 `keyof T` 에 드느냐 | **조수.** 2절 — 탐침이 목록을 자를 때 |
| ★ **진단이 나는 것 자체** | 「막혀야 정상」인 자리가 막혔다 | 5절 `TS2345` · 4절 `TS2339` |
| ★ **부적용 — 3창(`.js`)** | ★★ **잴 것이 없다** | `keyof`·`T[K]` 는 **방출에 아무 자국이 없다** |
| ★ **부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** | **계산하지 않는다**(6절) |

★★★ 마지막 두 줄이 이 주제의 성질이다 — [**18번**](../18-this-parameter-types/)·[**19번**](../19-generics-basics/)이 `.js` 로 결론을 낸 자리가
여기서는 「**잴 것이 없다**」다. 「재 봤더니 같았다」가 아니다.
[**20번**](../20-generic-constraints-and-defaults/)·[**21번**](../21-inference-control-const-and-noinfer/)과 같은 칸이고, 그래서 이 세 주제는 **순수 타입 층**이다.

### ★★ 제5의 상태 — 같은 질문을 다른 창으로 물었다

2절이 그 자리다. **`keyof string[]` 을 2창으로 물으면 tsc 가 `... 18 more ...` 로 잘라서 답한다.**
「못 잰 것」도 「부적용」도 아니다 — **창을 바꿔 답한 것**이다.
그래서 **1창(멤버십 대입)으로 낱낱이 물었다**(`"length"`·`"map"`·`0` 은 들고 `"0"` 은 안 든다).
★ **바꾼 창이 못 보는 것** — **전체 목록**은 여전히 못 본다. **물어본 것만** 안다.

비용 — 컴파일 여덟 번(TS 일곱 + Java 한 번) + `--strict` 대조 열 번 + 순서 확인 열다섯 번.

### (1) ★★★ `keyof` 가 무엇으로 펼쳐지나 — 그리고 탐침의 조수 `& {}`

**언제 쓰나** — 「`keyof T` 안에 정확히 무엇이 들었는지」를 알아야 할 때. 이 주제의 출발점이다.

```ts
// ex.22a.ts
// keyof 가 무엇으로 펼쳐지나 -- 인터페이스 · 인덱스 시그니처 · any · 유니온 · 교차
interface User {
    id: number;
    name: string;
    active: boolean;
}
const asName: null = null as unknown as keyof User;
const expanded: null = null as unknown as keyof User & {};

interface StringDict {
    [k: string]: number;
}
const strKeys: null = null as unknown as keyof StringDict;

interface NumberDict {
    [k: number]: number;
}
const numKeys: null = null as unknown as keyof NumberDict;

interface Mixed {
    [k: string]: number;
    fixed: number;
}
const mixedName: null = null as unknown as keyof Mixed;
const mixedKeys: null = null as unknown as keyof Mixed & {};

const anyKeys: null = null as unknown as keyof any;
const unknownKeys: null = null as unknown as keyof unknown;
const neverKeys: null = null as unknown as keyof never;

interface A {
    x: number;
    shared: string;
}
interface B {
    y: boolean;
    shared: string;
}
const unionKeys: null = null as unknown as keyof (A | B);
const interKeys: null = null as unknown as keyof (A & B);
console.log(asName, expanded, strKeys, numKeys, mixedName, mixedKeys, anyKeys, unknownKeys, neverKeys, unionKeys, interKeys);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.22a.ts (tsc exit=1) =====
ex.22a.ts(7,7): error TS2322: Type 'keyof User' is not assignable to type 'null'.
  Type '"active"' is not assignable to type 'null'.
ex.22a.ts(8,7): error TS2322: Type '"active" | "id" | "name"' is not assignable to type 'null'.
  Type '"active"' is not assignable to type 'null'.
ex.22a.ts(13,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.22a.ts(18,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.22a.ts(24,7): error TS2322: Type 'keyof Mixed' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.22a.ts(25,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.22a.ts(27,7): error TS2322: Type 'string | number | symbol' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.22a.ts(29,7): error TS2322: Type 'string | number | symbol' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.22a.ts(39,7): error TS2322: Type '"shared"' is not assignable to type 'null'.
ex.22a.ts(40,7): error TS2322: Type '"shared" | "x" | "y"' is not assignable to type 'null'.
  Type '"shared"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **열 건**이고 **전부 탐침**이다. 그리고 **진단이 안 난 탐침이 하나 있다**(28행) — 그것도 답이다.
- ★★★ **7행과 8행이 이 절의 급소다.** 같은 `keyof User` 인데\
  7행은 **`keyof User`** 라고 **별칭 이름 그대로** 되돌려 주고, 8행은 **`"active" | "id" | "name"`** 으로 **펼쳐** 준다.\
  차이는 **`& {}` 하나**뿐이다.
- ★★ 그러므로 **탐침만으로는 부족하다.** `keyof T` 를 물으면 tsc 가 「`keyof T` 다」라고 **되돌려 말한다** —\
  답이 아니라 메아리다. **`& {}` 를 붙여 교차로 만들면** 그 이름을 못 쓰고 펼쳐 적는다.
- ★★★ 이것은 **명세가 정한 규칙이 아니라 tsc 7.0.2 의 「표시」 방식**이다. **구현 층**에 적어라.
- ★★★ 13행이 **README 가 지정한 과녁**이다. **문자열 인덱스 시그니처**가 있으면 `keyof` 가 **`string | number`** 로 넓어진다.\
  ★ **`number` 가 왜 끼나** — JS 에서 `o[0]` 은 `o["0"]` 이므로 **숫자 키도 문자열 인덱스에 걸린다.**
- ★★ 18행 — **숫자 인덱스 시그니처**만 있으면 **`number`** 다. `string` 이 안 낀다. **방향이 한쪽이다.**
- ★★★ 24·25행이 **가장 아픈 자리**다. `Mixed` 는 `fixed: number` 라는 **이름 있는 키를 가졌는데도**\
  펼치면 **`string | number`** 다 — **`"fixed"` 라는 리터럴이 목록에서 사라졌다.**\
  **인덱스 시그니처가 이름 있는 키를 삼킨다.** 이것이 「인덱스 시그니처가 `keyof` 를 넓힌다」의 정확한 뜻이다.
- ★★ 27행 — `keyof any` 는 **`string | number | symbol`** 이다. **JS 의 키가 될 수 있는 것 전부**다.
- ★★★ 28행이 **조용하다.** `keyof unknown` 은 **`never`** 라서 탐침이 아무 말도 안 한다 —\
  `never` 는 `null` 에도 할당되므로 **진단이 날 이유가 없다.** ★ **탐침의 사각지대**다([**24번 주제**](../24-conditional-types-and-distribution/)가 그 창을 바꾼다).
- ★★ 29행 — `keyof never` 는 거꾸로 **`string | number | symbol`** 이다. `keyof any` 와 **같다.**\
  ★ 28행과 29행이 **정반대**라는 것이 이 줄의 값이다.
- ★★★ 39·40행이 **방향이 뒤집히는 자리**다.\
  **유니온의 `keyof` 는 키의 교집합**(`"shared"`), **교차의 `keyof` 는 키의 합집합**(`"shared" | "x" | "y"`)이다.

```text
  유니온과 교차에서 keyof 의 방향이 뒤집힌다

  interface A { x: number;  shared: string }
  interface B { y: boolean; shared: string }

     A | B  (둘 중 하나다)            A & B  (둘 다다)
     ────────────────────            ────────────────────
     무엇이 들었는지 모른다           양쪽 멤버를 다 가진다
     둘 다 가진 키만 안전             아무 키나 안전
          ▼                               ▼
     keyof (A|B) = "shared"          keyof (A&B) = "shared" | "x" | "y"
       ★ 교집합                        ★ 합집합
```

```text
  인덱스 시그니처가 이름 있는 키를 삼킨다

  interface Mixed {
      [k: string]: number;     <- 아무 문자열이나 키가 된다
      fixed: number;           <- 이름이 있는 키
  }

     기대            "fixed" | string | number
     실제            string | number                 ★ "fixed" 가 사라졌다

     왜   "fixed" 는 string 의 부분이다. 유니온이 흡수한다.
          (같은 일이 "id" | string = string 에서도 일어난다)
```

> **인덱스 시그니처(index signature)** — `[k: string]: V` 처럼 **키 이름을 정하지 않고 값 타입만** 정한 선언.\
> 예: `{ [k: string]: number }` 는 `o.아무거나` 를 `number` 로 읽게 해 준다. 정본은 [**07번 주제**](../07-object-type-details/).

비용 — 인덱스 시그니처를 하나 넣으면 **그 타입의 `keyof` 가 통째로 넓어진다.**
키 안전 접근을 쓰려던 목적이 **그 한 줄로 사라진다**(5절 비교).

### (2) ★★ 배열의 `keyof` — `number` 만이 아니다 (제5의 상태)

**언제 쓰나** — 「배열에 `keyof` 를 걸면 인덱스만 나오겠지」라고 생각했을 때.

```ts
// ex.22b.ts
// 배열의 keyof -- number 만이 아니다. 멤버십으로 하나씩 물어본다
const arrName: null = null as unknown as keyof string[];
const arrKeys: null = null as unknown as keyof string[] & {};
const tupleKeys: null = null as unknown as keyof [1, 2] & {};

const isNumber: keyof string[] = 0;
const isLength: keyof string[] = "length";
const isMap: keyof string[] = "map";
const isDigitString: keyof string[] = "0";

const onlyStringKeys: null = null as unknown as `${keyof string[] & string}`;
console.log(arrName, arrKeys, tupleKeys, isNumber, isLength, isMap, isDigitString, onlyStringKeys);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.22b.ts (tsc exit=1) =====
ex.22b.ts(2,7): error TS2322: Type 'keyof string[]' is not assignable to type 'null'.
  Type 'number' is not assignable to type 'null'.
ex.22b.ts(3,7): error TS2322: Type 'number | "at" | "concat" | "copyWithin" | "entries" | "every" | "fill" | "filter" | "find" | "findIndex" | "flat" | "flatMap" | "forEach" | "includes" | "indexOf" | "join" | "keys" | ... 18 more ... | unique symbol' is not assignable to type 'null'.
  Type 'number' is not assignable to type 'null'.
ex.22b.ts(4,7): error TS2322: Type 'number | "0" | "1" | "at" | "concat" | "copyWithin" | "entries" | "every" | "fill" | "filter" | "find" | "findIndex" | "flat" | "flatMap" | "forEach" | "includes" | "indexOf" | "join" | ... 19 more ... | unique symbol' is not assignable to type 'null'.
  Type 'number' is not assignable to type 'null'.
ex.22b.ts(9,7): error TS2322: Type '"0"' is not assignable to type 'keyof string[]'.
ex.22b.ts(11,7): error TS2322: Type '"at" | "concat" | "copyWithin" | "entries" | "every" | "fill" | "filter" | "find" | "findIndex" | "flat" | "flatMap" | "forEach" | "includes" | "indexOf" | "join" | "keys" | "lastIndexOf" | ... 15 more ... | "values"' is not assignable to type 'null'.
  Type '"at"' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **다섯 건**이다. ★ **6·7·8행은 진단이 없다** — 그 셋이 **통과했다는 것이 답**이다.
- ★★★ 2행 — 그냥 물으면 또 **`keyof string[]`** 이라는 메아리다(1절과 같다).
- ★★★ 3행에서 `& {}` 로 펼쳤더니 **`number` 로 시작해서 메서드 이름이 줄줄이** 나오고\
  끝이 **`unique symbol`** 이다. 그런데 가운데가 **`... 18 more ...`** 로 **잘렸다.**\
  ★★ **이것이 제5의 상태다** — 창이 답을 주긴 하는데 **전부를 안 준다.**
- ★★ 그래서 **1창(멤버십 대입)으로 바꿔 물었다.** 6·7·8행이 **조용히 통과**한다 —\
  **`0` 도 `"length"` 도 `"map"` 도 `keyof string[]` 에 든다.**
- ★★★ 9행이 **경계**다. **`"0"`(문자열)은 `TS2322` 로 막힌다.**\
  「Type '"0"' is not assignable to type 'keyof string[]'.」\
  **배열의 인덱스 키는 `number` 이지 `"0"` 이 아니다** — 1절의 문자열 인덱스 시그니처와 **정반대**다.
- ★★ 4행 — **튜플**은 다르다. `keyof [1, 2]` 에는 **`"0"` 과 `"1"` 이 들어 있다**(펼친 앞머리에 보인다).\
  **길이가 고정이라 자리 이름이 리터럴로 산다.**
- ★ 11행 — 템플릿 리터럴로 **문자열 키만** 뽑으면 `number` 와 `unique symbol` 이 빠진다.\
  **메서드 이름만 남는다.** 필요한 쪽만 걸러 쓰는 수다(목록의 **27번 주제**).

```text
  배열의 keyof 에 무엇이 드나 -- 낱낱이 물어본 결과 (1창)

     const k: keyof string[] = 0          ✓ 통과   (인덱스는 number 다)
     const k: keyof string[] = "length"   ✓ 통과   (프로퍼티)
     const k: keyof string[] = "map"      ✓ 통과   (메서드 이름도 키다)
     const k: keyof string[] = "0"        ✗ TS2322 「"0" 은 keyof string[] 가 아니다」

     2창으로 통째로 물으면         number | "at" | "concat" | ... 18 more ... | unique symbol
                                                                 ▲
                                                     ★ 여기서 잘린다 -- 그래서 창을 바꿨다
```

> **제5의 상태 — 「같은 질문을 다른 창으로 물었다」** — 창이 **답을 주긴 하는데 전부를 안 줄** 때\
> 「못 잰 것」으로 적으면 거짓이고 그냥 실으면 불완전하다. **창을 바꿔 물은 사실 자체를 적는다.**\
> 예: 여기서는 2창이 목록을 잘라서 1창으로 낱낱이 물었다 — **대신 전체 목록은 여전히 모른다.**

비용 — 배열에 `keyof` 를 그냥 걸면 **원하지 않는 메서드 이름이 전부 딸려 온다.**
인덱스만 쓰고 싶으면 **`T[number]`** 를 쓴다(4절 14·17행).

### (3) ★★ `keyof` 는 public 만 본다 — 그리고 `as const` 의 진짜 값

**언제 쓰나** — 클래스나 설정 객체에 `keyof` 를 걸기 전에.

```ts
// ex.22c.ts
// keyof 는 public 만 본다 -- private · protected · static · as const
class Account {
    id = 1;
    label = "가";
    private secret = "나";
    protected note = "다";
    static bank = "은행";
    static make(): Account {
        return new Account();
    }
    balance(): number {
        return 0;
    }
}
const instanceKeys: null = null as unknown as keyof Account & {};
const staticKeys: null = null as unknown as keyof typeof Account & {};

class Hash {
    #hidden = 1;
    shown = 2;
}
const hashKeys: null = null as unknown as keyof Hash & {};

const frozen = { 가: 1, 나: 2 } as const;
const plainObj = { 가: 1, 나: 2 };
const frozenKeys: null = null as unknown as keyof typeof frozen & {};
const plainKeys: null = null as unknown as keyof typeof plainObj & {};
const frozenValues: null = null as unknown as (typeof frozen)[keyof typeof frozen];
const plainValues: null = null as unknown as (typeof plainObj)[keyof typeof plainObj];
console.log(instanceKeys, staticKeys, hashKeys, frozenKeys, plainKeys, frozenValues, plainValues);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.22c.ts (tsc exit=1) =====
ex.22c.ts(15,7): error TS2322: Type '"balance" | "id" | "label"' is not assignable to type 'null'.
  Type '"balance"' is not assignable to type 'null'.
ex.22c.ts(16,7): error TS2322: Type '"bank" | "make" | "prototype"' is not assignable to type 'null'.
  Type '"bank"' is not assignable to type 'null'.
ex.22c.ts(22,7): error TS2322: Type '"shown"' is not assignable to type 'null'.
ex.22c.ts(26,7): error TS2322: Type '"가" | "나"' is not assignable to type 'null'.
  Type '"가"' is not assignable to type 'null'.
ex.22c.ts(27,7): error TS2322: Type '"가" | "나"' is not assignable to type 'null'.
  Type '"가"' is not assignable to type 'null'.
ex.22c.ts(28,7): error TS2322: Type '1 | 2' is not assignable to type 'null'.
  Type '1' is not assignable to type 'null'.
ex.22c.ts(29,7): error TS2322: Type 'number' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **일곱 건**이고 전부 탐침이다.
- ★★★ 15행 — `keyof Account` 는 **`"balance" | "id" | "label"`** 이다.\
  **`private secret` 과 `protected note` 가 빠졌고**, **메서드 `balance` 는 들어갔다.**\
  ★★ 「필드만 나온다」가 아니다 — **`public` 이면 메서드도 키다.**
- ★★ 그리고 **`static bank` 와 `static make` 도 빠졌다.** 정적 멤버는 **인스턴스 타입에 없다.**
- ★★★ 16행이 그 짝이다. `keyof typeof Account` 는 **`"bank" | "make" | "prototype"`** —\
  **정적 쪽만** 나오고 거기에 **`"prototype"` 이 끼어 있다.**\
  ★ `typeof Account` 가 **생성자 타입**이기 때문인데, 그 규칙은 [**23번 주제**](../23-typeof-type-operator/)가 정본이다.\
  **사슬(22·24·25)과 직교하는 축이 여기서 딱 한 번 만난다.**
- ★★ 22행 — `#hidden` 은 **JS 의 진짜 private** 이고, 역시 `keyof` 에 **안 나온다**(`"shown"` 뿐).\
  ★ TS 의 `private` 와 JS 의 `#` 는 **소거되느냐 런타임에 강제되느냐**가 다른데(목록의 **32번 주제**),\
  **`keyof` 에서는 둘 다 똑같이 안 보인다.**
- ★★★ 26·27행이 **뜻밖의 자리**다. `as const` 객체와 평범한 객체의 **키가 똑같다**(`"가" | "나"`).\
  「`as const` 를 붙여야 키가 리터럴로 산다」고 예상했다면 **틀린다.**
- ★★★ 28·29행이 **진짜 갈리는 자리**다. **값 타입**이 `1 | 2` 대 **`number`** 로 갈린다.\
  **`as const` 는 키가 아니라 값을 굳힌다.**

```text
  as const 는 키가 아니라 값을 굳힌다

                         keyof            [keyof …]  (값 타입)
     ─────────────────────────────────────────────────────────
     { 가:1, 나:2 } as const     "가" | "나"      1 | 2      ★ 굳었다
     { 가:1, 나:2 }              "가" | "나"      number     ★ 넓어졌다
                                 └── 같다 ──┘     └─ 여기서 갈린다 ─┘

     그래서 as const 의 값은 keyof 쪽이 아니라 T[keyof T] 쪽에 있다.
```

```text
  keyof 가 보는 것과 못 보는 것 (클래스)

     class Account {
         id                 ✓  들어간다
         label              ✓  들어간다
         balance()          ✓  ★ 메서드도 키다
         private secret     ✗  안 보인다
         protected note     ✗  안 보인다
         static bank        ✗  인스턴스 타입에 없다  ──┐
         static make()      ✗  인스턴스 타입에 없다  ──┤
     }                                                 │
                                                       ▼
     keyof Account          = "balance" | "id" | "label"
     keyof typeof Account   = "bank" | "make" | "prototype"   ★ 정적 쪽 + prototype
```

> **`as const`** — 객체·배열 리터럴의 **속을 리터럴 타입으로 굳히고 `readonly` 를 붙이는** 단언(TS 3.4).\
> 예: `{ 가: 1 } as const` 의 `가` 는 `number` 가 아니라 `1` 이다. 정본은 [**11번 주제**](../11-literal-types-and-as-const/).

비용 — `keyof` 로 만든 API 는 **`public` 표면에 묶인다.** 나중에 필드를 `private` 로 내리면
**그 키를 쓰던 호출부가 전부 깨진다.**

### (4) `T[K]` — 인덱스 접근 타입

**언제 쓰나** — 「그 키의 값 타입」을 이름 없이 가리켜야 할 때.

```ts
// ex.22d.ts
// T[K] -- 인덱스 접근 타입. 점 표기가 아니라 대괄호다
interface User {
    id: number;
    name: string;
    active: boolean;
}
const one: null = null as unknown as User["id"];
const two: null = null as unknown as User["id" | "name"];
const all: null = null as unknown as User[keyof User];
const missing: null = null as unknown as User["없는키"];

type Tup = readonly ["가", "나"];
const tupAt: null = null as unknown as Tup[0];
const tupAny: null = null as unknown as Tup[number];

const list = ["가", "나"];
const listElem: null = null as unknown as (typeof list)[number];

interface Nested {
    inner: { deep: boolean };
}
const deep: null = null as unknown as Nested["inner"]["deep"];
console.log(one, two, all, missing, tupAt, tupAny, listElem, deep);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.22d.ts (tsc exit=1) =====
ex.22d.ts(7,7): error TS2322: Type 'number' is not assignable to type 'null'.
ex.22d.ts(8,7): error TS2322: Type 'string | number' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.22d.ts(9,7): error TS2322: Type 'string | number | boolean' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.22d.ts(10,47): error TS2339: Property '없는키' does not exist on type 'User'.
ex.22d.ts(13,7): error TS2322: Type '"가"' is not assignable to type 'null'.
ex.22d.ts(14,7): error TS2322: Type '"가" | "나"' is not assignable to type 'null'.
  Type '"가"' is not assignable to type 'null'.
ex.22d.ts(17,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.22d.ts(22,7): error TS2322: Type 'boolean' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **여덟 건**이고 그중 하나(10행)만 **진짜 에러**다.
- ★★ 7행 — `User["id"]` 는 **`number`** 다. **점 표기가 아니라 대괄호**라는 것이 형태의 전부다.\
  `User.id` 라고 쓰면 그건 **값 공간의 문법**이라 타입 자리에서 안 된다([**23번 주제**](../23-typeof-type-operator/)).
- ★★ 8행 — 키에 **유니온**을 줄 수 있다. `User["id" | "name"]` 은 **`string | number`** 다.\
  **키를 유니온으로 주면 값도 유니온으로 나온다.**
- ★★★ 9행이 관용구다. `User[keyof User]` 는 **`string | number | boolean`** —\
  **그 타입의 값 타입 전부**다. 8행의 극한이다.
- ★★★ 10행이 **에러**다. 없는 키를 주면 **`TS2339`** 다.\
  「Property '없는키' does not exist on type 'User'.」 **타입 자리에서도 오타가 잡힌다.**
- ★★ 13·14행 — 튜플은 **자리 번호**로도(`Tup[0]` → `"가"`) **`number`** 로도(→ `"가" | "나"`) 꺼낸다.\
  ★ 2절에서 본 대로 튜플은 `"0"`·`"1"` 을 키로 갖기 때문이다.
- ★★★ 17행이 **가장 쓸모 있는 관용구**다. `(typeof list)[number]` 가 **`string`** 이다 —\
  **값에서 시작해 원소 타입까지 한 줄로 간다.** `typeof` 와 `T[number]` 가 합쳐진 꼴이다.
- ★ 22행 — 중첩도 된다. `Nested["inner"]["deep"]` 은 **`boolean`** 이다. **대괄호를 이어 붙인다.**

```text
  대괄호는 이어 붙는다 -- 값에서 타입으로 가는 길

     const list = ["가", "나"]          <- 값
            │
            │  typeof list                 (23번 주제 -- 값 공간에서 타입 공간으로)
            ▼
     string[]                            <- 타입
            │
            │  [number]                    (이 주제 -- 인덱스 접근)
            ▼
     string                              <- 원소 타입

     한 줄로:  (typeof list)[number]
     ★ 괄호를 빼면 typeof (list[number]) 로 읽힌다 -- 괄호가 필요하다
```

> **인덱스 접근 타입(indexed access type)** — `T[K]` 로 **키 `K` 의 값 타입**을 꺼내는 표기.\
> 예: `User["id"]` 는 `number`. **`K` 는 `keyof T` 에 들어야 하고**, 아니면 `TS2339` 다.

비용 — `T[K]` 는 **`T` 의 모양에 묶인다.** `T` 의 키 이름이 바뀌면 그 자리가 전부 깨진다 —
그것이 장점이자 대가다.

### (5) ★★★ `obj[key]` 가 안전해지는 세 단계

**언제 쓰나** — 이 주제의 **실용적 결론**이다. 「왜 굳이 제네릭 `K` 를 쓰나」에 답한다.

```ts
// ex.22e.ts
// obj[key] 가 안전해지는 관용구 -- K extends keyof T 와 그 아래 두 단계
interface User {
    id: number;
    name: string;
    active: boolean;
}
const u: User = { id: 1, name: "가", active: true };

function getTight<T, K extends keyof T>(o: T, k: K): T[K] {
    return o[k];
}
const tight: null = getTight(u, "name");
getTight(u, "없는키");

function getLoose<T extends object>(o: T, k: keyof T) {
    return o[k];
}
const loose: null = getLoose(u, "name");

function getWide(o: Record<string, unknown>, k: string) {
    return o[k];
}
const wide: null = getWide(u as unknown as Record<string, unknown>, "없는키");

function setTight<T, K extends keyof T>(o: T, k: K, v: T[K]): void {
    o[k] = v;
}
setTight(u, "id", 2);
setTight(u, "id", "둘");
console.log(tight, loose, wide);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.22e.ts (tsc exit=1) =====
ex.22e.ts(12,7): error TS2322: Type 'string' is not assignable to type 'null'.
ex.22e.ts(13,13): error TS2345: Argument of type '"없는키"' is not assignable to parameter of type 'keyof User'.
ex.22e.ts(18,7): error TS2322: Type 'string | number | boolean' is not assignable to type 'null'.
  Type 'string' is not assignable to type 'null'.
ex.22e.ts(23,7): error TS2322: Type 'unknown' is not assignable to type 'null'.
ex.22e.ts(29,19): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
```

그림 해설 — 한 단계에 한 문장.

- 진단이 **다섯 건**이다. ★ **28행은 조용하다** — `setTight(u, "id", 2)` 가 **통과했다는 것이 답**이다.
- ★★★ 12행 — `getTight(u, "name")` 이 **`string`** 이다. **딱 그 키의 값 타입**이다.\
  `K extends keyof T` 가 **호출마다 `K` 를 그 리터럴로 굳히기** 때문이다([**20번 주제**](../20-generic-constraints-and-defaults/) 2절).
- ★★★ 18행이 **한 단계 내려간 자리**다. `k: keyof T` 로 받으면 `getLoose(u, "name")` 이\
  **`string | number | boolean`** 이다 — **어느 키인지 안 기억한다.**\
  ★★ **이것이 「왜 제네릭 K 라야 하나」의 답**이다. `keyof T` 는 **키 하나가 아니라 키 전체**이므로\
  **값도 전체**로 돌아온다.
- ★★ 23행이 **바닥**이다. `k: string` 으로 받으면 **`unknown`** 이다. **타입이 아무것도 안 남는다.**
- ★★★ 13행 — 없는 키를 주면 `TS2345` 이고 **허용되는 키 목록이 진단에 찍힌다**(`'keyof User'`).\
  **오타가 컴파일 타임에 죽는다.**
- ★★★ 29행이 **쓰기 쪽의 값**이다. `setTight(u, "id", "둘")` 이 `TS2345` 로 막힌다 —\
  「Argument of type 'string' is not assignable to parameter of type 'number'.」\
  **키와 값이 같은 `K` 로 묶여 있어서** 짝이 안 맞으면 죽는다. 28행(`2`)은 통과한다.

```text
  세 단계 -- 같은 obj[key] 인데 돌아오는 타입이 다르다

  ① K extends keyof T      getTight(u, "name")   ->  string
     키를 그 리터럴로 굳힌다                            ★ 딱 그 키의 값
     없는 키 -> TS2345

  ② k: keyof T             getLoose(u, "name")   ->  string | number | boolean
     키 전체를 받는다                                  ★ 어느 키였는지 안 남는다
     없는 키 -> TS2345

  ③ k: string              getWide(u, "없는키")  ->  unknown
     아무 문자열이나 받는다                            ★ 오타도 안 잡고 타입도 없다

  한 줄로 -- 안전해지는 것은 keyof 가 아니라 "K 를 하나로 묶는 것"이다.
```

> **키 안전 접근(key-safe access)** — `<T, K extends keyof T>(o: T, k: K): T[K]` 꼴.\
> 예: `getTight(user, "name")` 이 `string` 을 돌려준다. **키가 값 타입을 정한다.**

비용 — `K` 가 **호출자의 리터럴에 묶인다.** 키를 **런타임 변수**로 받는 자리에는 못 쓴다 —
그때는 ②나 ③으로 내려가거나 좁히기를 따로 해야 한다([**20번 주제**](../20-generic-constraints-and-defaults/) 2절 15행).

### (6) ★ 다섯째 창을 닫는다 — `.d.ts` 는 계산하지 않는다

**언제 쓰나** — 「탐침 말고 `.d.ts` 로 여러 줄을 한꺼번에 보면 되지 않나」라고 생각했을 때.

```ts
// ex.22f.ts
// 다섯째 창을 닫는 근거 -- .d.ts 는 계산하지 않는다. 적은 그대로 남긴다
interface User {
    id: number;
    name: string;
}
export type Keys = keyof User;
export const oneKey: keyof User = "id";
export type Cond = string extends string ? "가" : "나";
export const frozen = ["가", "나"] as const;
export type Elem = (typeof frozen)[number];
```

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

그림 해설 — 한 단계에 한 문장.

- ★★★ 종료 코드가 **`0`** 이고 진단이 **0줄**이다. 그 **침묵도 캡처했다** — 명령과 종료 코드까지 블록에 들어 있다.
- ★★★ `export type Keys = keyof User;` 가 **적은 그대로** 남았다. **`"id" | "name"` 으로 안 펼쳐진다.**
- ★★ `oneKey` 도 **`keyof User`** 로 남았다. 값의 타입인데도 **계산하지 않는다.**
- ★★ 조건부 타입도 **`string extends string ? "가" : "나"`** 그대로다. **한쪽으로 안 접힌다**([**24번 주제**](../24-conditional-types-and-distribution/)).
- ★★ `Elem` 도 **`(typeof frozen)[number]`** 그대로다.
- ★★★ 즉 **5창은 이 주제에 부적용**이다 — 「재 봤더니 같았다」가 아니라 **잴 것이 없다.**\
  **`.d.ts` 는 「무엇이 선언됐나」를 말하지 「무엇이 계산되나」를 말하지 않는다.**
- ★ 단 **`frozen` 한 줄은 다르다** — `readonly ["가", "나"]` 로 **추론 결과가 적혀 있다.**\
  **추론된 것은 적어 주고, 타입 수준 계산은 안 해 준다.** 그 경계가 이 블록의 값이다.

비용 — 없음. **이 절의 값은 「이 창을 쓰지 마라」를 근거와 함께 남기는 것**이다.

### (7) ★ 교차 갈래 — Java 에는 키 집합을 가진 타입이 없다

**언제 쓰나** — 「다른 언어는 이걸 어떻게 하나」가 궁금할 때.

```java
// Keyed.java
import java.util.Map;
import java.util.TreeSet;

public class Keyed {
    public static void main(String[] args) {
        Map<String, Integer> m = Map.of("가", 1, "나", 2);
        System.out.println(m.get("없는키"));
        // Map.of 의 순회 순서는 실행마다 바뀐다 -- 정렬해서 결정적으로 찍는다
        System.out.println(new TreeSet<>(m.keySet()));
        record User(int id, String name) {}
        User u = new User(1, "가");
        System.out.println(u.getClass().getRecordComponents().length);
    }
}
```

```text
===== javac -d jout Keyed.java && java -cp jout Keyed (sh exit=0) =====
null
[가, 나]
2
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 첫 줄이 **`null`** 이다. `m.get("없는키")` 가 **컴파일도 통과하고 실행도 통과하고 `null` 을 돌려준다.**\
  ★★ 5절 13행의 `TS2345` 와 정확히 대비되는 자리다 — **TS 는 던지기 전에 막고, Java 는 던지고 나서 `null` 을 준다.**
- ★★ 둘째 줄 `[가, 나]` 가 `keySet()` 이다. **런타임 값**이다 — `for` 로 돌 수 있고 출력할 수 있다.\
  **`keyof` 는 반대다** — 컴파일 타임에만 있고 **찍을 수가 없다**(그래서 이 문서 내내 탐침을 썼다).\
  ★★★ **그 줄을 `TreeSet` 으로 감싼 이유가 이 주제와 맞닿아 있다** — `Map.of` 의 순회 순서는\
  **실행마다 바뀐다**(캡처를 두 번 돌렸더니 `[가, 나]` 와 `[나, 가]` 로 갈렸다).\
  **런타임 값이라 순서가 있고, 그 순서가 보장되지 않는다.** `keyof` 가 내놓는 것은 **집합이라 그런 칸이 없다.**
- ★★ 셋째 줄 `2` 는 `record` 의 컴포넌트 수다. **런타임에 구조가 남아 있다**는 뜻이지만\
  그것도 **리플렉션 값**이지 타입이 아니다. **「키 이름이 타입이 되는」 자리는 Java 에 없다.**
- ★★★ 축을 한 줄로 — **Java 의 키는 값이고, TS 의 키는 타입이다.**\
  `Map<String, Integer>` 의 `String` 은 「아무 문자열」이라 **오타를 막을 방법이 원리상 없다.**
- ★★ 앞 배치가 이미 실측해 둔 것을 **다시 재지 않고 인용한다** —\
  Rust 와의 진짜 축은 「정의 자리냐 사용 자리냐」가 아니라 「**모양이냐 이름이냐**」이고, **둘 다 양쪽에서 막는다**\
  ([**20번 주제**](../20-generic-constraints-and-defaults/) 6절).\
  `keyof` 는 그중 **모양 쪽의 극단**이다 — **이름을 선언하지 않고 모양에서 키 목록을 뽑아낸다.**

비용 — 없음(대비 관찰이다).

### (8) `--strict` 대조와 표시 순서

**언제 쓰나** — 「이 결론이 설정에 달렸나」와 「이 글자를 근거로 써도 되나」를 정할 때.

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.22a.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.22b.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.22c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.22d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.22e.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.22a.ts    5회 md5 가짓수 1
ex.24a.ts    5회 md5 가짓수 1
ex.25b.ts    5회 md5 가짓수 1
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **다섯 파일 전부 `--strict` 를 꺼도 한 글자도 같다.** `keyof` 와 `T[K]` 는 **플래그를 안 탄다.**
- ★★ 이것이 [**21번 주제**](../21-inference-control-const-and-noinfer/)와 **다른 점**이다 — 거기서는 여섯 중 하나가 갈렸다.\
  **「추론」은 플래그를 타고 「타입 연산」은 안 탄다**는 것이 이 배치의 관찰이다.
- ★★ 같은 명령을 **5회** 돌려 md5 **가짓수가 1** 이었다. **키 유니온의 표시 순서가 안 흔들렸다.**
- ★★★ 그래도 **관찰이지 보장이 아니다.** 실측에서 사전순으로 보이지만\
  **「사전순으로 정렬된다」고 적지 마라** — 그것을 약속한 문서를 읽지 않았다.

비용 — 없음.

## 문법 — 형태와 규칙

```text
형태 -- 이 주제에서 던진 것

  keyof T                       키의 유니온                       (TS 2.1)
  T[K]                          그 키의 값 타입                   (TS 2.1)
  T[keyof T]                    값 타입 전부
  T[number]                     배열·튜플의 원소 타입
  (typeof v)[number]            값에서 원소 타입까지 한 줄
  keyof typeof v                값의 키 목록                      (23번과 만나는 자리)
  <T, K extends keyof T>(o: T, k: K): T[K]     ★ 키 안전 접근 관용구

  ★ 탐침의 조수
  keyof T & {}                  별칭 이름 대신 펼쳐 찍게 만든다   (구현 층)
```

```text
금지 사례 -- 이 주제에서 던져 받은 것 셋. 전문은 「동작 방식」의 블록에 있다.

  1) 배열에 문자열 인덱스 키    ->  TS2322  '"0"' is not assignable to type 'keyof string[]'
  2) 없는 키로 인덱스 접근      ->  TS2339  Property '없는키' does not exist on type 'User'
  3) 없는 키를 인자로           ->  TS2345  Argument of type '"없는키"' is not assignable to
                                            parameter of type 'keyof User'
```

**규칙 불릿**

- ★★★ **`keyof T` 는 키의 유니온이다** — 값이 아니라 타입이다(1절 8행).
- ★★★ **문자열 인덱스 시그니처가 있으면 `keyof` 가 `string | number` 가 된다**(1절 13행) — ★ 숫자 인덱스면 **`number`** 다(18행).
- ★★★ **인덱스 시그니처는 이름 있는 키를 삼킨다** — `"fixed"` 가 목록에서 사라진다(1절 24·25행).
- ★★ **유니온의 `keyof` 는 교집합, 교차의 `keyof` 는 합집합**이다(1절 39·40행). **방향이 뒤집힌다.**
- ★★ **`keyof any` 는 `string | number | symbol`**, **`keyof unknown` 은 `never`**(1절 27·28행).
- ★★★ **배열의 `keyof` 에는 메서드 이름과 `length` 가 전부 들어간다** — `number` 만이 아니다(2절).
- ★★ **배열 인덱스 키는 `number` 이지 `"0"` 이 아니다**(2절 9행). **튜플은 `"0"` 을 갖는다**(4행).
- ★★★ **`keyof` 는 `public` 만 본다** — `private`·`protected`·`#` 이 빠지고 **메서드는 들어간다**(3절 15·22행).
- ★★ **`keyof typeof Class` 는 정적 쪽이고 `"prototype"` 이 낀다**(3절 16행).
- ★★★ **`as const` 는 키가 아니라 값을 굳힌다**(3절 26\~29행).
- ★★ **`T[K]` 의 `K` 는 `keyof T` 에 들어야 한다** — 아니면 `TS2339`(4절 10행).
- ★★★ **`K extends keyof T` 라야 값 타입이 하나로 좁는다** — `k: keyof T` 는 값 전체를 준다(5절 12·18행).
- ★★ **`--strict` 를 꺼도 결과가 한 글자도 안 바뀐다**(8절).
- ★ **`.d.ts` 는 `keyof` 를 계산하지 않는다** — 적은 그대로 남긴다(6절).

## 어디서 틀리나

- ★★★ 「**`keyof T` 를 탐침에 넣으면 목록이 보이겠지**」 — **안 보인다.** tsc 가 **별칭 이름을 되돌려 준다**(1절 7행). **`& {}` 를 붙여야** 펼쳐진다.
- ★★★ 「**인덱스 시그니처가 있어도 이름 있는 키는 남겠지**」 — **삼켜진다**(1절 24·25행). `"fixed"` 가 사라진다.
- ★★★ 「**배열의 `keyof` 는 `number` 겠지**」 — **메서드 이름이 전부 들어간다**(2절 3행).
- ★★ 「**배열 인덱스니까 `"0"` 도 되겠지**」 — **안 된다**(2절 9행). 단 **튜플은 된다**(4행).
- ★★★ 「**`as const` 를 붙여야 키가 리터럴이 되겠지**」 — **키는 원래 리터럴**이다. 갈리는 것은 **값**이다(3절 26\~29행).
- ★★ 「**`keyof Class` 에 `static` 이 들어가겠지**」 — **안 들어간다.** 정적 쪽은 `keyof typeof Class` 다(3절 15·16행).
- ★★ 「**`keyof` 에 `private` 도 보이겠지**」 — **안 보인다.** TS 의 `private` 도 JS 의 `#` 도 똑같이 빠진다(3절 15·22행).
- ★★★ 「**`k: keyof T` 로 받아도 값 타입이 좁겠지**」 — **안 좁는다.** `string | number | boolean` 이 돌아온다(5절 18행).
- ★★ 「**유니온의 `keyof` 는 키의 합집합이겠지**」 — **교집합**이다(1절 39행). 교차 쪽이 합집합이다.
- ★★ 「**`keyof unknown` 은 `string | number | symbol` 이겠지**」 — **`never`** 다(1절 28행). 그쪽은 **`keyof never`** 다(29행).
- ★ 「**타입 자리에서는 오타가 조용히 넘어가겠지**」 — `T["없는키"]` 는 **`TS2339`** 다(4절 10행).
- ★ 「**`.d.ts` 를 보면 계산 결과가 나오겠지**」 — **안 나온다**(6절).

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 tsc 가 보여 주는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(2.1)** | `keyof T` 가 **키의 유니온**이고 `T[K]` 가 **그 키의 값 타입**이다 | 1·4절 |
| **언어 보장** | 인덱스 시그니처가 `keyof` 를 **`string \| number`**(문자열) · **`number`**(숫자)로 만든다 | 1절 13·18행 |
| **언어 보장** | `keyof` 는 **`public` 표면만** 본다 | 3절 15·22행 |
| **언어 보장** | 유니온은 **교집합**, 교차는 **합집합** | 1절 39·40행 |
| **★ 구현(tsc 7.0.2)** | ★★★ `keyof User` 를 **별칭 이름으로 찍는 것** — `& {}` 가 펼치게 만든다 | 1절 7·8행 — **표시의 문제다** |
| **★ 구현(tsc 7.0.2)** | ★★ 긴 유니온을 **`... 18 more ...`** 로 자르는 것 | 2절 3·4행 |
| **★ 구현(tsc 7.0.2)** | 진단 **문구** 전문 | 코드(`TS2322`·`TS2339`·`TS2345`)가 더 오래 간다 |
| **★ 이 판의 관찰** | 키 유니온의 **표시 순서**(사전순으로 보인다) | 8절 — 5회 md5 가짓수 1. **보장이 아니다** |
| **★ 이 판의 관찰** | 배열의 `keyof` 에 **`unique symbol` 이 끼는 것** | 2절 3행 — `lib` 판에 달렸다 |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 같다** | 8절 |
| **★ 부적용 — 3창(`.js`)** | ★★ **잴 것이 없다** — 전부 타입 층이다 | 이 문서에 `.js` 블록이 **없다** |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — 계산하지 않는다 | 6절 |
| **안 잰 것** | 거대한 키 유니온의 **검사 시간**·메모리 | **재지 않았다** |
| **안 잰 것** | `keyof` 가 **매핑 타입**·**템플릿 리터럴**과 만나는 자리 | 목록의 **26번 주제**·**27번 주제** |

★★ **이 주제는 「언어 보장」 칸이 두껍다** — [**21번 주제**](../21-inference-control-const-and-noinfer/)와 정반대다.
`keyof` 는 **규칙이 정해져 있고** 추론처럼 자리마다 달라지지 않는다.
구현 층으로 빠지는 것은 대부분 「**어떻게 보여 주느냐**」다.

## 언제 쓰고 언제 안 쓰나

| `keyof` 를 쓴다 | 안 쓴다 |
|---|---|
| **키가 컴파일 타임에 알려진** 접근 함수(설정 읽기·폼 필드·컬럼 이름) | 키가 **런타임 문자열**로 들어오는 자리 — 좁히기가 따로 필요하다 |
| 그 타입에 **인덱스 시그니처가 없을 때** | 인덱스 시그니처가 있으면 `keyof` 가 **`string \| number`** 로 무너진다(1절) |
| **오타를 컴파일 타임에 죽이고** 싶을 때(5절 13행) | 키 목록이 **자주 바뀌는데** 호출부가 많을 때 — 전부 깨진다 |
| `as const` 객체에서 **값 타입까지** 뽑아야 할 때(3절 28행) | 배열에서 **원소만** 필요할 때 — `T[number]` 로 충분하다(4절) |

| `T[K]` 를 쓴다 | 안 쓴다 |
|---|---|
| 키와 값의 **짝을 타입으로 묶을** 때(5절 `setTight`) | 값 타입에 **이름이 있을 때** — 그 이름을 쓰는 쪽이 읽기 쉽다 |
| 배열·튜플의 **원소 타입**(`T[number]`) | `T` 가 자주 바뀌고 **그 자리만 고정하고 싶을** 때 |
| **중첩**을 한 줄로 가리킬 때(`A["b"]["c"]`) | 중첩이 세 단계를 넘을 때 — 중간 타입에 이름을 준다 |

## 핵심 문장

1. **`keyof` 는 키를 값이 아니라 타입으로 만든다** — `Object.keys` 와 만나지 않는다.
2. **인덱스 시그니처 하나가 `keyof` 를 통째로 무너뜨린다** — 이름 있는 키까지 삼킨다.
3. **배열의 `keyof` 에는 메서드 이름이 전부 들어간다** — 인덱스만 쓰려면 `T[number]` 다.
4. **`keyof` 는 `public` 만 본다** — 메서드는 들어가고 `private`·`#`·`static` 은 빠진다.
5. **`as const` 는 키가 아니라 값을 굳힌다** — 갈리는 자리는 `T[keyof T]` 다.
6. **안전해지는 것은 `keyof` 가 아니라 `K` 를 하나로 묶는 것**이다 — `K extends keyof T`.
7. **탐침이 별칭 이름을 되돌려 주면 `& {}` 로 펼친다** — 그것은 tsc 의 표시 방식이다.

## 관련 자료

- [**20번 주제** — 제네릭 제약과 기본 타입 인자](../20-generic-constraints-and-defaults/) — ★★★ **README 가 지정한 선행.**
  그쪽 2절이 `get(obj, key)` 관용구를 **제약 쪽에서** 다루고, 여기 5절은 **`keyof` 쪽에서** 다시 본다.
  그쪽은 **왜 제약이 필요한가**까지, 여기는 **`keyof` 가 무엇으로 펼쳐지나**부터.
- [**24번 주제** — 조건부 타입과 분배](../24-conditional-types-and-distribution/) — ★★★ **사슬의 다음 칸.**
  여기서 만든 **키 유니온**이 거기서 **분배된다.** 1절 28행의 「탐침이 조용한 `never`」도 거기서 창을 바꾼다.
- [**25번 주제** — `infer` 와 재귀 조건부 타입](../25-infer-and-recursive-conditional-types/) — ★★★ **사슬의 급소.**
  `T[number]` 로 꺼내던 것을 `infer` 로 **이름 붙여** 꺼낸다.
- [**23번 주제** — `typeof` 타입 연산자](../23-typeof-type-operator/) — ★★ **사슬이 아니라 직교하는 축**이다(값 공간 / 타입 공간).
  `keyof typeof x` 에서 **딱 한 번 만난다**(3절 16행 · 4절 17행). `typeof Class` 가 생성자라는 규칙은 그쪽이 정본이다.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — **인덱스 시그니처의 정본.**
  그쪽은 **무엇을 선언하는가**까지, 여기는 **그것이 `keyof` 를 어떻게 넓히는가**부터.
- [**11번 주제** — 리터럴 타입과 `as const`](../11-literal-types-and-as-const/) — **`as const` 의 정본.**
  그쪽은 **리터럴이 언제 넓어지나**까지, 여기는 **그 결과가 `T[keyof T]` 에서 어떻게 갈리나**부터.
- [**09번 주제** — 유니온 타입](../09-union-types/) · [**10번 주제** — 인터섹션 타입](../10-intersection-types/) — 1절 39·40행의 **방향이 뒤집히는 이유**는 그쪽이 정본이다.
- [**19번 주제** — 제네릭 기본](../19-generics-basics/) — 5절의 `K` 가 **호출마다 채워지는** 기제는 그쪽.
- 목록의 **26번 주제**(매핑 타입) — `in keyof` 로 **키를 돌며 새 타입을 만드는** 자리. 여기는 **읽기**까지만.
- 목록의 **27번 주제**(템플릿 리터럴 타입) — 2절 11행의 `` `${keyof T & string}` `` 가 그쪽 정본.
- 목록의 **28번 주제**(유틸리티 타입) — `Pick`·`Omit`·`Record` 가 전부 `keyof` 로 만들어진다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번**([타입 소거 — 런타임에 없는 것·제네릭 배열 금지·브리지 메서드](../../../java/syntax/19-type-erasure/)) — 7절의 대비.
  **Java 의 키는 값이고 TS 의 키는 타입이다.**
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번**([제네릭 선언 — 타입 파라미터·바운드·제네릭 메서드](../../../java/syntax/17-generic-declarations/)) — 5절의 `<T, K extends keyof T>` 에 **대응하는 것이 없다.**
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**([트레이트 정의·구현·기본 메서드·연관 타입](../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/)) — 「모양이냐 이름이냐」 축의 반대쪽.

## 용어 풀이

> **`keyof`** — 타입의 **키를 유니온 타입으로** 뽑는 연산자(TS 2.1).\
> 예: `keyof { id: number; name: string }` 은 `"id" | "name"` 이다. **값이 아니라 타입이다.**

> **인덱스 접근 타입(indexed access type)** — `T[K]` 로 **키 `K` 의 값 타입**을 꺼내는 표기(TS 2.1).\
> 예: `User["id"]` 는 `number`. 점 표기(`User.id`)는 타입 자리에서 안 된다.

> **인덱스 시그니처(index signature)** — `[k: string]: V` 처럼 **키 이름 없이 값 타입만** 정한 선언.\
> 예: `{ [k: string]: number }`. 이것이 있으면 `keyof` 가 **`string | number`** 로 넓어진다.

> **키 안전 접근(key-safe access)** — `<T, K extends keyof T>(o: T, k: K): T[K]` 관용구.\
> 예: `getTight(user, "name")` 이 `string` 을 돌려준다. **키가 값 타입을 정한다.**

> **탐침(probe)** — 일부러 틀린 주석 `const p: null = …` 을 달아 **컴파일러가 타입을 말하게** 하는 수.\
> 예: `TS2322: Type '"id" | "name"' is not assignable to type 'null'.` 에서 왼쪽을 읽는다.

> **`& {}` 조수** — 탐침이 **별칭 이름을 되돌려 줄 때** 교차로 만들어 **펼쳐 찍게** 하는 수.\
> 예: `keyof User` 는 메아리이고 `keyof User & {}` 는 `"active" | "id" | "name"` 이다. **tsc 의 표시 방식에 기댄 수다.**

> **제5의 상태** — 창이 **답을 주긴 하는데 전부를 안 줄** 때 **창을 바꿔 물은 사실**을 적는 것.\
> 예: 2절 — 2창이 목록을 잘라서 1창(멤버십 대입)으로 낱낱이 물었다.

> **멤버십 대입(1창)** — `const k: keyof T = "…";` 으로 **그 값이 그 타입에 드느냐**만 묻는 수.\
> 예: `const k: keyof string[] = "map";` 이 조용하면 `"map"` 이 키라는 뜻이다.

> **`as const`** — 리터럴의 **속을 리터럴 타입으로 굳히고 `readonly` 를 붙이는** 단언(TS 3.4).\
> 예: `{ 가: 1 } as const` 의 값 타입은 `number` 가 아니라 `1` 이다.

> **`unique symbol`** — 한 선언에 묶인 **고유한 심볼 타입**.\
> 예: 배열의 `keyof` 끝에 붙어 나오는 것이 `Symbol.iterator` 같은 **잘 알려진 심볼** 키다.

## 더 들어가면

- **왜 `keyof` 가 `Object.keys` 와 안 맞나** — `Object.keys(o)` 의 반환은 **`string[]`** 이지 `(keyof T)[]` 가 아니다.
  **구조적 타이핑 때문**이다 — `o` 에는 선언에 없는 키가 더 있을 수 있고([**05번 주제**](../05-structural-typing/)),
  런타임에 그것도 `keys` 에 나온다. **타입이 약속한 것보다 값이 더 많을 수 있다**는 사실이 그 자리를 막는다.
  ★ 이 배치에서는 **안 던졌다** — 여기서는 `keyof` 쪽만 봤다.
- **1절 24행이 왜 그렇게 되나** — `keyof Mixed` 는 개념적으로 `"fixed" | string | number` 인데,
  **`"fixed"` 는 `string` 의 부분 집합**이라 유니온이 **흡수**한다. 같은 일이 `"id" | string` 에서도 일어난다.
  ★★ 그래서 **인덱스 시그니처를 넣는 순간 이름 있는 키의 리터럴성이 전부 죽는다.**
  키 안전 접근이 목적이면 **인덱스 시그니처를 넣지 않는 것**이 유일한 수다.
- **`& {}` 가 왜 펼치게 만드나** — tsc 는 타입을 찍을 때 **그 타입에 붙은 별칭·연산 이름을 우선** 쓴다.
  `keyof User` 는 그 이름을 갖고 있지만 `keyof User & {}` 는 **교차라서 그 이름이 없다** — 그래서 원소를 적는다.
  ★★★ **이것은 tsc 7.0.2 의 표시 방식이지 명세가 아니다.** 판이 오르면 다시 확인할 자리다.
  ★ 같은 목적에 `` `${keyof T & string}` ``(2절 11행)도 쓸 수 있지만 **문자열 키만** 남는다.
- **탐침이 `never` 를 못 읽는 문제** — 1절 28행이 그 자리다. `never` 는 **모든 타입에 할당**되므로 `null` 탐침이
  침묵한다. **「진단이 없다」와 「never 다」가 같은 얼굴**이다.
  ★ [**24번 주제**](../24-conditional-types-and-distribution/)가 `IsNever<T>` 로 **창을 바꿔** 그 자리를 연다 — 사슬이 이어지는 이유 중 하나다.
- **배열의 `keyof` 가 판을 타는 자리** — 2절 3행의 목록은 **`lib` 설정이 정한다.** `es2022` 로 던졌으니
  `at`·`flat`·`flatMap` 이 들어 있다. `--target` 을 낮추면 **그 이름들이 빠진다.**
  ★ 이 배치에서는 **`es2022` 한 판만 던졌다** — 다른 `lib` 로는 **안 돌려 봤다.**
- **`keyof` 로 만든 API 의 수명** — 5절의 관용구는 **타입의 `public` 표면을 계약으로 굳힌다.**
  그 표면이 바뀌면 호출부가 **전부 컴파일 에러**로 드러난다 — 그것이 값이자 대가다.
  ★ 그래서 **내부 구현 타입에 `keyof` 를 걸지 말고**, 공개 계약 타입에만 거는 편이 낫다.
