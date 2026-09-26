# web-api/39 — 유휴 스케줄링: `requestIdleCallback` · `scheduler.postTask()`/`yield()` 와 긴 작업 쪼개기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「디스패치 계수기」로 잰 「입력 막힘 판」이다** — 200ms 어치 작업을 **한 덩어리 · `scheduler.yield()` 로 네 조각 · `setTimeout 0` 으로 네 조각** 세 방식으로 돌리며, 작업을 시작하자마자 하네스가 **CDP `Input.dispatchMouseEvent`** 로 버튼을 누른다. 판마다 **클릭이 작업 중에 일어났나**(`event.timeStamp`) · **핸들러가 불린 때 끝난 조각 수** · **핸들러가 작업 끝 뒤였나**(참/거짓)를 적고, 다섯 판 중 몇 판인지를 스크립트가 센다. 둘째 축이 **이어가기 순서 로그**(yield 대 setTimeout · `postTask` 우선순위)다. ★ **시간은 찍지 않는다** — 참/거짓 · 순서 · 범주 · 판 수다.\
> **기준 소스** — ① [HTML — event loop processing model](https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model) 의 유휴 단계 — 「**Let deadline be this event loop's last idle period start time plus 50.**」 · 「**The cap of 50ms in the future is to ensure responsiveness to new user input within the threshold of human perception.**」 · 활성 타이머와 다음 렌더링이 마감을 **당긴다.** ② [W3C requestIdleCallback](https://w3c.github.io/requestidlecallback/) — 「start an idle period」 · 「invoke idle callback timeout」(`didTimeout`) · 숨은 문서의 유휴 기간은 **조절할 수 있다**. ③ [WICG Prioritized Task Scheduling](https://wicg.github.io/scheduling-apis/)(Draft Community Group Report, 2025-05-30) — 우선순위 셋 · **이어가기(continuation)의 유효 우선순위 표** · 스케줄러 태스크와 다른 태스크 사이의 선택은 「**implementation-defined**」. 받아서 읽은 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다(실제 시간 · `--virtual-time-budget` 없음). 하네스는 [36번 주제](../36-resize-observer/3-answer.md)의 `wa36b-net.py` — 부탁 창구의 「누르기」는 **응답을 기다리지 않고** 보낸다(기다리면 페이지가 한가해질 때까지 하네스가 막힌다). node 는 **v18.19.1 · v20.19.6** 두 판에 지원만 물었다.\
> **버전 · 지원** — README 의 Baseline 조회: `requestIdleCallback` 은 **limited**(Chrome 2015 · Firefox 2017 · **Safari 미구현**), Scheduler API(`postTask`/`yield`)는 **limited**(Chrome 2024-09 · Firefox 2025-08 · **Safari 없음**). **Safari 는 이 머신에 없어 미실행**이다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★ **[38번 주제](../38-request-animation-frame/2-summary.md)** — 렌더링 단계 · 틀 간격 · 숨은 탭. 유휴 기간의 마감이 「**다음 렌더링**」에 당겨지는 것이 그 편의 틀 박자와 이어진다. ★ [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/2-summary.md) 「어디서 틀리나 (3)」 — **마이크로태스크로 쪼개면 양보가 아니다**(타이머가 0 번 돈다). 이 편은 **태스크로 쪼개는** 두 방식만 다룬다.\
> **경계** — ★★★ **「`yield` 가 INP 를 줄인다」는 이 편이 주장하지 않는다 — INP 도 입력 지연 ms 도 재지 않았다.** 잰 것은 **핸들러가 작업 중간에 끼었나(참/거짓)** 다. ★★ **서버의 스케줄러**(방아쇠 · 밀린 실행을 몰아서/버리고/다시 세고)는 [`ops-patterns/10-scheduler`](../../../ops-patterns/10-scheduler/) 의 몫이다 — 그쪽은 「**언제 돌릴지**」를 벽시계로 정하고, 여기는 **한 스레드 안에서 「누구에게 먼저 양보할지」** 를 정한다. ★ 스레드 · 프로세스 일반은 [`process-thread`](../../process-thread/) 다.\
> 이 본문은 Claude 작성이다(원고 없음). 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 지원 여덟 줄 · node 네 줄 · 입력 막힘 판(다섯 판 중 몇 판) · 이어가기 순서 여섯 줄 · 유휴 가 \~ 라 | 캡처 세 판이 **한 글자도 같았다** |
| ★★ **흔들렸다** | **유휴 마 — 「rAF 마다 20ms 바쁜 500ms」 열 판의 두 수** | 캡처 세 판에서 앞의 수가 **4 · 5 · 4** / 10 으로 움직였다(뒤의 수는 5 · 5 · 5). **움직인다는 사실이 그 칸의 결론**이다((5)) — 재대조는 이 한 줄의 두 수만 `--rule` 로 정규화했다 |
| ★ **판에 매일 수 있는 칸** | 입력 막힘 판의 「끝난 조각 1」 | 클릭이 렌더러에 닿는 데 걸리는 시간이 50ms 조각 하나보다 짧다는 전제 위에 선다 |
| **흔들린다** | Chrome 판 번호 · 포트 | 출력에 안 나온다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 입력이 없다 · 틀을 못 기다린다 |
| 창 ② 노드 프로브 | ★ **쓴다** | `typeof` · `deadline.timeRemaining()` · `didTimeout` · `event.timeStamp` |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다** | 같은 200ms 를 **세 방식**으로 · 같은 세 조각을 **양보 둘**로 · 같은 물음을 **Chrome 과 node 두 판**에 |
| **창 ④ 디스패치 계수기 → 입력 막힘 판 · 이어가기 순서** | ★★★ **본체** | 핸들러가 **언제** 불렸나 · 누가 **먼저** 돌았나 |
| ★★ **「응답성」을 「끼어들었나」로** | ★★ **제5의 상태 — 같은 질문을 다른 창으로** | 「입력이 빨리 처리되나」를 ms 로 재지 않고 **「핸들러가 작업 중간에 불렸나 · 몇 조각 뒤였나」** 로 물었다. ★ 바꾼 창이 못 보는 것 — **얼마나 빨리**(지연 ms · INP) · 화면에 결과가 **언제 그려졌나** |
| 서버 요청 로그 | **부적용** | 네트워크를 안 쓴다 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **INP · 입력 지연 ms** | **재지 않았다**(머리말) |
| ★★ **Safari** | 이 머신에 없다 — Baseline 날짜로만 |
| **진짜 손 입력 · OS 입력 큐** | CDP 로 넣은 합성 입력뿐이다 |
| **숨은 탭의 유휴 기간** | 던지지 않았다 — 명세는 「10초에 한 번」 같은 조절을 **허용**한다 |

