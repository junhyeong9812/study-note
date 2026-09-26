# js/syntax/24 — 배열 변형 메서드: 「무엇이 원본을 바꾸고 무엇을 돌려주나 — 그리고 `sort` 는 무엇으로 비교하나」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 「이 메서드가 원본을 바꾸나」는 이름으로 외우면 **반환값 쪽에서** 틀린다 — `sort`·`reverse` 는 **원본 그 자체**를 돌려주고, `push`·`unshift` 는 **길이**를 돌려준다.
> 그래서 메서드 **열다섯 개**에 「반환값이 원본인가 · 내용이 달라졌나 · `length` 가 달라졌나」 세 칸을 전부 묻고, **y 칸을 스크립트가 센다**(동작 (1)).
> ★★ `sort` 쪽은 창이 하나 더 붙는다 — **비교 함수에 로그를 심어** 몇 번 · 무엇을 받고 불리나를 본다(동작 (5)·(6)).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안 — Indexed Collections](https://tc39.es/ecma262/multipage/indexed-collections.html) —
>   `Array.prototype.sort` · `SortIndexedProperties` · `CompareArrayElements` · 「consistent comparator」 정의 · `Array.prototype.push`·`shift`·`splice`·`reverse`·`fill`·`copyWithin`
>   (ECMA-262 17판 = ES2026 HTML 을 내려받아 문장을 대조했다)
> - [ECMA-262 9판(ES2018)](https://262.ecma-international.org/9.0/) · [10판(ES2019)](https://262.ecma-international.org/10.0/) — `Array.prototype.sort` 첫 문장(안정성의 판 경계)
> - [ECMA-262 최신 초안 — Ordinary and Exotic Objects Behaviours](https://tc39.es/ecma262/multipage/ordinary-and-exotic-objects-behaviours.html) — `ArraySetLength` · `ArrayCreate`
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 값·호출 로그·예외 타입과 메시지는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, 대조한 `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★ **이 문서는 BMP 밖 글자를 한 글자도 싣지 않는다.**
>
> **버전** — 이 주제의 메서드는 **전부 ES2015 이전부터** 있었다(`fill`·`copyWithin` 만 ES2015). ★★★ **판이 갈리는 것은 메서드가 아니라 「약속」이다.**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `push`·`pop`·`shift`·`unshift`·`splice`·`sort`·`reverse` | ES1\~ES3 | 세 판 다 있다 |
> | `fill`·`copyWithin` | **ES2015** | 세 판 다 있다(판별 블록) |
> | ★★★ **`sort` 가 안정 정렬이어야 한다는 약속** | **ES2019** — 9판은 "The sort is not necessarily stable", 10판은 "The sort must be stable" | ★ **두 node 판 다 경계 뒤**다 — 판 차이로는 못 보이고 **같은 키 격자**로 보였다(동작 (4)) |
> | 복사판(`toSorted`·`toReversed`·`toSpliced`·`with`) | **ES2023**(TC39 finished proposals — Change Array by Copy) | node 18 에 없고 node 20·Chrome 에 있다 — **이 주제 밖**, [25번](../25-array-non-mutating-and-copy-methods/2-summary.md) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 메서드 **15개** × 세 칸(반환값이 원본인가 · 내용 · `length`) — **y 칸을 스크립트가 센다**(동작 (1)) · 같은 키 정렬을 **길이 10가지**에서(동작 (4)) · 동결 배열 × 메서드 **11개** × 입력 셋(동작 (8)) |
> | ★★ **① 추상 연산에 로그 심기** | 비교 함수가 **몇 번 불리고 무엇을 받나** — `undefined` 가 비교 함수에 **한 번도 안 간다**(동작 (6)의 `[2]`) · 규칙을 어긴 비교 함수의 호출 수(동작 (5)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 동결 배열에 쓰기 · `sort(1)` · `length = -1` — ★ **던지는 기준이 「바꾸려 했나」가 아니라 「썼나」인 것**이 문구로 드러난다 · ★ **메서드는 비엄격 모드에서도 던지고 대입식만 조용한 것**(동작 (8)) |
> | ★ **⑤ 두 판 대조기** | 이 주제의 탐침은 **두 판에서 한 글자도 같았다**(아래 집계 줄 — 갈린 것은 **다른 주제의 탐침**이다) |
> | ★★ **창을 바꿔 물었다**(제5의 상태) | 「안정 정렬은 ES2019 부터」는 **판 대조로 물을 수 없다** — 이 머신에 ES2019 이전 엔진이 없다. 그래서 **명세 두 판의 문장**과 **같은 키 격자**로 바꿔 물었다. ★ 바꾼 창이 못 보는 것 — **옛 엔진이 실제로 불안정했나**는 못 본다 |
> | ★ **미룬 창 — Proxy `set` 트랩** | 「원본에 **몇 번** 쓰나」를 트랩으로 세는 창은 [25번](../25-array-non-mutating-and-copy-methods/2-summary.md)의 본체다 — 여기서는 **「썼다는 것」만** 동결 배열의 예외로 본다 |
> | ★ **부적용 — ③ 브랜드 태그** | 이 주제의 메서드는 전부 **「intentionally generic」**(명세 Note)이다 — `this` 가 배열인지 묻지 않는다. **잴 것이 없다** |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 가 한 줄도 없다. **잴 것이 없다** |
> | ★ **안 쟀다 — 성능** | 「`push` 가 `concat` 보다 빠르다」·「`shift` 는 느리다」를 **한 줄도 쓰지 않는다.** 호출 횟수는 셌고 시간·메모리는 안 쟀다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **난수 비교 함수의 분포**(어느 순서가 몇 번 나오나) — 블록에 **아예 안 찍었다**. 대신 **가짓수**만 찍는다(동작 (5)의 둘째 블록) | ★★★ 격자의 y/n 과 집계 줄 · 반환값 · 원본의 모양 · 구멍의 자리 · 비교 함수의 호출 수와 인자 · 예외의 **종류** · 난수 비교 함수의 **가짓수** |
> | ★★ **규칙을 어긴 비교 함수의 결과** — 흔들리지 않았다(50판 모두 한 가지). 그러나 명세가 **「implementation-defined」** 라 부르는 칸이다. **성질의 근거로 쓰지 않는다** | 예외 **문구** — V8 의 것이다. 두 판에서 같았지만 명세가 정하는 것은 종류뿐이다 |
> | `localeCompare` 결과 — ECMA-402(`Intl`)와 ICU 데이터에 매인다. 동작 (3)의 한 줄뿐이다 | — |
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(직접 선행 — 배열도 객체라 **참조로 오간다**) ·
> [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md)(동작 (8) — `freeze` 가 무엇을 막나) ·
> [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md)(`[...a]` 가 얕은 복사인 것 — 동작 (7)) · [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)(문자열 비교가 코드 유닛 순서).
> **이어지는 곳** — [25 — 배열 비변형·복사 메서드](../25-array-non-mutating-and-copy-methods/2-summary.md)(★★★ **짝이다** — 같은 격자를 복사판으로 · `set` 트랩 0회) · [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md)(구멍 격자 · `Array.from`).
>
> ★★ **경계 — 스택·큐의 원리는 [`cs/foundations/data-structures-basics/`](../../../../data-structures-basics/README.md) 가 정본이다.**
> 그쪽은 **스택(4절)·큐(5절)가 무엇이고 어디에 쓰나**까지, 여기는 **JS 배열의 네 메서드가 무엇을 돌려주고 원본을 어떻게 바꾸나**부터다.
> ★ **경계 — 비변형·복사 메서드는 25번이 정본이다.** 동작 (1)의 격자에 `slice`·`concat`·`map`·`filter`·`join` 을 넣은 것은 **대조 행**일 뿐이다.

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

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 이 주제의 탐침 아홉 개는 전부 `identical` 이다. `DIFFERS` 는 다른 주제(복사 메서드 — ES2023)의 탐침이다.

`identical 26  ·  differs 4  ·  total 30`

## 한눈에 — 쉽게 말하면

**변형 메서드는 「그 자리에서 고치는 수선공」이고, 무엇을 들고 돌아오느냐가 제각각이다.**
옷을 맡기면 수선공은 **그 옷 자체를** 고친다 — 새 옷을 만들어 주지 않는다.
그런데 돌아올 때 들고 오는 것이 다르다. 어떤 수선공은 **고친 그 옷**을 들고 오고(`sort`·`reverse`·`fill`·`copyWithin`),
어떤 수선공은 **옷걸이에 걸린 벌 수**를 적은 쪽지만 들고 오고(`push`·`unshift`), 어떤 수선공은 **떼어 낸 조각**을 들고 온다(`pop`·`shift`·`splice`).

- ★★★ **「고친 그 옷」을 받아서 「새 옷이 생겼다」고 믿으면 사고가 난다.** `const r = a.reverse()` 의 `r` 은 `a` 자신이다.
- ★★★ **정렬 수선공은 설명서(비교 함수)가 없으면 옷에 붙은 이름표(글자)로 줄 세운다.** `10` 은 이름표로 `"10"` 이라 `"9"` 앞에 선다.
- ★★ **이름표가 같은 옷끼리는 맡긴 순서를 지킨다**(안정 정렬, ES2019 부터 약속).
- ★★ **설명서가 앞뒤가 안 맞으면(`a > b` 처럼) 명세는 결과를 약속하지 않는다.** 이 판에서는 **한 자리도 안 움직였다.**

```text
   a = [3, 1, 2]

   a.sort()      -> a 자신 (내용이 [1,2,3] 으로 바뀌었다)       고친 옷을 들고 온다
   a.push(9)     -> 4      (a 는 [1,2,3,9])                      벌 수 쪽지를 들고 온다
   a.splice(1,1) -> [2]    (a 는 [1,3,9])                        떼어 낸 조각을 들고 온다
   a.slice(1)    -> 새 배열 (a 는 그대로)                         수선공이 아니다 -- 25번
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 그 옷 자체를 고친다 | 원본 배열의 인덱스 프로퍼티와 `length` 에 직접 `Set`/`Delete` 한다 | 격자의 `content` 열 · 동결 배열의 예외 |
| 고친 그 옷을 들고 온다 | 명세의 마지막 단계 **"Return O"**(`sort` 는 "Return obj") | 격자의 `same?` 열 |
| 벌 수 쪽지를 들고 온다 | `push`·`unshift` 가 **새 `length`** 를 돌려준다 | 동작 (2)의 `[1]` |
| 떼어 낸 조각을 들고 온다 | `pop`·`shift` 는 원소 하나, `splice` 는 **지운 것들의 새 배열** | 동작 (2)의 `[2]` |
| 설명서 없이 이름표로 | 비교 함수가 없으면 `CompareArrayElements` 가 **`ToString` 한 뒤 문자열 비교** | 동작 (3) |
| 앞뒤가 안 맞는 설명서 | 「consistent comparator」가 아니다 → **「implementation-defined」** | 동작 (5) |
| 이름표 없는 옷·빈 옷걸이는 맨 뒤 | `undefined` 는 끝으로, **구멍은 그 뒤로** | 동작 (6) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**점수 표를 정렬해 1등을 뽑았더니 원본 표 순서까지 바뀌어 화면이 흔들렸다**」와
「**숫자 배열을 `sort()` 했더니 `100` 이 `25` 앞에 왔다**」가 그것이다.
앞엣것은 **고친 옷을 새 옷으로 믿은** 것이고(동작 (7)), 뒤엣것은 **설명서 없이 이름표로 줄 세운** 것이다(동작 (3)).

> **변형 메서드(mutating method)** — 호출한 배열 자체를 바꾸는 메서드. 원본에 쓰기(`Set`)나 지우기(`Delete`)를 한다.\
> 예: `a.sort()` 뒤에 `a` 의 순서가 바뀌어 있다.

> **비교 함수(comparator)** — `sort` 에 넘기는 `(x, y) => 수`. 음수면 x 가 앞, 양수면 y 가 앞, 0 이면 같다.\
> 예: `(a, b) => a - b` 는 숫자 오름차순.

> **구멍(hole)** — 배열의 자리 번호가 `length` 안에 있는데 **그 번호의 프로퍼티가 아예 없는** 것. `undefined` 가 들어 있는 것과 다르다.\
> 예: `[1, , 3]` 의 1번 자리 — `1 in arr` 이 `false`.

## 이 주제가 답하려는 질문

1. **무엇이 원본을 바꾸고, 무엇을 돌려주나** — 그리고 반환값이 원본이면 무엇이 새나?
2. **`sort` 는 무엇으로 비교하나** — 비교 함수가 없을 때 · 규칙을 어길 때 · `undefined` 와 구멍이 섞일 때.
3. **무엇이 명세의 약속이고 무엇이 이 엔진의 관찰인가** — 안정 정렬은 언제부터이고, 「구현 정의」 순서는 무엇을 뜻하나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 메서드 열다섯 개 × 세 칸 — 이 주제의 본체

**언제 쓰나** — 「이 메서드 뒤에 원본을 다시 써도 되나」·「반환값을 새 배열로 써도 되나」를 물을 때.
★★★ 이름으로 외우면 `push`(원본을 바꾸는데 원본을 안 돌려준다)와 `sort`(원본을 바꾸는데 **원본을** 돌려준다)를 한 칸에 넣게 된다. 그래서 전부 들이댔다.

```js
// js24b-24a-mutation-grid.js
// 메서드마다 세 가지를 묻는다 -- 반환값이 원본 그 자체인가 · 원본의 내용이 달라졌나 · length 가 달라졌나.
// 스크립트가 y 칸을 직접 센다.
const rows = [
  ["push(9)", (a) => a.push(9)],
  ["pop()", (a) => a.pop()],
  ["shift()", (a) => a.shift()],
  ["unshift(9)", (a) => a.unshift(9)],
  ["splice(1, 1)", (a) => a.splice(1, 1)],
  ["splice(1, 0, 9)", (a) => a.splice(1, 0, 9)],
  ["sort()", (a) => a.sort()],
  ["reverse()", (a) => a.reverse()],
  ["fill(0)", (a) => a.fill(0)],
  ["copyWithin(0, 2)", (a) => a.copyWithin(0, 2)],
  ["slice(1)", (a) => a.slice(1)],
  ["concat([9])", (a) => a.concat([9])],
  ["map(x => x)", (a) => a.map((x) => x)],
  ["filter(x => x > 1)", (a) => a.filter((x) => x > 1)],
  ["join()", (a) => a.join()],
];
const snap = (a) => JSON.stringify(a);
console.log("start value for every row: [3,1,2]");
console.log("");
console.log("method".padEnd(20) + "returns".padEnd(12) + "same?".padEnd(7) + "content".padEnd(9) + "length".padEnd(8) + "after");
let yes = 0, cells = 0, rowsChanged = 0, both = 0;
for (const [name, run] of rows) {
  const a = [3, 1, 2];
  const before = snap(a), len0 = a.length;
  const r = run(a);
  const same = r === a, content = snap(a) !== before, length = a.length !== len0;
  const yn = (b) => (b ? "y" : "n");
  for (const b of [same, content, length]) { cells++; if (b) yes++; }
  if (content) rowsChanged++;
  if (same && length) both++;
  const shown = r === a ? "(arr)" : snap(r);
  console.log(name.padEnd(20) + String(shown).padEnd(12) + yn(same).padEnd(7) + yn(content).padEnd(9) + yn(length).padEnd(8) + snap(a));
}
console.log("");
console.log("rows whose content column is y: " + rowsChanged + " / " + rows.length);
console.log("rows where same? and length are both y: " + both + " / " + rows.length);
console.log("cells answering y: " + yes + " / " + cells);
```
```text
===== node20 js24b-24a-mutation-grid.js (exit=0) =====
start value for every row: [3,1,2]

method              returns     same?  content  length  after
push(9)             4           n      y        y       [3,1,2,9]
pop()               2           n      y        y       [3,1]
shift()             3           n      y        y       [1,2]
unshift(9)          4           n      y        y       [9,3,1,2]
splice(1, 1)        [1]         n      y        y       [3,2]
splice(1, 0, 9)     []          n      y        y       [3,9,1,2]
sort()              (arr)       y      y        n       [1,2,3]
reverse()           (arr)       y      y        n       [2,1,3]
fill(0)             (arr)       y      y        n       [0,0,0]
copyWithin(0, 2)    (arr)       y      y        n       [2,1,2]
slice(1)            [1,2]       n      n        n       [3,1,2]
concat([9])         [3,1,2,9]   n      n        n       [3,1,2]
map(x => x)         [3,1,2]     n      n        n       [3,1,2]
filter(x => x > 1)  [3,2]       n      n        n       [3,1,2]
join()              "3,1,2"     n      n        n       [3,1,2]

rows whose content column is y: 10 / 15
rows where same? and length are both y: 0 / 15
cells answering y: 20 / 45
```

```text
   원본을 바꾸는 열 개가 두 가족으로 갈린다 -- 두 가족은 한 칸도 겹치지 않는다

                       same?   content   length      돌려주는 것
                       -----   -------   ------      -----------
   길이 가족            n       y         y          push·unshift -> 새 length
   (여섯)                                            pop·shift    -> 뺀 원소
                                                     splice       -> 지운 것들의 새 배열
   자리 가족            y       y         n          sort·reverse·fill·copyWithin -> 원본 그 자체
   (넷)
   대조 행              n       n         n          slice·concat·map·filter·join -> 새 값 (25번)
   (다섯)
```

- ★★★ **집계 — `cells answering y: 20 / 45`, `rows whose content column is y: 10 / 15`.** 열 개가 원본의 **내용**을 바꾼다.
- ★★★ **`rows where same? and length are both y: 0 / 15`** — **원본을 돌려주는 메서드는 길이를 안 바꾸고, 길이를 바꾸는 메서드는 원본을 안 돌려준다.** 이 열다섯 개 안에서는 한 칸도 겹치지 않았다.
  ★ 그래서 「반환값이 배열이면 원본이다」도 틀린다 — `splice` 는 **배열을 돌려주지만 원본이 아니다**(`[1]`).
- ★★ **`splice(1, 0, 9)` 는 아무것도 안 지워도 원본을 바꾼다** — 반환값 `[]` 만 보고 「아무 일도 없었다」로 읽으면 틀린다.
- ★★ **`copyWithin(0, 2)` 가 `[2,1,2]`** — 길이는 그대로이고 자리 0 에 자리 2 의 값을 **덮어썼다.** 세부는 동작 (7)의 `[4]`.
- ★ 대조 행 다섯은 세 칸이 전부 n 이다 — **새 값을 돌려주고 원본을 안 건드린다.** 그 쪽의 정본은 [25번](../25-array-non-mutating-and-copy-methods/2-summary.md)이다.

### (2) ★★ 넣고 빼는 넷과 `splice` — 무엇을 돌려주나

**언제 쓰나** — `const n = a.push(x)` 의 `n` 을 쓰거나, `splice` 의 반환값으로 「지운 것」을 받을 때.
★ 이 절의 블록(`js24b-24b-return-values.js`)은 소스와 출력 전문이 [1-question.md](1-question.md)·[3-answer.md](3-answer.md) 의 2번에 있다 — 여기서는 그림으로 읽는다.

```text
   a.splice(start, deleteCount, ...items)

      ["a","b","c","d","e"].splice(1, 2, "x", "y", "z")

       0    1    2    3    4
      "a" [ "b" "c" ] "d" "e"          start 1 부터 2 개를 떼어 낸다
            └──┬──┘
               └─────────▶ 돌려주는 것  ["b","c"]   (지운 것들의 새 배열)
      "a" "x" "y" "z" "d" "e"          그 자리에 items 를 끼운다 -> 원본 length 5 -> 6

   deleteCount 를 빼면     -> start 부터 끝까지 지운다       splice(2)  -> ["c","d","e"]
   인자를 다 빼면           -> 아무것도 안 지운다             splice()   -> []
   start 가 길이를 넘으면   -> 끝에 붙인다                    splice(9, 1, "x") -> [] , 원본 끝에 "x"
```

- ★★★ **`push`·`unshift` 는 새 `length` 를 돌려준다** — `a.push(3, 4)` 가 `4`. **넣은 값이 아니다.** 빈 배열에 `push()` 는 `0`.
- ★★ **`pop`·`shift` 는 뺀 원소를, 빈 배열에서는 `undefined`** 를 돌려준다. **던지지 않는다.**
- ★★★ **`splice` 는 지운 것들을 새 배열로** 돌려준다 — 끼우기만 하면(`splice(1, 0, 'x')`) `[]`.
  명세 Note 1 — "It returns an Array containing the deleted elements (if any)."
  ★ `deleteCount` 가 **없을 때**와 **0 일 때**가 다르다 — 명세가 「start 가 없으면 0 개」, 「deleteCount 가 없으면 끝까지」를 따로 적는다(`splice()` 는 `[]`, `splice(2)` 는 셋).
- ★ **`push([2, 3])` 은 배열 하나를 원소 하나로** 넣는다(`[1,[2,3]]`, 반환 `2`). 펼쳐 넣으려면 `push(...[2, 3])` — 스프레드는 [11번](../11-spread-and-rest/2-summary.md)이 정본이다.

### (3) ★★★ 비교 함수가 없으면 — 글자로 줄 세운다

**언제 쓰나** — 숫자 배열을 `sort()` 할 때(거의 언제나 틀린다) · 비교 함수를 짧게 쓰려다 불리언을 돌려줄 때.

```js
// js24b-24c-default-order.js
// 비교 함수 없이 sort() 를 부르면 무엇을 기준으로 줄 세우나.
const show = (label, r) => console.log(label.padEnd(48) + "-> " + JSON.stringify(r));

console.log("[1] no comparator");
show("[10, 9, 1].sort()", [10, 9, 1].sort());
show("[5, 25, 100, 1].sort()", [5, 25, 100, 1].sort());
show("[-1, -2, 3, -10].sort()", [-1, -2, 3, -10].sort());
show("[3, 'a', 1, 'B', true].sort()", [3, "a", 1, "B", true].sort());
show("['b', 'a', 'C', 'A'].sort()", ["b", "a", "C", "A"].sort());
show("[0.5, 1e21, 2, 1e-7].sort()", [0.5, 1e21, 2, 1e-7].sort());

console.log("");
console.log("[2] what each element is compared as");
for (const x of [10, 9, 1, -10, 1e21, 1e-7, true]) {
  console.log("  " + String(x).padEnd(8) + "String(x) = " + JSON.stringify(String(x)));
}

console.log("");
console.log("[3] with a numeric comparator");
show("[10, 9, 1].sort((a, b) => a - b)", [10, 9, 1].sort((a, b) => a - b));
show("[5, 25, 100, 1].sort((a, b) => a - b)", [5, 25, 100, 1].sort((a, b) => a - b));
show("[5, 25, 100, 1].sort((a, b) => b - a)", [5, 25, 100, 1].sort((a, b) => b - a));
show("['b','a','C','A'].sort(localeCompare)", ["b", "a", "C", "A"].sort((x, y) => x.localeCompare(y, "en")));

console.log("");
console.log("[4] a comparator that returns a boolean");
const boolCmp = (a, b) => a > b;
for (const arr of [[3, 1, 2], [1, 3, 2], [2, 1], [5, 1, 4, 2, 3], [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]]) {
  const input = JSON.stringify(arr);
  show("  " + input + ".sort((a, b) => a > b)", arr.sort(boolCmp));
}

console.log("");
console.log("[5] a comparator argument that is not a function");
for (const [label, arg] of [["sort(undefined)", undefined], ["sort(null)", null], ["sort(1)", 1], ["sort('desc')", "desc"]]) {
  try {
    console.log(label.padEnd(48) + "-> " + JSON.stringify([2, 1].sort(arg)));
  } catch (e) {
    console.log(label.padEnd(48) + "-> " + e.constructor.name + " 「" + e.message + "」");
  }
}
```
```text
===== node20 js24b-24c-default-order.js (exit=0) =====
[1] no comparator
[10, 9, 1].sort()                               -> [1,10,9]
[5, 25, 100, 1].sort()                          -> [1,100,25,5]
[-1, -2, 3, -10].sort()                         -> [-1,-10,-2,3]
[3, 'a', 1, 'B', true].sort()                   -> [1,3,"B","a",true]
['b', 'a', 'C', 'A'].sort()                     -> ["A","C","a","b"]
[0.5, 1e21, 2, 1e-7].sort()                     -> [0.5,1e+21,1e-7,2]

[2] what each element is compared as
  10      String(x) = "10"
  9       String(x) = "9"
  1       String(x) = "1"
  -10     String(x) = "-10"
  1e+21   String(x) = "1e+21"
  1e-7    String(x) = "1e-7"
  true    String(x) = "true"

[3] with a numeric comparator
[10, 9, 1].sort((a, b) => a - b)                -> [1,9,10]
[5, 25, 100, 1].sort((a, b) => a - b)           -> [1,5,25,100]
[5, 25, 100, 1].sort((a, b) => b - a)           -> [100,25,5,1]
['b','a','C','A'].sort(localeCompare)           -> ["a","A","b","C"]

[4] a comparator that returns a boolean
  [3,1,2].sort((a, b) => a > b)                 -> [3,1,2]
  [1,3,2].sort((a, b) => a > b)                 -> [1,3,2]
  [2,1].sort((a, b) => a > b)                   -> [2,1]
  [5,1,4,2,3].sort((a, b) => a > b)             -> [5,1,4,2,3]
  [10,9,8,7,6,5,4,3,2,1].sort((a, b) => a > b)  -> [10,9,8,7,6,5,4,3,2,1]

[5] a comparator argument that is not a function
sort(undefined)                                 -> [1,2]
sort(null)                                      -> TypeError 「The comparison function must be either a function or undefined」
sort(1)                                         -> TypeError 「The comparison function must be either a function or undefined」
sort('desc')                                    -> TypeError 「The comparison function must be either a function or undefined」
```

```text
   CompareArrayElements(x, y, comparator)

   ① x, y 둘 다 undefined?        -> 0
   ② x 가 undefined?               -> 1    (x 를 뒤로)
   ③ y 가 undefined?               -> -1   (y 를 뒤로)            <- 비교 함수보다 먼저 온다
   ④ comparator 가 있으면           -> ToNumber(comparator(x, y)), NaN 이면 0
   ⑤ 없으면  String(x) 와 String(y) 를 코드 유닛 순서로 비교

      10, 9, 1  --String-->  "10", "9", "1"
      "1" < "10" < "9"        (첫 글자 "1" "1" "9", 둘째 글자에서 "" < "0")
      결과 [1, 10, 9]
```

- ★★★ **`[10, 9, 1].sort()` 는 `[1,10,9]`** 다. 비교 함수가 없으면 명세 `CompareArrayElements` 가 **두 값을 `ToString` 한 뒤** 문자열로 비교한다(⑤). `[2]` 가 각 원소의 글자를 보여 준다.
  ★ 같은 이유로 `[5, 25, 100, 1]` 은 `[1,100,25,5]`, 음수는 `"-"` 가 먼저라 `[-1,-10,-2,3]`, `1e21` 은 `"1e+21"` 로 `2` 보다 앞이다.
- ★★ **타입이 섞여도 던지지 않는다** — `[3, 'a', 1, 'B', true]` 가 `[1,3,"B","a",true]`. 전부 글자가 되어 비교된다. **대문자가 소문자보다 앞**이다(코드 유닛 순서 — [04번](../04-strings-and-utf16/2-summary.md)).
- ★★ **숫자 순서는 비교 함수로** — `(a, b) => a - b`. 내림차순은 `b - a`. 사람의 알파벳 순서는 `localeCompare`(ECMA-402 — 이 한 줄은 ICU 데이터에 매인다).
- ★★★ **`[4]` 불리언을 돌려주는 비교 함수 `(a, b) => a > b` — 이 판에서는 다섯 입력 전부 한 자리도 안 움직였다.** `[10,9,…,1]` 이 그대로다.
  ★ 불리언은 `ToNumber` 로 **`1` 아니면 `0`** 이 된다(④). **음수가 한 번도 안 나오므로** 「x 가 앞」이라는 답을 정렬이 영영 못 받는다.
  ★★ **다만 「안 움직인다」는 이 판의 관찰이다** — 이런 비교 함수의 결과를 명세는 약속하지 않는다(동작 (5)).
- ★★ **`[5]` 비교 자리에 함수가 아닌 값** — `undefined` 만 통과하고(비교 함수 없음과 같다), `null`·`1`·`'desc'` 는 **`TypeError 「The comparison function must be either a function or undefined」`**.
  명세 `Array.prototype.sort` 의 **첫 단계**가 이것이다 — 배열을 읽기 **전에** 던진다.

### (4) ★★★ 안정 정렬 — 같은 키끼리 원래 순서를 지키나

**언제 쓰나** — 기준이 둘 이상일 때(부서별로 묶고 그 안에서 등급 순) · 「동점이면 원래 순서」를 기대할 때.

```js
// js24b-24d-equal-keys.js
// 키가 같은 원소들은 정렬 뒤에 원래 순서를 지키나 -- 길이를 바꿔 가며 묻는다.
// 원소 = { k: 키(0~2), i: 원래 자리 }. 키로만 비교한다.
const make = (n) => Array.from({ length: n }, (_, i) => ({ k: (i * 7) % 3, i }));
const kept = (sorted) => sorted.every((x, j) => j === 0 || sorted[j - 1].k !== x.k || sorted[j - 1].i < x.i);

console.log("[1] a small case, printed in full");
const small = make(9);
console.log("before  " + small.map((x) => x.k + ":" + x.i).join(" "));
small.sort((a, b) => a.k - b.k);
console.log("after   " + small.map((x) => x.k + ":" + x.i).join(" "));

console.log("");
console.log("[2] same question at many lengths");
let ok = 0, total = 0;
for (const n of [2, 5, 10, 11, 22, 23, 50, 100, 1000, 10000]) {
  const s = make(n).sort((a, b) => a.k - b.k);
  const r = kept(s);
  total++; if (r) ok++;
  console.log("  n = " + String(n).padEnd(6) + "equal-key groups in original order? " + (r ? "y" : "n"));
}
console.log("lengths answering y: " + ok + " / " + total);

console.log("");
console.log("[3] two passes -- secondary key first, then primary key");
const people = [["kim", "dev", 3], ["lee", "ops", 1], ["park", "dev", 1], ["choi", "ops", 3], ["jung", "dev", 1]];
const p = people.slice();
p.sort((a, b) => a[2] - b[2]);
p.sort((a, b) => (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
console.log(JSON.stringify(p));
```
```text
===== node20 js24b-24d-equal-keys.js (exit=0) =====
[1] a small case, printed in full
before  0:0 1:1 2:2 0:3 1:4 2:5 0:6 1:7 2:8
after   0:0 0:3 0:6 1:1 1:4 1:7 2:2 2:5 2:8

[2] same question at many lengths
  n = 2     equal-key groups in original order? y
  n = 5     equal-key groups in original order? y
  n = 10    equal-key groups in original order? y
  n = 11    equal-key groups in original order? y
  n = 22    equal-key groups in original order? y
  n = 23    equal-key groups in original order? y
  n = 50    equal-key groups in original order? y
  n = 100   equal-key groups in original order? y
  n = 1000  equal-key groups in original order? y
  n = 10000 equal-key groups in original order? y
lengths answering y: 10 / 10

[3] two passes -- secondary key first, then primary key
[["park","dev",1],["jung","dev",1],["kim","dev",3],["lee","ops",1],["choi","ops",3]]
```

```text
   원소 = 키:원래 자리       키로만 비교한다

   before  0:0 1:1 2:2 0:3 1:4 2:5 0:6 1:7 2:8
   after   0:0 0:3 0:6 | 1:1 1:4 1:7 | 2:2 2:5 2:8
           ^^^^^^^^^^^   ^^^^^^^^^^^   ^^^^^^^^^^^
           키 0 무리 안에서 원래 자리 0 < 3 < 6 -- 원래 순서 그대로

   그래서 두 번에 나눠 정렬할 수 있다 -- 덜 중요한 기준을 먼저
     1차: 등급으로 정렬       2차: 부서로 정렬(같은 부서 안에서는 1차의 등급 순이 남는다)
```

- ★★★ **`[1]` 같은 키 무리 안에서 원래 자리가 오름차순**이다 — 키 0 무리가 `0:0 0:3 0:6`.
- ★★★ **`[2]` 길이 열 가지 전부 y** — `lengths answering y: 10 / 10`. 짧은 배열과 긴 배열에서 알고리즘을 갈아 끼우는 엔진이 있어도 **결과는 안정**이어야 한다 — 그래서 길이를 넓게 흩었다.
- ★★ **`[3]` 두 번 나눠 정렬** — 등급으로 한 번, 부서로 한 번. 결과가 `dev` 무리 안에서 **등급 1 → 3** 이다. 두 번째 정렬이 첫 번째의 순서를 **동점 안에서 남겼기** 때문이다.
- ★★★ **판 경계** — 명세 **9판(ES2018)** 은 "The sort is not necessarily stable", **10판(ES2019)** 은 "The sort must be stable".
  최신 초안은 그 문장을 `SortIndexedProperties` 의 조건으로 옮겼다 — "if ℝ(SortCompare(old[j], old[k])) = 0, then π(j) < π(k); i.e., the sort is stable."
  ★★ **이 머신의 두 node 판은 둘 다 경계 뒤**다. 판 대조로는 이 경계를 **못 본다** — 그래서 **명세 두 판의 문장**과 **이 격자**로 바꿔 물었다(머리말의 「창을 바꿔 물었다」).
  ★ **「y 10 / 10」은 보장의 증명이 아니다** — 보장은 명세 문장이고, 이 격자는 **이 판이 그 보장을 어기지 않았다는 관찰**이다.

### (5) ★★★ 비교 함수가 규칙을 어기면 — 명세는 「구현 정의」라 부른다

**언제 쓰나** — `() => Math.random() - 0.5` 로 섞으려 할 때 · 불리언이나 `1` 만 돌려주는 비교 함수를 썼을 때.

```js
// js24b-24e-inconsistent-fixed.js
// 일관되지 않은 비교 함수 -- 입력이 같으면 결과도 같나(이 블록의 비교 함수에는 난수가 없다).
const show = (label, r) => console.log(label.padEnd(44) + "-> " + JSON.stringify(r));
const base = [5, 1, 4, 2, 3];
const cmps = [
  ["() => 1", () => 1],
  ["() => -1", () => -1],
  ["() => 0", () => 0],
  ["(a, b) => a > b", (a, b) => a > b],
  ["(a, b) => a < b", (a, b) => a < b],
  ["(a, b) => (a % 2) - (b % 2) || 1", (a, b) => (a % 2) - (b % 2) || 1],
  ["() => NaN", () => NaN],
];
console.log("input " + JSON.stringify(base));
for (const [label, f] of cmps) {
  const outs = new Set();
  for (let t = 0; t < 50; t++) outs.add(JSON.stringify(base.slice().sort(f)));
  show(label, [...outs].map((s) => JSON.parse(s)));
  console.log("".padEnd(44) + "   distinct results over 50 runs: " + outs.size);
}

console.log("");
console.log("[2] how many times each comparator is called on the same input");
for (const [label, f] of cmps) {
  let calls = 0;
  base.slice().sort((a, b) => { calls++; return f(a, b); });
  console.log("  " + label.padEnd(42) + "calls " + calls);
}
```
```text
===== node20 js24b-24e-inconsistent-fixed.js (exit=0) =====
input [5,1,4,2,3]
() => 1                                     -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1
() => -1                                    -> [[3,2,4,1,5]]
                                               distinct results over 50 runs: 1
() => 0                                     -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1
(a, b) => a > b                             -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1
(a, b) => a < b                             -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1
(a, b) => (a % 2) - (b % 2) || 1            -> [[4,2,5,1,3]]
                                               distinct results over 50 runs: 1
() => NaN                                   -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1

[2] how many times each comparator is called on the same input
  () => 1                                   calls 4
  () => -1                                  calls 4
  () => 0                                   calls 4
  (a, b) => a > b                           calls 4
  (a, b) => a < b                           calls 4
  (a, b) => (a % 2) - (b % 2) || 1          calls 8
  () => NaN                                 calls 4
```

```text
   consistent comparator 의 조건                  () => 1   () => 0   a > b    () => NaN   Math.random() - 0.5
   ------------------------------------------   -------   -------   -----    ---------   -------------------
   같은 쌍에 늘 같은 값                              지킴      지킴      지킴     지킴        어김
   그 값이 Number 이고 NaN 이 아니다                 지킴      지킴      어김     어김        지킴
                                                                  (불리언)
   대칭 (a = b 이면 b = a · < 와 > 중 하나만)          어김      지킴      어김     -           어김
   반사 (a = a -- 자기 자신과는 같다)                어김      지킴      지킴     -           어김

   하나라도 어기면 -> "The sort order is implementation-defined"
   ★ () => 0 은 조건을 다 지킨다 -- 「전부 같다」는 정당한 답이고, 안정 정렬이라 입력 그대로가 약속된 결과다
```

- ★★★ **명세의 요구** — 비교 함수는 「consistent comparator」여야 한다. 조건의 첫 줄 —
  "Calling comparator(a, b) always returns the same value v when given a specific pair of values a and b as its two arguments. Furthermore, v is a Number, and v is not NaN."
  그 뒤로 반사성·대칭성·추이성이 온다. **`() => 1` 은 대칭성을 어긴다**(`a > b` 이면서 `b > a`), **`(a, b) => a > b` 는 「v is a Number」를 어긴다**(불리언).
- ★★★ **어기면** — "The sort order is implementation-defined if SortCompare is not a consistent comparator for the elements of items."
  ★ **던지지도 않고, 결과도 약속하지 않는다.** 원소가 **모두 남아 있다는 것**(순열 π)조차 「구현 정의」가 아닐 때의 조건이다.
- ★★ **이 판의 관찰** — 난수가 없는 비교 함수 일곱 개는 **50판 모두 한 가지 결과**였다. 흔들리지 않았다.
  ★ 음수를 한 번도 안 돌려주는 다섯 개(`() => 1` · `() => 0` · `a > b` · `a < b` · `() => NaN`)는 **입력 그대로**, 언제나 음수인 `() => -1` 은 **역순**(`[3,2,4,1,5]`)이 나왔다. 호출은 다섯 원소에 **4번**.
  ★★ **이 수들은 V8 의 한 판이 고른 것**이다. 「흔들리지 않았다」를 「그렇게 된다」로 옮기면 명세의 `implementation-defined` 를 지우는 것이 된다.

```js
// js24b-24f-inconsistent-random.js
// 비교 함수가 난수를 돌려주면 -- 같은 입력으로 여러 번 정렬해 서로 다른 결과가 몇 가지인지 센다.
// 분포(어느 결과가 몇 번)는 실행마다 흔들리므로 찍지 않는다. 가짓수와 그 목록만 찍는다.
const trials = 20000;
for (const base of [[1, 2, 3], [1, 2, 3, 4]]) {
  const outs = new Set();
  for (let t = 0; t < trials; t++) outs.add(base.slice().sort(() => Math.random() - 0.5).join(""));
  let perms = 1;
  for (let k = 2; k <= base.length; k++) perms *= k;
  console.log("input " + JSON.stringify(base) + "  trials " + trials);
  console.log("  distinct results: " + outs.size + " / " + perms + " permutations");
  console.log("  " + [...outs].sort().join(" "));
}
```
```text
===== node20 js24b-24f-inconsistent-random.js (exit=0) =====
input [1,2,3]  trials 20000
  distinct results: 6 / 6 permutations
  123 132 213 231 312 321
input [1,2,3,4]  trials 20000
  distinct results: 24 / 24 permutations
  1234 1243 1324 1342 1423 1432 2134 2143 2314 2341 2413 2431 3124 3142 3214 3241 3412 3421 4123 4132 4213 4231 4312 4321
```

- ★★★ **난수 비교 함수는 같은 입력에서 결과가 흔들린다** — 그래서 **분포는 안 찍고 가짓수만** 찍었다(규칙 11). 원소 3개에서 **`6 / 6`**, 4개에서 **`24 / 24`** — 2만 판 안에 **모든 순열이 나왔다.**
  ★ **가짓수는 흔들리지 않는다**(재대조 동일). **어느 순서가 몇 번**인지는 흔들리고, 그것이 **고르지 않다는 것**도 이 블록은 주장하지 않는다(안 쟀다).
- ★ **섞기에 쓰지 마라** — 명세가 결과를 약속하지 않는 도구로 「고르게 섞기」를 할 수 없다. 섞기는 피셔-예이츠(Fisher-Yates)로 직접 쓴다.

### (6) ★★ `undefined` 와 구멍 — 비교 함수보다 먼저 끝으로 간다

**언제 쓰나** — 데이터에 빈 칸(`undefined`)이나 희소 배열의 구멍이 섞여 있는 채로 정렬할 때.

```js
// js24b-24g-undefined-and-holes.js
// undefined 와 구멍(빈 자리)이 섞인 배열을 sort 하면 -- 결과 · 각 자리가 구멍인가 · 비교 함수가 무엇을 받았나.
const describe = (a) => "[" + Array.from({ length: a.length }, (_, i) => (i in a ? String(a[i]) : "<hole>")).join(", ") + "]  length " + a.length;

console.log("[1] no comparator");
const a = [3, undefined, 1, , 2, undefined, , 10];
console.log("before  " + describe(a));
a.sort();
console.log("after   " + describe(a));

console.log("");
console.log("[2] numeric comparator, logging every call");
const b = [3, undefined, 1, , 2];
const seen = [];
b.sort((x, y) => { seen.push(String(x) + "," + String(y)); return x - y; });
console.log("after   " + describe(b));
console.log("calls   " + seen.length + "   " + seen.join(" | "));
console.log("any call received undefined? " + (seen.some((s) => s.includes("undefined")) ? "y" : "n"));

console.log("");
console.log("[3] a comparator that returns -1 when x is undefined");
const c = [2, undefined, 1];
c.sort((x, y) => (x === undefined ? -1 : y === undefined ? 1 : x - y));
console.log("after   " + describe(c));

console.log("");
console.log("[4] null and undefined in one array");
const d = [2, null, 1, undefined];
d.sort();
console.log("after   " + describe(d));
const e2 = [2, null, 1, undefined];
e2.sort((x, y) => x - y);
console.log("numeric " + describe(e2));
```
```text
===== node20 js24b-24g-undefined-and-holes.js (exit=0) =====
[1] no comparator
before  [3, undefined, 1, <hole>, 2, undefined, <hole>, 10]  length 8
after   [1, 10, 2, 3, undefined, undefined, <hole>, <hole>]  length 8

[2] numeric comparator, logging every call
after   [1, 2, 3, undefined, <hole>]  length 5
calls   4   1,3 | 2,1 | 2,3 | 2,1
any call received undefined? n

[3] a comparator that returns -1 when x is undefined
after   [1, 2, undefined]  length 3

[4] null and undefined in one array
after   [1, 2, null, undefined]  length 4
numeric [null, 1, 2, undefined]  length 4
```

```text
   Array.prototype.sort 가 원본을 되돌려 놓는 법

   ① SortIndexedProperties(obj, len, SortCompare, skip-holes)
        자리 0..len-1 을 돈다. 구멍(HasProperty 가 false)은 건너뛴다    -> items 에 안 들어간다
   ② items 를 정렬 (undefined 는 CompareArrayElements ①~③ 이 끝으로 보낸다 -- 비교 함수에 안 간다)
   ③ items 를 자리 0 부터 차례로 Set  (값이 같아도 쓴다)
   ④ 남은 자리 j..len-1 을 DeletePropertyOrThrow -- 구멍이 끝으로 모인다

   [3, undefined, 1, <hole>, 2, undefined, <hole>, 10]
     items = [3, undefined, 1, 2, undefined, 10]          구멍 둘 빠짐
     정렬  = [1, 10, 2, 3, undefined, undefined]           글자 순 + undefined 끝
     쓰기  = 자리 0..5 에 Set,  자리 6·7 을 Delete
     결과    [1, 10, 2, 3, undefined, undefined, <hole>, <hole>]
```

- ★★★ **`[1]` 순서는 「값들 → `undefined` 들 → 구멍들」** 이다. `length` 는 그대로 8.
  명세 Note 1 — "undefined property values always sort to the end of the result, followed by non-existent property values."
- ★★★ **`[2]` 비교 함수는 `undefined` 를 한 번도 안 받았다**(`any call received undefined? n`). 네 번의 호출이 전부 숫자 쌍이다.
  `CompareArrayElements` 가 **비교 함수를 부르기 전에** `undefined` 를 처리하기 때문이다(①\~③).
- ★★ **`[3]` 그래서 「`undefined` 를 앞으로」는 비교 함수로 안 된다** — `x === undefined ? -1 : …` 을 써도 `[1, 2, undefined]`. 그 가지가 **불릴 일이 없다.**
  앞으로 보내려면 `undefined` 를 다른 값으로 바꾼 뒤 정렬한다.
- ★ **`[4]` `null` 은 `undefined` 가 아니다** — 기본 정렬에서는 `"null"` 이라는 글자로(`2` 뒤), 숫자 비교에서는 `ToNumber(null)` 이 `0` 이라 **맨 앞**으로 간다. `undefined` 만 끝 자리가 고정이다.

### (7) ★★★ 원본을 돌려주는 메서드 — 두 이름이 한 배열을 본다

**언제 쓰나** — `const sorted = arr.sort()` 처럼 반환값을 **새 이름**으로 받을 때 · `Array(n).fill(…)` 로 2차원 배열을 만들 때 · `length` 로 배열을 비울 때.

```js
// js24b-24h-same-array.js
// 원본을 돌려주는 메서드의 반환값을 「새 배열」로 받아 쓰면 -- 두 이름이 무엇을 가리키나.
const j = (x) => JSON.stringify(x);

console.log("[1] rev = orig.reverse()");
const orig = [1, 2, 3];
const rev = orig.reverse();
console.log("rev  " + j(rev) + "   orig " + j(orig) + "   rev === orig " + (rev === orig));

console.log("");
console.log("[2] four chains");
const scores = [30, 10, 20];
const top = scores.sort((a, b) => b - a).slice(0, 2);
console.log("top    " + j(top) + "   scores " + j(scores));
const names = ["c", "a", "b"];
const last = names.sort().reverse()[0];
console.log("last   " + j(last) + "   names " + j(names));
const src = [3, 1, 2];
const copied = src.slice().sort();
console.log("copied " + j(copied) + "   src " + j(src));
const spread = [...src].reverse();
console.log("spread " + j(spread) + "   src " + j(src));

console.log("");
console.log("[3] fill with an object");
const grid = Array(3).fill([]);
grid[0].push("x");
console.log("grid " + j(grid));
console.log("grid[0] === grid[1] " + (grid[0] === grid[1]) + "   grid[1] === grid[2] " + (grid[1] === grid[2]));
const rows = Array.from({ length: 3 }, () => []);
rows[0].push("x");
console.log("rows " + j(rows) + "   rows[0] === rows[1] " + (rows[0] === rows[1]));
const fresh = Array(3);
console.log("Array(3)            length " + fresh.length + "   0 in it " + (0 in fresh));
console.log("Array(3).fill(0)    " + j(Array(3).fill(0)));
console.log("[1,2,3,4].fill(9, 1, 3)  " + j([1, 2, 3, 4].fill(9, 1, 3)));
console.log("[1,2,3,4].fill(9, -1)    " + j([1, 2, 3, 4].fill(9, -1)));

console.log("");
console.log("[4] copyWithin(target, start, end)");
for (const [label, args] of [["copyWithin(0, 3)", [0, 3]], ["copyWithin(1, 0)", [1, 0]], ["copyWithin(0, 1, 3)", [0, 1, 3]], ["copyWithin(-2, 0)", [-2, 0]], ["copyWithin(2, 0, 2)", [2, 0, 2]]]) {
  const a = [1, 2, 3, 4, 5];
  const r = a.copyWithin(...args);
  console.log("  [1,2,3,4,5]." + label.padEnd(22) + "-> " + j(r) + "   length " + a.length + "   same " + (r === a));
}

console.log("");
console.log("[5] assigning to length");
const t = [1, 2, 3, 4, 5];
const alias = t;
t.length = 2;
console.log("after length = 2   t " + j(t) + "   alias " + j(alias) + "   t[3] " + t[3]);
t.length = 4;
console.log("after length = 4   t.length " + t.length + "   2 in t " + (2 in t) + "   t[2] " + t[2]);
alias.length = 0;
console.log("after alias.length = 0   t " + j(t));
for (const v of [-1, 1.5, 2 ** 32]) {
  try { const x = [1]; x.length = v; console.log("length = " + String(v).padEnd(12) + "-> " + x.length); }
  catch (e) { console.log("length = " + String(v).padEnd(12) + "-> " + e.constructor.name + " 「" + e.message + "」"); }
}
```
```text
===== node20 js24b-24h-same-array.js (exit=0) =====
[1] rev = orig.reverse()
rev  [3,2,1]   orig [3,2,1]   rev === orig true

[2] four chains
top    [30,20]   scores [30,20,10]
last   "c"   names ["c","b","a"]
copied [1,2,3]   src [3,1,2]
spread [2,1,3]   src [3,1,2]

[3] fill with an object
grid [["x"],["x"],["x"]]
grid[0] === grid[1] true   grid[1] === grid[2] true
rows [["x"],[],[]]   rows[0] === rows[1] false
Array(3)            length 3   0 in it false
Array(3).fill(0)    [0,0,0]
[1,2,3,4].fill(9, 1, 3)  [1,9,9,4]
[1,2,3,4].fill(9, -1)    [1,2,3,9]

[4] copyWithin(target, start, end)
  [1,2,3,4,5].copyWithin(0, 3)      -> [4,5,3,4,5]   length 5   same true
  [1,2,3,4,5].copyWithin(1, 0)      -> [1,1,2,3,4]   length 5   same true
  [1,2,3,4,5].copyWithin(0, 1, 3)   -> [2,3,3,4,5]   length 5   same true
  [1,2,3,4,5].copyWithin(-2, 0)     -> [1,2,3,1,2]   length 5   same true
  [1,2,3,4,5].copyWithin(2, 0, 2)   -> [1,2,1,2,5]   length 5   same true

[5] assigning to length
after length = 2   t [1,2]   alias [1,2]   t[3] undefined
after length = 4   t.length 4   2 in t false   t[2] undefined
after alias.length = 0   t []
length = -1          -> RangeError 「Invalid array length」
length = 1.5         -> RangeError 「Invalid array length」
length = 4294967296  -> RangeError 「Invalid array length」
```

```text
   const rev = orig.reverse()

   orig ──┐
          ├──▶ [3, 2, 1]        하나뿐이다. rev === orig
   rev ───┘

   Array(3).fill([])                          Array.from({length: 3}, () => [])

   grid[0] ──┐                                rows[0] ──▶ []
   grid[1] ──┼──▶ [ ]  (배열 하나)             rows[1] ──▶ []
   grid[2] ──┘                                rows[2] ──▶ []
   fill 은 인자를 한 번 평가해 같은 값을 세 자리에 Set 한다     콜백이 자리마다 새 [] 를 만든다
```

- ★★★ **`[1]` `rev === orig` 가 true** — `reverse` 는 원본을 뒤집고 **원본을** 돌려준다. 「원본을 두고 뒤집은 사본」을 원했다면 실패다.
- ★★★ **`[2]` 체인의 첫 고리가 변형 메서드면 원본이 바뀐다** — `scores.sort(…).slice(0, 2)` 뒤에 `scores` 가 `[30,20,10]`, `names.sort().reverse()[0]` 뒤에 `names` 가 `["c","b","a"]`.
  ★ **복사를 먼저 하면 원본이 산다** — `src.slice().sort()` · `[...src].reverse()` 뒤에 `src` 가 `[3,1,2]` 그대로. 복사판 메서드(`toSorted`·`toReversed`)는 [25번](../25-array-non-mutating-and-copy-methods/2-summary.md)이다.
- ★★★ **`[3]` `Array(3).fill([])` 은 배열 하나를 세 자리에** 넣는다 — `grid[0].push("x")` 한 번에 세 칸이 다 `["x"]`, `grid[0] === grid[1]` 이 true.
  명세 `fill` 은 `value` 하나를 받아 **자리마다 `Set(O, Pk, value)`** 할 뿐이다 — 복사하지 않는다. 자리마다 새 배열이 필요하면 `Array.from({ length: 3 }, () => [])`(`rows[0] === rows[1]` 이 false — `Array.from` 은 [26번](../26-array-search-flatten-and-create/2-summary.md)).
  ★ `Array(3)` 은 **구멍 셋**이다(`0 in it false`). `fill` 이 그 구멍을 **값으로 채운다.** `fill(9, 1, 3)` 은 자리 1·2, `fill(9, -1)` 은 끝 자리.
- ★★ **`[4]` `copyWithin(target, start, end)`** — 배열 **안에서** `start..end` 조각을 `target` 자리로 덮어쓴다. 길이는 안 바뀌고 원본을 돌려준다.
  ★ **겹쳐도 원본 값으로 복사된다** — `copyWithin(1, 0)` 이 `[1,1,2,3,4]` 다(`[1,1,1,1,1]` 이 아니다). 명세가 `from < to` 이고 겹치면 **뒤에서부터(direction −1)** 복사한다.
- ★★★ **`[5]` `length` 대입은 자른다** — `t.length = 2` 뒤에 `t` 가 `[1,2]`, **같은 배열을 보는 `alias` 도** `[1,2]`. 늘리면(`length = 4`) **구멍**이 생긴다(`2 in t false`).
  `alias.length = 0` 은 **그 배열을 보는 모든 이름에서** 비운다. `-1` · `1.5` · `2 ** 32` 는 **`RangeError 「Invalid array length」`** — `ArraySetLength` 는 `ToUint32` 한 값과 `ToNumber` 한 값이 다르면 `RangeError` 를 던진다.

### (8) ★★ 동결된 배열 — 「바꾸려 했나」가 아니라 「썼나」에서 던진다

**언제 쓰나** — `Object.freeze` 한 설정 배열에 실수로 변형 메서드를 부를 때 · 「이미 정렬돼 있으면 괜찮겠지」를 믿을 때.

```js
// js24b-24i-frozen-target.js
"use strict";
// 동결된 배열에 변형 메서드를 부르면 -- 던지나, 던지면 무엇을. 원본은 어떻게 남나.
const calls = [
  ["push(9)", (a) => a.push(9)],
  ["pop()", (a) => a.pop()],
  ["shift()", (a) => a.shift()],
  ["unshift(9)", (a) => a.unshift(9)],
  ["splice(0, 1)", (a) => a.splice(0, 1)],
  ["sort()", (a) => a.sort()],
  ["reverse()", (a) => a.reverse()],
  ["fill(0)", (a) => a.fill(0)],
  ["copyWithin(0, 1)", (a) => a.copyWithin(0, 1)],
  ["length = 0", (a) => { a.length = 0; }],
  ["slice()", (a) => a.slice()],
];
for (const input of [[3, 1, 2], [1, 2, 3], []]) {
  console.log("frozen " + JSON.stringify(input));
  for (const [label, run] of calls) {
    const a = Object.freeze(input.slice());
    let r;
    try { run(a); r = "no throw"; }
    catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
    console.log("  " + label.padEnd(18) + r.padEnd(70) + "  after " + JSON.stringify(a));
  }
}
```
```text
===== node20 js24b-24i-frozen-target.js (exit=0) =====
frozen [3,1,2]
  push(9)           TypeError 「Cannot add property 3, object is not extensible」             after [3,1,2]
  pop()             TypeError 「Cannot delete property '2' of [object Array]」                after [3,1,2]
  shift()           TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  unshift(9)        TypeError 「Cannot add property 3, object is not extensible」             after [3,1,2]
  splice(0, 1)      TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  sort()            TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  reverse()         TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  fill(0)           TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  copyWithin(0, 1)  TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  length = 0        TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after [3,1,2]
  slice()           no throw                                                                after [3,1,2]
frozen [1,2,3]
  push(9)           TypeError 「Cannot add property 3, object is not extensible」             after [1,2,3]
  pop()             TypeError 「Cannot delete property '2' of [object Array]」                after [1,2,3]
  shift()           TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  unshift(9)        TypeError 「Cannot add property 3, object is not extensible」             after [1,2,3]
  splice(0, 1)      TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  sort()            TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  reverse()         TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  fill(0)           TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  copyWithin(0, 1)  TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  length = 0        TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after [1,2,3]
  slice()           no throw                                                                after [1,2,3]
frozen []
  push(9)           TypeError 「Cannot add property 0, object is not extensible」             after []
  pop()             TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after []
  shift()           TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after []
  unshift(9)        TypeError 「Cannot add property 0, object is not extensible」             after []
  splice(0, 1)      TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after []
  sort()            no throw                                                                after []
  reverse()         no throw                                                                after []
  fill(0)           no throw                                                                after []
  copyWithin(0, 1)  no throw                                                                after []
  length = 0        TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after []
  slice()           no throw                                                                after []
```

```text
   frozen 배열 -- 명세의 단계가 원본에 무엇을 부르나 -> 그 첫 호출에서 던진다

   push(9)          Set(O, "3", 9)            새 자리 -> not extensible
   pop()            Delete(O, "2")            지우기 -> Cannot delete
   sort() · reverse() · fill() · copyWithin() · shift() · splice()
                    Set(O, "0", …)            있는 자리 -> read only property '0'
   빈 배열의 pop() · shift() · splice()
                    Set(O, "length", 0)       같은 값 0 을 다시 쓴다 -> read only property 'length'
   빈 배열의 sort() · reverse() · fill() · copyWithin()
                    (Set 도 Delete 도 없다)   -> 안 던진다
   slice()          원본에는 Get 만           -> 안 던진다
```

- ★★★ **`frozen [3,1,2]` — 변형 메서드 열 개가 전부 `TypeError`**, `slice()` 만 통과한다. 원본은 **한 글자도 안 바뀐 채** 남는다.
  문구는 **셋**이다 — 새 자리를 만들려 하면 `Cannot add property 3, object is not extensible`, 지우려 하면 `Cannot delete property '2' of [object Array]`, 있는 자리에 쓰려 하면 `Cannot assign to read only property '0' …`.
  **첫 쓰기에서 던진다** — `push` 는 자리 3 을 **만들다가**, `pop` 은 자리 2 를 **지우다가** 막혔다.
- ★★★ **`frozen [1,2,3]` 에서도 `sort()` 가 던진다** — **이미 정렬돼 있는데** 던진다. 명세 `sort` 는 정렬한 목록을 **자리 0 부터 전부 `Set`** 한다(동작 (6)의 그림 ③). 값이 같아도 쓴다.
- ★★★ **`frozen []` 에서는 `sort`·`reverse`·`fill`·`copyWithin` 이 안 던진다** — 쓸 자리가 **하나도 없다.**
  그런데 **`pop`·`shift`·`splice` 는 던진다** — 문구가 `'length'` 다. 명세 `shift` 는 길이가 0 이어도 **`Set(O, "length", +0)`** 을 하고 나서 `undefined` 를 돌려준다. **같은 값 0 을 다시 쓰다가** 막혔다.
  ★ **기준 한 문장** — 「원본이 바뀌나」가 아니라 **「명세의 단계가 원본에 `Set`/`Delete` 를 부르나」** 에서 던진다.

★★★ **그런데 이 블록은 엄격 모드다 — 지시어를 빼면 무엇이 바뀌나.**

```js
// js24b-24j-frozen-sloppy.js
// 같은 질문을 엄격 모드 지시어 없이 -- 메서드 호출과 대입식 두 가지로.
const calls = [
  ["a.push(9)", (a) => a.push(9)],
  ["a.sort()", (a) => a.sort()],
  ["a.reverse()", (a) => a.reverse()],
  ["a.length = 0", (a) => { a.length = 0; }],
  ["a[0] = 9", (a) => { a[0] = 9; }],
  ["a[3] = 9", (a) => { a[3] = 9; }],
];
console.log("strict mode here? " + (function () { return this === undefined; })());
for (const [label, run] of calls) {
  const a = Object.freeze([3, 1, 2]);
  let r;
  try { run(a); r = "no throw"; }
  catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(16) + r.padEnd(70) + "  after " + JSON.stringify(a));
}
```
```text
===== node20 js24b-24j-frozen-sloppy.js (exit=0) =====
strict mode here? false
  a.push(9)       TypeError 「Cannot add property 3, object is not extensible」             after [3,1,2]
  a.sort()        TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  a.reverse()     TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  a.length = 0    no throw                                                                after [3,1,2]
  a[0] = 9        no throw                                                                after [3,1,2]
  a[3] = 9        no throw                                                                after [3,1,2]
```

- ★★★ **비엄격 모드에서도 메서드는 던진다** — `push`·`sort`·`reverse` 가 같은 `TypeError`. **대입식만 조용하다** — `a.length = 0` · `a[0] = 9` · `a[3] = 9` 가 `no throw` 이고 원본은 그대로다.
  ★ 명세의 변형 메서드는 쓰기를 전부 **`Set(O, P, V, true)`** — 마지막 인자 `true` 가 「실패하면 던져라」다 — 로 부른다. **호출한 코드가 엄격 모드인지와 상관이 없다.**
  대입식 `a[0] = 9` 는 **그 코드의 모드**를 따른다 — 비엄격이면 실패를 삼킨다. `freeze` 와 모드의 관계 자체는 [14번](../14-property-descriptors-and-freezing/2-summary.md)이 정본이다.
- ★ 쓰기 **횟수**(몇 번 `Set` 했나)는 이 창으로는 못 센다 — 첫 쓰기에서 멈추기 때문이다. 그것은 Proxy `set` 트랩으로 [25번](../25-array-non-mutating-and-copy-methods/2-summary.md)이 센다.

### (9) ★★ 파이썬과의 대비 — 무엇을 돌려주고, 기본은 무엇으로 비교하나

**언제 쓰나** — 파이썬 `list.sort` 습관으로 JS `sort` 를 예상할 때.

파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **10번**(리스트 메서드와 정렬 키)과 **31번**(비교 프로토콜과 정렬 가능성)이 실측했다 — 그 문서들의 출력만 인용한다.

| 자리 | 파이썬(10번·31번의 출력) | JS(이 문서의 출력) | 무엇이 갈리나 |
|---|---|---|---|
| 제자리 정렬의 반환값 | **`x.sort()        -> None`** — `append`·`reverse` 도 전부 `None` | **원본 그 자체**(동작 (1) — `same?` y) | ★★★ 파이썬은 **체이닝이 막힌다**, JS 는 **체이닝이 원본을 바꾼다** |
| 체이닝의 사고 | `sort().reverse()-> AttributeError 'NoneType' object has no attribute 'reverse'` — **그 자리에서 터진다** | `names.sort().reverse()[0]` 이 **조용히** 원본을 뒤집는다(동작 (7)의 `[2]`) | 파이썬의 사고는 시끄럽고 JS 의 사고는 **조용하다** |
| 새 리스트로 정렬 | `sorted(y)       -> [1, 3] \| y = [3, 1]` | `slice().sort()` · `[...a].sort()` · ES2023 `toSorted` | 파이썬은 처음부터 **이름이 둘**이다 |
| 기본 비교 | **값 비교**(`<`) — `[3,'a',1].sort()   -> TypeError '<' not supported between instances of 'str' and 'int'` | **글자 비교** — 섞여도 안 던진다, 숫자도 `[1,10,9]`(동작 (3)) | ★★★ 파이썬은 **못 비교하면 던지고**, JS 는 **전부 글자로 만들어 비교한다** |
| 실패한 정렬 뒤 원본 | `[3,1,2,'a'].sort()` 가 던진 뒤 `m2 = [1, 2, 3, 'a']` — **일부가 정렬된 채** 남는다 | 기본 정렬은 타입 때문에 던질 일이 없다. 동결 배열은 **첫 쓰기에서** 던져 원본이 그대로였다(동작 (8)) | 던지는 이유가 다르다 |
| 안정성 | 라이브러리 문서가 "guaranteed to be stable" · `reverse=True` 도 안정(31번 ③) | **ES2019 부터 명세**(동작 (4)) | 둘 다 **언어 쪽 약속**이다. JS 는 **판 경계가 있다** |

- ★★★ **방향이 반대다** — 파이썬은 **「바꾸는 메서드는 아무것도 안 돌려준다」** 로 사고를 **시끄럽게** 만들었고, JS 는 **원본을 돌려줘** 체이닝을 허락한 대신 사고가 **조용하다.**
- ★ **파이썬 쪽은 이 배치에서 다시 돌리지 않았다** — 10번·31번 문서에 실린 출력을 인용했다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28).

| 형태 | 돌려주는 것 | 원본 | 어디서 봤나 |
|---|---|---|---|
| `a.push(...items)` · `a.unshift(...items)` | **새 `length`** | 끝 · 앞에 넣는다 | 동작 (2)의 `[1]` |
| `a.pop()` · `a.shift()` | 뺀 원소 · 비었으면 `undefined` | 끝 · 앞에서 뺀다 | 동작 (2)의 `[1]` |
| `a.splice(start, deleteCount, ...items)` | **지운 것들의 새 배열** | 지우고 끼운다 | 동작 (2)의 `[2]` |
| `a.sort(comparator?)` | **`a` 자신** | 제자리 정렬 · 안정(ES2019) | 동작 (3)\~(6) |
| `a.reverse()` | **`a` 자신** | 제자리 뒤집기 | 동작 (7)의 `[1]` |
| `a.fill(value, start?, end?)` | **`a` 자신** | 같은 `value` 로 덮는다(복사 없음) | 동작 (7)의 `[3]` |
| `a.copyWithin(target, start, end?)` | **`a` 자신** | 안에서 조각을 덮어쓴다 · 길이 그대로 | 동작 (7)의 `[4]` |
| `a.length = n` | (대입식의 값 `n`) | 줄이면 **자르고**, 늘리면 **구멍** | 동작 (7)의 `[5]` |

- **비교 함수** — `(x, y) => 수`. 음수면 x 가 앞. **불리언을 돌려주지 마라**(`a - b` 또는 `a < b ? -1 : a > b ? 1 : 0`).
- **음수 인덱스** — `splice`·`fill`·`copyWithin` 의 위치 인자는 음수면 `length + 인자`.
- **전부 generic** — 명세 Note 가 "intentionally generic" 이라 적는다. `this` 가 배열이 아니어도 `length` 와 자리 프로퍼티로 동작한다.

## 어디서 틀리나

### (1) ★★★ 숫자 배열을 `sort()` 한다

`[10, 9, 1].sort()` 는 `[1,10,9]` 다(동작 (3)). 비교 함수 없이는 **글자 순서**다. 숫자는 언제나 `(a, b) => a - b`.

### (2) ★★★ 비교 함수가 불리언을 돌려준다

`(a, b) => a > b` 는 이 판에서 **한 자리도 안 움직였다**(동작 (3)의 `[4]`). 명세상으로는 **결과가 구현 정의**다(동작 (5)). 에러가 안 나서 테스트 데이터가 우연히 정렬돼 있으면 못 잡는다.

### (3) ★★★ `sort`·`reverse` 의 반환값을 사본으로 쓴다

`const r = a.reverse()` 의 `r` 은 `a` 다(동작 (7)의 `[1]`). 원본을 지키려면 `slice()`·`[...a]` 를 먼저, 또는 [25번](../25-array-non-mutating-and-copy-methods/2-summary.md)의 복사판.

### (4) ★★★ `Array(n).fill([])` 로 2차원 배열을 만든다

**배열 하나를 n 자리가 공유**한다(동작 (7)의 `[3]`). 한 줄에 `push` 하면 전부에 보인다. `Array.from({ length: n }, () => [])`.

### (5) ★★ `push` 의 반환값을 배열로 쓴다

`push` 는 **새 길이**를 돌려준다(동작 (2)). `a = a.push(x)` 는 `a` 를 숫자로 바꿔 버린다. `concat` 은 새 배열을 돌려주지만 원본을 안 바꾼다(동작 (1)의 대조 행).

### (6) ★★ `splice` 가 `[]` 를 돌려줬으니 아무 일도 없었다고 읽는다

`splice(1, 0, 9)` 는 `[]` 를 돌려주고 **원본에 9 를 끼웠다**(동작 (1)). 반환값은 **지운 것**이지 결과가 아니다.

### (7) ★★ 비교 함수로 `undefined` 를 앞에 두려 한다

`undefined` 는 **비교 함수에 안 간다**(동작 (6)의 `[2]`·`[3]`). 먼저 다른 값으로 바꾼다.

### (8) ★★ 난수 비교 함수로 섞는다

명세가 결과를 약속하지 않는다(동작 (5)). 모든 순열이 나오기는 했지만(`24 / 24`) **고르게** 나오는지는 이 문서가 **안 쟀다.** 피셔-예이츠를 쓴다.

### (9) ★★ 이미 정렬된 동결 배열에 `sort()` 는 괜찮을 것이라 믿는다

**던진다**(동작 (8)). `sort` 는 값이 같아도 **다시 쓴다.** 빈 동결 배열에서는 `sort` 는 통과하고 `pop` 이 던진다.

### (10) ★★ 「비엄격 모드면 동결 배열에 써도 조용하다」를 메서드에도 적용한다

**대입식만 조용하다.** `push`·`sort` 는 비엄격 모드에서도 `TypeError` 다(동작 (8)의 둘째 블록). 반대로 `a.length = 0` 은 비엄격이면 **아무 말 없이** 안 비워진다.

### (11) ★ `length` 를 줄여 놓고 다른 이름은 멀쩡할 것이라 믿는다

같은 배열을 보는 **모든 이름**에서 잘린다(동작 (7)의 `[5]`). 배열은 참조로 오간다([01번](../01-value-types-and-typeof/2-summary.md)).

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- 격자의 세 칸 전부 — 어느 메서드가 원본에 쓰고, 무엇을 돌려주나(**"Return O"** · 새 `length` · 지운 것들의 배열).
- 비교 함수가 없으면 **`ToString` 뒤 문자열 비교** · `undefined` 는 끝, 구멍은 그 뒤 · **비교 함수는 `undefined` 를 받지 않는다**(`CompareArrayElements` ①\~③).
- 비교 함수의 반환값이 `ToNumber` 되고 **`NaN` 이면 0** 인 것 · 함수도 `undefined` 도 아니면 **첫 단계에서 `TypeError`**.
- ★★★ **안정 정렬 — ES2019(10판) 부터.** 9판은 "not necessarily stable" 이었다.
- `sort` 가 정렬한 목록을 **자리 0 부터 전부 `Set`** 하고 남은 자리를 `Delete` 하는 것 — 그래서 동결 배열에서 **이미 정렬돼 있어도** 던진다.
- 변형 메서드가 쓰기를 **`Set(…, true)`** 로 해서 **모드와 상관없이** 실패에 던지는 것 · 대입식은 비엄격이면 조용한 것.
- `fill` 이 같은 값을 복사 없이 넣는 것 · `copyWithin` 이 겹칠 때 뒤에서부터 복사하는 것 · `length` 대입이 자르고, 잘못된 길이에 `RangeError` 인 것.
- 예외의 **종류**(`TypeError` · `RangeError`).

### 엔진(V8) 구현 · 이 판의 관찰

- ★★★ **규칙을 어긴 비교 함수의 결과 전부** — 불리언 비교 함수가 **한 자리도 안 움직인 것** · `() => -1` 이 역순인 것 · 호출 수 4 — 명세는 **「implementation-defined」** 다.
- **비교 함수의 호출 순서와 횟수**(동작 (5)·(6)의 로그) — 명세는 "an implementation-defined sequence of calls to SortCompare" 라고만 적는다.
- 난수 비교 함수에서 **모든 순열이 나온 것**(`6 / 6` · `24 / 24`) — 이 판 · 2만 판의 관찰이다.
- 예외 **문구 전부** — `The comparison function must be either a function or undefined` · `Cannot add property 3, object is not extensible` · `Cannot delete property '2' of [object Array]` ·
  `Cannot assign to read only property '0' of object '[object Array]'` · `Invalid array length`.
- 정렬 알고리즘의 **이름** — 명세에 없다. 이 문서는 알고리즘 이름을 한 번도 근거로 쓰지 않았다.

### 호스트·다른 명세가 정하는 것 — ECMA-262 밖

- `localeCompare` 의 순서 — ECMA-402 와 엔진이 싣는 ICU 데이터(동작 (3)의 한 줄).

### 그래서 이렇게 적으면 틀린다

- ✗ 「`(a, b) => a > b` 는 짧은 배열에서는 정렬된다」 → ○ 「**결과가 구현 정의다.** 이 판(node 20)에서는 **한 자리도 안 움직였다**」
- ✗ 「JS 정렬은 안정적이다」 → ○ 「**ES2019 부터** 명세가 안정을 요구한다. 그 전 판은 요구하지 않았다」
- ✗ 「`sort` 는 원본을 바꾸고 새 배열을 돌려준다」 → ○ 「원본을 바꾸고 **원본을** 돌려준다」
- ✗ 「`push` 가 `concat` 보다 빠르다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **변형 메서드** — 배열을 **혼자 소유**하고 있을 때(함수 안에서 만든 지역 배열) · 스택(`push`/`pop`)·큐(`push`/`shift`)처럼 **원본이 곧 상태**일 때.
- **`sort`** — 항상 비교 함수와 함께. 문자열 배열을 **코드 유닛 순서**로 정렬할 때만 비교 함수 없이.
- **`fill`** — 원시값으로 채울 때. 객체로 채울 때는 `Array.from` 과 콜백.
- **`length = 0`** — 같은 배열을 여러 곳이 보고 있고 **모두에게서 비우고 싶을 때만.** 한 이름만 비우려면 `a = []`.
- ★ **안 쓰는 자리** — 인자로 **받은** 배열(호출한 쪽의 배열이 바뀐다) · React 상태처럼 **참조가 바뀌어야 변화를 아는** 곳 · 동결된 설정값. 그 자리는 [25번](../25-array-non-mutating-and-copy-methods/2-summary.md)의 복사판이다.

## 핵심 문장

1. ★★★ 15 메서드 × 세 칸 격자에서 y 는 `20 / 45` 칸, 원본 내용을 바꾸는 것은 `10 / 15` 이고, **원본을 돌려주는 것과 길이를 바꾸는 것은 한 칸도 겹치지 않았다**(`0 / 15`).
2. ★★★ `sort`·`reverse`·`fill`·`copyWithin` 은 **원본 그 자체**를 돌려준다 — 체이닝이 원본을 바꾸고, 반환값을 받은 이름과 원본이 **한 배열**이다.
3. ★★★ 비교 함수가 없으면 **글자로** 비교한다(`[1,10,9]`). `undefined` 는 비교 함수보다 **먼저** 끝으로 가고, 구멍은 그 뒤다.
4. ★★★ 안정 정렬은 **ES2019 부터** 명세의 약속이다. 비교 함수가 규칙을 어기면 순서는 **구현 정의**다 — 이 판에서 흔들리지 않았어도 약속이 아니다.
5. ★★ 동결 배열은 **「썼나」에서** 던진다 — 이미 정렬된 배열의 `sort` 도, 빈 배열의 `pop` 도 던지고, **비엄격 모드에서도** 던진다(조용한 것은 대입식뿐이다).

## 관련 자료

- [ECMA-262 — Indexed Collections](https://tc39.es/ecma262/multipage/indexed-collections.html) — `Array.prototype.sort`·`SortIndexedProperties`·`CompareArrayElements`·변형 메서드들
- [ECMA-262 9판(ES2018)](https://262.ecma-international.org/9.0/) · [10판(ES2019)](https://262.ecma-international.org/10.0/) — 안정성의 판 경계
- [`cs/foundations/data-structures-basics/`](../../../../data-structures-basics/README.md) — ★ **경계**: 그쪽은 **스택·큐가 무엇이고 어디에 쓰나**까지, 여기는 **JS 의 네 메서드가 무엇을 돌려주고 원본을 어떻게 바꾸나**부터.
- [25 — 배열 비변형·복사 메서드](../25-array-non-mutating-and-copy-methods/2-summary.md) — ★ **경계**: 그쪽은 **새 배열을 돌려주는 쪽과 `set` 트랩 횟수**, 여기는 **원본을 바꾸는 쪽**.
- [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md) — ★ **경계**: 그쪽은 **구멍을 메서드마다 어떻게 보나**(격자), 여기는 **`sort` 가 구멍을 끝으로 보내는 것**만.
- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) — ★ **경계**: 그쪽은 **`freeze` 가 무엇을 막나**, 여기는 **변형 메서드가 어느 단계에서 막히나**만.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **10번**(리스트 메서드와 정렬 키) · **31번**(비교 프로토콜과 정렬 가능성) — 동작 (9)의 대비.

## 용어 풀이

- **변형 메서드** — 호출한 배열 자체에 쓰거나 지우는 메서드.
- **비교 함수** — `sort` 에 넘기는 `(x, y) => 수`. 음수면 x 가 앞.
- **consistent comparator** — 명세가 비교 함수에 요구하는 성질. 같은 쌍에 같은 수를 돌려주고, `NaN` 이 아닌 Number 이고, 반사·대칭·추이를 지킨다.
- **implementation-defined(구현 정의)** — 명세가 결과를 정하지 않고 **엔진이 정하게** 둔 것. 엔진마다·판마다 다를 수 있다.
- **안정 정렬(stable sort)** — 비교해서 같은 원소들의 원래 순서를 바꾸지 않는 정렬.
- **`CompareArrayElements`** — 두 원소를 비교하는 명세 연산. `undefined` 를 먼저 처리하고, 비교 함수가 없으면 문자열로 비교한다.
- **`SortIndexedProperties`** — 배열의 자리들을 읽어 목록을 만들고 정렬하는 명세 연산. `sort` 는 구멍을 건너뛰게(`skip-holes`) 부른다.
- **구멍(hole)** — `length` 안의 자리인데 프로퍼티가 없는 것. `i in arr` 이 `false`.
- **generic** — `this` 가 배열이 아니어도 `length` 와 자리 프로퍼티만 있으면 동작하는 메서드.
- **피셔-예이츠(Fisher-Yates)** — 뒤에서부터 한 자리씩 앞쪽의 임의 자리와 바꿔 섞는 방법. 이 문서는 실행하지 않았다.

## 더 들어가면

- **`TypedArray.prototype.sort`** — 기본 비교가 **숫자**다(글자가 아니다). 이 문서 밖이다 — **안 돌렸다.**
- **`sort` 의 `this` 가 배열이 아닐 때**(`Array.prototype.sort.call(arrayLike)`) — generic 이라 동작한다. 이 배치는 돌리지 않았다.
- **ES2019 이전 엔진의 불안정 정렬** — 이 머신에 그 판이 없어 **못 쟀다.** 명세 문장으로만 경계를 적었다.
