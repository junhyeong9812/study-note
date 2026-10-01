# database/02-keys-and-constraints — 키와 제약: 앱 검증이 못 막는 것을 DB가 막는다 — 정리 (힌트)

## 해결하는 문제

"이메일 중복이면 가입 거절"을 앱 코드로만 짜면 이렇게 된다.

```text
  요청 A                                   요청 B
  SELECT … WHERE email='a@x.com'  → 없음
                                           SELECT … WHERE email='a@x.com'  → 없음
  INSERT (a@x.com)                         INSERT (a@x.com)
  → 두 행 모두 들어간다. 검사와 삽입 사이에 틈이 있다.
```

- 로컬 재현(예시, PostgreSQL 17.11): 두 세션이 "없으면 1초 뒤 INSERT"를 동시에 돌리자 제약 없는 테이블에는 `count = 2`가 됐다.
- 같은 실험을 `email UNIQUE` 테이블에 하자 한쪽이 `23505 duplicate key value violates unique constraint`로 실패하고 `count = 1`이었다.

쉬운 예: 공연장 좌석표를 두 매표원이 각자 "비었네" 확인하고 같은 좌석을 판다. 좌석 번호마다 칸이 하나뿐인 **실물 좌석판**이 있으면 두 번째 매표원은 칸이 이미 찼다는 것을 알게 된다.

똑같은 구조다.\
DB 제약은 "확인"과 "쓰기"를 **한 자리(인덱스 삽입·검사)**에서 한다. 그래서 동시 요청 사이에 틈이 없다.

실무 예:
- 동시 가입 두 건으로 같은 이메일 계정이 둘 생긴다. 로그인 시 어느 계정인지 모호해진다.
- 주문을 넣는 사이 상품이 삭제되어, 존재하지 않는 상품을 가리키는 주문 행(고아 행)이 남는다.
- 수량에 음수가 들어가 재고 합계가 틀어진다.

## 동작·원리

### 1. 키의 종류 — 튜플을 구별하는 속성 집합

```text
  member(id, email, phone, name)

  슈퍼키          {id}, {email}, {id, name}, {email, phone}, …   <- 유일하게 식별만 하면 됨
  후보 키         {id}, {email}                                  <- 더 뺄 속성이 없는 최소 슈퍼키
  기본 키 (PK)    {id}                                           <- 후보 키 중 하나를 대표로 고름
  대체 키         {email}                                        <- 나머지 후보 키 → UNIQUE NOT NULL로 선언
  외래 키 (FK)    orders.member_id → member.id                   <- 다른 릴레이션의 키를 가리킴
```

- *슈퍼키(superkey)*: 값이 같은 두 튜플이 있을 수 없는 속성 집합.
- *후보 키(candidate key)*: 속성 하나라도 빼면 슈퍼키가 아니게 되는 최소 슈퍼키.
- *기본 키(primary key)*: 대표로 고른 후보 키. 테이블당 하나다(PostgreSQL 17 5.5.4).
- *외래 키(foreign key)*: 이 행이 다른 테이블의 어느 행에 대응하는지 가리키는 속성. 보통 상대의 PK를 가리킨다(CMU L1 §4).
- 대리키(surrogate)냐 자연키(natural)냐, bigint냐 UUID냐는 [28-key-strategy-surrogate-natural-public-id](../28-key-strategy-surrogate-natural-public-id/2-summary.md)에서 다룬다.

### 2. 제약 다섯 가지 — 무엇을 막고, NULL은 어떻게 보나

