# web-api/39 — 유휴 스케줄링: `requestIdleCallback` · `scheduler.postTask()`/`yield()` 와 긴 작업 쪼개기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 렌더링 단계와 틀 박자는 [38번 주제](../38-request-animation-frame/1-question.md), 마이크로태스크로 쪼개기는 [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/1-question.md), 서버의 스케줄러는 [`ops-patterns/10-scheduler`](../../../ops-patterns/10-scheduler/1-question.md)가 물었다. 여기는 **긴 작업이 입력을 어떻게 막나**와 **양보한 뒤 누가 먼저 도나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다(node 는 지원 판별만). **Safari 는 미실행** — Baseline 날짜로만. **시간 · INP 는 재지 않았다.**
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 어디에 무엇이 있나 (예측)

```js
// wa36b-39-q1.js
// 질문용 — 실행 대상 아님
// Chrome 151 페이지 · node 18 · node 20 에서 각각 —
typeof requestIdleCallback; typeof scheduler; typeof scheduler?.postTask; typeof scheduler?.yield;
typeof TaskController; typeof navigator.scheduling?.isInputPending;
// 그리고 node 의 require("timers/promises").scheduler 에는 무엇이 있나?
```

- 세 판 각각 `typeof` 는? node 의 `scheduler` 에는?

### 2. 긴 작업 중의 클릭 (예측)

```js
// wa36b-39-q2.js
// 질문용 — 실행 대상 아님
버튼.addEventListener("click", e => 적기(performance.now(), e.timeStamp));
// 작업을 시작하자마자 하네스가 버튼 클릭을 CDP 로 넣는다
// (가) 200ms 동기 루프 한 덩어리
// (나) 50ms 동기 루프 네 조각 — 조각 사이에 await scheduler.yield()
// (다) 50ms 동기 루프 네 조각 — 조각 사이에 await new Promise(r => setTimeout(r, 0))
// 각각 — 핸들러는 조각 몇 개가 끝났을 때 불리나? 작업이 다 끝난 뒤인가?
```

- (가)\~(다) 각각 핸들러는 언제?

### 3. 양보 뒤의 순서 (예측)

```js
// wa36b-39-q3.js
// 질문용 — 실행 대상 아님
for (const x of "ABC") setTimeout(() => 적기(x), 0);          // 다른 작업 셋을 먼저 줄 세운다
(async () => { 적기("1"); await 양보(); 적기("2"); await 양보(); 적기("3"); })();
// 양보 = scheduler.yield() 일 때와 양보 = setTimeout 0 일 때 — 적히는 순서는?
```

- 두 양보 각각 적히는 순서는?

### 4. `postTask` 우선순위 셋과 `setTimeout` (예측)

```js
// wa36b-39-q4.js
// 질문용 — 실행 대상 아님
setTimeout(() => 적기("setTimeout"), 0);
for (const p of ["background", "user-visible", "user-blocking"]) scheduler.postTask(() => 적기(p), { priority: p });
// 적히는 순서는?
```

- 적히는 순서는?

### 5. `timeRemaining()` 의 범위 (예측)

```js
// wa36b-39-q5.js
// 질문용 — 실행 대상 아님
requestIdleCallback(d => 적기(d.timeRemaining()));
// (가) 아무 일도 없는 페이지 · (나) rAF 고리가 도는 페이지 · (다) 30ms 뒤에 울릴 setTimeout 이 걸린 페이지
// 각각 timeRemaining() 은 어느 범위에 드나 — 50 초과 · 16.7 초과 50 이하 · 10 초과 16.7 이하 · 10 이하
// (라) 500ms 동기 작업 한 덩어리 「앞」에 requestIdleCallback(f, { timeout: 100 }) 과 requestIdleCallback(g) — 불리는 순서와 didTimeout 은?
```

- (가)\~(라) 각각은?

### 6. `timeRemaining()` 의 상한 (왜)

- 한가한 페이지에서도 넘지 않는 값이 있다면 그 수는 HTML 명세의 어느 단계에서 오나? 명세가 적은 **그 수의 이유**는? 그리고 그 마감을 **더 당기는 것** 둘은?

### 7. 「바쁜 페이지에서는 유휴 콜백이 안 불리다가 `timeout` 에만 불린다」 (경계)

- 이 판에서 그 문장을 시험한 조건과 결과는? 결과가 캡처마다 같았나? 그래서 `timeout` 은 무엇으로 읽어야 하나 — 어느 칸으로 가르나?

### 8. `yield` 와 `setTimeout 0` 을 견주기 (경계)

- 문항 2 와 문항 3 을 합쳐서 — 두 양보가 **같게** 한 일이 있나, **다르게** 한 일이 있나? 다르게 한 일이 있다면 그 가운데 명세가 정한 것과 구현이 고른 것을 갈라라.

### 9. 「`yield` 로 쪼개면 INP 가 줄어든다」 (경계)

- 이 편이 **잰 것**과 **재지 않은 것**을 갈라 답하라. 바꾼 창(「끼어들었나」)이 못 보는 것은?

### 10. 취소 · 우선순위 바꾸기 · 같은 우선순위끼리 (경계)

- `postTask` 직후 `TaskController.abort()` 하면 콜백과 약속은? `background` 로 건 일을 곧바로 `setPriority("user-blocking")` 하면? 같은 `background` 일 X(안에서 `yield`)와 뒤이어 등록한 Y 는 어느 순서인가 — 그 순서는 명세의 무엇이 정하나?

### 11. 다른 주제와 잇기 (연결)

- [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/1-question.md)의 「마이크로태스크로 잘게 쪼개 양보한다」가 틀린 이유를 문항 2 의 방식들과 견주어 말하라.
- [`ops-patterns/10-scheduler`](../../../ops-patterns/10-scheduler/1-question.md)의 스케줄러와 이 편의 스케줄러는 **무엇을 정하는 장치**인가 — 한 줄씩.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
