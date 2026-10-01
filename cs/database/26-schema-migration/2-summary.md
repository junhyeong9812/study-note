# database/26-schema-migration — 무중단 스키마 변경: 락, expand/contract, 백필 — 정리 (힌트)

## 해결하는 문제

서비스는 멈추지 않는데, 테이블 모양은 바꿔야 한다.\
이때 세 가지가 동시에 문제가 된다.

```text
  ① DB 안:   ALTER TABLE 이 테이블 락을 잡는다  → 그동안 읽기·쓰기가 줄을 선다
  ② 앱 쪽:   배포 중에는 구버전·신버전 코드가 같은 테이블을 본다
  ③ 데이터:  코드는 이전 이미지로 되돌리면 되지만, 지운 컬럼·바꾼 값은 되돌릴 수 없다
```

쉬운 예: 영업 중인 식당의 메뉴판을 바꾼다.
- 메뉴판을 떼어 내는 동안 손님은 주문을 못 한다(①).
- 새 메뉴판을 걸었는데 주방 일부는 옛 레시피를 본다(②).
- 옛 메뉴판을 버렸는데 새 메뉴판에 오타가 있으면 되돌릴 원본이 없다(③).

똑같은 구조다.\
그래서 스키마 변경은 "한 번에 바꾸기"가 아니라 **작은 단계로 나눠, 각 단계가 짧게 잠그고, 신·구 코드 모두와 호환되게** 한다.

실무 예:
- 컬럼 하나 추가했을 뿐인데 API 전체가 수십 초 멈춘다. `ALTER`가 오래 도는 트랜잭션 뒤에서 락을 기다리고, 그 뒤로 평범한 `SELECT`까지 줄을 섰다.
- 컬럼 이름을 바꾸자마자 롤링 배포 중인 구버전 인스턴스가 `column "name" does not exist`를 낸다.
- 1억 행을 한 번의 `UPDATE`로 백필했더니 읽기 복제본이 수십 분 뒤처진다.

기초(무중단 배포 전략, expand/contract 5단계, "하면 안 되는 것" 표)는 원고 [server-design/08 §1~2](../../systems/server-design/08-deployment-ops.md)에 있다.\
이 노트는 그 밑의 **DB 엔진 동작**(어떤 DDL이 어떤 락을 얼마나 잡는가), 장애, 진단을 채운다.

## 동작·원리

### 1. DDL도 락을 잡는다 — 그리고 락은 줄을 선다

PostgreSQL 17에서 `ALTER TABLE`은 따로 적힌 예외가 없으면 **ACCESS EXCLUSIVE** 락을 잡는다(문서 ALTER TABLE).
  - *ACCESS EXCLUSIVE*: 가장 강한 테이블 락. 평범한 `SELECT`가 잡는 ACCESS SHARE와도 충돌한다.

문제는 `ALTER` 자체가 빠를 때도 생긴다.

```text
  시간 →
  세션 A: BEGIN; SELECT count(*) FROM t;  (ACCESS SHARE 보유) ......... sleep ......... COMMIT
  세션 B:        ALTER TABLE t ADD COLUMN c int;   → ACCESS EXCLUSIVE 대기 ─────────────┐ 실행(수 ms)
  세션 C:               SELECT count(*) FROM t;     → ACCESS SHARE 대기 (B 뒤에 줄 섬) ─┘ 실행

  pg_locks (예시, PostgreSQL 17.11, 로컬 재현)
   pid  |        mode         | granted
   4128 | AccessShareLock     | t        ← A
   4150 | AccessExclusiveLock | f        ← B: A를 기다림   pg_blocking_pids = {4128}
   4157 | AccessShareLock     | f        ← C: B를 기다림   pg_blocking_pids = {4150}
```

- C의 `SELECT`는 A와 충돌하지 않는다. 그런데 **먼저 와서 기다리는 B의 요청과 충돌**하므로 B 뒤에 선다.
- 그래서 "수 ms짜리 DDL"이 "A가 끝날 때까지 전체 읽기 정지"가 된다.
- A가 오래 도는 배치, 또는 `idle in transaction`으로 방치된 세션이면 정지도 그만큼 길다.

MySQL 8.4 InnoDB도 같은 모양이다. 락의 이름이 **메타데이터 락(MDL)**일 뿐이다.

