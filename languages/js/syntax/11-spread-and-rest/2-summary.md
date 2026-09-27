# js/syntax/11 — 스프레드와 나머지: 「같은 점 셋이 자리마다 다른 일을 한다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `[...x]` 와 `{ ...x }` 는 **글자가 같고 결과 모양도 비슷한데 서로 다른 연산**을 부른다 —
> 앞엣것은 **이터레이터**를, 뒤엣것은 **프로퍼티 복사**를 부른다.
> **값만 봐서는 안 갈린다.** `Proxy` 트랩과 getter 에 로그를 심어야 그 차이가 출력으로 나온다.
> ② 전수 격자가 「무엇이 통하고 무엇이 터지나」를 담고, ④ 예외가 그 경계를 문구로 가른다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 스프레드 원소 · 객체 리터럴의 `CopyDataProperties` · 나머지 매개변수 · 인자 목록 평가
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — 객체 스프레드(ES2018)가 들어온 판을 가릴 때
> - [MDN — 스프레드 구문](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax) · [MDN — 나머지 매개변수](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/rest_parameters)
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
> ★★ **`SyntaxError` 는 `try`/`catch` 로 못 잡는다** — 그래서 문법 격자는 `new Function(소스)` 으로 컴파일만 해 본다.
> ★★ **`undefined` 를 `JSON.stringify` 로 찍지 않는다** — 배열 안에서는 `null` 로, 객체에서는 통째로 사라진다.
> ★★ **`padEnd` 격자의 라벨은 전부 ASCII 다.**
> ★ **이 주제에는 시각·로캘·난수가 닿는 칸이 하나도 없다.**
>
> **버전** — **배열·호출 자리의 스프레드와 나머지 매개변수는 ES2015**, **객체 자리의 스프레드와 객체 나머지는 ES2018** 이다.
> ★ 그래서 「점 셋」은 **한 번에 들어온 문법이 아니다** — 자리마다 판이 다르다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | `Proxy` 트랩과 getter 로 **배열 자리와 객체 자리가 서로 다른 연산을 부른다**는 것 |
> | ★★★ **② 전수 격자** | 세 자리 × 값 여러 종 — **무엇이 통하고 무엇이 조용히 빈 결과를 내나** |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `[...null]` 은 터지고 `{ ...null }` 은 안 터지는 경계 |
> | ★★ **동일성**(`===`) | 얕은 복사 — **한 겹만 새 객체**라는 것 |
> | ★★ **두 번 컴파일**(그대로 / `"use strict";` 붙여) | **설정에 달린 칸이 몇 개인가** — 이 주제에서는 **0** 이었다 |
> | ★ **③ 브랜드 태그** | 나머지가 `Array` 냐 `Object` 냐(보조) |
> | ★ **⑤ 두 판 대조기 + 브라우저** | 판이 갈린 칸 · 호스트가 정하는 칸이 있나 |
> | ★ **부적용 — ⑥ `toFixed(20)`** · **⑦ `\uXXXX` 펼치기** | 부동소수점·인코딩이 닿는 칸이 없다. **잴 것이 없다** |
> | ★ **부적용 — 성능 측정** | 「스프레드가 느리다」는 **재지 않았다.** 이 문서에 속도 주장이 한 줄도 없다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **트랩 호출 순서와 이름** |
> | 예외 **문구**(판이 오르면 바뀐다 — **이 주제에서 실제로 바뀌었다**) | ★★★ **예외의 종류** · 결과 객체의 키 목록 |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **동일성 판정** · 디스크립터의 모양 |
>
> ★★★ **이 주제는 두 판이 갈린 블록을 하나 갖고 있다** — `f(...obj)` 의 예외 문구다.
> v18 은 `Found non-callable @@iterator`, v20 은 `Spread syntax requires ...iterable[Symbol.iterator] to be a function` 이다.
> **종류는 둘 다 `TypeError`** 다. **갈린 블록은 양쪽을 다 싣는다.**
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 61블록 전부 동일).
>
> **선행** — [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) · [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md).
> ★★★ **10번이 「모양으로 뜯는 쪽」이었다면 여기는 「모양으로 펴는 쪽」이다.** 두 패턴이 서로 다른 문을 쓴다는 결론이 여기서도 그대로 되풀이된다.
> ★ **09번의 `apply` 를 스프레드가 대신한다** — 다만 **서로 못 덮는 자리를 하나씩** 갖는다는 것도 거기서 봤다.
> **이어지는 곳** — [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/) 「이터러블 프로토콜과 `for...of`」 · [목록의 **27번 주제**](../27-object-static-methods/) 「`Object` 정적 메서드」 · [목록의 **48번 주제**](../48-deep-copy-methods-compared/) 「깊은 복사 수단 비교」
>
> ★★ **경계 — 깊은 복사 수단 비교는 48번이 정본이다.** 여기서는 **스프레드가 얕다**는 사실과 그 결과까지다.
> ★★ **경계 — `Object.assign` 의 API 세부는 27번이 정본이다.** 여기서는 **스프레드와 갈리는 한 자리**(setter)만 본다.
> ★★ **경계 — 이터러블 프로토콜의 계약은 19번이 정본이다.** 여기서는 **배열 자리가 그것을 쓴다**는 사실까지다.

## 한눈에 — 쉽게 말하면

**점 셋은 「봉투를 뜯어 쏟는 것」과 「쏟아진 것을 봉투에 쓸어 담는 것」 두 일을 한다.**
어느 쪽인지는 **점 셋이 어디에 서 있느냐**가 정한다.

- **값이 오는 자리에 서면 펴는 것**(스프레드) — 배열 리터럴 안, 객체 리터럴 안, 호출 인자 자리.
- **받는 자리에 서면 모으는 것**(나머지) — 매개변수 목록, 배열 패턴, 객체 패턴.
- ★★★ 그런데 **펴는 세 자리가 서로 다른 규칙**을 쓴다. 이것이 이 주제의 전부다.

