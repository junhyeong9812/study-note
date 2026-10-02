# reliability/39-async-io-gains-and-limits — 비동기·논블로킹·가상 스레드가 주는 것과 못 주는 것 — 정리 (힌트)

## 해결하는 문제

"리액티브로 바꾸면 빨라진다", "가상 스레드를 켜면 빨라진다"는 기대가 흔하다.\
실제로 늘어나는 것은 **동시에 붙잡을 수 있는 요청 수(동시성)**이고, 그래서 I/O 대기가 병목이고 하류·CPU에 여유가 있으면 **처리량**이 는다. 한 요청이 실행되는 시간(서비스 시간)은 줄지 않는다. 줄 서서 기다리던 시간이 사라지면 대기 포함 지연은 줄 수 있지만, 운반 스레드·하류 경합이 생기면 오히려 늘 수도 있다(실험 A).\
이 경계를 모르면 바꾼 뒤에 "더 느려졌다", "DB가 터졌다", "메모리가 폭증했다"를 만난다.

쉬운 예: 식당 종업원이다.
- 종업원(스레드)이 주문을 받고 주방(DB·외부 API)에서 음식이 나올 때까지 테이블 옆에 서서 기다린다. 종업원 10명이면 동시에 10 테이블만 받는다.
- 종업원이 주문을 넣고 다른 테이블로 간다(논블로킹·가상 스레드). 같은 10명이 100 테이블을 받는다. 처리량이 는다.
- 하지만 음식이 나오는 시간(지연)은 그대로다. 주방이 화구 10개뿐이면(DB 커넥션 풀) 이제 주방 앞에 줄이 선다.
- 손님이 음식을 직접 요리하는 식당(CPU 계산)이라면 종업원을 어떻게 굴려도 화구 수(코어 수)가 상한이다.

똑같은 구조다.\
실무 예: Spring MVC → WebFlux 전환, 스레드 풀 → 가상 스레드(Spring Boot 3.2+ · Java 21+에서 `spring.threads.virtual.enabled=true` — 자동 구성된 실행기에 적용되고, 직접 정의한 실행기는 따로 확인한다. Spring Boot 문서 "Task Execution and Scheduling", 3.2.0 설정 메타데이터에 처음 등장), `CompletableFuture` 팬아웃, Node.js 이벤트 루프.

## 동작·원리

### 1. Little's Law로 보는 이득 — 늘어나는 것은 L이다

```text
 처리량 X = 동시에 처리 중인 건수 L / 한 건의 체류 시간 W

 블로킹 + 스레드 풀 200                    가상 스레드(또는 논블로킹)
 ┌ 스레드 200개 ┐                          ┌ 동시 작업 수천 개 ┐
 │ 각자 I/O를   │  L ≤ 200                 │ I/O 대기 중에는     │  L이 스레드 수에 묶이지 않음
 │ 기다리며 점유 │  X ≤ 200 / W              │ OS 스레드를 반납    │  X ≤ (하류·CPU가 허락하는 만큼)
 └─────────────┘                          └──────────────────┘
       W(한 건의 서비스 시간)는 둘 다 같다 — 하류가 100ms면 100ms
```

- 경계 주의: 여기서 L은 **실행 중인** 건수, W는 실행 시간(큐 대기 제외)이다. 그래서 200 / 0.1초 = 2,000 건/s는 실행 단계의 용량이다. 제출~완료 시간(큐 대기 포함)에 Little's Law를 쓰려면 L에도 실행기 큐에서 기다리는 건을 넣어야 한다.