| 제약 | 막는 것 | NULL에 대해 | 인덱스 |
|---|---|---|---|
| `NOT NULL` | 값 없음 | 막는다 | 없음 |
| `CHECK (식)` | 식이 **거짓**인 행 | 식이 NULL(알 수 없음)이면 **통과** | 없음 |
| `UNIQUE` | 같은 값 두 번 | 기본은 NULL끼리 다르다고 봄 → **NULL 여러 개 허용** | 유일 B-tree 자동 생성 |
| `PRIMARY KEY` | 중복 + NULL | `UNIQUE` + `NOT NULL` | 유일 B-tree 자동 생성 |
| `FOREIGN KEY` | 없는 부모를 가리킴 | PostgreSQL 17 기본(`MATCH SIMPLE`)은 참조 열 하나라도 NULL이면 **검사 안 함**(5.5.5). 로컬 재현에서 `parent_id` NULL 행이 들어갔다 | 부모 쪽은 PK·UNIQUE 제약 또는 부분 아닌 유일 인덱스 필요(PostgreSQL 17 5.5.5. 지연 가능(DEFERRABLE) UNIQUE는 안 된다 — CREATE TABLE `REFERENCES`. MySQL 8.4는 비유일·부분 키 참조를 폐기 예정 확장으로 두고, 기본 `restrict_fk_on_non_standard_key = ON`이 이를 막는다(7.1.8)). 자식 쪽은 제품마다 다름(아래) |

- CHECK와 NULL: PostgreSQL 17 5.5.1 "check 식이 참 **또는 NULL**이면 만족". MySQL 8.4 15.1.20.6 "TRUE 또는 UNKNOWN(NULL)이어야 한다". 로컬 재현에서 `qty int CHECK (qty > 0)`에 `NULL`이 들어갔다.
- UNIQUE와 NULL: PostgreSQL 17 5.5.3 "기본적으로 두 NULL은 같다고 보지 않는다". MySQL 8.4 15.1.15 "UNIQUE 인덱스는 NULL을 여러 개 허용한다". 로컬 재현에서 두 제품 모두 `(NULL),(NULL)`이 들어갔다.
  - PostgreSQL 15부터 `UNIQUE NULLS NOT DISTINCT`로 NULL도 하나만 허용할 수 있다(PostgreSQL 15 릴리스 노트). 로컬 재현에서 두 번째 NULL이 `23505 … Key (code)=(null) already exists`로 실패했다.
- CHECK는 **그 행만** 볼 수 있다. PostgreSQL 17 5.5.1: 다른 행·다른 테이블을 참조하는 CHECK는 지원하지 않는다. 간단한 테스트에서는 되는 것처럼 보여도 보장하지 못한다.
- MySQL은 8.0.16부터 CHECK를 기본적으로 강제한다(`NOT ENFORCED`로 선언한 제약은 강제하지 않는다, MySQL 8.4 15.1.20.6). 그 전에는 문법만 받고 무시했다(MySQL 8.0 15.1.20.6).

### 3. 유일성 검사 = 유일 인덱스에 넣으면서 검사

```text
  INSERT (email='a@x.com')
        │
        ▼
  유일 B-tree 인덱스에서 'a@x.com' 자리를 찾는다 ──┬── 없음 → 넣는다
                                                 ├── 커밋된 행이 있음 → 23505 / 1062
                                                 └── 아직 커밋 안 된 행이 있음 → 그 트랜잭션이 끝날 때까지 기다린다
                                                        ├── 상대 커밋 → 23505
                                                        └── 상대 롤백 → 넣는다
```

- PostgreSQL 17 62.5 Index Uniqueness Checks: 커밋되지 않은 충돌 행이 있으면 삽입자는 그 트랜잭션이 커밋하는지 기다린다. 롤백하면 충돌이 아니다.
- 로컬 재현(예시, PostgreSQL 17.11) 시간축

```text
  t=0.0  세션 A: BEGIN; INSERT 'b@x.com'  (커밋 안 함, 2초 대기)
  t=0.7  세션 B: INSERT 'b@x.com'
         pg_stat_activity: wait_event_type=Lock, wait_event=transactionid   <- A의 끝을 기다림
  t=2.0  세션 A: COMMIT
         세션 B: ERROR 23505 duplicate key … (B는 약 1.4초 걸림)
```

- 에러 위치는 `_bt_check_unique, nbtinsert.c`였다. B-tree 삽입 코드가 유일성을 본다.

### 4. 외래 키 검사 = 부모 인덱스 조회 + 공유 락

