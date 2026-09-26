# js/syntax/27 — `Object` 정적 메서드: 「복사·나열·묶기 — 결과가 같아 보여도 부르는 것이 다르다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `Object.assign({}, src)` 와 `{ ...src }` 는 결과 객체를 찍으면 **한 글자도 같다.** 갈리는 것은 **그 과정에서 무엇을 불렀나**다.
> 그래서 원본에는 **getter**, 대상에는 **setter**, 뷰 쪽에는 **`Proxy` 트랩**을 심어 호출 순서와 횟수를 찍는다(동작 (1)·(4)).
> ★★ 보조로 **② 전수 격자**(복사 도구 넷 × 성질 여섯 — 동작 (2))와 **④ 예외의 이름·문구**(동작 (3)·(5)·(6))를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Properties of the Object Constructor](https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-properties-of-the-object-constructor) —
>   `Object.assign` · `Object.keys`/`values`/`entries` · `Object.fromEntries` · `Object.groupBy`(와 그 note) · `Map.groupBy`
> - [ECMA-262 — Abstract Operations](https://tc39.es/ecma262/multipage/abstract-operations.html) — `EnumerableOwnProperties` · `GroupBy` · `Set`
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(`Object.values`/`entries` 2017 · `Object.fromEntries` 2019 · Array Grouping 2024)
> - 명세 문장은 이 배치가 받아 둔 **ES2025 판 HTML 에서 읽었다**(알고리즘 단계를 옮기지 않고 연산 이름과 짧은 인용만 싣는다).
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 값·호출 로그·예외 타입과 메시지는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★★ **`Object.groupBy`·`Map.groupBy`(ES2024)는 두 node 판에 없다**(아래 판별 블록). 그 탐침은 **Google Chrome 151 을 헤드리스로** 돌렸다 —
> 배너가 `google-chrome --headless` 로 시작하는 블록이 그것이다. 페이지는 `console.log` 를 가로채 줄을 모은다(`js24b-page.html`).
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** `이름 「메시지」` 꼴로 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★ **이 주제의 node 탐침 여섯 개는 두 판에서 한 글자도 같았다**(아래 대조기의 `identical` 줄들).
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `Object.keys` | ES5 | 세 판 다 있다 |
> | `Object.assign` · own 키 순서(정수 키 먼저) | **ES2015** | 세 판 다 있다 |
> | `Object.values` · `Object.entries` | **ES2017** | 세 판 다 있다 |
> | `Object.fromEntries` | **ES2019** | 세 판 다 있다 |
> | `Object.hasOwn` | ES2022 | 세 판 다 있다(탐침이 쓴다) |
> | `Object.groupBy` · `Map.groupBy` | **ES2024** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | `assign` 이 원본 getter 와 대상 setter 를 **어떤 순서로 몇 번** 부르나(동작 (1)) · `keys`/`values`/`entries` 가 `Proxy` 에 무엇을 묻나(동작 (4)) · `groupBy` 콜백의 인자와 횟수(동작 (6)) |
> | ★★ **② 전수 격자** | 복사 도구 **4개** × 성질 **6개** — `assign` 열과 **갈린 칸을 스크립트가 센다**(동작 (2)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 읽기 전용 대상 · `fromEntries` 의 입력 검사 · ★ **`groupBy` 결과의 `toString`/`String()`**(동작 (6)) |
> | ★ **③ 브랜드 태그** | `groupBy` 결과에 `Object.prototype.toString.call` 이 **`[object Object]`** 라고 답하는 한 줄뿐이다 — 15번에서 쓴 방식 그대로. 이 주제의 질문은 아니다 |
> | ★ **⑤ 두 판 대조기** | 이 주제의 node 탐침은 **전부 `identical`** — 두 판이 갈릴 기능(`groupBy`)은 둘 다 없어서 Chrome 으로 창을 바꿨다 |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 가 한 줄도 없다. 전부 런타임 의미다 — **잴 것이 없다** |
> | ★ **안 쟀다 — 성능** | 「`assign` 이 스프레드보다 빠르다」·「`structuredClone` 은 느리다」를 **한 줄도 쓰지 않는다.** 시간도 바이트도 안 쟀다. 센 것은 **호출 횟수**뿐이다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구** — V8 의 것이다(`Cannot assign to read only property 'a' of object '#<Object>'` 의 `#<Object>` 같은 표기). 다른 엔진은 다르게 적는다 | ★★★ **호출 로그의 순서와 개수** · 격자의 y/n 과 「갈린 칸 N / M」 · 키의 **순서** · 예외의 **종류**(`TypeError`) |
> | 대조기 블록의 **다른 주제 줄**(같은 배치가 한 대조기를 공유한다) | ★★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 하나도 없다**(재대조 동일) |
>
> **선행** — [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md)(직접 선행 — ★★★ **정수 키가 앞서는 열거 순서와 「뷰 일곱 가지」 격자는 거기서 이미 쟀다**) ·
> [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md)(★★★ **대상 setter 호출 0회 대 1회**는 거기서 쟀다) ·
> [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md)(`writable: false` · `freeze` 가 얕은 것) ·
> [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md)(`Object.create(null)`) · [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) ·
> [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md)(심볼 키를 누가 보나) · [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md)(`Map` 키와 `-0`).
> **같은 배치** — [24 — 배열 변형 메서드](../24-array-mutating-methods/2-summary.md) · [25 — 배열 비변형·복사 메서드](../25-array-non-mutating-and-copy-methods/2-summary.md) · [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md).
>
> ★★ **경계 — 열거 순서와 뷰의 격자는 13번이 정본이다.** 여기서는 **그 순서를 `keys`·`entries`·`assign` 이 그대로 따른다는 것**과 **뷰가 무엇을 부르나**만 본다.
> ★★ **경계 — 스프레드의 트랩 로그는 11번이 정본이다.** 여기서는 **`assign` 쪽의 getter·setter**를 잰다.
> ★★ **경계 — 깊은 복사는** [목록의 **48번 주제**](../48-deep-copy-methods-compared/)가 정본이다. 여기서는 `structuredClone` 을 **격자의 한 열**로만 둔다.

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

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 이 주제의 탐침(`js24b-27?-*.js`)은 전부 `identical` 이다. 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`identical 26  ·  differs 4  ·  total 30`

## 한눈에 — 쉽게 말하면

**`Object.assign` 은 「이사 업체」이고, 스프레드는 「새 집을 똑같이 지어 주는 업체」다.**
이사 업체는 원래 집의 물건을 **하나씩 꺼내서**(getter 를 부른다) 새 집의 **그 자리에 넣는다**(대상의 setter 를 부른다).
새 집 자리에 자동문이 달려 있으면 이사 업체는 그 문을 **연다**. 새로 짓는 업체는 **문째 새로 짓는다** — 원래 있던 자동문은 안 연다.

- ★★★ **물건은 한 번씩 꺼낸다.** 꺼낸 것은 **값**이다 — getter 자체가 복사되지 않는다.
- ★★★ **상자 안의 상자는 안 연다.** 중첩 객체는 **같은 것**이 새 집에도 들어간다(얕은 복사).
- ★★★ **도중에 문이 잠겨 있으면 거기서 멈춘다.** 이미 옮긴 물건은 **그대로 둔다**(되돌리지 않는다).
- ★★ **`Object.groupBy` 는 「빈 땅에 지은 창고」다.** 벽에 기본으로 붙어 있던 `toString` 같은 **붙박이가 하나도 없다** — 그래야 `"toString"` 이라는 이름의 묶음이 붙박이와 안 부딪친다.

```text
   Object.assign(target, src)                          { ...src }
   --------------------------                          ----------
   src 의 own 키를 순서대로                               src 의 own 키를 순서대로
     열거 가능한가?  (아니면 건너뛴다)                       열거 가능한가?
     v = src[k]          <- getter 를 부른다              v = src[k]          <- getter 를 부른다
     target[k] = v       <- 대입 : setter 를 부른다        새 객체에 k 를 정의  <- setter 는 안 부른다
                            실패하면 TypeError                                   (새 객체라 막을 것도 없다)
   target 을 돌려준다 (새 객체가 아니다)                    새 객체
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 물건을 꺼낸다 | 원본 키마다 `Get` — getter 를 **부른다** | 동작 (1)의 `get A.p` |
| 그 자리에 넣는다 | 대상에 `Set(to, key, value, true)` — setter 를 **부른다** | 동작 (1)의 `set target.q` |
| 문째 새로 짓는다 | 스프레드는 `CreateDataProperty` — 정의 | 동작 (1)의 `[3]` |
| 상자 안의 상자 | 중첩 객체 — **참조가 그대로 간다** | 동작 (2) 첫 행 |
| 잠긴 문에서 멈춘다 | `Set` 이 실패하면 `TypeError` · 앞서 쓴 키는 남는다 | 동작 (3)의 `[2]` |
| 붙박이 없는 창고 | `Object.groupBy` 의 결과 — `OrdinaryObjectCreate(null)` | 동작 (6)의 `[1]` |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**설정 객체를 `Object.assign({}, defaults, user)` 로 합쳤더니 중첩된 `db` 설정을 고친 것이 기본값까지 바꿨다**」와
「**`Object.freeze` 한 상태 객체에 `assign` 으로 덮어쓰려다 비엄격 코드에서도 `TypeError` 가 났고, 앞쪽 키만 바뀐 채 남았다**」가 그것이다(동작 (2)·(3)).

> **getter / setter** — 읽을 때 / 쓸 때 대신 불리는 함수가 달린 프로퍼티(접근자). 13번·14번이 정본이다.\
> 예: `{ get p() { return 1; } }` 의 `p`.

> **얕은 복사(shallow copy)** — 바깥 객체만 새로 만들고, 프로퍼티 값이 객체면 **그 참조를 그대로** 옮기는 복사.\
> 예: `Object.assign({}, { inner: x }).inner === x` 가 `true`.

## 이 주제가 답하려는 질문

1. **`Object.assign` 은 원본과 대상에게 무엇을 부르나** — 스프레드와는 어디서 갈리고, 도중에 실패하면 무엇이 남나?
2. **`keys`·`values`·`entries`·`fromEntries` 는 무엇을 세고 어떤 순서로 내나** — 심볼·비열거·체인의 키는?
3. **`Object.groupBy` 가 돌려주는 객체는 어떤 객체이고**, `Map.groupBy` 와 무엇이 다른가?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ `Object.assign` 의 호출 로그 — 이 주제의 본체

**언제 쓰나** — 설정 병합 · 기본값 채우기 · 「클래스 인스턴스에 필드를 한꺼번에 넣기」(`Object.assign(this, opts)`) 를 쓸 때.
★★★ 결과 객체만 찍어서는 스프레드와 구별이 안 된다. 그래서 **원본에 getter, 대상에 setter** 를 심었다.

```js
// js24b-27a-assign-log.js
// Object.assign(target, ...sources) -- which getters and setters run, and in what order?
const log = [];
const J = (x) => JSON.stringify(x);

const makeSource = (tag) => {
  const s = {};
  for (const k of ["p", "q"]) {
    Object.defineProperty(s, k, {
      get() { log.push("get " + tag + "." + k); return tag + k; },
      enumerable: true, configurable: true,
    });
  }
  Object.defineProperty(s, "hidden", {
    get() { log.push("get " + tag + ".hidden"); return 0; },
    enumerable: false,
  });
  s[Symbol("sym")] = tag + "sym";
  return s;
};
const makeTarget = () => {
  const t = {};
  let store = "initial";
  Object.defineProperty(t, "q", {
    get() { log.push("get target.q"); return store; },
    set(v) { log.push("set target.q <- " + v); store = v; },
    enumerable: true, configurable: true,
  });
  return t;
};

console.log("[1] one source, a target with a setter on q");
log.length = 0;
const t1 = makeTarget();
const r1 = Object.assign(t1, makeSource("A"));
console.log("  log                  " + J(log));
console.log("  returns the target?  " + (r1 === t1));
console.log("  own keys of target   " + J(Reflect.ownKeys(t1).map(String)));
console.log("  target.q descriptor  " + J(Object.keys(Object.getOwnPropertyDescriptor(t1, "q"))));
console.log("  target.p descriptor  " + J(Object.getOwnPropertyDescriptor(t1, "p")));

console.log("");
console.log("[2] two sources, left to right");
log.length = 0;
const t2 = makeTarget();
Object.assign(t2, makeSource("A"), makeSource("B"));
console.log("  log                  " + J(log));
log.length = 0;
console.log("  t2.p  t2.q           " + J([t2.p, t2.q]));

console.log("");
console.log("[3] the same source spread into an object literal (compare [1])");
log.length = 0;
const lit = { ...makeTarget(), ...makeSource("A") };
console.log("  log                  " + J(log));
console.log("  lit.q descriptor     " + J(Object.keys(Object.getOwnPropertyDescriptor(lit, "q"))));

console.log("");
console.log("[4] a source getter throws in the middle");
log.length = 0;
const t4 = {};
const bad = {
  get first() { log.push("get first"); return 1; },
  get second() { log.push("get second"); throw new Error("from getter"); },
  get third() { log.push("get third"); return 3; },
};
try { Object.assign(t4, bad); console.log("  no exception"); }
catch (e) { console.log("  " + e.constructor.name + " 「" + e.message + "」"); }
console.log("  log                  " + J(log));
console.log("  target afterwards    " + J(t4));

console.log("");
console.log("[5] sources that are not plain objects");
console.log("  null, undefined      " + J(Object.assign({}, null, undefined)));
console.log("  'ab'                 " + J(Object.assign({}, "ab")));
console.log("  5, true              " + J(Object.assign({}, 5, true)));
console.log("  [7, 8]               " + J(Object.assign({}, [7, 8])));
try { Object.assign(null, { a: 1 }); console.log("  target null: no exception"); }
catch (e) { console.log("  target null          " + e.constructor.name + " 「" + e.message + "」"); }
```
```text
===== node20 js24b-27a-assign-log.js (exit=0) =====
[1] one source, a target with a setter on q
  log                  ["get A.p","get A.q","set target.q <- Aq"]
  returns the target?  true
  own keys of target   ["q","p","Symbol(sym)"]
  target.q descriptor  ["get","set","enumerable","configurable"]
  target.p descriptor  {"value":"Ap","writable":true,"enumerable":true,"configurable":true}

[2] two sources, left to right
  log                  ["get A.p","get A.q","set target.q <- Aq","get B.p","get B.q","set target.q <- Bq"]
  t2.p  t2.q           ["Bp","Bq"]

[3] the same source spread into an object literal (compare [1])
  log                  ["get target.q","get A.p","get A.q"]
  lit.q descriptor     ["value","writable","enumerable","configurable"]

[4] a source getter throws in the middle
  Error 「from getter」
  log                  ["get first","get second"]
  target afterwards    {"first":1}

[5] sources that are not plain objects
  null, undefined      {}
  'ab'                 {"0":"a","1":"b"}
  5, true              {}
  [7, 8]               {"0":7,"1":8}
  target null          TypeError 「Cannot convert undefined or null to object」
```

```text
   Object.assign(t1, A)       A = { p(getter), q(getter), hidden(getter, 비열거), [sym] }
                              t1 = { q(getter+setter) }

   A 의 own 키:  p  q  hidden  Symbol(sym)
                 │  │    │        │
   열거 가능?     y  y    n        y
                 │  │    └ 건너뛴다 -- getter 도 안 부른다
                 ▼  ▼             ▼
   Get(A, k)     get A.p   get A.q          (심볼 값은 데이터라 로그가 없다)
   Set(t1,k,v)   t1.p 를 새로 만든다   set target.q <- Aq   t1[sym] 을 새로 만든다

   키 하나마다 「꺼내고 -> 넣고」 가 끝난 뒤 다음 키로 간다  (전부 꺼낸 뒤 한꺼번에 넣지 않는다)
```

- ★★★ **`[1]` 로그가 `["get A.p","get A.q","set target.q <- Aq"]`** 다. 원본 getter 는 **키마다 한 번**, 대상 setter 는 **그 키가 대상에 setter 로 있을 때** 불린다.
  ★ **`hidden`(비열거)의 getter 는 한 번도 안 불렸다** — 디스크립터를 먼저 보고 열거 불가면 **값을 읽지도 않는다.**
- ★★★ **대입 뒤에도 `target.q` 는 접근자 그대로다**(`["get","set","enumerable","configurable"]`). 값을 받은 것은 **setter 가 닫힌 변수**다.
  반면 대상에 없던 `p` 는 **보통 데이터 프로퍼티**로 생겼다(`writable/enumerable/configurable` 전부 `true`) — 원본의 getter 가 **값으로 굳었다.**
- ★★ **돌려주는 것은 대상 자신**이다(`returns the target? true`). 새 객체가 필요하면 첫 인자를 `{}` 로 준다.
- ★★ **심볼 키도 복사된다**(`own keys of target` 에 `Symbol(sym)`). 스프레드와 같다 — 13번 `[2]` 의 `Object.assign({}, o) keys` 줄이 이미 보였다.
- ★★★ **`[2]` 원본이 둘이면 왼쪽부터 원본 하나를 끝낸 뒤 다음 원본**이다. setter 가 **두 번** 불리고, 이긴 값은 **오른쪽**(`["Bp","Bq"]`)이다.
- ★★★ **`[3]` 스프레드의 로그에는 `set` 이 없다.** 첫 항목 `get target.q` 는 **스프레드가 `makeTarget()` 을 원본으로 읽은 것**이다 — 스프레드 앞자리 `...makeTarget()` 도 원본이기 때문이다.
  그리고 결과의 `q` 는 **데이터 프로퍼티**(`["value","writable",…]`)다. 11번 `[4]` 의 「setter 0회 대 1회」가 **이 로그의 한 줄**이다.
- ★★★ **`[4]` 도중에 던지면 거기서 멈추고, 앞서 쓴 키는 남는다** — `Error 「from getter」` 뒤 대상은 `{"first":1}` 이다. `third` 의 getter 는 **안 불렸다.**
- ★ **`[5]`** — `null`·`undefined` 원본은 **건너뛴다**(`{}`). 문자열은 **글자마다 인덱스 키**(`{"0":"a","1":"b"}`), 숫자·불리언은 own 키가 없어 `{}`, 배열은 인덱스 키다.
  **대상이 `null` 이면 `TypeError 「Cannot convert undefined or null to object」`** 다(대상은 `ToObject` 를 거친다).

### (2) ★★★ 복사 도구 넷 × 성질 여섯 — 전부 얕다

**언제 쓰나** — 「이 객체를 복사해 두고 고치자」 할 때 어느 도구를 쓸지 고를 때.

```js
// js24b-27b-copy-grid.js
// Four ways to copy an object -- what does each one keep? The script counts the cells.
const J = (x) => JSON.stringify(x);
const yn = (b) => (b ? "y" : "n");

class Point { constructor() { this.x = 1; } }
const make = () => {
  let reads = 0;
  const src = new Point();
  src.inner = { deep: 1 };
  Object.defineProperty(src, "counter", { get() { reads += 1; return reads; }, enumerable: true });
  Object.defineProperty(src, "hidden", { value: "h", enumerable: false });
  src[Symbol("tag")] = "s";
  return { src, reads: () => reads };
};

const tools = [
  ["Object.assign({}, src)", "assign", (s) => Object.assign({}, s)],
  ["{ ...src }", "spread", (s) => ({ ...s })],
  ["fromEntries(entries(src))", "entries", (s) => Object.fromEntries(Object.entries(s))],
  ["structuredClone(src)", "clone", (s) => structuredClone(s)],
];
const questions = [
  ["inner is the same object", (c, s) => c.inner === s.inner],
  ["counter is still a getter", (c) => typeof Object.getOwnPropertyDescriptor(c, "counter")?.get === "function"],
  ["symbol key copied", (c) => Object.getOwnPropertySymbols(c).length === 1],
  ["non-enumerable key copied", (c) => Object.hasOwn(c, "hidden")],
  ["prototype is Point.prototype", (c) => Object.getPrototypeOf(c) === Point.prototype],
  ["copy !== src", (c, s) => c !== s],
];

console.log("[1] grid -- y/n per cell");
console.log(("  " + "".padEnd(30) + tools.map(([, c]) => c.padEnd(8)).join(" ")).trimEnd());
const table = questions.map(([q, test]) => tools.map(([, , f]) => {
  const { src } = make();
  return test(f(src), src);
}));
questions.forEach(([q], i) => console.log(("  " + q.padEnd(30) + table[i].map((b) => yn(b).padEnd(8)).join(" ")).trimEnd()));

console.log("");
console.log("[2] how many times was the getter read during the copy?");
for (const [n, , f] of tools) {
  const { src, reads } = make();
  f(src);
  console.log("  " + n.padEnd(30) + reads());
}

console.log("");
console.log("[3] writing through the copy");
const { src } = make();
const shallow = Object.assign({}, src);
shallow.inner.deep = 99;
shallow.x = 2;
console.log("  src.inner.deep  " + src.inner.deep);
console.log("  src.x           " + src.x);

let differ = 0, total = 0;
for (const row of table) for (let j = 1; j < row.length; j++) { total += 1; if (row[j] !== row[0]) differ += 1; }
console.log("");
console.log("cells whose answer differs from the Object.assign column: " + differ + " / " + total);
```
```text
===== node20 js24b-27b-copy-grid.js (exit=0) =====
[1] grid -- y/n per cell
                                assign   spread   entries  clone
  inner is the same object      y        y        y        n
  counter is still a getter     n        n        n        n
  symbol key copied             y        y        n        n
  non-enumerable key copied     n        n        n        n
  prototype is Point.prototype  n        n        n        n
  copy !== src                  y        y        y        y

[2] how many times was the getter read during the copy?
  Object.assign({}, src)        1
  { ...src }                    1
  fromEntries(entries(src))     1
  structuredClone(src)          1

[3] writing through the copy
  src.inner.deep  99
  src.x           1

cells whose answer differs from the Object.assign column: 3 / 18
```

```text
   src = Point { x: 1, inner: {deep:1}, counter(getter), hidden(비열거), [Symbol(tag)] }

                         assign   spread   entries  clone
   inner 공유              y        y        y        n      <- clone 만 안쪽까지 새로 만든다
   getter 유지             n        n        n        n      <- 넷 다 「값」으로 굳힌다
   심볼 키                  y        y        n        n      <- entries 는 글자 키만 센다
   비열거 키                n        n        n        n
   Point.prototype 유지    n        n        n        n      <- 넷 다 평범한 객체가 된다
   copy !== src            y        y        y        y      <- (대조용 행)
```

- ★★★ **집계 줄 — `cells whose answer differs from the Object.assign column: 3 / 18`.** `assign` 과 **완전히 같은 열은 스프레드**(0칸)다.
  `entries` 열은 **심볼 행 하나**, `clone` 열은 **`inner` 행과 심볼 행 둘**이 갈린다.
- ★★★ **첫 행 — `assign`·스프레드·`fromEntries(entries())` 는 전부 `inner` 를 공유한다.** 바깥만 새 객체다. `[3]` 이 그 결과다 —
  복사본에서 `shallow.inner.deep = 99` 를 하면 **원본의 `src.inner.deep` 도 `99`** 이고, 바깥 키 `x` 를 고친 것은 원본에 안 간다(`src.x 1`).
- ★★ **둘째 행 — getter 를 getter 째 옮기는 도구는 넷 중에 없다.** `[2]` 에서 넷 다 **복사하는 동안 한 번 읽었다**(`1`). 옮기고 싶으면 `Object.defineProperties({}, Object.getOwnPropertyDescriptors(src))` 쪽이다(이 문서는 격자에 넣지 않았다).
- ★★ **셋째 행 — `Object.entries` 는 심볼 키를 안 센다.** 그래서 `fromEntries(entries(src))` 왕복은 **심볼을 잃는다**(동작 (4)).
- ★★ **다섯째 행 — 넷 다 프로토타입을 잃는다.** `Point` 인스턴스를 복사하면 **평범한 객체**가 나온다. `structuredClone` 도 마찬가지다.
- ★ **`structuredClone` 은 ECMA-262 가 아니라 호스트 API** 다(HTML 표준 — 이 판의 node 20 에는 전역으로 있다). 깊은 복사 수단의 비교는 [목록의 **48번 주제**](../48-deep-copy-methods-compared/)가 정본이라 여기서는 **한 열**로만 둔다.

### (3) ★★★ 쓰기를 거부하는 대상 — 비엄격에서도 던지고, 되돌리지 않는다

**언제 쓰나** — 얼린 객체(`Object.freeze`)나 읽기 전용 프로퍼티가 있는 객체를 `assign` 의 **대상**으로 쓸 때.

```js
// js24b-27c-readonly-target.js
// Object.assign into a target that refuses some writes -- in sloppy and in strict code.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { f(); console.log("  " + label.padEnd(42) + "no exception"); }
  catch (e) { console.log("  " + label.padEnd(42) + e.constructor.name + " 「" + e.message + "」"); }
};

function sloppyAssign(t, s) { return Object.assign(t, s); }
function sloppyWrite(t) { t.a = 2; }
function strictAssign(t, s) { "use strict"; return Object.assign(t, s); }
function strictWrite(t) { "use strict"; t.a = 2; }

console.log("[1] a frozen target");
show("sloppy   Object.assign(frozen, { a: 2 })", () => sloppyAssign(Object.freeze({ a: 1 }), { a: 2 }));
show("sloppy   frozen.a = 2", () => sloppyWrite(Object.freeze({ a: 1 })));
show("strict   Object.assign(frozen, { a: 2 })", () => strictAssign(Object.freeze({ a: 1 }), { a: 2 }));
show("strict   frozen.a = 2", () => strictWrite(Object.freeze({ a: 1 })));

console.log("");
console.log("[2] the target has one read-only key, b -- the source writes a, b, c");
const t = {};
Object.defineProperty(t, "b", { value: "old", writable: false, enumerable: true });
show("Object.assign(t, { a: 1, b: 2, c: 3 })", () => strictAssign(t, { a: 1, b: 2, c: 3 }));
console.log("  t afterwards                              " + J(t));

console.log("");
console.log("[3] a frozen source, an ordinary target");
const fs = Object.freeze({ a: 1, inner: { deep: 1 } });
const copy = Object.assign({}, fs);
copy.a = 2;
copy.inner.deep = 2;
console.log("  copy is frozen?     " + Object.isFrozen(copy));
console.log("  fs.a  fs.inner.deep " + J([fs.a, fs.inner.deep]));
```
```text
===== node20 js24b-27c-readonly-target.js (exit=0) =====
[1] a frozen target
  sloppy   Object.assign(frozen, { a: 2 })  TypeError 「Cannot assign to read only property 'a' of object '#<Object>'」
  sloppy   frozen.a = 2                     no exception
  strict   Object.assign(frozen, { a: 2 })  TypeError 「Cannot assign to read only property 'a' of object '#<Object>'」
  strict   frozen.a = 2                     TypeError 「Cannot assign to read only property 'a' of object '#<Object>'」

[2] the target has one read-only key, b -- the source writes a, b, c
  Object.assign(t, { a: 1, b: 2, c: 3 })    TypeError 「Cannot assign to read only property 'b' of object '#<Object>'」
  t afterwards                              {"b":"old","a":1}

[3] a frozen source, an ordinary target
  copy is frozen?     false
  fs.a  fs.inner.deep [1,2]
```

```text
   Object.assign(t, { a: 1, b: 2, c: 3 })     t 에는 b 가 읽기 전용("old")

   a :  Set(t, "a", 1, true)   -> 된다         t = { b:"old", a:1 }
   b :  Set(t, "b", 2, true)   -> 실패 -> throw 가 true 라서 TypeError
   c :  (여기까지 안 온다)

   ★ 네 번째 인자 true = 「실패하면 던져라」
       t.a = 2 (비엄격)   ->  같은 Set 을 throw = false 로 부른다  -> 조용히 실패
       t.a = 2 (엄격)     ->  throw = true                        -> TypeError
       Object.assign     ->  어느 모드에서 불러도 true
```

- ★★★ **`[1]` 비엄격 함수 안에서도 `Object.assign(frozen, …)` 은 `TypeError` 다.** 같은 함수 안의 `frozen.a = 2` 는 **조용히 무시**된다(`no exception`).
  ★ 명세 `Object.assign` 이 키마다 **`Set(to, nextKey, propValue, true)`** 를 부른다 — 마지막 인자가 「실패하면 던져라」이고, **호출한 코드의 모드와 상관없이 늘 `true`** 다.
  엄격 모드에서는 둘이 **같은 문구**로 던진다 — `Cannot assign to read only property 'a' of object '#<Object>'`. 동결이 대입을 막는 것 자체는 14번의 격자가 정본이다.
- ★★★ **`[2]` 도중에 던지면 앞의 키는 남는다** — `a` 는 들어갔고(`{"b":"old","a":1}`), `c` 는 **시도조차 안 됐다.**
  **`assign` 은 원자적(atomic)이 아니다** — 알고리즘에 **되돌리는 단계가 없다.** 동작 (1)의 `[4]`(원본 쪽 getter 가 던진 경우)와 같은 모양이다.
- ★★ **`[3]` 얼린 원본을 복사하면 복사본은 안 얼어 있다**(`copy is frozen? false`). 그리고 **동결이 얕으므로** 복사본을 거쳐 `inner.deep` 을 고치면 **원본의 것이 바뀐다**(`[1,2]`) —
  원본 `fs` 가 얼어 있는데도. 동결의 얕음(14번)과 복사의 얕음(동작 (2))이 **겹친 자리**다.

### (4) ★★★ `keys`·`values`·`entries` — 무엇을 묻고 어떤 순서로 내나

**언제 쓰나** — 객체를 배열로 바꿔 `map`/`filter` 를 쓸 때(동작 (5)의 왕복) · 순서에 기대는 출력을 만들 때.

```js
// js24b-27d-keys-values-entries.js
// Object.keys / values / entries -- order, what they ask the object, and what a getter can change mid-way.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(30) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(30) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] order -- keys inserted as b, 2, a, 1, Symbol");
const o = {};
o.b = "B"; o[2] = "two"; o.a = "A"; o[1] = "one"; o[Symbol("s")] = "S";
show("Object.keys", () => Object.keys(o));
show("Object.values", () => Object.values(o));
show("Object.entries", () => Object.entries(o));
show("Reflect.ownKeys", () => Reflect.ownKeys(o).map(String));

console.log("");
console.log("[2] what each one asks a Proxy (two keys, one of them non-enumerable)");
const target = {};
Object.defineProperty(target, "x", { value: 1, enumerable: true, configurable: true });
Object.defineProperty(target, "y", { value: 2, enumerable: false, configurable: true });
const log = [];
const traced = new Proxy(target, {
  ownKeys(t) { log.push("ownKeys"); return Reflect.ownKeys(t); },
  getOwnPropertyDescriptor(t, k) { log.push("gopd " + String(k)); return Reflect.getOwnPropertyDescriptor(t, k); },
  get(t, k, r) { log.push("get " + String(k)); return Reflect.get(t, k, r); },
});
for (const [n, f] of [["keys", Object.keys], ["values", Object.values], ["entries", Object.entries]]) {
  log.length = 0;
  f(traced);
  console.log("  " + n.padEnd(10) + J(log));
}

console.log("");
console.log("[3] a getter that deletes a later key and adds a new one");
const m = {
  get first() { delete this.second; this.added = "new"; return "F"; },
  second: "S",
  third: "T",
};
show("Object.entries(m)", () => Object.entries(m));
show("Object.keys(m) afterwards", () => Object.keys(m));

console.log("");
console.log("[4] non-objects");
show("Object.keys('ab')", () => Object.keys("ab"));
show("Object.entries(5)", () => Object.entries(5));
show("Object.values([7, , 9])", () => Object.values([7, , 9]));
show("Object.keys(null)", () => Object.keys(null));
```
```text
===== node20 js24b-27d-keys-values-entries.js (exit=0) =====
[1] order -- keys inserted as b, 2, a, 1, Symbol
  Object.keys                   ["1","2","b","a"]
  Object.values                 ["one","two","B","A"]
  Object.entries                [["1","one"],["2","two"],["b","B"],["a","A"]]
  Reflect.ownKeys               ["1","2","b","a","Symbol(s)"]

[2] what each one asks a Proxy (two keys, one of them non-enumerable)
  keys      ["ownKeys","gopd x","gopd y"]
  values    ["ownKeys","gopd x","get x","gopd y"]
  entries   ["ownKeys","gopd x","get x","gopd y"]

[3] a getter that deletes a later key and adds a new one
  Object.entries(m)             [["first","F"],["third","T"]]
  Object.keys(m) afterwards     ["first","third","added"]

[4] non-objects
  Object.keys('ab')             ["0","1"]
  Object.entries(5)             []
  Object.values([7, , 9])       [7,9]
  Object.keys(null)             TypeError 「Cannot convert undefined or null to object」
```

```text
   EnumerableOwnProperties(O, kind)       kind = key | value | key+value

   ownKeys = O.[[OwnPropertyKeys]]()      <- ① 목록을 먼저 한 번에 받는다 (정수 키 -> 글자 키 -> 심볼 순)
   목록의 키마다
     심볼이면 건너뛴다                       <- 디스크립터도 안 묻는다
     desc = O.[[GetOwnProperty]](key)      <- ② 지금 이 순간의 디스크립터 (지워졌으면 undefined -> 건너뛴다)
     열거 가능하면
        key 만   -> 키를 담는다              (keys    : get 을 안 부른다)
        아니면   -> Get(O, key)             (values · entries : 여기서 getter 가 돈다)
```

- ★★★ **`[1]` 넣은 순서가 `b, 2, a, 1` 이어도 셋 다 `1, 2, b, a`** 다 — **정수 키 오름차순 → 글자 키 삽입순.** 13번의 열거 순서 규칙을 **그대로** 따른다(정본은 13번).
  ★ 심볼은 **`Reflect.ownKeys` 에만** 나온다. `keys`·`values`·`entries` 는 알고리즘이 **심볼이면 건너뛰는** 단계를 가진다 — 22번의 「글자 이름표만 세는 도구」가 이 셋이다.
- ★★★ **`[2]` `keys` 는 `get` 을 한 번도 안 부른다** — `["ownKeys","gopd x","gopd y"]`. `values`·`entries` 는 **열거 가능한 `x` 에만** `get` 을 부른다. 비열거 `y` 는 디스크립터만 묻고 **값은 안 읽는다.**
  ★ 18번이 `for...in` 쪽 트랩을 쟀다 — 거기는 체인까지 올라가 `getPrototypeOf` 가 섞인다. 여기 셋은 **자기 칸만** 본다.
- ★★★ **`[3]` 키 목록은 처음에 한 번 받아 두고, 키마다 디스크립터를 다시 묻는다.**
  그래서 getter 가 도중에 **지운 `second` 는 빠지고**(그 순간 디스크립터가 없다), **새로 넣은 `added` 는 안 나온다**(처음 목록에 없었다) — 결과 `[["first","F"],["third","T"]]`.
  `added` 는 실제로 들어가 있다(`Object.keys(m) afterwards` 의 셋째 칸).
- ★ **`[4]` 원시값은 `ToObject` 를 거친다** — `'ab'` 는 `["0","1"]`, `5` 는 `[]`. **구멍은 건너뛴다**(`[7, , 9]` → `[7,9]` — 구멍에는 own 프로퍼티가 없다. 배열 구멍 전체는 26번).
  `null` 은 `TypeError 「Cannot convert undefined or null to object」`(18번이 `Object.keys(null)` 으로 같은 문구를 찍었다).

### (5) ★★ `Object.fromEntries` — 받는 것, 키가 되는 것, `Map` 왕복

**언제 쓰나** — `Object.entries(o).map(…)` 로 바꾼 쌍을 다시 객체로 · `Map` 을 JSON 으로 내보낼 때.

```js
// js24b-27e-fromentries.js
// Object.fromEntries -- what it accepts, what the keys become, and a round trip through a Map.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(40) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(40) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] inputs");
show("fromEntries([['a', 1], ['b', 2]])", () => Object.fromEntries([["a", 1], ["b", 2]]));
show("fromEntries(new Map([['a', 1]]))", () => Object.fromEntries(new Map([["a", 1]])));
show("fromEntries([['k', 1], ['k', 2]])", () => Object.fromEntries([["k", 1], ["k", 2]]));
show("fromEntries([['a']])  keys, String(a)", () => { const r = Object.fromEntries([["a"]]); return [Object.keys(r), String(r.a)]; });
show("fromEntries(['ab'])", () => Object.fromEntries(["ab"]));
show("fromEntries([1])", () => Object.fromEntries([1]));
show("fromEntries({ a: 1 })", () => Object.fromEntries({ a: 1 }));

console.log("");
console.log("[2] Map -> object -> Map");
const key = { id: 1 };
const map = new Map([[1, "number one"], ["1", "string one"], [key, "object"], [true, "bool"]]);
const obj = Object.fromEntries(map);
console.log("  map.size                  " + map.size);
console.log("  Object.keys(obj)          " + J(Object.keys(obj)));
console.log("  obj['1']                  " + J(obj["1"]));
const back = new Map(Object.entries(obj));
console.log("  back.size                 " + back.size);
console.log("  back.get(1)               " + String(back.get(1)));
console.log("  back.get('1')             " + String(back.get("1")));
console.log("  back.get(key)             " + String(back.get(key)));

console.log("");
console.log("[3] object -> entries -> transform -> object");
const prices = { apple: 3, pear: 5 };
const doubled = Object.fromEntries(Object.entries(prices).map(([k, v]) => [k, v * 2]));
console.log("  doubled                   " + J(doubled));

console.log("");
console.log("[4] the key \"__proto__\" -- fromEntries and assign side by side");
const pair = JSON.parse('{"__proto__": {"marker": true}}');
console.log("  own keys of the JSON source       " + J(Object.keys(pair)));
const viaEntries = Object.fromEntries([["__proto__", { marker: true }]]);
const viaAssign = Object.assign({}, pair);
for (const [n, r] of [["fromEntries", viaEntries], ["Object.assign", viaAssign]]) {
  console.log("  " + n.padEnd(14) + "own keys " + J(Object.keys(r)).padEnd(15) +
    "marker " + String(r.marker).padEnd(10) + "prototype changed " + (Object.getPrototypeOf(r) !== Object.prototype));
}
```
```text
===== node20 js24b-27e-fromentries.js (exit=0) =====
[1] inputs
  fromEntries([['a', 1], ['b', 2]])       {"a":1,"b":2}
  fromEntries(new Map([['a', 1]]))        {"a":1}
  fromEntries([['k', 1], ['k', 2]])       {"k":2}
  fromEntries([['a']])  keys, String(a)   [["a"],"undefined"]
  fromEntries(['ab'])                     TypeError 「Iterator value ab is not an entry object」
  fromEntries([1])                        TypeError 「Iterator value 1 is not an entry object」
  fromEntries({ a: 1 })                   TypeError 「object is not iterable (cannot read property Symbol(Symbol.iterator))」

[2] Map -> object -> Map
  map.size                  4
  Object.keys(obj)          ["1","[object Object]","true"]
  obj['1']                  "string one"
  back.size                 3
  back.get(1)               undefined
  back.get('1')             string one
  back.get(key)             undefined

[3] object -> entries -> transform -> object
  doubled                   {"apple":6,"pear":10}

[4] the key "__proto__" -- fromEntries and assign side by side
  own keys of the JSON source       ["__proto__"]
  fromEntries   own keys ["__proto__"]  marker undefined prototype changed false
  Object.assign own keys []             marker true      prototype changed true
```

```text
   Map { 1 -> "number one", "1" -> "string one", {id:1} -> "object", true -> "bool" }     size 4
          │                   │                    │                   │
   ToPropertyKey            "1"                 "1"            "[object Object]"         "true"
          └─────── 같은 칸 ───┘  (나중 것이 이긴다)
                                         ▼
   { "1": "string one", "[object Object]": "object", "true": "bool" }                       키 3개
                                         ▼  new Map(Object.entries(obj))
   Map { "1" -> …, "[object Object]" -> …, "true" -> … }     size 3 · get(1) 은 undefined
```

- ★★★ **`[2]` `Map` → 객체 → `Map` 은 되돌아오지 않는다.** `size 4` 가 `size 3` 이 됐다 — `1` 과 `"1"` 이 **한 칸**으로 합쳐졌고(나중 값 `"string one"`), 객체 키는 `"[object Object]"` 라는 **글자**가 됐다.
  되돌린 `Map` 에서 `get(1)` 은 **`undefined`**(키가 이제 문자열 `"1"`), `get(key)` 도 `undefined` 다. 「`Map` 은 정체로, 객체는 글자로」는 23번 동작 (3)이 정본이다.
- ★★ **`[1]` 입력은 「쌍의 이터러블」이다** — 배열의 배열도 `Map` 도 된다. 같은 키가 두 번이면 **나중 것**(`{"k":2}`), 쌍의 둘째가 없으면 값이 `undefined` 다.
  원소가 객체가 아니면 **`TypeError 「Iterator value ab is not an entry object」`** — 문자열 `'ab'` 도 **쌍으로 안 쳐 준다.** 평범한 객체 `{ a: 1 }` 은 이터러블이 아니라 `TypeError`(19번의 프로토콜).
- ★★ **`[3]` 「객체 → `entries` → `map` → `fromEntries`」** 가 객체에 배열 메서드를 쓰는 표준 경로다. 결과는 **새 객체**다.
- ★★★ **`[4]` `"__proto__"` 라는 키가 둘에서 갈린다.**
  `fromEntries` 는 **자기 키**로 만든다(`own keys ["__proto__"]`, 프로토타입 그대로) — 명세가 `CreateDataPropertyOrThrow` 로 **정의**하기 때문이다.
  `Object.assign` 은 **대입**이라 `Object.prototype` 의 `__proto__` setter 를 불러 **프로토타입을 바꾼다**(`own keys []`, `marker true`). 원본은 `JSON.parse` 가 만든 **자기 키 `"__proto__"`** 였다.
  ★ **「정의 대 대입」이 동작 (1)의 setter 에 이어 여기서 한 번 더** 갈린다. 23번 동작 (3)의 `[4]` 가 같은 접근자를 평범한 대입으로 보였다.

### (6) ★★★ `Object.groupBy`(ES2024) — 붙박이 없는 창고, 그리고 `Map.groupBy`

**언제 쓰나** — 배열을 종류별로 나눌 때(`reduce` 로 손으로 짜던 것). ★ **두 node 판에 없다** — Chrome 151 로 돌렸다.

```js
// js24b-27f-groupby.web.js
// Object.groupBy and Map.groupBy -- what comes back, and what the callback sees.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(42) + f()); }
  catch (e) { console.log("  " + label.padEnd(42) + e.constructor.name + " 「" + e.message + "」"); }
};
const items = [
  { name: "a", kind: "fruit", n: 3 },
  { name: "b", kind: "herb", n: 10 },
  { name: "c", kind: "fruit", n: 2 },
];

