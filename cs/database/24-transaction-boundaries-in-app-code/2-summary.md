# database/24-transaction-boundaries-in-app-code — 앱 코드의 트랜잭션 경계: 프록시·전파·롤백 규칙 — 정리 (힌트)

## 해결하는 문제

DB 트랜잭션은 `BEGIN … COMMIT` 사이다. 앱 코드에서는 그 경계를 **어느 메서드가 여닫나**로 정한다.

```text
  주문하기() {
     재고 차감      ─┐
     주문 행 삽입    ├─ 이 셋이 한 트랜잭션이어야 한다 (원자성, 13번)
     포인트 차감    ─┘
     결제 API 호출  ── 이건 트랜잭션 밖이어야 한다 (커넥션·락을 쥔 채 3초 기다리지 않게)
     메일 발송      ── 이건 커밋이 확정된 뒤여야 한다 (롤백됐는데 메일이 가지 않게)
  }
```

- Spring은 `@Transactional` 한 줄로 경계를 선언하게 해 준다. 편한 대신 경계가 **코드에 보이지 않는다**.
- 그래서 경계가 틀려도 컴파일도 테스트도 조용하다. 틀린 것이 드러나는 때는 롤백이 필요한 순간이나 부하가 몰린 순간이다.

쉬운 예: 은행 창구의 "거래 시작" 버튼이다.
- 창구 직원(프록시)이 버튼을 누르고 업무를 시작한다. 끝나면 확정 버튼을 누른다.
- 직원을 거치지 않고 손님이 뒷문으로 들어오면(자기 호출) 버튼은 눌리지 않는다.
- 업무 도중 직원이 외부에 전화를 걸어 3분 기다리면, 그동안 창구(커넥션)가 묶인다.

똑같은 구조다.\
선언적 트랜잭션은 **프록시를 거친 호출**에만 걸린다. 경계 안에 둔 모든 것은 커넥션과 락을 쥔 채 실행된다.

실무 예:
- 같은 클래스 안에서 `this.save()`를 불렀더니 `@Transactional`이 **조용히 무시**됐다.
- `IOException`(checked)을 던졌는데 앞의 INSERT가 커밋됐다.
- 트랜잭션 안에서 외부 HTTP를 부르는 API가 느려지자 `Connection is not available`이 났다.

## 동작·원리

### 1. 프록시가 경계를 연다

```text
  호출자 ──> [프록시: Svc$$SpringCGLIB$$0] ──> TransactionInterceptor
                                                 │ ① 풀에서 커넥션 대여 (21번)
                                                 │ ② setAutoCommit(false)  → 트랜잭션 시작
                                                 │ ③ 커넥션을 현재 스레드에 묶음 (ThreadLocal)
                                                 ▼
                                            [진짜 Svc.method()]
                                                 │ JdbcTemplate·JPA가 스레드에 묶인 커넥션을 꺼내 씀
                                                 ▼
                                   정상 반환 → commit / 롤백 규칙에 맞는 예외 → rollback
                                   → 커넥션 풀로 반납
```

- 로컬 재현(예시, Spring Framework 6.2.11): 빈의 실제 클래스는 `TxRepro$Svc$$SpringCGLIB$$0`였다. 서브클래스 프록시다.
- 그림은 기본 구성(JDBC `DataSourceTransactionManager`, 커넥션을 바로 빌리는 DataSource)의 순서다. `LazyConnectionDataSourceProxy`를 끼우면 실제 커넥션은 첫 SQL 문장을 만들 때에야 빌린다(Spring javadoc).
- "정상 반환 → commit"에도 예외가 있다. 반환값이 실패를 담고 있으면 롤백한다(§5).
- `@Transactional`은 메타데이터일 뿐이다. `@EnableTransactionManagement` 같은 인프라가 있어야 동작한다(Spring 문서 "Using @Transactional").

### 2. 자기 호출은 프록시를 거치지 않는다

