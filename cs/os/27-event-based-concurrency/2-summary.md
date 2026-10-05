# os/27-event-based-concurrency — 스레드 없이 동시에: 이벤트 루프·리액터·콜백 — 정리 (힌트)

## 해결하는 문제

스레드로 동시성을 만들면 두 가지 값을 치른다.
- 공유 데이터마다 락이 필요하고, 락을 틀리면 경쟁 조건·교착이 난다(15~20번).
- 언제 어느 스레드가 도는지는 OS 스케줄러가 정한다. 앱은 그 순서를 통제하지 못한다.

OSTEP 33장은 이렇게 묻는다. **스레드 없이 동시 서버를 만들 수 있나?**\
답이 이벤트 기반 동시성이다.

```text
  while (1) {
      events = getEvents();       // 준비된 일 목록을 받는다 (epoll_wait, 26번)
      for (e in events)
          processEvent(e);        // 하나씩, 짧게 처리한다 (이벤트 핸들러)
  }
```

쉬운 예: 혼자 일하는 카페 직원이다.
- 주문을 받고, 커피 머신을 켜 두고(비동기 작업), 바로 다음 손님 주문을 받는다.
- 머신이 "완료" 소리를 내면 그 컵을 내준다.
- 직원이 우유를 사러 가게 밖으로 나가면(블로킹 호출) **줄 선 모든 손님**이 기다린다.

똑같은 구조다.\
이벤트 루프는 스레드 하나가 여러 연결을 "조금씩 번갈아" 처리한다.\
핸들러 하나가 오래 걸리면 그동안 다른 모든 연결이 멈춘다.

실무 예:
- Node.js, Redis, nginx 워커 하나, Netty 이벤트 루프 스레드 하나, 브라우저 메인 스레드가 이 구조다.
- "Node 서버에서 큰 JSON을 `JSON.parse`하는 순간 다른 요청이 전부 늦어졌다."
- "Redis에서 `KEYS *` 한 번에 모든 클라이언트가 멈췄다."

## 동작·원리

### 이벤트 루프 — 선택이 곧 스케줄링

- 이벤트 핸들러가 도는 동안 시스템에서 **그 핸들러만** 돈다. 그래서 다음에 무슨 이벤트를 처리할지 고르는 것이 곧 스케줄링이다(OSTEP 33.1).
- CPU 하나에 루프 하나면 핸들러끼리 끼어들 일이 없다. 그래서 **락이 필요 없다**(OSTEP 33.4).
- 대가로 규칙 하나가 생긴다. **블로킹 호출 금지.** 핸들러가 막히면 서버 전체가 막힌다(OSTEP 33.5).

### 리액터 패턴 — 이벤트 루프의 설계 이름

```text
   +-------------------------------+
   | Initiation Dispatcher (루프)   |   handle_events():
   |   핸들러 등록표: fd -> handler  |     1. demultiplexer로 준비된 fd들을 기다린다
   +---------------+---------------+     2. fd마다 등록된 handler를 호출한다
                   |
                   v
   Synchronous Event Demultiplexer        Event Handler (연결마다)
   (select / poll / epoll_wait)           handle_event(): 읽고, 처리하고, 쓰고, 짧게 반환
```

- Schmidt의 Reactor 논문은 이 구조를 "동기 이벤트를 디멀티플렉싱하고 디스패치하는" 패턴으로 정리했다.
  - *디멀티플렉싱*: 여러 입력 중 무엇이 준비됐는지 가려내는 일이다. 여기서는 epoll이 한다.
  - *디스패치*: 가려낸 이벤트를 알맞은 핸들러에 넘기는 일이다.
- 같은 논문이 꼽는 한계
  - **비선점**: 핸들러는 도중에 끊기지 않는다. 그래서 핸들러가 블로킹 I/O를 하면 프로세스 전체가 막힌다. 긴 작업은 스레드(Active Object)로 넘기라고 한다.
  - **디버깅이 어렵다**: 제어 흐름이 프레임워크와 콜백 사이를 오간다.
