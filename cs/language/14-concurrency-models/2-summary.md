# language/14-concurrency-models — 동시성 모델: 스레드·이벤트 루프·async/await·가상 스레드·CSP·액터 — 정리 (힌트)

## 해결하는 문제

서버는 "동시에 많이 기다리는" 일을 한다.

```text
  요청 10,000개가 각각 DB 응답을 100ms 기다린다 (예시)

  요청당 OS 스레드 1개      → 스레드 10,000개. 대부분 잠들어 있는데 스택 메모리·스케줄링 비용은 낸다
  OS 스레드 200개 풀        → 동시에 200개만 처리. 나머지는 줄 선다 → 10,000 / 200 × 0.1s ≈ 5초
  기다리는 동안 스레드를 놓는다 → 같은 OS 스레드 몇 개로 10,000개를 동시에 기다린다
```

- *동시성(concurrency)*: 여러 일이 **겹친 시간 동안 진행 중**인 것. 한 코어에서 번갈아 해도 동시성이다.
- *병렬성(parallelism)*: 여러 일이 **같은 순간에** 실행되는 것. 코어가 여러 개 있어야 한다.
  - 흔한 오해: 동시성 모델을 바꾸면 계산이 빨라진다. JEP 444는 가상 스레드가 "더 빠른 스레드가 아니다", 규모(처리량)를 위한 것이라고 적는다.

모든 동시성 모델은 두 질문에 다르게 답한다.

1. **기다리는 동안 "어디까지 했나"를 어디에 두나?** (스택? 힙의 객체? 메일박스?)
2. **누가, 언제 다른 일로 갈아 끼우나?** (커널이 아무 때나? 코드가 `await`에서만?)

쉬운 예: 식당.
- 테이블마다 종업원 한 명(스레드). 손님이 메뉴를 고르는 동안 종업원은 서서 기다린다.
- 종업원 한 명이 수첩에 "3번 테이블: 주문 받음, 음식 대기"를 적고 돌아다닌다(이벤트 루프 + 상태 기계).
- 주방과 홀이 창구로만 주문서를 주고받는다(CSP 채널).
- 요리사마다 자기 주문함이 있고, 주문함에 쪽지를 넣어서만 일을 시킨다(액터).

똑같은 구조다.\
수첩에 적는 방식이면 종업원은 적지만, **한 테이블에서 오래 서 있으면 다른 모든 테이블이 멈춘다.**

실무 예:
- Node·Netty 이벤트 루프 안에서 동기 암호화·JSON 파싱·JDBC 호출 → 그 루프가 맡은 요청이 모두 같이 느려진다(Node는 루프가 하나라 전부, Netty는 막힌 루프에 배정된 채널들).
- JDK 21 가상 스레드가 `synchronized` 안에서 블로킹 → 캐리어 스레드가 묶여 처리량이 플랫폼 스레드 수준으로 떨어진다.
- Go에서 타임아웃으로 먼저 떠난 호출자 때문에 결과를 못 보낸 고루틴이 쌓인다.

## 동작·원리

### 1. 모델 한눈에 — "상태를 어디에, 전환은 누가"

```text
  모델                   기다리는 동안의 상태            전환하는 주체·시점
  ───────────────────── ───────────────────────────── ────────────────────────────────
  OS 스레드(플랫폼)       스레드 자기 스택(OS가 할당)        커널 스케줄러, 아무 때나(선점)
  이벤트 루프 + 콜백      클로저·힙 객체(손으로 관리)        루프, 콜백이 끝났을 때만(협력)
  async/await           컴파일러가 만든 상태 기계 객체      런타임, await 지점에서만(협력)
  가상 스레드(JDK 21)     힙에 옮겨 둔 스택 조각            JDK 스케줄러, 블로킹 API 호출 시
  고루틴(Go)             고루틴 스택(런타임 관리)          Go 런타임. 1.14부터 비동기 선점도
  액터                   액터 객체 상태 + 메일박스 큐       런타임 디스패처, 메시지 하나 단위
```

