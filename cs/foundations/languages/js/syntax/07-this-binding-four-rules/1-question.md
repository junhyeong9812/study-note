# js/syntax/07 — `this` 바인딩 네 규칙: 「이 호출식에서 `this` 는 무엇인가」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **네 규칙과 그 우선순위** ② ★★★ **엄격 모드가 답을 바꾸는 칸이 몇 개인가** ③ **메서드를 떼면 왜 조용히 틀리나**.
> ★★★ **[06번](../06-scope-and-closures/2-summary.md)의 결론을 여기서 뒤집는다** — 이름은 정의된 자리가 정하지만 **`this` 는 호출식이 정한다.**
> ★ 예외가 딱 하나 있고 그것이 **화살표 함수**다(4번 문항).
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★★ **`this` 는 브랜드 태그로 답한다** — `[object Object]`·`[object global]`·`globalThis`·`undefined`.
> ★ **7번은 Node 로만 풀면 반쪽이다.** 브라우저에 같은 줄을 던져야 어느 칸이 언어인지 갈린다.
>
> **선행** — [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md) · [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「같은 함수인데 왜 답이 아홉 가지인가」까지 적어야** 답이다.
- ★★★ **2번은 「몇 칸이 갈렸나」를 먼저 세는 것이 답의 절반**이다.
- ★★ **3번은 「왜 에러가 안 나나」까지** 적어야 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 함수를 아홉 가지로 부르면 (예측) ★★★ 이 주제의 축

```js
// js06b-07a-four-rules.js
// this 는 함수에 붙어 있지 않다 -- 호출식의 모양이 정한다. 네 규칙을 한 함수로 확인한다.
// 브랜드 태그는 Object.prototype.toString.call 로 찍는다.
function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") {
    const brand = Object.prototype.toString.call(t);
    return brand + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}

// 이 한 함수를 네 가지 모양으로 부른다. 함수는 처음부터 끝까지 같은 객체다.
function who() { return tag(this); }

const holder = { mark: "holder", who };
const nested = { mark: "outer", inner: { mark: "inner", who } };
const arr = [who];
arr.mark = "array";

console.log("[1] 네 규칙 -- 같은 함수, 다른 호출식");
const calls = [
  ["default   who()", () => who()],
  ["implicit  holder.who()", () => holder.who()],
  ["implicit  nested.inner.who()", () => nested.inner.who()],
  ["implicit  obj['who']()", () => holder["who"]()],
  ["implicit  arr[0]()", () => arr[0]()],
  ["explicit  who.call(o)", () => who.call({ mark: "called" })],
  ["explicit  who.apply(o)", () => who.apply({ mark: "applied" })],
  ["explicit  who.bind(o)()", () => who.bind({ mark: "bound" })()],
  ["new       new who()", () => new who()],
];
for (const [label, run] of calls) console.log("  " + label.padEnd(30) + " -> " + run());

console.log("");
console.log("[2] 우선순위 -- 한 호출식에 규칙이 둘 이상 걸리면");
console.log("  " + "new beats bind".padEnd(30) + " -> " + tag(new (who.bind({ mark: "bound" }))()));
console.log("  " + "call beats implicit".padEnd(30) + " -> " + holder.who.call({ mark: "called" }));
console.log("  " + "bind beats implicit".padEnd(30) + " -> " + ({ mark: "host", w: who.bind({ mark: "bound" }) }).w());

console.log("");
console.log("[3] 점 왼쪽이 있어도 암시적 바인딩이 아닌 자리");
console.log("  " + "(holder.who)()".padEnd(30) + " -> " + (holder.who)());
console.log("  " + "(0, holder.who)()".padEnd(30) + " -> " + (0, holder.who)());
console.log("  " + "(holder.who = holder.who)()".padEnd(30) + " -> " + (holder.who = holder.who)());
console.log("  " + "(true && holder.who)()".padEnd(30) + " -> " + (true && holder.who)());
console.log("  " + "holder?.who()".padEnd(30) + " -> " + holder?.who());

console.log("");
console.log("[4] 원시값을 this 로 주면 -- 비엄격은 감싸고 엄격은 그대로 둔다");
function looseThis() { return tag(this); }
function strictThis() { "use strict"; return tag(this); }
for (const v of [7, "s", true, null, undefined]) {
  console.log("  this = " + String(v).padEnd(10) +
              " sloppy " + looseThis.call(v).padEnd(24) +
              " strict " + strictThis.call(v));
}
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 아홉 줄에서 **함수 객체는 몇 개**인가? 그러면 무엇이 답을 바꿨는가?
- ★★★ `[2]` 의 세 줄로 **우선순위를 한 줄**로 적으면?
- ★★★ `[3]` 의 다섯 줄 중 **암시적 바인딩이 살아남는 것은 몇 개**인가? 갈림의 기준은?
- ★★ `[4]` 에서 비엄격과 엄격이 갈리는 칸은 **몇 개**이고 각각 무엇인가?
- ★ `null` 과 `undefined` 를 `this` 로 주면 두 모드에서 각각 무엇이 되는가?

### 2. 같은 탐침을 두 모드로 컴파일하면 (예측) ★★★

```js
// js06b-07b-mode-matrix.js
// 엄격 모드가 this 의 답을 바꾸는 칸이 몇 개인가 -- 세어서 고정 행으로 둔다.
// 같은 탐침 소스를 두 번 컴파일한다: 그대로(비엄격)와 "use strict"; 를 앞에 붙여(엄격).
// new Function 을 쓰는 이유 -- 파일로 던지면 진단에 절대 경로가 박힌다. 여기서는 값만 받는다.
const HELPERS = `
  function tag(t) {
    if (t === undefined) return "undefined";
    if (t === null) return "null";
    if (t === globalThis) return "globalThis";
    if (typeof t === "object" || typeof t === "function") return Object.prototype.toString.call(t);
    return typeof t + " " + String(t);
  }
`;

function run(src, strict) {
  // ★ @@ 는 모드마다 다른 이름으로 바꾼다.
  //   한 이름을 두 모드가 나눠 쓰면 앞 모드가 만든 전역 때문에 뒤 모드의 답이 바뀐다(실제로 그랬다).
  src = src.replace(/@@/g, "undeclared_" + (strict ? "strict" : "sloppy"));
  const body = (strict ? '"use strict";\n' : "") + HELPERS + "\nreturn (" + src + ");";
  try { return String(new Function(body)()); }
  catch (e) { return e.constructor.name + ": " + e.message; }
}

const probes = [
  ["plain call", "(function () { return tag(this); })()"],
  ["callback of forEach", "(function () { var r; [1].forEach(function () { r = tag(this); }); return r; })()"],
  ["this from call(7)", "(function () { return tag(this); }).call(7)"],
  ["this from call(null)", "(function () { return tag(this); }).call(null)"],
  ["this from call(undefined)", "(function () { return tag(this); }).call(undefined)"],
  ["detached method (guarded)", "(function () { var o = { n: 'obj', m: function () { return String(this && this.n); } }; var d = o.m; return d(); })()"],
  ["detached method (unguarded)", "(function () { var o = { n: 'obj', m: function () { return String(this.n); } }; var d = o.m; return d(); })()"],
  ["method kept on the object", "(function () { var o = { n: 'obj', m: function () { return String(this.n); } }; return o.m(); })()"],
  ["arrow at top of the fn", "(function () { return (() => tag(this))(); })()"],
  ["arrow called with call(7)", "(function () { var a = () => tag(this); return a.call(7); })()"],
  ["this inside new", "(function () { function C() { this.x = 1; } return JSON.stringify(new C()); })()"],
  ["assigning to an undeclared name", "(function () { @@ = 1; return 'assigned ' + String(globalThis['@@']); })()"],
  ["this in a getter", "(function () { var o = { n: 'g', get v() { return String(this.n); } }; return o.v; })()"],
  ["setTimeout-like: fn passed along", "(function () { function pass(f) { return f(); } var o = { n: 'obj', m: function () { return String(this && this.n); } }; return pass(o.m); })()"],
];

let differ = 0;
console.log("  " + "probe".padEnd(34) + "sloppy".padEnd(26) + "strict");
console.log("  " + "-".repeat(34) + "-".repeat(26) + "-".repeat(26));
for (const [label, src] of probes) {
  const a = run(src, false), b = run(src, true);
  if (a !== b) differ += 1;
  console.log("  " + label.padEnd(34) + a.padEnd(26) + b + (a === b ? "" : "   <- differs"));
}
console.log("");
console.log("  probes " + probes.length + " · same " + (probes.length - differ) + " · DIFFER " + differ);
```

- 열네 줄의 두 칸을 각각 적으면?
- ★★★ **갈린 칸은 몇 개**인가? 안 갈린 다섯은 무엇이고 **왜 안 갈리는가**?
- ★★★ 「떼어 낸 메서드」 두 줄 중 **방어를 넣은 쪽**은 두 모드가 같은 글자다 — **이유도 같은가**?
- ★★ 화살표 두 줄이 갈리는 것이 「화살표에 `this` 가 없다」를 어떻게 반박하는가?
- ★★ 탐침의 이름을 **모드마다 다르게** 만든 이유는? 같게 두면 무엇이 잘못되는가?
- ★ 이 격자를 `new Function` 으로 만든 이유는?

### 3. 점 하나가 사라지면 (예측) ★★★

```js
// js06b-07c-detached.js
// 메서드를 떼어 내면 this 를 잃는다 -- 그리고 그 실패가 조용하다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(36) + " -> " + r);
}

