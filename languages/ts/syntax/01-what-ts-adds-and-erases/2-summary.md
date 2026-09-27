# ts/syntax/01 — TS 가 더하는 것과 지우는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [TypeScript Handbook — The Basics](https://www.typescriptlang.org/docs/handbook/2/basic-types.html) ·
> [Handbook — Enums](https://www.typescriptlang.org/docs/handbook/enums.html) ·
> [TSConfig — `erasableSyntaxOnly`](https://www.typescriptlang.org/tsconfig/#erasableSyntaxOnly) ·
> [TSConfig — `experimentalDecorators`](https://www.typescriptlang.org/tsconfig/#experimentalDecorators).
> 핸드북은 **규칙 확인용으로만** 열었다. 본문의 진단·방출 결과는 전부 이 판에서 직접 던져서 받은 것이다.
> **실행 검증** — 이 문서의 모든 진단·방출된 JS·실행 출력은 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version =====
Version 7.0.2
v18.19.1
```

> ★★★ **`tsc` 가 7.0.2 다 — 5.x 가 아니다.** 7.0 은 Go 로 다시 쓴 네이티브 포팅판이고 **기본값이 다르다** —
> 이 문서의 모든 결과는 **옵션을 안 준 `tsc <파일>.ts`** 기준이며, 그때 `strict` 는 **켜져 있고**(기본 `true`)
> `target` 은 **es2025**, `module` 은 **esnext** 다(`tsc --help --all` 에서 확인).\
> ★ `tsc` 에 **파일을 직접 주면 `tsconfig.json` 을 무시하고 기본 옵션으로 컴파일한다**(`tsc --help` 의 문구).
> 그래서 이 문서의 블록은 설정 파일 없이도 그대로 재현된다.\
> ★ 진단이 **stdout 으로 나오는지 stderr 로 나오는지**는 [**02번 주제**](../02-type-checking-vs-emit/)에서 갈라 받아 확인했다 — **전부 stdout 이다**.
> **버전** — `enum`·`namespace`·매개변수 프로퍼티는 TS 1.x 부터, `import type` 은 3.8 부터,
> `erasableSyntaxOnly` 는 5.8 부터다. 7.0 에서 이 다섯 중 **사라진 것은 없다**(전부 이 판에서 돌아갔다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS2693`·`TS1294`)·에러 문구·`(행,열)`·종료 코드·**방출된 JS 전문** | 같은 입력이면 컴파일러가 같은 글자를 낸다. 10회 재실행에서 한 글자도 안 바뀌었다 |
| **안 흔들린다** | `node` 실행 출력 | 난수·시각·순서 미정 컬렉션을 안 썼다 |
| **흔들린다** | 절대 경로 | 그래서 **작업 디렉토리에서 상대 경로로만** 던졌다 — 진단에 `ex.01b.ts` 처럼 파일명만 박힌다 |
| **흔들린다** | `--pretty` 가 켜졌을 때의 ANSI 색·소스 발췌·`Found N errors` 요약 줄 | `--pretty` 기본값이 **`true`** 라 터미널에서는 다르게 보인다. 그래서 모든 블록을 **`--pretty false`** 로 고정했다 |

> ★ **소스 펜스의 첫 줄 `// 파일명` 은 대조용 배너다** — 실파일에는 없다.\
> 그래서 **진단의 행 번호 = 펜스에서 센 줄 번호 − 1** 이다.

## 한눈에 — 쉽게 말하면

**TS 는 JS 원고 위에 붙이는 포스트잇이다.** 인쇄기에 넣기 전에 포스트잇을 전부 떼어 낸다.

| 비유 | 실체 |
|---|---|
| 원고 종이 | **JS 코드** — 실제로 실행되는 것 |
| 포스트잇 — 「여기는 숫자만」 | **타입 표기** — `: number`·`interface`·`type` |
| 인쇄 전에 떼어 낸다 | **소거(erasure)** — 방출된 `.js` 에 타입이 한 글자도 안 남는다 |
| 포스트잇을 보고 교정을 본다 | **타입 검사** — 떼어 내기 **전에** 한 번 읽는다 |
| ★ 떼어지지 않는 스티커 넷 | `enum` · `namespace` · **매개변수 프로퍼티** · **레거시 데코레이터** |
| 떼어 냈는데 자국이 남는 것 | `const enum` — 선언은 사라지고 **값이 그 자리에 박힌다** |
| 포스트잇으로는 못 하는 일 | **런타임 검사** — 떼어 낸 뒤에는 아무도 읽을 수 없다 |

- ★★ 한 줄로 — **「타입은 컴파일 시각에만 존재하고, 실행 시각에는 없다.」**
- ★★ 그래서 이 갈래의 창은 **방출된 `.js` 자체**다. 「안 남는다」가 말이 아니라 **글자로 보인다**.

```text
   ex.01a.ts  ──── tsc ────┬──▶ 타입 검사   : 포스트잇을 읽는다 (여기서만 타입이 있다)
                           │
                           └──▶ 코드 방출   : 포스트잇을 떼고 JS 를 쓴다
                                    │
                                    ▼
                                ex.01a.js  ──── node ────▶ 실행
                                    ▲
                        여기에는 타입이 한 글자도 없다
```

```text
  지워지는 것                            안 지워지는 것
  +---------------------------+          +---------------------------+
  | : number  : string        |          | enum Color { ... }        |
  | interface User { ... }    |          | namespace Config { ... }  |
  | type Id = string          |          | constructor(public x: …)  |
  | <T> 제네릭 인자           |          | @log  (레거시 데코레이터) |
  | as User  ·  satisfies     |          +---------------------------+
  | ?  (선택 매개변수 표기)   |            → JS 코드로 **번역**된다
  | !  (확정 할당 표기)       |
  | import type { … }         |          const enum Dir { Up }
  +---------------------------+          +---------------------------+
    → 방출된 파일에 **없다**              | 선언은 사라지고            |
                                          | 쓴 자리에 값이 박힌다      |
                                          +---------------------------+
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **무엇이 지워지나** — 타입 표기·`interface`·`type` 이 방출된 JS 에 남지 않는다는 것을 **무엇으로 증명하나**.
2. **무엇이 안 지워지나** — TS 가 JS 에 **없는 것을 더한** 자리는 어디이고, 그것이 방출에서 어떤 JS 가 되나.
3. **그래서 타입으로 못 하는 검사는 무엇인가** — 실행 시각에 필요한 판정을 무엇으로 대신하나.

★ 이 주제가 「**타입은 없다**」를 세우면, [**02번 주제**](../02-type-checking-vs-emit/)가 「**그래서 검사와 방출이 따로 돈다**」를 세운다. 둘은 한 쌍이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★ **방출된 `.js` 전문** | 「타입이 안 남는다」가 **글자로** 보인다 | ★ 이 갈래의 고유 창 |
| **일부러 던져서 받는 진단** | 「이 이름은 값이 아니다」 — `TS2693` | 모든 주제 공통 |
| ★ **`--erasableSyntaxOnly`** | **컴파일러가 「지울 수 없는 것」을 직접 가리킨다** | ★ 이 주제의 고유 창 |
| **`node` 실행 출력** | 떼어 낸 뒤에 실제로 무슨 값이 도는지 | 모든 주제 공통 |

★ **세 번째 창이 이 주제의 값이다.** 「무엇이 안 지워지나」를 외우는 대신 **컴파일러에게 세어 달라고 하면 된다.**

비용 — 없음. 셋 다 컴파일 한 번이다.

### (1) ★★ 타입 표기를 모아 놓고 방출을 본다

**언제 쓰나** — 「이 표기가 런타임에 남나?」가 궁금할 때. **외우지 말고 방출을 찍는다.**

```ts
// ex.01a.ts
// 타입에만 속하는 표기를 모아 놓고, 방출된 JS 에 무엇이 남는지 본다
type Id = string;
type Handler<T> = (value: T) => void;
interface User {
    id: Id;
    name: string;
    nickname?: string;
}

function greet(u: User): string {
    return "안녕 " + u.name;
}

const onUser: Handler<User> = (u) => console.log(greet(u));
const raw = JSON.parse('{"id":"u-1","name":"준"}') as User;
const size = { w: 10, h: 20 } satisfies Record<string, number>;
let count!: number;
count = 3;

onUser(raw);
console.log(size.w, count);
```

```text
===== tsc --pretty false ex.01a.ts (tsc exit=0) =====
===== 방출된 ex.01a.js =====
"use strict";
function greet(u) {
    return "안녕 " + u.name;
}
const onUser = (u) => console.log(greet(u));
const raw = JSON.parse('{"id":"u-1","name":"준"}');
const size = { w: 10, h: 20 };
let count;
count = 3;
onUser(raw);
console.log(size.w, count);
```

그림 해설 — 한 단계에 한 문장.

- `type Id`·`type Handler<T>`·`interface User` **세 선언이 통째로 사라졌다.** 방출된 파일의 첫 줄이 곧장 `function greet` 이다.
- `function greet(u: User): string` 에서 `: User` 와 `: string` 이 빠지고 `function greet(u)` 만 남았다.
- `const onUser: Handler<User> = …` 에서 **표기와 제네릭 인자가 같이** 빠졌다.
- `as User` 가 사라졌다 — `JSON.parse(...)` 가 그대로다. **단언은 실행에서 아무 일도 하지 않는다.**
- `satisfies Record<string, number>` 도 사라졌다 — `{ w: 10, h: 20 }` 만 남았다.
- `let count!: number` 의 **느낌표(확정 할당 표기)까지** 빠져 `let count;` 가 됐다.

★ 같은 파일을 **`--erasableSyntaxOnly`** 로 다시 던지면 컴파일러가 아무 말도 안 한다 — **전부 지울 수 있는 문법**이라는 뜻이다.

```text
===== tsc --pretty false --erasableSyntaxOnly --noEmit ex.01a.ts (tsc exit=0) =====
```

비용 — 소거는 공짜다. 방출 단계에서 노드를 안 쓰는 것뿐이라 런타임 비용이 0이다.

### (2) ★★★ 안 지워지는 넷 — TS 가 JS 에 **더한** 것

**언제 쓰나** — 「TS 를 쓰면 번들이 커지나?」·「이 문법을 써도 되나?」를 판정할 때.

```ts
// ex.01b.ts
// TS 고유 문법 넷 — 이것들은 방출에서 사라지지 않는다
enum Color {
    Red,
    Green,
}
const enum Dir {
    Up,
    Down,
}
namespace Config {
    export const retry = 3;
}
class Point {
    constructor(public x: number, private y: number) {}
    sum() {
        return this.x + this.y;
    }
}

console.log(Color.Red, Color[0], Dir.Up, Config.retry, new Point(1, 2).sum());
```

```text
===== tsc --pretty false ex.01b.ts (tsc exit=0) =====
===== 방출된 ex.01b.js =====
"use strict";
// TS 고유 문법 넷 — 이것들은 방출에서 사라지지 않는다
var Color;
(function (Color) {
    Color[Color["Red"] = 0] = "Red";
    Color[Color["Green"] = 1] = "Green";
})(Color || (Color = {}));
var Config;
(function (Config) {
    Config.retry = 3;
})(Config || (Config = {}));
class Point {
    x;
    y;
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }
    sum() {
        return this.x + this.y;
    }
}
console.log(Color.Red, Color[0], 0 /* Dir.Up */, Config.retry, new Point(1, 2).sum());
```

```text
===== node ex.01b.js (node exit=0) =====
0 Red 0 3 3
```

그림 해설 — 한 단계에 한 문장.

- `enum Color` 는 **IIFE 한 덩어리로 번역됐다.** `Color[Color["Red"] = 0] = "Red"` 가 **역매핑**을 만든다 — 그래서 `Color[0]` 이 `"Red"` 를 돌려준다(실행 출력 둘째 칸).
- `namespace Config` 도 **같은 모양의 IIFE** 다. 이름 공간이 런타임 객체가 된다.
- `constructor(public x: number, private y: number)` 는 **필드 선언 두 줄 + 대입 두 줄**로 풀렸다. `private` 도 예외가 아니다 — `y;` 가 그대로 방출된다.
- ★ `const enum Dir` 만 다르다. **선언은 통째로 사라졌는데** 쓴 자리에 `0 /* Dir.Up */` 이 박혔다 — 「지워지되 자국을 남긴다」.

```text
  TS 소스                                   방출된 JS
  ---------------------------------------   ------------------------------------------
  enum Color { Red, Green }          ───▶   var Color;
                                            (function (Color) { … })(Color || (Color = {}));
                                                       ↑ 런타임 객체가 **생긴다**

  const enum Dir { Up, Down }        ───▶   (없음)
  … Dir.Up …                         ───▶   0 /* Dir.Up */
                                                       ↑ 값이 **박힌다**

  constructor(public x: number)      ───▶   x;
                                            constructor(x) { this.x = x; }
                                                       ↑ 코드가 **늘어난다**
```

비용 — `enum` 하나가 방출에서 **4줄**, `namespace` 하나가 **4줄**이다. `const enum` 은 0줄이지만 **파일 경계를 넘으면 인라인이 안 된다**(→ [목록의 **31번 주제**](../31-enum-pitfalls/)).

### (3) ★★★ 컴파일러에게 「지울 수 없는 것」을 세어 달라고 한다

**언제 쓰나** — 「우리 코드가 타입만 떼면 그대로 JS 가 되나?」를 기계로 판정할 때.

다시 던질 수 있게 소스를 같은 자리에 둔다(1절과 같은 파일이다).

```ts
// ex.01b.ts
// TS 고유 문법 넷 — 이것들은 방출에서 사라지지 않는다
enum Color {
    Red,
    Green,
}
const enum Dir {
    Up,
    Down,
}
namespace Config {
    export const retry = 3;
}
class Point {
    constructor(public x: number, private y: number) {}
    sum() {
        return this.x + this.y;
    }
}

console.log(Color.Red, Color[0], Dir.Up, Config.retry, new Point(1, 2).sum());
```

```text
===== tsc --pretty false --erasableSyntaxOnly --noEmit ex.01b.ts (tsc exit=1) =====
ex.01b.ts(2,6): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.01b.ts(6,12): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.01b.ts(10,11): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.01b.ts(14,17): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.01b.ts(14,35): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
```

그림 해설 — 한 단계에 한 문장.

- 에러가 **다섯 건**인데 소스의 TS 고유 문법도 **다섯 자리**다 — `enum`(2행) · `const enum`(6행) · `namespace`(10행) · `public x`(14행) · `private y`(14행).
- ★ 매개변수 프로퍼티는 **한 생성자 안에 둘이면 둘 다** 따로 걸린다(`(14,17)` 과 `(14,35)`).
- 문구는 다섯 줄 모두 같다 — 「This syntax is not allowed when 'erasableSyntaxOnly' is enabled.」

> **`erasableSyntaxOnly`** — 「타입 표기만 떼면 그대로 JS 가 되는 문법」만 허용하는 플래그(TS 5.8 도입).\
> 예: Node 의 타입 소거 실행(`node --experimental-strip-types`)처럼 **떼기만 하는 도구**에 태울 코드에서 켠다.

비용 — 검사 한 번. 방출을 바꾸지 않는다.

### (4) ★★ 타입 이름은 값이 아니다

**언제 쓰나** — 「이 인터페이스로 `instanceof` 를 쓸 수 있나?」가 궁금할 때.

```ts
// ex.01c.ts
// 타입은 값이 아니다 — 값 자리에 쓰면 무엇이라고 하나
interface User {
    id: string;
}
type Id = string;

function isUser(v: unknown): boolean {
    return v instanceof User;
}
const kind = typeof Id;
console.log(isUser({}), kind);
```

```text
===== tsc --pretty false --noEmit ex.01c.ts (tsc exit=1) =====
ex.01c.ts(8,25): error TS2693: 'User' only refers to a type, but is being used as a value here.
ex.01c.ts(10,21): error TS2693: 'Id' only refers to a type, but is being used as a value here.
```

그림 해설 — 한 단계에 한 문장.

- `v instanceof User` 가 **값 자리**라서 걸렸다 — `interface User` 는 **타입 공간에만** 있는 이름이다.
- `typeof Id` 도 같은 이유로 걸렸다. `type Id` 는 **런타임에 존재 자체가 없다.**
- 두 진단이 같은 코드(`TS2693`)이고 문구가 「only refers to a type, but is being used as a value here」다.

```text
   이름 공간이 둘이다
   +---------------------+        +---------------------+
   |    타입 공간        |        |    값 공간          |
   | interface User      |        | class Session       |
   | type Id             |        | const x             |
   | type Handler<T>     |        | function greet      |
   +---------------------+        +---------------------+
        ↑ 방출에서 사라진다            ↑ 방출에 남는다
        ↑ instanceof 에 못 쓴다        ↑ instanceof 에 쓴다

   class 는 **양쪽에 다 있다** — 타입으로도 값으로도 쓸 수 있다.
```

비용 — 없음. 검사 시각의 판정이다.

### (5) ★ 그래서 런타임 검사로 대신하는 자리

**언제 쓰나** — 경계 밖에서 들어온 값(`JSON.parse`·`fetch`·`localStorage`)을 믿어야 할 때.

```ts
// ex.01d.ts
// 타입으로 못 하는 검사를 런타임 검사로 대신하는 자리
interface User {
    id: string;
    name: string;
}
class Session {
    constructor(public token: string) {}
}

function isUser(v: unknown): v is User {
    if (typeof v !== "object" || v === null) return false;
    const o = v as Record<string, unknown>;
    return typeof o.id === "string" && typeof o.name === "string";
}

const good: unknown = JSON.parse('{"id":"u-1","name":"준"}');
const bad: unknown = JSON.parse('{"id":1}');

console.log("isUser(good)        :", isUser(good));
console.log("isUser(bad)         :", isUser(bad));
console.log("instanceof Session  :", new Session("t") instanceof Session);
console.log("'id' in good        :", typeof good === "object" && good !== null && "id" in good);
console.log("typeof 로 갈리는 것  :", typeof "a", typeof 1, typeof null, typeof undefined);
```

```text
===== node ex.01d.js (node exit=0) =====
isUser(good)        : true
isUser(bad)         : false
instanceof Session  : true
'id' in good        : true
typeof 로 갈리는 것  : string number object undefined
```

그림 해설 — 한 단계에 한 문장.

- `isUser` 는 `v is User` 라는 **타입 술어**를 반환하지만, 몸통은 **전부 JS 런타임 검사**(`typeof`·`!== null`)다.
- `bad` 는 `{"id":1}` 이라 `typeof o.id === "string"` 에서 걸려 `false` 가 됐다 — **타입은 이것을 못 잡는다**(`JSON.parse` 의 정적 타입은 `any` 다).
- `instanceof Session` 은 된다 — `class` 는 **값 공간에도** 있기 때문이다.
- `"id" in good` 도 JS 연산자라 그대로 돈다.
- `typeof null` 이 `"object"` 인 것은 JS 쪽 사실이다(→ `../../js/syntax/README.md` 의 **01번 주제**).

비용 — 검사가 **실행 시각에 실제로 돈다.** 타입 표기는 0원이지만 런타임 가드는 공짜가 아니다.

### (6) ★ `import` 목록에서 이름이 지워진다

**언제 쓰나** — 「타입만 쓰는 모듈을 import 했는데 번들에 딸려 들어오나?」를 판정할 때.

```ts
// ex.01e-lib.ts
// 타입과 값을 한 파일에서 같이 내보낸다
export interface Shape {
    area(): number;
}
export class Circle implements Shape {
    constructor(public r: number) {}
    area() {
        return 3 * this.r * this.r;
    }
}
```

```ts
// ex.01e.ts
// 타입만 쓰는 이름은 import 목록에서 지워진다
import { Shape, Circle } from "./ex.01e-lib.js";
import type { Shape as Shape2 } from "./ex.01e-lib.js";

const s: Shape = new Circle(2);
const t: Shape2 = s;
console.log(s.area(), t.area());
```

```text
===== tsc --pretty false --module esnext ex.01e.ts ex.01e-lib.ts (tsc exit=0) =====
===== 방출된 ex.01e.js =====
// 타입만 쓰는 이름은 import 목록에서 지워진다
import { Circle } from "./ex.01e-lib.js";
const s = new Circle(2);
const t = s;
console.log(s.area(), t.area());
```

그림 해설 — 한 단계에 한 문장.

- 첫 줄 `import { Shape, Circle }` 에서 **`Shape` 만 빠지고** `import { Circle }` 이 됐다 — 타입으로만 쓰인 이름이라 소거됐다.
- 둘째 줄 `import type { Shape as Shape2 }` 는 **줄째로** 사라졌다.
- `const t: Shape2 = s` 는 `const t = s` 가 됐다.
- ★ 즉 `import type` 은 **방출 결과를 바꾸는 게 아니라 의도를 못 박는 것**이다 — 안 써도 이 판에서는 같은 JS 가 나왔다.
- ★★ 다만 `verbatimModuleSyntax` 를 켜면 이야기가 달라진다 — [**02번 주제**](../02-type-checking-vs-emit/)에서 **방출된 파일이 실행에서 터지는** 것까지 본다.

비용 — 소거된 import 는 **번들에도 안 들어간다.** 타입만 쓰는 의존성은 런타임 비용이 0이다.

### (7) ★ 지워지기는커녕 코드가 늘어나는 자리 — 레거시 데코레이터

**언제 쓰나** — `experimentalDecorators` 를 켤지 말지 고를 때.

```ts
// ex.01f.ts
// 레거시 데코레이터는 지워지기는커녕 헬퍼 함수를 덧붙인다
function log(_target: unknown, key: string, desc: PropertyDescriptor) {
    const orig = desc.value;
    desc.value = function (this: unknown, ...args: unknown[]) {
        console.log("호출:", key);
        return orig.apply(this, args);
    };
}

class Svc {
    @log
    run(n: number) {
        return n * 2;
    }
}

console.log(new Svc().run(21));
```

옵션 없이 그냥 던지면 이 판은 **표준 데코레이터로 읽고** 거절한다.

```text
===== tsc --pretty false --noEmit ex.01f.ts (tsc exit=1) =====
ex.01f.ts(11,5): error TS1241: Unable to resolve signature of method decorator when called as an expression.
  The runtime will invoke the decorator with 2 arguments, but the decorator expects 3.
```

`--experimentalDecorators` 를 켜면 통과하고, **방출에 `__decorate` 헬퍼가 통째로 붙는다.**

```text
===== tsc --pretty false --experimentalDecorators ex.01f.ts (tsc exit=0) =====
===== 방출된 ex.01f.js =====
"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
// 레거시 데코레이터는 지워지기는커녕 헬퍼 함수를 덧붙인다
function log(_target, key, desc) {
    const orig = desc.value;
    desc.value = function (...args) {
        console.log("호출:", key);
        return orig.apply(this, args);
    };
}
class Svc {
    run(n) {
        return n * 2;
    }
}
__decorate([
    log
], Svc.prototype, "run", null);
console.log(new Svc().run(21));
```

```text
===== node ex.01f.js (node exit=0) =====
호출: run
42
```

그림 해설 — 한 단계에 한 문장.

- 방출된 파일의 **처음 여섯 줄이 원본에 없던 코드**다 — `__decorate` 헬퍼.
- 클래스 몸통에서 `@log` 가 빠지고, 클래스 뒤에 `__decorate([log], Svc.prototype, "run", null);` 이 붙었다.
- 실행하면 `호출: run` 이 먼저 찍힌다 — **데코레이터가 실제로 런타임에 돈다.**
- ★ 즉 데코레이터는 「타입 층」이 아니다. **소거 대상이 아니라 번역 대상**이다.

비용 — 헬퍼 6줄 + 데코레이트 호출. `emitDecoratorMetadata` 까지 켜면 더 붙는다(→ [목록의 **47번 주제**](../47-decorators/)).

## 문법 — 형태와 규칙

**형태** — 「지워지는 표기」는 값 문법에 **덧붙는 자리**에만 온다. 아래 한 파일이 그 형태를 전부 담고 있고, 그대로 컴파일된다.

```ts
// ex.01g.ts
// 지워지는 표기를 형태별로 한 줄씩 모은 것 — 전부 컴파일된다
type Id = string;
interface U {
    id: Id;
}
declare const v: unknown;
declare const ambient: number;

let x: number;
function f(a: string, b?: number): void {
    console.log(a, b);
}
const g = <T,>(value: T): T => value;
const y = v as string;
const z = { retry: 3 } satisfies Record<string, number>;
let w!: number;

x = 1;
w = 2;
f("a");
console.log(g(1), y, z.retry, x, w, ambient);
export type { U };
```

```text
===== tsc --pretty false --module esnext ex.01g.ts (tsc exit=0) =====
===== 방출된 ex.01g.js =====
let x;
function f(a, b) {
    console.log(a, b);
}
const g = (value) => value;
const y = v;
const z = { retry: 3 };
let w;
x = 1;
w = 2;
f("a");
console.log(g(1), y, z.retry, x, w, ambient);
export {};
```

**규칙 불릿**

- ★ **지워지는 것은 전부 「JS 문법이 아닌 덧붙임」이다.** 콜론 뒤, 꺾쇠 안, `as`·`satisfies` 뒤, `declare` 뒤, `!` 자리.
- ★ 방출을 보면 `declare const v`·`declare const ambient` 두 줄이 **통째로 없다.** 그런데 마지막 줄은 `ambient` 를 그대로 쓴다 — `declare` 는 「값은 다른 데서 온다」는 **약속만** 적는 것이라, 실제로 돌리면 `ReferenceError` 가 난다.
- ★ `export type { U };` 도 사라지고 자리에 `export {};` 만 남았다 — 모듈이라는 표시다.
- ★★ **안 지워지는 넷은 전부 「JS 에 없는 선언을 새로 만든 것」이다** — `enum`·`namespace`·매개변수 프로퍼티·레거시 데코레이터.\
  네 개의 공통점은 **런타임에 존재해야 뜻이 서는 것**이라는 점이다.
- `const enum` 은 다섯째 부류다 — **선언은 지워지고 사용처에 값이 박힌다.**
- `class` 는 **타입 공간과 값 공간에 동시에** 있다. 그래서 `implements` 대상이면서 `instanceof` 대상이다.
- `abstract`·`implements`·`override`·접근 제어자(`public`/`private`/`protected`)는 **매개변수 프로퍼티가 아닌 한 지워진다**(→ [목록의 **32번 주제**](../32-class-type-aspects/)).

**금지 사례** — 이 주제에서 던져 받은 것 셋이다. 전문은 「동작 방식」의 블록에 있다.

```text
1) 타입 이름을 값 자리에            ->  TS2693  'User' only refers to a type, …
2) erasableSyntaxOnly 아래의 TS 고유 문법 ->  TS1294  This syntax is not allowed …
3) 표준 데코레이터 자리에 3인자 함수  ->  TS1241  Unable to resolve signature …
```

## 어디서 틀리나

- ★★★ **「TS 는 런타임에 타입 검사를 해 준다」** — 안 한다. 방출된 JS 에 검사가 **한 줄도 없다**(§동작 방식 (1) 의 방출 전문이 근거다).\
  경계에서 들어오는 값은 **직접 검사**해야 한다.
- ★★ **「`interface` 로 `instanceof` 를 쓴다」** — `TS2693`. 타입 공간의 이름은 값 자리에 못 온다.
- ★★ **「`enum` 도 어차피 지워지겠지」** — 안 지워진다. 방출에 IIFE 4줄이 붙고 역매핑 객체가 런타임에 산다.\
  ★ 「`const enum` 을 쓰면 되겠네」도 성급하다 — `isolatedModules`·번들러와 엮이면 또 다른 문제가 된다(→ [목록의 **31번 주제**](../31-enum-pitfalls/)).
- ★★ **「`private` 은 런타임에 감춰진다」** — 안 감춰진다. 방출된 필드 이름이 `y` 그대로다.\
  진짜로 감추려면 JS 의 `#` 를 쓴다(→ [**05번 주제**](../05-structural-typing/) 에서 타입 쪽 차이도 본다).
