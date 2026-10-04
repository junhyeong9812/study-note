# web-platform/16-long-tasks-and-web-workers — 긴 태스크, 양보(yield), 웹 워커와 메시지 복제 비용 — 정리 (힌트)

## 해결하는 문제

브라우저 메인 스레드는 JS 실행, 이벤트 처리, 스타일·레이아웃·페인트를 **한 줄로** 처리한다(03 이벤트 루프).
그래서 JS 하나가 오래 돌면 그동안 클릭도, 화면 갱신도 기다린다.

```text
  메인 스레드 (한 줄)
  ──[ 클릭 핸들러: 300ms 계산 ]────────────────────[다른 클릭 처리][페인트]──>
            ↑ 사용자가 60ms 뒤 다른 버튼 클릭 → 240ms 넘게 기다림
```

- *긴 태스크(long task)*: 50ms를 넘는 태스크. 50ms를 넘는 부분을 "차단 시간"으로 본다(web.dev "Optimize long tasks").
- *INP(Interaction to Next Paint)*: 클릭·탭·키 입력에서 다음 화면이 그려질 때까지의 지연. 페이지의 상호작용 중 가장 느린 축(50번당 최고 1개는 제외)을 고르고, 사용자 페이지 뷰의 75번째 백분위로 판정한다. 200ms 이하 "좋음", 500ms 초과 "나쁨"(web.dev "Interaction to Next Paint").

쉬운 예: 계산대가 하나뿐인 가게다.
- 손님 한 명(긴 계산)이 계산대를 300ms 붙잡으면 뒤의 손님(클릭)은 기다린다.
- 계산을 잘게 나눠 중간에 "잠깐만요" 하고 비켜 주면(양보) 급한 손님이 끼어든다.
- 아예 뒤쪽 창고 직원(워커)에게 계산을 맡기면 계산대는 계속 비어 있다. 대신 물건을 창고로 나르는 비용(메시지 복제)이 든다.

똑같은 구조다.\
실무 예:
- 필터 버튼을 누르면 5만 건을 클라이언트에서 정렬·집계 → "버튼이 안 눌린다", INP 나쁨.
- 엑셀 파일 파싱, 이미지 처리, 마크다운 렌더, 큰 JSON 파싱을 클릭 핸들러 안에서 바로 한다.

## 동작·원리

### 1. 상호작용 지연의 세 조각

```text
  사용자 입력                                                    다음 프레임 표시
     │◄── input delay ──►│◄── processing ──►│◄── presentation delay ──►│
     │ (앞 태스크가 끝나기 │ (이벤트 핸들러들 │ (스타일·레이아웃·페인트·  │
     │   를 기다림)        │   실행)          │   합성)                   │
     └──────────────────────── 상호작용 지연(INP 후보) ─────────────────────┘
```

- web.dev INP 문서의 정의다. 긴 태스크는 **두 군데**에서 INP를 키운다.
  - 내 핸들러가 길면 → processing이 길다.
  - 다른 태스크가 길면 → 그 사이 들어온 입력의 input delay가 길다.
- 브라우저 측정 API는 *Event Timing*(W3C)이다. 항목의 `duration`은 이벤트 `startTime`부터 그 뒤 렌더링 갱신이 끝날 때까지이고, 8ms 단위로 반올림된다. `durationThreshold`는 최소 16ms, 기본 104ms다(W3C Event Timing).

### 2. 처방 세 가지

```text
  (a) 그대로        ███████████████████████████████ (300ms 한 태스크) → 클릭은 끝난 뒤
  (b) 쪼개고 양보   ███ ▸ ███ ▸ ███ ▸ ... (30ms × 10, ▸ = 양보)  → 클릭이 ▸ 자리에 끼어듦
  (c) 워커로        메인: ▮(postMessage)                   ▮(결과 반영)
                    워커: ███████████████████████████████
```

- **(b) 양보(yield)**: 일을 조각으로 나누고, 조각 사이에 메인 스레드를 돌려준다.
  - `await scheduler.yield()`: 이어지는 코드를 **우선순위가 높은 이어가기(continuation)** 로 예약한다. 다른 태스크(입력 처리 등)가 먼저 돌 기회를 얻고, 그 뒤 새로 쌓인 일반 태스크보다 먼저 이어 간다(web.dev "Optimize long tasks").
  - `setTimeout(r, 0)`: 이어지는 코드가 태스크 큐의 **맨 뒤**로 간다. 그 사이 다른 스크립트의 태스크가 먼저 돌 수 있다.
  - 매 조각마다 양보하면 오버헤드가 생긴다. 문서는 "마감(예: 50ms)이 지나면 양보"하는 묶음 방식을 권한다.
  - `navigator.scheduling.isInputPending()`은 더 이상 권장하지 않는다(같은 문서).
  - 각 API의 지원 판별·우선순위·`requestIdleCallback` 규칙은 [web-api/39 유휴 스케줄링](../../../languages/web-api/39-idle-scheduling/2-summary.md)에 있다.
