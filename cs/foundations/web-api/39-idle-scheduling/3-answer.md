# web-api/39 — 유휴 스케줄링: `requestIdleCallback` · `scheduler.postTask()`/`yield()` 와 긴 작업 쪼개기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 와 node v18.19.1 · v20.19.6 에서 실제로 받은 것**이다 — 페이지는 같은 기계의 로컬 서버(A)에서 열었고 **실제 시간**으로 돌렸다. 클릭은 CDP `Input.dispatchMouseEvent` 다.\
> ★ 명세는 **HTML(유휴 단계) · W3C requestIdleCallback · WICG Prioritized Task Scheduling** 을 받아 읽었다. **시간 · INP 는 재지 않았다.** Safari 는 미실행이다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 지원 판별 · 입력 막힘 판 · 이어가기 순서 · 유휴 가 \~ 라 | ★★ **흔들렸다** — 유휴 마(바쁜 동안의 열 판) 두 수 |
| 캡처를 세 판 돌려 **한 글자도 같았다**(유휴 마 한 줄 빼고) | **못 잰 것** — INP · 지연 ms · Safari · 진짜 손 입력 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. Chrome 은 다 있다 · node 는 전부 `undefined` — 대신 `timers/promises` 에 `yield` · `wait`

**출력**

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

```text
$ node wa36b-39-node.js; "$HOME/.nvm/versions/node/v20.19.6/bin/node" wa36b-39-node.js
node v18.19.1	requestIdleCallback=undefined · scheduler=undefined · TaskController=undefined · queueMicrotask=function · setImmediate=function
node v18.19.1	require("timers/promises").scheduler = object · 메서드 = yield, wait
node v20.19.6	requestIdleCallback=undefined · scheduler=undefined · TaskController=undefined · queueMicrotask=function · setImmediate=function
node v20.19.6	require("timers/promises").scheduler = object · 메서드 = yield, wait
(exit 0)
```

**왜 그런가**

- **Chrome 151** — `requestIdleCallback` · `scheduler.postTask` · `scheduler.yield` · `TaskController` · `navigator.scheduling.isInputPending` 전부 있다.
- **node 18 · 20** — 전역에는 **하나도 없다.** `require("timers/promises").scheduler` 는 `yield` · `wait` 를 가진 **node 의 별도 API** 다(`postTask` 가 없다).
- **Safari** — 미실행. Baseline 조회로 **두 API 모두 미구현**이다.

### 2. (가) 작업 끝 뒤 · (나)·(다) 첫 조각 뒤

**출력**

```text
$ python3 wa36b-net.py page wa36b-39-block.html
방식	클릭이 작업 중에 일어났나	핸들러가 불린 때 끝난 조각(/4)	핸들러가 작업 끝 뒤였나
한 덩어리	참 5 / 5 판	4	참 5 / 5 판
scheduler.yield	참 5 / 5 판	1	참 0 / 5 판
setTimeout 0	참 5 / 5 판	1	참 0 / 5 판
한 덩어리 작업 안에서 navigator.scheduling.isInputPending() 이 한 번이라도 true 였나 — 참 5 / 5 판
(exit 0)
```

**왜 그런가**

- **(가)** 클릭은 **작업 중에 일어났는데**(참 5 / 5) 핸들러는 **200ms 가 다 끝난 뒤**(참 5 / 5). 태스크는 도중에 안 끊긴다.
- **(나)·(다)** 둘 다 **끝난 조각 1** · 작업 끝 뒤였나 **참 0 / 5** — 첫 양보 사이에 끼었다. `isInputPending()` 은 한 덩어리 작업 안에서 **참이 됐지만**(5 / 5) 알려 줄 뿐이다.

### 3. `yield` — `1 2 3 A B C` · `setTimeout 0` — `1 A B C 2 3`

**출력**

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

**왜 그런가**

- **가 줄** — `yield` 뒤의 나머지는 **이어가기**라 먼저 줄 선 타이머 A · B · C 보다 **앞**에 섰다.
- **나 줄** — `setTimeout 0` 뒤의 나머지는 **새 타이머**라 A · B · C **뒤**에 섰다.

### 4. `user-blocking → setTimeout → user-visible → background`

**출력**

```text
$ python3 wa36b-net.py page wa36b-39-order.html | sed -n '3p'
다 postTask 를 background → user-visible → user-blocking 순으로 등록 (setTimeout 0 을 먼저)	user-blocking → setTimeout → user-visible → background
(exit 0)
```

**왜 그런가**

- 등록 순서(`background` 먼저)와 **정반대**로 돌았다 — 우선순위가 높은 줄부터.
- `setTimeout` 은 **`user-blocking` 과 `user-visible` 사이**에 끼었다. 그 자리는 명세가 「**implementation-defined**」로 두고 전략의 예(유효 우선순위 3 이상은 높게 · 2 는 타이머처럼 · 0 · 1 은 나중)만 든다 — **Chrome 은 그 예대로** 돌았다.

### 5. (가) 16.7 초과 · 50 이하 · (나) 16.7 이하 · (다) 타이머까지 남은 시간 이하 · (라) timeout 쪽 먼저, `true / false`

