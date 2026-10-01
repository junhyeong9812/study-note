# distributed/20-data-ownership-and-cross-service-queries — 데이터 소유권과 서비스 경계를 넘는 조회 — 정리 (힌트)

## 해결하는 문제

서비스를 나누면 "누가 이 표를 소유하나"를 정해야 한다. 그리고 소유를 나누는 순간 JOIN 한 줄로 되던 조회가 어려워진다.

```text
  모놀리스:   SELECT o.id, c.name, p.title
             FROM orders o JOIN customers c … JOIN products p …     ← DB가 한 번에 조인

  서비스 분리: 주문 서비스(orders)   고객 서비스(customers)   상품 서비스(products)
             "내 주문 목록(고객 이름·상품명 포함)"은 누가 어떻게 만드나?
```

- 선택지는 크게 둘이다.
  - *Shared Database*: 여러 서비스가 한 DB를 같이 쓰고, 서로의 표를 로컬 ACID 트랜잭션으로 직접 읽고 쓴다(microservices.io).
  - *Database per Service*: 각 서비스의 데이터는 그 서비스만 쓰고, 다른 서비스는 API로만 접근한다(microservices.io).
- Database per Service를 고르면 서비스 경계를 넘는 조회 방법이 필요하다. 이 노트가 다루는 네 가지: *API Composition*, *Command-side Replica*, *Materialized View*, *Index Table*.

쉬운 예: 부서마다 자기 장부를 갖는다. 영업부가 "고객 이름이 들어간 주문 목록"을 만들려면?
- 고객관리부 장부를 직접 펼쳐 본다(공유 DB) → 고객관리부가 장부 양식을 바꾸면 영업부 보고서가 깨진다.
- 매번 전화로 물어본다(API Composition) → 주문 20건이면 전화 20통.
- 고객 명단 사본을 받아 둔다(복제본·뷰) → 사본이 조금 늦을 수 있다.

똑같은 구조다. 실무 예: "내 주문 목록" 화면, 관리자 검색, 주문 생성 시 상품 가격 검증, 대시보드 집계.

## 동작·원리

### 1. Shared Database vs Database per Service

```text
  Shared Database                          Database per Service
  ┌────────┐ ┌────────┐                    ┌────────┐      ┌────────┐
  │ 주문 서비스│ │ 고객 서비스│                    │ 주문 서비스│ API  │ 고객 서비스│
  └───┬────┘ └───┬────┘                    └───┬────┘ ───> └───┬────┘
      └────┬─────┘                             │               │
      ┌────▼──────────────┐                ┌───▼───┐       ┌───▼───┐
      │ orders · customers │               │ orders │       │customers│
      └───────────────────┘                └───────┘       └───────┘
  + 익숙한 ACID, 운영 단순                    + 스키마 변경이 다른 서비스에 안 번짐
  − 스키마 변경 조율(개발 시점 결합)            − 서비스 경계를 넘는 트랜잭션·조회가 어렵다
  − 한 서비스의 긴 트랜잭션·락이 남을 막음(런타임 결합)
```

- 단점·장점은 microservices.io "Shared database"·"Database per service"의 정리다.
- Database per Service는 DB 서버를 서비스마다 둘 필요가 없다. 같은 서버 안에서 서비스별 *private tables*, *schema per service*, *database server per service* 중 고를 수 있다. 문서는 **DB 사용자를 서비스마다 다르게 하고 권한(grant)으로 장벽을 세우라**고 권한다. 장벽이 없으면 개발자는 API를 우회해 데이터를 직접 읽고 싶어진다.

### 실험: 공유 DB의 스키마 결합, 그리고 권한 장벽

- 환경: 전용 일회용 PostgreSQL 17.11, DB 하나에 스키마 `customer`(소유 `customer_svc`)·`ordering`(소유 `order_svc`). 2026-10-01.

(실험, PostgreSQL 17.11, 2026-10-01)