- ★ **「`as` 를 쓰면 변환이 일어난다」** — 안 일어난다. `as` 는 방출에서 **통째로 사라진다**. 값은 한 비트도 안 바뀐다.
- ★ **「타입만 쓰는 import 는 번들에 안 들어간다」를 무조건 믿는 것** — 이 판의 기본 설정에서는 맞지만 **`verbatimModuleSyntax` 를 켜면 남는다.** 설정을 안 밝히고 단정하면 틀린다.
- ★ **「`!` 를 붙였으니 값이 있다」** — `!` 는 검사를 끄는 표기일 뿐 방출에서 사라진다. 실행 시각에 값이 없으면 그대로 터진다.

## 구현 세부사항 대 언어 보장

이 갈래에서 이 절은 「**타입 검사가 보장하는 것 대 방출된 JS 가 하는 것**」으로 읽는다.

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장** | 타입 표기·`interface`·`type`·`as`·`satisfies`·`import type` 은 **런타임 의미가 없다** | 핸드북이 소거를 언어 설계로 못 박는다. 이 판의 방출 전문이 그 결과다 |
| **언어 보장** | `enum`·`namespace`·매개변수 프로퍼티·레거시 데코레이터는 **JS 코드로 번역된다** | `erasableSyntaxOnly` 가 정확히 이 넷을 거절한다(`TS1294` 다섯 건) |
| **언어 보장** | 타입 공간과 값 공간은 **분리돼 있다** | `TS2693` 의 문구 자체가 그 규칙이다 |
| **이 판의 관찰** | `enum` 이 **IIFE + 역매핑**으로, 매개변수 프로퍼티가 **필드 선언 + 대입**으로 방출되는 **정확한 모양** | `target`(기본 es2025)·`useDefineForClassFields`(es2022 이상에서 `true`) 에 달려 있다 |
| **이 판의 관찰** | `const enum` 이 `0 /* Dir.Up */` 으로 **주석까지 붙여** 인라인되는 것 | 주석 형식은 컴파일러 구현이다. 「인라인된다」만 성질로 읽는다 |
| **이 판의 관찰** | `__decorate` 헬퍼의 **본문 여섯 줄** | 헬퍼 구현은 판마다 바뀐다. 「헬퍼가 붙는다」만 성질로 읽는다 |
| **설정에 달림** | `Shape` 가 import 목록에서 지워지는 것 | `verbatimModuleSyntax` 가 꺼져 있을 때만이다 |

