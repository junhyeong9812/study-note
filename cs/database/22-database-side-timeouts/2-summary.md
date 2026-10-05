# database/22-database-side-timeouts — 서버 측 시간 한도와 클라이언트 타임아웃의 정렬 — 정리 (힌트)

## 해결하는 문제

타임아웃은 여러 층에 따로 있다. 앱이 "3초 뒤 포기"를 해도 DB가 멈추는 것은 아니다.

```text
  앱: "3초 지났다, 포기"  ──X── (소켓을 닫음)
  DB: SELECT ... 계속 실행 중 (CPU·I/O·락을 그대로 쥔 채)
      → 사용자는 이미 떠났는데 일은 끝까지 한다
      → 같은 요청을 재시도하면 같은 무거운 쿼리가 하나 더 돈다
```

- PostgreSQL 17과 MySQL 8.4의 서버 측 시간 한도는 **기본값이 꺼져 있거나 매우 길다**. `statement_timeout`·`lock_timeout`·`idle_in_transaction_session_timeout`은 PostgreSQL 17에서 기본 0(끔)이다. MySQL 8.4의 메타데이터 락 대기 `lock_wait_timeout`은 기본 31536000초(1년)다.
- 그래서 한 번 폭주한 쿼리나 열린 채 버려진 트랜잭션이 커넥션과 락을 오래 붙잡는다.

쉬운 예: 식당 주문이다.
- 손님(앱)이 기다리다 나가도, 주방(DB)은 주문서를 받은 요리를 계속 만든다.
- 주방이 "20분 넘는 주문은 버린다"는 규칙(서버 측 한도)을 가져야 주방이 막히지 않는다.
- 손님이 나갈 때 주문 취소를 **알려 줘야**(취소 요청) 주방이 멈춘다.

똑같은 구조다.\
클라이언트 타임아웃은 "내가 기다리기를 그만둔다"이고, 서버 타임아웃은 "일 자체를 멈춘다"다.

실무 예:
- 앱 로그 `ERROR: canceling statement due to statement timeout`(PostgreSQL, 57014).
- 컬럼 하나 추가하는 `ALTER TABLE` 배포 직후 해당 테이블의 모든 쿼리가 멈췄다.
- `pg_stat_activity`에 `idle in transaction`이 몇 시간째 떠 있고, 테이블이 계속 부푼다.

## 동작·원리

### 1. 층별 타임아웃 지도

```text
  [클라이언트 쪽]                                        누가 멈추나
  요청 데드라인(HTTP 타임아웃, 게이트웨이)                  앱이 기다리기를 멈춤
   └ 풀 connectionTimeout (HikariCP 기본 30s)            커넥션 대여를 포기
      └ JDBC Statement.setQueryTimeout(초)               드라이버가 서버에 "취소" 요청
         └ 드라이버 socketTimeout (pgjdbc 초 / Connector/J ms, 기본 0)
                                                        소켓을 닫고 포기. 서버에는 알리지 않음
  ───────────── 네트워크 (TCP keepalive, 중간 장비 idle timeout) ─────────────
  [서버 쪽 — PostgreSQL 17]
   statement_timeout                    문장 하나의 실행 시간        → ERROR 57014
   lock_timeout                         락 하나를 기다리는 시간      → ERROR 55P03
   idle_in_transaction_session_timeout  트랜잭션 안에서 노는 시간     → FATAL 25P03 (세션 종료)
   transaction_timeout (17 신규)         트랜잭션 전체 시간          → FATAL 25P04 (세션 종료)
   idle_session_timeout                 트랜잭션 밖에서 노는 시간     → FATAL 57P05 (세션 종료)
  [서버 쪽 — MySQL 8.4 InnoDB]
   max_execution_time (ms)              읽기 전용 SELECT만           → ERROR 3024
   innodb_lock_wait_timeout (기본 50s)   InnoDB 행 락 대기           → ERROR 1205 (문장만 롤백)
   lock_wait_timeout (기본 1년)           메타데이터 락 대기(DDL 등)
   wait_timeout (기본 28800s)            유휴 연결                  → 연결 끊음
```

