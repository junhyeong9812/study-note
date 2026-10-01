# database/56-db-symptom-index — 증상 사전: SQLSTATE·에러 번호·풀/ORM 메시지·지표 패턴 → 층·원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

데이터베이스 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"긴 트랜잭션이 스냅샷을 붙든다 → VACUUM이 못 치운다 → 테이블이 부푼다"처럼 쓴다.\
장애 현장에서는 반대 방향이 필요하다.\
손에 든 것은 로그 한 줄(`ERROR 1205`), 예외 이름 하나(`CannotAcquireLockException`), 그래프 한 장(`replay_lag` 상승)뿐이다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                          이 노트 (역방향)
  원인 --> 메커니즘 --> 증상                   증상 --> 층 --> 흔한 원인 --> 첫 진단 --> leaf
  "락을 50초 넘게 쥐면 1205, 문장만 롤백"       "1205다. 교착이 아니다. 누가 오래 쥐나부터"
```

쉬운 예: 병원 응급실의 분류(트리아지) 표다.\
"가슴 통증"이라는 한마디로 병을 정하지 않는다. 표가 "먼저 심전도"라고 정해 준다.\
표는 치료하지 않는다. **어디를 먼저 볼지**만 정한다.

똑같은 구조다.\
`ERROR 1205`라면 대기 상대를 찾는 `sys.innodb_lock_waits`로 간다(15번).\
`ERROR 1213`이라면 `LATEST DETECTED DEADLOCK`으로 간다(15번).\
둘 다 Spring에서는 같은 예외 클래스로 보일 수 있다(아래 §2).

실무 예:
- 같은 사건이 층마다 **다른 이름**으로 보인다. DB의 락 대기가 앱에서는 풀 고갈 `Connection is not available`로, 사용자에게는 504로 보인다.
- 이름이 같아도 **제품**이 다르면 뜻이 다르다. `40001`은 PostgreSQL에서 직렬화 실패·복구 충돌이고, MySQL에서는 교착(1213)이며, MySQL Connector/J에서는 락 대기 시간 초과(1205)까지 포함한다.
- 에러가 **없는** 증상이 가장 흔하다. 9시간 밀린 시각, 전날로 넘어간 매출, 백필 뒤 빈 칸이 그렇다.

## 동작·원리

### 0. 증상이 올라오는 길 — 어느 층이 만든 말인가

```text
  +--------------------------------------------------------------------------+
  | 앱 로그         "주문 실패" / HTTP 500·504 (원문을 버리면 여기서 끝)          |
  +--------------------------------------------------------------------------+
  | ORM·프레임워크   Spring DataAccessException 계층, Hibernate 예외, @Transactional |
  +--------------------------------------------------------------------------+
  | 커넥션 풀       HikariCP: Connection is not available, request timed out    |
  +--------------------------------------------------------------------------+
  | 드라이버        JDBC SQLException(getSQLState, getErrorCode), 소켓 타임아웃   |
  +--------------------------------------------------------------------------+
  | DB 엔진         SQLSTATE·에러 번호·서버 로그, pg_stat_*, INNODB STATUS       |
  +--------------------------------------------------------------------------+
  | OS·저장장치      디스크 풀, fsync 지연, OOM kill (os 영역)                    |
  +--------------------------------------------------------------------------+