const user = {
  name: "kim",
  greet() { return "hi " + this.name; },
};

console.log("[1] 같은 함수인데 점이 있고 없고로 갈린다");
probe("user.greet()", () => user.greet());
probe("const g = user.greet; g()", () => { const g = user.greet; return g(); });
probe("same function object?", () => { const g = user.greet; return g === user.greet; });

console.log("");
console.log("[2] 떼어 내는 모양이 여럿이다 -- 전부 같은 사고다");
probe("passed to another function", () => { const call = (f) => f(); return call(user.greet); });
probe("stored in an array", () => { const a = [user.greet]; return a[0](); });
probe("assigned to another object", () => { const other = { name: "lee" }; other.greet = user.greet; return other.greet(); });
probe("used as a callback of map", () => [1].map(user.greet)[0]);
probe("destructured out", () => { const { greet } = user; return greet(); });

console.log("");
console.log("[3] 왜 조용한가 -- this 가 무엇이 되어 있나");
function where() { return Object.prototype.toString.call(this) + " name=" + JSON.stringify(this && this.name); }
const holder2 = { name: "kim", where };
probe("holder2.where()", () => holder2.where());
probe("detached where()", () => { const w = holder2.where; return w(); });
probe("globalThis.name in this host", () => globalThis.name);

console.log("");
console.log("[4] 엄격 모드에서는 조용하지 않다");
const strictUser = {
  name: "kim",
  greet() { "use strict"; return "hi " + this.name; },
};
probe("strict method, attached", () => strictUser.greet());
probe("strict method, detached", () => { const g = strictUser.greet; return g(); });