```text
  performance_schema.metadata_locks (예시, MySQL 8.4.10, 로컬 재현)
  object | lock_type         | lock_status | 누구
  t      | SHARED_READ       | GRANTED     | A: 열린 트랜잭션 안의 SELECT
  t      | SHARED_UPGRADABLE | GRANTED     | B: ALTER ... ALGORITHM=INSTANT
  t      | EXCLUSIVE         | PENDING     | B: 정의 교체용 배타 MDL 대기
  t      | SHARED_READ       | PENDING     | C: 평범한 SELECT — B 뒤에 줄 섬

  SHOW PROCESSLIST → State: "Waiting for table metadata lock"
```

  - *메타데이터 락(MDL)*: 테이블 정의를 보호하는 서버 계층 락. 트랜잭션이 테이블을 한 번 건드리면 **트랜잭션이 끝날 때까지** 쥔다.
- MySQL 문서(Online DDL Performance and Concurrency)는 온라인 DDL이 실행 준비 단계(필요한 경우)와 정의 커밋 단계에서 잠깐 배타 MDL로 올라간다고 설명한다. 그리고 "대기 중인 배타 MDL 요청이 이후 트랜잭션을 막는다"고 명시한다.
- `ALGORITHM=INSTANT`라도 이 배타 MDL은 피할 수 없다. INSTANT가 줄이는 것은 **데이터 재작성 시간**이지 락 대기가 아니다.

**방어: 락 대기에 상한을 걸고 재시도한다.**

```sql
-- PostgreSQL 17: 락을 1초 안에 못 잡으면 포기(55P03), 잠시 뒤 재시도
SET lock_timeout = '1s';
ALTER TABLE t ADD COLUMN d int;
-- ERROR:  55P03: canceling statement due to lock timeout   (로컬 재현)

-- MySQL 8.4: MDL 대기 상한(세션). 기본값 31536000초 = 1년
SET SESSION lock_wait_timeout = 1;
ALTER TABLE t ADD COLUMN d int, ALGORITHM=INSTANT;
-- ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction   (로컬 재현)
```

- PG `lock_timeout`의 기본값은 0(끔)이다. MySQL `lock_wait_timeout`의 기본값은 31536000초다(두 값 모두 로컬 `SHOW`로 확인).
- MySQL은 MDL 대기 초과도 행 락 대기 초과와 같은 **1205**로 보고한다. 에러 번호만 보고 "행 락 문제"라고 단정하면 안 된다.

### 2. 어떤 변경이 빠르고, 어떤 변경이 테이블을 다시 쓰나

락을 잡은 **다음**에 걸리는 시간은 변경 종류가 정한다.

```text
                 메타데이터만 바꿈        전체 스캔(검증)          전체 재작성(rewrite)
                 ─────────────           ─────────────           ────────────────
  DDL 작업 시간     ms                      행 수에 비례              행 수 + 인덱스 재구축
  예(PG 17)      ADD COLUMN (기본값 없음   ADD CHECK / SET NOT NULL   ALTER COLUMN TYPE int→bigint
                 또는 상수 기본값)                                  ADD COLUMN ... DEFAULT clock_timestamp()
```

- 표는 DDL 작업 자체의 시간이다. PostgreSQL에서 잡은 테이블 락은 보통 **트랜잭션이 끝날 때까지** 유지된다(문서 13.3 "normally held until the end of the transaction"). 그래서 실제 락 보유 시간 = 작업 시간 + 커밋까지 남은 시간이다. DDL을 트랜잭션 안에 넣고 다른 일을 하면 ms짜리 변경도 `ACCESS EXCLUSIVE`를 오래 쥔다.

PostgreSQL 17 (문서 ALTER TABLE Notes + 로컬 재현, `pg_relation_filenode` 변화로 재작성 확인):

| 변경 | 재작성 | 재현(20만 행) |
|---|---|---|
| `ADD COLUMN e int NOT NULL DEFAULT 0` (비휘발 기본값) | 없음 — 기본값을 메타데이터에 저장 | 3.8 ms, filenode 그대로 |
| `ADD COLUMN f timestamptz DEFAULT clock_timestamp()` (휘발 기본값) | 있음 | filenode 바뀜 |
| `ALTER COLUMN c TYPE bigint` (int → bigint) | 있음 | filenode 바뀜 |
| `ALTER COLUMN name TYPE varchar(100)` (varchar(50)에서 늘림) | 없음 — 이진 호환 | filenode 그대로 |
| `ALTER COLUMN name TYPE varchar(50)` (text에서, 길이 제한을 새로 둠) | 있음(이 재현에서) | filenode 바뀜 |

