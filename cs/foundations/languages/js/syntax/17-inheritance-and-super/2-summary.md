# js/syntax/17 — 상속과 `super`: 「`super` 는 정의된 자리를 기억하고, `this` 는 부른 자리를 따른다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `super.who()` 의 **값**은 `Animal.who` 라고만 답한다 — 그 값이 **누구의 윗집에서 왔는지, 누구를 수신자로 넘겼는지**는 한 글자도 말하지 않는다.
> 그래서 부모 칸을 `Proxy` 로 감싸 트랩 로그를 찍었다 — `guest.m()` 은 **윗집 관계가 전혀 없는** 부모 칸에 `get(who)` 를 묻고, 수신자로 **`guest`** 를 넘긴다.
> 부모 생성자 안에서 자식 메서드가 **무엇을 보나**도 같은 창이다 — 생성 순서를 **번호 붙은 로그**로 찍었다(동작 (4)).
> ③ 브랜드 태그가 **내장 객체 상속의 판정 창**이고(`[object Array]` 대 `[object Object]`), ④ 예외 문구가 `super()` 규칙 셋을 가른다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — `ClassDefinitionEvaluation`(부모 칸 두 개를 고르는 자리) · 기본 생성자의 동작 · `MakeMethod` · `DefineField`.
>   ★ 멀티페이지의 함수·클래스 절([ecmascript-language-functions-and-classes](https://tc39.es/ecma262/multipage/ecmascript-language-functions-and-classes.html))을 받아 **문장을 grep 해서** 확인했다.
>   `GetSuperBase`·`MakeSuperPropertyReference`·`GetSuperConstructor` 는 **이름만** 목차에서 확인했다(본문은 열지 않았다).
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — `class`·`extends`·`super`·`new.target`·`Symbol.species` 가 ES2015, 필드·`Error` `cause` 가 ES2022 인 것을 가릴 때
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 클래스 필드·`#private`·`Error` `cause` 의 판
> - [MDN — `super`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/super) · [MDN — `extends`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes/extends) · [MDN — `new.target`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/new.target)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·로그·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ 예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만 찍는다 — 스택트레이스는 한 줄도 없다. 모든 블록은 표준 출력뿐이다.
>
> **버전** — 판 경계는 아래 표 하나다. 첫 블록이 **두 판 모두 ES2022 클래스 문법과 `Error` `cause` 를 갖고 있음**을 찍는다.
>
> | 무엇 | 판 |
> |---|---|
> | `class` · `extends` · `super` · `new.target` · `Symbol.species` | **ES2015** |
> | 공개/`#private` 필드 · `#x in obj` · `Object.hasOwn` · `Error` 의 `cause` 옵션 | **ES2022** |
> | `__proto__:` 리터럴(동작 (3)의 객체 리터럴 예) | **Annex B**([13번](../13-object-literals-and-properties/2-summary.md)이 정본) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | 부모 칸의 `get` 트랩이 `super.who()` 의 **질문 상대와 수신자**를 찍는다 · 부모 생성자 안의 가상 호출을 **번호 붙은 생성 로그**로 찍는다 |
> | ★★★ **③ 브랜드 태그** `Object.prototype.toString.call` | **내장 상속의 판정 창이다.** `class extends Array` 는 `[object Array]`, 옛 방식은 `[object Object]` — 그런데 옛 방식도 `instanceof Array` 는 `true` 다. **`instanceof` 가 속는 자리에서 브랜드만 바른 답을 한다** |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `ReferenceError` 두 문구(`super()` 전 `this` · 두 번 호출) · `TypeError` 넷(원시 반환 · `extends null` · `#private` 미설치 · 추상 클래스 흉내) · `SyntaxError` 한 문구(`super` 를 못 쓰는 자리) |
> | ★ **② 전수 격자** | 작게만 쓴다 — `super()` 를 **전에 / 안 / 두 번** 부르는 것과 **무엇을 반환하나** 의 칸을 한 블록에 모았다 |
> | ★ **⑤ 두 판 대조기** | 이 주제의 블록은 **두 판에서 전부 identical** 이다 |
> | ★★ **창을 바꿔 물었다**(제5의 상태) | 부모 생성자 안에서 자식의 `#label` 을 읽으면 **값 창이 `TypeError` 로 닫힌다.** 그래서 [16번](../16-class-syntax/2-summary.md)의 브랜드 검사 `#label in this` 로 바꿔 물었다 — `false`, 즉 「`undefined` 인 칸」이 아니라 「**칸이 아직 없다**」 |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 는 두 줄 있지만 묻는 것이 「**어디에 묶이나**」가 아니라 「**컴파일되나**」다. `compiles` 와 `SyntaxError` 한 단어로 답이 나서 **가를 열이 없다** |
> | ★ **부적용 — 파이썬 MRO 창** | JS 는 **단일 상속**이다. 조상을 한 줄로 세울 일이 없어 `__mro__` 에 해당하는 물건이 **없다** — 잴 것이 없다(동작 (6)) |
> | ★ **안 쟀다 — 성능** | 「`super` 호출은 느리다」·「내장 상속은 느리다」 같은 말을 **한 줄도 쓰지 않는다** |
> | ★ **안 돌렸다 — 브라우저** | 이 배치는 Node 두 판만 돌렸다 |
> | ★ **안 돌렸다 — 두 번 컴파일**(엄격/비엄격) | 클래스 몸통은 **언제나 엄격**이라(16번) 클래스 쪽에는 비엄격 판이 없다. 객체 리터럴 메서드의 `super` 는 비엄격 파일에서만 돌렸다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(V8 — 판이 오르면 바뀐다) | ★★★ **예외의 종류** · 트랩 로그의 **질문 상대와 수신자** |
> | ★★ `e.stack` 의 **존재와 첫 줄** — **ECMA-262 에 없다** | ★★★ **생성 로그의 순서** · 체인을 글자로 찍은 줄 |
> | `own keys of e2` 에 `stack` 이 끼는 것(엔진) | ★★ **브랜드 태그** `[object Array]` · `[object Error]` · `[object Map]` |
>
> ★★ **주소도 시간도 난수도 한 곳도 안 찍힌다.** 두 판 대조기의 마지막 줄 —
`identical 22  ·  differs 1  ·  total 23`
> ★ 갈린 한 블록은 [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)의 것이다. 이 주제의 블록은 **전부 identical** 이다.
>
> **선행** — [16 — `class` 문법](../16-class-syntax/2-summary.md) · [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md).
> ★★★ **15번의 결론을 그대로 받아 쓴다** — 「**탐색은 체인을 타고, 값은 수신자에 떨어진다**」 · 「**체인 위 setter 의 `this` 는 수신자**」.
> `super.who()` 는 **탐색의 출발점만 바꾼 조회**이고, 수신자 규칙은 15번과 같다. 동작 (3)의 트랩 로그가 그것을 보인다.
> ★★★ **07번과 정반대 자리가 이 주제의 급소다.** 07번은 「**떼어 붙이면 `this` 가 바뀐다**」였다. 여기는 「**떼어 붙여도 `super` 는 안 바뀐다**」다.
> ★★ **16번이 「멤버가 어디에 붙나」와 「필드 초기화 순서」의 정본**이다. 여기서는 **상속이 끼었을 때** 그 순서가 무슨 사고를 내나만 본다.
> **이어지는 곳** — [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) · [목록의 **22번 주제**](../22-symbol-and-well-known-symbols/) 「`Symbol` 과 잘 알려진 심볼」 · [목록의 **32번 주제**](../32-error-handling-and-error/) 「오류 처리와 `Error`」 · [목록의 **34번 주제**](../34-type-checking-idioms/) 「타입 검사 관용구」 · [목록의 **45번 주제**](../45-proxy/) 「`Proxy`」 · [목록의 **46번 주제**](../46-reflect/) 「`Reflect`」
>
> ★★ **경계 — 체인 조회 규칙은 15번이 정본이다.** 여기서는 **`extends` 가 체인에 무엇을 잇나**와 **`super` 가 체인의 어디서 출발하나**만 본다.
> ★★ **경계 — `Error` 의 `throw`/`catch` 흐름과 `cause` 의 쓰임은 32번**, **`Symbol.species` 가 속한 잘 알려진 심볼 전체는 22번**, **`Proxy` 트랩의 계약은 45번**이 정본이다.

```sh
# js16b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 그리고 ES2022 클래스 문법이 두 판에 다 있는지.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    const has = (src) => { try { new Function(src); return "yes"; } catch (e) { return "no"; } };
    console.log("node " + v.node + "  v8 " + v.v8 +
      "  fields " + has("class A { x = 1; static y = 2 }") +
      "  #private " + has("class A { #x; m(o) { return #x in o } }") +
      "  static{} " + has("class A { static { } }") +
      "  hasOwn " + typeof Object.hasOwn +
      "  errorCause " + String(new Error("m", { cause: 1 }).cause === 1));'
done
```
```text
===== ./js16b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  fields yes  #private yes  static{} yes  hasOwn function  errorCause true
node 20.19.6  v8 11.3.244.8-node.33  fields yes  #private yes  static{} yes  hasOwn function  errorCause true
```

## 한눈에 — 쉽게 말하면

**메서드는 태어날 때 「출생지 도장」을 받는다.** 클래스 몸통이나 객체 리터럴 안에서 메서드 문법으로 적힌 함수는
**자기가 적힌 객체**(`Dog.prototype`)를 기억한다. 이 기억이 `[[HomeObject]]` 다.

- **`this`** — 「**지금 누가 불렀나**」. 부르는 순간 점 왼쪽으로 정해진다(07번).
- **`super`** — 「**내가 태어난 집의 윗집**」. 정의하는 순간 도장이 찍히고, **누가 부르든 그 도장을 본다.**

```text
   메서드를 다른 집에 빌려주면 -- 무엇이 따라가고 무엇이 남나

   class Dog extends Animal { describe() { ... this ... super.who() ... } }

     Dog.prototype ──(윗집)──▶ Animal.prototype      who() = "Animal.who"
        ▲
        │ 출생지 도장 [[HomeObject]]   (태어날 때 찍힌다 -- 바뀌지 않는다)
        │
     describe  ─── 빌려준다 ───▶  toaster.describe = Dog.prototype.describe

     toaster ──(윗집)──▶ Toaster.prototype ──▶ Robot.prototype   who() = "Robot.who"

     toaster.describe()
        this  = toaster              ← 부른 자리 (점 왼쪽)
        super = Animal.prototype     ← 도장의 윗집. toaster 의 윗집 Robot 은 안 본다
```

★★★ **이 한 장이 이 주제의 전부다.** `this` 는 **따라가고**, `super` 는 **남는다.**
그래서 `toaster.describe()` 가 `this=toaster  super.who()=Animal.who` 를 찍는다(동작 (3)).

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 출생지 도장 | 메서드의 `[[HomeObject]]` | 직접 못 읽는다. **떼어 붙여 보고** `super` 가 어디로 가나 본다 |
| 도장의 윗집 | `Object.getPrototypeOf(HomeObject)` | `super.x` 가 찾기 시작하는 칸 |
| 지금 부른 사람 | `this`(수신자) | 07번의 네 규칙 |
| 윗집이 둘 | `extends` 가 잇는 두 사슬 | 인스턴스 쪽 `B.prototype → A.prototype` · 생성자 쪽 `B → A` |
| 집을 짓는 쪽 | 파생 클래스에서는 **부모 생성자** | `super()` 전에는 `this` 가 없다 |
| 누가 공사를 주문했나 | `new.target` | `new` 에 적힌 그 클래스 |
| 진짜 배열 인증서 | 브랜드 태그 `[object Array]` | `Object.prototype.toString.call` |

> **`[[HomeObject]]`** — 메서드 문법으로 정의된 함수가 **자기가 정의된 객체**를 기억하는 내부 슬롯.\
> 예: `Dog.prototype.describe` 의 HomeObject 는 `Dog.prototype` 이다. 그래서 그 안의 `super` 는 `Animal.prototype` 에서 찾기 시작한다.

> **파생 클래스(derived class)** — `extends` 가 붙은 클래스. **객체를 자기가 만들지 않고 부모 생성자에게 만들게 한다.**\
> 예: `class Stack extends Array` 의 인스턴스는 `Array` 생성자가 만든다. 그래서 **진짜 배열**이다.

> **`new.target`** — 생성자 안에서 「`new` 가 **어느 클래스 이름으로** 불렸나」.\
> 예: `new Circle()` 이면 부모 `Shape` 의 생성자 안에서도 `new.target` 이 `Circle` 이다. 일반 호출이면 `undefined` 다.

## 이 주제가 답하려는 질문

1. **`class B extends A` 는 무엇과 무엇을 잇나** — 그리고 그것 때문에 **정적 메서드까지 상속되는 이유**는?
2. ★★★ **`super.m()` 은 누구에게 묻고 누구를 수신자로 넘기나** — 메서드를 떼어 붙이면 **무엇이 바뀌고 무엇이 안 바뀌나**?
3. **파생 생성자는 왜 `super()` 전에 `this` 를 못 쓰나** — 그 규칙이 **내장 객체 상속**과 **부모 생성자 속 가상 호출**에서 각각 무슨 결과를 내나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★ 체인이 두 줄이다 — 인스턴스 쪽과 생성자 쪽

**언제 쓰나** — 「정적 메서드가 왜 자식 클래스에서도 불리지?」·「옛날 `function` 상속 코드를 `class` 로 옮기면 무엇이 달라지지?」를 물을 때.

```js
// js16b-17a-two-chains.js
// class B extends A 가 만드는 체인 -- 인스턴스 쪽과 생성자 함수 쪽을 둘 다 찍는다.
const nameOf = (o) => {
  if (o === null) return "null";
  if (o === Object.prototype) return "Object.prototype";
  if (o === Function.prototype) return "Function.prototype";
  for (const [n, v] of Object.entries(known)) if (o === v) return n;
  return "(anonymous)";
};
const chain = (o) => { const out = []; for (let p = o; p !== null; p = Object.getPrototypeOf(p)) out.push(nameOf(p)); out.push("null"); return out.join(" -> "); };

class A {
  hello() { return "A.hello"; }
  static create() { return "A.create called on " + this.name; }
}
class B extends A {}
class Plain {}
const known = { A, B, Plain, "A.prototype": A.prototype, "B.prototype": B.prototype, "Plain.prototype": Plain.prototype, "new B()": null };
const b = new B();
known["new B()"] = b;

console.log("[1] the instance side");
console.log("  " + chain(b));
console.log("[2] the constructor side");
console.log("  " + chain(B));
console.log("  " + chain(Plain) + "   <- a class without extends");

console.log("");
console.log("[3] a static method defined on A, called through B");
console.log("  B.create()                 -> " + B.create());
console.log("  Object.hasOwn(B, 'create') -> " + Object.hasOwn(B, "create"));
console.log("  b.hello()                  -> " + b.hello() + "   own? " + Object.hasOwn(b, "hello"));

console.log("");
console.log("[4] the same two links, written by hand for old-style functions");
function OldA() {}
function OldB() {}
Object.setPrototypeOf(OldB.prototype, OldA.prototype);
console.log("  only the instance link:      Object.getPrototypeOf(OldB) === OldA ? " + (Object.getPrototypeOf(OldB) === OldA));
Object.setPrototypeOf(OldB, OldA);
console.log("  after setPrototypeOf(OldB, OldA):                    === OldA ? " + (Object.getPrototypeOf(OldB) === OldA));

console.log("");
console.log("[5] extends null");
class N extends null {}
console.log("  chain of N.prototype       " + (Object.getPrototypeOf(N.prototype) === null ? "N.prototype -> null" : "?"));
console.log("  Object.getPrototypeOf(N) === Function.prototype ? " + (Object.getPrototypeOf(N) === Function.prototype));
try { new N(); console.log("  new N()  -> ok"); } catch (e) { console.log("  new N()  -> " + e.constructor.name + " " + e.message); }
class N2 extends null { constructor() { return Object.create(N2.prototype); } }
const n2 = new N2();
console.log("  new N2() with `return Object.create(N2.prototype)` -> instanceof N2 " + (n2 instanceof N2) + ", has toString? " + ("toString" in n2));
```
```text
===== node20 js16b-17a-two-chains.js (exit=0) =====
[1] the instance side
  new B() -> B.prototype -> A.prototype -> Object.prototype -> null
[2] the constructor side
  B -> A -> Function.prototype -> Object.prototype -> null
  Plain -> Function.prototype -> Object.prototype -> null   <- a class without extends

[3] a static method defined on A, called through B
  B.create()                 -> A.create called on B
  Object.hasOwn(B, 'create') -> false
  b.hello()                  -> A.hello   own? false

[4] the same two links, written by hand for old-style functions
  only the instance link:      Object.getPrototypeOf(OldB) === OldA ? false
  after setPrototypeOf(OldB, OldA):                    === OldA ? true

[5] extends null
  chain of N.prototype       N.prototype -> null
  Object.getPrototypeOf(N) === Function.prototype ? true
  new N()  -> TypeError Super constructor null of N is not a constructor
  new N2() with `return Object.create(N2.prototype)` -> instanceof N2 true, has toString? false
```

```text
   class B extends A {}  이 한 줄이 잇는 두 사슬

   인스턴스 쪽 (메서드)            생성자 쪽 (정적 멤버)
   new B()                         B
     │                             │
     v                             v
   B.prototype                     A              ← ★ B 의 윗집이 A 자신이다
     │                             │
     v                             v
   A.prototype   hello()           Function.prototype
     │                             │
     v                             v
   Object.prototype                Object.prototype
     │                             │
     v                             v
   null                            null
```

**그림 해설 — 한 덩어리에 한 문장.**

- ★★★ **`[1]` 과 `[2]` 가 두 사슬이다.** 15번이 「`extends` 가 체인을 두 줄 만든다」까지 봤고, 여기서 **왜 두 줄이어야 하나**를 `[3]` 이 답한다.
- ★★★ **`[3]` — 정적 메서드는 생성자 쪽 사슬로 상속된다.** `B.create()` 가 `A.create called on B` 를 찍는다.
  `Object.hasOwn(B, 'create')` 가 `false` 이니 **`B` 는 빌려 본 것**이고(15번의 조회), 그 안의 `this` 는 **수신자 `B`** 다(15번의 수신자 규칙).
  ★ 그래서 `static create() { return new this() }` 류의 팩토리가 **자식 클래스에서 자식을 만든다.**
- ★ `Plain` 줄이 대조군이다 — `extends` 가 없으면 생성자의 윗집은 곧장 `Function.prototype` 이다.
- ★★ **`[4]` — 옛 방식은 두 링크를 손으로 따로 건다.** `setPrototypeOf(OldB.prototype, OldA.prototype)` 만 하면 **인스턴스 쪽만** 이어지고
  `Object.getPrototypeOf(OldB) === OldA` 는 `false` 다. 두 번째 `setPrototypeOf(OldB, OldA)` 를 해야 `true` 가 된다.
  ★ 옛 코드가 **정적 멤버 상속을 흔히 빠뜨린** 이유가 이 한 줄이다.
- ★★ **`[5]` — `extends null` 은 인스턴스 쪽 사슬만 끊는다.** `N.prototype -> null` 이지만 생성자 쪽은 `Function.prototype` 그대로다.
  명세가 정확히 그렇게 적는다 — *"If superclass is null, then Let protoParent be null. Let ctorParent be %Function.prototype%."*
- ★★★ **그런데 `new N()` 은 `TypeError` 다** — `Super constructor null of N is not a constructor`.
  `extends` 가 붙은 이상 **파생 클래스**이고, 암묵 생성자가 `super(...args)` 처럼 **생성자 쪽 윗집을 부르려 한다.**
  명세의 기본 생성자 단계가 *"Let func be ! ctorFunc.[[GetPrototypeOf]](). If IsConstructor(func) is false, throw a TypeError exception."* 다 —
  그 윗집이 `Function.prototype` 이라 생성자가 아니다.
  ★ **문구는 `null` 이라 말하고 사슬은 `Function.prototype` 을 가리킨다** — 문구는 V8 이 소스의 `extends null` 을 옮긴 것이다.
- ★ 살리는 길은 **객체를 직접 반환하는 것**이다. `N2` 는 `Object.create(N2.prototype)` 을 반환해 `instanceof N2` 가 `true` 이고,
  **`toString` 이 없다**(`Object.prototype` 이 사슬에 없다). 「`Object.create(null)` 을 클래스로 만든 것」이다.

**비용** — 두 사슬을 오가는 조회의 비용은 **재지 않았다.**

### (2) ★★ `super()` — 파생 클래스에서는 부모가 집을 짓는다

**언제 쓰나** — 파생 생성자를 처음 쓸 때 만나는 두 `ReferenceError` 를 풀 때. 그리고 「생성자가 다른 객체를 반환하면?」을 물을 때.

```js
// js16b-17b-super-call.js
// 파생 클래스 생성자의 규칙 -- super() 를 언제, 몇 번, 안 부르면. 전부 던져서 문구까지 찍는다.
const run = (label, fn) => {
  let r;
  try { r = "-> " + fn(); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(52) + r);
};
class Base { constructor(v) { this.v = v; } }

console.log("[1] this before super()");
class ThisFirst extends Base { constructor() { this.early = 1; super(1); } }
run("this.early = 1; super(1)", () => { new ThisFirst(); return "ok"; });
class ArrowFirst extends Base { constructor() { const peek = () => this; peek(); super(1); } }
run("an arrow reads this before super()", () => { new ArrowFirst(); return "ok"; });

console.log("");
console.log("[2] never calling super()");
class NoSuper extends Base { constructor() {} }
run("constructor() {}", () => { new NoSuper(); return "ok"; });
class NoSuperReturnsObj extends Base { constructor() { return { replaced: true }; } }
run("constructor() { return { replaced: true } }", () => JSON.stringify(new NoSuperReturnsObj()));
run("  ...is it an instance of the class?", () => String(new NoSuperReturnsObj() instanceof NoSuperReturnsObj));
class NoSuperReturns7 extends Base { constructor() { return 7; } }
run("constructor() { return 7 }", () => { new NoSuperReturns7(); return "ok"; });
class Returns7AfterSuper extends Base { constructor() { super(1); return 7; } }
run("super(1); return 7", () => { new Returns7AfterSuper(); return "ok"; });
class PlainReturns7 { constructor() { this.a = 1; return 7; } }
run("base class: this.a = 1; return 7", () => JSON.stringify(new PlainReturns7()));

console.log("");
console.log("[3] calling super() twice");
class Twice extends Base { constructor() { super(1); super(2); } }
run("super(1); super(2)", () => { new Twice(); return "ok"; });

console.log("");
console.log("[4] the implicit constructor forwards every argument");
class Implicit extends Base {}
run("new Implicit(42).v", () => String(new Implicit(42).v));
run("Implicit.length", () => String(Implicit.length));

console.log("");
console.log("[5] new.target -- which class did `new` name?");
class Shape {
  constructor() {
    if (new.target === Shape) throw new TypeError("Shape is abstract");
    this.kind = new.target.name;
  }
}
class Circle extends Shape {}
run("new Shape()", () => { new Shape(); return "ok"; });
run("new Circle().kind", () => new Circle().kind);
function Legacy() { return new.target === undefined ? "called without new" : "called with new"; }
run("Legacy()", () => Legacy());
run("new Legacy()  (returns an object, not the string)", () => typeof new Legacy());
```
```text
===== node20 js16b-17b-super-call.js (exit=0) =====
[1] this before super()
this.early = 1; super(1)                            -> ReferenceError Must call super constructor in derived class before accessing 'this' or returning from derived constructor
an arrow reads this before super()                  -> ReferenceError Must call super constructor in derived class before accessing 'this' or returning from derived constructor

[2] never calling super()
constructor() {}                                    -> ReferenceError Must call super constructor in derived class before accessing 'this' or returning from derived constructor
constructor() { return { replaced: true } }         -> {"replaced":true}
  ...is it an instance of the class?                -> false
constructor() { return 7 }                          -> TypeError Derived constructors may only return object or undefined
super(1); return 7                                  -> TypeError Derived constructors may only return object or undefined
base class: this.a = 1; return 7                    -> {"a":1}

[3] calling super() twice
super(1); super(2)                                  -> ReferenceError Super constructor may only be called once

[4] the implicit constructor forwards every argument
new Implicit(42).v                                  -> 42
Implicit.length                                     -> 0

[5] new.target -- which class did `new` name?
new Shape()                                         -> TypeError Shape is abstract
new Circle().kind                                   -> Circle
Legacy()                                            -> called without new
new Legacy()  (returns an object, not the string)   -> object
```

```text
   파생 생성자 안의 시간 -- this 는 super() 가 돌려줘야 생긴다

   constructor() {
     ...                   this 없음   읽으면 ReferenceError (화살표로 읽어도)
     super(args)  ───────▶ 부모 생성자가 객체를 만든다   (new.target 의 prototype 으로)
                  ◀─────── 그 객체가 this 가 된다
     ...                   this 있음
     super(args)  ───────▶ ReferenceError 로 막힌다 (두 번째)
   }
   끝날 때:  this 를 한 번도 못 받았으면        ReferenceError
             원시값을 return 하면              TypeError  (super 뒤여도)
             객체를 return 하면                그 객체가 결과 -- 이 클래스의 인스턴스가 아닐 수 있다
```

**그림 해설.**

- ★★★ **`[1]` — `this` 는 `super()` 가 돌아와야 생긴다.** 먼저 쓰면 `ReferenceError` 이고 문구가 규칙을 그대로 말한다 —
  `Must call super constructor in derived class before accessing 'this' or returning from derived constructor`.
  ★ **화살표로 우회해도 같다** — 화살표의 `this` 는 둘러싼 생성자의 것이라(07번) 그 생성자의 `this` 가 아직 없다.
- ★★★ **왜 그런가 — 파생 클래스에서는 객체를 부모가 만든다.** 명세의 기본 생성자가 파생일 때
  *"Let result be ? Construct(func, args, NewTarget)."* 로 **부모에게 만들게 하고**, 기반일 때만
  *"OrdinaryCreateFromConstructor(NewTarget, ...)"* 로 **스스로 만든다.** 만들어지기 전의 객체는 가리킬 수가 없다.
  ★ 이 한 사실이 동작 (4)와 (5)를 **둘 다** 설명한다.
- ★★ **`[2]` — 안 부르면 끝날 때 같은 `ReferenceError`** 다(`constructor() {}`). 문구 뒷부분 「`or returning from derived constructor`」가 이 경우다.
  ★ **객체를 반환하면 `super()` 없이도 된다** — 결과는 `{"replaced":true}` 이고 **이 클래스의 인스턴스가 아니다**(`false`).
- ★★ **원시값 반환은 파생에서만 `TypeError`** 다 — `Derived constructors may only return object or undefined`. **`super(1)` 뒤여도** 같다.
  ★ **기반 클래스는 원시 반환을 조용히 무시한다** — `this.a = 1; return 7` 의 결과가 `{"a":1}` 이다. **같은 문장이 상속 유무로 갈린다.**
- ★★ **`[3]` — 두 번 부르면 `ReferenceError`** 다 — `Super constructor may only be called once`.
  ★ 부모 생성자는 **두 번째에도 돈다**고 봐야 할지, 막히기 전에 멈추는지는 이 블록이 **묻지 않았다.**
- ★ **`[4]` — 암묵 생성자는 인자를 전부 넘긴다**(`new Implicit(42).v` 가 `42`). 명세의 NOTE 가
  *"This branch behaves similarly to constructor(...args) { super(...args); }."* 다. **그런데 `Implicit.length` 는 `0`** 이다 — 받는 인자를 선언하지 않았다.
- ★★ **`[5]` — `new.target` 은 「`new` 에 적힌 클래스」** 다. 부모 `Shape` 의 생성자 안에서 읽어도 `Circle` 이라 `kind` 가 `Circle` 이 된다.
  그래서 `new.target === Shape` 이면 던지는 것으로 **추상 클래스를 흉내 낸다**(`Shape is abstract` 는 우리가 던진 문구다).
  ★ 일반 함수에서는 `new` 없이 부르면 `undefined` 다. `new Legacy()` 가 `object` 인 것은 **기반 생성자의 원시 반환 무시** 규칙 그대로다.

### (3) ★★★ `[[HomeObject]]` — `super` 는 도장을 본다

**언제 쓰나** — 메서드를 **믹스인·위임·재사용**으로 다른 객체에 옮겨 붙일 때. 「옮겼더니 `super` 가 엉뚱한 부모를 부른다」가 나는 자리다.
★★★ **값으로는 반만 보인다** — `super.who()` 는 `Animal.who` 라고만 답한다. **누구에게 물었고 누구를 넘겼나**는 `[4]` 의 로그로 본다.

```js
// js16b-17c-homeobject.js
// super 는 무엇으로 정해지나 -- 메서드를 떼어 다른 객체에 붙여 this 와 super 를 함께 찍는다.
// 07편의 this 규칙과 견줄 자리다.
class Animal { who() { return "Animal.who"; } }
class Dog extends Animal {
  describe() { return "this=" + this.name + "  super.who()=" + super.who(); }
}
class Robot { who() { return "Robot.who"; } }
class Toaster extends Robot {}

const dog = Object.assign(new Dog(), { name: "dog" });
const toaster = Object.assign(new Toaster(), { name: "toaster" });

console.log("[1] detach Dog's method and attach it to an object whose parent is Robot");
console.log("  dog.describe()                 " + dog.describe());
toaster.describe = Dog.prototype.describe;
console.log("  toaster.describe()             " + toaster.describe());
console.log("  Dog.prototype.describe.call({name:'plain'})  " + Dog.prototype.describe.call({ name: "plain" }));
console.log("  toaster.who()  (its own chain) " + toaster.who());

console.log("");
console.log("[2] the same with object literals");
const P1 = { who() { return "P1.who"; } };
const P2 = { who() { return "P2.who"; } };
const o1 = { __proto__: P1, name: "o1", m() { return "this=" + this.name + "  super.who()=" + super.who(); } };
const o2 = { __proto__: P2, name: "o2" };
o2.m = o1.m;
console.log("  o1.m()   " + o1.m());
console.log("  o2.m()   " + o2.m());
console.log("  Object.setPrototypeOf(o2, null) and call again  " + (Object.setPrototypeOf(o2, null), o2.m()));

console.log("");
console.log("[3] change the prototype of the object the method was written in");
Object.setPrototypeOf(o1, P2);
console.log("  after setPrototypeOf(o1, P2):  o2.m()  " + o2.m());
Object.setPrototypeOf(o1, P1);

console.log("");
console.log("[4] trap log -- whom does super.who() ask, and with which receiver?");
const L = [];
const tapped = new Proxy({ who() { return "tapped.who"; } }, {
  get(t, k, r) { if (typeof k === "string") L.push("get(" + k + ") receiver=" + (r && r.name)); return Reflect.get(t, k, r); },
});
const home = { __proto__: tapped, name: "home", m() { return super.who(); } };
const guest = { name: "guest", m: home.m };
L.length = 0; home.m();  console.log("  home.m()   " + JSON.stringify(L));
L.length = 0; guest.m(); console.log("  guest.m()  " + JSON.stringify(L));

console.log("");
console.log("[5] super.x = v -- where does the value land?");
const parent = { x: "parent's x" };
const kid = { __proto__: parent, name: "kid", setX() { super.x = "written via super"; } };
kid.setX();
console.log("  own x on kid?  " + Object.hasOwn(kid, "x") + "   kid.x " + kid.x + "   parent.x " + parent.x);

console.log("");
console.log("[6] super in three function forms");
for (const src of ["return { m() { return super.toString; } }",
                   "return { m: function () { return super.toString; } }",
                   "return { m: () => super.toString }"]) {
  let r;
  try { new Function(src); r = "compiles"; } catch (e) { r = e.constructor.name + " " + e.message; }
  console.log("  " + src.padEnd(56) + "-> " + r);
}
```
```text
===== node20 js16b-17c-homeobject.js (exit=0) =====
[1] detach Dog's method and attach it to an object whose parent is Robot
  dog.describe()                 this=dog  super.who()=Animal.who
  toaster.describe()             this=toaster  super.who()=Animal.who
  Dog.prototype.describe.call({name:'plain'})  this=plain  super.who()=Animal.who
  toaster.who()  (its own chain) Robot.who

[2] the same with object literals
  o1.m()   this=o1  super.who()=P1.who
  o2.m()   this=o2  super.who()=P1.who
  Object.setPrototypeOf(o2, null) and call again  this=o2  super.who()=P1.who

[3] change the prototype of the object the method was written in
  after setPrototypeOf(o1, P2):  o2.m()  this=o2  super.who()=P2.who

[4] trap log -- whom does super.who() ask, and with which receiver?
  home.m()   ["get(who) receiver=home"]
  guest.m()  ["get(who) receiver=guest"]

[5] super.x = v -- where does the value land?
  own x on kid?  true   kid.x written via super   parent.x parent's x

[6] super in three function forms
  return { m() { return super.toString; } }               -> compiles
  return { m: function () { return super.toString; } }    -> SyntaxError 'super' keyword unexpected here
  return { m: () => super.toString }                      -> SyntaxError 'super' keyword unexpected here
```

```text
   super.who() 한 번이 하는 일 -- [4] 의 로그를 그림으로

   guest.m()       guest = { name: "guest", m: home.m }     (guest 의 윗집은 Object.prototype)
     │
     ├─ this = guest                         ← 부른 자리
     ├─ home object = home                   ← m 이 태어난 객체 (고정)
     ├─ 출발 칸 = getPrototypeOf(home)       ← ★ 부르는 이 순간에 읽는다
     │           = tapped (Proxy)
     └─ tapped 에게 묻는다   get(who, receiver = guest)
                              ^^^^^^^^^^^^^^^^^^^^^^^^
                              로그: "get(who) receiver=guest"
```

**그림 해설 — 여섯 덩어리.**

- ★★★ **`[1]` — 떼어 붙이면 `this` 는 바뀌고 `super` 는 안 바뀐다.** `toaster.describe()` 가 `this=toaster  super.who()=Animal.who` 다.
  `toaster` 자신의 사슬로 부르면 `Robot.who` 인데(마지막 줄), **`super` 는 그 사슬을 안 탔다.**
  `.call({name:'plain'})` 처럼 **사슬이 아예 다른 객체**에서 불러도 `Animal.who` 다.
  ★★★ **07번의 「다른 객체에 붙이면 `this` 가 그 객체」(`assigned to another object -> "hi lee"`)와 나란히 놓고 외운다.**
- ★★ **`[2]` — 객체 리터럴의 메서드 단축도 도장을 받는다.** `o2.m = o1.m` 뒤 `o2.m()` 이 `P1.who` 다 — `o2` 의 윗집 `P2` 가 아니다.
  ★ **`o2` 의 윗집을 `null` 로 끊어도** 답이 같다. `super` 가 `o2` 쪽을 **한 번도 안 본다**는 뜻이다.
- ★★★ **`[3]` — 도장은 고정이지만, 도장 찍힌 집의 윗집은 부를 때 읽는다.** `setPrototypeOf(o1, P2)` 뒤 `o2.m()` 이 **`P2.who`** 가 된다.
  ★ 「`super` 는 정의할 때 정해진다」를 **한 단계 더 정밀하게** 말하면 — **정해지는 것은 집(HomeObject)이고, 윗집은 호출 시점의 조회**다.
  15번의 「`instanceof` 는 함수의 **지금** `.prototype` 을 본다」와 같은 성질이다.
- ★★★ **`[4]` — 트랩 로그가 이 주제의 근거다.** `home.m()` 도 `guest.m()` 도 **`home` 의 윗집(`tapped`)** 에게 `get(who)` 를 한 번 묻는다.
  달라지는 것은 **receiver 한 칸뿐**이다 — `home` 대 `guest`.
  ★★★ **이것이 15번 결론의 재등장이다** — 「탐색은 체인을 타고, 값은 수신자에 떨어진다」. `super` 는 **탐색의 출발 칸만 바꾸고** 수신자는 `this` 로 넘긴다.
  그래서 부모 쪽이 getter 였다면 그 getter 안의 `this` 도 `guest` 다(15번의 「체인 위 setter 의 `this` 는 수신자」와 같은 규칙).
- ★★ **`[5]` — `super.x = v` 는 부모가 아니라 `this` 에 쓴다.** `kid` 에 own `x` 가 생기고 `parent.x` 는 그대로다.
  ★ 「`super` 로 쓰면 부모 것을 고친다」는 **틀린 직관**이다 — 15번의 **「쓰기는 수신자에 내려앉는다」** 가 여기서도 이긴다.
- ★★ **`[6]` — 도장은 메서드 문법에만 찍힌다.** `m() {}` 은 `compiles`, `m: function () {}` 과 `m: () => …` 는 `SyntaxError 'super' keyword unexpected here` 다.
  명세가 메서드 정의마다 *"Perform MakeMethod(closure, obj)."* 를 하고, 그것이 도장이다. `function` 식에는 그 단계가 없다.

**남은 두 자리 — 메서드 안의 화살표 · 정적 메서드 안의 `super`**

```js
// js16b-17f-super-edges.js
// super 의 남은 두 자리 -- 메서드 안의 화살표, 그리고 정적 메서드 안의 super.
class Animal {
  who() { return "Animal.who"; }
  static kind() { return "Animal.kind on " + this.name; }
}
class Dog extends Animal {
  who() { return "Dog.who"; }
  viaArrow() { const f = () => super.who(); return f(); }
  static kind() { return "Dog.kind -> " + super.kind(); }
}
const d = new Dog();
console.log("[1] an arrow inside a method");
console.log("  d.who()       " + d.who());
console.log("  d.viaArrow()  " + d.viaArrow());
const stolen = d.viaArrow;
console.log("  detached, called on {}  " + stolen.call({}));

console.log("");
console.log("[2] super inside a static method");
console.log("  Dog.kind()    " + Dog.kind());
console.log("  Object.getPrototypeOf(Dog) === Animal ? " + (Object.getPrototypeOf(Dog) === Animal));
```
```text
===== node20 js16b-17f-super-edges.js (exit=0) =====
[1] an arrow inside a method
  d.who()       Dog.who
  d.viaArrow()  Animal.who
  detached, called on {}  Animal.who

[2] super inside a static method
  Dog.kind()    Dog.kind -> Animal.kind on Dog
  Object.getPrototypeOf(Dog) === Animal ? true
```

- ★★ **화살표는 스스로 도장이 없지만 둘러싼 메서드의 것을 쓴다** — `d.viaArrow()` 가 `Animal.who` 다. `[6]` 의 `SyntaxError` 는 **둘러싼 메서드가 없는 화살표**였다.
  명세가 그렇게 적는다 — *"An ArrowFunction that references super is always contained within a non-ArrowFunction and the necessary state to implement super is accessible via the envRecord that is captured by the function object of the ArrowFunction."*
  ★ 떼어서 `{}` 에 대고 불러도 `Animal.who` 다 — 화살표가 빌린 것도 **도장**이다.
- ★★ **정적 메서드의 도장은 클래스 자신이다.** 그래서 그 안의 `super` 는 **생성자 쪽 사슬의 윗집**(`Animal`)이고,
  `Dog.kind()` 가 `Dog.kind -> Animal.kind on Dog` 를 찍는다 — 부모 정적 메서드 안의 `this` 는 **`Dog`**(수신자)다. 동작 (1)의 두 사슬이 여기서 다시 쓰인다.

### (4) ★★★ 부모 생성자가 자식 메서드를 부르면 — 자식 필드는 아직 없다

**언제 쓰나** — 부모 생성자에서 `this.render()`·`this.init()` 같은 **덮어쓸 수 있는 메서드**를 부르는 설계를 볼 때. 「초기화했는데 값이 날아갔다」가 나는 자리다.
★★ **필드 초기화 순서 자체는 16번이 정본이다** — 16번 블록이 `Derived constructor body -- before super()` → `Base field initializer` → `Base constructor body` → `Derived field initializer` 순서를 찍었다.
여기서는 **그 순서 한가운데서 자식 메서드가 불리면** 무엇을 보나만 본다.

```js
// js16b-17e-ctor-virtual.js
// ★ 부모 생성자가 자식이 덮어쓴 메서드를 부르면 -- 그 순간 자식 필드는 무엇인가.
// C# 12편과 견줄 자리다. 로그로 확인한다.
const L = [];
class Widget {
  constructor() {
    L.push("Widget constructor calls this.describe()");
    L.push("  -> " + this.describe());
    L.push("Widget constructor calls this.init()");
    this.init();
  }
  describe() { return "Widget.describe"; }
  init() {}
}
class Button extends Widget {
  label = "OK";
  count = 0;
  note;
  constructor() {
    super();
    L.push("Button constructor after super(): label=" + this.label + " count=" + this.count + " note=" + this.note);
  }
  describe() { return "Button.describe sees label=" + this.label + " (own? " + Object.hasOwn(this, "label") + ")"; }
  init() {
    this.count = 99;
    this.note = "set by init";
    L.push("  Button.init set count=99, note='set by init'");
  }
}
new Button();
console.log("[1] the log");
L.forEach((m, i) => console.log("  " + String(i + 1).padStart(2) + ". " + m));

console.log("");
console.log("[2] the same, with a #private field");
class PrivButton extends Widget {
  #label = "OK";
  describe() {
    const has = #label in this;
    try { return "PrivButton.describe  #label in this=" + has + "  value=" + this.#label; }
    catch (e) { return "PrivButton.describe  #label in this=" + has + "  " + e.constructor.name + " " + e.message; }
  }
}
L.length = 0; const pb = new PrivButton();
L.forEach((m, i) => console.log("  " + String(i + 1).padStart(2) + ". " + m));
console.log("  after construction: pb.describe()  " + pb.describe());
```
```text
===== node20 js16b-17e-ctor-virtual.js (exit=0) =====
[1] the log
   1. Widget constructor calls this.describe()
   2.   -> Button.describe sees label=undefined (own? false)
   3. Widget constructor calls this.init()
   4.   Button.init set count=99, note='set by init'
   5. Button constructor after super(): label=OK count=0 note=undefined

[2] the same, with a #private field
   1. Widget constructor calls this.describe()
   2.   -> PrivButton.describe  #label in this=false  TypeError Cannot read private member #label from an object whose class did not declare it
   3. Widget constructor calls this.init()
  after construction: pb.describe()  PrivButton.describe  #label in this=true  value=OK
```

```text
   new Button() 의 시간 -- 로그 번호를 따라간다

   Button 생성자 시작          this 없음
   super() ─▶ Widget 생성자    this 생김 (Button.prototype 을 윗집으로)
               1. this.describe() ─▶ Button.describe     ← 디스패치는 이미 자식
               2.   label 은 undefined, own 도 아니다     ← 자식 필드 초기자가 아직 안 돌았다
               3. this.init()     ─▶ Button.init
               4.   count = 99, note = 'set by init'      ← 대입으로 own 이 생긴다
           ◀─ 돌아온다
   Button 필드 초기자           label = "OK"  count = 0  note (값 없음)
                                ★ 정의(define)로 다시 놓는다 -- 4 에서 넣은 값을 덮는다
   5. Button 생성자 나머지      label=OK  count=0  note=undefined
```

**그림 해설.**

- ★★★ **디스패치는 부모 생성자 안에서도 자식을 가리킨다** — 1번 줄이 `Button.describe` 다. `this` 의 윗집이 이미 `Button.prototype` 이기 때문이다(동작 (2) — `new.target` 의 prototype 으로 만든다).
- ★★★ **그런데 자식 필드는 아직 없다** — 2번 줄이 `label=undefined (own? false)` 다. **`undefined` 인 칸이 있는 것이 아니라 칸이 없다.**
- ★★★ **부모 생성자가 부른 자식 메서드가 넣은 값은 필드 초기자가 덮는다** — 4번에서 `count=99, note='set by init'` 을 넣었는데 5번에서 `count=0 note=undefined` 다.
  ★★ **`note;` 처럼 초기자가 없는 필드도 `undefined` 로 덮는다.** 필드 선언은 「없으면 만든다」가 아니라 **「이 값으로 정의한다」** 이기 때문이다 —
  명세의 `DefineField` 가 공개 필드를 `CreateDataPropertyOrThrow(receiver, fieldName, initValue)` 로 놓는다(16번의 define 대 set).
  명세의 기본 생성자도 `Construct(func, args, NewTarget)` **다음에** 필드를 설치한다(`InitializeInstanceElements`).
- ★★★ **`[2]` — `#private` 필드는 「없다」가 더 날카롭다.** 값 창(`this.#label`)은 `TypeError` 로 닫혀서, **창을 바꿔** `#label in this` 로 물었다 — `false`.
  문구는 `Cannot read private member #label from an object whose class did not declare it` 인데, ★ **클래스는 분명히 선언했다** — 아직 **설치되지 않았을 뿐**이다.
  **V8 문구가 원인을 잘못 짚는 자리**라 문구를 근거로 쓰지 않는다. 생성이 끝난 뒤에는 `#label in this=true  value=OK` 다.

**★★★ C# 12번과 정반대다** — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번**이 같은 실험(`cs12b-virtual.cs`)을 돌려 두었다. 재실행하지 않고 인용한다.

| 부모 생성자 안에서 자식이 덮어쓴 메서드를 부르면 | C# (12번 4번 문항) | **JS (이 블록)** | C++ (C# 12번이 같이 돌린 대조) |
|---|---|---|---|
| 어느 메서드가 불리나 | **자식 것** | **자식 것**(`Button.describe`) | **부모 것**(`Parent::describe (기반 버전)`) |
| 그때 자식 **필드 초기자** 값 | ★ **이미 있다**(`FromInitializer=「필드 초기자가 넣은 값」`) | ★★★ **아직 없다**(`label=undefined (own? false)`) | 자식 상태를 **아예 안 본다** |
| 그때 자식 **생성자 본문** 값 | 아직 없다(`FromBody=「null」`) | 아직 없다(본문은 `super()` 뒤) | 안 본다 |
| 왜 | C# 은 **파생 필드 초기자가 기반 생성자보다 먼저** 돈다(12번 1번 문항) | JS 는 **파생 필드 초기자가 `super()` 가 돌아온 뒤** 돈다(16번) | 기반 생성 중에는 객체가 아직 기반 타입이다 |
| 부모 생성자 중에 자식이 넣은 값 | **안 물었다** | ★★ **필드 초기자가 덮는다**(`count=0 note=undefined`) | — |

★★★ **같은 「생성자에서 가상 호출」 사고인데 C# 은 초기자 값을 보고, JS 는 못 본다.** 처방은 셋 다 같다 — **생성자에서 덮어쓸 수 있는 메서드를 부르지 않는다.**

### (5) ★★ 내장 객체 상속 — 브랜드 태그가 판정한다

**언제 쓰나** — `Array`·`Error`·`Map` 을 상속한 클래스를 만들 때. 그리고 옛 코드의 `Array.call(this)`·`Error.call(this)` 상속을 읽을 때.

```js
// js16b-17d-builtins.js
// 내장 객체 상속 -- class 로 한 것과 옛 방식을 브랜드 태그로 견준다.
const tag = (o) => Object.prototype.toString.call(o);
const row = (label, v) => console.log(label.padEnd(52) + v);

console.log("[1] extends Array");
class Stack extends Array { top() { return this[this.length - 1]; } }
const s = new Stack();
s.push(1, 2);
s[5] = 9;
row("s.length after push(1,2) and s[5] = 9", s.length);
s.length = 1;
row("after s.length = 1 -> JSON", JSON.stringify(s));
row("tag / Array.isArray / instanceof Stack", tag(s) + " / " + Array.isArray(s) + " / " + (s instanceof Stack));
row("s.top()", s.top());

console.log("");
console.log("[2] what do map / filter / slice / spread build?");
const t = Stack.from([1, 2, 3]);
row("Stack.from([1,2,3]) constructor", t.constructor.name);
row("t.map(x => x * 2) constructor", t.map((x) => x * 2).constructor.name);
row("t.filter(x => x > 1) constructor", t.filter((x) => x > 1).constructor.name);
row("t.slice(1) constructor", t.slice(1).constructor.name);
row("[...t] constructor", [...t].constructor.name);
row("Stack[Symbol.species] === Stack", Stack[Symbol.species] === Stack);
class PlainResults extends Array { static get [Symbol.species]() { return Array; } }
const u = PlainResults.from([1, 2, 3]);
row("species -> Array : u.map(...) constructor", u.map((x) => x).constructor.name);
row("                   u itself", u.constructor.name);

console.log("");
console.log("[3] the old way -- Array.call(this)");
function OldStack() { Array.call(this); }
OldStack.prototype = Object.create(Array.prototype);
OldStack.prototype.constructor = OldStack;
const o = new OldStack();
o.push(1, 2);
o[5] = 9;
row("o.length after push(1,2) and o[5] = 9", o.length);
row("tag / Array.isArray / instanceof Array", tag(o) + " / " + Array.isArray(o) + " / " + (o instanceof Array));

console.log("");
console.log("[4] extends Error");
class ValidationError extends Error {}
const e1 = new ValidationError("bad input");
row("e1.name / e1.constructor.name", e1.name + " / " + e1.constructor.name);
row("String(e1)", String(e1));
row("e1.stack first line", e1.stack.split("\n")[0]);
row("tag / instanceof Error / instanceof ValidationError", tag(e1) + " / " + (e1 instanceof Error) + " / " + (e1 instanceof ValidationError));
class NamedError extends Error { constructor(m, opts) { super(m, opts); this.name = "NamedError"; } }
const e2 = new NamedError("bad input", { cause: e1 });
row("with this.name set: String(e2)", String(e2));
row("                    e2.stack first line", e2.stack.split("\n")[0]);
row("                    e2.cause === e1", e2.cause === e1);
row("own keys of e2", JSON.stringify(Object.getOwnPropertyNames(e2)));
class ProtoNamed extends Error {}
ProtoNamed.prototype.name = "ProtoNamed";
row("name on the prototype: stack first line", new ProtoNamed("x").stack.split("\n")[0]);
function OldError(m) { Error.call(this, m); }
OldError.prototype = Object.create(Error.prototype);
const e3 = new OldError("lost");
row("old way: e3.message / tag", JSON.stringify(e3.message) + " / " + tag(e3));
row("old way: has own stack?", Object.hasOwn(e3, "stack"));

console.log("");
console.log("[5] extends Map");
class Registry extends Map {}
const r = new Registry([["k", 1]]);
row("tag / size / get('k')", tag(r) + " / " + r.size + " / " + r.get("k"));
```
```text
===== node20 js16b-17d-builtins.js (exit=0) =====
[1] extends Array
s.length after push(1,2) and s[5] = 9               6
after s.length = 1 -> JSON                          [1]
tag / Array.isArray / instanceof Stack              [object Array] / true / true
s.top()                                             1

[2] what do map / filter / slice / spread build?
Stack.from([1,2,3]) constructor                     Stack
t.map(x => x * 2) constructor                       Stack
t.filter(x => x > 1) constructor                    Stack
t.slice(1) constructor                              Stack
[...t] constructor                                  Array
Stack[Symbol.species] === Stack                     true
species -> Array : u.map(...) constructor           Array
                   u itself                         PlainResults

[3] the old way -- Array.call(this)
o.length after push(1,2) and o[5] = 9               2
tag / Array.isArray / instanceof Array              [object Object] / false / true

[4] extends Error
e1.name / e1.constructor.name                       Error / ValidationError
String(e1)                                          Error: bad input
e1.stack first line                                 Error: bad input
tag / instanceof Error / instanceof ValidationError [object Error] / true / true
with this.name set: String(e2)                      NamedError: bad input
                    e2.stack first line             NamedError: bad input
                    e2.cause === e1                 true
own keys of e2                                      ["stack","message","cause","name"]
name on the prototype: stack first line             ProtoNamed: x
old way: e3.message / tag                           "" / [object Object]
old way: has own stack?                             false

[5] extends Map
tag / size / get('k')                               [object Map] / 1 / 1
```

```text
   누가 객체를 만드나 -- 이것이 두 방식을 가른다

   class Stack extends Array            function OldStack() { Array.call(this) }
   new Stack()                          new OldStack()
     │                                    │
     ├ Stack 생성자: this 없음            ├ new 가 먼저 평범한 객체를 만든다  ← 이미 늦었다
     ├ super() ─▶ Array 생성자가          ├ Array.call(this)
     │            진짜 배열을 만든다       │   그 객체를 배열로 바꾸지 못한다
     │            (윗집 = Stack.prototype)│
     v                                    v
   [object Array]  length 가 따라 움직인다 [object Object]  length 는 평범한 값
   Array.isArray  true                    Array.isArray  false
   instanceof Array  true                 instanceof Array  true   ← ★ 속는다
```

**그림 해설.**

- ★★★ **`[1]` — `extends Array` 의 인스턴스는 진짜 배열이다.** `s[5] = 9` 에 `length` 가 `6` 이 되고, `length = 1` 에 `[1]` 로 **잘린다.**
  브랜드가 `[object Array]`, `Array.isArray` 가 `true` 다. 동작 (2)의 「**부모가 집을 짓는다**」 그대로 — `Array` 가 만들었다.
- ★★★ **`[3]` — 옛 방식은 가짜다.** `o[5] = 9` 뒤에도 `length` 가 `2` 다 — `push` 는 평범한 객체에도 `length` 를 적는 범용 메서드라 2 가 됐고, 그 뒤 인덱스 대입은 `length` 를 안 움직였다.
  브랜드 `[object Object]` · `Array.isArray` `false` 인데 ★★ **`instanceof Array` 는 `true`** 다 — 사슬에 `Array.prototype` 이 있기 때문이다(15번).
  ★★★ **이것이 ③ 브랜드 창이 이 주제의 판정 창인 이유다.** `instanceof` 는 사슬을 보고, 브랜드는 **누가 만들었나**를 본다.
- ★★ **`[2]` — `map`·`filter`·`slice`·`from` 은 자식을 만든다.** 결과의 `constructor` 가 전부 `Stack` 이다 — `Symbol.species` 를 거쳐 「같은 종류」를 만든다.
  ★ **스프레드 `[...t]` 는 `Array`** 다 — 배열 리터럴은 species 를 안 묻는다.
  ★ `static get [Symbol.species]() { return Array }` 로 **되돌릴 수 있다** — `u.map(...)` 이 `Array`, `u` 자신은 `PlainResults` 다.
- ★★★ **`[4]` — `extends Error` 의 `name` 은 클래스 이름이 아니다.** `e1.name` 이 `Error`, `String(e1)` 이 `Error: bad input` 이다.
  `name` 은 **`Error.prototype` 에서 빌려 보는 값**이고 `class ValidationError` 는 그 칸을 안 만든다. `constructor.name` 만 `ValidationError` 다.
  ★ 고치는 법 둘 — 생성자에서 `this.name = ...`(own 이 된다 — own 키에 `name` 이 보인다) 또는 **프로토타입에 `name`**(`ProtoNamed`).
  ★ `cause` 옵션(ES2022)은 `super(m, opts)` 로 넘기면 own `cause` 가 된다 — `e2.cause === e1` 이 `true`.
- ★★ **`e.stack` 은 ECMA-262 에 없다** — V8(호스트/엔진)의 것이다. 그래서 `stack first line` 줄들과 own 키 목록의 `stack` 은 **엔진 칸**이다.
  ★ 이 판에서는 `name` 을 `super()` 뒤에 대입했는데도 `stack` 첫 줄이 `NamedError: bad input` 이다 — **이유는 명세 밖이라 적지 않는다.**
- ★★ **옛 방식 `Error.call(this, m)` 은 `message` 를 잃는다** — `e3.message` 가 `""`(빈 문자열), 브랜드 `[object Object]`, own `stack` 도 없다.
  ★ `Error.call(this)` 는 `this` 를 채우지 않는다 — 출력이 그렇게 답한다.
- ★ **`[5]` — `extends Map` 도 같다.** 브랜드 `[object Map]` · `size` `1` — `Map` 생성자가 만들었다.

### (6) ★ 파이썬 34번과의 대비 — MRO 가 없고, `super` 가 정해지는 방식이 다르다

**언제 쓰나** — 파이썬에서 온 사람이 「`super` 는 부모가 아니라 MRO 상 다음」을 JS 에 그대로 옮기려 할 때.
Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **34번**을 **재실행하지 않고 인용**한다.

| | 파이썬 (34번) | JS (이 주제) |
|---|---|---|
| 상속 | **다중** — 조상을 C3 로 한 줄로 세운다(`__mro__`) | **단일** — `extends` 뒤에 식 하나. 줄 세울 조상이 **하나** |
| `super` 가 찾기 시작하는 곳 | **`type(self)` 의 MRO 에서 「내 다음」** | **HomeObject 의 윗집** |
| 부르는 인스턴스에 따라 바뀌나 | ★★★ **바뀐다** — 같은 `Left.go` 안의 `super()` 가 `Left()` 에서는 `Base`, `Both()` 에서는 `Right`(형제) | ★★★ **안 바뀐다** — `toaster` 가 불러도 `Animal.who`(동작 (3) `[1]`) |
| 정의 자리가 하는 일 | `__class__` 셀이 **출발 클래스**만 정한다 | HomeObject 가 **출발 칸 전체**를 정한다(윗집은 호출 시점 조회) |
| 다이아몬드 | 부모가 한 번만 돈다 — 모두가 `super()` 를 부를 때 | **생기지 않는다** |

★★★ **「`super` 는 부모가 아니다」는 파이썬에서만 맞다.** JS 의 `super` 는 **정의 자리의 부모**이고, 누가 부르든 형제로 새지 않는다.
★ 그래서 이 주제에서 **MRO 창은 부적용**이다 — 계산할 줄이 없다.

## 문법 — 형태와 규칙

```text
   extends · super · new.target 이 설 수 있는 자리

   class B extends 식 { }        식은 생성자이거나 null.  B.prototype -> 식.prototype · B -> 식
   class B extends null { }      인스턴스 사슬만 끊긴다. new 하려면 객체를 return 해야 한다

   constructor(...) {
     super(인자)                 파생 클래스에서만.  딱 한 번.  this 는 그 뒤부터
   }
   메서드 안     super.m(...)    HomeObject 의 윗집에서 m 을 찾아 this 로 부른다
                 super.x         같은 곳에서 읽는다 (수신자 = this)
                 super.x = v     this 에 쓴다 (부모가 아니다)
   정적 메서드   super.m()       생성자 쪽 사슬의 윗집 (부모 클래스)
   메서드 안의 화살표  super      둘러싼 메서드의 것을 빌린다

   super 를 못 쓰는 자리  m: function () {}  ·  m: () => ...  (둘러싼 메서드가 없는 화살표)
                          -> SyntaxError 로 막힌다

   new.target            생성자 안: new 에 적힌 클래스 / 일반 호출: undefined
```

- **`extends` 는 사슬 둘을 잇는다** — 인스턴스 쪽 `B.prototype → A.prototype`, 생성자 쪽 `B → A`. 정적 메서드는 뒤엣것으로 상속된다.
- ★★★ **파생 생성자에서는 부모가 객체를 만든다.** 그래서 `super()` 전에는 `this` 가 없고, 두 번 부를 수 없고, 안 부르면 객체를 반환해야 한다.
- **파생 생성자가 원시값을 반환하면 `TypeError`** 다. 기반 생성자는 원시 반환을 무시한다.
- ★★★ **`super` 의 출발 칸은 HomeObject 의 윗집이다.** HomeObject 는 정의할 때 고정, 그 윗집은 부를 때 읽는다. 수신자는 `this` 다.
- **HomeObject 는 메서드 문법(클래스 메서드·객체 리터럴 단축·접근자)에만 생긴다.**
- ★★ **자식 필드는 `super()` 가 돌아온 뒤 정의된다** — 부모 생성자가 부른 자식 메서드는 그것을 못 보고, 그 사이 넣은 값은 덮인다.
- **`extends Array`/`Error`/`Map` 은 진짜 내장 객체를 만든다.** 옛 `Base.call(this)` 방식은 못 만든다.
- **`Array` 하위 클래스의 `map`·`filter`·`slice` 는 `Symbol.species` 가 가리키는 생성자로 결과를 만든다.**

## 어디서 틀리나

### (1) ★★★ 메서드를 옮겨 붙이면 `super` 도 새 부모를 따라간다고 믿는다

**안 따라간다.** `toaster.describe()` 가 `super.who()=Animal.who` 다. `this` 만 `toaster` 가 된다.
★ 믹스인을 **메서드 복사**로 만들면(`Object.assign(Target.prototype, mixin)`) 그 안의 `super` 는 **원래 객체의 윗집**을 부른다.
★ 옮길 메서드에 `super` 가 있으면 **옮기지 말고 사슬로 잇는다**(`class X extends Mixin(Base)` 꼴).

### (2) ★★★ 부모 생성자에서 덮어쓸 수 있는 메서드를 부른다

자식 메서드가 불리는데 **자식 필드는 아직 없고**, 그 메서드가 넣은 값은 **필드 초기자가 덮는다**(`count=99` 가 `count=0` 으로).
★★ **예외가 안 난다** — 값이 조용히 바뀐다. C# 에서 옮겨 온 습관이라면 더 위험하다 — C# 은 초기자 값이 **보였다.**
★ 처방 — 부모 생성자에서는 **덮어쓸 수 없는 일만** 한다. 초기화 훅이 필요하면 **생성이 끝난 뒤** 부른다(팩토리·`static create()`).

### (3) ★★★ `extends Error` 만 하면 `name` 이 클래스 이름이 된다고 믿는다

`e1.name` 은 **`Error`** 다. 로그에 `Error: bad input` 만 찍혀 **어느 오류인지 모른다.**
★ `this.name = new.target.name` 류를 생성자에 두거나, 프로토타입에 `name` 을 단다. **판정은 `instanceof ValidationError`** 로 한다 — `name` 문자열 비교는 약하다.

### (4) ★★ `instanceof Array` 가 `true` 면 진짜 배열이라고 믿는다

옛 방식 `OldStack` 이 `instanceof Array` 는 `true` 인데 **`length` 가 안 따라오고** `Array.isArray` 가 `false` 다.
★★ **배열인지는 `Array.isArray` 로, 무엇이 만들었나는 브랜드로** 묻는다(34번 주제의 정본).

### (5) ★★ `super()` 전에 `this` 를 한 번도 안 건드리면 괜찮다고 믿는다 — 화살표·헬퍼로 우회한다

화살표로 읽어도 **같은 `ReferenceError`** 다. `this` 는 **아직 없는 것**이지 가려진 것이 아니다.
★ 필드 초기자·계산에 `this` 가 필요하면 **`super()` 뒤로** 옮긴다. `super()` 에 넘길 값은 `this` 없이 계산한다.

### (6) ★★ 파생 생성자에서 `return` 으로 다른 값을 돌려준다

**원시값이면 `TypeError`**(`super()` 뒤여도), **객체면 `instanceof` 가 `false`** 인 남의 객체가 결과가 된다.
★ 기반 클래스에서 멀쩡하던 `return 7` 이 **`extends` 하나 붙이자 터진다.**

### (7) ★★ `super.x = v` 로 부모의 값을 고친다고 믿는다

**`this` 에 own 이 생긴다.** 부모는 그대로다. 15번의 「**쓰기는 수신자에 내려앉는다**」 를 `super` 도 못 이긴다.

### (8) ★★ `map`·`filter` 결과가 평범한 배열이라고 믿는다

`Stack` 에서 `map` 하면 **`Stack`** 이 나온다. 생성자가 인자를 다르게 받는 하위 클래스라면 **`map` 이 그 생성자를 부른다**는 뜻이다.
★ 평범한 배열이 필요하면 `Symbol.species` 를 `Array` 로 돌리거나 `[...t]`·`Array.from` 을 쓴다(`Stack.from` 은 `Stack` 이다).

### (9) ★ 옛 코드의 정적 멤버 상속이 저절로 된다고 믿는다

`setPrototypeOf(OldB.prototype, OldA.prototype)` 만으로는 **인스턴스 쪽만** 이어진다. 생성자 쪽은 **따로** 이어야 한다.
★ `class` 로 옮기면 두 줄이 한 번에 생긴다 — 동작 (1)의 `[4]`.

### (10) ★ 「`super` 호출은 느리다」·「내장 상속은 느리다」를 근거 없이 옮긴다

★★★ **이 문서는 그 말을 하지 않는다 — 안 쟀기 때문이다.** 말할 수 있는 것은 **의미**뿐이다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- **`extends` 가 `B.prototype → A.prototype` 과 `B → A` 두 연결을 만드는 것** · **`extends null` 이면 인스턴스 쪽 윗집만 `null` 이고 생성자 쪽은 `Function.prototype` 인 것.**
- **파생 생성자에서 `super()` 전에 `this` 를 읽으면 `ReferenceError`**, **두 번 부르면 `ReferenceError`**, **`this` 를 못 받고 끝나면 `ReferenceError`** 인 것 — 종류가.
- **파생 생성자의 원시 반환이 `TypeError`** 이고 **기반 생성자의 원시 반환이 무시되는 것.**
- **암묵 파생 생성자가 인자를 전부 넘기는 것** · `new.target` 이 `new` 에 적힌 생성자이고 일반 호출에서 `undefined` 인 것.
- ★★★ **`super` 가 HomeObject 의 윗집에서 찾기 시작하고 수신자로 `this` 를 넘기는 것** · **HomeObject 가 메서드 문법에만 생기는 것** · **`super.x = v` 가 `this` 에 쓰는 것.**
- **공개 필드가 `super()` 뒤에 정의(`DefineField`)로 설치되는 것** — 그래서 그 전에 대입된 값이 덮이는 것.
- **`extends Array` 인스턴스가 이그조틱 배열이고 브랜드가 `[object Array]` 인 것** · **`map`/`filter`/`slice` 가 `Symbol.species` 를 따르는 것.**
- **`Error.prototype.name` 이 `"Error"` 이고 하위 클래스가 그것을 빌려 보는 것** · **`cause` 옵션이 own `cause` 가 되는 것**(ES2022).

### 엔진(V8) 구현 · 이 판의 관찰

- **예외 문구 전부** — `Must call super constructor in derived class before accessing 'this' or returning from derived constructor` ·
  `Super constructor may only be called once` · `Derived constructors may only return object or undefined` ·
  `Super constructor null of N is not a constructor` · `Cannot read private member #label from an object whose class did not declare it` ·
  `'super' keyword unexpected here`. **종류만 명세가 정한다.**
- ★★ **`Super constructor null of N` 의 `null`** — 사슬이 실제로 가리키는 것은 `Function.prototype` 이다(`[5]` 둘째 줄). 문구는 소스를 옮긴 것이다.
- ★★ **`#label` 문구의 「class did not declare it」** — 선언은 했고 설치 전이다. 문구가 원인을 틀리게 말한다.
- **두 판(18·20)이 이 주제에서 한 글자도 안 갈렸다** — 같은 V8 계열이기 때문이지 보장이 아니다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★★ **`Error.prototype.stack` 과 `e.stack` 의 내용·첫 줄 형식 전부** — ECMA-262 에 없다. V8 이 넣는 것이고 Node 가 그것을 쓴다.
  own 키 목록 `["stack","message","cause","name"]` 의 **`stack` 한 칸**도 여기다. `message`·`cause`·`name` 셋은 명세 쪽이다.

### 그래서 이렇게 적으면 틀린다

- 「`super` 는 `this` 의 부모다」 — **아니다.** **메서드가 정의된 객체의 부모**다. `toaster` 가 불러도 `Animal` 이다.
- 「`super` 는 정의할 때 완전히 고정된다」 — **반만 맞다.** 고정은 HomeObject 이고 그 **윗집은 부를 때 읽는다**(`P2.who`).
- 「`super.x = v` 는 부모를 고친다」 — **아니다.** `this` 에 쓴다.
- 「부모 생성자에서 부른 자식 메서드는 자식 필드를 본다」 — **C# 에서는 그렇고 JS 에서는 아니다.**
- 「`extends Error` 면 `name` 이 클래스 이름이다」 — **아니다.** `Error` 다.
- 「`e.stack` 첫 줄은 `name: message` 로 정해져 있다」 — **명세에 `stack` 자체가 없다.**
- 「`instanceof Array` 면 배열이다」 — **옛 방식 상속이 반례다.**
- 「JS 의 `super` 도 파이썬처럼 MRO 상 다음이다」 — **MRO 가 없다.** 단일 상속이다.

## 언제 쓰고 언제 안 쓰나

- **`extends`** — **「is-a」가 분명하고 부모 계약을 그대로 지킬 때.** 코드 재사용만이 목적이면 조합(필드로 들고 위임)이 덜 놀랍다.
- **`super.m()`** — 부모 동작에 **덧붙일 때**(`super.render()` 뒤에 한 줄 더). ★ 그 메서드를 **다른 객체로 옮길 계획이 있으면 쓰지 않는다.**
- **`new.target`** — **추상 클래스 흉내**와 「어느 하위 클래스로 만들었나」에 따라 갈라야 할 때. 그 밖에는 `this.constructor` 로 충분한 경우가 많다.
- **`extends Array`/`Map`** — 진짜 배열·맵이어야 할 때(`Array.isArray`·`length`·브랜드). ★ `map` 이 자식 생성자를 부른다는 것을 받아들일 수 있을 때만.
- **`extends Error`** — **언제나 `name` 을 같이 단다.** 원인이 있으면 `cause` 로 잇는다(32번).
- **안 쓸 자리** — 부모 생성자 안의 덮어쓸 수 있는 메서드 호출 · 파생 생성자의 `return` · `super` 가 든 메서드의 복사 믹스인 · 옛 `Base.call(this)` 방식의 내장 상속.

## 핵심 문장

1. ★★★ **`super` 는 정의된 자리(HomeObject)의 윗집에서 찾고, `this` 는 부른 자리를 따른다.**
   메서드를 떼어 붙이면 `this` 는 바뀌고 `super` 는 안 바뀐다 — 07번과 정반대다.
2. ★★★ **`super` 는 탐색의 출발 칸만 바꾼 조회다.** 수신자는 `this` 이고, `super.x = v` 는 `this` 에 쓴다 — 15번 결론 그대로다.
3. ★★★ **파생 클래스에서는 부모가 객체를 만든다.** 그래서 `super()` 전에 `this` 가 없고, `extends Array` 는 진짜 배열이며, 옛 `Array.call(this)` 는 못 만든다.
4. ★★★ **자식 필드는 `super()` 가 돌아온 뒤에 정의된다.** 부모 생성자가 부른 자식 메서드는 그것을 못 보고, 그 사이 넣은 값은 덮인다 — C# 과 반대다.
5. ★★ **`extends` 는 사슬을 두 줄 잇는다.** 정적 메서드가 상속되는 것도, 정적 메서드 안의 `super` 가 부모 클래스인 것도 생성자 쪽 사슬 덕이다.

## 관련 자료

- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — **그쪽이 조회·쓰기 규칙과 수신자의 정본**이다. 여기는 **`super` 가 출발 칸을 바꾼다**는 것부터.
- [16 — `class` 문법](../16-class-syntax/2-summary.md) — **그쪽이 멤버가 어디에 붙나·필드 초기화 순서·define 대 set·`#x in obj` 의 정본**이다. 여기는 **상속이 끼었을 때**만.
- [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) — **그쪽이 `this` 판정의 정본**이다. 여기는 **`super` 는 그 규칙을 안 따른다**는 대비만.
- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) — **그쪽이 `__proto__:` 리터럴 문법의 정본**이다. 동작 (3)의 리터럴 예가 그 문법을 쓴다.
- [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) — 상속된 열거 가능 프로퍼티를 순회할 때 두 사슬 중 **인스턴스 쪽**이 걸린다.
- [목록의 **22번 주제**](../22-symbol-and-well-known-symbols/) 「`Symbol` 과 잘 알려진 심볼」 — **그쪽이 `Symbol.species` 를 포함한 잘 알려진 심볼 전체의 정본**이다.
- [목록의 **32번 주제**](../32-error-handling-and-error/) 「오류 처리와 `Error`」 — **그쪽이 `Error` 계층·`cause` 의 쓰임의 정본**이다. 여기는 **상속했을 때 `name` 이 무엇인가**까지.
- [목록의 **34번 주제**](../34-type-checking-idioms/) 「타입 검사 관용구」 — **그쪽이 `instanceof`·`Array.isArray`·브랜드 중 무엇을 고르나의 정본**이다.
- [목록의 **45번 주제**](../45-proxy/) 「`Proxy`」 · [목록의 **46번 주제**](../46-reflect/) 「`Reflect`」 — 트랩의 `receiver` 인자가 무엇인지의 정본. 여기서는 **로그 도구로만** 썼다.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번** — ★★★ **생성자 속 가상 호출의 대비축.** 파생 필드 초기자 값이 **보였다.**
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **34번** — ★★ **`super` 가 정해지는 방식의 대비축.** 그쪽은 `type(self)` 의 MRO, 여기는 HomeObject.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **09번** — 메서드는 재정의되고 필드는 숨는 **정적 언어 쪽 상속**. 여기는 인용하지 않았다.

## 용어 풀이

- **`extends`** — 클래스의 두 사슬(인스턴스 쪽·생성자 쪽)의 윗집을 정하는 절. 뒤에 생성자나 `null` 이 온다.
- **파생 클래스 / 기반 클래스(derived / base)** — `extends` 가 있으면 파생, 없으면 기반. **객체를 누가 만드나**가 다르다.
- **`super(...)`** — 파생 생성자에서 부모 생성자에게 객체를 만들게 하는 호출. 돌아온 객체가 `this` 가 된다.
- **`super.x`** — HomeObject 의 윗집에서 시작하는 조회. 수신자는 `this`.
- **`[[HomeObject]]`** — 메서드가 자기가 정의된 객체를 기억하는 내부 슬롯. 명세에서는 `MakeMethod` 가 찍는다.
- **`new.target`** — `new` 에 적힌 생성자. 부모 생성자 안에서도 자식 클래스다.
- **이그조틱 객체(exotic object)** — 평범한 객체와 다른 내부 동작을 가진 객체. 배열은 `length` 가 인덱스 대입을 따라 움직인다.
- **`Symbol.species`** — 「같은 종류의 새 객체」를 만들 생성자를 알려 주는 정적 접근자. `map`·`filter`·`slice` 가 묻는다.
- **브랜드 태그(brand tag)** — `Object.prototype.toString.call(x)` 의 `[object …]`. 이 주제에서는 **누가 만들었나**의 판정.
- **`cause`** — `new Error(msg, { cause })` 로 원인을 잇는 옵션(ES2022). own 프로퍼티가 된다.
- **가상 호출(virtual call)** — 부모 코드가 부른 메서드가 **자식이 덮어쓴 것**으로 가는 것. JS 의 메서드 호출은 늘 이렇다.
- **MRO(파이썬)** — 다중 상속의 조상을 한 줄로 편 것. **JS 에는 없다.**

## 더 들어가면

- **`super` 가 든 메서드를 믹스인으로 쓰는 법** — 복사하면 도장이 따라간다(동작 (3)). 그래서 JS 믹스인은
  `const Mixin = (Base) => class extends Base { ... }` 처럼 **클래스를 만드는 함수**로 쓰는 것이 관용이다.
  그 안의 메서드는 **새 클래스의 프로토타입**을 도장으로 받는다. ★ **이 꼴은 이번에 안 돌려 봤다.**
- **생성자 쪽 윗집을 바꾸면 `super()` 가 부르는 부모도 바뀌나** — 명세의 기본 생성자는 `ctorFunc.[[GetPrototypeOf]]()` 를 **부를 때** 읽는다.
  동작 (3)의 「윗집은 호출 시점 조회」와 같은 성질일 것으로 보이지만, ★ **`setPrototypeOf(B, X)` 뒤 `new B()` 를 던져 보지 않았다.**
- **`Symbol.species` 는 `Promise`·`RegExp`·`ArrayBuffer`·TypedArray 에도 있다**(명세 목차에 `get … [ %Symbol.species% ]` 항목이 있다). 그쪽 동작은 22번과 각 주제의 몫이다.
- **`Object.setPrototypeOf(o1, P2)` 로 `super` 의 답이 바뀐 것**은 「HomeObject 의 윗집을 바꾸는 코드」가 곧 「그 메서드를 가진 모든 객체의 `super` 를 바꾸는 코드」라는 뜻이다. 실무에서 할 일은 아니다 — **의미가 그렇다는 것**까지만 적는다.
