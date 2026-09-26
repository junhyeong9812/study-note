# js/syntax/26 — 배열 탐색·평탄화·생성: 「구멍을 누가 건너뛰고 누가 읽나 · 찾기는 무엇으로 비교하나 · 배열을 만드는 입구 넷」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 배열의 **구멍**(프로퍼티가 아예 없는 칸)은 메서드마다 다르게 다뤄진다 — 건너뛰는 쪽과 `undefined` 로 읽는 쪽.
> 흔히 「**ES5 까지의 메서드는 건너뛰고 ES2015 부터는 읽는다**」로 외운다. 그 통설을 **구멍 하나짜리 배열 `[, 1]` × 연산 스물아홉 줄**에 들이대고,
> **통설과 어긋난 줄을 스크립트가 마지막 줄로 센다**(동작 (1)). 통설은 **거의** 맞고, 어긋난 줄이 통설 대신 쓸 규칙을 알려 준다.
> ★★ 나머지 절은 창이 바뀐다 — 찾기 메서드는 **콜백에 심은 로그**(방문한 인덱스)로, 배열 생성은 **구멍을 드러내는 출력 함수**(`<hole>`)로 본다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 2026 (17판)](https://262.ecma-international.org/17.0/) — `Array ( ...values )` · `Array.from` · `Array.fromAsync` · `Array.of` · `Array.prototype.includes`(note 셋) · `Array.prototype.indexOf` ·
>   `FindViaPredicate`(`find`·`findIndex`·`findLast`·`findLastIndex` 가 함께 쓰는 연산) · `Array.prototype.flat` · `FlattenIntoArray` · `Array.prototype.copyWithin` · `AsyncFromSyncIteratorContinuation`(`closeOnRejection`)
> - [ECMA-262 2025 (16판)](https://262.ecma-international.org/16.0/) — **`Array.fromAsync` 가 이 판에는 없다**(본문에서 그 이름을 찾아 0건)
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(`includes` 2016 · `flat`/`flatMap` 2019 · `.at()` 2022 · find from last 2023 · `Array.fromAsync` 2026)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 값·호출 로그·예외 타입과 메시지는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node` 다. **이 주제의 node 탐침은 node 18 에서도 한 글자도 같았다**(아래 대조기).
> ★★★ **`Array.fromAsync`(ES2026)는 두 node 판에 없다**(아래 판별 블록). 그 탐침은 **Google Chrome 151 을 헤드리스로** 돌렸다 —
> 배너가 `google-chrome --headless` 로 시작하는 블록이 그것이다. 페이지는 `console.log` 를 가로채 줄이 늘 때마다 `<pre>` 를 다시 쓰고,
> `--virtual-time-budget=2000` 이 **타이머를 가상 시간으로** 돌려 프라미스·타이머 뒤의 줄까지 받는다(`js24b-page.html`).
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `indexOf` · `lastIndexOf` · `forEach` · `map` · `filter` · `some` · `every` · `reduce` | **ES5** | 세 판 다 있다 |
> | `find` · `findIndex` · `fill` · `copyWithin` · `keys`/`entries` · `Array.from` · `Array.of` | **ES2015** | 세 판 다 있다 |
> | `includes` | **ES2016** | 세 판 다 있다 |
> | `flat` · `flatMap` | **ES2019** | 세 판 다 있다 |
> | `at` | **ES2022** | 세 판 다 있다 |
> | `findLast` · `findLastIndex` | **ES2023** | 세 판 다 있다(★ node 18 에도 있다 — 같은 ES2023 의 복사 메서드는 node 18 에 없다. [25번](../25-array-non-mutating-and-copy-methods/2-summary.md)) |
> | `Array.fromAsync` | **ES2026** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 구멍 하나짜리 배열 × 연산 **스물아홉 줄**. 「판이 ES5 이하면 건너뛴다」는 통설과 **어긋난 줄을 스크립트가 센다**(동작 (1)) |
> | ★★★ **① 추상 연산에 로그 심기** | 찾기 네 형제의 **방문한 인덱스**(동작 (3)) · `Array.fromAsync` 가 원본의 `next` 를 **언제 부르나**와 거부 뒤 **`finally` 가 도나**(동작 (7)) · `Array.from` 매핑 함수의 **인자 수와 `this`**(동작 (6)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `Array(2.5)` · `Array(-1)` 의 `RangeError` · `Array.from(null)` · 아주 깊은 `flat(Infinity)` · 없는 판의 `Array.fromAsync` |
> | ★ **⑤ 두 판 대조기** | **이 주제의 node 탐침 일곱 개는 두 판에서 전부 같았다.** 대조기의 `DIFFERS` 줄은 다른 주제의 탐침이다 |
> | ★ **부적용 — ③ 브랜드 태그** | 「이것이 배열인가」는 `flat` 이 `IsArray` 로 묻는 한 자리뿐이고, 그것은 동작 (5)의 `[3]` 이 **결과로** 보여 준다(`Set` 을 안 편다). 태그를 따로 읽을 거리가 없다 — **잴 것이 없다** |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 가 한 줄도 없다. 전부 런타임 의미다 — **잴 것이 없다** |
> | ★ **안 쟀다 — 성능** | 「`find` 가 `filter` 보다 빠르다」·「`includes` 가 `indexOf` 보다 느리다」·「`flat` 은 비싸다」를 **한 줄도 쓰지 않는다.** 콜백 **호출 횟수만** 셌다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구** — V8 의 글자다(`Invalid array length` · `Maximum call stack size exceeded` · `object null is not iterable …`). 종류만 명세가 정한다 | ★★★ 격자의 `skips`/`reads` 와 「**N / M**」 · 돌려받은 배열의 **구멍 위치** · 찾기 메서드의 **반환값과 방문한 인덱스** |
> | ★ **아주 깊은 배열에서 `flat(Infinity)` 가 터지는 깊이** — 명세에는 한계가 없고, 스택 크기는 엔진·설정의 몫이다. 이 판에서 10만 겹이 `RangeError` 였을 뿐이다(재대조에서는 안 흔들렸다) | ★★ `Array.fromAsync` 로그의 **`next`/`settle` 순서** — 타이머가 가상 시간이라 기계 속도에 안 매인다(재대조 동일) |
>
> **선행** — [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md)(★★★ `indexOf`/`includes` 가 `NaN` 에서 갈리는 것 — 거기서 쟀다) ·
> [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md)(구멍은 **프로퍼티가 없는 칸**이다 — `for-in` 은 건너뛰고 `for-of` 는 방문) ·
> [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md)(스프레드와 `Array.from` 이 구멍을 채우고 `slice` 는 남긴다) ·
> [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(`Array.from` 이 이터러블과 유사 배열을 **둘 다** 받는다) ·
> [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md)(`find`·`some`·`every` 는 배열판도 도중에 멈춘다) ·
> [24 — 배열 변형 메서드](../24-array-mutating-methods/2-summary.md)(이 주제가 갈라져 나온 곳).
> **이어지는 곳** — [25 — 배열 비변형·복사 메서드](../25-array-non-mutating-and-copy-methods/2-summary.md) · [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md).
>
> ★★ **경계 — `NaN` 에서 `indexOf` 와 `includes` 가 갈리는 것은 23번이 정본이다**(비교 격자 `9 / 56`). 여기서는 인용만 하고 **`-0` 과 구멍**으로 넓힌다.
> ★★ **경계 — 스프레드·`apply`·`Array.from` 이 무엇을 받는가는 11번·19번이 정본이다.** 여기서는 `Array.from` 의 **매핑 함수·길이만 있는 객체·`Array(n)` 과의 짝**만 본다.
> ★ **경계 — `sort` 가 구멍을 끝으로 보내는 규칙은 24번이 정본이다.** 격자에는 `skips` 한 칸으로만 들어간다.

```sh
# js24b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 그리고 판별 기능 표(js24b-features.js)를 세 판에 던진다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'console.log("node " + process.versions.node + "  v8 " + process.versions.v8)'
  "$n" js24b-features.js
done
google-chrome --version | sed 's/ *$//'
google-chrome --headless --virtual-time-budget=2000 --dump-dom "file://$PWD/js24b-page.html?js24b-features.js" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d'
```
```js
// js24b-features.js
// 이 문서의 기능이 이 판에 있나 -- 판마다 같은 스크립트를 던진다(node 두 판 · Chrome).
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no (" + e.constructor.name + ")"; }
  console.log("  " + label.padEnd(52) + r);
};
has("ES2015  Array.from / Array.of / fill / copyWithin", () => [Array.from, Array.of, [].fill, [].copyWithin].every((f) => typeof f === "function"));
has("ES2015  find / findIndex", () => typeof [].find === "function" && typeof [].findIndex === "function");
has("ES2016  includes", () => typeof [].includes === "function");
has("ES2017  Object.values / Object.entries", () => typeof Object.values === "function" && typeof Object.entries === "function");
has("ES2019  flat / flatMap", () => typeof [].flat === "function" && typeof [].flatMap === "function");
has("ES2019  Object.fromEntries", () => typeof Object.fromEntries === "function");
has("ES2022  Array.prototype.at", () => typeof [].at === "function");
has("ES2022  Object.hasOwn", () => typeof Object.hasOwn === "function");
has("ES2023  findLast / findLastIndex", () => typeof [].findLast === "function" && typeof [].findLastIndex === "function");
has("ES2023  toSorted / toReversed / toSpliced / with", () => ["toSorted", "toReversed", "toSpliced", "with"].every((k) => typeof [][k] === "function"));
has("ES2024  Object.groupBy", () => typeof Object.groupBy === "function");
has("ES2024  Map.groupBy", () => typeof Map.groupBy === "function");
has("ES2026  Array.fromAsync", () => typeof Array.fromAsync === "function");
```
```text
===== ./js24b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  Array.from / Array.of / fill / copyWithin   yes
  ES2015  find / findIndex                            yes
  ES2016  includes                                    yes
  ES2017  Object.values / Object.entries              yes
  ES2019  flat / flatMap                              yes
  ES2019  Object.fromEntries                          yes
  ES2022  Array.prototype.at                          yes
  ES2022  Object.hasOwn                               yes
  ES2023  findLast / findLastIndex                    yes
  ES2023  toSorted / toReversed / toSpliced / with    no
  ES2024  Object.groupBy                              no
  ES2024  Map.groupBy                                 no
  ES2026  Array.fromAsync                             no
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  Array.from / Array.of / fill / copyWithin   yes
  ES2015  find / findIndex                            yes
  ES2016  includes                                    yes
  ES2017  Object.values / Object.entries              yes
  ES2019  flat / flatMap                              yes
  ES2019  Object.fromEntries                          yes
  ES2022  Array.prototype.at                          yes
  ES2022  Object.hasOwn                               yes
  ES2023  findLast / findLastIndex                    yes
  ES2023  toSorted / toReversed / toSpliced / with    yes
  ES2024  Object.groupBy                              no
  ES2024  Map.groupBy                                 no
  ES2026  Array.fromAsync                             no
Google Chrome 151.0.7922.173
  ES2015  Array.from / Array.of / fill / copyWithin   yes
  ES2015  find / findIndex                            yes
  ES2016  includes                                    yes
  ES2017  Object.values / Object.entries              yes
  ES2019  flat / flatMap                              yes
  ES2019  Object.fromEntries                          yes
  ES2022  Array.prototype.at                          yes
  ES2022  Object.hasOwn                               yes
  ES2023  findLast / findLastIndex                    yes
  ES2023  toSorted / toReversed / toSpliced / with    yes
  ES2024  Object.groupBy                              yes
  ES2024  Map.groupBy                                 yes
  ES2026  Array.fromAsync                             yes
```

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 이 주제의 탐침(`js24b-26…`)은 전부 `identical` 이다. 대조기 전문은 [3-answer.md](3-answer.md) 의 7번에 있다.

`identical 26  ·  differs 4  ·  total 30`

브라우저 탐침을 돌리는 페이지(`js24b-page.html`)의 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

## 한눈에 — 쉽게 말하면

**배열의 구멍은 「빈 상자」가 아니라 「상자가 아예 없는 자리」** 다.
`[, 1]` 은 선반에 자리가 두 개인데 **0번 자리에는 상자가 놓여 있지 않다.** `length` 는 2 다.
선반을 훑는 사람은 두 부류로 나뉜다 —

- ★★★ **「상자 있어요?」부터 묻는 사람**(`HasProperty`) — 없으면 **그냥 지나간다.** `forEach` · `map` · `filter` · `indexOf` · `flat`.
- ★★★ **묻지 않고 자리를 읽는 사람**(`Get` 만) — 없는 상자를 **「안에 `undefined` 가 들었다」로** 읽는다. `find` · `includes` · `at` · `Array.from` · 스프레드.
- ★★ **어느 부류인지는 「언제 생긴 메서드인가」와 거의 겹치지만 딱 맞지는 않는다** — 동작 (1)이 그 어긋남을 센다.

```text
   선반  arr = [ , 1 ]          length 2 ,  0 in arr  ->  false

        자리 0          자리 1
       ┌ ─ ─ ┐         ┌─────┐
       │ 없음 │         │  1  │
       └ ─ ─ ┘         └─────┘

   「있어요?」부터 묻는 쪽 (HasProperty)       묻지 않고 읽는 쪽 (Get)
   ----------------------------------         -----------------------
   자리 0 은 건너뛴다                          자리 0 을 undefined 로 읽는다
   forEach 콜백: 자리 1 만                     find 콜백: 자리 0, 자리 1
   map 결과:   [<hole>, 1]                    [...arr]:  [undefined, 1]
   indexOf(undefined) -> -1                   includes(undefined) -> true
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 상자가 아예 없는 자리 | **구멍** — 그 인덱스의 프로퍼티가 없다 | `i in arr` 이 `false` |
| 「상자 있어요?」 | `HasProperty(O, Pk)` | 명세 알고리즘의 반복 단계 |
| 묻지 않고 읽기 | `Get(O, Pk)` 만 — 없으면 `undefined` | 동작 (1)의 `reads` 줄 |
| 빈 상자(`undefined` 가 든 상자) | 프로퍼티가 **있고** 값이 `undefined` | `[undefined, 1]` 의 `0 in` 이 `true` |
| 선반 길이 | `length` — 상자 수가 아니라 **자리 수** | `Array(3).length` 가 3 인데 상자는 0 개 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**`Array(5).map((_, i) => i)` 가 `[0,1,2,3,4]` 가 아니라 빈 배열 같은 것을 준다**」와
「**`indexOf(undefined)` 로 빈 칸을 찾았는데 -1 이 나온다**」가 그것이다.
둘 다 **상자가 없는 자리를 「있어요?」부터 묻는 사람에게** 맡긴 것이다.

> **구멍(hole)** — 배열에서 인덱스는 `length` 안에 있는데 **그 인덱스의 프로퍼티가 없는** 자리. 값이 `undefined` 인 칸과 다르다.\
> 예: `[, 1]` 의 0번 · `Array(3)` 의 세 자리 전부.

> **`HasProperty`** — 「이 객체(또는 그 프로토타입 체인)에 이 키가 있나」를 묻는 명세 연산. `in` 연산자가 쓰는 것이다.\
> 예: `0 in [, 1]` 이 `false`.

> **희소 배열(sparse array)** — 구멍이 하나라도 있는 배열. 반대말은 빽빽한 배열(dense array).

## 이 주제가 답하려는 질문

1. **구멍을 어느 메서드가 건너뛰고 어느 메서드가 `undefined` 로 읽나** — 「ES5 는 건너뛴다」는 통설은 어디까지 맞나?
2. **찾기 메서드들은 무엇으로 비교하고 어디서 멈추나** — `indexOf`·`includes`·`find` 네 형제·`at` 이 `NaN`·`-0`·음수 인덱스에서 어떻게 갈리나?
3. **배열을 만드는 입구 넷**(`Array(n)` · `Array.of` · `Array.from` · `Array.fromAsync`)은 각각 무엇을 받고 무엇을 만드나 — 구멍이 남나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 구멍 하나 × 연산 스물아홉 줄 — 이 주제의 본체

**언제 쓰나** — `Array(n)` 이나 `delete arr[i]` 로 생긴 배열을 메서드에 넘길 때 · 서버가 준 희소 배열을 그대로 돌릴 때.
★★★ 통설을 문장으로 외우면 **어긋난 줄에서** 반드시 틀린다. 그래서 전부 들이댔다.

```js
// js24b-26a-hole-grid.js
// arr = [, 1] -- index 0 is a hole (no property at all), index 1 holds 1.
// Each row asks the same question of one operation: at the hole, does it skip, or does it read undefined?
// The "rule" column is the folk rule under test: edition <= ES5 -> skips, ES2015 or later -> reads.
const make = () => [, 1];
const show = (a) => "[" + Array.from({ length: a.length }, (_, i) => (i in a ? String(a[i]) : "<hole>")).join(",") + "]";
const visits = (run) => { const seen = []; run((v, i) => { seen.push(i); }); return seen.includes(0) ? "reads" : "skips"; };
const kept = (r) => (0 in r ? "reads" : "skips");

const rows = [
  // [operation, edition, measure() -> "reads" | "skips", detail()]
  ["forEach",            "ES5",    () => visits((f) => make().forEach(f)),                          () => ""],
  ["map",                "ES5",    () => kept(make().map((x) => x)),                                () => show(make().map((x) => x))],
  ["filter",             "ES5",    () => visits((f) => make().filter((v, i) => { f(v, i); return true; })), () => show(make().filter(() => true))],
  ["some",               "ES5",    () => visits((f) => make().some((v, i) => { f(v, i); return false; })),  () => ""],
  ["every",              "ES5",    () => visits((f) => make().every((v, i) => { f(v, i); return true; })),  () => ""],
  ["reduce",             "ES5",    () => visits((f) => make().reduce((acc, v, i) => { f(v, i); return acc; }, 0)), () => ""],
  ["indexOf(undefined)", "ES5",    () => (make().indexOf(undefined) === 0 ? "reads" : "skips"),     () => String(make().indexOf(undefined))],
  ["lastIndexOf(undef)", "ES5",    () => (make().lastIndexOf(undefined) === 0 ? "reads" : "skips"), () => String(make().lastIndexOf(undefined))],
  ["slice()",            "ES3",    () => kept(make().slice()),                                      () => show(make().slice())],
  ["concat()",           "ES3",    () => kept(make().concat()),                                     () => show(make().concat())],
  ["reverse()",          "ES3",    () => kept(make().reverse().reverse()),                          () => show(make().reverse())],
  ["sort()",             "ES3",    () => { const r = make().sort(); return r.length - 1 in r ? "reads" : "skips"; }, () => show(make().sort())],
  ["join('-')",          "ES3",    () => "(n/a)",                                                   () => JSON.stringify(make().join("-"))],
  ["for-in",             "ES3",    () => { const ks = []; for (const k in make()) ks.push(k); return ks.includes("0") ? "reads" : "skips"; }, () => ""],
  ["find",               "ES2015", () => visits((f) => make().find((v, i) => { f(v, i); return false; })),  () => ""],
  ["findIndex",          "ES2015", () => visits((f) => make().findIndex((v, i) => { f(v, i); return false; })), () => ""],
  ["fill(0)",            "ES2015", () => kept(make().fill(0)),                                      () => show(make().fill(0))],
  ["copyWithin(1, 0)",   "ES2015", () => { const r = make().copyWithin(1, 0); return 1 in r ? "reads" : "skips"; }, () => show(make().copyWithin(1, 0))],
  ["keys()",             "ES2015", () => ([...make().keys()].includes(0) ? "reads" : "skips"),     () => JSON.stringify([...make().keys()])],
  ["entries()",          "ES2015", () => ([...make().entries()].some(([i]) => i === 0) ? "reads" : "skips"), () => JSON.stringify([...make().entries()])],
  ["for-of",             "ES2015", () => { const vs = []; for (const v of make()) vs.push(v); return vs.length === 2 ? "reads" : "skips"; }, () => ""],
  ["[...arr]",           "ES2015", () => kept([...make()]),                                         () => show([...make()])],
  ["Array.from(arr)",    "ES2015", () => kept(Array.from(make())),                                  () => show(Array.from(make()))],
  ["includes(undefined)","ES2016", () => (make().includes(undefined) ? "reads" : "skips"),         () => String(make().includes(undefined))],
  ["flat()",             "ES2019", () => (make().flat().length === 2 ? "reads" : "skips"),                                       () => show(make().flat())],
  ["flatMap(x => [x])",  "ES2019", () => visits((f) => make().flatMap((v, i) => { f(v, i); return [v]; })),                          () => show(make().flatMap((x) => [x]))],
  ["at(0)",              "ES2022", () => "(n/a)",                                                   () => String(make().at(0))],
  ["findLast",           "ES2023", () => visits((f) => make().findLast((v, i) => { f(v, i); return false; })), () => ""],
  ["findLastIndex",      "ES2023", () => visits((f) => make().findLastIndex((v, i) => { f(v, i); return false; })), () => ""],
];

const ruleOf = (ed) => (ed === "ES3" || ed === "ES5" ? "skips" : "reads");
console.log("arr = [, 1]   (0 in arr) = " + (0 in make()) + "   length = " + make().length);
console.log("");
console.log("operation            edition  measured  rule    detail");
let asked = 0, off = 0;
for (const [name, ed, measure, detail] of rows) {
  const m = measure();
  const r = ruleOf(ed);
  let mark = "";
  if (m !== "(n/a)") { asked++; if (m !== r) { off++; mark = "  <- differs"; } }
  console.log(name.padEnd(21) + ed.padEnd(9) + m.padEnd(10) + r.padEnd(8) + (detail() + mark).trim());
}
console.log("");
console.log("rows where the edition rule misses: " + off + " / " + asked);
```
```text
===== node20 js24b-26a-hole-grid.js (exit=0) =====
arr = [, 1]   (0 in arr) = false   length = 2

operation            edition  measured  rule    detail
forEach              ES5      skips     skips   
map                  ES5      skips     skips   [<hole>,1]
filter               ES5      skips     skips   [1]
some                 ES5      skips     skips   
every                ES5      skips     skips   
reduce               ES5      skips     skips   
indexOf(undefined)   ES5      skips     skips   -1
lastIndexOf(undef)   ES5      skips     skips   -1
slice()              ES3      skips     skips   [<hole>,1]
concat()             ES3      skips     skips   [<hole>,1]
reverse()            ES3      skips     skips   [1,<hole>]
sort()               ES3      skips     skips   [1,<hole>]
join('-')            ES3      (n/a)     skips   "-1"
for-in               ES3      skips     skips   
find                 ES2015   reads     reads   
findIndex            ES2015   reads     reads   
fill(0)              ES2015   reads     reads   [0,0]
copyWithin(1, 0)     ES2015   skips     reads   [<hole>,<hole>]  <- differs
keys()               ES2015   reads     reads   [0,1]
entries()            ES2015   reads     reads   [[0,null],[1,1]]
for-of               ES2015   reads     reads   
[...arr]             ES2015   reads     reads   [undefined,1]
Array.from(arr)      ES2015   reads     reads   [undefined,1]
includes(undefined)  ES2016   reads     reads   true
flat()               ES2019   skips     reads   [1]  <- differs
flatMap(x => [x])    ES2019   skips     reads   [1]  <- differs
at(0)                ES2022   (n/a)     reads   undefined
findLast             ES2023   reads     reads   
findLastIndex        ES2023   reads     reads   

rows where the edition rule misses: 3 / 27
```

```text
   통설  「판이 ES5 이하면 건너뛴다, ES2015 부터는 읽는다」

            ES3 / ES5                      ES2015 이후
          ┌──────────────────────┐       ┌───────────────────────────────┐
   skips  │ forEach map filter   │       │ copyWithin        <- 어긋남    │
          │ some every reduce    │       │ flat  flatMap     <- 어긋남    │
          │ indexOf lastIndexOf  │       │                               │
          │ slice concat reverse │       │                               │
          │ sort  for-in         │       │                               │
          ├──────────────────────┤       ├───────────────────────────────┤
   reads  │ (없음)               │       │ find findIndex findLast(Index)│
          │                      │       │ fill keys entries for-of      │
          │                      │       │ [...arr] Array.from includes  │
          └──────────────────────┘       └───────────────────────────────┘

   왼쪽 열은 통설대로 전부 skips.  오른쪽 열에 skips 가 세 줄 섞여 있다.
```

- ★★★ **집계 줄 — `rows where the edition rule misses: 3 / 27`.** 셀 수 있는 스물일곱 줄(`join`·`at(0)` 두 줄은 「건너뛰나」를 물을 거리가 없어 `(n/a)`) 가운데 **스물넷이 통설대로**다.
- ★★★ **어긋난 셋 — `copyWithin`(ES2015) · `flat` · `flatMap`(ES2019)** 은 **새 판인데 건너뛴다.**
  `flat()` 이 `[, 1]` 을 **`[1]`** 로 만든다 — 구멍이 **사라진다**(`undefined` 로 채워지지 않는다). `copyWithin(1, 0)` 은 구멍을 **복사해** `[<hole>,<hole>]` 이 된다.
- ★★★ **ES5 쪽에는 어긋난 줄이 없다** — 오래된 메서드 가운데 구멍을 `undefined` 로 **읽는** 것은 하나도 없었다.
- ★★ **「건너뛴다」의 결과는 셋으로 갈린다** — `map`·`slice`·`concat`·`reverse` 는 **구멍을 그대로 옮기고**(`[<hole>,1]`), `filter`·`flat` 은 **구멍을 지우고**(`[1]`), `forEach`·`some`·`reduce` 는 콜백을 **안 부를 뿐**이다.
- ★★ **`reads` 의 결과** — `[...arr]` · `Array.from(arr)` 은 **`[undefined,1]`**: 구멍이 **빈 상자**로 바뀐다(`0 in` 이 `true`). 11번의 `[3]` 블록이 `[1, , 3]` 으로 같은 것을 봤다.
  `entries()` 의 `[[0,null],[1,1]]` 에서 `null` 은 `JSON.stringify` 가 `undefined` 를 배열 안에서 `null` 로 찍은 것이다.
- ★ **`sort()` 는 `skips`** — 구멍을 **끝으로 보낸다**(`[1,<hole>]`). 그 규칙의 정본은 [24번](../24-array-mutating-methods/2-summary.md)이다.

**그러면 통설 대신 무엇으로 외우나** — 어긋난 셋의 명세 알고리즘을 읽으면 공통점이 하나다.

```text
   반복 단계에 이 한 줄이 있나?          있다 -> skips          없다 -> reads
   ---------------------------          ------------            ------------
   Let kPresent be ? HasProperty(O, Pk)  indexOf  (ES5)          includes (ES2016)
                                         FlattenIntoArray        FindViaPredicate
                                           (flat · flatMap)        (find 네 형제)
                                         copyWithin              at · fill · Array.from
```

- ★★★ **판(edition)이 아니라 「알고리즘이 `HasProperty` 를 먼저 묻느냐」가 가른다.** 명세 `FlattenIntoArray` 는 원소마다 `Let exists be ? HasProperty(source, P)` 를 먼저 묻고,
  `copyWithin` 은 `Let fromPresent be ? HasProperty(O, fromKey)` 뒤에 **없으면 `DeletePropertyOrThrow`** 한다 — 그래서 구멍이 **복사**된다.
- ★★ **통설이 거의 맞는 이유** — ES2015 이후에 들어온 메서드는 **대부분** `HasProperty` 없이 `Get` 만 쓰도록 설계됐다. `flat` 은 ES2019 이지만 `forEach` 식 반복을 따랐다.
- ★ `includes` 의 note 가 이것을 한 문장으로 적는다 — 동작 (2).

### (2) ★★ 찾는 값이 `-0`·`NaN`·`undefined` 일 때 — `indexOf` 와 `includes`

**언제 쓰나** — 「이 값이 배열에 있나」를 물을 때 · 찾는 값이 계산 결과(`NaN`·`-0` 이 나올 수 있는)일 때.

```js
// js24b-26b-zero-and-nan.js
// Three searches, three signed/unsigned zero arrangements, and NaN.
// Each line prints the raw return value -- no interpretation.
const row = (label, v) => console.log("  " + label.padEnd(44) + String(v));

console.log("[1] searching for -0 in [0]");
row("[0].indexOf(-0)", [0].indexOf(-0));
row("[0].lastIndexOf(-0)", [0].lastIndexOf(-0));
row("[0].includes(-0)", [0].includes(-0));

console.log("[2] searching for 0 in [-0]");
row("[-0].indexOf(0)", [-0].indexOf(0));
row("[-0].includes(0)", [-0].includes(0));

console.log("[3] which zero comes back");
const found = [-0].find((x) => x === 0);
row("Object.is([-0].find(x => x === 0), -0)", Object.is(found, -0));
row("Object.is([-0].at(0), -0)", Object.is([-0].at(0), -0));
row("[0, -0].findIndex(x => Object.is(x, -0))", [0, -0].findIndex((x) => Object.is(x, -0)));

console.log("[4] NaN, and the ways to find it");
row("[NaN].indexOf(NaN)", [NaN].indexOf(NaN));
row("[NaN].lastIndexOf(NaN)", [NaN].lastIndexOf(NaN));
row("[NaN].includes(NaN)", [NaN].includes(NaN));
row("[NaN].findIndex(Number.isNaN)", [NaN].findIndex(Number.isNaN));
row("[NaN].findIndex(x => x !== x)", [NaN].findIndex((x) => x !== x));

console.log("[5] fromIndex -- the second argument");
row("[1, 2, 1].indexOf(1, 1)", [1, 2, 1].indexOf(1, 1));
row("[1, 2, 1].indexOf(1, -1)", [1, 2, 1].indexOf(1, -1));
row("[1, 2, 1].lastIndexOf(1, -2)", [1, 2, 1].lastIndexOf(1, -2));
row("[1, 2, 1].includes(1, 3)", [1, 2, 1].includes(1, 3));
row("[1, 2, 1].includes(1, -100)", [1, 2, 1].includes(1, -100));

console.log("[6] strict comparison, no coercion");
row("['1'].indexOf(1)", ["1"].indexOf(1));
row("['1'].includes(1)", ["1"].includes(1));
row("[[1]].includes([1])", [[1]].includes([1]));
```
```text
===== node20 js24b-26b-zero-and-nan.js (exit=0) =====
[1] searching for -0 in [0]
  [0].indexOf(-0)                             0
  [0].lastIndexOf(-0)                         0
  [0].includes(-0)                            true
[2] searching for 0 in [-0]
  [-0].indexOf(0)                             0
  [-0].includes(0)                            true
[3] which zero comes back
  Object.is([-0].find(x => x === 0), -0)      true
  Object.is([-0].at(0), -0)                   true
  [0, -0].findIndex(x => Object.is(x, -0))    1
[4] NaN, and the ways to find it
  [NaN].indexOf(NaN)                          -1
  [NaN].lastIndexOf(NaN)                      -1
  [NaN].includes(NaN)                         true
  [NaN].findIndex(Number.isNaN)               0
  [NaN].findIndex(x => x !== x)               0
[5] fromIndex -- the second argument
  [1, 2, 1].indexOf(1, 1)                     2
  [1, 2, 1].indexOf(1, -1)                    2
  [1, 2, 1].lastIndexOf(1, -2)                0
  [1, 2, 1].includes(1, 3)                    false
  [1, 2, 1].includes(1, -100)                 true
[6] strict comparison, no coercion
  ['1'].indexOf(1)                            -1
  ['1'].includes(1)                           false
  [[1]].includes([1])                         false
```

```text
                         NaN 을 찾으면      -0 과 +0      구멍을 undefined 로 찾으면     비교
                         -------------      --------      -------------------------     ----
   indexOf/lastIndexOf   못 찾는다 (-1)     같다          못 찾는다 (-1)  건너뛴다       IsStrictlyEqual (===)
   includes              찾는다 (true)      같다          찾는다 (true)   읽는다         SameValueZero
   findIndex(pred)       pred 가 정한다     pred 가 정한다  읽는다                       사용자 함수

   ★ 두 메서드는 「비교 규칙」과 「구멍」 두 축에서 동시에 갈린다
```

- ★★★ **`-0` 에서는 안 갈린다** — `[0].indexOf(-0)` 이 `0`, `[0].includes(-0)` 이 `true`, `[-0].indexOf(0)` 도 `0`. `===` 도 SameValueZero 도 **부호를 안 가린다.** 부호를 가리는 것은 `Object.is`(SameValue) 하나뿐이다(23번 격자의 `0, -0` 행 — 여덟 자리 중 `Object.is` 만 n).
- ★★★ **`NaN` 에서 갈린다** — `[NaN].indexOf(NaN)` · `lastIndexOf` 는 `-1`, `includes` 는 `true`. 23번이 이미 잰 것과 같다(`indexOf` 열 `1 / 8`).
  ★ **인덱스가 필요하면 `findIndex(Number.isNaN)`** — `0` 을 돌려준다. `x !== x` 도 된다(`NaN` 만 자기와 다르다).
- ★★★ **배열은 `-0` 을 그대로 들고 있다** — `Object.is([-0].at(0), -0)` 이 **`true`**, `find` 가 돌려준 값도 `-0` 이다. `Map` 은 **넣을 때 `+0` 으로 바꿔 저장했다**(23번 동작 (2)). 배열에는 **`CanonicalizeKeyedCollectionKey` 같은 입구가 없다.**
- ★★ **구멍 축** — 동작 (1)의 `indexOf(undefined)` 가 `-1`, `includes(undefined)` 가 `true`. 명세 `includes` 의 note 가 두 차이를 나란히 적는다 —
  > "This method intentionally differs from the similar indexOf method in two ways. First, it uses the SameValueZero algorithm, instead of IsStrictlyEqual, allowing it to detect NaN array elements. Second, it does not skip missing array elements, instead treating them as undefined."
- ★ **`[5]` `fromIndex`** — 음수면 `length + fromIndex` 에서 시작하고(`indexOf(1, -1)` 이 `2`), 너무 작으면 0 으로 붙는다(`includes(1, -100)` 이 `true`). `lastIndexOf` 는 거기서 **거꾸로** 간다.
- ★ **`[6]` 강제 변환도 정체 비교도 없다** — `['1'].includes(1)` 은 `false`, `[[1]].includes([1])` 은 `false`(모양이 같은 다른 배열).

### (3) ★★ 찾기 네 형제 — 어디서 시작해 어디서 멈추나

**언제 쓰나** — 조건에 맞는 **첫** 원소(또는 마지막 원소)만 필요할 때.

```js
// js24b-26c-find-family.js
// find / findIndex / findLast / findLastIndex on the same array, with a logging predicate.
const arr = [5, 12, 8, 130, 44];
const run = (name, call) => {
  const log = [];
  const pred = (v, i) => { log.push(i); return v > 10; };
  const result = call(pred);
  console.log("  " + name.padEnd(16) + "result " + String(result).padEnd(12) + "visited indexes " + JSON.stringify(log));
};

console.log("[1] predicate v > 10 on " + JSON.stringify(arr));
run("find", (p) => arr.find(p));
run("findIndex", (p) => arr.findIndex(p));
run("findLast", (p) => arr.findLast(p));
run("findLastIndex", (p) => arr.findLastIndex(p));
run("filter", (p) => JSON.stringify(arr.filter(p)));

console.log("[2] nothing matches");
const none = () => false;
console.log("  find           " + String(arr.find(none)));
console.log("  findIndex      " + String(arr.findIndex(none)));
console.log("  findLast       " + String(arr.findLast(none)));
console.log("  findLastIndex  " + String(arr.findLastIndex(none)));

console.log("[3] a matching element whose value is undefined");
const withUndef = [1, undefined, 3];
console.log("  find(v => v === undefined)       " + String(withUndef.find((v) => v === undefined)));
console.log("  findIndex(v => v === undefined)  " + String(withUndef.findIndex((v) => v === undefined)));

console.log("[4] the array grows during find -- how many calls?");
const grow = [1, 2, 3];
let calls = 0;
const r4 = grow.find((v) => { calls++; if (grow.length < 6) grow.push(v * 10); return false; });
console.log("  result " + String(r4) + "   calls " + calls + "   array now " + JSON.stringify(grow));

console.log("[5] an element is deleted during find");
const del = [1, 2, 3];
const seen = [];
del.find((v, i) => { seen.push(String(v)); if (i === 0) delete del[1]; return false; });
console.log("  values the predicate saw " + JSON.stringify(seen));
```
```text
===== node20 js24b-26c-find-family.js (exit=0) =====
[1] predicate v > 10 on [5,12,8,130,44]
  find            result 12          visited indexes [0,1]
  findIndex       result 1           visited indexes [0,1]
  findLast        result 44          visited indexes [4]
  findLastIndex   result 4           visited indexes [4]
  filter          result [12,130,44] visited indexes [0,1,2,3,4]
[2] nothing matches
  find           undefined
  findIndex      -1
  findLast       undefined
  findLastIndex  -1
[3] a matching element whose value is undefined
  find(v => v === undefined)       undefined
  findIndex(v => v === undefined)  1
[4] the array grows during find -- how many calls?
  result undefined   calls 3   array now [1,2,3,10,20,30]
[5] an element is deleted during find
  values the predicate saw ["1","undefined","3"]
```

```text
   arr = [5, 12, 8, 130, 44]      pred = v > 10

   인덱스       0    1    2    3    4
   find        ▶ .  ▶ ✓                      멈춘다   결과 12   방문 [0,1]
   findIndex   ▶ .  ▶ ✓                      멈춘다   결과 1    방문 [0,1]
   findLast                        ✓ ◀       멈춘다   결과 44   방문 [4]
   findLastIndex                   ✓ ◀       멈춘다   결과 4    방문 [4]
   filter      ▶    ▶    ▶    ▶    ▶         끝까지   결과 [12,130,44]

   못 찾으면   find / findLast -> undefined      findIndex / findLastIndex -> -1
```

- ★★★ **`find`·`findIndex` 는 처음 맞은 자리에서 멈춘다**(방문 `[0,1]`), **`findLast`·`findLastIndex` 는 끝에서 시작해** 첫 맞은 자리에서 멈춘다(방문 `[4]` — 한 번). `filter` 는 다섯 번 다 부른다.
  ★ 21번이 `find(x > 3)` 을 배열판·헬퍼판 모두 **`4 / 4`** 로 셌다 — **배열의 `find` 도 원래 도중에 멈춘다**는 같은 사실이다.
- ★★ **못 찾으면** — 값을 돌려주는 쪽은 `undefined`, 인덱스를 돌려주는 쪽은 `-1`.
- ★★★ **`[3]` `find` 의 `undefined` 는 두 뜻이다** — `[1, undefined, 3].find(v => v === undefined)` 는 **찾아서** `undefined` 를 돌려줬는데, 못 찾은 것과 글자가 같다. **찾았는지가 중요하면 `findIndex` 로** 묻는다(`1`).
- ★★ **`[4]` 방문 범위는 시작할 때 정해진다** — 도는 동안 세 개를 덧붙였는데 콜백은 **3번**만 불렸다. 명세 `FindViaPredicate` 의 note — "The range of elements processed is set before the first call to predicate … Elements that are appended to the array after this will not be visited by predicate."
- ★★ **`[5]` 도는 중에 지운 자리도 방문한다** — 값은 `undefined`(`["1","undefined","3"]`). 같은 note — "Elements that are deleted after traversal begins and before being visited are still visited and are either looked up from the prototype or are undefined." **`find` 가 구멍을 읽는 것과 같은 성질**이다(동작 (1)).

### (4) ★★ `at(i)` — 음수는 끝에서 센다, 괄호 접근은 안 센다

**언제 쓰나** — 마지막 원소가 필요할 때(`arr[arr.length - 1]` 대신).

```js
// js24b-26d-at.js
// at(i) against bracket access arr[i], on the same array.
const arr = ["a", "b", "c"];
const row = (label, v) => console.log("  " + label.padEnd(52) + JSON.stringify(v === undefined ? "<undefined>" : v));

console.log("[1] negative and out-of-range indexes");
for (const i of [0, 2, -1, -3, -4, 3]) {
  console.log("  i = " + String(i).padEnd(4) + "at(i) " + String(arr.at(i)).padEnd(12) + "arr[i] " + String(arr[i]));
}

console.log("[2] non-integer arguments");
row("arr.at(1.7)", arr.at(1.7));
row("arr.at(-1.7)", arr.at(-1.7));
row("arr.at('1')", arr.at("1"));
row("arr.at(NaN)", arr.at(NaN));
row("arr.at()", arr.at());
row("arr.at(-0)", arr.at(-0));
row("arr['1.7']", arr["1.7"]);

console.log("[3] what arr[-1] = v does");
const w = ["a", "b", "c"];
w[-1] = "z";
console.log("  length " + w.length + "   keys " + JSON.stringify(Object.keys(w)) + "   at(-1) " + w.at(-1));

console.log("[4] the same method on other receivers");
row("'abc'.at(-1)", "abc".at(-1));
row("new Uint8Array([7, 8]).at(-1)", new Uint8Array([7, 8]).at(-1));
row("Array.prototype.at.call({ length: 2, 1: 'x' }, -1)", Array.prototype.at.call({ length: 2, 1: "x" }, -1));
```
```text
===== node20 js24b-26d-at.js (exit=0) =====
[1] negative and out-of-range indexes
  i = 0   at(i) a           arr[i] a
  i = 2   at(i) c           arr[i] c
  i = -1  at(i) c           arr[i] undefined
  i = -3  at(i) a           arr[i] undefined
  i = -4  at(i) undefined   arr[i] undefined
  i = 3   at(i) undefined   arr[i] undefined
[2] non-integer arguments
  arr.at(1.7)                                         "b"
  arr.at(-1.7)                                        "c"
  arr.at('1')                                         "b"
  arr.at(NaN)                                         "a"
  arr.at()                                            "a"
  arr.at(-0)                                          "a"
  arr['1.7']                                          "<undefined>"
[3] what arr[-1] = v does
  length 3   keys ["0","1","2","-1"]   at(-1) c
[4] the same method on other receivers
  'abc'.at(-1)                                        "c"
  new Uint8Array([7, 8]).at(-1)                       8
  Array.prototype.at.call({ length: 2, 1: 'x' }, -1)  "x"
```

```text
   arr = ["a", "b", "c"]

   at(i)    i >= 0  ->  arr[i]
            i <  0  ->  arr[length + i]         at(-1) -> "c"   at(-3) -> "a"   at(-4) -> undefined
   인자는 먼저 ToIntegerOrInfinity:   1.7 -> 1   -1.7 -> -1   "1" -> 1   NaN -> 0   (없음) -> 0

   arr[i]   i 를 **프로퍼티 키 글자**로 바꿔 그 키를 찾는다
            arr[-1]  ->  arr["-1"]   (그런 키는 없다 -> undefined)
            arr[-1] = "z"  ->  "-1" 이라는 평범한 키가 생긴다. length 는 그대로
```

- ★★★ **`arr[-1]` 은 「끝에서 첫째」가 아니다** — `"-1"` 이라는 **글자 키**를 찾는다. 그래서 `undefined` 이고, 대입하면 `keys` 에 `"-1"` 이 **평범한 키로 붙고 `length` 는 3 그대로**다(`[3]`). `at(-1)` 은 여전히 `c` 다.
- ★★ **`at` 은 인자를 정수로 깎는다** — `at(1.7)` 이 `b`, `at(-1.7)` 이 `c`(−1 로), `at(NaN)` 과 `at()` 이 `a`(0 으로). **`arr['1.7']` 은 `undefined`** — 괄호 접근은 깎지 않고 글자 `"1.7"` 을 찾는다.
- ★★ **범위 밖은 `undefined`** — `at(3)` · `at(-4)`. 던지지 않는다. ★ 같은 자리에 `with` 는 `RangeError` 를 던진다 — [25번](../25-array-non-mutating-and-copy-methods/2-summary.md).
- ★ **`[4]` 문자열 · 타입 배열 · 유사 배열** 에서도 된다 — `Array.prototype.at` 은 `length` 와 인덱스만 읽는 **범용(generic)** 메서드다.
- ★ **`at` 은 구멍을 읽는다** — 동작 (1)의 `at(0)` 이 `undefined`. `Get` 만 부른다.

### (5) ★★ `flat` 의 깊이 · `flatMap` 은 한 겹

**언제 쓰나** — 중첩 배열을 펴거나, 원소 하나를 여러 개(또는 0개)로 바꾸며 모을 때.

```js
// js24b-26e-flat.js
// flat(depth) and flatMap on one nested array.
const nested = [1, [2, [3, [4, [5]]]]];
const J = JSON.stringify;
console.log("nested = " + J(nested));
console.log("[1] depth argument");
for (const d of [undefined, 0, 1, 2, -1, Infinity, "2", NaN]) {
  console.log("  flat(" + (typeof d === "string" ? J(d) : String(d)).padEnd(9) + ") " + J(d === undefined ? nested.flat() : nested.flat(d)));
}

console.log("[2] flatMap -- callback returns");
const src = [1, 2];
console.log("  flatMap(x => [x, x * 10])     " + J(src.flatMap((x) => [x, x * 10])));
console.log("  flatMap(x => [[x]])           " + J(src.flatMap((x) => [[x]])));
console.log("  flatMap(x => x)               " + J(src.flatMap((x) => x)));
console.log("  flatMap(x => [])              " + J(src.flatMap(() => [])));
console.log("  map(x => [[x]]).flat(2)       " + J(src.map((x) => [[x]]).flat(2)));

console.log("[3] what counts as an array to flatten");
const spreadable = { length: 2, 0: "p", 1: "q", [Symbol.isConcatSpreadable]: true };
console.log("  [[1], 'ab', spreadable].flat()   " + J([[1], "ab", spreadable].flat().map((x) => (x === spreadable ? "<the object>" : x))));
console.log("  [[1], 'ab', spreadable] concat   " + J([].concat([1], "ab", spreadable)));
console.log("  [new Set([1, 2])].flat()         " + J([new Set([1, 2])].flat().map((x) => (x instanceof Set ? "<the Set>" : x))));

console.log("[4] holes inside the nested arrays");
console.log("  [[1, , 3], , [5]].flat()         " + J([[1, , 3], , [5]].flat()));

console.log("[5] a very deep array with flat(Infinity)");
let deep = [0];
for (let i = 0; i < 100000; i++) deep = [deep];
try {
  console.log("  length " + deep.flat(Infinity).length);
} catch (e) {
  console.log("  " + e.constructor.name + " 「" + e.message + "」");
}
```
```text
===== node20 js24b-26e-flat.js (exit=0) =====
nested = [1,[2,[3,[4,[5]]]]]
[1] depth argument
  flat(undefined) [1,2,[3,[4,[5]]]]
  flat(0        ) [1,[2,[3,[4,[5]]]]]
  flat(1        ) [1,2,[3,[4,[5]]]]
  flat(2        ) [1,2,3,[4,[5]]]
  flat(-1       ) [1,[2,[3,[4,[5]]]]]
  flat(Infinity ) [1,2,3,4,5]
  flat("2"      ) [1,2,3,[4,[5]]]
  flat(NaN      ) [1,[2,[3,[4,[5]]]]]
[2] flatMap -- callback returns
  flatMap(x => [x, x * 10])     [1,10,2,20]
  flatMap(x => [[x]])           [[1],[2]]
  flatMap(x => x)               [1,2]
  flatMap(x => [])              []
  map(x => [[x]]).flat(2)       [1,2]
[3] what counts as an array to flatten
  [[1], 'ab', spreadable].flat()   [1,"ab","<the object>"]
  [[1], 'ab', spreadable] concat   [1,"ab","p","q"]
  [new Set([1, 2])].flat()         ["<the Set>"]
[4] holes inside the nested arrays
  [[1, , 3], , [5]].flat()         [1,3,5]
[5] a very deep array with flat(Infinity)
  RangeError 「Maximum call stack size exceeded」
```

```text
   nested = [1, [2, [3, [4, [5]]]]]

   flat(depth)      depth 를 ToIntegerOrInfinity -> 음수면 0
     flat()   = flat(1)   [1, 2, [3,[4,[5]]]]        한 겹
     flat(2)              [1, 2, 3, [4,[5]]]          두 겹
     flat(Infinity)       [1, 2, 3, 4, 5]             끝까지
     flat(0) · flat(-1) · flat(NaN)   원래 모양 그대로(얕은 복사)

   flatMap(f)  =  map(f) 뒤에 flat(1)  -- 깊이 인자가 없다
     x => [[x]]   ->  [[1],[2]]        한 겹만 벗긴다
```

- ★★★ **`flatMap` 은 한 겹만 편다** — `flatMap(x => [[x]])` 가 **`[[1],[2]]`** 다. 더 펴려면 `map(...).flat(2)`(`[1,2]`). 명세 `FlattenIntoArray` 의 assert — mapper 가 있으면 "depth is 1".
- ★★ **깊이 인자** — 기본 1. `"2"` 는 **숫자로 바뀌어** 2 겹. `-1`·`NaN`·`0` 은 **0 겹** — 펴지 않는다(명세: "If depthNum < 0, set depthNum to 0").
- ★★ **`flatMap(x => x)` 가 `[1,2]`** — 콜백이 배열이 아닌 값을 돌려주면 **그대로 한 원소**가 된다. `[]` 를 돌려주면 **그 원소가 빠진다** — `filter` + `map` 을 한 번에 하는 관용구다.
- ★★★ **`[3]` `flat` 은 「진짜 배열」만 편다** — `Symbol.isConcatSpreadable` 을 켠 객체도, `Set` 도 **안 편다**(`"<the object>"` · `"<the Set>"` 그대로). 명세가 `IsArray(element)` 로 묻는다.
  ★ **같은 객체를 `concat` 은 편다**(`[1,"ab","p","q"]`) — `concat` 은 `IsConcatSpreadable` 을 본다(심볼 자체는 [22번](../22-symbol-and-well-known-symbols/2-summary.md)). 이름이 비슷한 두 「펴기」가 **다른 질문**을 한다.
- ★★ **`[4]` 안쪽 배열의 구멍도 지운다** — `[[1, , 3], , [5]].flat()` 이 `[1,3,5]`. 바깥 구멍과 안쪽 구멍이 **모두** 사라졌다(동작 (1)의 `flat` 줄과 같은 `HasProperty`).
- ★ **`[5]` 10만 겹을 `flat(Infinity)` 로 펴면 `RangeError 「Maximum call stack size exceeded」`** — `FlattenIntoArray` 가 **재귀**로 적혀 있고 V8 도 그 깊이에서 스택이 넘쳤다. ★ **명세에는 깊이 한계가 없다** — 몇 겹에서 터지는가는 **이 판의 관찰**이다.

### (6) ★★★ 배열을 만드는 세 입구 — `Array(n)` · `Array.of` · `Array.from`

**언제 쓰나** — 길이 n 짜리 배열을 만들어 채울 때 · 이터러블이나 유사 배열을 배열로 바꿀 때.

```js
// js24b-26f-create.js
// Making arrays: the Array constructor, Array.of, Array.from.
const J = JSON.stringify;
const V = (v) => (v === undefined ? "undefined" : J(v));
const show = (a) => "[" + Array.from({ length: a.length }, (_, i) => (i in a ? V(a[i]) : "<hole>")).join(",") + "]";
const row = (label, f) => {
  let out;
  try { out = f(); } catch (e) { out = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(40) + out);
};

console.log("[1] one argument to Array vs Array.of");
row("Array(3)", () => show(Array(3)));
row("Array.of(3)", () => show(Array.of(3)));
row("Array('3')", () => show(Array("3")));
row("Array(3, 4)", () => show(Array(3, 4)));
row("Array.of(3, 4)", () => show(Array.of(3, 4)));
row("Array(2.5)", () => show(Array(2.5)));
row("Array(-1)", () => show(Array(-1)));
row("Array.of()", () => show(Array.of()));

console.log("[2] filling the slots of Array(3)");
let calls = 0;
row("Array(3).map(() => 0)", () => show(Array(3).map(() => { calls++; return 0; })));
row("  callback calls", () => String(calls));
row("Array(3).fill(0)", () => show(Array(3).fill(0)));
row("[...Array(3)]", () => show([...Array(3)]));
row("Array.from(Array(3))", () => show(Array.from(Array(3))));
row("Array.from({ length: 3 })", () => show(Array.from({ length: 3 })));
row("Array.from({ length: 3 }, (_, i) => i)", () => show(Array.from({ length: 3 }, (_, i) => i)));
row("Array.apply(null, Array(3))", () => show(Array.apply(null, Array(3))));

console.log("[3] what Array.from accepts");
row("Array.from('abc')", () => show(Array.from("abc")));
row("Array.from(new Set([1, 1, 2]))", () => show(Array.from(new Set([1, 1, 2]))));
row("Array.from(new Map([[1, 'a']]))", () => show(Array.from(new Map([[1, "a"]]))));
row("Array.from({ length: 2, 0: 'x' })", () => show(Array.from({ length: 2, 0: "x" })));
row("Array.from({ 0: 'x' })", () => show(Array.from({ 0: "x" })));
row("Array.from(5)", () => show(Array.from(5)));
row("Array.from(null)", () => show(Array.from(null)));
row("Array.from([1, 2], 'x')", () => show(Array.from([1, 2], "x")));

console.log("[4] an object that is both iterable and array-like");
const both = { length: 2, 0: "index-0", 1: "index-1", *[Symbol.iterator]() { yield "iter-a"; } };
row("Array.from(both)", () => show(Array.from(both)));

console.log("[5] the mapping function -- arguments and this");
const log = [];
Array.from({ length: 2, 0: "p", 1: "q" }, function (v, i) { log.push(J([v, i, arguments.length, this && this.tag])); return v; }, { tag: "T" });
for (const line of log) console.log("  " + line);

console.log("[6] Array.from called on a subclass");
class Tagged extends Array {}
row("Tagged.from([1]) instanceof Tagged", () => String(Tagged.from([1]) instanceof Tagged));
row("Tagged.of(1) instanceof Tagged", () => String(Tagged.of(1) instanceof Tagged));
```
```text
===== node20 js24b-26f-create.js (exit=0) =====
[1] one argument to Array vs Array.of
  Array(3)                                [<hole>,<hole>,<hole>]
  Array.of(3)                             [3]
  Array('3')                              ["3"]
  Array(3, 4)                             [3,4]
  Array.of(3, 4)                          [3,4]
  Array(2.5)                              RangeError 「Invalid array length」
  Array(-1)                               RangeError 「Invalid array length」
  Array.of()                              []
[2] filling the slots of Array(3)
  Array(3).map(() => 0)                   [<hole>,<hole>,<hole>]
    callback calls                        0
  Array(3).fill(0)                        [0,0,0]
  [...Array(3)]                           [undefined,undefined,undefined]
  Array.from(Array(3))                    [undefined,undefined,undefined]
  Array.from({ length: 3 })               [undefined,undefined,undefined]
  Array.from({ length: 3 }, (_, i) => i)  [0,1,2]
  Array.apply(null, Array(3))             [undefined,undefined,undefined]
[3] what Array.from accepts
  Array.from('abc')                       ["a","b","c"]
  Array.from(new Set([1, 1, 2]))          [1,2]
  Array.from(new Map([[1, 'a']]))         [[1,"a"]]
  Array.from({ length: 2, 0: 'x' })       ["x",undefined]
  Array.from({ 0: 'x' })                  []
  Array.from(5)                           []
  Array.from(null)                        TypeError 「object null is not iterable (cannot read property Symbol(Symbol.iterator))」
  Array.from([1, 2], 'x')                 TypeError 「x is not a function」
[4] an object that is both iterable and array-like
  Array.from(both)                        ["iter-a"]
[5] the mapping function -- arguments and this
  ["p",0,2,"T"]
  ["q",1,2,"T"]
[6] Array.from called on a subclass
  Tagged.from([1]) instanceof Tagged      true
  Tagged.of(1) instanceof Tagged          true
```

```text
   Array(x)  인자가 하나일 때만 뜻이 바뀐다
     x 가 Number  ->  length 가 x 인 빈 선반 (상자 0 개)      Array(3)   -> [<hole>,<hole>,<hole>]
                      정수가 아니거나 음수면 RangeError        Array(2.5) -> RangeError
     x 가 그 밖     ->  x 한 개를 담는다                       Array('3') -> ["3"]
   인자가 둘 이상    ->  그것들을 담는다                          Array(3, 4) -> [3,4]

   Array.of(...xs)   언제나 「담는다」                          Array.of(3) -> [3]

   Array.from(src, mapFn?)
     src 에 Symbol.iterator 가 있나? ──yes──▶ 이터레이터로 읽는다
          │ no
          ▼
     length 를 읽고 0..length-1 을 Get 으로 읽는다 (구멍 -> undefined)
     mapFn 은 (값, 인덱스) 두 인자로 부른다
```

- ★★★ **`Array(3)` 과 `Array.of(3)`** — 앞은 **구멍 셋**, 뒤는 **`[3]`**. 인자가 **Number 하나**일 때만 `Array` 는 「길이」로 읽는다. `Array('3')` 은 **`["3"]`**(글자는 담는다). `Array.of` 는 이 예외를 없애려고 들어왔다.
  ★ `Array(2.5)` · `Array(-1)` 은 **`RangeError`** — 명세: `ToUint32(len)` 이 `len` 과 SameValueZero 가 아니면 던진다.
- ★★★ **`Array(3).map(() => 0)` 은 구멍 셋 그대로이고 콜백은 0번** — `map` 은 `HasProperty` 를 묻는다(동작 (1)). **채우려면 `fill` · `Array.from({ length: 3 }, …)` · `[...Array(3)]`.**
- ★★ **`Array.from({ length: 3 })` 은 구멍이 아니라 `undefined` 셋** — 유사 배열 경로가 `Get` 만 부른다. 그래서 **`Array.from({ length: n }, (_, i) => i)`** 가 `[0,1,2]` 를 만든다.
  ★ `[...Array(3)]` · `Array.from(Array(3))` · `Array.apply(null, Array(3))` 도 `undefined` 셋이다 — 스프레드와 `Array.from` 은 이터레이터가, `apply` 는 인자 목록 만들기가 **`Get` 으로** 읽는다.
- ★★ **`[3]`** — 문자열 · `Set`(중복이 이미 없다) · `Map`(쌍) 은 이터레이터로 읽힌다. `{ length: 2, 0: 'x' }` 는 **`["x",undefined]`**, `length` 가 없으면 **`[]`**, `Array.from(5)` 도 **`[]`**(숫자 객체의 `length` 가 없다 → 0).
  `null` 은 `TypeError`, 매핑 자리에 `'x'` 는 `TypeError 「x is not a function」`.
- ★★★ **`[4]` 이터러블이면서 유사 배열이면 이터러블이 이긴다** — `["iter-a"]`. 명세 `Array.from` 이 `GetMethod(items, %Symbol.iterator%)` 를 **먼저** 묻는다. 두 문의 정본은 [19번](../19-iterable-protocol-and-for-of/2-summary.md)·[11번](../11-spread-and-rest/2-summary.md)이다.
- ★★ **`[5]` 매핑 함수는 두 인자**(`arguments.length` 가 2) — `map` 의 콜백이 세 인자(값·인덱스·배열)를 받는 것과 다르다. 명세가 매핑 함수를 **값과 인덱스 두 개**로 부른다(`Call(mapper, thisArg, « next, k »)` — 수 표기 기호는 뺐다). 셋째 인자 `{ tag: "T" }` 가 `this` 다.
- ★ **`[6]` 하위 클래스에서 부르면 하위 클래스를 만든다** — `Tagged.from([1]) instanceof Tagged` 가 `true`. `this` 가 생성자면 그것으로 만든다(`IsConstructor(C)`). `Symbol.species` 와는 다른 길이다([22번](../22-symbol-and-well-known-symbols/2-summary.md)).

### (7) ★★ `Array.fromAsync`(ES2026) — 하나씩 기다린다

**언제 쓰나** — 비동기 이터러블(스트림·페이지 넘기기)을 배열로 모을 때 · `for await` 루프 + `push` 를 한 줄로 줄일 때.
★ **두 node 판에 없다** — 판별 블록의 `ES2026  Array.fromAsync` 줄이 node 18·20 에서 `no`, Chrome 151 에서 `yes` 다. node 에서 부르면 이렇다.

```js
// js24b-26x-node-fromasync.js
// Is Array.fromAsync callable on this node? Ask the runtime, then try the call.
console.log("typeof Array.fromAsync   " + typeof Array.fromAsync);
try {
  Array.fromAsync([1]);
  console.log("call returned");
} catch (e) {
  console.log(e.constructor.name + " 「" + e.message + "」");
}
```
```text
===== node20 js24b-26x-node-fromasync.js (exit=0) =====
typeof Array.fromAsync   undefined
TypeError 「Array.fromAsync is not a function」
```

★ 이 문구(`… is not a function`)만으로 판별하지 않는다 — **`typeof Array.fromAsync` 가 `undefined`** 인 줄이 근거다. 그래서 탐침은 Chrome 151 로 돌렸다.

```js
// js24b-26g-fromasync.web.js
// Array.fromAsync (Chrome only in this batch). Every line is a log event, in the order it happened.
// Timers are virtual (--virtual-time-budget), so the order below does not depend on machine speed.
const J = JSON.stringify;
const later = (ms, v, log, tag) => new Promise((res) => setTimeout(() => { log.push("settle " + tag); res(v); }, ms));

(async () => {
  console.log("[1] return value of the call");
  const p = Array.fromAsync([1, Promise.resolve(2), 3]);
  console.log("  instanceof Promise  " + (p instanceof Promise));
  console.log("  resolved to         " + J(await p));

  console.log("[2] a sync iterable whose items settle 30, 20, 10 ms after they are made");
  const run = async (label, consume) => {
    const log = [];
    function* source() {
      const delays = [30, 20, 10];
      for (let i = 0; i < 3; i++) { log.push("next " + i); yield later(delays[i], "v" + i, log, i); }
    }
    const out = await consume(source());
    console.log("  " + label.padEnd(26) + J(out));
    console.log("  " + "".padEnd(26) + log.join(" | "));
  };
  await run("Array.fromAsync(gen())", (it) => Array.fromAsync(it));
  await run("Promise.all([...gen()])", (it) => Promise.all([...it]));

  console.log("[3] an async generator");
  const pulls = [];
  async function* agen() { for (let i = 0; i < 3; i++) { pulls.push(i); yield i * 10; } }
  console.log("  result " + J(await Array.fromAsync(agen())) + "   pulled " + J(pulls));

  console.log("[4] the mapping function");
  const margs = [];
  const mapped = await Array.fromAsync([Promise.resolve("a"), "b"], async (v, i) => { margs.push(J([v, i])); return v + v; });
  console.log("  result " + J(mapped) + "   mapper saw " + margs.join(" "));

  console.log("[5] an array-like of promises");
  console.log("  " + J(await Array.fromAsync({ length: 2, 0: Promise.resolve("x"), 1: "y" })));

  console.log("[6] one item rejects -- what reaches the caller, and how far did it pull");
  const log6 = [];
  function* withReject() {
    try {
      log6.push("next 0"); yield Promise.resolve(0);
      log6.push("next 1"); yield Promise.reject(new Error("item 1"));
      log6.push("next 2"); yield Promise.resolve(2);
    } finally { log6.push("finally ran"); }
  }
  try { await Array.fromAsync(withReject()); console.log("  resolved"); }
  catch (e) { console.log("  " + e.constructor.name + " 「" + e.message + "」"); }
  console.log("  log " + J(log6));

  console.log("[7] a bad mapper -- thrown now, or a rejected promise?");
  let sync = "no exception during the call";
  let q;
  try { q = Array.fromAsync([1], 5); } catch (e) { sync = "thrown during the call: " + e.constructor.name; }
  console.log("  " + sync);
  if (q) { try { await q; } catch (e) { console.log("  rejected: " + e.constructor.name + " 「" + e.message + "」"); } }

  console.log("[8] not iterable, not array-like");
  try { await Array.fromAsync(null); } catch (e) { console.log("  " + e.constructor.name + " 「" + e.message + "」"); }
  console.log("  " + J(await Array.fromAsync(5)));
  console.log("done");
})();
```
```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js24b-page.html?js24b-26g-fromasync.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] return value of the call
  instanceof Promise  true
  resolved to         [1,2,3]
[2] a sync iterable whose items settle 30, 20, 10 ms after they are made
  Array.fromAsync(gen())    ["v0","v1","v2"]
                            next 0 | settle 0 | next 1 | settle 1 | next 2 | settle 2
  Promise.all([...gen()])   ["v0","v1","v2"]
                            next 0 | next 1 | next 2 | settle 2 | settle 1 | settle 0
[3] an async generator
  result [0,10,20]   pulled [0,1,2]
[4] the mapping function
  result ["aa","bb"]   mapper saw ["a",0] ["b",1]
[5] an array-like of promises
  ["x","y"]
[6] one item rejects -- what reaches the caller, and how far did it pull
  Error 「item 1」
  log ["next 0","next 1","finally ran"]
[7] a bad mapper -- thrown now, or a rejected promise?
  no exception during the call
  rejected: TypeError 「5 is not a function」
[8] not iterable, not array-like
  TypeError 「Cannot read properties of null (reading 'Symbol(Symbol.asyncIterator)')」
  []
done
```

```text
   항목이 30 · 20 · 10 ms 뒤에 정해지는 세 프라미스일 때

   Array.fromAsync(gen())                     Promise.all([...gen()])
   ----------------------                     -----------------------
   next 0                                     next 0          <- 스프레드가 먼저
   settle 0      (기다린다)                    next 1             셋을 다 꺼낸다
   next 1                                     next 2
   settle 1                                   settle 2        <- 짧은 것부터 정해진다
   next 2                                     settle 1
   settle 2                                   settle 0
   -> ["v0","v1","v2"]                        -> ["v0","v1","v2"]   결과는 같다

   ★ 결과로는 못 가른다 -- 로그로만 갈린다
```

- ★★★ **`[2]` 결과는 같은데 순서가 다르다** — `Array.fromAsync` 는 **한 항목이 정해질 때까지 다음 `next` 를 안 부른다**(`next 0 | settle 0 | next 1 …`). `Promise.all([...gen()])` 은 **스프레드가 셋을 먼저 다 꺼내** 동시에 기다린다.
  ★ **명세의 모양이 곧 이유다** — `Array.fromAsync` 는 **「This async function performs the following steps」** 로 적혀 있고, 동기 이터러블을 `CreateAsyncFromSyncIterator` 로 감싸 **`for await` 처럼 한 값씩 `Await`** 한다.
  ★ **시간은 안 쟀다** — 가상 시간이라 「몇 ms 걸렸나」는 이 블록이 말하지 못하고 말하려 하지도 않는다. **로그의 순서만** 근거다.
- ★★ **`[1]` 돌려주는 것은 프라미스** — 값이 이미 있는 배열이어도 `instanceof Promise` 가 `true`. 섞인 프라미스는 풀어서 담는다(`[1,2,3]`).
- ★★ **`[3]` 비동기 제너레이터** — 세 번 당겼다(`pulled [0,1,2]`). **`[4]` 매핑 함수** — 풀린 값과 인덱스를 받고(`["a",0] ["b",1]`), 매핑 함수가 돌려준 프라미스도 기다린다(`["aa","bb"]`).
- ★★ **`[5]` 유사 배열도 받는다** — `Array.from` 처럼 이터러블이 아니면 `length` 로 읽는다(`["x","y"]`).
- ★★★ **`[6]` 하나가 거부되면 거기서 멈추고 원본을 닫는다** — `Error 「item 1」` 로 거부되고, 로그에 **`next 2` 가 없고 `finally ran` 이 있다.** 동기 이터레이터의 `return()` 이 불렸다는 뜻이다.
  명세 `AsyncFromSyncIteratorContinuation` 의 `closeOnRejection` 이 참이면 거부된 값에서 `IteratorClose` 를 한다 — ES2025(16판)·ES2026(17판) 두 판 본문에 다 있다.
- ★★★ **`[7]` 매핑 함수가 함수가 아니어도 호출하는 순간에는 안 던진다** — `no exception during the call` 뒤에 **거부**(`TypeError 「5 is not a function」`)로 온다. async function 이라 **모든 오류가 거부된 프라미스**가 된다. `Array.from` 은 같은 자리에서 **즉시 던졌다**(동작 (6)의 `[3]`).
- ★ **`[8]` `null` 은 거부, `5` 는 `[]`** — `Array.from` 과 같은 모양이다. 문구는 V8 의 글자다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28 — 돌리지 않은 코드 펜스를 싣지 않는다).