MySQL 8.4 InnoDB (문서 Online DDL Operations + 로컬 재현):

| 변경 | 알고리즘 |
|---|---|
| `ADD COLUMN` | 8.4의 기본은 `INSTANT`. 제한: 행 버전 64개까지, `ROW_FORMAT=COMPRESSED`·FULLTEXT 테이블은 불가 |
| `MODIFY c bigint` (타입 변경) | `COPY`만 가능. `INSTANT`·`INPLACE`를 명시하면 `ERROR 1846`으로 거절(로컬 재현) |
| 보조 인덱스 추가 | `INPLACE`, 동시 DML 허용 |

- 운영 팁: MySQL에서는 `ALGORITHM=INSTANT`(또는 `INPLACE, LOCK=NONE`)를 **명시**한다. 원하는 방식이 불가능하면 조용히 COPY로 떨어지지 않고 에러로 멈춘다.
- PG에는 `ALGORITHM` 절이 없다. 스테이징에서 `pg_relation_filenode` 전후 비교로 재작성 여부를 확인한다.

> 참고: 원본 §2 표의 "`NOT NULL` 컬럼 즉시 추가 → 테이블 전체 락 (DB·버전에 따라)"은 조건을 구체적으로 적을 수 있다. PostgreSQL 11 이후는 **비휘발(non-volatile) 기본값을 가진** `NOT NULL` 컬럼 추가가 재작성 없이 끝나고(문서 ALTER TABLE Notes, 위 표 3.8 ms), MySQL 8.4는 `INSTANT`로 추가한다. 다만 두 경우 모두 1절의 **락 대기**는 여전히 생긴다.

### 3. 제약·인덱스는 "잠깐 잠그고, 검증은 따로"

큰 테이블에 제약을 걸면 검증 스캔이 락을 오래 쥔다. PostgreSQL 17은 이를 둘로 쪼갠다.

```text
  1) ADD CONSTRAINT ... NOT VALID      짧은 락. 스캔 없음. 이후 INSERT/UPDATE부터 강제
  2) 기존 위반 행 정리(백필)
  3) VALIDATE CONSTRAINT               SHARE UPDATE EXCLUSIVE — 읽기·쓰기와 공존하며 스캔
  4) (NOT NULL이 목표면) SET NOT NULL   유효한 CHECK(col IS NOT NULL)이 있으면 스캔 생략
```

- 로컬 재현(PostgreSQL 17.11): `NOT VALID` 추가 직후 NULL `INSERT`는 즉시 거절됐다. 위반 행이 남은 상태의 `VALIDATE`는 `check constraint "name_nn" ... is violated by some row`로 실패했다. 정리 후 `VALIDATE`가 성공했고, 이어진 `SET NOT NULL`은 2.7 ms에 끝났다.
- `NOT VALID`는 FOREIGN KEY와 CHECK에만 쓸 수 있다(문서).

인덱스는 `CREATE INDEX CONCURRENTLY`다.
- 쓰기를 막지 않는 대신 테이블을 두 번 스캔하고, 기존 트랜잭션이 끝나기를 기다린다. 트랜잭션 블록 안에서는 못 쓴다(문서 CREATE INDEX).
- 실패하면 **INVALID 인덱스가 남는다.** 쿼리에는 안 쓰이지만 쓰기 비용은 계속 낸다. 유니크 인덱스가 두 번째 스캔에서 실패했다면 유니크 제약도 계속 강제한다(문서).

```text
  (예시, PostgreSQL 17.11) 중복 값이 있는 컬럼에 CREATE UNIQUE INDEX CONCURRENTLY
  ERROR:  could not create unique index "t_name_uq"
  \d t →  "t_name_uq" UNIQUE, btree (name) INVALID
```

### 4. expand/contract — 신·구 코드가 같이 도는 시간을 설계한다

원고 §2의 5단계를 **배포 버전과 겹쳐서** 보면 왜 각 단계가 필요한지 보인다(`name` → `full_name`).