- *선점(preemptive)*: 실행 중인 흐름을 바깥(커널·런타임)이 강제로 멈추고 갈아 끼운다.
- *협력(cooperative)*: 흐름이 스스로 양보하는 지점(`await`, 콜백 반환)에서만 바뀐다.
  - 흔한 오해: async 코드는 "알아서" 다른 요청에 양보한다. 양보는 `await`에서만 일어난다. 그 사이의 동기 코드는 끝날 때까지 루프를 쥔다(실험 3).
- Go 1.14 릴리스 노트: "Goroutines are now asynchronously preemptible." 그 전에는 함수 호출 없는 루프가 스케줄러를 막을 수 있었다.
- OS 스레드 자체의 비용(스택·컨텍스트 스위칭)은 [os/07](../../os/07-threads-and-context-switch/2-summary.md), 이벤트 루프·리액터의 구조는 [os/27](../../os/27-event-based-concurrency/2-summary.md)이 다룬다. 이 노트는 **언어가 그 위에 얹는 모델**을 본다.

### 2. async/await — 컴파일러가 함수를 상태 기계로 바꾼다

```text
  async function handler(id) {          컴파일러·런타임이 만드는 것(개념도)
    const u = await db.user(id);        ┌───────────────────────────────┐
    const o = await db.orders(u);       │ 상태 객체 { state, id, u, o }  │ ← 힙에 있다
    return render(u, o);                └───────────────────────────────┘
  }                                      state 0: db.user(id) 시작 → 반환(루프로 돌아감)
                                         state 1: u 받음 → db.orders(u) 시작 → 반환
                                         state 2: o 받음 → render → 완료
```

- `await`마다 함수가 **둘로 잘린다.** 잘린 뒤쪽(나머지 일)을 *continuation*이라 한다.
  - 실행 중 실제로 멈추는지는 언어마다 다르다. JS는 이미 끝난 값을 `await`해도 일단 멈추고 마이크로태스크로 재개한다(ECMAScript `Await` 추상 연산). C#·Rust는 기다리는 작업이 이미 끝났으면 멈추지 않고 그대로 진행한다.
  - *continuation*: "이 일이 끝나면 이어서 할 나머지 계산".
- 지역 변수(`u`, `o`)는 스택이 아니라 상태 객체의 필드로 살아남는다. 그래서 스택이 없는 코루틴, *stackless coroutine*이라 부른다.
- Rust는 이 변환을 컴파일 시점에 `Future` 상태 기계로 한다([languages/rust/syntax/54](../../../languages/rust/syntax/54-async-await-and-future-state-machines/2-summary.md)). JS(V8)·C#·Kotlin도 같은 생각이다(구현 세부는 언어마다 다르다).
- 대가: **색깔 문제.** `await`는 async 함수 안에서만 쓸 수 있다(JS는 ES 모듈 최상위도 허용). 동기 함수가 async 함수를 기다리려면 자기도 async가 되어야 해서 호출 사슬 전체로 번진다(해석 — 흔히 "function coloring"이라 부른다).

### 3. 가상 스레드 — 스택을 힙에 떼어 두는 스레드 (JDK 21, JEP 444)

```text
  가상 스레드 VT1..VTn (힙의 객체)          캐리어 = 플랫폼 스레드 (기본 = 사용 가능한 CPU 수)
                                          ┌──────────┐   ┌──────────┐
  VT1: sleep/소켓 읽기 → 언마운트 ───┐       │ carrier1 │   │ carrier2 │
       (스택 프레임을 힙으로 복사)    │       └────▲─────┘   └────▲─────┘
  VT2: 준비됨 ──────────────────────┼─────── 마운트 ┘              │
  VT3: 준비됨 ──────────────────────┴────────────────── 마운트 ────┘

  pinning: VT가 synchronized 안이나 네이티브 프레임 위에서 블로킹
           → 언마운트 못 함 → 캐리어가 같이 잠든다
```

