# domain-modeling/09-domain-events — 도메인 이벤트: "일어난 일"을 모델에 올리고 커밋 뒤에 내보낸다 — 정리 (힌트)

## 해결하는 문제

주문이 들어오면 할 일이 줄줄이 붙는다. 확인 메일, 포인트 적립, 재고 예약, 배송 요청.

```text
  OrderService.place()
    ├─ 주문 저장            ← 이 서비스의 일
    ├─ 메일 발송            ┐
    ├─ 포인트 적립          ├ 다른 팀·다른 컨텍스트의 일
    └─ 배송 요청            ┘
  → 기능이 붙을 때마다 place()가 커진다. 메일 서버가 느리면 주문이 느려진다.
```

- 해법 1단계: "주문이 접수됐다"는 **사실**을 객체로 만든다. 후속 처리는 그 사실을 구독한다.
  - *도메인 이벤트(domain event)*: 도메인 전문가가 신경 쓰는, 도메인에서 일어난 일을 나타내는 객체. 이름은 과거형이다(`OrderPlaced`, `PaymentRefunded`).
- 해법 2단계: 그 사실을 **언제** 내보내는지 정한다. 이 노트의 장애는 대부분 여기서 나온다.

쉬운 예: 학교 게시판이다.
- 교무실은 "3월 2일 개학"이라고 공지를 붙인다. 버스 회사·급식실·학부모가 각자 공지를 보고 움직인다.
- 교무실이 버스 회사에 직접 전화하지 않는다.
- 그런데 공지를 **결재 전에** 붙였다가 결재가 반려되면? 버스는 이미 출발했다.

똑같은 구조다. 공지 = 도메인 이벤트, 결재 = DB 트랜잭션 커밋이다.

실무 예:
- 주문 트랜잭션 안에서 `@EventListener`로 메일을 보냈다. 그 뒤 재고 검사가 실패해 롤백됐다. 고객은 "주문 완료" 메일을 받았는데 주문이 없다.
- 결제 승인 이벤트를 커밋 직후 브로커로 보내다 프로세스가 죽었다. 결제는 됐는데 배송 요청이 안 갔다(이쪽은 [distributed/16 outbox](../../distributed/16-outbox-and-dual-write/2-summary.md)가 다룬다).

## 동작·원리

### 1. 이벤트는 모델의 일부다 — Evans 『DDD Reference』(2015)

```text
  애그리거트(주문)                        이벤트(불변 값)
  ┌────────────────────┐   place()     ┌──────────────────────────────┐
  │ Order#7  PLACED    │ ────────────> │ OrderPlaced                  │
  │  - lines           │               │  eventId    (중복 식별용)      │
  │  - total           │               │  orderId=7  (관련 엔티티 ID)   │
  │  - events: [ ... ] │               │  occurredAt (일어난 시각)      │
  └────────────────────┘               │  total=30000                 │
                                       └──────────────────────────────┘
```

- 『DDD Reference』 "Domain Events" 절의 요지(원문 확인, domainlanguage.com PDF):
  - 엔티티는 지금 상태만 들고 있어 "왜 이렇게 됐나"가 드러나지 않는다. 그래서 도메인 활동을 **이산적인 이벤트의 연속**으로 모델링하고, 각 이벤트를 도메인 객체로 표현한다.
  - 소프트웨어 내부 활동을 나타내는 *시스템 이벤트*와는 구분한다.
  - 이벤트는 과거의 기록이라 보통 불변이다. 보통 일어난 시각과 관련 엔티티의 ID를 담는다. 시스템에 입력된 시각·입력한 사람을 따로 담기도 한다.
  - 쓸모가 있으면 이벤트의 식별자를 이 속성들의 조합으로 만들 수 있다. 그러면 같은 이벤트가 두 번 도착해도 같은 것으로 알아본다. (실무에서는 따로 `eventId`(UUID 등)를 붙이는 경우가 많다 — 이것은 원문이 아닌 관행이다.)
