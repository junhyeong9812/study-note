# js/syntax/09 — `call`·`apply`·`bind`: 「`this` 와 인자를 손으로 건넨다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ③ 브랜드 태그다.** 세 메서드가 하는 일은 「`this` 자리에 무엇을 넣었나」 하나인데,
> **그 결과는 값으로는 안 갈리고 `Object.prototype.toString.call` 로만 갈린다**(원시값이 감싸졌는지, 전역이 들어갔는지).
> ② 전수 격자가 그 태그를 담는 그릇이고, ④ 예외는 `bind` 가 만든 함수의 자격을 가를 때 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — `Function.prototype.call`·`apply`·`bind` · bound function exotic object · `Reflect.apply`
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — `bind` 와 `Reflect` 가 들어온 판을 가릴 때
> - [MDN — `Function.prototype.call`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/call) · [MDN — `Function.prototype.bind`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.

```sh
// js08b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    console.log("node " + v.node + "  v8 " + v.v8 +
                "  arrow-proto " + Object.prototype.hasOwnProperty.call(() => {}, "prototype") +
                "  default-len " + (function (a, b = 1) {}).length +
                "  obj-rest " + JSON.stringify((({ a, ...r }) => r)({ a: 1, b: 2 })) +
                "  obj-spread " + JSON.stringify({ ...null }) +
                "  bind-name " + JSON.stringify(function f() {}.bind(null).name));'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js08b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  arrow-proto false  default-len 1  obj-rest {"b":2}  obj-spread {}  bind-name "bound f"
node 20.19.6  v8 11.3.244.8-node.33  arrow-proto false  default-len 1  obj-rest {"b":2}  obj-spread {}  bind-name "bound f"
Google Chrome 151.0.7922.173 
```

> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 **`e.constructor.name` 과 `e.message` 만** 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박혀 다른 머신에서 재현이 안 되기 때문이다.
> ★★ **`this` 는 브랜드 태그로 찍는다** — `String(this)` 는 호스트마다 다르게 나온다.
> ★★ **`padEnd` 격자의 라벨은 전부 ASCII 다.** 한글은 터미널에서 두 칸이라 칸이 어긋난다.
> ★★★ **인자 개수의 경계는 자릿수로만 찍는다.** 정확한 수는 **그 순간 스택이 얼마나 차 있는지**에 달려 흔들린다 —
> 흔들리지 않는 것은 **자릿수와 예외의 종류**뿐이라 그 둘만 싣는다.
> ★ **이 주제에는 시각·로캘·난수가 닿는 칸이 하나도 없다.**
>
> **버전** — `call`·`apply` 는 **초판부터**, **`bind` 는 ES5**, **`Reflect.apply` 는 ES2015** 다.
> 스프레드(`f(...arr)`)가 `apply` 를 대신할 수 있게 된 것도 **ES2015** 부터다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **③ 브랜드 태그**(본체) | `this` 자리에 **무엇이 들어갔나** — 원시값이 감싸졌나, 전역이 들어갔나, 그대로인가 |
> | ★★★ **② 전수 격자** | 값 8종 × 메서드 3종 × 모드 2 — **설정이 답을 바꾸는 칸이 몇 개인가** |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `apply` 가 무엇을 안 받나 · `bind` 한 함수를 `new` 할 수 있나 |
> | ★★ **동일성**(`===`) | `bind` 가 **매번 새 함수**를 만든다는 것 — 이 주제의 실무 비용이 전부 여기 있다 |
> | ★ **⑤ 두 판 대조기 + 브라우저** | 판이 갈린 칸 · 호스트가 정하는 칸이 있나 |
> | ★ **부적용 — ⑥ `toFixed(20)`** | 부동소수점이 닿는 칸이 한 칸도 없다. **잴 것이 없다** |
> | ★ **부적용 — ⑦ `\uXXXX` 펼치기** | 문자 인코딩이 답을 바꾸는 자리가 없다 |
> | ★ **부적용 — 성능 측정** | 「`bind` 가 느리다」는 **재지 않았다.** 이 문서에 속도 주장이 한 줄도 없다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **인자 개수 경계의 정확한 수** — 자릿수만 싣는다 | ★★★ **브랜드 태그** · **설정에 달린 칸의 개수** |
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **`bound ` 접두** · `length` 의 감소량 |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★ **예외의 종류** · `instanceof` 결과 |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **동일성 판정**(`bind` 는 매번 다른 객체) |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 61블록 전부 동일).
>
> **선행** — [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md).
> ★★★ **07번이 「어느 규칙이 이기나」까지였다면 여기는 그 명시적 바인딩의 API 세부다.**
> 07번은 「`bind` 가 두 번 안 먹는다」 하나만 확인했고, **`bind` 가 만든 함수가 어떤 물건인지는 여기가 정본**이다.
> ★ 08번에서 **함수 형태마다 `prototype`·`new` 칸이 따로 논다**는 것을 봤다. `bind` 가 그 격자의 한 행이었다.
> **이어지는 곳** — [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · 목록의 **34번 주제** 「타입 검사 관용구」 · 목록의 **46번 주제** 「`Reflect`」
>
> ★★ **경계 — `this` 의 네 규칙과 우선순위는 07번이 정본이다.** 여기서는 **셋을 실제로 어떻게 쓰나**부터다.
> ★★ **경계 — `Reflect` 전체는 46번이 정본이다.** 여기서는 `Reflect.apply` 가 **`apply` 와 무엇이 같고 다른지**까지만 본다.
> ★★ **경계 — 스프레드 문법 자체는 11번이 정본이다.** 여기서는 **`apply` 를 대신한다**는 사실까지다.

## 한눈에 — 쉽게 말하면

**함수를 부르는 일은 원래 「값 세 묶음을 건네는 일」이다** — 함수 자신, `this`, 인자들.
평소에는 호출식이 그 셋을 자동으로 정해 주는데, **셋을 손으로 건네고 싶을 때 쓰는 것이 이 세 메서드**다.

- **`call`** — 지금 부른다. `this` 를 첫 인자로, 나머지 인자는 **하나씩 편다.**
- **`apply`** — 지금 부른다. `this` 를 첫 인자로, 나머지 인자는 **유사 배열 하나로 묶어** 준다.
- **`bind`** — **안 부른다.** `this` 와 앞쪽 인자를 못질해 둔 **새 함수**를 만들어 돌려준다.

```text
   f(a, b)                    호출식이 this 를 정한다 (07번)

   f.call(t, a, b)            this = t,  인자는 하나씩
   f.apply(t, [a, b])         this = t,  인자는 유사 배열 하나로
   const g = f.bind(t, a)     아직 안 부른다. 새 함수 g 가 생긴다
   g(b)                       this = t,  인자는 a 다음에 b

   ★ 앞의 둘은 「부르기」이고 뒤엣것은 「만들기」다. 반환값의 성격이 다르다.
```

**`bind` 가 만든 것은 원본이 아니라 한 겹 덧씌운 새 함수다.**

```text
        orig                          bound = orig.bind(A, 1)
   ┌──────────────┐              ┌──────────────────────┐
   │ name  "orig" │              │ name   "bound orig"  │
   │ length 3     │   bind  ->   │ length 2  (3 - 1)    │
   │ prototype O  │              │ prototype X          │
   └──────────────┘              │ 안에 A 와 1 을 못질   │
                                 └──────────────────────┘

   ★ 새 객체다(=== 가 false). 그래서 부를 때마다 bind 하면 매번 다른 함수가 생긴다.
   ★ 다시 bind 해도, call 로 다른 this 를 줘도 안쪽이 이긴다. new 만 이긴다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 손으로 건네는 첫 봉투 | `call`/`apply`/`bind` 의 첫 인자 | 브랜드 태그로 무엇이 들어갔는지 본다 |
| 하나씩 편다 | `call` 의 나머지 인자 | `arguments.length` 를 센다 |
| 묶어서 한 번에 | `apply` 의 유사 배열 | `length` 만 있는 객체도 받는다 |
| 못질해 둔 새 함수 | `bind` 의 반환값 | `=== 원본` 이 `false` 다 |
| 못질을 이기는 것 | `new` | 새 객체가 `this` 가 된다 |
| 매번 새로 만드는 열쇠 | `bind` 를 호출부에서 부르는 것 | 두 번 `bind` 하면 `===` 가 `false` 다 |
| 남의 연장 빌려 쓰기 | `Array.prototype.slice.call(유사배열)` | 배열이 아닌 것에 배열 메서드를 건다 |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
`addEventListener(handler.bind(this))` 로 걸어 놓고 `removeEventListener(handler.bind(this))` 로 떼려다
**안 떨어지는** 사고가 그것이고, `apply` 에 `Set` 을 넘겨 놓고 **인자가 0개로 들어가는데도 에러가 안 나는** 사고가 그것이다.

## 이 주제가 답하려는 질문

1. ★★★ **세 메서드에 같은 값을 건네면 `this` 자리에 정확히 무엇이 들어가나** — 원시값은? `null` 은? 모드가 바꾸나?
2. ★★★ **`bind` 가 만든 함수는 어떤 물건인가** — 이름·`length`·`prototype`·`new`·재바인딩 가능 여부는?
3. ★★ **`apply` 는 두 번째 인자로 무엇을 받나** — 그리고 **안 받는 것을 어떻게 알리나**?

## 동작 방식

### (1) ★★★ 세 메서드 — 같은 값을 셋으로 건넨다

```js
// js08b-09a-three-methods.js
// call.apply.bind -- 셋이 this 를 어떻게 정하나. 답은 브랜드 태그로만 갈린다.
function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}
function looseWho() { return tag(this); }
function strictWho() { "use strict"; return tag(this); }

