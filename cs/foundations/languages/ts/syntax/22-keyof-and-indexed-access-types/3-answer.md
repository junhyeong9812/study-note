# ts/syntax/22 — `keyof` 와 인덱스 접근 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출물은 `tsc` **7.0.2** 에서 실제로 얻었다. Java 블록은 `javac` **21.0.5** 다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 6번은 **진단이 0줄인 것이 결론**이다. 그 블록도 **명령과 종료 코드까지** 캡처했다.\
> ★★★ `const p: null = null as unknown as X;` 는 **탐침**이다 — 일부러 틀린 주석을 달아 컴파일러가 타입을 말하게 한다.\
> ★★ 이 문서의 `TS2322` 는 대부분 **에러가 아니라 출력**이다. 단 2번 9행·4번 10행·5번 13·29행은 **진짜 에러**이고 그것이 답이다.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.\
> ★★ 표 안의 `\|` 는 이스케이프다 — **뜻은 `|` 다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 탐침이 메아리를 돌려준다 — `& {}` 를 붙여야 펼쳐진다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 7 | `keyof User` | ★★★ **`keyof User`** — 메아리다. 펼쳐 주지 않는다 |
| 8 | ★★★ `keyof User & {}` | **`"active" \| "id" \| "name"`** |
| 13 | `keyof StringDict`(문자열 인덱스) | ★★★ **`string \| number`** — README 가 지정한 과녁 |
| 18 | `keyof NumberDict`(숫자 인덱스) | **`number`** — `string` 이 안 낀다 |
| 24·25 | `keyof Mixed` · 그 펼친 것 | ★★★ **`string \| number`** — **`"fixed"` 가 사라졌다** |
| 27 | `keyof any` | **`string \| number \| symbol`** |
| 28 | ★★★ `keyof unknown` | **진단이 없다** = **`never`** |
| 29 | `keyof never` | **`string \| number \| symbol`** — `keyof any` 와 같다 |
| 39 | ★★ `keyof (A \| B)` | **`"shared"`** — 키의 **교집합** |
| 40 | ★★ `keyof (A & B)` | **`"shared" \| "x" \| "y"`** — 키의 **합집합** |

- ★★★ **7행과 8행이 이 문항의 전부다.** 소스는 `& {}` 하나만 다른데 한쪽은 **이름**을, 한쪽은 **내용물**을 준다.\
  tsc 는 타입을 찍을 때 **그 타입에 붙은 연산 이름을 우선** 쓴다. `keyof User & {}` 는 **교차라서 그 이름이 없어** 원소를 적는다.\
  ★★ **이것은 명세가 아니라 tsc 7.0.2 의 표시 방식이다.** 「구현 층」에 적어야 한다.
- ★★★ 13행이 과녁이다. **문자열 인덱스 시그니처**가 있으면 `keyof` 가 **`string | number`** 다.\
  `number` 가 끼는 이유는 JS 에서 **`o[0]` 이 `o["0"]`** 이기 때문이다 — 숫자 키도 문자열 인덱스에 걸린다.
- ★★ 18행이 그 짝이다. **숫자 인덱스만** 있으면 **`number`** 뿐이다. **방향이 한쪽으로만 넓어진다.**
- ★★★ 24·25행이 가장 아프다. `Mixed` 에는 **`fixed` 라는 이름 있는 키가 있는데도** 답이 `string | number` 다.\
  `"fixed"` 는 **`string` 의 부분 집합**이라 유니온이 **흡수**한다 — `"fixed" | string` 은 그냥 `string` 이다.\
  ★★ **인덱스 시그니처 한 줄이 이름 있는 키의 리터럴성을 전부 죽인다.**
- ★★★ 28행이 **조용하다.** `keyof unknown` 은 **`never`** 이고 `never` 는 **`null` 에도 할당**되므로\
  탐침이 말할 거리가 없다. **「진단 없음」과 「`never`」가 같은 얼굴**이다 — 탐침의 사각지대다(9번).
- ★★ 29행이 그 정반대다. `keyof never` 는 **`string | number | symbol`** 로 `keyof any` 와 **같다.**\
  ★ 「`never` 니까 키도 없겠지」가 **틀린다.**
