# js/syntax/07 — `this` 바인딩 네 규칙: 「이 호출식에서 `this` 는 무엇인가」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 함수 환경 레코드의 `this` · 함수 호출과 `new` · 화살표 함수
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — 엄격 모드와 화살표 함수가 들어온 판을 가릴 때
> - [MDN — `this`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this) · [MDN — `Function.prototype.bind`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> **어느 판에서 나왔는지는 아래 첫 블록**에 있다.

```sh
// js06b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    console.log("node " + v.node + "  v8 " + v.v8 +
                "  strict-this " + String((function(){ "use strict"; return this; })()) +
                "  globalThis " + Object.prototype.toString.call(globalThis) +
                "  arrow-proto " + Object.prototype.hasOwnProperty.call(() => {}, "prototype") +
                "  class-fields " + typeof (new (class { f = 1 })()).f);'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js06b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  strict-this undefined  globalThis [object global]  arrow-proto false  class-fields number
node 20.19.6  v8 11.3.244.8-node.33  strict-this undefined  globalThis [object global]  arrow-proto false  class-fields number
Google Chrome 151.0.7922.173 
```

> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 **`e.constructor.name` 과 `e.message` 만** 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박혀 다른 머신에서 재현이 안 되기 때문이다.
> 그래서 이 주제의 블록에는 **표준 오류가 한 줄도 섞이지 않는다** — 전부 표준 출력이다.
> ★★ **`SyntaxError` 는 `try`/`catch` 로 못 잡는다**(파싱 단계에서 나기 때문이다).
> 그래서 엄격/비엄격 격자는 `new Function(소스)` 으로 **두 번 컴파일**해 값과 문구를 받는다 — 파일로 던지면 진단에 경로가 박힌다.
> ★★ **`padEnd` 격자의 라벨은 전부 ASCII 다.** 한글은 터미널에서 두 칸이라 칸이 어긋난다.
> ★★ **`this` 는 브랜드 태그로 찍는다** — `Object.prototype.toString.call(this)`. `String(this)` 는 호스트마다 다르게 나온다.
>
> **버전** — `this` 네 규칙은 **초판부터**다. **엄격 모드는 ES5**, **화살표 함수와 `class` 는 ES2015**, **클래스 필드는 ES2022** 다.
> 이 주제에는 **시각·로캘·난수가 닿는 칸이 하나도 없다.**
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **브랜드 태그** `Object.prototype.toString.call` | `this` 가 무엇이 되어 있나 — `globalThis` 냐 래퍼 객체냐 호스트 객체냐 |
> | ★★★ **두 번 컴파일**(그대로 / `"use strict";` 붙여) | **설정이 답을 바꾸는 칸이 몇 개인가** — 세어서 고정 행으로 둔다 |
> | 두 호스트(Node·브라우저)에 같은 줄 던지기 | **ECMA-262 가 안 정하는 칸**이 어디인가 |
> | 예외의 종류·메시지 | 「조용한 실패」가 어디서 「시끄러운 실패」로 바뀌나 |
> | ★ **부적용** — 「값이 흔들리나 여러 번 돌려 본다」 | 이 주제에는 **난수·시각·순서 비보장이 한 칸도 없다.** 잴 것이 없다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **브랜드 태그**(`[object Object]`·`[object global]`·`[object Window]`) |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **엄격·비엄격이 갈린 칸의 개수** |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **예외의 종류** · `bound` 접두 · `length` 값 |
> | Node 타이머 객체의 **내부 필드** — 한 줄도 안 찍었다 | ★★ 타이머 콜백의 `this` 가 **`Timeout` 이라는 것**(호스트 사실) |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 54블록 전부 동일).
>
> **선행** — [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md).
> ★★★ **그 주제의 결론을 여기서 뒤집는다** — 이름은 **정의된 자리**가 정하지만 **`this` 는 호출식이 정한다.**
> ★ 예외가 딱 하나 있고 그것이 **화살표 함수**다(4번 절).
> **이어지는 곳** — [목록의 **08번 주제**](../08-function-forms-and-parameters/) 「함수 정의 형태와 매개변수」 · [목록의 **09번 주제**](../09-call-apply-bind/) 「`call`·`apply`·`bind`」
>
> ★★ **경계 — `call`·`apply`·`bind` 의 API 세부는 여기가 아니다.**
> 여기서는 「그 셋이 `this` 를 정한다」와 **「`bind` 가 두 번 안 먹는다」 두 가지**까지다. 인자 처리·성능·폴리필은 09번의 몫이다.

## 한눈에 — 쉽게 말하면

**`this` 는 함수에 붙어 있는 것이 아니라 「부를 때 같이 건네지는 숨은 인자」다.**

- 그래서 **같은 함수를 다르게 부르면 다른 값**이 들어온다. 함수를 아무리 들여다봐도 안 나온다.
- 무엇이 건네지는지는 **호출식의 모양** 하나로 정해진다 — 점 왼쪽이 있나, `call` 로 줬나, `new` 를 붙였나.
- 그래서 메서드를 **변수에 옮겨 담기만 해도** 점이 사라져 `this` 가 바뀐다.
- 화살표 함수만 예외다 — **자기 `this` 를 아예 안 만들어서** 바깥 것을 그대로 쓴다(06번의 이름 규칙과 같다).

```text
   함수 하나                          호출식 네 가지

   function who() { return this; }

     who()              ->  기본     : 비엄격이면 globalThis, 엄격이면 undefined
     holder.who()       ->  암시적   : 점 왼쪽의 객체
     who.call(target)   ->  명시적   : 첫 인자
     new who()          ->  new      : 갓 만든 새 객체

   ★ 함수는 한 번도 안 바뀌었다. 바뀐 것은 부르는 모양뿐이다.
```

**규칙이 겹치면 순서가 있다.**

```text
   new   >   bind / call / apply   >   점 왼쪽   >   기본

   new (who.bind(target))()      -> 새 객체        (new 가 이긴다)
   holder.who.call(target)       -> target        (call 이 이긴다)
   ({ w: who.bind(target) }).w() -> target        (bind 가 이긴다)
   holder.who()                  -> holder        (점 왼쪽)
   (0, holder.who)()             -> 기본          (★ 점이 사라졌다)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 숨은 인자 | 호출마다 함수에 건네지는 `this` | 같은 함수를 다르게 불러 본다 |
| 점 왼쪽의 객체 | 암시적 바인딩 | `o.m()` |
| 손으로 건넨다 | `call`·`apply`·`bind` | 첫 인자가 그대로 들어온다 |
| 못질해 둔 봉투 | `bind` 가 만든 새 함수 | 두 번 감싸도 **안쪽이 이긴다** |
| 갓 만든 빈 상자 | `new` 가 만든 객체 | 프로토타입이 `C.prototype` 이다 |
| 봉투에 안 든 편지 | 떼어 낸 메서드 | 점이 없어져 기본 바인딩이 된다 |
| 창문이 없는 방 | 화살표 함수 | 자기 `this` 를 안 만들어 바깥 것이 보인다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
`setTimeout(obj.method, 0)` 이 조용히 엉뚱한 값을 쓰는 사고가 그것이고,
클래스 메서드를 이벤트 핸들러로 넘겼더니 `this.state` 가 `undefined` 인 사고가 그것이다.
**둘 다 「점이 사라졌다」 한 문장이 답이다.**

> **바인딩(binding)** — 호출할 때 `this` 에 무엇이 들어갈지 정해지는 일.
> 예: `o.m()` 은 `o` 가 들어간다. **함수를 정의할 때가 아니라 부를 때** 정해진다.

> **엄격 모드(strict mode)** — `"use strict";` 로 켜는 더 깐깐한 규칙 집합(ES5).
> 예: 기본 바인딩의 `this` 가 `globalThis` 가 아니라 `undefined` 다. **모듈과 `class` 몸통은 언제나 엄격**이다.
> 정본은 목록의 **35번 주제**다.

## 이 주제가 답하려는 질문

1. **임의의 호출식을 보고 `this` 를 판정할 수 있나** — 네 규칙과 그 우선순위로.
2. **왜 메서드를 옮겨 담기만 해도 깨지나** — 그리고 그 실패가 왜 **조용한가.**
3. **설정이 답을 바꾸는 칸이 몇 개인가** — 엄격 모드와 호스트가 각각 어디를 바꾸나.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### (1) ★★★ 네 규칙 — 같은 함수를 아홉 가지로 부른다

**언제 쓰나** — 「이 호출식에서 `this` 가 뭐지?」를 물을 때. 모든 문항의 출발점이다.

```text
   호출식을 보고 이 순서로 묻는다

   1) new 가 붙었나?            -> 갓 만든 객체
   2) bind / call / apply 인가? -> 그때 준 것
   3) 점 왼쪽이 있나?           -> 점 왼쪽의 객체
   4) 아무것도 아니면           -> 기본 (비엄격 globalThis · 엄격 undefined)

   ★ 함수 본문을 읽어서는 답이 안 나온다. 답은 호출식에 있다.
```

```js
// js06b-07a-four-rules.js
// this 는 함수에 붙어 있지 않다 -- 호출식의 모양이 정한다. 네 규칙을 한 함수로 확인한다.
// 브랜드 태그는 Object.prototype.toString.call 로 찍는다.
function tag(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") {
    const brand = Object.prototype.toString.call(t);
    return brand + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}

// 이 한 함수를 네 가지 모양으로 부른다. 함수는 처음부터 끝까지 같은 객체다.
function who() { return tag(this); }

const holder = { mark: "holder", who };
const nested = { mark: "outer", inner: { mark: "inner", who } };
const arr = [who];
arr.mark = "array";

console.log("[1] 네 규칙 -- 같은 함수, 다른 호출식");
const calls = [
  ["default   who()", () => who()],
  ["implicit  holder.who()", () => holder.who()],
  ["implicit  nested.inner.who()", () => nested.inner.who()],
  ["implicit  obj['who']()", () => holder["who"]()],
  ["implicit  arr[0]()", () => arr[0]()],
  ["explicit  who.call(o)", () => who.call({ mark: "called" })],
  ["explicit  who.apply(o)", () => who.apply({ mark: "applied" })],
  ["explicit  who.bind(o)()", () => who.bind({ mark: "bound" })()],
  ["new       new who()", () => new who()],
];
for (const [label, run] of calls) console.log("  " + label.padEnd(30) + " -> " + run());