## 한눈에 — 쉽게 말하면

**★ 메인 스레드는 「계산대가 하나뿐인 가게」다. 손님 한 명(긴 작업)이 200ms 동안 계산대를 붙들면, 뒤에 선 급한 손님(클릭)은 그 계산이 다 끝날 때까지 기다린다. 계산을 네 번에 나눠 「잠깐만요」 하고 비켜 주면(양보) 급한 손님이 그 사이에 들어온다. 비켜 준 뒤 다시 차례를 받는 방식이 둘이다 — `setTimeout 0` 은 줄 맨 뒤로 다시 서고, `scheduler.yield()` 는 「하던 사람」 표를 받아 새 손님보다 앞에 선다. 가게가 한가할 때만 하는 일(재고 정리)은 `requestIdleCallback` 에 맡기는데, 점원이 쓸 수 있는 한가한 시간은 한 번에 최대 50ms 로 정해져 있다 — 그 뒤에 손님이 오면 바로 받으려고.**

| 비유 | 실체 |
|---|---|
| 계산대 하나 | 메인 스레드 — 태스크는 한 번에 하나, 도중에 안 끊긴다 |
| 200ms 붙듦 | 긴 동기 작업 — 클릭 핸들러가 **작업 끝 뒤**에 불린다 |
| 「잠깐만요」 | 조각 사이의 양보 — `await scheduler.yield()` · `await setTimeout 0` |
| 줄 맨 뒤 · 「하던 사람」 표 | 새 타이머 태스크 · 이어가기(continuation) — 유효 우선순위가 한 칸 높다 |
| 한가한 때만 · 최대 50ms | `requestIdleCallback` · `timeRemaining()` 상한 50 |
| 급한 순 · 보통 · 나중 | `postTask` 의 `user-blocking` · `user-visible` · `background` |

```text
   200ms 작업 중 클릭 (이 판 · 다섯 판 모두)

   한 덩어리        ████████████████████████████████ → 클릭 핸들러      ← 작업 끝 뒤
   yield 네 조각    ████████ → 클릭 핸들러 → ████████ ████████ ████████   ← 첫 조각 뒤
   setTimeout 네 조각 ████████ → 클릭 핸들러 → ████████ ████████ ████████ ← 첫 조각 뒤
   ★ 끼어들기는 둘 다 됐다 · 갈린 것은 「양보 뒤 누가 먼저」다 — (3)
```

## 이 주제가 답하려는 질문

1. **긴 동기 작업은 입력을 어떻게 막나 · 쪼개면 무엇이 달라지나** — 핸들러가 불린 자리.
2. **양보하는 방식들은 무엇이 다른가** — `yield` 대 `setTimeout 0` · `postTask` 우선순위 · 취소.
3. **각 API 의 지원 한계와 `requestIdleCallback` 의 규칙** — 무엇이 있나 · 50ms · `timeout`.

## 동작 방식

### (1) 지원 판별 — Chrome 151 과 node

```html
<!-- wa36b-39-support.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>39 support</title>
<script>
// 이 판의 Chrome 에 유휴·우선순위 스케줄링 표면이 있나 — typeof 로만 묻는다
const 물음 = [
  ["requestIdleCallback", () => typeof requestIdleCallback],
  ["cancelIdleCallback", () => typeof cancelIdleCallback],
  ["scheduler", () => typeof globalThis.scheduler],
  ["scheduler.postTask", () => typeof globalThis.scheduler?.postTask],
  ["scheduler.yield", () => typeof globalThis.scheduler?.yield],
  ["TaskController", () => typeof globalThis.TaskController],
  ["navigator.scheduling", () => typeof navigator.scheduling],
  ["navigator.scheduling.isInputPending", () => typeof navigator.scheduling?.isInputPending],
];
window.__끝 = () => 물음.map(([이름, f]) => `${이름}\t${f()}`).join("\n");
</script>
```