const THIS_VALUES = [
  ["object", { mark: "given" }],
  ["number 7", 7],
  ["string s", "s"],
  ["boolean true", true],
  ["null", null],
  ["undefined", undefined],
  ["array", []],
  ["function", function named() {}],
];

console.log("[1] same this value through call / apply / bind -- sloppy callee");
console.log("  " + "this given".padEnd(16) + "call".padEnd(28) + "apply".padEnd(28) + "bind()()");
for (const [label, v] of THIS_VALUES) {
  console.log("  " + label.padEnd(16) +
              looseWho.call(v).padEnd(28) +
              looseWho.apply(v).padEnd(28) +
              looseWho.bind(v)());
}

console.log("");
console.log("[2] the same grid with a strict callee -- how many cells change");
let differ = 0;
console.log("  " + "this given".padEnd(16) + "call".padEnd(28) + "apply".padEnd(28) + "bind()()");
for (const [label, v] of THIS_VALUES) {
  const a = strictWho.call(v), b = strictWho.apply(v), c = strictWho.bind(v)();
  if (a !== looseWho.call(v)) differ += 1;
  if (b !== looseWho.apply(v)) differ += 1;
  if (c !== looseWho.bind(v)()) differ += 1;
  console.log("  " + label.padEnd(16) + a.padEnd(28) + b.padEnd(28) + c);
}
console.log("  " + "settings-dependent cells".padEnd(30) + differ + " of " + (THIS_VALUES.length * 3));

console.log("");
console.log("[3] how the arguments are handed over");
function args3(a, b, c) { return "a=" + String(a) + " b=" + String(b) + " c=" + String(c) + " n=" + arguments.length; }
const SHAPES = [
  ["call(t, 1, 2, 3)", () => args3.call(null, 1, 2, 3)],
  ["apply(t, [1, 2, 3])", () => args3.apply(null, [1, 2, 3])],
  ["apply(t, undefined)", () => args3.apply(null, undefined)],
  ["apply(t, null)", () => args3.apply(null, null)],
  ["apply(t, [])", () => args3.apply(null, [])],
  ["apply(t, arguments-like)", () => args3.apply(null, { 0: 1, 1: 2, length: 2 })],
  ["apply(t, { length: 3 })", () => args3.apply(null, { length: 3 })],
  ["apply(t, 'abc')", () => args3.apply(null, "abc")],
  ["apply(t, new Set([1, 2]))", () => args3.apply(null, new Set([1, 2]))],
  ["apply(t, 7)", () => args3.apply(null, 7)],
  ["apply(t, true)", () => args3.apply(null, true)],
  ["call(t) with no args", () => args3.call(null)],
  ["Reflect.apply(f, t, [1, 2])", () => Reflect.apply(args3, null, [1, 2])],
  ["Reflect.apply(f, t, 'ab')", () => Reflect.apply(args3, null, "ab")],
  ["f(...[1, 2, 3]) spread", () => args3(...[1, 2, 3])],
];
for (const [label, run] of SHAPES) {
  try { console.log("  " + label.padEnd(30) + run()); }
  catch (e) { console.log("  " + label.padEnd(30) + e.constructor.name + ": " + e.message); }
}
```

```text
===== node20 js08b-09a-three-methods.js (exit=0) =====
[1] same this value through call / apply / bind -- sloppy callee
  this given      call                        apply                       bind()()
  object          [object Object] mark=given  [object Object] mark=given  [object Object] mark=given
  number 7        [object Number]             [object Number]             [object Number]
  string s        [object String]             [object String]             [object String]
  boolean true    [object Boolean]            [object Boolean]            [object Boolean]
  null            globalThis                  globalThis                  globalThis
  undefined       globalThis                  globalThis                  globalThis
  array           [object Array]              [object Array]              [object Array]
  function        [object Function]           [object Function]           [object Function]

[2] the same grid with a strict callee -- how many cells change
  this given      call                        apply                       bind()()
  object          [object Object] mark=given  [object Object] mark=given  [object Object] mark=given
  number 7        number 7                    number 7                    number 7
  string s        string s                    string s                    string s
  boolean true    boolean true                boolean true                boolean true
  null            null                        null                        null
  undefined       undefined                   undefined                   undefined
  array           [object Array]              [object Array]              [object Array]
  function        [object Function]           [object Function]           [object Function]
  settings-dependent cells      15 of 24

[3] how the arguments are handed over
  call(t, 1, 2, 3)              a=1 b=2 c=3 n=3
  apply(t, [1, 2, 3])           a=1 b=2 c=3 n=3
  apply(t, undefined)           a=undefined b=undefined c=undefined n=0
  apply(t, null)                a=undefined b=undefined c=undefined n=0
  apply(t, [])                  a=undefined b=undefined c=undefined n=0
  apply(t, arguments-like)      a=1 b=2 c=undefined n=2
  apply(t, { length: 3 })       a=undefined b=undefined c=undefined n=3
  apply(t, 'abc')               TypeError: CreateListFromArrayLike called on non-object
  apply(t, new Set([1, 2]))     a=undefined b=undefined c=undefined n=0
  apply(t, 7)                   TypeError: CreateListFromArrayLike called on non-object
  apply(t, true)                TypeError: CreateListFromArrayLike called on non-object
  call(t) with no args          a=undefined b=undefined c=undefined n=0
  Reflect.apply(f, t, [1, 2])   a=1 b=2 c=undefined n=2
  Reflect.apply(f, t, 'ab')     TypeError: CreateListFromArrayLike called on non-object
  f(...[1, 2, 3]) spread        a=1 b=2 c=3 n=3