console.log("[1] Object.groupBy -- the returned object");
const g = Object.groupBy(items, (it) => it.kind);
show("JSON.stringify", () => J(g));
show("Object.getPrototypeOf(g) === null", () => Object.getPrototypeOf(g) === null);
show("'toString' in g", () => "toString" in g);
show("g.toString()", () => g.toString());
show("String(g)", () => String(g));
show("`${g}`", () => `${g}`);
show("Object.prototype.toString.call(g)", () => Object.prototype.toString.call(g));
show("g.fruit[0] === items[0]", () => g.fruit[0] === items[0]);
show("Array.isArray(g.fruit)", () => Array.isArray(g.fruit));
show("g.vegetable", () => String(g.vegetable));

console.log("");
console.log("[2] the callback -- arguments and call count");
const calls = [];
Object.groupBy(["x", "y", "z"], (v, i, ...rest) => { calls.push([v, i, rest.length]); return "k"; });
show("calls", () => J(calls));

console.log("");
console.log("[3] the keys -- returned values of different types");
const byType = Object.groupBy([1, 2, 3, 4], (n) => [n % 2, "odd", { id: 1 }, true][n - 1]);
show("Object.keys", () => J(Object.keys(byType)));
const numeric = Object.groupBy(["p", "q", "r"], (v) => ({ p: "z", q: "10", r: "2" })[v]);
show("keys for 'z', '10', '2' (in that order)", () => J(Object.keys(numeric)));