- "동기 이벤트"라는 말은 25번의 "준비 알림"과 같은 뜻이다. 완료 알림을 쓰는 짝은 프로액터다(36번).

### libuv(Node)의 한 바퀴

```text
   +--> 시간 갱신
   |    타이머      : 만기된 setTimeout/setInterval 콜백 (타이머 힙의 최솟값부터)
   |    대기 콜백   : 지난 바퀴에서 미뤄진 I/O 콜백
   |    idle·prepare
   |    I/O 대기    : epoll_wait(timeout = 가장 가까운 타이머까지 남은 시간)   <- 여기서만 잠든다
   |    check       : setImmediate 콜백
   |    close 콜백
   +--- 살아 있는 핸들·요청이 있으면 반복
```

- libuv 설계 문서의 단계 순서다. I/O 대기의 타임아웃은 활성 핸들·요청을 보고 계산한다. 타이머가 있으면 가장 가까운 만기까지만 잠든다.
- libuv 루프와 핸들은 **스레드 안전하지 않다**. 루프 하나는 스레드 하나에서만 돈다(libuv 설계 문서).
- 네트워크 I/O는 epoll(리눅스)·kqueue·IOCP로 기다린다. 파일 I/O·`getaddrinfo`는 OS에 쓸 만한 비동기 API가 없어 **스레드 풀**에서 블로킹으로 돌린다. 풀 기본 크기는 4, `UV_THREADPOOL_SIZE`로 최대 1024까지(libuv 문서).
- libuv 1.45~1.48은 리눅스에서 일부 파일 작업을 io_uring으로도 보냈다. 1.49부터는 그 경로가 기본 꺼짐이다(libuv ChangeLog, 34번).

### 타이머는 "최소 지연"이다

```text
  setTimeout(f, 100)   -> 타이머 힙에 (now+100, f) 삽입
  루프: epoll_wait(timeout = 힙 최솟값 - now) -> 깨어나서 만기된 것 실행
  그 사이 다른 콜백이 500ms를 쓰면 -> f는 약 500ms 뒤에야 실행된다
```

- Node 문서: 콜백은 정확히 `delay` 뒤에 불리지 않을 가능성이 높다. 정확한 시점·순서를 보장하지 않는다. 가능한 한 가깝게 부를 뿐이다.

```text
  재현 (예시, 리눅스 7.0, Node 18.19.1): 100ms 간격 타이머 + 250ms 시점에 500ms 동기 루프
  tick gap 101 ms
  tick gap 100 ms
  blocked 500ms (sync loop)
  tick gap 558 ms          <- 이 사이에 들어온 모든 콜백·요청이 같이 밀린다
  tick gap 101 ms
  eventloop delay max ms 514   (perf_hooks.monitorEventLoopDelay)
```

### 콜백과 상태 관리 — "손으로 하는 스택 관리"

스레드 코드는 상태가 스택에 있다.

```c
int rc = read(fd, buffer, size);     /* 스레드가 여기서 잠든다 */
rc = write(sd, buffer, size);        /* 깨어나면 sd가 스택에 그대로 있다 */
```

이벤트 코드는 읽기를 비동기로 걸고 **핸들러를 반환**해야 한다. 그러면 `sd`를 어디에 두나.

```text
  1. read 비동기 요청 + "끝나면 sd로 써라"를 자료구조에 저장 (예: fd -> sd 해시 테이블)
  2. 핸들러 반환, 루프는 다른 일
  3. 완료 이벤트(fd) -> 테이블에서 sd를 찾아 write
```

- OSTEP은 이것을 Adya 외의 말로 **manual stack management**라 부르고, 해법으로 **continuation**(남은 일을 기록해 두었다가 이벤트가 오면 이어 가기)을 든다(33.7).
  - *continuation*: "이 일이 끝나면 이어서 할 나머지 계산"을 값으로 들고 다니는 것이다. 콜백 함수와 그 클로저가 흔한 구현이다.
- JS의 Promise·`async/await`는 이 continuation을 언어가 대신 만들어 준다. 컴파일러가 함수를 상태 기계로 바꾼다(language/14).

### 이벤트 방식에도 남는 어려움 (OSTEP 33.8)

