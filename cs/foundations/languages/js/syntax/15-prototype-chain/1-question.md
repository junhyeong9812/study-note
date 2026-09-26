# js/syntax/15 — 프로토타입 체인: 「읽기는 체인을 타고, 쓰기는 수신자에 내려앉는다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> 프로퍼티 조회는 **어느 칸에서 답이 나와도 같은 값**을 내놓는다 — **값으로는 원리상 경로를 못 가른다.**
> 그래서 체인의 각 칸에 `Proxy` 를 씌워 **트랩 로그**로 경로를 찍었다.
> **2번 문항이 이 주제의 중심이고, 3번이 그 결론을 평범한 객체로 되짚는다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **읽기가 어디서 멈추나**(그리고 「없다」를 무엇으로 증명하나)
> ② ★★★ **쓰기가 어디에 내려앉나**(그리고 그것이 깨지는 예외 셋)
> ③ **`prototype`·`[[Prototype]]`·`__proto__` 세 이름을 가르기.**
>
> ★★★ **답을 적을 때 「값」만 적으면 절반도 못 맞힌 것이다.**
> 2번은 **로그 줄 수**, 3번은 **own 인가 아닌가**, 5번은 **어느 쪽이 이겼나**를 같이 적어야 답이다.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★★★ **이 주제에는 두 판이 갈린 줄이 하나도 없다.** 그래서 「판이 갈렸나」를 묻는 문항이 없다 —
> 대신 10번이 **무엇이 보장이고 무엇이 이 엔진의 사정인지**를 묻는다.
> ★ **엄격/비엄격을 묻는 문항도 없다** — 이 주제의 다섯 탐침 중 둘은 엄격 고정이고 셋은 모드와 무관하다.
> 모드가 답을 바꾸는 칸은 [14번](../14-property-descriptors-and-freezing/2-summary.md)의 격자가 이미 갖고 있다.
>
> **선행** — [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) · [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md).
> ★★★ **07번을 먼저 떠올려라** — 7번 문항의 답이 거기 있다.

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1\~5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **2번은 「무엇이 나오나」가 아니라 「무엇이 몇 줄 찍히나」를 묻는다.** 로그를 먼저 적어라.
- ★★★ **3번과 5번은 매 줄마다 `own?` 칸을 같이 적어라.** own 인가 아닌가가 이 주제의 답이다.
- ★★ **4번은 「되는 것」과 「막히는 것」을 갈라서** 적어야 답이다. 개수를 세라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「느리다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 체인을 `null` 까지 찍으면 무엇이 나오나 (예측) ★★

```js
// js12b-15a-chain.js
// 체인을 글자로 찍는다 -- getPrototypeOf 를 null 까지 돌며 각 칸의 이름을 한 줄로.
// 이름은 「그 프로토타입 객체가 스스로 들고 있는 constructor」로 짓는다(상속된 것을 읽으면 전부 Object 가 된다).
const own = Object.prototype.hasOwnProperty;
function nameOf(p) {
  if (p === null) return "null";
  if (own.call(p, "constructor") && typeof p.constructor === "function" && p.constructor.name) {
    return p.constructor.name + ".prototype";
  }
  if (typeof p === "function" && p.name) return p.name + " (the class object)";
  const brand = Object.prototype.toString.call(p);
  return "(anonymous " + brand + ")";
}
function chain(x) {
  const out = [];
  let cur;
  try { cur = Object.getPrototypeOf(Object(x)); }
  catch (e) { return e.constructor.name + " " + e.message; }
  let guard = 0;
  while (cur !== null && guard < 20) { out.push(nameOf(cur)); cur = Object.getPrototypeOf(cur); guard += 1; }
  out.push("null");
  return out.join(" -> ");
}

class A { }
class B extends A { }
function Ctor() { }
const nullProto = Object.create(null);

console.log("[1] chains, each printed to null");
const rows = [
  ["{}", {}],
  ["[]", []],
  ["function f() {}", function f() { }],
  ["() => {}", () => { }],
  ["function* g() {}", function* g() { }],
  ["async function h() {}", async function h() { }],
  ["new A   (class A)", new A()],
  ["new B   (class B extends A)", new B()],
  ["new Ctor  (function Ctor)", new Ctor()],
  ["new Map()", new Map()],
  ["new Error('x')", new Error("x")],
  ["new TypeError('x')", new TypeError("x")],
  ["/re/", /re/],
  ["1  (number primitive)", 1],
  ["'s'  (string primitive)", "s"],
  ["Symbol('s')", Symbol("s")],
  ["Object.create(null)", nullProto],
  ["Object.create(Object.create(null))", Object.create(nullProto)],
  ["Object.create({ a: 1 })", Object.create({ a: 1 })],
];
for (const [label, v] of rows) console.log(label.padEnd(36) + chain(v));

console.log("");
console.log("[2] the constructors themselves are objects too -- their chain is different");
for (const [label, v] of [["A  (the class object)", A], ["B  (extends A)", B],
                          ["Ctor  (function)", Ctor], ["Object", Object], ["Function", Function]]) {
  console.log(label.padEnd(36) + chain(v));
}

console.log("");
console.log("[3] prototype  vs  [[Prototype]] -- two different slots with confusable names");
console.log("Ctor.prototype                       " + Object.prototype.toString.call(Ctor.prototype) +
  "   own keys " + JSON.stringify(Object.getOwnPropertyNames(Ctor.prototype)));
console.log("Object.getPrototypeOf(Ctor)          " + (Object.getPrototypeOf(Ctor) === Function.prototype ? "Function.prototype" : "?"));
console.log("Ctor.prototype === getPrototypeOf(Ctor)?  " + (Ctor.prototype === Object.getPrototypeOf(Ctor)));
const inst = new Ctor();
console.log("getPrototypeOf(new Ctor) === Ctor.prototype?  " + (Object.getPrototypeOf(inst) === Ctor.prototype));
console.log("does an instance have .prototype?    " + ("prototype" in inst));
console.log("does an arrow function have one?     " + own.call(() => { }, "prototype"));
console.log("does a class method have one?        " + own.call((class K { m() { } }).prototype.m, "prototype"));
console.log("does class A have one?               " + own.call(A, "prototype"));
```

