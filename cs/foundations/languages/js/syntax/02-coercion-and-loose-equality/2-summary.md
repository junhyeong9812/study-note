# js/syntax/02 — 강제 변환과 `==` 대 `===`: 「엔진이 무엇을 먼저 부르나」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 추상 연산 `ToPrimitive`·`ToNumber`·`ToString`·`ToBoolean` 과 느슨한 비교 표
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — 판을 가려야 할 때
> - [MDN — Equality comparisons and sameness](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Equality_comparisons_and_sameness) · [MDN — `Symbol.toPrimitive`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/toPrimitive)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·호출 순서·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **`==` 격자는 손으로 채우지 않았다** — 15개 값을 서로 던져 **225칸**을 받았고, `===`·`Object.is` 까지 **675칸**이다.

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
> Node 의 스택트레이스에는 **절대 경로**가 박히기 때문이다. 이 주제의 블록은 전부 표준 출력이다.
>
> **버전** — `Object.is` 는 ES2015, `Symbol.toPrimitive` 도 ES2015. 느슨한 비교 표 자체는 초판부터 거의 그대로이고,
> **`BigInt` 가 들어오면서(ES2020) 표에 줄이 늘었다** — 그때 늘어난 줄이 이 문서의 `0n` 열이다.
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | **225칸 격자의 모든 칸** · **참인 칸의 개수** |
> | 예외 **문구**(판이 오르면 바뀐다) | **예외의 타입** · **`valueOf`/`toString` 의 호출 순서** |
> | `String(new Date(0))` — **시간대·로캘**에 달렸다. 그래서 표에서 뺐다 | **`Symbol.toPrimitive` 가 받는 힌트 문자열**(`default`·`number`·`string`) |
> | 브라우저 UA 문자열의 뒷자리 | **`+` 가 문자열로 기우는 것** · 종료 코드 |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다** — `Date` 를 표에서 뺀 이유가 그것이다.
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(**원시 7종과 객체의 정본** · falsy 목록 · `document.all`)
> **이어지는 곳** — [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md) · [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)
>
> ★★ **경계 — 타입 검사 이야기는 여기가 아니다.** TypeScript 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **01번** [`01-what-ts-adds-and-erases`](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md)가
> 「타입은 런타임에 안 남는다」의 정본이다. TS 는 `==` 를 **정적으로 막을 수** 있지만, **막지 못하고 통과한 `==` 가 런타임에 무엇을 하는가**는 여기가 정본이다.

## 한눈에 — 쉽게 말하면

**`==` 는 「타입이 다르면 맞춰 보고 다시 묻는다」이고 `===` 는 「타입이 다르면 그 자리에서 아니다」이다.**

전화로 번호를 확인한다고 하자.
「일이삼사」라고 말한 사람과 「1234」라고 적어 낸 사람이 있다.

- **`===`** 는 「한 사람은 말했고 한 사람은 적었으니 형식이 다르다 — 아니다」라고 끊는다.
- **`==`** 는 「둘 다 숫자로 바꿔 보자」 하고 맞춰 본 뒤 「같다」고 한다.
- 문제는 **맞추는 규칙이 하나가 아니라 표**라는 것이다. 그 표에 이상한 칸이 몇 개 있다.

```text
   x == y  가 하는 일 (타입이 다를 때)

   undefined 와 null  --------> ★ 서로만 같다. 다른 어떤 것과도 안 같다
   숫자 와 문자열      --------> 문자열을 숫자로
   불리언이 한쪽       --------> 불리언을 먼저 숫자로 (true -> 1, false -> 0)
   BigInt 와 숫자/문자열 ------> 수학적 값으로 견준다
   객체가 한쪽         --------> ★ ToPrimitive 로 객체를 원시 값으로 만든 뒤 다시 묻는다
   그 밖               --------> false

   ★ 그래서 [] == false 가 true 다 —  [] -> "" -> 0  와  false -> 0
   ★ 그래서 NaN 은 어떤 칸에서도 참이 안 된다 — 자기 자신과도.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 형식이 다르면 그냥 끊는다 | `===` (엄격 동등) | 타입이 다르면 무조건 `false` |
| 맞춰 보고 다시 묻는다 | `==` (느슨한 동등) | 표대로 한쪽을 바꾼 뒤 재귀적으로 다시 비교 |
| 봉투를 열어 「알맹이」를 꺼내는 절차 | `ToPrimitive` | `valueOf`/`toString` 에 로그를 심으면 보인다 |
| 「숫자로 꺼내 주세요」라는 쪽지 | 힌트 `number` | `Symbol.toPrimitive` 의 인자로 찍힌다 |
| 「글자로 꺼내 주세요」라는 쪽지 | 힌트 `string` | 템플릿·`String()`·프로퍼티 키 자리 |
| 쪽지가 없으면 숫자처럼 | 힌트 `default` | `+` 와 `==` 가 이 쪽지를 보낸다 |
| 봉투에 붙은 전용 창구 | `Symbol.toPrimitive` | 있으면 나머지 둘을 **아예 안 부른다** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 하나로 굳어 있다.
`if (userInput == 0)` 에 빈 문자열이 들어오면 **참**이 되고, `[]` 가 들어와도 **참**이 된다.
`total = price + quantity` 에서 하나가 문자열이면 **덧셈이 이어붙이기로 바뀐다.**
둘 다 **에러가 안 나고 값만 틀린다** — 이 주제의 값이 전부 거기 있다.

> **강제 변환(coercion)** — 연산자가 필요해서 **말없이** 타입을 바꾸는 것.
> 예: `"1" * 2` 가 `2` 인 것. `Number("1")` 처럼 **내가 부르는 것**은 명시적 변환이다.

> **추상 연산(abstract operation)** — 명세가 규칙을 적기 위해 쓰는 내부 절차.
> 예: `ToPrimitive`·`ToNumber`. **코드에서 이름으로 부를 수는 없지만**, 그것이 부르는 메서드에 로그를 심으면 **관찰할 수 있다.**

## 이 주제가 답하려는 질문

1. **객체를 원시 값으로 바꿀 때 엔진이 무엇을 어느 순서로 부르는가** — 로그를 심어 직접 본다.
2. **`==` 표의 이상한 칸들이 어디서 오는가** — 225칸을 전수로 던져 채운다.
3. **`==` 를 써도 되는 자리가 있는가** — 하나 있다.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### (1) ★★★ 추상 연산에 로그를 심는다 — `ToPrimitive` 가 무엇을 부르나

**언제 쓰나** — 객체가 연산자를 만나는 모든 자리. `+`·`-`·`<`·`==`·템플릿·프로퍼티 키.

`ToPrimitive` 는 명세 안에만 있는 절차라 이름으로 부를 수가 없다.
그런데 **그것이 부르는 메서드는 내가 만든 객체의 것**이다 — 거기에 로그를 심으면 **순서가 그대로 찍힌다.**

```text
   ToPrimitive(객체, 힌트) 가 하는 일

   힌트는 세 가지다:  "number" | "string" | "default"

         객체에 [Symbol.toPrimitive] 가 있나?
                |
        있다 ---+--- 없다
         |            |
   그것 하나만 부른다   힌트가 "string" 이면   toString -> valueOf 순서
   (원시 값이 아니면    아니면(number/default) valueOf -> toString 순서
    TypeError)              |
                            v
                   앞엣것이 원시 값을 주면 거기서 끝.
                   아니면 뒤엣것을 부른다.
                   둘 다 객체를 주면 ★ TypeError.
```

```js
// js01b-02a-toprimitive-spy.js
// 객체를 원시 값으로 바꿀 때 엔진이 무엇을 어느 순서로 부르는지 로그로 찍는다.
// ★ 명세의 추상 연산(ToPrimitive)에는 이름이 없지만, 그것이 부르는 메서드에는 로그를 심을 수 있다.
function makeSpy({ valueOfResult, toStringResult, symbolResult }) {
  const log = [];
  const o = {
    valueOf()  { log.push("valueOf()");  return valueOfResult; },
    toString() { log.push("toString()"); return toStringResult; },
  };
  if (symbolResult !== undefined) {
    o[Symbol.toPrimitive] = (hint) => {
      log.push("[Symbol.toPrimitive](\"" + hint + "\")");
      return symbolResult;
    };
  }
  return [o, log];
}

function run(label, opts, use) {
  const [o, log] = makeSpy(opts);
  let out;
  try { out = String(use(o)); }
  catch (e) { out = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(22) + " => " + out.padEnd(18) + " | 부른 것: " + (log.join(" -> ") || "(없음)"));
}