- **멀티코어**: 코어를 다 쓰려면 루프를 여러 개 돌려야 한다. 그러면 공유 상태에 다시 락이 필요하다.
- **페이지 폴트**: 핸들러가 스왑된 페이지를 건드리면 **암묵적으로** 블록된다. 코드에 블로킹 호출이 없어도 피하기 어렵다.
- **API 의미 변화**: 어떤 함수가 논블로킹에서 블로킹으로 바뀌면 그걸 부르는 핸들러를 둘로 쪼개야 한다.
- **디스크와 네트워크의 통합**: 네트워크는 select류로, 디스크는 AIO로 따로 다루게 되는 일이 많다. 비동기 I/O가 없는 시스템을 위한 하이브리드(이벤트 + I/O용 스레드 풀)는 OSTEP 33.6이 Pai 외 1999(Flash)로 소개한다.

## 쓰이는 자료구조·알고리즘

- **이벤트 큐 / 준비 목록** — 커널의 epoll 준비 목록(26번)과, 앱이 쌓는 대기 콜백 큐. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **최소 힙(타이머 힙)** — "가장 먼저 만기되는 타이머"를 O(1)로 보고, 삽입·삭제 O(log n). libuv `src/timer.c`가 `heap_insert`·`heap_min`으로 구현하고, `uv__next_timeout`이 힙 최솟값으로 epoll 대기 시간을 정한다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
  - 대비: Redis `ae.c`의 시간 이벤트는 정렬되지 않은 연결 리스트라 다음 타이머 찾기가 O(N)이다. 소스 주석이 직접 "O(N) since time events are unsorted"라고 적는다. 타이머 수가 적다는 전제다.
- **해시 테이블(continuation 저장)** — OSTEP 예: fd를 키로 "이어서 쓸 소켓"을 찾는다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **연결별 상태 기계** — "헤더 읽는 중 → 본문 읽는 중 → 응답 쓰는 중". `EAGAIN`에서 멈춘 자리를 저장한다(epoll(7) 예제 설명).
- **스레드 풀 + 작업 큐** — 루프가 못 하는 블로킹 일을 넘기는 곳(libuv 스레드 풀).

## 적용 — 풀어나가는 법

### 1. C — 타이머 힙으로 epoll 대기 시간을 정한다

```c
for (;;) {
    int timeout = -1;                               /* 타이머가 없으면 무한 대기 */
    if (!heap_empty(&timers)) {
        long d = heap_min(&timers)->deadline_ms - now_ms();
        timeout = d > 0 ? (int)d : 0;
    }
    int n = epoll_wait(ep, evs, 64, timeout);
    for (int i = 0; i < n; i++)
        dispatch(evs[i].data.ptr, evs[i].events);   /* 핸들러: 짧게, 블로킹 금지 */
    while (!heap_empty(&timers) && heap_min(&timers)->deadline_ms <= now_ms())
        run_timer(heap_pop(&timers));               /* 만기된 타이머 실행 */
}
```

### 2. JS — 루프를 막는 것을 찾고, 무거운 일은 넘긴다

```js
const { monitorEventLoopDelay } = require('node:perf_hooks');
const h = monitorEventLoopDelay({ resolution: 10 });
h.enable();
setInterval(() => {
  console.log('loop delay p99 ms', (h.percentile(99) / 1e6).toFixed(1));  // 지표로 내보낸다
  h.reset();
}, 10_000);

// CPU 무거운 일은 worker_threads로
const { Worker } = require('node:worker_threads');
new Worker('./resize-image.js', { workerData: { path } });
```

- 동기 API(`*Sync`), 큰 `JSON.parse`/`JSON.stringify`, 무거운 정규식, 암호 연산의 동기 버전이 대표적인 루프 차단 원인이다.
- libuv 스레드 풀은 기본 4개다. `fs.*`, `crypto.pbkdf2`·`scrypt` 같은 비동기 암호 함수, `dns.lookup`이 이 4개를 **나눠 쓴다**.

