# database/22-database-side-timeouts — 정답

## 정답

### 1. 누가 무엇을 멈추나

- 클라이언트 타임아웃은 **기다리기**를 멈춘다. 소켓 타임아웃은 소켓을 닫을 뿐 서버에 알리지 않는다.
- 서버 타임아웃은 **일**을 멈춘다. `statement_timeout`이면 서버가 문장을 취소한다(57014).
- 그래서 앱이 포기해도 서버는 쿼리를 끝까지 돌린다. 재시도가 붙으면 같은 쿼리가 하나 더 올라와 부하가 곱절이 된다.
- 예외: 드라이버 query timeout은 서버에 **취소 요청**을 보내므로 서버 일도 멈추게 *시도*한다. 취소가 쿼리가 끝나기 전에 도착해 유효하면 문장이 57014로 중단된다. 이미 끝난 뒤 도착하면 효과가 없고, 클라이언트는 성공 여부를 직접 통보받지 못한다(문서 53.2.8).

### 2. socketTimeout vs setQueryTimeout (로컬 재현, PostgreSQL 17.11 · pgjdbc 42.7.8)

| | (a) socketTimeout=2 | (b) setQueryTimeout(2) |
|---|---|---|
| 앱이 받는 것 | 08006 `An I/O error occurred while sending to the backend` (cause `SocketTimeoutException: Read timed out`) | 57014 `canceling statement due to user request` |
| 서버 쿼리 | 2초 시점에 여전히 `active`, 6초까지 다 돈 뒤 사라짐 | 곧바로 `idle` — 취소됨 |
| 커넥션 | 닫힘(`isClosed() = true`) | 살아 있음, 같은 커넥션으로 `SELECT 1` 성공 |

- (b)의 취소는 새 연결로 CancelRequest를 보내는 방식이다(문서 53.2.8).

### 3. DDL 락 대기열

```text
  A: AccessShareLock  granted            (놀고 있음)
  B: AccessExclusiveLock  대기  ← A와 충돌
  C: AccessShareLock      대기  ← A와는 충돌 안 함, 그러나 앞선 대기자 B와 충돌
  대기 관계: C → B → A
```

- PostgreSQL 락 관리자는 새 요청을 받을 때 이미 준 락뿐 아니라 **대기 중인 요청**과도 충돌하는지 본다(lmgr README 규칙 1). 그래서 C는 도착하자마자 B 뒤에 줄 선다.
- 대기자를 깨울 때도 "이미 준 락과 충돌하지 않고, **앞선 대기자의 요청과도** 충돌하지 않을 것"을 본다(lmgr README). 도착 순서를 지키려는 규칙이다. 그래서 C는 B를 추월하지 못한다.
- 로컬 재현에서 C의 `pg_blocking_pids`는 A가 아니라 B였다.
- 막는 법:
  - DDL 세션에 `SET lock_timeout = '1s'`(예시)를 둔다. 락 획득을 최대 1초까지 기다린 뒤 55P03으로 실패하고, 재시도한다. 줄 앞에 서 있는 시간이 1초로 묶인다.
  - 배포 전에 오래 열린 트랜잭션을 정리한다.
  - `idle_in_transaction_session_timeout`으로 A 같은 세션이 생기지 않게 한다.

### 4. PostgreSQL 17 서버 한도

| 설정 | 재는 것 | 넘으면 | 기본 |
|---|---|---|---|
| `statement_timeout` | 명령이 서버에 도착한 뒤 끝날 때까지 | 문장 취소 ERROR 57014 | 0(끔) |
| `lock_timeout` | 락 획득 시도 **하나하나**의 대기 | 문장 취소 ERROR 55P03 | 0 |
| `idle_in_transaction_session_timeout` | 열린 트랜잭션 안에서 다음 쿼리를 기다린 시간 | **세션 종료** FATAL 25P03 | 0 |
| `transaction_timeout`(17 신규) | 트랜잭션 전체 길이(암묵 트랜잭션 포함, prepared transaction은 제외) | **세션 종료** FATAL 25P04 | 0 |

- `transaction_timeout`이 다른 둘보다 짧거나 같으면 긴 쪽은 무시된다(문서).

### 5. MySQL 1205

- 문서와 로컬 재현(MySQL 8.4.10) 모두 같다. InnoDB 행 락 대기(`innodb_lock_wait_timeout`)로 난 1205라면 타임아웃이 난 **문장만** 롤백되고 트랜잭션은 살아 있다(`innodb_rollback_on_timeout` 기본 OFF).
- 첫 번째 UPDATE는 트랜잭션 안에 남는다. 앱이 그대로 COMMIT하면 **첫 번째만 커밋**된다. 반쯤 된 트랜잭션이다.
- 그래서 1205를 받으면 앱이 명시적으로 ROLLBACK하고, 필요하면 처음부터 재시도한다.
- 같은 1205(`ER_LOCK_WAIT_TIMEOUT`)가 메타데이터 락 대기(`lock_wait_timeout`)에서도 난다. 그 문장이 `ALTER TABLE` 같은 DDL이면 실행 전에 이미 암묵 커밋이 일어났으므로 "트랜잭션이 살아 있다"는 설명이 맞지 않는다(MySQL 8.4 문서 15.3.3 암묵 커밋).
- 1213(교착)은 InnoDB가 희생자 트랜잭션을 **통째로** 롤백한다. 서버 SQLSTATE도 40001로, 재시도 대상임이 드러난다(1205는 HY000). 다만 Connector/J는 1205도 40001로 바꿔 올리므로 JDBC에서는 SQLSTATE로 둘을 가를 수 없고 `getErrorCode()`를 본다([56번](../56-db-symptom-index/2-summary.md) §2).

