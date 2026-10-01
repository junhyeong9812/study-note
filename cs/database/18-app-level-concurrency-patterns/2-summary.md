# database/18-app-level-concurrency-patterns — 앱 수준 동시성 패턴: FOR UPDATE, 조건부 UPDATE, 원자적 upsert, 유니크 제약 — 정리 (힌트)

## 해결하는 문제

DB는 격리 수준을 주지만, 앱 코드의 흔한 모양은 기본 격리 수준(PostgreSQL 17 READ COMMITTED, MySQL 8.4 REPEATABLE READ)에서 보호되지 않는다.

```text
  check-then-act (확인하고 행동하기)
  요청 A: SELECT ... 이메일 있나? → 없다 ─────────── INSERT a@x.com
  요청 B:        SELECT ... 이메일 있나? → 없다 ─────────── INSERT a@x.com
  → 둘 다 "없다"를 보고 둘 다 넣는다. 확인과 행동 사이에 틈이 있다.
```

- 확인(SELECT)과 행동(INSERT·UPDATE) 사이에 다른 트랜잭션이 끼어들 수 있다. 격리 수준을 높이지 않는 한 이 틈은 앱이 막아야 한다.
- 막는 도구는 네 가지다.
  1. 확인과 행동을 **한 문장**으로 합친다 — 조건부 UPDATE, 원자적 upsert.
  2. **제약**에게 맡긴다 — UNIQUE·CHECK. 틈이 있어도 DB가 두 번째를 거부한다.
  3. 확인할 때 **잠근다** — `SELECT ... FOR UPDATE`.
  4. 버전으로 **검증**한다 — 17번 OCC.

쉬운 예: 공연 좌석 예매다.
- "빈자리인지 보고 → 결제 → 좌석 확정"을 두 사람이 동시에 하면 둘 다 확정된다.
- 해법: "빈자리이면 내 것으로" 한 동작으로 확정하거나(조건부 UPDATE), 좌석 번호에 유일성을 건다(UNIQUE).

똑같은 구조다.\
DDIA 7장은 이것을 lost update 방지(원자적 쓰기·명시적 잠금·자동 감지·compare-and-set)와 write skew로 정리한다.

실무 예:
- 회원 가입 버튼 더블 클릭 → 같은 이메일 계정 두 개.
- 선착순 쿠폰·재고 → 재고가 음수가 된다(api-design 03).
- 결제 API를 트랜잭션 안에서 호출 → 결제사가 느려지자 재고 행 락이 수 초씩 잡혀 전체가 멈춘다.

## 동작·원리

### 1. 조건부 UPDATE — 확인과 차감을 한 문장으로

```text
  나쁜 모양 (확인 따로, 차감 따로)            좋은 모양 (한 문장)
  SELECT qty → 1                               UPDATE inv SET qty = qty - 1
  if (qty > 0)                                  WHERE id = 1 AND qty > 0
     UPDATE inv SET qty = qty - 1              → 영향 행 1 = 성공, 0 = 품절
  (두 요청 모두 qty=1을 보면 → -1)
```

- 한 문장 안에서 "조건 검사 + 변경"은 행 락 아래에서 일어난다.
  - PostgreSQL 17 READ COMMITTED: 앞 트랜잭션이 행을 고치는 중이면 기다린다. 커밋 뒤 **새 버전으로 WHERE를 다시 평가**한다(13.2.1). 그래서 `qty > 0`이 최신 값으로 검사된다.
  - MySQL 8.4 InnoDB: `UPDATE`는 최신 커밋 버전을 잠그고 조건을 본다(17.7.2.3).
- 영향받은 행 수가 결과다. 0이면 품절로 처리한다.

로컬 재현(예시, PostgreSQL 17.11) — 재고 100, 8세션이 각 30번 구매를 시도(각 시도 사이 1ms 대기).

```text
  방식                                      최종 재고   판매 수
  SELECT 확인 → UPDATE qty = qty - 1          -7        107    ← 초과 판매
  UPDATE ... WHERE qty > 0 (조건부)             0        100
```

- 첫 방식은 `qty = qty - 1`로 **원자적으로 차감**했는데도 음수가 됐다. 차감이 아니라 **확인**이 문장 밖에 있었기 때문이다.
- 이중 방어: `CHECK (qty >= 0)` 제약을 함께 둔다. 코드가 틀려도 DB가 거부한다(PostgreSQL 23514 `check_violation`, MySQL 8.4 `ERROR 3819 (HY000): Check constraint '...' is violated` — 로컬 재현).