```text
  재현 (예시, 리눅스 7.0, Node 18.19.1): crypto.pbkdf2 8개를 동시에 시작
  기본(4):               job 0~3 약 72~81ms에 완료, job 4~7 약 145~155ms에 완료  <- 두 물결
  UV_THREADPOOL_SIZE=8:  8개 모두 약 77~96ms에 완료
```

### 3. Java — Netty 이벤트 루프에서는 막지 않는다

```java
EventExecutorGroup biz = new DefaultEventExecutorGroup(16);   // 블로킹 일을 위한 별도 그룹(예시 16)
pipeline.addLast("codec", new HttpServerCodec());             // I/O 스레드(이벤트 루프)에서 실행
pipeline.addLast(biz, "handler", new MyBusinessLogicHandler()); // 별도 스레드에서 실행
```

- Netty `ChannelPipeline` Javadoc 예제가 이 방식이다. "시간이 걸리는 작업으로 I/O 스레드가 막히지 않도록" 다른 그룹을 지정하라고 한다. 로직이 완전히 비동기이거나 매우 빠르면 필요 없다고도 적는다.
- 같은 문서는 `DefaultEventLoopGroup`으로 넘겨도 `ChannelHandlerContext`별로는 **순서대로** 처리되므로 여전히 병목이 될 수 있다고 경고한다.
- 이벤트 루프 스레드에서 자기 자신의 결과를 블로킹으로 기다리면 Netty는 `BlockingOperationException`을 던진다. 교착에 빠질 가능성이 크기 때문이다(Netty 소스 Javadoc).

### 4. 진단 명령

```bash
# 루프 스레드 하나가 CPU 100%인가 (Node 메인 스레드, Netty nioEventLoopGroup-*, redis-server)
top -H -p <pid>

# epoll_wait 사이 간격이 길면 그 사이에 핸들러가 오래 돈 것
strace -f -tt -T -e trace=epoll_wait,epoll_pwait -p <pid>

# 루프 스레드가 D 상태로 빠지나 (파일·페이지 폴트 대기)
ps -L -o tid,stat,wchan:32,comm -p <pid>
pidstat -r -p <pid> 1          # majflt/s: 주 페이지 폴트(디스크에서 읽어 오는 폴트)

# Redis: 느린 명령 기록
redis-cli SLOWLOG GET 10
```

## 장애 시나리오와 대처

### 1. 이벤트 루프에서 블로킹 호출 → 모든 요청이 동시에 늦어진다

- **현상**: 특정 API 하나가 느린 게 아니라, 그 순간 처리 중이던 **모든** 요청의 지연이 한꺼번에 튄다. 헬스 체크도 늦어져 LB가 인스턴스를 빼기도 한다.
- **보이는 형태**
  - 지연 그래프에 모든 엔드포인트가 같은 시각에 스파이크.
  - Node: `monitorEventLoopDelay` 최댓값이 튄다(재현에서 500ms 차단 → 514ms).
  - `top -H`에서 루프 스레드 하나만 100%, 나머지는 한가하다.
  - Netty: `nioEventLoopGroup-*`·`epollEventLoopGroup-*` 스레드 덤프가 JDBC·HTTP 클라이언트 호출 스택에 있다.
- **원인**: 핸들러가 동기 파일 I/O, 블로킹 DB·HTTP 호출, 큰 CPU 작업을 했다. 이벤트 루프는 비선점이라 그동안 다른 이벤트를 하나도 처리하지 못한다(Reactor 논문 한계, OSTEP 33.5).
- **대처**
  - 블로킹 일은 별도 풀로 넘긴다(libuv 스레드 풀, `worker_threads`, Netty `EventExecutorGroup`).
  - 이벤트 루프 지연을 지표로 수집하고 경보를 건다.
  - 드라이버 선택: 비동기 드라이버가 없으면 전용 풀 + 유계 큐로 격리한다(36번).

### 2. libuv 스레드 풀 고갈 → 파일·DNS가 이유 없이 느리다