- **(c) 웹 워커**: 별도 스레드에서 JS를 돌린다.
  - *Web Worker*: 페이지와 다른 이벤트 루프·전역 객체를 가진 실행 컨텍스트. DOM과 `window`·`document`가 없다(web.dev "Use web workers…", HTML 표준 "Web workers" 절).
  - 메인과 워커는 기본적으로 `postMessage`로 대화한다. 메시지는 받는 쪽 큐에 쌓이는 태스크다.
  - 예외: 문서가 교차 출처 격리(COOP·COEP 헤더)된 경우 `SharedArrayBuffer`를 넘겨 같은 메모리를 함께 읽고 쓸 수 있다. 동기화는 `Atomics`로 한다(MDN `SharedArrayBuffer`).
  - web.dev는 메인 스레드 밖 실행(OMT)이 앱을 더 넓은 기기에서 안정적으로 돌게 할 뿐 "더 빠르게 하지는 않는다"고, 워커와 메인 사이 통신 오버헤드 때문에 "때로 약간 더 느려질 수 있다"고 적는다.

### 3. `postMessage`의 비용 — 구조적 복제 vs 소유권 이전

```text
  구조적 복제 (기본)                         Transferable (소유권 이전)
  메인 [32MB 배열] ──직렬화(복사)──> 워커 [32MB 사본]   메인 [buffer] ──포인터 넘김──> 워커 [buffer]
       원본 그대로 남음                                  원본은 detached (byteLength 0)
       비용 ∝ 데이터 크기·객체 수                        비용 ≈ 크기와 무관
```

- *구조적 복제(structured clone)*: 값을 직렬화해 다른 realm에 다시 만드는 HTML 표준 알고리즘. 함수처럼 직렬화할 수 없는 값을 만나면 `DataCloneError`를 던진다(HTML 표준 "Safe passing of structured data").
- *Transferable*: `ArrayBuffer`·`MessagePort`·`ImageBitmap` 등. 넘기면 받는 쪽이 같은 데이터를 쓰고, 보낸 쪽 객체는 detach되어 다시 쓸 수 없다(같은 절 — "irreversible and non-idempotent").
- 직렬화는 **보내는 스레드에서 동기로** 일어난다. 그래서 큰 객체 그래프를 보내면 `postMessage` 호출 자체가 메인 스레드의 긴 태스크가 된다.
  - web.dev는 JSON으로 10KB 미만이면 대개 문제없고, 더 크면 `ArrayBuffer`(Transferable)나 WebAssembly를 고려하라고 한다.

### 실험: 같은 300ms 일을 세 방식으로 — 클릭 지연 비교

조건: 300ms 바쁜 루프(`while (performance.now() < end)`)를 `go` 버튼 클릭 핸들러에서 돌린다. 60ms 뒤 CDP로 `other` 버튼을 클릭한다. Event Timing(`durationThreshold: 16`)·`longtask`·`long-animation-frame` 항목을 모은다.

```js
// lt.html 핵심 (scratchpad/wp/16/www/lt.html)
go.addEventListener('click', async () => {
  if (mode === 'sync') { busy(300); out.textContent = 'done'; }
  else if (mode === 'yield') {
    out.textContent = 'working…';
    for (let i = 0; i < 10; i++) { await scheduler.yield(); busy(30); }   // 30ms 조각 10개
    out.textContent = 'done';
  } else if (mode === 'worker') {
    out.textContent = 'working…';
    w.onmessage = () => { out.textContent = 'done'; };
    w.postMessage(300);                                                  // 워커가 300ms 바쁜 루프
  }
});
```

(실험, headless Chrome 151.0.7922.173, 스로틀 없음, 뷰포트 800×600, 2026-10-04 — 단위 ms, `<16`은 임계 16ms 미만이라 항목이 없었다는 뜻)

