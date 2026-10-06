# os/36-server-concurrency-architectures — 스레드를 어떻게 배치하나: 연결당 스레드·리액터·프로액터·반동기/반비동기·리더/팔로워 — 정리 (힌트)

## 해결하는 문제

서버는 세 가지를 동시에 다룬다.

```text
  1. 연결을 받는다          (accept)
  2. 연결에서 읽고 쓴다      (I/O 대기가 대부분)
  3. 요청을 처리한다         (CPU, 또는 DB·외부 호출 대기)
```

이 셋을 **어느 스레드가 맡나**가 서버 동시성 아키텍처다.\
Kegel의 "The C10K problem"(연결 1만 개를 동시에)은 이 질문을 I/O 전략 목록으로 정리했다.
- 스레드 하나가 여러 클라이언트 + 논블로킹 I/O + 레벨 트리거 준비 알림(select/poll)
- 스레드 하나가 여러 클라이언트 + 논블로킹 I/O + 준비 "변화" 알림(epoll ET, kqueue)
- 스레드 하나가 여러 클라이언트 + 비동기 I/O + 완료 알림
- 클라이언트마다 서버 스레드 하나, `read`/`write`는 블로킹
- 서버 코드를 커널 안에 넣기

쉬운 예: 식당 운영 방식이다.
- **연결당 스레드**: 손님마다 전담 웨이터. 손님이 메뉴를 고르는 동안 웨이터도 서 있다.
- **리액터**: 홀 매니저 한 명이 호출벨 판을 보고, 벨이 울린 테이블에 가서 짧게 처리한다.
- **프로액터**: 주방에 주문서를 넣어 두면 요리가 **다 된 뒤** 완료 벨이 울린다.
- **반동기/반비동기**: 입구 접수 창구(비동기)가 주문을 받아 주문 꽂이(큐)에 꽂고, 요리사들(동기)이 하나씩 빼서 만든다.
- **리더/팔로워**: 웨이터들이 줄을 서서 한 명씩 돌아가며 입구를 지킨다. 손님이 오면 지키던 웨이터가 다음 사람에게 입구를 넘기고 **자기가** 그 손님을 맡는다.

실무 예:
- Tomcat(NIO 커넥터 + 워커 풀 200), Netty(boss/worker 이벤트 루프), nginx(워커 프로세스마다 이벤트 루프), Redis·Node(단일 이벤트 루프), Windows IIS(IOCP).
- "스레드를 늘렸더니 `OutOfMemoryError: unable to create native thread`."
- "Netty 핸들러에서 JDBC를 불렀더니 전 연결이 같이 느려졌다."
- "워커 풀 큐가 무한이라 지연이 수십 초가 된 뒤 OOM으로 죽었다."

## 동작·원리

### 1. 연결당 스레드 (thread-per-connection)

```text
  acceptor 스레드: accept() -> 새 스레드 생성(또는 풀에서 꺼냄) -> 넘김
  스레드 1: read(c1) ... 처리 ... write(c1) ... read(c1)   (대부분 잠들어 있다)
  스레드 2: read(c2) ... 처리 ... write(c2)
  ...
  스레드 N: read(cN) ...
```

- 코드가 가장 단순하다. 상태가 스택에 있다(27번의 manual stack management가 없다).
- 비용은 **스레드 수 = 동시 연결 수**라는 데서 나온다.
  - **메모리**: 스레드마다 사용자 스택과 커널 스택을 가진다. Kegel은 스레드당 2MB 스택이면 32비트 1GB 사용자 공간에서 512개에 가상 메모리가 바닥난다고 계산했다.
    - x86-64 리눅스의 커널 스택은 `THREAD_SIZE` = 16KB다(KASAN 없는 빌드, `arch/x86/include/asm/page_64_types.h`).
  - **스케줄링**: 깨어날 스레드가 많을수록 컨텍스트 스위칭과 캐시 오염이 는다(07번).
  - **한도**: `kernel.threads-max`, `kernel.pid_max`, `vm.max_map_count`, `ulimit -u`, cgroup `pids.max`.

