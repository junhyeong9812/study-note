# reliability/48-performance-and-stability-antipatterns-in-code — 코드 수준 성능·안정성 안티패턴 — 정리 (힌트)

## 해결하는 문제

테스트와 코드 리뷰를 통과한 코드가, 트래픽이나 데이터가 커진 어느 날 서비스를 멈춘다.\
문법도 로직도 틀리지 않았다. **규모가 커질 때만** 드러나는 모양이 몇 가지 반복된다. 그 모양에 이름을 붙여 두면 리뷰와 진단에서 빨리 찾는다.

```text
 개발·테스트 환경                         운영 (데이터 100배, 동시 요청 100배)
 요청마다 new HttpClient  → 문제없음        → 소켓·스레드 수천 개, TIME_WAIT 폭증, connect 실패
 SELECT * FROM orders     → 200행          → 2000만 행을 힙에 올림 → OOM
 외부 호출에 타임아웃 없음  → 늘 빠름          → 외부가 느려지는 날 요청 스레드 전부 묶임 → 헬스체크까지 실패
 자정에 전 서버가 배치 시작 → 서버 1대         → 서버 200대가 같은 초에 DB를 때림
```

- *안티패턴(antipattern)*: 흔히 쓰이지만 나쁜 결과로 이어지는 해법의 모양. 이름이 있으면 "이건 Chatty I/O다"처럼 한 마디로 짚을 수 있다.

쉬운 예: 식당 주방이다.
- 접시가 필요할 때마다 새로 사 오고 쓰고 버린다(Improper Instantiation).
- 재료를 한 번에 안 가져오고 하나씩 창고를 오간다(Chatty I/O).
- 주문 하나 받을 때 창고 재고 전부를 주방으로 옮긴다(Extraneous Fetching, Unbounded Result Sets).
- 요리사 넷이 모두 한 납품업자 전화를 기다리며 서 있다(Blocked Threads). 그동안 손님이 "괜찮아요?"라고 물어도 답할 사람이 없다(헬스체크 실패).

똑같은 구조다.\
이 노트는 두 카탈로그를 코드 수준에서 묶는다.
- Microsoft Azure Architecture Center "Performance antipatterns for cloud applications"의 10개.
- Nygard 『Release It!』 2판 4장 "Stability Antipatterns"(Integration Points, Chain Reactions, Cascading Failures, Users, Blocked Threads, Self-Denial Attacks, Scaling Effects, Unbalanced Capacities, Dogpile, Force Multiplier, Slow Responses, Unbounded Result Sets — pragprog.com 목차).

설계·운영 수준의 안티패턴(인스턴스 수만큼 도는 자정 정산, 깊은 헬스체크, 증설이 DB를 죽이는 것 등)은 [47-server-design-antipatterns](../47-server-design-antipatterns/2-summary.md) 쪽이다.

## 동작·원리

### 1. 두 카탈로그를 한 지도에

```text
                 자원을 어떻게 만들고 재사용하나        한 번에 얼마나 오가나              스레드가 어디서 기다리나
 성능(Azure)     Improper Instantiation            Chatty I/O · Extraneous Fetching   Synchronous I/O · Busy Front End
                                                  No Caching
 안정성(Nygard)  ─                                  Unbounded Result Sets              Blocked Threads · Slow Responses
                                                                                      Integration Points(뿌리)
 저장소          Busy Database · Monolithic Persistence
 트래픽 모양      Self-Denial Attacks · Dogpile · Retry Storm(Azure) · Noisy Neighbor(Azure)
```

- Azure 카탈로그 10개: Busy Database, Busy Front End, Chatty I/O, Extraneous Fetching, Improper Instantiation, Monolithic Persistence, No Caching, Noisy Neighbor, Retry Storm, Synchronous I/O(2026-10-01 열람, 페이지 갱신 2026-02-03).
- Nygard는 4장 첫 항목 "Integration Points" 절에서 이렇게 말한다: 통합 지점은 시스템을 죽이는 1번 원인이고, 모든 소켓·프로세스·파이프·원격 호출은 멈출 수 있다("Integration points are the number-one killer of systems ... can and will hang" — 2판 P1.0 발췌 PDF).
  - *통합 지점(integration point)*: 내 프로세스 밖의 무언가를 부르는 자리. DB, 외부 API, 캐시, 메시지 브로커.