- ★★ `[1]` 에서 **칸이 한 개인 줄**·**두 개인 줄**·**세 개 이상인 줄**을 갈라 보라.
- ★★★ `Object.create(null)` 줄에는 무엇이 찍히는가?
- ★★★ `Object.create(Object.create(null))` 의 가운데 칸에는 **왜 이름을 못 붙이는가**?
  그리고 이 스크립트는 **무엇으로** 칸의 이름을 짓는가?
- ★★ `function* g() {}` 와 `() => {}` 의 체인은 **몇 칸이 다른가**?
- ★★ 원시값 `1` 에 체인이 찍히는 것은 **무슨 뜻인가** — 원시값이 객체라는 뜻인가?
- ★★★ `[2]` 에서 **`B` 의 윗집**은 무엇인가? 그 사실이 **무엇을 설명하는가**?
- ★★★ `[3]` 의 `Ctor.prototype === getPrototypeOf(Ctor)?` 는 무엇을 답하는가?
- ★ `[3]` 의 마지막 네 줄 중 **`true` 는 몇 개**인가?

### 2. 조회가 어디서 멈추나 — 트랩 로그를 적어라 (예측) ★★★ 이 주제의 축

```js
// js12b-15b-proxy.js
// ★ 이 주제의 본체 -- 체인의 각 칸에 Proxy 로 로그를 심어 「조회가 어디서 멈추나」를 증명한다.
// 값으로는 안 갈린다(어느 칸에서 왔든 같은 값이 나온다). 트랩 로그만이 경로를 말한다.
const L = [];
function tap(name, target) {
  return new Proxy(target, {
    get(t, k, r) { if (typeof k === "string") L.push(name + ".get(" + k + ")"); return Reflect.get(t, k, r); },
    set(t, k, v, r) { L.push(name + ".set(" + String(k) + ")"); return Reflect.set(t, k, v, r); },
    has(t, k) { L.push(name + ".has(" + String(k) + ")"); return Reflect.has(t, k); },
    getPrototypeOf(t) { L.push(name + ".getPrototypeOf"); return Reflect.getPrototypeOf(t); },
    getOwnPropertyDescriptor(t, k) { L.push(name + ".gopd(" + String(k) + ")"); return Reflect.getOwnPropertyDescriptor(t, k); },
  });
}
const A = tap("A", { fromA: "a" });
const Bt = Object.create(A); Bt.fromB = "b";
const B = tap("B", Bt);
const Ct = Object.create(B); Ct.fromC = "c";
const C = tap("C", Ct);

const run = (label, fn) => {
  L.length = 0;
  let r;
  try { r = String(fn()); } catch (e) { r = e.constructor.name + " " + e.message; }
  console.log(label.padEnd(20) + ("-> " + r).padEnd(16) + "trap log " + JSON.stringify(L));
};

console.log("[1] reading -- the lookup walks down until it finds the key");
run("C.fromC", () => C.fromC);
run("C.fromB", () => C.fromB);
run("C.fromA", () => C.fromA);
run("C.nope", () => C.nope);
run("C.toString", () => typeof C.toString);

console.log("");
console.log("[2] 'in' and hasOwnProperty walk differently");
run("'fromA' in C", () => "fromA" in C);
run("hasOwn(C,'fromA')", () => Object.hasOwn(C, "fromA"));
run("hasOwn(C,'fromC')", () => Object.hasOwn(C, "fromC"));

console.log("");
console.log("[3] writing -- the write does NOT walk to where the value lives");
run("C.fromA = 'W'", () => { C.fromA = "W"; return "done"; });
console.log("after the write:");
run("C.fromA  (read)", () => C.fromA);
console.log("A still holds       -> " + Reflect.get(A, "fromA"));
console.log("own keys of C's target -> " + JSON.stringify(Object.getOwnPropertyNames(Ct)));

console.log("");
console.log("[4] a setter on the chain -- now the write DOES walk");
const log2 = [];
const base = {
  _v: "base",
  get s() { return this._v; },
  set s(v) { log2.push("setter ran, this is the " + (this === mid ? "MIDDLE" : this === leaf ? "LEAF" : "BASE") + " object"); this._v = v; },
};
const mid = Object.create(base);
const leaf = Object.create(mid);
leaf.s = "written";
console.log("leaf.s = 'written'   log " + JSON.stringify(log2));
console.log("own keys of leaf     " + JSON.stringify(Object.getOwnPropertyNames(leaf)));
console.log("base._v              " + base._v + "   leaf._v " + leaf._v + "   leaf.s " + leaf.s);
```