```text
  유휴 스레드 1000개 생성 (예시, 리눅스 7.0, glibc 기본 스택 = ulimit -s 8192KB)
  [before]  VmSize:     2692 kB  VmRSS:  1612 kB  Threads:    1
  [after ]  VmSize:  8198956 kB  VmRSS: 10088 kB  Threads: 1001    <- 가상 8GB, 실제 상주 약 10MB
  스택 256KB로 지정:   VmSize:   262956 kB  VmRSS: 10088 kB
```

- 64비트에서는 가상 공간이 넉넉하다. 유휴 스레드의 **상주 메모리**는 스레드당 수 KB~수십 KB로 작다(위 재현: 약 8.5KB, 커널 스택은 별도). 스택을 깊게 쓰면 그만큼 는다.
- 그래서 오늘날의 한계는 "가상 메모리"보다 **스레드 수 한도·스케줄링·스레드마다 쥔 버퍼·힙**에서 먼저 오는 경우가 많다.
- Java 21 가상 스레드(JEP 444)는 이 스타일을 **지키면서** 비용을 낮춘다. JVM이 많은 가상 스레드를 적은 OS 스레드(캐리어)에 얹는다.
  - JEP 444: 가상 스레드는 "더 빠른 스레드가 아니다". 속도(지연)가 아니라 규모(처리량)를 준다.
  - JDK 21~23에서는 `synchronized` 안에서 블로킹하면 캐리어에 고정(pinning)됐다. JDK 24의 JEP 491이 이것을 거의 없앴다.

### 2. 리액터 — 단일 리액터와 멀티 리액터

```text
  단일 리액터                               멀티 리액터 (main + sub)
  +----------------------------+            main reactor: accept 전용
  | 루프 1개: epoll_wait         |              | 새 연결을 sub 중 하나에 배정(라운드 로빈)
  |  accept / read / 처리 / write |              v
  +----------------------------+            sub reactor 1   sub reactor 2   ...  (CPU 수만큼)
  예: Redis, Node                           각자 epoll + 루프, 연결은 한 루프에 고정
                                            예: Netty(boss/worker)
```

- 준비 알림(epoll)으로 여러 연결을 한 스레드가 기다린다(26·27번).
- 단일 리액터는 코어 하나만 쓴다. 멀티 리액터는 루프를 코어 수만큼 두고 **연결을 한 루프에 고정**한다. 연결 상태를 루프끼리 공유하지 않으니 락이 거의 필요 없다.
  - Netty `MultithreadEventLoopGroup`의 기본 스레드 수는 `max(1, CPU 수 × 2)`다(`io.netty.eventLoopThreads`로 변경).
  - nginx `worker_processes`는 기본 1이고, CPU 코어 수(`auto`)가 좋은 출발점이라고 문서가 적는다.
- accept를 어떻게 나누나
  - main reactor 하나가 accept해서 배정한다(Netty boss group).
  - main reactor 없이 워커가 공유 리슨 소켓에서 직접 accept한다. nginx가 이 방식이다. 1.11.3부터 `accept_mutex` 기본값이 off이고, 리눅스에서는 `EPOLLEXCLUSIVE`를 쓴다(nginx CHANGES 1.11.3).
  - 워커마다 리슨 소켓을 따로 두고 `SO_REUSEPORT`로 커널이 나눈다(nginx `listen ... reuseport`, 1.9.1+). socket(7)은 이것이 "accept 스레드 하나가 나눠 주는 방식"이나 "여러 스레드가 같은 소켓에서 경쟁하는 방식"보다 분배가 낫다고 적는다(26번 thundering herd).
- 한계: 핸들러는 비선점이다. 한 핸들러가 막히면 **그 루프에 묶인 모든 연결**이 멈춘다(27번).

### 3. 프로액터 — 완료를 받는다

```text
  앱: "이 소켓에서 4KB 읽어 이 버퍼에 넣어 줘" 비동기 시작 (+ 완료 핸들러)
        |
  OS: 준비 대기 + 복사까지 수행 -> 완료 큐에 결과를 넣음
        |
  Completion Dispatcher: 완료 큐에서 꺼내 완료 핸들러 호출 -> 핸들러가 다음 비동기 작업 시작
```

