# js/syntax/22 — `Symbol` 과 잘 알려진 심볼: 「심볼은 이름이 겹칠 수 없는 키이고, 잘 알려진 심볼은 언어가 먼저 들여다보는 키다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(headless) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다. 이 파일은 **소스만** 싣는다 — 출력은 정답 파일에 있다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `+`·`instanceof`·`map` 이 **어떤 심볼 키를 읽고 무엇을 넘기는지**는 결과값에 흔적이 없다 — 그 키에 로그를 심어야 보인다.
> **1번 문항(hint 로그)이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **심볼 키가 누구에게 보이나**(그리고 그것이 「비공개」인가)
> ② ★★★ **잘 알려진 심볼이 어느 연산에서 무엇을 가로채나**
> ③ **심볼 자신의 변환과 같음**(`String()` · 템플릿 리터럴 · `Symbol.for`).
>
> ★★ **예외는 타입과 메시지로만 답한다.** ★ 메시지는 판마다 다를 수 있다 — 종류가 먼저다.
>
> **선행** — [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ 직접 선행) ·
> [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) · [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) ·
> [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md) · [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md).
> ★★★ **02편 `[5]` 의 세 줄을 먼저 떠올려라** — `o + 1`·`` `${o}` ``·`o * 2` 가 각각 어떤 hint 를 받았나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「결과」보다 「hint」를 먼저** 적어라. 줄마다 `default`/`number`/`string`/「안 부름」 중 하나다.
- ★★ **2번은 격자의 `o`/`.` 을 칸마다** 적고, 마지막 줄의 「N / M」 까지 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판에만 있는 것인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「심볼 키는 느리다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 연산 24가지가 `Symbol.toPrimitive` 에 넘기는 hint (예측) ★★★ 이 주제의 축

```text
x 의 [Symbol.toPrimitive](hint) 는 hint 를 로그에 적고, hint 가 "string" 이면 "S", 아니면 7 을 돌려준다.
```

```js
// js20b-22c-toprimitive-hints.js
// Symbol.toPrimitive 에 로그를 심고 연산자·내장 함수마다 hint 가 무엇으로 오나를 찍는다.
// 02편의 ToPrimitive 탐침(valueOf/toString 순서)을 이 한 메서드로 가로챈 판이다.
const L = [];
const x = { [Symbol.toPrimitive](hint) { L.push(hint); return hint === "string" ? "S" : 7; } };
let counting = true;
const tally = { default: 0, number: 0, string: 0, "(no call)": 0 };
const show = (v) => (typeof v === "string" ? JSON.stringify(v) : typeof v === "bigint" ? v + "n" : String(v));
function probe(label, run) {
  L.length = 0;
  let r;
  try { r = show(run()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  const hints = L.length ? L.join(",") : "(no call)";
  if (counting) for (const h of L.length ? L : ["(no call)"]) tally[h]++;
  console.log("  " + label.padEnd(24) + hints.padEnd(26) + r);
}

console.log("[1] expression               hint(s)                   result");
probe("x + 1", () => x + 1);
probe("x + ''", () => x + "");
probe("`${x}`", () => `${x}`);
probe("x == 7", () => x == 7);
probe("x != 'S'", () => x != "S");
probe("x === 7", () => x === 7);
probe("x < 8", () => x < 8);
probe("x * 1", () => x * 1);
probe("+x", () => +x);
probe("-x", () => -x);
probe("x ** 1", () => x ** 1);
probe("x | 0", () => x | 0);
probe("String(x)", () => String(x));
probe("Number(x)", () => Number(x));
probe("BigInt(x)", () => BigInt(x));
probe("[x].join()", () => [x].join());
probe("({})[x] = 1 -> key", () => { const t = {}; t[x] = 1; return Object.keys(t)[0]; });
probe("x in {S: 1}", () => x in { S: 1 });
probe("new Date(x).getTime()", () => new Date(x).getTime());
probe("isNaN(x)", () => isNaN(x));
probe("'aSb'.includes(x)", () => "aSb".includes(x));
probe("!x", () => !x);
probe("x ? 'y' : 'n'", () => (x ? "y" : "n"));
probe("JSON.stringify(x)", () => JSON.stringify(x));

console.log("");
console.log("[2] hint tally " + JSON.stringify(tally));
counting = false;

console.log("");
console.log("[3] what the method returns, or what it is");
const spy = (f) => function (hint) { L.push("@@toPrimitive(" + hint + ")"); return f(); };
const bad = (label, v) => probe(label, () => { const o = { [Symbol.toPrimitive]: v, valueOf() { L.push("valueOf"); return 1; }, toString() { L.push("toString"); return "T"; } }; return o + 1; });
bad("returns an object", spy(() => ({})));
bad("returns a symbol", spy(() => Symbol("r")));
bad("is the number 1", 1);
bad("is null", null);
bad("is undefined", undefined);
probe("returns a symbol, `${}`", () => `${{ [Symbol.toPrimitive]: spy(() => Symbol("r")) }}`);

console.log("");
console.log("[4] Date carries its own Symbol.toPrimitive -- spy on it");
const dproto = Date.prototype;
const orig = dproto[Symbol.toPrimitive];
const d = new Date(0);
Object.defineProperty(d, Symbol.toPrimitive, { value(hint) { L.push(hint); return orig.call(this, hint); } });
probe("typeof (d + 1)", () => typeof (d + 1));
probe("typeof (d - 1)", () => typeof (d - 1));
probe("d == d.toString()", () => d == d.toString());
probe("d < 1", () => d < 1);
console.log("  own descriptor on Date.prototype: " + JSON.stringify(Object.getOwnPropertyDescriptor(dproto, Symbol.toPrimitive), (k, v) => (typeof v === "function" ? "fn" : v)));
```

