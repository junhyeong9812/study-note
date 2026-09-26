# js/syntax/16 — `class` 문법: 「메서드는 프로토타입에, 필드는 인스턴스에 정의된다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v20.19.6(nvm, 기본 판) · node v18.19.1(기본 PATH, 대조) · x86-64 Linux. 브라우저는 **안 돌렸다.**
> 배너의 `node20` 은 v20.19.6 이다. 이 주제의 블록은 **두 판에서 한 글자도 안 갈렸다.**
>
> ★★★ **이 주제의 본체는 ② 전수 격자(「어디에 붙나」)다.**
> 멤버 9행 × 자리 3열(프로토타입 · 인스턴스 · 생성자) = 27칸을 전수로 찍었다. **1번 문항이 이 주제의 중심이다.**
> ★★★ **`#private` 는 격자·브랜드 태그·`Proxy` 트랩·예외 네 창에 전부 안 보인다** — 「없다」가 아니라 「있는데 안 보인다」라서
> 클래스 **안쪽**의 `#x in o` 로 창을 바꿔 물었다. 5·6·9번이 그 자리다.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **어디에 붙나**(격자) ② **언제 도나**(필드 초기자 순서) ③ ★★★ **정의인가 대입인가**(부모 setter 에서 갈린다).
>
> ★★★ **답을 적을 때 「값」만 적으면 절반이다.** 1번은 **칸마다 자리와 플래그**, 3번은 **번호 순서**, 4번은 **setter 호출 횟수와 own 키**를 같이 적어야 답이다.
> ★★ **예외는 종류와 문구로 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
>
> **선행** — [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) ·
> [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md).
> ★★★ **15번의 「쓰기는 수신자에 내려앉고, 체인 위 setter 의 `this` 는 수신자다」를 먼저 떠올려라** — 4번의 절반이 거기 있다.
>
> **이 파일은 정답을 싣지 않는다.** 예측형 문항에는 **소스만** 있고 출력은 [3-answer.md](3-answer.md)에 있다.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 격자를 손으로 그려라** — 9행 × 3열에 칸마다 `.` 인지 플래그(`W`·`E`·`C`)인지. 그리고 **차는 칸이 몇 개**인지 센다.
- ★★★ **3번은 번호를 먼저 적어라** — 「무엇이 나오나」가 아니라 「몇 번째에 도나」가 답이다.
- ★★ **5·6번은 「막히는 것」과 「되는 것」을 갈라서** 적어라. 막히면 **어느 예외 종류**인지까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.
- ★★★ **속도·메모리에 관한 답은 하나도 없다.** 「`#private` 는 느리다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 클래스 몸통의 멤버 아홉 줄 — 27칸 격자를 채워라 (예측) ★★★ 이 주제의 축

