# distributed/16-outbox-and-dual-write — 이중 쓰기 문제와 transactional outbox, CDC — 정리 (힌트)

## 해결하는 문제

주문을 DB에 저장하고, "주문됨" 이벤트를 Kafka에 보낸다. 두 줄이다.

```text
  orderRepo.save(order);          // ① DB 커밋
  ──── † 여기서 프로세스가 죽으면 ────
  kafka.send("orders", event);    // ② 브로커 발행
  → 주문은 있는데 이벤트가 없다. DB만 보면 정상이라 아무도 모른다 (유실)

  순서를 바꾸면:  send → †롤백  → 이벤트는 나갔는데 주문이 없다 (유령 이벤트)
```

- *이중 쓰기(dual write)*: 한 작업이 서로 다른 두 저장소(DB·브로커)에 각각 쓰는 것. 둘을 원자적으로 묶어 줄 것이 없다.
- 2PC(14)로 묶으면 되지 않나? microservices.io는 두 이유로 배제한다. DB나 브로커가 2PC를 지원하지 않을 수 있고, 지원해도 서비스를 둘 모두에 묶는 것이 바람직하지 않다.
- 재시도로도 못 고친다. 프로세스가 죽으면 재시도할 코드도 같이 죽는다.

쉬운 예: 일기장에 "초대장 보냄"이라 쓰고 우체국에 가다 쓰러지면, 일기엔 보냈다고 적혀 있는데 초대장은 안 갔다. 그래서 일기를 쓰는 **그 자리에서** 초대장을 집 앞 발신함에 넣고, 부치는 일은 우편배달부에게 맡긴다.

똑같은 구조다. 발신함이 *outbox 테이블*, 우편배달부가 *메시지 릴레이*다.
- *transactional outbox*: 보낼 메시지를 비즈니스 데이터와 **같은 DB 트랜잭션**으로 outbox 테이블에 쓰는 패턴.
- *메시지 릴레이(message relay)*: outbox의 행을 읽어 브로커에 보내는 별도 프로세스.

실무 예: 주문 저장 + 주문됨 이벤트, 결제 승인 + 사가의 다음 걸음 메시지(15), 회원 가입 + 환영 메일 큐잉, 상품 변경 + 검색 인덱스 갱신.

기초(직접 발행의 장애 지점 3곳, 릴레이의 "발행 → 표시" 순서, 지우지 않고 표시, 독이 든 메시지)는 원본 [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md)에 있다. 이 노트는 실제 PostgreSQL·Kafka로 돌린 실험, 순서 역전, CDC(로그 tailing)의 원리, 보장의 범위를 더한다.

## 동작·원리

### 1. 구조

```text
  서비스 (한 DB 트랜잭션)                        릴레이 (따로 돈다)                 브로커
  BEGIN                                        ┌─ 폴링: SELECT … WHERE published_at IS NULL
    INSERT INTO orders …                       │        ORDER BY id … FOR UPDATE SKIP LOCKED
    INSERT INTO outbox(aggregate_id, payload)  │  또는
  COMMIT  ← 둘 다 있거나 둘 다 없다              └─ CDC: WAL/binlog에서 outbox INSERT를 읽음
                                                   │
                                                   ├─ 1) send ───────────────────────> Kafka
                                                   └─ 2) published_at = now() (폴링일 때)
```

- microservices.io "Transactional outbox"가 주는 보장: 메시지는 **DB 트랜잭션이 커밋될 때, 그리고 그때만** 보내진다. 서비스가 보낸 순서대로 브로커에 보내진다.
- 남는 문제(같은 문서): 릴레이가 발행 후 "보냈음"을 기록하기 전에 죽으면 재시작 후 다시 보낸다. **소비자는 멱등해야 한다.**
  - 그래서 이 패턴의 전달 보장은 *at-least-once*다: 유실은 없고 중복은 있을 수 있다.