console.log("");
console.log("[5] 고치는 세 가지 -- 무엇을 옮기는지가 다르다");
probe("bind at handoff", () => { const g = user.greet.bind(user); return g(); });
probe("wrap in an arrow", () => { const g = () => user.greet(); return g(); });
probe("bind in the constructor-ish factory", () => {
  function make(name) { const self = { name }; self.greet = user.greet.bind(self); return self; }
  const m = make("park");
  const g = m.greet;
  return g();
});
probe("arrow as the method itself", () => {
  const bad = { name: "kim", greet: () => "hi " + String(this && this.name) };
  return bad.greet();
});
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 세 번째 줄이 `true` 다 — 그러면 **무엇이 달라진 것**인가?
- ★★★ `[2]` 의 다섯 줄 중 **하나만 답이 다르다** — 어느 것이고 왜인가?
- ★★★ `[3]` 을 근거로 「**왜 에러가 안 나나**」를 설명하면? 브라우저에서는 무엇이 달라지는가?
- ★★ `[4]` 에서 같은 코드가 무엇으로 바뀌는가?
- ★ `[5]` 의 마지막 줄은 고침이 아니다 — 왜인가?

### 4. 화살표를 넣으면 무엇이 달라지나 (예측) ★★★

```js
// js06b-07d-arrow.js
// 화살표 함수는 this 를 만들지 않는다 -- 그래서 06번의 스코프 규칙이 this 에도 그대로 적용된다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(38) + " -> " + r);
}
function brand(t) {
  if (t === undefined) return "undefined";
  if (t === globalThis) return "globalThis";
  return Object.prototype.toString.call(t) + (t && t.mark ? " mark=" + t.mark : "");
}

console.log("[1] 화살표는 바깥에서 this 를 가져온다 -- 이름을 찾듯이");
const obj = {
  mark: "obj",
  withFunction() { const inner = function () { return brand(this); }; return inner(); },
  withArrow() { const inner = () => brand(this); return inner(); },
  deepArrow() { const a = () => () => () => brand(this); return a()()(); },
};
probe("method + inner function()", () => obj.withFunction());
probe("method + inner arrow", () => obj.withArrow());
probe("three arrows deep", () => obj.deepArrow());

console.log("");
console.log("[2] 화살표는 call/apply/bind 로도 안 바뀐다");
const fnAt = { mark: "host2", f() { const a = () => brand(this); return [a(), a.call({ mark: "forced" }), a.apply({ mark: "forced" }), a.bind({ mark: "forced" })()]; } };
probe("arrow: plain / call / apply / bind", () => fnAt.f());
const normal = { mark: "host3", f() { const n = function () { return brand(this); }; return [n(), n.call({ mark: "forced" })]; } };
probe("function(): plain / call", () => normal.f());

console.log("");
console.log("[3] 화살표를 메서드로 쓰면 깨진다");
const broken = { mark: "broken", who: () => brand(this) };
const fine = { mark: "fine", who() { return brand(this); } };
probe("arrow as a method", () => broken.who());
probe("shorthand method", () => fine.who());
probe("what the arrow actually saw", () => brand(this));

console.log("");
console.log("[4] 그런데 콜백으로는 화살표가 맞는 도구다");
const timer = {
  mark: "timer",
  ticks: 0,
  runFunction() { const out = []; [1, 2].forEach(function () { out.push(brand(this)); }); return out; },
  runArrow() { const out = []; [1, 2].forEach(() => out.push(brand(this))); return out; },
};
probe("forEach + function()", () => timer.runFunction());
probe("forEach + arrow", () => timer.runArrow());

console.log("");
console.log("[5] 화살표에 없는 것이 this 만은 아니다");
probe("new on an arrow", () => { const A = () => {}; return new A(); });
probe("arrow has a prototype property?", () => Object.prototype.hasOwnProperty.call(() => {}, "prototype"));
probe("function has one?", () => Object.prototype.hasOwnProperty.call(function () {}, "prototype"));
probe("class field arrow keeps this", () => {
  class C { mark = "C"; who = () => brand(this); }
  const c = new C();
  const detached = c.who;
  return [c.who(), detached()];
});
probe("class method loses this", () => {
  class C { constructor() { this.mark = "C"; } who() { return brand(this); } }
  const c = new C();
  const detached = c.who;
  return [c.who(), detached()];
});
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[2]` 에서 네 시도가 전부 같은 답이다 — **무엇을 못 바꾸는 것**인가? 왜 못 바꾸는가?
- ★★★ `[3]` 의 세 줄에서 화살표 메서드가 본 것은 **무엇**인가? 그것이 객체 리터럴인가?
- ★★ `[4]` 와 `[3]` 이 정반대 결론이다 — 두 자리를 가르는 한 문장은?
- ★★ `[5]` 의 마지막 두 줄이 갈리는 이유는? 어느 쪽이 「떼어 내도 안 깨지는」 쪽인가?
- ★ 화살표에 없는 것을 `this` 말고 **둘 더** 대면?