- ★★★ 39·40행에서 **방향이 뒤집힌다.** `A | B` 는 **둘 중 무엇인지 모르므로 양쪽에 다 있는 키만** 안전하고,\
  `A & B` 는 **둘 다이므로 어느 쪽 키든** 안전하다.

### 2. ★★★ 배열의 `keyof` 에는 메서드 이름이 전부 들어간다 — 그리고 `"0"` 은 안 든다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 2 | `keyof string[]` | **`keyof string[]`** — 또 메아리다 |
| 3 | ★★★ 그 펼친 것 | **`number`** + 메서드 이름 다수 + **`... 18 more ...`** + **`unique symbol`** |
| 4 | ★★ `keyof [1, 2]`(튜플) | 3행에 더해 **`"0"` 과 `"1"`** 이 앞머리에 있다 |
| 6·7·8 | `0` · `"length"` · `"map"` | ★ **전부 조용하다** = 전부 키다 |
| 9 | ★★★ `"0"` | **`TS2322`** — 「Type '"0"' is not assignable to type 'keyof string[]'.」 |
| 11 | 템플릿 리터럴로 문자열 키만 | **`number` 와 `unique symbol` 이 빠진** 메서드 이름들 |

- ★★★ 3행에서 **2창이 목록을 잘랐다**(`... 18 more ...`). 답을 주긴 했는데 **전부를 안 줬다.**\
  ★★ 이것이 **제5의 상태**다 — 「못 잰 것」도 「부적용」도 아니라 **창을 바꿔 물은 것**이다.\
  그래서 6\~9행에서 **1창**(멤버십 대입)으로 낱낱이 물었다.\
  ★ **바꾼 창이 못 보는 것** — 전체 목록은 여전히 모른다. **물어본 것만** 안다.
- ★★★ 6·7·8행이 **조용하다**. `0` 도 `"length"` 도 `"map"` 도 `keyof string[]` 에 **든다.**\
  「배열의 키는 인덱스뿐」이 **틀렸다** — **프로토타입의 메서드 이름까지 전부 키다.**
- ★★★ 9행이 **경계**다. **`"0"`(문자열)은 안 든다.** 배열의 인덱스 키는 **`number`** 이지 `"0"` 이 아니다.\
  ★★ 1절 13행의 **문자열 인덱스 시그니처와 정반대**다 — 그쪽은 `string | number` 둘 다였다.
- ★★ 4행 — **튜플은 길이가 고정**이라 자리 이름이 **리터럴 `"0"`·`"1"`** 로 산다.\
  **배열과 튜플이 여기서 갈린다.**
- ★ 11행 — `` `${keyof T & string}` `` 로 씌우면 **문자열 키만** 남는다. 필요한 쪽만 거르는 수다.
- ★★ 3행 끝의 **`unique symbol`** 은 `Symbol.iterator` 같은 **잘 알려진 심볼** 키다.\
  ★ 그 목록은 **`lib` 판이 정한다** — `es2022` 로 던졌다. 다른 `lib` 로는 **안 돌려 봤다.**

```text
  배열과 튜플 -- 인덱스 키의 꼴이 다르다

     keyof string[]     number | "at" | "concat" | ... | "length" | ... | unique symbol
                        ▲                                                ▲
                        └ 인덱스는 number 다 ("0" 이 아니다)              └ 잘 알려진 심볼

     keyof [1, 2]       number | "0" | "1" | "at" | ... | unique symbol
                                 ▲     ▲
                                 └─────┴ 길이가 고정이라 자리 이름이 리터럴로 산다
```

### 3. ★★★ `keyof` 는 `public` 만 본다 · `as const` 는 키가 아니라 값을 굳힌다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 15 | `keyof Account` | ★★★ **`"balance" \| "id" \| "label"`** — 메서드는 들고 `private`·`protected`·`static` 은 빠진다 |
| 16 | `keyof typeof Account` | ★★★ **`"bank" \| "make" \| "prototype"`** — 정적 쪽 + **`"prototype"`** |
| 22 | `keyof Hash`(`#` 필드) | **`"shown"`** — `#hidden` 이 안 보인다 |
| 26·27 | `as const` 객체 · 평범한 객체의 키 | ★★★ **둘 다 `"가" \| "나"`** — **같다** |
| 28 | `as const` 객체의 값 | ★★★ **`1 \| 2`** |
| 29 | 평범한 객체의 값 | ★★★ **`number`** — 여기서 갈린다 |