### 2. 순서 — 어디까지 지켜지나

```text
  outbox id:  1(order-7#1) 2(order-7#2) 3(order-7#3) 4(order-8#1) …
  릴레이 1개:  1 2 3 4 …                       → 키별 순서 유지
  릴레이 2개 (SKIP LOCKED로 배치를 나눠 잡음):
     R1: [1..10]   R2: [11..20]   → 서로 다른 속도로 발행
     order-x#3이 11번, order-x#2가 10번이면 #3이 #2보다 먼저 나갈 수 있다 → 키별 순서 역전
```

- microservices.io "Polling publisher"의 단점에 "순서대로 발행하기 까다롭다"가 있다.
- 순서는 세 구간을 모두 지켜야 유지된다.
  - outbox → 릴레이: 릴레이 하나, 또는 같은 키(aggregate)를 한 릴레이가 맡게 나눈다.
  - 릴레이 → Kafka: 같은 키는 같은 파티션. Debezium Outbox Event Router도 `aggregateid`를 메시지 키로 쓰고, 문서는 이것이 파티션 순서 유지에 중요하다고 적는다.
  - 프로듀서 재시도: Kafka 4.1 프로듀서는 `enable.idempotence` 기본 `true`이고, 이때 재시도해도 순서가 보존된다(producer configs).
- 보장의 범위를 구분한다. 프로듀서 멱등성은 **한 프로듀서 세션 안의 재시도 중복**만 없앤다. 릴레이 프로세스가 죽고 새로 떠서 같은 행을 다시 보내면 새 메시지다. 아래 실험의 중복 127건은 `enable.idempotence=true`(기본값)에서 나왔다.

### 실험: 직접 발행 vs outbox — 프로세스를 진짜로 죽인다

- 환경: 전용 일회용 컨테이너 PostgreSQL 17.11 + Kafka 4.1.0(KRaft 단일 노드, 파티션 1), Java 21 + kafka-clients 4.1.0, PostgreSQL JDBC 42.7.4. 2026-10-01.
- "죽음" = `Runtime.getRuntime().halt(1)` — JVM이 정리 없이 즉시 끝난다. 셸이 다음 주문·다음 릴레이 실행으로 다시 띄운다.

```java
// A. 직접 발행: 10번째 주문마다 커밋 직후·발행 전에 죽는다
c.createStatement().executeUpdate("insert into orders values (" + i + ", 100)");   // 자동 커밋
if (i % every == 0) halt("order " + i + " committed, not published");
pr.send(new ProducerRecord<>(topic, "order-" + i, "OrderCreated:" + i)).get();

// B. outbox 릴레이: 배치 10건을 잠그고 → 하나씩 발행 → 표시 → 배치 끝에 커밋
ResultSet rs = c.createStatement().executeQuery(
    "select id, aggregate_id, seq, payload from outbox where published_at is null " +
    "order by id limit " + batch + " for update skip locked");
for (...) {
    pr.send(new ProducerRecord<>(topic, "order-" + aggId, payload)).get();     // 1) 발행
    if (id % 9 == 0 && 처음이면) halt(...);                                     // 발행 후·표시 전 죽음(행마다 한 번)
    c.createStatement().executeUpdate("update outbox set published_at = now() where id = " + id);  // 2) 표시
}
c.commit();
```

(실험, PostgreSQL 17.11 + Kafka 4.1.0, 2026-10-01)