```

- 아래층 사건이 위층 이름으로 **번역**된다. 번역하면서 정보가 줄어든다.
  - 예: Spring 예외 클래스는 "락 획득 실패"까지만 말한다. 그것이 1205(대기 시간 초과)인지 1213(교착)인지는 원인 예외의 `getErrorCode()`에 남는다.
- 번역하는 층이 **다른 말**을 보태기도 한다.
  - 예: MySQL 서버는 1205를 SQLSTATE `HY000`으로 보낸다. Connector/J는 이를 `40001`로 바꿔 올린다(아래 §2).
- 그래서 색인을 쓰기 전에 두 가지를 확보한다.
  - **원문**: SQLSTATE, 에러 번호, 서버 로그 줄, 예외 체인 전체(`Caused by`까지).
  - **모양**: 즉시 실패인가, 몇십 초 멈춘 뒤 실패인가, 에러 없이 값만 틀렸나. 배포·배치·자정 같은 **시각**과 겹치나.

  - *SQLSTATE*: SQL 표준이 정한 다섯 글자 오류 코드다. 앞 두 글자가 분류(class)다. 예: `23` 무결성 위반, `40` 트랜잭션 롤백, `57` 운영자 개입(PostgreSQL 부록 A).
  - *에러 번호*: 제품 고유 번호다. MySQL의 1205·1213이 그렇다. 같은 SQLSTATE에 여러 번호가 묶인다.

### 1. 에러 코드 사전 — SQLSTATE·에러 번호

PostgreSQL 17 SQLSTATE는 `src/backend/utils/errcodes.txt`에서 이름을 확인했다. MySQL 번호의 SQLSTATE는 각 leaf의 재현 출력과 Connector/J `MysqlErrorNumbers.java` 주석을 따른다.

**락·동시성**

| 코드 · 메시지 | 제품 | 층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|---|
| `1205 (HY000)` `Lock wait timeout exceeded; try restarting transaction` | MySQL | 엔진 | 다른 트랜잭션이 행 락을 `innodb_lock_wait_timeout`(8.4 기본 50초) 넘게 쥠. 트랜잭션 안 원격 호출, 대형 백필, in-doubt XA, 교착 탐지를 끈 교착. 메타데이터 락(DDL 대기)이 `lock_wait_timeout`을 넘겨도 같은 1205다. **행 락 대기는 기본(`innodb_rollback_on_timeout=OFF`)에서 마지막 문장만 롤백** | `sys.innodb_lock_waits`, `information_schema.innodb_trx`의 `trx_started`. DDL이 얽혔으면 `performance_schema.metadata_locks` | [15](../15-two-phase-locking-and-deadlock/2-summary.md) · [13](../13-transactions-acid/2-summary.md) · [18](../18-app-level-concurrency-patterns/2-summary.md) · [34](../34-large-backfill-and-batch-dml/2-summary.md) · [55](../55-distributed-databases/2-summary.md) |
| `1213 (40001)` `Deadlock found when trying to get lock; try restarting transaction` | MySQL | 엔진 | 반대 순서 잠금, next-key·갭 락(없는 행 `FOR UPDATE`), SERIALIZABLE의 공유 락 | `SHOW ENGINE INNODB STATUS`의 `LATEST DETECTED DEADLOCK`, `innodb_print_all_deadlocks` | [15](../15-two-phase-locking-and-deadlock/2-summary.md) · [14](../14-isolation-levels-and-anomalies/2-summary.md) · [18](../18-app-level-concurrency-patterns/2-summary.md) · [28](../28-key-strategy-surrogate-natural-public-id/2-summary.md) |
| `40P01` `deadlock detected` (+ `DETAIL: Process N waits for ...`) | PostgreSQL | 엔진 | 반대 순서 잠금, `ON UPDATE CASCADE` 연쇄. 탐지 전 `deadlock_timeout`만큼 지연 | 서버 로그의 DETAIL(두 쿼리), `pg_locks` | [15](../15-two-phase-locking-and-deadlock/2-summary.md) · [28](../28-key-strategy-surrogate-natural-public-id/2-summary.md) |
| `40001` `could not serialize access due to concurrent update` | PostgreSQL | 엔진 | REPEATABLE READ에서 스냅샷 이후 커밋된 행을 갱신 | 어느 트랜잭션·행이 겹쳤나(재시도 로그) | [16](../16-mvcc/2-summary.md) · [14](../14-isolation-levels-and-anomalies/2-summary.md) |
| `40001` `... due to read/write dependencies among transactions` | PostgreSQL | 엔진 | SERIALIZABLE(SSI)의 위험 구조. 순차 스캔의 테이블 전체 술어 락, 술어 락 승격 | `pg_locks`의 `SIReadLock`, 계획의 `Seq Scan` | [14](../14-isolation-levels-and-anomalies/2-summary.md) |
| `40001` `canceling statement due to conflict with recovery` | PostgreSQL 대기 서버 | 엔진(복제) | 팔로워의 긴 조회가 리더의 vacuum 기록 재생과 충돌. `max_standby_streaming_delay`(30초) 초과 | 오류 DETAIL(충돌 사유), `pg_stat_database_conflicts` | [32](../32-replication-leader-follower/2-summary.md) |
| `40001` `ReadWithinUncertaintyIntervalError` | CockroachDB | 엔진(분산) | 노드 간 시계 오차 안의 쓰기를 만남, 핫 키 경합 | 시계 오프셋 지표, 키별 재시도 수 | [55](../55-distributed-databases/2-summary.md) |
| `55P03` `canceling statement due to lock timeout` / `could not obtain lock` | PostgreSQL | 엔진 | `lock_timeout`·`NOWAIT`가 제 역할을 함. `REQUIRES_NEW`가 바깥 트랜잭션이 쥔 행을 기다림 | `pg_blocking_pids(pid)` | [22](../22-database-side-timeouts/2-summary.md) · [24](../24-transaction-boundaries-in-app-code/2-summary.md) · [15](../15-two-phase-locking-and-deadlock/2-summary.md) |
| `Waiting for table metadata lock` (PROCESSLIST 상태) | MySQL | 엔진 | DDL이 앞의 긴 트랜잭션 뒤에서 대기, 뒤의 조회가 DDL 뒤에 줄 섬 | `SHOW PROCESSLIST`, `performance_schema.metadata_locks` | [26](../26-schema-migration/2-summary.md) · [22](../22-database-side-timeouts/2-summary.md) |

- `40001` 한 코드에 원인이 넷 이상 겹친다. **메시지와 제품**을 같이 읽어야 한다.
- `55P03`의 메시지는 `lock_timeout`일 때(`canceling statement due to lock timeout`)와 `NOWAIT`일 때(`could not obtain lock on row in relation "…"`)가 다르다. 두 경우 모두 SQLSTATE는 `55P03`이다(REL_17_STABLE `tcop/postgres.c`·`access/heap/heapam.c`, 로컬 재현 PostgreSQL 17.11).

**타임아웃·취소·연결**

| 코드 · 메시지 | 제품 | 층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|---|
| `57014` `canceling statement due to statement timeout` | PostgreSQL | 엔진 | 한도가 제 역할을 함. 쿼리가 느려진 이유(플랜 급변·통계·인덱스 누락·재귀 CTE 순환)를 찾을 차례 | `EXPLAIN (ANALYZE, BUFFERS)`, `pg_stat_statements` | [22](../22-database-side-timeouts/2-summary.md) · [05](../05-window-functions-and-cte/2-summary.md) · [12](../12-query-optimizer-and-explain/2-summary.md) |
| `57014` `canceling statement due to user request` | PostgreSQL | 드라이버→엔진 | 드라이버의 쿼리 타임아웃(취소 요청)·`pg_cancel_backend` | 앱의 쿼리 타임아웃 설정, 누가 취소했나 | [22](../22-database-side-timeouts/2-summary.md) |
| `25P03` `terminating connection due to idle-in-transaction timeout` | PostgreSQL | 엔진 | 트랜잭션 안 외부 호출·사용자 대기, 예외 경로의 커밋·롤백 누락 | 앱 쪽 트랜잭션 경계 | [22](../22-database-side-timeouts/2-summary.md) · [24](../24-transaction-boundaries-in-app-code/2-summary.md) |
| `25P02` `current transaction is aborted, commands ignored until end of transaction block` | PostgreSQL | 엔진(앱 원인) | 첫 오류(23505 등)를 앱이 삼키고 같은 트랜잭션에서 계속 쿼리 | 로그에서 **첫** 오류를 찾는다 | [13](../13-transactions-acid/2-summary.md) · [18](../18-app-level-concurrency-patterns/2-summary.md) |
| `53300` `FATAL: sorry, too many clients already` | PostgreSQL | 엔진 | 인스턴스 수 × 풀 크기 + 도구 커넥션 > `max_connections`. 배포 중 신구 인스턴스 겹침, 캐시 눈사태 | `SELECT count(*) FROM pg_stat_activity` + `max_connections` | [21](../21-connection-pooling/2-summary.md) · [30](../30-caching-with-databases/2-summary.md) |
| `1040 (08004)` `Too many connections` | MySQL | 엔진 | 위와 같음 | `SHOW GLOBAL STATUS LIKE 'Threads_connected'`, `max_connections` | [21](../21-connection-pooling/2-summary.md) · [30](../30-caching-with-databases/2-summary.md) |
| `57P03` `the database system is in recovery mode` | PostgreSQL | 엔진 | 크래시 뒤 재실행(redo) 중. 체크포인트 간격이 길수록 오래 걸림 | 서버 로그 `redo starts at` / `redo done` | [42](../42-recovery-aries-checkpoints/2-summary.md) |
| `08006` `An I/O error occurred while sending to the backend` / `SocketTimeoutException: Read timed out` | pgJDBC | 드라이버 | 중간 장비·서버가 먼저 끊은 커넥션 재사용, 드라이버 소켓 타임아웃 | HikariCP `maxLifetime` vs 경로상 idle 한도, DB의 같은 쿼리가 아직 `active`인가 | [21](../21-connection-pooling/2-summary.md) · [22](../22-database-side-timeouts/2-summary.md) |
| `08S01` `Communications link failure` | Connector/J | 드라이버 | 위와 같음. MySQL `wait_timeout`(8.4 기본 28800초) | 위와 같음 | [21](../21-connection-pooling/2-summary.md) · [22](../22-database-side-timeouts/2-summary.md) |

**무결성·스키마·데이터 형식**

| 코드 · 메시지 | 제품 | 층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|---|
| `23505` `duplicate key value violates unique constraint` | PostgreSQL | 엔진 | 동시 check-then-insert를 UNIQUE가 막음(정상 방어), 소프트 삭제 행과 재가입 충돌, RLS가 숨긴 다른 테넌트 행 | 제약 이름, 충돌 행 조회 | [02](../02-keys-and-constraints/2-summary.md) · [18](../18-app-level-concurrency-patterns/2-summary.md) · [29](../29-soft-delete-and-data-lifecycle/2-summary.md) · [43](../43-row-level-security/2-summary.md) |
| `1062 (23000)` `Duplicate entry '…' for key '…'` | MySQL | 엔진 | 위와 같음 + **`_ai_ci` collation이 대소문자·악센트 다른 값을 같다고 봄** | 컬럼 collation(`SHOW FULL COLUMNS`) | [10](../10-collation-and-text-comparison/2-summary.md) · [29](../29-soft-delete-and-data-lifecycle/2-summary.md) |
| `23503` / `1451`·`1452` FK 위반 | PG / MySQL | 엔진 | 소프트 삭제 부모를 하드 삭제, 자연키 변경에 CASCADE 없음 | 참조하는 자식 조회 | [28](../28-key-strategy-surrogate-natural-public-id/2-summary.md) · [29](../29-soft-delete-and-data-lifecycle/2-summary.md) |
| `22P02` `invalid input syntax for type …` | PostgreSQL | 엔진 | JSON 필드에 다른 타입 값 섞임, RLS 설정이 빈 문자열 `''` | 실패한 값, `current_setting(…)` | [36](../36-data-models-document-graph/2-summary.md) · [43](../43-row-level-security/2-summary.md) |
| `42703` `column … does not exist` / `1054 (42S22)` `Unknown column` | PG / MySQL | 엔진(배포 원인) | 컬럼 rename·drop 뒤 구버전 코드로 롤백 | 마이그레이션 이력 vs 실행 중 코드 버전 | [26](../26-schema-migration/2-summary.md) |
| `1055 (42000)` `… incompatible with sql_mode=only_full_group_by` | MySQL | 엔진 | GROUP BY에 없는 비집계 열 | 해당 쿼리 | [04](../04-sql-joins-and-aggregation/2-summary.md) |
| `1267 (HY000)` `Illegal mix of collations` | MySQL | 엔진 | 조인 키 컬럼의 collation이 다름 | 두 컬럼의 collation | [10](../10-collation-and-text-comparison/2-summary.md) |
| `1292 (22007)` `Incorrect datetime value` / `1298` `Unknown or incorrect time zone` | MySQL | 엔진 | `TIMESTAMP` 2038 상한 / 시간대 테이블 비어 있음 | 값 범위 / `mysql.time_zone_name` | [27](../27-temporal-types-and-session-timezone/2-summary.md) |
| `1118 (42000)` `Row size too large (> 8126)` | MySQL | 엔진 | 고정 길이 컬럼이 많아 페이지 밖으로 뺄 것이 없음 | 테이블 정의 | [06](../06-pages-and-tuple-layout/2-summary.md) |
| `4092` `Maximum row versions reached` | MySQL | 엔진 | INSTANT ADD/DROP 누적(8.4 상한 64) | `INNODB_TABLES.TOTAL_ROW_VERSIONS` | [26](../26-schema-migration/2-summary.md) |
| `1526 (HY000)` `Table has no partition for value …` / `no partition of relation … found for row` | MySQL / PG | 엔진 | 미래 파티션을 미리 만들지 않음 | 파티션 목록, 생성 잡 상태 | [33](../33-partitioning-and-sharding/2-summary.md) · [44](../44-timeseries-resolution-tiers/2-summary.md) |
| `invalid byte sequence for encoding "UTF8"` / `1300 (HY000)` `Invalid utf8mb4 character string` | PG / MySQL | 엔진(입력) | CP949 파일을 UTF-8로 적재 | 파일 앞 바이트(`xxd`) | [35](../35-bulk-file-import-export/2-summary.md) |
| `3636` `Recursive query aborted after 1001 iterations` / `1406 (22001)` `Data too long` | MySQL | 엔진 | 재귀 CTE 순환 / 비재귀 항이 열 폭을 고정 | 데이터의 순환, 비재귀 항 타입 | [05](../05-window-functions-and-cte/2-summary.md) |

**자원·디스크·내구성**

| 코드 · 메시지 | 제품 | 층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|---|
| `database is not accepting commands that assign new transaction IDs to avoid wraparound data loss` (앞서 `WARNING: … must be vacuumed within N transactions`) | PostgreSQL 17 문구(14~16은 `database is not accepting commands to avoid wraparound data loss`) | 엔진 | 동결이 따라가지 못함: 긴 트랜잭션, 버려진 복제 슬롯, prepared transaction, 거대 테이블 | `SELECT datname, age(datfrozenxid) FROM pg_database` | [16](../16-mvcc/2-summary.md) · [57](../57-db-incidents/2-summary.md) |
| `PANIC: could not write to log file … No space left on device` | PostgreSQL | 엔진(디스크) | WAL 디스크 풀: 비활성 복제·CDC 슬롯, `archive_command` 연속 실패 | `pg_replication_slots`의 `active`·보존량, `pg_stat_archiver` | [19](../19-wal-and-logging/2-summary.md) · [32](../32-replication-leader-follower/2-summary.md) · [48](../48-search-index-sync-and-reindexing/2-summary.md) |
| `53400` (`temp_file_limit` 초과) · `could not write to file "…": No space left on device` | PostgreSQL | 엔진 | 거대 정렬·해시의 임시 파일 | `pg_stat_database.temp_bytes`, `log_temp_files` | [41](../41-sorting-and-aggregation/2-summary.md) |
| `server process (PID …) was terminated by signal 9: Killed` | PostgreSQL 서버 로그 | OS→엔진 | `work_mem` 전역 상향·버퍼 풀 과대로 OOM kill | 커널 로그 OOM, 동시 세션 수 × 노드 수 | [41](../41-sorting-and-aggregation/2-summary.md) · [07](../07-buffer-pool/2-summary.md) |
| `[MY-014084] … unable to reserve space in redo log … Consider increasing innodb_redo_log_capacity` | MySQL 에러 로그(8.4.6+) | 엔진 | 대량 쓰기에 redo 용량 부족, 체크포인트가 못 따라옴 | `innodb_redo_log_capacity` | [42](../42-recovery-aries-checkpoints/2-summary.md) |
| `DB::Exception: Too many parts (N with average size of …) in table '…'. Merges are processing significantly slower than inserts` | ClickHouse | 엔진 | 작은 동기 INSERT 폭주, 너무 잘게 나눈 파티션 키, 멈춘 병합 | `system.parts`의 파티션별 활성 파트 수, `system.merges`, `system.mutations` | [45](../45-clickhouse-mergetree/2-summary.md) · [37](../37-row-vs-column-storage/2-summary.md) |
| `Stalling writes because we have 20 level-0 files` / `Stopping writes …` | RocksDB LOG | 엔진 | compaction 적체 | `rocksdb.stats`의 stall 시간 | [38](../38-lsm-storage-engine/2-summary.md) |

### 2. Java·Spring에서 보이는 이름 — 번역은 경로마다 다르다

```text
  DB 엔진 ──SQLSTATE·번호──▶ 드라이버 ──SQLException(서브클래스)──▶ Spring 번역기 ──▶ DataAccessException
                               ▲                                        ▲
                     Connector/J는 HY000을                    어느 번역기인지가
                     자기 표로 바꾼다(1205→40001)               Spring 6.x 기본에서 바뀌었다
