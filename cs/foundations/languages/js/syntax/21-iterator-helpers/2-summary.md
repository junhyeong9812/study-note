# js/syntax/21 — 이터레이터 헬퍼: 「배열 메서드는 단계마다 전부 돌고, 헬퍼는 한 값씩 끝까지 흘려보낸다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다** — 여기서는 **콜백과 원본 `next`/`return` 에 심은 로그**다.
> `arr.map(f).filter(g).slice(0, 2)` 와 `arr.values().map(f).filter(g).take(2).toArray()` 는 **결과가 한 글자도 같다**(`[20,40]`).
> 그런데 `f` 와 `g` 가 **몇 번, 어떤 순서로** 불렸는지는 결과에 흔적이 없다. ★★★ **값으로는 원리상 못 가른다.**
> 그래서 콜백마다 로그를 남기게 하고, 원본 이터레이터의 `next`·`return` 에도 로그를 심었다.
> **이 문서의 결론은 전부 그 로그와, 그 로그를 센 격자에서 나온다.**
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 2025 (16판)](https://262.ecma-international.org/16.0/) — `Iterator` 생성자 · `Iterator.from` · `Iterator.prototype` 의 `map`·`filter`·`take`·`drop`·`flatMap`·`reduce`·`toArray`·`forEach`·`some`·`every`·`find` · 추상 연산 `GetIteratorDirect` · `IteratorClose`. ★ **이 판에는 `Iterator.concat` 이 없다**(본문에서 그 이름을 찾아 0건).
> - [ECMA-262 2026 (17판)](https://262.ecma-international.org/17.0/) — `Iterator.concat` 이 **이 판에서 처음 나온다**(같은 검색 2건).
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 「Sync Iterator helpers」 **2025** · 「Iterator Sequencing」 **2026** · 「Explicit Resource Management」 **2027**
>
> ★ 명세 문장을 인용하는 곳은 딱 한 군데다 — `Iterator.prototype.take` 의 단계 가운데
> 「`If numLimit is NaN, then … Return ? IteratorClose(iterated, error).`」(16판). 나머지 규칙 진술은 **추상 연산 이름**으로만 하고,
> **값·호출 로그·예외 타입과 메시지는 전부 실행으로** 접지했다. 명세 조항 번호는 인용하지 않는다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> ★★★ **헬퍼는 이 머신의 node 두 판(v18.19.1 · v20.19.6)에 없다** — 아래 판별 블록이 그 근거다.
> 그래서 **본체 탐침은 전부 Google Chrome 151 의 헤드리스 모드**에서 돌렸다. 탐침 파일 하나를 `js20b-page.html?<파일>` 로 열고,
> 페이지가 `console.log` 를 가로채 모은 줄을 `--dump-dom` 으로 받는다(페이지 소스도 아래에 싣는다).
> 배너가 `google-chrome --headless …` 인 블록이 그것이고, `node20` 배너는 `~/.nvm/versions/node/v20.19.6/bin/node` 다.
> ★★ **예외는 `try`/`catch` 로 받아 `이름 「메시지」` 꼴로만** 찍었다 — 스택트레이스는 한 줄도 싣지 않는다.
> ★ **이 주제의 블록에는 주소도 시간도 난수도 없다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.
>
> **버전** — 이 주제는 **한 판(ES2025)에 들어왔다.** 그 위에 얹힌 것 하나가 다음 판이다.
>
> | 무엇 | 판 | node 18 / 20 | Chrome 151 |
> |---|---|---|---|
> | 이터레이터 프로토콜 · 제너레이터 · 배열 메서드 `map`/`filter`/`slice` | **ES2015** 이전\~ES2015 | 있다 | 있다 |
> | 전역 `Iterator` · `Iterator.from` · `Iterator.prototype.map`/`take`/… | **ES2025** | **없다** | 있다 |
> | `Iterator.concat` | **ES2026** | 없다(안 물었다 — 헬퍼 자체가 없다) | 있다 |
> | `Iterator.prototype[Symbol.dispose]` | ES2027 쪽(finished proposals 의 해) — ★ 이 문서는 **쓰지 않는다** | — | 있다(동작 (4)의 `[3]`) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | 콜백 `map(x)` · `filter(x)` 로그 → **몇 번 · 어떤 순서로** · 원본의 `next#N` · `return()` 로그 → **원본을 몇 번 당기고 언제 닫나** |
> | ★★★ **② 전수 격자** | 파이프라인 열 벌을 배열판/헬퍼판으로 → **값이 갈린 칸 / 호출 수가 갈린 칸**을 스크립트가 센다 · 헬퍼·종단 메서드 14가지의 `return()` 요약 표 |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 인자 검사가 **만드는 순간**에 던지나 **첫 `next()`** 에 던지나 — 그리고 그때 원본을 닫나. ★ **문구가 원인을 가리키지 않는 자리가 하나 있다**(`flatMap` — 어디서 틀리나 (6)) |
> | ★★ **판별 블록** | 이 기능이 **판마다 있나** — node 두 판과 Chrome 을 같은 스크립트로 |
> | ★★ **창을 바꿔 물었다**(제5의 상태) | node 에는 헬퍼가 없어 **같은 질문(「한 값씩 흐르나」)을 제너레이터 함수로 손수 만든 파이프라인**에 던졌다(동작 (7)) — 로그가 헬퍼판과 **한 글자도 같다** |
> | ★ **부적용 — ③ 브랜드 태그** | 헬퍼가 붙느냐는 **내부 슬롯이 아니라 프로토타입 사슬**이 정한다(동작 (4)) — `Object.prototype.toString` 이 답할 질문이 없다. **잴 것이 없다** |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | 이 주제에는 `SyntaxError` 가 한 줄도 없다. 헬퍼는 전부 런타임 메서드다 — **잴 것이 없다** |
> | ★★★ **안 쟀다 — 시간 · 메모리** | 「헬퍼는 메모리를 아낀다」·「헬퍼가 배열보다 빠르다」를 **한 줄도 쓰지 않는다.** 센 것은 **콜백 호출 수와 원본을 당긴 수**뿐이다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(V8 의 표현 — 판이 오르면 바뀔 수 있다) | ★★★ **콜백 로그의 개수와 순서** · 원본 `next`/`return` 로그 |
> | Chrome 의 **판 번호**(판별 블록 첫 줄) | ★★★ **예외의 종류**(`TypeError`/`RangeError`)와 **던진 시점**(만들 때 / 첫 `next()`) |
> | 스택트레이스 — 한 줄도 싣지 않았다 | ★★ 격자의 **「갈린 칸 N / M」** 집계 줄 · 결과 값 |
>
> 이 주제의 탐침 가운데 **node 에서 도는 것은 `js20b-21x-node-absent.js` 하나**다 — 두 판 대조기는 그 줄을 `identical` 로 세었다.
> 배치 전체의 집계 줄은 판별 블록 바로 아래에 싣는다(대조기 전문은 3-answer 의 10번).
>
> **선행** — [20 — 제너레이터](../20-generators/2-summary.md)(★★★ 직접 선행) · [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ `return()` 의 규칙) ·
> [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md)(헬퍼가 **어디에** 붙어 있나).
> ★★★ **19번이 이미 잰 것을 다시 재지 않는다** — 소비자 17가지 중 `return()` 이 불린 자리는 **8가지**였고(`return() was called in 8 of 17 probes`),
> `const [a, b, c] = it` 이 값이 딱 셋인데도 닫는다는 것, `next()` 자체가 던지면 닫지 않는다는 것도 거기서 봤다.
> 그리고 19번 `js16b-19f-close-and-helpers.js` 의 `[4]` 가 **node20 에 `typeof globalThis.Iterator` 가 `undefined`** 임을 이미 찍었다.
> **이어지는 곳** — [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) · [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) · 목록의 **40번 주제** 「비동기 이터레이션」
>
> ★★ **경계 — `return()` 이 언제 불리나의 규칙은 19번이 정본이다.** 여기서는 **헬퍼·종단 메서드가 그 규칙 위에서 원본을 언제 닫나**만 본다.
> ★★ **경계 — 제너레이터의 내부 흐름(`yield`·`next(값)`·`yield*`)은 20번이 정본이다.** 여기서 제너레이터는 **끝없는 원본**과 **손수 만든 파이프라인**으로만 쓴다.
> ★ **경계 — 배열 메서드 자체(`map`·`filter`·`slice` 의 비변형 계약)는** [목록의 **25번 주제**](../25-array-non-mutating-and-copy-methods/) 「배열 비변형·복사 메서드」**가 정본이다.** 여기서는 **평가 시점의 대비 상대**로만 쓴다.

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

- ★★★ **node 두 판은 ES2025 의 세 줄이 전부 `no`, Chrome 151 은 전부 `yes`** 다. `Iterator.from` 은 node 에서 `no (ReferenceError)` — **전역 이름 `Iterator` 자체가 없다.**
- ★ 이 판별 블록은 22·23번과 **공유한다** — ES2023·ES2026 줄은 그 편들의 몫이다.

두 node 판 대조기의 집계 줄(배치 전체 — 이 주제의 것은 `js20b-21x-node-absent.js` 한 줄이고 `identical` 이다) —

`identical 18  ·  differs 6  ·  total 24`

브라우저 탐침을 돌리는 페이지는 이것 하나다.

```html
<!-- js20b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js20b</title>
<pre id="o"></pre>
<script>
// 탐침 스크립트 하나를 이 페이지에서 돌린다 -- 파일 이름은 주소의 ? 뒤에 온다.
// console.log 를 가로채 줄을 모으고, 마지막 스크립트가 그 줄을 <pre> 에 쓴다(--dump-dom 이 그것을 내보낸다).
const __lines = [];
console.log = (...a) => { __lines.push(a.join(" ")); };
window.addEventListener("error", (e) => { __lines.push("uncaught " + e.message); });
document.write('<script src="' + location.search.slice(1) + '"><\/script>');
</script>
<script>
document.getElementById("o").textContent = "==" + "=OUT===\n" + __lines.join("\n") + "\n===END" + "===";
</script>
```

- ★ `console.log` 를 가로채 줄을 모으고, **다음 `<script>` 가 그 줄을 `<pre>` 에 쓴다.** 그래서 **동기 코드와 마이크로태스크까지만** 잡힌다(이 주제의 탐침은 전부 동기다).
- ★ 잡히지 않은 예외는 `uncaught …` 로 남게 해 두었다 — **이 주제의 블록에는 그 줄이 하나도 없다.**

## 한눈에 — 쉽게 말하면

**배열 메서드 사슬은 「공정별 일괄 작업장」** 이다. 1공정(`map`)이 **상자 열 개를 전부** 처리해 선반에 올려야 2공정(`filter`)이 시작하고,
2공정도 **열 개를 전부** 본 다음에야 3공정(`slice(0, 2)`)이 「앞의 두 개만 주세요」를 한다.

**이터레이터 헬퍼 사슬은 「컨베이어 벨트」** 다. 상자가 **한 개씩** 1공정 → 2공정을 지나 포장대에 닿고,
포장대(`take(2)`)가 **두 개를 받으면 벨트를 멈춘다.** 3번째 상자부터는 **아무 공정도 손대지 않는다.**
그리고 **포장대가 「주세요」라고 하기 전에는 벨트가 아예 안 돈다**(`toArray()` 같은 종단 메서드가 그 「주세요」다).

- ★★★ **결과는 같다** — 둘 다 `[20,40]`. **다른 것은 일한 양과 순서**다.
- ★★★ **벨트는 한 번 흘려보낸 상자를 되돌리지 않는다** — 헬퍼는 원본을 **소비**한다. 두 번째 `toArray()` 는 `[]` 다.
- ★★ **벨트를 멈출 때 창고에 「그만」이라고 알린다** — 원본의 `return()`. 이것이 19번의 `IteratorClose` 다.

```text
   배열판  arr.map(f).filter(g).slice(0, 2)            헬퍼판  arr.values().map(f).filter(g).take(2).toArray()

   [1 2 3 4 5 6 7 8 9 10]                              1 ─f─▶ 10 ─g─▶ 버림
     │ f 를 10번                                         2 ─f─▶ 20 ─g─▶ 통과 ──▶ [20]
     ▼                                                  3 ─f─▶ 30 ─g─▶ 버림
   [10 20 30 ... 100]      (중간 배열 하나)              4 ─f─▶ 40 ─g─▶ 통과 ──▶ [20, 40]   <- 둘 찼다. 멈춘다
     │ g 를 10번                                         5 .. 10          (아무도 안 건드린다)
     ▼
   [20 40 60 80 100]       (중간 배열 또 하나)
     │ slice(0, 2)
     ▼
   [20 40]

   f 10번 · g 10번                                      f 4번 · g 4번       <- 동작 (1)의 실측
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 공정별 일괄 작업장 | 배열 메서드 사슬 — 단계마다 **새 배열**을 만든다 | 로그가 `map(1) … map(10)` 뒤에 `filter(10) …` |
| 컨베이어 벨트 | 헬퍼 사슬 — 단계마다 **새 이터레이터**(헬퍼 객체)를 만든다 | 로그가 `map(1) filter(10) map(2) filter(20) …` 로 번갈아 |
| 포장대의 「주세요」 | 종단 메서드(`toArray`·`reduce`·`forEach`·`some`·`every`·`find`) 또는 `next()` | 종단 전에는 로그 0 |
| 「두 개만」 | `take(2)` | 콜백 4번에서 멈춤 |
| 흘려보낸 상자 | 원본에서 이미 꺼낸 값 — 되돌릴 수 없다 | 두 번째 `toArray()` 가 `[]` |
| 창고에 「그만」 | 원본의 `return()` — `IteratorClose` | 원본 로그의 `return()` |
| 벨트 규격 | `Iterator.prototype` — 헬퍼가 사는 곳 | 모든 내장 이터레이터의 사슬 위에 있다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**로그 파일 줄 이터레이터에서 조건에 맞는 첫 두 줄만 필요한데 전체를 배열로 만든 뒤 걸렀다**」와
「**`const top = gen.map(f); top.toArray()` 를 두 번 불렀더니 두 번째가 비어 있었다**」가 그것이다.
앞엣것은 **공정별 작업장을 쓴 쪽**이고, 뒤엣것은 **벨트가 상자를 되돌리지 않는 쪽**이다.

> **이터레이터 헬퍼(iterator helpers)** — `Iterator.prototype` 에 붙은 메서드들. ES2025.\
> 예: `[1, 2, 3].values().map((x) => x * 2).toArray()` 가 `[2, 4, 6]`.

> **종단 메서드** — 헬퍼 사슬 끝에서 **값을 실제로 당겨** 결과를 내는 메서드(`toArray`·`reduce`·`forEach`·`some`·`every`·`find`). 이 문서의 말이다.\
> 예: `it.map(f)` 만으로는 아무것도 안 돌고, `.toArray()` 를 붙여야 돈다.

> **지연 평가(lazy evaluation)** — 값이 **필요해질 때** 계산하는 것. 헬퍼 사슬은 종단 메서드가 값을 달라고 할 때 원본을 한 칸씩 당긴다.\
> 예: 끝없는 제너레이터에 `.take(5)` 를 걸면 원본을 5번만 당긴다(동작 (3)).

## 이 주제가 답하려는 질문

1. **같은 파이프라인을 배열 메서드와 헬퍼로 쓰면 콜백이 언제, 몇 번, 어떤 순서로 불리나** — 그리고 **어느 모양에서 갈리고 어느 모양에서 안 갈리나?**
2. **헬퍼는 어디에 붙어 있어서** 제너레이터·`Map` 이터레이터·문자열 이터레이터에 다 쓸 수 있고, **손으로 만든 `{ next }` 객체**에는 왜 안 붙나?
3. **헬퍼는 원본에 무엇을 하나** — 소비하나, 언제 닫나, 인자가 틀리면 **언제** 던지나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 같은 파이프라인 두 벌 — 이 주제의 본체

**언제 쓰나** — 「이 사슬이 **일을 얼마나 하나**」를 물을 때. ★★★ 결과만 보면 답이 안 나온다.

원본은 `1..10`, `map` 은 `x * 10`, `filter` 는 **20 의 배수만**, 그리고 **앞의 두 개**.
콜백 둘이 부를 때마다 `map(x)`·`filter(x)` 를 로그에 남긴다.

```js
// js20b-21a-when.web.js
// 같은 파이프라인을 두 벌로 -- 배열 메서드판과 이터레이터 헬퍼판. 콜백이 「언제 · 몇 번 · 어떤 순서로」 불리나를 로그로 찍는다.
// 원본은 1..10. map 은 x*10, filter 는 20 의 배수만, 앞의 두 개만 취한다.
const L = [];
const src = () => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const mapFn = (x) => { L.push("map(" + x + ")"); return x * 10; };
const keep = (x) => { L.push("filter(" + x + ")"); return x % 20 === 0; };
const n = (p) => L.filter((m) => m.startsWith(p)).length;

console.log("[1] array methods: arr.map(f).filter(g).slice(0, 2)");
L.length = 0;
const a = src().map(mapFn).filter(keep).slice(0, 2);
console.log("    result " + JSON.stringify(a));
console.log("    map calls " + n("map(") + " · filter calls " + n("filter("));
console.log("    order  " + L.join(" "));
const arrayCounts = [n("map("), n("filter(")];

console.log("");
console.log("[2] iterator helpers: arr.values().map(f).filter(g).take(2)");
L.length = 0;
const pipe = src().values().map(mapFn).filter(keep).take(2);
console.log("    after building the pipeline:  log entries " + L.length);
const h = pipe.toArray();
console.log("    after toArray():  result " + JSON.stringify(h));
console.log("    map calls " + n("map(") + " · filter calls " + n("filter("));
console.log("    order  " + L.join(" "));
const helperCounts = [n("map("), n("filter(")];

console.log("");
console.log("[3] the same helper pipeline, one next() at a time");
L.length = 0;
const step = src().values().map(mapFn).filter(keep).take(2);
for (let i = 1; i <= 3; i++) {
  const before = L.length;
  const r = step.next();
  console.log("    next#" + i + "  " + JSON.stringify(r).padEnd(28) + " callbacks run in this call: " + (L.slice(before).join(" ") || "(none)"));
}

console.log("");
console.log("[4] counts side by side  (array / helper)");
console.log("    map     " + arrayCounts[0] + " / " + helperCounts[0]);
console.log("    filter  " + arrayCounts[1] + " / " + helperCounts[1]);
console.log("    results equal: " + String(JSON.stringify(a) === JSON.stringify(h)));
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21a-when.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] array methods: arr.map(f).filter(g).slice(0, 2)
    result [20,40]
    map calls 10 · filter calls 10
    order  map(1) map(2) map(3) map(4) map(5) map(6) map(7) map(8) map(9) map(10) filter(10) filter(20) filter(30) filter(40) filter(50) filter(60) filter(70) filter(80) filter(90) filter(100)

[2] iterator helpers: arr.values().map(f).filter(g).take(2)
    after building the pipeline:  log entries 0
    after toArray():  result [20,40]
    map calls 4 · filter calls 4
    order  map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)

