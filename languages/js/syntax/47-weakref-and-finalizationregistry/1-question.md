# js/syntax/47 — `WeakRef`·`FinalizationRegistry`: 「약한 참조로 무엇이 보이나 — 그중 명세가 약속한 것은 어느 쪽인가」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1 · v20.19.6(`--expose-gc` 유무) · Google Chrome 151(`--js-flags=--expose-gc` 유무) · Python 3.12.3 · x86-64 Linux.
>
> ★★★ **이 주제의 본체는 층 가르기다** — 같은 숫자가 **명세 보장 / 호스트 / 이 판의 관찰** 중 어디에 속하나. 도구는 관찰 격자(8칸 × 20판 × 판 넷). **1번 · 2번 · 5번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`gc()` 가 있고 없음 · 부르고 안 부름 · 기다림의 종류마다 무엇이 보이나**
> ② ★★★ **「동기 실행이 끝날 때까지 살려 둔다」 의 끝은 어디인가 · `deref()` 는 무엇을 하나**
> ③ ★★ **`gc()` 없이 기대할 수 있는 것 · CPython 과의 차이.**
>
> **선행** — [23](../23-map-set-and-weak-collections/2-summary.md) · [06](../06-scope-and-closures/2-summary.md) · [36](../36-event-loop-and-microtasks/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸마다 「`0/20` · `20/20` · 그 사이」 셋 중 하나**만 먼저 적어도 된다 — 그리고 **그 칸이 어느 층의 답인지**를 옆에 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 숫자가 다른 엔진에서 달라져도 명세 위반인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 관찰 격자 (예측) ★★★ 이 주제의 축

```js
// js44b-47a-observe-grid.js
// What a WeakRef and a FinalizationRegistry let a program see. One cell = ROUNDS rounds; each round makes a new target
// that nothing else holds, registers it, and keeps only a WeakRef to it. Then it
//   waits:      not at all | await null once | await null ten times | one setTimeout(0)
//   does:       nothing | calls gc()
//   reads:      ref.deref() -- is it undefined?
//   and last waits up to ten more setTimeout(0) turns for the cleanup callback.
// A cell prints in how many of the ROUNDS rounds deref() was undefined, and in how many the callback ran.
// The "gc()" rows need a global gc(); without one they print n/a.
const ROUNDS = 20;
const turn = () => new Promise((r) => setTimeout(r, 0));
const waits = {
  "no wait": null,
  "await null x1": async () => { await null; },
  "await null x10": async () => { for (let i = 0; i < 10; i++) await null; },
  "setTimeout 0": turn,
};
const actions = {
  "nothing": () => {},
  "gc()": () => gc(),
};
async function round(wait, action) {
  let called = false;
  const reg = new FinalizationRegistry(() => { called = true; });
  let ref;
  (() => { const target = {}; ref = new WeakRef(target); reg.register(target, "held"); })();
  if (waits[wait]) await waits[wait]();
  actions[action]();
  const gone = ref.deref() === undefined;
  for (let i = 0; i < 10 && !called; i++) await turn();
  return { gone, called };
}
(async () => {
  const hasGc = typeof gc === "function";
  console.log("typeof gc: " + typeof gc + " · " + ROUNDS + " rounds per cell");
  console.log("  " + "does".padEnd(10) + "waits".padEnd(16) + "deref() undefined".padEnd(20) + "callback ran");
  let seen = 0, cells = 0;
  for (const action of Object.keys(actions)) {
    for (const wait of Object.keys(waits)) {
      if (action === "gc()" && !hasGc) { console.log("  " + action.padEnd(10) + wait.padEnd(16) + "n/a"); continue; }
      let gone = 0, called = 0;
      for (let r = 0; r < ROUNDS; r++) { const o = await round(wait, action); gone += o.gone; called += o.called; }
      cells++;
      if (gone > 0 || called > 0) seen++;
      console.log("  " + action.padEnd(10) + wait.padEnd(16) + (gone + "/" + ROUNDS).padEnd(20) + called + "/" + ROUNDS);
    }
  }
  console.log("cells where at least one round saw deref() undefined or the callback: " + seen + " / " + cells);
})();
```

```sh
# js44b-47a-observe.sh
#!/usr/bin/env bash
# The observation grid (js44b-47a-observe-grid.js) with and without a global gc():
# node20, node20 --expose-gc, Chrome 151 with --js-flags=--expose-gc in full,
# then node18 --expose-gc and Chrome 151 without the flag compared with the run that has the same gc() situation.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
a="$("$N20" js44b-47a-observe-grid.js)" || exit 1
b="$("$N20" --expose-gc js44b-47a-observe-grid.js)" || exit 1
c="$(./js44b-browser.sh --gc js44b-47a-observe-grid.js)" || exit 1
d="$("$N18" --expose-gc js44b-47a-observe-grid.js)" || exit 1
e="$(./js44b-browser.sh js44b-47a-observe-grid.js)" || exit 1
echo "--- node20"; printf '%s\n' "$a"
echo "--- node20 --expose-gc"; printf '%s\n' "$b"
echo "--- Chrome 151 --js-flags=--expose-gc"; printf '%s\n' "$c"
echo ""
[ "$d" = "$b" ] && s=yes || s=no
echo "node18 --expose-gc prints the same as node20 --expose-gc: $s"
[ "$e" = "$a" ] && s=yes || s=no
echo "Chrome 151 without the flag prints the same as node20 without it: $s"
```

- ★★★ `gc()` 가 없는 판에서 네 칸은? 요약 줄의 `N / 4` 는?
- ★★★ `gc()` 가 있는 판에서 `gc()` 행 네 칸은 각각? 요약 줄의 `N / 8` 은?
- ★★ node 18 과 Chrome 151 은 비교 두 줄에서 무엇이라 나오나?

### 2. 한 판의 다섯 지점 (예측) ★★★

```js
// js44b-47c-kept-alive.js
// Needs a global gc(). One round: make a target that only a WeakRef points to, then read deref() at five points.
// Prints, for each point, in how many of ROUNDS rounds deref() gave the object back.
const ROUNDS = 20;
const turn = () => new Promise((r) => setTimeout(r, 0));
const points = ["[1] same job: gc(), then deref()",
  "[2] after await null: gc(), then deref()",
  "[3] next setTimeout turn: deref() before any gc()",
  "[4]   same turn, after that deref(): gc(), then deref()",
  "[5] one more setTimeout turn: gc(), then deref()"];
async function round() {
  let ref;
  (() => { ref = new WeakRef({}); })();
  const got = [];
  const read = () => got.push(ref.deref() !== undefined);
  gc(); read();
  await null; gc(); read();
  await turn(); read();
  gc(); read();
  await turn(); gc(); read();
  return got;
}
(async () => {
  console.log("typeof gc: " + typeof gc + " · " + ROUNDS + " rounds");
  const count = points.map(() => 0);
  for (let r = 0; r < ROUNDS; r++) (await round()).forEach((alive, i) => { count[i] += alive; });
  points.forEach((p, i) => console.log("  " + p.padEnd(56) + "object " + count[i] + "/" + ROUNDS));
})();
```

- ★★★ `[1]`\~`[5]` 각각 `object N/20` 의 N 은?

### 3. 등록과 취소 (예측) ★

```js
// js44b-47d-registry-api.js
// What the FinalizationRegistry and WeakRef objects offer, and what unregister() answers.
const run = (label, f) => {
  let r;
  try { r = "ok " + String(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(52) + r);
};
const own = (o) => Object.getOwnPropertyNames(o).join(" ");
console.log("[1] own properties");
run("WeakRef.prototype", () => own(WeakRef.prototype));
run("FinalizationRegistry.prototype", () => own(FinalizationRegistry.prototype));
console.log("[2] register and unregister");
const reg = new FinalizationRegistry(() => {});
const token = {};
run("reg.register({}, 'h1', token)", () => reg.register({}, "h1", token));
run("reg.register({}, 'h2', token)", () => reg.register({}, "h2", token));
run("reg.unregister(token)   (first time)", () => reg.unregister(token));
run("reg.unregister(token)   (second time)", () => reg.unregister(token));
run("reg.unregister({})   (a token never used)", () => reg.unregister({}));
run("reg.unregister(1)", () => reg.unregister(1));
const t = {};
run("reg.register(t, 'h', t)   (token = target)", () => reg.register(t, "h", t));
run("reg.unregister(t)", () => reg.unregister(t));
run("reg.register({}, 'h', 1)   (a number as token)", () => reg.register({}, "h", 1));
run("new FinalizationRegistry()", () => new FinalizationRegistry());
```

- ★ `[1]` 두 줄과 `[2]` 여덟 줄은?

### 4. CPython 에서 같은 질문 (예측) ★★

```python
# js44b-47e-python.py
# The same question in CPython: a weakref.ref and a weakref.finalize on an object, then del.
# [1]-[2] an object that only one name holds; [3]-[5] an object that holds itself (a reference cycle).
import gc
import weakref


class Box:
    pass


b = Box()
r = weakref.ref(b)
weakref.finalize(b, print, "  finalize callback for b ran")
print("[1] before del b: r() is alive ->", r() is not None)
del b
print("[2] the line after del b: r() ->", r())

c = Box()
c.me = c
r2 = weakref.ref(c)
weakref.finalize(c, print, "  finalize callback for c ran")
del c
print("[3] the line after del c (c.me = c): r2() is None ->", r2() is None)
print("[4] gc.collect() found", gc.collect(), "unreachable objects")
print("[5] after gc.collect(): r2() is None ->", r2() is None)
```

- ★★ 일곱 줄은 어떤 순서로 나오나? 콜백 두 줄은 각각 어느 줄 사이에 끼나?

### 5. 층을 가른다 (경계) ★★★

- ★★★ 1번과 2번의 칸 가운데 **다른 엔진에서 달라지면 명세 위반**인 것과 **달라져도 되는** 것을 갈라라. `gc()` 자체는 어느 층인가?

### 6. 「동기 실행」 의 끝 (왜) ★★★

- ★★★ 1번의 `await null x10` 행과 `setTimeout 0` 행의 결과를 명세의 `ClearKeptObjects` 와 HTML 의 한 문장으로 설명하라.

### 7. `gc()` 없이 할당 압력만 주면 (경계) ★★

```js
// js44b-47b-pressure-grid.js
// js44b-47a-observe-grid.js with gc() replaced by allocation "pressure": the round allocates about 200 000
// short-lived objects, so a collection may start on its own. The whole grid (four waits x ROUNDS rounds) runs RUNS times;
// one line per run: for each wait, "deref() undefined N · callback ran M" out of ROUNDS rounds.
const ROUNDS = 20, RUNS = 5;
const turn = () => new Promise((r) => setTimeout(r, 0));
const waits = {
  "no wait": null,
  "await null x1": async () => { await null; },
  "await null x10": async () => { for (let i = 0; i < 10; i++) await null; },
  "setTimeout 0": turn,
};
const pressure = () => { let junk = []; for (let i = 0; i < 200000; i++) junk.push({ i }); junk = null; };
async function round(wait) {
  let called = false;
  const reg = new FinalizationRegistry(() => { called = true; });
  let ref;
  (() => { const target = {}; ref = new WeakRef(target); reg.register(target, "held"); })();
  if (waits[wait]) await waits[wait]();
  pressure();
  const gone = ref.deref() === undefined;
  for (let i = 0; i < 10 && !called; i++) await turn();
  return { gone, called };
}
(async () => {
  console.log("typeof gc: " + typeof gc + " · " + ROUNDS + " rounds per cell · each cell is: deref() undefined / callback ran");
  console.log("       " + Object.keys(waits).map((w) => w.padEnd(17)).join("").trimEnd());
  let anyGone = 0, anyCalled = 0;
  for (let run = 1; run <= RUNS; run++) {
    const cells = [];
    let g = false, c = false;
    for (const wait of Object.keys(waits)) {
      let gone = 0, called = 0;
      for (let r = 0; r < ROUNDS; r++) { const o = await round(wait); gone += o.gone; called += o.called; }
      if (gone) g = true;
      if (called) c = true;
      cells.push((gone + " / " + called).padEnd(17));
    }
    anyGone += g; anyCalled += c;
    console.log("run " + run + "  " + cells.join("").trimEnd());
  }
  console.log("runs with deref() undefined in at least one round: " + anyGone + " / " + RUNS +
    " · runs with the callback in at least one round: " + anyCalled + " / " + RUNS);
})();
```

- ★★ 이 블록은 왜 「흔들리는 칸」 으로 선언해야 하나? 무엇까지는 근거로 쓸 수 있나?

### 8. `WeakMap` 과 무엇이 다른가 (연결) ★★

- ★★ 23번의 `WeakMap` 과 견주어, `WeakRef` 가 **새로 보이게 만드는 것**은 무엇인가? 그것이 명세가 이 절을 "may" 로 적는 이유와 어떻게 이어지나?

### 9. 정리를 무엇에 맡기나 (연결) ★★

- ★★ 4번의 CPython 결과와 1번의 결과를 견주면, 「객체가 사라질 때 자원을 닫는다」 는 설계는 두 언어에서 각각 무엇에 기대나? JS 에서는 무엇으로 대신하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