```text
=== 1. 공유 DB: 주문 서비스가 고객 표를 직접 조인
 id  | full_name | amount
-----+-----------+--------
 100 | Kim       |   5000
=== 2. 고객 팀이 자기 표의 열 이름을 바꾼다 (자기 서비스 코드는 함께 배포)
ALTER TABLE
=== 3. 주문 서비스의 같은 조회
ERROR:  column c.full_name does not exist
LINE 1: select o.id, c.full_name, o.amount from ordering.orders o jo...
=== 4. 장벽: 권한을 거두면 직접 접근 자체가 막힌다 (Database per Service를 권한으로 강제)
REVOKE
ERROR:  permission denied for table customers
```

- 고객 팀의 `ALTER`는 성공했다. DB는 "다른 서비스가 이 열을 쓴다"는 것을 모른다(뷰 같은 DB 객체 의존이 없으면). 깨진 것은 **다른 팀의 서비스**다. 이것이 *분산 모놀리스*의 전형이다.
  - *분산 모놀리스(distributed monolith)*: 서비스는 나눴지만 공유 DB·동기 호출 사슬 때문에 함께 배포·함께 장애가 나는 구조. 결합은 그대로인데 분산 비용만 더해진다(원고 [systems/server-design/11-antipatterns](../../systems/server-design/11-antipatterns.md) 1절 「분산 모놀리스」·3절 「공유 데이터베이스」).
- 4번처럼 권한을 거두면 우회 조회가 **배포 전에** 드러난다. 장벽은 실수를 일찍 시끄럽게 만든다.

### 2. API Composition — 조회 시점에 모아서 메모리에서 조인

```text
  API Composer(게이트웨이·BFF·조회 서비스)
     ① 주문 서비스: GET /orders?customer=7&page=1        → 주문 20건 (customerId, productId)
     ② 고객 서비스: GET /customers?ids=…  ┐ 병렬
     ③ 상품 서비스: GET /products?ids=…   ┘
     ④ 메모리 해시 조인: Map<id, 고객>, Map<id, 상품> → 주문마다 찾아 붙인다
```

- microservices.io "API Composition": 데이터를 가진 서비스들을 호출하고 결과를 **메모리에서 조인**한다. API 게이트웨이가 흔히 이 역할을 한다. 단점: 큰 데이터셋의 메모리 조인은 비효율적이다.
- 같은 조합이라도 **호출 모양**이 성능을 가른다.
  - 주문마다 고객·상품을 하나씩 부르면 1 + 2N 호출이다. ORM의 N+1([database/23](../../database/23-orm-and-n-plus-one/2-summary.md))이 네트워크 너머로 옮겨 온 것이다.
  - ID를 모아 배치로, 서로 독립인 호출은 병렬로 부르면 3 호출, 지연은 대략 "가장 느린 한 갈래"다.

### 실험: N+1 조합 vs 배치·병렬 조합, 그리고 꼬리 지연

- 환경: Java 21 한 JVM 안에 JDK `HttpServer` 세 개(주문·고객·상품, 127.0.0.1), `HttpClient`로 조합. 호출마다 서버가 2ms 잠든다. 상품 서비스는 호출의 0%·1%·5%에서 100ms 잠든다(꼬리 지연 흉내). 페이지 20건, 페이지 200번 측정. 2026-10-01.
- 서버는 `-Dsun.net.httpserver.nodelay=true`로 띄웠다. 이 옵션 없이 처음 돌렸을 때는 호출마다 약 24ms가 더 붙어(naive p50 966ms, batch 48ms) 서비스 지연보다 전송 지연이 커졌다. 사실 점검 때 옵션 없이 다시 돌려도 naive p50 967ms, batch 48ms였다. JDK 21 HttpServer는 이 속성이 없으면 TCP_NODELAY를 켜지 않는다(`sun.net.httpserver.ServerConfig`의 `Boolean.getBoolean("sun.net.httpserver.nodelay")`, 기본 false). 그래서 Nagle 알고리즘과 지연 ACK가 맞물려 생긴 지연으로 보인다(원인 기제는 해석). 두 결과의 대소 관계는 같았다.

