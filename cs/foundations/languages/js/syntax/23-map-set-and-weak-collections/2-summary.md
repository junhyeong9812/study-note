# js/syntax/23 — `Map`·`Set` 과 약한 컬렉션: 「키는 `-0` 을 `+0` 으로 접은 뒤 같은 값으로 찾고, 약한 쪽은 수명을 들여다볼 창을 아예 안 준다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 「두 값이 같은 키인가」는 **비교 자리마다 답이 다르다** — `Map` 키 · `Set` · `===` · `==` · `Object.is` · 객체 키 · `includes` · `indexOf`.
> 규칙을 외워서 맞히는 자리가 아니라 **값의 짝 여덟 개를 여덟 자리에 전부 들이대 세는** 자리다.
> 그래서 동작 (1)의 격자가 이 문서의 중심이고, 마지막 줄의 「갈린 칸 N / M」을 **스크립트가 직접 센다.**
> ★★ 약한 컬렉션 쪽은 창이 바뀐다 — **값으로는 수명이 안 보이므로** `gc()` 를 부르고 `FinalizationRegistry` 콜백이 **불렸나**를 판마다 센다(동작 (5)).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안 — Keyed Collections](https://tc39.es/ecma262/multipage/keyed-collections.html) —
>   `CanonicalizeKeyedCollectionKey` · `Map.prototype.set` · `Map.prototype.getOrInsertComputed` · `GetSetRecord` · `Set.prototype.intersection` · `WeakMap` 절 머리말
> - [ECMA-262 최신 초안 — Executable Code and Execution Contexts](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html) —
>   「Processing Model of WeakRef and FinalizationRegistry Targets」(Objectives · Liveness · Execution) · `ClearKeptObjects` · `AddToKeptObjects` · `CanBeHeldWeakly`
> - [ECMA-262 최신 초안 — Managing Memory](https://tc39.es/ecma262/multipage/managing-memory.html) — `WeakRef` · `WeakRefDeref` · `FinalizationRegistry`
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(WeakRefs 2021 · Symbols as WeakMap keys 2023 · New Set methods 2025 · Upsert 2026)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 값·호출 로그·예외 타입과 메시지는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★★ **집합 연산(ES2025)과 Upsert(ES2026)는 두 node 판에 없다**(아래 판별 블록). 그 두 탐침은 **Google Chrome 151 을 헤드리스로** 돌렸다 —
> 배너가 `google-chrome --headless --dump-dom` 으로 시작하는 블록이 그것이다. 페이지는 `console.log` 를 가로채 줄을 모은다(`js20b-page.html`).
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★ **이 문서는 BMP 밖 글자를 한 글자도 싣지 않는다.**
>
> **버전** — 이 주제는 **네 판에 걸쳐 들어왔다.** 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `Map` · `Set` · `WeakMap` · `WeakSet` · 삽입 순서 · SameValueZero 비교 | **ES2015** | 세 판 다 있다 |
> | `WeakRef` · `FinalizationRegistry` | **ES2021** | 세 판 다 있다 |
> | 심볼을 약한 키로(Symbols as WeakMap keys) | **ES2023** | ★ **node 18 에 없고** node 20 · Chrome 에 있다 — 동작 (4) |
> | 집합 연산 일곱 개(`union` · `intersection` · `difference` · `symmetricDifference` · `isSubsetOf` · `isSupersetOf` · `isDisjointFrom`) | **ES2025** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
> | Upsert(`getOrInsert` · `getOrInsertComputed`, `Map` 과 `WeakMap`) | **ES2026** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 값의 짝 **8개** × 비교 자리 **8곳**. `Map` 키 열을 기준으로 **갈린 칸을 스크립트가 센다**(동작 (1)) · 약한 키 후보 **11개**(동작 (4)) · 수명 조건 **6개 × 20판**(동작 (5)) |
> | ★★★ **① 추상 연산에 로그 심기** | 집합 연산이 인자의 `size` · `has` · `keys` 중 **무엇을 부르나**(동작 (7)) · `getOrInsertComputed` 가 콜백을 **언제 부르나**(동작 (8)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 약한 키 거부 문구 · 집합 연산 인자 검사 · ★ **`getOrInsertComputed` 의 문구가 사실과 다른 자리**(동작 (8)의 `[4]`) |
> | ★★ **⑤ 두 판 대조기** | 이 주제에서 갈린 탐침은 **`js20b-23d-weak-keys.js` 하나** — 심볼 키(ES2023)와 `WeakRef` 문구다 |
> | ★★★ **창을 바꿔 물었다**(제5의 상태) | `WeakMap` 에는 **키를 꺼내 볼 창이 하나도 없다**(`size`·순회 없음 — 동작 (4)의 `[3]`). 그래서 「이 키가 아직 살아 있나」는 **`FinalizationRegistry` 콜백과 `WeakRef.deref()`** 로 바꿔 물었다. ★ 바꾼 창이 못 보는 것 — **`WeakMap` 안의 항목 자체**는 끝까지 못 본다. 대상 객체가 수거됐다는 것까지만 본다 |
> | ★ **부적용 — ③ 브랜드 태그** | 「이것이 `Map` 인가」는 이 주제의 질문이 아니다. 집합 연산의 인자조차 **브랜드가 아니라 `size`·`has`·`keys` 세 프로퍼티**로 판정된다(동작 (7)의 `[2]` — `Map` 이 인자로 통과한다). **잴 것이 없다** |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 가 한 줄도 없다. 전부 런타임 의미다 — **잴 것이 없다** |
> | ★ **안 쟀다 — 성능** | 「`Map` 이 객체보다 빠르다」·「`WeakMap` 이 메모리를 아낀다」를 **한 줄도 쓰지 않는다.** 시간도 바이트도 안 쟀다 |
> | ★ **안 돌렸다 — 브라우저의 GC** | `FinalizationRegistry` 는 **node 에서만** 돌렸다. 페이지 하네스가 `setTimeout` 뒤의 출력을 못 받는다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **`FinalizationRegistry` 콜백이 「언제」 도나** — gc() 뒤 몇 번째 매크로태스크인가 · gc() 없이 도나. **명세가 묶지 않는다.** `js20b-23f-timing-gc.js` 한 블록에 몰아 두고 그 블록의 `ticks:` 줄을 흔들리는 칸으로 선언한다 | ★★★ **격자의 y/n 과 「갈린 칸 N / M」** · `Map`/`Set` 의 **삽입 순서** · 집합 연산 **결과의 순서** · 인자 로그의 **순서와 개수** · 예외의 **종류** |
> | 예외 **문구** — ★ **이 주제 안에서 판마다 갈렸다**(`WeakRef: target must be an object` 대 `WeakRef: invalid target`) | ★★ **이 판에서** `gc()` 뒤 콜백이 **불렸나**(「20판 중 몇」) — 명세 보장이 아니라 **판의 관찰**이다. 흔들리지는 않았지만(재대조 동일) 성질의 근거로는 안 쓴다 |
> | — | `KeptAlive` — **같은 잡 안에서는 `deref()` 가 살아 있다**(명세 보장, 20/20) |
>
> **선행** — [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md)(직접 선행 — 심볼이 약한 키가 되는 조건) ·
> [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ `Map`·`Set` 의 삽입 순서와 **순회 중 변경**은 거기서 이미 쟀다) ·
> [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md)(★★ 정수 키가 앞서는 열거 순서 · `__proto__` 다섯 형태) ·
> [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md)(`==` 열) · [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md)(`NaN` · `-0`).
> **이어지는 곳** — 목록의 **24번 주제** 「배열 변형 메서드」 · 목록의 **25번 주제** 「배열 비변형·복사 메서드」.
>
> ★★ **경계 — 해시 테이블의 원리는 [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/2-summary.md) 이 정본이다.**
> 그쪽은 **버킷·충돌 처리·재해싱·`LinkedHashMap` 이 삽입 순서를 옆 리스트로 기억하는 법**까지, 여기는 **JS 가 그 위에 약속한 관찰 가능한 의미**(무엇이 같은 키인가 · 어떤 순서로 나오나)부터다.
> ★★ **경계 — 순회 프로토콜 자체는 19번이 정본이다.** 여기서는 `Map`·`Set` 이 **무엇을 같은 원소로 치나**만 본다.
> ★ **경계 — 심볼 자체(설명 · 등록 · 잘 알려진 심볼)는 22번이 정본이다.** 여기서는 **어떤 심볼이 약한 키가 되나**만 본다.

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

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 이 주제에서 갈린 것은 `js20b-23d-weak-keys.js` 하나이고, 갈린 줄의 전문은 [3-answer.md](3-answer.md) 의 12번에 있다.

`identical 18  ·  differs 6  ·  total 24`

브라우저 탐침을 돌리는 페이지(`js20b-page.html`)의 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

## 한눈에 — 쉽게 말하면

**`Map` 은 「이름표가 아니라 물건 자체를 붙잡는 보관함」** 이다.
평범한 객체는 맡긴 물건에 **이름표(문자열)를 써 붙여** 그 글자로 칸을 찾는다 — 그래서 서로 다른 두 사람이 **같은 글자**를 쓰면 한 칸이 된다.
`Map` 은 물건을 **그대로** 붙잡고, 「같은 물건인가」를 **한 가지 규칙(SameValueZero)** 으로만 묻는다.

- ★★★ **숫자 `NaN` 은 여럿 맡겨도 한 칸이다.** `===` 로는 자기 자신과도 다른데 `Map` 은 같다고 친다.
- ★★★ **`-0` 을 맡기면 `+0` 이 들어간다.** 보관함이 입구에서 부호를 지운다.
- ★★ **모양이 같아도 다른 물건이면 다른 칸이다.** `{ a: 1 }` 두 개는 두 칸이다.
- ★★ **`WeakMap` 은 「주인이 떠나면 저절로 비는 칸」** 이다. 대신 **칸 목록을 보여 주지 않는다** — 보여 주면 「주인이 언제 떠났나」가 새어 나가기 때문이다.

```text
   평범한 객체 o                          Map m
   ------------                          -----
   o[key] = v                            m.set(key, v)
     key 를 글자로 바꾼다                   -0 이면 +0 으로 접는다
       {a:1}      -> "[object Object]"       {a:1} 은 {a:1} 그대로
       1          -> "1"                     1     은 1     그대로
       NaN        -> "NaN"                   NaN   은 NaN   그대로
     그 글자로 칸을 찾는다                  SameValue 로 칸을 찾는다
                                             (NaN 은 NaN 과 같다 · 객체는 정체로)

   {a:1} 두 개 -> 한 칸("[object Object]")     {a:1} 두 개 -> 두 칸
   1 과 "1"    -> 한 칸("1")                    1 과 "1"    -> 두 칸
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 이름표를 써 붙이는 보관함 | 평범한 객체 — 키를 `ToPropertyKey` 로 문자열(또는 심볼)로 바꾼다 | 격자의 「object key」 열 |
| 물건을 그대로 붙잡는 보관함 | `Map` · `Set` | 격자의 「Map key」·「Set」 열 |
| 입구에서 부호를 지우는 것 | `CanonicalizeKeyedCollectionKey` — `-0` 을 `+0` 으로 | 꺼낸 키에 `Object.is(k, -0)` |
| 「같은 물건인가」 규칙 | 키를 접은 뒤의 **SameValue** — 결과적으로 **SameValueZero** | `NaN` 행 · `0, -0` 행 |
| 넣은 순서대로 늘어선 칸 | `[[MapData]]` 리스트 — 삽입 순서 | 19번 동작 (5) · 동작 (3)의 `[6]` |
| 주인이 떠나면 비는 칸 | `WeakMap` 키 — 다른 곳에서 안 붙잡히면 수거될 **수 있다** | `FinalizationRegistry` 콜백 |
| 칸 목록을 안 보여 주는 것 | `WeakMap` 에 `size` · `keys` · 순회가 없다 | 동작 (4)의 `[3]` |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**객체를 키로 쓰려고 `{}` 에 넣었더니 전부 `"[object Object]"` 한 칸에 덮어쓰였다**」와
「**캐시에 넣은 DOM 노드가 화면에서 지워진 뒤에도 메모리에 남았다**」가 그것이다.
앞엣것은 **이름표 보관함에 물건을 맡긴** 것이고, 뒤엣것은 **보통 `Map` 이 주인 대신 물건을 붙잡고 있는** 것이다(동작 (5)의 「key of a Map」 행).

> **SameValueZero** — `NaN` 은 `NaN` 과 같고, `+0` 과 `-0` 도 같다고 보는 비교. 나머지는 `===` 와 같다.\
> 예: `new Set([NaN, NaN]).size` 가 1.

> **SameValue** — `Object.is` 의 비교. SameValueZero 와 **`+0`/`-0` 에서만** 다르다(둘을 다르다고 본다).\
> 예: `Object.is(0, -0)` 이 `false`.

> **약한 참조(weak reference)** — 대상이 **수거되는 것을 막지 않는** 참조. 다른 곳에서 강하게 붙잡히지 않으면 GC 가 대상을 거둘 수 있다.\
> 예: `WeakMap` 의 키 · `WeakRef` 의 대상.

## 이 주제가 답하려는 질문

1. **「두 값이 같은 키인가」는 비교 자리마다 어떻게 다르고**, `Map` 은 그중 어느 규칙을 쓰나?
2. **`Map` 과 평범한 객체를 무엇으로 고르나** — 키 타입 · 크기 · 물려받은 이름 · `"__proto__"` · JSON 에서 각각 무엇이 갈리나?
3. **`WeakMap` 의 「약하다」는 무엇을 보장하고 무엇을 보장하지 않나** — 그리고 왜 들여다볼 창이 없나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 값의 짝 여덟 개 × 비교 자리 여덟 곳 — 이 주제의 본체

**언제 쓰나** — 「이 두 값을 `Map`/`Set` 이 같은 것으로 치나」를 물을 때 · `indexOf` 를 `includes` 로 바꿔도 되나를 물을 때.
★★★ 규칙을 문장으로 외우면 **`NaN` 과 `-0` 두 행**에서 반드시 틀린다. 그래서 전부 들이댔다.

```js
// js20b-23a-key-equality-grid.js
// 두 값 a, b 를 「같은 것」으로 보나 -- 비교 자리 여덟 곳 x 값의 짝 여덟 개.
// 칸마다 y(같다고 본다) / n(다르다고 본다) 를 찍는다. 기준 열은 Map key.
const shape1 = { a: 1 };
const shape2 = { a: 1 };
const pairs = [
  ["NaN, NaN", NaN, NaN],
  ["0, -0", 0, -0],
  ["'1', 1", "1", 1],
  ["1, 1.0", 1, 1.0],
  ["true, 1", true, 1],
  ["null, undefined", null, undefined],
  ["{a:1}, {a:1}  (two objects)", shape1, shape2],
  ["o, o  (one object)", shape1, shape1],
];
const cols = [
  ["Map key", (a, b) => new Map([[a, "x"]]).has(b)],
  ["Set", (a, b) => new Set([a, b]).size === 1],
  ["===", (a, b) => a === b],
  ["==", (a, b) => a == b],
  ["Object.is", (a, b) => Object.is(a, b)],
  ["object key", (a, b) => { const o = {}; o[a] = "x"; return Object.hasOwn(o, b); }],
  ["includes", (a, b) => [a].includes(b)],
  ["indexOf", (a, b) => [a].indexOf(b) !== -1],
];
const W = 30;
console.log("[1] the grid  (y = treated as the same, n = treated as different)");
console.log(("".padEnd(W) + cols.map(([n]) => n.padEnd(11)).join("")).trimEnd());
let cells = 0, apart = 0;
const perCol = cols.map(() => 0);
for (const [label, a, b] of pairs) {
  const ans = cols.map(([, f]) => (f(a, b) ? "y" : "n"));
  ans.forEach((v, i) => { if (i > 0) { cells++; if (v !== ans[0]) { apart++; perCol[i]++; } } });
  console.log((label.padEnd(W) + ans.map((v) => v.padEnd(11)).join("")).trimEnd());
}
console.log("");
console.log("[2] per column, cells whose answer differs from the Map-key column:");
cols.forEach(([n], i) => { if (i > 0) console.log("  " + n.padEnd(12) + perCol[i] + " / " + pairs.length); });
console.log("cells whose answer differs from the Map-key column: " + apart + " / " + cells);

```
```text
===== node20 js20b-23a-key-equality-grid.js (exit=0) =====
[1] the grid  (y = treated as the same, n = treated as different)
                              Map key    Set        ===        ==         Object.is  object key includes   indexOf
NaN, NaN                      y          y          n          n          y          y          y          n
0, -0                         y          y          y          y          n          y          y          y
'1', 1                        n          n          n          y          n          y          n          n
1, 1.0                        y          y          y          y          y          y          y          y
true, 1                       n          n          n          y          n          n          n          n
null, undefined               n          n          n          y          n          n          n          n
{a:1}, {a:1}  (two objects)   n          n          n          n          n          y          n          n
o, o  (one object)            y          y          y          y          y          y          y          y

[2] per column, cells whose answer differs from the Map-key column:
  Set         0 / 8
  ===         1 / 8
  ==          4 / 8
  Object.is   1 / 8
  object key  2 / 8
  includes    0 / 8
  indexOf     1 / 8
cells whose answer differs from the Map-key column: 9 / 56
```

```text
   비교 규칙의 집안 -- 네 가족이 두 행(NaN · 0/-0)에서만 서로 갈린다

                      NaN, NaN      0, -0
                      --------      -----
   SameValue          같다          다르다      Object.is
   SameValueZero      같다          같다        Map 키 · Set · includes
   ===  (IsStrictly)  다르다        같다        === · indexOf
   ==   (IsLoosely)   다르다        같다        + 타입을 가로질러 강제 변환 ('1'==1, true==1, null==undefined)

   객체 키 열만 집안이 다르다 -- 비교가 아니라 「글자로 바꾼 뒤 글자가 같나」
       NaN -> "NaN" · 0 과 -0 -> "0" · '1' 과 1 -> "1" · {a:1} -> "[object Object]"
```

- ★★★ **집계 줄 — `cells whose answer differs from the Map-key column: 9 / 56`.** 여덟 자리 중 **`Map` 키와 완전히 같은 답을 낸 것은 `Set` 과 `includes` 둘**(각 `0 / 8`)이다.
  이 셋이 **SameValueZero 한 가족**이다.
- ★★★ **`NaN, NaN` 행** — `Map` 키 · `Set` · `Object.is` · `includes` 는 **y**, `===` · `==` · `indexOf` 는 **n**.
  ★ **`indexOf` 와 `includes` 가 여기서 갈린다** — `[NaN].indexOf(NaN)` 은 못 찾고 `[NaN].includes(NaN)` 은 찾는다. 이름이 비슷한 두 메서드가 **다른 비교 규칙**을 쓴다.
- ★★★ **`0, -0` 행** — 여덟 자리 중 **`Object.is` 하나만 n** 이다. SameValueZero 의 「Zero」가 바로 이 행이다.
- ★★ **`'1', 1` 행** — y 는 **`==` 와 객체 키** 둘이다. 이유가 다르다 — `==` 는 **숫자로 강제 변환**해서, 객체 키는 **둘 다 `"1"` 이라는 글자가 돼서** 같다.
- ★★ **`{a:1}, {a:1}` 행** — **객체 키 하나만 y** 다. 두 객체가 다 `"[object Object]"` 로 바뀌어 한 칸을 쓴다. 나머지 일곱 자리는 전부 **정체(identity)** 로 본다.
- ★ **`1, 1.0` 행이 전부 y 인 것** — JS 에서 `1` 과 `1.0` 은 **처음부터 같은 Number 값**이다. 비교할 거리가 없다. 파이썬과 대비는 동작 (9).
- ★ **`true, 1` · `null, undefined` 행** — **`==` 만 y** 다. 강제 변환 규칙은 [02번](../02-coercion-and-loose-equality/2-summary.md)이 정본이다.

### (2) ★★★ `-0` 을 넣으면 무엇이 저장되나 — 입구에서 접힌다

**언제 쓰나** — 계산 결과(`-0` 이 나올 수 있는 곱셈·반올림)를 키로 쓰고, 꺼낸 키를 다시 부호에 민감한 곳에 넘길 때.

```text
   m.set(-0, "minus zero")

   ① CanonicalizeKeyedCollectionKey(-0)  ->  +0          (입구에서 접는다)
   ② [[MapData]] 에서 SameValue(entry.key, +0) 인 칸을 찾는다
   ③ 없으면 { key: +0, value: "minus zero" } 를 끝에 붙인다

   그래서
     [...m.keys()][0]           ->  +0   (Object.is(k, -0) 은 false)
     m.get(0) · m.get(-0)       ->  둘 다 "minus zero"    (get 도 먼저 접는다)
```

- ★★★ **꺼낸 키는 `-0` 이 아니라 `+0` 이다** — [3-answer.md](3-answer.md) 2번의 블록이 `Object.is(key, -0)` **false**, `Object.is(key, +0)` **true** 를 찍었다. `Set` 도 같다.
- ★★ **최신 초안은 `Map.prototype.set` 을 「SameValueZero 로 비교」라고 적지 않는다** — **먼저 `-0` 을 `+0` 으로 접고 그다음 SameValue 로 찾는다.**
  관찰되는 결과는 SameValueZero 와 같다. 다만 **「저장되는 키가 바뀐다」는 사실은 이 표현에서만 보인다** — 비교 규칙만 외우면 놓친다.
- ★ **`NaN` 을 네 가지로 만들어 넣어도 한 칸**이다(`NaN` · `0/0` · `Number('x')` · `Math.sqrt(-1)` → `size` 1, 한 키에 4번 누적). 같은 블록에 있다.

### (3) ★★ `Map` 과 평범한 객체 — 같은 일을 시켜 보면

**언제 쓰나** — 「사전(dictionary)」이 필요할 때 둘 중 무엇을 쓸지 고를 때.

```js
// js20b-23c-map-vs-object.js
// 같은 일을 Map 과 평범한 객체에 시킨다 -- 키 타입 · 크기 · 물려받은 이름 · "__proto__" · JSON.
const row = (label, v) => console.log("  " + label.padEnd(58) + v);
const J = JSON.stringify;

console.log("[1] two different objects as keys");
const u1 = { id: 1 }, u2 = { id: 2 };
const om = {}; om[u1] = "first"; om[u2] = "second";
const mm = new Map([[u1, "first"], [u2, "second"]]);
row("object: Object.keys(om)", J(Object.keys(om)));
row("object: om[u1]", om[u1]);
row("Map:    mm.size / mm.get(u1) / mm.get(u2)", mm.size + " / " + mm.get(u1) + " / " + mm.get(u2));
row("Map:    mm.get({ id: 1 })", String(mm.get({ id: 1 })));

console.log("");
console.log("[2] the size of each");
const o3 = { a: 1, b: 2, c: 3 };
const m3 = new Map(Object.entries(o3));
row("object: o3.size", String(o3.size));
row("object: Object.keys(o3).length", Object.keys(o3).length);
row("Map:    m3.size", m3.size);

console.log("");
console.log("[3] names that come from Object.prototype");
const counts = {};
const cm = new Map();
for (const w of ["toString", "constructor", "hasOwnProperty"]) {
  row("object: '" + w + "' in {}  /  typeof {}['" + w + "']", String(w in counts) + "  /  " + typeof counts[w]);
  row("Map:    new Map().has('" + w + "')", cm.has(w));
}
const tally = {};
for (const w of ["a", "constructor", "a"]) tally[w] = (tally[w] || 0) + 1;
row("object: tally of a, constructor, a", J(tally));
const tm = new Map();
for (const w of ["a", "constructor", "a"]) tm.set(w, (tm.get(w) || 0) + 1);
row("Map:    tally of a, constructor, a", J([...tm]));

console.log("");
console.log("[4] the string key \"__proto__\"");
const po = {};
po["__proto__"] = "plain string";
row("object: after po['__proto__'] = 'plain string'", "keys " + J(Object.keys(po)) + "  typeof po.__proto__ " + typeof po.__proto__);
const po2 = {};
po2["__proto__"] = { injected: true };
row("object: after po2['__proto__'] = { injected: true }", "keys " + J(Object.keys(po2)) + "  po2.injected " + po2.injected);
const pm = new Map();
pm.set("__proto__", { injected: true });
row("Map:    after set('__proto__', { injected: true })", "size " + pm.size + "  keys " + J([...pm.keys()]) + "  pm.injected " + pm.injected);
const parsed = JSON.parse('{"__proto__": {"injected": true}}');
row("JSON.parse('{\"__proto__\": ...}')", "keys " + J(Object.keys(parsed)) + "  parsed.injected " + parsed.injected);

console.log("");
console.log("[5] JSON");
const jm = new Map([["a", 1], ["b", 2]]);
row("JSON.stringify(map)", J(jm));
row("JSON.stringify([...map])", J([...jm]));
row("JSON.stringify(Object.fromEntries(map))", J(Object.fromEntries(jm)));
row("new Map(JSON.parse(JSON.stringify([...map]))).get('b')", new Map(JSON.parse(J([...jm]))).get("b"));
row("JSON.stringify(new Set([1, 2]))", J(new Set([1, 2])));
row("JSON.stringify({ m: map })", J({ m: jm }));

console.log("");
console.log("[6] a Set: add again, delete then add");
const st = new Set(["x", "y", "z"]);
st.add("x");
row("add('x') again -> order", J([...st]));
st.delete("x"); st.add("x");
row("delete('x'), add('x') -> order", J([...st]));
row("st.add('w') returns the set itself?", st.add("w") === st);
```
```text
===== node20 js20b-23c-map-vs-object.js (exit=0) =====
[1] two different objects as keys
  object: Object.keys(om)                                   ["[object Object]"]
  object: om[u1]                                            second
  Map:    mm.size / mm.get(u1) / mm.get(u2)                 2 / first / second
  Map:    mm.get({ id: 1 })                                 undefined

[2] the size of each
  object: o3.size                                           undefined
  object: Object.keys(o3).length                            3
  Map:    m3.size                                           3

[3] names that come from Object.prototype
  object: 'toString' in {}  /  typeof {}['toString']        true  /  function
  Map:    new Map().has('toString')                         false
  object: 'constructor' in {}  /  typeof {}['constructor']  true  /  function
  Map:    new Map().has('constructor')                      false
  object: 'hasOwnProperty' in {}  /  typeof {}['hasOwnProperty']true  /  function
  Map:    new Map().has('hasOwnProperty')                   false
  object: tally of a, constructor, a                        {"a":2,"constructor":"function Object() { [native code] }1"}
  Map:    tally of a, constructor, a                        [["a",2],["constructor",1]]

[4] the string key "__proto__"
  object: after po['__proto__'] = 'plain string'            keys []  typeof po.__proto__ object
  object: after po2['__proto__'] = { injected: true }       keys []  po2.injected true
  Map:    after set('__proto__', { injected: true })        size 1  keys ["__proto__"]  pm.injected undefined
  JSON.parse('{"__proto__": ...}')                          keys ["__proto__"]  parsed.injected undefined

[5] JSON
  JSON.stringify(map)                                       {}
  JSON.stringify([...map])                                  [["a",1],["b",2]]
  JSON.stringify(Object.fromEntries(map))                   {"a":1,"b":2}
  new Map(JSON.parse(JSON.stringify([...map]))).get('b')    2
  JSON.stringify(new Set([1, 2]))                           {}
  JSON.stringify({ m: map })                                {"m":{}}

[6] a Set: add again, delete then add
  add('x') again -> order                                   ["x","y","z"]
  delete('x'), add('x') -> order                            ["y","z","x"]
  st.add('w') returns the set itself?                       true
```

```text
   om[u1] = "first"  ;  om[u2] = "second"

   u1 ──ToPropertyKey──▶ "[object Object]" ─┐
                                             ├──▶ 한 칸   om["[object Object]"] = "second"
   u2 ──ToPropertyKey──▶ "[object Object]" ─┘

   mm.set(u1, "first") ; mm.set(u2, "second")

   u1 ──(정체 그대로)──▶ 칸 1  "first"
   u2 ──(정체 그대로)──▶ 칸 2  "second"          mm.get({ id: 1 })  ->  undefined (새 객체는 새 정체)
```

- ★★★ **`[1]` 객체를 키로 넣으면 객체는 한 칸, `Map` 은 두 칸이다.** `Object.keys(om)` 이 `["[object Object]"]` 이고 `om[u1]` 이 **나중에 쓴 `second`** 다.
  ★ 그리고 `mm.get({ id: 1 })` 은 `undefined` — **모양이 같은 새 객체는 다른 키**다(동작 (1)의 `{a:1}, {a:1}` 행과 같은 사실).
- ★★ **`[2]` 크기** — 객체에는 `size` 가 없다(`undefined`). `Object.keys(o3).length` 로 **매번 배열을 만들어** 센다. `Map` 은 `size` 하나다.
- ★★★ **`[3]` 물려받은 이름** — 빈 객체 `{}` 에도 `'toString' in {}` 이 **true** 다(`Object.prototype` 에서 온다 — [15번](../15-prototype-chain/2-summary.md)의 체인).
  그래서 단어를 세는 흔한 코드 `tally[w] = (tally[w] || 0) + 1` 이 `"constructor"` 에서 **`"function Object() { [native code] }1"`** 을 만든다.
  `Map` 은 `has('constructor')` 가 **false** 이고 셈이 `1` 로 맞다. **`Map` 에는 물려받은 키가 없다.**
- ★★★ **`[4]` 문자열 키 `"__proto__"`** — 객체에 `po["__proto__"] = x` 로 **대입**하면 그것은 **키를 만드는 게 아니라 `Object.prototype` 의 접근자(setter)를 부르는 것**이다.
  문자열을 넣으면 **조용히 무시**되고(`keys []`), 객체를 넣으면 **프로토타입이 바뀌어** `po2.injected` 가 `true` 가 된다. **자기 키는 여전히 `[]`** 다.
  `Map` 은 `size 1` · `keys ["__proto__"]` 로 **그냥 한 칸**이다. `JSON.parse` 가 만든 `"__proto__"` 는 **자기 키**가 된다(리터럴 다섯 형태는 [13번](../13-object-literals-and-properties/2-summary.md)의 `[5]` 가 정본).
- ★★★ **`[5]` JSON** — `JSON.stringify(map)` 은 **`{}`** 다. 에러가 아니다 — **`Map` 에는 열거 가능한 자기 프로퍼티가 없어서** 빈 객체로 찍힌다. `Set` 도 `{}`, 객체 안의 `Map` 도 `{"m":{}}`.
  ★ **데이터가 조용히 사라진다.** 내보낼 때는 `[...map]`(쌍의 배열)이나 `Object.fromEntries(map)`(문자열 키일 때만)로 바꾸고, 들여올 때 `new Map(...)` 으로 되돌린다.
- ★ **`[6]` `Set` 의 재삽입** — 이미 있는 `x` 를 다시 `add` 해도 **자리가 안 바뀐다**. **지웠다가 넣으면 맨 뒤로 간다.** `add` 는 **자기 자신을 돌려준다**(체이닝이 되는 이유).
  `Map` 의 같은 규칙과 **순회 중 추가·삭제**는 [19번](../19-iterable-protocol-and-for-of/2-summary.md) 동작 (5)가 이미 쟀다 — 다시 재지 않는다.

**선택 기준** — 위 출력에서 나온 것만 적는다.

| 기준 | 평범한 객체 | `Map` | 근거 |
|---|---|---|---|
| 키 타입 | 문자열·심볼만 — 나머지는 **글자로 바뀐다** | **아무 값이나**, 객체는 정체로 | `[1]` · 동작 (1) |
| 순서 | **정수 같은 키가 앞으로** 온 뒤 삽입순 | **삽입순 하나** | [13번](../13-object-literals-and-properties/2-summary.md) · [19번](../19-iterable-protocol-and-for-of/2-summary.md) |
| 크기 | `size` 없음 — 세려면 배열을 만든다 | `size` | `[2]` |
| 물려받은 이름 | `toString`·`constructor` 가 **이미 있다** | **없다** | `[3]` |
| `"__proto__"` | 대입하면 **프로토타입을 바꾼다** | 그냥 키 | `[4]` |
| JSON | 그대로 나간다 | **`{}` 가 된다** — 직접 바꿔야 한다 | `[5]` |
| 속도 · 메모리 | **안 쟀다** | **안 쟀다** | — |

★ **「레코드(필드 이름이 코드에 적힌 것)는 객체, 키가 데이터인 사전은 `Map`」** 이 위 표의 요약이다.

### (4) ★★ 약한 쪽에 무엇을 넣을 수 있나 — 그리고 무엇이 없나

**언제 쓰나** — 객체에 **남의 코드를 안 건드리고** 데이터를 덧붙일 때(캐시·메타데이터·방문 표시) · 그 키로 원시값을 쓰려 할 때.

```js
// js20b-23d-weak-keys.js
// 무엇이 WeakMap 의 키 · WeakSet 의 원소 · WeakRef 의 대상이 될 수 있나 -- 그리고 WeakMap 에 무엇이 없나.
const row = (label, v) => console.log("  " + label.padEnd(50) + v);
const attempt = (label, run) => {
  try { row(label, "ok " + String(run())); }
  catch (e) { row(label, e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] candidate keys for WeakMap.prototype.set");
const candidates = [
  ["{}", {}],
  ["[]", []],
  ["function () {}", function () {}],
  ["1", 1],
  ["'str'", "str"],
  ["null", null],
  ["undefined", undefined],
  ["1n", 1n],
  ["Symbol('local')", Symbol("local")],
  ["Symbol.for('registered')", Symbol.for("registered")],
  ["Symbol.iterator", Symbol.iterator],
];
for (const [label, key] of candidates) attempt("new WeakMap().set(" + label + ", 1)", () => new WeakMap().set(key, 1).has(key));

console.log("");
console.log("[2] the same primitive in the other weak holders");
attempt("new WeakSet().add(1)", () => new WeakSet().add(1));
attempt("new WeakRef(1)", () => new WeakRef(1));
attempt("new WeakRef(Symbol('local')).deref()", () => typeof new WeakRef(Symbol("local")).deref());
attempt("new WeakRef(Symbol.for('registered'))", () => new WeakRef(Symbol.for("registered")));
attempt("new FinalizationRegistry(f).register(1, 'h')", () => new FinalizationRegistry(() => {}).register(1, "h"));
const t = {};
attempt("registry.register(t, t)  (held value = target)", () => new FinalizationRegistry(() => {}).register(t, t));
attempt("new WeakMap([[1, 'x']])", () => new WeakMap([[1, "x"]]));
attempt("new WeakMap().get(1)", () => new WeakMap().get(1));
attempt("new WeakMap().has(1)", () => new WeakMap().has(1));

console.log("");
console.log("[3] what each prototype has");
const names = ["size", "keys", "values", "entries", "forEach", "clear", "get", "set", "has", "delete"];
const show = (C) => names.map((n) => (n in C.prototype ? n : "-".repeat(n.length))).join(" ");
row("Map.prototype", show(Map));
row("WeakMap.prototype", show(WeakMap));
row("Symbol.iterator in Map.prototype", Symbol.iterator in Map.prototype);
row("Symbol.iterator in WeakMap.prototype", Symbol.iterator in WeakMap.prototype);
attempt("[...new WeakMap()]", () => [...new WeakMap()]);
attempt("for (const x of new WeakSet()) {}", () => { for (const x of new WeakSet()) {} return "done"; });
row("JSON.stringify(new WeakMap([[t, 1]]))", JSON.stringify(new WeakMap([[t, 1]])));
```
```text
===== node20 js20b-23d-weak-keys.js (exit=0) =====
[1] candidate keys for WeakMap.prototype.set
  new WeakMap().set({}, 1)                          ok true
  new WeakMap().set([], 1)                          ok true
  new WeakMap().set(function () {}, 1)              ok true
  new WeakMap().set(1, 1)                           TypeError 「Invalid value used as weak map key」
  new WeakMap().set('str', 1)                       TypeError 「Invalid value used as weak map key」
  new WeakMap().set(null, 1)                        TypeError 「Invalid value used as weak map key」
  new WeakMap().set(undefined, 1)                   TypeError 「Invalid value used as weak map key」
  new WeakMap().set(1n, 1)                          TypeError 「Invalid value used as weak map key」
  new WeakMap().set(Symbol('local'), 1)             ok true
  new WeakMap().set(Symbol.for('registered'), 1)    TypeError 「Invalid value used as weak map key」
  new WeakMap().set(Symbol.iterator, 1)             ok true

[2] the same primitive in the other weak holders
  new WeakSet().add(1)                              TypeError 「Invalid value used in weak set」
  new WeakRef(1)                                    TypeError 「WeakRef: invalid target」
  new WeakRef(Symbol('local')).deref()              ok symbol
  new WeakRef(Symbol.for('registered'))             TypeError 「WeakRef: invalid target」
  new FinalizationRegistry(f).register(1, 'h')      TypeError 「FinalizationRegistry.prototype.register: invalid target」
  registry.register(t, t)  (held value = target)    TypeError 「FinalizationRegistry.prototype.register: target and holdings must not be same」
  new WeakMap([[1, 'x']])                           TypeError 「Invalid value used as weak map key」
  new WeakMap().get(1)                              ok undefined
  new WeakMap().has(1)                              ok false

[3] what each prototype has
  Map.prototype                                     size keys values entries forEach clear get set has delete
  WeakMap.prototype                                 ---- ---- ------ ------- ------- ----- get set has delete
  Symbol.iterator in Map.prototype                  true
  Symbol.iterator in WeakMap.prototype              false
  [...new WeakMap()]                                TypeError 「WeakMap is not a function or its return value is not iterable」
  for (const x of new WeakSet()) {}                 TypeError 「WeakSet is not a function or its return value is not iterable」
  JSON.stringify(new WeakMap([[t, 1]]))             {}
```

```text
   CanBeHeldWeakly(v)  -- 약한 키 · 약한 원소 · WeakRef 대상 · 레지스트리 대상, 네 자리가 같은 검사를 쓴다

   v 가 객체인가? ──yes──▶ 된다                ({} · [] · function)
        │ no
        ▼
   v 가 심볼이고, Symbol.for 로 등록되지 않았나? ──yes──▶ 된다   (Symbol('local') · Symbol.iterator)   ES2023
        │ no                                                    ★ node 18 은 이 가지가 없다
        ▼
   안 된다  -> TypeError 「Invalid value used as weak map key」   (1 · 'str' · null · undefined · 1n · Symbol.for(...))
```

- ★★★ **`[1]` 원시값은 전부 `TypeError`** 다 — `1` · `'str'` · `null` · `undefined` · `1n`. 문구는 `WeakMap` 이 **`Invalid value used as weak map key`**, `WeakSet` 이 **`Invalid value used in weak set`**.
- ★★★ **심볼은 둘로 갈린다** — `Symbol('local')` 과 `Symbol.iterator` 는 **된다**(node 20), **`Symbol.for('registered')` 는 안 된다.**
  명세 `CanBeHeldWeakly` 가 그대로 적는다 — "If arg is a Symbol and KeyForSymbol(arg) is undefined, return true."
  ★ **등록된 심볼은 전역 레지스트리가 영원히 붙잡고 있어서**(같은 문자열로 언제든 다시 얻을 수 있다) 약하게 쥘 의미가 없다. 심볼 레지스트리는 [22번](../22-symbol-and-well-known-symbols/2-summary.md)이 정본이다.
- ★★★ **이 블록이 두 판에서 갈렸다** — node 18 에서는 **심볼이 전부 거부**되고 `WeakRef` 문구가 `target must be an object` 다(ES2023 이전 판). 전문은 [3-answer.md](3-answer.md) 12번.
- ★★ **`[2]` `get(1)` · `has(1)` 은 던지지 않는다** — `undefined` · `false`. **넣을 때만 막고 물을 때는 안 막는다.**
  ★ `register(t, t)`(대상과 보관값이 같은 객체)는 `TypeError` 다. 명세 `register` 가 `SameValue(target, heldValue)` 이면 던지고,
  그 note 가 이유를 준다 — 보관값은 **레지스트리가 그 칸을 가진 동안 살아 있다.** 보관값이 곧 대상이면 **대상이 영원히 안 죽는다.**
- ★★★ **`[3]` `WeakMap.prototype` 에는 `get`·`set`·`has`·`delete` 넷뿐**이다. `size` · `keys` · `values` · `entries` · `forEach` · `clear` · `Symbol.iterator` 가 **없다.**
  펴 보면 `TypeError`, `JSON.stringify` 는 `{}`.
  ★★★ **이것은 빠뜨린 게 아니라 설계다.** 명세 `WeakMap` 절 머리말 —
  "an ECMAScript implementation must not provide any means to observe a key of a WeakMap that does not require the observer to present the observed key."
  키를 이미 손에 쥔 사람만 물을 수 있게 해야 **「언제 비워졌나」가 프로그램에 새지 않는다.** 명세가 이유까지 적는다 — 그 지연이 보이면 "a source of indeterminacy" 가 된다.

### (5) ★★★ 수명 — `gc()` 를 부르고 「불렸나」를 20판씩 센다

**언제 쓰나** — 「`WeakMap` 에 넣었으니 새지 않겠지」·「`Map` 에 넣은 키도 결국 치워지겠지」를 확인하고 싶을 때.
★★★ **값으로는 원리상 못 본다** — 동작 (4)에서 봤듯 `WeakMap` 에는 들여다볼 창이 없다. 그래서 **창을 바꿔 물었다**: 대상 객체에 `FinalizationRegistry` 와 `WeakRef` 를 같이 걸고, `node --expose-gc` 가 여는 `gc()` 를 직접 부른다.

```js
// js20b-23e-reclaim-gc.js
// gc() 를 부른 뒤 FinalizationRegistry 콜백이 「불렸나」 와 WeakRef.deref() 의 답을 센다 -- 조건 여섯 x 20판.
// 판마다 새 객체를 만들고, gc() 를 부르고, 매크로태스크를 최대 WAIT 번 넘기며 콜백을 기다린다.
// ★ 이 블록은 「몇 판 중 몇」 만 찍는다. 「몇 번째 틱에 불렸나」 는 js20b-23f-timing-gc.js 가 따로 찍는다.
const ROUNDS = 20, WAIT = 20;
const tick = () => new Promise((r) => setTimeout(r, 0));
const strongMap = new Map();
const weakMap = new WeakMap();

// 조건마다: 대상을 만들고, 조건에 맞게 붙잡거나 놓는다. 대상 자체는 이 함수 밖으로 새지 않는다.
const conditions = {
  "dropped (no reference left)": () => ({}),
  "kept in a local that stays alive": () => { const o = {}; keep.push(o); return o; },
  "key of a Map": () => { const o = {}; strongMap.set(o, "v"); return o; },
  "key of a WeakMap": () => { const o = {}; weakMap.set(o, "v"); return o; },
  "WeakMap key whose value points back at it": () => { const o = {}; weakMap.set(o, { back: o }); return o; },
  "unregistered before gc": null,
};
const keep = [];

async function round(name, make) {
  let called = 0;
  const reg = new FinalizationRegistry(() => { called++; });
  let ref;
  const token = {};
  (() => {
    const target = make ? make() : {};
    reg.register(target, "held", token);
    ref = new WeakRef(target);
  })();
  if (!make) reg.unregister(token);
  const sameJob = ref.deref() !== undefined;
  gc();
  const sameJobAfterGc = ref.deref() !== undefined;
  await tick();
  gc();
  for (let i = 0; i < WAIT && called === 0; i++) await tick();
  return { sameJob, sameJobAfterGc, alive: ref.deref() !== undefined, called: called > 0 };
}

(async () => {
  console.log("condition".padEnd(46) + "callback  deref() after  deref() in the job");
  console.log("".padEnd(46) + "ran       a later gc     right after gc()");
  for (const [name, make] of Object.entries(conditions)) {
    let ran = 0, alive = 0, sameJobAfterGc = 0;
    for (let r = 0; r < ROUNDS; r++) {
      const o = await round(name, make);
      if (o.called) ran++;
      if (o.alive) alive++;
      if (o.sameJobAfterGc) sameJobAfterGc++;
    }
    console.log(name.padEnd(46) + (ran + "/" + ROUNDS).padEnd(10) + ("object " + alive + "/" + ROUNDS).padEnd(15) + "object " + sameJobAfterGc + "/" + ROUNDS);
  }
})();
```
```text
===== node20 --expose-gc js20b-23e-reclaim-gc.js (exit=0) =====
condition                                     callback  deref() after  deref() in the job
                                              ran       a later gc     right after gc()
dropped (no reference left)                   20/20     object 0/20    object 20/20
kept in a local that stays alive              0/20      object 20/20   object 20/20
key of a Map                                  0/20      object 20/20   object 20/20
key of a WeakMap                              20/20     object 0/20    object 20/20
WeakMap key whose value points back at it     20/20     object 0/20    object 20/20
unregistered before gc                        0/20      object 0/20    object 20/20
```

```text
   누가 대상을 강하게 붙잡나                           콜백      deref()
   ------------------------                           ----      -------
   아무도                                    ─▶ 수거   20/20    0/20 살아 있음
   살아 있는 배열 keep                        ─▶ 안 됨    0/20   20/20
   Map 의 키            (Map 이 키를 강하게 쥔다)  ─▶ 안 됨    0/20   20/20      <- 캐시가 새는 자리
   WeakMap 의 키        (키를 약하게 쥔다)       ─▶ 수거   20/20    0/20
   WeakMap 의 키, 값이 키를 되가리킴            ─▶ 수거   20/20    0/20      <- 에피머론: 값은 키를 못 살린다
   unregister 한 뒤                          ─▶ 수거    0/20    0/20      <- 콜백만 취소됐다

   ★ 맨 오른쪽 열(같은 잡 안에서 gc() 직후 deref)은 여섯 행 전부 20/20 -- KeptAlive
```

- ★★★ **「key of a Map」 행 — 콜백 `0/20`, `deref()` 가 `20/20` 객체.** 보통 `Map` 의 키는 **다른 곳에서 전부 잊혀도 `Map` 이 살려 둔다.** 캐시가 새는 자리가 여기다.
- ★★★ **「key of a WeakMap」 행 — 콜백 `20/20`, `deref()` 는 `0/20`.** `WeakMap` 에 들어간 것이 **대상을 살리지 못했다.**
- ★★★ **「WeakMap key whose value points back at it」 행도 `20/20`** 이다. 값 `{ back: o }` 가 키를 가리키는데도 수거됐다 —
  **값은 키가 살아 있는 동안만 살아 있고, 키를 살리지는 못한다**(에피머론 — 이 관계를 가리키는 이름). 보통 `Map` 이었다면 순환이 서로를 살렸을 자리다.
- ★★ **「unregistered before gc」 행** — 콜백 `0/20`, `deref()` 도 `0/20`. **수거는 됐는데 콜백만 취소된 것**이다. 「콜백이 안 불렸다」를 「안 수거됐다」로 읽으면 이 행에서 틀린다 — **두 창을 같이 봐야 갈린다.**
- ★★★ **맨 오른쪽 열이 여섯 행 전부 `20/20`** 이다 — **같은 동기 실행 안에서는 `gc()` 를 불러도 `deref()` 가 대상을 돌려준다.**
  ★ 명세 보장이다. `new WeakRef(t)` 와 `deref()` 가 대상을 `[[KeptAlive]]` 목록에 넣고(`AddToKeptObjects`), 그 목록은
  "when a synchronous sequence of ECMAScript executions completes" 에야 비워진다(`ClearKeptObjects`). 그래서 탐침은 **`await tick()` 으로 잡을 넘긴 뒤** 다시 `gc()` 를 부른다.

```text
   같은 잡                                  │ 다음 잡 (setTimeout 뒤)
   ───────────────────────────────────────┼──────────────────────────────
   ref = new WeakRef(t)   KeptAlive += t   │
   t 를 잊는다                              │
   gc()                                    │   ClearKeptObjects 가 이미 돌았다
   ref.deref()  -> t   (목록이 붙잡고 있다)  │   gc()
                                           │   ref.deref()  -> undefined
```

★★★ **그런데 이 표의 숫자는 「명세가 보장한 것」이 아니라 「이 판에서 관찰된 것」이다.** 명세의 목표 절이 첫 문장으로 못 박는다 —

> "This specification does not make any guarantees that any object or symbol will be garbage collected. Objects or symbols which are not live may be released after long periods of time, or never at all."

- ★★★ **명세가 보장하는 쪽** — 「**강하게 붙잡힌 것은 수거되지 않는다**」(`keep` · `Map` 의 키 행 · KeptAlive 열). 이쪽은 **어느 엔진에서도 0/20 · 20/20** 이어야 한다.
- ★★★ **명세가 보장하지 않는 쪽** — 「**안 붙잡힌 것은 수거된다**」(`20/20` 인 행들). 이 판의 V8 이 `gc()` 한 번에 거뒀을 뿐이다.
  ★ 그래서 머리말 표에 이 칸을 **「안 흔들리지만 성질의 근거로 쓰지 않는 칸」** 으로 따로 적었다. **판의 관찰**이다.

### (6) ★★ 「언제」 는 다른 블록에 — 흔들려도 되는 칸을 따로 둔다

**언제 쓰나** — 콜백이 도는 시점에 코드를 기대게 하고 싶어질 때(그러면 안 된다는 것을 보려고).

```js
// js20b-23f-timing-gc.js
// 「언제」 를 찍는다 -- gc() 뒤 몇 번째 매크로태스크에서 콜백이 돌았나, gc() 를 안 부르면 돌았나.
// ★ 명세가 묶지 않는 칸이다. 이 블록은 흔들려도 되는 블록으로 선언해 둔다(js20b-23e 와 쪼갠 이유).
const ROUNDS = 20, WAIT = 20;
const tick = () => new Promise((r) => setTimeout(r, 0));

let beforeReturn = 0;
async function round(callGc) {
  let at = -1, n = 0;
  const reg = new FinalizationRegistry(() => { at = n; });
  (() => { reg.register({}, "held"); })();
  await tick();
  if (callGc) { gc(); if (at >= 0) beforeReturn++; }
  for (n = 0; n < WAIT && at < 0; n++) await tick();
  return at;
}

(async () => {
  const withGc = [];
  for (let r = 0; r < ROUNDS; r++) withGc.push(await round(true));
  console.log("[1] gc() called -- macrotask index at which the callback ran, per round (-1 = not within " + WAIT + ")");
  console.log("  ticks: " + withGc.join(" "));
  console.log("  rounds where it had run before gc() returned: " + beforeReturn + "/" + ROUNDS);
  const withoutGc = [];
  for (let r = 0; r < ROUNDS; r++) withoutGc.push(await round(false));
  console.log("[2] gc() not called -- the same, per round");
  console.log("  ticks: " + withoutGc.join(" "));
})();
```
```text
===== node20 --expose-gc js20b-23f-timing-gc.js (exit=0) =====
[1] gc() called -- macrotask index at which the callback ran, per round (-1 = not within 20)
  ticks: 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  rounds where it had run before gc() returned: 0/20
[2] gc() not called -- the same, per round
  ticks: -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1
```

- ★★★ **이 블록과 동작 (5)의 블록을 일부러 쪼갰다**(규칙 11). **「불렸나」는 동작 (5)에, 「언제」는 여기에** 둔다.
  `ticks:` 줄은 머리말 표의 **흔들리는 칸**이다 — 재대조에서 이 줄이 달라져도 「고칠 것」이 아니다.
- ★★ **`[1]` 이 판에서는 `gc()` 뒤 첫 매크로태스크(`0`)에 20판 다 돌았다.** `gc()` 가 **돌아오기 전에는 한 번도 안 돌았다**(`0/20`) — 콜백은 **나중 잡으로 예약**된다.
  명세는 정리 작업을 **호스트가 잡으로 넣게** 한다 — `HostEnqueueFinalizationRegistryCleanupJob` 은 그 잡을 "at some future time, if possible" 에 돌린다.
  **몇 번째 틱인지는 호스트 몫**이고, "if possible" 이라 **돈다는 것조차** 약속이 아니다.
- ★★★ **`[2]` `gc()` 를 안 부르면 20판 모두 20틱 안에 안 돌았다**(`-1`). ★ 이것을 「안 불린다」로 적으면 틀린다 — **「이 판이 이 짧은 시간에 GC 를 안 했다」** 일 뿐이다.
  ★★ **제4의 상태와 헷갈리지 마라.** 「잴 것이 없다」가 아니라 **재 봤고, 그 시간 안에는 안 왔다**다. 더 기다리면 올 수도, 영영 안 올 수도 있다 — 명세 문장 그대로 "or never at all".

### (7) ★★ 집합 연산(ES2025) — 결과의 순서와 인자에게 무엇을 묻나

**언제 쓰나** — 두 `Set` 의 합·교·차를 손으로 `filter` 하던 코드를 바꿀 때 · 인자로 `Set` 이 아닌 것을 넘기고 싶을 때.
★ **두 node 판에 없다** — Chrome 151 로 돌렸다.

```js
// js20b-23g-set-methods.web.js
// 집합 연산 일곱 개(ES2025) -- 결과와 그 순서 · 인자로 무엇을 받나 · 인자의 무엇을 부르나(로그).
const row = (label, v) => console.log("  " + label.padEnd(56) + v);
const J = (s) => "[" + [...s].map(String).join(",") + "]";
const attempt = (label, run) => {
  try { row(label, String(run())); }
  catch (e) { row(label, e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] a = {1,2,3,4}, b = {5,3,1} -- results in iteration order");
const a = new Set([1, 2, 3, 4]);
const b = new Set([5, 3, 1]);
row("a.union(b)", J(a.union(b)));
row("b.union(a)", J(b.union(a)));
row("a.intersection(b)", J(a.intersection(b)));
row("b.intersection(a)", J(b.intersection(a)));
row("a.difference(b)", J(a.difference(b)));
row("a.symmetricDifference(b)", J(a.symmetricDifference(b)));
row("a.isSubsetOf(b) / isSupersetOf(b) / isDisjointFrom(b)", [a.isSubsetOf(b), a.isSupersetOf(b), a.isDisjointFrom(b)].join(" / "));
row("new Set([1,3]).isSubsetOf(a)", new Set([1, 3]).isSubsetOf(a));
row("a after all of the above", J(a));
row("a.union(b) === a", a.union(b) === a);

console.log("");
console.log("[2] what can be the argument");
attempt("a.union([5, 6])", () => J(a.union([5, 6])));
attempt("a.union(new Map([[9, 'x']]))", () => J(a.union(new Map([[9, "x"]]))));
attempt("a.union({ size: 1, has: () => true })", () => J(a.union({ size: 1, has: () => true })));
attempt("a.union({ has() {}, keys() {} })  (no size)", () => J(a.union({ has() {}, keys() {} })));
attempt("a.union({ size: -1, has() {}, keys() {} })", () => J(a.union({ size: -1, has() {}, keys() {} })));
attempt("a.union('abc')", () => J(a.union("abc")));
attempt("new Set([NaN, 0]).intersection(new Set([NaN, -0]))", () => J(new Set([NaN, 0]).intersection(new Set([NaN, -0]))));

console.log("");
console.log("[3] a set-like argument with logging -- which of size / has / keys each method calls");
function setLike(values, log) {
  return {
    get size() { log.push("size"); return values.length; },
    has(v) { log.push("has(" + v + ")"); return values.includes(v); },
    keys() {
      log.push("keys()");
      let i = 0;
      return { next() { log.push("next"); return i < values.length ? { value: values[i++], done: false } : { value: undefined, done: true }; } };
    },
  };
}
const three = new Set([1, 2, 3]);
for (const m of ["union", "intersection", "difference", "symmetricDifference", "isSubsetOf", "isSupersetOf", "isDisjointFrom"]) {
  for (const other of [[2, 9], [2, 9, 8, 7, 6]]) {
    const log = [];
    const r = three[m](setLike(other, log));
    const shown = r instanceof Set ? J(r) : String(r);
    console.log("  {1,2,3}." + m + "(size " + other.length + ")  -> " + shown);
    console.log("      " + log.join(" "));
  }
}
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-23g-set-methods.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] a = {1,2,3,4}, b = {5,3,1} -- results in iteration order
  a.union(b)                                              [1,2,3,4,5]
  b.union(a)                                              [5,3,1,2,4]
  a.intersection(b)                                       [3,1]
  b.intersection(a)                                       [3,1]
  a.difference(b)                                         [2,4]
  a.symmetricDifference(b)                                [2,4,5]
  a.isSubsetOf(b) / isSupersetOf(b) / isDisjointFrom(b)   false / false / false
  new Set([1,3]).isSubsetOf(a)                            true
  a after all of the above                                [1,2,3,4]
  a.union(b) === a                                        false

[2] what can be the argument
  a.union([5, 6])                                         TypeError 「The .size property is NaN」
  a.union(new Map([[9, 'x']]))                            [1,2,3,4,9]
  a.union({ size: 1, has: () => true })                   TypeError 「string "keys" is not a function」
  a.union({ has() {}, keys() {} })  (no size)             TypeError 「The .size property is NaN」
  a.union({ size: -1, has() {}, keys() {} })              RangeError 「'-1' is an invalid size」
  a.union('abc')                                          TypeError 「Set.prototype.union argument must be an object」
  new Set([NaN, 0]).intersection(new Set([NaN, -0]))      [NaN,0]

[3] a set-like argument with logging -- which of size / has / keys each method calls
  {1,2,3}.union(size 2)  -> [1,2,3,9]
      size keys() next next next
  {1,2,3}.union(size 5)  -> [1,2,3,9,8,7,6]
      size keys() next next next next next next
  {1,2,3}.intersection(size 2)  -> [2]
      size keys() next next next
  {1,2,3}.intersection(size 5)  -> [2]
      size has(1) has(2) has(3)
  {1,2,3}.difference(size 2)  -> [1,3]
      size keys() next next next
  {1,2,3}.difference(size 5)  -> [1,3]
      size has(1) has(2) has(3)
  {1,2,3}.symmetricDifference(size 2)  -> [1,3,9]
      size keys() next next next
  {1,2,3}.symmetricDifference(size 5)  -> [1,3,9,8,7,6]
      size keys() next next next next next next
  {1,2,3}.isSubsetOf(size 2)  -> false
      size
  {1,2,3}.isSubsetOf(size 5)  -> false
      size has(1)
  {1,2,3}.isSupersetOf(size 2)  -> false
      size keys() next next
  {1,2,3}.isSupersetOf(size 5)  -> false
      size
  {1,2,3}.isDisjointFrom(size 2)  -> false
      size keys() next
  {1,2,3}.isDisjointFrom(size 5)  -> false
      size has(1) has(2)
```

```text
   a.intersection(b)     a = {1,2,3,4} (size 4)   b = {5,3,1} (size 3)

   GetSetRecord(b)  ->  size · has · keys 를 읽어 둔다 (셋 중 하나라도 이상하면 여기서 던진다)

   this.size <= other.size ?
      yes ─▶ this 를 돈다, 원소마다 other.has(x)   -> 결과는 this 의 순서
      no  ─▶ other.keys() 를 돈다, this 에 있나      -> 결과는 other 의 순서   ★ a.intersection(b) 가 여기

   a.intersection(b)  ->  [3,1]      (b 의 순서: 5 없음, 3, 1)
   b.intersection(a)  ->  [3,1]      (b 가 더 작다 -> b 를 돈다)
```

- ★★★ **`[1]` 결과는 새 `Set` 이고 원본은 안 바뀐다**(`a after all` 이 그대로, `a.union(b) === a` 가 false).
  ★★★ **순서가 비대칭이다** — `a.union(b)` 는 `[1,2,3,4,5]`, `b.union(a)` 는 `[5,3,1,2,4]`(this 먼저, 그다음 인자의 새 원소).
  ★★ **`a.intersection(b)` 가 `[3,1]` 로 a 의 순서(`1,3`)가 아니다** — a 가 더 커서 **b 를 돌았기 때문**이다. 명세 `Set.prototype.intersection` 이 크기 비교로 가지를 가른다.
- ★★★ **`[2]` 인자는 「`Set`」 이 아니라 「set-like」다** — `size` · `has` · `keys` 셋을 가진 객체면 된다(`GetSetRecord`).
  그래서 **`Map` 이 그냥 통과**하고(`[1,2,3,4,9]` — 키만 쓴다), **배열은 `TypeError 「The .size property is NaN」`** 다. 배열에는 `size` 가 없고 `length` 가 있다.
  ★ `size` 가 음수면 **`RangeError`**, `keys` 가 없으면 `TypeError`, 원시값이면 `TypeError` — 전부 **호출 전에** 인자를 검사한다.
- ★★★ **`[3]` 로그 — 같은 메서드가 인자 크기에 따라 다른 것을 부른다.**
  `intersection`·`difference` 는 인자가 작으면(size 2) **`keys()` 를 돌고**, 크면(size 5) **`has()` 를 원소마다** 부른다.
  `union`·`symmetricDifference` 는 크기와 상관없이 **`keys()` 만** 돈다. 판정 메서드는 **일찍 끝낸다** —
  `isSubsetOf(size 2)` 는 **`size` 하나만 읽고** false(3 원소가 2 원소의 부분집합일 수 없다), `isDisjointFrom(size 2)` 는 `next` 한 번에 공통 원소를 찾아 끝냈다.
  ★ **「인자의 `has` 가 불린다고 믿고 부작용을 걸면」 인자 크기에 따라 안 불린다** — 이 로그가 그것을 보여 준다.

### (8) ★★ Upsert(ES2026) — 「없으면 넣고 꺼내기」 가 콜백을 언제 부르나

**언제 쓰나** — `if (!m.has(k)) m.set(k, []); m.get(k).push(x)` 같은 세 줄을 한 줄로 줄일 때.
★ **두 node 판에 없다** — Chrome 151 로 돌렸다.

```js
// js20b-23h-upsert.web.js
// getOrInsert / getOrInsertComputed (ES2026 Upsert) -- 무엇을 돌려주나 · 콜백을 언제 부르나(로그).
const row = (label, v) => console.log("  " + label.padEnd(58) + v);
const J = JSON.stringify;
const attempt = (label, run) => {
  try { row(label, String(run())); }
  catch (e) { row(label, e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] getOrInsert(key, value)");
const m = new Map([["a", 1]]);
row("m.getOrInsert('a', 99)", m.getOrInsert("a", 99));
row("m.getOrInsert('b', 2)", m.getOrInsert("b", 2));
row("m entries", J([...m]));
let evaluated = 0;
const mk = () => { evaluated++; return []; };
m.getOrInsert("a", mk());
row("argument expression evaluated for an existing key?", "times " + evaluated);

console.log("");
console.log("[2] getOrInsertComputed(key, callback) with a logging callback");
const log = [];
const cb = (k) => { log.push("callback(" + String(k) + ")"); return "made-" + String(k); };
const c = new Map([["a", "old"]]);
row("c.getOrInsertComputed('a', cb)", c.getOrInsertComputed("a", cb) + "   log " + J(log));
log.length = 0;
row("c.getOrInsertComputed('b', cb)", c.getOrInsertComputed("b", cb) + "   log " + J(log));
log.length = 0;
row("c.getOrInsertComputed('b', cb)  (again)", c.getOrInsertComputed("b", cb) + "   log " + J(log));
log.length = 0;
row("c.getOrInsertComputed(-0, cb) -> key passed to cb", c.getOrInsertComputed(-0, (k) => { log.push(Object.is(k, -0) ? "-0" : "+0"); return "zero"; }) + "   log " + J(log));
row("c entries", J([...c].map(([k, v]) => [String(k), v])));

console.log("");
console.log("[3] the callback writes the same key before returning");
const w = new Map();
const r = w.getOrInsertComputed("k", () => { w.set("k", "set inside"); return "returned"; });
row("return value", r);
row("w.get('k') afterwards", w.get("k"));
row("w.size", w.size);

console.log("");
console.log("[4] the callback throws");
const t = new Map();
attempt("t.getOrInsertComputed('k', () => { throw ... })", () => t.getOrInsertComputed("k", () => { throw new Error("from callback"); }));
row("t.has('k') afterwards", t.has("k"));
attempt("t.getOrInsertComputed('k', 'not a function')", () => t.getOrInsertComputed("k", "not a function"));
attempt("new Map([['k', 1]]).getOrInsertComputed('k', 42)", () => new Map([["k", 1]]).getOrInsertComputed("k", 42));

console.log("");
console.log("[5] the WeakMap versions");
const wm = new WeakMap();
const key = {};
row("wm.getOrInsert(key, 1) then (key, 2)", wm.getOrInsert(key, 1) + " then " + wm.getOrInsert(key, 2));
attempt("wm.getOrInsert(1, 'x')", () => wm.getOrInsert(1, "x"));
log.length = 0;
attempt("wm.getOrInsertComputed(1, cb)  -> cb log", () => wm.getOrInsertComputed(1, cb) + "   log " + J(log));
row("  cb log after that attempt", J(log));
row("typeof Set.prototype.getOrInsert", typeof Set.prototype.getOrInsert);

console.log("");
console.log("[6] the older idiom next to it -- a Map subclass that logs its own has / get / set");
const calls = [];
class Counted extends Map {
  has(k) { calls.push("has"); return super.has(k); }
  get(k) { calls.push("get"); return super.get(k); }
  set(k, v) { calls.push("set"); return super.set(k, v); }
}
const old = new Counted();
if (!old.has("x")) old.set("x", []);
old.get("x").push(1);
row("if (!has) set; get(...).push  -> calls", J(calls));
calls.length = 0;
old.getOrInsert("y", []).push(1);
row("getOrInsert(...).push          -> calls", J(calls));
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-23h-upsert.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] getOrInsert(key, value)
  m.getOrInsert('a', 99)                                    1
  m.getOrInsert('b', 2)                                     2
  m entries                                                 [["a",1],["b",2]]
  argument expression evaluated for an existing key?        times 1

[2] getOrInsertComputed(key, callback) with a logging callback
  c.getOrInsertComputed('a', cb)                            old   log []
  c.getOrInsertComputed('b', cb)                            made-b   log ["callback(b)"]
  c.getOrInsertComputed('b', cb)  (again)                   made-b   log []
  c.getOrInsertComputed(-0, cb) -> key passed to cb         zero   log ["+0"]
  c entries                                                 [["a","old"],["b","made-b"],["0","zero"]]

[3] the callback writes the same key before returning
  return value                                              returned
  w.get('k') afterwards                                     returned
  w.size                                                    1

[4] the callback throws
  t.getOrInsertComputed('k', () => { throw ... })           Error 「from callback」
  t.has('k') afterwards                                     false
  t.getOrInsertComputed('k', 'not a function')              TypeError 「Map.prototype.getOrInsertComputed is not a function」
  new Map([['k', 1]]).getOrInsertComputed('k', 42)          TypeError 「Map.prototype.getOrInsertComputed is not a function」

[5] the WeakMap versions
  wm.getOrInsert(key, 1) then (key, 2)                      1 then 1
  wm.getOrInsert(1, 'x')                                    TypeError 「Invalid value used as weak map key」
  wm.getOrInsertComputed(1, cb)  -> cb log                  TypeError 「Invalid value used as weak map key」
    cb log after that attempt                               []
  typeof Set.prototype.getOrInsert                          undefined

[6] the older idiom next to it -- a Map subclass that logs its own has / get / set
  if (!has) set; get(...).push  -> calls                    ["has","set","get"]
  getOrInsert(...).push          -> calls                   []
```

```text
   m.getOrInsertComputed(key, cb)

   ① cb 가 함수인가?  아니면 TypeError  (키가 이미 있어도 먼저 검사한다)
   ② key 를 접는다 (-0 -> +0)
   ③ 있으면 그 값을 돌려준다                         <- cb 는 안 불린다
   ④ 없으면 value = cb(key)                          <- 접힌 key 가 넘어간다
   ⑤ cb 가 도는 사이 같은 key 가 생겼으면 그 칸을 value 로 덮는다
      아니면 { key, value } 를 끝에 붙인다
   ⑥ value 를 돌려준다
```

- ★★★ **`[2]` 콜백은 키가 없을 때만, 한 번 불린다** — 있는 `a` 에는 `log []`, 없는 `b` 에는 `["callback(b)"]`, 두 번째 `b` 에는 다시 `[]`.
  ★ **`-0` 으로 부르면 콜백은 `+0` 을 받는다**(`log ["+0"]`) — 동작 (2)의 접기가 **콜백을 부르기 전에** 일어난다.
- ★★★ **`[1]` `getOrInsert(key, value)` 의 `value` 는 키가 있어도 먼저 평가된다**(`times 1`). **메서드가 아니라 JS 의 인자 평가 규칙**이다.
  비싼 값이면 `getOrInsertComputed` 를 쓰는 이유가 이것이다.
- ★★ **`[3]` 콜백 안에서 같은 키를 `set` 하면 콜백의 반환값이 이긴다**(`returned`, `size 1`). 명세 note — "The Map may have been modified during execution of callback." 그래서 ⑤ 에서 다시 찾는다.
- ★★ **`[4]` 콜백이 던지면 아무것도 안 들어간다**(`has('k')` false).
- ★★★ **`[4]` 둘째·셋째 줄 — 콜백 자리에 함수가 아닌 값을 넘기면 문구가 `Map.prototype.getOrInsertComputed is not a function`** 이다.
  **메서드는 멀쩡히 있다** — 함수가 아닌 것은 **콜백**이다. ★★ **V8 의 문구가 원인을 가리키지 않는 자리**다(규칙 27). 근거로는 **종류(`TypeError`)와 「키가 있어도 던진다」** 만 쓴다.
- ★ **`[5]` `WeakMap` 판도 있다** — `getOrInsert(key, 1)` 뒤 `(key, 2)` 는 `1`. 원시값 키는 `TypeError`, 그리고 **콜백을 부르기 전에** 던진다(`cb log []`). `Set` 에는 없다(`undefined`).
- ★★ **`[6]` 옛 관용구는 `has` · `set` · `get` 세 번을 부르고, `getOrInsert` 는 서브클래스가 덮어쓴 메서드를 하나도 안 부른다**(`[]`).
  ★ 「조회 횟수가 줄었다」까지만 이 출력이 말한다. **빠르다는 뜻은 아니다 — 안 쟀다.** 그리고 서브클래스의 `set` 을 믿은 코드는 **`getOrInsert` 로 바꾸면 그 훅이 안 불린다.**

### (9) ★★ 파이썬과의 대비 — 「같은 키」 의 규칙이 반대 방향으로 갈린다

**언제 쓰나** — 파이썬 `dict` 습관으로 JS `Map` 의 키를 예상할 때.

파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번**이 `dict` 키 요건을 실측했다 — 그 문서의 출력만 인용한다.

| 짝 | 파이썬 `dict` (12번의 출력) | JS `Map` (동작 (1)·(2)) | 왜 갈리나 |
|---|---|---|---|
| `1` · `1.0` · `True` | **한 칸** — `{1: '불리언'}` · `len 1` | `1` · `1.0` 은 한 칸, **`true` 는 다른 칸** | 파이썬은 `hash` + `==` 가 **타입을 가로질러** 같다. JS `Map` 은 **강제 변환을 안 한다** |
| `nan` 두 개 | **두 칸** — `{nan: '첫째', nan: '둘째'}` · 같은 객체일 때만 찾힌다 | **한 칸** — 네 가지로 만든 `NaN` 이 `size 1` | 파이썬은 **정체(`is`) 먼저, 그다음 `==`**. JS 는 **SameValueZero 가 `NaN` 을 같다고 정의**한다 |
| `0.0` · `-0.0` | **한 칸** — 남은 키 `0.0` | **한 칸** — 남은 키 `+0`(입구에서 접는다) | 둘 다 같다. JS 는 **저장되는 키까지 `+0` 으로 바뀐다** |
| `'1'` · `1` | 두 칸 | 두 칸 | 같다 — 객체 키만 한 칸으로 뭉갠다(동작 (1)) |

- ★★★ **방향이 반대다** — 파이썬은 **「값이 같으면 타입이 달라도 한 칸」** 이고 `nan` 에서 무너진다. JS `Map` 은 **「타입이 다르면 다른 칸」** 이고 `NaN` 을 **일부러** 한 칸으로 묶었다.
- ★ `set` 의 원소 규칙은 같은 목록의 **13번**이 정본이다 — 파이썬 `set` 도 `dict` 키와 같은 요건(`hash` + `==`)을 쓴다. JS `Set` 은 동작 (1)에서 `Map` 키와 **56칸 중 한 칸도 안 갈렸다**.
- ★ **파이썬 쪽은 이 배치에서 다시 돌리지 않았다** — 12번 문서에 실린 출력을 인용했다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28 — 돌리지 않은 코드 펜스를 싣지 않는다).

| 형태 | 돌려주는 것 | 판 | 어디서 봤나 |
|---|---|---|---|
| `new Map()` · `new Map(쌍의 이터러블)` | 새 `Map` — 인자는 19번의 프로토콜로 읽는다 | ES2015 | 동작 (3) |
| `m.set(k, v)` | **`m` 자신** — 체이닝 | ES2015 | 명세 `Map.prototype.set` 의 끝 단계 "Return map" |
| `m.get(k)` · `m.has(k)` · `m.delete(k)` | 값 또는 `undefined` · boolean · boolean | ES2015 | 동작 (1)·(3) |
| `m.size` | 개수 — **접근자 속성**(괄호 없음) | ES2015 | 동작 (3)의 `[2]` |
| `new Map(Object.entries(o))` · `Object.fromEntries(m)` | 객체 ↔ `Map` (되돌리면 키가 글자가 된다) | ES2015 · ES2019 | 동작 (3)의 `[5]` |
| `s.add(x)` | **`s` 자신** | ES2015 | 동작 (3)의 `[6]` |
| `a.union(b)` 외 여섯 | 새 `Set` 또는 boolean — 인자는 **set-like** | **ES2025** | 동작 (7) |
| `m.getOrInsert(k, v)` · `m.getOrInsertComputed(k, cb)` | 있던 값 또는 넣은 값 — `WeakMap` 에도 있다 | **ES2026** | 동작 (8) |
| `new WeakMap()` · `wm.get/set/has/delete` | 넷뿐 — `size`·순회 없음 | ES2015 | 동작 (4)의 `[3]` |
| `new WeakRef(t)` · `ref.deref()` | 대상 또는 `undefined` | ES2021 | 동작 (5) |
| `new FinalizationRegistry(cb)` · `reg.register(t, held, token)` · `reg.unregister(token)` | `undefined` · boolean | ES2021 | 동작 (5) |

- **비교** — `Map` 키 · `Set` 원소 · `includes` 는 SameValueZero. 키는 **들어갈 때 `-0` 이 `+0` 이 된다.**
- **순서** — 삽입순. 이미 있는 키에 `set`/`add` 는 자리를 안 바꾸고, 지웠다 넣으면 맨 뒤.
- **약한 쪽** — `CanBeHeldWeakly`: 객체이거나 **등록 안 된 심볼**(ES2023). 원시값은 `TypeError`.

## 어디서 틀리나

### (1) ★★★ `indexOf` 와 `includes` 를 같은 것으로 쓴다

`[NaN].indexOf(NaN)` 은 **-1**, `[NaN].includes(NaN)` 은 **true** 다(동작 (1)의 `NaN, NaN` 행 — `indexOf` 열 n, `includes` 열 y).
`includes` 는 `Map`·`Set` 과 한 가족(SameValueZero)이고 `indexOf` 는 `===` 가족이다.

### (2) ★★★ 객체를 평범한 객체의 키로 쓴다

모든 객체가 `"[object Object]"` 한 칸으로 **덮어쓰인다**(동작 (3)의 `[1]`). 에러가 안 나서 **마지막 값만 남은 채** 진행된다. 객체가 키면 `Map` 이다.

### (3) ★★★ `JSON.stringify(map)` 이 내용을 내보낼 것이라 믿는다

**`{}`** 가 나온다. 에러도 경고도 없다(동작 (3)의 `[5]`). 객체 안에 박힌 `Map` 도 `{"m":{}}` 로 조용히 빈다. `[...map]` 으로 바꿔서 보낸다.

### (4) ★★★ `Map` 에 넣은 객체도 결국 치워질 것이라 믿는다

보통 `Map` 의 키는 `Map` 이 **강하게** 쥔다 — 콜백 `0/20`(동작 (5)의 「key of a Map」 행). 객체 수명에 맞춰 사라져야 하는 캐시는 `WeakMap` 이다.

### (5) ★★★ `FinalizationRegistry` 콜백을 정리 로직의 **보장**으로 쓴다

명세가 "or never at all" 이라고 적는다. 이 판에서도 **`gc()` 를 안 부르면 20판 모두 안 돌았다**(동작 (6)의 `[2]`).
파일 닫기·락 풀기 같은 **반드시 일어나야 하는 정리**는 `try`/`finally` 나 명시적인 `close()` 로 한다. 콜백은 **보조**다.

### (6) ★★ 「콜백이 안 불렸으니 안 수거됐다」 로 읽는다

`unregister` 한 행은 **수거는 됐는데(`deref` 0/20) 콜백만 없다**(동작 (5)). 콜백과 `deref()` 두 창을 같이 봐야 한다.

### (7) ★★ `WeakMap` 의 크기나 목록을 찍어 디버깅하려 한다

**창이 없다** — `size`·`keys`·순회가 전부 없고 `JSON.stringify` 는 `{}` 다(동작 (4)의 `[3]`). 명세가 **일부러** 막았다. 목록이 필요하면 그 자료는 `Map` 이어야 한다.

### (8) ★★ 원시값이나 `Symbol.for` 심볼을 `WeakMap` 키로 쓴다

`TypeError` 다(동작 (4)). 등록 안 된 심볼은 되지만 **node 18 에서는 그것도 안 된다**(ES2023). 판을 확인한다.

### (9) ★★ `a.intersection(b)` 의 결과가 a 의 순서일 것이라 믿는다

**크기가 작은 쪽의 순서**다 — a 가 더 크면 b 를 돌아 `[3,1]` 이 나왔다(동작 (7)의 `[1]`). 순서가 의미를 가지면 결과를 다시 정렬하거나 순서를 가진 쪽을 this 로 두고 `filter` 로 쓴다.

### (10) ★★ 집합 연산에 배열을 넘긴다

`TypeError 「The .size property is NaN」`(동작 (7)의 `[2]`). `new Set(arr)` 로 감싸서 넘긴다. ★ 반대로 **`Map` 은 그냥 통과**한다 — 키 집합으로 쓰인다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- `Map` 키 · `Set` 원소가 **`-0` 을 `+0` 으로 접은 뒤 SameValue** 로 비교되는 것(결과적으로 SameValueZero) · **저장되는 키가 `+0`** 인 것 — `CanonicalizeKeyedCollectionKey`.
- `includes` 가 SameValueZero, `indexOf`·`===` 가 IsStrictlyEqual, `Object.is` 가 SameValue 인 것.
- **삽입 순서** — `[[MapData]]`·`[[SetData]]` 가 리스트다.
- `WeakMap`/`WeakSet`/`WeakRef`/`FinalizationRegistry` 의 대상이 **`CanBeHeldWeakly`**(객체 · 등록 안 된 심볼)여야 하는 것 · 아니면 `TypeError`.
- ★★★ **`WeakMap` 에 키를 꺼내 볼 수단이 없는 것** — 머리말의 "must not provide any means to observe a key".
- ★★★ **강하게 붙잡힌 것은 수거되지 않는 것 · 같은 동기 실행 안에서 `WeakRef` 대상이 살아 있는 것**(`AddToKeptObjects`/`ClearKeptObjects`).
- 집합 연산이 인자를 **`GetSetRecord`**(`size` → `has` → `keys` 순으로 읽고 검사)로 받는 것 · `intersection`·`difference` 가 **크기 비교로 가지를 가르는 것** · 결과가 새 `Set` 인 것.
- `getOrInsertComputed` 가 **콜백 검사를 먼저** 하고, 키가 없을 때만 **접힌 키로** 부르고, 콜백 뒤 **다시 찾아 덮는 것**.
- 예외의 **종류**(`TypeError` · `RangeError`).

### 엔진(V8) 구현 · 이 판의 관찰

- ★★★ **`gc()` 한 번에 안 붙잡힌 대상이 거둬진 것**(20/20) · 콜백이 **첫 매크로태스크**에 돈 것 · `gc()` 없이는 20틱 안에 안 돈 것 — **전부 이 판의 관찰**이다. 명세는 "may" 로만 적는다.
- `gc()` 자체 — **ECMA-262 에 없다.** V8 플래그 `--expose-gc` 가 여는 전역 함수다.
- 예외 **문구 전부** — `Invalid value used as weak map key` · `WeakRef: invalid target`(v20) 대 `WeakRef: target must be an object`(v18) · `The .size property is NaN` · `'-1' is an invalid size` ·
  ★ `Map.prototype.getOrInsertComputed is not a function`(**원인과 다른 문구**).
- 내부 자료구조(해시 테이블인지 무엇인지) — 명세는 "hash tables or other mechanisms that, on average, provide access times that are sublinear" 까지만 요구한다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★ **`FinalizationRegistry` 정리 잡을 언제 넣나** — `HostEnqueueFinalizationRegistryCleanupJob`. node 와 브라우저가 각자 정한다(이 배치는 node 만 돌렸다).
- `ClearKeptObjects` 를 부르는 정확한 시점 — 명세는 「동기 실행이 끝날 때」로만 적고 호스트의 잡 경계에 맡긴다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`WeakMap` 에 넣으면 **수거된다**」 → ○ 「`WeakMap` 은 대상을 **살리지 않는다**. 수거는 **될 수 있다**(명세는 보장하지 않는다)」
- ✗ 「`Map` 은 SameValueZero 로 비교하므로 `-0` 을 넣으면 `-0` 이 들어 있다」 → ○ 「**`+0` 으로 접혀 들어간다**」
- ✗ 「`FinalizationRegistry` 콜백은 gc 직후 돈다」 → ○ 「**이 판(node 20)에서** gc() 뒤 첫 매크로태스크였다. 명세는 시점을 묶지 않는다」
- ✗ 「`Map` 이 객체보다 빠르다」 → ○ **안 쟀다**
- ✗ 「`getOrInsertComputed is not a function` 이면 그 판에 메서드가 없다」 → ○ 「**콜백이 함수가 아니어도 이 문구다**(Chrome 151). 판별은 `typeof Map.prototype.getOrInsertComputed` 로 한다」

## 언제 쓰고 언제 안 쓰나

- **`Map`** — 키가 **데이터**일 때(사용자 ID·객체·임의 문자열) · 크기를 자주 셀 때 · **키 이름을 믿을 수 없을 때**(`"__proto__"`·`"constructor"` 가 들어올 수 있는 입력).
- **평범한 객체** — 필드 이름이 **코드에 적힌 레코드** · JSON 으로 그대로 오가야 할 때.
- **`Set`** — 중복 제거·포함 검사. 합·교·차는 ES2025 메서드(판 확인). `NaN` 도 한 번만 들어간다.
- **`WeakMap`** — 남의 객체에 데이터를 **덧붙이되 그 객체의 수명을 늘리지 않을 때**(DOM 노드별 상태 · 객체별 캐시 · 비공개 데이터).
- **`WeakRef`/`FinalizationRegistry`** — **거의 쓰지 않는다.** 명세의 비보장 문장이 이유다. 캐시의 보조 청소 정도.
- ★ **안 쓰는 자리** — `WeakMap` 으로 목록을 만들려 할 때(순회가 없다) · 정리가 **반드시** 일어나야 할 때(콜백은 보장이 아니다).

## 핵심 문장

1. ★★★ `Map` 키 · `Set` · `includes` 는 **SameValueZero** 한 가족이고, 8×7 격자에서 `Map` 키와 **9 / 56 칸**이 갈렸다 — 갈린 자리는 전부 `NaN` · `-0` · 강제 변환 · 문자열화다.
2. ★★★ `Map`/`Set` 은 키를 **들어갈 때 `-0` → `+0` 으로 접는다** — 저장된 키가 바뀐다.
3. ★★★ 평범한 객체는 키를 **글자로 바꾼다** — 객체 키가 한 칸으로 뭉개지고, `"__proto__"` 대입은 프로토타입을 바꾸고, 물려받은 이름이 이미 있다. `JSON.stringify(map)` 은 `{}` 다.
4. ★★★ `WeakMap` 은 키를 **살리지 않는다**(보통 `Map` 은 살린다). 그리고 **키를 꺼내 볼 창을 명세가 일부러 안 준다** — 수명이 새지 않게.
5. ★★★ **GC 는 명세가 보장하지 않는다** — "or never at all". `20/20` 은 이 판의 관찰이고, 보장은 「붙잡힌 것은 안 죽는다」 쪽뿐이다.

## 관련 자료

- [ECMA-262 — Keyed Collections](https://tc39.es/ecma262/multipage/keyed-collections.html) · [Executable Code and Execution Contexts](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html)(WeakRef 처리 모델) · [Managing Memory](https://tc39.es/ecma262/multipage/managing-memory.html)
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계
- [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/2-summary.md) — ★ **경계**: 그쪽은 **해시·충돌·재해싱·삽입 순서를 기억하는 구현**까지, 여기는 **JS 가 약속한 관찰 가능한 의미**부터.
- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — ★ **경계**: 그쪽은 `Map`/`Set` 의 **순회 순서와 순회 중 변경**까지, 여기는 **무엇을 같은 원소로 치나**부터.
- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) — ★ **경계**: 그쪽은 **객체의 열거 순서와 `__proto__` 리터럴 형태**, 여기는 **그것과 `Map` 의 대비**만.
- [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) — ★ **경계**: 그쪽은 **심볼과 레지스트리 자체**, 여기는 **어느 심볼이 약한 키가 되나**만.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번**(dict 키 요건) · **13번**(set) — 동작 (9)의 대비.

## 용어 풀이

- **SameValueZero** — `NaN` 끼리 같고 `+0`/`-0` 도 같은 비교. `Map`·`Set`·`includes` 가 쓴다.
- **SameValue** — `Object.is`. `+0` 과 `-0` 을 **다르다**고 본다.
- **IsStrictlyEqual** — `===`. `NaN` 은 자기와도 다르다. `indexOf` 가 쓴다.
- **`CanonicalizeKeyedCollectionKey`** — 키가 `-0` 이면 `+0` 으로 바꾸는 명세 연산. `Map`/`Set` 의 입구.
- **`ToPropertyKey`** — 객체 키로 쓸 값을 문자열(또는 심볼)로 바꾸는 연산.
- **`CanBeHeldWeakly`** — 약하게 쥘 수 있는 값인가. 객체 또는 **등록 안 된 심볼**.
- **등록된 심볼** — `Symbol.for('x')` 로 전역 레지스트리에 들어간 심볼. 같은 문자열로 언제든 다시 얻을 수 있다.
- **에피머론(ephemeron)** — 「키가 살아 있을 때만 값이 산다」는 관계. `WeakMap` 의 항목이 이렇다 — 값이 키를 가리켜도 키를 못 살린다.
- **`[[KeptAlive]]`** — 같은 동기 실행 동안 `WeakRef` 대상을 강하게 붙잡아 두는 명세상의 목록. `ClearKeptObjects` 가 비운다.
- **잡(job)** — 명세의 실행 단위. 한 잡이 끝나야 다음 잡이 시작한다. `setTimeout` 콜백·프라미스 반응이 각각 잡이다.
- **set-like** — `size`·`has`·`keys` 를 가진 객체. 집합 연산의 인자 조건.
- **Upsert** — 「없으면 넣고(insert) 있으면 그대로」 한 번에 하는 연산. ES2026 의 `getOrInsert`/`getOrInsertComputed`.
- **`--expose-gc`** — V8 플래그. 전역 `gc()` 를 연다. 언어 기능이 아니다.

## 더 들어가면

- **`WeakMap` 으로 비공개 데이터를 흉내 내던 관용구** — `#private`([16번](../16-class-syntax/2-summary.md)) 이전의 방법이다. 지금도 **남의 객체**에 덧붙일 때는 이쪽이다.
- **브라우저의 GC** — 이 배치는 `FinalizationRegistry` 를 Chrome 에서 돌리지 않았다. **안 돌렸다.**
- **`Map.groupBy`(ES2024)** · **`WeakMap` 에 심볼 키를 넣는 실전 용도** — 이 문서 밖이다. 판별 블록에도 넣지 않았다.