### 2. 유니크 제약 — check-then-insert의 최후 방어선

```text
  UNIQUE 없음                              UNIQUE(email)
  A: SELECT → 0건 ─ INSERT → 성공            A: SELECT → 0건 ─ INSERT → 성공 ─ COMMIT
  B: SELECT → 0건 ─ INSERT → 성공            B: SELECT → 0건 ─ INSERT → (A 커밋까지 대기) → 23505
  → 같은 이메일 2행                         → 1행만 남는다
```

로컬 재현(예시, PostgreSQL 17.11): 위 두 경우를 그대로 돌렸다. UNIQUE가 없을 때 `a@x.com`이 2행, 있을 때 B가 `ERROR: duplicate key value violates unique constraint "member_uq_email_key"`를 받았다.

- 유니크 검사는 인덱스로 한다. 진행 중인 트랜잭션이 같은 키를 넣었으면 그 결과를 기다린 뒤 판정한다. 그래서 동시 요청에도 뚫리지 않는다.
- 앱에서 `SELECT`로 먼저 확인하는 것은 **친절한 에러 메시지용**이다. 정합성은 제약이 지킨다.
- 오류 형태
  - PostgreSQL: SQLSTATE `23505`
  - MySQL: `ERROR 1062 (23000): Duplicate entry ...`
  - Spring 6 JDBC(`JdbcTemplate`): 둘 다 `DuplicateKeyException`(기본 번역기 `SQLStateSQLExceptionTranslator.indicatesDuplicateKey`: SQLSTATE 23505, 또는 23000 + MySQL 1062)
  - Spring JPA/Hibernate(`saveAndFlush` 등): 보통 `DataIntegrityViolationException`(`HibernateJpaDialect`가 Hibernate `ConstraintViolationException`을 이렇게 번역). 그래서 「적용」 2절 코드는 이 상위 타입을 잡는다.

### 3. 원자적 upsert — "없으면 넣고 있으면 고친다"를 한 문장으로

```sql
-- PostgreSQL 17
INSERT INTO daily_cnt (day, item, cnt) VALUES ('2026-10-01', 1, 1)
ON CONFLICT (day, item) DO UPDATE SET cnt = daily_cnt.cnt + 1;

INSERT INTO member (email) VALUES ('a@x.com')
ON CONFLICT (email) DO NOTHING RETURNING id;    -- 이미 있으면 0행 반환

-- MySQL 8.4 (행 별칭 형식. VALUES() 함수 형식은 deprecated)
INSERT INTO daily_cnt VALUES ('2026-10-01', 1, 1) AS new
ON DUPLICATE KEY UPDATE cnt = daily_cnt.cnt + new.cnt;
```

- PostgreSQL 17 문서: `ON CONFLICT DO UPDATE`는 "독립적인 오류가 없는 한 높은 동시성에서도" INSERT 또는 UPDATE 중 하나의 결과를 보장한다.
- 로컬 재현(예시, PostgreSQL 17.11): 8세션 × 200번 upsert → `cnt = 1600`. 중복 키 오류 없이 정확했다.
- MySQL의 영향 행 수: 새로 넣음 1, 기존 행 갱신 2, 기존 값 그대로 0(`CLIENT_FOUND_ROWS` 플래그면 1). 로컬 재현(예시, MySQL 8.4.10)에서 1 → 2 → 0이 나왔다.
- 주의: 유니크 인덱스가 **여럿**인 테이블에 `ON DUPLICATE KEY UPDATE`는 피하라고 MySQL 문서가 적는다. 어느 키에 걸렸는지에 따라 다른 행이 갱신될 수 있다.
- 문법 세부는 [languages/sql/syntax/52-upsert](../../../languages/sql/syntax/52-upsert/2-summary.md).

### 4. `SELECT ... FOR UPDATE` — 읽으면서 잠근다

```sql
BEGIN;
SELECT balance FROM account WHERE id = :id FOR UPDATE;   -- 다른 FOR UPDATE·UPDATE는 여기서 대기
-- 앱 로직: 한도 검사, 수수료 계산 ...
UPDATE account SET balance = :newBalance WHERE id = :id;
COMMIT;
```