```java
static void naivePage() {                         // 1 + 2N
    get("http://127.0.0.1:8101/orders?page=1");
    for (int i = 0; i < PAGE; i++) {
        get("http://127.0.0.1:8102/customers/" + i);
        get("http://127.0.0.1:8103/products/" + i);
    }
}
static void batchPage() {                         // 1 + 2, 병렬
    get("http://127.0.0.1:8101/orders?page=1");
    CompletableFuture<String> c = CompletableFuture.supplyAsync(() -> get(".../customers?ids=" + ids));
    CompletableFuture<String> p = CompletableFuture.supplyAsync(() -> get(".../products?ids=" + ids));
    c.join(); p.join();                           // 이어서 메모리 해시 조인
}
```

(실험, Java 21 HttpServer 3개·nodelay=true, 페이지 200번, 2026-10-01 — 같은 설정 두 번 중 1회차)

```text
slow=0% naive | 페이지당 호출 41 | p50 149 ms, p90 178 ms, p99 248 ms | 100ms 이상 페이지 200/200
slow=0% batch | 페이지당 호출 3 | p50 7 ms, p90 8 ms, p99 9 ms | 100ms 이상 페이지 0/200
slow=1% naive | 페이지당 호출 41 | p50 131 ms, p90 229 ms, p99 332 ms | 100ms 이상 페이지 200/200
slow=1% batch | 페이지당 호출 3 | p50 6 ms, p90 7 ms, p99 7 ms | 100ms 이상 페이지 1/200
slow=5% naive | 페이지당 호출 41 | p50 226 ms, p90 327 ms, p99 523 ms | 100ms 이상 페이지 200/200
slow=5% batch | 페이지당 호출 3 | p50 6 ms, p90 7 ms, p99 104 ms | 100ms 이상 페이지 14/200
```

- 호출 수: 41 vs 3. 지연 p50: 149ms vs 7ms. 2회차도 같은 경향(5% 꼬리에서 naive p99 525ms, batch p99 105ms). 사실 점검 재실행도 같았다(naive p50 150ms, batch 7ms, 5% 꼬리 naive p50 227ms·p99 522ms).
- 꼬리 지연의 증폭: 상품 호출의 5%만 느린데, naive는 한 페이지에서 상품을 20번 부르므로 p50부터 226ms로 올랐다. 느린 호출을 하나도 안 만날 확률은 0.95^20 ≈ 36%뿐이다(계산). batch는 상품을 한 번만 부르므로 p99에서만 느린 호출(약 100ms)이 보인다.
- 0%의 naive p50(149ms)이 1%(131ms)보다 큰 것은 첫 측정이라 JIT 예열이 덜 된 영향으로 보인다(해석, 두 실행 모두 같았다).
- 결론: 조합 조회의 지연은 **가장 느린 서비스 × 그 서비스를 부르는 횟수**가 정한다. 배치·병렬로 횟수를 줄여도 가장 느린 갈래는 남는다.

### 3. Command-side Replica — 명령 처리에 필요한 남의 데이터를 복제해 둔다

```text
  상품 서비스 ── ProductPriceChanged 이벤트 ──> 주문 서비스의 replica 표(읽기 전용)
  주문 생성 명령: 가격 검증을 replica로 → 상품 서비스를 부르지 않는다
```

- microservices.io "Command-side replica": 명령을 처리하는 서비스가 제공자 서비스의 도메인 이벤트를 구독해 읽기 전용 복제본을 유지한다.
  - 얻는 것: 런타임 결합 감소(제공자가 죽어도 명령 처리), 상호작용이 단순·효율적.
  - 잃는 것: 복제본은 **오래된 값일 수 있다**(문서: "the replica is potentially stale"). 제공자는 이벤트를 발행해야 하고, 두 팀의 설계 시점 결합이 늘 수 있다.

### 4. Materialized View — 조회 전용 모델을 미리 만들어 둔다

