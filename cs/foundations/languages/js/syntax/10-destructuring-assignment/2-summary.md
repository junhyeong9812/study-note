# js/syntax/10 — 구조 분해 할당: 「왼쪽은 값이 아니라 모양이다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ④ 예외의 `constructor.name` + `message` 다.**
> 구조 분해의 값은 **성공했을 때가 아니라 실패했을 때** 나온다 — `null` 과 `undefined` 에서,
> 그리고 **객체 패턴과 배열 패턴이 서로 다른 이유로** 터진다.
> **예외 문구 그 자체가 이 주제의 교재**다. ② 전수 격자(값 15 × 패턴 4)가 그 문구를 담는 그릇이고,
> ① 추상 연산 로그 심기가 「그래서 무엇을 부르는가」를 보인다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 구조 분해 바인딩·할당 패턴 · `RequireObjectCoercible` · 이터레이터 닫기
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — 객체 나머지(ES2018)가 들어온 판을 가릴 때
> - [MDN — 구조 분해 할당](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Destructuring)
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
> ★★ **`SyntaxError` 는 `try`/`catch` 로 못 잡는다**(파싱 단계에서 나기 때문이다).
> 그래서 엄격/비엄격 격자는 `new Function(소스)` 으로 **두 번 컴파일**해 값과 문구를 받는다.
> ★★★ **그 격자는 엄격 쪽을 먼저 돌린다.** 비엄격이 먼저 돌면 **암시적 전역이 만들어져 엄격 쪽이 그것을 읽는다** —
> 실제로 이 순서 때문에 한 번 거짓 「**0 / 12**」가 나왔다.
> ★★ **`undefined` 를 `JSON.stringify` 로 찍지 않는다.** 배열 안에서는 `null` 로, 객체에서는 통째로 사라져
> **이 주제에서 가장 중요한 값이 안 보인다.** 그래서 치환자로 `"<undefined>"` 를 찍는다.
> ★★ **`padEnd` 격자의 라벨은 전부 ASCII 다.**
> ★ **이 주제에는 시각·로캘·난수가 닿는 칸이 하나도 없다.**
>
> **버전** — 배열·객체 구조 분해와 기본값·나머지 원소는 **ES2015**, **객체 나머지(`{ a, ...r }`)는 ES2018** 이다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **④ 예외의 `constructor.name` + `message`**(본체) | `null`·`undefined` 가 **패턴마다 다른 문구**로 터지는 것 — 그 문구가 교재다 |
> | ★★★ **② 전수 격자** | 값 15 × 패턴 4 = 60칸 — **터지는 칸이 몇 개인가** |
> | ★★★ **① 추상 연산에 로그 심기** | 객체 패턴은 **getter 를**, 배열 패턴은 **이터레이터를** 부른다는 것 |
> | ★★ **두 번 컴파일** | 설정에 달린 칸 · **`SyntaxError` 가 나는 자리** |
> | ★ **⑤ 두 판 대조기 + 브라우저** | 판이 갈린 칸 · 호스트가 정하는 칸이 있나 |
> | ★ **부적용 — ③ 브랜드 태그** | 여기서는 보조로만 쓴다(나머지가 `Array` 냐 `Object` 냐). 본체가 아니다 |
> | ★ **부적용 — ⑥ `toFixed(20)`** · **⑦ `\uXXXX` 펼치기** | 부동소수점·인코딩이 닿는 칸이 없다. **잴 것이 없다** |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **예외의 종류** · **터진 칸의 개수** |
> | 예외 **문구**(판이 오르면 바뀐다) · 문구에 박히는 **변수 이름** | ★★★ **getter·`next` 호출 순서와 횟수** |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **`length` 값** · 객체 나머지가 무엇을 복사하는지 |
>
> ★★ **문구에 변수 이름이 박히는 것을 주의해서 읽어라** — V8 은 **그 자리의 소스 텍스트**를 메시지에 넣는다.
> 같은 실패라도 `v is not iterable` 과 `{(intermediate value)} is not iterable` 로 다르게 나온다. **근거는 종류이고 문구가 아니다.**
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md).
> ★★★ **08번에서 「매개변수 목록이 단순하지 않으면 `arguments` 연동이 끊긴다」를 봤다.** 구조 분해 매개변수가 그것을 만드는 셋 중 하나였고,
> **그 패턴의 규칙 자체는 여기가 정본**이다.
> ★ 01번의 **원시값 임시 래핑**이 여기서 그대로 쓰인다 — `const { length } = "abc"` 가 되는 이유다.
> **이어지는 곳** — [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/) 「이터러블 프로토콜과 `for...of`」
>
> ★★ **경계 — 이터러블 프로토콜의 계약은 19번이 정본이다.** 여기서는 **배열 패턴이 그 프로토콜을 쓴다**는 사실과
> **몇 번 부르고 언제 닫는가**까지 본다.
> ★★ **경계 — 스프레드(`...`)의 세 자리는 11번이 정본이다.** 여기서는 **패턴 안의 나머지**만 다룬다.
> ★★ **경계 — 타입 이야기는 여기 없다.** 구조 분해의 타입 추론은 TS 갈래의 몫이다.

## 한눈에 — 쉽게 말하면

**구조 분해는 「왼쪽에 값을 적는 대신 모양을 적는 것」이다.**

- 대입은 원래 `왼쪽 = 오른쪽` 인데, **왼쪽에 이름 하나 대신 모양을 적으면** JS 가 그 모양대로 오른쪽을 뜯어 담는다.
- **배열 모양은 자리로**, **객체 모양은 키로** 뜯는다. 그래서 **배열은 순서가 중요하고 객체는 순서가 상관없다.**
- 뜯을 것이 없으면 **`undefined`** 가 들어간다. 그런데 **뜯을 대상 자체가 `null`·`undefined` 면 터진다.**
- ★ 그리고 **그 둘이 터지는 이유가 패턴마다 다르다.** 이 주제의 값이 거기 있다.

```text
   const { a, b } = obj;              키로 뜯는다. 순서 상관없다
   const [x, y]   = arr;              자리로 뜯는다. 순서가 전부다

        obj                              arr
   ┌───────────┐                   ┌───┬───┬───┐
   │ b: 2      │ ──키 'a'──> a     │ 1 │ 2 │ 3 │
   │ a: 1      │ ──키 'b'──> b     └─┬─┴─┬─┴───┘
   └───────────┘                     │   └──> y
                                     └──────> x

   ★ 배열 모양은 「인덱스로 읽는다」가 아니다. 이터레이터를 돌린다.
     그래서 Set 도 문자열도 뜯어진다.
```

**터지는 두 가지가 서로 다른 실패다.**

```text
   const { a } = null    ->  TypeError   「Cannot destructure property 'a' of 'null' as it is null.」
   const [a]   = null    ->  TypeError   「null is not iterable」

   const { a } = {}      ->  a = undefined        (조용히 통과한다)
   const [a]   = {}      ->  TypeError   「{} is not iterable」

   ★ 객체 패턴은 「객체로 바꿀 수 있나」만 묻는다. 7 도 "ab" 도 통과한다.
   ★ 배열 패턴은 「이터러블인가」를 묻는다. 객체는 그 자리에서 거부된다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 모양이 적힌 틀 | 왼쪽의 패턴 | 값이 아니라 모양이라 중첩된다 |
| 자리로 뜯는 틀 | 배열 패턴 | 이터레이터를 돌린다 |
| 이름표로 뜯는 틀 | 객체 패턴 | 키로 읽는다. 순서 상관없다 |
| 틀에 안 맞는 칸 | 없는 키·모자란 원소 | `undefined` 가 들어간다 |
| 틀을 댈 수 없는 것 | `null`·`undefined` | 객체 패턴은 「강제할 수 없다」, 배열 패턴은 「이터러블이 아니다」 |
| 빈 칸에 미리 적어 둔 값 | 기본값 | `undefined` 일 때만 쓴다 |
| 남은 것을 쓸어 담는 자루 | 나머지 원소·나머지 프로퍼티 | 반드시 마지막 |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
API 응답이 `null` 일 때 `const { data } = res` 가 **터지는 사고**가 그것이고,
`const { a = 1 } = { a: null }` 이 **`1` 이 아니라 `null` 을 주는** 사고가 그것이다.

## 이 주제가 답하려는 질문

1. ★★★ **무엇을 뜯을 수 있고 무엇을 못 뜯나** — 값 15종 × 패턴 4종을 전수로 던지면 몇 칸이 터지나?
2. ★★★ **`null` 과 `undefined` 는 왜 다른 문구로 터지나** — 그리고 객체 패턴과 배열 패턴의 실패는 왜 다른 실패인가?
3. ★★ **구조 분해는 실제로 무엇을 부르나** — getter 인가 인덱스인가 이터레이터인가? 몇 번 부르고 언제 닫나?

## 동작 방식

### (1) ★★ 형태 — 무엇을 어떻게 뜯나

```js
// js08b-10a-forms.js
// 구조 분해 -- 형태마다 무엇을 꺼내는가. 왼쪽은 「모양」이고 오른쪽은 「값」이다.
function show(label, run) {
  try { console.log("  " + label.padEnd(44) + " -> " + String(run())); }
  catch (e) { console.log("  " + label.padEnd(44) + " -> " + e.constructor.name + ": " + e.message); }
}
// undefined 가 JSON 에서 사라지거나 null 로 보이는 것을 막는다 -- 이 주제는 그 자리가 답이다.
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));

