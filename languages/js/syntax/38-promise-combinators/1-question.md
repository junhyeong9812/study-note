# js/syntax/38 — Promise 조합기: 「무엇을 기다리고, 언제 끝나고, 나머지는 어떻게 되나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(헤드리스) · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 조합기 4 × 입력 모양 4 격자다** — **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **네 조합기는 각각 언제 끝나고 무엇을 돌려주나 — 빈 입력에서는?**
> ② ★★ **조합기가 끝난 뒤 나머지 입력은 어떻게 되나**
> ③ **`withResolvers`·`try` 는 무엇을 줄이고, 어느 판부터인가.**
>
> **선행** — [37](../37-promise-state-model/2-summary.md) · [19](../19-iterable-protocol-and-for-of/2-summary.md) · [26](../26-array-search-flatten-and-create/2-summary.md) · [32](../32-error-handling-and-error/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1\~4 · 7)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 16칸 각각 「몇 단계째에 · 이행/거부 · 무엇」** 을 적어라. 안 끝나는 칸이 있으면 그렇게 적는다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 ECMA-262 가 정하나, 이 판의 관찰인가**」.
- ★★★ **속도에 관한 답은 하나도 없다** — 「`all` 이 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 조합기 4 × 입력 모양 4 (예측) ★★★ 이 주제의 축

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

- ★★★ 네 모양 각각에서 네 조합기가 **몇 단계째에** 무엇으로 끝나나?
- ★★★ `empty` 모양의 네 칸은?
- ★★ 마지막 줄의 두 `N / 16` 은?

### 2. 첫 걸음에서 던지는 작업 하나와 긴 작업 둘 (예측) ★★★

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

- ★★★ `>> all rejected …` 줄은 어디쯤 찍히나? 그 뒤에 `A`·`C` 의 줄이 더 찍히나?
- ★★ 각 조합기의 마지막 줄의 숫자는?

### 3. 이미 이행한 두 입력의 `race` — 200판 (예측) ★★

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

- ★★ 두 순서 각각의 가짓수와 결과는?

### 4. `withResolvers` 와 `try` — Chrome 151 (예측) ★★

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

- ★★ `[1]` 의 네 줄은?
- ★★★ `[2]` 세 방식 각각에서 `callback runs` 와 `call returned` 중 무엇이 먼저 찍히나? 거부로 받나?
- ★★ `[3]` 과 `[4]` 는?

### 5. 빈 입력에서 `race` 만 다른 이유 (왜) ★★★

- ★★★ `all`·`allSettled`·`any` 가 세는 「남은 수」는 어디서 시작해 언제 0 이 되나? 빈 입력이면?
- ★★ `race` 의 알고리즘에는 무엇이 없나? 명세 노트는 무엇이라 적나?

### 6. 조합기는 왜 아무것도 취소하지 않나 (왜) ★★★

- ★★★ 조합기가 입력에게 하는 일은 무엇이고, 하지 않는 일은 무엇인가?
- ★★ 그러면 입력 작업을 「동시에 시작시킨」 것은 누구인가?

### 7. 끝없는 제너레이터를 `Promise.all` 에 (예측) ★★

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

- ★★ 첫 줄의 숫자는? `Promise.all` 이 던지나, 프라미스를 돌려주나? 둘째 줄은?
- ★★ 19번이 `Promise.all(it)` 을 부른 바로 다음 줄에서 본 것과 어떻게 이어지나?
- ★ 26번의 `Array.fromAsync(gen())` 과 `Promise.all([...gen()])` 은 `next` 를 부르는 순서가 어떻게 달랐나?

### 8. JS `race` 와 Go `select` (연결) ★★

- ★★ 준비된 입력이 둘일 때 JS `race` 와 Go `select` 는 각각 무엇을 고르나? 가짓수는?
- ★ 그 차이는 무엇이 정하나 — 명세인가 구현인가?

### 9. 판 경계 (경계) ★★

- ★★ `allSettled`·`any`·`withResolvers`·`try` 는 각각 ES 몇 판인가? 두 node 판에 없는 것은?
- ★ `any` 가 거부할 때 던지는 오류의 이름과 `errors` 의 순서는? 그 오류의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
