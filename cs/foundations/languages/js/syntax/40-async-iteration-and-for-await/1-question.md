# js/syntax/40 — 비동기 이터레이션: 「`for await` 는 떠날 때 무엇을 부르고, 무엇을 기다리고, 동기 이터러블을 어떻게 쓰나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(헤드리스) · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 격자다** — 루프 셋 × 끝나는 법 다섯. **1번 · 2번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`for await` 가 떠날 때 `return()` 과 `finally` 는 도나 — 동기 `for...of` 와 어느 칸이 다르나**
> ② ★★★ **미리 만든 프라미스 배열을 `for await` 로 돌면 무엇이 위험한가**
> ③ **어느 메서드를 찾나 · 몸통은 무엇을 받나 · `next()` 를 겹쳐 부르면.**
>
> **선행** — [20](../20-generators/2-summary.md) · [19](../19-iterable-protocol-and-for-of/2-summary.md) · [39](../39-async-await/2-summary.md) · [37](../37-promise-state-model/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸마다 `yes`/`no` 두 개**만 적어도 된다 — 그 판단이 이 주제의 절반이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 ECMA-262 가 정하나, node 가 정하나, 이 판의 엔진이 정하나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 루프와 끝나는 법의 격자 (예측) ★★★ 이 주제의 축

```js
// js40b-40a-close-grid.js
// Three loops x five ways the loop ends. In each cell: is the iterator's return() called? does the generator's finally run?
//   A  for...of   over a sync generator            (values 1, 2, 3)
//   B  for await  over an async generator          (values 1, 2, 3)
//   C  for await  over a sync generator of promises (Promise.resolve(1), ...(2), ...(3))
// The loop body acts on the second value. In the "rejects" column the second value is a rejected promise.
const rejected = () => { const p = Promise.reject(new Error("rejected value")); p.catch(() => {}); return p; };
function* syncGen(L, vals) { try { for (const v of vals) yield v; } finally { L.push("finally"); } }
async function* asyncGen(L, vals) { try { for (const v of vals) yield v; } finally { L.push("finally"); } }
const watch = (it, L) => { const r = it.return; it.return = function (v) { L.push("return()"); return r.call(this, v); }; return it; };
const show = (v) => (v instanceof Promise ? "a Promise" : String(v));
const exits = ["break", "return", "throw", "end", "rejects"];
const values = (exit, wrap) => [1, 2, 3].map((v) => (exit === "rejects" && v === 2 ? rejected() : wrap ? Promise.resolve(v) : v));
const act = (exit, v, L) => {
  L.push("got " + show(v));
  if (v !== 2) return "";
  if (exit === "break") return "break";
  if (exit === "return") return "return";
  if (exit === "throw") throw new Error("body threw");
  return "";
};
const loops = {
  "A for...of + sync generator": (exit, L) => {
    const run = () => { for (const v of watch(syncGen(L, values(exit, false)), L)) { const a = act(exit, v, L); if (a === "break") break; if (a === "return") return "returned"; } return "completed"; };
    try { const r = run(); return Promise.resolve(r === "completed" && exit === "break" ? "left by break" : r); } catch (e) { return Promise.resolve("caught " + e.message); }
  },
  "B for await + async generator": async (exit, L) => {
    const run = async () => { for await (const v of watch(asyncGen(L, values(exit, false)), L)) { const a = act(exit, v, L); if (a === "break") break; if (a === "return") return "returned"; } return "completed"; };
    try { const r = await run(); return r === "completed" && exit === "break" ? "left by break" : r; } catch (e) { return "caught " + e.message; }
  },
  "C for await + sync generator of promises": async (exit, L) => {
    const run = async () => { for await (const v of watch(syncGen(L, values(exit, true)), L)) { const a = act(exit, v, L); if (a === "break") break; if (a === "return") return "returned"; } return "completed"; };
    try { const r = await run(); return r === "completed" && exit === "break" ? "left by break" : r; } catch (e) { return "caught " + e.message; }
  },
};
(async () => {
  const cells = {};
  for (const [name, loop] of Object.entries(loops)) {
    console.log(name);
    for (const exit of exits) {
      const L = [];
      const outcome = await loop(exit, L);
      const key = [L.includes("return()"), L.includes("finally")];
      cells[name[0] + exit] = key.join();
      console.log("  " + exit.padEnd(8) + ("return() " + (key[0] ? "yes" : "no ")).padEnd(13) + ("finally " + (key[1] ? "yes" : "no ")).padEnd(13) + outcome.padEnd(24) + L.join(" > "));
    }
  }
  let n = 0, m = 0;
  for (const row of ["B", "C"]) for (const exit of exits) { m++; if (cells[row + exit] !== cells["A" + exit]) n++; }
  console.log("cells where a for await row differs from row A in (return() called, finally ran): " + n + " / " + m);
})();
```

- ★★★ 15칸 각각 — `return()` 이 불리나? `finally` 가 도나?
- ★★ 마지막 줄의 `N / 10` 은?

### 2. 1번의 `rejects` 열 — 세 행과 세 판 (경계) ★★★

- ★★★ A · B · C 행의 `rejects` 칸에서 **거부된 프라미스를 기다린 것은 각각 누구인가**?
- ★★★ C 행 `rejects` 칸이 node 18·20 과 Chrome 151 에서 같았나? 다르다면 무엇이 그 차이를 정하나?
- ★ 그 규칙은 ECMA-262 의 몇 번째 판 본문에서 보이나?

### 3. 미리 만든 프라미스 배열 (예측) ★★★

```js
// js40b-40-h-premade.js
// Promises made up front, then consumed one by one with for await (argv[2] says how).
//   a: succeeds after three steps · b: rejects after one step · c: succeeds after two steps · d: rejects after three steps
// argv[3] === "hooks" installs node's process events and prints them on standard output.
const how = process.argv[2];
if (process.argv[3] === "hooks") {
  process.on("unhandledRejection", (r) => console.log("unhandledRejection(" + r.message + ")"));
  process.on("rejectionHandled", () => console.log("rejectionHandled"));
}
const steps = (n) => new Promise((r) => { const go = (k) => (k === 0 ? r() : setTimeout(go, 0, k - 1)); go(n); });
const ok = async (name, n) => { await steps(n); console.log(name + " settles"); return name; };
const bad = async (name, n) => { await steps(n); console.log(name + " rejects"); throw new Error(name); };
(async () => {
  try {
    if (how === "array-a-b-c") { for await (const v of [ok("a", 3), bad("b", 1), ok("c", 2)]) console.log("got " + v); }
    if (how === "array-b-d") { for await (const v of [bad("b", 1), bad("d", 3)]) console.log("got " + v); }
    if (how === "all-a-b-c") { for (const v of await Promise.all([ok("a", 3), bad("b", 1), ok("c", 2)])) console.log("got " + v); }
    if (how === "gen-a-b-c") {
      async function* lazy() { yield ok("a", 3); yield bad("b", 1); yield ok("c", 2); }
      for await (const v of lazy()) console.log("got " + v);
    }
  } catch (e) {
    console.log("caught " + e.constructor.name + " 「" + e.message + "」");
  }
})();
```

```sh
# js40b-40b-premade.sh
#!/usr/bin/env bash
# Promises made up front and consumed with for await -- against Promise.all and a lazy async generator.
# With hooks: standard output. No hooks: exit code only.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
same=0; t=0
for how in array-a-b-c array-b-d all-a-b-c gen-a-b-c; do
  t=$((t + 1))
  echo "--- $how"
  out="$("$N20" js40b-40-h-premade.js "$how" hooks | paste -sd' ' -)"
  echo "  with hooks : $out"
  "$N20" js40b-40-h-premade.js "$how" > /dev/null 2>&1
  e=$?
  echo "  no hooks   : exit $e"
  o18="$("$N18" js40b-40-h-premade.js "$how" hooks | paste -sd' ' -)"
  "$N18" js40b-40-h-premade.js "$how" > /dev/null 2>&1
  [ "$o18 $?" = "$out $e" ] && same=$((same + 1))
done
echo ""
echo "rows where node18 gives the same two answers as node20: $same / $t"
```

- ★★★ 네 행 각각 — 훅이 있을 때의 한 줄과 훅이 없을 때의 종료 코드는?
- ★★ `gen-a-b-c` 에서 `c` 는 시작하나?

### 4. 어느 메서드를 읽나 (예측) ★★

```js
// js40b-40c-which-protocol.js
// Which method does each loop look up? Getters log every read of Symbol.asyncIterator / Symbol.iterator.
const show = (e) => e.constructor.name + " 「" + e.message + "」";
const make = (L, withAsync, withSync) => {
  const o = {};
  if (withAsync) Object.defineProperty(o, Symbol.asyncIterator, { get() { L.push("get asyncIterator"); return async function* () { yield "from async"; }; } });
  if (withSync) Object.defineProperty(o, Symbol.iterator, { get() { L.push("get iterator"); return function* () { yield "from sync"; }; } });
  return o;
};
const cases = [["both", true, true], ["asyncIterator only", true, false], ["iterator only", false, true], ["neither", false, false]];
(async () => {
  console.log("[1] for await ... of");
  for (const [label, a, s] of cases) {
    const L = [];
    try { for await (const v of make(L, a, s)) L.push("got " + v); } catch (e) { L.push(show(e)); }
    console.log("  " + label.padEnd(20) + L.join(" > "));
  }
  console.log("[2] for ... of");
  for (const [label, a, s] of cases) {
    const L = [];
    try { for (const v of make(L, a, s)) L.push("got " + v); } catch (e) { L.push(show(e)); }
    console.log("  " + label.padEnd(20) + L.join(" > "));
  }
  console.log("[3] an async generator object");
  async function* ag() { yield 1; }
  const g = ag();
  console.log("  typeof g[Symbol.asyncIterator] " + typeof g[Symbol.asyncIterator] + " · typeof g[Symbol.iterator] " + typeof g[Symbol.iterator] + " · g[Symbol.asyncIterator]() === g " + (g[Symbol.asyncIterator]() === g));
  try { for (const v of ag()) console.log(v); } catch (e) { console.log("  for...of over it: " + show(e)); }
  try { console.log([...ag()]); } catch (e) { console.log("  spread of it:     " + show(e)); }

  console.log("[4] break out of for await -- the generator's finally contains an await");
  const L = [];
  const step = () => new Promise((r) => setTimeout(r, 0));
  async function* withCleanup() { try { yield 1; yield 2; } finally { L.push("finally start"); await step(); L.push("finally end"); } }
  for await (const v of withCleanup()) { L.push("got " + v); break; }
  L.push("line after the loop");
  console.log("  " + L.join(" > "));
})();
```

- ★★ `[1]`·`[2]` 여덟 행 각각의 로그는?
- ★★ `[3]` 의 세 줄은? `[4]` 의 한 줄에서 `line after the loop` 는 어디에 오나?

### 5. 몸통이 받는 것과 틱 · 겹쳐 부른 `next()` (예측) ★★

```js
// js40b-40d-yield-and-ticks.js
// [1] What does the loop body receive, and after how many microtask ticks does it first run?
//     A counter job requeues itself once per tick; @k = k ticks since the loop started.
// [2] it.next() on an async generator, called three times in a row without waiting.
const settledP = Promise.resolve("v");
const kind = (v) => (v instanceof Promise ? "a Promise" : typeof v + " " + JSON.stringify(v));
const measure = (label, loop) => new Promise((done) => {
  let tick = 0, stop = false;
  const counter = () => { if (stop) return; tick++; queueMicrotask(counter); };
  const ev = [];
  queueMicrotask(counter);
  loop((v) => ev.push("body got " + kind(v) + " @" + tick)).then(() => { stop = true; });
  setTimeout(() => { console.log("  " + label.padEnd(44) + ev.join(" > ")); done(); }, 0);
});
(async () => {
  console.log("[1] one value, one loop");
  await measure("async gen: yield 1", async (f) => { async function* g() { yield 1; } for await (const v of g()) f(v); });
  await measure("async gen: yield settledP", async (f) => { async function* g() { yield settledP; } for await (const v of g()) f(v); });
  await measure("async gen: yield await settledP", async (f) => { async function* g() { yield await settledP; } for await (const v of g()) f(v); });
  await measure("for await over [1]", async (f) => { for await (const v of [1]) f(v); });
  await measure("for await over [settledP]", async (f) => { for await (const v of [settledP]) f(v); });
  await measure("for...of over sync gen: yield settledP", async (f) => { function* g() { yield settledP; } for (const v of g()) f(v); });

  console.log("[2] three it.next() calls in a row");
  const L = [];
  const step = () => new Promise((r) => setTimeout(r, 0));
  async function* slow() { for (let i = 1; i <= 3; i++) { L.push("body: step " + i + " begins"); await step(); L.push("body: yield " + i); yield i; } }
  const it = slow();
  const ps = [it.next(), it.next(), it.next()];
  L.push("caller: three next() calls returned " + ps.map((p) => (p instanceof Promise ? "Promise" : typeof p)).join(","));
  ps.forEach((p, i) => p.then((r) => L.push("caller: next#" + (i + 1) + " -> " + JSON.stringify(r))));
  await Promise.all(ps);
  await step();
  console.log("  " + L.join("\n  "));
})();
```

- ★★ `[1]` 여섯 행 각각 — 몸통이 받은 것의 종류와 `@k` 는?
- ★★ `[2]` 에서 `body: step 2 begins` 는 `caller: next#1 -> …` 보다 먼저인가?

### 6. 루프를 일찍 떠날 때 명세가 부르는 연산 (왜) ★★★

- ★★★ 루프를 일찍 떠날 때 명세가 부르는 연산은? 그 연산은 `return()` 의 결과를 어떻게 다루나?
- ★★ 그래서 `finally` 안의 `await` 는 루프 뒤의 줄과 어떤 순서가 되나?

### 7. async generator 의 `yield` 가 명세에서 하는 일 (왜) ★★

- ★★ async generator 의 `yield x` 가 명세에서 무엇으로 바뀌나?
- ★ 그래서 `yield promise` 와 `yield await promise` 는 몸통이 받는 것이 같은가, 틱이 같은가?

### 8. 동기 `for...of` 와 이어 보기 (연결) ★★

- ★★ 19번 격자에서 `return()` 을 부른 소비자 수는 17 중 몇이었나? 그중 이 문서의 A 행이 다시 보인 것은?
- ★★ 20번의 `return()` 과 `finally` 규칙은 B 행의 어느 칸에 그대로 나타나나?

### 9. 이미 시작한 것을 기다리는 법 (연결) ★★

- ★★ 3번의 `array-a-b-c` 는 39번의 어느 함정과 같은 모양인가?
- ★ 그 함정을 피하는 두 방법은 무엇이고, 둘은 무엇이 다른가(언제 시작하나)?

### 10. `next()` 를 겹쳐 부르는 것과 20번의 재진입 (경계) ★

- ★ async generator 에서 `next()` 를 세 번 겹쳐 불렀을 때와, 동기 제너레이터 본문에서 자기 `next()` 를 불렀을 때 각각 무엇이 되나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
