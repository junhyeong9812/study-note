# js/syntax/15 — 프로토타입 체인: 「읽기는 체인을 타고, 쓰기는 수신자에 내려앉는다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> 프로퍼티 조회는 **어느 칸에서 답이 나와도 같은 값**을 내놓는다 — `C.fromA` 가 `'a'` 인 것은
> 그 값이 **첫 칸에 있었는지 셋째 칸에 있었는지 한 글자도 말해 주지 않는다.**
> ★★★ **값으로는 원리상 못 가른다.** 그래서 체인의 **각 칸에 `Proxy` 를 씌워** 트랩 로그로 경로를 찍었다 —
> `C.fromC` 는 로그 **1줄**, `C.fromB` 는 **2줄**, `C.fromA` 와 `C.nope` 는 **3줄**이다.
> **이 문서의 결론은 전부 그 로그에서 나온다.**
> ② 전수 격자가 체인 **19종**과 생성자 **5종**을 글자로 찍고,
> ③ 브랜드 태그(`Object.prototype.toString.call`)가 **다른 창이 전부 닫힌 자리**에서 홀로 답한다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — `OrdinaryGet` · `OrdinarySet` · `OrdinarySetWithOwnDescriptor` ·
>   `OrdinaryHasInstance` · `Object.create` · `Object.getPrototypeOf` / `setPrototypeOf` · `__proto__` 의 Annex B
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — `Object.create` 가 ES5, `setPrototypeOf`·`Symbol.hasInstance` 가 ES2015, `Object.hasOwn` 이 ES2022 인 것을 가릴 때
> - [MDN — Inheritance and the prototype chain](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Inheritance_and_the_prototype_chain) · [MDN — `Object.getPrototypeOf`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getPrototypeOf)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·경로·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
>
> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박혀 다른 머신에서 재현이 안 되기 때문이다.
> ★★ **이 문서의 모든 블록은 표준 출력뿐이다** — 표준 오류와 섞은 블록이 하나도 없다.
> ★★★ **엄격 블록과 비엄격 블록을 섞지 않았다** — `js12b-15c-shadow.js` 와 `js12b-15e-pycontrast.js` 는
> 첫 줄이 `"use strict"` 이고, 나머지 셋은 **모드와 무관한 것만** 묻는다.
>
> **버전** — 프로토타입 체인 자체는 **초판부터**다.
> **`Object.create` 는 ES5**, **`Object.getPrototypeOf` 도 ES5**,
> **`Object.setPrototypeOf`·`Symbol.hasInstance`·`class` 는 ES2015**,
> **`Object.hasOwn` 은 ES2022**, **`__proto__`(접근자와 리터럴 문법 둘 다)는 Annex B** 다.
> ★ Annex B 는 **웹 호환을 위한 규범적 선택 사항**이지만 **모든 웹 엔진이 구현한다.**
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | 체인의 각 칸을 `Proxy` 로 감싸 `get`·`set`·`has`·`gopd`·`getPrototypeOf` 트랩을 찍는다. **조회가 어디서 멈추나**는 **오직 이것으로만** 보인다 |
> | ★★★ **② 전수 격자** | 체인 **19종** · 생성자 자신의 체인 **5종** · 「있나」를 묻는 뷰 **4종** · 프로토타입 쪽 프로퍼티 **3종**(데이터 / 접근자 / 비쓰기) |
> | ★★★ **③ 브랜드 태그** `Object.prototype.toString.call` | **창을 바꿔 물은 자리다**(제5의 상태) — `Object.create(null)` 은 `toString` 도 없고 `String()` 이 `TypeError` 라 **평소 창이 전부 닫힌다.** 브랜드 태그만 `[object Object]` 라고 답한다 |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `TypeError` **여섯 종** — 비쓰기 · getter-only · 원시값 변환 · 프로토타입 인자 · `instanceof` 우변 두 가지 |
> | ★ **⑤ 두 판 대조기 + 브라우저** | 판이 갈린 칸 · 호스트가 정하는 칸 — **이 주제에서 갈린 블록 0개** |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | 이 주제에는 **`SyntaxError` 가 한 줄도 없다.** 체인은 전부 런타임 의미라 파서가 볼 것이 없다 — **잴 것이 없다** |
> | ★ **안 쟀다 — 성능** | ★★★ 「`setPrototypeOf` 가 느리다」·「체인이 길면 조회가 느리다」는 **흔한 말이지만 여기서 한 줄도 쓰지 않는다.** **안 쟀다** |
> | ★ **안 돌렸다 — 두 번 컴파일**(엄격/비엄격) | 모드가 답을 바꾸는 칸은 **체인 위의 실패한 쓰기** 두 줄뿐이고, 그 격자는 [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md)의 `proto has non-writable a` 줄이 이미 갖고 있다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **트랩 로그의 개수와 순서** |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **예외의 종류** · **own 키 목록** |
> | 브라우저 UA 문자열의 뒷자리 | ★★★ **체인을 글자로 찍은 줄** · 격자의 `true`/`false` |
> | `console.log(bare)` 가 찍는 **표기 형식**(Node 의 `util.inspect` — 호스트가 정한다) | ★★ **브랜드 태그** `[object Object]`(명세가 정한다) |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> ★★★ **두 판이 갈린 블록은 이 주제에 0개다**(전체 19블록 중 갈린 것은 14번 주제의 `toSorted` 한 블록뿐이다).
>
> **선행** — [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) · [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) · [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md).
> ★★★ **07번이 이 주제의 setter 절을 떠받친다.** 체인 위의 setter 가 불릴 때 그 안의 `this` 는
> **setter 가 사는 객체가 아니라 점 왼쪽의 객체**다 — 07번의 **암시적 바인딩** 그대로다.
> 그래서 `this._store = v` 가 **자식에** own 프로퍼티를 만든다. 07번을 안 읽으면 이 줄이 마술로 보인다.
> ★★★ **14번이 「무엇이 쓰기를 막나」의 정본**이다. 여기서는 **그 막는 것이 체인 위에 있을 때** 무슨 일이 나는지만 본다.
> ★★ **13번이 `__proto__:` 리터럴 문법을 이미 갈랐다** — 다섯 형태 중 둘만 프로토타입을 바꾼다는 실측이 거기 있다.
> 여기서는 **`__proto__` 의 다른 얼굴**, 즉 `Object.prototype` 에 사는 **접근자** 쪽을 본다. **둘은 다른 물건이다.**
> **이어지는 곳** — 목록의 **16번 주제** 「`class` 문법」 · 목록의 **17번 주제** 「상속과 `super`」 ·
> 목록의 **18번 주제** 「`for...in` 과 열거」 · 목록의 **34번 주제** 「타입 검사 관용구」 · 목록의 **45번 주제** 「`Proxy`」
>
> ★★ **경계 — `class` 가 무엇을 어디에 붙이나는 16번이 정본이다.** 여기서는 **`class B extends A` 가 체인을 두 줄 만든다**는 사실까지다.
> ★★ **경계 — `extends`·`super`·내장 객체 상속의 제약은 17번이 정본이다.**
> ★★ **경계 — 체인을 타는 열거(`for...in`)는 18번이 정본이다.** 여기서는 **조회가 체인을 탄다**는 사실까지다.
> ★★ **경계 — `instanceof` 를 실무에서 어느 검사와 견주나는 34번이 정본이다.** 여기서는 **`instanceof` 가 무엇을 보나**까지다.
> ★★ **경계 — `Proxy` 트랩의 계약과 불변식은 45번이 정본이다.** 여기서는 **로그를 심는 도구로만** 쓴다.

```sh
# js12b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    const ord = {}; ord.b = 1; ord[2] = 1; ord.a = 1; ord[1] = 1;
    const box = { p: 0 };
    box.p ??= 9;
    console.log("node " + v.node + "  v8 " + v.v8 +
      "  optchain " + String(({ a: { b: 7 } }).a?.b) +
      "  nullish " + String(0 ?? "D") + "/" + String(0 || "D") +
      "  logical-assign " + box.p +
      "  ownKeys " + JSON.stringify(Reflect.ownKeys(ord)) +
      "  hasOwn " + typeof Object.hasOwn +
      "  desc " + JSON.stringify(Object.getOwnPropertyDescriptor({ q: 1 }, "q")) +
      "  defineProp-desc " + JSON.stringify(Object.getOwnPropertyDescriptor(Object.defineProperty({}, "q", { value: 1 }), "q")));'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js12b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  optchain 7  nullish 0/D  logical-assign 0  ownKeys ["1","2","b","a"]  hasOwn function  desc {"value":1,"writable":true,"enumerable":true,"configurable":true}  defineProp-desc {"value":1,"writable":false,"enumerable":false,"configurable":false}
node 20.19.6  v8 11.3.244.8-node.33  optchain 7  nullish 0/D  logical-assign 0  ownKeys ["1","2","b","a"]  hasOwn function  desc {"value":1,"writable":true,"enumerable":true,"configurable":true}  defineProp-desc {"value":1,"writable":false,"enumerable":false,"configurable":false}
Google Chrome 151.0.7922.173 
```

## 한눈에 — 쉽게 말하면

**객체는 혼자 있지 않고 「윗집」을 하나 가리키고 있다.** 그 윗집도 다시 윗집을 가리키고, 언젠가 `null` 에서 끝난다.
이 사슬이 **프로토타입 체인**이다.

- **읽을 때** — 자기 서랍에 없으면 **윗집으로 올라가** 찾는다. 끝까지 없으면 **예외가 아니라 `undefined`** 다.
- **쓸 때** — ★★★ **윗집까지 올라가 보기는 하는데, 값을 놓는 자리는 언제나 자기 서랍이다.**
  올라가는 이유는 「윗집에 **막는 장치**나 **대신 받아 줄 사람**이 있나」를 보기 위해서다.

```text
   읽기 -- 위로 올라가며 이름표를 본다

   o  ──▶  [ 1칸 ]   own 키에 x 가 있나 ── 있다 ──▶ 그 값이 답 (끝)
                │ 없다
                v
            [ 2칸 ]   own 키에 x 가 있나 ── 있다 ──▶ 그 값이 답 (끝)
                │ 없다
                v
            [ 3칸 ]   ...
                │ 없다
                v
             null     더 갈 칸이 없다  ──▶  undefined
                                            ★ 예외가 아니다. "없다" 도 답이다
```

```text
   쓰기 -- 같은 계단을 올라가지만 내려앉는 자리는 맨 아래다

   o.x = V

   o  ──▶  [ 1칸 ]   own x 가 있나 ─ 있고 쓸 수 있으면 ──▶ 여기 덮어쓴다 (끝)
           │  없다
           │    ┌──────────────────────────────────────────┐
           ├───▶│ [ 2칸 ] 을 본다   무엇을 보러 가나:        │
           │    │   · setter 가 있나        -> 그것이 가져간다 │
           ├───▶│ [ 3칸 ]           · 비쓰기 데이터인가  -> 막힌다  │
           │    │   · getter 만 있나        -> 막힌다        │
           │    └──────────────────────────────────────────┘
           │              아무것도 안 걸리면
           v
      ★ 값은 o 자신의 own 프로퍼티로 새로 생긴다
        윗칸의 값은 한 글자도 안 바뀐다
```