- **현상**: CPU도 네트워크도 여유인데 `fs.readFile`이나 외부 호출의 연결 시작이 가끔 수백 ms 늦다.
- **보이는 형태**: 비밀번호 해시(`bcrypt`/`pbkdf2`)나 대량 파일 작업이 몰리는 시간에만 `dns.lookup`(호스트 이름으로 여는 HTTP 요청 포함)이 늦다.
- **원인**: 기본 4개 스레드를 `fs`·암호·`dns.lookup`이 나눠 쓴다. Node 문서는 `dns.lookup`이 스레드 풀에서 도는 동기 `getaddrinfo`라 "놀라운 성능 영향"이 있을 수 있다고 적는다.
- **대처**
  - `UV_THREADPOOL_SIZE`를 늘린다(프로세스 시작 전에 설정, 최대 1024).
  - DNS는 `dns.resolve*`(스레드 풀 미사용)나 캐시를 쓴다.
  - 무거운 암호 작업은 `worker_threads`로 분리한다.

### 3. Redis `KEYS *` → 모든 클라이언트 정지

- **현상**: 운영 Redis에서 누군가 `KEYS *`를 실행하자 모든 클라이언트 명령이 수 초 멈췄다. 애플리케이션 쪽에서 Redis 타임아웃이 한꺼번에 난다.
- **보이는 형태**: `SLOWLOG`에 `KEYS` 기록, 그 시각 `redis-server` 메인 스레드 CPU 100%.
- **원인**: Redis는 대부분 단일 스레드로 모든 요청을 순서대로 처리한다(Redis latency 문서). O(N) 명령 하나가 루프를 점유한다. 문서는 운영에서 `KEYS` 사용을 지연의 "매우 흔한 원인"으로 꼽는다.
- **대처**: `SCAN` 계열로 나눠 순회한다. 위험 명령은 `rename-command`(redis.conf)나 ACL(`-@dangerous`, `KEYS`는 `@dangerous` 범주)로 막는다.

### 4. 타이머가 늦게 울린다·페이지 폴트로 루프가 멈춘다

- **현상**: 100ms마다 돌아야 할 heartbeat가 가끔 수백 ms씩 밀려 상대가 연결을 끊는다. 코드엔 블로킹 호출이 없다.
- **보이는 형태**
  - 타이머 간격 로그가 불규칙하게 길다(재현: 100ms 간격이 558ms).
  - `pidstat -r`의 `majflt/s`가 그 시각에 오른다. 루프 스레드가 `D` 상태로 잡힌다.
- **원인**
  - 타이머는 최소 지연일 뿐이고, 다른 콜백이 루프를 쓰는 동안 미뤄진다(Node 문서).
  - 메모리가 부족해 스왑이 일어나면 핸들러가 페이지 폴트로 **암묵적으로** 블록된다(OSTEP 33.8, 12번).
- **대처**: 루프 지연 원인(1번)을 먼저 없앤다. heartbeat는 여유 있는 타임아웃과 함께 쓴다. 메모리 압박·스왑을 해소한다(`vmstat`의 `si`/`so`).

## 핵심 문장

- 이벤트 루프는 "준비된 이벤트를 받아 핸들러를 하나씩 짧게 실행"을 반복한다. 무엇을 다음에 처리할지 고르는 것이 곧 스케줄링이고, 싱글 코어 루프에는 락이 필요 없다.
- 규칙은 하나다. **이벤트 루프 안에서 블로킹 금지.** 핸들러 하나가 막히면 그 루프의 모든 연결이 함께 막힌다.
- 리액터 = 동기 이벤트 디멀티플렉서(epoll) + 디스패처 + 핸들러다. 핸들러는 비선점이라 긴 일은 스레드로 넘긴다.
- 타이머는 최소 힙으로 관리하고, 가장 가까운 만기까지만 epoll에서 잠든다. 타이머는 "최소 지연"일 뿐이다.
- 이벤트 방식의 대가는 상태를 스택 대신 자료구조에 직접 들고 다니는 것(manual stack management)이다. 콜백·Promise·async/await가 그 continuation을 표현한다.

## 관련 주제·근거

