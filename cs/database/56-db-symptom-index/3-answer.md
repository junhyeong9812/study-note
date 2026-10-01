# database/56-db-symptom-index — 정답

## 정답

### 1. 예외 이름만으로 원인을 적으면 안 되는 이유

증상은 아래층 사건이 위층 이름으로 **번역**된 것이다. 번역하면서 정보가 줄어든다.
- `CannotAcquireLockException`은 "락 획득 실패"까지만 말한다. MySQL 1205(대기 시간 초과)와 1213(교착)이 모두 이 이름으로 올 수 있다(Spring 6.x 기본 번역 경로 + Connector/J).
- 풀 고갈 `Connection is not available`의 원인은 DB의 락 대기·느린 쿼리·트랜잭션 안 HTTP 호출 중 무엇이든 될 수 있다.

함께 확보할 것:
- **원문**: SQLSTATE, 제품 에러 번호(`getErrorCode()`), 서버 로그 줄, 예외 체인 전체(`Caused by`).
- **모양**: 즉시 실패인가, 몇십 초 멈춘 뒤 실패인가(풀 기본 30초, InnoDB 락 대기 50초), 에러 없이 값만 틀렸나. 배포·배치·자정 같은 시각과 겹치나.

### 2. 1205 vs 1213

| | 1205 `Lock wait timeout exceeded` | 1213 `Deadlock found` |
|---|---|---|
| 뜻 | 락을 `innodb_lock_wait_timeout`(8.4 기본 50초) 넘게 기다림. 사이클이 없어도 난다 | 탐지기가 wait-for 사이클을 찾아 한쪽을 롤백 |
| 걸린 시간 | 약 50초 멈춘 뒤 | 거의 즉시 |
| 롤백 범위 | 기본(`innodb_rollback_on_timeout=OFF`)은 **마지막 문장만**. 트랜잭션은 열려 있다 | 트랜잭션 전체 |
| 첫 진단 | `sys.innodb_lock_waits`, `innodb_trx.trx_started` — 오래 쥔 쪽. DDL이 기다렸다면 메타데이터 락(`performance_schema.metadata_locks`) | `SHOW ENGINE INNODB STATUS`의 `LATEST DETECTED DEADLOCK` — 두 쿼리와 잠금 순서 |

- 교착인데 1205가 되는 경우: `innodb_deadlock_detect=OFF`면 교착은 락 대기 시간 초과로만 풀린다(15번). 앱 락과 DB 락이 섞인 교착처럼 탐지기 밖의 사이클도 대기 초과로 끝난다.
- 1205 뒤에는 명시적으로 `ROLLBACK`하고 트랜잭션 전체를 재시도한다. 그대로 커밋하면 반쪽 반영이 된다(13·15번).

### 3. `40001`의 여러 얼굴

| 제품 · 메시지 | 원인 | 대처 |
|---|---|---|
| PostgreSQL `could not serialize access due to concurrent update` | RR에서 스냅샷 뒤 커밋된 행을 갱신(16번) | 트랜잭션 전체 재시도. 경합 행이면 RC + 조건부 UPDATE |
| PostgreSQL `… read/write dependencies among transactions` | SSI 위험 구조, 순차 스캔의 넓은 술어 락(14번) | 재시도 + 인덱스로 술어 락 좁히기 |
| PostgreSQL 팔로워 `canceling statement due to conflict with recovery` | 복제 재생과 충돌(32번) | 재시도보다 `max_standby_streaming_delay`·`hot_standby_feedback`·조회 쪼개기 |
| MySQL `1213 (40001)` 교착 | 반대 순서 잠금·갭 락(15번) | 잠금 순서 통일 + 재시도 |
| MySQL 1205 (Connector/J가 `40001`로 올림) | 오래 쥔 락(15번) | 오래 쥔 쪽 제거, 명시 롤백 |
| CockroachDB `ReadWithinUncertaintyIntervalError` | 시계 불확실성·핫 키(55번) | 시계 오프셋 경보, 키 분산, 백오프 재시도 |