```text
  주문 서비스 ─ OrderCreated ─┐
  고객 서비스 ─ CustomerRenamed ┼─> 프로젝터(이벤트를 접어 반영) ─> order_view(조회 전용)
  상품 서비스 ─ ProductRenamed ─┘                                  │
                                                     "내 주문 목록" API가 여기만 읽는다
```

- Azure "Materialized View": 조회에 맞는 모양으로 데이터를 **미리** 만들어 두는 읽기 모델·프로젝션. 원천에서 언제든 **다시 만들 수 있으므로 버려도 되는**(disposable) 특수한 캐시다. 조회자는 뷰를 직접 고치지 않는다.
  - 문서가 꼽는 주의점: 갱신 신호가 유실·지연되면 뷰가 **조용히** 오래된 결과를 낸다. 뷰의 최신성을 감시하고 허용 범위를 넘으면 알람을 건다.
- 이벤트로 뷰를 갱신하려면 원천의 이벤트 발행이 믿을 만해야 한다. 원천 변경과 발행이 원자적이지 않으면 뷰가 영원히 어긋난다 → outbox(16).
- *CQRS*: 쓰기 모델과 읽기 모델을 분리하는 설계. Materialized View가 그 읽기 모델이다. 원고 [systems/server-design/03-data-layer](../../systems/server-design/03-data-layer.md) 3절.

### 실험: 이벤트로 유지하는 뷰의 지연 — "주문했는데 목록에 없음"

- 환경: 전용 일회용 PostgreSQL 17.11 + Kafka 4.1.0, Java 21. 주문 서비스가 `orders20`을 커밋하고 이벤트를 발행한다. 프로젝터 스레드가 소비해 `order_view`에 넣는다. 주문 직후 사용자가 `order_view`를 조회한다. 200건. 두 번째 실행은 50번째 주문 직후 프로젝터를 3초 멈춘다(배포·GC·리밸런스 흉내). 2026-10-01.

(실험, PostgreSQL 17.11 + Kafka 4.1.0, 2026-10-01)

```text
pause=0ms | 주문 직후 조회에서 없음 200/200 | 보이기까지 p50 15 ms, p99 28 ms, max 119 ms
pause=3000ms | 주문 직후 조회에서 없음 199/200 | 보이기까지 p50 15 ms, p99 103 ms, max 3006 ms
```

- 평소에도 주문 직후 조회는 **매번**(200/200) 뷰에 없었다. 발행 ack부터 셌을 때 보이기까지 p50 15ms였다. 사람 눈에는 짧지만 "저장 직후 목록 화면으로 리다이렉트"하는 코드에는 충분히 길다.
- 프로젝터가 3초 멈추자 그 주문은 3초 동안 목록에 없었다(max 3006ms).
- 지연 값과 '없음' 건수는 실행마다 조금 다르다. 사실 점검 재실행: pause 0은 200/200·p50 16ms·p99 29ms, pause 3000은 200/200·max 3013ms. 실제 장애에서는 프로젝터가 멈춘 동안 들어온 신규 주문이 그만큼 안 보인다.
- 대처는 아래 「적용 3」.

### 5. Index Table — 보조 키로 찾을 수 있게 따로 색인 표를 둔다

```text
  사실 표(fact, PK = customerId)        색인 표(PK = town)
   1 → Smith, Redmond                   Redmond → [1, 4, …]       ← 정규화: 참조만, 조회 2번
   2 → Jones, Seattle                   Seattle → [2, …]
                                        (완전 비정규화: 행 전체 복사 / 부분 비정규화: 자주 쓰는 열만 복사)
```

- Azure "Index Table": 보조 인덱스가 없거나 부족한 저장소(키-값·일부 NoSQL)에서 보조 키 → 기본 키 표를 직접 만든다. 세 가지 구성: 완전 비정규화, 정규화 인덱스(조회 2번), 부분 비정규화.
- 서비스 경계에서는 "다른 서비스의 ID로 내 데이터를 찾는" 표(예: 결제 서비스가 가진 `orderId → paymentId`)가 같은 역할을 한다.
- 문서의 주의: 원천과 색인을 같은 트랜잭션에서 갱신할 수 없으면 최종 일관성을 전제로 설계한다. 원천 갱신 뒤 따로 색인 메시지를 발행하지 말고(그 사이 실패하면 색인이 오래된 채 남는다) 변경 피드·transactional outbox를 쓰라고 한다.

