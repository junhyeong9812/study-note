# database/21-connection-pooling — 정답

## 정답

### 1. 커넥션 생성 비용

- 새 커넥션 하나에 드는 일: TCP 3-way 핸드셰이크 → (쓰면) TLS 핸드셰이크 → 인증 → 세션 초기화. 짧은 쿼리 하나보다 준비가 더 길 수 있다.
- 서버 쪽 처리 단위:
  - PostgreSQL 17: "process per user". postmaster가 연결마다 **백엔드 프로세스**를 새로 띄운다(문서 50.2).
  - MySQL 8.4: 커넥션 관리자 스레드가 연결마다 **전용 스레드**를 붙인다(문서 7.1.12.1).
- 그래서 미리 열어 둔 커넥션을 빌려 쓰고 돌려주는 풀을 둔다.

### 2. 네 번째 스레드

```text
  T1 C1 / T2 C2 / T3 C3 → 풀 빈 자리 0
  T4: getConnection() 에서 막힘 → connectionTimeout(HikariCP 기본 30s)까지 대기
  T1: close() → C1이 풀로 반납 → 기다리던 T4에게 넘어감
```

- 풀에서 빌린 커넥션의 `close()`는 **반납**이다. 보통 실제 소켓은 열린 채로 남는다(쓰는 동안 수명이 지났거나 제거 표시된 커넥션은 반납 때 닫힌다).
- 30초 안에 반납이 없으면 T4는 `SQLTransientConnectionException: ... Connection is not available, request timed out after 30000ms`를 받는다.

### 3. 리틀의 법칙

- L = λ × W = 400/s × 0.020s = **8개**.
- 60ms가 되면 400 × 0.060 = **24개**.
- 풀을 24 이상으로 키우면 DB가 최대 24개까지 동시에 실행할 수 있다(실제 동시 실행 수는 `pg_stat_activity`의 `active`로 따로 잰다). DB 코어 수가 그대로면 쿼리마다 더 느려진다. W가 또 늘어 더 많은 커넥션이 필요해 보이는 악순환이 된다.
- 먼저 할 일은 **왜 W가 늘었나**를 찾는 것이다(느린 쿼리, 락 대기, 트랜잭션 안 외부 호출).

### 4. 연결 예산

- PostgreSQL 17 기본값: `max_connections` 100 − `superuser_reserved_connections` 3 − `reserved_connections` 0 = **97**.
- 배치 5 + 모니터링 2 = 7. 97 − 7 = 90. 운영자 접속 여유를 조금 남긴다.
- 인스턴스 12대로 나누면 90 ÷ 12 = 7.5 → **인스턴스당 7**.
- 배포 중 신구 인스턴스가 겹치면 순간 인스턴스 수가 더 늘 수 있다. 롤링 배포의 최대 동시 인스턴스 수로 나눠야 안전하다.

### 5. `maxLifetime`의 상한

- DB·인프라가 거는 **연결 수명 한도**보다 몇 초 이상 짧아야 한다. HikariCP README가 "몇 초 짧게"를 강하게 권한다.
- LB·NAT·방화벽의 idle timeout, DB의 `wait_timeout`(MySQL 8.4 기본 28800초) 같은 **유휴 한도**는 `keepaliveTime`을 그보다 짧게 두어 피한다. `maxLifetime`을 그보다 짧게 두는 것도 통한다(더 보수적).
- 반대로 두면: 이미 끊긴 커넥션을 빌려준다. 첫 쿼리가 `Communications link failure`(08S01)나 `An I/O error occurred while sending to the backend`(08006)로 실패한다.
- 검증이 있어도 늦어지는 이유:
  - HikariCP는 마지막 사용 후 500ms가 지난 커넥션을 빌려주기 전에 `isValid()`로 확인한다(`connectionTestQuery`를 설정했으면 그 쿼리).
  - 서버가 연결을 닫고 알린 경우는 바로 잡힌다. 로컬 재현(MySQL `wait_timeout=2`)에서도 경고를 남기고 새 커넥션으로 바꿔 53ms 만에 빌려줬다.
  - 중간 장비가 기록만 지우고 아무것도 보내지 않으면 검증 요청에 응답이 없다. `validationTimeout`(기본 5000ms)만큼 기다린 뒤에야 버린다.

### 6. 풀 교착