- `[1]` 의 24줄마다 **hint(또는 「안 부름」)와 결과**를 적어라. 특히 `x + ''` 의 결과는 `"S"` 인가 `"7"` 인가?
- `[2]` 의 집계 줄을 적어라.
- `[3]` — 메서드 자리에 `null`·`undefined`·`1` 을 두면 각각 무엇이 되나? 객체나 심볼을 돌려주면?
- `[4]` — `Date` 인스턴스의 `d + 1` 과 `d - 1` 은 각각 어떤 hint 를 받고 결과의 `typeof` 는 무엇인가?

### 2. 키 종류 다섯 × 문법 열 개 (예측)

```js
// js20b-22b-key-grid.js
// 심볼 키의 성질 격자 -- 키 종류 × 키를 늘어놓는(또는 복사하는) 문법. 누가 무엇을 보나를 전수로 찍는다.
// 18편의 격자(프로퍼티 여섯 종 × 아홉 문법)에서 own 줄만 떼어 심볼 쪽 줄을 늘렸다.
const sEnum = Symbol("sEnum");
const sHidden = Symbol("sHidden");
const sReg = Symbol.for("sReg");
const o = {};
o.str = 1;
o[sEnum] = 1;
Object.defineProperty(o, sHidden, { value: 1, enumerable: false });
o[sReg] = 1;
o[Symbol.iterator] = function* () {};

const kinds = [
  ["string key", "str"],
  ["symbol key", sEnum],
  ["symbol key, non-enumerable", sHidden],
  ["Symbol.for key", sReg],
  ["Symbol.iterator key", Symbol.iterator],
];
const forIn = (x) => { const r = []; for (const k in x) r.push(k); return r; };
const views = [
  ["for-in", (x) => forIn(x)],
  ["keys", (x) => Object.keys(x)],
  ["entries", (x) => Object.entries(x).map(([k]) => k)],
  ["JSON", (x) => Object.keys(JSON.parse(JSON.stringify(x)))],
  ["gOPN", (x) => Object.getOwnPropertyNames(x)],
  ["gOPS", (x) => Object.getOwnPropertySymbols(x)],
  ["ownKeys", (x) => Reflect.ownKeys(x)],
  ["{...}", (x) => Reflect.ownKeys({ ...x })],
  ["assign", (x) => Reflect.ownKeys(Object.assign({}, x))],
  ["hasOwn", (x) => kinds.map(([, k]) => k).filter((k) => Object.hasOwn(x, k))],
];
console.log("[1] who sees what   (o = sees it, . = does not)");
console.log(("".padEnd(28) + views.map(([n]) => n.padEnd(9)).join("")).trimEnd());
const seen = views.map(([, f]) => f(o));
const grid = kinds.map(([, k]) => seen.map((s) => s.includes(k)));
kinds.forEach(([label], i) => {
  console.log((label.padEnd(28) + grid[i].map((b) => (b ? "o" : ".").padEnd(9)).join("")).trimEnd());
});

console.log("");
console.log("[2] row 'symbol key' against row 'string key', column by column");
const differ = views.filter((_, j) => grid[0][j] !== grid[1][j]).map(([n]) => n);
console.log("  columns that differ " + JSON.stringify(differ));
const sameAs = (a, b) => grid[a].every((v, j) => v === grid[b][j]);
console.log("  'Symbol.for key' row equals 'symbol key' row       " + sameAs(3, 1));
console.log("  'Symbol.iterator key' row equals 'symbol key' row  " + sameAs(4, 1));

console.log("");
console.log("[3] Reflect.ownKeys order -- keys added as: sym1, b, 2, sym2, a, 1");
const q = {};
const sym1 = Symbol("sym1"), sym2 = Symbol("sym2");
q[sym1] = 1; q.b = 1; q[2] = 1; q[sym2] = 1; q.a = 1; q[1] = 1;
console.log("  " + JSON.stringify(Reflect.ownKeys(q).map(String)));

console.log("");
console.log("differing cells (string key vs symbol key) " + differ.length + " / " + views.length);
```