```

**Spring 6.x JDBC 번역기 선택** (spring-framework 6.2.x 소스 `JdbcAccessor.getExceptionTranslator()`)
- classpath 루트에 **사용자가 만든** `sql-error-codes.xml`이 있으면 `SQLErrorCodeSQLExceptionTranslator`(에러 코드 표)를 쓴다.
- 없으면 `SQLExceptionSubclassTranslator`(JDBC 예외 서브클래스)를 쓰고, 거기서 못 정하면 `SQLStateSQLExceptionTranslator`(SQLSTATE 앞 두 글자)로 넘긴다.
- JPA·Hibernate 경로는 이 번역기가 아니라 Hibernate 예외를 Spring 예외로 바꾸는 별도 경로를 탄다. 이 노트는 그 경로의 매핑을 소스로 확인하지 않았다 [?].

| 원문 | 에러 코드 표 경로(`sql-error-codes.xml`) | 기본 경로(서브클래스 → SQLSTATE) | leaf에 적힌 이름 |
|---|---|---|---|
| MySQL 1205 | `CannotAcquireLockException` | Connector/J가 SQLSTATE를 `40001`로 바꾸고(`NativeProtocol`: 서버 상태가 `HY000`이면 자기 표로 대체, `MysqlErrorNumbers` 주석 "Overrides HY000 due to Bug#16634180") `40`으로 시작하므로 `SQLTransactionRollbackException` 계열로 던진다 → `40001`이라 `CannotAcquireLockException` | 15: `CannotAcquireLockException` |
| MySQL 1213 | `DeadlockLoserDataAccessException`(6.0.3부터 deprecated) | `40001` → `CannotAcquireLockException` | 15: `PessimisticLockingFailureException` 계열 |
| PostgreSQL 40001 | `CannotSerializeTransactionException`(deprecated) | pgJDBC `PSQLException`은 `SQLException`을 바로 상속 → SQLSTATE 경로 → `CannotAcquireLockException` | 16: `CannotSerializeTransactionException` |
| PostgreSQL 40P01 | `DeadlockLoserDataAccessException` | `40` 분류 → `PessimisticLockingFailureException` | 15 |
| PostgreSQL 55P03 | `CannotAcquireLockException` | `55` 분류는 SQLSTATE 표에 없다 → 번역기가 `null`을 돌려주고 `JdbcTemplate`이 `UncategorizedSQLException`으로 감싼다(소스 확인) | — |
| PostgreSQL 57014 | 표에 없음 → 폴백(서브클래스 → SQLSTATE) → 기본 경로와 같음 | Spring 6.2.9+: `QueryTimeoutException`. 6.2.8 이하: `57` 분류라 `DataAccessResourceFailureException` | — |
| 23505 / MySQL 1062 | `DuplicateKeyException` | `DuplicateKeyException`(23505, 또는 23000 + 1062) | 02·10 |
| 23503 / 1451·1452 | `DataIntegrityViolationException` | `23` 분류 → `DataIntegrityViolationException` | — |
| PostgreSQL 53300 | `DataAccessResourceFailureException` | `53` 분류 → 같음 | — |
| HikariCP 풀 대기 초과 | — | `DataSourceTransactionManager`면 트랜잭션 시작 시 `CannotCreateTransactionException: Could not open JDBC Connection for transaction`(`JpaTransactionManager`면 `Could not open JPA EntityManager for transaction`) | 21·24 |

- 두 경로 모두 1205·1213·40001·40P01은 부모 `PessimisticLockingFailureException` 아래에 있다. **그래서 예외 클래스로는 1205와 1213을 가를 수 없다.** 원인 예외의 `getErrorCode()`(1205 / 1213)를 로그에 남긴다.
- MySQL은 `getSQLState()`로도 가를 수 없다. Connector/J에서 1205와 1213이 둘 다 `40001`이기 때문이다(위 소스). mysql 명령행 클라이언트는 서버 값을 그대로 보여 주므로 `ERROR 1205 (HY000)`이다. 같은 오류가 도구에 따라 다른 SQLSTATE로 보인다.
- 이 표의 기본 경로 칸은 소스 읽기(spring-jdbc 6.2.x `JdbcAccessor`·`SQLExceptionSubclassTranslator`·`SQLStateSQLExceptionTranslator`, Connector/J release/9.x `NativeProtocol.checkErrorMessage`·`MysqlErrorNumbers`·`SQLError.createSQLException`)로 정리했다. JVM에서 실행해 확인하지 않았다.

**풀·ORM·Spring 메시지**

| 보이는 줄 | 층 | 뜻 · 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| `HikariPool-1 - Connection is not available, request timed out after 30000ms (total=10, active=10, idle=0, waiting=37)` | 풀 | 풀 고갈. 커넥션을 오래 쥠(느린 쿼리·락 대기·트랜잭션 안 HTTP·반납 누락), 풀 교착(`REQUIRES_NEW`), 캐시 스탬피드 | DB의 `pg_stat_activity`에서 오래된 `active`·`idle in transaction`, 스레드 덤프의 `getConnection` | [21](../21-connection-pooling/2-summary.md) · [22](../22-database-side-timeouts/2-summary.md) · [24](../24-transaction-boundaries-in-app-code/2-summary.md) · [30](../30-caching-with-databases/2-summary.md) |
| `Failed to validate connection … Possibly consider using a shorter maxLifetime value.` | 풀 | 중간 장비·서버가 먼저 끊은 커넥션 | `maxLifetime` vs 경로상 idle 한도 | [21](../21-connection-pooling/2-summary.md) |
| `LazyInitializationException: … could not initialize proxy - no Session` | ORM | 트랜잭션 밖에서 지연 연관 접근. `@Transactional` 자기 호출로 트랜잭션이 없었을 수도 | 트랜잭션 DEBUG 로그 | [23](../23-orm-and-n-plus-one/2-summary.md) · [24](../24-transaction-boundaries-in-app-code/2-summary.md) |
| `HHH90003004: firstResult/maxResults specified with collection fetch; applying in memory` | ORM | 컬렉션 fetch join + 페이징 → 전부 읽고 메모리에서 자름 | 생성 SQL에 LIMIT이 있나 | [23](../23-orm-and-n-plus-one/2-summary.md) |
| `ObjectOptimisticLockingFailureException` / `StaleObjectStateException: Row was updated or deleted by another transaction` | ORM | 낙관적 락 충돌. 핫 행이면 재시도 폭증 | 충돌 비율, 같은 행 동시 쓰기 수 | [17](../17-occ-and-timestamp-ordering/2-summary.md) · [52](../52-offline-concurrency-patterns/2-summary.md) |
| `UnexpectedRollbackException: Transaction rolled back because it has been marked as rollback-only` | Spring | 안쪽 `REQUIRED`가 실패 표시를 남긴 트랜잭션을 바깥이 커밋하려 함 | DEBUG 로그의 `Global transaction is marked as rollback-only` | [24](../24-transaction-boundaries-in-app-code/2-summary.md) |
| `SerializationException: Cannot deserialize` + `InvalidClassException: … serialVersionUID` / `UnrecognizedPropertyException` | 앱(캐시) | 배포 직후 값 형식이 바뀌었는데 캐시 키는 그대로 | 신·구 인스턴스별 오류율, 캐시 키 버전 | [31](../31-cache-key-versioning-and-serialization/2-summary.md) · [30](../30-caching-with-databases/2-summary.md) |
| `NonUniqueResultException` / `IncorrectResultSizeDataAccessException` | ORM | 유일해야 할 행이 둘: UNIQUE 없는 check-then-insert, 기간 겹침 | `GROUP BY … HAVING count(*) > 1` | [02](../02-keys-and-constraints/2-summary.md) · [18](../18-app-level-concurrency-patterns/2-summary.md) · [50](../50-temporal-and-bitemporal-tables/2-summary.md) |

### 3. 지표·로그 패턴 사전 — 에러는 없는데 숫자가 이상하다

| 패턴 | 먼저 의심 | 첫 진단 | leaf |
|---|---|---|---|
| 행 수는 그대로인데 테이블·인덱스 크기 증가(bloat) | 긴 트랜잭션·`idle in transaction`이 스냅샷을 붙듦, autovacuum이 못 따라감. 일반 VACUUM은 보통 파일을 줄이지 않는다(테이블 끝의 완전히 빈 페이지만 잘라낼 수 있다) | `pg_stat_user_tables.n_dead_tup`·`last_autovacuum`, `VACUUM VERBOSE`의 `dead but not yet removable`, `pg_stat_activity`의 `xact_start` | [16](../16-mvcc/2-summary.md) · [06](../06-pages-and-tuple-layout/2-summary.md) · [34](../34-large-backfill-and-batch-dml/2-summary.md) · [22](../22-database-side-timeouts/2-summary.md) |
| `History list length` 수만~수백만, undo 증가 | MySQL의 bloat 짝: 오래된 read view가 purge를 막음 | `SHOW ENGINE INNODB STATUS`, `innodb_trx` | [16](../16-mvcc/2-summary.md) · [34](../34-large-backfill-and-batch-dml/2-summary.md) |
| `replay_lag`·`Seconds_Behind_Source` 상승, "방금 쓴 게 안 보임" | 대량 DML·백필(MySQL은 거대 트랜잭션이 커밋 뒤 한꺼번에 전달), 팔로워의 긴 조회, 적용 병렬도 | `pg_stat_replication`, `SHOW REPLICA STATUS` | [32](../32-replication-leader-follower/2-summary.md) · [26](../26-schema-migration/2-summary.md) · [34](../34-large-backfill-and-batch-dml/2-summary.md) |
| 리더 커밋이 에러 없이 멈춤, `wait_event = SyncRep` | 동기 팔로워 하나가 죽음 | `synchronous_standby_names`, `pg_stat_replication` | [32](../32-replication-leader-follower/2-summary.md) |
| `pg_wal` 디렉터리 계속 증가 | `active = f`인 복제·CDC 슬롯, 아카이브 실패 | `pg_replication_slots` 보존량, `pg_stat_archiver.failed_count` | [32](../32-replication-leader-follower/2-summary.md) · [48](../48-search-index-sync-and-reindexing/2-summary.md) · [19](../19-wal-and-logging/2-summary.md) · [20](../20-backup-and-pitr/2-summary.md) |
| 코드 변경 없이 한 쿼리가 수십 배 느려짐(플랜 급변) | 배치 뒤 통계 오래됨, 상관 컬럼 독립 가정, 준비된 문장의 일반 계획(6번째 실행부터), GEQO(FROM 항목 12개+) | `EXPLAIN ANALYZE`의 `rows=` vs `actual rows=`, `pg_stat_statements`를 주기적으로 떠 둔 구간별 `total_exec_time`·`calls` 차이(뷰 자체는 누적값만 가진다) | [12](../12-query-optimizer-and-explain/2-summary.md) · [11](../11-join-algorithms/2-summary.md) |
| `Sort Method: external merge Disk:`, `Batches:` > 1, `temp_bytes` 증가(스필) | `work_mem` 초과. 단 스필이 병목인지 먼저 확인 | `SET LOCAL work_mem` 올려 재측정, `log_temp_files` | [41](../41-sorting-and-aggregation/2-summary.md) · [11](../11-join-algorithms/2-summary.md) |
| MySQL `Created_tmp_disk_tables` 증가(`Using temporary`는 임시 테이블을 쓴다는 뜻일 뿐 디스크 여부는 아님) | 내부 임시 테이블이 `tmp_table_size` 또는 전역 한도 `temptable_max_ram`을 넘어 디스크(InnoDB)로 전환 | `EXPLAIN ANALYZE`, `Created_tmp_tables` 대비 `Created_tmp_disk_tables`. `memory/temptable/physical_disk`는 메모리 매핑 파일 오버플로를 켠 경우(8.4 기본 `temptable_use_mmap=OFF`)에만 의미 | [41](../41-sorting-and-aggregation/2-summary.md) |
| `checkpoints are occurring too frequently` | `max_wal_size`가 부하에 비해 작음 | `pg_stat_checkpointer`의 `num_requested` vs `num_timed` | [42](../42-recovery-aries-checkpoints/2-summary.md) · [07](../07-buffer-pool/2-summary.md) |
| 쓰기 p99 일제히 상승, `wait_event = WalSync` | 저장장치 fsync 지연 | `pg_stat_wal`(`track_wal_io_timing`) | [19](../19-wal-and-logging/2-summary.md) |
| 배치·덤프 뒤 OLTP 느림, 적중률 하락 | 대형 스캔의 버퍼 풀 오염, 재시작 뒤 차가운 캐시 | `blks_read`, InnoDB `Pages made young` | [07](../07-buffer-pool/2-summary.md) · [37](../37-row-vs-column-storage/2-summary.md) |
| `pg_locks`는 비었는데 `wait_event_type = LWLock` | 락이 아니라 래치 경합(단조 증가 키의 오른쪽 리프) | `pg_stat_activity`의 `wait_event` 표본 | [53](../53-index-concurrency-control/2-summary.md) |
| `pg_stat_statements`에서 짧은 쿼리 `calls` 폭증, 슬로 로그는 조용 | N+1 | `show_sql`, 요청당 쿼리 수 | [23](../23-orm-and-n-plus-one/2-summary.md) |
| `Workers Planned: 2`, `Workers Launched: 0` | 병렬 작업자 상한 소진 | `max_parallel_workers` | [54](../54-query-execution-models/2-summary.md) |
| 캐시 miss 급증과 같은 시각에 DB 동시 쿼리 수백 개 | 스탬피드·눈사태·배포 뒤 캐시 비움 | 캐시 히트율과 DB QPS를 한 그래프에 | [30](../30-caching-with-databases/2-summary.md) · [31](../31-cache-key-versioning-and-serialization/2-summary.md) · [49](../49-multi-level-caching/2-summary.md) |

### 4. 조용한 실패 사전 — 에러도 경보도 없는 증상

| 증상 | 흔한 원인 | 첫 확인 | leaf |
|---|---|---|---|
| 저장된 시각이 9시간 밀림(새 데이터만) | JVM·드라이버·DB 세션 시간대 불일치. 예: Connector/J `connectionTimeZone=LOCAL` 가정 | 같은 행을 `UTC`·`Asia/Seoul` 세션에서 조회, `@@session.time_zone`, `SHOW TimeZone` | [27](../27-temporal-types-and-session-timezone/2-summary.md) |
| 일별 매출이 전날로 넘어감 | UTC 세션에서 `date_trunc('day', …)`·`DATE(…)`. 차이는 매일 00:00~08:59 KST | 쿼리의 "누구의 하루" | [27](../27-temporal-types-and-session-timezone/2-summary.md) |
| collation 때문에 UNIQUE 위반(또는 이관 뒤 중복 허용) | MySQL 8.4 기본 `utf8mb4_0900_ai_ci`는 대소문자·악센트 무시, PostgreSQL 기본은 구분 | `GROUP BY lower(email) HAVING count(*) > 1` | [10](../10-collation-and-text-comparison/2-summary.md) |
| glibc 업그레이드 뒤 있는 행이 안 찾힘 | 텍스트 B-tree가 옛 정렬 순서 | `collation … has version mismatch` 경고, `amcheck` | [10](../10-collation-and-text-comparison/2-summary.md) |
| 백필 잡 "완료"인데 행 누락 | 처리하면 대상에서 빠지는 조건 위에 OFFSET 청크 | 잡 끝의 대상 조건 재계수 | [34](../34-large-backfill-and-batch-dml/2-summary.md) |
| 백필 재실행 뒤 값이 두 배 | 비멱등 변환 + 체크포인트 없음 | 값 분포 | [34](../34-large-backfill-and-batch-dml/2-summary.md) |
| `@Transactional`이 무시됨(앞 INSERT가 남음) | 자기 호출·private 메서드로 프록시를 안 거침 | 트랜잭션 DEBUG 로그에 생성 줄이 있나, `isActualTransactionActive()` | [24](../24-transaction-boundaries-in-app-code/2-summary.md) · [13](../13-transactions-acid/2-summary.md) |
| checked 예외인데 반쯤 커밋 | Spring 기본 롤백 규칙은 RuntimeException·Error만 | `rollbackFor` | [24](../24-transaction-boundaries-in-app-code/2-summary.md) |
| MySQL에서 오류 뒤 커밋 → 반쪽 반영 | 문장 단위로만 롤백하는 오류(기본 설정의 1205, 중복 키 등)에서 앱이 예외를 삼키고 커밋. 1213 교착은 트랜잭션 전체를 롤백한다 | 예외 경로의 `ROLLBACK` | [13](../13-transactions-acid/2-summary.md) · [15](../15-two-phase-locking-and-deadlock/2-summary.md) |
| 합계가 몇 배 부풂 | 일 대 다 조인 팬아웃 | `count(*)` vs `count(DISTINCT …)` | [04](../04-sql-joins-and-aggregation/2-summary.md) · [11](../11-join-algorithms/2-summary.md) |
| 발송 대상이 0명 | `NOT IN` 서브쿼리에 NULL 한 줄 | `NOT EXISTS`로 비교 | [04](../04-sql-joins-and-aggregation/2-summary.md) |
| 재고 음수·lost update | 읽고-계산-쓰기, MySQL REPEATABLE READ도 막지 않음 | 대사 쿼리 | [14](../14-isolation-levels-and-anomalies/2-summary.md) · [17](../17-occ-and-timestamp-ordering/2-summary.md) · [18](../18-app-level-concurrency-patterns/2-summary.md) |
| 규칙("최소 1명")이 깨짐 | write skew(SI는 막지 않음) | 동시성 테스트 | [14](../14-isolation-levels-and-anomalies/2-summary.md) |
| 다른 테넌트 데이터가 보임 | RLS 누락·소유자 롤·풀에 남은 세션 변수, 캐시 키에 테넌트 누락 | `relrowsecurity`, 캐시 키 | [43](../43-row-level-security/2-summary.md) · [31](../31-cache-key-versioning-and-serialization/2-summary.md) |
| 정전 뒤 "커밋 완료" 주문이 없음 | `synchronous_commit=off`, `innodb_flush_log_at_trx_commit` 0·2, 거짓 쓰기 캐시 | 설정값, 저장장치 캐시 | [13](../13-transactions-acid/2-summary.md) · [19](../19-wal-and-logging/2-summary.md) · [42](../42-recovery-aries-checkpoints/2-summary.md) |
| 페일오버 뒤 "성공" 쓰기가 사라짐 | 비동기 복제 | 옛 리더 binlog·GTID와 새 리더 비교 | [32](../32-replication-leader-follower/2-summary.md) · [57](../57-db-incidents/2-summary.md) |
| 백업이 있다고 믿었는데 비어 있음 | 결과가 아니라 작업만 확인, 실패 알림 경로가 막힘 | 마지막 **복원** 성공 시각 | [20](../20-backup-and-pitr/2-summary.md) · [57](../57-db-incidents/2-summary.md) |
| ClickHouse `ReplacingMergeTree`에 중복 | 중복 제거는 병합 때만 | `FINAL`로 비교 | [45](../45-clickhouse-mergetree/2-summary.md) |
| 검색에 삭제된 상품이 계속 노출 | 이중 쓰기의 검색 쪽 실패, 폴링 커서가 늦은 커밋을 건너뜀 | DB와 색인 대조 | [48](../48-search-index-sync-and-reindexing/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **역색인(inverted index)** — 이 노트 자체다. 정방향 "leaf → 증상 목록"을 뒤집어 "증상 → leaf 목록"으로 만든다. 46번 전문 검색의 역색인과 같은 구조다. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- **해시 맵** — 코드(`1205`, `40P01`)를 키로 후보 목록을 찾는다. 로그 수집기의 "코드별 집계"도 같다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **접두사 분류** — SQLSTATE의 앞 두 글자가 분류다. Spring `SQLStateSQLExceptionTranslator`도 `substring(0, 2)`로 분류한 뒤 몇 개의 전체 코드(`23505`, `40001`, `57014`)만 따로 본다.
- **결정 트리** — 한 코드에 원인이 여럿이면 질문 몇 개로 가른다. 아래 `40001` 그림이 그렇다.
- **wait-for 그래프** — 락 대기를 "누가 누구를 기다리나"로 따라간다. `pg_blocking_pids()`, `sys.innodb_lock_waits`가 이 그래프의 간선을 보여 준다(15번).

```text
  40001을 보면 먼저 묻는다: "어느 제품, 어느 메시지인가?"

    PostgreSQL ─┬─ "due to concurrent update"          -> RR 갱신 충돌, 전체 재시도   (16)
                ├─ "read/write dependencies"            -> SSI, 재시도 + 술어 락 범위  (14)
                └─ "conflict with recovery" (팔로워)    -> 복제 재생 충돌, 재시도보다 설정 (32)
    MySQL ──────┬─ 1213 Deadlock found                   -> 잠금 순서                   (15)
                └─ 1205 (Connector/J가 40001로 바꿈)      -> 오래 쥔 쪽 찾기, 명시 롤백    (15)
    분산 DB ────── 시계 불확실성·핫 키                      -> 시계 오프셋, 키 분산        (55)
