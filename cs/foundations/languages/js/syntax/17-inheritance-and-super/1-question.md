# js/syntax/17 — 상속과 `super`: 「`super` 는 정의된 자리를 기억하고, `this` 는 부른 자리를 따른다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · x86-64 Linux. 브라우저는 **안 돌렸다.**
> 배너의 `node20` 은 v20.19.6 이다. 이 주제의 블록은 **두 판에서 전부 identical** 이다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `super.who()` 의 값은 **누구에게 물었고 누구를 수신자로 넘겼나**를 말하지 않는다 — 부모 칸의 `Proxy` 트랩 로그가 그것을 찍는다.
> 부모 생성자 속 가상 호출도 **번호 붙은 생성 로그**로 찍었다. **3번 문항이 이 주제의 중심이고, 4번이 그 옆자리다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **`extends` 가 잇는 두 사슬**(그리고 정적 멤버)
> ② ★★★ **`super` 가 어디서 찾기 시작하나**(떼어 붙였을 때 `this` 와 갈리는 것)
> ③ **파생 클래스에서는 부모가 객체를 만든다**(`super()` 규칙 · 가상 호출 · 내장 상속이 전부 여기서 나온다).
>
> **선행** — [16 — `class` 문법](../16-class-syntax/2-summary.md) · [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md).
> ★★★ **07번의 「다른 객체에 붙이면 `this` 가 바뀐다」를 먼저 떠올려라** — 3번은 그 반대편을 묻는다.
> ★★ **이 파일은 정답을 싣지 않는다.** 예측형 문항에는 **소스만** 있다.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **3번은 줄마다 `this=` 와 `super.who()=` 를 갈라 적어라.** 한쪽만 맞으면 틀린 것이다.
- ★★★ **4번은 로그 줄 번호마다 「그 순간 자식 필드가 있나」를 적어라.**
- ★★ **예외는 종류와 문구로 적는다.** 문구가 기억나지 않으면 종류와 「무엇을 말하는 문구인가」까지만.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 엔진의 사정인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「느리다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `class B extends A` 가 만드는 사슬과 정적 메서드 (예측) ★★

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

- `[1]`·`[2]` 두 줄의 사슬을 `null` 까지 적어라. `Plain` 줄은 어떻게 다른가?
- `B.create()` 가 찍는 문장과 `Object.hasOwn(B, 'create')` 의 값은?
- `[4]` 의 두 줄은 각각 `true` 인가 `false` 인가?
- `[5]` — `N.prototype` 의 사슬 · `N` 의 윗집 · `new N()` 의 결과 · `N2` 의 두 값은?

### 2. 파생 생성자에서 `super()` 를 전에 / 안 / 두 번 부르면 (예측) ★★★

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

- `[1]`\~`[3]` 의 여덟 줄마다 **성공인지, 무슨 예외인지**를 적어라. 같은 문구가 몇 줄에 나오나?
- `constructor() { return 7 }` 과 `super(1); return 7` 은 같은 결과인가? 기반 클래스의 `return 7` 은?
- `[4]` 의 두 값과 `[5]` 의 네 줄은?

### 3. 떼어 붙인 메서드의 `this` 와 `super` (예측) ★★★ 이 주제의 축

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

- `[1]` 네 줄의 `this=` 와 `super.who()=` 를 갈라 적어라.
- `[2]` 세 줄 — `o2` 의 윗집을 `null` 로 끊은 뒤에는?
- `[3]` — `o1` 의 윗집을 바꾼 뒤 `o2.m()` 은?
- ★★★ `[4]` 두 줄의 트랩 로그를 적어라. 두 줄에서 **같은 것과 다른 것**은?
- `[5]` — `kid` 에 own `x` 가 생기나? `parent.x` 는?
- `[6]` 세 줄 중 컴파일되는 것은?

### 4. 부모 생성자가 자식 메서드를 부를 때 자식 필드는 (예측) ★★★

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

- `[1]` 다섯 줄의 로그를 적어라. 특히 **2번 줄의 `label` 과 `own?`**, **5번 줄의 `count` 와 `note`** 는?
- `[2]` — `#label in this` 는? 그 뒤 `this.#label` 은 값인가 예외인가? 생성이 끝난 뒤는?