- PostgreSQL 17 문서 19.11.1(Statement Behavior)이 각 한도의 정의다. 로컬 `SHOW`로도 전부 0임을 확인했다(PostgreSQL 17.11).
- MySQL 8.4 기본값은 로컬 `SELECT @@...`로 확인했다(MySQL 8.4.10). `innodb_lock_wait_timeout` 50, `max_execution_time` 0, `wait_timeout` 28800, `lock_wait_timeout` 31536000.
- `max_execution_time`은 **읽기 전용 SELECT**에만 걸린다. 저장 프로그램 안의 SELECT에는 걸리지 않는다(MySQL 8.4 문서, 서버 시스템 변수). UPDATE·DELETE에는 효과가 없다.

### 2. 클라이언트가 포기해도 서버는 계속 돈다

로컬 재현(예시, PostgreSQL 17.11, pgjdbc 42.7.8): 6초 걸리는 쿼리에 두 가지 클라이언트 타임아웃을 걸었다.

```text
  (a) socketTimeout=2 (초)
      client after 2023ms: SQLState=08006 An I/O error occurred while sending to the backend.
                           cause=SocketTimeoutException: Read timed out
      server: pid=4012 state=active running=00:00:02.033 q=select pg_sleep(6)   ← 아직 돈다
      5초 뒤: (no such query)                                                   ← 끝까지 돌고 끝남

  (b) setQueryTimeout(2)
      client after 2013ms: SQLState=57014 ERROR: canceling statement due to user request
      server: pid=4022 state=idle                                               ← 서버가 멈춤
      같은 커넥션 재사용: 가능
```

- (a) 소켓 타임아웃은 **소켓만 닫는다**. 서버는 결과를 보내려 할 때까지 모른다.
- (b) 쿼리 타임아웃은 드라이버가 서버에 **취소 요청**을 보낸다. pgjdbc 문서는 취소 명령이 별도 연결로(out of band) 간다고 적는다(`cancelSignalTimeout` 기본 10초). 취소가 쿼리 실행 중에 도착하면 서버는 57014로 문장을 멈추고, 커넥션은 살아 있다. 이미 끝난 뒤 도착한 취소는 효과가 없고, 성공 여부도 따로 통보되지 않는다(문서 53.2.8).
- MySQL 8.4(Connector/J 8.4.0)도 같다.
  - `socketTimeout`으로 끊으면 클라이언트는 `Communications link failure`(08S01)를 받는다. 이때도 서버 processlist에는 `SELECT SLEEP(6)`이 `User sleep` 상태로 남아 있었다.
  - `setQueryTimeout(2)`는 2047ms 뒤 `MySQLTimeoutException: Statement cancelled due to timeout or client request`를 냈다. 서버 쪽 쿼리도 사라졌다.

**서버가 끊긴 클라이언트를 알아채게 하기** — PostgreSQL 14부터 `client_connection_check_interval`이 있다.

```text
  로컬 재현(예시): client_connection_check_interval=500ms, socketTimeout=2s, pg_sleep(6)
  client: SQLState=08006
  1.5초 뒤 서버 쪽 해당 쿼리: 0건
  서버 로그: FATAL:  connection to client lost
```

- 쿼리 실행 중에 소켓을 주기적으로 폴링해, 커널이 연결 종료를 알려 주면 쿼리를 멈춘다(문서 19.3.1). 기본 0(끔).
- 이번 재현은 클라이언트가 소켓을 **닫아서** 커널이 알 수 있었다. 네트워크가 끊겨 아무 패킷도 오지 않으면 커널도 모른다. 이 경우는 TCP keepalive 설정(`tcp_keepalives_*`)이 함께 필요하다고 문서가 적는다.