원인이 다르니 대처가 다르다. 같은 "재시도"도 팔로워 충돌에서는 설정을 바꾸지 않으면 계속 실패하고, 1205에서는 롤백 없이 재시도하면 반쪽 커밋이 남는다.

### 4. Spring 번역 경로와 1205/1213

- Spring 6.x `JdbcAccessor.getExceptionTranslator()`:
  - classpath 루트에 **사용자** `sql-error-codes.xml`이 있으면 `SQLErrorCodeSQLExceptionTranslator`(에러 코드 표). MySQL 1205 → `CannotAcquireLockException`, 1213 → `DeadlockLoserDataAccessException`(deprecated).
  - 없으면 `SQLExceptionSubclassTranslator` → 못 정하면 `SQLStateSQLExceptionTranslator`. `40001`이면 `CannotAcquireLockException`, 그 밖의 `40`이면 `PessimisticLockingFailureException`.
- Connector/J 9.x는 서버 SQLSTATE가 `HY000`이면 자기 표로 바꾼다. 표는 1205와 1213을 모두 `40001`로 둔다. `40`으로 시작하면 `MySQLTransactionRollbackException`(`SQLTransactionRollbackException` 계열)을 던진다.
- 그래서 기본 경로에서는 둘 다 `CannotAcquireLockException`이고 `getSQLState()`도 둘 다 `40001`이다. mysql 명령행 클라이언트는 `ERROR 1205 (HY000)`로 보여 주므로 도구마다 SQLSTATE가 달라 보인다.
- 로그에 남길 값: 원인 `SQLException`의 `getErrorCode()`(1205 / 1213)와 메시지.
- 이 정리는 소스 읽기다. JVM에서 실행해 확인하지 않았다.

### 5. "재시작하니 풀렸다"

- 의심: 앱이 끊어도 DB에서 계속 도는 폭주 쿼리(PostgreSQL 기본 `client_connection_check_interval = 0`이면 다음 소켓 상호작용까지 모른다), 또는 앞에서 락을 쥔 `idle in transaction`·DDL 락 큐. 앱 재시작은 앱 쪽 대기열만 비운다. 새 인스턴스가 재시도로 같은 쿼리를 다시 올리면 더 쌓인다.
- 먼저 볼 것: `pg_stat_activity`의 `state`·`wait_event_type`·`now() - query_start`·`now() - xact_start`·`pg_blocking_pids(pid)`. 원인 세션만 `pg_cancel_backend`·`pg_terminate_backend`(MySQL `KILL QUERY`).
- 재발 방지:
  1. 서버 측 `statement_timeout`을 소켓 타임아웃보다 짧게.
  2. `idle_in_transaction_session_timeout`.
  3. 마이그레이션 세션의 `lock_timeout`(MySQL `lock_wait_timeout`). PostgreSQL 14+는 `client_connection_check_interval`도 있다.
- 재시도에는 상한과 백오프를 둔다(22번).

### 6. 57014

- statement timeout의 `57014`는 한도가 **제 역할을 한** 것이다. 먼저 쿼리가 왜 느려졌는지 본다.
  - `EXPLAIN (ANALYZE, BUFFERS)`: `rows=` vs `actual rows=` 괴리(통계·플랜 급변, 12번), `external merge`(스필, 41번), 재귀 CTE 순환(05번).
  - `pg_stat_statements`는 누적값이다. 주기적으로 떠 둔 스냅숏의 구간별 `total_exec_time`·`calls` 차이로 느려진 시각을 찾아 배치·ANALYZE 시각과 대조한다.
- 한도를 무작정 올리면 느린 쿼리가 커넥션을 오래 쥐어 풀 고갈로 번진다(21번). 정말 긴 작업만 배치 역할이나 `SET LOCAL`로 늘린다.
- `due to user request`: 같은 `57014`지만 드라이버의 쿼리 타임아웃(취소 요청)이나 `pg_cancel_backend`가 취소한 것이다. 서버 한도가 아니라 **누가 취소했는지**를 봐야 한다(22번).