- 한 문장으로 표현하기 어려운 로직(여러 규칙 검사, 여러 테이블 계산)에 쓴다.
- 잠금은 커밋까지 간다. 그래서 **트랜잭션 안에서 하는 일이 짧아야** 한다.
- 여러 행을 잠글 때는 순서를 통일한다(`ORDER BY id FOR UPDATE`, 15번).
- 큐 소비처럼 "잠긴 건 건너뛰고 다음 것"이 필요하면 `FOR UPDATE SKIP LOCKED`(PostgreSQL 17 SELECT 문서, MySQL 8.4 17.7.2.4) — [languages/sql/syntax/57](../../../languages/sql/syntax/57-explicit-locking-and-deadlock/2-summary.md) 2절.

### 5. "없는 행"은 FOR UPDATE로 잠글 수 없다

```text
  MySQL 8.4 REPEATABLE READ, UNIQUE(email), 기존 키 'a@x.com', 'm@x.com'
  A: SELECT ... WHERE email='c@x.com' FOR UPDATE → 0행, 갭 락 ('a'~'m' 사이)
  B: SELECT ... WHERE email='c@x.com' FOR UPDATE → 0행, 같은 갭 락 (갭 락끼리는 호환)
  A: INSERT 'c@x.com' → B의 갭 락 때문에 대기
  B: INSERT 'c@x.com' → A의 갭 락 때문에 대기 → 사이클 → ERROR 1213
```

로컬 재현(예시, MySQL 8.4.10) — 두 세션이 `SLEEP(1)`을 사이에 두고 위 순서로 돌렸다.

```text
  data_locks:  14584 uk_email RECORD X,GAP GRANTED 'm@x.com', 2
               14585 uk_email RECORD X,GAP GRANTED 'm@x.com', 2
  세션 A: ERROR 1213 (40001) Deadlock found ...    세션 B: INSERT 성공
```

- 갭 락은 "그 틈에 넣지 마라"만 막는다. 같은 갭에 여러 트랜잭션이 동시에 갭 락을 가질 수 있다(17.7.1). 그래서 "없으면 넣기"를 FOR UPDATE로 지키려 하면 교착이 된다.
- PostgreSQL은 없는 행에 행 락을 걸지 않는다(SERIALIZABLE의 SIRead 술어 락은 별개 — 이것은 막지 않고, 위험을 검출하면 문장 실행 중이나 커밋 때 40001로 실패시킨다. 동시 키 INSERT에서는 23505로 나오기도 한다, 13.2.3·13.5). 두 세션 모두 0행을 보고 지나가 결국 INSERT에서 부딪힌다.
- 결론: "없는 것"은 **유니크 제약 + upsert**로 막는다. 잠글 대상이 없으면 DDIA 7장의 **충돌 구체화**(잠글 행을 미리 만들어 두기, 예: 회의실 × 시간 칸 테이블)를 쓴다.

### 6. 트랜잭션 안의 원격 호출 — 락을 쥔 채 기다린다

```text
  BEGIN
  UPDATE inv ... (행 락 획득)
  ── 결제 API 호출 3초 ── DB 입장: "idle in transaction", 락은 그대로
  COMMIT (락 해제)
  → 같은 행을 원하는 모든 요청이 3초씩 줄을 선다
```

로컬 재현(예시, PostgreSQL 17.11) — 세션 A가 UPDATE 뒤 셸에서 4초 쉬고(원격 호출 흉내) 커밋, 세션 B가 같은 행을 UPDATE.

```text
   pid  |        state        | wait_event_type |  wait_event   | blocked_by
   7800 | idle in transaction | Client          | ClientRead    | {}
   7809 | active              | Lock            | transactionid | {7800}
  B: UPDATE 1   Time: 3518.110 ms
```

- DB는 A가 아무것도 안 하는데도 락을 풀 수 없다. 트랜잭션이 끝나지 않았기 때문이다.
- 서버 측 안전장치: `idle_in_transaction_session_timeout`(PostgreSQL 17 기본 0 = 끔). 1초로 두고 재현하니 `FATAL: terminating connection due to idle-in-transaction timeout`(SQLSTATE 25P03)으로 연결이 끊기고 트랜잭션이 롤백됐다.

## 쓰이는 자료구조·알고리즘