### 5. `bind` 를 두 번 걸면 (예측) ★★

```js
// js06b-07e-bind.js
// bind 가 만드는 것은 새 함수다 -- 그래서 두 번 감싸도 안쪽이 이긴다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(38) + " -> " + r);
}
function who() { return this && this.mark; }

console.log("[1] 두 번 bind 해도 안쪽이 이긴다");
probe("bind(A)()", () => who.bind({ mark: "A" })());
probe("bind(A).bind(B)()", () => who.bind({ mark: "A" }).bind({ mark: "B" })());
probe("bind(A).call(B)", () => who.bind({ mark: "A" }).call({ mark: "B" }));
probe("bind(A).apply(B)", () => who.bind({ mark: "A" }).apply({ mark: "B" }));
probe("attached as a method of B", () => { const o = { mark: "B" }; o.w = who.bind({ mark: "A" }); return o.w(); });

console.log("");
console.log("[2] bind 는 새 함수다 -- 원본은 그대로다");
probe("bound === original", () => who.bind({}) === who);
probe("two binds of the same fn are equal?", () => who.bind({}) === who.bind({}));
probe("original still floats", () => who());

console.log("");
console.log("[3] 인자도 앞에서부터 박힌다 -- 그것도 되돌릴 수 없다");
function add(a, b, c) { return [a, b, c]; }
probe("add.bind(null, 1)(2, 3)", () => add.bind(null, 1)(2, 3));
probe("add.bind(null, 1).bind(null, 9)(3)", () => add.bind(null, 1).bind(null, 9)(3));
probe("add.bind(null, 1, 2, 3)(9, 9)", () => add.bind(null, 1, 2, 3)(9, 9));

console.log("");
console.log("[4] 바인딩된 함수의 이름과 length");
function named(a, b, c) {}
probe("name / length of the original", () => [named.name, named.length]);
probe("name / length after bind(null)", () => { const b = named.bind(null); return [b.name, b.length]; });
probe("name / length after bind(null, 1)", () => { const b = named.bind(null, 1); return [b.name, b.length]; });
probe("name after two binds", () => named.bind(null).bind(null).name);
probe("bound fn has a prototype property?", () => Object.prototype.hasOwnProperty.call(named.bind(null), "prototype"));

console.log("");
console.log("[5] new 는 bind 를 이긴다 -- 이 한 자리만 예외다");
function C(x) { this.x = x; }
const Bound = C.bind({ mark: "ignored" }, 7);
probe("new Bound()", () => new Bound());
probe("prototype chain still points at C", () => Object.getPrototypeOf(new Bound()) === C.prototype);
probe("instanceof C", () => new Bound() instanceof C);
probe("Bound() without new (sloppy)", () => { Bound(); return "no throw"; });
probe("new on a bound arrow", () => { const A = (() => {}).bind(null); return new A(); });
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 다섯 줄이 전부 같다 — 「덮어쓴다」와 「한 겹 더 감싼다」 중 어느 그림이 맞는가?
- ★★ `[3]` 의 두 번째 줄이 `[1,9,3]` 이다 — 인자는 **어디부터** 박히는가?
- ★★ `[4]` 에서 이름과 `length` 에 무엇이 남는가? `prototype` 은?
- ★★★ `[5]` 가 이 주제의 **유일한 예외**다 — 무엇이 무엇을 이기는가? 프로토타입은 누구 것인가?
- ★ 바인딩된 화살표에 `new` 를 걸면?

### 6. `new` 를 붙이거나 빼면 (예측) ★★

```js
// js06b-07f-new.js
// new 는 네 단계를 한다 -- 각 단계를 따로 관찰한다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(40) + " -> " + r);
}

