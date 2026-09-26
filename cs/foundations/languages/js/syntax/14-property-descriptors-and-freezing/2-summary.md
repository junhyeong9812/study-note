# js/syntax/14 — 프로퍼티 디스크립터와 동결: 「막힌 것은 값이 아니라 플래그에 적혀 있다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다. 그리고 그 격자의 눈금이 `getOwnPropertyDescriptor` 덤프다.**
> 「이 프로퍼티는 무엇이 막혀 있나」는 **값을 아무리 읽어도 안 보인다** — `o.a` 는 막혔든 안 막혔든 `1` 이다.
> 보이는 곳은 **디스크립터의 세 플래그**(`writable`·`enumerable`·`configurable`) 하나뿐이고,
> 「그래서 무엇이 되고 무엇이 안 되나」는 **그 세 플래그의 조합을 전부 던져 본 격자**로만 나온다.
> 이 문서의 격자는 셋이다 — **설정 불가 27칸** · **세 봉인 함수 24칸** · **엄격/비엄격 13칸**.
> ★★ **④ 예외의 `constructor.name` + `message`** 는 이 주제에서 「**엄격 모드에서만 열리는 창**」이다.
> 비엄격에서는 **막힌 쓰기가 예외도 경고도 없이 조용히 버려진다** — 그때는 창이 닫힌다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — Property Descriptor · `Object.defineProperty` · `Object.freeze`/`seal`/`preventExtensions` · `ValidateAndApplyPropertyDescriptor` · `OrdinarySet`
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — **`defineProperty`·`getOwnPropertyDescriptor`·세 봉인 함수·세 술어 여덟 개가 ES5 판에 이미 다 있다**는 것과, **복수형 `getOwnPropertyDescriptors` 만 ES2017** 이라는 것을 가릴 때 열었다
> - [MDN — Object.defineProperty](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/defineProperty) · [MDN — Object.freeze](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/freeze)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **플래그 값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
>
> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박혀 다른 머신에서 재현이 안 되기 때문이다.
> ★★ **이 문서의 모든 블록은 표준 출력뿐이다** — 표준 오류와 섞은 블록이 하나도 없다.
> ★★★ **격자 두 개는 통째로 `"use strict"` 아래에서 돌렸다.** 비엄격에서는 막힌 칸이 **`OK` 로 보이기** 때문에
> 격자를 읽을 수가 없다. 「모드가 무엇을 바꾸나」는 따로 세 번째 격자에서 잰다.
>
> **버전** — **세 플래그·`defineProperty`·`getOwnPropertyDescriptor`·`freeze`/`seal`/`preventExtensions`·`isFrozen`/`isSealed`/`isExtensible` 은 전부 ES5** 다.
> **복수형 `Object.getOwnPropertyDescriptors` 는 ES2017**, **`Reflect.defineProperty`·`Reflect.getOwnPropertyDescriptor` 는 ES2015** 다.
> ★ 아래 격자에 한 줄 섞여 있는 `Array.prototype.toSorted` 는 **ES2023** 라 **v18 에 없다.**
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | `configurable:false` **27칸** · 세 봉인 함수 **6연산 × 4상태 = 24칸** · 엄격/비엄격 **13칸** |
> | ★★★ **디스크립터 덤프**(이 주제 고유의 창 — 격자의 눈금) | `getOwnPropertyDescriptor` 가 **값에 안 보이는 세 플래그**를 표로 꺼낸다. 이 창이 없으면 격자의 칸에 이름을 못 붙인다 |
> | ★★ **④ 예외의 `constructor.name` + `message`** | **엄격 모드에서만 열린다.** `TypeError` 의 종류가 「무엇이 막혔나」를 가른다 |
> | ★★ **두 번 컴파일**(엄격 먼저 / 비엄격 나중) | **설정에 달린 칸이 몇 개인가** — 13칸 중 **9칸**이었다. 이 배치 네 주제 중 **가장 크게 갈린다** |
> | ★★★ **⑤ 두 판 대조기 + 브라우저** | ★★ **이 배치에서 두 판이 갈린 단 하나의 블록이 이 주제의 것**이다(19블록 중 1개) |
> | ★ **① 추상 연산에 로그 심기** | 한 자리에만 쓰인다 — **동결된 객체의 getter 에 카운터**를 달아 「얼었는데 값이 바뀐다」를 찍는다 |
> | ★ **부적용 — ③ 브랜드 태그**(`Object.prototype.toString.call`) | 디스크립터는 값의 **종류**를 묻지 않는다. 가를 칸이 없다 — **잴 것이 없다** |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | 이 주제에는 **`SyntaxError` 가 한 줄도 없다.** 전부 런타임 `TypeError` 라 캐럿이 나올 자리가 없다 |
> | ★ **안 쟀다 — 성능** | 「동결하면 느려진다」·「`defineProperty` 가 비싸다」는 **한 줄도 안 쟀다.** 이 문서에 속도 주장이 없다 |
>
> ★★ **제5의 상태 — 창을 바꿔 물은 자리가 하나 있다.**
> 「**비엄격에서 그 쓰기가 막혔나**」는 ④ 예외 창으로는 **원리상 못 묻는다** — 예외가 안 나기 때문이다.
> 그래서 같은 질문을 **「쓴 뒤에 값을 다시 읽는」 창**으로 바꿔 물었다(엄격/비엄격 격자의 `return 'a=' + o.a`).
> ★ 바꾼 창이 못 보는 것도 적어 둔다 — **원래 값과 쓰려던 값이 같으면 그 창도 아무것도 못 가른다.**
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **세 플래그의 `true`/`false`** |
> | 예외 **문구**(`Cannot redefine property: p` 등 — 판이 오르면 바뀐다) | ★★★ **격자의 집계 줄** — `blocked 11 / 27` · `mode-dependent cells 9 / 13` |
> | V8 이 객체를 적는 방식(`#<Object>`·`[object Array]`) | ★★★ **예외의 종류**(`TypeError`) · 세 술어의 판정 |
> | ★ **`fa.toSorted()` 한 줄** — **판에 달렸다** | ★★ **전역 오염 목록** · 두 판 대조기의 `identical / differs` 집계 |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> ★★★ **두 판이 갈린 블록이 이 주제에 하나 있다** — `js12b-14c-freeze.js` 의 `fa.toSorted()` 한 줄이다.
> **갈린 블록은 양쪽을 다 싣는다.**
>
> **선행** — [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [12 — 옵셔널 체이닝·널 병합·논리 할당](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) · [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md).
> ★★★ **13번이 이 주제의 뿌리다.** 13번은 「어느 문법이 어떤 디스크립터를 만드나」까지 갔고,
> 여기서는 **그 세 플래그가 실제로 무엇을 막는지**를 격자로 연다.
> ★★ **12번이 「막혔을 때 무엇이 보이나」까지 갔다.** `||=` 가 동결된 객체에서 조용했던 그 자리의 **이유**가 여기 있다.
> ★★ **11번의 `{ ...o }` 가 보는 「열거 가능」의 정본이 여기**다 — `enumerable: false` 가 그 문법을 통째로 건너뛰게 한다.
> **이어지는 곳** — [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [목록의 **18번 주제**](../18-for-in-and-enumeration/) 「`for...in` 과 열거」 · [목록의 **25번 주제**](../25-array-non-mutating-and-copy-methods/) 「배열 비변형·복사 메서드」 · [목록의 **27번 주제**](../27-object-static-methods/) 「`Object` 정적 메서드」 · [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」 · [목록의 **45번 주제**](../45-proxy/) 「`Proxy`」 · [목록의 **46번 주제**](../46-reflect/) 「`Reflect`」 · [목록의 **48번 주제**](../48-deep-copy-methods-compared/) 「깊은 복사 수단 비교」
>
> ★★ **경계 — 조회가 체인을 타는 경로는 15번이 정본이다.** 여기서는 **프로토타입의 `writable: false` 가 자식의 쓰기를 막는다**는 한 칸까지다.
> ★★ **경계 — 엄격 모드가 바꾸는 규칙 전부는 35번이 정본이다.** 여기서는 **동결·봉인이 실패하는 자리에서 모드가 만드는 차이**까지다.
> ★★ **경계 — 프록시 불변식과 트랩은 45·46번이 정본이다.** 여기서는 **디스크립터가 그 계약의 언어라는 사실**까지다(프록시는 안 던져 봤다).
> ★★ **경계 — 깊은 동결(`deepFreeze`)과 깊은 복사는 48번이 정본이다.** 여기서는 **동결이 얕다는 사실**까지다.

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

**모든 프로퍼티에는 값 말고도 「허가증」이 한 장씩 붙어 있고, 거기에 도장 세 개가 찍혀 있다.**
값을 읽는 것으로는 허가증을 볼 수 없다. **허가증을 보는 유일한 창이 `Object.getOwnPropertyDescriptor`** 다.

```text
   프로퍼티 하나 = 값 + 허가증

   ┌──────────────────────────────────────────────┐
   │  o.a                                          │
   │  ┌────────┐   ┌──────────────────────────┐   │
   │  │ 값 1   │   │ 허가증                    │   │
   │  └────────┘   │  writable      덮어쓰기   │   │
   │               │  enumerable    보이기     │   │
   │               │  configurable  손대기     │   │
   │               └──────────────────────────┘   │
   └──────────────────────────────────────────────┘

   ★ o.a 를 읽으면 「1」만 나온다. 도장 세 개는 값에 아무 흔적도 남기지 않는다.
   ★ 그래서 이 주제의 모든 근거는 getOwnPropertyDescriptor 의 덤프다.
```

도장 셋이 각각 다른 문을 지킨다 — **셋이 서로 상관없다**는 것이 이 주제의 첫 매듭이다.

- **`writable`** — `o.a = 2` 라고 **대입**할 수 있나. 이것만이 대입을 정한다.
- **`enumerable`** — `Object.keys`·`for...in`·`JSON.stringify`·`{ ...o }` 에 **보이나.**
- **`configurable`** — **지우거나**(`delete`) **허가증 자체를 고쳐 쓸** 수 있나(플래그 변경·데이터↔접근자 변경).

그리고 객체 통째로 잠그는 함수가 셋 있는데, **세 함수는 나란한 선택지가 아니라 계단**이다.

```text
   세 봉인 함수는 계단이다 -- 뒤엣것이 앞엣것을 포함한다

   preventExtensions  ┐  새 프로퍼티 추가를 막는다
                      │  프로토타입 교체도 같이 막힌다
                      ├─ seal        ┐  + 삭제와 허가증 고쳐쓰기를 막는다
                      │              ├─ freeze   + 덮어쓰기까지 막는다
                      │              │
   ────────────────────────────────────────────────────────────
   기존 값 덮어쓰기     되고          되고        막힌다
   새 프로퍼티 추가     막힌다        막힌다      막힌다
   프로퍼티 삭제        되고          막힌다      막힌다
   허가증 고쳐쓰기      되고          막힌다      막힌다
   프로토타입 교체      막힌다        막힌다      막힌다
   ★ 안쪽 객체 고치기   되고          되고        된다   <- 셋 다 못 막는다
```

> **디스크립터(property descriptor)** — 프로퍼티의 허가증을 **평범한 객체로 꺼내 놓은 것.**\
> 예: `Object.getOwnPropertyDescriptor({ a: 1 }, 'a')` 는 `{ value: 1, writable: true, enumerable: true, configurable: true }` 를 돌려준다.\
> 꺼낸 것은 **사본**이라 그 객체를 고쳐도 원래 프로퍼티는 안 바뀐다 — 다시 넣으려면 `defineProperty` 를 불러야 한다.

## 이 주제가 답하려는 질문

1. **같은 `1` 인데 무엇이 다른가** — 리터럴로 쓴 `{ a: 1 }` 과 `defineProperty` 로 만든 `a` 는 **값이 같고 허가증이 정반대**다. 왜 그렇게 정했나?
2. **`configurable: false` 뒤에 남는 문은 정확히 무엇인가** — 「이제 아무것도 못 바꾼다」가 맞나? **되돌릴 수 있는 것과 없는 것**의 경계는?
3. **`Object.freeze` 는 어디서 멈추는가** — 중첩은? 접근자는? 그리고 **얼었는지 묻는 `isFrozen` 은 언제 `true` 라고 답하는가?**

## 동작 방식

### (1) ★★★ 디스크립터 덤프 — 「어디서 온 프로퍼티인가」가 허가증에 적혀 있다

**언제 쓰나** — 「내 객체에 분명히 넣었는데 `Object.keys` 에 안 나온다」·「덮어썼는데 값이 그대로다」가 나올 때.
**값을 아무리 찍어 봐도 안 나온다.** 허가증을 꺼내야 보인다.

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

```text
===== node20 js12b-14a-dump.js (exit=0) =====
[1] where did the property come from?
source                                kind      value                 writable enumerable configurable
literal  { a: 1 }                     data      1                     w=true   e=true   c=true
assignment  o.a = 1                   data      1                     w=true   e=true   c=true
defineProperty { value: 1 }           data      1                     w=false  e=false  c=false
defineProperty {} (no value)          data      undefined             w=false  e=false  c=false
literal getter  { get g() {} }        accessor  get=fn set=undefined  w=-      e=true   c=true
defineProperty { get }                accessor  get=fn set=undefined  w=-      e=false  c=false
Object.create 2nd arg                 data      1                     w=false  e=false  c=false
class prototype method                data      [fn]                  w=true   e=false  c=true
array element  [7]                    data      7                     w=true   e=true   c=true
array length   [7]                    data      1                     w=true   e=false  c=false
function .prototype                   data      {}                    w=true   e=false  c=false
function .name                        data      "f"                   w=false  e=false  c=true
function .length                      data      2                     w=false  e=false  c=true
Object.prototype.toString             data      [fn]                  w=true   e=false  c=true
globalThis.NaN                        data      NaN                   w=false  e=false  c=false

[2] the same property after each sealing call
state                                 kind      value                 writable enumerable configurable
plain                      .a         data      1                     w=true   e=true   c=true
preventExtensions          .a         data      1                     w=true   e=true   c=true
seal                       .a         data      1                     w=true   e=true   c=false
freeze                     .a         data      1                     w=false  e=true   c=false
plain                      .g         accessor  get=fn set=undefined  w=-      e=true   c=true
seal                       .g         accessor  get=fn set=undefined  w=-      e=true   c=false
freeze                     .g         accessor  get=fn set=undefined  w=-      e=true   c=false

[3] defineProperty defaults are the opposite of the literal's
literal        {"value":1,"writable":true,"enumerable":true,"configurable":true}
defineProperty {"value":1,"writable":false,"enumerable":false,"configurable":false}
all three flags flipped? true
is the defineProperty one visible to Object.keys / JSON? [] {}

[4] defineProperty on an EXISTING property only changes what you pass
after { enumerable: false } -> {"value":1,"writable":true,"enumerable":false,"configurable":true}
```

**그림 해설 — 한 단계에 한 문장.**

- ★★★ `[1]` 첫 두 줄 — **리터럴 `{ a: 1 }` 과 대입 `o.a = 1` 은 한 글자도 같다.** 둘 다 `w=true e=true c=true` 다.
  「대입은 뭔가 다를 것」이라는 짐작이 여기서 끊긴다.
- ★★★ `[3]` 이 이 절의 급소다 — **`defineProperty` 의 기본값은 리터럴의 정반대**다.
  `all three flags flipped? true` 가 스크립트가 직접 센 판정이고,
  그 아래 줄이 결과를 보인다 — `Object.keys` 가 `[]` 이고 `JSON.stringify` 가 `{}` 다.
  **넣었는데 안 보인다.** `enumerable` 이 기본 `false` 이기 때문이다.
- ★★ `Object.create` 의 두 번째 인자도 **같은 `false,false,false`** 다. 디스크립터를 받는 문은 전부 이 기본값을 쓴다.
- ★★ **클래스 프로토타입 메서드가 `e=false`** 다 — 그래서 `Object.keys(C.prototype)` 이 비고, `for...in` 에도 메서드가 안 뜬다.
  ★ **리터럴 메서드 단축(`{ m() {} }`)과 다른 자리**다. 13번의 뷰 격자가 그 짝이다.
- ★ **여덟 조합 중 일곱이 이 덤프에 나온다.** 데이터 프로퍼티의 `(w,e,c)` 조합으로 세면
  `ttt`(리터럴·대입·배열 요소) · `fff`(`defineProperty`·`Object.create`·`globalThis.NaN`) ·
  `tft`(클래스 메서드·`Object.prototype.toString`) · `tff`(배열 `length`·함수 `.prototype`) ·
  `fft`(함수 `.name`·`.length`) 가 `[1]` 에 있고, `ttf`(seal 뒤)·`ftf`(freeze 뒤)가 `[2]` 에 있다.
  **안 나온 하나는 `w=false e=true c=true`** — 만들 수 없어서가 아니라 이 열아홉 줄에 우연히 없는 것이다.
- ★★ **배열의 `length` 는 `w=true e=false c=false`** — 이 조합이 뜻하는 바가 정확하다.
  **값은 바꿀 수 있는데**(`arr.length = 0` 이 먹는다) **지우거나 허가증을 고칠 수는 없다.**
  함수의 `.prototype` 도 같은 조합이다.
- ★★ **함수의 `.name` 과 `.length` 는 정반대인 `w=false e=false c=true`** —
  **대입으로는 못 바꾸는데 `defineProperty` 로는 바꿀 수 있다.** 「읽기 전용」과 「고정」이 다른 말이라는 실증이다.
- ★ **`Object.prototype.toString` 이 `w=true c=true`** 다. 내장 메서드인데 **그냥 덮어쓸 수 있다** —
  JS 의 내장 객체가 얼마나 열려 있는지를 보여 주는 줄이다. 반대로 **`globalThis.NaN` 은 `false,false,false`** 로 완전히 잠겨 있다.
- ★★ `[2]` 가 세 봉인 함수를 허가증 수준에서 가른다 —
  **`preventExtensions` 는 기존 프로퍼티의 허가증을 한 칸도 안 건드린다**(`ttt` 그대로) ·
  **`seal` 은 `configurable` 만 내린다** · **`freeze` 는 거기에 `writable` 까지 내린다.**
  ★★★ **`enumerable` 은 셋 다 안 건드린다** — 동결해도 `e=true` 다. 「얼리면 안 보이게 된다」는 오해가 여기서 끊긴다.
- ★★★ **접근자 프로퍼티는 `freeze` 로도 `c=false` 밖에 안 바뀐다**(`.g` 세 줄).
  접근자에는 **`writable` 칸 자체가 없기 때문**이다 — 덤프의 `w=-` 가 그 표시이고,
  스크립트가 `("get" in d)` 로 종류를 가르는 것이 **두 디스크립터의 키 집합이 다르다**는 증거다.
- ★★ `[4]` — **`defineProperty` 를 기존 프로퍼티에 부르면 준 칸만 바꾼다.** 기본값으로 안 덮는다.
  `{ enumerable: false }` 하나만 줬더니 `writable` 과 `configurable` 은 `true` 로 남았다.
  ★ **새로 만들 때와 고칠 때의 규칙이 다르다** — 이것이 `defineProperty` 에서 가장 자주 틀리는 자리다.

```text
   같은 값 1, 정반대의 허가증

   { a: 1 }                     Object.defineProperty({}, 'a', { value: 1 })
   ┌───────────────────┐        ┌───────────────────┐
   │ value        1    │        │ value        1    │
   │ writable     true │        │ writable     false│
   │ enumerable   true │        │ enumerable   false│
   │ configurable true │        │ configurable false│
   └───────────────────┘        └───────────────────┘
          o.a -> 1                      o.a -> 1
      Object.keys -> ["a"]         Object.keys -> []      <- 여기서만 갈린다

   ★ 「빠진 칸은 false」다. 디스크립터에 안 적은 칸은 기본값이 false 이지 true 가 아니다.
   ★ 단 이미 있는 프로퍼티에 부르면 다르다 -- 안 적은 칸은 그대로 둔다(덮지 않는다).
```

### (2) ★★★ `configurable: false` 뒤에 남는 문 — 27칸 격자

**언제 쓰나** — 「한 번 잠근 프로퍼티를 되돌릴 수 있나」를 판단할 때. **직관이 두 군데서 틀린다.**

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

```text
===== node20 js12b-14b-configurable.js (exit=0) =====
[1] grid -- strict mode throughout
start             operation                               result
w=true  c=false   defineProperty value: 2                 OK  now value=2 w=true e=true c=false
w=true  c=false   defineProperty value: 1 (same)          OK  now value=1 w=true e=true c=false
w=true  c=false   defineProperty writable: true           OK  now value=1 w=true e=true c=false
w=true  c=false   defineProperty writable: false          OK  now value=1 w=false e=true c=false
w=true  c=false   defineProperty enumerable: false        TypeError Cannot redefine property: p
w=true  c=false   defineProperty configurable: true       TypeError Cannot redefine property: p
w=true  c=false   defineProperty get() {} (to accessor)   TypeError Cannot redefine property: p
w=true  c=false   assignment  o.p = 2                     OK  now value=2 w=true e=true c=false
w=true  c=false   delete o.p                              TypeError Cannot delete property 'p' of #<Object>

w=false c=false   defineProperty value: 2                 TypeError Cannot redefine property: p
w=false c=false   defineProperty value: 1 (same)          OK  now value=1 w=false e=true c=false
w=false c=false   defineProperty writable: true           TypeError Cannot redefine property: p
w=false c=false   defineProperty writable: false          OK  now value=1 w=false e=true c=false
w=false c=false   defineProperty enumerable: false        TypeError Cannot redefine property: p
w=false c=false   defineProperty configurable: true       TypeError Cannot redefine property: p
w=false c=false   defineProperty get() {} (to accessor)   TypeError Cannot redefine property: p
w=false c=false   assignment  o.p = 2                     TypeError Cannot assign to read only property 'p' of object '#<Object>'
w=false c=false   delete o.p                              TypeError Cannot delete property 'p' of #<Object>

w=true  c=true    defineProperty value: 2                 OK  now value=2 w=true e=true c=true
w=true  c=true    defineProperty value: 1 (same)          OK  now value=1 w=true e=true c=true
w=true  c=true    defineProperty writable: true           OK  now value=1 w=true e=true c=true
w=true  c=true    defineProperty writable: false          OK  now value=1 w=false e=true c=true
w=true  c=true    defineProperty enumerable: false        OK  now value=1 w=true e=false c=true
w=true  c=true    defineProperty configurable: true       OK  now value=1 w=true e=true c=true
w=true  c=true    defineProperty get() {} (to accessor)   OK  now accessor e=true c=true
w=true  c=true    assignment  o.p = 2                     OK  now value=2 w=true e=true c=true
w=true  c=true    delete o.p                              OK  now (deleted)

blocked cells 11 / 27

[2] the one-way door -- writable true->false is allowed even when configurable is false
true -> false   {"value":1,"writable":false,"enumerable":false,"configurable":false}
false -> true   TypeError Cannot redefine property: p
```

**그림 해설.**

- ★★★ **막힌 칸은 27칸 중 11칸**이다(마지막 줄을 스크립트가 직접 셌다). 나머지 16칸은 **통과한다.**
  「설정 불가로 만들면 아무것도 못 한다」가 절반도 안 맞는 셈이다.
- ★★★ **가장 반직관적인 칸** — `w=true c=false` 에서 **`defineProperty` 로 `value: 2` 를 주는 것이 통과한다.**
  「설정 불가인데 값이 바뀐다」로 보이지만, 그 자리에서 **값을 바꿀 권한은 `writable` 이 이미 주고 있다.**
  `configurable` 이 지키는 문은 **허가증 자체**이지 값이 아니다.
- ★★★ **`writable` 은 일방통행 문이다.** 같은 행에서 `writable: false` 는 통과하고,
  `[2]` 가 그 문을 한 번 더 확인한다 — `true -> false` 는 되고 **`false -> true` 는 `TypeError`** 다.
  ★ `[2]` 의 결과 디스크립터가 `"enumerable":false` 인 것도 읽을거리다 —
  만들 때 `enumerable` 을 안 줬으니 기본값 `false` 가 박힌 것이다((1)의 결론이 여기서 되풀이된다).
- ★★ **`w=false c=false` 인데 `value: 1 (same)` 이 통과한다.** 같은 값으로 재정의하는 것은 **아무것도 안 바꾸므로** 허용된다.
  ★★★ **그래서 「`TypeError` 가 안 났다」가 「바꿀 수 있다」가 아니다.** 같은 행의 `value: 2` 는 막힌다.
- ★★ **세 문이 각각 다른 플래그에 달려 있다** — 격자를 세로로 읽으면 보인다.
  `assignment o.p = 2` 는 **`writable` 만** 본다(`w=true c=false` 에서 통과) ·
  `delete o.p` 는 **`configurable` 만** 본다(`w=true c=false` 에서도 막힌다) ·
  `enumerable`·`configurable` 변경과 **데이터→접근자 변환**은 **`configurable` 만** 본다.
- ★ 마지막 행(`w=true c=true`)은 **아홉 칸 전부 `OK`** 다 — 잠그기 전에는 무엇이든 된다는 대조군이다.

```text
   writable 은 일방통행 문 -- configurable: false 인 채로도 내려갈 수는 있다

        w=true                                w=false
        c=false                               c=false
          │                                      │
          │   defineProperty { writable:false }  │
          ├─────────────────────────────────────>│   통과
          │                                      │
          │<─────X───────────────────────────────┤   TypeError 로 막힌다
          │   defineProperty { writable:true }   │
          │                                      │
     값 바꾸기 O                             값 바꾸기 X
     삭제     X                             삭제     X

   ★ 이 문은 되돌릴 수 없다. 한 번 내려가면 그 객체에서는 끝이다.
   ★ configurable 이 true 일 때만 양방향이다 -- 격자의 셋째 덩어리가 그것을 보인다.
```

### (3) ★★ 세 봉인 함수 · 얕음 · 세 술어 — 24칸 격자와 13줄 덤프

**언제 쓰나** — 「`freeze` 했으니 안 바뀐다」를 믿기 전에. **세 군데에서 그 믿음이 깨진다** — 안쪽·접근자·배열이다.

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

```text
===== node20 js12b-14c-freeze.js (exit=0) =====
[1] grid -- strict mode throughout
operation                 plain               preventExtensions   seal                freeze              
add    o.nu = 1           OK                  TypeError           TypeError           TypeError           
write  o.a = 2            OK                  OK                  OK                  TypeError           
delete o.a                OK                  OK                  TypeError           TypeError           
reconfig defineProperty   OK                  OK                  TypeError           TypeError           
mutate o.deep.n = 2       OK                  OK                  OK                  OK                  
setPrototypeOf(o, null)   OK                  TypeError           TypeError           TypeError           

[2] the three predicates
object                            isExtensible   isSealed   isFrozen
{}                                true           false      false
Object.preventExtensions({})      false          true       true
Object.seal({})                   false          true       true
Object.freeze({})                 false          true       true
{ a: 1 }                          true           false      false
Object.preventExtensions({a:1})   false          false      false
Object.seal({a:1})                false          true       false
Object.freeze({a:1})              false          true       true
preventExt + w:false,c:false prop false          true       true
Object.freeze([])                 false          true       true
Object.freeze([1])                false          true       true
5  (primitive)                    false          true       true
'str'  (primitive)                false          true       true

[3] freeze is shallow -- the nested object is untouched
after mutating through the frozen object -> {"a":1,"deep":{"n":99},"arr":[1,2,3]}
isFrozen(outer)      true
isFrozen(outer.deep) false

[4] a getter survives freeze -- the VALUE it returns can still change
isFrozen true   descriptor {"get":"[fn]","enumerable":true,"configurable":false}
g.next reads: 1 2 3

[5] a frozen array
fa[0] = 9       TypeError Cannot assign to read only property '0' of object '[object Array]'
fa.push(4)      TypeError Cannot add property 3, object is not extensible
fa.length = 0   TypeError Cannot assign to read only property 'length' of object '[object Array]'
fa.sort()       TypeError Cannot assign to read only property '0' of object '[object Array]'
fa.toSorted()   OK  [1,2,3]  returned [1,2,3]
```

★★★ **이 블록이 이 배치에서 두 판이 갈린 유일한 블록이다.** 아래가 같은 소스의 node18 판이다.

```text
===== node18 js12b-14c-freeze.js (exit=0) =====
[1] grid -- strict mode throughout
operation                 plain               preventExtensions   seal                freeze              
add    o.nu = 1           OK                  TypeError           TypeError           TypeError           
write  o.a = 2            OK                  OK                  OK                  TypeError           
delete o.a                OK                  OK                  TypeError           TypeError           
reconfig defineProperty   OK                  OK                  TypeError           TypeError           
mutate o.deep.n = 2       OK                  OK                  OK                  OK                  
setPrototypeOf(o, null)   OK                  TypeError           TypeError           TypeError           

[2] the three predicates
object                            isExtensible   isSealed   isFrozen
{}                                true           false      false
Object.preventExtensions({})      false          true       true
Object.seal({})                   false          true       true
Object.freeze({})                 false          true       true
{ a: 1 }                          true           false      false
Object.preventExtensions({a:1})   false          false      false
Object.seal({a:1})                false          true       false
Object.freeze({a:1})              false          true       true
preventExt + w:false,c:false prop false          true       true
Object.freeze([])                 false          true       true
Object.freeze([1])                false          true       true
5  (primitive)                    false          true       true
'str'  (primitive)                false          true       true

[3] freeze is shallow -- the nested object is untouched
after mutating through the frozen object -> {"a":1,"deep":{"n":99},"arr":[1,2,3]}
isFrozen(outer)      true
isFrozen(outer.deep) false

[4] a getter survives freeze -- the VALUE it returns can still change
isFrozen true   descriptor {"get":"[fn]","enumerable":true,"configurable":false}
g.next reads: 1 2 3

[5] a frozen array
fa[0] = 9       TypeError Cannot assign to read only property '0' of object '[object Array]'
fa.push(4)      TypeError Cannot add property 3, object is not extensible
fa.length = 0   TypeError Cannot assign to read only property 'length' of object '[object Array]'
fa.sort()       TypeError Cannot assign to read only property '0' of object '[object Array]'
fa.toSorted()   OK  [1,2,3]
```

**그림 해설.**

- ★★★ `[1]` 이 앞의 계단 그림을 **출력으로** 확인한다. 세로로 읽으면 **뒤엣것이 앞엣것을 포함**한다 —
  `preventExtensions` 가 **추가와 프로토타입 교체** 둘을 막고, `seal` 이 거기에 **삭제와 허가증 고쳐쓰기**를 더하고,
  `freeze` 가 거기에 **덮어쓰기**를 더한다.
- ★★ **`setPrototypeOf` 가 `preventExtensions` 만으로 이미 막힌다.** 프로토타입 교체는
  **확장 가능성에 걸려 있지 개별 프로퍼티의 플래그에 걸려 있지 않다.** 15번이 그쪽 정본이다.
- ★★★ **`mutate o.deep.n = 2` 행은 네 칸이 전부 `OK`** 다. **셋 중 무엇으로도 안쪽은 못 막는다.**
- ★★★ `[2]` 가 **브리핑의 전제를 뒤집은 자리**다. 「빈 객체는 얼어 있다」가 **틀렸다.**
  **`{}` 는 `isFrozen` 이 `false`** 다(첫 줄). `isExtensible` 이 `true` 라서다.
  **`true` 인 빈 객체는 `Object.preventExtensions({})`** 이고, `seal({})`·`freeze({})` 도 같다 —
  ★★ **비확장이기만 하면 빈 객체는 셋 중 무엇을 불렀든 `isSealed` 도 `isFrozen` 도 `true`** 다.
  「모든 프로퍼티가 …」라는 조건이 **검사할 프로퍼티가 없어 자동으로 참**이 되기 때문이다.
- ★★★ **세 술어의 정의를 이 13줄에서 역산할 수 있다.**
  `isExtensible` = 새 프로퍼티를 더할 수 있나 ·
  `isSealed` = **비확장 ∧ 모든 own 프로퍼티가 `c=false`** ·
  `isFrozen` = **`isSealed` ∧ 모든 own 데이터 프로퍼티가 `w=false`**.
  `{ a: 1 }` 세 줄이 그 계단을 그대로 보인다 — `preventExtensions` 는 둘 다 `false`,
  `seal` 은 `isSealed` 만 `true`, `freeze` 라야 `isFrozen` 이 `true` 다.
- ★★★ **`freeze` 를 한 번도 안 불렀는데 `isFrozen` 이 `true` 인 줄이 있다** — `preventExt + w:false,c:false prop`.
  **`isFrozen` 은 「`freeze` 를 불렀나」를 묻는 것이 아니라 「지금 상태가 그 조건을 만족하나」를 묻는다.**
  ★ 그래서 `isFrozen` 이 `true` 라고 해서 **누가 `freeze` 를 불렀다고 읽으면 안 된다.**
- ★★ **원시값에 물으면 `isExtensible false` · `isSealed true` · `isFrozen true`** 다(마지막 두 줄).
  터지지 않는다. **원시값에는 own 프로퍼티를 못 붙이니 조건이 자동으로 참**이 된다.
- ★★★ `[3]` — **얕다.** `outer.deep.n = 99` 도 `outer.arr.push(3)` 도 **엄격 모드인데 안 터지고 실제로 바뀌었다.**
  `isFrozen(outer)` 는 `true` 인데 `isFrozen(outer.deep)` 는 `false` 다.
  ★★ **「얼었다」는 그 객체 한 겹의 성질**이고, **참조로 이어진 저쪽은 남의 객체**다.
- ★★★ `[4]` — **접근자는 `freeze` 로 안 잠긴다.** `isFrozen` 이 `true` 인데 `g.next` 를 세 번 읽으니 **`1 2 3`** 이다.
  (1)의 `[2]` 가 이유를 이미 보였다 — **`freeze` 가 내리는 것은 `writable` 인데 접근자에는 그 칸이 없다.**
  ★ 여기가 이 주제에서 **① 로그 심기 창**이 쓰인 유일한 자리다. `counter` 가 세 번 오른 것이 근거다.
  ★ 그 줄의 디스크립터 JSON 에 `set` 칸이 안 보이는 것은 **`set` 이 `undefined` 라 `JSON.stringify` 가 지운 것**이지
  칸이 없는 것이 아니다 — (1)의 덤프가 `set=undefined` 로 그것을 따로 보인다.
- ★★ `[5]` — 동결된 배열에서 **네 줄이 `TypeError`** 다. 눈여겨볼 것은 **문구가 무엇을 가리키나**이다.
  `fa[0] = 9` 와 `fa.sort()` 는 **같은 문구**(`read only property '0'`)로 막힌다 — **`sort` 가 제자리 연산**이기 때문이다.
  `fa.push(4)` 는 **다른 문구**(`Cannot add property 3, object is not extensible`)다 — 길이를 늘리려 한 것이라서다.
  `fa.length = 0` 은 **`length` 가 읽기 전용**이 됐다고 답한다.
- ★★★ **다섯째 줄이 두 판에서 갈린 줄**이다.
  node20 은 `OK  [1,2,3]  returned [1,2,3]` 이고 node18 은 `OK  [1,2,3]` 이다.
  ★★ **node18 의 `OK` 를 「`toSorted` 가 통과했다」로 읽으면 안 된다.**
  소스가 `fa.toSorted && fa.toSorted()` 이므로 **v18 에서는 `fa.toSorted` 가 `undefined` 라 `&&` 가 단락 평가**했고,
  그래서 돌려받은 값이 `undefined` 이라 `returned …` 꼬리가 안 붙은 것이다.
  **근거의 종류가 두 판에서 다르다** — node20 줄은 **「동결된 배열에서도 비변형 메서드는 된다」의 근거**이고,
  node18 줄은 **「그 메서드가 이 판에 없다」의 근거**일 뿐이다. ★ 12번에서 본 단축 평가가 여기서 되돌아온다.

```text
   동결은 겉면 한 겹만 언다

   Object.freeze(outer)
   ┌───────────────────────────────────────┐
   │ outer            [ 얼음 ]              │
   │   a: 1           <- 못 바꾼다           │
   │   deep ──────────┐                     │
   │   arr  ──────────┼──┐                  │
   └──────────────────┼──┼──────────────────┘
                      │  │
                      v  v
            ┌──────────────┐  ┌──────────────┐
            │ { n: 1 }     │  │ [1, 2]       │   <- 얼지 않았다
            │  n = 99 된다 │  │ push(3) 된다 │      isFrozen 이 false 라고 답한다
            └──────────────┘  └──────────────┘

   ★ 얼린 것은 「outer 가 들고 있는 참조」이지 「그 참조가 가리키는 객체」가 아니다.
   ★ 접근자도 같은 모양이다 -- get 함수는 얼지만 그 함수가 세는 값은 밖에 있다.
```

### (4) ★★★ 엄격 / 비엄격 — 막힌 것이 보이는 창은 엄격에만 열린다

**언제 쓰나** — 「동결했는데 코드가 멀쩡히 돈다」가 나올 때. **돈 게 아니라 조용히 버려진 것**일 수 있다.

> ★★★ **엄격을 먼저 돌렸다. 그리고 탐침마다 전역 이름을 다르게 줬다.**
> 이 배치 직전에 실제 사고가 있었다 — **비엄격 탐침을 먼저 돌리면 암시적 전역이 만들어지고**,
> 뒤에 도는 엄격 탐침이 그것을 읽어 **두 모드가 「같다」는 거짓 결과**가 난다.
> 값도 그럴듯하고 예외도 안 나서 **모든 검사기를 통과한다.**
> 아래 블록은 **엄격 열을 먼저 채우고**, 마지막에 **무엇이 실제로 전역에 샜는지**를 찍는다.

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

```text
===== node20 js12b-14s-strict.js (exit=0) =====
[1] strict-first grid
frozen.a = 2                SPLIT strict: TypeError Cannot assign to read only property 'a' of object '#<Object>'
                                  sloppy: OK a=1
frozen.nu = 1 (add)         SPLIT strict: TypeError Cannot add property nu, object is not extensible
                                  sloppy: OK keys=["a"]
delete frozen.a             SPLIT strict: TypeError Cannot delete property 'a' of #<Object>
                                  sloppy: OK false keys=["a"]
sealed.a = 2                SAME  strict: OK a=2
                                  sloppy: OK a=2
delete sealed.a             SPLIT strict: TypeError Cannot delete property 'a' of #<Object>
                                  sloppy: OK false keys=["a"]
preventExt.nu = 1           SPLIT strict: TypeError Cannot add property nu, object is not extensible
                                  sloppy: OK keys=["a"]
non-writable.a = 2          SPLIT strict: TypeError Cannot assign to read only property 'a' of object '#<Object>'
                                  sloppy: OK a=1
getter-only.a = 2           SPLIT strict: TypeError Cannot set property a of #<Object> which has only a getter
                                  sloppy: OK a=1
proto has non-writable a    SPLIT strict: TypeError Cannot assign to read only property 'a' of object '#<Object>'
                                  sloppy: OK a=1 own=false
frozen array push           SAME  strict: TypeError Cannot add property 1, object is not extensible
                                  sloppy: TypeError Cannot add property 1, object is not extensible
defineProperty on frozen    SAME  strict: TypeError Cannot redefine property: a
                                  sloppy: TypeError Cannot redefine property: a
assign to undeclared G      SPLIT strict: ReferenceError <G> is not defined
                                  sloppy: OK 1
frozen globalThis-ish prop  SAME  strict: TypeError Cannot assign to read only property 'a' of object '#<Object>'
                                  sloppy: TypeError Cannot assign to read only property 'a' of object '#<Object>'

mode-dependent cells 9 / 13

[2] leftovers on globalThis
globals starting with js12b14 -> ["js12b14SloppyG11"]
any js12b14StrictG* leaked?    -> false
```

**그림 해설.**

- ★★★ **설정에 달린 칸은 13칸 중 9칸**이다(`mode-dependent cells 9 / 13` — 스크립트가 직접 셌다).
  이 배치 네 주제 중 **가장 크게 갈린다**. 12번이 11칸 중 6칸, 13번은 잴 칸 자체가 없었다.
- ★★★ **갈린 아홉 칸의 모양이 전부 같다** — 엄격은 `TypeError`, 비엄격은 **`OK` 인데 값이 안 바뀌어 있다.**
  `frozen.a = 2` 의 비엄격 답이 **`OK a=1`** 인 것이 그 전형이다. **던지지 않고, 쓰지도 않는다.**
  ★★ **그래서 「에러가 없다」로는 절대 못 가른다.** 이것이 이 주제의 가장 비싼 사고다.
- ★★★ **SAME 인 네 칸이 두 종류로 갈린다 — 뭉뚱그리면 결론이 틀린다.**
  - **`sealed.a = 2` 는 양쪽 다 `OK a=2`** — **애초에 아무것도 안 막혔다.** `seal` 이 `writable` 을 안 건드리기 때문이고,
    (1)의 `[2]` 에서 `seal .a` 가 `w=true` 인 것이 그 증거다. **두 블록이 서로를 설명한다.**
  - **나머지 셋은 양쪽 다 `TypeError`** — **그 문들은 모드와 무관하게 던진다.**
    `Object.defineProperty` · `Array.prototype.push` · `Object.assign` 이 그것이다.
    ★★ **「비엄격이면 조용하다」는 대입(`=`)과 `delete` 에만 해당한다.** 메서드로 부르면 모드가 상관없다.
- ★★ **`delete` 는 비엄격에서 `false` 를 돌려준다** — `delete frozen.a` 의 비엄격 답이 `OK false keys=["a"]` 다.
  ★ 12번에서 본 그대로다 — `delete` 의 반환값은 **「지웠나」가 아니라 「거부되지 않았나」** 이고, 여기서는 **거부됐으니 `false`** 다.
- ★★ **프로토타입의 `w=false` 가 자식의 쓰기를 막는다**(`proto has non-writable a`).
  비엄격 답이 **`OK a=1 own=false`** 다 — **own 프로퍼티가 아예 안 생겼다.**
  ★ 쓰기가 체인을 어떻게 보는지는 15번이 정본이다. 여기서는 **막는 것이 디스크립터라는 사실**까지다.
- ★★★ `[2]` — **전역에 남은 이름은 하나**(`js12b14SloppyG11`)이고 **`js12b14StrictG*` 는 하나도 안 샜다.**
  샌 하나는 열두 번째 탐침(`assign to undeclared G`)의 **비엄격** 판이 만든 것이다.
  ★★ **이름을 공유했다면** 그 값을 다른 탐침이 읽어 **갈린 칸이 하나 줄었을** 자리다.
  「0 이 결론인 격자일수록 그 0 이 진짜인지 따로 물어야 한다」의 짝이 **이 두 줄**이다.

```text
   같은 한 줄, 두 모드

                    o.a = 2   (o 는 동결됨)
                         │
            ┌────────────┴────────────┐
            │                         │
        "use strict"               비엄격
            │                         │
            v                         v
      TypeError 로 멈춘다        아무 일도 안 일어난다
      「무엇이 막혔나」가          예외 없음 · 경고 없음
      문구에 적혀 나온다          반환값도 없음
            │                         │
            v                         v
      ④ 창이 열린다              ④ 창이 닫힌다
                                 -> 창을 바꿔 묻는다:
                                    쓴 뒤에 값을 다시 읽는다 (a=1 이 답)

   ★ 갈린 아홉 칸이 전부 이 모양이다.
   ★ 단 defineProperty · push · Object.assign 은 양쪽 다 왼쪽 길로 간다.
```

### (5) ★ 두 판이 갈린 한 줄 — 19블록 중 1개

```text
===== ./js12b-vdiff.sh (exit=0) =====
js12b-12a-shortcircuit.js    identical
js12b-12b-grid.js            identical
js12b-12c-assign.js          identical
js12b-12s-strict.js          identical
js12b-12x-forms.js           identical
js12b-12y-caret.js           identical
js12b-13a-order.js           identical
js12b-13b-intkeys.js         identical
js12b-13c-computed.js        identical
js12b-13d-views.js           identical
js12b-14a-dump.js            identical
js12b-14b-configurable.js    identical
js12b-14c-freeze.js          DIFFERS
    40c40
    < fa.toSorted()   OK  [1,2,3]
    ---
    > fa.toSorted()   OK  [1,2,3]  returned [1,2,3]
js12b-14s-strict.js          identical
js12b-15a-chain.js           identical
js12b-15b-proxy.js           identical
js12b-15c-shadow.js          identical
js12b-15d-misc.js            identical
js12b-15e-pycontrast.js      identical

identical 18  ·  differs 1  ·  total 19
```

★★ **이 배치 19블록 중 갈린 것은 하나**이고, **그 하나가 이 주제의 것**이다(`js12b-14c-freeze.js`).
★ 갈린 것은 **디스크립터나 동결의 규칙이 아니라 `Array.prototype.toSorted` 의 존재 여부**다(ES2023).
**동결의 규칙 쪽은 두 판이 한 글자도 안 갈렸다** — 위 목록의 `js12b-14a-dump.js`·`js12b-14b-configurable.js`·`js12b-14s-strict.js` 가 전부 `identical` 이다.

### (6) ★ 같은 질문을 브라우저에 던지면

```js
// js12b-hb-browser.js
// 같은 질문을 브라우저에 던진다 -- 네 주제에 호스트가 정하는 칸이 있나.
const lines = [];
function row(k, v) { lines.push("  " + k.padEnd(38) + v); }
function attempt(label, run) {
  try { row(label, String(run())); }
  catch (e) { row(label, e.constructor.name + ": " + e.message); }
}
const J = JSON.stringify;
row("engine", navigator.userAgent.replace(/^.*(Chrome\/[0-9.]+).*$/, "$1"));
attempt("12  0 ?? 'D' / 0 || 'D'", () => J([0 ?? "D", 0 || "D"]));
attempt("12  ||= does not write", () => {
  const log = []; let v = "keep";
  const o = { get x() { return v; }, set x(n) { log.push("set"); v = n; } };
  o.x ||= "R"; return J(log);
});
attempt("12  = x || y writes", () => {
  const log = []; let v = "keep";
  const o = { get x() { return v; }, set x(n) { log.push("set"); v = n; } };
  o.x = o.x || "R"; return J(log);
});
attempt("12  a?.b[f()] skips f", () => {
  let n = 0; const o = { a: null }; void o.a?.b[(n += 1, "c")]; return "calls " + n;
});
attempt("12  a ?? b || c compiles?", () => { new Function("let a,b,c; return a ?? b || c;"); return "ok"; });
attempt("12  new a?.b() compiles?", () => { new Function("let a; return new a?.b();"); return "ok"; });
attempt("13  enumeration order", () => {
  const s = Symbol("s"); const o = {};
  o.b = 1; o[2] = 1; o[s] = 1; o.a = 1; o[1] = 1; o["01"] = 1;
  return J(Reflect.ownKeys(o).map(String));
});
attempt("13  '4294967295' is an index?", () => {
  const o = { a: 0 }; o["4294967295"] = 1; o.z = 2; return J(Object.keys(o));
});
attempt("13  computed key calls toString", () => {
  const log = []; const k = { toString() { log.push("toString"); return "K"; } };
  const o = { [k]: 1 }; return J(Object.keys(o)) + " " + J(log);
});
attempt("13  __proto__ literal vs computed", () => {
  const P = {}; return String(Object.getPrototypeOf({ "__proto__": P }) === P) + "," +
    String(Object.getPrototypeOf({ ["__proto__"]: P }) === P);
});
attempt("14  literal vs defineProperty desc", () =>
  J(Object.getOwnPropertyDescriptor({ a: 1 }, "a")) + " | " +
  J(Object.getOwnPropertyDescriptor(Object.defineProperty({}, "a", { value: 1 }), "a")));
attempt("14  isFrozen {} / prevExt {}", () =>
  J([Object.isFrozen({}), Object.isFrozen(Object.preventExtensions({}))]));
attempt("14  freeze is shallow", () => {
  const o = Object.freeze({ d: { n: 1 } }); o.d.n = 2; return J(o);
});
attempt("14  strict write to frozen", () => { "use strict"; const o = Object.freeze({ a: 1 }); o.a = 2; return "no throw"; });
attempt("15  chain of new TypeError", () => {
  const out = []; let c = Object.getPrototypeOf(new TypeError("x"));
  while (c !== null) { out.push(Object.prototype.hasOwnProperty.call(c, "constructor") ? c.constructor.name : "?"); c = Object.getPrototypeOf(c); }
  return out.join(" -> ") + " -> null";
});
attempt("15  String(Object.create(null))", () => String(Object.create(null)));
attempt("15  write does not walk", () => {
  const p = { v: "p" }; const o = Object.create(p); o.v = "o";
  return o.v + "/" + p.v + "/own:" + Object.prototype.hasOwnProperty.call(o, "v");
});
attempt("15  non-writable proto blocks", () => {
  "use strict";
  const p = Object.defineProperty({}, "v", { value: 1 }); const o = Object.create(p);
  o.v = 2; return "no throw";
});
attempt("15  Symbol.hasInstance overrides", () =>
  String("s" instanceof class { static [Symbol.hasInstance]() { return true; } }));
document.documentElement.appendChild(document.createElement("pre")).textContent =
  "===OUT===" + String.fromCharCode(10) + lines.join(String.fromCharCode(10)) + String.fromCharCode(10) + "===END===";
```

```html
<!-- js12b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js12b</title>
<script src="js12b-hb-browser.js"></script>
```

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

★★ **호스트가 정하는 칸이 하나도 없었다.** `14` 로 시작하는 네 줄이 Node 쪽과 전부 같다 —
디스크립터 두 벌도, **`isFrozen {} / prevExt {}` 가 `[false,true]` 인 것도**, 얕음도, 엄격 쓰기의 `TypeError` 도 같다.
★★★ **빈 객체가 안 얼어 있다는 실측이 두 번째 엔진 자리에서도 재확인된다** — 브리핑의 전제가 판이나 호스트 때문에 뒤집힌 것이 아니다.
★ **예외 문구까지 같은 것은 둘 다 V8 이기 때문**이지 명세가 정한 것이 아니다.

## 문법 — 형태와 규칙

```text
   디스크립터는 두 종류 -- 칸이 섞이면 TypeError 다

   데이터 디스크립터            접근자 디스크립터
   ┌────────────────┐          ┌────────────────┐
   │ value          │          │ get            │
   │ writable       │          │ set            │
   │ enumerable     │          │ enumerable     │
   │ configurable   │          │ configurable   │
   └────────────────┘          └────────────────┘
     ★ 둘 다 갖는 형태는 없다. value 와 get 을 한 객체에 같이 주면 거부된다.

   허가증을 읽는 문 / 쓰는 문

   읽기   Object.getOwnPropertyDescriptor(o, k)    한 칸
          Object.getOwnPropertyDescriptors(o)      전부      (ES2017)
          Reflect.getOwnPropertyDescriptor(o, k)   한 칸     (ES2015)

   쓰기   Object.defineProperty(o, k, desc)        실패하면 throw
          Object.defineProperties(o, descs)
          Reflect.defineProperty(o, k, desc)       실패하면 false 를 돌려준다 (ES2015)

   객체 통째로 잠그는 문 / 묻는 문

          Object.preventExtensions(o)   <->  Object.isExtensible(o)
          Object.seal(o)                <->  Object.isSealed(o)
          Object.freeze(o)              <->  Object.isFrozen(o)
```

- **디스크립터를 새로 만들 때 빠진 칸은 `false`**(값 칸은 `undefined`)다. **`true` 가 아니다.**
- **이미 있는 프로퍼티에 `defineProperty` 를 부르면 준 칸만 바뀐다.** 안 준 칸은 그대로 둔다.
- **`writable` 은 대입을, `configurable` 은 삭제와 재정의를, `enumerable` 은 보이기를 정한다.** 셋은 서로 상관없다.
- **`configurable: false` 여도 `writable: true -> false` 는 된다.** 반대는 안 된다.
- **`configurable: false` 여도 `writable` 이 `true` 인 동안에는 `value` 를 바꿀 수 있다**(대입으로도, `defineProperty` 로도).
- **같은 값·같은 플래그로 재정의하는 것은 언제나 허용된다** — 아무것도 안 바꾸기 때문이다.
- **접근자에는 `writable` 이 없다.** 그래서 **`freeze` 가 접근자를 잠그지 못한다.**
- **세 봉인 함수는 계단이다** — `preventExtensions` ⊂ `seal` ⊂ `freeze`.
- **셋 다 얕다.** 중첩 객체·배열은 그대로 바뀐다.
- **세 술어는 「그 함수를 불렀나」가 아니라 「지금 상태가 조건을 만족하나」를 묻는다.**
- **비확장인 빈 객체는 `isSealed` 도 `isFrozen` 도 `true`** 다. **확장 가능한 `{}` 는 둘 다 `false`** 다.
- **원시값에 물으면 터지지 않고 `isFrozen: true`** 라고 답한다.
- **막힌 쓰기는 엄격에서 `TypeError`, 비엄격에서 조용히 버려진다.**
  단 **`defineProperty`·`push`·`Object.assign` 은 모드와 무관하게 던진다.**

## 어디서 틀리나

### (1) ★★★ 「`Object.freeze` 했으니 안 바뀐다」로 읽는다

**세 군데가 새어 나간다** — **중첩 객체**(`[3]`) · **접근자 프로퍼티**(`[4]`) · **비엄격에서 시도한 쓰기의 결과 확인 누락**.
★ 특히 설정 객체·상태 객체를 얼릴 때, **한 겹만 얼고 안쪽은 그대로**라 「불변이다」라는 계약이 조용히 깨진다.

### (2) ★★★ 빈 객체가 얼어 있다고 생각한다

**`Object.isFrozen({})` 는 `false`** 다. `{}` 는 아직 **확장 가능**하기 때문이다.
★★ 헷갈리는 이유는 반대쪽이 참이어서다 — **`Object.isFrozen(Object.preventExtensions({}))` 는 `true`** 다.
**「빈 객체」가 아니라 「비확장 빈 객체」라야 얼어 있다.** 이 문서를 쓰는 과정에서 실제로 뒤집힌 전제다.

### (3) ★★★ 비엄격에서 「에러가 안 났으니 통과했다」로 읽는다

갈린 아홉 칸이 전부 이 모양이다 — **예외도 경고도 없고 반환값도 없는데 값이 안 바뀌어 있다.**
★ 발견하는 법은 셋 — **엄격 모드(또는 모듈)로 돌려 본다** · **쓴 뒤에 다시 읽는다** · **`isFrozen`/디스크립터를 찍어 본다.**

### (4) ★★★ `defineProperty` 로 만들고 `Object.keys` 에 안 나온다고 당황한다

**기본값이 `enumerable: false`** 라서다. 리터럴과 **정반대**다.
★ 같은 이유로 `JSON.stringify` 에도 `{ ...o }` 에도 `Object.assign` 에도 안 실린다 — **11번·13번의 뷰가 전부 이 플래그를 본다.**

### (5) ★★ `configurable: false` 를 「값까지 고정」으로 읽는다

**아니다.** `writable: true` 가 남아 있으면 **대입도 되고 `defineProperty` 로 값 바꾸기도 된다.**
★ 값까지 고정하려면 **`writable: false` 를 같이** 줘야 한다. 격자의 첫 덩어리가 그 반례 셋을 보인다.

### (6) ★★ `seal` 을 「값 고정」으로 읽는다

`seal` 은 **`configurable` 만 내린다.** 값은 그대로 바뀐다 — 엄격/비엄격 격자의 `sealed.a = 2` 가 **양쪽 다 `OK a=2`** 다.
★ `seal` 이 보장하는 것은 **「키 집합이 안 바뀐다」** 이지 「값이 안 바뀐다」가 아니다.

### (7) ★★ 「읽기 전용」과 「고정」을 같은 말로 쓴다

함수의 `.name`·`.length` 는 **`w=false` 인데 `c=true`** 다 — **대입으로는 못 바꾸는데 `defineProperty` 로는 바꿀 수 있다.**
배열의 `length` 는 정반대다(`w=true c=false`) — **값은 바꾸는데 지우거나 허가증은 못 고친다.**
★ **두 낱말을 갈라 써야 이 두 줄을 설명할 수 있다.**

### (8) ★★ `isFrozen` 이 `true` 이니 누가 `freeze` 를 불렀다고 읽는다

**술어는 호출 이력이 아니라 상태를 본다.** `preventExtensions` 만 부른 객체가 `isFrozen: true` 인 줄이 실측에 있다.
★ 반대로 **`freeze` 를 부른 객체 안쪽은 `isFrozen: false`** 다 — 그 둘을 헷갈리면 깊은 동결을 이미 한 줄로 착각한다.

### (9) ★ `defineProperty` 를 기존 프로퍼티에 부르며 「기본값으로 초기화된다」고 생각한다

**안 준 칸은 그대로 둔다.** `{ enumerable: false }` 하나만 줬더니 `writable`·`configurable` 이 `true` 로 남았다.
★ **새로 만들 때와 고칠 때의 규칙이 다르다**는 것이 이 함수에서 가장 자주 틀리는 자리다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- **세 플래그의 존재와 의미** · **리터럴과 대입이 `true,true,true` 를 만드는 것** ·
  **`defineProperty` 가 새로 만들 때 빠진 칸을 `false` 로 채우는 것** · **기존 프로퍼티에는 준 칸만 바꾸는 것.**
- **`configurable: false` 격자의 허용/거부 전부** — `writable` 의 일방통행 · **같은 값 재정의 허용** ·
  **`w=true` 인 동안 값 변경 허용** · `delete` 와 플래그 변경 금지.
- **세 봉인 함수가 계단이라는 것** · **셋 다 얕다는 것** · **`enumerable` 은 셋 다 안 건드린다는 것** ·
  **접근자에는 `writable` 이 없어 `freeze` 가 못 잠근다는 것.**
- **세 술어의 정의** — **비확장인 빈 객체가 `isSealed`·`isFrozen` 둘 다 `true`** 인 것 포함.
- **엄격에서 실패한 쓰기가 `TypeError` 인 것** · **비엄격에서 조용히 버려지는 것** ·
  **`defineProperty`·`push`·`Object.assign` 이 모드와 무관하게 던지는 것.**
- ★★★ **여기가 「예전엔 구현 나름이라던 것이 명세로 못 박힌」 자리다.**
  **ES5 가 `Object.defineProperty` 와 `Object.getOwnPropertyDescriptor` 를 들여오면서**
  프로퍼티의 **속성을 사용자 코드가 처음으로 관찰하고 조작할 수 있게** 됐다.
  그 전까지 「이 내장 프로퍼티는 왜 `for...in` 에 안 나오지?」는 **엔진에 물어볼 방법이 없는 질문**이었다.
  ★ **ES2015 가 `Reflect` 와 프록시 불변식으로 그 계약을 확장했다** — 디스크립터가
  **「엔진과 사용자 코드가 프로퍼티에 대해 주고받는 공용 언어」** 가 된 것이 그 판이다.
  ★★ 판별은 **[ECMA-262 아카이브](https://262.ecma-international.org/)** 로만 접지했다 — **조항 번호는 인용하지 않는다.**
  ★ 13번의 「열거 순서가 ES2015·ES2020 에 못 박혔다」와 **같은 집안이고, 이쪽이 먼저 일어난 일**이다.

### 엔진(V8) 구현 · 이 판의 관찰

- **예외 문구 전부** — `Cannot redefine property: p` · `Cannot delete property 'p' of #<Object>` ·
  `Cannot assign to read only property 'a' of object '#<Object>'` ·
  `Cannot add property nu, object is not extensible` ·
  `Cannot set property a of #<Object> which has only a getter` 는 **V8 의 문구**다.
  **종류(`TypeError`·`ReferenceError`)만 명세가 정한다.**
- **객체를 적는 방식**(`#<Object>` · `[object Array]`)도 V8 의 표기다. ★ 앞엣것이 브랜드 태그처럼 보이지만
  **우리가 ③ 창을 연 것이 아니라 엔진이 메시지에 적어 넣은 것**이다 — 근거로 쓰지 않는다.
- **두 판(18·20)과 Chrome 151 이 이 주제에서 `toSorted` 한 줄 빼고 전부 같았다** — 셋 다 V8 이기 때문이지 보장이 아니다.
- **`Array.prototype.toSorted` 의 존재 여부** — 이것은 엔진의 사정이 아니라 **판(ES2023)의 문제**다. 25번이 정본이다.

### 호스트가 정하는 것 — ECMA-262 밖

- **없다.** 브라우저 대조에서 호스트가 정하는 칸이 0개였다.
  ★ 다만 **호스트 객체**(DOM 요소 등)는 자기만의 디스크립터를 가질 수 있다 — **그것은 안 던져 봤다.**

### 그래서 이렇게 적으면 틀린다

- 「`Object.freeze` 하면 그 객체는 변하지 않는다」 — **아니다.** 중첩도 접근자도 그대로 변한다.
- 「빈 객체는 얼어 있다」 — **아니다.** `isFrozen({})` 는 `false` 다. **비확장 빈 객체**라야 `true` 다.
- 「`configurable: false` 면 아무것도 못 바꾼다」 — **아니다.** 27칸 중 16칸이 통과한다.
- 「`seal` 은 값을 고정한다」 — **아니다.** `writable` 을 안 건드린다.
- 「`defineProperty` 로 만든 프로퍼티도 `Object.keys` 에 보인다」 — **아니다.** 기본이 `enumerable: false` 다.
- 「비엄격에서 안 터졌으니 쓰기가 성공했다」 — **아니다.** 조용히 버려진 것이다.
- 「원시값에 `isFrozen` 을 부르면 터진다」 — **이 판에서는 아니다.** `true` 를 돌려준다.
- 「동결하면 느려진다(또는 빨라진다)」 — **이 문서는 안 쟀다.** 어느 쪽도 적지 않는다.

## 언제 쓰고 언제 안 쓰나

- **`Object.freeze`** — **상수 테이블·설정 객체·열거형 대용**처럼 **한 겹이고 값만 있는** 객체에.
  ★ 중첩이 있으면 **깊은 동결을 따로 써야 한다**(48번).
- **`Object.seal`** — **키 집합만 고정**하고 값은 바뀌어도 될 때. 오타로 새 키가 생기는 사고를 막는다.
- **`Object.preventExtensions`** — **추가만 막고 싶을 때.** ★ 프로토타입 교체까지 같이 막힌다는 것을 기억한다.
- **`Object.defineProperty`** — **열거에서 숨긴 메타데이터**를 붙일 때, 또는 **읽기 전용 접근자**를 만들 때.
  ★ 일상적인 프로퍼티 추가에 쓰면 **기본값이 정반대**라 조용한 사고가 난다 — 그때는 그냥 대입한다.
- **`Object.getOwnPropertyDescriptor(s)`** — **「왜 안 보이지 / 왜 안 바뀌지」를 진단할 때의 첫 도구.**
  ★ 얕은 복사가 getter 를 값으로 뭉개는 것을 피할 때도 쓴다(`defineProperties` 와 짝이다 — 27번·48번).
- **안 쓸 자리** — **동결을 불변 자료구조의 대용으로** 쓰는 것. 얕고, 접근자를 못 막고, 비엄격에서 조용하다.
  **계약을 코드로 강제하려면 동결이 아니라 타입·캡슐화·복사 중 하나**를 골라야 한다.

## 핵심 문장

1. **막힌 것은 값에 안 보인다 — 허가증의 세 플래그에만 적혀 있다.**
2. **리터럴은 `true,true,true`, `defineProperty` 의 기본은 `false,false,false` — 세 칸이 전부 뒤집혀 있다.**
3. **`writable` 은 대입을, `configurable` 은 삭제와 재정의를, `enumerable` 은 보이기를 정한다 — 셋은 서로 상관없다.**
4. **세 봉인 함수는 계단이고 셋 다 얕다 — 그리고 접근자는 `freeze` 로도 안 잠긴다.**
5. **엄격에서는 `TypeError` 로 보이고 비엄격에서는 아무 흔적도 없다 — 갈린 칸이 13칸 중 9칸이다.**

## 관련 자료

- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) — **그쪽이 「어느 문법이 어떤 디스크립터를 만드나」의 정본**이다. 여기는 **그 플래그가 무엇을 막는지**부터.
- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — **그쪽이 조회·쓰기가 체인을 타는 경로의 정본**이다. 여기는 **프로토타입의 `w=false` 가 자식의 쓰기를 막는다**는 한 칸까지.
- [12 — 옵셔널 체이닝·널 병합·논리 할당](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) — **그쪽이 「막혔을 때 무엇이 보이나」까지** 갔다. 여기는 **왜 막히나**부터.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — **그쪽이 `{ ...o }` 의 정본**이다. 여기는 **그것이 보는 `enumerable` 의 정본**이다.
- [목록의 **18번 주제**](../18-for-in-and-enumeration/) 「`for...in` 과 열거」 — **그쪽이 열거와 체인 순회의 정본**이다.
- [목록의 **25번 주제**](../25-array-non-mutating-and-copy-methods/) 「배열 비변형·복사 메서드」 — **그쪽이 `toSorted`(ES2023)의 정본**이다. 여기는 **동결된 배열에서 갈린 한 줄**까지.
- [목록의 **27번 주제**](../27-object-static-methods/) 「`Object` 정적 메서드」 — **그쪽이 `Object.assign`·`entries` 의 정본**이다. 여기는 **그것들이 이 플래그를 본다는 사실**까지.
- [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」 — **그쪽이 모드가 바꾸는 규칙 전부의 정본**이다. 여기는 **막힌 쓰기가 갈리는 칸**까지.
- [목록의 **45번 주제**](../45-proxy/) 「`Proxy`」 · [목록의 **46번 주제**](../46-reflect/) 「`Reflect`」 — **그쪽이 트랩과 불변식의 정본**이다. 여기는 **디스크립터가 그 계약의 언어**라는 사실까지(프록시는 안 던져 봤다).
- [목록의 **48번 주제**](../48-deep-copy-methods-compared/) 「깊은 복사 수단 비교」 — **그쪽이 깊은 동결·깊은 복사의 정본**이다. 여기는 **얕다는 사실**까지.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **29번** 「클래스와 속성 탐색」 —
  ★★ **이름이 같고 하는 일이 다르다.** 파이썬의 **데이터 디스크립터는 조회 우선순위를 바꿔 「인스턴스 칸을 이긴다」**.
  **JS 의 디스크립터는 플래그 셋일 뿐 조회 순서를 한 칸도 바꾸지 않는다** — 조회 경로 대비의 본론은 15번이 맡는다.

## 용어 풀이

- **프로퍼티 디스크립터(property descriptor)** — 프로퍼티의 값과 플래그를 담은 평범한 객체. 꺼내면 **사본**이다.
- **데이터 프로퍼티(data property)** — `value` 와 `writable` 을 갖는 프로퍼티. 보통의 프로퍼티가 전부 이것이다.
- **접근자 프로퍼티(accessor property)** — `get`/`set` 함수를 갖는 프로퍼티. **`value` 도 `writable` 도 없다.**
- **`writable`** — 대입(`o.a = 2`)으로 값을 바꿀 수 있나.
- **`enumerable`** — `Object.keys`·`for...in`·`JSON.stringify`·`{ ...o }`·`Object.assign` 에 보이나.
- **`configurable`** — 삭제하거나 디스크립터를 고쳐 쓸 수 있나. **데이터↔접근자 변환도 이 플래그가 정한다.**
- **확장 가능(extensible)** — 새 프로퍼티를 더할 수 있나. **프로토타입 교체 가능 여부도 여기 걸려 있다.**
- **own 프로퍼티** — 프로토타입이 아니라 그 객체 자신이 들고 있는 프로퍼티. 디스크립터는 **own 만** 읽는다.
- **얕은 동결(shallow freeze)** — 그 객체 한 겹만 잠그고 참조가 가리키는 저쪽은 안 잠그는 것.
- **조용한 실패(silent failure)** — 비엄격 모드에서 막힌 쓰기가 예외도 경고도 없이 버려지는 것.
- **엄격 모드(strict mode)** — `"use strict"` 나 모듈에서 켜지는 모드. 조용히 실패하던 것이 `TypeError` 가 된다.

## 더 들어가면

- **세 술어가 「상태」를 묻는다는 설계가 깊은 동결을 어렵게 만든다.** `isFrozen` 이 `true` 여도
  **그 안쪽은 아무것도 보장하지 않으므로**, 깊은 동결의 검사는 **재귀로 직접 돌아야** 한다.
  ★ 그리고 그 재귀는 **순환 참조에서 멈출 방법을 스스로 마련해야** 한다 — 언어가 주지 않는다.
- **`configurable: false` 가 「되돌릴 수 없다」는 성질을 언어 안에 만든다.** JS 에서 이런 **단방향 전이**는 드물다.
  ★ 프록시 불변식이 이 단방향성 위에 세워져 있다 — 「한 번 보고한 것을 나중에 뒤집을 수 없다」가 그 계약의 골자다(45번).
- **접근자가 `freeze` 를 빠져나가는 것은 버그가 아니라 정의다.** `freeze` 는 **`writable` 을 내리는 일**을 하는데
  접근자에는 그 칸이 없다. ★ **접근자까지 잠그려면 `configurable: false` 로 만들어 `set` 을 못 바꾸게 하는 것까지가 전부**이고,
  **`get` 이 무엇을 돌려주느냐는 언어가 관여하지 않는다.**
- **엄격 모드가 이 주제의 진단 도구라는 점이 실무의 결론이다.** 모듈(`.mjs`·ESM)은 **항상 엄격**이므로
  같은 코드가 **번들러를 거치느냐에 따라 조용하던 버그가 터지기 시작한다.** ★ 35번·42번에서 이어진다.