- Proactor 논문(Pyarali 외 1997)의 흐름이다. 리액터가 "읽을 수 있다"를 받는다면, 프로액터는 "**읽었다**"를 받는다.
- 장점: 여러 연산이 앱 스레드 수와 무관하게 동시에 진행된다(논문 "primary advantage"). 복사까지 OS가 하니 25번 분류로 진짜 비동기다.
- OS 지원
  - Windows IOCP가 대표적이다.
  - 리눅스는 io_uring이 완료 큐를 준다(34번).
  - Java NIO.2 `AsynchronousSocketChannel`은 리눅스에서 **epoll + 스레드 풀로 흉내 낸다**. OpenJDK의 `LinuxAsynchronousChannelProvider`가 `EPollPort`(스레드 풀 포함)를 만든다. 겉은 프로액터, 속은 리액터다.
- 비용: 버퍼를 **작업 시작 시점에** 넘겨야 한다. 연결 1만 개에 읽기를 걸어 두면 버퍼 1만 개가 묶인다. 완료 순서가 제출 순서와 다를 수 있어 완료 토큰(`user_data`, POSA2의 Asynchronous Completion Token)으로 짝을 맞춘다.

### 4. 반동기/반비동기 (Half-Sync/Half-Async)

```text
  비동기 층   : NIO/epoll 루프가 연결 준비·읽기·요청 파싱   (블로킹 금지)
                   |
  큐잉 층     : [요청][요청][요청] ...   <- 핸드오프 큐 (여기의 크기·정책이 핵심)
                   |
  동기 층     : 워커 스레드 풀. 요청을 꺼내 블로킹 코드로 처리 (JDBC, 파일, 외부 API)
```

- POSA2의 Half-Sync/Half-Async는 동기 작업과 비동기 작업을 두 층으로 나누고, 그 사이에 **큐잉 층**을 둔다.
- 흔한 구현
  - Tomcat NIO 커넥터: 커넥터가 논블로킹으로 연결을 관리하고, 요청 처리는 워커 풀(`maxThreads` 기본 200)에 넘긴다. 연결은 `maxConnections`(NIO 기본 8192)까지 받아 둔다.
  - Netty 이벤트 루프 + 비즈니스 `EventExecutorGroup`(27번).
- HS-HA 논문이 강조하는 설계 항목: **층 사이 흐름 제어.** "시스템은 큐잉 층의 버퍼에 무한한 자원을 쓸 수 없다."
  - 동기 층은 블록할 수 있으니, 너무 많이 넣으면 재운다.
  - 비동기 층은 블록할 수 없으니, 넘치면 **버린다**. 논문은 "TCP면 보낸 쪽이 결국 재전송한다"고 적는데, 이는 큐잉 층이 커널 안에 있어 ACK 전에 버리는 경우(BSD 예)다.
  - 사용자 공간 이벤트 루프가 이미 `read`한 바이트는 커널 TCP가 ACK했다. 앱이 버려도 재전송되지 않고 조용히 사라진다. 그래서 명시적으로 거절(503·연결 종료)하거나, 읽기를 멈춰 수신 버퍼·TCP 윈도로 보낸 쪽을 늦춘다.
- 대가(LF 논문의 지적): 요청마다 큐에 넣고 빼는 동적 할당, 동기화, **스레드 간 핸드오프의 컨텍스트 스위치**가 든다. 데이터가 다른 스레드로 넘어가 CPU 캐시 친화성도 떨어진다.

### 5. 리더/팔로워 (Leader/Followers)

```text
  스레드 풀: [L] [F] [F] [F]      L = 리더 (핸들 집합을 기다림), F = 팔로워 (차례 대기)
  이벤트 도착 -> L이 F 하나를 새 리더로 승격 -> 옛 L은 그 이벤트를 **직접** 처리
              -> 처리 끝나면 팔로워로 돌아가 줄 선다
```

