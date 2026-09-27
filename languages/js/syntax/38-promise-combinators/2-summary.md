# js/syntax/38 — Promise 조합기: 「무엇을 기다리고, 언제 끝나고, 무엇을 버리나 — 그리고 아무것도 취소하지 않는다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — 조합기 4(`all`·`allSettled`·`race`·`any`) × 입력 모양 4(전부 이행 · 하나 거부 · 전부 거부 · **빈 배열**) = **16칸**.
> 입력을 **한 단계에 하나씩 손으로** 확정하고(단계 = `setTimeout` 하나), 칸마다 **결과**와 **몇 단계째에 끝났나**를 찍는다.
> 마지막 줄은 **「마지막 입력보다 먼저 끝난 칸 N / 16 · 끝내 안 끝난 칸 M / 16」**(동작 (1)).
> ★★ 보조로 **① 추상 연산에 로그 심기**(입력 작업이 단계마다 찍는다 — 조합기가 끝난 **뒤에도** 찍히나 · 동작 (2))와
> **④ 예외의 `constructor.name` + `message`**(`any` 가 던지는 `AggregateError 「All promises were rejected」` 와 `errors` 개수)를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Properties of the Promise Constructor](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-properties-of-the-promise-constructor) — `Promise.all`·`allSettled`·`any`·`race`(「**iterable 이 값을 하나도 내지 않거나 … 끝내 확정되지 않으면, 이 메서드가 돌려준 pending 프라미스는 영원히 확정되지 않는다**」 — `race` 의 노트) · `Promise.try` · `Promise.withResolvers`
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(`allSettled` 2020 · `any` 2021 · `withResolvers` 2024 · `try` 2025)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **메서드·연산 이름**으로, 결과와 끝나는 단계는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다. Chrome 151 은 헤드리스(`./js36b-browser.sh` — 소스는 [36번](../36-event-loop-and-microtasks/2-summary.md)에 있다).
> ★★★ **`Promise.withResolvers`(ES2024)·`Promise.try`(ES2025)는 두 node 판에 없다**(아래 판별 블록) — 그 탐침은 **Chrome 151 로만** 돌렸다.
> ★★ **이 주제의 node 탐침은 두 node 판과 Chrome 151 에서 한 글자도 같았다**(아래 대조기의 집계 줄).
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `Promise.all` · `Promise.race` | ES2015 | 세 판 다 있다 |
> | `Promise.allSettled` | **ES2020** | 세 판 다 있다 |
> | `Promise.any` · `AggregateError` | **ES2021** | 세 판 다 있다 |
> | `Promise.withResolvers` | **ES2024** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
> | `Promise.try` | **ES2025** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
>
> ★★ **판 경계는 TC39 finished proposals 표와 이 목록의 README 를 대조했다** — 38행의 `withResolvers`(ES2024)·`try`(ES2025)는 **표와 같다.** README 의 판 표(`ES2024`·`ES2025` 행)에도 같은 번호로 올라 있다. `allSettled`(2020)·`any`(2021)는 README 38행에 판이 없다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 조합기 4 × 입력 모양 4 = **16칸** — 결과 · 끝난 단계 · 「`7 / 16` · `1 / 16`」(동작 (1)) |
> | ★★ **① 추상 연산에 로그 심기** | 입력 작업이 단계마다 한 줄 — 조합기가 끝난 **뒤의 줄 수**를 센다(동작 (2)) · `Promise.try` 의 콜백이 **호출 안에서** 도나(동작 (4)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `AggregateError 「All promises were rejected」` 와 `errors` 개수(3 · **0**) |
> | ★ **`sort -u` 가짓수**(규칙 11) | 이미 확정된 두 입력의 `race` 를 200판 — **Go `select` 의 가짓수 격자와 나란히** 읽는다(동작 (3)) |
> | ★ **부적용 — ③ 브랜드 태그** | 판정할 객체의 종류가 없다 |
> | ★ **안 쟀다 — 시간** | ★★★ **「`Promise.all` 이 빠르다」를 쓰지 않는다.** 이 문서의 「단계」는 **내가 손으로 넘긴 순번**이지 시간이 아니다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 — 머신에 매인다 | ★★★ 16칸의 **결과와 끝난 단계** · 마지막 줄 — 입력을 **손으로 한 단계씩** 확정했으므로 타이머 경쟁이 없다 |
> | ★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) | ★★ 동작 (2)의 **줄 순서**와 `8` — 입력 작업이 **마이크로태스크로만** 걸음을 옮긴다(명세의 FIFO) · 동작 (3)의 가짓수 `1` |
>
> **층** — 조합기는 **전부 언어(ECMA-262)의 것**이다. 호스트가 끼어드는 자리는 **입력을 확정하는 타이머뿐**이고, 그 타이머는 **한 번에 하나만** 걸었다.
>
> **선행** — [37 — Promise 상태 모델](../37-promise-state-model/2-summary.md)(직접 선행 — ★★ 조합기는 결과 프라미스의 **resolve·reject 를 한 번만** 부르는 장치다. 처음 것만 효력이 있다는 규칙이 「`all` 은 첫 거부로 끝난다」의 뒷면이다) ·
> [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ **`Promise.all` 은 이터러블을 호출 안에서 동기로 끝까지 읽는다** — 거기서 `next#4 done` 까지 찍었다) ·
> [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md)(★★ **`Array.fromAsync` 는 `next` → settle 을 하나씩, `Promise.all([...gen()])` 은 `next` 셋을 먼저** — 동작 (2)의 「시작은 이미 끝났다」와 이어진다) ·
> [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md)(★★ `AggregateError` 의 `errors` 는 **복사한 배열** — 거기가 정본이다).
>
> ★ **경계 — 순서의 원리**는 [36번](../36-event-loop-and-microtasks/2-summary.md), **`await` 로 조합기를 받는 법과 순차 대 병렬**은 [39번](../39-async-await/2-summary.md), **취소(`AbortController`)** 는 [목록의 **41번 주제**](../41-cancellation-and-timeouts/)다.

