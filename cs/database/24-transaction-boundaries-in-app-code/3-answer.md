# database/24-transaction-boundaries-in-app-code — 정답

## 정답

### 1. 프록시의 일

```text
  호출자 → 프록시(CGLIB 서브클래스, 예: Svc$$SpringCGLIB$$0)
    ① 트랜잭션 속성 읽기(전파·격리·readOnly·timeout·롤백 규칙)
    ② 풀에서 커넥션 대여 → setAutoCommit(false)
    ③ (DataSource → 커넥션)을 현재 스레드의 ThreadLocal에 묶음
    ④ 진짜 메서드 실행 — JdbcTemplate 등은 스레드에 묶인 커넥션을 꺼내 씀
    ⑤ 정상 → commit / 롤백 규칙 예외 → rollback
    ⑥ 스레드에서 떼고 커넥션 반납
```

- DAO는 `DataSource`를 키로 스레드 로컬 맵(`TransactionSynchronizationManager`)을 조회해 같은 커넥션을 찾는다.

### 2. 자기 호출

- `doWork()` 안에서 트랜잭션은 **활성이 아니다**. 에러도 나지 않는다. 로컬 재현에서 `doWork() inTx=false`였다.
- `this`는 프록시가 아니라 진짜 객체라서 가로챌 자리가 없다. Spring 문서: 프록시 모드에서는 외부에서 프록시로 들어오는 호출만 가로챈다.
- 고치는 법:
  1. `doWork()`를 다른 빈으로 옮긴다.
  2. `TransactionTemplate.execute(...)`로 경계를 코드에 명시한다.
  3. AspectJ 모드(바이트코드 위빙)로 바꾼다.

### 3. 롤백 규칙

- `IOException`(checked): 기본 설정에서는 롤백하지 않는다 → INSERT가 **커밋**된다. 로컬 재현 `rows in audit: [checked]`.
- `IllegalStateException`(RuntimeException): 롤백.
- 바꾸는 법: `@Transactional(rollbackFor = Exception.class)`. 또는 checked 예외를 unchecked 도메인 예외로 감싸 던진다.

### 4. 삼킨 안쪽 예외

- 커밋되지 않는다. B가 참여 트랜잭션에 rollback-only 표시를 남겼다. A가 커밋을 요청해도 실제로는 롤백된다.
- 예외: `UnexpectedRollbackException: Transaction rolled back because it has been marked as rollback-only`(로컬 재현). DEBUG 로그에는 `Participating transaction failed - marking existing transaction as rollback-only`가 먼저 찍힌다.
- 설계 이유(Spring 문서): 호출자가 "커밋됐다"고 잘못 믿지 않게 한다. 조용히 롤백하면 호출자는 성공으로 착각한다.
- B의 실패를 A와 분리하려면 B를 `REQUIRES_NEW`나 `NESTED`로 둔다.

### 5. REQUIRES_NEW 자기 교착

- 안쪽 새 트랜잭션이 바깥이 잡은 행 락을 기다린다. 바깥은 자바 호출 스택에서 안쪽이 끝나기를 기다린다. 서로를 기다린다.
- DB가 풀어 주지 않는 이유: DB의 wait-for 그래프에는 "안쪽 → 바깥"(락 대기) 간선만 있다. "바깥 → 안쪽" 대기는 JVM 안에 있어서 DB가 보지 못한다. 사이클이 없으니 교착 탐지(`deadlock_timeout` 기본 1초 뒤 검사)가 아무것도 찾지 못한다.
- 결과: `lock_timeout`이 있으면 55P03(`canceling statement due to lock timeout`, 로컬 재현), 없으면 `statement_timeout`까지 기다린다. 바깥 세션은 DB 입장에서 `idle in transaction`이라 `idle_in_transaction_session_timeout`·`transaction_timeout`(PostgreSQL 17 신설)이 바깥을 끊어 풀 수도 있다. 아무것도 없으면 무한 대기.

### 6. 풀 크기

- 스레드마다 동시에 최대 2개를 쥔다(Cm = 2). HikariCP 위키 공식 `Tn × (Cm − 1) + 1` = 20 × 1 + 1 = **21**.
- Spring 문서 권고도 같은 말이다. 풀이 동시 스레드 수보다 **최소 1** 커야 한다. 그보다 작으면 모든 스레드가 바깥 커넥션을 쥔 채 안쪽 커넥션을 기다리는 교착이 날 수 있다.

