# web-platform/03-event-loop — 이벤트 루프: 태스크·마이크로태스크·렌더링 기회·rAF — 정리 (힌트)

## 해결하는 문제

렌더러의 메인 스레드는 하나다([01](../01-browser-architecture/2-summary.md)). 그 한 스레드가 스크립트 실행, 클릭 처리, 타이머, 네트워크 응답, 화면 그리기를 모두 맡는다.

```text
  메인 스레드 하나에 몰려드는 일
   클릭 ─┐  setTimeout ─┐  fetch 응답 ─┐  Promise.then ─┐  "다음 프레임 그려야 함" ─┐
         ▼              ▼              ▼               ▼                         ▼
                      [ 무엇을, 어떤 순서로, 언제 끊고 그리나? ]
```

- 규칙이 없으면 두 가지가 깨진다.
  - 순서: `then` 콜백이 클릭 핸들러 중간에 끼어들면 상태가 반쯤 바뀐 채로 보인다.
  - 응답성: 한 일이 끝날 때까지 다른 일(입력·그리기)이 기다린다. 스레드가 하나라 선점이 없다.
- HTML 표준의 **이벤트 루프**가 이 규칙이다. "한 번에 태스크 하나를 끝까지 → 마이크로태스크를 비움 → 때가 되면 렌더링".
  - *태스크(task)*: 이벤트 루프가 한 번에 하나씩 꺼내 끝까지 실행하는 일 단위. 예) 클릭 이벤트 디스패치, `setTimeout` 콜백, HTML 파싱 한 조각.
  - *마이크로태스크(microtask)*: 현재 태스크(또는 콜백)가 끝나자마자 실행되는 작은 일. 예) `Promise.then`, `queueMicrotask`, `MutationObserver` 콜백.

쉬운 예: 은행 창구 직원 한 명이다.
- 번호표 손님(태스크)을 한 명씩 끝까지 처리한다.
- 손님을 보내기 직전, 그 손님 건으로 생긴 후속 서류(마이크로태스크)는 다 처리한다. 후속 서류가 또 서류를 만들면 그것도 다 처리한다.
- 정해진 시각마다 게시판(화면)을 갱신한다. 그런데 직원이 한 손님에게 붙잡혀 있으면 게시판도 번호표도 멈춘다.

똑같은 구조다.\
그래서 **긴 태스크는 입력 지연**, **끝없는 마이크로태스크는 화면 정지**가 된다.

실무 예:
- 300ms짜리 동기 작업 도중 누른 클릭은 핸들러가 약 250ms 늦게 시작했다(아래 실험). INP의 "입력 지연"이 이것이다.
- `Promise.then`으로 500ms 동안 스스로를 다시 거는 코드는 그동안 rAF를 0번 돌게 했다. 같은 일을 `setTimeout`으로 이으면 31~32번 돌았다(아래 실험).

## 동작·원리

### 1. 한 바퀴 — 처리 모델

```text
        ┌────────────────────────────────────────────────────────────────┐
        │  ① 태스크 큐들 중 하나를 고름(구현 정의) → 가장 오래된 실행 가능 태스크 1개 실행 │
        │  ② 마이크로태스크 체크포인트: 마이크로태스크 큐가 빌 때까지 실행            │
        │     (실행 중 새로 들어온 마이크로태스크도 이번에 실행)                    │
        │  ③ 긴 태스크 보고(Long Tasks), 할 일이 없으면 유휴 기간(rIC)            │
        └───────────────────────────┬────────────────────────────────────┘
                                    │ 다시 ①
  병렬로: 렌더링 기회가 오면 ──▶ "update the rendering" 태스크를 렌더링 태스크 소스에 넣음
        │
        └▶ 그 태스크가 ①에서 뽑히면:
           resize → scroll → 미디어 쿼리 → 애니메이션 갱신 → 전체화면
           → **rAF 콜백** → 스타일·레이아웃(ResizeObserver 루프) → … → 페인트 갱신
```

