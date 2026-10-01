# database/02-keys-and-constraints — 정답

## 정답

### 1. 앱 검증의 틈과 UNIQUE

```text
  요청 A: SELECT → 없음 ──────────── INSERT
  요청 B:          SELECT → 없음 ──────────── INSERT
  → 둘 다 "없음"을 보고 둘 다 넣는다.
```

- 조회와 삽입이 별개 문장이라 그 사이에 다른 요청이 끼어든다. PostgreSQL 기본 READ COMMITTED, MySQL 기본 REPEATABLE READ에서도 이 틈은 남는다(로컬 재현: 제약 없는 테이블에 2행).
- `UNIQUE`는 유일 B-tree 인덱스에 **넣는 순간** 같은 키를 찾는다. 확인과 쓰기가 한 지점이다. 두 번째 삽입은 첫 번째가 커밋되면 `23505`로 실패한다(로컬 재현: 1행 + 23505).

### 2. 키 구분

- 슈퍼키: 유일하게 식별하는 속성 집합 전부. `{id}`, `{email}`, `{id, name}`, `{email, phone}` 등.
- 후보 키: 최소 슈퍼키. `{id}`, `{email}`. `{id, name}`은 name을 빼도 식별되므로 후보 키가 아니다.
- 기본 키: 후보 키 중 대표로 고른 것. 보통 `{id}`.
- 대체 키: 기본 키가 아닌 후보 키 `{email}`. `UNIQUE`(+ `NOT NULL`)로 선언한다.

### 3. 커밋 안 된 유일 충돌

- B는 **기다린다**. A가 커밋할지 알 수 없기 때문이다(PostgreSQL 17 62.5).
  - A 커밋 → B는 `ERROR 23505 duplicate key value violates unique constraint`.
  - A 롤백 → 충돌이 없으므로 B의 INSERT가 성공한다.
- 로컬 재현(예시, PostgreSQL 17.11): B는 `wait_event_type = Lock`, `wait_event = transactionid`로 보였다. A의 트랜잭션 ID 락을 기다리는 것이다. A 커밋 뒤 B가 23505로 끝났다(약 1.4초).

### 4. NULL과 제약

| | PostgreSQL 17 | MySQL 8.4 |
|---|---|---|
| (a) UNIQUE에 NULL 둘 | 성공 | 성공 |
| (b) CHECK (qty > 0)에 NULL | 성공 | 성공 |
| (c) NULLS NOT DISTINCT에 NULL 둘 | 두 번째 실패(23505) | 해당 문법 없음 |

- (a) 두 제품 모두 NULL끼리 같다고 보지 않는다(PG 5.5.3, MySQL 15.1.15).
- (b) CHECK는 식이 거짓일 때만 거부한다. `NULL > 0`은 UNKNOWN이라 통과한다(PG 5.5.1, MySQL 15.1.20.6).
- (c) PostgreSQL 15부터 있는 옵션이다.

### 5. FK 검사가 조회하는 것

- 자식 INSERT·UPDATE: 부모 키(이 예에서는 PK) 인덱스에서 그 키를 찾는다. PostgreSQL RI 트리거는 `SELECT 1 FROM parent x WHERE id = $1 FOR KEY SHARE OF x`를 돌린다(`ri_triggers.c`). 부모 행에 공유 락이 걸려, 자식 트랜잭션이 끝날 때까지 부모 삭제가 기다린다.
- 부모 DELETE·키 UPDATE: 자식 테이블에서 그 키를 참조하는 행을 찾는다. 자식 FK 열에 인덱스가 없으면 전체 스캔이다.
- PostgreSQL: 자식 FK 열 인덱스를 **자동으로 만들지 않는다**(5.5.5). MySQL InnoDB: FK 열이 앞에 오는 인덱스가 **필요**하고, 없으면 **자동으로 만든다**(15.1.20.5, 로컬 재현 `SHOW INDEX`).

### 6. NO ACTION vs RESTRICT