- Evans의 2003년 책에는 이 패턴이 정식으로 없었다. 『DDD Reference』 목차는 "Domain Events"에 `*`를 달고 "`*` New term introduced since the 2004 book"이라고 적는다. Vernon 『IDDD』(2013) 견본 페이지(Pearson)의 8장 안내도 "Domain Events were not formally introduced by Eric Evans as part of DDD until after his book was published"라고 적는다.
  - *애그리거트(aggregate)*: 한 트랜잭션에서 함께 일관성을 지키는 객체 묶음. 루트를 통해서만 바꾼다. 기초는 [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md).

### 2. 이벤트를 모으는 곳과 내보내는 때는 따로다

```text
  ① 애그리거트 메서드가 이벤트를 "기록"한다 (메모리 목록에 추가)   ← 도메인 코드, 프레임워크 없음
  ② 애플리케이션 서비스가 저장한다 (트랜잭션 안)
  ③ 누군가 이벤트를 "발행"한다 ─┬─ 트랜잭션 안에서 바로      → 롤백돼도 이미 나감 (유령 이벤트)
                               ├─ 커밋 직후 (AFTER_COMMIT)  → 커밋과 발행 사이에 죽으면 유실
                               └─ 같은 트랜잭션에 outbox 행  → 커밋되면 있고 롤백되면 없음
```

- ①은 도메인 규칙의 일부다. "주문 확정 시 `OrderPlaced`가 생긴다"는 단위 테스트로 검증할 수 있다.
- ③은 인프라 결정이다. 도메인 객체가 브로커를 직접 부르면 ①과 ③이 붙어 버린다.
- 이 노트의 ⚠: **트랜잭션 커밋 전에 발행하면, 롤백됐는데 후속 처리가 진행된다.**

### 3. 시간축 — 커밋 전 발행 vs 커밋 후 발행 vs outbox

```text
  시간 →
  트랜잭션   BEGIN ── INSERT orders ── publish(e) ── 재고 부족! ── ROLLBACK
  @EventListener                       │ 메일 발송 ✉ (되돌릴 수 없음)
  AFTER_COMMIT 리스너                   │ (대기) ───────────────────────── 실행 안 됨
  outbox 행                             INSERT outbox ─────────────────── 같이 사라짐

  트랜잭션   BEGIN ── INSERT orders ── publish(e) ── COMMIT ─†─ (프로세스 사망)
  AFTER_COMMIT 리스너                                         실행 못 함 → 유실
  outbox 행                             INSERT outbox ── 커밋됨 → 릴레이가 나중에 보냄
```

- Spring에서 `ApplicationEventPublisher.publishEvent()`의 기본 리스너(`@EventListener`)는 기본 설정(멀티캐스터에 `TaskExecutor`를 주지 않고 `@Async`도 없을 때)에서 **발행한 스레드에서 바로** 실행된다. 트랜잭션 안이면 트랜잭션 안에서 돈다.
- `@TransactionalEventListener`는 트랜잭션 단계에 묶인다. Spring Framework 문서: 기본 phase는 `AFTER_COMMIT`이다. `BEFORE_COMMIT`·`AFTER_ROLLBACK`·`AFTER_COMPLETION`도 있다. 진행 중인 트랜잭션이 없으면 **호출되지 않는다**(`fallbackExecution = true`로 바꿀 수 있다).
- AFTER_COMMIT도 프로세스가 커밋 직후 죽으면 유실이다. 메모리에만 있기 때문이다. 유실이 안 되려면 이벤트를 **커밋되는 데이터의 일부**로 남겨야 한다 → outbox. 프로세스를 실제로 죽인 실험은 [distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md)에 있다.

### 실험: 커밋 전 발행, AFTER_COMMIT, outbox — 롤백 5건에서 무엇이 새나

- 환경: 전용 일회용 컨테이너 PostgreSQL 17.11, JDK 21(eclipse-temurin:21-jdk), Spring Framework 6.2.11(spring-context·spring-tx·spring-jdbc), pgjdbc 42.7.4, `SimpleDriverDataSource` + `DataSourceTransactionManager`. 2026-10-03.
- 주문 10건. 짝수 주문은 이벤트를 발행한 **뒤** 예외를 던져 롤백한다(재고 부족 흉내). 메일은 메모리 목록에 넣는 것으로 흉내 낸다 — 바깥 세계는 DB 롤백을 모른다.