★★★ **이 두 그림의 비대칭이 이 주제의 전부다.**
「읽기는 남의 것을 **빌려 본다**, 쓰기는 **내 것을 새로 만든다**」 — 그래서 **읽은 자리와 쓴 자리가 다르다.**

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 내 서랍 | own 프로퍼티 | `Object.hasOwn(o, 'x')` |
| 윗집 | `[[Prototype]]` | `Object.getPrototypeOf(o)` |
| 윗집으로 가는 계단 | 프로토타입 체인 | `getPrototypeOf` 를 `null` 까지 반복 |
| 계단 끝 | `null` | 거기서 `undefined` 가 돌아온다 |
| 내 서랍에 같은 이름표를 붙이기 | 섀도잉 | `o.x = v` 뒤 `Object.hasOwn(o, 'x')` 가 `true` |
| 윗집의 대리인 | 체인 위의 setter | 쓰기가 **가로채여** own 이 안 생긴다 |
| 윗집의 자물쇠 | 비쓰기 데이터 프로퍼티 | 엄격에서 `TypeError` 로 막힌다 |
| ★ 새 집을 짓는 설계도 | 함수의 `.prototype` **프로퍼티** | `Ctor.prototype` |
| ★ 지금 살고 있는 윗집 | 그 인스턴스의 `[[Prototype]]` | `Object.getPrototypeOf(inst)` |
| 계단이 아예 없는 집 | `Object.create(null)` | `String(o)` 가 `TypeError` 로 막힌다 |
| 몇 층에서 답이 나왔는지 세는 계기 | `Proxy` 트랩 로그 | 이 주제의 본체 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**프로토타입에 배열을 올려 뒀더니 인스턴스 전부가 같은 배열을 쓴다**」와
「**분명히 대입했는데 값이 안 바뀐다**」가 그것이다.
앞엣것은 **한 개를 같이 쓰는 윗집**이고, 뒤엣것은 **윗집의 대리인이 가져간 것**이다.

> **프로토타입(prototype)** — 어떤 객체가 「없으면 여기로 가 보라」고 가리키고 있는 다른 객체.\
> 예: `{}` 의 프로토타입은 `Object.prototype` 이다. 그래서 `({}).toString` 이 `undefined` 가 아니다.

> **own 프로퍼티(own property)** — 그 객체 **자신의 서랍**에 있는 프로퍼티. 빌려 본 것이 아니다.\
> 예: `Object.hasOwn(o, 'x')` 가 `true` 면 own 이고, `'x' in o` 만 `true` 면 윗집에서 빌려 보는 중이다.

> **수신자(receiver)** — 점 왼쪽에 있던, **처음 요청을 받은 객체.**\
> 예: `leaf.s = 1` 에서 setter 가 체인 위에 있어도 그 안의 `this` 는 `leaf` 다. 07번의 암시적 바인딩과 같은 규칙이다.

## 이 주제가 답하려는 질문

1. **`o.x` 는 어디를 어떤 순서로 보고, 「없다」는 무엇으로 증명하나** — 그리고 **어느 칸에서 답이 나왔는지를 무엇으로 아나?**
2. **`o.x = v` 는 어디에 내려앉나** — 읽은 자리와 같은가 다른가? 그 규칙이 깨지는 예외는 몇 개인가?
3. **`prototype` 과 `[[Prototype]]` 과 `__proto__` 는 각각 무엇이고, `new` 와 `instanceof` 는 그 중 무엇을 보나?**

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 체인을 글자로 찍는다 — 19종 전수 격자

**언제 쓰나** — 「이 값의 메서드가 어디서 오는 거지?」를 물을 때. 추측하지 말고 **`null` 까지 찍어 보면 끝난다.**

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

```text
===== node20 js12b-15a-chain.js (exit=0) =====
[1] chains, each printed to null
{}                                  Object.prototype -> null
[]                                  Array.prototype -> Object.prototype -> null
function f() {}                     Function.prototype -> Object.prototype -> null
() => {}                            Function.prototype -> Object.prototype -> null
function* g() {}                    GeneratorFunction.prototype -> Function.prototype -> Object.prototype -> null
async function h() {}               AsyncFunction.prototype -> Function.prototype -> Object.prototype -> null
new A   (class A)                   A.prototype -> Object.prototype -> null
new B   (class B extends A)         B.prototype -> A.prototype -> Object.prototype -> null
new Ctor  (function Ctor)           Ctor.prototype -> Object.prototype -> null
new Map()                           Map.prototype -> Object.prototype -> null
new Error('x')                      Error.prototype -> Object.prototype -> null
new TypeError('x')                  TypeError.prototype -> Error.prototype -> Object.prototype -> null
/re/                                RegExp.prototype -> Object.prototype -> null
1  (number primitive)               Number.prototype -> Object.prototype -> null
's'  (string primitive)             String.prototype -> Object.prototype -> null
Symbol('s')                         Symbol.prototype -> Object.prototype -> null
Object.create(null)                 null
Object.create(Object.create(null))  (anonymous [object Object]) -> null
Object.create({ a: 1 })             (anonymous [object Object]) -> Object.prototype -> null

[2] the constructors themselves are objects too -- their chain is different
A  (the class object)               Function.prototype -> Object.prototype -> null
B  (extends A)                      A (the class object) -> Function.prototype -> Object.prototype -> null
Ctor  (function)                    Function.prototype -> Object.prototype -> null
Object                              Function.prototype -> Object.prototype -> null
Function                            Function.prototype -> Object.prototype -> null

[3] prototype  vs  [[Prototype]] -- two different slots with confusable names
Ctor.prototype                       [object Object]   own keys ["constructor"]
Object.getPrototypeOf(Ctor)          Function.prototype
Ctor.prototype === getPrototypeOf(Ctor)?  false
getPrototypeOf(new Ctor) === Ctor.prototype?  true
does an instance have .prototype?    false
does an arrow function have one?     false
does a class method have one?        false
does class A have one?               true
```

**그림 해설 — 한 덩어리에 한 문장.**

- ★★★ **이 스크립트가 하는 일은 `getPrototypeOf` 를 `null` 이 나올 때까지 반복하는 것뿐**이다.
  체인은 신비한 것이 아니라 **한 줄짜리 반복문으로 끝까지 찍히는** 유한한 사슬이다.
- ★★★ **칸의 이름은 「그 칸이 스스로 들고 있는 `constructor`」로 지었다.**
  ★ 이것이 중요하다 — **상속된 `constructor` 를 읽으면 전부 `Object` 가 되어** 이름이 쓸모없어진다.
  `Object.create({ a: 1 })` 줄의 **첫 칸**이 `(anonymous [object Object])` 인 것이 그 증거다.
  그 칸(`{ a: 1 }`)은 `constructor` 를 **빌려 볼 뿐 갖고 있지 않아서** 이름을 지을 수 없다.
  이름이 없을 때 쓴 `[object Object]` 가 **③ 브랜드 태그**이고, 이 문서에서 그 창이 처음 열리는 자리다.
- ★★ **원시값도 체인이 있다** — `1` 은 `Number.prototype -> Object.prototype -> null` 이다.
  ★ 정확히는 **원시값 자체에 칸이 있는 것이 아니라** 스크립트가 `Object(x)` 로 감싸 찍은 것이고,
  **점 접근도 같은 일을 한다**(01번의 임시 래핑). 그래서 `(1).toFixed` 가 어디서 오는지가 이 줄 하나로 끝난다.
- ★★ **제너레이터와 async 함수는 칸이 하나 더 있다** —
  `GeneratorFunction.prototype -> Function.prototype -> ...`, `AsyncFunction.prototype -> Function.prototype -> ...` 이다.
  평범한 함수와 화살표 함수는 **바로 `Function.prototype`** 이다. **네 가지가 여기서 갈린다.**
- ★★★ **`Object.create(null)` 줄은 `null` 한 글자다.** 칸이 하나도 없다. 동작 (4)의 주인공이 이 줄이다.
- ★★ **`class B extends A` 는 체인을 두 줄 만든다.**
  `[1]` 에서 `new B` 의 체인이 `B.prototype -> A.prototype -> Object.prototype -> null` 이고,
  `[2]` 에서 **`B` 라는 클래스 객체 자체**의 체인이 `A (the class object) -> Function.prototype -> ...` 이다.
  ★★★ **`B` 의 윗집이 `A` 다** — 이것이 **정적 멤버가 상속되는 이유**다.
  ★ 왜 두 줄이 필요한가 — 인스턴스가 쓰는 메서드 사슬과 클래스 자신이 쓰는 정적 멤버 사슬이 **다른 사슬**이기 때문이다.
  **`extends` 가 정확히 무엇을 잇나는 16·17번이 정본**이고, 여기서는 **사슬이 둘이라는 사실**까지다.
- ★★ `[2]` 의 나머지 네 줄도 같은 것을 말한다 — **생성자도 객체라서 자기 체인이 따로 있다.**
  `A`·`Ctor`·`Object` 가 전부 `Function.prototype -> Object.prototype -> null` 이다.
  ★ **`Function` 자신의 윗집이 `Function.prototype`** 인 것이 재미있는 줄이다 — 자기 `.prototype` 이 자기 윗집이다.
- ★★★ `[3]` 이 **이름 때문에 가장 헷갈리는 자리**를 가른다. 동작 (4)의 그림에서 세 상자로 다시 그린다.
  여기서 먼저 확인할 것은 두 줄이다 —
  **`Ctor.prototype === Object.getPrototypeOf(Ctor)` 는 `false`** 이고,
  **`Object.getPrototypeOf(new Ctor()) === Ctor.prototype` 은 `true`** 다.
- ★ `[3]` 의 마지막 네 줄이 **`.prototype` 을 누가 갖고 있나**를 전수로 찍는다 —
  **인스턴스는 없고**(`"prototype" in inst` 가 `false`), **화살표 함수도 없고**, **메서드 단축도 없고**, **클래스는 있다.**
  ★ 13번에서 「메서드 단축과 화살표는 `prototype` 을 안 만든다」를 실측했는데, **그 사실이 여기서 다시 쓰인다** —
  `.prototype` 이 없는 함수는 **`new` 로 못 부른다.**

**비용** — 체인이 길 때의 조회 비용은 **재지 않았다.** 이 문서에 속도 주장이 한 줄도 없다.

### (2) ★★★ 조회가 어디서 멈추나 — 트랩 로그가 유일한 근거

**언제 쓰나** — 「이 값이 own 인가 상속인가」를 넘어 「**어느 칸에서 왔나**」를 물을 때.
★★★ **값으로는 원리상 못 가른다** — 어느 칸에서 왔든 `'a'` 는 `'a'` 다. 로그만이 경로를 말한다.

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

