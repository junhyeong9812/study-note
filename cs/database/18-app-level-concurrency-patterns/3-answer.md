# database/18-app-level-concurrency-patterns — 정답

## 정답

### 1. check-then-act의 틈

```text
  A: SELECT (없다) ─────────── INSERT
  B:        SELECT (없다) ─────────── INSERT
             ↑ 두 확인이 모두 상대의 행동보다 먼저 끝났다
```

- PostgreSQL 17 기본 READ COMMITTED, MySQL 8.4 기본 REPEATABLE READ 모두 이 모양을 막지 않는다. 확인은 락을 걸지 않는 일관된 읽기다.
- 도구 네 가지
  1. 한 문장으로 합치기: 조건부 UPDATE, upsert
  2. 제약: UNIQUE, CHECK
  3. 확인하며 잠그기: `SELECT ... FOR UPDATE`
  4. 버전 검증: 버전 컬럼(17번)

### 2. 원자적 차감인데 음수

- 원자적인 것은 `qty = qty - 1` **차감**뿐이다. `qty > 0` **확인**은 앞 문장에서 끝났다.
- qty = 1일 때 여러 세션이 동시에 1을 보고 모두 차감한다 → 음수.
- 로컬 재현(예시, PostgreSQL 17.11): 재고 100 → −7, 107개 판매.
- 고친 SQL

```sql
UPDATE inv SET qty = qty - 1 WHERE id = 1 AND qty > 0;   -- 영향 행 1 = 성공, 0 = 품절
```

- 같은 재현에서 최종 재고 0, 판매 100.
- 추가 방어: `CHECK (qty >= 0)`. 위반 시 PostgreSQL 23514, MySQL 8.4 `ERROR 3819`.

### 3. 조건부 UPDATE가 정확한 이유 (PostgreSQL 17 RC)

1. B가 명령 시작 시점의 커밋된 행(qty = 1)을 찾는다.
2. A가 그 행을 고치는 중이면 B는 A의 커밋·롤백을 기다린다.
3. A가 커밋하면 B는 **갱신된 버전**(qty = 0)에 WHERE를 다시 평가한다(13.2.1). `qty > 0`이 거짓 → 0행.
4. A가 롤백하면 A의 변경은 없던 일이 되고, B는 원래 찾은 행(qty = 1)을 고친다 → 1행.

- 즉 조건 검사가 **행 락을 쥔 뒤 최신 값**으로 이루어진다.

### 4. UNIQUE와 동시 INSERT

- 두 번째 INSERT는 인덱스에서 같은 키를 찾는다. 첫 트랜잭션이 아직 진행 중이면 그 결과를 **기다린다**.
  - 첫 쪽이 커밋 → 중복 오류. 첫 쪽이 롤백 → 두 번째가 성공.
- 오류 형태
  - PostgreSQL: `ERROR: duplicate key value violates unique constraint "..."`, SQLSTATE 23505 (로컬 재현)
  - MySQL: `ERROR 1062 (23000): Duplicate entry '...' for key '...'`
  - Spring: JDBC(`JdbcTemplate`)는 `DuplicateKeyException`(`DataIntegrityViolationException` 하위), JPA/Hibernate 경로는 보통 상위 `DataIntegrityViolationException`
- 사전 `SELECT`는 대부분의 경우에 친절한 메시지를 빨리 주려는 것이다. 정합성은 제약이 지킨다. 제약이 없으면 로컬 재현처럼 같은 이메일이 2행 생긴다.

### 5. MySQL 없는 행의 `FOR UPDATE` → 1213

```text
  기존 키 'a@x.com', 'm@x.com'  (UNIQUE uk_email)
  A: FOR UPDATE 'c@x.com' → 0행, X,GAP ('m@x.com' 앞 갭)
  B: FOR UPDATE 'c@x.com' → 0행, X,GAP (같은 갭, 호환)
  A: INSERT → B의 갭 락과 충돌 → 대기
  B: INSERT → A의 갭 락과 충돌 → 대기 → 사이클 → 한쪽 ERROR 1213
```

- 로컬 재현(예시, MySQL 8.4.10): `data_locks`에 두 트랜잭션의 `X,GAP GRANTED 'm@x.com', 2`가 함께 보였고, 한쪽이 1213, 다른 쪽이 INSERT에 성공했다.
- 갭 락은 "삽입 금지"만 뜻하고 갭 락끼리는 충돌하지 않는다(17.7.1). 그래서 둘 다 확인을 통과한다.
- 해법: UNIQUE + `INSERT ... ON DUPLICATE KEY UPDATE`(MySQL)·`ON CONFLICT DO NOTHING`(PostgreSQL), 또는 1062를 잡아 처리.

### 6. upsert의 보장과 영향 행 수