```text
=== A. 직접 발행: 주문 200건, 10건마다 커밋 직후 프로세스 halt → 재시작해 다음 주문부터
재시작 20 회
topic=w14-direct 전체 180, 서로 다른 180, 중복 0, 키별 순서 역전 0
DB orders 200, outbox 0, 미발행 0
=== B. outbox: 같은 200건 (주문당 이벤트 1개), 릴레이는 outbox id가 9의 배수인 행을 발행한 직후 행마다 한 번 halt (배치 10, 배치 끝에 표시·커밋)
R1 drained, sent 10
릴레이 실행 23 회
topic=w14-outbox 전체 327, 서로 다른 200, 중복 127, 키별 순서 역전 0
DB orders 200, outbox 200, 미발행 0
=== C. 순서: 주문 100건 x 이벤트 3개, 릴레이 1개 vs 2개 동시 (halt 없음, 배치 10)
R1 drained, sent 300
topic=w14-outbox2 전체 300, 서로 다른 300, 중복 0, 키별 순서 역전 0
R1 drained, sent 140
R2 drained, sent 160
topic=w14-outbox2 전체 300, 서로 다른 300, 중복 0, 키별 순서 역전 15
```

- A: 크래시 20번 = 유실 20건. DB에는 주문 200건이 멀쩡히 있다. **오류 로그는 크래시뿐이고, 무엇이 빠졌는지는 DB와 토픽을 대조해야 안다.**
- B: 크래시 22번(9의 배수 id 22개), 서로 다른 메시지 200 = 유실 0. 대신 중복 127. 표시를 **배치 끝에 한 번 커밋**하므로, 배치 중간에 죽으면 그 배치에서 이미 보낸 행도 전부 다시 나간다. 크래시당 중복이 1이 아니라 평균 약 5.8이다.
- C: 릴레이를 2개로 늘리자 같은 주문 안의 이벤트 순서가 15번 뒤집혔다. 수는 실행마다 다르다(다시 돌렸을 때 18번, 릴레이 몫은 130·170). A·B의 수는 다시 돌려도 같았다. B는 크래시 지점이 정해져 있어 결정적이다.

### 실험: 릴레이가 매번 같은 지점 전에 죽으면 — 진행 0, 재발행 폭주

(실험, 같은 환경, 2026-10-01) 처음에 실수로 "실행마다 7번째 발행 직후 halt"로 돌렸다. 배치 크기는 10, 표시는 배치 끝에 커밋.

```text
94회 재시작 후 수동 중단
topic=w14-outbox 전체 658, 서로 다른 7, 중복 651, 키별 순서 역전 0
DB orders 200, outbox 200, 미발행 200
```

- 릴레이는 매번 1~7번 행을 보내고 표시 커밋 전에 죽었다. 같은 7건이 94번 나갔고, 미발행은 계속 200이었다.
- 원본 07-outbox의 "독이 든 메시지" 한계와 같은 모양이다. 유실은 막았지만 **진행이 막힌다.** 그리고 메시지 수만 보면 "열심히 발행 중"처럼 보인다.
- 대처: 표시를 행 단위(또는 작은 배치)로 커밋한다. 같은 행에서 반복해 실패하면 그 행을 격리(별도 상태·DLQ)하고 다음으로 넘어간다. outbox 미발행 건수와 **가장 오래된 미발행 행의 나이**에 알람을 건다.

### 3. CDC(transaction log tailing) — 폴링 대신 DB 로그를 읽는다

```text
  INSERT INTO outbox … COMMIT ──> WAL ──> 논리 디코딩 슬롯 ──> 커넥터(Debezium 등) ──> Kafka
                                          (커밋된 변경만, 커밋 순서로)
  슬롯은 restart_lsn(소비자가 아직 필요로 할 수 있는 가장 오래된 위치) 이후의 WAL을
  지우지 못하게 붙잡는다 — restart_lsn은 소비자가 확인한 confirmed_flush_lsn보다 앞설 수 있다
```

- microservices.io "Transaction log tailing": outbox에 들어간 메시지를 DB 트랜잭션 로그(MySQL binlog, Postgres WAL, DynamoDB streams)에서 읽어 발행한다. 단점 중 하나가 "중복 발행을 피하기 까다롭다"이다 — 즉 CDC도 at-least-once다.
- 상세(초기 스냅샷, 슬롯 운영, DDL 변경)는 [data-engineering/05-change-data-capture](../../data-engineering/05-change-data-capture/2-summary.md)에서 다룬다.