```js
// js16b-16a-where.js
// ★ 이 주제의 본체 -- 클래스 몸통의 멤버 일곱 종이 「어디에 붙나」를 전수로 찍는다.
// 붙을 수 있는 자리는 셋: 프로토타입(C.prototype) / 인스턴스(new C()) / 생성자 함수(C 자신).
class C {
  method() { return "m"; }
  get acc() { return "g"; }
  field = "f";
  #secret = "s";
  #privMethod() { return "pm"; }
  static staticMethod() { return "sm"; }
  static staticField = "sf";
  static #staticSecret = "ss";
  static { C.fromBlock = "set in static {}"; }
  static reveal(o) { return [o.#secret, o.#privMethod(), C.#staticSecret].join(","); }
}
const inst = new C();
const places = [["prototype", C.prototype], ["instance", inst], ["constructor", C]];
const names = ["method", "acc", "field", "staticMethod", "staticField", "fromBlock",
               "#secret", "#privMethod", "#staticSecret"];

function flags(d) {
  const kind = "get" in d || "set" in d ? "accessor" : "data";
  const w = kind === "data" ? (d.writable ? "W" : "-") : " ";
  return kind.padEnd(9) + w + (d.enumerable ? "E" : "-") + (d.configurable ? "C" : "-");
}

console.log("[1] where does each member land?   (W=writable E=enumerable C=configurable)");
console.log("member".padEnd(15) + places.map(([p]) => p.padEnd(18)).join(""));
let found = 0;
for (const n of names) {
  let row = n.padEnd(15);
  for (const [, obj] of places) {
    const d = Object.getOwnPropertyDescriptor(obj, n);
    row += (d ? flags(d) : ".").padEnd(18);
    if (d) found++;
  }
  console.log(row);
}
console.log("cells with a property: " + found + " / " + names.length * places.length);

console.log("");
console.log("[2] the whole own-key list of each place (Reflect.ownKeys sees strings AND symbols)");
for (const [p, obj] of places) console.log(p.padEnd(13) + JSON.stringify(Reflect.ownKeys(obj)));

console.log("");
console.log("[3] #private -- what does each reflection API report?");
const views = [
  ["Reflect.ownKeys(inst)", () => JSON.stringify(Reflect.ownKeys(inst))],
  ["Object.getOwnPropertySymbols(inst)", () => JSON.stringify(Object.getOwnPropertySymbols(inst))],
  ["JSON.stringify(inst)", () => JSON.stringify(inst)],
  ["Object.entries(inst)", () => JSON.stringify(Object.entries(inst))],
  ["{ ...inst }", () => JSON.stringify({ ...inst })],
  ["structuredClone(inst)", () => JSON.stringify(structuredClone(inst))],
  ["'#secret' in inst", () => String("#secret" in inst)],
  ["C.reveal(inst)  (inside the class)", () => C.reveal(inst)],
];
for (const [label, f] of views) console.log(label.padEnd(38) + f());

console.log("");
console.log("[4] enumerable flag -- class members vs object-literal and old-style members");
const lit = { method() { return 1; }, get acc() { return 2; } };
function Old() {}
Old.prototype.method = function () { return 3; };
const rows = [
  ["class C { method() {} }", C.prototype, "method"],
  ["class C { get acc() {} }", C.prototype, "acc"],
  ["class C { static staticMethod() {} }", C, "staticMethod"],
  ["class C { field = ... }", inst, "field"],
  ["class C { static staticField = ... }", C, "staticField"],
  ["{ method() {} }  (literal)", lit, "method"],
  ["{ get acc() {} }  (literal)", lit, "acc"],
  ["Old.prototype.method = function", Old.prototype, "method"],
];
for (const [label, obj, k] of rows) console.log(label.padEnd(38) + "enumerable " + Object.getOwnPropertyDescriptor(obj, k).enumerable);
console.log("Object.keys(C.prototype)              " + JSON.stringify(Object.keys(C.prototype)));
console.log("Object.keys(Old.prototype)            " + JSON.stringify(Object.keys(Old.prototype)));
```

- ★★★ `[1]` 의 9행 × 3열을 채워라. 칸마다 `.` 인가, 아니면 `data`/`accessor` 와 `W`·`E`·`C` 중 무엇인가? **마지막 줄의 숫자**는?
- ★★★ `[2]` 세 자리의 own 키 목록을 **순서까지** 적어라. 생성자 쪽의 순서가 소스 순서와 같은가?
- ★★★ `[3]` 여덟 줄 각각에 무엇이 찍히나? 마지막 줄 `C.reveal(inst)` 는?
- ★★ `[4]` 여덟 줄의 `enumerable` 을 적고, `Object.keys` 두 줄을 적어라.

### 2. 클래스를 함수처럼 쓰면 (예측) ★★★