console.log("");
console.log("[2] 우선순위 -- 한 호출식에 규칙이 둘 이상 걸리면");
console.log("  " + "new beats bind".padEnd(30) + " -> " + tag(new (who.bind({ mark: "bound" }))()));
console.log("  " + "call beats implicit".padEnd(30) + " -> " + holder.who.call({ mark: "called" }));
console.log("  " + "bind beats implicit".padEnd(30) + " -> " + ({ mark: "host", w: who.bind({ mark: "bound" }) }).w());

console.log("");
console.log("[3] 점 왼쪽이 있어도 암시적 바인딩이 아닌 자리");
console.log("  " + "(holder.who)()".padEnd(30) + " -> " + (holder.who)());
console.log("  " + "(0, holder.who)()".padEnd(30) + " -> " + (0, holder.who)());
console.log("  " + "(holder.who = holder.who)()".padEnd(30) + " -> " + (holder.who = holder.who)());
console.log("  " + "(true && holder.who)()".padEnd(30) + " -> " + (true && holder.who)());
console.log("  " + "holder?.who()".padEnd(30) + " -> " + holder?.who());

console.log("");
console.log("[4] 원시값을 this 로 주면 -- 비엄격은 감싸고 엄격은 그대로 둔다");
function looseThis() { return tag(this); }
function strictThis() { "use strict"; return tag(this); }
for (const v of [7, "s", true, null, undefined]) {
  console.log("  this = " + String(v).padEnd(10) +
              " sloppy " + looseThis.call(v).padEnd(24) +
              " strict " + strictThis.call(v));
}
```

```text
===== node20 js06b-07a-four-rules.js (exit=0) =====
[1] 네 규칙 -- 같은 함수, 다른 호출식
  default   who()                -> globalThis
  implicit  holder.who()         -> [object Object] mark=holder
  implicit  nested.inner.who()   -> [object Object] mark=inner
  implicit  obj['who']()         -> [object Object] mark=holder
  implicit  arr[0]()             -> [object Array] mark=array
  explicit  who.call(o)          -> [object Object] mark=called
  explicit  who.apply(o)         -> [object Object] mark=applied
  explicit  who.bind(o)()        -> [object Object] mark=bound
  new       new who()            -> [object Object]

[2] 우선순위 -- 한 호출식에 규칙이 둘 이상 걸리면
  new beats bind                 -> [object Object]
  call beats implicit            -> [object Object] mark=called
  bind beats implicit            -> [object Object] mark=bound

[3] 점 왼쪽이 있어도 암시적 바인딩이 아닌 자리
  (holder.who)()                 -> [object Object] mark=holder
  (0, holder.who)()              -> globalThis
  (holder.who = holder.who)()    -> globalThis
  (true && holder.who)()         -> globalThis
  holder?.who()                  -> [object Object] mark=holder

[4] 원시값을 this 로 주면 -- 비엄격은 감싸고 엄격은 그대로 둔다
  this = 7          sloppy [object Number]          strict number 7
  this = s          sloppy [object String]          strict string s
  this = true       sloppy [object Boolean]         strict boolean true
  this = null       sloppy globalThis               strict null
  this = undefined  sloppy globalThis               strict undefined
```

그림 해설 (한 단계씩).

- ★★★ **`[1]` 의 아홉 줄이 전부 같은 `who` 다.** 함수는 한 번도 안 바뀌었고 **부르는 모양만** 바뀌었다.
  ★ 점 왼쪽이 **중첩이면 바로 왼쪽**이 이긴다(`nested.inner.who()` 가 `inner`), 배열도 마찬가지다(`arr[0]()` 가 배열 자신).
- ★★★ **`[2]` 가 우선순위다.** `new` 가 `bind` 를 이기고, `call`·`bind` 가 점 왼쪽을 이긴다.
  ★ 그래서 **`new` 만이 「되돌릴 수 없는 `bind`」를 되돌린다**(5번 절이 그 자리를 따로 본다).
- ★★★ **`[3]` 이 이 주제에서 가장 조용한 자리다.** `holder.who` 라고 써 놓고도 `this` 를 잃는 모양이 넷이다 —
  `(0, holder.who)()` · `(holder.who = holder.who)()` · `(true && holder.who)()`.
  ★★ **점 왼쪽이 있어도 「그 자리에서 바로 부르지」 않으면** 암시적 바인딩이 안 붙는다.
  ★ 반대로 **괄호로만 감싼 것과 `?.` 는 그대로 붙는다** — 둘은 참조가 안 풀리기 때문이다.
- ★★ **`[4]` 는 원시값을 `this` 로 줬을 때다.** 비엄격은 **객체로 감싸고**(`[object Number]`) 엄격은 **그대로 둔다**(`number 7`).
  `null`·`undefined` 는 비엄격에서 **`globalThis` 로 바뀐다** — 엄격에서는 그대로다.
  ★★★ **이것이 「설정이 답을 바꾸는 칸」의 첫 다섯 줄**이고, 2번 절이 그 개수를 센다.

**비용** — 호출식이 정하니 **한 함수를 여러 객체에 붙여 쓸 수 있다**(`call`·`apply` 의 쓸모).
대신 **함수만 봐서는 판정이 안 된다** — 읽는 사람이 호출부를 전부 찾아야 한다.

### (2) ★★★ 엄격 모드가 답을 바꾸는 칸이 몇 개인가 — 세어서 고정 행으로

**언제 쓰나** — 「이 코드가 엄격인가?」를 먼저 묻지 않으면 답이 안 서는 자리가 어디인지 알아 둘 때.

같은 탐침 소스를 **두 번 컴파일**한다 — 그대로(비엄격) 한 번, 앞에 `"use strict";` 를 붙여 한 번.
**둘을 글자로 비교해 갈린 칸을 기계가 센다.**

```js
// js06b-07b-mode-matrix.js
// 엄격 모드가 this 의 답을 바꾸는 칸이 몇 개인가 -- 세어서 고정 행으로 둔다.
// 같은 탐침 소스를 두 번 컴파일한다: 그대로(비엄격)와 "use strict"; 를 앞에 붙여(엄격).
// new Function 을 쓰는 이유 -- 파일로 던지면 진단에 절대 경로가 박힌다. 여기서는 값만 받는다.
const HELPERS = `
  function tag(t) {
    if (t === undefined) return "undefined";
    if (t === null) return "null";
    if (t === globalThis) return "globalThis";
    if (typeof t === "object" || typeof t === "function") return Object.prototype.toString.call(t);
    return typeof t + " " + String(t);
  }
`;

function run(src, strict) {
  // ★ @@ 는 모드마다 다른 이름으로 바꾼다.
  //   한 이름을 두 모드가 나눠 쓰면 앞 모드가 만든 전역 때문에 뒤 모드의 답이 바뀐다(실제로 그랬다).
  src = src.replace(/@@/g, "undeclared_" + (strict ? "strict" : "sloppy"));
  const body = (strict ? '"use strict";\n' : "") + HELPERS + "\nreturn (" + src + ");";
  try { return String(new Function(body)()); }
  catch (e) { return e.constructor.name + ": " + e.message; }
}

const probes = [
  ["plain call", "(function () { return tag(this); })()"],
  ["callback of forEach", "(function () { var r; [1].forEach(function () { r = tag(this); }); return r; })()"],
  ["this from call(7)", "(function () { return tag(this); }).call(7)"],
  ["this from call(null)", "(function () { return tag(this); }).call(null)"],
  ["this from call(undefined)", "(function () { return tag(this); }).call(undefined)"],
  ["detached method (guarded)", "(function () { var o = { n: 'obj', m: function () { return String(this && this.n); } }; var d = o.m; return d(); })()"],
  ["detached method (unguarded)", "(function () { var o = { n: 'obj', m: function () { return String(this.n); } }; var d = o.m; return d(); })()"],
  ["method kept on the object", "(function () { var o = { n: 'obj', m: function () { return String(this.n); } }; return o.m(); })()"],
  ["arrow at top of the fn", "(function () { return (() => tag(this))(); })()"],
  ["arrow called with call(7)", "(function () { var a = () => tag(this); return a.call(7); })()"],
  ["this inside new", "(function () { function C() { this.x = 1; } return JSON.stringify(new C()); })()"],
  ["assigning to an undeclared name", "(function () { @@ = 1; return 'assigned ' + String(globalThis['@@']); })()"],
  ["this in a getter", "(function () { var o = { n: 'g', get v() { return String(this.n); } }; return o.v; })()"],
  ["setTimeout-like: fn passed along", "(function () { function pass(f) { return f(); } var o = { n: 'obj', m: function () { return String(this && this.n); } }; return pass(o.m); })()"],
];

let differ = 0;
console.log("  " + "probe".padEnd(34) + "sloppy".padEnd(26) + "strict");
console.log("  " + "-".repeat(34) + "-".repeat(26) + "-".repeat(26));
for (const [label, src] of probes) {
  const a = run(src, false), b = run(src, true);
  if (a !== b) differ += 1;
  console.log("  " + label.padEnd(34) + a.padEnd(26) + b + (a === b ? "" : "   <- differs"));
}
console.log("");
console.log("  probes " + probes.length + " · same " + (probes.length - differ) + " · DIFFER " + differ);
```

```text
===== node20 js06b-07b-mode-matrix.js (exit=0) =====
  probe                             sloppy                    strict
  --------------------------------------------------------------------------------------
  plain call                        globalThis                undefined   <- differs
  callback of forEach               globalThis                undefined   <- differs
  this from call(7)                 [object Number]           number 7   <- differs
  this from call(null)              globalThis                null   <- differs
  this from call(undefined)         globalThis                undefined   <- differs
  detached method (guarded)         undefined                 undefined
  detached method (unguarded)       undefined                 TypeError: Cannot read properties of undefined (reading 'n')   <- differs
  method kept on the object         obj                       obj
  arrow at top of the fn            globalThis                undefined   <- differs
  arrow called with call(7)         globalThis                undefined   <- differs
  this inside new                   {"x":1}                   {"x":1}
  assigning to an undeclared name   assigned 1                ReferenceError: undeclared_strict is not defined   <- differs
  this in a getter                  g                         g
  setTimeout-like: fn passed along  undefined                 undefined

  probes 14 · same 5 · DIFFER 9
