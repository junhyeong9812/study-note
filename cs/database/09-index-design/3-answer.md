# database/09-index-design — 정답

## 정답

### 1. 읽는 구간과 오른쪽 컬럼 조건

```text
  (a, b, c) 정렬:  ... (5,41,*) | (5,42,*) ... (5,99,*) | (6, ...)
                              ^ 시작                   ^ 끝 (a=5의 마지막)
  c < 77 은 이 구간 안의 항목을 하나씩 보며 거른다 (읽는 양은 그대로)
```

- 선행 컬럼의 등호(`a = 5`)와 등호가 없는 첫 컬럼의 부등호(`b >= 42`)가 읽을 범위를 정한다. `(5, 42)`부터 `a = 5`의 끝까지 읽는다(PostgreSQL 17 11.3).
- `c < 77`은 인덱스 안에서 걸러 힙 방문을 줄인다. 읽는 인덱스 구간은 줄이지 못한다.
- 이 규칙은 복합 키가 **사전순**으로 정렬되기 때문이다. `b`가 범위로 풀리면 그 안에서 `c`는 더 이상 연속된 구간이 아니다.

### 2. 선행 컬럼이 빠진 조건

| | `SELECT *` | `SELECT tenant_id, created_at` |
|---|---|---|
| PostgreSQL 17 | 순차 스캔 | 순차 스캔이 보통(인덱스 전체 스캔보다 싸다고 추정되면) |
| MySQL 8.4 | `Table scan` | `Covering index skip scan` 가능 |

- 로컬 재현(예시): PostgreSQL 17.11은 `Parallel Seq Scan`. MySQL 8.4.10은 `SELECT *`에 `Table scan on ev`, 인덱스 컬럼만 고른 쿼리에 `Covering index skip scan on ev using ev_tenant_created`.
- MySQL skip scan은 테이블 하나, `GROUP BY`·`DISTINCT` 없음, **인덱스 컬럼만 참조** 같은 조건이 모두 맞아야 한다(MySQL 8.4 10.2.1.2). `ev`의 `SELECT *`는 인덱스에 없는 컬럼(`amount` 등)까지 요구하므로 마지막 조건을 어긴다.
- PostgreSQL 17 B-tree에는 skip scan이 없다. 18 문서에 설명이 추가됐다.

### 3. `Heap Fetches`와 가시성 맵

- PostgreSQL 인덱스 항목에는 MVCC 가시성 정보가 없다. 인덱스 전용 스캔은 해당 힙 페이지의 가시성 맵 비트가 켜져 있을 때만 힙을 건너뛴다(11.9).
- UPDATE 직후에는 그 페이지들의 비트가 꺼져 있다. 그래서 힙을 방문했다. 로컬 재현에서 400행을 갱신한 직후 `Heap Fetches: 800`이었다. 옛 버전과 새 버전의 인덱스 항목을 모두 확인했기 때문으로 보인다.
- VACUUM이 비트를 다시 켜면 0이 된다. 로컬 재현에서도 VACUUM 뒤 `Heap Fetches: 0`, 버퍼 807 → 7이었다.
- InnoDB 보조 인덱스 레코드는 PK 컬럼을 담는다(MySQL 8.4 17.6.2.1). 그래서 `SELECT id, tenant_id`도 `(tenant_id, …)` 인덱스로 커버된다. MySQL에는 `INCLUDE`가 없어서, 짐 컬럼은 키 컬럼으로 붙여야 한다.

### 4. 대기 주문 인덱스

```sql
-- PostgreSQL 17: 부분 인덱스 (대상 행만)
CREATE INDEX orders_pending ON orders (created_at) WHERE status = 'pending';
SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at LIMIT 10;

-- MySQL 8.4: 부분 인덱스가 없다 → 복합 인덱스
CREATE INDEX orders_status_created ON orders (status, created_at);
```

- 로컬 재현(예시): 전체 `(status, created_at)` 인덱스는 6184 kB, 부분 인덱스는 64 kB였다. 대기 10건 조회는 `Index Scan using ev_pending`으로 0.03 ms였다.
- 부분 인덱스는 쿼리의 `WHERE`가 인덱스 술어를 함의한다고 플래너가 알아볼 때만 쓰인다. 매칭은 계획 시점에 한다. 그래서 문서는 `status = ?` 같은 파라미터 절이 부분 인덱스와 맞지 않는다고 적는다(PostgreSQL 17 11.8). 값을 넣어 계획하는 custom plan이면 쓰일 수 있지만 generic plan으로 바뀌면 못 쓴다. 확실하게 하려면 `'pending'`을 리터럴로 쓴다.

### 5. 함수가 씌워진 컬럼