- ★★★ `[1]` 의 다섯 줄에서 **트랩 로그가 각각 몇 줄**인가?
- ★★★ `C.nope` 의 결과는 무엇인가? **예외인가 값인가**?
- ★★★ `C.nope` 와 `C.toString` 의 **로그 길이가 같은데 답이 다르다.** 그 사실이 말하는 것은?
- ★★ `[2]` 에서 `'fromA' in C` 와 `Object.hasOwn(C, 'fromA')` 는 **각각 무슨 트랩을 몇 줄** 남기고 무엇을 답하는가?
- ★★★ `[3]` 의 `C.fromA = 'W'` 는 **어떤 트랩이 어떤 순서로** 찍히는가? **네 번째 줄**이 특히 중요한 이유는?
- ★★★ 그 쓰기 뒤에 **`A` 가 들고 있는 값**과 **`C` 의 타깃 own 키**는 각각 무엇인가?
- ★★ 쓰기 **직후의 읽기**는 로그가 몇 줄인가? 왜 달라졌는가?
- ★★★ `[4]` 에서 setter 안의 `this` 는 **누구**인가? 그래서 `_v` 는 **어느 객체**에 생기는가?

### 3. 같은 이름에 대입하면 어디에 내려앉나 (예측) ★★★

```js
// js12b-15c-shadow.js
// 읽기/쓰기 비대칭 -- 이 주제의 급소. 프록시 없이 평범한 객체로 다시 확인한다.
// 비엄격 블록과 엄격 블록을 섞지 않는다. 여기는 전부 엄격이다.
"use strict";
const own = Object.prototype.hasOwnProperty;
const line = (a, b) => console.log(String(a).padEnd(38) + b);

console.log("[1] read walks the chain; write lands on the receiver");
const proto = { v: "from proto", n: 0 };
const a = Object.create(proto);
const b = Object.create(proto);
line("a.v  (before)", a.v + "   ownProperty? " + own.call(a, "v"));
a.v = "own on a";
line("a.v = 'own on a'  -> a.v", a.v + "   ownProperty? " + own.call(a, "v"));
line("proto.v", proto.v);
line("b.v  (the sibling)", b.v + "   ownProperty? " + own.call(b, "v"));
delete a.v;
line("delete a.v  -> a.v", a.v + "   ownProperty? " + own.call(a, "v"));

console.log("");
console.log("[2] the trap: a shared MUTABLE value on the prototype");
const shared = { list: [], count: 0 };
const x = Object.create(shared);
const y = Object.create(shared);
x.list.push("pushed through x");
x.count += 1;
line("x.list.push(...)  -> y.list", JSON.stringify(y.list));
line("x.count += 1      -> x.count", x.count + "   own? " + own.call(x, "count"));
line("                  -> y.count", y.count + "   own? " + own.call(y, "count"));
line("                  -> shared.count", shared.count);

console.log("");
console.log("[3] when the prototype's property is NOT writable, the write is blocked (strict: TypeError)");
const ro = Object.defineProperty({}, "v", { value: "read only", writable: false, enumerable: true, configurable: true });
const kid = Object.create(ro);
try { kid.v = "try"; line("kid.v = 'try'", "OK, kid.v = " + kid.v); }
catch (e) { line("kid.v = 'try'", e.constructor.name + " " + e.message); }
line("own? after the failed write", own.call(kid, "v"));
Object.defineProperty(kid, "v", { value: "defined", writable: true, enumerable: true, configurable: true });
line("defineProperty on kid instead", "kid.v = " + kid.v + "   own? " + own.call(kid, "v") + "   ro.v = " + ro.v);

console.log("");
console.log("[4] a setter on the prototype takes the write -- and `this` is the receiver");
const withSetter = {
  _store: "proto store",
  get s() { return this._store; },
  set s(v) { this._store = v; },
};
const child = Object.create(withSetter);
child.s = "child wrote";
line("child.s = 'child wrote'", "child.s = " + child.s);
line("own keys of child", JSON.stringify(Object.getOwnPropertyNames(child)));
line("withSetter._store", withSetter._store);
line("did 's' become an own property?", own.call(child, "s"));

console.log("");
console.log("[5] getter-only on the prototype -- strict throws, and nothing is shadowed");
const getterOnly = { get s() { return "always this"; } };
const c2 = Object.create(getterOnly);
try { c2.s = "nope"; line("c2.s = 'nope'", "OK, c2.s = " + c2.s); }
catch (e) { line("c2.s = 'nope'", e.constructor.name + " " + e.message); }
line("own keys of c2", JSON.stringify(Object.getOwnPropertyNames(c2)));

console.log("");
console.log("[6] four ways to ask 'does it have v?' on a shadowing object");
const p2 = { v: 1 };
const o2 = Object.create(p2);
line("'v' in o2", String("v" in o2));
line("Object.hasOwn(o2, 'v')", String(Object.hasOwn(o2, "v")));
line("o2.hasOwnProperty('v')", String(o2.hasOwnProperty("v")));
line("Object.keys(o2)", JSON.stringify(Object.keys(o2)));
o2.v = 2;
line("after o2.v = 2 : Object.hasOwn", String(Object.hasOwn(o2, "v")));
line("after o2.v = 2 : Object.keys", JSON.stringify(Object.keys(o2)));
line("after o2.v = 2 : p2.v", String(p2.v));
```

