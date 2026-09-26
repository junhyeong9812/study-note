# js/syntax/41 — 취소와 타임아웃: 「`abort()` 는 무엇을 멈추고, 무엇을 전달하고, 어디까지 번지나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(헤드리스) · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 로그 심기다** — 작업의 걸음마다, `abort()` 를 부른 자리에, 호출자가 받은 것에 로그를 심었다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`abort()` 를 부르면 이미 시작된 작업은 어떻게 되나 — 프라미스에는 무엇이 없나**
> ② ★★★ **`reason` 은 무엇이 되나 — `AbortError` 와 `TimeoutError`, 그리고 판마다 다른 것**
> ③ **취소는 어디까지 번지나 — `any` 로 세운 나무 · `fetch` 의 호출자와 서버.**
>
> **선행** — [39](../39-async-await/2-summary.md) · [38](../38-promise-combinators/2-summary.md) · [32](../32-error-handling-and-error/2-summary.md) · [40](../40-async-iteration-and-for-await/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 행마다 「`abort()` 뒤에 `job step 3` 이 찍히나」 하나**만 먼저 적어도 된다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 ECMA-262 가 정하나, DOM 표준이 정하나, node 가 정하나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 걸음 작업과 `abort()` (예측) ★★★ 이 주제의 축

```js
// js40b-41a-abort-mid-job.js
// A job of five steps (a setTimeout 0 each). The controller's abort() is called right after "step 2" is logged.
// [1] the job never looks at the signal  [2] the job calls signal.throwIfAborted() before each step
// [3] the caller wraps the job so that its own promise rejects on the abort event -- the job itself is as in [1]
// [0] what a Promise offers for stopping it
const show = (x) => (x instanceof Error || (typeof DOMException === "function" && x instanceof DOMException) ? x.constructor.name + " " + x.name + " 「" + x.message + "」" : JSON.stringify(x));
const step = () => new Promise((r) => setTimeout(r, 0));
const job = async (L, signal, checks, c) => {
  for (let i = 1; i <= 5; i++) {
    if (checks) signal.throwIfAborted();
    await step();
    L.push("job step " + i);
    if (i === 2) { c.abort(); L.push("-- abort() called"); }
  }
  L.push("job returns");
  return "job result";
};
const wrap = (p, signal) => new Promise((resolve, reject) => {
  signal.addEventListener("abort", () => reject(signal.reason), { once: true });
  p.then(resolve, reject);
});
const run = async (label, body) => {
  const L = [];
  const c = new AbortController();
  const p = body(L, c);
  let got;
  try { got = "caller got fulfilled " + show(await p); } catch (e) { got = "caller got rejected " + show(e); }
  L.push(got);
  for (let i = 0; i < 8; i++) await step();
  console.log(label);
  console.log("  " + L.join(" > "));
};
(async () => {
  console.log("[0] Promise.prototype: " + Object.getOwnPropertyNames(Promise.prototype).filter((k) => k !== "constructor").join(", ") + " · 'cancel' in it: " + ("cancel" in Promise.prototype));
  await run("[1] job ignores the signal", (L, c) => job(L, c.signal, false, c));
  await run("[2] job checks signal.throwIfAborted()", (L, c) => job(L, c.signal, true, c));
  await run("[3] caller's wrapper rejects on abort, job ignores the signal", (L, c) => wrap(job(L, c.signal, false, c), c.signal));
})();
```

- ★★★ `[1]`·`[2]`·`[3]` 각각 — `-- abort() called` 뒤에 무엇이 찍히나? 호출자는 무엇을 받나?
- ★★ `[0]` 의 한 줄은?

### 2. `reason` 격자 (예측) ★★★

```js
// js40b-41b-reasons.js
// What is signal.reason after each way of aborting -- and what does throwIfAborted() throw?
// Columns: constructor.name · name · message · code · instanceof Error
const row = (label, r) => {
  const cols = r && typeof r === "object"
    ? [r.constructor.name, r.name, "「" + r.message + "」", r.code === undefined ? "-" : r.code, r instanceof Error]
    : [typeof r, JSON.stringify(r)];
  console.log("  " + label.padEnd(40) + cols.join(" · "));
};
(async () => {
  console.log("[1] signal.reason");
  let c = new AbortController(); c.abort(); row("controller.abort()", c.signal.reason);
  c = new AbortController(); c.abort(undefined); row("controller.abort(undefined)", c.signal.reason);
  c = new AbortController(); c.abort("stop"); row('controller.abort("stop")', c.signal.reason);
  const mine = new Error("mine");
  c = new AbortController(); c.abort(mine); row("controller.abort(new Error(\"mine\"))", c.signal.reason);
  console.log("  " + "  same object as the Error passed in".padEnd(40) + (c.signal.reason === mine));
  row("AbortSignal.abort()", AbortSignal.abort().reason);
  const t = AbortSignal.timeout(0);
  const keep = setInterval(() => {}, 1000); // an interval timer, cleared once the timeout signal fires
  await new Promise((r) => t.addEventListener("abort", r, { once: true }));
  clearInterval(keep);
  row("AbortSignal.timeout(0), after abort", t.reason);

  console.log("[2] a second abort(), and AbortSignal.any");
  c = new AbortController(); c.abort("first"); c.abort("second"); row('abort("first") then abort("second")', c.signal.reason);
  const src = new AbortController();
  const dep = AbortSignal.any([src.signal, new AbortController().signal]);
  src.abort(mine);
  console.log("  " + "any([src, other]) after src.abort(e)".padEnd(40) + "aborted " + dep.aborted + " · reason === e " + (dep.reason === mine));

  console.log("[3] throwIfAborted()");
  const s = AbortSignal.abort("why");
  try { s.throwIfAborted(); console.log("  returned"); } catch (e) { console.log("  " + "on an aborted signal, threw".padEnd(40) + JSON.stringify(e) + " · same as reason " + (e === s.reason)); }
  const live = new AbortController().signal;
  console.log("  " + "on a live signal, returned".padEnd(40) + String(live.throwIfAborted()));

  console.log("[4] addEventListener with { signal } on a plain EventTarget -- calls after dispatching once");
  const et = new EventTarget();
  let calls = 0;
  const live2 = new AbortController();
  et.addEventListener("x", () => calls++, { signal: live2.signal });
  et.dispatchEvent(new Event("x"));
  console.log("  " + "live signal".padEnd(40) + calls);
  live2.abort(); calls = 0; et.dispatchEvent(new Event("x"));
  console.log("  " + "after that signal's abort()".padEnd(40) + calls);
  calls = 0; et.addEventListener("x", () => calls++, { signal: AbortSignal.abort() }); et.dispatchEvent(new Event("x"));
  console.log("  " + "registered with an aborted signal".padEnd(40) + calls);
})();
```

- ★★★ `[1]` 일곱 행 각각의 종류 · `name` · `code` 는? (`message` 는 판마다 다를 수 있다 — node 판으로 적어 보라)
- ★★ `[2]`·`[3]` 의 네 줄은?
- ★ `[4]` 의 세 숫자는?

### 3. `any` 로 세운 나무 (예측) ★★

```js
// js40b-41c-signal-tree.js
// The tree of Go's context probe (root -> a, b, c; a -> a1, b -> b1, c -> c1), built from AbortSignal.any.
// Every node has its own controller; its signal is any([parent's signal, own controller's signal]).
// Abort one node, then read aborted on all seven.
const build = () => {
  const n = {};
  const add = (name, parent) => {
    const own = new AbortController();
    n[name] = { own, signal: parent ? AbortSignal.any([n[parent].signal, own.signal]) : own.signal };
  };
  add("root"); add("a", "root"); add("a1", "a"); add("b", "root"); add("b1", "b"); add("c", "root"); add("c1", "c");
  return n;
};
for (const target of ["root", "a", "a1"]) {
  const n = build();
  const why = new Error("stop at " + target);
  n[target].own.abort(why);
  const names = Object.keys(n);
  const hit = names.filter((k) => n[k].signal.aborted);
  console.log("abort " + target.padEnd(5) + names.map((k) => k + "=" + n[k].signal.aborted).join(" ") + "   aborted " + hit.length + " / " + names.length +
    " · every aborted reason is the same object " + hit.every((k) => n[k].signal.reason === why));
}
```

- ★★ 세 줄 각각의 `aborted N / 7` 과 마지막 칸은?

### 4. `fetch` 를 네 방법으로 멈추면 (예측) ★★★

```js
// js40b-41-h-fetch.js
// fetch() against a local server whose /hang route never answers. argv[2] says how the request is stopped.
// Lines are printed in a fixed order after everything has settled (the two sides report in no fixed order).
// The timeout row leaves the server side out: whether the request got there before 50 ms is a race.
const http = require("http");
const how = process.argv[2];
const show = (x) => (x && typeof x === "object" ? x.constructor.name + " " + x.name + " 「" + x.message + "」" : JSON.stringify(x));
let received = 0, closed;
const closedP = new Promise((r) => { closed = r; });
const c = new AbortController();
const server = http.createServer((req, res) => {
  received++;
  res.on("close", () => closed("yes"));
  if (how === "abort-in-flight") c.abort();
  if (how === "abort-in-flight-reason") c.abort("mine");
});
server.listen(0, "127.0.0.1", async () => {
  const url = "http://127.0.0.1:" + server.address().port + "/hang";
  const signal = how === "already-aborted" ? AbortSignal.abort() : how === "timeout-50ms" ? AbortSignal.timeout(50) : c.signal;
  let got;
  try { got = "fulfilled " + (await fetch(url, { signal })).status; } catch (e) { got = "rejected " + show(e) + " · === signal.reason " + (e === signal.reason); }
  console.log("fetch " + got);
  if (how === "timeout-50ms") console.log("server: - (this row does not report the server side)");
  else console.log("server: requests received " + received + " · saw the connection close " + (received ? await closedP : "-"));
  server.close();
});
```

```js
// js40b-41-h-timeout-alone.js
// A timeout signal and an abort listener -- and nothing else in the program. argv[2] === "keep" adds an interval timer, cleared in the listener.
const s = AbortSignal.timeout(10);
s.addEventListener("abort", () => { console.log("abort event: " + s.reason.name); clearInterval(keep); });
const keep = process.argv[2] === "keep" ? setInterval(() => {}, 1000) : undefined;
console.log("end of the script");
```

- ★★★ 네 행 각각 — node 20 에서 `fetch` 는 무엇으로 거부되나? 서버는 요청을 받았나?
- ★★ node 18 과 갈리는 행이 있나? 있다면 무엇으로 갈리나?
- ★★ `js40b-41-h-timeout-alone.js` 를 `alone` 과 `keep` 으로 돌리면 각각 몇 줄이 찍히나?

### 5. 「취소」라는 말이 가리키는 것 (왜) ★★★

- ★★★ `Promise.prototype` 에는 무엇이 있고 무엇이 없나? 그것이 1번 `[1]` 의 결과와 어떻게 이어지나?
- ★★ 그러면 1번 `[2]` 에서 멈춘 것은 누구인가 — DOM 표준은 `throwIfAborted` 를 어떤 자리에 쓰라고 설명하나?

### 6. 이유를 가르는 법 (경계) ★★

- ★★ `catch (e)` 에서 취소와 시간 초과와 진짜 실패를 가르려면 `e.name` · `e.message` · `e === signal.reason` 중 무엇을 쓰나? 왜 하나는 안 되나?
- ★ `abort("stop")` 을 받은 쪽에서 `e.name` 은 무엇인가?

### 7. 층을 가른다 (경계) ★★

- ★★ `AbortController` · `DOMException` · `fetch` · 프라미스의 취소 부재 — 각각 ECMA-262 · DOM(과 fetch) 표준 · node 중 누구의 것인가?
- ★★ 4번 `alone` 과 `keep` 의 차이를 만든 것은 표준인가, node 인가?

### 8. Go `context` 와 나란히 (연결) ★★

- ★★ Go 34번의 `7 / 7` · `2 / 7` 과 3번의 결과는 같은가?
- ★ 둘이 **다른** 자리 하나(정리 호출)와 **같은** 자리 하나(협조적)는?

### 9. 데드라인 전파 정본과 이어 보기 (연결) ★★

- ★★ 4번 `abort-in-flight` 의 서버 쪽 두 칸은 데드라인 전파 문서의 어느 절이 말하는 것인가?
- ★ 그 문서와 이 문서의 경계는 어디인가?

### 10. `{ signal }` 로 단 리스너 (연결) ★

- ★ 2번 `[4]` 의 세 숫자는 web-api 20번이 Chrome 에서 잰 것과 같은가? 그래서 컨트롤러를 재사용하면 무엇이 되나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