- `EXPLAIN`: `Seq Scan`(또는 `Parallel Seq Scan`)과 `Filter: (lower(email) = '…'::text)`. 로컬 재현(PostgreSQL 17.11)에서 표현식 인덱스가 없을 때 그렇게 나왔다.
- 원인: `email` 인덱스는 원래 값의 순서다. `lower(email)`의 순서는 모른다.
- 고치는 법
  1. 저장할 때 소문자로 정규화하고 `WHERE email = ?`로 조회한다.
  2. 표현식 인덱스를 만든다. PostgreSQL `CREATE INDEX ON users (lower(email))`, MySQL 8.4 `CREATE INDEX … ((lower(email)))`. 로컬 재현에서 PostgreSQL은 `Index Scan using ev_email_lower`, MySQL은 `Index lookup on ev using ev_email_lower`였다.

### 6. 같은 조건, 다른 계획

- `status='done'`만으로 99%를 가져오면, 인덱스를 따라 힙을 행마다 방문하는 비용이 전체 순차 스캔보다 크다. 그래서 `Seq Scan`이다.
- `ORDER BY created_at LIMIT 10`이면 인덱스 `(status, created_at)`은 `status='done'` 구간을 이미 `created_at` 순서로 갖고 있다. 앞에서 10개만 읽고 멈추면 된다. 정렬도 필요 없다.
- 선택도만으로 판단하지 말고 "몇 행을 읽고 멈출 수 있는가"까지 본다.

### 7. 인덱스 과다

- 원인
  1. 행마다 그 행을 담는 모든 인덱스에 항목을 넣는다(부분 인덱스는 술어를 만족하는 행만). 로컬 재현에서 보조 인덱스 5개를 더하자 같은 20만 행 적재의 WAL이 34 MB → 121 MB, 시간이 0.26 s → 2.73 s였다(예시).
  2. PostgreSQL에서 인덱스 컬럼을 바꾸는 UPDATE는 HOT가 안 되어 모든 인덱스(부분 인덱스는 술어를 만족할 때만)에 새 항목을 넣는다.
- 지울 인덱스를 고를 때
  - `pg_stat_user_indexes.idx_scan`(MySQL은 `sys.schema_unused_indexes`)이 0인지 본다.
  - 통계가 언제 리셋됐는지, 월말 배치처럼 드물게 도는 쿼리가 있는지, 복제본에서만 쓰는 쿼리는 아닌지 확인한다. 통계는 서버별로 따로 쌓인다.
  - UNIQUE·PK처럼 제약을 지키는 인덱스는 조회가 없어도 지우면 안 된다.
  - MySQL은 먼저 `INVISIBLE`로 바꿔 영향을 본다(10.3.12).

### 8. HOT 갱신

- 인덱스 컬럼을 안 바꾸고 같은 페이지에 자리가 있으면 HOT 갱신이다. 새 행 버전을 만들어도 **인덱스 항목은 새로 만들지 않는다**(PostgreSQL 17 65.7).
- 인덱스 컬럼을 하나라도 바꾸면 HOT가 아니다. 그 테이블의 **모든 인덱스**(부분 인덱스는 새 버전이 술어를 만족할 때만)에 새 항목이 들어간다. 예외로, BRIN 같은 요약(summarizing) 인덱스의 컬럼만 바뀐 경우는 HOT가 유지된다(요약 인덱스만 갱신될 수 있다).
- 그래서 인덱스가 많을수록, 그리고 자주 바뀌는 컬럼에 인덱스가 걸릴수록 UPDATE 비용이 커진다. HOT 비율은 `pg_stat_all_tables`(`n_tup_hot_upd`)로 본다.

### 9. INVALID 인덱스

- 실패하면 카탈로그에 **INVALID 인덱스**가 남는다. `\d`에 `INVALID`로 보인다(PostgreSQL 17 CREATE INDEX).
- 조회에는 안 쓰이지만 갱신 비용은 계속 낸다. 즉 이득 없이 쓰기만 느리게 한다.
- UNIQUE 인덱스라면 더 있다. 두 번째 테이블 스캔 중에 실패한 경우, 이 INVALID 인덱스는 **유일성 검사를 계속 강제한다**. 그래서 다른 쓰기가 유일성 위반 에러를 받을 수 있다(PostgreSQL 17 CREATE INDEX).
- 정리: `DROP INDEX CONCURRENTLY`로 지우고, 유일성 위반 데이터를 정리한 뒤 다시 만든다. (`REINDEX INDEX CONCURRENTLY`로 다시 짓는 방법도 문서에 있다.)
- `CONCURRENTLY` 없이 만들면 테이블에 `SHARE` 락을 잡는다. 읽기는 되지만 `INSERT`·`UPDATE`·`DELETE`가 생성이 끝날 때까지 막힌다(PostgreSQL 17 13.3.1, CREATE INDEX).