### 2. Improper Instantiation — 공유해야 할 객체를 요청마다 만들기

```text
 공유 클라이언트 하나                       요청마다 new HttpClient
 [client]──연결 1개 재사용──> 서버           [c1]──연결──> 서버   (c1 버려짐, 연결·스레드는 남음)
                                          [c2]──연결──>
                                          ... 300개 → 연결 300개, 스레드 수백 개
```

- Azure 문서: HTTP 클라이언트 같은 클래스는 "한 번 만들어 애플리케이션 수명 내내 재사용하도록" 설계됐다. 요청마다 만들면 부하가 클 때 소켓이 고갈될 수 있다("might exhaust the number of available sockets").
- JDK 21 `HttpClient` 문서: 클라이언트는 대개(typically) 자기 커넥션 풀을 갖고, 풀은 대개 클라이언트끼리 공유하지 않는다. 연산마다 새 클라이언트를 만들면 보통 연결을 재사용하지 못한다. `close()`는 JDK 21에 추가됐다.
- 같은 모양: JDBC 커넥션을 풀 없이 매번 열기, 요청마다 `ObjectMapper`·SSLContext·스레드 풀 만들기.

### 3. 실험: 요청마다 `new HttpClient`

- 한 JVM 안에 서버(127.0.0.1:8081)와 클라이언트를 두고 GET 300번을 순서대로 보낸다.
- `shared`: 클라이언트 하나 재사용. `new`: 요청마다 `HttpClient.newHttpClient()`, 닫지 않음. `new+close`: 요청마다 만들고 `try-with-resources`로 `close()`.
- 끝나고 0.5초 뒤 `/proc/net/tcp`·`tcp6`의 클라이언트 쪽 소켓 상태와 `Thread.activeCount()`를 센다.

```java
switch (mode) {
    case "shared"    -> shared.send(r, ofString());
    case "new"       -> HttpClient.newHttpClient().send(r, ofString());
    case "new+close" -> { try (HttpClient c = HttpClient.newHttpClient()) { c.send(r, ofString()); } }
}
```

(실험, eclipse-temurin:21-jdk, `--cpus=2`, `-Xmx256m`, 서버 `-Dsun.net.httpserver.nodelay=true`, 2026-10-01 — 집필 2회, 아래 로그)

```text
shared    300요청  1942ms | 클라이언트 쪽(포트≠8081) TCP {ESTABLISHED=1} | 스레드 15
new       300요청  3046ms | 클라이언트 쪽(포트≠8081) TCP {ESTABLISHED=200, TIME_WAIT=19} | 스레드 900
new+close 300요청  3440ms | 클라이언트 쪽(포트≠8081) TCP {TIME_WAIT=300} | 스레드 12
shared    300요청  1872ms | 클라이언트 쪽(포트≠8081) TCP {ESTABLISHED=1} | 스레드 15
new       300요청  2876ms | 클라이언트 쪽(포트≠8081) TCP {ESTABLISHED=160, TIME_WAIT=140} | 스레드 517
new+close 300요청  3161ms | 클라이언트 쪽(포트≠8081) TCP {TIME_WAIT=300} | 스레드 12
```

- 관찰 1 — `shared`: 연결 **1개**로 300요청을 처리했다.
- 관찰 2 — `new`: 열린 연결과 TIME_WAIT를 합쳐 200~300개, 스레드가 **513~900개**다(점검 재실행 2회 포함: ESTABLISHED 162·200, TIME_WAIT 138·46, 스레드 513·807). 버려진 클라이언트의 연결·스레드가 GC 전까지 남는다. 수치는 GC 시점에 따라 실행마다 다르다.
  - ESTABLISHED가 네 번 중 두 번 정확히 200에서 멈췄다. JDK `HttpServer`의 유휴 연결 상한 `sun.net.httpserver.maxIdleConnections` 기본값이 200이다(jdk21u `ServerConfig.java`). 서버가 200개 넘는 유휴 연결을 닫은 것으로 보인다(해석). 클라이언트 쪽 고유의 상한이 아니다.