```java
@Transactional
public void place(long id, boolean failAfterPublish) {
    jdbc.update("insert into orders(id, status) values (?, 'PLACED')", id);
    jdbc.update("insert into outbox(order_id, type) values (?, 'OrderPlaced')", id); // 같은 트랜잭션
    pub.publishEvent(new OrderPlaced(id));
    if (failAfterPublish) throw new IllegalStateException("재고 부족 — 롤백 " + id);
}

@EventListener                 public void mailNow(OrderPlaced e)        { mailByEventListener.add(e.orderId()); }
@TransactionalEventListener    public void mailAfterCommit(OrderPlaced e) { mailByAfterCommit.add(e.orderId()); }
@TransactionalEventListener    public void auditNoTx(OrderPlaced e)      { jdbc.update("insert into audit_a ...", e.orderId()); }
@TransactionalEventListener
@Transactional(propagation = Propagation.REQUIRES_NEW)
                               public void auditNewTx(OrderPlaced e)     { jdbc.update("insert into audit_b ...", e.orderId()); }
```

(실험, PostgreSQL 17.11 + JDK 21 + Spring 6.2.11, 2026-10-03)

```text
주문 시도 10건: 커밋 5, 롤백 5
DB orders 행        5
DB outbox 행        5
@EventListener 메일  10  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
AFTER_COMMIT 메일    5  [1, 3, 5, 7, 9]
AFTER_COMMIT DB쓰기(전파 지정 없음) audit_a 행 5
AFTER_COMMIT DB쓰기(REQUIRES_NEW)  audit_b 행 5
유령 메일(주문이 없는데 나간 메일) [2, 4, 6, 8, 10]
```

- `@EventListener`: 롤백된 5건에도 메일이 나갔다. 커리큘럼 ⚠ 그대로다. 오류 로그에는 "재고 부족"만 남고, 메일이 나갔다는 흔적은 메일 서버에만 있다.
- `AFTER_COMMIT`: 커밋된 5건에만 실행됐다.
- outbox: 롤백과 함께 사라졌다. 커밋된 5건만 남았다.

#### 덧붙인 관찰 1 — AFTER_COMMIT에서 DB에 쓰면?

- `TransactionSynchronization.afterCommit()`·`afterCompletion()` Javadoc(Spring 6.2): 이 시점의 데이터 접근은 원래 트랜잭션에 "참여"하며 **이후 커밋이 따라오지 않는다**("with no commit following anymore!"). 그래서 여기서 부르는 트랜잭션 작업에는 `PROPAGATION_REQUIRES_NEW`를 쓰라고 한다.
- 그런데 위 실험에서 전파 지정 없는 `audit_a`도 5행이 **저장됐다.** 문서의 경고와 결과가 다르다.
- 원인을 따로 확인했다. pgjdbc 42.7.4에서 트랜잭션 중에 `setAutoCommit(true)`를 부르면 그 트랜잭션이 커밋된다(JDBC `Connection.setAutoCommit` 규약, pgjdbc `PgConnection.setAutoCommit`의 `if (!this.autoCommit) commit();`).

(실험, 같은 환경, 2026-10-03)

```text
setAutoCommit(true) 전, 다른 연결이 본 행 수: 0
setAutoCommit(true) 후, 다른 연결이 본 행 수: 1
```

- 소스로 확인한 경로(Spring Framework v6.2.11 태그, pgjdbc REL42.7.4 태그):

```text
  AbstractPlatformTransactionManager.processCommit()
    doCommit()                         ← 주문 트랜잭션 커밋
    triggerAfterCompletion(COMMITTED)  ← AFTER_COMMIT 리스너가 여기서 돈다
       └ jdbc.update(audit_a)          ← 아직 묶여 있는 같은 연결(autoCommit=false) → 드라이버가 새 트랜잭션을 연다
    cleanupAfterCompletion()
       └ DataSourceTransactionManager.doCleanupAfterCompletion()
            if (mustRestoreAutoCommit) con.setAutoCommit(true)   ← 시작 때 autoCommit=true였던 연결만
               └ PgConnection.setAutoCommit: if (!this.autoCommit) commit()   ← audit_a가 여기서 커밋
```