```text
===== node20 js12b-15b-proxy.js (exit=0) =====
[1] reading -- the lookup walks down until it finds the key
C.fromC             -> c            trap log ["C.get(fromC)"]
C.fromB             -> b            trap log ["C.get(fromB)","B.get(fromB)"]
C.fromA             -> a            trap log ["C.get(fromA)","B.get(fromA)","A.get(fromA)"]
C.nope              -> undefined    trap log ["C.get(nope)","B.get(nope)","A.get(nope)"]
C.toString          -> function     trap log ["C.get(toString)","B.get(toString)","A.get(toString)"]

[2] 'in' and hasOwnProperty walk differently
'fromA' in C        -> true         trap log ["C.has(fromA)","B.has(fromA)","A.has(fromA)"]
hasOwn(C,'fromA')   -> false        trap log ["C.gopd(fromA)"]
hasOwn(C,'fromC')   -> true         trap log ["C.gopd(fromC)"]

[3] writing -- the write does NOT walk to where the value lives
C.fromA = 'W'       -> done         trap log ["C.set(fromA)","B.set(fromA)","A.set(fromA)","C.gopd(fromA)"]
after the write:
C.fromA  (read)     -> W            trap log ["C.get(fromA)"]
A still holds       -> a
own keys of C's target -> ["fromC","fromA"]

[4] a setter on the chain -- now the write DOES walk
leaf.s = 'written'   log ["setter ran, this is the LEAF object"]
own keys of leaf     ["_v"]
base._v              base   leaf._v written   leaf.s written
```

**그림 해설.**

```text
   C -> B -> A  세 칸에 전부 Proxy 를 씌웠다

   C.fromC   로그 1줄   ["C.get(fromC)"]                          ┐
   C.fromB   로그 2줄   ["C.get","B.get"]                         │ 찾은 칸에서 멈춘다
   C.fromA   로그 3줄   ["C.get","B.get","A.get"]                 ┘
   C.nope    로그 3줄   ["C.get","B.get","A.get"]  -> undefined
   C.toString 로그 3줄  ["C.get","B.get","A.get"]  -> function

   ★ nope 와 toString 의 로그가 똑같이 3줄인데 답이 다르다.
     A 위에는 Object.prototype 과 null 이 더 있고 거기엔 탐침을 안 심었다.
     toString 이 function 으로 돌아온 것이 "A 위로 더 올라갔다" 는 증거다.
```

- ★★★ `[1]` **로그의 길이가 곧 걸어간 칸 수**다. `fromC` 는 1, `fromB` 는 2, `fromA` 는 3 —
  **찾는 순간 멈춘다**(`fromC` 를 읽을 때 `B` 와 `A` 는 로그에 한 줄도 안 남는다).
- ★★★ **`C.nope` 가 「없다」의 증명이다.** 세 칸을 전부 뒤지고도 못 찾아 **`undefined`** 가 돌아왔다.
  ★★ **예외가 아니다** — JS 에서 「없는 프로퍼티」는 실패가 아니라 **`undefined` 라는 답**이다.
  이것이 12번의 `?.` 가 필요한 이유이기도 하다(거기서 터지는 것은 **그 다음 점**이다).
- ★★★ **로그 3줄이 「체인이 3칸」이라는 뜻은 아니다 — 계측한 칸이 셋일 뿐이다.**
  `C.toString` 이 `function` 으로 돌아온 것이 그 반증이다.
  `A` 의 타깃은 평범한 객체라 **그 위에 `Object.prototype` 이 더 있고**, `toString` 은 거기서 왔다.
  ★ **침묵은 「안 갔다」가 아니라 「거기엔 탐침이 없다」** — 18-A 의 규칙을 이 주제가 그대로 겪는 자리다.
- ★★ `[2]` **`in` 과 `Object.hasOwn` 은 다른 질문이다.**
  `'fromA' in C` 는 **`has` 트랩 3줄**을 남기고 `true` 를 답한다 — **체인을 끝까지 탄다.**
  `Object.hasOwn(C, 'fromA')` 는 **`gopd` 트랩 1줄**만 남기고 `false` 를 답한다 — **첫 칸만 본다.**
  ★★★ **같은 프로퍼티에 대해 하나는 `true`, 하나는 `false`** 다. 둘은 경쟁이 아니라 **다른 질문**이다.
- ★★★ `[3]` **이 문서에서 가장 중요한 로그 한 줄이다.**
  `C.fromA = 'W'` 의 트랩 로그가 **`["C.set","B.set","A.set","C.gopd"]`** 다.

```text
   C.fromA = 'W'  의 트랩 로그를 그대로 읽으면

   ① C.set(fromA)     "나한테 own fromA 가 없네. 윗칸에 뭐가 있는지 보자"
   ② B.set(fromA)     "여기도 없네. 더 위로"
   ③ A.set(fromA)     "여기 있다. setter 가 아니고 쓸 수 있는 데이터다"
   ④ C.gopd(fromA)    "그럼 처음 요청한 C 에게 되돌아가 거기 자리를 만든다"
                       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                       ★ 네 번째 줄이 결정적이다. C 로 "돌아왔다"

   결과 : A.fromA 는 여전히 'a'   ·   C 의 타깃 own 키가 ["fromC","fromA"] 로 늘었다
```

- ★★★ **「쓰기는 체인을 안 탄다」는 거친 요약이고, 실측은 더 정확하다.**
  **탐색은 체인을 탄다** — 윗칸에 **setter 가 있나**, **비쓰기 프로퍼티가 있나**를 보러 끝까지 올라간다.
  **바뀌는 것은 그 다음이다** — 아무것도 안 걸리면 **값이 놓이는 자리는 수신자**다.
  ★★★ 네 번째 트랩(`C.gopd`)이 **되돌아온 발자국**이고, 「탐색과 저장이 다른 객체에서 일어났다」의 유일한 증거다.
  ★ 확인 두 줄이 그것을 닫는다 — **`A` 는 여전히 `'a'` 를 들고 있고**, **`C` 의 타깃에 own `fromA` 가 생겼다.**
- ★★ 쓴 **직후의 읽기가 로그 1줄**(`["C.get(fromA)"]`)로 끝나는 것도 같은 사실의 다른 얼굴이다 —
  이제 첫 칸에서 찾기 때문에 **더 이상 올라가지 않는다.**
- ★★★ `[4]` **체인 위에 setter 가 있으면 쓰기가 정말로 체인을 탄다.**
  `leaf.s = 'written'` 이 **`base` 의 setter 를 부르고**, 로그가 `"setter ran, this is the LEAF object"` 다.
  ★★★ **`this` 는 setter 가 사는 `base` 가 아니라 점 왼쪽의 `leaf`** 다 — 07번의 **암시적 바인딩** 그대로다.
  그래서 setter 안의 `this._v = v` 가 **`leaf` 에 own `_v` 를 만들었고**(`own keys of leaf` 가 `["_v"]`),
  **`base._v` 는 `base` 그대로**다. `s` 자체는 **own 이 되지 않았다.**

> **트랩(trap)** — `Proxy` 에 심는 갈고리 함수. 대상 객체에 일어나는 내부 동작을 가로채 대신 실행한다.\
> 예: `get` 트랩은 프로퍼티를 읽을 때마다 불린다. 정본은 목록의 **45번 주제** 「`Proxy`」이고, 여기서는 **로그를 심는 도구**로만 쓴다.

**비용** — `Proxy` 를 씌우면 값이 달라지는지 **따로 확인했다** — 트랩이 전부 `Reflect` 로 그대로 넘기므로
답은 원본과 같다(`C.fromA` 가 `'a'`). **속도는 재지 않았다.**

### (3) ★★★ 읽기/쓰기 비대칭 — 프록시 없이 다시 확인한다

**언제 쓰나** — (2)의 결론을 **평범한 객체**로 재확인할 때. 그리고 **공유 가변값 함정**을 만날 때.
★ 이 블록은 **전부 엄격 모드**다(첫 줄이 `"use strict"`).

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

```text
===== node20 js12b-15c-shadow.js (exit=0) =====
[1] read walks the chain; write lands on the receiver
a.v  (before)                         from proto   ownProperty? false
a.v = 'own on a'  -> a.v              own on a   ownProperty? true
proto.v                               from proto
b.v  (the sibling)                    from proto   ownProperty? false
delete a.v  -> a.v                    from proto   ownProperty? false

[2] the trap: a shared MUTABLE value on the prototype
x.list.push(...)  -> y.list           ["pushed through x"]
x.count += 1      -> x.count          1   own? true
                  -> y.count          0   own? false
                  -> shared.count     0

[3] when the prototype's property is NOT writable, the write is blocked (strict: TypeError)
kid.v = 'try'                         TypeError Cannot assign to read only property 'v' of object '#<Object>'
own? after the failed write           false
defineProperty on kid instead         kid.v = defined   own? true   ro.v = read only

[4] a setter on the prototype takes the write -- and `this` is the receiver
child.s = 'child wrote'               child.s = child wrote
own keys of child                     ["_store"]
withSetter._store                     proto store
did 's' become an own property?       false

[5] getter-only on the prototype -- strict throws, and nothing is shadowed
c2.s = 'nope'                         TypeError Cannot set property s of #<Object> which has only a getter
own keys of c2                        []

[6] four ways to ask 'does it have v?' on a shadowing object
'v' in o2                             true
Object.hasOwn(o2, 'v')                false
o2.hasOwnProperty('v')                false
Object.keys(o2)                       []
after o2.v = 2 : Object.hasOwn        true
after o2.v = 2 : Object.keys          ["v"]
after o2.v = 2 : p2.v                 1
```

**그림 해설.**

- ★★★ `[1]` **읽기는 빌려 보고 쓰기는 새로 만든다.**
  `a.v` 는 처음에 `'from proto'` 이고 own 이 `false` 다. `a.v = 'own on a'` 뒤에는 own 이 `true` 가 되고,
  **`proto.v` 는 한 글자도 안 바뀌었다.** 형제 객체 `b.v` 도 여전히 `'from proto'` 다.
  ★★ **`delete a.v` 를 하면 원래 값이 다시 드러난다** — 덮은 것이 아니라 **가린 것**이었다는 증거다.
- ★★★ `[2]` **실무 급소는 여기다.** 프로토타입에 **가변 객체**가 있으면 그림이 뒤집힌다.
  `x.list.push(...)` 는 **대입이 아니라 고치기**라 own 을 안 만들고 **윗집의 그 배열 한 개**를 늘린다 —
  그래서 `y.list` 에도 보인다.
  ★★★ **바로 아래 줄이 대비다** — `x.count += 1` 은 **읽고 나서 대입**이므로 `x` 에 own `count` 가 생기고,
  `y.count` 는 `0`, `shared.count` 도 `0` 이다.
  ★ **같은 프로토타입 위에서 한 줄은 공유를 만들고 한 줄은 own 을 만든다.** 이 둘을 섞어 쓰면 반은 공유되고 반은 안 된다.

```text
   프로토타입에 가변 객체를 올려 두면

        shared  { list: [], count: 0 }
                     ^            ^
                     │            │
        x ───────────┘            │        x.list.push(...)   -> 윗집의 그 배열이 늘어난다
        y ────────────────────────┘        y.list 에도 보인다  ★ own 은 안 생긴다

        x.count += 1
             = (읽기) + (쓰기)
               읽기는 윗집에서 0 을 가져오고
               쓰기는 x 에 own count = 1 을 만든다   ★ shared.count 는 0 그대로
```