```text
   펴는 자리 셋

   [ ...x ]        이터레이터를 돌린다      -> Set·문자열·Map 이 된다. 일반 객체는 TypeError
   f( ...x )       이터레이터를 돌린다      -> 배열 자리와 같은 규칙
   { ...x }        프로퍼티를 복사한다      -> 일반 객체·문자열·배열이 된다. null 도 조용히 {}

   ★ 같은 점 셋인데 { } 안에서만 다른 문을 쓴다.
   ★ 그래서 [...null] 은 터지고 { ...null } 은 안 터진다.
```

```text
   모으는 자리 셋 -- 전부 마지막이어야 한다

   function f(a, ...rest)     남은 인자를 진짜 배열로
   const [a, ...rest] = arr   남은 원소를 진짜 배열로
   const { a, ...rest } = obj 남은 프로퍼티를 평범한 객체로

   ★ 모으는 자리는 기본값을 못 갖는다. 꼬리 쉼표도 못 쓴다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 봉투를 뜯어 쏟는다 | 스프레드(값 자리) | 결과에 원소가 늘어난다 |
| 쓸어 담는다 | 나머지(받는 자리) | 반드시 마지막이고 배열·객체가 된다 |
| 줄을 세워 꺼낸다 | 배열·호출 자리의 이터레이터 | 순서가 있고 `Set` 도 된다 |
| 이름표를 베껴 적는다 | 객체 자리의 프로퍼티 복사 | 키가 그대로 오고 순서는 키 순서 |
| 겉봉만 새것 | 얕은 복사 | 안쪽 객체는 `===` 가 `true` |
| 사진을 찍어 붙인다 | getter 가 값으로 굳는 것 | 복사본의 디스크립터에 `value` 가 있다 |
| 나중에 적은 것이 이긴다 | 객체 스프레드의 순서 | `{ ...o, a: 9 }` 와 `{ a: 9, ...o }` |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
`setState({ ...state, ...patch })` 로 병합했는데 **중첩 객체가 통째로 갈아치워지는** 사고가 그것이고,
`{ ...instance }` 로 복사한 객체에서 **메서드가 사라지는** 사고가 그것이다.

## 이 주제가 답하려는 질문

1. ★★★ **세 자리가 정말 다른가** — 다르다면 **무엇을 부르는지**로 증명할 수 있나?
2. ★★★ **얕은 복사라는 사실이 중첩 구조에서 무엇을 만드나** — 그리고 복사에서 **빠지는 것은 무엇인가**?
3. ★★ **어느 형태가 `SyntaxError` 이고 어느 형태가 조용히 빈 결과를 내나**?

## 동작 방식

### (1) ★★ 세 자리 — 같은 값을 세 자리에 넣어 본다

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

```text
===== node20 js08b-11a-three-places.js (exit=0) =====
[1] spread -- three places, three different rules
  [...arr]                                 -> [1,2]
  [0, ...arr, 3]                           -> [0,1,2,3]
  [...'ab']                                -> ["a","b"]
  [...new Set([1, 1, 2])]                  -> [1,2]
  [...new Map([['k', 1]])]                 -> [["k",1]]
  [...obj]                                 -> TypeError: objSrc is not iterable
  { ...obj }                               -> {"a":1,"b":2}
  { ...arr }                               -> {"0":1,"1":2}
  { ...'ab' }                              -> {"0":"a","1":"b"}
  { ...new Set([1, 2]) }                   -> {}
  { ...7 }                                 -> {}
  { ...null }                              -> {}
  { ...undefined }                         -> {}
  [...null]                                -> TypeError: null is not iterable
  f(...arr)                                -> [1,2]
  f(...'ab')                               -> ["a","b"]
  f(...obj)                                -> TypeError: Spread syntax requires ...iterable[Symbol.iterator] to be a function

[2] later wins -- object spread is just property copying in order
  { ...obj, a: 9 }                         -> {"a":9,"b":2}
  { a: 9, ...obj }                         -> {"a":1,"b":2}
  { ...{ a: 1 }, ...{ a: 2 } }             -> {"a":2}
  { ...obj, ...{ b: undefined } }          -> {"a":1,"b":"<undefined>"}
  array spread does not merge              -> [1,2,2,3]

[3] rest -- three places, always the last one
  function (a, ...r) with (1, 2, 3)        -> [1,[2,3]]
  const [a, ...r] = [1, 2, 3]              -> [1,[2,3]]
  const { a, ...r } = { a: 1, b: 2 }       -> [1,{"b":2}]
  rest of an array pattern is an Array     -> true
  rest of an object pattern is an Object   -> [object Object]
  rest param is an Array                   -> true

[4] which form each place accepts -- SyntaxError or not
  form                                    sloppy  strict
  [...a, b]  spread not last              ok      ok
  [a, ...b] = arr  rest not last          ERR     ERR
  function f(...r, b)                     ERR     ERR
  function f(...r = [])                   ERR     ERR
  const [...r = []] = []                  ERR     ERR
  const { ...r, a } = {}                  ERR     ERR
  const { a, ...r } = {}                  ok      ok
  const [...r,] = []  trailing comma      ERR     ERR
  [...a,]  spread then comma              ok      ok
  f(...a,)  call trailing comma           ok      ok
  const { ...{ a } } = {}                 ERR     ERR
  const [...[a, b]] = [1, 2]              ok      ok
  settings-dependent cells                0 of 12

[5] the messages behind the ERR cells
  [a, ...b] = arr  rest not last          SyntaxError: Rest element must be last element
  function f(...r, b)                     SyntaxError: Rest parameter must be last formal parameter
  function f(...r = [])                   SyntaxError: Rest parameter may not have a default initializer
  const [...r = []] = []                  SyntaxError: Invalid destructuring assignment target
  const { ...r, a } = {}                  SyntaxError: Rest element must be last element
  const [...r,] = []  trailing comma      SyntaxError: Rest element must be last element
  const { ...{ a } } = {}                 SyntaxError: `...` must be followed by an identifier in declaration contexts
