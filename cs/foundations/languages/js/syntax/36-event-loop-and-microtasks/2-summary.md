# js/syntax/36 — 이벤트 루프와 마이크로태스크: 「동기 코드 → 마이크로태스크 전부 → 매크로태스크 하나」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — **한 파일**(콜백 열한 개)을 **세 호스트**(node CommonJS · node ES 모듈 · Chrome 151)에 던지고,
> 라벨마다 **몇 번째로 찍혔나**를 칸에 적어 **「세 호스트에서 자리가 같지 않은 라벨 N / M」** 을 스크립트가 마지막 줄로 센다(동작 (1)).
> 격자의 칸은 **① 추상 연산에 로그 심기**로 얻는다 — 콜백마다 **자기 라벨을 찍는 것**이 로그다.
> ★★ 보조 창 하나 — **`sort -u` 가짓수**(규칙 11). 흔들리는 순서(`setTimeout` 0 대 `setImmediate`)는 **300판의 서로 다른 순서가 몇 가지인가**로만 싣는다(동작 (4)).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Jobs and Host Operations to Enqueue Jobs](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html#sec-jobs) — 「**Jobs must run in the same order as the `HostEnqueuePromiseJob` invocations that scheduled them.**」 · `HostEnqueueTimeoutJob` 은 「**after at least milliseconds**」
> - [HTML — Event loop processing model](https://html.spec.whatwg.org/multipage/webappapis.html#perform-a-microtask-checkpoint) — `perform a microtask checkpoint` 의 「**While the event loop's microtask queue is not empty**」
> - [HTML — Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers) — 먼저 시작했고 시간이 같거나 짧은 타이머를 기다린다 · 중첩 수준이 5 를 넘으면 4ms 하한 · [Microtask queuing](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#microtask-queuing)(`queueMicrotask`)
> - [Node.js v20 — process: `queueMicrotask()` 대 `process.nextTick()`](https://nodejs.org/docs/latest-v20.x/api/process.html#when-to-use-queuemicrotask-vs-processnexttick) — 「CJS 에서는 `nextTick` 이 먼저, ESM 에서는 `queueMicrotask` 가 먼저」
> - [Node.js — The Node.js Event Loop](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick) — 「메인 모듈에서는 `setTimeout` 0 과 `setImmediate` 의 순서가 **non-deterministic**」
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **알고리즘·연산 이름**으로, 순서는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ Chrome 151 은 **헤드리스로** 돌렸다 — 배너가 `./js36b-browser.sh` 로 시작하는 블록이다. 그 스크립트가 **가상 시간 예산**(`--virtual-time-budget=2000`)을 주고 페이지를 떠 온다(소스는 아래).
> ★★ **이 묶음(36\~39)의 node 탐침은 두 node 판에서 한 글자도 같았고, 호스트 전용 API 를 안 쓰는 탐침은 Chrome 151 에서도 같았다**(아래 대조기의 집계 줄).
> ★★★ **시간은 한 번도 재지 않았다.** 이 문서의 모든 근거는 **순서**와 **횟수**다.
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `Promise` · `then` | ES2015 | 세 판 다 있다 |
> | `async` 함수 · `await` | ES2017 | 세 판 다 있다 |
> | `queueMicrotask` | — **ECMA-262 밖**(HTML 의 API, node 도 구현한다) | 세 판 다 있다 |
> | `setTimeout` | — **ECMA-262 밖**(HTML · node) | 세 판 다 있다 |
> | `setImmediate` · `process.nextTick` | — **node 의 것** | ★ **Chrome 에 없다**(판별 블록의 `host` 줄) |
>
> ★★ **판 경계는 TC39 finished proposals 표와 이 목록의 README 를 대조했다** — Async functions 가 **2017**. README 36행은 판을 적지 않는다(적을 것이 호스트 API 뿐이다).
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 라벨 11 × 호스트 3 — 칸은 **찍힌 순위**, 마지막 줄은 **「세 호스트에서 자리가 같지 않은 라벨 N / M」**(동작 (1)) |
> | ★★★ **① 추상 연산에 로그 심기** | 콜백마다 **자기 라벨**을 찍는다 · 기아 탐침은 **돈 횟수**를 센다(동작 (5)) |
> | ★★ **`sort -u` 가짓수**(규칙 11) | 흔들리는 순서 하나(`setTimeout` 0 대 `setImmediate`)를 **300판의 서로 다른 순서 수**로 결정적으로 바꾼다(동작 (4)) |
> | ★ **부적용 — ③ 브랜드 태그** | 이 주제에는 판정할 객체의 종류가 없다 |
> | ★ **부적용 — ④ 예외의 `constructor.name` + `message`** | 이 주제의 탐침은 **아무것도 던지지 않는다.** 거부와 예외는 37번 |
> | ★ **안 쟀다 — 시간** | 「`setTimeout(f, 0)` 은 몇 ms 뒤에 도나」를 **재지 않았다.** 「마이크로태스크가 빠르다」도 쓰지 않는다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **메인 모듈에서 `setTimeout` 0 과 `setImmediate` 중 누가 먼저냐** — **판마다** 바뀐다. 그래서 **어느 쪽이 몇 번**인지는 싣지 않고 **가짓수만** 실었다 | ★★★ 순서 퍼즐 격자의 **모든 칸**과 「`8 / 11`」 — 마이크로태스크끼리는 **언어 명세가**, 같은 지연의 타이머끼리는 **HTML 이** 순서를 정한다(node 쪽은 관찰) |
> | 판별 블록의 판 문자열 — 머신에 매인다 | ★★ **가짓수** `2` 와 `1` — 300판이면 **두 순서가 다 나온다**(어느 쪽이 몇 번인지는 판마다 흔들려 싣지 않는다) |
> | | 기아 탐침의 **돈 횟수**와 **타이머가 돈 횟수** — 가드가 횟수로 끊으므로 기계 속도에 안 매인다 |
>
> **★★★ 층 — 이 묶음은 「언어」와 「호스트」가 갈리는 곳이다**
>
> | 층 | 무엇을 정하나 | 이 문서의 어디 |
> |---|---|---|
> | **언어 명세(ECMA-262 Jobs)** | 프라미스 잡은 **등록한 순서대로**(FIFO) 돈다. 잡은 **다른 코드가 돌고 있지 않을 때만** 시작한다. **언제**·**무엇과 섞어** 돌리나는 정하지 않는다 | 동작 (1)의 `P1 → Q1 → A2 → P2 → P3` |
> | **호스트 — HTML event loop** | 태스크 **하나** → 마이크로태스크 체크포인트(**빌 때까지**) → 다음 태스크 · `queueMicrotask` · `setTimeout` 의 순서와 4ms 하한 | 동작 (2)·(5) |
> | **호스트 — node(libuv)** | `process.nextTick` 큐가 **프라미스 큐보다 먼저** 비워진다(**CJS 에서**) · `setImmediate` 와 libuv 의 단계(timers → poll → check) | 동작 (1)의 `N1` · 동작 (3)·(4) |
> | **구현(V8)** | 이 주제에서는 **구현이 갈라 놓은 칸을 못 찾았다** — node 20 의 V8 과 Chrome 151 의 V8 이 같은 순서를 냈다 | 대조기 |
> | **이 판의 관찰** | node 의 같은 지연 타이머끼리의 순서 · 가짓수 `2`·`1` | 동작 (1)·(4) |
>
> **선행** — [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md)(목록의 선행. ★ 거기서 **동기 `throw`** 를 봤다 — 여기서부터 **같은 코드가 「나중에」 돈다**) ·
> [20 — 제너레이터](../20-generators/2-summary.md)(★ **멈췄다 이어 도는 함수** — 동작 (1)의 `A1 → A2` 가 그 모양이다. 정본은 39번) ·
> [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md)(`Array.fromAsync` 의 로그가 **이미 이 주제의 순서**를 쓰고 있었다).
>
> ★★ **경계 — 연혁·「왜 단일 스레드인가」** 는 [`history/js/04-비동기-진화.md`](../../../../../../history/js/04-비동기-진화.md) 의 **「이벤트 루프 상세 — 매크로태스크 vs 마이크로태스크」** 절이 정본이다. 여기서는 **그 순서를 세 호스트에서 재고 층을 가른다.**
> ★★★ 그 절의 Node 주석 「`process.nextTick` 이 마이크로태스크보다도 먼저」는 **CommonJS 에서만 맞았다** — **ES 모듈에서는 뒤집혔다**(동작 (3)). 그 문서는 고치지 않았다(이 배치의 범위 밖).
> ★ **경계 — 프로세스·스레드 일반**은 [`process-thread/`](../../../../process-thread/README.md)의 몫이다. ★ **경계 — 프라미스의 상태와 거부**는 [37번](../37-promise-state-model/2-summary.md), **`await` 의 틱 수**는 [39번](../39-async-await/2-summary.md).

```sh
# js36b-versions.sh
#!/usr/bin/env bash
# Which runtime printed each block -- and the feature table (js36b-features.js) in all three.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'console.log("node " + process.versions.node + "  v8 " + process.versions.v8)'
  "$n" js36b-features.js
done
google-chrome --version | sed 's/ *$//'
./js36b-browser.sh js36b-features.js
python3 --version
```

```js
// js36b-features.js
// Is each feature of this batch here? The same script goes to node18, node20 and Chrome.
// Syntax is asked through new Function, so a missing feature does not kill the whole script.
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no (" + e.constructor.name + ")"; }
  console.log("  " + label.padEnd(50) + r);
};
const syntax = (src) => () => (new Function(src), true);
has("ES2015  Promise", () => typeof Promise === "function");
has("ES2017  async function / await", syntax("return async function () { await 1; }"));
has("ES2018  Promise.prototype.finally", () => typeof Promise.prototype.finally === "function");
has("ES2020  Promise.allSettled", () => typeof Promise.allSettled === "function");
has("ES2021  Promise.any / AggregateError", () => typeof Promise.any === "function" && typeof AggregateError === "function");
has("ES2024  Promise.withResolvers", () => typeof Promise.withResolvers === "function");
has("ES2025  Promise.try", () => typeof Promise.try === "function");
has("ES2026  Array.fromAsync", () => typeof Array.fromAsync === "function");
has("host    queueMicrotask", () => typeof queueMicrotask === "function");
has("host    setTimeout", () => typeof setTimeout === "function");
has("host    setImmediate", () => typeof setImmediate === "function");
has("host    process.nextTick", () => typeof process === "object" && typeof process.nextTick === "function");
```

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

두 node 판 · Chrome 대조기의 집계 줄(이 묶음의 모든 node 탐침) — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 13 · differs 0   ·   node20 vs Chrome 151: identical 12 · differs 0 · node only 1`

Chrome 탐침은 이 두 파일로 돌린다 — 페이지가 `console.log` 를 가로채 줄마다 `<pre>` 를 다시 쓰므로 **프라미스·타이머 뒤에 찍힌 줄도** 떠 온 DOM 에 들어 있다.

```sh
# js36b-browser.sh
#!/usr/bin/env bash
# Run probe scripts in headless Chrome and print what they logged.
#   usage: ./js36b-browser.sh [--muted] <script.js>[,<script.js>...]
# --dump-dom writes HTML entities, so the last sed turns them back.
# --allow-file-access-from-files: without it a file:// script counts as cross-origin ("muted errors").
set -u -o pipefail
cd "$(dirname "$0")"
flag=--allow-file-access-from-files
if [ "$1" = "--muted" ]; then flag=; shift; fi
google-chrome --headless $flag --virtual-time-budget=2000 --dump-dom "file://$PWD/js36b-page.html?$1" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' \
  | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g'
```

```html
<!-- js36b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js36b</title>
<pre id="o"></pre>
<script>
// Runs the probe scripts named after "?" in the address (comma-separated, in that order).
// console.log is replaced: every call appends a line and rewrites <pre>, so lines printed
// after promises and timers are present when --dump-dom writes the page out.
const __lines = [];
const __render = () => {
  document.getElementById("o").textContent = "==" + "=OUT===\n" + __lines.join("\n") + "\n===END" + "===";
};
console.log = (...a) => { __lines.push(a.join(" ")); __render(); };
window.addEventListener("error", (e) => { __lines.push("uncaught " + e.message); __render(); });
__render();
for (const f of location.search.slice(1).split(",")) document.write('<script src="' + f + '"><\/script>');
</script>
```

## 한눈에 — 쉽게 말하면

**이벤트 루프는 「주문 한 건씩 받는 주방」이다. 주문(매크로태스크)을 하나 끝내면, 그 주문을 만드는 동안 붙여 둔 메모(마이크로태스크)를 **한 장도 남김없이** 처리한 뒤에야 다음 주문을 받는다.**

- ★★★ **지금 만들고 있는 요리(동기 코드)는 끝까지 만든다** — 도중에 메모도 다음 주문도 끼어들지 않는다.
- ★★★ **메모는 붙인 순서대로** 처리한다. 메모를 처리하다 새 메모가 붙으면 **그것까지** 처리한다.
- ★★ **다음 주문은 메모가 다 떨어져야** 받는다 — 그래서 메모가 메모를 끝없이 낳으면 **다음 주문을 영영 못 받는다**(기아).
- ★★ **node 주방에는 셰프 개인 포스트잇(`process.nextTick`)이 하나 더 있다** — CommonJS 주방에서는 메모보다 **먼저** 본다. ES 모듈 주방에서는 **나중에** 본다.

```text
   ┌──────────────────────── 한 바퀴 ────────────────────────┐
   │                                                          │
   │   ① 매크로태스크 하나        ② 마이크로태스크 전부           │
   │      (스크립트 전체 ·   ───▶    (then · queueMicrotask ·   ───┐
   │       setTimeout 콜백)          await 뒤)  빌 때까지        │
   │                                                          │
   └────────────────────────── ◀── ③ 다음 매크로태스크 ─────────┘
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 지금 만드는 요리 | 실행 중인 코드 — 스크립트 본문 · 콜백 하나. **끝까지 돈다**(run-to-completion) | 동작 (1)의 `S1 → A1 → S2` |
| 주문 | **매크로태스크**(태스크) — 스크립트 전체 · `setTimeout` 콜백 · I/O 완료 | 동작 (1)의 `T1`·`T2` |
| 붙여 둔 메모 | **마이크로태스크** — `then` 콜백 · `queueMicrotask` · `await` 다음 줄 | 동작 (1)의 `P`·`Q`·`A2` |
| 「메모가 다 떨어지면」 | HTML 의 **마이크로태스크 체크포인트** — 큐가 **빌 때까지** 돈다 | 동작 (2)의 그림 |
| 셰프 개인 포스트잇 | node 의 **`nextTick` 큐** — ECMA-262 에도 HTML 에도 없다 | 동작 (3) |
| 메모가 메모를 낳는다 | **마이크로태스크 기아** | 동작 (5) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**`setTimeout(f, 0)` 으로 「바로 다음」에 돌렸는데 `then` 콜백들보다 늦게 돌았다**」와
「**재귀하는 `then` 이 돌기 시작하자 타이머·화면 갱신이 멈췄다**」가 그것이다(동작 (1)·(5)).

> **매크로태스크(태스크)** — 이벤트 루프가 한 바퀴에 **하나만** 꺼내 돌리는 일감.\
> 예: `setTimeout(f, 0)` 의 `f`.

> **마이크로태스크** — 지금 도는 코드가 끝난 직후, 큐가 **빌 때까지** 연달아 도는 일감.\
> 예: `Promise.resolve().then(f)` 의 `f`.

## 이 주제가 답하려는 질문

1. **동기 코드 · 프라미스 콜백 · `queueMicrotask` · `await` 뒤 · `setTimeout` 0 · `setImmediate` · `process.nextTick` 이 섞이면 어떤 순서로 찍히나** — 그 순서를 **누가** 정하나(언어인가 호스트인가)?
2. **같은 파일이 호스트에 따라 순서가 바뀌는 칸은 어디인가** — node CommonJS · node ES 모듈 · Chrome 에서?
3. **마이크로태스크가 자기 자신을 계속 큐에 넣으면 무엇이 멈추나** — 매크로태스크로 다시 넣으면 무엇이 달라지나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 순서 퍼즐 격자 — 한 파일, 세 호스트

**언제 쓰나** — 「이 콜백이 저 콜백보다 먼저 도나」를 코드를 읽고 판단해야 할 때 · 같은 코드를 브라우저와 node 에 같이 올릴 때.
★★★ 파일은 하나다. 콜백마다 **라벨 두 글자**로 시작하는 줄을 찍는다. `process` 가 없는 호스트(Chrome)에서는 `N1` 을 **등록하지 않는다.**

```js
// js36b-36-h-order.js
// One script for three hosts: node (CommonJS), node (ES module), Chrome.
// Every callback prints its own label. The order of the printed lines is the whole answer.
const log = (s) => console.log(s);
const tick = typeof process === "object" ? process.nextTick : undefined;

log("S1 sync, first line");
setTimeout(() => log("T1 setTimeout 0, scheduled first"), 0);
Promise.resolve().then(() => {
  log("P1 then, scheduled first");
  Promise.resolve().then(() => log("P3 then, scheduled from inside P1"));
});
queueMicrotask(() => log("Q1 queueMicrotask"));
if (tick) tick(() => log("N1 process.nextTick"));
(async () => {
  log("A1 async function, before its await");
  await undefined;
  log("A2 async function, after its await");
})();
setTimeout(() => log("T2 setTimeout 0, scheduled second"), 0);
Promise.resolve().then(() => log("P2 then, scheduled second"));
log("S2 sync, last line");
```

```sh
# js36b-36a-order-grid.sh
#!/usr/bin/env bash
# The same file (js36b-36-h-order.js) in three hosts. A cell is the rank at which that host printed the label.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cjs="$("$N20" js36b-36-h-order.js | cut -c1-2)"
esm="$("$N20" --input-type=module < js36b-36-h-order.js | cut -c1-2)"
web="$(./js36b-browser.sh js36b-36-h-order.js | cut -c1-2)"
rank() { printf '%s\n' "$2" | grep -n -x "$1" | cut -d: -f1; }
printf '%-7s %-10s %-10s %-10s\n' "label" "node CJS" "node ESM" "Chrome 151"
moved=0; n=0
for l in $cjs; do
  a="$(rank "$l" "$cjs")"; b="$(rank "$l" "$esm")"; c="$(rank "$l" "$web")"
  printf '%-7s %-10s %-10s %-10s\n' "$l" "$a" "$b" "${c:--}"
  n=$((n + 1))
  [ "$a" = "$b" ] && [ "$a" = "${c:-x}" ] || moved=$((moved + 1))
done
echo ""
echo "labels not at the same rank in all three hosts: $moved / $n"
f() { printf '%s\n' "$1" | grep -v -x N1 | tr '\n' ' '; }
[ "$(f "$cjs")" = "$(f "$esm")" ] && [ "$(f "$esm")" = "$(f "$web")" ] && same=yes || same=no
echo "with N1 left out, the three orders are identical: $same"
[ "$("$N18" js36b-36-h-order.js)" = "$("$N20" js36b-36-h-order.js)" ] && s18a=same || s18a=DIFFERENT
[ "$("$N18" --input-type=module < js36b-36-h-order.js)" = "$("$N20" --input-type=module < js36b-36-h-order.js)" ] && s18b=same || s18b=DIFFERENT
echo "node18 against node20 -- CJS: $s18a · ESM: $s18b"
```

```text
===== ./js36b-36a-order-grid.sh (exit=0) =====
label   node CJS   node ESM   Chrome 151
S1      1          1          1         
A1      2          2          2         
S2      3          3          3         
N1      4          9          -         
P1      5          4          4         
Q1      6          5          5         
A2      7          6          6         
P2      8          7          7         
P3      9          8          8         
T1      10         10         9         
T2      11         11         10        

labels not at the same rank in all three hosts: 8 / 11
with N1 left out, the three orders are identical: yes
node18 against node20 -- CJS: same · ESM: same
```

```text
   node CommonJS — 동기 코드(S2)가 끝난 순간의 큐 세 줄

   nextTick 큐     [ N1 ]
   마이크로태스크   [ P1 · Q1 · A2 · P2 ]            ← 등록한 순서 그대로
   타이머           [ T1 · T2 ]

   비우는 순서:  nextTick 큐 전부 → 마이크로태스크 전부 → (P1 이 도는 중에 P3 가 뒤에 붙는다) → 타이머 하나씩
                 N1              → P1 Q1 A2 P2 P3       → T1 → T2
```

- ★★★ **집계 줄 — `labels not at the same rank in all three hosts: 8 / 11`.** 그런데 **`N1` 을 빼면 세 순서가 한 글자도 같다**(`with N1 left out, the three orders are identical: yes`).
  **순위가 갈린 여덟 칸은 전부 `N1` 하나가 끼어든 자리 때문**이다 — node CJS 에서는 4위, ES 모듈에서는 9위, Chrome 에는 없다. 뒤의 라벨들이 한 칸씩 밀리거나 당겨졌을 뿐이다.
- ★★★ **`S1 → A1 → S2` — 동기 코드는 끝까지 돈다.** `async` 함수의 본문도 **첫 `await` 까지는 동기**다(`A1` 이 `S2` 보다 먼저). 정본은 39번.
- ★★★ **`P1 → Q1 → A2 → P2` — 마이크로태스크는 등록한 순서대로** 돈다. `then` 이든 `queueMicrotask` 든 `await` 뒤든 **한 줄에 선다.** 명세의 한 문장 — 「**Jobs must run in the same order as the `HostEnqueuePromiseJob` invocations that scheduled them.**」
- ★★★ **`P3` 는 `T1` 보다 먼저** 돈다 — `P1` 이 **도는 중에** 등록한 마이크로태스크도 **같은 비우기 안에서** 돈다. 타이머는 **마이크로태스크가 다 빠진 뒤에야** 차례가 온다.
- ★★ **`T1 → T2` — 같은 지연의 타이머는 등록한 순서**다. HTML 은 이것을 정한다(「먼저 시작했고 시간이 같거나 짧은 타이머가 끝나기를 기다린다」). node 는 **관찰**이다.
- ★★ **두 node 판도 같았다**(`node18 against node20 -- CJS: same · ESM: same`).

### (2) ★★★ 큐 세 줄 — HTML 이 정하는 한 바퀴

**언제 쓰나** — 「`await` 다음 줄은 화면 갱신보다 먼저 도나」·「타이머 콜백 두 개 사이에 `then` 이 끼어드나」를 판단할 때.

```text
   HTML event loop 의 한 바퀴 (이 문서가 확인한 부분만)

   ① 태스크 큐에서 가장 오래된 태스크 하나를 꺼내 돌린다          ← 스크립트 전체 · setTimeout 콜백 하나
   ② 마이크로태스크 체크포인트:
        while (마이크로태스크 큐가 비어 있지 않다) {                ← 「빌 때까지」 — 도중에 붙은 것도 포함
            가장 오래된 마이크로태스크 하나를 꺼내 돌린다
        }
        미처리 거부를 알린다(37번)
   ③ (필요하면 렌더링)                                            ← 이 문서는 재지 않았다
   ④ ①로

   → 태스크 콜백 두 개(T1, T2) 사이에는 반드시 체크포인트가 있다
   → 그래서 T1 이 등록한 then 은 T2 보다 먼저 돈다
```

- ★★★ **① 은 하나, ② 는 전부**다. 명세의 글자가 「**While the event loop's microtask queue is not empty**」다 — 도중에 붙은 마이크로태스크도 **같은 루프가 꺼낸다.** 동작 (1)의 `P3` 가 그 증거다.
- ★★ **ECMA-262 는 이 바퀴를 모른다** — 언어 명세는 「잡을 등록한 순서대로 돌려라」와 「**다른 실행 컨텍스트가 없을 때만** 잡을 시작해라」까지다.
  **「태스크 하나 → 마이크로태스크 전부」라는 모양은 HTML 이 정한다.** node 는 같은 모양을 **자기 방식으로** 구현한다(동작 (3)).
- ★ **`queueMicrotask` 는 HTML 의 API**다(ECMA-262 에 없다). 같은 큐에 넣는 것이 **`then` 과 같은 줄에 서는 이유**다.
- ★ **③ 렌더링**은 이 문서가 **재지 않았다**(헤드리스 페이지에서 `requestAnimationFrame` 을 세지 않았다). 연혁 문서의 「`await` 다음 줄은 같은 사이클의 렌더링보다 먼저」는 ②가 ③보다 앞이라는 **HTML 의 순서에서 나온 말**이다.

### (3) ★★★ `process.nextTick` — node 의 셋째 줄, 그리고 ES 모듈에서 뒤집히는 이유

**언제 쓰나** — node 코드에서 `nextTick` 과 `then` 을 섞어 쓸 때 · 같은 코드를 `.js`(CommonJS)에서 `.mjs` 로 옮길 때.

```text
   node 가 한 콜백을 끝낸 뒤 하는 일 (CommonJS 의 모양)

   콜백 끝 ─▶ nextTick 큐 전부 ─▶ 마이크로태스크 전부 ─▶ (nextTick 이 또 생겼으면 다시) ─▶ 다음 단계

   ES 모듈 — 모듈 본문 자체가 「이미 마이크로태스크를 비우는 중」에 돈다

   모듈 본문 끝 ─▶ (지금 비우던) 마이크로태스크 전부 ─▶ nextTick 큐 ─▶ 다음 단계
                    P1 Q1 A2 P2 P3                      N1
```

- ★★★ **CommonJS 에서는 `N1` 이 4위**(동기 코드 바로 뒤, 모든 마이크로태스크 앞), **ES 모듈에서는 9위**(마이크로태스크를 다 비운 뒤, 타이머 앞)다 — **같은 파일**이다.
- ★★★ node 문서의 설명 — 「**CJS 모듈에서는 `process.nextTick()` 콜백이 항상 `queueMicrotask()` 콜백보다 먼저 돈다. ESM 모듈은 이미 마이크로태스크 큐의 일부로 처리되므로, 거기서는 `queueMicrotask()` 콜백이 항상 먼저다.**」
  **「`nextTick` 은 마이크로태스크보다 먼저」는 CommonJS 에서만 참**이다.
- ★★ 이 순서는 **ECMA-262 에도 HTML 에도 없다** — `nextTick` 큐는 **node 의 것**이다. Chrome 에는 `process` 가 없다(판별 블록의 `host  process.nextTick  no`).
- ★ **`setImmediate` 도 node 의 것**이다 — 동작 (4).

### (4) ★★ `setTimeout` 0 대 `setImmediate` — 메인 모듈에서는 흔들린다, I/O 콜백 안에서는 안 흔들린다

**언제 쓰나** — node 에서 「이번 바퀴가 끝나면 바로」를 `setTimeout(f, 0)` 과 `setImmediate(f)` 중 무엇으로 쓸지 고를 때.
★★★ **흔들리는 순서를 한 판으로 싣지 않는다** — 300판을 돌려 **서로 다른 순서가 몇 가지인가**를 센다(규칙 11).

```js
// js36b-36-h-main.js
// Scheduled straight from the main module.
setTimeout(() => console.log("timeout"), 0);
setImmediate(() => console.log("immediate"));
```

```js
// js36b-36-h-io.js
// Scheduled from inside an I/O callback (readFile has finished).
require("fs").readFile(__filename, () => {
  setTimeout(() => console.log("timeout"), 0);
  setImmediate(() => console.log("immediate"));
});
```

```sh
# js36b-36b-timeout-vs-immediate.sh
#!/usr/bin/env bash
# Run each file 300 times and keep only the distinct orders (sort -u). The number of distinct orders is the answer.
set -u -o pipefail
cd "$(dirname "$0")"
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for f in js36b-36-h-main.js js36b-36-h-io.js; do
  runs="$(for i in $(seq 300); do "$N20" "$f" | paste -sd' ' -; done)"
  kinds="$(printf '%s\n' "$runs" | sort -u)"
  echo "--- $f · 300 runs · distinct orders: $(printf '%s\n' "$kinds" | wc -l)"
  printf '%s\n' "$kinds" | sed 's/^/    /'
done
```

```text
===== ./js36b-36b-timeout-vs-immediate.sh (exit=0) =====
--- js36b-36-h-main.js · 300 runs · distinct orders: 2
    immediate timeout
    timeout immediate
--- js36b-36-h-io.js · 300 runs · distinct orders: 1
    immediate timeout
```

```text
   libuv 의 한 바퀴 (node 문서의 단계 중 이 탐침에 걸리는 셋)

         ┌─▶ timers  ── 만료된 setTimeout 콜백
         │     │
         │   poll    ── I/O 완료 콜백 (readFile 의 콜백이 여기서 돈다)
         │     │
         │   check   ── setImmediate 콜백
         └─────┘

   메인 모듈에서 둘 다 등록 → 첫 timers 단계에 도착했을 때 1ms 가 이미 지났나?
                              지났으면 timeout 이 먼저, 아니면 immediate 가 먼저   ← 기계 사정
   poll 단계(I/O 콜백) 안에서 둘 다 등록 → 다음은 check → immediate 가 늘 먼저
```

- ★★★ **메인 모듈 — 가짓수 `2`**(`immediate timeout` · `timeout immediate` 둘 다 나왔다). **I/O 콜백 안 — 가짓수 `1`**(`immediate timeout` 만).
  node 문서도 메인 모듈의 순서를 「**non-deterministic** — 프로세스의 성능에 매인다」고 적는다.
- ★★ **I/O 콜백 안에서는 poll 다음이 check** 이므로 `setImmediate` 가 **다음 timers 단계보다 먼저** 온다. 이 순서는 **libuv 단계의 순서**에서 나온다 — 언어도 HTML 도 아니다.
- ★ **어느 쪽이 몇 번 나왔는지는 싣지 않는다** — 그 비율은 **판마다 흔들린다**(머리말의 흔들리는 칸). 가짓수 `2` 와 `1` 만 근거다.
- ★ Go 의 `select` 가 준비된 가지를 **명세상 무작위로** 고르는 것과 성격이 다르다 — 여기는 **무작위가 아니라 경쟁**이다(누가 먼저 준비되나). Go 쪽 가짓수 격자는 [Go 30](../../../go/syntax/30-select-default-and-timeouts/2-summary.md) 동작 (1).

### (5) ★★★ 마이크로태스크 기아 — 타이머는 몇 번 돌았나

**언제 쓰나** — 긴 작업을 「잘게 쪼개 양보」하려고 `then`·`queueMicrotask` 로 다시 거는 코드를 볼 때.
★★★ **가드**(`n` 번째에서 멈춘다)가 있어서 탐침이 **끝난다.** 첫 바퀴에서 `setTimeout` 0 을 하나 걸고, **돌고 있는 동안 그 타이머가 몇 번 돌았나**를 센다.

```js
// js36b-36c-starvation.js
// A job that queues itself again, stopped by a guard after n turns.
// At turn 1 a timer (setTimeout 0) is set. Question: how many times does that timer run while the loop is turning?
function trial(label, n, requeue) {
  return new Promise((done) => {
    let timerRuns = 0, turns = 0, seenAt = "-";
    const turn = () => {
      turns++;
      if (turns === 1) setTimeout(() => { timerRuns++; seenAt = turns; }, 0);
      if (turns < n) { requeue(turn); return; }
      const during = timerRuns;
      setTimeout(() => {
        console.log(label);
        console.log("  turns " + turns + " · timer runs while turning " + during + " · turns done when the timer ran " + seenAt);
        done();
      }, 0);
    };
    requeue(turn);
  });
}
(async () => {
  await trial("[1] requeue with queueMicrotask, n = 100000", 100000, (f) => queueMicrotask(f));
  await trial("[2] requeue with Promise.resolve().then, n = 100000", 100000, (f) => Promise.resolve().then(f));
  await trial("[3] requeue with setTimeout 0, n = 100", 100, (f) => setTimeout(f, 0));
})();
```

```text
===== node20 js36b-36c-starvation.js (exit=0) =====
[1] requeue with queueMicrotask, n = 100000
  turns 100000 · timer runs while turning 0 · turns done when the timer ran 100000
[2] requeue with Promise.resolve().then, n = 100000
  turns 100000 · timer runs while turning 0 · turns done when the timer ran 100000
[3] requeue with setTimeout 0, n = 100
  turns 100 · timer runs while turning 1 · turns done when the timer ran 1
```

같은 파일을 Chrome 151 에서.

```text
===== ./js36b-browser.sh js36b-36c-starvation.js (exit=0) =====
[1] requeue with queueMicrotask, n = 100000
  turns 100000 · timer runs while turning 0 · turns done when the timer ran 100000
[2] requeue with Promise.resolve().then, n = 100000
  turns 100000 · timer runs while turning 0 · turns done when the timer ran 100000
[3] requeue with setTimeout 0, n = 100
  turns 100 · timer runs while turning 1 · turns done when the timer ran 1
```

```text
   [1]·[2] 마이크로태스크로 다시 건다

   태스크(스크립트) ─▶ 체크포인트: turn 1 → turn 2 → … → turn 100000 ─▶ 타이머
                                    └─ 여기서 setTimeout 0 을 걸었다      ↑ 이제야 돈다
                     (체크포인트는 큐가 빌 때까지 안 끝난다 — 큐는 turn 이 스스로 계속 채운다)

   [3] setTimeout 0 으로 다시 건다

   태스크 turn 1 ─▶ (체크포인트) ─▶ 타이머 ─▶ 태스크 turn 2 ─▶ … ─▶ 태스크 turn 100
       └─ 여기서 타이머를 걸었다      ↑ turn 1 바로 다음에 돈다
```

- ★★★ **`[1]`·`[2]` — `timer runs while turning 0`.** 10만 바퀴 동안 타이머가 **한 번도** 안 돌았고, **10만 바퀴가 다 끝난 뒤에야** 돌았다(`turns done when the timer ran 100000`).
  **`queueMicrotask` 든 `then` 이든 같다** — 둘 다 마이크로태스크다.
- ★★★ **`[3]` — `timer runs while turning 1`, `turns done when the timer ran 1`.** 매크로태스크로 다시 걸면 **한 바퀴마다 다른 태스크가 끼어들 틈**이 생긴다. 타이머는 **turn 1 바로 다음**에 돌았다.
- ★★ **node 와 Chrome 151 이 한 글자도 같았다** — 이 모양은 **HTML 의 「빌 때까지」와 node 의 구현이 같은 답**을 낸 것이다.
- ★★ **가드가 없으면 탐침이 안 끝난다** — 그래서 「영원히 안 돈다」를 **돌려서 보이는 방법은 가드뿐**이다. 이 문서는 **가드 안에서 0 회**를 보였다.
- ★ 연혁 문서가 말하는 **「렌더링이 영영 안 일어나는 기아」** 는 같은 원리의 **화면 쪽**이다. 이 문서는 렌더링을 **재지 않았다.**

node 에는 한 겹이 더 있다 — **`nextTick` 이 자기 자신을 다시 걸면 프라미스 콜백이 굶는다.**

```js
// js36b-36d-nexttick-starvation.js
// node only. process.nextTick requeues itself, stopped by a guard after n turns.
// At turn 1 a promise reaction (then) is queued. Question: how many times does it run while the loop is turning?
const n = 100000;
let turns = 0, thenRuns = 0, seenAt = "-";
const turn = () => {
  turns++;
  if (turns === 1) Promise.resolve().then(() => { thenRuns++; seenAt = turns; });
  if (turns < n) { process.nextTick(turn); return; }
  console.log("turns " + turns + " · then runs while turning " + thenRuns);
  setTimeout(() => console.log("turns done when the then callback ran " + seenAt), 0);
};
process.nextTick(turn);
```

```text
===== node20 js36b-36d-nexttick-starvation.js (exit=0) =====
turns 100000 · then runs while turning 0
turns done when the then callback ran 100000
```

- ★★ **`then runs while turning 0`** — `nextTick` 큐가 **빌 때까지** 프라미스 콜백 차례가 안 온다(동작 (3)의 그림). 이것은 **node 의 것**이다.

### (6) ★★ 파이썬 `asyncio` 대비 — 줄이 하나뿐인 루프

**언제 쓰나** — 파이썬에서 온 사람이 「완료 콜백이 다른 콜백을 앞지른다」고 기대할 때 · 반대 방향.
★★★ 같은 모양을 두 언어로 — **콜백 하나 → 이미 끝난 것의 완료 콜백 → 콜백 하나** 순서로 **등록**한다.

```python
# js36b-36-h-onequeue.py
# asyncio: a callback, then a finished future's done-callback, then another callback -- in that order of scheduling.
import asyncio

async def main():
    loop = asyncio.get_running_loop()
    log = []
    loop.call_soon(log.append, "C1 call_soon, scheduled first")
    fut = loop.create_future()
    fut.add_done_callback(lambda f: log.append("F1 done-callback of a future"))
    fut.set_result(None)
    loop.call_soon(log.append, "C2 call_soon, scheduled second")
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    print("\n".join(log))

asyncio.run(main())
```

```js
// js36b-36-h-twoqueues.js
// The same shape in JS: a macrotask, a promise reaction, another macrotask -- in that order of scheduling.
const log = [];
setTimeout(() => log.push("C1 setTimeout 0, scheduled first"), 0);
Promise.resolve().then(() => log.push("F1 then of a fulfilled promise"));
setTimeout(() => log.push("C2 setTimeout 0, scheduled second"), 0);
setTimeout(() => console.log(log.join("\n")), 0);
```

```sh
# js36b-36e-python-contrast.sh
#!/usr/bin/env bash
# Python asyncio against JS: schedule a callback, a completion callback, another callback. Which order comes out?
set -u -o pipefail
cd "$(dirname "$0")"
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
echo "--- python3 $(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])') js36b-36-h-onequeue.py"
python3 js36b-36-h-onequeue.py
echo "--- node20 js36b-36-h-twoqueues.js"
"$N20" js36b-36-h-twoqueues.js
```

```text
===== ./js36b-36e-python-contrast.sh (exit=0) =====
--- python3 3.12 js36b-36-h-onequeue.py
C1 call_soon, scheduled first
F1 done-callback of a future
C2 call_soon, scheduled second
--- node20 js36b-36-h-twoqueues.js
F1 then of a fulfilled promise
C1 setTimeout 0, scheduled first
C2 setTimeout 0, scheduled second
```

```text
                 등록한 순서       C1          F1(완료 콜백)        C2

   asyncio       ready 큐 하나     C1   ─▶    F1          ─▶     C2        ← 등록 순서 그대로
   JS            두 줄             F1(마이크로) ─▶ C1 ─▶ C2                   ← 마이크로태스크가 앞지른다
```

- ★★★ **파이썬은 등록한 순서 그대로**(`C1 → F1 → C2`), **JS 는 `F1` 이 맨 앞**이다. 파이썬 `asyncio` 에서 완료된 future 의 콜백은 `call_soon` 과 **같은 ready 큐**에 선다 — **우선순위가 높은 줄이 따로 없다.**
- ★★ 그래서 **「마이크로태스크」라는 두 번째 줄은 JS(와 그 호스트)의 모양**이다. 파이썬 `asyncio` 는 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **51번**·**52번**이 정본이다(아직 폴더가 없다).

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 어느 줄에 서나 | 누구의 것 | 어디서 봤나 |
|---|---|---|---|
| `Promise.resolve().then(f)` | 마이크로태스크 | **ECMA-262**(프라미스 잡) | 동작 (1) |
| `await x` 다음 줄 | 마이크로태스크 | **ECMA-262** | 동작 (1)의 `A2` · 39번 |
| `queueMicrotask(f)` | 마이크로태스크 | **HTML**(node 도 구현) | 동작 (1)의 `Q1` |
| `setTimeout(f, 0)` | 매크로태스크(타이머) | **HTML** · node | 동작 (1)·(5) |
| `setImmediate(f)` | node 의 check 단계 | **node** | 동작 (4) |
| `process.nextTick(f)` | node 의 `nextTick` 큐 | **node** | 동작 (1)·(3) |

- **동기 코드는 끝까지 돈다.** 그 뒤에 마이크로태스크가 **빌 때까지**, 그 뒤에 매크로태스크 **하나**.
- **같은 줄 안에서는 등록한 순서**다(마이크로태스크는 명세가, 같은 지연의 타이머는 HTML 이 정한다).
- **node 의 `nextTick` 은 CommonJS 에서 마이크로태스크보다 먼저, ES 모듈에서 나중이다.**

## 어디서 틀리나

### (1) ★★★ `setTimeout(f, 0)` 을 「바로 다음」으로 읽는다

**마이크로태스크가 다 빠진 뒤**다(동작 (1)의 `T1` 은 10위). 이미 등록된 `then` 콜백과 **그 콜백들이 새로 건 것**까지 먼저 돈다.

### (2) ★★★ 「`nextTick` 은 언제나 `then` 보다 먼저」라고 외운다

**CommonJS 에서만 맞다.** 같은 파일을 ES 모듈로 돌리면 **`nextTick` 이 마이크로태스크 뒤로 간다**(동작 (3) — 4위 대 9위). 코드를 `.mjs` 로 옮기면 **말없이** 순서가 바뀐다.

### (3) ★★★ 마이크로태스크로 「잘게 쪼개 양보」한다

**양보가 아니다** — 체크포인트는 큐가 빌 때까지 안 끝나므로 **타이머가 0 번** 돈다(동작 (5)). 양보하려면 **매크로태스크**(`setTimeout`·`MessageChannel`·node 의 `setImmediate`)로 다시 건다.

### (4) ★★ 메인 모듈에서 `setTimeout` 0 과 `setImmediate` 의 순서에 기댄다

**판마다 바뀐다**(가짓수 `2`). I/O 콜백 안에서만 `setImmediate` 가 먼저로 **고정**된다(가짓수 `1`).

### (5) ★★ 여러 번 돌려 같았으니 순서가 보장된다고 믿는다

동작 (4)의 메인 모듈 순서는 **몇 판을 내리 같게 나오다가 바뀐다.** 보장은 **명세·문서**로만 적는다 — 이 문서의 「결정적」 칸은 전부 **명세(ECMA-262 · HTML)가 정한 자리**이거나 **관찰이라고 적은 자리**다.

### (6) ★★ 「`async` 함수를 부르면 본문은 나중에 돈다」

**첫 `await` 까지는 지금 돈다**(`A1` 이 `S2` 보다 먼저). 39번이 정본이다.

### (7) ★ `queueMicrotask` 를 언어 기능으로 안다

**HTML 의 API** 다 — ECMA-262 에 없다. node 도 구현해서 **어디서나 있는 것처럼 보일 뿐**이다.

### (8) ★ `file://` 로 연 페이지에서 미처리 거부 이벤트가 안 온다고 「거부가 없다」고 결론 낸다

이 배치의 실측 — **파일로 연 스크립트는 교차 출처로 취급되어**(muted errors) `unhandledrejection` 이 **아예 안 온다.** [37번](../37-promise-state-model/2-summary.md) 동작 (5)가 정본이다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262) — 어느 엔진에서도 같아야 하는 것

- ★★★ **프라미스 잡은 등록한 순서대로 돈다** — `then` 콜백 · `await` 재개가 이 줄이다. 동작 (1)의 `P1 → Q1 → A2 → P2 → P3` 중 `Q1` 을 뺀 넷이 여기서 나온다.
- ★★ **잡은 다른 코드가 돌고 있지 않을 때만 시작한다** — 그래서 동기 코드가 끝까지 돈다.
- ★★ `HostEnqueueTimeoutJob` 은 「**적어도** 그 시간 뒤에」만 말한다 — **정확히 언제**는 호스트의 몫이다.

### 호스트 — HTML event loop

- ★★★ **태스크 하나 → 마이크로태스크 체크포인트(빌 때까지) → 다음 태스크.** 기아가 여기서 나온다.
- ★★ **`queueMicrotask`** 는 프라미스 잡과 **같은 마이크로태스크 큐**에 넣는다(`Q1` 이 `P1` 과 `A2` 사이에 선다).
- ★★ **같은 지연의 타이머는 등록한 순서** · 중첩이 5 를 넘으면 **4ms 하한**(이 문서는 시간을 재지 않았다 — 순서만 봤다).

### 호스트 — node(libuv)

- ★★★ **`nextTick` 큐** — CommonJS 에서는 마이크로태스크보다 먼저, ES 모듈에서는 나중. **node 문서가 그렇게 적고, 두 판이 그렇게 돌았다.**
- ★★ **`setImmediate`** 와 libuv 의 단계 — 메인 모듈에서 `setTimeout` 0 과의 순서는 **정해져 있지 않다**(문서의 「non-deterministic」, 실측 가짓수 `2`).
- ★ **같은 지연의 타이머끼리 등록 순서** — node 에서는 **관찰**이다(이 문서가 node 의 보장 문장을 찾지 못했다).

### 구현(V8) · 이 판의 관찰

- 이 주제에서 **구현이 갈라 놓은 칸은 없었다** — node 20 과 Chrome 151 의 V8 이 호스트 전용 API 를 뺀 모든 탐침에서 같은 글자를 냈다(대조기).
- 가짓수 `2`·`1` — 300판에서 본 것이다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`process.nextTick` 은 마이크로태스크보다 먼저 돈다」 → ○ 「**CommonJS 에서.** ES 모듈에서는 마이크로태스크 뒤다」
- ✗ 「이벤트 루프는 JavaScript 언어의 일부다」 → ○ 「**언어는 잡의 순서까지**, 한 바퀴의 모양은 **호스트**(HTML · node)가 정한다」
- ✗ 「`setTimeout(f, 0)` 은 0ms 뒤에 돈다」 → ○ 「**적어도** 그만큼 뒤, 그리고 **마이크로태스크가 다 빠진 뒤**」 — 이 문서는 ms 를 **재지 않았다**
- ✗ 「마이크로태스크가 매크로태스크보다 빠르다」 → ○ **안 쟀다** — 「**먼저 돈다**」가 이 문서가 보인 것이다

## 언제 쓰고 언제 안 쓰나

- **`then`·`await`** — 값이 준비되면 **이 바퀴 안에서** 이어 가고 싶을 때(대부분의 비동기 코드).
- **`queueMicrotask`** — 프라미스를 만들 필요 없이 「지금 코드가 끝나면 곧바로」 돌리고 싶을 때. **자기 자신을 다시 걸지 않는다.**
- **`setTimeout(f, 0)`·`MessageChannel`** — **다른 태스크(입력·타이머·화면)에 차례를 넘기며** 긴 작업을 쪼갤 때.
- **`setImmediate`** — node 에서 **I/O 콜백 다음에** 확실히 돌리고 싶을 때. 메인 모듈에서 `setTimeout` 0 과의 순서에 기대지 않는다.
- **`process.nextTick`** — node 에서 **같은 콜백이 끝나자마자**(CommonJS 기준). ★ **안 쓰는 자리** — 모듈 형식을 가리지 않는 순서가 필요한 곳(ES 모듈에서 뒤집힌다).

## 핵심 문장

1. ★★★ 동기 코드는 끝까지 돌고, 그다음 **마이크로태스크가 빌 때까지**, 그다음 **매크로태스크 하나**다 — 한 파일의 열한 콜백이 세 호스트에서 **`N1` 하나를 빼고 한 글자도 같은 순서**로 찍혔다.
2. ★★★ **마이크로태스크끼리의 순서는 언어가**(잡은 등록 순서대로), **한 바퀴의 모양은 호스트가**(HTML 의 체크포인트 · node 의 libuv) 정한다.
3. ★★★ node 의 `nextTick` 은 **CommonJS 에서 4위, ES 모듈에서 9위**였다 — 「마이크로태스크보다 먼저」는 CommonJS 에서만 참이다.
4. ★★ 메인 모듈의 `setTimeout` 0 대 `setImmediate` 는 **300판에 두 가지 순서**, I/O 콜백 안에서는 **한 가지**였다.
5. ★★★ 마이크로태스크가 자기 자신을 다시 걸면 **10만 바퀴 동안 타이머가 0 번** 돈다 — 매크로태스크로 걸면 **turn 1 바로 다음**에 돈다.

## 관련 자료

- [ECMA-262 — Jobs and Host Operations to Enqueue Jobs](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html#sec-jobs) · [HTML — Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops) · [HTML — Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)
- [Node.js v20 — process](https://nodejs.org/docs/latest-v20.x/api/process.html#when-to-use-queuemicrotask-vs-processnexttick) · [Node.js — The Node.js Event Loop](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)
- [`history/js/04-비동기-진화.md`](../../../../../../history/js/04-비동기-진화.md) — ★ **경계**: 그쪽은 **콜백에서 `async` 까지의 연혁과 이벤트 루프의 큰 모양**, 여기는 **그 순서를 세 호스트에서 재고 언어·호스트 층을 가르는 것**부터.
- [`process-thread/`](../../../../process-thread/README.md) — 스레드·프로세스 일반. 여기는 **스레드 하나 위의 순서**만.
- [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) · [20 — 제너레이터](../20-generators/2-summary.md) · [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md)(`Array.fromAsync` 의 로그).
- [37 — Promise 상태 모델](../37-promise-state-model/2-summary.md)(프라미스 상태와 미처리 거부) · [38 — Promise 조합기](../38-promise-combinators/2-summary.md) · [39 — `async`/`await`](../39-async-await/2-summary.md)(`await` 의 틱 수).
- [Go 30 — `select`](../../../go/syntax/30-select-default-and-timeouts/2-summary.md) — 가짓수 격자의 짝. 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **51번**(`asyncio` 코루틴 기초).

## 용어 풀이

- **이벤트 루프(event loop)** — 할 일을 큐에서 하나씩 꺼내 돌리는 호스트의 반복. **언어가 아니라 호스트**(HTML · node)가 정한다.
- **매크로태스크(태스크)** — 한 바퀴에 하나만 꺼내는 일감. 스크립트 전체 · 타이머 콜백 · I/O 완료.
- **마이크로태스크** — 지금 코드가 끝나면 **빌 때까지** 도는 일감. `then` 콜백 · `queueMicrotask` · `await` 재개.
- **마이크로태스크 체크포인트** — HTML 이 마이크로태스크 큐를 비우는 알고리즘. 「비어 있지 않은 동안」 꺼낸다.
- **잡(Job)** — ECMA-262 의 말. 다른 코드가 돌지 않을 때 시작하는 계산 하나. 프라미스 잡은 **등록 순서대로** 돈다.
- **run-to-completion** — 한 번 시작한 코드는 끝까지 돈다는 것. 다른 콜백이 **중간에** 끼어들지 않는다.
- **`process.nextTick`** — node 의 별도 큐. CommonJS 에서는 마이크로태스크보다 먼저 비운다.
- **`setImmediate`** — node 의 check 단계에서 도는 콜백.
- **libuv** — node 의 이벤트 루프를 구현한 C 라이브러리. timers · poll · check 같은 **단계**가 있다.
- **기아(starvation)** — 앞줄이 끊이지 않아 뒷줄이 차례를 못 받는 것.
- **가짓수** — 여러 판을 돌려 **서로 다른 결과가 몇 가지였나**. 흔들리는 순서를 결정적으로 싣는 방법(규칙 11).

## 더 들어가면

- **렌더링과 `requestAnimationFrame`** — HTML 의 한 바퀴에서 체크포인트 **뒤**에 온다. 이 문서는 **재지 않았다**(헤드리스 페이지에서 프레임을 세지 않았다).
- **`MessageChannel` 을 이용한 양보** — 타이머의 4ms 하한을 피하는 방법으로 알려져 있다. **이 문서는 돌리지 않았다.**
- **워커·`Atomics.wait`** — 스레드가 여럿이 되는 자리. 연혁 문서의 「동시성 — 진짜 병렬이 필요할 때」 절이 연혁 쪽 정본이다.