console.log("");
console.log("[4] Map.groupBy on the same kind of input");
const k1 = { id: 1 };
const k2 = { id: 1 };
const mg = Map.groupBy([1, 2, 3, 4, 5], (n) => [k1, k2, k1, -0, 0][n - 1]);
show("mg instanceof Map", () => mg instanceof Map);
show("mg.size", () => mg.size);
show("mg.get(k1)", () => J(mg.get(k1)));
show("mg.get(k2)", () => J(mg.get(k2)));
show("mg.get({ id: 1 })", () => String(mg.get({ id: 1 })));
show("mg.get(0)", () => J(mg.get(0)));
show("Object.is(zero key, -0)", () => Object.is([...mg.keys()][2], -0));

console.log("");
console.log("[5] inputs that are not arrays");
show("Object.groupBy(new Set([1, 2, 3]))", () => J(Object.groupBy(new Set([1, 2, 3]), (n) => (n > 1 ? "big" : "small"))));
show("Object.groupBy('aba')", () => J(Object.groupBy("aba", (ch) => ch)));
show("Object.groupBy({ length: 2 })", () => J(Object.groupBy({ length: 2, 0: "a", 1: "b" }, (v) => v)));
show("typeof [].groupBy", () => typeof [].groupBy);

console.log("");
console.log("[6] group keys named like Object.prototype members -- a hand-written version into {} and groupBy");
const words = ["toString", "__proto__", "plain"];
const byHand = (list) => {
  const acc = {};
  for (const w of list) (acc[w] ??= []).push(w);
  return acc;
};
for (const w of words) {
  show("by hand into {}   key " + J(w), () => J(Object.keys(byHand([w]))));
  show("Object.groupBy    key " + J(w), () => J(Object.keys(Object.groupBy([w], (x) => x))));
}
```
```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js24b-page.html?js24b-27f-groupby.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] Object.groupBy -- the returned object
  JSON.stringify                            {"fruit":[{"name":"a","kind":"fruit","n":3},{"name":"c","kind":"fruit","n":2}],"herb":[{"name":"b","kind":"herb","n":10}]}
  Object.getPrototypeOf(g) === null         true
  'toString' in g                           false
  g.toString()                              TypeError 「g.toString is not a function」
  String(g)                                 TypeError 「Cannot convert object to primitive value」
  `${g}`                                    TypeError 「Cannot convert object to primitive value」
  Object.prototype.toString.call(g)         [object Object]
  g.fruit[0] === items[0]                   true
  Array.isArray(g.fruit)                    true
  g.vegetable                               undefined