```

- ★★★ **`{ ...null }` 은 안 터지고 `[...null]` 은 터진다.** 이 한 쌍이 세 자리의 차이를 가장 짧게 보인다.
  객체 자리는 **복사할 프로퍼티가 없으면 빈 객체**를 만들고, 배열 자리는 **이터러블이 아니면 거부**한다.
  ★ `{ ...7 }` 도 `{ ...undefined }` 도 전부 `{}` 다 — **객체 자리는 아무것도 거부하지 않는다.**
- ★★★ **`{ ...new Set([1, 2]) }` 이 `{}` 다.** `Set` 은 원소를 **프로퍼티로 갖고 있지 않기** 때문이다.
  ★★ **에러가 안 난다.** 09번의 `apply(t, new Set(...))` 과 **같은 모양의 조용한 실패**다 —
  「이터러블이니까 되겠지」가 **자리를 잘못 고른 것**이다.
- ★★ **호출 자리는 배열 자리와 같은 규칙**이다. `f(...obj)` 가 `TypeError` 다.
  ★★★ **이 줄이 두 판에서 갈렸다** — 문구만 갈렸고 종류는 같다. 아래 (5)에서 양쪽을 싣는다.
- ★★ **객체 스프레드는 「순서대로 복사」일 뿐**이다. `{ ...obj, a: 9 }` 는 `a` 가 `9` 이고
  `{ a: 9, ...obj }` 는 `a` 가 `1` 이다 — **나중에 적은 것이 이긴다.**
  ★ **`undefined` 도 값이라 덮어쓴다** — `{ ...obj, ...{ b: undefined } }` 의 `b` 가 `undefined` 다.
  ★ **배열 스프레드는 병합이 아니다** — 중복이 그대로 남는다.
- ★★ **모으는 자리 셋은 타입이 다르다** — 매개변수와 배열 패턴의 나머지는 **진짜 배열**,
  객체 패턴의 나머지는 **평범한 객체**다.
- ★★★ **문법 격자 12형태 중 설정에 달린 칸은 0개**다. 08\~10번은 각각 1/9·7/12·7/20·15/24·2/12 였는데
  **여기서는 엄격·비엄격이 한 칸도 안 갈린다** — 점 셋의 규칙은 **모드와 완전히 무관**하다.
  ★ 「설정에 달린 칸이 몇 개인가」를 고정 행으로 두면 **0도 결론**이 된다.
- ★★ **그 격자가 「스프레드는 자유롭고 나머지는 마지막」을 보인다.**
  `[...a, b]` 는 되지만 `[a, ...b, c] = arr` 은 안 된다 — **같은 대괄호인데 펴는 쪽과 모으는 쪽의 규칙이 다르다.**
  ★ `const { ...{ a } } = {}` 도 안 된다 — **선언 자리의 나머지는 이름이어야 한다.**
  ★ `const [...[a, b]] = [1, 2]` 는 **된다** — 그쪽은 선언이 아니라 패턴이 한 겹 더 있는 것이다.

### (2) ★★★ 로그를 심어 보면 — 세 자리가 다른 연산을 부른다

**이 주제의 본체가 이 블록이다.** 값만 봐서는 안 갈리는 것을 트랩이 갈라 준다.

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

```text
===== node20 js08b-11b-traps.js (exit=0) =====
[1] object spread -- ownKeys, then a descriptor and a get per key
  { ...traced(2 keys) }         ["ownKeys","getOwnPropertyDescriptor a","get a","getOwnPropertyDescriptor b","get b"]
  { ...traced(0 keys) }         ["ownKeys"]
  Object.assign({}, traced)     ["ownKeys","getOwnPropertyDescriptor a","get a"]
  const { ...r } = traced       ["ownKeys","getOwnPropertyDescriptor a","get a"]
  const { a, ...r } = traced    ["get a","ownKeys","getOwnPropertyDescriptor b","get b"]

[2] array spread -- the iterator protocol, and nothing else
  [...tracedIterable(2)]        ["read Symbol.iterator","next 0","next 1","next 2"]
  [0, ...it(1), 9]              ["read Symbol.iterator","next 0","next 1"]
  f(...it(2))                   ["read Symbol.iterator","next 0","next 1","next 2"]
  { ...it(2) }  object place    ["read Symbol.iterator"]
  new Set([...it(1)])           ["read Symbol.iterator","next 0","next 1"]

[3] a getter is called once and its value is stored -- the getter itself is not copied
  source read twice             [2,3]
  copy read twice               [1,1]
  descriptor in the source      ["get","set","enumerable","configurable"]
  descriptor in the copy        {"value":1,"writable":true,"enumerable":true,"configurable":true}
  getter calls so far           3

[4] a setter in the target is skipped by spread but not by assign
  { ...sink, k: 1 } -> k is         1
  setter calls after spread         0
  setter calls after Object.assign  1
  spread target descriptor          ["value","writable","enumerable","configurable"]
```

```text
   { ...traced({ a: 1, b: 2 }) }
     -> ownKeys, getOwnPropertyDescriptor a, get a, getOwnPropertyDescriptor b, get b

   [ ...tracedIterable([1, 2]) ]
     -> read Symbol.iterator, next 0, next 1, next 2

   { ...tracedIterable([1, 2]) }
     -> read Symbol.iterator            <- 그것을 「프로퍼티로」 읽었을 뿐이다

   ★ 마지막 줄이 증명이다. 객체 자리는 Symbol.iterator 를 「부르지 않고 베낀다」.
