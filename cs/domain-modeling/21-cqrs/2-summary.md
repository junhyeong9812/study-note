# domain-modeling/21-cqrs — CQRS: 명령 모델과 조회 모델을 나누고, 그 사이의 지연과 누락을 관리한다 — 정리 (힌트)

## 해결하는 문제

하나의 모델로 쓰기 규칙과 화면 조회를 둘 다 감당하면, 한쪽에 맞출수록 다른 쪽이 나빠진다.

```text
  하나의 Order 모델
   쓰기: 불변식 검사·애그리거트 경계·정규화  ← 작고 엄격해야 한다
   읽기: "내 주문 목록" = 주문 + 상품명 + 배송 상태 + 리뷰 여부, 정렬·필터·검색  ← 넓고 비정규화돼야 편하다
  → 목록 조회마다 조인 6개, 또는 엔티티에 화면용 필드가 붙어 불변식이 흐려진다
```

- 해법: 상태를 바꾸는 쪽(명령)과 읽는 쪽(조회)에 **다른 모델**을 쓴다.
  - *CQRS(Command Query Responsibility Segregation)*: Fowler "CQRS"(2011-07-14)의 정의로 "정보를 갱신할 때 쓰는 모델과 읽을 때 쓰는 모델을 다르게 할 수 있다"는 생각이다. Fowler는 이 패턴을 Greg Young에게서 처음 들었다고 적는다.
  - *CQS(Command-Query Separation)*: Bertrand Meyer의 원칙. **메서드** 수준에서 "상태를 바꾸는 명령"과 "값을 돌려주는 조회"를 나눈다. CQRS는 이것을 **모델** 수준으로 키운 것이라고 흔히 설명한다(해석). Fowler 글이 적는 것은 갱신용·표시용 모델을 나누고, 그 이름(Command·Query)을 CQS의 어휘에서 따왔다는 점이다.

쉬운 예: 도서관이다.
- 사서의 대출 장부(명령 모델)는 "누가 무엇을 언제 빌렸나"를 엄격히 적는다.
- 로비의 "이번 주 인기 도서" 게시판(조회 모델)은 장부에서 **베껴** 만든다. 게시판은 몇 시간 늦어도 된다.
- 게시판이 틀리면 장부에서 다시 베끼면 된다. 장부가 틀리면 되돌릴 원본이 없다.

똑같은 구조다. 장부 = 쓰기 모델(원천), 게시판 = 읽기 모델(파생본)이다.

실무 예: 주문은 정규화된 OLTP 테이블에, "내 주문 목록"은 비정규화 테이블·검색 엔진에. 이 구성과 동기화 수단(CDC·애플리케이션 이벤트·배치 재구축)의 기초는 원고 [systems/server-design/03-data-layer.md](../../systems/server-design/03-data-layer.md) 3절 「읽기 모델 분리(CQRS)」·4절 「다중 저장소 정합성」에 있다. 요약하면 "대가는 최종적 일관성, 어느 화면이 얼마의 지연을 허용하는지 먼저 정한다"이다.

이 노트는 원고 위에 세 가지를 더한다.
1. 프로젝션이 **폴드**라는 것과, 재구축·대조로 읽기 모델을 검증하는 법.
2. 폴링 프로젝터가 이벤트를 **영영** 건너뛰는 구멍(시퀀스 구멍) — 실험.
3. "저장했는데 목록에 없음"(⚠)을 read-your-writes 토큰으로 막는 법 — 실험. 그리고 CQRS를 **쓰지 말아야 할** 때.

## 동작·원리

### 1. 구조 — 명령 쪽, 이벤트, 프로젝터, 조회 쪽

```text
  명령 ─> [명령 핸들러] ─> 애그리거트 검사 ─> 쓰기 모델 저장 + 이벤트 기록 (한 트랜잭션)
                                                          │
                                                   events (seq 1, 2, 3, ...)
                                                          │  프로젝터: seq > checkpoint 를 순서대로 읽어
                                                          ▼          뷰에 반영하고 checkpoint 전진
  조회 ─> [조회 핸들러] ─────────────────────────> 읽기 모델 (order_view)
```