- 관찰 3 — `new+close`: 스레드는 정리됐지만 TIME_WAIT가 **정확히 300**이다. 연결을 먼저 닫은 쪽(클라이언트)에 TIME_WAIT가 남는다. 같은 목적지로 초당 수백 번이면 임시 포트가 바닥나 `connect()`가 `EADDRNOTAVAIL`로 실패한다([network/20-time-wait-and-close-wait](../../network/20-time-wait-and-close-wait/2-summary.md) 「동작·원리」 3).
- 관찰 4 — 시간: 순차 300요청에서 `shared`가 가장 빨랐다(1.6~1.9초 vs 2.9~3.4초, 점검 재실행 포함). 같은 루프 안의 JIT 워밍업이 포함된 값이라 비율만 본다.
- 곁가지: 서버의 `sun.net.httpserver.nodelay`를 끄면 `shared`가 13.6초로 느려졌다(1회). 재사용 연결에서 Nagle과 지연 ACK가 겹친 것으로 보인다(해석, [network/22-nagle-and-delayed-ack](../../network/22-nagle-and-delayed-ack/2-summary.md)). 이 노트의 주제와는 별개다.

### 4. Chatty I/O · Extraneous Fetching · Unbounded Result Sets — 양의 문제

```text
 Chatty I/O (작은 요청 여러 번)          Extraneous Fetching (필요 이상)           Unbounded Result Sets (상한 없음)
 for (id : ids) db.find(id)  ×N         SELECT * … 화면엔 2컬럼              SELECT * FROM orders WHERE user=?
 왕복 N번 × RTT                         전송·역직렬화·메모리 낭비               오늘 200행, 1년 뒤 2000만 행 → OOM
 고침: IN(...)·배치·JOIN                고침: 필요한 컬럼·페이지                 고침: LIMIT·keyset 페이지·fetchSize·상한 검사
```

- Azure 문서(Chatty I/O): 작은 I/O 요청이 많으면 누적 오버헤드가 성능과 응답성을 떨어뜨린다. ORM의 N+1이 대표다([database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md)).
- Azure 문서(Extraneous Fetching): Chatty I/O를 **과하게 보상**해 "필요할지 모르는 것까지 다 가져오기"로 가면 생긴다. 목록은 페이지로(예: 20개씩).
- *Unbounded Result Sets*: 결과 크기에 상한이 없는 조회. Nygard 4장 항목이다. 데이터가 자라는 속도와 상관없이 코드는 그대로라 "어느 날" 터진다. 상한은 호출하는 쪽이 정한다 — 상대가 몇 행을 줄지 믿지 않는다.

### 5. Synchronous I/O · Blocked Threads · Slow Responses — 스레드가 묶이는 문제

```text
 요청 스레드 4개 (예시)
 [T1] /order → 외부 결제 (5초 멈춤, 타임아웃 없음) ─┐
 [T2] /order → 〃                               ├─ 전부 묶임
 [T3] /order → 〃                               │
 [T4] /order → 〃                               ─┘
 큐:  /order × 4, /health ← 처리할 스레드가 없다 → LB·쿠버네티스가 "죽었다"고 판단
```

- *Blocked Threads*: 요청 스레드가 느린 통합 지점이나 락에서 기다리며 묶이는 것. 묶인 스레드가 풀을 다 채우면 아무 요청도 처리 못 한다. 헬스체크도 같은 풀을 쓰면 함께 실패한다.
- *Synchronous I/O*(Azure): I/O가 끝날 때까지 호출 스레드를 막는 것. 스레드가 기다리는 동안 일을 못 한다.
- *Slow Responses*(Nygard 4장 항목): 느린 응답은 호출한 쪽의 스레드·연결을 오래 붙잡는다. 아래 실험 6이 그 모양이다. 원문의 정의와 논지는 열지 못했다 `[?]`.
- *Busy Front End*(Azure): 무거운 작업을 백그라운드 스레드로 많이 넘기면 그 스레드들이 요청 처리 스레드의 자원을 굶긴다.

### 6. 실험: 느린 외부 호출이 헬스체크를 죽인다

- 앱 서버: JDK `HttpServer`, 요청 스레드 4개. `/order`가 느린 외부 서버(5초 멈춤)를 부른다. `/health`는 즉시 200.
- 주문 8건을 한꺼번에 보내고 0.5초 뒤 헬스체크(타임아웃 1초)를 3번 한다.
- `plain`: 외부 호출 타임아웃 없음. `timeout`: 외부 호출을 300ms에서 끊고 503(빨리 실패). `bulkhead`: `/health`를 다른 스레드(별도 서버 소켓)로 분리.