const N = { valueOfResult: 7, toStringResult: "S" };

console.log("[1] 힌트가 number 인 자리 — valueOf 가 먼저다");
run("o * 2",        N, (o) => o * 2);
run("o - 0",        N, (o) => o - 0);
run("o < 1",        N, (o) => o < 1);
run("Number(o)",    N, (o) => Number(o));
run("+o",           N, (o) => +o);

console.log("");
console.log("[2] 힌트가 string 인 자리 — toString 이 먼저다");
run("`${o}`",       N, (o) => `${o}`);
run("String(o)",    N, (o) => String(o));
run("({})[o] = 1",  N, (o) => { const t = {}; t[o] = 1; return Object.keys(t)[0]; });
run("[o] + ''",     N, (o) => [o] + "");

console.log("");
console.log("[3] 힌트가 default 인 자리 — 기본 객체는 number 처럼 군다");
run("o + 1",        N, (o) => o + 1);
run("o + 'x'",      N, (o) => o + "x");
run("o == 7",       N, (o) => o == 7);

console.log("");
console.log("[4] 첫 메서드가 원시 값을 안 돌려주면 다음 것을 부른다");
run("valueOf -> obj",   { valueOfResult: {}, toStringResult: "S" }, (o) => o + 1);
run("toString -> obj",  { valueOfResult: 7,  toStringResult: {} },  (o) => `${o}`);
run("both -> obj",      { valueOfResult: {}, toStringResult: {} },  (o) => o + 1);

console.log("");
console.log("[5] Symbol.toPrimitive 가 있으면 나머지 둘은 아예 안 불린다");
run("o + 1",        { ...N, symbolResult: 99 }, (o) => o + 1);
run("`${o}`",       { ...N, symbolResult: 99 }, (o) => `${o}`);
run("o * 2",        { ...N, symbolResult: 99 }, (o) => o * 2);
```

```text
===== node20 js01b-02a-toprimitive-spy.js (exit=0) =====
[1] 힌트가 number 인 자리 — valueOf 가 먼저다
  o * 2                  => 14                 | 부른 것: valueOf()
  o - 0                  => 7                  | 부른 것: valueOf()
  o < 1                  => false              | 부른 것: valueOf()
  Number(o)              => 7                  | 부른 것: valueOf()
  +o                     => 7                  | 부른 것: valueOf()

[2] 힌트가 string 인 자리 — toString 이 먼저다
  `${o}`                 => S                  | 부른 것: toString()
  String(o)              => S                  | 부른 것: toString()
  ({})[o] = 1            => S                  | 부른 것: toString()
  [o] + ''               => S                  | 부른 것: toString()

[3] 힌트가 default 인 자리 — 기본 객체는 number 처럼 군다
  o + 1                  => 8                  | 부른 것: valueOf()
  o + 'x'                => 7x                 | 부른 것: valueOf()
  o == 7                 => true               | 부른 것: valueOf()

[4] 첫 메서드가 원시 값을 안 돌려주면 다음 것을 부른다
  valueOf -> obj         => S1                 | 부른 것: valueOf() -> toString()
  toString -> obj        => 7                  | 부른 것: toString() -> valueOf()
  both -> obj            => TypeError: Cannot convert object to primitive value | 부른 것: valueOf() -> toString()

[5] Symbol.toPrimitive 가 있으면 나머지 둘은 아예 안 불린다
  o + 1                  => 100                | 부른 것: [Symbol.toPrimitive]("default")
  `${o}`                 => 99                 | 부른 것: [Symbol.toPrimitive]("string")
  o * 2                  => 198                | 부른 것: [Symbol.toPrimitive]("number")
```

그림 해설 (한 단계씩).

- ★★★ **`[1]` 과 `[2]` 가 정확히 갈린다.** 산술·비교 자리에서는 `valueOf` 가, 문자열이 필요한 자리에서는 `toString` 이 먼저다.
  **어느 쪽이 먼저 불렸는지가 로그에 그대로 찍혀 있다** — 추측이 아니다.
- ★★★ **`o + 1` 과 `o == 7` 이 `valueOf` 를 부른다.** 힌트가 `default` 인데 **기본 객체는 `default` 를 `number` 처럼** 다룬다.
  ★ 「`+` 는 문자열 쪽이니 `toString` 을 부르겠지」는 **틀린 예측**이다 — `+` 가 문자열로 기우는 것은
  **ToPrimitive 가 끝난 다음** 단계의 일이다(4번 절).
- ★★ **`[o] + ''` 는 `toString` 을 부른다.** 배열을 문자열로 만들 때 원소마다 `String()` 을 부르기 때문에
  **힌트가 `string` 으로 바뀐다.** 한 겹만 감쌌는데 순서가 뒤집힌다.
- ★★ **`({})[o] = 1` 도 `toString`** 이다. 프로퍼티 키 자리는 문자열을 원한다.
- ★★★ **`[4]` 가 「원시 값이 아니면 다음 것」 규칙을 보여 준다.** `valueOf` 가 객체를 돌려주자 `toString` 을 이어 불렀고,
  **둘 다 객체를 주자 `TypeError: Cannot convert object to primitive value`** 다.
  ★ 두 메서드를 **다 부르고 나서야** 터진다 — 로그에 둘 다 찍혀 있다.
- ★★★ **`[5]` 에서 `Symbol.toPrimitive` 가 나머지 둘을 완전히 덮는다.** `valueOf` 도 `toString` 도 **한 번도 안 불렸다.**
  그리고 **힌트가 인자로 넘어온다** — `default`·`string`·`number` 세 글자가 그대로 찍혔다.

**비용** — 객체를 숫자·문자열 자리에 그냥 놓을 수 있고, `Symbol.toPrimitive` 로 그 동작을 내가 정할 수 있다.
대신 **어느 메서드가 불릴지가 문맥에 달려 있어서** 같은 객체가 자리마다 다른 값이 된다.

### (2) `Date` 가 반대로 구는 진짜 이유 — 순서가 바뀐 게 아니다

**언제 쓰나** — `date + 1` 과 `date - 0` 이 다른 타입을 내는 것을 설명할 때.

```text
   흔한 설명 (틀렸다)            실제 (명세)

   "Date 는 valueOf 와          Date.prototype 에는 제 [Symbol.toPrimitive] 가 있고,
    toString 의 순서가          그것이 힌트 "default" 를 "string" 으로 바꿔 버린다.
    뒤바뀌어 있다"                    |
                                     +-- "default" -> 문자열로
                                     +-- "string"  -> 문자열로
                                     +-- "number"  -> 숫자로
                                     +-- 그 밖      -> ★ TypeError

   ★ 순서가 뒤집힌 게 아니라 "쪽지를 갈아 끼운" 것이다.
```

```js
// js01b-02b-date-hint.js
// Date 는 왜 반대로 구는가 — "valueOf 와 toString 의 순서가 바뀐 것" 이 아니다.
class Logged extends Date {
  valueOf()  { console.log("      valueOf() 가 불렸다");  return super.valueOf(); }
  toString() { console.log("      toString() 이 불렸다"); return super.toString(); }
}

console.log("[1] Date 는 무엇을 부르나");
const d = new Logged(0);
console.log("  d + 1   ->"); void (d + 1);
console.log("  d * 1   ->"); void (d * 1);
console.log("  d - 0   ->"); void (d - 0);
console.log("  `${d}`  ->"); void `${d}`;

console.log("");
console.log("[2] 그래서 같은 연산자가 타입을 다르게 낸다");
const plain = new Date(0);
console.log("  typeof (date + 1) :", typeof (plain + 1));
console.log("  typeof (date - 0) :", typeof (plain - 0));
console.log("  typeof ({} + 1)   :", typeof ({ valueOf: () => 1 } + 1));