```js
// js16b-16b-rules.js
// class 가 「함수 위에 무엇을 더 얹나」 -- 던져서 확인한다. 예외는 종류 + 문구만 찍는다.
// ★ 이 파일은 "use strict" 가 없다. 클래스 몸통만 엄격이고 바깥은 비엄격이다.
const run = (label, fn) => {
  let r;
  try { r = "-> " + String(fn()); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(44) + r);
};

console.log("[1] typeof, and calling without new");
class K { m() { return "m"; } static s() { return "s"; } }
function F() { return "called as a plain function"; }
run("typeof class {}", () => typeof class {});
run("typeof K", () => typeof K);
run("F()   (plain function, no new)", () => F());
run("K()   (class, no new)", () => K());
run("K.call({})", () => K.call({}));
run("new K() instanceof K", () => new K() instanceof K);

console.log("");
console.log("[2] using the name before the declaration line");
run("use before `class Late {}` in the block", () => { const v = new Late(); class Late {} return v; });
run("use before `function Early() {}`", () => { const v = typeof Early; function Early() {} return v; });

console.log("");
console.log("[3] implicit globals and detached this -- inside a class body vs a plain function");
// ★ 탐침마다 전역 이름이 다르다. 엄격(클래스)을 먼저 돌린다.
class StrictProbe { leak() { leakedFromClass = 1; return "assigned"; } }
function sloppyProbe() { leakedFromFunction = 1; return "assigned"; }
run("class method: leakedFromClass = 1", () => new StrictProbe().leak());
run("plain function: leakedFromFunction = 1", () => sloppyProbe());
run("'leakedFromClass' in globalThis", () => "leakedFromClass" in globalThis);
run("'leakedFromFunction' in globalThis", () => "leakedFromFunction" in globalThis);
const leaked = ["leakedFromClass", "leakedFromFunction"].filter((n) => n in globalThis);
console.log("globals leaked by the 2 probes: " + JSON.stringify(leaked) + "  (" + leaked.length + " / 2)");
class ThisProbe { who() { return this === undefined ? "undefined" : typeof this; } }
function sloppyWho() { return this === globalThis ? "globalThis" : typeof this; }
const w = new ThisProbe().who;
run("detached class method: this is", () => w());
run("detached plain function: this is", () => sloppyWho());

console.log("");
console.log("[4] reassigning the class name from inside");
class Named { rename() { Named = 1; } }
run("Named = 1  (inside a method)", () => new Named().rename());
let Outer = class Inner { static who() { return typeof Inner; } };
run("class expression's own name, from inside", () => Outer.who());
run("typeof Inner  (from outside)", () => typeof Inner);

console.log("");
console.log("[5] has .prototype? can it be new-ed? (see topic 08)");
const forms = [
  ["class K", K],
  ["function F", F],
  ["K.prototype.m  (class method)", K.prototype.m],
  ["K.s  (static method)", K.s],
  ["() => {}", () => {}],
];
for (const [label, f] of forms) {
  let canNew;
  try { new f(); canNew = "new ok"; } catch (e) { canNew = e.constructor.name; }
  console.log(label.padEnd(32) + ("has .prototype " + ("prototype" in f)).padEnd(22) + canNew);
}
console.log("K.prototype writable?  " + Object.getOwnPropertyDescriptor(K, "prototype").writable +
            "   F.prototype writable?  " + Object.getOwnPropertyDescriptor(F, "prototype").writable);
```

- ★★★ `[1]` 여섯 줄 — 클래스를 `new` 없이 부르면? `call` 로 부르면?
- ★★ `[2]` 두 줄 — 선언 줄 앞에서 클래스를 쓰면? 함수는?
- ★★★ `[3]` — 이 파일은 `"use strict"` 가 **없다.** 두 탐침은 각각 무엇을 내놓고, `globalThis` 에 남은 이름은 몇 개인가? 떼어 낸 두 함수의 `this` 는?
- ★★ `[4]` 세 줄 — 메서드 안에서 클래스 이름에 대입하면? 클래스 식의 이름은 안과 밖에서 어떻게 보이나?
- ★★★ `[5]` 다섯 형태의 `prototype` 유무와 `new` 가능 여부 — 그리고 마지막 줄의 두 `writable` 은?