- ★★★ `[1]` 의 다섯 줄을 **값과 `ownProperty?` 를 짝지어** 적어 보라. `proto.v` 와 `b.v` 는 바뀌는가?
- ★★★ `delete a.v` 뒤에 무엇이 나오는가? 그 사실이 「덮었다」와 「가렸다」 중 어느 쪽을 말하는가?
- ★★★ `[2]` 에서 `x.list.push(...)` 뒤의 **`y.list`** 와, `x.count += 1` 뒤의 **`y.count`·`shared.count`** 를 적어 보라.
  **두 줄의 결과가 왜 다른가**?
- ★★ `[3]` 에서 `kid.v = 'try'` 는 무엇을 내놓고, 그 뒤 **`own?` 은 무엇**인가?
- ★★★ 바로 다음 줄의 `defineProperty` 는 **왜 통과하는가**?
- ★★★ `[4]` 에서 `child` 의 **own 키 목록**은 무엇인가? `s` 는 own 이 되는가? `withSetter._store` 는 바뀌는가?
- ★★ `[5]` 에서 `c2` 의 **own 키 목록**은 무엇인가?
- ★ `[6]` 의 네 가지 창이 섀도잉 **전**과 **후**에 각각 무엇을 답하는가?

### 4. 계단이 없는 객체에는 무엇을 물을 수 있나 (예측) ★★★

