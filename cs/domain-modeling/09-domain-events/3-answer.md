# domain-modeling/09-domain-events — 정답

## 정답

### 1. 직접 호출의 문제와 이벤트가 푸는 것

- 직접 호출하면 기능이 붙을 때마다 주문 서비스가 커진다. 메일 서버가 느리면 주문이 느려지고, 메일 실패가 주문 실패가 된다.
- 도메인 이벤트는 "주문이 접수됐다"는 사실을 객체로 만들고, 후속 처리가 그것을 구독하게 한다. 발행자는 구독자를 모른다.
- 새로 생기는 문제: 이벤트를 **언제** 내보내나. 커밋 전이면 롤백돼도 나가고(유령), 커밋 후 메모리에서 내보내면 프로세스가 죽을 때 빠진다(유실).

### 2. 도메인 이벤트 vs 시스템 이벤트

- 도메인 이벤트: 도메인 전문가가 신경 쓰는, 도메인에서 일어난 일. 모델의 정식 구성원이다. 시스템 이벤트: 소프트웨어 내부 활동(예: 캐시 만료, 배치 시작).
- 보통 담는 것(『DDD Reference』): 일어난 시각, 관련 엔티티의 ID, 이벤트 설명. 시스템에 입력된 시각과 입력한 사람을 따로 담기도 한다.
- 이벤트 ID: 같은 이벤트가 두 번 도착해도 같은 것으로 알아보기 위해서다(중복 제거). 『DDD Reference』는 이 식별자를 위 속성들의 조합으로 만들 수 있다고 적는다.

### 3. 시간축

```text
  롤백 경우:   BEGIN ─ INSERT ─ publish ─ 실패 ─ ROLLBACK
    트랜잭션 안 발행  → 이미 나감 (유령)
    AFTER_COMMIT      → 실행 안 됨
    outbox 행         → 같이 사라짐
  커밋 후 사망: BEGIN ─ INSERT ─ publish ─ COMMIT ─† 
    AFTER_COMMIT      → 실행 못 함 (유실)
    outbox 행         → 남아 있음 → 릴레이가 나중에 보냄
```

- 기록(애그리거트가 메모리 목록에 추가)은 도메인 규칙이고, 내보내기(리스너·브로커·outbox)는 인프라 결정이다.

### 4. 롤백 5건 실험

- `@EventListener` 메일 10건(롤백된 2·4·6·8·10도 나감), AFTER_COMMIT 메일 5건(1·3·5·7·9), outbox 5행.
- 실험 출력: `@EventListener 메일  10`, `AFTER_COMMIT 메일    5`, `DB outbox 행        5`, `유령 메일 ... [2, 4, 6, 8, 10]`(PostgreSQL 17.11 + Spring 6.2.11).

### 5. AFTER_COMMIT에서의 DB 쓰기

- 이 조합에서는 남았다(`audit_a 행 5`).
- Javadoc(`afterCommit`)은 이 시점의 쓰기가 원래 트랜잭션에 참여하고 **이후 커밋이 따라오지 않는다**고 설명한다. 결과가 다르다.
- 원인: pgjdbc 42.7.4는 트랜잭션 중 `setAutoCommit(true)`를 부르면 그 트랜잭션을 커밋한다(실험: 다른 연결이 본 행 수 0 → 1). Spring 6.2.11 소스에서 리스너는 `triggerAfterCompletion` 안에서 돌고, 그 뒤 `doCleanupAfterCompletion`이 시작 때 auto-commit=true였던 연결에 `setAutoCommit(true)`를 부른다. 리스너의 쓰기가 이때 커밋된다.
- 연결을 auto-commit=false로 내주는 데이터소스에서는 복원 호출이 없어 `audit_a 행 0`이었다(재실행).
- 교훈: 풀 설정에 따라 뒤집히는 우연한 동작이다. `REQUIRES_NEW`를 명시한다.

### 6. AFTER_COMMIT 리스너 예외

- 받지 않는다. 실험에서 3번 주문의 리스너가 예외를 던졌지만 호출자는 성공으로 셌다(커밋 5).
- 실패는 `SEVERE: TransactionSynchronization.afterCompletion threw exception` 로그로만 남았다. Spring 6.2.11에서 AFTER_COMMIT 리스너는 `afterCompletion` 콜백 안에서 돌고, 그 단계 예외는 "로그만, 전파 안 함"(Javadoc)이다.

### 7. 리스너 + `@Transactional`

- `@EnableTransactionManagement`(Spring Boot 포함) 구성에서 기본 전파(`REQUIRED`)면 컨텍스트 시작이 실패한다(XML `<tx:annotation-driven/>`은 검사하지 않는다. phase가 `BEFORE_COMMIT`인 리스너는 검사에서 빠진다): `@TransactionalEventListener method must not be annotated with @Transactional unless when declared as REQUIRES_NEW or NOT_SUPPORTED`.
- 허용: `REQUIRES_NEW`, `NOT_SUPPORTED`(실험에서 시작 성공). 제한은 Spring 6.1에서 들어왔다(이슈 #31414). `NOT_SUPPORTED` 허용은 6.1.3부터다(이슈 #31907).

### 8. 발행 시점 고르기

- 같은 DB 집계 갱신: 주문과 함께 성공·실패해야 한다 → 동기 리스너나 BEFORE_COMMIT(사실상 같은 트랜잭션).
- 메일: 되돌릴 수 없는 바깥 효과라 커밋 전은 안 된다. 유실을 재시도·대사로 메울 수 있으면 AFTER_COMMIT + `REQUIRES_NEW` + 실패 감시.
- 통합 이벤트: 유실 불가 → 같은 트랜잭션의 outbox + 릴레이 + 멱등 소비자.

### 9. 유령 메일 진단

- 메일 발송 기록과 주문 테이블을 주문 ID로 LEFT JOIN 해서 주문이 없는 메일을 찾는다. 같은 시각의 롤백 로그(재고 부족 등)와 맞춰 본다.
- 원인: 트랜잭션 안에서 동기 리스너·직접 호출로 메일을 보냈다.
- 수정: 메일을 AFTER_COMMIT 리스너(또는 outbox 소비자)로 옮긴다. 이미 나간 건은 정정 안내.

### 10. outbox 뒤 중복 적립

- outbox 릴레이는 at-least-once다. 발행한 뒤 "보냈음" 표시를 커밋하기 전에 죽으면 재시작 후 다시 보낸다(distributed/16 실험: 중복 127건).
- 소비자 쪽에 처리한 이벤트 ID 표(유니크 제약)를 두고, 적립과 같은 트랜잭션에 기록한다. 두 번째 도착은 유니크 위반으로 버린다.
