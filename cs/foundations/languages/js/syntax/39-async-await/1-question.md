# js/syntax/39 — `async`/`await`: 「부르면 어디까지 지금 돌고, `await` 는 어디서 멈추고, 둘을 언제 시작하나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(헤드리스) · Python 3.12 · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 로그 심기다** — 본문 줄 · 호출자의 다음 줄 · `await` 뒤에 로그를 심었다. **1번 · 3번 · 6번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`async` 함수를 부르면 무엇이 돌아오고 본문은 어디까지 지금 도나 — `await` 는 몇 틱 쉬나**
> ② ★★★ **순차와 병렬은 무엇으로 갈리나 — 시간이 아니라 시작 순서로**
> ③ **`try` 안의 `return` · `forEach` · 최상위 `await` 에서 무엇이 기대와 다르게 도나.**
>
> **선행** — [37](../37-promise-state-model/2-summary.md) · [36](../36-event-loop-and-microtasks/2-summary.md) · [20](../20-generators/2-summary.md) · [32](../32-error-handling-and-error/2-summary.md) · [38](../38-promise-combinators/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **3번은 행마다 `true`/`false` 하나**만 적어도 된다 — 그 판단이 이 주제의 절반이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 ECMA-262 가 정하나, node 가 정하나**」.
- ★★★ **시간에 관한 답은 하나도 없다.** 「병렬이 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 가지 반환 모양과 한 번의 호출 (예측) ★★★ 이 주제의 축

```js
// js36b-39a-async-basics.js
// [1] What does calling an async function return? [2] How far does its body run before the call returns?
// [3] Microtask ticks: a counter job requeues itself once per tick, and the probe reads the counter (@k = k ticks so far).
const show = (x) => (x instanceof Error ? x.constructor.name + " 「" + x.message + "」" : JSON.stringify(x));
const log = (s) => console.log(s);
(async () => {
  log("[1] return values");
  const inner = Promise.resolve("v");
  const cases = [
    ["async () => 1", async () => 1],
    ["async () => { throw Error('x') }", async () => { throw new Error("x"); }],
    ["async () => inner (a promise)", async () => inner],
    ["async () => {} (nothing)", async () => {}],
  ];
  for (const [label, f] of cases) {
    let r, how = "returned";
    try { r = f(); } catch (e) { how = "threw " + show(e); }
    let settled;
    try { settled = "fulfilled " + show(await r); } catch (e) { settled = "rejected " + show(e); }
    log("  " + label.padEnd(34) + how.padEnd(9) + (r instanceof Promise ? "a Promise" : typeof r) + " · same object as inner " + (r === inner) + " · " + settled);
  }

  log("[2] order of lines around a call");
  const order = [];
  async function f() {
    order.push("f: line 1");
    order.push("f: line 2");
    await null;
    order.push("f: after await");
  }
  order.push("caller: before f()");
  const pr = f();
  order.push("caller: after f()");
  await pr;
  log("  " + order.join(" > "));

  log("[3] microtask ticks until the step after X runs");
  const measure = (label, body) => new Promise((done) => {
    let tick = 0, stop = false;
    const counter = () => { if (stop) return; tick++; queueMicrotask(counter); };
    const ev = [];
    body(ev, () => tick).then(() => { stop = true; ev.push("caller's then @" + tick); });
    ev.push("caller's next line @" + tick);
    queueMicrotask(counter);
    setTimeout(() => { log("  " + label.padEnd(40) + ev.join(" > ")); done(); }, 0);
  });
  const settledP = Promise.resolve("v");
  const thenable = { then(onF) { onF("t"); } };
  await measure("await 1", async (ev, t) => { await 1; ev.push("after await @" + t()); });
  await measure("await settledP", async (ev, t) => { await settledP; ev.push("after await @" + t()); });
  await measure("await thenable", async (ev, t) => { await thenable; ev.push("after await @" + t()); });
  await measure("no await, return 'v'", async () => "v");
  await measure("return settledP", async () => settledP);
  await measure("return await settledP", async () => await settledP);
})();
```

- ★★★ `[1]` 네 행 각각 — `returned`/`threw`? 무엇을 돌려줬나? `inner` 와 같은 객체인가? 결국 무엇으로 확정되나?
- ★★★ `[2]` 의 한 줄은?

### 2. `await` 와 `return` 의 틱 (예측) ★★★

- ★★★ 1번 소스의 `[3]` — 여섯 행 각각의 `@k` 는?
- ★★ `await 1` 행에서 `caller's next line` 과 `after await` 중 무엇이 먼저 찍히나?

### 3. 작업 둘을 기다리는 네 가지 (예측) ★★★

```js
// js36b-39b-seq-vs-par.js
// Two independent jobs a and b. Each prints "start", waits three steps (a setTimeout 0 each), prints "end".
// No clock is read: the question is only whether b's "start" comes before a's "end".
const run = async (label, body) => {
  const lines = [];
  const job = async (name) => {
    lines.push(name + " start");
    for (let i = 0; i < 3; i++) await new Promise((r) => setTimeout(r, 0));
    lines.push(name + " end");
    return name;
  };
  const result = await body(job);
  const overlap = lines.indexOf("b start") < lines.indexOf("a end");
  console.log(label);
  console.log("  " + lines.join(" > ") + "   result " + JSON.stringify(result));
  console.log("  b started before a ended: " + overlap);
};
(async () => {
  await run("[1] await a(); await b();", async (job) => { const x = await job("a"); const y = await job("b"); return [x, y]; });
  await run("[2] await Promise.all([a(), b()])", async (job) => Promise.all([job("a"), job("b")]));
  await run("[3] const pa = a(), pb = b(); await pa; await pb;", async (job) => { const pa = job("a"), pb = job("b"); return [await pa, await pb]; });
  await run("[4] for (const n of ['a', 'b']) await job(n)", async (job) => { const out = []; for (const n of ["a", "b"]) out.push(await job(n)); return out; });
})();
```

- ★★★ 네 행 각각의 로그 순서와 `b started before a ended` 는?
- ★★ 결과 배열이 다른 행이 있나?

### 4. 먼저 부르고 차례로 기다리는데 뒤의 것이 먼저 거부되면 (예측) ★★★

```js
// js36b-39-h-early-reject.js
// a takes three steps and succeeds; b rejects after one step. Both are started first, then awaited (argv[2] says how).
// argv[3] === "hooks" installs node's process events and prints them on standard output.
const how = process.argv[2];
if (process.argv[3] === "hooks") {
  process.on("unhandledRejection", (r) => console.log("unhandledRejection(" + r.message + ")"));
  process.on("rejectionHandled", () => console.log("rejectionHandled"));
}
const step = () => new Promise((r) => setTimeout(r, 0));
const a = async () => { for (let i = 0; i < 3; i++) await step(); console.log("a end"); return "a"; };
const b = async () => { await step(); console.log("b rejects"); throw new Error("b"); };
(async () => {
  try {
    if (how === "one-by-one") { const pa = a(), pb = b(); await pa; await pb; }
    if (how === "all") { await Promise.all([a(), b()]); }
  } catch (e) {
    console.log("caught " + e.constructor.name + " 「" + e.message + "」");
  }
})();
```

```sh
# js36b-39c-early-reject.sh
#!/usr/bin/env bash
# Start both, then await: one-by-one (await pa; await pb) or Promise.all. With hooks: standard output. No hooks: exit code only.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
same=0
for how in one-by-one all; do
  echo "--- $how"
  out="$("$N20" js36b-39-h-early-reject.js "$how" hooks | paste -sd' ' -)"
  echo "  with hooks : $out"
  "$N20" js36b-39-h-early-reject.js "$how" > /dev/null 2>&1
  e=$?
  echo "  no hooks   : exit $e"
  o18="$("$N18" js36b-39-h-early-reject.js "$how" hooks | paste -sd' ' -)"
  "$N18" js36b-39-h-early-reject.js "$how" > /dev/null 2>&1
  [ "$o18 $?" = "$out $e" ] && same=$((same + 1))
done
echo ""
echo "rows where node18 gives the same two answers as node20: $same / 2"
```

- ★★★ `one-by-one` 과 `all` 각각 — 훅이 있을 때의 한 줄과 훅이 없을 때의 종료 코드는?
- ★ 마지막 줄의 `N / 2` 는?

### 5. `forEach` · `for…of` · `Promise.all(map)` (예측) ★★★

```js
// js36b-39d-foreach.js
// An async callback per item; each waits one step (setTimeout 0) and prints. When does the line after the loop print?
const step = () => new Promise((r) => setTimeout(r, 0));
const items = ["x", "y", "z"];
(async () => {
  const lines = [];
  console.log("[1] items.forEach(async (it) => { await step(); ... })");
  const ret = items.forEach(async (it) => { lines.push(it + " start"); await step(); lines.push(it + " done"); });
  lines.push("-- line after forEach · forEach returned " + ret);
  await step(); await step();
  console.log("  " + lines.join(" > "));

  lines.length = 0;
  console.log("[2] for (const it of items) { await step(); ... }");
  for (const it of items) { lines.push(it + " start"); await step(); lines.push(it + " done"); }
  lines.push("-- line after for...of");
  console.log("  " + lines.join(" > "));

  lines.length = 0;
  console.log("[3] await Promise.all(items.map(async (it) => { await step(); ... }))");
  await Promise.all(items.map(async (it) => { lines.push(it + " start"); await step(); lines.push(it + " done"); }));
  lines.push("-- line after Promise.all");
  console.log("  " + lines.join(" > "));
})();
```

- ★★★ 세 행 각각에서 `-- line after …` 는 어디쯤 찍히나? `forEach` 는 무엇을 돌려주나?

### 6. `try` 안에서 `return p` 와 `return await p` (예측) ★★★

```js
// js36b-39e-return-await.js
// A promise that rejects one step later. Returned from inside try, with and without await.
// Which lines run, and what does the caller get?
const step = () => new Promise((r) => setTimeout(r, 0));
const failLater = async () => { await step(); throw new Error("late"); };
const show = (x) => (x instanceof Error ? x.constructor.name + " 「" + x.message + "」" : JSON.stringify(x));
const variants = [
  ["return failLater()", async (L) => { try { return failLater(); } catch (e) { L.push("catch ran"); return "from catch"; } finally { L.push("finally ran"); } }],
  ["return await failLater()", async (L) => { try { return await failLater(); } catch (e) { L.push("catch ran"); return "from catch"; } finally { L.push("finally ran"); } }],
];
(async () => {
  for (const [label, f] of variants) {
    const L = [];
    const p = f(L);
    const done = p.then((v) => L.push("caller got fulfilled " + show(v)), (e) => L.push("caller got rejected " + show(e)));
    L.push("caller: call returned");
    await done;
    console.log(label);
    console.log("  " + L.join(" > "));
  }
})();
```

- ★★★ 두 변형 각각 — `catch ran` 이 찍히나? `finally ran` 은 `caller: call returned` 보다 먼저인가? 호출자는 무엇을 받나?

### 7. 최상위 `await` 는 어디서 되나 (경계) ★★

- ★★ 같은 글자를 `.mjs` 파일로 · `--input-type=module` 의 표준 입력으로 · `--input-type=commonjs` 의 표준 입력으로 주면 각각 어떻게 되나? CommonJS 판의 표준 출력은 몇 줄인가?
- ★ 그래서 기준은 확장자인가, 「모듈 코드인가」인가? 그 판정은 누구의 몫인가?

### 8. `async` 함수와 제너레이터 + 러너 (연결) ★★

- ★★ 20번의 `yield` 와 이 주제의 `await` 는 무엇이 대응하나? 거부는 러너에서 무엇으로 바뀌나?
- ★★ 옆에서 도는 다른 마이크로태스크와 섞인 **줄 순서까지** 같았나? 명세의 `Await` 와 러너의 한 줄은 어떤 두 걸음이 같은가?

### 9. 파이썬 코루틴 · Rust `Future` 와 (연결) ★★

- ★★ 파이썬 `async def` 함수를 부르기만 하면 본문이 도나? JS 는?
- ★ 그 차이가 4번의 함정과 어떻게 이어지나?
- ★ Rust `Future` 는 어느 쪽에 가깝나 — 이 문서는 그것을 돌렸나?

### 10. `Await` 의 세 걸음 (왜) ★★★

- ★★★ 명세의 `Await(arg)` 가 하는 세 걸음은?
- ★★ 그래서 값이 이미 있어도 쉬는 이유는? thenable 이 한 틱 더 드는 이유는?
- ★★ `try` 안의 `return p` 가 `catch` 를 건너뛰는 것은 32번의 어느 규칙과 같은가?

### 11. 순차 대 병렬 — 무엇을 근거로 말하나 (경계) ★★

- ★★ 3번의 `true` 를 만든 것은 `Promise.all` 인가, 다른 무엇인가?
- ★ 이 문서가 「병렬이 빠르다」를 쓰지 않는 이유는? 연혁 문서의 그림은 가로 길이에 대해 스스로 무엇이라 적나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