```js
// js12b-15d-misc.js
// Object.create(null) · __proto__ · instanceof · new 가 잇는 것.
// 예외는 전부 try/catch 로 받아 타입과 메시지만 찍는다.
const own = Object.prototype.hasOwnProperty;
const shot = (label, fn) => {
  try { console.log(label.padEnd(40) + "-> " + String(fn())); }
  catch (e) { console.log(label.padEnd(40) + "-> " + e.constructor.name + " " + e.message); }
};

console.log("[1] Object.create(null) -- an object with no chain at all");
const bare = Object.create(null);
bare.k = 1;
shot("typeof bare", () => typeof bare);
shot("bare.toString", () => String(bare.toString));
shot("bare.hasOwnProperty", () => String(bare.hasOwnProperty));
shot("Object.keys(bare)", () => JSON.stringify(Object.keys(bare)));
shot("Object.prototype.toString.call(bare)", () => Object.prototype.toString.call(bare));
shot("JSON.stringify(bare)", () => JSON.stringify(bare));
shot("String(bare)", () => String(bare));
shot("bare + ''", () => bare + "");
shot("`${bare}`", () => `${bare}`);
shot("bare == '[object Object]'", () => bare == "[object Object]");
shot("'k' in bare", () => "k" in bare);
shot("Object.hasOwn(bare, 'k')", () => Object.hasOwn(bare, "k"));
console.log("console.log(bare) prints ->");
console.log(bare);
console.log("util.inspect(bare)       -> " + require("util").inspect(bare));

console.log("");
console.log("[2] __proto__ is an accessor that LIVES ON Object.prototype -- so a bare object has none");
const d = Object.getOwnPropertyDescriptor(Object.prototype, "__proto__");
console.log("descriptor on Object.prototype       get=" + typeof d.get + " set=" + typeof d.set +
  " e=" + d.enumerable + " c=" + d.configurable);
console.log("own.call(Object.prototype,'__proto__')  " + own.call(Object.prototype, "__proto__"));
const plain = {};
console.log("({}).__proto__ === Object.prototype    " + (plain.__proto__ === Object.prototype));
bare.__proto__ = { marker: "M" };
console.log("bare.__proto__ = {...} -> real proto?  " + (Object.getPrototypeOf(bare) === null ? "still null" : "changed"));
console.log("                       -> own keys     " + JSON.stringify(Object.getOwnPropertyNames(bare)));
console.log("                       -> bare.marker  " + String(bare.marker));
const viaSet = {};
Object.setPrototypeOf(viaSet, { marker: "M" });
console.log("setPrototypeOf on a normal object      " + viaSet.marker);
shot("Object.setPrototypeOf({}, 5)", () => JSON.stringify(Object.getPrototypeOf(Object.setPrototypeOf({}, 5))));
shot("Object.getPrototypeOf(null)", () => Object.getPrototypeOf(null));
shot("Object.getPrototypeOf(5)", () => Object.prototype.toString.call(Object.getPrototypeOf(5)));

console.log("");
console.log("[3] what `new` links -- and what happens if you rewire .prototype afterwards");
function Ctor() { this.made = true; }
Ctor.prototype.hello = () => "hi";
const i1 = new Ctor();
console.log("getPrototypeOf(i1) === Ctor.prototype   " + (Object.getPrototypeOf(i1) === Ctor.prototype));
console.log("i1.constructor === Ctor                 " + (i1.constructor === Ctor));
console.log("own.call(i1, 'constructor')             " + own.call(i1, "constructor"));
const manual = Object.create(Ctor.prototype);
Ctor.call(manual);
console.log("hand-rolled new: same shape?            " +
  (Object.getPrototypeOf(manual) === Ctor.prototype && manual.made === i1.made));
Ctor.prototype = { note: "brand new prototype object" };
const i2 = new Ctor();
console.log("after reassigning Ctor.prototype:");
console.log("  i1.hello()                            " + i1.hello());
console.log("  i2.hello                              " + String(i2.hello));
console.log("  i2.note                               " + i2.note);
console.log("  i1 instanceof Ctor                    " + (i1 instanceof Ctor));
console.log("  i2 instanceof Ctor                    " + (i2 instanceof Ctor));
console.log("  i2.constructor.name                   " + i2.constructor.name);

console.log("");
console.log("[4] instanceof walks the chain -- and Symbol.hasInstance can replace the walk");
class P { }
class Q extends P { }
const q = new Q();
console.log("q instanceof Q / P / Object             " + (q instanceof Q) + " / " + (q instanceof P) + " / " + (q instanceof Object));
console.log("same answer by hand (walk to null)      " + (() => {
  let cur = Object.getPrototypeOf(q);
  const seen = [];
  while (cur !== null) { seen.push(cur === Q.prototype ? "Q" : cur === P.prototype ? "P" : cur === Object.prototype ? "Object" : "?"); cur = Object.getPrototypeOf(cur); }
  return seen.join(" -> ");
})());
console.log("bare instanceof Object                  " + (bare instanceof Object));
const Never = class { static [Symbol.hasInstance]() { return false; } };
const Always = class { static [Symbol.hasInstance]() { return true; } };
console.log("new Never() instanceof Never            " + (new Never() instanceof Never));
console.log("'a string' instanceof Always            " + ("a string" instanceof Always));
shot("({}) instanceof {}", () => ({}) instanceof {});
shot("({}) instanceof (() => {})", () => ({}) instanceof (() => { }));
console.log("Object.prototype.isPrototypeOf(q)       " + Object.prototype.isPrototypeOf(q));
console.log("P.prototype.isPrototypeOf(q)            " + P.prototype.isPrototypeOf(q));
```