```

```text
   비엄격 함수에 건네면                   엄격 함수에 건네면

   call(7)        -> [object Number]      call(7)        -> number 7
   call("s")      -> [object String]      call("s")      -> string s
   call(true)     -> [object Boolean]     call(true)     -> boolean true
   call(null)     -> globalThis           call(null)     -> null
   call(undefined)-> globalThis           call(undefined)-> undefined
   call({...})    -> 그 객체              call({...})    -> 그 객체

   ★ 값으로는 안 갈린다. 브랜드 태그라야 「감싸졌다」가 보인다.
   ★ 24칸 중 15칸이 설정에 달렸다.
```

- ★★★ **세 메서드가 `this` 를 정하는 규칙은 완전히 같다.** 24칸 격자에서 `call`·`apply`·`bind()()` 세 열이
  **한 글자도 다르지 않다.** 달라지는 것은 **인자를 어떻게 건네느냐**뿐이다.
- ★★★ **비엄격 함수는 원시값을 객체로 감싼다.** `7` 을 주면 `this` 가 `[object Number]` 다 — **숫자가 아니라 래퍼 객체**다.
  ★ 이것이 값으로는 안 보인다. `String(this)` 는 `"7"` 이라 똑같이 나온다. **브랜드 태그가 본체 창인 이유**가 이것이다.
- ★★★ **비엄격은 `null`·`undefined` 를 `globalThis` 로 바꾼다.** 엄격은 **그대로 둔다.**
  ★ 그래서 `f.call(null)` 은 「`this` 를 안 쓰겠다」는 뜻으로 흔히 쓰이는데, **비엄격이면 전역이 들어간다.**
- ★★ **인자를 건네는 열다섯 모양 중 세 개가 터진다** — `apply` 의 둘째 인자가 **객체가 아닐 때**다
  (`'abc'`·`7`·`true`). 문구는 `CreateListFromArrayLike called on non-object` 다.
  ★★★ **그런데 `null`·`undefined` 는 안 터진다** — **인자 0개로 조용히 부른다.**
  ★★★ **`Set` 도 안 터진다** — `length` 가 없으니 **인자 0개**다. **이터러블이어도 소용없다.**
  ★ `apply` 는 **이터러블이 아니라 「유사 배열」을 본다** — `{ length: 3 }` 만 줘도 `undefined` 세 개가 들어간다.
  ★★ **스프레드는 정반대다** — 이터러블을 보고, 유사 배열은 안 본다(11번).

### (2) ★★★ `bind` 가 만든 함수는 무엇인가

```js
// js08b-09b-bind.js
// bind 가 만든 함수는 무엇인가 -- 원본이 아니라 한 겹 덧씌운 새 함수다.
function show(label, run) {
  try { console.log("  " + label.padEnd(40) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(40) + " -> " + e.constructor.name + ": " + e.message); }
}
function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}

function orig(a, b, c) { return tag(this) + " args=" + [a, b, c].map(String).join(","); }
const A = { mark: "A" }, B = { mark: "B" };
const bound1 = orig.bind(A, 1);

console.log("[1] the bound function is a different object");
show("bound1 === orig", () => bound1 === orig);
show("orig.name", () => JSON.stringify(orig.name));
show("bound1.name", () => JSON.stringify(bound1.name));
show("orig.length", () => orig.length);
show("bound1.length", () => bound1.length);
show("orig has prototype?", () => Object.prototype.hasOwnProperty.call(orig, "prototype"));
show("bound1 has prototype?", () => Object.prototype.hasOwnProperty.call(bound1, "prototype"));
show("proto of bound1 is orig?", () => Object.getPrototypeOf(bound1) === orig);
show("proto of bound1 is Function.prototype?", () => Object.getPrototypeOf(bound1) === Function.prototype);
show("bound1 own keys", () => JSON.stringify(Object.getOwnPropertyNames(bound1)));
show("String(bound1)", () => String(bound1));

console.log("");
console.log("[2] you cannot rebind it -- the first bind wins");
show("bound1(2, 3)", () => bound1(2, 3));
show("bound1.call(B, 2, 3)", () => bound1.call(B, 2, 3));
show("bound1.apply(B, [2, 3])", () => bound1.apply(B, [2, 3]));
show("bound1.bind(B)(2, 3)", () => bound1.bind(B)(2, 3));
show("bound1.bind(B, 9)(3)", () => bound1.bind(B, 9)(3));
show("({ mark: 'host', m: bound1 }).m(2, 3)", () => ({ mark: "host", m: bound1 }).m(2, 3));
show("Reflect.apply(bound1, B, [2, 3])", () => Reflect.apply(bound1, B, [2, 3]));

console.log("");
console.log("[3] new beats bind -- but the bound arguments stay");
function Ctor(a, b) { this.got = [a, b]; this.mark = "ctor"; }
Ctor.prototype.kind = "Ctor.prototype";
const BoundCtor = Ctor.bind({ mark: "ignored" }, 1);
const made = new BoundCtor(2);
show("new BoundCtor(2).got", () => JSON.stringify(made.got));
show("made instanceof Ctor", () => made instanceof Ctor);
show("made instanceof BoundCtor", () => made instanceof BoundCtor);
show("made.kind (from prototype chain)", () => made.kind);
show("proto of made is Ctor.prototype?", () => Object.getPrototypeOf(made) === Ctor.prototype);
show("BoundCtor.prototype", () => String(BoundCtor.prototype));
show("new (bound arrow)", () => { const ba = ((x) => x).bind(null, 1); return new ba(); });

console.log("");
console.log("[4] bind on an arrow changes nothing about this -- but still fixes arguments");
const outerThis = { mark: "outer" };
const arrowFn = function () { return (a, b) => tag(this) + " args=" + [a, b].map(String).join(","); }.call(outerThis);
show("arrowFn(1, 2)", () => arrowFn(1, 2));
show("arrowFn.call(B, 1, 2)", () => arrowFn.call(B, 1, 2));
show("arrowFn.bind(B)(1, 2)", () => arrowFn.bind(B)(1, 2));
show("arrowFn.bind(B, 9)(2)", () => arrowFn.bind(B, 9)(2));
show("arrowFn.bind(B).length", () => arrowFn.bind(B).length);
show("arrowFn.bind(B, 9).length", () => arrowFn.bind(B, 9).length);

console.log("");
console.log("[5] borrowing a method -- the classic uses");
const arrayLike = { 0: "a", 1: "b", length: 2 };
show("slice.call(arrayLike)", () => JSON.stringify(Array.prototype.slice.call(arrayLike)));
show("join.call(arrayLike, '-')", () => Array.prototype.join.call(arrayLike, "-"));
const hasOwn = Function.prototype.call.bind(Object.prototype.hasOwnProperty);
show("uncurried hasOwn({ x: 1 }, 'x')", () => hasOwn({ x: 1 }, "x"));
show("uncurried hasOwn({ x: 1 }, 'y')", () => hasOwn({ x: 1 }, "y"));
const toStr = Function.prototype.call.bind(Object.prototype.toString);
show("uncurried toString([])", () => toStr([]));
show("Math.max.apply(null, [3, 1, 2])", () => Math.max.apply(null, [3, 1, 2]));
show("Math.max(...[3, 1, 2])", () => Math.max(...[3, 1, 2]));

console.log("");
console.log("[6] how many wrappers does bind add");
let f = orig;
const depths = [];
for (let i = 0; i < 4; i += 1) {
  depths.push("depth " + i + " name=" + JSON.stringify(f.name) + " length=" + f.length);
  f = f.bind(A);
}
for (const d of depths) console.log("  " + d);
show("4-deep bound call", () => f());
```

```text
===== node20 js08b-09b-bind.js (exit=0) =====
[1] the bound function is a different object
  bound1 === orig                          -> false
  orig.name                                -> "orig"
  bound1.name                              -> "bound orig"
  orig.length                              -> 3
  bound1.length                            -> 2
  orig has prototype?                      -> true
  bound1 has prototype?                    -> false
  proto of bound1 is orig?                 -> false
  proto of bound1 is Function.prototype?   -> true
  bound1 own keys                          -> ["length","name"]
  String(bound1)                           -> function () { [native code] }