★ **「여러 번 돌려 같았다」는 보장이 아니다.** 이 문서의 방출 전문은 **이 판(7.0.2)·이 옵션**의 결과다. `target` 을 낮추면 클래스 필드 방출 모양이 바뀐다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| `interface`·`type`·표기 — **비용이 0이다.** 마음껏 쓴다 | `enum` — 방출이 붙고 역매핑이 딸려 온다. 유니온 리터럴 + `as const` 로 대신한다 |
| `import type` — 의도를 못 박고 설정이 바뀌어도 안전하다 | `namespace` — 모듈이 표준이 된 뒤로는 선언 병합 말고는 쓸 데가 없다 |
| 매개변수 프로퍼티 — 방출이 붙지만 **읽기가 훨씬 낫다** | 레거시 데코레이터 — 새 코드에 굳이 켤 이유가 없다 |
| 타입 술어(`v is T`) — 런타임 검사를 타입 층에 **연결**한다 | `as` 로 때우기 — 검사를 끄는 것이지 안전해지는 게 아니다 |

## 핵심 문장

1. **타입은 컴파일 시각에만 있고 실행 시각에는 없다** — 방출된 `.js` 에 한 글자도 안 남는다.
2. **TS 가 JS 에 더한 것 넷은 지워지지 않는다** — `enum`·`namespace`·매개변수 프로퍼티·레거시 데코레이터. 이것들은 **번역**된다.
3. **`const enum` 은 다섯째 부류다** — 선언은 지워지고 값이 사용처에 박힌다.
4. **타입 공간과 값 공간은 다른 이름 공간이다** — `interface` 는 `instanceof` 에 못 쓴다(`TS2693`).
5. **경계에서 들어온 값은 런타임 검사로만 확인된다** — `typeof`·`instanceof`·`in`, 그리고 그것을 타입에 잇는 타입 술어.