```text
===== ./js36b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  Promise                                   yes
  ES2017  async function / await                    yes
  ES2018  Promise.prototype.finally                 yes
  ES2020  Promise.allSettled                        yes
  ES2021  Promise.any / AggregateError              yes
  ES2024  Promise.withResolvers                     no
  ES2025  Promise.try                               no
  ES2026  Array.fromAsync                           no
  host    queueMicrotask                            yes
  host    setTimeout                                yes
  host    setImmediate                              yes
  host    process.nextTick                          yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  Promise                                   yes
  ES2017  async function / await                    yes
  ES2018  Promise.prototype.finally                 yes
  ES2020  Promise.allSettled                        yes
  ES2021  Promise.any / AggregateError              yes
  ES2024  Promise.withResolvers                     no
  ES2025  Promise.try                               no
  ES2026  Array.fromAsync                           no
  host    queueMicrotask                            yes
  host    setTimeout                                yes
  host    setImmediate                              yes
  host    process.nextTick                          yes
Google Chrome 151.0.7922.173
  ES2015  Promise                                   yes
  ES2017  async function / await                    yes
  ES2018  Promise.prototype.finally                 yes
  ES2020  Promise.allSettled                        yes
  ES2021  Promise.any / AggregateError              yes
  ES2024  Promise.withResolvers                     yes
  ES2025  Promise.try                               yes
  ES2026  Array.fromAsync                           yes
  host    queueMicrotask                            yes
  host    setTimeout                                yes
  host    setImmediate                              no
  host    process.nextTick                          no
Python 3.12.3
```

두 node 판 · Chrome 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 13 · differs 0   ·   node20 vs Chrome 151: identical 12 · differs 0 · node only 1`

## 한눈에 — 쉽게 말하면

**조합기는 「여러 택배를 한 번에 받는 네 가지 방식」이다. 택배(입력 프라미스)는 이미 출발했고, 조합기는 「언제 문을 닫을지」만 정한다.**

- ★★★ **`all`** — 「전부 오면 닫는다. **하나라도 파손이면 그 자리에서 닫는다.**」
- ★★★ **`allSettled`** — 「파손이든 아니든 **전부 올 때까지** 기다렸다가 목록을 준다.」
- ★★★ **`race`** — 「**먼저 온 것 하나**로 닫는다 — 파손이어도.」
- ★★★ **`any`** — 「**성한 것 하나**가 오면 닫는다. 전부 파손이면 파손 목록(`AggregateError`)을 준다.」
- ★★★ **문을 닫아도 오던 택배는 계속 온다** — 조합기는 **아무것도 취소하지 않는다.**

```text
   입력 세 개가 1 · 2 · 3 단계에 차례로 확정된다  (★ = 거부)

                    전부 이행            하나 거부(2단계★)        전부 거부
   all              3단계  [v0,v1,v2]    ★ 2단계  e1             ★ 1단계  e0
   allSettled       3단계  목록          3단계  목록              3단계  목록
   race             1단계  v0            1단계  v0               ★ 1단계  e0
   any              1단계  v0            1단계  v0               ★ 3단계  AggregateError
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 이미 출발한 택배 | 조합기에 넘기기 **전에** 시작된 입력 프라미스들 | 동작 (2)의 `start` 세 줄 |
| 문을 닫는다 | 결과 프라미스를 **확정**한다(resolve·reject 를 한 번 부른다) | 동작 (1)의 `at step k` |
| 파손 목록 | `AggregateError` 의 `errors` 배열 | 동작 (1)의 `errors 3` |
| 문이 영원히 안 닫힌다 | `race([])` — 영원히 pending | 동작 (1)의 `never settled` |
| 계속 오는 택배 | 조합기가 끝난 뒤에도 도는 입력 작업 | 동작 (2)의 `8` |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**`Promise.all` 이 첫 실패로 거부된 뒤에도 나머지 요청이 끝까지 돌아 DB 에 썼다**」와
「**`Promise.race([])` 로 만든 타임아웃이 영영 안 풀렸다**」(입력 목록이 비어 있었다)가 그것이다(동작 (1)·(2)).

> **조합기(combinator)** — 프라미스 여럿을 받아 **프라미스 하나**를 돌려주는 정적 메서드.\
> 예: `Promise.all([p, q])`.

## 이 주제가 답하려는 질문

1. **네 조합기는 각각 무엇을 기다리고, 언제 끝나고, 무엇을 돌려주나** — 하나 거부 · 전부 거부 · **빈 입력**에서?
2. **조합기가 끝나면 나머지 입력은 어떻게 되나** — 멈추나, 계속 도나?
3. **`withResolvers`(ES2024)·`try`(ES2025)는 무엇을 줄여 주나** — 이미 쓰던 어떤 코드와 같고 어디서 다른가?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 조합기 격자 — 4 × 4, 끝나는 단계까지