```text
  자식 INSERT (parent_id = 2)
        │  PostgreSQL RI 트리거가 내부적으로 실행:
        ▼  SELECT 1 FROM parent x WHERE id = $1 FOR KEY SHARE OF x      (ri_triggers.c)
  부모 PK 인덱스 조회 ── 없음 → 23503 "is not present in table"
                    └─ 있음 → 부모 행에 KEY SHARE 락 → 자식 트랜잭션이 끝날 때까지 부모 삭제가 기다린다

  부모 DELETE (id = 2)
        │  NO ACTION/RESTRICT: 자식 테이블에서 parent_id = 2 인 행을 찾는다
        ▼
  자식 쪽 인덱스가 있으면 인덱스 조회, 없으면 **자식 테이블 전체 스캔**
```

- 로컬 재현(예시, PostgreSQL 17.11): A가 자식을 넣고 커밋 전 2초 대기, B가 그 부모를 `DELETE`. B는 약 1.5초 기다렸다가 A 커밋 뒤 `23503 … is still referenced from table "c_fk"`로 실패했다. 같은 시나리오를 FK 없는 테이블로 하자 부모는 지워지고 자식은 **고아 행**으로 남았다.
- 자식 쪽 인덱스
  - PostgreSQL 17 5.5.5: FK 선언은 참조하는 열에 인덱스를 **자동으로 만들지 않는다**. 부모 삭제·키 변경 때 자식 스캔이 필요하므로 보통 만들어 두는 게 좋다. 로컬 재현에서 `child`의 인덱스는 `child_pkey`뿐이었다.
  - MySQL 8.4 15.1.20.5: 참조하는 테이블에 FK 열이 앞에 오는 인덱스가 **필요**하고, 없으면 **자동으로 만든다**. 로컬 재현에서 `SHOW INDEX`에 `parent_id` 인덱스가 생겼다.

### 5. 참조 동작 — 부모가 지워지거나 키가 바뀌면

| 동작 | 뜻 | 비고 |
|---|---|---|
| `NO ACTION` (기본) | 검사 시점에 참조 행이 남아 있으면 오류 | PostgreSQL: 트랜잭션 끝으로 **미룰 수 있다**(DEFERRABLE) |
| `RESTRICT` | 참조 행이 있으면 즉시 오류 | 미룰 수 없다 |
| `CASCADE` | 자식도 같이 지우거나 바꾼다 | 대량 연쇄 삭제 주의 |
| `SET NULL` / `SET DEFAULT` | 자식 열을 NULL / 기본값으로 | MySQL 8.4: 파서는 `SET DEFAULT`를 알지만 InnoDB·NDB는 그런 테이블 정의를 거부한다 |

- PostgreSQL 17 5.5.5: `NO ACTION`과 `RESTRICT`의 본질적 차이는 검사를 미룰 수 있느냐다.
- MySQL 8.4 15.1.20.5: InnoDB에서 `NO ACTION`은 `RESTRICT`와 같다. 즉시 거부한다. 미뤄진 검사는 NDB만 지원한다.

## 쓰이는 자료구조·알고리즘