## 관련 자료

- [**02번 주제** — 타입 검사와 코드 방출의 분리](../02-type-checking-vs-emit/) — 여기는 「**무엇이 지워지나**」까지, 그쪽은 「**지우는 일과 검사하는 일이 왜 따로 도나**」부터.
- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — `private` 멤버가 **타입 쪽에서** 무엇을 바꾸는지는 그쪽이 정본이다.
- `../../js/syntax/README.md` 의 **01번 주제**(값의 종류와 `typeof`) — `typeof null === "object"` 같은 **런타임 의미는 JS 갈래가 정본**이다. 여기서는 그것을 **가드에 쓰는 법**만 다룬다.
- [목록의 **31번 주제**](../31-enum-pitfalls/)(열거형의 함정) — `enum`·`const enum` 의 선택은 그쪽이 정본이다. 여기서는 **방출 모양**까지만 본다.
- [목록의 **32번 주제**](../32-class-type-aspects/)(클래스의 타입 측면) — 매개변수 프로퍼티·`private` 대 `#` 의 전면적인 비교는 그쪽.
- [목록의 **36번 주제**](../36-type-only-imports-and-exports/)(타입 전용 import·export) — `verbatimModuleSyntax`·`erasableSyntaxOnly` 의 전면 비교는 그쪽.
- `cs/foundations/compiler-pipeline/` — 「컴파일러가 단계를 나눠 도는 것」 일반론은 그쪽. 여기서는 TS 고유의 **소거**만 본다.