- 명령 쪽은 도메인 모델(애그리거트·불변식)을 쓴다. 조회 쪽은 화면 모양 그대로의 테이블·DTO를 쓴다. 조회 쪽에는 도메인 규칙이 없다.
- 둘을 잇는 것은 **변경의 흐름**이다. 도메인 이벤트([09](../09-domain-events/2-summary.md))를 outbox로 남기거나([distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md)), DB 로그를 CDC로 읽는다.
- CQRS는 이벤트 소싱을 요구하지 않는다. 쓰기 모델이 평범한 테이블이어도 된다. 이벤트를 원천으로 삼는 경우는 [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md).
  - *프로젝션(projection)*: 이벤트 흐름을 읽어 조회용 상태를 만드는 것. 만드는 프로그램을 *프로젝터*라 한다.
  - *체크포인트(checkpoint)*: 프로젝터가 어디까지 반영했는지 적어 둔 위치(마지막 seq).

### 2. 프로젝션 = 폴드

```text
  view = fold(apply, 빈 뷰, events[1..n])

  seq  event                 view(order 7)
  1    OrderPlaced(7, 3만원)  {7: PLACED, 30000}
  2    OrderPaid(7)           {7: PAID,   30000}
  3    OrderCancelled(7)      {7: CANCELLED, 30000}
```

- *폴드(fold)*: 목록의 원소를 하나씩 누적 함수에 넣어 값 하나로 접는 연산.
- 이 성질에서 두 가지가 나온다.
  - **재구축 가능**: 빈 뷰에서 seq 1부터 다시 접으면 같은 뷰가 나와야 한다. 읽기 모델은 버려도 되는 파생본이다.
  - **대조 가능**: 라이브 뷰와 재구축 뷰를 `EXCEPT`로 비교하면 프로젝터 버그·누락이 행 단위로 드러난다.
- 전제: `apply`가 결정적이어야 하고(현재 시각·외부 조회를 안 쓴다), 이벤트가 **빠짐없이, 순서대로** 들어와야 한다. 두 번째 전제가 아래 실험에서 깨진다.

### 실험: 동시 작성자 4개 + 폴링 프로젝터 — 시퀀스 구멍으로 이벤트를 영영 건너뛴다

- 환경: 전용 일회용 컨테이너 PostgreSQL 17.11, JDK 21, pgjdbc 42.7.4, 2026-10-03.
- 작성자 스레드 4개가 주문을 250건씩(합 1,000) 넣는다. 트랜잭션마다 `orders` INSERT + `events` INSERT(`seq bigserial`) 후 0~2ms 쉬고 커밋한다. 프로젝터는 5ms마다 `seq > checkpoint`를 seq 순으로 읽어 뷰에 반영하고 checkpoint를 마지막 seq로 옮긴다. 작성이 끝난 뒤 프로젝터를 세 번 더 돌린다.
- 비교: 이벤트를 붙이기 직전에 `pg_advisory_xact_lock(42)`를 잡아(커밋까지 유지) 붙이기를 직렬화한 판.

```java
long place(Connection c, long id, ..., boolean lockAppend, int sleepMs) {
    c.setAutoCommit(false);
    exec(c, "insert into orders values (...)");
    if (lockAppend) exec(c, "select pg_advisory_xact_lock(42)");      // 커밋까지 붙이기 직렬화
    long seq = one(c, "insert into events(...) values (...) returning seq");
    Thread.sleep(random(sleepMs));                                     // 커밋 전 지연(예시)
    c.commit();
}
// 프로젝터
"select ... from events where seq > " + checkpoint + " order by seq limit 500"   → 반영 → checkpoint = 마지막 seq
```

(실험, PostgreSQL 17.11 + JDK 21, 2026-10-03)

```text
[구멍 실험 lockAppend=false] orders 1000, events 1000, view 975, 뷰에 영영 없는 주문 25
[구멍 실험 lockAppend=true] orders 1000, events 1000, view 1000, 뷰에 영영 없는 주문 0
```

- 직렬화 없이: 1,000건 중 25건이 뷰에 **영영** 없었다. 작성이 끝난 뒤 프로젝터를 더 돌려도 회복되지 않았다. 집필 3회 + 사실 점검 재실행 3회에서 14~25건(실행마다 다르다). 직렬화한 판은 6회 모두 0건.
- 왜:

```text
  T1: seq=41 받음 ............................. COMMIT (늦게)
  T2: seq=42 받음 ── COMMIT (먼저)
  프로젝터: seq > 40 조회 → 42만 보임 (41은 아직 커밋 전이라 안 보임) → checkpoint = 42
  이후: seq > 42 만 조회 → 41은 영원히 다시 안 읽힌다
```

  - 시퀀스 번호는 **할당 순서**이지 **커밋 순서**가 아니다. PostgreSQL 17 문서(9.17 Sequence Manipulation Functions)는 `nextval`로 받은 값이 트랜잭션이 중단돼도 재사용되지 않으며, 그래서 할당된 값에 구멍이 생길 수 있다고 적는다. 동시 트랜잭션끼리는 번호를 받은 순서와 커밋하는 순서도 따로 논다.
- 직렬화(advisory lock)하면 seq 순서 = 커밋 순서가 되어 누락 0. 대가는 이벤트 붙이기가 한 줄로 서는 것(쓰기 처리량 상한).
- 다른 해법: 커밋 순서로 내보내는 CDC(논리 디코딩)를 원천으로 쓴다([distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md) 3절). 또는 구멍을 만나면 일정 시간 기다렸다 넘어가는 프로젝터(기다림 상한 안에 커밋되지 않으면 여전히 누락 가능 — 그래서 대조가 필요하다).

### 3. "저장했는데 목록에 없음" — 지연과 read-your-writes

```text
  사용자: 주문 저장 ─(201 Created)─> 목록 화면으로 이동 ─> 조회 쪽 읽기
                    │                                     │
  프로젝터:          └──────── 아직 반영 전 ─────────────────┘   → 목록에 없음
```

- 이벤트로 유지하는 뷰의 지연 측정(평소 p50 15ms, 프로젝터 3초 정지 시 max 3006ms)은 [distributed/20](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md) 「실험: 이벤트로 유지하는 뷰의 지연」에 있다. 여기서는 해법 하나를 실험한다.
- *read-your-writes 토큰*: 명령 응답에 "내 쓰기의 위치"(이벤트 seq 또는 버전)를 실어 보내고, 조회 쪽은 체크포인트가 그 위치를 넘을 때까지 기다린 뒤(상한 있음) 읽는다.
  - 복제 지연에서의 같은 생각(LSN 비교)은 [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) 「read-your-writes를 구현한다」.

### 실험: 쓰고 바로 읽기 — 그냥 읽기 vs 토큰을 기다렸다 읽기

- 환경: 같은 PostgreSQL 17.11, JDK 21. 작성자 1개, 프로젝터 폴링 50ms(예시). 100번 반복: (a) 쓰고 바로 뷰 조회, (b) 다른 주문을 쓰고 받은 seq를 토큰으로, 체크포인트 ≥ 토큰이 될 때까지 2ms 간격 폴링(상한 1초) 후 조회.

(실험, PostgreSQL 17.11 + JDK 21, 2026-10-03)

```text
[RYW 실험] 그냥 읽기: 쓰기 직후 뷰에 없음 100/100 | 토큰 대기 후 읽기: 없음 0/100, 대기 p50 46 ms, max 56 ms
```

- 그냥 읽으면 100번 모두 없었다. 토큰을 기다리면 0번. 기다린 시간은 폴링 주기(50ms) 근처였다(재실행 3회: p50 46ms, max 48~52ms).
- 대가: 조회가 그만큼 느려진다. 프로젝터가 멈추면 상한(1초)까지 기다린 뒤 "아직 반영 중"을 보여 주거나, 그 한 건만 쓰기 모델에서 읽어 덧붙이는 대체 경로가 필요하다.

### 실험: 프로젝터 버그 → 재구축 → EXCEPT로 차이 찾기

- 주문 300건, 그중 30건 취소. 라이브 프로젝터는 `OrderCancelled`를 무시하는 버그판으로 돌렸다. 고친 프로젝터로 새 뷰(`order_view2`)를 seq 1부터 재구축해 비교했다.

(실험, PostgreSQL 17.11 + JDK 21, 2026-10-03)

```text
[재구축 실험] 쓰기 모델 기준 취소 30건 | 라이브 뷰의 취소 0건 | 재구축 뷰의 취소 30건
  라이브 EXCEPT 재구축 30행, 재구축 EXCEPT 라이브 30행, 재구축 vs 쓰기 모델 차이 0행
```