```text
  외부 ──> 프록시.outer()          (outer에는 @Transactional 없음 → 트랜잭션 없음)
               └─> 진짜.outer()
                      └─> this.doWork()   ← this = 진짜 객체, 프록시가 아님
                                            @Transactional 붙어 있어도 가로챌 자리가 없다
```

- 로컬 재현(예시):

```text
  via proxy -> outer():
    outer() inTx=false
    doWork() inTx=false      ← @Transactional 메서드인데 트랜잭션 없음
  via proxy -> doWork():
    doWork() inTx=true
```

- Spring 문서: "프록시 모드(기본)에서는 프록시를 통해 들어오는 **외부** 메서드 호출만 가로챈다. 자기 호출은 … `@Transactional`이 붙어 있어도 실제 트랜잭션이 되지 않는다."
- 고치는 법:
  - 트랜잭션 메서드를 **다른 빈**으로 옮긴다(가장 흔하다).
  - `TransactionTemplate`으로 경계를 코드에 명시한다.
  - AspectJ 모드(바이트코드 위빙)를 쓴다. 문서가 자기 호출까지 감싸려면 이 모드를 고려하라고 적는다.
- 같은 이유로 `@PostConstruct` 안에서는 기대하지 않는다(프록시가 아직 완성 전, 같은 문서).

### 3. 트랜잭션 컨텍스트 = 스레드에 묶인 자원

```text
  스레드 T1의 ThreadLocal
  ┌──────────────────────────────────────────────┐
  │ resources: { DataSource → ConnectionHolder }  │ ← 현재 트랜잭션의 커넥션
  │ synchronizations: [afterCommit 훅들 ...]       │
  │ currentTransactionReadOnly / isolation / name │
  └──────────────────────────────────────────────┘
  REQUIRES_NEW 진입 → 바깥 것을 떼어 "보류"(suspend) → 새 커넥션으로 새 트랜잭션
  REQUIRES_NEW 종료 → 안쪽 커밋·반납 → 보류했던 바깥 것을 다시 묶음(resume)
```

- `TransactionSynchronizationManager`가 이 스레드별 저장소를 관리한다(로컬 재현에서 `isActualTransactionActive()`로 확인).
- 이 절은 `PlatformTransactionManager`(JDBC·JPA) 기반 명령형 트랜잭션의 이야기다. 반응형 `ReactiveTransactionManager`는 ThreadLocal 대신 Reactor 컨텍스트에 트랜잭션을 둔다(Spring 문서 "Understanding the Spring Framework's Declarative Transaction Implementation").
- 스레드에 묶이므로 **다른 스레드로 넘어가면 트랜잭션도 끊긴다**. `@Async`, `CompletableFuture.supplyAsync` 안의 DB 호출은 바깥 트랜잭션에 참여하지 않는다.
  - 병렬 스트림은 더 헷갈린다. 종료 연산을 부른 스레드도 일부 요소를 처리한다(`ForkJoinTask.invoke()`는 현재 스레드에서 작업을 시작한다). 그래서 일부 요소만 바깥 트랜잭션에 들고 나머지는 빠진다.
- 보류→재개가 겹치면 사실상 **호출 스택 모양의 트랜잭션 스택**이 된다.

### 4. 전파 속성 — 이미 트랜잭션이 있을 때 어떻게 하나

```text
  속성            바깥 트랜잭션이 있으면                없으면
  REQUIRED(기본)   참여 (같은 물리 트랜잭션)            새로 시작
  REQUIRES_NEW    바깥을 보류, 새 커넥션으로 독립 트랜잭션   새로 시작
  NESTED          같은 트랜잭션 안 세이브포인트           새로 시작 (REQUIRED처럼)
  SUPPORTS        참여                              트랜잭션 없이 실행
  MANDATORY       참여                              예외
  NOT_SUPPORTED   바깥을 보류, 트랜잭션 없이 실행         트랜잭션 없이 실행
  NEVER           예외                              트랜잭션 없이 실행
```

**REQUIRED — 안쪽 실패가 바깥 커밋을 막는다**