```java
app.setExecutor(Executors.newFixedThreadPool(4));                 // 요청 스레드 4개
app.createContext("/order", ex -> {
    HttpRequest.Builder b = HttpRequest.newBuilder(URI.create("http://127.0.0.1:9000/"));
    if (mode.equals("timeout")) b.timeout(Duration.ofMillis(300));
    int code;
    try { dep.send(b.build(), BodyHandlers.discarding()); code = 200; }
    catch (Exception e) { code = 503; }                           // 빨리 실패
    ex.sendResponseHeaders(code, -1); ex.close();
});
```

(실험, eclipse-temurin:21-jdk, `--cpus=2`, 2026-10-01)

```text
plain    헬스 체크 1: 타임아웃 (1007ms)
plain    헬스 체크 2: 타임아웃 (1001ms)
plain    헬스 체크 3: 타임아웃 (1000ms)
timeout  헬스 체크 1: HTTP 200 (765ms)
timeout  헬스 체크 2: HTTP 200 (6ms)
timeout  헬스 체크 3: HTTP 200 (5ms)
bulkhead 헬스 체크 1: HTTP 200 (155ms)
bulkhead 헬스 체크 2: HTTP 200 (7ms)
bulkhead 헬스 체크 3: HTTP 200 (6ms)
```

- 관찰 1 — `plain`: 앱 자체는 멀쩡한데 헬스체크 3번이 모두 실패했다. 쿠버네티스 liveness라면 이 파드를 재시작한다. 재시작은 처리 중인 주문까지 끊는다.
- 관찰 2 — `timeout`: 첫 헬스체크가 765ms 걸렸다(점검 재실행 640·746ms). 주문 8건이 스레드 4개로 300ms씩 두 차례 줄을 섰고, 헬스체크가 그 뒤에 섰다.
  - "300ms × 2 − 0.5초 ≈ 0.1초"보다 긴 이유: 첫 연결·클래스 로딩 때문에 주문 처리 시작이 늦었다. 점검에서 시각 로그를 넣어 보니 첫 주문 시작이 전송 약 0.3초 뒤였고, 두 번째 차례가 끝난 직후 헬스체크가 처리됐다(헬스 대기 약 600ms). 타임아웃은 묶이는 **시간**을 줄일 뿐 줄을 없애지는 않는다.
- 관찰 3 — `bulkhead`: 헬스체크는 주문과 상관없이 응답했다. 다만 주문 쪽 스레드는 여전히 5초씩 묶여 있다. 격벽은 **번지는 것**을 막을 뿐 주문 실패를 막지 않는다. 그래서 타임아웃과 격벽을 함께 쓴다([28-bulkhead](../28-bulkhead/2-summary.md)).
- 범위: 이 실험의 "헬스체크 = 같은 스레드 풀"은 의도한 단순화다. 실제 서버(Tomcat 등)도 기본 설정에서 헬스 엔드포인트가 요청 스레드 풀을 함께 쓰는지는 서버·설정마다 확인해야 한다 `[?]`.

### 7. 저장소와 트래픽 모양