- JEP 444는 이 관계를 그대로 쓴다. 서버의 확장성은 Little's Law가 지배한다. 지연이 같다면 처리량을 늘리려면 동시 처리 건수가 비례해 늘어야 한다.
- 같은 JEP의 문장: 가상 스레드는 더 빠른 스레드가 아니다. **속도(낮은 지연)가 아니라 규모(높은 처리량)**를 위해 있다.
  - *가상 스레드(virtual thread)*: JDK가 만드는 가벼운 스레드. 블로킹 I/O를 만나면 JDK가 그 가상 스레드를 *운반 스레드(carrier — 실제 OS 스레드)*에서 내려놓고 다른 가상 스레드를 올린다(JDK 21, JEP 444).
  - *논블로킹 I/O*: I/O가 끝날 때까지 기다리지 않고 바로 돌아오는 호출. 완료는 이벤트·콜백으로 받는다([os/25-io-models](../../os/25-io-models/2-summary.md), [os/26-io-multiplexing-epoll](../../os/26-io-multiplexing-epoll/2-summary.md)).
- JEP 444가 적은 이득 조건 두 가지
  1. 동시 작업 수가 많다(수천 이상).
  2. 작업이 CPU 바운드가 아니다. 코어보다 훨씬 많은 스레드는 CPU 바운드 작업의 처리량을 올리지 못한다.

### 2. 이득이 없거나 역효과가 나는 네 경우

```text
 ① CPU 바운드          코어 2개 ─ 계산 16건 ─ 스레드를 어떻게 굴려도 16 × 150ms / 2 ≈ 1.2초
 ② 블로킹 경로 혼입      이벤트 루프 스레드(몇 개뿐)에서 JDBC 호출 → 루프 전체 정지
                       가상 스레드가 synchronized 안에서 블로킹(JDK 21) → 운반 스레드 고정(pinning)
 ③ 병목이 하류로 이동     동시 요청 10배 → DB 커넥션 풀 10개는 그대로 → 커넥션 대기 타임아웃
 ④ 백프레셔 없는 팬아웃   동시 작업 수 제한 없음 → 작업마다 잡은 버퍼 × 동시 수 = 메모리
```

- ② *고정(pinning)*: 가상 스레드가 운반 스레드에서 내려오지 못하는 상태. JDK 21에서는 `synchronized` 블록·메서드 안, 또는 네이티브 메서드·외부 함수 안에서 생긴다(JEP 444).
  - 고정된 채 블로킹하면 운반 스레드와 OS 스레드도 같이 막힌다. 스케줄러는 고정을 보상하려고 병렬도를 늘리지 **않는다**(JEP 444).
  - JDK 24의 JEP 491 "Synchronize Virtual Threads without Pinning"이 `synchronized` 때문의 고정을 거의 없앴다. 네이티브 코드에서 블로킹하는 경우는 남는다.
  - 파일 시스템 연산·`Object.wait()`처럼 운반 스레드를 붙잡는 일부 블로킹은 스케줄러가 병렬도를 **임시로 늘려** 보상한다(JEP 444). 고정과 다른 경우다.
- ③ JEP 444는 동시 접근을 제한하려고 가상 스레드를 풀로 묶지 말고, **세마포어**처럼 그 목적의 도구를 쓰라고 한다.
- ④ 비동기 팬아웃은 "기다리는 동안 자원을 안 쓴다"가 아니다. 기다리는 동안에도 각 작업이 잡은 메모리(요청·응답 버퍼, 컨텍스트)는 남는다. 메모리 ≈ L × 한 건당 메모리.

### 3. 실험: 가상 스레드 — 처리량·CPU 바운드·하류 풀·고정

- 환경: Docker `--cpus=2`(availableProcessors=2, 그래서 가상 스레드 스케줄러 병렬도도 2).
- A: 100ms `Thread.sleep`(I/O 대기 흉내) 작업 1만 개. 플랫폼 스레드 풀 200 vs 가상 스레드. 작업 본문 시간(시작~끝)과 제출~완료를 따로 잰다.
- B: 약 150ms 계산 작업 16개. 플랫폼 풀 2 vs 가상 스레드.
- C: 요청 2,000건이 한꺼번에. DB 커넥션 10개(공정 세마포어), 쿼리 20ms, 커넥션 대기 한도 300ms(HikariCP `connectionTimeout` 흉내).
- D: 가상 스레드 100개가 **각자 다른** 객체의 락을 잡고 50ms 블로킹. `synchronized` vs `ReentrantLock`.