## 쓰이는 자료구조·알고리즘

- **해시 조인(메모리 합성)** — API Composer는 ID → 객체 해시맵을 만들어 주문마다 찾아 붙인다. DB의 해시 조인과 같은 알고리즘이다. 커리큘럼 🔧 칸. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md)
- **이벤트 → 프로젝션 폴드** — 뷰 = `fold(apply, 빈 뷰, 이벤트들)`. 이벤트 순서대로 상태를 접어 만든다. 다시 만들 수 있으니 버려도 된다. 커리큘럼 🔧 칸. [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md)
- **보조 인덱스(역색인)** — Index Table은 "값 → 기본 키 목록" 사상이다. DB의 보조 인덱스를 손으로 만든 것이다. [database/09-index-design](../../database/09-index-design/2-summary.md)
- **배치·병렬 호출(scatter-gather)** — ID를 모아 한 번에, 독립 호출은 동시에.

## 적용 — 풀어나가는 법

### 1. 고르는 순서

```text
  조회가 한 서비스 데이터로 끝나나? ─ 예 ─> 그 서비스 API
        │ 아니오
  건수가 작고(한 화면), 최신성이 중요하고, 참여 서비스가 적은가? ─ 예 ─> API Composition (배치·병렬·타임아웃)
        │ 아니오 (목록·검색·정렬·집계, 여러 서비스 필드로 필터)
  Materialized View (조회 서비스가 이벤트로 유지, 지연 허용 범위 명시)
        │
  명령 처리 중 남의 데이터로 검증해야 하나? ─> Command-side Replica (오래된 값 허용 범위 확인)
  키-값 저장소에서 보조 키로 찾아야 하나?   ─> Index Table
```

- 공유 DB에서 출발한 시스템을 바꿀 때는 먼저 **소유를 정하고 권한으로 장벽**을 세운다. 그다음 다른 서비스의 직접 조회를 하나씩 API·뷰로 옮긴다.

### 2. API Composition 코드 모양 (Java)

```java
public List<OrderRow> myOrders(long customerId, int page) {
    List<Order> orders = orderClient.list(customerId, page);                 // 1회
    Set<Long> productIds = orders.stream().map(Order::productId).collect(toSet());
    CompletableFuture<Customer> cust = supplyAsync(() -> customerClient.get(customerId));
    CompletableFuture<Map<Long, Product>> prods = supplyAsync(() -> productClient.getAll(productIds))  // 배치 1회
            .completeOnTimeout(Map.of(), 300, MILLISECONDS);                  // 느린 갈래는 잘라 낸다 (예시 값)
    Map<Long, Product> byId = prods.join();
    return orders.stream()
            .map(o -> new OrderRow(o, cust.join(), byId.get(o.productId())))  // 없으면 null → 화면에서 "상품 정보 지연"
            .toList();
}
```

- 타임아웃과 부분 응답 정책을 정한다. 가장 느린 서비스가 전체 지연을 정하므로, 필수가 아닌 갈래는 잘라 내고 빈 칸으로 보여 줄 수 있다.

### 3. 뷰 지연을 다루는 법

- 쓰기 직후의 화면은 **쓴 쪽 응답**으로 그린다. 예: 주문 생성 API가 돌려준 주문을 목록 맨 위에 붙인다.
- 또는 뷰가 그 이벤트를 반영했는지 확인할 토큰을 쓴다. 예: 응답에 이벤트 오프셋·버전을 주고, 조회 서비스가 그 버전 이상을 반영할 때까지 짧게 기다린다.
- 프로젝터 지연을 지표로 둔다.

```bash
# 프로젝터 컨슈머 그룹의 지연 (Kafka 4.1)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group order-view-projector   # LAG 열
```

