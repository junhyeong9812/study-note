# database/16-mvcc — MVCC: 버전 체인, 스냅샷, 가시성, 가비지 수집 — 정리 (힌트)

## 해결하는 문제

락만 쓰는 동시성 제어(15번)에서는 읽기와 쓰기가 서로를 막는다.

```text
  락만 쓸 때
  T1(보고서):  SELECT sum(bal) FROM account   ── S 락이 필요 ── 쓰는 쪽이 끝날 때까지 대기
  T2(이체):    UPDATE account ... (X 락 보유)
  → 긴 보고서 쿼리 하나가 이체를 막거나, 이체가 보고서를 막는다.
```

- 해법: 값을 덮어쓰지 않고 **새 버전을 하나 더 만든다.** 읽는 쪽은 자기에게 맞는 옛 버전을 읽는다.
  - *MVCC(Multi-Version Concurrency Control)*: 한 논리적 행에 대해 물리 버전 여러 개를 두고, 트랜잭션마다 볼 버전을 고르는 방식.
- 핵심 효과: **쓰는 쪽은 읽는 쪽을 막지 않고, 읽는 쪽은 쓰는 쪽을 막지 않는다**(CMU 15-445 L19). 같은 행을 둘이 쓰면 여전히 서로 막는다.

쉬운 예: 공유 문서의 "버전 기록"이다.
- 내가 읽기 시작한 순간의 판을 계속 본다. 남이 고쳐도 내 화면은 안 바뀐다.
- 고친 사람은 새 판을 만든다. 옛 판은 아무도 안 볼 때 지운다.

똑같은 구조다.\
대신 **옛 판을 언제 지울 수 있나**라는 새 문제가 생긴다. 이것이 PostgreSQL의 `VACUUM`, InnoDB의 purge다.

실무 예:
- PostgreSQL에서 몇 시간 열린 트랜잭션 하나 때문에 `VACUUM`이 죽은 행을 못 지우고 테이블이 계속 커진다.
- MySQL에서 `mysqldump --single-transaction` 중에 `History list length`가 치솟는다.
- PostgreSQL이 `database is not accepting commands that assign new transaction IDs to avoid wraparound data loss`(17판 문구)를 내고 쓰기를 거부한다.

## 동작·원리

### 1. 버전 체인 — 두 엔진의 저장 방식

```text
  PostgreSQL 17: 옛 버전과 새 버전이 같은 힙에 나란히 (append-only, 옛 → 새)
  힙 페이지 0
   lp1  [xmin=1574 xmax=1575 bal=100] ──t_ctid──> lp3
   lp2  [xmin=1574 xmax=0    bal=200]
   lp3  [xmin=1575 xmax=0    bal=110]   ← 새 버전

  MySQL 8.4 InnoDB: 클러스터드 인덱스에는 최신 버전만, 옛 버전은 undo 로그에 (델타, 새 → 옛)
  클러스터드 인덱스 레코드                       undo 로그(rollback segment)
   [id=1 bal=110 DB_TRX_ID=T2 DB_ROLL_PTR] ──> [T2 이전: bal=100, 이전 ROLL_PTR] ──> ...
```

- CMU L19의 분류로 보면
  - PostgreSQL = **append-only 저장**. 갱신할 때마다 새 튜플을 힙에 추가하고, 옛 튜플의 `t_ctid`가 새 튜플을 가리킨다.
  - InnoDB = **델타 저장**. 레코드는 제자리에서 바뀌고, 이전 값을 되살리는 정보가 undo 로그에 쌓인다(MySQL 17.3).
- InnoDB 행에 붙는 숨은 필드(MySQL 17.3)
  - *DB_TRX_ID*(6바이트): 마지막으로 삽입·갱신한 트랜잭션 ID. 삭제도 "삭제 비트를 켠 갱신"으로 처리한다.
  - *DB_ROLL_PTR*(7바이트): 이 행의 이전 모습을 되살리는 undo 레코드를 가리킨다.