- **유니크 인덱스(B+트리) 조회** — 유니크 검사는 인덱스에서 같은 키를 찾는 것이다. 진행 중 삽입이 있으면 그 결과를 기다린다. database [08-btree-indexes](../08-btree-indexes/2-summary.md), [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **compare-and-set** — `UPDATE ... WHERE qty > 0`, `WHERE version = ?`는 DB 수준 CAS다. [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)
- **갭(범위) 락** — 인덱스 키 사이의 구간을 잠가 팬텀 삽입을 막는다(CMU L18의 index locking·gap lock). 15번.
- **작업 큐 = 잠금 + 건너뛰기** — `SKIP LOCKED`는 잠긴 행을 건너뛰어 여러 소비자가 서로 다른 행을 집게 한다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 패턴 고르기

| 하려는 일 | 1순위 | 대안 |
|---|---|---|
| 재고·잔액·카운터 차감 | 조건부 UPDATE + CHECK 제약 | `FOR UPDATE` 후 계산 |
| 중복 가입·중복 발급 막기 | UNIQUE + `ON CONFLICT DO NOTHING` / 1062·23505 처리 | — |
| 일별 집계 누적 | upsert(`DO UPDATE SET cnt = cnt + 1`) | — |
| 여러 규칙을 검사하는 변경 | `SELECT ... FOR UPDATE`(짧게, 순서 통일) | 버전 컬럼(17번) |
| 여러 요청에 걸친 편집 | 버전 컬럼(17번) | 오프라인 락(52번) |
| 작업 큐 | `FOR UPDATE SKIP LOCKED` | 전용 큐 |

### 2. Spring 코드 모양

```java
// 재고 차감: 조건부 UPDATE, 영향 행 수로 판정
@Modifying
@Query("update Inventory i set i.qty = i.qty - :n where i.id = :id and i.qty >= :n")
int decrease(@Param("id") long id, @Param("n") int n);

@Transactional
public void order(long itemId, int n) {
    if (inventoryRepo.decrease(itemId, n) == 0) throw new SoldOutException();
    orderRepo.save(new Order(itemId, n));
}

// 중복 가입: 제약에 맡기고 예외를 도메인 에러로
try {
    memberRepo.saveAndFlush(new Member(email));   // flush해야 여기서 제약 위반이 난다
} catch (DataIntegrityViolationException e) {    // DuplicateKeyException은 이 하위
    throw new EmailAlreadyUsedException(email);
}
```

- JPA `save`만으로는 INSERT가 커밋 시점까지 미뤄질 수 있다. 예외를 이 자리에서 잡으려면 `saveAndFlush`나 명시적 `flush`를 쓴다.
- PostgreSQL에서 제약 위반이 나면 **그 트랜잭션은 실패 상태**다. 같은 트랜잭션에서 이어서 쿼리할 수 없다. "넣어 보고 실패하면 조회" 흐름은 `ON CONFLICT DO NOTHING`이나 별도 트랜잭션으로 한다.

### 3. 원격 호출은 트랜잭션 밖으로

```text
  1) 짧은 트랜잭션: 주문 PENDING 저장, 재고 예약(조건부 UPDATE)  → COMMIT
  2) 트랜잭션 밖: 결제 API 호출 (타임아웃·멱등 키)
  3) 짧은 트랜잭션: 결과에 따라 PAID 확정 또는 예약 취소(보상)
```

- 대가는 중간 상태(PENDING)가 생기는 것이다. 멱등 키와 보상 처리가 필요하다([ops-patterns/08-saga](../../ops-patterns/08-saga/2-summary.md), [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)).
- 커밋 뒤에 할 일(메시지 발행 등)은 아웃박스로 옮긴다([ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md)).

### 4. 진단

```sql
-- PostgreSQL 17: 락을 쥔 채 놀고 있는 트랜잭션
SELECT pid, state, now() - xact_start AS xact_age, now() - state_change AS idle_for, left(query, 60)
FROM pg_stat_activity WHERE state = 'idle in transaction' ORDER BY xact_start;
SELECT pid, pg_blocking_pids(pid), wait_event_type, wait_event FROM pg_stat_activity WHERE wait_event_type = 'Lock';

-- MySQL 8.4
SELECT * FROM sys.innodb_lock_waits\G
SELECT ENGINE_TRANSACTION_ID, INDEX_NAME, LOCK_MODE, LOCK_STATUS, LOCK_DATA FROM performance_schema.data_locks;
```

- 중복 데이터 사후 점검: `SELECT email, count(*) FROM member GROUP BY email HAVING count(*) > 1;` 결과가 있으면 제약부터 건다(기존 중복 정리 후).

## 장애 시나리오와 대처

### 1. check-then-insert → 중복 행

- **현상**: 같은 이메일 계정이 두 개, 같은 주문 번호가 두 건.
- **보이는 형태**: 에러가 없다. 나중에 조회에서 `NonUniqueResultException`(JPA `getSingleResult`)이나 `IncorrectResultSizeDataAccessException`이 터진다.
- **원인**: `SELECT`로 확인하고 `INSERT`했다. 두 요청이 동시에 "없다"를 봤다. 로컬 재현에서 UNIQUE가 없으면 2행이 생겼다.
- **대처**
  - UNIQUE 제약을 건다(기존 중복부터 정리).
  - 삽입은 `ON CONFLICT DO NOTHING`/`DO UPDATE`, 또는 23505·1062를 도메인 에러로 바꾼다.
  - MySQL에서 `FOR UPDATE`로 "없는 행"을 잠그려 하지 않는다 — 갭 락 교착(1213)이 된다.

### 2. 재고 음수 / 초과 발급

- **현상**: 재고 100개 상품이 107개 팔렸다. 쿠폰이 한도보다 많이 발급됐다.
- **보이는 형태**: 재고 컬럼이 음수. 에러는 없다.
- **원인**: 확인(`SELECT qty`)과 차감이 다른 문장이었다. 로컬 재현에서 재고 100 → −7(107 판매).
- **대처**
  - `UPDATE ... SET qty = qty - :n WHERE id = :id AND qty >= :n`, 영향 행 수 0이면 품절.
  - `CHECK (qty >= 0)`을 추가해 마지막 방어선으로 둔다.
  - 경합이 매우 크면 행 하나에 모든 쓰기가 줄 서므로, 재고를 여러 행(버킷)으로 나누거나 앞단에서 줄을 세우는 설계를 검토한다(api-design 03).

### 3. 트랜잭션 안 원격 호출 → 락 장기 보유

- **현상**: 결제사 응답이 느려진 순간 주문 API 전체가 느려지고, 커넥션 풀이 고갈된다.
- **보이는 형태**
  - `pg_stat_activity`에 `idle in transaction`이 늘고, 뒤에 `wait_event_type = Lock`이 줄선다.
  - MySQL은 `ERROR 1205 Lock wait timeout exceeded`(기본 50초), 앱에는 HikariCP `... - Connection is not available, request timed out after <N>ms`(HikariCP 소스 `HikariPool.java`).
- **원인**: 행 락은 커밋까지 간다. 원격 호출 시간만큼 락과 커넥션을 쥔다. 로컬 재현에서 4초 쉬는 동안 다른 UPDATE가 3.5초 기다렸다.
- **대처**
  - 원격 호출을 트랜잭션 밖으로 뺀다(위 3단계 흐름).
  - 원격 호출에 짧은 타임아웃을 둔다.
  - 서버 안전장치: `idle_in_transaction_session_timeout`, `lock_timeout`(PostgreSQL), `innodb_lock_wait_timeout`(MySQL). [22번](../22-database-side-timeouts/2-summary.md).

### 4. 유니크 위반 뒤 같은 트랜잭션을 계속 쓰려다 실패 (PostgreSQL)

- **현상**: "넣어 보고 중복이면 기존 행을 조회" 코드가 PostgreSQL에서만 실패한다.
- **보이는 형태**: 23505 다음 쿼리에서 `ERROR: current transaction is aborted, commands ignored until end of transaction block`(25P02).
- **원인**: PostgreSQL은 오류가 난 트랜잭션의 이후 명령을 모두 거부한다. MySQL InnoDB는 중복 키 오류면 그 문장만 롤백하고 계속 간다(교착 1213은 트랜잭션 전체를 롤백한다, 17.20.5).
- **대처**: `INSERT ... ON CONFLICT DO NOTHING RETURNING id` 후 0행이면 `SELECT`. 또는 세이브포인트로 감싼다.

## 핵심 문장

- 확인과 행동이 다른 문장이면 그 사이에 틈이 있다. 기본 격리 수준은 이 틈을 막지 않는다.
- 차감은 `WHERE qty >= :n`을 붙인 한 문장으로 하고, 영향 행 수로 성공을 판정한다. CHECK 제약이 마지막 방어선이다.
- 중복은 UNIQUE 제약이 막는다. 앱의 사전 조회는 메시지용이다.
- "없으면 넣기"는 upsert로 한다. MySQL에서 없는 행을 `FOR UPDATE`로 잠그면 갭 락끼리 호환이라 교착이 난다.
- 락은 커밋까지 간다. 트랜잭션 안의 원격 호출은 그 시간만큼 모두를 줄 세운다.

## 관련 주제·근거

- 선행
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md) — 행 락·갭 락·교착
  - [17-occ-and-timestamp-ordering](../17-occ-and-timestamp-ordering/2-summary.md) — 버전 컬럼과 경합 비용