### 3. 락 대기열 — `lock_timeout` 없는 DDL이 모두를 멈춘다

```text
  시간 →
  A: BEGIN; SELECT count(*) FROM t;  ── (AccessShareLock 쥔 채 6초 딴 일) ──> COMMIT
  B:        ALTER TABLE t ADD COLUMN c1 int;  ── AccessExclusiveLock 대기...  ──> 그제야 실행
  C:                 SELECT count(*) FROM t;  ── AccessShareLock 대기...      ──> 그 다음
                     ↑ A와는 충돌하지 않는데도 B 뒤에 줄 선다
```

로컬 재현(예시, PostgreSQL 17.11):

```text
   pid  | state  | wait_event_type | wait_event | blockers | q
  ------+--------+-----------------+------------+----------+------------------------------
   4723 | active | Timeout         | PgSleep    | {}       | SELECT pg_sleep(6);
   4730 | active | Lock            | relation   | {4723}   | ALTER TABLE t ADD COLUMN c1 int
   4737 | active | Lock            | relation   | {4730}   | SELECT count(*) FROM t

   pg_locks:  4723 AccessShareLock granted=t / 4730 AccessExclusiveLock granted=f /
              4737 AccessShareLock granted=f
```

- C의 blocker가 A가 아니라 **아직 락을 받지도 못한 B**다.
- PostgreSQL 락 관리자 README 규칙 1: 새 요청은 이미 준 락뿐 아니라 **대기 중인 요청**과도 충돌하지 않아야 즉시 받는다. C의 AccessShareLock은 A와는 맞지만 대기 중인 B의 AccessExclusiveLock과 충돌하므로 줄 끝에 선다.
- 같은 README: 락이 풀릴 때 대기자를 깨우는 조건은 둘이다. (a) 이미 준 락과 충돌하지 않고 (b) **앞선 대기자의 요청과도 충돌하지 않아야** 한다. 규칙 (b)가 도착 순서를 지킨다. 그래서 C는 B를 추월하지 못한다.
- 해법은 DDL에 `lock_timeout`을 짧게 거는 것이다. 실패하면 재시도한다.

```sql
SET lock_timeout = '1s';
ALTER TABLE t ADD COLUMN c2 int;
-- ERROR:  55P03: canceling statement due to lock timeout   (로컬 재현)
```

- `lock_timeout`은 락 **획득 시도 하나하나**에 따로 적용된다(문서). `statement_timeout`이 같거나 작으면 `lock_timeout`은 의미가 없다. 문장 타임아웃이 먼저 터지기 때문이다(문서).
- MySQL 8.4에서 DDL이 기다리는 메타데이터 락은 `lock_wait_timeout`(기본 1년)이 다룬다. `innodb_lock_wait_timeout`은 InnoDB 행 락에만 걸리고 테이블 락 대기에는 걸리지 않는다(문서).

### 4. idle in transaction — 세션을 끊는 이유

```text
  BEGIN; SELECT ... ;   ← 여기서 앱이 외부 API를 부르거나, 예외로 커밋·롤백을 빠뜨림
  (트랜잭션 열린 채 대기)
     - 이미 잡은 행 락·테이블 락 유지
     - 이 트랜잭션이 볼 수도 있는 옛 행 버전을 vacuum이 못 지움 → bloat
```

- PostgreSQL 17 문서는 `idle_in_transaction_session_timeout`의 용도를 두 가지로 적는다. 놀고 있는 세션이 락을 오래 쥐지 않게 하는 것, 그리고 열린 트랜잭션이 vacuum을 막아 테이블이 부푸는 것을 막는 것이다.
- 로컬 재현(예시, PostgreSQL 17.11): 1초로 두고 2초 쉰 뒤 다음 문장을 보냈다.

```text
  FATAL:  25P03: terminating connection due to idle-in-transaction timeout
  server closed the connection unexpectedly
```