(실험, PostgreSQL 17.11 전용 컨테이너, `wal_level=logical`, `test_decoding` 플러그인, 2026-10-01)

```text
 slot_name |    lsn
-----------+-----------
 w14_slot  | 0/1A802A8
-- 커밋한 트랜잭션(주문 + outbox)과 롤백한 트랜잭션을 하나씩 실행한 뒤 peek:
    lsn    | xid  | data
-----------+------+-----------------------------------------------------------------------------
 0/1A802A8 | 1372 | BEGIN 1372
 0/1A802A8 | 1372 | table public.orders: INSERT: id[integer]:9001 amount[integer]:100
 0/1A80328 | 1372 | table public.outbox: INSERT: id[bigint]:301 aggregate_id[integer]:9001 seq[integer]:1 payload[text]:'order-9001#1' published_at[timestamp with time zone]:null
 0/1A80430 | 1372 | COMMIT 1372
--- 슬롯을 소비하지 않은 채 쓰기 2만 건
 slot_name | active | retained_wal | unconsumed
 w14_slot  | f      | 2548 kB      | 2548 kB
```

- LSN·xid는 실행마다 다르다. 같은 절차를 두 번 돌려 두 번 다 `retained_wal` 2548 kB였다.

- 롤백한 트랜잭션(주문 9002)은 아예 나오지 않았다. 커밋된 트랜잭션은 주문과 outbox INSERT가 **한 트랜잭션 묶음(BEGIN…COMMIT)** 으로 나왔다. outbox의 "커밋될 때만 발행"이 로그 수준에서 성립하는 이유다.
- 연결된 소비자가 없어도(`active = f`) 슬롯이 WAL을 붙잡았다. PostgreSQL 17 문서: 슬롯은 크래시를 넘어 유지되고, 소비자 상태를 모른 채 필요한 WAL 삭제를 막는다. `max_slot_wal_keep_size` 기본값은 -1(제한 없음)이었다(이 컨테이너에서 `SHOW`로 확인).

## 쓰이는 자료구조·알고리즘