- `[1]` 의 격자를 `o`/`.` 로 채워라. **비열거 심볼 줄**은 스프레드·`assign` 에서 어떻게 되나?
- `[2]` 의 「갈린 열」 목록과 두 `true`/`false`, 마지막 집계 줄을 적어라.
- `[3]` — `sym1, b, 2, sym2, a, 1` 순서로 넣은 키를 `Reflect.ownKeys` 는 어떤 순서로 돌려주나?

### 3. 심볼 하나를 만들고, 설명을 읽고, 변환한다 (예측)

```js
// js20b-22a-basics.js
// Symbol() 한 개의 성질 -- 만들기 · 설명 · 같음 · 변환. 예외는 이름과 메시지로 찍는다.
const row = (label, v) => console.log("  " + label.padEnd(36) + v);
const attempt = (label, run) => {
  let r;
  try { r = run(); r = typeof r === "string" ? JSON.stringify(r) : String(r); }
  catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  row(label, r);
};

console.log("[1] making symbols");
attempt("typeof Symbol('a')", () => typeof Symbol("a"));
attempt("Symbol('a') === Symbol('a')", () => Symbol("a") === Symbol("a"));
attempt("new Symbol('a')", () => new Symbol("a"));
attempt("typeof Object(Symbol('a'))", () => typeof Object(Symbol("a")));
attempt("Object(s) == s  (same s)", () => { const s = Symbol("a"); return Object(s) == s; });

console.log("");
console.log("[2] description");
attempt("Symbol('a').description", () => Symbol("a").description);
attempt("Symbol('').description", () => Symbol("").description);
attempt("Symbol().description", () => Symbol().description);
attempt("Symbol(undefined).description", () => Symbol(undefined).description);
attempt("Symbol(42).description", () => Symbol(42).description);
attempt("Symbol({}).description", () => Symbol({}).description);

console.log("");
console.log("[3] String() · .toString() · Boolean() · a symbol key under Object.keys");
const s = Symbol("k");
attempt("String(s)", () => String(s));
attempt("s.toString()", () => s.toString());
attempt("Boolean(s) / !!s", () => Boolean(s) + " / " + !!s);
attempt("Object.keys({ [s]: 1 }).length", () => Object.keys({ [s]: 1 }).length);

console.log("");
console.log("[4] operators · concat · join · Number() · JSON");
attempt("s + ''", () => s + "");
attempt("`${s}`", () => `${s}`);
attempt("'x'.concat(s)", () => "x".concat(s));
attempt("[s].join()", () => [s].join());
attempt("+s", () => +s);
attempt("Number(s)", () => Number(s));
attempt("s + 1", () => s + 1);
attempt("s == 'Symbol(k)'", () => s == "Symbol(k)");
attempt("s < 1", () => s < 1);
attempt("JSON.stringify(s)", () => JSON.stringify(s));
attempt("JSON.stringify({ v: s })", () => JSON.stringify({ v: s }));
attempt("JSON.stringify([s])", () => JSON.stringify([s]));

console.log("");
const cells = [];
for (const [label, f] of [["String(s)", () => String(s)], ["s + ''", () => s + ""], ["`${s}`", () => `${s}`],
  ["[s].join()", () => [s].join()], ["Number(s)", () => Number(s)], ["+s", () => +s]]) {
  try { f(); cells.push(label + ":ok"); } catch (e) { cells.push(label + ":" + e.constructor.name); }
}
console.log("[5] six conversions: " + cells.join("  "));
console.log("throwing cells " + cells.filter((c) => !c.endsWith(":ok")).length + " / " + cells.length);
```