```

그림 해설.

- ★★★ **열네 칸 중 아홉이 갈린다.** 이 한 줄이 이 주제의 고정 행이다 — **`this` 는 「설정에 달린」 기능**이다.
- ★★★ **가장 아픈 것은 「떼어 낸 메서드」 두 줄**이다.
  방어를 넣은 판(`this && this.n`)은 **두 모드가 같은 글자**를 내는데 **이유가 다르다** —
  비엄격은 `globalThis.n` 이 `undefined` 라서, 엄격은 `this` 가 `undefined` 라서다.
  ★★ 방어를 빼면 **비엄격은 여전히 `undefined` 이고 엄격은 `TypeError`** 다.
  **같은 버그가 한쪽에서는 조용하고 한쪽에서는 시끄럽다** — 3번 절이 그 자리를 편다.
- ★★ **화살표 두 줄도 갈린다.** 화살표는 자기 `this` 를 안 만드는데, **바깥의 `this` 자체가 모드에 따라 다르므로** 같이 갈린다.
  ★ 「화살표는 `this` 가 없다」가 아니라 「**자기 것을 안 만들고 바깥 것을 쓴다**」가 맞는 문장이라는 증거다.
- ★ **안 갈리는 다섯 칸**이 있다 — 점 왼쪽이 붙어 있는 메서드, `new` 안의 `this`, 게터 안의 `this`,
  그리고 **떼어 낸 메서드를 다른 함수가 대신 부르는 자리**(둘 다 `undefined`). **점이 붙어 있으면 모드가 상관없다.**
- ★ 탐침 소스에서 **이름을 모드마다 다르게** 만든 것에 이유가 있다.
  한 이름을 두 모드가 나눠 쓰면 **비엄격 판이 만든 전역 때문에 엄격 판이 안 터진다** — 실제로 그렇게 한 번 잘못 나왔다.

**비용** — 엄격 모드는 **조용한 실패를 시끄럽게** 만든다. 대신 **옛 코드의 답이 바뀐다** —
그래서 `"use strict"` 를 파일 위에 얹는 것만으로도 동작이 달라지는 자리가 아홉 칸이나 된다.

### (3) ★★★ 메서드를 떼어 내면 — 그리고 그 실패가 조용하다

**언제 쓰나** — 「분명히 `user.greet` 인데 왜 이름이 없지?」를 만났을 때.

```text
   user = { name: "kim", greet() { return "hi " + this.name } }

   user.greet()            점이 있다   ->  this = user        -> "hi kim"
   const g = user.greet    점이 사라진다
   g()                     점이 없다   ->  this = globalThis  -> "hi undefined"
                                            ^
                           ★ 함수 객체는 똑같다. g === user.greet 가 true 다.
```

```js
// js06b-07c-detached.js
// 메서드를 떼어 내면 this 를 잃는다 -- 그리고 그 실패가 조용하다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(36) + " -> " + r);
}

const user = {
  name: "kim",
  greet() { return "hi " + this.name; },
};

console.log("[1] 같은 함수인데 점이 있고 없고로 갈린다");
probe("user.greet()", () => user.greet());
probe("const g = user.greet; g()", () => { const g = user.greet; return g(); });
probe("same function object?", () => { const g = user.greet; return g === user.greet; });

console.log("");
console.log("[2] 떼어 내는 모양이 여럿이다 -- 전부 같은 사고다");
probe("passed to another function", () => { const call = (f) => f(); return call(user.greet); });
probe("stored in an array", () => { const a = [user.greet]; return a[0](); });
probe("assigned to another object", () => { const other = { name: "lee" }; other.greet = user.greet; return other.greet(); });
probe("used as a callback of map", () => [1].map(user.greet)[0]);
probe("destructured out", () => { const { greet } = user; return greet(); });

console.log("");
console.log("[3] 왜 조용한가 -- this 가 무엇이 되어 있나");
function where() { return Object.prototype.toString.call(this) + " name=" + JSON.stringify(this && this.name); }
const holder2 = { name: "kim", where };
probe("holder2.where()", () => holder2.where());
probe("detached where()", () => { const w = holder2.where; return w(); });
probe("globalThis.name in this host", () => globalThis.name);

console.log("");
console.log("[4] 엄격 모드에서는 조용하지 않다");
const strictUser = {
  name: "kim",
  greet() { "use strict"; return "hi " + this.name; },
};
probe("strict method, attached", () => strictUser.greet());
probe("strict method, detached", () => { const g = strictUser.greet; return g(); });

console.log("");
console.log("[5] 고치는 세 가지 -- 무엇을 옮기는지가 다르다");
probe("bind at handoff", () => { const g = user.greet.bind(user); return g(); });
probe("wrap in an arrow", () => { const g = () => user.greet(); return g(); });
probe("bind in the constructor-ish factory", () => {
  function make(name) { const self = { name }; self.greet = user.greet.bind(self); return self; }
  const m = make("park");
  const g = m.greet;
  return g();
});
probe("arrow as the method itself", () => {
  const bad = { name: "kim", greet: () => "hi " + String(this && this.name) };
  return bad.greet();
});
```

```text
===== node20 js06b-07c-detached.js (exit=0) =====
[1] 같은 함수인데 점이 있고 없고로 갈린다
  user.greet()                         -> "hi kim"
  const g = user.greet; g()            -> "hi undefined"
  same function object?                -> true

[2] 떼어 내는 모양이 여럿이다 -- 전부 같은 사고다
  passed to another function           -> "hi undefined"
  stored in an array                   -> "hi undefined"
  assigned to another object           -> "hi lee"
  used as a callback of map            -> "hi undefined"
  destructured out                     -> "hi undefined"

[3] 왜 조용한가 -- this 가 무엇이 되어 있나
  holder2.where()                      -> "[object Object] name=\"kim\""
  detached where()                     -> "[object global] name=undefined"
  globalThis.name in this host         -> undefined

[4] 엄격 모드에서는 조용하지 않다
  strict method, attached              -> "hi kim"
  strict method, detached              -> TypeError: Cannot read properties of undefined (reading 'name')

[5] 고치는 세 가지 -- 무엇을 옮기는지가 다르다
  bind at handoff                      -> "hi kim"
  wrap in an arrow                     -> "hi kim"
  bind in the constructor-ish factory  -> "hi park"
  arrow as the method itself           -> "hi undefined"
```

그림 해설.

- ★★★ **`g === user.greet` 가 `true` 다.** 함수는 그대로이고 **호출식만 바뀌었다.**
- ★★★ **`[2]` 의 다섯 줄이 전부 같은 사고**다 — 다른 함수에 넘기기·배열에 담기·구조 분해·`map` 콜백.
  ★ 그중 **`other.greet = user.greet` 만 답이 다르다**(`"hi lee"`) — **점이 새로 생겼기** 때문이다. 이 줄이 규칙을 거꾸로 확인해 준다.
- ★★★ **`[3]` 이 「왜 조용한가」를 설명한다.** `this` 가 `globalThis` 가 되었고 **`globalThis.name` 이 이 호스트에서 `undefined`** 다.
  ★★ **브라우저에서는 `window.name` 이 빈 문자열이라 `"hi "` 가 나온다**(8번 절) — **호스트에 따라 조용함의 모양까지 달라진다.**
  [05번](../05-var-let-const-and-tdz/2-summary.md)이 `window.name` 이 `""` 인 것을 기억해 두라고 한 자리가 여기다.
- ★★ **`[4]` 가 엄격 모드를 대비한다.** 같은 코드가 `TypeError: Cannot read properties of undefined (reading 'name')` 가 된다.
  **틀린 것이 값이 아니라 예외로 바뀐다.**
- ★★ **`[5]` 의 고침 셋이 각각 다른 것을 옮긴다** — `bind` 는 **함수를 새로 만들고**, 화살표 래퍼는 **호출식을 감추지 않고 그대로 둔다**,
  팩토리에서 미리 `bind` 하면 **떼어 내도 안 깨진다**(`"hi park"`).
  ★ **마지막 줄이 함정이다** — 화살표를 **메서드 자리에 쓰면** 고쳐지지 않는다(4번 절).

**비용** — 조용한 실패는 **테스트가 통과하는데 값만 틀린** 모양으로 나온다.
엄격 모드나 화살표 래퍼가 그것을 막지만, **`bind` 는 함수 객체를 하나 더 만든다**(★ 비용은 안 쟀다).

### (4) ★★★ 화살표 함수 — 자기 `this` 를 안 만든다

**언제 쓰나** — 콜백 안에서 `this` 가 사라질 때, 그리고 **메서드 자리에 화살표를 쓰고 싶을 때**(쓰면 안 된다).

```text
   06번의 이름 규칙                     this 규칙

   const where = "outer"                obj.method() { ... }
   function f() { return where }          const inner = () => this
      ^ 정의된 자리에서 바깥으로              ^ 정의된 자리에서 바깥으로

   ★ 화살표의 this 는 "이름처럼" 찾는다 — 이 주제에서 유일하게 렉시컬한 칸이다.
   ★ 그래서 call/apply/bind 로도 못 바꾼다. 바꿀 자기 칸이 없기 때문이다.
```

```js
// js06b-07d-arrow.js
// 화살표 함수는 this 를 만들지 않는다 -- 그래서 06번의 스코프 규칙이 this 에도 그대로 적용된다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(38) + " -> " + r);
}
function brand(t) {
  if (t === undefined) return "undefined";
  if (t === globalThis) return "globalThis";
  return Object.prototype.toString.call(t) + (t && t.mark ? " mark=" + t.mark : "");
}