[3] the same helper pipeline, one next() at a time
    next#1  {"value":20,"done":false}    callbacks run in this call: map(1) filter(10) map(2) filter(20)
    next#2  {"value":40,"done":false}    callbacks run in this call: map(3) filter(30) map(4) filter(40)
    next#3  {"done":true}                callbacks run in this call: (none)

[4] counts side by side  (array / helper)
    map     10 / 4
    filter  10 / 4
    results equal: true
```

```text
   ★ 평가 시점 — 같은 두 값 [20, 40] 을 얻는 두 줄

   배열판   map(1) map(2) map(3) map(4) map(5) map(6) map(7) map(8) map(9) map(10) │ filter(10) filter(20) ... filter(100) │ slice
            └──────────────── 1단계가 전부 끝난다 ─────────────────────────────────┘ └────── 2단계가 전부 끝난다 ─────────┘

   헬퍼판   (사슬을 만든 순간: 0)   toArray() ─▶ map(1) filter(10) map(2) filter(20) │ map(3) filter(30) map(4) filter(40) │ (끝)
                                                └──────── next#1 이 한 일 ───────┘ └──────── next#2 가 한 일 ───────┘  next#3: (none)
```

- ★★★ **`[1]` 배열판은 `map calls 10 · filter calls 10`** 이다. 로그 순서가 **`map` 열 개 → `filter` 열 개**로 **단계별로 뭉쳐** 있다.
  `slice(0, 2)` 는 이미 다 계산된 배열에서 앞 둘을 자를 뿐이다.
- ★★★ **`[2]` 헬퍼판은 사슬을 만든 직후 `log entries 0`** — `map`·`filter`·`take` 를 **다 불렀는데 콜백이 한 번도 안 돌았다.**
  `toArray()` 를 부르자 **`map calls 4 · filter calls 4`** 이고, 순서가 **`map(1) filter(10) map(2) filter(20) …`** 으로 **값마다 번갈아** 간다.
- ★★★ **`[3]` `next()` 를 하나씩 부르면 「누가 어느 일을 했나」가 보인다** — `next#1` 이 `map(1) filter(10) map(2) filter(20)` 를,
  `next#2` 가 `map(3) filter(30) map(4) filter(40)` 을 했고, **`next#3` 은 콜백을 하나도 안 부르고 `{"done":true}`** 다.
  ★★ **`take(2)` 는 두 개를 내준 뒤 세 번째 요청에 원본을 당기지 않고 끝낸다** — 그래서 `map(5)` 가 영영 없다. 원본 쪽 로그는 동작 (6)에서 본다.