- ★★★ `[1]` 에서 **`TypeError` 가 나는 줄은 몇 줄**이고 어느 줄인가?
- ★★★ `bare == '[object Object]'` 까지 터지는 이유는 무엇인가?
- ★★★ 그런데 **`Object.prototype.toString.call(bare)` 는 답한다.** 무엇이라고 답하는가? 그것이 왜 가능한가?
- ★★ `Object.keys`·`JSON.stringify`·`in`·`Object.hasOwn` 은 되고 `bare.toString()` 은 안 된다.
  **되는 것들의 공통점**을 한 문장으로.
- ★★★ `[2]` 에서 `bare.__proto__ = { marker: "M" }` 뒤의 **세 줄**(실제 프로토타입 · own 키 · `bare.marker`)을 적어 보라.
- ★★★ 그 결과가 평범한 객체와 다른 이유는? `__proto__` 는 **어디에 사는 무엇**인가?
- ★★ `[3]` 에서 `Ctor.prototype` 을 새 객체로 갈아끼운 뒤 **`i1 instanceof Ctor`** 는 무엇인가?
  `i1.hello()` 는 여전히 도는가?
- ★★ `i2.constructor.name` 이 **왜 그렇게 나오는가**?
- ★★ `[4]` 에서 **`bare instanceof Object`** 는 무엇인가? 왜 그런가?
- ★ `({}) instanceof {}` 와 `({}) instanceof (() => {})` 의 **`TypeError` 문구가 다르다.** 무엇이 다른가?

### 5. 파이썬과 같은 질문을 던지면 어느 쪽이 이기나 (예측) ★★★

