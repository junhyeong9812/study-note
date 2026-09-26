# ts/syntax/01 — TS 가 더하는 것과 지우는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출된 JS·실행 출력은 `tsc` **7.0.2** 와 `node` **v18.19.1** 에서 실제로 얻었다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(tsc exit=N)` 도 스크립트가 찍은 값이다.\
> ★ `--pretty false` 를 고정했다. 기본값이 `true` 라 **터미널에서는 색·소스 발췌·요약 줄이 더 붙어 보인다**.\
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 종료 코드 **0** · 방출은 **11줄** · 흔적을 남기는 것은 **하나도 없다**

**출력**

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

**왜 그런가**

- ★★★ 선언 **세 개**(`type Id`·`type Handler<T>`·`interface User`)가 통째로 없다. 방출의 첫 줄이 곧장 `function greet` 이다.
- 표기가 붙었던 자리는 **표기만** 빠졌다 — `function greet(u: User): string` → `function greet(u)`.
- `as User` 와 `satisfies Record<string, number>` 가 **한 글자도 안 남았다.** 둘 다 **검사 시각의 지시**일 뿐이다.
- `let count!: number` 의 느낌표까지 빠져 `let count;` 가 됐다.
- ★ 종료 코드가 `0` 인 것은 「에러가 없었다」는 뜻이다 — [**02번 주제**](../02-type-checking-vs-emit/)에서 **에러가 있어도 방출이 되는** 경우를 본다.
- ★ 같은 파일을 `--erasableSyntaxOnly` 로 던지면 아무 말도 안 한다 — **전부 지울 수 있는 문법**이기 때문이다.

```text
===== tsc --pretty false --erasableSyntaxOnly --noEmit ex.01a.ts (tsc exit=0) =====
```

### 2. ★★★ `enum`·`namespace` 는 **IIFE**, 매개변수 프로퍼티는 **필드+대입**, `const enum` 만 **값이 박힌다**

**출력**

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

**왜 그런가**

- ★★ `enum Color` 는 `var Color;` + **IIFE 네 줄**이 됐다. 안쪽의 `Color[Color["Red"] = 0] = "Red"` 가 **역매핑**을 만든다.
- 그래서 실행 출력 둘째 칸 `Color[0]` 이 `Red` 다 — **런타임 객체가 실제로 있다.**
- `namespace Config` 도 **같은 모양의 IIFE** 다. 이름 공간이 런타임 객체가 된다.
- ★ `constructor(public x: number, private y: number)` 가 **필드 선언 `x;` `y;` 두 줄 + 대입 두 줄**로 풀렸다.\
  `private` 도 예외가 아니다 — 방출된 이름이 `y` 그대로다.
- ★★★ `const enum Dir` 만 다르다. **선언이 통째로 사라졌는데** 쓴 자리에 `0 /* Dir.Up */` 이 박혔다.
- 실행 출력 다섯 칸은 `0 Red 0 3 3` 이다 — 차례로 `Color.Red`·`Color[0]`·`Dir.Up`·`Config.retry`·`new Point(1,2).sum()`.

### 3. ★★★ `ex.01b.ts` 는 **다섯 건**, `ex.01a.ts` 는 **0건**

**출력**

다시 던질 수 있게 소스를 같은 자리에 둔다(위와 같은 파일이다).

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

```text
===== tsc --pretty false --erasableSyntaxOnly --noEmit ex.01a.ts (tsc exit=0) =====
```

**왜 그런가**

- 에러 다섯 건이 소스의 TS 고유 문법 다섯 자리와 정확히 맞는다 — `enum`(2,6) · `const enum`(6,12) · `namespace`(10,11) · `public x`(14,17) · `private y`(14,35).
- ★ **매개변수 프로퍼티는 한 생성자 안에 둘이면 둘 다 따로 걸린다.** 「생성자 하나에 한 건」이 아니다.
- ★★ 이게 이 주제의 **가장 값싼 창**이다 — 「무엇이 안 지워지나」를 외우는 대신 **컴파일러에게 가리키게 한다.**
- `ex.01a.ts` 는 0건이다. 진단 줄이 하나도 없고 종료 코드가 `0` 이다 — **전부 지울 수 있는 문법**이라는 뜻이다.
- ★ 종료 코드가 `1` 인 것은 `--noEmit` 을 같이 줘서 **아무것도 안 나왔기** 때문이다(→ [**02번 주제**](../02-type-checking-vs-emit/)).