**언제 쓰나** — 여러 비동기 작업을 묶을 때 **어느 조합기**를 고를지 · 입력 목록이 **비어 있을 수 있는** 코드를 쓸 때.
★★★ 입력은 전부 손으로 만든 **지연 프라미스**다. 단계 k 에 **k 번째 입력**을 확정한다(`ok` 면 `"v<i>"` 로 이행, `no` 면 `Error e<i>` 로 거부). 단계마다 `setTimeout` 이 **하나만** 걸린다.

```js
// js36b-38a-combinator-grid.js
// Four combinators x four input shapes. Inputs are settled by hand, one per step: input 0 at step 1, input 1 at step 2, ...
// Each step is its own setTimeout, so "settled at step k" means the combinator's promise settled right after step k.
const show = (x) => {
  if (x instanceof AggregateError) return "AggregateError 「" + x.message + "」 errors " + x.errors.length;
  if (x instanceof Error) return x.constructor.name + " 「" + x.message + "」";
  if (Array.isArray(x)) return "[" + x.map((r) => (r && r.status ? r.status : JSON.stringify(r))).join(",") + "]";
  return JSON.stringify(x);
};
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };
const shapes = [["all fulfil", ["ok", "ok", "ok"]], ["one rejects", ["ok", "no", "ok"]], ["all reject", ["no", "no", "no"]], ["empty", []]];
const combos = ["all", "allSettled", "race", "any"];
let step = 0;
const cells = [];
for (const [shape, plan] of shapes) for (const c of combos) {
  const ins = plan.map(() => deferred());
  const cell = { shape, c, plan, ins, result: "pending", at: "never" };
  Promise[c](ins.map((d) => d.promise)).then(
    (v) => { cell.result = "fulfilled " + show(v); cell.at = step; },
    (e) => { cell.result = "rejected  " + show(e); cell.at = step; });
  cells.push(cell);
}
const next = () => {
  step++;
  for (const cell of cells) {
    const i = step - 1, d = cell.ins[i];
    if (!d) continue;
    if (cell.plan[i] === "ok") d.resolve("v" + i); else d.reject(new Error("e" + i));
  }
  if (step < 4) setTimeout(next, 0); else report();
};
setTimeout(next, 0);
function report() {
  let early = 0, never = 0;
  for (const [shape] of shapes) {
    console.log("--- " + shape);
    for (const cell of cells.filter((x) => x.shape === shape)) {
      console.log("  " + cell.c.padEnd(11) + (cell.at === "never" ? "never settled" : "at step " + cell.at).padEnd(15) + cell.result);
      if (cell.at === "never") never++;
      else if (cell.at < cell.plan.length) early++;
    }
  }
  console.log("cells settled before their last input settled: " + early + " / " + cells.length + " · cells never settled: " + never + " / " + cells.length);
}
```

```text
===== node20 js36b-38a-combinator-grid.js (exit=0) =====
--- all fulfil
  all        at step 3      fulfilled ["v0","v1","v2"]
  allSettled at step 3      fulfilled [fulfilled,fulfilled,fulfilled]
  race       at step 1      fulfilled "v0"
  any        at step 1      fulfilled "v0"
--- one rejects
  all        at step 2      rejected  Error 「e1」
  allSettled at step 3      fulfilled [fulfilled,rejected,fulfilled]
  race       at step 1      fulfilled "v0"
  any        at step 1      fulfilled "v0"
--- all reject
  all        at step 1      rejected  Error 「e0」
  allSettled at step 3      fulfilled [rejected,rejected,rejected]
  race       at step 1      rejected  Error 「e0」
  any        at step 3      rejected  AggregateError 「All promises were rejected」 errors 3
--- empty
  all        at step 0      fulfilled []
  allSettled at step 0      fulfilled []
  race       never settled  pending
  any        at step 0      rejected  AggregateError 「All promises were rejected」 errors 0
cells settled before their last input settled: 7 / 16 · cells never settled: 1 / 16
```

```text
   명세의 네 알고리즘이 결과 프라미스를 확정하는 조건 (PerformPromiseXxx)

                 입력 하나가 이행하면           입력 하나가 거부하면            남은 수가 0 이 되면
   all           값을 제자리에 넣고 남은 수 -1   ★ 곧바로 reject               resolve(값 배열)
   allSettled    {fulfilled, value} 넣고 -1     {rejected, reason} 넣고 -1    resolve(목록)
   race          ★ 곧바로 resolve              ★ 곧바로 reject               (세지 않는다)
   any           ★ 곧바로 resolve              이유를 넣고 남은 수 -1         reject(AggregateError)

   남은 수는 1 에서 시작해 입력마다 +1, 다 읽은 뒤 -1   → 입력이 0 개면 읽자마자 0 이 된다
   race 에는 이 수가 없다                             → 입력이 0 개면 확정할 계기가 없다
```

- ★★★ **집계 줄 — `cells settled before their last input settled: 7 / 16 · cells never settled: 1 / 16`.**
  일찍 끝난 일곱은 **`race`(3) · `any`(2) · `all`(2)** 이다 — `all` 은 **거부가 있는 두 모양**에서만 일찍 끝났다(`at step 2` · `at step 1`). **`allSettled` 는 한 칸도 일찍 안 끝났다.**