console.log("[1] 화살표는 바깥에서 this 를 가져온다 -- 이름을 찾듯이");
const obj = {
  mark: "obj",
  withFunction() { const inner = function () { return brand(this); }; return inner(); },
  withArrow() { const inner = () => brand(this); return inner(); },
  deepArrow() { const a = () => () => () => brand(this); return a()()(); },
};
probe("method + inner function()", () => obj.withFunction());
probe("method + inner arrow", () => obj.withArrow());
probe("three arrows deep", () => obj.deepArrow());

console.log("");
console.log("[2] 화살표는 call/apply/bind 로도 안 바뀐다");
const fnAt = { mark: "host2", f() { const a = () => brand(this); return [a(), a.call({ mark: "forced" }), a.apply({ mark: "forced" }), a.bind({ mark: "forced" })()]; } };
probe("arrow: plain / call / apply / bind", () => fnAt.f());
const normal = { mark: "host3", f() { const n = function () { return brand(this); }; return [n(), n.call({ mark: "forced" })]; } };
probe("function(): plain / call", () => normal.f());

console.log("");
console.log("[3] 화살표를 메서드로 쓰면 깨진다");
const broken = { mark: "broken", who: () => brand(this) };
const fine = { mark: "fine", who() { return brand(this); } };
probe("arrow as a method", () => broken.who());
probe("shorthand method", () => fine.who());
probe("what the arrow actually saw", () => brand(this));

console.log("");
console.log("[4] 그런데 콜백으로는 화살표가 맞는 도구다");
const timer = {
  mark: "timer",
  ticks: 0,
  runFunction() { const out = []; [1, 2].forEach(function () { out.push(brand(this)); }); return out; },
  runArrow() { const out = []; [1, 2].forEach(() => out.push(brand(this))); return out; },
};
probe("forEach + function()", () => timer.runFunction());
probe("forEach + arrow", () => timer.runArrow());

console.log("");
console.log("[5] 화살표에 없는 것이 this 만은 아니다");
probe("new on an arrow", () => { const A = () => {}; return new A(); });
probe("arrow has a prototype property?", () => Object.prototype.hasOwnProperty.call(() => {}, "prototype"));
probe("function has one?", () => Object.prototype.hasOwnProperty.call(function () {}, "prototype"));
probe("class field arrow keeps this", () => {
  class C { mark = "C"; who = () => brand(this); }
  const c = new C();
  const detached = c.who;
  return [c.who(), detached()];
});
probe("class method loses this", () => {
  class C { constructor() { this.mark = "C"; } who() { return brand(this); } }
  const c = new C();
  const detached = c.who;
  return [c.who(), detached()];
});
```

```text
===== node20 js06b-07d-arrow.js (exit=0) =====
[1] 화살표는 바깥에서 this 를 가져온다 -- 이름을 찾듯이
  method + inner function()              -> "globalThis"
  method + inner arrow                   -> "[object Object] mark=obj"
  three arrows deep                      -> "[object Object] mark=obj"

[2] 화살표는 call/apply/bind 로도 안 바뀐다
  arrow: plain / call / apply / bind     -> ["[object Object] mark=host2","[object Object] mark=host2","[object Object] mark=host2","[object Object] mark=host2"]
  function(): plain / call               -> ["globalThis","[object Object] mark=forced"]

[3] 화살표를 메서드로 쓰면 깨진다
  arrow as a method                      -> "[object Object]"
  shorthand method                       -> "[object Object] mark=fine"
  what the arrow actually saw            -> "[object Object]"

[4] 그런데 콜백으로는 화살표가 맞는 도구다
  forEach + function()                   -> ["globalThis","globalThis"]
  forEach + arrow                        -> ["[object Object] mark=timer","[object Object] mark=timer"]

[5] 화살표에 없는 것이 this 만은 아니다
  new on an arrow                        -> TypeError: A is not a constructor
  arrow has a prototype property?        -> false
  function has one?                      -> true
  class field arrow keeps this           -> ["[object Object] mark=C","[object Object] mark=C"]
  class method loses this                -> ["[object Object] mark=C","undefined"]
```

그림 해설.

- ★★★ **`[1]` 의 두 줄이 대비다.** 메서드 안에서 `function` 으로 만든 안쪽 함수는 `this` 를 잃고(`globalThis`),
  화살표는 **메서드의 `this` 를 그대로 본다**(`mark=obj`). 세 겹을 겹쳐도 같다.
- ★★★ **`[2]` 가 「못 바꾼다」를 보인다.** 화살표에 `call`·`apply`·`bind` 를 걸어도 **네 값이 전부 같다.**
  ★★ 같은 자리의 `function` 은 `call` 로 바뀐다 — **바꿀 자기 칸이 있느냐가 갈림**이다.
- ★★★ **`[3]` 이 「메서드로 쓰면 깨진다」를 보인다.** 화살표 메서드의 `this` 는 **그 객체가 아니라 그 객체 리터럴을 쓴 자리의 `this`** 다.
  ★ 여기서는 Node CommonJS 의 최상위 `this`(=`module.exports`)라 `[object Object]` 인데, **브라우저에서는 `window`** 다(8번 절).
  ★★ **「`[object Object]` 니까 맞게 나온 것 아닌가?」가 함정**이다 — 세 번째 줄이 그것이 **객체 리터럴이 아님**을 보인다.
- ★★ **`[4]` 는 화살표가 맞는 도구인 자리다.** 메서드 안에서 `forEach` 콜백으로 쓰면 `this` 가 그대로 이어진다.
- ★★ **`[5]` 가 「없는 것이 `this` 만은 아님」을 보인다.** 화살표는 `new` 를 못 받고 `prototype` 프로퍼티도 없다.
  ★★★ **클래스 필드 화살표는 떼어 내도 안 깨진다**(`["...mark=C","...mark=C"]`) — **인스턴스마다 못질되기** 때문이다.
  같은 자리의 **클래스 메서드는 떼면 `undefined`** 다. 정본은 [목록의 **16번 주제**](../16-class-syntax/)다.

**비용** — 화살표는 **콜백에서 `bind` 를 없애 준다.** 대신 **메서드·생성자·`prototype` 자리에 못 쓰고**,
클래스 필드 화살표는 **인스턴스마다 함수를 하나씩 만든다**(★ 비용은 안 쟀다).

### (5) ★★ `bind` — 두 번 감싸도 안쪽이 이긴다

**언제 쓰나** — 넘기기 전에 `this` 를 못질할 때. 그리고 「왜 다시 `bind` 해도 안 바뀌지?」를 물을 때.

```text
   who.bind(A)          ->  새 함수 B1 (A 가 못질됨)
   B1.bind(B)           ->  또 새 함수 B2
       B2 를 부르면 B2 가 B1 을 부르는데, B1 은 이미 A 로 못질돼 있다
       -> B2 의 this 는 무시된다  -> A

   ★ "덮어쓴다"가 아니라 "한 겹 더 감싼다"이기 때문이다.
   ★ 인자도 같다 — 앞에서부터 박히고 되돌릴 수 없다.
```

```js
// js06b-07e-bind.js
// bind 가 만드는 것은 새 함수다 -- 그래서 두 번 감싸도 안쪽이 이긴다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(38) + " -> " + r);
}
function who() { return this && this.mark; }

console.log("[1] 두 번 bind 해도 안쪽이 이긴다");
probe("bind(A)()", () => who.bind({ mark: "A" })());
probe("bind(A).bind(B)()", () => who.bind({ mark: "A" }).bind({ mark: "B" })());
probe("bind(A).call(B)", () => who.bind({ mark: "A" }).call({ mark: "B" }));
probe("bind(A).apply(B)", () => who.bind({ mark: "A" }).apply({ mark: "B" }));
probe("attached as a method of B", () => { const o = { mark: "B" }; o.w = who.bind({ mark: "A" }); return o.w(); });

console.log("");
console.log("[2] bind 는 새 함수다 -- 원본은 그대로다");
probe("bound === original", () => who.bind({}) === who);
probe("two binds of the same fn are equal?", () => who.bind({}) === who.bind({}));
probe("original still floats", () => who());

console.log("");
console.log("[3] 인자도 앞에서부터 박힌다 -- 그것도 되돌릴 수 없다");
function add(a, b, c) { return [a, b, c]; }
probe("add.bind(null, 1)(2, 3)", () => add.bind(null, 1)(2, 3));
probe("add.bind(null, 1).bind(null, 9)(3)", () => add.bind(null, 1).bind(null, 9)(3));
probe("add.bind(null, 1, 2, 3)(9, 9)", () => add.bind(null, 1, 2, 3)(9, 9));

console.log("");
console.log("[4] 바인딩된 함수의 이름과 length");
function named(a, b, c) {}
probe("name / length of the original", () => [named.name, named.length]);
probe("name / length after bind(null)", () => { const b = named.bind(null); return [b.name, b.length]; });
probe("name / length after bind(null, 1)", () => { const b = named.bind(null, 1); return [b.name, b.length]; });
probe("name after two binds", () => named.bind(null).bind(null).name);
probe("bound fn has a prototype property?", () => Object.prototype.hasOwnProperty.call(named.bind(null), "prototype"));

console.log("");
console.log("[5] new 는 bind 를 이긴다 -- 이 한 자리만 예외다");
function C(x) { this.x = x; }
const Bound = C.bind({ mark: "ignored" }, 7);
probe("new Bound()", () => new Bound());
probe("prototype chain still points at C", () => Object.getPrototypeOf(new Bound()) === C.prototype);
probe("instanceof C", () => new Bound() instanceof C);
probe("Bound() without new (sloppy)", () => { Bound(); return "no throw"; });
probe("new on a bound arrow", () => { const A = (() => {}).bind(null); return new A(); });
```

```text
===== node20 js06b-07e-bind.js (exit=0) =====
[1] 두 번 bind 해도 안쪽이 이긴다
  bind(A)()                              -> "A"
  bind(A).bind(B)()                      -> "A"
  bind(A).call(B)                        -> "A"
  bind(A).apply(B)                       -> "A"
  attached as a method of B              -> "A"

[2] bind 는 새 함수다 -- 원본은 그대로다
  bound === original                     -> false
  two binds of the same fn are equal?    -> false
  original still floats                  -> undefined