| 형태 | 돌려주는 것 | 구멍 | 판 | 어디서 봤나 |
|---|---|---|---|---|
| `arr.indexOf(x, from?)` · `lastIndexOf` | 인덱스 또는 `-1` — `===` 비교 | 건너뜀 | ES5 | 동작 (2) |
| `arr.includes(x, from?)` | boolean — SameValueZero | `undefined` 로 읽음 | ES2016 | 동작 (2) |
| `arr.find(pred)` · `findLast(pred)` | 원소 또는 `undefined` | 읽음 | ES2015 · ES2023 | 동작 (3) |
| `arr.findIndex(pred)` · `findLastIndex(pred)` | 인덱스 또는 `-1` | 읽음 | ES2015 · ES2023 | 동작 (3) |
| `arr.at(i)` | 원소 또는 `undefined` — 음수는 끝에서 | 읽음 | ES2022 | 동작 (4) |
| `arr.flat(depth = 1)` | 새 배열 | **지운다** | ES2019 | 동작 (5) |
| `arr.flatMap(f)` | 새 배열 — `map` 뒤 **한 겹** | **지운다** | ES2019 | 동작 (5) |
| `Array(n)` · `Array(a, b, …)` | 길이 n 의 **구멍 배열** / 인자를 담은 배열 | 만든다 | ES1 | 동작 (6) |
| `Array.of(...xs)` | 인자를 담은 배열 | — | ES2015 | 동작 (6) |
| `Array.from(src, mapFn?, thisArg?)` | 새 배열 — 이터러블 먼저, 아니면 유사 배열 | `undefined` 로 채움 | ES2015 | 동작 (6) |
| `Array.fromAsync(src, mapFn?, thisArg?)` | **프라미스** — 한 항목씩 기다려 모은 배열 | — | **ES2026** | 동작 (7) |