[2] the callback -- arguments and call count
  calls                                     [["x",0,0],["y",1,0],["z",2,0]]

[3] the keys -- returned values of different types
  Object.keys                               ["1","odd","[object Object]","true"]
  keys for 'z', '10', '2' (in that order)   ["2","10","z"]

[4] Map.groupBy on the same kind of input
  mg instanceof Map                         true
  mg.size                                   3
  mg.get(k1)                                [1,3]
  mg.get(k2)                                [2]
  mg.get({ id: 1 })                         undefined
  mg.get(0)                                 [4,5]
  Object.is(zero key, -0)                   false

[5] inputs that are not arrays
  Object.groupBy(new Set([1, 2, 3]))        {"small":[1],"big":[2,3]}
  Object.groupBy('aba')                     {"a":["a","a"],"b":["b"]}
  Object.groupBy({ length: 2 })             TypeError 「object is not iterable (cannot read property Symbol(Symbol.iterator))」
  typeof [].groupBy                         undefined

[6] group keys named like Object.prototype members -- a hand-written version into {} and groupBy
  by hand into {}   key "toString"          TypeError 「acc[w].push is not a function」
  Object.groupBy    key "toString"          ["toString"]
  by hand into {}   key "__proto__"         TypeError 「acc[w].push is not a function」
  Object.groupBy    key "__proto__"         ["__proto__"]
  by hand into {}   key "plain"             ["plain"]
  Object.groupBy    key "plain"             ["plain"]