- HTML 표준 8.1.7.3 Processing model(2026-10 판 확인)
  - "실행 가능한 태스크가 있는 태스크 큐 하나를 **구현 정의 방식으로** 고른다." 그 큐의 첫 실행 가능 태스크를 꺼내 실행한다.
  - 태스크가 끝나면 "Perform a microtask checkpoint".
  - 창(window) 이벤트 루프는 병렬로 렌더링 기회를 기다렸다가 "update the rendering"을 **렌더링 태스크 소스의 태스크로** 넣는다. 렌더링 업데이트도 큐에 들어가는 태스크 중 하나라는 뜻이다.
- 표준 문장 두 개를 기억해 둔다.
  - "Task queues are sets, not queues" — 큐에서 첫 원소를 빼는 게 아니라 "첫 실행 가능 태스크"를 고르기 때문이다.
  - "The microtask queue is not a task queue" — 마이크로태스크 큐는 ①에서 선택되지 않는다. 체크포인트로만 비워진다.
  - *태스크 소스*: 태스크의 출처 분류(타이머, DOM 조작, 사용자 상호작용, 네트워킹, 렌더링 등). 같은 소스의 태스크는 같은 큐에 들어가 서로 순서가 유지된다. 다른 큐 사이의 우선순위는 브라우저가 정한다.

### 2. 마이크로태스크 체크포인트 — "비울 때까지"

```text
  perform a microtask checkpoint:
    while (마이크로태스크 큐가 비어 있지 않음) {
       가장 오래된 마이크로태스크를 꺼내 실행   ← 실행 중 queueMicrotask 하면 큐 뒤에 붙고, 이 while이 또 꺼냄
    }
    거부된 Promise 알림, IndexedDB 트랜잭션 정리, ClearKeptObjects()
```

- 표준 그대로다("While the event loop's microtask queue is not empty"). 재진입 방지 플래그가 있어 체크포인트 안에서 체크포인트가 중첩되지 않는다.
- 체크포인트는 태스크 끝에만 있는 것이 아니다. 스크립트 콜백이 끝나 JS 실행 스택이 비면("clean up after running script") 그때도 돈다. 그래서 rAF 콜백 하나가 끝나면 그 콜백이 만든 `then`이 다음 rAF 콜백보다 먼저 실행된다.
- ECMAScript는 Promise 반응을 "Job"으로 정의하고 호스트(HTML)가 `HostEnqueuePromiseJob`으로 마이크로태스크 큐에 넣는다. → [js/36 이벤트 루프와 마이크로태스크](../../../languages/js/syntax/36-event-loop-and-microtasks/2-summary.md)
- 결과: **마이크로태스크가 스스로를 계속 다시 걸면 ②가 끝나지 않는다.** ①의 다음 태스크도, 렌더링 태스크도 오지 않는다.

### 3. 렌더링 기회와 rAF

```text
  60Hz 화면 (예시)
  |◀──── 16.7ms ────▶|◀──── 16.7ms ────▶|
  ▲ 렌더링 기회        ▲                  ▲
  │ [task][task][micro]│[rAF→style→layout→paint]
  └ 태스크 사이사이에 렌더링 태스크가 끼어든다. 태스크가 길면 기회를 놓친다.
```

- 표준: 렌더링 기회는 "하드웨어 주사율 제약과 성능을 위한 UA의 조절"로 정해진다. 60Hz면 약 16.67ms 간격이라는 예를 든다(idle deadline 계산 주석).
- 렌더링 업데이트 단계에서 문서를 걸러 낸다. 숨겨진 문서(`visibilityState === "hidden"`), 렌더 차단 중인 문서, 렌더링 기회가 없는 문서는 이번 업데이트에서 빠진다. 바뀐 게 없고 rAF 콜백도 없으면 "불필요한 렌더링"으로 건너뛴다.
- **rAF 콜백은 스타일·레이아웃 직전에** 돈다. 그래서 rAF 안의 쓰기는 이번 프레임에 반영되고, 따로 강제 레이아웃을 부르지 않으면 이 단계의 스타일·레이아웃 계산에 모인다. 다만 표준의 이 단계는 `ResizeObserver` 알림이 있으면 스타일·레이아웃을 다시 돌리므로, 한 프레임의 레이아웃이 꼭 한 번이라는 보장은 없다. → [web-api/38 rAF](../../../languages/web-api/38-request-animation-frame/2-summary.md)
- 타이머 최소 지연: `setTimeout`이 5단계 넘게 중첩되면 지연이 4ms 미만일 때 4ms로 올린다("If nestingLevel is greater than 5, and timeout is less than 4, then set timeout to 4" — HTML 표준 Timers).
- 유휴 기간: 할 일이 없으면 `requestIdleCallback`의 마감을 계산한다. 상한은 50ms다 — "50ms 상한은 새 입력에 사람이 지각하는 범위 안에서 응답하기 위해서"(표준 주석). → [web-api/39 유휴 스케줄링](../../../languages/web-api/39-idle-scheduling/2-summary.md)