- ★★★ **빈 배열 행** — `all([])` → **`at step 0` 에 `fulfilled []`**(첫 단계 전에 이미), `allSettled([])` 도 같다, **`race([])` → `never settled`**, **`any([])` → `at step 0` 에 `AggregateError … errors 0`.**
  명세의 `race` 노트가 그대로다 — 「**iterable 이 값을 하나도 내지 않으면 … 영원히 확정되지 않는다.**」 `all`·`allSettled`·`any` 는 **남은 수를 세는** 알고리즘이라 0 개에서 곧바로 끝난다.
- ★★★ **`any` 가 전부 거부되면 `AggregateError 「All promises were rejected」`** — `errors` 는 **입력 순서대로 이유 3 개**다. 이것이 32번 동작 (5)의 그 오류다. 빈 입력이면 `errors 0`.
- ★★ **`race` 는 거부로도 끝난다**(전부 거부 행 — `at step 1` 에 `Error 「e0」`). 「첫 **성공**」을 원하면 `any` 다.
- ★★ **`all` 의 첫 거부는 「그 입력의 이유」 그대로**다(`Error 「e1」`) — 감싸지 않는다. `allSettled` 는 **거부하지 않는다**(세 모양 모두 `fulfilled` 목록).

### (2) ★★★ `all` 은 나머지를 취소하지 않는다 — 로그로

**언제 쓰나** — 「하나 실패하면 나머지는 그만둔다」고 기대하고 `Promise.all` 을 쓸 때 · 부작용(쓰기·전송)이 있는 작업을 묶을 때.
★★ 작업 셋이 **마이크로태스크 한 걸음씩** 나아가며 줄을 찍는다. `B` 는 첫 걸음에서 던진다. 조합기가 끝나면 `>>` 로 시작하는 줄이 찍힌다.

```js
// js36b-38b-no-cancel.js
// Three jobs, each a few microtask steps long; job B rejects at its first step.
// Every step prints a line. Where do the combinator's line and the jobs' lines fall relative to each other?
const lines = [];
const log = (s) => lines.push(s);
const job = (name, steps, failAt) => (async () => {
  log(name + " start");
  for (let i = 1; i <= steps; i++) {
    await null;
    log(name + " step " + i);
    if (i === failAt) throw new Error(name + " failed");
  }
  log(name + " finished");
  return name;
})();
const run = (combo) => {
  lines.length = 0;
  return Promise[combo]([job("A", 6), job("B", 1, 1), job("C", 5)]).then(
    (v) => log(">> " + combo + " fulfilled " + JSON.stringify(v)),
    (e) => log(">> " + combo + " rejected " + e.constructor.name + " 「" + e.message + "」"));
};
(async () => {
  for (const combo of ["all", "race"]) {
    await run(combo);
    await new Promise((r) => setTimeout(r, 0));
    const at = lines.findIndex((l) => l.startsWith(">>"));
    console.log("--- Promise." + combo);
    for (const l of lines) console.log("  " + l);
    console.log("  lines printed by the jobs after the combinator settled: " + (lines.length - at - 1));
  }
})();
```

```text
===== node20 js36b-38b-no-cancel.js (exit=0) =====
--- Promise.all
  A start
  B start
  C start
  A step 1
  B step 1
  C step 1
  A step 2
  C step 2
  A step 3
  >> all rejected Error 「B failed」
  C step 3
  A step 4
  C step 4
  A step 5
  C step 5
  C finished
  A step 6
  A finished
  lines printed by the jobs after the combinator settled: 8
--- Promise.race
  A start
  B start
  C start
  A step 1
  B step 1
  C step 1
  A step 2
  C step 2
  A step 3
  >> race rejected Error 「B failed」
  C step 3
  A step 4
  C step 4
  A step 5
  C step 5
  C finished
  A step 6
  A finished
  lines printed by the jobs after the combinator settled: 8
```

```text
   Promise.all([A, B, C])  — 호출하는 순간 A·B·C 는 이미 「start」 를 지났다

   A ──1──2──3──┆──4──5──6── finished        ← 끝까지 간다
   B ──1✗       ┆                            ← 여기서 거부
   C ──1──2─────┆──3──4──5── finished        ← 끝까지 간다
                ┆
             >> all rejected  (B 의 거부가 결과에 닿기까지 몇 걸음 걸렸다)

   조합기가 하는 일: 결과 프라미스를 확정한다 — 그게 전부다. 입력에게 아무 말도 안 한다.
```

- ★★★ **`lines printed by the jobs after the combinator settled: 8`** — `all` 이 거부된 뒤에도 `A`·`C` 는 **끝까지** 걸었다(`A finished` · `C finished`). **`race` 도 똑같이 `8`** 이다.
- ★★★ **입력은 조합기에 넘기기 전에 이미 시작했다** — `start` 세 줄이 조합기보다 먼저 찍혔다. 조합기는 **이미 도는 프라미스를 기다릴 뿐**이다. 명세의 네 알고리즘에는 **입력에게 무엇을 알리는 단계가 없다.**
- ★★ **`B step 1` 과 `>> all rejected` 사이에 네 줄**(`C step 1` · `A step 2` · `C step 2` · `A step 3`)이 끼었다 — `B` 의 거부가 **async 함수의 결과 → `all` 의 반응 → 결과 프라미스 → `then` 처리기**를 거치며 틱을 먹는다(37번 동작 (2)의 흡수 규칙).
- ★★ 멈추게 하려면 **취소 신호를 따로** 넘겨야 한다 — 프라미스 자체에는 취소가 없다([목록의 **41번 주제**](../41-cancellation-and-timeouts/) `AbortController`).
- ★ 입력이 **한꺼번에 시작하는 것**은 `Promise.all` 의 덕이 아니라 **배열을 만들 때 셋을 이미 불렀기 때문**이다 — 26번의 `Promise.all([...gen()])` 이 `next` 셋을 **먼저** 부른 것과 같은 이야기다. 39번 동작 (3)이 「시작 로그」로 다시 잰다.