### 7. `too many clients` 뒤 한도를 키우면

- 생길 수 있는 일:
  - PostgreSQL `max_connections`는 공유 메모리 등을 그만큼 잡고, 바꾸려면 재시작해야 한다(21번).
  - 풀을 키워 동시 실행이 코어 수를 크게 넘으면 전환·락 경합 비용이 늘어 쿼리 하나하나가 느려진다. 쥔 시간이 늘어 풀이 더 필요해 보이는 악순환이 생긴다(21번 시나리오 3). 결과는 p99 악화다.
- 먼저 할 계산: 커넥션 예산 = 인스턴스 수 × 풀 크기 + 배치·도구 커넥션. 배포 중 신구 인스턴스가 겹치는 순간(최대 2배)을 넣는다. 캐시 눈사태 때 DB로 몰리는 요청도 고려한다(30번).
- 대처: 풀은 작게, 앞단 풀러(PgBouncer)로 서버 커넥션 수를 줄인다.

### 8. bloat와 History list length

- PostgreSQL: `pg_stat_user_tables.n_dead_tup`이 쌓이고 `VACUUM VERBOSE`가 `dead but not yet removable`을 보고한다(16번).
- MySQL: `SHOW ENGINE INNODB STATUS`의 `History list length`가 수만~수백만으로 오르고 undo 공간이 커진다(16·34번).
- 공통 원인: 오래 열린 트랜잭션(리포트·백업·잊힌 `idle in transaction`)의 스냅샷(read view)이 옛 버전 정리를 막는다.
- 첫 진단: PostgreSQL `pg_stat_activity`의 `xact_start`, MySQL `information_schema.innodb_trx`의 `trx_started`.
- 이미 커진 PostgreSQL 파일은 일반 `VACUUM`으로 보통 줄지 않는다. 재사용 가능으로 표시만 한다(테이블 끝의 완전히 빈 페이지만 잘라낼 수 있다, 06·34번).

### 9. 에러 없는 증상 넷

| 증상 | 원인 | 첫 확인 |
|---|---|---|
| 저장 시각 9시간 밀림 | JVM·드라이버·DB 세션 시간대 불일치(예: Connector/J `connectionTimeZone=LOCAL` 가정인데 세션은 UTC), 27번 | 같은 행을 `UTC`·`Asia/Seoul` 세션에서 조회, `@@session.time_zone`·`SHOW TimeZone`, 시작 시각이 배포와 겹치나 |
| 일별 매출이 전날로 | UTC 세션에서 `date_trunc('day', …)`·`DATE(…)`. UTC 자정 = KST 09:00, 27번 | 차이가 매일 00:00~08:59 KST 금액인가 |
| 백필 뒤 행 누락 | "처리하면 대상에서 빠지는" 조건 위의 OFFSET 청크, 34번 | 잡 끝에 대상 조건 재계수(0이어야 함) |
| `@Transactional` 무시 | 자기 호출·private 메서드라 프록시를 거치지 않음, 24번 | 트랜잭션 DEBUG 로그에 생성 줄이 있나, `isActualTransactionActive()` |

### 10. 팔로워의 40001

- 메시지는 `canceling statement due to conflict with recovery`다. 격리 수준과 무관하다.
- 원인: 팔로워가 리더의 vacuum 기록을 재생해야 하는데 조회가 그 옛 버전을 보고 있었다. `max_standby_streaming_delay`(기본 30초)를 넘겨 조회가 취소됐다(32번).
- SQLSTATE가 `40001`이라 Spring·재시도 로직이 직렬화 실패와 같은 부류로 다룬다. 그래서 코드만 보면 오판한다.
- 대처: 리포트 전용 팔로워의 `max_standby_streaming_delay`를 늘리거나(지연 증가) `hot_standby_feedback = on`(리더 bloat 감수). 조회를 짧게 쪼갠다. 아주 긴 분석은 별도 분석 DB로 보낸다.
