# reliability/28-bulkhead — 벌크헤드: 스레드풀·커넥션 격벽 — 정리 (힌트)

## 해결하는 문제

요청 스레드·커넥션이 하나의 공용 풀이면, **가장 느린 하류**가 풀을 다 물고 나머지를 굶긴다.

```text
 공용 요청 스레드 20
 [추][추][추][추][추][추][추][추][추][추][추][추][추][추][추][추][추][추][추][추]   ← 추천 하류가 1초씩 붙든다
 결제 요청: 빈 스레드가 없다 → 큐에서 대기 → 수 초 지연·타임아웃
 격벽(추천 4칸)
 [추][추][추][추] | [결][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ]
 추천 5번째부터는 즉시 거절(폴백) → 결제는 남은 스레드로 바로 처리
```

- *벌크헤드(bulkhead)*: 배의 칸막이벽. 자원을 용도·하류별 칸으로 나눠 한 칸의 장애가 다른 칸으로 번지지 않게 하는 패턴.
- *자원 고갈(resource exhaustion)*: 스레드·커넥션·메모리 같은 유한 자원이 바닥나 새 작업을 시작하지 못하는 상태.

쉬운 예: 응급실 침대를 경증 환자가 다 차지하면 응급 환자가 못 눕는다. 그래서 응급 전용 침대를 따로 둔다.\
똑같은 구조다.\
실무 예: 결제 API와 추천 API가 같은 톰캣 스레드 풀·같은 HTTP 커넥션 풀을 쓰다가, 추천 서버 지연 하나로 결제까지 타임아웃 나는 사고.

10(서킷 브레이커)은 하류가 아프다는 것을 **배운 뒤** 끊는다. 느린 호출 비율(Resilience4j의 slow call rate)도 호출이 끝나야 기록된다. 배우기 전, 그리고 느린 호출이 끝나기 전까지 스레드를 붙드는 동안의 번짐은 벌크헤드가 막는다.\
기초(공용·고정·탄력 세 구현, 세마포어 release의 함정, 보장 vs 최대)는 원본 [ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md) 「동작·원리」에 있다.\
이 노트는 스레드 고갈을 실제로 재현하고, Resilience4j·Hystrix의 두 격리 방식과 "격벽 안에서 기다리기"의 함정을 더한다.

## 동작·원리

### 1. 격리 방식 둘

```text
 세마포어 격벽 (호출자 스레드에서 실행)          스레드풀 격벽 (전용 스레드에서 실행)
 요청 스레드 ─ [허가 4개] ─> 하류 호출           요청 스레드 ─ submit ─> [전용 스레드 4 + 큐 10] ─> 하류
   허가 없으면 즉시 거절(또는 대기)               큐 가득이면 거절. 호출자는 Future를 기다리다
   호출 중에는 요청 스레드가 묶인다                시간이 되면 떠날 수 있다(전용 스레드는 계속 일함)
```

- *세마포어(semaphore)*: "동시에 N개까지"를 세는 동기화 도구. 원리는 [os/18-semaphores](../../os/18-semaphores/2-summary.md).
- Resilience4j 문서: 두 구현이 있다. `SemaphoreBulkhead`(세마포어)와 `FixedThreadPoolBulkhead`(고정 스레드 풀 + 유한 큐).
  - SemaphoreBulkhead는 Hystrix와 달리 "그림자" 스레드 풀을 두지 않는다. 스레드 풀 크기를 격벽 설정과 맞추는 것은 사용자 몫이라고 적는다.
- Hystrix 위키("How it Works"): 하류별 스레드 풀로 격리하면 호출자(톰캣 스레드)가 오래 걸리는 호출에서 **떠날 수 있다**. 대가는 큐잉·스케줄링·컨텍스트 스위칭 비용이다.
  - 같은 위키: JVM에서는 늦은 스레드를 강제로 멈출 수 없고 `InterruptedException`을 던지는 것이 최선이다. HTTP 클라이언트 대부분이 인터럽트를 해석하지 않으니 커넥션·읽기 타임아웃을 꼭 설정하라고 적는다.
  - Hystrix는 유지보수 모드다(GitHub README).