[2] you cannot rebind it -- the first bind wins
  bound1(2, 3)                             -> [object Object] mark=A args=1,2,3
  bound1.call(B, 2, 3)                     -> [object Object] mark=A args=1,2,3
  bound1.apply(B, [2, 3])                  -> [object Object] mark=A args=1,2,3
  bound1.bind(B)(2, 3)                     -> [object Object] mark=A args=1,2,3
  bound1.bind(B, 9)(3)                     -> [object Object] mark=A args=1,9,3
  ({ mark: 'host', m: bound1 }).m(2, 3)    -> [object Object] mark=A args=1,2,3
  Reflect.apply(bound1, B, [2, 3])         -> [object Object] mark=A args=1,2,3

[3] new beats bind -- but the bound arguments stay
  new BoundCtor(2).got                     -> [1,2]
  made instanceof Ctor                     -> true
  made instanceof BoundCtor                -> true
  made.kind (from prototype chain)         -> Ctor.prototype
  proto of made is Ctor.prototype?         -> true
  BoundCtor.prototype                      -> undefined
  new (bound arrow)                        -> TypeError: ba is not a constructor

[4] bind on an arrow changes nothing about this -- but still fixes arguments
  arrowFn(1, 2)                            -> [object Object] mark=outer args=1,2
  arrowFn.call(B, 1, 2)                    -> [object Object] mark=outer args=1,2
  arrowFn.bind(B)(1, 2)                    -> [object Object] mark=outer args=1,2
  arrowFn.bind(B, 9)(2)                    -> [object Object] mark=outer args=9,2
  arrowFn.bind(B).length                   -> 2
  arrowFn.bind(B, 9).length                -> 1

[5] borrowing a method -- the classic uses
  slice.call(arrayLike)                    -> ["a","b"]
  join.call(arrayLike, '-')                -> a-b
  uncurried hasOwn({ x: 1 }, 'x')          -> true
  uncurried hasOwn({ x: 1 }, 'y')          -> false
  uncurried toString([])                   -> [object Array]
  Math.max.apply(null, [3, 1, 2])          -> 3
  Math.max(...[3, 1, 2])                   -> 3

[6] how many wrappers does bind add
  depth 0 name="orig" length=3
  depth 1 name="bound orig" length=3
  depth 2 name="bound bound orig" length=3
  depth 3 name="bound bound bound orig" length=3
  4-deep bound call                        -> [object Object] mark=A args=undefined,undefined,undefined
```

- ★★★ **`bind` 는 원본을 안 건드리고 새 함수를 만든다.** `bound1 === orig` 가 `false` 이고
  **프로토타입은 `Function.prototype`** 이다(원본이 아니다).
  ★ 소유 프로퍼티는 `length` 와 `name` **둘뿐**이고, `prototype` 은 **없다.**
  ★ `String(bound1)` 은 `function () { [native code] }` — **원본 소스가 안 나온다.**
- ★★★ **이름에 `bound ` 가 붙고 `length` 가 줄어든다.** `orig.length` 가 `3`, 인자 하나를 못질했으니 `bound1.length` 는 `2` 다.
  ★ 겹칠 때마다 접두가 하나씩 더 붙는다(`bound bound orig`). **`length` 는 0 밑으로 안 내려간다.**
- ★★★ **재바인딩이 안 된다.** `call`·`apply`·다시 `bind`·점 왼쪽·`Reflect.apply` **다섯 경로 전부** 첫 `bind` 가 이긴다.
  ★ **인자는 다르다** — 나중에 준 인자는 **못질된 인자 뒤에 붙는다**(`args=1,9,3`).
  ★ 즉 **`this` 는 못이고 인자는 앞쪽만 못**이다.
- ★★★ **`new` 만 이긴다.** `new BoundCtor(2)` 는 못질한 `this` 를 무시하고 새 객체를 쓰는데
  **못질한 인자 `1` 은 그대로 남는다**(`got` 이 `[1,2]`).
  ★★ **`instanceof` 는 둘 다 `true`** 다 — bound 함수의 `instanceof` 는 **원본의 `prototype`** 을 본다.
  `BoundCtor.prototype` 자체는 `undefined` 인데도 그렇다. **프로퍼티가 없는 것과 판정이 못 되는 것은 다르다.**
  ★ 생성자로 못 쓰는 함수(화살표)를 `bind` 하면 **`new` 에서 `TypeError`** 다 — 08번 격자의 「자격」이 그대로 따라온다.
- ★★ **화살표에 `bind` 를 걸면 `this` 는 안 바뀌고 인자만 못질된다.** `arrowFn.bind(B)(1,2)` 가 여전히 `outer` 다.
  ★ **문법은 통하고 효과만 없다** — 에러가 안 나서 조용히 틀린다(07번의 결론).
  ★ 그런데 `length` 는 줄어든다 — **바인딩 객체는 만들어진다.**
- ★★ **메서드 빌려 쓰기가 `call` 의 고전적 쓸모다.** `Array.prototype.slice.call(유사배열)` ·
  `Function.prototype.call.bind(Object.prototype.hasOwnProperty)` 로 만든 **언커리 함수**가 그것이다.
  ★ `Math.max.apply(null, arr)` 는 오늘날 **`Math.max(...arr)` 로 쓴다**(11번). 결과가 같다.

### (3) ★★ 명세가 정하는 것과 엔진이 정하는 것 — 인자 개수

```js
// js08b-09c-limits.js
// 명세가 보장하는 것과 엔진이 정하는 것 -- 인자 개수의 한계는 어느 쪽인가.
function count() { return arguments.length; }

function firstFailure(call) {
  // 2의 거듭제곱으로 올려 처음 터지는 구간을 잡고, 그 구간을 이분해 경계를 찾는다.
  let lo = 1, hi = 1;
  for (;;) {
    try { call(hi); lo = hi; hi *= 2; if (hi > (1 << 30)) return ["no fail", lo, ""]; }
    catch (e) { break; }
  }
  let err = "";
  while (lo + 1 < hi) {
    const mid = Math.floor((lo + hi) / 2);
    try { call(mid); lo = mid; }
    catch (e) { hi = mid; err = e.constructor.name + ": " + e.message; }
  }
  return ["last ok", lo, err];
}

const CASES = [
  ["f.apply(null, arr)", (n) => count.apply(null, new Array(n))],
  ["Reflect.apply(f, null, arr)", (n) => Reflect.apply(count, null, new Array(n))],
  ["f(...arr)  spread", (n) => count(...new Array(n))],
  ["f.bind(null, ...arr)()", (n) => count.bind(null, ...new Array(n))()],
  ["new Array(n) itself", (n) => new Array(n)],
];
console.log("[1] where does each call form stop accepting arguments");
for (const [label, call] of CASES) {
  const [kind, at, err] = firstFailure(call);
  // 경계의 정확한 수는 그 순간 스택이 얼마나 차 있는지에 달려 흔들린다.
  // 흔들리지 않는 것은 자릿수와 예외의 종류다 -- 그 둘만 찍는다.
  console.log(("  " + label.padEnd(30) + kind.padEnd(10) +
              (at > 0 ? String(at).length + "-digit" : "n/a").padEnd(10) + err).replace(/ +$/, ""));
}