- PostgreSQL 튜플 헤더
  - *xmin*: 이 버전을 만든 트랜잭션 ID.
  - *xmax*: 이 버전을 지웠거나(갱신 포함) 잠근 트랜잭션 ID. 0이면 아직 살아 있다.

로컬 재현(예시, PostgreSQL 17.11) — `UPDATE acc SET bal=110 WHERE id=1` 뒤 `pageinspect`로 본 페이지:

```text
   lp | t_xmin | t_xmax | t_ctid | hot_updated | heap_only
  ----+--------+--------+--------+-------------+-----------
    1 |   1574 |   1575 | (0,3)  | t           | f          ← 옛 버전, 1575가 지움
    2 |   1574 |      0 | (0,2)  | f           | f
    3 |   1575 |      0 | (0,3)  | f           | t          ← 새 버전 (HOT)
```

- 보통 `SELECT`에서는 lp1이 안 보인다. 1575가 커밋했으니 지금 스냅샷에는 죽은 버전이다.

### 2. 스냅샷과 가시성 — "누가 쓴 버전을 볼 수 있나"

```text
  PostgreSQL 스냅샷  xmin : xmax : xip_list     예) 100:105:101,103

  XID →   ... 99 | 100  101  102  103  104 | 105 106 ...
               끝남 |  xmin ← 판단 구간 → xmax  | 아직 시작 전 = 안 보임
                    |  101·103 = 진행 중 → 안 보임
                    |  100·102·104 = 끝남 → 커밋이면 보임, 중단이면 안 보임
```

- PostgreSQL 17 스냅샷 구성(9.27 표 9.83)
  - *xmin*: 아직 살아 있는 가장 오래된 트랜잭션 ID. 이보다 작은 ID는 모두 끝났다.
  - *xmax*: 끝난 가장 큰 ID + 1. 이상인 ID는 스냅샷 시점에 안 끝났다 → 안 보임.
  - *xip_list*: 스냅샷 시점에 진행 중이던 ID 목록. 구간 안이라도 여기 있으면 안 보임.
- 한 버전이 보이려면(단순화): 그 버전의 `xmin`이 스냅샷 기준 **커밋 완료**이고, `xmax`는 비었거나 스냅샷 기준 **아직 커밋 전**(또는 중단)이어야 한다.
  - 커밋 여부는 `pg_xact`(트랜잭션당 2비트)에서 확인한다(24.1.5).
- InnoDB도 같은 생각이다. 읽기용 **read view**를 만들고, 레코드의 `DB_TRX_ID`가 안 보이는 트랜잭션이면 `DB_ROLL_PTR`을 따라 undo에서 옛 버전을 복원한다(17.3, 17.7.2.3).

스냅샷을 **언제** 찍는지가 격리 수준을 가른다(14번).

| | 스냅샷 시점 |
|---|---|
| PostgreSQL 17 READ COMMITTED(기본) | 문장마다 새로 |
| PostgreSQL 17 REPEATABLE READ | 트랜잭션의 첫 문장(트랜잭션 제어 문장 제외) 시작 시 한 번 |
| InnoDB READ COMMITTED | 일관된 읽기마다 새로 |
| InnoDB REPEATABLE READ(기본) | 트랜잭션의 첫 일관된 읽기 시 한 번(17.7.2.3) |

### 3. 같은 행을 둘이 쓰면 — 두 엔진이 갈린다

```text
  T1 (REPEATABLE READ)                 T2
  SELECT bal WHERE id=2  → 200
                                       UPDATE bal=bal+50 WHERE id=2; COMMIT   (→ 250)
  UPDATE bal=bal+1 WHERE id=2
     PostgreSQL 17: ERROR  could not serialize access due to concurrent update (40001)
     MySQL 8.4    : 성공. 최신 커밋 값 250에 +1 → 251. 다음 SELECT도 251
```