```js
// js12b-15e-pycontrast.js
// 파이썬 29편의 「데이터 디스크립터가 인스턴스 칸을 이긴다」와 견줄 자리를 JS 에서 전수로 찍는다.
// 묻는 것 하나 -- 「접근자가 체인에 있을 때, own 프로퍼티가 생기면 누가 이기나」.
"use strict";
const own = Object.prototype.hasOwnProperty;
const line = (a, b) => console.log(String(a).padEnd(50) + b);

console.log("[1] read -- does an own property beat an accessor on the prototype?");
const accProto = {
  get v() { return "ACCESSOR on prototype"; },
  set v(x) { this._viaSetter = x; },
};
const kid = Object.create(accProto);
line("kid.v  (no own property yet)", kid.v);
Object.defineProperty(kid, "v", { value: "OWN data property", writable: true, enumerable: true, configurable: true });
line("after defineProperty(kid, 'v')  -> kid.v", kid.v);
line("  own? / accessor still on proto?", own.call(kid, "v") + " / " + (typeof Object.getOwnPropertyDescriptor(accProto, "v").get));
line("  accProto.v itself", accProto.v);

console.log("");
console.log("[2] write -- the accessor on the prototype takes it, so NO own property appears");
const kid2 = Object.create(accProto);
kid2.v = "written through";
line("kid2.v = 'written through'", "kid2.v = " + kid2.v);
line("  own keys of kid2", JSON.stringify(Object.getOwnPropertyNames(kid2)));
line("  where did the value land?", "kid2._viaSetter = " + kid2._viaSetter + " · accProto._viaSetter = " + String(accProto._viaSetter));

console.log("");
console.log("[3] the same three cells for a PLAIN data property on the prototype");
const dataProto = { v: "DATA on prototype" };
const kid3 = Object.create(dataProto);
line("kid3.v  (before)", kid3.v + "   own? " + own.call(kid3, "v"));
kid3.v = "written through";
line("kid3.v = 'written through'", kid3.v + "   own? " + own.call(kid3, "v"));
line("  dataProto.v", dataProto.v);

console.log("");
console.log("[4] the chain is made of OBJECTS, not classes -- two instances of one class");
class C { }
C.prototype.shared = "on C.prototype";
const c1 = new C(); const c2 = new C();
line("c1.shared / c2.shared", c1.shared + " / " + c2.shared);
line("getPrototypeOf(c1) === getPrototypeOf(c2)", String(Object.getPrototypeOf(c1) === Object.getPrototypeOf(c2)));
line("getPrototypeOf(c1) === C.prototype", String(Object.getPrototypeOf(c1) === C.prototype));
line("getPrototypeOf(c1) === C", String(Object.getPrototypeOf(c1) === C));
c1.shared = "own on c1";
line("after c1.shared = 'own on c1' : c2.shared", c2.shared);
Object.setPrototypeOf(c1, { shared: "a different object entirely" });
line("setPrototypeOf(c1, {...}) : c1 instanceof C", String(c1 instanceof C));
line("  c1.shared (own still wins)", c1.shared + "   own? " + own.call(c1, "shared"));
delete c1.shared;
line("  after delete c1.shared", c1.shared);

console.log("");
console.log("[5] what JS does NOT have -- a per-property hook that beats an own property on READ");
const probe = { get v() { return "proto accessor"; }, set v(x) { this._x = x; } };
const leaf = Object.create(probe);
Object.defineProperty(leaf, "v", { value: "own", writable: true, enumerable: true, configurable: true });
line("proto has get+set, leaf has own data -> leaf.v", leaf.v);
line("is there any flag that flips this?", "no -- ordinary [[Get]] returns at the first own hit");
line("Proxy CAN do it, but that is a different object", (() => {
  const px = new Proxy(leaf, { get(t, k, r) { return k === "v" ? "PROXY wins" : Reflect.get(t, k, r); } });
  return px.v;
})());
```

- ★★★ `[1]` 에서 `defineProperty` 로 own 을 만든 뒤 **`kid.v`** 는 무엇인가?
  프로토타입의 접근자는 **없어졌는가 살아 있는가**?
- ★★★ `[2]` 에서 `kid2.v = 'written through'` 뒤의 **own 키 목록**과 **`kid2.v` 를 다시 읽은 값**을 적어 보라.
  ★★ 둘을 나란히 놓으면 무엇이 이상한가?
- ★★ `[3]` 이 `[2]` 의 **대조군**인 이유는? 두 블록에서 갈리는 조건은 **정확히 무엇 하나**인가?
- ★★★ `[4]` 에서 `getPrototypeOf(c1)` 은 `C.prototype` 과 같은가, `C` 와 같은가?
  그 차이가 말하는 것은?
- ★★★ `setPrototypeOf(c1, {...})` 뒤에 `c1 instanceof C` 는 무엇인가?
  그리고 `c1.shared` 는? `delete c1.shared` 뒤에는?
- ★★★ `[5]` 가 묻는 것은 「JS 에 **없는 것**」이다. 그것이 무엇인가?
  **`Proxy` 가 그 반례가 못 되는 이유**를 한 문장으로.

### 6. `prototype` 과 `[[Prototype]]` 과 `__proto__` (경계) ★★★

- ★★★ 셋을 **각각 한 문장으로** 정의해 보라. 무엇이 **함수만** 갖는 것이고, 무엇이 **모든 객체**가 갖는 것인가?
- ★★★ 셋 중 **체인이 없는 객체에 아예 없는 것**은 무엇인가?
- ★★ **인스턴스에 `.prototype` 이 있는가**? 그것이 왜 가장 빠른 판별인가?
- ★★ 13번이 다룬 **네 번째 얼굴**이 하나 더 있다 — 그것은 무엇이고 위의 셋과 어떻게 다른가?
- ★ 읽기와 쓰기에 각각 **무엇을 쓰라고** 이 문서는 말하는가?

### 7. 쓰기가 체인 쪽에 걸리는 세 경우 (왜) ★★★