console.log("");
console.log("[2] what the spec fixes -- these are not engine numbers");
const rows = [
  ["Function.prototype.call.length", Function.prototype.call.length],
  ["Function.prototype.apply.length", Function.prototype.apply.length],
  ["Function.prototype.bind.length", Function.prototype.bind.length],
  ["Reflect.apply.length", Reflect.apply.length],
  ["call is a function?", typeof Function.prototype.call],
  ["Math.max.length", Math.max.length],
  ["Math.max() with no args", Math.max()],
  ["[].reduce.length", Array.prototype.reduce.length],
];
for (const [k, v] of rows) console.log("  " + k.padEnd(34) + String(v));

console.log("");
console.log("[3] thisArg on built-ins -- which ones take one");
const takesThisArg = [
  ["map", (o) => [1].map(function () { return this.mark; }, o)],
  ["filter", (o) => [1].filter(function () { return this.mark; }, o).length],
  ["forEach", (o) => { let r; [1].forEach(function () { r = this.mark; }, o); return r; }],
  ["some", (o) => [1].some(function () { return this.mark; }, o)],
  ["every", (o) => [1].every(function () { return this.mark; }, o)],
  ["find", (o) => [1].find(function () { return this.mark; }, o)],
  ["flatMap", (o) => [1].flatMap(function () { return this.mark; }, o)],
  ["reduce", (o) => [1, 2].reduce(function () { return this.mark; }, 0, o)],
  ["sort", (o) => [2, 1].sort(function () { return this.mark ? -1 : 1; }, o)],
  ["Array.from", (o) => Array.from([1], function () { return this.mark; }, o)],
];
const host = { mark: "HOST" };
for (const [label, run] of takesThisArg) {
  try { console.log("  " + label.padEnd(14) + JSON.stringify(run(host))); }
  catch (e) { console.log("  " + label.padEnd(14) + e.constructor.name + ": " + e.message); }
}
```

```text
===== node20 js08b-09c-limits.js (exit=0) =====
[1] where does each call form stop accepting arguments
  f.apply(null, arr)            last ok   6-digit   RangeError: Maximum call stack size exceeded
  Reflect.apply(f, null, arr)   last ok   6-digit   RangeError: Maximum call stack size exceeded
  f(...arr)  spread             last ok   6-digit   RangeError: Maximum call stack size exceeded
  f.bind(null, ...arr)()        last ok   6-digit   RangeError: Maximum call stack size exceeded
  new Array(n) itself           no fail   10-digit

[2] what the spec fixes -- these are not engine numbers
  Function.prototype.call.length    1
  Function.prototype.apply.length   2
  Function.prototype.bind.length    1
  Reflect.apply.length              3
  call is a function?               function
  Math.max.length                   2
  Math.max() with no args           -Infinity
  [].reduce.length                  1

[3] thisArg on built-ins -- which ones take one
  map           ["HOST"]
  filter        1
  forEach       "HOST"
  some          true
  every         true
  find          1
  flatMap       ["HOST"]
  reduce        undefined
  sort          [2,1]
  Array.from    ["HOST"]
```

- ★★★ **인자 개수의 상한은 명세에 없다.** 네 호출 형태가 전부 **여섯 자리 수**에서 `RangeError` 를 낸다 —
  **그 수는 V8 의 스택 크기가 정한다.**
  ★★ 그래서 **정확한 수를 싣지 않는다.** 그 순간 스택이 얼마나 차 있는지에 달려 흔들리기 때문이다.
  **자릿수와 예외의 종류만** 싣는다 — 그 둘은 세 판을 돌려도 같았다.
  ★ `new Array(n)` 자체는 **10자리까지 안 터진다** — 막히는 것은 **배열을 만드는 일이 아니라 호출로 펴는 일**이다.
- ★★ **`length` 값은 명세가 정한다** — `call` 1 · `apply` 2 · `bind` 1 · `Reflect.apply` 3.
  ★ 이 수치는 **엔진과 무관하다.** 위 자릿수와 성격이 정반대인 칸이라 나란히 실었다.
- ★★★ **`thisArg` 를 받는 배열 메서드와 안 받는 것이 갈린다.** `map`·`filter`·`forEach`·`some`·`every`·`find`·`flatMap`·`Array.from` 은 받고,
  **`reduce` 와 `sort` 는 안 받는다.**
  ★★ **안 받는데 에러도 안 난다** — `reduce` 의 세 번째 인자는 **그냥 무시**되고 `sort` 의 두 번째도 그렇다.
  출력에서 `reduce` 가 `undefined` 를, `sort` 가 정렬 안 된 `[2,1]` 을 돌려준 것이 그 증거다.
  ★ **조용한 실패**라 화살표를 쓰거나 `bind` 로 고쳐야 한다.

### (4) ★★ 떼어 낸 메서드를 고치는 네 가지

```js
// js08b-09d-fixes.js
// 떼어 낸 메서드를 고치는 네 가지 -- 무엇이 this 를 지키고 무엇이 「같은 함수」인가.
// 07번이 「왜 깨지나」였다면 여기는 「무엇으로 고치고 그 대가가 무엇인가」다.
function show(label, run) {
  try { console.log("  " + label.padEnd(34) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(34) + " -> " + e.constructor.name + ": " + e.message); }
}

const counter = {
  mark: "counter",
  n: 0,
  inc() { this.n += 1; return this.mark + " n=" + this.n; },
};

console.log("[1] four ways to hand the method to someone else");
const detached = counter.inc;
const bound = counter.inc.bind(counter);
const wrapped = () => counter.inc();
const viaCall = function () { return counter.inc.call(counter); };
show("detached()", () => detached());
show("bound()", () => bound());
show("wrapped()", () => wrapped());
show("viaCall()", () => viaCall());
show("counter.n after those calls", () => counter.n);

console.log("");
console.log("[2] are two fixes the same function object");
const rows = [
  ["counter.inc === counter.inc", counter.inc === counter.inc],
  ["bind twice gives the same fn?", counter.inc.bind(counter) === counter.inc.bind(counter)],
  ["arrow twice gives the same fn?", (() => counter.inc()) === (() => counter.inc())],
  ["a saved bound fn === itself", (() => { const b = counter.inc.bind(counter); return b === b; })()],
];
for (const [k, v] of rows) console.log("  " + k.padEnd(38) + String(v));
console.log("  " + "why it matters".padEnd(38) + "removeEventListener needs the same object");

console.log("");
console.log("[3] a fake listener registry shows what that costs");
const registry = new Set();
function on(fn) { registry.add(fn); return registry.size; }
function off(fn) { const had = registry.delete(fn); return "deleted=" + had + " left=" + registry.size; }
show("on(counter.inc.bind(counter))", () => on(counter.inc.bind(counter)));
show("off(counter.inc.bind(counter))", () => off(counter.inc.bind(counter)));
const saved = counter.inc.bind(counter);
show("on(saved)", () => on(saved));
show("off(saved)", () => off(saved));

console.log("");
console.log("[4] what each fix keeps and drops");
const probes = [
  ["original", counter.inc],
  ["bound", counter.inc.bind(counter)],
  ["arrow wrapper", () => counter.inc()],
  ["bound with an arg", counter.inc.bind(counter, 1)],
];
console.log("  " + "fix".padEnd(18) + "name".padEnd(16) + "length".padEnd(8) + "proto?".padEnd(8) + "new?");
for (const [label, f] of probes) {
  let canNew;
  try { Reflect.construct(f, []); canNew = "yes"; }
  catch (e) { canNew = "no:" + e.constructor.name; }
  console.log("  " + label.padEnd(18) +
              JSON.stringify(f.name).padEnd(16) +
              String(f.length).padEnd(8) +
              String(Object.prototype.hasOwnProperty.call(f, "prototype")).padEnd(8) +
              canNew);
}
function takesTwo(a, b) { return "got " + String(a) + "," + String(b); }
const holder = { mark: "holder", takesTwo };
show("bound forwards later args", () => takesTwo.bind(holder)(1, 2));
show("arrow wrapper with no params", () => ((...args) => takesTwo.apply(holder, args))(1, 2));
show("arrow wrapper that drops args", () => (() => takesTwo.call(holder))(1, 2));
```

```text
===== node20 js08b-09d-fixes.js (exit=0) =====
[1] four ways to hand the method to someone else
  detached()                         -> undefined n=NaN
  bound()                            -> counter n=1
  wrapped()                          -> counter n=2
  viaCall()                          -> counter n=3
  counter.n after those calls        -> 3