console.log("");
console.log("[3] 진짜 이유 — Date 에는 제 Symbol.toPrimitive 가 있다");
console.log("  typeof Date.prototype[Symbol.toPrimitive] :", typeof Date.prototype[Symbol.toPrimitive]);
console.log("  typeof Object.prototype[Symbol.toPrimitive]:", typeof Object.prototype[Symbol.toPrimitive]);
const f = Date.prototype[Symbol.toPrimitive];
console.log('  hint "default" 로 직접 부르면 타입이 :', typeof f.call(plain, "default"));
console.log('  hint "number"  로 직접 부르면 타입이 :', typeof f.call(plain, "number"));
console.log('  hint "string"  로 직접 부르면 타입이 :', typeof f.call(plain, "string"));
let bad;
try { f.call(plain, "nope"); } catch (e) { bad = e.constructor.name + ": " + e.message; }
console.log('  hint "nope"    로 부르면 :', bad);
```

```text
===== node20 js01b-02b-date-hint.js (exit=0) =====
[1] Date 는 무엇을 부르나
  d + 1   ->
      toString() 이 불렸다
  d * 1   ->
      valueOf() 가 불렸다
  d - 0   ->
      valueOf() 가 불렸다
  `${d}`  ->
      toString() 이 불렸다

[2] 그래서 같은 연산자가 타입을 다르게 낸다
  typeof (date + 1) : string
  typeof (date - 0) : number
  typeof ({} + 1)   : number

[3] 진짜 이유 — Date 에는 제 Symbol.toPrimitive 가 있다
  typeof Date.prototype[Symbol.toPrimitive] : function
  typeof Object.prototype[Symbol.toPrimitive]: undefined
  hint "default" 로 직접 부르면 타입이 : string
  hint "number"  로 직접 부르면 타입이 : number
  hint "string"  로 직접 부르면 타입이 : string
  hint "nope"    로 부르면 : TypeError: Invalid hint: nope
```

그림 해설.

- ★★★ **`d + 1` 이 `toString` 을, `d * 1` 이 `valueOf` 를 부른다.** 여기까지는 「순서가 반대」처럼 보인다.
- ★★★ **`[3]` 이 진짜 이유를 보여 준다.** `Date.prototype[Symbol.toPrimitive]` 가 **존재**하고
  `Object.prototype` 에는 **없다.** 그 함수를 직접 힌트를 바꿔 가며 불러 보면
  **`default` 와 `string` 이 둘 다 문자열을, `number` 만 숫자를** 준다.
- ★★ **없는 힌트를 주면 `TypeError: Invalid hint: nope`** 다. 힌트가 세 글자로 닫혀 있다는 관찰이다.
- ★ 그래서 `typeof (date + 1)` 이 `"string"` 이고 `typeof (date - 0)` 이 `"number"` 다.
  **`-` 는 힌트를 `number` 로 보내므로** 갈아 끼울 것이 없다.
- ★★ **1번 절의 규칙이 깨진 것이 아니다** — `Symbol.toPrimitive` 가 있으면 그것만 부른다는 규칙이 **그대로 적용된** 결과다.

**비용** — `date + ""` 로 사람이 읽을 날짜를 얻을 수 있다.
대신 **`date1 - date2` 는 밀리초 차이인데 `date1 + date2` 는 문자열 두 개를 이어붙인다.** 같은 두 값에 두 연산자가 전혀 다른 일을 한다.

### (3) ★★★ 격자를 전수로 던진다 — 225칸 × 세 연산자

**언제 쓰나** — 「이 비교가 참인가」를 외우는 대신 **표를 읽는 법**을 익힐 때.

```js
// js01b-02c-equality-grids.js
// == · === · Object.is 를 같은 15개 값으로 전수 대조한다. 한 격자가 225칸이다.
// ★ 값은 매번 새로 만든다(thunk) — 그래야 [] 끼리가 "다른 객체" 로 비교된다.
const V = [
  ["undef", () => undefined], ["null", () => null],
  ["false", () => false],     ["true", () => true],
  ["0", () => 0],             ["-0", () => -0],        ["1", () => 1],
  ['""', () => ""],           ['"0"', () => "0"],      ['"1"', () => "1"],
  ["NaN", () => NaN],
  ["[]", () => []],           ["[0]", () => [0]],      ["{}", () => ({})],
  ["0n", () => 0n],
];
const W = 6, C = 6;

function grid(title, cmp) {
  console.log("[" + title + "]  T = 참 · . = 거짓 · ! = 예외");
  console.log(" ".repeat(W) + V.map(([n]) => n.padStart(C)).join(""));
  let yes = 0, cells = 0, thrown = 0;
  for (const [an, af] of V) {
    let row = an.padEnd(W);
    for (const [, bf] of V) {
      let mark;
      try { mark = cmp(af(), bf()) ? "T" : "."; }
      catch { mark = "!"; thrown++; }
      if (mark === "T") yes++;
      cells++;
      row += mark.padStart(C);
    }
    console.log(row);
  }
  console.log("  " + cells + "칸 중 참 " + yes + "칸 · 예외 " + thrown + "칸");
  console.log("");
  return cells;
}

let total = 0;
total += grid("==",        (a, b) => a == b);
total += grid("===",       (a, b) => a === b);
total += grid("Object.is", (a, b) => Object.is(a, b));
console.log("던진 칸 합계: " + total);
```

```text
===== node20 js01b-02c-equality-grids.js (exit=0) =====
[==]  T = 참 · . = 거짓 · ! = 예외
       undef  null false  true     0    -0     1    ""   "0"   "1"   NaN    []   [0]    {}    0n
undef      T     T     .     .     .     .     .     .     .     .     .     .     .     .     .
null       T     T     .     .     .     .     .     .     .     .     .     .     .     .     .
false      .     .     T     .     T     T     .     T     T     .     .     T     T     .     T
true       .     .     .     T     .     .     T     .     .     T     .     .     .     .     .
0          .     .     T     .     T     T     .     T     T     .     .     T     T     .     T
-0         .     .     T     .     T     T     .     T     T     .     .     T     T     .     T
1          .     .     .     T     .     .     T     .     .     T     .     .     .     .     .
""         .     .     T     .     T     T     .     T     .     .     .     T     .     .     T
"0"        .     .     T     .     T     T     .     .     T     .     .     .     T     .     T
"1"        .     .     .     T     .     .     T     .     .     T     .     .     .     .     .
NaN        .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
[]         .     .     T     .     T     T     .     T     .     .     .     .     .     .     T
[0]        .     .     T     .     T     T     .     .     T     .     .     .     .     .     T
{}         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
0n         .     .     T     .     T     T     .     T     T     .     .     T     T     .     T
  225칸 중 참 67칸 · 예외 0칸

[===]  T = 참 · . = 거짓 · ! = 예외
       undef  null false  true     0    -0     1    ""   "0"   "1"   NaN    []   [0]    {}    0n
undef      T     .     .     .     .     .     .     .     .     .     .     .     .     .     .
null       .     T     .     .     .     .     .     .     .     .     .     .     .     .     .
false      .     .     T     .     .     .     .     .     .     .     .     .     .     .     .
true       .     .     .     T     .     .     .     .     .     .     .     .     .     .     .
0          .     .     .     .     T     T     .     .     .     .     .     .     .     .     .
-0         .     .     .     .     T     T     .     .     .     .     .     .     .     .     .
1          .     .     .     .     .     .     T     .     .     .     .     .     .     .     .
""         .     .     .     .     .     .     .     T     .     .     .     .     .     .     .
"0"        .     .     .     .     .     .     .     .     T     .     .     .     .     .     .
"1"        .     .     .     .     .     .     .     .     .     T     .     .     .     .     .
NaN        .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
[]         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
[0]        .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
{}         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
0n         .     .     .     .     .     .     .     .     .     .     .     .     .     .     T
  225칸 중 참 13칸 · 예외 0칸

[Object.is]  T = 참 · . = 거짓 · ! = 예외
       undef  null false  true     0    -0     1    ""   "0"   "1"   NaN    []   [0]    {}    0n
undef      T     .     .     .     .     .     .     .     .     .     .     .     .     .     .
null       .     T     .     .     .     .     .     .     .     .     .     .     .     .     .
false      .     .     T     .     .     .     .     .     .     .     .     .     .     .     .
true       .     .     .     T     .     .     .     .     .     .     .     .     .     .     .
0          .     .     .     .     T     .     .     .     .     .     .     .     .     .     .
-0         .     .     .     .     .     T     .     .     .     .     .     .     .     .     .
1          .     .     .     .     .     .     T     .     .     .     .     .     .     .     .
""         .     .     .     .     .     .     .     T     .     .     .     .     .     .     .
"0"        .     .     .     .     .     .     .     .     T     .     .     .     .     .     .
"1"        .     .     .     .     .     .     .     .     .     T     .     .     .     .     .
NaN        .     .     .     .     .     .     .     .     .     .     T     .     .     .     .
[]         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
[0]        .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
{}         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
0n         .     .     .     .     .     .     .     .     .     .     .     .     .     .     T
  225칸 중 참 12칸 · 예외 0칸