```text
sync 0 {"go":312,"other":248,"otherInputDelay":242,"longtasks":[302],"loaf":[305]}
sync 1 {"go":312,"other":248,"otherInputDelay":244,"longtasks":[304],"loaf":[305]}
sync 2 {"go":312,"other":248,"otherInputDelay":243,"longtasks":[303],"loaf":[306]}
sync 3 {"go":312,"other":256,"otherInputDelay":246,"longtasks":[306],"loaf":[308]}
sync 4 {"go":312,"other":248,"otherInputDelay":243,"longtasks":[303],"loaf":[305]}
yield 0 {"go":"<16","other":"<16","otherInputDelay":9,"longtasks":[],"loaf":[65]}
yield 1 {"go":16,"other":"<16","otherInputDelay":"n/a","longtasks":[],"loaf":[]}
yield 2 {"go":16,"other":"<16","otherInputDelay":"n/a","longtasks":[],"loaf":[]}
yield 3 {"go":"<16","other":16,"otherInputDelay":9,"longtasks":[],"loaf":[56]}
yield 4 {"go":"<16","other":16,"otherInputDelay":8,"longtasks":[],"loaf":[56]}
worker 0 {"go":16,"other":"<16","otherInputDelay":"n/a","longtasks":[],"loaf":[]}
worker 1 {"go":"<16","other":"<16","otherInputDelay":"n/a","longtasks":[],"loaf":[]}
...
worker 4 {"go":"<16","other":"<16","otherInputDelay":"n/a","longtasks":[],"loaf":[]}
```

- **sync**: `go` 상호작용 312ms — INP 기준 "개선 필요"(200 초과)다. 60ms 뒤 누른 `other`는 input delay만 242~246ms. 긴 태스크 1개(301~306ms, 재실행 포함).
- **yield**: 두 상호작용 모두 16ms 이하(같은 날 앞선 3회 실행에서는 `other`가 24ms인 판도 있었다). `other`의 input delay는 8~10ms(사실 점검 재실행 포함) — 진행 중이던 30ms 조각이 끝나기를 기다린 만큼이다. 긴 태스크는 없다.
  - 그런데 `loaf`(Long Animation Frame)가 55~65ms로 잡힌 판이 있다(재실행 포함). 해석: LoAF는 **태스크가 아니라 프레임** 단위다. 30ms 조각 둘이 한 프레임 안에 이어 돌면 그 프레임이 50ms를 넘는다. "긴 태스크 0개"가 "프레임 지연 0"을 뜻하지는 않는다.
- **worker**: 두 상호작용 모두 16ms 이하(재실행 1회에서 `other` 항목이 16ms·input delay 2ms로 잡혔다). 메인 스레드에는 긴 태스크·LoAF가 없다. 300ms 계산은 워커 스레드에서 돌았다.
- 결과 표시까지의 **총 시간**은 세 방식이 비슷하게 300ms 이상이다. 처방은 일을 줄이는 것이 아니라 입력이 **끼어들 자리**를 만드는 것이다.

## 쓰이는 자료구조·알고리즘

- **협력적 스케줄링(청크 분할)**: 운영체제의 선점 스케줄링과 달리, 메인 스레드는 태스크 도중에 끊기지 않는다. 일을 하는 쪽이 스스로 조각을 나누고 양보해야 한다 — [os/08 CPU 스케줄링](../../os/08-cpu-scheduling/2-summary.md)의 비선점·협력 모델, [os/27 이벤트 기반 동시성](../../os/27-event-based-concurrency/2-summary.md)의 "핸들러는 짧게"와 같은 원리다.
- **메시지 큐**: 워커와 페이지는 공유 메모리 없이 각자의 큐로 메시지를 주고받는다(액터 모델과 같은 모양) — [data-structure/04 큐](../../data-structure/04-queue-deque/2-summary.md).
- **우선순위 큐**: `scheduler.postTask`의 `user-blocking`·`user-visible`·`background`, `scheduler.yield()`의 이어가기 우선순위는 우선순위가 있는 태스크 큐다.
- **직렬화 = 그래프 순회**: 구조적 복제는 객체 그래프를 순회하며 방문 표(memory)로 순환 참조를 처리한다(HTML 표준 StructuredSerializeInternal의 memory 맵). 그래서 비용이 객체 수에 비례한다.
- **소유권 이전**: Transferable은 "한 시점에 한 쪽만 소유"하는 이동(move) 의미론이다. 복사 비용 대신 원본을 못 쓰게 되는 대가를 낸다.