- `[1]`·`[2]` 의 결과를 적어라 — 특히 `Symbol().description` 과 `Symbol('').description` 은 같은가?
- `[3]`·`[4]` 에서 **던지는 줄을 전부** 골라 문구까지 적어라. `Number(s)` 는 어느 쪽인가?
- `[5]` 의 집계 줄 「throwing cells N / 6」 의 N 은?

### 4. `Symbol.toStringTag` 를 붙인 값과 슬롯 판별 (예측)

```js
// js20b-22e-tostringtag.js
// Symbol.toStringTag 로 브랜드 태그 창 ③(Object.prototype.toString.call)을 바꿔치기한다.
// 같은 값에 내부 슬롯을 보는 판별을 나란히 대서 두 창이 갈리는 칸을 센다.
const tag = (v) => Object.prototype.toString.call(v);
const slot = {
  Array: (v) => Array.isArray(v),
  Map: (v) => { try { Map.prototype.has.call(v, 1); return true; } catch { return false; } },
  Date: (v) => { try { Date.prototype.getTime.call(v); return true; } catch { return false; } },
  Promise: (v) => { try { Promise.prototype.then.call(v, () => {}); return true; } catch { return false; } },
};

console.log("[1] brand tags of built-ins, as they come");
for (const [label, v] of [["[]", []], ["new Map()", new Map()], ["new Date(0)", new Date(0)], ["Promise.resolve()", Promise.resolve()],
  ["new Error('e')", new Error("e")], ["function(){}", function () {}], ["null", null], ["{}", {}], ["Symbol()", Symbol()]]) {
  console.log("  " + label.padEnd(26) + tag(v));
}

console.log("");
console.log("[2] a string-valued Symbol.toStringTag, and a slot check on the same value");
console.log("  value".padEnd(40) + "toString tag".padEnd(20) + "slot check");
const cases = [
  ["{ tag 'Array' }", { [Symbol.toStringTag]: "Array" }, "Array"],
  ["{ tag 'Map' }", { [Symbol.toStringTag]: "Map" }, "Map"],
  ["{ tag 'Date' }", { [Symbol.toStringTag]: "Date" }, "Date"],
  ["{ tag 'Promise' }", { [Symbol.toStringTag]: "Promise" }, "Promise"],
  ["[] with tag 'Foo'", Object.assign([], { [Symbol.toStringTag]: "Foo" }), "Array"],
  ["new Map() with tag 'Foo'", Object.defineProperty(new Map(), Symbol.toStringTag, { value: "Foo" }), "Map"],
  ["new Date(0) with tag 'Foo'", Object.assign(new Date(0), { [Symbol.toStringTag]: "Foo" }), "Date"],
];
let split = 0;
for (const [label, v, kind] of cases) {
  const t = tag(v);
  const says = t === "[object " + kind + "]";
  const s = slot[kind](v);
  if (says !== s) split++;
  console.log(("  " + label).padEnd(40) + t.padEnd(20) + kind + " slot " + s);
}

console.log("");
console.log("[3] a tag that is not a string");
console.log("  { tag 42 }".padEnd(40) + tag({ [Symbol.toStringTag]: 42 }));
console.log("  { tag undefined }".padEnd(40) + tag({ [Symbol.toStringTag]: undefined }));

console.log("");
console.log("[4] where Map's tag lives -- and after deleting it");
console.log("  descriptor on Map.prototype  " + JSON.stringify(Object.getOwnPropertyDescriptor(Map.prototype, Symbol.toStringTag)));
const arrDesc = Object.getOwnPropertyDescriptor(Array.prototype, Symbol.toStringTag);
console.log("  descriptor on Array.prototype " + JSON.stringify(arrDesc === undefined ? "none" : arrDesc));
delete Map.prototype[Symbol.toStringTag];
console.log("  after delete: tag(new Map()) " + tag(new Map()));

console.log("");
console.log("cells where the toString tag and the slot check disagree " + split + " / " + cases.length);
```

