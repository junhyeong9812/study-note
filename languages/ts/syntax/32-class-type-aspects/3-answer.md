# ts/syntax/32 — 클래스의 타입 측면 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·격자·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 5번의 마지막 행은 **`tsc` 4.9.5** 를 환경변수(`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 3창(방출된 `.js` + `node`)이다** — 1번 격자와 2번 두 방출물이 결론을 낸다.\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 넷 다 **`x = 1;`** · `private` 도 `["x"]`·`{"x":1}` · `o["x"]` **컴파일된다** · `#x` 는 **`TS18013` + `SyntaxError`** · **10 / 30**, 전부 `#x` 두 행

**출력**

```text
===== bash ts30b-privgrid.sh (sh exit=0) =====
[public] x = 1;  (-t es2022)
    emit  x = 1;
    keys  ["x"]
    json  {"x":1}
    dot   1
    brack 1
    write [["x",9]]
[private] private x = 1;  (-t es2022)
    emit  x = 1;
    keys  ["x"]
    json  {"x":1}
    dot   (TS2341) 1
    brack 1
    write (TS2341) [["x",9]]
[protected] protected x = 1;  (-t es2022)
    emit  x = 1;
    keys  ["x"]
    json  {"x":1}
    dot   (TS2445) 1
    brack 1
    write (TS2445) [["x",9]]
[readonly] readonly x = 1;  (-t es2022)
    emit  x = 1;
    keys  ["x"]
    json  {"x":1}
    dot   1
    brack 1
    write (TS2540) [["x",9]]
[#x] #x = 1;  (-t es2022)
    emit  #x = 1;
    keys  []
    json  {}
    dot   (TS18013) SyntaxError
    brack (TS7053) undefined
    write (TS18013) SyntaxError
[#x@es2021] #x = 1;  (-t es2021)
    emit  constructor() { _Box_x.set(this, 1); }
    keys  []
    json  {}
    dot   (TS18013) SyntaxError
    brack (TS7053) undefined
    write (TS18013) SyntaxError

런타임에 값이 안 보이거나 막힌 칸 10 / 30
```

**왜 그런가**

| 행 | emit | keys · json | dot | brack | write |
|---|---|---|---|---|---|
| `public` | `x = 1;` | 보인다 | `1` | `1` | 쓴다 |
| `private` | ★★★ **`x = 1;`** | ★★★ **보인다** | `(TS2341) 1` | ★★★ **`1` — 진단 없음** | `(TS2341)` 쓴다 |
| `protected` | `x = 1;` | 보인다 | `(TS2445) 1` | `1` | `(TS2445)` 쓴다 |
| `readonly` | `x = 1;` | 보인다 | `1` | `1` | ★ `(TS2540)` **그래도 쓴다** |
| `#x` | `#x = 1;` | ★ **안 보인다** | ★ `SyntaxError` | `undefined` | ★ `SyntaxError` |
| `#x@es2021` | ★ WeakMap `set` | ★ **안 보인다** | ★ `SyntaxError` | `undefined` | ★ `SyntaxError` |

- ★★★ **TS 수식어 네 행의 실행 칸 스무 개 중 막힌 칸은 0** 이다.

### 2. ★★ 진단 **0줄** · `owner = "kim";` 과 **`#balance = 100;` 그대로** · es2021 은 **WeakMap** · `node` 다섯 줄 **같다**

**출력**

```ts
// ex.32a.ts
// TS private 와 JS # 을 한 클래스에 -- 방출물과 바깥에서 본 모습
class Account {
    private owner = "kim";
    #balance = 100;
    peek(): number {
        return this.#balance;
    }
}
const acc = new Account();
console.log("[1] keys ", Object.keys(acc));
console.log("[2] json ", JSON.stringify(acc));
console.log("[3] owner", acc["owner"]);
console.log("[4] peek ", acc.peek());
console.log("[5] spread", { ...acc });
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.32a.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e32a ex.32a.ts (tsc exit=0) =====
===== 방출된 e32a/ex.32a.js =====
"use strict";
// TS private 와 JS # 을 한 클래스에 -- 방출물과 바깥에서 본 모습
class Account {
    owner = "kim";
    #balance = 100;
    peek() {
        return this.#balance;
    }
}
const acc = new Account();
console.log("[1] keys ", Object.keys(acc));
console.log("[2] json ", JSON.stringify(acc));
console.log("[3] owner", acc["owner"]);
console.log("[4] peek ", acc.peek());
console.log("[5] spread", { ...acc });
```