### (3) ★★ 이미 확정된 입력 둘의 `race` — 200판 가짓수

**언제 쓰나** — 캐시 값과 네트워크 요청을 `race` 에 넣을 때 · Go 의 `select` 에서 온 사람이 「준비된 것 중 아무거나」를 기대할 때.

```js
// js36b-38-h-race-ready.js
// Both inputs are already fulfilled before race is called. argv[2] gives the order they are passed in.
const a = Promise.resolve("a"), b = Promise.resolve("b");
const ins = process.argv[2] === "ba" ? [b, a] : [a, b];
Promise.race(ins).then((v) => console.log(v));
```

```sh
# js36b-38d-race-ready.sh
#!/usr/bin/env bash
# Promise.race over two inputs that are both ready already -- 200 runs per order, distinct results (sort -u).
set -u -o pipefail
cd "$(dirname "$0")"
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for order in ab ba; do
  got="$(for i in $(seq 200); do "$N20" js36b-38-h-race-ready.js "$order"; done)"
  echo "[$order] 200 runs · distinct results $(printf '%s\n' "$got" | sort -u | wc -l) : $(printf '%s\n' "$got" | sort -u | paste -sd' ' -)"
done
```

```text
===== ./js36b-38d-race-ready.sh (exit=0) =====
[ab] 200 runs · distinct results 1 : a
[ba] 200 runs · distinct results 1 : b
```

```text
   이미 이행한 a · b 를 race 에 넘길 때

   race([a, b]):  a.then(확정) 을 건다 → 반응 잡 Ja   (a 가 이미 이행 → 곧바로 줄을 선다)
                  b.then(확정) 을 건다 → 반응 잡 Jb
                  잡 큐 [Ja, Jb]  → Ja 가 먼저 돈다 → 결과 "a"  → Jb 의 확정은 무시된다(37번의 「처음 것만」)

   Go select { case <-ca: … case <-cb: … }  — 둘 다 준비됨 → 균등 무작위로 하나   (200판 가짓수 2)
```

- ★★★ **두 순서 모두 가짓수 `1`** — `[a, b]` 면 늘 `a`, `[b, a]` 면 늘 `b`. **먼저 넘긴 것**이 이긴다.
  `race` 는 입력을 **넘긴 순서대로** `then` 을 건다. 둘 다 이미 이행했으면 반응 잡이 **건 순서대로** 줄을 서고(36번의 FIFO), 먼저 돈 것이 결과를 확정한다 — 뒤의 것은 37번의 「처음 것만」에 걸려 버려진다.
- ★★ **Go 의 `select` 는 반대**다 — 준비된 가지가 둘이면 **명세상 무작위**로 골라 200판 가짓수가 **2** 였다([Go 30](../../../go/syntax/30-select-default-and-timeouts/2-summary.md) 동작 (1)). **「먼저 적은 것이 이긴다」가 JS 에서는 참, Go 에서는 거짓**이다.

### (4) ★★ `Promise.withResolvers`(ES2024) · `Promise.try`(ES2025) — Chrome 151

**언제 쓰나** — `resolve` 를 **executor 밖에서** 불러야 할 때(이벤트 콜백·큐) · 동기로 던질 수도 있는 함수를 **프라미스 하나로** 받고 싶을 때.
★★★ **두 node 판에는 둘 다 없다**(판별 블록의 `ES2024`·`ES2025` 줄이 `no`). 이 탐침은 Chrome 151 로만 돌렸다.

```js
// js36b-38c-resolvers-try.web.js
// Chrome only in this batch (node18 and node20 have neither function -- see the feature table).
const show = (x) => (x instanceof Error ? x.constructor.name + " 「" + x.message + "」" : JSON.stringify(x));
const log = (s) => console.log(s);
(async () => {
  log("[1] Promise.withResolvers()");
  const r = Promise.withResolvers();
  log("  own keys " + JSON.stringify(Object.keys(r)) + " · promise instanceof Promise " + (r.promise instanceof Promise));
  setTimeout(() => r.resolve("from a timer"), 0);
  log("  awaited " + show(await r.promise));
  r.resolve("again"); r.reject(new Error("again"));
  log("  after resolve and reject once more " + show(await r.promise));

  log("[2] when does the callback run, and where does its throw go?");
  const boom = (tag) => () => { log("  callback runs (" + tag + ")"); throw new Error(tag); };
  for (const [tag, label, call] of [
    ["t", "Promise.try(f)", (f) => Promise.try(f)],
    ["r", "Promise.resolve().then(f)", (f) => Promise.resolve().then(f)],
    ["n", "new Promise((res) => res(f()))", (f) => new Promise((res) => res(f()))],
  ]) {
    log(" " + label);
    let p;
    try { p = call(boom(tag)); log("  call returned"); } catch (e) { log("  call threw " + show(e)); }
    try { await p; } catch (e) { log("  awaited promise rejected with " + show(e)); }
  }
  log("[3] Promise.try passes the extra arguments");
  log("  " + show(await Promise.try((a, b) => a + b, 2, 3)));
  log("[4] Promise.resolve(f()) with the same kind of f");
  try { Promise.resolve(boom("p")()); } catch (e) { log("  thrown at the call site: " + show(e)); }
})();
```