```text
$ python3 wa36b-net.py page wa36b-39-support.html
requestIdleCallback	function
cancelIdleCallback	function
scheduler	object
scheduler.postTask	function
scheduler.yield	function
TaskController	function
navigator.scheduling	object
navigator.scheduling.isInputPending	function
(exit 0)
```

```js
// wa36b-39-node.js
// 같은 물음을 node 에 던진다 — 전역에 있나(typeof) · 그리고 node 가 따로 가진 timers/promises 의 scheduler
const 물음 = ["requestIdleCallback", "scheduler", "TaskController", "queueMicrotask", "setImmediate"];
console.log(`node ${process.version}\t` + 물음.map(x => `${x}=${typeof globalThis[x]}`).join(" · "));
const s = require("timers/promises").scheduler;
const 메서드 = s ? Object.getOwnPropertyNames(Object.getPrototypeOf(s)).filter(k => k !== "constructor" && typeof s[k] === "function") : [];
console.log(`node ${process.version}\trequire("timers/promises").scheduler = ${typeof s} · 메서드 = ${메서드.join(", ") || "(없음)"}`);
```

```text
$ node wa36b-39-node.js; "$HOME/.nvm/versions/node/v20.19.6/bin/node" wa36b-39-node.js
node v18.19.1	requestIdleCallback=undefined · scheduler=undefined · TaskController=undefined · queueMicrotask=function · setImmediate=function
node v18.19.1	require("timers/promises").scheduler = object · 메서드 = yield, wait
node v20.19.6	requestIdleCallback=undefined · scheduler=undefined · TaskController=undefined · queueMicrotask=function · setImmediate=function
node v20.19.6	require("timers/promises").scheduler = object · 메서드 = yield, wait
(exit 0)
```

- ★★ **Chrome 151 에는 여덟 표면이 다 있다** — `navigator.scheduling.isInputPending` 까지 — **이 판에는 있고** 아래 (2)에서 실제로 `true` 를 돌려줬다(★ 폐기 일정은 확인하지 않았다 — 받은 명세에 없는 표면이다).
- ★★ **node 18 · 20 둘 다 `requestIdleCallback` · 전역 `scheduler` · `TaskController` 가 `undefined`** 다. 대신 node 는 **`require("timers/promises").scheduler`** 에 `yield` · `wait` 를 따로 둔다 — **이름만 같은 다른 API** 다(브라우저의 `postTask` 가 없다).
- ★ **Safari 는 미실행** — Baseline 조회로 **두 API 모두 Safari 미구현**이다(머리말). 그래서 실제 코드는 **없을 때의 대체**를 같이 둔다(「언제 쓰고」).

### (2) ★★★ 본체 — 긴 작업 중의 클릭

```html
<!-- wa36b-39-block.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>39 block</title>
<style> body { margin: 0; } #btn { position: absolute; left: 50px; top: 50px; width: 200px; height: 60px; } </style>
<button id="btn">누름</button>
<script>
// 긴 작업 중의 클릭 — 작업을 시작하자마자 하네스에게 클릭을 부탁한다(CDP Input.dispatchMouseEvent · 응답을 안 기다린다)
// 작업은 200ms 어치 — 가 한 덩어리 · 나 50ms 네 조각 사이에 await scheduler.yield() · 다 네 조각 사이에 await setTimeout 0
// 한 판의 칸 = 클릭이 작업 중에 일어났나(event.timeStamp) · 핸들러가 불린 때 끝난 조각 수 · 핸들러가 작업 끝 뒤였나
const 바쁨 = ms => { const t = performance.now(); while (performance.now() - t < ms) {} };
const 쉬기 = { "한 덩어리": null, "scheduler.yield": () => scheduler.yield(), "setTimeout 0": () => new Promise(r => setTimeout(r, 0)) };
let 받음 = null;
document.getElementById("btn").addEventListener("click", e => { 받음 = { 때: performance.now(), 일어남: e.timeStamp, 조각: 끝낸조각 }; });
let 끝낸조각 = 0;
const 한판 = async 방식 => {
  받음 = null; 끝낸조각 = 0;
  const r = document.getElementById("btn").getBoundingClientRect();
  __부탁("누르기", { x: r.x + r.width / 2, y: r.y + r.height / 2 });
  const 시작 = performance.now();
  let 기다리는입력 = false;
  if (!쉬기[방식]) { const t = performance.now(); while (performance.now() - t < 200) { if (navigator.scheduling.isInputPending()) 기다리는입력 = true; } 끝낸조각 = 4; }
  else for (let k = 0; k < 4; k++) { 바쁨(50); 끝낸조각++; if (k < 3) await 쉬기[방식](); }
  const 끝 = performance.now();
  await new Promise(res => { const 봄 = () => 받음 ? res() : setTimeout(봄, 10); 봄(); });
  return { 중: 받음.일어남 > 시작 && 받음.일어남 < 끝, 조각: 받음.조각, 뒤: 받음.때 > 끝, 기다리는입력 };
};
window.__끝 = async () => {
  const 줄 = [["방식", "클릭이 작업 중에 일어났나", "핸들러가 불린 때 끝난 조각(/4)", "핸들러가 작업 끝 뒤였나"].join("\t")];
  let 대기참 = 0;
  for (const 방식 of Object.keys(쉬기)) {
    const 판 = [];
    for (let k = 0; k < 5; k++) { await new Promise(r => setTimeout(r, 50)); 판.push(await 한판(방식)); }
    if (방식 === "한 덩어리") 대기참 = 판.filter(p => p.기다리는입력).length;
    const 셈 = f => `${판.filter(f).length} / 5 판`;
    const 조각들 = [...new Set(판.map(p => p.조각))].sort().join("·");
    줄.push([방식, "참 " + 셈(p => p.중), `${조각들}`, "참 " + 셈(p => p.뒤)].join("\t"));
  }
  줄.push(`한 덩어리 작업 안에서 navigator.scheduling.isInputPending() 이 한 번이라도 true 였나 — 참 ${대기참} / 5 판`);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-39-block.html
방식	클릭이 작업 중에 일어났나	핸들러가 불린 때 끝난 조각(/4)	핸들러가 작업 끝 뒤였나
한 덩어리	참 5 / 5 판	4	참 5 / 5 판
scheduler.yield	참 5 / 5 판	1	참 0 / 5 판
setTimeout 0	참 5 / 5 판	1	참 0 / 5 판
한 덩어리 작업 안에서 navigator.scheduling.isInputPending() 이 한 번이라도 true 였나 — 참 5 / 5 판
(exit 0)
```