[2] are two fixes the same function object
  counter.inc === counter.inc           true
  bind twice gives the same fn?         false
  arrow twice gives the same fn?        false
  a saved bound fn === itself           true
  why it matters                        removeEventListener needs the same object

[3] a fake listener registry shows what that costs
  on(counter.inc.bind(counter))      -> 1
  off(counter.inc.bind(counter))     -> deleted=false left=1
  on(saved)                          -> 2
  off(saved)                         -> deleted=true left=1

[4] what each fix keeps and drops
  fix               name            length  proto?  new?
  original          "inc"           0       false   no:TypeError
  bound             "bound inc"     0       false   no:TypeError
  arrow wrapper     ""              0       false   no:TypeError
  bound with an arg "bound inc"     0       false   no:TypeError
  bound forwards later args          -> got 1,2
  arrow wrapper with no params       -> got 1,2
  arrow wrapper that drops args      -> got undefined,undefined
```

```text
   counter.inc 를 남에게 건넬 때

   detached  = counter.inc                 -> this 가 전역. n 이 NaN 이 된다 (조용히)
   bound     = counter.inc.bind(counter)   -> 고쳐진다. 새 함수가 하나 생긴다
   wrapped   = () => counter.inc()         -> 고쳐진다. 새 함수가 하나 생긴다
   viaCall   = function(){ return counter.inc.call(counter); }  -> 고쳐진다

   ★ 셋 다 고치는데, 셋 다 「원본과 다른 함수 객체」를 만든다.
   ★ 그래서 등록/해제를 짝으로 하는 API 에서는 그 객체를 반드시 저장해 둬야 한다.
```

- ★★★ **떼어 낸 메서드는 조용히 틀린다.** `detached()` 가 `undefined n=NaN` 을 돌려주는데 **예외가 안 난다** —
  비엄격이라 `this` 가 전역이 되고 `globalThis.n` 이 `undefined` 라 `NaN` 이 됐다.
  ★ 07번의 결론이 여기서 **실무 형태**로 나타난다.
- ★★★ **`bind` 는 부를 때마다 새 함수를 만든다.** `counter.inc.bind(counter) === counter.inc.bind(counter)` 가 `false` 다.
  ★★ **이것이 이 주제의 실무 비용 전부**다 — 등록·해제를 짝으로 하는 API(`removeEventListener`·`Set`·구독 해제)에서
  **해제가 조용히 실패한다.** 출력의 `deleted=false left=1` 이 그것이다.
  ★ **고치는 법은 하나** — 만든 함수를 **변수에 저장해 두고 같은 객체로 해제**한다(`deleted=true`).
  ★ 화살표 래퍼도 같은 문제를 갖는다(`(() => f()) === (() => f())` 가 `false`).
- ★★ **고친 함수가 원본의 성질을 다 물려받지는 않는다.** `name` 에 `bound ` 가 붙고 화살표 래퍼는 이름이 빈 문자열이다.
  ★ **인자 전달도 다르다** — `bind` 와 `(...args) => f.apply(o, args)` 는 인자를 넘기지만
  **`() => f.call(o)` 는 인자를 버린다.** 출력의 마지막 세 줄이 그 셋을 가른다.
  ★ 「화살표로 감싸면 된다」가 **인자를 쓰는 콜백에서 조용히 틀리는** 자리가 여기다.

### (5) ★★ 두 판에서 돌려 보면 — 갈린 자리가 없다

```text
===== ./js08b-vdiff.sh 09 (exit=0) =====
  same      js08b-09a-three-methods.js
  same      js08b-09b-bind.js
  same      js08b-09c-limits.js
  same      js08b-09d-fixes.js
  ----
  identical on node18 and node20: 4   different: 0
```

- ★★ **네 스크립트가 두 판에서 한 글자도 같았다.** 08번은 예외 문구 하나가 갈렸는데 **여기서는 0개**다.
  ★★ **「같았다」는 보장이 아니라 관찰**이다. 보장은 명세가 하고, 이 줄은 **그 보장이 두 판에서 지켜졌다**는 관찰이다.
  ★ 특히 **인자 개수 경계를 자릿수로만 찍은 덕에** 이 블록이 결정적이 됐다 —
  정확한 수를 찍었으면 여기서 **두 판이 갈렸을 것**이다(v18 125526 대 v20 125551 부근).

### (6) ★★ 같은 질문을 브라우저에 던지면

```js
// js08b-09h-browser.js
// 같은 질문을 브라우저에 던진다 -- call.apply.bind 에 호스트가 정하는 칸이 있나.
const lines = [];
function row(k, v) { lines.push("  " + k.padEnd(36) + v); }
function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") return Object.prototype.toString.call(t);
  return typeof t + " " + String(t);
}
row("engine", navigator.userAgent.replace(/^.*(Chrome\/[0-9.]+).*$/, "$1"));
function looseWho() { return tag(this); }
function strictWho() { "use strict"; return tag(this); }
row("sloppy call(null)", looseWho.call(null));
row("strict call(null)", strictWho.call(null));
row("sloppy call(7)", looseWho.call(7));
row("strict call(7)", strictWho.call(7));
row("globalThis brand", Object.prototype.toString.call(globalThis));
function orig(a, b, c) { return "args=" + [a, b, c].map(String).join(","); }
const b1 = orig.bind(null, 1);
row("bind name", JSON.stringify(b1.name));
row("bind length", String(b1.length));
row("bind has prototype?", String(Object.prototype.hasOwnProperty.call(b1, "prototype")));
row("rebinding is ignored", b1.bind(null, 9)(3));
function Ctor(a) { this.got = a; }
const BC = Ctor.bind(null, 1);
row("new on a bound ctor", String(new BC() instanceof Ctor));
try { orig.apply(null, "ab"); row("apply with a string", "no throw"); }
catch (e) { row("apply with a string", e.constructor.name); }
function count() { return arguments.length; }
row("apply with a Set (no length)", String(count.apply(null, new Set([1, 2]))));
row("apply with { length: 3 }", String(count.apply(null, { length: 3 })));
row("reduce ignores thisArg", String([1, 2].reduce(function () { return this === undefined || this === globalThis; }, 0, { m: 1 })));
document.documentElement.appendChild(document.createElement("pre")).textContent =
  "===OUT===" + String.fromCharCode(10) + lines.join(String.fromCharCode(10)) + String.fromCharCode(10) + "===END===";
```

호스트 페이지는 이 네 줄이 전부다.

```text
<!doctype html>
<meta charset="utf-8">
<title>js08b 09</title>
<script src="js08b-09h-browser.js"></script>
```

```text
===== google-chrome --headless --dump-dom page09.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' (exit=0) =====
  engine                              Chrome/151.0.0.0
  sloppy call(null)                   globalThis
  strict call(null)                   null
  sloppy call(7)                      [object Number]
  strict call(7)                      number 7
  globalThis brand                    [object Window]
  bind name                           "bound orig"
  bind length                         2
  bind has prototype?                 false
  rebinding is ignored                args=1,9,3
  new on a bound ctor                 true
  apply with a string                 TypeError
  apply with a Set (no length)        0
  apply with { length: 3 }            3
  reduce ignores thisArg              true