### 6. 정렬

```text
  lock_timeout < statement_timeout < 드라이버 query timeout < socketTimeout < 요청 데드라인
```

- 서버 쪽 한도가 먼저 터져야 일이 실제로 멈추고, 커넥션도 재사용된다.
- 드라이버 query timeout은 서버 한도가 없거나 더 길 때의 보조다. 취소 요청이라 (취소가 제때 도착하면) 서버 일도 멈춘다.
- socketTimeout은 서버가 응답 불능일 때의 마지막 안전핀이다. 이것이 먼저 터지면 서버 쿼리는 계속 돌고 커넥션은 버려진다.
- 요청 데드라인은 가장 길다. 안쪽 층이 모두 스스로 정리할 시간을 준다.
- `lock_timeout` ≥ `statement_timeout`이면 의미가 없다. 문장 타임아웃이 항상 먼저 터지기 때문이다(문서가 "rather pointless"라고 적는다).

### 7. 역할별 한도

- 역할·DB별 기본값을 둔다.

```sql
ALTER ROLE web_app  IN DATABASE app SET statement_timeout = '5s';
ALTER ROLE web_app  IN DATABASE app SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE batch    IN DATABASE app SET statement_timeout = '30min';
ALTER ROLE migrator IN DATABASE app SET lock_timeout = '2s';
```

- 특정 트랜잭션만 예외가 필요하면 `SET LOCAL statement_timeout = ...`. 트랜잭션이 끝나면 원래 값으로 돌아간다(로컬 재현으로 확인).
- 전역 설정을 피하는 이유: 문서가 `postgresql.conf`에 두는 것을 권하지 않는다. 백업·관리 작업까지 모든 세션에 걸린다.
- PgBouncer transaction 모드: 트랜잭션마다 다른 서버 커넥션을 받을 수 있다. 세션 `SET`이 이어진다고 기대할 수 없다(기능 표 `SET/RESET` "Never"). 역할 기본값이나 `SET LOCAL`을 쓴다.

### 8. idle in transaction

- 나빠지는 것:
  - 이 트랜잭션이 잡은 **락이 유지**된다. 같은 행을 바꾸려는 세션이 기다린다. DDL이 오면 §3의 대기열이 생긴다.
  - 열린 트랜잭션이 볼 수도 있는 옛 행 버전을 **vacuum이 지우지 못한다**. 테이블·인덱스가 부푼다(bloat).
- 타임아웃을 켜면 서버가 세션을 끊는다: `FATAL: terminating connection due to idle-in-transaction timeout`(25P03).
  - 앱은 다음 쿼리에서 I/O 에러(커넥션 끊김)를 본다.
  - 트랜잭션은 롤백된 것이다. 풀은 그 커넥션을 검증에서 버리고 새로 연다.
- 근본 원인은 앱의 트랜잭션 경계다. 트랜잭션 안에서 외부 호출을 하거나, 예외 경로에서 커밋·롤백을 빠뜨렸다([24](../24-transaction-boundaries-in-app-code/2-summary.md)).

### 9. MySQL 8.4의 한도

- `max_execution_time`은 **읽기 전용 SELECT**에만 걸린다(문서). UPDATE 폭주는 막지 못한다.
  - UPDATE가 락 때문에 멈춘다면 `innodb_lock_wait_timeout`이 대상이다.
  - 실행 자체가 긴 UPDATE는 드라이버 query timeout(KILL QUERY)이나 운영자의 `KILL QUERY`로 멈춘다.
- DDL이 기다리는 메타데이터 락은 `lock_wait_timeout`이 제한한다. 기본값은 31536000초(1년)다. `innodb_lock_wait_timeout`은 InnoDB 행 락에만 걸리고 테이블 락 대기에는 걸리지 않는다(문서).

### 10. 주인 잃은 쿼리

- 확인: `pg_stat_activity`에서 `state = 'active'`이고 `query_age`가 앱의 소켓 타임아웃보다 긴 쿼리를 찾는다. 같은 쿼리가 여러 개면 재시도가 쌓인 것이다.
- 긴급: `pg_cancel_backend(pid)`.
- 근본:
  - 역할 기본 `statement_timeout`을 소켓 타임아웃보다 짧게 둔다.
  - 소켓 타임아웃 대신 쿼리 타임아웃(취소 요청)을 쓴다.
- PostgreSQL 14+ `client_connection_check_interval`을 켠다. 쿼리 실행 중 소켓을 주기적으로 폴링하고, 커널이 연결 종료를 알려 주면 쿼리를 멈춘다.
  - 로컬 재현: 500ms로 두자 1.5초 안에 서버 쿼리가 사라졌다. 서버 로그는 `FATAL: connection to client lost`.
- 한계: 커널이 **연결 종료를 알 때만** 동작한다. 클라이언트가 소켓을 닫았으면 알 수 있다. 네트워크가 끊겨 아무 패킷도 오지 않으면 모른다. 그래서 TCP keepalive(`tcp_keepalives_*`)를 함께 맞춰야 한다고 문서가 적는다. 기본 0(끔)이다. 모든 OS에서 쓸 수 있는 것도 아니다(Linux·macOS·illumos·BSD).