## 적용 — 풀어나가는 법

1. **측정부터** — 어느 상호작용이 느린지, 원인이 input delay·processing·presentation 중 어디인지 본다.

```js
// 느린 상호작용과 세 조각 (Chrome 151에서 확인한 Event Timing 필드)
new PerformanceObserver(list => {
  for (const e of list.getEntries()) {
    if (!e.interactionId) continue;
    console.log(e.name, e.duration,
      'input', e.processingStart - e.startTime,
      'proc', e.processingEnd - e.processingStart,
      'present', e.startTime + e.duration - e.processingEnd);
  }
}).observe({ type: 'event', durationThreshold: 16, buffered: true });
// 어떤 스크립트가 프레임을 붙잡았나 — Long Animation Frames (scripts 속성에 출처가 담긴다.
// 단 메인 스레드·같은 출처 iframe의 5ms 넘는 스크립트만. 교차 출처 iframe·워커·확장 코드는 빠지고,
// 렌더링 작업만으로 긴 프레임이면 scripts가 비어 있을 수 있다 — Chrome for Developers LoAF 문서)
new PerformanceObserver(l => l.getEntries().forEach(f => console.log(f.duration, f.scripts)))
  .observe({ type: 'long-animation-frame', buffered: true });
```

   - 현장 수치는 `web-vitals` 라이브러리의 `onINP`(attribution 빌드)로 RUM에 보낸다. 랩(DevTools Performance 패널) 수치와 섞지 않는다(08 Web Vitals).
2. **피드백 먼저, 무거운 일은 나중** — 핸들러에서 화면 변화(로딩 표시)를 먼저 하고 양보한 뒤 무거운 일을 한다. 그러면 로딩 표시가 다음 프레임에 그려질 **기회**가 생긴다. 양보가 렌더링을 보장하지는 않는다(렌더 갱신 시점은 브라우저가 정한다 — HTML 표준 "update the rendering").
3. **쪼개고 양보** — 마감 기반 묶음이 기본형이다.

```js
async function processAll(items, work) {
  let deadline = performance.now() + 50;          // 50ms = 긴 태스크 경계
  for (const it of items) {
    work(it);
    if (performance.now() >= deadline) {
      await (globalThis.scheduler?.yield?.() ?? new Promise(r => setTimeout(r, 0)));  // yield 미지원 시 폴백
      deadline = performance.now() + 50;
    }
  }
}
```

4. **CPU 위주이고 DOM이 필요 없는 일은 워커로** — 파싱·정렬·집계·압축·이미지 처리. 결과만 받아 DOM에 반영한다.
   - 큰 숫자 데이터는 `TypedArray`로 만들어 `postMessage(msg, [buf])`로 넘긴다(Transferable).
   - 큰 객체 그래프를 왕복시키지 말고, 워커가 데이터를 **소유**하게 둔다. 원본을 워커에서 fetch·파싱하고 요약만 메인으로 보낸다.
   - Comlink 같은 라이브러리는 `postMessage`를 함수 호출처럼 감싼다(web.dev가 소개). 복제 비용은 그대로다.
5. **취소·경쟁 처리** — 사용자가 다시 누르면 이전 계산 결과를 버린다(요청 번호 비교, `AbortSignal`, `worker.terminate()`).

### 실험: 구조적 복제 vs Transferable, 워커 안 `document`, 함수 복제

```js
// clone.html 핵심 — sendMs = postMessage 호출이 메인 스레드에서 걸린 시간
const t0 = performance.now(); w.postMessage(msg, transfer); const sendMs = performance.now() - t0;
let a = new Float64Array(4_000_000).fill(1.5);    // 32MB
ask(a);              // 복제
ask(a, [a.buffer]);  // 이전 → a.byteLength === 0
ask(Array.from({ length: 200_000 }, (_, i) => ({ id: i, name: 'item' + i, tags: ['a', 'b'], price: i * 1.1 })));
```

(실험, headless Chrome 151.0.7922.173, 스로틀 없음, 2026-10-04, 3회 — endToEnd는 보낸 시각부터 워커가 받은 시각까지, 두 컨텍스트의 `timeOrigin + now()` 차이)