- `[2]` 의 일곱 줄마다 **toString 태그**와 **슬롯 판별**(`true`/`false`)을 적어라.
- `[4]` — `Map.prototype` 과 `Array.prototype` 에 `Symbol.toStringTag` 프로퍼티가 있나? `Map` 의 것을 지우면 `new Map()` 의 태그는?
- 마지막 집계 줄의 N / 7 은?

### 5. 보통 함수에 `Symbol.hasInstance` 를 대입하면 (예측)

```js
// js20b-22d-hasinstance.js
// Symbol.hasInstance -- instanceof 가 오른쪽 피연산자에게 무엇을 묻나. 15편 [4] 의 뒤를 잇는다.
const row = (label, v) => console.log("  " + label.padEnd(50) + v);
const attempt = (label, run) => {
  let r;
  try { r = String(run()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  row(label, r);
};

console.log("[1] a logging hasInstance -- what it receives, what instanceof returns");
const L = [];
class Even { static [Symbol.hasInstance](v) { L.push("hasInstance(" + JSON.stringify(v) + ")"); return v % 2 === 0 ? "yes" : 0; } }
attempt("4 instanceof Even", () => 4 instanceof Even);
attempt("3 instanceof Even", () => 3 instanceof Even);
attempt("typeof (4 instanceof Even)", () => typeof (4 instanceof Even));
row("log", JSON.stringify(L));

console.log("");
console.log("[2] the right-hand side");
attempt("({}) instanceof { [Symbol.hasInstance]: () => true }", () => ({}) instanceof { [Symbol.hasInstance]: () => true });
attempt("({}) instanceof {}", () => ({}) instanceof {});
attempt("({}) instanceof { [Symbol.hasInstance]: 1 }", () => ({}) instanceof { [Symbol.hasInstance]: 1 });
attempt("({}) instanceof 1", () => ({}) instanceof 1);

console.log("");
console.log("[3] Function.prototype[Symbol.hasInstance] -- its descriptor");
row("descriptor", JSON.stringify(Object.getOwnPropertyDescriptor(Function.prototype, Symbol.hasInstance), (k, v) => (typeof v === "function" ? "fn" : v)));

console.log("");
console.log("[4] putting a hasInstance on a plain function F");
function F() {}
attempt("sloppy  F[Symbol.hasInstance] = () => true", () => { F[Symbol.hasInstance] = () => true; return "no throw"; });
attempt("  then ({}) instanceof F", () => ({}) instanceof F);
attempt("  then hasOwn(F, Symbol.hasInstance)", () => Object.hasOwn(F, Symbol.hasInstance));
attempt("strict  F[Symbol.hasInstance] = () => true", () => { "use strict"; F[Symbol.hasInstance] = () => true; return "no throw"; });
attempt("defineProperty(F, Symbol.hasInstance, ...)", () => { Object.defineProperty(F, Symbol.hasInstance, { value: () => true }); return "no throw"; });
attempt("  then ({}) instanceof F", () => ({}) instanceof F);

console.log("");
console.log("[5] the default path for comparison -- Function.prototype[Symbol.hasInstance].call");
class A {}
const a = new A();
attempt("Function.prototype[@@hasInstance].call(A, a)", () => Function.prototype[Symbol.hasInstance].call(A, a));
attempt("Function.prototype[@@hasInstance].call(A, {})", () => Function.prototype[Symbol.hasInstance].call(A, {}));
```

- `[1]` — `4 instanceof Even` 과 그 `typeof` 는? 로그에는 무엇이 몇 번 찍히나?
- `[2]` 의 네 줄 — 던지면 문구까지.
- `[4]` 의 여섯 줄을 적어라. **비엄격 대입** 뒤에 `({}) instanceof F` 와 `hasOwn` 은? 엄격 대입은?

### 6. `Array` 하위 클래스에서 species 를 읽는 메서드 (예측)