```text
===== tsc --pretty false -t es2021 --strict --outDir e32a21 ex.32a.ts (tsc exit=0) =====
===== 방출된 e32a21/ex.32a.js =====
"use strict";
var __classPrivateFieldGet = (this && this.__classPrivateFieldGet) || function (receiver, state, kind, f) {
    if (kind === "a" && !f) throw new TypeError("Private accessor was defined without a getter");
    if (typeof state === "function" ? receiver !== state || !f : !state.has(receiver)) throw new TypeError("Cannot read private member from an object whose class did not declare it");
    return kind === "m" ? f : kind === "a" ? f.call(receiver) : f ? f.value : state.get(receiver);
};
var _Account_balance;
// TS private 와 JS # 을 한 클래스에 -- 방출물과 바깥에서 본 모습
class Account {
    constructor() {
        this.owner = "kim";
        _Account_balance.set(this, 100);
    }
    peek() {
        return __classPrivateFieldGet(this, _Account_balance, "f");
    }
}
_Account_balance = new WeakMap();
const acc = new Account();
console.log("[1] keys ", Object.keys(acc));
console.log("[2] json ", JSON.stringify(acc));
console.log("[3] owner", acc["owner"]);
console.log("[4] peek ", acc.peek());
console.log("[5] spread", { ...acc });
```

```text
===== node e32a/ex.32a.js (node exit=0) =====
[1] keys  [ 'owner' ]
[2] json  {"owner":"kim"}
[3] owner kim
[4] peek  100
[5] spread { owner: 'kim' }
```

```text
===== node e32a21/ex.32a.js (node exit=0) =====
[1] keys  [ 'owner' ]
[2] json  {"owner":"kim"}
[3] owner kim
[4] peek  100
[5] spread { owner: 'kim' }
```

**왜 그런가**

- ★★★ `private` 는 **사라지고**, `#` 는 JS 문법이라 **남는다.** 하향하면 `_Account_balance = new WeakMap()` + `__classPrivateFieldGet` 도우미가 금고 노릇을 한다.
- ★★ 두 판 모두 `owner` 는 `keys`·`json`·스프레드에 **나가고** `balance` 는 **안 나간다.**

### 3. ★★ **11행 `TS7006`** — `implements` 는 타입을 안 준다 · 생성자 몸통 **세 줄**(대입) · `implements` 는 **어디에도 없다** · `--erasableSyntaxOnly` 는 **`TS1294` 셋**

**출력**

```ts
// ex.32b.ts
// 매개변수 프로퍼티와 implements -- 방출물에 무엇이 남나
interface Shape {
    area(): number;
    scale(factor: number): void;
}
class Rect implements Shape {
    constructor(public w: number, private h: number, readonly tag = "rect") {}
    area(): number {
        return this.w * this.h;
    }
    scale(factor) {
        this.w *= factor;
    }
}
const r = new Rect(2, 3);
r.scale(2);
console.log(r.area(), Object.keys(r), r instanceof Rect);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.32b.ts (tsc exit=1) =====
ex.32b.ts(11,11): error TS7006: Parameter 'factor' implicitly has an 'any' type.
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e32b ex.32b.ts (tsc exit=2) =====
ex.32b.ts(11,11): error TS7006: Parameter 'factor' implicitly has an 'any' type.
===== 방출된 e32b/ex.32b.js =====
"use strict";
class Rect {
    w;
    h;
    tag;
    constructor(w, h, tag = "rect") {
        this.w = w;
        this.h = h;
        this.tag = tag;
    }
    area() {
        return this.w * this.h;
    }
    scale(factor) {
        this.w *= factor;
    }
}
const r = new Rect(2, 3);
r.scale(2);
console.log(r.area(), Object.keys(r), r instanceof Rect);
```