- ★ **`[4]` 결과는 `results equal: true`** 다. **같은 값을 다른 양의 일로 얻었다.**

★★ **「배열판은 열 번, 헬퍼판은 필요한 만큼」은 이 모양의 파이프라인에서 맞다** — 그런데 **모든 모양에서 갈리는 것은 아니다.** 다음 격자가 그것을 센다.

### (2) ★★★ 격자 — 열 벌 중 몇 벌에서 갈리나

**언제 쓰나** — 「헬퍼로 바꾸면 **언제나** 일이 준다」를 반증하고 싶을 때.

```js
// js20b-21b-grid.web.js
// 격자 -- 파이프라인 여러 벌을 배열판 / 헬퍼판으로 돌려 「결과 값」과 「콜백 호출 수」를 칸마다 견준다.
// 원본은 언제나 1..10. 콜백은 전부 한 계수기를 올린다.
let calls = 0;
const f = (fn) => (...args) => { calls++; return fn(...args); };
const arr = () => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const it = () => arr().values();
const cases = [
  ["map(x*2) then first 3", () => arr().map(f((x) => x * 2)).slice(0, 3), () => it().map(f((x) => x * 2)).take(3).toArray()],
  ["filter(odd) then first 2", () => arr().filter(f((x) => x % 2)).slice(0, 2), () => it().filter(f((x) => x % 2)).take(2).toArray()],
  ["skip 3, then map, first 2", () => arr().slice(3).map(f((x) => -x)).slice(0, 2), () => it().drop(3).map(f((x) => -x)).take(2).toArray()],
  ["find(x > 3)", () => arr().find(f((x) => x > 3)), () => it().find(f((x) => x > 3))],
  ["some(x === 2)", () => arr().some(f((x) => x === 2)), () => it().some(f((x) => x === 2))],
  ["every(x < 4)", () => arr().every(f((x) => x < 4)), () => it().every(f((x) => x < 4))],
  ["map then find(x > 30)", () => arr().map(f((x) => x * 10)).find(f((x) => x > 30)), () => it().map(f((x) => x * 10)).find(f((x) => x > 30))],
  ["flatMap([x, x]) then first 3", () => arr().flatMap(f((x) => [x, x])).slice(0, 3), () => it().flatMap(f((x) => [x, x])).take(3).toArray()],
  ["reduce(sum)", () => arr().reduce(f((s, x) => s + x), 0), () => it().reduce(f((s, x) => s + x), 0)],
  ["map then reduce(sum)", () => arr().map(f((x) => x * 2)).reduce(f((s, x) => s + x), 0), () => it().map(f((x) => x * 2)).reduce(f((s, x) => s + x), 0)],
];
const run = (fn) => { calls = 0; const v = fn(); return [JSON.stringify(v), calls]; };
let valueDiff = 0, callDiff = 0;
console.log("pipeline".padEnd(32) + "array value".padEnd(16) + "helper value".padEnd(16) + "calls array / helper");
for (const [label, A, H] of cases) {
  const [va, ca] = run(A);
  const [vh, ch] = run(H);
  if (va !== vh) valueDiff++;
  if (ca !== ch) callDiff++;
  console.log(label.padEnd(32) + va.padEnd(16) + vh.padEnd(16) + String(ca).padStart(2) + " / " + String(ch).padStart(2) + (ca !== ch ? "   <- differs" : ""));
}
console.log("");
console.log("value cells that differ " + valueDiff + " / " + cases.length);
console.log("call-count cells that differ " + callDiff + " / " + cases.length);
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21b-grid.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
pipeline                        array value     helper value    calls array / helper
map(x*2) then first 3           [2,4,6]         [2,4,6]         10 /  3   <- differs
filter(odd) then first 2        [1,3]           [1,3]           10 /  3   <- differs
skip 3, then map, first 2       [-4,-5]         [-4,-5]          7 /  2   <- differs
find(x > 3)                     4               4                4 /  4
some(x === 2)                   true            true             2 /  2
every(x < 4)                    false           false            4 /  4
map then find(x > 30)           40              40              14 /  8   <- differs
flatMap([x, x]) then first 3    [1,1,2]         [1,1,2]         10 /  2   <- differs
reduce(sum)                     55              55              10 / 10
map then reduce(sum)            110             110             20 / 20

value cells that differ 0 / 10
call-count cells that differ 5 / 10
```

- ★★★ **값이 갈린 칸 `0 / 10`, 호출 수가 갈린 칸 `5 / 10`** — 마지막 두 줄은 **스크립트가 센 것**이다.
- ★★★ **갈린 다섯 칸에는 공통점이 하나 있다** — **「앞의 몇 개만」(`slice`/`take`) 이 사슬의 뒤에 붙어 있다**(또는 `find` 앞에 `map` 이 있다).
  배열판은 **앞 단계가 원본 전체를 다 돈 뒤에야** 뒤 단계가 「그만」을 말할 수 있고, 헬퍼판은 뒤 단계의 「그만」이 **앞 단계까지 거슬러 올라간다.**
  `map then find(x > 30)` 가 `14 / 8` 인 것이 그 모양이다 — 배열판은 `map` 10 + `find` 4, 헬퍼판은 `map` 4 + `find` 4.
- ★★★ **안 갈린 다섯 칸도 두 부류다.**
  - **`find`·`some`·`every` 한 단계만** 있을 때 — `4 / 4` · `2 / 2` · `4 / 4`. ★ **배열의 `find`·`some`·`every` 도 원래 도중에 멈춘다** —
    「배열은 전부 돈다」가 아니라 **「배열은 단계마다 새 배열을 만든다」** 가 정확한 말이다. 한 단계면 만들 것이 없다.
  - **`reduce` 처럼 전부 봐야 답이 나올 때** — `10 / 10` · `20 / 20`. **어느 쪽이든 원본 전체를 봐야 하니** 헬퍼가 줄일 것이 없다.
- ★ `skip 3, then map, first 2` 는 배열판이 `7` 이다 — `slice(3)` 이 **콜백 없이** 앞 셋을 잘라서다. 헬퍼판 `drop(3)` 도 콜백은 없지만 원본을 셋 **당기기는** 한다(동작 (6)의 `drop`).

```text
   「뒤에서 그만」이 앞 단계까지 닿나

   배열판   [map ───── 10개 전부 ─────▶ 새 배열] ──▶ [slice: 앞 2개]            그만이 닿지 않는다 (앞 단계는 이미 끝났다)
   헬퍼판   [map] ◀─ 하나 줘 ─ [filter] ◀─ 하나 줘 ─ [take(2)] ◀─ 하나 줘 ─ toArray
             │                                          │
             └── take 가 "그만" 하면 map 도 더 안 불린다 ─┘                          그만이 원본까지 거슬러 간다

   ★ 안 갈리는 두 경우
     · 단계가 하나 (find / some / every) — 배열판도 도중에 멈춘다
     · 전부 봐야 답이 나온다 (reduce)   — 헬퍼판도 끝까지 간다
```