- ★★★ **한 덩어리 — 핸들러가 작업 끝 뒤였나 참 5 / 5 판.** 클릭은 **작업 중에 일어났는데**(`event.timeStamp` 가 작업 시작과 끝 사이 — 참 5 / 5) 핸들러는 **200ms 가 다 끝난 뒤**에 불렸다. 태스크는 **도중에 안 끊긴다.**
- ★★★ **`yield` · `setTimeout 0` 네 조각 — 둘 다 「끝난 조각 1」 · 작업 끝 뒤였나 참 0 / 5 판.** 첫 조각이 끝나고 양보한 **그 사이에** 핸들러가 불렸다. **입력을 받는다는 점에서는 두 방식이 같았다.**
- ★★ **`isInputPending()` 은 한 덩어리 작업 안에서 참이 됐다(5 / 5)** — 「기다리는 입력이 있다」를 **작업 도중에 알 수 있었다.** 그래도 **알기만 할 뿐** 핸들러는 작업이 끝나야 돈다 — 쓰려면 참일 때 **스스로 양보**해야 한다.
- ★ **이것은 「몇 ms 빨라졌나」가 아니다** — 핸들러가 **어느 자리에 끼었나**다(머리말 제5의 상태).

### (3) ★★★ 양보 뒤 누가 먼저인가 — 이어가기 순서

먼저 **다른 작업 셋(A · B · C)** 을 `setTimeout 0` 으로 줄 세우고, 세 조각짜리 일(1 · 2 · 3)을 조각 사이에 양보하며 돌린다.

```html
<!-- wa36b-39-order.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>39 order</title>
<script>
// 이어가기의 순서 — 먼저 다른 작업 셋(A·B·C)을 setTimeout 0 으로 줄 세우고, 세 조각짜리 일(1·2·3)을 조각 사이에 양보하며 돌린다
// 판 가 yield 로 양보 · 판 나 setTimeout 0 으로 양보 · 판 다 postTask 우선순위 셋을 낮은 것부터 등록 · 라 abort · 마 setPriority
const 줄세움 = 로그 => { for (const x of "ABC") setTimeout(() => 로그.push(x), 0); };
const 다됨 = () => new Promise(r => setTimeout(() => setTimeout(r, 20), 20));
window.__끝 = async () => {
  const 줄 = [];
  { const 로그 = []; 줄세움(로그);
    (async () => { 로그.push("1"); await scheduler.yield(); 로그.push("2"); await scheduler.yield(); 로그.push("3"); })();
    await 다됨(); 줄.push(`가 조각 사이 await scheduler.yield()\t${로그.join(" ")}`); }
  { const 로그 = []; 줄세움(로그);
    (async () => { 로그.push("1"); await new Promise(r => setTimeout(r, 0)); 로그.push("2"); await new Promise(r => setTimeout(r, 0)); 로그.push("3"); })();
    await 다됨(); 줄.push(`나 조각 사이 await setTimeout 0\t${로그.join(" ")}`); }
  { const 로그 = [];
    setTimeout(() => 로그.push("setTimeout"), 0);
    for (const p of ["background", "user-visible", "user-blocking"]) scheduler.postTask(() => 로그.push(p), { priority: p });
    await 다됨(); 줄.push(`다 postTask 를 background → user-visible → user-blocking 순으로 등록 (setTimeout 0 을 먼저)\t${로그.join(" → ")}`); }
  { const 로그 = [], tc = new TaskController();
    const p = scheduler.postTask(() => 로그.push("돌았다"), { signal: tc.signal });
    tc.abort();
    const 결과 = await p.then(() => "이행", e => `거부 ${e.name}: ${e.message}`);
    줄.push(`라 postTask 직후 TaskController.abort()\t콜백 ${로그.length ? "돌았다" : "안 돌았다"} · 약속 ${결과}`); }
  { const 로그 = [], tc = new TaskController({ priority: "background" });
    scheduler.postTask(() => 로그.push("tc 의 일"), { signal: tc.signal });
    scheduler.postTask(() => 로그.push("user-visible 일"), { priority: "user-visible" });
    tc.setPriority("user-blocking");
    await 다됨(); 줄.push(`마 background 로 건 일을 곧바로 setPriority("user-blocking")\t${로그.join(" → ")}`); }
  { const 로그 = [];
    scheduler.postTask(async () => { 로그.push("X1"); await scheduler.yield(); 로그.push("X2"); }, { priority: "background" });
    scheduler.postTask(() => 로그.push("Y"), { priority: "background" });
    await 다됨(); 줄.push(`바 background 일 X(안에서 yield) 와 뒤이어 등록한 background 일 Y\t${로그.join(" → ")}`); }
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-39-order.html
가 조각 사이 await scheduler.yield()	1 2 3 A B C
나 조각 사이 await setTimeout 0	1 A B C 2 3
다 postTask 를 background → user-visible → user-blocking 순으로 등록 (setTimeout 0 을 먼저)	user-blocking → setTimeout → user-visible → background
라 postTask 직후 TaskController.abort()	콜백 안 돌았다 · 약속 거부 AbortError: signal is aborted without reason
마 background 로 건 일을 곧바로 setPriority("user-blocking")	tc 의 일 → user-visible 일
바 background 일 X(안에서 yield) 와 뒤이어 등록한 background 일 Y	X1 → X2 → Y
(exit 0)
```