- 연결
  - [16-mvcc](../16-mvcc/2-summary.md) — RR에서도 막히지 않는 lost update
  - [api-design/03-stock-deduct](../../api-design/03-stock-deduct/2-summary.md) — 재고 차감 설계(여러 상품 잠금 순서, 복원, 예약) · [api-design/02-coupon-issue](../../api-design/02-coupon-issue/2-summary.md)
  - [ops-patterns/failure-modes](../../ops-patterns/failure-modes/2-summary.md) — F-01 lost update, F-02 데드락, F-05 롱 트랜잭션
  - [languages/sql/syntax/52-upsert](../../../languages/sql/syntax/52-upsert/2-summary.md) · [languages/sql/syntax/57](../../../languages/sql/syntax/57-explicit-locking-and-deadlock/2-summary.md) — upsert·잠금 문법과 재현
  - database [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md)(write skew), [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md), [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md), [52-offline-concurrency-patterns](../52-offline-concurrency-patterns/2-summary.md)
  - reliability `04-failure-modes-catalog` — 미작성, [reliability/README](../../reliability/README.md)
- 교재
  - Martin Kleppmann, 『Designing Data-Intensive Applications』 1판 7장 — Preventing Lost Updates(원자적 쓰기 연산, 명시적 잠금, 자동 감지, compare-and-set), Write Skew and Phantoms(충돌 구체화)