### (3) ★★ 끝없는 원본 — 배열로는 시작도 못 하는 것

**언제 쓰나** — 원본에 **끝이 없거나 끝을 모를 때**(자연수 · 입력 스트림 · 폴링 결과).

```js
// js20b-21c-endless.web.js
// 끝이 없는 제너레이터에 헬퍼를 건다. 원본이 몇 번 불렸나를 센다.
let pulled = 0;
function* naturals() { let i = 1; while (true) { pulled++; yield i++; } }

const show = (label, fn) => {
  pulled = 0;
  let r;
  try { r = JSON.stringify(fn()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log(label.padEnd(46) + r.padEnd(22) + "values pulled " + pulled);
};
show("naturals().take(5).toArray()", () => naturals().take(5).toArray());
show("naturals().map(x => x * x).take(4).toArray()", () => naturals().map((x) => x * x).take(4).toArray());
show("naturals().filter(x => x % 7 === 0).take(3)", () => naturals().filter((x) => x % 7 === 0).take(3).toArray());
show("naturals().drop(100).take(2).toArray()", () => naturals().drop(100).take(2).toArray());
show("naturals().find(x => x * x > 50)", () => naturals().find((x) => x * x > 50));
show("naturals().some(x => x === 3)", () => naturals().some((x) => x === 3));
show("naturals().every(x => x < 5)", () => naturals().every((x) => x < 5));
show("naturals().map(x => x)  (no terminal)", () => { naturals().map((x) => x); return "built"; });
show("naturals().take(0).toArray()", () => naturals().take(0).toArray());
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21c-endless.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
naturals().take(5).toArray()                  [1,2,3,4,5]           values pulled 5
naturals().map(x => x * x).take(4).toArray()  [1,4,9,16]            values pulled 4
naturals().filter(x => x % 7 === 0).take(3)   [7,14,21]             values pulled 21
naturals().drop(100).take(2).toArray()        [101,102]             values pulled 102
naturals().find(x => x * x > 50)              8                     values pulled 8
naturals().some(x => x === 3)                 true                  values pulled 3
naturals().every(x => x < 5)                  false                 values pulled 5
naturals().map(x => x)  (no terminal)         "built"               values pulled 0
naturals().take(0).toArray()                  []                    values pulled 0
```

- ★★★ **`take(5)` 는 원본을 `5` 번 당긴다**(`values pulled 5`). `map(x => x * x).take(4)` 도 `4` 번이다.
- ★★ **`filter(x => x % 7 === 0).take(3)` 은 `21` 번** 당긴다 — 7·14·21 을 찾을 때까지. **걸러지는 값도 당겨야 걸러진다.**
  `drop(100).take(2)` 는 **`102`** 번 — `drop` 은 버리는 값도 당긴다.
- ★★ **`find`·`some`·`every` 도 답이 정해지는 순간 멈춘다** — `8` · `3` · `5` 번.
- ★★★ **종단 메서드가 없으면 `values pulled 0`** 이다(`naturals().map(x => x)` 는 헬퍼 객체만 만들고 끝났다).
  ★ `take(0).toArray()` 도 `0` 이다 — **아무것도 달라고 하지 않았다.**
- ★★ **같은 일을 배열로 하는 방법은 없다** — `[...naturals()]` 는 **돌아오지 않는다.** ★ 이 문서는 그것을 **일부러 돌리지 않았다**(끝나지 않는 탐침은 캡처를 멈춘다).

```text
   naturals()  ──▶ 1 2 3 4 5 6 7 ...  (끝이 없다)

   .take(5).toArray()            당긴다: 1 2 3 4 5            그리고 닫는다           -> [1,2,3,4,5]   pulled 5
   .filter(%7).take(3)           당긴다: 1 .. 21 (21개)        7 14 21 만 통과        -> [7,14,21]     pulled 21
   .map(x => x)                  당긴다: (없음)                종단 메서드가 없다     -> 헬퍼 객체만   pulled 0
   [...naturals()]               당긴다: 1 2 3 ... (영원히)    -- 돌리지 않았다 --
```

### (4) ★★ 헬퍼는 어디에 사나 — `Iterator.prototype` 과 `Iterator.from`

**언제 쓰나** — 「**이 이터레이터에 `.map` 이 있나**」를 판정할 때. ★ 답은 **사슬**이 한다(15번 주제의 조회 규칙 그대로).

```js
// js20b-21d-chain.web.js
// 헬퍼는 어디에 붙어 있나 -- 이터레이터마다 프로토타입 사슬을 따라가며 Iterator.prototype 을 몇 단계 위에서 만나는지 찍는다.
const IP = Iterator.prototype;
const name = (p) => {
  if (p === null) return "null";
  if (p === IP) return "Iterator.prototype";
  if (p === Object.prototype) return "Object.prototype";
  if (p === gen.prototype) return "gen.prototype";
  const tag = Object.prototype.hasOwnProperty.call(p, Symbol.toStringTag) ? p[Symbol.toStringTag] : "?";
  return "(" + tag + " proto)";
};
const chain = (o) => { const out = []; let p = Object.getPrototypeOf(o); while (p !== null) { out.push(name(p)); p = Object.getPrototypeOf(p); } return out.join(" -> "); };
function* gen() { yield 1; }
const samples = [
  ["[1].values()", [1].values()],
  ["new Map([[1, 2]]).entries()", new Map([[1, 2]]).entries()],
  ["new Set([1]).values()", new Set([1]).values()],
  ["'ab'[Symbol.iterator]()", "ab"[Symbol.iterator]()],
  ["'a-b'.matchAll(/-/g)", "a-b".matchAll(/-/g)],
  ["gen()", gen()],
  ["{ next() {...} }  (hand-written)", { next() { return { done: true }; } }],
];
console.log("[1] prototype chain of each iterator");
for (const [label, o] of samples) console.log("  " + label.padEnd(34) + chain(o));

console.log("");
console.log("[2] typeof o.map / typeof o.toArray");
for (const [label, o] of samples) console.log("  " + label.padEnd(34) + typeof o.map + " / " + typeof o.toArray);

console.log("");
console.log("[3] own properties of Iterator.prototype (names, sorted)");
console.log("  " + Reflect.ownKeys(IP).map(String).sort().join(" "));

console.log("");
console.log("[4] Iterator itself");
const t = (label, fn) => { let r; try { r = String(fn()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; } console.log("  " + label.padEnd(56) + r); };
t("typeof Iterator", () => typeof Iterator);
t("new Iterator()", () => new Iterator());
t("class C extends Iterator; new C() instanceof Iterator", () => { class C extends Iterator { next() { return { done: true }; } } return new C() instanceof Iterator; });
t("[1].values() instanceof Iterator", () => [1].values() instanceof Iterator);
t("gen() instanceof Iterator", () => gen() instanceof Iterator);
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21d-chain.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] prototype chain of each iterator
  [1].values()                      (Array Iterator proto) -> Iterator.prototype -> Object.prototype
  new Map([[1, 2]]).entries()       (Map Iterator proto) -> Iterator.prototype -> Object.prototype
  new Set([1]).values()             (Set Iterator proto) -> Iterator.prototype -> Object.prototype
  'ab'[Symbol.iterator]()           (String Iterator proto) -> Iterator.prototype -> Object.prototype
  'a-b'.matchAll(/-/g)              (RegExp String Iterator proto) -> Iterator.prototype -> Object.prototype
  gen()                             gen.prototype -> (Generator proto) -> Iterator.prototype -> Object.prototype
  { next() {...} }  (hand-written)  Object.prototype

[2] typeof o.map / typeof o.toArray
  [1].values()                      function / function
  new Map([[1, 2]]).entries()       function / function
  new Set([1]).values()             function / function
  'ab'[Symbol.iterator]()           function / function
  'a-b'.matchAll(/-/g)              function / function
  gen()                             function / function
  { next() {...} }  (hand-written)  undefined / undefined

[3] own properties of Iterator.prototype (names, sorted)
  Symbol(Symbol.dispose) Symbol(Symbol.iterator) Symbol(Symbol.toStringTag) constructor drop every filter find flatMap forEach map reduce some take toArray

[4] Iterator itself
  typeof Iterator                                         function
  new Iterator()                                          TypeError 「Abstract class Iterator not directly constructable」
  class C extends Iterator; new C() instanceof Iterator   true
  [1].values() instanceof Iterator                        true
  gen() instanceof Iterator                               true
```

```text
   [1].values() ──▶ %ArrayIteratorPrototype% ──┐
   m.entries()  ──▶ %MapIteratorPrototype%   ──┤
   s.values()   ──▶ %SetIteratorPrototype%   ──┤
   'ab'[@@it]() ──▶ %StringIteratorPrototype% ─┼──▶ Iterator.prototype ──▶ Object.prototype ──▶ null
   matchAll()   ──▶ %RegExpStringIteratorPrototype% ┤      (map filter take drop flatMap
   gen()        ──▶ gen.prototype ──▶ %GeneratorPrototype% ┘       reduce toArray forEach some every find)

   { next() {...} } ─────────────────────────────────────────────▶ Object.prototype      <- 헬퍼가 없다
```

- ★★★ **`[1]` 내장 이터레이터 여섯 가지가 전부 한두 단계 위에서 `Iterator.prototype` 을 만난다.**
  제너레이터 객체만 **한 단계 더 깊다** — `gen.prototype -> (Generator proto) -> Iterator.prototype`.
