# js/syntax/11 — 스프레드와 나머지: 「같은 점 셋이 자리마다 다른 일을 한다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `[...x]` 와 `{ ...x }` 는 글자가 같고 결과 모양도 비슷한데 **서로 다른 연산을 부른다** —
> **값만 봐서는 안 갈리고** `Proxy` 트랩과 getter 에 로그를 심어야 출력으로 나온다.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **세 자리가 정말 다른가** ② ★★★ **얕은 복사가 무엇을 만드나** ③ **어느 형태가 문법 오류인가**.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★★★ **이 주제에는 두 판이 갈린 줄이 하나 있다** — 예외 **문구**다. 종류는 같다.
> ★ **2번은 「무엇이 나오나」가 아니라 「무엇을 부르나」를 묻는다.** 로그를 먼저 적어라.
>
> **선행** — [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) · [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 세 문항(1\~3)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「터지는 것과 조용히 비는 것」을 갈라야** 답이다.
- ★★★ **2번은 트랩 이름과 순서를 그대로** 적어야 답이다.
- ★★ **3번은 「무엇을 잃었나」를 네 가지로** 대야 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 값을 세 자리에 넣으면 (예측) ★★★ 이 주제의 축

```js
// js08b-11a-three-places.js
// 점 셋(...)이 서는 자리는 셋이다 -- 배열 리터럴, 객체 리터럴, 호출 인자.
// 같은 글자가 「펼치기」이기도 하고 「모으기」이기도 하다. 무엇이 가르나.
function show(label, run) {
  try { console.log("  " + label.padEnd(40) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(40) + " -> " + e.constructor.name + ": " + e.message); }
}
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));

console.log("[1] spread -- three places, three different rules");
const arrSrc = [1, 2];
const objSrc = { a: 1, b: 2 };
show("[...arr]", () => J([...arrSrc]));
show("[0, ...arr, 3]", () => J([0, ...arrSrc, 3]));
show("[...'ab']", () => J([..."ab"]));
show("[...new Set([1, 1, 2])]", () => J([...new Set([1, 1, 2])]));
show("[...new Map([['k', 1]])]", () => J([...new Map([["k", 1]])]));
show("[...obj]", () => J([...objSrc]));
show("{ ...obj }", () => J({ ...objSrc }));
show("{ ...arr }", () => J({ ...arrSrc }));
show("{ ...'ab' }", () => J({ ..."ab" }));
show("{ ...new Set([1, 2]) }", () => J({ ...new Set([1, 2]) }));
show("{ ...7 }", () => J({ ...7 }));
show("{ ...null }", () => J({ ...null }));
show("{ ...undefined }", () => J({ ...undefined }));
show("[...null]", () => J([...null]));
show("f(...arr)", () => { function f(a, b) { return J([a, b]); } return f(...arrSrc); });
show("f(...'ab')", () => { function f(a, b) { return J([a, b]); } return f(..."ab"); });
show("f(...obj)", () => { function f(a, b) { return J([a, b]); } return f(...objSrc); });

console.log("");
console.log("[2] later wins -- object spread is just property copying in order");
show("{ ...obj, a: 9 }", () => J({ ...objSrc, a: 9 }));
show("{ a: 9, ...obj }", () => J({ a: 9, ...objSrc }));
show("{ ...{ a: 1 }, ...{ a: 2 } }", () => J({ ...{ a: 1 }, ...{ a: 2 } }));
show("{ ...obj, ...{ b: undefined } }", () => J({ ...objSrc, ...{ b: undefined } }));
show("array spread does not merge", () => J([...[1, 2], ...[2, 3]]));

console.log("");
console.log("[3] rest -- three places, always the last one");
show("function (a, ...r) with (1, 2, 3)", () => { function f(a, ...r) { return J([a, r]); } return f(1, 2, 3); });
show("const [a, ...r] = [1, 2, 3]", () => { const [a, ...r] = [1, 2, 3]; return J([a, r]); });
show("const { a, ...r } = { a: 1, b: 2 }", () => { const { a, ...r } = { a: 1, b: 2 }; return J([a, r]); });
show("rest of an array pattern is an Array", () => { const [, ...r] = [1, 2]; return Array.isArray(r); });
show("rest of an object pattern is an Object", () => { const { ...r } = { a: 1 }; return Object.prototype.toString.call(r); });
show("rest param is an Array", () => { function f(...r) { return Array.isArray(r); } return f(1); });

console.log("");
console.log("[4] which form each place accepts -- SyntaxError or not");
const FORMS = [
  ["[...a, b]  spread not last", "var a = [], b = 1; var x = [...a, b];"],
  ["[a, ...b] = arr  rest not last", "var arr = [1, 2]; var a, b, c; [a, ...b, c] = arr;"],
  ["function f(...r, b)", "function f(...r, b) {}"],
  ["function f(...r = [])", "function f(...r = []) {}"],
  ["const [...r = []] = []", "const [...r = []] = [];"],
  ["const { ...r, a } = {}", "const { ...r, a } = {};"],
  ["const { a, ...r } = {}", "const { a, ...r } = {};"],
  ["const [...r,] = []  trailing comma", "const [...r,] = [];"],
  ["[...a,]  spread then comma", "var a = []; var x = [...a,];"],
  ["f(...a,)  call trailing comma", "function f() {} var a = []; f(...a,);"],
  ["const { ...{ a } } = {}", "const { ...{ a } } = {};"],
  ["const [...[a, b]] = [1, 2]", "const [...[a, b]] = [1, 2];"],
];
function compile(src, strict) {
  try { new Function((strict ? '"use strict";\n' : "") + src); return "ok"; }
  catch (e) { return e.constructor.name + ": " + e.message; }
}
console.log("  " + "form".padEnd(40) + "sloppy".padEnd(8) + "strict");
let differ = 0;
for (const [label, src] of FORMS) {
  const a = compile(src, false), b = compile(src, true);
  if (a !== b) differ += 1;
  console.log("  " + label.padEnd(40) + (a === "ok" ? "ok" : "ERR").padEnd(8) + (b === "ok" ? "ok" : "ERR") +
              (a === b ? "" : "   <-- DIFFERENT"));
}
console.log("  " + "settings-dependent cells".padEnd(40) + differ + " of " + FORMS.length);
console.log("");
console.log("[5] the messages behind the ERR cells");
for (const [label, src] of FORMS) {
  const a = compile(src, false);
  if (a !== "ok") console.log("  " + label.padEnd(40) + a);
}
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 **터지는 줄은 몇 개**이고 **조용히 빈 결과를 내는 줄은 몇 개**인가?
- ★★★ `{ ...null }` 과 `[...null]` 이 갈린다. **무엇이 가른 것인가**?
- ★★★ `{ ...new Set([1, 2]) }` 은 무엇인가? 「이터러블이니까 될 것」이라는 기대가 **왜 틀리는가**?
- ★★ `[2]` 에서 `{ ...obj, a: 9 }` 와 `{ a: 9, ...obj }` 가 갈린다. 규칙을 한 줄로 적으면?
- ★★ `[3]` 의 모으는 자리 셋은 **각각 무슨 타입**을 만드는가?
- ★★★ `[4]` 에서 `[...a, b]` 는 되는데 `[a, ...b, c] = arr` 은 안 된다. **같은 대괄호인데** 왜 갈리는가?
- ★★★ `[4]` 에서 **설정에 달린 칸은 몇 개**인가? 08\~10번과 견주면 무엇이 보이는가?

### 2. 로그를 심으면 무엇이 보이나 (예측) ★★★

```js
// js08b-11b-traps.js
// 점 셋이 실제로 무엇을 부르나 -- Proxy 트랩에 로그를 심어 추상 연산을 받아 본다.
// 배열 스프레드는 이터레이터를, 객체 스프레드는 프로퍼티 복사를 쓴다. 같은 글자인데 경로가 다르다.
const log = [];
function reset() { log.length = 0; }
function dump(label) { console.log("  " + label.padEnd(30) + JSON.stringify(log)); }

function traced(target) {
  return new Proxy(target, {
    ownKeys(t) { log.push("ownKeys"); return Reflect.ownKeys(t); },
    getOwnPropertyDescriptor(t, k) { log.push("getOwnPropertyDescriptor " + String(k)); return Reflect.getOwnPropertyDescriptor(t, k); },
    get(t, k, r) { log.push("get " + String(k)); return Reflect.get(t, k, r); },
    has(t, k) { log.push("has " + String(k)); return Reflect.has(t, k); },
    getPrototypeOf(t) { log.push("getPrototypeOf"); return Reflect.getPrototypeOf(t); },
  });
}

console.log("[1] object spread -- ownKeys, then a descriptor and a get per key");
reset(); void { ...traced({ a: 1, b: 2 }) }; dump("{ ...traced(2 keys) }");
reset(); void { ...traced({}) }; dump("{ ...traced(0 keys) }");
reset(); void Object.assign({}, traced({ a: 1 })); dump("Object.assign({}, traced)");
reset(); { const { ...r } = traced({ a: 1 }); } dump("const { ...r } = traced");
reset(); { const { a, ...r } = traced({ a: 1, b: 2 }); } dump("const { a, ...r } = traced");

console.log("");
console.log("[2] array spread -- the iterator protocol, and nothing else");
function tracedIterable(values) {
  return {
    get [Symbol.iterator]() {
      log.push("read Symbol.iterator");
      return function () {
        let i = 0;
        return {
          next() { log.push("next " + i); return i < values.length ? { value: values[i++], done: false } : { value: undefined, done: true }; },
          return() { log.push("return"); return { done: true }; },
        };
      };
    },
  };
}
reset(); void [...tracedIterable([1, 2])]; dump("[...tracedIterable(2)]");
reset(); void [0, ...tracedIterable([1]), 9]; dump("[0, ...it(1), 9]");
reset(); (function f() {})(...tracedIterable([1, 2])); dump("f(...it(2))");
reset(); void { ...tracedIterable([1, 2]) }; dump("{ ...it(2) }  object place");
reset(); void new Set([...tracedIterable([1])]); dump("new Set([...it(1)])");

console.log("");
console.log("[3] a getter is called once and its value is stored -- the getter itself is not copied");
let calls = 0;
const withGetter = { get live() { calls += 1; return calls; } };
const copy = { ...withGetter };
console.log("  " + "source read twice".padEnd(30) + JSON.stringify([withGetter.live, withGetter.live]));
console.log("  " + "copy read twice".padEnd(30) + JSON.stringify([copy.live, copy.live]));
console.log("  " + "descriptor in the source".padEnd(30) + JSON.stringify(Object.keys(Object.getOwnPropertyDescriptor(withGetter, "live"))));
console.log("  " + "descriptor in the copy".padEnd(30) + JSON.stringify(Object.getOwnPropertyDescriptor(copy, "live")));
console.log("  " + "getter calls so far".padEnd(30) + calls);

console.log("");
console.log("[4] a setter in the target is skipped by spread but not by assign");
const sink = {};
let setterCalls = 0;
Object.defineProperty(sink, "k", { set(v) { setterCalls += 1; }, get() { return "from getter"; }, enumerable: true, configurable: true });
const spreadInto = { ...sink, k: 1 };
console.log("  " + "{ ...sink, k: 1 } -> k is".padEnd(34) + JSON.stringify(spreadInto.k));
console.log("  " + "setter calls after spread".padEnd(34) + setterCalls);
Object.assign(sink, { k: 1 });
console.log("  " + "setter calls after Object.assign".padEnd(34) + setterCalls);
console.log("  " + "spread target descriptor".padEnd(34) + JSON.stringify(Object.keys(Object.getOwnPropertyDescriptor(spreadInto, "k"))));
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 객체 자리는 **어떤 트랩을 몇 번** 부르는가? **디스크립터를 왜 먼저 보는가**?
- ★★★ `[2]` 의 마지막에서 두 번째 줄(`{ ...it(2) }`)의 로그가 한 줄뿐이다. **무엇을 증명하는가**?
- ★★ 호출 자리(`f(...it(2))`)의 로그는 배열 자리와 같은가 다른가?
- ★★★ `[3]` 에서 원본과 복사본을 두 번씩 읽으면 각각 무엇이 나오는가? **디스크립터는 어떻게 바뀌었는가**?
- ★★★ `[4]` 에서 대상에 setter 가 있으면 스프레드와 `Object.assign` 이 갈린다. **몇 번씩 불렸는가**?

### 3. 복사본을 만들어 원본을 보면 (예측) ★★

```js
// js08b-11c-shallow.js
// 얕은 복사라는 사실이 중첩 구조에서 무엇을 만드나 -- 그리고 무엇이 복사에서 빠지나.
const J = JSON.stringify;
function row(k, v) { console.log("  " + k.padEnd(40) + v); }

console.log("[1] one level deep is copied, the rest is shared");
const original = { n: 1, inner: { deep: 1 }, list: [1, 2] };
const copy = { ...original };
copy.n = 99;
copy.inner.deep = 99;
copy.list.push(3);
row("original after editing the copy", J(original));
row("copy", J(copy));
row("copy.inner === original.inner", String(copy.inner === original.inner));
row("copy.list === original.list", String(copy.list === original.list));
const arrOrig = [{ deep: 1 }];
const arrCopy = [...arrOrig];
arrCopy[0].deep = 99;
row("array spread, same story", J(arrOrig));
row("arrCopy[0] === arrOrig[0]", String(arrCopy[0] === arrOrig[0]));

console.log("");
console.log("[2] what a spread copy loses");
class Point { constructor(x) { this.x = x; } get double() { return this.x * 2; } kind() { return "Point"; } }
const p = new Point(3);
p.own = 1;
Object.defineProperty(p, "hidden", { value: "h", enumerable: false });
const sym = Symbol("s");
p[sym] = "symbol value";
const pc = { ...p };
row("instance own keys", J(Object.keys(p)));
row("copy own keys", J(Object.keys(pc)));
row("p instanceof Point", String(p instanceof Point));
row("pc instanceof Point", String(pc instanceof Point));
row("p.double (prototype getter)", String(p.double));
row("pc.double", String(pc.double));
row("typeof pc.kind", typeof pc.kind);
row("non-enumerable 'hidden' copied?", String(Object.prototype.hasOwnProperty.call(pc, "hidden")));
row("symbol key copied?", String(Object.prototype.hasOwnProperty.call(pc, sym)));
row("prototype of the copy", String(Object.getPrototypeOf(pc) === Object.prototype));

console.log("");
console.log("[3] arrays -- spread reads the iterator, so holes and extra keys change shape");
const sparse = [1, , 3];
sparse.tag = "extra";
row("sparse array", J(sparse));
row("1 in sparse (hole present?)", String(1 in sparse));
const sc = [...sparse];
row("[...sparse]", J(sc));
row("1 in [...sparse]", String(1 in sc));
row("[...sparse].length", String(sc.length));
row("extra key survived?", String(Object.prototype.hasOwnProperty.call(sc, "tag")));
row("Array.from(sparse)", J(Array.from(sparse)));
row("sparse.slice() keeps the hole", String(1 in sparse.slice()));
row("{ ...sparse } (object place)", J({ ...sparse }));

console.log("");
console.log("[4] merging -- what each form does with the same two objects");
const base = { a: 1, inner: { deep: 1 } };
const patch = { b: 2, inner: { deep: 2 } };
row("{ ...base, ...patch }", J({ ...base, ...patch }));
row("Object.assign({}, base, patch)", J(Object.assign({}, base, patch)));
row("nested object is replaced, not merged", J({ ...base, ...patch }.inner));
const listBase = [1, 2], listPatch = [3];
row("[...listBase, ...listPatch]", J([...listBase, ...listPatch]));
row("[listBase, listPatch] (no spread)", J([listBase, listPatch]));
row("[...listBase].concat is the same", J([...listBase].concat(listPatch)));
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ `[2]` 에서 클래스 인스턴스를 스프레드하면 **무엇을 잃는가**? 네 가지를 대면?
- ★★ **심볼 키는 오는가**? 복사본의 프로토타입은 무엇인가?
- ★★★ `[3]` 에서 `1 in sparse` 와 `1 in [...sparse]` 가 갈린다. **무엇이 일어난 것인가**?
- ★★ 같은 희소 배열을 **객체 자리**에 넣으면 결과가 어떻게 다른가?
- ★★ `[4]` 에서 중첩 객체는 병합되는가 갈아치워지는가?

### 4. 세 자리는 무엇을 보고 고르나 (경계) ★★★

- 배열 자리·호출 자리·객체 자리가 각각 **요구하는 것**을 한 낱말로 대면?
- ★★★ **유사 배열**을 펴야 하면 무엇을 쓰는가? 스프레드는 왜 안 되는가?
- ★★ 09번의 `apply` 와 스프레드는 **서로 못 덮는 자리를 하나씩** 갖는다. 각각 무엇인가?
- ★ `Array.from` 은 왜 둘 다 되는가?

### 5. 스프레드와 `Object.assign` 은 무엇이 다른가 (왜) ★★

- 결과가 거의 같은데 **한 자리에서 갈린다.** 어디인가?
- ★★ 「정의」와 「대입」이라는 말로 그 차이를 설명하면?
- ★ 어느 주제가 `Object.assign` 의 정본인가?

### 6. 나머지는 왜 마지막이어야 하나 (왜) ★★

- 세 자리(매개변수·배열 패턴·객체 패턴)에서 나머지가 앞에 오면 각각 무엇이 나는가?
- ★★★ **펴는 쪽은 자리가 자유로운데** 모으는 쪽만 마지막인 이유는?
- ★ 나머지에 기본값을 달면? 꼬리 쉼표를 붙이면?

### 7. 어디서 조용히 틀리나 (경계) ★★★

- 이 주제에서 **에러 없이 틀리는 자리** 넷을 대면?
- ★★★ 그 중 **09번에서 본 것과 같은 모양**인 것은 무엇인가?
- ★★ 비싼 getter 가 있는 객체에 `{ ...obj }` 를 쓰면?

### 8. 보장인가 엔진 사정인가 (연결) ★★★

- 이 주제에서 **두 판이 갈린 자리는 몇 개**였고 무엇이었는가?
- ★★★ 그 차이는 **명세인가 V8 의 사정인가**? 어떻게 아는가?
- ★★ 브라우저에 같은 줄을 던졌을 때 **호스트가 정하는 칸은 몇 개**였는가? 문구까지 같은 이유는?
- ★ 이 주제에서 **부적용인 창**은 무엇인가? 성능은 왜 여기 없는가?

### 9. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **이터러블 프로토콜** · **`Object.assign` API** · **깊은 복사** · **구조 분해 패턴** · **열거 순서** 는 각각 어느 주제가 정본인가?
- ★★★ 10번에서 **무엇을 이어받는가**? 한 문장으로.
- ★★ Go 의 `xs...` 와 이 주제의 스프레드는 무엇이 닮고 무엇이 다른가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