던진 칸 합계: 675
```

그림 해설.

- ★★★ **`==` 는 225칸 중 67칸이 참**이고 **`===` 는 13칸**, **`Object.is` 는 12칸**이다.
  `===` 와 `Object.is` 가 **한 칸 차이**로 보이지만 **갈린 칸은 둘**이다 — 하나가 줄고 하나가 늘었다.
- ★★★ **`===` 와 `Object.is` 가 갈리는 두 자리**는 대각선 위에 있다 —
  `0`/`-0` 은 `===` 로 같고 `Object.is` 로 다르며, `NaN`/`NaN` 은 그 반대다.
  ★ **표의 `NaN` 행이 `===` 에서 통째로 비어 있다** — 자기 자신과도 안 같다.
- ★★★ **`==` 의 `false` 행이 가장 넓다** — `0`·`-0`·`""`·`"0"`·`[]`·`[0]`·`0n` 이 전부 참이다.
  **`false` 는 먼저 `0` 이 되고**, 오른쪽도 숫자가 되어 견줘지기 때문이다.
- ★★★ **`undefined` 와 `null` 은 서로만 같다.** 두 행·두 열이 **대각선 2×2 블록** 하나를 이룬다.
  `0` 과도 `""` 와도 `false` 와도 안 같다 — **표에 그 줄만 따로 있다.**
- ★★ **`[]` 와 `[]` 는 `==` 로도 다르다.** 양쪽이 다 객체면 **ToPrimitive 를 아예 안 하고 참조만** 본다.
  ★ 그래서 `[] == 0` 은 참인데 `[] == []` 는 거짓이다 — **한쪽만 객체일 때만** 변환이 일어난다.
- ★★ **`0n` 행이 `0` 행과 똑같다.** BigInt 와 Number 는 `==` 에서 **수학적 값**으로 견줘진다.
  그런데 **`===` 에서는 `0n === 0` 이 거짓**이다(타입이 다르다) — 03번 주제의 자리다.
- ★ **예외 칸이 0개다.** `==` 는 어떤 조합에서도 안 터진다 — **그래서 조용히 틀린다.**

**비용** — 표 하나로 모든 조합이 정의돼 있어 **엔진마다 다를 여지가 없다.**
대신 **표가 사람의 직관과 안 맞는 칸을 여럿 갖고 있고**, 그 칸들은 웹 호환 때문에 **영원히 안 고쳐진다.**

### (4) 유명한 식들을 한 줄씩 무너뜨린다

**언제 쓰나** — 면접·퀴즈에 나오는 식들을 **외우지 않고 유도**할 때.

```js
// js01b-02d-famous.js
// 유명한 식들을 "중간 단계까지" 찍어 한 줄씩 무너뜨린다.
const show = (expr, value, steps) =>
  console.log("  " + expr.padEnd(20) + " = " + String(value).padEnd(7) + " | " + steps);

console.log("[1] [] == false");
show("![]",        ![],        "ToBoolean([]) 은 true 라서 !true = false");
show("[] == false", [] == false, "false -> 0 · [] -> ToPrimitive -> '' -> 0");
show("[].toString()", JSON.stringify([].toString()), "빈 배열의 toString 은 빈 문자열");
show("Number('')",  Number(""),  "빈 문자열의 ToNumber 는 0");
show("[] == ![]",  [] == ![],   "오른쪽이 false 가 되므로 위와 같은 식이 된다");
show("[] == []",   [] == [],    "둘 다 객체라 ToPrimitive 를 안 하고 참조만 본다");

console.log("");
console.log("[2] null 과 undefined 는 서로만 같다");
for (const [e, v] of [["null == undefined", null == undefined], ["null === undefined", null === undefined],
                      ["null == 0", null == 0], ["null >= 0", null >= 0], ["null > 0", null > 0],
                      ["null <= 0", null <= 0], ["undefined == 0", undefined == 0], ["Number(null)", Number(null)],
                      ["Number(undefined)", Number(undefined)]])
  console.log("  " + e.padEnd(20) + " = " + v);

console.log("");
console.log("[3] NaN 은 자기 자신과도 다르다");
for (const [e, v] of [["NaN == NaN", NaN == NaN], ["NaN === NaN", NaN === NaN],
                      ["Object.is(NaN,NaN)", Object.is(NaN, NaN)], ["[NaN].includes(NaN)", [NaN].includes(NaN)],
                      ["[NaN].indexOf(NaN)", [NaN].indexOf(NaN)], ["new Set([NaN,NaN]).size", new Set([NaN, NaN]).size]])
  console.log("  " + e.padEnd(24) + " = " + v);

console.log("");
console.log("[4] + 는 한쪽이 문자열이면 문자열로 기운다 — 나머지는 안 그렇다");
for (const [e, v] of [["1 + '2'", 1 + "2"], ["1 - '2'", 1 - "2"], ["1 * '2'", 1 * "2"],
                      ["'3' + null", "3" + null], ["3 - null", 3 - null],
                      ["[1,2] + [3]", [1, 2] + [3]], ["{} + []", ({}) + []],
                      ["1 + 2 + '3'", 1 + 2 + "3"], ["'1' + 2 + 3", "1" + 2 + 3],
                      ["true + true", true + true], ["'b' + 'a' + +'a' + 'a'", "b" + "a" + +"a" + "a"]])
  console.log("  " + e.padEnd(24) + " = " + JSON.stringify(v));

console.log("");
console.log("[5] 관계 연산자는 문자열 둘이면 사전순이다");
for (const [e, v] of [["'10' < '9'", "10" < "9"], ["10 < 9", 10 < 9], ["'10' < 9", "10" < 9],
                      ["[] < [1]", [] < [1]], ["'a' < 'b'", "a" < "b"],
                      ["NaN < 1", NaN < 1], ["NaN >= 1", NaN >= 1]])
  console.log("  " + e.padEnd(24) + " = " + v);
```

```text
===== node20 js01b-02d-famous.js (exit=0) =====
[1] [] == false
  ![]                  = false   | ToBoolean([]) 은 true 라서 !true = false
  [] == false          = true    | false -> 0 · [] -> ToPrimitive -> '' -> 0
  [].toString()        = ""      | 빈 배열의 toString 은 빈 문자열
  Number('')           = 0       | 빈 문자열의 ToNumber 는 0
  [] == ![]            = true    | 오른쪽이 false 가 되므로 위와 같은 식이 된다
  [] == []             = false   | 둘 다 객체라 ToPrimitive 를 안 하고 참조만 본다

[2] null 과 undefined 는 서로만 같다
  null == undefined    = true
  null === undefined   = false
  null == 0            = false
  null >= 0            = true
  null > 0             = false
  null <= 0            = true
  undefined == 0       = false
  Number(null)         = 0
  Number(undefined)    = NaN

[3] NaN 은 자기 자신과도 다르다
  NaN == NaN               = false
  NaN === NaN              = false
  Object.is(NaN,NaN)       = true
  [NaN].includes(NaN)      = true
  [NaN].indexOf(NaN)       = -1
  new Set([NaN,NaN]).size  = 1

[4] + 는 한쪽이 문자열이면 문자열로 기운다 — 나머지는 안 그렇다
  1 + '2'                  = "12"
  1 - '2'                  = -1
  1 * '2'                  = 2
  '3' + null               = "3null"
  3 - null                 = 3
  [1,2] + [3]              = "1,23"
  {} + []                  = "[object Object]"
  1 + 2 + '3'              = "33"
  '1' + 2 + 3              = "123"
  true + true              = 2
  'b' + 'a' + +'a' + 'a'   = "baNaNa"

[5] 관계 연산자는 문자열 둘이면 사전순이다
  '10' < '9'               = true
  10 < 9                   = false
  '10' < 9                 = false
  [] < [1]                 = true
  'a' < 'b'                = true
  NaN < 1                  = false
  NaN >= 1                 = false