[3] 인자도 앞에서부터 박힌다 -- 그것도 되돌릴 수 없다
  add.bind(null, 1)(2, 3)                -> [1,2,3]
  add.bind(null, 1).bind(null, 9)(3)     -> [1,9,3]
  add.bind(null, 1, 2, 3)(9, 9)          -> [1,2,3]

[4] 바인딩된 함수의 이름과 length
  name / length of the original          -> ["named",3]
  name / length after bind(null)         -> ["bound named",3]
  name / length after bind(null, 1)      -> ["bound named",2]
  name after two binds                   -> "bound bound named"
  bound fn has a prototype property?     -> false

[5] new 는 bind 를 이긴다 -- 이 한 자리만 예외다
  new Bound()                            -> {"x":7}
  prototype chain still points at C      -> true
  instanceof C                           -> true
  Bound() without new (sloppy)           -> "no throw"
  new on a bound arrow                   -> TypeError: A is not a constructor
```

그림 해설.

- ★★★ **`[1]` 의 다섯 줄이 전부 `"A"`** 다. 두 번 `bind` 하든 `call`·`apply` 로 덮든 점을 새로 붙이든 **안쪽이 이긴다.**
- ★★ **`[2]` 가 「새 함수다」를 보인다.** `bind` 의 결과는 원본과 다른 객체이고, 두 번 `bind` 한 것끼리도 다르다.
  **원본은 그대로 떠다닌다**(`undefined`).
- ★★ **`[3]` 은 인자도 같은 성질임을 보인다.** `add.bind(null, 1).bind(null, 9)(3)` 이 `[1,9,3]` 이다 —
  **앞에서부터 차례로 박히고 지워지지 않는다.** 다 채운 뒤의 인자는 **버려진다**(`[1,2,3]`).
- ★★ **`[4]` 가 흔적을 보인다.** 이름에 **`bound ` 가 접두**로 붙고(두 번이면 `bound bound named`),
  `length` 는 **박은 인자 수만큼 줄어든다**(`3` → `2`). **`prototype` 프로퍼티는 없다.**
- ★★★ **`[5]` 가 유일한 예외다.** `new` 는 `bind` 가 못질한 `this` 를 **무시하고** 새 객체를 만든다.
  ★ 프로토타입도 **원본의 것**을 쓰므로 `instanceof C` 가 `true` 다. **박아 둔 인자는 그대로 남는다**(`{"x":7}`).
  ★ 화살표는 `bind` 해도 여전히 생성자가 아니다.

**비용** — `bind` 는 **한 번 정하면 못 바꾸는** 대신 읽는 사람에게 확실하다.
대신 **함수 객체가 하나 더 생기고**(★ 비용은 안 쟀다) `new` 와 섞이면 헷갈린다.

### (6) ★★ `new` 가 하는 네 단계

**언제 쓰나** — 「`new` 를 빼먹으면 무슨 일이 나나」를 물을 때.

```text
   new Point(1, 2)

   (1) 빈 객체를 만든다                 {}
   (2) 그 객체의 프로토타입을 Point.prototype 으로 잇는다
   (3) 그 객체를 this 로 해서 몸통을 돌린다   this.x = 1; this.y = 2
   (4) 몸통이 객체를 돌려주지 않았으면 그 객체를 돌려준다

   ★ (4)만 예외가 있다 — 객체를 돌려주면 그것이 이긴다. 원시값은 무시된다.
```

```js
// js06b-07f-new.js
// new 는 네 단계를 한다 -- 각 단계를 따로 관찰한다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(40) + " -> " + r);
}

function Point(x, y) {
  this.x = x;
  this.y = y;
}
Point.prototype.label = "from prototype";

console.log("[1] 단계를 하나씩 관찰한다");
probe("(1) this is a brand new object", () => {
  let seen;
  function C() { seen = [Object.keys(this).length, this === globalThis]; }
  new C();
  return seen;
});
probe("(2) its prototype is C.prototype", () => Object.getPrototypeOf(new Point(1, 2)) === Point.prototype);
probe("(2) so it inherits", () => new Point(1, 2).label);
probe("(3) the body runs with it as this", () => new Point(1, 2));
probe("(4) it comes back with no return stmt", () => typeof new Point(1, 2));

console.log("");
console.log("[2] 4단계의 예외 -- 객체를 돌려주면 그것이 이긴다");
probe("return an object", () => { function C() { this.x = 1; return { x: "returned" }; } return new C(); });
probe("return a primitive", () => { function C() { this.x = 1; return 42; } return new C(); });
probe("return an array", () => { function C() { this.x = 1; return [9]; } return new C(); });
probe("return a function", () => { function C() { this.x = 1; return function f() {}; } return typeof new C(); });
probe("return null", () => { function C() { this.x = 1; return null; } return new C(); });

console.log("");
console.log("[3] new 없이 부르면 -- 조용히 전역을 더럽힌다");
probe("Point(1, 2) with no new (sloppy)", () => { const r = Point(1, 2); return [r, globalThis.x, globalThis.y]; });
probe("the same in strict mode", () => {
  function SP(x) { "use strict"; this.x = x; }
  return SP(1);
});

console.log("");
console.log("[4] new.target 이 그 둘을 가른다");
function Guarded(x) {
  if (new.target === undefined) return "called without new";
  this.x = x;
  return undefined;
}
probe("new Guarded(1)", () => new Guarded(1));
probe("Guarded(1)", () => Guarded(1));
probe("new.target is the function itself", () => {
  let seen;
  function C() { seen = new.target === C; }
  new C();
  return seen;
});

console.log("");
console.log("[5] new 를 못 받는 것들");
probe("new on an arrow", () => { const A = () => {}; return new A(); });
probe("new on a shorthand method", () => { const o = { m() {} }; return new o.m(); });
probe("new on a getter-made function", () => { const o = { get g() { return () => {}; } }; return new o.g(); });
probe("class called without new", () => { class K {} return K(); });
probe("new on a class", () => { class K { constructor() { this.k = 1; } } return new K(); });
probe("new on Math.max", () => new Math.max(1));
```

```text
===== node20 js06b-07f-new.js (exit=0) =====
[1] 단계를 하나씩 관찰한다
  (1) this is a brand new object           -> [0,false]
  (2) its prototype is C.prototype         -> true
  (2) so it inherits                       -> "from prototype"
  (3) the body runs with it as this        -> {"x":1,"y":2}
  (4) it comes back with no return stmt    -> "object"

[2] 4단계의 예외 -- 객체를 돌려주면 그것이 이긴다
  return an object                         -> {"x":"returned"}
  return a primitive                       -> {"x":1}
  return an array                          -> [9]
  return a function                        -> "function"
  return null                              -> {"x":1}

[3] new 없이 부르면 -- 조용히 전역을 더럽힌다
  Point(1, 2) with no new (sloppy)         -> [null,1,2]
  the same in strict mode                  -> TypeError: Cannot set properties of undefined (setting 'x')

[4] new.target 이 그 둘을 가른다
  new Guarded(1)                           -> {"x":1}
  Guarded(1)                               -> "called without new"
  new.target is the function itself        -> true

[5] new 를 못 받는 것들
  new on an arrow                          -> TypeError: A is not a constructor
  new on a shorthand method                -> TypeError: o.m is not a constructor
  new on a getter-made function            -> TypeError: o.g is not a constructor
  class called without new                 -> TypeError: Class constructor K cannot be invoked without 'new'
  new on a class                           -> {"k":1}
  new on Math.max                          -> TypeError: Math.max is not a constructor
```

그림 해설.

- ★★★ **`[1]` 이 네 단계를 하나씩 보인다.** `this` 는 **키가 0개인 새 객체**이고 `globalThis` 가 아니다(`[0,false]`).
  프로토타입이 `Point.prototype` 이라 **상속도 따라온다**(`"from prototype"`).
- ★★★ **`[2]` 가 4단계의 예외다.** **객체를 돌려주면 그것이 이기고**(`{"x":"returned"}`, `[9]`, 함수도),
  **원시값과 `null` 은 무시된다**(`{"x":1}`). ★ `null` 이 객체가 아닌 것이 여기서 드러난다.
- ★★★ **`[3]` 이 「`new` 를 빼먹으면」이다.** 비엄격에서는 **조용히 전역에 `x`·`y` 가 생긴다**(`[null,1,2]` —
  함수가 아무것도 안 돌려줘 첫 칸이 `null` 로 찍혔다). ★★ 엄격에서는 `TypeError` 다.
- ★★ **`[4]` 의 `new.target` 이 그 둘을 가른다.** `new` 로 불렸으면 **함수 자신**이고 아니면 `undefined` 다.
  ★ **`class` 는 이 검사를 언어가 해 준다** — `[5]` 의 `TypeError: Class constructor K cannot be invoked without 'new'`.
- ★ **`[5]` 가 「`new` 를 못 받는 것들」 목록**이다. 화살표·단축 메서드·게터가 만든 함수·내장 메서드가 전부 `is not a constructor` 다.
  **`function` 과 `class` 만 받는다.**

**비용** — `new` 는 **프로토타입 연결을 공짜로** 해 준다. 대신 **빼먹으면 비엄격에서 조용히 전역을 더럽힌다** —
`class` 를 쓰거나 `new.target` 으로 막는 것이 그 대가를 치우는 방법이다.

### (7) ★★ 콜백에 넘길 때 — 누가 부르느냐가 정한다

**언제 쓰나** — `forEach`·`setTimeout`·이벤트 핸들러에 메서드를 넘길 때.

```js
// js06b-07g-callbacks.js
// 콜백에 넘기는 순간 this 가 바뀐다 -- 누가 부르느냐가 정하기 때문이다.
function brand(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "") +
           (t.constructor && t.constructor.name ? " ctor=" + t.constructor.name : "");
  }
  return typeof t + " " + String(t);
}
function line(label, v) { console.log("  " + label.padEnd(38) + " -> " + v); }