```text
===== ./js36b-browser.sh js36b-38c-resolvers-try.web.js (exit=0) =====
[1] Promise.withResolvers()
  own keys ["promise","resolve","reject"] · promise instanceof Promise true
  awaited "from a timer"
  after resolve and reject once more "from a timer"
[2] when does the callback run, and where does its throw go?
 Promise.try(f)
  callback runs (t)
  call returned
  awaited promise rejected with Error 「t」
 Promise.resolve().then(f)
  call returned
  callback runs (r)
  awaited promise rejected with Error 「r」
 new Promise((res) => res(f()))
  callback runs (n)
  call returned
  awaited promise rejected with Error 「n」
[3] Promise.try passes the extra arguments
  5
[4] Promise.resolve(f()) with the same kind of f
  callback runs (p)
  thrown at the call site: Error 「p」
```

```text
   f 를 부르는 세 가지 — f 가 곧바로 던질 때

                                   f 는 언제 도나        f 의 throw 는 어디로
   Promise.try(f)                  호출 안에서(지금)      거부된 프라미스
   Promise.resolve().then(f)       다음 틱               거부된 프라미스
   new Promise(r => r(f()))        호출 안에서(지금)      거부된 프라미스 (executor 가 잡는다)
   Promise.resolve(f())            호출 안에서(지금)      ★ 호출한 자리로 던져진다
```

- ★★★ **`withResolvers()` 는 own 키 `promise`·`resolve`·`reject` 셋**을 가진 평범한 객체다 — `let resolve; new Promise(r => resolve = r)` 를 한 줄로 줄인 것이다. **37번의 규칙이 그대로**다 — 타이머가 먼저 `resolve` 한 뒤의 `resolve`·`reject` 는 무시됐다(`"from a timer"`).
- ★★★ **`Promise.try(f)` 는 `f` 를 호출 안에서 곧바로 부른다**(`callback runs` 가 `call returned` 보다 먼저). `then(f)` 은 **다음 틱**이라 순서가 반대다.
  셋 다 `f` 의 `throw` 를 **거부로 바꾼다.** `Promise.resolve(f())` 만 **호출한 자리로 던진다**(`[4]` — `f()` 가 프라미스가 생기기 전에 돈다).
- ★★ **`Promise.try(f, 2, 3)` 은 인자를 넘긴다**(`5`) — `new Promise(r => r(f(2, 3)))` 를 짧게 쓴 것과 같다. 명세도 「`Call(callback, undefined, args)` → 던지면 reject, 아니면 `PromiseResolve`」 한 줄이다.
- ★ node 에서 쓰려면 **판을 올리거나 폴리필**이다 — 이 문서는 node 22 이상을 돌리지 않았다.

### (5) ★★ 이터러블은 호출 안에서 끝까지 — 끝없는 제너레이터

**언제 쓰나** — 제너레이터·스트림을 곧바로 조합기에 넘기려 할 때.
★ 19번이 「돌려 보지 않았다」로 남긴 경우다 — **가드**가 10만 번째 `next()` 에서 던져 탐침이 끝나게 했다.

```js
// js36b-38e-endless.js
// An endless generator handed to Promise.all. A guard throws at the 100000th next(), so the probe ends.
// Question: how many next() calls happen before Promise.all returns, and what does it return?
let nexts = 0;
function* endless() {
  for (;;) {
    nexts++;
    if (nexts === 100000) throw new RangeError("guard: stopped at next #" + nexts);
    yield nexts;
  }
}
let returned;
try {
  returned = Promise.all(endless());
  console.log("Promise.all returned after " + nexts + " next() calls · a " + returned.constructor.name);
} catch (e) {
  console.log("Promise.all threw " + e.constructor.name + " 「" + e.message + "」");
}
if (returned) returned.then(
  (v) => console.log("fulfilled with " + v.length + " values"),
  (e) => console.log("rejected with " + e.constructor.name + " 「" + e.message + "」"));
```

```text
===== node20 js36b-38e-endless.js (exit=0) =====
Promise.all returned after 100000 next() calls · a Promise
rejected with RangeError 「guard: stopped at next #100000」
```

```text
   Promise.all(endless())  — 호출 한 번 안에서 일어나는 일

   GetIterator ─▶ next#1 ─▶ Promise.resolve(1).then(…) ─▶ next#2 ─▶ … ─▶ next#100000 ✗ (가드가 던진다)
                                                                              │
   호출이 여기까지 돌아오지 않는다 ◀──────────────────────────────────────────────┘
                                                                IfAbruptRejectPromise → 거부된 프라미스를 돌려준다
```