- 문장 하나가 아니라 **세션이 끝난다**. 풀 입장에서는 그 커넥션이 죽은 것이다. 다음 대여 때 검증에 걸려 교체된다.
- 17 신규 `transaction_timeout`은 트랜잭션 **전체 길이**를 제한한다. 명시적 `BEGIN`에도, 문장 하나짜리 암묵 트랜잭션에도 걸린다. prepared transaction(`PREPARE TRANSACTION`)에는 걸리지 않는다. 이 값이 `idle_in_transaction_session_timeout`이나 `statement_timeout`보다 짧거나 같으면 긴 쪽은 무시된다(문서).

### 5. MySQL의 락 대기 타임아웃은 문장만 되돌린다

```text
  세션 A: BEGIN; UPDATE t SET v=v+1 WHERE id=1; (4초 쥠)
  세션 B: SET SESSION innodb_lock_wait_timeout=2; BEGIN;
          UPDATE t SET v=100 WHERE id=2;          ← 성공
          UPDATE t SET v=v+10 WHERE id=1;         ← ERROR 1205 (HY000): Lock wait timeout exceeded
          SELECT ...  → id=2 v=100 이 트랜잭션 안에 그대로 있다
          COMMIT;                                  ← id=2 변경만 커밋됨
```

- 로컬 재현(MySQL 8.4.10) 결과다. 문서도 같다: 타임아웃이 나면 **현재 문장만** 롤백한다. 트랜잭션 전체를 롤백하려면 `--innodb-rollback-on-timeout`으로 서버를 시작해야 한다(기본 OFF).
- 그래서 1205를 받은 앱이 그냥 COMMIT하면 **반쯤 된 트랜잭션**이 커밋된다. 1205를 받으면 앱이 명시적으로 롤백해야 한다.
- 비교: 교착(1213)은 InnoDB가 트랜잭션 하나를 통째로 롤백한다([15](../15-two-phase-locking-and-deadlock/2-summary.md)).

### 6. 정렬 규칙 — 누가 먼저 터져야 하나

```text
  짧다 ──────────────────────────────────────────────────────────> 길다
  lock_timeout < statement_timeout < 드라이버 query timeout < socketTimeout < 요청 데드라인
  (락만 오래 기다리면     (서버가 깔끔히 멈춤,    (서버 한도가 없을 때의    (서버가 응답 불능일 때
   먼저 포기)             커넥션은 살아 있음)      취소 요청)               마지막 안전핀)

  maxLifetime < 경로상 가장 짧은 idle 한도 (LB·NAT·DB wait_timeout)       ← 21번
```

- 서버 쪽이 **먼저** 터지게 둔다. 그래야 일이 실제로 멈추고, 커넥션도 재사용할 수 있다.
- `socketTimeout`이 먼저 터지면 서버는 계속 돌고, 커넥션은 버려진다. 그래서 가장 길게, 마지막 안전핀으로 둔다.
- 요청 데드라인이 짧은데 서버 한도가 길면 이 절 §2의 "주인 잃은 쿼리"가 쌓인다. 재시도가 붙으면 부하가 곱절이 된다.

### 7. 역할별 기본값 — 전역 설정 대신

- PostgreSQL 17 문서는 `statement_timeout`·`lock_timeout`·`transaction_timeout`을 `postgresql.conf`에 두는 것을 권하지 않는다. 모든 세션(관리 작업·백업 포함)에 걸리기 때문이다.
- 대신 **역할(계정)별·DB별 기본값**을 둔다.

```sql
-- PostgreSQL: 웹 앱 계정은 짧게, 배치 계정은 길게
ALTER ROLE web_app   IN DATABASE app SET statement_timeout = '5s';
ALTER ROLE web_app   IN DATABASE app SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE batch_job IN DATABASE app SET statement_timeout = '30min';
ALTER ROLE migrator  IN DATABASE app SET lock_timeout = '2s';

-- 특정 트랜잭션만 예외
BEGIN;
SET LOCAL statement_timeout = '60s';   -- 이 트랜잭션이 끝나면 원래 값으로
...
COMMIT;
```