```

- ★★★ **객체 자리는 `ownKeys` 한 번 + 키마다 `getOwnPropertyDescriptor` 와 `get` 한 번씩**을 부른다.
  ★ **디스크립터를 먼저 보는 이유**는 「열거 가능한가」를 가려야 하기 때문이다 — 그래서 비열거 프로퍼티는 안 온다.
  ★ **빈 객체면 `ownKeys` 만** 부른다.
- ★★★ **배열 자리는 `Symbol.iterator` 를 읽어 부르고 `next` 를 `done` 까지 돌린다.** 그게 전부다.
  `ownKeys` 도 `get` 도 안 부른다.
  ★ **호출 자리도 똑같다** — `f(...it(2))` 의 로그가 `[...it(2)]` 와 한 글자도 같다.
- ★★★ **같은 이터러블을 객체 자리에 넣으면 `read Symbol.iterator` 한 줄로 끝난다.**
  **그 키를 프로퍼티로 베꼈을 뿐** 부르지 않았다.
  ★★ **이것이 「세 자리가 다르다」의 결정적 증거**다 — 값으로는 `{}` 하나만 보이고 이유가 안 보인다.
- ★★★ **getter 는 한 번 불려 값으로 굳는다.** 원본은 읽을 때마다 늘어나는데(`[2,3]`)
  복사본은 **항상 같은 값**(`[1,1]`)이고, 디스크립터가 `get`/`set` 에서 **`value`/`writable`** 로 바뀌었다.
  ★ 10번의 객체 나머지와 **정확히 같은 규칙**이다.
- ★★★ **대상 쪽 setter 는 스프레드가 건너뛴다.** `{ ...sink, k: 1 }` 에서 setter 호출이 **0회**이고,
  같은 대상에 `Object.assign` 을 하면 **1회**다.
  ★★ **스프레드는 「프로퍼티를 정의」하고 `Object.assign` 은 「프로퍼티에 대입」한다.**
  결과가 거의 같아 보여서 **이 한 자리에서만 갈린다.** 정본은 [목록의 **27번 주제**](../27-object-static-methods/)다.

### (3) ★★ 얕은 복사 — 무엇이 복사되고 무엇이 남나

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

```text
===== node20 js08b-11c-shallow.js (exit=0) =====
[1] one level deep is copied, the rest is shared
  original after editing the copy         {"n":1,"inner":{"deep":99},"list":[1,2,3]}
  copy                                    {"n":99,"inner":{"deep":99},"list":[1,2,3]}
  copy.inner === original.inner           true
  copy.list === original.list             true
  array spread, same story                [{"deep":99}]
  arrCopy[0] === arrOrig[0]               true

[2] what a spread copy loses
  instance own keys                       ["x","own"]
  copy own keys                           ["x","own"]
  p instanceof Point                      true
  pc instanceof Point                     false
  p.double (prototype getter)             6
  pc.double                               undefined
  typeof pc.kind                          undefined
  non-enumerable 'hidden' copied?         false
  symbol key copied?                      true
  prototype of the copy                   true

[3] arrays -- spread reads the iterator, so holes and extra keys change shape
  sparse array                            [1,null,3]
  1 in sparse (hole present?)             false
  [...sparse]                             [1,null,3]
  1 in [...sparse]                        true
  [...sparse].length                      3
  extra key survived?                     false
  Array.from(sparse)                      [1,null,3]
  sparse.slice() keeps the hole           false
  { ...sparse } (object place)            {"0":1,"2":3,"tag":"extra"}

[4] merging -- what each form does with the same two objects
  { ...base, ...patch }                   {"a":1,"inner":{"deep":2},"b":2}
  Object.assign({}, base, patch)          {"a":1,"inner":{"deep":2},"b":2}
  nested object is replaced, not merged   {"deep":2}
  [...listBase, ...listPatch]             [1,2,3]
  [listBase, listPatch] (no spread)       [[1,2],[3]]
  [...listBase].concat is the same        [1,2,3]
```

```text
   const copy = { ...original };

     copy.n = 99          -> 원본 안 바뀜      (한 겹은 새것)
     copy.inner.deep = 99 -> 원본 바뀜         (안쪽은 같은 객체)
     copy.list.push(3)    -> 원본 바뀜

   ★ 「복사했다」가 아니라 「한 겹만 복사했다」다.
```

- ★★★ **한 겹만 새것이다.** `copy.inner === original.inner` 가 `true` 다. 배열 스프레드도 똑같다.
- ★★★ **클래스 인스턴스를 스프레드하면 네 가지를 잃는다** —
  **프로토타입**(`instanceof` 가 `false`) · **메서드**(`typeof pc.kind` 가 `undefined`) ·
  **프로토타입의 getter**(`pc.double` 이 `undefined`) · **비열거 프로퍼티.**
  ★ **심볼 키는 온다.** 복사본의 프로토타입은 **`Object.prototype`** 이다 — 평범한 객체가 된다.
  ★★ 그래서 **「객체를 복사한다」로 쓰면 도메인 객체가 조용히 평범한 자료 덩어리가 된다.**
- ★★★ **배열 스프레드는 구멍을 메운다.** `[1, , 3]` 은 `1 in sparse` 가 `false` 인데
  `[...sparse]` 는 `1 in` 이 **`true`** 다 — **이터레이터가 구멍 자리에서 `undefined` 를 내주기 때문**이다.
  ★ **`slice()` 는 구멍을 유지한다.** 같은 「복사」인데 결과가 다르다.
  ★ **배열의 여분 프로퍼티(`arr.tag`)는 안 온다** — 이터레이터는 원소만 낸다.
  ★ **같은 희소 배열을 객체 자리에 넣으면** 구멍이 **키째 빠지고** `tag` 는 **온다**(`{"0":1,"2":3,"tag":"extra"}`).
  ★★ **한 값에 두 자리를 대면 서로 다른 답이 나온다** — 10번의 `[4]` 와 같은 모양의 증거다.
- ★★ **병합에서 중첩은 병합되지 않고 갈아치워진다.** `{ ...base, ...patch }` 의 `inner` 가 `{deep:2}` 다.
  ★ `Object.assign` 도 같다. **깊은 병합은 둘 다 안 해 준다.**

### (4) ★★ 두 판에서 돌려 보면 — 갈린 칸이 하나 있다

```text
===== ./js08b-vdiff.sh 11 (exit=0) =====
  DIFFERENT js08b-11a-three-places.js
      18c18
      <   f(...obj)                                -> TypeError: Found non-callable @@iterator
      ---
      >   f(...obj)                                -> TypeError: Spread syntax requires ...iterable[Symbol.iterator] to be a function
  same      js08b-11b-traps.js
  same      js08b-11c-shallow.js
  ----
  identical on node18 and node20: 2   different: 1