**출력**

```text
$ python3 wa36b-net.py page wa36b-39-idle.html
가 한가한 페이지 · 20번	범주 = 16.7 초과 · 50 이하 · 가장 큰 값이 50 이하인가 = true
나 rAF 고리가 도는 페이지 · 20번	가장 큰 값이 16.7 이하인가 = true
다 30ms 타이머가 걸린 페이지 · 20번	타이머보다 먼저 불린 번 중 timeRemaining 이 타이머까지 남은 시간(+1ms) 이하 = 20 / 20
라 500ms 동기 작업 앞에 건 rIC 둘	불린 순서 = timeout 100 → timeout 없음 · didTimeout = true / false · 둘 다 작업 끝 뒤 = true
마 rAF 마다 20ms 바쁜 500ms · 열 판	timeout 없는 rIC 가 바쁨이 끝난 뒤에야 불린 판 = 4 / 10 · timeout 100 인 rIC 가 didTimeout=true 인 판 = 5 / 10
(exit 0)
```

**왜 그런가**

- **(가)** 한가하면 마감은 「유휴 시작 + 50」 — 20번 모두 그 상한 **가까이**(16.7 초과 · 50 이하).
- **(나)** rAF 가 기다리면 마감이 **다음 렌더링**으로 당겨진다 — 전부 16.7 이하.
- **(다)** 걸린 타이머가 마감을 당긴다 — 타이머보다 먼저 불린 20번 모두 **타이머까지 남은 시간(+1ms) 이하**.
- **(라)** 500ms 작업 중에 100ms 가 지나 **timeout 쪽이 태스크로 먼저** 섰다(`didTimeout = true`). 없는 쪽은 한가해진 뒤(`false`). 둘 다 작업 끝 뒤다.
- ★ 이 블록의 **마지막 줄(마)** 은 A7 이다 — 판마다 수가 움직인다.

### 6. 50 — 「유휴 시작 + 50」 · 사람이 느끼는 한계 안에서 입력에 답하려고 · 타이머와 렌더링이 당긴다

- HTML 이벤트 루프의 유휴 단계 — 「**Let deadline be this event loop's last idle period start time plus 50.**」
- 이유 — 「**The cap of 50ms in the future is to ensure responsiveness to new user input within the threshold of human perception.**」 (requestIdleCallback 명세는 100ms 안의 응답이 즉각으로 느껴진다는 연구를 근거로 든다.)
- 더 당기는 것 — **활성 타이머**(`timerCallbackEstimates`)와 **기다리는 렌더링**(`hasPendingRenders` → 다음 렌더링 시각). A5 의 (나)·(다) 가 그것이다.

### 7. 성립하지 않았다 · 판마다 달랐다 · `timeout` 은 상한 — `didTimeout` 으로 가른다

**출력**

```text
$ python3 wa36b-net.py page wa36b-39-idle.html | sed -n '5p'
마 rAF 마다 20ms 바쁜 500ms · 열 판	timeout 없는 rIC 가 바쁨이 끝난 뒤에야 불린 판 = 4 / 10 · timeout 100 인 rIC 가 didTimeout=true 인 판 = 5 / 10
(exit 0)
```

**왜 그런가**

- 조건 — **rAF 마다 20ms 씩 바쁜 500ms** 동안 `timeout` 없는 것과 `timeout 100` 인 것을 건다. 열 판.
- 결과 — timeout 없는 쪽이 **바쁨이 끝난 뒤에야** 불린 판이 **열 판 중 일부뿐**이다 — 나머지는 바쁜 동안에도 불렸다. `timeout 100` 쪽의 `didTimeout=true` 도 **일부 판**이다. **수는 캡처마다 움직였다** — 캡처 세 판에서 timeout 없는 쪽 **4 · 5 · 4** / 10, `didTimeout=true` 쪽 **5 · 5 · 5** / 10(이쪽은 세 캡처가 같았지만 판 단위로는 참과 거짓이 섞였다).
- 그래서 **`timeout` 은 「늦어도 이때까지」** 다 — 바빠도 틀 사이의 짧은 유휴에서 먼저 불릴 수 있다. 어느 쪽인지는 **`deadline.didTimeout`** 이 가른다.

### 8. 같게 — 입력을 끼웠다 · 다르게 — 남의 타이머와의 순서

- **같게 한 일** — 두 방식 다 **첫 조각 뒤에 클릭 핸들러를 끼웠다**(A2 — 작업 끝 뒤였나 참 0 / 5).
- **다르게 한 일** — **먼저 줄 선 타이머와의 순서**. `yield` 는 `1 2 3 A B C`, `setTimeout 0` 은 `1 A B C 2 3`(A3).
- **명세가 정한 것** — 이어가기가 **같은 우선순위의 새 일보다** 앞선다(유효 우선순위 표 — A10 의 `X1 → X2 → Y`).
- **구현이 고른 것** — 이어가기가 **타이머(다른 태스크 원천)보다** 앞선 것. 스케줄러 태스크와 다른 태스크 사이는 「implementation-defined」다.