- ★★★ **`Promise.all returned after 100000 next() calls`** — 가드가 던질 때까지 **호출이 돌아오지 않았다.** 네 조합기는 이터러블을 **호출 안에서 동기로 끝까지** 읽는다(19번 동작 (1)의 `[4]` — 호출 직후 이미 `next#4 done`).
- ★★ 읽다가 난 예외는 **던지지 않고 거부**가 된다(`rejected with RangeError …`) — 명세의 `IfAbruptRejectPromise`. 호출한 자리의 `try`/`catch` 는 **아무것도 못 잡는다.**
- ★ 하나씩 기다리며 당기려면 `for await` 나 `Array.fromAsync`(ES2026 — 26번 동작 (7))다. [목록의 **40번 주제**](../40-async-iteration-and-for-await/)가 정본이다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 끝나는 때 | 결과 | 빈 입력 | 판 |
|---|---|---|---|---|
| `Promise.all(it)` | 전부 이행 · **첫 거부** | 값 배열(입력 순서) · 그 이유 | 곧바로 `[]` | ES2015 |
| `Promise.allSettled(it)` | **전부 확정** | `{status, value}`·`{status, reason}` 배열 — **거부하지 않는다** | 곧바로 `[]` | **ES2020** |
| `Promise.race(it)` | **첫 확정**(이행이든 거부든) | 그 값 · 그 이유 | ★ **영원히 pending** | ES2015 |
| `Promise.any(it)` | **첫 이행** · 전부 거부 | 그 값 · `AggregateError`(이유 배열) | 곧바로 `AggregateError` | **ES2021** |
| `Promise.withResolvers()` | — | `{ promise, resolve, reject }` | — | **ES2024** |
| `Promise.try(f, ...args)` | `f` 를 **지금** 부른다 | `f` 의 결과(던지면 거부) | — | **ES2025** |

- **네 조합기 모두 이터러블을 호출 안에서 동기로 끝까지 읽는다**(19번 동작 (1)의 `[4]` · 동작 (5) — 끝없으면 **돌아오지 않는다**). 입력의 비프라미스 값은 `Promise.resolve` 로 감싼다.
- **어느 것도 입력을 취소하지 않는다.**
- **같은 단계에 이미 확정된 입력들 사이에서는 먼저 넘긴 것이 이긴다**(`race`·`any` · 동작 (3)).

## 어디서 틀리나

### (1) ★★★ `Promise.all` 이 거부되면 나머지 작업이 멈춘다고 믿는다

**계속 돈다**(동작 (2)의 `8` 줄). 부작용이 있는 작업이면 **취소 신호**를 따로 넘기거나, 다 끝나기를 원하면 `allSettled` 다.

### (2) ★★★ `Promise.race([])` 를 「곧바로 끝나는 것」으로 쓴다

**영원히 pending** 이다(`never settled`). 목록이 동적으로 만들어지는 타임아웃 코드에서 **말없이 멈춘다.** 비어 있을 수 있으면 먼저 검사한다.

### (3) ★★★ `race` 를 「첫 성공」으로 쓴다

**첫 거부로도 끝난다**(전부 거부 행의 `race` — `Error 「e0」`). 첫 성공은 `any` 다.

### (4) ★★ `any` 의 거부 이유가 마지막 입력의 이유일 것이라 믿는다

**`AggregateError`** 다 — 이유는 `errors` 에 **입력 순서대로** 들어 있다. 빈 입력이면 `errors` 가 **0 개**인 채로 곧바로 거부된다.

### (5) ★★ `Promise.all` 이 입력을 「동시에 시작시킨다」고 믿는다

**시작시킨 것은 배열을 만든 식**이다 — `Promise.all` 이 받을 때는 이미 돌고 있다(동작 (2)의 `start` 세 줄). 거꾸로, **나중에 부를 함수**를 넘기면 아무것도 시작하지 않는다(39번).

### (6) ★★ 준비된 입력 여럿의 `race` 가 무작위일 것이라 믿는다

**먼저 넘긴 것**이다(가짓수 `1`). Go 의 `select` 와 반대다.

### (7) ★★ `Promise.resolve(f())` 로 「던져도 거부로 받겠다」를 쓴다

**`f()` 가 먼저 돌아 호출한 자리로 던진다**(동작 (4)의 `[4]`). `Promise.try(f)` 나 `new Promise(r => r(f()))` 를 쓴다.

### (8) ★ node 18·20 에서 `Promise.withResolvers`·`Promise.try` 를 쓴다

**없다** — `typeof` 가 `undefined` 다(판별 블록). ES2024·2025 기능이다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ 네 알고리즘(`PerformPromiseAll`·`AllSettled`·`Any`·`Race`)의 **확정 조건** — 위 동작 (1)의 그림. **남은 수를 세는 셋은 빈 입력에서 곧바로 끝나고, `race` 는 영원히 pending.**
- ★★★ **입력에게 알리는 단계가 없다** — 취소가 없다.
- ★★ `any` 의 거부는 **`AggregateError`**(`errors` = 이유 배열, 입력 순서). 결과 배열도 **입력 순서**다(끝난 순서가 아니다).
- ★★ `Promise.try` — `f(...args)` 를 **곧바로** 부르고 던지면 거부. `withResolvers` — 세 키의 객체.
- ★★ 이미 확정된 입력들 사이의 순서 — `then` 을 **건 순서대로** 반응 잡이 선다(잡 FIFO).

### 호스트 · 구현(V8) · 이 판의 관찰

- ★ **이 주제에는 호스트 칸이 없다** — 조합기는 호스트를 부르지 않는다. 입력을 확정한 타이머만 호스트의 것이다.
- `AggregateError` 의 **문구** `All promises were rejected` — V8 의 글자다.
- 동작 (2)에서 거부가 결과에 닿기까지 끼인 **줄 수**(4) — 명세의 잡 개수에서 나오지만, 이 문서는 그것을 **잡 하나하나로 대조하지 않았다**(관찰로 둔다).