```text
===== node e32b/ex.32b.js (node exit=0) =====
12 [ 'w', 'h', 'tag' ] true
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.32b.ts (tsc exit=1) =====
ex.32b.ts(7,17): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.32b.ts(7,35): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.32b.ts(7,54): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.32b.ts(11,11): error TS7006: Parameter 'factor' implicitly has an 'any' type.
```

**왜 그런가**

- ★★★ 핸드북 — `implements` 는 **검사일 뿐** 클래스·메서드의 타입을 **전혀** 바꾸지 않는다. 그래서 `scale(factor)` 의 `factor` 는 **문맥 타입을 못 받고** `any` 로 추론돼 `TS7006`.
- ★★ 매개변수 프로퍼티 셋이 **`w; h; tag;`** + **`this.w = w;` 세 줄**로. 방출물 첫 줄은 `class Rect {` — `implements` 가 없다.
- ★★ `TS1294` 세 개는 7행의 **열 17·35·54** — 매개변수 프로퍼티 **하나에 하나씩**이다.

### 4. ★★ **20행 `TS2511`** 하나 · 방출물은 **평범한 `class Animal`** · `[2] TypeError this.sound is not a function` · `[3] object function`

**출력**

```ts
// ex.32c.ts
// abstract 클래스와 abstract 메서드 -- 방출물과 node
abstract class Animal {
    abstract sound(): string;
    greet(): string {
        return "I say " + this.sound();
    }
}
class Dog extends Animal {
    sound(): string {
        return "woof";
    }
}
console.log("[1]", new Dog().greet());
const Ctor = Animal as unknown as new () => Animal;
try {
    console.log("[2]", new Ctor().greet());
} catch (e) {
    console.log("[2]", (e as Error).constructor.name, (e as Error).message);
}
const direct = new Animal();
console.log("[3]", typeof direct, typeof direct.greet);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.32c.ts (tsc exit=1) =====
ex.32c.ts(20,16): error TS2511: Cannot create an instance of an abstract class.
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e32c ex.32c.ts (tsc exit=2) =====
ex.32c.ts(20,16): error TS2511: Cannot create an instance of an abstract class.
===== 방출된 e32c/ex.32c.js =====
"use strict";
// abstract 클래스와 abstract 메서드 -- 방출물과 node
class Animal {
    greet() {
        return "I say " + this.sound();
    }
}
class Dog extends Animal {
    sound() {
        return "woof";
    }
}
console.log("[1]", new Dog().greet());
const Ctor = Animal;
try {
    console.log("[2]", new Ctor().greet());
}
catch (e) {
    console.log("[2]", e.constructor.name, e.message);
}
const direct = new Animal();
console.log("[3]", typeof direct, typeof direct.greet);
```

```text
===== node e32c/ex.32c.js (node exit=0) =====
[1] I say woof
[2] TypeError this.sound is not a function
[3] object function
```

**왜 그런가**

- ★★★ `abstract` 와 `abstract sound()` 는 **방출물에 한 글자도 없다.** 그러니 `new Animal()` 은 **된다**(`[3]`), 없는 메서드를 부르는 `greet()` 가 **터진다**(`[2]`).
- ★ 14행은 `as unknown as` 로 넘겨 **진단조차 없다** — 30편의 이중 단언.

### 5. ★★★ es2022 — **`["x"] x 1` · `undefined` · `NaN`** · es2021 — **`[] x -1` · `base` · `42`** · setter 는 **대입 방출 판**에서만 · `es2021 + true` 의 `[3]` 은 **`42`** · **13 / 20**

**출력**