- ★★ `[3]` **윗집의 데이터 프로퍼티가 비쓰기면 쓰기가 막힌다.**
  엄격에서 `TypeError` 이고, **own 프로퍼티도 안 생긴다**(`own?` 가 `false`).
  ★★★ **그런데 `defineProperty` 는 통과한다** — 바로 다음 줄에서 `kid.v` 가 `'defined'` 가 되고 own 이 `true` 이며
  `ro.v` 는 그대로 `'read only'` 다.
  **대입(`=`)과 정의(`defineProperty`)는 다른 문이다** — 대입은 체인을 보고, 정의는 **그 객체에 바로 꽂는다.**
  ★ 왜 이런 규칙인가 — 대입은 「**값을 바꾸겠다**」는 뜻이라 윗집의 금지를 존중하고,
  정의는 「**이 객체에 이 모양의 칸을 만들겠다**」는 뜻이라 윗집과 무관하기 때문이다. 정본은 14번이다.
- ★★★ `[4]` **윗집에 setter 가 있으면 그것이 쓰기를 가져간다.**
  `child.s = 'child wrote'` 뒤에 **`child` 의 own 키가 `["_store"]`** 이고 **`s` 는 own 이 아니다.**
  ★★★ 그리고 **`withSetter._store` 는 `'proto store'` 그대로**다 —
  setter 안의 `this` 가 `withSetter` 가 아니라 **`child`** 였다는 증거다.
  ★★ 이것이 07번의 규칙이 그대로 걸리는 자리다: **메서드 호출에서 `this` 는 수신자**다. setter 도 메서드다.

```text
   체인 위에 setter 가 있을 때의 쓰기 경로

   child.s = 'child wrote'

   child            withSetter
   ┌──────┐         ┌───────────────────────────┐
   │ (빔) │ ──────▶ │ _store : "proto store"    │
   └──────┘         │ get s  ()                 │
       ^            │ set s  (v) { this._store = v }
       │            └──────────────┬────────────┘
       │                           │ 여기 setter 가 있다 -> 쓰기를 가져간다
       │                           │
       │      this 는 setter 가 사는 집이 아니라 점 왼쪽의 child 다
       └───────────────────────────┘
                 그래서 _store 가 child 에 생긴다

   결과 : child 의 own 키 ["_store"]   ·   s 는 own 이 아니다
          withSetter._store 는 "proto store" 그대로
```

- ★★ `[5]` **윗집에 getter 만 있으면 엄격에서 `TypeError` 이고, 아무것도 섀도잉되지 않는다.**
  `c2` 의 own 키가 **빈 배열**이다. ★ setter 가 없으니 가져갈 사람도 없고, 그렇다고 own 을 만들지도 않는다 —
  **접근자 프로퍼티가 체인에 있다는 사실만으로 그 이름은 대입으로 막힌다.**
  ★★ 이것을 뚫는 유일한 길이 `[3]` 과 같은 `defineProperty` 다(동작 (5)의 `[1]` 이 그 실측이다).
- ★★ `[6]` **「있나」를 묻는 네 가지 창을 한 줄에 세웠다.**
  섀도잉 전에는 `'v' in o2` 만 `true` 이고 `Object.hasOwn`·`hasOwnProperty`·`Object.keys` 는 전부 `false`/`[]` 다.
  `o2.v = 2` 뒤에는 `hasOwn` 이 `true` 가 되고 `keys` 에 `"v"` 가 나타나며 **`p2.v` 는 `1` 그대로**다.
  ★ 13번의 「일곱 가지 뷰」 격자가 **체인 위에서 어떻게 보이는지**를 이 여섯 줄이 좁혀 보여 준다.

> **섀도잉(shadowing)** — 아래 칸의 같은 이름이 윗칸의 것을 **가려서** 안 보이게 하는 것.\
> 예: 덮어쓴 것이 아니라 가린 것이라서 **지우면 다시 드러난다**(`[1]` 의 마지막 줄).

**비용** — 섀도잉이 생겼을 때의 조회 비용 변화는 **재지 않았다.**

### (4) ★★★ 계단이 없는 집 · 이름이 같은 두 물건 · `new` 와 `instanceof`

**언제 쓰나** — `Object.create(null)` 을 만났을 때 · `prototype` 과 `[[Prototype]]` 이 헷갈릴 때 ·
`instanceof` 가 예상과 다른 답을 줄 때.

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

```text
===== node20 js12b-15d-misc.js (exit=0) =====
[1] Object.create(null) -- an object with no chain at all
typeof bare                             -> object
bare.toString                           -> undefined
bare.hasOwnProperty                     -> undefined
Object.keys(bare)                       -> ["k"]
Object.prototype.toString.call(bare)    -> [object Object]
JSON.stringify(bare)                    -> {"k":1}
String(bare)                            -> TypeError Cannot convert object to primitive value
bare + ''                               -> TypeError Cannot convert object to primitive value
`${bare}`                               -> TypeError Cannot convert object to primitive value
bare == '[object Object]'               -> TypeError Cannot convert object to primitive value
'k' in bare                             -> true
Object.hasOwn(bare, 'k')                -> true
console.log(bare) prints ->
[Object: null prototype] { k: 1 }
util.inspect(bare)       -> [Object: null prototype] { k: 1 }

[2] __proto__ is an accessor that LIVES ON Object.prototype -- so a bare object has none
descriptor on Object.prototype       get=function set=function e=false c=true
own.call(Object.prototype,'__proto__')  true
({}).__proto__ === Object.prototype    true
bare.__proto__ = {...} -> real proto?  still null
                       -> own keys     ["k","__proto__"]
                       -> bare.marker  undefined
setPrototypeOf on a normal object      M
Object.setPrototypeOf({}, 5)            -> TypeError Object prototype may only be an Object or null: 5
Object.getPrototypeOf(null)             -> TypeError Cannot convert undefined or null to object
Object.getPrototypeOf(5)                -> [object Number]

[3] what `new` links -- and what happens if you rewire .prototype afterwards
getPrototypeOf(i1) === Ctor.prototype   true
i1.constructor === Ctor                 true
own.call(i1, 'constructor')             false
hand-rolled new: same shape?            true
after reassigning Ctor.prototype:
  i1.hello()                            hi
  i2.hello                              undefined
  i2.note                               brand new prototype object
  i1 instanceof Ctor                    false
  i2 instanceof Ctor                    true
  i2.constructor.name                   Object

[4] instanceof walks the chain -- and Symbol.hasInstance can replace the walk
q instanceof Q / P / Object             true / true / true
same answer by hand (walk to null)      Q -> P -> Object
bare instanceof Object                  false
new Never() instanceof Never            false
'a string' instanceof Always            true
({}) instanceof {}                      -> TypeError Right-hand side of 'instanceof' is not callable
({}) instanceof (() => {})              -> TypeError Function has non-object prototype 'undefined' in instanceof check
Object.prototype.isPrototypeOf(q)       true
P.prototype.isPrototypeOf(q)            true
```

**그림 해설 — 네 덩어리를 따로 읽는다.**

#### `[1]` 계단이 아예 없는 객체

```text
   평범한 객체                          Object.create(null)

   o  ──▶ Object.prototype ──▶ null    bare ──▶ null
             │                                   ★ 첫 칸부터 없다
             ├ toString
             ├ hasOwnProperty
             ├ valueOf
             └ __proto__ (접근자)        bare 에는 이 넷이 전부 없다

   String(bare)   TypeError 로 막힌다  (원시값으로 바꿀 방법이 아예 없다)
   `${bare}`      TypeError 로 막힌다
   bare == '...'  TypeError 로 막힌다  (느슨한 비교도 원시값 변환을 시도한다)

   ★ 그런데 Object.prototype.toString.call(bare) 는 "[object Object]" 라고 답한다
     -- 그 함수를 "빌려서 부르면" 되기 때문이다. 창을 바꿔 물은 것이다
```

- ★★★ **`bare.toString` 과 `bare.hasOwnProperty` 가 둘 다 `undefined`** 다. 빌려 올 윗집이 없다.
- ★★★ **`String(bare)`·`bare + ''`·`` `${bare}` ``·`bare == '[object Object]'` 네 줄이 전부 `TypeError`** 다.
  ★ 넷째 줄이 특히 중요하다 — **느슨한 비교도 원시값 변환을 시도한다**(02번). 그래서 `==` 조차 터진다.
- ★★★ **그런데 `Object.prototype.toString.call(bare)` 는 `[object Object]` 라고 답한다.**
  객체 자신에게 물을 수 없을 뿐, **그 함수를 빌려다 부르면 된다.**
  ★★ **이것이 「창을 바꿔 물었다」(제5의 상태)의 실물이다** — 평소 창(`String`·`.toString()`)이 전부 닫혔고,
  **다른 창(브랜드 태그)으로 같은 질문에 답을 얻었다.**
  ★ 그 창이 못 보는 것도 적어 둔다 — 브랜드 태그는 **「무슨 종류인가」만** 말하고 **내용은 안 말한다.**
- ★★ **`Object.keys`·`JSON.stringify`·`in`·`Object.hasOwn` 은 전부 멀쩡히 돈다.**
  ★★★ **공통점이 있다 — 넷 다 「객체에게 메서드를 부르는」 것이 아니라 「객체를 인자로 받는」 것**이다.
  `bare` 에 대해 **정적 함수는 되고 메서드 호출은 안 된다** — 이 한 문장이 `Object.create(null)` 을 다루는 규칙이다.
- ★ **`console.log(bare)` 와 `util.inspect(bare)` 가 `[Object: null prototype] { k: 1 }` 로 찍는다.**
  ★★ **이 접두는 Node 가 정한 표기**다 — ECMA-262 밖이다. 「흔들리는 칸」 표에 그래서 넣었다.
  다만 실무에서는 **로그에서 이것을 보는 순간 체인이 없다는 것을 알아채는** 신호라 값이 크다.

#### `[2]` ★★★ `__proto__` 는 어디에 사는가

```text
   __proto__ 는 "모든 객체가 가진 마법 슬롯" 이 아니다.
   Object.prototype 에 놓인 접근자 프로퍼티 한 개다.

        Object.prototype
        ┌────────────────────────────────┐
        │ get __proto__()   ← 이 두 함수가 │   e=false  c=true
        │ set __proto__(v)     전부다      │
        └────────────────────────────────┘
                 ^
                 │ 평범한 객체는 여기까지 올라가서 그 접근자를 빌려 쓴다
        {} ──────┘

        bare ──▶ null        ★ 빌려 올 곳이 없다
        bare.__proto__ = {...}
             -> setter 가 없으므로 "평범한 own 데이터 프로퍼티" 가 하나 생긴다
             -> 프로토타입은 여전히 null 이다
```

- ★★★ **`Object.prototype` 의 `__proto__` 디스크립터가 `get=function set=function`** 이다.
  **데이터가 아니라 접근자**이고, `enumerable: false`·`configurable: true` 다.
- ★★★ **`bare.__proto__ = { marker: "M" }` 이 프로토타입을 못 바꾼다.**
  출력이 `still null` 이고, **own 키에 `"__proto__"` 가 평범하게 추가**됐으며(`["k","__proto__"]`),
  **`bare.marker` 는 `undefined`** 다.
  ★★★ **이것이 이 절의 급소다** — 같은 문장이 평범한 객체에서는 프로토타입을 바꾸고
  체인 없는 객체에서는 **그냥 키 하나를 만든다.** 에러도 경고도 없다.
  ★ 같은 이름의 **세 번째 얼굴**이 13번에 있다 — 객체 리터럴 안의 `{ __proto__: P }` 는
  접근자도 데이터도 아닌 **리터럴 문법**이다. **셋을 갈라 두지 않으면 이 자리를 절대 못 푼다.**