- ★★★ 15행에서 **`balance` 가 들어갔다.** 「필드만 키가 된다」가 **틀렸다** —\
  `public` 이면 **메서드 이름도 키**다. 2번의 배열에서 `"map"` 이 들어간 것과 **같은 이유**다.
- ★★ `private secret`·`protected note` 는 빠졌다. **`keyof` 는 접근 가능한 표면만 본다.**
- ★★ `static bank`·`static make` 도 빠졌다. **정적 멤버는 인스턴스 타입에 아예 없다.**
- ★★★ 16행이 그 짝이다. `typeof Account` 는 **생성자 타입**이라 정적 쪽이 나오고,\
  거기에 **`"prototype"`** 이 끼어 있다 — 생성자 함수가 실제로 가진 프로퍼티다.\
  ★ `typeof Class` 가 왜 생성자인지는 [**23번 주제**](../23-typeof-type-operator/)가 정본이다.\
  **직교하는 축이 여기서 딱 한 번 만난다.**
- ★★ 22행 — JS 의 진짜 private 인 `#hidden` 도 **안 보인다.**\
  TS 의 `private` 는 소거되고 `#` 는 런타임에 강제되는데(목록의 **32번 주제**), **`keyof` 에서는 똑같이 빠진다.**
- ★★★ 26·27행이 **뜻밖의 자리**다. `as const` 를 붙이나 안 붙이나 **키는 똑같이 `"가" | "나"`** 다.\
  ★★ 「`as const` 를 붙여야 키가 리터럴로 산다」가 **틀렸다** — **객체 리터럴의 키는 원래 리터럴**이다.
- ★★★ 28·29행이 **진짜 갈리는 자리**다. `T[keyof T]` 가 **`1 | 2`** 대 **`number`** 로 갈린다.\
  **`as const` 의 값은 `keyof` 쪽이 아니라 `T[keyof T]` 쪽에 있다.**

### 4. ★★ `T[K]` — 대괄호는 유니온도 받고 이어 붙기도 한다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 7 | `User["id"]` | **`number`** |
| 8 | `User["id" \| "name"]` | **`string \| number`** — 키를 유니온으로 주면 값도 유니온 |
| 9 | ★★ `User[keyof User]` | **`string \| number \| boolean`** — 값 타입 전부 |
| 10 | ★★★ `User["없는키"]` | **`TS2339`** — 「Property '없는키' does not exist on type 'User'.」 |
| 13 | `Tup[0]` | **`"가"`** |
| 14 | `Tup[number]` | **`"가" \| "나"`** |
| 17 | ★★★ `(typeof list)[number]` | **`string`** |
| 22 | `Nested["inner"]["deep"]` | **`boolean`** — 대괄호가 이어 붙는다 |

- ★★ 7행 — **점 표기가 아니라 대괄호**다. `User.id` 는 **값 공간의 문법**이라 타입 자리에서 안 된다([**23번 주제**](../23-typeof-type-operator/)).
- ★★ 8행 — 키에 **유니온**을 주면 값도 **유니온**으로 나온다. 9행은 그 극한이다.
- ★★★ 10행이 **이 문항의 유일한 진짜 에러**다. **타입 자리에서도 오타가 잡힌다** — `TS2339` 다.\
  ★ 열이 **47** 인 것은 `"없는키"` 가 시작하는 자리다. `(행,열)`은 안 흔들리는 칸이다.
- ★★ 13·14행 — 튜플은 **자리 번호**로도 **`number`** 로도 꺼낸다. 2번 4행에서 본 대로\
  **튜플은 `"0"`·`"1"` 을 키로 갖기** 때문에 `Tup[0]` 이 성립한다.