```ts
// ex.32d.ts
// 필드 선언이 방출물에서 무엇이 되나 -- 세 가지 클래스
class Parent {
    set x(v: number) {
        console.log("    (Parent setter got " + v + ")");
    }
    get x() {
        return -1;
    }
}
class Child extends Parent {
    x = 1;
}

class Base {
    name = "base";
}
class Redeclared extends Base {
    name!: string;
}

class Point {
    doubled = this.n * 2;
    constructor(public n: number) {}
}

const c = new Child();
console.log("[1] Child      own keys", JSON.stringify(Object.keys(c)), "x", c.x);
console.log("[2] Redeclared name    ", new Redeclared().name);
console.log("[3] Point      doubled ", new Point(21).doubled);
```

```text
===== bash ts30b-definegrid.sh (sh exit=0) =====
[7.0.2 -t es2022]
    진단   TS2610 TS2612 TS2729
    setter 호출 0번
    [1] Child      own keys ["x"] x 1
    [2] Redeclared name     undefined
    [3] Point      doubled  NaN
[7.0.2 -t es2021]
    진단   TS2610
    setter 호출 1번
    [1] Child      own keys [] x -1
    [2] Redeclared name     base
    [3] Point      doubled  42
[7.0.2 -t es2022 --useDefineForClassFields false]
    진단   TS2610
    setter 호출 1번
    [1] Child      own keys [] x -1
    [2] Redeclared name     base
    [3] Point      doubled  42
[7.0.2 -t es2021 --useDefineForClassFields true]
    진단   TS2610 TS2612
    setter 호출 0번
    [1] Child      own keys ["x"] x 1
    [2] Redeclared name     undefined
    [3] Point      doubled  42
[4.9.5 -t es2022]
    진단   TS2610 TS2612
    setter 호출 0번
    [1] Child      own keys ["x"] x 1
    [2] Redeclared name     undefined
    [3] Point      doubled  NaN

첫 행(7.0.2 -t es2022)과 갈린 칸 13 / 20
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e32d ex.32d.ts (tsc exit=2) =====
ex.32d.ts(11,5): error TS2610: 'x' is defined as an accessor in class 'Parent', but is overridden here in 'Child' as an instance property.
ex.32d.ts(18,5): error TS2612: Property 'name' will overwrite the base property in 'Base'. If this is intentional, add an initializer. Otherwise, add a 'declare' modifier or remove the redundant declaration.
ex.32d.ts(22,20): error TS2729: Property 'n' is used before its initialization.
===== 방출된 e32d/ex.32d.js =====
"use strict";
// 필드 선언이 방출물에서 무엇이 되나 -- 세 가지 클래스
class Parent {
    set x(v) {
        console.log("    (Parent setter got " + v + ")");
    }
    get x() {
        return -1;
    }
}
class Child extends Parent {
    x = 1;
}
class Base {
    name = "base";
}
class Redeclared extends Base {
    name;
}
class Point {
    n;
    doubled = this.n * 2;
    constructor(n) {
        this.n = n;
    }
}
const c = new Child();
console.log("[1] Child      own keys", JSON.stringify(Object.keys(c)), "x", c.x);
console.log("[2] Redeclared name    ", new Redeclared().name);
console.log("[3] Point      doubled ", new Point(21).doubled);
```

```text
===== tsc --pretty false -t es2021 --strict --useDefineForClassFields true --outDir e32d21 ex.32d.ts (tsc exit=2) =====
ex.32d.ts(11,5): error TS2610: 'x' is defined as an accessor in class 'Parent', but is overridden here in 'Child' as an instance property.
ex.32d.ts(18,5): error TS2612: Property 'name' will overwrite the base property in 'Base'. If this is intentional, add an initializer. Otherwise, add a 'declare' modifier or remove the redundant declaration.
===== 방출된 e32d21/ex.32d.js =====
"use strict";
// 필드 선언이 방출물에서 무엇이 되나 -- 세 가지 클래스
class Parent {
    set x(v) {
        console.log("    (Parent setter got " + v + ")");
    }
    get x() {
        return -1;
    }
}
class Child extends Parent {
    constructor() {
        super(...arguments);
        Object.defineProperty(this, "x", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: 1
        });
    }
}
class Base {
    constructor() {
        Object.defineProperty(this, "name", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: "base"
        });
    }
}
class Redeclared extends Base {
    constructor() {
        super(...arguments);
        Object.defineProperty(this, "name", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
    }
}
class Point {
    constructor(n) {
        Object.defineProperty(this, "n", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: n
        });
        Object.defineProperty(this, "doubled", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: this.n * 2
        });
    }
}
const c = new Child();
console.log("[1] Child      own keys", JSON.stringify(Object.keys(c)), "x", c.x);
console.log("[2] Redeclared name    ", new Redeclared().name);
console.log("[3] Point      doubled ", new Point(21).doubled);
```