- 로컬 재현(PostgreSQL 17.11): `ALTER ROLE w21_app IN DATABASE w21 SET statement_timeout = '1s'` 뒤 새 연결의 `SHOW statement_timeout`이 `1s`였다. `pg_sleep(2)`는 57014로 취소됐다. `SET LOCAL statement_timeout='5s'` 트랜잭션 안에서는 `pg_sleep(2)`가 통과했고, 커밋 뒤 `SHOW`는 다시 `1s`였다.
- PgBouncer `transaction` 모드에서는 세션 `SET`이 다음 트랜잭션에 이어진다고 기대할 수 없다(기능 표에서 `SET/RESET` "Never"). 역할 기본값이나 `SET LOCAL`을 쓴다.
- MySQL 8.4: `max_execution_time`은 `SET_VAR` 힌트나 `MAX_EXECUTION_TIME(N)` 옵티마이저 힌트로 문장별로 줄 수 있다. `innodb_lock_wait_timeout`은 `SET_VAR` 힌트가 적용되지 않는다(문서 "SET_VAR Hint Applies: No"). 세션 `SET`으로 준다.

## 쓰이는 자료구조·알고리즘

- **타이머 다중화**: PostgreSQL 백엔드는 여러 타임아웃 사유를 **SIGALRM 하나**로 다중화한다(`src/backend/utils/misc/timeout.c` 머리 주석). 활성 타임아웃을 만료 시각 순 배열(`active_timeouts[]`)로 두고, 가장 이른 것 하나에 타이머를 건다.
  - 타이머 자료구조 일반(타이머 힙 vs 타이머 휠)은 [data-structure/26-timer-structures](../../data-structure/26-timer-structures/2-summary.md).
- **락 대기 큐**: 락 객체마다 대기자 큐가 있다. 깨울 때 "앞선 대기자와 충돌하면 못 깬다" 규칙이 도착 순서를 지킨다. 이 때문에 §3의 DDL 줄서기가 생긴다(PostgreSQL `src/backend/storage/lmgr/README`).
  - 교착 탐지기는 이 큐 순서를 "soft edge"로 wait-for 그래프에 넣고, 필요하면 큐를 재배열한다(같은 README).
- **취소 요청 프로토콜**: PostgreSQL 클라이언트는 **새 연결**을 열어 CancelRequest를 보낸다. 연결 시작 때 받은 PID·비밀 키가 맞아야 서버가 받아들인다(PostgreSQL 17 문서 53.2.8 "Canceling Requests in Progress"). 원래 연결은 결과를 기다리던 그대로다.

## 적용 — 풀어나가는 법

### 1. Java — 층별로 한 번씩

```java
// 풀 (21번)
HikariConfig c = new HikariConfig();
c.setJdbcUrl("jdbc:postgresql://db/app?socketTimeout=60");  // 초 단위, 마지막 안전핀
c.setConnectionTimeout(3_000);
c.setMaxLifetime(25 * 60_000);
// 서버 한도는 역할 기본값(ALTER ROLE ... SET)으로 — 풀이 SET을 보내지 않아도 된다

// 쿼리별 예외
try (PreparedStatement ps = conn.prepareStatement(sql)) {
    ps.setQueryTimeout(10);   // 드라이버가 취소 요청을 보낸다 (pgjdbc: 57014 "due to user request")
    ps.executeQuery();
}
```