- ★★★ **손으로 만든 `{ next() {...} }` 의 사슬은 `Object.prototype` 하나**다. 그래서 `[2]` 에서 **그것만 `undefined / undefined`** 다.
  ★★ **「이터레이터다」는 프로토콜(19번)의 말이고, 「헬퍼가 있다」는 사슬의 말이다.** 둘은 다른 질문이다.
- ★ **`[3]` `Iterator.prototype` 의 자기 프로퍼티**에 헬퍼 열한 개 · `constructor` · `Symbol.iterator` · `Symbol.toStringTag` 가 있다.
  ★ `Symbol(Symbol.dispose)` 도 보인다 — **이 판(Chrome 151)이 ES2027 쪽 기능까지 들인 것**이고, 이 문서는 그것을 다루지 않는다.
- ★★ **`[4]` `Iterator` 는 함수인데 `new Iterator()` 는 `TypeError 「Abstract class Iterator not directly constructable」`** 이다.
  **`class C extends Iterator` 는 된다** — 하위 클래스로 쓰라고 만든 **추상 클래스**다. 그리고 `[1].values() instanceof Iterator` · `gen() instanceof Iterator` 가 `true` 다.

**손으로 만든 이터레이터에 헬퍼를 달려면 `Iterator.from`** 을 쓴다(출력 전문은 3-answer 의 6번).

- ★★★ **`Iterator.from(bare)` 는 `bare` 가 아니다**(`=== bare` 가 `false`) — **감싼 새 객체**를 주고, 그 객체에는 `map` 이 있다.
- ★★★ **이미 `Iterator.prototype` 을 물려받은 것은 그대로 돌려준다** — `Iterator.from([7, 8].values()) === that iterator` 가 `true`.
- ★★ **이터러블도 받는다** — 배열 · `Symbol.iterator` 를 가진 객체 · **문자열**(`'ab'` 가 `["a","b"]`).
- ★★ **원시값 `42`·`null` 은 부르는 순간 `TypeError 「Iterator.from called on non-object」`** 다.
  ★ **문자열만 원시값 중에 예외**다 — 16판의 `Iterator.from` 은 `GetIteratorFlattenable(O, iterate-string-primitives)` 로 **문자열을 따로 허용**한다.
- ★★★ **`{}` 는 부르는 순간에는 통과한다**(`typeof from({})` 가 `object`) — **`toArray()` 에서야 `TypeError 「undefined is not a function」`** 이다.
  `Symbol.iterator` 가 없으면 **그 객체 자체를 이터레이터로 보고** `next` 를 나중에 부르기 때문이다(같은 `GetIteratorFlattenable` 의 단계).
  ★ **「받아 줬다」가 「이터레이터다」가 아니다** — 틀린 것이 첫 `next` 까지 미뤄진다.
- ★ **감싸지 않고 빌려 쓰는 길도 있다** — `Iterator.prototype.map.call(bare2, x => -x).toArray()` 가 `[-1,-2]` 다(15번의 「메서드는 `this` 만 본다」).

### (5) ★★★ 헬퍼는 원본을 소비한다 — 두 번째는 빈 것

**언제 쓰나** — 헬퍼 사슬을 **변수에 담아 두고 두 번 쓸 때.** 배열 메서드에 익은 손이 가장 많이 틀리는 자리다.

```js
// js20b-21f-consume.web.js
// 헬퍼는 원본을 「소비」하나 -- 같은 헬퍼 · 같은 원본을 두 번 쓰면 무엇이 남나.
const J = JSON.stringify;
console.log("[1] one helper, two toArray() calls");
const m = [1, 2, 3].values().map((x) => x * 2);
console.log("  first  toArray()  " + J(m.toArray()));
console.log("  second toArray()  " + J(m.toArray()));

console.log("");
console.log("[2] the source after a helper has been drained");
const src = [1, 2, 3].values();
const doubled = src.map((x) => x * 2);
console.log("  doubled.toArray()   " + J(doubled.toArray()));
console.log("  src.next()          " + J(src.next()));

console.log("");
console.log("[3] two helpers built on one source, pulled in turn");
const shared = [1, 2, 3, 4, 5, 6].values();
const a = shared.map((x) => "a" + x);
const b = shared.map((x) => "b" + x);
const got = [];
for (let k = 0; k < 4; k++) got.push(String(a.next().value), String(b.next().value));
console.log("  a, b, a, b, ...     " + J(got));

console.log("");
console.log("[4] the array, by contrast");
const arr = [1, 2, 3];
const d = arr.map((x) => x * 2);
console.log("  arr.map twice       " + J(d) + " " + J(arr.map((x) => x * 2)));
console.log("  arr after           " + J(arr));

console.log("");
console.log("[5] h[Symbol.iterator]() === h, and two spreads of h");
const h = [1, 2].values().map((x) => x);
console.log("  h[Symbol.iterator]() === h   " + String(h[Symbol.iterator]() === h));
console.log("  [...h] then [...h]           " + J([...h]) + " " + J([...h]));

console.log("");
console.log("[6] callback arguments, and the methods a helper object has");
console.log("  map((v, i) => v + ':' + i)       " + J([10, 20, 30].values().map((v, i) => v + ":" + i).toArray()));
console.log("  reduce((s, v, i) => s + i, '')   " + J([10, 20, 30].values().reduce((s, v, i) => s + i, "")));
const hh = [1].values().map((x) => x);
console.log("  typeof next / return / throw     " + typeof hh.next + " / " + typeof hh.return + " / " + typeof hh.throw);
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21f-consume.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] one helper, two toArray() calls
  first  toArray()  [2,4,6]
  second toArray()  []

[2] the source after a helper has been drained
  doubled.toArray()   [2,4,6]
  src.next()          {"done":true}

[3] two helpers built on one source, pulled in turn
  a, b, a, b, ...     ["a1","b2","a3","b4","a5","b6","undefined","undefined"]

[4] the array, by contrast
  arr.map twice       [2,4,6] [2,4,6]
  arr after           [1,2,3]

[5] h[Symbol.iterator]() === h, and two spreads of h
  h[Symbol.iterator]() === h   true
  [...h] then [...h]           [1,2] []

[6] callback arguments, and the methods a helper object has
  map((v, i) => v + ':' + i)       ["10:0","20:1","30:2"]
  reduce((s, v, i) => s + i, '')   "012"
  typeof next / return / throw     function / function / undefined
```

- ★★★ **`[1]` 같은 헬퍼에 `toArray()` 를 두 번 부르면 `[2,4,6]` 다음 `[]`** 다. **에러가 아니라 빈 결과**라 조용히 틀린다.
  19번의 「자기 자신을 돌려주는 이터레이터는 두 번째가 `[]`」와 **같은 자리**다 — **`[5]` 가 헬퍼도 `h[Symbol.iterator]() === h` 가 `true` 이고 `[1,2] []` 임을 보인다.**
- ★★★ **`[2]` 헬퍼를 다 돈 뒤 원본에 `next()` 를 부르면 `{"done":true}`** — 헬퍼가 **원본을 끝까지 당겨 버렸다.** 헬퍼는 원본의 **복사본을 만들지 않는다.**
- ★★★ **`[3]` 한 원본 위에 헬퍼 둘을 만들고 번갈아 당기면 `["a1","b2","a3","b4","a5","b6","undefined","undefined"]`** 다.
  `a` 와 `b` 가 **같은 원본에서 번갈아 한 칸씩 가져갔다** — 각자 `1..6` 을 다 받는 것이 아니다.
- ★ **`[4]` 배열은 대조군이다** — `arr.map` 을 두 번 불러도 두 번 다 `[2,4,6]`, 원본도 `[1,2,3]` 그대로다.
- ★ **`[6]` 콜백은 `(값, 번호)` 를 받는다** — `["10:0","20:1","30:2"]`. `reduce` 는 `(누산, 값, 번호)` 라 `"012"` 다. 번호는 **헬퍼마다 0 부터** 센다.

```text
   원본 이터레이터 shared:  1 2 3 4 5 6 | done
                           ▲ ▲ ▲ ▲ ▲ ▲
   a = shared.map("a"+x)   1   3   5          a.next() 가 당긴 칸
   b = shared.map("b"+x)     2   4   6        b.next() 가 당긴 칸
                                        a.next(), b.next() -> undefined (원본이 끝났다)

   ★ 헬퍼는 원본을 붙들고 있을 뿐, 따로 저장하지 않는다. 당기면 원본이 한 칸 나간다.
```

### (6) ★★★ 헬퍼는 원본을 언제 닫나 — 19번의 규칙 위에서

**언제 쓰나** — 원본이 **파일 핸들 · 연결 · 잠금**처럼 `return()` 에서 정리해야 하는 것일 때.
원본 이터레이터를 `Object.create(Iterator.prototype)` 로 만들어 **헬퍼를 달고**, `next`·`return` 에 로그를 심었다. 원본은 값 **다섯**(1\~5)이다.