### 2. Resilience4j 2.4.0 기본값 — 라이브러리에서 직접 출력

(실험, Resilience4j 2.4.0, JDK 21 temurin `--cpus=2`, `scratchpad/rel/06/e28/Bh.java`, 2026-10-01)

```text
Resilience4j 2.4.0 BulkheadConfig.ofDefaults(): maxConcurrentCalls=25 maxWaitDuration=PT0S fairCallHandlingEnabled=true
ThreadPoolBulkheadConfig.ofDefaults(): coreThreadPoolSize=1 maxThreadPoolSize=2 queueCapacity=100 keepAliveDuration=PT0.02S (이 JVM availableProcessors=2)
```

- 세마포어 격벽: 동시 25, 대기 0(허가가 없으면 즉시 `BulkheadFullException`).
- 스레드풀 격벽: 코어 = 프로세서 수 − 1(프로세서가 1개면 1 — 2.4.0 소스), 최대 = 프로세서 수(문서 기본값 표). 이 실험은 `--cpus=2`라 1·2였다. **기본값이 실행 기계의 CPU 수에 따라 바뀐다.** 큐 100.

### 실험: 느린 하류 하나가 요청 스레드를 다 먹는다

- 요청 스레드 20개(톰캣 `maxThreads` 흉내, 큐 무제한).
- 추천 하류 1000ms, 결제 처리 10ms.
- 500ms 동안 추천 100건 + 결제 25건이 섞여 도착한다.
- 변형 넷: 격벽 없음 / 추천 세마포어 격벽 4(대기 0) / 추천 전용 풀 4 + 큐 10(호출자 200ms 뒤 포기) / 추천 세마포어 격벽 4(대기 2초).

```java
// 변형 2 — 요청 스레드 안에서 추천 호출을 세마포어 격벽으로 감싼다
Bulkhead recBh = Bulkhead.of("rec", BulkheadConfig.custom()
    .maxConcurrentCalls(4).maxWaitDuration(Duration.ZERO).build());
try { recBh.executeRunnable(() -> recommendClient.call()); }
catch (BulkheadFullException e) { /* 폴백: 추천 칸 비우기 */ }

// 변형 3 — 추천 전용 풀(4 스레드, 큐 10, 넘치면 거절) + 호출자는 200ms만 기다린다
ThreadPoolExecutor recPool = new ThreadPoolExecutor(4, 4, 0, TimeUnit.MILLISECONDS,
    new ArrayBlockingQueue<>(10), new ThreadPoolExecutor.AbortPolicy());
recPool.submit(call).get(200, TimeUnit.MILLISECONDS);   // TimeoutException → 폴백
```

(실험, 같은 환경, 2026-10-01 — 결제 25건이라 p99 = max. 실행마다 조금 다르다. 집필 6회(변형 3은 4회)·점검 3회에서 1) p50 1801~1808ms, 2) max 15~25ms, 3) max 10~11ms, 4) p50 4727~4733ms)

```text
요청 스레드 20개, 추천 1000ms·결제 10ms, 500ms 동안 추천 100 + 결제 25 도착
1) 공유 풀만(격벽 없음)                    결제 25건 지연 p50= 1807ms p99= 4493ms max= 4493ms | 추천 성공 100 거절   0 | 전체 5138ms
2) 추천 세마포어 격벽 4, 대기 0              결제 25건 지연 p50=   10ms p99=   18ms max=   18ms | 추천 성공   4 거절  96 | 전체 1015ms
   (호출자 200ms 포기 14건, 끝난 시점 전용 풀 활성 4·큐 10 — 포기해도 풀 스레드는 계속 잔다)
3) 추천 전용 풀 4 + 큐 10, 200ms 포기      결제 25건 지연 p50=   10ms p99=   10ms max=   10ms | 추천 성공   0 거절  86 | 전체 536ms
4) 추천 세마포어 격벽 4, 대기 2s             결제 25건 지연 p50= 4731ms p99=10492ms max=10492ms | 추천 성공  52 거절  48 | 전체 13017ms
```