### 3. 필드 초기자와 생성자 본문의 순서 (예측) ★★★

```js
// js16b-16c-order.js
// 필드 초기자는 언제 도나 -- 생성자 본문과의 순서를 로그로 찍는다.
// ★ C# 12편(파생 필드 초기자가 제일 먼저)·C++ 13편(기반 → 파생)과 견줄 자리다.
const L = [];
const step = (msg, v) => { L.push(msg); return v; };

console.log("[1] one class -- field initializers vs the constructor body");
class One {
  a = step("field a initializer", 1);
  constructor() {
    step("constructor body starts  (this.a is " + this.a + ", this.b is " + this.b + ")");
    this.c = 3;
  }
  b = step("field b initializer  (sees this.a = " + this.a + ")", 2);
}
L.length = 0; new One();
L.forEach((m, i) => console.log("  " + (i + 1) + ". " + m));

console.log("");
console.log("[2] base and derived -- where do the derived fields go?");
class Base {
  baseField = step("Base field initializer", "B");
  constructor() { step("Base constructor body"); }
}
class Derived extends Base {
  derivedField = step("Derived field initializer", "D");
  constructor() {
    step("Derived constructor body -- before super()");
    super();
    step("Derived constructor body -- after super()  (derivedField is " + this.derivedField + ")");
  }
}
L.length = 0; new Derived();
L.forEach((m, i) => console.log("  " + (i + 1) + ". " + m));

console.log("");
console.log("[3] static parts -- when do they run?");
L.length = 0;
step("before the class");
class S {
  static first = step("static field first", 1);
  static { step("static {} block  (this === S: " + (this === S) + ", S.first set: " + (S.first === undefined ? "no" : "yes") + ")"); }
  static second = step("static field second  (this.name is " + this.name + ")");
  inst = step("instance field initializer  (only at new S())");
}
step("after the class");
new S();
step("after new S()");
L.forEach((m, i) => console.log("  " + (i + 1) + ". " + m));
```

- ★★★ `[1]` 세 줄의 순서와 괄호 안 값 — `b` 는 소스에서 생성자 **아래**에 있다.
- ★★★ `[2]` 다섯 줄의 순서 — 마지막 줄의 `derivedField` 는 무엇인가?
- ★★★ `[3]` 일곱 줄의 순서 — `static {}` 블록 안의 두 값과 `static second` 의 `this.name` 은?

### 4. 부모에 setter 가 있을 때 필드와 대입 (예측) ★★★

```js
// js16b-16d-define-vs-set.js
// 필드 x = 1 과 생성자 안의 this.x = 1 -- 부모 프로토타입에 같은 이름이 있으면 둘은 같은 일을 하나.
// 11편의 「스프레드 대 Object.assign」과 견줄 자리다.
"use strict";
const calls = [];
class Parent {
  set x(v) { calls.push("Parent setter got " + v); this._x = v; }
  get x() { return "getter:" + this._x; }
}
class ByField extends Parent { x = 1; }
class ByAssign extends Parent { constructor() { super(); this.x = 1; } }

const show = (label, o) => {
  const d = Object.getOwnPropertyDescriptor(o, "x");
  console.log(label.padEnd(12) + "own keys " + JSON.stringify(Object.keys(o)).padEnd(10) +
    "own x " + (d ? JSON.stringify(d) : "none").padEnd(72) + "o.x " + o.x);
};

console.log("[1] a setter named x on the parent's prototype");
calls.length = 0; const f = new ByField();
show("x = 1", f);
console.log("            setter calls " + JSON.stringify(calls));
calls.length = 0; const a = new ByAssign();
show("this.x = 1", a);
console.log("            setter calls " + JSON.stringify(calls));

console.log("");
console.log("[2] a NON-writable x on the parent's prototype (strict)");
class Frozen {}
Object.defineProperty(Frozen.prototype, "x", { value: "locked", writable: false });
class FieldOverRO extends Frozen { x = 1; }
class AssignOverRO extends Frozen { constructor() { super(); this.x = 1; } }
for (const [label, C] of [["x = 1", FieldOverRO], ["this.x = 1", AssignOverRO]]) {
  try { const o = new C(); console.log(label.padEnd(12) + "ok, own x = " + o.x); }
  catch (e) { console.log(label.padEnd(12) + e.constructor.name + " " + e.message); }
}

console.log("");
console.log("[3] the same two operations outside classes (topic 11)");
const target = Object.create(Parent.prototype);
calls.length = 0;
Object.defineProperty(target, "x", { value: 2, writable: true, enumerable: true, configurable: true });
console.log("defineProperty  setter calls " + calls.length + "   own x? " + Object.hasOwn(target, "x"));
const target2 = Object.create(Parent.prototype);
calls.length = 0;
target2.x = 2;
console.log("plain  o.x = 2  setter calls " + calls.length + "   own x? " + Object.hasOwn(target2, "x"));
```