```

- ★★ **세 스크립트 중 둘이 두 판에서 한 글자도 같았고, 하나가 갈렸다.**
  갈린 것은 **값이 아니라 예외 문구**다.
- ★★ **그래서 v18 쪽도 같이 싣는다.**

```text
===== node18 js08b-11a-three-places.js (exit=0) =====
[1] spread -- three places, three different rules
  [...arr]                                 -> [1,2]
  [0, ...arr, 3]                           -> [0,1,2,3]
  [...'ab']                                -> ["a","b"]
  [...new Set([1, 1, 2])]                  -> [1,2]
  [...new Map([['k', 1]])]                 -> [["k",1]]
  [...obj]                                 -> TypeError: objSrc is not iterable
  { ...obj }                               -> {"a":1,"b":2}
  { ...arr }                               -> {"0":1,"1":2}
  { ...'ab' }                              -> {"0":"a","1":"b"}
  { ...new Set([1, 2]) }                   -> {}
  { ...7 }                                 -> {}
  { ...null }                              -> {}
  { ...undefined }                         -> {}
  [...null]                                -> TypeError: null is not iterable
  f(...arr)                                -> [1,2]
  f(...'ab')                               -> ["a","b"]
  f(...obj)                                -> TypeError: Found non-callable @@iterator

[2] later wins -- object spread is just property copying in order
  { ...obj, a: 9 }                         -> {"a":9,"b":2}
  { a: 9, ...obj }                         -> {"a":1,"b":2}
  { ...{ a: 1 }, ...{ a: 2 } }             -> {"a":2}
  { ...obj, ...{ b: undefined } }          -> {"a":1,"b":"<undefined>"}
  array spread does not merge              -> [1,2,2,3]

[3] rest -- three places, always the last one
  function (a, ...r) with (1, 2, 3)        -> [1,[2,3]]
  const [a, ...r] = [1, 2, 3]              -> [1,[2,3]]
  const { a, ...r } = { a: 1, b: 2 }       -> [1,{"b":2}]
  rest of an array pattern is an Array     -> true
  rest of an object pattern is an Object   -> [object Object]
  rest param is an Array                   -> true

[4] which form each place accepts -- SyntaxError or not
  form                                    sloppy  strict
  [...a, b]  spread not last              ok      ok
  [a, ...b] = arr  rest not last          ERR     ERR
  function f(...r, b)                     ERR     ERR
  function f(...r = [])                   ERR     ERR
  const [...r = []] = []                  ERR     ERR
  const { ...r, a } = {}                  ERR     ERR
  const { a, ...r } = {}                  ok      ok
  const [...r,] = []  trailing comma      ERR     ERR
  [...a,]  spread then comma              ok      ok
  f(...a,)  call trailing comma           ok      ok
  const { ...{ a } } = {}                 ERR     ERR
  const [...[a, b]] = [1, 2]              ok      ok
  settings-dependent cells                0 of 12

[5] the messages behind the ERR cells
  [a, ...b] = arr  rest not last          SyntaxError: Rest element must be last element
  function f(...r, b)                     SyntaxError: Rest parameter must be last formal parameter
  function f(...r = [])                   SyntaxError: Rest parameter may not have a default initializer
  const [...r = []] = []                  SyntaxError: Invalid destructuring assignment target
  const { ...r, a } = {}                  SyntaxError: Rest element must be last element
  const [...r,] = []  trailing comma      SyntaxError: Rest element must be last element
  const { ...{ a } } = {}                 SyntaxError: `...` must be followed by an identifier in declaration contexts
```

- ★★★ **종류는 둘 다 `TypeError`** 이고 **바뀐 것은 말하는 방식**뿐이다.
  v20 쪽이 **무엇을 기대했는지를 말해 준다**(`requires ...iterable[Symbol.iterator] to be a function`).
  ★ **근거로 쓰는 것은 종류이고 문구가 아니다** — 머리말의 「흔들리는 칸」 표가 그것을 미리 선언해 둔 것이다.
  ★★ 08번에서도 같은 일이 있었다 — **두 배치에서 각각 한 건씩, 둘 다 예외 문구**였다.

### (5) ★★ 같은 질문을 브라우저에 던지면

```js
// js08b-11h-browser.js
// 같은 질문을 브라우저에 던진다 -- 스프레드의 세 자리에 호스트가 정하는 칸이 있나.
const lines = [];
function row(k, v) { lines.push("  " + k.padEnd(36) + v); }
function attempt(label, run) {
  try { row(label, String(run())); }
  catch (e) { row(label, e.constructor.name + ": " + e.message); }
}
const J = JSON.stringify;
row("engine", navigator.userAgent.replace(/^.*(Chrome\/[0-9.]+).*$/, "$1"));
attempt("{ ...null }", () => J({ ...null }));
attempt("[...null]", () => J([...null]));
attempt("{ ...7 }", () => J({ ...7 }));
attempt("{ ...'ab' }", () => J({ ..."ab" }));
attempt("{ ...new Set([1, 2]) }", () => J({ ...new Set([1, 2]) }));
attempt("[...new Set([1, 1, 2])]", () => J([...new Set([1, 1, 2])]));
attempt("[...{ length: 1 }]", () => J([...{ length: 1 }]));
attempt("object spread trap order", () => {
  const log = [];
  const t = new Proxy({ a: 1 }, {
    ownKeys(x) { log.push("ownKeys"); return Reflect.ownKeys(x); },
    getOwnPropertyDescriptor(x, k) { log.push("gopd " + String(k)); return Reflect.getOwnPropertyDescriptor(x, k); },
    get(x, k, r) { log.push("get " + String(k)); return Reflect.get(x, k, r); },
  });
  void { ...t };
  return log.join(",");
});
attempt("getter becomes a value", () => {
  const src = { get live() { return 1; } };
  return J(Object.getOwnPropertyDescriptor({ ...src }, "live"));
});
attempt("spread copy loses the prototype", () => {
  class P { constructor() { this.x = 1; } m() { return 1; } }
  return String({ ...new P() } instanceof P) + "," + typeof { ...new P() }.m;
});
attempt("hole becomes a slot", () => {
  const sparse = [1, , 3];
  return String(1 in sparse) + " then " + String(1 in [...sparse]);
});
attempt("f(...r, b) compiles?", () => { new Function("function f(...r, b) {}"); return "ok"; });
document.documentElement.appendChild(document.createElement("pre")).textContent =
  "===OUT===" + String.fromCharCode(10) + lines.join(String.fromCharCode(10)) + String.fromCharCode(10) + "===END===";