- **비교** — `indexOf`·`lastIndexOf` 는 `===`(`NaN` 못 찾음), `includes` 는 SameValueZero. **셋 다 `-0` 과 `+0` 을 같게 본다.**
- **구멍** — 반복 단계에 **`HasProperty` 가 있으면 건너뛴다.** 판으로 외우면 `flat`·`flatMap`·`copyWithin` 에서 틀린다.
- **음수 인덱스** — `at`·`indexOf` 의 `fromIndex`·`slice` 는 끝에서 센다. **`arr[-1]` 은 안 센다**(글자 키).

## 어디서 틀리나

### (1) ★★★ `Array(n).map(...)` 으로 채우려 한다

**구멍 n 개가 그대로** 나오고 콜백은 **0번** 불린다(동작 (6)의 `[2]`). 에러가 없어서 **빈 배열 같은 것**이 조용히 흘러간다.
`Array.from({ length: n }, (_, i) => …)` 이나 `Array(n).fill(v)` 로 만든다.

### (2) ★★★ `Array(3)` 과 `Array.of(3)` 을 같은 것으로 쓴다

`Array(3)` 은 **길이 3 인 빈 선반**, `Array.of(3)` 은 **`[3]`** 이다. 인자가 **숫자 하나**일 때만 갈린다 — 변수로 받은 숫자 하나를 `Array(x)` 에 넘기는 코드가 여기서 터진다(`Array(2.5)` 는 `RangeError`).