```

그림 해설.

- ★★★ **`[] == ![]` 가 참인 것은 두 규칙이 겹친 결과**다.
  `![]` 는 **ToBoolean** 을 거친다 — **객체는 전부 참**이므로 `![]` 는 `false` 다(01번 주제).
  그다음은 `[] == false` 이고, `false` 가 `0` 이 되고 `[]` 가 `""` 를 거쳐 `0` 이 된다.
  ★ **`==` 와 `!` 가 서로 다른 변환을 쓴다**는 것이 요점이다.
- ★★★ **`null == 0` 은 거짓인데 `null >= 0` 은 참이다.**
  `==` 는 `null` 에 **전용 줄**을 갖고 있어 숫자로 안 바꾸고, 관계 연산자(`<`·`>`·`<=`·`>=`)에는 그 줄이 없어
  `null` 이 `0` 으로 바뀐다. ★ **같은 값에 두 연산자가 다른 표를 쓴다.**
- ★★ **`NaN` 은 `==`·`===` 로 안 같은데 `includes` 와 `Set` 은 같다고 본다.**
  `indexOf` 만 `===` 를 쓰고 나머지는 **SameValueZero** 라는 셋째 규칙을 쓴다 —
  ★ **동등성 규칙이 셋이다**(33번 주제가 정본).
- ★★★ **`+` 만 문자열로 기운다.** `1 + '2'` 는 `"12"` 인데 `1 - '2'` 는 `-1` 이고 `1 * '2'` 는 `2` 다.
  ★ **ToPrimitive 가 끝난 뒤**, 한쪽이 문자열이면 `+` 는 이어붙이기로 간다 — 1번 절의 `valueOf` 호출과 **다른 단계**다.
- ★★ **`1 + 2 + '3'` 은 `"33"` 이고 `'1' + 2 + 3` 은 `"123"`** 이다. 왼쪽부터 접히므로 **문자열이 언제 들어오는지**가 결과를 가른다.
- ★ **`'10' < '9'` 가 참이다.** 양쪽이 문자열이면 숫자로 안 바꾸고 **코드 유닛 순서**로 견준다(04번 주제).
- ★ **`NaN < 1` 도 `NaN >= 1` 도 둘 다 거짓**이다. 관계 연산자는 **참·거짓 말고** 「모르겠다」 를 표에 갖고 있고, 그것이 전부 거짓으로 떨어진다.

**비용** — 규칙이 표로 닫혀 있어 **유도할 수 있다** — 외울 필요가 없다.
대신 **유도할 줄 모르면 전부 마법으로 보이고**, 그 상태로 `==` 를 쓰면 사고가 난다.

### (5) 세 방향 변환표 — falsy 목록과 `== false` 목록은 다르다

**언제 쓰나** — `if (x)` 와 `x == false` 를 같은 질문으로 쓰고 있을 때.

```js
// js01b-02e-conversion-table.js
// 같은 값을 세 방향으로 바꿔 본다 — ToNumber · ToString · ToBoolean.
// ★ "falsy 목록" 과 "== false 인 목록" 이 같지 않다는 것이 이 표의 요점이다.
// ★ Date 는 일부러 뺐다 — String(new Date(0)) 이 시간대·로캘에 달려 흔들리는 칸이기 때문이다.
const V = [
  ["undefined", undefined], ["null", null], ["true", true], ["false", false],
  ["0", 0], ["-0", -0], ["1", 1], ["NaN", NaN], ["Infinity", Infinity],
  ['""', ""], ['" "', " "], ['"0"', "0"], ['"12"', "12"], ['"0x10"', "0x10"],
  ['"1e3"', "1e3"], ['"12px"', "12px"], ['"Infinity"', "Infinity"],
  ["[]", []], ["[7]", [7]], ["[1,2]", [1, 2]], ["{}", {}],
  ["0n", 0n], ["1n", 1n],
];
const cell = (f) => { try { return String(f()); } catch (e) { return "!" + e.constructor.name; } };

console.log("value".padEnd(12) + "Number()".padEnd(14) + "String()".padEnd(24) +
            "Boolean()".padEnd(11) + "== false");
console.log("-".repeat(12 + 14 + 24 + 11 + 8));
let falsy = 0, eqFalse = 0;
for (const [label, v] of V) {
  const b = Boolean(v), e = cell(() => v == false);
  if (!b) falsy++;
  if (e === "true") eqFalse++;
  console.log(label.padEnd(12) +
              cell(() => Number(v)).padEnd(14) +
              JSON.stringify(cell(() => String(v))).padEnd(24) +
              String(b).padEnd(11) + e);
}
console.log("");
const falsyOnly  = V.filter(([, v]) => !Boolean(v) && !(v == false)).map(([n]) => n);
const eqFalseOnly = V.filter(([, v]) => Boolean(v) && (v == false)).map(([n]) => n);
const both        = V.filter(([, v]) => !Boolean(v) && (v == false)).map(([n]) => n);
console.log("falsy 인데 `== false` 는 거짓 :", falsyOnly.join(" "));
console.log("truthy 인데 `== false` 가 참   :", eqFalseOnly.join(" "));
console.log("둘 다 인 것                    :", both.join(" "));
console.log("");
console.log("★ 두 목록은 같지 않다. `if (x)` 와 `x == false` 는 다른 질문이다.");
```

```text
===== node20 js01b-02e-conversion-table.js (exit=0) =====
value       Number()      String()                Boolean()  == false
---------------------------------------------------------------------
undefined   NaN           "undefined"             false      false
null        0             "null"                  false      false
true        1             "true"                  true       false
false       0             "false"                 false      true
0           0             "0"                     false      true
-0          0             "0"                     false      true
1           1             "1"                     true       false
NaN         NaN           "NaN"                   false      false
Infinity    Infinity      "Infinity"              true       false
""          0             ""                      false      true
" "         0             " "                     true       true
"0"         0             "0"                     true       true
"12"        12            "12"                    true       false
"0x10"      16            "0x10"                  true       false
"1e3"       1000          "1e3"                   true       false
"12px"      NaN           "12px"                  true       false
"Infinity"  Infinity      "Infinity"              true       false
[]          0             ""                      true       true
[7]         7             "7"                     true       false
[1,2]       NaN           "1,2"                   true       false
{}          NaN           "[object Object]"       true       false
0n          0             "0"                     false      true
1n          1             "1"                     true       false

falsy 인데 `== false` 는 거짓 : undefined null NaN
truthy 인데 `== false` 가 참   : " " "0" []
둘 다 인 것                    : false 0 -0 "" 0n

★ 두 목록은 같지 않다. `if (x)` 와 `x == false` 는 다른 질문이다.
```

그림 해설.

- ★★★ **두 목록이 어긋나는 칸이 여섯**이다.
  `undefined`·`null`·`NaN` 은 **falsy 인데 `== false` 는 거짓**이고,
  `" "`·`"0"`·`[]` 는 **truthy 인데 `== false` 가 참**이다.
  ★ **`if (x)` 와 `x == false` 는 다른 질문**이다 — 서로 부정도 아니다.
- ★★ **`"0x10"` 이 `16` 이 된다.** `Number()` 는 **16진·8진·2진 접두와 지수 표기를 받아들인다.**
  `parseInt` 와 다른 규칙이다.
- ★★ **`" "` 이 `0`** 이다. 공백만 있는 문자열은 빈 문자열처럼 다뤄진다 — 폼 입력에서 사고가 나는 자리다.
- ★★ **`[1,2]` 는 `NaN` 인데 `[7]` 은 `7`** 이다. 배열의 `toString` 이 `"1,2"`·`"7"` 을 주고 그것을 숫자로 바꾸기 때문이다.
  ★ **원소가 하나인 배열만 숫자가 된다.**
- ★ **`{}` 는 `"[object Object]"` 를 거쳐 `NaN`** 이다.
- ★ **`Date` 를 이 표에서 뺐다.** `String(new Date(0))` 은 **시간대와 로캘**에 달려 흔들리는 칸이라
  같은 블록에 두면 재대조가 깨진다. 「흔들리는 칸」을 선언하는 것보다 **안 흔들리게 만드는 쪽**이 낫다.

**비용** — 어떤 값이든 세 방향으로 바꿀 수 있어 코드가 짧아진다.
대신 **세 방향의 규칙이 서로 달라서**, 한 방향의 직관을 다른 방향에 쓰면 틀린다.

### (6) `==` 를 써도 되는 자리 — 딱 하나 있다

**언제 쓰나** — 「값이 비었나」를 묻는 자리.

```js
// js01b-02f-loose-eq-safe.js
// == 를 써도 되는 좁은 자리 하나 — `x == null` 은 "null 이거나 undefined" 를 한 번에 묻는다.
const VALUES = [
  ["undefined", undefined], ["null", null], ["0", 0], ['""', ""],
  ["false", false], ["NaN", NaN], ["0n", 0n], ["[]", []], ["{}", {}],
];