```java
// C의 핵심 — 동시성이 커져도 하류 자원(커넥션 10개)은 그대로다
if (!pool.tryAcquire(300, TimeUnit.MILLISECONDS)) {          // HikariCP connectionTimeout 흉내
    timeout.incrementAndGet();
    return null;
}
try { Thread.sleep(20); ok.incrementAndGet(); } finally { pool.release(); }

// D의 핵심 — 락은 서로 달라 경합이 없다. 차이는 "고정"뿐이다
if (kind.equals("synchronized")) { synchronized (mon) { Thread.sleep(50); } }
else { lock.lock(); try { Thread.sleep(50); } finally { lock.unlock(); } }
```

(실험, JDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-01 — 집필 3회 + 사실 점검 재실행 1회, 첫 회 출력)

```text
JDK 21.0.12+8-LTS, availableProcessors=2
A I/O 대기   플랫폼 풀 200      1만 건  5.10s →   1962 건/s | 작업 본문 p50=100ms p99=109ms | 제출~완료 p50=2515ms p99=4986ms
A I/O 대기   가상 스레드         1만 건  0.63s →  15944 건/s | 작업 본문 p50=221ms p99=332ms | 제출~완료 p50=340ms p99=402ms
B CPU 계산   플랫폼 풀 2        16건  1.20s
B CPU 계산   가상 스레드         16건  1.16s
C 하류 풀    플랫폼 풀 50       성공 2000 / 커넥션 대기 초과    0, 전체 4.07s, 응답 p50=2034ms p99=4015ms
C 하류 풀    가상 스레드         성공  160 / 커넥션 대기 초과 1840, 전체 0.58s, 응답 p50=485ms p99=564ms
    첫 오류: Connection is not available, request timed out after 300ms (흉내)
D 고정       synchronized   가상 스레드 100개 × 50ms 블로킹(락은 서로 다름) →  2.51s
D 고정       ReentrantLock  가상 스레드 100개 × 50ms 블로킹(락은 서로 다름) →  0.05s
```

