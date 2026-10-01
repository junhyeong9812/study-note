# database/21-connection-pooling — 커넥션 풀: 크기·대기·검증, 그리고 max_connections — 정리 (힌트)

## 해결하는 문제

DB 커넥션 하나를 새로 여는 일은 비싸다.

```text
  요청마다 새 커넥션을 연다면
  앱 ──TCP 3-way──> DB
     ──TLS 핸드셰이크(쓰면)──>
     ──인증(비밀번호·SCRAM 등)──>
     ──세션 초기화(SET ...)──>
                              DB 쪽: PostgreSQL은 커넥션마다 백엔드 **프로세스**를 하나 띄운다
     ──SELECT 1건──>           (1ms짜리 쿼리 앞에 수 ms~수십 ms(예시)의 준비 비용)
     ──close──>
```

- PostgreSQL 17은 "process per user" 모델이다. 연결 요청이 오면 postmaster가 백엔드 프로세스를 새로 띄운다(PostgreSQL 17 문서 50.2 "How Connections Are Established").
- MySQL 8.4는 커넥션 관리자 스레드가 클라이언트 연결마다 **전용 스레드**를 붙인다(문서 7.1.12.1 "Connection Interfaces"). 스레드 풀 플러그인은 Enterprise 기능이다.

그래서 커넥션을 **미리 열어 두고 빌려 쓰고 돌려주는** 계층을 둔다. 이것이 커넥션 풀이다.

쉬운 예: 공용 자전거 거치대다.
- 자전거(커넥션)를 매번 사지 않는다. 거치대에서 빌리고 돌려놓는다.
- 거치대가 비면 누군가 돌려놓을 때까지 **줄을 선다**.
- 너무 오래 기다리면 포기한다(대기 타임아웃).
- 낡은 자전거는 정기적으로 교체한다(최대 수명).

똑같은 구조다.\
풀은 "커넥션 수의 상한"과 "기다리는 줄"을 함께 관리한다.

실무 예:
- Spring Boot 2.0부터 기본 풀은 HikariCP다(1.5까지는 Tomcat JDBC 풀 우선). 풀이 비면 `Connection is not available, request timed out after 30000ms`가 난다.
- 인스턴스를 늘렸더니 PostgreSQL이 새 연결을 `FATAL`로 거부한다(`remaining connection slots are reserved ...` 또는 `sorry, too many clients already`).
- 풀을 200으로 키웠더니 오히려 응답이 느려진다.

## 동작·원리

### 1. 빌리기·돌려주기·기다리기

```text
  앱 스레드들                  커넥션 풀 (maximumPoolSize = 3)              DB
                          ┌──────────────────────────────────┐
  T1 ─ getConnection() ──>│ [C1 사용중:T1] [C2 사용중:T2]     │── C1 ──> 백엔드 프로세스 1
  T2 ─ getConnection() ──>│ [C3 유휴]                        │── C2 ──> 백엔드 프로세스 2
  T3 ─ getConnection() ──>│   → C3를 T3에게                  │── C3 ──> 백엔드 프로세스 3
  T4 ─ getConnection() ──>│ 줄: T4 (connectionTimeout까지 대기)│
                          └──────────────────────────────────┘
  T1 ─ close() ──────────> C1은 닫히지 않고 풀로 돌아간다 → 기다리던 T4에게 바로 넘어간다
```

- `Connection.close()`는 풀에서 빌린 커넥션이면 **반납**이다. 보통 실제 소켓은 열린 채로 남는다.
  - 예외: 쓰는 동안 수명(`maxLifetime`)이 지났거나 제거 표시(evict)된 커넥션은 반납 때 실제로 닫힌다(HikariCP 6.3.0 `HikariPool.recycle()`).
- 풀이 꽉 찼으면 `getConnection()`이 막힌다(블로킹). `connectionTimeout`이 지나면 예외다.
  - *connectionTimeout*: 풀에서 커넥션을 기다리는 최대 시간. HikariCP 기본값 30000ms(README).
- 로컬 재현(예시, PostgreSQL 17.11, HikariCP 6.3.0): 풀 2개, `connectionTimeout` 1000ms, 세 스레드가 각각 2초짜리 쿼리를 보냈다.