```sql
-- 뷰의 최신성: 마지막으로 반영한 이벤트 시각
SELECT now() - max(source_event_at) AS view_staleness FROM order_view;
```

## 장애 시나리오와 대처

### 1. 공유 DB → 한 팀의 스키마 변경이 다른 서비스 장애 (커리큘럼 ⚠)

- **현상**: 고객 서비스 배포 직후 주문 목록 API만 500을 낸다. 주문 팀은 배포한 게 없다.
- **보이는 형태**: `ERROR: column c.full_name does not exist`(실험). 스택 트레이스가 다른 팀 표를 가리킨다.
- **원인**: 공유 DB에서 다른 서비스가 그 표를 직접 읽고 있었다. 소유 팀은 그 사실을 모른다(분산 모놀리스).
- **대처**: 당장은 열 이름 되돌리기나 호환 뷰. 근본은 소유 선언 + 권한 장벽(실험 4번처럼 `permission denied`로 일찍 드러나게) + 조회를 API·뷰로 이전. 피할 수 없으면 expand/contract 방식 스키마 변경([database/26-schema-migration](../../database/26-schema-migration/2-summary.md)).

### 2. API Composition으로 목록 조회 → 분산 N+1, 가장 느린 서비스가 전체 지연 (커리큘럼 ⚠)

- **현상**: 목록 화면이 느리고, 하위 서비스 하나가 가끔 느려질 때 목록 전체가 크게 느려진다.
- **보이는 형태**: 분산 추적에서 한 요청 아래 같은 서비스 호출이 수십 개(실험: 41개). p50부터 오른다(실험: 상품 5%가 느릴 때 p50 226ms).
- **원인**: 항목마다 호출(1 + 2N). 호출 횟수만큼 꼬리 지연을 만날 확률이 커진다.
- **대처**: ID 배치 API, 병렬 호출, 갈래별 타임아웃·부분 응답. 목록·검색·정렬이 주된 용도면 Materialized View로 옮긴다.

### 3. 복제 뷰 지연 → "주문했는데 목록에 없음" (커리큘럼 ⚠)

- **현상**: 주문 직후 목록 화면에 방금 주문이 없다. 새로고침하면 보인다. 프로젝터 배포 중에는 몇 분간 안 보인다.
- **보이는 형태**: 프로젝터 컨슈머 그룹 LAG 증가. 실험: 평소에도 직후 조회 200/200이 미반영, 프로젝터 3초 정지 시 max 3006ms.
- **원인**: 뷰는 이벤트를 받아 비동기로 갱신된다. 쓰기와 뷰 반영 사이에 간격이 생긴다(실험: 평소 p50 15ms).
- **대처**: 쓰기 응답으로 화면을 그리거나 버전 토큰으로 기다린다(「적용 3」). LAG·뷰 최신성 알람. 원천 발행은 outbox로(유실되면 간격이 영원해진다).

### 4. 뷰가 조용히 영원히 어긋난다

- **현상**: 특정 고객 이름이 목록에서만 옛 이름이다. 몇 주째 그대로다.
- **보이는 형태**: 원천과 뷰를 대조하면 일부 행만 다르다. LAG는 0이다.
- **원인**: 원천 변경 뒤 이벤트 발행이 실패했다(이중 쓰기, 16). 또는 프로젝터가 처리 실패 이벤트를 건너뛰었다.
- **대처**: 원천은 outbox로 발행. 프로젝터는 실패 이벤트를 DLQ로 보내고 알람. 뷰는 버려도 되는 사본이므로 원천에서 다시 만드는 절차(재생·재구축)를 준비한다(Azure "Materialized View").

## 핵심 문장