### 그래서 이렇게 적으면 틀린다

- ✗ 「`Promise.all` 은 하나가 실패하면 나머지를 중단한다」 → ○ 「**결과만 거부된다.** 나머지는 끝까지 돈다」
- ✗ 「`Promise.race([])` 는 곧바로 끝난다」 → ○ 「**영원히 pending**」
- ✗ 「`Promise.all` 이 병렬로 실행해서 빠르다」 → ○ 「**이미 시작된 것을 모아 기다린다**」 — 속도는 **안 쟀다**
- ✗ 「`Promise.try` 는 ES2024」 → ○ 「**ES2025**」(finished proposals 표)

## 언제 쓰고 언제 안 쓰나

- **`all`** — 전부 있어야 다음으로 갈 수 있을 때. **하나 실패하면 전체가 실패**여도 될 때.
- **`allSettled`** — 부분 실패를 **모아서** 보고할 때(일괄 처리 결과 표).
- **`race`** — 타임아웃 · 「먼저 끝난 쪽」. ★ 입력이 비지 않게 한다. 진 쪽은 **계속 돈다**는 것을 안다.
- **`any`** — 여러 미러 중 **첫 성공**. 전부 실패면 `errors` 를 본다.
- **`withResolvers`** — `resolve` 를 **밖으로 꺼내야** 할 때(ES2024 가 되는 곳에서).
- **`try`** — 동기로 던질 수도 있는 함수를 **프라미스 하나로** 받을 때(ES2025 가 되는 곳에서).
- ★ **안 쓰는 자리** — 부작용이 있는 작업을 `all` 로 묶고 「실패하면 멈춘다」고 기대하는 것 · 취소가 필요한 곳(`AbortController` 를 같이 쓴다).

## 핵심 문장

1. ★★★ **`all` 은 전부 또는 첫 거부, `allSettled` 는 전부, `race` 는 첫 확정, `any` 는 첫 이행 또는 전부 거부**에 끝난다 — 16칸 중 **7칸**이 마지막 입력보다 먼저 끝났다.
2. ★★★ **빈 입력** — `all`·`allSettled` 는 곧바로 `[]`, `any` 는 곧바로 `AggregateError`(`errors 0`), **`race` 는 영원히 pending.**
3. ★★★ 조합기는 **아무것도 취소하지 않는다** — `all` 이 거부된 뒤에도 입력 작업이 **8 줄**을 더 찍고 끝까지 갔다.
4. ★★ 이미 확정된 입력 사이에서는 **먼저 넘긴 것이 이긴다**(200판 가짓수 `1`) — Go `select` 의 무작위와 반대다.
5. ★★ `withResolvers`(ES2024)는 `resolve` 를 밖으로 꺼내고, `try`(ES2025)는 `f` 를 **지금** 부르며 그 `throw` 를 거부로 바꾼다 — **두 node 판에는 둘 다 없다.**

## 관련 자료

- [ECMA-262 — Properties of the Promise Constructor](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-properties-of-the-promise-constructor) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md)
- [37 — Promise 상태 모델](../37-promise-state-model/2-summary.md) — ★ **경계**: 그쪽은 **프라미스 하나**의 전이·전파·보고, 여기는 **여럿을 묶는 네 방식**.
- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — `Promise.all` 이 이터러블을 **동기로** 읽는다. [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md) — `Array.fromAsync` 대 `Promise.all`.
- [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) — `AggregateError`. [36](../36-event-loop-and-microtasks/2-summary.md) — 잡 FIFO. [39 — `async`/`await`](../39-async-await/2-summary.md) — 순차 대 병렬.
- [Go 30 — `select`](../../../go/syntax/30-select-default-and-timeouts/2-summary.md) · [Go 28 — 고루틴](../../../go/syntax/28-goroutines-go-statement-cost-and-termination/2-summary.md) — 「기다리는 쪽」과 「도는 쪽」이 따로인 모양의 짝. [목록의 **41번 주제**](../41-cancellation-and-timeouts/)(취소).

## 용어 풀이

- **조합기** — 프라미스 여럿을 받아 하나를 돌려주는 정적 메서드.
- **확정(settle)** — 이행이든 거부든 결과가 정해지는 것.
- **남은 수(remaining elements)** — `all`·`allSettled`·`any` 가 세는 수. 1 에서 시작해 입력마다 +1, 다 읽은 뒤 −1 — 0 이 되면 끝난다.
- **`AggregateError`** — 여러 이유를 `errors` 배열로 든 오류(ES2021).
- **지연 프라미스(deferred)** — `resolve`·`reject` 를 밖에서 부를 수 있게 꺼내 둔 프라미스. `withResolvers` 가 표준 모양이다.
- **취소(cancellation)** — 도는 작업을 멈추게 하는 것. 프라미스에는 **없다.**

## 더 들어가면

- **`Promise.all` 의 `this` 와 `resolve` 조회** — 명세는 `GetPromiseResolve` 로 **생성자의 `resolve`** 를 한 번 읽는다. 상속한 생성자에서 무엇이 달라지나는 이 문서가 돌리지 않았다.
- **Promise 기반 취소 제안들** — 표준에 없다. 41번이 `AbortSignal` 을 다룬다.
