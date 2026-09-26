# js/syntax/01 — 값의 종류와 `typeof`: 「이 값은 무엇인가」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 언어 타입 일곱과 `typeof` 의 결과표
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — 판을 가려야 할 때
> - [HTML Standard — `document.all`](https://html.spec.whatwg.org/multipage/obsolete.html#dom-document-all) — 여덟 번째 `typeof` 예외의 출처
> - [MDN — `typeof`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/typeof) · [MDN — `Object.prototype.toString`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/toString)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·타입·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> **어느 판에서 나왔는지는 아래 첫 블록**에 있다.

```sh
// js01b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 — 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    console.log("node " + v.node + "  v8 " + v.v8 + "  icu " + v.icu + "  unicode " + v.unicode +
                "  Intl.Segmenter " + typeof Intl.Segmenter +
                "  isWellFormed " + typeof String.prototype.isWellFormed);'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js01b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  icu 74.2  unicode 15.1  Intl.Segmenter function  isWellFormed undefined
node 20.19.6  v8 11.3.244.8-node.33  icu 77.1  unicode 16.0  Intl.Segmenter function  isWellFormed function
Google Chrome 151.0.7922.173 
```

> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 **`e.constructor.name` 과 `e.message` 만** 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박혀 다른 머신에서 재현이 안 되기 때문이다.
> 그래서 이 주제의 블록에는 **표준 오류가 한 줄도 섞이지 않는다** — 전부 표준 출력이다.
>
> **버전** — 원시 타입 일곱 중 `symbol` 은 ES2015, `bigint` 는 ES2020 에 들어왔다. 나머지는 초판부터다.
> `Object.hasOwn` 은 ES2022, `Array.prototype.at` 은 ES2022 — 이 주제에서는 쓰지 않는다.
>
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계로 가르려고 미리 선언한다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 그래서 한 줄도 싣지 않았다 | **`typeof` 의 결과 문자열** 여덟 가지 |
> | 판이 오르면 바뀔 수 있는 **예외 메시지 문구** | **예외의 타입**(`ReferenceError`·`TypeError`) |
> | `document.all.length` — 페이지의 요소 수에 달렸다 | **`Object.prototype.toString.call` 의 태그 문자열** |
> | 브라우저 UA 문자열의 **뒷자리**(`151.0.0.0` 은 축약된 값이다) | **`typeof` 가 선언 안 된 이름에 안 터지는 것** · 종료 코드 |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
>
> **선행** — 없다. 이 갈래의 첫 주제다.
> **이어지는 곳** — [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) · [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md) · [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)
>
> ★★ **경계 — 타입 이야기는 여기가 아니다.** TypeScript 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **01번** [`01-what-ts-adds-and-erases`](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md)가 「타입은 런타임에 안 남는다」의 정본이다.
> 그쪽은 **검사기가 무엇을 지우는가**를, 여기는 **런타임에 무엇이 남아 있는가**를 본다.
> `typeof` 는 **지워지지 않는 쪽**이다 — 그래서 이 주제에 있다.

## 한눈에 — 쉽게 말하면

**JS 의 값은 「봉투에 들어 있지 않은 것」 일곱 종과 「봉투에 든 것」 하나로 갈린다.**

봉투에 안 든 것이 **원시 값**이다. 값 그 자체라서 고칠 수가 없고, 이름에 넣으면 **값이 복사**된다.
봉투에 든 것이 **객체**다. 이름에는 **봉투를 가리키는 쪽지**가 들어가고, 봉투 안은 언제든 고칠 수 있다.

```text
   원시 값 7종 — 값 그 자체                객체 — 봉투를 가리키는 쪽지

   undefined  null  boolean               +---------+
   number  string  symbol  bigint         | { a:1 } |  <- 봉투
                                          +---------+
     42        "abc"        true              ^    ^
     |           |            |               |    |
    x=42      s="abc"      f=true            o1   o2   <- 쪽지 둘이 한 봉투를 가리킨다

   ★ x 를 바꿔도 다른 이름은 안 바뀐다      ★ o1 로 고치면 o2 로도 보인다
   ★ 42 라는 값 자체를 고칠 방법이 없다     ★ 봉투 안은 언제든 고칠 수 있다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 봉투에 안 든 것 | 원시 값(primitive) 7종 | `typeof` 가 `object` 가 아닌 것을 답한다 |
| 봉투를 가리키는 쪽지 | 객체 참조 | 같은 봉투를 가리키는 둘은 `===` 로 같다 |
| 봉투에 「이건 날짜요」라고 적힌 딱지 | 내부 브랜드 | `Object.prototype.toString.call` 이 읽어 준다 |
| 봉투를 열어 일하는 임시 도우미 | 임시 래퍼 객체 | 메서드 안에서 `typeof this` 가 `object` 다 |
| 창고에 아예 없는 이름 | 선언 안 된 식별자 | `typeof` 만 안 터진다 |
| 창고에 자리는 잡혔는데 아직 못 쓰는 이름 | TDZ 의 `let`/`const` | `typeof` 도 터진다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 하나로 굳어 있다.
`if (typeof x === "object")` 로 「객체인가」를 물으면 **`null` 이 그 안으로 들어온다.**
그리고 `typeof x === "function"` 을 빼먹으면 **함수가 그 밖으로 빠져나간다.**
두 사고가 **같은 표의 두 칸**이고, 둘 다 「버그처럼 보이는데 명세가 그렇게 정해 둔 것」이다.

> **원시 값(primitive)** — 값 그 자체인 것. 고칠 수 없고 복사된다.
> 예: `42`·`"abc"`·`true`·`undefined`·`null`·`Symbol()`·`10n`. 일곱 종이 전부다.

> **`typeof`** — 값의 종류를 **문자열로** 답하는 연산자.
> 예: `typeof 42` 는 `"number"`. 돌려줄 수 있는 문자열은 정해져 있다.

## 이 주제가 답하려는 질문

1. **값의 종류가 몇 가지이고 `typeof` 가 그것을 그대로 답하는가** — 답은 「아니다」이고, 어긋나는 칸이 셋이다.
2. **`typeof` 가 「object」라고 답한 것을 더 갈라 보려면 무엇을 써야 하는가** — 창이 하나 더 필요하다.
3. **원시 값에 메서드를 부를 수 있는 이유는 무엇인가** — 없는 봉투가 잠깐 생겼다 사라진다.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### (1) 언어 타입은 여덟, `typeof` 의 답도 여덟 — 그런데 짝이 안 맞는다

**언제 쓰나** — 값이 무엇인지 런타임에 물어야 하는 모든 자리.

```text
   언어가 정한 값의 종류                 typeof 가 돌려주는 문자열

   Undefined  ---------------------->  "undefined"
   Null       ------\                  "object"      <- ★ 어긋난 칸 1
   Boolean    ------|--------------->  "boolean"
   Number     ------|--------------->  "number"
   String     ------|--------------->  "string"
   Symbol     ------|--------------->  "symbol"
   BigInt     ------|--------------->  "bigint"
   Object     ------+--------------->  "object"
      \                                "function"    <- ★ 어긋난 칸 2
       \-- [[Call]] 이 있는 객체 ---->
                                       (호스트가 만든 예외 하나 더 — 4번 절)

   ★ 종류는 8개, 답도 8가지. 그런데 1:1 이 아니다.
```

```js
// js01b-01a-typeof-grid.js
// 원시 7종과 객체를 한 줄씩 typeof 에 던진다.
// ★ 둘째 칸은 Object.prototype.toString.call — typeof 가 "object" 로 뭉갠 것을 갈라 준다.
const tag = (v) => Object.prototype.toString.call(v);

const rows = [
  ["undefined",            undefined],
  ["null",                 null],
  ["true",                 true],
  ["42",                   42],
  ["NaN",                  NaN],
  ["Infinity",             Infinity],
  ["10n",                  10n],
  ['"abc"',                "abc"],
  ["Symbol('s')",          Symbol("s")],
  ["{}",                   {}],
  ["[]",                   []],
  ["function f(){}",       function f() {}],
  ["() => {}",             () => {}],
  ["class C {}",           class C {}],
  ["/re/",                 /re/],
  ["new Date(0)",          new Date(0)],
  ["new Number(42)",       new Number(42)],
  ["new String('abc')",    new String("abc")],
  ["Math",                 Math],
  ["JSON",                 JSON],
  ["new Map()",            new Map()],
  ["Object.create(null)",  Object.create(null)],
];

console.log("expr".padEnd(22) + "typeof".padEnd(12) + "Object.prototype.toString.call");
console.log("-".repeat(22) + "-".repeat(12) + "-".repeat(30));
for (const [label, v] of rows) {
  console.log(label.padEnd(22) + String(typeof v).padEnd(12) + tag(v));
}

console.log("");
console.log("typeof 가 돌려줄 수 있는 문자열은 이 여덟 가지뿐이다:");
console.log("  " + [...new Set(rows.map(([, v]) => typeof v))].sort().join(" "));
```

```text
===== node20 js01b-01a-typeof-grid.js (exit=0) =====
expr                  typeof      Object.prototype.toString.call
----------------------------------------------------------------
undefined             undefined   [object Undefined]
null                  object      [object Null]
true                  boolean     [object Boolean]
42                    number      [object Number]
NaN                   number      [object Number]
Infinity              number      [object Number]
10n                   bigint      [object BigInt]
"abc"                 string      [object String]
Symbol('s')           symbol      [object Symbol]
{}                    object      [object Object]
[]                    object      [object Array]
function f(){}        function    [object Function]
() => {}              function    [object Function]
class C {}            function    [object Function]
/re/                  object      [object RegExp]
new Date(0)           object      [object Date]
new Number(42)        object      [object Number]
new String('abc')     object      [object String]
Math                  object      [object Math]
JSON                  object      [object JSON]
new Map()             object      [object Map]
Object.create(null)   object      [object Object]

typeof 가 돌려줄 수 있는 문자열은 이 여덟 가지뿐이다:
  bigint boolean function number object string symbol undefined
```

그림 해설 (한 단계씩).

- ★★★ **`typeof null` 이 `"object"` 다.** 이것은 구현 버그가 아니라 **명세에 박힌 결과**다.
  초기 구현에서 값의 태그 비트가 `0` 인 것을 객체로 읽던 사정이 있었고, 고치면 기존 웹이 깨지므로 **명세가 그 동작을 그대로 못 박았다.**
  ★ **「버그처럼 보이는데 보장인 것」의 대표**다 — 다음 판에서 고쳐지지 않는다.
- ★★★ **함수만 `"function"` 을 받는다.** 함수는 `Object` 타입의 하나인데 `typeof` 만 따로 답한다.
  **화살표 함수도 클래스도 전부 `"function"`** 이다 — `class` 는 문법이 다를 뿐 함수다.
- ★★ **`typeof` 의 답은 여덟 가지로 닫혀 있다.** 위 출력의 마지막 줄이 그것을 센 것이다.
  새 원시 타입이 들어오면(가장 최근이 `bigint`) 그때 한 가지가 늘어난다.
- ★ **둘째 칸이 다른 창이다** — `Object.prototype.toString.call` 은 `null` 을 `[object Null]` 로, `Date` 를 `[object Date]` 로 갈라 준다.
  `typeof` 가 `"object"` 로 뭉갠 것을 여기서 풀 수 있다.
- ★ **`Object.create(null)` 도 `[object Object]` 다.** 프로토타입이 없어도 태그는 같다.

**비용** — `typeof` 는 **값을 읽지 않고 종류만** 보므로 부작용이 없고 어떤 값에도 안전하다.
대신 **`"object"` 라는 답이 너무 넓다** — `null`·배열·`Date`·`Map` 이 전부 같은 답을 받는다.

### (2) `typeof` 는 선언 안 된 이름에도 안 터진다 — 그런데 TDZ 는 못 넘는다

**언제 쓰나** — 전역에 무엇이 있는지 모르는 코드(라이브러리 감지·폴리필 분기).

```text
   이름의 세 가지 상태

   (A) 아예 선언이 없다            typeof -> "undefined"   그냥 읽기 -> ReferenceError
   (B) let/const 인데 아직 초기화 전  typeof -> ReferenceError  그냥 읽기 -> ReferenceError
   (C) 선언·초기화가 끝났다          typeof -> 그 값의 종류     그냥 읽기 -> 그 값

   ★ (A) 만이 typeof 의 특권이다. (B) 에는 그 특권이 없다.
     "typeof 는 절대 안 터진다" 는 (B) 에서 틀린다.
```

```js
// js01b-01b-typeof-undeclared.js
// typeof 가 ReferenceError 를 피해 가는 유일한 자리 — 그리고 그 예외의 예외.
function show(label, f) {
  let r;
  try { r = JSON.stringify(f()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log(label.padEnd(32) + " -> " + r);
}

console.log("[1] 선언조차 안 된 이름");
show("typeof neverDeclared", () => typeof neverDeclared);
show("neverDeclared", () => neverDeclared);

console.log("");
console.log("[2] let/const 의 TDZ 는 typeof 도 못 넘는다");
function tdzProbe() { const r = typeof tdzLet; let tdzLet = 1; return r; }
show("typeof tdzLet (TDZ)", tdzProbe);
function okProbe() { let x = 1; return typeof x; }
show("typeof x (initialized let)", okProbe);

console.log("");
console.log("[3] globalThis 에 묻는 것과 typeof 는 다른 질문이다");
show("'nope' in globalThis", () => "nope" in globalThis);
show("typeof nope", () => typeof nope);
show("globalThis.nope", () => globalThis.nope);
```

```text
===== node20 js01b-01b-typeof-undeclared.js (exit=0) =====
[1] 선언조차 안 된 이름
typeof neverDeclared             -> "undefined"
neverDeclared                    -> ReferenceError: neverDeclared is not defined

[2] let/const 의 TDZ 는 typeof 도 못 넘는다
typeof tdzLet (TDZ)              -> ReferenceError: Cannot access 'tdzLet' before initialization
typeof x (initialized let)       -> "number"

[3] globalThis 에 묻는 것과 typeof 는 다른 질문이다
'nope' in globalThis             -> false
typeof nope                      -> "undefined"
globalThis.nope                  -> undefined
```

그림 해설.

- ★★★ **`typeof neverDeclared` 는 `"undefined"` 를 주고, 같은 이름을 그냥 읽으면 `ReferenceError` 다.**
  **언어 전체에서 이 특권을 가진 연산자는 `typeof` 하나뿐**이다.
- ★★★ **그런데 TDZ 에서는 `typeof` 도 터진다.** 「선언이 없는 것」과 「선언은 있는데 아직 못 쓰는 것」은 다른 상태다.
  ★ TDZ 자체의 정본은 [목록의 **05번 주제**](../05-var-let-const-and-tdz/)다 — 여기서는 「`typeof` 의 특권에 구멍이 있다」는 사실만 본다.
- ★★ **`"nope" in globalThis` 는 `false` 인데 `typeof nope` 는 `"undefined"` 다.** 두 질문이 다르다 —
  앞엣것은 「전역 객체에 그 키가 있나」이고 뒤엣것은 「이 이름을 읽으면 무엇이 나오나」다.
- ★ `globalThis.nope` 는 그냥 `undefined` 를 준다. **객체의 없는 프로퍼티는 에러가 아니다.**

**비용** — 값이 있는지 **읽기 전에** 물을 수 있어서 방어 코드가 짧아진다.
대신 **오타를 잡아 주지 않는다** — `typeof usrename` 도 조용히 `"undefined"` 다.

### (3) 원시 값에 메서드를 부르면 — 없는 봉투가 잠깐 생겼다 사라진다

**언제 쓰나** — `"abc".length`·`(5).toFixed(2)` 처럼 **원시 값에 점을 찍는** 모든 자리.

```text
   "abc".toUpperCase() 가 실제로 하는 일

   "abc"              원시 문자열 (봉투 없음)
     |
     |  점을 찍는 순간
     v
   [ String 래퍼 ]    <- 임시 봉투가 생긴다
     |   toUpperCase 를 찾아 부른다
     v
   "ABC"              결과는 다시 원시 값
     |
     x                <- 임시 봉투는 버려진다

   ★ 그래서 s.mine = 1 을 해도 다음 줄에서 s.mine 은 undefined 다.
     매번 새 봉투가 생기고 매번 버려지기 때문이다.
```

```js
// js01b-01c-boxing.js
// 원시 값에 메서드를 부르면 무슨 일이 나는가 — 래퍼를 실제로 붙잡아 본다.
String.prototype.peek = function () {
  return { typeofThis: typeof this, isStringObject: this instanceof String,
           tag: Object.prototype.toString.call(this) };
};
Number.prototype.peekStrict = function () {
  "use strict";
  return { typeofThis: typeof this, isNumberObject: this instanceof Number };
};

const s = "abc";
console.log("[1] 원시 문자열에 메서드를 부르면 this 가 무엇인가");
console.log("  느슨한 모드 :", JSON.stringify(s.peek()));
console.log("  엄격 모드   :", JSON.stringify((42).peekStrict()));

console.log("");
console.log("[2] 래퍼는 그 호출 한 번만 살고 버려진다");
s.mine = 1;
console.log("  s.mine = 1 을 한 뒤 s.mine :", s.mine);
const boxed = new String("abc");
boxed.mine = 1;
console.log("  new String('abc') 는 남는다:", boxed.mine);

console.log("");
console.log("[3] 래퍼 객체는 원시 값과 다른 물건이다");
console.log("  'abc' === new String('abc')      :", "abc" === new String("abc"));
console.log("  'abc' ==  new String('abc')      :", "abc" == new String("abc"));
console.log("  typeof new String('abc')         :", typeof new String("abc"));
console.log("  Boolean(new Boolean(false))      :", Boolean(new Boolean(false)));
console.log("  new Boolean(false) ? 'T' : 'F'   :", new Boolean(false) ? "T" : "F");
console.log("  JSON.stringify(new Number(1))    :", JSON.stringify(new Number(1)));

console.log("");
console.log("[4] 래퍼가 없는 원시 값도 있다 — 부르면 바로 터진다");
for (const [label, f] of [
  ["(null).toString()", () => null.toString()],
  ["(undefined).toString()", () => undefined.toString()],
  ["(10n).toString()", () => (10n).toString()],
  ["Symbol('s').toString()", () => Symbol("s").toString()],
]) {
  let r; try { r = f(); } catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(26) + " -> " + r);
}
```

```text
===== node20 js01b-01c-boxing.js (exit=0) =====
[1] 원시 문자열에 메서드를 부르면 this 가 무엇인가
  느슨한 모드 : {"typeofThis":"object","isStringObject":true,"tag":"[object String]"}
  엄격 모드   : {"typeofThis":"number","isNumberObject":false}

[2] 래퍼는 그 호출 한 번만 살고 버려진다
  s.mine = 1 을 한 뒤 s.mine : undefined
  new String('abc') 는 남는다: 1

[3] 래퍼 객체는 원시 값과 다른 물건이다
  'abc' === new String('abc')      : false
  'abc' ==  new String('abc')      : true
  typeof new String('abc')         : object
  Boolean(new Boolean(false))      : true
  new Boolean(false) ? 'T' : 'F'   : T
  JSON.stringify(new Number(1))    : 1

[4] 래퍼가 없는 원시 값도 있다 — 부르면 바로 터진다
  (null).toString()          -> TypeError: Cannot read properties of null (reading 'toString')
  (undefined).toString()     -> TypeError: Cannot read properties of undefined (reading 'toString')
  (10n).toString()           -> 10
  Symbol('s').toString()     -> Symbol(s)
```

그림 해설.

- ★★★ **느슨한 모드에서는 메서드 안의 `this` 가 정말 객체다** — `typeof this` 가 `"object"` 이고 `this instanceof String` 이 `true` 다.
  **봉투가 실제로 만들어졌다는 관찰**이다. 「그런 것처럼 동작한다」가 아니다.
- ★★★ **엄격 모드에서는 안 만들어진다** — `typeof this` 가 `"number"` 다.
  ★ 그래서 **같은 코드가 모드에 따라 `this` 의 타입이 다르다.** 엄격 모드의 정본은 목록의 **35번 주제**다.
- ★★ **`s.mine = 1` 이 조용히 버려진다.** 느슨한 모드에서는 에러도 안 난다 — 새 봉투에 넣고 그 봉투를 버린다.
  `new String("abc")` 로 만든 **진짜 봉투**에는 남는다.
- ★★★ **래퍼 객체는 원시 값과 다른 물건이다.** `new Boolean(false)` 가 **truthy** 인 것이 그 결과다 —
  객체는 전부 truthy 이므로 `false` 를 담은 봉투도 참이다. **래퍼 생성자는 쓰지 마라.**
- ★ **`null` 과 `undefined` 에는 래퍼가 없다** — 점을 찍는 순간 `TypeError` 다.
  원시 값 일곱 중 **둘만** 그렇다.

**비용** — 래퍼 덕에 원시 값에도 메서드를 쓸 수 있고, 문법이 객체와 같아진다.
대신 **대입이 조용히 버려지고**, `new String` 같은 래퍼 객체가 섞여 들어오면 `===` 와 `if` 가 전부 어긋난다.

### (4) 여덟 번째 예외 — `document.all` 은 브라우저에서만 던져 볼 수 있다

**언제 쓰나** — 「`typeof` 의 답은 여덟 가지」라는 말이 어디서 깨지는지 알 때.

`document.all` 은 Node 에 없다. **브라우저로 던져야** 보인다.
호스트 페이지는 네 줄이고, 실제 검사는 옆의 `.js` 가 한다.

```text
<!doctype html><meta charset="utf-8"><title>document.all</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js01b-01d-browser.js"></script>
```

```js
// js01b-01d-browser.js
const rows = [
  ["typeof document.all",            typeof document.all],
  ["document.all === undefined",     document.all === undefined],
  ["document.all == undefined",      document.all == undefined],
  ["document.all == null",           document.all == null],
  ["Boolean(document.all)",          Boolean(document.all)],
  ["document.all ? 'T' : 'F'",       document.all ? "T" : "F"],
  ["Object.prototype.toString.call", Object.prototype.toString.call(document.all)],
  ["document.all.length",            document.all.length],
  ["document.all[1].tagName",        document.all[1].tagName],
  ["typeof document.body",           typeof document.body],
];
document.getElementById("out").textContent =
  rows.map(([k, v]) => k.padEnd(32) + " : " + String(v)).join("\n");
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --dump-dom js01b-01d-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">typeof document.all              : undefined
document.all === undefined       : false
document.all == undefined        : true
document.all == null             : true
Boolean(document.all)            : false
document.all ? 'T' : 'F'         : F
Object.prototype.toString.call   : [object HTMLAllCollection]
document.all.length              : 8
document.all[1].tagName          : HEAD
typeof document.body             : object</pre>
```

그림 해설.

- ★★★ **`typeof document.all` 이 `"undefined"` 인데 `document.all === undefined` 는 `false` 다.**
  객체이면서 `typeof` 가 `"undefined"` 를 답하는 **유일한 값**이다.
- ★★★ **`Object.prototype.toString.call` 은 `[object HTMLAllCollection]` 이라고 정직하게 답한다.**
  ★ **첫째 창(`typeof`)이 거짓말을 하고 둘째 창이 참말을 하는 자리**다 — 창이 둘 필요한 이유가 여기 있다.
- ★★ **`Boolean(document.all)` 이 `false` 다.** 객체인데 falsy 다 — 이것도 이 값 하나뿐이다.
- ★★ **`document.all == undefined` 는 `true`, `== null` 도 `true`** 다. 느슨한 비교까지 예외로 만들어 두었다.
- ★ **왜 이런 것이 명세에 있나** — 옛 IE 전용 코드가 `if (document.all)` 로 브라우저를 갈랐다.
  그 코드를 안 깨면서 `document.all` 을 표준 밖으로 밀어내려고 「**있는데 없는 척하는 값**」을 명세에 넣었다.
  ★★ ECMA-262 에 이 예외를 위한 **내부 표시**가 있고 `typeof`·`ToBoolean`·느슨한 비교 세 곳이 그것을 본다.
- ★ `document.all.length` 는 **페이지의 요소 수**라 흔들리는 칸이다. 근거로 쓰지 않는다.

**비용** — 20년 된 웹이 안 깨진다.
대신 **「`typeof` 의 답이 여덟 가지」라는 규칙에 구멍이 하나 뚫려 있고**, 그 구멍은 영원히 안 막힌다.

### (5) 두 판에서 돌려 보면 — 갈리는 자리가 없다

**언제 쓰나** — 「이게 이 판에서만 그런 건 아닐까」를 물을 때.

```sh
// js01b-vdiff.sh
#!/usr/bin/env bash
# 이 주제의 모든 스크립트를 두 판으로 돌려 한 글자라도 다른지 본다.
# 쓰는 법: ./js01b-vdiff.sh <주제번호>
set -u -o pipefail
N18=node                                        # v18.19.1 (기본 PATH)
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"  # v20.19.6 (nvm)
printf '%-34s %s\n' "script" "node v18.19.1 대 v20.19.6"
printf '%-34s %s\n' "----------------------------------" "-------------------------"
for f in js01b-"$1"*.js; do
  case "$f" in *-browser.js|*-forms.js) continue;; esac   # 브라우저용·형태만 모은 것은 뺀다
  a=$("$N18" "$f" 2>&1); b=$("$N20" "$f" 2>&1)
  if [ "$a" = "$b" ]; then printf '%-34s 같다 (한 글자도)\n' "$f"
  else printf '%-34s ★ 다르다 — 다른 줄 %s개\n' "$f" "$(diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | grep -c '^[<>]')"
  fi
done
```

```text
===== ./js01b-vdiff.sh 01 (exit=0) =====
script                             node v18.19.1 대 v20.19.6
---------------------------------- -------------------------
js01b-01a-typeof-grid.js           같다 (한 글자도)
js01b-01b-typeof-undeclared.js     같다 (한 글자도)
js01b-01c-boxing.js                같다 (한 글자도)
```

그림 해설.

- **세 스크립트 전부 한 글자도 같았다.** 값의 종류와 `typeof` 는 **판이 올라도 안 움직이는 층**이다.
- ★★ **그런데 「같았다」는 보장이 아니다.** 보장은 명세에서 오고 이것은 관찰이다.
  같은 것이 앞으로도 같으리라는 근거가 되지는 않는다 — 다만 **이 문서의 출력을 어느 판에서 읽어도 된다**는 뜻은 된다.
- ★ 이 배치 네 주제에서 **두 판이 갈린 자리는 딱 하나**였고 그것은 04번의 `isWellFormed` 다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js01b-01x-forms.js
// 형태만 모아 둔 파일 — 출력은 없다. `node --check` 로 문법만 확인한다.
const x = 42;

typeof x;                 // 문자열 하나를 돌려준다. 괄호는 필요 없다
typeof (1 + 2);           // 식에도 쓸 수 있다 — 우선순위 때문에 괄호가 필요할 때가 있다
typeof neverDeclared;     // ★ 선언이 없어도 안 터진다. 언어에서 이 자리 하나뿐

Object.prototype.toString.call(x);   // "[object Number]" — 둘째 창
Array.isArray(x);                    // 배열만 정확히 가른다
x === null;                          // null 은 이것으로만 가른다
x == null;                           // null 이거나 undefined (02번 주제)
typeof x === "function";             // 부를 수 있나

Boolean(x);               // 이것이 참·거짓으로 바꾸는 법
String(x);                // 이것이 문자열로 바꾸는 법
// new Boolean(x);        // ★ 쓰지 마라 — 객체가 되어 언제나 truthy 다
// new String(x);         // ★ 쓰지 마라 — 원시 값과 === 로 다르다
```

```text
===== node20 --check js01b-01x-forms.js (exit=0) =====

```

규칙은 일곱이다.

1. **값의 종류는 여덟**이다 — 원시 일곱(`undefined`·`null`·`boolean`·`number`·`string`·`symbol`·`bigint`)과 객체.
2. **`typeof` 의 답도 여덟 가지**인데 **1:1 이 아니다** — `null` 이 `"object"` 로, 함수가 `"function"` 으로 간다.
3. **`typeof` 는 선언 안 된 이름에 안 터진다.** 언어에서 그런 자리는 여기뿐이다. **TDZ 는 예외**다.
4. **원시 값에 점을 찍으면 임시 래퍼가 생긴다.** 느슨한 모드에서만 관찰되고, **엄격 모드에서는 안 생긴다.**
5. **`null` 과 `undefined` 에는 래퍼가 없다** — 점을 찍으면 `TypeError` 다.
6. **래퍼 객체는 전부 truthy** 다. `new Boolean(false)` 도 참이다.
7. **호스트가 만든 예외 하나**(`document.all`)가 `typeof`·`ToBoolean`·느슨한 비교 세 곳에서 규칙을 깬다.

## 어디서 틀리나

### (1) ★★★ `typeof x === "object"` 로 「객체인가」를 묻는다

**`null` 이 그 안으로 들어오고 함수가 그 밖으로 빠져나간다.** 한 줄에 두 사고가 같이 있다.
고치면 `x !== null && (typeof x === "object" || typeof x === "function")` 이다.

### (2) ★★ `typeof x === "undefined"` 로 「값이 없나」를 묻는다

**「선언 안 됨」·「`undefined`」·「`null`」이 서로 다른 세 상태**다. `typeof` 는 앞의 둘만 잡는다.
값이 비었는지만 물으려면 `x == null`(02번 주제)이 맞고, **이름의 존재**를 물을 때만 `typeof` 다.

### (3) ★★ `typeof` 가 절대 안 터진다고 믿는다

**TDZ 에서는 터진다.** 특권은 「선언이 아예 없는 이름」에만 있다.
`function f() { typeof v; let v = 1; }` 가 `ReferenceError` 다.

### (4) ★★★ 래퍼 생성자로 값을 만든다

`new Boolean(false)` 는 **객체라서 참**이다. `if` 가 통째로 뒤집힌다.
`new` 없이 `Boolean(x)`·`String(x)`·`Number(x)` 를 쓴다.

### (5) ★★ 원시 값에 프로퍼티를 넣고 남기를 기대한다

`s.tag = "x"` 뒤에 `s.tag` 가 `undefined` 다. **느슨한 모드에서는 에러도 안 난다.**
엄격 모드에서는 `TypeError` 가 난다 — **조용한 실패를 시끄럽게 바꾸는 것**이 엄격 모드의 일이다.

### (6) ★ 배열을 `typeof` 로 가리려 한다

`typeof []` 는 `"object"` 라 객체와 구분이 안 된다. `Array.isArray([])` 를 쓴다.
셋 중 무엇이 언제 깨지는지는 목록의 **34번 주제**가 정본이다.

### (7) ★ `typeof` 로 `NaN` 을 걸러낼 수 있다고 본다

`typeof NaN` 은 `"number"` 다. `Infinity` 도 `-0` 도 전부 `"number"` 다 — 03번 주제의 일이다.

### (8) ★★ 「함수는 객체가 아니다」로 외운다

**함수는 부를 수 있는 객체**다. `f.mine = 1` 이 들어가고 브랜드 태그는 `[object Function]` 이다.
`typeof` 만 따로 답할 뿐이다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「명세 보장」 칸이 압도적으로 두껍다** — JS 는 **이상해 보이는 동작까지 명세가 못 박은** 언어다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **명세(ECMA-262) 보장** | 어느 엔진에서도 같아야 하는 것 | 위 기준 소스를 열어서 + 실행으로 재확인 |
| **엔진(V8) 구현** | V8 이 그렇게 하는 것 | 실행 + 두 판 대조 |
| **이 판의 관찰** | node 20.19.6 / Chrome 151 에서 그랬을 뿐 | 「관찰」로 명기 |

### 명세 보장

| 사실 | 어떻게 확인했나 |
|---|---|
| 언어 타입은 **여덟**이고 그중 일곱이 원시다 | 기준 소스의 타입 목록 |
| **`typeof null` 이 `"object"`** 다 | `typeof` 결과표에 그렇게 적혀 있다 + 실행 |
| **`[[Call]]` 이 있는 객체만 `"function"`** 을 받는다 | 결과표 + 화살표·`class` 까지 던져 확인 |
| **`typeof` 는 선언 안 된 이름에 예외를 안 던진다** | `typeof` 의 평가 규칙 + 실행 |
| **TDZ 의 이름은 `typeof` 도 `ReferenceError`** 다 | 실행(`Cannot access 'tdzLet' before initialization`) |
| 원시 값에 프로퍼티를 읽으면 **임시 래퍼**가 만들어진다 | 메서드 안의 `this` 를 찍어 확인 |
| **엄격 모드에서는 래퍼를 안 만든다** | 같은 프로그램의 두 메서드를 비교 |
| **`null`·`undefined` 에는 래퍼가 없다** | `TypeError` 로 확인 |
| `document.all` 은 `typeof`·`ToBoolean`·느슨한 비교에서 **예외로 다뤄진다** | HTML 표준 + Chrome 151 실행 |

★ **마지막 줄만 ECMA-262 밖이다** — 규정은 HTML 표준이 하고 ECMA-262 는 그 예외를 받아 줄 자리만 둔다.

### 엔진(V8) 구현

| 사실 | 어떻게 확인했나 |
|---|---|
| Node 20.19.6 의 V8 은 **11.3.244.8**, Node 18.19.1 은 **10.2.154.26** | `process.versions.v8` |
| 이 주제의 세 스크립트가 **두 판에서 한 글자도 같았다** | `js01b-vdiff.sh 01` |
| Chrome 151 과 Node 20 이 **`typeof document.all` 을 빼고 같은 답**을 냈다 | 같은 식을 양쪽에서 던짐 |

### 이 판의 관찰 — 판이 오르면 다시 찍어야 하는 것

| 관찰 | 어디가 흔들리나 |
|---|---|
| `Cannot read properties of null (reading 'toString')` 같은 **문구** | 예외의 **종류**는 명세지만 문구는 아니다 |
| `document.all.length` 가 `8` 인 것 | **페이지의 요소 수**다. 근거로 쓰지 않는다 |
| UA 가 `Chrome/151.0.0.0` 인 것 | 브라우저가 **일부러 축약**한 값이다(실제 판은 `151.0.7922.173`) |
| `[object HTMLAllCollection]` 이라는 태그 | HTML 표준이 정하지만 **이름은 바뀔 수 있는 축**이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`typeof null` 은 JS 의 버그다」
  ○ **버그에서 출발했지만 지금은 명세**다. 고치면 웹이 깨져서 안 고친다.
- ✗ 「`typeof` 는 절대 예외를 안 던진다」
  ○ **TDZ 에서는 던진다.** 특권은 「선언이 없는 이름」에만 있다.
- ✗ 「함수는 객체가 아니다」
  ○ **부를 수 있는 객체**다. `typeof` 만 따로 답한다.
- ✗ 「원시 값에는 메서드가 없다」
  ○ **임시 래퍼가 만들어져** 있는 것처럼 쓸 수 있다. 엄격 모드에서는 래퍼 없이 프로토타입만 본다.
- ✗ 「`typeof` 의 답은 여덟 가지로 닫혀 있다」
  ○ **호스트가 뚫어 둔 구멍이 하나 있다** — `document.all` 이 객체인데 `"undefined"` 를 받는다.
- ✗ 「`Object.prototype.toString` 은 믿을 수 있는 타입 검사다」
  ○ **바꿀 수 있는 태그**다(`Symbol.toStringTag`). 34번 주제의 일이다.

**판정 기준 한 줄**: 어떤 코드가 **`typeof` 의 답 하나로 분기**하고 있으면, `null` 과 함수가 그 분기에서 어디로 가는지 세어 본다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `typeof x === "string"` 류 | **원시 값의 종류**를 물을 때 — 이것이 `typeof` 의 본업이다 |
| `typeof x === "function"` | **부를 수 있나**를 물을 때. 대안이 사실상 없다 |
| `typeof maybeGlobal !== "undefined"` | **선언 여부를 모르는 전역**을 볼 때(폴리필 분기) |
| `x === null` | `null` 을 가릴 때 — `typeof` 로는 안 된다 |
| `Array.isArray(x)` | 배열을 가릴 때 |
| `Object.prototype.toString.call(x)` | `typeof` 가 `"object"` 로 뭉갠 것을 **한 번 더 갈라** 볼 때 |
| `Boolean(x)` | 참·거짓으로 바꿀 때. **`new Boolean` 은 절대 안 된다** |

**안 쓰는 자리**는 셋이다.
**`typeof x === "object"` 로 「객체인가」를 묻지 마라** — `null` 이 들어오고 함수가 빠진다.
**`new String`·`new Number`·`new Boolean` 을 쓰지 마라** — 값이 아니라 봉투가 만들어진다.
**`typeof` 로 오타를 방어하지 마라** — 오타난 이름도 조용히 `"undefined"` 다.

## 핵심 문장

- **값의 종류는 여덟, `typeof` 의 답도 여덟 — 그런데 1:1 이 아니다.** 어긋난 칸이 이 주제의 전부다.
- **`typeof null` 이 `"object"` 인 것은 버그가 아니라 보장이다.** 다음 판에서도 그대로다.
- **함수는 부를 수 있는 객체**이고 `typeof` 만 따로 답한다.
- **`typeof` 는 선언 안 된 이름에 안 터지는 유일한 연산자**이고, **TDZ 에서는 그 특권이 없다.**
- **원시 값에 점을 찍으면 임시 래퍼가 생겼다 버려진다** — 엄격 모드에서는 그마저 안 생긴다.
- **창이 하나로는 모자란다.** `typeof` 가 `"object"` 라고 답한 자리에서는 `Object.prototype.toString.call` 이 둘째 창이다.
- **`document.all` 은 명세가 만든 거짓말**이다 — 객체인데 `typeof` 가 `"undefined"` 이고 falsy 다.

## 관련 자료

- 목록: [js/syntax 주제 목록](../README.md) — 이 주제는 **01번**
- 이어지는 곳: [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) — 여기서 갈라 둔 **종류들이 서로 섞일 때** 무슨 일이 나나.
- 이어지는 곳: [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md) — `"number"` 와 `"bigint"` 두 칸의 속사정.
- 이어지는 곳: [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) — `"string"` 한 칸의 속사정.
- 이어지는 곳: [목록의 **05번 주제**](../05-var-let-const-and-tdz/) 「`var`·`let`·`const` 와 TDZ」 — **TDZ 의 정본**이다. 여기서는 「`typeof` 의 특권에 구멍이 있다」까지만 본다.
- 이어지는 곳: 목록의 **34번 주제** 「타입 검사 관용구」 — `Array.isArray`·`instanceof`·브랜드 태그가 **어디서 깨지나**의 정본.
- 이어지는 곳: 목록의 **35번 주제** 「엄격 모드」 — 래퍼가 안 생기는 것과 **조용한 대입이 터지는 것**의 정본.
- 이어지는 곳: [목록의 **22번 주제**](../22-symbol-and-well-known-symbols/) 「`Symbol` 과 잘 알려진 심볼」 — `Symbol.toStringTag` 로 **브랜드 태그를 바꾸는** 자리.
- 경계 — 타입 표기: TypeScript 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **01번** [`01-what-ts-adds-and-erases`](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md).
  **그쪽은 「타입은 런타임에 안 남는다」까지, 여기는 「런타임에 남아 있는 것이 무엇인가」부터다.** `typeof` 는 남는 쪽이다.
- 경계 — 다른 언어의 같은 자리: [`python/syntax/01-object-and-name-binding`](../../../python/syntax/01-object-and-name-binding/2-summary.md) —
  파이썬은 **모든 것이 객체**라 이 주제의 절반이 성립하지 않는다.
- 연혁은 여기가 아니다: [`history/js/`](../../../../../../history/js/) — `bigint`·`symbol` 이 언제 들어왔나.

## 용어 풀이

- **원시 값(primitive)**: 값 그 자체인 것. 고칠 수 없고 이름에 넣으면 복사된다. `undefined`·`null`·`boolean`·`number`·`string`·`symbol`·`bigint` 일곱이다.
- **객체(object)**: 프로퍼티를 담는 것. 이름에는 **가리키는 쪽지**가 들어가므로 여럿이 한 객체를 공유할 수 있다.
- **`typeof`**: 값의 종류를 문자열로 답하는 연산자. 돌려줄 수 있는 문자열은 여덟 가지다.
- **TDZ (Temporal Dead Zone, 일시적 사각지대)**: `let`/`const` 가 선언되었지만 아직 초기화되지 않은 구간.
  이 구간의 이름은 읽어도 `typeof` 해도 `ReferenceError` 다.
- **임시 래퍼(wrapper)**: 원시 값에 프로퍼티를 읽을 때 잠깐 만들어지는 객체. `String`·`Number`·`Boolean`·`Symbol`·`BigInt` 다섯 종이 있다.
- **브랜드 태그(brand tag)**: `Object.prototype.toString.call(x)` 이 돌려주는 `[object Xxx]` 문자열. 내장 객체의 종류를 드러낸다.
- **falsy**: `if` 에서 거짓으로 취급되는 값. `undefined`·`null`·`false`·`0`·`-0`·`0n`·`NaN`·`""`, 그리고 `document.all` 이다.
- **`document.all`**: 옛 IE 가 만든 전역. 명세가 「**객체인데 `typeof` 가 `"undefined"` 이고 falsy**」 라는 예외로 못 박아 두었다.
- **호스트(host)**: 엔진을 감싸 실행 환경을 제공하는 쪽. 브라우저와 Node 가 각각 호스트다. `document` 는 브라우저 호스트의 것이다.

## 더 들어가면

- **`typeof` 의 답이 아홉 번째로 늘어난 적은 없다.** 마지막으로 늘어난 것이 `bigint`(ES2020)이고,
  그 전이 `symbol`(ES2015)이다. **새 원시 타입이 들어올 때만** 늘어난다.
- **`Symbol.toStringTag` 로 브랜드 태그를 바꿀 수 있다.** 그래서 `Object.prototype.toString` 도 「믿을 수 있는 검사」가 아니다 —
  둘째 창은 첫째 창보다 넓게 보지만 **여전히 속일 수 있다**(34번 주제).
- **`typeof` 는 프록시를 통과한다** — `new Proxy(function(){}, {})` 는 `"function"` 이고 `new Proxy({}, {})` 는 `"object"` 다.
  대상의 `[[Call]]` 유무를 그대로 따른다(45번 주제). 이 문서에서는 던지지 않았다.
- **엔진 안에서 값이 어떻게 담기는가**(포인터 태깅·Smi·NaN 박싱)는 **이 주제가 아니다.**
  그 층은 관찰할 방법이 표준에 없고, 관찰하더라도 **명세 보장이 아니다.**
- **`typeof` 와 `void 0`** — 옛 코드가 `undefined` 대신 `void 0` 을 쓰는 것은 옛날 `undefined` 가 **재대입 가능한 전역**이었기 때문이다.
  지금은 `undefined` 가 쓰기 불가라 그럴 필요가 없다. 이 문서에서는 던지지 않았다.