```js
// js20b-21g-close.web.js
// 원본 이터레이터에 next / return 로그를 심고, 헬퍼와 종단 메서드가 원본의 return() 을 부르는 자리를 찍는다.
const L = [];
function traced(n = 5) {
  let i = 0;
  const it = Object.create(Iterator.prototype);
  it.next = () => { i++; const done = i > n; L.push(done ? "next#" + i + " done" : "next#" + i); return done ? { value: undefined, done: true } : { value: i, done: false }; };
  it.return = () => { L.push("return()"); return { value: undefined, done: true }; };
  return it;
}
const rows = [];
function probe(label, fn) {
  L.length = 0;
  let r;
  try { r = "result " + JSON.stringify(fn()); } catch (e) { r = "caught " + e.constructor.name + " 「" + e.message + "」"; }
  rows.push([label, L.filter((m) => m.startsWith("next#")).length, L.filter((m) => m === "return()").length]);
  console.log(label);
  console.log("    " + (L.join(" | ") || "(nothing)") + "   [" + r + "]");
}
console.log("[1] helpers and terminals over a 5-value source");
probe("take(2).toArray()", () => traced().take(2).toArray());
probe("take(5).toArray()", () => traced().take(5).toArray());
probe("take(9).toArray()", () => traced().take(9).toArray());
probe("drop(2).toArray()", () => traced().drop(2).toArray());
probe("find(x => x === 2)", () => traced().find((x) => x === 2));
probe("some(x => x === 2)", () => traced().some((x) => x === 2));
probe("every(x => x < 2)", () => traced().every((x) => x < 2));
probe("find(x => x === 99)", () => traced().find((x) => x === 99));
probe("forEach(x => {})", () => traced().forEach((x) => {}));
probe("reduce((s, x) => s + x)", () => traced().reduce((s, x) => s + x));
console.log("");
console.log("[2] when a callback throws, or the consumer leaves");
probe("map(throws at 2).toArray()", () => traced().map((x) => { if (x === 2) throw new Error("mapper threw"); return x; }).toArray());
probe("for (x of map(f)) break at 2", () => { for (const x of traced().map((v) => v)) if (x === 2) break; });
probe("const [a] = map(f)", () => { const [a] = traced().map((v) => v); return a; });
probe("flatMap(x => [x, x]).take(3).toArray()", () => traced().flatMap((x) => [x, x]).take(3).toArray());
console.log("");
console.log("[3] summary  (label / source next calls / source return calls)");
for (const [label, n, r] of rows) console.log("  " + label.padEnd(40) + String(n).padStart(2) + "  " + r);
console.log("return() was called in " + rows.filter(([, , r]) => r > 0).length + " of " + rows.length + " probes");
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21g-close.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] helpers and terminals over a 5-value source
take(2).toArray()
    next#1 | next#2 | return()   [result [1,2]]
take(5).toArray()
    next#1 | next#2 | next#3 | next#4 | next#5 | return()   [result [1,2,3,4,5]]
take(9).toArray()
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result [1,2,3,4,5]]
drop(2).toArray()
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result [3,4,5]]
find(x => x === 2)
    next#1 | next#2 | return()   [result 2]
some(x => x === 2)
    next#1 | next#2 | return()   [result true]
every(x => x < 2)
    next#1 | next#2 | return()   [result false]
find(x => x === 99)
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result undefined]
forEach(x => {})
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result undefined]
reduce((s, x) => s + x)
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result 15]

[2] when a callback throws, or the consumer leaves
map(throws at 2).toArray()
    next#1 | next#2 | return()   [caught Error 「mapper threw」]
for (x of map(f)) break at 2
    next#1 | next#2 | return()   [result undefined]
const [a] = map(f)
    next#1 | return()   [result 1]
flatMap(x => [x, x]).take(3).toArray()
    next#1 | next#2 | return()   [result [1,1,2]]

[3] summary  (label / source next calls / source return calls)
  take(2).toArray()                        2  1
  take(5).toArray()                        5  1
  take(9).toArray()                        6  0
  drop(2).toArray()                        6  0
  find(x => x === 2)                       2  1
  some(x => x === 2)                       2  1
  every(x => x < 2)                        2  1
  find(x => x === 99)                      6  0
  forEach(x => {})                         6  0
  reduce((s, x) => s + x)                  6  0
  map(throws at 2).toArray()               2  1
  for (x of map(f)) break at 2             2  1
  const [a] = map(f)                       1  1
  flatMap(x => [x, x]).take(3).toArray()   2  1
return() was called in 9 of 14 probes
```

- ★★★ **`take(2)` 는 `next#1 | next#2 | return()`** — **원본을 두 번 당기고 닫는다.** 세 번째 `next` 는 부르지 않는다.
- ★★★ **`take(5)` 도 `next#1 … next#5 | return()`** 이다 — 값이 **딱 다섯인데도** 여섯째 `next` 로 끝을 확인하지 않고 **닫는다.**
  **`take(9)` 는 `next#6 done` 까지 가고 `return()` 이 없다** — 원본이 먼저 끝났으니 닫을 이유가 없다.
  ★★★ **19번의 `const [a, b, c] = it`(값이 딱 셋인데 닫는다)과 `[a, b, c, d]`(`done` 을 받아 안 닫는다)와 같은 모양이다.**
  **「`done` 을 직접 받았나」가 닫기를 가른다** — 규칙이 하나다.
- ★★ **`drop(2)`·`forEach`·`reduce`·`find(없는 값)` 은 `next#6 done` 까지 가고 `return()` 이 없다.**
  **`find(있는 값)`·`some(참)`·`every(거짓)` 은 답이 나온 자리에서 `return()`** 이다.
- ★★★ **`[2]` 콜백이 던지면 닫고 그 예외를 올린다** — `map(throws at 2)` 가 `next#1 | next#2 | return()` 에 `caught Error 「mapper threw」`.
  ★★ **헬퍼를 `for...of` 로 돌다가 `break` 하거나 `const [a] = …` 로 하나만 받아도 원본까지 닫힌다** —
  소비자가 **헬퍼**의 `return()` 을 부르고, 헬퍼가 그것을 **원본**에 전한다.
- ★★ **`flatMap(x => [x, x]).take(3)` 는 원본을 두 번만 당긴다** — 첫 값에서 `[1, 1]`, 둘째 값에서 `[2, …]` 의 첫 칸을 얻어 셋이 찼다.
- ★ **`[3]` 요약 표**의 마지막 줄 `return() was called in 9 of 14 probes` 는 **스크립트가 센 것**이다.

```text
   원본: 1 2 3 4 5 | done

   take(2)  next#1 next#2 ─────────────────────────▶ return()      2개 채움. 끝 확인 없이 닫는다
   take(5)  next#1 next#2 next#3 next#4 next#5 ────▶ return()      딱 5개여도 여섯째를 안 부르고 닫는다
   take(9)  next#1 ... next#5 next#6(done) ─────────▶ (닫지 않음)   원본이 먼저 끝났다

   ★ 19번과 같은 규칙: done 을 직접 받았으면 닫지 않고, 못 받고 멈추면 닫는다.
```

### (7) ★★ node 에는 헬퍼가 없다 — 같은 질문을 제너레이터에 던졌다(제5의 상태)

**언제 쓰나** — 헬퍼가 없는 판에서 **같은 평가 순서**를 얻고 싶을 때. 그리고 **헬퍼의 로그가 「헬퍼만의 성질」인지 「이터레이터 사슬의 성질」인지** 가를 때.

```js
// js20b-21x-node-absent.js
// 이 판(node)에서 헬퍼를 부르면 어떻게 되나 -- 그리고 제너레이터로 손수 만든 파이프라인은 어떤 로그를 내나.
const L = [];
const mapFn = (x) => { L.push("map(" + x + ")"); return x * 10; };
const keep = (x) => { L.push("filter(" + x + ")"); return x % 20 === 0; };
const src = () => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

console.log("[1] the helper call on this node");
try { src().values().map(mapFn); console.log("  no error"); }
catch (e) { console.log("  " + e.constructor.name + " 「" + e.message + "」"); }
console.log("  typeof globalThis.Iterator  " + typeof globalThis.Iterator);

console.log("");
console.log("[2] a hand-rolled pipeline with generator functions");
function* map(it, f) { for (const x of it) yield f(x); }
function* filter(it, p) { for (const x of it) if (p(x)) yield x; }
function* take(it, n) { if (n <= 0) return; for (const x of it) { yield x; if (--n === 0) return; } }
L.length = 0;
const out = [...take(filter(map(src(), mapFn), keep), 2)];
console.log("  result " + JSON.stringify(out));
console.log("  map calls " + L.filter((m) => m.startsWith("map(")).length + " · filter calls " + L.filter((m) => m.startsWith("filter(")).length);
console.log("  order  " + L.join(" "));
```
```text
===== node20 js20b-21x-node-absent.js (exit=0) =====
[1] the helper call on this node
  TypeError 「src(...).values(...).map is not a function」
  typeof globalThis.Iterator  undefined

[2] a hand-rolled pipeline with generator functions
  result [20,40]
  map calls 4 · filter calls 4
  order  map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)
```

- ★★★ **`[1]` node20 에서 헬퍼 호출은 `TypeError 「src(...).values(...).map is not a function」`** 이다 — 메서드가 **사슬에 없다.**
  ★ **node18 도 한 글자도 같았다** — 이 탐침은 두 판 대조기에서 `identical` 이다.
- ★★★ **`[2]` 제너레이터 함수 셋(`map`·`filter`·`take`)으로 손수 만든 파이프라인의 로그가 Chrome 의 헬퍼판 로그와 한 글자도 같다** —
  `map calls 4 · filter calls 4`, 순서 `map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)`.
  ★★ **「값이 한 칸씩 흐른다」는 헬퍼가 새로 만든 성질이 아니라 이터레이터를 사슬로 이은 것의 성질**이다. 헬퍼는 그것을 **표준 메서드로 붙여 준 것**이다.
- ★ 이것이 **「창을 바꿔 물었다」**(제5의 상태)다 — node 에서 헬퍼 창이 **아예 안 열려서** 같은 질문을 제너레이터 창으로 물었다.
  ★ **바꾼 창이 못 보는 것**도 있다 — 손수 만든 `take` 가 원본을 **언제 닫나**는 이 탐침이 재지 않았다(`return()` 로그를 안 심었다). 닫기 규칙은 동작 (6)의 Chrome 로그만 근거로 쓴다.