- PostgreSQL: 둘 다 참조 행이 있으면 오류다. 차이는 `NO ACTION`만 검사를 트랜잭션 뒤로 **미룰 수 있다**(DEFERRABLE)는 점이다. `RESTRICT`는 즉시 검사한다(5.5.5). 기본은 `NO ACTION`.
- MySQL InnoDB: `NO ACTION` = `RESTRICT`. 즉시 거부한다. 미룬 검사는 NDB만 지원한다(15.1.20.5).

### 7. 운영 중 제약 추가 (PostgreSQL)

```sql
-- 0) 점검: 이미 위반한 행
SELECT count(*) FROM orders WHERE qty <= 0;                                    -- CHECK 위반 (NULL은 위반 아님)
SELECT count(*) FROM orders o LEFT JOIN member m ON m.id = o.member_id
WHERE o.member_id IS NOT NULL AND m.id IS NULL;                                -- 고아 행

-- 1) 자식 쪽 인덱스 (부모 삭제 대비)
CREATE INDEX CONCURRENTLY orders_member_id_idx ON orders(member_id);

-- 2) 새 행만 검사하도록 추가 (기존 행 스캔 없음)
ALTER TABLE orders ADD CONSTRAINT orders_qty_pos CHECK (qty > 0) NOT VALID;
ALTER TABLE orders ADD CONSTRAINT orders_member_fk FOREIGN KEY (member_id) REFERENCES member(id) NOT VALID;

-- 3) 위반 행 정리 후 검증
ALTER TABLE orders VALIDATE CONSTRAINT orders_qty_pos;
ALTER TABLE orders VALIDATE CONSTRAINT orders_member_fk;
```

- `NOT VALID` 추가는 기존 행 스캔 없이 바로 끝난다. 다만 추가하는 순간에는 짧게 락을 잡는다(CHECK는 `ACCESS EXCLUSIVE`, FK는 `SHARE ROW EXCLUSIVE`). 검증 단계는 `SHARE UPDATE EXCLUSIVE`만 잡아 일반 쓰기를 막지 않는다(PostgreSQL 17 ALTER TABLE).

### 8. 부모 삭제가 느림

- 원인: 부모 한 행을 지울 때마다 RI 트리거가 자식 테이블에서 참조 행을 찾는다. `orders.member_id`에 인덱스가 없어 매번 전체 스캔한다. PostgreSQL은 이 인덱스를 자동으로 만들지 않는다.
- 로컬 재현(예시, PostgreSQL 17.11, 자식 20만 행): 트리거 시간 8.870ms → 인덱스 생성 후 0.411ms.
- 대처: `CREATE INDEX CONCURRENTLY … ON orders(member_id)`.
- MySQL InnoDB는 FK를 만들 때 필요한 인덱스를 자동으로 만들므로, 보통 같은 원인은 생기지 않는다. 단 그 인덱스는 다른 인덱스가 대신할 수 있으면 조용히 없어질 수 있다(15.1.20.5).

### 9. 중복 에러와 예외 매핑

- PostgreSQL: SQLSTATE `23505`(`duplicate key value violates unique constraint "…"`).
- MySQL: `ERROR 1062 (23000): Duplicate entry 'a@x.com' for key 'm.email'`(로컬 재현).
- Spring `sql-error-codes.xml`: PostgreSQL은 SQLSTATE로 번역하며 `23505` → `DuplicateKeyException`. MySQL은 에러 번호로 번역하며 `1062` → `DuplicateKeyException`. 둘 다 `DataIntegrityViolationException`의 하위다.
- 처리: 예외를 잡아 "이미 사용 중" 같은 비즈니스 오류로 바꾼다. 트랜잭션 안이면 PostgreSQL은 그 트랜잭션이 중단 상태가 되므로 롤백 후 다시 시작해야 한다. 멱등 처리가 목적이면 `ON CONFLICT DO NOTHING`(PG)으로 예외 없이 처리한다.