### 4. ★★ 선언이 남는 쪽은 `enum` · `const enum` 은 **사용처에 값을 남긴다**

**왜 그런가**

- `enum Color` → 방출에 `var Color;` + IIFE 4줄. **런타임 객체가 생긴다.**
- `const enum Dir` → 방출에 **선언이 없다.** 대신 `Dir.Up` 을 쓴 자리에 `0 /* Dir.Up */` 이 박혔다.
- ★ 그래서 「소거된다 / 안 된다」 **둘로 안 갈린다** — 세 부류다.

```text
  ① 통째로 사라진다        : type · interface · 표기 · as · satisfies · import type
  ② JS 코드로 번역된다      : enum · namespace · 매개변수 프로퍼티 · 레거시 데코레이터
  ③ 선언은 사라지고 값이 박힌다 : const enum
```

- ★ ③의 대가는 **파일 경계**다. 인라인은 컴파일러가 선언을 볼 수 있을 때만 되므로, 파일 단위로만 변환하는 도구(`isolatedModules` 세계)와 부딪힌다 — [목록의 **31번 주제**](../31-enum-pitfalls/)가 정본이다.

### 5. ★★ 에러 **두 건** · 코드는 둘 다 `TS2693`

**출력**

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

**왜 그런가**

- `v instanceof User` 의 `User` 가 **값 자리**다. `interface User` 는 **타입 공간에만** 있으므로 못 온다.
- `typeof Id` 도 같다 — `type Id` 는 런타임에 **존재 자체가 없다**.
- ★ `class` 는 안 걸린다. **`class` 선언 하나가 타입 공간과 값 공간에 동시에 이름을 만들기** 때문이다.\
  그래서 `implements Shape` 의 대상도 되고 `instanceof Session` 의 대상도 된다.
- ★ 문구가 결론을 그대로 말한다 — 「only refers to a type, but is being used as a value here」.

### 6. ★★ 첫 줄은 `import { Circle } …` · 둘째 줄은 **통째로 사라졌다**

**출력**

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

**왜 그런가**

- `import { Shape, Circle }` 에서 **`Shape` 만 빠졌다.** 타입으로만 쓰인 이름이라 소거됐다.
- `import type { Shape as Shape2 }` 는 **줄째로** 사라졌다 — 애초에 값을 안 가져오겠다고 적은 것이다.
- `const t: Shape2 = s;` 는 `const t = s;` 가 됐다.
- ★ **이 판의 기본 설정에서는 `import type` 을 안 써도 같은 JS 가 나온다.** `import type` 의 값은 방출을 바꾸는 게 아니라 **의도를 못 박는 것**이다.
- ★★ 단 `verbatimModuleSyntax` 를 켜면 갈린다 — 타입 이름이 import 목록에 **그대로 남고**, 그 파일은 실행에서 터진다. [**02번 주제**](../02-type-checking-vs-emit/)에서 `node` 로 터뜨려 본다.

### 7. ★★★ 기본값은 `TS1241` 로 거절 · 켜면 방출이 **길어지고** 첫 줄은 `호출: run`

**출력**

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

```text
===== tsc --pretty false --noEmit ex.01f.ts (tsc exit=1) =====
ex.01f.ts(11,5): error TS1241: Unable to resolve signature of method decorator when called as an expression.
  The runtime will invoke the decorator with 2 arguments, but the decorator expects 3.
```

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

**왜 그런가**

- 옵션 없이 던지면 이 판은 이 데코레이터를 **표준(TC39) 데코레이터로 읽는다.** 표준은 인자가 둘인데 이 함수는 셋이라 `TS1241` 이 났다.\
  진단 둘째 줄이 그 이유를 그대로 적는다 — 「The runtime will invoke the decorator with 2 arguments, but the decorator expects 3.」