```

호스트 페이지는 이 네 줄이 전부다.

```text
<!doctype html>
<meta charset="utf-8">
<title>js08b 11</title>
<script src="js08b-11h-browser.js"></script>
```

```text
===== google-chrome --headless --dump-dom page11.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' (exit=0) =====
  engine                              Chrome/151.0.0.0
  { ...null }                         {}
  [...null]                           TypeError: null is not iterable
  { ...7 }                            {}
  { ...'ab' }                         {"0":"a","1":"b"}
  { ...new Set([1, 2]) }              {}
  [...new Set([1, 1, 2])]             [1,2]
  [...{ length: 1 }]                  TypeError: {(intermediate value)} is not iterable
  object spread trap order            ownKeys,gopd a,get a
  getter becomes a value              {"value":1,"writable":true,"enumerable":true,"configurable":true}
  spread copy loses the prototype     false,undefined
  hole becomes a slot                 false then true
  f(...r, b) compiles?                SyntaxError: Rest parameter must be last formal parameter
```

- ★★★ **호스트가 정하는 칸이 하나도 없었다.** 열세 줄이 Node 쪽과 전부 같다.
  ★★ **예외 문구까지 같다** — 다만 그것은 **둘 다 V8 이기 때문**이다. Chrome 151 은 v20 쪽 문구를 쓴다.
  ★ 같은 줄이 **Node 18 에서는 다른 문구**였다는 것이 그 증거다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js08b-11x-forms.js
// 형태만 모아 둔 파일 -- 출력은 없다. `node --check` 로 문법만 확인한다.
const arr = [1, 2];
const obj = { a: 1 };

const copied = [...arr];                 // 배열 리터럴 -- 이터레이터를 돈다
const joined = [0, ...arr, 9];           // 앞뒤 어디에나 올 수 있다
const fromString = [..."ab"];            // 문자열도 이터러블이다
const fromSet = [...new Set(arr)];       // Set·Map 도 이터러블이다

const merged = { ...obj, b: 2 };         // 객체 리터럴 -- 프로퍼티를 복사한다 (ES2018)
const overridden = { ...obj, a: 9 };     // 뒤엣것이 이긴다
const fromArr = { ...arr };              // 인덱스가 키가 된다
const fromNull = { ...null };            // 터지지 않는다. 빈 객체다

function sum(a, b) { return a + b; }
sum(...arr);                             // 호출 인자 -- 이터레이터를 돈다
Math.max(...arr);                        // apply 를 대신한다 (09번 주제)

function collect(a, ...rest) { return [a, rest]; }   // 나머지 매개변수 -- 진짜 배열
const [h, ...t] = arr;                               // 배열 패턴의 나머지
const { a: kept, ...others } = { a: 1, b: 2 };       // 객체 패턴의 나머지 (10번 주제)

const nested = { inner: { deep: 1 } };
const shallow = { ...nested };           // 얕다 -- shallow.inner 는 같은 객체다
void [copied, joined, fromString, fromSet, merged, overridden, fromArr, fromNull, collect, h, t, kept, others, shallow];
```

```text
===== node20 --check js08b-11x-forms.js (exit=0) =====

```

> ★ **이 빈 블록이 근거다.** 「문법 오류가 안 났다」를 산문으로 적으면 **안 물어본 것과 구분이 안 된다.**

**금지 사례 — 컴파일이 안 되는 형태.** 문구까지는 위 1번 블록의 `[5]` 가 확인해 준다.

```text
function f(...r, b) {}       // 나머지 매개변수는 마지막이어야 한다
function f(...r = []) {}     // 나머지는 기본값을 못 가진다
const [a, ...b, c] = arr;    // 배열 패턴의 나머지도 마지막이어야 한다
const [...r,] = arr;         // 나머지 뒤에 꼬리 쉼표를 못 쓴다
const [...r = []] = arr;     // 패턴의 나머지도 기본값을 못 가진다
const { ...r, a } = obj;     // 객체 패턴의 나머지도 마지막이어야 한다
const { ...{ a } } = obj;    // 선언 자리의 나머지는 이름이어야 한다
```

규칙은 여덟이다.

1. **값 자리에 서면 펴는 것, 받는 자리에 서면 모으는 것**이다. 자리가 뜻을 정한다.
2. **배열 자리와 호출 자리는 이터레이터를 돌린다.** 이터러블이 아니면 `TypeError` 다.
3. **객체 자리는 프로퍼티를 복사한다.** **아무것도 거부하지 않는다** — `null` 도 `7` 도 `{}` 가 된다.
4. **객체 자리는 「자기 것이고 열거 가능한」 것만 가져온다.** 심볼 키는 가져오고, getter 는 값으로 굳는다.
5. **나중에 적은 것이 이긴다.** `undefined` 도 값이라 덮어쓴다.
6. **스프레드는 프로퍼티를 정의하고 `Object.assign` 은 대입한다** — 대상의 setter 에서 갈린다.
7. **얕다.** 한 겹만 새것이고 프로토타입·메서드·비열거 프로퍼티는 안 온다.
8. **모으는 자리는 반드시 마지막**이고 기본값도 꼬리 쉼표도 못 쓴다. **펴는 자리는 어디든 된다.**