- *가상 스레드*: JDK가 만드는 `java.lang.Thread`. 블로킹 API를 만나면 스택을 힙(stack chunk 객체)으로 옮기고 캐리어를 놓는다(JEP 444 "Memory use and interaction with garbage collection").
  - 코드 모양은 평범한 블로킹 코드 그대로다. async/await와 달리 **색깔이 없다.**
  - 스택을 통째로 보존하므로 *stackful* 방식이다.
- *캐리어(carrier)*: 가상 스레드를 실제로 실행하는 플랫폼 스레드.
- JEP 444가 적는 스케줄러
  - work-stealing `ForkJoinPool`을 FIFO 모드로 쓴다. 병렬 스트림이 쓰는 공용 풀(LIFO)과 다른 풀이다.
  - 병렬도(캐리어 수) 기본값 = 사용 가능한 프로세서 수. `jdk.virtualThreadScheduler.parallelism`으로 바꾼다.
- *pinning(고정)*: JEP 444는 두 경우를 든다. `synchronized` 블록·메서드 안에서 실행 중일 때, 네이티브 메서드·외부 함수를 실행 중일 때.
  - "정확성을 해치지는 않지만 확장성을 해칠 수 있다"(JEP 444).
  - 파일 I/O·`Object.wait()`처럼 언마운트를 못 하는 일부 블로킹은 스케줄러 병렬도를 잠시 늘려 보상한다. 최대치는 `jdk.virtualThreadScheduler.maxPoolSize`(JEP 444).
  - JDK 24의 JEP 491이 `synchronized` 안 블로킹의 pinning을 "거의 모든 경우" 없앴다. 이 노트의 실험 2 같은 붕괴는 **JDK 21~23**에서 난다(JDK 24 이후도 기본이 아닌 `LM_LEGACY` 잠금 모드에서는 고쳐지지 않았다 — JEP 491 구현 PR 설명).
- 가상 스레드 문법·사용 패턴은 [languages/java/syntax/56](../../../languages/java/syntax/56-virtual-threads/2-summary.md)이 다룬다.

### 4. CSP와 액터 — 공유하지 말고 메시지로

```text
  CSP (Go 채널)                                  액터 (Erlang·Akka 계열)
  ┌────┐   ch (이름 없는 통로)    ┌────┐          ┌──────────┐  메시지  ┌──────────────────┐
  │ G1 │ ── ch <- v ──▶ ▣ ──▶ ──│ G2 │          │ 보내는 쪽 │ ───────▶ │ 메일박스 ▣▣▣ → 액터 │
  └────┘   무버퍼: 둘이 만나야 성립 └────┘          └──────────┘  (비동기) └──────────────────┘
           버퍼: 찰 때까지만 안 막힘                 받는 쪽 "주소"로 보낸다. 한 번에 메시지 하나 처리
```

- *CSP(Communicating Sequential Processes)*: Hoare, "Communicating sequential processes", Communications of the ACM 21(8):666–677, 1978(서지는 Crossref로 확인, 본문 미열람). 순차 프로세스들이 **통신으로만** 협력한다는 모델.
  - Go 명세: 용량이 0이거나 없으면 무버퍼 채널이고 "송신자와 수신자가 모두 준비됐을 때만" 통신이 성립한다. 버퍼 채널은 버퍼가 차지 않았으면 송신이 막히지 않는다.
  - Effective Go의 구호: "Do not communicate by sharing memory; instead, share memory by communicating." 같은 글이 "지나치게 밀어붙일 수 있다"며 참조 카운트는 뮤텍스가 나을 수 있다고도 적는다.
- *액터(actor)*: 각 액터가 자기 상태와 메일박스를 갖는다. 다른 액터의 상태는 직접 못 만지고 메시지만 보낸다.
  - 액터 하나는 메시지를 하나씩 처리한다. 그래서 액터 **안에서는** 락이 필요 없다.
  - 감독 트리·Let It Crash 같은 장애 처리 쪽은 [reliability/49](../../reliability/49-steady-state-fail-fast-and-supervision/2-summary.md)가 다룬다.
- 둘 다 데이터 레이스를 **구조로** 줄인다. 대신 교착·누수가 "메시지를 영원히 기다리는" 모양으로 바뀐다(실험 4).