- `--experimentalDecorators` 를 켜면 통과하고, 방출 **맨 앞에 `__decorate` 헬퍼 여섯 줄**이 붙는다 — 원본에 없던 코드다.
- 클래스 몸통에서 `@log` 가 빠지고 클래스 뒤에 `__decorate([log], Svc.prototype, "run", null);` 이 붙었다.
- 실행 첫 줄이 `호출: run` 인 것은 **데코레이터가 런타임에 실제로 돌았다**는 뜻이다.
- ★ 그래서 데코레이터는 「타입 층」이 아니다. **소거 대상이 아니라 번역 대상**이고, 코드를 **줄이는 게 아니라 늘린다**.

### 8. ★★★ 타입은 실행 시각에 없으니까 — `typeof`·`instanceof`·`in` 과 타입 술어로 대신한다

**출력**

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

**왜 그런가**

- ★★ `JSON.parse` 의 정적 반환 타입은 `any` 다. **문자열을 읽기 전에는 무엇이 들었는지 컴파일러가 알 수 없다.**
- 설령 `as User` 를 붙여도 방출에서 사라지므로 **실행 시각에는 아무 검사도 안 남는다**(1번의 방출 전문이 근거다).
- 그래서 쓰는 것이 셋이다 — **`typeof`**(원시 종류) · **`instanceof`**(클래스 · 프로토타입 사슬) · **`in`**(프로퍼티 존재).
- 그 셋을 타입 층에 잇는 것이 **타입 술어**(`v is User`)다. 몸통은 전부 JS 검사인데 **반환 타입 표기 하나로** 좁히기에 연결된다.
- 실행 출력이 그 결과다 — `bad` 는 `{"id":1}` 이라 `typeof o.id === "string"` 에서 걸려 `false` 가 됐다.
- `typeof null` 이 `"object"` 인 것은 JS 쪽 사실이다 — 그래서 `isUser` 가 `v !== null` 을 따로 본다.

### 9. ★★ 방출 **다섯 줄**(`var` 한 줄 + IIFE 네 줄) · 런타임에 **역매핑 객체**가 생긴다

**왜 그런가**

- 2번 블록에서 `enum Color` 하나가 방출에서 차지한 줄은 `var Color;` 와 IIFE 네 줄, 합해 **다섯 줄**이다.
- 그 객체는 **양방향**이다 — `Color["Red"] === 0` 이고 `Color[0] === "Red"` 다. 실행 출력 둘째 칸이 그 증거다.
- 대가는 셋이다 — ① 번들 크기 ② **트리 셰이킹이 안 먹는다**(IIFE 는 부수 효과로 보인다) ③ 숫자 `enum` 은 **범위 밖 숫자도 받는다**.
- ★ 대안은 유니온 리터럴 + `as const` 다. 방출이 **0줄**이고 타입만으로 같은 일을 한다(→ [목록의 **31번 주제**](../31-enum-pitfalls/)).

### 10. ★★ 이름이 사라지는 쪽은 **JS 의 `#`** · 매개변수 프로퍼티의 `private` 은 **`y;` 와 `this.y = y;` 두 줄**

**왜 그런가**

- 2번 방출 전문에서 `private y: number` 가 **`y;`** 라는 필드 선언과 **`this.y = y;`** 라는 대입으로 나왔다.\
  이름이 그대로라 실행 시각에 `obj["y"]` 로 읽힌다 — **감추지 않는다.**
- TS 의 `private` 은 **검사 시각의 접근 제어**일 뿐이다. 소거 대상이다.
- JS 의 `#` 는 **언어 차원의 진짜 비공개**다 — 방출된 파일에도 `#` 로 남고 밖에서 못 읽는다.
- ★ 타입 쪽에서도 둘이 다르다 — **`private` 멤버가 하나만 있어도 그 클래스는 구조적 타이핑에서 빠져나온다.** [**05번 주제**](../05-structural-typing/)가 정본이다.

### 11. ★★ 세 층