- 로컬 재현(예시, PostgreSQL 17.11 / MySQL 8.4.10)에서 위 결과 그대로 나왔다.
- PostgreSQL RR은 "먼저 쓴 쪽이 이긴다(first-updater-wins)". 스냅샷 이후 남이 바꾼 행을 고치려 하면 40001로 실패한다. 앱이 재시도해야 한다(13.2.2).
- InnoDB RR의 스냅샷은 `SELECT`에만 적용된다. `UPDATE`·`DELETE`는 최신 커밋 버전을 잠그고 고친다(17.7.2.3 Note). 그래서 읽은 값(200)과 고친 기준(250)이 다를 수 있다.
  - 앱이 "읽은 값 + 1"을 계산해 `SET bal = 201`로 쓰면 T2의 +50이 사라진다(lost update). 18번의 조건부 UPDATE·`FOR UPDATE`가 필요한 이유다.

### 4. 가비지 수집 — PostgreSQL VACUUM

```text
  죽은 버전을 지워도 되는 조건: 그 버전을 볼 수 있는 스냅샷이 하나도 없다
                        ┌────────── 가장 오래된 스냅샷의 xmin = "removable cutoff" ──────────┐
  XID  ─────────────────┼──────────────────────────────────────────────────────────────> 현재
  이보다 전에 죽은 버전 = 지울 수 있음        이후에 죽은 버전 = "dead but not yet removable"
```

- `VACUUM`은 죽은 버전을 지우고 그 자리를 **재사용 가능**으로 표시한다. 파일 크기를 OS에 돌려주지는 않는다. 끝쪽 페이지가 통째로 비었고 배타 락을 쉽게 얻을 때만 예외다(24.1.2).
- `VACUUM FULL`은 테이블을 새로 쓴다. 크기가 줄지만 ACCESS EXCLUSIVE 락이 필요하고, 테이블 크기만큼 디스크가 더 든다.
- autovacuum은 기본 설정에서 `죽은 행 수 > 50 + 0.2 × 행 수`이면 테이블을 청소한다(PostgreSQL 17 기본 `autovacuum_vacuum_threshold`=50, `autovacuum_vacuum_scale_factor`=0.2, 19.10·24.1.6). 삽입 수 기준 트리거(`autovacuum_vacuum_insert_*`)와 wraparound 방지용 강제 실행은 따로 있다.

로컬 재현(예시, PostgreSQL 17.11) — 1만 행 테이블. 세션 A가 REPEATABLE READ로 스냅샷을 연 채 8초 쉬는 동안 세션 B가 전 행을 갱신했다.

```text
  B 직후 VACUUM (VERBOSE):
    tuples: 0 removed, 20000 remain, 10000 are dead but not yet removable
    removable cutoff: 1588, which was 1 XIDs old when operation ended
  A: SELECT sum(v) → 0      (B 커밋 뒤에도 A는 옛 값을 본다. 그래서 옛 버전을 못 지운다)
  A 커밋 뒤 VACUUM:
    tuples: 10000 removed, 10000 remain, 0 are dead but not yet removable
  pg_relation_size: 712 kB → 712 kB   (지웠지만 파일은 그대로 = 재사용할 빈자리)
```

- 오래 열린 트랜잭션 **하나**가 클러스터 전체의 cutoff를 붙잡는다. 이것이 bloat의 가장 흔한 원인이다.
  - *bloat*: 죽은 버전이나 재사용되지 않은 빈자리 때문에 테이블·인덱스가 실제 데이터보다 커진 상태.
- cutoff를 붙잡는 것(24.1.5의 복구 절차가 열거): 오래된 열린 트랜잭션, 오래된 prepared transaction, 오래된 복제 슬롯. 대기 서버의 `hot_standby_feedback=on`(기본 off)도 대기 서버에서 도는 쿼리를 주 서버에 알려 주 서버의 bloat를 부를 수 있다(19.6).

### 5. HOT — 인덱스를 안 건드리는 갱신 (PostgreSQL)