### (3) ★★★ `indexOf` 로 `NaN` 이나 빈 칸을 찾는다

`[NaN].indexOf(NaN)` 이 `-1`, `[, 1].indexOf(undefined)` 도 `-1` 이다(동작 (2) · 동작 (1)). 있나만 물으면 `includes`, **인덱스가 필요하면 `findIndex(Number.isNaN)`**.

### (4) ★★★ `find` 가 돌려준 `undefined` 를 「못 찾았다」로 읽는다

**찾은 원소가 `undefined` 여도** `find` 는 `undefined` 다(동작 (3)의 `[3]`). 원소에 `undefined` 가 있을 수 있으면 `findIndex` 로 묻고 `-1` 과 견준다.

### (5) ★★★ `arr[-1]` 로 마지막 원소를 읽는다

`undefined` 다. 쓰면 **`"-1"` 이라는 키가 생기고 `length` 는 안 바뀐다**(동작 (4)의 `[3]`). 파이썬의 `a[-1]` 습관이 여기서 조용히 틀린다. `at(-1)` 을 쓴다.

### (6) ★★ `flatMap` 이 끝까지 펼 것이라 믿는다

**한 겹**이다 — `flatMap(x => [[x]])` 이 `[[1],[2]]`(동작 (5)). 더 깊으면 `map(...).flat(depth)`.