## 용어 풀이

> **소거(type erasure)** — 타입 정보를 산출물에 남기지 않고 지워 버리는 것.\
> 예: `function greet(u: User): string` 이 방출에서 `function greet(u)` 가 된다.

> **방출(emit)** — 컴파일러가 실제 산출물(`.js`·`.d.ts`·`.js.map`)을 파일로 쓰는 단계.\
> 예: `tsc ex.01a.ts` 가 `ex.01a.js` 를 만드는 것.

> **타입 공간 / 값 공간(type space / value space)** — 이름이 사는 두 세계. 같은 글자가 두 세계에 따로 있을 수 있다.\
> 예: `interface User` 는 타입 공간에만, `const user` 는 값 공간에만, `class Session` 은 **양쪽에** 있다.

> **매개변수 프로퍼티(parameter property)** — 생성자 매개변수에 접근 제어자를 붙여 **필드 선언과 대입을 한 번에** 하는 TS 문법.\
> 예: `constructor(public x: number)` 가 방출에서 `x;` 와 `this.x = x;` 두 줄이 된다.

> **역매핑(reverse mapping)** — 숫자 `enum` 이 값에서 이름을 되찾을 수 있게 **양방향으로** 넣어 두는 것.\
> 예: `Color[0]` 이 `"Red"` 를 돌려준다.