- 관찰 1 — 격벽 없음: 결제 처리 자체는 10ms인데 p50이 1.8초, 최대 4.5초다. 스레드 20개가 추천에 물려 결제가 큐에서 기다렸다.
- 관찰 2 — 세마포어 격벽(대기 0): 결제 p50 10ms. 추천은 4건만 하류로 가고 96건은 즉시 거절됐다. 요청 스레드가 바로 풀렸다.
- 관찰 3 — 전용 풀 + 호출자 포기: 결제는 10ms. 추천은 14건(실행 4 + 큐 10)이 200ms 뒤 포기, 86건 거절.
  - **호출자가 떠나도 이미 받은 작업은 취소되지 않았다**(끝난 시점 전용 풀 실행 중 4·큐 대기 10). 거절된 86건은 하류에 가지 않았다. 포기한 14건 중 실행 중 4건은 하류 호출을 이어 가고, 큐의 10건도 취소되지 않았으니 차례가 오면 하류를 부른다(관측은 끝난 시점의 활성·큐 수까지). 하류 호출 자체의 타임아웃이 따로 필요하다(Hystrix 위키의 경고와 같다).
- 관찰 4 — 격벽 안에서 2초 기다리기: **격벽이 없을 때보다 나쁘다**(p50 4.7초, max 10.5초). 허가를 기다리는 요청 스레드도 스레드를 붙든다. 기다림이 스레드 고갈을 그대로 되살렸다.
- 실행 조건: `--cpus=2` 컨테이너, 하류는 `Thread.sleep`으로 흉내. 수치는 이 환경의 값이다.

### 3. 격벽을 어디에 두나 — 병목 자원과 같은 자리

```text
 요청 스레드 ─> [격벽: 결제 10칸] ─> HTTP 커넥션 풀(결제용 5) ─> PG
                     ↑ 칸 10인데 아래 커넥션이 5 → 칸을 얻은 5건이 커넥션을 기다리며 칸 안에서 막힌다
```

- 칸 수가 아래 자원(커넥션 풀·DB 커넥션)보다 크면 격벽 안에서 같은 고갈이 난다(원본 장애 1).
- 그래서 하류별로 **커넥션 풀 자체를 나누는 것**도 벌크헤드다. HTTP 클라이언트 인스턴스를 하류마다 따로 만들고 각 풀 상한을 둔다. DB도 업무별(OLTP·배치·리포트) 커넥션 풀을 나눈다.
- Envoy의 클러스터별 동시성 상한(`max_connections`·`max_pending_requests`·`max_requests`, 기본 1024 — Envoy `circuit_breaker.proto` 문서)은 이름은 circuit breaking이지만 하는 일은 하류(클러스터)별 격벽이다.
- 더 큰 단위: 인스턴스 풀 분리(중요 고객 전용 서버), 셀 아키텍처, 컨테이너 CPU·메모리 한도. 쿠버네티스 requests/limits는 원본 「쓰이는 자료구조」에 있다.

## 쓰이는 자료구조·알고리즘

- **카운팅 세마포어** — 칸 하나 = 허가 N개. `java.util.concurrent.Semaphore`. [os/18-semaphores](../../os/18-semaphores/2-summary.md), 원본의 `release` 이중 반납 함정.
- **유한 큐 + 거절 정책** — 스레드풀 격벽. `ArrayBlockingQueue(10)` + `AbortPolicy`. 무한 큐(`LinkedBlockingQueue` 기본)는 스레드 대신 큐에 쌓을 뿐이다(12 backpressure).
- **스레드 풀** — 고정 크기 작업자 + 작업 큐. 스레드·컨텍스트 스위치 비용은 [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md).
- **해시맵 이름 → 칸** — 하류 이름별 격벽 레지스트리(`BulkheadRegistry`). 모르는 이름을 어떻게 다룰지는 원본 「동작 — FixedBulkhead」의 설계 결정. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **Little's Law로 칸 수 잡기** — 평균 동시 칸 ≈ 도착률 × **평균** 하류 지연. 예: 추천 초당 50건 × 평균 0.2초 = 10칸(예시). p99 같은 꼬리 지연을 곱하면 Little's Law 값이 아니라 여유를 둔 보수적 추정이다. 21 scaling-principles.