```text
   Chrome 151     arr.values().map(f).filter(g).take(2).toArray()      ─┐
                                                                         ├─▶ 같은 로그: map(1) filter(10) map(2) filter(20) ...
   node 18 / 20   [...take(filter(map(arr, f), g), 2)]  (function* 셋) ─┘

   ★ 판별: node 에는 Iterator 가 없다 -> 헬퍼 창이 안 열린다 -> 제너레이터 창으로 같은 질문을 던졌다
```

## 문법 — 형태와 규칙

```text
   원본                         중간 헬퍼 (새 헬퍼 객체를 돌려준다 · 아직 안 돈다)        종단 (값을 당겨 결과를 낸다)
   ────                         ──────────────────────────────────────────────           ─────────────────────────────
   arr.values()                 .map(fn)        .filter(fn)     .take(n)                 .toArray()
   m.entries() · s.values()     .drop(n)        .flatMap(fn)                             .reduce(fn[, init])
   gen()                                                                                 .forEach(fn)
   'str'[Symbol.iterator]()                                                              .some(fn) · .every(fn) · .find(fn)
   Iterator.from(x)                                                                      (또는 for...of · 스프레드 · next())
```

- **원본은 이터레이터**다. 배열 자체에는 헬퍼가 없다 — `arr.map` 은 **배열 메서드**이고, 헬퍼를 쓰려면 `arr.values()` 로 이터레이터를 먼저 얻는다.
- **중간 헬퍼**(`map`·`filter`·`take`·`drop`·`flatMap`)는 **새 헬퍼 객체**를 돌려주고 **그 자리에서는 원본을 당기지 않는다.**
- **종단 메서드**(`toArray`·`reduce`·`forEach`·`some`·`every`·`find`)가 값을 당긴다. `for...of`·스프레드·수동 `next()` 도 같은 일을 한다(헬퍼 객체도 이터러블이다).
- 콜백은 `(값, 번호)` 를 받는다 — 번호는 0 부터 센다. `reduce` 는 `(누산, 값, 번호)`(동작 (5)의 `[6]`).
- `take(n)`·`drop(n)` 의 `n` 은 **숫자로 바꾼 뒤 `NaN` 이거나 음수면 `RangeError`** 다. `"2"` 는 받는다(3-answer 의 5번).
- `flatMap` 의 콜백은 **이터레이터나 이터러블 객체**를 돌려줘야 한다 — **문자열은 거절**한다(어디서 틀리나 (6)).
- `Iterator.from(x)` — 헬퍼가 없는 이터레이터를 감싸거나, 이터러블에서 이터레이터를 얻는다.
- `Iterator.concat(a, b, …)` — **ES2026**. 이터러블을 **차례로 이어** 하나의 이터레이터로 준다(3-answer 의 12번).

## 어디서 틀리나

### (1) ★★★ 헬퍼 사슬을 두 번 쓴다

`const evens = it.filter(isEven)` 을 만들어 `evens.toArray()` 를 두 번 부르면 **두 번째가 `[]`** 다(동작 (5)의 `[1]`).
**에러가 없어서** 로그에서도 안 보인다. 두 번 쓸 것이면 **한 번 `toArray()` 로 배열을 만들어 그것을 쓰거나**, **원본부터 다시 얻는다**(`arr.values()` 를 다시 부른다).

### (2) ★★★ 「헬퍼로 바꾸면 일이 줄어든다」를 모든 사슬에 적용한다

격자의 **안 갈린 칸 5 / 10**(동작 (2)). `reduce` 처럼 전부 봐야 하는 사슬, `find`·`some`·`every` 한 단계짜리는 **호출 수가 같다.**
줄어드는 것은 **「앞의 몇 개만」이 뒤에 붙은 사슬**이다. ★ **「메모리를 아낀다」·「빠르다」는 이 문서가 잰 적이 없다** — 콜백 수만 셌다.

### (3) ★★★ 종단 메서드 없이 부작용을 기대한다

`it.map((x) => { save(x); return x; })` 는 **아무것도 저장하지 않는다** — 로그 0(동작 (1)의 `[2]`, 동작 (3)의 `pulled 0`).
부작용이 목적이면 **`forEach`** 를 쓴다. `map` 은 **값을 바꾸는 단계**이지 **도는 단계**가 아니다.

### (4) ★★ 한 원본에 헬퍼를 여럿 걸고 각자 전부 받는다고 믿는다

두 헬퍼가 **같은 원본을 번갈아 당긴다**(동작 (5)의 `[3]` — `a1 b2 a3 b4 …`). 파이썬의 `itertools.tee` 같은 **갈래 복제는 헬퍼에 없다.**
갈래가 필요하면 **배열로 받아 두고** 거기서 `values()` 를 두 번 얻는다.

### (5) ★★ 손으로 만든 `{ next }` 이터레이터에 `.map` 을 부른다

**`undefined` 라서 `TypeError`** 다 — 헬퍼는 **사슬(`Iterator.prototype`)** 에 있고 프로토콜만 지킨 객체의 사슬에는 없다(동작 (4)).
**`Iterator.from(obj)`** 로 감싸거나, 처음부터 `class … extends Iterator` 로 만든다.

### (6) ★★ `flatMap` 이 문자열을 펼쳐 줄 것이라 믿는다 — 그리고 문구를 믿는다

`flatMap(x => 'ab')` 은 **첫 `next()` 에서 `TypeError 「Iterator.prototype.flatMap called on non-object」`** 다(3-answer 의 5번).
배열의 `flatMap` 과 달리 **헬퍼의 `flatMap` 은 문자열을 거절**한다(명세의 `GetIteratorFlattenable` 이 원시값을 거절한다).
★★★ **문구가 원인을 가리키지 않는다** — `called on non-object` 는 **`flatMap` 을 부른 대상(`this`)이 객체가 아니라는 말처럼 읽히지만**
대상은 멀쩡한 이터레이터이고 **틀린 것은 콜백의 반환값**이다. `flatMap(x => x)`(숫자를 돌려줌)도 **같은 문구**다.
**문구 말고 「어느 시점에 던졌나」 — 만들 때가 아니라 첫 `next()` 에서 — 를 근거로 읽어라**(가이드 규칙 27).

### (7) ★★ 인자 검사가 첫 `next()` 에서 일어난다고 믿는다

`take(-1)`·`drop(-1)`·`map('not a function')` 은 **헬퍼를 만드는 순간** 던지고, 그때 **원본의 `return()` 을 부른다**(3-answer 의 5번 — `source log: return()`).
**원본을 한 칸도 당기지 않았는데 닫는다.** 원본이 파일 핸들이면 **잘못된 인자 하나로 핸들이 닫힌다**는 뜻이다.
반면 `flatMap` 의 반환값 검사는 **값이 와야** 할 수 있으니 첫 `next()` 에서 던진다.

### (8) ★★ node 에서 헬퍼가 없는 것을 「문법 오류」로 읽는다

`TypeError 「… .map is not a function」` 이다 — **파싱은 되고 실행에서** 메서드를 못 찾는다(동작 (7)의 `[1]`).
판을 먼저 확인하라 — **판별 블록의 `ES2025  Iterator (global)` 줄이 `no` 면 헬퍼가 없는 판**이다.

### (9) ★ 배열에 바로 `.take()` 를 부른다

배열에는 **`take` 가 없다** — 헬퍼는 **이터레이터**의 것이다. `arr.values().take(2)` 이거나, 배열이면 그냥 `arr.slice(0, 2)` 다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **중간 헬퍼는 만들 때 원본을 당기지 않고, 헬퍼의 `next()` 가 불릴 때 필요한 만큼만 당긴다** — 헬퍼의 본문이 **제너레이터처럼 멈췄다 도는 추상 클로저**로 정의돼 있다.
- ★★★ **콜백 호출 순서가 값마다 번갈아 가는 것** — 위의 결과다. 로그 `map(1) filter(10) map(2) …` 은 엔진이 고른 것이 아니다.
- ★★★ **`take` 가 한도를 채우면 원본을 `IteratorClose` 하는 것** · **콜백이 던지면 원본을 닫는 것** · **`find`/`some`/`every` 가 답이 나오면 닫는 것**.
- ★★ **인자 검사가 헬퍼를 만들 때 일어나고, 실패하면 원본을 닫는 것** — 16판 `take` 의 단계에 `IteratorClose(iterated, error)` 가 그대로 있다.
- ★★ **헬퍼가 `Iterator.prototype` 에 있고, 내장 이터레이터들의 사슬이 거기를 지나는 것** · **`new Iterator()` 가 `TypeError` 인 것**.
- ★★ **`Iterator.from` 이 이미 `Iterator.prototype` 을 물려받은 것은 그대로 돌려주고, 아니면 감싸는 것** · **문자열을 받는 것**.
- ★ **예외의 종류** — `TypeError`·`RangeError`.

### 엔진(V8) 구현 · 이 판의 관찰

- ★★ **예외 문구 전부** — `-1 must be positive` · `Abstract class Iterator not directly constructable` · `Iterator.from called on non-object` ·
  `Iterator.prototype.flatMap called on non-object` · `Reduce of a done iterator with no initial value` · `string "not a function" is not a function`.
