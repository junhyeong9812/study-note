# js/syntax/05 — `var`·`let`·`const` 와 TDZ: 「이 이름은 언제부터 쓸 수 있나」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 선언과 스코프(Declarations and the Variable Statement)·환경 레코드·전역 환경
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — `let`/`const` 가 들어온 판(ES2015)을 가릴 때
> - [MDN — `let`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let) · [MDN — `const`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const) · [MDN — `var`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/var)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> **어느 판에서 나왔는지는 아래 첫 블록**에 있다.

```sh
// js05b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 — 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    console.log("node " + v.node + "  v8 " + v.v8 +
                "  globalThis " + typeof globalThis +
                "  new.target " + typeof (function(){ return new.target; })() +
                "  logical-assign " + typeof (function(){ let a; a ??= 1; return a; })());'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js05b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  globalThis object  new.target undefined  logical-assign number
node 20.19.6  v8 11.3.244.8-node.33  globalThis object  new.target undefined  logical-assign number
Google Chrome 151.0.7922.173 
```

> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 **`e.constructor.name` 과 `e.message` 만** 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박혀 다른 머신에서 재현이 안 되기 때문이다.
> 그래서 이 주제의 블록에는 **표준 오류가 한 줄도 섞이지 않는다** — 전부 표준 출력이다.
> ★★ **`SyntaxError` 는 `try`/`catch` 로 못 잡는다**(파싱 단계에서 나기 때문이다).
> 그래서 재선언 격자는 `new Function(소스)` 으로 **파싱만 시키고** 타입과 문구를 받는다 — 파일로 던지면 진단에 경로가 박힌다.
> ★★ **`padEnd` 격자의 라벨은 전부 ASCII 다.** 한글은 터미널에서 두 칸이라 칸이 어긋난다.
>
> **버전** — `var` 는 초판부터다. **`let`·`const`·블록 스코프·TDZ 는 ES2015**, `globalThis` 는 **ES2020** 이다.
> 이 주제에는 **시각·로캘·난수가 닿는 칸이 하나도 없다.**
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **예외의 종류** — `ReferenceError`·`TypeError`·`SyntaxError` |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **격자의 어느 칸이 터지고 어느 칸이 안 터지는가** |
> | Node 모듈 래퍼의 **인자 다섯 개**가 무엇인가(런타임 사정) | ★★ **프로퍼티 디스크립터**(`configurable` 등) · 종료 코드 |
> | 브라우저 UA 문자열의 **뒷자리** | ★★ **`globalThis` 에 붙나 안 붙나** |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> ★ **두 판(18·20)에서 이 주제의 일곱 스크립트가 전부 한 글자도 같았다**(7번 절).
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) —
> ★★ **`typeof` 가 TDZ 에서 터지는 것을 거기서 이미 실측했다.** 이 주제가 그것을 이어받아 넓힌다.
> **이어지는 곳** — [목록의 **06번 주제**](../06-scope-and-closures/) 「스코프와 클로저」 · [목록의 **07번 주제**](../07-this-binding-four-rules/) 「`this` 바인딩 네 규칙」 · [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」
>
> ★★ **경계 — 「언제 들어왔나」는 여기가 아니다.** [`history/js/02-ES6-모던.md`](../../../../../../history/js/02-ES6-모던.md)가 도입 역사의 정본이다.
> **여기는 「지금 이 규칙이 코드에서 무엇을 만드나」부터다.**

## 한눈에 — 쉽게 말하면

**선언은 「창고에 이름표를 붙이는 일」이고, `var` 와 `let` 은 이름표를 붙이는 시점이 아니라 「쓸 수 있게 되는 시점」이 다르다.**

셋 다 **블록(또는 함수)에 들어서는 순간 이름표는 이미 붙는다.**
다른 것은 그다음이다 — `var` 는 **빈 칸(`undefined`)이 먼저 들어가** 있고,
`let`/`const` 는 **칸이 잠겨 있어** 선언문이 실행될 때까지 손을 대면 손이 잘린다.

```text
   블록에 들어선다                 선언문이 실행된다              그 뒤

   var v                          var v = 1
   [ v | undefined ]  ---------->  [ v | 1 ]  ------------>  [ v | 1 ]
     ^ 읽어도 된다                                             읽어도 된다

   let l                          let l = 1
   [ l | 잠김 ]      ---------->  [ l | 1 ]  ------------>  [ l | 1 ]
     ^ 읽으면 ReferenceError                                  읽어도 된다
     ^ typeof 해도 ReferenceError

   (선언 없음)
   (칸 자체가 없다)  -------------------------------------->  (여전히 없다)
     ^ 읽으면 ReferenceError · ★ typeof 만 "undefined" 를 준다
```

**「잠긴 구간」이 TDZ 다.** 시작은 **블록에 들어선 순간**이고 끝은 **선언문이 실행된 순간**이다 — 줄 번호가 아니라 **시간**이다.

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 창고 한 칸 | 바인딩(이름과 값이 들어가는 자리) | 이름을 읽어 본다 |
| 칸에 미리 들어간 빈 종이 | `var` 의 `undefined` 초기화 | 선언문 앞에서 읽으면 `undefined` |
| 잠긴 칸 | TDZ | 읽어도 `typeof` 해도 `ReferenceError` |
| 칸 자체가 없음 | 선언 안 된 이름 | 읽으면 `ReferenceError`, ★ `typeof` 만 `"undefined"` |
| 칸에 못을 박아 둔 것 | `const` — 칸의 **내용물**을 바꿀 수 없다 | 재대입에 `TypeError` |
| 칸 안의 상자를 여는 것 | `const` 가 안 막는 것 | `o.k = 1` 은 그대로 된다 |
| 창고를 나눠 쓰는 단위 | 스코프 — `var` 는 함수, `let`/`const` 는 블록 | 블록 밖에서 이름을 불러 본다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 하나로 굳어 있다.
`for (var i = 0; ...)` 로 만든 콜백 셋이 전부 같은 값을 보는 사고가 그것이고,
`if (typeof maybe === "undefined")` 로 방어한 코드가 TDZ 에서 터지는 사고가 그것이다.
**둘 다 「이름표는 언제 붙고 칸은 언제 열리나」 한 문장이 답이다.**

> **호이스팅(hoisting)** — 선언이 그 스코프의 맨 위로 「끌어올려진 것처럼」 보이는 것.
> 예: `console.log(v); var v = 1;` 이 에러가 아니라 `undefined` 를 찍는다. ★ **`let`/`const` 도 끌어올려지지만 잠겨 있다.**

> **TDZ (Temporal Dead Zone, 일시적 사각지대)** — `let`/`const`/`class` 의 이름이 **있긴 한데 아직 못 쓰는** 구간.
> 예: 블록 첫 줄에서 그 블록의 `let v` 를 읽으면 `ReferenceError` 다. **「일시적」이라는 말대로 줄이 아니라 시간이다.**

## 이 주제가 답하려는 질문

1. **선언 전에 이름을 건드리면 무엇이 나오나** — `undefined` 냐 `ReferenceError` 냐가 선언 종류로 갈린다.
2. **TDZ 는 어디서 시작해 어디서 끝나나** — 답은 「줄」이 아니라 「실행 순간」이고, 같은 함수를 두 번 불러 증명한다.
3. **`const` 가 고정하는 것은 무엇인가** — 이름이지 값이 아니다. 그 차이가 버그의 절반이다.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### (1) ★★★ 선언 여섯 가지를 한 격자에 — 어긋나는 칸이 어디인가

**언제 쓰나** — 「이 줄 위에서 이 이름을 건드리면 무엇이 되나」를 물을 때.

```text
   선언문 앞에서 건드렸을 때

   선언 종류        그냥 읽기              typeof
   ------------     -------------------   -------------------
   var v            undefined             "undefined"
   let l            ReferenceError        ReferenceError   <- ★ typeof 에 구멍
   const c          ReferenceError        ReferenceError
   function f       그 함수 (부를 수도 있다)  "function"
   class K          ReferenceError        ReferenceError   <- ★ class 도 TDZ
   (선언 없음)       ReferenceError        "undefined"      <- ★ 여기만 어긋난다

   ★ 읽기 칸에서 통과하는 것은 var 와 function 둘뿐이다.
   ★ typeof 칸에서 var / 선언없음 / function 셋이 통과한다 — 그래서 typeof 는
     「없는 것」과 「아직 안 넣은 것」을 구분해 주지 않는다.
```

```js
// js05b-05a-hoisting-grid.js
// 선언 여섯 가지를 「선언문 앞」에서 두 가지 방법으로 건드려 본다.
// 라벨은 전부 ASCII 다 — 한글을 padEnd 격자에 넣으면 칸이 어긋난다.
function fmt(v) {
  if (typeof v === "function") return "[Function: " + (v.name || "anonymous") + "]";
  if (v === undefined) return "undefined";
  return JSON.stringify(v);
}
function probe(read) {
  try { return fmt(read()); }
  catch (e) { return e.constructor.name + ": " + e.message; }
}

const rows = [
  ["var v",        () => { const a = probe(() => v),    b = probe(() => typeof v);    var v = 1;      return [a, b]; }],
  ["let l",        () => { const a = probe(() => l),    b = probe(() => typeof l);    let l = 1;      return [a, b]; }],
  ["const c",      () => { const a = probe(() => c),    b = probe(() => typeof c);    const c = 1;    return [a, b]; }],
  ["function f",   () => { const a = probe(() => f),    b = probe(() => typeof f);    function f() {} return [a, b]; }],
  ["class K",      () => { const a = probe(() => K),    b = probe(() => typeof K);    class K {}      return [a, b]; }],
  ["(undeclared)", () => { const a = probe(() => nope), b = probe(() => typeof nope);                 return [a, b]; }],
];

console.log("decl".padEnd(14) + "read it".padEnd(56) + "typeof it");
console.log("-".repeat(14) + "-".repeat(56) + "-".repeat(46));
for (const [label, run] of rows) {
  const [a, b] = run();
  console.log(label.padEnd(14) + a.padEnd(56) + b);
}

console.log("");
console.log("[함수 선언은 이름만이 아니라 본문까지 이미 있다]");
function early() { const s = f(1); function f(x) { return x + 1; } return s; }
console.log("  calling f(1) before its declaration -> " + early());
```

```text
===== node20 js05b-05a-hoisting-grid.js (exit=0) =====
decl          read it                                                 typeof it
--------------------------------------------------------------------------------------------------------------------
var v         undefined                                               "undefined"
let l         ReferenceError: Cannot access 'l' before initialization ReferenceError: Cannot access 'l' before initialization
const c       ReferenceError: Cannot access 'c' before initialization ReferenceError: Cannot access 'c' before initialization
function f    [Function: f]                                           "function"
class K       ReferenceError: Cannot access 'K' before initialization ReferenceError: Cannot access 'K' before initialization
(undeclared)  ReferenceError: nope is not defined                     "undefined"

[함수 선언은 이름만이 아니라 본문까지 이미 있다]
  calling f(1) before its declaration -> 2
```

그림 해설 (한 단계씩).

- ★★★ **`var` 는 `undefined` 로 먼저 초기화되고 `let`/`const` 는 잠겨 있다.** 「끌어올려지느냐」가 아니라 「**끌어올려진 뒤 초기화되느냐**」가 차이다.
  ★ 셋 다 스코프에 이름은 이미 있다. `let` 이 「호이스팅이 안 된다」는 흔한 설명은 **틀렸다** — 이름이 없으면 `is not defined` 가 나와야 하는데 실제로는 `Cannot access ... before initialization` 이 나온다.
- ★★★ **두 메시지가 그 증거다.** `is not defined` 는 **칸이 없다**, `Cannot access ... before initialization` 은 **칸은 있는데 잠겼다**는 뜻이다.
  ★ 「예외의 종류」는 둘 다 `ReferenceError` 로 같고, **가르는 것은 문구**다 — 그래서 이 구분은 **흔들리는 칸** 위에 있다(아래 층 표).
- ★★★ **`typeof` 도 TDZ 를 못 넘는다.** [01번](../01-value-types-and-typeof/2-summary.md)에서 이미 본 사실이고, 여기서 **여섯 줄 격자로 넓혔다.**
  ★★ 그래서 **「`typeof` 는 절대 안 터진다」는 틀린 문장**이고, 정확히는 「**선언이 아예 없는 이름에 한해** 안 터진다」다.
- ★★ **`function` 선언은 이름만이 아니라 본문까지 이미 들어 있다.** 마지막 줄이 선언문 앞에서 `f(1)` 을 불러 `2` 를 받았다.
  ★ **`var` 로 만든 함수 표현식은 그렇지 않다** — 08번이 그 격자를 따로 편다.
- ★ **`class` 는 `function` 이 아니라 `let` 쪽**이다. 문법이 선언처럼 생겼다고 호이스팅 방식이 같지는 않다.

**비용** — `var` 의 「미리 `undefined`」는 **실수를 에러가 아니라 값으로** 만든다.
`let`/`const` 의 잠금은 **실수를 즉시 에러**로 만든다 — 대신 「`typeof` 로 방어한다」는 관용구가 그 자리에서 깨진다.

### (2) ★★★ TDZ 의 시작과 끝 — 줄이 아니라 시간이다

**언제 쓰나** — 「선언문 위/아래」로 외운 규칙이 안 맞는 자리를 만났을 때.

```text
   function late(flag) {
     const read = () => w;        <- 클로저를 여기서 만든다 (아직 아무 일도 안 났다)
     if (flag) read();            <- (A) 여기서 부르면 ReferenceError
     let w = 1;                   <- ★ 이 문장이 "실행되는 순간" 잠금이 풀린다
     read();                      <- (B) 같은 함수인데 이제 1 을 준다
   }

   ★ (A)와 (B)는 같은 함수 객체다. 함수가 바뀐 것이 아니라 칸이 열린 것이다.
   ★ 그래서 TDZ 의 경계는 소스의 줄이 아니라 "실행 시점"이다.
```

```js
// js05b-05b-tdz-boundary.js
// TDZ 는 어디서 시작하고 어디서 끝나는가 — 같은 클로저를 두 번 불러 가른다.
function probe(label, read) {
  let r;
  try { r = JSON.stringify(read()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(30) + " -> " + r);
}

let v = "outer";
console.log("[1] TDZ 는 선언문 줄이 아니라 블록 진입에서 시작한다");
console.log("  (바깥에 v = \"outer\" 가 있다 — 그것이 보이는지를 본다)");
{
  probe("block entered", () => v);
  const peek = () => v;
  probe("peek() before the let", peek);
  let v = "inner";
  probe("after the let stmt", () => v);
  probe("the same peek() again", peek);
}

console.log("");
console.log("[2] 끝나는 것은 선언문이 놓인 줄이 아니라 그 문장이 실행되는 순간이다");
function late(flag) {
  const read = () => w;
  if (flag) probe("read() with flag=true", read);
  let w = 1;
  probe("read() after the let ran", read);
}
late(true);

console.log("");
console.log("[3] 초기화자가 없어도 TDZ 는 있다");
{ probe("before `let u;`", () => u); let u; probe("after  `let u;`", () => u); }

console.log("");
console.log("[4] 매개변수 기본값에도 TDZ 가 있고 왼쪽에서 오른쪽이다");
function ok(a = 1, b = a + 1) { return [a, b]; }
function bad(a = b, b = 2) { return [a, b]; }
probe("ok()  -- b sees a", () => ok());
probe("bad() -- a sees b", () => bad());

console.log("");
console.log("[5] class 선언도 TDZ 에 들어가고 function 선언은 안 들어간다");
probe("new K() before class K", () => new K());
probe("g() before function g", () => g());
class K {}
function g() { return "g ran"; }
```

```text
===== node20 js05b-05b-tdz-boundary.js (exit=0) =====
[1] TDZ 는 선언문 줄이 아니라 블록 진입에서 시작한다
  (바깥에 v = "outer" 가 있다 — 그것이 보이는지를 본다)
  block entered                  -> ReferenceError: Cannot access 'v' before initialization
  peek() before the let          -> ReferenceError: Cannot access 'v' before initialization
  after the let stmt             -> "inner"
  the same peek() again          -> "inner"

[2] 끝나는 것은 선언문이 놓인 줄이 아니라 그 문장이 실행되는 순간이다
  read() with flag=true          -> ReferenceError: Cannot access 'w' before initialization
  read() after the let ran       -> 1

[3] 초기화자가 없어도 TDZ 는 있다
  before `let u;`                -> ReferenceError: Cannot access 'u' before initialization
  after  `let u;`                -> undefined

[4] 매개변수 기본값에도 TDZ 가 있고 왼쪽에서 오른쪽이다
  ok()  -- b sees a              -> [1,2]
  bad() -- a sees b              -> ReferenceError: Cannot access 'b' before initialization

[5] class 선언도 TDZ 에 들어가고 function 선언은 안 들어간다
  new K() before class K         -> ReferenceError: Cannot access 'K' before initialization
  g() before function g          -> "g ran"
```

그림 해설.

- ★★★ **시작은 블록에 들어선 순간**이다. `[1]` 에서 **바깥에 `v = "outer"` 가 있는데도** 블록 첫 줄의 `v` 가 `ReferenceError` 다.
  ★★ 만약 TDZ 가 선언문 줄에서 시작했다면 그 자리에서 **바깥의 `"outer"` 가 읽혔을 것**이다. 안 읽혔다는 것이 곧 **「블록 진입부터」의 증거**다.
- ★★★ **끝은 그 선언문이 실행된 순간**이다. `[2]` 에서 **같은 클로저**가 앞에서는 터지고 뒤에서는 `1` 을 준다.
  ★ 「선언문 아래면 괜찮다」가 아니다 — **아래에 있어도 아직 실행되지 않았으면 잠겨 있다.**
- ★★ **초기화자가 없어도 TDZ 는 있다.** `let u;` 앞은 `ReferenceError` 이고 뒤는 `undefined` 다 — **두 상태가 다르다.**
- ★★ **매개변수 기본값도 자기 TDZ 를 가진다.** `f(a = 1, b = a + 1)` 은 되고 `f(a = b, b = 2)` 는 터진다 — **왼쪽에서 오른쪽**이다. 08번이 이 칸을 이어받는다.
- ★ **`class` 는 TDZ 에 들어가고 `function` 은 안 들어간다.** `[5]` 두 줄이 그 대비다.

**비용** — 「선언 전에 쓰면 즉시 에러」라 **오타·순서 실수가 값으로 새지 않는다.**
대신 **읽기만 해도 터지므로** 「있으면 쓰고 없으면 넘어간다」는 방어 코드를 `typeof` 로 쓸 수 없다.

### (3) ★★ `const` 가 고정하는 것 — 이름이지 값이 아니다

**언제 쓰나** — 「`const` 로 했는데 왜 바뀌지?」를 물을 때.

```text
   const o = { k: 1 };

   이름 o  ──못질됨──>  [ 상자 ]  { k: 1 }
     ^                      ^
     |                      |
   o = {} 는 TypeError    o.k = 2 는 그냥 된다

   ★ const 는 "화살표"를 못 바꾸게 할 뿐, 상자 안은 아무것도 안 막는다.
   ★ 상자 안까지 막으려면 Object.freeze 이고, 그것도 한 겹만 막는다.
```

```js
// js05b-05d-const.js
// const 는 무엇을 고정하는가 — 이름이냐 값이냐.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(34) + " -> " + r);
}

console.log("[1] const 가 고정하는 것은 이름이지 그 뒤의 값이 아니다");
probe("const n = 1; n = 2", () => { const n = 1; n = 2; return n; });
probe("const o = {}; o.k = 1", () => { const o = {}; o.k = 1; return o; });
probe("const a = []; a.push(1)", () => { const a = []; a.push(1); return a; });
probe("const o = {}; o = {}", () => { const o = {}; o = {}; return o; });

console.log("");
console.log("[2] 값까지 고정하고 싶으면 그것은 다른 도구다");
probe("frozen.k = 1 (sloppy)", () => { const o = Object.freeze({ k: 0 }); o.k = 1; return o; });
probe("frozen.k = 1 (strict)", () => { "use strict"; const o = Object.freeze({ k: 0 }); o.k = 1; return o; });
probe("freeze is shallow", () => { const o = Object.freeze({ inner: { k: 0 } }); o.inner.k = 1; return o; });

console.log("");
console.log("[3] const 는 초기화자가 있어야 하고 let 은 없어도 된다");
for (const src of ["const c;", "let l;", "const c = 1;"]) {
  let r; try { new Function(src); r = "parsed ok"; }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + src.padEnd(34) + " -> " + r);
}

console.log("");
console.log("[4] 루프의 const — for-of 는 회차마다 새 이름, for(;;) 는 아니다");
probe("for (const x of [1,2,3])", () => { const seen = []; for (const x of [1, 2, 3]) seen.push(x); return seen; });
probe("for (const k in {a:1,b:2})", () => { const seen = []; for (const k in { a: 1, b: 2 }) seen.push(k); return seen; });
probe("for (const i=0; i<3; i++)", () => new Function("for (const i = 0; i < 3; i++) {} return 'ran';")());

console.log("");
console.log("[5] 섀도잉은 재선언이 아니다 — 안쪽 블록은 같은 이름을 다시 쓸 수 있다");
probe("inner block shadows outer", () => {
  const n = "outer";
  let inner;
  { const n = "inner"; inner = n; }
  return [n, inner];
});
probe("same block twice", () => new Function("const n = 1; const n = 2; return n;")());
```

```text
===== node20 js05b-05d-const.js (exit=0) =====
[1] const 가 고정하는 것은 이름이지 그 뒤의 값이 아니다
  const n = 1; n = 2                 -> TypeError: Assignment to constant variable.
  const o = {}; o.k = 1              -> {"k":1}
  const a = []; a.push(1)            -> [1]
  const o = {}; o = {}               -> TypeError: Assignment to constant variable.

[2] 값까지 고정하고 싶으면 그것은 다른 도구다
  frozen.k = 1 (sloppy)              -> {"k":0}
  frozen.k = 1 (strict)              -> TypeError: Cannot assign to read only property 'k' of object '#<Object>'
  freeze is shallow                  -> {"inner":{"k":1}}

[3] const 는 초기화자가 있어야 하고 let 은 없어도 된다
  const c;                           -> SyntaxError: Missing initializer in const declaration
  let l;                             -> parsed ok
  const c = 1;                       -> parsed ok

[4] 루프의 const — for-of 는 회차마다 새 이름, for(;;) 는 아니다
  for (const x of [1,2,3])           -> [1,2,3]
  for (const k in {a:1,b:2})         -> ["a","b"]
  for (const i=0; i<3; i++)          -> TypeError: Assignment to constant variable.

[5] 섀도잉은 재선언이 아니다 — 안쪽 블록은 같은 이름을 다시 쓸 수 있다
  inner block shadows outer          -> ["outer","inner"]
  same block twice                   -> SyntaxError: Identifier 'n' has already been declared
```

그림 해설.

- ★★★ **`const n = 1; n = 2` 는 `TypeError` 이고 `const o = {}; o.k = 1` 은 그냥 된다.** **막히는 것은 대입 연산자의 왼쪽이 그 이름일 때뿐**이다.
- ★★ **`Object.freeze` 도 조용할 수 있다.** 느슨한 모드에서 `o.k = 1` 은 **에러 없이 버려지고** 엄격 모드에서만 `TypeError` 다.
  ★ **「에러가 안 났다」가 「먹혔다」가 아니다** — `[2]` 의 두 줄이 그 대비다. 그리고 **얕게만 막는다**(`o.inner.k` 는 바뀐다).
- ★★ **`const` 는 초기화자를 요구하고 `let` 은 안 한다.** 파싱 단계에서 갈리므로 `SyntaxError` 다 — 런타임에 도달조차 안 한다.
- ★★ **루프에서 `const` 가 되는 자리와 안 되는 자리가 갈린다.** `for (const x of ...)` 는 **회차마다 이름이 새로 생겨서** 되고,
  `for (const i = 0; i < 3; i++)` 는 **같은 이름을 다시 대입하므로** `TypeError` 다. ★ 이 사실이 06번의 「회차마다 새 바인딩」과 같은 사실이다.
- ★ **섀도잉은 재선언이 아니다.** 안쪽 블록의 같은 이름은 **다른 칸**이라 `SyntaxError` 가 아니다.

**비용** — `const` 를 기본으로 쓰면 **재대입이라는 사고 한 종류가 통째로 사라진다.**
대신 **「값이 안 변한다」는 보장은 못 준다** — 그것을 기대하면 더 위험하다.

### (4) ★★★ 블록 스코프 대 함수 스코프 — `for` 에서 가장 크게 벌어진다

**언제 쓰나** — 루프 안에서 만든 함수가 나중에 이상한 값을 볼 때.

```text
   for (var i = 0; i < 3; i++)          for (let i = 0; i < 3; i++)

   함수 전체가 i 한 칸을 나눠 쓴다        회차마다 i 칸이 새로 생긴다
   +------------------+                 +-----+  +-----+  +-----+
   |   i              |                 | i=0 |  | i=1 |  | i=2 |
   +------------------+                 +-----+  +-----+  +-----+
     ^   ^   ^                             ^        ^        ^
     f0  f1  f2   (셋이 같은 칸)            f0       f1       f2

   루프 뒤 i -> 3                        루프 뒤 i -> ReferenceError
   f0(),f1(),f2() -> 3 3 3               f0(),f1(),f2() -> 0 1 2

   ★ 값이 다른 것은 결과이고, 원인은 "칸이 몇 개냐"다 — 06번이 그 개수를 직접 센다.
```

```js
// js05b-05e-loop-scope.js
// for 루프의 var 와 let — 블록 스코프와 함수 스코프의 차이가 가장 크게 벌어지는 자리.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(30) + " -> " + r);
}

console.log("[1] 루프가 끝난 뒤에 그 이름이 남아 있나");
probe("var: read i after loop", () => { for (var i = 0; i < 3; i++) {} return i; });
probe("let: read i after loop", () => { for (let i = 0; i < 3; i++) {} return i; });

console.log("");
console.log("[2] 루프 안에서 만든 함수 셋을 나중에 부르면");
function withVar() { const fns = []; for (var i = 0; i < 3; i++) fns.push(() => i); return fns.map((f) => f()); }
function withLet() { const fns = []; for (let i = 0; i < 3; i++) fns.push(() => i); return fns.map((f) => f()); }
probe("var", withVar);
probe("let", withLet);

console.log("");
console.log("[3] 블록 하나로도 갈린다 — if 블록 안의 선언");
probe("var inside if block", () => { if (true) { var a = 1; } return typeof a; });
probe("let inside if block", () => { if (true) { let b = 1; } return typeof b; });

console.log("");
console.log("[4] var 는 블록을 몇 겹이든 빠져나오지만 함수는 못 빠져나온다");
probe("var out of nested blocks", () => { { { var q = 7; } } return q; });
probe("let out of nested blocks", () => { { { let q = 7; } } return typeof q; });
probe("var out of a function", () => { function inner() { var deep = 7; } inner(); return typeof deep; });
```

```text
===== node20 js05b-05e-loop-scope.js (exit=0) =====
[1] 루프가 끝난 뒤에 그 이름이 남아 있나
  var: read i after loop         -> 3
  let: read i after loop         -> ReferenceError: i is not defined

[2] 루프 안에서 만든 함수 셋을 나중에 부르면
  var                            -> [3,3,3]
  let                            -> [0,1,2]

[3] 블록 하나로도 갈린다 — if 블록 안의 선언
  var inside if block            -> "number"
  let inside if block            -> "undefined"

[4] var 는 블록을 몇 겹이든 빠져나오지만 함수는 못 빠져나온다
  var out of nested blocks       -> 7
  let out of nested blocks       -> "undefined"
  var out of a function          -> "undefined"
```

그림 해설.

- ★★★ **`var` 는 루프가 끝난 뒤에도 남고 `let` 은 없다.** `[1]` 이 `3` 과 `ReferenceError` 로 갈린다.
- ★★★ **콜백 셋이 `[3,3,3]` 과 `[0,1,2]` 로 갈린다.** 이것이 이 언어에서 가장 자주 인용되는 함정이다.
  ★★ 흔한 설명 「나중에 읽어서 덮어써졌다」는 **증상의 절반만** 말한다 — 칸이 셋이었다면 나중에 읽어도 `0 1 2` 가 나왔을 것이다.
  **원인은 「칸이 하나」라는 것**이고, 06번이 그 개수를 **직접 세어 증명한다.**
- ★★ **블록 하나로도 갈린다.** `if (true) { var a = 1; }` 뒤에 `a` 가 살아 있고 `let b` 는 없다.
- ★★ **`var` 는 블록을 몇 겹이든 빠져나오지만 함수는 못 빠져나온다.** `[4]` 의 세 줄이 「함수 스코프」의 정확한 뜻이다.

**비용** — 함수 스코프는 **규칙이 하나**라 단순하지만, 「블록마다 가두고 싶다」는 요구를 **함수로 감싸야만** 채울 수 있었다(IIFE — 06번).
블록 스코프는 **가두는 비용이 0**이 되지만, `var` 로 짠 옛 코드를 `let` 으로 바꾸면 **의미가 조용히 달라지는 자리**가 생긴다.

### (5) ★★ 같은 이름을 두 번 — 되는 것과 `SyntaxError` 인 것

**언제 쓰나** — 파일을 합치거나 옛 코드를 `let` 으로 바꿀 때.

```js
// js05b-05f-redeclare.js
// 같은 이름을 두 번 선언하면 — SyntaxError 는 잡을 수 없으므로 new Function 으로 파싱만 시킨다.
// ★ new Function 을 쓰는 이유: 파일을 던지면 진단에 절대 경로가 박힌다. 여기서는 타입과 문구만 받는다.
function parse(src) {
  try { new Function(src); return "parsed ok"; }
  catch (e) { return e.constructor.name + ": " + e.message; }
}

const cases = [
  "var a = 1; var a = 2;",
  "let a = 1; let a = 2;",
  "const a = 1; const a = 2;",
  "var a = 1; let a = 2;",
  "let a = 1; var a = 2;",
  "let a = 1; const a = 2;",
  "function a() {} function a() {}",
  "let a = 1; function a() {}",
  "var a = 1; function a() {}",
  "let a = 1; { let a = 2; }",
  "let a = 1; function f(a) {}",
  "function f(a, a) { return a; }",
  "'use strict'; function f(a, a) { return a; }",
];

console.log("source".padEnd(46) + "result");
console.log("-".repeat(46) + "-".repeat(52));
for (const src of cases) console.log(src.padEnd(46) + parse(src));

console.log("");
console.log("[통과한 것이 실제로 무엇을 만들었나 — 통과도 출력이다]");
console.log("  var a=1; var a=2 -> a is " + new Function("var a = 1; var a = 2; return a;")());
console.log("  function a twice -> a() is " + new Function("function a(){return 1} function a(){return 2} return a();")());
console.log("  sloppy dup param -> f(1,2) is " + new Function("function f(a, a) { return a; } return f(1, 2);")());
```

```text
===== node20 js05b-05f-redeclare.js (exit=0) =====
source                                        result
--------------------------------------------------------------------------------------------------
var a = 1; var a = 2;                         parsed ok
let a = 1; let a = 2;                         SyntaxError: Identifier 'a' has already been declared
const a = 1; const a = 2;                     SyntaxError: Identifier 'a' has already been declared
var a = 1; let a = 2;                         SyntaxError: Identifier 'a' has already been declared
let a = 1; var a = 2;                         SyntaxError: Identifier 'a' has already been declared
let a = 1; const a = 2;                       SyntaxError: Identifier 'a' has already been declared
function a() {} function a() {}               parsed ok
let a = 1; function a() {}                    SyntaxError: Identifier 'a' has already been declared
var a = 1; function a() {}                    parsed ok
let a = 1; { let a = 2; }                     parsed ok
let a = 1; function f(a) {}                   parsed ok
function f(a, a) { return a; }                parsed ok
'use strict'; function f(a, a) { return a; }  SyntaxError: Duplicate parameter name not allowed in this context

[통과한 것이 실제로 무엇을 만들었나 — 통과도 출력이다]
  var a=1; var a=2 -> a is 2
  function a twice -> a() is 2
  sloppy dup param -> f(1,2) is 2
```

그림 해설.

- ★★★ **`let`·`const` 가 걸린 조합은 전부 `SyntaxError: Identifier 'a' has already been declared` 다.** 순서를 바꿔도(`var` 먼저든 `let` 먼저든) 같다.
  ★★ **`SyntaxError` 는 파싱 단계에서 난다** — 그래서 **그 파일의 다른 코드가 한 줄도 실행되지 않는다.** 런타임 에러와 성질이 다르다.
- ★★ **`var` 끼리와 `function` 끼리는 통과한다.** 그리고 **통과한 것이 무엇을 만들었는지**까지 찍었다 — 마지막 것이 이긴다(`2`).
  ★ 「통과도 출력이다」 — 통과했다고 아무 일도 안 난 것이 아니다.
- ★★ **매개변수 중복은 모드가 가른다.** 비엄격은 `function f(a, a)` 를 받고 **뒤엣것이 이긴다**(`f(1,2)` 가 `2`),
  엄격은 `SyntaxError: Duplicate parameter name not allowed in this context` 다. ★ **설정이 답을 바꾸는 칸**이다.
- ★ **블록이 다르면 재선언이 아니다**(`let a = 1; { let a = 2; }` 는 통과). **매개변수와 몸통의 `let` 은 재선언**이다(08번).

**비용** — `SyntaxError` 는 **가장 이른 시점에 잡히는 에러**다. 테스트를 안 돌려도 잡힌다.
대신 **파일 전체가 안 돈다** — 한 줄 때문에 나머지가 통째로 멈춘다.

### (6) ★★ 전역이라는 지붕 — 「전역 `var` 는 `globalThis` 에 붙는다」가 어디까지 참인가

**언제 쓰나** — 「전역에 뒀는데 `window.` 로 안 보인다」를 만났을 때.

```text
   같은 var 한 줄이 세 자리에서 세 가지로 끝난다

   (A) Node 의 .js 파일 (CommonJS)      (B) 진짜 전역 스크립트           (C) 브라우저 classic <script>
       function (exports, require,           var sv = 1                       var declaredVar = 1
                 module, __filename,
                 __dirname) { ... }
       -> 래퍼 함수의 지역 변수             -> globalThis.sv = 1             -> window.declaredVar = 1
       -> globalThis 에 안 붙는다          -> 지울 수 없다(configurable:false)  -> 붙는다

   ★ let 은 (B)(C) 에서도 프로퍼티가 안 된다 — 다만 "이름으로는" 읽힌다.
```

```js
// js05b-05c-globalthis.js
// 「전역 var 는 globalThis 에 붙는다」 — 어디까지 참인가.
// 이 파일 자체는 Node 의 CommonJS 모듈이다. 그 사실이 답의 절반이다.
const vm = require("vm");   // Node 내장 — 진짜 전역 스코프에서 스크립트를 돌린다
function line(label, value) { console.log("  " + label.padEnd(38) + " -> " + JSON.stringify(value)); }
const desc = (k) => Object.getOwnPropertyDescriptor(globalThis, k);

var topVar = 1;
let topLet = 2;

console.log("[1] 이 파일은 Node 가 감싼 모듈이라 최상위가 전역 스코프가 아니다");
line("typeof module", typeof module);
line("this === module.exports", this === module.exports);
line("top-level arrow arguments.length", (() => arguments.length)());
line("what those 5 arguments are", Array.from(arguments, (a) => typeof a));
line("globalThis.topVar", globalThis.topVar);
line("globalThis.topLet", globalThis.topLet);

console.log("");
console.log("[2] 진짜 전역 스코프의 스크립트 — vm.runInThisContext");
vm.runInThisContext("var sv = 1; let sl = 2; const sc = 3; function sf(){}");
line("globalThis.sv", globalThis.sv);
line("descriptor of sv", desc("sv"));
line("'sl' in globalThis", "sl" in globalThis);
line("'sc' in globalThis", "sc" in globalThis);
line("descriptor of sf", desc("sf"));

console.log("");
console.log("[3] let/const 도 거기 있다 — 다만 프로퍼티가 아닐 뿐이다");
line("a later script reading sl", vm.runInThisContext("sl"));
line("a later script reading sc", vm.runInThisContext("sc"));

console.log("");
console.log("[4] var 가 만든 전역 프로퍼티는 못 지우고 그냥 대입한 것은 지워진다");
line("delete globalThis.sv", vm.runInThisContext("delete globalThis.sv"));
line("globalThis.sv after delete", globalThis.sv);
globalThis.plain = 1;
line("delete globalThis.plain", delete globalThis.plain);
(0, eval)("var ev = 1;");
line("descriptor of an eval-made var", desc("ev"));

console.log("");
console.log("[5] 전역 let 은 두 번째 선언을 거부한다 — 스크립트가 달라도");
for (const src of ["let sl = 9;", "var sl = 9;", "var sv = 9;"]) {
  let r; try { vm.runInThisContext(src); r = "ok"; }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + src.padEnd(38) + " -> " + r);
}
```

```text
===== node20 js05b-05c-globalthis.js (exit=0) =====
[1] 이 파일은 Node 가 감싼 모듈이라 최상위가 전역 스코프가 아니다
  typeof module                          -> "object"
  this === module.exports                -> true
  top-level arrow arguments.length       -> 5
  what those 5 arguments are             -> ["object","function","object","string","string"]
  globalThis.topVar                      -> undefined
  globalThis.topLet                      -> undefined

[2] 진짜 전역 스코프의 스크립트 — vm.runInThisContext
  globalThis.sv                          -> 1
  descriptor of sv                       -> {"value":1,"writable":true,"enumerable":true,"configurable":false}
  'sl' in globalThis                     -> false
  'sc' in globalThis                     -> false
  descriptor of sf                       -> {"writable":true,"enumerable":true,"configurable":false}

[3] let/const 도 거기 있다 — 다만 프로퍼티가 아닐 뿐이다
  a later script reading sl              -> 2
  a later script reading sc              -> 3

[4] var 가 만든 전역 프로퍼티는 못 지우고 그냥 대입한 것은 지워진다
  delete globalThis.sv                   -> false
  globalThis.sv after delete             -> 1
  delete globalThis.plain                -> true
  descriptor of an eval-made var         -> {"value":1,"writable":true,"enumerable":true,"configurable":true}

[5] 전역 let 은 두 번째 선언을 거부한다 — 스크립트가 달라도
  let sl = 9;                            -> SyntaxError: Identifier 'sl' has already been declared
  var sl = 9;                            -> SyntaxError: Identifier 'sl' has already been declared
  var sv = 9;                            -> ok
```

**그리고 브라우저에서 같은 것을 던지면** — 호스트 페이지는 네 줄이고 실제 검사는 옆의 `.js` 가 한다.

```text
<!doctype html><meta charset="utf-8"><title>this in a browser</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js05b-07g-browser.js"></script>
```

```js
// js05b-07g-browser.js
var declaredVar = "on window";
let declaredLet = "not on window";

function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis (window)";
  if (typeof t === "object" || typeof t === "function") return Object.prototype.toString.call(t);
  return typeof t + " " + String(t);
}
function loose() { return tag(this); }
function tight() { "use strict"; return tag(this); }
const obj = { name: "obj", hello() { return "hi " + this.name; } };
const detached = obj.hello;

const rows = [
  ["top-level this in a classic script", tag(this)],
  ["sloppy f()", loose()],
  ["strict f()", tight()],
  ["globalThis === window", String(globalThis === window)],
  ["window.name is", JSON.stringify(window.name)],
  ["obj.hello()", obj.hello()],
  ["detached hello() -- the silent one", detached()],
  ["window.declaredVar", String(window.declaredVar)],
  ["window.declaredLet", String(window.declaredLet)],
  ["declaredLet read by name", String(declaredLet)],
  ["top-level arrow: arguments?", (() => { try { return String(arguments.length); } catch (e) { return e.constructor.name + ": " + e.message; } })()],
];

setTimeout(function () {
  rows.push(["setTimeout(fn) this", tag(this)]);
  document.getElementById("out").textContent =
    rows.map(([k, v]) => k.padEnd(38) + " : " + v).join("\n");
}, 0);
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --virtual-time-budget=1000 --dump-dom js05b-07g-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">top-level this in a classic script     : globalThis (window)
sloppy f()                             : globalThis (window)
strict f()                             : undefined
globalThis === window                  : true
window.name is                         : ""
obj.hello()                            : hi obj
detached hello() -- the silent one     : hi 
window.declaredVar                     : on window
window.declaredLet                     : undefined
declaredLet read by name               : not on window
top-level arrow: arguments?            : ReferenceError: arguments is not defined
setTimeout(fn) this                    : globalThis (window)</pre>
```

그림 해설.

- ★★★ **「전역 `var` 는 `globalThis` 에 붙는다」는 이 파일에서 거짓이다.** Node 의 `.js` 는 **인자 다섯 개짜리 함수로 감싸여** 돌기 때문이다.
  ★★ 증거가 세 줄이다 — `typeof module` 이 `"object"`, 최상위 `this` 가 `module.exports`, **최상위 화살표의 `arguments.length` 가 `5`**.
  ★ **브라우저 블록에서 같은 줄이 `ReferenceError` 다** — 거기에는 래퍼가 없다. **같은 문장이 두 호스트에서 갈리는 것이 이 사실의 증명**이다.
- ★★★ **진짜 전역에서는 `var` 만 프로퍼티가 된다.** `sv` 는 `globalThis.sv` 로 보이고 `sl`·`sc` 는 `in` 검사에서 `false` 다.
  ★★ **그런데 없는 것이 아니다** — 뒤이은 스크립트가 **이름으로는 읽는다**(`2`, `3`). **「프로퍼티가 아니다」와 「없다」는 다른 말**이다.
- ★★ **`var` 가 만든 전역 프로퍼티는 못 지운다**(`delete` 가 `false`, `configurable: false`).
  그냥 대입해서 만든 프로퍼티는 지워지고, **`eval` 이 만든 `var` 는 `configurable: true` 라 지워진다** — 세 가지가 다르다.
- ★★ **전역 `let` 은 스크립트가 달라도 두 번 선언되지 않는다.** 두 스크립트가 같은 이름을 쓰면 뒤엣것이 `SyntaxError` 다 —
  ★ **`var` 는 이 충돌이 안 난다**(마지막 줄이 `ok`). 옛 코드가 `var` 로 전역을 겹쳐 쓰던 관행이 여기서 갈린다.
- ★ 브라우저 블록의 `window.name` 이 **`""`(빈 문자열)** 인 것을 기억해 둘 것 — 07번에서 이것이 **가장 조용한 실패**를 만든다.

**비용** — `var` 의 전역 프로퍼티화는 **스크립트끼리 값을 주고받는 통로**였다.
`let` 은 그 통로를 막는 대신 **이름 충돌을 파싱 단계에서 잡아 준다.**

### (7) 두 판에서 돌려 보면 — 갈리는 자리가 없다

**언제 쓰나** — 「이게 이 판에서만 그런 건 아닐까」를 물을 때.

```sh
// js05b-vdiff.sh
#!/usr/bin/env bash
# 이 배치의 스크립트를 두 판으로 돌려 한 글자라도 다른지 본다.
# 쓰는 법: ./js05b-vdiff.sh <주제번호>
set -u -o pipefail
N18=node                                          # v18.19.1 (기본 PATH)
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"  # v20.19.6 (nvm)
printf '%-30s %s\n' "script" "node v18.19.1 vs v20.19.6"
printf '%-30s %s\n' "------------------------------" "-------------------------"
for f in js05b-"$1"*.js; do
  case "$f" in *-browser.js) continue;; esac      # 브라우저용은 뺀다
  a=$("$N18" "$f" 2>&1); b=$("$N20" "$f" 2>&1)
  if [ "$a" = "$b" ]; then printf '%-30s same (byte for byte)\n' "$f"
  else printf '%-30s DIFF -- lines %s\n' "$f" "$(diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | grep -c '^[<>]')"
  fi
done
```

```text
===== ./js05b-vdiff.sh 05 (exit=0) =====
script                         node v18.19.1 vs v20.19.6
------------------------------ -------------------------
js05b-05a-hoisting-grid.js     same (byte for byte)
js05b-05b-tdz-boundary.js      same (byte for byte)
js05b-05c-globalthis.js        same (byte for byte)
js05b-05d-const.js             same (byte for byte)
js05b-05e-loop-scope.js        same (byte for byte)
js05b-05f-redeclare.js         same (byte for byte)
js05b-05x-forms.js             same (byte for byte)
```

그림 해설.

- **일곱 스크립트 전부 한 글자도 같았다.** 선언과 스코프는 **판이 올라도 안 움직이는 층**이다.
- ★★ **그런데 「같았다」는 보장이 아니다.** 보장은 명세에서 오고 이것은 관찰이다.
  다만 **이 문서의 출력을 어느 판에서 읽어도 된다**는 뜻은 된다.
- ★ **이 배치 네 주제(05\~08) 전체에서 두 판이 갈린 자리는 0개**였다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js05b-05x-forms.js
// 형태만 모아 둔 파일 — 출력은 없다. `node --check` 로 문법만 확인한다.
var a = 1;                 // 함수 스코프. 선언문 앞에서 읽으면 undefined
let b = 2;                 // 블록 스코프. 선언문 앞은 TDZ — 읽어도 typeof 해도 ReferenceError
const c = 3;               // 블록 스코프 + 재대입 금지. 초기화자가 반드시 있어야 한다
let d;                     // 초기화자 없는 let 은 된다. 선언문 뒤에 undefined
// const e;                // ★ SyntaxError: Missing initializer in const declaration

{
  let b = "shadow";        // 섀도잉 — 재선언이 아니다. 안쪽 블록의 다른 이름이다
  var a = "same name";     // var 는 블록을 무시한다 — 위의 a 와 같은 이름이다
}

for (var i = 0; i < 3; i++) {}   // i 는 루프 밖에서도 산다
for (let j = 0; j < 3; j++) {}   // j 는 회차마다 새로 생기고 루프 밖에는 없다
for (const k of [1, 2, 3]) {}    // for-of 는 회차마다 새 이름이라 const 가 된다

const o = { k: 1 };
o.k = 2;                   // ★ const 는 이름을 고정하지 값을 고정하지 않는다
Object.freeze(o);          // 값을 고정하려면 이것 — 얕게만 먹는다
// o = {};                 // ★ TypeError: Assignment to constant variable.
```

```text
===== node20 --check js05b-05x-forms.js (exit=0) =====

```

> ★ **이 빈 블록이 근거다.** 「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 구분이 안 된다.**
> 명령과 `(exit=0)` 까지 담긴 **빈 출력**이라야 「던졌고 조용했다」가 된다.

규칙은 여덟이다.

1. **셋 다 호이스팅된다** — 스코프에 들어서는 순간 이름이 만들어진다. 다른 것은 **초기화 시점**이다.
2. **`var` 는 `undefined` 로 미리 초기화**되고, **`let`/`const`/`class` 는 TDZ 에 들어간다.**
3. **TDZ 는 블록 진입에서 시작해 선언문이 실행될 때 끝난다** — 줄이 아니라 시간이다.
4. **TDZ 에서는 `typeof` 도 터진다.** `typeof` 의 특권은 「선언이 아예 없는 이름」에만 있다(01번).
5. **`const` 는 재대입만 막는다.** 값의 내용은 안 막는다 — 그건 `Object.freeze` 이고 **얕게만** 먹는다.
6. **`var` 는 함수 스코프, `let`/`const` 는 블록 스코프**다. `for` 의 `let` 은 **회차마다** 새 이름을 만든다(06번).
7. **`let`/`const` 가 낀 재선언은 `SyntaxError`** 다. `var` 끼리·`function` 끼리는 통과하고 **마지막 것이 이긴다.**
8. **진짜 전역에서만 `var` 가 `globalThis` 의 프로퍼티**가 된다. Node 의 `.js` 는 래퍼 안이라 해당하지 않는다.

## 어디서 틀리나

### (1) ★★★ 「`let` 은 호이스팅이 안 된다」로 외운다

**된다.** 안 되는 것은 **초기화**다. 안 된다면 `is not defined` 가 나와야 하는데 실제로는
`Cannot access 'l' before initialization` 이 나온다 — **이름이 이미 있다는 뜻**이다.
그리고 이 오해는 (2)의 사고로 곧장 이어진다.

### (2) ★★★ 안쪽 블록의 `let` 이 바깥 같은 이름을 가릴 줄 모른다

```text
   let v = "outer";
   { console.log(v); let v = "inner"; }   // ★ "outer" 가 아니라 ReferenceError
```

**블록에 들어선 순간 안쪽 `v` 가 바깥 `v` 를 이미 덮는다.** 선언문을 아래에 뒀다고 그 위에서 바깥 것이 보이지 않는다.

### (3) ★★ `typeof` 로 방어하면 안전하다고 믿는다

`typeof maybe === "undefined"` 는 **선언이 아예 없을 때만** 안전하다.
**TDZ 에서는 그 방어 코드 자체가 터진다.** 정본은 01번이고 이 주제가 그 구멍을 넓혀 보였다.

### (4) ★★★ `const` 를 「값이 안 변한다」로 읽는다

`const o = {}` 뒤에 `o.k = 1` 이 그냥 된다. **막히는 것은 `o = ...` 하나뿐**이다.
값까지 고정하려면 `Object.freeze` 이고, **그것도 한 겹만** 막으며 **느슨한 모드에서는 조용히 버려진다.**

### (5) ★★ `var` 를 `let` 으로 일괄 치환한다

**루프 뒤에 `i` 를 쓰던 코드가 `ReferenceError` 로 죽고**, 블록 밖에서 읽던 이름이 사라진다.
반대로 **의도적으로 겹쳐 선언하던 `var` 가 `SyntaxError`** 가 된다. 기계 치환이 안 되는 자리다.

### (6) ★★ 「전역에 뒀으니 `window.` 로 보이겠지」

**`let`/`const`/`class` 는 전역에서도 프로퍼티가 안 된다.** 그리고 **Node 의 `.js` 에서는 `var` 조차 안 된다**(모듈 래퍼).
★ 「안 보인다」를 「없다」로 읽으면 두 번 틀린다 — **이름으로는 읽힌다.**

### (7) ★★ 선언문 아래면 괜찮다고 생각한다

**아래에 있어도 그 문장이 아직 실행되지 않았으면 잠겨 있다.** 조건문·이른 반환·재귀가 그 자리를 만든다.
2번 절의 `late(true)` 가 정확히 그 모양이다.

### (8) ★ `const` 를 루프 헤더에 쓴다

`for (const i = 0; i < 3; i++)` 는 **`i++` 에서** `TypeError` 다. `for (const x of ...)` 는 된다 —
**회차마다 이름이 새로 생기느냐**가 두 자리를 가른다.

### (9) ★ 매개변수 기본값에서 뒤 매개변수를 읽는다

`function f(a = b, b = 2)` 가 `ReferenceError` 다. **왼쪽에서 오른쪽**이고, 아직 안 온 이름은 TDZ 다. 08번의 일이다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「명세 보장」 칸이 압도적으로 두껍다** — 선언과 스코프는 엔진이 고를 여지가 거의 없다.
★★ 대신 **네 번째 칸이 두껍다 — 「호스트가 정하는 것」**. 최상위가 무엇이냐를 ECMA-262 가 정하지 않기 때문이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **명세(ECMA-262) 보장** | 어느 엔진에서도 같아야 하는 것 | 위 기준 소스를 열어서 + 실행으로 재확인 |
| **호스트(Node·브라우저)가 정하는 것** | 「최상위」가 무엇이냐 | 같은 코드를 Node `.js`·`vm`·브라우저 세 곳에 던져 대조 |
| **엔진(V8) 구현** | V8 이 그렇게 하는 것 — 특히 **예외 문구** | 실행 + 두 판 대조 |
| **이 판의 관찰** | node 20.19.6 / 18.19.1 / Chrome 151 에서 그랬을 뿐 | 「관찰」로 명기 |

### 명세 보장

| 사실 | 어떻게 확인했나 |
|---|---|
| 세 선언 모두 **스코프 진입 시 이름이 만들어진다** | `Cannot access ... before initialization` 이 나온다는 것 자체 |
| **`var` 는 `undefined` 로 초기화**되고 `let`/`const`/`class` 는 **TDZ** 다 | 여섯 줄 격자 |
| **TDZ 에서는 `typeof` 도 `ReferenceError`** 다 | 같은 격자의 둘째 칸 |
| **TDZ 는 블록 진입에서 시작한다** | 바깥의 같은 이름이 **안 읽힌다**는 관찰 |
| **TDZ 는 선언문의 실행으로 끝난다** | 같은 클로저가 전후로 갈린 것 |
| **`const` 는 재대입만 막는다** | `o.k = 1` 이 통과 · `o = {}` 가 `TypeError` |
| **`const` 는 초기화자를 요구한다** | `SyntaxError: Missing initializer in const declaration` |
| **`var` 는 함수 스코프, `let`/`const` 는 블록 스코프** | 블록·함수 경계를 넘겨 본 네 줄 |
| **`let`/`const` 가 낀 재선언은 `SyntaxError`** | 13줄 격자 |
| **엄격 모드에서 중복 매개변수는 `SyntaxError`** | 같은 격자의 마지막 두 줄 |
| 진짜 전역에서 **`var` 만 전역 객체의 프로퍼티**가 되고 **`configurable: false`** 다 | 디스크립터를 찍어 확인 |

### 호스트가 정하는 것 — ECMA-262 밖

| 사실 | 어디서 갈렸나 |
|---|---|
| Node 의 `.js` 최상위는 **함수 안**이다(인자 다섯) | 최상위 화살표의 `arguments.length` 가 `5` |
| 그래서 **최상위 `var` 가 `globalThis` 에 안 붙는다** | 같은 줄이 브라우저에서는 붙는다 |
| 브라우저 classic script 의 최상위는 **진짜 전역**이다 | `window.declaredVar` 가 `"on window"` |
| 브라우저 최상위 화살표의 `arguments` 는 **`ReferenceError`** | 래퍼가 없기 때문 |

### 엔진(V8) 구현 · 이 판의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `Cannot access 'l' before initialization` 같은 **문구** | 예외의 **종류**는 명세지만 문구는 아니다. ★ **「없다」와 「잠겼다」를 가르는 근거가 이 문구뿐**이라 이 주제는 그 위에 결론을 세우지 않는다 |
| `Identifier 'a' has already been declared` | 같은 성질 |
| Node 20.19.6 의 V8 은 **11.3.244.8**, 18.19.1 은 **10.2.154.26** | `process.versions.v8` |
| 이 주제의 일곱 스크립트가 **두 판에서 한 글자도 같았다** | `js05b-vdiff.sh 05` |
| Node 모듈 래퍼의 인자가 **다섯 개**인 것 | Node 의 구현 사정이다. **개수가 아니라 「래퍼가 있다」가 요점** |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`let` 은 호이스팅되지 않는다」
  ○ **된다.** 초기화가 안 될 뿐이고, 그 증거가 `Cannot access ... before initialization` 이다.
- ✗ 「TDZ 는 선언문 위쪽이다」
  ○ **블록 진입부터 선언문 실행까지**다. 아래에 있어도 아직 실행 전이면 잠겨 있다.
- ✗ 「`typeof` 는 안 터지니까 안전하다」
  ○ **TDZ 에서는 터진다.**
- ✗ 「`const` 는 값을 바꿀 수 없게 한다」
  ○ **이름을 다시 못 가리키게** 할 뿐이다.
- ✗ 「전역 `var` 는 항상 `globalThis` 에 붙는다」
  ○ **진짜 전역 스코프에서만** 그렇다. Node 의 `.js` 는 래퍼 안이다.
- ✗ 「`let` 을 전역에 두면 사라진다」
  ○ **프로퍼티가 아닐 뿐 이름으로는 읽힌다.** 「안 보인다」는 「없다」가 아니다.

**판정 기준 한 줄**: 어떤 이름을 건드리는 코드를 보면 「**이 문장이 실행되는 시점에 그 칸이 열렸나**」를 묻는다. 줄 번호를 보지 않는다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `const` | **기본값.** 재대입할 이유가 생기기 전까지 전부 이것 |
| `let` | **재대입이 필요할 때만.** 루프 카운터·누적 변수 |
| `for (const x of ...)` | 순회 — 회차마다 새 이름이라 `const` 가 된다 |
| `for (let i = 0; ...)` | 인덱스가 필요할 때. **콜백을 만들면 회차마다 다른 칸**이다(06번) |
| `Object.freeze` | **값까지** 고정하고 싶을 때. 얕다는 것을 알고 쓴다 |
| `var` | ★ **새 코드에는 쓰지 않는다.** 옛 코드를 읽을 때만 필요한 지식이다 |

**안 쓰는 자리**는 셋이다.
**`var` 로 새로 짜지 마라** — 함수 스코프가 주는 이득이 지금은 없다.
**`typeof` 로 TDZ 를 방어하지 마라** — 그 자리가 정확히 터지는 자리다.
**`const` 를 불변의 증거로 쓰지 마라** — 그것은 `Object.freeze` 의 일이고 그마저 얕다.

## 핵심 문장

- **셋 다 호이스팅된다. 다른 것은 「초기화되느냐」다.** `var` 는 `undefined` 가 먼저 들어가고 `let`/`const` 는 잠겨 있다.
- **TDZ 의 경계는 줄이 아니라 시간이다** — 블록에 들어선 순간 시작하고, 선언문이 **실행되는** 순간 끝난다.
- **`typeof` 의 특권은 TDZ 에 없다.** 특권은 「선언이 아예 없는 이름」에만 있다.
- **`const` 가 못질하는 것은 이름이다.** 상자 안은 아무것도 안 막는다.
- **`var` 는 함수를 못 빠져나오고, 블록은 몇 겹이든 빠져나온다.**
- **`let`/`const` 가 낀 재선언은 파싱 단계에서 죽는다** — 파일이 한 줄도 안 돈다.
- **「전역 `var` 는 `globalThis` 에 붙는다」는 호스트가 정한다.** Node 의 `.js` 에서는 거짓이다.

## 관련 자료

- 목록: [js/syntax 주제 목록](../README.md) — 이 주제는 **05번**
- 선행: [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) —
  **`typeof` 가 TDZ 에서 터지는 것의 첫 실측**이 거기 있다. **그쪽은 「`typeof` 의 특권에 구멍이 있다」까지, 여기는 「그 구멍이 왜 거기 있나」부터다.**
- 이어지는 곳: [목록의 **06번 주제**](../06-scope-and-closures/) 「스코프와 클로저」 — 4번 절의 `[3,3,3]` 대 `[0,1,2]` 를 **「칸이 몇 개냐」로** 바꿔 센다.
- 이어지는 곳: [목록의 **07번 주제**](../07-this-binding-four-rules/) 「`this` 바인딩 네 규칙」 — **`this` 는 스코프로 안 찾는다.** 그 대비가 07번의 첫 문장이다.
- 이어지는 곳: [목록의 **08번 주제**](../08-function-forms-and-parameters/) 「함수 정의 형태와 매개변수」 — 함수 선언의 호이스팅과 **매개변수 기본값의 TDZ**.
- 이어지는 곳: [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」 — 이 주제에서 모드가 답을 바꾼 칸(중복 매개변수·`freeze` 의 조용한 실패)의 정본.
- 이어지는 곳: [목록의 **42번 주제**](../42-esm-modules/) 「ESM 모듈」 — 모듈의 최상위가 무엇이냐, 그리고 **모듈은 언제나 엄격**이라는 것.
- 경계 — 다른 언어의 같은 자리: [`python/syntax/21-scope-legb-global-nonlocal`](../../../python/syntax/21-scope-legb-global-nonlocal/2-summary.md) —
  **파이썬에는 블록 스코프가 없다.** `if`/`for` 안에서 만든 이름이 함수 전체에 산다 — JS 의 `var` 쪽에 가깝다.
  **그쪽은 「어느 스코프에서 찾나(LEGB)」까지, 여기는 「그 이름이 언제부터 쓸 수 있나」부터다.**
- 경계 — 연혁은 여기가 아니다: [`history/js/02-ES6-모던.md`](../../../../../../history/js/02-ES6-모던.md) — `let`/`const` 가 **언제 왜** 들어왔나.
- 경계 — 타입 이야기: TypeScript 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **01번**.
  **그쪽은 「타입은 런타임에 안 남는다」, 여기는 런타임 규칙이다.** `let`/`const` 는 **남는 쪽**이다.

## 용어 풀이

- **바인딩(binding)**: 이름과 값이 들어가는 창고 한 칸. 「변수」라고 부르는 것의 실체다.
- **호이스팅(hoisting)**: 선언이 스코프 맨 위로 끌어올려진 것처럼 보이는 현상. **셋 다 끌어올려지고, 초기화 시점만 다르다.**
- **TDZ (Temporal Dead Zone)**: `let`/`const`/`class` 의 이름이 만들어졌지만 아직 초기화되지 않은 구간. 읽어도 `typeof` 해도 `ReferenceError` 다.
- **블록 스코프(block scope)**: `{ }` 하나가 스코프가 되는 것. `let`/`const`/`class`/`function`(엄격) 이 여기 산다.
- **함수 스코프(function scope)**: 함수 하나가 스코프가 되는 것. `var` 가 여기 산다 — **블록을 무시한다.**
- **섀도잉(shadowing)**: 안쪽 스코프가 같은 이름으로 바깥 것을 가리는 것. **재선언이 아니다** — 다른 칸이다.
- **재선언(redeclaration)**: **같은 스코프**에서 같은 이름을 두 번 선언하는 것. `let`/`const` 가 걸리면 `SyntaxError` 다.
- **`globalThis`**: 어느 호스트에서든 전역 객체를 가리키는 표준 이름(ES2020). 브라우저의 `window`, Node 의 `global` 과 같은 것을 가리킨다.
- **모듈 래퍼(module wrapper)**: Node 의 CommonJS 가 `.js` 파일을 감싸는 함수. 인자가 `exports`·`require`·`module`·`__filename`·`__dirname` 다섯이다.
- **디스크립터(property descriptor)**: 프로퍼티의 성질표(`writable`·`enumerable`·`configurable`). 정본은 [목록의 **14번 주제**](../14-property-descriptors-and-freezing/)다.

## 더 들어가면

- **`class` 선언도 TDZ 에 들어간다**는 것이 `function` 과 갈리는 자리다. 문법이 선언처럼 생겼다고 호이스팅 방식이 같지는 않다 — 16번 주제의 일이다.
- **모듈(ESM)의 최상위는 또 다르다** — `this` 가 `undefined` 이고, 언제나 엄격이며, `var` 도 전역 객체에 안 붙는다.
  이 배치는 CommonJS 와 브라우저 classic script 두 자리만 던졌다. **ESM 은 42번 주제**의 몫이다.
- **`let` 의 TDZ 를 엔진이 어떻게 구현하나**(특별한 표식 값을 넣어 두고 읽을 때 검사하는 식)는 **이 주제가 아니다.**
  표준 API 로 관찰할 방법이 없고, 관찰하더라도 **명세 보장이 아니다.**
- **`with` 와 `eval` 이 스코프를 바꾸는 자리**는 엄격 모드에서 막히거나 쓰지 않는다 — 35번 주제에서 한 줄로 다룬다.
  이 문서의 `(0, eval)` 은 **전역 스코프에 닿기 위한 도구**로만 썼고 그 자체를 주제로 삼지 않았다.
- **안 돌려 본 것** — ESM(`.mjs`) 최상위 · Web Worker · `vm.createContext` 로 만든 다른 realm ·
  Node 18 보다 낮은 판 · 다른 엔진(SpiderMonkey·JavaScriptCore) · `--frozen-intrinsics` 같은 플래그.
