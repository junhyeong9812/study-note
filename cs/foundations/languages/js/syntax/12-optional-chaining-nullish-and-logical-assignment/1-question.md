# js/syntax/12 — 옵셔널 체이닝·널 병합·논리 할당: 「안 부르는 것」이 전부다 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `?.`·`??`·`??=` 는 **무엇을 만드는 문법이 아니라 무엇을 안 하는 문법**이라서
> **값으로는 안 갈린다.** 호출 횟수를 세야 보이고, 결정적인 숫자는 **0** 이다.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **사슬이 어디까지 끊기나** ② ★★★ **`??` 와 `||` 가 어느 값에서 갈리나** ③ **대입이 정말 일어났나**.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★★★ **이 주제에는 두 판이 갈린 줄이 하나도 없다.** 그래서 「판이 갈렸나」를 묻는 문항이 없다 — 대신 **모드가 갈린 칸**을 묻는다.
> ★ **3번은 「무엇이 나오나」가 아니라 「무엇을 불렀나」를 묻는다.** 로그를 먼저 적어라.
>
> **선행** — [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) · [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번과 3번은 「값」이 아니라 「호출 횟수」를 적어야** 답이다. 값만 적으면 절반도 못 맞힌 것이다.
- ★★★ **2번은 갈린 칸이 몇 개인지를 숫자로** 적어야 답이다.
- ★★ **4번은 「어느 줄이 모드에 달렸나」와 「무엇이 전역에 샜나」 둘을** 대야 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 사슬이 끊겼을 때 무엇이 안 불리나 (예측) ★★★ 이 주제의 축

```js
// js12b-12a-shortcircuit.js
// 단축 평가를 「안 불린 것」으로 증명한다 -- 값이 아니라 호출 횟수로.
// 격자의 라벨은 전부 ASCII 다(폭이 안 맞으면 표가 깨진다).
// 예외는 try/catch 로 받아 e.constructor.name + e.message 만 찍는다.
const row = (a, b, c) => console.log(String(a).padEnd(34) + String(b).padEnd(12) + c);

function probe() {
  let n = 0;
  return { calls: () => n, f: (v) => { n += 1; return v; } };
}

console.log("[1] argument of ?.[] and ?.() is never evaluated when the chain is cut");
row("expression", "result", "probe calls");
{
  const p = probe(); const o = { a: null };
  const r = o.a?.[p.f("k")];
  row("o.a?.[f('k')]        a=null", String(r), p.calls());
}
{
  const p = probe(); const o = { a: { k: "hit" } };
  row("o.a?.[f('k')]        a=obj", String(o.a?.[p.f("k")]), p.calls());
}
{
  const p = probe(); const o = {};
  row("o.fn?.(f(1))         no fn", String(o.fn?.(p.f(1))), p.calls());
}
{
  const p = probe(); const o = { fn: (x) => "got" + x };
  row("o.fn?.(f(1))         has fn", String(o.fn?.(p.f(1))), p.calls());
}

console.log("");
console.log("[2] was the right-hand side called?  ??  vs  ||  vs  &&");
row("expression", "result", "rhs calls");
for (const [label, left] of [["0", 0], ["null", null], ["undefined", undefined], ["'x'", "x"]]) {
  const p1 = probe(); const r1 = left ?? p1.f("R");
  row(("left=" + label).padEnd(18) + "left ?? f('R')", String(r1), p1.calls());
  const p2 = probe(); const r2 = left || p2.f("R");
  row(("left=" + label).padEnd(18) + "left || f('R')", String(r2), p2.calls());
  const p3 = probe(); const r3 = left && p3.f("R");
  row(("left=" + label).padEnd(18) + "left && f('R')", String(r3), p3.calls());
}

console.log("");
console.log("[3] a?.b.c short-circuits the WHOLE chain; parentheses end it");
const show = (tag, fn) => {
  try { console.log(tag.padEnd(26) + "-> " + String(fn())); }
  catch (e) { console.log(tag.padEnd(26) + "-> " + e.constructor.name + " " + e.message); }
};
const nil = { a: null };
show("nil.a?.b.c", () => nil.a?.b.c);
show("nil.a?.b.c.d.e", () => nil.a?.b.c.d.e);
show("(nil.a?.b).c", () => (nil.a?.b).c);
show("nil.a.b.c", () => nil.a.b.c);
show("nil.a?.b?.c", () => nil.a?.b?.c);
{
  const p = probe(); const deep = { a: null };
  const r = deep.a?.b[p.f("c")].d;
  console.log("deep.a?.b[f('c')].d".padEnd(26) + "-> " + String(r) + "   probe calls " + p.calls());
}

console.log("");
console.log("[4] ?. stops at null and undefined ONLY");
row("value", "v?.ctor", "v?.nope");
for (const [label, v] of [["0", 0], ["-0", -0], ["''", ""], ["NaN", NaN], ["false", false],
                          ["0n", 0n], ["null", null], ["undefined", undefined]]) {
  row(label, String(v?.constructor?.name), String(v?.nope));
}

console.log("");
console.log("[5] delete a?.b");
const del = { a: null };
show("delete del.a?.b", () => delete del.a?.b);
const del2 = { a: { b: 1 } };
show("delete del2.a?.b", () => delete del2.a?.b);
console.log("keys of del2.a after delete -> " + JSON.stringify(Object.keys(del2.a)));
```

- `[1]` 네 줄의 **탐침 호출 횟수**를 각각 적어 보라.
- ★★★ `[3]` 의 여섯 줄 중 **예외가 나는 것은 몇 줄**이고 어느 줄인가?
- ★★ `deep.a?.b[f('c')].d` 에서 **탐침은 몇 번 불리는가**?
- ★ `[4]` 에서 `?.` 가 **막는 값**과 **통과시키는 값**을 갈라 보라.
- ★ `[5]` 의 두 `delete` 는 각각 무엇을 돌려주는가?

### 2. 같은 값을 두 연산자에 던지면 (예측) ★★★

```js
// js12b-12b-grid.js
// ?? 대 || 전수 격자 -- 어느 칸에서 갈리나. 라벨은 전부 ASCII.
// 값 자체를 찍으면 -0 과 0 이, "" 와 0 이 구분되지 않으므로 라벨을 따로 들고 다닌다.
const D = "DEF";
const cases = [
  ["0", 0], ["-0", -0], ["''", ""], ["NaN", NaN], ["false", false],
  ["0n", 0n], ["null", null], ["undefined", undefined],
  ["'0'", "0"], ["[]", []], ["{}", {}], ["' '", " "], ["1", 1],
];
const tag = (v) => {
  if (v === null) return "null";
  if (v === undefined) return "undefined";
  if (typeof v === "number" && Object.is(v, -0)) return "-0";
  if (typeof v === "string") return "'" + v + "'";
  if (typeof v === "bigint") return String(v) + "n";
  if (Array.isArray(v)) return "[]";
  if (typeof v === "object") return "{}";
  return String(v);
};

console.log("[1] v ?? DEF   vs   v || DEF   vs   v && DEF");
console.log("value".padEnd(12) + "truthy".padEnd(9) + "nullish".padEnd(9) +
            "v ?? DEF".padEnd(12) + "v || DEF".padEnd(12) + "v && DEF".padEnd(12) + "?? vs ||");
let split = 0;
for (const [label, v] of cases) {
  const a = v ?? D, b = v || D, c = v && D;
  const same = Object.is(a, b);
  if (!same) split += 1;
  console.log(label.padEnd(12) + String(Boolean(v)).padEnd(9) +
    String(v === null || v === undefined).padEnd(9) +
    tag(a).padEnd(12) + tag(b).padEnd(12) + tag(c).padEnd(12) + (same ? "same" : "SPLIT"));
}
console.log("");
console.log("split cells " + split + " / " + cases.length);

console.log("");
console.log("[2] the same grid written as a default-value idiom");
const port = (v) => v ?? 8080;
const portOr = (v) => v || 8080;
console.log("input".padEnd(12) + "v ?? 8080".padEnd(12) + "v || 8080");
for (const [label, v] of [["0", 0], ["''", ""], ["false", false], ["null", null], ["undefined", undefined], ["3000", 3000]]) {
  console.log(label.padEnd(12) + tag(port(v)).padEnd(12) + tag(portOr(v)));
}

console.log("");
console.log("[3] ?? is NOT the same as an isNullish() call: it also short-circuits");
let n = 0;
const expensive = () => { n += 1; return 8080; };
n = 0; const r1 = 0 ?? expensive();
console.log("0 ?? expensive()      -> " + r1 + "   calls " + n);
n = 0; const r2 = 0 || expensive();
console.log("0 || expensive()      -> " + r2 + "   calls " + n);
n = 0; const r3 = (0 === null || 0 === undefined) ? expensive() : 0;
console.log("ternary on isNullish  -> " + r3 + "   calls " + n);
```

- ★★★ `[1]` 에서 **`SPLIT` 이 찍히는 줄은 몇 개**인가? 그 줄들의 공통점은?
- ★★ `null`·`undefined` 줄은 왜 `SPLIT` 이 아닌가?
- ★ `[3]` 의 세 줄에서 **`calls` 값**을 각각 적어 보라.

### 3. 로그가 둘로 갈리는 자리 (예측) ★★★

```js
// js12b-12c-assign.js
// ||= 와 = x || y 의 차이는 값이 아니라 「setter 가 불렸나」에 있다.
// setter 와 오른쪽 식에 각각 로그를 심어 호출 횟수로 가른다.
function box(init) {
  const log = [];
  let v = init;
  const o = {
    get x() { log.push("get"); return v; },
    set x(n) { log.push("set:" + String(n)); v = n; },
  };
  return { o, log, read: () => v };
}
function rhs(val) {
  let n = 0;
  return { calls: () => n, v: () => { n += 1; return val; } };
}
const tag = (v) => (typeof v === "string" ? "'" + v + "'" : String(v));

console.log("[1] b.x ||= R   vs   b.x = b.x || R      (same value, different writes)");
console.log("start".padEnd(10) + "form".padEnd(22) + "final".padEnd(10) +
            "rhs calls".padEnd(11) + "setter log");
for (const [label, init] of [["'keep'", "keep"], ["0", 0], ["''", ""], ["null", null]]) {
  {
    const b = box(init); const r = rhs("R");
    b.o.x ||= r.v();
    console.log(label.padEnd(10) + "b.x ||= R".padEnd(22) + tag(b.read()).padEnd(10) +
      String(r.calls()).padEnd(11) + JSON.stringify(b.log));
  }
  {
    const b = box(init); const r = rhs("R");
    b.o.x = b.o.x || r.v();
    console.log(label.padEnd(10) + "b.x = b.x || R".padEnd(22) + tag(b.read()).padEnd(10) +
      String(r.calls()).padEnd(11) + JSON.stringify(b.log));
  }
}

console.log("");
console.log("[2] ??=  vs  ||=  vs  &&=      (setter log is the answer)");
console.log("start".padEnd(10) + "form".padEnd(12) + "final".padEnd(10) +
            "rhs calls".padEnd(11) + "setter log");
for (const [label, init] of [["0", 0], ["''", ""], ["null", null], ["undefined", undefined], ["'v'", "v"]]) {
  for (const form of ["??=", "||=", "&&="]) {
    const b = box(init); const r = rhs("R");
    if (form === "??=") b.o.x ??= r.v();
    else if (form === "||=") b.o.x ||= r.v();
    else b.o.x &&= r.v();
    console.log(label.padEnd(10) + ("b.x " + form + " R").padEnd(12) + tag(b.read()).padEnd(10) +
      String(r.calls()).padEnd(11) + JSON.stringify(b.log));
  }
}

console.log("");
console.log("[3] on a frozen object: ||= only fails when it actually tries to write (sloppy mode)");
console.log("case".padEnd(34) + "result");
const shot = (label, obj, key, fn) => {
  try { fn(); console.log(label.padEnd(34) + "no throw, value=" + tag(obj[key])); }
  catch (e) { console.log(label.padEnd(34) + e.constructor.name + " " + e.message); }
};
const fz1 = Object.freeze({ keep: "kept" });
shot("frozen.keep ||= 'R'   (truthy)", fz1, "keep", () => { fz1.keep ||= "R"; });
const fz2 = Object.freeze({ keep: "" });
shot("frozen.keep ||= 'R'   (falsy)", fz2, "keep", () => { fz2.keep ||= "R"; });
const fz3 = Object.freeze({ keep: null });
shot("frozen.keep ??= 'R'   (null)", fz3, "keep", () => { fz3.keep ??= "R"; });
const fz4 = Object.freeze({ keep: "" });
shot("frozen.keep = keep || 'R'", fz4, "keep", () => { fz4.keep = fz4.keep || "R"; });
```

- ★★★ `[1]` 의 첫 두 줄에서 **`setter log` 칸**에 무엇이 찍히는가? 둘이 다른가?
- ★★★ 그 두 줄의 **`final` 칸**은 같은가 다른가?
- ★★ `[2]` 에서 시작값이 `0` 일 때 **세 연산자가 각각 쓰는가**?
- ★ `[3]` 에서 동결된 객체의 네 줄 중 **아무것도 안 터진 이유**는?

### 4. 두 모드에서 같은 줄을 돌리면 (예측) ★★

```js
// js12b-12s-strict.js
// 엄격 / 비엄격 전수 격자.
// ★ 바로 앞 배치의 사고를 막는 처방 둘을 그대로 쓴다 --
//   (1) 엄격을 먼저 돌린다  (2) 탐침마다 전역 이름을 다르게 준다.
// 두 탐침이 같은 전역을 쓰면 비엄격이 만든 암시적 전역을 엄격이 읽어 「같다」는 거짓 결과가 난다.
// 이름이 다르면 메시지에 그 이름이 박히므로, 비교 전에 이름을 <G> 로 되돌려 놓는다.
const probes = [
  ["plain  G = 1", "G = 1; return String(G);"],
  ["plain  var q; q = 1", "var q; q = 1; return String(q);"],
  ["logical  G ??= 1", "G ??= 1; return String(G);"],
  ["logical  G ||= 1", "G ||= 1; return String(G);"],
  ["frozen.p ||= 'R'   p=''", "const o = Object.freeze({ p: '' }); o.p ||= 'R'; return JSON.stringify(o.p);"],
  ["frozen.p ??= 'R'   p=null", "const o = Object.freeze({ p: null }); o.p ??= 'R'; return JSON.stringify(o.p);"],
  ["getter-only ??= 'R'", "const o = { get p() { return null; } }; o.p ??= 'R'; return JSON.stringify(o.p);"],
  ["getter-only ||= 'R'", "const o = { get p() { return 0; } }; o.p ||= 'R'; return JSON.stringify(o.p);"],
  ["delete o?.p   configurable", "const o = { p: 1 }; const r = delete o?.p; return r + ' keys=' + JSON.stringify(Object.keys(o));"],
  ["delete o?.p   non-config", "const o = Object.defineProperty({}, 'p', { value: 1 }); const r = delete o?.p; return r + ' keys=' + JSON.stringify(Object.getOwnPropertyNames(o));"],
  ["delete nul?.p  nul=null", "const nul = null; return String(delete nul?.p);"],
];

function run(mode, body, gname) {
  const src = (mode === "strict" ? '"use strict";\n' : "") + body.replace(/\bG\b/g, gname);
  let out;
  try { out = "OK " + new Function(src)(); }
  catch (e) { out = e.constructor.name + " " + e.message; }
  return out.split(gname).join("<G>");
}

// ★ 엄격을 먼저 -- 비엄격이 전역을 만들기 전에 찍는다.
const strictOut = probes.map(([, body], i) => run("strict", body, "js12bStrictG" + i));
const sloppyOut = probes.map(([, body], i) => run("sloppy", body, "js12bSloppyG" + i));

console.log("[1] strict-first grid   (each probe owns a unique global name, printed back as <G>)");
let split = 0;
probes.forEach(([label], i) => {
  const same = strictOut[i] === sloppyOut[i];
  if (!same) split += 1;
  console.log(label.padEnd(30) + (same ? "SAME  " : "SPLIT ") + "strict: " + strictOut[i]);
  console.log("".padEnd(30) + "      " + "sloppy: " + sloppyOut[i]);
});
console.log("");
console.log("mode-dependent cells " + split + " / " + probes.length);

console.log("");
console.log("[2] what the sloppy probes left behind on globalThis");
const leaked = Object.getOwnPropertyNames(globalThis).filter((k) => k.startsWith("js12b")).sort();
console.log("globals starting with js12b -> " + JSON.stringify(leaked));
console.log("any js12bStrictG* leaked?   -> " + leaked.some((k) => k.startsWith("js12bStrictG")));
console.log("if strict had run SECOND it would have read the sloppy leftover and reported SAME.");
```

- ★★★ **`SPLIT` 로 찍히는 줄은 몇 / 몇**인가?
- ★★★ `G ??= 1` 은 두 모드에서 각각 무엇을 내놓는가? **`G = 1` 과 같은가**?
- ★★ `[2]` 에서 **globalThis 에 남은 이름은 몇 개**이고 무엇인가?
- ★ 마지막 줄이 말하는 「엄격을 나중에 돌렸다면」은 무슨 뜻인가?

### 5. 컴파일되는 것과 안 되는 것 (예측) ★★

```js
// js12b-12x-forms.js
// 문법 격자 -- SyntaxError 는 try/catch 로 못 잡으므로 new Function 으로 「컴파일만」 해 본다.
// ★ 엄격을 먼저 돌린다. 이 격자는 값을 만들지 않으므로 전역을 오염시키지 않는다.
const forms = [
  "a ?? b || c",
  "a || b ?? c",
  "a ?? b && c",
  "a && b ?? c",
  "(a ?? b) || c",
  "a ?? (b || c)",
  "a ?? b ?? c",
  "a || b || c",
  "new a?.b()",
  "new (a?.b)()",
  "a?.b()",
  "a?.()",
  "new a?.()",
  "a?.b`tpl`",
  "a?.b = 1",
  "delete a?.b",
  "a?.b++",
  "a ??= b",
  "a?.b ??= c",
  "({}) ?? 1",
];

function compile(mode, expr) {
  const src = (mode === "strict" ? '"use strict";\n' : "") + "let a, b, c; return (" + expr + ");";
  try { new Function(src); return "OK"; }
  catch (e) { return e.constructor.name + " " + e.message; }
}

// ★ 엄격 먼저.
const strictOut = forms.map((f) => compile("strict", f));
const sloppyOut = forms.map((f) => compile("sloppy", f));

console.log("[1] does it even compile?   (strict run first, then sloppy)");
let split = 0;
forms.forEach((f, i) => {
  const same = strictOut[i] === sloppyOut[i];
  if (!same) split += 1;
  console.log(f.padEnd(18) + (same ? "SAME  " : "SPLIT ") + strictOut[i]);
  if (!same) console.log("".padEnd(18) + "      sloppy: " + sloppyOut[i]);
});
console.log("");
console.log("mode-dependent cells " + split + " / " + forms.length);

console.log("");
console.log("[2] duplicate keys in an object literal -- ES5 strict forbade this, ES6+ does not");
for (const mode of ["strict", "sloppy"]) {
  const src = (mode === "strict" ? '"use strict";\n' : "") + "return JSON.stringify({ a: 1, a: 2, a: 3 });";
  let out;
  try { out = "OK " + new Function(src)(); } catch (e) { out = e.constructor.name + " " + e.message; }
  console.log(mode.padEnd(8) + "{ a: 1, a: 2, a: 3 }  -> " + out);
}
```

- ★★ 20형태 중 **컴파일되는 것은 몇 개**인가?
- ★★★ `SPLIT` 는 몇 개인가?
- ★ `[2]` 의 두 줄은 어떤 결과인가? 그리고 그 사실이 **왜 놀라운가**?

### 6. 캐럿은 어디를 가리키나 (예측) ★

```js
// js12b-12y-caret.js
// 18-C -- 값으로 못 가르는 문법 성질은 진단이 가리키는 열로 증명한다.
// new Function 은 파일명을 못 주므로 vm.Script 에 filename 을 고정해 캐럿까지 결정적으로 받는다.
// (node --check 는 절대 경로를 박아 재현이 안 된다 -- 그래서 안 쓴다.)
const vm = require("vm");
for (const src of [
  "a ?? b || c",
  "a || b ?? c",
  "a ?? b && c",
  "a && b ?? c",
  "(a ?? b) || c",
  "a ?? (b || c)",
  "a ?? b ?? c",
  "new a?.b()",
  "a?.b`t`",
  "a?.b ??= c",
]) {
  try {
    new vm.Script(src, { filename: "ex.js" });
    console.log("=== " + src);
    console.log("compiles.");
  } catch (e) {
    console.log("=== " + src);
    console.log(e.stack.split("\n").slice(0, 3).join("\n"));
    console.log(e.constructor.name + " " + e.message);
  }
  console.log("");
}
```

- ★★ 첫 네 식의 **캐럿 열이 같은가 다른가**?
- ★★★ 그 열이 말하는 것은 무엇인가 — 「우선순위가 낮다」인가 「우선순위가 없다」인가?
- ★ `a?.b ??= c` 의 캐럿은 **식의 어느 부분**을 덮는가?

### 7. `?.` 는 정확히 무엇을 막는가 (경계) ★★★

- ★★★ `?.` 가 막는 값은 몇 종류이고 무엇인가? **falsy 여덟 종과 어떻게 다른가**?
- ★★★ `a?.b.c` 에서 `a` 가 아니라 **`a.b` 가 `null`** 이면 어떻게 되는가?
- ★★ `(a?.b).c` 와 `a?.b.c` 는 왜 다른가?
- ★ 옵셔널 체인이 **대입의 왼쪽**이 될 수 없는데 `delete` 만 되는 이유는 무엇으로 확인하는가?

### 8. 왜 `??` 를 `||` 와 못 섞는가 (왜) ★★

- ★★★ 이것은 **런타임 오류인가 파싱 오류인가**? 그 차이가 실무에서 왜 큰가?
- ★★ 괄호를 치면 되는 이유를 한 문장으로.
- ★ `a ?? b ?? c` 는 왜 되는가?

### 9. 어디서 조용히 틀리나 (경계) ★★★

- 이 주제에서 **에러 없이 틀리는 자리** 넷을 대면?
- ★★★ 그 중 **11번에서 본 것과 같은 모양**(값은 같은데 부른 연산이 다르다)인 것은 무엇인가?
- ★★ 동결된 객체에 `||=` 를 썼는데 안 터졌다면, 그것이 **동결이 느슨하다는 뜻인가**?
- ★ 비엄격에서 「조용히 실패」한 쓰기를 **무엇으로 발견**할 수 있는가?

### 10. 보장인가 엔진 사정인가 (연결) ★★★

- 이 주제에서 **두 판이 갈린 칸은 몇 개**였는가?
- ★★★ 예외 **종류**와 **문구** 중 어느 쪽이 명세의 몫인가? 어떻게 아는가?
- ★★ 브라우저에 같은 줄을 던졌을 때 **호스트가 정하는 칸은 몇 개**였는가?
- ★ 이 주제에서 **부적용인 창**은 무엇이고, 「안 쟀다」와 어떻게 다른가?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **falsy 목록** · **엄격 모드 규칙 전부** · **동결이 왜 쓰기를 막나** · **`Object.is`** 는 각각 어느 주제가 정본인가?
- ★★★ **10번의 기본값**(구조 분해)과 **`??`** 는 「비었다」를 **어떻게 다르게 세는가**?
- ★★ 02번의 결론 중 이 주제가 **그대로 받아 쓰는 것**은 무엇인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