### (7) ★★ 「새 메서드는 구멍을 `undefined` 로 읽는다」로 외운다

`flat`·`flatMap`(ES2019)·`copyWithin`(ES2015)은 **건너뛴다**(동작 (1) — `3 / 27`). `[, 1].flat()` 이 **`[1]`** 이라 길이가 바뀐다. 구멍이 있을 수 있는 배열은 **먼저 `Array.from` 으로 빽빽하게** 만들어 두면 모든 메서드가 같은 답을 낸다.

### (8) ★★ `flat` 이 `Set` 이나 펴기 표시(`isConcatSpreadable`)를 켠 객체도 펼 것이라 믿는다

안 편다 — `IsArray` 만 본다(동작 (5)의 `[3]`). `concat` 은 **편다.** `Set` 은 `[...set]` 으로 먼저 바꾼다.

### (9) ★★ `Array.fromAsync` 가 `Promise.all` 처럼 동시에 기다릴 것이라 믿는다

**하나씩** 기다린다 — 다음 `next` 는 앞 항목이 정해진 뒤에야 불린다(동작 (7)의 `[2]`). 동시에 시작하고 싶으면 프라미스를 먼저 다 만들어 `Promise.all` 에 넘긴다. ★ 반대로 **순서대로 하나씩**(요청 폭주를 막으려고)이 목적이면 `fromAsync` 가 맞다.