console.log("[1] 배열 메서드는 두 번째 인자로 this 를 받는다");
[1].forEach(function () { line("forEach, no thisArg", brand(this)); });
[1].forEach(function () { line("forEach, thisArg given", brand(this)); }, { mark: "given" });
line("map, thisArg given", [1].map(function () { return brand(this); }, { mark: "given" })[0]);
line("filter, thisArg given", String([1].filter(function () { return brand(this) && true; }, { mark: "given" }).length));
line("some/every take one too", String([1].some(function () { return this.mark === "given"; }, { mark: "given" })));
line("reduce does NOT take one", String((function () {
  try { return [1, 2].reduce(function () { return brand(this); }, 0, { mark: "given" }); }
  catch (e) { return e.constructor.name; }
})()));
line("sort comparator saw", (function () { let seen; [2, 1].sort(function () { seen = brand(this); return 0; }); return seen; })());

console.log("");
console.log("[2] 화살표를 주면 thisArg 가 무시된다");
[1].forEach(() => line("forEach + arrow, thisArg given", brand(this)), { mark: "given" });

console.log("");
console.log("[3] 메서드를 그대로 넘기면 떨어진다 -- 그리고 고치는 법 셋");
const counter = {
  mark: "counter",
  n: 0,
  bump() { this.n += 1; return this.n; },
};
function report(label, run) {
  let r;
  try { r = JSON.stringify(run()); } catch (e) { r = e.constructor.name + ": " + e.message; }
  line(label, r);
}
report("[1,2].forEach(counter.bump)", () => { const c = { mark: "c", n: 0, bump: counter.bump }; [1, 2].forEach(c.bump); return c.n; });
report("thisArg", () => { const c = { mark: "c", n: 0, bump: counter.bump }; [1, 2].forEach(c.bump, c); return c.n; });
report("bind", () => { const c = { mark: "c", n: 0, bump: counter.bump }; [1, 2].forEach(c.bump.bind(c)); return c.n; });
report("arrow wrapper", () => { const c = { mark: "c", n: 0, bump: counter.bump }; [1, 2].forEach(() => c.bump()); return c.n; });

console.log("");
console.log("[4] 타이머는 호스트가 정한다 -- 그래서 여기 값은 Node 의 것이다");
const t  = { mark: "t", m() { line("setTimeout(t.m) this", brand(this)); } };
const tb = { mark: "tb", m() { line("setTimeout(t.m.bind(t)) this", brand(this)); } };
setTimeout(function () {
  line("setTimeout(function(){}) this", brand(this));
  setTimeout(t.m, 0);
  setTimeout(tb.m.bind(tb), 0);
  setTimeout(() => line("setTimeout(arrow inside cb) this", brand(this)), 0);
}, 0);
```

```text
===== node20 js06b-07g-callbacks.js (exit=0) =====
[1] 배열 메서드는 두 번째 인자로 this 를 받는다
  forEach, no thisArg                    -> globalThis
  forEach, thisArg given                 -> [object Object] mark=given ctor=Object
  map, thisArg given                     -> [object Object] mark=given ctor=Object
  filter, thisArg given                  -> 1
  some/every take one too                -> true
  reduce does NOT take one               -> globalThis
  sort comparator saw                    -> globalThis

[2] 화살표를 주면 thisArg 가 무시된다
  forEach + arrow, thisArg given         -> [object Object] ctor=Object

[3] 메서드를 그대로 넘기면 떨어진다 -- 그리고 고치는 법 셋
  [1,2].forEach(counter.bump)            -> 0
  thisArg                                -> 2
  bind                                   -> 2
  arrow wrapper                          -> 2

[4] 타이머는 호스트가 정한다 -- 그래서 여기 값은 Node 의 것이다
  setTimeout(function(){}) this          -> [object Object] ctor=Timeout
  setTimeout(t.m) this                   -> [object Object] ctor=Timeout
  setTimeout(t.m.bind(t)) this           -> [object Object] mark=tb ctor=Object
  setTimeout(arrow inside cb) this       -> [object Object] ctor=Timeout
```

그림 해설.

- ★★ **`[1]` 이 배열 메서드의 `thisArg` 다.** `forEach`·`map`·`filter`·`some`·`every` 는 **두 번째 인자**로 `this` 를 받는다.
  ★★ **`reduce` 는 안 받는다** — 그 자리가 초기값이라 세 번째 인자를 줘도 버려진다(`globalThis`).
  ★ **`sort` 의 비교 함수도 안 받는다.**
- ★★ **`[2]` 가 「화살표를 주면 `thisArg` 가 무시된다」를 보인다.** 줄 것이 없는 게 아니라 **받을 칸이 없다**(4번 절).
- ★★★ **`[3]` 이 조용한 실패다.** `[1,2].forEach(c.bump)` 뒤에 `c.n` 이 **여전히 `0`** 이다 —
  `this` 가 `globalThis` 라 **거기에 `n` 이 생겼기** 때문이다. **에러가 한 줄도 안 났다.**
  ★ 고침 셋(`thisArg`·`bind`·화살표 래퍼)은 전부 `2` 를 만든다.
- ★★★ **`[4]` 는 ECMA-262 밖이다.** Node 의 `setTimeout` 콜백은 `this` 가 **`Timeout` 객체**다.
  ★★ **브라우저에서는 `window`** 다(8번 절). **같은 줄이 두 호스트에서 갈린다** — 언어가 정하는 칸이 아니라는 증거다.
  ★ `bind` 로 못질하면 **양쪽에서 같아진다.**

**비용** — `thisArg` 는 공짜지만 **메서드가 그것을 받는지 일일이 외워야** 한다.
`bind` 나 화살표 래퍼는 어느 자리에서나 같게 도는 대신 함수를 하나 더 만든다.

### (8) ★★ 같은 질문을 브라우저에 던지면 — 호스트가 정하는 칸

**언제 쓰나** — 「이게 언어 규칙인가 Node 사정인가」를 가를 때.

호스트 페이지는 네 줄이고 **실제 검사는 옆의 `.js` 가 한다.**

```text
<!doctype html><meta charset="utf-8"><title>this in a browser</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js06b-07h-browser.js"></script>
```

```js
// js06b-07h-browser.js
// 같은 질문을 브라우저에 던진다 -- 호스트가 정하는 칸이 어디인지 가리려는 것이다.
function brand(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis (window)";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}
function loose() { return brand(this); }
function tight() { "use strict"; return brand(this); }

const user = { name: "kim", greet() { return "hi " + this.name; } };
const detached = user.greet;
const arrowMethod = { name: "kim", greet: () => "hi " + String(this && this.name) };

const rows = [
  ["top-level this in a classic script", brand(this)],
  ["sloppy f()", loose()],
  ["strict f()", tight()],
  ["sloppy f.call(7)", loose.call(7)],
  ["strict f.call(7)", tight.call(7)],
  ["user.greet()", user.greet()],
  ["detached greet() -- the silent one", detached()],
  ["window.name is", JSON.stringify(window.name)],
  ["arrow used as a method", arrowMethod.greet()],
  ["brand of globalThis", Object.prototype.toString.call(globalThis)],
  ["top-level arrow: arguments?", (() => { try { return String(arguments.length); } catch (e) { return e.constructor.name + ": " + e.message; } })()],
  ["forEach with no thisArg (sloppy)", (() => { let r; [1].forEach(function () { r = brand(this); }); return r; })()],
];

setTimeout(function () {
  rows.push(["setTimeout(fn) this", brand(this)]);
  rows.push(["addEventListener this", "see below"]);
  const btn = document.createElement("button");
  btn.id = "b1";
  btn.addEventListener("click", function () {
    rows[rows.length - 1] = ["addEventListener this", brand(this) + " id=" + this.id];
    document.getElementById("out").textContent =
      rows.map(([k, v]) => k.padEnd(38) + " : " + v).join("\n");
  });
  document.body.appendChild(btn);
  btn.click();
}, 0);
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --virtual-time-budget=1000 --dump-dom js06b-07h-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">top-level this in a classic script     : globalThis (window)
sloppy f()                             : globalThis (window)
strict f()                             : undefined
sloppy f.call(7)                       : [object Number]
strict f.call(7)                       : number 7
user.greet()                           : hi kim
detached greet() -- the silent one     : hi 
window.name is                         : ""
arrow used as a method                 : hi 
brand of globalThis                    : [object Window]
top-level arrow: arguments?            : ReferenceError: arguments is not defined
forEach with no thisArg (sloppy)       : globalThis (window)
setTimeout(fn) this                    : globalThis (window)
addEventListener this                  : [object HTMLButtonElement] id=b1</pre>
```

그림 해설.

- ★★★ **호스트가 정하는 칸이 넷이다.**
  ① **최상위 `this`** — 브라우저 classic script 는 `window`, Node CommonJS 는 `module.exports` ·
  ② **`globalThis` 의 브랜드** — `[object Window]` 대 `[object global]` ·
  ③ **`setTimeout` 콜백의 `this`** — `window` 대 `Timeout` ·
  ④ **`globalThis.name`** — `""` 대 `undefined`.
- ★★★ **④가 「조용함의 모양」을 바꾼다.** 떼어 낸 `greet()` 이 브라우저에서는 **`"hi "`(빈 이름)** 이고 Node 에서는 `"hi undefined"` 다.
  ★★ **같은 버그인데 브라우저 쪽이 더 조용하다** — 사람 눈에는 그냥 이름이 안 나온 것처럼 보인다.
- ★★ **화살표 메서드도 같은 이유로 `"hi "`** 다. Node 에서는 `"hi undefined"` 였다.
- ★★ **언어가 정하는 칸은 그대로다** — 엄격 `f()` 가 `undefined`, `call(7)` 이 비엄격에서 `[object Number]`·엄격에서 `number 7`,
  `forEach` 콜백이 `globalThis`. **두 호스트에서 한 글자도 같다.**
- ★ **`addEventListener` 의 `this` 는 그 요소**다(`[object HTMLButtonElement] id=b1`) — 이것도 언어가 아니라 DOM 이 정한 것이다.
- ★ **최상위 화살표의 `arguments` 가 브라우저에서는 `ReferenceError`** 다. Node 의 `.js` 에는 **모듈 래퍼가 있기** 때문이다(05번·08번).

**비용** — 호스트가 정하는 칸이 있다는 것은 **「JS 규칙」으로 외운 것이 절반만 참일 수 있다**는 뜻이다.
그래서 이 주제는 **같은 줄을 두 호스트에 던져** 어느 칸이 언어인지 가렸다.

### (9) 두 판에서 돌려 보면 — 갈리는 자리가 없다

**언제 쓰나** — 「이게 이 판에서만 그런 건 아닐까」를 물을 때.

```sh
// js06b-vdiff.sh
#!/usr/bin/env bash
# 이 배치의 스크립트를 두 판으로 돌려 한 글자라도 다른지 본다.
# 쓰는 법: ./js06b-vdiff.sh <주제번호>
set -u -o pipefail
N18=node                                          # v18.19.1 (기본 PATH)
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"  # v20.19.6 (nvm)
printf '%-30s %s\n' "script" "node v18.19.1 vs v20.19.6"
printf '%-30s %s\n' "------------------------------" "-------------------------"
for f in js06b-"$1"*.js; do
  case "$f" in *-browser.js) continue;; esac      # 브라우저용은 뺀다
  flags=""
  case "$f" in *-retain.js) flags="--expose-gc";; esac
  a=$("$N18" $flags "$f" 2>&1); b=$("$N20" $flags "$f" 2>&1)
  if [ "$a" = "$b" ]; then printf '%-30s same (byte for byte)\n' "$f"
  else printf '%-30s DIFF -- lines %s\n' "$f" "$(diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | grep -c '^[<>]')"
  fi