function Point(x, y) {
  this.x = x;
  this.y = y;
}
Point.prototype.label = "from prototype";

console.log("[1] 단계를 하나씩 관찰한다");
probe("(1) this is a brand new object", () => {
  let seen;
  function C() { seen = [Object.keys(this).length, this === globalThis]; }
  new C();
  return seen;
});
probe("(2) its prototype is C.prototype", () => Object.getPrototypeOf(new Point(1, 2)) === Point.prototype);
probe("(2) so it inherits", () => new Point(1, 2).label);
probe("(3) the body runs with it as this", () => new Point(1, 2));
probe("(4) it comes back with no return stmt", () => typeof new Point(1, 2));

console.log("");
console.log("[2] 4단계의 예외 -- 객체를 돌려주면 그것이 이긴다");
probe("return an object", () => { function C() { this.x = 1; return { x: "returned" }; } return new C(); });
probe("return a primitive", () => { function C() { this.x = 1; return 42; } return new C(); });
probe("return an array", () => { function C() { this.x = 1; return [9]; } return new C(); });
probe("return a function", () => { function C() { this.x = 1; return function f() {}; } return typeof new C(); });
probe("return null", () => { function C() { this.x = 1; return null; } return new C(); });

console.log("");
console.log("[3] new 없이 부르면 -- 조용히 전역을 더럽힌다");
probe("Point(1, 2) with no new (sloppy)", () => { const r = Point(1, 2); return [r, globalThis.x, globalThis.y]; });
probe("the same in strict mode", () => {
  function SP(x) { "use strict"; this.x = x; }
  return SP(1);
});

console.log("");
console.log("[4] new.target 이 그 둘을 가른다");
function Guarded(x) {
  if (new.target === undefined) return "called without new";
  this.x = x;
  return undefined;
}
probe("new Guarded(1)", () => new Guarded(1));
probe("Guarded(1)", () => Guarded(1));
probe("new.target is the function itself", () => {
  let seen;
  function C() { seen = new.target === C; }
  new C();
  return seen;
});

