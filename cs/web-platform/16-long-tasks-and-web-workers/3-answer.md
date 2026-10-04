# web-platform/16-long-tasks-and-web-workers — 정답

## 정답

### 1. 한 줄 메인 스레드

- 메인 스레드는 JS·이벤트 처리·렌더링을 한 줄로 처리하고, 태스크 도중에 끊기지 않는다.
- 내 클릭: 핸들러가 300ms → **processing**이 길다.
- 그 사이 들어온 다른 클릭: 앞 태스크가 끝나기를 기다림 → **input delay**가 길다.
- 핸들러 뒤 큰 DOM 갱신이 있으면 → **presentation delay**도 커진다.

### 2. 세 방식 비교 (실험, headless Chrome 151, 스로틀 없음, 5회 + 사실 점검 재실행 5회)

| 방식 | `go` 상호작용 | 60ms 뒤 `other`의 input delay | 긴 태스크 |
|---|---|---|---|
| ① 한 덩어리 | 312ms | 242~246ms | 1개(301~306ms) |
| ② 30ms × 10 + yield | 16ms 이하 | 8~10ms(진행 중이던 조각이 끝나기를 기다린 만큼) 또는 항목 없음 | 0개 |
| ③ 워커 | 16ms 이하 | 대개 항목 없음(16ms 미만), 재실행 1회에서 2ms | 0개 |

- 결과가 화면에 나올 때까지의 총 시간은 셋 다 300ms 이상이다. 처방은 입력이 끼어들 자리를 만든다.

### 3. 기준값

- 긴 태스크: 50ms 초과(web.dev "Optimize long tasks").
- INP: 200ms 이하 좋음, 200 초과~500 이하 개선 필요, 500 초과 나쁨.
- 한 페이지 뷰에서는 가장 느린 상호작용(50번당 최고 1개 제외)을 쓰고, 사용자 페이지 뷰의 75번째 백분위로 판정한다(web.dev INP).

### 4. `yield` vs `setTimeout 0`

- `scheduler.yield()`: 이어지는 코드가 우선순위 높은 이어가기로 예약된다. 입력 등 밀린 일이 먼저 돌 기회를 얻은 뒤, 새로 쌓인 일반 태스크보다 먼저 이어 간다.
- `setTimeout(r, 0)`: 태스크 큐 맨 뒤로 간다. 다른 스크립트의 태스크가 먼저 끼어들 수 있다.
- 매 반복 양보 대신 **마감 기반 묶음**: 50ms 같은 마감이 지났을 때만 양보한다(같은 문서).

### 5. 복제 vs 이전 (실험, 3회)

| 보낸 것 | 메인 스레드 `postMessage` 시간 | 보낸 뒤 원본 |
|---|---|---|
| 32MB `Float64Array` 복제 | 40~49ms | `byteLength` 32000000 그대로 |
| 32MB 이전(`[a.buffer]`) | 0.1~0.3ms | `byteLength` 0(detached) |
| 객체 20만 개 배열 복제 | 240~305ms | 그대로 |

- 구조적 복제는 보내는 스레드에서 동기로 일어나고 비용이 데이터 크기·객체 수에 비례한다. 이전은 소유권만 넘긴다.

### 6. 워커인데 굳는다

- Performance 패널에서 `postMessage` 호출과 `message` 이벤트 처리 구간이 긴 태스크인지 본다(직렬화·역직렬화).
- 원인: 큰 객체 그래프를 왕복 복제.
- 대처: 워커가 데이터를 소유(워커에서 fetch·파싱)하고 요약만 보낸다. 숫자 데이터는 TypedArray + Transferable. 보낸 뒤 원본을 다시 쓰는 코드가 있으면 detach 때문에 깨지므로 함께 고친다.

### 7. 워커 안 DOM과 함수

- 워커 전역에는 DOM·`window`·`document`가 없다 → `ReferenceError: document is not defined`(실험 출력).
- 함수는 직렬화할 수 없다 → `DataCloneError: Failed to execute 'postMessage' on 'Worker': () => 1 could not be cloned.`(실험 출력). HTML 표준은 `IsCallable`이면 `DataCloneError`를 던지게 정한다.
- 대처: 워커는 계산만, DOM 갱신은 메인에서. 메시지는 데이터만.

### 8. 긴 태스크 0개인데 LoAF

- LoAF는 태스크가 아니라 **프레임** 단위다. 30ms 조각 둘이 한 프레임 안에서 연달아 돌면 그 프레임이 50ms를 넘는다(실험의 yield 판에서 55~65ms).
- 볼 곳: Event Timing의 presentation delay, LoAF의 `scripts`(어느 메인 스레드 스크립트가 붙잡았나 — 비어 있으면 렌더링 작업 의심), 양보 뒤 DOM 갱신 크기(17 가상화·18 재렌더), 서드파티 스크립트의 긴 태스크.

### 9. 연결

- 양보 = **협력적(비선점) 스케줄링**. 일하는 쪽이 스스로 CPU를 내놓는다(os/08, os/27의 "핸들러는 짧게").
- `postMessage` = 공유 메모리 없이 각자의 **메시지 큐**로 주고받는 액터 모양(기본형. 교차 출처 격리 시 `SharedArrayBuffer`+`Atomics`로 공유 메모리 모델도 쓸 수 있다). `scheduler.postTask` 우선순위는 우선순위 큐. Transferable은 소유권 이동(move).