## 어디서 틀리나

### (1) ★★★ 「이터러블이면 어디서든 펴진다」고 믿는다

**객체 자리에서는 안 펴진다.** `{ ...new Set([1,2]) }` 가 `{}` 다. **에러도 안 난다.**
★ 09번의 `apply(t, set)` 과 같은 집안의 사고다 — **자리마다 보는 것이 다르다.**

### (2) ★★★ 「복사했다」로 읽는다

**한 겹만 복사한다.** 중첩 객체는 원본과 같은 객체다.
★ 깊은 복사가 필요하면 [목록의 **48번 주제**](../48-deep-copy-methods-compared/)가 정본이다.

### (3) ★★★ 클래스 인스턴스를 스프레드한다

프로토타입·메서드·getter 가 **전부 사라진다.** `instanceof` 가 `false` 가 된다.
★ 인스턴스를 복사하려면 **그 클래스가 복사 방법을 제공**해야 한다.

### (4) ★★ 중첩 객체를 병합하려고 스프레드를 쓴다

**갈아치워진다.** `{ ...state, ...patch }` 는 `state.a.b` 를 지킨다는 뜻이 아니다.

### (5) ★★ 희소 배열을 스프레드로 「그대로」 복사한다고 믿는다

**구멍이 `undefined` 슬롯으로 바뀐다.** `slice()` 와 결과가 다르다.

### (6) ★★ `Object.assign` 과 완전히 같다고 믿는다

**대상의 setter 에서 갈린다.** 스프레드는 setter 를 안 부르고 값을 덮어쓴다.

### (7) ★ 나머지를 앞에 쓴다

**전부 `SyntaxError`** 다 — 매개변수든 배열 패턴이든 객체 패턴이든 마지막이어야 한다.
★ 반면 **펴는 쪽은 어디든 된다** — `[0, ...a, 9]` 가 된다.

### (8) ★ 큰 배열을 호출 인자로 편다

**여섯 자리에서 `RangeError`** 다(09번). 스프레드도 `apply` 와 같은 벽에 걸린다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- **배열·호출 자리가 이터레이터를, 객체 자리가 프로퍼티 복사를 쓰는 것** — 그리고 그 호출 순서.
- **객체 자리가 아무 값도 거부하지 않는 것**(`null`·`undefined` 포함)과 **배열·호출 자리가 이터러블만 받는 것.**
- **객체 자리가 「자기 것이고 열거 가능한」 것만 가져오고 심볼 키를 포함하는 것.**
- **getter 가 한 번 불려 값으로 굳는 것**과 **대상의 setter 가 안 불리는 것**(`Object.assign` 과 갈리는 자리).
- **나중에 적은 것이 이기는 것.**
- **얕은 복사라는 것**과 **복사본의 프로토타입이 `Object.prototype` 인 것.**
- **이터레이터가 구멍 자리에서 `undefined` 를 내주는 것**(`[...sparse]` 가 구멍을 메운다).
- **모으는 자리가 마지막이어야 하고 기본값을 못 갖는 것.**

### 엔진(V8) 구현 · 이 판의 관찰

- ★★★ **예외 문구.** 그리고 **이 주제에서 실제로 두 판이 갈렸다** —
  `Found non-callable @@iterator`(v18) 대 `Spread syntax requires ...iterable[Symbol.iterator] to be a function`(v20).
  **종류는 둘 다 `TypeError`** 다.
- ★★ **`{(intermediate value)} is not iterable` 처럼 문구에 소스 텍스트가 박히는 것** — 10번과 같은 성질이다.
- ★ **호출 인자 개수의 상한** — 09번에서 확인했듯 **명세에 없고** 스택이 정한다.

### 호스트가 정하는 것 — ECMA-262 밖

- **없다.** 브라우저에 던진 열세 줄이 Node 와 전부 같았다.
  ★ 문구까지 같은 것은 **둘 다 V8 이기 때문**이다 — Node 18 에서는 한 줄이 달랐다.

### 그래서 이렇게 적으면 틀린다

| 이렇게 적으면 틀린다 | 이렇게 적어야 한다 |
|---|---|
| 「`...` 는 이터러블을 편다」 | **배열·호출 자리만** 그렇다. 객체 자리는 프로퍼티를 복사한다 |
| 「`{ ...set }` 으로 Set 을 객체로 만든다」 | `{}` 가 된다. **에러도 안 난다** |
| 「`{ ...null }` 은 터진다」 | 안 터진다. `{}` 다. **터지는 것은 `[...null]`** 이다 |
| 「스프레드로 객체를 복사한다」 | 한 겹만이다. 프로토타입·메서드·비열거는 안 온다 |
| 「스프레드는 `Object.assign` 과 같다」 | **대상의 setter** 에서 갈린다 |
| 「`[...sparse]` 는 구멍을 유지한다」 | 메운다. `slice()` 와 다르다 |
| 「`TypeError: Found non-callable @@iterator` 가 난다」 | **종류만** 근거다. v18 과 v20 의 문구가 다르다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓰는 모양 | 왜 |
|---|---|---|
| 배열 이어 붙이기 | `[...a, ...b]` | `concat` 과 결과가 같고 자리가 자유롭다 |
| 이터러블을 배열로 | `[...set]` · `[...map]` | `Array.from` 과 같은 결과다 |
| 인자를 배열에서 펴기 | `f(...arr)` | `apply` 를 대신한다(09번) |
| 필드 몇 개만 바꾼 새 객체 | `{ ...obj, a: 9 }` | 원본을 안 건드린다 |
| 필드 몇 개만 빼고 넘기기 | `const { secret, ...safe } = obj` | 10번의 나머지 패턴 |
| 인자 개수가 열린 함수 | `function f(...args)` | 진짜 배열이라 배열 메서드가 바로 된다 |
| 유사 배열을 펴야 할 때 | **`apply` 또는 `Array.from`** | 스프레드는 유사 배열을 못 편다 |