- **유일 B+Tree 인덱스**: PK·UNIQUE는 유일 B-tree를 자동으로 만든다(PostgreSQL 17 5.5.3·5.5.4). 삽입할 자리를 찾는 탐색이 곧 중복 검사다. "제약 검사 = 인덱스 조회"(커리큘럼 🔧). [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **FK 검사 = 두 방향 인덱스 조회**: 자식 쓰기는 부모 PK 인덱스를, 부모 삭제는 자식 FK 열 인덱스(있으면)를 조회한다. 없으면 선형 스캔이다.
- **락**: FK 검사는 부모 행에 `FOR KEY SHARE`(PostgreSQL)를 건다. 유일성 충돌은 상대 트랜잭션 ID를 기다린다. 락 모드와 대기는 [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 규칙은 DDL로 선언한다

```sql
CREATE TABLE member (
  id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- PG. MySQL은 BIGINT AUTO_INCREMENT
  email  text   NOT NULL UNIQUE,                             -- NOT NULL을 같이 걸어 NULL 다중 허용을 막는다
  status text   NOT NULL CHECK (status IN ('ACTIVE','LOCKED'))
);
CREATE TABLE orders (
  id        bigint PRIMARY KEY,
  member_id bigint NOT NULL REFERENCES member(id),           -- 부모 없는 주문 금지
  qty       int    NOT NULL CHECK (qty > 0)                  -- NOT NULL이 없으면 NULL이 CHECK를 통과
);
CREATE INDEX ON orders(member_id);                           -- PG: FK 쪽 인덱스는 직접 만든다
```

### 2. 앱은 "먼저 확인"보다 "넣고 위반을 받는다"

```java
// Spring JDBC: 유일 위반을 예외로 받아 비즈니스 오류로 바꾼다
try {
    jdbc.update("INSERT INTO member(email, status) VALUES (?, 'ACTIVE')", email);
} catch (DuplicateKeyException e) {          // PG 23505, MySQL 1062 (sql-error-codes.xml duplicateKeyCodes)
    throw new EmailAlreadyUsed(email);
}
```

- 사전 조회(`SELECT … WHERE email = ?`)는 **사용자 안내용**으로만 쓴다. 최종 판정은 제약이 한다.
- 조용히 건너뛰려면 PostgreSQL은 `INSERT … ON CONFLICT (email) DO NOTHING`을 쓴다. MySQL `INSERT … ON DUPLICATE KEY UPDATE`는 건너뛰기가 아니라 중복 시 기존 행에 지정한 `UPDATE`를 실행한다(MySQL 8.4 15.2.7.2)([18-app-level-concurrency-patterns](../18-app-level-concurrency-patterns/2-summary.md)). MySQL `INSERT IGNORE`는 중복 키만이 아니라 "무시 가능한" 오류 전반을 경고로 바꾼다(MySQL 8.4 15.2.7 INSERT). 조용히 버려지는 행이 생기므로 조심한다.
- 에러 → 예외 매핑(Spring `sql-error-codes.xml`)
  - PostgreSQL(SQLSTATE 기준): `23505` → `DuplicateKeyException`, `23502`·`23503`·`23514` → `DataIntegrityViolationException`.
  - MySQL(에러 번호 기준): `1062` → `DuplicateKeyException`, `1451`·`1452` 등 → `DataIntegrityViolationException`. CHECK 위반 `3819`(SQLSTATE `HY000`, 로컬 재현)는 목록에 없어 폴백 번역기(`SQLExceptionSubclassTranslator` → SQLSTATE 기반)로 넘어간다(`SQLErrorCodeSQLExceptionTranslator.java`). 최종 예외 타입은 드라이버가 던진 `SQLException` 하위 타입과 SQLSTATE에 달렸다.

### 3. 운영 중인 큰 테이블에 제약 추가 (PostgreSQL)

```sql
-- 1) 새로 들어오는 행만 검사, 기존 행 스캔 없음 → 바로 커밋
ALTER TABLE orders ADD CONSTRAINT orders_qty_pos CHECK (qty > 0) NOT VALID;
-- 2) 기존 행 검증은 따로 (쓰기를 막는 강한 락이 필요 없다)
ALTER TABLE orders VALIDATE CONSTRAINT orders_qty_pos;
```

- PostgreSQL 17 ALTER TABLE: 제약 추가는 보통 기존 행 전체를 스캔해 검증한다. `NOT VALID`는 이 스캔을 건너뛰고, `VALIDATE CONSTRAINT`가 나중에 검증한다.
- 락: `NOT VALID` 추가 자체도 짧게 락을 잡는다(CHECK 추가는 `ACCESS EXCLUSIVE`, FK 추가는 양쪽 테이블에 `SHARE ROW EXCLUSIVE`). 검증 단계는 `SHARE UPDATE EXCLUSIVE`만 잡아 일반 읽기·쓰기를 막지 않는다(FK면 참조 테이블에 `ROW SHARE`도).
- 기존 위반 행은 먼저 찾아 고친다.

```sql
-- 고아 행 찾기 (안티 조인)
SELECT o.* FROM orders o LEFT JOIN member m ON m.id = o.member_id WHERE m.id IS NULL;
-- 중복 찾기
SELECT email, count(*) FROM member GROUP BY email HAVING count(*) > 1;
```

### 4. 진단

```sql
-- PostgreSQL: 테이블의 제약과 인덱스
SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'orders'::regclass;
SELECT indexrelid::regclass FROM pg_index WHERE indrelid = 'orders'::regclass;
-- 무엇을 기다리나 (FK·유일성 대기)
SELECT pid, wait_event_type, wait_event, pg_blocking_pids(pid), query FROM pg_stat_activity WHERE wait_event_type = 'Lock';
-- MySQL
SHOW CREATE TABLE orders;
SHOW INDEX FROM orders;
SELECT * FROM performance_schema.data_lock_waits;
```

- 문법 세부는 [sql/43 PK·UNIQUE와 NULL](../../../languages/sql/syntax/43-primary-key-unique-and-null/2-summary.md), [sql/44 FK와 참조 동작](../../../languages/sql/syntax/44-foreign-key-referential-actions/2-summary.md), [sql/45 CHECK·NOT NULL·DEFAULT](../../../languages/sql/syntax/45-check-not-null-default-generated-columns/2-summary.md).

## 장애 시나리오와 대처

### 1. 앱 검증만 믿다가 동시 요청에 중복 행 (⚠ 커리큘럼)

- **현상**: 같은 이메일 계정이 둘, 같은 주문 번호가 둘 생긴다. 평소에는 안 나고 더블 클릭·재시도·트래픽 몰림에서 난다.
- **보이는 형태**: 에러 없음. 나중에 `NonUniqueResultException`(JPA 단건 조회가 두 행을 받음) 같은 엉뚱한 곳에서 터진다.
- **원인**: "조회 → 없으면 삽입" 사이의 틈. 두 요청이 둘 다 "없음"을 본다. 기본 격리 수준(PostgreSQL 17 기본 READ COMMITTED, MySQL 8.4 InnoDB 기본 REPEATABLE READ — 로컬 재현 컨테이너에서 확인)에서 로컬 재현이 두 행을 만들었다. 격리 수준별 차이는 [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md).
- **대처**
  - `UNIQUE` 제약을 건다. 기존 중복은 먼저 정리한다.
  - 앱은 위반을 예외(`DuplicateKeyException`)로 받아 "이미 사용 중"으로 응답한다.
  - 멱등 요청이면 `ON CONFLICT DO NOTHING` 후 기존 행을 돌려준다.

### 2. FK 없이 운영하다 고아 행 (⚠ 커리큘럼)

- **현상**: 주문 목록 화면에서 상품명이 비거나, 내부 조인 집계에서 주문 건수가 빠진다.
- **보이는 형태**: 에러 없음. `LEFT JOIN … WHERE parent.id IS NULL`로 찾으면 고아 행이 나온다. 로컬 재현(예시): 앱이 부모 존재를 확인한 직후 다른 세션이 부모를 지워 `c_nofk(1, 1)`이 부모 없이 남았다.
- **원인**: 앱의 "부모 존재 확인"과 "자식 삽입" 사이에 부모가 지워졌다. 또는 배치·수작업 삭제가 자식을 모른다.
- **대처**
  - FK를 건다. 기존 고아는 정리하거나 `NOT VALID`로 걸고 정리 후 `VALIDATE`한다(PostgreSQL).
  - FK를 쓸 수 없는 구조(샤딩·다른 DB)면 주기적 고아 검사 쿼리와 경보를 둔다.

### 3. UNIQUE 컬럼에 NULL이 여러 개 (⚠ 커리큘럼)

- **현상**: "사업자번호는 유일"이라 했는데 미입력(NULL) 회원이 여럿이다. 또는 `UNIQUE(tenant_id, deleted_at)`로 "활성 행 하나"를 지키려 했는데 `deleted_at IS NULL`인 행이 여러 개 들어간다.
- **보이는 형태**: 에러 없음. 로컬 재현(예시): PostgreSQL 17.11·MySQL 8.4.10 모두 `UNIQUE` 열에 `(NULL),(NULL)`이 들어갔다(`count = 2`).
- **원인**: SQL에서 NULL은 "알 수 없음"이라 NULL끼리 같다고 보지 않는다. 두 제품의 기본 동작이다.
- **대처**
  - 값이 반드시 있어야 하면 `NOT NULL`을 같이 건다.
  - PostgreSQL 15+: `UNIQUE NULLS NOT DISTINCT`로 NULL도 하나만.
  - "활성 행 하나"는 부분 유니크 인덱스로 표현한다: `CREATE UNIQUE INDEX … ON t(tenant_id) WHERE deleted_at IS NULL`(PostgreSQL). MySQL은 부분 인덱스가 없어 생성 열 등 다른 방법을 쓴다([29-soft-delete-and-data-lifecycle](../29-soft-delete-and-data-lifecycle/2-summary.md)).

### 4. 부모 한 줄 삭제가 느리고 다른 쓰기가 막힌다 (PostgreSQL)

- **현상**: `DELETE FROM member WHERE id = ?` 한 건이 수 초 걸린다. 그동안 관련 쓰기가 줄을 선다.
- **보이는 형태**: `EXPLAIN ANALYZE`의 `Trigger for constraint …_fkey: time=…` 줄이 크다. 로컬 재현(예시, PostgreSQL 17.11, 자식 20만 행): 자식 FK 열 인덱스 없이 부모 한 행 삭제 시 `time=8.870`(ms), 인덱스를 만든 뒤 `time=0.411`. 자식이 커질수록 차이는 행 수에 비례해 벌어진다.
- **원인**: 부모 삭제 때 자식 테이블에서 참조 행을 찾는데, 자식 FK 열에 인덱스가 없어 매번 전체 스캔한다. PostgreSQL은 이 인덱스를 자동으로 만들지 않는다(5.5.5).
- **대처**: 자식 FK 열에 인덱스를 만든다(운영 중이면 `CREATE INDEX CONCURRENTLY`). MySQL InnoDB는 필요 인덱스를 자동으로 만든다.

### 5. CHECK가 있는데 이상한 값이 들어갔다

- **현상**: `CHECK (qty > 0)`인데 수량 없는 행이 있고, 합계 계산에서 빠진다.
- **보이는 형태**: 에러 없음. `SELECT count(*) FROM orders WHERE qty IS NULL`이 0이 아니다.
- **원인**: CHECK는 식이 **거짓일 때만** 거부한다. NULL이면 결과가 UNKNOWN이라 통과한다(PostgreSQL 5.5.1, MySQL 15.1.20.6). MySQL 8.0.16 이전 서버에서 만든 스키마라면 CHECK 자체가 강제되지 않았을 수 있다.
- **대처**: `NOT NULL`을 같이 건다. 다른 행을 보는 규칙(예: "기간이 겹치면 안 됨")은 CHECK로 못 한다. PostgreSQL은 배제 제약(5.5.6)을, 그 밖에는 트리거나 앱 락을 쓴다.

## 핵심 문장

- 앱의 "먼저 조회하고 없으면 넣기"에는 틈이 있다. DB 제약은 검사와 쓰기를 한 지점에서 해서 그 틈을 없앤다.
- PK·UNIQUE는 유일 B-tree 인덱스로 강제된다. 삽입 위치를 찾는 탐색이 곧 중복 검사이고, 커밋 안 된 충돌 행이 있으면 그 트랜잭션의 끝을 기다린다.
- FK는 자식 쓰기 때 부모 인덱스를 조회하고, 부모 삭제 때 자식을 찾는다. PostgreSQL은 자식 쪽 인덱스를 자동으로 만들지 않고, MySQL InnoDB는 만든다.
- CHECK는 NULL을 통과시키고, UNIQUE는 기본적으로 NULL 여러 개를 허용한다. "반드시 있어야 함"은 `NOT NULL`로 따로 말해야 한다.
- 앱은 제약 위반을 예외로 받아 비즈니스 오류로 바꾼다. 사전 조회는 안내용일 뿐이다.

## 관련 주제·근거

- 선행: [01-relational-model-and-algebra](../01-relational-model-and-algebra/2-summary.md)
- 후속
  - [03-normalization](../03-normalization/2-summary.md) — 키와 함수 종속으로 스키마를 나누기
  - [09-index-design](../09-index-design/2-summary.md) · [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md) · [18-app-level-concurrency-patterns](../18-app-level-concurrency-patterns/2-summary.md) · [28-key-strategy-surrogate-natural-public-id](../28-key-strategy-surrogate-natural-public-id/2-summary.md) · [29-soft-delete-and-data-lifecycle](../29-soft-delete-and-data-lifecycle/2-summary.md)
- 문법 세부(languages/sql): [sql/43](../../../languages/sql/syntax/43-primary-key-unique-and-null/2-summary.md) · [sql/44](../../../languages/sql/syntax/44-foreign-key-referential-actions/2-summary.md) · [sql/45](../../../languages/sql/syntax/45-check-not-null-default-generated-columns/2-summary.md)
- 교재: CMU 15-445 Fall 2024 Lecture #01 §4(PK·FK·제약) <https://15445.courses.cs.cmu.edu/fall2024/notes/01-relationalmodel.pdf> · Silberschatz 외 『Database System Concepts』 7판 7장 슬라이드(슈퍼키·후보 키)
- PostgreSQL 17
  - 5.5 Constraints — 5.5.1 CHECK(NULL이면 만족, 다른 행 참조 불가), 5.5.3 UNIQUE(NULL 기본 구별, `NULLS NOT DISTINCT`), 5.5.4 PK, 5.5.5 FK(`MATCH FULL`, NO ACTION vs RESTRICT, 참조 열 인덱스 자동 생성 안 함), 5.5.6 Exclusion <https://www.postgresql.org/docs/17/ddl-constraints.html>
  - 62.5 Index Uniqueness Checks(커밋 안 된 충돌 행을 기다림) <https://www.postgresql.org/docs/17/index-unique-checks.html>
  - ALTER TABLE — `NOT VALID`·`VALIDATE CONSTRAINT`, 추가·검증 단계의 락 수준 <https://www.postgresql.org/docs/17/sql-altertable.html>
  - PostgreSQL 15 릴리스 노트 — `UNIQUE NULLS NOT DISTINCT` <https://www.postgresql.org/docs/15/release-15.html>
  - 소스 `src/backend/utils/adt/ri_triggers.c` — `SELECT 1 FROM … FOR KEY SHARE OF x` <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/utils/adt/ri_triggers.c> · `src/backend/access/nbtree/nbtinsert.c` `_bt_check_unique`
- MySQL 8.4
  - 15.1.20.5 FOREIGN KEY Constraints(참조 쪽 인덱스 자동 생성, InnoDB NO ACTION = RESTRICT) <https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html>
  - 15.1.20.6 CHECK Constraints(TRUE 또는 UNKNOWN, `NOT ENFORCED`) <https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html> · 8.0판 같은 절(8.0.16 이전엔 무시)
  - 15.1.15 CREATE INDEX(UNIQUE는 NULL 다중 허용) <https://dev.mysql.com/doc/refman/8.4/en/create-index.html>
  - 15.2.7 INSERT(`IGNORE`는 무시 가능한 오류를 경고로) <https://dev.mysql.com/doc/refman/8.4/en/insert.html>
- Spring Framework `SQLErrorCodeSQLExceptionTranslator.java`(목록에 없는 코드는 폴백 `SQLExceptionSubclassTranslator`로) <https://github.com/spring-projects/spring-framework/blob/main/spring-jdbc/src/main/java/org/springframework/jdbc/support/SQLErrorCodeSQLExceptionTranslator.java>
- Spring Framework `sql-error-codes.xml`(PostgreSQL `duplicateKeyCodes` 23505, `dataIntegrityViolationCodes` 23502·23503·23514 / MySQL 1062, 1451·1452) <https://github.com/spring-projects/spring-framework/blob/main/spring-jdbc/src/main/resources/org/springframework/jdbc/support/sql-error-codes.xml>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): 기본 격리 수준 확인, 부모 삭제 트리거 시간(자식 FK 인덱스 유무), 앱 검증 경쟁(제약 없음 2행 / UNIQUE 1행+23505), 커밋 전 유일 충돌 대기(`Lock/transactionid`), FK 없는 고아 행 vs FK의 부모 삭제 대기·23503, UNIQUE NULL 다중 허용(두 제품)과 `NULLS NOT DISTINCT`, CHECK의 NULL 통과, 제약별 에러 코드(23502·23503·23514 / 1048·1062·1451·1452·3819), MySQL FK 인덱스 자동 생성