- 둘 다 첫 커넥션을 쥔 채 두 번째를 기다린다. 풀에 빈 자리가 없어 아무도 진행하지 못한다.
  - 로컬 재현: 두 스레드 모두 `request timed out after 2000ms (total=2, active=2, idle=0, waiting=0)`.
  - HikariCP에서 `connectionTimeout`을 0으로 두면 `Integer.MAX_VALUE` ms(약 24.8일)가 되어 사실상 영원히 멈춘다.
- 최소 풀 크기(HikariCP 위키 Pool-locking): `Tn × (Cm − 1) + 1` = 8 × (3 − 1) + 1 = **17**.
  - 교착을 피하는 최소값일 뿐 최적값이 아니다.
  - 근본 해법은 한 스레드가 커넥션 하나만 쥐게 하는 것이다(점유 대기 제거).

### 7. 자료구조

- 개념적으로 **블로킹 큐**(생산자–소비자)다. 반납이 생산, 대여가 소비다. 비면 소비자가 잠든다.
- HikariCP `ConcurrentBag`의 `borrow()` 순서(6.3.0 소스):
  1. 현재 스레드의 ThreadLocal 목록(최근에 내가 반납한 것) — 락 없이 CAS로 상태를 `NOT_IN_USE → IN_USE`.
  2. 공유 `CopyOnWriteArrayList` 전체를 훑으며 CAS.
  3. 없으면 `SynchronousQueue`(handoffQueue)에서 timeout까지 기다린다. 반납하는 쪽이 기다리는 스레드에게 직접 건넨다.

### 8. 풀 고갈 로그 읽기

- `total=10, active=10, idle=0`: 풀 10개가 전부 대여 중이다. `waiting=37`: 37개 스레드가 줄 서 있다.
- 확인 순서:
  1. **누가 오래 쥐나**: DB에서 `pg_stat_activity`를 `state`·`now() - xact_start` 순으로 본다. `active`로 오래 도는 쿼리인가, `idle in transaction`인가?
  2. `idle in transaction`이 많으면 트랜잭션 안에서 앱이 딴 일을 한다(외부 HTTP 호출 등, [24](../24-transaction-boundaries-in-app-code/2-summary.md)).
  3. `active`이고 `wait_event_type = 'Lock'`이면 락 대기다. `pg_blocking_pids()`로 막는 쪽을 찾는다([22](../22-database-side-timeouts/2-summary.md)).
  4. DB 쪽 세션이 적은데 풀이 비었다면 누수다. `leakDetectionThreshold`를 켜서 반납하지 않은 스택을 찾는다.
- 대처: 원인 세션 정리 → 쥔 시간 단축 → 서버 측 타임아웃으로 상한 → `connectionTimeout` 단축(빨리 실패). 풀을 키우는 것은 마지막이다.

### 9. `too many clients`

- PostgreSQL `FATAL: sorry, too many clients already`의 SQLSTATE는 **53300**(`too_many_connections`)이다. 소스 `proc.c`의 `InitProcess`가 낸다.
  - 같은 53300이 문구만 다르게 나오기도 한다. 기본 설정(`superuser_reserved_connections` 3)에서 일반 역할인 앱 계정은 97번째를 넘기는 순간 `remaining connection slots are reserved for roles with the SUPERUSER attribute`를 먼저 받는다(`postinit.c`). `sorry, too many clients already`는 100자리가 전부 찼을 때다.
- MySQL 8.4에서 같은 상황은 `ERROR 1040 (08004): Too many connections`이다.
- `max_connections`를 올리는 대신 할 일:
  - 모든 클라이언트의 풀 합을 다시 계산한다. 오토스케일 최대치와 배포 중 겹침까지 넣는다.
  - 인스턴스당 풀을 줄인다(대부분 풀이 과하다).
  - PgBouncer 같은 앞단 풀러를 `transaction` 모드로 둔다. 서버 커넥션 수를 클라이언트 수와 분리한다. 대신 세션 상태(`SET`·세션 advisory lock)를 쓸 수 없다.
- `max_connections`는 서버 재시작이 필요하다. 값에 비례해 공유 메모리 등 자원을 더 잡는다(문서 19.3.1).

### 10. node-postgres 기본값

- `connectionTimeoutMillis` 기본값은 0(타임아웃 없음)이다.
- pg-pool 소스에서 이 값이 0이면, 풀이 꽉 찼을 때 요청을 대기 큐에 **무기한** 넣는다. 에러 없이 요청이 계속 쌓이고 응답만 멈춘다.
- `connectionTimeoutMillis`를 주면 그 시간 뒤 `timeout exceeded when trying to connect`로 실패한다. `client.release()`는 `finally`에서 부른다(누수 방지).