### 실험 1: 블로킹 10,000개 — 플랫폼 스레드 풀 vs 가상 스레드

```java
// Java 21. 작업마다 Thread.sleep(100) — I/O 대기를 흉내 낸다
Runnable sleep100 = () -> { try { Thread.sleep(100); } catch (InterruptedException e) { } };
try (var ex = Executors.newFixedThreadPool(200))          { for (int i = 0; i < 10_000; i++) ex.submit(sleep100); }
try (var ex = Executors.newVirtualThreadPerTaskExecutor()) { for (int i = 0; i < 10_000; i++) ex.submit(sleep100); }
// try-with-resources의 close()가 모든 작업 완료를 기다린다
```

환경: i7-13700HX 호스트, `eclipse-temurin:21-jdk`(21.0.12) 컨테이너, `--cpus=2`, 2회(+ 사실 점검 재실행 1회).

```text
  platform pool(200) + sleep 100ms   n=10000    5083 ms / 5086 ms   (재실행 5088 ms)
  virtual per task + sleep 100ms     n=10000     507 ms /  569 ms   (재실행  500 ms)
```

- 풀 200개는 이론값 10,000 / 200 × 0.1초 = 5초와 맞는다.
- 가상 스레드는 10,000개가 동시에 잠들어 약 0.5초다. 100ms 대기 위에 가상 스레드 1만 개 생성·스케줄 비용이 얹혔다(해석).
- 작업이 `sleep`이 아니라 계산이었다면 둘 다 코어 2개를 넘지 못한다(JEP 444 "not faster threads").

### 실험 2: JDK 21의 pinning — `synchronized` 안에서 잠들기

```java
// 작업마다 새 락 객체 → 경합은 없다. 차이는 "락 종류"뿐이다
() -> { Object lock = new Object();
        synchronized (lock) { Thread.sleep(100); } }                  // vsync
() -> { Lock lock = new ReentrantLock(); lock.lock();
        try { Thread.sleep(100); } finally { lock.unlock(); } }       // vlock
```

환경: 위와 같음, 가상 스레드 100개, 캐리어 2개(`--cpus=2`의 기본 병렬도. `-Djdk.virtualThreadScheduler.parallelism=2 -Djdk.virtualThreadScheduler.maxPoolSize=2`를 명시한 실행도 같은 값).

```text
  virtual + synchronized{sleep}      n=  100    5032 ms / 5029 ms / 5058 ms   (재실행 5053 / 5031 ms)
  virtual + ReentrantLock{sleep}     n=  100     122 ms /  121 ms /  123 ms   (재실행  143 /  128 ms)

  -Djdk.tracePinnedThreads=short 출력
  VirtualThread[#19]/runnable@ForkJoinPool-1-worker-1 reason:MONITOR
      VtThroughput.lambda$main$1(VtThroughput.java:22) <== monitors:1
```

- 5,032ms ≈ 100 × 0.1초 / 2. 캐리어 2개가 각각 하나씩 잠들어 **2개씩만** 진행됐다.
- `ReentrantLock`은 블로킹 시 언마운트되어 100개가 거의 동시에 잔다.
- `reason:MONITOR`·`<== monitors:1`이 `synchronized`(모니터)가 원인이라는 표시다.

### 실험 3: async 함수 안의 동기 블로킹 (node 22)

```js
// 10ms마다 울려야 하는 타이머 = "다른 요청"의 대리. handler 실행 중 최대 지연을 잰다
const pbkdf2Async = promisify(pbkdf2);   // node:util의 promisify로 콜백판 pbkdf2를 Promise로 감싼다
async function handler() {
  if (mode === 'sync') pbkdf2Sync('pw', 'salt', 300_000, 32, 'sha256');          // 루프 스레드에서 계산
  else await pbkdf2Async('pw', 'salt', 300_000, 32, 'sha256');                     // libuv 스레드 풀로 넘김
}
```

환경: `node:22-alpine`(v22.23.2), `--cpus=2`, 2회 + 사실 점검 재실행 2회.