done
```

```text
===== ./js06b-vdiff.sh 07 (exit=0) =====
script                         node v18.19.1 vs v20.19.6
------------------------------ -------------------------
js06b-07a-four-rules.js        same (byte for byte)
js06b-07b-mode-matrix.js       same (byte for byte)
js06b-07c-detached.js          same (byte for byte)
js06b-07d-arrow.js             same (byte for byte)
js06b-07e-bind.js              same (byte for byte)
js06b-07f-new.js               same (byte for byte)
js06b-07g-callbacks.js         same (byte for byte)
js06b-07x-forms.js             same (byte for byte)
```

그림 해설.

- **여덟 스크립트 전부 한 글자도 같았다.** `this` 규칙은 **판이 올라도 안 움직이는 층**이다.
- ★★ **그런데 「같았다」는 보장이 아니다.** 보장은 명세에서 오고 이것은 관찰이다.
- ★ **브라우저 블록은 이 대조에서 뺐다** — Chrome 151 한 벌로만 돌렸다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js06b-07x-forms.js
// 형태만 모아 둔 파일 -- 출력은 없다. `node --check` 로 문법만 확인한다.
function who() { return this; }
const target = { mark: "target", who };

who();                       // 기본   -- 비엄격이면 globalThis, 엄격이면 undefined
target.who();                // 암시적 -- 점 왼쪽의 객체
who.call(target);            // 명시적 -- 첫 인자
who.apply(target, []);       // 명시적 -- 인자를 배열로
const bound = who.bind(target);  // 명시적 -- 새 함수를 만들어 못질한다
new who();                   // new    -- 새 객체를 만들어 this 로 준다

const arrow = () => this;    // ★ 화살표는 this 를 안 만든다. 바깥 것을 그대로 쓴다
const bad = { mark: "bad", who: () => this };      // ★ 메서드로 쓰면 깨진다
const good = { mark: "good", who() { return this; } };  // 단축 메서드가 맞는 도구다

[1].forEach(function () { return this; }, target);  // 배열 메서드는 thisArg 를 받는다
[1].forEach(() => this, target);                    // ★ 화살표면 thisArg 가 무시된다

function Guarded(x) {
  if (new.target === undefined) throw new TypeError("call me with new");
  this.x = x;
}

class K {                    // class 는 new 없이 못 부른다
  constructor() { this.k = 1; }
  method() { return this; }               // 떼면 잃는다
  field = () => this;                     // ★ 필드 화살표는 인스턴스마다 못질된다
}
```

```text
===== node20 --check js06b-07x-forms.js (exit=0) =====

```

> ★ **이 빈 블록이 근거다.** 「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 구분이 안 된다.**
> 명령과 `(exit=0)` 까지 담긴 **빈 출력**이라야 「던졌고 조용했다」가 된다.

규칙은 여덟이다.

1. **`this` 는 호출식이 정한다.** 함수를 정의한 자리는 상관없다 — **06번의 이름 규칙과 정반대**다.
2. **판정 순서는 `new` → `bind`/`call`/`apply` → 점 왼쪽 → 기본**이다.
3. **기본 바인딩은 모드가 가른다** — 비엄격 `globalThis`, 엄격 `undefined`.
4. **점 왼쪽이 있어도 그 자리에서 바로 부르지 않으면** 암시적 바인딩이 안 붙는다.
5. **`bind` 는 한 겹 더 감싸는 것**이라 두 번 해도 안쪽이 이긴다. **`new` 만 그것을 이긴다.**
6. **화살표는 자기 `this` 를 안 만든다** — 바깥 것을 쓰고 `call`·`apply`·`bind`·`thisArg` 로 못 바꾼다.
7. **화살표는 메서드·생성자 자리에 쓰지 않는다.** 클래스 **필드** 화살표는 반대로 그 자리가 쓸모다.
8. **타이머·이벤트의 `this` 는 호스트가 정한다** — ECMA-262 밖이다.

## 어디서 틀리나

### (1) ★★★ `this` 를 이름처럼 찾는다

**06번의 규칙을 그대로 가져오면 전부 틀린다.** 이름은 **정의된 자리**가 정하고 `this` 는 **호출식**이 정한다.
★ 예외는 화살표 하나뿐이고, **그래서 화살표가 헷갈리는 것**이다.

### (2) ★★★ 메서드를 변수에 담으면 그대로일 거라고 믿는다

```text
   const g = user.greet;   // g === user.greet 가 true 다
   g()                     // 그런데 this 가 다르다
```

**함수는 같고 호출식이 다르다.** 넘기기·담기·구조 분해가 전부 같은 사고다.

### (3) ★★★ 「엄격이든 아니든 비슷하겠지」로 넘어간다

**열네 칸 중 아홉이 갈린다**(2번 절). 특히 **떼어 낸 메서드가 한쪽에서는 조용하고 한쪽에서는 `TypeError`** 다.
★ **모듈과 `class` 몸통은 언제나 엄격**이므로, 같은 코드를 `.mjs` 나 클래스 안으로 옮기면 답이 바뀐다.

### (4) ★★ 화살표를 메서드로 쓴다

```text
   const o = { name: "kim", greet: () => "hi " + this.name };   // ★ 깨진다
   const o = { name: "kim", greet()   { return "hi " + this.name } };  // 이쪽
```

화살표는 **그 객체가 아니라 그 리터럴을 쓴 자리의 `this`** 를 본다.
★ **클래스 필드 화살표는 정반대로 유용하다** — 인스턴스에 못질되어 떼어 내도 안 깨진다.

### (5) ★★ `bind` 를 다시 걸면 바뀔 거라고 믿는다

**안 바뀐다.** 덮어쓰기가 아니라 **한 겹 더 감싸기**다. 되돌릴 수 있는 것은 **`new` 하나**다.

### (6) ★★ `new` 를 빼먹고도 돌아간 것을 「괜찮다」로 읽는다

비엄격에서는 **조용히 전역을 더럽히고** 함수는 `undefined` 를 돌려준다.
★ `class` 를 쓰거나 `new.target` 으로 막아야 시끄러워진다.

### (7) ★ 모든 배열 메서드가 `thisArg` 를 받는다고 믿는다

**`reduce` 와 `sort` 는 안 받는다.** 그리고 **화살표를 주면 받는 메서드에서도 무시된다.**

### (8) ★ 타이머의 `this` 를 언어 규칙으로 외운다

**호스트가 정한다.** Node 는 `Timeout` 객체, 브라우저는 `window` 다. **같은 줄이 두 곳에서 갈린다.**

## 구현 세부사항 대 언어 보장

네 층으로 가른다. ★★ **이 주제는 「호스트가 정하는 것」 칸이 두껍다** — 「최상위」와 「타이머」를 ECMA-262 가 정하지 않기 때문이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **명세(ECMA-262) 보장** | 어느 엔진에서도 같아야 하는 것 | 위 기준 소스를 열어서 + 실행으로 재확인 |
| **호스트(Node·브라우저)가 정하는 것** | 「최상위」가 무엇이냐 · 타이머·이벤트의 `this` | 같은 코드를 Node 와 Chrome 두 곳에 던져 대조 |
| **엔진(V8) 구현** | V8 이 그렇게 하는 것 — 특히 **예외 문구** | 실행 + 두 판 대조 |
| **이 판의 관찰** | node 20.19.6 / 18.19.1 / Chrome 151 에서 그랬을 뿐 | 「관찰」로 명기 |

### 명세 보장

| 사실 | 어떻게 확인했나 |
|---|---|
| **`this` 는 호출식이 정한다** | 같은 함수 객체를 아홉 가지로 불러 아홉 답을 받았다 |
| **판정 순서 `new` → 명시적 → 암시적 → 기본** | `[2]` 의 세 줄 |
| **비엄격 기본은 `globalThis`, 엄격은 `undefined`** | 두 번 컴파일한 격자 |
| **비엄격은 원시 `this` 를 객체로 감싸고 엄격은 안 감싼다** | `call(7)` 의 두 답 |
| **참조가 풀리면 암시적 바인딩이 사라진다** | `(0, o.m)()` · `(o.m = o.m)()` · `(true && o.m)()` |
| **`bind` 는 되돌릴 수 없다** | 두 번 `bind`·`call`·점 재부착이 전부 안쪽을 따랐다 |
| **`new` 는 `bind` 를 이기고 프로토타입은 원본을 쓴다** | `instanceof C` 가 `true` |
| **`new` 는 객체 반환만 존중하고 원시값·`null` 은 무시한다** | 다섯 줄 격자 |
| **화살표는 자기 `this` 를 안 만들고 못 바꾼다** | `call`·`apply`·`bind`·`thisArg` 네 시도가 전부 실패 |
| **화살표·단축 메서드·게터 함수는 생성자가 아니다** | `is not a constructor` |
| **`forEach`·`map`·`filter`·`some`·`every` 는 `thisArg` 를 받고 `reduce`·`sort` 는 안 받는다** | 일곱 줄 |
| **클래스 필드 화살표는 인스턴스에 못질된다** | 떼어 내도 같은 답 |