```

```java
// 원문을 잃지 않게 — Spring 예외 아래의 SQLException에서 SQLSTATE와 제품 번호를 같이 남긴다
catch (DataAccessException e) {
    Throwable c = e.getMostSpecificCause();
    if (c instanceof SQLException sql) {
        log.warn("db error sqlState={} vendorCode={} msg={}",
                 sql.getSQLState(), sql.getErrorCode(), sql.getMessage());
        // MySQL: 1205(락 대기 초과) vs 1213(교착) 은 vendorCode로만 가른다 — Connector/J에서 SQLSTATE는 둘 다 40001
    }
    throw e;
}
```

## 적용 — 풀어나가는 법

### 1. 모양으로 1차 분류한다

```text
  모양                                   대개 뜻하는 것                            가 볼 곳
  ------------------------------------   ---------------------------------------   ------------
  몇십 초 멈춘 뒤 한꺼번에 실패            풀 대기(기본 30초)·락 대기(50초)·타임아웃   21, 22, 15
  즉시 실패, 일부 요청만                    교착·직렬화 실패·UNIQUE 위반              15, 14, 02
  배포 직후부터                             DDL 락 큐, 롤백 불가 스키마, 캐시 형식,     26, 31, 27
                                          시간대 바뀐 이미지
  배치·백필이 도는 동안                     락·undo·복제 지연·버퍼 풀 오염             34, 32, 07
  매일 같은 시각                            TTL 동시 만료, 파티션 미생성, 체크포인트     31, 33, 44
  며칠~몇 달 서서히                         bloat, XID 나이, 슬롯이 붙든 WAL           16, 19, 32
  에러 없이 값만 틀림                       시간대, collation, 팬아웃, lost update     27, 10, 04, 14