- Spring `@Transactional(timeout = 5)`도 있다. `JdbcTemplate` 경로에서는 `DataSourceUtils.applyTransactionTimeout`이 남은 트랜잭션 시간을 각 `Statement`의 query timeout으로 건다(Spring `DataSourceUtils` javadoc). 결국 드라이버 취소 요청이다. JPA(Hibernate) 경로도 같은 결과다. Spring `HibernateJpaDialect`가 `session.getTransaction().setTimeout(...)`을 걸고, Hibernate `StatementPreparerImpl`이 남은 시간을 각 `PreparedStatement.setQueryTimeout`으로 건다(spring-orm·hibernate-core 소스).

### 2. TS — node-postgres는 서버 한도와 클라이언트 한도를 이름으로 구분한다

```ts
const pool = new Pool({
  statement_timeout: 5_000,                   // 서버에 statement_timeout 으로 전달
  lock_timeout: 1_000,                        // 서버 lock_timeout
  idle_in_transaction_session_timeout: 30_000,// 서버
  query_timeout: 10_000,                      // 클라이언트: query() 호출을 기다리는 시간
  connectionTimeoutMillis: 3_000,             // 클라이언트: 연결·대여 대기
});
```

- node-postgres 문서의 `Client` 설정 설명: `statement_timeout`은 "statement in query will time out", `query_timeout`은 "query call will timeout", 둘 다 기본 타임아웃 없음. 앞의 것은 서버가 멈추고, 뒤의 것은 호출만 포기한다.

### 3. 진단

```sql
-- PostgreSQL: 오래 도는 문장·오래 열린 트랜잭션
SELECT pid, usename, state, wait_event_type, wait_event,
       now() - xact_start  AS xact_age,
       now() - query_start AS query_age,
       pg_blocking_pids(pid) AS blockers,
       left(query, 60)
FROM pg_stat_activity
WHERE backend_type = 'client backend' AND state <> 'idle'
ORDER BY xact_start NULLS LAST;

SELECT pg_cancel_backend(pid);     -- 문장만 취소 (57014)
SELECT pg_terminate_backend(pid);  -- 세션 종료 (idle in transaction 정리)
```

```sql
-- MySQL 8.4
SHOW PROCESSLIST;                                         -- Time, State
SELECT * FROM information_schema.innodb_trx ORDER BY trx_started;   -- 오래 열린 트랜잭션
SELECT * FROM performance_schema.data_lock_waits;         -- 누가 누구를 막나
KILL QUERY <id>;   -- 문장만
KILL <id>;         -- 연결
```

## 장애 시나리오와 대처

### 1. 폭주 쿼리가 커넥션을 붙잡아 풀이 마른다

- 현상: 특정 화면을 몇 번 누르자 전체 API가 느려지고, 곧 풀 고갈 에러가 난다.
- 보이는 형태: `Connection is not available, request timed out after 30000ms`. `pg_stat_activity`에 같은 쿼리가 `active`로 여러 개, `query_age`가 수 분.
- 원인: 서버 측 `statement_timeout`이 0(기본값)이다. 앱은 요청 타임아웃으로 포기하고 재시도해 같은 쿼리를 또 올린다.
- 대처: 긴급으로 `pg_cancel_backend`. 근본으로 역할 기본 `statement_timeout`을 둔다. 요청 데드라인보다 짧게 한다. 재시도에는 상한과 백오프를 둔다.

### 2. `canceling statement due to statement timeout` (57014)

- 현상: 평소 되던 리포트 API가 특정 조건에서만 실패한다.
- 보이는 형태: `ERROR: canceling statement due to statement timeout`, SQLSTATE 57014(`query_canceled`). 클라이언트가 보낸 취소는 같은 57014이지만 메시지가 `due to user request`다.
- 원인: 한도가 제 역할을 한 것이다. 쿼리가 느려진 이유(플랜 변경·통계·인덱스 누락)를 찾아야 한다.
- 대처: 한도를 올리기 전에 `EXPLAIN (ANALYZE, BUFFERS)`로 원인을 본다([12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md)). 정말 긴 작업이면 배치 역할로 분리하거나 `SET LOCAL`로 그 트랜잭션만 늘린다.