- 조건 두 가지가 맞으면 새 버전이 **같은 페이지**에 들어가고 새 인덱스 항목을 만들지 않는다(65.7).
  - 갱신이 인덱스가 걸린 컬럼(BRIN 같은 요약 인덱스 제외)을 바꾸지 않는다.
  - 옛 버전이 있는 페이지에 새 버전이 들어갈 빈자리가 있다.
- 인덱스는 여전히 lp1을 가리킨다. 같은 페이지 안의 체인(lp1 → lp3)을 따라간다. 중간 버전은 `VACUUM` 없이 평소 `SELECT` 중에도 정리될 수 있다.
- 위 재현의 `hot_updated=t`(옛)·`heap_only=t`(새)가 그 표시다. `fillfactor`를 낮추면 HOT 확률이 오른다.

### 6. 가비지 수집 — InnoDB purge

- undo 로그는 두 종류다(17.3).
  - insert undo: 롤백에만 필요하다. 커밋하면 바로 버린다.
  - update undo: 일관된 읽기에도 쓴다. 그 undo가 필요한 read view가 **하나도 없을 때까지** 버리지 못한다.
- 삭제한 행도 바로 지워지지 않는다. delete-mark만 된다. purge 스레드가 update undo를 처리할 때 행과 인덱스 레코드를 실제로 지운다(17.8.9).
- 아직 purge하지 못한 undo 목록이 **history list**다. 그 길이가 `SHOW ENGINE INNODB STATUS`의 `History list length`다(17.8.9).

로컬 재현(예시, MySQL 8.4.10) — 세션 A가 `START TRANSACTION WITH CONSISTENT SNAPSHOT`으로 read view를 연 채 25초 쉬는 동안, 세션 B가 한 행짜리 UPDATE 2,000개를 자동 커밋으로 돌렸다.

```text
  전      History list length 6       0 read views open inside InnoDB
  중      History list length 2008    1 read views open inside InnoDB
  A 커밋 뒤 History list length 10      0 read views open inside InnoDB
  A의 SELECT sum(v)는 처음과 끝 모두 2000 (B 뒤 실제 값은 4000)
```

## 쓰이는 자료구조·알고리즘