```

```text
   Object.groupBy(items, cb)                            Map.groupBy(items, cb)

   GroupBy(items, cb, property)                         GroupBy(items, cb, collection)
     items 를 이터레이터로 돈다 (배열만이 아니다)             같다
     key = cb(value, index)                              같다
     key = ToPropertyKey(key)   <- 글자로                  key = CanonicalizeKeyedCollectionKey(key)  <- -0 만 +0 으로
   obj = OrdinaryObjectCreate(null)  <- 프로토타입 없음     new Map
   묶음마다 obj[key] = 새 배열                             map.set(key, 새 배열)
```

- ★★★ **`[1]` 결과의 프로토타입은 `null` 이다**(`true`). 그래서 **`'toString' in g` 가 `false`**, `g.toString()` 은 **`TypeError 「g.toString is not a function」`**,
  `String(g)` 와 템플릿 리터럴은 **`TypeError 「Cannot convert object to primitive value」`** 다.
  ★ **15번의 `Object.create(null)` 블록이 `String(bare)` 와 `` `${bare}` `` 에서 한 글자도 같은 문구**를 찍었다 — 결과 객체가 **그것과 같은 종류의 객체**다.
  브랜드 태그 `Object.prototype.toString.call(g)` 만 `[object Object]` 라고 답한다(15번에서 쓴 창 그대로).
  명세 note 가 그대로 적는다 — "The return value of groupBy is an object that does not inherit from %Object.prototype%."
- ★★ **묶음 값은 새 배열이고, 원소는 원본 그대로**다(`Array.isArray` true · `g.fruit[0] === items[0]` true) — **원소는 복사되지 않는다.** 없는 묶음은 `undefined`.
- ★★ **`[2]` 콜백은 원소마다 한 번, 인자는 `(값, 인덱스)` 둘**이다(`rest.length` 가 `0` — 배열 메서드처럼 셋째 인자로 배열을 주지 않는다). 입력이 **이터러블**이라 줄 배열이 없다.
- ★★★ **`[3]` 키는 `ToPropertyKey` 를 거친다** — `1` 은 `"1"`, `{ id: 1 }` 은 `"[object Object]"`, `true` 는 `"true"`.
  ★★★ **그리고 결과는 평범한 객체라 13번의 순서를 따른다** — `'z'`, `'10'`, `'2'` 순으로 만들어도 `["2","10","z"]` 다. **묶음이 생긴 순서가 아니다.**
- ★★★ **`[4]` `Map.groupBy` 는 키를 정체로 본다** — 모양이 같은 `k1`·`k2` 가 **두 칸**(`size 3`), 새로 만든 `{ id: 1 }` 로는 못 찾는다. `-0` 과 `0` 은 **한 칸**이고 **남은 키는 `+0`** 이다(`Object.is(zero key, -0)` false) — 23번 동작 (2)의 접기와 같다.
- ★★ **`[5]` 입력은 이터러블이면 된다** — `Set`·문자열이 된다. **유사 배열(`{ length: 2 }`)은 `TypeError`** 다(`Array.from` 은 유사 배열도 연다 — 11번이 쟀고 19번이 인용했다). `[].groupBy` 는 **없다**(`undefined`) — 배열 메서드가 아니라 **`Object`·`Map` 의 정적 메서드**다.
- ★★★ **`[6]` 붙박이가 없어서 생기는 차이** — `{}` 에 손으로 모으는 `(acc[w] ??= []).push(w)` 는 키가 `"toString"` · `"__proto__"` 일 때 **`TypeError 「acc[w].push is not a function」`** 다.
  `acc.toString` 은 **물려받은 함수**, `acc.__proto__` 는 **`Object.prototype` 자체**라 `??=` 가 「이미 있다」고 본다. `Object.groupBy` 는 둘 다 **자기 키**로 만든다.
  ★ **명세가 결과를 null 프로토타입으로 만드는 이유가 이 한 블록**이다.

### (7) ★★ 병합에서 자리와 값 — 파이썬 `dict` 와의 대비

**언제 쓰나** — 파이썬의 `a | b` 습관으로 `Object.assign`·스프레드 병합의 결과를 예상할 때.

```js
// js24b-27g-merge-order.js
// Merging two objects -- which position and which value does a shared key end up with?
const J = (x) => JSON.stringify(x);
const a = { x: 1, y: 2 };
const b = { y: 20, z: 30 };
console.log("Object.assign({}, a, b)   " + J(Object.assign({}, a, b)));
console.log("Object.assign({}, b, a)   " + J(Object.assign({}, b, a)));
console.log("{ ...b, ...a }            " + J({ ...b, ...a }));
console.log("a afterwards              " + J(a));
const words = { b: 1 };
const numbers = { 2: "two", 1: "one" };
console.log("Object.assign({}, words, numbers)  keys " + J(Object.keys(Object.assign({}, words, numbers))));
```
```text
===== node20 js24b-27g-merge-order.js (exit=0) =====
Object.assign({}, a, b)   {"x":1,"y":20,"z":30}
Object.assign({}, b, a)   {"y":2,"z":30,"x":1}
{ ...b, ...a }            {"y":2,"z":30,"x":1}
a afterwards              {"x":1,"y":2}
Object.assign({}, words, numbers)  keys ["1","2","b"]
```

파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번**이 `dict` 병합을 실측했다 — 그 문서의 출력만 인용한다.

```text
   b = { y:20, z:30 }  ·  a = { x:1, y:2 }

   Python  b | a               ->  {'y': 2, 'z': 30, 'x': 1}      (12번의 출력)
   JS      Object.assign({}, b, a)  ->  {"y":2,"z":30,"x":1}     (위 블록)

   자리  <- 먼저 들어간 쪽(b)의 것 :  y 가 0번 자리
   값    <- 나중 쪽(a)이 이긴다      :  y 는 2