- 같은 물리 트랜잭션을 공유하지만, 메서드마다 **논리** 범위가 있다.
- 안쪽이 롤백 규칙에 걸린 예외를 던지면 공유 트랜잭션에 rollback-only 표시가 붙는다. 바깥이 그 예외를 잡고 커밋을 시도해도 실제로는 롤백되고, `UnexpectedRollbackException`이 난다. 문서의 취지는 "커밋되지 않았는데 커밋됐다고 믿게 하지 않는다"이다(Spring 문서 "Transaction Propagation").
- 참여하는 안쪽의 격리 수준·타임아웃·readOnly 설정은 **조용히 무시**된다(같은 문서). `validateExistingTransaction=true`면 불일치를 거부한다.

**REQUIRES_NEW — 커넥션을 하나 더 쓴다**

- 안쪽은 독립 물리 트랜잭션이다. 따로 커밋·롤백되고, 끝나는 즉시 락을 푼다.
- 바깥 커넥션은 묶인 채 남고, 안쪽은 **풀에서 새 커넥션**을 빌린다. 문서가 직접 경고한다: 여러 스레드가 바깥 트랜잭션을 쥔 채 안쪽 커넥션을 기다리면 풀 고갈·교착이 날 수 있다. 풀 크기가 동시 스레드 수보다 최소 1 커야 한다([21 §5](../21-connection-pooling/2-summary.md)).
- 같은 행을 건드리면 **자기 교착**이다.

```text
  바깥(REQUIRED):     UPDATE account SET ... WHERE id = 1   ← 행 락 쥠, 커밋 전
  안쪽(REQUIRES_NEW):   UPDATE account SET ... WHERE id = 1   ← 바깥의 락을 기다림
  바깥은 안쪽이 돌아오기를 기다림(자바 호출 스택)
  → DB 교착 탐지기는 "안쪽 → 바깥" 간선만 본다. "바깥 → 안쪽" 대기는 JVM 안에 있다
  → 사이클이 DB에 보이지 않는다 → deadlock detected 없이 lock_timeout까지 대기
    (없으면 statement_timeout, 또는 바깥 세션을 끊는 idle_in_transaction_session_timeout·
     transaction_timeout까지. 아무것도 없으면 무한)
```

- 로컬 재현(예시, PostgreSQL 17.11, `lock_timeout=2s`): `SQL state [55P03] ... ERROR: canceling statement due to lock timeout / Where: while updating tuple (0,1) in relation "account"`.
  - `deadlock_timeout`(기본 1초)이 먼저 지났는데도 교착으로 잡히지 않았다. DB 쪽 wait-for 그래프에 사이클이 없기 때문이다([15](../15-two-phase-locking-and-deadlock/2-summary.md)).

**NESTED** — 한 물리 트랜잭션 안의 세이브포인트다. 안쪽만 부분 롤백하고 바깥은 계속할 수 있다. 문서는 JDBC 세이브포인트로 대응되므로 JDBC 자원 트랜잭션에서만 동작한다고 적고 `DataSourceTransactionManager`를 가리킨다.
  - `JpaTransactionManager`도 JDBC 세이브포인트로 NESTED를 지원한다(6.2 javadoc, `nestedTransactionAllowed` 기본 true). 다만 세이브포인트는 JDBC 커넥션에만 걸리고 JPA EntityManager와 캐시된 엔티티는 되돌리지 않는다. 그래서 javadoc도 이 값을 false로 두는 편이 낫다고 적는다(7.0부터 기본 false).

### 5. 롤백 규칙 — checked 예외는 기본적으로 커밋된다

```text
  던진 것                         기본 동작
  RuntimeException 및 하위         롤백
  Error                          롤백
  checked Exception (IOException 등)  커밋 (!)
  메서드 안에서 잡고 삼킨 예외          (프록시는 모름) 커밋
                                 — 단 안쪽 참여 범위가 rollback-only를 남겼으면 롤백(§4)
```