console.log("value".padEnd(12) + "x == null".padEnd(12) +
            "x === null || x === undefined".padEnd(32) + "두 칸이 같은가");
console.log("-".repeat(12 + 12 + 32 + 14));
let same = true;
for (const [label, v] of VALUES) {
  const a = v == null, b = v === null || v === undefined;
  if (a !== b) same = false;
  console.log(label.padEnd(12) + String(a).padEnd(12) + String(b).padEnd(32) + (a === b ? "같다" : "★ 다르다"));
}
console.log("");
console.log("아홉 줄 전부 같은가:", same);

console.log("");
console.log("★ 그런데 `x == null` 과 `!x` 는 전혀 다른 질문이다");
console.log("value".padEnd(12) + "x == null".padEnd(12) + "!x".padEnd(8) + "x ?? 'D'".padEnd(12) + "x || 'D'");
console.log("-".repeat(12 + 12 + 8 + 12 + 10));
for (const [label, v] of VALUES.slice(0, 7))
  console.log(label.padEnd(12) + String(v == null).padEnd(12) + String(!v).padEnd(8) +
              String(v ?? "D").padEnd(12) + String(v || "D"));
```

```text
===== node20 js01b-02f-loose-eq-safe.js (exit=0) =====
value       x == null   x === null || x === undefined   두 칸이 같은가
----------------------------------------------------------------------
undefined   true        true                            같다
null        true        true                            같다
0           false       false                           같다
""          false       false                           같다
false       false       false                           같다
NaN         false       false                           같다
0n          false       false                           같다
[]          false       false                           같다
{}          false       false                           같다

아홉 줄 전부 같은가: true

★ 그런데 `x == null` 과 `!x` 는 전혀 다른 질문이다
value       x == null   !x      x ?? 'D'    x || 'D'
------------------------------------------------------
undefined   true        true    D           D
null        true        true    D           D
0           false       true    0           D
""          false       true                D
false       false       true    false       D
NaN         false       true    NaN         D
0n          false       true    0           D
```

그림 해설.

- ★★★ **`x == null` 은 `x === null || x === undefined` 와 아홉 줄에서 전부 같다.**
  `==` 표의 **`undefined`/`null` 전용 줄** 덕에 다른 값이 절대 안 섞인다 — **이것이 유일하게 안전한 `==`** 다.
- ★★ **그런데 `!x` 와는 전혀 다르다.** `0`·`""`·`false`·`NaN`·`0n` 이 `!x` 에서는 참이고 `x == null` 에서는 거짓이다.
  ★ 「값이 비었나」와 「값이 falsy 인가」는 **다른 질문**이고, 실무 버그의 상당수가 그 둘을 바꿔 쓴 것이다.
- ★★ **`??` 가 `x == null` 과 같은 편**이고 **`||` 가 `!x` 와 같은 편**이다.
  `0 || "D"` 는 `"D"` 인데 `0 ?? "D"` 는 `0` 이다 — 12번 주제의 자리다.
- ★ 그래서 실무 규칙은 「**`==` 는 `x == null` 에서만 쓴다**」 하나로 줄어든다.

**비용** — 한 줄이 짧아지고 의도가 또렷해진다.
대신 **`==` 를 한 자리에서 허용하면 다른 자리에도 새어 들어간다** — 그래서 린터가 `eqeqeq` 규칙에 예외 옵션을 따로 둔다.

### (7) 두 판과 브라우저에서 — 갈리는 자리가 없다

**언제 쓰나** — 「이 표가 엔진마다 다르지 않을까」를 물을 때.

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
===== ./js01b-vdiff.sh 02 (exit=0) =====
script                             node v18.19.1 대 v20.19.6
---------------------------------- -------------------------
js01b-02a-toprimitive-spy.js       같다 (한 글자도)
js01b-02b-date-hint.js             같다 (한 글자도)
js01b-02c-equality-grids.js        같다 (한 글자도)
js01b-02d-famous.js                같다 (한 글자도)
js01b-02e-conversion-table.js      같다 (한 글자도)
js01b-02f-loose-eq-safe.js         같다 (한 글자도)
```

```text
<!doctype html><meta charset="utf-8"><title>coercion in the browser</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js01b-02g-browser.js"></script>
```

```js
// js01b-02g-browser.js
const rows = [
  ["엔진",                     navigator.userAgent.replace(/^.*(Chrome\/[\d.]+).*$/, "$1")],
  ["[] == false",              [] == false],
  ["[] == ![]",                [] == ![]],
  ["null == undefined",        null == undefined],
  ["NaN === NaN",              NaN === NaN],
  ["Object.is(NaN, NaN)",      Object.is(NaN, NaN)],
  ["1 + '2'",                  1 + "2"],
  ["typeof (new Date(0) + 1)", typeof (new Date(0) + 1)],
  ["typeof document.all",      typeof document.all],
  ["document.all == undefined", document.all == undefined],
  ["Boolean(document.all)",    Boolean(document.all)],
  ["Object.prototype.toString.call(document.all)", Object.prototype.toString.call(document.all)],
];
document.getElementById("out").textContent =
  rows.map(([k, v]) => k.padEnd(46) + " : " + String(v)).join("\n");
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --dump-dom js01b-02g-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">엔진                                             : Chrome/151.0.0.0
[] == false                                    : true
[] == ![]                                      : true
null == undefined                              : true
NaN === NaN                                    : false
Object.is(NaN, NaN)                            : true
1 + '2'                                        : 12
typeof (new Date(0) + 1)                       : string
typeof document.all                            : undefined
document.all == undefined                      : true
Boolean(document.all)                          : false
Object.prototype.toString.call(document.all)   : [object HTMLAllCollection]</pre>
```

그림 해설.

- **여섯 스크립트가 두 판에서 한 글자도 같았다.** 강제 변환 규칙은 **판이 올라도 안 움직이는 층**이다.
- **Chrome 151 도 Node 와 같은 답**을 냈다. 다만 **V8 은 같은 엔진**이므로 이것은 「다른 엔진에서도 같다」의 근거가 못 된다 —
  ★ **판이 다를 뿐 엔진이 같다.**
- ★★ **브라우저에서만 나오는 줄이 셋** 있다 — `document.all` 세 줄이다.
  `typeof` 가 `"undefined"` 이고 **`== undefined` 가 참**이며 **falsy** 다.
  ★ 이 값이 `==` 표에 **호스트가 뚫어 놓은 예외**이고, 01번 주제의 그 값과 같은 것이다.
- ★ **「같았다」는 보장이 아니다.** 보장은 명세의 비교표에서 온다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js01b-02x-forms.js
// 형태만 모아 둔 파일 — 출력은 없다. `node --check` 로 문법만 확인한다.
const a = 1, b = "1", o = {};

a == b;                   // 느슨한 비교 — 타입이 다르면 맞춰 본 뒤 비교한다
a === b;                  // 엄격 비교 — 타입이 다르면 그 자리에서 false
Object.is(a, b);          // SameValue — NaN 과 -0 에서 === 와 갈린다
[a].includes(b);          // SameValueZero — NaN 은 같다고 보고 -0 은 0 과 같다

Number(o);                // ToNumber — 객체면 먼저 ToPrimitive(number)
String(o);                // ToString — 객체면 먼저 ToPrimitive(string)
Boolean(o);               // ToBoolean — 객체는 언제나 true (document.all 만 예외)
+o;                       // 단항 + 는 ToNumber 와 같다. ★ BigInt 에는 못 쓴다
`${o}`;                   // 템플릿은 ToString 쪽

o.valueOf;                // 힌트가 number·default 일 때 먼저 불린다
o.toString;               // 힌트가 string 일 때 먼저 불린다
o[Symbol.toPrimitive];    // ★ 있으면 위의 둘을 아예 안 부른다

a == null;                // ★ 쓸 만한 유일한 느슨한 비교 — null 이거나 undefined
a ?? "기본값";             // null·undefined 일 때만 기본값 (12번 주제)
a || "기본값";             // 모든 falsy 에서 기본값 — 0 과 "" 이 샌다
```

```text
===== node20 --check js01b-02x-forms.js (exit=0) =====