- ★★ **`Object.setPrototypeOf(viaSet, {...})` 는 평범한 객체에서 제대로 동작한다**(`marker` 가 `M`).
  ★ 그리고 **인자가 객체도 `null` 도 아니면 `TypeError`** 다(`Object prototype may only be an Object or null: 5`).
- ★ **`Object.getPrototypeOf(null)` 은 `TypeError`** 이고, **`Object.getPrototypeOf(5)` 는 `Number.prototype`** 을 답한다
  (브랜드 태그로 찍어 `[object Number]`). **원시값은 감싸서 답하고 `null` 은 못 감싼다.**
- ★★ **그래서 무엇을 쓰나** — 읽기는 **`Object.getPrototypeOf`**, 쓰기는 **`Object.setPrototypeOf`** 다.
  `__proto__` 는 **웹 호환용 유물**(Annex B)이고 **체인이 없는 객체에서 조용히 다른 일을 한다.**
  ★★★ **「`setPrototypeOf` 는 느리니 쓰지 마라」는 말은 여기 적지 않는다 — 안 쟀다.**

#### `[3]` ★★★ `prototype` 과 `[[Prototype]]` — 상자 셋

```text
   function Ctor() { ... }   이 한 줄이 만드는 것은 상자 둘이다

   ┌──────────────────────────┐         ┌──────────────────────────────┐
   │ 상자 1 : 함수 객체 Ctor   │         │ 상자 2 : Ctor.prototype      │
   │                          │         │                              │
   │  .prototype ─────────────┼────────▶│  constructor ────────────────┼──┐
   │  [[Prototype]] ──┐       │◀────────┼──────────────────────────────┘  │
   └──────────────────┼───────┘    이 화살표가 "constructor" 다            │
                      │                 └──────────────────────────────┘  │
                      v                        ^                          │
              Function.prototype               │ [[Prototype]]            │
                                               │                          │
                                     ┌─────────┴────────┐                 │
                                     │ 상자 3 : new Ctor │                │
                                     │  made : true     │                 │
                                     └──────────────────┘                 │
                                                                          │
   ★ 화살표가 주장하는 것                                                  │
     · Ctor.prototype  은 "Ctor 가 만들 인스턴스에게 줄 윗집" 이다  ────────┘
     · Ctor 의 [[Prototype]] 은 "Ctor 자신의 윗집" 이고 Function.prototype 이다
     · 두 화살표는 서로 다른 상자를 가리킨다 -> 같을 리가 없다
```

- ★★★ **`Ctor.prototype === Object.getPrototypeOf(Ctor)` 가 `false`** 다.
  이름이 비슷해서 헷갈릴 뿐 **아예 다른 두 슬롯**이다.
  - **`.prototype`** — **함수만 갖는 평범한 프로퍼티.** 「내가 만들 인스턴스에게 줄 윗집」을 담아 둔 상자다.
  - **`[[Prototype]]`** — **모든 객체가 갖는 내부 슬롯.** 「지금 나의 윗집」이다. `getPrototypeOf` 로만 읽는다.
- ★★★ **`Object.getPrototypeOf(new Ctor()) === Ctor.prototype` 이 `true`** 다.
  **`new` 가 하는 일이 정확히 이 연결**이다 — 전자의 상자를 후자의 슬롯에 꽂는다.
- ★★ **`Ctor.prototype` 의 own 키가 `["constructor"]`** 하나다. 그 화살표가 **도로 함수를 가리킨다.**
  ★ 그래서 `i1.constructor === Ctor` 가 `true` 인데 **`own.call(i1, 'constructor')` 는 `false`** 다 —
  인스턴스는 그것을 **빌려 볼 뿐**이다.
- ★★ **손으로 만든 `new` 가 진짜와 같은 모양을 낸다** —
  `Object.create(Ctor.prototype)` + `Ctor.call(manual)` 이 `true` 를 냈다.
  ★ **`new` 는 마법이 아니라 이 두 줄**이다(반환값 규칙 같은 나머지는 07번의 `new` 절이 정본이다).

#### `[3]` 이어서 — ★★ `.prototype` 을 갈아끼우면

```text
   Ctor.prototype 을 새 객체로 바꾸면

   시간 순서            Ctor.prototype 이 가리키는 곳       만들어진 인스턴스
   ───────────────────────────────────────────────────────────────────────
   ① i1 = new Ctor()   [ 상자 A ]  hello 가 있다     i1 ──▶ 상자 A
   ② Ctor.prototype = [ 상자 B ]  note 가 있다
   ③ i2 = new Ctor()                                 i2 ──▶ 상자 B

   i1.hello()          "hi"        ★ i1 의 윗집은 여전히 상자 A 다. 안 끊겼다
   i2.hello            undefined
   i2.note             "brand new prototype object"

   i1 instanceof Ctor  false   ★★★ 멀쩡히 돌던 객체가 false 가 됐다
   i2 instanceof Ctor  true
   i2.constructor.name "Object" ★ 상자 B 에 constructor 를 안 달아 줬다
```

- ★★★ **`i1 instanceof Ctor` 가 `false` 가 된다.** `i1` 은 아무것도 안 변했고 **`hello()` 도 여전히 돈다.**
  바뀐 것은 **`Ctor.prototype` 이 가리키는 곳**뿐이다.
  ★★★ **그래서 `instanceof` 는 「이 생성자로 만들어졌나」를 묻는 것이 아니다** —
  「**함수의 지금 `.prototype` 이 이 객체의 체인 위에 있나**」를 묻는다. **과거가 아니라 현재를 본다.**
- ★★ **`i2.constructor.name` 이 `Object`** 다. 새 프로토타입 객체(`{ note: ... }`)에 `constructor` 를 안 달았으므로
  그 이름은 **`Object.prototype` 에서 빌려 온 것**이다.
  ★★★ **`constructor` 는 자동으로 유지되는 것이 아니라 그냥 프로퍼티 하나**다 — 갈아끼우면 사라진다.
  타입 검사에 `constructor` 를 쓰면 안 되는 이유가 이 한 줄이다(정본은 34번).

#### `[4]` ★★ `instanceof` 가 보는 것 · `Symbol.hasInstance` 로 바꿔치기

- ★★ **`instanceof` 는 체인을 탄다.** `q instanceof Q / P / Object` 가 전부 `true` 이고,
  **손으로 `getPrototypeOf` 를 돌린 결과가 `Q -> P -> Object`** 로 같은 답을 낸다.
  ★ **둘이 같다는 것이 「`instanceof` 는 체인 순회다」의 증명**이다.
- ★★★ **`bare instanceof Object` 가 `false`** 다. `bare` 는 객체인데도 `false` 다 —
  체인이 없어 **`Object.prototype` 을 만날 수가 없기** 때문이다.
  ★ 그래서 **`instanceof Object` 를 「객체인가」의 검사로 쓰면 안 된다.** 정본은 34번이다.
- ★★ **`Symbol.hasInstance` 를 달면 체인 순회 자체가 안 일어난다.**
  `new Never() instanceof Never` 가 **`false`**(자기가 만든 것인데도),
  `'a string' instanceof Always` 가 **`true`**(원시값인데도)다.
  ★★★ **`instanceof` 는 언어가 고정한 검사가 아니라 바꿔치기 가능한 훅**이다.
- ★ **우변이 잘못됐을 때의 `TypeError` 가 두 종류**라는 것도 정보다 —
  `({}) instanceof {}` 는 **`Right-hand side of 'instanceof' is not callable`**(호출 가능하지 않다),
  `({}) instanceof (() => {})` 는 **`Function has non-object prototype 'undefined' in instanceof check`**
  (호출은 가능한데 `.prototype` 이 없다).
  ★★ **화살표 함수가 `.prototype` 을 안 만든다**는 `[3]` 의 사실이 여기서 에러 문구로 되돌아온다.
- ★ **`isPrototypeOf` 는 방향이 반대인 같은 질문**이다 — `P.prototype.isPrototypeOf(q)` 가 `true` 다.
  `instanceof` 는 **함수**를 우변에 놓고, `isPrototypeOf` 는 **프로토타입 객체 자신**을 주어로 놓는다.
  ★ `Symbol.hasInstance` 로 못 속이는 쪽이 이쪽이다.

### (5) ★★★ 파이썬 29번과의 대비 — 같은 집안인데 이기는 방향이 반대다

**언제 쓰나** — 파이썬을 먼저 배운 사람이 JS 의 체인을 읽을 때. **가장 많이 어긋나는 자리**다.

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

```text
===== node20 js12b-15e-pycontrast.js (exit=0) =====
[1] read -- does an own property beat an accessor on the prototype?
kid.v  (no own property yet)                      ACCESSOR on prototype
after defineProperty(kid, 'v')  -> kid.v          OWN data property
  own? / accessor still on proto?                 true / function
  accProto.v itself                               ACCESSOR on prototype

[2] write -- the accessor on the prototype takes it, so NO own property appears
kid2.v = 'written through'                        kid2.v = ACCESSOR on prototype
  own keys of kid2                                ["_viaSetter"]
  where did the value land?                       kid2._viaSetter = written through · accProto._viaSetter = undefined

[3] the same three cells for a PLAIN data property on the prototype
kid3.v  (before)                                  DATA on prototype   own? false
kid3.v = 'written through'                        written through   own? true
  dataProto.v                                     DATA on prototype

[4] the chain is made of OBJECTS, not classes -- two instances of one class
c1.shared / c2.shared                             on C.prototype / on C.prototype
getPrototypeOf(c1) === getPrototypeOf(c2)         true
getPrototypeOf(c1) === C.prototype                true
getPrototypeOf(c1) === C                          false
after c1.shared = 'own on c1' : c2.shared         on C.prototype
setPrototypeOf(c1, {...}) : c1 instanceof C       false
  c1.shared (own still wins)                      own on c1   own? true
  after delete c1.shared                          a different object entirely

[5] what JS does NOT have -- a per-property hook that beats an own property on READ
proto has get+set, leaf has own data -> leaf.v    own
is there any flag that flips this?                no -- ordinary [[Get]] returns at the first own hit
Proxy CAN do it, but that is a different object   PROXY wins
```

```text
   파이썬 (MRO -- 클래스를 탄다)              JS (체인 -- 객체를 탄다)

   obj                                        o
    │ type(obj)                                │ [[Prototype]]
    v                                          v
   [ 클래스 C ]                               [ 어떤 객체 ]
    │ MRO                                      │ [[Prototype]]
    v                                          v
   [ 클래스 B ]                               [ 어떤 객체 ]
    │                                          │
    v                                          v
   [ object ]                                  null

   ★ 왼쪽은 "인스턴스 -> 클래스" 로 종류가 바뀐다.
     오른쪽은 처음부터 끝까지 전부 그냥 객체다.
     getPrototypeOf(c1) === C.prototype  이고  === C  는 false

   ────────────────────────────────────────────────────────────────

   읽기에서 누가 이기나 -- 방향이 반대다

   파이썬                                     JS
   클래스 칸의 데이터 디스크립터              체인 위의 접근자(get + set)
        v 이긴다                                   v 진다
   인스턴스 칸의 값                           own 데이터 프로퍼티
                                                   ^ 이긴다

   파이썬 : vars(obj) 에 값이 보이는데 답은 클래스 쪽에서 나온다
   JS     : own 이 있으면 무조건 own 이 답한다. 뒤집을 플래그가 없다
```