- 버그는 오류를 내지 않았다. 라이브 뷰는 조용히 30행이 틀렸다.
- 재구축 뷰는 쓰기 모델과 차이 0. 두 뷰의 `EXCEPT` 양방향 30행이 정확히 틀린 행들이다.
- 고치는 법: 버그를 고친 프로젝터로 새 뷰를 처음부터 만들고, 대조가 0이 되면 조회를 새 뷰로 바꾼다(블루-그린 재구축). 기존 뷰를 제자리에서 고치지 않는다.

### 4. 언제 CQRS를 쓰지 않나

- Fowler(2011): "대부분의 시스템에서 CQRS는 위험한 복잡도를 더한다." 또 CQRS는 시스템 전체가 아니라 **특정 부분(DDD의 Bounded Context)** 에만 써야 한다고 적는다. 그가 본 사례 다수에서 CQRS가 시스템을 심각한 어려움에 빠뜨렸다고도 한다.
- 이 노트 실험 코드에서 "주문에 필드 하나 추가"가 닿는 곳을 세면(예시 코드 기준)
  - CRUD 하나의 모델: 테이블 1, 조회 쿼리 1.
  - CQRS: 쓰기 테이블, 이벤트 페이로드, 프로젝터 `apply`, 뷰 테이블, 조회 쿼리, 그리고 기존 뷰 재구축.
- 판단 기준(주장): 읽기와 쓰기의 **모양이 실제로 다르고**(조인·검색·집계가 무겁다), 읽기 쪽 지연을 화면별로 허용할 수 있을 때. 단순 CRUD 화면이면 같은 테이블의 인덱스·뷰(DB `VIEW`)로 충분한 경우가 많다.

참고: 원고 4절 표의 "CDC ✅ 유실 없음, 순서 보장"은 조건부다. 논리 복제 슬롯이 삭제되거나 무효가 되면 CDC 소비자는 그 사이 변경을 받지 못한다(PostgreSQL 17 문서: 슬롯이 `max_slot_wal_keep_size`보다 더 뒤처지면 필요한 WAL이 지워져 복제를 계속하지 못할 수 있다. [distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md) 장애 5). 순서는 DB 커밋 순서까지이고, 브로커에 들어간 뒤에는 파티션 단위로만 유지된다.

## 쓰이는 자료구조·알고리즘

- **폴드(fold)** — 프로젝션 = 이벤트 목록을 누적 함수로 접기. 재구축 = 처음부터 다시 접기.
- **append-only 로그 + 체크포인트** — 이벤트 테이블과 "어디까지 읽었나" 위치. 위치가 단조 증가한다는 가정이 시퀀스 구멍에서 깨진다(실험). [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)
- **집합 차(EXCEPT)·대조 조인** — 라이브 뷰 vs 재구축 뷰, 뷰 vs 쓰기 모델. PostgreSQL 17.11에서 `EXCEPT`는 조인이 아니라 집합 연산 노드 `HashSetOp Except`(해시를 못 쓰면 정렬 + `SetOp`)로 실행됐고, 같은 대조를 `NOT EXISTS`로 쓰면 `Hash Anti Join`(해시 반조인)이 나왔다(1만 행 표 두 개 EXPLAIN, 2026-10-03). [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md)
- **비정규화 테이블·인덱스** — 조회 모양 그대로 미리 만든 표. [database/03-normalization](../../database/03-normalization/2-summary.md)
- **단조 위치 비교(토큰)** — read-your-writes. 체크포인트 ≥ 토큰.

## 적용 — 풀어나가는 법

### 1. 순서

1. 조회가 정말 쓰기와 다른 모양인지 본다. 아니면 멈춘다(위 4절).
2. 화면별 허용 지연을 정한다. "저장 직후 내 목록"처럼 지연 0이 필요한 화면을 따로 표시한다.
3. 변경 흐름을 고른다. outbox(이벤트) 또는 CDC. 이중 쓰기(앱이 DB와 뷰에 각각 쓰기)는 쓰지 않는다.
4. 프로젝터를 결정적 폴드로 짠다. 이벤트 ID로 멱등하게(같은 이벤트를 두 번 반영해도 같은 결과).
5. 체크포인트를 뷰 갱신과 **같은 트랜잭션**에 저장한다(뷰와 위치가 어긋나지 않게).
6. 이벤트 순서 = 커밋 순서가 되게 한다(붙이기 직렬화·CDC), 또는 구멍을 감시한다.
7. 재구축 절차와 대조 쿼리를 처음부터 만든다. 정기적으로 돌린다.
8. 지연이 0이어야 하는 화면에는 토큰 대기나 쓰기 모델 대체 경로를 둔다.