- 선행: [26-io-multiplexing-epoll](../26-io-multiplexing-epoll/2-summary.md) — 루프의 `getEvents()`
- 함께: [25-io-models](../25-io-models/2-summary.md) — 준비 알림 vs 완료 알림, 정규 파일은 논블로킹이 안 된다
- 후속
  - [34-zero-copy-and-io-uring](../34-zero-copy-and-io-uring/2-summary.md) — 완료 큐 기반 루프(프로액터)
  - [36-server-concurrency-architectures](../36-server-concurrency-architectures/2-summary.md) — 멀티 리액터, 반동기/반비동기, 워커 풀
  - [language/README](../../language/README.md) — `14-concurrency-models`(async/await 상태 기계, 가상 스레드). 미작성
  - [web-platform/03-event-loop](../../web-platform/03-event-loop/2-summary.md)(브라우저 태스크·마이크로태스크)
- 다른 OS 주제
  - [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md)·[15-race-conditions](../15-race-conditions/2-summary.md) — 스레드 방식의 비용
  - [12-swapping-and-page-replacement](../12-swapping-and-page-replacement/2-summary.md) — 페이지 폴트·스왑이 루프를 암묵적으로 막는 이유
- 교재·논문
  - OSTEP 33장 "Event-based Concurrency (Advanced)" — 33.1 이벤트 루프, 33.4 락 불필요, 33.5 블로킹 시스템 콜, 33.6 비동기 I/O·하이브리드(Flash), 33.7 manual stack management·continuation, 33.8 남은 어려움 <https://pages.cs.wisc.edu/~remzi/OSTEP/threads-events.pdf>
  - D. C. Schmidt, "Reactor: An Object Behavioral Pattern for Demultiplexing and Dispatching Handles for Synchronous Events" — 11.2 Liabilities(비선점, 디버깅) <https://www.dre.vanderbilt.edu/~schmidt/PDF/reactor-siemens.pdf>
  - Schmidt 외, 『Pattern-Oriented Software Architecture Vol.2』(POSA2, Wiley 2000) — Reactor·Proactor·Active Object <https://www.dre.vanderbilt.edu/~schmidt/POSA/POSA2/>
- 문서·소스
  - libuv Design overview — 루프 단계, 스레드 안전하지 않음, 파일 I/O는 스레드 풀 <https://docs.libuv.org/en/v1.x/design.html>
  - libuv Thread pool — 기본 4, 최대 1024, fs·getaddrinfo·getnameinfo <https://docs.libuv.org/en/v1.x/threadpool.html>
  - libuv `src/timer.c` — `heap_insert`·`heap_min`·`uv__next_timeout` <https://github.com/libuv/libuv/blob/v1.x/src/timer.c>
  - Node.js timers — "precisely delay"를 보장하지 않음 <https://nodejs.org/api/timers.html>
  - Node.js dns — `dns.lookup`은 스레드 풀의 동기 `getaddrinfo` <https://nodejs.org/api/dns.html>
  - Netty 4.1 `ChannelPipeline` Javadoc(EventExecutorGroup 예제·순서 경고), `BlockingOperationException` <https://github.com/netty/netty/blob/4.1/transport/src/main/java/io/netty/channel/ChannelPipeline.java>
  - Redis latency 문서 — 대부분 단일 스레드, `KEYS`는 흔한 지연 원인 <https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/>
  - Redis `src/ae.c` — 시간 이벤트 O(N) 주석, epoll/kqueue/evport/select 백엔드 선택 <https://github.com/redis/redis/blob/unstable/src/ae.c>
  - Redis `redis.conf`(`rename-command`), ACL 문서(`-@dangerous`), `src/commands/keys.json`(`acl_categories`: KEYSPACE, DANGEROUS) <https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/>
  - libuv ChangeLog — 1.45.0 io_uring 도입, 1.49.0 SQPOLL io_uring 기본 비활성 <https://github.com/libuv/libuv/blob/v1.x/ChangeLog>
- 로컬 재현(리눅스 7.0, Node 18.19.1): 500ms 동기 루프 중 100ms 타이머 간격 558ms·루프 지연 최대 514ms, pbkdf2 8개의 두 물결(풀 4) vs 한 물결(풀 8)