### 3. `lock_timeout` 없는 DDL이 락 대기열 앞에 선다

- 현상: 배포의 마이그레이션 단계에서 서비스 전체가 멈춘다. DDL 자체는 아주 빠른 작업이다.
- 보이는 형태: `pg_stat_activity`에서 `ALTER TABLE`이 `wait_event_type = Lock`. 그 뒤로 같은 테이블의 SELECT가 줄줄이 `Lock` 대기이고, `pg_blocking_pids`가 DDL의 pid를 가리킨다.
- 원인: 앞에 오래 열린 트랜잭션(보통 `idle in transaction`)이 약한 락을 쥐고 있다. DDL은 `AccessExclusiveLock`을 기다리며 줄 앞에 선다. 뒤따르는 읽기는 DDL과 충돌하므로 추월하지 못한다.
- 대처: 마이그레이션 역할에 `lock_timeout = '2s'`(예시)를 두고 실패 시 재시도한다. 배포 전 오래 열린 트랜잭션을 확인한다. MySQL이면 `lock_wait_timeout`을 세션에서 짧게 둔다. 마이그레이션 일반은 [26-schema-migration](../26-schema-migration/2-summary.md).

### 4. idle in transaction — 락 유지와 vacuum 정지

- 현상: 특정 행 UPDATE가 가끔 오래 멈춘다. 테이블·인덱스 크기가 데이터 양보다 빠르게 는다.
- 보이는 형태: `pg_stat_activity.state = 'idle in transaction'`, `xact_age`가 수십 분. 타임아웃을 켜 두었다면 앱 쪽에 `FATAL: terminating connection due to idle-in-transaction timeout`(25P03)과 이어지는 I/O 에러가 보인다.
- 원인: 트랜잭션 안에서 외부 호출·사용자 입력 대기를 하거나, 예외 경로에서 커밋·롤백을 빠뜨렸다([24](../24-transaction-boundaries-in-app-code/2-summary.md)).
- 대처: 역할 기본 `idle_in_transaction_session_timeout`(예: 30초, 예시)을 둔다. 근본으로 트랜잭션 경계 안에서 외부 호출을 빼낸다.

### 5. 앱 소켓 타임아웃으로 끊어도 DB 쿼리는 계속 돈다

- 현상: 앱 로그에는 타임아웃 에러만 있는데, DB CPU는 계속 높다. 재시도 폭주가 겹치면 DB가 포화된다.
- 보이는 형태: 앱 `SocketTimeoutException: Read timed out`(pgjdbc 08006) 또는 `Communications link failure`(08S01). DB에는 같은 쿼리가 `active`로 남아 있다(§2 재현).
- 원인: 소켓 타임아웃은 서버에 아무것도 알리지 않는다. 서버는 결과를 보내려 할 때까지 끊긴 줄 모른다.
- 대처: 서버 측 `statement_timeout`을 소켓 타임아웃보다 짧게 둔다. 쿼리 타임아웃(취소 요청)을 쓴다. PostgreSQL이면 `client_connection_check_interval`을 켠다(14+). 레이어별 타임아웃 설계는 [reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md)·[09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md).

### 6. `maxLifetime`이 중간 장비 idle timeout보다 길다

- 현상·원인·대처는 [21 §장애 4](../21-connection-pooling/2-summary.md)와 같다. 이미 끊긴 커넥션을 빌려 첫 쿼리가 실패하거나 검증에서 늦어진다.
- 정렬 규칙에 넣어 한 번에 본다: `maxLifetime` < 경로상 가장 짧은 idle 한도.

## 핵심 문장