```text
0 {"typedClone":{"sendMs":48.6,"endToEndMs":106.5},"typedCloneLenAfter":32000000,"typedTransfer":{"sendMs":0.1,"endToEndMs":0.6},"typedTransferLenAfter":0,"objClone":{"sendMs":304.7,"endToEndMs":609.6},"domInWorker":"ReferenceError: document is not defined","fnClone":"DataCloneError: Failed to execute 'postMessage' on 'Worker': () => 1 could not be cloned."}
1 {"typedClone":{"sendMs":43.7,"endToEndMs":87.9},...,"typedTransfer":{"sendMs":0.2,"endToEndMs":0.3},...,"objClone":{"sendMs":247.5,"endToEndMs":525.8},...}
2 {"typedClone":{"sendMs":39.6,"endToEndMs":82.3},...,"typedTransfer":{"sendMs":0.1,"endToEndMs":0.2},...,"objClone":{"sendMs":240.5,"endToEndMs":558.4},...}
```

- 32MB `Float64Array` 복제: 메인 스레드 40~49ms, 도착까지 82~107ms. 이전(transfer): 0.1~0.3ms(재실행 포함), 이후 원본 `byteLength`는 0.
- 객체 20만 개 배열 복제: **메인 스레드에서 240~305ms**(사실 점검 재실행 240~257ms) — 그 자체가 긴 태스크다. 워커에 일을 넘기려다 메인에 300ms짜리 긴 태스크를 새로 만든 셈이다.
- 워커 안 `document` → `ReferenceError: document is not defined`. 함수가 든 메시지 → `DataCloneError`.

## 장애 시나리오와 대처

### 1. "버튼이 안 눌린다" — 클릭 핸들러 안의 무거운 계산

- 현상: 필터·정렬 버튼을 누르면 화면이 굳고, 그 사이 누른 다른 버튼도 늦게 반응한다.
- 보이는 형태: RUM INP p75가 200ms 초과. Event Timing 항목의 processing이 길다. DevTools Performance 패널에 빨간 삼각형 표시가 붙은 긴 태스크. 위 실험의 sync(312ms, 다른 클릭 input delay 242~246ms).
- 원인: 동기 계산이 한 태스크로 메인 스레드를 붙잡는다.
- 대처: 피드백 먼저 → 마감 기반으로 쪼개 `scheduler.yield()`(미지원 시 `setTimeout` 폴백) → CPU 위주면 워커. 계산 자체를 줄이는 것(인덱스·캐시·서버 집계)도 함께 검토한다.

### 2. 워커로 옮겼는데 더 느려졌다 — 구조적 복제 비용

- 현상: 워커 도입 후에도 클릭 직후 화면이 굳는다. 전체 처리 시간은 오히려 늘었다.
- 보이는 형태: Performance 패널에서 `postMessage` 호출(직렬화)과 `message` 이벤트(역직렬화)가 긴 태스크로 보인다. 위 실험의 객체 20만 개 복제 = 메인 240~305ms.
- 원인: 큰 객체 그래프를 매번 왕복 복제한다. 복제는 보내는 스레드에서 동기로 일어난다.
- 대처: 데이터를 워커가 소유(워커에서 fetch·파싱), 요약만 전송. 숫자 대량 데이터는 TypedArray + Transferable. 보낸 뒤 원본을 쓰는 코드가 있으면 detach로 깨지니 함께 고친다.

### 3. 워커 안에서 DOM 접근 — `ReferenceError: document is not defined`

- 현상: 메인에서 쓰던 유틸(DOM 파서·`localStorage`·`window` 참조)을 워커에 그대로 옮겼더니 에러.
- 보이는 형태: 워커의 `error` 이벤트, 콘솔 `ReferenceError: document is not defined`(위 실험 출력 그대로).
- 원인: 워커 전역(`DedicatedWorkerGlobalScope`)에는 DOM이 없다.
- 대처: 워커는 순수 계산만, DOM 갱신은 메인에서. 의존 라이브러리가 `window`를 참조하는지 확인한다. 함수·DOM 노드를 메시지에 넣으면 `DataCloneError`가 난다.

### 4. 양보했는데도 INP가 나쁘다

- 현상: 긴 태스크는 사라졌는데 INP가 그대로다.
- 보이는 형태: Event Timing의 presentation delay가 크다. LoAF 항목이 남는다(위 실험의 yield에서도 55~65ms LoAF).
- 원인 후보: 조각 여러 개가 한 프레임에 몰림, 양보 후 큰 DOM 갱신(스타일·레이아웃이 큼 — 17 가상화·18 재렌더), 다른 서드파티 스크립트의 긴 태스크가 input delay를 만듦.
- 대처: LoAF의 `scripts` 속성으로 출처를 찾는다(메인 스레드 스크립트만 잡힌다 — `scripts`가 비면 렌더링 작업을 의심). 렌더링 비용이 원인이면 DOM 크기·재렌더 범위를 줄인다.