- PostgreSQL 17: `ON CONFLICT DO UPDATE`는 독립적인 오류가 없는 한, 높은 동시성에서도 INSERT 또는 UPDATE 중 하나의 결과를 보장한다(INSERT 문서). 로컬 재현(예시, PostgreSQL 17.11)에서 8세션 × 200번 → 정확히 1600.
- MySQL 8.4 영향 행 수(15.2.7.2)
  - 1: 새 행 삽입
  - 2: 기존 행 갱신
  - 0: 기존 행을 같은 값으로 "갱신"(`CLIENT_FOUND_ROWS` 플래그면 1)
  - 로컬 재현(예시, MySQL 8.4.10)에서 1 → 2 → 0.
- 유니크 인덱스가 **여러 개**인 테이블에서는 피하라고 문서가 적는다. 어느 유니크 키가 충돌했느냐에 따라 갱신되는 행이 달라진다.
- MySQL 8.4에서 `VALUES(col)` 참조는 deprecated이고, 행 별칭(`AS new ... new.col`)을 쓴다.

### 7. 트랜잭션 안 원격 호출

- 보이는 것
  - 결제 호출 중인 세션: `state = 'idle in transaction'`, `wait_event = ClientRead`
  - 같은 행을 원하는 세션들: `wait_event_type = Lock`, `wait_event = transactionid`, `pg_blocking_pids`가 위 세션
  - 로컬 재현(예시, PostgreSQL 17.11): A가 4초 쉬는 동안 B의 UPDATE가 3518 ms 기다렸다.
- 원인: 행 락은 커밋까지 간다. 원격 호출 시간 = 락 보유 시간 = 커넥션 점유 시간. 뒤 요청들이 줄을 서고 풀이 마른다.
- 구조적 대처
  1. 짧은 트랜잭션으로 주문 PENDING + 재고 예약 → 커밋
  2. 트랜잭션 밖에서 결제 호출(타임아웃, 멱등 키)
  3. 짧은 트랜잭션으로 확정 또는 보상
- 안전장치: `idle_in_transaction_session_timeout`(PostgreSQL 17 기본 0). 1초로 두면 `FATAL: terminating connection due to idle-in-transaction timeout`(25P03)으로 끊고 롤백한다(로컬 재현).

### 8. 23505 뒤 같은 트랜잭션에서 SELECT

- 오류: `ERROR: current transaction is aborted, commands ignored until end of transaction block`(25P02).
- 이유: PostgreSQL은 한 문장이 실패하면 트랜잭션 전체가 실패 상태가 된다. 롤백 전까지 모든 명령을 거부한다. MySQL InnoDB는 중복 키 오류면 실패한 문장만 롤백하고 트랜잭션을 계속한다(교착이면 트랜잭션 전체 롤백).
- 고치는 법
  - `INSERT ... ON CONFLICT (email) DO NOTHING RETURNING id` → 0행이면 `SELECT id ... WHERE email = ?`
  - 또는 INSERT를 세이브포인트로 감싸 실패 시 세이브포인트로 롤백한다.

### 9. 패턴 고르기

| 작업 | 패턴 | 이유 |
|---|---|---|
| (a) 일별 조회수 누적 | upsert `DO UPDATE SET cnt = cnt + 1` | 행이 없을 때와 있을 때를 한 문장으로, 동시에도 정확 |
| (b) 쿠폰 1인 1매 | UNIQUE(user_id, coupon_id) + `DO NOTHING`/1062 처리 | "없으면 넣기"는 제약이 막는다 |
| (c) 규칙 여러 개인 출금 | `SELECT ... FOR UPDATE` 후 검사·갱신, 짧게 | 한 문장으로 표현하기 어려운 로직 |
| (d) 작업 큐 | `FOR UPDATE SKIP LOCKED` | 잠긴 작업을 건너뛰어 워커끼리 기다리지 않음 |

- (b)의 총 발급 한도(선착순 N매)는 별도로 조건부 UPDATE(`issued < limit`)가 필요하다(api-design 02).

### 10. 잠글 행이 없을 때

- 예: "회의실 R, 10:00~11:00에 겹치는 예약이 없으면 넣기." 확인할 때 잠글 행이 없다. 이것은 write skew·팬텀 문제다(DDIA 7장).
- 해법
  - **충돌 구체화(materializing conflicts)**: 회의실 × 시간 칸(예: 15분 단위) 행을 미리 만들어 두고, 예약 시 해당 칸들을 `FOR UPDATE`로 잠근다. 잠글 대상을 인위적으로 만든다. DDIA는 이것을 최후 수단으로 본다.
  - SERIALIZABLE 격리 수준(PostgreSQL SSI는 40001로 실패시킨다. 경우에 따라 23505·23P01로 나오기도 한다 → 트랜잭션 전체 재시도, 13.5).
  - PostgreSQL이라면 배제 제약(`EXCLUDE USING gist (room WITH =, during WITH &&)`, 정수 `=`에는 `btree_gist` 확장 필요)으로 겹침 자체를 DB가 거부하게 할 수 있다. 로컬 재현(예시, PostgreSQL 17.11)에서 겹치는 두 번째 예약이 `ERROR: conflicting key value violates exclusion constraint`를 받았다.