- 여러 스레드가 핸들 집합(예: epoll)을 **번갈아** 기다리고, 이벤트를 받은 스레드가 그 일을 직접 처리한다(Schmidt 외, Leader/Followers).
- 장점(논문): 스레드 간 핸드오프 큐가 없다. 요청 버퍼를 자기 스택에 둘 수 있어 캐시 친화적이고 동적 할당·락이 준다. 이벤트마다 컨텍스트 스위치가 필요 없다(리더 승격 때는 필요).
- 단점(논문): 구현이 복잡하다(승격·복귀가 동시에 일어난다). 큐가 없으니 이벤트를 **버리거나 우선순위를 다시 매길 수 없다.**
- 리눅스 epoll에서는 여러 스레드가 한 epfd를 기다리고 `EPOLLONESHOT`으로 한 fd를 한 스레드만 처리하게 하는 방식이 이 패턴에 가깝다(26번). 정확한 대응은 구현마다 다르다.

### 6. Acceptor-Connector

- "연결 수립·서비스 초기화"를 "연결된 뒤의 처리"와 분리하는 패턴이다(Schmidt, Acceptor-Connector).
  - Acceptor: 수동 연결(listen·accept)을 받아 서비스 핸들러를 만들어 붙인다.
  - Connector: 능동 연결(connect, 논블로킹 connect 포함)을 걸고 완성되면 핸들러를 붙인다.
- 위 아키텍처들과 **조합**해서 쓴다. Netty의 `ServerBootstrap`(boss group이 accept → worker에 채널 등록)이 Acceptor, `Bootstrap.connect`가 Connector 역할이다.

### 비교표

| | 연결당 스레드 | 리액터 | 프로액터 | 반동기/반비동기 | 리더/팔로워 |
|---|---|---|---|---|---|
| 알림 | 없음(블로킹) | 준비 | 완료 | 준비(비동기 층) | 준비 |
| 스레드 수 | 연결 수 | 루프 수(≈코어) | 적음 | 루프 + 워커 풀 | 풀 크기 |
| 블로킹 코드 | 자유 | 금지 | 금지 | 동기 층에서만 | 가능(처리 스레드가 곧 리더 후보) |
| 핸드오프 큐 | 없음 | 없음 | 완료 큐 | **있음** | 없음 |
| 대표 | 전통 Tomcat BIO, 가상 스레드 | Redis, Node, nginx, Netty | IOCP, io_uring | Tomcat NIO + 워커, Netty + 비즈니스 풀 | ACE `ACE_TP_Reactor`, TAO(LF 논문 Known Uses) |

## 쓰이는 자료구조·알고리즘

- **준비 이벤트 디멀티플렉싱** — epoll의 관심 목록(레드블랙 트리) + 준비 목록(리스트)(26번).
- **완료 큐** — io_uring CQ는 커널→앱 단일 생산자·단일 소비자 링이다(34번). IOCP 완료 포트는 링이 아니라 여러 스레드가 함께 기다리는 커널 큐다. 완료 패킷은 FIFO로 쌓이고, 기다리는 스레드는 LIFO로 깨우며, 동시 실행 스레드 수 한도(concurrency value)가 있다(Microsoft Learn "I/O Completion Ports").
- **핸드오프 큐(유계 블로킹 큐)** — HS/HA의 큐잉 층. 생산자·소비자 문제 그 자체다(18번 세마포어). 크기 한도와 넘칠 때 정책(거절·호출자 실행·버림)이 설계의 핵심이다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **리틀의 법칙 L = λW** — 필요한 동시성(스레드·연결) = 도착률 × 체류 시간. JEP 444 예: 지연 50ms, 초당 200건이면 동시 10건. 초당 2000건이면 100건. [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md)
- **라운드 로빈 배정** — main reactor가 새 연결을 sub reactor에 돌려 가며 붙인다. `SO_REUSEPORT`는 라운드 로빈이 아니다. 커널이 패킷의 해시로 그룹 안 리슨 소켓 하나를 고른다. BPF 프로그램을 붙이면 그 결과를 쓴다(`net/core/sock_reuseport.c`의 `reuseport_select_sock`).

## 적용 — 풀어나가는 법

### 1. 고르는 순서