### 9. 잰 것 — 「끼어들었나 · 몇 조각 뒤」 · 안 잰 것 — ms · INP

- **잰 것** — 핸들러가 **작업 끝 뒤였나**(한 덩어리 5 / 5 · 쪼갠 두 방식 0 / 5)와 **끝난 조각 수**(4 · 1 · 1).
- **안 잰 것** — 입력 지연 **ms** · **INP** · 화면에 결과가 그려진 때.
- **바꾼 창이 못 보는 것** — **얼마나 빨리**와 **다음 그림까지**. 「끼었다」는 응답이 **가능해졌다**는 뜻이지 **빨라진 양**이 아니다.

### 10. 콜백 안 돎 · `AbortError` · 먼저 돈다 · `X1 → X2 → Y` — 유효 우선순위 표

**출력**

```text
$ python3 wa36b-net.py page wa36b-39-order.html | sed -n '4,6p'
라 postTask 직후 TaskController.abort()	콜백 안 돌았다 · 약속 거부 AbortError: signal is aborted without reason
마 background 로 건 일을 곧바로 setPriority("user-blocking")	tc 의 일 → user-visible 일
바 background 일 X(안에서 yield) 와 뒤이어 등록한 background 일 Y	X1 → X2 → Y
(exit 0)
```

**왜 그런가**

- **`abort()`** — 콜백은 **안 돌았고** 약속은 **`AbortError: signal is aborted without reason`** 으로 거부됐다.
- **`setPriority("user-blocking")`** — 뒤에 등록한 `user-visible` 일보다 **먼저** 돌았다(`tc 의 일 → user-visible 일`). 신호에 묶인 태스크는 **우선순위가 움직인다**(명세의 동적 우선순위 큐).
- **`X1 → X2 → Y`** — X 의 이어가기(`background` · 이어가기 = 1)가 Y(`background` 태스크 = 0)보다 높다. **명세의 유효 우선순위 표**가 정한다.

### 11. 마이크로태스크는 양보가 아니다 · 벽시계 방아쇠 대 한 스레드 안의 양보 순서

- **JS 36편** — 마이크로태스크 체크포인트는 **빌 때까지** 돈다. 쪼갠 조각을 `then` 으로 이으면 **태스크 경계가 안 생겨** 문항 2 의 (가)와 같은 모양(작업 끝 뒤)이 된다 — 입력이 낄 자리가 없다. 끼우려면 (나)·(다)처럼 **태스크로** 양보해야 한다.
- **`ops-patterns/10-scheduler`** — 「**언제 돌릴지**」(주기 · 밀린 실행을 몰아서/버리고/다시 세기)를 **벽시계**로 정하는 장치.
- **이 편의 스케줄러** — 한 스레드 안에서 「**지금 누구에게 먼저 양보할지**」(입력 · 이어가기 · 우선순위 · 유휴)를 정하는 장치.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless(실제 시간) · node v18.19.1 · v20.19.6 · Python 3 표준 라이브러리 `http.server`(서버 A). **엔진은 Chrome 하나다.**

★ **하네스** — [36번 주제](../36-resize-observer/3-answer.md)의 `wa36b-net.py`. 「누르기」는 `Input.dispatchMouseEvent` 두 번(누름 · 뗌)을 **응답을 기다리지 않고** 보낸다.

```sh
# wa36b-39-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa36b-net.py page wa36b-39-support.html
node wa36b-39-node.js; "$HOME/.nvm/versions/node/v20.19.6/bin/node" wa36b-39-node.js
python3 wa36b-net.py page wa36b-39-block.html
python3 wa36b-net.py page wa36b-39-order.html
python3 wa36b-net.py page wa36b-39-idle.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 지원 판별(Chrome · node 두 판) | 캡처 3판 | 동작 방식 (1) · A1 |
| 입력 막힘 판 3방식 × 5판 | 캡처 3판 | 동작 방식 (2) · A2 · A8 · A9 |
| 이어가기 순서 여섯 | 캡처 3판 | 동작 방식 (3) · A3 · A4 · A8 · A10 |
| 유휴 가 \~ 라 | 캡처 3판 | 동작 방식 (4) · A5 · A6 |
| 유휴 마(바쁜 동안 열 판) | 캡처 3판 — **판마다 수가 달랐다** | 동작 방식 (5) · A7 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `yield` 이어가기가 타이머보다 앞 | 앞 | implementation-defined |
| `setTimeout` 이 `user-blocking` 과 `user-visible` 사이 | 사이 | implementation-defined |
| `isInputPending` | 있다 | 받은 명세 밖의 표면 — 판이 오르면 빠질 수 있다 |
| 바쁜 동안의 유휴 콜백 | 판마다 다름 | 유휴 기간은 user agent defined |

**안 돌려 본 것** — ① Firefox·Safari(Safari 는 없다 · Firefox 는 이 환경에서 헤드리스 산출이 조용히 실패한다 — README). ② INP · 지연 ms. ③ 숨은 탭의 유휴 기간. ④ `postTask` 의 `delay` · `prioritychange`.