```

### 2. 첫 진단 세트 — PostgreSQL 17

```sql
-- 지금 무엇이 돌고, 누가 누구를 막나 (락·풀 고갈·bloat의 공통 출발점)
SELECT pid, state, wait_event_type, wait_event,
       now() - xact_start  AS xact_age,
       now() - query_start AS query_age,
       pg_blocking_pids(pid) AS blocked_by,
       left(query, 60) AS q
FROM pg_stat_activity
WHERE state <> 'idle' AND pid <> pg_backend_pid()
ORDER BY xact_start;

SELECT count(*) AS conns, current_setting('max_connections') AS max_conn FROM pg_stat_activity;  -- 53300
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;                              -- wraparound
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
FROM pg_replication_slots;                                                                       -- pg_wal 증가
SELECT client_addr, state, write_lag, flush_lag, replay_lag FROM pg_stat_replication;            -- 복제 지연
SELECT relname, n_live_tup, n_dead_tup, last_autovacuum
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;                                      -- bloat
SELECT datname, temp_files, pg_size_pretty(temp_bytes) FROM pg_stat_database;                    -- 스필
SHOW TimeZone;                                                                                   -- 9시간
```

- 위 쿼리는 이 노트 작성 환경(PostgreSQL 17.11 컨테이너, 전용 DB)에서 문법·열 이름을 확인했다.

### 3. 첫 진단 세트 — MySQL 8.4

```sql
SELECT * FROM sys.innodb_lock_waits\G                         -- 1205: 누가 누구를 기다리나
SELECT trx_id, trx_state, trx_started, trx_mysql_thread_id, trx_rows_locked
FROM information_schema.innodb_trx ORDER BY trx_started;      -- 오래 열린 트랜잭션
SHOW ENGINE INNODB STATUS\G                                   -- LATEST DETECTED DEADLOCK(1213), History list length
SELECT OBJECT_SCHEMA, OBJECT_NAME, LOCK_TYPE, LOCK_MODE, LOCK_STATUS
FROM performance_schema.data_locks;                           -- 행 락 목록
SHOW REPLICA STATUS\G                                         -- Seconds_Behind_Source
SHOW GLOBAL STATUS LIKE 'Threads_connected';                  -- 1040
SELECT @@max_connections, @@innodb_lock_wait_timeout, @@innodb_deadlock_detect,
       @@innodb_rollback_on_timeout, @@global.time_zone, @@session.time_zone, @@system_time_zone;