```text
  t0 got conn after 3ms
  t1 got conn after 32ms
  t2 SQLTransientConnectionException: demo - Connection is not available,
     request timed out after 1000ms (total=2, active=2, idle=0, waiting=0)
```

- 괄호 안 숫자가 진단의 출발점이다. `active=2, idle=0`이면 **풀이 바닥났다**는 뜻이다.
  - 풀이 작아서일 수도 있다.
  - 커넥션을 오래 쥐는 코드 때문일 수도 있다(느린 쿼리, 트랜잭션 안 외부 호출, 누수).

### 2. 풀 크기 — "작은 풀 + 기다리는 스레드"

```text
  리틀의 법칙:  L = λ × W
    L = 동시에 쥐고 있는 커넥션 수(평균)
    λ = 초당 커넥션 대여 수
    W = 한 번 쥐는 시간

  예시: 초당 200건 × 건당 25ms 쥠 = 평균 5개가 동시에 사용 중
        → 풀 10이면 여유, 풀 5면 요동에 약함, 풀 200은 과잉
```

- 쥐는 시간 W가 늘면 필요한 커넥션 수가 비례해 는다. 쿼리가 두 배 느려지면 풀도 두 배 필요해 보인다.
- 그렇다고 풀을 키우면 DB가 더 많은 일을 **동시에** 떠안는다. DB의 CPU 코어 수는 그대로다.

```text
  DB 코어 8개
  활성 커넥션 8개   : 코어마다 쿼리 하나 → 컨텍스트 스위칭 적음
  활성 커넥션 200개 : 코어 하나에 25개가 번갈아 → 전환·캐시 오염·락 경합
                      → 개별 쿼리가 느려짐 → W 증가 → 더 많은 커넥션이 필요해 보임 (악순환)
```

- HikariCP 위키 "About Pool Sizing"은 PostgreSQL 프로젝트의 출발점 공식을 소개한다.
  - `connections = ((core_count * 2) + effective_spindle_count)`
  - 4코어·디스크 1개면 9, 반올림해 10.
  - 공식은 **출발점**이다. 위키도 부하 시험으로 그 근처를 찾으라고 한다. SSD에 대해서는 분석이 없다고 적는다.
- 위키의 공리: "스레드가 커넥션을 기다리며 줄 서 있는 **작은 풀**을 원한다."

### 3. 풀 크기의 합 ≤ DB의 연결 한도

```text
  PostgreSQL 17 (기본값)
  max_connections = 100
    └ superuser_reserved_connections = 3   (슈퍼유저 전용)
    └ reserved_connections = 0            (pg_use_reserved_connections 역할 전용, 16부터)
  일반 역할이 쓸 수 있는 자리 = 100 − 3 − 0 = 97

  앱 인스턴스 10대 × 풀 10 = 100  → 97을 넘는다 → 새 연결이 FATAL로 거부
  (배포 중 신구 인스턴스가 겹치면 순간적으로 2배)
```

- PostgreSQL 17 문서 19.3.1: `max_connections` 기본은 "typically 100", 서버 시작 때만 바꿀 수 있다.
- MySQL 8.4 기본 `max_connections`는 151이다. mysqld는 `CONNECTION_ADMIN` 권한 계정용으로 **1개를 더** 허용한다(`max_connections + 1`, 문서 B.3.2.5).
- 로컬 확인(PostgreSQL 17.11): `SHOW max_connections` → 100, `superuser_reserved_connections` → 3, `reserved_connections` → 0. MySQL 8.4.10: `@@max_connections` → 151.

### 4. 수명 규칙 — `maxLifetime` < 누군가 끊는 시간

```text
  앱 ─── 풀 ─── [L4 LB / NAT / 방화벽: idle 몇 분이면 조용히 기록 삭제] ─── DB [wait_timeout 등]

  maxLifetime  (HikariCP 기본 30분)
  ─────────────────────────────────────────>|  풀이 먼저 은퇴시킨다 → 안전
  중간 장비 idle timeout (장비마다 다름)
  ──────────────────────────>|               장비가 먼저 끊는다 → 끊긴 커넥션을 빌려 줌 → 첫 쿼리 실패
```