- Spring 문서 "Rolling Back a Declarative Transaction": 기본 설정은 런타임(unchecked) 예외에만 롤백을 표시하고, checked 예외는 롤백을 일으키지 않는다.
- 같은 문서: 예외 없이 반환해도 롤백되는 경우가 있다. 반환 시점에 이미 예외로 끝난 `CompletableFuture`(`Future`, 6.1부터)와 Vavr `Try`의 실패 값이다.
- 로컬 재현(예시): 세 메서드가 각각 `audit`에 한 행을 넣고 예외를 던졌다.

```text
  checked()               → throw new Exception      → 행 남음 (커밋됨)
  checkedRollbackFor()    → rollbackFor = Exception.class → 롤백
  unchecked()             → throw IllegalStateException → 롤백
  rows in audit: [checked]
```

- 대처: checked 예외를 쓰는 서비스는 `@Transactional(rollbackFor = Exception.class)`를 쓰거나, 도메인 예외를 unchecked로 만든다.

### 6. readOnly — 힌트이자, 드라이버에 따라 강제

- `@Transactional(readOnly = true)` javadoc: "실제 트랜잭션 하위 시스템에 주는 **힌트**다. 쓰기 시도가 반드시 실패하는 것은 아니다. 해석하지 못하는 매니저는 조용히 무시한다."
- 실제 효과는 층마다 다르다.

```text
  DataSourceTransactionManager ─ Connection.setReadOnly(true)
     └ pgjdbc(readOnlyMode 기본 "transaction") ─ BEGIN READ ONLY 전송
         └ PostgreSQL 17 ─ 쓰기 시 ERROR: cannot execute INSERT in a read-only transaction
  JpaTransactionManager + Hibernate ─ flush 모드 MANUAL, Session 기본 읽기 전용
     (더티 체킹 스냅샷을 줄이고, 커밋 때 flush하지 않음)
```

- 로컬 재현(예시, PostgreSQL 17.11 + pgjdbc 42.7.8): readOnly 메서드에서 INSERT → `UncategorizedSQLException: ERROR: cannot execute INSERT in a read-only transaction`.
- Hibernate 쪽은 Spring 6.2 소스 `HibernateJpaDialect.prepareFlushMode`가 readOnly면 `FlushMode.MANUAL`로 바꾸고, 트랜잭션 로컬 EntityManager면 `session.setDefaultReadOnly(true)`를 부른다.
  - 같은 `HibernateJpaDialect.beginTransaction`은 readOnly면 JDBC 커넥션에도 `DataSourceUtils.prepareConnectionForTransaction`으로 읽기 전용을 건다(`prepareConnection` 기본 true이고 커넥션 해제 모드가 ON_CLOSE일 때). 이 경우 pgjdbc 경로의 `BEGIN READ ONLY`도 함께 적용된다.
- `DataSourceTransactionManager.setEnforceReadOnly(true)`면 `SET TRANSACTION READ ONLY` 문을 명시적으로 보낸다(javadoc).

### 7. 커밋 후 훅 — "확정된 뒤에" 할 일

```java
@Transactional
public void placeOrder(Order o) {
    orders.save(o);
    TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
        @Override public void afterCommit() { mailer.sendConfirmation(o); }  // 커밋 성공 뒤에만
    });
}
// 또는 이벤트: @TransactionalEventListener  (기본 phase = AFTER_COMMIT)
```

- 로컬 재현(예시): 성공 경로 `afterCommit hook ran` → `afterCompletion status=COMMITTED`. 실패 경로는 `afterCommit` 없이 `afterCompletion status=ROLLED_BACK`.
- `@TransactionalEventListener`의 phase는 `BEFORE_COMMIT`·`AFTER_COMMIT`(기본)·`AFTER_ROLLBACK`·`AFTER_COMPLETION`이다. 트랜잭션이 없으면 리스너가 **호출되지 않는다**(`fallbackExecution=true`로 바꿀 수 있다, Spring 문서 "Transaction-bound Events").
- 주의 둘(`TransactionSynchronization.afterCommit` javadoc):
  - 커밋은 끝났지만 트랜잭션 자원이 아직 묶여 있다. 여기서 DB에 쓰면 원래 트랜잭션에 "참여"하고 **커밋이 따라오지 않는다**. 쓰기가 필요하면 `REQUIRES_NEW`를 쓰라고 적는다.
  - 여기서 던진 RuntimeException은 호출자에게 전파된다. 하지만 DB 커밋은 이미 끝났다.