```

- 이 노트 작성 환경(MySQL 8.4.10)에서 실행해 확인했다. 기본값은 `max_connections` 151, `innodb_lock_wait_timeout` 50, `innodb_deadlock_detect` ON, `innodb_rollback_on_timeout` OFF였다(예시, MySQL 8.4.10).

### 4. leaf로 간다

- §1~§4 표에서 후보 leaf를 고른다. 후보가 여럿이면 각 leaf의 「장애 시나리오」 "보이는 형태"와 내 관찰을 대조해 지운다.
- 원인이 DB 밖이면 다른 색인으로 간다.
  - OOM kill·디스크·fsync: [os/37-os-symptom-index](../../os/37-os-symptom-index/2-summary.md)
  - 소켓 타임아웃·RST·연결 거부: [network/52-network-symptom-index](../../network/52-network-symptom-index/2-summary.md)
- 실제 사건에서 이 증상들이 어떻게 이어졌는지는 [57-db-incidents](../57-db-incidents/2-summary.md)에 있다.

## 장애 시나리오와 대처

이 절은 **읽기 실수**를 다룬다. 증상 자체는 위 표와 leaf에 있다.

### 1. 1205를 교착으로 읽는다

- **현상**: 주문 API가 50초 멈췄다가 실패한다. 담당자가 "교착이다"라고 판단하고 잠금 순서를 정렬하는 수정을 배포한다. 실패는 그대로다.
- **보이는 형태**
  - `ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction`.
  - Spring에서는 1205와 1213이 모두 `PessimisticLockingFailureException` 아래로 온다. 기본 번역 경로에서는 둘 다 `CannotAcquireLockException`일 수 있다(§2).
  - 메시지 끝의 "try restarting transaction"이 1213과 같아 보인다.
- **원인**
  - 1205는 **대기 시간 초과**다. 사이클이 없어도 난다. 한쪽이 락을 50초 넘게 쥐었을 뿐이다(15번). 1213은 탐지기가 사이클을 찾아 **즉시** 한쪽을 롤백한 것이다.
  - 단, 교착 탐지를 끈 서버(`innodb_deadlock_detect=OFF`)에서는 교착도 1205로 나타난다(15번 시나리오 4). 그래서 1205를 보면 설정부터 확인한다.
  - 1205는 기본 설정에서 **마지막 문장만** 롤백한다. 트랜잭션은 열린 채다. 그대로 커밋하면 반쪽 반영이 된다(13·15번).
- **대처**
  - 가르는 기준: 걸린 시간(즉시 vs 약 50초), 에러 번호(`getErrorCode()`), `innodb_deadlock_detect` 값.
  - 1205면 **오래 쥔 쪽**을 찾는다: `sys.innodb_lock_waits`, `innodb_trx.trx_started`. 그 문장이 DDL이면 메타데이터 락 대기일 수 있으니 `performance_schema.metadata_locks`를 본다(로컬 재현: `lock_wait_timeout=2`에서 `ALTER TABLE`이 `ERROR 1205`). 트랜잭션 안 원격 호출(18·24번), 대형 백필(34번), in-doubt XA(55번)가 흔하다.
  - 1205를 받으면 명시적으로 `ROLLBACK`한 뒤 트랜잭션 전체를 재시도한다.
  - 로그에 SQLSTATE만 남기면 안 된다. Connector/J에서 1205도 `40001`이다. 제품 번호를 같이 남긴다.

### 2. "앱을 재시작하니 풀렸다"로 닫는다 — DB에서는 쿼리가 계속 돈다

- **현상**: API가 전부 타임아웃이다. 앱을 재시작하자 잠시 괜찮다가 몇 분 뒤 다시 막힌다. DB CPU는 내내 높다.
- **보이는 형태**
  - 앱: `SocketTimeoutException: Read timed out`(pgJDBC 08006) 또는 풀 고갈 `Connection is not available`.
  - DB: `pg_stat_activity`에 같은 쿼리가 `active`로 여러 개, `query_age`가 수 분. 또는 `idle in transaction` 세션이 앞에서 락을 쥐고 있다.
- **원인**
  - 앱이 소켓을 끊어도 서버는 바로 모른다. PostgreSQL 기본(`client_connection_check_interval = 0`)에서는 다음 소켓 읽기·쓰기 때까지 쿼리를 계속 돈다(22번 재현). 이 값을 켜면 실행 중에도 끊김을 검사해 더 일찍 멈출 수 있다.
  - 앱 재시작은 **앱 쪽 대기열만** 비운다. DB의 폭주 쿼리·락은 남는다. 새 인스턴스가 같은 쿼리를 재시도로 다시 올리면 더 쌓인다.
  - DDL 락 큐도 같은 모양이다. 앞의 긴 트랜잭션 뒤에 `ALTER`가 서고, 그 뒤에 모든 SELECT가 선다(15·22·26번). 앱을 재시작해도 줄은 DB에 있다.
- **대처**
  - 재시작 전에 DB부터 본다. `pg_stat_activity`에서 `query_age`·`xact_age`가 큰 세션을 찾아 원인 세션만 `pg_cancel_backend`·`pg_terminate_backend`(MySQL `KILL QUERY`).
  - 재발 방지: 서버 측 `statement_timeout`을 소켓 타임아웃보다 짧게, `idle_in_transaction_session_timeout`, 마이그레이션에 `lock_timeout`. PostgreSQL 14+는 `client_connection_check_interval`(22번).
  - 재시도에는 상한과 백오프를 둔다.

### 3. 57014를 "타임아웃을 늘리자"로 읽는다

- **현상**: 리포트 API가 `canceling statement due to statement timeout`으로 실패한다. 한도를 30초에서 5분으로 올렸다. 이번에는 풀이 마른다.
- **보이는 형태**: SQLSTATE `57014`. Spring 기본 번역 경로에서는 6.2.9부터 `QueryTimeoutException`, 그 이전 6.x는 `DataAccessResourceFailureException`(§2). 한도를 올린 뒤에는 `Connection is not available`.
- **원인**
  - `57014` statement timeout은 한도가 **제 역할을 한** 것이다. 쿼리가 왜 느려졌는지가 질문이다(22번).
  - 흔한 뿌리: 배치 뒤 통계가 오래되어 플랜이 급변함(12번), 스필(41번), 재귀 CTE 순환(05번).
  - 같은 `57014`라도 메시지가 `due to user request`면 드라이버의 취소 요청이다. 누가 취소했는지가 다르다.
  - 한도를 올리면 느린 쿼리가 커넥션을 더 오래 쥔다. 풀 고갈로 번진다(21번).
- **대처**
  - 먼저 `EXPLAIN (ANALYZE, BUFFERS)`를 본다. `pg_stat_statements`는 누적값이므로 주기적으로 떠 둔 스냅숏의 구간별 차이(`total_exec_time`·`calls`)로 언제 느려졌는지 본다. `rows=`와 `actual rows=`가 크게 다르면 `ANALYZE`부터.
  - 정말 긴 작업이면 전역 한도가 아니라 배치 역할이나 `SET LOCAL`로 그 트랜잭션만 늘린다.

### 4. `too many clients`를 보고 `max_connections`·풀 크기를 키운다

- **현상**: 배포 중 새 인스턴스가 `FATAL: sorry, too many clients already`로 기동에 실패한다. `max_connections`를 올리고, 느리다는 보고에 풀 크기도 50 → 200으로 올렸다. p99가 더 나빠졌다.
- **보이는 형태**: `53300` / MySQL `1040`. 올린 뒤에는 DB CPU 100%, `active` 세션이 코어 수의 몇 배, `LWLock`·`Lock` 대기 증가.
- **원인**
  - 한도 초과의 뿌리는 **예산 계산**이다. 인스턴스 수 × 풀 크기 + 도구 커넥션. 배포 중에는 신구 인스턴스가 겹쳐 순간 2배가 된다(21번). 캐시 눈사태로 모든 읽기가 DB로 오면 풀도 한꺼번에 찬다(30번).
  - PostgreSQL `max_connections`는 공유 메모리 등 자원을 그만큼 잡고, 바꾸려면 재시작이 필요하다(21번).
  - 동시 실행이 코어 수를 크게 넘으면 전환·경합 비용이 늘어 쿼리 하나하나가 느려진다. 그러면 쥔 시간이 늘어 풀이 더 필요해 보인다(21번 시나리오 3).
- **대처**: 커넥션 예산을 다시 계산한다. 풀은 작게 유지하고 앱 쪽 줄에서 기다리게 한다. 앞단 풀러(PgBouncer)로 서버 커넥션 수를 줄인다. 풀 고갈이면 풀 크기가 아니라 **쥔 시간**을 줄인다.

### 5. 팔로워의 `40001`을 격리 수준 문제로 읽는다

- **현상**: 읽기 전용 리포트가 가끔 `40001`로 실패한다. 담당자는 "직렬화 실패"로 보고 격리 수준을 낮추는 코드를 넣는다. 그대로다.
- **보이는 형태**: `ERROR: canceling statement due to conflict with recovery`, `DETAIL: User query might have needed to see row versions that must be removed.` 리포트는 팔로워에 연결되어 있다. SQLSTATE가 `40001`이라 Spring·재시도 로직은 직렬화 실패와 같은 부류로 다룬다(32번).
- **원인**: 격리 수준과 무관하다. 팔로워가 리더의 vacuum 기록을 재생하려는데 조회가 그 옛 버전을 보고 있었다. `max_standby_streaming_delay`(기본 30초)를 넘겨 조회가 취소됐다(32번).
- **대처**
  - 코드만 보지 말고 **메시지와 연결 대상**을 본다.
  - 리포트 전용 팔로워는 `max_standby_streaming_delay`를 늘리거나(지연 증가) `hot_standby_feedback = on`(리더 bloat 감수)을 쓴다. 조회를 짧게 쪼갠다. 아주 긴 분석은 별도 분석 DB로 보낸다.

## 핵심 문장

- 이 노트는 **증상 → 층 → 흔한 원인 → 첫 진단 → leaf** 순서의 역색인이다. 고치지 않고 어느 노트로 갈지 정한다.
- `40001` 한 코드에 PostgreSQL의 RR 갱신 충돌·SSI 실패·팔로워 복구 충돌, MySQL의 교착(1213)이 겹친다. Connector/J에서는 1205도 `40001`이다. **메시지·제품·에러 번호**를 같이 읽는다.
- 1205는 대기 시간 초과이고 1213은 탐지된 교착이다. 1205는 기본 설정에서 마지막 문장만 롤백하므로 명시적으로 `ROLLBACK`한다.
- Spring 예외 클래스는 원문을 줄인다. 1205와 1213은 예외 클래스로 가를 수 없으니 원인 `SQLException`의 `getErrorCode()`를 남긴다.
- 앱이 연결을 끊어도 DB 쿼리는 계속 돈다. 재시작 전에 `pg_stat_activity`를 보고, 서버 측 타임아웃을 소켓 타임아웃보다 짧게 둔다.
- 가장 비싼 증상은 에러가 없다. 9시간 밀림·전날 매출(시간대), UNIQUE 위반(collation), 백필 누락(OFFSET), `@Transactional` 무시(자기 호출)는 leaf의 점검 쿼리로 찾는다.

## 관련 주제·근거

- 선행: 데이터베이스 영역 전체([../README.md](../README.md)). 특히
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md) — 1205·1213·40P01, 락 큐
  - [21-connection-pooling](../21-connection-pooling/2-summary.md) · [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md) — 풀 고갈, `too many clients`, 57014, 끊긴 뒤에도 도는 쿼리
  - [16-mvcc](../16-mvcc/2-summary.md) · [32-replication-leader-follower](../32-replication-leader-follower/2-summary.md) — bloat, wraparound, 복제 지연
  - [27-temporal-types-and-session-timezone](../27-temporal-types-and-session-timezone/2-summary.md) · [10-collation-and-text-comparison](../10-collation-and-text-comparison/2-summary.md) · [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md) · [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md) · [31-cache-key-versioning-and-serialization](../31-cache-key-versioning-and-serialization/2-summary.md)
- 이 노트가 가리키는 leaf: §1~§4 표의 링크 전부.
- 후속·연결
  - [57-db-incidents](../57-db-incidents/2-summary.md) — 실사건에서 이 증상들이 어떻게 이어졌나
  - [os/37-os-symptom-index](../../os/37-os-symptom-index/2-summary.md) · [network/52-network-symptom-index](../../network/52-network-symptom-index/2-summary.md) — OS·네트워크 증상 색인
- PostgreSQL 17 문서 부록 A "PostgreSQL Error Codes" <https://www.postgresql.org/docs/17/errcodes-appendix.html>, 소스 `src/backend/utils/errcodes.txt`(REL_17_STABLE) — 40001·40P01·55P03·57014·53300·53400·25P02·25P03·23505·23503·22P02·42703·57P03·08006 이름 확인
- PostgreSQL 17 문서 24.1.2 Recovering Disk Space(일반 VACUUM은 테이블 끝의 빈 페이지만 OS에 반환) · F.30 `pg_stat_statements`(누적 통계) · 19.3 `client_connection_check_interval`(기본 0 = 검사 안 함) <https://www.postgresql.org/docs/17/runtime-config-connection.html>
- PostgreSQL 문서 24.1.5 "Preventing Transaction ID Wraparound Failures" — 14~17판은 4천만 남으면 경고·3백만 남으면 새 XID 거부, 13판은 1,100만·1백만 <https://www.postgresql.org/docs/17/routine-vacuuming.html>. 거부 문구의 "that assign new transaction IDs"는 17판부터다(REL_16_STABLE·REL_17_STABLE `access/transam/varsup.c` 대조)
- MySQL 8.4 Reference Manual — 에러 메시지 참조 <https://dev.mysql.com/doc/mysql-errors/8.4/en/server-error-reference.html>, 17.14 InnoDB 설정(`innodb_lock_wait_timeout`, `innodb_rollback_on_timeout`) · 17.20.5 InnoDB Error Handling(교착은 트랜잭션 전체, 락 대기 초과·중복 키는 문장 롤백) <https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html> · 7.1.8 `lock_wait_timeout`(메타데이터 락) · Performance Schema `metadata_locks` 표 · 10.4.4 Internal Temporary Table Use(`Using temporary`, `Created_tmp_disk_tables`, `temptable_max_ram`, `temptable_use_mmap` 기본 OFF, `physical_disk`는 mmap 오버플로일 때) <https://dev.mysql.com/doc/refman/8.4/en/internal-temporary-tables.html>
- Spring Framework 6.2.x 소스 (spring-jdbc)
  - `JdbcAccessor.getExceptionTranslator()` — 사용자 `sql-error-codes.xml`이 있을 때만 에러 코드 번역기, 없으면 `SQLExceptionSubclassTranslator`
  - `sql-error-codes.xml` — MySQL `cannotAcquireLockCodes` 1205·3572, `deadlockLoserCodes` 149·1213, `duplicateKeyCodes` 1062 / PostgreSQL `cannotAcquireLockCodes` 55P03, `cannotSerializeTransactionCodes` 40001, `deadlockLoserCodes` 40P01, `dataAccessResourceFailureCodes` 53300 등
  - `SQLStateSQLExceptionTranslator` — `40001` → `CannotAcquireLockException`, 그 밖의 `40` → `PessimisticLockingFailureException`, `57014` → `QueryTimeoutException`(6.2.9부터. v6.2.8 태그 소스는 `57` 분류 → `DataAccessResourceFailureException`), `23505`·(23000 + 1062) → `DuplicateKeyException`
  - `SQLExceptionSubclassTranslator` — `SQLTransactionRollbackException` + `40001` → `CannotAcquireLockException`
  - <https://github.com/spring-projects/spring-framework/tree/6.2.x/spring-jdbc/src/main/java/org/springframework/jdbc/support> · 57014 버전 차이는 태그 `v6.2.8`·`v6.2.9`의 `SQLStateSQLExceptionTranslator.java` 대조
- MySQL Connector/J 9.x 소스 — `MysqlErrorNumbers.java`(1205·1213 → `40001`, 1205 줄 주석 "Overrides HY000 due to Bug#16634180"), `NativeProtocol.java`(서버 SQLSTATE가 `HY000`이면 자기 표로 대체), `SQLError.java`(`40`으로 시작하면 `MySQLTransactionRollbackException`) <https://github.com/mysql/mysql-connector-j/tree/release/9.x>
- pgJDBC 소스 `org/postgresql/util/PSQLException.java` — `extends SQLException` <https://github.com/pgjdbc/pgjdbc>
- 로컬 재현(2026-10-01, PostgreSQL 17.11·MySQL 8.4.10 컨테이너, 전용 DB `w56` — 끝나고 삭제): §적용 2·3의 진단 쿼리 문법·열 이름 확인, MySQL 기본값(`max_connections` 151 등) 확인. 에러별 출력은 각 leaf의 재현을 따른다. 사실 점검 재현(전용 DB `fc56` — 끝나고 삭제): mysql 클라이언트의 `ERROR 1205 (HY000)` 표시, PostgreSQL `55P03`의 `lock_timeout`·`NOWAIT` 두 문구. 판정 재현(전용 DB `fa54` — 끝나고 삭제): `lock_wait_timeout=2`에서 메타데이터 락을 기다린 `ALTER TABLE`이 `ERROR 1205 (HY000)`, 교착 문구 `Deadlock found when trying to get lock; try restarting transaction`, `temptable_use_mmap` 기본 0.