- *Busy Database*(Azure): 저장 프로시저·트리거 등 처리를 DB에 너무 많이 넘겨 DB가 저장·조회 대신 코드를 돌리느라 바쁜 것. 많은 시스템에서 DB는 앱 서버보다 늘리기 어렵다(해석).
- *Monolithic Persistence*(Azure): 쓰임새가 다른 데이터(주문, 로그, 세션, 검색)를 한 저장소에 몰아 넣어 서로 경합하는 것.
- *Self-Denial Attack*: 시스템(사람 포함)이 스스로를 공격하는 상황. 예: 마케팅이 쿠폰 공지를 수십만 명에게 한꺼번에 보내 자기 서비스에 트래픽을 몰았다. Nygard 2판 4장 항목이다. 원문 정의 문장은 확인하지 못했다 `[?]`.
- *Dogpile*: 많은 서버나 클라이언트가 **같은 순간에** 같은 일을 하는 것. 예: 전 서버의 크론이 자정 00:00:00에 시작, 캐시가 같은 TTL로 동시에 만료, 장애 뒤 모든 클라이언트가 동시에 재접속. Nygard 2판 4장 항목이다. 원문 예시 목록은 확인하지 못했다 `[?]`. 캐시 쪽은 [29-cache-stampede](../29-cache-stampede/2-summary.md).
- *Retry Storm*(Azure): 실패한 요청을 너무 자주 재시도해 서버를 더 누르는 것([06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **커넥션 풀** — 한 번 맺은 연결을 큐에 두고 빌려 쓰고 돌려준다. Improper Instantiation의 해법이다([database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md)).
- **배치·묶음 조회** — N번 왕복을 `IN (...)`·bulk API·DataLoader식 모으기로 1~몇 번으로([40-batching-and-round-trips](../40-batching-and-round-trips/2-summary.md)).
- **keyset 페이지네이션 커서** — `WHERE id > :last ORDER BY id LIMIT n`. 상한 있는 조회의 기본 모양.
- **고정 크기 스레드 풀 + 큐** — 묶인 스레드 수가 곧 처리 능력의 상한이다. Little의 법칙으로 "필요 스레드 ≈ 도착률 × 대기 시간"을 계산한다([21-scaling-principles](../21-scaling-principles/2-summary.md)).
- **세마포어·별도 풀(격벽)** — 통합 지점마다 동시 호출 수에 상한을 둔다.
- **지터(무작위 지연)** — 같은 순간에 몰리는 Dogpile을 흩는다. 크론 시작 시각에 무작위 0~N초를 더한다.

## 적용 — 풀어나가는 법

### 1. 리뷰 체크리스트 — "이 코드가 100배 데이터·100배 동시성에서 어떻게 되나"

```text
 □ 클라이언트·풀·ObjectMapper·SSLContext를 요청마다 만들지 않나 (싱글턴·빈으로)
 □ 반복문 안에 DB·HTTP 호출이 있나 (N+1, Chatty I/O)
 □ 모든 조회에 상한이 있나 (LIMIT, 페이지, fetchSize, 최대 건수 검사)
 □ 모든 통합 지점에 연결·읽기 타임아웃이 있나 (기본값이 무한인 라이브러리 확인)
 □ 느린 통합 지점이 요청 스레드 풀 전체를 묶을 수 있나 (격벽·세마포어)
 □ 헬스체크가 요청 풀·의존성과 분리됐나
 □ 정해진 시각에 모든 인스턴스가 동시에 시작하는 작업이 있나 (지터·리더 한 대만)
```

### 2. 고친 모양 — Java

```java
// Improper Instantiation → 공유
@Configuration
class HttpConfig {
    @Bean HttpClient httpClient() {                       // 애플리케이션에 하나
        return HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(1)).build();
    }
}

// Unbounded Result Sets → 상한과 페이지
List<Order> page(long userId, long afterId, int size) {
    int limit = Math.min(size, 500);                      // 호출자가 큰 값을 줘도 상한
    return jdbc.query("SELECT id, amount FROM orders WHERE user_id = ? AND id > ? ORDER BY id LIMIT ?",
                      mapper, userId, afterId, limit);
}

// Blocked Threads → 요청마다 타임아웃 + 동시 호출 상한
private final Semaphore paymentSlots = new Semaphore(8);
PaymentResult pay(Req r) throws Exception {
    if (!paymentSlots.tryAcquire(50, TimeUnit.MILLISECONDS)) throw new Busy();   // 빨리 실패
    try {
        return client.send(HttpRequest.newBuilder(uri).timeout(Duration.ofMillis(800)).POST(body(r)).build(),
                           handler).body();
    } finally { paymentSlots.release(); }
}
```

- Dogpile → 크론 시작에 지터: `Thread.sleep(ThreadLocalRandom.current().nextLong(0, 60_000))` 뒤 시작하거나, 리더 한 대만 실행.

### 3. 진단

```bash
# Improper Instantiation: 연결·TIME_WAIT 수, 원격 주소별
ss -tan state time-wait | wc -l
ss -tan state established | awk '{print $4}' | sort | uniq -c | sort -rn | head
cat /proc/sys/net/ipv4/ip_local_port_range        # 임시 포트 범위
# Blocked Threads: 스레드 덤프에서 같은 프레임에 멈춘 스레드 수
jcmd <pid> Thread.print > td.txt
grep 'java.lang.Thread.State' td.txt | sort | uniq -c        # 상태별 스레드 수
grep -A2 'java.lang.Thread.State' td.txt | grep 'at ' | sort | uniq -c | sort -rn | head   # 가장 많이 멈춘 맨 위 프레임
# 스레드 수 추이 (Improper Instantiation이면 계속 오른다)
ls /proc/<pid>/task | wc -l
```

```sql
-- Chatty I/O · Busy Database: 호출 수가 많은 쿼리 (PostgreSQL pg_stat_statements 확장)
SELECT calls, mean_exec_time, rows / NULLIF(calls,0) AS rows_per_call, left(query, 80)
FROM pg_stat_statements ORDER BY calls DESC LIMIT 10;
```

- 요청 하나당 쿼리 수·외부 호출 수를 지표나 트레이스 스팬 수로 본다. "요청당 쿼리 50개"는 Chatty I/O의 신호다.

## 장애 시나리오와 대처

### 1. 요청마다 `new HttpClient` → TIME_WAIT 폭증·`EADDRNOTAVAIL`

- 현상: 트래픽이 오르자 외부 API 호출이 간헐적으로 연결 단계에서 실패한다. 재시작하면 잠깐 낫는다.
- 보이는 형태: `Cannot assign requested address`(errno `EADDRNOTAVAIL`). `ss -tan state time-wait`가 수만. 스레드 수가 시간에 따라 오른다(실험 `new`: 513~900개).
- 원인: 클라이언트·연결을 요청마다 만들고 버린다. 먼저 닫는 쪽에 TIME_WAIT가 남아 임시 포트를 잡고 있다(connect(2): 임시 포트 범위가 모두 사용 중이면 EADDRNOTAVAIL).
- 대처: 클라이언트를 공유하고 연결을 재사용한다(실험 `shared`: 연결 1개). 상대가 keep-alive를 끊는지, 풀 크기·idle 타임아웃이 맞는지 본다([network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md)).

### 2. `LIMIT` 없는 조회 → 데이터가 커진 어느 날 OOM

- 현상: 몇 달 잘 돌던 서비스가 특정 고객 요청에서 `OutOfMemoryError`로 죽는다. 그 고객만 데이터가 많다.
- 보이는 형태: 힙 덤프에서 엔티티 리스트 하나가 수백만 개. GC 로그의 Full GC 연속 뒤 OOM. DB 쪽에는 큰 결과 전송.
- 원인: 결과 크기에 상한이 없다(Unbounded Result Sets). 코드는 그대로인데 데이터가 자랐다.
- 대처: 목록 조회마다 페이지·`LIMIT`·최대 건수 검사. 대량 처리는 스트리밍(`fetchSize`)이나 배치 커서로([31-batch-job-restart-and-checkpoint](../31-batch-job-restart-and-checkpoint/2-summary.md)). 메모리 한도와 OOM의 모양은 [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md).

### 3. 스레드 풀 전부가 느린 외부 호출에 묶임 → 헬스체크까지 실패

- 현상: 외부 결제사가 느려진 시각에 우리 서비스 전체가 응답하지 않는다. 쿠버네티스가 파드를 연달아 재시작한다.
- 보이는 형태: 스레드 덤프에서 요청 스레드 전부가 같은 소켓 읽기 프레임. liveness 실패 이벤트. 실험 `plain`처럼 헬스체크 타임아웃.
- 원인: 타임아웃 없는 동기 호출(Blocked Threads) + 헬스체크가 같은 풀을 씀. 재시작은 처리 중 요청까지 끊어 상황을 키운다.
- 대처: 통합 지점마다 연결·읽기 타임아웃, 동시 호출 상한(세마포어·별도 풀), 서킷 브레이커([10-circuit-breaker](../10-circuit-breaker/2-summary.md)). liveness는 의존성을 보지 않게 하고 별도 경로로 둔다(실험 `bulkhead`).

### 4. 자정 배치·쿠폰 공지 → 자기 트래픽이 DoS

- 현상: 매일 00:00에 DB CPU가 치솟고 API 지연이 튄다. 또는 쿠폰 푸시 직후 서비스가 멈춘다.
- 보이는 형태: 지표가 정확히 정각에 수직으로 오른다. 요청 출처가 우리 서버들의 배치이거나, 푸시를 받은 사용자 앱이다.
- 원인: 모든 인스턴스가 같은 시각에 같은 일을 한다(Dogpile). 또는 우리 쪽 결정(마케팅 발송)이 자기 용량을 넘는 트래픽을 만들었다(Self-Denial).
- 대처: 크론에 지터를 넣거나 리더 한 대만 실행. 발송은 나눠서(배치·속도 제한). 마케팅 일정은 운영과 공유하고, 사전 증설·대기열(가상 대기실)·우선순위 셰딩을 둔다([12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md)).

## 핵심 문장

- 이 안티패턴들은 코드가 틀려서가 아니라 규모가 커져서 터진다. 리뷰 질문은 "100배 데이터·100배 동시성에서 어떻게 되나"다.
- 공유하도록 설계된 객체를 요청마다 만들면 자원이 샌다. 실험에서 클라이언트 하나는 연결 1개를 썼고, 요청마다 만든 클라이언트는 스레드 513~900개, 닫아 줘도 TIME_WAIT 300개를 남겼다.
- 상한 없는 조회는 데이터가 자라는 날 OOM이 된다. 상한은 받는 쪽이 정한다.
- 타임아웃 없는 통합 지점은 요청 스레드 전부를 묶고, 같은 풀을 쓰는 헬스체크까지 실패시킨다(실험 `plain`). 타임아웃은 묶이는 시간을, 격벽은 번지는 범위를 줄인다.
- 정해진 시각·정해진 사건에 모두가 한꺼번에 움직이면 자기 자신이 공격자가 된다. 지터·분산 발송·리더 한 대로 흩는다.

## 관련 주제·근거

- 선행
  - [47-server-design-antipatterns](../47-server-design-antipatterns/2-summary.md) — 구조·운영 수준 안티패턴
  - [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md) — 풀, 대기, 크기
- 연결
  - [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md) — Chatty I/O의 대표
  - [network/20-time-wait-and-close-wait](../../network/20-time-wait-and-close-wait/2-summary.md) — TIME_WAIT, 임시 포트 고갈
  - [network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md) — 연결 재사용
  - [28-bulkhead](../28-bulkhead/2-summary.md) · [10-circuit-breaker](../10-circuit-breaker/2-summary.md) · [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) · [29-cache-stampede](../29-cache-stampede/2-summary.md) · [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md)
  - [49-steady-state-fail-fast-and-supervision](../49-steady-state-fail-fast-and-supervision/2-summary.md) — 같은 책 5장의 대응 패턴
- 문서·책
  - Microsoft Learn, "Performance testing and antipatterns for cloud applications"(카탈로그 10개) 및 각 항목 페이지(Improper Instantiation·Chatty I/O·Extraneous Fetching·Synchronous I/O·Busy Front End·Busy Database·Monolithic Persistence) <https://learn.microsoft.com/en-us/azure/architecture/antipatterns/>
  - Nygard, 『Release It!』 2판(Pragmatic Bookshelf, 2018) 4장 "Stability Antipatterns" — 항목 목록은 pragprog.com 목차, 4장 도입부(1968년 NATO 회의의 "software crisis")와 Integration Points 절("number-one killer" 문장)은 출판사 발췌 PDF(P1.0)로 확인. Self-Denial·Dogpile·Slow Responses의 원문 정의는 미확인 `[?]` <https://pragprog.com/titles/mnee2/release-it-second-edition/>
  - JDK 21 API `java.net.http.HttpClient`(클라이언트별 커넥션 풀, `close()` since 21)
  - connect(2) — `EADDRNOTAVAIL` <https://man7.org/linux/man-pages/man2/connect.2.html>
- 실험 목록
  - E48a 요청마다 `new HttpClient` vs 공유 vs 만들고 close — JDK 21 단일 컨테이너, `/proc/net/tcp*` 소켓 상태·스레드 수, 코드 `ClientPerRequest.java`
  - E48b 요청 스레드 4개 + 5초 외부 호출 8건 → 헬스체크(plain·timeout·bulkhead) — JDK 21 단일 컨테이너, 코드 `BlockedThreads.java`
