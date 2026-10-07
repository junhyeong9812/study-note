# language/14-concurrency-models — 정답

## 정답

### 1. 두 질문으로 모델 가르기

- 질문 ①: 기다리는 동안 "어디까지 했나"(상태)를 어디에 두나.
- 질문 ②: 누가, 언제 다른 일로 갈아 끼우나.

| 모델 | ① 상태 | ② 전환 |
|---|---|---|
| OS 스레드 | 스레드 자기 스택 | 커널 스케줄러, 아무 때나(선점) |
| async/await | 컴파일러가 만든 상태 기계 객체(힙) | 런타임, `await` 지점에서만(협력) |
| 가상 스레드(JDK 21) | 힙에 옮겨 둔 스택 조각(stack chunk) | JDK 스케줄러, 블로킹 API 호출 시 언마운트 |
| 액터 | 액터 상태 + 메일박스 큐 | 디스패처, 메시지 하나 단위 |

### 2. async 함수의 상태 기계

```text
  상태 객체 { state, id, u, o }   ← 힙
  state 0: db.user(id) 시작 → 루프로 반환
  state 1: u 저장 → db.orders(u) 시작 → 반환
  state 2: o 저장 → render(u, o) → 완료
```

- `u`는 스택이 아니라 상태 객체의 필드에 있다. 함수는 `await`에서 멈출 때마다 반환하므로 스택 프레임이 사라진다(JS는 매 `await`마다, C#·Rust는 기다리는 작업이 아직 안 끝났을 때만 멈춘다).
- 스택을 보존하지 않고 필요한 지역 변수만 객체에 옮기므로 *stackless coroutine*이다. 가상 스레드처럼 스택을 통째로 보존하는 방식은 stackful이다.

### 3. 플랫폼 풀 vs 가상 스레드

- (a) 풀 200: 10,000 / 200 × 0.1초 ≈ 5초. 실험: 5,083·5,086ms(재실행 5,088ms).
- (b) 가상 스레드: 모두 동시에 잠든다 → 약 0.1초 + 생성·스케줄 비용. 실험: 507·569ms(재실행 500ms).
- 100ms 계산이면 둘 다 코어 2개가 상한이다. 10,000 × 0.1초 / 2 ≈ 500초 근처가 되고 모델 차이는 사라진다. JEP 444: 가상 스레드는 "더 빠른 스레드가 아니다"(계산 쪽은 실험하지 않은 계산값이다).

### 4. `synchronized` vs `ReentrantLock` 안의 sleep (JDK 21, 캐리어 2)

- `synchronized`: 약 5초(실험 5,029~5,058ms). `ReentrantLock`: 약 0.12~0.14초(121~143ms, 재실행 포함).
- 락마다 새 객체라 경합은 없다. 차이는 **언마운트 가능 여부**다.
  - `synchronized` 안에서 블로킹하면 가상 스레드가 캐리어에 고정(pinning)된다. 캐리어 2개가 하나씩 잠들어 100 × 0.1 / 2 = 5초.
  - `ReentrantLock`은 블로킹 시 언마운트되어 100개가 동시에 잔다.
- `-Djdk.tracePinnedThreads=short`가 `reason:MONITOR`와 `<== monitors:1`을 출력했다.

### 5. pinning의 경계

- JEP 444의 두 경우: `synchronized` 블록·메서드 안에서 실행 중일 때, 네이티브 메서드·외부 함수를 실행 중일 때.
- JEP 491(JDK 24)은 `synchronized` 쪽을 거의 모두 없앴다(기본 잠금 모드 기준 — 기본이 아닌 `LM_LEGACY` 모드는 제외). 네이티브 프레임 위의 블로킹은 남는다.
- 파일 I/O·`Object.wait()`처럼 언마운트를 못 하는 일부 블로킹은 스케줄러가 병렬도를 잠시 늘려 보상한다. 상한은 `jdk.virtualThreadScheduler.maxPoolSize`(JEP 444).

### 6. async 안의 동기 계산 (node 22)

- `pbkdf2Sync`: 타이머 최대 지연 ≈ handler 시간(실험 171·173ms, 재실행 156·166ms).
- `await pbkdf2Async(...)`(콜백판 `pbkdf2`를 Promise로 감싼 것): 최대 지연 1~4ms(재실행 1·2ms).
- `async` 표시는 전환 지점을 만들지 않는다. 전환은 `await`에서만 일어난다.
  - `pbkdf2Sync`는 루프 스레드에서 계산하므로 그동안 타이머 콜백이 실행되지 못한다.
  - 콜백판 `pbkdf2`는 계산을 libuv 스레드 풀로 보내고 루프는 계속 돈다.

### 7. 아무도 안 받는 채널

- 무버퍼: 1,001개(송신 고루틴 1,000개 + `main`). 받는 쪽이 와야 송신이 끝나는데 호출자가 떠났다.
- 버퍼 1: 1개(`main`만). 받는 쪽 없이도 한 번은 보내고 고루틴이 끝난다.
- 근거: Go 명세 Channel types — 무버퍼 채널은 송신자·수신자가 모두 준비됐을 때만 통신이 성립한다.

### 8. CSP vs 액터

| | CSP(Go 채널) | 액터 |
|---|---|---|
| 보내는 곳 | 채널(통로). 누가 받는지는 모른다 | 받는 액터의 주소(메일박스) |
| 송신이 막히나 | 무버퍼는 수신자가 올 때까지, 버퍼는 찰 때까지 막힌다 | 보통 막히지 않는다(비동기, 메일박스에 쌓인다) |
| 대신 생기는 장애 | 아무도 안 받는 송신·수신 → 고루틴 누수·교착 | 소비가 느린 액터의 메일박스 무한 증가 → 메모리 증가 |

- 둘 다 상태의 소유자를 하나로 모아 데이터 레이스를 구조적으로 줄인다.
- 서지: Hoare, CACM 21(8):666–677, 1978(Crossref 확인, 본문 미열람).

### 9. 가상 스레드인데 처리량이 낮다

- 의심 1: pinning(JDK 21~23). 블로킹 I/O를 감싼 `synchronized`(직접 코드나 드라이버·풀 라이브러리).
  - 확인: `-Djdk.tracePinnedThreads=short`의 `reason:MONITOR` 스택, JFR `jdk.VirtualThreadPinned`(기본 켜짐, 20ms 문턱), 스레드 덤프에서 캐리어 `ForkJoinPool-1-worker-*` 전부가 `synchronized` 안 블로킹.
  - 대처: `ReentrantLock`으로 교체, 라이브러리 갱신, JDK 24+.
- 의심 2: 하류 풀 고갈. 풀 대기 타임아웃 로그가 같이 늘면 이쪽이다 → 세마포어로 동시성 제한([reliability/39](../../reliability/39-async-io-gains-and-limits/2-summary.md)).
- 의심 3: 작업이 사실 CPU 위주. CPU가 놀고 있다면 이 가설은 약하다.

### 10. 모든 API의 p99가 동시에

- 가설: 무거워진 API가 이벤트 루프 스레드에서 동기 계산·블로킹을 한다. 협력적 전환이라 그동안 다른 요청 콜백이 못 돈다.
- 확인
  - `perf_hooks.monitorEventLoopDelay`의 p99·max가 요청 지연과 같이 뛰는지(실험: 200ms 바쁜 루프 → `max ms 211 p99 ms 211`).
  - CPU 프로파일에서 루프 스레드가 `*Sync` 함수·큰 `JSON.parse`·정규식 안에 있는지.
- 대처: 비동기 API로 교체, `worker_threads`나 별도 서비스로 계산 분리, 입력 크기 제한. 정규식이면 백트래킹 패턴 제거([language/02](../02-lexing-and-regular-languages/2-summary.md)).