### 2. 코드 모양 (Java)

```java
// 명령 쪽: 결과에 토큰(이벤트 seq)을 실어 돌려준다
public record PlaceOrderResult(long orderId, long position) {}

@Transactional
public PlaceOrderResult handle(PlaceOrder cmd) {
    Order o = Order.place(cmd.customerId(), cmd.lines());        // 도메인 규칙
    orders.save(o);
    long pos = events.append(o.pullEvents());                    // 같은 트랜잭션, 마지막 seq 반환
    return new PlaceOrderResult(o.id(), pos);
}

// 조회 쪽: 토큰이 있으면 그 위치까지 기다린다 (상한)
public List<OrderRow> myOrders(long customerId, OptionalLong minPosition) {
    minPosition.ifPresent(p -> checkpoints.awaitAtLeast("order_view", p, Duration.ofSeconds(1)));
    return jdbc.query("SELECT * FROM order_view WHERE customer = ? ORDER BY created_at DESC", rowMapper, customerId);
}

// 프로젝터: 뷰 반영 + 체크포인트를 한 트랜잭션에
@Transactional
public void projectBatch() {
    long cp = checkpoints.get("order_view");
    for (StoredEvent e : events.after(cp, 500)) { apply(e); cp = e.seq(); }
    checkpoints.set("order_view", cp);
}
```

### 3. 진단

```sql
-- 뷰 지연: 이벤트 끝과 체크포인트의 차이
SELECT (SELECT max(seq) FROM events) - seq AS lag_events FROM checkpoint WHERE name = 'order_view';

-- 시퀀스 구멍 뒤에 남은 미반영 이벤트: 체크포인트보다 작은데 뷰에 없는 주문
SELECT e.seq, e.order_id FROM events e
WHERE e.seq <= (SELECT seq FROM checkpoint WHERE name = 'order_view')
  AND e.type = 'OrderPlaced'
  AND NOT EXISTS (SELECT 1 FROM order_view v WHERE v.order_id = e.order_id);

-- 뷰 vs 쓰기 모델 대조 (양방향)
SELECT order_id, customer, amount, status FROM order_view
EXCEPT SELECT id, customer, amount, status FROM orders;
SELECT id, customer, amount, status FROM orders
EXCEPT SELECT order_id, customer, amount, status FROM order_view;
```

## 장애 시나리오와 대처

### 1. "저장했는데 목록에 없음" — 조회 모델 지연 (커리큘럼 ⚠)

- 현상: 주문 직후 목록 화면에 방금 주문이 없다. 새로고침하면 보인다.
- 보이는 형태: 오류 없음. 지연 지표(`lag_events`)가 0보다 크다. 프로젝터 정지·배포 중이면 수 초 이상.
- 원인: 읽기 모델은 비동기로 갱신된다. 실험에서 쓰기 직후 조회는 100/100 없었다.
- 대처: 토큰 대기(실험에서 0/100, 대기 p50 46ms), 또는 방금 쓴 한 건을 쓰기 모델에서 읽어 덧붙인다. 화면에 "반영 중" 표시. 지연 지표 경보.

### 2. 뷰에서 주문이 영영 빠졌다 — 시퀀스 구멍

- 현상: 극소수 주문이 목록에 영영 안 나온다. 재시작해도 그대로다.
- 보이는 형태: 위 "시퀀스 구멍" 진단 쿼리에 행이 나온다. 동시 쓰기가 많을 때 더 많다.
- 원인: 폴링 프로젝터가 `seq > checkpoint`로 읽는데, seq는 커밋 순서가 아니다. 실험 6회에서 1,000건 중 14~25건.
- 대처: 붙이기 직렬화(advisory lock, 실험에서 0건)나 CDC. 이미 빠진 건은 재구축 또는 누락분 재반영. 정기 대조.

### 3. 프로젝터 버그로 뷰가 조용히 틀렸다

- 현상: 취소한 주문이 목록에 "주문 완료"로 남아 있다.
- 보이는 형태: 오류 로그 없음. 대조 쿼리에서만 보인다(실험에서 30행).
- 원인: 프로젝터가 이벤트 종류 하나를 처리하지 않았다.
- 대처: 고친 프로젝터로 새 뷰를 처음부터 재구축 → 대조 0 확인 → 전환. 정기 대조를 배치로 둔다.