- ★★★ **가 `yield` — `1 2 3 A B C`.** 양보했는데 **A · B · C 가 끼지 않았다** — 이어가기가 **먼저 줄 선 타이머들보다 앞**에 섰다.
- ★★★ **나 `setTimeout 0` — `1 A B C 2 3`.** 양보 뒤의 조각이 **줄 맨 뒤**로 가서 A · B · C 가 다 돈 뒤에 이어졌다.
- ★★ **(2)와 함께 읽으면** — 두 방식 다 **입력은 끼워 줬지만**, `yield` 는 **다른 태스크(남의 타이머 · 뒤이은 일)에게는 자리를 안 내줬다.** 명세의 이어가기 설계 그대로다 — 「**Continuations have a higher effective priority than tasks with the same TaskPriority.**」
- ★★ **다 우선순위 셋 — `user-blocking → setTimeout → user-visible → background`.** 등록 순서(낮은 것부터)와 **정반대**로 돌았고, `setTimeout` 은 **`user-blocking` 과 `user-visible` 사이**에 끼었다. ★ **이 끼는 자리는 명세가 정하지 않는다** — 스케줄러 태스크와 다른 태스크 사이의 선택은 「**implementation-defined**」이고, 명세는 전략의 예로 「유효 우선순위 3 이상은 대부분의 태스크보다 높게 · 2(`user-visible` 태스크)는 타이머처럼 · 0 · 1 은 다른 것이 없을 때」를 든다. **Chrome 151 은 그 예대로 돌았다 — 재량 안의 선택**이다.
- ★★ **라 `abort()` — 콜백 안 돌았다 · 약속 거부 `AbortError: signal is aborted without reason`.** **마 `setPriority("user-blocking")` — 뒤에 등록한 `user-visible` 일보다 먼저**(`tc 의 일 → user-visible 일`). **바 같은 `background` 끼리 — `X1 → X2 → Y`**: X 의 이어가기(유효 우선순위 1)가 **뒤이어 등록한 같은 우선순위의 새 일 Y**(0)보다 앞섰다.

```text
   유효 우선순위 (명세의 표 — 숫자가 클수록 먼저)

   background 태스크 0 · 이어가기 1  <  user-visible 태스크 2 · 이어가기 3  <  user-blocking 태스크 4 · 이어가기 5
   ★ 이 판: 가의 yield(이어가기 3) 가 타이머 A·B·C 보다 먼저 · 다의 setTimeout 은 4 와 2 사이
```

### (4) ★★ `requestIdleCallback` — 50ms 상한과 마감을 당기는 것들