```

| 무엇 | 파이썬 `dict` (12번의 출력) | JS 객체 (이 문서) | 왜 |
|---|---|---|---|
| 겹친 키의 자리와 값 | 자리는 왼쪽, 값은 오른쪽 — `{'y': 2, 'z': 30, 'x': 1}` | **같다** — `{"y":2,"z":30,"x":1}` | 둘 다 「지우고 넣기」가 아니라 **덮어쓰기**다 |
| 원본 | `a 는 그대로` | `a afterwards` 가 그대로 | 첫 인자 `{}` 가 대상이라서 — 대상을 `a` 로 주면 `a` 가 바뀐다(동작 (1)) |
| 정수처럼 생긴 키 | **넣은 순서 그대로**(3.7 부터 언어 보장) | ★★★ **정수 키가 앞으로 간다** — `["1","2","b"]` | JS 객체의 own 키 순서 규칙(13번) · 파이썬 `dict` 는 키 종류로 줄을 안 가른다 |
| 이터러블을 오른쪽에 | `a \| [("k", 9)]` 는 `TypeError` | `Object.assign({}, [7, 8])` 은 **인덱스 키로 들어간다** | JS 는 원본을 `ToObject` 해 own 키를 읽을 뿐이다(동작 (1)의 `[5]`) |

- ★★★ **「자리는 먼저, 값은 나중」은 두 언어가 같다.** 갈리는 것은 **정수 키** — JS 는 병합 결과조차 `1, 2` 를 글자 키 앞에 세운다.
- ★ **파이썬 쪽은 이 배치에서 다시 돌리지 않았다** — 12번 문서에 실린 출력을 인용했다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28 — 돌리지 않은 코드 펜스를 싣지 않는다).

| 형태 | 돌려주는 것 | 판 | 어디서 봤나 |
|---|---|---|---|
| `Object.assign(target, ...sources)` | **`target` 자신** — 열거 가능한 own 키(심볼 포함)를 **대입** | ES2015 | 동작 (1) |
| `Object.keys(o)` · `Object.values(o)` · `Object.entries(o)` | 새 배열 — **열거 가능한 own 글자 키**만, 13번의 순서 | ES5 · ES2017 | 동작 (4) |
| `Object.fromEntries(iterable)` | 새 객체 — 쌍마다 키를 **정의** | ES2019 | 동작 (5) |
| `Object.groupBy(iterable, cb)` | **프로토타입이 `null` 인** 새 객체 — 값은 새 배열 | **ES2024** | 동작 (6) |
| `Map.groupBy(iterable, cb)` | 새 `Map` — 키는 정체로(`-0` 은 `+0`) | **ES2024** | 동작 (6)의 `[4]` |
| `Object.getOwnPropertyNames` · `Object.getOwnPropertySymbols` · `Reflect.ownKeys` | 비열거까지 · 심볼만 · 전부 | ES5 · ES2015 | 13번의 뷰 격자 |
| `structuredClone(v)` | 깊은 복사 — **호스트 API**(ECMA-262 밖) | — | 동작 (2) · [목록의 **48번 주제**](../48-deep-copy-methods-compared/) |

- **대입 대 정의** — `assign` 은 `Set`(setter 를 부르고, 실패하면 **모드와 상관없이** 던진다), 스프레드·`fromEntries`·`groupBy` 는 `CreateDataProperty`(정의).
- **얕다** — 이 표의 `Object.*` 는 전부 바깥 한 겹만 새로 만든다.
- **순서** — 결과가 평범한 객체면 **정수 키 먼저**(13번). `Map.groupBy` 만 삽입순.

## 어디서 틀리나

### (1) ★★★ `Object.assign({}, defaults, user)` 로 깊게 합쳐질 것이라 믿는다

**얕다** — 중첩 객체는 **같은 것**이 들어간다(동작 (2)의 첫 행 · `src.inner.deep 99`). 오른쪽의 중첩 객체가 왼쪽 것을 **통째로 덮어쓰고**, 안쪽 키를 합치지 않는다(11번이 `inner` 가 통째로 바뀌는 것을 찍었다).

### (2) ★★★ `Object.assign` 과 스프레드를 아무 데서나 바꿔 쓴다

대상에 **setter** 가 있으면 갈린다 — `assign` 은 부르고 스프레드는 안 부른다(동작 (1)의 `[1]` 대 `[3]`, 11번의 0회 대 1회).
그리고 **첫 인자를 바꾼다** — `Object.assign(config, patch)` 는 `config` 자체를 고친다. 새 객체가 필요하면 `{}` 를 첫 인자로.

### (3) ★★★ 비엄격 코드니까 얼린 객체에 `assign` 해도 조용할 것이라 믿는다

**던진다**(동작 (3)의 `[1]`). 평범한 대입 `frozen.a = 2` 만 비엄격에서 조용하다. 명세가 `Set(…, true)` 로 부른다.

### (4) ★★★ `assign` 이 실패하면 대상이 원래대로일 것이라 믿는다

**앞의 키는 들어간 채** 남는다(동작 (3)의 `[2]` — `{"b":"old","a":1}` · 동작 (1)의 `[4]` — `{"first":1}`). 되돌리는 단계가 없다.
여러 키를 「전부 아니면 전무」로 바꿔야 하면 **새 객체에 먼저 만들고 한 번에 바꿔 끼운다.**

### (5) ★★★ `Object.groupBy` 결과를 평범한 객체처럼 찍는다 — 또는 손으로 짠 묶기를 `{}` 에 한다

`String(g)` · `` `${g}` `` · `g.toString()` 이 **`TypeError`** 다(동작 (6)의 `[1]`). `Object.prototype` 의 메서드는 전부 없다고 봐야 한다 — 확인은 `in` 이나 정적 메서드(`Object.hasOwn`) 쪽으로 한다. 찍을 때는 `JSON.stringify(g)`.
반대로 **`groupBy` 없이 `{}` 에 손으로 묶으면** 키가 `"toString"`·`"__proto__"` 일 때 `TypeError` 가 난다(동작 (6)의 `[6]`) — `Object.create(null)` 에 모으거나 `Map` 을 쓴다.

### (6) ★★ `Object.groupBy` 의 키가 묶음이 생긴 순서로 나올 것이라 믿는다

**정수처럼 생긴 키는 앞으로 간다**(`["2","10","z"]` — 동작 (6)의 `[3]`). 순서가 의미를 가지면 `Map.groupBy` 를 쓴다.

### (7) ★★ `Object.groupBy` 로 객체를 키로 묶는다

전부 **`"[object Object]"` 한 묶음**이 된다(동작 (6)의 `[3]`). 객체 키는 `Map.groupBy` 다 — 단 **모양이 아니라 정체**로 묶는다(`k1`·`k2` 가 두 칸).

### (8) ★★ `Object.entries` → `Object.fromEntries` 왕복이 원본을 되살린다고 믿는다

**심볼 키 · 비열거 키 · getter · 프로토타입**을 잃는다(동작 (2) 격자의 `entries` 열). `Map` 을 거치면 **키가 글자가 되어** `1` 과 `"1"` 이 합쳐진다(동작 (5)의 `[2]`).

### (9) ★★ `Object.keys(o).length` 가 「키가 몇 개냐」라고 믿는다

**열거 가능한 own 글자 키**의 개수다 — 심볼·비열거는 안 센다(동작 (4)의 `[1]`·`[2]`). 전부 세려면 `Reflect.ownKeys(o).length`.

### (10) ★ `Object.groupBy` 에 유사 배열을 넘긴다

`TypeError`(동작 (6)의 `[5]`) — 이터러블만 받는다. `Array.from(arrayLike)` 로 감싸서 넘긴다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ `Object.assign` 이 원본마다 **own 키 목록 → 키마다 디스크립터 → 열거 가능하면 `Get` → `Set(to, key, value, true)`** 순으로 도는 것. 그래서 **getter 는 열거 가능한 키에서만, 키마다 한 번** · **대상 setter 가 불린다** · **실패하면 모드와 상관없이 `TypeError`** · **되돌리지 않는다.**
- `null`·`undefined` 원본을 건너뛰는 것 · 대상이 `ToObject` 를 거치는 것 · 돌려주는 것이 대상인 것.
- ★★★ `keys`/`values`/`entries` 가 **`EnumerableOwnProperties`** 로 — 목록을 먼저 받고 키마다 디스크립터를 다시 묻고, **심볼은 건너뛰고**, `keys` 는 `Get` 을 안 부르는 것. 순서가 `[[OwnPropertyKeys]]`(정수 키 → 글자 키 → 심볼)인 것.
- `fromEntries` 가 키를 `ToPropertyKey` 로 바꿔 **`CreateDataPropertyOrThrow` 로 정의**하는 것 — 그래서 `"__proto__"` 가 자기 키가 되는 것.
- ★★★ `Object.groupBy` 가 **`OrdinaryObjectCreate(null)`** 로 결과를 만드는 것 · 키가 `ToPropertyKey` 를 거치는 것 · 콜백이 `(값, 인덱스)` 로 원소마다 한 번 불리는 것 · 입력이 이터레이터로 읽히는 것.
- `Map.groupBy` 가 키를 `CanonicalizeKeyedCollectionKey` 로 접는 것(`-0` → `+0`).
- 예외의 **종류**(`TypeError`).

### 엔진(V8) 구현 · 이 판의 관찰

- 예외 **문구 전부** — `Cannot assign to read only property 'a' of object '#<Object>'` · `Cannot convert undefined or null to object` · `Iterator value ab is not an entry object` ·
  `object is not iterable (cannot read property Symbol(Symbol.iterator))` · `g.toString is not a function` · `Cannot convert object to primitive value`.
- 이 주제에서 두 node 판이 **한 글자도 같았다**는 것 — 관찰이다(판이 같아서 보장이라는 뜻이 아니다).

### 호스트가 정하는 것 — ECMA-262 밖

- ★★ **`structuredClone`** — HTML 표준의 API 다. node 와 브라우저가 각자 구현한다. 이 문서는 **node 20 에서 한 열**로만 돌렸다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`Object.assign` 은 스프레드와 같다」 → ○ 「**대상의 setter 와 첫 인자 변경**에서 갈린다 — `assign` 은 **대입**, 스프레드는 **정의**」
- ✗ 「`Object.assign` 은 엄격 모드에서만 던진다」 → ○ 「**늘 던진다** — `Set(…, true)`」
- ✗ 「`assign` 이 실패하면 아무것도 안 바뀐다」 → ○ 「**앞의 키는 남는다**」
- ✗ 「`Object.groupBy` 결과는 `{}` 와 같다」 → ○ 「**프로토타입이 `null`** 이다 — `toString` 이 없다」
- ✗ 「`Object.entries` 는 모든 키를 준다」 → ○ 「**열거 가능한 own 글자 키**만」
- ✗ 「`assign` 이 스프레드보다 빠르다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **`Object.assign(target, …)`** — **이미 있는 객체를 고쳐야** 할 때(생성자에서 `Object.assign(this, opts)`) · 대상의 setter 를 **일부러** 거치게 하고 싶을 때.
- **스프레드 `{ ...a, ...b }`** — 새 객체가 필요한 병합의 기본값. 대상 setter 가 끼어들 여지가 없다.
- **`Object.entries` + `fromEntries`** — 객체의 값에 배열 메서드를 쓸 때. 심볼·비열거는 버려도 될 때만.
- **`Object.groupBy`** — 글자 키로 묶을 때. 결과를 **찍기 전에 `JSON.stringify`** 를 떠올린다.
- **`Map.groupBy`** — 객체를 키로 묶을 때 · 묶음 순서가 의미를 가질 때.
- ★ **안 쓰는 자리** — **깊은 복사**(넷 다 얕다 — [목록의 **48번 주제**](../48-deep-copy-methods-compared/)) · **원자적 갱신**(`assign` 은 도중 실패를 되돌리지 않는다) · 얼린 객체가 대상일 수 있는 곳(비엄격이라도 던진다).

## 핵심 문장

1. ★★★ `Object.assign` 은 원본의 열거 가능한 own 키마다 **getter 를 한 번 부르고 대상에 대입**한다 — 대상의 setter 가 불리고, 비열거 키의 getter 는 안 불린다.
2. ★★★ 대입은 **`Set(…, true)`** 라서 **비엄격에서도 실패하면 `TypeError`** 이고, **앞서 쓴 키는 남는다**(원자적이지 않다).
3. ★★★ 복사 도구 넷(`assign`·스프레드·`entries` 왕복·`structuredClone`)의 격자에서 `assign` 과 **3 / 18 칸**이 갈렸고, 앞의 셋은 **전부 얕다.**
4. ★★★ `keys`/`values`/`entries` 는 **열거 가능한 own 글자 키**만, **13번의 순서**로 낸다 — `keys` 는 값을 안 읽고, 목록은 처음에 한 번 받는다.
5. ★★★ `Object.groupBy` 는 **프로토타입이 `null`** 인 객체를 돌려준다 — `String()` 이 `TypeError` 이고 키가 정수 키 순서를 따른다. 정체로 묶으려면 `Map.groupBy`.

## 관련 자료

- [ECMA-262 — Properties of the Object Constructor](https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-properties-of-the-object-constructor) · [Abstract Operations](https://tc39.es/ecma262/multipage/abstract-operations.html)(`EnumerableOwnProperties` · `GroupBy`)
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계
- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) — ★ **경계**: 그쪽은 **열거 순서 규칙과 뷰 일곱 가지의 격자**까지, 여기는 **`keys`·`entries`·`assign`·`groupBy` 가 그 순서를 따른다는 것**부터.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — ★ **경계**: 그쪽은 **스프레드의 트랩 로그와 setter 0회**, 여기는 **`assign` 의 getter·setter 로그와 실패**.
- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) — ★ **경계**: 그쪽은 **동결이 무엇을 막나**, 여기는 **동결된 대상에 `assign` 하면**만.
- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — `Object.create(null)` 의 증상(동작 (6)).
- [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) — `Map` 과 객체의 키 규칙(동작 (5)·(6)).
- [목록의 **48번 주제**](../48-deep-copy-methods-compared/)(깊은 복사 수단 비교) — ★ **경계**: 그쪽이 **`structuredClone`·JSON 왕복이 무엇을 잃나**의 정본, 여기는 **격자의 한 열**.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번**(dict 병합과 순서) — 동작 (7)의 대비.

## 용어 풀이

- **own 프로퍼티** — 객체 자신에게 붙은 프로퍼티. 체인에서 물려받은 것이 아닌 것.
- **열거 가능(enumerable)** — 디스크립터의 `enumerable: true`. `keys`·`entries`·`assign`·스프레드가 이것만 센다.
- **`[[OwnPropertyKeys]]`** — own 키 목록을 내는 내부 메서드. 순서가 정수 키 → 글자 키(삽입순) → 심볼(삽입순).
- **`EnumerableOwnProperties`** — `keys`/`values`/`entries` 의 공통 명세 연산. 글자 키만, 열거 가능한 것만.
- **`Set(O, P, V, Throw)`** — 대입의 명세 연산. `Throw` 가 `true` 면 실패할 때 `TypeError`.
- **`CreateDataProperty`** — 프로퍼티를 **정의**하는 명세 연산. setter 를 안 부른다.
- **대입 대 정의** — 대입은 기존 프로퍼티(와 체인의 setter)를 거치고, 정의는 그 자리에 새 데이터 프로퍼티를 놓는다.
- **얕은 복사** — 바깥 한 겹만 새로 만드는 복사. 안쪽 객체는 공유된다.
- **원자적(atomic)** — 전부 되거나 전부 안 되거나. `assign` 은 아니다.
- **null 프로토타입 객체** — `[[Prototype]]` 이 `null` 인 객체. `toString` 등 `Object.prototype` 의 것이 없다.
- **`ToPropertyKey`** — 값을 프로퍼티 키(문자열 또는 심볼)로 바꾸는 연산.
- **`structuredClone`** — HTML 표준의 깊은 복사 함수. ECMA-262 밖이다.

## 더 들어가면

- **getter 를 getter 째 복사하기** — `Object.defineProperties({}, Object.getOwnPropertyDescriptors(src))`. 이 문서는 격자에 넣지 않았다(**안 돌렸다**).
- **`Object.groupBy` 가 `Array.prototype.group` 이 아닌 이유** — 제안 과정의 웹 호환성 논의다. 이 문서는 그 경위를 확인하지 않았다.
- **깊은 병합** — 표준에 없다. [목록의 **48번 주제**](../48-deep-copy-methods-compared/)와 라이브러리의 몫이다.