- ★★ **`flatMap` 의 문구가 원인과 어긋나는 것** — V8 의 표현이다. 다른 엔진은 다르게 말할 수 있다.
- ★ **Chrome 151 이 `Iterator.prototype[Symbol.dispose]`(ES2027 쪽)까지 들인 것** — 이 판의 사정이다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★ **node 18/20 에 헬퍼가 없는 것** — 그 판들이 들인 V8(10.2 · 11.3)이 ES2025 이전의 것이라서다(판별 블록). **언어의 성질이 아니다.**
- ★ 탐침 페이지의 `console.log` 가로채기 · `--dump-dom` — 호스트(브라우저)의 기능이다.

### 그래서 이렇게 적으면 틀린다

| 틀린 문장 | 왜 틀리나 | 고친 문장 |
|---|---|---|
| 「헬퍼는 메모리를 아낀다」 | 이 문서는 메모리를 **재지 않았다** | 「헬퍼 사슬은 단계마다 배열을 만들지 않고, 콜백을 필요한 만큼만 부른다(호출 수 실측)」 |
| 「배열 메서드는 언제나 끝까지 돈다」 | `find`·`some`·`every` 는 배열도 도중에 멈춘다(격자 `4 / 4`) | 「배열 메서드 사슬은 **단계마다** 원본 전체를 돈다」 |
| 「헬퍼로 바꾸면 호출이 준다」 | 격자에서 **5 / 10 만** 갈렸다 | 「**앞의 몇 개만**이 뒤에 붙은 사슬에서 준다」 |
| 「JS 에는 헬퍼가 없다」 | **판의 사정**이다 — Chrome 151 에는 있다 | 「node 18/20 에는 없다(ES2025 이전 판)」 |
| 「`flatMap` 이 non-object 에서 불렸다」 | 문구가 원인과 다르다 — 틀린 것은 **콜백의 반환값** | 「`flatMap` 의 콜백이 문자열·숫자를 돌려주면 첫 `next()` 에서 `TypeError`」 |

## 언제 쓰고 언제 안 쓰나

- **쓴다** — 원본이 **이터레이터**(제너레이터 · `Map` 의 `entries()` · 줄 단위 입력)이고, 사슬 끝에 **「앞의 몇 개만」·「처음 맞는 것」** 이 있을 때.
  원본에 **끝이 없을 때**는 사실상 이것뿐이다(배열로는 시작을 못 한다).
- **쓴다** — `Map`·`Set` 을 **배열로 안 바꾸고** 거를 때 — `m.entries().filter(…).map(…)` (배열판은 `[...m].filter(…)` 로 **배열부터 만든다**).
- **안 쓴다** — 결과를 **두 번 이상** 쓸 것이면 한 번 `toArray()` 해서 배열로 들고 간다(어디서 틀리나 (1)).
- **안 쓴다** — **node 18/20 을 지원해야 하는 코드.** 그 판에는 없다. 제너레이터 함수로 손수 만든 파이프라인이 같은 평가 순서를 준다(동작 (7)).
- **안 쓴다** — `reduce` 처럼 **전부 봐야 하는** 사슬을 「헬퍼라서 가볍다」는 이유로 고르지 않는다 — 호출 수가 같다(격자).
- ★ **판단 근거는 「몇 번 불리나」다** — 시간·메모리로 고르고 싶으면 **그 코드에서 직접 재라.** 이 문서는 그 근거를 주지 않는다.

## 핵심 문장

1. ★★★ **배열 메서드 사슬은 단계마다 원본 전체를 돌아 새 배열을 만들고, 헬퍼 사슬은 값 하나를 끝까지 흘려보낸 뒤 다음 값을 당긴다** — 결과는 같고 **일한 양과 순서**가 다르다(`10 / 4`).
2. ★★★ **헬퍼는 종단 메서드가 당길 때만 돈다** — 사슬을 만든 것만으로는 콜백이 0번이다.
3. ★★★ **호출 수가 갈리는 것은 「앞의 몇 개만」이 뒤에 붙은 사슬뿐이다** — 격자 `5 / 10`. `reduce`·한 단계짜리 `find` 는 같다.
4. ★★★ **헬퍼는 원본을 소비하고 복사하지 않는다** — 두 번째 `toArray()` 는 `[]`, 한 원본의 두 헬퍼는 번갈아 가져간다.
5. ★★ **헬퍼가 원본을 닫는 규칙은 19번과 같다** — `done` 을 직접 받았으면 안 닫고, 못 받고 멈추면(한도·답·예외·`break`) 닫는다. **인자가 틀려도 닫는다.**

## 관련 자료

- [20 — 제너레이터](../20-generators/2-summary.md) — ★ **그쪽은 `yield` 로 값을 만드는 쪽의 흐름까지, 여기는 만들어진 이터레이터 위에 사슬을 거는 것부터.** 동작 (7)의 손수 만든 파이프라인이 두 편의 이음매다.
- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — ★ **그쪽은 `return()` 이 언제 불리나의 규칙까지(소비자 17가지), 여기는 헬퍼가 그 규칙으로 원본을 언제 닫나부터.**
- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — ★ **그쪽은 조회가 사슬을 타는 규칙까지, 여기는 그 규칙이 「헬퍼가 붙나」를 정한다는 것부터.**
- [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) — `entries()`·`values()` 가 여기의 원본이다. 컬렉션 자체는 그쪽.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **15번**(제너레이터 표현식과 지연 평가) · **16번**(이터레이터 프로토콜) · **44번**(`itertools`) —
  ★★ **파이썬은 이 지연 파이프라인을 언어 초기부터 들고 있었다** — 제너레이터 표현식 `(f(x) for x in it if g(x))` 과 `itertools.islice` 가 여기의 `map`·`filter`·`take` 자리다.
  JS 는 그 자리를 **ES2025 에 와서 메서드 사슬로** 채웠다. ★ 파이썬에는 **갈래 복제 `itertools.tee`** 가 있고 JS 헬퍼에는 없다(어디서 틀리나 (4)). ★ 이 문서는 파이썬 쪽을 **돌리지 않았다** — 그쪽 편의 실측을 인용할 자리다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **36번**(`Iterator` 와 어댑터·게으름·`collect`) — 어댑터 사슬이 **최종 소비 전엔 아무 일도 안 한다**는 같은 계약. `collect` 가 여기의 `toArray` 자리다.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **47번**(`Sequence`) — Kotlin 은 컬렉션 연산이 **기본 즉시**이고 `asSequence()` 로 **명시적으로 전환**한다. JS 의 `arr.values()` 가 그 전환 자리다.
- [ECMA-262 2025](https://262.ecma-international.org/16.0/) · [ECMA-262 2026](https://262.ecma-international.org/17.0/) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md)

## 용어 풀이

- **이터레이터 헬퍼** — `Iterator.prototype` 의 메서드 열한 개(`map`·`filter`·`take`·`drop`·`flatMap`·`reduce`·`toArray`·`forEach`·`some`·`every`·`find`). ES2025.
- **중간 헬퍼** — 새 헬퍼 객체를 돌려주고 그 자리에서는 원본을 안 당기는 것(`map`·`filter`·`take`·`drop`·`flatMap`).
- **종단 메서드** — 값을 당겨 결과를 내는 것(`toArray`·`reduce`·`forEach`·`some`·`every`·`find`). 이 문서의 말이다.
- **헬퍼 객체** — 중간 헬퍼가 돌려주는 이터레이터. 원본을 붙들고 있고, 자기 자신을 이터레이터로 돌려준다.
- **원본(underlying iterator)** — 헬퍼가 값을 당겨 오는 이터레이터. 명세는 `iterated` 라고 부른다.
- **소비** — 이터레이터에서 값을 꺼내 **되돌릴 수 없게** 나아가는 것.
- **`IteratorClose`** — 원본의 `return()` 을 찾아 부르는 명세의 추상 연산(19번).
- **`Iterator.from`** — 이터레이터·이터러블·문자열을 받아 헬퍼가 붙은 이터레이터를 돌려주는 정적 메서드.
- **`Iterator.concat`** — 이터러블 여럿을 차례로 잇는 정적 메서드. ES2026.
- **추상 클래스** — 직접 `new` 할 수 없고 상속해서 쓰라고 만든 클래스. `Iterator` 가 그렇다.
- **지연 평가** — 값이 필요해질 때 계산하는 것.
- **판별 블록** — 기능이 판마다 있는지를 같은 스크립트로 물어 찍은 블록(`js20b-versions.sh`).

## 더 들어가면

- ★ **헬퍼 객체의 메서드** — `typeof next / return / throw` 가 `function / function / undefined` 다(동작 (5)의 `[6]`). 자기 `return()` 을 받으면 원본에 전한다(동작 (6)의 `break` 줄).
  **`throw()` 는 없다** — 20번의 제너레이터 객체와 다른 점이다. 헬퍼는 **바깥에서 값을 밀어 넣는 통로가 없는** 한 방향 사슬이다.
- ★ **`Iterator.concat`** — 인자를 **이터러블로만** 받고 이터레이터 프로토콜만 가진 `{ next }` 는 거절한다. 각 인자의 `Symbol.iterator` 는 **그 차례가 올 때** 부른다(3-answer 의 12번). ES2026.
- ★ **비동기 쪽** — `AsyncIterator.prototype` 의 헬퍼는 ES2025 에 **없다**(finished proposals 의 「Sync Iterator helpers」 가 그 이름대로 동기만이다). 목록의 **40번 주제**의 몫이다.
- ★ **`Iterator.prototype[Symbol.dispose]`** — `using` 선언과 함께 쓰는 자원 정리 규약. Chrome 151 에 있고 finished proposals 에서 2027 이다. 이 문서는 다루지 않는다.