- 즉 저장 여부는 **연결이 처음에 auto-commit=true였는가**에 달렸다. `doBegin()`은 그런 연결에만 `mustRestoreAutoCommit`을 켠다.
  - 풀이 연결을 auto-commit=false로 내주게 설정하면(HikariCP `autoCommit=false` 류) 복원 호출이 없다. 연결을 돌려줄 때 쓰기가 버려진다(HikariCP `ProxyConnection.close()`는 dirty 상태면 `rollback()`).
  - 이 반대 경우를 데이터소스가 연결을 auto-commit=false로 내주게 바꿔 재현했다(사실 점검 재실행).

(실험, 같은 환경 + 연결을 `setAutoCommit(false)`로 내주는 `SimpleDriverDataSource`, 2026-10-03)

```text
AFTER_COMMIT DB쓰기(전파 지정 없음) audit_a 행 0
AFTER_COMMIT DB쓰기(REQUIRES_NEW)  audit_b 행 5
```

  - 그래서 "우연히" 저장되는 동작이다. 문서가 보장하지 않고 풀 설정 하나로 뒤집히므로 기대지 않는다.
- Spring 6.2.11은 이 혼동을 일부 막는다. `@TransactionalEventListener`(phase가 `BEFORE_COMMIT`이 아닌 것)에 전파 기본값(`REQUIRED`)의 `@Transactional`을 붙이면 **컨텍스트 시작이 실패한다.** 검사 코드는 `RestrictedTransactionalEventListenerFactory`이고, `BEFORE_COMMIT` 리스너는 검사에서 빠진다.
  - 조건: 이 검사 팩토리는 Java 설정 `@EnableTransactionManagement`(Spring Boot도 이 경로)가 등록한다(`AbstractTransactionManagementConfiguration`). XML `<tx:annotation-driven/>`은 검사 없는 `TransactionalEventListenerFactory`를 등록해 시작이 실패하지 않는다(6.2.11 `AnnotationDrivenBeanDefinitionParser`). 아래 실험은 `@EnableTransactionManagement` 구성이다.

(실험, 같은 환경, 2026-10-03)

```text
NotSup: 시작 성공
Req: @TransactionalEventListener method must not be annotated with @Transactional unless when declared as REQUIRES_NEW or NOT_SUPPORTED: public void e09c.R$Req.on(e09c.R$Ev)
```