- PostgreSQL 17
  - 13.2.1 Read Committed(동시 갱신 뒤 WHERE 재평가) <https://www.postgresql.org/docs/17/transaction-iso.html>
  - 13.3 Explicit Locking <https://www.postgresql.org/docs/17/explicit-locking.html> · 13.4 Data Consistency Checks at the Application Level
  - INSERT — `ON CONFLICT DO UPDATE`의 원자성 보장 <https://www.postgresql.org/docs/17/sql-insert.html> · SELECT — `FOR UPDATE ... NOWAIT | SKIP LOCKED`
  - 부록 A — 23505 `unique_violation`, 23514 `check_violation`, 25P02 `in_failed_sql_transaction`, 25P03 `idle_in_transaction_session_timeout`, 55P03, 40001
- MySQL 8.4
  - 15.2.7.2 INSERT ... ON DUPLICATE KEY UPDATE — 영향 행 1/2/0, `VALUES()` deprecated, 유니크 인덱스 여럿이면 피하라 <https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html>
  - 17.7.2.4 Locking Reads(`NOWAIT`·`SKIP LOCKED`), 17.7.1 InnoDB Locking(갭 락 호환), 17.7.3 Locks Set by Different SQL Statements(중복 키 오류 시 공유 락과 교착) <https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html>
- Spring Framework 6.2.12 소스 — `spring-jdbc/.../support/SQLStateSQLExceptionTranslator.java`(23505, 23000+1062 → `DuplicateKeyException`, Spring 6 기본 번역 경로), `spring-orm/.../vendor/HibernateJpaDialect.java`(`ConstraintViolationException` → `DataIntegrityViolationException`). 구형 `sql-error-codes.xml`의 `duplicateKeyCodes`는 사용자 파일을 둘 때만 쓰인다.
- MySQL 8.4 17.20.5 InnoDB Error Handling — 중복 키는 문장 롤백, 교착은 트랜잭션 롤백 <https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html>
- PostgreSQL 17 13.5 Serialization Failure Handling — 40001, 경우에 따라 23505·23P01도 재시도 <https://www.postgresql.org/docs/17/mvcc-serialization-failure-handling.html>
- HikariCP `src/main/java/com/zaxxer/hikari/pool/HikariPool.java` — 풀 대기 타임아웃 메시지
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): UNIQUE 유무에 따른 check-then-insert(2행 vs 23505), 8세션 upsert 1600 정확, MySQL upsert 영향 행 1·2·0, MySQL CHECK 위반 3819, 재고 100에서 확인-후-차감 −7 vs 조건부 UPDATE 0, MySQL 없는 행 `FOR UPDATE` 갭 락 → 1213, PG 배제 제약(`EXCLUDE USING gist`)으로 겹치는 예약 거부, 트랜잭션 안 4초 대기 동안 다른 UPDATE 3.5초 대기와 `idle in transaction`, `idle_in_transaction_session_timeout` 1초 → FATAL