- 서비스마다 데이터를 소유하게 하면 스키마 변경이 다른 서비스로 번지지 않는다. 대신 경계를 넘는 조회가 어려워진다.
- 공유 DB는 결합을 숨길 뿐 없애지 않는다. 한 팀의 `ALTER`가 다른 팀의 장애가 된다. 소유는 권한으로 강제한다.
- API Composition은 단순하지만, 항목마다 부르면 분산 N+1이 되고 가장 느린 서비스가 전체 지연을 정한다.
- Materialized View·Command-side Replica는 런타임 결합을 끊는 대신 조금 늦은 데이터를 줄 수 있다. 쓰기 직후 화면은 따로 다룬다.
- 뷰·복제본·색인 표를 이벤트로 유지하려면 원천의 발행이 믿을 만해야 한다(outbox).

## 관련 주제·근거

- 선행
  - [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 뷰·복제본을 유지할 이벤트를 잃지 않고 내보내기
  - software-design `45-monolith-vs-microservices` — 미작성, [software-design/README](../../software-design/README.md)
  - domain-modeling `21-cqrs` — 원고 [systems/server-design/03-data-layer](../../systems/server-design/03-data-layer.md) 3절 (영역 표 [domain-modeling/curriculum](../../domain-modeling/curriculum.md))
- 연결
  - reliability `47-server-design-antipatterns` — 원고 [systems/server-design/11-antipatterns](../../systems/server-design/11-antipatterns.md) 3절 "공유 데이터베이스"
  - [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md) — 같은 문제의 DB판
  - [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md) · [database/26-schema-migration](../../database/26-schema-migration/2-summary.md)
  - [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md) — 이벤트로 상태 접기
- 근거
  - microservices.io "Database per service" — private tables·schema·server per service, 서비스별 DB 사용자·grant로 장벽, 장단점 <https://microservices.io/patterns/data/database-per-service.html>
  - microservices.io "Shared database" — 로컬 ACID, 개발 시점 결합(스키마 변경 조율)·런타임 결합(긴 트랜잭션의 락) <https://microservices.io/patterns/data/shared-database.html>
  - microservices.io "API Composition" — 메모리 조인, 큰 데이터셋에서 비효율 <https://microservices.io/patterns/data/api-composition.html>
  - microservices.io "Command-side replica" — 도메인 이벤트 구독으로 읽기 전용 복제본, 복제본은 오래될 수 있음 <https://microservices.io/patterns/data/command-side-replica.html>
  - Azure Architecture Center "Materialized View pattern" — 미리 만든 읽기 모델, 버려도 되는 특수 캐시, 갱신 신호 유실 시 조용히 오래됨·최신성 감시 <https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view>
  - OpenJDK 21 `sun/net/httpserver/ServerConfig.java` — `noDelay = Boolean.getBoolean("sun.net.httpserver.nodelay")`(미설정이면 false) <https://raw.githubusercontent.com/openjdk/jdk21u/master/src/jdk.httpserver/share/classes/sun/net/httpserver/ServerConfig.java>
  - Azure Architecture Center "Index Table pattern" — 완전 비정규화·정규화·부분 비정규화, 일관성 복잡도, outbox·변경 피드 권장 <https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table>
- 실험 목록
  - `exp20b.sh` — 전용 PostgreSQL 17.11: 스키마별 소유·역할, 고객 팀 열 이름 변경 → 주문 서비스 조회 `column c.full_name does not exist`, 권한 회수 → `permission denied for table customers`
  - `ApiCompExp.java` — Java 21 HttpServer 3개(nodelay=true), 페이지 20건·200회, 상품 0·1·5% 100ms 꼬리. naive 41호출 p50 149ms vs batch 3호출 7ms, 5% 꼬리에서 naive p50 226ms·p99 523ms vs batch p99 104ms. 두 번 실행. nodelay 없는 첫 실행(호출당 약 24ms 추가)은 `exp20a-nagle.out`. 사실 점검 때 두 설정 모두 다시 돌려 같은 값을 얻었다(옵션 없음 naive p50 967ms·batch 48ms)
  - `ViewLagExp.java` + `exp20c.sh` — 전용 PostgreSQL 17.11 + Kafka 4.1.0: 주문 직후 뷰 조회 200/200 미반영, 보이기까지 p50 15ms·p99 28ms, 프로젝터 3초 정지 시 max 3006ms