- ★★★ 17행이 **가장 쓸모 있는 관용구**다. **값에서 시작해 원소 타입까지 한 줄**로 간다.\
  ★ **괄호가 필요하다** — `typeof list[number]` 라고 쓰면 `typeof (list[number])` 로 읽힌다.\
  [**23번 주제**](../23-typeof-type-operator/)의 `typeof` 와 이 주제의 `[number]` 가 합쳐진 꼴이다.
- ★ 22행 — 중첩은 **대괄호를 이어 붙인다.** 세 단계를 넘으면 중간 타입에 이름을 주는 편이 읽기 낫다.

### 5. ★★★ `K extends keyof T` 라야 값이 하나로 좁는다 — 세 단계가 갈린다

**출력**

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

**왜 그런가**

| 줄 | 자리 | 답 |
|---|---|---|
| 12 | ★★★ `getTight(u, "name")` — `K extends keyof T` | **`string`** — 딱 그 키의 값 |
| 13 | 없는 키를 인자로 | **`TS2345`** — 진단에 **`'keyof User'`** 가 찍힌다 |
| 18 | ★★★ `getLoose(u, "name")` — `k: keyof T` | **`string \| number \| boolean`** — 값 전체 |
| 23 | `getWide(…, "없는키")` — `k: string` | **`unknown`** — 아무것도 안 남는다 |
| 28 | `setTight(u, "id", 2)` | ★ **조용하다** = 통과 |
| 29 | ★★★ `setTight(u, "id", "둘")` | **`TS2345`** — 「Argument of type 'string' is not assignable to parameter of type 'number'.」 |

- ★★★ 12행과 18행이 이 문항의 급소다. **같은 `keyof` 를 쓰는데 답이 다르다.**\
  ①은 `K` 가 **호출마다 `"name"` 이라는 리터럴로 굳으므로** `T[K]` 가 **`string`** 하나다.\
  ②는 `k` 가 **`keyof T` 전체**이므로 돌아오는 값도 **전체**다 — **어느 키였는지 안 남는다.**
- ★★ 그러므로 안전해지는 것은 `keyof` 가 아니라 「**`K` 를 하나로 묶는 것**」이다.\
  `keyof` 는 **거르기**만 하고, **정밀도는 제네릭 `K` 가 만든다**([**20번 주제**](../20-generic-constraints-and-defaults/) 2절 · [**19번 주제**](../19-generics-basics/)).
- ★★ 23행이 바닥이다. `k: string` 이면 **오타도 안 잡히고 값 타입도 `unknown`** 이다. **둘 다 잃는다.**
- ★★★ 13행 — 오타가 **컴파일 타임에 죽는다.** 진단이 **허용되는 타입까지 찍어 준다.**\
  ★ 여기서는 `'keyof User'` 라는 **이름**으로 찍혔다 — 1번 7행과 같은 「메아리」다.\
  펼쳐 보려면 역시 `& {}` 가 필요하다.
- ★★★ 29행이 **쓰기 쪽의 값**이다. `setTight` 는 키와 값이 **같은 `K` 로 묶여** 있어서\
  `"id"` 에 `"둘"` 을 넣으면 죽는다. 28행(`2`)은 통과한다 — **짝이 맞기 때문**이다.

```text
  세 단계 -- 같은 obj[key] 인데 돌아오는 타입이 다르다

  ① K extends keyof T     getTight(u, "name")   ->  string
                                                     ★ 키가 값 타입을 정한다
  ② k: keyof T            getLoose(u, "name")   ->  string | number | boolean
                                                     ★ 어느 키였는지 안 남는다
  ③ k: string             getWide(u, "없는키")  ->  unknown
                                                     ★ 오타도 안 잡고 타입도 없다
```

### 6. ★★★ `.d.ts` 는 계산하지 않는다 — 다섯째 창을 닫는 근거

**출력**

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

**왜 그런가**

- ★★★ 종료 코드가 **`0`** 이고 진단이 **0줄**이다. **그 침묵도 블록으로 캡처했다** —\
  명령과 `(tsc exit=0)` 까지 들어 있어야 **다시 던질 수 있고**, 「안 물어본 것」과 구분된다.