### (10) ★★ `Array.fromAsync` 의 잘못된 인자가 `try` 에서 잡힐 것이라 믿는다

**호출은 안 던지고 거부된 프라미스를 돌려준다**(동작 (7)의 `[7]`). `await` 없이 `try` 로 감싸면 **아무것도 안 잡히고** 처리 안 된 거부가 된다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **구멍을 건너뛰나 읽나** — 알고리즘의 반복 단계에 `HasProperty` 가 있느냐로 정해진다. 격자의 `skips`/`reads` 스물일곱 줄은 전부 명세가 정한 것이다.
- `indexOf`·`lastIndexOf` 가 IsStrictlyEqual, `includes` 가 SameValueZero 인 것 · **배열이 `-0` 을 바꾸지 않고 담는 것.**
- `FindViaPredicate` 의 **방문 범위가 시작할 때 정해지는 것** · 지운 자리도 방문하는 것 · `findLast` 가 **내림차순**인 것.
- `at` 의 `ToIntegerOrInfinity` 와 음수 처리 · 범위 밖이 `undefined` 인 것.
- `flat` 의 깊이 규칙(음수 → 0) · `flatMap` 이 깊이 1 인 것 · `IsArray` 로만 펴는 것 · 결과를 `ArraySpeciesCreate` 로 만드는 것.
- `Array(n)` 의 `RangeError` 조건 · `Array.of` · `Array.from` 이 **이터레이터를 먼저** 보는 것 · 매핑 함수가 **두 인자**인 것.
- ★★ **`Array.fromAsync` 가 async function 인 것**(모든 오류가 거부) · 한 값씩 `Await` 하는 것 · 거부된 값에서 동기 이터레이터를 **닫는 것**(`closeOnRejection`).
- 예외의 **종류**(`RangeError` · `TypeError`).