```html
<!-- wa36b-39-idle.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>39 idle</title>
<script>
// requestIdleCallback — 콜백이 받은 deadline.timeRemaining() 을 범주로(ms 는 찍지 않는다)
// 가 아무 일도 없는 페이지 · 나 rAF 고리가 도는 페이지 · 다 30ms 뒤 타이머가 걸려 있는 페이지
// 라 500ms 동기 작업 한 덩어리 앞에 건 rIC 둘(timeout 100 · timeout 없음) · 마 rAF 콜백마다 20ms 씩 바쁜 500ms 동안 건 rIC 둘(열 판)
const 한번 = 옵션 => new Promise(r => requestIdleCallback(d => r({ 남음: d.timeRemaining(), 늦음: d.didTimeout, 때: performance.now() }), 옵션));
const 범주 = x => x > 50 ? "50 초과" : x > 1000 / 60 ? "16.7 초과 · 50 이하" : x > 10 ? "10 초과 · 16.7 이하" : "10 이하";
const 쉼 = ms => new Promise(r => setTimeout(r, ms));
window.__끝 = async () => {
  const 줄 = [];
  await 쉼(300);
  { const 값 = []; for (let k = 0; k < 20; k++) 값.push((await 한번()).남음);
    줄.push(`가 한가한 페이지 · 20번\t범주 = ${[...new Set(값.map(범주))].sort().join(" / ")} · 가장 큰 값이 50 이하인가 = ${Math.max(...값) <= 50}`); }
  { let 켬 = true; const 돌기 = () => { if (켬) requestAnimationFrame(돌기); }; requestAnimationFrame(돌기);
    const 값 = []; for (let k = 0; k < 20; k++) 값.push((await 한번()).남음); 켬 = false;
    줄.push(`나 rAF 고리가 도는 페이지 · 20번\t가장 큰 값이 16.7 이하인가 = ${Math.max(...값) <= 1000 / 60}`); }
  { await 쉼(100); let 먼저 = 0, 맞음 = 0;
    for (let k = 0; k < 20; k++) {
      let 울림 = false; const 때 = performance.now() + 30; setTimeout(() => { 울림 = true; }, 30);
      const r = await 한번(); if (!울림) { 먼저++; if (r.남음 <= 때 - r.때 + 1) 맞음++; } await 쉼(40); }
    줄.push(`다 30ms 타이머가 걸린 페이지 · 20번\t타이머보다 먼저 불린 번 중 timeRemaining 이 타이머까지 남은 시간(+1ms) 이하 = ${맞음} / ${먼저}`); }
  { await 쉼(100); const 순서 = []; const 둘 = [한번({ timeout: 100 }).then(r => (순서.push("timeout 100"), r)), 한번().then(r => (순서.push("timeout 없음"), r))];
    const t = performance.now(); while (performance.now() - t < 500) {} const 끝 = performance.now();
    const [빠른, 느린] = await Promise.all(둘);
    줄.push(`라 500ms 동기 작업 앞에 건 rIC 둘\t불린 순서 = ${순서.join(" → ")} · didTimeout = ${빠른.늦음} / ${느린.늦음} · 둘 다 작업 끝 뒤 = ${빠른.때 > 끝 && 느린.때 > 끝}`); }
  { let 뒤 = 0, 늦음 = 0;
    for (let k = 0; k < 10; k++) {
      await 쉼(100); const 시작 = performance.now(); let 끝 = Infinity;
      const f = () => { const t = performance.now(); while (performance.now() - t < 20) {} if (performance.now() - 시작 < 500) requestAnimationFrame(f); else 끝 = performance.now(); };
      requestAnimationFrame(f);
      const [a, b] = await Promise.all([한번(), 한번({ timeout: 100 })]);
      if (a.때 > 끝) 뒤++; if (b.늦음) 늦음++; await 쉼(600); }
    줄.push(`마 rAF 마다 20ms 바쁜 500ms · 열 판\ttimeout 없는 rIC 가 바쁨이 끝난 뒤에야 불린 판 = ${뒤} / 10 · timeout 100 인 rIC 가 didTimeout=true 인 판 = ${늦음} / 10`); }
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa36b-net.py page wa36b-39-idle.html
가 한가한 페이지 · 20번	범주 = 16.7 초과 · 50 이하 · 가장 큰 값이 50 이하인가 = true
나 rAF 고리가 도는 페이지 · 20번	가장 큰 값이 16.7 이하인가 = true
다 30ms 타이머가 걸린 페이지 · 20번	타이머보다 먼저 불린 번 중 timeRemaining 이 타이머까지 남은 시간(+1ms) 이하 = 20 / 20
라 500ms 동기 작업 앞에 건 rIC 둘	불린 순서 = timeout 100 → timeout 없음 · didTimeout = true / false · 둘 다 작업 끝 뒤 = true
마 rAF 마다 20ms 바쁜 500ms · 열 판	timeout 없는 rIC 가 바쁨이 끝난 뒤에야 불린 판 = 4 / 10 · timeout 100 인 rIC 가 didTimeout=true 인 판 = 5 / 10
(exit 0)
```

- ★★★ **가 한가한 페이지 — 20번 모두 「16.7 초과 · 50 이하」 · 가장 큰 값이 50 이하 `true`.** HTML 의 글자 그대로다 — 마감은 「**유휴 시작 + 50**」이 상한이다. 한가하면 **그 상한 가까이** 받는다.
- ★★ **나 rAF 고리가 도는 페이지 — 전부 16.7 이하.** 명세의 「**hasPendingRenders**」 — 렌더링이 기다리고 있으면 마감이 **다음 렌더링 시각**으로 당겨진다([38번 주제](../38-request-animation-frame/2-summary.md)의 틀 박자와 같은 60Hz 예).
- ★★ **다 30ms 타이머가 걸린 페이지 — 타이머보다 먼저 불린 20번 모두, `timeRemaining` 이 타이머까지 남은 시간(+1ms) 이하.** 명세의 「**timerCallbackEstimates** … deadline 을 그 타이머로」 — 활성 타이머도 마감을 당긴다.
- ★★ **라 500ms 동기 작업 앞에 건 둘 — `timeout 100 → timeout 없음` 순 · `didTimeout = true / false`.** 작업 중에 100ms 가 지나 **timeout 쪽이 먼저 태스크로 줄에 섰고**(「invoke idle callback timeout」 — `didTimeout` 을 참으로), 없는 쪽은 그 뒤 **한가해진 뒤**에 왔다.

### (5) ★★ 바쁜 페이지에서도 유휴 콜백은 끼어든다 — 판마다

**rAF 콜백마다 20ms 씩 바쁜 500ms** 동안 `requestIdleCallback` 둘(`timeout` 없음 · `timeout 100`)을 건다. 열 판.

