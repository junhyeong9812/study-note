# js/syntax/14 — 프로퍼티 디스크립터와 동결: 「막힌 것은 값이 아니라 플래그에 적혀 있다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자이고, 그 격자의 눈금은 `getOwnPropertyDescriptor` 덤프다.**
> 「무엇이 막혀 있나」는 **값으로는 원리상 안 보인다** — 막힌 `o.a` 도 안 막힌 `o.a` 도 똑같이 `1` 이다.
> **답을 적을 때 값이 아니라 세 플래그를 적어라.**
> ★★ **이 주제의 인출 축은 넷**이다 —
> ① **이 프로퍼티는 어떤 허가증을 갖고 있나** ② ★★★ **무엇이 막히고 무엇이 남나**
> ③ **동결은 어디서 멈추나** ④ **엄격과 비엄격이 어디서 갈리나**.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★★★ **2번과 3번 소스는 통째로 `"use strict"` 아래에서 돌렸다.**
> 비엄격이면 막힌 칸이 `OK` 로 보여 격자를 읽을 수가 없기 때문이다.
> 1번은 덤프라 모드와 무관하고, 4번이 **그 모드 차이 자체**를 따로 잰다.
> ★★★ **이 주제에는 두 판이 갈린 줄이 딱 하나 있다.** 9번이 그것을 묻는다 — **어느 줄인지 찾아 두어라.**
>
> **선행** — [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [12 — 옵셔널 체이닝·널 병합·논리 할당](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) · [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 네 문항(1\~4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「값」이 아니라 「`w`/`e`/`c` 세 글자」를 적어야** 답이다. 값만 적으면 하나도 못 맞힌 것이다.
- ★★★ **2번과 4번은 집계 줄의 숫자를 먼저** 적어라 — 「몇 칸 중 몇 칸」이다. 스크립트가 직접 세어 마지막 줄에 찍는다.
- ★★ **3번은 격자·술어·얕음·접근자·배열 다섯 덩어리**다. 덩어리마다 따로 답을 적어라.
- ★★★ **5\~8번은 예측형이 아니지만 이 주제의 값이 거기 몰려 있다.** 특히 6번은 **한 번 틀리면 계속 틀리는 자리**다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가, 아니면 이 판의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 어디서 온 프로퍼티인가 (예측) ★★★ 이 주제의 축

```js
// js12b-14a-dump.js
// getOwnPropertyDescriptor 덤프가 이 주제의 본체다 -- 표로 찍는다.
const dump = (label, obj, key) => {
  const d = Object.getOwnPropertyDescriptor(obj, key);
  if (!d) { console.log(label.padEnd(38) + "(no such property)"); return; }
  const kind = ("get" in d) ? "accessor" : "data";
  const tag = (v) => {
    if (typeof v === "function") return "[fn]";
    if (typeof v === "string") return '"' + v + '"';
    if (typeof v === "object" && v !== null) return Array.isArray(v) ? "[]" : "{}";
    return String(v);
  };
  const val = kind === "data"
    ? tag(d.value)
    : ("get=" + (d.get ? "fn" : "undefined") + " set=" + (d.set ? "fn" : "undefined"));
  console.log(label.padEnd(38) + kind.padEnd(10) + String(val).padEnd(22) +
    "w=" + String(kind === "data" ? d.writable : "-").padEnd(7) +
    "e=" + String(d.enumerable).padEnd(7) + "c=" + d.configurable);
};

console.log("[1] where did the property come from?");
console.log("source".padEnd(38) + "kind".padEnd(10) + "value".padEnd(22) + "writable enumerable configurable");
dump("literal  { a: 1 }", { a: 1 }, "a");
dump("assignment  o.a = 1", (() => { const o = {}; o.a = 1; return o; })(), "a");
dump("defineProperty { value: 1 }", Object.defineProperty({}, "a", { value: 1 }), "a");
dump("defineProperty {} (no value)", Object.defineProperty({}, "a", {}), "a");
dump("literal getter  { get g() {} }", { get g() { return 1; } }, "g");
dump("defineProperty { get }", Object.defineProperty({}, "g", { get() { return 1; } }), "g");
dump("Object.create 2nd arg", Object.create(null, { a: { value: 1 } }), "a");
dump("class prototype method", (class C { m() {} }).prototype, "m");
dump("array element  [7]", [7], "0");
dump("array length   [7]", [7], "length");
dump("function .prototype", function f() {}, "prototype");
dump("function .name", function f() {}, "name");
dump("function .length", function f(a, b) {}, "length");
dump("Object.prototype.toString", Object.prototype, "toString");
dump("globalThis.NaN", globalThis, "NaN");

console.log("");
console.log("[2] the same property after each sealing call");
const mk = () => ({ a: 1, get g() { return "G"; } });
console.log("state".padEnd(38) + "kind".padEnd(10) + "value".padEnd(22) + "writable enumerable configurable");
dump("plain                      .a", mk(), "a");
dump("preventExtensions          .a", Object.preventExtensions(mk()), "a");
dump("seal                       .a", Object.seal(mk()), "a");
dump("freeze                     .a", Object.freeze(mk()), "a");
dump("plain                      .g", mk(), "g");
dump("seal                       .g", Object.seal(mk()), "g");
dump("freeze                     .g", Object.freeze(mk()), "g");

console.log("");
console.log("[3] defineProperty defaults are the opposite of the literal's");
const lit = Object.getOwnPropertyDescriptor({ a: 1 }, "a");
const def = Object.getOwnPropertyDescriptor(Object.defineProperty({}, "a", { value: 1 }), "a");
console.log("literal        " + JSON.stringify(lit));
console.log("defineProperty " + JSON.stringify(def));
console.log("all three flags flipped? " +
  (lit.writable !== def.writable && lit.enumerable !== def.enumerable && lit.configurable !== def.configurable));
console.log("is the defineProperty one visible to Object.keys / JSON? " +
  JSON.stringify(Object.keys(Object.defineProperty({}, "a", { value: 1 }))) + " " +
  JSON.stringify(Object.defineProperty({}, "a", { value: 1 })));

console.log("");
console.log("[4] defineProperty on an EXISTING property only changes what you pass");
const o = { a: 1 };
Object.defineProperty(o, "a", { enumerable: false });
console.log("after { enumerable: false } -> " + JSON.stringify(Object.getOwnPropertyDescriptor(o, "a")));
```

- ★★★ `[1]` 의 **첫 세 줄**(리터럴 · 대입 · `defineProperty`)에 `w`/`e`/`c` 를 각각 적어 보라. **몇 줄이 서로 같은가**?
- ★★★ `[3]` 의 `all three flags flipped?` 는 무엇을 찍는가? 그 바로 아래 줄의 **`Object.keys` 와 `JSON.stringify` 결과**는?
- ★★ **클래스 프로토타입 메서드**의 세 플래그는? 그 결과 `Object.keys(C.prototype)` 는 무엇이 되는가?
- ★★ **배열의 `length`** 와 **함수의 `.name`** 은 세 플래그가 어떻게 다른가? 둘 중 **대입으로 바꿀 수 있는 쪽**은?
- ★★ `[2]` 에서 세 봉인 함수가 **각각 어느 칸을 내리는가**? **`enumerable` 은 누가 건드리는가**?
- ★★ `[2]` 의 `.g` 세 줄은 왜 `w=-` 인가? `freeze` 뒤에 무엇이 바뀌었나?
- ★ `[4]` — 이미 있는 프로퍼티에 `{ enumerable: false }` 하나만 주면 나머지 두 칸은 어떻게 되는가?

### 2. 설정 불가가 된 뒤에는 무엇이 통하나 (예측) ★★★

```js
// js12b-14b-configurable.js
// configurable: false 가 된 뒤 무엇이 되고 무엇이 안 되나 -- 전수 격자.
// 이 블록은 전부 엄격 모드다(defineProperty/delete 자체가 모드와 무관하게 던지는 자리를 본다).
"use strict";

const starts = [
  ["w=true  c=false", { value: 1, writable: true, enumerable: true, configurable: false }],
  ["w=false c=false", { value: 1, writable: false, enumerable: true, configurable: false }],
  ["w=true  c=true ", { value: 1, writable: true, enumerable: true, configurable: true }],
];
const ops = [
  ["defineProperty value: 2", (o) => Object.defineProperty(o, "p", { value: 2 })],
  ["defineProperty value: 1 (same)", (o) => Object.defineProperty(o, "p", { value: 1 })],
  ["defineProperty writable: true", (o) => Object.defineProperty(o, "p", { writable: true })],
  ["defineProperty writable: false", (o) => Object.defineProperty(o, "p", { writable: false })],
  ["defineProperty enumerable: false", (o) => Object.defineProperty(o, "p", { enumerable: false })],
  ["defineProperty configurable: true", (o) => Object.defineProperty(o, "p", { configurable: true })],
  ["defineProperty get() {} (to accessor)", (o) => Object.defineProperty(o, "p", { get() { return 9; } })],
  ["assignment  o.p = 2", (o) => { o.p = 2; }],
  ["delete o.p", (o) => { delete o.p; }],
];

console.log("[1] grid -- strict mode throughout");
console.log("start".padEnd(18) + "operation".padEnd(40) + "result");
let blocked = 0, total = 0;
for (const [label, desc] of starts) {
  for (const [opName, op] of ops) {
    const o = Object.defineProperty({}, "p", { ...desc });
    total += 1;
    let out;
    try {
      op(o);
      const d = Object.getOwnPropertyDescriptor(o, "p");
      out = "OK  now " + (d
        ? (("get" in d) ? "accessor" : "value=" + d.value + " w=" + d.writable) + " e=" + d.enumerable + " c=" + d.configurable
        : "(deleted)");
    } catch (e) { blocked += 1; out = e.constructor.name + " " + e.message; }
    console.log(label.padEnd(18) + opName.padEnd(40) + out);
  }
  console.log("");
}
console.log("blocked cells " + blocked + " / " + total);

console.log("");
console.log("[2] the one-way door -- writable true->false is allowed even when configurable is false");
const o = Object.defineProperty({}, "p", { value: 1, writable: true, configurable: false });
Object.defineProperty(o, "p", { writable: false });
console.log("true -> false   " + JSON.stringify(Object.getOwnPropertyDescriptor(o, "p")));
try { Object.defineProperty(o, "p", { writable: true }); console.log("false -> true   OK"); }
catch (e) { console.log("false -> true   " + e.constructor.name + " " + e.message); }
```

- ★★★ 마지막 집계 줄의 **`blocked … / …`** 두 숫자를 적어 보라.
- ★★★ 첫 덩어리(`w=true c=false`)에서 **`defineProperty value: 2` 는 통과하는가 막히는가**? 그 답이 왜 놀라운가?
- ★★★ `[2]` 의 두 줄 — `writable` 을 **어느 방향으로는 바꿀 수 있고 어느 방향으로는 못 바꾸는가**?
- ★★ `w=false c=false` 덩어리에서 **`value: 1 (same)` 만 통과하는 이유**는?
- ★★ `assignment o.p = 2` 와 `delete o.p` 는 각각 **어느 플래그 하나에만 달려 있는가**?
- ★ `[2]` 의 첫 줄 결과에 `"enumerable":false` 가 찍힌다. 그 `false` 는 **어디서 왔는가**?

### 3. 세 봉인 함수를 나란히 돌리면 (예측) ★★★

```js
// js12b-14c-freeze.js
// freeze / seal / preventExtensions 셋의 차이 + 얕음 + isFrozen 의 경계.
// 이 블록은 전부 엄격 모드다 -- 실패가 조용하지 않고 TypeError 로 나오게 해서 격자를 읽는다.
"use strict";

const makers = [
  ["plain", (o) => o],
  ["preventExtensions", Object.preventExtensions],
  ["seal", Object.seal],
  ["freeze", Object.freeze],
];
const ops = [
  ["add    o.nu = 1", (o) => { o.nu = 1; }],
  ["write  o.a = 2", (o) => { o.a = 2; }],
  ["delete o.a", (o) => { delete o.a; }],
  ["reconfig defineProperty", (o) => Object.defineProperty(o, "a", { enumerable: false })],
  ["mutate o.deep.n = 2", (o) => { o.deep.n = 2; }],
  ["setPrototypeOf(o, null)", (o) => Object.setPrototypeOf(o, null)],
];

console.log("[1] grid -- strict mode throughout");
console.log("operation".padEnd(26) + makers.map(([n]) => n.padEnd(20)).join(""));
for (const [opName, op] of ops) {
  const cells = makers.map(([, mk]) => {
    const o = mk({ a: 1, deep: { n: 1 } });
    try { op(o); return "OK"; } catch (e) { return e.constructor.name; }
  });
  console.log(opName.padEnd(26) + cells.map((c) => c.padEnd(20)).join(""));
}

console.log("");
console.log("[2] the three predicates");
console.log("object".padEnd(34) + "isExtensible".padEnd(15) + "isSealed".padEnd(11) + "isFrozen");
const preds = (label, o) => console.log(label.padEnd(34) + String(Object.isExtensible(o)).padEnd(15) +
  String(Object.isSealed(o)).padEnd(11) + String(Object.isFrozen(o)));
preds("{}", {});
preds("Object.preventExtensions({})", Object.preventExtensions({}));
preds("Object.seal({})", Object.seal({}));
preds("Object.freeze({})", Object.freeze({}));
preds("{ a: 1 }", { a: 1 });
preds("Object.preventExtensions({a:1})", Object.preventExtensions({ a: 1 }));
preds("Object.seal({a:1})", Object.seal({ a: 1 }));
preds("Object.freeze({a:1})", Object.freeze({ a: 1 }));
preds("preventExt + w:false,c:false prop", Object.preventExtensions(Object.defineProperty({}, "a", { value: 1 })));
preds("Object.freeze([])", Object.freeze([]));
preds("Object.freeze([1])", Object.freeze([1]));
preds("5  (primitive)", 5);
preds("'str'  (primitive)", "str");

console.log("");
console.log("[3] freeze is shallow -- the nested object is untouched");
const outer = Object.freeze({ a: 1, deep: { n: 1 }, arr: [1, 2] });
outer.deep.n = 99;
outer.arr.push(3);
console.log("after mutating through the frozen object -> " + JSON.stringify(outer));
console.log("isFrozen(outer)      " + Object.isFrozen(outer));
console.log("isFrozen(outer.deep) " + Object.isFrozen(outer.deep));

console.log("");
console.log("[4] a getter survives freeze -- the VALUE it returns can still change");
let counter = 0;
const g = Object.freeze({ get next() { counter += 1; return counter; } });
console.log("isFrozen " + Object.isFrozen(g) + "   descriptor " +
  JSON.stringify(Object.getOwnPropertyDescriptor(g, "next"), (k, v) => (typeof v === "function" ? "[fn]" : v)));
console.log("g.next reads: " + g.next + " " + g.next + " " + g.next);

console.log("");
console.log("[5] a frozen array");
const fa = Object.freeze([1, 2, 3]);
for (const [label, fn] of [["fa[0] = 9", () => { fa[0] = 9; }], ["fa.push(4)", () => fa.push(4)],
                           ["fa.length = 0", () => { fa.length = 0; }], ["fa.sort()", () => fa.sort()],
                           ["fa.toSorted()", () => fa.toSorted && fa.toSorted()]]) {
  try { const r = fn(); console.log(label.padEnd(16) + "OK  " + JSON.stringify(fa) + (r === undefined ? "" : "  returned " + JSON.stringify(r))); }
  catch (e) { console.log(label.padEnd(16) + e.constructor.name + " " + e.message); }
}
```

- ★★★ `[1]` 의 여섯 행 중 **네 칸이 전부 같은 행**은 무엇인가? 그 행이 말하는 것은?
- ★★ `setPrototypeOf` 행은 **어느 함수부터** 막히는가? 왜 거기서부터인가?
- ★★★ `[2]` 에서 **`{}` 의 `isFrozen`** 은 무엇인가? **`Object.preventExtensions({})` 의 `isFrozen`** 은?
  둘이 다르다면 그 차이를 만드는 조건은 무엇인가?
- ★★★ `[2]` 에서 **`freeze` 를 한 번도 안 불렀는데 `isFrozen` 이 `true` 인 줄**을 찾아라. 왜 그런가?
- ★★ `[2]` 의 마지막 두 줄 — **원시값**에 세 술어를 물으면 어떻게 되는가? 터지는가?
- ★★★ `[3]` — `isFrozen(outer)` 와 `isFrozen(outer.deep)` 는 각각 무엇인가? `outer.arr` 는 어떻게 되었나?
- ★★★ `[4]` — `isFrozen` 이 `true` 인데 **`g.next` 를 세 번 읽으면** 무엇이 찍히는가? 왜 그럴 수 있나?
- ★★ `[5]` 다섯 줄 중 **막히는 것은 몇 줄**인가? `fa[0] = 9` 와 `fa.sort()` 의 **문구가 같은 이유**는?

### 4. 두 모드에서 같은 열세 줄을 돌리면 (예측) ★★★

```js
// js12b-14s-strict.js
// 「조용히 무시」 대 「TypeError」 -- 엄격 / 비엄격 전수 격자.
// ★ 엄격을 먼저 돌린다. 탐침이 전역을 만들면 이름을 탐침마다 다르게 준다.
const probes = [
  ["frozen.a = 2", "const o = Object.freeze({ a: 1 }); o.a = 2; return 'a=' + o.a;"],
  ["frozen.nu = 1 (add)", "const o = Object.freeze({ a: 1 }); o.nu = 1; return 'keys=' + JSON.stringify(Object.keys(o));"],
  ["delete frozen.a", "const o = Object.freeze({ a: 1 }); const r = delete o.a; return r + ' keys=' + JSON.stringify(Object.keys(o));"],
  ["sealed.a = 2", "const o = Object.seal({ a: 1 }); o.a = 2; return 'a=' + o.a;"],
  ["delete sealed.a", "const o = Object.seal({ a: 1 }); const r = delete o.a; return r + ' keys=' + JSON.stringify(Object.keys(o));"],
  ["preventExt.nu = 1", "const o = Object.preventExtensions({ a: 1 }); o.nu = 1; return 'keys=' + JSON.stringify(Object.keys(o));"],
  ["non-writable.a = 2", "const o = Object.defineProperty({}, 'a', { value: 1 }); o.a = 2; return 'a=' + o.a;"],
  ["getter-only.a = 2", "const o = { get a() { return 1; } }; o.a = 2; return 'a=' + o.a;"],
  ["proto has non-writable a", "const p = Object.defineProperty({}, 'a', { value: 1 }); const o = Object.create(p); o.a = 2; return 'a=' + o.a + ' own=' + Object.prototype.hasOwnProperty.call(o, 'a');"],
  ["frozen array push", "const a = Object.freeze([1]); a.push(2); return JSON.stringify(a);"],
  ["defineProperty on frozen", "const o = Object.freeze({ a: 1 }); Object.defineProperty(o, 'a', { value: 2 }); return 'a=' + o.a;"],
  ["assign to undeclared G", "G = 1; return String(G);"],
  ["frozen globalThis-ish prop", "const o = Object.freeze({ a: 1 }); Object.assign(o, { a: 2 }); return 'a=' + o.a;"],
];

function run(mode, body, gname) {
  const src = (mode === "strict" ? '"use strict";\n' : "") + body.replace(/\bG\b/g, gname);
  let out;
  try { out = "OK " + new Function(src)(); }
  catch (e) { out = e.constructor.name + " " + e.message; }
  return out.split(gname).join("<G>");
}

// ★ 엄격 먼저.
const strictOut = probes.map(([, b], i) => run("strict", b, "js12b14StrictG" + i));
const sloppyOut = probes.map(([, b], i) => run("sloppy", b, "js12b14SloppyG" + i));

console.log("[1] strict-first grid");
let split = 0;
probes.forEach(([label], i) => {
  const same = strictOut[i] === sloppyOut[i];
  if (!same) split += 1;
  console.log(label.padEnd(28) + (same ? "SAME  " : "SPLIT ") + "strict: " + strictOut[i]);
  console.log("".padEnd(28) + "      " + "sloppy: " + sloppyOut[i]);
});
console.log("");
console.log("mode-dependent cells " + split + " / " + probes.length);

console.log("");
console.log("[2] leftovers on globalThis");
const leaked = Object.getOwnPropertyNames(globalThis).filter((k) => k.startsWith("js12b14")).sort();
console.log("globals starting with js12b14 -> " + JSON.stringify(leaked));
console.log("any js12b14StrictG* leaked?    -> " + leaked.some((k) => k.startsWith("js12b14StrictG")));
```

- ★★★ 집계 줄의 **`mode-dependent cells … / …`** 두 숫자를 적어 보라.
- ★★★ 갈린 칸들의 **비엄격 쪽 답이 전부 같은 모양**이다. 그 모양을 한 문장으로 적어 보라.
- ★★★ **`SAME` 인 네 칸이 두 종류로 갈린다.** 어느 한 칸만 다른 이유로 `SAME` 인가?
- ★★ `delete frozen.a` 의 **비엄격 반환값**은 무엇인가? 그것이 12번의 어느 결론과 같은가?
- ★★ `proto has non-writable a` 의 비엄격 답에 `own=false` 가 붙는다. 무슨 뜻인가?
- ★★★ `[2]` 에서 **전역에 남은 이름은 몇 개이고 어느 탐침의 것**인가? **`Strict` 쪽은 샜는가**?
- ★ 이 스크립트가 **엄격을 먼저 돌린 이유**를 한 문장으로.

### 5. 세 플래그는 각각 무엇을 지키는가 (경계) ★★★

- ★★★ `writable`·`enumerable`·`configurable` 이 **각각 어느 연산**을 정하는가? 셋을 한 줄씩.
- ★★★ **「읽기 전용」과 「고정」은 다른 말**이다. 함수의 `.name` 과 배열의 `length` 중 **어느 쪽이 어느 쪽**인가?
- ★★ **접근자 프로퍼티에 없는 칸**은 무엇인가? 그 사실이 `freeze` 에서 무엇을 만드는가?
- ★ 디스크립터를 **꺼내서 고치면** 원래 프로퍼티가 바뀌는가?

### 6. `isFrozen` 은 언제 `true` 라고 답하는가 (왜) ★★★

- ★★★ 세 술어의 조건을 **하나씩 포함 관계로** 적어 보라. `isSealed` 와 `isFrozen` 은 무엇이 다른가?
- ★★★ **빈 객체에서 그 조건이 특별해지는 이유**는 무엇인가?
- ★★ `isFrozen` 이 `true` 라는 것이 **「누가 `freeze` 를 불렀다」는 뜻인가**?
- ★ 그 반대 방향은? **`freeze` 를 부른 객체 안쪽에 대고** `isFrozen` 을 물으면?

### 7. 동결은 정확히 어디서 멈추는가 (경계) ★★★

- ★★★ 「`Object.freeze` 했으니 안 변한다」가 **깨지는 자리 셋**을 대면?
- ★★★ `freeze` 가 실제로 **하는 일**을 플래그 수준에서 한 줄로 적어 보라. 그 한 줄에서 **접근자가 빠져나가는 이유**가 나오는가?
- ★★ `seal` 이 **보장하는 것**과 **보장하지 않는 것**을 각각 한 줄로.
- ★ `preventExtensions` 하나만 불렀을 때 **같이 막히는 다른 연산**은 무엇인가?

### 8. 왜 엄격 모드라야 보이는가 (왜) ★★★

- ★★★ 비엄격에서 막힌 쓰기는 **무엇을 남기는가** — 예외? 경고? 반환값? 로그?
- ★★★ 그래서 이 주제에서 **④ 예외 창이 닫히는 자리**가 생긴다. 같은 질문을 **어떤 창으로 바꿔 물었는가**?
  그리고 **바꾼 창이 못 보는 것**은 무엇인가?
- ★★ **모드와 무관하게 던지는 세 가지**는 무엇이고, 그것들의 공통점은?
- ★ 실무에서 **조용한 실패를 발견하는 방법** 셋을 대면?

### 9. 두 판이 갈린 한 줄 (경계) ★★

- ★★★ 이 배치 **19블록 중 갈린 것은 몇 개**이고, 그것은 **어느 파일의 어느 줄**인가?
- ★★★ node18 쪽 줄의 `OK` 를 **「그 연산이 통과했다」로 읽으면 안 되는 이유**는? 소스의 어느 표현 때문인가?
- ★★ 갈린 것은 **동결의 규칙인가, 다른 무엇인가**?
- ★ 이 줄을 근거로 쓸 때 **node20 쪽과 node18 쪽이 각각 무엇의 근거**가 되는가?

### 10. 보장인가 엔진 사정인가 판인가 (연결) ★★★

- ★★★ 디스크립터 기본값·격자의 허용/거부·세 술어의 정의 중 **명세가 아닌 것**이 있는가?
- ★★★ **예외의 종류와 문구** 중 어느 쪽이 명세의 몫인가? `#<Object>` 는 어느 쪽인가?
- ★★ 브라우저에 같은 줄을 던졌을 때 **호스트가 정하는 칸은 몇 개**였는가?
- ★★★ ★ **「예전엔 구현 나름이라던 것이 명세로 못 박힌」 자리**가 이 주제에 있다. 무엇이고 **어느 판**이었나?
- ★ 이 주제에서 **부적용인 창** 둘은 무엇이고, 「안 쟀다」와 어떻게 다른가?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **어느 문법이 어떤 디스크립터를 만드나** · **조회가 체인을 타는 경로** · **엄격 모드 규칙 전부** ·
  **프록시 불변식** · **깊은 동결** 은 각각 어느 주제가 정본인가?
- ★★★ 13번이 **어디까지** 갔고 이 주제는 **어디서부터**인가? 12번과의 경계는?
- ★★ 파이썬의 **데이터 디스크립터**와 JS 의 **프로퍼티 디스크립터**는 이름이 같은데 무엇이 다른가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