- 커밋 후 훅은 **메모리 안의 약속**이다. 커밋 직후 프로세스가 죽으면 훅은 실행되지 않는다. "커밋되면 반드시 발행"이 필요하면 같은 트랜잭션에 발행할 메시지를 행으로 넣는 outbox를 쓴다(distributed/16-outbox-and-dual-write — 미작성, [distributed 영역 표](../../distributed/README.md)).

### 8. 트랜잭션 안에서 외부 호출을 하지 않는 이유

```text
  @Transactional
  주문하기():  SELECT ... FOR UPDATE (락)  ── 결제 API 3초 ──  UPDATE ... COMMIT
               |<──────── 커넥션 점유 + 행 락 유지 + idle in transaction ────────>|
```

- 쥔 시간 W가 외부 호출 시간만큼 늘어 필요한 커넥션 수가 비례해 는다(리틀의 법칙, [21](../21-connection-pooling/2-summary.md)).
- 외부 호출 동안 DB 입장에서는 `idle in transaction`이다. 락이 유지되고 vacuum이 막힌다([22](../22-database-side-timeouts/2-summary.md)).
- 외부 호출은 롤백되지 않는다. 결제는 됐는데 DB가 롤백되는 불일치가 생긴다.
- 로컬 재현(예시): 풀 2, `connectionTimeout` 1.5초, 트랜잭션 안에서 3초 대기하는 요청 4개를 동시에 보냈다.

```text
  req2 CannotCreateTransactionException: Could not open JDBC Connection for transaction
  req3 CannotCreateTransactionException: Could not open JDBC Connection for transaction
  req1 ok 3047ms
  req0 ok 3047ms
```

## 쓰이는 자료구조·알고리즘