## 핵심 문장

- 메인 스레드는 태스크 도중에 끊기지 않으므로, 50ms를 넘는 태스크는 그동안 들어온 입력을 모두 기다리게 한다.
- 양보(`scheduler.yield()`)는 일의 총량을 줄이지 않고, 입력이 끼어들 자리를 만든다.
- 웹 워커는 DOM 없는 별도 스레드이고 기본적으로 `postMessage`로 대화하며(교차 출처 격리 시 `SharedArrayBuffer` 공유도 가능), 메시지는 기본적으로 보내는 쪽에서 동기로 구조적 복제된다.
- 큰 객체 그래프를 워커로 복제하면 그 복제 자체가 메인 스레드의 긴 태스크가 될 수 있다 — 숫자 대량 데이터는 Transferable로 넘긴다.
- 긴 태스크가 없어도 한 프레임에 조각이 몰리면 LoAF와 INP는 나빠질 수 있다.

## 관련 주제·근거

- 선행: [03 이벤트 루프](../03-event-loop/2-summary.md), [08 Web Vitals](../08-web-performance-vitals/2-summary.md)
- 후속: [17 목록 가상화](../17-list-virtualization/2-summary.md), [18 재렌더와 메모이제이션](../18-ui-rerender-and-memoization/2-summary.md), [19 하이드레이션 비용](../19-hydration-cost-and-partial-hydration/2-summary.md), [23 증상 색인](../23-web-symptom-index/2-summary.md)
- 문법·API: [web-api/39 유휴 스케줄링](../../../languages/web-api/39-idle-scheduling/2-summary.md), [web-api/38 requestAnimationFrame](../../../languages/web-api/38-request-animation-frame/2-summary.md)
- 다른 영역: [os/08 CPU 스케줄링](../../os/08-cpu-scheduling/2-summary.md), [os/27 이벤트 기반 동시성](../../os/27-event-based-concurrency/2-summary.md), [data-structure/04 큐](../../data-structure/04-queue-deque/2-summary.md)
- 근거
  - web.dev "Optimize long tasks" https://web.dev/articles/optimize-long-tasks — 50ms 정의, `scheduler.yield()` 이어가기, 마감 기반 양보, `isInputPending` 비권장
  - web.dev "Interaction to Next Paint (INP)" https://web.dev/articles/inp — 200/500ms, p75, 세 조각, 대상 입력
  - W3C Event Timing https://w3c.github.io/event-timing/ — `durationThreshold` 최소 16·기본 104, 8ms 단위, `interactionId`
  - web.dev "Use web workers to run JavaScript off the browser's main thread" https://web.dev/articles/off-main-thread — DOM 접근 불가, 10KB 기준, 오버헤드 경고
  - HTML 표준 "Safe passing of structured data" https://html.spec.whatwg.org/multipage/structured-data.html — `DataCloneError`, Transferable·detach
  - HTML 표준 "Web workers" https://html.spec.whatwg.org/multipage/workers.html
  - Chrome for Developers "Long Animation Frames API" https://developer.chrome.com/docs/web-platform/long-animation-frames — script attribution 범위(메인 스레드·5ms 초과, 교차 출처 iframe·워커 제외)
  - MDN `SharedArrayBuffer` https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer — 보안 컨텍스트·교차 출처 격리 조건, `Atomics`
- 실험 목록 (headless Chrome 151.0.7922.173, Node 20.19.6 + playwright-core 1.62.1, 127.0.0.1 로컬 서버, 2026-10-04)
  - 16-A 긴 태스크 vs yield vs worker: `scratchpad/wp/16/exp16-lt.js`, `www/lt.html`, `www/lt-worker.js` — 모드당 5회
  - 16-B 복제 vs 이전·워커 DOM·함수 복제: `scratchpad/wp/16/exp16-clone.js`, `www/clone.html`, `www/clone-worker.js` — 3회
  - 사실 점검 재실행(같은 코드·같은 환경, 2026-10-04): 16-A 모드당 5회, 16-B 3회 — `scratchpad/wp/fc-16/out16-lt.txt`·`out16-clone.txt`. 결정적 출력(에러 문구·`byteLength`)은 일치, 시간은 위 범위 안팎