- ★★★ `[1]` 두 인스턴스 각각의 **own 키 · own `x` 의 디스크립터 · `o.x` · setter 호출 목록**을 적어라.
- ★★★ `[2]` 부모 프로토타입의 `x` 가 쓰기 불가일 때 두 클래스는 각각 무엇을 내놓나?
- ★★ `[3]` 클래스 밖의 두 줄 — setter 호출 횟수와 own 여부는?

### 5. `#private` 를 남의 객체에 들이대면 (예측) ★★★

```js
// js16b-16e-private.js
// #private 의 경계 -- 누가 읽을 수 있고, 남의 객체에 들이대면 무엇이 나오나.
const run = (label, fn) => {
  let r;
  try { r = "-> " + String(fn()); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(56) + r);
};

class Account {
  #balance;
  constructor(b) { this.#balance = b; }
  static isAccount(o) { return #balance in o; }
  static peek(o) { return o.#balance; }
  sameAs(other) { return this.#balance === other.#balance; }
}
class Lookalike { balance = 10; }
const a1 = new Account(10);
const a2 = new Account(10);

console.log("[1] #x in obj -- the brand check (ES2022)");
run("Account.isAccount(a1)", () => Account.isAccount(a1));
run("Account.isAccount(new Lookalike())", () => Account.isAccount(new Lookalike()));
run("Account.isAccount({})", () => Account.isAccount({}));
run("Account.isAccount(Object.create(Account.prototype))", () => Account.isAccount(Object.create(Account.prototype)));
run("Object.create(Account.prototype) instanceof Account", () => Object.create(Account.prototype) instanceof Account);
run("Account.isAccount(7)", () => Account.isAccount(7));

console.log("");
console.log("[2] reading #balance off something that lacks it");
run("Account.peek(a1)", () => Account.peek(a1));
run("a1.sameAs(a2)  (another instance, same class)", () => a1.sameAs(a2));
run("Account.peek(new Lookalike())", () => Account.peek(new Lookalike()));
run("Account.peek(Object.create(Account.prototype))", () => Account.peek(Object.create(Account.prototype)));
run("Account.peek(new Proxy(a1, {}))", () => Account.peek(new Proxy(a1, {})));

console.log("");
console.log("[3] #x written outside any class body");
run("new Function('o', 'return o.#balance')", () => new Function("o", "return o.#balance"));
run("new Function('class Q { m() { return this.#nope } }')", () => new Function("class Q { m() { return this.#nope } }"));
```

- ★★★ `[1]` 여섯 줄 — 특히 **`Object.create(Account.prototype)` 의 두 줄**은 서로 같은 답인가? 원시값 `7` 에는?
- ★★★ `[2]` 다섯 줄 — 같은 클래스의 다른 인스턴스는? 칸이 없는 객체와 **트랩이 하나도 없는 프록시**는?
- ★★ `[3]` 두 줄 — 무엇이 언제 던져지나?