- 클라이언트 타임아웃은 "기다리기를 멈춘다"이고, 서버 타임아웃은 "일을 멈춘다"다. 소켓 타임아웃으로 끊어도 DB 쿼리는 계속 돈다.
- PostgreSQL 17의 `statement_timeout`·`lock_timeout`·`idle_in_transaction_session_timeout`은 기본 0(끔)이다. 전역 대신 **역할별 기본값**(`ALTER ROLE ... SET`)으로 켠다.
- 정렬: `lock_timeout` < `statement_timeout` < 드라이버 query timeout < `socketTimeout` < 요청 데드라인. 서버 쪽이 먼저 터져야 일이 멈추고 커넥션이 산다.
- `lock_timeout` 없는 DDL은 락 대기열 앞에 서서, 충돌하는 뒤의 모든 쿼리를 멈춘다.
- MySQL 8.4 `innodb_lock_wait_timeout`(기본 50초) 초과는 **문장만** 롤백한다. 1205를 받으면 앱이 트랜잭션을 롤백해야 한다.
- idle in transaction은 락을 쥐고 vacuum을 막는다. 타임아웃은 세션을 끊는다(25P03).

## 관련 주제·근거

- 선행
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md) — 락 모드·락 대기·교착(1213·40P01)
  - [21-connection-pooling](../21-connection-pooling/2-summary.md) — 풀 `connectionTimeout`·`maxLifetime`
- 후속·연결
  - [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md) — idle in transaction을 만드는 앱 코드
  - [16-mvcc](../16-mvcc/2-summary.md)(vacuum·bloat) · [26-schema-migration](../26-schema-migration/2-summary.md)
  - [reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md) · [09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md)
  - [network/21-tcp-keepalive-and-user-timeout](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md) — 끊긴 연결을 커널이 알아채는 방법
- 문서
  - PostgreSQL 17 문서 19.11.1 Statement Behavior(`statement_timeout`·`transaction_timeout`·`lock_timeout`·`idle_in_transaction_session_timeout`·`idle_session_timeout`) <https://www.postgresql.org/docs/17/runtime-config-client.html>
  - PostgreSQL 17 문서 19.3.1 Connection Settings(`client_connection_check_interval`) <https://www.postgresql.org/docs/17/runtime-config-connection.html> · 부록 A 에러 코드(57014·55P03·25P03)
  - PostgreSQL 소스(REL_17_STABLE): `src/backend/utils/misc/timeout.c`, `src/backend/storage/lmgr/README`(대기 큐·soft edge), `src/backend/tcop/postgres.c`(타임아웃 메시지), `src/backend/utils/errcodes.txt`(25P04·57P05)
  - Spring `spring-orm` `HibernateJpaDialect.java` · Hibernate ORM `StatementPreparerImpl.java`(`setStatementTimeout`)
  - MySQL 8.4 Reference Manual: InnoDB 시작 옵션·시스템 변수(`innodb_lock_wait_timeout`), 서버 시스템 변수(`max_execution_time`·`lock_wait_timeout`·`wait_timeout`) · MySQL 8.4 Error Reference(1205·3024)
  - pgjdbc 연결 속성(`socketTimeout`·`cancelSignalTimeout`) <https://jdbc.postgresql.org/documentation/use/> · Connector/J 연결 속성(`socketTimeout`·`connectTimeout`) <https://dev.mysql.com/doc/connector-j/en/connector-j-connp-props-networking.html>
  - node-postgres `Client` 설정 <https://node-postgres.com/apis/client> · PgBouncer 기능 표 <https://www.pgbouncer.org/features.html>
  - HikariCP README (`connectionTimeout`·`maxLifetime`)
- 로컬 재현(PostgreSQL 17.11 · MySQL 8.4.10 · pgjdbc 42.7.8 · Connector/J 8.4.0): 57014(서버 한도·클라이언트 취소), 소켓 타임아웃 뒤 서버 쿼리 잔존(PG·MySQL), `client_connection_check_interval`, DDL 락 대기열과 `lock_timeout` 55P03, idle in transaction 25P03, MySQL 1205 문장 단위 롤백, `max_execution_time` 3024, `ALTER ROLE ... SET`·`SET LOCAL`