## 적용 — 풀어나가는 법

### 1. 순서

1. **격리 단위**: 중요도와 장애 상관관계로 나눈다. "없어도 되는 것(추천)"과 "죽으면 안 되는 것(결제)"을 같은 칸에 두지 않는다.
2. **병목 자원 찾기**: 요청 스레드인가, 하류별 커넥션 풀인가, DB 커넥션인가. 격벽은 병목과 같은 자리에 둔다.
3. **칸 수**: Little's Law(도착률 × 정상 지연)에 여유를 두고, 아래 자원 수를 넘지 않게.
4. **대기**: 기본은 대기 0(즉시 거절). 기다리면 실험 4처럼 스레드가 다시 묶인다.
5. **거절 처리**: `BulkheadFullException` → 폴백·503. Resilience4j 기본 설정의 브레이커는 받은 예외를 모두 실패로 센다. 그래서 `ignoreExceptions(BulkheadFullException.class)`로 빼거나, 브레이커가 이 예외를 받지 않게 배치한다(10).
6. **칸 안 시간 상한**: 하류 호출 타임아웃. 칸은 "몇 개"만 막지 "얼마나 오래"는 막지 않는다.

### 2. 코드 (Java, Resilience4j 2.x + 하류별 HTTP 클라이언트)

```java
// 하류별 격벽 — 결제는 넉넉히, 추천은 작게
BulkheadRegistry reg = BulkheadRegistry.ofDefaults();
Bulkhead payBh = reg.bulkhead("pg",  BulkheadConfig.custom().maxConcurrentCalls(20).maxWaitDuration(Duration.ZERO).build());
Bulkhead recBh = reg.bulkhead("rec", BulkheadConfig.custom().maxConcurrentCalls(4).maxWaitDuration(Duration.ZERO).build());

// 하류별 HTTP 클라이언트 = 하류별 커넥션 풀 (JDK HttpClient는 빌더에 동시 연결 수 상한 설정이 없어 예시로 Apache HttpClient 5 사용)
PoolingHttpClientConnectionManager recCm = PoolingHttpClientConnectionManagerBuilder.create()
    .setMaxConnTotal(4).setMaxConnPerRoute(4).build();
CloseableHttpClient recHttp = HttpClients.custom().setConnectionManager(recCm)
    .setDefaultRequestConfig(RequestConfig.custom().setResponseTimeout(Timeout.ofMilliseconds(300)).build())
    .build();

List<Item> recommend(long userId) {
    try { return recBh.executeSupplier(() -> callRecommend(recHttp, userId)); }
    catch (BulkheadFullException e) { return List.of(); }        // 폴백
}
```

- 격벽 칸(4) = 커넥션 풀 상한(4)으로 맞췄다. 응답 타임아웃(`setResponseTimeout`)은 **응답을 기다리는 구간만** 묶는다. 칸 안 시간 전체를 묶으려면 풀에서 커넥션을 빌리는 대기(`setConnectionRequestTimeout`, HttpClient 5 문서 기본 3분)와 연결 수립(`ConnectionConfig`의 `setConnectTimeout`)에도 타임아웃을 주고, 재시도까지 감싸는 호출 전체 데드라인을 둔다(05).
- Spring Boot + Resilience4j라면 `resilience4j.bulkhead.instances.rec.max-concurrent-calls=4`, `max-wait-duration=0` 같은 속성으로 같은 설정을 한다.

### 3. 진단

- 스레드 덤프에서 요청 스레드가 어디에 묶였나 센다.

```sh
jcmd <pid> Thread.print | grep -A3 'http-nio' | grep -E 'at .*(Recommend|socketRead|Semaphore)' | sort | uniq -c | sort -rn | head
```

- 톰캣 스레드 사용률: Micrometer `tomcat_threads_busy_threads` / `tomcat_threads_config_max_threads`.
- 격벽 지표: `resilience4j_bulkhead_available_concurrent_calls`(남은 칸), `resilience4j_bulkhead_max_allowed_concurrent_calls`(칸 수) — resilience4j-micrometer master 소스 `BulkheadMetricNames`(2026-10-01 열람)의 `resilience4j.bulkhead.available.concurrent.calls`를 Prometheus 표기로 바꾼 이름.
- 커넥션 풀: HikariCP `hikaricp_connections_pending`(커넥션을 기다리는 스레드 수).