### 4. 불필요한 CQRS → 복잡도만 증가 (커리큘럼 ⚠)

- 현상: 필드 하나 추가에 PR이 다섯 파일, 재구축 작업, 배포 순서 조율이 붙는다. 조회 화면은 단순 목록이다.
- 원인: 읽기와 쓰기의 모양이 같은 곳에 모델을 둘 두었다. Fowler가 경고한 "위험한 복잡도"다.
- 대처: 그 컨텍스트에서는 CQRS를 걷어내고 하나의 모델 + 인덱스로 되돌린다. CQRS는 조회가 실제로 무거운 컨텍스트에만 남긴다.

### 5. 재구축이 끝나지 않는다

- 현상: 이벤트가 수억 건이라 재구축에 며칠이 걸린다.
- 원인: 폴드를 처음부터 다시 돈다.
- 대처: 스냅샷(어느 seq까지 접은 상태)에서 재시작, 파티션별 병렬 재구축. 이벤트 소싱 쪽 스냅샷 실험은 [distributed/22](../../distributed/22-event-sourcing/2-summary.md).

## 핵심 문장

- CQRS는 갱신 모델과 조회 모델을 나누는 것이다. 조회 모델은 쓰기 모델에서 접어(fold) 만든 파생본이라 버리고 다시 만들 수 있다.
- 대가는 지연이다 — 쓰기 직후 조회는 실험에서 100/100 없었고, 토큰을 기다리면 0/100이었다.
- `seq > checkpoint` 폴링은 seq가 커밋 순서가 아니라서 이벤트를 영영 건너뛸 수 있다 — 실험 6회에서 1,000건 중 14~25건.
- 프로젝터 버그는 오류 없이 뷰를 틀리게 한다. 오류 로그로는 안 보이므로 재구축 + `EXCEPT` 대조로 확인한다.
- Fowler(2011): 대부분의 시스템에 CQRS는 위험한 복잡도다 — 조회가 실제로 다른 모양인 컨텍스트에만 쓴다.

## 관련 주제·근거

- 원고(이어받음, 수정하지 않음): [systems/server-design/03-data-layer.md](../../systems/server-design/03-data-layer.md) 3절 CQRS·4절 다중 저장소 정합성
- 선행: [09-domain-events](../09-domain-events/2-summary.md) · [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md)(복제 지연·read-your-writes)
- 함께: [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md) · [distributed/20-data-ownership-and-cross-service-queries](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md)(Materialized View·지연 실험) · [distributed/29-outbox-vs-dispatch-log](../../distributed/29-outbox-vs-dispatch-log/2-summary.md)(대조 배치) · [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md)
- 후속: [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) · [26-advanced-modeling-exercises](../26-advanced-modeling-exercises/2-summary.md)
- 근거
  - Fowler, "CQRS", bliki, 2011-07-14 — https://martinfowler.com/bliki/CQRS.html
  - Fowler, "CommandQuerySeparation" — https://martinfowler.com/bliki/CommandQuerySeparation.html ("The term 'command query separation' was coined by Bertrand Meyer in his book 'Object Oriented Software Construction'" — Fowler 글은 열어 확인, Meyer 책 본문은 미열람)
  - Evans, 『DDD Reference』 2015 감사의 글 — CQRS·이벤트 소싱을 Greg Young·Udi Dahan의 공으로 든다(원문 확인)
  - PostgreSQL 17 문서 9.17 Sequence Manipulation Functions(`nextval` 값은 중단돼도 재사용 안 됨 → 구멍) · 9.28.10 Advisory Lock Functions(`pg_advisory_xact_lock`)
- 실험 목록
  - 동시 작성자 4 + 폴링 프로젝터의 시퀀스 구멍 누락(직렬화 유무): PostgreSQL 17.11 + JDK 21 + pgjdbc 42.7.4, 일회용 컨테이너, 집필 3회 + 사실 점검 재실행 3회(14~25건 / 0건)
  - read-your-writes 토큰 대기 100회: 같은 환경
  - 프로젝터 버그 → 재구축 → EXCEPT 대조: 같은 환경
  - `EXCEPT` vs `NOT EXISTS` 실행 계획(1만 행 표 두 개 EXPLAIN): PostgreSQL 17.11 일회용 컨테이너 — `HashSetOp Except` / `Hash Anti Join`
