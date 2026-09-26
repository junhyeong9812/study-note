# js/syntax/41 — 취소와 타임아웃: 「프라미스에는 취소가 없다 — `AbortSignal` 은 호스트가 주는 『그만』 쪽지이고, 읽는 쪽이 멈춘다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다** — 다섯 걸음짜리 작업의 걸음마다, `abort()` 를 부른 자리에, **호출자가 무엇을 받았나**에 로그를 심는다. 「`abort()` 해도 **이미 시작된 작업은 계속 돈다**」를 **로그 줄로** 보인다(동작 (1)).
> ★★ 보조로 **② 전수 격자**(`reason` 7행 · 취소 나무 3행의 「`aborted N / 7`」 · `fetch` 4행의 「`node18 and node20 differ N / 4`」)와 **④ 예외의 `constructor.name` + `name` + `message`**(`AbortError` 대 `TimeoutError` · 판마다 다른 문구)를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [WHATWG DOM Standard — Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities) — 「signal abort: **reason 이 주어지면 그것, 아니면 새 `"AbortError"` `DOMException`**」 · `timeout(ms)`: 「**새 `"TimeoutError"` `DOMException`** 으로 signal abort」 · `throwIfAborted()`: 「**abort 됐으면 이것의 abort reason 을 던진다**」 · `any(signals)`: 「dependent abort signal 을 만든다 — 의존 신호에 **원본의 abort reason 을 그대로** 넣는다」
> - [Node.js v20 — Globals](https://nodejs.org/docs/latest-v20.x/api/globals.html) — `AbortController` **v15.0.0**(v14.17.0) · `AbortSignal.timeout` **v17.3.0**(v16.14.0) · `AbortSignal.any` **v20.3.0** · `throwIfAborted` **v17.3.0**(v16.17.0) · `fetch` **v18.0.0 에서 실험 딱지를 뗐다**
> - [ECMA-262 — `Promise.prototype`](https://tc39.es/ecma262/multipage/control-abstraction-objects.html) — 메서드는 `then`·`catch`·`finally` 셋이다(동작 (1)의 `[0]` 이 같은 셋을 찍었다)
>
> ★★★ **`AbortController`·`AbortSignal`·`DOMException` 은 ECMA-262 에 없다 — DOM 표준(호스트)의 것이다.** node 는 같은 API 를 **자기 구현**으로 준다. 이 문서의 「보장」은 **DOM 표준 문장**이고, 문구·종료·타이머 성질은 **판의 관찰**이다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다. Chrome 151 은 `./js40b-browser.sh`(소스는 [42번](../42-esm-modules/2-summary.md) 머리말 · `fetch` 는 `--http` 로 로컬 서버를 띄웠다).
> ★★★ **판이 갈린 자리가 둘 있다** — ① **`message` 문구**(node 는 `This operation was aborted`, Chrome 은 `signal is aborted without reason`) · ② **node 18 의 `fetch` 가 `abort("mine")` 을 `TypeError 「invalid_argument」` 로 바꿨다**(node 20 은 `"mine"` 그대로 — 동작 (4)).
> ★★ **시간은 한 번도 재지 않았다** — `timeout-50ms` 행은 「**`TimeoutError` 로 거부되나**」만 근거로 쓴다(서버 쪽 칸은 경쟁이라 안 찍었다).
>
> **버전**
>
> | 무엇 | 누구의 것 | 이 머신에서 |
> |---|---|---|
> | 프라미스에 취소가 없다 | **ECMA-262** | 세 판 다 `then, catch, finally` 뿐(동작 (1)) |
> | `AbortController` · `signal.reason` · `AbortSignal.abort` | DOM · node v15.0.0(문서) | 세 판 다 있다 |
> | `AbortSignal.timeout` · `throwIfAborted` | DOM · node v17.3.0(문서) | 세 판 다 있다 |
> | `AbortSignal.any` | DOM · node **v20.3.0**(v20 문서) | ★ **node 18.19.1 에도 있었다**(판별 블록 — v20 문서는 18 계열 판을 적지 않는다) |
> | `fetch` | fetch 표준 · node v18.0.0 부터 실험 아님(문서) | 세 판 다 있다 — 단 **abort reason 전달이 node 18 에서 달랐다** |
>
> ★★ **판 경계는 TC39 표로 가를 수 없다** — 이 API 들은 TC39 제안이 아니다. 위 판은 **node v20 문서의 「Added in」** 과 판별 블록이다. README 41행은 판을 적지 않는다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | 작업의 걸음 · `-- abort() called` · 호출자가 받은 것 — **`abort()` 뒤에도 `job step 3` 이 찍히나**(동작 (1)) |
> | ★★ **② 전수 격자** | `reason` 7행(동작 (2)) · 취소 나무 3행 「`aborted N / 7`」(동작 (3)) · `fetch` 4행 「`differ N / 4`」(동작 (4)) |
> | ★★ **④ 예외의 `constructor.name` + `name` + `message`** | `DOMException` · `AbortError`/`TimeoutError` · `code` 20/23 · 판마다 다른 문구 |
> | ★ **창을 바꿔 물었다**(제5의 상태) | 「`fetch` 를 끊으면 **서버는** 무엇을 보나」를 브라우저가 아니라 **node 안의 서버**로 물었다 — 페이지는 서버 쪽을 못 본다(동작 (4)) |
> | ★ **부적용 — ③ 브랜드 태그** | 판정할 객체의 종류가 없다(`reason` 의 종류는 `constructor.name` 으로 충분했다) |
> | ★ **못 잰 것** | Chrome 의 `AbortSignal.timeout` + `fetch` — 하네스의 `--virtual-time-budget` 아래에서는 페이지 시계가 가상이라 **`fulfilled 200` 이 나왔다**. 근거가 못 되므로 빼고, 그 행은 node 로만 적었다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 | ★★★ 로그의 **줄 순서** · `aborted N / 7` · `=== signal.reason` · 종료 코드 — `abort()` 는 **로그를 찍은 그 자리에서** 부르고, 걸음은 `setTimeout` 0 이다 |
> | ★ `timeout-50ms` 에서 **요청이 서버에 닿았나** — 경쟁이라 **찍지 않았다** | ★★ **판 사이의 문구 차이**는 흔들림이 아니라 **판의 차이**다(세 판 모두 재실행에서 같았다) |
>
> **층** — **언어(ECMA-262)** 가 정하는 것은 하나다 — **프라미스에는 취소 연산이 없다.** `AbortController`·`AbortSignal`·`DOMException`·`fetch` 는 **호스트(DOM·fetch 표준, 그리고 node 의 구현)** 다.
>
> **선행** — [39 — `async`/`await`](../39-async-await/2-summary.md)(직접 선행 — `await` 가 멈추는 자리가 곧 **취소를 확인할 자리**다) ·
> [38 — Promise 조합기](../38-promise-combinators/2-summary.md)(★★★ **`all` 이 거부돼도 입력 작업은 끝까지 갔다** — 여기서는 **`abort()` 해도** 같은지 본다) ·
> [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md)(`DOMException` 이 `Error` 인가 · `cause`) ·
> [40 — 비동기 이터레이션](../40-async-iteration-and-for-await/2-summary.md)(루프를 떠나면 `return()` 이 불린다 — 신호로 끊을 때도 같은 출구다).
>
> ★★★ **경계** —
> - **데드라인 전파의 설계**(타임아웃 대 데드라인 · 고아 작업 · 진입점 → 작업 → DB → 외부 연결 → 큐 · 취소가 닿지 않는 곳)는 [`ops-patterns/deadline-propagation/`](../../../../../ops-patterns/deadline-propagation/2-summary.md) 가 정본이다 — 그 문서의 **「2. 고아 작업 — 클라이언트가 끊어도 서버는 모른다」** 와 **「3-2. 작업 스레드」**(「**취소는 협조적이다**」)가 이 주제의 동작 (1)·(4)를 **설계 쪽에서** 말한다. **그쪽은 「무엇을 어디까지 넘기나」의 설계까지**, 여기는 **JS 의 `AbortSignal` API 가 그 협조를 어떻게 모양 짓나**부터.
>   ★ README 41행은 이 정본을 `cs/ops-patterns/deadline-propagation.md` 로 적지만 **실제로는 폴더**(`deadline-propagation/`)다 — README 는 고치지 않았다(범위 밖).
> - **`signal` 로 리스너를 떼는 것**은 web-api 갈래의 [20번](../../../../web-api/20-listener-lifetime/2-summary.md)(과 [15번](../../../../web-api/15-listener-registration/2-summary.md))이 Chrome 에서 쟀다 — 「**이미 abort 된 signal 로 등록하면 아예 안 붙는다**(호출 0회)」. 여기서는 **node 의 `EventTarget` 도 같은지**만 한 줄 본다(동작 (5)).
> - **네트워크 쪽 취소**(`fetch` 와 `timeout`/`any` 의 조합 설계)는 web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **27번** — 아직 폴더가 없다.
> - ★★ **Go `context`** 의 취소 나무는 Go 갈래 [34번](../../../go/syntax/34-context-cancellation-deadlines-and-values/2-summary.md)이 정본이다(`7 / 7` · `2 / 7`). 동작 (3)이 **같은 나무를 `AbortSignal.any` 로** 세운다.

```text
===== ./js40b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           no
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           no
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             yes
Google Chrome 151.0.7922.173
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           yes
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             no
```

세 판 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 3 · differs 3 · node only 3`

## 한눈에 — 쉽게 말하면

**`AbortSignal` 은 「작업자 책상에 붙이는 『그만』 쪽지」다. 관리자(`AbortController`)가 쪽지를 붙여도, 작업자가 쪽지를 들여다보지 않으면 일은 끝까지 간다. 프라미스는 그 작업의 「결과 받는 창구」일 뿐이라 작업을 멈출 손잡이가 없다.**

- ★★★ **창구에는 멈춤 버튼이 없다** — `Promise.prototype` 에는 `then`·`catch`·`finally` 뿐이다. 「결과를 안 기다린다」는 할 수 있어도 「일을 멈춘다」는 **프라미스로는** 못 한다.
- ★★★ **쪽지는 읽어야 효과가 있다** — 작업이 걸음마다 `signal.throwIfAborted()` 로 쪽지를 보면 멈춘다. 안 보면 **`abort()` 뒤에도 계속 돈다.**
- ★★ **창구만 닫으면 거짓 안심이다** — 호출자 쪽에서 「abort 되면 거부」로 감싸면 **호출자는 곧바로 `AbortError` 를 받지만** 작업은 **뒤에서 끝까지** 돈다.
- ★★ **쪽지에는 이유가 적힌다** — 아무것도 안 적으면 `AbortError`, 시간이 다 돼서 붙은 쪽지는 `TimeoutError`, 직접 적으면 **적은 값 그대로**.

```text
   관리자                         작업자                         결과 창구(프라미스)
   c = new AbortController()
   job(c.signal) ───────────────▶ step 1
                                  step 2
   c.abort()  ── 쪽지를 붙인다 ─▶ (쪽지를 보나?)
                                     ├─ 본다: throwIfAborted() ─▶ 멈춤 ───▶ rejected AbortError
                                     └─ 안 본다: step 3 · 4 · 5 ─▶ 끝 ────▶ fulfilled "job result"

   프라미스에는 이 화살표를 거꾸로 보낼 길이 없다 — then · catch · finally 뿐
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 결과 받는 창구 | 프라미스 — `then`·`catch`·`finally` 뿐 | 동작 (1)의 `[0]` |
| 관리자 / 쪽지 | `AbortController` / 그 `signal` | 동작 (1) |
| 쪽지를 들여다본다 | `signal.throwIfAborted()` · `signal.aborted` · `abort` 이벤트 | 동작 (1)의 `[2]` |
| 쪽지에 적힌 이유 | `signal.reason` — 기본 `AbortError`, 시간 초과 `TimeoutError`, 아니면 준 값 | 동작 (2) |
| 부서마다 끈으로 이은 쪽지 | `AbortSignal.any([부모, 내 것])` — 부모가 끊기면 나도 | 동작 (3) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**타임아웃으로 요청을 포기했는데 서버 로그에는 요청이 끝까지 처리됐다**」,
「**`Promise.race([work(), timeout()])` 로 시간 제한을 걸었더니 `work` 가 뒤에서 계속 DB 에 썼다**」,
「**`catch (e)` 에서 `e.name === 'AbortError'` 로 갈랐는데 시간 초과는 `TimeoutError` 라 새어 나갔다**」가 그것이다(동작 (1)·(2)·(4)).

> **`AbortSignal`** — 「그만」 여부(`aborted`)와 그 이유(`reason`)를 들고 있는 객체. 받은 쪽이 **스스로 확인해** 멈춘다.\
> 예: `const c = new AbortController(); fetch(url, { signal: c.signal }); c.abort();`

## 이 주제가 답하려는 질문

1. **`abort()` 를 부르면 이미 시작된 작업은 멈추나** — 작업이 신호를 안 볼 때 · 볼 때 · 호출자만 감쌀 때 각각 무엇이 찍히나?
2. **`signal.reason` 은 무엇이 되나** — 인자 없음 · 값 · 시간 초과 · 두 번째 `abort` · `any` · `throwIfAborted` 는 무엇을 던지나?
3. **`AbortSignal.any` 로 세운 취소 나무는 Go `context` 와 같은 범위로 번지나** — 그리고 `fetch` 를 끊으면 호출자와 **서버**는 각각 무엇을 보나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 「프라미스에는 취소가 없다」 — 로그로

**언제 쓰나** — 오래 걸리는 작업에 취소 버튼을 달 때 · `Promise.race` 나 감싸개로 「시간 제한」을 걸 때.
★★★ 작업은 **다섯 걸음**(`setTimeout` 0 하나씩)이고, **`job step 2` 를 찍은 바로 그 자리에서** `abort()` 를 부른다. 시간을 기다려 부르지 않는다.

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

```text
===== node20 js40b-41a-abort-mid-job.js (exit=0) =====
[0] Promise.prototype: then, catch, finally · 'cancel' in it: false
[1] job ignores the signal
  job step 1 > job step 2 > -- abort() called > job step 3 > job step 4 > job step 5 > job returns > caller got fulfilled "job result"
[2] job checks signal.throwIfAborted()
  job step 1 > job step 2 > -- abort() called > caller got rejected DOMException AbortError 「This operation was aborted」
[3] caller's wrapper rejects on abort, job ignores the signal
  job step 1 > job step 2 > -- abort() called > caller got rejected DOMException AbortError 「This operation was aborted」 > job step 3 > job step 4 > job step 5 > job returns
```

같은 소스를 Chrome 151 에서 — **줄 순서는 한 글자도 같고, `message` 문구만** 다르다.

```text
===== ./js40b-browser.sh js40b-41a-abort-mid-job.js (exit=0) =====
[0] Promise.prototype: then, catch, finally · 'cancel' in it: false
[1] job ignores the signal
  job step 1 > job step 2 > -- abort() called > job step 3 > job step 4 > job step 5 > job returns > caller got fulfilled "job result"
[2] job checks signal.throwIfAborted()
  job step 1 > job step 2 > -- abort() called > caller got rejected DOMException AbortError 「signal is aborted without reason」
[3] caller's wrapper rejects on abort, job ignores the signal
  job step 1 > job step 2 > -- abort() called > caller got rejected DOMException AbortError 「signal is aborted without reason」 > job step 3 > job step 4 > job step 5 > job returns
```

```text
   [1] 신호를 안 본다       step 1 · step 2 · abort() · step 3 · step 4 · step 5 · returns ─▶ fulfilled "job result"
   [2] throwIfAborted()     step 1 · step 2 · abort() · ✕ 다음 걸음 전에 던진다             ─▶ rejected AbortError
   [3] 호출자만 감싼다       step 1 · step 2 · abort() ─▶ rejected AbortError (호출자는 여기서 끝)
                                                   └─ step 3 · step 4 · step 5 · returns   (작업은 뒤에서 계속)
```

- ★★★ **`[1]` — `-- abort() called` 뒤에도 `job step 3 > job step 4 > job step 5 > job returns`**, 호출자는 **`fulfilled "job result"`** 를 받았다. `abort()` 는 **쪽지를 붙였을 뿐** 아무것도 멈추지 않는다.
- ★★★ **`[2]` — `throwIfAborted()` 가 다음 걸음 **전에** 던져 `step 3` 이 없다.** 멈춘 것은 **작업이 스스로 확인했기 때문**이다. DOM 표준이 `throwIfAborted` 를 「**신호를 넘길 수 없는 비동기 작업 사이의 확인 지점**」으로 설명하는 그대로다.
- ★★★ **`[3]` — 호출자는 `abort()` 직후 `rejected AbortError` 를 받았는데, 그 뒤에 `job step 3 … job returns` 가 찍혔다.** 감싸개는 **기다리기를 그만뒀을 뿐** 작업을 멈추지 못한다. 38번 동작 (2)의 「`all` 이 거부돼도 입력은 끝까지 갔다」와 **같은 성질의 취소판**이다.
- ★★ **`[0]` — `Promise.prototype` 은 `then, catch, finally` 뿐이고 `'cancel' in it: false`** — 세 판이 같았다.

### (2) ★★★ `reason` — 무엇이 전달되나, `AbortError` 와 `TimeoutError`

**언제 쓰나** — `catch` 에서 「취소인가 · 시간 초과인가 · 진짜 실패인가」를 가를 때 · `abort()` 에 이유를 넣을 때.

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

```text
===== node20 js40b-41b-reasons.js (exit=0) =====
[1] signal.reason
  controller.abort()                      DOMException · AbortError · 「This operation was aborted」 · 20 · true
  controller.abort(undefined)             DOMException · AbortError · 「This operation was aborted」 · 20 · true
  controller.abort("stop")                string · "stop"
  controller.abort(new Error("mine"))     Error · Error · 「mine」 · - · true
    same object as the Error passed in    true
  AbortSignal.abort()                     DOMException · AbortError · 「This operation was aborted」 · 20 · true
  AbortSignal.timeout(0), after abort     DOMException · TimeoutError · 「The operation was aborted due to timeout」 · 23 · true
[2] a second abort(), and AbortSignal.any
  abort("first") then abort("second")     string · "first"
  any([src, other]) after src.abort(e)    aborted true · reason === e true
[3] throwIfAborted()
  on an aborted signal, threw             "why" · same as reason true
  on a live signal, returned              undefined
[4] addEventListener with { signal } on a plain EventTarget -- calls after dispatching once
  live signal                             1
  after that signal's abort()             0
  registered with an aborted signal       0
```

Chrome 151 — **종류·`name`·`code`·`true`/`false` 는 한 글자도 같고, `message` 만** 다르다.

```text
===== ./js40b-browser.sh js40b-41b-reasons.js (exit=0) =====
[1] signal.reason
  controller.abort()                      DOMException · AbortError · 「signal is aborted without reason」 · 20 · true
  controller.abort(undefined)             DOMException · AbortError · 「signal is aborted without reason」 · 20 · true
  controller.abort("stop")                string · "stop"
  controller.abort(new Error("mine"))     Error · Error · 「mine」 · - · true
    same object as the Error passed in    true
  AbortSignal.abort()                     DOMException · AbortError · 「signal is aborted without reason」 · 20 · true
  AbortSignal.timeout(0), after abort     DOMException · TimeoutError · 「signal timed out」 · 23 · true
[2] a second abort(), and AbortSignal.any
  abort("first") then abort("second")     string · "first"
  any([src, other]) after src.abort(e)    aborted true · reason === e true
[3] throwIfAborted()
  on an aborted signal, threw             "why" · same as reason true
  on a live signal, returned              undefined
[4] addEventListener with { signal } on a plain EventTarget -- calls after dispatching once
  live signal                             1
  after that signal's abort()             0
  registered with an aborted signal       0
```

```text
   무엇으로 abort 했나              signal.reason                     e.name          code
   abort() · abort(undefined)      새 DOMException                    AbortError      20
   AbortSignal.timeout(ms)         새 DOMException                    TimeoutError    23
   abort("stop")                   "stop" 그대로                      (없다 — 문자열)   -
   abort(new Error("mine"))        그 객체 그대로 (=== true)           Error           -
   그 뒤 abort("second")            바뀌지 않는다 — 첫 이유가 남는다
   any([src, …]) · throwIfAborted   src 의 reason 을 그대로 · reason 을 그대로 던진다
```

- ★★★ **인자가 없으면(또는 `undefined`) `DOMException · AbortError · code 20`**, **`AbortSignal.timeout` 은 `DOMException · TimeoutError · code 23`** — **`name` 이 다르다.** `e.name === "AbortError"` 로만 거르면 **시간 초과가 새어 나간다.** 둘 다 `instanceof Error` 는 `true` 다.
- ★★★ **값을 주면 그 값 그대로** — 문자열 `"stop"` 은 `string`, `new Error("mine")` 은 **같은 객체**(`true`)다. `reason` 이 `Error` 라는 보장은 없다.
- ★★ **두 번째 `abort("second")` 는 무시** — `reason` 은 `"first"` 로 남는다(DOM 의 signal abort 첫 단계 「**이미 abort 됐으면 돌아간다**」).
- ★★ **`any([src, other])` 는 `src` 의 `reason` 을 같은 객체로** 받고(`reason === e true`), **`throwIfAborted()` 는 `reason` 자체를 던진다**(`"why" · same as reason true`) — 살아 있는 신호에서는 `undefined` 를 돌려줄 뿐이다.
- ★★ **문구는 표준이 정하지 않는다** — node 는 `This operation was aborted` · `The operation was aborted due to timeout`, Chrome 은 `signal is aborted without reason` · `signal timed out`. **근거로 쓸 칸은 `name`·`code`** 다.

### (3) ★★★ `AbortSignal.any` 로 세운 취소 나무 — Go `context` 와 나란히

**언제 쓰나** — 요청 하나에 딸린 작업들을 **한 번에** 끊고, 그 가운데 하나만 **따로** 끊고도 싶을 때.
★★ Go 34번의 나무(`root` → `a`·`b`·`c`, 각자 자식 하나)를 그대로 세웠다. 노드마다 **자기 컨트롤러**가 있고, 신호는 `any([부모 신호, 내 신호])` 다.

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

```text
===== node20 js40b-41c-signal-tree.js (exit=0) =====
abort root root=true a=true a1=true b=true b1=true c=true c1=true   aborted 7 / 7 · every aborted reason is the same object true
abort a    root=false a=true a1=true b=false b1=false c=false c1=false   aborted 2 / 7 · every aborted reason is the same object true
abort a1   root=false a=false a1=true b=false b1=false c=false c1=false   aborted 1 / 7 · every aborted reason is the same object true
```

```text
                 root                    root 를 끊으면       a 를 끊으면       a1 을 끊으면
               /  |  \
              a   b   c                  7 / 7                2 / 7 (a · a1)    1 / 7 (a1)
              |   |   |
              a1  b1  c1

   Go 34번 (context.WithCancel)          7 / 7                2 / 7             —
   이 문서 (AbortSignal.any)             7 / 7                2 / 7             1 / 7
```

- ★★★ **`root` 를 끊으면 `aborted 7 / 7`, `a` 를 끊으면 `2 / 7`** — Go 34번의 **`Done 을 받은 노드 7 / 7` · `2 / 7`** 과 같은 범위다. 취소는 **아래로만** 흐르고(`root=false` 가 남는다), 형제(`b`·`c`)는 건드리지 않는다.
- ★★ **모든 노드의 `reason` 이 같은 객체**(`true`) — DOM 이 의존 신호에 **원본의 abort reason 을 그대로** 넣는다. Go 의 `context.Cause` 가 원인을 나르는 자리와 대응한다(34번 — 이 문서는 Go 를 돌리지 않았다).
- ★★ **다른 점** — Go 는 `WithCancel` 이 **나무를 만드는 API** 이고 `cancel` 을 안 부르면 샌다(`vet lostcancel` — 34번). JS 는 `any` 가 **여러 신호를 묶는 API** 일 뿐이고 **정리 호출이 없다**(DOM 표준은 의존 신호의 수명을 **GC 절**로 다룬다 — web-api 20번이 그 절을 인용했다).
- ★ **같은 점** — 둘 다 **협조적**이다. Go 31번 (3)절은 고루틴이 **`ctx` 를 보게 고쳐서** 누수를 막았다(34번 머리말이 인용). 동작 (1)의 `[1]`·`[2]` 가 JS 쪽의 같은 이야기다.

### (4) ★★★ `fetch` 를 끊으면 — 호출자와 서버

**언제 쓰나** — 사용자가 페이지를 떠나거나 검색어를 바꿔 **앞 요청을 버릴** 때 · 시간 제한을 걸 때.
★★ node 안에 서버를 띄우고 `/hang` 은 **응답하지 않는다.** `abort-in-flight` 는 **서버가 요청을 받은 그 순간** 서버 쪽에서 `abort()` 를 부른다(시간을 기다리지 않는다).

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

```sh
# js40b-41d-node-fetch.sh
#!/usr/bin/env bash
# fetch() stopped four ways (js40b-41-h-fetch.js), on node20 and node18 -- then a timeout signal left alone in a program.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
diff=0; t=0
for how in abort-in-flight abort-in-flight-reason already-aborted timeout-50ms; do
  t=$((t + 1))
  echo "--- $how"
  a="$("$N20" js40b-41-h-fetch.js "$how")"; e20=$?
  b="$("$N18" js40b-41-h-fetch.js "$how")"; e18=$?
  printf '%s\n' "$a" | sed 's/^/  node20  /'
  echo "  node20  (exit $e20)"
  if [ "$a $e20" = "$b $e18" ]; then echo "  node18  the same"; else diff=$((diff + 1)); printf '%s\n' "$b" | sed 's/^/  node18  /'; echo "  node18  (exit $e18)"; fi
done
echo ""
echo "rows where node18 and node20 differ: $diff / $t"
echo ""
for v in 20 18; do
  [ $v = 18 ] && n="$N18" || n="$N20"
  for k in alone keep; do
    echo "--- node$v js40b-41-h-timeout-alone.js $k"
    "$n" js40b-41-h-timeout-alone.js "$k"
    echo "(exit $?)"
  done
done
```

```text
===== ./js40b-41d-node-fetch.sh (exit=0) =====
--- abort-in-flight
  node20  fetch rejected DOMException AbortError 「This operation was aborted」 · === signal.reason true
  node20  server: requests received 1 · saw the connection close yes
  node20  (exit 0)
  node18  the same
--- abort-in-flight-reason
  node20  fetch rejected "mine" · === signal.reason true
  node20  server: requests received 1 · saw the connection close yes
  node20  (exit 0)
  node18  fetch rejected TypeError TypeError 「invalid_argument」 · === signal.reason false
  node18  server: requests received 1 · saw the connection close yes
  node18  (exit 0)
--- already-aborted
  node20  fetch rejected DOMException AbortError 「This operation was aborted」 · === signal.reason true
  node20  server: requests received 0 · saw the connection close -
  node20  (exit 0)
  node18  the same
--- timeout-50ms
  node20  fetch rejected DOMException TimeoutError 「The operation was aborted due to timeout」 · === signal.reason true
  node20  server: - (this row does not report the server side)
  node20  (exit 0)
  node18  the same

rows where node18 and node20 differ: 1 / 4

--- node20 js40b-41-h-timeout-alone.js alone
end of the script
(exit 0)
--- node20 js40b-41-h-timeout-alone.js keep
end of the script
abort event: TimeoutError
(exit 0)
--- node18 js40b-41-h-timeout-alone.js alone
end of the script
(exit 0)
--- node18 js40b-41-h-timeout-alone.js keep
end of the script
abort event: TimeoutError
(exit 0)
```

Chrome 151 — 로컬 서버(`js40b-serve.py`)로 띄운 페이지에서 같은 세 행. **서버 쪽은 페이지가 못 본다.**

```js
// js40b-41e-fetch.web.js
// Three of the four ways of stopping fetch(), in Chrome, against js40b-serve.py's /hang (it answers after 2 seconds).
// The abort() calls come right after fetch() returns -- the page cannot see the server side.
// No timeout row: under this harness (--virtual-time-budget, a virtual page clock) it came back fulfilled 200, so it proves nothing here.
const show = (x) => (x && typeof x === "object" ? x.constructor.name + " " + x.name + " 「" + x.message + "」" : JSON.stringify(x));
const one = async (label, make) => {
  const { signal, after } = make();
  let got;
  const p = fetch("/hang?" + label, { signal });
  after();
  try { got = "fulfilled " + (await p).status; } catch (e) { got = "rejected " + show(e) + " · === signal.reason " + (e === signal.reason); }
  console.log(label.padEnd(24) + "fetch " + got);
};
(async () => {
  await one("abort-in-flight", () => { const c = new AbortController(); return { signal: c.signal, after: () => c.abort() }; });
  await one("abort-in-flight-reason", () => { const c = new AbortController(); return { signal: c.signal, after: () => c.abort("mine") }; });
  await one("already-aborted", () => ({ signal: AbortSignal.abort(), after: () => {} }));
})();
```

```text
===== ./js40b-browser.sh --http js40b-41e-fetch.web.js (exit=0) =====
abort-in-flight         fetch rejected DOMException AbortError 「signal is aborted without reason」 · === signal.reason true
abort-in-flight-reason  fetch rejected "mine" · === signal.reason true
already-aborted         fetch rejected DOMException AbortError 「signal is aborted without reason」 · === signal.reason true
```

```text
   abort-in-flight                    호출자                              서버
   fetch(url, { signal }) ──요청──▶                                     requests received 1
                                     c.abort()
                          ◀── rejected AbortError (=== signal.reason)
                          ── 연결을 끊는다 ──────────────────────────▶ saw the connection close yes
                                                                        (이미 받은 요청은 「없던 일」이 아니다)

   already-aborted        ✕ 요청을 보내지 않는다 ─▶ rejected AbortError   requests received 0
```

- ★★★ **`abort-in-flight` — 호출자는 `rejected DOMException AbortError`(`=== signal.reason true`), 서버는 `requests received 1 · saw the connection close yes`.** 서버는 **요청을 이미 받았다** — 끊은 것은 **연결**이지 서버가 한 일이 아니다. 데드라인 전파 정본의 「**클라이언트가 끊어도 서버는 모른다**」(고아 작업)가 이 줄이다.
- ★★ **`already-aborted` — `requests received 0`** — 이미 끊긴 신호로는 **요청조차 안 나간다.** 세 판이 같은 종류로 거부했다.
- ★★★ **`abort-in-flight-reason` 이 판마다 갈렸다**(`differ 1 / 4`) — **node 20 과 Chrome 151 은 `rejected "mine"`**(준 이유 그대로), **node 18 은 `TypeError 「invalid_argument」` · `=== signal.reason false`** 다. node 18 의 `fetch` 가 **문자열 이유를 제 오류로 바꿔치기**한 것이다 — `catch` 에서 `reason` 을 기대하는 코드는 node 18 에서 **조용히 다른 값을** 받는다.
- ★★ **`timeout-50ms` 는 `TimeoutError`** 로 거부됐다(두 node 판). 서버 쪽 칸은 **요청이 50ms 전에 닿았나가 경쟁**이라 찍지 않았다.
```text
   node 프로세스 — 「아직 기다릴 것이 있나」 (이 문서가 관찰로 본 모양)

   alone : AbortSignal.timeout(10) 만 있다      ─▶ 기다릴 것 없음 ─▶ exit 0   (abort 리스너는 끝내 안 불림)
   keep  : timeout(10) + setInterval(…)        ─▶ 기다린다 ─▶ abort event: TimeoutError ─▶ clearInterval ─▶ exit 0
```

- ★★★ **`AbortSignal.timeout` 은 node 프로세스를 붙잡지 않는다** — `alone` 은 `end of the script` 만 찍고 **`abort event` 없이 `exit 0`**, `keep`(다른 타이머가 있을 때)에서만 `abort event: TimeoutError` 가 왔다. 두 node 판이 같았다. **이것은 node 의 성질이다** — DOM 표준은 「abort 리스너가 있는 동안 **전역이 그 신호를 강하게 참조해야 한다**」고만 적는다(프로세스를 살려 두라는 말은 아니다).

### (5) ★ `{ signal }` 로 단 리스너 — node 의 `EventTarget` 에서도

**언제 쓰나** — 리스너 여러 개를 신호 하나로 뗄 때. **Chrome 쪽 정본은 web-api 20번**이다.
위 (2) 소스의 `[4]` 다.

- ★★ **살아 있는 신호 `1` → `abort()` 뒤 `0` → 이미 abort 된 신호로 등록 `0`** — node 의 `EventTarget` 에서도 web-api 20번이 Chrome 에서 잰 것과 **같은 세 숫자**가 나왔다(Chrome 151 도 같은 블록에서 같았다).
- ★ 그래서 **「abort 한 컨트롤러를 재사용」하면 조용히 안 붙는다** — web-api 20번의 결론이 호스트를 바꿔도 선다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 누구의 것 | 어디서 봤나 |
|---|---|---|---|
| `const c = new AbortController(); c.signal` | 쪽지와 관리자 한 쌍 | DOM | 동작 (1) |
| `c.abort()` · `c.abort(reason)` | 신호를 abort — 이유 없으면 `AbortError` · **두 번째 호출은 무시** | DOM | 동작 (2) |
| `AbortSignal.abort(reason?)` | 처음부터 abort 된 신호 | DOM | 동작 (2)·(4) |
| `AbortSignal.timeout(ms)` | `ms` 뒤 `TimeoutError` 로 abort — ★ node 에서는 프로세스를 안 붙잡는다 | DOM · node | 동작 (2)·(4) |
| `AbortSignal.any([s1, s2])` | 하나라도 abort 되면 abort — **원본 `reason` 그대로** | DOM | 동작 (2)·(3) |
| `signal.throwIfAborted()` | abort 됐으면 **`reason` 을 던진다** | DOM | 동작 (1)·(2) |
| `fetch(url, { signal })` | abort 되면 **`signal.reason` 으로 거부** | fetch 표준 | 동작 (4) |
| `addEventListener(t, f, { signal })` | abort 되면 리스너를 뗀다 · 이미 abort 면 **안 단다** | DOM | 동작 (5) · web-api 20번 |

- **신호는 작업에 넘기고, 작업이 확인한다** — 걸음마다 `throwIfAborted()`, 또는 API(`fetch`·`addEventListener`)에 넘긴다.
- **이유를 가를 때는 `name`**(`AbortError`/`TimeoutError`) 또는 **`=== signal.reason`** 을 쓴다. 문구는 판마다 다르다.

## 어디서 틀리나

### (1) ★★★ 「`abort()` 하면 작업이 멈춘다」

**작업이 신호를 보지 않으면 끝까지 돈다**(`[1]` 의 `job step 3 … job returns`). `abort()` 는 신호의 상태를 바꾸고 리스너를 부를 뿐이다.

### (2) ★★★ 「타임아웃 감싸개(`race`·abort 거부)로 작업을 멈췄다」

**호출자가 기다리기를 그만뒀을 뿐이다**(`[3]` — `rejected AbortError` 뒤에 `job step 3 … job returns`). 부작용이 있는 작업이면 **신호를 작업 안까지** 넘긴다.

### (3) ★★★ `catch` 에서 `e.name === "AbortError"` 만 본다

**시간 초과는 `TimeoutError`** 다(`code 23`). 그리고 **직접 준 이유는 그 값 그대로** 온다(`"stop"` — `name` 이 없다). `signal.aborted` 나 `e === signal.reason` 으로 가른다.

### (4) ★★★ 요청을 끊었으니 서버에서는 「없던 일」이라 믿는다

**서버는 이미 받았다**(`requests received 1`). 끊은 것은 연결이다 — 서버가 무엇을 했는지는 이쪽이 모른다(데드라인 전파 정본의 고아 작업).

### (5) ★★ `abort(reason)` 의 이유가 어느 판에서나 `fetch` 의 거부값이라 믿는다

**node 18 은 `TypeError 「invalid_argument」` 로 바꿨다**(동작 (4)). node 20 · Chrome 151 은 그대로였다.

### (6) ★★ 문구 `This operation was aborted` 로 판정한다

**Chrome 151 은 `signal is aborted without reason`** 이다. 문구는 표준 밖이다.

### (7) ★★ `AbortSignal.timeout` 만 걸어 두면 node 가 그때까지 기다려 준다고 믿는다

**안 기다린다** — 다른 일이 없으면 `abort event` 없이 `exit 0` 으로 끝났다(동작 (4)의 `alone`).

### (8) ★ abort 한 컨트롤러를 다음에 재사용한다

**이미 abort 된 신호로 단 리스너는 안 붙는다**(`0` — 동작 (5) · web-api 20번). 매번 새 컨트롤러를 만든다.

## 구현 세부사항 대 언어 보장

### 명세 보장

- ★★★ **ECMA-262** — 프라미스에는 **취소 연산이 없다**(`Promise.prototype` 은 `then`·`catch`·`finally`). 이 주제에서 언어가 보장하는 것은 이 **부재** 하나다.
- ★★★ **DOM 표준** — signal abort 는 **이유가 없으면 새 `AbortError` `DOMException`** · **이미 abort 됐으면 아무것도 안 한다** · `timeout` 은 **`TimeoutError`** · `any` 는 의존 신호에 **원본 `reason` 을 그대로** · `throwIfAborted` 는 **`reason` 을 던진다**.
- ★★ **fetch 표준** — 요청을 **신호의 abort reason 으로** 끝낸다(node 20 · Chrome 151 이 그랬다).

### 호스트(node)

- ★★★ **`AbortSignal.timeout` 의 타이머가 프로세스를 붙잡지 않는다**(두 판 관찰) — 표준 문장에는 없는 **node 의 성질**이다.
- ★★ **node 18 의 `fetch` 는 문자열 `reason` 을 `TypeError 「invalid_argument」` 로 바꿨다** — node 20 에서는 사라졌다.
- ★ `AbortSignal.any` — v20 문서는 **v20.3.0** 만 적는데 **node 18.19.1 에도 있었다.**

### 구현 · 이 판의 관찰

- ★★ **`message` 문구** — node 와 Chrome 이 다르다(동작 (1)·(2)·(4)).
- ★ `DOMException` 이 `instanceof Error` 로 `true` — 세 판 같았다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`AbortController` 로 프라미스를 취소한다」 → ○ 「**신호를 보낸다** — 작업이 그 신호를 확인해야 멈춘다. 프라미스에는 취소가 없다」
- ✗ 「`Promise.race` 로 타임아웃을 걸면 느린 작업이 멈춘다」 → ○ 「**호출자만 떠난다** — 작업은 끝까지 간다」
- ✗ 「`AbortController` 는 자바스크립트 표준이다」 → ○ 「**DOM 표준(호스트)** 이다 — ECMA-262 에 없다」
- ✗ 「시간 초과도 `AbortError` 다」 → ○ 「**`TimeoutError`**(`code 23`)」

## 언제 쓰고 언제 안 쓰나

- **신호를 인자로 받는 함수** — `async function load(url, { signal } = {})` 로 받아 **`fetch` 에 넘기고, 걸음 사이마다 `signal?.throwIfAborted()`**.
- **`AbortSignal.timeout(ms)`** — 요청 하나의 시간 제한. **`any([사용자 취소, timeout])`** — 둘 중 먼저 오는 것.
- **`any([부모, 내 것])`** — 요청 단위로 딸린 작업을 한 번에 끊는 나무(동작 (3)).
- ★ **안 쓰는 자리** — 「작업을 멈춘다」는 뜻으로 `race` 감싸개만 두기 · abort 한 컨트롤러 재사용 · 문구로 이유 판정.

## 핵심 문장

1. ★★★ **프라미스에는 취소가 없다** — `abort()` 뒤에도 신호를 안 보는 작업은 **`job step 3 … job returns`** 까지 갔고 호출자는 **`fulfilled`** 를 받았다.
2. ★★★ **멈추는 것은 작업 자신이다** — `throwIfAborted()` 로 확인하면 다음 걸음 **전에** 멈춘다. 호출자만 감싸면 호출자는 떠나도 **작업은 뒤에서 계속** 돈다.
3. ★★★ `reason` 은 기본 **`AbortError`(20)**, 시간 초과 **`TimeoutError`(23)**, 아니면 **준 값 그대로** — 두 번째 `abort` 는 무시된다. 문구는 판마다 다르다.
4. ★★★ `any([부모, 내 것])` 나무는 Go `context` 와 **같은 범위로** 번졌다 — `7 / 7` · `2 / 7`. 둘 다 **협조적**이다.
5. ★★ `fetch` 를 끊으면 호출자는 `signal.reason` 으로 거부되지만 **서버는 이미 받았다** — node 18 은 문자열 이유를 `TypeError` 로 바꿨고, node 의 `timeout` 은 **프로세스를 붙잡지 않는다.**

## 관련 자료

- [DOM Standard — Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities) · [Node.js v20 — Globals](https://nodejs.org/docs/latest-v20.x/api/globals.html)
- [`ops-patterns/deadline-propagation/`](../../../../../ops-patterns/deadline-propagation/2-summary.md) — ★ **경계**: 그쪽은 **타임아웃 대 데드라인 · 고아 작업 · 전파 경로의 설계**, 여기는 **JS `AbortSignal` API 의 동작**부터.
- Go 갈래 [34 — `context`](../../../go/syntax/34-context-cancellation-deadlines-and-values/2-summary.md) — 취소 나무의 정본(`7 / 7` · `2 / 7`).
- web-api 갈래 [20 — 리스너 수명](../../../../web-api/20-listener-lifetime/2-summary.md) · [15 — 리스너 등록](../../../../web-api/15-listener-registration/2-summary.md) — `signal` 로 떼기. web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **27번** — 네트워크 쪽 취소.
- [38 — Promise 조합기](../38-promise-combinators/2-summary.md) — 조합기도 취소하지 않는다. [39](../39-async-await/2-summary.md) · [32](../32-error-handling-and-error/2-summary.md) · [40](../40-async-iteration-and-for-await/2-summary.md).

## 용어 풀이

- **`AbortController`** — 신호 하나를 만들고 그것을 abort 할 수 있는 객체.
- **`AbortSignal`** — `aborted`·`reason` 을 들고 `abort` 이벤트를 쏘는 객체. 받는 쪽이 확인한다.
- **abort reason** — 신호가 abort 된 이유. 기본은 `AbortError` `DOMException`.
- **`DOMException`** — DOM 표준의 예외 객체. `name`(`AbortError`·`TimeoutError`)과 옛 `code` 숫자를 가진다.
- **의존 신호(dependent signal)** — `AbortSignal.any` 가 만든 신호. 원본 중 하나가 abort 되면 같은 이유로 abort 된다.
- **협조적 취소** — 멈추라는 신호를 받는 쪽이 **스스로 확인해** 멈추는 방식. JS 의 `AbortSignal` 과 Go 의 `context` 가 둘 다 그렇다.
- **고아 작업** — 요청한 쪽은 포기했는데 받은 쪽에서 계속 도는 작업(데드라인 전파 정본의 용어).
- **unref(node)** — 타이머가 **프로세스를 살려 두지 않게** 하는 node 의 성질. 동작 (4)의 `alone` 이 그 모양이었다.

## 더 들어가면

- **`AbortSignal.any` 의 수명** — DOM 표준은 abort 되지 않은 의존 신호를 **GC 절**에서 다룬다(web-api 20번이 인용). 이 문서는 회수 여부를 재지 않았다.
- **node 의 다른 API(`fs`·`timers/promises`·`events.once`)의 `signal`** — 이 문서는 `fetch` 와 `EventTarget` 만 돌렸다.
- **Chrome 에서의 `timeout` + `fetch`** — 가상 시간 없는 하네스라면 잴 수 있다. 이 문서의 하네스로는 **못 쟀다**(머리말).
