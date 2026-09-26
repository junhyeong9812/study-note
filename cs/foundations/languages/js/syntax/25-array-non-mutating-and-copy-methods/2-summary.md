# js/syntax/25 — 배열 비변형·복사 메서드: 「원본에는 쓰기가 한 번도 안 닿는다 — 단 얕게, 그리고 콜백은 예외다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기 — `Proxy` 쓰기 트랩이다.**
> 「이 메서드는 원본을 안 바꾼다」는 결과 배열을 봐서는 반만 증명된다 — **도중에 썼다가 되돌렸을 수도** 있기 때문이다.
> 그래서 원본을 `Proxy` 로 감싸 **`set` · `defineProperty` · `deleteProperty` 트랩이 몇 번 불리나**를 메서드마다 세고,
> 마지막 줄의 「쓰기 트랩 0 으로 돌아온 메서드 N / M」을 **스크립트가 직접 센다**(동작 (1)).
> ★ **이 창 하나가 24편(변형)과 25편(복사)을 한 줄로 가른다** — 변형 메서드는 같은 격자에서 트랩이 불린다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 2025(16판)](https://262.ecma-international.org/16.0/) — `Array.prototype.sort` · `toSorted` · `toReversed` · `toSpliced` · `with` · `reduce` · `map` 의 단계와 note ·
>   `SortIndexedProperties`(`skip-holes` 대 `read-through-holes`) · `ToIntegerOrInfinity`
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(★ **Change Array by Copy 는 2023**)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **메서드와 추상 연산 이름**으로, 값·트랩 횟수·예외 타입과 메시지는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★ **이 문서는 BMP 밖 글자를 한 글자도 싣지 않는다.**
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `map` · `filter` · `reduce` · `reduceRight` · `slice` · `concat` | **ES2015 이전부터** | 세 판 다 있다 |
> | `Symbol.species` · `Symbol.isConcatSpreadable` | **ES2015** | 세 판 다 있다 — [22번](../22-symbol-and-well-known-symbols/2-summary.md)이 정본 |
> | ★★★ `toSorted` · `toReversed` · `toSpliced` · `with`(Change Array by Copy) | ★★★ **ES2023** — [README](../README.md) 는 「ES2024」라 적었다. **finished proposals 표가 2023 이다**(목록 쪽이 틀렸다 — 이 편은 고치지 않고 보고만 한다) | ★ **node 18 에 없고** node 20 · Chrome 에 있다 |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | 원본을 `Proxy` 로 감싸 메서드 **17개**의 `set` · `defineProperty` · `deleteProperty` · `get` 트랩 횟수(동작 (1)) · `map` 이 콜백에 넘기는 인자(동작 (5)) · `reduce` 콜백이 받는 `(acc, x, i)`(동작 (4)) · 비교 함수 호출 횟수(동작 (6)) |
> | ★★★ **② 전수 격자** | 동작 (1)의 격자 자체 — **「쓰기 트랩 0 으로 돌아온 메서드 N / M」과 「던진 메서드 N / M」을 스크립트가 센다** · 인덱스 8개 × (`with` · 대입)(동작 (3)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `with` 의 `RangeError` · 빈 배열 `reduce` 의 `TypeError` · 비교 함수 자리의 `TypeError` · ★ **node 18 에서 메서드가 없는 `TypeError`** |
> | ★★ **⑤ 두 판 대조기** | 이 주제에서 갈린 탐침은 **넷**(`25a` · `25b` · `25c` · `25f`) — 전부 **복사 메서드 넷이 node 18 에 없어서**다 |
> | ★ **부적용 — ③ 브랜드 태그** | 결과가 「배열인가」는 `Array.isArray` 로 충분했다. 「어느 클래스인가」(species)는 **22번이 이미 쟀다** — 인용만 한다(동작 (8)) |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 가 한 줄도 없다. 전부 런타임 의미다 — **잴 것이 없다** |
> | ★★★ **안 쟀다 — 성능** | 「`toSorted` 는 복사라서 느리다」·「`slice().sort()` 가 더 빠르다」를 **한 줄도 쓰지 않는다.** 시간도 메모리도 안 쟀다. 센 것은 **트랩 횟수와 호출 횟수**뿐이다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 · 근거로 쓰지 않는다 | 안 흔들린다 · 근거로 쓴다 |
> |---|---|
> | 예외 **문구** — ★ **판마다 다르다**(node 18 의 `[3,(intermediate value),1].toSorted is not a function` 처럼 **소스 모양이 문구에 박힌다**) | ★★★ **쓰기 트랩 횟수**(`set`·`defineProperty`·`deleteProperty`)와 두 집계 줄 · 원본이 바뀌었나 · 돌려준 값이 원본과 `===` 인가 · 예외의 **종류** |
> | ★ **`get` 트랩 횟수** — 명세 단계를 따르지만 이 문서의 주장은 여기에 기대지 않는다 | `with` 가 던지는 **인덱스 범위** · `reduce` 가 던지는 **조건**(원소가 하나도 없고 초기값이 없을 때) |
> | ★ **비교 함수 호출 횟수**(`4` · `108`) — 재대조에서 같았지만 **호출 순서가 구현 정의**라 엔진이 바뀌면 움직일 수 있다 | ★★★ **비교 함수가 던지면 `sort` 의 원본이 그대로인 것** — 명세 단계가 그렇게 짜여 있다(동작 (6)) |
>
> **선행** — [24 — 배열 변형 메서드](../24-array-mutating-methods/2-summary.md)(★★★ **직접 짝** — 변형 쪽의 반환값과 원본, 기본 `sort` 의 문자열 비교·안정 정렬은 거기가 정본) ·
> [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md)(★★ `Symbol.species` 를 **읽는 메서드 7 / 14** · `isConcatSpreadable`) ·
> [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md)(`extends Array` 의 `map`·`filter`·`slice` 결과가 자식 클래스) ·
> [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md)(배열 메서드 사슬이 **단계마다 전부 도는 것**) ·
> [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md)(`map(parseInt)` 의 이유 — 남는 인자와 `length`) ·
> [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md)(얕은 복사).
> **이어지는 곳** — [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md)(★ **구멍을 메서드마다 어떻게 보나**는 거기가 정본) · [목록의 **48번 주제**](../48-deep-copy-methods-compared/) 「깊은 복사 수단 비교」.
>
> ★★ **경계 — 변형 메서드의 동작 자체는 24번이 정본이다.** 여기서는 **같은 일을 복사로 하면 무엇이 달라지나**만 본다. 격자에 변형 메서드가 들어간 것은 **대조군**이다.
> ★★ **경계 — species 가 무엇을 바꾸나는 22번(읽는 메서드)·17번(결과 생성자)이 정본이다.** 여기서는 그 표를 인용해 **복사 메서드 넷이 species 를 안 읽는다**는 것만 잇는다.
> ★ **경계 — 구멍 처리의 전수 격자는 26번이다.** 여기서는 **복사 메서드가 구멍을 `undefined` 로 채운다**는 한 줄만 본다(동작 (7)).
> ★ **경계 — 깊은 복사(`structuredClone` 등)는 48번 주제다.** 여기서는 **복사가 한 겹이라는 사실**까지만.

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

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 이 주제에서 갈린 것은 `25a` · `25b` · `25c` · `25f` 넷이고, 갈린 판의 전문은 [3-answer.md](3-answer.md) 의 9번에 있다.

`identical 26  ·  differs 4  ·  total 30`

## 한눈에 — 쉽게 말하면

**비변형 메서드는 「원본을 복사기에 올려 복사본에 작업하는 것」** 이다. 원본 종이에는 **펜이 한 번도 안 닿는다.**
변형 메서드(24편)는 **원본 종이에 직접 고쳐 쓴다.**

- ★★★ **펜이 닿았나는 결과를 봐서는 모른다** — 고쳐 쓰고 지웠을 수도 있다. 그래서 **종이에 감지기(`Proxy`)를 붙여** 펜이 닿은 횟수를 센다.
- ★★ **복사기는 한 겹만 복사한다.** 종이에 붙어 있던 **사진(객체)은 복사본과 원본이 같은 사진**을 나눠 쓴다.
- ★★ **작업자(콜백)는 원본을 만질 수 있다.** 복사기가 안 썼다는 것이지 **작업자가 안 썼다는 게 아니다.**
- ★ **새 복사기(ES2023 `toSorted` 류)는 빈칸(구멍)을 「빈칸」이 아니라 「`undefined` 라고 적힌 칸」으로 복사한다.**

```text
   변형 (24편)                               비변형 · 복사 (이 편)
   -----------                               ---------------------
   arr.sort()                                arr.toSorted()
     arr 의 칸을 읽는다                         arr 의 칸을 읽는다
     정렬한다                                   정렬한다
     arr 의 칸에 다시 쓴다   <- 쓰기 트랩       새 배열 A 에 쓴다        <- arr 에는 쓰기 트랩 0
     arr 를 돌려준다                            A 를 돌려준다

   돌려준 값 === arr   -> true                  돌려준 값 === arr   -> false
   arr 가 바뀌었나     -> 그렇다                arr 가 바뀌었나     -> 아니다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 원본 종이 | 메서드를 부른 배열(`this`) | 격자의 「target after」 열 |
| 펜이 닿는 것 | 원본에 대한 `[[Set]]` · `[[DefineOwnProperty]]` · `[[Delete]]` | `Proxy` 의 `set` · `defineProperty` · `deleteProperty` 트랩 |
| 복사본 | 메서드가 새로 만든 배열(`ArrayCreate` · `ArraySpeciesCreate`) | 돌려준 값 `=== arr` 가 `false` |
| 한 겹만 복사 | 원소 **값**을 옮긴다 — 객체 원소는 **참조**가 옮겨진다 | `sorted[1] === rows[0]` |
| 작업자가 원본을 만지는 것 | 콜백의 세 번째 인자(원본 배열)에 쓰기 | 격자 마지막 행 |
| 빈칸을 `undefined` 로 복사 | `SortIndexedProperties(…, read-through-holes)` · 복사 메서드의 `Get` | 동작 (7) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**React 상태 배열을 `sort()` 했더니 화면이 안 바뀌었다**」(원본이 바뀌고 같은 참조가 돌아와 「변화 없음」으로 판정된다)와
「**`toSorted()` 로 복사해 정렬했는데 원본의 객체 필드가 바뀌었다**」(한 겹 복사)가 그것이다.
앞엣것은 **원본 종이에 고쳐 쓴** 것이고, 뒤엣것은 **복사본과 원본이 같은 사진을 나눠 쓴** 것이다.

> **비변형(non-mutating) 메서드** — 메서드 **자신은** 호출한 배열에 쓰지 않는 메서드. 결과는 새 배열이나 값으로 돌려준다.\
> 예: `map` · `filter` · `slice` · `toSorted`.

> **`Proxy` 트랩** — 객체에 대한 기본 연산(읽기·쓰기·삭제)을 가로채는 함수. 이 문서는 **세기만 하고** 원래 동작(`Reflect.*`)으로 넘긴다.\
> 예: `set(t, k, v, r) { n++; return Reflect.set(t, k, v, r); }`.

## 이 주제가 답하려는 질문

1. **「원본을 안 바꾼다」를 무엇으로 증명하나** — 결과가 아니라 **쓰기가 원본에 닿았나**를 어떻게 세나?
2. **복사 메서드 넷(`toSorted`·`toReversed`·`toSpliced`·`with`)은 짝이 되는 변형 메서드와 무엇이 같고 무엇이 다른가** — 반환값 · 원본 · 범위 밖 인덱스 · 구멍 · 예외?
3. **비변형이라도 틀리는 자리는 어디인가** — 얕은 복사 · 콜백의 쓰기 · `reduce` 의 초기값 · `map(parseInt)`?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 쓰기 트랩 격자 — 이 주제의 본체

**언제 쓰나** — 「이 메서드는 원본을 건드리나」를 **결과가 아니라 과정으로** 확인하고 싶을 때 · 라이브러리 함수가 입력 배열에 손대는지 의심될 때.

```js
// js24b-25a-trap-grid.js
// 배열을 Proxy 로 감싸고 메서드마다 쓰기 트랩(set · defineProperty · deleteProperty)이 몇 번 불리는지 센다.
// 메서드는 this 가 Proxy 인 채로 부른다 -- 원본에 무엇을 하는지가 트랩에 전부 찍힌다.
const probe = (label, run) => {
  const n = { get: 0, set: 0, defineProperty: 0, deleteProperty: 0 };
  const target = [3, 1, 2];
  const p = new Proxy(target, {
    get(t, k, r) { n.get++; return Reflect.get(t, k, r); },
    set(t, k, v, r) { n.set++; return Reflect.set(t, k, v, r); },
    defineProperty(t, k, d) { n.defineProperty++; return Reflect.defineProperty(t, k, d); },
    deleteProperty(t, k) { n.deleteProperty++; return Reflect.deleteProperty(t, k); },
  });
  let result, threw = false;
  try { result = run(p); } catch (e) { threw = true; result = e.constructor.name + " 「" + e.message + "」"; }
  const writes = n.set + n.defineProperty + n.deleteProperty;
  const shown = typeof result === "string" ? result : (result === p ? "<the proxy itself>" : JSON.stringify(result));
  console.log(
    "  " + label.padEnd(28) + String(n.set).padStart(4) + String(n.defineProperty).padStart(8) +
    String(n.deleteProperty).padStart(8) + String(n.get).padStart(6) + "   " + JSON.stringify(target).padEnd(12) + shown
  );
  return threw ? "threw" : writes;
};

console.log("  method                       set  define  delete   get   target after returned");
const rows = [
  ["map(x => x * 10)", (p) => p.map((x) => x * 10)],
  ["filter(x => x > 1)", (p) => p.filter((x) => x > 1)],
  ["reduce((a, x) => a + x)", (p) => p.reduce((a, x) => a + x)],
  ["slice(1)", (p) => p.slice(1)],
  ["concat([9])", (p) => p.concat([9])],
  ["toSorted()", (p) => p.toSorted()],
  ["toReversed()", (p) => p.toReversed()],
  ["toSpliced(0, 1)", (p) => p.toSpliced(0, 1)],
  ["with(0, 9)", (p) => p.with(0, 9)],
  ["sort()", (p) => p.sort()],
  ["reverse()", (p) => p.reverse()],
  ["splice(0, 1)", (p) => p.splice(0, 1)],
  ["push(9)", (p) => p.push(9)],
  ["fill(0)", (p) => p.fill(0)],
  ["shift()", (p) => p.shift()],
  ["copyWithin(0, 1)", (p) => p.copyWithin(0, 1)],
  ["map((x, i, a) => a[i] = 0)", (p) => p.map((x, i, a) => (a[i] = 0))],
];
let zero = 0, threw = 0;
for (const [label, run] of rows) {
  const w = probe(label, run);
  if (w === "threw") threw++; else if (w === 0) zero++;
}
console.log("");
console.log("methods that threw: " + threw + " / " + rows.length);
console.log("methods that returned with zero write traps: " + zero + " / " + rows.length);
```
```text
===== node20 js24b-25a-trap-grid.js (exit=0) =====
  method                       set  define  delete   get   target after returned
  map(x => x * 10)               0       0       0     6   [3,1,2]     [30,10,20]
  filter(x => x > 1)             0       0       0     6   [3,1,2]     [3,2]
  reduce((a, x) => a + x)        0       0       0     5   [3,1,2]     6
  slice(1)                       0       0       0     5   [3,1,2]     [1,2]
  concat([9])                    0       0       0     7   [3,1,2]     [3,1,2,9]
  toSorted()                     0       0       0     5   [3,1,2]     [1,2,3]
  toReversed()                   0       0       0     5   [3,1,2]     [2,1,3]
  toSpliced(0, 1)                0       0       0     4   [3,1,2]     [1,2]
  with(0, 9)                     0       0       0     4   [3,1,2]     [9,1,2]
  sort()                         3       3       0     5   [1,2,3]     <the proxy itself>
  reverse()                      2       2       0     4   [2,1,3]     <the proxy itself>
  splice(0, 1)                   3       3       1     6   [1,2]       [3]
  push(9)                        2       2       0     2   [3,1,2,9]   4
  fill(0)                        3       3       0     2   [0,0,0]     <the proxy itself>
  shift()                        3       3       1     5   [1,2]       3
  copyWithin(0, 1)               2       2       0     4   [1,2,2]     <the proxy itself>
  map((x, i, a) => a[i] = 0)     3       3       0     6   [0,0,0]     [0,0,0]

methods that threw: 0 / 17
methods that returned with zero write traps: 9 / 17
```

```text
   p.toSorted()                                p.sort()
   ------------                                --------
   Proxy p ──get──▶ length, "0", "1", "2"       Proxy p ──get──▶ length, "0", "1", "2"
                  (읽기만 한다)                                  (읽는다)
   새 배열 A ◀── CreateDataProperty            정렬된 목록을 p 에 되쓴다
      (A 는 Proxy 가 아니다 -- 트랩 없음)          p["0"] = 1   ──set──▶ ──defineProperty──▶
                                                p["1"] = 2   ──set──▶ ──defineProperty──▶
                                                p["2"] = 3   ──set──▶ ──defineProperty──▶
   쓰기 트랩  0                                 쓰기 트랩  set 3 · define 3
```

- ★★★ **집계 줄 — `methods that threw: 0 / 17` · `methods that returned with zero write traps: 9 / 17`.**
  0 인 아홉이 전부 **비변형 쪽**(`map` · `filter` · `reduce` · `slice` · `concat` · `toSorted` · `toReversed` · `toSpliced` · `with`)이고, **변형 쪽 일곱은 전부 0 이 아니다** — 남은 한 행은 콜백이 쓰는 `map` 이다(아래).
  ★ **이 한 격자가 24편과 25편을 가른다** — 결과 배열이 아니라 **원본에 쓰기가 닿았나**로.
- ★★★ **마지막 행 `map((x, i, a) => a[i] = 0)` 이 `set 3` 이다.** `map` 자신은 안 쓰지만 **콜백이 세 번째 인자로 받은 원본에 쓴다.**
  명세 `map` 의 note 가 그대로 적는다 — "map does not directly mutate the object on which it is called but the object may be mutated by the calls to callback."
  ★ **「비변형」은 메서드의 성질이지 그 호출 전체의 성질이 아니다.**
- ★★ **변형 쪽의 쓰기 횟수가 곧 「몇 칸을 건드렸나」다** — `sort` 3(전부 되쓴다) · `reverse` 2(가운데는 제자리) · `push` 2(새 칸 + `length`) · `splice(0, 1)`·`shift` 는 **`set` 3 에 `delete` 1**(당기고 끝 칸을 지운다).
  각 메서드가 **무엇을 돌려주나**는 [24번](../24-array-mutating-methods/2-summary.md)이 정본이다.
- ★ **`set` 과 `defineProperty` 가 늘 같은 수**다 — 동작 (2).
- ★ **`get` 열은 근거로 쓰지 않는다**(머리말 표) — 비변형 쪽도 **읽기는 한다**는 것만 본다.

★★★ **같은 격자를 node 18 에 던지면 집계 줄이 달라진다** — `methods that threw: 4 / 17` · `methods that returned with zero write traps: 5 / 17`.
복사 메서드 넷이 **없어서 `TypeError` 로 던지고**, 던진 행은 쓰기 트랩이 **0 인 채로** 끝난다.
★★ **「던진 행」을 따로 안 세면** 없는 메서드가 「원본을 안 바꾼 메서드」로 세어진다 — 그래서 격자에 `threw` 칸을 둔다(그 전 판의 출력은 캡처로 남기지 않았으므로 싣지 않는다).
**0 이 결론인 격자일수록 그 0 이 「안 썼다」인지 「돌지도 않았다」인지를 따로 세어야 한다**(규칙 22 와 같은 집안). 전문은 [3-answer.md](3-answer.md) 9번.

### (2) ★★ 쓰기 하나에 트랩이 둘 — `set` 뒤에 `defineProperty`

**언제 쓰나** — `Proxy` 로 쓰기를 세다가 **숫자가 두 배로 나올 때**.

```text
   sort 가 p["0"] = 1 을 한다  =  Set(p, "0", 1, true)
        │
        ▼
   p.[[Set]]("0", 1, receiver = p)       ──▶ set 트랩            (1번째)
        │  트랩이 Reflect.set(t, "0", 1, p) 로 넘긴다
        ▼
   OrdinarySet(t, "0", 1, receiver = p)
        │  receiver 가 p 이므로 「p 에 자기 프로퍼티를 정의」한다
        ▼
   p.[[DefineOwnProperty]]("0", {value: 1})  ──▶ defineProperty 트랩   (2번째)
```

- ★★ **`Reflect.set` 에 받은 `receiver`(= Proxy)를 그대로 넘겼기 때문**이다. 평범한 쓰기는 「**수신자에** 데이터 프로퍼티를 정의」로 끝나고, 수신자가 Proxy 라 그 정의가 다시 트랩에 걸린다.
- ★ 그래서 격자에서 **`set` 과 `defineProperty` 가 전 행에서 같은 수**다. **셀 때는 한 열만 보면 된다** — 이 문서는 둘을 다 싣고 합으로 판정했다.
- ★ 트랩의 계약 자체는 [목록의 **45번 주제**](../45-proxy/)(`Proxy`)가 정본이다.

### (3) ★★★ 범위 밖 인덱스 — `with` 는 던지고 대입은 조용히 늘린다

**언제 쓰나** — `arr[i] = v` 를 불변 스타일로 `arr.with(i, v)` 로 바꿀 때 · 음수 인덱스를 쓸 때.

```js
// js24b-25c-index-range.js
// 범위 밖 인덱스 -- with(i, v) 와 대입 a[i] = v 에 같은 인덱스를 준다. 원본 길이는 3.
const cell = (a, i) => (i in a ? JSON.stringify(a[i]) : "<hole>");
const show = (a) => "[" + Array.from({ length: a.length }, (_, i) => cell(a, i)).join(",") + "]";
const idx = [2, 3, 5, -1, -3, -4, 1.5, "1"];

console.log("[1] a.with(i, 9)");
for (const i of idx) {
  const a = [0, 1, 2];
  let r;
  try { const c = a.with(i, 9); r = show(c) + "  length " + c.length; } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  i = " + JSON.stringify(i).padEnd(6) + r + "   a " + show(a));
}

console.log("");
console.log("[2] a[i] = 9");
for (const i of idx) {
  const a = [0, 1, 2];
  let r;
  try { a[i] = 9; r = show(a) + "  length " + a.length + "  own keys " + JSON.stringify(Object.keys(a)); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  i = " + JSON.stringify(i).padEnd(6) + r);
}

console.log("");
console.log("[3] at(i) and with(i) read the same index");
const a = [0, 1, 2];
for (const i of [-1, -3, -4, 3]) {
  let w;
  try { w = show(a.with(i, 9)); } catch (e) { w = e.constructor.name; }
  console.log("  i = " + String(i).padEnd(4) + "at " + String(a.at(i)).padEnd(10) + "with " + w);
}
```
```text
===== node20 js24b-25c-index-range.js (exit=0) =====
[1] a.with(i, 9)
  i = 2     [0,1,9]  length 3   a [0,1,2]
  i = 3     RangeError 「Invalid index : 3」   a [0,1,2]
  i = 5     RangeError 「Invalid index : 5」   a [0,1,2]
  i = -1    [0,1,9]  length 3   a [0,1,2]
  i = -3    [9,1,2]  length 3   a [0,1,2]
  i = -4    RangeError 「Invalid index : -4」   a [0,1,2]
  i = 1.5   [0,9,2]  length 3   a [0,1,2]
  i = "1"   [0,9,2]  length 3   a [0,1,2]

[2] a[i] = 9
  i = 2     [0,1,9]  length 3  own keys ["0","1","2"]
  i = 3     [0,1,2,9]  length 4  own keys ["0","1","2","3"]
  i = 5     [0,1,2,<hole>,<hole>,9]  length 6  own keys ["0","1","2","5"]
  i = -1    [0,1,2]  length 3  own keys ["0","1","2","-1"]
  i = -3    [0,1,2]  length 3  own keys ["0","1","2","-3"]
  i = -4    [0,1,2]  length 3  own keys ["0","1","2","-4"]
  i = 1.5   [0,1,2]  length 3  own keys ["0","1","2","1.5"]
  i = "1"   [0,9,2]  length 3  own keys ["0","1","2"]

[3] at(i) and with(i) read the same index
  i = -1  at 2         with [0,1,9]
  i = -3  at 0         with [9,1,2]
  i = -4  at undefined with RangeError
  i = 3   at undefined with RangeError
```

```text
   a = [0, 1, 2]  (length 3)

   a.with(i, v)                                  a[i] = v
   ------------                                  --------
   ① i 를 ToIntegerOrInfinity (1.5 -> 1)          i 를 프로퍼티 키로 (1.5 -> "1.5")
   ② i < 0 이면 len + i  (-1 -> 2)                 음수도 그냥 글자 키 ("-1")
   ③ 0 <= 실제 인덱스 < len 이 아니면 RangeError    배열 인덱스면 칸에, 넘으면 length 를 늘린다
   ④ 새 배열에 복사하며 그 칸만 v                   아니면 평범한 프로퍼티가 하나 생긴다

   i =  3  ->  RangeError                         [0,1,2,9]           length 4
   i =  5  ->  RangeError                         [0,1,2,<hole>,<hole>,9]  length 6
   i = -1  ->  [0,1,9]                            [0,1,2]  + 키 "-1"  length 3
   i = -4  ->  RangeError                         [0,1,2]  + 키 "-4"
```

- ★★★ **`with(3, 9)` 은 `RangeError 「Invalid index : 3」`, `a[3] = 9` 는 `length 4` 로 조용히 늘어난다.** `a[5] = 9` 는 **구멍 둘**을 만들며 `length 6`.
  `with` 는 **길이를 절대 안 바꾼다** — 명세 `with` 는 `actualIndex ≥ len` 이거나 `< 0` 이면 `RangeError` 를 던지고, 결과는 늘 `ArrayCreate(len)` 이다.
- ★★★ **음수의 뜻이 정반대다** — `with(-1, 9)` 는 **끝 칸**(`[0,1,9]`)을 바꾸고, `a[-1] = 9` 는 **`"-1"` 이라는 이름의 평범한 프로퍼티**를 만든다(`own keys` 에 `"-1"`, `length 3` 그대로).
  배열 칸은 **정수처럼 보이는 문자열 키**일 때만이다 — 정수 키 규칙은 [13번](../13-object-literals-and-properties/2-summary.md)이 정본이다.
- ★★ **`1.5` 도 갈린다** — `with(1.5, 9)` 는 **`1` 로 잘라** `[0,9,2]`, `a[1.5] = 9` 는 **`"1.5"` 프로퍼티**. `"1"` 은 둘 다 칸 `1` 이다.
- ★ **`[3]` `with` 의 인덱스 해석은 `at` 과 같다** — `at` 이 `undefined` 를 주는 자리(`-4` · `3`)에서 `with` 가 던진다. `at` 의 전수는 [26번](../26-array-search-flatten-and-create/2-summary.md)이다.
- ★ **node 18 에서는 `[1]` 여덟 줄이 전부 `TypeError 「a.with is not a function」`** 이다(판 경계). `[2]` 대입 쪽은 두 판이 같다.

### (4) ★★ `reduce` — 초기값이 있으면 한 번 더 불리고, 없고 비었으면 던진다

**언제 쓰나** — 합계·누적 객체를 만들 때 · 빈 배열이 들어올 수 있는 자리.

```js
// js24b-25d-reduce.js
// reduce -- 초기값이 있을 때와 없을 때, 콜백이 몇 번 불리고 무엇을 받나.
const run = (label, f) => {
  const calls = [];
  let r;
  try { r = JSON.stringify(f(calls)); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(34) + "result " + String(r).padEnd(62) + "calls " + calls.length + "  " + calls.join(" "));
};
const add = (calls) => (acc, x, i) => { calls.push("(" + acc + "," + x + ",i" + i + ")"); return acc + x; };

console.log("[1] reduce");
run("[1, 2, 3].reduce(f)", (c) => [1, 2, 3].reduce(add(c)));
run("[1, 2, 3].reduce(f, 0)", (c) => [1, 2, 3].reduce(add(c), 0));
run("[7].reduce(f)", (c) => [7].reduce(add(c)));
run("[].reduce(f, 0)", (c) => [].reduce(add(c), 0));
run("[].reduce(f)", (c) => [].reduce(add(c)));
run("[, , 5].reduce(f)", (c) => [, , 5].reduce(add(c)));
run("[, ,].reduce(f)", (c) => [, ,].reduce(add(c)));
run("[].reduce(f, undefined)", (c) => [].reduce(add(c), undefined));

console.log("");
console.log("[2] reduceRight");
run("[1, 2, 3].reduceRight(f)", (c) => [1, 2, 3].reduceRight(add(c)));
run("[].reduceRight(f)", (c) => [].reduceRight(add(c)));

console.log("");
console.log("[3] string accumulator -- same callback, which side starts");
run("['a','b','c'].reduce(f)", (c) => ["a", "b", "c"].reduce(add(c)));
run("['a','b','c'].reduce(f, '')", (c) => ["a", "b", "c"].reduce(add(c), ""));
run("['a','b','c'].reduce(f, 0)", (c) => ["a", "b", "c"].reduce(add(c), 0));
```
```text
===== node20 js24b-25d-reduce.js (exit=0) =====
[1] reduce
  [1, 2, 3].reduce(f)               result 6                                                             calls 2  (1,2,i1) (3,3,i2)
  [1, 2, 3].reduce(f, 0)            result 6                                                             calls 3  (0,1,i0) (1,2,i1) (3,3,i2)
  [7].reduce(f)                     result 7                                                             calls 0  
  [].reduce(f, 0)                   result 0                                                             calls 0  
  [].reduce(f)                      result TypeError 「Reduce of empty array with no initial value」       calls 0  
  [, , 5].reduce(f)                 result 5                                                             calls 0  
  [, ,].reduce(f)                   result TypeError 「Reduce of empty array with no initial value」       calls 0  
  [].reduce(f, undefined)           result undefined                                                     calls 0  

[2] reduceRight
  [1, 2, 3].reduceRight(f)          result 6                                                             calls 2  (3,2,i1) (5,1,i0)
  [].reduceRight(f)                 result TypeError 「Reduce of empty array with no initial value」       calls 0  

[3] string accumulator -- same callback, which side starts
  ['a','b','c'].reduce(f)           result "abc"                                                         calls 2  (a,b,i1) (ab,c,i2)
  ['a','b','c'].reduce(f, '')       result "abc"                                                         calls 3  (,a,i0) (a,b,i1) (ab,c,i2)
  ['a','b','c'].reduce(f, 0)        result "0abc"                                                        calls 3  (0,a,i0) (0a,b,i1) (0ab,c,i2)
```

```text
   [1, 2, 3].reduce(f)            acc=1 에서 시작 (첫 원소)      f(1,2,i1) f(3,3,i2)          호출 2
   [1, 2, 3].reduce(f, 0)         acc=0 에서 시작 (초기값)       f(0,1,i0) f(1,2,i1) f(3,3,i2) 호출 3

   원소가 하나도 없다 ─┬─ 초기값 있음  -> 초기값 그대로, 호출 0
                      └─ 초기값 없음  -> TypeError   (구멍만 있는 [, ,] 도 「없다」)
   원소가 하나뿐       ─── 초기값 없음  -> 그 원소 그대로, 호출 0   ([7] · [, , 5])
```

- ★★★ **`[].reduce(f)` 는 `TypeError 「Reduce of empty array with no initial value」`** 이다. 명세 note — "It is a TypeError if the array contains no elements and initialValue is not provided."
  ★ **`[, ,]` 도 같은 `TypeError`** — `length` 가 2 여도 **원소(있는 칸)가 없다.** 구멍은 원소가 아니다.
- ★★★ **원소가 하나고 초기값이 없으면 콜백이 한 번도 안 불린다**(`[7]` → `7`, `calls 0`). 콜백 안의 변환(예: 문자열로)이 **적용되지 않은 값**이 그대로 나온다.
- ★★ **초기값 `undefined` 를 명시하면 「초기값이 있다」** 로 친다 — `[].reduce(f, undefined)` 는 던지지 않고 `undefined`. 명세가 **인자의 개수**로 가른다.
- ★★ **`[3]` 초기값이 결과의 타입을 정한다** — 같은 콜백에 `0` 을 주면 `"0abc"`. 초기값 없이 쓰면 **첫 원소가 곧 누산기**라 원소 타입이 누산기 타입이 된다.
- ★ `reduceRight` 는 **끝에서** 시작한다(`(3,2,i1) (5,1,i0)`). 빈 배열 규칙은 같다.

### (5) ★★ `map(parseInt)` — 콜백은 인자를 셋 받는다

**언제 쓰나** — 문자열 배열을 숫자로 바꾸려고 내장 함수를 **그대로** 콜백으로 넘길 때.

```js
// js24b-25e-map-parseint.js
// map(parseInt) -- map 이 콜백에 무엇을 넘기는지 먼저 찍고, 그것을 parseInt 에 그대로 준다.
console.log("[1] what map passes to its callback");
["1", "2", "3"].map((...args) => { console.log("  args " + JSON.stringify(args)); return 0; });

console.log("");
console.log("[2] the same arguments given to parseInt");
for (const [s, i] of [["1", 0], ["2", 1], ["3", 2]]) {
  console.log("  parseInt(" + JSON.stringify(s) + ", " + i + ")".padEnd(4) + "-> " + parseInt(s, i));
}
console.log("  parseInt.length       " + parseInt.length);

console.log("");
console.log("[3] map(parseInt) and the alternatives");
const show = (label, v) => console.log("  " + label.padEnd(40) + JSON.stringify(v.map((x) => (Number.isNaN(x) ? "NaN" : x))));
show("['1','2','3'].map(parseInt)", ["1", "2", "3"].map(parseInt));
show("['10','10','10','10'].map(parseInt)", ["10", "10", "10", "10"].map(parseInt));
show("['1','2','3'].map(Number)", ["1", "2", "3"].map(Number));
show("['1','2','3'].map(s => parseInt(s, 10))", ["1", "2", "3"].map((s) => parseInt(s, 10)));
show("['1.5','2px'].map(Number)", ["1.5", "2px"].map(Number));
show("['1.5','2px'].map(s => parseInt(s, 10))", ["1.5", "2px"].map((s) => parseInt(s, 10)));
show("['1','2','3'].map(parseFloat)", ["1", "2", "3"].map(parseFloat));
console.log("  parseFloat.length     " + parseFloat.length + "   Number.length " + Number.length);
```
```text
===== node20 js24b-25e-map-parseint.js (exit=0) =====
[1] what map passes to its callback
  args ["1",0,["1","2","3"]]
  args ["2",1,["1","2","3"]]
  args ["3",2,["1","2","3"]]

[2] the same arguments given to parseInt
  parseInt("1", 0)   -> 1
  parseInt("2", 1)   -> NaN
  parseInt("3", 2)   -> NaN
  parseInt.length       2

[3] map(parseInt) and the alternatives
  ['1','2','3'].map(parseInt)             [1,"NaN","NaN"]
  ['10','10','10','10'].map(parseInt)     [10,"NaN",2,3]
  ['1','2','3'].map(Number)               [1,2,3]
  ['1','2','3'].map(s => parseInt(s, 10)) [1,2,3]
  ['1.5','2px'].map(Number)               [1.5,"NaN"]
  ['1.5','2px'].map(s => parseInt(s, 10)) [1,2]
  ['1','2','3'].map(parseFloat)           [1,2,3]
  parseFloat.length     1   Number.length 1
```

```text
   ['1','2','3'].map(parseInt)

   map 이 부르는 것          parseInt 가 받아들이는 것          결과
   ----------------          ------------------------          ----
   parseInt('1', 0, arr)     string '1' · radix 0 (= 없음 -> 10)   1
   parseInt('2', 1, arr)     string '2' · radix 1  (범위 밖)        NaN
   parseInt('3', 2, arr)     string '3' · radix 2  ('3' 은 이진수 아님) NaN
                             세 번째 인자는 버려진다

   ★ 콜백의 둘째 매개변수 자리에 「인덱스」가 들어간다
```

- ★★★ **`[1]` `map` 은 콜백에 `(값, 인덱스, 배열)` 셋을 넘긴다** — `args ["1",0,["1","2","3"]]`.
  `parseInt` 는 **매개변수가 둘**(`parseInt.length 2`)이라 **인덱스가 기수(radix)** 로 들어간다.
- ★★★ **`[2]` 같은 인자를 직접 주면 같은 답** — `parseInt("2", 1)` 은 `NaN`(기수 1 은 없다), `parseInt("3", 2)` 는 `NaN`(`3` 은 이진수 숫자가 아니다). 기수 `0` 은 「주지 않음」으로 쳐서 10진이다.
  ★ `['10','10','10','10'].map(parseInt)` 이 `[10, NaN, 2, 3]` — 이진 `10` 은 2, 삼진 `10` 은 3 이다.
- ★★ **JS 는 남는 인자에 아무 말도 안 한다** — [08번](../08-function-forms-and-parameters/2-summary.md)의 「`length` 는 첫 기본값 또는 나머지 앞까지만 센다. `arguments.length` 는 실제로 넘어온 개수다」가 이 사고의 바탕이다.
  함수가 **몇 개를 받을지** 호출하는 쪽이 모른다.
- ★ **고치는 법 둘** — `map(Number)`(`Number.length 1` — 인덱스를 버린다) · `map(s => parseInt(s, 10))`(기수를 못 박는다).
  ★ **둘은 같은 함수가 아니다** — `'2px'` 에 `Number` 는 `NaN`, `parseInt(s, 10)` 은 `2`(앞에서 읽을 수 있는 만큼). `'1.5'` 는 `1.5` 대 `1`. 숫자 변환 규칙은 [03번](../03-numbers-and-bigint/2-summary.md)이다.

### (6) ★★★ 비교 함수가 던지면 — `sort` 의 원본도 그대로다

**언제 쓰나** — 비교 함수가 데이터 이상(`null` 필드 등)에서 던질 수 있을 때 · 파이썬 습관으로 「정렬이 실패하면 리스트가 반쯤 바뀐다」를 예상할 때.

```js
// js24b-25f-comparator-throws.js
// 비교 함수가 도중에 던지면 -- sort 와 toSorted 의 원본은 어떻게 남나. 원본은 [5, 4, 3, 2, 1].
const attempt = (run) => { try { run(); return "returned"; } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };

console.log("[0] how many times the comparator is called when nothing throws");
let calls = 0;
[5, 4, 3, 2, 1].sort((a, b) => { calls++; return a - b; });
console.log("  sort     " + calls);
calls = 0;
attempt(() => [5, 4, 3, 2, 1].toSorted((a, b) => { calls++; return a - b; }));
console.log("  toSorted " + calls);

console.log("");
console.log("[1] the comparator throws at call k");
const cmpThrowingAt = (k) => { let n = 0; return (a, b) => { if (++n === k) throw new Error("call " + k); return a - b; }; };
for (const k of [1, 2, 4]) {
  const a = [5, 4, 3, 2, 1];
  const r = attempt(() => a.sort(cmpThrowingAt(k)));
  console.log("  sort     k=" + k + "   " + r.padEnd(22) + "a " + JSON.stringify(a));
  const b = [5, 4, 3, 2, 1];
  const r2 = attempt(() => b.toSorted(cmpThrowingAt(k)));
  console.log("  toSorted k=" + k + "   " + r2.padEnd(22) + "b " + JSON.stringify(b));
}

console.log("");
console.log("[2] 30 elements in a fixed shuffled order, the comparator throws at call k");
const mixed30 = () => Array.from({ length: 30 }, (_, i) => (i * 7) % 30);
const orig = JSON.stringify(mixed30());
let total = 0;
mixed30().sort((x, y) => { total++; return x - y; });
console.log("  comparator calls when nothing throws: " + total);
for (const k of [1, Math.floor(total / 2), total]) {
  const a = mixed30();
  const r = attempt(() => a.sort(cmpThrowingAt(k)));
  console.log("  sort     k=" + String(k).padEnd(4) + r.padEnd(22) + "a unchanged " + (JSON.stringify(a) === orig));
}

console.log("");
console.log("[3] a comparator that is not a function");
for (const cmp of [undefined, null, "desc", 1]) {
  const a = [2, 1];
  console.log("  " + String(JSON.stringify(cmp)).padEnd(10) + "sort     " + attempt(() => a.sort(cmp)));
  console.log("  " + "".padEnd(10) + "toSorted " + attempt(() => a.toSorted(cmp)));
}
```
```text
===== node20 js24b-25f-comparator-throws.js (exit=0) =====
[0] how many times the comparator is called when nothing throws
  sort     4
  toSorted 4

[1] the comparator throws at call k
  sort     k=1   Error 「call 1」        a [5,4,3,2,1]
  toSorted k=1   Error 「call 1」        b [5,4,3,2,1]
  sort     k=2   Error 「call 2」        a [5,4,3,2,1]
  toSorted k=2   Error 「call 2」        b [5,4,3,2,1]
  sort     k=4   Error 「call 4」        a [5,4,3,2,1]
  toSorted k=4   Error 「call 4」        b [5,4,3,2,1]

[2] 30 elements in a fixed shuffled order, the comparator throws at call k
  comparator calls when nothing throws: 108
  sort     k=1   Error 「call 1」        a unchanged true
  sort     k=54  Error 「call 54」       a unchanged true
  sort     k=108 Error 「call 108」      a unchanged true

[3] a comparator that is not a function
  undefined sort     returned
            toSorted returned
  null      sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「The comparison function must be either a function or undefined」
  "desc"    sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「The comparison function must be either a function or undefined」
  1         sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「The comparison function must be either a function or undefined」
```

```text
   Array.prototype.sort(cmp)  -- 명세의 단계 순서

   ① cmp 가 함수(또는 undefined)인가?  아니면 TypeError      <- 원본을 읽기도 전에
   ② 원본의 칸을 읽어 목록(sortedList)을 만든다
   ③ 목록을 정렬한다  -- cmp 가 던지면 「여기서 멈추고 그 예외를 돌려준다」
   ④ 정렬된 목록을 원본에 되쓴다   <- ③ 이 던지면 여기에 오지 않는다
   ⑤ 남는 칸(구멍 몫)을 지운다

   그래서 cmp 가 몇 번째 호출에서 던지든 원본은 한 칸도 안 바뀐다 -- 마지막 호출(108번째)에서 던져도
```

- ★★★ **`[1]` · `[2]` 비교 함수가 첫 번째든 마지막(`108` 번째)이든 던지면 `sort` 의 원본이 그대로다**(`a unchanged true` 세 줄).
  명세 `sort` 는 **`SortIndexedProperties` 가 끝나야** 되쓰기(`Set`) 단계로 간다 — 그리고 `SortIndexedProperties` 는 비교가 던지면 "stop before performing any further calls to SortCompare and return that Completion Record" 다.
  ★★★ **그래서 이것은 V8 의 사정이 아니라 명세 보장이다** — 원본에 쓰기는 **정렬이 끝난 뒤 한꺼번에** 일어난다.
- ★★★ **파이썬은 반대였다** — 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **10번**이 `[3,1,2,'a'].sort()` 가 `TypeError` 로 끝난 뒤 `m2 = [1, 2, 3, 'a']` 로 **바뀐 채 남는 것**을 찍었다(문서가 "the list will likely be left in a partially modified state" 라 적는다).
  **JS `sort` 는 「제자리」지만 「원자적」이다** — 한 번에 쓰거나 아예 안 쓴다(비교가 던지는 경우에 한해서 — `Set` 자체가 던지는 경우는 이 문서 밖이다).
- ★★ **`[3]` 비교 함수 검사는 `sort` 와 `toSorted` 가 같다** — `null` · `"desc"` · `1` 은 전부 `TypeError`, `undefined` 만 기본 비교. ★ `sort(null)` 도 던진다 — **「비워 두기」는 `undefined` 만**이다.
- ★ **`[0]` 비교 함수 호출 횟수(`4` · `108`)는 근거로 쓰지 않는다** — 명세는 "an implementation-defined sequence of calls to SortCompare" 라고만 적는다. `sort` 와 `toSorted` 가 같은 수(`4`)인 것도 **이 판의 관찰**이다.
- ★ node 18 에서는 `toSorted` 줄이 전부 `TypeError` 라 **`sort` 쪽만 근거가 선다**(`toSorted 0` 은 「안 불렸다」가 아니라 「메서드가 없다」다).

### (7) ★★ 짝 넷 — 복사 메서드는 돌려준 값이 원본이 아니고, 구멍을 `undefined` 로 채운다

**언제 쓰나** — 변형 메서드를 복사 메서드로 바꿔 끼울 때 · 「`slice()` 를 먼저 하고 `sort()`」 같은 옛 관용구를 대신할 때.

```js
// js24b-25b-pairs.js
// 짝 넷 -- 바꾸는 쪽과 복사하는 쪽에 같은 일을 시키고 (돌려준 값 · 그것이 원본과 같은 객체인가 · 원본) 을 찍는다.
// 배열은 칸마다 찍는다 -- 구멍은 <hole>, undefined 값은 undefined (JSON.stringify 는 둘 다 null 로 뭉갠다).
const cell = (a, i) => (i in a ? (a[i] === undefined ? "undefined" : JSON.stringify(a[i])) : "<hole>");
const show = (v) => (Array.isArray(v) ? "[" + Array.from({ length: v.length }, (_, i) => cell(v, i)).join(",") + "]" : String(v));
const attempt = (run) => { try { return run(); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };

const pair = (label, run) => {
  const arr = [30, 10, 20];
  let r, same;
  try { r = run(arr); same = r === arr; r = show(r); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; same = "-"; }
  console.log("  " + label.padEnd(22) + "returned " + r.padEnd(14) + "  === arr " + String(same).padEnd(6) + "  arr " + show(arr));
};
console.log("[1] four pairs on [30, 10, 20]");
pair("sort()", (a) => a.sort());
pair("toSorted()", (a) => a.toSorted());
pair("reverse()", (a) => a.reverse());
pair("toReversed()", (a) => a.toReversed());
pair("splice(1, 1, 99)", (a) => a.splice(1, 1, 99));
pair("toSpliced(1, 1, 99)", (a) => a.toSpliced(1, 1, 99));
pair("a[1] = 99", (a) => (a[1] = 99));
pair("with(1, 99)", (a) => a.with(1, 99));

console.log("");
console.log("[2] a chain that starts from a copy");
const base = [30, 10, 20];
console.log("  base.toSorted().reverse()       " + attempt(() => show(base.toSorted().reverse())) + "   base " + show(base));
console.log("  base.slice().sort().reverse()   " + attempt(() => show(base.slice().sort().reverse())) + "   base " + show(base));

console.log("");
console.log("[3] how deep is the copy");
const rows = [{ id: 2 }, { id: 1 }];
console.log(attempt(() => {
  const sorted = rows.toSorted((a, b) => a.id - b.id);
  const out = [];
  out.push("  sorted === rows            " + (sorted === rows));
  out.push("  sorted[1] === rows[0]      " + (sorted[1] === rows[0]));
  sorted[1].id = 200;
  out.push("  after sorted[1].id = 200   rows " + JSON.stringify(rows));
  return out.join("\n");
}));

console.log("");
console.log("[4] holes in the receiver [3, <hole>, 1]");
const row4 = (label, run) => console.log("  " + label.padEnd(22) + attempt(run));
row4("toSorted()", () => show([3, , 1].toSorted()));
row4("sort()", () => { const d = [3, , 1]; d.sort(); return show(d); });
row4("toReversed()", () => show([3, , 1].toReversed()));
row4("reverse()", () => { const d = [3, , 1]; d.reverse(); return show(d); });
row4("with(0, 9)", () => show([3, , 1].with(0, 9)));
row4("slice()", () => show([3, , 1].slice()));
row4("map(x => x)", () => show([3, , 1].map((x) => x)));
```
```text
===== node20 js24b-25b-pairs.js (exit=0) =====
[1] four pairs on [30, 10, 20]
  sort()                returned [10,20,30]      === arr true    arr [10,20,30]
  toSorted()            returned [10,20,30]      === arr false   arr [30,10,20]
  reverse()             returned [20,10,30]      === arr true    arr [20,10,30]
  toReversed()          returned [20,10,30]      === arr false   arr [30,10,20]
  splice(1, 1, 99)      returned [10]            === arr false   arr [30,99,20]
  toSpliced(1, 1, 99)   returned [30,99,20]      === arr false   arr [30,10,20]
  a[1] = 99             returned 99              === arr false   arr [30,99,20]
  with(1, 99)           returned [30,99,20]      === arr false   arr [30,10,20]

[2] a chain that starts from a copy
  base.toSorted().reverse()       [30,20,10]   base [30,10,20]
  base.slice().sort().reverse()   [30,20,10]   base [30,10,20]

[3] how deep is the copy
  sorted === rows            false
  sorted[1] === rows[0]      true
  after sorted[1].id = 200   rows [{"id":200},{"id":1}]

[4] holes in the receiver [3, <hole>, 1]
  toSorted()            [1,3,undefined]
  sort()                [1,3,<hole>]
  toReversed()          [1,undefined,3]
  reverse()             [1,<hole>,3]
  with(0, 9)            [9,undefined,1]
  slice()               [3,<hole>,1]
  map(x => x)           [3,<hole>,1]
```

```text
   변형                  돌려주는 것            복사                  돌려주는 것
   ----                  ----------            ----                  ----------
   sort()                arr 자신               toSorted()            새 배열 (정렬됨)
   reverse()             arr 자신               toReversed()          새 배열 (뒤집힘)
   splice(1, 1, 99)      「지운 것들」 [10]      toSpliced(1, 1, 99)   ★ 「바뀐 결과 전체」 [30,99,20]
   a[1] = 99             99 (대입식의 값)        with(1, 99)           새 배열 (한 칸 바뀜)

   ★ toSpliced 만 짝과 「돌려주는 것」의 종류가 다르다 -- 지운 것이 아니라 결과다
```

- ★★★ **`[1]` 복사 쪽 넷은 전부 `=== arr false` 에 원본 `[30,10,20]` 그대로**, 변형 쪽 `sort`·`reverse` 는 `=== arr true` 다.
  ★★★ **`splice` 와 `toSpliced` 는 돌려주는 것의 뜻이 다르다** — `splice` 는 **지운 원소들**(`[10]`), `toSpliced` 는 **바뀐 뒤의 전체 배열**(`[30,99,20]`). 이름만 보고 바꿔 끼우면 여기서 틀린다.
- ★★ **`[2]` 사슬의 첫 고리만 복사면 나머지 변형은 복사본에 일어난다** — `base.toSorted().reverse()` 의 `reverse` 는 **새 배열을 뒤집는다**(`base` 그대로). 옛 관용구 `slice().sort()` 와 결과가 같다.
  ★ 반대로 **첫 고리가 변형이면** 사슬 전체가 원본을 바꾼다 — 그 함정은 [24번](../24-array-mutating-methods/2-summary.md)이 정본이다.
- ★★★ **`[3]` 복사는 한 겹이다** — `sorted === rows` 는 `false` 인데 **`sorted[1] === rows[0]` 은 `true`**. 복사본에서 `id` 를 바꾸면 **원본의 객체가 바뀐다**(`rows [{"id":200},{"id":1}]`).
  스프레드의 얕은 복사와 같은 성질이다([11번](../11-spread-and-rest/2-summary.md)). 깊은 복사는 [목록의 **48번 주제**](../48-deep-copy-methods-compared/).
- ★★★ **`[4]` 구멍 — 복사 메서드는 구멍을 `undefined` 로 채우고, 옛 메서드는 구멍을 남긴다.**
  `toSorted()` 는 `[1,3,undefined]` 인데 `sort()` 는 `[1,3,<hole>]` · `toReversed()` 는 `[1,undefined,3]` 인데 `reverse()` 는 `[1,<hole>,3]` · `with` 도 `undefined` · `slice`·`map` 은 `<hole>` 을 남긴다.
  ★ 명세가 그대로 갈라 적는다 — `sort` 는 `SortIndexedProperties(…, skip-holes)`, `toSorted` 는 `read-through-holes`. `toReversed`·`with` 는 칸마다 **`Get`** 으로 읽어 **`CreateDataPropertyOrThrow`** 로 쓴다 — 구멍을 읽으면 `undefined` 이고, 그것을 **칸으로 만든다.**
  ★ 메서드별 구멍 처리의 전수 격자는 [26번](../26-array-search-flatten-and-create/2-summary.md)이 정본이다.

```text
   원본 [3, <hole>, 1]

   slice · map · sort · reverse         toSorted · toReversed · with · toSpliced
   (HasProperty 로 「있나」 먼저 묻는다)     (Get 으로 그냥 읽는다)
          │                                        │
     없는 칸은 건너뛴다                         없는 칸 -> undefined
          ▼                                        ▼
   결과에도 구멍                             결과에는 구멍이 없다 -- undefined 가 든 칸
```

### (8) ★★ 결과는 어느 클래스인가 — species 를 읽는 쪽과 안 읽는 쪽

**언제 쓰나** — `class X extends Array` 에서 `map`·`toSorted` 결과가 `X` 일 것이라 기대할 때.

★ **이 동작은 22번이 이미 쟀다 — 다시 재지 않고 인용한다.** [22번](../22-symbol-and-well-known-symbols/2-summary.md) 동작 (5-b)가 species getter 에 로그를 심어 **메서드 14가지**를 셌고, 집계 줄이 **`methods that read species 7 / 14`** 였다.

```text
   22번의 표에서 이 편의 메서드만 추리면

   species 를 읽는다 (결과가 하위 클래스일 수 있다)   species 를 안 읽는다 (결과는 늘 Array)
   ---------------------------------------------   --------------------------------------
   map · filter · slice · concat  (+ splice)          toSorted · toReversed · with · toSpliced
                                                      (reduce 는 배열을 안 만든다)

   17번:  class Stack extends Array  ->  map · filter · slice 결과의 constructor 가 Stack
```

- ★★ **ES2015 계열(`map` · `filter` · `slice` · `concat`)은 `ArraySpeciesCreate` 로 결과를 만든다** — 하위 클래스면 **하위 클래스 인스턴스**다([17번](../17-inheritance-and-super/2-summary.md) 동작 (5)의 `[2]`).
- ★★★ **ES2023 복사 메서드 넷은 species 를 한 번도 안 읽는다** — 결과가 늘 **`Array`** 다(22번 표의 `toSorted - Array` 네 줄). 명세 단계도 `ArrayCreate(len)` 이다(동작 (1)·(3)에서 본 `with`·`toReversed`·`toSorted` 단계).
  ★ 그래서 **`Stack` 을 `toSorted` 하면 `Stack` 메서드가 없는 평범한 배열**이 돌아온다. 같은 「새 배열을 돌려주는」 메서드인데 **판에 따라 규칙이 다르다.**
- ★ `concat` 이 인자를 펼칠지 정하는 `Symbol.isConcatSpreadable` 도 [22번](../22-symbol-and-well-known-symbols/2-summary.md) 동작 (5-c)의 `[3]` 이 정본이다(배열에 `false` 면 통째로 한 원소, 유사 배열에 `true` 면 펼친다).

### (9) ★ `slice` · `concat` 의 모양 — 음수 인덱스, 한 겹 펼치기

**언제 쓰나** — `slice` 로 복사본을 뜨거나 끝에서 자를 때 · `concat` 에 배열과 값을 섞어 넘길 때.

```js
// js24b-25g-shapes.js
// slice · concat 의 인자 규칙 -- 음수 인덱스, 비워 둔 인자, 몇 겹까지 펼치나.
const row = (label, v) => console.log("  " + label.padEnd(36) + JSON.stringify(v));
const a = [0, 1, 2, 3, 4];
console.log("[1] slice on [0, 1, 2, 3, 4]");
row("slice()", a.slice());
row("slice() === a", a.slice() === a);
row("slice(-2)", a.slice(-2));
row("slice(1, -1)", a.slice(1, -1));
row("slice(3, 1)", a.slice(3, 1));
row("slice(10)", a.slice(10));
row("slice('1', '3')", a.slice("1", "3"));

console.log("");
console.log("[2] concat");
row("[1].concat(2, [3], [[4]])", [1].concat(2, [3], [[4]]));
row("[1].concat('ab')", [1].concat("ab"));
row("[1].concat({ 0: 'x', length: 1 })", [1].concat({ 0: "x", length: 1 }));
row("[1].concat() === [1]", (() => { const b = [1]; return b.concat() === b; })());
row("[1].concat([2]) length", [1].concat([2]).length);

console.log("");
console.log("[3] filter and map whose callbacks keep every element");
const b = [1, 2];
row("b.filter(() => true) === b", b.filter(() => true) === b);
row("b.map(x => x) === b", b.map((x) => x) === b);
row("b.filter(() => false)", b.filter(() => false));
```
```text
===== node20 js24b-25g-shapes.js (exit=0) =====
[1] slice on [0, 1, 2, 3, 4]
  slice()                             [0,1,2,3,4]
  slice() === a                       false
  slice(-2)                           [3,4]
  slice(1, -1)                        [1,2,3]
  slice(3, 1)                         []
  slice(10)                           []
  slice('1', '3')                     [1,2]

[2] concat
  [1].concat(2, [3], [[4]])           [1,2,3,[4]]
  [1].concat('ab')                    [1,"ab"]
  [1].concat({ 0: 'x', length: 1 })   [1,{"0":"x","length":1}]
  [1].concat() === [1]                false
  [1].concat([2]) length              2

[3] filter and map whose callbacks keep every element
  b.filter(() => true) === b          false
  b.map(x => x) === b                 false
  b.filter(() => false)               []
```

- ★★ **`slice()` 는 인자 없이 전체 복사**(`=== a false`) · **음수는 끝에서** 센다(`slice(-2)` → `[3,4]`, `slice(1, -1)` → `[1,2,3]`) · 시작이 끝보다 뒤면 `[]` · 범위를 넘어도 던지지 않는다(`slice(10)` → `[]`).
  ★ **`with` 와 대비** — `slice` 는 범위 밖을 **잘라 주고**, `with` 는 **던진다**(동작 (3)).
- ★★ **`concat` 은 배열 인자를 한 겹만 펼친다** — `[1].concat(2, [3], [[4]])` 이 `[1,2,3,[4]]`. 문자열(`'ab'`)도 유사 배열(`{0:'x', length:1}`)도 **펼치지 않고 한 원소**로 넣는다 — 기준은 「이터러블인가」가 아니라 **`IsConcatSpreadable`**(배열이거나 `Symbol.isConcatSpreadable` 이 참)이다.
- ★ **`[3]` 콜백이 전부 통과시켜도 `filter`·`map` 은 새 배열**이다(`=== b false`). 「아무것도 안 바뀌었으면 같은 배열을 돌려준다」는 최적화는 **없다** — 참조 비교로 변화를 감지하는 코드는 늘 「바뀌었다」로 본다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28 — 돌리지 않은 코드 펜스를 싣지 않는다).

| 형태 | 돌려주는 것 | 원본 | species | 판 | 어디서 봤나 |
|---|---|---|---|---|---|
| `a.map(f)` · `a.filter(f)` | 새 배열 | 메서드는 안 쓴다 · **콜백은 쓸 수 있다** | 읽는다 | ES2015 이전 | 동작 (1)·(9) |
| `a.reduce(f[, init])` · `a.reduceRight(…)` | 누산 결과 — 비었고 `init` 없으면 `TypeError` | 안 쓴다 | — | ES2015 이전 | 동작 (4) |
| `a.slice([s[, e]])` | 새 배열 — 음수는 끝에서, 범위 밖은 잘린다 | 안 쓴다 | 읽는다 | ES2015 이전 | 동작 (9) |
| `a.concat(...v)` | 새 배열 — `IsConcatSpreadable` 인 인자만 한 겹 펼친다 | 안 쓴다 | 읽는다 | ES2015 이전 | 동작 (9) |
| `a.toSorted([cmp])` | 새 배열 — 구멍은 `undefined` | 안 쓴다 | **안 읽는다** | **ES2023** | 동작 (6)·(7) |
| `a.toReversed()` | 새 배열 — 구멍은 `undefined` | 안 쓴다 | **안 읽는다** | **ES2023** | 동작 (7) |
| `a.toSpliced(s, n, ...items)` | ★ **바뀐 뒤의 전체** 새 배열(지운 것이 아니다) | 안 쓴다 | **안 읽는다** | **ES2023** | 동작 (7) |
| `a.with(i, v)` | 새 배열 — `i` 가 범위 밖이면 **`RangeError`**, 음수는 끝에서 | 안 쓴다 | **안 읽는다** | **ES2023** | 동작 (3) |

- **비교 함수** — `sort`·`toSorted` 둘 다 **`undefined` 가 아닌 비함수면 먼저 `TypeError`**(원본을 읽기 전에).
- **인덱스** — `with`·`at` 은 `ToIntegerOrInfinity` 뒤 음수면 `len + i`. 대입 `a[i]` 는 **프로퍼티 키**로 읽는다.
- **깊이** — 복사는 전부 **한 겹**. 원소가 객체면 참조가 옮겨진다.

## 어디서 틀리나

### (1) ★★★ 「비변형 메서드니까 원본이 안전하다」고 믿는다 — 콜백이 쓴다

격자 마지막 행 — `map((x, i, a) => a[i] = 0)` 이 **`set 3`**, 원본이 `[0,0,0]`(동작 (1)). 메서드가 안 쓴다는 것이지 **콜백이 세 번째 인자로 받은 원본에 쓰는 것**은 못 막는다.

### (2) ★★★ 복사본의 객체를 고치면 원본은 안 바뀐다고 믿는다

`toSorted` 결과에서 `id` 를 바꿨더니 **원본의 객체가 바뀌었다**(`sorted[1] === rows[0]` true — 동작 (7)의 `[3]`). 복사는 **배열 한 겹**이다.

### (3) ★★★ `with` 를 대입의 불변판으로 믿고 범위 밖이나 음수를 넘긴다

`with(3, v)` 는 **`RangeError`**(대입은 조용히 늘린다), `with(-1, v)` 는 **끝 칸**(대입은 `"-1"` 프로퍼티) — 동작 (3). 뜻이 **두 군데서 반대**다.

### (4) ★★★ `splice` 를 `toSpliced` 로 바꿔 끼우고 반환값을 그대로 쓴다

`splice` 는 **지운 것**, `toSpliced` 는 **결과 전체**를 돌려준다(`[10]` 대 `[30,99,20]` — 동작 (7)의 `[1]`).

### (5) ★★★ 빈 배열에 초기값 없이 `reduce` 를 부른다

`TypeError 「Reduce of empty array with no initial value」`(동작 (4)). 구멍만 있는 배열도 같다. **초기값을 늘 준다** — 원소가 하나일 때 콜백이 안 불리는 함정도 같이 사라진다.

### (6) ★★★ `map(parseInt)` 로 문자열을 숫자로 바꾼다

`[1, NaN, NaN]`(동작 (5)). 인덱스가 기수로 들어간다. `map(Number)` 나 `map(s => parseInt(s, 10))` — **둘의 뜻도 다르다**(`'2px'`).

### (7) ★★ 「`toSorted` 가 구멍을 남긴다」고 믿는다 — 또는 그 반대

복사 메서드 넷은 **`undefined` 로 채우고**, `slice`·`map`·`sort`·`reverse` 는 **구멍을 남긴다**(동작 (7)의 `[4]`). `in` 으로 칸을 검사하는 코드는 둘에서 답이 갈린다.

### (8) ★★ `Array` 하위 클래스에 `toSorted` 를 쓰고 하위 클래스 메서드를 부른다

결과는 **평범한 `Array`** 다 — 복사 메서드 넷은 species 를 안 읽는다(동작 (8), 22번 표).

### (9) ★★ node 18 에서 격자를 돌리고 「0 이니 안 바꿨다」로 읽는다

없는 메서드가 **던진 채 쓰기 0** 으로 세어졌다(동작 (1) 끝의 node 18 집계). **「던졌나」를 따로 세야** 0 이 뜻을 갖는다.

### (10) ★ 「`toSorted` 는 복사라서 느리니 `sort` 를 쓴다」

**안 쟀다.** 이 문서는 시간도 메모리도 재지 않았다. 잰 것은 **트랩과 호출 횟수**뿐이다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **비변형 메서드가 원본에 `[[Set]]`·`[[DefineOwnProperty]]`·`[[Delete]]` 를 하지 않는 것** — 명세 단계가 원본에는 `Get`·`HasProperty` 만, 결과에는 `CreateDataPropertyOrThrow` 만 한다. 격자의 **0 칸**이 그것의 관찰이다.
- ★★★ **`sort` 가 정렬을 다 끝낸 뒤에 되쓰는 것** — 비교가 던지면 원본이 그대로다(`SortIndexedProperties` 뒤에 `Set` 단계).
- `with` 의 `RangeError` 조건(`actualIndex ≥ len` 또는 `< 0`) · `ToIntegerOrInfinity` 로 자르기 · 음수는 `len + i`.
- `reduce` 가 원소가 없고 초기값이 없으면 `TypeError` · 초기값이 없으면 첫 원소로 시작하는 것.
- 복사 메서드 넷이 **`ArrayCreate`** 로 결과를 만드는 것(species 를 안 읽는다) · 구멍을 `Get` 으로 읽어 **`undefined` 칸으로 쓰는 것**(`toSorted` 는 `read-through-holes`).
- `map` 이 콜백에 `(값, 인덱스, 배열)` 을 넘기는 것 · `parseInt` 의 둘째 인자가 기수인 것.
- 비교 함수가 `undefined` 가 아닌 비함수면 **원본을 읽기 전에** `TypeError`.
- 예외의 **종류**(`TypeError` · `RangeError`).

### 엔진(V8) 구현 · 이 판의 관찰

- ★★ **비교 함수 호출 횟수**(`4` · `108`)와 **순서** — 명세는 "implementation-defined sequence of calls" 다.
- ★ **`get` 트랩 횟수** — 명세 단계를 따르는 것으로 보이지만 이 문서는 그 수를 하나하나 명세와 맞춰 보지 않았다. 근거로 안 쓴다.
- 예외 **문구 전부** — `Invalid index : 3` · `Reduce of empty array with no initial value` · `The comparison function must be either a function or undefined` · node 18 의 `… is not a function`(★ 소스 모양 `[3,(intermediate value),1]` 이 박힌다).

### 그래서 이렇게 적으면 틀린다

- ✗ 「비변형 메서드를 쓰면 원본이 안 바뀐다」 → ○ 「**메서드 자신은** 안 쓴다. 콜백은 쓸 수 있고, 원소 객체는 공유된다」
- ✗ 「`toSorted` 는 `sort` 에 `slice` 를 붙인 것」 → ○ 「결과는 같지만 **구멍을 `undefined` 로 채우고 species 를 안 읽는다**」
- ✗ 「JS 의 `sort` 도 실패하면 반쯤 바뀐다(파이썬처럼)」 → ○ 「**비교가 던지면 원본은 그대로**다 — 명세 단계」
- ✗ 「`with(i, v)` 는 `a[i] = v` 의 복사판」 → ○ 「범위 밖은 **`RangeError`**, 음수는 **끝에서**」
- ✗ 「`toSorted` 는 ES2024」 → ○ **ES2023**(finished proposals). 목록 README 의 표기가 다르다.
- ✗ 「`toSorted` 는 복사라서 느리다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **복사 메서드 넷** — 원본을 **다른 코드가 같이 들고 있을 때**(상태 관리 · 인자로 받은 배열 · 캐시). 판을 확인한다 — **node 18 에 없다.**
- **`map` · `filter` · `slice` · `concat`** — 새 배열이 필요할 때. 콜백 안에서는 **원본(세 번째 인자)에 쓰지 않는다.**
- **`reduce`** — 늘 **초기값과 함께.** 합계라면 `0`, 객체 누적이라면 `{}` 나 `new Map()`.
- **변형 메서드(24편)** — 배열을 **혼자 소유**할 때. 복사할 이유가 없다.
- ★ **안 쓰는 자리** — **깊은 복사가 필요할 때**(복사는 한 겹이다 — 48번 주제) · `Array` 하위 클래스를 유지해야 할 때 `toSorted` 류(평범한 `Array` 가 된다) · 구멍을 구멍으로 남겨야 할 때 `toSorted` 류.

## 핵심 문장

1. ★★★ 원본을 `Proxy` 로 감싸 쓰기 트랩을 세면 **비변형 아홉은 0, 변형 일곱은 전부 0 이 아니다**(`9 / 17` — 나머지 한 행은 콜백이 쓰는 `map`) — 단 **콜백이 원본에 쓰는 것**은 비변형 메서드도 못 막는다.
2. ★★★ 복사 메서드 넷(**ES2023**)은 돌려준 값이 원본이 아니고, **구멍을 `undefined` 로 채우고, species 를 안 읽는다.** `toSpliced` 만 **돌려주는 것의 종류**가 짝(`splice`)과 다르다.
3. ★★★ **`with` 는 범위 밖에서 `RangeError`**, 대입은 조용히 늘린다 — 음수도 `with` 는 끝에서, 대입은 글자 키.
4. ★★★ **`reduce` 는 비었고 초기값이 없으면 `TypeError`** 이고, 원소 하나면 콜백을 안 부른다 — 초기값을 늘 준다.
5. ★★★ **`sort` 는 비교가 던지면 원본을 한 칸도 안 바꾼다**(명세 단계) — 파이썬 `list.sort` 와 반대다. 복사는 전부 **한 겹**이다.

## 관련 자료

- [ECMA-262 2025(16판)](https://262.ecma-international.org/16.0/) — `Array.prototype` 의 `sort` · `toSorted` · `toReversed` · `toSpliced` · `with` · `reduce` · `map` · `SortIndexedProperties`
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — Change Array by Copy **2023**
- [24 — 배열 변형 메서드](../24-array-mutating-methods/2-summary.md) — ★ **경계**: 그쪽은 **원본을 바꾸는 메서드 자체**(반환값 · 기본 비교 · 안정 정렬)까지, 여기는 **같은 일을 복사로 하면 무엇이 달라지나**부터.
- [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md) — ★ **경계**: 그쪽은 **구멍을 메서드마다 어떻게 보나의 전수 격자**, 여기는 **복사 메서드가 구멍을 채운다**는 한 줄.
- [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) · [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md) — ★ **경계**: species 를 **읽는 메서드**(22)와 **결과 생성자**(17)는 거기가 정본, 여기는 인용만.
- [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) — `length` 와 남는 인자(`map(parseInt)` 의 바탕).
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — 얕은 복사.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **10번**(`sort` 대 `sorted` · 정렬 실패 시 부분 변경) — 동작 (6)의 대비.

## 용어 풀이

- **비변형 메서드** — 호출한 배열에 **메서드 자신이** 쓰지 않는 메서드. 콜백의 쓰기는 별개다.
- **복사 메서드(Change Array by Copy)** — ES2023 의 `toSorted` · `toReversed` · `toSpliced` · `with`. 변형 메서드의 짝.
- **`Proxy` 트랩** — 객체의 기본 연산(`get`·`set`·`defineProperty`·`deleteProperty` …)을 가로채는 함수.
- **`receiver`** — `[[Set]]` 에서 「누구에게 프로퍼티를 정의하나」. 트랩이 그것을 Proxy 로 넘기면 정의가 다시 트랩에 걸린다.
- **`ArrayCreate`** — 평범한 `Array` 를 만드는 명세 연산. 복사 메서드가 쓴다.
- **`ArraySpeciesCreate`** — `this.constructor[Symbol.species]` 로 결과를 만드는 연산. `map`·`filter`·`slice`·`concat` 이 쓴다.
- **`SortIndexedProperties`** — 칸을 읽어 목록으로 정렬하는 명세 연산. `skip-holes`(`sort`) 와 `read-through-holes`(`toSorted`) 두 방식이 있다.
- **`ToIntegerOrInfinity`** — 값을 정수로 자르는 연산(`1.5` → `1`). `with`·`at`·`slice` 가 인덱스에 쓴다.
- **구멍(hole)** — `length` 안에 있지만 **프로퍼티가 없는** 칸. `i in a` 가 `false`.
- **기수(radix)** — 수를 읽는 진법. `parseInt` 의 둘째 인자. `0`·`undefined` 는 「주지 않음」.
- **얕은 복사** — 컨테이너만 새로 만들고 원소는 **그대로** 옮기는 복사. 객체 원소는 공유된다.

## 더 들어가면

- **`Set` 이 던지는 경우의 `sort`** — 되쓰는 도중 원본이 동결돼 있거나 setter 가 던지면 **그때는 일부만 쓰인 채** 끝날 수 있다(명세의 `?` 가 되쓰기 단계에도 붙어 있다). 이 문서는 **비교가 던지는 경우만** 쟀다. 동결 배열에 쓰는 쪽은 [24번](../24-array-mutating-methods/2-summary.md)과 [14번](../14-property-descriptors-and-freezing/2-summary.md)이다.
- **`TypedArray` 의 복사 메서드** — 이 배치는 `TypedArray` 를 **한 줄도 안 돌렸다.** 어느 메서드가 거기에도 있는지는 이 문서가 말하지 않는다.
- **`Proxy` 불변식** — 트랩이 거짓을 말할 수 있는 한계는 [목록의 **45번 주제**](../45-proxy/)다.