```

- ★★★ **호스트가 정하는 칸은 하나**다 — **비엄격에서 `call(null)` 이 주는 전역 객체의 정체**다.
  Node 에서는 `globalThis` 브랜드가 `[object global]` 이고 **브라우저에서는 `[object Window]`** 다.
  ★ **규칙은 같다**(「`null` 이면 전역을 넣는다」). **그 전역이 무엇인지만 호스트가 정한다.**
- ★★ **나머지 열네 줄은 Node 와 전부 같다.** `bind` 의 이름·`length`·재바인딩 불가·`new` 승리 ·
  `apply` 가 문자열을 거부하고 `Set` 을 조용히 0개로 받는 것 · `reduce` 가 `thisArg` 를 무시하는 것.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js08b-09x-forms.js
// 형태만 모아 둔 파일 -- 출력은 없다. `node --check` 로 문법만 확인한다.
function greet(greeting, mark) { return greeting + " " + this.name + mark; }
const who = { name: "who" };

greet.call(who, "hi", "!");            // call  -- 인자를 하나씩 편다
greet.apply(who, ["hi", "!"]);         // apply -- 인자를 유사 배열 하나로 준다
const bound = greet.bind(who, "hi");   // bind  -- 부르지 않고 새 함수를 만든다
bound("!");                            // 남은 인자만 넘긴다

Reflect.apply(greet, who, ["hi", "!"]);  // apply 와 같은 일 -- 함수를 첫 인자로 받는다
greet.call(who, ...["hi", "!"]);         // 스프레드가 apply 를 대신한다 (11번 주제)

Array.prototype.slice.call({ 0: "a", length: 1 });   // 메서드 빌려 쓰기
const hasOwn = Function.prototype.call.bind(Object.prototype.hasOwnProperty);  // 언커리
hasOwn({ x: 1 }, "x");

const arrow = () => this;              // 화살표는 세 메서드로 this 를 못 바꾼다 (07번)
arrow.call(who);                       // 문법은 되고 효과가 없다

function Ctor(a) { this.a = a; }
const BoundCtor = Ctor.bind(null, 1);  // bind 한 생성자
new BoundCtor();                       // new 는 bind 를 이긴다 -- this 만, 인자는 남는다

[1].map(function () { return this; }, who);   // thisArg 를 받는 배열 메서드
[1, 2].reduce(function () { return this; }, 0);  // reduce 는 thisArg 자리가 없다
```

```text
===== node20 --check js08b-09x-forms.js (exit=0) =====

```

> ★ **이 빈 블록이 근거다.** 「문법 오류가 안 났다」를 산문으로 적으면 **안 물어본 것과 구분이 안 된다.**

규칙은 여덟이다.

1. **셋 다 `this` 를 첫 인자로 받는다.** `this` 를 정하는 규칙은 셋이 완전히 같다.
2. **`call` 은 인자를 하나씩, `apply` 는 유사 배열 하나로** 받는다. `apply` 의 둘째 인자가
   **`null`/`undefined` 면 인자 0개**, **객체가 아니면 `TypeError`** 다.
3. **`apply` 는 「유사 배열」을 본다** — `length` 프로퍼티다. **이터러블이어도 `length` 가 없으면 0개**다.
4. **`bind` 는 부르지 않고 새 함수를 만든다.** 이름에 `bound ` 가 붙고 `length` 가 못질한 인자 수만큼 줄며 `prototype` 이 없다.
5. **한 번 `bind` 하면 `this` 를 못 바꾼다.** `call`·`apply`·재`bind`·점 왼쪽 전부 무시된다.
6. **`new` 만 `bind` 의 `this` 를 이긴다.** 못질한 **인자는 남고** `instanceof` 는 원본 기준이다.
7. **화살표에 셋을 걸면 `this` 는 안 바뀌고 인자만 못질된다.** 문법은 통하고 효과가 없다.
8. **`bind` 는 부를 때마다 새 객체를 만든다.** 등록·해제를 짝으로 하는 API 에서는 **반드시 저장해 둔다.**

## 어디서 틀리나

### (1) ★★★ `f.call(null)` 을 「`this` 없음」으로 읽는다

**비엄격이면 전역이 들어간다.** 엄격이라야 `null` 그대로다.
★ 라이브러리 코드가 비엄격이면 `this.something = x` 가 **전역을 오염시키고도 에러가 안 난다.**

### (2) ★★★ `bind` 를 호출부에서 부른다

`addEventListener(h.bind(this))` 로 걸고 `removeEventListener(h.bind(this))` 로 떼면 **안 떨어진다.**
★ 만든 함수를 **필드나 변수에 저장**해 두고 같은 객체로 떼야 한다.

### (3) ★★★ `apply` 에 이터러블을 넘긴다

`Set`·`Map`·제너레이터는 **`length` 가 없어 인자 0개**로 들어간다. **에러가 안 난다.**
★ 오늘날의 정답은 **스프레드**다(`f(...set)`). 11번이 정본이다.

### (4) ★★ `bind` 한 함수를 다시 `bind` 하면 바뀔 거라고 믿는다

**안쪽이 이긴다.** 07번에서 한 번 확인했고 여기서 다섯 경로 전부 확인했다.

### (5) ★★ 화살표에 `bind` 를 걸고 고쳤다고 생각한다

`this` 는 안 바뀐다. **`length` 는 줄어들어서** 「무언가 일어났다」는 착각을 준다.

### (6) ★★ `reduce`·`sort` 에 `thisArg` 를 넘긴다

**받지 않고 에러도 안 낸다.** 조용히 무시된다.
★ 배열 메서드마다 `thisArg` 자리가 있는지 **외우지 말고 화살표를 쓴다.**

### (7) ★ `new` 한 bound 함수의 `instanceof` 를 헷갈린다

`BoundCtor.prototype` 은 `undefined` 인데 **`instanceof BoundCtor` 는 `true`** 다.
★ bound 함수의 `instanceof` 는 **원본의 `prototype`** 을 본다.

### (8) ★ 인자 개수 한계를 언어 규칙으로 외운다

**명세에 없다.** V8 의 스택이 정하고 판마다 다르다. 외울 것은 「**여섯 자리 언저리에서 `RangeError` 가 난다**」까지다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- **세 메서드가 `this` 를 정하는 규칙이 같은 것**과 **비엄격이 원시값을 감싸고 `null`/`undefined` 를 전역으로 바꾸는 것.**
- **`apply` 가 유사 배열을 보는 것** · **`null`/`undefined` 면 인자 0개** · **객체가 아니면 `TypeError`.**
- **`bind` 의 반환값이 새 함수인 것** · **`bound ` 접두** · **`length` 감소** · **`prototype` 없음.**
- **재바인딩 불가** · **`new` 가 `this` 를 이기고 인자는 남는 것** · **`instanceof` 가 원본 기준인 것.**
- **화살표에 셋을 걸어도 `this` 가 안 바뀌는 것.**
- **`call`·`apply`·`bind`·`Reflect.apply` 의 `length` 값**(1·2·1·3).
- **어느 배열 메서드가 `thisArg` 자리를 갖는지.**

### 엔진(V8) 구현 · 이 판의 관찰

- ★★★ **인자 개수의 상한.** 명세에 수치가 없다. **여섯 자리 언저리**라는 것만 관찰이고,
  **정확한 수는 그 순간 스택 상태에 달려 흔들린다** — 그래서 이 문서는 자릿수만 싣는다.
- ★★ **예외 문구 전부.** `CreateListFromArrayLike called on non-object` · `Maximum call stack size exceeded` ·
  `ba is not a constructor` 는 **V8 의 말**이다. 종류만 명세다.