> **IIFE(즉시 실행 함수 표현식)** — 정의하자마자 바로 호출하는 함수. 변수를 밖에 안 흘리려고 쓴다.\
> 예: `(function (Color) { … })(Color || (Color = {}));`

> **타입 술어(type predicate)** — 반환 타입을 `v is T` 로 적어 **런타임 검사 결과를 타입 좁히기에 잇는** 함수.\
> 예: `function isUser(v: unknown): v is User` 를 통과하면 그 분기에서 `v` 가 `User` 로 읽힌다.

> **앰비언트 선언(ambient declaration)** — `declare` 로 「이 이름이 어딘가에 있다」고만 알리고 값은 안 만드는 선언.\
> 예: `declare let a: any;` 는 방출에 한 줄도 안 남는다.

> **단언(type assertion)** — `as T` 로 「이건 `T` 라고 치자」고 컴파일러에게 통보하는 것. **변환이 아니다.**\
> 예: `JSON.parse(s) as User` 는 실행에서 `JSON.parse(s)` 그대로다.

## 더 들어가면

- **`--erasableSyntaxOnly` 는 팀 규약을 기계로 바꾼다.** 「`enum` 쓰지 말자」를 리뷰로 지키는 대신 플래그 하나로 `TS1294` 를 내게 할 수 있다.
- **표준 데코레이터(TC39)는 소거 대상이 아니다.** `experimentalDecorators` 없이 쓰면 이 판이 `__esDecorate` 계열 헬퍼를 방출한다 — 레거시보다 **더 많은** 코드가 붙는다. 자세한 비교는 [목록의 **47번 주제**](../47-decorators/).
- **`declare` 는 「값을 만들지 않는다」는 뜻이다.** 그래서 이 문서의 예제에서 `declare let a: any;` 로 선언한 변수는 방출에 없고, 실행하면 `ReferenceError` 가 난다 — **타입 실험 전용 도구**로만 쓴다.