| 층 | 이 주제의 항목 |
|---|---|
| **언어 보장** | 타입 표기·`interface`·`type`·`as`·`satisfies` 는 **런타임 의미가 없다** · `enum`·`namespace`·매개변수 프로퍼티·레거시 데코레이터는 **JS 로 번역된다**(`TS1294` 다섯 건이 그 목록이다) · 타입 공간과 값 공간은 분리돼 있다(`TS2693`) |
| **이 판(7.0.2)·이 옵션의 관찰** | `enum` 이 **IIFE + 역매핑**이라는 **정확한 모양** · `const enum` 이 `0 /* Dir.Up */` 으로 **주석까지 붙여** 인라인되는 것 · `__decorate` 헬퍼의 **본문 여섯 줄** · 클래스 필드가 `x;` 로 선언되는 것(`target` 기본 es2025 · `useDefineForClassFields` 기본 `true` 에 달렸다) |
| **설정에 달린 것** | `Shape` 가 import 목록에서 **지워지는 것** — `verbatimModuleSyntax` 가 꺼져 있을 때만이다 · 레거시 데코레이터가 통과하는 것 — `experimentalDecorators` 를 켰을 때만이다 |

- ★ **「여러 번 돌려 같았다」는 보장이 아니다.** 방출 전문은 판과 옵션의 함수다. `target` 을 낮추면 클래스 필드 모양부터 바뀐다.

### 12. ★★★ 타입이 런타임에 없으니 **방출은 타입을 몰라도 할 수 있다**

**왜 그런가**

- 방출이 하는 일은 「**타입에만 속한 조각을 떼고 나머지를 JS 로 적는 것**」이다.
- 그 일에는 **타입이 맞는지 여부가 필요 없다.** `const label: string = 42` 에서 `: string` 을 떼면 `const label = 42;` 가 되고, 이것은 **완벽하게 유효한 JS** 다.
- 그래서 `tsc` 안에서 **검사 패스와 방출 패스가 서로를 기다리지 않는다** — 에러를 보고하면서도 파일을 쓴다.
- ★ 그 사실과 종료 코드가 어떻게 엮이는지가 [**02번 주제**](../02-type-checking-vs-emit/)의 본체다.

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` | `Version 7.0.2` · `v18.19.1` |
| 소거 전수 | `tsc --pretty false ex.01a.ts` 후 `ex.01a.js` 덤프 | exit 0 · 타입 층 **전부 사라짐** |
| 소거 가능성 | `tsc --erasableSyntaxOnly --noEmit ex.01a.ts` | exit 0 · **진단 0건** |
| 안 지워지는 것 | `tsc --pretty false ex.01b.ts` 후 덤프 + `node ex.01b.js` | exit 0 · IIFE 2벌 · 필드 2줄 · 실행 `0 Red 0 3 3` |
| 안 지워지는 것 전수 | `tsc --erasableSyntaxOnly --noEmit ex.01b.ts` | exit 1 · `TS1294` **5건** |
| 값 자리의 타입 이름 | `tsc --noEmit ex.01c.ts` | exit 1 · `TS2693` **2건** |
| 런타임 검사 | `tsc ex.01d.ts` 후 `node ex.01d.js` | exit 0 · 다섯 줄 출력 |
| import 소거 | `tsc --module esnext ex.01e.ts ex.01e-lib.ts` 후 덤프 | exit 0 · `Shape` 가 import 목록에서 빠짐 |
| 데코레이터(기본) | `tsc --noEmit ex.01f.ts` | exit 1 · `TS1241` 1건 |
| 데코레이터(레거시) | `tsc --experimentalDecorators ex.01f.ts` 후 덤프 + 실행 | exit 0 · `__decorate` 헬퍼 6줄 · 실행 `호출: run` / `42` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- `enum`·`namespace` 의 IIFE 모양, 매개변수 프로퍼티의 필드 방출 모양 — `target`·`useDefineForClassFields` 에 달렸다.
- `const enum` 인라인의 **주석 형식**(`0 /* Dir.Up */`).
- `__decorate` 헬퍼 본문.
- `--help --all` 이 `outFile`·`downlevelIteration` 을 **여전히 목록에 싣지만 실제로 주면 `TS5102` 로 거절한다** — 도움말과 실제가 어긋나 있으므로 옵션 유무는 **던져서** 확인한다.

**안 돌려 본 것**

- `target` 을 낮춘 방출(`--target es2015` 등) — 이 주제의 결론(무엇이 지워지나)은 `target` 과 무관하므로 생략했다. **모양**을 인용하는 자리에는 전부 「이 판의 관찰」로 표시했다.