- ★★★ `Keys` 가 **`keyof User`** 로 **적은 그대로** 남았다. `"id" | "name"` 으로 **안 펼쳐진다.**
- ★★ `oneKey` 도 **`keyof User`** 다. **값의 타입인데도 계산하지 않는다.**
- ★★ `Cond` 도 **`string extends string ? "가" : "나"`** 그대로다. 결과가 뻔한데도 **한쪽으로 안 접힌다**([**24번 주제**](../24-conditional-types-and-distribution/)).
- ★★ `Elem` 도 **`(typeof frozen)[number]`** 그대로다.
- ★★★ 그러므로 **5창은 이 주제에 부적용**이다 — 「재 봤더니 같았다」가 아니라 **잴 것이 없다.**\
  **`.d.ts` 는 「무엇이 선언됐나」를 말하지 「무엇이 계산되나」를 말하지 않는다.**
- ★★ **단 `frozen` 한 줄만 다르다** — `readonly ["가", "나"]` 로 **추론 결과가 적혀 있다.**\
  ★★★ 그 경계가 이 블록의 값이다 — **추론은 적어 주고 타입 수준 계산은 안 해 준다.**\
  앞 배치가 「`.d.ts` 는 계산하지 않는다」고 판정한 것을 **이 판에서 다시 확인**한 셈이다.
- ★ 앞 배치의 다른 근거(「`.d.ts` 가 글자를 바꾼다 — `const` 초기자만 한글을 이스케이프한다」)는\
  **여기서는 안 던졌다.** 이 블록에 한글이 `["가", "나"]` 로 **그대로** 나온 것은 그 자리가 아니기 때문이다.

### 7. ★★★ `"fixed" | string` 은 그냥 `string` 이다

**왜 그런가**

- 유니온은 **부분 집합을 흡수**한다. `"fixed"` 는 **`string` 의 부분 집합**이므로\
  `"fixed" | string` 은 **`string`** 으로 줄어든다. `1 | number` 가 `number` 인 것과 같다.
- `keyof Mixed` 는 개념적으로 **`"fixed" | string | number`** 인데 첫 항이 둘째에 먹혀 **`string | number`** 가 된다.
- ★★ 그래서 이것은 **`keyof` 의 특별한 규칙이 아니라 유니온의 일반 성질**이다([**09번 주제**](../09-union-types/)).
- ★★★ 실용적 함의 — **인덱스 시그니처를 넣는 순간 그 타입의 키 안전성이 통째로 죽는다.**\
  5번의 `getTight` 를 그런 타입에 쓰면 `K` 가 `string | number` 로 굳어 **아무 문자열이나 통과**한다.
- ★ 고치는 수는 **인덱스 시그니처를 안 넣는 것**뿐이다. 넣어야 한다면 키 목록을 **따로 `as const` 로 들고 있어야** 한다(3번).

```text
  흡수 -- keyof 의 규칙이 아니라 유니온의 성질이다

     "fixed" | string          ->  string        ★ 부분 집합이 먹힌다
     1 | number                ->  number        ★ 같은 일
     "id" | "name" | string    ->  string        ★ 여럿이어도 같다

     keyof Mixed = "fixed" | string | number  ->  string | number
```

### 8. ★★★ 「무엇인지 아느냐」가 방향을 정한다

**왜 그런가**

- `A | B` 인 값은 **A 인지 B 인지 모른다.** 그러므로 **양쪽에 다 있는 키만** 읽어도 안전하다 → **교집합**.
- `A & B` 인 값은 **둘 다이다.** 그러므로 **어느 쪽 키든** 읽어도 안전하다 → **합집합**.
- ★★ 즉 `keyof` 가 뒤집는 것이 아니라 **「안전하게 읽을 수 있는 키」의 정의가 그렇게 생겼다.**\
  1번 39·40행이 그 결과를 글자로 보여 준다.
- ★ 값 쪽 규칙과 나란히 놓으면 외우기 쉽다 — **유니온 값은 공통 멤버만 쓸 수 있다**([**09번 주제**](../09-union-types/)).\
  `keyof (A | B)` 가 교집합인 것은 **그 규칙을 타입 수준으로 옮긴 것**이다.