- **append-only 로그 테이블** — outbox는 단조 증가 id로 덧붙이는 표다. 릴레이는 id 순서로 읽는다. 커리큘럼 🔧 칸의 "로그 테이블 폴링". [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md)의 이벤트 저장소가 같은 모양이다.
- **부분 인덱스** — `CREATE INDEX … ON outbox(id) WHERE published_at IS NULL`. 미발행 행만 담아 폴링 비용을 표 크기와 떼어 놓는다(실험 코드의 `outbox_unpublished`).
- **`FOR UPDATE SKIP LOCKED`** — 여러 릴레이가 같은 행을 잡지 않게 한다. 중복은 줄지만 순서는 깨질 수 있다(실험 C).
- **WAL + 논리 디코딩** — 커리큘럼 🔧 칸의 CDC. 커밋 순서로 변경을 내보내는 DB 로그를 그대로 메시지 원천으로 쓴다. [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md)
- **멱등 소비(처리한 메시지 id 집합)** — at-least-once를 "효과는 한 번"으로 바꾸는 받는 쪽 장치. [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
- **키 → 파티션 해시** — 같은 aggregate의 이벤트를 같은 파티션에 넣어 순서를 지킨다.

## 적용 — 풀어나가는 법

### 1. 순서

```text
  ① 비즈니스 쓰기와 outbox 쓰기를 같은 트랜잭션에 (커밋 1번)
  ② 릴레이: 발행 → 표시. 표시는 행 단위나 작은 배치로 커밋
  ③ 메시지 키 = aggregate id, outbox 행 id(또는 이벤트 id)를 헤더에 → 소비자 멱등
  ④ 순서가 필요하면 릴레이 1개(리더 선출로 이중화) 또는 aggregate 단위로 분담
  ⑤ 미발행 부분 인덱스, 발행된 행 보관 기간·정리
  ⑥ 알람: 미발행 건수, 가장 오래된 미발행 행의 나이, (CDC면) 슬롯 지연 WAL
```

### 2. Spring 코드 모양

```java
@Transactional
public void placeOrder(PlaceOrder cmd) {
    Order order = orderRepository.save(Order.create(cmd));
    outboxRepository.save(new OutboxEvent(            // 같은 DB, 같은 트랜잭션
        UUID.randomUUID(), "Order", order.getId().toString(), "OrderCreated", toJson(order)));
    // kafkaTemplate.send(...) 를 여기서 부르지 않는다 — @Transactional이 롤백해도 전송은 롤백되지 않는다
}
```

```java
// 폴링 릴레이 (한 행씩 표시 커밋)
@Scheduled(fixedDelay = 500)
public void relay() {
    for (OutboxEvent e : tx.execute(s -> outboxRepository.lockUnpublished(100))) {   // FOR UPDATE SKIP LOCKED
        kafkaTemplate.send("outbox.event." + e.aggregateType(), e.aggregateId(), e.payload())
                     .get(10, TimeUnit.SECONDS);                                   // 브로커 ack 확인
        tx.executeWithoutResult(s -> outboxRepository.markPublished(e.id()));       // 그다음 표시
    }
}
```

- 위 코드는 잠금 트랜잭션과 표시 트랜잭션을 나눈 단순화다. 릴레이를 여러 개 띄우면 같은 행을 두 번 집을 수 있으므로, 순서가 필요하면 릴레이를 하나로 유지한다.
- CDC를 쓰면 릴레이 코드 대신 커넥터 설정을 운영한다. Debezium Outbox Event Router(Debezium 3.x 문서)는 outbox 표의 `id`(이벤트 id, 헤더로 → 중복 제거에 사용 가능), `aggregatetype`(토픽 라우팅, 기본 `outbox.event.${routedByValue}`), `aggregateid`(메시지 키), `type`, `payload` 열을 기대한다.

### 3. 진단 명령

```sql
-- 릴레이가 멈췄나: 미발행 건수와 가장 오래된 미발행의 나이
SELECT count(*), now() - min(created_at) AS oldest_unpublished
FROM outbox WHERE published_at IS NULL;

-- CDC 슬롯이 WAL을 붙잡고 있나 (PostgreSQL)
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots;
```

```bash
# 소비자가 따라오고 있나 (Kafka 4.1)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group order-projector   # LAG 열
```

## 장애 시나리오와 대처

### 1. DB 커밋 후 발행 전 크래시 → 이벤트 유실 (커리큘럼 ⚠)

- **현상**: 주문은 있는데 배송·알림이 안 나간다. 배포·재시작 시각 근처의 주문에 몰린다.
- **보이는 형태**: 오류 로그 없음(또는 프로세스 종료 로그뿐). DB 주문 수 > 토픽 메시지 수(실험 A: 200 vs 180).
- **원인**: 직접 발행(이중 쓰기). 커밋과 발행 사이에서 죽으면 발행할 주체가 사라진다.
- **대처**: outbox로 바꾼다. 이미 빠진 건은 DB와 토픽(또는 하위 시스템)을 대조해 재발행한다. 이 대조는 이벤트를 원천 상태에서 다시 만들 수 있을 때만 된다(29).

### 2. 순서 역전 (커리큘럼 ⚠)

- **현상**: 소비자가 `OrderShipped`를 `OrderPaid`보다 먼저 받는다. "없는 결제의 배송" 같은 오류가 난다.
- **보이는 형태**: 소비자 로그의 상태 전이 위반. 키별 seq가 줄어든다(실험 C: 릴레이 2개에서 15번).
- **원인**: 릴레이 여럿이 같은 aggregate의 행을 나눠 집었다. 또는 메시지 키를 aggregate id로 두지 않아 다른 파티션으로 갔다.
- **대처**: 릴레이 1개(리더 선출로 이중화), aggregate 키 = 메시지 키. 소비자 쪽에서도 seq를 보고 오래된 이벤트를 무시하거나 대기시킨다.

### 3. 중복 발행이 효과로 이어진다

- **현상**: 같은 주문에 포인트가 두 번 적립된다. 릴레이 재시작 직후에 몰린다.
- **보이는 형태**: 같은 이벤트 id로 처리 로그 두 줄. 실험 B: 크래시 22번에 중복 127건.
- **원인**: outbox는 at-least-once다. 표시 전 크래시면 재발행한다. Kafka 프로듀서 멱등성은 새 프로세스의 재발행을 막지 못한다.
- **대처**: 소비자 멱등(처리한 이벤트 id를 같은 트랜잭션에 기록). 표시 커밋 단위를 줄여 중복 폭을 줄인다.

### 4. 릴레이 진행 0, 재발행 폭주

- **현상**: 토픽 메시지는 계속 늘어나는데 하위 시스템은 새 주문을 못 받는다.
- **보이는 형태**: outbox 미발행 건수가 줄지 않는다. 토픽에 같은 페이로드가 수백 번(실험: 658건 중 서로 다른 7건). 릴레이가 같은 시점에 반복 재시작.
- **원인**: 표시를 배치 끝에 커밋하는데, 배치 안의 같은 지점에서 매번 죽는다(특정 행의 직렬화 오류, 메모리 초과, 너무 큰 메시지 등).
- **대처**: 행 단위 표시, 반복 실패 행 격리, "가장 오래된 미발행 나이" 알람.

### 5. CDC 슬롯이 버려져 디스크가 찬다

- **현상**: DB 서버 디스크가 꾸준히 차고, 결국 쓰기가 멈춘다.
- **보이는 형태**: `pg_replication_slots`에 `active = f`인 슬롯, `retained_wal`이 계속 커진다. `pg_wal` 디렉터리 크기 증가.
- **원인**: 커넥터를 내렸는데 슬롯을 지우지 않았다. 슬롯은 소비자 상태를 모른 채 WAL을 붙잡는다(PostgreSQL 17 47.2). `max_slot_wal_keep_size` 기본 -1이면 상한도 없다.
- **대처**: 쓰지 않는 슬롯은 `pg_drop_replication_slot`. `max_slot_wal_keep_size`로 상한을 둔다. 대가: 슬롯이 그 크기보다 뒤처지면 필요한 WAL이 지워져 그 슬롯으로는 더 이어 받지 못할 수 있다(PostgreSQL 17 19.6). 그러면 CDC를 처음부터 다시 맞춰야 한다. 슬롯 지연에 알람.

## 핵심 문장

- DB 커밋과 브로커 발행은 원자적으로 묶이지 않는다. 그 사이에서 죽으면 이벤트가 유실되고, 재시도 코드도 같이 죽는다.
- outbox는 이벤트를 비즈니스 데이터와 같은 트랜잭션에 써서 커밋됐을 때만 발행되고, 커밋됐다면 릴레이가 결국 발행하게 한다.
- 릴레이는 발행한 뒤 표시하므로 중복이 남는다. 전달은 at-least-once이고, 소비자 멱등이 짝으로 필요하다.
- 순서는 outbox → 릴레이 → 파티션 → 프로듀서 재시도 구간을 모두 지켜야 유지된다. 릴레이를 늘리면 깨질 수 있다.
- CDC는 폴링 대신 DB 로그에서 커밋된 outbox 행을 읽는다. 슬롯을 버려 두면 WAL이 쌓인다.

## 관련 주제·근거

- 선행
  - [15-saga](../15-saga/2-summary.md) — 각 걸음이 "DB 갱신 + 다음 메시지"를 해야 하는 이유
  - [14-two-phase-commit](../14-two-phase-commit/2-summary.md) — DB와 브로커를 2PC로 묶지 않는 이유
  - 원본 [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md) — 장애 지점·릴레이 순서·독이 든 메시지
- 후속·연결
  - [17-queues-logs-and-delivery-semantics](../17-queues-logs-and-delivery-semantics/2-summary.md) · [18-consumer-failure-handling](../18-consumer-failure-handling/2-summary.md) — at-least-once와 소비자 멱등
  - [29-outbox-vs-dispatch-log](../29-outbox-vs-dispatch-log/2-summary.md) — 발행 시점에 기록하는 방식과의 경계, 대조 배치 실험
  - [data-engineering/05-change-data-capture](../../data-engineering/05-change-data-capture/2-summary.md) — 스냅샷·복제 슬롯·DDL
  - [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md) — WAL
  - [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md) · [ops-patterns/12-leader-election](../../ops-patterns/12-leader-election/2-summary.md)(릴레이 하나 유지)
  - [systems/outbox-vs-dispatch-log](../../systems/outbox-vs-dispatch-log/2-summary.md) — 폴링 vs CDC 비교표
- 근거
  - microservices.io "Pattern: Transactional outbox" — 2PC 배제 이유, "if and only if the database transaction commits", 순서 요구, 릴레이 중복·소비자 멱등 <https://microservices.io/patterns/data/transactional-outbox.html>
  - microservices.io "Polling publisher"(순서 발행이 까다로움) <https://microservices.io/patterns/data/polling-publisher.html> · "Transaction log tailing"(binlog·WAL·DynamoDB streams, 중복 발행 회피가 까다로움) <https://microservices.io/patterns/data/transaction-log-tailing.html>
  - Richardson, 『Microservices Patterns』(2018) 3장 — transactional messaging
  - Debezium 3.x "Outbox Event Router" — 기대 열(id·aggregatetype·aggregateid·type·payload), 이벤트 id 헤더로 중복 제거 가능, aggregateid = 키(파티션 순서), `route.topic.replacement` 기본 `outbox.event.${routedByValue}` <https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html>
  - Kafka 4.1 Producer Configs — `enable.idempotence` 기본 true, 재시도 시 순서 보존 조건 <https://kafka.apache.org/41/configuration/producer-configs/>
  - PostgreSQL 17 47.2 Logical Decoding Concepts — 슬롯은 크래시를 넘어 유지, 소비자 상태를 모른 채 WAL·카탈로그 행 제거를 막음 <https://www.postgresql.org/docs/17/logicaldecoding-explanation.html>
  - PostgreSQL 17 19.6 Replication — `max_slot_wal_keep_size` 기본 -1(무제한), 넘으면 필요한 WAL이 지워져 슬롯으로 이어 받지 못할 수 있음 <https://www.postgresql.org/docs/17/runtime-config-replication.html>
- 실험 목록
  - `OutboxExp.java` + `exp16.sh` — 전용 PostgreSQL 17.11 + Kafka 4.1.0 컨테이너, Java 21. A 직접 발행 200건·halt 20번 → 180건(유실 20) / B outbox·릴레이 halt 22번 → 서로 다른 200·중복 127 / C 릴레이 1개 vs 2개 → 키별 순서 역전 0 vs 15
  - 재발행 폭주 — `exp16.sh` 끝 주석의 명령(`relay … 10 7 R1`)을 94번 반복: 실행마다 7번째 발행 후 halt(배치 커밋 전) → 658건 중 서로 다른 7, 미발행 200. 사실 점검 때 같은 절차로 다시 돌려 같은 수가 나왔다
  - `exp16b.sh` — PostgreSQL 17.11 `test_decoding` 슬롯: 롤백 트랜잭션 미출력, 커밋 트랜잭션이 BEGIN…COMMIT 묶음으로 출력, 미소비 슬롯이 WAL 2548 kB 보유(두 번 실행 같음)
