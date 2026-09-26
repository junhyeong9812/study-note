# js/syntax/08 — 함수 정의 형태와 매개변수: 「이 형태는 무엇을 가지고 무엇을 안 가지나」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.** 함수 형태 16가지 × 칸 7개를 **손으로 한 칸도 안 채우고** 받아 놓고,
> 그 격자를 문장으로 읽어 주는 것이 이 문서의 골격이다. 나머지 창은 그 격자를 보조한다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 함수 정의 · 매개변수 목록과 인스턴스화 · `arguments` 객체 · 엄격 모드
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — 화살표·기본값·나머지 매개변수가 들어온 판을 가릴 때
> - [MDN — Functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions) · [MDN — `arguments`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/arguments)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> **어느 판에서 나왔는지는 아래 첫 블록**에 있다.

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
> 그래서 이 주제의 블록에는 **표준 오류가 한 줄도 섞이지 않는다** — 전부 표준 출력이다.
> ★★ **`SyntaxError` 는 `try`/`catch` 로 못 잡는다**(파싱 단계에서 나기 때문이다).
> 그래서 엄격/비엄격 격자는 `new Function(소스)` 으로 **두 번 컴파일**해 값과 문구를 받는다 — 파일로 던지면 진단에 경로가 박힌다.
> ★★ **`padEnd` 격자의 라벨은 전부 ASCII 다.** 한글은 터미널에서 두 칸이라 칸이 어긋난다.
> ★ **이 주제에는 시각·로캘·난수가 닿는 칸이 하나도 없다.**
>
> **버전** — 함수 선언과 함수 표현식·`arguments` 는 **초판부터**다. **엄격 모드는 ES5**,
> **화살표 함수·기본 매개변수·나머지 매개변수는 ES2015**, **매개변수 목록의 꼬리 쉼표는 ES2017** 이다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 형태 16 × 칸 7 · 매개변수 목록 20형태 × 두 모드 — **한 칸도 손으로 안 채운다** |
> | ★★★ **두 번 컴파일**(그대로 / `"use strict";` 붙여) | **설정이 답을 바꾸는 칸이 몇 개인가** — 세어서 고정 행으로 둔다 |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 「조용한 실패」가 어디서 「시끄러운 실패」로 바뀌나 |
> | ★ **③ 브랜드 태그** `Object.prototype.toString.call` | `arguments` 가 배열이 아니라는 것 · 형태마다 다른 브랜드 |
> | ★ **⑤ 두 판 대조기 + 브라우저** | 판이 갈린 칸 · 호스트가 정하는 칸이 있나 |
> | ★ **부적용 — ⑥ `toFixed(20)`** | 이 주제에는 **부동소수점이 닿는 칸이 한 칸도 없다.** 잴 것이 없다 |
> | ★ **부적용 — ⑦ `\uXXXX` 펼치기** | 식별자·문자열 인코딩이 답을 바꾸는 자리가 없다 |
> | ★ **부적용 — 「여러 번 돌려 흔들림을 본다」** | 난수·시각·순서 비보장이 한 칸도 없다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **격자의 칸 값**(`length`·`name`·`prototype` 소유 여부) |
> | 예외 **문구**(판이 오르면 바뀐다 — 실제로 하나 바뀌었다) | ★★★ **엄격·비엄격이 갈린 칸의 개수** |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **예외의 종류** · `SyntaxError` 냐 `TypeError` 냐 |
> | — | ★★ **기본값 평가 횟수** · `arguments` 연동 여부 |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 51블록 전부 동일).
>
> **선행** — [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) · [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md) · [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md).
> ★★★ **07번이 「어떤 호출식이 어떤 `this` 를 주나」였다면 여기는 「어떤 형태가 애초에 `this` 칸을 가지나」다.**
> 화살표가 `this` 를 안 만든다는 결론은 07번의 것이고, 여기서는 **그것이 `arguments`·`prototype`·`new` 와 한 묶음**이라는 것을 격자로 본다.
> ★ TDZ 는 [05번](../05-var-let-const-and-tdz/2-summary.md)의 것이다 — 여기서는 **매개변수 기본값이 그 규칙을 그대로 받는다**는 것만 확인한다.
> **이어지는 곳** — [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) · [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) · [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」
>
> ★★ **경계 — 엄격 모드 자체는 35번이 정본이다.** 여기서는 **함수와 매개변수에 닿는 칸만** 세고, 그 밖의 strict 규칙은 다루지 않는다.
> ★★ **경계 — `this` 의 네 규칙은 07번이 정본이다.** 여기서는 「형태가 `this` 칸을 갖느냐」까지다.
> ★★ **경계 — 타입 이야기는 여기 없다.** 매개변수 타입·오버로드는
> [TS 갈래의 16번 「함수 타입과 오버로드」](../../../ts/syntax/16-function-types-and-overloads/)가 정본이고, 여기는 **런타임 동작만** 다룬다.

## 한눈에 — 쉽게 말하면

**함수를 만드는 형태는 여럿인데, 형태마다 「딸려 오는 칸」이 다르다.**

- 함수는 값이다. 그런데 **어떤 모양으로 만들었느냐에 따라 딸려 오는 것이 다르다** — 자기 `this` 칸, 자기 `arguments` 칸, `prototype` 칸, `new` 로 불릴 자격.
- 화살표 함수는 **그 칸들을 아예 안 만든다.** 그래서 짧은 것이 아니라 **없는 것이 많은 것**이다.
- 매개변수는 「받을 자리」인데, **기본값을 붙이는 순간 그 자리가 식(expression)이 된다** — 그래서 **호출마다 다시 평가된다.**
- `arguments` 는 매개변수와 **한 몸일 때가 있고 아닐 때가 있다.** 그 갈림이 이 주제에서 가장 조용한 함정이다.

```text
   같은 일을 하는 네 형태                      딸려 오는 칸

   function f(a, b) { ... }        this O   arguments O   prototype O   new O
   const f = function (a, b) {...} this O   arguments O   prototype O   new O
   const f = (a, b) => { ... }     this X   arguments X   prototype X   new X
   obj = { f(a, b) { ... } }       this O   arguments O   prototype X   new X

   ★ 화살표는 「짧은 함수」가 아니라 「칸이 없는 함수」다.
```

**매개변수 목록은 두 종류로 갈린다 — 그리고 그 갈림이 `arguments` 를 끊는다.**

```text
   단순 목록(simple parameter list)      f(a, b, c)
     -> 비엄격이면 arguments 와 매개변수가 한 몸이다(하나를 고치면 다른 쪽도 바뀐다)

   단순하지 않은 목록                     f(a, b = 1)   f(a, ...r)   f({ a })
     -> 기본값·나머지·구조 분해가 하나라도 있으면 그 연동이 끊긴다
     -> 비엄격이어도 끊긴다. 엄격 모드와 무관하게 끊긴다
     -> 함수 안에 "use strict"; 를 쓸 수도 없어진다(SyntaxError)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 딸려 오는 칸 | 함수 객체가 갖는 내부 슬롯과 프로퍼티 | 전수 격자의 한 행을 읽는다 |
| 칸이 없는 함수 | 화살표 함수 | `prototype` 이 없고 `new` 가 `TypeError` 다 |
| 창구에 붙은 이름표 | 기명 함수 표현식의 이름 | 안에서는 보이고 밖에서는 안 보인다 |
| 한 몸인 두 장부 | 비엄격 + 단순 목록의 매개변수와 `arguments` | 한쪽을 고치고 다른 쪽을 읽는다 |
| 끊어진 두 장부 | 엄격이거나 단순하지 않은 목록 | 같은 탐침이 다른 값을 낸다 |
| 부를 때마다 새로 쓰는 쪽지 | 기본 매개변수 식 | 호출 횟수만큼 평가된다 |
| 미리 적어 둔 쪽지 한 장 | **파이썬의 기본 인자** | 정의 시점에 한 번 만들어 계속 쓴다 |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
`function f(opts = {})` 를 쓰면서 「매번 같은 객체가 오겠지」 하고 캐시로 쓰려다 매번 새 객체를 받는 일,
`function f(a) { arguments[0] = x; }` 로 인자를 「고쳤는데」 기본값 하나를 추가한 순간 그 고침이 사라지는 일이 그것이다.

## 이 주제가 답하려는 질문

1. ★★★ **이 형태는 무엇을 가지고 무엇을 안 가지나** — `this`·`arguments`·`prototype`·`new`·`length`·`name` 여섯 칸을 형태마다 채울 수 있나?
2. ★★★ **`arguments` 는 언제 매개변수와 한 몸이고 언제 끊기나** — 그 갈림을 만드는 것이 엄격 모드 하나인가?
3. ★★★ **기본 매개변수는 언제 평가되나** — 정의할 때 한 번인가 부를 때마다인가? 그리고 그것이 무엇을 바꾸나?

## 동작 방식

### (1) ★★★ 전수 격자 — 열여섯 형태를 한 화면에

**먼저 격자를 받아 놓고 그 격자를 문장으로 읽는다.** 이 주제의 본체가 이것이다.

```js
// js08b-08a-forms.js
// 함수를 만드는 형태마다 무엇이 달라지나 -- 손으로 한 칸도 안 채우고 전수 격자로 받는다.
// 보는 칸: typeof / name / length / prototype 소유 / new 가능 / 그냥 호출 가능 / 브랜드 태그
function decl(a, b) { return [a, b]; }
const anon = function (a, b) { return [a, b]; };
const named = function inner(a, b) { return [a, b]; };
const arrowConcise = (a, b) => [a, b];
const arrowBlock = (a, b) => { return [a, b]; };
const obj = {
  method(a, b) { return [a, b]; },
  *gen(a, b) { yield [a, b]; },
  async am(a, b) { return [a, b]; },
};
function* genDecl(a, b) { yield [a, b]; }
async function asyncDecl(a, b) { return [a, b]; }
const asyncArrow = async (a, b) => [a, b];
class K { constructor(a, b) { this.v = [a, b]; } }
const fromCtor = new Function("a", "b", "return [a, b];");
const bound = decl.bind(null, 1);
const withDefault = function (a, b = 2, c) { return [a, b, c]; };
const withRest = function (a, ...rest) { return [a, rest]; };

const probes = [
  ["function decl", decl],
  ["anon fn expr", anon],
  ["named fn expr", named],
  ["arrow concise", arrowConcise],
  ["arrow block", arrowBlock],
  ["method shorthand", obj.method],
  ["generator method", obj.gen],
  ["async method", obj.am],
  ["generator decl", genDecl],
  ["async decl", asyncDecl],
  ["async arrow", asyncArrow],
  ["class", K],
  ["new Function", fromCtor],
  ["bound fn", bound],
  ["default param", withDefault],
  ["rest param", withRest],
];

function canNew(f) {
  try { Reflect.construct(f, []); return "yes"; }
  catch (e) { return "no:" + e.constructor.name; }
}
function canCall(f) {
  try { const r = f(1, 2); if (r && typeof r.then === "function") r.then(() => {}, () => {}); return "yes"; }
  catch (e) { return "no:" + e.constructor.name; }
}

console.log("[1] form matrix -- 16 forms x 7 columns");
console.log("  " + "form".padEnd(18) + "typeof".padEnd(10) + "name".padEnd(16) +
            "len".padEnd(5) + "proto?".padEnd(8) + "new?".padEnd(14) + "call?".padEnd(14) + "brand");
for (const [label, f] of probes) {
  console.log("  " + label.padEnd(18) +
              (typeof f).padEnd(10) +
              JSON.stringify(f.name).padEnd(16) +
              String(f.length).padEnd(5) +
              String(Object.prototype.hasOwnProperty.call(f, "prototype")).padEnd(8) +
              canNew(f).padEnd(14) +
              canCall(f).padEnd(14) +
              Object.prototype.toString.call(f));
}

console.log("");
console.log("[2] name -- where does an unnamed function get its name");
const assigned = function () {};
const arrowAssigned = () => {};
let letAssigned; letAssigned = function () {};
const o2 = { key: function () {}, arrowKey: () => {} };
const arr2 = [function () {}];
const defaulted = (function (p = function () {}) { return p; })();
const rows = [
  ["const assigned", assigned],
  ["const arrow", arrowAssigned],
  ["let then assign", letAssigned],
  ["object literal key", o2.key],
  ["object literal arrow", o2.arrowKey],
  ["array element", arr2[0]],
  ["default value", defaulted],
  ["bound", decl.bind(null)],
  ["getter", Object.getOwnPropertyDescriptor({ get g() { return 1; } }, "g").get],
];
for (const [label, f] of rows) console.log("  " + label.padEnd(22) + JSON.stringify(f.name));

console.log("");
console.log("[3] arrow has no own arguments -- it reads the enclosing function's, by identity");
function outer(a, b) {
  const arrow = () => arguments;
  return [arguments, arrow()];
}
const [outerArgs, arrowArgs] = outer(10, 20);
console.log("  " + "same object?".padEnd(22) + String(outerArgs === arrowArgs));
console.log("  " + "outer arguments".padEnd(22) + JSON.stringify([...outerArgs]));
console.log("  " + "brand".padEnd(22) + Object.prototype.toString.call(outerArgs));
console.log("  " + "Array.isArray".padEnd(22) + String(Array.isArray(outerArgs)));
console.log("  " + "has callee?".padEnd(22) + String(Object.prototype.hasOwnProperty.call(outerArgs, "callee")));
console.log("  " + "Symbol.iterator?".padEnd(22) + String(typeof outerArgs[Symbol.iterator]));
```

```text
===== node20 js08b-08a-forms.js (exit=0) =====
[1] form matrix -- 16 forms x 7 columns
  form              typeof    name            len  proto?  new?          call?         brand
  function decl     function  "decl"          2    true    yes           yes           [object Function]
  anon fn expr      function  "anon"          2    true    yes           yes           [object Function]
  named fn expr     function  "inner"         2    true    yes           yes           [object Function]
  arrow concise     function  "arrowConcise"  2    false   no:TypeError  yes           [object Function]
  arrow block       function  "arrowBlock"    2    false   no:TypeError  yes           [object Function]
  method shorthand  function  "method"        2    false   no:TypeError  yes           [object Function]
  generator method  function  "gen"           2    true    no:TypeError  yes           [object GeneratorFunction]
  async method      function  "am"            2    false   no:TypeError  yes           [object AsyncFunction]
  generator decl    function  "genDecl"       2    true    no:TypeError  yes           [object GeneratorFunction]
  async decl        function  "asyncDecl"     2    false   no:TypeError  yes           [object AsyncFunction]
  async arrow       function  "asyncArrow"    2    false   no:TypeError  yes           [object AsyncFunction]
  class             function  "K"             2    true    yes           no:TypeError  [object Function]
  new Function      function  "anonymous"     2    true    yes           yes           [object Function]
  bound fn          function  "bound decl"    1    false   yes           yes           [object Function]
  default param     function  "withDefault"   1    true    yes           yes           [object Function]
  rest param        function  "withRest"      1    true    yes           yes           [object Function]

[2] name -- where does an unnamed function get its name
  const assigned        "assigned"
  const arrow           "arrowAssigned"
  let then assign       "letAssigned"
  object literal key    "key"
  object literal arrow  "arrowKey"
  array element         ""
  default value         "p"
  bound                 "bound decl"
  getter                "get g"

[3] arrow has no own arguments -- it reads the enclosing function's, by identity
  same object?          true
  outer arguments       [10,20]
  brand                 [object Arguments]
  Array.isArray         false
  has callee?           true
  Symbol.iterator?      function
```

**격자를 읽는 법** — 세로로 읽으면 칸의 성질이, 가로로 읽으면 형태의 성질이 나온다.

```text
   prototype 칸이 있는가          new 가 되는가
   ------------------------       ------------------------
   function decl        O         function decl        O
   function expr        O         function expr        O
   arrow                X         arrow                X
   method shorthand     X         method shorthand     X
   generator            O (!)     generator            X (!)
   async                X         async                X
   class                O         class                O
   bound fn             X         bound fn             O (!)

   ★ prototype 유무와 new 가능 여부는 같은 것이 아니다.
     제너레이터는 prototype 이 있는데 new 가 안 되고,
     bound 함수는 prototype 이 없는데 new 가 된다.
```

- ★★★ **「화살표는 `prototype` 이 없다」와 「화살표는 `new` 가 안 된다」는 같은 사실의 두 얼굴이 아니다.**
  격자에 **반례가 두 개** 있다 — 제너레이터(`prototype` 있음 · `new` 안 됨)와 bound 함수(`prototype` 없음 · `new` 됨).
  ★ 외울 것은 프로퍼티가 아니라 「**생성자로 쓰일 자격이 따로 있다**」이다.
- ★★ **메서드 단축 표기도 `prototype` 이 없다.** `{ m() {} }` 는 `{ m: function () {} }` 와 **같은 것이 아니다.**
  눈으로는 구분이 안 되고 **격자에서만 갈린다.**
- ★★ **`class` 는 `typeof` 가 `"function"` 이고 브랜드도 `[object Function]` 인데 그냥 부르면 `TypeError` 다.**
  「형태가 다르다」가 아니라 「**호출 규약이 다르다**」이다.
- ★ **브랜드 태그는 세 갈래로만 갈린다** — `[object Function]` · `[object GeneratorFunction]` · `[object AsyncFunction]`.
  화살표·메서드·클래스는 전부 `[object Function]` 이라 **브랜드로는 안 갈린다.** 이 주제에서 브랜드는 보조 창이다.
- ★ **`name` 은 「어디에 놓였는가」가 정한다.** 익명 함수라도 `const` 로 받으면 그 이름이 붙고,
  **배열 원소로 놓으면 빈 문자열**이다. 붙일 자리가 없기 때문이다.

### (2) ★★★ 호이스팅 — 세 형태가 줄 위에서 갈린다

```js
// js08b-08b-hoisting.js
// 선언·표현식·화살표의 호이스팅 차이 -- 같은 탐침을 두 모드로 두 번 컴파일해 격자로 받는다.
// new Function 을 쓰는 이유: 파일로 던지면 진단에 절대 경로가 박힌다. 여기서는 값과 문구만 받는다.
const HELPERS = `
  const snap = (label, run) => {
    try { return label.padEnd(34) + " -> " + String(run()); }
    catch (e) { return label.padEnd(34) + " -> " + e.constructor.name + ": " + e.message; }
  };
  const out = [];
`;
const PROBES = [
  ["decl called before its line", `
    out.push(snap("decl()", () => decl(1)));
    function decl(a) { return "decl ran " + a; }
  `],
  ["typeof decl before its line", `
    out.push(snap("typeof decl", () => typeof decl));
    function decl(a) { return a; }
  `],
  ["var fn expr before its line", `
    out.push(snap("typeof vexpr", () => typeof vexpr));
    out.push(snap("vexpr()", () => vexpr(1)));
    var vexpr = function (a) { return "vexpr ran " + a; };
  `],
  ["const fn expr before its line", `
    out.push(snap("typeof cexpr", () => typeof cexpr));
    out.push(snap("cexpr()", () => cexpr(1)));
    const cexpr = function (a) { return "cexpr ran " + a; };
  `],
  ["arrow before its line", `
    out.push(snap("typeof arr", () => typeof arr));
    out.push(snap("arr()", () => arr(1)));
    const arr = (a) => "arr ran " + a;
  `],
  ["decl inside a block, seen outside", `
    out.push(snap("typeof blockFn before", () => typeof blockFn));
    { function blockFn() { return "block"; } }
    out.push(snap("typeof blockFn after", () => typeof blockFn));
  `],
  ["decl inside if(false)", `
    if (false) { function deadFn() { return "dead"; } }
    out.push(snap("typeof deadFn", () => typeof deadFn));
  `],
  ["two decls with the same name", `
    function dup() { return "first"; }
    function dup() { return "second"; }
    out.push(snap("dup()", () => dup()));
  `],
  ["decl and var with the same name", `
    var both = 1;
    function both() { return "fn"; }
    out.push(snap("typeof both", () => typeof both));
  `],
];

function compile(body, strict) {
  const src = (strict ? '"use strict";\n' : "") + HELPERS + body + "\n  return out.join(String.fromCharCode(10));";
  try {
    const f = new Function(src);
    return f();
  } catch (e) {
    return "COMPILE " + e.constructor.name + ": " + e.message;
  }
}

console.log("[1] hoisting -- sloppy");
for (const [label, body] of PROBES) {
  console.log("  " + label);
  for (const line of String(compile(body, false)).split(String.fromCharCode(10))) console.log("    " + line);
}

console.log("");
console.log("[2] hoisting -- strict");
for (const [label, body] of PROBES) {
  console.log("  " + label);
  for (const line of String(compile(body, true)).split(String.fromCharCode(10))) console.log("    " + line);
}

console.log("");
console.log("[3] how many of the 9 probes differ between the two modes");
let differ = 0;
for (const [label, body] of PROBES) {
  const a = String(compile(body, false));
  const b = String(compile(body, true));
  const same = a === b;
  if (!same) differ += 1;
  console.log("  " + label.padEnd(34) + (same ? "same" : "DIFFERENT"));
}
console.log("  " + "total".padEnd(34) + differ + " of " + PROBES.length + " differ");
```

```text
===== node20 js08b-08b-hoisting.js (exit=0) =====
[1] hoisting -- sloppy
  decl called before its line
    decl()                             -> decl ran 1
  typeof decl before its line
    typeof decl                        -> function
  var fn expr before its line
    typeof vexpr                       -> undefined
    vexpr()                            -> TypeError: vexpr is not a function
  const fn expr before its line
    typeof cexpr                       -> ReferenceError: Cannot access 'cexpr' before initialization
    cexpr()                            -> ReferenceError: Cannot access 'cexpr' before initialization
  arrow before its line
    typeof arr                         -> ReferenceError: Cannot access 'arr' before initialization
    arr()                              -> ReferenceError: Cannot access 'arr' before initialization
  decl inside a block, seen outside
    typeof blockFn before              -> undefined
    typeof blockFn after               -> function
  decl inside if(false)
    typeof deadFn                      -> undefined
  two decls with the same name
    dup()                              -> second
  decl and var with the same name
    typeof both                        -> number

[2] hoisting -- strict
  decl called before its line
    decl()                             -> decl ran 1
  typeof decl before its line
    typeof decl                        -> function
  var fn expr before its line
    typeof vexpr                       -> undefined
    vexpr()                            -> TypeError: vexpr is not a function
  const fn expr before its line
    typeof cexpr                       -> ReferenceError: Cannot access 'cexpr' before initialization
    cexpr()                            -> ReferenceError: Cannot access 'cexpr' before initialization
  arrow before its line
    typeof arr                         -> ReferenceError: Cannot access 'arr' before initialization
    arr()                              -> ReferenceError: Cannot access 'arr' before initialization
  decl inside a block, seen outside
    typeof blockFn before              -> undefined
    typeof blockFn after               -> undefined
  decl inside if(false)
    typeof deadFn                      -> undefined
  two decls with the same name
    dup()                              -> second
  decl and var with the same name
    typeof both                        -> number

[3] how many of the 9 probes differ between the two modes
  decl called before its line       same
  typeof decl before its line       same
  var fn expr before its line       same
  const fn expr before its line     same
  arrow before its line             same
  decl inside a block, seen outside DIFFERENT
  decl inside if(false)             same
  two decls with the same name      same
  decl and var with the same name   same
  total                             1 of 9 differ
```

```text
   같은 줄 위에서 부르면

   function decl(){}          decl()   -> 돈다        (이름과 값이 둘 다 미리 올라간다)
   var  expr = function(){}   expr()   -> TypeError   (이름만 올라가고 값은 undefined)
   const expr = function(){}  expr()   -> ReferenceError (TDZ -- 05번)
   const arr  = () => {}      arr()    -> ReferenceError (TDZ -- 05번)

   ★ 셋 다 「호이스팅」이라는 한 낱말로 뭉치면 이 세 답이 안 갈린다.
```

- ★★★ **함수 선언만 「값까지」 올라간다.** 나머지 형태는 **이름의 규칙을 그대로 따른다** — `var` 면 `undefined`,
  `let`/`const` 면 TDZ 다. 그래서 화살표의 호이스팅을 따로 외울 것이 없다.
  ★ **화살표가 특별한 것이 아니라 `const` 가 특별한 것**이다.
- ★★★ **블록 안의 함수 선언이 유일하게 모드에 따라 갈렸다.** 비엄격에서는 블록 밖에서도 보이고(`function`),
  엄격에서는 안 보인다(`undefined`). **아홉 탐침 중 이 하나**다.
- ★ **`if (false)` 안의 함수 선언도 이름은 올라간다** — 비엄격에서 `typeof deadFn` 이 `undefined` 인 것은
  「이름이 없어서」가 아니라 「**이름은 있고 값이 안 채워져서**」다. 엄격에서는 블록 밖으로 아예 안 나온다.
- ★ **같은 이름의 선언이 둘이면 뒤엣것이 이긴다**(`second`). 그리고 **`var` 와 함수 선언이 같은 이름이면 대입이 이긴다** — `typeof both` 가 `number` 였다.

### (3) ★★ 기명 함수 표현식 — 이름이 안쪽에만 있다

```js
// js08b-08c-named-fexpr.js
// 기명 함수 표현식의 이름은 어디서 보이나 -- 안쪽에서만 보이고, 그 이름은 못 바꾼다.
function show(label, run) {
  try { console.log("  " + label.padEnd(38) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(38) + " -> " + e.constructor.name + ": " + e.message); }
}

console.log("[1] the name is visible inside, not outside");
const fact = function selfName(n) { return n <= 1 ? 1 : n * selfName(n - 1); };
show("fact(5)", () => fact(5));
show("fact.name", () => fact.name);
show("typeof selfName (outside)", () => typeof selfName);
show("selfName(5) (outside)", () => selfName(5));

console.log("");
console.log("[2] a function declaration puts its name outside too");
function declFact(n) { return n <= 1 ? 1 : n * declFact(n - 1); }
show("declFact(5)", () => declFact(5));
show("typeof declFact (outside)", () => typeof declFact);

console.log("");
console.log("[3] the inner name is an immutable binding -- sloppy is silent, strict throws");
const sloppyReassign = function me() {
  me = 1;
  return typeof me;
};
const strictReassign = function me2() {
  "use strict";
  try { me2 = 1; return "assigned, typeof " + typeof me2; }
  catch (e) { return e.constructor.name + ": " + e.message; }
};
show("sloppy: me = 1 then typeof me", () => sloppyReassign());
show("strict: me2 = 1", () => strictReassign());

console.log("");
console.log("[4] the inner binding lives in its own scope -- a parameter or a var shadows it");
const shadowByParam = function me3(me3) { return "param wins: " + typeof me3; };
show("named fn expr with param of same name", () => shadowByParam(42));
const shadowByVar = function me4() { var me4 = 7; return "var wins: " + typeof me4; };
show("named fn expr with var of same name", () => shadowByVar());
const notShadowed = function me5() { return "no shadow: " + typeof me5; };
show("named fn expr, nothing shadows", () => notShadowed());

console.log("");
console.log("[5] the name survives reassignment of the outer variable");
let holder = function me6(n) { return n <= 1 ? 1 : n * me6(n - 1); };
const saved = holder;
holder = function () { return "replaced"; };
show("saved(5) after holder replaced", () => saved(5));
show("holder(5)", () => holder(5));
const anonSelf = function (n) { return n <= 1 ? 1 : n * anonSelf(n - 1); };
const savedAnon = anonSelf;
show("anon self-recursion still works", () => savedAnon(5));
let anonSelf2 = function (n) { return n <= 1 ? 1 : n * anonSelf2(n - 1); };
const savedAnon2 = anonSelf2;
anonSelf2 = null;
show("anon self-recursion after var cleared", () => savedAnon2(5));
```

```text
===== node20 js08b-08c-named-fexpr.js (exit=0) =====
[1] the name is visible inside, not outside
  fact(5)                                -> 120
  fact.name                              -> selfName
  typeof selfName (outside)              -> undefined
  selfName(5) (outside)                  -> ReferenceError: selfName is not defined

[2] a function declaration puts its name outside too
  declFact(5)                            -> 120
  typeof declFact (outside)              -> function

[3] the inner name is an immutable binding -- sloppy is silent, strict throws
  sloppy: me = 1 then typeof me          -> function
  strict: me2 = 1                        -> TypeError: Assignment to constant variable.

[4] the inner binding lives in its own scope -- a parameter or a var shadows it
  named fn expr with param of same name  -> param wins: number
  named fn expr with var of same name    -> var wins: number
  named fn expr, nothing shadows         -> no shadow: function

[5] the name survives reassignment of the outer variable
  saved(5) after holder replaced         -> 120
  holder(5)                              -> replaced
  anon self-recursion still works        -> 120
  anon self-recursion after var cleared  -> TypeError: anonSelf2 is not a function
```

```text
   const fact = function selfName(n) { ... selfName(n - 1) ... };

        바깥에서 보이는 이름 : fact
        안쪽에서만 보이는 이름 : selfName      <- 이 이름만 담긴 스코프가 하나 더 있다
        fact.name            : "selfName"

   ★ 함수 선언이라면 이름 하나가 양쪽에 다 있다. 표현식은 그 이름이 안쪽에 갇힌다.
```

- ★★ **안쪽 이름은 바꿀 수 없는 바인딩이다.** 비엄격에서는 대입이 **조용히 무시되고**(`typeof me` 가 여전히 `function`),
  엄격에서는 `TypeError: Assignment to constant variable.` 이 난다. **같은 잘못이 한쪽에서는 침묵한다.**
- ★★ **그 이름은 자기 스코프에 산다** — 같은 이름의 매개변수나 `var` 가 있으면 **그쪽이 이긴다**(둘 다 `number`).
  「함수 이름이니까 이길 것」이라는 직관이 틀린 자리다.
- ★★★ **그래서 기명 함수 표현식은 재귀에서 값을 한다.** 바깥 변수를 누가 덮어써도(`holder = ...`)
  **안쪽 이름은 원래 함수를 계속 가리킨다.** 익명으로 자기 이름을 부르면 **바깥 변수가 비는 순간 `TypeError`** 다 — 출력의 마지막 줄이 그것이다.

### (4) ★★★ `arguments` — 한 몸일 때와 끊길 때

```js
// js08b-08d-arguments.js
// arguments 와 매개변수의 연동 -- 비엄격에서는 이어지고 엄격에서는 끊긴다.
// 같은 탐침을 두 번 컴파일해(그대로 / "use strict"; 붙여) 격자로 받는다.
const PROBES = [
  ["write param, read arguments", `
    function f(a) { a = 99; return "arguments[0]=" + arguments[0]; }
    return f(1);
  `],
  ["write arguments, read param", `
    function f(a) { arguments[0] = 99; return "a=" + a; }
    return f(1);
  `],
  ["two params, write the second", `
    function f(a, b) { b = 99; return "arguments=" + JSON.stringify([...arguments]); }
    return f(1, 2);
  `],
  ["param not passed, then written", `
    function f(a) { a = 99; return "len=" + arguments.length + " [0]=" + arguments[0]; }
    return f();
  `],
  ["delete arguments[0], then write param", `
    function f(a) { delete arguments[0]; a = 99; return "[0]=" + arguments[0] + " a=" + a; }
    return f(1);
  `],
  ["default param present", `
    function f(a, b = 2) { a = 99; return "arguments[0]=" + arguments[0]; }
    return f(1, 2);
  `],
  ["rest param present", `
    function f(a, ...r) { a = 99; return "arguments[0]=" + arguments[0]; }
    return f(1, 2);
  `],
  ["destructuring param present", `
    function f(a, { b } = {}) { a = 99; return "arguments[0]=" + arguments[0]; }
    return f(1, { b: 2 });
  `],
  ["arguments.callee", `
    function f(a) { return "callee is f? " + (arguments.callee === f); }
    return f(1);
  `],
  ["duplicate parameter names", `
    function f(a, a) { return "a=" + a + " arguments=" + JSON.stringify([...arguments]); }
    return f(1, 2);
  `],
  ["assign to arguments itself", `
    function f(a) { arguments = 1; return "arguments=" + arguments; }
    return f(1);
  `],
  ["arguments as a parameter name", `
    function f(arguments) { return "arguments=" + arguments; }
    return f(7);
  `],
];

function run(body, strict) {
  const src = (strict ? '"use strict";\n' : "") + body;
  try { return String(new Function(src)()); }
  catch (e) { return (e instanceof SyntaxError ? "COMPILE " : "") + e.constructor.name + ": " + e.message; }
}

console.log("[1] sloppy vs strict -- same probe, compiled twice");
let differ = 0;
for (const [label, body] of PROBES) {
  const s = run(body, false);
  const t = run(body, true);
  if (s !== t) differ += 1;
  console.log("  " + label);
  console.log("    " + "sloppy".padEnd(8) + s);
  console.log("    " + "strict".padEnd(8) + t + (s === t ? "" : "   <-- DIFFERENT"));
}
console.log("");
console.log("  " + "settings-dependent cells".padEnd(30) + differ + " of " + PROBES.length);

console.log("");
console.log("[2] arguments is not an array -- what it has and what it lacks");
function probe(a, b) { return arguments; }
const args = probe(1, 2, 3);
const rows = [
  ["brand", Object.prototype.toString.call(args)],
  ["Array.isArray", String(Array.isArray(args))],
  ["length", String(args.length)],
  ["fn.length", String(probe.length)],
  ["typeof args.map", typeof args.map],
  ["typeof args[Symbol.iterator]", typeof args[Symbol.iterator]],
  ["own keys", JSON.stringify(Object.getOwnPropertyNames(args))],
  ["proto is Object.prototype?", String(Object.getPrototypeOf(args) === Object.prototype)],
  ["spread to array", JSON.stringify([...args])],
  ["Array.from", JSON.stringify(Array.from(args))],
];
for (const [k, v] of rows) console.log("  " + k.padEnd(30) + v);

console.log("");
console.log("[3] rest is a real array -- the same probe with ...r");
function probe2(a, ...r) { return r; }
const rest = probe2(1, 2, 3);
const rows2 = [
  ["brand", Object.prototype.toString.call(rest)],
  ["Array.isArray", String(Array.isArray(rest))],
  ["length", String(rest.length)],
  ["fn.length", String(probe2.length)],
  ["typeof rest.map", typeof rest.map],
  ["holds", JSON.stringify(rest)],
  ["rest only takes the leftovers", JSON.stringify(probe2(1))],
];
for (const [k, v] of rows2) console.log("  " + k.padEnd(30) + v);
```

```text
===== node20 js08b-08d-arguments.js (exit=0) =====
[1] sloppy vs strict -- same probe, compiled twice
  write param, read arguments
    sloppy  arguments[0]=99
    strict  arguments[0]=1   <-- DIFFERENT
  write arguments, read param
    sloppy  a=99
    strict  a=1   <-- DIFFERENT
  two params, write the second
    sloppy  arguments=[1,99]
    strict  arguments=[1,2]   <-- DIFFERENT
  param not passed, then written
    sloppy  len=0 [0]=undefined
    strict  len=0 [0]=undefined
  delete arguments[0], then write param
    sloppy  [0]=undefined a=99
    strict  [0]=undefined a=99
  default param present
    sloppy  arguments[0]=1
    strict  arguments[0]=1
  rest param present
    sloppy  arguments[0]=1
    strict  arguments[0]=1
  destructuring param present
    sloppy  arguments[0]=1
    strict  arguments[0]=1
  arguments.callee
    sloppy  callee is f? true
    strict  TypeError: 'caller', 'callee', and 'arguments' properties may not be accessed on strict mode functions or the arguments objects for calls to them   <-- DIFFERENT
  duplicate parameter names
    sloppy  a=2 arguments=[1,2]
    strict  COMPILE SyntaxError: Duplicate parameter name not allowed in this context   <-- DIFFERENT
  assign to arguments itself
    sloppy  arguments=1
    strict  COMPILE SyntaxError: Unexpected eval or arguments in strict mode   <-- DIFFERENT
  arguments as a parameter name
    sloppy  arguments=7
    strict  COMPILE SyntaxError: Unexpected eval or arguments in strict mode   <-- DIFFERENT

  settings-dependent cells      7 of 12

[2] arguments is not an array -- what it has and what it lacks
  brand                         [object Arguments]
  Array.isArray                 false
  length                        3
  fn.length                     2
  typeof args.map               undefined
  typeof args[Symbol.iterator]  function
  own keys                      ["0","1","2","length","callee"]
  proto is Object.prototype?    true
  spread to array               [1,2,3]
  Array.from                    [1,2,3]

[3] rest is a real array -- the same probe with ...r
  brand                         [object Array]
  Array.isArray                 true
  length                        2
  fn.length                     1
  typeof rest.map               function
  holds                         [2,3]
  rest only takes the leftovers []
```

```text
   비엄격 + 단순 매개변수 목록            그 밖의 모든 경우

   function f(a) {                       function f(a) { "use strict"; ... }
     a = 99;                             function f(a, b = 1) { ... }
     arguments[0]  ->  99                function f(a, ...r) { ... }
   }                                     function f(a, { b }) { ... }
   한 장부를 둘이 나눠 본다                  두 장부가 따로 논다 (arguments[0] -> 1)

   ★ 끊는 것은 엄격 모드 하나가 아니다. 기본값 하나만 붙여도 끊긴다.
```

- ★★★ **연동은 양방향이다.** 매개변수를 고치면 `arguments` 가 바뀌고, `arguments` 를 고치면 매개변수가 바뀐다.
  출력의 첫 두 탐침이 각각 한 방향씩 확인한다.
- ★★★ **기본 매개변수 하나로 연동이 끊긴다 — 비엄격이어도 끊긴다.** 이것이 이 주제에서 가장 조용한 함정이다.
  `function f(a) { arguments[0] = x; }` 로 돌아가던 코드에 나중에 `function f(a, b = 1)` 을 만들면
  **에러 없이 동작만 바뀐다.** 나머지 매개변수·구조 분해 매개변수도 똑같다.
- ★★ **전달되지 않은 인자는 연동될 자리가 없다.** `f()` 로 부르고 `a = 99` 를 해도 `arguments.length` 는 `0`,
  `arguments[0]` 은 `undefined` 다. **연동은 「넘어온 만큼」만 걸린다.**
- ★★ **`delete arguments[0]` 은 그 자리의 연동을 끊는다** — 지운 뒤 `a = 99` 를 해도 `arguments[0]` 은 돌아오지 않는다.
- ★★ **`arguments` 는 배열이 아니다.** 브랜드가 `[object Arguments]` 이고 `Array.isArray` 가 `false` 이며
  **`map` 이 없다**(`typeof args.map` 이 `undefined`). 프로토타입은 `Object.prototype` 이다.
  다만 **`Symbol.iterator` 는 있어서** 스프레드와 `Array.from` 이 둘 다 통한다.
- ★★★ **나머지 매개변수는 진짜 배열이다.** 같은 탐침에서 브랜드가 `[object Array]` 이고 `map` 이 있다.
  ★ 그리고 **세는 대상이 다르다** — `arguments.length` 는 **넘어온 전부**를, `...r` 은 **앞 매개변수가 가져가고 남은 것**만 담는다.
- ★ **`arguments.callee` 는 엄격에서 `TypeError` 다.** 「조용한 실패」가 아니라 **시끄러운 실패**로 바뀌는 자리다.

### (5) ★★★ 기본 매개변수 — 호출마다 평가된다

```js
// js08b-08e-defaults.js
// 기본 매개변수 -- 호출마다 평가된다. 그리고 앞 매개변수는 보이고 뒤 매개변수는 안 보인다.
function show(label, run) {
  try { console.log("  " + label.padEnd(46) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(46) + " -> " + e.constructor.name + ": " + e.message); }
}

console.log("[1] the default expression runs on every call -- not once at definition");
let evalCount = 0;
function fresh(list = (evalCount++, [])) { list.push("x"); return JSON.stringify(list); }
show("fresh() 1st", () => fresh());
show("fresh() 2nd", () => fresh());
show("fresh() 3rd", () => fresh());
show("how many times was it evaluated", () => evalCount);
const shared = [];
function notFresh(list = shared) { list.push("x"); return JSON.stringify(list); }
show("notFresh() 1st (shared array)", () => notFresh());
show("notFresh() 2nd (shared array)", () => notFresh());
show("passing a value skips the default", () => { evalCount = 0; fresh(["given"]); return "evals=" + evalCount; });

console.log("");
console.log("[2] what triggers the default -- only undefined does");
function trig(a = "DEFAULT") { return typeof a + " " + JSON.stringify(String(a)); }
for (const [label, run] of [
  ["trig()", () => trig()],
  ["trig(undefined)", () => trig(undefined)],
  ["trig(null)", () => trig(null)],
  ["trig(0)", () => trig(0)],
  ["trig('')", () => trig("")],
  ["trig(NaN)", () => trig(NaN)],
  ["trig(false)", () => trig(false)],
  ["trig(void 0)", () => trig(void 0)],
]) show(label, run);

console.log("");
console.log("[3] length counts only the params before the first default or rest");
const lens = [
  ["(a, b, c)", function (a, b, c) {}],
  ["(a, b = 1, c)", function (a, b = 1, c) {}],
  ["(a = 1, b, c)", function (a = 1, b, c) {}],
  ["(a, ...r)", function (a, ...r) {}],
  ["(...r)", function (...r) {}],
  ["({ a }, b)", function ({ a }, b) {}],
  ["(a, { b } = {})", function (a, { b } = {}) {}],
  ["()", function () {}],
];
for (const [label, f] of lens) console.log("  " + label.padEnd(46) + " -> length " + f.length);
console.log("  " + "arguments.length is what was passed".padEnd(46) + " -> " +
            (function (a, b = 1, c) { return arguments.length; })(1, 2, 3, 4));

console.log("");
console.log("[4] a default can see the params to its left, never the ones to its right");
show("(a, b = a * 2) with f(3)", () => (function (a, b = a * 2) { return a + "," + b; })(3));
show("(a = b, b = 2) with f()", () => (function (a = b, b = 2) { return a + "," + b; })());
show("(a = b, b = 2) with f(1)", () => (function (a = b, b = 2) { return a + "," + b; })(1));
show("(a = later()) with later below", () => {
  function g(a = later()) { return a; }
  function later() { return "hoisted decl is fine"; }
  return g();
});
show("(a = a) with f()", () => (function (a = a) { return a; })());

console.log("");
console.log("[5] a non-simple parameter list gets its own scope -- var in the body does not reach it");
show("param scope: (a, b = () => a) then var a = 99", () =>
  (function (a, b = () => a) { var a = 99; return "a=" + a + " b()=" + b(); })(1));
show("simple list for comparison (no default)", () =>
  (function (a, b) { var a = 99; return "a=" + a; })(1, 2));
show("default sees the outer binding, not the body var", () => {
  var outer = "outer";
  return (function (a = outer) { var outer = "body"; return "a=" + a + " outer=" + outer; })();
});
```

```text
===== node20 js08b-08e-defaults.js (exit=0) =====
[1] the default expression runs on every call -- not once at definition
  fresh() 1st                                    -> ["x"]
  fresh() 2nd                                    -> ["x"]
  fresh() 3rd                                    -> ["x"]
  how many times was it evaluated                -> 3
  notFresh() 1st (shared array)                  -> ["x"]
  notFresh() 2nd (shared array)                  -> ["x","x"]
  passing a value skips the default              -> evals=0

[2] what triggers the default -- only undefined does
  trig()                                         -> string "DEFAULT"
  trig(undefined)                                -> string "DEFAULT"
  trig(null)                                     -> object "null"
  trig(0)                                        -> number "0"
  trig('')                                       -> string ""
  trig(NaN)                                      -> number "NaN"
  trig(false)                                    -> boolean "false"
  trig(void 0)                                   -> string "DEFAULT"

[3] length counts only the params before the first default or rest
  (a, b, c)                                      -> length 3
  (a, b = 1, c)                                  -> length 1
  (a = 1, b, c)                                  -> length 0
  (a, ...r)                                      -> length 1
  (...r)                                         -> length 0
  ({ a }, b)                                     -> length 2
  (a, { b } = {})                                -> length 1
  ()                                             -> length 0
  arguments.length is what was passed            -> 4

[4] a default can see the params to its left, never the ones to its right
  (a, b = a * 2) with f(3)                       -> 3,6
  (a = b, b = 2) with f()                        -> ReferenceError: Cannot access 'b' before initialization
  (a = b, b = 2) with f(1)                       -> 1,2
  (a = later()) with later below                 -> hoisted decl is fine
  (a = a) with f()                               -> ReferenceError: Cannot access 'a' before initialization

[5] a non-simple parameter list gets its own scope -- var in the body does not reach it
  param scope: (a, b = () => a) then var a = 99  -> a=99 b()=1
  simple list for comparison (no default)        -> a=99
  default sees the outer binding, not the body var -> a=outer outer=body
```

```text
   function fresh(list = []) { list.push("x"); return list; }

     fresh()  ->  ["x"]        <- 새 배열
     fresh()  ->  ["x"]        <- 또 새 배열
     fresh()  ->  ["x"]        <- 또 새 배열

   ★ 기본값 자리에 있는 것은 「값」이 아니라 「식」이다. 부를 때마다 다시 평가된다.
   ★ 인자를 주면 그 식은 아예 평가되지 않는다(evals=0).
```

- ★★★ **이것이 파이썬과 정반대다.** 같은 모양의 코드를 파이썬에서 돌리면 이렇게 된다.

```python
# js08b-08p-default-contrast.py
# 같은 모양의 함수를 파이썬에서 -- 기본값은 정의 시점에 한 번만 만들어진다.
def fresh(items=[]):
    items.append("x")
    return items

print("[1] python: default evaluated once, at definition time")
print("  fresh() 1st   ->", fresh())
print("  fresh() 2nd   ->", fresh())
print("  fresh() 3rd   ->", fresh())
print("  the object itself ->", fresh.__defaults__)

print("")
print("[2] python: None does not trigger anything -- there is no undefined rule")
def trig(a="DEFAULT"):
    return (type(a).__name__, a)

print("  trig()        ->", trig())
print("  trig(None)    ->", trig(None))
print("  trig(0)       ->", trig(0))
```

```text
===== python3 js08b-08p-default-contrast.py (exit=0) =====
[1] python: default evaluated once, at definition time
  fresh() 1st   -> ['x']
  fresh() 2nd   -> ['x', 'x']
  fresh() 3rd   -> ['x', 'x', 'x']
  the object itself -> (['x', 'x', 'x'],)

[2] python: None does not trigger anything -- there is no undefined rule
  trig()        -> ('str', 'DEFAULT')
  trig(None)    -> ('NoneType', None)
  trig(0)       -> ('int', 0)
```

  ★★★ **파이썬은 `def` 를 만나는 순간 기본값 객체를 한 번 만들어 함수에 붙여 둔다**(`fresh.__defaults__` 가 그 객체 자신이다).
  그래서 리스트가 **호출을 건너 쌓인다.** JS 는 붙여 두는 것이 없고 **식을 들고 있다가 부를 때마다 실행**한다.
  ★★ 그래서 **파이썬에서는 `None` 센티널이 관용구이고 JS 에서는 그 관용구가 필요 없다** —
  자세한 것은 [파이썬 갈래의 20번 「가변 기본 인자 함정」](../../../python/syntax/20-mutable-default-args/)이 정본이다.
  ★ 그리고 **함정의 방향이 정반대다** — 파이썬은 「같은 객체가 계속 쓰여서」 사고가 나고,
  JS 는 「매번 새 객체라서」 사고가 난다(캐시·누적을 기본값에 기대는 코드).
- ★★★ **기본값을 부르는 조건은 `undefined` 하나다.** `null`·`0`·`""`·`NaN`·`false` 는 전부 **그대로 들어온다.**
  `void 0` 은 `undefined` 이므로 기본값이 걸린다.
  ★ **`||` 로 기본값을 흉내 내던 습관과 다른 자리**가 여기다 — `||` 는 falsy 전부를 갈아치운다.
- ★★ **`length` 는 「첫 기본값·나머지 앞까지」만 센다.** `(a, b = 1, c)` 가 `1` 이고 `(a = 1, b, c)` 가 `0` 이다.
  **뒤에 이름이 몇 개 더 있든 세지 않는다.** 구조 분해 매개변수는 기본값이 없으면 **한 자리로 센다**(`({ a }, b)` 가 `2`).
- ★★★ **기본값은 왼쪽을 볼 수 있고 오른쪽은 못 본다.** `(a, b = a * 2)` 는 돌고 `(a = b, b = 2)` 는
  `ReferenceError: Cannot access 'b' before initialization` 이다 — **매개변수도 TDZ 를 탄다**([05번](../05-var-let-const-and-tdz/2-summary.md)).
  `(a = a)` 도 같은 이유로 터진다.
- ★★ **단순하지 않은 매개변수 목록은 자기 스코프를 따로 갖는다.** 출력의 `[5]` 가 그것이다 —
  `function (a, b = () => a) { var a = 99; return b(); }` 에서 **`a` 는 `99` 인데 `b()` 는 `1`** 을 돌려준다.
  ★ 본문의 `var a` 는 매개변수 스코프의 `a` 와 **다른 칸**이고, 기본값 식이 붙들고 있는 것은 **매개변수 쪽**이다.
  ★ 그래서 기본값 식이 바깥 변수를 참조하면 **본문의 같은 이름 `var` 가 아니라 바깥 것**을 본다(마지막 줄).

### (6) ★★ 매개변수 목록의 문법 — 무엇이 컴파일되나

```js
// js08b-08f-param-syntax.js
// 매개변수 목록의 문법 -- 무엇이 컴파일되고 무엇이 SyntaxError 인가.
// 같은 소스를 두 번 컴파일한다: 그대로(비엄격)와 "use strict"; 를 앞에 붙여(엄격).
const FORMS = [
  ["f(a, b)", "function f(a, b) {}"],
  ["f(a, b,)  trailing comma", "function f(a, b,) {}"],
  ["f(a, a)  duplicate", "function f(a, a) {}"],
  ["f(a, a = 1)  dup + default", "function f(a, a = 1) {}"],
  ["(a, a) => {}", "var g = (a, a) => {};"],
  ["f(a = 1) { 'use strict'; }", "function f(a = 1) { 'use strict'; }"],
  ["f(a, b) { 'use strict'; }", "function f(a, b) { 'use strict'; }"],
  ["f(a, a) { 'use strict'; }", "function f(a, a) { 'use strict'; }"],
  ["f(...r)", "function f(...r) {}"],
  ["f(...r,)  comma after rest", "function f(...r,) {}"],
  ["f(...r, b)  rest not last", "function f(...r, b) {}"],
  ["f(...r = [])  rest default", "function f(...r = []) {}"],
  ["f(a = 1, b)  default first", "function f(a = 1, b) {}"],
  ["f({ a }, [b])  destructured", "function f({ a }, [b]) {}"],
  ["f(eval)", "function f(eval) {}"],
  ["f(arguments)", "function f(arguments) {}"],
  ["(arguments) => {}", "var g = (arguments) => {};"],
  ["f(a) { var arguments; }", "function f(a) { var arguments; }"],
  ["f(yield)", "function f(yield) {}"],
  ["function* f(yield) {}", "function* f(yield) {}"],
];

function compile(src, strict) {
  try { new Function((strict ? '"use strict";\n' : "") + src); return "ok"; }
  catch (e) { return e.constructor.name + ": " + e.message; }
}

console.log("[1] parameter list forms -- compiled twice");
console.log("  " + "form".padEnd(32) + "sloppy".padEnd(8) + "strict");
let differ = 0;
for (const [label, src] of FORMS) {
  const s = compile(src, false);
  const t = compile(src, true);
  if (s !== t) differ += 1;
  console.log("  " + label.padEnd(32) + (s === "ok" ? "ok" : "ERR").padEnd(8) + (t === "ok" ? "ok" : "ERR") +
              (s === t ? "" : "   <-- DIFFERENT"));
}
console.log("  " + "settings-dependent cells".padEnd(32) + differ + " of " + FORMS.length);

console.log("");
console.log("[2] the messages behind the ERR cells");
for (const [label, src] of FORMS) {
  const s = compile(src, false);
  const t = compile(src, true);
  if (s !== "ok") console.log("  " + ("sloppy " + label).padEnd(42) + s);
  if (t !== "ok" && t !== s) console.log("  " + ("strict " + label).padEnd(42) + t);
}
```

```text
===== node20 js08b-08f-param-syntax.js (exit=0) =====
[1] parameter list forms -- compiled twice
  form                            sloppy  strict
  f(a, b)                         ok      ok
  f(a, b,)  trailing comma        ok      ok
  f(a, a)  duplicate              ok      ERR   <-- DIFFERENT
  f(a, a = 1)  dup + default      ERR     ERR
  (a, a) => {}                    ERR     ERR
  f(a = 1) { 'use strict'; }      ERR     ERR
  f(a, b) { 'use strict'; }       ok      ok
  f(a, a) { 'use strict'; }       ERR     ERR
  f(...r)                         ok      ok
  f(...r,)  comma after rest      ERR     ERR
  f(...r, b)  rest not last       ERR     ERR
  f(...r = [])  rest default      ERR     ERR
  f(a = 1, b)  default first      ok      ok
  f({ a }, [b])  destructured     ok      ok
  f(eval)                         ok      ERR   <-- DIFFERENT
  f(arguments)                    ok      ERR   <-- DIFFERENT
  (arguments) => {}               ok      ERR   <-- DIFFERENT
  f(a) { var arguments; }         ok      ERR   <-- DIFFERENT
  f(yield)                        ok      ERR   <-- DIFFERENT
  function* f(yield) {}           ERR     ERR   <-- DIFFERENT
  settings-dependent cells        7 of 20

[2] the messages behind the ERR cells
  strict f(a, a)  duplicate                 SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(a, a = 1)  dup + default         SyntaxError: Duplicate parameter name not allowed in this context
  sloppy (a, a) => {}                       SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(a = 1) { 'use strict'; }         SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list
  sloppy f(a, a) { 'use strict'; }          SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(...r,)  comma after rest         SyntaxError: Rest parameter must be last formal parameter
  sloppy f(...r, b)  rest not last          SyntaxError: Rest parameter must be last formal parameter
  sloppy f(...r = [])  rest default         SyntaxError: Rest parameter may not have a default initializer
  strict f(eval)                            SyntaxError: Unexpected eval or arguments in strict mode
  strict f(arguments)                       SyntaxError: Unexpected eval or arguments in strict mode
  strict (arguments) => {}                  SyntaxError: Unexpected eval or arguments in strict mode
  strict f(a) { var arguments; }            SyntaxError: Unexpected eval or arguments in strict mode
  strict f(yield)                           SyntaxError: Unexpected strict mode reserved word
  sloppy function* f(yield) {}              SyntaxError: Unexpected identifier 'yield'
  strict function* f(yield) {}              SyntaxError: Unexpected strict mode reserved word
```

- ★★★ **스무 형태 중 일곱이 설정에 달렸다.** 중복 매개변수 이름 · `eval`/`arguments` 를 이름으로 쓰기 ·
  `var arguments` · `yield` 를 이름으로 쓰기가 그것이고, **비엄격에서는 전부 통과한다.**
- ★★★ **「`'use strict';` 를 함수 안에 못 쓰는」 자리가 있다.** 매개변수 목록이 단순하지 않으면
  `SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list` 다.
  ★ **기본값을 하나 붙인 순간 그 함수만 엄격으로 만들 방법이 사라진다** — 파일이나 모듈 단위로 올려야 한다.
- ★★ **중복 이름은 「엄격에서만 금지」가 아니다.** 목록이 단순하지 않으면 **비엄격에서도 `SyntaxError`** 이고,
  화살표는 **모드와 무관하게** 금지다. 즉 **금지 조건이 셋**이다 — 엄격이거나, 목록이 단순하지 않거나, 화살표이거나.
- ★ **나머지 매개변수는 마지막이어야 하고 기본값을 못 가진다.** 문구가 서로 달라
  (`Rest parameter must be last formal parameter` 대 `may not have a default initializer`)
  **어느 규칙에 걸렸는지가 메시지로 갈린다.**
- ★ **꼬리 쉼표는 매개변수 목록에서는 되고 나머지 매개변수 뒤에서는 안 된다.**

### (7) ★★ 두 판에서 돌려 보면 — 갈린 칸이 하나 있다

```text
===== ./js08b-vdiff.sh 08 (exit=0) =====
  same      js08b-08a-forms.js
  same      js08b-08b-hoisting.js
  same      js08b-08c-named-fexpr.js
  same      js08b-08d-arguments.js
  same      js08b-08e-defaults.js
  DIFFERENT js08b-08f-param-syntax.js
      39c39
      <   sloppy function* f(yield) {}              SyntaxError: Unexpected identifier
      ---
      >   sloppy function* f(yield) {}              SyntaxError: Unexpected identifier 'yield'
  ----
  identical on node18 and node20: 5   different: 1
```

- ★★ **여섯 스크립트 중 다섯이 두 판에서 한 글자도 같았고, 하나가 갈렸다.**
  갈린 것은 **값이 아니라 예외 문구**다 — `SyntaxError: Unexpected identifier` 가 v20 에서 `Unexpected identifier 'yield'` 가 됐다.
- ★★ **그래서 v18 쪽도 같이 싣는다.** 갈린 블록만 양쪽을 싣는 것이 이 갈래의 규칙이다.

```text
===== node18 js08b-08f-param-syntax.js (exit=0) =====
[1] parameter list forms -- compiled twice
  form                            sloppy  strict
  f(a, b)                         ok      ok
  f(a, b,)  trailing comma        ok      ok
  f(a, a)  duplicate              ok      ERR   <-- DIFFERENT
  f(a, a = 1)  dup + default      ERR     ERR
  (a, a) => {}                    ERR     ERR
  f(a = 1) { 'use strict'; }      ERR     ERR
  f(a, b) { 'use strict'; }       ok      ok
  f(a, a) { 'use strict'; }       ERR     ERR
  f(...r)                         ok      ok
  f(...r,)  comma after rest      ERR     ERR
  f(...r, b)  rest not last       ERR     ERR
  f(...r = [])  rest default      ERR     ERR
  f(a = 1, b)  default first      ok      ok
  f({ a }, [b])  destructured     ok      ok
  f(eval)                         ok      ERR   <-- DIFFERENT
  f(arguments)                    ok      ERR   <-- DIFFERENT
  (arguments) => {}               ok      ERR   <-- DIFFERENT
  f(a) { var arguments; }         ok      ERR   <-- DIFFERENT
  f(yield)                        ok      ERR   <-- DIFFERENT
  function* f(yield) {}           ERR     ERR   <-- DIFFERENT
  settings-dependent cells        7 of 20

[2] the messages behind the ERR cells
  strict f(a, a)  duplicate                 SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(a, a = 1)  dup + default         SyntaxError: Duplicate parameter name not allowed in this context
  sloppy (a, a) => {}                       SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(a = 1) { 'use strict'; }         SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list
  sloppy f(a, a) { 'use strict'; }          SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(...r,)  comma after rest         SyntaxError: Rest parameter must be last formal parameter
  sloppy f(...r, b)  rest not last          SyntaxError: Rest parameter must be last formal parameter
  sloppy f(...r = [])  rest default         SyntaxError: Rest parameter may not have a default initializer
  strict f(eval)                            SyntaxError: Unexpected eval or arguments in strict mode
  strict f(arguments)                       SyntaxError: Unexpected eval or arguments in strict mode
  strict (arguments) => {}                  SyntaxError: Unexpected eval or arguments in strict mode
  strict f(a) { var arguments; }            SyntaxError: Unexpected eval or arguments in strict mode
  strict f(yield)                           SyntaxError: Unexpected strict mode reserved word
  sloppy function* f(yield) {}              SyntaxError: Unexpected identifier
  strict function* f(yield) {}              SyntaxError: Unexpected strict mode reserved word
```

- ★★★ **이 차이는 언어가 아니라 V8 의 문구**다. 무엇이 `SyntaxError` 인지는 안 바뀌었고 **어떻게 말하는지만** 바뀌었다.
  ★ 그래서 **문서에서 근거로 쓰는 것은 「종류」이고 「문구」가 아니다** — 머리말의 「흔들리는 칸」 표가 그것을 미리 선언해 둔 것이다.

### (8) ★★ 같은 질문을 브라우저에 던지면

```js
// js08b-08h-browser.js
// 같은 질문을 브라우저에 던진다 -- 호스트가 정하는 칸이 있나.
const lines = [];
function row(k, v) { lines.push("  " + k.padEnd(34) + v); }

row("engine", navigator.userAgent.replace(/^.*(Chrome\/[0-9.]+).*$/, "$1"));
function decl(a, b) { return [a, b]; }
const arrow = (a, b) => [a, b];
row("decl.length", String(decl.length));
row("arrow has prototype?", String(Object.prototype.hasOwnProperty.call(arrow, "prototype")));
row("(function (a, b = 1) {}).length", String((function (a, b = 1) {}).length));

function mapped(a) { a = 99; return arguments[0]; }
row("sloppy param-arguments link", String(mapped(1)));
function unmapped(a) { "use strict"; a = 99; return arguments[0]; }
row("strict param-arguments link", String(unmapped(1)));
function withDefault(a, b = 2) { a = 99; return arguments[0]; }
row("default param breaks the link", String(withDefault(1, 2)));

let n = 0;
function fresh(list = (n++, [])) { list.push("x"); return list.length; }
fresh(); fresh(); fresh();
row("default evaluated per call", "calls=3 evals=" + n);

row("arguments brand", Object.prototype.toString.call((function () { return arguments; })()));
try { (function (a) { "use strict"; return arguments.callee; })(1); row("strict arguments.callee", "no throw"); }
catch (e) { row("strict arguments.callee", e.constructor.name); }
try { new Function('"use strict"; function f(a, a) {}'); row("strict duplicate param", "ok"); }
catch (e) { row("strict duplicate param", e.constructor.name); }
try { new Function("function f(a = 1) { 'use strict'; }"); row("'use strict' + default param", "ok"); }
catch (e) { row("'use strict' + default param", e.constructor.name); }
const named = function selfName() { return typeof selfName; };
row("named fn expr, name inside", named());
row("named fn expr, name outside", typeof window.selfName);

document.documentElement.appendChild(document.createElement("pre")).textContent =
  "===OUT===" + String.fromCharCode(10) + lines.join(String.fromCharCode(10)) + String.fromCharCode(10) + "===END===";
```

호스트 페이지는 이 네 줄이 전부다.

```text
<!doctype html>
<meta charset="utf-8">
<title>js08b 08</title>
<script src="js08b-08h-browser.js"></script>
```

```text
===== google-chrome --headless --dump-dom page08.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' (exit=0) =====
  engine                            Chrome/151.0.0.0
  decl.length                       2
  arrow has prototype?              false
  (function (a, b = 1) {}).length   1
  sloppy param-arguments link       99
  strict param-arguments link       1
  default param breaks the link     1
  default evaluated per call        calls=3 evals=3
  arguments brand                   [object Arguments]
  strict arguments.callee           TypeError
  strict duplicate param            SyntaxError
  'use strict' + default param      SyntaxError
  named fn expr, name inside        function
  named fn expr, name outside       undefined
```

- ★★★ **호스트가 정하는 칸이 하나도 없었다.** 열네 줄이 Node 쪽 답과 전부 같다.
  ★ 07번(`this`)에서는 호스트 칸이 네 개였는데 **여기서는 0개**다 — 함수 형태와 매개변수는 **순수하게 언어 쪽**이라는 뜻이다.
  ★★ 다만 **「같았다」는 보장이 아니라 관찰**이다. 보장은 명세가 하고, 이 줄은 **그 보장이 이 두 호스트에서 지켜졌다**는 관찰이다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js08b-08x-forms.js
// 형태만 모아 둔 파일 -- 출력은 없다. `node --check` 로 문법만 확인한다.
function decl(a, b) { return a + b; }               // 선언   -- 이름과 값이 둘 다 호이스팅된다
const expr = function (a, b) { return a + b; };     // 표현식 -- 붙은 이름의 규칙을 따른다
const named = function add(a, b) { return a + b; }; // 기명   -- add 는 안쪽에서만 보인다
const arrow = (a, b) => a + b;                      // 화살표 -- this·arguments·prototype 칸이 없다
const obj = { m(a, b) { return a + b; } };          // 메서드 단축 -- prototype 이 없다
const gen = function* (a) { yield a; };             // 제너레이터 -- prototype 은 있고 new 는 안 된다
const asy = async (a) => a;                         // async 화살표 -- 둘 다 없다

function withDefault(a, b = a * 2) { return [a, b]; }   // 기본값 -- 호출마다 평가된다
function withRest(a, ...rest) { return [a, rest]; }     // 나머지 -- 진짜 배열이다
function withPattern({ x = 0 } = {}) { return x; }      // 구조 분해 매개변수 -- 10번 주제
function trailing(a, b,) { return a + b; }              // 꼬리 쉼표 -- ES2017

function mapped(a) { a = 99; return arguments[0]; }     // 비엄격 + 단순 목록 -- 99
function unmapped(a) { "use strict"; a = 99; return arguments[0]; }  // 엄격 -- 1
function broken(a, b = 1) { a = 99; return arguments[0]; }           // 기본값 하나로 끊긴다 -- 1

const selfRec = function me(n) { return n <= 1 ? 1 : n * me(n - 1); }; // 안쪽 이름으로 재귀
```

```text
===== node20 --check js08b-08x-forms.js (exit=0) =====

```

> ★ **이 빈 블록이 근거다.** 「문법 오류가 안 났다」를 산문으로 적으면 **안 물어본 것과 구분이 안 된다.**
> 명령과 `(exit=0)` 까지 담긴 **빈 출력**이라야 「던졌고 조용했다」가 된다.

**금지 사례 — 컴파일이 안 되는 형태.** 문구까지는 위 `[2]` 블록이 확인해 준다.

```text
function bad1(...r, b) {}               // 나머지는 마지막이어야 한다
function bad2(...r = []) {}             // 나머지는 기본값을 못 가진다
function bad3(...r,) {}                 // 나머지 뒤에는 꼬리 쉼표를 못 쓴다
function bad4(a = 1) { "use strict"; }  // 단순하지 않은 목록 + 함수 안 strict 지시문
const bad5 = (a, a) => {};              // 화살표는 모드와 무관하게 중복 이름 금지
function bad6(a, a = 1) {}              // 단순하지 않은 목록이면 비엄격에서도 중복 금지
function bad7(eval) {}                  // 엄격에서만 금지 -- 비엄격이면 통과한다
```

**규칙 불릿.**

- **함수 선언은 이름과 값이 둘 다 올라간다.** 나머지 형태는 붙은 이름의 규칙(`var`/`let`/`const`)을 그대로 따른다.
- **화살표는 자기 `this`·`arguments`·`new.target` 을 안 만들고 `prototype` 도 없다.** 생성자로 못 쓴다.
- **메서드 단축 표기는 `prototype` 이 없다** — `{ m: function () {} }` 와 다르다.
- **`length` 는 첫 기본값 또는 나머지 앞까지만 센다.** `arguments.length` 는 실제로 넘어온 개수다.
- **기본값은 식이고 호출마다 평가된다.** `undefined` 일 때만 걸린다.
- **기본값은 왼쪽 매개변수를 볼 수 있고 오른쪽은 TDZ 로 막힌다.**
- **매개변수 목록이 단순하지 않으면**(기본값·나머지·구조 분해) `arguments` 연동이 끊기고,
  그 함수 안에 `"use strict";` 지시문을 쓸 수 없다.
- **중복 매개변수 이름은 엄격이거나 목록이 단순하지 않거나 화살표이면 금지다.**

## 어디서 틀리나

### (1) ★★★ 「화살표는 짧은 함수」로 외운다

화살표는 **칸이 없는 함수**다. 짧게 쓰려고 골랐는데 `this`·`arguments`·`new`·`prototype` 이 한꺼번에 사라진다.
★ 격자의 화살표 행을 통째로 읽으면 **네 칸이 동시에 X** 라는 것이 한눈에 보인다.

### (2) ★★★ 「`arguments` 를 끊는 것은 엄격 모드」로 외운다

**기본값 하나만 붙여도 끊긴다.** 비엄격이어도 끊긴다.
★ 실무에서 이것이 **에러 없이 동작만 바꾸는** 변경으로 들어온다 — 시그니처에 기본값을 더한 커밋이 원인이다.

### (3) ★★★ 기본값이 「정의 시점에 한 번」이라고 믿는다

파이썬을 먼저 배운 사람이 특히 그렇다. **JS 는 호출마다 평가한다.**
★ 반대로 **JS 만 안 사람은 파이썬에서 같은 착각을 반대 방향으로** 한다 — 두 갈래의 대비를 같이 외운다.

### (4) ★★ `length` 를 「매개변수 개수」로 읽는다

`(a, b = 1, c)` 의 `length` 는 `3` 이 아니라 `1` 이다.
★ 라이브러리가 `fn.length` 로 분기하는 코드(콜백의 arity 로 동작을 고르는 것)는 **기본값 하나에 조용히 다른 길로 간다.**

### (5) ★★ 기명 함수 표현식의 이름을 밖에서 부른다

`const f = function inner() {}` 에서 `inner()` 는 밖에서 `ReferenceError` 다.
★ 그런데 **디버거·스택트레이스에는 `inner` 로 나온다.** 그래서 「보이는데 못 부른다」는 착시가 생긴다.

### (6) ★★ 블록 안의 함수 선언에 기댄다

비엄격이면 밖에서 보이고 엄격이면 안 보인다. **모듈은 항상 엄격**이므로 ESM 으로 옮기는 순간 깨진다.
★ 고치는 법은 하나다 — **블록 안에서는 `const f = function ...` 을 쓴다.**

### (7) ★ 「매개변수도 `var` 랑 같은 스코프」라고 믿는다

단순하지 않은 목록이면 **매개변수 스코프가 따로 생긴다.** 위 `[5]` 가 그 반례다.

### (8) ★ 나머지 매개변수와 `arguments` 를 같은 것으로 쓴다

세는 대상이 다르고(`arguments` 는 전부, `...r` 은 남은 것), 타입이 다르다(유사 배열 대 배열).
★ **새 코드에서는 `arguments` 를 쓸 이유가 거의 없다** — 화살표에서 아예 안 되기도 한다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- **형태별로 `prototype`·`new`·`this`·`arguments` 칸을 갖는지**가 전부 명세다. 위 격자의 여섯 칸 전부.
- **함수 선언만 값까지 호이스팅되는 것**과 **나머지 형태가 이름 규칙을 따르는 것.**
- **기명 함수 표현식의 이름이 자기 스코프의 변경 불가 바인딩인 것.**
- **`length` 가 첫 기본값·나머지 앞까지만 세는 것**과 **`arguments.length` 가 실제 인자 수인 것.**
- **기본값이 호출마다 평가되고 `undefined` 에만 걸리는 것.**
- **기본값이 왼쪽만 볼 수 있는 것**(오른쪽은 TDZ).
- **단순하지 않은 매개변수 목록이 `arguments` 연동을 끊고 함수 안 `"use strict";` 를 금지하는 것.**
- **어떤 형태가 `SyntaxError` 인지** — 나머지 매개변수의 자리, 중복 이름의 세 조건.

### 엔진(V8) 구현 · 이 판의 관찰

- ★★ **예외 문구 전부.** `Duplicate parameter name not allowed in this context` ·
  `Illegal 'use strict' directive in function with non-simple parameter list` ·
  `Rest parameter must be last formal parameter` 는 **V8 의 말**이다. 종류(`SyntaxError`)만 명세다.
- ★★★ **두 판에서 실제로 하나가 바뀌었다** — `Unexpected identifier` 가 `Unexpected identifier 'yield'` 로.
  **문구를 근거로 쓰면 판이 오를 때 문서가 조용히 틀린다**는 것을 이 주제가 스스로 증명한다.
- ★ **`new Function` 이 만든 함수의 `name` 이 `"anonymous"` 인 것**은 명세가 정한 값이지만,
  **그 함수가 어느 스코프를 보는지**(전역만 본다)는 이 격자가 다루지 않는다.
- ★ **`bound` 접두가 붙는 것**(`"bound decl"`)은 명세다. 다만 **몇 겹까지 붙는지**는 겹칠 때마다 한 번씩 붙는 것이 관찰됐다.

### 호스트가 정하는 것

- **없다.** 브라우저에 던진 열네 줄이 Node 와 전부 같았다.
  ★ 이 주제에서 **호스트 칸이 0개인 것 자체가 결론**이다 — 07번과 정확히 대비된다.

### 그래서 이렇게 적으면 틀린다

| 이렇게 적으면 틀린다 | 이렇게 적어야 한다 |
|---|---|
| 「화살표는 `prototype` 이 없으니 `new` 가 안 된다」 | 두 성질은 따로다 — 제너레이터와 bound 함수가 반례다 |
| 「`arguments` 연동은 엄격 모드에서 끊긴다」 | 엄격이거나 **목록이 단순하지 않으면** 끊긴다 |
| 「중복 매개변수는 엄격에서만 금지」 | 목록이 단순하지 않거나 화살표여도 금지다 |
| 「`SyntaxError: Unexpected identifier 'yield'` 가 난다」 | **종류만** 근거다. 문구는 v18 과 v20 이 다르다 |
| 「`fn.length` 로 매개변수 개수를 안다」 | 기본값·나머지 앞까지만 센다 |
| 「기본값은 정의할 때 한 번 만들어진다」 | 그것은 **파이썬**이다. JS 는 호출마다 평가한다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 형태 | 왜 |
|---|---|---|
| 모듈 최상위의 이름 있는 함수 | **함수 선언** | 호이스팅이 값까지 올라가 순서에 안 눌린다 |
| 콜백·짧은 변환 | **화살표** | `this` 를 안 만들어 바깥 것을 그대로 쓴다([07번](../07-this-binding-four-rules/2-summary.md)) |
| 객체의 메서드 | **메서드 단축 표기** | `this` 가 필요하고 `prototype` 은 필요 없다 |
| 이벤트 핸들러로 넘길 메서드 | **화살표 필드 또는 `bind`** | 떼어 내도 `this` 가 안 바뀐다([09번](../09-call-apply-bind/2-summary.md)) |
| 인자 개수가 열린 함수 | **나머지 매개변수** | 진짜 배열이라 `map`·`reduce` 가 바로 된다 |
| 선택 인자가 많은 함수 | **구조 분해 매개변수 + 기본값** | 호출부에서 이름이 보인다([10번](../10-destructuring-assignment/2-summary.md)) |
| 블록 안에서만 쓸 함수 | **`const` + 함수 표현식** | 블록 함수 선언은 모드에 따라 갈린다 |
| 재귀하는 함수 표현식 | **기명 함수 표현식** | 바깥 변수가 바뀌어도 자기 이름은 안 변한다 |

**안 쓰는 쪽**

- **`arguments` 는 새 코드에서 쓰지 않는다** — 나머지 매개변수로 전부 대체된다. 화살표에서는 아예 없다.
- **`arguments.callee` 는 쓰지 않는다** — 엄격에서 `TypeError` 다. 기명 함수 표현식이 대체다.
- **기본값을 캐시·누적에 쓰지 않는다** — 호출마다 새로 만들어진다.
- **`fn.length` 로 동작을 분기하지 않는다** — 시그니처에 기본값이 하나 붙으면 조용히 바뀐다.

## 핵심 문장

- **함수 형태의 차이는 문법의 차이가 아니라 「딸려 오는 칸」의 차이다** — 격자의 한 행을 통째로 읽어야 보인다.
- **`prototype` 이 있다와 `new` 가 된다는 다른 사실이다** — 격자에 반례가 둘 있다.
- **함수 선언만 값까지 호이스팅된다.** 나머지는 붙은 이름의 규칙을 그대로 따른다.
- **`arguments` 연동을 끊는 조건은 둘이다** — 엄격이거나, 매개변수 목록이 단순하지 않거나.
- **기본 매개변수는 식이고 호출마다 평가된다** — 파이썬과 정반대다.
- **설정에 달린 칸을 세면 이 주제의 크기가 나온다** — 호이스팅 9탐침 중 1, `arguments` 12탐침 중 7, 매개변수 문법 20형태 중 7.

## 관련 자료

- [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) — **그쪽은 「어떤 호출식이 어떤 `this` 를 주나」까지, 여기는 「어떤 형태가 `this` 칸을 갖나」부터.**
- [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md) — **그쪽은 이름이 어느 환경을 붙드는가까지, 여기는 매개변수 스코프가 따로 생기는 자리부터.**
- [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md) — **TDZ 의 정본은 그쪽이고, 여기서는 매개변수 기본값이 그 규칙을 그대로 받는 것만 본다.**
- [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) — **`bind` 가 만든 함수의 성질은 그쪽이 정본이고, 여기서는 격자의 한 행으로만 등장한다.**
- [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) — **구조 분해 매개변수의 규칙은 그쪽이 정본이고, 여기서는 「목록을 단순하지 않게 만든다」는 사실까지.**
- [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」 — **strict 전체 규칙은 그쪽이고, 여기서는 함수·매개변수에 닿는 칸만 센다.**
- [파이썬 갈래의 19번 「함수 인자 규칙」](../../../python/syntax/19-function-argument-rules/) — **위치 인자·키워드 인자·가변 인자의 조합 규칙은 그쪽이 정본이다.**
- [파이썬 갈래의 20번 「가변 기본 인자 함정」](../../../python/syntax/20-mutable-default-args/) — ★★★ **기본값 평가 시점이 정반대인 자리.** 그쪽은 「한 번 만들어 계속 쓴다」, 여기는 「부를 때마다 만든다」.
- [Go 갈래의 12번 「함수: 다중 반환·명명 반환값·가변 인자」](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/) — **가변 인자를 슬라이스로 받는 설계 대비.**
- [TS 갈래의 16번 「함수 타입과 오버로드」](../../../ts/syntax/16-function-types-and-overloads/) — **타입 쪽 정본.** 여기는 런타임만 본다.

## 용어 풀이

- **함수 선언(function declaration)**: `function 이름(...) {}` 형태. 이름과 값이 둘 다 스코프 꼭대기로 올라간다.
- **함수 표현식(function expression)**: 값이 오는 자리에 쓴 `function ... {}`. 붙은 이름의 규칙을 따른다.
- **기명 함수 표현식**: 이름이 붙은 함수 표현식. 그 이름은 **함수 안쪽에서만** 보인다.
- **화살표 함수(arrow function)**: `(a) => b`. 자기 `this`·`arguments`·`new.target` 을 안 만들고 `prototype` 도 없다.
- **메서드 단축 표기(method shorthand)**: `{ m() {} }`. 메서드지만 `prototype` 이 없어 `new` 가 안 된다.
- **호이스팅(hoisting)**: 선언이 스코프 꼭대기에서 먼저 처리되는 것. **값까지 올라가는 것은 함수 선언뿐**이다.
- **TDZ(temporal dead zone)**: `let`/`const` 가 선언되기 전 구간. 읽으면 `ReferenceError` 다([05번](../05-var-let-const-and-tdz/2-summary.md)).
- **단순 매개변수 목록(simple parameter list)**: 이름만 나열한 목록. 기본값·나머지·구조 분해가 하나라도 있으면 단순하지 않다.
- **`arguments` 객체**: 함수가 받은 인자를 담은 **유사 배열**. 배열이 아니고 화살표에는 없다.
- **연동(mapped arguments)**: 비엄격 + 단순 목록에서 매개변수와 `arguments` 가 같은 칸을 보는 것.
- **나머지 매개변수(rest parameter)**: `...이름`. 남은 인자를 **진짜 배열**로 받는다. 마지막이어야 한다.
- **기본 매개변수(default parameter)**: `a = 식`. **호출마다** 평가되고 `undefined` 일 때만 걸린다.
- **`length`**: 함수가 선언한 필수 자리 수. 첫 기본값·나머지 앞까지만 센다.

## 더 들어가면

- **`Function.prototype.toString` 의 보장** — ES2018 이후 **소스 텍스트를 그대로 돌려주는 것**이 보장된다.
  다만 내장 함수와 bound 함수는 `function () { [native code] }` 다 — [09번](../09-call-apply-bind/2-summary.md)에서 실제로 찍는다.
- **`new.target`** — `new` 로 불렸는지 함수 자신이 알 수 있는 칸. 화살표에는 없다. 07번에서 다뤘다.
- **제너레이터·async 함수의 `prototype`** — 제너레이터의 `prototype` 은 「인스턴스의 프로토타입」이 아니라
  **만들어진 이터레이터의 프로토타입**이다. [목록의 **20번 주제**](../20-generators/)가 정본이다.
- **매개변수 스코프와 클로저** — 기본값 식 안에서 만든 클로저는 **매개변수 스코프**를 붙든다.
  위 `[5]` 가 그 관찰이고, 클로저 자체는 [06번](../06-scope-and-closures/2-summary.md)이 정본이다.