```js
// js20b-22f-species.js
// Symbol.species -- 어느 메서드가 그것을 읽나. 17편은 map/filter/slice/from 의 결과 생성자까지 봤다.
// 여기서는 species getter 에 로그를 심어 메서드마다 읽었나를 센다(ES2023 복사 메서드 포함).
const L = [];
class Tracked extends Array {
  static get [Symbol.species]() { L.push("species"); return Array; }
}
const t = Tracked.from([3, 1, 2]);
const methods = [
  ["map", (a) => a.map((x) => x)],
  ["filter", (a) => a.filter(() => true)],
  ["slice", (a) => a.slice()],
  ["splice", (a) => a.splice(0, 0)],
  ["concat", (a) => a.concat([])],
  ["flat", (a) => a.flat()],
  ["flatMap", (a) => a.flatMap((x) => [x])],
  ["toSorted", (a) => a.toSorted()],
  ["toReversed", (a) => a.toReversed()],
  ["with", (a) => a.with(0, 9)],
  ["toSpliced", (a) => a.toSpliced(0, 0)],
  ["Array.from(a)", (a) => Array.from(a)],
  ["[...a]", (a) => [...a]],
  ["sort", (a) => a.sort()],
];
console.log("[1] method          species read?   result constructor");
let read = 0, total = 0;
for (const [label, f] of methods) {
  L.length = 0;
  let r;
  try { r = f(Tracked.from(t)).constructor.name; } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  total++; if (L.length) read++;
  console.log("  " + label.padEnd(18) + (L.length ? "read x" + L.length : "-").padEnd(16) + r);
}
console.log("methods that read species " + read + " / " + total);

console.log("");
console.log("[2] species values other than a constructor");
const withSpecies = (v) => { class S extends Array { static get [Symbol.species]() { return v; } } return S.from([1, 2]); };
for (const [label, v] of [["undefined", undefined], ["null", null], ["42", 42], ["function returning {}", function () { return {}; }]]) {
  let r;
  try { const m = withSpecies(v).map((x) => x); r = (m.constructor && m.constructor.name) + " " + JSON.stringify(m); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  species = " + label.padEnd(20) + r);
}

console.log("");
console.log("[3] Promise.prototype.then and species");
const P = [];
class TP extends Promise { static get [Symbol.species]() { P.push("species"); return Promise; } }
const tp = TP.resolve(1);
const th = tp.then((x) => x);
console.log("  tp.then(...) constructor " + th.constructor.name + "   species reads " + P.length);
P.length = 0;
const fin = tp.finally(() => {});
console.log("  tp.finally(...) constructor " + fin.constructor.name + "   species reads " + P.length);
```

- `[1]` 의 14줄마다 **species 를 읽었나**와 **결과 생성자**를 적고, 집계 줄 N / 14 를 적어라.
- `[2]` — species 가 `undefined`·`null`·`42`·`{}` 를 돌려주는 함수일 때 `map` 의 결과는?
- `[3]` — `then` 과 `finally` 는 species 를 각각 몇 번 읽나?
- ★ 이 탐침을 **node18** 로 돌리면 어느 줄이 달라지나?

### 7. `String(s)` 은 되는데 `Number(s)` 와 `` `${s}` `` 는 던진다 (왜)

- 명세의 어느 함수·추상 연산이 이 비대칭을 만드나? 「명시적이면 된다」는 요약이 왜 틀리나?
- 로그 문자열에 심볼 키를 안전하게 끼우려면 무엇을 쓰나?

### 8. `Symbol.for` 와 `Symbol()` — 같음 · `keyFor` · 약한 키 (경계)