**그림 해설.**

- ★★★ `[1]` **읽기에서 own 이 접근자를 이긴다.**
  `kid.v` 는 own 이 생기기 전에는 `ACCESSOR on prototype` 이고, `defineProperty` 로 own 을 만든 뒤에는
  **`OWN data property`** 다. ★★ **접근자는 그대로 프로토타입에 살아 있다**(`get` 이 여전히 `function` 이고
  `accProto.v` 자체는 여전히 접근자가 답한다). **가린 것이지 없앤 것이 아니다.**
  ★★★ **파이썬은 여기서 정반대다** —
  Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **29번**이
  「데이터 디스크립터 > 인스턴스 칸」을 실측으로 못 박아 두었다(그 편의 동작 7의 ①).
  거기서는 `vars(c)` 에 값이 **버젓이 있는데도** 클래스 쪽이 답한다.
- ★★★ `[2]` **쓰기에서는 JS 도 체인 쪽이 이긴다.**
  `kid2.v = 'written through'` 뒤에 **own 키가 `["_viaSetter"]`** 이고 **`v` 는 own 이 아니다.**
  값은 setter 가 `this._viaSetter` 로 옮겨 놓았고, `this` 가 수신자라 **`kid2._viaSetter`** 에 들어갔다
  (`accProto._viaSetter` 는 `undefined`).
  ★★★ **그리고 읽어 보면 `ACCESSOR on prototype` 이 돌아온다** — **쓴 값이 읽기로 안 돌아온다.**
  getter 가 `_viaSetter` 를 안 보기 때문이다. **에러도 경고도 없는 조용한 어긋남**이라 실무에서 가장 나쁘다.
- ★★★ **그래서 결론이 이 한 줄이다 — 「같은 집안인데 이기는 방향이 반대다.」**

| 묻는 것 | 파이썬(29번) | JS(이 주제) | 근거 |
|---|---|---|---|
| 사슬이 무엇으로 되어 있나 | **클래스**의 MRO | **객체**의 체인 | `[4]` — `getPrototypeOf(c1) === C.prototype` 이고 `=== C` 는 `false` |
| 사슬을 누가 계산하나 | 클래스를 **만들 때 C3 로 한 번** | 없다 — **객체마다 윗집 한 칸**만 있다 | `[4]` · 동작 (1)의 19줄 |
| 읽기에서 **own/인스턴스 칸**이 이기나 | ★ **진다**(데이터 디스크립터에게) | ★★★ **무조건 이긴다** | `[1]` · `[5]` |
| 읽기에서 그것을 뒤집는 플래그 | `__set__` 의 유무 | ★★★ **없다** | `[5]` |
| 쓰기에서 사슬이 끼어드나 | 끼어든다(`__set__`) | ★ **끼어든다**(setter) | `[2]` · 동작 (3)의 `[4]` |
| 쓸 때 `this`/`self` 는 누구인가 | 인스턴스 | **수신자** | 동작 (2)의 `[4]` · 동작 (3)의 `[4]` |
| 사슬을 나중에 갈아끼울 수 있나 | 어렵다(클래스 구조) | ★ **된다**(`setPrototypeOf`) | `[4]` |
| 못 찾으면 | `AttributeError` | ★★ **`undefined`** | 동작 (2)의 `C.nope` |

- ★★★ `[5]` 「**읽기에서 own 을 이기는 훅이 JS 에는 없다**」가 이 대비의 결론이다.
  프로토타입에 `get` 과 `set` 을 **둘 다** 달아 두고 자식에 own 데이터를 꽂아도 **`own` 이 답한다.**
  ★★ **`Proxy` 는 반례가 아니다** — 같은 줄에서 `PROXY wins` 가 나오지만 그것은 **다른 객체**다.
  파이썬의 데이터 디스크립터는 **같은 객체**에 다는 훅이고, `Proxy` 는 **객체를 하나 더 만들어 앞에 세우는 것**이다.
  ★ 그래서 **원래 객체를 들고 있는 코드에는 아무 효과가 없다.**
  (스크립트가 찍는 `no -- ordinary [[Get]] returns at the first own hit` 는 **라벨 문자열**이고,
  근거는 그 위의 `leaf.v` 가 `own` 이라는 줄과 `[1]` 이다.)
- ★★ `[3]` 이 **대조군**이다 — 프로토타입 쪽이 **평범한 데이터 프로퍼티**면 쓰기가 own 을 만들고
  `dataProto.v` 는 그대로다. `[2]` 와 나란히 놓으면 **갈리는 것이 「접근자인가」 하나뿐**임이 보인다.
- ★★ `[4]` **체인은 객체로 되어 있다**를 네 줄로 못 박는다.
  `getPrototypeOf(c1) === getPrototypeOf(c2)` 가 `true`(두 인스턴스가 **한 객체를 같이 본다**),
  `=== C.prototype` 이 `true`, **`=== C` 가 `false`** 다.
  ★★★ **`C` 라는 클래스는 체인 위에 없다** — 체인 위에 있는 것은 `C.prototype` 이라는 **평범한 객체**다.
  ★ `setPrototypeOf(c1, {...})` 로 갈아끼우면 **`c1 instanceof C` 가 `false`** 가 되고,
  own 이 있는 동안은 여전히 own 이 이기며, `delete` 하자 **새 윗집의 값**이 나온다.
  **사슬을 런타임에 바꿀 수 있다는 것**이 파이썬 MRO 와 가장 다른 성질이다.

### (6) ★ 같은 질문을 브라우저에 던지면

```text
===== google-chrome --headless --dump-dom js12b-page.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g' (exit=0) =====
  engine                                Chrome/151.0.0.0
  12  0 ?? 'D' / 0 || 'D'               [0,"D"]
  12  ||= does not write                []
  12  = x || y writes                   ["set"]
  12  a?.b[f()] skips f                 calls 0
  12  a ?? b || c compiles?             SyntaxError: Unexpected token '||'
  12  new a?.b() compiles?              SyntaxError: Invalid optional chain from new expression
  13  enumeration order                 ["1","2","b","a","01","Symbol(s)"]
  13  '4294967295' is an index?         ["a","4294967295","z"]
  13  computed key calls toString       ["K"] ["toString"]
  13  __proto__ literal vs computed     true,false
  14  literal vs defineProperty desc    {"value":1,"writable":true,"enumerable":true,"configurable":true} | {"value":1,"writable":false,"enumerable":false,"configurable":false}
  14  isFrozen {} / prevExt {}          [false,true]
  14  freeze is shallow                 {"d":{"n":2}}
  14  strict write to frozen            TypeError: Cannot assign to read only property 'a' of object '#<Object>'
  15  chain of new TypeError            TypeError -> Error -> Object -> null
  15  String(Object.create(null))       TypeError: Cannot convert object to primitive value
  15  write does not walk               o/p/own:true
  15  non-writable proto blocks         TypeError: Cannot assign to read only property 'v' of object '#<Object>'
  15  Symbol.hasInstance overrides      true
```

★★ **호스트가 정하는 칸이 하나도 없었다.** 15번의 다섯 줄이 전부 Node 쪽과 같다 —
`new TypeError` 의 체인 `TypeError -> Error -> Object -> null` · `String(Object.create(null))` 의 `TypeError` ·
쓰기가 own 을 만드는 것(`o/p/own:true`) · 체인 위 비쓰기에서의 `TypeError` · `Symbol.hasInstance` 의 `true`.
★ **예외 문구까지 같은 것은 둘 다 V8 이기 때문**이지 명세가 정한 것이 아니다.
★★ 다만 **한 줄의 라벨이 거칠다** — 탐침의 이름이 `15 write does not walk` 인데,
동작 (2)의 `[3]` 이 보인 정확한 사실은 「**탐색은 걷고 저장만 수신자에 내려앉는다**」이다.
**라벨은 브리핑의 거친 요약이고 로그가 더 정확하다.**

## 문법 — 형태와 규칙

```text
   체인을 만드는 법 · 읽는 법 · 바꾸는 법

   만들기
   Object.create(P)            [[Prototype]] 이 P 인 새 객체
   Object.create(null)         체인이 없는 객체
   new Ctor()                  [[Prototype]] 이 Ctor.prototype 인 새 객체
   { __proto__: P }            리터럴 문법 (Annex B) -- 13번 주제
   class B extends A { }       B.prototype -> A.prototype  그리고  B -> A

   읽기
   Object.getPrototypeOf(o)    ★ 표준 창
   o.__proto__                 Object.prototype 의 접근자 (Annex B)
   P.isPrototypeOf(o)          P 가 o 의 체인 위에 있나
   o instanceof F              F.prototype 이 o 의 체인 위에 있나

   바꾸기
   Object.setPrototypeOf(o, P) ★ 표준 창. P 가 객체도 null 도 아니면 TypeError
   o.__proto__ = P             ★ 체인 없는 객체에서는 그냥 키가 하나 생긴다

   묻기
   'x' in o                    체인을 탄다
   Object.hasOwn(o, 'x')       첫 칸만 본다   (ES2022)
   o.hasOwnProperty('x')       같은 질문인데 ★ 체인으로 빌려 오는 호출이다
```

- **읽기(`[[Get]]`)는 체인을 타고, 찾는 순간 멈추며, 끝까지 없으면 `undefined` 다.** 예외가 아니다.
- ★★★ **쓰기(`[[Set]]`)도 체인을 타지만, 값이 놓이는 자리는 언제나 수신자다.**
  체인을 타는 이유는 **가로챌 것이 있나 보려는 것**이고, 없으면 수신자에 own 이 생긴다.
- **쓰기가 체인 쪽에 걸리는 경우는 셋뿐이다** —
  ① **setter 가 있다** → 그것이 불리고 own 이 안 생긴다. `this` 는 **수신자**다.
  ② **비쓰기 데이터 프로퍼티가 있다** → 엄격에서 `TypeError`, own 도 안 생긴다.
  ③ **getter 만 있다** → 엄격에서 `TypeError`, own 도 안 생긴다.
- **`defineProperty` 는 이 셋을 전부 통과한다.** 대입과 정의는 다른 문이다.
- **`.prototype` 은 함수의 평범한 프로퍼티이고, `[[Prototype]]` 은 모든 객체의 내부 슬롯이다.** 둘은 다른 것이다.
- **`new` 가 하는 연결은 「함수의 현재 `.prototype` 을 새 객체의 `[[Prototype]]` 에 꽂는 것」이다.**
- **`instanceof` 는 함수의 현재 `.prototype` 을 체인에서 찾는다.** `Symbol.hasInstance` 가 있으면 **그것이 전부 한다.**
- **`__proto__` 는 `Object.prototype` 에 사는 접근자다.** 체인이 없는 객체에는 **아예 없다.**
- **`Object.create(null)` 인 객체에는 메서드를 못 부른다.** 정적 함수(`Object.keys`·`JSON.stringify`·`in`·`hasOwn`)는 된다.