## 장애 시나리오와 대처

### 1. 공유 풀 하나 → 느린 의존성 하나가 전체 스레드 점유 (⚠ 커리큘럼)

- 현상: 추천 하류만 느려졌는데 결제·로그인까지 느려지고 타임아웃 난다.
- 보이는 형태: 톰캣 busy 스레드 = max. 스레드 덤프 대부분이 추천 호출의 소켓 읽기에서 대기. 결제 서버 쪽 지표는 정상.
- 원인: 요청 스레드 풀(또는 공용 HTTP 커넥션 풀) 하나를 모든 하류가 나눠 쓴다. 실험 1: 결제 처리 10ms인데 p50 1.8초, 최대 4.5초.
- 대처: 하류별 세마포어 격벽(대기 0) + 하류별 커넥션 풀. 실험 2: 결제 p50 10ms.

### 2. 격벽 안에서 기다리게 해서 격벽이 소용없다

- 현상: 격벽을 넣었는데도 스레드 고갈이 그대로다. 오히려 지연이 더 길다.
- 보이는 형태: 스레드 덤프에 `Semaphore.tryAcquire`(타임아웃 대기)에서 멈춘 요청 스레드가 가득.
- 원인: `maxWaitDuration`을 길게 줬다. 허가를 기다리는 스레드도 요청 스레드다. 실험 4: 격벽 없음보다 나쁜 p50 4.7초.
- 대처: 대기 0(즉시 거절) + 폴백. 기다려야 하면 아주 짧게, 호출자 데드라인 안에서.

### 3. 호출자는 떠났는데 전용 풀은 계속 하류를 부른다

- 현상: 스레드풀 격벽으로 응답은 빨라졌는데, 호출자가 포기한 호출의 하류 부하는 줄지 않는다(거절된 호출만 줄어든다). 전용 풀은 늘 가득.
- 보이는 형태: 호출자 쪽 타임아웃 로그가 많은데 하류 접근 로그에는 같은 수의 요청이 끝까지 처리된다.
- 원인: `Future.get(timeout)`은 호출자만 놓아 준다. 이미 받은 작업은 계속된다(실험 3: 포기 후에도 실행 중 4·큐 대기 10). JVM은 스레드를 강제로 멈출 수 없다(Hystrix 위키).
- 대처: 하류 호출 자체에 타임아웃(연결·응답)을 건다. 포기할 때 `future.cancel(true)`로 인터럽트하고, 인터럽트에 반응하는 클라이언트를 쓴다(09 cancellation-propagation).

### 4. 칸 수가 아래 자원보다 크다

- 현상: 격벽 거절은 0인데 결제가 여전히 타임아웃.
- 보이는 형태: `BulkheadFullException` 없음. HikariCP `Connection is not available, request timed out` 또는 HTTP 커넥션 풀 대기 시간 초과.
- 원인: 칸은 10인데 그 하류의 커넥션 풀은 5. 칸을 얻은 요청이 커넥션을 기다리며 칸 안에서 막힌다.
- 대처: 칸 수 ≤ 하류별 커넥션 수. 또는 커넥션 풀 자체를 격벽으로 삼는다.

### 5. 스레드풀 격벽 기본값이 기계마다 다르다

- 현상: 개발 PC에서는 괜찮았는데 2코어 컨테이너에서 추천이 거의 다 거절·지연된다.
- 보이는 형태: `ThreadPoolBulkhead` 지표에서 스레드 1~2개, 큐가 가득.
- 원인: Resilience4j 기본 코어·최대 스레드가 `availableProcessors` 기준이다(실험 출력: 2코어에서 1·2). I/O 대기 하류에는 너무 작다.
- 대처: 코어·최대·큐를 명시한다. CPU 수가 아니라 Little's Law(도착률 × 지연)로 정한다.

## 핵심 문장

