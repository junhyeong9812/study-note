# js/syntax/46 — `Reflect`: 「트랩 13개와 이름이 1:1 로 맞는 함수 13개 — 던지던 자리에서 `false` 를 돌려주고, 원시값을 감싸지 않고, `this` 로 누구를 볼지 `receiver` 로 고른다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자 둘이다** — ① **대응 표** — `Reflect` 의 함수 **13개**를 각각 「트랩 이름 13개를 **손으로 적은** handler」의 Proxy 에 불러 **어느 트랩이 불렸나**를 찍고, 「**같은 이름의 트랩 하나만 불린 함수 N / 13**」을 스크립트가 센다(동작 (1)). ② **`Object`/연산자 대 `Reflect` 격자 19행** — 「**한쪽만 던진 행 N / 19**」·「**둘 다 돌려줬는데 값이 다른 행 N / 19**」(동작 (2)).
> ★★ 보조로 **① 로그 심기**(`receiver` — getter 가 `this` 로 누구를 보나 · `set` 을 넘기면 어느 트랩이 더 불리나 — 동작 (3))를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Reflection · The Reflect Object](https://tc39.es/ecma262/multipage/reflection.html) — 「**평범한 객체** · 함수가 아니다 · `[[Construct]]`·`[[Call]]` 이 없다」 · `Reflect.apply` 는 `IsCallable` 이 거짓이면 `TypeError`, 인자 목록은 **`CreateListFromArrayLike(args)`**(빼면 `undefined` 라 던진다) · `Reflect.construct(target, args [, newTarget])` · 나머지 11개는 **대상이 객체가 아니면 `TypeError`** 로 시작해 해당 내부 메서드를 그대로 부른다
> - [ECMA-262 — Proxy Object Internal Methods](https://tc39.es/ecma262/multipage/ordinary-and-exotic-objects-behaviours.html) — 트랩이 불리는 내부 메서드 13개(45번 머리말)
> - ★ **`Reflect` 는 ES2015 본문**이다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 v20.19.6 이다. 하네스 소스는 [44번](../44-dynamic-import-top-level-await-and-import-attributes/2-summary.md) 머리말에 있다.
> ★★★ **이 주제의 탐침 셋은 node 18 · node 20 · Chrome 151 에서 한 글자도 같았다**(세 판 대조기 · 아래 집계 줄) — 블록은 node 20 판 하나씩만 싣는다.
> ★★ **탐침 파일 `js44b-46b-object-vs-reflect.js` 는 엄격 모드다** — 대입·`delete` 행이 비엄격이면 조용히 지나가 「같다」로 셀 것이기 때문이다(14번 동작 (4)).
> ★★★ **성능은 재지 않았다.**
>
> **버전** — `Reflect` 13개 함수 전부 **ES2015** · 세 판 다 있다(판별 블록).
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 대응 표 13행 「`13 / 13`」(동작 (1)) · `Object` 대 `Reflect` 19행 「`only one side threw`」·「`both returned, different values`」(동작 (2)) |
> | ★★ **① 로그 심기** | getter 의 `this` · 쓰기가 떨어진 객체 · `set` 트랩을 넘겼을 때 **더 불린 트랩**(동작 (3)) |
> | ★ **45번 격자의 한 줄을 다시 쓴다** | `Reflect` 로 넘기는 트랩 24칸 — 「**맨 대상과 다른 칸 `0 / 24`**」(45번 동작 (1)의 `[2]`) |
> | ★ **부적용 — ④ 예외 문구** | 격자 칸은 **예외의 이름**만 싣는다 — 이 주제의 질문은 「던지나 `false` 인가」라서 문구가 답을 바꾸지 않는다 |
> | ★ **부적용 — 판 격자** | 세 판이 같아 **갈린 칸이 없다** |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 · ★ `Object.getOwnPropertyNames(Reflect)` 의 **나열 순서**(명세가 정하지 않는다 — V8 이 정의 순서대로 준 것이다. 근거로는 **개수 13**만 쓴다) | ★★★ 두 격자의 모든 칸과 집계 줄 · 로그 값 · 예외의 **종류** |
> | ★ **재실행에서 흔들린 칸은 없다**(재대조 동일) | — |
>
> **선행** — [45 — `Proxy`](../45-proxy/2-summary.md)(직접 선행 — ★★★ **불변식 격자 24칸** · ★★ **`Reflect` 로 넘기는 트랩은 맨 대상과 `0 / 24` 다르다** · 트랩의 `false` 를 **엄격 대입이** `TypeError` 로 바꾼다) ·
> [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md)(★★ **`apply(t, null)` 은 인자 0개로 조용히 부른다** · `Reflect.apply(f, t, 'ab')` 는 `CreateListFromArrayLike called on non-object` — 거기 동작 (1). 그 편은 「`Reflect` 전체는 46번이 정본」이라고 적는다) ·
> [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) · [22 — `Symbol`](../22-symbol-and-well-known-symbols/2-summary.md)(★ **`Reflect.ownKeys` 는 심볼 키를 본다** — 거기 동작의 격자) · [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md).

```text
===== ./js44b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             yes
Google Chrome 151.0.7922.173
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             no
gc():
  node20                        typeof gc: undefined
  node20 --expose-gc            typeof gc: function
  Chrome                        typeof gc: undefined
  Chrome --js-flags=--expose-gc typeof gc: function
```

세 판 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 8 · differs 0 · node only 1`

## 한눈에 — 쉽게 말하면

**`Reflect` 는 「객체의 내부 창구 13개를 그대로 부르는 공용 전화기」다. Proxy 의 트랩 13개가 그 창구 앞에 선 대리인이라면, `Reflect` 는 대리인이 「원래대로 처리해 주세요」라고 넘길 때 쓰는 직통 번호다. 그래서 이름이 1:1 로 맞는다. 옛 창구(`Object.*`·연산자)와 달리 이 전화기는 실패해도 소리 지르지 않고(던지지 않고) `false` 라고 답하며, 번호를 잘못 누르면(객체가 아니면) 바로 끊는다(`TypeError`).**

- ★★★ **이름이 1:1 이다** — `Reflect.get` 을 부르면 `get` 트랩 **하나만** 불렸다. 13개 다(`13 / 13`).
- ★★★ **던지던 자리에서 `false`** — `Object.defineProperty` · `Object.setPrototypeOf` · 엄격 대입 · 엄격 `delete` 가 던지는 자리에서 `Reflect` 는 **`false`** 를 돌려준다.
- ★★★ **원시값을 안 감싼다** — `Object.getPrototypeOf(1)` 은 `Number.prototype`, `Reflect.getPrototypeOf(1)` 은 **`TypeError`**.
- ★★ **`receiver` 로 `this` 를 고른다** — `Reflect.get(obj, 'x', other)` 의 getter 는 `this` 로 **`other`** 를 본다. Proxy 의 트랩이 이것을 넘겨야 상속이 맞게 돈다.

```text
      연산 / Object.*                    Reflect.*                         Proxy 트랩
   ─────────────────────        ─────────────────────────        ───────────────────
   o.x                           Reflect.get(o, "x", r)     ─▶     get(t, k, r)
   o.x = v   (엄격: 실패면 throw)  Reflect.set(o, "x", v, r)  ─▶     set(t, k, v, r)    → false 를 값으로
   "x" in o                      Reflect.has(o, "x")        ─▶     has(t, k)
   delete o.x (엄격: throw)       Reflect.deleteProperty     ─▶     deleteProperty     → false 를 값으로
   Object.defineProperty (throw) Reflect.defineProperty     ─▶     defineProperty     → false 를 값으로
   Object.keys (열거·문자열만)     Reflect.ownKeys (전부)      ─▶     ownKeys
   f.apply(t, a)  (f.apply 조회)  Reflect.apply(f, t, a)     ─▶     apply
   new C(...a)                   Reflect.construct(C, a, nt) ─▶     construct
     … 13개 전부 같은 이름
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 내부 창구 13개 | 내부 메서드 `[[Get]]`·`[[Set]]`·… | 45번 |
| 창구 앞의 대리인 | Proxy 트랩 13개 | 45번 · 동작 (1) |
| 직통 번호 | `Reflect.<같은 이름>` — 내부 메서드를 **그대로** 부른다 | 동작 (1) `13 / 13` |
| 소리 지르지 않고 `false` | 실패를 **값**으로 — `defineProperty`·`set`·`deleteProperty`·`setPrototypeOf`·`preventExtensions` | 동작 (2) |
| 번호를 잘못 누르면 끊는다 | 대상이 객체가 아니면 **`TypeError`** — 원시값을 감싸지 않는다 | 동작 (2) |
| 누구 이름으로 거나 | `receiver` — getter·setter 의 `this` · 데이터 쓰기가 떨어지는 객체 | 동작 (3) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**Proxy 의 `get` 트랩에서 `target[key]` 로 넘겼더니 상속한 객체의 getter 가 엉뚱한 `this` 를 본다**」,
「**`try { Object.defineProperty(…) } catch` 대신 `if (!Reflect.defineProperty(…))`**」,
「**`hasOwnProperty`·`apply` 를 덮어쓴 객체 — `Reflect.apply` 는 안 속는다**」가 그것이다(동작 (2)·(3)).

> **`receiver`** — `Reflect.get`/`Reflect.set` 의 마지막 인자이자 `get`/`set` 트랩의 마지막 인자. getter·setter 가 `this` 로 받는 객체이고, 데이터 쓰기는 **이 객체**에 떨어진다.\
> 예: `Reflect.get({ get x() { return this.n; } }, "x", { n: 1 })` → `1`.

## 이 주제가 답하려는 질문

1. **`Reflect` 의 함수는 몇 개이고, Proxy 트랩과 정말 1:1 인가** — 불러 보면 어느 트랩이 불리나?
2. **같은 요청을 `Object`/연산자와 `Reflect` 로 하면 어디서 갈리나** — 던지나 `false` 인가, 원시값을 감싸나, 무엇을 세나?
3. **`receiver` 는 무엇을 바꾸나** — getter 의 `this` · 쓰기가 떨어지는 객체 · Proxy 트랩에서 넘길 때?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 대응 표 — 13개 × 불린 트랩

**언제 쓰나** — Proxy 트랩에서 「원래 동작」으로 넘길 함수를 고를 때 · `Reflect` 에 무엇이 있는지 셀 때.
★★ **트랩 이름 목록은 `Reflect` 에서 뽑지 않고 손으로 적었다** — 뽑으면 「1:1 이다」가 **순환 논증**이 된다. 트랩은 **넘기지 않고** 기록만 한 뒤 불변식을 지키는 고정 답을 돌려준다(넘기면 다른 트랩이 덩달아 불린다 — 동작 (3)의 `[7]`).

```js
// js44b-46a-reflect-and-traps.js
// [1] What Reflect owns. [2] Each Reflect function called on a proxy whose handler has every trap name
// (the list is written out below, not taken from Reflect) -- which traps fire. The traps do not forward;
// each returns a fixed answer that keeps the invariants of an ordinary extensible target.
// [3] Which Reflect function names are also own properties of Object.
const names = Object.getOwnPropertyNames(Reflect);
const fns = names.filter((n) => typeof Reflect[n] === "function");
console.log("[1] Object.getOwnPropertyNames(Reflect): " + names.length + " names · functions: " + fns.length);
console.log("  " + fns.join(" "));
console.log("  Reflect[Symbol.toStringTag] = " + String(Reflect[Symbol.toStringTag]) + " · typeof Reflect = " + typeof Reflect);

const trapNames = ["apply", "construct", "defineProperty", "deleteProperty", "get", "getOwnPropertyDescriptor",
  "getPrototypeOf", "has", "isExtensible", "ownKeys", "preventExtensions", "set", "setPrototypeOf"];
const answers = {
  apply: undefined, construct: {}, defineProperty: true, deleteProperty: true, get: undefined,
  getOwnPropertyDescriptor: undefined, getPrototypeOf: Function.prototype, has: false, isExtensible: true,
  ownKeys: ["prototype"], preventExtensions: false, set: true, setPrototypeOf: true,
};
let fired = [];
const handler = {};
for (const t of trapNames) handler[t] = () => { fired.push(t); return answers[t]; };
const target = class {};
const p = new Proxy(target, handler);
const calls = {
  apply: () => Reflect.apply(p, null, []),
  construct: () => Reflect.construct(p, []),
  defineProperty: () => Reflect.defineProperty(p, "x", { value: 1, configurable: true }),
  deleteProperty: () => Reflect.deleteProperty(p, "x"),
  get: () => Reflect.get(p, "x"),
  getOwnPropertyDescriptor: () => Reflect.getOwnPropertyDescriptor(p, "x"),
  getPrototypeOf: () => Reflect.getPrototypeOf(p),
  has: () => Reflect.has(p, "x"),
  isExtensible: () => Reflect.isExtensible(p),
  ownKeys: () => Reflect.ownKeys(p),
  preventExtensions: () => Reflect.preventExtensions(p),
  set: () => Reflect.set(p, "x", 1),
  setPrototypeOf: () => Reflect.setPrototypeOf(p, Function.prototype),
};
console.log("");
console.log("[2] Reflect.<name>(proxy, ...) -- the traps that fired");
let same = 0;
for (const n of fns) {
  fired = [];
  let r;
  try { calls[n](); r = fired.join(", "); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  if (fired.length === 1 && fired[0] === n) same++;
  console.log("  Reflect." + n.padEnd(26) + r);
}
console.log("  Reflect functions that fired exactly one trap, of the same name: " + same + " / " + fns.length);
console.log("  trap names without a Reflect function of that name: " + (trapNames.filter((t) => !fns.includes(t)).join(" ") || "none"));

console.log("");
console.log("[3] the same name as an own property of Object?");
console.log("  on Object too:  " + fns.filter((n) => Object.hasOwn(Object, n)).join(" "));
console.log("  Reflect only:   " + fns.filter((n) => !Object.hasOwn(Object, n)).join(" "));
```

```text
===== node20 js44b-46a-reflect-and-traps.js (exit=0) =====
[1] Object.getOwnPropertyNames(Reflect): 13 names · functions: 13
  defineProperty deleteProperty apply construct get getOwnPropertyDescriptor getPrototypeOf has isExtensible ownKeys preventExtensions set setPrototypeOf
  Reflect[Symbol.toStringTag] = Reflect · typeof Reflect = object

[2] Reflect.<name>(proxy, ...) -- the traps that fired
  Reflect.defineProperty            defineProperty
  Reflect.deleteProperty            deleteProperty
  Reflect.apply                     apply
  Reflect.construct                 construct
  Reflect.get                       get
  Reflect.getOwnPropertyDescriptor  getOwnPropertyDescriptor
  Reflect.getPrototypeOf            getPrototypeOf
  Reflect.has                       has
  Reflect.isExtensible              isExtensible
  Reflect.ownKeys                   ownKeys
  Reflect.preventExtensions         preventExtensions
  Reflect.set                       set
  Reflect.setPrototypeOf            setPrototypeOf
  Reflect functions that fired exactly one trap, of the same name: 13 / 13
  trap names without a Reflect function of that name: none

[3] the same name as an own property of Object?
  on Object too:  defineProperty getOwnPropertyDescriptor getPrototypeOf isExtensible preventExtensions setPrototypeOf
  Reflect only:   deleteProperty apply construct get has ownKeys set
```

- ★★★ **`[1]` — 이름 13개 · 함수 13개**, `Symbol.toStringTag` 는 `"Reflect"`(심볼 키라 `getOwnPropertyNames` 에 안 나온다 — 22번), `typeof Reflect` 는 **`object`**(함수가 아니다 — `new Reflect` 도 `Reflect()` 도 없다).
- ★★★ **`[2]` — `fired exactly one trap, of the same name: 13 / 13` · `trap names without a Reflect function …: none`.** 손으로 적은 트랩 이름 13개와 `Reflect` 의 함수 13개가 **남는 것 없이** 짝이 맞았다.
- ★★ **`[3]` — `Object` 에도 같은 이름이 있는 것은 6개**(`defineProperty` · `getOwnPropertyDescriptor` · `getPrototypeOf` · `isExtensible` · `preventExtensions` · `setPrototypeOf`), **`Reflect` 에만 있는 것 7개**(`deleteProperty` · `apply` · `construct` · `get` · `has` · `ownKeys` · `set`) — 뒤쪽 7개는 원래 **연산자**(`delete`·`()`·`new`·`.`·`in`·`=`)나 `Object.keys` 가 하던 일이다.

### (2) ★★★ `Object`/연산자 대 `Reflect` — 19행

**언제 쓰나** — 실패를 `try`/`catch` 로 받을지 반환값으로 받을지 정할 때 · 원시값이 들어올 수 있는 자리에서.

```js
// js44b-46b-object-vs-reflect.js
"use strict";
// The same request made with an Object method or an operator (left) and with Reflect (right).
// A cell is the value the call returned, or the name of the exception it threw.
// The last lines count the rows where only one side threw, and the rows where both returned but different values.
const fixed = () => Object.defineProperty({}, "x", { value: 1, writable: false, configurable: false, enumerable: true });
const sealed = () => Object.preventExtensions({ x: 1 });
const withSymbol = () => { const o = { a: 1, [Symbol("s")]: 2 }; Object.defineProperty(o, "hidden", { value: 3, enumerable: false }); return o; };
const f = function (a, b) { return a + b; };
const shadowed = Object.assign(function (a, b) { return a + b; }, { apply: () => "own apply property" });
class C { constructor(v) { this.v = v; } }
const show = (v) => {
  if (typeof v === "string") return JSON.stringify(v);
  if (v === Number.prototype) return "Number.prototype";
  if (v === Object.prototype) return "Object.prototype";
  if (Array.isArray(v)) return "[" + v.map(String).join(", ") + "]";
  if (v instanceof C) return "C { v: " + v.v + " }";
  if (v && typeof v === "object" && "writable" in v) return "descriptor { value: " + v.value + ", writable: " + v.writable + " }";
  return String(v);
};
const out = (g) => { try { return show(g()); } catch (e) { return "throws " + e.constructor.name; } };
const rows = [
  ["defineProperty -- change x's value (x fixed)", () => Object.defineProperty(fixed(), "x", { value: 2 }) && "the object", () => Reflect.defineProperty(fixed(), "x", { value: 2 })],
  ["defineProperty -- add y (not extensible)", () => Object.defineProperty(sealed(), "y", { value: 2 }) && "the object", () => Reflect.defineProperty(sealed(), "y", { value: 2 })],
  ["getOwnPropertyDescriptor('str', 'length')", () => Object.getOwnPropertyDescriptor("str", "length"), () => Reflect.getOwnPropertyDescriptor("str", "length")],
  ["getPrototypeOf(1)", () => Object.getPrototypeOf(1), () => Reflect.getPrototypeOf(1)],
  ["setPrototypeOf -- not extensible, to {}", () => Object.setPrototypeOf(sealed(), {}) && "the object", () => Reflect.setPrototypeOf(sealed(), {})],
  ["setPrototypeOf -- not extensible, to the same", () => Object.setPrototypeOf(sealed(), Object.prototype) && "the object", () => Reflect.setPrototypeOf(sealed(), Object.prototype)],
  ["preventExtensions(1)", () => Object.preventExtensions(1), () => Reflect.preventExtensions(1)],
  ["isExtensible(1)", () => Object.isExtensible(1), () => Reflect.isExtensible(1)],
  ["keys vs ownKeys -- symbol and non-enumerable key", () => Object.keys(withSymbol()), () => Reflect.ownKeys(withSymbol())],
  ["keys vs ownKeys -- on 1", () => Object.keys(1), () => Reflect.ownKeys(1)],
  ["delete o.x vs deleteProperty (x fixed)", () => delete fixed().x, () => Reflect.deleteProperty(fixed(), "x")],
  ["o.x = 2 vs set (x fixed)", () => { fixed().x = 2; return "assigned"; }, () => Reflect.set(fixed(), "x", 2)],
  ["o.x vs get", () => fixed().x, () => Reflect.get(fixed(), "x")],
  ["'x' in o vs has", () => "x" in fixed(), () => Reflect.has(fixed(), "x")],
  ["'x' in 1 vs has(1, 'x')", () => "x" in 1, () => Reflect.has(1, "x")],
  ["f.apply(null, [1, 2]) vs apply", () => f.apply(null, [1, 2]), () => Reflect.apply(f, null, [1, 2])],
  ["g.apply(...) -- g has its own apply property", () => shadowed.apply(null, [1, 2]), () => Reflect.apply(shadowed, null, [1, 2])],
  ["f.apply(null) vs apply(f, null) -- no list", () => f.apply(null), () => Reflect.apply(f, null)],
  ["new C(1) vs construct(C, [1])", () => new C(1), () => Reflect.construct(C, [1])],
];
console.log("  " + "request".padEnd(50) + "Object / operator".padEnd(42) + "Reflect");
let oneThrows = 0, bothReturn = 0;
for (const [label, left, right] of rows) {
  const l = out(left), r = out(right);
  const lt = l.startsWith("throws"), rt = r.startsWith("throws");
  let mark = "  ";
  if (lt !== rt) { oneThrows++; mark = "* "; }
  else if (!lt && l !== r) { bothReturn++; mark = "~ "; }
  console.log(mark + label.padEnd(50) + l.padEnd(42) + r);
}
console.log("");
console.log("rows where only one side threw (*): " + oneThrows + " / " + rows.length);
console.log("rows where both returned, different values (~): " + bothReturn + " / " + rows.length);
console.log("rows that differ: " + (oneThrows + bothReturn) + " / " + rows.length);
```

```text
===== node20 js44b-46b-object-vs-reflect.js (exit=0) =====
  request                                           Object / operator                         Reflect
* defineProperty -- change x's value (x fixed)      throws TypeError                          false
* defineProperty -- add y (not extensible)          throws TypeError                          false
* getOwnPropertyDescriptor('str', 'length')         descriptor { value: 3, writable: false }  throws TypeError
* getPrototypeOf(1)                                 Number.prototype                          throws TypeError
* setPrototypeOf -- not extensible, to {}           throws TypeError                          false
~ setPrototypeOf -- not extensible, to the same     "the object"                              true
* preventExtensions(1)                              1                                         throws TypeError
* isExtensible(1)                                   false                                     throws TypeError
~ keys vs ownKeys -- symbol and non-enumerable key  [a]                                       [a, hidden, Symbol(s)]
* keys vs ownKeys -- on 1                           []                                        throws TypeError
* delete o.x vs deleteProperty (x fixed)            throws TypeError                          false
* o.x = 2 vs set (x fixed)                          throws TypeError                          false
  o.x vs get                                        1                                         1
  'x' in o vs has                                   true                                      true
  'x' in 1 vs has(1, 'x')                           throws TypeError                          throws TypeError
  f.apply(null, [1, 2]) vs apply                    3                                         3
~ g.apply(...) -- g has its own apply property      "own apply property"                      3
* f.apply(null) vs apply(f, null) -- no list        NaN                                       throws TypeError
  new C(1) vs construct(C, [1])                     C { v: 1 }                                C { v: 1 }

rows where only one side threw (*): 11 / 19
rows where both returned, different values (~): 3 / 19
rows that differ: 14 / 19
```

```text
   19행이 가른 세 갈래

   ① 한쪽만 던진다 (*) — 11행
      Object/연산자가 던지고 Reflect 는 false   : defineProperty ×2 · setPrototypeOf · delete · 대입      ← 실패를 「값」으로
      Object 는 감싸서 답하고 Reflect 는 던진다  : getOwnPropertyDescriptor · getPrototypeOf · preventExtensions
                                                · isExtensible · keys(1)                             ← 원시값을 안 감싼다
      apply 는 목록 없이도 부르고 Reflect 는 던진다 : f.apply(null) → NaN  ·  Reflect.apply(f, null) → TypeError
   ② 둘 다 돌려주는데 값이 다르다 (~) — 3행
      setPrototypeOf 성공: 객체 대 true · keys 대 ownKeys: [a] 대 [a, hidden, Symbol(s)] · 덮어쓴 apply
   ③ 같다 — 5행
      o.x · 'x' in o · 'x' in 1 (둘 다 TypeError) · f.apply(null, [1, 2]) · new C(1)
```

- ★★★ **마지막 세 줄 — `only one side threw (*): 11 / 19` · `both returned, different values (~): 3 / 19` · `rows that differ: 14 / 19`.**
- ★★★ **실패를 값으로** — `defineProperty` 두 행(설정 불가 `x` 를 바꾸기 · 확장 불가에 `y` 더하기), `setPrototypeOf`(확장 불가를 `{}` 로), 엄격 `delete`, 엄격 대입 — **왼쪽 `throws TypeError`, 오른쪽 `false`.**
- ★★★ **원시값을 안 감싼다** — `Object.getOwnPropertyDescriptor('str', 'length')` 는 **감싼 뒤** `descriptor { value: 3, writable: false }` 를, `Object.getPrototypeOf(1)` 은 `Number.prototype` 을, `Object.preventExtensions(1)` 은 **`1` 그대로**, `Object.isExtensible(1)` 은 **`false`**, `Object.keys(1)` 은 **`[]`** 를 돌려줬다. `Reflect` 는 다섯 다 **`TypeError`** — 대상이 **객체여야** 한다.
- ★★ **`keys` 대 `ownKeys`** — `[a]` 대 **`[a, hidden, Symbol(s)]`**. `ownKeys` 는 `[[OwnPropertyKeys]]` 를 그대로 — **열거 불가·심볼 키까지** 준다(22번).
- ★★ **`apply` 두 행** — 함수에 **자기 `apply` 프로퍼티**가 있으면 `g.apply(…)` 는 **그것을** 부른다(`"own apply property"`), `Reflect.apply` 는 안 속는다(`3`). **목록을 빼면** `f.apply(null)` 은 인자 0개로 불러 `NaN`(09번의 「`null` 은 인자 0개」), `Reflect.apply(f, null)` 은 **`TypeError`**(`CreateListFromArrayLike(undefined)`).
- ★ **같은 5행** — 읽기 · `in` · 호출 · `new` 는 같은 내부 메서드라 같다. **`'x' in 1` 도 둘 다 `TypeError`** 다 — `in` 연산자는 원래 감싸지 않는다.
- ★ **`setPrototypeOf` 가 같은 프로토타입으로 성공하는 행** — 왼쪽은 **객체를**, 오른쪽은 **`true`** 를 돌려준다. 성공해도 **반환의 모양**이 다르다.

### (3) ★★ `receiver` — getter 의 `this`, 쓰기가 떨어지는 곳, 트랩에서 넘길 때

**언제 쓰나** — Proxy 트랩에서 `get`·`set` 을 넘길 때 · 상속 사슬 위에 Proxy 가 있을 때.

```js
// js44b-46c-receiver.js
// The receiver argument: whom a getter or setter sees as this, and where a data write lands.
const base = {
  name: "base",
  get who() { return this.name; },
  set who(v) { this.written = v; },
};
const other = { name: "other" };
console.log("[1] base.who                              " + base.who);
console.log("[2] Reflect.get(base, 'who')              " + Reflect.get(base, "who"));
console.log("[3] Reflect.get(base, 'who', other)       " + Reflect.get(base, "who", other));
console.log("[4] Reflect.set(base, 'who', 1, other)    " + Reflect.set(base, "who", 1, other) +
  " · other.written " + other.written + " · base.written " + base.written);
const plain = { x: 1 };
const into = {};
console.log("[5] Reflect.set(plain, 'x', 2, into)      " + Reflect.set(plain, "x", 2, into) +
  " · plain.x " + plain.x + " · into.x " + into.x + " · own x in into " + Object.hasOwn(into, "x"));

// [6] Two proxies over the same target with a getter, used as the prototype of an object named "child".
// The first get trap reads target[key]; the second hands on the receiver with Reflect.get(target, key, receiver).
const target = { name: "target", get who() { return this.name; } };
const readsTarget = new Proxy(target, { get(t, k) { return t[k]; } });
const passesReceiver = new Proxy(target, { get(t, k, r) { return Reflect.get(t, k, r); } });
const child1 = Object.create(readsTarget); child1.name = "child";
const child2 = Object.create(passesReceiver); child2.name = "child";
console.log("[6] child.who through get(t, k) { return t[k] }                     " + child1.who);
console.log("    child.who through get(t, k, r) { return Reflect.get(t, k, r) }  " + child2.who);

// [7] A set trap that forwards with Reflect.set(t, k, v, r), and two more traps that only log. p.x = 1 -- which traps fire?
const fired = [];
const p = new Proxy({}, {
  set(t, k, v, r) { fired.push("set"); return Reflect.set(t, k, v, r); },
  getOwnPropertyDescriptor(t, k) { fired.push("getOwnPropertyDescriptor"); return Reflect.getOwnPropertyDescriptor(t, k); },
  defineProperty(t, k, d) { fired.push("defineProperty"); return Reflect.defineProperty(t, k, d); },
});
p.x = 1;
console.log("[7] p.x = 1 fired: " + fired.join(" -> "));
fired.length = 0;
Reflect.set(p, "y", 1, {});
console.log("    Reflect.set(p, 'y', 1, {}) fired: " + fired.join(" -> "));
```

```text
===== node20 js44b-46c-receiver.js (exit=0) =====
[1] base.who                              base
[2] Reflect.get(base, 'who')              base
[3] Reflect.get(base, 'who', other)       other
[4] Reflect.set(base, 'who', 1, other)    true · other.written 1 · base.written undefined
[5] Reflect.set(plain, 'x', 2, into)      true · plain.x 1 · into.x 2 · own x in into true
[6] child.who through get(t, k) { return t[k] }                     target
    child.who through get(t, k, r) { return Reflect.get(t, k, r) }  child
[7] p.x = 1 fired: set -> getOwnPropertyDescriptor -> defineProperty
    Reflect.set(p, 'y', 1, {}) fired: set
```

```text
   child = Object.create(proxy)    child.name = "child"    child.who ?

   child 에 who 없음 ─▶ 프로토타입(proxy).[[Get]]("who", receiver = child)
                              │
        get(t, k)      { return t[k] }              ─▶ t.who  : getter 의 this = t      ─▶ "target"
        get(t, k, r)   { return Reflect.get(t,k,r) } ─▶ getter 의 this = r = child      ─▶ "child"
```

- ★★★ **`[3]` `Reflect.get(base, 'who', other)` → `other`** · `[4]` setter 도 **`other.written 1 · base.written undefined`** — 접근자는 `receiver` 를 `this` 로 받는다.
- ★★★ **`[5]` 데이터 프로퍼티 — `plain.x 1 · into.x 2 · own x in into true`.** 쓰기는 **`receiver` 에 자기 프로퍼티로** 떨어진다(대상은 안 바뀐다). 상속한 객체에 대입하면 **자식에게 생기는** 규칙(15번)이 이 인자로 표현된다.
- ★★★ **`[6]` — `get(t, k) { return t[k] }` 는 `target`, `Reflect.get(t, k, r)` 는 `child`.** 앞쪽은 **`receiver` 를 버렸다** — 상속한 쪽의 `this` 가 사라진다. **트랩에서 넘길 때 `receiver` 까지 넘기는 것이 표준 형태**인 이유다.
- ★★ **`[7]` — `p.x = 1` 은 `set → getOwnPropertyDescriptor → defineProperty`** 를 불렀다. `set` 트랩이 `Reflect.set(t, k, v, r)` 로 넘기자 `receiver` 가 **Proxy 자신**이라 `OrdinarySet` 이 **그 Proxy 에** 프로퍼티를 확인하고 정의했다 — 트랩이 **두 번 더** 불린다. `Reflect.set(p, 'y', 1, {})` 처럼 `receiver` 가 다른 객체면 **`set` 하나**뿐이다. 동작 (1)이 트랩을 **넘기지 않은** 이유가 이것이다.

### (4) ★ 45번 격자의 한 줄 — `Reflect` 로 넘기면 불변식이 지켜진다

★★★ **45번이 이미 쟀다** — 트랩 8개 × 대상 상태 3개의 24칸을 **`(...args) => Reflect[name](...args)`** 로 넘기자 「**`cells where the bare target gave a different answer: 0 / 24`**」였고, 던진 1칸(`defineProperty` / 설정 불가)은 **맨 대상도 던지는** 칸이었다(45번 동작 (1)의 `[2]`). 트랩이 받은 인자를 **같은 이름의 `Reflect` 에 그대로** 주면 대상의 답이 그대로 나오니 **대조에 걸릴 거짓이 없다.** 다시 재지 않았다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| `Reflect.*` | 대응 연산 / `Object.*` | 실패하면 | 원시값 대상 |
|---|---|---|---|
| `get(o, k, r?)` | `o[k]` | — | `TypeError` |
| `set(o, k, v, r?)` | `o[k] = v` | **`false`**(엄격 대입은 throw) | `TypeError` |
| `has(o, k)` | `k in o` | — | `TypeError`(`in` 도) |
| `deleteProperty(o, k)` | `delete o[k]` | **`false`**(엄격 `delete` 는 throw) | `TypeError` |
| `defineProperty(o, k, d)` | `Object.defineProperty` | **`false`**(Object 는 throw) | `TypeError` |
| `getOwnPropertyDescriptor(o, k)` | `Object.getOwnPropertyDescriptor` | — | **`TypeError`**(Object 는 감싼다) |
| `getPrototypeOf(o)` · `setPrototypeOf(o, p)` | `Object.*` | set 은 **`false`** | **`TypeError`** |
| `isExtensible(o)` · `preventExtensions(o)` | `Object.*` | prevent 는 **`false`** | **`TypeError`**(Object 는 `false`·그대로) |
| `ownKeys(o)` | (`Object.keys` 는 열거·문자열만) | — | **`TypeError`** |
| `apply(f, t, args)` | `f.apply(t, args)` | — | `args` 필수 |
| `construct(C, args, newTarget?)` | `new C(...args)` | — | — |

- **13개 전부 함수 · `Reflect` 자신은 함수가 아니다**(`typeof` `object`).
- 「실패하면」 칸의 `false` 는 동작 (2)의 5행에서, 「원시값」 칸은 동작 (2)의 6행에서 봤다(`has` 는 `'x' in 1` 행).

## 어디서 틀리나

### (1) ★★★ Proxy 트랩에서 `target[key]` 로 넘긴다

**`receiver` 가 사라진다** — 상속한 객체의 getter 가 `this` 로 **대상**을 봤다(`target` 대 `child`, 동작 (3)의 `[6]`). `Reflect.get(t, k, r)` 로 넘긴다.

### (2) ★★★ `Reflect.defineProperty` 의 실패를 `catch` 로 기다린다

**던지지 않는다 — `false` 다**(동작 (2)). 반환값을 검사하지 않으면 실패가 **조용히** 지나간다.

### (3) ★★★ `Reflect.*` 가 `Object.*` 처럼 원시값을 받아 준다고 믿는다

**`TypeError`** — `getPrototypeOf(1)` · `ownKeys(1)` · `getOwnPropertyDescriptor('str', …)` 다섯 행 전부(동작 (2)).

### (4) ★★ `Object.keys` 와 `Reflect.ownKeys` 를 같은 것으로 쓴다

**열거 불가·심볼 키**에서 갈린다 — `[a]` 대 `[a, hidden, Symbol(s)]`(동작 (2)).

### (5) ★★ `Reflect.apply(f, null)` 을 `f.apply(null)` 처럼 쓴다

**인자 목록이 필수**다 — 빼면 `TypeError`(동작 (2)). `f.apply(null)` 은 인자 0개로 부른다(09번).

### (6) ★★ `set` 트랩을 `Reflect.set(t, k, v, r)` 로 넘기면 트랩이 한 번만 불린다고 믿는다

**`receiver` 가 Proxy 면 `getOwnPropertyDescriptor`·`defineProperty` 트랩이 더 불린다**(동작 (3)의 `[7]`). 로그 트랩이 겹쳐 찍히는 자리다.

### (7) ★ `Reflect` 를 생성자나 함수로 쓴다

`typeof Reflect` 는 **`object`** 다(동작 (1)). `[[Call]]`·`[[Construct]]` 가 없다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ **`Reflect` 의 함수 13개가 내부 메서드 13개를 그대로 부르는 것** — 그래서 트랩 13개와 1:1(`13 / 13`).
- ★★★ **실패를 `false` 로 돌려주는 것** — 내부 메서드의 불리언 결과를 **그대로** 준다. 던지는 것은 그 결과를 받은 **`Object.*`·엄격 연산** 쪽이다.
- ★★★ **대상이 객체가 아니면 `TypeError`** — `Object.*` 의 일부는 `ToObject` 로 감싼다.
- ★★ **`receiver`** — `[[Get]]`/`[[Set]]` 의 인자를 그대로 넘긴다. `OrdinarySet` 은 쓰기를 **`receiver` 에** 정의한다(동작 (3)의 `[5]`·`[7]`).
- ★★ **`Reflect.apply` 의 `CreateListFromArrayLike(args)`** — 목록이 없으면 던진다.

### 구현(V8) · 이 판의 관찰

- ★ `Object.getOwnPropertyNames(Reflect)` 의 **순서**(`defineProperty deleteProperty apply …`) — 세 판 같았지만 근거로 쓰지 않는다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`Reflect` 는 `Object` 메서드를 옮겨 놓은 것이다」 → ○ 「**내부 메서드 13개의 직통 번호**다 — `Object` 에 같은 이름이 있는 것은 6개뿐이고, 실패 처리와 원시값 처리가 다르다」
- ✗ 「`Reflect.set` 은 엄격 모드에서 실패하면 던진다」 → ○ 「**모드와 무관하게 `false`**」
- ✗ 「트랩에서는 `target[key]` 로 넘기면 된다」 → ○ 「**`Reflect.get(target, key, receiver)`** — 안 그러면 상속한 쪽의 `this` 가 사라진다」

## 언제 쓰고 언제 안 쓰나

- **Proxy 트랩에서 넘길 때** — 항상 **같은 이름의 `Reflect` 에 받은 인자를 전부**(`receiver` 포함). 45번의 `0 / 24` 가 그 근거다.
- **실패를 분기로 받을 때** — `if (!Reflect.defineProperty(…))`. 예외로 받고 싶으면 `Object.defineProperty`.
- **덮어쓴 `apply`·`hasOwnProperty` 가 있을 수 있는 객체** — `Reflect.apply` · `Object.hasOwn`.
- ★ **안 쓰는 자리** — 원시값이 들어올 수 있는 자리에서 `Reflect.getPrototypeOf` 등(던진다) · 열거 가능한 문자열 키만 원할 때 `ownKeys`.

## 핵심 문장

1. ★★★ `Reflect` 는 **함수 13개** — 트랩 이름을 손으로 적은 handler 에 불러 보니 **같은 이름의 트랩 하나만** 불렸다 `13 / 13`.
2. ★★★ `Object`/연산자 대 `Reflect` 19행 — **한쪽만 던진 행 `11 / 19`**, 값이 다른 행 `3 / 19`, 합 **`14 / 19`**.
3. ★★★ 갈리는 이유는 둘 — **실패를 `false` 로**(defineProperty·set·delete·setPrototypeOf) · **원시값을 안 감싼다**(getPrototypeOf(1) 등 다섯).
4. ★★★ **`receiver`** 는 getter·setter 의 `this` 와 데이터 쓰기가 떨어지는 객체다 — 트랩에서 버리면 상속한 쪽이 `target` 을 본다(`child` 가 아니라).
5. ★★ 트랩에서 **`Reflect.<같은 이름>(...arguments)`** 로 넘기면 맨 대상과 다른 칸 **`0 / 24`**(45번).

## 관련 자료

- [ECMA-262 — Reflection](https://tc39.es/ecma262/multipage/reflection.html) · [ECMA-262 — Proxy Object Internal Methods](https://tc39.es/ecma262/multipage/ordinary-and-exotic-objects-behaviours.html)
- [45 — `Proxy`](../45-proxy/2-summary.md) — ★ **경계**: 트랩과 불변식은 거기. 여기는 **트랩이 넘기는 짝(`Reflect`)과 옛 창구와의 차이**부터.
- [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) — `apply` 의 인자 규칙 · [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md) · [22 — `Symbol`](../22-symbol-and-well-known-symbols/2-summary.md) · [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md)(상속한 쪽에 쓰면 자식에게 생긴다).

## 용어 풀이

- **`Reflect`** — 내부 메서드 13개를 부르는 함수 13개를 가진 평범한 객체(ES2015). 함수가 아니다.
- **내부 메서드(internal method)** — `[[Get]]`·`[[Set]]` 처럼 명세가 객체마다 정의한 동작. Proxy 트랩이 가로채는 대상이다.
- **`receiver`** — `get`/`set` 에서 `this` 가 될 객체. 기본은 대상 자신이다.
- **`CreateListFromArrayLike`** — 유사 배열을 인자 목록으로 바꾸는 명세 연산. 객체가 아니면 `TypeError`.
- **`ToObject`** — 원시값을 래퍼 객체로 감싸는 명세 연산. `Object.*` 의 일부가 쓰고 `Reflect.*` 는 안 쓴다.

## 더 들어가면

- **`Reflect.construct` 의 `newTarget`** — 셋째 인자로 `new.target` 을 바꾼다(17번의 `new.target`). 이 문서는 두 인자 판만 돌렸다.
- **`Object.hasOwn` 대 `Reflect.has`** — 자기 것만 대 체인 전체. 이 문서의 격자에 넣지 않았다(27번 · 15번).