```text
  작업이 CPU 위주인가?          -> 코어 수만큼의 스레드. 모델보다 알고리즘이 중요하다 (가상 스레드도 이득 없음, JEP 444)
  I/O 대기 위주 + 블로킹 라이브러리(JDBC 등)를 써야 하나?
                               -> 반동기/반비동기(유계 큐 + 워커 풀), 또는 가상 스레드
  I/O 대기 위주 + 전 구간 논블로킹 가능?
                               -> 멀티 리액터 (이벤트 루프 = 코어 수)
  디스크 I/O가 많고 커널이 허용하나? -> io_uring 프로액터 검토 (34번의 보안 제약 확인)
```

- 어느 모델이든 **하류 자원(DB 풀·외부 API 한도)** 이 진짜 상한이다. 동시성을 늘리면 병목이 하류로 옮겨 갈 뿐이다.

### 2. Java — 워커 풀은 유계 큐로

```java
ThreadPoolExecutor workers = new ThreadPoolExecutor(
    32, 32, 0L, TimeUnit.MILLISECONDS,
    new ArrayBlockingQueue<>(1_000),                 // 유계 큐(예시 1000)
    new ThreadPoolExecutor.AbortPolicy());           // 넘치면 RejectedExecutionException -> 503으로 빨리 거절

// 피할 것: Executors.newFixedThreadPool(32)
//   Javadoc: "a fixed number of threads operating off a shared unbounded queue" -> 큐가 무한
```

Java 21 가상 스레드 — 연결당(요청당) 스레드 스타일을 유지한다.

```java
try (ExecutorService ex = Executors.newVirtualThreadPerTaskExecutor()) {
    ex.submit(() -> handle(request));   // 블로킹 코드 그대로. 단, DB 풀 크기가 새 상한이 된다
}
```

Netty — boss(accept)와 worker(I/O) 그룹을 나눈다.

```java
EventLoopGroup boss = new NioEventLoopGroup(1);      // Acceptor: accept 전용 루프
EventLoopGroup worker = new NioEventLoopGroup();     // sub reactor들: 기본 CPU×2
new ServerBootstrap().group(boss, worker)
    .channel(NioServerSocketChannel.class)
    .childHandler(initializer);                      // 블로킹 로직은 별도 EventExecutorGroup (27번)
```

### 3. 진단 명령

```bash
# 스레드 수
ps -o pid,nlwp,cmd -p <pid>
grep Threads /proc/<pid>/status

# 컨텍스트 스위치: cswch/s(자발적 = 대기), nvcswch/s(비자발적 = CPU 경쟁)
pidstat -w -t -p <pid> 1

# 스레드 한도
cat /proc/sys/kernel/threads-max /proc/sys/kernel/pid_max /proc/sys/vm/max_map_count
ulimit -u
cat /sys/fs/cgroup/pids.max 2>/dev/null        # 컨테이너 안이면 cgroup v2 pids 한도

# 어떤 스레드가 무엇을 하나 (Java)
jstack <pid> | grep -A5 'EventLoop\|http-nio'

# 큐가 쌓이나: accept 큐(커널)와 앱 큐(지표)
ss -lnt 'sport = :8080'                          # Recv-Q = accept 큐 길이 (network/15)
```

## 장애 시나리오와 대처

### 1. 연결당 스레드 → C10K에서 스레드 생성 실패·컨텍스트 스위칭 폭증

- **현상**: 동시 연결이 수천~수만으로 늘자 새 연결 처리가 실패하거나, CPU 대부분이 커널 시간으로 간다.
- **보이는 형태**
  - Java: `java.lang.OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached`(현재 OpenJDK 메시지. JDK 8은 `unable to create new native thread`).
  - C: `pthread_create`가 `EAGAIN`.
  - `pidstat -w`의 컨텍스트 스위치가 초당 수십만, `vmstat`의 `cs` 열 급증, `%sy` 증가.
