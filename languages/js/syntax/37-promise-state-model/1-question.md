# js/syntax/37 — Promise 상태 모델: 「누가 상태를 정하고, 값과 거부는 어디로 흐르고, 아무도 안 받은 거부는 누가 알리나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151(헤드리스) · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 주제의 본체는 전수 격자 셋과 틱 세기다** — **1번 · 2번 · 5번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **상태는 언제 정해지고, 정해진 뒤의 호출은 어떻게 되나 — thenable 은 틱이 몇 개 드나**
> ② **`then` 사슬과 `.finally()` 에서 값·예외는 어디로 흐르나**
> ③ ★★★ **거부를 아무도 안 받으면 언제, 누가 알리나 — 언어인가 호스트인가.**
>
> **선행** — [36](../36-event-loop-and-microtasks/2-summary.md) · [32](../32-error-handling-and-error/2-summary.md) · [19](../19-iterable-protocol-and-for-of/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 행마다 `fulfilled`/`rejected`/`pending` 과 값**을, **2번은 행마다 `@숫자`** 를 적어라.
- ★★★ **5번은 행마다 세 칸**(훅 있을 때의 출력 · 종료 코드 · 훅 없을 때의 종료 코드)을 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 ECMA-262 인가, HTML 인가, node 인가, V8 의 글자인가**」.
- ★★★ **시간에 관한 답은 하나도 없다** — 틱은 세고 시간은 안 쟀다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. executor 가 여러 번 부르면 — 전이 격자 (예측) ★★★ 이 주제의 축

```js
// js36b-37a-transitions.js
// Each row: an executor that makes several calls. Every call is recorded; the final state is read later.
// Final state = what then(onFulfilled, onRejected) sees after all queued jobs ran (or "pending" if neither ran).
const show = (x) => (x instanceof Error ? x.constructor.name + " 「" + x.message + "」" : JSON.stringify(x));
const later = { p: null, resolve: null };
later.p = new Promise((r) => { later.resolve = r; });
const thenable = (body) => ({ then(onF, onR) { body(onF, onR); } });
const rows = [
  ["resolve('a') · resolve('b')",                (res, rej) => { res("a"); res("b"); }],
  ["resolve('a') · reject('b')",                 (res, rej) => { res("a"); rej("b"); }],
  ["reject('a') · resolve('b')",                 (res, rej) => { rej("a"); res("b"); }],
  ["throw Error('a')",                           (res, rej) => { throw new Error("a"); }],
  ["resolve('a') · throw Error('b')",            (res, rej) => { res("a"); throw new Error("b"); }],
  ["resolve(p pending) · reject('b')",           (res, rej) => { res(later.p); rej("b"); }],
  ["resolve(Promise.reject('r'))",               (res, rej) => { res(Promise.reject("r")); }],
  ["resolve(thenable: onF('t'))",                (res, rej) => { res(thenable((f) => f("t"))); }],
  ["resolve(thenable: onF('t') · onR('u') · throw)", (res, rej) => { res(thenable((f, r) => { f("t"); r("u"); throw new Error("x"); })); }],
  ["resolve(object whose then getter throws)",   (res, rej) => { res({ get then() { throw new Error("g"); } }); }],
  ["resolve(the promise itself)",                (res, rej) => { setTimeout(() => res(self), 0); }],
];
let self;
const out = rows.map(([label, ex]) => {
  const row = { label, final: "pending" };
  const p = new Promise(ex);
  if (label.startsWith("resolve(the promise itself)")) self = p;
  p.then((v) => { row.final = "fulfilled " + show(v); }, (e) => { row.final = "rejected  " + show(e); });
  return row;
});
setTimeout(() => {
  console.log("[before p settles]");
  for (const r of out) if (r.label.startsWith("resolve(p pending)")) console.log("  " + r.label.padEnd(48) + r.final);
  later.resolve("c");
  setTimeout(() => {
    console.log("[after everything settled]");
    for (const r of out) console.log("  " + r.label.padEnd(48) + r.final);
    const firstWins = out.filter((r) => /^resolve\('a'\)|^reject\('a'\)|^throw/.test(r.label));
    const later2 = firstWins.filter((r) => !r.final.includes('"a"') && !r.final.includes("「a」"));
    console.log("rows with a plain first call where a later call decided the state: " + later2.length + " / " + firstWins.length);
  }, 0);
}, 0);
```

- ★★★ `[after everything settled]` 의 열한 행 각각의 최종 상태와 값은?
- ★★★ `[before p settles]` 의 한 행은?
- ★★ 마지막 줄의 `N / M` 은?

### 2. 계수 잡으로 센 틱 (예측) ★★★

```js
// js36b-37b-ticks.js
// Count microtask ticks. A counter job requeues itself once per tick; the probe's then callback reads the counter.
// Each row runs alone (the rows are separated by a setTimeout), so rows cannot disturb each other.
function measure(label, make) {
  return new Promise((done) => {
    let tick = 0, stop = false;
    const counter = () => { if (stop) return; tick++; queueMicrotask(counter); };
    const events = [];
    const p = make(events);
    p.then(() => { stop = true; events.push("then callback @" + tick); });
    queueMicrotask(counter);
    events.push("sync code done @" + tick);
    setTimeout(() => { console.log("  " + label.padEnd(44) + events.join(" > ")); done(); }, 0);
  });
}
const loggingThenable = (events) => ({
  get then() {
    events.push("get then");
    return (onF) => { events.push("then() called"); onF("t"); };
  },
});
(async () => {
  console.log("[1] new Promise((resolve) => resolve(X))");
  await measure("X = 'v'", () => new Promise((r) => r("v")));
  await measure("X = Promise.resolve('v')", () => new Promise((r) => r(Promise.resolve("v"))));
  await measure("X = thenable (then calls onF at once)", (ev) => new Promise((r) => r(loggingThenable(ev))));
  console.log("[2] Promise.resolve(X)");
  const q = Promise.resolve("v");
  console.log("  Promise.resolve(q) === q        " + (Promise.resolve(q) === q));
  await measure("Promise.resolve(Promise.resolve('v'))", () => Promise.resolve(Promise.resolve("v")));
  await measure("Promise.resolve(thenable)", (ev) => Promise.resolve(loggingThenable(ev)));
  console.log("[3] a then callback returns X -- ticks counted from the start");
  await measure("then(() => 'v')", () => Promise.resolve().then(() => "v"));
  await measure("then(() => Promise.resolve('v'))", () => Promise.resolve().then(() => Promise.resolve("v")));
})();
```

- ★★★ `[1]` 세 행의 `then callback @k` 는 각각?
- ★★★ thenable 행에서 `get then` · `sync code done` · `then() called` 의 순서는?
- ★★ `[2]` 의 `===` 결과와 두 행은? `[3]` 의 두 행은?
- ★ Chrome 151 에서 돌리면 달라지는 줄이 있나?

### 3. 한 사슬 — 어느 처리기가 도나 (예측) ★★

```js
// js36b-37c-chain.js
// [1] One chain. Every handler that runs prints a line; a handler that does not run prints nothing.
// [2] upstream (fulfilled 'T' / rejected Error T) x what the finally callback does -> what the caller receives.
const show = (x) => (x instanceof Error ? "Error 「" + x.message + "」" : JSON.stringify(x));
const log = (s) => console.log(s);
(async () => {
  log("[1] a chain");
  await Promise.resolve(1)
    .then((v) => { log("  h1 got " + show(v)); return v + 1; })
    .then((v) => { log("  h2 got " + show(v)); throw new Error("from h2"); })
    .then((v) => { log("  h3 got " + show(v)); return "h3"; })
    .then(undefined, undefined)
    .catch((e) => { log("  h4 (catch) got " + show(e)); return "from h4"; })
    .then((v) => { log("  h5 got " + show(v)); return Promise.reject(new Error("from h5")); })
    .then((v) => { log("  h6 got " + show(v)); }, (e) => { log("  h6 (second argument) got " + show(e)); })
    .finally((...a) => { log("  h7 (finally) got " + a.length + " arguments"); })
    .then((v) => log("  h8 got " + show(v)));

  log("[2] Promise.prototype.finally grid");
  const ups = [["fulfilled 'T'", () => Promise.resolve("T")], ["rejected Error T", () => Promise.reject(new Error("T"))]];
  const fins = [
    ["returns nothing", () => {}],
    ["returns 'F'", () => "F"],
    ["throws Error F", () => { throw new Error("F"); }],
    ["returns Promise.reject(Error F)", () => Promise.reject(new Error("F"))],
  ];
  let lost = 0, n = 0;
  for (const [u, mk] of ups) for (const [f, fn] of fins) {
    let got;
    try { got = "value " + show(await mk().finally(fn)); } catch (e) { got = "threw " + show(e); }
    const reached = got.includes("T");
    n++; if (!reached) lost++;
    log("  " + u.padEnd(18) + f.padEnd(33) + got.padEnd(20) + "upstream reached caller: " + reached);
  }
  log("cells where the upstream outcome did not reach the caller: " + lost + " / " + n);
})();
```

- ★★★ `[1]` 에서 찍히는 줄은? `h3` 은 찍히나?
- ★★ `h7` 은 인자를 몇 개 받나? `h8` 이 받는 값은?

### 4. `.finally()` 격자 (예측) ★★★

- ★★★ 3번 소스의 `[2]` — 여덟 칸 각각 호출자가 받는 것은? 마지막 줄의 `N / M` 은?
- ★★ `returns 'F'` 두 칸에서 호출자는 무엇을 받나?

### 5. `catch` 를 언제 다나 — node 두 판 (예측) ★★★

```js
// js36b-37-h-late-catch.js
// A promise is rejected at once. When is the catch attached? (argv[2]) Are node's hooks installed? (argv[3])
const when = process.argv[2], hooks = process.argv[3] === "hooks";
if (hooks) {
  process.on("unhandledRejection", (reason) => console.log("unhandledRejection(" + reason + ")"));
  process.on("rejectionHandled", () => console.log("rejectionHandled"));
}
const p = Promise.reject("R");
const attach = () => p.catch(() => console.log("catch ran"));
if (when === "same-tick") attach();
if (when === "next-microtask") queueMicrotask(attach);
if (when === "3rd-microtask") Promise.resolve().then().then().then(attach);
if (when === "setTimeout-0") setTimeout(attach, 0);
if (when === "setImmediate") setImmediate(attach);
if (when === "never") { /* nothing is attached */ }
```

```sh
# js36b-37d-unhandled-node.sh
#!/usr/bin/env bash
# One row per "when the catch is attached", for node18 and node20.
#   with hooks : what node's process events printed (standard output), then the exit code
#   no hooks   : the exit code, and whether standard error mentions ERR_UNHANDLED_REJECTION
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cases="same-tick next-microtask 3rd-microtask setTimeout-0 setImmediate never"
declare -A row
for v in 18 20; do
  [ $v = 18 ] && n="$N18" || n="$N20"
  echo "--- node$v"
  printf '  %-16s %-52s %-9s %s\n' "catch attached" "with hooks: stdout" "exit" "no hooks: exit · ERR_UNHANDLED_REJECTION on stderr"
  for c in $cases; do
    out="$("$n" js36b-37-h-late-catch.js "$c" hooks | paste -sd' ' -)"; e1=$?
    err="$("$n" js36b-37-h-late-catch.js "$c" 2>&1 >/dev/null)"; e2=$?
    case $err in *ERR_UNHANDLED_REJECTION*) m=yes ;; *) m=no ;; esac
    line="$(printf '  %-16s %-52s %-9s %s' "$c" "$out" "$e1" "$e2 · $m")"
    printf '%s\n' "$line"
    row[$v,$c]="$line"
  done
done
d=0; t=0
for c in $cases; do t=$((t + 1)); [ "${row[18,$c]}" = "${row[20,$c]}" ] || d=$((d + 1)); done
echo ""
echo "rows where node18 and node20 differ: $d / $t"
```

- ★★★ 여섯 행 각각 — 훅이 있을 때 표준 출력은? 그 종료 코드는? 훅이 없을 때 종료 코드와 `ERR_UNHANDLED_REJECTION` 은?
- ★★ 마지막 줄의 `N / M` 은?

### 6. 같은 질문을 Chrome 151 에서 (예측) ★★★

```js
// js36b-37f-unhandled.web.js
// Chrome. Five promises rejected at once, each with its own reason; the catch is attached at different moments.
// Every event the page receives is printed with the reason it carries.
addEventListener("unhandledrejection", (e) => console.log("unhandledrejection(" + e.reason + ")"));
addEventListener("rejectionhandled", (e) => console.log("rejectionhandled(" + e.reason + ")"));
const make = (reason, attachLater) => {
  const p = Promise.reject(reason);
  attachLater(() => p.catch(() => console.log("catch ran(" + reason + ")")));
};
make("same-tick", (a) => a());
make("next-microtask", (a) => queueMicrotask(a));
make("setTimeout-0", (a) => setTimeout(a, 0));
make("setTimeout-0-twice", (a) => setTimeout(() => setTimeout(a, 0), 0));
make("never", () => {});
```

- ★★★ 찍히는 줄은 어떤 순서로 무엇인가? `setTimeout-0` 은 보고되나?
- ★★ 같은 페이지를 `--allow-file-access-from-files` 없이 열면 무엇이 빠지나?

### 7. 왜 처음 호출만 효력이 있나 (왜) ★★

- ★★★ `CreateResolvingFunctions` 가 resolve 와 reject 에게 **나눠 주는 것**은 무엇이고, 첫 호출은 그것을 어떻게 바꾸나?
- ★★ executor 안의 `throw` 는 무엇을 부르는 것과 같나? 그래서 `resolve('a')` 뒤의 `throw` 는?

### 8. 진짜 프라미스로 `resolve` 하면 왜 두 틱이 더 드나 (왜) ★★★

- ★★★ 더 드는 두 잡은 각각 무엇인가?
- ★★ 곧바로 `onF` 를 부르는 thenable 은 왜 하나만 더 드나?
- ★ `Promise.resolve(q)` 는 왜 `@0` 인가?

### 9. `.finally()` 와 `try`/`finally` (연결) ★★★

- ★★★ 32번의 `try`/`finally` 격자는 `6 / 9`, 이 문서의 `.finally()` 격자는 `4 / 8` 이다. 결정적으로 갈린 칸은 어느 것인가?
- ★★ `thenFinally` 가 콜백의 반환값으로 하는 일과 하지 않는 일은?

### 10. 미처리 거부 — 누가 정하나 (경계) ★★★

- ★★★ ECMA-262 가 미처리 거부에 대해 하는 일은 무엇까지인가? 그 훅의 두 연산 이름은?
- ★★ node 기본 모드가 `exit 1` 로 끝내는 조건은? 훅이 있으면? `warn` 모드면?
- ★★ HTML 은 언제 이벤트를 쏘나? `setTimeout` 0 에 단 `catch` 가 Chrome 에서 보고되지 않은 것은 명세 보장인가 관찰인가?

### 11. 로컬 파일로 연 페이지의 침묵 (경계) ★★

- ★★ HTML 의 `HostPromiseRejectionTracker` 첫 단계는 무엇을 보고 그냥 돌아가나?
- ★ 「이벤트가 안 왔다」에서 「거부가 없었다」로 가면 왜 틀리나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