```text
$ python3 wa36b-net.py page wa36b-39-idle.html | sed -n '5p'
마 rAF 마다 20ms 바쁜 500ms · 열 판	timeout 없는 rIC 가 바쁨이 끝난 뒤에야 불린 판 = 4 / 10 · timeout 100 인 rIC 가 didTimeout=true 인 판 = 5 / 10
(exit 0)
```

- ★★ **timeout 없는 쪽이 바쁨이 끝난 뒤에야 불린 판은 열 판 중 일부뿐**이다 — 나머지 판에서는 **바쁜 동안에도** 불렸다. **timeout 100 쪽도 `didTimeout=true` 인 판이 열 판 중 일부**다. 수는 **캡처마다 움직였다**(앞의 수 4 · 5 · 4 / 10 — 머리말).
- ★★ **「바쁜 페이지에서는 유휴 콜백이 안 불리다가 timeout 에만 불린다」는 이 판에서 성립하지 않았다** — 틀과 틀 사이에 **짧은 유휴**가 생기면 거기서 불린다. 명세도 유휴 기간을 「**user agent defined**」로 둔다.
- ★ 그래서 `timeout` 은 「**바쁘면 이때 불린다**」가 아니라 「**늦어도 이때까지는**」이다. 어느 쪽으로 불렸는지는 **`didTimeout`** 으로 가른다.

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   const id = requestIdleCallback(deadline => {
     while (deadline.timeRemaining() > 0 && 할일이있다) 한조각();      ← 50 이하 · 타이머 · 렌더링이 당긴다
     if (할일이있다) requestIdleCallback(같은함수);                   ← 남으면 다음 유휴에
   }, { timeout: 2000 });                                              ← 늦어도 이때까지 — deadline.didTimeout
   cancelIdleCallback(id)

   await scheduler.yield();                                            ← 이어가기 — 원래 일의 우선순위를 물려받는다
   scheduler.postTask(콜백, { priority: "user-blocking" | "user-visible" | "background", delay, signal })  → Promise
   const tc = new TaskController({ priority }); tc.abort(); tc.setPriority(p);   tc.signal 을 postTask 에
   navigator.scheduling.isInputPending()                               ← 이 판에는 있다 · 알려 줄 뿐 양보는 아니다