- **원인**: 스레드 수가 연결 수를 따라간다. 스레드 한도(`ulimit -u`, `threads-max`, cgroup `pids.max`, `max_map_count`)나 메모리에 먼저 닿는다. 깨어나는 스레드가 많아 스케줄링 비용이 커진다.
- **대처**
  - 리액터·HS/HA로 바꿔 스레드 수를 연결 수와 떼어 낸다.
  - Java 21+면 가상 스레드로 스타일을 유지하며 OS 스레드 수를 줄인다(JDK 24 전이면 `synchronized` 내 블로킹 pinning 주의, JEP 491).
  - 당장은 스레드 스택을 줄이고(`-Xss`, `pthread_attr_setstacksize`) 한도를 점검한다.

### 2. 리액터 스레드에서 DB 호출 → 모든 연결이 동시에 느려진다

- **현상**: 특정 API만이 아니라 그 서버의 **모든** 연결 지연이 같은 시각에 튄다. Netty·WebFlux·Vert.x 서비스에서 흔하다.
- **보이는 형태**: 스레드 덤프에서 `nioEventLoopGroup-*`(Reactor Netty·WebFlux면 `reactor-http-epoll-*`·`reactor-http-nio-*`) 스레드가 JDBC·블로킹 HTTP 호출 스택에 있다. 이벤트 루프 스레드 CPU는 낮은데 지연은 높다.
- **원인**: 리액터 핸들러는 비선점이다. DB 응답을 기다리는 동안 그 루프에 묶인 수천 연결의 이벤트가 처리되지 않는다(27번, Reactor 논문 한계). 연결이 루프에 고정돼 있어 다른 루프로 옮겨 가지도 못한다.
- **대처**
  - 블로킹 호출을 워커 풀로 넘긴다(HS/HA로 전환). Netty `EventExecutorGroup`, Reactor의 `Schedulers.boundedElastic()`(Javadoc: 블로킹 작업용, 스레드 수 상한 있음).
  - 비동기 드라이버(R2DBC 등)로 전 구간 논블로킹을 만든다.
  - 이벤트 루프 지연을 지표로 감시한다.

### 3. 반동기/반비동기 사이 큐가 무한 → 지연 폭증 후 OOM

- **현상**: 하류(DB)가 느려진 뒤 응답 시간이 수 초 → 수십 초로 늘다가 결국 프로세스가 `OutOfMemoryError`로 죽는다. 재시작해도 같은 트래픽에 다시 죽는다.
- **보이는 형태**
  - 워커 큐 길이 지표가 끝없이 증가(지표가 없으면 힙 덤프에서 `LinkedBlockingQueue` 노드가 대량).
  - GC 시간 급증 → `OutOfMemoryError: Java heap space`.
  - 클라이언트는 이미 타임아웃으로 떠났는데 서버는 그 요청들을 계속 처리한다(헛일).
- **원인**
  - 처리율 < 도착률이 되면 큐는 계속 자란다. 리틀의 법칙으로 대기 시간 W = L/λ도 같이 자란다.
  - `Executors.newFixedThreadPool`은 무한 큐다(Javadoc "shared unbounded queue"). 넘칠 때 거절할 지점이 없다.
  - HS-HA 논문이 경고한 "층 사이 흐름 제어"가 없다.
- **대처**
  - 유계 큐 + 거절 정책(빠른 503), 또는 큐 대기 시간 한도(오래 기다린 요청은 버림).
  - 앞단에서 동시 연결·요청 수를 제한한다(Tomcat `maxConnections`·`acceptCount`, LB).
  - 하류별로 풀을 나눈다(bulkhead, [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)·[reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md)).

### 4. 스레드(또는 가상 스레드)를 늘렸더니 DB 풀이 고갈

- **현상**: 처리량을 올리려고 워커를 200 → 2000으로 늘리거나 가상 스레드로 바꿨더니, 오히려 타임아웃이 는다.
- **보이는 형태**: HikariCP `... - Connection is not available, request timed out after 30001ms (total=10, active=10, idle=0, waiting=…)`(예시, HikariCP `HikariPool` 메시지). 숫자는 실제 대기 시간이라 `connectionTimeout`과 거의 같다. 괄호 카운트는 5.x 소스에 있고 4.0.3에는 없다. DB CPU·연결 수 포화.
- **원인**: 동시성은 올랐지만 하류 DB 풀(예: 10개)과 DB 자체 처리량은 그대로다. 대기가 앱 스레드에서 DB 풀 대기로 옮겨 갔다. 가상 스레드는 속도가 아니라 규모를 준다(JEP 444).
- **대처**: 하류 용량에서 거꾸로 동시성 한도를 정한다(세마포어·풀 크기). 풀 대기 타임아웃을 요청 타임아웃보다 짧게 둔다.