- 벌크헤드는 하류를 고치지 않는다. 한 하류의 느림이 다른 기능으로 번지는 것을 막는다.
- 공용 요청 스레드 20개에서 1초짜리 추천 100건이 몰리자 10ms짜리 결제의 p50이 1.8초가 됐다. 추천에 세마포어 4칸(대기 0)을 주자 결제 p50이 10ms로 돌아왔다.
- 격벽 안에서 기다리게 하면 기다리는 스레드가 다시 자원을 붙든다. 대기 2초 격벽은 격벽이 없을 때보다 나빴다.
- 스레드풀 격벽에서 호출자가 떠나도 이미 받은 작업은 취소되지 않고 하류 호출을 이어 간다. 하류 호출 자체의 타임아웃과 취소가 따로 필요하다.
- 격벽은 병목 자원과 같은 자리에 둔다. 칸 수가 아래 커넥션 수보다 크면 칸 안에서 같은 고갈이 난다.

## 관련 주제·근거

- 선행
  - [10-circuit-breaker](../10-circuit-breaker/2-summary.md) — 배운 뒤 끊기. `BulkheadFullException`은 기본 설정이면 브레이커 실패로 세므로 `ignoreExceptions`로 뺀다
  - [os/18-semaphores](../../os/18-semaphores/2-summary.md) — 카운팅 세마포어
- 원본
  - [ops-patterns/03-bulkhead](../../ops-patterns/03-bulkhead/2-summary.md) — SharedPool·FixedBulkhead·ElasticBulkhead 구현, 이중 반납·반납 누락, 보장 vs 최대, IsolationTest
- 후속·연결
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 재시도 대기가 칸을 오래 붙든다
  - [11-rate-limiter](../11-rate-limiter/2-summary.md) — 들어오는 쪽에서 막기
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 유한 큐와 거절
  - [21-scaling-principles](../21-scaling-principles/2-summary.md) — Little's Law
  - [09-cancellation-propagation](../09-cancellation-propagation/2-summary.md)
  - [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md) — 스레드 풀의 비용
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 느림을 실패로 바꾸는 타임아웃
- 글·문서
  - Michael Nygard, 『Release It!』 2판(2018) 「Stability Patterns」 장의 Bulkheads 절 — pragprog 목차로 절 위치만 확인, 본문은 열람하지 못했다 [?] <https://pragprog.com/titles/mnee2/release-it-second-edition/>
  - Resilience4j Bulkhead 문서(SemaphoreBulkhead·FixedThreadPoolBulkhead, 기본값 표: 25·0, 코어=프로세서−1·최대=프로세서) <https://resilience4j.readme.io/docs/bulkhead> · 2.4.0 소스 `ThreadPoolBulkheadConfig.java`(코어 = `availableProcessors > 1 ? n−1 : 1`)
  - Resilience4j 2.4.0 소스 `CircuitBreakerConfig.java` — `DEFAULT_RECORD_EXCEPTION_PREDICATE = throwable -> true`(모든 예외를 실패로 기록), slow call 기본 100%·60초
  - Apache HttpClient 5 `RequestConfig.Builder` API(응답·커넥션 대여 타임아웃) <https://hc.apache.org/httpcomponents-client-5.6.x/current/httpclient5/apidocs/org/apache/hc/client5/http/config/RequestConfig.Builder.html>
  - Netflix Hystrix 위키 "How it Works" — Isolation(스레드 풀 격리의 이점·비용, 인터럽트로 멈출 수 없음) <https://github.com/Netflix/Hystrix/wiki/How-it-Works> · README(유지보수 모드)
  - Envoy circuit breaking(클러스터별 동시성 상한) <https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking>
- 실험 목록 (코드: scratchpad `rel/06/e28/Bh.java`, Resilience4j 2.4.0, JDK 21 temurin `--cpus=2`)
  - 기본값 출력 — `BulkheadConfig`·`ThreadPoolBulkheadConfig.ofDefaults()`
  - 요청 스레드 20 + 추천 1초 100건 + 결제 10ms 25건: 격벽 없음 / 세마포어 4·대기 0 / 전용 풀 4+큐 10·200ms 포기 / 세마포어 4·대기 2초 (집필 6회(변형 3은 4회) + 점검 3회)