- ★★ 교차 쪽은 [**10번 주제**](../10-intersection-types/)가 정본이다 — 프로퍼티가 충돌하면 그 키의 값이 `never` 가 되는데,\
  **키 목록 자체는 그래도 합집합**이다. 이 배치에서는 **충돌하는 교차는 안 던졌다.**

### 9. ★★★ 탐침이 조용하면 `never` 다 — 창을 바꿔야 읽힌다

**왜 그런가**

- `never` 는 **모든 타입에 할당 가능**하다. 그래서 `const p: null = … as never` 는 **아무 진단도 안 낸다.**\
  1번 28행(`keyof unknown`)이 정확히 그 자리다.
- ★★★ 문제는 **「진단이 없다」가 두 가지를 뜻한다**는 것이다 —\
  ① 타입이 `never` 다 ② 애초에 그 줄이 틀리지 않았다. **탐침만으로는 못 가른다.**
- ★★ 그래서 창을 바꾼다. [**24번 주제**](../24-conditional-types-and-distribution/)에서 쓰는 수가 이것이다:

```text
  never 를 읽는 창 -- 조건부로 바꿔 물어본다

     type IsNever<T> = [T] extends [never] ? "never 다" : "never 가 아니다";

     const p: null = null as unknown as IsNever<keyof unknown>;
                                        └─ 결과가 문자열 리터럴이라 탐침이 말한다

     ★ [T] 로 감싸는 이유는 24번 주제의 분배 때문이다 -- 맨몸 T 로 쓰면 또 조용해진다.
     ★ 바꾼 창이 못 보는 것 -- "never 인가"만 답하지 "무엇인가"는 안 말한다.
```

- ★ 이 주제에서는 **그 창을 쓰지 않았다** — 1번 28행 하나뿐이라 **「조용하다」로 적고 넘겼다.**\
  ★★★ 사슬의 다음 칸([**24번 주제**](../24-conditional-types-and-distribution/))에서 `never` 가 **주제 자체**가 되므로 거기서 정식으로 연다.

### 10. ★★ 런타임 키에는 못 쓰고, 인덱스 시그니처 하나에 무너진다

**왜 그런가**

| 상황 | 무슨 일이 나나 | 근거 |
|---|---|---|
| 키가 **런타임 문자열**(`declare const k: string`) | `K` 가 `string` 으로 굳어 **`TS2345`** 로 막힌다 | [**20번 주제**](../20-generic-constraints-and-defaults/) 2절 15행 |
| 그 타입에 **문자열 인덱스 시그니처**가 있다 | `keyof` 가 **`string \| number`** 라 **아무 문자열이나 통과** | 1번 13·25행 |
| 그 타입에 **숫자 인덱스 시그니처**만 있다 | `keyof` 가 **`number`** — 이름 키는 아예 못 쓴다 | 1번 18행 |
| **배열**에 그냥 `keyof` 를 걸었다 | 메서드 이름이 **전부 딸려 온다** | 2번 3행 |
| 필드를 나중에 **`private` 로 내렸다** | 그 키를 쓰던 **호출부가 전부 깨진다** | 3번 15행 |

- ★★★ 첫 줄이 이 주제의 가장 큰 경계다. **`keyof` 는 「키가 컴파일 타임에 알려져 있을 때」만 값을 낸다.**\
  런타임 키를 받는 자리에는 **좁히기**나 **검증 함수**가 따로 필요하다([**13번 주제**](../13-type-guards-and-predicates/)).
- ★★ 둘째 줄이 **조용히 무너지는 자리**다 — **에러가 안 난다.** `getTight(dict, "오타")` 가 그냥 통과한다.\
  ★ 「타입을 걸었으니 안전하겠지」가 **가장 위험한 자리**다. 인덱스 시그니처가 있는지 **먼저 확인**하라.
- ★ 배열은 `T[number]` 로 충분한 경우가 많다(4번 14·17행) — **`keyof` 를 걸 이유가 대개 없다.**

### 11. ★★ 20 은 제약 쪽, 22 는 `keyof` 쪽 · 23 은 직교하는 축 · 24 는 사슬의 다음 칸

**왜 그런가**