- 이 제한은 Spring 6.1에서 들어왔다(spring-framework 이슈 #30679·#31414). NOT_SUPPORTED 허용은 이슈 #31907로 6.1.3부터다(6.1.0~6.1.2에서는 NOT_SUPPORTED도 거부). 6.2.11에서는 위 출력처럼 허용된다.

#### 덧붙인 관찰 2 — AFTER_COMMIT 리스너가 예외를 던지면?

- 3번 주문의 AFTER_COMMIT 리스너가 DB에 쓴 뒤 예외를 던지게 바꿔 다시 돌렸다.

(실험, 같은 환경, 2026-10-03)

```text
SEVERE: TransactionSynchronization.afterCompletion threw exception
java.lang.IllegalStateException: AFTER_COMMIT 리스너 실패 3
...
주문 시도 10건: 커밋 5, 롤백 5
```

- 호출자는 예외를 받지 않았다(커밋 5로 셌다). 리스너 예외는 로그 한 줄(SEVERE)로만 남았다.
- 스택은 `invokeAfterCompletion`이었다. Spring 6.2.11에서 AFTER_COMMIT 리스너가 `afterCompletion` 콜백 안에서 실행된다는 뜻이다. `afterCompletion` Javadoc은 이 단계의 예외를 "로그만 남기고 전파하지 않는다"고 적는다.
- 결론: AFTER_COMMIT 후속 처리의 실패는 **호출자에게 보이지 않는다.** 실패를 다시 시도할 장치(outbox·재시도 큐)가 없으면 로그를 grep해야 찾는다.

## 쓰이는 자료구조·알고리즘

- **이벤트 목록(애그리거트 안의 리스트)** — 메서드가 실행되는 동안 생긴 이벤트를 순서대로 모은다. 저장 후 비운다. Spring Data의 `@DomainEvents`·`@AfterDomainEventPublication`이 이 모양이다.
- **append-only 로그** — outbox 테이블과 이벤트 저장소는 행을 붙이기만 한다. 순서 번호(시퀀스)가 소비 위치(체크포인트)가 된다. [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)
- **멱등 키(이벤트 ID) 집합** — 소비자는 처리한 이벤트 ID를 저장해 두 번째 도착을 버린다. outbox는 at-least-once라 중복이 온다. [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)
- **관찰자 패턴(Observer)** — 발행자는 구독자를 모른다. 프로세스 안에서는 `ApplicationEventPublisher`가 이 역할이다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **이벤트를 도메인 언어로 이름 짓는다.** 과거형, 도메인 전문가가 쓰는 말. `OrderStatusChanged`보다 `OrderCancelled`처럼 의도가 드러나게.
2. **애그리거트 메서드가 이벤트를 기록한다.** 상태 변경과 같은 메서드 안에서. 그러면 "상태는 바뀌었는데 이벤트는 없음"이 생기지 않는다.
3. **페이로드를 정한다.** 이벤트 ID, 애그리거트 ID, 일어난 시각, 소비자가 다시 조회하지 않아도 되는 최소 사실. 엔티티 객체 자체를 넣지 않는다(지연 로딩·변경 가능성).
4. **내보내는 때를 고른다.** 아래 표.
5. **소비자를 멱등하게 만든다.** 이벤트 ID로 중복을 버린다.

| 후속 처리 | 유실 허용? | 고르는 것 |
|---|---|---|
| 같은 트랜잭션 안에서 함께 성공·실패해야 하는 일(같은 DB의 집계 갱신 등) | — | 동기 `@EventListener` 또는 BEFORE_COMMIT. 사실상 같은 트랜잭션의 일부 |
| 되돌릴 수 없는 바깥 효과(메일·외부 API), 유실돼도 재시도·대사로 메울 수 있음 | 허용 | AFTER_COMMIT + `REQUIRES_NEW`, 실패 감시 |
| 다른 서비스·컨텍스트로 가는 통합 이벤트, 유실 불가 | 불허 | outbox(같은 트랜잭션) + 릴레이 + 멱등 소비자 |

### 2. 코드 모양 (Java — 프레임워크 없는 도메인 + 얇은 발행 계층)

```java
public final class Order {
    private final long id;
    private OrderStatus status;
    private final List<DomainEvent> events = new ArrayList<>();

    public void cancel(String reason, Clock clock) {
        if (status == OrderStatus.SHIPPED) throw new IllegalStateException("배송 중에는 취소할 수 없다");
        status = OrderStatus.CANCELLED;
        events.add(new OrderCancelled(UUID.randomUUID(), id, reason, clock.instant()));   // 상태 변경과 같은 자리
    }
    public List<DomainEvent> pullEvents() {            // 꺼내면서 비운다
        var out = List.copyOf(events); events.clear(); return out;
    }
}

public record OrderCancelled(UUID eventId, long orderId, String reason, Instant occurredAt) implements DomainEvent {}

// 애플리케이션 서비스: 같은 트랜잭션에 outbox로 남긴다
@Transactional
public void cancel(long orderId, String reason) {
    Order o = orders.findById(orderId);
    o.cancel(reason, clock);
    orders.save(o);
    for (DomainEvent e : o.pullEvents()) outbox.append(e);   // INSERT INTO outbox ... (같은 커넥션)
}
```

- Spring Data JPA를 쓰면 `AbstractAggregateRoot.registerEvent()`로 ①을 하고, `save()` 때 발행되게 할 수 있다.
  - Spring Data 문서가 발행 트리거로 드는 메서드는 `save`·`saveAll`·`delete`·`deleteAll`·`deleteAllInBatch`·`deleteInBatch`다. `deleteById`는 빠진다.
  - 그래서 더티 체킹만 믿고 `save()`를 부르지 않는 코드에서는 이벤트가 안 나간다(문서의 트리거 목록에서 나오는 결론).

### 3. 진단

```sql
-- 롤백됐는데 나간 이벤트 찾기: 바깥 기록(메일 로그 등)과 원천 대조
SELECT m.order_id FROM mail_log m
LEFT JOIN orders o ON o.id = m.order_id
WHERE o.id IS NULL;                         -- 주문 없이 나간 메일 = 유령 이벤트

-- outbox가 밀리는지: 미발행 건수와 가장 오래된 미발행 행의 나이
SELECT count(*), now() - min(created_at) FROM outbox WHERE published_at IS NULL;
```

- 로그에서 `TransactionSynchronization.afterCompletion threw exception`(SEVERE)을 경보로 건다. AFTER_COMMIT 리스너 실패가 여기로만 나온다(위 실험).

## 장애 시나리오와 대처

### 1. 롤백됐는데 메일·후속 처리가 나갔다 (커리큘럼 ⚠)

- 현상: "주문 완료" 메일을 받은 고객이 주문 내역에서 주문을 못 찾는다.
- 보이는 형태: 애플리케이션 로그에는 롤백 원인(재고 부족 등)만 있다. 메일 발송 로그에는 해당 주문 ID가 있다. 위 진단 SQL로 대조하면 나온다.
- 원인: 트랜잭션 안에서 동기 리스너(`@EventListener`)나 직접 호출로 바깥 효과를 냈다. 실험에서 롤백 5건 전부 유령 메일이 됐다.
- 대처: 바깥 효과는 AFTER_COMMIT 이후나 outbox 릴레이로 옮긴다. 이미 나간 건은 정정 메일·보상 처리.

### 2. 커밋은 됐는데 후속 처리가 조용히 빠졌다

- 현상: 주문은 있는데 포인트가 적립 안 된 건이 드문드문 있다.
- 보이는 형태: 호출자는 성공을 받았다. 로그에 `afterCompletion threw exception`이 있거나, 배포·OOM으로 프로세스가 커밋 직후 죽은 시각과 겹친다.
- 원인: AFTER_COMMIT 리스너는 메모리에서 돈다. 예외는 전파되지 않고(실험 관찰 2), 프로세스가 죽으면 대기 중이던 리스너도 사라진다.
- 대처: 유실이 안 되는 일은 outbox로. AFTER_COMMIT을 쓰면 실패 로그 경보 + 정기 대사(원천 vs 효과)로 메운다.

### 3. AFTER_COMMIT 리스너의 DB 쓰기가 환경마다 저장되거나 안 된다

- 현상: 로컬에서는 감사 행이 저장되는데 다른 환경에서는 빠진다는 보고.
- 보이는 형태: 리스너에 `REQUIRES_NEW`가 없다. 데이터소스·풀 설정이 환경마다 다르다.
- 원인: Spring 문서상 이 시점의 쓰기에는 커밋이 따라오지 않는다. 연결이 auto-commit=true로 시작했으면 Spring이 정리 단계에서 `setAutoCommit(true)`로 되돌릴 때 pgjdbc가 커밋해 버린다(실험: 5행). 풀이 auto-commit=false로 연결을 내주면 그 호출이 없어 버려진다(실험: 0행). 둘 중 어느 쪽에도 기대면 안 된다.
- 대처: AFTER_COMMIT 리스너의 DB 쓰기는 `@Transactional(propagation = REQUIRES_NEW)`로 명시한다. Spring 6.1+는 `@EnableTransactionManagement`(Spring Boot 포함) 구성에서 `REQUIRED`를 붙이면 시작을 거부한다(XML `<tx:annotation-driven/>`은 검사하지 않는다).

### 4. 같은 이벤트가 두 번 처리됐다

- 현상: 포인트가 두 번 적립됐다.
- 보이는 형태: 같은 `eventId`(또는 같은 주문 ID)로 적립 행이 2개.
- 원인: outbox 릴레이는 at-least-once다. 발행 후 "보냈음" 표시 전에 죽으면 다시 보낸다([distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md) 실험의 중복 127건).
- 대처: 소비자 쪽에 처리한 이벤트 ID 표(유니크 제약)를 둔다. 효과와 같은 트랜잭션에 기록한다.

### 5. 이벤트에 엔티티를 통째로 넣었다

- 현상: 소비자가 이벤트를 처리할 때 `LazyInitializationException`, 또는 이벤트 내용이 발행 후에 바뀌어 보인다.
- 원인: 이벤트가 불변 값이 아니라 살아 있는 엔티티 참조를 들고 있었다.
- 대처: 이벤트는 레코드(불변)로, ID와 필요한 사실만 복사해 넣는다. 『DDD Reference』도 이벤트를 "보통 불변"인 과거 기록으로 정의한다.

## 핵심 문장

- 도메인 이벤트는 "일어난 일"을 과거형 불변 객체로 모델에 올린 것이다. 상태 변경과 같은 메서드에서 기록한다.
- 이벤트를 **기록하는 때**(도메인)와 **내보내는 때**(인프라)를 나눈다. 장애는 내보내는 때에서 난다.
- 커밋 전에 바깥으로 내보내면 롤백돼도 되돌릴 수 없다 — 실험에서 롤백 5건 전부가 유령 메일이 됐다.
- AFTER_COMMIT은 유령은 막지만 유실은 못 막는다. 예외는 호출자에게 전파되지 않고 로그로만 남는다(Spring 6.2.11 실험).
- 유실이 안 되는 이벤트는 커밋되는 데이터의 일부(outbox)로 남기고, 소비자는 이벤트 ID로 멱등하게 만든다.

## 관련 주제·근거

- 선행: [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md) · [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md)(outbox·CDC·프로세스 halt 실험)
- 후속: [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md)(전이마다 이벤트) · [21-cqrs](../21-cqrs/2-summary.md)(이벤트로 읽기 모델 만들기) · [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)(이벤트를 원천으로) · [distributed/15-saga](../../distributed/15-saga/2-summary.md)
- 함께: [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) · [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md) · [distributed/29-outbox-vs-dispatch-log](../../distributed/29-outbox-vs-dispatch-log/2-summary.md) · 기초 연습 [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md)
- 근거
  - Evans, 『Domain-Driven Design Reference』 2015, "Domain Events" 절 — https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf (원문 확인)
  - Vernon, 『Implementing Domain-Driven Design』 2013, 8장 "Domain Events" — 장 구성은 Pearson 견본 페이지·O'Reilly 목차로 확인, 본문 세부는 미확인 `[?]`
  - Spring Framework 문서 "Transaction-bound Events" — https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html
  - Spring `TransactionSynchronization` Javadoc(`afterCommit`·`afterCompletion`) — https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/transaction/support/TransactionSynchronization.html
  - spring-framework 이슈 #30679, #31414, #31907 — https://github.com/spring-projects/spring-framework/issues/31414
  - Spring Data Commons "Publishing Events from Aggregate Roots" — https://docs.spring.io/spring-data/commons/reference/repositories/core-domain-events.html
- 실험 목록
  - 커밋 전 발행·AFTER_COMMIT·outbox 비교(롤백 5/10): PostgreSQL 17.11 + JDK 21 + Spring 6.2.11 + pgjdbc 42.7.4, 일회용 컨테이너
  - AFTER_COMMIT 리스너 예외 전파 여부: 같은 환경
  - pgjdbc `setAutoCommit(true)`가 진행 중 트랜잭션을 커밋하는지: 같은 환경
  - 반대 경우 — 데이터소스가 연결을 auto-commit=false로 내줄 때 AFTER_COMMIT 리스너의 쓰기(audit_a 0행): 같은 환경(사실 점검 재실행)
  - 소스: spring-framework v6.2.11 `AbstractPlatformTransactionManager.processCommit`·`DataSourceTransactionManager.doBegin/doCleanupAfterCompletion`·`TransactionalApplicationListenerSynchronization.afterCompletion`·`RestrictedTransactionalEventListenerFactory`, pgjdbc REL42.7.4 `PgConnection.setAutoCommit`, HikariCP `ProxyConnection.close` — https://github.com/spring-projects/spring-framework/tree/v6.2.11 · https://github.com/pgjdbc/pgjdbc/blob/REL42.7.4/pgjdbc/src/main/java/org/postgresql/jdbc/PgConnection.java
  - `@TransactionalEventListener` + `@Transactional` 전파별 시작 검사: Spring 6.2.11