## 어디서 틀리나

### (1) ★★★ 「쓰기는 체인을 안 탄다」로 외운다

**거친 요약이다.** 트랩 로그가 `["C.set","B.set","A.set","C.gopd"]` 로 **체인을 끝까지 걸었다는 것**을 보인다.
★★★ 정확히는 — **탐색은 걷고, 저장만 수신자에 내려앉는다.**
★ 왜 이 정밀화가 중요한가 — **거친 요약으로는 setter·비쓰기·getter-only 세 예외를 설명할 수 없기 때문**이다.
「안 탄다」가 사실이라면 그 셋이 왜 끼어드는지 말이 안 된다.

### (2) ★★★ 프로토타입에 가변 객체를 올려 둔다

`shared = { list: [] }` 를 윗집에 두면 **모든 자식이 그 배열 한 개**를 본다.
`x.list.push(...)` 는 **own 을 안 만들고 그 한 개를 늘린다** — `y.list` 에도 보인다.
★★ **증상과 진단이 어긋난다** — 값은 자기 것처럼 보이는데 `Object.hasOwn` 은 `false` 다.
★ 바로 옆의 `x.count += 1` 은 **대입이라 own 을 만든다.** 한 객체 안에서 **두 규칙이 섞인다.**
★ 고치는 법은 한 줄 — **가변 상태는 생성자/`__init__` 자리에서 인스턴스마다 만든다.**
파이썬 29번의 「가변 클래스 변수」와 **같은 집안이고 처방도 같다.**

### (3) ★★★ `prototype` 과 `[[Prototype]]` 을 같은 것으로 읽는다

`Ctor.prototype === Object.getPrototypeOf(Ctor)` 는 **`false`** 다.
★ 이름이 비슷할 뿐 한쪽은 「**내가 만들 것에게 줄 윗집**」, 한쪽은 「**지금 나의 윗집**」이다.
★★ 인스턴스에는 **`.prototype` 이 아예 없다**(`"prototype" in inst` 가 `false`) — 이것이 가장 빠른 판별이다.

### (4) ★★★ `bare.__proto__ = X` 로 프로토타입을 바꾸려 한다

`Object.create(null)` 인 객체에는 **그 접근자가 없다.** 그래서 **평범한 own 키가 하나 생기고 프로토타입은 `null` 그대로**다.
**에러도 경고도 없다.** ★★★ 같은 문장이 평범한 객체에서는 성공하고 여기서는 조용히 다른 일을 한다.
★ 처방 — **`Object.setPrototypeOf` 를 쓴다.** 읽기도 **`Object.getPrototypeOf`** 다.

### (5) ★★ `Object.create(null)` 을 문자열에 섞거나 `==` 로 비교한다

`String(bare)`·`` `${bare}` ``·`bare + ''` 는 물론 **`bare == '[object Object]'` 까지 `TypeError`** 다.
★ 로그 한 줄이 서비스를 세울 수 있다. ★★ **읽기용 덤프는 `JSON.stringify`** 를 쓰고,
「무슨 물건인가」는 **`Object.prototype.toString.call`** 로 묻는다.
★ 그리고 `bare.hasOwnProperty(...)` 도 못 쓴다 — **`Object.hasOwn`** 이 정답이다.

### (6) ★★ `instanceof` 를 「이 생성자로 만들었나」로 읽는다

**아니다.** `.prototype` 을 갈아끼우면 **멀쩡히 돌던 `i1` 이 `false`** 가 된다.
★★★ **`instanceof` 는 과거가 아니라 「함수의 지금 `.prototype`」을 본다.**
★ `bare instanceof Object` 가 `false` 인 것도 같은 규칙의 결과다 — **체인에 `Object.prototype` 이 없다.**
★ `Symbol.hasInstance` 를 달면 답이 통째로 바뀐다. **믿을 수 있는 검사가 아니다**(정본은 34번).

### (7) ★★ 체인 위의 세 예외를 모른 채 「대입했으니 됐다」고 믿는다

- **setter** — 값이 **다른 이름**으로 가고 `s` 는 own 이 안 된다. ★ 심하면 **읽기로 안 돌아온다**(동작 (5)의 `[2]`).
- **비쓰기 데이터** — 엄격에서 `TypeError`, 비엄격에서는 **조용히 무시**된다(14번 격자의 `proto has non-writable a`).
- **getter-only** — 엄격에서 `TypeError`, own 이 **하나도 안 생긴다**.

★★ **셋 다 「대입 뒤에 다시 읽어 확인한다」로 잡힌다.** 12번·14번에서 반복해 나온 그 처방이 여기서도 유효하다.

### (8) ★★ `constructor` 로 타입을 검사한다

**`constructor` 는 자동으로 유지되는 것이 아니라 프로토타입 객체의 평범한 프로퍼티 하나**다.
`.prototype` 을 갈아끼우고 다시 안 달면 **`i2.constructor.name` 이 `Object`** 가 된다.
★ 이것이 「`Child.prototype = Object.create(Parent.prototype)` 뒤에 `constructor` 를 다시 달아 주라」는
낡은 관용구의 이유이고, **`class` 문법이 그 손질을 없앤 이유**이기도 하다(16번).

### (9) ★★ `o.hasOwnProperty('x')` 를 안전한 검사로 쓴다

**그 호출 자체가 체인을 타고 빌려 오는 것**이다. 그래서 두 가지로 깨진다 —
**체인이 없으면**(`Object.create(null)`) `undefined` 라 호출이 터진다 — 그 줄은 실측했다.
★ 그리고 **`hasOwnProperty` 라는 이름이 섀도잉되어 있으면** 엉뚱한 함수가 불린다 —
이쪽은 **따로 안 던져 봤고**, 동작 (3)의 섀도잉 규칙에서 따라 나오는 결론이다.
★ 처방 — **`Object.hasOwn(o, 'x')`**(ES2022), 또는 `Object.prototype.hasOwnProperty.call(o, 'x')`.

### (10) ★ `in` 과 `Object.hasOwn` 을 같은 질문으로 읽는다

`'fromA' in C` 는 `true` 이고 `Object.hasOwn(C, 'fromA')` 는 `false` 다.
★ 트랩 로그가 그 차이를 그대로 보인다 — **`has` 3줄 대 `gopd` 1줄.**
★★ **어느 쪽이 맞는지는 묻는 사람이 정한다** — 「쓸 수 있나」면 `in`, 「이 객체의 것인가」면 `hasOwn` 이다.

### (11) ★ 「`setPrototypeOf` 는 느리다」를 근거 없이 옮긴다

★★★ **이 문서는 그 말을 하지 않는다 — 안 쟀기 때문이다.**
★ 말할 수 있는 것은 **의미**뿐이다 — `setPrototypeOf` 는 **살아 있는 객체의 사슬을 갈아끼워**
`instanceof` 의 답까지 바꾼다(동작 (5)의 `[4]`). **그것만으로도 놀라움이 크다는 것이 안 쓸 이유**이고,
속도는 **별도의 측정이 필요한 다른 주장**이다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **읽기가 체인을 타고 찾는 순간 멈추는 것** · **끝까지 없으면 `undefined` 인 것.**
- ★★★ **쓰기가 체인을 타되 값이 수신자에 놓이는 것** — 그리고 **윗칸의 값이 안 바뀌는 것.**
- ★★★ **체인 위의 setter 가 쓰기를 가져가고 그 안의 `this` 가 수신자인 것.**
- **체인 위의 비쓰기 데이터 프로퍼티와 getter-only 가 대입을 막는 것**(엄격에서 `TypeError`, 비엄격에서 조용한 실패).
- **`defineProperty` 가 그 셋과 무관하게 그 객체에 바로 정의하는 것.**
- **`Object.create(null)` 의 `[[Prototype]]` 이 `null` 인 것** · **그 객체를 원시값으로 못 바꾸는 것.**
- **`Object.prototype.toString.call` 이 브랜드 태그를 답하는 것**(`[object Object]`).
- **`__proto__` 가 `Object.prototype` 의 접근자인 것**(Annex B — 규범적 선택 사항이지만 웹 엔진 전부가 구현한다).
- **`Object.setPrototypeOf` 가 객체도 `null` 도 아닌 인자에서 `TypeError` 인 것.**
- **`Object.getPrototypeOf(null)` 이 `TypeError` 이고 원시값은 감싸서 답하는 것.**
- **`new` 가 함수의 **현재** `.prototype` 을 꽂는 것** · **`instanceof` 가 그 현재 값을 체인에서 찾는 것.**
- **`Symbol.hasInstance` 가 있으면 그것이 `instanceof` 를 전부 대신하는 것.**
- **`in` 이 체인을 타고 `Object.hasOwn` 이 own 만 보는 것.**
- **`class B extends A` 가 `B.prototype -> A.prototype` 과 `B -> A` 두 연결을 만드는 것.**

### 엔진(V8) 구현 · 이 판의 관찰

- **예외 문구 전부** — `Cannot assign to read only property 'v' of object '#<Object>'` ·
  `Cannot set property s of #<Object> which has only a getter` ·
  `Cannot convert object to primitive value` ·
  `Object prototype may only be an Object or null: 5` ·
  `Cannot convert undefined or null to object` ·
  `Right-hand side of 'instanceof' is not callable` ·
  `Function has non-object prototype 'undefined' in instanceof check`.
  **종류(`TypeError`)만 명세가 정한다.**
- **`GeneratorFunction`·`AsyncFunction` 이라는 이름이 `constructor.name` 으로 읽히는 것** —
  그 내장 객체들은 전역에 노출되지 않는데 **이름은 그대로 읽힌다.** 이 판의 관찰로 적는다.
- **`(anonymous [object Object])` 라는 표기는 우리 스크립트가 지은 것**이다. 엔진의 출력이 아니다.
- **두 판(18·20)과 Chrome 151 이 이 주제에서 한 글자도 안 갈렸다** — 셋 다 V8 이기 때문이지 보장이 아니다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★ **`console.log(bare)` 와 `util.inspect(bare)` 가 찍는 `[Object: null prototype]` 접두** —
  **Node 의 표기**다. 브라우저 콘솔은 다르게 그린다.
  ★ 그래도 **실무 가치가 큰 신호**라 본문에 살려 두되, 「흔들리는 칸」에 넣었다.
- 그 밖에 **이 주제의 브라우저 대조에서 호스트가 정하는 칸은 0개**였다.

### 그래서 이렇게 적으면 틀린다

- 「쓰기는 체인을 안 탄다」 — **거칠다.** 탐색은 탄다. 저장만 수신자다. 로그 넷째 줄이 그 증거다.
- 「`__proto__` 는 모든 객체가 가진 슬롯이다」 — **아니다.** `Object.prototype` 의 접근자이고,
  **체인이 없는 객체에는 아예 없다.**