console.log("");
console.log("[5] new 를 못 받는 것들");
probe("new on an arrow", () => { const A = () => {}; return new A(); });
probe("new on a shorthand method", () => { const o = { m() {} }; return new o.m(); });
probe("new on a getter-made function", () => { const o = { get g() { return () => {}; } }; return new o.g(); });
probe("class called without new", () => { class K {} return K(); });
probe("new on a class", () => { class K { constructor() { this.k = 1; } } return new K(); });
probe("new on Math.max", () => new Math.max(1));
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 네 줄을 **`new` 의 네 단계**에 각각 짝지으면?
- ★★★ `[2]` 의 다섯 줄에서 **돌려준 것이 이기는 경우와 무시되는 경우**를 가르는 기준은?
- ★★ `[3]` 의 첫 줄이 `[null,1,2]` 다 — 세 값이 각각 무엇을 뜻하는가?
- ★★ `[4]` 의 `new.target` 이 두 경우에 각각 무엇인가?
- ★ `[5]` 에서 `new` 를 받는 것은 **몇 개**이고 어느 것인가?

### 7. 누가 부르느냐 — 콜백과 타이머 (경계) ★★★

```js
// js06b-07g-callbacks.js
// 콜백에 넘기는 순간 this 가 바뀐다 -- 누가 부르느냐가 정하기 때문이다.
function brand(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "") +
           (t.constructor && t.constructor.name ? " ctor=" + t.constructor.name : "");
  }
  return typeof t + " " + String(t);
}
function line(label, v) { console.log("  " + label.padEnd(38) + " -> " + v); }

console.log("[1] 배열 메서드는 두 번째 인자로 this 를 받는다");
[1].forEach(function () { line("forEach, no thisArg", brand(this)); });
[1].forEach(function () { line("forEach, thisArg given", brand(this)); }, { mark: "given" });
line("map, thisArg given", [1].map(function () { return brand(this); }, { mark: "given" })[0]);
line("filter, thisArg given", String([1].filter(function () { return brand(this) && true; }, { mark: "given" }).length));
line("some/every take one too", String([1].some(function () { return this.mark === "given"; }, { mark: "given" })));
line("reduce does NOT take one", String((function () {
  try { return [1, 2].reduce(function () { return brand(this); }, 0, { mark: "given" }); }
  catch (e) { return e.constructor.name; }
})()));
line("sort comparator saw", (function () { let seen; [2, 1].sort(function () { seen = brand(this); return 0; }); return seen; })());

console.log("");
console.log("[2] 화살표를 주면 thisArg 가 무시된다");
[1].forEach(() => line("forEach + arrow, thisArg given", brand(this)), { mark: "given" });

console.log("");
console.log("[3] 메서드를 그대로 넘기면 떨어진다 -- 그리고 고치는 법 셋");
const counter = {
  mark: "counter",
  n: 0,
  bump() { this.n += 1; return this.n; },
};
function report(label, run) {
  let r;
  try { r = JSON.stringify(run()); } catch (e) { r = e.constructor.name + ": " + e.message; }
  line(label, r);
}
report("[1,2].forEach(counter.bump)", () => { const c = { mark: "c", n: 0, bump: counter.bump }; [1, 2].forEach(c.bump); return c.n; });
report("thisArg", () => { const c = { mark: "c", n: 0, bump: counter.bump }; [1, 2].forEach(c.bump, c); return c.n; });
report("bind", () => { const c = { mark: "c", n: 0, bump: counter.bump }; [1, 2].forEach(c.bump.bind(c)); return c.n; });
report("arrow wrapper", () => { const c = { mark: "c", n: 0, bump: counter.bump }; [1, 2].forEach(() => c.bump()); return c.n; });

console.log("");
console.log("[4] 타이머는 호스트가 정한다 -- 그래서 여기 값은 Node 의 것이다");
const t  = { mark: "t", m() { line("setTimeout(t.m) this", brand(this)); } };
const tb = { mark: "tb", m() { line("setTimeout(t.m.bind(t)) this", brand(this)); } };
setTimeout(function () {
  line("setTimeout(function(){}) this", brand(this));
  setTimeout(t.m, 0);
  setTimeout(tb.m.bind(tb), 0);
  setTimeout(() => line("setTimeout(arrow inside cb) this", brand(this)), 0);
}, 0);
```

그리고 같은 질문을 브라우저에 던진다 — 호스트 페이지는 네 줄이다.