### 엔진(V8) 구현 · 이 판의 관찰

- 예외 **문구 전부** — `Invalid array length` · `object null is not iterable (cannot read property Symbol(Symbol.iterator))` · `x is not a function` · `5 is not a function` · `Array.fromAsync is not a function` ·
  `Cannot read properties of null (reading 'Symbol(Symbol.asyncIterator)')`.
- ★★ **10만 겹 `flat(Infinity)` 의 `RangeError 「Maximum call stack size exceeded」`** — 명세에 없는 한계다. 스택 크기(엔진·플래그·호스트)에 달렸다.
- `JSON.stringify` 가 배열 안의 `undefined` 를 `null` 로 찍는 것은 명세(`SerializeJSONArray`)지만, **이 문서가 구멍을 `<hole>` 로 보이게 한 것은 탐침의 출력 함수**다 — 엔진이 그렇게 찍는 게 아니다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★ **`Array.fromAsync` 가 어느 판에 들어오나** — node 18·20 에는 없고 Chrome 151 에는 있다. 명세 판(ES2026)과 **엔진 도입 시점은 별개**다.
- 타이머(`setTimeout`) 자체 — 동작 (7)의 지연은 **호스트 API** 로 만들었다. 헤드리스 Chrome 의 가상 시간 예산도 호스트(브라우저)의 기능이다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「ES5 메서드는 구멍을 건너뛰고 ES2015 이후는 `undefined` 로 읽는다」 → ○ 「**반복 단계에 `HasProperty` 가 있는 메서드가 건너뛴다.** `flat`·`flatMap`·`copyWithin` 은 새 판인데 건너뛴다」
- ✗ 「`indexOf` 는 `-0` 을 못 찾는다」 → ○ 「**`-0` 은 찾는다**(`===` 가 부호를 안 가린다). 못 찾는 것은 `NaN` 이다」
- ✗ 「`Array.fromAsync` 는 `Promise.all` 의 배열판이다」 → ○ 「**한 항목씩 기다린다.** 결과는 같아도 `next` 를 부르는 시점이 다르다」
- ✗ 「`find` 가 `filter` 보다 빠르다」 → ○ **안 쟀다.** 콜백 호출 수가 2 대 5 였다는 것까지만 말한다
- ✗ 「`flat(Infinity)` 는 아무리 깊어도 편다」 → ○ 「명세에는 한계가 없지만 **이 판은 10만 겹에서 스택이 넘쳤다**」