| 주제 | 무엇이 정본인가 | 이 주제와의 경계 |
|---|---|---|
| [**20번**](../20-generic-constraints-and-defaults/) | **제약**(`extends`)이 무엇을 하나 · 왜 제약 없는 `T` 는 아무것도 못 하나 | 그쪽 2절이 `get(obj,key)` 를 **제약 쪽에서**, 여기 5번은 **`keyof` 쪽에서** |
| [**23번**](../23-typeof-type-operator/) | **값 공간 / 타입 공간**의 분리 · `typeof Class` 가 생성자인 것 | ★★ **사슬이 아니라 직교하는 축.** `keyof typeof x` 에서 **딱 한 번 만난다** |
| [**24번**](../24-conditional-types-and-distribution/) | 조건부 타입과 **분배** | 여기서 만든 **키 유니온**이 거기서 **분배된다.** 9번의 `never` 창도 거기서 연다 |
| [**25번**](../25-infer-and-recursive-conditional-types/) | `infer` 와 재귀 | `T[number]` 로 꺼내던 것을 **이름 붙여** 꺼낸다 |
| [**07번**](../07-object-type-details/) | 인덱스 시그니처를 **어떻게 선언하나** | 여기는 그것이 **`keyof` 를 어떻게 넓히나**부터 |
| [**11번**](../11-literal-types-and-as-const/) | `as const` 가 **리터럴을 언제 지키나** | 여기는 그 결과가 **`T[keyof T]` 에서 어떻게 갈리나**부터 |

- ★★★ **22 → 24 → 25 가 한 사슬이고 25 가 급소다.**\
  22 가 **키 유니온을 만들고**, 24 가 **그 유니온을 분배하고**, 25 가 **`infer` 로 되뽑는다.**
- ★★ **23 은 사슬에 안 낀다.** 「값에서 타입을 끌어오는」 다른 축이다.\
  다만 3번 16행(`keyof typeof Account`)과 4번 17행(`(typeof list)[number]`)이 **두 축이 교차하는 점**이다.

```text
  사슬과 직교하는 축

           22 keyof            24 조건부·분배          25 infer·재귀
        키 유니온을 만든다  ->  그 유니온을 나눈다  ->  이름 붙여 되뽑는다   ★ 급소
             │
             │  keyof typeof x  <- 여기서 딱 한 번 만난다
             ▼
           23 typeof  (값 공간 / 타입 공간 -- 직교하는 축)
```

### 12. ★★ 세 층

**왜 그런가**

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장(2.1)** | `keyof T` 가 키의 유니온이고 `T[K]` 가 그 키의 값 타입이다 · 인덱스 시그니처가 `keyof` 를 넓힌다 · `keyof` 는 `public` 만 본다 · 유니온은 교집합, 교차는 합집합 |
| **★ 구현(tsc 7.0.2)** | ★★★ `keyof User` 를 **별칭 이름으로 찍는 것**(1번 7행) — `& {}` 가 펼치게 만든다 · ★★ 긴 유니온을 **`... 18 more ...`** 로 자르는 것(2번 3행) · 진단 **문구** 전문 |
| **★ 이 판의 관찰** | 키 유니온의 **표시 순서**(사전순으로 보인다 — 5회 md5 가짓수 1) · 배열의 `keyof` 에 **`unique symbol`** 이 끼는 것(`lib` 판에 달렸다) |
| **★ 부적용 — 설정** | `--strict` 를 꺼도 **다섯 파일 전부 한 글자도 같다** — [**21번 주제**](../21-inference-control-const-and-noinfer/)는 여섯 중 하나가 갈렸다 |
| **★ 부적용 — 3창(`.js`)** | ★★ **잴 것이 없다** — `keyof`·`T[K]` 는 **전부 타입 층**이다. 이 문서에 `.js` 블록이 **하나도 없다** |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — **계산하지 않는다**(6번) |

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

- ★★★ **이 주제는 「언어 보장」 칸이 두껍다** — [**21번 주제**](../21-inference-control-const-and-noinfer/)와 정반대다.\
  추론은 자리마다 달라지지만 **`keyof` 는 규칙이 정해져 있다.**\
  구현 층으로 빠지는 것은 거의 전부 「**어떻게 보여 주느냐**」다.