```text
  sync  handler 171ms, 10ms 타이머 최대 지연 171ms   /  173ms, 173ms   (재실행 156·156ms / 166·166ms)
  async handler 172ms, 10ms 타이머 최대 지연   4ms   /  163ms,   1ms   (재실행 160·1ms / 158·2ms)
```

- 두 경우 모두 handler는 `async`이고 걸린 시간도 비슷하다(4회 모두 약 155~175ms).
- `sync`는 그 시간 동안 타이머가 한 번도 못 울렸다. 이벤트 루프 스레드가 계산을 쥐고 있었다.
- `async`는 계산을 libuv 스레드 풀로 보냈다. 루프는 그동안 타이머를 처리했다.

### 실험 4: CSP의 누수 — 아무도 안 받는 채널에 보내기 (Go 1.23)

```go
func call(buffered bool) {
    ch := make(chan int)              // buffered면 make(chan int, 1)
    go func() { time.Sleep(20 * time.Millisecond); ch <- 42 }()   // 느린 하류
    select {
    case <-ch:
    case <-time.After(5 * time.Millisecond):   // 호출자 타임아웃 → ch를 더는 안 받는다
    }
}
```

환경: `golang:1.23-alpine`(go1.23.12), `--cpus=2`, 1,000번 호출 뒤 100ms 기다리고 `runtime.NumGoroutine()`.

```text
  buffered=false 1000번 호출 뒤 남은 고루틴 1001
  buffered=true  1000번 호출 뒤 남은 고루틴 1
```

- 무버퍼 채널은 받는 쪽이 와야 송신이 끝난다. 호출자가 떠났으니 송신 고루틴 1,000개가 `ch <- 42`에서 영원히 멈췄다(+1은 `main`).
- 버퍼 1이면 받는 쪽 없이도 한 번은 보내고 끝난다. 채널은 쓰레기가 되어 수거된다.

## 쓰이는 자료구조·알고리즘