### 6. 브랜드 태그 · 트랩 로그 · 동결 · 두 번 평가 (예측) ★★★

```js
// js16b-16f-private-windows.js
// #private 는 네 창에 다 안 보이나 -- 브랜드 태그(③)·Proxy 트랩 로그(①)로 한 번 더 묻고,
// 「있는데 안 보인다」는 것을 클래스 안쪽의 #x in 으로 답한다(창을 바꿔 물었다).
const run = (label, fn) => {
  let r;
  try { r = "-> " + String(fn()); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(46) + r);
};

class WithPriv { #x = 1; field = "f"; static has(o) { return #x in o; } static bump(o) { o.#x += 1; return o.#x; } }
class NoPriv { field = "f"; }
const w = new WithPriv();

console.log("[1] window 3 -- the brand tag, with and without #x");
run("toString.call(new WithPriv())", () => Object.prototype.toString.call(w));
run("toString.call(new NoPriv())", () => Object.prototype.toString.call(new NoPriv()));
run("getOwnPropertyNames(new WithPriv())", () => JSON.stringify(Object.getOwnPropertyNames(w)));

console.log("");
console.log("[2] window 1 -- a Proxy that logs every trap");
const L = [];
const handler = {};
for (const t of ["get", "set", "has", "getOwnPropertyDescriptor", "defineProperty", "ownKeys", "getPrototypeOf"]) {
  handler[t] = (...a) => { L.push(t + (typeof a[1] === "string" ? "(" + a[1] + ")" : "")); return Reflect[t](...a); };
}
const p = new Proxy(w, handler);
L.length = 0; run("p.field", () => p.field); console.log("  trap log " + JSON.stringify(L));
L.length = 0; run("WithPriv.has(p)", () => WithPriv.has(p)); console.log("  trap log " + JSON.stringify(L));
L.length = 0; run("WithPriv.bump(p)", () => WithPriv.bump(p)); console.log("  trap log " + JSON.stringify(L));

console.log("");
console.log("[3] #x after Object.freeze");
Object.freeze(w);
run("Object.isFrozen(w)", () => Object.isFrozen(w));
run("WithPriv.bump(w)  (after freeze)", () => WithPriv.bump(w));
run("w.field = 'g'  (after freeze, sloppy file)", () => { w.field = "g"; return w.field; });

console.log("");
console.log("[4] two classes that both spell #x");
class Other { #x = 1; }
run("WithPriv.has(new Other())  (same spelling #x)", () => WithPriv.has(new Other()));
const make = () => class { #x = 1; static has(o) { return #x in o; } };
const K1 = make();
const K2 = make();
run("K1.has(new K1())", () => K1.has(new K1()));
run("K1.has(new K2())  (same source, 2nd eval)", () => K1.has(new K2()));
```

- ★★★ `[1]` 브랜드 태그 두 줄은 같은가 다른가?
- ★★★ `[2]` 세 호출의 결과와 **각각의 트랩 로그**를 적어라.
- ★★ `[3]` 얼린 뒤의 세 줄 — `#x` 를 늘리는 호출과 공개 필드 대입은 각각 어떻게 되나?
- ★★ `[4]` 세 줄 — 철자가 같은 `#x` 와 **같은 소스를 두 번 평가한** 클래스는?

### 7. `typeof` 가 `function` 인데 함수처럼 못 부르는 이유 (왜) ★★

- ★★ `typeof` 는 무엇을 말해 주고 무엇을 말해 주지 않는가?
- ★★★ 「`prototype` 이 있으면 `new` 가 된다」가 틀린 반례를 08번에서 둘 대라. 클래스 메서드와 정적 메서드는 어느 칸인가?
- ★★ 15번에서 `.prototype` 을 갈아끼워 `instanceof` 를 바꿨다. 클래스의 `.prototype` 은 **어떤 플래그**인가? 근거가 된 출력 한 줄과, **이 문서가 실제로 대입까지 던졌는지**를 답하라.
- ★ 클래스 몸통이 엄격이라는 사실이 **떼어 낸 메서드의 `this`** 에 주는 결과는? 처방은 어느 주제에 있나?