```

### 어디서 헷갈리나

- **`setTimeout 0` 과 `yield` 는 입력에는 같고 남의 태스크에는 다르다**((2)·(3)).
- **`postTask` 의 기본 우선순위는 `user-visible`** 이다 — 명세 기본값. 이 판에서 그 태스크는 **타이머와 같은 줄처럼** 돌았다((3) 다).
- **`timeRemaining()` 은 50 을 넘지 않는다** — 그리고 **더 짧을 수 있다**((4)).
- **`timeout` 은 보장된 호출 시각이 아니라 상한**이다((5)).

## 어디서 틀리나

### 1. 긴 작업을 `async` 함수로 감싸면 입력이 막히지 않는다고 믿는다

**`await` 가 없으면 한 덩어리다**((2) — 작업 끝 뒤 5 / 5). 쪼개는 것은 **태스크로 양보**하는 `await` 다. 마이크로태스크(`await Promise.resolve()`)로는 양보가 아니다(JS 36편).

### 2. `setTimeout 0` 으로 쪼개면 내 일이 곧 이어진다고 믿는다

**줄 맨 뒤로 간다**((3) 나 — `1 A B C 2 3`). 남의 타이머가 많으면 그만큼 늦는다.

### 3. `yield` 로 쪼개면 모든 태스크에게 양보한다고 믿는다

**입력은 끼웠지만 먼저 줄 선 타이머는 앞지르지 못했다**((3) 가). 「남의 일에게도 자리를 내줘야 하는」 백그라운드 일은 **`postTask({ priority: "background" })`** 로 건다.

### 4. `postTask` 우선순위를 「`setTimeout` 보다 무조건 먼저」로 외운다

**`user-blocking` 만 앞섰다**((3) 다). 다른 태스크와의 자리는 **구현이 고른다.**

### 5. `requestIdleCallback` 안에서 오래 일한다

**마감은 50 이하**다((4)). `timeRemaining()` 을 보며 조각을 끊고, 남으면 다시 건다.

### 6. `timeout` 을 「바쁘면 이때 불린다」로 쓴다

**바빠도 먼저 불린 판이 있었다**((5)). `didTimeout` 을 보고 가른다.

### 7. node 에서 같은 코드를 돌린다

**`requestIdleCallback` · 전역 `scheduler` 가 없다**((1)). node 의 `timers/promises` 의 `scheduler` 는 **다른 API** 다.

### 8. 「yield 로 쪼갰으니 INP 가 좋아졌다」

**재지 않았다**((2) — 끼어들었다는 사실뿐). 실제 지표는 필드 측정의 몫이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 태스크는 도중에 안 끊긴다 — 핸들러는 작업 끝 뒤 | ★ **명세**(이벤트 루프 — 태스크 하나를 끝까지) + 이 판의 관찰(5 / 5) |
| 조각 사이 양보에 핸들러가 끼었다 | ★ **이 판의 관찰** — 입력을 다음에 고르는 것은 구현의 선택(HTML 은 태스크 큐 선택을 구현에 맡긴다) |
| `yield` 이어가기가 같은 우선순위의 새 일보다 앞 | ★ **명세**(유효 우선순위 표) |
| `yield` 이어가기가 타이머보다 앞 · `setTimeout` 이 `user-blocking` 과 `user-visible` 사이 | ★ **재량 안의 선택**(명세는 「implementation-defined」 + 전략의 예) |
| `timeRemaining()` ≤ 50 · 타이머 · 렌더링이 마감을 당김 | ★ **명세**(HTML 유휴 단계의 computeDeadline) |
| `timeout` 이 지나면 태스크로 · `didTimeout = true` | ★ **명세**(invoke idle callback timeout) |
| 바쁜 동안에도 유휴 콜백이 판마다 끼었다 | ★ **이 판의 관찰 — 흔들린다**(유휴 기간은 「user agent defined」) |
| `isInputPending` 이 있다 | ★ **이 판의 관찰**(지원 판별) |
| INP · 지연 ms | ★ **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 클릭 뒤 긴 계산(내 일을 빨리 끝내고 싶다) | 조각 + `await scheduler.yield()`(없으면 `setTimeout 0` 대체) | 한 덩어리 · 마이크로태스크로 쪼개기 |
| 급하지 않은 뒷일(분석 전송 · 미리 계산) | `requestIdleCallback`(+ `timeout`) 또는 `postTask({ priority: "background" })` | rAF(틀 예산을 먹는다) |
| 사용자에게 곧 보일 갱신 | `postTask({ priority: "user-blocking" })` · 렌더링 직전이면 rAF(38편) | `background` |
| 취소될 수 있는 예약 | `TaskController` + `signal` · `cancelIdleCallback` | 플래그를 들고 콜백 안에서 무시 |
| Safari 까지 | 기능 판별 후 `setTimeout` · `MessageChannel` 대체 | 판별 없이 `scheduler.yield()` |
| 서버의 주기 작업 · 밀린 실행 처리 | [`ops-patterns/10-scheduler`](../../../ops-patterns/10-scheduler/) 의 방아쇠 | 브라우저 API 로 흉내 |

## 핵심 문장

1. **긴 동기 작업은 입력을 작업 끝까지 막는다** — 클릭은 작업 중에 일어났는데 핸들러는 끝 뒤였다(5 / 5).
2. **태스크로 양보하면 입력이 그 사이에 낀다** — `yield` 도 `setTimeout 0` 도 첫 조각 뒤.
3. **둘이 갈리는 곳은 「양보 뒤 누가 먼저」다** — `yield` 는 이어가기라 먼저 줄 선 타이머보다도 앞(`1 2 3 A B C`), `setTimeout 0` 은 줄 맨 뒤(`1 A B C 2 3`).
4. **`requestIdleCallback` 의 마감은 50ms 가 상한이고, 타이머와 다음 렌더링이 더 당긴다.** `timeout` 은 상한이지 약속된 시각이 아니다.
5. **지원은 한쪽뿐이다** — Chrome 151 에는 다 있고 node 에는 없고 Safari 는 둘 다 미구현이다. 대체를 같이 둔다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 39번 · Baseline 표의 limited 행)
- [38번 주제](../38-request-animation-frame/2-summary.md) — 렌더링 단계와 틀 박자. 유휴 마감이 렌더링에 당겨지는 이유
- [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/2-summary.md) — 마이크로태스크로 쪼개면 양보가 아니라는 것(타이머 0 번)의 정본
- [`ops-patterns/10-scheduler`](../../../ops-patterns/10-scheduler/) — 서버 스케줄러의 정본. 그쪽은 벽시계 방아쇠와 밀린 실행, 여기는 한 스레드 안의 양보 순서
- [`process-thread`](../../process-thread/) — 스레드 · 프로세스 일반
- [24번 주제](../24-document-lifecycle-events/2-summary.md) — 숨은 탭(유휴 기간 조절은 이 편이 던지지 않았다)

## 용어 풀이

- **긴 작업(long task)** — 메인 스레드를 오래 붙드는 태스크 하나. 그동안 입력 핸들러가 못 돈다.
- **양보(yield)** — 작업을 쪼개 조각 사이에 이벤트 루프로 돌아가는 것. 태스크로 돌아가야 양보다.
- **이어가기(continuation)** — `await scheduler.yield()` 뒤의 나머지. 원래 일의 우선순위를 물려받고 **한 칸 높게** 선다.
- **유효 우선순위** — 우선순위 셋 × 이어가기 여부 = 0\~5 의 숫자. 큰 쪽이 먼저.
- **유휴 기간** — 이벤트 루프가 할 태스크가 없을 때. 마감은 50ms 가 상한이고 타이머 · 렌더링이 당긴다.
- **`didTimeout`** — 유휴가 아니라 `timeout` 이 지나서 불렸는가.
- **입력 막힘 판** — 200ms 를 세 방식으로 돌리며 클릭 핸들러가 불린 자리를 센 표. 이 편의 본체.

## 더 들어가면

- **INP · Long Animation Frames** — 실제 응답성 지표. 성능 측정 갈래의 몫.
- **`postTask` 의 `delay` · `TaskSignal` 의 `prioritychange` 이벤트** — 던지지 않았다.
- **숨은 탭의 유휴 기간 조절** — 명세가 허용한다(「10초에 한 번」 예). 던지지 않았다.
- **`isInputPending` 으로 스스로 양보하기** — 참일 때만 양보하는 형태. 판별까지만 했다.