- **버전 체인 = 연결 리스트** — PostgreSQL은 힙 안에서 `t_ctid`로 옛 → 새, InnoDB는 `DB_ROLL_PTR`로 새 → 옛. 찾는 버전이 나올 때까지 따라간다. [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **스냅샷 = 구간 + 진행 중 집합** — `xmin`·`xmax` 두 경계와 `xip_list` 집합으로 "이 ID가 보이나"를 판정한다.
- **영속(persistent) 자료구조와 같은 발상** — 고치지 않고 새 판을 만들어 옛 판을 읽는 쪽을 보호한다. [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)
- **비트맵** — PostgreSQL 가시성 맵(페이지당 all-visible·all-frozen 비트)으로 `VACUUM`이 볼 필요 없는 페이지를 건너뛴다(24.1.4·24.1.5). 커밋 상태는 `pg_xact`에 트랜잭션당 2비트다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **모듈러 비교(원형 공간)** — 32비트 XID를 2^32 모듈로 비교한다. 어느 XID든 앞의 약 20억 개는 과거, 뒤의 약 20억 개는 미래다(24.1.5).

## 적용 — 풀어나가는 법

### 1. 긴 트랜잭션을 찾아 끊는다

```sql
-- PostgreSQL 17: cutoff를 붙잡는 세션
-- 쓰기 트랜잭션은 backend_xid만 있고 backend_xmin이 NULL일 수 있어 둘 다 본다(24.1.5)
SELECT pid, state, backend_xid, backend_xmin,
       greatest(age(backend_xid), age(backend_xmin)) AS xid_age,
       now() - xact_start AS xact_age, left(query, 60)
FROM pg_stat_activity
WHERE backend_xid IS NOT NULL OR backend_xmin IS NOT NULL
ORDER BY xid_age DESC;

SELECT slot_name, active, xmin, catalog_xmin FROM pg_replication_slots;
SELECT gid, prepared, age(transaction) FROM pg_prepared_xacts;

-- 방어선: 트랜잭션 안에서 놀고 있는 세션을 서버가 끊는다 (PostgreSQL 17 기본 0 = 끔)
SET idle_in_transaction_session_timeout = '60s';   -- 예시 값, 역할 단위 ALTER ROLE ... SET 도 가능
```

```sql
-- MySQL 8.4: 오래된 트랜잭션과 history list
SELECT trx_id, trx_started, trx_state, trx_isolation_level, trx_mysql_thread_id
FROM information_schema.INNODB_TRX ORDER BY trx_started;
SELECT count FROM information_schema.INNODB_METRICS WHERE name = 'trx_rseg_history_len';
SHOW ENGINE INNODB STATUS\G   -- TRANSACTIONS 절: History list length, read views
```

- 흔한 범인: 자동 커밋을 끄고 `SELECT`만 한 뒤 커밋을 잊은 세션, 스트리밍 커서를 연 채 느리게 읽는 배치, 트랜잭션 안의 원격 호출(18번), `mysqldump --single-transaction`(17.8.9).
- Spring: 읽기만 하는 긴 `@Transactional` 메서드도 스냅샷을 붙잡을 수 있다. MySQL 기본(REPEATABLE READ)·PostgreSQL REPEATABLE READ는 첫 읽기 스냅샷을 커밋까지 쥔다. PostgreSQL 기본(READ COMMITTED)은 문장이 끝나면 스냅샷을 놓지만, 그 트랜잭션이 이미 쓰기를 했다면 자기 XID(`backend_xid`)가 cutoff를 붙잡는다. 트랜잭션 범위를 짧게 한다([24번](../24-transaction-boundaries-in-app-code/2-summary.md)).
  - 로컬 재현(예시, PostgreSQL 17.11): `idle in transaction` 상태에서 READ COMMITTED 읽기 전용 세션은 `backend_xmin` NULL, REPEATABLE READ 세션은 값이 남았다. INSERT한 세션은 `backend_xid`만 있고 `backend_xmin`은 NULL이었다.

### 2. bloat와 vacuum 상태를 본다 (PostgreSQL 17)

```sql
SELECT relname, n_live_tup, n_dead_tup, last_autovacuum, n_tup_upd, n_tup_hot_upd
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;

VACUUM (VERBOSE) account;   -- "dead but not yet removable"가 크면 cutoff를 누가 붙잡는지 본다

-- XID 나이: autovacuum_freeze_max_age(기본 2억)에 다가가는지
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;
SELECT oid::regclass, age(relfrozenxid) FROM pg_class WHERE relkind IN ('r','m') ORDER BY 2 DESC LIMIT 10;
```

- 갱신이 잦은 큰 테이블은 테이블 단위로 autovacuum을 더 자주 돌게 한다.

```sql
ALTER TABLE account SET (autovacuum_vacuum_scale_factor = 0.02);  -- 예시 값
```

- 이미 부푼 테이블을 줄이려면 `VACUUM FULL`(ACCESS EXCLUSIVE, 서비스 중단)이다. 무중단이 필요하면 처리 중 배타 락을 쥐지 않는 확장 도구(pg_repack 등)를 검토한다(pg_repack README: "works online, without holding an exclusive lock on the processed tables during processing").

### 3. 쓰기 충돌을 전제로 코드를 짠다

- PostgreSQL REPEATABLE READ·SERIALIZABLE을 쓰면 40001을 **정상 흐름**으로 보고 트랜잭션 전체를 재시도한다(13.5).
- MySQL RR에서 "읽고 계산해서 쓰기"는 보호되지 않는다. `UPDATE ... SET bal = bal + ?`처럼 DB에서 계산하거나 `SELECT ... FOR UPDATE`로 읽는다(18번).

## 장애 시나리오와 대처

### 1. 장기 트랜잭션 → vacuum 불가 → 테이블 bloat

- **현상**: 행 수는 그대로인데 테이블·인덱스 크기가 계속 늘고, 쿼리가 점점 느려진다.
- **보이는 형태**
  - `pg_stat_user_tables.n_dead_tup`이 계속 쌓인다.
  - `VACUUM VERBOSE`에 `N are dead but not yet removable`, `removable cutoff ... which was <큰 수> XIDs old`.
  - `pg_stat_activity`에 `state = idle in transaction`이고 `xact_start`가 몇 시간 전인 세션.
- **원인**: 가장 오래된 스냅샷보다 뒤에 죽은 버전은 누군가 볼 수 있으므로 지우지 못한다. 그 사이 갱신이 계속 새 버전을 만든다.
- **대처**
  - 붙잡은 세션을 끝낸다(`pg_terminate_backend(pid)`). 버려진 복제 슬롯·prepared transaction을 정리한다.
  - `idle_in_transaction_session_timeout`, `statement_timeout`으로 재발을 막는다([22번](../22-database-side-timeouts/2-summary.md)).
  - 이미 커진 크기는 일반 `VACUUM`으로 줄지 않는다(재사용만 된다).

### 2. PostgreSQL XID wraparound 임박 → 쓰기 중단

- **현상**: 모든 INSERT·UPDATE·DELETE가 실패한다. 읽기는 된다.
- **보이는 형태**(PostgreSQL 17 문서 24.1.5의 메시지)
  - 먼저 경고: `WARNING: database "mydb" must be vacuumed within 39985967 transactions` — 남은 XID가 약 4천만일 때부터.
  - 이어서 거부: `ERROR: database is not accepting commands that assign new transaction IDs to avoid wraparound data loss in database "mydb"` — 약 3백만 남았을 때.
  - 이 거부 문구는 PostgreSQL 17판 문구다. 14~16판 문서는 `database is not accepting commands to avoid wraparound data loss in database "mydb"`로 적는다(각 판 24.1.5 대조).
- **원인**
  - XID는 32비트다. 한 행이 약 20억 트랜잭션 넘게 동결(freeze)되지 않으면 "미래"로 보여 사라진다.
  - `VACUUM`이 오래된 행을 동결해 이를 막는다. autovacuum은 `age(relfrozenxid)`가 `autovacuum_freeze_max_age`(기본 2억)를 넘으면 autovacuum을 꺼 둬도 강제로 돈다.
  - 그런데 긴 트랜잭션·버려진 슬롯이 cutoff를 붙잡거나, 거대한 테이블의 동결 작업이 따라잡지 못하면 나이가 계속 오른다.
- **대처**(24.1.5의 순서)
  1. 오래된 prepared transaction을 커밋·롤백한다.
  2. 오래 열린 트랜잭션을 끝낸다.
  3. 오래된 복제 슬롯을 지운다.
  4. 해당 DB에서 `VACUUM`을 돈다. **슈퍼유저로** 돌아야 시스템 카탈로그까지 처리해 `datfrozenxid`가 전진한다. `VACUUM FULL`은 쓰지 않는다. XID가 필요해 실패하고, 슈퍼유저면 실패 대신 XID를 소비해 위험을 키운다. `VACUUM FREEZE`도 필요 이상 일이라 권하지 않는다.
  - 예전처럼 단일 사용자 모드로 내릴 필요는 보통 없고 피하라고 문서가 명시한다. 유일한 예외는 불필요한 테이블을 `TRUNCATE`·`DROP`해 vacuum 대상에서 빼려는 경우다.
- 예방: `age(datfrozenxid)`에 알람을 건다. 최후 수단으로 `age(relfrozenxid)`가 `vacuum_failsafe_age`(PostgreSQL 17 기본 16억)를 넘으면 `VACUUM`이 비용 기반 지연을 끄고 인덱스 vacuum 같은 부가 작업을 건너뛴다(19.11).

### 3. MySQL history list length 폭증 → 전체가 느려진다

- **현상**: 특정 쿼리가 아니라 전반적으로 느려지고, undo 테이블스페이스가 커진다.
- **보이는 형태**: `History list length`가 수만~수백만(평소 수천 이하, 17.8.9). `INNODB_TRX`에 `trx_started`가 오래된 트랜잭션.
- **원인**: 오래된 read view가 update undo의 purge를 막는다. 일관된 읽기는 긴 undo 체인을 따라가야 하고, delete-mark된 행도 물리적으로 남는다.
- **대처**
  - 오래된 트랜잭션을 끝낸다. 백업(`--single-transaction`)은 쓰기가 적은 시간이나 복제본에서 돈다.
  - `innodb_max_purge_lag`(8.4 기본 0 = 제한 없음)를 걸면 purge가 밀릴 때 DML에 지연을 준다. 증상 완화이지 원인 제거가 아니다.

### 4. PostgreSQL RR에서 `could not serialize access due to concurrent update`

- **현상**: 격리 수준을 REPEATABLE READ로 올렸더니 일부 요청이 실패한다.
- **보이는 형태**: SQLSTATE `40001`. Spring 6 기본 JDBC 번역기(`SQLExceptionSubclassTranslator` → `SQLStateSQLExceptionTranslator`)에서는 `CannotAcquireLockException`(부모 `PessimisticLockingFailureException`)이 된다. 사용자 `sql-error-codes.xml`을 두어 구형 `SQLErrorCodeSQLExceptionTranslator`가 쓰이면 `CannotSerializeTransactionException`이다.
- **원인**: 스냅샷 이후 다른 트랜잭션이 커밋한 행을 고치려 했다. PostgreSQL은 옛 스냅샷 기준의 갱신을 허용하지 않는다(13.2.2).
- **대처**: 트랜잭션 전체 재시도. 경합이 심한 행이면 READ COMMITTED + 조건부 UPDATE가 더 맞을 수 있다(17·18번).

## 핵심 문장

- MVCC는 덮어쓰지 않고 새 버전을 만들어, 읽기와 쓰기가 서로를 막지 않게 한다. 같은 행의 쓰기끼리는 여전히 막는다.
- PostgreSQL은 힙에 옛·새 버전을 나란히 두고(xmin·xmax), InnoDB는 최신만 두고 옛 모습을 undo 로그로 되살린다(DB_TRX_ID·DB_ROLL_PTR).
- 스냅샷은 "끝난 트랜잭션 경계 + 진행 중 목록"이다. 스냅샷을 언제 찍느냐가 READ COMMITTED와 REPEATABLE READ를 가른다.
- 옛 버전은 그것을 볼 수 있는 스냅샷이 하나도 없을 때만 지운다. 그래서 긴 트랜잭션 하나가 vacuum·purge를 멈춰 bloat를 만든다.
- 일반 VACUUM은 공간을 재사용 가능하게 할 뿐 파일을 줄이지 않는다.
- PostgreSQL XID는 32비트라 동결이 밀리면 약 3백만 남은 시점부터 새 XID 발급을 거부한다.

## 관련 주제·근거

- 선행
  - database [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md) — 격리 수준과 이상 현상.
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md) — 락 기반 동시성, 쓰기끼리의 충돌
- 후속·연결
  - [17-occ-and-timestamp-ordering](../17-occ-and-timestamp-ordering/2-summary.md) — 검증 기반 동시성과 타임스탬프
  - [18-app-level-concurrency-patterns](../18-app-level-concurrency-patterns/2-summary.md) — RR에서도 막히지 않는 lost update 막기
  - [19-wal-and-logging](../19-wal-and-logging/2-summary.md) — 버전 생성·vacuum도 WAL에 기록된다
  - database [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md), [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md), [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md)(대량 DELETE → bloat), [57-db-incidents](../57-db-incidents/2-summary.md)(Sentry XID wraparound)
  - [languages/sql/syntax/56](../../../languages/sql/syntax/56-isolation-levels-read-phenomena-mvcc/2-summary.md) — 격리 수준·읽기 현상 문법과 재현
  - [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md) · [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md) · [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- 강의
  - CMU 15-445/645 Fall 2024 Lecture #19 Multi-Version Concurrency Control — 쓰기·읽기 비차단, 스냅샷 격리·write skew, 버전 저장 3방식(append-only·time-travel·delta), 체인 방향 O2N·N2O, GC(튜플 단위·트랜잭션 단위), 인덱스 포인터 <https://15445.courses.cs.cmu.edu/fall2024/notes/19-multiversioning.pdf>
- PostgreSQL 17
  - 13.1 Introduction(MVCC), 13.2 Transaction Isolation(스냅샷 시점, 40001), 13.5 Serialization Failure Handling <https://www.postgresql.org/docs/17/mvcc.html>
  - 24.1 Routine Vacuuming — 24.1.2 Recovering Disk Space, 24.1.5 Preventing Transaction ID Wraparound Failures(2^32 모듈로, 4천만 경고·3백만 거부, 복구 절차, pg_xact 2비트) <https://www.postgresql.org/docs/17/routine-vacuuming.html>
  - 19.10 Automatic Vacuuming — `autovacuum_vacuum_threshold` 50, `autovacuum_vacuum_scale_factor` 0.2, `autovacuum_freeze_max_age` 2억 <https://www.postgresql.org/docs/17/runtime-config-autovacuum.html>
  - 19.6 Replication — `hot_standby_feedback`(off, 주 서버 bloat 가능) <https://www.postgresql.org/docs/17/runtime-config-replication.html> · 19.11 `vacuum_failsafe_age`·`idle_in_transaction_session_timeout`
  - 9.27 System Information Functions — 표 9.83 Snapshot Components(xmin·xmax·xip_list) <https://www.postgresql.org/docs/17/functions-info.html>
  - 65.6 Database Page Layout, 65.7 Heap-Only Tuples(HOT) <https://www.postgresql.org/docs/17/storage-hot.html> · F.23 pageinspect
- MySQL 8.4
  - 17.3 InnoDB Multi-Versioning — DB_TRX_ID·DB_ROLL_PTR·DB_ROW_ID, insert/update undo, purge, 보조 인덱스 <https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html>
  - 17.7.2.3 Consistent Nonlocking Reads — 스냅샷 시점, DML은 스냅샷을 따르지 않음 <https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html>
  - 17.8.9 Purge Configuration — history list, `innodb_max_purge_lag`(0), 긴 트랜잭션 예시 <https://dev.mysql.com/doc/refman/8.4/en/innodb-purge-configuration.html> · 17.6.6 Undo Logs
- pg_repack README <https://github.com/reorg/pg_repack> — 온라인 재구성
- Spring Framework 6.2.12 `spring-jdbc` 소스 — `JdbcAccessor`(사용자 `sql-error-codes.xml`이 없으면 `SQLExceptionSubclassTranslator`), `SQLStateSQLExceptionTranslator.indicatesCannotAcquireLock`(40001 → `CannotAcquireLockException`), 구형 `sql-error-codes.xml`의 PostgreSQL 40001 → `cannotSerializeTransactionCodes`
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `pageinspect`로 본 xmin·xmax·t_ctid·HOT 비트, `pg_current_snapshot()`, RR 스냅샷이 붙잡은 `VACUUM VERBOSE`("dead but not yet removable") 전후와 파일 크기, RR 동시 갱신의 PG 40001 vs MySQL 최신 값 갱신, `idle in transaction`의 `backend_xmin`·`backend_xid`(RC 읽기 전용 NULL·RR 유지·쓰기는 xid만), read view가 연 동안 `History list length` 6 → 2008 → 10, PostgreSQL 17 `pg_settings`(`vacuum_failsafe_age` 1600000000, `idle_in_transaction_session_timeout` 0)