```js
// js20b-22h-registry.js
// Symbol.for 전역 레지스트리 대 Symbol() -- 같음 · keyFor · 잘 알려진 심볼 · 약한 참조의 키가 될 수 있나.
const row = (label, v) => console.log("  " + label.padEnd(52) + v);
const attempt = (label, run) => {
  let r;
  try { r = String(run()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  row(label, r);
};

console.log("[1] same description, three ways");
attempt("Symbol.for('app') === Symbol.for('app')", () => Symbol.for("app") === Symbol.for("app"));
attempt("Symbol('app') === Symbol('app')", () => Symbol("app") === Symbol("app"));
attempt("Symbol.for('app') === Symbol('app')", () => Symbol.for("app") === Symbol("app"));
attempt("Symbol.for('app').description", () => Symbol.for("app").description);

console.log("");
console.log("[2] Symbol.keyFor");
attempt("Symbol.keyFor(Symbol.for('app'))", () => Symbol.keyFor(Symbol.for("app")));
attempt("Symbol.keyFor(Symbol('app'))", () => Symbol.keyFor(Symbol("app")));
attempt("Symbol.keyFor(Symbol.iterator)", () => Symbol.keyFor(Symbol.iterator));
attempt("Symbol.keyFor('app')", () => Symbol.keyFor("app"));
attempt("Symbol.iterator === Symbol.for('Symbol.iterator')", () => Symbol.iterator === Symbol.for("Symbol.iterator"));

console.log("");
console.log("[3] across realms -- a fresh vm context (node:vm)");
const vm = require("node:vm");
const other = vm.runInNewContext("({ reg: Symbol.for('app'), it: Symbol.iterator, plain: Symbol('app') })");
attempt("other.reg === Symbol.for('app')", () => other.reg === Symbol.for("app"));
attempt("other.it === Symbol.iterator", () => other.it === Symbol.iterator);
attempt("other.plain === Symbol('app')", () => other.plain === Symbol("app"));

console.log("");
console.log("[4] as a WeakMap key / WeakRef target");
const kinds = [["Symbol('k')", Symbol("k")], ["Symbol.for('k')", Symbol.for("k")], ["Symbol.iterator", Symbol.iterator]];
let ok = 0;
for (const [label, s] of kinds) {
  attempt("new WeakMap().set(" + label + ", 1)", () => { new WeakMap().set(s, 1); ok++; return "ok"; });
  attempt("new WeakRef(" + label + ")", () => { new WeakRef(s); return "ok"; });
}
console.log("");
console.log("symbol kinds accepted as a WeakMap key " + ok + " / " + kinds.length);
```

- `[1]`\~`[3]` 에서 `true` 가 나오는 줄은 어느 것인가?
- `[4]` — node20 과 node18 에서 각각 몇 / 3 인가? node20 에서 거절되는 심볼은 **왜** 거절되나(명세의 추상 연산 이름으로)?

### 9. `Symbol.toPrimitive` 가 `null` 이면 조용하고 `1` 이면 던진다 (왜)

- 1번 `[3]` 의 두 줄이 반대로 갈리는 이유를 명세의 추상 연산 이름 하나로 설명하라.
- 같은 규칙이 `Symbol.hasInstance`·`Symbol.iterator` 에도 서나? 이 문서의 어느 출력이 그것을 보이나?

### 10. 배열의 `Symbol.iterator` 를 바꾸거나 지우면 누가 따라가나 (연결)