- HikariCP README: `maxLifetime`은 "DB나 인프라가 거는 어떤 연결 시간 한도보다 몇 초 짧게" 두라고 강하게 권한다. 기본 1800000ms(30분), 최솟값 30000ms.
  - 사용 중인 커넥션은 은퇴시키지 않는다. 반납될 때 닫힌다.
  - 한꺼번에 은퇴하지 않게 커넥션마다 수명을 조금씩 줄인다. HikariCP 6.3.0 소스(`HikariPool.java`)는 `maxLifetime`의 최대 25%까지 무작위로 뺀다.
- `keepaliveTime`(기본 2분): 유휴 커넥션을 잠깐 꺼내 `isValid()`로 찔러 본다(`connectionTestQuery`를 설정했으면 그 쿼리). 중간 장비의 idle 기록을 살려 두는 용도다. `maxLifetime`보다 작아야 한다.
- 빌려줄 때 검증: HikariCP는 마지막 사용 후 500ms가 지난 커넥션이면 빌려주기 전에 살아 있는지 확인한다(`aliveBypassWindowMs` 기본 500, `HikariPool.java`). 검증은 `validationTimeout`(기본 5000ms) 안에 끝나야 한다.
- 로컬 재현(예시, MySQL 8.4.10): 세션 `wait_timeout=2`로 두고 3.5초 쉰 뒤 쿼리를 보냈다.

```text
  풀 없이 직접:  SQLState=08S01 CommunicationsException: The client was disconnected by the
                 server because of inactivity. See wait_timeout and interactive_timeout ...
  HikariCP:     WARN PoolBase - Failed to validate connection ... Possibly consider using a
                 shorter maxLifetime value.
                 hikari borrow ok after 53ms  (죽은 커넥션을 버리고 새로 열어 줌)
```

- 한도의 종류를 구분한다.
  - 전체 연결 수명 한도(예: "연결 후 1시간이면 끊음"): `maxLifetime`을 그보다 몇 초 짧게 둔다.
  - 유휴(idle) 한도(LB·NAT idle timeout, MySQL `wait_timeout`): `keepaliveTime`을 그보다 짧게 두어 유휴 기록을 살린다. `maxLifetime`을 idle 한도보다 짧게 두는 것도 통하지만 더 보수적인 방법이다.
- 서버가 연결을 **닫고 알려 준** 경우라 검증이 잡았다. 중간 장비가 기록만 지우고 아무것도 보내지 않으면 검증 요청이 응답 없이 걸린다. 이때는 `validationTimeout`만큼 늦어진다. 그래서 검증에 기대지 말고 수명 규칙을 지킨다.

### 5. 풀 교착 — 한 스레드가 커넥션 두 개를 원할 때

```text
  풀 크기 2, 스레드 2개, 각 스레드가 "바깥 커넥션을 쥔 채 안쪽 커넥션을 하나 더" 빌림
  T1: C1 쥠 ── 두 번째 요청 대기...
  T2: C2 쥠 ── 두 번째 요청 대기...
  풀: 빈 자리 0 → 둘 다 connectionTimeout까지 기다렸다 실패 (HikariCP에서 0으로 두면 약 24.8일 — 사실상 멈춤)
```

- 로컬 재현(예시, HikariCP 6.3.0): 두 스레드 모두 `request timed out after 2000ms (total=2, active=2, idle=0, waiting=0)`.
- HikariCP 위키 "Pool-locking" 절의 최소 크기: `pool size = Tn × (Cm − 1) + 1`.
  - HikariCP 6.3.0 `HikariConfig.setConnectionTimeout(0)`은 `Integer.MAX_VALUE` ms(약 24.8일)로 바뀐다. 최솟값은 250ms다.
  - Tn = 최대 스레드 수, Cm = 한 스레드가 **동시에** 쥐는 최대 커넥션 수.
  - 예: Tn = 8, Cm = 3 → 8 × 2 + 1 = 17. 교착을 피하는 **최소값**이지 최적값이 아니다.