## 언제 쓰고 언제 안 쓰나

- **`includes`** — 「있나」만 물을 때. `NaN` 도 찾는다.
- **`indexOf`** — 위치가 필요하고 `NaN` 이 들어올 일이 없을 때. `NaN` 이 있을 수 있으면 **`findIndex(Number.isNaN)`**.
- **`find`/`findIndex`** — 조건으로 **첫** 원소를 찾을 때. **`findLast`/`findLastIndex`** — 마지막 원소(최신 기록)를 찾을 때 — `reverse()` 한 뒤 `find` 하면 **원본이 뒤집힌다**([24번](../24-array-mutating-methods/2-summary.md)).
- **`at(-1)`** — 마지막 원소. `arr[arr.length - 1]` 을 대신한다.
- **`flat`** — 중첩을 알 때 깊이를 적는다. **`flatMap`** — 원소를 0\~n 개로 바꾸며 모을 때(`filter` + `map`).
- **`Array.from({ length: n }, fn)`** — 길이 n 을 계산으로 채울 때. **`Array.of`** — 인자를 그대로 담을 때(특히 숫자 하나).
- **`Array.fromAsync`** — 비동기 이터러블을 **순서대로** 모을 때. ★ **판 확인이 먼저**다(node 20 에 없다).
- ★ **안 쓰는 자리** — `Array(n)` 에 `map`/`forEach` 를 바로 거는 것 · 희소 배열을 그대로 여러 메서드에 넘기는 것(메서드마다 답이 다르다).

## 핵심 문장

1. ★★★ 구멍은 **프로퍼티가 없는 자리**이고, 반복 단계에 **`HasProperty` 를 묻는 메서드가 건너뛴다.** 「판으로 외우는 규칙」은 스물일곱 줄 중 **`3 / 27`** 에서 어긋났다(`copyWithin` · `flat` · `flatMap`).
2. ★★★ `indexOf` 와 `includes` 는 **두 축**에서 갈린다 — 비교(`NaN`)와 구멍. **`-0` 에서는 안 갈린다.** 배열은 `-0` 을 그대로 담는다(`Map` 은 `+0` 으로 바꿨다).
3. ★★★ `find` 네 형제는 **맞은 자리에서 멈추고**, `findLast` 쪽은 **끝에서** 시작한다. `find` 의 `undefined` 는 「못 찾음」과 「`undefined` 를 찾음」 두 뜻이다.
4. ★★★ `Array(3)` 은 **구멍 셋**, `Array.of(3)` 은 `[3]`, `Array.from({ length: 3 })` 은 **`undefined` 셋** — 그래서 `Array(3).map` 은 콜백을 **한 번도** 안 부른다.
5. ★★ `Array.fromAsync`(ES2026)는 **async function** 이라 한 항목씩 기다리고, 모든 오류를 **거부**로 돌려준다. **node 18·20 에는 없다.**

## 관련 자료

- [ECMA-262 2026 (17판)](https://262.ecma-international.org/17.0/) · [ECMA-262 2025 (16판)](https://262.ecma-international.org/16.0/) — `Array.fromAsync` 가 17판에 있고 16판에 없다
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계
- [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) — ★ **경계**: 그쪽은 **여덟 비교 자리의 `NaN`·`-0` 격자**(`9 / 56`)까지, 여기는 그 가운데 **배열 찾기 메서드의 구멍과 `-0`** 부터.
- [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) — ★ **경계**: 그쪽은 **`for-in` 과 `for-of` 가 구멍에서 갈리는 것**까지, 여기는 **배열 메서드 전부**.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — ★ **경계**: 그쪽은 **스프레드·`apply`·`Array.from` 이 여는 문**까지, 여기는 **`Array.from` 의 매핑 함수와 `Array(n)`·`Array.of` 와의 짝**.
- [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md) — ★ **경계**: 그쪽은 **배열 메서드와 헬퍼의 호출 격자**, 여기는 **`find` 네 형제의 방문 인덱스**만.
- [24 — 배열 변형 메서드](../24-array-mutating-methods/2-summary.md) — ★ **경계**: 그쪽은 **`sort`·`copyWithin`·`fill` 이 원본을 바꾸는 것**, 여기는 그것들이 **구멍을 어떻게 다루나** 한 칸씩만.
- [25 — 배열 비변형·복사 메서드](../25-array-non-mutating-and-copy-methods/2-summary.md) — `with` 의 `RangeError` 와 `at` 의 `undefined` 대비.

## 용어 풀이

- **구멍(hole)** — `length` 안의 인덱스인데 프로퍼티가 없는 자리. `i in arr` 이 `false`.
- **희소 배열(sparse array)** — 구멍이 있는 배열. **빽빽한 배열(dense array)** — 구멍이 없는 배열.
- **`HasProperty`** — 키가 객체(또는 체인)에 있나를 묻는 명세 연산. `in` 이 쓴다.
- **`Get`** — 키의 값을 읽는 명세 연산. 없으면 `undefined`(체인도 본다).
- **IsStrictlyEqual** — `===`. `NaN` 은 자기와 다르고 `+0`/`-0` 은 같다.
- **SameValueZero** — `NaN` 끼리 같고 `+0`/`-0` 도 같은 비교. `includes` 가 쓴다.
- **`FindViaPredicate`** — `find`·`findIndex`·`findLast`·`findLastIndex` 가 함께 쓰는 명세 연산. 방향(오름·내림)만 다르다.
- **`FlattenIntoArray`** — `flat`·`flatMap` 이 쓰는 재귀 연산. 원소마다 `HasProperty` 를 먼저 묻는다.
- **`ToIntegerOrInfinity`** — 인자를 정수로 깎는 연산(`NaN` → 0, 소수점 버림, `±∞` 는 그대로). `at`·`flat`·`fromIndex` 가 쓴다.
- **유사 배열(array-like)** — `length` 와 인덱스 키를 가진 객체. 이터러블이 아니어도 된다.
- **범용(generic) 메서드** — `this` 가 배열이 아니어도 `length` 와 인덱스만으로 도는 메서드. `Array.prototype.at.call(obj, …)`.
- **async function** — 호출하면 곧바로 프라미스를 돌려주고 안의 오류를 전부 **거부**로 바꾸는 함수. 명세가 `Array.fromAsync` 를 이렇게 적는다.
- **`closeOnRejection`** — 동기 이터레이터를 비동기로 감쌀 때, 넘어온 프라미스가 거부되면 원본을 닫으라는 명세 표시.

## 더 들어가면

- **구멍이 프로토타입에서 값을 얻는 경우** — `Array.prototype[0] = "p"` 를 두면 `HasProperty` 가 체인에서 찾아 **`forEach` 도 그 자리를 방문**한다. 이 배치는 그 탐침을 돌리지 않았다 — **안 돌렸다.** 체인 자체는 [15번](../15-prototype-chain/2-summary.md)이 정본이다.
- **엔진이 희소 배열을 어떻게 저장하나**(V8 의 elements kind) — 관찰 가능한 의미가 아니라 이 문서 밖이다. 성능 이야기도 **안 쟀다.**
- **`Array.fromAsync` 의 node 판** — node 22 이후 판에서 판별 블록의 `no` 가 `yes` 로 바뀌면 동작 (7)을 node 로도 돌린다.