console.log("[1] array pattern -- position decides");
show("const [a, b] = [1, 2]", () => { const [a, b] = [1, 2]; return J([a, b]); });
show("const [, b] = [1, 2]  hole", () => { const [, b] = [1, 2]; return J(b); });
show("const [a, , c] = [1, 2, 3]", () => { const [a, , c] = [1, 2, 3]; return J([a, c]); });
show("const [a, b, c] = [1, 2]  short", () => { const [a, b, c] = [1, 2]; return J([a, b, c]); });
show("const [a, ...r] = [1, 2, 3]", () => { const [a, ...r] = [1, 2, 3]; return J([a, r]); });
show("const [a, ...r] = [1]", () => { const [a, ...r] = [1]; return J([a, r]); });
show("const [[x], [y]] = [[1], [2]]", () => { const [[x], [y]] = [[1], [2]]; return J([x, y]); });
show("const [a, b] = 'hi'  string", () => { const [a, b] = "hi"; return J([a, b]); });
show("const [a, b] = new Set([1, 2])", () => { const [a, b] = new Set([1, 2]); return J([a, b]); });
show("const [[k, v]] = new Map([['x', 1]])", () => { const [[k, v]] = new Map([["x", 1]]); return J([k, v]); });

console.log("");
console.log("[2] object pattern -- the key decides, order does not");
show("const { a, b } = { b: 2, a: 1 }", () => { const { a, b } = { b: 2, a: 1 }; return J([a, b]); });
show("const { a: x } = { a: 1 }  rename", () => { const { a: x } = { a: 1 }; return J(x); });
show("const { a: { b } } = { a: { b: 1 } }", () => { const { a: { b } } = { a: { b: 1 } }; return J(b); });
show("const { missing } = { a: 1 }", () => { const { missing } = { a: 1 }; return J(missing); });
show("const { a, ...rest } = { a: 1, b: 2, c: 3 }", () => { const { a, ...rest } = { a: 1, b: 2, c: 3 }; return J([a, rest]); });
const key = "dyn";
show("const { [key]: v } = { dyn: 9 }  computed", () => { const { [key]: v } = { dyn: 9 }; return J(v); });
show("const { length } = 'abc'  primitive", () => { const { length } = "abc"; return J(length); });
show("const { toFixed } = 7  from prototype", () => { const { toFixed } = 7; return typeof toFixed; });
show("const { 0: first } = ['a', 'b']  index key", () => { const { 0: first } = ["a", "b"]; return J(first); });
const sym = Symbol("s");
show("const { [sym]: sv } = { [sym]: 1 }", () => { const { [sym]: sv } = { [sym]: 1 }; return J(sv); });

console.log("");
console.log("[3] what object rest copies -- and what it leaves behind");
const src = { a: 1, b: 2 };
Object.defineProperty(src, "hidden", { value: 3, enumerable: false });
src[sym] = 4;
Object.defineProperty(src, "getter", { get() { return 5; }, enumerable: true });
const proto = { inherited: 6 };
Object.setPrototypeOf(src, proto);
const { a, ...restOf } = src;
show("own enumerable string keys", () => J(Object.keys(restOf)));
show("non-enumerable 'hidden' copied?", () => Object.prototype.hasOwnProperty.call(restOf, "hidden"));
show("symbol key copied?", () => Object.prototype.hasOwnProperty.call(restOf, sym));
show("inherited 'inherited' copied?", () => Object.prototype.hasOwnProperty.call(restOf, "inherited"));
show("getter copied as a value?", () => J(Object.getOwnPropertyDescriptor(restOf, "getter")));
show("prototype of the rest object", () => String(Object.getPrototypeOf(restOf) === Object.prototype));
const nested = { inner: { n: 1 } };
const { ...shallow } = nested;
shallow.inner.n = 99;
show("rest is a shallow copy", () => J(nested));

console.log("");
console.log("[4] assignment without a declaration -- the parentheses are not optional");
show("({ a: A } = { a: 1 })", () => { let A; ({ a: A } = { a: 1 }); return J(A); });
show("[p, q] = [1, 2]  no parens needed", () => { let p, q; [p, q] = [1, 2]; return J([p, q]); });
show("swap: [p, q] = [q, p]", () => { let p = 1, q = 2; [p, q] = [q, p]; return J([p, q]); });
show("{ a: A } = { a: 1 }  without parens", () => new Function("let A; { a: A } = { a: 1 }; return A;")());
show("target can be a property", () => { const t = {}; [t.x, t.y] = [1, 2]; return J(t); });
show("target can be an index", () => { const t = []; ({ a: t[0] } = { a: 7 }); return J(t); });
```

```text
===== node20 js08b-10a-forms.js (exit=0) =====
[1] array pattern -- position decides
  const [a, b] = [1, 2]                        -> [1,2]
  const [, b] = [1, 2]  hole                   -> 2
  const [a, , c] = [1, 2, 3]                   -> [1,3]
  const [a, b, c] = [1, 2]  short              -> [1,2,"<undefined>"]
  const [a, ...r] = [1, 2, 3]                  -> [1,[2,3]]
  const [a, ...r] = [1]                        -> [1,[]]
  const [[x], [y]] = [[1], [2]]                -> [1,2]
  const [a, b] = 'hi'  string                  -> ["h","i"]
  const [a, b] = new Set([1, 2])               -> [1,2]
  const [[k, v]] = new Map([['x', 1]])         -> ["x",1]

[2] object pattern -- the key decides, order does not
  const { a, b } = { b: 2, a: 1 }              -> [1,2]
  const { a: x } = { a: 1 }  rename            -> 1
  const { a: { b } } = { a: { b: 1 } }         -> 1
  const { missing } = { a: 1 }                 -> "<undefined>"
  const { a, ...rest } = { a: 1, b: 2, c: 3 }  -> [1,{"b":2,"c":3}]
  const { [key]: v } = { dyn: 9 }  computed    -> 9
  const { length } = 'abc'  primitive          -> 3
  const { toFixed } = 7  from prototype        -> function
  const { 0: first } = ['a', 'b']  index key   -> "a"
  const { [sym]: sv } = { [sym]: 1 }           -> 1

[3] what object rest copies -- and what it leaves behind
  own enumerable string keys                   -> ["b","getter"]
  non-enumerable 'hidden' copied?              -> false
  symbol key copied?                           -> true
  inherited 'inherited' copied?                -> false
  getter copied as a value?                    -> {"value":5,"writable":true,"enumerable":true,"configurable":true}
  prototype of the rest object                 -> true
  rest is a shallow copy                       -> {"inner":{"n":99}}

[4] assignment without a declaration -- the parentheses are not optional
  ({ a: A } = { a: 1 })                        -> 1
  [p, q] = [1, 2]  no parens needed            -> [1,2]
  swap: [p, q] = [q, p]                        -> [2,1]
  { a: A } = { a: 1 }  without parens          -> SyntaxError: Unexpected token '='
  target can be a property                     -> {"x":1,"y":2}
  target can be an index                       -> [7]