### 5. `Array`·`Error`·`Map` 을 상속하면 — 새 방식과 옛 방식 (예측) ★★★

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

- `[1]` — `s.length` · `length = 1` 뒤의 JSON · 브랜드 · `Array.isArray` 는?
- `[2]` — 다섯 가지 결과의 `constructor` 이름과 `species` 를 돌린 뒤의 두 이름은?
- `[3]` — 옛 방식의 `length` · 브랜드 · `Array.isArray` · `instanceof Array` 는?
- `[4]` — `e1.name` · `String(e1)` · `String(e2)` · `e2` 의 own 키 · 옛 방식의 `message` 는?

### 6. 메서드 안의 화살표 · 정적 메서드 안의 `super` (예측) ★★

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

- `[1]` 세 줄은? 떼어서 `{}` 에 대고 부른 줄은 앞 줄과 같은가?
- `[2]` — `Dog.kind()` 가 찍는 문장에서 **`Animal.kind` 안의 `this.name`** 은 무엇인가?

### 7. 파생 클래스에서는 부모가 객체를 만든다 (왜) ★★★ 이 주제의 결론

- ★★★ 이 한 사실로 **`super()` 전의 `ReferenceError`**, **`extends Array` 가 진짜 배열인 것**, **옛 `Array.call(this)` 가 실패하는 것**을 각각 한 문장으로 설명하면?
- ★★ 부모가 만든 객체의 윗집이 **부모의 `prototype` 이 아니라 자식의 `prototype`** 인 것은 무엇 덕인가?
- ★ 기반 생성자와 파생 생성자가 **원시값 반환**에서 갈리는 이유를 같은 사실로 말하면?

### 8. `[[HomeObject]]` 는 고정인데 `P2.who` 가 나온 이유 (왜) ★★★

- ★★★ `super` 가 정해지는 것을 **「정의할 때」와 「부를 때」** 두 칸으로 갈라 적어라 — 각 칸에 무엇이 들어가나?
- ★★ 트랩 로그의 `receiver` 가 15번의 어느 결론을 다시 보이는가?
- ★ `super.x = v` 가 부모를 안 고치는 것도 같은 결론으로 설명되나?

### 9. C# 12번과 정반대인 자리 (연결) ★★★

- ★★★ 부모 생성자에서 자식이 덮어쓴 메서드를 부를 때 **C#·JS·C++** 는 각각 **어느 메서드가 불리고, 자식 필드 초기자 값이 보이나**?
- ★★ 그 차이는 **필드 초기자가 언제 도나**의 차이다 — C# 과 JS 에서 각각 언제인가?
- ★ JS 에서만 생기는 두 번째 사고(부모 생성자 중에 넣은 값)는 무엇이고, 그 근거가 되는 명세 연산의 이름은?

### 10. 파이썬 34번의 `super()` 와 무엇이 다른가 (연결) ★★

- ★★ 파이썬의 `super()` 는 **무엇의 무엇**에서 다음을 고르고, JS 의 `super` 는 **어디**에서 찾기 시작하나?
- ★★★ **부르는 인스턴스가 바뀌면** `super` 의 목적지가 바뀌는 쪽은 어디인가? 그 근거가 된 두 출력은?
- ★ 이 주제에서 **MRO 창이 부적용**인 이유는?

### 11. 보장인가 엔진 사정인가 (경계) ★★★

- ★★★ **명세가 정하는 것** 셋과 **V8 의 문구** 셋을 대면?
- ★★ `e.stack` 은 어느 칸인가? own 키 `["stack","message","cause","name"]` 중 **명세 밖인 것**은?
- ★★ **V8 문구가 원인을 틀리게 말하는 자리** 두 곳은?
- ★ 이 주제에서 **창을 바꿔 물은 자리**와 **부적용인 창** 둘은?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **필드 초기화 순서** · **조회와 수신자 규칙** · **`this` 판정** · **`Symbol.species` 가 속한 심볼 전체** · **`Error` 의 `cause` 쓰임** · **`instanceof` 대 `Array.isArray`** · **트랩의 `receiver`** 는 각각 어느 주제가 정본인가?
- ★★ 16번이 본 필드 순서 로그와 **이 주제의 생성 로그**는 무엇이 다른가?
- ★ 이 주제가 **끝까지 책임지는 것** 셋을 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