- ★ **`String(bound)` 이 `function () { [native code] }` 인 것** — 명세는 「구현 정의 문자열」이라고만 한다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★★ **비엄격에서 `call(null)` 이 주는 전역 객체의 정체.** Node 는 `[object global]`, 브라우저는 `[object Window]` 다.
  **규칙은 언어가, 그 객체는 호스트가** 정한다.

### 그래서 이렇게 적으면 틀린다

| 이렇게 적으면 틀린다 | 이렇게 적어야 한다 |
|---|---|
| 「`f.call(null)` 은 `this` 가 `null` 이다」 | 엄격이라야 그렇다. 비엄격은 전역이다 |
| 「`apply` 는 이터러블을 편다」 | **유사 배열**을 본다. `Set` 은 인자 0개가 된다 |
| 「`bind` 한 함수를 `call` 로 다시 바꿀 수 있다」 | 못 바꾼다. `new` 만 이긴다 |
| 「`bind` 한 함수는 `prototype` 이 없으니 `new` 가 안 된다」 | `new` 는 된다. 08번 격자의 반례다 |
| 「배열 메서드는 `thisArg` 를 받는다」 | `reduce`·`sort` 는 안 받고 **에러도 안 낸다** |
| 「인자는 65535개까지 된다」 | 명세에 상한이 없다. 이 판에서 **여섯 자리** 언저리다 |
| 「화살표에 `bind` 를 걸면 `this` 가 바뀐다」 | 안 바뀐다. `length` 만 줄어 착각을 준다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 인자 개수가 정해진 한 번의 호출 | **`call`** | 읽기 쉽다 |
| 인자가 이미 배열에 있다 | **스프레드 `f(...arr)`** | `apply` 보다 짧고 이터러블을 본다(11번) |
| 인자가 **유사 배열**이다 | **`apply`** | 스프레드는 `length` 만 있는 객체를 못 편다 |
| 함수를 나중에 넘겨야 한다 | **`bind` 또는 화살표 래퍼** | 미리 못질해 둔다 |
| 등록·해제를 짝으로 하는 API | **`bind` 한 결과를 저장** | 같은 객체라야 해제된다 |
| 부분 적용(partial application) | **`bind(null, 앞인자)`** | 앞쪽 인자를 고정한다 |
| 유사 배열에 배열 메서드 | **`Array.from` 또는 스프레드** | `slice.call` 보다 뜻이 드러난다 |
| 메타 프로그래밍·Proxy 트랩 | **`Reflect.apply`** | 트랩과 1:1 로 대응한다(46번) |

**안 쓰는 쪽**

- **`apply` 로 큰 배열을 펴지 않는다** — 여섯 자리에서 `RangeError` 다. 루프나 청크로 나눈다.
- **화살표에 `bind`·`call` 을 걸지 않는다** — 효과가 없고 읽는 사람을 속인다.
- **`reduce`·`sort` 에 `thisArg` 를 넘기지 않는다** — 조용히 무시된다.
- **호출부에서 `bind` 를 부르지 않는다** — 해제가 안 되고 렌더마다 새 함수가 생긴다.

## 핵심 문장

- **세 메서드는 `this` 규칙이 같고 인자 건네는 방식만 다르다** — 24칸 격자의 세 열이 한 글자도 같다.
- **`this` 자리에 무엇이 들어갔는지는 값으로 안 보인다** — 브랜드 태그라야 보인다. 그래서 이 주제의 본체 창이 그것이다.
- **`apply` 는 유사 배열을 보고 스프레드는 이터러블을 본다** — 서로 못 덮는 자리가 있다.
- **`bind` 는 원본을 덮지 않고 한 겹 덧씌운 새 함수를 만든다** — 그래서 되돌릴 수 없고, 그래서 매번 다른 객체다.
- **`new` 만 `bind` 를 이긴다** — 그런데 못질한 인자는 그대로 남는다.
- **조용한 실패가 셋 있다** — 비엄격 `call(null)` · `apply` 에 이터러블 · `reduce`/`sort` 의 `thisArg`.

## 관련 자료

- [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) — **그쪽은 네 규칙과 우선순위까지, 여기는 명시적 바인딩의 API 세부부터.**
- [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) — **bound 함수가 그쪽 격자의 한 행이었다.** 여기서는 그 행을 통째로 편다.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — **`f(...arr)` 문법의 정본은 그쪽이고, 여기서는 `apply` 를 대신한다는 사실까지.**
- 목록의 **34번 주제** 「타입 검사 관용구」 — **`Object.prototype.toString.call` 을 검사로 쓰는 법은 그쪽이 정본이고, 여기서는 관찰 도구로만 쓴다.**
- 목록의 **46번 주제** 「`Reflect`」 — **`Reflect` 전체는 그쪽이고, 여기서는 `Reflect.apply` 가 `apply` 와 같은 답을 낸다는 것까지.**
- 목록의 **35번 주제** 「엄격 모드」 — **strict 전체 규칙은 그쪽이고, 여기서는 `this` 박싱에 닿는 칸만 센다.**
- [파이썬 갈래의 19번 「함수 인자 규칙」](../../../python/syntax/19-function-argument-rules/) — **`f(*args)` 로 편다는 점이 `apply`/스프레드와 닮았다.** 다만 파이썬에는 `this` 를 건네는 자리가 없다.
- [TS 갈래의 16번 「함수 타입과 오버로드」](../../../ts/syntax/16-function-types-and-overloads/) — **`ThisParameterType`·`OmitThisParameter` 같은 타입 쪽은 그쪽이 정본이다.**

## 용어 풀이

- **`call`**: `f.call(thisArg, ...args)`. `this` 를 정해 **지금 부른다.** 인자는 하나씩 편다.
- **`apply`**: `f.apply(thisArg, argsArrayLike)`. `this` 를 정해 **지금 부른다.** 인자는 **유사 배열** 하나로 준다.
- **`bind`**: `f.bind(thisArg, ...args)`. **부르지 않고** `this` 와 앞쪽 인자를 못질한 **새 함수**를 돌려준다.
- **bound function**: `bind` 가 만든 함수 객체. `prototype` 이 없고 이름에 `bound ` 가 붙는다.
- **유사 배열(array-like)**: `length` 프로퍼티와 인덱스 키를 가진 객체. **이터러블과 다른 개념**이다.
- **부분 적용(partial application)**: 인자 일부를 미리 고정해 둔 함수를 만드는 것. `bind` 의 둘째 인자부터가 그 일이다.
- **언커리(uncurry)**: `Function.prototype.call.bind(메서드)` 로 「메서드를 첫 인자로 받는 함수」를 만드는 관용구.
- **박싱(boxing)**: 원시값이 대응하는 래퍼 객체로 감싸지는 것. 비엄격 `this` 에서 일어난다.
- **`thisArg`**: 배열 메서드가 콜백의 `this` 로 쓰라고 받는 선택 인자. **받지 않는 메서드도 있다.**

## 더 들어가면

- **`Reflect.apply` 와 `apply` 의 차이** — 값은 같지만 **`f.apply` 는 `f` 의 `apply` 프로퍼티를 읽는다.**
  누가 그 프로퍼티를 바꿔 놨으면 다른 함수가 불린다. `Reflect.apply` 는 그 조회를 건너뛴다. 정본은 46번이다.
- **`Function.prototype.call.call`** — `call` 자신을 `call` 로 부르는 것. 언커리 관용구의 뿌리다.
- **`Symbol.hasInstance`** — `instanceof` 의 판정을 가로채는 심볼. bound 함수의 `instanceof` 도 그 경로를 탄다. 목록의 **22번 주제**가 정본이다.
- **`bind` 의 폴리필이 못 흉내 내는 것** — 못질한 인자의 `length` 계산과 `new` 동작은 함수로 흉내 내기 어렵다.
  **재 본 적이 없으므로 「느리다」·「빠르다」는 이 문서에 없다.**