```

- ★★ **배열 패턴은 자리로 뜯는다.** 구멍(`[, b]`)으로 건너뛰고, 모자라면 `undefined` 가 들어간다.
  ★ **배열이 아니어도 된다** — 문자열·`Set`·`Map` 이 전부 뜯어진다. **이터러블이면 된다.**
- ★★ **객체 패턴은 키로 뜯는다.** 오른쪽의 키 순서는 상관없고, 없는 키는 `undefined` 다.
  ★★ **원시값도 뜯어진다** — `const { length } = "abc"` 가 `3` 이고 `const { toFixed } = 7` 이 함수다.
  01번의 **임시 래핑**이 여기서 그대로 쓰인다.
  ★ **인덱스도 키로 읽을 수 있다** — `const { 0: first } = ["a","b"]` 가 `"a"` 다. **이터레이터를 안 탄다.**
- ★★★ **객체 나머지(`{ a, ...rest }`)가 복사하는 것은 「자기 것이고 열거 가능한」 프로퍼티**다.
  출력의 `[3]` 이 네 칸을 갈랐다 — **비열거 프로퍼티는 안 오고**, **심볼 키는 오고**,
  **상속된 프로퍼티는 안 오고**, **getter 는 「그때의 값」으로** 온다(`{"value":5,...}`).
  ★★ **그리고 얕다** — `nested.inner.n` 이 `99` 로 바뀌었다. 정본은 [11번](../11-spread-and-rest/2-summary.md)이다.
- ★★ **선언 없이 쓰려면 객체 패턴은 괄호가 필요하다.** `{ a: A } = { a: 1 }` 은 `SyntaxError` 다 —
  줄 첫머리의 `{` 가 **블록으로 파싱**되기 때문이다. 배열 패턴은 그 문제가 없다.
  ★ **대입 대상은 변수가 아니어도 된다** — `[t.x, t.y] = [1, 2]` 처럼 프로퍼티나 인덱스도 된다.

### (2) ★★★ 전수 격자 — 값 15종 × 패턴 4종

**이 주제의 본체가 이 격자다.** 예외의 종류와 문구를 **손으로 한 칸도 안 채우고** 받는다.

```js
// js08b-10b-failures.js
// 구조 분해가 어디서 터지나 -- 값 12종 x 패턴 4종 전수 격자.
// 예외는 constructor.name 과 message 로만 찍는다. 이 주제의 답은 그 문구에 다 있다.
const VALUES = [
  ["{ a: 1 }", () => ({ a: 1 })],
  ["[1, 2]", () => [1, 2]],
  ["'ab'", () => "ab"],
  ["7", () => 7],
  ["0", () => 0],
  ["true", () => true],
  ["false", () => false],
  ["null", () => null],
  ["undefined", () => undefined],
  ["NaN", () => NaN],
  ["Symbol('s')", () => Symbol("s")],
  ["10n", () => 10n],
  ["function f() {}", () => function f() {}],
  ["new Set([1])", () => new Set([1])],
  ["{ length: 1 }", () => ({ length: 1 })],
];
const PATTERNS = [
  ["{ a }", (v) => { const { a } = v; return "a=" + String(a); }],
  ["{}", (v) => { const {} = v; return "ok"; }],
  ["[a]", (v) => { const [a] = v; return "a=" + String(a); }],
  ["[]", (v) => { const [] = v; return "ok"; }],
];

console.log("[1] value x pattern -- what comes out, or what is thrown");
console.log(("  " + "value".padEnd(18) + PATTERNS.map(([p]) => p.padEnd(16)).join("")).replace(/ +$/, ""));
const errs = [];
let thrown = 0;
for (const [vlabel, make] of VALUES) {
  const cells = [];
  for (const [plabel, run] of PATTERNS) {
    try { cells.push(run(make()).padEnd(16)); }
    catch (e) { thrown += 1; cells.push((e.constructor.name).padEnd(16)); errs.push([vlabel, plabel, e.constructor.name + ": " + e.message]); }
  }
  console.log("  " + vlabel.padEnd(18) + cells.join("").replace(/ +$/, ""));
}
console.log("  " + "cells thrown".padEnd(18) + thrown + " of " + VALUES.length * PATTERNS.length);

console.log("");
console.log("[2] the messages behind the thrown cells");
for (const [v, p, msg] of errs) console.log("  " + (p + " = " + v).padEnd(26) + msg);

console.log("");
console.log("[3] the same two failures are not the same failure");
const probe = [
  ["const { a } = null", () => { const { a } = null; return a; }],
  ["const [a] = null", () => { const [a] = null; return a; }],
  ["const { a } = {}", () => { const { a } = {}; return String(a); }],
  ["const [a] = {}", () => { const [a] = {}; return String(a); }],
  ["const [a] = { length: 1 }", () => { const [a] = { length: 1 }; return String(a); }],
  ["const [a] = { 0: 'x', length: 1 }", () => { const [a] = { 0: "x", length: 1 }; return String(a); }],
  ["Array.from({ 0: 'x', length: 1 })", () => JSON.stringify(Array.from({ 0: "x", length: 1 }))],
  ["const { a } = Object.create(null)", () => { const { a } = Object.create(null); return String(a); }],
];
for (const [label, run] of probe) {
  try { console.log("  " + label.padEnd(36) + " -> " + run()); }
  catch (e) { console.log("  " + label.padEnd(36) + " -> " + e.constructor.name + ": " + e.message); }
}

console.log("");
console.log("[4] a default value turns the undefined case into a value -- and only that case");
const withDefault = [
  ["const { a = 'D' } = { a: undefined }", () => { const { a = "D" } = { a: undefined }; return String(a); }],
  ["const { a = 'D' } = { a: null }", () => { const { a = "D" } = { a: null }; return String(a); }],
  ["const { a = 'D' } = {}", () => { const { a = "D" } = {}; return String(a); }],
  ["const { a = 'D' } = null", () => { const { a = "D" } = null; return String(a); }],
  ["const [a = 'D'] = [undefined]", () => { const [a = "D"] = [undefined]; return String(a); }],
  ["const [a = 'D'] = [null]", () => { const [a = "D"] = [null]; return String(a); }],
  ["const [a = 'D'] = []", () => { const [a = "D"] = []; return String(a); }],
  ["const [a = 'D'] = null", () => { const [a = "D"] = null; return String(a); }],
  ["const { a: { b } = {} } = {}", () => { const { a: { b } = {} } = {}; return String(b); }],
  ["const { a: { b } } = {}", () => { const { a: { b } } = {}; return String(b); }],
];
for (const [label, run] of withDefault) {
  try { console.log("  " + label.padEnd(40) + " -> " + run()); }
  catch (e) { console.log("  " + label.padEnd(40) + " -> " + e.constructor.name + ": " + e.message); }
}
```

```text
===== node20 js08b-10b-failures.js (exit=0) =====
[1] value x pattern -- what comes out, or what is thrown
  value             { a }           {}              [a]             []
  { a: 1 }          a=1             ok              TypeError       TypeError
  [1, 2]            a=undefined     ok              a=1             ok
  'ab'              a=undefined     ok              a=a             ok
  7                 a=undefined     ok              TypeError       TypeError
  0                 a=undefined     ok              TypeError       TypeError
  true              a=undefined     ok              TypeError       TypeError
  false             a=undefined     ok              TypeError       TypeError
  null              TypeError       TypeError       TypeError       TypeError
  undefined         TypeError       TypeError       TypeError       TypeError
  NaN               a=undefined     ok              TypeError       TypeError
  Symbol('s')       a=undefined     ok              TypeError       TypeError
  10n               a=undefined     ok              TypeError       TypeError
  function f() {}   a=undefined     ok              TypeError       TypeError
  new Set([1])      a=undefined     ok              a=1             ok
  { length: 1 }     a=undefined     ok              TypeError       TypeError
  cells thrown      28 of 60

[2] the messages behind the thrown cells
  [a] = { a: 1 }            TypeError: v is not iterable
  [] = { a: 1 }             TypeError: v is not iterable
  [a] = 7                   TypeError: v is not iterable
  [] = 7                    TypeError: v is not iterable
  [a] = 0                   TypeError: v is not iterable
  [] = 0                    TypeError: v is not iterable
  [a] = true                TypeError: v is not iterable
  [] = true                 TypeError: v is not iterable
  [a] = false               TypeError: v is not iterable
  [] = false                TypeError: v is not iterable
  { a } = null              TypeError: Cannot destructure property 'a' of 'v' as it is null.
  {} = null                 TypeError: Cannot destructure 'v' as it is null.
  [a] = null                TypeError: v is not iterable
  [] = null                 TypeError: v is not iterable
  { a } = undefined         TypeError: Cannot destructure property 'a' of 'v' as it is undefined.
  {} = undefined            TypeError: Cannot destructure 'v' as it is undefined.
  [a] = undefined           TypeError: v is not iterable
  [] = undefined            TypeError: v is not iterable
  [a] = NaN                 TypeError: v is not iterable
  [] = NaN                  TypeError: v is not iterable
  [a] = Symbol('s')         TypeError: v is not iterable
  [] = Symbol('s')          TypeError: v is not iterable
  [a] = 10n                 TypeError: v is not iterable
  [] = 10n                  TypeError: v is not iterable
  [a] = function f() {}     TypeError: v is not iterable
  [] = function f() {}      TypeError: v is not iterable
  [a] = { length: 1 }       TypeError: v is not iterable
  [] = { length: 1 }        TypeError: v is not iterable

[3] the same two failures are not the same failure
  const { a } = null                   -> TypeError: Cannot destructure property 'a' of 'null' as it is null.
  const [a] = null                     -> TypeError: null is not iterable
  const { a } = {}                     -> undefined
  const [a] = {}                       -> TypeError: {} is not iterable
  const [a] = { length: 1 }            -> TypeError: {(intermediate value)} is not iterable
  const [a] = { 0: 'x', length: 1 }    -> TypeError: {(intermediate value)(intermediate value)} is not iterable
  Array.from({ 0: 'x', length: 1 })    -> ["x"]
  const { a } = Object.create(null)    -> undefined

[4] a default value turns the undefined case into a value -- and only that case
  const { a = 'D' } = { a: undefined }     -> D
  const { a = 'D' } = { a: null }          -> null
  const { a = 'D' } = {}                   -> D
  const { a = 'D' } = null                 -> TypeError: Cannot read properties of null (reading 'a')
  const [a = 'D'] = [undefined]            -> D
  const [a = 'D'] = [null]                 -> null
  const [a = 'D'] = []                     -> D
  const [a = 'D'] = null                   -> TypeError: null is not iterable
  const { a: { b } = {} } = {}             -> undefined
  const { a: { b } } = {}                  -> TypeError: Cannot read properties of undefined (reading 'b')
```

```text
   60칸 중 28칸이 터졌다. 터진 칸은 두 덩어리다.

   덩어리 A — null 과 undefined (8칸)
     { a } = null       Cannot destructure property 'a' of 'v' as it is null.
     {}    = null       Cannot destructure 'v' as it is null.
     [a]   = null       null is not iterable
     []    = null       null is not iterable

     ★ 객체 패턴은 「빈 패턴이어도」 터진다. 뜯기 전에 「객체로 바꿀 수 있나」를 묻기 때문이다.

   덩어리 B — 이터러블이 아닌 것 (20칸)
     [a] = { a: 1 }     v is not iterable
     [a] = 7            v is not iterable
     [a] = { length: 1 } v is not iterable

     ★ 객체 패턴은 이 값들을 전부 통과시킨다. 배열 패턴만 거부한다.
```

- ★★★ **객체 패턴이 거부하는 값은 `null` 과 `undefined` 둘뿐**이다. 나머지 열셋은 전부 통과한다 —
  숫자·문자열·불리언·심볼·BigInt·함수·`Set` 까지. **뽑을 키가 없으면 `undefined` 를 줄 뿐** 터지지 않는다.
- ★★★ **배열 패턴은 이터러블만 받는다.** 15종 중 통과한 것은 **셋뿐**이다 — 배열·문자열·`Set`.
  `{ length: 1 }` 도 거부된다. **`apply` 와 정반대**다(09번은 유사 배열을 봤다).
- ★★★ **빈 패턴도 터진다.** `const {} = null` 과 `const [] = null` 이 둘 다 `TypeError` 다.
  ★ **아무것도 안 뜯어도 「뜯을 수 있는지」는 먼저 묻는다** — 이것이 두 패턴 공통의 첫 단계다.
  ★★ 다만 **문구가 다르다** — 빈 객체 패턴은 `Cannot destructure 'v' as it is null.` 로 **프로퍼티 이름이 빠진다.**
- ★★ **`[3]` 이 두 실패를 나란히 놓는다.** `const { a } = {}` 는 `undefined` 를 주고
  `const [a] = {}` 는 터진다 — **같은 오른쪽인데 왼쪽 모양 하나로 갈린다.**
  ★ `Array.from({ 0: 'x', length: 1 })` 은 되는데 `const [a] = { 0: 'x', length: 1 }` 은 안 된다.
  **`Array.from` 은 유사 배열도 보고 구조 분해는 안 본다.**
- ★★★ **기본값은 `undefined` 에만 걸린다.** `{ a = 'D' } = { a: null }` 이 **`null`** 이다.
  ★★ **그리고 기본값이 대상의 `null` 을 구해 주지는 않는다** — `{ a = 'D' } = null` 은 여전히 터진다.
  ★ 다만 **문구가 바뀐다**(`Cannot read properties of null (reading 'a')`) — 같은 종류, 다른 말이다.
- ★★ **중첩 패턴에 기본값을 다는 자리가 중요하다.** `{ a: { b } = {} } = {}` 는 통과하고
  `{ a: { b } } = {}` 는 터진다. **안쪽 모양을 댈 대상이 `undefined` 이기 때문**이다.

### (3) ★★★ 로그를 심어 보면 — 무엇을 부르나

```js
// js08b-10c-order.js
// 구조 분해가 실제로 무엇을 부르나 -- 추상 연산에 로그를 심어 호출 순서를 받는다.
const log = [];
function reset() { log.length = 0; }
function dump(label) { console.log("  " + label.padEnd(40) + JSON.stringify(log)); }

console.log("[1] object pattern -- the pattern's order wins, not the object's");
const src = {
  get b() { log.push("get b"); return 2; },
  get a() { log.push("get a"); return 1; },
  get c() { log.push("get c"); return 3; },
};
reset(); { const { a, b } = src; } dump("const { a, b } = src");
reset(); { const { b, a } = src; } dump("const { b, a } = src");
reset(); { const { a } = src; } dump("const { a } = src");
reset(); { const {} = src; } dump("const {} = src");
reset(); { const { ...all } = src; } dump("const { ...all } = src");
reset(); { const { a, ...rest } = src; } dump("const { a, ...rest } = src");

console.log("");
console.log("[2] a default is evaluated only when the slot is undefined");
function d(n) { log.push("default " + n); return n; }
const obj2 = { present: 1, undef: undefined, nul: null };
reset(); { const { present = d(1) } = obj2; } dump("{ present = d(1) }");
reset(); { const { undef = d(2) } = obj2; } dump("{ undef = d(2) }");
reset(); { const { nul = d(3) } = obj2; } dump("{ nul = d(3) }");
reset(); { const { missing = d(4) } = obj2; } dump("{ missing = d(4) }");
reset(); { const { absent: renamed = d(5) } = obj2; } dump("{ absent: renamed = d(5) }");

console.log("");
console.log("[3] array pattern goes through the iterator protocol, not through indexes");
function tracked(values) {
  return {
    [Symbol.iterator]() {
      let i = 0;
      log.push("Symbol.iterator");
      return {
        next() { log.push("next " + i); return i < values.length ? { value: values[i++], done: false } : { value: undefined, done: true }; },
        return(v) { log.push("return"); return { value: v, done: true }; },
      };
    },
  };
}
reset(); { const [a, b] = tracked([1, 2, 3]); } dump("const [a, b] = tracked(3 items)");
reset(); { const [a] = tracked([1, 2, 3]); } dump("const [a] = tracked(3 items)");
reset(); { const [] = tracked([1, 2, 3]); } dump("const [] = tracked(3 items)");
reset(); { const [a, ...r] = tracked([1, 2, 3]); } dump("const [a, ...r] = tracked(3 items)");
reset(); { const [a, b, c, d2] = tracked([1, 2]); } dump("const [a,b,c,d] = tracked(2 items)");
reset(); { const [, , third] = tracked([1, 2, 3]); } dump("const [, , third] = tracked(3)");

console.log("");
console.log("[4] the array's own iterator can be replaced -- destructuring follows it");
const arr = [10, 20, 30];
arr[Symbol.iterator] = function () {
  let i = arr.length;
  return { next: () => (i > 0 ? { value: arr[--i], done: false } : { value: undefined, done: true }) };
};
const [first, second] = arr;
console.log("  " + "const [first, second] = arr".padEnd(40) + JSON.stringify([first, second]));
console.log("  " + "arr[0], arr[1] are still".padEnd(40) + JSON.stringify([arr[0], arr[1]]));
const { 0: byKey, 1: byKey2 } = arr;
console.log("  " + "object pattern reads keys instead".padEnd(40) + JSON.stringify([byKey, byKey2]));

console.log("");
console.log("[5] a failing pattern still closes the iterator");
function throwing() {
  return {
    [Symbol.iterator]() {
      let i = 0;
      return {
        next() { log.push("next"); const v = i === 1 ? null : i; i += 1; return { value: v, done: false }; },
        return() { log.push("return called"); return { done: true }; },
      };
    },
  };
}
reset();
try { const [a, { b }] = throwing(); } catch (e) { log.push("threw " + e.constructor.name); }
dump("const [a, { b }] = throwing()");
reset();
try { const [a, b] = throwing(); } catch (e) { log.push("threw"); }
dump("const [a, b] = throwing()  plain");
```

```text
===== node20 js08b-10c-order.js (exit=0) =====
[1] object pattern -- the pattern's order wins, not the object's
  const { a, b } = src                    ["get a","get b"]
  const { b, a } = src                    ["get b","get a"]
  const { a } = src                       ["get a"]
  const {} = src                          []
  const { ...all } = src                  ["get b","get a","get c"]
  const { a, ...rest } = src              ["get a","get b","get c"]

[2] a default is evaluated only when the slot is undefined
  { present = d(1) }                      []
  { undef = d(2) }                        ["default 2"]
  { nul = d(3) }                          []
  { missing = d(4) }                      ["default 4"]
  { absent: renamed = d(5) }              ["default 5"]

[3] array pattern goes through the iterator protocol, not through indexes
  const [a, b] = tracked(3 items)         ["Symbol.iterator","next 0","next 1","return"]
  const [a] = tracked(3 items)            ["Symbol.iterator","next 0","return"]
  const [] = tracked(3 items)             ["Symbol.iterator","return"]
  const [a, ...r] = tracked(3 items)      ["Symbol.iterator","next 0","next 1","next 2","next 3"]
  const [a,b,c,d] = tracked(2 items)      ["Symbol.iterator","next 0","next 1","next 2"]
  const [, , third] = tracked(3)          ["Symbol.iterator","next 0","next 1","next 2","return"]

[4] the array's own iterator can be replaced -- destructuring follows it
  const [first, second] = arr             [30,20]
  arr[0], arr[1] are still                [10,20]
  object pattern reads keys instead       [10,20]

[5] a failing pattern still closes the iterator
  const [a, { b }] = throwing()           ["next","next","return called","threw TypeError"]
  const [a, b] = throwing()  plain        ["next","next","return called"]
```

```text
   const { a, b } = src        ->  ["get a", "get b"]      패턴 순서
   const { b, a } = src        ->  ["get b", "get a"]      패턴 순서
   const {}       = src        ->  []                      아무것도 안 읽는다
   const { ...all } = src      ->  ["get b","get a","get c"]  객체의 키 순서

   const [a, b] = it(3)        ->  iterator, next 0, next 1, return
   const [a, ...r] = it(3)     ->  iterator, next 0, next 1, next 2, next 3
   const []     = it(3)        ->  iterator, return

   ★ 객체 패턴은 「필요한 키만」 읽고, 배열 패턴은 「필요한 만큼만」 돌린 뒤 닫는다.
```

- ★★★ **객체 패턴은 패턴에 적은 순서로 읽는다.** 객체의 키 순서가 아니다 —
  `{ a, b }` 와 `{ b, a }` 가 **다른 순서**로 getter 를 부른다.
  ★ **빈 패턴은 아무 getter 도 안 부른다**(`[]`). 그런데 **나머지는 전부 부른다** —
  `{ ...all }` 은 객체의 키 순서로 셋 다 읽는다.
  ★★ 그래서 **getter 에 부수 효과가 있으면 패턴 모양이 그 순서와 횟수를 정한다.**
- ★★★ **기본값 식은 그 칸이 `undefined` 일 때만 평가된다.** `null` 도 `0` 도 아니고 **`undefined` 뿐**이다.
  출력의 `[2]` 다섯 줄이 그것을 하나씩 확인한다 — 08번의 매개변수 기본값과 **완전히 같은 규칙**이다.
- ★★★ **배열 패턴은 이터레이터 프로토콜을 탄다.** 인덱스를 읽지 않는다.
  ★★ **필요한 만큼만 돌린 뒤 `return()` 으로 닫는다** — `[a, b]` 는 `next` 두 번 뒤 `return` 이다.
  ★★ **나머지가 있으면 안 닫는다** — 끝까지 돌아 `done` 을 받았으니 닫을 것이 없다.
  ★ **빈 패턴도 이터레이터를 얻고 곧바로 닫는다**(`iterator, return`).
  ★ **구멍은 건너뛰는 것이 아니라 버리는 것**이다 — `[, , third]` 가 `next` 를 세 번 부른다.
- ★★ **배열의 `Symbol.iterator` 를 바꿔 놓으면 구조 분해가 그것을 따라간다.**
  `[first, second]` 가 `[30, 20]` 인데 `arr[0]`, `arr[1]` 은 여전히 `[10, 20]` 이다.
  ★ **같은 배열을 객체 패턴으로 읽으면 키로 읽어** 원래 값이 나온다 — **두 패턴이 서로 다른 문을 쓴다**는 증거다.
- ★★ **패턴 중간에서 터져도 이터레이터는 닫힌다.** `[a, { b }]` 에서 안쪽 패턴이 터지는데
  로그에 `return called` 가 **예외보다 먼저** 찍힌다. **자원을 흘리지 않는다**는 보장이다.

### (4) ★★ 매개변수 자리 — 그리고 설정에 달린 칸

```js
// js08b-10d-params.js
// 매개변수 자리의 구조 분해 -- 그리고 설정(엄격/비엄격)에 달린 칸.
// ★ 엄격 쪽을 먼저 돌린다. 비엄격이 먼저 돌면 암시적 전역이 만들어져 엄격 쪽이 그것을 읽는다.
const PROBES = [
  ["no declaration keyword", `
    ({ a: gObj } = { a: 1 });
    return "typeof gObj = " + typeof gObj;
  `],
  ["array target, no declaration", `
    [gArr] = [1];
    return "typeof gArr = " + typeof gArr;
  `],
  ["f({ a }) called with nothing", `
    function f({ a }) { return a; }
    return String(f());
  `],
  ["f({ a } = {}) called with nothing", `
    function f({ a } = {}) { return String(a); }
    return f();
  `],
  ["f({ a = 1 } = {}) called with nothing", `
    function f({ a = 1 } = {}) { return String(a); }
    return f();
  `],
  ["f([a, b]) called with nothing", `
    function f([a, b]) { return a; }
    return String(f());
  `],
  ["f([a, b]) called with an object", `
    function f([a, b]) { return a; }
    return String(f({}));
  `],
  ["f({ a }, { a })  same name twice", `
    function f({ a }, { a }) { return a; }
    return String(f({ a: 1 }, { a: 2 }));
  `],
  ["f(a, { a })  name reused", `
    function f(a, { a }) { return a; }
    return String(f(1, { a: 2 }));
  `],
  ["const { a, a } = { a: 1 }", `
    const { a, a } = { a: 1 };
    return String(a);
  `],
  ["var { a } = {}; var { a } = {}", `
    var { a } = { a: 1 };
    var { a } = { a: 2 };
    return String(a);
  `],
  ["f({ a }) { 'use strict'; }", `
    function f({ a }) { "use strict"; return a; }
    return String(f({ a: 1 }));
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
  const t = run(body, true), s = run(body, false);
  if (s !== t) differ += 1;
  console.log("  " + label);
  console.log("    " + "sloppy".padEnd(8) + s);
  console.log("    " + "strict".padEnd(8) + t + (s === t ? "" : "   <-- DIFFERENT"));
}
console.log("");
console.log("  " + "settings-dependent cells".padEnd(30) + differ + " of " + PROBES.length);

console.log("");
console.log("[2] length and name when the parameter is a pattern");
const fns = [
  ["function ({ a })", function ({ a }) {}],
  ["function ({ a } = {})", function ({ a } = {}) {}],
  ["function ([a, b])", function ([a, b]) {}],
  ["function (x, { a })", function (x, { a }) {}],
  ["function ({ a }, ...r)", function ({ a }, ...r) {}],
];
for (const [label, f] of fns) console.log("  " + label.padEnd(28) + "length " + f.length);

console.log("");
console.log("[3] the shapes that read well in real code");
function point({ x = 0, y = 0, label = "p" } = {}) { return label + "(" + x + "," + y + ")"; }
console.log("  " + "point()".padEnd(34) + point());
console.log("  " + "point({ x: 1 })".padEnd(34) + point({ x: 1 }));
console.log("  " + "point({ y: 2, label: 'q' })".padEnd(34) + point({ y: 2, label: "q" }));
const entries = Object.entries({ a: 1, b: 2 });
const joined = entries.map(([k, v]) => k + "=" + v).join(",");
console.log("  " + "entries.map(([k, v]) => ...)".padEnd(34) + joined);
const rows = [{ id: 1, tags: ["x", "y"] }];
const firstTag = rows.map(({ id, tags: [head] }) => id + ":" + head).join(",");
console.log("  " + "nested pattern in a callback".padEnd(34) + firstTag);
function head([first, ...rest] = []) { return String(first) + " / " + JSON.stringify(rest); }
console.log("  " + "head([1, 2, 3])".padEnd(34) + head([1, 2, 3]));
console.log("  " + "head()".padEnd(34) + head());
```

```text
===== node20 js08b-10d-params.js (exit=0) =====
[1] sloppy vs strict -- same probe, compiled twice
  no declaration keyword
    sloppy  typeof gObj = number
    strict  ReferenceError: gObj is not defined   <-- DIFFERENT
  array target, no declaration
    sloppy  typeof gArr = number
    strict  ReferenceError: gArr is not defined   <-- DIFFERENT
  f({ a }) called with nothing
    sloppy  TypeError: Cannot destructure property 'a' of 'undefined' as it is undefined.
    strict  TypeError: Cannot destructure property 'a' of 'undefined' as it is undefined.
  f({ a } = {}) called with nothing
    sloppy  undefined
    strict  undefined
  f({ a = 1 } = {}) called with nothing
    sloppy  1
    strict  1
  f([a, b]) called with nothing
    sloppy  TypeError: undefined is not iterable (cannot read property Symbol(Symbol.iterator))
    strict  TypeError: undefined is not iterable (cannot read property Symbol(Symbol.iterator))
  f([a, b]) called with an object
    sloppy  TypeError: object is not iterable (cannot read property Symbol(Symbol.iterator))
    strict  TypeError: object is not iterable (cannot read property Symbol(Symbol.iterator))
  f({ a }, { a })  same name twice
    sloppy  COMPILE SyntaxError: Duplicate parameter name not allowed in this context
    strict  COMPILE SyntaxError: Duplicate parameter name not allowed in this context
  f(a, { a })  name reused
    sloppy  COMPILE SyntaxError: Duplicate parameter name not allowed in this context
    strict  COMPILE SyntaxError: Duplicate parameter name not allowed in this context
  const { a, a } = { a: 1 }
    sloppy  COMPILE SyntaxError: Identifier 'a' has already been declared
    strict  COMPILE SyntaxError: Identifier 'a' has already been declared
  var { a } = {}; var { a } = {}
    sloppy  2
    strict  2
  f({ a }) { 'use strict'; }
    sloppy  COMPILE SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list
    strict  COMPILE SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list

  settings-dependent cells      2 of 12

[2] length and name when the parameter is a pattern
  function ({ a })            length 1
  function ({ a } = {})       length 0
  function ([a, b])           length 1
  function (x, { a })         length 2
  function ({ a }, ...r)      length 1

[3] the shapes that read well in real code
  point()                           p(0,0)
  point({ x: 1 })                   p(1,0)
  point({ y: 2, label: 'q' })       q(0,2)
  entries.map(([k, v]) => ...)      a=1,b=2
  nested pattern in a callback      1:x
  head([1, 2, 3])                   1 / [2,3]
  head()                            undefined / []
```

- ★★★ **설정에 달린 칸은 열둘 중 둘**이다. 둘 다 **선언 키워드 없이 대입한 것** —
  비엄격은 **암시적 전역**을 만들고 엄격은 `ReferenceError` 다.
  ★★★ **이 격자는 엄격 쪽을 먼저 돌려야 한다.** 비엄격이 먼저 돌면 전역이 만들어져
  **엄격 쪽이 그것을 읽고 「같다」고 답한다** — 실제로 처음엔 거짓 「**0 / 12**」가 나왔다.
  ★ 「두 번 컴파일」 격자는 **탐침끼리 전역을 통해 새는지**를 늘 의심해야 한다.
- ★★★ **`f({ a })` 를 인자 없이 부르면 터진다.** `undefined` 에 객체 패턴을 대는 것이기 때문이다.
  ★★ **고치는 법은 바깥 기본값**이다 — `f({ a } = {})`. **안쪽 기본값(`{ a = 1 }`)만으로는 안 고쳐진다.**
  ★ 이 둘을 헷갈리는 것이 이 주제에서 가장 흔한 실수다.
- ★★ **중복 이름은 패턴 안이든 밖이든 `SyntaxError`** 다 — `f({ a }, { a })` 도 `f(a, { a })` 도 막힌다.
  ★ **패턴이 있으면 매개변수 목록이 단순하지 않으므로**(08번) **비엄격에서도** 막힌다.
  ★ `const { a, a }` 는 다른 이유로 막힌다 — `Identifier 'a' has already been declared` 다.
  ★★ **`var` 는 막히지 않는다**(`var { a } = ...` 두 번이 통과한다). **선언 키워드가 규칙을 정한다.**
- ★★ **패턴 하나는 `length` 한 자리로 센다.** `({ a })` 가 `1`, `({ a } = {})` 가 `0` 이다 — 08번의 규칙 그대로다.
- ★ **읽기 좋은 모양은 굳어 있다** — 옵션 객체(`{ x = 0, y = 0 } = {}`) · `Object.entries` 순회 ·
  콜백 매개변수의 중첩 패턴 · `[first, ...rest] = []`.

### (5) ★★ 두 판에서 돌려 보면 — 갈린 자리가 없다

```text
===== ./js08b-vdiff.sh 10 (exit=0) =====
  same      js08b-10a-forms.js
  same      js08b-10b-failures.js
  same      js08b-10c-order.js
  same      js08b-10d-params.js
  ----
  identical on node18 and node20: 4   different: 0
```

- ★★ **네 스크립트가 두 판에서 한 글자도 같았다.** 예외 문구까지 같다.
  ★★ **「같았다」는 보장이 아니라 관찰**이다 — 08번에서 예외 문구 하나가 실제로 판 사이에 바뀌었다.
  **그래서 이 주제도 근거로 쓰는 것은 종류이고 문구가 아니다.**

### (6) ★★ 같은 질문을 브라우저에 던지면

```js
// js08b-10h-browser.js
// 같은 질문을 브라우저에 던진다 -- 구조 분해의 실패 문구는 호스트가 정하나.
const lines = [];
function row(k, v) { lines.push("  " + k.padEnd(38) + v); }
function attempt(label, run) {
  try { row(label, String(run())); }
  catch (e) { row(label, e.constructor.name + ": " + e.message); }
}
row("engine", navigator.userAgent.replace(/^.*(Chrome\/[0-9.]+).*$/, "$1"));
attempt("const { a } = null", () => { const { a } = null; return a; });
attempt("const {} = null", () => { const {} = null; return "ok"; });
attempt("const { a } = undefined", () => { const { a } = undefined; return a; });
attempt("const [a] = null", () => { const [a] = null; return a; });
attempt("const [a] = {}", () => { const [a] = {}; return a; });
attempt("const { a } = 7", () => { const { a } = 7; return String(a); });
attempt("const { length } = 'abc'", () => { const { length } = "abc"; return length; });
attempt("const { a = 'D' } = { a: null }", () => { const { a = "D" } = { a: null }; return String(a); });
attempt("const { a = 'D' } = { a: undefined }", () => { const { a = "D" } = { a: undefined }; return String(a); });
attempt("f({ a }) with no argument", () => { function f({ a }) { return a; } return f(); });
attempt("pattern order beats object order", () => {
  const log = [];
  const src = { get b() { log.push("b"); return 1; }, get a() { log.push("a"); return 2; } };
  const { a, b } = src;
  return log.join(",");
});
attempt("iterator calls for [a, b]", () => {
  const log = [];
  const it = { [Symbol.iterator]() { let i = 0; return { next() { log.push("next"); return { value: i++, done: false }; }, return() { log.push("return"); return { done: true }; } }; } };
  const [x, y] = it;
  return log.join(",");
});
document.documentElement.appendChild(document.createElement("pre")).textContent =
  "===OUT===" + String.fromCharCode(10) + lines.join(String.fromCharCode(10)) + String.fromCharCode(10) + "===END===";
```

호스트 페이지는 이 네 줄이 전부다.

```text
<!doctype html>
<meta charset="utf-8">
<title>js08b 10</title>
<script src="js08b-10h-browser.js"></script>
```

```text
===== google-chrome --headless --dump-dom page10.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' (exit=0) =====
  engine                                Chrome/151.0.0.0
  const { a } = null                    TypeError: Cannot destructure property 'a' of 'null' as it is null.
  const {} = null                       TypeError: Cannot destructure 'null' as it is null.
  const { a } = undefined               TypeError: Cannot destructure property 'a' of 'undefined' as it is undefined.
  const [a] = null                      TypeError: null is not iterable
  const [a] = {}                        TypeError: {} is not iterable
  const { a } = 7                       undefined
  const { length } = 'abc'              3
  const { a = 'D' } = { a: null }       null
  const { a = 'D' } = { a: undefined }  D
  f({ a }) with no argument             TypeError: Cannot destructure property 'a' of 'undefined' as it is undefined.
  pattern order beats object order      a,b
  iterator calls for [a, b]             next,next,return
```

- ★★★ **호스트가 정하는 칸이 하나도 없었다.** 열세 줄이 Node 쪽과 전부 같다 — **예외 문구까지 한 글자도 같다.**
  ★ 구조 분해는 **순수하게 언어 쪽**이라는 뜻이다.
  ★★ 문구가 같은 것은 **같은 엔진(V8)이기 때문**이지 명세가 정해서가 아니다. 다른 엔진에서는 다를 수 있다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js08b-10x-forms.js
// 형태만 모아 둔 파일 -- 출력은 없다. `node --check` 로 문법만 확인한다.
const arr = [1, 2, 3];
const obj = { a: 1, b: { c: 2 } };

const [first, second] = arr;              // 배열 -- 자리가 정한다
const [, onlySecond] = arr;               // 구멍 -- 건너뛴다
const [head, ...tail] = arr;              // 나머지 -- 마지막에만 온다
const [x = 10] = [];                      // 기본값 -- undefined 일 때만 걸린다

const { a } = obj;                        // 객체 -- 키가 정한다
const { a: renamed } = obj;               // 이름 바꾸기
const { b: { c } } = obj;                 // 중첩
const { missing = "D" } = obj;            // 기본값
const { a: kept, ...rest } = obj;         // 객체 나머지 -- ES2018
const key = "a";
const { [key]: computed } = obj;          // 계산된 키

let p, q;
({ a: p } = obj);                         // 선언 없이 -- 괄호가 필요하다
[p, q] = [q, p];                          // 맞바꾸기 -- 괄호가 필요 없다
const target = {};
[target.x] = arr;                         // 대상이 프로퍼티일 수도 있다

function point({ x = 0, y = 0 } = {}) { return x + y; }   // 매개변수 자리
point();                                                   // 바깥 기본값이 있어야 빈 호출이 된다
function head2([h] = []) { return h; }

for (const [k, v] of Object.entries(obj)) { void k; void v; }  // for-of 자리
arr.map(([a2, b2]) => a2 + b2);                                // 콜백 자리
```

```text
===== node20 --check js08b-10x-forms.js (exit=0) =====

```

> ★ **이 빈 블록이 근거다.** 「문법 오류가 안 났다」를 산문으로 적으면 **안 물어본 것과 구분이 안 된다.**

**금지 사례 — 컴파일이 안 되는 형태.** 문구까지는 위 4번 블록이 확인해 준다.

```text
{ a } = obj;                // 줄 첫머리의 { 가 블록으로 파싱된다 -- 괄호가 필요하다
const { a, a } = obj;       // 같은 이름을 두 번 선언할 수 없다
function f({ a }, { a }) {} // 매개변수 이름 중복 -- 비엄격에서도 막힌다
function f(a, { a }) {}     // 패턴 밖과 안이 겹쳐도 막힌다
const [a, ...r, b] = arr;   // 나머지는 마지막이어야 한다
const [...r = []] = arr;    // 나머지는 기본값을 못 가진다
const [...r,] = arr;        // 나머지 뒤에 꼬리 쉼표를 못 쓴다
```

규칙은 여덟이다.

1. **왼쪽은 값이 아니라 모양이다.** 그래서 중첩되고, 이름을 바꾸고, 기본값을 달 수 있다.
2. **배열 패턴은 이터레이터를, 객체 패턴은 프로퍼티 조회를 쓴다.** 그래서 받아들이는 값이 다르다.
3. **객체 패턴이 거부하는 값은 `null`·`undefined` 뿐이다.** 빈 패턴이어도 거부한다.
4. **배열 패턴은 이터러블만 받는다.** 유사 배열도 거부한다.
5. **기본값은 `undefined` 일 때만 쓰인다.** `null` 은 그대로 들어온다.
6. **객체 패턴은 패턴 순서대로 읽고, 배열 패턴은 필요한 만큼만 돌린 뒤 닫는다.**
7. **나머지는 반드시 마지막이고 기본값을 못 가진다.** 객체 나머지는 **자기 것이고 열거 가능한 것만** 얕게 복사한다.
8. **선언 없이 객체 패턴으로 대입하려면 괄호가 필요하다.** 비엄격이면 **암시적 전역**이 만들어진다.

## 어디서 틀리나

### (1) ★★★ 기본값이 `null` 도 막아 줄 거라고 믿는다

`const { a = 1 } = { a: null }` 은 **`null`** 이다. API 가 「없음」을 `null` 로 주면 기본값이 안 걸린다.
★ 고치는 법은 `a ?? 1` 이나 `a || 1` 이다 — 정본은 [목록의 **12번 주제**](../12-optional-chaining-nullish-and-logical-assignment/)다.

### (2) ★★★ 바깥 기본값과 안쪽 기본값을 헷갈린다

`function f({ a = 1 })` 은 `f()` 에서 **터진다.** `function f({ a = 1 } = {})` 이라야 안 터진다.
★ 안쪽은 「**키가 없을 때**」를, 바깥은 「**대상이 없을 때**」를 막는다.

### (3) ★★★ 「객체 패턴은 객체에만」이라고 믿는다

**숫자·문자열·불리언·함수·`Set` 에 전부 통한다.** `const { length } = "abc"` 가 `3` 이다.
★ 거부되는 것은 **`null`·`undefined` 둘뿐**이다.

### (4) ★★★ 배열 패턴이 유사 배열에도 통할 거라고 믿는다

**안 통한다.** `{ 0: 'x', length: 1 }` 은 `TypeError` 다.
★ `Array.from` 이나 `apply` 와 **서로 다른 문을 쓴다** — 그쪽은 유사 배열을 본다(09번).

### (5) ★★ 배열 패턴이 인덱스를 읽는다고 믿는다

**이터레이터를 돈다.** `Symbol.iterator` 를 바꿔 놓으면 다른 값이 나온다.
★ 그래서 **무한 이터러블에서도 안전하다** — 필요한 만큼만 돌고 닫는다.

### (6) ★★ getter 가 몇 번 불릴지 신경 안 쓴다

`{ ...all }` 은 **모든 getter 를 부른다.** 비싼 getter 가 있으면 필요한 키만 적는다.

### (7) ★★ 줄 첫머리에 `{` 를 쓴다

`{ a } = obj` 는 `SyntaxError` 다. 괄호로 감싼다 — `({ a } = obj)`.
★ 세미콜론을 안 쓰는 스타일에서는 **앞 줄과 붙어** 더 이상하게 깨진다.

### (8) ★ 선언 키워드를 빼먹는다

비엄격이면 **암시적 전역**이 조용히 만들어진다. 모듈은 항상 엄격이라 `ReferenceError` 다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- **객체 패턴이 `null`·`undefined` 만 거부하고 나머지는 전부 받는 것** — 빈 패턴이어도 거부한다.
- **배열 패턴이 이터러블만 받는 것** — 유사 배열은 거부한다.
- **기본값이 `undefined` 에만 걸리는 것.**
- **객체 패턴의 읽기 순서가 패턴 순서인 것**과 **나머지가 객체의 키 순서로 읽는 것.**
- **배열 패턴이 필요한 만큼만 `next` 를 부르고 끝나지 않았으면 `return()` 으로 닫는 것** — 예외로 끝날 때도 닫는다.
- **객체 나머지가 「자기 것이고 열거 가능한」 프로퍼티만 얕게 복사하는 것**(심볼 키 포함).
- **어떤 형태가 `SyntaxError` 인지** — 나머지의 자리, 중복 이름, 괄호 없는 객체 패턴.
- **패턴 매개변수가 `length` 한 자리로 세어지는 것.**

### 엔진(V8) 구현 · 이 판의 관찰

- ★★★ **예외 문구 전부.** 특히 **V8 은 그 자리의 소스 텍스트를 메시지에 넣는다** —
  같은 실패가 `v is not iterable` · `{} is not iterable` · `{(intermediate value)} is not iterable` 로 **다르게 나온다.**
  ★ **근거로 쓸 것은 `TypeError` 라는 종류**이지 문구가 아니다.
- ★★ **기본값이 붙으면 문구가 바뀌는 것** — `{ a } = null` 은 `Cannot destructure property ...`,
  `{ a = 'D' } = null` 은 `Cannot read properties of null (reading 'a')` 다. **종류는 같고 말이 다르다.**
- ★ **두 판에서 이 주제는 한 글자도 안 갈렸다.** 다만 **08번에서 갈린 전례가 있으므로** 보장으로 읽지 않는다.

### 호스트가 정하는 것 — ECMA-262 밖

- **없다.** 브라우저에 던진 열세 줄이 Node 와 전부 같았다(문구까지).
  ★ 같은 V8 이라 문구까지 같은 것이고, **다른 엔진에서는 문구가 다를 수 있다.**

### 그래서 이렇게 적으면 틀린다

| 이렇게 적으면 틀린다 | 이렇게 적어야 한다 |
|---|---|
| 「`{ a = 1 }` 은 `null` 도 막아 준다」 | `undefined` 에만 걸린다. `null` 은 그대로 온다 |
| 「객체 패턴은 객체에만 쓴다」 | `null`·`undefined` 만 거부한다. 원시값도 뜯어진다 |
| 「배열 패턴은 인덱스를 읽는다」 | 이터레이터를 돈다. `Symbol.iterator` 를 바꾸면 따라간다 |
| 「배열 패턴은 유사 배열도 받는다」 | 안 받는다. `Array.from`·`apply` 와 다른 문이다 |
| 「빈 패턴이면 안 터진다」 | `{} = null` 도 `[] = null` 도 터진다 |
| 「`TypeError: v is not iterable` 이 난다」 | **종류만** 근거다. 문구에는 소스 텍스트가 박힌다 |
| 「객체 나머지는 전부 복사한다」 | 비열거·상속은 안 오고, getter 는 값으로 굳는다. 얕다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓰는 모양 | 왜 |
|---|---|---|
| 선택 인자가 많은 함수 | `function f({ a = 1, b = 2 } = {})` | 호출부에서 이름이 보이고 순서를 안 외운다 |
| `Object.entries` 순회 | `for (const [k, v] of ...)` | 자리 둘이 고정이라 읽기 쉽다 |
| 배열 앞쪽만 필요할 때 | `const [head, ...tail] = arr` | 이터러블이면 무엇이든 된다 |
| 두 값 맞바꾸기 | `[a, b] = [b, a]` | 임시 변수가 없다 |
| 일부만 빼고 나머지를 넘길 때 | `const { secret, ...safe } = obj` | 한 줄로 뜻이 드러난다 |
| 응답의 일부만 쓸 때 | `const { data } = res ?? {}` | 대상이 `null` 일 수 있으면 먼저 막는다 |

**안 쓰는 쪽**

- **깊은 중첩 패턴을 쓰지 않는다** — `{ a: { b: { c } } }` 는 중간이 `undefined` 면 터지고, 어디서 터졌는지 문구로 알기 어렵다.
- **비싼 getter 가 있는 객체에 `{ ...rest }` 를 쓰지 않는다** — 전부 부른다.
- **`null` 이 올 수 있는 값에 바로 패턴을 대지 않는다** — `?? {}` 로 먼저 막는다.
- **구조 분해로 깊은 복사를 흉내 내지 않는다** — 얕다. 정본은 [목록의 **48번 주제**](../48-deep-copy-methods-compared/)다.

## 핵심 문장

- **왼쪽은 값이 아니라 모양이다** — 그래서 중첩되고 기본값이 붙고 이름이 바뀐다.
- **두 패턴은 서로 다른 문을 쓴다** — 객체 패턴은 프로퍼티 조회, 배열 패턴은 이터레이터.
- **받아들이는 값의 범위가 정반대로 넓고 좁다** — 객체 패턴은 둘만 거부하고 배열 패턴은 셋만 받았다.
- **기본값은 `undefined` 에만 걸린다** — 08번의 매개변수 기본값과 같은 규칙이다.
- **배열 패턴은 필요한 만큼만 돌고 닫는다** — 예외로 끝날 때도 닫는다.
- **예외 문구에는 소스 텍스트가 박힌다** — 근거로 쓸 것은 종류다.

## 관련 자료

- [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) — **원시값의 임시 래핑은 그쪽이 정본이고, 여기서는 그 덕에 `{ length } = "abc"` 가 되는 것만 본다.**
- [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) — **매개변수 목록을 단순하지 않게 만드는 셋 중 하나가 패턴이다.** 그쪽은 그 사실까지, 여기는 패턴의 규칙부터.
- [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) — **`apply` 는 유사 배열을 보고 배열 패턴은 이터러블을 본다.** 정반대의 문이다.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — **`...` 의 세 자리와 얕은 복사는 그쪽이 정본이고, 여기서는 패턴 안의 나머지만 다룬다.**
- [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/) 「이터러블 프로토콜과 `for...of`」 — **`Symbol.iterator` 계약은 그쪽이 정본이고, 여기서는 배열 패턴이 그것을 쓴다는 것까지.**
- [목록의 **12번 주제**](../12-optional-chaining-nullish-and-logical-assignment/) 「옵셔널 체이닝·널 병합·논리 할당」 — **`null` 을 막는 것은 그쪽이다.** 기본값으로는 안 된다.
- [목록의 **13번 주제**](../13-object-literals-and-properties/) 「객체 리터럴과 프로퍼티」 — **열거 순서 규칙은 그쪽이 정본이고, 여기서는 나머지가 그 순서로 읽는 것만 관찰한다.**
- [파이썬 갈래의 11번 「튜플과 언패킹」](../../../python/syntax/11-tuple-and-unpacking/) — **`a, *rest = seq` 가 배열 패턴과 닮았다.** 다만 파이썬에는 객체 패턴이 없다.

## 용어 풀이

- **구조 분해(destructuring)**: 왼쪽에 모양을 적어 오른쪽 값을 그 모양대로 뜯어 담는 것.
- **바인딩 패턴 / 할당 패턴**: 선언과 함께 쓰는 패턴(`const { a } = o`)과 이미 있는 이름에 대입하는 패턴(`({ a } = o)`).
- **배열 패턴**: `[a, b]`. **이터레이터 프로토콜**을 쓴다. 자리가 뜻을 정한다.
- **객체 패턴**: `{ a, b }`. **프로퍼티 조회**를 쓴다. 키가 뜻을 정한다.
- **나머지 원소 / 나머지 프로퍼티**: `[...r]` · `{ ...r }`. 반드시 마지막이고 기본값을 못 가진다.
- **유사 배열(array-like)**: `length` 와 인덱스 키를 가진 객체. **배열 패턴은 안 받는다.**
- **이터러블(iterable)**: `Symbol.iterator` 를 가진 값. **배열 패턴은 이것만 받는다.**
- **이터레이터 닫기(iterator close)**: 다 안 돌고 그만둘 때 `return()` 을 불러 주는 것.
- **얕은 복사(shallow copy)**: 한 겹만 새로 만들고 안쪽은 같은 객체를 가리키는 것.

## 더 들어가면

- **`Symbol.iterator` 를 구현해 자기 타입을 구조 분해 가능하게 만드는 것** — 정본은 [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/)다.
- **`for await (const [k, v] of ...)`** — 비동기 이터레이션에서도 같은 패턴 문법이 쓰인다. [목록의 **40번 주제**](../40-async-iteration-and-for-await/).
- **`catch ({ message })`** — `catch` 바인딩도 패턴을 받는다. [목록의 **32번 주제**](../32-error-handling-and-error/)가 정본이다.
- **정규식 명명 그룹 구조 분해** — `const { groups: { year } } = re.exec(s)`. [목록의 **30번 주제**](../30-regexp-advanced/).
- **패턴이 만드는 매개변수 스코프** — 08번의 `[5]` 가 그 관찰이다. 기본값 식이 붙드는 것은 본문의 `var` 가 아니다.