**왜 그런가**

| 판 | setter | `[1]` | `[2]` | `[3]` | 진단 |
|---|---|---|---|---|---|
| 7.0.2 `es2022` | 0번 | `["x"] x 1` | `undefined` | ★ `NaN` | `TS2610 TS2612 TS2729` |
| 7.0.2 `es2021` | ★ 1번 | `[] x -1` | `base` | `42` | `TS2610` |
| `es2022` + `false` | ★ 1번 | `[] x -1` | `base` | `42` | `TS2610` |
| `es2021` + `true` | 0번 | `["x"] x 1` | `undefined` | ★★★ **`42`** | `TS2610 TS2612` |
| 4.9.5 `es2022` | 0번 | `["x"] x 1` | `undefined` | `NaN` | ★ `TS2610 TS2612` |

- ★★★ `[3]` 의 `NaN` 은 **네이티브 필드로 방출됐을 때만** 난다 — 필드 초기자가 **생성자 몸통의 `this.n = n` 보다 먼저** 돈다. `es2021 + true` 는 `defineProperty` 두 번을 **`n` 먼저** 적어 `42`.

### 6. ★★★ 방출물에서 `private` 가 **사라져** `x = 1;` 이 되기 때문 — 막는 것은 **컴파일러의 점 접근**뿐

- ★★ 1번 `emit` 열이 `public` 행과 **같은 글자**다. 실행 세계에는 두 클래스가 **같은 코드**다.
- ★★★ 그리고 컴파일러도 **점 접근(`o.x`)만** 막는다 — `o["x"]` 는 통과(`brack` 열). 핸드북이 이것을 「soft private」라 부른다.

### 7. ★★ **문법 강제**다 — 런타임 `TypeError` 는 **클래스 안 코드가 칸 없는 객체를 읽을 때**

- ★★★ 클래스 **바깥**에서 `o.#x` 를 쓰는 것 자체가 JS 문법 에러라, 방출물은 **파싱 단계에서** 멈춘다 — 파일의 어떤 줄도 안 돈다.
- ★★ JS 갈래 [`../../../js/syntax/16-class-syntax/`](../../../js/syntax/16-class-syntax/) 5절 — **클래스 안의 정적 메서드**가 `Object.create(…)`·`new Proxy(…)` 처럼 **칸이 없는 객체**를 읽으면 `TypeError`「Cannot read private member #balance from an object whose class did not declare it」. **그것이 런타임 브랜드 검사**다. 여기서는 **다시 재지 않았다.**

### 8. ★★ 하는 일 — 클래스가 인터페이스 모양을 **만족하는지 검사** · 안 하는 일 — **타입을 주는 것**과 **방출물에 남는 것**

- ★ 3번 `TS7006` — `Shape.scale(factor: number)` 가 있어도 `factor` 는 타입을 못 받았다.
- ★ 3번 방출물 — `class Rect {`.

### 9. ★★ **컴파일 세계에서만** — 넘기면 **없는 추상 메서드를 부를 때** `TypeError`

- ★★★ 4번 — `new Animal()` 의 `TS2511` 은 **컴파일러의 규칙**이다. 방출물은 평범한 클래스라 `new` 가 되고(`[3]`), `greet()` 안의 `this.sound()` 가 **없는 함수**라 `[2]` 에서 터진다.

### 10. ★★ es2022 판은 **(가) 정의** · es2021 판은 **(나) 대입** · `w; h; tag;` 는 **클래스 필드 선언**(JS 의 필드 문법)