- 이것은 os 교착의 네 조건 그대로다. 점유 대기(바깥 커넥션을 쥔 채 대기)를 없애는 게 근본 해법이다.
  - Spring `REQUIRES_NEW`가 대표적 원인이다([24](../24-transaction-boundaries-in-app-code/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **블로킹 큐(생산자–소비자)**: 개념적으로 풀은 "유휴 커넥션 큐 + 기다리는 스레드 줄"이다.
  - 반납이 생산, 대여가 소비다. 큐가 비면 소비자가 잠든다.
  - 조건 변수·세마포어로 구현하는 고전 구조다([os/17 조건 변수](../../os/17-condition-variables-and-monitors/2-summary.md), [os/18 세마포어](../../os/18-semaphores/2-summary.md)).
- **HikariCP `ConcurrentBag`**: 블로킹 큐를 그대로 쓰지 않는다. 소스 주석은 `LinkedBlockingQueue`보다 빠르게 하려고 만든 전용 구조라고 적는다.

```text
  borrow():
   ① 내 스레드의 ThreadLocal 목록 → 최근에 내가 돌려준 커넥션부터 (락 없음)
   ② 공유 목록(CopyOnWriteArrayList) 훑기 → 상태를 CAS로 NOT_IN_USE → IN_USE
   ③ 없으면 SynchronousQueue(handoffQueue)에서 timeout까지 기다림
  requite() (반납):
   상태를 NOT_IN_USE로 → 기다리는 스레드가 있으면 handoffQueue로 직접 넘김
```

  - *CAS(compare-and-set)*: "값이 아직 X면 Y로 바꿔라"를 원자적으로 하는 CPU 명령. 락 없이 한 커넥션을 두 스레드가 동시에 가져가지 못하게 한다.
  - 커넥션마다 상태 값 4개: `NOT_IN_USE`(0)·`IN_USE`(1)·`REMOVED`(-1)·`RESERVED`(-2).
- **지연 작업 큐(타이머)**: `maxLifetime`·`keepaliveTime`·누수 탐지는 커넥션마다 걸어 두는 예약 작업이다. HikariCP는 `ScheduledExecutorService`에 맡긴다(`HikariPool.java`, `ProxyLeakTask.java`). JDK의 `ScheduledThreadPoolExecutor`는 만료 시각 순 힙(`DelayedWorkQueue`)을 쓴다.
- **리틀의 법칙**: 풀 크기 추정([math 영역](../../math/README.md)의 10-queueing-and-littles-law — 미작성).

## 적용 — 풀어나가는 법

### 1. 설정의 뼈대 (Java, HikariCP)

```java
HikariConfig c = new HikariConfig();
c.setJdbcUrl("jdbc:postgresql://db:5432/app");
c.setMaximumPoolSize(10);          // 기본 10. 부하 시험으로 정한다
// minimumIdle 미설정 → maximumPoolSize와 같음(고정 크기 풀, README 권장)
c.setConnectionTimeout(3_000);     // 기본 30s. 사용자 요청 경로면 짧게 → 빨리 실패
c.setValidationTimeout(1_000);     // 기본 5s. README: connectionTimeout보다 작아야 한다
c.setMaxLifetime(25 * 60_000);     // DB·인프라의 연결 수명 한도보다 몇 초 이상 짧게
c.setKeepaliveTime(2 * 60_000);    // 기본 2분. maxLifetime보다, 중간 장비 idle 한도보다 작게
c.setLeakDetectionThreshold(20_000); // 20초 넘게 안 돌아온 커넥션 → 스택과 함께 경고
HikariDataSource ds = new HikariDataSource(c);
```

- `leakDetectionThreshold`가 넘으면 `Connection leak detection triggered for ... on thread ..., stack trace follows` 경고가 찍힌다(HikariCP `ProxyLeakTask.java`). 기본 0(꺼짐), 켜려면 2000ms 이상.

### 2. TS (node-postgres)

```ts
import { Pool } from "pg";
const pool = new Pool({
  max: 10,                        // 기본 10
  idleTimeoutMillis: 10_000,      // 기본 10초 — 유휴 클라이언트를 닫음
  connectionTimeoutMillis: 3_000, // 기본 0 = 타임아웃 없음 → 무한 대기 위험
  maxLifetimeSeconds: 1500,       // 연결 최대 수명
});
const client = await pool.connect();
try { await client.query("SELECT 1"); } finally { client.release(); } // release 누락 = 누수
```

- node-postgres 문서는 `connectionTimeoutMillis` 기본값이 0(타임아웃 없음)이라고 적는다.
  - pg-pool 소스(`packages/pg-pool/index.js`)를 보면, 풀이 꽉 찼을 때 이 값이 0이면 요청을 대기 큐에 **무기한** 넣는다.
  - 값이 있으면 그 시간 뒤 `timeout exceeded when trying to connect` 에러로 끝낸다.
  - 설정하지 않으면 풀 고갈이 에러가 아니라 "응답 없음"으로 드러난다.

### 3. 예산 계산 순서

1. DB 한도에서 시작한다. PostgreSQL이면 `max_connections − superuser_reserved_connections − reserved_connections − 운영용 여유`.
2. 그 안을 **모든 클라이언트**가 나눠 쓴다. 앱 인스턴스, 배치, 마이그레이션 도구, 모니터링, 배포 중 겹치는 구 인스턴스까지 센다.
3. 인스턴스당 풀 = 예산 ÷ 최대 인스턴스 수. 오토스케일 최대치로 나눈다.
4. 모자라면 풀을 키우지 말고 앞단에 커넥션 풀러를 둔다.
   - PgBouncer `pool_mode=transaction`: 트랜잭션이 끝나면 서버 커넥션을 다른 클라이언트에게 넘긴다.
   - 대가: 세션 상태가 공유되지 않는다. PgBouncer 기능 표에서 transaction 모드는 `SET/RESET`·세션 수준 advisory lock을 "Never"로 표시한다.

### 4. 진단 SQL

```sql
-- PostgreSQL: 누가 몇 개를 어떤 상태로 쥐고 있나
SELECT application_name, usename, state, count(*)
FROM pg_stat_activity
WHERE backend_type = 'client backend'
GROUP BY 1, 2, 3 ORDER BY 4 DESC;
-- state = 'idle in transaction' 이 많으면: 트랜잭션을 연 채 앱이 딴 일을 한다 (22·24번)

SHOW max_connections;  SHOW superuser_reserved_connections;
```

```sql
-- MySQL 8.4
SHOW GLOBAL STATUS LIKE 'Threads_connected';
SHOW GLOBAL STATUS LIKE 'Max_used_connections';   -- 기동 후 최대 동시 연결
SHOW PROCESSLIST;                                  -- Command = Sleep 은 유휴 *세션* (풀 유휴분인지 앱이 쥔 채 노는지는 풀 지표와 대조)
```

- 풀 쪽 지표(Micrometer, HikariCP 6.3.0 소스 이름): `hikaricp.connections.active`·`.idle`·`.pending`(대기 스레드 수)·`.timeout`(대여 실패 수)·`.acquire`(대여 대기 시간)·`.usage`(쥔 시간).
  - `pending`이 0보다 큰 상태가 이어지고 `usage`가 늘었다면, 풀을 키우기 전에 **쥔 시간**부터 줄인다.

## 장애 시나리오와 대처

### 1. 풀 고갈 — `Connection is not available`

- 현상: 요청이 30초(기본값) 멈춘 뒤 한꺼번에 실패한다. DB CPU는 한가할 수도 있다.
- 보이는 형태: `HikariPool-1 - Connection is not available, request timed out after 30000ms (total=10, active=10, idle=0, waiting=37)`. Spring `DataSourceTransactionManager`면 `CannotCreateTransactionException: Could not open JDBC Connection for transaction`으로 감싸진다. 지표 `hikaricp.connections.pending` 급증.
- 원인: 커넥션을 오래 쥐는 코드다. 느린 쿼리, 트랜잭션 안 HTTP 호출([24](../24-transaction-boundaries-in-app-code/2-summary.md)), 반납 누락(누수), 락 대기([22](../22-database-side-timeouts/2-summary.md)).
- 대처:
  - 긴급: `pg_stat_activity`에서 오래된 `active`·`idle in transaction`을 찾는다. 원인 세션만 `pg_cancel_backend`·`pg_terminate_backend`로 정리한다.
  - 근본: 쥔 시간을 줄인다. 누수 탐지를 켠다. 서버 측 타임아웃으로 상한을 둔다(22).
  - `connectionTimeout`을 짧게 해 빨리 실패하게 한다. 풀 크기를 무작정 키우지 않는다.

### 2. DB 연결 한도 초과 — `too many clients`

- 현상: 새 인스턴스가 기동에 실패한다. 배포·오토스케일 직후에 난다.
- 보이는 형태: PostgreSQL은 SQLSTATE 53300(`too_many_connections`)이고 문구는 두 가지다.
  - 일반 역할이 예약분만 남은 자리에 들어오면: `FATAL:  remaining connection slots are reserved for roles with the SUPERUSER attribute`(PostgreSQL 17 소스 `src/backend/utils/init/postinit.c`). 기본 설정의 앱 계정은 보통 이 문구를 먼저 본다.
  - `max_connections` 자리가 전부 찼으면: `FATAL:  sorry, too many clients already`(소스 `src/backend/storage/lmgr/proc.c`의 `InitProcess`). 앱이 슈퍼유저로 붙는 경우 등.
  - MySQL `ERROR 1040 (08004): Too many connections`.
- 원인: 인스턴스 수 × 풀 크기 + 배치·도구 커넥션이 한도를 넘었다. 배포 중 신구 인스턴스가 겹쳐 순간 2배가 되기도 한다.
- 대처: §적용 3의 예산 계산을 다시 한다. `max_connections`를 올리는 것은 마지막 수단이다. PostgreSQL은 이 값에 비례해 공유 메모리 등 자원을 잡고, 바꾸려면 재시작해야 한다(문서 19.3.1). 앞단 풀러(PgBouncer)로 서버 커넥션 수를 줄인다.

### 3. 풀이 너무 커서 느려진다

- 현상: 풀을 50 → 200으로 키웠더니 처리량은 그대로이고 p99는 나빠졌다.
- 보이는 형태: DB CPU 100%, 실행 대기(run queue) 증가, `pg_stat_activity`의 `active` 수가 코어 수의 몇 배다. 락 대기 이벤트(`wait_event_type = 'Lock'`·`'LWLock'`)가 는다.
- 원인: 동시 실행이 코어 수를 크게 넘어 전환·경합 비용이 늘었다. 쿼리 하나하나가 느려져 쥔 시간 W가 늘고, 풀이 더 필요해 보이는 악순환이다.
- 대처: 풀을 줄여 앱 쪽 줄에서 기다리게 한다(위키의 "작은 풀" 공리). 부하 시험으로 `(코어 × 2) + 스핀들` 근처를 찾는다.

### 4. 끊긴 커넥션을 빌려준다 — `maxLifetime` > 중간 장비 idle timeout

- 현상: 한가한 새벽 뒤 첫 요청 몇 개만 실패하거나, 수 초씩 늦다.
- 보이는 형태: `Communications link failure`(MySQL, 08S01), `An I/O error occurred while sending to the backend`(PostgreSQL JDBC, 08006), HikariCP 경고 `Failed to validate connection ... Possibly consider using a shorter maxLifetime value.`
- 원인: LB·NAT·방화벽·DB(`wait_timeout` 기본 28800초, MySQL 8.4)가 풀보다 먼저 연결을 끊었다. 조용히 기록만 지운 경우 검증 요청이 응답 없이 걸려 `validationTimeout`만큼 늦다.
- 대처: idle 한도에는 `keepaliveTime`을 그보다 짧게 두어 유휴 커넥션을 주기적으로 찌른다(또는 `maxLifetime`을 idle 한도보다 짧게). 연결 수명 한도에는 `maxLifetime`을 그보다 몇 초 이상 짧게 둔다. TCP keepalive 설정은 [network/21](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md)을 본다.

### 5. 풀 교착 — 커넥션을 쥔 채 커넥션을 기다린다

- 현상: 부하가 몰릴 때만 전체가 멈춘다. DB는 한가하고 교착 탐지도 조용하다.
- 보이는 형태: 모든 스레드 덤프가 `HikariPool.getConnection`에서 대기 중이다. 몇 초 뒤 `Connection is not available`이 한꺼번에 난다.
- 원인: 한 스레드가 커넥션을 쥔 채 두 번째를 빌린다. `REQUIRES_NEW`, 트랜잭션 안에서 별도 `DataSource` 호출 등이 원인이다. 대기의 한쪽 끝이 앱(풀)에 있어서 DB의 교착 탐지기는 볼 수 없다.
- 대처: 한 스레드가 커넥션 하나만 쥐게 코드를 바꾼다. 불가피하면 풀 크기를 `Tn × (Cm − 1) + 1` 이상으로 둔다.

## 핵심 문장

- 풀은 커넥션 생성 비용을 없애고 **동시 커넥션 수에 상한과 대기 줄**을 준다. 풀이 비면 스레드는 `connectionTimeout`까지 기다린다.
- 필요한 커넥션 수는 "초당 대여 수 × 쥔 시간"이다. 풀이 모자라 보이면 풀을 키우기 전에 **쥔 시간**을 줄인다.
- 풀을 키우면 DB가 코어 수보다 훨씬 많은 일을 동시에 떠안아 오히려 느려질 수 있다. 작은 풀과 앱 쪽 대기 줄이 기본이다.
- 모든 클라이언트의 풀 합은 DB 연결 한도(PostgreSQL 17 기본 `max_connections` 100에서 예약 3을 뺀 97) 안에 들어가야 한다.
- `maxLifetime`은 경로상 누군가(LB·NAT·DB)가 거는 연결 수명 한도보다 짧아야 하고, idle 한도는 `keepaliveTime`(또는 더 짧은 `maxLifetime`)으로 피한다. 아니면 끊긴 커넥션을 빌려준다.
- 커넥션을 쥔 채 커넥션을 더 빌리면 풀 교착이 난다. DB는 이 교착을 탐지하지 못한다.

## 관련 주제·근거

- 선행
  - [13-transactions-acid](../13-transactions-acid/2-summary.md)
  - math/10-queueing-and-littles-law — 미작성([math 영역 표](../../math/README.md))
- 후속·연결
  - [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md) — 서버 측 시간 한도와 풀 설정의 정렬
  - [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md) — 트랜잭션 안 외부 호출·`REQUIRES_NEW`가 풀을 말리는 경로
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md) — DB 안의 교착(풀 교착과 비교)
  - [os/19-deadlock](../../os/19-deadlock/2-summary.md) — 교착 네 조건
  - [os/17-condition-variables-and-monitors](../../os/17-condition-variables-and-monitors/2-summary.md) — 블로킹 큐의 바탕
  - [network/21-tcp-keepalive-and-user-timeout](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md) · [network/11-nat-and-conntrack](../../network/11-nat-and-conntrack/2-summary.md) — 중간 장비 idle timeout
- 문서
  - HikariCP README(설정 표: `connectionTimeout`·`idleTimeout`·`keepaliveTime`·`maxLifetime`·`minimumIdle`·`maximumPoolSize`·`validationTimeout`·`leakDetectionThreshold`) <https://github.com/brettwooldridge/HikariCP>
  - HikariCP wiki "About Pool Sizing"(공식·공리·Pool-locking) <https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing>
  - HikariCP 소스(6.3.0 태그): `pool/HikariPool.java`(timeout 메시지, `aliveBypassWindowMs`, 수명 편차), `util/ConcurrentBag.java`, `pool/ProxyLeakTask.java`, `metrics/micrometer/MicrometerMetricsTracker.java`
  - PostgreSQL 17 문서 19.3.1 Connection Settings(`max_connections`·`reserved_connections`·`superuser_reserved_connections`) <https://www.postgresql.org/docs/17/runtime-config-connection.html> · 50.2 How Connections Are Established <https://www.postgresql.org/docs/17/connect-estab.html> · 부록 A 에러 코드(53300)
  - PostgreSQL 소스 `src/backend/storage/lmgr/proc.c`(REL_17_STABLE) — "sorry, too many clients already" · `src/backend/utils/init/postinit.c` — "remaining connection slots are reserved for roles with the SUPERUSER attribute"
  - MySQL 8.4 Reference Manual B.3.2.5 Too many connections · 서버 시스템 변수(`max_connections`·`wait_timeout`) · MySQL 8.4 Error Reference(1040 `ER_CON_COUNT_ERROR`)
  - node-postgres `Pool` API <https://node-postgres.com/apis/pool>
  - PgBouncer 설정(`pool_mode`)·기능 표 <https://www.pgbouncer.org/config.html> · <https://www.pgbouncer.org/features.html>
- 로컬 재현(PostgreSQL 17.11 · MySQL 8.4.10 · HikariCP 6.3.0 · pgjdbc 42.7.8 · Connector/J 8.4.0): 풀 고갈 메시지, 풀 교착, `wait_timeout`으로 끊긴 커넥션과 풀 검증, 기본값 조회