### 호스트가 정하는 것 — ECMA-262 밖

| 사실 | 어디서 갈렸나 |
|---|---|
| 최상위 `this` — 브라우저는 `window`, Node CJS 는 `module.exports` | 같은 줄을 두 곳에 던져 |
| `globalThis` 의 브랜드 — `[object Window]` 대 `[object global]` | 〃 |
| `setTimeout` 콜백의 `this` — `window` 대 `Timeout` | 〃 |
| `globalThis.name` — `""` 대 `undefined` | 〃. ★ 이것이 **조용함의 모양**을 바꾼다 |
| `addEventListener` 의 `this` 가 그 요소인 것 | DOM 이 정한다 |
| 최상위 화살표의 `arguments` — Node 는 래퍼가 있고 브라우저는 없다 | 〃 |

### 엔진(V8) 구현 · 이 판의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `Cannot read properties of undefined (reading 'name')` 같은 **문구** | 예외의 **종류**는 명세지만 문구는 아니다 |
| `A is not a constructor` 에 **어떤 이름이 박히나** | 소스의 이름을 그대로 쓴다 — V8 의 사정이다 |
| Node 20.19.6 의 V8 은 **11.3.244.8**, 18.19.1 은 **10.2.154.26** | `process.versions.v8` |
| 이 주제의 여덟 스크립트가 **두 판에서 한 글자도 같았다** | `js06b-vdiff.sh 07` |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`this` 는 그 함수가 정의된 객체다」
  ○ **호출식이 정한다.** 정의된 자리는 상관없다.
- ✗ 「화살표 함수는 `this` 가 없다」
  ○ **자기 것을 안 만들 뿐** 바깥 것을 쓴다. 그래서 모드가 바뀌면 화살표의 답도 같이 바뀐다.
- ✗ 「`bind` 를 다시 하면 덮어쓴다」
  ○ **한 겹 더 감싼다.** 되돌리는 것은 `new` 뿐이다.
- ✗ 「`new` 를 빼먹으면 에러가 난다」
  ○ **비엄격에서는 조용히 전역을 더럽힌다.** 에러는 엄격이거나 `class` 일 때만 난다.
- ✗ 「`setTimeout` 콜백의 `this` 는 전역이다」
  ○ **호스트가 정한다.** Node 는 `Timeout` 객체다.
- ✗ 「배열 메서드는 다 `thisArg` 를 받는다」
  ○ **`reduce`·`sort` 는 안 받고**, 화살표를 주면 받는 메서드에서도 무시된다.

**판정 기준 한 줄**: 어떤 호출을 보면 「**이 괄호 바로 왼쪽에 무엇이 붙어 있나**」를 묻는다. 함수 본문을 보지 않는다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| 단축 메서드 `m() {}` | 객체·클래스의 메서드. `this` 를 받아야 하는 자리 |
| 화살표 | **콜백**. 바깥 `this` 를 그대로 이어야 할 때 |
| 클래스 **필드** 화살표 | 메서드를 **떼어 내 넘길** 때(이벤트 핸들러) |
| `bind` | 넘기기 전에 못질할 때. **한 번만 먹는다**는 것을 알고 쓴다 |
| `thisArg` | `forEach`·`map`·`filter`·`some`·`every` 한정 |
| `new.target` | `new` 없이 부른 것을 막을 때. `class` 면 언어가 대신 해 준다 |

**안 쓰는 자리**는 넷이다.
**화살표를 메서드로 쓰지 마라** — 그 객체를 안 본다.
**화살표를 생성자·프로토타입 자리에 쓰지 마라** — `new` 를 못 받는다.
**`bind` 로 재바인딩을 기대하지 마라** — 안쪽이 이긴다.
**`this` 를 쓰는 함수를 점 없이 넘기지 마라** — 비엄격에서 조용히 틀린다.

## 핵심 문장

- **`this` 는 함수에 붙어 있지 않다.** 호출식이 정한다 — 06번의 이름 규칙과 정반대다.
- **순서는 `new` → `bind`/`call`/`apply` → 점 왼쪽 → 기본**이다.
- ★★★ **열네 칸 중 아홉이 엄격 모드에서 갈린다** — 「이 코드가 엄격인가」를 먼저 물어야 답이 선다.
- ★★ **메서드를 떼면 함수는 같고 호출식만 바뀐다** — 그리고 비엄격에서는 **에러 없이 값만 틀린다.**
- ★★ **화살표는 자기 `this` 를 안 만든다** — 그래서 콜백에는 맞고 메서드에는 안 맞는다.
- ★ **`bind` 는 한 겹 더 감싸는 것**이고 그것을 이기는 것은 `new` 하나다.
- ★ **타이머·이벤트의 `this` 는 언어가 아니라 호스트가 정한다.**

## 관련 자료

- 목록: [js/syntax 주제 목록](../README.md) — 이 주제는 **07번**
- 선행: [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md) —
  ★★★ **그쪽은 「이름은 정의된 자리가 정한다」까지, 여기는 「`this` 는 그렇지 않다」부터다.**
  화살표의 `this` 만 그쪽 규칙을 따른다.
- 선행: [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md) —
  최상위 `this` 가 호스트마다 다른 것과 `window.name` 이 `""` 인 것의 첫 실측이 거기 있다.
- 이어지는 곳: [목록의 **08번 주제**](../08-function-forms-and-parameters/) 「함수 정의 형태와 매개변수」 — 화살표에 **`arguments` 도 없다**는 것, 그리고 형태별 차이 표의 정본.
- 이어지는 곳: [목록의 **09번 주제**](../09-call-apply-bind/) 「`call`·`apply`·`bind`」 — **세 메서드의 API 세부**가 거기다. 여기는 「`this` 를 정한다」까지다.
- 이어지는 곳: [목록의 **16번 주제**](../16-class-syntax/) 「`class` 문법」 — 클래스 필드 화살표가 어디에 붙나.
- 이어지는 곳: 목록의 **35번 주제** 「엄격 모드」 — 2번 절이 센 아홉 칸의 **정본**. 모듈이 언제나 엄격인 것도 그쪽이다.
- 이어지는 곳: 목록의 **36번 주제** 「이벤트 루프와 마이크로태스크」 — 7번 절의 타이머가 **언제** 도는가.
- 경계 — 다른 언어의 같은 자리: [`python/syntax/21-scope-legb-global-nonlocal`](../../../python/syntax/21-scope-legb-global-nonlocal/2-summary.md) —
  파이썬은 **`self` 를 매개변수로 명시**한다. 그래서 「떼어 내면 잃는다」가 성립하지 않고, 대신 **바운드 메서드**라는 객체가 따로 생긴다.
  **그쪽은 「이름이 어느 스코프에서 풀리나」까지, 여기는 「숨은 인자 하나가 어떻게 정해지나」부터다.**
- 경계 — 연혁은 여기가 아니다: [`history/js/02-ES6-모던.md`](../../../../../../history/js/02-ES6-모던.md) — 화살표 함수가 **언제 왜** 들어왔나.
- 경계 — 타입 이야기: TypeScript 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **16번**.
  **그쪽은 `this` 매개변수 타입 표기, 여기는 런타임 값이다.**

## 용어 풀이

- **기본 바인딩(default binding)**: 아무 규칙도 안 걸렸을 때. 비엄격은 `globalThis`, 엄격은 `undefined`.
- **암시적 바인딩(implicit binding)**: `o.m()` 처럼 점 왼쪽이 있을 때. **그 자리에서 바로 불러야** 붙는다.
- **명시적 바인딩(explicit binding)**: `call`·`apply`·`bind` 로 직접 줄 때.
- **`new` 바인딩**: `new f()` 로 불러 갓 만든 객체가 들어갈 때.
- **떼어 낸 메서드(detached method)**: 객체에서 꺼내 변수·인자·배열에 담은 함수. **점이 사라져 기본 바인딩**이 된다.
- **바인딩된 함수(bound function)**: `bind` 가 만든 새 함수. 이름에 `bound ` 접두가 붙고 `prototype` 이 없다.
- **`thisArg`**: `forEach` 류가 받는 두 번째 인자. 콜백의 `this` 가 된다. **화살표에는 안 먹는다.**
- **`new.target`**: `new` 로 불렸는지 보는 값. `new` 면 그 함수, 아니면 `undefined`.
- **엄격 모드(strict mode)**: `"use strict";` 로 켜는 깐깐한 규칙 집합. **모듈과 `class` 몸통은 언제나 엄격**이다.
- **브랜드 태그(brand tag)**: `Object.prototype.toString.call(x)` 가 내놓는 `[object …]` 문자열. 정본은 목록의 **34번 주제**다.

## 더 들어가면

- **`class` 몸통이 언제나 엄격**이라 클래스 메서드를 떼어 내면 `undefined` 다(4번 절 `[5]`).
  같은 코드를 객체 리터럴에 쓰면 비엄격이라 `globalThis` 다 — **옮겨 적기만 해도 답이 바뀐다.** 정본은 16번·35번이다.
- **모듈(ESM)의 최상위 `this` 는 또 다르다**(`undefined`). 이 배치는 CommonJS 와 브라우저 classic script 두 자리만 던졌다 — **ESM 은 42번 주제**다.
- **`Reflect.apply`·`Function.prototype.call.bind` 같은 관용구**는 같은 규칙 위에 얹혀 있다 — 46번 주제.
- **안 돌려 본 것** — ESM(`.mjs`) 최상위 · Web Worker · 다른 엔진(SpiderMonkey·JavaScriptCore) ·
  Node 18 보다 낮은 판 · `with` 문 · 프록시로 가로챈 호출(45번) · `super` 호출 안의 `this`(17번).
- ★ **못 잰 것** — **`bind` 와 화살표 래퍼의 비용.** 함수 객체가 하나 더 생긴다는 것은 관찰했지만
  **얼마나 드는지는 재지 않았다** — 이 노트는 벤치마크를 돌리지 않으므로 「느리다」·「빠르다」를 한 줄도 쓰지 않았다.