```text
  스키마      [name]      [name, full_name]  ─────────────────────────────  [full_name]
  단계        (현재)      ① expand           ③ backfill      ④ switch        ⑤ contract
  코드 v1     name 읽기·쓰기 ─────────────────── (v1이 모두 내려갈 때까지 name 유지)
  코드 v2                ② name+full_name 양쪽 쓰기, name 읽기
  코드 v3                                              full_name 읽기(양쪽 쓰기 유지)
  코드 v4                                                               full_name만
  되돌리기    ①~④는 코드만 이전으로 돌리면 된다.  ⑤ 뒤로는 name 데이터가 없다 → 되돌리기 불가
```

- 규칙: **어느 시점이든, 살아 있는 모든 코드 버전이 현재 스키마에서 동작해야 한다.**
- ③ 백필은 v2가 모든 인스턴스에 퍼져 **v1이 다 내려간 뒤** 시작한다. v1이 남아 있으면 백필 뒤에도 v1이 `name`만 바꾼 행의 `full_name`이 다시 낡는다.
- 되돌릴 수 없는 단계(⑤ DROP, 타입 축소)는 **맨 끝에, 따로, 충분한 관찰 뒤에** 한다. 이 단계는 "롤백"이 아니라 "앞으로 고치기(forward fix)"만 가능하다고 전제한다.

### 5. DDL과 트랜잭션 — 제품마다 다르다

```text
  (예시, 로컬 재현)       BEGIN; INSERT 1행; ALTER TABLE r ADD COLUMN x; ROLLBACK;
  PostgreSQL 17.11   →   행도 없고 컬럼도 없다   (DDL이 트랜잭션에 참여)
  MySQL 8.4.10       →   행도 있고 컬럼도 있다   (ALTER가 앞 트랜잭션을 암묵 커밋)
```

- MySQL 8.4 문서: "Atomic DDL is not transactional DDL." DDL 한 문장은 원자적이다(중간에 죽어도 반쯤 바뀐 정의는 남지 않음). 하지만 앞선 트랜잭션을 암묵적으로 커밋한다.
- 그래서 MySQL에서 "마이그레이션 파일 여러 문장을 트랜잭션으로 감싸 실패 시 전부 롤백"은 성립하지 않는다. 실패한 지점까지 적용된 상태로 남는다.
- PostgreSQL에서도 예외가 있다. `CREATE INDEX CONCURRENTLY` 등은 트랜잭션 블록 안에서 못 쓴다.

### 6. 백필 — 작게 나눠, 복제본 속도에 맞춰

```text
  나쁜 예:  UPDATE big SET full_name = name;          -- 1억 행, 1 트랜잭션
            └ 행 락 1억 개를 커밋까지 보유, undo/WAL 폭증,
              MySQL: 트랜잭션 전체가 커밋 시점에 binlog로 → 복제본이 그만큼 한 번에 재생

  좋은 예:  keyset 청크 + 청크마다 커밋 + 복제 지연 보고 쉬기
            id  1 ~ 5000   UPDATE ... ; COMMIT;  lag 확인 → OK
            id 5001~10000  UPDATE ... ; COMMIT;  lag 확인 → 높음 → sleep
            ...            (마지막 처리 id를 기록 → 중단해도 거기서 재시작)
```

- MySQL 8.4 문서(The Binary Log): 트랜잭션의 변경은 커밋 전까지 binlog 캐시에 모였다가 **커밋 때 한 번에** binlog에 쓰인다. 그래서 거대한 트랜잭션 하나는 복제본에서도 한 덩어리로 재생된다.
- 복제 지연 지표: PostgreSQL `pg_stat_replication.replay_lag`, MySQL `SHOW REPLICA STATUS`의 `Seconds_Behind_Source`.
- 대량 DML의 청크·스로틀·재시작·검증은 34번 노트의 주제다(아래 링크).

## 쓰이는 자료구조·알고리즘