**안 쓰는 쪽**

- **클래스 인스턴스에 쓰지 않는다** — 프로토타입과 메서드를 잃는다.
- **깊은 복사·깊은 병합에 쓰지 않는다** — 한 겹뿐이다.
- **큰 배열을 호출 인자로 펴지 않는다** — `RangeError` 다(09번).
- **비싼 getter 가 있는 객체에 `{ ...obj }` 를 쓰지 않는다** — 전부 불린다.
- **희소 배열의 구멍을 지켜야 하면 쓰지 않는다** — `slice()` 를 쓴다.

## 핵심 문장

- **자리가 뜻을 정한다** — 값 자리면 펴고 받는 자리면 모은다.
- **펴는 세 자리가 두 규칙으로 갈린다** — 배열·호출은 이터레이터, 객체는 프로퍼티 복사.
- **그 차이는 값으로 안 보이고 로그로만 보인다** — `{ ...it }` 이 `Symbol.iterator` 를 읽기만 하고 안 부른다.
- **객체 자리는 아무것도 거부하지 않는다** — `null` 도 `{}` 가 된다. 그래서 조용히 틀린다.
- **얕다.** 한 겹만 새것이고 프로토타입·메서드·비열거 프로퍼티는 안 온다.
- **스프레드는 정의하고 `Object.assign` 은 대입한다** — 대상의 setter 한 자리에서 갈린다.

## 관련 자료

- [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) — **나머지 매개변수가 `arguments` 와 무엇이 다른지는 그쪽이 정본이고, 여기서는 세 자리 중 하나로만 등장한다.**
- [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) — **`apply` 는 유사 배열을, 스프레드는 이터러블을 본다.** 서로 못 덮는 자리를 하나씩 갖는다.
- [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) — **모으는 자리 둘(배열 패턴·객체 패턴)의 규칙은 그쪽이 정본이고, 여기서는 「펴는 쪽과 짝」으로만 본다.**
- [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/) 「이터러블 프로토콜과 `for...of`」 — **`Symbol.iterator` 계약은 그쪽이 정본이고, 여기서는 배열·호출 자리가 그것을 쓴다는 것까지.**
- [목록의 **27번 주제**](../27-object-static-methods/) 「`Object` 정적 메서드」 — **`Object.assign` 의 API 세부는 그쪽이고, 여기서는 스프레드와 갈리는 한 자리만 본다.**
- [목록의 **48번 주제**](../48-deep-copy-methods-compared/) 「깊은 복사 수단 비교」 — **깊은 복사는 그쪽이 정본이고, 여기서는 「얕다」는 사실과 그 결과까지.**
- [목록의 **13번 주제**](../13-object-literals-and-properties/) 「객체 리터럴과 프로퍼티」 — **열거 순서 규칙은 그쪽이 정본이고, 여기서는 나머지가 그 순서로 읽는 것만 관찰한다.**
- [파이썬 갈래의 19번 「함수 인자 규칙」](../../../python/syntax/19-function-argument-rules/) — **`f(*args)` 와 키워드 가변 인자가 자리마다 다른 일을 한다는 점이 닮았다.** 정본은 그쪽이다.
- [Go 갈래의 12번 「함수: 다중 반환·명명 반환값·가변 인자」](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/) — **`xs...` 로 슬라이스를 펴는 것과 대비된다.** Go 는 타입이 맞아야 하고 객체 자리가 없다.

## 용어 풀이

- **스프레드(spread)**: 값이 오는 자리에서 하나를 여럿으로 펴는 것. `[...x]` · `{ ...x }` · `f(...x)`.
- **나머지(rest)**: 받는 자리에서 여럿을 하나로 모으는 것. `function f(...r)` · `[a, ...r]` · `{ a, ...r }`.
- **이터러블(iterable)**: `Symbol.iterator` 를 가진 값. **배열·호출 자리가 이것을 요구한다.**
- **유사 배열(array-like)**: `length` 와 인덱스 키를 가진 객체. **스프레드는 못 편다.**
- **프로퍼티 복사(CopyDataProperties)**: 객체 자리의 스프레드가 하는 일. 자기 것이고 열거 가능한 것만 가져온다.
- **얕은 복사(shallow copy)**: 한 겹만 새로 만들고 안쪽은 같은 객체를 가리키는 것.
- **구멍(hole)**: 희소 배열에서 값이 아예 없는 자리. `1 in arr` 이 `false` 다.
- **정의 대 대입**: 스프레드는 프로퍼티를 **정의**하고 `Object.assign` 은 **대입**한다. 대상의 setter 에서 갈린다.

## 더 들어가면

- **`Array.from` 의 두 문** — 이터러블이면 그쪽으로, 아니면 유사 배열로 읽는다.
  그래서 **스프레드가 못 하는 일을 한다.** 정본은 [목록의 **26번 주제**](../26-array-search-flatten-and-create/)다.
- **`structuredClone`** — 호스트 API 로 깊은 복사를 한다. 정본은 [목록의 **48번 주제**](../48-deep-copy-methods-compared/)다.
- **`Proxy` 를 스프레드하면** — `ownKeys` 와 트랩이 그대로 불린다. 위 로그가 그 관찰이고 정본은 [목록의 **45번 주제**](../45-proxy/)다.
- **제너레이터를 펴면** — 끝까지 돌린다. 무한 제너레이터에 `[...gen]` 을 쓰면 안 끝난다. [목록의 **20번 주제**](../20-generators/).
- **JSX·객체 스프레드의 순서 관용구** — 「기본값 먼저, 덮어쓸 것 나중」은 이 주제의 규칙 5를 쓰는 것이다.