### 7. readOnly

- 기본은 **힌트**다. javadoc: 쓰기 시도가 반드시 실패하는 것은 아니고, 해석하지 못하는 매니저는 조용히 무시한다.
- `DataSourceTransactionManager` + pgjdbc + PostgreSQL:
  - 매니저가 `Connection.setReadOnly(true)`를 부른다.
  - pgjdbc `readOnlyMode` 기본값 `transaction`이 `BEGIN READ ONLY`를 보낸다.
  - PostgreSQL이 거부한다: `ERROR: cannot execute INSERT in a read-only transaction`(로컬 재현).
- `JpaTransactionManager` + Hibernate:
  - Spring 6.2 `HibernateJpaDialect`가 flush 모드를 `MANUAL`로 바꾸고, 트랜잭션 로컬 EntityManager면 `setDefaultReadOnly(true)`를 부른다.
  - 더티 체킹 대상이 줄고 커밋 때 flush하지 않는다. `prepareConnection`(기본 true)이 켜져 있고 Hibernate 커넥션 해제 모드가 `ON_CLOSE`일 때는 JDBC 커넥션에도 read-only가 전달된다(같은 소스의 조건문).
- REQUIRED로 **참여**하는 안쪽 메서드의 readOnly는 조용히 무시된다(바깥 설정을 따른다).

### 8. 커밋 후 메일

- 동작: `afterCommit`·`@TransactionalEventListener`(기본 `AFTER_COMMIT`)는 커밋이 성공한 뒤에만 실행된다. 롤백이면 실행되지 않는다(로컬 재현: 실패 경로는 `afterCompletion status=ROLLED_BACK`만).
- 주의점:
  1. 트랜잭션이 없으면 `@TransactionalEventListener`는 호출되지 않는다(`fallbackExecution` 기본 false).
  2. `afterCommit` 시점에도 자원이 묶여 있다. 여기서 DB에 쓰면 원래 트랜잭션에 참여해 **커밋되지 않는다**. `REQUIRES_NEW`를 쓰라고 javadoc이 적는다.
  3. 여기서 던진 예외는 호출자에게 가지만, DB 커밋은 이미 끝났다.
- "반드시" 보내야 한다면: 훅은 메모리 안의 약속이라 커밋 직후 프로세스가 죽으면 사라진다. 같은 트랜잭션에 발송할 메시지를 **outbox 행**으로 넣고, 별도 발송기가 읽어 보낸다. 발송은 최소 한 번이 되므로 수신 쪽은 멱등이어야 한다.

### 9. 트랜잭션 안 외부 호출

- DB에서 보이는 것: `pg_stat_activity`에 `idle in transaction` 세션이 풀 크기만큼 있다. `idle_for`가 결제사 지연만큼 길다.
- 이유: 트랜잭션 안에서 결제 API를 기다리는 동안 커넥션을 쥔다. 결제와 무관한 API도 같은 풀을 쓰므로 함께 굶는다. 로컬 재현(풀 2, 3초 대기 요청 4개)에서 2개가 `Could not open JDBC Connection for transaction`으로 실패했다.
- 고치기:
  - 외부 호출을 트랜잭션 밖으로 뺀다. 파사드가 먼저 결제를 부르고, 결과를 들고 짧은 트랜잭션 빈을 부른다.
  - 외부 호출 클라이언트에 짧은 타임아웃을 둔다.
  - 서버 측 `idle_in_transaction_session_timeout`으로 상한을 둔다.

### 10. 다른 스레드

- 포함되지 **않는다**. 트랜잭션 컨텍스트(커넥션 홀더)는 호출한 스레드의 ThreadLocal에 묶여 있다(JDBC·JPA 명령형 경로. 반응형 트랜잭션은 Reactor 컨텍스트를 쓴다).
- `@Async` 메서드나 병렬 스트림의 작업자 스레드에는 그 컨텍스트가 없다. 그곳의 DB 호출은 트랜잭션 없이, 또는 자기 트랜잭션으로 **다른 커넥션**에서 실행된다.
- 병렬 스트림은 호출 스레드도 일부 요소를 처리한다. 그 요소만 바깥 트랜잭션에 들어가고 작업자 스레드가 처리한 나머지는 빠진다. 결과가 요소마다 섞인다.
- 그래서 바깥이 롤백돼도 그 쓰기는 남을 수 있다. 바깥 트랜잭션이 아직 커밋하지 않은 데이터도 보이지 않는다.
