# js/syntax/20 — 제너레이터: 「`next(값)` 은 대답을 넣고 다음 질문을 받는 무전이다 — 첫 무전은 아무도 안 듣는다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기 — 그중에서도 「양방향 흐름」의 로그다.**
> 제너레이터는 **값이 두 방향으로 흐른다** — `yield` 가 바깥으로 값을 내보내고, `next(값)` 이 안으로 값을 들여보낸다.
> 그런데 결과 객체 `{ value, done }` 에는 **바깥으로 나간 쪽만** 찍힌다. 안으로 들어간 값이 **어디에 닿았나(또는 안 닿았나)** 는 결과에 한 글자도 안 남는다.
> 그래서 제너레이터 본문 안에 「**`yield` 식이 무엇으로 평가됐나**」를 찍는 로그를 심고, 바깥에서 준 값과 **한 줄에 나란히** 찍었다.
> **이 문서의 결론은 전부 그 나란한 두 줄에서 나온다.**
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안 — Control Abstraction Objects](https://tc39.es/ecma262/multipage/control-abstraction-objects.html) —
>   Generator Objects · `GeneratorStart` · `GeneratorValidate` · `GeneratorResumeAbrupt` · `%GeneratorPrototype%` 의 `next`/`return`/`throw`
> - [ECMA-262 최신 초안 — ECMAScript Language: Functions and Classes](https://tc39.es/ecma262/multipage/ecmascript-language-functions-and-classes.html) —
>   Generator Function Definitions · `yield` · `yield*` 의 평가 규칙
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계를 가릴 때
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서의 **추상 연산 이름과 짧은 영문 인용**으로, **값·호출 로그·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `이름 「메시지」` 꼴로만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★ **이 주제의 블록에는 주소도 시간도 난수도 없다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.
>
> **버전** — 이 주제의 거의 전부가 **한 판에 들어왔다.**
>
> | 무엇 | 판 |
> |---|---|
> | `function*` · `yield` · `yield*` · `next`/`return`/`throw` | **ES2015** |
> | 객체·클래스의 제너레이터 메서드(`*m() {}`) | **ES2015** |
> | 이터레이터 헬퍼(제너레이터 객체에도 붙는 `map`·`take` 등) | **ES2025** — ★ 두 node 판에는 **없다**(아래 판별 블록). [목록의 **21번 주제**](../21-iterator-helpers/)가 정본 |
> | `async function*` · `for await...of` | **ES2018** — 이 주제 밖([목록의 **40번 주제**](../40-async-iteration-and-for-await/)) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | 본문 안에 「`yield` 식이 무엇으로 평가됐나」를 찍고, 바깥의 `next(값)` 과 **한 줄에 나란히** 찍는다. 첫 `next(값)` 이 **어디에도 안 닿는 것**은 오직 이것으로만 보인다 |
> | ★★★ **② 전수 격자** | **세 메서드(`next`·`return`·`throw`) × 세 상태(시작 전 · `yield` 에서 멈춤 · 끝남)** 아홉 칸. 칸마다 결과와 본문 로그를 찍고, **본문 코드가 돈 칸 수**를 스크립트가 센다 |
> | ★★ **③ 브랜드 태그** | `%GeneratorPrototype%.next` 를 평범한 객체에 빌려 부르면 **`incompatible receiver`** 로 막힌다 — 제너레이터인지는 **내부 슬롯**이 가른다. ★ `Object.prototype.toString` 이 `[object Generator]` 라고 답하는 것은 **프로퍼티(`Symbol.toStringTag`) 하나**라 브랜드가 아니다([목록의 **22번 주제**](../22-symbol-and-well-known-symbols/)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `new gen()` · 화살표 제너레이터 · 콜백 안의 `yield` · 실행 중 재진입 · 배열을 `yield*` 하던 중의 `throw()` |
> | ★★ **⑤ 두 판 대조기** | 두 판이 갈린 줄은 **`SyntaxError` 문구 한 줄**뿐이다(동작 (7)) |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | 이 주제의 `SyntaxError` 는 **값으로 가를 수 없는 문법 성질**을 증명하려는 것이 아니라 「안 된다」를 보이려는 것이다. `new Function` 으로 던져 **문구만** 받았다 — 열을 읽을 질문이 없다 |
> | ★ **안 쟀다 — 성능·메모리** | 「제너레이터는 메모리를 아낀다」·「느리다」를 **한 줄도 쓰지 않는다.** 잰 것은 **몇 개를 만들었나(호출 횟수)** 뿐이다(동작 (8)) |
> | ★ **안 돌렸다 — 파이썬 · 브라우저** | 파이썬 `send()` 대비는 **파이썬 17번 문서가 이미 실은 출력**을 인용했다(동작 (9)). 이 주제는 Chrome 을 판별 블록 말고는 돌리지 않았다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구** — ★ **이 주제에서 실제로 판마다 갈렸다**(`Unexpected identifier` 뒤의 `'x'`) | ★★★ **로그의 개수와 순서** · 결과 객체의 `value`/`done` |
> | Node 스택트레이스의 절대 경로 — 한 줄도 싣지 않았다 | ★★★ **예외의 종류**(`TypeError`·`SyntaxError`) |
> | | ★★ 격자의 **「본문 코드가 돈 칸」 수** |
>
> 두 판 대조기가 **갈렸다고 세는 이 주제의 탐침은 `js20b-20f-errors.js` 하나**다 — 집계 줄은 동작 (7)의 끝에 있다.
>
> **선행** — [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ 직접 선행) ·
> [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md)(제너레이터의 `prototype` 과 `new`) ·
> [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md).
> ★★★ **19번이 이미 잰 것은 다시 재지 않는다** — 소비자 17가지가 `return()` 을 부르는 자리(**8곳**), `next()` 가 던지면 닫기 0,
> 제너레이터 객체가 **이터러블이자 이터레이터**(`g[Symbol.iterator]() === g`)라 두 번째 스프레드가 `[]` 인 것.
> 여기는 그 「닫기」가 **제너레이터 안쪽에서 무엇을 일으키나**부터 본다.
> **이어지는 곳** — [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md) · [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) · [목록의 **40번 주제**](../40-async-iteration-and-for-await/) 「비동기 이터레이션」
>
> ★★ **경계 — 소비자 쪽 `return()` 호출표는 19번이 정본이다.** 여기서는 그 호출이 제너레이터의 `finally` 에서 **무엇을 돌리나**만 본다.
> ★★ **경계 — 지연 파이프라인(`map`·`filter`·`take` 를 이어 붙이는 것)은 21번이 정본이다.** 여기서는 **손으로 짠 `take`/`map` 제너레이터**로 「당긴 만큼만 만든다」까지다.
> ★ **경계 — `async function*` 은 40번이 정본이다.**

```sh
# js20b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 그리고 판별 기능 표(js20b-features.js)를 세 판에 던진다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'console.log("node " + process.versions.node + "  v8 " + process.versions.v8)'
  "$n" js20b-features.js
done
google-chrome --version | sed 's/ *$//'
google-chrome --headless --dump-dom "file://$PWD/js20b-page.html?js20b-features.js" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d'
```
```js
// js20b-features.js
// 이 문서의 기능이 이 판에 있나 -- 판마다 같은 스크립트를 던진다(node 두 판 · Chrome).
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no (" + e.constructor.name + ")"; }
  console.log("  " + label.padEnd(44) + r);
};
const compiles = (src) => () => { new Function(src); return true; };
has("ES2015  function* / yield*", compiles("function* g() { yield* [1]; }"));
has("ES2015  Symbol.toPrimitive", () => typeof Symbol.toPrimitive === "symbol");
has("ES2015  Map / Set / WeakMap / WeakSet", () => [Map, Set, WeakMap, WeakSet].every((f) => typeof f === "function"));
has("ES2021  WeakRef / FinalizationRegistry", () => typeof WeakRef === "function" && typeof FinalizationRegistry === "function");
has("ES2023  symbols as WeakMap keys", () => { new WeakMap().set(Symbol("k"), 1); return true; });
has("ES2025  Iterator (global)", () => typeof Iterator === "function");
has("ES2025  Iterator.prototype.map / take", () => typeof [].values().map === "function" && typeof [].values().take === "function");
has("ES2025  Iterator.from", () => typeof Iterator.from === "function");
has("ES2025  Set.prototype.union / isSubsetOf", () => typeof new Set().union === "function" && typeof new Set().isSubsetOf === "function");
has("ES2026  Map.prototype.getOrInsert", () => typeof new Map().getOrInsert === "function");
has("ES2026  Map.prototype.getOrInsertComputed", () => typeof new Map().getOrInsertComputed === "function");
has("ES2026  WeakMap.prototype.getOrInsert", () => typeof new WeakMap().getOrInsert === "function");
```
```text
===== ./js20b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  function* / yield*                  yes
  ES2015  Symbol.toPrimitive                  yes
  ES2015  Map / Set / WeakMap / WeakSet       yes
  ES2021  WeakRef / FinalizationRegistry      yes
  ES2023  symbols as WeakMap keys             no (TypeError)
  ES2025  Iterator (global)                   no
  ES2025  Iterator.prototype.map / take       no
  ES2025  Iterator.from                       no (ReferenceError)
  ES2025  Set.prototype.union / isSubsetOf    no
  ES2026  Map.prototype.getOrInsert           no
  ES2026  Map.prototype.getOrInsertComputed   no
  ES2026  WeakMap.prototype.getOrInsert       no
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  function* / yield*                  yes
  ES2015  Symbol.toPrimitive                  yes
  ES2015  Map / Set / WeakMap / WeakSet       yes
  ES2021  WeakRef / FinalizationRegistry      yes
  ES2023  symbols as WeakMap keys             yes
  ES2025  Iterator (global)                   no
  ES2025  Iterator.prototype.map / take       no
  ES2025  Iterator.from                       no (ReferenceError)
  ES2025  Set.prototype.union / isSubsetOf    no
  ES2026  Map.prototype.getOrInsert           no
  ES2026  Map.prototype.getOrInsertComputed   no
  ES2026  WeakMap.prototype.getOrInsert       no
Google Chrome 151.0.7922.173
  ES2015  function* / yield*                  yes
  ES2015  Symbol.toPrimitive                  yes
  ES2015  Map / Set / WeakMap / WeakSet       yes
  ES2021  WeakRef / FinalizationRegistry      yes
  ES2023  symbols as WeakMap keys             yes
  ES2025  Iterator (global)                   yes
  ES2025  Iterator.prototype.map / take       yes
  ES2025  Iterator.from                       yes
  ES2025  Set.prototype.union / isSubsetOf    yes
  ES2026  Map.prototype.getOrInsert           yes
  ES2026  Map.prototype.getOrInsertComputed   yes
  ES2026  WeakMap.prototype.getOrInsert       yes
```

- ★★ **제너레이터 한 줄은 세 판이 전부 `yes`** 다. 이 주제의 본문은 **node20 한 판**으로 돌리고, node18 과 갈린 곳만 따로 싣는다.
- ★ 두 node 판에 **이터레이터 헬퍼가 없다**는 줄이 이 주제에 걸리는 유일한 판 사정이다 — 그래서 동작 (8)의 `take`/`map` 을 **손으로 짰다.**

## 한눈에 — 쉽게 말하면

**제너레이터는 「무전기 너머의 이야기꾼」** 이다. 바깥(나)이 무전기 버튼을 누를 때마다(`next`) 이야기꾼이 **한 토막**을 말하고(`yield`) **입을 다문 채 기다린다.**
버튼을 누를 때 **내가 한마디 얹을 수도 있다**(`next(값)`) — 그 말은 이야기꾼이 **방금 멈춘 자리**에 도착한다.

- ★★★ **처음 버튼을 누를 때 이야기꾼은 아직 무전기를 안 들었다.** 그때 내가 얹은 말은 **아무도 못 듣는다** — 에러도 없이 사라진다.
- ★★★ **내가 얹은 말은 「이번에 나오는 토막」이 아니라 「지난번 멈춘 자리」에 닿는다.** 그래서 질문과 대답이 **한 박자씩 어긋나** 보인다.
- ★★ **「그만!」(`return`)을 외치면 이야기꾼은 뒷정리(`finally`)를 하고 끊는다.** 단, 뒷정리 중에 **한 토막 더 말하면** 거기서 또 멈춘다.
- ★★ **「돌 던지기」(`throw`)는 멈춘 그 자리에 떨어진다.** 이야기꾼이 받아 내면(`try`/`catch`) 이야기가 계속된다.

```text
   바깥 (나)                                  제너레이터 본문 (이야기꾼)
   ---------                                  --------------------------
   g = echo()          ──▶  (아무 일도 없다 — 본문 로그 0)

   g.next("A")         ──▶  본문 시작 ... yield "out-1" 에서 멈춤
                       ◀──  { value: "out-1" }
                             "A" 는 받을 yield 가 아직 없다  -> 사라진다

   g.next("B")         ──▶  멈췄던 yield#1 이 "B" 로 평가됨 ... yield "out-2" 에서 멈춤
                       ◀──  { value: "out-2" }

   g.next("C")         ──▶  멈췄던 yield#2 가 "C" 로 평가됨 ... return
                       ◀──  { value: "done with [B,C]", done: true }   <- return 값은 여기 한 번

   g.next("D")         ──▶  (끝난 뒤 — 본문 로그 0)
                       ◀──  { value: undefined, done: true }
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 이야기꾼을 부른다 | `gen()` 호출 — 본문은 안 돌고 **제너레이터 객체**만 생긴다 | 호출 직후 본문 로그 `[]` |
| 버튼을 누른다 | `g.next()` | 결과 객체 `{ value, done }` |
| 버튼을 누르며 한마디 얹는다 | `g.next(값)` — 그 값이 **멈춰 있던 `yield` 식의 값**이 된다 | 본문의 `yield#N evaluated to …` 로그 |
| 한 토막 말하고 기다린다 | `yield 값` | 결과의 `value` |
| 이야기가 끝났다 | `return 값` → `{ value: 값, done: true }` **한 번** | 그 다음부터는 `{ value: undefined, done: true }` |
| 「그만!」 | `g.return(값)` — 멈춘 자리에서 `return` 이 일어난 것처럼 | `finally` 로그 |
| 돌 던지기 | `g.throw(err)` — 멈춘 자리에서 `throw err` 가 일어난 것처럼 | 본문의 `catch` 로그 |
| 다른 이야기꾼에게 마이크를 넘긴다 | `yield* inner` — 버튼·말·「그만」·돌이 **전부 안쪽으로 간다** | 안쪽의 로그 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**제너레이터에 설정값을 `next(config)` 로 넘겼는데 무시됐다**」와
「**`for...of` 로 돌렸더니 `return` 한 값이 결과에 없다**」가 그것이다.
앞엣것은 **첫 무전을 아무도 안 들은 것**이고, 뒤엣것은 **소비자가 `done: true` 의 값을 안 읽는 것**(19번)이다.

> **제너레이터 함수(generator function)** — `function*` 로 선언한 함수. 부르면 본문을 돌리지 않고 **제너레이터 객체**를 돌려준다.\
> 예: `function* g() { yield 1; }` — `g()` 는 본문을 한 줄도 안 돌린다.

> **제너레이터 객체(generator object)** — 멈춘 자리를 기억하는 이터레이터. `next`·`return`·`throw` 세 메서드를 가진다.\
> 예: `const it = g(); it.next()` 가 `{ value: 1, done: false }`.

> **`yield` 식(yield expression)** — 값을 바깥으로 내보내고 멈추는 식. **식이므로 자기도 값을 가진다** — 재개할 때 `next` 에 준 인자가 그 값이다.\
> 예: `const a = yield "out";` 에서 `a` 는 **다음** `next(값)` 의 `값`.

## 이 주제가 답하려는 질문

1. **`next(값)` 의 값은 어느 `yield` 에 닿나** — 그리고 **첫 `next(값)` 의 값은 어디로 가나?**
2. **`return()`·`throw()` 는 멈춘 자리에서 무엇을 일으키나** — `finally` 는 도나, 본문이 받아 낼 수 있나, **상태(시작 전·멈춤·끝남)에 따라 무엇이 달라지나?**
3. **`yield*` 는 무엇을 안쪽으로 넘기고, 식의 값으로 무엇을 받아 오나?**

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★ 불러도 본문은 안 돈다 — 그리고 `return` 값은 한 번만 나온다

**언제 쓰나** — 「제너레이터를 부르면 **언제** 부수 효과가 일어나나」를 판단할 때.

```js
// js20b-20a-start-and-end.js
// 제너레이터를 부른 순간과 끝난 뒤 -- 본문 로그가 언제 찍히나, 결과 객체가 어떻게 바뀌나.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
function* gen() {
  L.push("body: start");
  yield "y1";
  L.push("body: after y1");
  yield "y2";
  L.push("body: after y2");
  return "R";
}

console.log("[1] calling gen()");
const g = gen();
console.log("  body log right after gen()      " + J(L));
console.log("  typeof g.next                   " + typeof g.next);
console.log("  Object.prototype.toString(g)    " + Object.prototype.toString.call(g));

console.log("");
console.log("[2] next() five times -- result object, then body log so far");
for (let i = 1; i <= 5; i++) {
  const r = g.next();
  console.log("  next#" + i + "  " + J(r).padEnd(34) + " log " + J(L));
  L.length = 0;
}

console.log("");
console.log("[3] consumers on the same kind of generator");
console.log("  [...gen()]                      " + J([...gen()]));
const seen = [];
for (const x of gen()) seen.push(x);
console.log("  for (const x of gen())          " + J(seen));
const [a, b, c] = gen();
console.log("  const [a, b, c] = gen()         " + J([a, b, c]));
console.log("  Array.from(gen())               " + J(Array.from(gen())));

console.log("");
console.log("[4] parameters at the call -- a default with a side effect, a destructuring parameter");
L.length = 0;
function* withDefault(x = (L.push("default evaluated"), 1)) { L.push("body: x is " + x); yield x; }
const w = withDefault();
console.log("  log right after withDefault()   " + J(L));
function* destructure({ a }) { yield a; }
try { destructure(); console.log("  destructure()                   returned a generator"); }
catch (e) { console.log("  destructure()                   " + e.constructor.name + " 「" + e.message + "」"); }
```
```text
===== node20 js20b-20a-start-and-end.js (exit=0) =====
[1] calling gen()
  body log right after gen()      []
  typeof g.next                   function
  Object.prototype.toString(g)    [object Generator]

[2] next() five times -- result object, then body log so far
  next#1  {"value":"y1","done":false}        log ["body: start"]
  next#2  {"value":"y2","done":false}        log ["body: after y1"]
  next#3  {"value":"R","done":true}          log ["body: after y2"]
  next#4  {"value":"<undefined>","done":true} log []
  next#5  {"value":"<undefined>","done":true} log []

[3] consumers on the same kind of generator
  [...gen()]                      ["y1","y2"]
  for (const x of gen())          ["y1","y2"]
  const [a, b, c] = gen()         ["y1","y2","<undefined>"]
  Array.from(gen())               ["y1","y2"]

[4] parameters at the call -- a default with a side effect, a destructuring parameter
  log right after withDefault()   ["default evaluated"]
  destructure()                   TypeError 「Cannot destructure property 'a' of 'undefined' as it is undefined.」
```

- ★★★ **`[1]` `gen()` 직후 본문 로그가 `[]` 이다.** 호출은 **객체만 만든다.** 본문의 첫 줄(`body: start`)은 **첫 `next()` 에서야** 찍힌다(`[2]` 의 `next#1`).
- ★★ **`[2]` 로그가 `next` 한 번에 한 토막씩 붙는다** — `next#1` 에 `body: start`, `next#2` 에 `body: after y1`.
  **본문은 `yield` 와 `yield` 사이의 코드만 한 번에 돌리고 멈춘다.**
- ★★★ **`return "R"` 은 `next#3` 에서 `{"value":"R","done":true}` 로 딱 한 번 나오고, `next#4`·`next#5` 는 `{"value":"<undefined>","done":true}`** 다.
  **끝난 제너레이터는 계속 불러도 에러가 아니라 같은 빈 결과**를 준다 — 본문 로그도 `[]` 다.
- ★★★ **`[3]` 소비자 넷 — `[...gen()]` · `for...of` · `Array.from` 은 `["y1","y2"]`, `R` 이 없다.**
  19번이 `withReturn()` 으로 이미 본 자리다(「`done: true` 의 값은 소비자 창이 전부 버린다」). ★ 여기서는 **구조 분해 `[a, b, c]` 도** 셋째 칸이 `"<undefined>"` 다 — `R` 이 아니다.
  **`return` 값을 받는 유일한 소비자는 `yield*`** 다(동작 (5)).
- ★★ **`[4]` 그런데 매개변수는 호출에서 평가된다.** 기본값의 부수 효과(`default evaluated`)가 `withDefault()` **직후** 로그에 있고,
  구조 분해 매개변수 `{ a }` 에 `undefined` 를 주면 **`destructure()` 호출 자체**가 `TypeError 「Cannot destructure property 'a' of 'undefined' as it is undefined.」` 로 막힌다.
  ★★★ **「제너레이터를 부르면 아무 일도 안 일어난다」는 반만 맞다 — 본문은 안 돌지만 매개변수 목록은 돈다.**
  ★ 명세의 `EvaluateGeneratorBody` 가 그 순서를 적는다 — "Perform ? FunctionDeclarationInstantiation(funcObj, argList)." 로 **매개변수를 먼저 묶고**,
  그 다음에 제너레이터 객체를 만들어 "Perform GeneratorStart(gen, FunctionBody)." 로 **본문을 매달아 두기만** 한다.

### (2) ★★★ 양방향 흐름 — `next(값)` 은 「지난번 멈춘 자리」에 닿는다 · 이 주제의 본체

**언제 쓰나** — 제너레이터에 **바깥에서 값을 밀어 넣는**(코루틴처럼 쓰는) 코드를 읽거나 쓸 때.

```js
// js20b-20b-two-way.js
// next(값) 의 값은 어디로 가나 -- 본문이 받은 값과 바깥이 받은 값을 한 줄씩 찍는다.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
function* echo() {
  L.push("body starts (arguments.length " + arguments.length + ")");
  const a = yield "out-1";
  L.push("yield#1 evaluated to " + J(a));
  const b = yield "out-2";
  L.push("yield#2 evaluated to " + J(b));
  return "done with " + J([a, b]);
}

console.log("[1] next('A'), next('B'), next('C'), next('D')");
const g = echo();
for (const arg of ["A", "B", "C", "D"]) {
  const r = g.next(arg);
  console.log("  next(" + J(arg) + ")  ->  " + J(r).padEnd(40) + " body: " + (L.length ? L.join(" / ") : "(no log)"));
  L.length = 0;
}

console.log("");
console.log("[2] a running total -- priming next() first, then values");
function* total() {
  let sum = 0;
  while (true) {
    const x = yield sum;
    sum += x;
  }
}
const t = total();
const steps = [["next()", () => t.next()], ["next(10)", () => t.next(10)], ["next(5)", () => t.next(5)], ["next(1)", () => t.next(1)]];
for (const [label, run] of steps) console.log("  " + label.padEnd(10) + J(run()));

console.log("");
console.log("[3] the same, without priming -- next(10) first");
const t2 = total();
for (const x of [10, 5, 1]) console.log("  " + ("next(" + x + ")").padEnd(10) + J(t2.next(x)));
```
```text
===== node20 js20b-20b-two-way.js (exit=0) =====
[1] next('A'), next('B'), next('C'), next('D')
  next("A")  ->  {"value":"out-1","done":false}           body: body starts (arguments.length 0)
  next("B")  ->  {"value":"out-2","done":false}           body: yield#1 evaluated to "B"
  next("C")  ->  {"value":"done with [\"B\",\"C\"]","done":true} body: yield#2 evaluated to "C"
  next("D")  ->  {"value":"<undefined>","done":true}      body: (no log)

[2] a running total -- priming next() first, then values
  next()    {"value":0,"done":false}
  next(10)  {"value":10,"done":false}
  next(5)   {"value":15,"done":false}
  next(1)   {"value":16,"done":false}

[3] the same, without priming -- next(10) first
  next(10)  {"value":0,"done":false}
  next(5)   {"value":5,"done":false}
  next(1)   {"value":6,"done":false}
```

```text
   next 호출        바깥이 받은 것 (value)     본문 안에서 일어난 일
   ---------        ----------------------     ---------------------
   next("A")   ->   "out-1"                    본문 시작 · arguments.length 0
                                               "A" 가 닿을 yield 가 없다   ◀── 사라진다
   next("B")   ->   "out-2"                    yield#1 이 "B" 로 평가됨
   next("C")   ->   return 값 (done: true)     yield#2 가 "C" 로 평가됨
   next("D")   ->   undefined (done: true)     (본문 없음)

   ★ 바깥이 받는 값과 안으로 들어간 값이 한 박자 어긋난다:
     next(k번째 인자)  ──▶  (k-1)번째 yield 식의 값
     next(1번째 인자)  ──▶  0번째 yield 는 없다
```

- ★★★ **`[1]` 첫 줄 — `next("A")` 가 `out-1` 을 받는 동안 본문 로그는 `body starts (arguments.length 0)` 뿐이다.**
  `"A"` 는 **어느 로그에도 없다.** 에러도 경고도 없이 사라졌다.
  ★ `arguments.length 0` 은 **「첫 `next` 의 인자가 제너레이터 함수의 인자로 들어오지도 않는다」** 는 증거다 — 제너레이터 함수는 `echo()` 로 **인자 없이** 불렸다.
- ★★★ **`next("B")` 에서야 `yield#1 evaluated to "B"`** — **`B` 는 `out-2` 를 요청한 호출의 인자인데 `out-1` 을 내보낸 `yield` 의 값이 됐다.**
  이것이 「한 박자 어긋남」이다. **`yield` 식의 값은 그 `yield` 를 재개시킨 다음 `next` 의 인자다.**
- ★★ **`next("C")` 가 `return` 을 부르며 `done: true` 를 받고, 그 `value` 는 `["B","C"]` 를 담은 문자열이다** — **`A` 가 끝까지 없다.**
- ★★ **`next("D")` 는 끝난 뒤라 본문이 없다** — `(no log)`. `D` 도 사라진다(동작 (1)의 `next#4` 와 같다).
- ★★★ **`[2]` 누산기 — 먼저 `next()` 를 한 번 부르고(프라이밍) 나서 `next(10)`·`next(5)`·`next(1)`** 이 `10`·`15`·`16` 이다. 값이 **전부** 들어갔다.
- ★★★ **`[3]` 프라이밍 없이 `next(10)` 부터** — `0`·`5`·`6` 이다. **첫 `10` 이 사라졌다.** 합계에서 10 이 통째로 빠진 것이 그 증거다.
  ★★ **같은 제너레이터, 같은 값 목록인데 결과가 다르다** — 차이는 **첫 호출에 값을 실었느냐** 하나다.
- ★★★ **왜 사라지나** — 첫 `next` 가 재개하는 것은 **「본문의 시작」** 이지 어떤 `yield` 가 아니다.
  `GeneratorStart` 가 그 자리를 이렇게 적는다 — "Set the code evaluation state of genContext such that when evaluation is resumed for that execution context, closure will be called with no arguments."
  **본문은 인자 없이 시작된다.** 첫 `next` 에 준 값이 들어갈 칸이 명세에 없다.

### (3) ★★★ `return()` 과 `finally` — 상태에 따라 다르고, `finally` 가 `yield` 하면 거기서 또 멈춘다

**언제 쓰나** — 제너레이터 안에 **정리 코드**(파일 닫기·구독 해제)를 `try`/`finally` 로 둘 때. 19번의 소비자 8곳이 부르는 `return()` 이 **여기로 온다.**

```js
// js20b-20c-return-finally.js
// gen.return(v) -- 어느 상태에서 부르느냐에 따라 finally 가 도나, 무엇을 돌려받나.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
const log = (label, r) => { console.log("  " + label.padEnd(36) + J(r).padEnd(34) + " body: " + (L.length ? L.join(" / ") : "(no log)")); L.length = 0; };

function* withFinally() {
  try {
    L.push("try");
    yield 1;
    yield 2;
  } finally {
    L.push("finally");
  }
}

console.log("[1] return('R') in three states");
let g = withFinally();
log("before the first next: return('R')", g.return("R"));
log("  then next()", g.next());
g = withFinally(); g.next(); L.length = 0;
log("paused at yield 1: return('R')", g.return("R"));
log("  then next()", g.next());
g = withFinally(); [...g]; L.length = 0;
log("after completion: return('R')", g.return("R"));

console.log("");
console.log("[2] a finally block that itself yields");
function* yieldsInFinally() {
  try {
    yield 1;
  } finally {
    L.push("finally starts");
    yield "from finally";
    L.push("finally ends");
  }
}
g = yieldsInFinally(); g.next(); L.length = 0;
log("return('R')", g.return("R"));
log("next()", g.next());
log("next()", g.next());

console.log("");
console.log("[3] a finally block with its own return");
function* returnsInFinally() {
  try { yield 1; } finally { L.push("finally returns 'F'"); return "F"; }
}
g = returnsInFinally(); g.next(); L.length = 0;
log("return('R')", g.return("R"));

console.log("");
console.log("[4] break in for-of over withFinally()");
for (const x of withFinally()) { L.push("loop got " + x); break; }
log("after the loop", "-");
```
```text
===== node20 js20b-20c-return-finally.js (exit=0) =====
[1] return('R') in three states
  before the first next: return('R')  {"value":"R","done":true}          body: (no log)
    then next()                       {"value":"<undefined>","done":true} body: (no log)
  paused at yield 1: return('R')      {"value":"R","done":true}          body: finally
    then next()                       {"value":"<undefined>","done":true} body: (no log)
  after completion: return('R')       {"value":"R","done":true}          body: (no log)

[2] a finally block that itself yields
  return('R')                         {"value":"from finally","done":false} body: finally starts
  next()                              {"value":"R","done":true}          body: finally ends
  next()                              {"value":"<undefined>","done":true} body: (no log)

[3] a finally block with its own return
  return('R')                         {"value":"F","done":true}          body: finally returns 'F'

[4] break in for-of over withFinally()
  after the loop                      "-"                                body: try / loop got 1 / finally
```

```text
   g.return("R") 을 부른 때           본문에서 일어나는 일              돌려받는 것
   ------------------------           --------------------              -----------
   시작 전 (next 를 한 번도 안 부름)   아무것도 안 돈다 · try 에 들어간 적이 없다    { R, done: true }
   yield 1 에서 멈춤 (try 안)          그 자리에서 return "R" 이 일어난 것처럼
                                       -> finally 가 돈다                          { R, done: true }
   끝난 뒤                             아무것도 안 돈다                             { R, done: true }

   ★ finally 가 yield 를 하면
      g.return("R")   -> finally 시작 ... yield "from finally" 에서 멈춘다        { "from finally", done: false }
      g.next()        -> finally 끝 ... 미뤄 둔 return "R" 이 마저 일어난다       { R, done: true }
   ★ finally 가 return "F" 를 하면
      g.return("R")   -> "F" 가 "R" 을 덮는다                                     { F, done: true }
```

- ★★★ **`[1]` 세 상태에서 돌려받는 것은 전부 `{"value":"R","done":true}`** 로 **똑같다.** 갈리는 것은 **본문 로그**다.
  **시작 전과 끝난 뒤는 `(no log)`**, **`yield 1` 에서 멈춘 것만 `finally`** 다.
  ★★ 시작 전에 `return()` 을 부르면 **`try` 에 들어간 적이 없으니 `finally` 도 없다** — 명세의 `GeneratorResumeAbrupt` 가
  "If state is suspended-start, then Set gen.[[GeneratorState]] to completed." 로 **본문을 안 돌리고 끝난 것으로 표시**한다.
  그리고 끝난 것에는 "If abruptCompletion is a return completion, then Return CreateIteratorResultObject(abruptCompletion.[[Value]], true)." — **준 값을 그대로 돌려준다.**
- ★★ **`return()` 뒤의 `next()` 는 전부 `{"value":"<undefined>","done":true}`** — 한 번 닫히면 끝난 상태에서 안 나온다.
- ★★★ **`[2]` `finally` 안의 `yield` — `return("R")` 이 `{"value":"from finally","done":false}` 를 돌려준다.**
  **「그만」을 외쳤는데 `done: false`** 다. 제너레이터는 **`finally` 안의 `yield` 에서 다시 멈췄고**, `R` 은 **미뤄져 있다.**
  다음 `next()` 가 `finally ends` 를 찍고 **그제야 `{"value":"R","done":true}`** 를 준다.
  ★★★ **그러니 `return()` 은 「반드시 닫는다」가 아니다 — 「멈춘 자리에서 `return` 을 일으킨다」** 이고, 그 `return` 이 `finally` 를 지나는 동안 무엇을 할지는 **본문이 정한다.**
  ★ 19번의 `for...of` + `break` 가 부르는 것도 이 `return()` 이다 — 그 소비자는 **돌려받은 결과를 안 본다**(19번의 「`return()` 의 결과가 객체이기만 하면 된다」). 즉 `finally` 가 `yield` 하면 **`for...of` 는 그 값을 버리고 떠나고, 제너레이터는 `finally` 중간에 멈춘 채 남는다.** ★ 이 주제는 그 조합을 **로그로 돌리지 않았다** — 두 출력(19번의 호출표 · 여기의 `[2]`)을 이어 읽은 것이다.
- ★★ **`[3]` `finally` 안의 `return "F"` 가 `R` 을 덮는다** — `{"value":"F","done":true}`. 평범한 함수의 `try`/`finally` 와 같은 규칙이다.
- ★★ **`[4]` `for...of` 에서 `break` 하면 로그가 `try / loop got 1 / finally`** — 19번의 「`break` 가 `return()` 을 부른다」가 **제너레이터에서는 `finally` 로 보인다.**

### (4) ★★ `throw()` — 멈춘 `yield` 자리에서 던져지고, 받아 내면 계속 돈다

**언제 쓰나** — 바깥에서 제너레이터에 **취소·오류를 알릴** 때.

```js
// js20b-20d-throw.js
// gen.throw(e) -- 예외가 어디서 생기나, 본문이 잡으면 무엇을 돌려받나.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
const E = (e) => e.constructor.name + " 「" + e.message + "」";
const attempt = (label, run) => {
  let r;
  try { r = J(run()); } catch (e) { r = "caught outside: " + E(e); }
  console.log("  " + label.padEnd(30) + r.padEnd(44) + " body: " + (L.length ? L.join(" / ") : "(no log)"));
  L.length = 0;
};

function* catchesAround() {
  let n = 0;
  while (true) {
    try {
      L.push("yield " + n);
      yield n++;
    } catch (e) {
      L.push("caught inside: " + E(e));
    }
  }
}
console.log("[1] a body that catches around its yield");
let g = catchesAround();
attempt("next()", () => g.next());
attempt("throw(new Error('X'))", () => g.throw(new Error("X")));
attempt("next()", () => g.next());

console.log("");
console.log("[2] a body with no catch");
function* noCatch() {
  try { yield 1; yield 2; } finally { L.push("finally"); }
}
g = noCatch();
attempt("next()", () => g.next());
attempt("throw(new Error('X'))", () => g.throw(new Error("X")));
attempt("next()", () => g.next());

console.log("");
console.log("[3] throw() before the first next()");
g = catchesAround();
attempt("throw(new Error('early'))", () => g.throw(new Error("early")));
attempt("next()", () => g.next());
```
```text
===== node20 js20b-20d-throw.js (exit=0) =====
[1] a body that catches around its yield
  next()                        {"value":0,"done":false}                     body: yield 0
  throw(new Error('X'))         {"value":1,"done":false}                     body: caught inside: Error 「X」 / yield 1
  next()                        {"value":2,"done":false}                     body: yield 2

[2] a body with no catch
  next()                        {"value":1,"done":false}                     body: (no log)
  throw(new Error('X'))         caught outside: Error 「X」                    body: finally
  next()                        {"value":"<undefined>","done":true}          body: (no log)

[3] throw() before the first next()
  throw(new Error('early'))     caught outside: Error 「early」                body: (no log)
  next()                        {"value":"<undefined>","done":true}          body: (no log)
```

```text
   g.throw(err)                      본문
   ------------                      ----
   yield n 에서 멈춰 있다  ──▶       그 yield 자리에서 throw err
                                     ├─ try/catch 가 감싸고 있다 -> catch 가 받는다 -> 다음 yield 까지 돈다
                                     │                              -> throw() 의 반환값 = 그 다음 yield 의 값
                                     └─ 아무도 안 받는다 -> finally 를 지나 바깥으로 -> throw() 호출이 던진다
                                                                                      -> 제너레이터는 끝남
   시작 전  ──▶  본문을 안 돌리고 바로 바깥으로 던진다 (finally 도 없다)
```

- ★★★ **`[1]` 본문이 `yield` 를 `try`/`catch` 로 감쌌다 — `throw(new Error('X'))` 가 **던지지 않고** `{"value":1,"done":false}` 를 돌려준다.**
  로그가 `caught inside: Error 「X」 / yield 1` — **예외가 `yield 0` 자리에 떨어졌고, `catch` 가 받았고, 루프가 돌아 `yield 1` 에서 다시 멈췄다.**
  ★★ **`throw()` 의 반환값은 「예외를 받은 뒤 다음으로 멈춘 `yield`」의 값**이다 — `next()` 와 모양이 같다.
- ★★ **`[2]` 받는 `catch` 가 없으면 — `throw()` 호출 자체가 `Error 「X」` 로 던지고, 가는 길에 `finally` 가 돈다.** 그 뒤 `next()` 는 `done: true` — 끝났다.
- ★★ **`[3]` 시작 전에 `throw()` — 바깥으로 곧장 `Error 「early」`, 본문 로그 0.** 루프 안의 `catch` 는 **아직 존재하지 않는** 것이다.
  `return()` 의 시작 전 칸과 같은 규칙(`GeneratorResumeAbrupt` 의 suspended-start)이다 — 본문을 안 돌리고 끝난 것으로 표시하고, **던질 것을 던진다.**

### (5) ★★★ `yield*` — 식의 값은 안쪽의 `return` 값이고, 버튼·말·「그만」·돌이 전부 안쪽으로 간다

**언제 쓰나** — 제너레이터를 **쪼개서 조립**할 때(재귀 트리 순회 · 파서의 하위 규칙).

```js
// js20b-20e-delegate.js
// yield* -- 식의 값은 무엇인가, next(값) · throw · return 이 안쪽까지 가나.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
const E = (e) => e.constructor.name + " 「" + e.message + "」";
const step = (label, run) => {
  let r;
  try { r = J(run()); } catch (e) { r = "caught outside: " + E(e); }
  console.log("  " + label.padEnd(24) + r.padEnd(36) + " log: " + (L.length ? L.join(" / ") : "(none)"));
  L.length = 0;
};

function* inner() {
  try {
    const a = yield "i1";
    L.push("inner got " + J(a));
    const b = yield "i2";
    L.push("inner got " + J(b));
    return "inner-R";
  } catch (e) {
    L.push("inner caught " + E(e));
    yield "i-after-catch";
    return "inner-R2";
  } finally {
    L.push("inner finally");
  }
}
function* outer() {
  const got = yield* inner();
  L.push("outer: yield* evaluated to " + J(got));
  yield "o1";
}

console.log("[1] next(value) through yield*");
let g = outer();
step("next('ignored')", () => g.next("ignored"));
step("next('A')", () => g.next("A"));
step("next('B')", () => g.next("B"));
step("next()", () => g.next());
console.log("  [...outer()]            " + J([...outer()]));
L.length = 0;

console.log("");
console.log("[2] throw() through yield*");
g = outer();
step("next()", () => g.next());
step("throw(new Error('X'))", () => g.throw(new Error("X")));
step("next()", () => g.next());

console.log("");
console.log("[3] return() through yield*");
g = outer();
step("next()", () => g.next());
step("return('R')", () => g.return("R"));

console.log("");
console.log("[4] yield* over an array iterator -- then throw()");
function* overArray() {
  try { yield* [1, 2, 3]; } finally { L.push("overArray finally"); }
}
g = overArray();
step("next()", () => g.next());
step("throw(new Error('X'))", () => g.throw(new Error("X")));
step("next()", () => g.next());

console.log("");
console.log("[5] a hand-written iterator under yield* -- which methods are called");
const handMade = {
  [Symbol.iterator]() {
    let i = 0;
    return {
      next(v) { L.push("hand next(" + J(v) + ")"); i++; return i <= 2 ? { value: "h" + i, done: false } : { value: "hand-R", done: true }; },
      return(v) { L.push("hand return(" + J(v) + ")"); return { value: v, done: true }; },
    };
  },
};
function* overHand() { const r = yield* handMade; L.push("overHand got " + J(r)); }
g = overHand();
step("next('a')", () => g.next("a"));
step("next('b')", () => g.next("b"));
step("next('c')", () => g.next("c"));
g = overHand();
step("next()", () => g.next());
step("return('R')", () => g.return("R"));
g = overHand();
step("next()", () => g.next());
step("throw(new Error('X'))", () => g.throw(new Error("X")));
```
```text
===== node20 js20b-20e-delegate.js (exit=0) =====
[1] next(value) through yield*
  next('ignored')         {"value":"i1","done":false}          log: (none)
  next('A')               {"value":"i2","done":false}          log: inner got "A"
  next('B')               {"value":"o1","done":false}          log: inner got "B" / inner finally / outer: yield* evaluated to "inner-R"
  next()                  {"value":"<undefined>","done":true}  log: (none)
  [...outer()]            ["i1","i2","o1"]

[2] throw() through yield*
  next()                  {"value":"i1","done":false}          log: (none)
  throw(new Error('X'))   {"value":"i-after-catch","done":false} log: inner caught Error 「X」
  next()                  {"value":"o1","done":false}          log: inner finally / outer: yield* evaluated to "inner-R2"

[3] return() through yield*
  next()                  {"value":"i1","done":false}          log: (none)
  return('R')             {"value":"R","done":true}            log: inner finally

[4] yield* over an array iterator -- then throw()
  next()                  {"value":1,"done":false}             log: (none)
  throw(new Error('X'))   caught outside: TypeError 「The iterator does not provide a 'throw' method.」 log: overArray finally
  next()                  {"value":"<undefined>","done":true}  log: (none)

[5] a hand-written iterator under yield* -- which methods are called
  next('a')               {"value":"h1","done":false}          log: hand next("<undefined>")
  next('b')               {"value":"h2","done":false}          log: hand next("b")
  next('c')               {"value":"<undefined>","done":true}  log: hand next("c") / overHand got "hand-R"
  next()                  {"value":"h1","done":false}          log: hand next("<undefined>")
  return('R')             {"value":"R","done":true}            log: hand return("R")
  next()                  {"value":"h1","done":false}          log: hand next("<undefined>")
  throw(new Error('X'))   caught outside: TypeError 「The iterator does not provide a 'throw' method.」 log: hand return("<undefined>")
```

```text
   바깥 g.next(v) / g.throw(e) / g.return(r)
          │
          ▼
   outer:  const got = yield* inner();      <- outer 는 중간에서 값을 받아 다시 yield 하지 않는다
          │                                    호출이 그대로 inner 에게 간다
          ▼
   inner:  next(v)   -> 멈춘 yield 의 값이 v
           throw(e)  -> 멈춘 yield 자리에서 throw e   (inner 가 catch 하면 계속)
           return(r) -> 멈춘 yield 자리에서 return r  (inner 의 finally 가 돈다)
          │
          ▼ inner 가 return "inner-R" 로 끝나면
   outer:  got === "inner-R"     <- ★ 바깥 결과에는 안 나오고 yield* 식의 값이 된다

   ★ 안쪽에 throw 메서드가 없으면 (배열 이터레이터 · 손으로 짠 이터레이터)
      g.throw(e) -> 안쪽을 return() 으로 닫고 -> TypeError 「The iterator does not provide a 'throw' method.」
```

- ★★★ **`[1]` `next('A')` 에서 `inner got "A"`, `next('B')` 에서 `inner got "B"`** — 바깥에 준 값이 **안쪽 `yield` 식의 값**이 됐다. `outer` 는 중간에서 아무것도 안 했다.
  ★★ 첫 `next('ignored')` 는 여기서도 **사라진다**(로그 `(none)`) — `outer` 도 첫 무전은 못 듣는다.
- ★★★ **`next('B')` 한 번에 `inner got "B" / inner finally / outer: yield* evaluated to "inner-R"`** — 안쪽이 `return "inner-R"` 로 끝나자
  **그 값이 `yield*` 식의 값(`got`)이 되고**, `outer` 가 이어서 `yield "o1"` 까지 갔다.
  ★★★ **`[...outer()]` 는 `["i1","i2","o1"]` — `inner-R` 이 없다.** 안쪽의 `return` 값은 **바깥 결과가 아니라 `yield*` 식으로만** 간다.
  동작 (1)의 「`return` 값을 받는 유일한 소비자」가 이것이다. 명세의 `yield*` 가 "If done is true, then Return ? IteratorValue(innerResult)." — **안쪽이 끝난 결과의 `value` 가 식의 값이다.**
- ★★★ **`[2]` `throw()` 가 안쪽 `catch` 에 닿는다** — `inner caught Error 「X」`, 안쪽이 `i-after-catch` 를 `yield` 해서 **바깥 `throw()` 가 그 값을 돌려받는다.**
  다음 `next()` 에서 안쪽이 `inner-R2` 로 끝나고 `outer` 가 그것을 `got` 으로 받았다.
- ★★ **`[3]` `return('R')` 이 안쪽 `finally` 를 돌린다** — `inner finally`. `outer` 의 `L.push("outer: …")` 는 **안 찍혔다** — `return` 이 `outer` 까지 올라와 `outer` 도 끝났다.
- ★★★ **`[4]` 배열을 `yield*` 하던 중 `throw()` — `TypeError 「The iterator does not provide a 'throw' method.」`**, 그리고 `overArray finally` 가 돌았다.
  **배열 이터레이터에는 `throw` 메서드가 없다.** 명세의 `yield*` 가 이 자리를 적는다 —
  "NOTE: If iterator does not have a throw method, this throw is going to terminate the yield* loop. But first we need to give iterator a chance to clean up."
  **안쪽을 닫고(`IteratorClose`) 나서 `TypeError`** 를 `yield*` 자리에서 던진다 — 내가 던진 `Error 「X」` 가 **아니라** `TypeError` 가 바깥으로 나온다.
- ★★★ **`[5]` 손으로 짠 이터레이터로 「무엇이 불리나」를 찍었다.**
  - **첫 `next('a')` 인데 안쪽은 `hand next("<undefined>")`** 이다 — `'a'` 는 `overHand` 의 시작에서 사라졌고, `yield*` 는 **안쪽의 첫 `next` 를 `undefined` 로** 부른다.
    명세 — "Let received be NormalCompletion(undefined)." 가 `yield*` 루프의 첫 줄이다.
  - **`next('b')` → `hand next("b")`** — 그 다음부터는 **받은 값을 그대로** 넘긴다.
  - **안쪽이 `done: true` 와 `hand-R` 을 주자 `overHand got "hand-R"`** — 손으로 짠 이터레이터의 `done: true` 값도 `yield*` 식이 받는다.
  - **`return('R')` → `hand return("R")`** — 바깥에 준 값까지 그대로 간다.
  - ★★ **`throw()` → `hand return("<undefined>")` 를 부르고 `TypeError`** — `[4]` 와 같은 규칙인데, 이번에는 **닫는 호출이 로그에 보인다.** `throw` 가 없는 안쪽을 **`return()` 으로 닫고 나서** 던진다.

### (6) ★★★ 세 메서드 × 세 상태 — 아홉 칸 격자

**언제 쓰나** — 「이 제너레이터에 지금 `return`/`throw` 를 부르면 **본문이 도나**」를 한 표로 판단할 때.

```js
// js20b-20g-grid.js
// 세 메서드 x 세 상태 -- 칸마다 결과와 본문 로그를 찍고, 본문 코드가 돈 칸을 센다.
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
const E = (e) => e.constructor.name + " 「" + e.message + "」";
let L = [];
function* subject() {
  try {
    L.push("try");
    yield "y";
    L.push("after yield");
  } catch (e) {
    L.push("catch");
  } finally {
    L.push("finally");
  }
}
const states = {
  "suspendedStart": () => subject(),
  "suspendedYield": () => { const g = subject(); g.next(); return g; },
  "completed": () => { const g = subject(); [...g]; return g; },
};
const calls = {
  "next('v')": (g) => g.next("v"),
  "return('R')": (g) => g.return("R"),
  "throw(err)": (g) => g.throw(new Error("err")),
};
let ran = 0, total = 0;
for (const [sname, make] of Object.entries(states)) {
  console.log(sname);
  for (const [cname, call] of Object.entries(calls)) {
    const g = make();
    L = [];
    let r;
    try { r = J(call(g)); } catch (e) { r = "throws " + E(e); }
    total++;
    if (L.length) ran++;
    console.log("  " + cname.padEnd(12) + r.padEnd(32) + " body log " + J(L));
  }
}
console.log("");
console.log("cells where body code ran: " + ran + " / " + total);
```
```text
===== node20 js20b-20g-grid.js (exit=0) =====
suspendedStart
  next('v')   {"value":"y","done":false}       body log ["try"]
  return('R') {"value":"R","done":true}        body log []
  throw(err)  throws Error 「err」               body log []
suspendedYield
  next('v')   {"value":"<undefined>","done":true} body log ["after yield","finally"]
  return('R') {"value":"R","done":true}        body log ["finally"]
  throw(err)  {"value":"<undefined>","done":true} body log ["catch","finally"]
completed
  next('v')   {"value":"<undefined>","done":true} body log []
  return('R') {"value":"R","done":true}        body log []
  throw(err)  throws Error 「err」               body log []

cells where body code ran: 4 / 9
```

```text
                     next('v')                    return('R')                  throw(err)
                     ---------                    -----------                  ----------
   시작 전           본문 시작 -> 첫 yield        본문 안 돎 · {R, done}       본문 안 돎 · 바깥으로 던짐
   yield 에서 멈춤   yield 가 'v' -> 계속         그 자리에서 return -> finally  그 자리에서 throw -> catch/finally
   끝남              본문 안 돎 · {undefined}     본문 안 돎 · {R, done}       본문 안 돎 · 바깥으로 던짐

   본문 코드가 도는 칸 = 「시작 전 × next」 하나 + 「yield 에서 멈춤」 줄 셋
```

- ★★★ **마지막 줄의 집계가 곧 결론이다 — 본문 코드가 돈 칸은 넷이다.** 「시작 전 × `next`」 하나와 「`yield` 에서 멈춤」 줄 셋.
  **나머지 다섯 칸은 본문이 한 줄도 안 돈다** — 시작 전과 끝난 뒤의 `return`/`throw` 는 **본문을 거치지 않고** 결과를 만든다.
- ★★ **`return` 칸 셋은 전부 `{"value":"R","done":true}`** — **결과만 보면 상태를 못 가른다.** 본문 로그(`["finally"]` 대 `[]`)로만 갈린다.
  ★ 이것이 이 주제에서 ① 로그 창이 본체인 이유다.
- ★★ **`throw` 칸은 시작 전·끝남이 둘 다 `throws Error 「err」`** — 이것도 결과로는 못 가른다.
  「`yield` 에서 멈춤 × `throw`」만 `catch` 가 받아 **`done: true`** 로 끝난다(`catch` 뒤에 `yield` 가 없어서다).
- ★ **「`yield` 에서 멈춤 × `next('v')`」의 로그에 `'v'` 가 없다** — `subject` 가 `yield` 의 값을 안 쓰기 때문이다. 동작 (2)의 규칙과 어긋나는 것이 아니다.

### (7) ★★ 막히는 자리 — `new` · 화살표 · 콜백 안의 `yield` · 재진입 · 브랜드

**언제 쓰나** — 제너레이터를 **생성자처럼**, **화살표로**, **콜백 안에서** 쓰려다 막혔을 때.

```js
// js20b-20f-errors.js
// 제너레이터에서 막히는 자리 -- 예외의 종류와 문구.
const J = (v) => JSON.stringify(v);
const E = (e) => e.constructor.name + " 「" + e.message + "」";
const row = (label, run) => {
  let r;
  try { r = String(run()); } catch (e) { r = E(e); }
  console.log("  " + label.padEnd(52) + r);
};

console.log("[1] new on a generator function");
function* gen() { yield 1; }
row("typeof gen.prototype", () => typeof gen.prototype);
row("Object.getPrototypeOf(gen()) === gen.prototype", () => Object.getPrototypeOf(gen()) === gen.prototype);
row("new gen()", () => new gen());

console.log("");
console.log("[2] five forms passed to new Function");
const compile = (src) => () => { new Function(src); return "compiles"; };
row("const g = *() => { yield 1; };", compile("const g = *() => { yield 1; };"));
row("const g = () => { yield 1; };", compile("const g = () => { yield 1; };"));
row("function* g() { [1].forEach(x => { yield x; }); }", compile("function* g() { [1].forEach(x => { yield x; }); }"));
row("const o = { *m() { yield 1; } };", compile("const o = { *m() { yield 1; } };"));
row("class C { static *m() { yield 1; } }", compile("class C { static *m() { yield 1; } }"));

console.log("");
console.log("[3] calling next() from inside the running body");
let self;
function* reenter() { yield self.next(); }
self = reenter();
row("self.next() inside the body", () => J(self.next()));
row("then self.next()", () => J(self.next()));

console.log("");
console.log("[4] next / return borrowed onto a plain object");
const proto = Object.getPrototypeOf(gen());
const GenProto = Object.getPrototypeOf(proto);
row("GenProto.next.call({})", () => GenProto.next.call({}));
row("GenProto.return.call({})", () => GenProto.return.call({}));
```
```text
===== node20 js20b-20f-errors.js (exit=0) =====
[1] new on a generator function
  typeof gen.prototype                                object
  Object.getPrototypeOf(gen()) === gen.prototype      true
  new gen()                                           TypeError 「gen is not a constructor」

[2] five forms passed to new Function
  const g = *() => { yield 1; };                      SyntaxError 「Unexpected token '*'」
  const g = () => { yield 1; };                       SyntaxError 「Unexpected number」
  function* g() { [1].forEach(x => { yield x; }); }   SyntaxError 「Unexpected identifier 'x'」
  const o = { *m() { yield 1; } };                    compiles
  class C { static *m() { yield 1; } }                compiles

[3] calling next() from inside the running body
  self.next() inside the body                         TypeError 「Generator is already running」
  then self.next()                                    {"done":true}

[4] next / return borrowed onto a plain object
  GenProto.next.call({})                              TypeError 「Method [Generator].prototype.next called on incompatible receiver #<Object>」
  GenProto.return.call({})                            TypeError 「Method [Generator].prototype.return called on incompatible receiver #<Object>」
```

- ★★★ **`[1]` `typeof gen.prototype` 이 `object` 이고 `gen()` 이 만든 객체의 프로토타입이 그것인데, `new gen()` 은 `TypeError 「gen is not a constructor」`** 다.
  08번의 격자가 이미 짚은 반례 — 「`prototype` 이 있으면 `new` 가 된다」가 **틀리다** — 를 이 주제에서 다시 확인했다.
  ★★ 제너레이터의 `prototype` 은 **「제너레이터 객체들의 프로토타입」** 이지 생성자의 인스턴스 프로토타입이 아니다.
- ★★★ **`[2]` 화살표 제너레이터는 문법이 없다** — `*() => …` 가 `SyntaxError 「Unexpected token '*'」`.
- ★★★ **`() => { yield 1; }` 은 `SyntaxError 「Unexpected number」`** — **`yield` 가 아니라 `1` 에서 막혔다.**
  비엄격 스크립트의 평범한 함수 안에서 **`yield` 는 키워드가 아니라 식별자**라서, `yield 1` 이 「식별자 뒤에 숫자」로 읽혔다.
- ★★ **제너레이터 안의 콜백 `x => { yield x; }` 도 막힌다** — `yield` 는 **그것을 직접 감싼 함수**가 제너레이터여야 한다. 콜백은 평범한 화살표다.
  ★ **이 줄이 두 판이 갈린 유일한 줄이다** — node18 은 `Unexpected identifier`, node20 은 `Unexpected identifier 'x'`(node18 판 블록은 [3-answer.md](3-answer.md) 의 같은 문항에 있다).
- ★ **객체·클래스의 `*m() {}` 는 된다** — 제너레이터 **메서드**의 문법이다.
- ★★★ **`[3]` 실행 중에 자기 `next()` 를 부르면 `TypeError 「Generator is already running」`.**
  명세의 `GeneratorValidate` — "If state is executing, throw a TypeError exception."
  ★ 그 예외가 **본문 안에서** 생겼는데 본문이 안 잡았으니 제너레이터가 끝났다 — 다음 `next()` 가 `{"done":true}` 다(`value` 가 `undefined` 라 `JSON.stringify` 가 칸째 뺐다).
- ★★ **`[4]` ③ 브랜드 — `next`·`return` 을 평범한 객체에 빌려 부르면 `incompatible receiver #<Object>`.**
  `%GeneratorPrototype%` 의 메서드는 받는 쪽이 **제너레이터의 내부 슬롯(`[[GeneratorState]]`)을 가졌나**를 본다(`GeneratorValidate`).
  ★ 동작 (1)의 `[object Generator]` 는 **`Symbol.toStringTag` 프로퍼티**가 낸 글자라 이것과 성격이 다르다 — 22번 주제가 그 바꿔치기를 다룬다.

두 판 대조기의 집계 줄 — 이 배치 네 주제의 node 탐침 전부를 센다(대조기 전문과 출력은 [3-answer.md](3-answer.md) 의 실행 검증에 있다).

`identical 18  ·  differs 6  ·  total 24`

### (8) ★★ 지연 시퀀스 — 끝없는 제너레이터에서 당긴 만큼만 만든다

**언제 쓰나** — 무한 수열·페이지 단위 조회처럼 **끝을 모르는 값**을 소비자가 필요한 만큼만 가져가게 할 때.

```js
// js20b-20h-lazy-seq.js
// 끝이 없는 제너레이터 -- 소비자가 몇 개를 당기나, 멈추면 finally 가 도나.
const L = [];
const J = (v) => JSON.stringify(v);
function* naturals() {
  let n = 1;
  try {
    while (true) { L.push("make " + n); yield n++; }
  } finally {
    L.push("finally");
  }
}
function* take(it, k) {
  if (k <= 0) return;
  for (const x of it) { yield x; if (--k === 0) return; }
}
function* map(it, f) { for (const x of it) yield f(x); }

console.log("[1] const [a, b, c] = naturals()");
const [a, b, c] = naturals();
console.log("  " + J([a, b, c]) + "   log " + J(L)); L.length = 0;

console.log("");
console.log("[2] for-of with break after 2");
for (const x of naturals()) if (x === 2) break;
console.log("  log " + J(L)); L.length = 0;

console.log("");
console.log("[3] hand-made take / map pipeline: [...take(map(naturals(), x => x * x), 3)]");
const sq = [...take(map(naturals(), (x) => { L.push("square " + x); return x * x; }), 3)];
console.log("  " + J(sq));
console.log("  log " + J(L)); L.length = 0;
```
```text
===== node20 js20b-20h-lazy-seq.js (exit=0) =====
[1] const [a, b, c] = naturals()
  [1,2,3]   log ["make 1","make 2","make 3","finally"]

[2] for-of with break after 2
  log ["make 1","make 2","finally"]

[3] hand-made take / map pipeline: [...take(map(naturals(), x => x * x), 3)]
  [1,4,9]
  log ["make 1","square 1","make 2","square 2","make 3","square 3","finally"]
```

```text
   [...take(map(naturals(), sq), 3)]

   take        map          naturals
   ----        ---          --------
   next  ──▶   next  ──▶    make 1  -> 1
               square 1 -> 1
   yield 1 ◀──
   next  ──▶   next  ──▶    make 2  -> 2
               square 2 -> 4
   yield 4 ◀──
   next  ──▶   next  ──▶    make 3  -> 3
               square 3 -> 9
   yield 9  -- k 가 0 -> take 가 return
              -> for...of 가 map 을 닫고 -> map 의 for...of 가 naturals 를 닫고 -> finally
```

- ★★★ **`[1]` `const [a, b, c] = naturals()` 는 `make 1`·`make 2`·`make 3` 셋만 만들고 `finally`** — 무한 루프가 **셋에서 멈췄고 닫혔다.**
  19번의 「`[a, b, c]` 도 `return()` 을 부른다」가 **제너레이터에서는 `finally` 로 보인다.**
- ★★ **`[2]` `break` 도 `make 1`·`make 2` 와 `finally`.**
- ★★★ **`[3]` 세 단 파이프라인의 로그가 `make 1, square 1, make 2, square 2, make 3, square 3, finally`** —
  **한 값이 세 단을 끝까지 지나간 뒤에야 다음 값이 만들어진다.** 「전부 만들고 → 전부 제곱하고 → 셋 자르기」가 **아니다.**
  ★★ 그리고 **넷째를 만들지 않았다** — `take` 가 셋째를 내보낸 직후 `return` 했고, 그 닫기가 **`for...of` 두 겹을 타고 `naturals` 의 `finally` 까지** 내려갔다.
  ★ 이 모양을 표준으로 만든 것이 ES2025 이터레이터 헬퍼다 — 배열 메서드판과 호출 횟수를 나란히 세는 것은 **21번 주제**가 정본이다.
- ★★★ **이 절은 「몇 개를 만들었나」만 셌다 — 메모리·시간은 안 쟀다.** 「제너레이터라서 메모리를 아낀다」는 이 문서의 결론이 아니다.

### (9) ★★ 파이썬과의 대비 — 첫 `send` 는 막고, 첫 `next(값)` 은 버린다

파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **17번** 「제너레이터 함수와 `yield`」가 이미 돌려 실은 출력이 있다 —
**막 시작한 제너레이터에 `None` 이 아닌 값을 `send` 하면 `TypeError: can't send non-None value to a just-started generator`** 다.

| 자리 | Python(17번 실측) | JS(이 문서 실측) |
|---|---|---|
| 값을 들여보내는 호출 | `g.send(v)` · `next(g)` 는 `g.send(None)` | `g.next(v)` · `g.next()` 는 `g.next(undefined)` |
| ★★★ **시작 전에 값을 들여보내면** | `TypeError` 로 **막는다** | ★★★ **에러 없이 버린다**(동작 (2)의 `A`) |
| `yield` 식의 값 | 다음 `send` 의 인자 | 다음 `next` 의 인자 — **같다** |
| 위임 | `yield from` — 하위의 `return` 값이 식의 값, `send`·`throw`·`close` 전달 | `yield*` — **같다**(동작 (5)) |
| 닫기 | `g.close()` — 멈춘 자리에 `GeneratorExit` | `g.return(v)` — 멈춘 자리에 `return v` |

- ★★★ **두 언어의 모델은 거의 같은데 「첫 값」에서만 정반대로 군다.** 파이썬은 **실수라고 알려 주고**, JS 는 **조용히 버린다.**
  JS 쪽에서 첫 값을 잃는 버그가 **에러 없이 합계만 틀리게** 나오는 이유다(동작 (2)의 `[3]` — 합계에서 10 이 통째로 빠졌다).
- ★ 파이썬 16번 「이터레이터 프로토콜」의 `StopIteration.value` 가 JS 의 `{ value, done: true }` 자리다 — 둘 다 **`for` 는 그 값을 안 보고, 위임(`yield from`/`yield*`)만 받는다.**
- ★ Kotlin 은 같은 「당긴 만큼만」을 **`sequence {}` 빌더**로 쓴다 — Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **47번**. 이 문서는 Kotlin 을 **안 돌렸다.**

## 문법 — 형태와 규칙

```text
   function* name(params) { ... }          제너레이터 선언
   const f = function* (params) { ... };   제너레이터 식
   const o = { *m() { ... } };             제너레이터 메서드 (객체)
   class C { *m() { ... }  static *s() { ... } }   제너레이터 메서드 (클래스)
   (화살표 제너레이터는 없다)

   yield expr          expr 을 내보내고 멈춘다. 식의 값 = 재개시킨 next 의 인자
   yield               undefined 를 내보낸다
   yield* iterable     iterable 에 위임한다. 식의 값 = 안쪽이 done: true 와 함께 준 value

   g.next(v)    -> { value, done }     멈춘 yield 의 값을 v 로 하고 재개
   g.return(v)  -> { value, done }     멈춘 자리에서 return v
   g.throw(e)   -> { value, done }     멈춘 자리에서 throw e  (안 받으면 이 호출이 던진다)
```

- **`yield` 는 그것을 직접 감싼 함수가 제너레이터일 때만** 키워드다. 콜백·중첩 함수 안에서는 못 쓴다(동작 (7)).
- **제너레이터 함수는 `new` 로 못 부른다** — `prototype` 이 있어도 그렇다(동작 (7)).
- **부르면 매개변수 목록은 돌고 본문은 안 돈다**(동작 (1)의 `[4]`).
- **끝난 제너레이터의 `next()` 는 `{ value: undefined, done: true }`** 를 계속 준다 — 에러가 아니다.
- **`yield` 는 우선순위가 낮은 식**이라 다른 식 안에 넣을 때 괄호가 필요하다(`"a" + (yield 1)`) — 이 문서는 그 규칙을 **따로 돌리지 않았다.**

## 어디서 틀리나

### (1) ★★★ 첫 `next(값)` 으로 설정값을 넘긴다

`g.next(config)` 를 첫 호출로 쓰면 **`config` 는 사라진다** — 에러도 경고도 없다(동작 (2)).
**설정은 제너레이터 함수의 인자로** 넘기고, `next(값)` 은 **첫 `next()` 로 첫 `yield` 까지 몰고 간 뒤**부터 쓴다.

### (2) ★★★ `next(값)` 의 값이 「이번에 나오는 값」과 짝이라고 읽는다

`next("B")` 가 받은 `out-2` 는 `B` 와 무관하다 — `B` 는 **그 전에 멈춘 `yield#1`** 의 값이 됐다(동작 (2)).
**질문과 대답이 한 박자 어긋난다**는 그림을 먼저 그려라.

### (3) ★★★ `return()` 이면 무조건 닫힌다고 믿는다

`finally` 안에 `yield` 가 있으면 `return()` 이 **`done: false`** 를 돌려주고 제너레이터는 **`finally` 중간에서 멈춘다**(동작 (3)의 `[2]`).
정리 코드의 `finally` 에서 **`yield` 하지 마라.**

### (4) ★★ `return` 한 값이 `for...of`·스프레드에 나온다고 믿는다

**안 나온다**(동작 (1)의 `[3]`, 19번). 구조 분해로 한 칸 더 받아도 `undefined` 다. **`return` 값은 `yield*` 만 받는다**(동작 (5)).

### (5) ★★ 「제너레이터를 부르면 아무 일도 안 일어난다」고 믿는다

**매개변수 기본값과 구조 분해는 호출에서 돈다**(동작 (1)의 `[4]`). 인자 검사를 본문 첫 줄에 두면 **첫 `next()` 까지 미뤄진다** —
빨리 실패시키고 싶으면 **평범한 함수로 감싸 검사하고 안쪽 제너레이터를 돌려주는** 모양을 쓴다.

### (6) ★★ `yield*` 에 배열을 넘기고 `throw()` 로 취소한다

배열 이터레이터에는 `throw` 가 없어서 **내가 던진 예외 대신 `TypeError` 가 나온다**(동작 (5)의 `[4]`). 받는 쪽이 예외 종류로 분기하면 엉뚱한 가지로 간다.

### (7) ★★ 콜백 안에서 `yield` 한다

`arr.forEach(x => { yield x; })` 는 `SyntaxError` 다(동작 (7)). **`for...of` 로 바꾸거나 `yield*` 로 위임**한다.
★ 비엄격 스크립트의 평범한 함수에서는 `yield` 가 **식별자**라 문구가 엉뚱한 토큰(`Unexpected number`)을 가리킨다.

### (8) ★ 「제너레이터는 메모리를 아낀다·느리다」를 근거 없이 옮긴다

이 문서는 **호출 횟수만** 셌다(동작 (8)). 시간과 메모리는 **안 쟀다.**

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **호출은 본문을 안 돌리고 제너레이터 객체를 돌려주는 것** · **본문은 인자 없이 시작하는 것**(`GeneratorStart`) — 그래서 **첫 `next` 의 값이 버려지는 것.**
- ★★★ **`yield` 식의 값이 그것을 재개시킨 `next` 의 인자인 것.**
- ★★★ **시작 전·끝난 뒤의 `return`/`throw` 가 본문을 안 돌리는 것**(`GeneratorResumeAbrupt`) · 끝난 뒤 `return(v)` 이 `{ v, done: true }` 인 것.
- ★★ **`return()`·`throw()` 가 멈춘 자리에서 `return`/`throw` 가 일어난 것처럼 구는 것** — 그래서 `finally` 의 `yield`·`return` 이 결과를 바꾸는 것.
- ★★★ **`yield*` 가 `next`·`throw`·`return` 을 안쪽으로 넘기고, 안쪽이 끝난 결과의 `value` 를 식의 값으로 받는 것** · 안쪽 첫 `next` 를 `undefined` 로 부르는 것.
- ★★ **안쪽에 `throw` 가 없으면 닫고 `TypeError`** 인 것(`yield*` 의 NOTE).
- ★★ **실행 중 재진입이 `TypeError`**(`GeneratorValidate`) · **`new` 가 `TypeError`** · **화살표 제너레이터가 문법에 없는 것.**

### 엔진(V8) 구현 · 이 판의 관찰

- **예외 문구 전부** — `gen is not a constructor` · `Unexpected token '*'` · `Unexpected number` · `Unexpected identifier 'x'`(v20) / `Unexpected identifier`(v18) ·
  `Generator is already running` · `Method [Generator].prototype.next called on incompatible receiver #<Object>` · `The iterator does not provide a 'throw' method.`
  **종류(`TypeError`·`SyntaxError`)만 명세가 정한다.**
- ★ **두 node 판에 이터레이터 헬퍼가 없는 것**(판별 블록) — 판의 사정이다.

### 호스트가 정하는 것 — ECMA-262 밖

- **이 주제의 블록에서 호스트가 정하는 칸은 없다.** 출력은 전부 `console.log` 에 **우리가 만든 문자열**만 넘겼다.

### 그래서 이렇게 적으면 틀린다

- 「`next(값)` 의 값은 이번 `yield` 가 받는다」 — **지난번 멈춘 `yield` 가 받는다. 첫 값은 아무도 안 받는다.**
- 「첫 `next(값)` 에 값을 주면 에러다」 — 그건 **파이썬**이다. JS 는 **조용히 버린다.**
- 「`return()` 은 제너레이터를 반드시 끝낸다」 — **`finally` 가 `yield` 하면 `done: false` 로 멈춘다.**
- 「`return()` 을 부르면 `finally` 가 돈다」 — **멈춘 자리가 `try` 안일 때만.** 시작 전이면 안 돈다.
- 「`yield*` 는 `for (const x of it) yield x` 의 줄임이다」 — **`return` 값 회수와 `throw`·`return` 전달이 다르다.**
- 「제너레이터는 `prototype` 이 있으니 `new` 가 된다」 — **안 된다**(08번과 같은 반례).
- 「제너레이터는 메모리를 아낀다」 — ★★★ **안 쟀다.**

## 언제 쓰고 언제 안 쓰나

- **쓴다** — 끝을 모르는 수열·페이지 조회를 **당긴 만큼만** 만들 때(동작 (8)) · 트리 순회를 **재귀 `yield*`** 로 짤 때 ·
  직접 이터러블을 만들 때 `[Symbol.iterator]` 를 **`*[Symbol.iterator]() { … }`** 로 쓰면 `next`/`done` 을 손으로 안 짜도 될 때.
- ★ **조심해서 쓴다** — `next(값)` 으로 값을 밀어 넣는 코루틴 모양. **첫 값을 잃는 함정**(동작 (2))을 문서에 적어 둔다.
- **안 쓴다** — 결과를 **두 번 돌아야** 하는 값(제너레이터 객체는 한 번 돌면 비어 있다 — 19번) · 비동기 흐름([목록의 **40번 주제**](../40-async-iteration-and-for-await/)의 `async function*`·`for await` 로).

## 핵심 문장

1. ★★★ **제너레이터를 부르면 본문은 안 돈다 — 매개변수만 돈다.** 본문은 첫 `next()` 에서 시작해 `yield` 마다 멈춘다.
2. ★★★ **`next(값)` 의 값은 지난번 멈춘 `yield` 식의 값이 된다 — 첫 `next(값)` 의 값은 받을 `yield` 가 없어 에러 없이 사라진다.**
3. ★★★ **`return()`·`throw()` 는 멈춘 자리에서 `return`/`throw` 를 일으킨다** — 시작 전·끝난 뒤에는 본문이 안 돌고, `finally` 가 `yield` 하면 `return()` 도 `done: false` 로 멈춘다.
4. ★★ **`return` 값은 `for...of`·스프레드·구조 분해가 안 보고 `yield*` 만 식의 값으로 받는다.**
5. ★★ **`yield*` 는 `next`·`throw`·`return` 을 안쪽으로 그대로 넘긴다** — 안쪽에 `throw` 가 없으면 닫고 `TypeError`.

## 관련 자료

- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — ★ **그쪽은 소비자가 `next`·`return` 을 언제 부르나(8곳)까지, 여기는 그 호출이 제너레이터 본문에서 무엇을 돌리나부터.**
- [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) — 그쪽은 함수 형태 격자(`prototype`·`new`)까지, 여기는 제너레이터의 `new` 가 막히는 것 한 줄만 재확인.
- [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md) — 그쪽은 표준 지연 파이프라인과 배열판의 호출 횟수 대비, 여기는 손으로 짠 `take`/`map` 까지.
- [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) — `[object Generator]` 를 만드는 `Symbol.toStringTag` 는 그쪽.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **17번**(`send`·`yield from`) · **16번**(이터레이터 프로토콜) · **15번**(제너레이터 표현식과 지연 평가) — 그쪽은 파이썬의 규칙, 여기는 대비 한 표(동작 (9)).
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **47번**(`Sequence`) — 같은 지연 평가를 빌더로 쓰는 쪽.
- [ECMA-262 — Control Abstraction Objects](https://tc39.es/ecma262/multipage/control-abstraction-objects.html) · [ECMA-262 — Functions and Classes](https://tc39.es/ecma262/multipage/ecmascript-language-functions-and-classes.html)

## 용어 풀이

- **제너레이터 함수** — `function*` 로 선언한 함수. 부르면 제너레이터 객체를 돌려준다.
- **제너레이터 객체** — 멈춘 자리를 기억하는 이터레이터. `next`·`return`·`throw` 를 가지고 `[Symbol.iterator]()` 가 자기 자신이다(19번).
- **`yield`** — 값을 내보내고 멈추는 식. 재개할 때 받은 값이 그 식의 값이다.
- **`yield*`** — 다른 이터러블에 위임하는 식. 안쪽이 끝날 때의 `value` 가 식의 값이다.
- **프라이밍(priming)** — 값을 밀어 넣기 전에 첫 `next()` 로 첫 `yield` 까지 몰고 가는 것.
- **시작 전(suspended-start) · `yield` 에서 멈춤(suspended-yield) · 실행 중(executing) · 끝남(completed)** — 명세의 제너레이터 상태 넷.
- **`GeneratorStart`** — 제너레이터 객체에 본문을 매달아 두는 명세 연산. 본문은 인자 없이 시작하도록 적혀 있다.
- **`GeneratorResumeAbrupt`** — `return()`·`throw()` 가 부르는 명세 연산. 시작 전이면 본문 없이 끝난 것으로 표시한다.
- **`GeneratorValidate`** — 받는 쪽이 제너레이터인지, 실행 중이 아닌지 검사하는 명세 연산.
- **브랜드(brand)** — 내부 슬롯으로 「이 종류의 객체인가」를 가리는 것. 프로퍼티(`Symbol.toStringTag`)와 달리 바꿔치기가 안 된다.

## 더 들어가면

- **`finally` 가 `yield` 하는 제너레이터를 `for...of` + `break` 로 닫으면** 제너레이터가 `finally` 중간에 멈춘 채 남는다 — 동작 (3)에서 **두 출력을 이어 읽은 추론**이고 로그로는 안 돌렸다. 확인하려면 그 조합에 로그를 심어 `break` 뒤에 `g.next()` 를 한 번 더 불러 보라.
- **`async function*`** 은 `next`/`return`/`throw` 가 전부 **프라미스를 돌려주고 요청을 큐에 쌓는다** — 명세의 `AsyncGeneratorEnqueue`. [목록의 **40번 주제**](../40-async-iteration-and-for-await/)가 정본이다.
- **`yield` 의 우선순위** — `yield a, b` 가 무엇을 내보내나, `yield` 뒤 줄바꿈이 무엇을 하나(ASI)는 이 문서가 돌리지 않았다.