### 실험: 실행 순서

환경: headless Chrome 151.0.7922.173, Playwright `playwright-core`, Node 20, 127.0.0.1 로컬 페이지, 스로틀 없음. 10회(새 탭).

```js
setTimeout(() => { L('timeout-1'); Promise.resolve().then(() => L('timeout-1 안의 micro')); }, 0);
setTimeout(() => L('timeout-2'), 0);
const mc = new MessageChannel(); mc.port1.onmessage = () => L('message'); mc.port2.postMessage(0);
requestAnimationFrame(() => { L('rAF'); Promise.resolve().then(() => L('rAF 안의 micro')); });
Promise.resolve().then(() => { L('micro-1'); queueMicrotask(() => L('micro-1이 넣은 micro')); });
queueMicrotask(() => L('micro-2'));
L('sync-끝');
```

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04)

```text
10/10회: sync-끝 → micro-1 → micro-2 → micro-1이 넣은 micro → timeout-1 → timeout-1 안의 micro → timeout-2 → message → rAF → rAF 안의 micro
```

- 표준이 정하는 부분
  - 동기 코드 → 마이크로태스크 전부(실행 중 새로 넣은 것까지) → 다음 태스크.
  - `timeout-1 안의 micro`가 `timeout-2`보다 먼저다. 태스크 하나가 끝날 때마다 체크포인트가 돈다.
  - 같은 타이머 태스크 소스의 `timeout-1` → `timeout-2` 순서.
- 표준이 정하지 않는 부분(이 환경의 관찰)
  - 타이머와 `MessageChannel`은 다른 태스크 소스라 둘 사이 순서는 구현이 고른다. 이 환경에서는 타이머가 먼저였다.
  - rAF는 렌더링 기회에 달려 있어, 앞의 태스크들과의 상대 순서는 화면 주사율·타이밍에 따라 달라질 수 있다. 10회 모두 마지막이었을 뿐이다.

### 실험: 긴 태스크 중 클릭, 마이크로태스크 연쇄 vs 태스크 연쇄

환경: 같음. (1) `setTimeout(0)`으로 300ms 동기 루프를 시작하고 50ms 뒤 실제 마우스 클릭(Playwright `page.mouse.click` → CDP 입력). 핸들러 시작 시각 − `event.timeStamp`와 Event Timing(`PerformanceObserver`, `type: 'event'`, `durationThreshold: 16`)의 `processingStart − startTime`. (2) 500ms 동안 스스로를 다시 거는 루프를 `Promise.then`과 `setTimeout(0)`으로 각각 돌리고, 그동안 rAF 횟수와 "루프보다 먼저 걸어 둔 `setTimeout(0)`"의 실행 시각을 쟀다. 각 3회.

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 3회 범위)

```text
긴 태스크 0ms 중 클릭 run1: 핸들러 시작 - event.timeStamp = 3ms; Event Timing ["pointerup:delay=2 dur=16","click:delay=2 dur=16"]
긴 태스크 300ms 중 클릭 run1: 핸들러 시작 - event.timeStamp = 249ms; Event Timing ["pointerup:delay=248 dur=256","click:delay=249 dur=256"]
긴 태스크 300ms 중 클릭 run2: 핸들러 시작 - event.timeStamp = 250ms; Event Timing ["pointerup:delay=249 dur=256","click:delay=249 dur=256"]
마이크로태스크 연쇄 500ms run1: 그동안 rAF 0회, 먼저 걸어 둔 setTimeout(0) 실행 시각 501ms
태스크(setTimeout) 연쇄 500ms run1: 그동안 rAF 31회, 먼저 걸어 둔 setTimeout(0) 실행 시각 1ms
```