```js
// js20b-22g-other-hooks.js
// 잘 알려진 심볼 넷 -- 값 하나를 바꾸면 어느 언어 동작·내장 함수가 따라 바뀌나.
// Symbol.iterator(19편) · Symbol.isConcatSpreadable · Symbol.match · Symbol.unscopables
const row = (label, v) => console.log("  " + label.padEnd(50) + v);
const attempt = (label, run) => {
  let r;
  try { r = JSON.stringify(run()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  row(label, r);
};

console.log("[1] an array whose own Symbol.iterator yields 'x' once");
const arr = [1, 2, 3];
arr[Symbol.iterator] = function* () { yield "x"; };
attempt("[...arr]", () => [...arr]);
attempt("Array.from(arr)", () => Array.from(arr));
attempt("const [a, b] = arr", () => { const [a, b] = arr; return [a, b ?? "<undefined>"]; });
attempt("for-of collects", () => { const r = []; for (const v of arr) r.push(v); return r; });
attempt("arr.map(v => v)", () => arr.map((v) => v));
attempt("arr.join('')", () => arr.join(""));
attempt("Math.max.apply(null, arr)", () => Math.max.apply(null, arr));
attempt("JSON.stringify(arr)", () => arr);

console.log("");
console.log("[2] the same array with Symbol.iterator set to undefined");
arr[Symbol.iterator] = undefined;
attempt("[...arr]", () => [...arr]);
attempt("Array.from(arr)", () => Array.from(arr));
attempt("for-of", () => { for (const v of arr) {} return "ran"; });
attempt("arr.map(v => v)", () => arr.map((v) => v));

console.log("");
console.log("[3] Symbol.isConcatSpreadable");
attempt("[0].concat([1, 2])", () => [0].concat([1, 2]));
attempt("[0].concat(array with flag false)", () => [0].concat(Object.assign([1, 2], { [Symbol.isConcatSpreadable]: false })).length);
attempt("[0].concat({0:'a', length:1})", () => [0].concat({ 0: "a", length: 1 }).length);
attempt("[0].concat({0:'a', length:1, flag true})", () => [0].concat({ 0: "a", length: 1, [Symbol.isConcatSpreadable]: true }));

console.log("");
console.log("[4] Symbol.match -- what String methods decide is a RegExp");
attempt("'/a/b'.startsWith(/a/)", () => "/a/b".startsWith(/a/));
attempt("re[Symbol.match] = false; '/a/b'.startsWith(re)", () => { const re = /a/; re[Symbol.match] = false; return "/a/b".startsWith(re); });
attempt("'xa'.includes({ [Symbol.match]: true })", () => "xa".includes({ [Symbol.match]: true }));

console.log("");
console.log("[5] Symbol.unscopables on Array.prototype -- its keys");
row("keys", JSON.stringify(Object.keys(Array.prototype[Symbol.unscopables])));
row("prototype of that object", String(Object.getPrototypeOf(Array.prototype[Symbol.unscopables])));
const keys = "outer keys";
let seen;
with ([1, 2]) { seen = [typeof keys, typeof length === "number" ? "length " + length : "?"]; }
row("sloppy: with ([1, 2]) { keys / length }", JSON.stringify(seen));
attempt("strict: compile a with statement", () => { new Function('"use strict"; with ({}) {}'); return "compiled"; });
```

- `[1]` 에서 `["x"]` 를 내는 소비자와 `[1,2,3]` 을 내는 소비자를 갈라라. 11편의 「세 자리의 문」과 어떻게 이어지나?
- `[2]` — `undefined` 로 지운 뒤에도 `Array.from(arr)` 이 도는 이유는? 19편 동작 (4)의 무엇과 짝인가?
- `[4]` — `Symbol.match` 는 브랜드 태그(4번)와 **어떤 점에서 같은 꼴**인가?

### 11. `Symbol.unscopables` 와 `Symbol.dispose` — 쓸 자리가 있나 (경계)

```js
// js20b-22i-wellknown.js
// 이 판의 잘 알려진 심볼 목록 -- Symbol 생성자에 붙은 심볼 값 프로퍼티를 전부 찍는다.
const names = Object.getOwnPropertyNames(Symbol).filter((k) => typeof Symbol[k] === "symbol");
console.log(names.length + " " + JSON.stringify(names));
const d = Object.getOwnPropertyDescriptor(Symbol, "iterator");
console.log("Symbol.iterator descriptor " + JSON.stringify({ ...d, value: String(d.value) }));
let compiled;
try { new Function("{ using r = null; }"); compiled = "compiled"; } catch (e) { compiled = e.constructor.name + " 「" + e.message + "」"; }
console.log("a `using` declaration: " + compiled);
```

- `Symbol.unscopables` 가 바꾸는 문법은 무엇이고, 왜 현대 코드(모듈·`class`)에서 그 효과를 볼 일이 거의 없나?
- 이 파일을 세 판(node18 · node20 · Chrome 151)에 던지면 잘 알려진 심볼은 몇 개씩인가? `dispose`·`asyncDispose` 는 ES2026 명세 본문에 있나?
- 「`Symbol.dispose` 가 있다」와 「`using` 을 쓸 수 있다」는 같은 말인가? 마지막 줄은 세 판에서 각각 무엇인가?

### 12. 파이썬의 dunder 대 JS 의 잘 알려진 심볼 (연결)

- 파이썬은 언어 동작을 바꾸는 훅을 **무엇으로** 부르고(Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**), JS 는 무엇으로 부르나? 그 차이가 **이름 충돌**에 대해 무엇을 바꾸나?
- 파이썬의 `__bool__`(같은 목록의 **05번**)에 해당하는 심볼이 JS 에 있나? 1번의 어느 줄이 그 답인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