- 「`instanceof` 는 이 생성자로 만들었는지 본다」 — **아니다.** **함수의 지금 `.prototype`** 을 본다.
- 「`Object.create(null)` 은 그냥 더 안전한 `{}` 다」 — **안전의 종류가 다르다.**
  프로토타입 오염은 막지만 **문자열로 못 바꾸고 메서드도 못 부른다.**
- 「`setPrototypeOf` 는 느리다」 — ★★★ **안 쟀다.** 이 문서에 속도 주장이 한 줄도 없다.
- 「파이썬처럼 클래스 쪽이 이긴다」 — **반대다.** JS 는 **읽기에서 own 이 무조건 이긴다.**
- 「`constructor` 로 타입을 알 수 있다」 — **아니다.** 갈아끼우면 `Object` 가 된다.

## 언제 쓰고 언제 안 쓰나

- **`class`** — 체인을 만드는 **기본 선택**이다. `.prototype` 손질과 `constructor` 다시 달기를 전부 없애 준다(16번).
- **`Object.create(P)`** — **한 객체의 윗집을 직접 정할 때.** 프로토타입 실험과 가벼운 위임에 맞는다.
- **`Object.create(null)`** — ★ **키가 사용자 입력인 사전**에 쓴다. `"__proto__"`·`"toString"` 같은 키가 들어와도
  안전하고, 체인을 안 타니 「있나」 검사가 정직해진다.
  ★★ **대신 그 객체를 절대 문자열에 섞지 않는다**는 규칙을 같이 세워야 한다.
- **`Object.setPrototypeOf`** — ★ **이미 만들어진 객체의 사슬을 바꿔야만 할 때.**
  `instanceof` 의 답까지 바뀌므로 **놀라움이 크다.** 만들 때 정할 수 있으면 `Object.create` 쪽이다.
- **프로토타입에 올릴 것** — ★★ **메서드처럼 불변인 것만.** 가변 객체는 **전부가 한 개를 같이 쓴다.**
- **`instanceof`** — 같은 realm 안에서 **내가 만든 클래스 계층**을 물을 때만.
  ★ 라이브러리 경계·`iframe`·프로토타입 조작이 섞이면 34번의 다른 검사를 쓴다.
- **안 쓸 자리** — `__proto__`(읽기도 쓰기도) · `o.hasOwnProperty(...)` 직접 호출 · `constructor` 로 하는 타입 검사.

## 핵심 문장

1. ★★★ **읽기는 체인을 타고 찾는 순간 멈추며, 끝까지 없으면 예외가 아니라 `undefined` 다.**
   그리고 **어느 칸에서 왔는지는 값으로 원리상 못 가른다** — 트랩 로그만이 말한다.
2. ★★★ **쓰기도 체인을 타지만 값이 놓이는 자리는 수신자다.**
   로그 `["C.set","B.set","A.set","C.gopd"]` 에서 **넷째 줄이 되돌아온 발자국**이다.
3. ★★★ **쓰기가 체인 쪽에 걸리는 경우는 셋뿐이다** — setter · 비쓰기 데이터 · getter-only.
   그리고 **setter 안의 `this` 는 수신자**라 값이 자식에 생긴다(07번의 암시적 바인딩).
4. ★★★ **`prototype` 은 함수의 프로퍼티이고 `[[Prototype]]` 은 모든 객체의 슬롯이다.**
   `new` 가 앞엣것을 뒤엣것에 꽂고, `instanceof` 는 **함수의 지금 `.prototype`** 을 체인에서 찾는다.
5. ★★★ **파이썬과 이기는 방향이 반대다** — 파이썬은 **읽기에서 클래스 쪽(데이터 디스크립터)이 이기고**,
   JS 는 **읽기에서 own 이 무조건 이긴다.** 대신 **쓰기에서는 둘 다 사슬 쪽이 가져간다.**

## 관련 자료

- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) —
  **그쪽이 `__proto__:` 리터럴 다섯 형태의 정본**이다. 여기는 **`Object.prototype` 의 접근자 쪽**부터.
- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) —
  **그쪽이 「무엇이 쓰기를 막나」와 엄격/비엄격 격자의 정본**이다. 여기는 **막는 것이 체인 위에 있을 때**까지.
- [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) —
  **그쪽이 `this` 판정의 정본**이다. 여기는 **체인 위 setter 안의 `this` 가 수신자라는 사실**만 받아 쓴다.
- [12 — 옵셔널 체이닝·널 병합·논리 할당](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) —
  **없는 프로퍼티가 `undefined` 라는 사실 위에 `?.` 가 선다.** 그쪽이 `?.` 의 정본이다.
- [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) —
  **그쪽이 원시값의 임시 래핑 정본**이다. 여기는 **그 래퍼의 체인이 무엇인가**까지.
- 목록의 **16번 주제** 「`class` 문법」 — **그쪽이 필드·정적 멤버·프라이빗 `#` 이 어디에 붙나의 정본**이다.
  여기는 **`extends` 가 체인을 두 줄 만든다**는 사실까지.
- 목록의 **17번 주제** 「상속과 `super`」 — **그쪽이 `super`·`new.target`·내장 상속 제약의 정본**이다.
- 목록의 **18번 주제** 「`for...in` 과 열거」 — **그쪽이 체인 순회 열거의 정본**이다.
- 목록의 **34번 주제** 「타입 검사 관용구」 — **그쪽이 어느 검사가 언제 깨지나의 정본**이다.
  여기는 **`instanceof` 가 무엇을 보나**까지.
- 목록의 **45번 주제** 「`Proxy`」 — **그쪽이 트랩 계약의 정본**이다. 여기서는 **로그 도구로만** 썼다.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **29번** —
  ★★★ **이 주제의 대비축.** 파이썬은 **클래스의 MRO** 를 타고 JS 는 **객체의 체인**을 탄다.
  그리고 **읽기에서 이기는 방향이 반대**다. 자세한 대비는 동작 (5)의 표에 있다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **09번** —
  자바는 **단일 상속에 컴파일 시점 결정**이라 런타임에 사슬을 갈아끼울 수 없다. JS 와 가장 먼 자리다.

## 용어 풀이

- **프로토타입(prototype)** — 어떤 객체가 「없으면 여기」라고 가리키는 다른 객체.
- **`[[Prototype]]`** — 그 가리킴을 담은 **내부 슬롯.** `Object.getPrototypeOf` 로만 정식으로 읽는다.
- **`.prototype`** — **함수가 갖는 평범한 프로퍼티.** 「내가 만들 인스턴스에게 줄 윗집」을 담는다.
  ★ 화살표 함수와 메서드 단축에는 없다.
- **프로토타입 체인(prototype chain)** — `[[Prototype]]` 을 따라가 `null` 에서 끝나는 사슬.
- **own 프로퍼티(own property)** — 빌려 온 것이 아니라 **그 객체 자신의** 프로퍼티.
- **섀도잉(shadowing)** — 아래 칸의 같은 이름이 윗칸의 것을 **가리는** 것. 덮는 것이 아니라 가리는 것이다.
- **수신자(receiver)** — 점 왼쪽에 있던, **처음 요청을 받은 객체.** 쓰기가 내려앉는 자리이고 setter 안의 `this` 다.
- **접근자 프로퍼티(accessor property)** — 값 대신 `get`/`set` 함수를 들고 있는 프로퍼티.
- **setter** — 대입할 때 대신 불리는 함수. 체인 위에 있으면 **쓰기를 가져간다.**
- **비쓰기 데이터 프로퍼티(non-writable)** — `writable: false` 인 값 프로퍼티. 체인 위에 있으면 대입을 막는다.
- **`Object.create(P)`** — `[[Prototype]]` 이 `P` 인 새 객체를 만든다. `P` 가 `null` 이면 체인이 없다.
- **`__proto__`** — `Object.prototype` 에 사는 **접근자 프로퍼티**(Annex B). 체인 없는 객체에는 **없다.**
- **브랜드 태그(brand tag)** — `Object.prototype.toString.call(x)` 가 답하는 `[object …]` 문자열.
  **다른 창이 닫혔을 때 쓰는 마지막 창**이다.
- **`instanceof`** — 「우변 함수의 **현재** `.prototype` 이 좌변의 체인 위에 있나」를 묻는 연산자.
- **`Symbol.hasInstance`** — 그 질문 자체를 통째로 바꿔치기하는 훅.
- **`isPrototypeOf`** — 같은 질문을 **프로토타입 객체 쪽에서** 묻는 메서드.
- **`Proxy` 트랩(trap)** — 내부 동작을 가로채는 갈고리. 이 주제에서는 **로그를 심는 도구**로만 썼다.
- **MRO(파이썬)** — 클래스의 조상을 훑을 순서를 한 줄로 편 것. **JS 에는 없는 개념**이다.
- **데이터 디스크립터(파이썬)** — `__get__` 과 `__set__` 을 함께 가진 것. **인스턴스 칸을 이긴다** — JS 와 반대다.

## 더 들어가면

- **`Object.create(null)` 이 실무에서 진짜로 쓰이는 자리**는 「**키가 사용자 입력인 사전**」이다.
  평범한 객체에서는 `obj["toString"]` 이 **함수를 답하고** `"constructor" in obj` 가 **`true`** 라
  「없는 키」를 물었는데 있다고 답한다. 체인을 끊으면 그 거짓말이 사라진다.
  ★ 그 대가가 이 문서의 `[1]` 블록 전체다 — **메서드를 못 부른다.**
- **`Object.hasOwn` 이 ES2022 에 들어온 이유**가 이 주제 안에 있다.
  `o.hasOwnProperty(...)` 는 **체인으로 빌려 오는 호출**이라 두 가지로 깨지고,
  그래서 다들 `Object.prototype.hasOwnProperty.call(o, k)` 라는 긴 관용구를 썼다.
  **정적 함수로 승격시킨 것**이 `Object.hasOwn` 이다 — **체인 문제를 체인 밖으로 꺼내는 처방**이다.
- **`Symbol.hasInstance` 가 있다는 사실이 「타입 검사」의 성격을 바꾼다.**
  `instanceof` 는 **언어가 고정한 사실이 아니라 객체가 대답하는 질문**이다.
  그래서 「어떤 검사가 프로토타입 조작에서 깨지나」가 34번의 주제가 된다.
- **파이썬 29번과의 대비에서 안 다룬 축이 둘 더 있다** —
  ① 파이썬의 `__getattr__`(못 찾았을 때 불리는 갈고리)에 해당하는 것이 JS 에는 **평범한 객체에 없다.**
  `Proxy` 의 `get` 트랩이 가장 가깝지만 **다른 객체**다.
  ② 파이썬의 `__slots__` 처럼 **칸 자체를 없애는 장치**도 JS 에는 없다.
  `Object.preventExtensions`·`seal`·`freeze` 는 **칸을 못 늘리게** 할 뿐 구조를 바꾸지 않는다(14번).
  ★ **둘 다 이번에 안 돌려 봤다** — 대비축을 넓히려면 탐침이 더 필요하다.
- **`class` 가 만드는 체인 두 줄은 16·17번의 출발점이다.**
  `B.prototype -> A.prototype`(인스턴스 메서드)와 `B -> A`(정적 멤버)를 갈라 두지 않으면
  「정적 메서드가 왜 상속되지?」에서 막힌다. 이 문서는 **그 두 줄이 있다는 것**까지만 책임진다.