- 바쁘지 않을 때 핸들러는 3~4ms 안에 시작했다. 300ms 태스크 중 클릭은 249~250ms 늦게 시작했다(사실 점검 재실행 3회: 246~251ms) = 태스크의 남은 시간. Event Timing `duration`은 8ms 단위로 반올림된다(Event Timing 표준) — 그래서 `dur`가 16·256처럼 8의 배수다. `delay`(= `processingStart − startTime`, 248·249 등)는 이 반올림 대상이 아니다.
  - 바쁘지 않은 경우 3회 중 1회는 Event Timing 항목이 비었다. `duration`이 임계 16ms 미만이면 보고되지 않는다.
- 마이크로태스크 연쇄: 500ms 동안 rAF 0회, 먼저 걸어 둔 타이머도 501ms에야 돌았다. 체크포인트가 끝나지 않아 다음 태스크(렌더링 포함)가 오지 않았다.
- 태스크 연쇄: 같은 500ms 동안 rAF 31~32회(약 60Hz, 재실행 포함), 먼저 걸어 둔 타이머는 0~1ms에 돌았다. 태스크 사이마다 이벤트 루프가 다른 큐·렌더링을 고를 기회가 있다.

## 쓰이는 자료구조·알고리즘

- **태스크 큐 = "집합"**: 표준은 태스크 큐를 집합으로 정의하고 "첫 실행 가능 태스크"를 고른다(문서가 비활성인 태스크는 실행 불가). 큐 여러 개 사이 선택은 구현 정의 → 브라우저가 우선순위 스케줄링을 할 여지. Prioritized Task Scheduling 명세(WICG)의 `scheduler.postTask` 우선순위(`user-blocking`·`user-visible`·`background`)가 그 예다. → [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **마이크로태스크 큐 = FIFO 큐**: 꺼내 실행, 실행 중 추가는 뒤에. "빌 때까지"라 기아(starvation)가 생길 수 있다. → [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **타이머 = 키 → 만료 시각 맵**: 표준은 활성 타이머를 "map of active timers"(ordered map, 타이머 키 → 만료 시각)로 든다. 정렬 구조를 요구하지는 않고, 순서는 규칙으로 정한다 — 한 타이머는 같은 종류로 먼저 시작했고 지연이 같거나 짧은 타이머가 끝나기를 기다린다(HTML Timers, "run steps after a timeout"). 유휴 마감 계산도 이 맵의 만료 시각을 본다. 가장 이른 마감을 빨리 찾으려 구현이 우선순위 큐를 쓰는 경우가 흔하다 [?: Chromium 타이머 큐의 실제 자료구조는 미확인].
- **반응기(reactor) 패턴**: 이벤트 디멀티플렉싱 → 핸들러 디스패치 → 핸들러는 막지 않는다. 서버의 epoll 루프와 같은 모양이다. → [os/27-event-based-concurrency](../../os/27-event-based-concurrency/2-summary.md)

## 적용 — 풀어나가는 법

1. **증상을 단계로 나눈다.** 상호작용 지연 = 입력 지연(앞 태스크가 안 끝남) + 처리 시간(내 핸들러) + 표시 지연(다음 프레임까지). web.dev INP 문서의 세 단계다. INP 임계값은 75번째 백분위로 200ms 이하가 "좋음", 500ms 초과가 "나쁨"이다(web.dev INP).
2. **긴 태스크를 찾는다.** Long Tasks 명세는 정의에서 50ms를 "초과"(exceeds 50ms)하는 것을 긴 태스크로 본다. 다만 같은 명세의 처리 단계는 50ms "미만"만 버리므로 정확히 50ms도 보고될 수 있다. DevTools Performance 패널의 빨간 삼각형, 코드로는 다음과 같다.

```js
new PerformanceObserver(list => {
  for (const e of list.getEntries()) console.log('long task', e.duration.toFixed(0), 'ms');
}).observe({ type: 'longtask', buffered: true });

new PerformanceObserver(list => {
  for (const e of list.getEntries())
    console.log(e.name, '입력 지연', e.processingStart - e.startTime, '전체', e.duration);
}).observe({ type: 'event', durationThreshold: 16, buffered: true });
```

3. **긴 태스크를 쪼갠다.** 조각 사이에 이벤트 루프로 돌아간다. 마이크로태스크(`await Promise.resolve()`)로는 양보가 안 된다 — 같은 체크포인트 안에 머문다.

```ts
async function processAll<T>(items: T[], work: (x: T) => void) {
  let last = performance.now();
  for (const item of items) {
    work(item);
    if (performance.now() - last > 40) {               // 조각 상한(예시)
      await new Promise(r => setTimeout(r, 0));        // 태스크로 양보 → 입력·렌더링 기회
      // 지원 브라우저라면 await scheduler.yield()
      last = performance.now();
    }
  }
}
```

4. **시각 갱신은 rAF에서, 무거운 계산은 워커에서.** 화면에 쓰는 일은 rAF로 모으고(→ [02](../02-rendering-pipeline/2-summary.md) 읽기·쓰기 분리), 메인 스레드가 필요 없는 계산은 Web Worker로 넘긴다([16 `long-tasks-and-web-workers`](../16-long-tasks-and-web-workers/2-summary.md)).
5. **마이크로태스크 재귀를 의심한다.** 재시도·폴링을 `then` 안에서 즉시 다시 거는 코드는 끝나는 조건이 없으면 렌더링을 멈춘다. 반복 사이에는 태스크(`setTimeout`)나 rAF를 둔다.

## 장애 시나리오와 대처

### 1. 긴 태스크 → 입력 지연(INP 악화) (⚠ 커리큘럼)

- **현상**: 버튼을 눌러도 한참 뒤에 반응한다. 특히 저사양 기기.
- **보이는 형태**: RUM의 INP p75가 200ms 초과. Event Timing의 `processingStart − startTime`이 크다(실험: 249ms). Performance 패널에 50ms 초과 태스크.
- **원인**: 앞선 태스크(큰 JSON 파싱, 무거운 렌더, 동기 루프)가 끝날 때까지 클릭 태스크가 기다린다. 선점이 없다.
- **대처**: 태스크 쪼개기 + 태스크로 양보(`setTimeout`, `scheduler.yield()` — 지원 브라우저 확인), 워커로 이전, 필요한 일만 먼저 하고 나머지는 지연.

### 2. 마이크로태스크 무한 연쇄 → 렌더 영구 정지 (⚠ 커리큘럼)

- **현상**: 화면이 얼고 타이머도 안 돈다. CPU는 100%.
- **보이는 형태**: Performance 패널에 끝나지 않는 태스크 하나 안에 "Run Microtasks"가 길게. rAF 0회(실험: 500ms 동안 0회), 먼저 건 `setTimeout`도 실행되지 않음(실험: 501ms에야 실행).
- **원인**: `then` 안에서 같은 함수를 다시 거는 재귀, 상태가 안 바뀌는 `while(await check())`류 루프, `MutationObserver` 콜백이 관찰 대상 DOM을 다시 바꾸는 순환.
- **대처**: 반복 사이에 태스크 경계를 둔다(`setTimeout`·rAF). 종료 조건과 횟수 상한을 둔다.

### 3. "`await` 했으니 화면이 갱신되겠지" 오해

- **현상**: 로딩 스피너를 켜고 무거운 작업을 했는데 스피너가 안 보인다.
- **보이는 형태**: 스피너 DOM은 들어가는데 화면에 나타나지 않고, 작업이 끝난 뒤 바로 사라진다.
- **원인**: `spinner.show(); await Promise.resolve(); heavy();` — `await`의 이어짐은 마이크로태스크라 렌더링 태스크가 끼어들 틈이 없다.
- **대처**: 스피너를 보인 뒤 렌더링 기회를 넘긴다. 예) `await new Promise(r => requestAnimationFrame(() => setTimeout(r, 0)))` — rAF 뒤 다음 태스크에서 작업 시작. 근본적으로는 무거운 작업을 쪼개거나 워커로.

### 4. 백그라운드 탭에서 rAF가 멈춰 로직이 멈춤

- **현상**: 탭을 다른 데로 돌렸다 오면 진행 상태(타이머 표시, 폴링)가 멈춰 있다.
- **보이는 형태**: 숨겨진 동안 rAF 콜백이 오지 않는다.
- **원인**: 숨겨진 문서는 렌더링 업데이트 대상에서 빠진다(표준 "Filter non-renderable documents"). rAF는 렌더링 업데이트 안에서 돈다.
- **대처**: 비시각 로직(폴링·타이머)은 rAF에 두지 않는다. `visibilitychange`로 멈춤·재개를 명시한다. 숨은 탭의 타이머 조절(throttling)은 브라우저 정책이라 수치는 판마다 다르다 [?: Chrome의 숨은 탭 타이머 조절 수치는 이 노트에서 미확인].

## 핵심 문장

- 이벤트 루프는 태스크 하나를 끝까지 실행하고, 마이크로태스크 큐를 빌 때까지 비우고, 렌더링 기회에 렌더링 태스크를 돌린다.
- 태스크 큐는 여러 개이고 그중 무엇을 고를지는 브라우저가 정한다. 같은 태스크 소스 안의 순서만 보장된다.
- 마이크로태스크는 체크포인트가 "빌 때까지" 돌기 때문에, 스스로를 다시 걸면 렌더링과 다음 태스크를 막는다(실험: 500ms 동안 rAF 0회).
- 긴 태스크 중 입력은 태스크가 끝날 때까지 기다린다(실험: 약 250ms 지연). INP는 이 입력 지연·처리·표시 지연을 합친 지표다.
- rAF는 렌더링 업데이트 안, 스타일·레이아웃 직전에 돈다. 숨겨진 문서에서는 돌지 않는다.

## 관련 주제·근거

- 선행
  - [02-rendering-pipeline](../02-rendering-pipeline/2-summary.md) — 렌더링 업데이트에서 도는 스타일·레이아웃·페인트
  - [os/27-event-based-concurrency](../../os/27-event-based-concurrency/2-summary.md) — 이벤트 루프·반응기 패턴의 OS 쪽 모습
- 후속·연결
  - [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md) — 이벤트 디스패치가 태스크 안에서 어떻게 도나
  - [01-browser-architecture](../01-browser-architecture/2-summary.md) — 이벤트 루프를 공유하는 문서들
  - [08 `web-performance-vitals`](../08-web-performance-vitals/2-summary.md)(INP), [16 `long-tasks-and-web-workers`](../16-long-tasks-and-web-workers/2-summary.md)
  - 문법: [js/36 이벤트 루프와 마이크로태스크](../../../languages/js/syntax/36-event-loop-and-microtasks/2-summary.md), [web-api/38 rAF](../../../languages/web-api/38-request-animation-frame/2-summary.md), [web-api/39 유휴 스케줄링](../../../languages/web-api/39-idle-scheduling/2-summary.md)
  - 자료구조: [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md), [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- 문서
  - HTML 표준 8.1.7 Event loops — Definitions("Task queues are sets, not queues", "The microtask queue is not a task queue"), Processing model(태스크 선택·체크포인트·렌더링 기회·update the rendering 단계·idle 50ms 상한), perform a microtask checkpoint <https://html.spec.whatwg.org/multipage/webappapis.html#event-loops>
  - HTML 표준 Timers — 중첩 5단계 초과 시 4ms, map of active timers(ordered map, 키 → 만료 시각), run steps after a timeout의 순서 규칙 <https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers>
  - W3C Long Tasks API — "duration exceeds 50ms" <https://w3c.github.io/longtasks/>
  - W3C Event Timing — 8ms 단위, 기본 임계 104ms·최소 16ms, delay = processingStart − startTime <https://w3c.github.io/event-timing/>
  - web.dev, "Interaction to Next Paint (INP)" <https://web.dev/articles/inp> — 200ms·500ms, p75, 세 단계
  - ECMA-262 Jobs·HostEnqueuePromiseJob <https://tc39.es/ecma262/#sec-jobs>
- 실험 목록(headless Chrome 151.0.7922.173, Playwright `playwright-core`, Node 20, 127.0.0.1 로컬 페이지, 스로틀 없음, 2026-10-04)
  - `e03-order.js`: 동기·마이크로태스크·`setTimeout`·`MessageChannel`·rAF 실행 순서, 10회
  - `e03b-block.js`: 300ms 태스크 중 실제 클릭의 지연(Event Timing), 500ms 마이크로태스크 연쇄 vs 태스크 연쇄의 rAF 횟수·선행 타이머 시각, 각 3회