- **프록시(데코레이터)**: 같은 타입의 대리 객체가 호출을 가로채 앞뒤에 트랜잭션 처리를 끼운다. CGLIB는 서브클래스를, JDK 동적 프록시는 인터페이스 구현을 만든다(software-design/33-aop-and-proxies — 미작성, [software-design 영역 표](../../software-design/README.md)).
- **스레드 로컬 맵**: `ThreadLocal<Map<Object, Object>>` 형태로 (DataSource → 커넥션 홀더)를 스레드마다 둔다. 같은 스레드 안의 모든 DAO가 같은 커넥션을 꺼낸다.
- **보류 스택**: REQUIRES_NEW·NOT_SUPPORTED가 바깥 자원을 떼어 보관했다가 되돌린다. 중첩되면 호출 스택과 같은 모양의 스택이 된다.
- **세이브포인트**: NESTED는 DB의 `SAVEPOINT`/`ROLLBACK TO SAVEPOINT`로 부분 롤백한다.
- **wait-for 그래프의 한계**: DB 교착 탐지기는 DB 안의 대기 간선만 본다. 앱이 만든 대기(커넥션을 기다리는 스레드, 호출 스택)는 그래프 밖이다([os/19-deadlock](../../os/19-deadlock/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 경계 설계 순서

1. 한 트랜잭션에 들어갈 **DB 작업만** 고른다. 불변식을 함께 지켜야 하는 쓰기들이다.
2. 외부 호출·파일·메일·메시지 발행을 경계 **밖**으로 뺀다. 앞이면 먼저 하고, 뒤면 커밋 후(훅·outbox)로 옮긴다.
3. 경계를 여는 메서드는 **서비스 빈의 public 메서드 하나**로 둔다. 자기 호출이 생기지 않게 한다.
4. 롤백 규칙을 명시한다(checked 예외를 쓰면 `rollbackFor`).
5. 읽기 전용 경로는 `readOnly = true`로 연다.

```java
@Service
class OrderFacade {                       // 트랜잭션 밖: 오케스트레이션
    private final OrderTx tx; private final PaymentClient pay; private final Outbox outbox;
    public void place(Cmd c) {
        PaymentResult r = pay.authorize(c);   // 외부 호출은 트랜잭션 밖
        tx.saveOrder(c, r);                   // 다른 빈 → 프록시를 거친다
    }
}

@Service
class OrderTx {
    @Transactional(rollbackFor = Exception.class)
    public void saveOrder(Cmd c, PaymentResult r) {
        orders.insert(c, r);
        stock.decrease(c.sku(), c.qty());
        outbox.insert(new OrderPlaced(c.id()));   // 발행할 이벤트를 같은 트랜잭션에 기록
    }
}
```

### 2. 경계가 보이지 않을 때 확인하는 법

- 코드: 메서드 안에서 `TransactionSynchronizationManager.isActualTransactionActive()`를 찍는다(로컬 재현에서 쓴 방법).
- 로그: 트랜잭션 매니저 로거를 DEBUG로 둔다. `DataSourceTransactionManager`는 `org.springframework.jdbc.datasource` 패키지에 있다. 로컬 재현에서 `Creating new transaction with name [...]: PROPAGATION_REQUIRED,ISOLATION_DEFAULT`, `Participating in existing transaction`, `Participating transaction failed - marking existing transaction as rollback-only` 같은 줄이 나왔다. 자기 호출로 무시된 메서드는 이런 줄이 없다.
- DB:

```sql
-- PostgreSQL: 트랜잭션을 연 채 노는 세션 = 경계 안에서 앱이 딴 일을 하는 중
SELECT pid, application_name, now() - xact_start AS xact_age, now() - state_change AS idle_for, left(query, 60)
FROM pg_stat_activity WHERE state = 'idle in transaction' ORDER BY xact_start;
```

### 3. TS에서의 같은 문제

```ts
// node-postgres: 트랜잭션은 "같은 클라이언트"에서 BEGIN~COMMIT 해야 한다
const client = await pool.connect();
try {
  await client.query("BEGIN");
  await client.query("UPDATE stock SET qty = qty - $1 WHERE sku = $2", [qty, sku]);
  await client.query("INSERT INTO orders ...");
  await client.query("COMMIT");
} catch (e) {
  await client.query("ROLLBACK");
  throw e;
} finally {
  client.release();
}
// pool.query("BEGIN") 후 pool.query("UPDATE ...") 는 서로 다른 커넥션일 수 있다 → 경계가 깨진다
```

- node-postgres 문서 "Transactions": 트랜잭션 안의 모든 문장은 **같은 클라이언트 인스턴스**로 보내야 한다. PostgreSQL은 트랜잭션을 클라이언트(연결) 단위로 격리하기 때문이다. 그래서 `pool.query`로 트랜잭션을 쓰지 말라고 경고한다.

## 장애 시나리오와 대처

### 1. `@Transactional`이 조용히 무시된다 (자기 호출)

- 현상: 중간에 예외가 났는데 앞의 INSERT가 남아 있다. 또는 지연 로딩에서 `LazyInitializationException`이 난다([23](../23-orm-and-n-plus-one/2-summary.md)).
- 보이는 형태: 에러 로그가 없다. 트랜잭션 DEBUG 로그에 해당 메서드의 트랜잭션 생성 줄이 없다. `isActualTransactionActive()`가 false다.
- 원인: 같은 클래스의 다른 메서드에서 `this.method()`로 불렀다. 프록시를 거치지 않았다. private 메서드, `@PostConstruct`, 인터페이스 기반 프록시에서 인터페이스에 없는 메서드도 같은 이유로 걸리지 않는다.
- 대처: 트랜잭션 메서드를 다른 빈으로 옮긴다. 또는 `TransactionTemplate`으로 경계를 명시한다. 통합 테스트에서 "예외 시 롤백"을 실제로 확인한다.

### 2. checked 예외인데 반쯤 커밋됐다

- 현상: 파일 처리 중 `IOException`이 났는데, 앞의 DB 변경이 커밋돼 있다.
- 보이는 형태: 호출자는 예외를 받았는데 DB에는 일부 행이 있다.
- 원인: Spring 기본 롤백 규칙은 예외 중 RuntimeException·Error만 롤백한다. checked 예외는 커밋된다.
- 대처: `rollbackFor = Exception.class`. 또는 checked 예외를 경계 안에서 unchecked 도메인 예외로 감싸 던진다. 예외를 잡고 삼키는 `catch`가 없는지도 본다.

### 3. 트랜잭션 안 HTTP 호출 → 풀 고갈

- 현상: 외부 결제사가 느려지자 우리 API 전체가 멈춘다. 결제와 무관한 API도 멈춘다.
- 보이는 형태: `CannotCreateTransactionException: Could not open JDBC Connection for transaction` ← `Connection is not available, request timed out after ...ms`. DB에는 `idle in transaction` 세션이 풀 크기만큼 있다.
- 원인: 트랜잭션 안에서 외부 호출을 기다리며 커넥션을 쥔다. 외부 지연이 그대로 커넥션 점유 시간이 된다.
- 대처: 외부 호출을 트랜잭션 밖으로 뺀다(§적용 1). 외부 호출 자체에 짧은 타임아웃을 둔다. 서버 측 `idle_in_transaction_session_timeout`으로 상한을 둔다([22](../22-database-side-timeouts/2-summary.md)).

### 4. `REQUIRES_NEW` 남용 → 자기 교착·풀 교착

- 현상: 감사 로그를 `REQUIRES_NEW`로 남기는 코드가 가끔 멈춘다. 부하가 몰리면 전체가 멈춘다.
- 보이는 형태:
  - 같은 행: DB에 `deadlock detected`가 없다. `lock_timeout`이 있으면 55P03. 다른 타임아웃(동작·원리 §4 그림의 괄호)도 없으면 무한 대기.
  - 풀: 스레드 덤프가 전부 `getConnection` 대기이고 `Connection is not available`이 난다.
- 원인:
  - 바깥이 락을 쥔 행을 안쪽 새 트랜잭션이 기다린다. 바깥은 안쪽이 돌아오기를 기다린다. 대기의 한쪽이 JVM 안이라 DB가 사이클을 보지 못한다.
  - 스레드마다 커넥션 2개가 필요해 풀이 마른다.
- 대처: 안쪽이 바깥과 같은 행을 건드리지 않게 설계한다. 정말 독립이어야 하는 기록(실패 감사 로그 등)만 `REQUIRES_NEW`로 둔다. 풀 크기 ≥ 동시 스레드 × (최대 동시 커넥션 − 1) + 1. 서버 측 `lock_timeout`을 둔다.

### 5. 안쪽 예외를 잡았는데 `UnexpectedRollbackException`

- 현상: 서비스 A(REQUIRED)가 서비스 B(REQUIRED)의 예외를 try/catch로 잡고 계속 진행했다. 커밋 시점에 예외가 난다.
- 보이는 형태: `UnexpectedRollbackException: Transaction rolled back because it has been marked as rollback-only`(로컬 재현, Spring 6.2.11). DEBUG 로그에는 `Global transaction is marked as rollback-only but transactional code requested commit`이 먼저 찍힌다.
- 원인: B가 참여한 트랜잭션에 rollback-only 표시를 남겼다. A가 예외를 잡아도 공유 물리 트랜잭션은 롤백된다.
- 대처: B의 실패가 A의 커밋을 막지 않아야 한다면 B를 `REQUIRES_NEW`나 `NESTED`로 분리한다. 또는 B가 예외 대신 결과 값으로 실패를 알린다. 막아야 한다면 예외를 잡지 않는다.

## 핵심 문장

- 선언적 트랜잭션은 **프록시를 거친 외부 호출**에만 걸린다. 자기 호출은 에러 없이 트랜잭션 없이 실행된다.
- Spring 기본 롤백 규칙은 예외 중 RuntimeException·Error만 롤백한다. checked 예외는 커밋된다.
- (JDBC·JPA 명령형 경로에서) 트랜잭션 컨텍스트는 스레드에 묶인다. 다른 스레드로 넘긴 DB 작업은 바깥 트랜잭션 밖이다.
- `REQUIRES_NEW`는 커넥션을 하나 더 빌린다. 풀 교착과, DB가 탐지하지 못하는 자기 교착을 만들 수 있다.
- 트랜잭션 안의 외부 호출은 그 시간만큼 커넥션과 락을 쥔다. 외부 호출은 경계 밖으로, 커밋 뒤 할 일은 훅이나 outbox로 옮긴다.
- `readOnly`는 힌트다. 실제로 막는지는 트랜잭션 매니저·드라이버·DB에 달렸다(pgjdbc + PostgreSQL은 `BEGIN READ ONLY`로 쓰기를 거부).

## 관련 주제·근거

- 선행
  - [13-transactions-acid](../13-transactions-acid/2-summary.md) — 원자성·격리의 정확한 뜻
  - [21-connection-pooling](../21-connection-pooling/2-summary.md) — 쥔 시간과 풀 크기, 풀 교착
  - distributed/16-outbox-and-dual-write — 미작성([distributed 영역 표](../../distributed/README.md))
- 연결
  - [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md) — idle in transaction·lock_timeout
  - [23-orm-and-n-plus-one](../23-orm-and-n-plus-one/2-summary.md) — Session 수명·OSIV·flush
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md) — DB 교착 탐지의 범위
  - 원고 [engineering/data-access](../../engineering/data-access/README.md) — JPA·Spring Data JDBC의 쓰기 경로
  - software-design/33-aop-and-proxies — 미작성([software-design 영역 표](../../software-design/README.md))
- 문서
  - Spring Framework 문서 "Using @Transactional"(프록시 모드·자기 호출·메서드 가시성) <https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html>
  - Spring Framework 문서 "Rolling Back a Declarative Transaction" <https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html>
  - Spring Framework 문서 "Transaction Propagation"(REQUIRED·REQUIRES_NEW 풀 경고·NESTED) <https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html>
  - Spring Framework 문서 "Transaction-bound Events" <https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html>
  - Spring javadoc: `@Transactional.readOnly`, `TransactionSynchronization.afterCommit`, `DataSourceTransactionManager.setEnforceReadOnly`
  - Spring Framework 소스(6.2.x) `spring-orm/.../vendor/HibernateJpaDialect.java`(readOnly → `FlushMode.MANUAL`) · `spring-orm/.../JpaTransactionManager.java`(NESTED via JDBC Savepoints javadoc)
  - pgjdbc 연결 속성 `readOnlyMode`(기본 transaction → `BEGIN READ ONLY`) <https://jdbc.postgresql.org/documentation/use/>
  - node-postgres "Transactions" <https://node-postgres.com/features/transactions>
  - Kleppmann 『Designing Data-Intensive Applications』 1판 7장(트랜잭션)
- 로컬 재현(Spring Framework 6.2.11 · HikariCP 6.3.0 · pgjdbc 42.7.8 · PostgreSQL 17.11): CGLIB 프록시 클래스, 자기 호출 무시, 안쪽 예외를 삼킨 REQUIRED의 `UnexpectedRollbackException`, checked/unchecked/rollbackFor 롤백 결과, readOnly 쓰기 거부, REQUIRES_NEW 같은 행 자기 교착(55P03), afterCommit/afterCompletion 순서, 트랜잭션 안 3초 대기로 풀 고갈