## 핵심 문장

- 서버 동시성 아키텍처는 "accept·I/O 대기·처리를 어느 스레드가 맡나"의 선택이다. 핵심 변수는 알림 종류(없음·준비·완료)와 핸드오프 큐 유무다.
- 연결당 스레드는 단순하지만 스레드 수 = 연결 수라서 C10K에서 한도·스케줄링 비용에 먼저 닿는다. 가상 스레드는 이 스타일을 유지하며 OS 스레드를 줄인다(속도가 아니라 규모).
- 리액터는 준비 알림으로 여러 연결을 한 루프가 처리한다. 멀티 리액터는 연결을 루프에 고정해 코어를 쓴다. 루프에서 블로킹하면 그 루프의 모든 연결이 멈춘다.
- 프로액터는 완료 알림을 받는다(IOCP, io_uring). Java NIO.2는 리눅스에서 epoll + 스레드 풀로 흉내 낸다.
- 반동기/반비동기의 생명은 **큐잉 층의 흐름 제어**다. 무한 큐는 지연 폭증 후 OOM으로 끝난다. 리더/팔로워는 큐를 없애 핸드오프 비용을 줄이지만 버리기·재정렬을 못 한다.

## 관련 주제·근거

- 선행
  - [27-event-based-concurrency](../27-event-based-concurrency/2-summary.md) — 이벤트 루프·리액터·블로킹 금지
  - [26-io-multiplexing-epoll](../26-io-multiplexing-epoll/2-summary.md) — 준비 알림, `EPOLLEXCLUSIVE`·`EPOLLONESHOT`·`SO_REUSEPORT`
  - [34-zero-copy-and-io-uring](../34-zero-copy-and-io-uring/2-summary.md) — 완료 큐(프로액터의 리눅스 구현)
- 함께: [25-io-models](../25-io-models/2-summary.md) — 준비 vs 완료, 동기 vs 비동기
- 다른 OS 주제
  - [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md) — 스레드 비용·컨텍스트 스위칭
  - [18-semaphores](../18-semaphores/2-summary.md) — 생산자/소비자, 유계 버퍼
- 다른 영역
  - [network/15-tcp-handshake-and-backlog](../../network/15-tcp-handshake-and-backlog/2-summary.md) — accept 큐(앞단의 첫 큐)
  - [systems/server-design/06-resilience](../../systems/server-design/06-resilience.md) — 스레드 고갈·벌크헤드
  - [language/README](../../language/README.md) — `14-concurrency-models`(가상 스레드·코루틴). 미작성
  - [reliability/39-async-io-gains-and-limits](../../reliability/39-async-io-gains-and-limits/2-summary.md), [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)
- 패턴 문헌
  - Schmidt·Stal·Rohnert·Buschmann, 『Pattern-Oriented Software Architecture Vol.2: Patterns for Concurrent and Networked Objects』(POSA2, Wiley 2000) — 17개 패턴 목록(Reactor, Proactor, Acceptor-Connector, Leader/Followers, Half-Sync/Half-Async, Asynchronous Completion Token 등) <https://www.dre.vanderbilt.edu/~schmidt/POSA/POSA2/>
  - Schmidt, "Reactor" <https://www.dre.vanderbilt.edu/~schmidt/PDF/reactor-siemens.pdf>
  - Pyarali·Harrison·Schmidt·Jordan, "Proactor"(PLoP 1997) <https://www.dre.vanderbilt.edu/~schmidt/PDF/proactor.pdf>
  - Schmidt 외, "Half-Sync/Half-Async" — 큐잉 층, 층 사이 흐름 제어 <https://www.dre.vanderbilt.edu/~schmidt/PDF/HS-HA.pdf>
  - Schmidt·O'Ryan·Kircher·Pyarali·Buschmann, "Leader/Followers" — Consequences(장점·단점), Half-Sync/Half-Reactive 대비 <https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf>
  - Schmidt, "Acceptor-Connector" <https://www.dre.vanderbilt.edu/~schmidt/PDF/Acc-Con.pdf>
  - Dan Kegel, "The C10K problem" — I/O 전략 1~5, 스레드당 2MB 스택 계산 <http://www.kegel.com/c10k.html>