- **락 대기 큐 + 충돌 행렬**: 테이블마다 대기 요청 목록이 있다. 새 요청은 이미 쥔 락뿐 아니라 **앞에서 기다리는 요청과의 충돌**도 본다. 1절의 "SELECT가 ALTER 뒤에 줄 서는" 현상이 여기서 나온다. 락 모드와 교착은 [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md).
- **keyset 순회(B+Tree 범위 스캔)**: `WHERE id > :last ORDER BY id LIMIT n`은 PK 인덱스의 범위 스캔이다. OFFSET과 달리 청크마다 비용이 일정하다. B+Tree는 [08-btree-indexes](../08-btree-indexes/2-summary.md), [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md).
- **버전 번호가 붙은 마이그레이션 이력 테이블**: 적용한 스크립트의 번호·체크섬을 기록한다. 예: Flyway 기본 테이블 이름 `flyway_schema_history`(Flyway 소스 `FlywayModel`).
- **행 버전(MySQL INSTANT)**: 컬럼을 하나 이상 즉시 추가·삭제하는 `ALTER TABLE ... ALGORITHM=INSTANT` 문장마다 테이블의 행 버전이 하나 늘고(로컬 재현: 한 문장에 2개 추가 → `TOTAL_ROW_VERSIONS` 1), 각 행은 자기 버전으로 해석된다. 상한이 64개라 INSTANT 변경을 계속 쌓으면 결국 재구축이 필요하다(문서).
- **섀도 테이블 + 변경 따라잡기**: 새 정의의 빈 테이블에 복사하면서 원본 변경을 따라잡고, 마지막에 이름을 바꾼다. pt-online-schema-change는 트리거로, gh-ost는 binlog 스트림으로 변경을 따라잡는다(각 문서·README).

## 적용 — 풀어나가는 법

**1) 변경을 분류한다.**

```text
  이 변경은?  메타데이터만 / 스캔 / 재작성          → 락을 얼마나 쥐나
  구버전 코드가 새 스키마에서 도나?  예 / 아니오      → 아니오면 expand/contract로 쪼갬
  되돌릴 수 있나?  예 / 아니오(DROP·축소·값 덮어쓰기) → 아니오면 마지막 단계로, 백업 확인
```

**2) 스테이징에서 실제 크기로 확인한다.**

```sql
-- PostgreSQL: 재작성 여부
SELECT pg_relation_filenode('t');   -- 변경 전후 비교
-- MySQL: 원하는 알고리즘을 명시해서 불가능하면 에러로 멈추게
ALTER TABLE t ADD COLUMN c int, ALGORITHM=INSTANT;
```

**3) 운영 적용 직전에 "지금 오래 도는 트랜잭션"을 본다.**

```sql
-- PostgreSQL
SELECT pid, now() - xact_start AS xact_age, state, left(query, 60)
FROM pg_stat_activity
WHERE datname = current_database() AND xact_start IS NOT NULL
ORDER BY xact_age DESC LIMIT 5;

-- MySQL
SELECT trx_mysql_thread_id, trx_started, trx_state
FROM information_schema.innodb_trx ORDER BY trx_started LIMIT 5;
```

**4) 락 대기 상한 + 재시도로 적용한다.**

```sql
-- PostgreSQL
SET lock_timeout = '2s';            -- 세션 단위 (postgresql.conf 전역 설정은 문서가 비권장)
ALTER TABLE orders ADD COLUMN memo text;
-- 실패(55P03)하면 잠시 뒤 재시도. 성공할 때까지 사람 대신 스크립트가 반복

-- MySQL
SET SESSION lock_wait_timeout = 2;
ALTER TABLE orders ADD COLUMN memo text, ALGORITHM=INSTANT;
```

**5) 적용 중 막힘을 진단한다.**

```sql
-- PostgreSQL: 누가 누구를 막나
SELECT pid, wait_event_type, wait_event, pg_blocking_pids(pid) AS blocked_by, left(query, 50)
FROM pg_stat_activity WHERE wait_event_type = 'Lock';

-- MySQL: MDL 대기
SELECT object_name, lock_type, lock_status, owner_thread_id
FROM performance_schema.metadata_locks WHERE object_schema = DATABASE();
```

**6) 앱 쪽 순서 (Java 예)**: 배포 파이프라인이 "마이그레이션 → 앱 배포" 순서를 강제하고, 앱 기동 시 자동 마이그레이션은 끄거나 한 인스턴스만 하게 한다.

```java
// v2: 양쪽 쓰기 — 구버전(v1)이 여전히 name을 읽으므로 name도 계속 채운다
@Transactional
public void rename(long userId, String fullName) {
    jdbc.update("UPDATE users SET name = ?, full_name = ? WHERE id = ?",
                fullName, fullName, userId);
}
```

## 장애 시나리오와 대처