- ★★★ 셋을 대면? 각각 **엄격 모드에서 무엇이 나오고** **own 이 생기는가**?
- ★★★ setter 가 가져갔을 때 그 안의 `this` 는 무엇인가? **어느 주제의 규칙**인가?
- ★★★ 그래서 값은 **어느 객체의 어느 이름**에 들어가는가?
- ★★ 그 셋을 **전부 통과하는 문**이 하나 있다. 무엇이고, 대입과 어떻게 다른가?
- ★ 비엄격에서는 어떻게 되는가? 그 실측은 **이 주제의 블록에 있는가**?

### 8. `new` 와 `instanceof` 는 각각 무엇을 보나 (왜) ★★★

- ★★★ `new Ctor()` 가 하는 **연결 한 줄**을 적어 보라. 그것을 손으로 쓰면 어떤 두 줄이 되는가?
- ★★★ `instanceof` 는 「이 생성자로 만들었나」를 묻는가? **아니라면 무엇을 묻는가**?
- ★★★ 그 답의 증거가 되는 **실측 한 줄**은 무엇인가?
- ★★ `Symbol.hasInstance` 를 달면 무엇이 달라지는가? 그것이 `instanceof` 의 성격에 대해 말하는 것은?
- ★ `isPrototypeOf` 는 같은 질문인가 다른 질문인가? **속일 수 있는 쪽**은 어느 쪽인가?

### 9. 「쓰기는 체인을 안 탄다」는 어디까지 맞나 (왜) ★★★ 이 주제의 결론

- ★★★ 그 요약이 **어디까지 맞고 어디서 틀리는가**? 정확한 한 문장으로 고쳐 써 보라.
- ★★★ 그 정밀화의 **근거가 되는 로그 한 줄**을 적어 보라. 그 로그의 **몇 번째 줄**이 결정적인가?
- ★★★ 거친 요약으로는 **설명할 수 없는 것**이 있다. 무엇인가?
- ★★ 「탐색은 걷는다」를 **로그 없이** 증명할 수 있는가? 왜 못 하는가?
- ★ 브라우저 탐침의 라벨 하나가 그 거친 요약을 쓰고 있다. 어느 줄이고, 왜 그대로 두었는가?

### 10. 보장인가 엔진 사정인가 (연결) ★★★

- 이 주제에서 **두 판이 갈린 블록은 몇 개**였는가?
- ★★★ **명세가 정하는 것**과 **V8 의 문구**를 각각 셋씩 대면?
- ★★ 브라우저에 같은 줄을 던졌을 때 **호스트가 정하는 칸은 몇 개**였는가?
  그런데 이 문서가 **호스트의 것**이라고 따로 적어 둔 표기가 하나 있다 — 무엇인가?
- ★★★ 이 주제에서 **부적용인 창**은 무엇인가? 그리고 「**창을 바꿔 물었다**」에 해당하는 자리는 어디인가?
- ★★★ 「`setPrototypeOf` 는 느리다」에 대해 이 문서는 무엇이라고 적는가?

### 11. 파이썬 29번과의 대비 (연결) ★★★

- ★★★ 파이썬은 **무엇**의 사슬을 타고 JS 는 **무엇**의 사슬을 타는가?
- ★★★ **읽기에서 누가 이기는가** — 파이썬과 JS 를 갈라서. 그 차이를 한 문장으로.
- ★★★ **쓰기에서는 어떤가**? 두 언어가 같은 자리는 어디인가?
- ★★ 파이썬에서 인스턴스 칸을 이기는 것의 **판별식**은 무엇인가? JS 에 **그에 해당하는 플래그가 있는가**?
- ★★ 못 찾았을 때 두 언어는 각각 무엇을 하는가?
- ★ 사슬을 **런타임에 갈아끼울 수 있는** 쪽은 어디인가? 그 증거는?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **`__proto__:` 리터럴 문법** · **무엇이 쓰기를 막나** · **`this` 판정** · **체인 순회 열거** ·
  **`class` 가 무엇을 어디에 붙이나** · **어느 타입 검사가 깨지나** · **`Proxy` 트랩 계약** 은 각각 어느 주제가 정본인가?
- ★★★ 13번이 본 `__proto__` 와 **이 주제가 본 `__proto__`** 는 어떻게 다른가?
- ★★ 14번이 본 「비쓰기 프로퍼티」와 **이 주제가 본 그것**은 어떻게 다른가?
- ★★ 07번에서 **그대로 받아 쓰는 것**은 무엇인가?
- ★ 이 주제가 **끝까지 책임지는 것** 셋을 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