```

규칙은 여덟이다.

1. **`===` 는 타입이 다르면 그 자리에서 거짓**이다. 변환이 없다.
2. **`==` 는 타입이 다르면 표를 따라 한쪽을 바꾸고 다시 묻는다.** 예외를 던지는 칸이 없다.
3. **`undefined` 와 `null` 은 `==` 에서 서로만 같다.** 전용 줄이 있어 다른 값이 안 섞인다.
4. **객체가 한쪽일 때만 `ToPrimitive`** 가 돈다. 양쪽이 객체면 **참조만** 본다.
5. **`ToPrimitive` 의 힌트는 셋**(`number`·`string`·`default`)이고 **`default` 는 기본 객체에서 `number` 처럼** 다뤄진다.
6. **`Symbol.toPrimitive` 가 있으면 `valueOf`·`toString` 을 아예 안 부른다.** `Date` 가 그 대표다.
7. **`+` 만 문자열로 기운다.** 다른 산술 연산자는 전부 숫자 쪽이다.
8. **동등성 규칙은 셋**이다 — `==`·`===`(SameValue 아님)·`Object.is`(SameValue). 그리고 `includes`·`Set` 은 **SameValueZero** 라는 넷째를 쓴다.

## 어디서 틀리나

### (1) ★★★ `if (x == 0)` 으로 「0 인가」를 묻는다

`""`·`" "`·`false`·`[]`·`"0"`·`0n` 이 전부 참이 된다. **폼 입력이 빈 문자열로 들어오는 자리**가 정확히 이것이다.
`x === 0` 을 쓴다.

### (2) ★★★ `+` 로 숫자를 더하는데 한쪽이 문자열이다

`price + quantity` 가 `"1002"` 가 된다. **에러가 안 나고 값만 틀린다.**
`Number(price) + Number(quantity)` 로 **경계에서 한 번** 바꾼다.

### (3) ★★ 「`Date` 는 `valueOf`/`toString` 순서가 반대」로 외운다

★ **순서가 반대인 게 아니라 `Symbol.toPrimitive` 가 힌트를 갈아 끼운다.**
그래서 `date + 1` 은 문자열이고 `date - 0` 은 숫자다. 규칙이 깨진 게 아니라 **그대로 적용된** 결과다.

### (4) ★★ `NaN` 을 `===` 로 거른다

`x === NaN` 은 **언제나 거짓**이다. `Number.isNaN(x)` 이나 `x !== x` 를 쓴다(03번 주제).

### (5) ★★ `Object.is` 를 「더 엄격한 `===`」로 안다

**더 엄격한 게 아니라 다르다.** `NaN` 에서는 더 너그럽고(`true`) `±0` 에서는 더 까다롭다(`false`).
225칸 격자에서 **갈린 칸이 정확히 둘**이다.

### (6) ★★ `[] == []` 가 참일 거라 본다

**양쪽이 객체면 변환이 없다** — 참조만 본다. `[] == 0` 은 참인데 `[] == []` 는 거짓이다.

### (7) ★ `null == 0` 과 `null >= 0` 이 같을 거라 본다

앞은 거짓, 뒤는 참이다. **`==` 에는 `null` 전용 줄이 있고 관계 연산자에는 없다.**

### (8) ★★ `x || 기본값` 으로 기본값을 준다

`0`·`""`·`false` 가 전부 기본값으로 바뀐다. **「값이 없을 때」를 뜻했다면 `??` 다**(12번 주제).

### (9) ★ `Number()` 와 `parseInt()` 를 같은 것으로 본다

`Number("12px")` 는 `NaN` 이고 `parseInt("12px")` 는 `12` 다. `Number("")` 는 `0` 이고 `parseInt("")` 는 `NaN` 이다.
**둘은 규칙이 아예 다르다.**

### (10) ★★ 「`==` 는 절대 쓰지 마라」를 곧이곧대로 지킨다

**`x == null` 하나는 써도 된다** — 표에 전용 줄이 있어 다른 값이 안 섞이고, `x === null || x === undefined` 보다 짧다.
「전부 금지」는 외우기 쉬운 대신 **이 한 자리를 잃는다.**

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★★ **이 주제는 「명세 보장」 칸이 거의 전부**다 — 강제 변환 규칙은 표로 닫혀 있어 엔진이 고를 여지가 없다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **명세(ECMA-262) 보장** | 어느 엔진에서도 같아야 하는 것 | 기준 소스 + 675칸 전수 실행 |
| **엔진(V8) 구현** | V8 이 그렇게 하는 것 | 두 판 대조 + Chrome 151 |
| **이 판의 관찰** | 이 판에서 그랬을 뿐 | 「관찰」로 명기 |

### 명세 보장

| 사실 | 어떻게 확인했나 |
|---|---|
| **느슨한 비교 표의 모든 칸** — 225칸 전부 | 전수로 던져 격자를 채움 |
| `undefined` 와 `null` 은 **서로만 같다** | 격자의 2×2 블록 |
| **양쪽이 객체면 변환 없이 참조만** 본다 | `[] == []` 가 거짓 |
| `ToPrimitive` 의 **힌트 세 가지**와 그 이름 | `Symbol.toPrimitive` 의 인자를 찍음 |
| **`default` 는 기본 객체에서 `number` 처럼** 다뤄진다 | `o + 1` 이 `valueOf` 를 부름 |
| **`Symbol.toPrimitive` 가 있으면 나머지 둘을 안 부른다** | 로그에 둘이 한 번도 안 찍힘 |
| 첫 메서드가 원시 값을 안 주면 **다음 것을 부르고, 둘 다 실패하면 `TypeError`** | 로그에 둘 다 찍힌 뒤 예외 |
| **`Date.prototype[Symbol.toPrimitive]`** 가 있고 `Object.prototype` 에는 없다 | `typeof` 로 확인 |
| **`+` 만 문자열로 기운다** | 네 연산자를 같은 값에 던져 비교 |
| **`Object.is` 가 `===` 와 갈리는 곳은 `NaN` 과 `±0` 둘뿐** | 675칸 격자 대조 |
| **`==` 는 어떤 조합에서도 예외를 안 던진다** | 격자의 예외 칸이 0 |

### 엔진(V8) 구현

| 사실 | 어떻게 확인했나 |
|---|---|
| 여섯 스크립트가 **두 판에서 한 글자도 같았다** | `js01b-vdiff.sh 02` |
| Chrome 151 이 **Node 20 과 같은 답**을 냈다 | 같은 식을 양쪽에서 던짐 |
| 예외 **문구**가 두 판에서 같았다 | 같은 대조 |

★ **셋 다 「같았다」이지 「같아야 한다」가 아니다.** 그리고 **Chrome 과 Node 는 같은 V8** 이라
「다른 엔진에서도 같다」의 근거로는 쓸 수 없다.

### 이 판의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `Cannot convert object to primitive value` 같은 **문구** | 예외의 **종류**는 명세지만 문구는 V8 의 것이다 |
| `Invalid hint: nope` | 같은 부류 |
| `String(new Date(0))` | **시간대·로캘**에 달렸다 — 그래서 이 문서의 어느 블록에도 안 실었다 |
| UA 가 `Chrome/151.0.0.0` 인 것 | 브라우저가 일부러 축약한 값이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`==` 는 타입을 무시한다」
  ○ **무시하지 않는다.** 타입마다 **다른 줄**을 가진 표를 따른다. `undefined`/`null` 줄이 그 증거다.
- ✗ 「`Date` 는 `valueOf` 와 `toString` 의 순서가 반대다」
  ○ **`Symbol.toPrimitive` 가 힌트를 갈아 끼운다.** 순서 규칙은 그대로다.
- ✗ 「`+` 는 언제나 문자열을 만든다」
  ○ **양쪽 다 문자열이 아니면 숫자**다. `true + true` 는 `2` 다.
- ✗ 「`Object.is` 는 더 엄격한 `===` 다」
  ○ **다른 규칙**이다. `NaN` 에서는 더 너그럽다.
- ✗ 「`[] == []` 는 참이다」
  ○ **거짓**이다. 양쪽이 객체면 변환이 없다.
- ✗ 「`==` 표는 엔진마다 다를 수 있다」
  ○ **표로 닫혀 있다.** 675칸을 던져도 두 판이 한 글자도 안 달랐다.
- ✗ 「`==` 는 예외를 던질 수 있다」
  ○ **비교 자체는 안 던진다.** 다만 **`ToPrimitive` 가 던질 수는 있다** — 그것은 비교가 아니라 변환이 던지는 것이다.

**판정 기준 한 줄**: 어떤 코드가 **`==` 를 `null` 아닌 값과 쓰고 있으면** 그 자리는 표를 펴 봐야 하는 자리다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `===` / `!==` | **기본값.** 다른 이유가 없으면 이것이다 |
| `x == null` | 「`null` 이거나 `undefined` 인가」 — **유일하게 안전한 `==`** |
| `Object.is(a, b)` | **`NaN` 이나 `-0` 을 정확히** 가려야 할 때 |
| `Number.isNaN(x)` | `NaN` 판별. `x === NaN` 은 언제나 거짓이다 |
| `Number(x)` / `String(x)` / `Boolean(x)` | **경계에서 한 번** 명시적으로 바꾼다 |
| `Symbol.toPrimitive` | 내 객체가 연산자를 만났을 때의 동작을 **내가 정할 때** |
| `x ?? 기본값` | 「값이 없을 때만」 기본값 |

**안 쓰는 자리**는 넷이다.
**`==` 를 `null` 아닌 값과 쓰지 마라** — 표를 외우고 있지 않으면 틀린다.
**`+` 로 숫자를 더하기 전에 타입을 확인하라** — 문자열 하나가 전체를 이어붙이기로 바꾼다.
**`x === NaN` 을 쓰지 마라** — 언제나 거짓이다.
**`x || 기본값` 으로 「값이 없을 때」를 뜻하지 마라** — `0` 과 `""` 이 샌다.

## 핵심 문장

- **`==` 는 타입을 무시하는 게 아니라 타입마다 다른 줄을 가진 표를 따른다.** 675칸을 던지면 표가 통째로 보인다.
- **추상 연산은 이름으로 못 부르지만 로그로 볼 수 있다** — `valueOf`/`toString`/`Symbol.toPrimitive` 에 로그를 심으면 순서가 찍힌다.
- **힌트가 셋이고 `default` 는 숫자 쪽**이다. `+` 가 문자열로 기우는 것은 **그다음 단계**다.
- **`Symbol.toPrimitive` 는 나머지 둘을 덮는다.** `Date` 가 반대로 구는 이유가 그것이지 순서가 바뀐 게 아니다.
- **`undefined` 와 `null` 은 서로만 같다** — 그 전용 줄이 `x == null` 을 안전하게 만든다.
- **`Object.is` 가 `===` 와 갈리는 칸은 정확히 둘**이다 — `NaN` 과 `±0`.
- **`==` 는 예외를 안 던진다.** 그래서 **조용히 틀린다** — 이 주제의 값이 전부 거기 있다.

## 관련 자료

- 목록: [js/syntax 주제 목록](../README.md) — 이 주제는 **02번**
- 선행: [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) — **원시 7종과 객체**·falsy 목록·`document.all` 의 정본.
  **경계**: 그쪽은 「값이 무엇인가」까지, 여기는 「**그 값들이 섞일 때 무엇이 되나**」부터다.
- 이어지는 곳: [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md) — `0n == 0` 은 참인데 `0n === 0` 은 거짓인 것의 정본.
- 이어지는 곳: [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) — `'10' < '9'` 가 참인 것, 즉 **문자열 비교의 단위**.
- 이어지는 곳: [목록의 **12번 주제**](../12-optional-chaining-nullish-and-logical-assignment/) 「옵셔널 체이닝·널 병합·논리 할당」 — `??` 와 `||` 가 갈리는 falsy 케이스.
- 이어지는 곳: 목록의 **33번 주제** 「동등성 세 종류」 — `===`·`Object.is`·SameValueZero 가 **`Map` 키·`includes`** 에서 갈리는 것의 정본.
- 이어지는 곳: [목록의 **22번 주제**](../22-symbol-and-well-known-symbols/) 「`Symbol` 과 잘 알려진 심볼」 — `Symbol.toPrimitive` 가 **언어 동작 자체를 바꾸는** 자리의 정본.
- 이어지는 곳: 목록의 **35번 주제** 「엄격 모드」 — 엄격 모드도 `==` 는 안 막는다는 것.
- 경계 — 타입 검사: TypeScript 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **01번** [`01-what-ts-adds-and-erases`](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md).
  **그쪽은 「검사기가 무엇을 지우는가」까지, 여기는 「지워진 뒤 런타임이 무엇을 하는가」부터다.**
- 경계 — 다른 언어의 같은 자리: [`python/syntax/04-numeric-types-and-division`](../../../python/syntax/04-numeric-types-and-division/2-summary.md) —
  파이썬도 `1 == 1.0` 은 참이지만 **`"1" == 1` 은 거짓**이다. 문자열과 숫자 사이에 다리가 없다.
- 연혁은 여기가 아니다: [`history/js/`](../../../../../../history/js/) — `==` 표가 왜 초판에 그렇게 들어갔나.

## 용어 풀이

- **강제 변환(coercion)**: 연산자가 필요해서 말없이 타입을 바꾸는 것. `Number(x)` 처럼 내가 부르는 것은 **명시적 변환**이다.
- **추상 연산(abstract operation)**: 명세가 규칙을 적기 위해 쓰는 내부 절차. `ToPrimitive`·`ToNumber`·`ToString`·`ToBoolean` 등.
  코드에서 이름으로 못 부르지만 **그것이 부르는 메서드에 로그를 심으면 관찰된다.**
- **`ToPrimitive`**: 객체를 원시 값으로 바꾸는 절차. 힌트(`number`·`string`·`default`)를 받아 어느 메서드를 먼저 부를지 정한다.
- **힌트(hint)**: `ToPrimitive` 에 「숫자를 원한다 / 글자를 원한다 / 아무거나」를 알리는 문자열. `Symbol.toPrimitive` 의 인자로 그대로 넘어온다.
- **`Symbol.toPrimitive`**: 객체가 원시 값으로 바뀌는 방식을 **직접 정하는** 잘 알려진 심볼. 있으면 `valueOf`·`toString` 을 아예 안 부른다.
- **느슨한 동등 `==`**: 타입이 다르면 표를 따라 한쪽을 바꾼 뒤 다시 비교한다. **예외를 던지는 칸이 없다.**
- **엄격 동등 `===`**: 타입이 다르면 그 자리에서 거짓. 단 **`NaN`/`NaN` 은 거짓이고 `0`/`-0` 은 참**이라 「값이 같으면 참」도 아니다.
- **SameValue**: `Object.is` 가 쓰는 규칙. `NaN`/`NaN` 이 참이고 `0`/`-0` 이 거짓이다.
- **SameValueZero**: `includes`·`Set`·`Map` 키가 쓰는 규칙. `NaN`/`NaN` 이 참이고 `0`/`-0` 도 참이다.
- **falsy**: `if` 에서 거짓으로 취급되는 값. `undefined`·`null`·`false`·`0`·`-0`·`0n`·`NaN`·`""` 과 `document.all` 이다.
- **truthy**: falsy 가 아닌 모든 값. **객체는 전부 truthy** 다(`document.all` 만 예외).

## 더 들어가면

- **`==` 의 표에는 「재귀」가 있다.** 한쪽을 바꾼 뒤 **다시 `==` 를 부른다** — `[] == false` 는
  `[] == 0` → `"" == 0` → `0 == 0` 처럼 여러 번 접힌다. 그래서 표를 한 번만 읽으면 못 푼다.
- **관계 연산자에는 넷째 답이 있다.** `<`·`>` 의 비교 절차는 참·거짓 말고 「**비교 불가**」를 돌려줄 수 있고,
  `NaN` 이 걸리면 그 답이 나와 **전부 거짓**으로 떨어진다. 그래서 `NaN < 1` 과 `NaN >= 1` 이 둘 다 거짓이다.
- **`Symbol` 은 `==` 격자에서 뺐다.** 심볼은 자기 자신과만 같고 다른 어떤 타입과도 안 같아 **행·열이 통째로 비기** 때문이다.
  다만 **`Symbol() + ""` 은 `TypeError`** 라 변환 쪽에서는 따로 볼 자리가 있다 — 22번 주제다.
- **`ToNumber` 가 문자열을 읽는 규칙은 `parseInt` 와 완전히 다르다.** 앞뒤 공백을 버리고, 빈 문자열은 `0`,
  `0x`·`0o`·`0b` 접두와 지수 표기를 받고, **그 밖에 글자가 하나라도 남으면 `NaN`** 이다.
- **린터의 `eqeqeq` 규칙에 `"smart"`·`"allow-null"` 옵션이 있다.** 이 주제의 6번 절이 그 옵션의 근거다.
  이 문서에서는 린터를 돌리지 않았다.