**① `ALTER TABLE` 한 줄로 서비스 정지 (커리큘럼 ⚠)**
- 현상: 컬럼 추가 배포 직후 API p99가 수십 초로 뛰고 커넥션 풀이 고갈된다.
- 보이는 형태: PG `pg_stat_activity`에 `wait_event_type = Lock`이 줄줄이, `pg_blocking_pids`가 `ALTER`의 pid를 가리킴. MySQL `SHOW PROCESSLIST`에 `Waiting for table metadata lock`이 수십 개. 앱에는 풀 대기 타임아웃.
- 원인: 오래 도는 트랜잭션(또는 `idle in transaction`)이 테이블 락을 쥐었다. `ALTER`가 배타 락을 기다리고, 그 뒤로 모든 조회가 줄을 섰다. `ALTER` 자체는 빠른 종류여도 생긴다.
- 대처: 즉시 `ALTER` 세션을 취소한다(PG `pg_cancel_backend`, MySQL `KILL QUERY`). 재발 방지로 `lock_timeout`/`lock_wait_timeout` + 재시도, 적용 전 장기 트랜잭션 확인, `idle_in_transaction_session_timeout` 같은 서버 측 상한(22번 노트)을 둔다.

**② 롤백할 수 없는 마이그레이션 (커리큘럼 ⚠)**
- 현상: 컬럼 rename·drop을 배포와 함께 했다. 신버전에 버그가 있어 이전 이미지로 되돌렸는데 구버전이 즉시 죽는다.
- 보이는 형태: PG `ERROR: column "name" does not exist`(SQLSTATE 42703), MySQL `ERROR 1054 (42S22): Unknown column 'name' in 'field list'`(SELECT 목록에서 난 경우, 로컬 재현).
- 원인: 스키마가 구버전 코드와 호환되지 않는 방향으로 이미 바뀌었다. 데이터는 이미지 롤백으로 돌아오지 않는다.
- 대처: expand/contract로 쪼개 "살아 있는 모든 코드 버전이 현재 스키마에서 동작"을 지킨다. DROP·축소는 맨 끝 별도 배포로 한다. MySQL은 DDL이 트랜잭션으로 묶이지 않으므로 다문장 마이그레이션의 중간 실패 상태도 대비한다.

**③ 백필이 복제 지연을 만든다 (커리큘럼 ⚠)**
- 현상: 백필 시작 뒤 복제본에서 읽는 화면이 "방금 저장한 게 안 보인다"는 문의가 몰린다.
- 보이는 형태: `Seconds_Behind_Source` 또는 `replay_lag`가 수 분~수십 분. 원본의 WAL·binlog 생성량이 급증한다.
- 원인: 한 번에 너무 많이 쓴다. 특히 MySQL에서 거대 트랜잭션은 커밋 시점에 통째로 binlog에 쓰이고, 복제본이 한 덩어리로 재생한다.
- 대처: keyset 청크 + 청크별 커밋 + 복제 지연이 임계를 넘으면 쉬기. 재시작 지점을 기록한다(34번 노트).

**④ `CREATE INDEX CONCURRENTLY` 실패 후 남은 INVALID 인덱스**
- 현상: 인덱스 생성이 실패했는데 쓰기 지연이 조금 늘었다. 같은 이름으로 다시 만들려니 이미 있다고 한다.
- 보이는 형태: `\d t`에 `INVALID`, `pg_index.indisvalid = false`.
- 원인: CIC는 실패해도 카탈로그에 인덱스를 남긴다. 유지 비용은 계속 들고, 유니크 인덱스가 두 번째 스캔에서 실패했다면 제약도 계속 강제한다.
- 대처: `DROP INDEX CONCURRENTLY` 후 원인(중복 값·교착)을 없애고 다시 만든다. 또는 `REINDEX INDEX CONCURRENTLY`.

**⑤ INSTANT가 갑자기 안 된다 (MySQL)**
- 현상: 늘 몇 ms에 끝나던 컬럼 추가가 에러를 낸다.
- 보이는 형태: `ERROR 4092 ... Maximum row versions reached ... Please use COPY/INPLACE.`
- 원인: INSTANT 추가·삭제가 누적돼 행 버전이 상한(8.4에서 64)에 닿았다.
- 대처: `INFORMATION_SCHEMA.INNODB_TABLES.TOTAL_ROW_VERSIONS`를 감시한다. 한가한 시간에 재구축(`OPTIMIZE TABLE` 또는 재구축 ALTER)으로 0으로 되돌리거나, 섀도 테이블 도구를 쓴다.

## 핵심 문장