- **상태 기계로 변환된 Future** — `state` 정수 + 살아남아야 할 지역 변수 필드. `await` 하나가 상태 전이 하나다. 이벤트 루프의 콜백 상태 관리와 같은 일을 컴파일러가 대신한다([os/27](../../os/27-event-based-concurrency/2-summary.md)).
- **채널 큐** — 버퍼 채널 = 유계 FIFO(원형 버퍼) + 송신·수신 대기자 큐. 무버퍼 채널은 버퍼 0인 랑데부다. [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md) · [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **work-stealing 덱** — 가상 스레드 스케줄러(`ForkJoinPool`)는 캐리어마다 작업 덱을 두고, 빈 캐리어가 남의 덱에서 훔친다. [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md)
- **메일박스 = 다중 생산자·단일 소비자(MPSC) 큐** — 여러 액터가 넣고, 주인 액터 하나만 꺼낸다.
- **타이머 힙** — `time.After`, `setTimeout`, `Thread.sleep`의 깨우기 시각 관리([os/27](../../os/27-event-based-concurrency/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 먼저 "무엇을 기다리나"를 적는다

```text
  CPU 계산이 대부분           → 코어 수만큼의 스레드(또는 프로세스). 모델을 바꿔도 이득 없음
  I/O 대기 + 동시성 수천 이상   → 가상 스레드(JDK 21+), async/await, 고루틴
  공유 상태가 복잡하고 경합 큼   → 액터·채널로 소유권을 한 곳에 모은다
  이벤트 루프 런타임(Node·Netty) → 루프에서는 기다리지도 오래 계산하지도 않는다. 무거운 일은 넘긴다
```

- 동시성을 늘리면 병목이 하류(DB 풀)로 옮겨 간다. 그 계산은 [reliability/39](../../reliability/39-async-io-gains-and-limits/2-summary.md)와 [math/10](../../math/10-queueing-and-littles-law/2-summary.md)(Little's law).

### 2. Java 21 — 가상 스레드로 옮길 때

```java
// 1) 풀이 아니라 작업마다 가상 스레드. 풀링하지 않는다(JEP 444 "Do not pool virtual threads")
try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
    // 2) 하류 자원 제한은 스레드 수가 아니라 세마포어로
    Semaphore dbPermits = new Semaphore(20);
    ex.submit(() -> {
        dbPermits.acquire();
        try { return repo.find(id); } finally { dbPermits.release(); }
    });
}
// 3) JDK 21~23: 블로킹을 감싸는 synchronized는 ReentrantLock으로
private final ReentrantLock lock = new ReentrantLock();
```

```bash
# pinning 찾기 (JDK 21)
java -Djdk.tracePinnedThreads=short -jar app.jar     # 고정된 채 블로킹한 스택을 출력
# JFR 이벤트 jdk.VirtualThreadPinned — 기본 켜짐, 문턱 20ms (JEP 444)
jcmd <pid> Thread.dump_to_file -format=json /tmp/threads.json   # 가상 스레드까지 포함한 덤프(JEP 444)
```

### 3. Node — 루프를 막는 코드를 찾는다

```js
import { monitorEventLoopDelay } from 'node:perf_hooks';
const h = monitorEventLoopDelay({ resolution: 10 }); h.enable();
setInterval(() => console.log('loop delay p99(ms)', h.percentile(99) / 1e6), 10_000);
```

- 같은 컨테이너(node 22)에서 200ms 바쁜 루프를 넣었더니 `max ms 211 p99 ms 211`이 나왔다.
- 막는 코드는 `*Sync` API, 큰 JSON 파싱, 정규식 백트래킹([language/02](../02-lexing-and-regular-languages/2-summary.md)) 순으로 의심한다. 무거운 계산은 `worker_threads`나 별도 서비스로 보낸다.

### 4. Go — 고루틴 누수를 찾는다

- `runtime.NumGoroutine()`(현재 존재하는 고루틴 수)을 지표로 내보낸다. 부하가 그대로인데 계속 오르면 누수를 의심하고 아래 프로파일로 확인한다.
- `net/http/pprof`의 goroutine 프로파일에서 같은 `chan send`·`chan receive` 줄에 멈춘 고루틴이 수천 개인지 본다.
- 결과 채널은 버퍼 1로 만들거나, `context`로 송신 쪽도 취소를 듣게 한다([reliability/09](../../reliability/09-cancellation-propagation/2-summary.md)).

## 장애 시나리오와 대처

### 1. async 안의 블로킹 호출 → 런타임 전체 정지

- **현상**: 특정 API 하나가 무거워졌는데 **모든** 요청의 지연이 동시에 뛴다. CPU는 코어 하나만 100%.
- **보이는 형태**: 이벤트 루프 지연 지표(p99) 급등, 헬스 체크 타임아웃. 프로파일에서 루프 스레드가 `pbkdf2Sync`·`JSON.parse`·JDBC 드라이버 안에 있다.
- **원인**: 협력적 전환은 `await`(콜백 반환)에서만 일어난다. 동기 코드가 도는 동안 같은 루프의 다른 일은 못 돈다(실험 3).
- **대처**: 비동기 API로 바꾸거나 별도 스레드 풀·워커로 넘긴다. Netty는 블로킹 작업을 별도 `EventExecutorGroup`으로 보낸다([os/27](../../os/27-event-based-concurrency/2-summary.md)).

### 2. 가상 스레드 `synchronized` pinning → 캐리어 고갈 (JDK 21~23)

- **현상**: 가상 스레드로 바꿨는데 처리량이 오히려 풀 시절보다 낮다. CPU는 놀고 있다.
- **보이는 형태**: `-Djdk.tracePinnedThreads`에 `reason:MONITOR`, JFR `jdk.VirtualThreadPinned`. 스레드 덤프에서 `ForkJoinPool-1-worker-*`가 모두 `synchronized` 안의 블로킹 호출에 있다.
- **원인**: `synchronized` 안에서 블로킹하면 언마운트가 안 되어 캐리어(기본 CPU 수만큼)가 같이 잠든다(실험 2: 100ms 작업 100개가 5초).
- **대처**: 블로킹을 감싼 `synchronized`를 `ReentrantLock`으로 바꾼다. 라이브러리(JDBC 드라이버·커넥션 풀) 버전을 확인한다. JDK 24+(JEP 491)로 올리면 이 경우는 대부분 사라진다. 네이티브 호출 중 블로킹은 JEP 491 뒤에도 고정된다.

### 3. 가상 스레드로 동시성 10배 → 하류 커넥션 풀 고갈

- **현상**: 전환 뒤 `Connection is not available, request timed out` 같은 풀 대기 타임아웃이 는다.
- **원인**: 가상 스레드는 동시 요청을 늘릴 뿐 DB 처리량은 그대로다. 대기가 앱 스레드에서 풀 대기로 옮겨 간다.
- **대처**: 세마포어로 하류 동시성을 제한하고, 풀 크기는 DB가 감당할 만큼만. 자세한 계산은 [reliability/39](../../reliability/39-async-io-gains-and-limits/2-summary.md)·[os/36](../../os/36-server-concurrency-architectures/2-summary.md).

### 4. 고루틴 누수 — 아무도 안 받는 채널

- **현상**: 메모리와 고루틴 수가 배포 뒤 계속 오르다가 OOM으로 재시작된다.
- **보이는 형태**: `runtime.NumGoroutine()` 우상향. goroutine 프로파일에 같은 `chan send` 위치가 수천 개.
- **원인**: 호출자가 타임아웃으로 떠난 뒤, 결과를 보내려던 고루틴이 무버퍼 채널 송신에서 영원히 멈춘다(실험 4: 1,000번 호출에 1,000개 잔류).
- **대처**: 결과 채널 버퍼 1, `select`에 `ctx.Done()` 추가, 고루틴을 만든 쪽이 끝까지 책임진다(구조적 동시성 — Java는 `StructuredTaskScope`, JDK 21에서는 preview).

### 5. 액터 메일박스 무한 증가

- **현상**: 특정 액터가 느려지자 힙이 계속 커진다. 처리 지연이 분 단위로 늘어난다.
- **원인**: 메시지 송신은 비동기라 보내는 쪽이 막히지 않는다. 소비가 생산보다 느리면 메일박스(무한 큐)가 쌓인다(해석 — 무한 큐 스레드풀 OOM과 같은 모양, [language/16](../16-concurrency-design-patterns/2-summary.md)).
- **대처**: 유계 메일박스·배압, 느린 액터를 여러 개로 나누기, 메일박스 길이를 지표로 노출.

## 핵심 문장

- 동시성 모델의 차이는 "기다리는 동안의 상태를 어디에 두나"와 "누가 언제 갈아 끼우나" 두 가지다.
- async/await는 함수를 `await` 지점에서 잘라 상태 기계로 만든다. 전환은 `await`에서만 일어나므로 그 사이의 동기 블로킹은 루프 전체를 멈춘다.
- 가상 스레드는 블로킹 지점에서 스택을 힙으로 옮기고 캐리어를 놓는다. JDK 21~23에서는 `synchronized`·네이티브 프레임 안에서는 놓지 못한다(pinning).
- 가상 스레드·async는 처리량(규모)을 늘리지 계산 속도를 늘리지 않는다. 계산 위주 작업은 코어 수가 상한이다.
- CSP·액터는 공유 메모리 대신 메시지로 소유권을 옮겨 레이스를 줄인다. 대신 "아무도 받지 않는 메시지"가 누수·정지의 새 모양이 된다.

## 관련 주제·근거

- 선행
  - [os/27-event-based-concurrency](../../os/27-event-based-concurrency/2-summary.md) — 이벤트 루프·리액터·콜백
  - [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md) — OS 스레드 비용, 1:1·M:N
- 후속·연결
  - [15-gil-and-runtime-constraints](../15-gil-and-runtime-constraints/2-summary.md) — 스레드를 늘려도 병렬이 안 되는 런타임 제약
  - [16-concurrency-design-patterns](../16-concurrency-design-patterns/2-summary.md)(스레드 풀·Future 합성·DCL) · [13-language-memory-model](../13-language-memory-model/2-summary.md)(happens-before)
  - [os/36-server-concurrency-architectures](../../os/36-server-concurrency-architectures/2-summary.md) · [os/25-io-models](../../os/25-io-models/2-summary.md) · [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)
  - [reliability/39-async-io-gains-and-limits](../../reliability/39-async-io-gains-and-limits/2-summary.md) · [reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md) · [reliability/49-steady-state-fail-fast-and-supervision](../../reliability/49-steady-state-fail-fast-and-supervision/2-summary.md)(액터 감독)
  - 연결 노트: [languages/java/syntax/56-virtual-threads](../../../languages/java/syntax/56-virtual-threads/2-summary.md) · [languages/rust/syntax/54](../../../languages/rust/syntax/54-async-await-and-future-state-machines/2-summary.md) · [languages/rust/syntax/55](../../../languages/rust/syntax/55-async-in-practice-runtime-send-and-pin/2-summary.md)
  - [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md) · [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md)
- 근거
  - JEP 444 "Virtual Threads"(JDK 21) — 스케줄러(FIFO `ForkJoinPool`, 병렬도 = 프로세서 수), pinning 두 경우와 보상, `jdk.tracePinnedThreads`, JFR `jdk.VirtualThreadPinned`(기본 켜짐·20ms), JSON 스레드 덤프, "not faster threads", 풀링 금지 <https://openjdk.org/jeps/444>
  - JEP 491 "Synchronize Virtual Threads without Pinning"(JDK 24) <https://openjdk.org/jeps/491>
  - JEP 491 구현 PR 설명(core-libs-dev 2024-11) — 기본 `LM_LIGHTWEIGHT`에서 고쳐지고 `LM_LEGACY`는 제외 <https://mail.openjdk.org/pipermail/core-libs-dev/2024-November/134177.html>
  - C# `await` 연산자(이미 완료된 작업은 중단 없이 결과 반환) <https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/await> · Rust Reference "Await expressions"(`Poll::Ready`면 그대로 진행) <https://doc.rust-lang.org/reference/expressions/await-expr.html> · ECMAScript 2024 §27.7.5.3 Await, §15.8 Note 1(모듈 최상위 `await`) · Netty `EventLoop` Javadoc(채널은 등록된 루프 하나가 처리) <https://netty.io/4.1/api/io/netty/channel/EventLoop.html>
  - C. A. R. Hoare, "Communicating sequential processes", CACM 21(8):666–677, 1978, doi:10.1145/359576.359585 — 서지는 Crossref, 본문 미열람
  - The Go Programming Language Specification — Channel types(무버퍼·버퍼 채널의 성립 조건) <https://go.dev/ref/spec> · Effective Go "Concurrency"(Share by communicating) <https://go.dev/doc/effective_go> · Go 1.14 Release Notes(비동기 선점) <https://go.dev/doc/go1.14>
  - Node.js `perf_hooks.monitorEventLoopDelay` <https://nodejs.org/api/perf_hooks.html>
- 실험 목록(모두 i7-13700HX 호스트의 일회용 컨테이너, `--cpus=2 --network none`)
  - 실험 1: `eclipse-temurin:21-jdk`(21.0.12) — 10,000개 `sleep(100)`, 고정 풀 200 vs 가상 스레드, 2회(+ 점검 재실행 1회)
  - 실험 2: 같은 이미지 — 가상 스레드 100개, `synchronized` vs `ReentrantLock` 안 `sleep(100)`, 캐리어 2, 3회(+ 점검 재실행 2회) + `-Djdk.tracePinnedThreads=short`
  - 실험 3: `node:22-alpine`(v22.23.2) — async handler 안 `pbkdf2Sync` vs `pbkdf2`(콜백), 10ms 타이머 최대 지연, 2회(+ 점검 재실행 2회) + `monitorEventLoopDelay` 1회
  - 실험 4: `golang:1.23-alpine`(go1.23.12) — 타임아웃 뒤 무버퍼/버퍼 채널 송신 고루틴 잔류 수