### 8. JS 의 필드 순서는 C# 쪽인가 C++ 쪽인가 (연결) ★★★

- ★★★ C#·C++·JS 세 열을 단계별로 적어라. **파생의 필드(멤버) 초기자**가 각 언어에서 몇 번째인가?
- ★★★ 그래서 JS 는 어느 쪽과 같은가? 그 판정의 근거가 된 **로그 번호**는?
- ★★ JS 에만 있는 단계가 하나 있다. 무엇인가? 그 자리에서 `this` 를 쓰면 무엇이 되나 — **이 문서는 그것을 던졌나**?
- ★ C++ 의 기반/파생 순서는 **어느 문서가** 실측했나? C++ 13번은 무엇을 쟀나?
- ★ 이 차이가 실무에서 물리는 자리는? (**기반 생성자가 파생이 덮어쓴 메서드를 부를 때** — 그것은 어느 주제의 일인가?)

### 9. `#private` 는 왜 「잴 것이 없다」가 아니라 「창을 바꿔 물었다」인가 (경계) ★★★

- ★★★ 18-B 의 「부적용(잴 것이 없다)」과 「제5의 상태(창을 바꿔 물었다)」를 한 문장씩 정의하라. 둘을 가르는 **관찰 한 줄**은?
- ★★★ 네 창(①②③④)이 각각 `#private` 앞에서 **무엇을 내놓았나**? ④ 창은 클래스 밖과 안에서 어떻게 다른가?
- ★★★ 바꾼 창(`#x in o`)이 **못 보는 것** 셋을 대라.
- ★★ `'#secret' in inst` 가 `false` 인 것은 무엇을 물은 결과인가? 진짜 브랜드 검사와 **글자로** 어떻게 다른가?

### 10. 클래스 메서드가 비열거라서 생기는 일 (연결) ★★

- ★★★ 명세의 어느 연산이 그 `false` 를 넘기나? 필드는 왜 `true` 인가?
- ★★ 옛 방식(`F.prototype.m = function`)을 클래스로 옮기면 인스턴스의 `for...in` 결과가 어떻게 바뀌나? `Object.keys` 는? **이 문서가 그것을 돌렸나**?
- ★★ `'method' in new Modern()` 은? 「비열거」는 「없다」인가?
- ★ `for...in` 의 규칙 자체는 어느 주제가 정본인가?

### 11. 보장인가 엔진 사정인가 (연결) ★★★

- ★★★ **명세가 정하는 것** 셋과 **V8 의 문구** 셋을 대라.
- ★★ `structuredClone` 은 누가 정하는 API 인가? 그 줄을 명세 보장으로 적으면 왜 틀리나?
- ★★ 이 주제에서 **부적용인 창**은 무엇이고 왜 부적용인가? **안 돌린 것**과 **안 잰 것**은?
- ★★ 엄격/비엄격을 이 주제는 어떻게 견줬나? 그때 지킨 순서 규칙 둘은?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **체인 조회·쓰기 경로** · **`extends`·`super`·`new.target`** · **열거 규칙** · **`Proxy` 트랩 계약** · **클래스 TDZ** · **떼어 낸 메서드의 `this`** · **「정의 대 대입」을 처음 잰 곳** 은 각각 어느 주제가 정본인가?
- ★★★ 15번에서 **다시 재지 않고 받아 쓴 것** 넷을 대라.
- ★★ 11번의 「정의 대 대입」과 이 주제의 그것은 **어느 자리**에서 같은 갈림길인가?
- ★ 이 주제가 **끝까지 책임지는 것** 셋을 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