- DDL이 빠른 종류여도 **락 대기**는 생긴다. 배타 락 요청이 줄에 서면 그 뒤의 평범한 조회까지 막힌다.
- 그래서 스키마 변경에는 `lock_timeout`(PG)·`lock_wait_timeout`(MySQL)으로 대기 상한을 걸고 재시도한다.
- 락을 쥔 **뒤** 걸리는 시간은 변경 종류가 정한다: 메타데이터만 / 검증 스캔 / 전체 재작성. 재작성 여부는 버전마다 다르므로 스테이징에서 확인한다.
- expand/contract의 규칙은 하나다. 어느 시점이든 살아 있는 모든 코드 버전이 현재 스키마에서 동작해야 한다.
- 되돌릴 수 없는 단계(DROP·축소)는 맨 끝에 따로 한다. PostgreSQL DDL은 트랜잭션에 참여하지만, MySQL DDL은 앞 트랜잭션을 암묵 커밋한다.
- 백필은 작은 청크로, 복제 지연을 보면서, 재시작 가능하게 한다.

## 관련 주제·근거

- 선행
  - [08-btree-indexes](../08-btree-indexes/2-summary.md) — 인덱스 구조, keyset 순회의 바탕
  - [16-mvcc](../16-mvcc/2-summary.md) — 재작성 DDL이 MVCC-safe하지 않은 이유(문서 ALTER TABLE Notes)
- 연결
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md) — 락 모드·대기
  - [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md) — `lock_timeout`·`idle_in_transaction_session_timeout`
  - [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md) — 청크·스로틀·재시작·검증
  - [32-replication-leader-follower](../32-replication-leader-follower/2-summary.md) — 복제 지연. 원고 [server-design/03-data-layer](../../systems/server-design/03-data-layer.md)
  - 원고 [server-design/08-deployment-ops §1~3](../../systems/server-design/08-deployment-ops.md) — 무중단 배포·expand/contract·롤백 가능성
- PostgreSQL 17 문서
  - ALTER TABLE(락 수준, `NOT VALID`/`VALIDATE CONSTRAINT`, Notes의 재작성 조건) <https://www.postgresql.org/docs/17/sql-altertable.html>
  - CREATE INDEX "Building Indexes Concurrently"(두 번 스캔, INVALID 인덱스) <https://www.postgresql.org/docs/17/sql-createindex.html>
  - 19.11 Client Connection Defaults — `lock_timeout` <https://www.postgresql.org/docs/17/runtime-config-client.html>
  - 13.3 Explicit Locking(락은 보통 트랜잭션 끝까지 유지) <https://www.postgresql.org/docs/17/explicit-locking.html>
  - PostgreSQL 11 Release Notes — "add a column with a non-null default without doing a table rewrite" <https://www.postgresql.org/docs/release/11.0/>
  - 27.2 `pg_stat_replication.replay_lag` <https://www.postgresql.org/docs/17/monitoring-stats.html>
- MySQL 8.4 Reference Manual
  - 17.12.1 Online DDL Operations(INSTANT 기본, 행 버전 64, 타입 변경은 COPY) <https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html>
  - 17.12.2 Online DDL Performance and Concurrency — "Online DDL and Metadata Locks" <https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-performance.html>
  - 15.1.1 Atomic Data Definition Statement Support("not transactional DDL") <https://dev.mysql.com/doc/refman/8.4/en/atomic-ddl.html>
  - 15.3.3 Statements That Cause an Implicit Commit <https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html>
  - 7.4.4 The Binary Log(커밋 때 binlog 기록) <https://dev.mysql.com/doc/refman/8.4/en/binary-log.html> · SHOW REPLICA STATUS <https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html>
- 도구
  - gh-ost README(트리거 없이 binlog로 따라잡기) <https://github.com/github/gh-ost> · Percona pt-online-schema-change 문서(트리거) <https://docs.percona.com/percona-toolkit/pt-online-schema-change.html>
  - Flyway 소스 `flyway-core/.../FlywayModel.java`(기본 이력 테이블 `flyway_schema_history`)
- 교재: Sadalage–Ambler 『Refactoring Databases』(2006) [?] — 미열람
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10, 20만 행): 락 대기 줄(pg_locks·metadata_locks), `lock_timeout` 55P03·`lock_wait_timeout` 1205, 변경별 재작성 여부(filenode), `NOT VALID`→`VALIDATE`→`SET NOT NULL`, CIC 실패 INVALID, MySQL 타입 변경 1846, DDL과 ROLLBACK