```text
<!doctype html><meta charset="utf-8"><title>this in a browser</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js06b-07h-browser.js"></script>
```

```js
// js06b-07h-browser.js
// 같은 질문을 브라우저에 던진다 -- 호스트가 정하는 칸이 어디인지 가리려는 것이다.
function brand(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis (window)";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}
function loose() { return brand(this); }
function tight() { "use strict"; return brand(this); }

const user = { name: "kim", greet() { return "hi " + this.name; } };
const detached = user.greet;
const arrowMethod = { name: "kim", greet: () => "hi " + String(this && this.name) };

const rows = [
  ["top-level this in a classic script", brand(this)],
  ["sloppy f()", loose()],
  ["strict f()", tight()],
  ["sloppy f.call(7)", loose.call(7)],
  ["strict f.call(7)", tight.call(7)],
  ["user.greet()", user.greet()],
  ["detached greet() -- the silent one", detached()],
  ["window.name is", JSON.stringify(window.name)],
  ["arrow used as a method", arrowMethod.greet()],
  ["brand of globalThis", Object.prototype.toString.call(globalThis)],
  ["top-level arrow: arguments?", (() => { try { return String(arguments.length); } catch (e) { return e.constructor.name + ": " + e.message; } })()],
  ["forEach with no thisArg (sloppy)", (() => { let r; [1].forEach(function () { r = brand(this); }); return r; })()],
];

setTimeout(function () {
  rows.push(["setTimeout(fn) this", brand(this)]);
  rows.push(["addEventListener this", "see below"]);
  const btn = document.createElement("button");
  btn.id = "b1";
  btn.addEventListener("click", function () {
    rows[rows.length - 1] = ["addEventListener this", brand(this) + " id=" + this.id];
    document.getElementById("out").textContent =
      rows.map(([k, v]) => k.padEnd(38) + " : " + v).join("\n");
  });
  document.body.appendChild(btn);
  btn.click();
}, 0);
```

- 두 블록의 출력을 각각 적으면?
- ★★★ 두 호스트에서 **갈린 칸이 몇 개**이고 각각 무엇인가?
- ★★★ 「떼어 낸 메서드」의 결과가 두 호스트에서 다르다 — **어느 쪽이 더 조용한가**? 왜인가?
- ★★ `thisArg` 를 **안 받는** 배열 메서드는 무엇인가? 화살표를 주면?
- ★★ Node 의 `setTimeout` 콜백 `this` 는 무엇인가? 그것은 어느 층의 사실인가?
- ★ `addEventListener` 의 `this` 는 무엇이 정하는가?

### 8. 왜 `this` 만 다른 규칙인가 (왜) ★★★

- ★★★ 06번의 이름 규칙과 이 주제의 규칙을 **한 문장씩**으로 대비하면?
- ★★★ 화살표 함수가 **어느 쪽 규칙을 따르는가**? 그것이 왜 헷갈림의 원인인가?
- ★★ 「함수만 읽어서는 `this` 를 못 정한다」가 실무에서 무슨 뜻인가?
- ★★ 파이썬은 `self` 를 **매개변수로 적는다** — 그 차이가 「떼어 내면 잃는다」에 어떻게 작용하는가?
- ★ 이 주제를 한 질문으로 줄이면 무엇을 묻게 되는가?

### 9. 보장인가 호스트인가 사정인가 (연결) ★★★ 이 갈래의 축

- ★★★ 이 주제에서 **명세 보장** 칸에 들어가는 것 다섯을 대면?
- ★★★ **호스트가 정하는** 칸 넷을 대면? 그중 **조용함의 모양을 바꾸는 것**은?
- ★★ 「엄격 모드에서 기본 `this` 가 `undefined`」는 어느 칸인가?
- ★★ 「`setTimeout` 의 `this` 가 `Timeout` 객체」는 어느 칸인가?
- ★ 이 주제에서 **부적용인 창**은 무엇인가?

### 10. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **`call`/`apply`/`bind` 의 API** · **엄격 모드** · **클래스 필드** · **이벤트 루프** 는 각각 어느 주제가 정본인가?
- ★★★ 06번에서 **무엇을 이어받고 무엇을 뒤집는가**? 한 문장씩.
- ★★ 08번이 이 주제에서 **무엇을 이어받는가**?
- ★ 모듈(ESM)의 최상위 `this` 를 여기서 안 다룬 이유는?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