- A — 처리량은 약 8배(1,962 → 15,944 건/s, 4회 범위 13,375~20,878 — 약 7~11배)로 늘었다. 플랫폼 풀은 200 / 0.1초 = 2,000 건/s가 상한이다(Little's Law).
  - **지연은 줄지 않았다.** 작업 본문 p50이 100ms → 221ms(4회 범위 105~221ms, p99 204~332ms)로 오히려 늘었다. 실행마다 차이가 크지만 100ms보다 짧아진 적은 없다.
  - 해석: 2코어에서 1만 개 가상 스레드를 만들고 깨우는 일이 운반 스레드 2개를 바쁘게 해, sleep에서 깨어난 뒤 다시 올라탈 차례를 기다린 시간이 붙었다.
  - 제출~완료가 크게 줄어든 것(2,515 → 340ms)은 **줄 서서 기다린 시간**이 없어졌기 때문이다. 한 건의 서비스 시간이 빨라진 것이 아니다.
- B — CPU 계산은 둘 다 약 1.1~1.2초(4회 1.05~1.22초)다. 16건 × 약 150ms / 코어 2 ≈ 1.2초. 가상 스레드는 이득이 없다.
- C — 가상 스레드는 2,000건을 한꺼번에 하류로 보냈다. 커넥션 10개 × (300ms / 20ms) ≈ 150건만 한도 안에 커넥션을 얻고, **1,840건(3회 1,840~1,850)이 커넥션 대기 초과**로 실패했다.
  - 플랫폼 풀 50은 동시성이 50으로 묶여 있어 커넥션 대기가 짧았다(실패 0). 대신 요청이 실행기 큐에서 기다려 p99가 4초였다. **병목(대기 장소)이 옮겨 갔을 뿐**이다.
  - 실패 요청의 응답이 300ms가 아니라 약 0.5~0.7초(4회 p50 485~698ms)인 것은 2코어에서 가상 스레드 2,000개를 시작시키는 데 걸린 시간이 더해진 것이다(해석).
- D — 같은 일인데 `synchronized` 2.51초, `ReentrantLock` 0.05초. 고정된 가상 스레드가 운반 스레드 2개를 50ms씩 붙잡아 100 × 50ms / 2 = 2.5초가 됐다.

`-Djdk.tracePinnedThreads=short`로 돌리면 고정이 일어난 자리를 찍는다(JEP 444).

(실험, JDK 21.0.12, 같은 D)

```text
VirtualThread[#15]/runnable@ForkJoinPool-1-worker-2 reason:MONITOR
    AsyncLimits.lambda$pinning$3(AsyncLimits.java:67) <== monitors:1
D 고정       synchronized   가상 스레드 100개 × 50ms 블로킹(락은 서로 다름) →  2.56s
D 고정       ReentrantLock  가상 스레드 100개 × 50ms 블로킹(락은 서로 다름) →  0.05s
```

같은 D를 JDK 25에서 돌리면 JEP 491 덕에 차이가 사라진다.

(실험, JDK 25.0.4.1 temurin, Docker `--cpus=2`, 2026-10-01)

```text
JDK 25.0.4.1+1-LTS, availableProcessors=2
D 고정       synchronized   가상 스레드 100개 × 50ms 블로킹(락은 서로 다름) →  0.11s
D 고정       ReentrantLock  가상 스레드 100개 × 50ms 블로킹(락은 서로 다름) →  0.06s
```

### 4. 실험: 백프레셔 없는 팬아웃의 메모리

- 가상 스레드로 작업 6,000개를 낸다. 작업마다 64KB 버퍼를 잡고 200ms 하류를 기다린다.
- 동시 한도 없음 vs 세마포어 1,000 vs 200(제출자가 자리가 날 때까지 기다리는 백프레셔).

```java
if (sem != null) sem.acquire();          // 백프레셔: 자리가 날 때까지 제출자가 기다린다
ex.submit(() -> {
    byte[] buf = new byte[64 * 1024];    // 하류 응답을 받을 버퍼
    Thread.sleep(200);                   // 하류 대기
    ...
    finally { if (sem != null) sem.release(); }
});
```

(실험, JDK 21.0.12, `-Xmx512m`, Docker `--cpus=2 --memory=1g`, 2026-10-01 — 2회 실행, 두 번째 출력. 메모리 1GB 제한 컨테이너라 JVM이 SerialGC를 고른다(`-XX:+PrintFlagsFinal`의 `UseSerialGC = true {ergonomic}`, 사실 점검 확인). 힙 사용은 5ms마다 잰 `totalMemory − freeMemory`의 최댓값이라 아직 회수되지 않은 쓰레기도 들어 있다)

```text
동시 한도 없음     → 완료  6000 / OOM     0, 최대 동시  3706, 걸린 시간 1.29s, 힙 사용 최대 315MB (-Xmx=494MB)
동시 한도 1000   → 완료  6000 / OOM     0, 최대 동시  1000, 걸린 시간 1.65s, 힙 사용 최대 152MB (-Xmx=494MB)
동시 한도 200    → 완료  6000 / OOM     0, 최대 동시   200, 걸린 시간 6.26s, 힙 사용 최대 39MB (-Xmx=494MB)
```

- 관찰: 최대 동시 수가 3,706 → 1,000 → 200으로 줄자 힙 최대가 315 → 152 → 39MB로 줄었다. 메모리 ≈ 동시 수 × 건당 메모리(3,706 × 64KB ≈ 232MB + 쓰레기)다.
  - 한도 없음의 최대 동시 수는 실행마다 다르다(사실 점검 재실행 2,634·3,029).
  - 사실 점검 재실행(같은 조건 `--memory=1g`): 313 → 154 → 39MB로 같은 경향이다.
  - 주의: 메모리 제한 없이(`--cpus=2`만) 돌리면 JVM이 G1을 고르고, 같은 측정이 415 → 309 → 344MB로 나와 경향이 보이지 않는다(사실 점검 재실행). G1은 힙에 여유가 있으면 쓰레기를 늦게 치우므로 `totalMemory − freeMemory`가 살아 있는 버퍼보다 쓰레기를 더 많이 잰다. 살아 있는 메모리를 보려면 GC 직후 힙(GC 로그의 after 값)을 본다. `jcmd GC.heap_info`는 호출 시점의 힙 요약이라 GC 직후 값이 아니다(JDK 21 `jcmd` 문서: "generic Java heap information").
- 대가: 한도 200이면 6,000 × 0.2초 / 200 = 6초가 걸린다(측정 6.26초). 처리량 = 한도 / W(Little's Law).
- 같은 코드를 작업 2만 개·`-Xmx256m`·한도 없음으로 돌렸을 때는 100초 안에 끝나지 않아 중단했다. 출력이 없어 원인은 확인하지 못했다(살아 있는 버퍼가 힙을 채워 GC가 회수할 것이 없는 상태로 추정 `[?]`).

## 쓰이는 자료구조·알고리즘

- **Little's Law(L = λW)** — 동시성·처리량·지연의 관계. [21-scaling-principles](../21-scaling-principles/2-summary.md), [math/10-queueing-and-littles-law](../../math/README.md)(미작성).
- **유계 큐·세마포어** — 동시 작업 수의 상한(백프레셔). JEP 444가 권하는 동시성 제한 도구. [os/18-semaphores](../../os/18-semaphores/2-summary.md), [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md).
- **작업 훔치기(work-stealing) ForkJoinPool** — JDK 가상 스레드 스케줄러. FIFO 모드로 돌고, 병렬도 기본값은 사용 가능한 프로세서 수다(`jdk.virtualThreadScheduler.parallelism`으로 조정 — JEP 444).
- **연속(continuation)과 힙의 스택 조각** — 가상 스레드의 스택은 GC 힙에 stack chunk 객체로 저장되고, 실행에 따라 늘고 준다(JEP 444). 그래서 기다리는 동안 OS 스레드를 반납할 수 있다. 대신 기다리는 동안의 지역 변수도 힙 메모리다(실험 4).
- **이벤트 루프 + epoll** — 논블로킹 서버의 구조. 루프 스레드가 몇 개뿐이라 한 번의 블로킹 호출이 전체를 막는다. [os/27-event-based-concurrency](../../os/27-event-based-concurrency/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 바꾸기 전에 묻는 순서

1. **병목이 동시성인가?** 스레드 풀이 가득 차 요청이 줄을 서는데 CPU는 한가하다(I/O 대기가 길다) → 이득 후보. CPU가 이미 바쁘다 → 이득 없음.
2. **하류가 동시성 증가를 받을 수 있나?** DB 커넥션 풀·외부 API 동시 한도·레이트 리밋. 받을 수 없으면 대기 장소만 옮겨 간다(실험 C). 하류별 세마포어 한도를 먼저 설계한다.
3. **블로킹 경로가 섞여 있나?** 이벤트 루프 위의 JDBC·파일 I/O·`synchronized` 안의 I/O(JDK 21). 가상 스레드는 JDK 21이면 고정을 찾고, 가능하면 JDK 24+로 올린다.
4. **동시 작업 수에 상한이 있나?** 팬아웃마다 세마포어나 유계 큐. 메모리 = 상한 × 건당 메모리로 계산한다.
5. **바꾼 뒤 무엇을 잴까?** 처리량, p99, 하류 대기 시간(커넥션 획득 시간), 힙·RSS, 고정 이벤트.

### 2. 가상 스레드 + 하류별 동시성 상한 (Java 21)

```java
/** 가상 스레드는 풀로 묶지 않는다. 하류 자원마다 세마포어로 동시성을 제한한다(JEP 444 권고). */
class InventoryClient {
    private final Semaphore permits = new Semaphore(20);   // 이 하류가 견디는 동시 호출 수(측정해서 정한다)

    String fetch(String sku) throws Exception {
        if (!permits.tryAcquire(200, TimeUnit.MILLISECONDS)) {
            throw new RejectedExecutionException("inventory 동시 한도 초과");   // 빠르게 거절
        }
        try {
            return http.send(request(sku), BodyHandlers.ofString()).body();   // java.net 블로킹 호출 → 가상 스레드가 내려간다
        } finally {
            permits.release();
        }
    }
}

try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(() -> handle(request));
}
```

- DB 커넥션 풀은 이미 상한이다. 가상 스레드 수 ≫ 풀 크기면 `connectionTimeout`에 걸린다. 풀을 키우기 전에 DB가 그 동시성을 감당하는지 본다([database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md)).
- HikariCP는 기본 `maximumPoolSize` 10, `connectionTimeout` 30,000ms다. 시간 안에 커넥션을 못 얻으면 `SQLException`을 던진다(HikariCP README). 소스(dev 브랜치 `HikariPool.java`)의 메시지는 `"<풀 이름> - Connection is not available, request timed out after <경과>ms (total=…, active=…, idle=…, waiting=…)"` 꼴이다.

### 3. 진단 명령

```bash
# JDK 21: 고정이 일어난 스택을 찍는다(운영에서는 비용 주의)
java -Djdk.tracePinnedThreads=short -jar app.jar
# JFR: 고정된 채 멈춘 이벤트(jdk.VirtualThreadPinned — 기본 임계 20ms, JEP 444)
jcmd <pid> JFR.start duration=60s filename=pin.jfr
jfr print --events jdk.VirtualThreadPinned pin.jfr
# 가상 스레드 덤프(JSON)
jcmd <pid> Thread.dump_to_file -format=json threads.json
```

```text
# PromQL 예 — 바꾼 뒤 하류 대기가 늘었나 (HikariCP의 Micrometer 지표)
# _bucket은 이 타이머에 퍼센타일 히스토그램을 켰을 때만 나온다(기본은 _count·_sum·_max)
histogram_quantile(0.99, sum by (le) (rate(hikaricp_connections_acquire_seconds_bucket[5m])))
hikaricp_connections_pending
```

- 지표 이름의 근원은 HikariCP 소스 `MicrometerMetricsTracker.java`(dev 브랜치)다. 획득 시간 타이머가 `hikaricp.connections.acquire`, 대기 수 게이지가 `hikaricp.connections.pending`이다. 이 타이머는 히스토그램 설정 없이 등록되므로 `_bucket`을 쓰려면 MeterFilter나 Spring Boot `management.metrics.distribution.percentiles-histogram` 설정으로 켜야 한다. Prometheus 쪽 최종 이름(`_seconds` 접미사 등)은 실제 `/actuator/prometheus` 출력에서 확인한다.

## 장애 시나리오와 대처

### 1. 리액티브로 바꿨는데 처리량이 떨어졌다 (⚠ JDBC 블로킹)

- 현상: WebFlux로 옮긴 뒤 부하가 조금만 와도 모든 요청이 느려진다.
- 보이는 형태: 이벤트 루프 스레드(예: `reactor-http-nio-*`, 리눅스 네이티브 전송이면 `reactor-http-epoll-*`) 스택이 JDBC 소켓 읽기에서 멈춰 있다. CPU는 낮고 처리 중 요청이 루프 스레드 수 근처에서 막힌다.
- 원인: 루프 스레드는 몇 개뿐이다(Reactor Netty 기본 = max(코어 수, 4) — `LoopResources.DEFAULT_IO_WORKER_COUNT`). 그 위에서 블로킹 JDBC를 부르면 루프 전체가 멈춘다. 블로킹 스레드 풀(200개)보다 동시성이 오히려 작아졌다.
- 대처: 블로킹 호출을 별도 유계 스케줄러로 옮기거나(예: Reactor `boundedElastic`), 논블로킹 드라이버(R2DBC)로 바꾸거나, 가상 스레드 + 동기 코드로 되돌린다.

### 2. 가상 스레드를 켰더니 DB 풀이 고갈됐다 (⚠)

- 현상: 가상 스레드 전환 후 피크에 `Connection is not available, request timed out after …ms` 오류가 쏟아진다.
- 보이는 형태: 커넥션 대기 수(pending)가 수백~수천, 획득 시간 p99가 `connectionTimeout`에 붙는다. 실험 C처럼 성공 160 / 실패 1,840.
- 원인: 동시 요청 수가 스레드 풀 크기(예: 200)에서 사실상 무제한으로 커졌다. DB 풀은 그대로라 대기 장소가 DB 풀 앞으로 옮겨 갔다.
- 대처: 하류별 세마포어로 입구에서 동시성을 제한하고 넘치면 빠르게 거절한다. 풀 크기는 DB가 감당하는 동시성으로 정한다. 요청 단위 타임아웃을 둔다.

### 3. JDK 21 가상 스레드에서 처리량이 오르지 않는다 (고정)

- 현상: 가상 스레드로 바꿨는데 동시성이 운반 스레드 수(코어 수) 근처에 묶여 있다.
- 보이는 형태: `jdk.VirtualThreadPinned` JFR 이벤트, `-Djdk.tracePinnedThreads`의 `<== monitors:1` 스택. 실험 D의 2.51초 vs 0.05초.
- 원인: `synchronized` 안에서 I/O·sleep·`BlockingQueue.take()` 같은 블로킹을 한다. 오래된 라이브러리(커넥션 풀·HTTP 클라이언트)가 자주 원인이다.
- 대처: 해당 `synchronized`를 `ReentrantLock`으로 바꾸거나, 라이브러리를 고정이 없는 버전으로 올리거나, JDK 24+(JEP 491)로 올린다. 네이티브 코드 안의 블로킹은 JDK 24+에서도 고정된다.

### 4. 비동기 팬아웃에서 메모리가 폭증했다 (⚠ 백프레셔 없음)

- 현상: 배치가 100만 건을 `CompletableFuture`/가상 스레드로 한꺼번에 하류에 보내자 힙이 차고 GC가 멈추지 않는다.
- 보이는 형태: 힙 사용이 동시 작업 수에 비례해 오른다. GC 로그에 Full GC 연속, 결국 `OutOfMemoryError`. 실험 4의 315MB vs 39MB.
- 원인: 동시 작업 수에 상한이 없다. 기다리는 동안에도 작업마다 잡은 버퍼가 남는다.
- 대처: 세마포어·유계 큐로 동시 수를 정하고(메모리 = 상한 × 건당), 결과를 모아 두지 말고 흘려 보낸다(스트리밍). 처리 시간은 건수 × W / 상한으로 계산해 받아들인다.

### 5. CPU 바운드 서비스에 가상 스레드를 적용했다

- 현상: 전환 후 처리량 변화가 없다. 기대했던 개선이 안 나온다.
- 보이는 형태: CPU 사용률이 이미 높다. 실험 B처럼 두 방식의 시간이 같다.
- 원인: CPU 바운드는 코어 수가 상한이다. 스레드 수를 늘려도 계산이 빨라지지 않는다(JEP 444).
- 대처: 알고리즘·데이터 구조 개선, 프로파일링([36-profiling](../36-profiling/2-summary.md)), 코어 추가. 가상 스레드는 I/O 대기 비율이 높은 경로에만 쓴다.

## 핵심 문장

- 비동기·논블로킹·가상 스레드가 늘려 주는 것은 동시성(L)이고, 그래서 I/O 대기가 병목이면 처리량(X = L/W)이 는다(하류·CPU가 상한이면 늘지 않는다). 한 건의 서비스 시간(W)은 줄지 않는다(JEP 444: "scale, not speed"). 줄던 대기 시간은 사라질 수 있다.
- 실험에서 I/O 대기 작업의 처리량은 약 8배 늘었지만, 작업 본문 시간은 100ms보다 오히려 길어졌다. CPU 계산 작업은 이득이 없었다.
- 동시성이 늘면 병목은 하류 풀로 옮겨 간다. 실험에서 DB 커넥션 10개 앞에서 2,000건 중 1,840건이 커넥션 대기 초과로 실패했다. 하류마다 세마포어로 상한을 둔다.
- JDK 21 가상 스레드는 `synchronized` 안에서 블로킹하면 운반 스레드를 고정한다(실험 2.51초 vs 0.05초). JDK 24의 JEP 491이 이를 거의 없앴다(JDK 25 실험 0.11초).
- 백프레셔 없는 팬아웃은 메모리 = 동시 수 × 건당 메모리다. 상한을 두면 메모리가 줄고 처리 시간은 건수 × W / 상한이 된다.

## 관련 주제·근거

- 선행
  - [language/14-concurrency-models](../../language/README.md) — 미작성(스레드·async/await·가상 스레드 일반)
  - [os/25-io-models](../../os/25-io-models/2-summary.md) — 블로킹·논블로킹·비동기 I/O 구분
  - [math/10-queueing-and-littles-law](../../math/README.md) — 미작성(Little's Law는 [21-scaling-principles](../21-scaling-principles/2-summary.md))
  - [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md) — 풀 크기·획득 타임아웃
- 후속·연결
  - [os/26-io-multiplexing-epoll](../../os/26-io-multiplexing-epoll/2-summary.md), [os/27-event-based-concurrency](../../os/27-event-based-concurrency/2-summary.md), [os/36-server-concurrency-architectures](../../os/36-server-concurrency-architectures/2-summary.md)
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) · [28-bulkhead](../28-bulkhead/2-summary.md) · [40-batching-and-round-trips](../40-batching-and-round-trips/2-summary.md)
  - [52-reliability-symptom-index](../52-reliability-symptom-index/2-summary.md)의 "비동기 전환 후 더 느림"
- 문서·소스
  - JEP 444 "Virtual Threads"(JDK 21) — Motivation(Little's Law), "scale (higher throughput), not speed (lower latency)", 이득 조건 두 가지, Do not pool virtual threads(세마포어), Scheduling(work-stealing ForkJoinPool·FIFO·병렬도), Pinning(synchronized·native, 보상 없음), `jdk.tracePinnedThreads`, `jdk.VirtualThreadPinned`(임계 20ms) <https://openjdk.org/jeps/444>
  - JEP 491 "Synchronize Virtual Threads without Pinning"(JDK 24) — synchronized 고정 제거, 네이티브 고정은 남음 <https://openjdk.org/jeps/491>
  - HikariCP README(`connectionTimeout` 기본 30,000ms·최소 250ms, `maximumPoolSize` 기본 10), `src/main/java/com/zaxxer/hikari/pool/HikariPool.java`(dev 브랜치, 타임아웃 메시지), `src/main/java/com/zaxxer/hikari/metrics/micrometer/MicrometerMetricsTracker.java`(지표 이름) <https://github.com/brettwooldridge/HikariCP>
  - Reactor Netty `reactor-netty-core/src/main/java/reactor/netty/resources/LoopResources.java`(`DEFAULT_IO_WORKER_COUNT` = max(availableProcessors, 4))
  - J. D. C. Little, "A Proof for the Queuing Formula: L = λW", 1961
- 실험 목록
  - E39-A~D `AsyncLimits.java`: I/O 1만 건(풀 200 vs 가상), CPU 16건(풀 2 vs 가상), 하류 풀 10·대기 300ms(풀 50 vs 가상), 고정(synchronized vs ReentrantLock) — JDK 21.0.12 3회, D는 JDK 25.0.4.1에서도, `-Djdk.tracePinnedThreads=short` 1회. Docker `--cpus=2`
  - E39-E `FanOut.java`: 가상 스레드 6,000건 × 64KB 버퍼 × 200ms, 동시 한도 없음/1,000/200 — JDK 21.0.12 `-Xmx512m`, Docker `--cpus=2 --memory=1g`(SerialGC), 2회 + 사실 점검 재실행(`--memory=1g` 1회, 메모리 제한 없음(G1) 1회)