- ★★ 그래서 이 주제에서 **외울 것은 규칙이고, 던져 볼 것은 표시**다.\
  「`keyof` 가 무엇이 되나」는 외울 수 있고, 「그것을 어떻게 읽어 내나」는 **`& {}` 를 기억하는 문제**다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `javac -version` · `rustc --version` | `Version 7.0.2` · `v18.19.1` · `javac 21.0.5` · `rustc 1.92.0` |
| ★★★ `keyof` 가 펼쳐지는 꼴 | `--noEmit ex.22a.ts` | exit 1 · **10건** · 7행 메아리 대 8행 **펼침** · 28행 **침묵** |
| ★★★ 배열의 `keyof` | `--noEmit ex.22b.ts` | exit 1 · **5건** · 6·7·8행 **통과**, 9행 **`TS2322`** |
| `public` 표면과 `as const` | `--noEmit ex.22c.ts` | exit 1 · **7건** · 26·27행 **같고** 28·29행 **갈린다** |
| 인덱스 접근 타입 | `--noEmit ex.22d.ts` | exit 1 · **8건** · 10행 **`TS2339`** |
| ★★★ 세 단계 접근 | `--noEmit ex.22e.ts` | exit 1 · **5건** · 12행 `string` · 18행 유니온 · 23행 `unknown` · 28행 **통과** |
| 5창 닫기 | `--declaration --emitDeclarationOnly ex.22f.ts` | ★ **exit 0 · 진단 0줄** · `keyof User` 가 **그대로** 남는다 |
| 교차 갈래(Java) | `javac -d jout Keyed.java && java -cp jout Keyed` | exit 0 · `null` · `[가, 나]` · `2` |
| `--strict` 대조 | 다섯 파일을 `--strict false` 로 재실행 | ★★★ **다섯 전부 한 글자도 같다** — 하나도 안 갈렸다 |
| 표시 순서 | 같은 명령 **5회** × 세 파일 | ★★ md5 **가짓수 1** — 순서가 안 흔들렸다 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ `keyof User` 를 **별칭 이름으로 찍는 것**(1번 7행)과 **`& {}` 가 펼치게 만드는 것**(8행) — **표시 방식**이다.
- ★★★ 긴 유니온을 **`... 18 more ...`** 로 자르는 것(2번 3행) — 잘리는 **개수**도 판에 달렸다.
- ★★ 배열의 `keyof` 에 든 **메서드 이름 목록** — **`lib`/`--target` 이 정한다.** `es2022` 로만 던졌다.
- ★★ 키 유니온의 **표시 순서** — 5회 동일했지만 **관찰이지 보장이 아니다.**
- ★★ 진단 **문구** 전문 — `TS2322`·`TS2339`·`TS2345` 라는 **코드**가 더 오래 간다.
- ★ `keyof typeof Account` 에 **`"prototype"`** 이 끼는 것 — 생성자 타입의 모양에 달렸다([**23번 주제**](../23-typeof-type-operator/)).

**안 돌려 본 것**

- **다른 `lib`/`--target`** 으로 배열의 `keyof` 를 다시 찍는 것 — **안 던졌다.** `es2022` 한 판뿐이다.
- **`Object.keys` 의 반환 타입**과 `keyof` 의 어긋남 — **안 던졌다.** 원리만 「더 들어가면」에 적었다.
- **`Symbol` 키를 가진 객체**의 `keyof` — **안 던졌다.**
- **프로퍼티가 충돌하는 교차**(`A & B` 에서 같은 키의 타입이 다른 경우) — **안 던졌다.** [**10번 주제**](../10-intersection-types/).
- **매핑 타입**(`in keyof`)·**템플릿 리터럴 키 리매핑** — **안 던졌다.** 목록의 **26번 주제**·**27번 주제**.
- **`noUncheckedIndexedAccess`** 를 켠 판 — **안 던졌다.** 목록의 **41번 주제**.
- **거대한 키 유니온의 검사 시간** — **재지 않았고 수치를 적지 않았다.**