- 문서·소스
  - JEP 444 Virtual Threads(Java 21) — 리틀의 법칙, "not faster threads" <https://openjdk.org/jeps/444>
  - JEP 491 Synchronize Virtual Threads without Pinning(Java 24) <https://openjdk.org/jeps/491>
  - Java SE `Executors.newFixedThreadPool` — "shared unbounded queue" <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Executors.html>
  - Apache Tomcat HTTP Connector — `maxThreads` 200, `maxConnections` NIO 8192 <https://tomcat.apache.org/tomcat-10.1-doc/config/http.html>
  - Netty 4.1 `MultithreadEventLoopGroup`(기본 CPU×2) <https://github.com/netty/netty/blob/4.1/transport/src/main/java/io/netty/channel/MultithreadEventLoopGroup.java>
  - nginx `ngx_core_module` — `worker_processes`(기본 1, `auto`) <https://nginx.org/en/docs/ngx_core_module.html#worker_processes>, `accept_mutex`(기본 off) <https://nginx.org/en/docs/ngx_core_module.html#accept_mutex>, CHANGES 1.11.3(accept_mutex off 기본, EPOLLEXCLUSIVE) <https://nginx.org/en/CHANGES>, `listen ... reuseport` <https://nginx.org/en/docs/http/ngx_http_core_module.html#listen>
  - Microsoft Learn "I/O Completion Ports" — FIFO 패킷 큐, LIFO 스레드 해제, concurrency value <https://learn.microsoft.com/en-us/windows/win32/fileio/i-o-completion-ports>
  - socket(7) — `SO_REUSEPORT`(3.9)의 accept 분배 <https://man7.org/linux/man-pages/man7/socket.7.html>
  - OpenJDK `LinuxAsynchronousChannelProvider.java`·`EPollPort.java` — NIO.2 비동기 채널 = epoll + 스레드 풀 <https://github.com/openjdk/jdk/tree/master/src/java.base/linux/classes/sun/nio/ch>; Windows는 `WindowsAsynchronousChannelProvider`가 `Iocp`를 만든다 <https://github.com/openjdk/jdk/tree/master/src/java.base/windows/classes/sun/nio/ch>
  - Linux `net/core/sock_reuseport.c` — `reuseport_select_sock`(BPF 또는 해시로 소켓 선택) <https://github.com/torvalds/linux/blob/master/net/core/sock_reuseport.c>
  - Reactor Netty `TcpResources`(`"reactor-" + name` 접두사)·`DefaultLoopEpoll`("epoll"), reactor-core `Schedulers.boundedElastic` Javadoc <https://github.com/reactor/reactor-netty>
  - OpenJDK `src/hotspot/share/runtime/os.hpp` — `OS_NATIVE_THREAD_CREATION_FAILED_MSG` <https://github.com/openjdk/jdk/blob/master/src/hotspot/share/runtime/os.hpp>
  - Linux `arch/x86/include/asm/page_64_types.h` — `THREAD_SIZE` <https://github.com/torvalds/linux/blob/master/arch/x86/include/asm/page_64_types.h>
  - HikariCP `HikariPool.java` `createTimeoutException()` — `elapsedMillis(startTime)` + 풀 카운트 <https://github.com/brettwooldridge/HikariCP/blob/dev/src/main/java/com/zaxxer/hikari/pool/HikariPool.java>
- 로컬 재현(리눅스 7.0, glibc, gcc 13.3): 유휴 스레드 1000개의 VmSize·VmRSS(기본 8MB 스택 vs 256KB 스택)