- ★★★ JS 16편 4절 — (가) 필드 `x = 1` 은 **setter 호출 0, own 키 `["x"]`**, (나) 생성자 `this.x = 1` 은 **setter 호출 1, own 키 `["_x"]`**.
  5번 `es2022` 판의 `[1] own keys ["x"] x 1` 은 (가), `es2021` 판의 `[1] own keys [] x -1` 은 (나)다 — own 키가 `[]` 인 것은 이 부모 setter 가 **`_x` 에 안 쓰고 로그만 찍기** 때문이다.
- ★ `w; h; tag;` — 초기자 없는 **네이티브 필드 선언**. `-t es2022` + 정의 방출이라 남았다.

### 11. ★★ 기본값은 **타깃**에 달렸다 — **`es2021`** 행과 **`es2022 --useDefineForClassFields false`** 행 · 진단 칸만 다른 것은 **컴파일러 판**의 차이

- ★★★ `-t es2021` 과 `-t es2022 --useDefineForClassFields false` 가 **다섯 칸이 한 글자도 같다** → es2021 의 기본값은 `false`. 첫 행과 `es2021 + true` 가 `[1]`·`[2]` 에서 같다 → es2022 의 기본값은 `true`.
- ★★ 4.9.5 는 실행 세 줄이 7.0.2 와 같고 **`TS2729` 만 없다** — **언어(방출 의미)는 같고 진단이 늘었다.** 이 판의 관찰이다.

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.32a.ts    exit 0 = exit 0 · 출력 한 글자도 같다
ex.32b.ts    exit 1 = exit 0 · ★ 출력이 다르다
ex.32c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.32d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

```text
===== diff <(tsc --pretty false --noEmit -t es2022 --strict ex.32b.ts) <(tsc --pretty false --noEmit -t es2022 --strict false ex.32b.ts) (sh exit=1) =====
1d0
< ex.32b.ts(11,11): error TS7006: Parameter 'factor' implicitly has an 'any' type.
```

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `node --version` · `python3 --version` | `Version 7.0.2` · `v18.19.1` · `Python 3.12.3` |
| ★★★ `private` 대 `#` 격자 | `bash ts30b-privgrid.sh` (6 × 6 칸) | exit 0 · **10 / 30** — 전부 `#x` 행 |
| 두 방출물 | `--outDir e32a` · `-t es2021 --outDir e32a21` · `node` 두 번 | 진단 0줄 · `node` 다섯 줄 **같다** |
| 매개변수 프로퍼티·`implements` | `--noEmit`·`--outDir e32b`·`node`·`--erasableSyntaxOnly` | `TS7006` 1건 · 대입 세 줄 · `TS1294` 세 개 |
| `abstract` | `--noEmit`·`--outDir e32c`·`node` | `TS2511` 1건 · `[2] TypeError` |
| ★★★ 필드 방출 판 격자 | `bash ts30b-definegrid.sh` (다섯 판) | exit 0 · **13 / 20** |
| `strict` 대조 | 네 파일을 `--strict false` 로 재실행 | **`ex.32b.ts` 만** — `TS7006` 이 사라짐 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ `useDefineForClassFields` 의 **기본값**(타깃 경계) — TSConfig 페이지 본문에 문장이 없어 **던져서** 얻었다.
- ★★ `es2021 + true` 판의 **정의 순서**(매개변수 프로퍼티 먼저) — 방출기의 선택이다.
- ★ `TS2729` 가 있느냐 — 4.9.5 에는 없었다.

**안 돌려 본 것**

- ★★ **WeakMap 하향 방출의 브랜드 검사를 깨뜨리는 코드**(칸 없는 객체에 `__classPrivateFieldGet`) — 방출물에서 **읽기만** 했다.
- ★★ **`declare name: string`** — `name!` 대신 쓰면 `"base"` 가 남을 것으로 **예상만** 한다.
- ★ **`private` 멤버가 있는 클래스의 명목적 호환성** — 던지지 않았다.
