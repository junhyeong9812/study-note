# systems/orchestration-choreography — 정리 (힌트)

> 복습은 [1-question.md](1-question.md)에서 시작하고, 막힐 때만 이 파일을 힌트로 연다.\
> 원고 출처: `jun-bank/docs/study/06-orchestration-vs-choreography/README.md` · 이관일 2026-09-16.\
> 본문 절들(2PC·Saga·오케스트레이션·코레오그래피·비교·어려운 부분)은 **원고**를 고쳐 쓴 것이다(문체·순서 유지).\
> 「한눈에」의 일상 비유와 세로 도식들은 **Claude가 원고 이해를 돕기 위해 새로 그린 것**이며, 원고에 없던 지식은 맨 끝 `[Claude 추가]`에만 둔다. 원본의 특정 서비스 이름·내부 코드(품질 시나리오 번호 등)는 「현장에서 만나는 상황」으로 일반화했다.

여러 서비스에 걸친 하나의 업무 흐름을 **누가 조율하는가**의 문제다.\
큰 트랜잭션 하나로 묶을 수 없을 때, 흐름을 쪼개고(Saga) 그 순서를 **중앙 조율자**가 지휘하느냐(오케스트레이션) **각자 이벤트를 듣고 스스로**(코레오그래피) 하느냐로 갈린다.

---

## 한눈에 — 쉽게 말하면

**오케스트라와 길거리 춤**을 떠올리면 된다. *(Claude 보강 — 원고의 지휘자/무용수 비유를 그림으로 확장)*

```text
오케스트레이션 (지휘자 있음)          코레오그래피 (지휘자 없음)
+---------------------------+       +---------------------------+
|      [지휘자]              |       |  무용수1 → 무용수2 → 무용수3 |
|     ↙  ↓  ↘               |       |  (앞 사람 동작을 보고        |
| 연주1 연주2 연주3          |       |   자기 차례를 스스로 시작)   |
| 지휘자가 순서를 다 안다     |       |  악보를 아는 사람이 없다     |
+---------------------------+       +---------------------------+
  → 흐름이 한 곳에 보인다              → 결합이 낮지만 흐름이 안 보인다
```

**분산 시스템의 업무 흐름도 똑같은 구조다.** 여러 서비스가 한 가지 일(예: 결제 승인 = 한도확인 → 잔액홀딩 → 원장기록)을 함께 해내야 하는데, 예전처럼 큰 트랜잭션 하나로 "전부 되거나 전부 안 되거나"를 공짜로 얻을 수 없다.\
그래서 흐름을 여러 조각으로 쪼개 각자 커밋하고(**Saga**), 실패하면 이미 한 것을 **보상**으로 되돌린다.\
이 쪼갠 흐름의 순서를 **지휘자 한 명이 지시하면 오케스트레이션**, **각자 옆 사람 동작을 보고 알아서 하면 코레오그래피**다.

쉽게 말하면 이렇다.\
**Saga는 "무엇을 하나"(쪼개고 보상한다)라는 패턴이고, 오케스트레이션·코레오그래피는 "그 순서를 누가 아나"라는 구현 방식이다.** 둘은 같은 층위의 경쟁자가 아니라, 패턴과 그 실행 방법의 관계다.

---

## 문제 — 이 개념이 답하려는 질문

이 주제에는 풀어야 할 코드 과제가 없다(설계 패턴 정리다). 대신 네 개의 질문에 답한다.

```text
1. "여러 DB에 걸친 하나의 작업을 어떻게 원자적으로 처리하나?"
       → 2PC는 왜 마이크로서비스에서 안 쓰나 (§ 2PC)
2. "ACID를 포기한 자리를 무엇으로 메우나?"
       → Saga = 쪼개고 보상한다 (§ Saga)
3. "쪼갠 흐름의 순서는 누가 아나?"
       → 중앙 조율자(오케스트레이션) vs 각자 이벤트(코레오그래피)
4. "격리성이 없어 생기는 문제들은 어떻게 막나?"
       → 보상 불가 작업·피벗·시맨틱 락·Outbox·멱등성 (§ 어려운 부분)
```

아래 서머리는 이 네 질문을 하나씩 분석·정리한 것이다.

---

## 전체 흐름

Saga가 상위 패턴이고, 오케스트레이션/코레오그래피는 그 아래 두 갈래다.

```text
큰 트랜잭션 하나 (모놀리식: @Transactional)
   │  서비스·DB가 분리되면 불가능
   ▼
2PC (이론적 해법)
   │  락·단일 장애점·가용성 문제로 실무에서 기피
   ▼
Saga (패턴 — "쪼개고 보상한다")
   │
   ├─ 오케스트레이션 방식   중앙 조율자가 순서를 안다
   └─ 코레오그래피 방식     각자 이벤트를 듣고 스스로 결정
   │
   ▼
격리성 부재가 남긴 숙제
   → 보상 불가 작업 · 피벗 · 시맨틱 락 · Outbox · 멱등성
```

---

## 왜 이 문제가 생기는가 — 2PC를 안 쓰는 이유

> 출처: `jun-bank/docs/study/06-orchestration-vs-choreography/README.md` — §1

**언제 나오나** — 하나의 논리적 작업이 여러 서비스·여러 DB에 걸쳐 있을 때.

모놀리식에서는 이렇게 하면 끝난다.

```java
@Transactional
public void transfer(AccountId from, AccountId to, Money amount) {
    accountRepository.withdraw(from, amount);
    accountRepository.deposit(to, amount);
    ledgerRepository.post(from, to, amount);
}   // 하나라도 실패하면 전부 롤백. ACID가 공짜로 보장된다
```

서비스와 DB가 분리되면 이게 불가능하다. 이론적 해법인 **2PC**는 이렇게 동작한다.

```text
조율자: "준비됐나?" (Prepare)   모든 참여자에게 커밋 준비를 물음
        ↓
참여자: "예"                    응답한 순간부터 락을 잡고 대기
        ↓
조율자: "커밋해" (Commit)       전원 OK일 때만 실제 커밋
        ↓
참여자: 커밋                    ← 이 대기 중 조율자가 죽으면 영원히 블로킹
```

**왜 마이크로서비스에서 안 쓰는가.**

- **락을 오래 잡는다** — 준비~커밋 사이 내내 잠긴다. 처리량이 급락한다.\
- **조율자가 단일 장애점** — "예" 응답 후 조율자가 죽으면 참여자는 영원히 대기(blocking)한다.\
- **가용성이 곱해진다** — 참여자 각각 99.9%면 5개 참여 시 99.5%로 떨어진다.\
- **많은 시스템이 지원하지 않는다** — 메시지 브로커, 대부분의 NoSQL, 외부 API.

**비용/결론** — 분산 환경에서는 ACID를 **포기하고** Saga를 쓴다.\
"포기한다"가 정확한 표현이다. 공짜 대체재가 아니라 **트레이드오프**다.

---

## Saga 패턴

> 출처: `jun-bank/docs/study/06-orchestration-vs-choreography/README.md` — §2

### 정의

> 긴 트랜잭션을 **여러 개의 로컬 트랜잭션**으로 쪼갠다.\
> 각 로컬 트랜잭션은 즉시 커밋된다. 중간에 실패하면, 이미 커밋된 것들을 **보상 트랜잭션**으로 되돌린다.

```text
정상 흐름
   T1 커밋 ─▶ T2 커밋 ─▶ T3 커밋 ─▶ T4 완료

실패 흐름 (T3에서 실패)
   T1  커밋됨
    ↓
   T2  커밋됨
    ↓
   T3  ✗ 실패
    ↓
   보상 시작 — 완료된 것만 역순으로
    ↓
   C2  T2를 의미적으로 되돌림
    ↓
   C1  T1을 의미적으로 되돌림
```

### 핵심 성질 — ACID가 아니다

| ACID 속성 | Saga에서는 |
|---|---|
| **원자성 (A)** | ❌ 중간 상태가 **외부에 보인다.** T2까지 커밋된 상태를 다른 요청이 읽을 수 있다 |
| **일관성 (C)** | △ **결과적으로만** 일관 |
| **격리성 (I)** | ❌ **없다.** 이게 Saga의 가장 어려운 부분 |
| **지속성 (D)** | ✅ 각 로컬 트랜잭션은 커밋되므로 유지된다 |

**격리성이 없다는 것의 실제 의미**: 이체 중간에 출금은 됐고 입금은 안 된 상태에서 잔액을 조회하면 **돈이 사라진 것처럼 보인다.**\
이걸 다루려면 별도 장치가 필요하다(아래 「어려운 부분」 §격리성).

### Saga는 패턴, 오케스트레이션/코레오그래피는 구현 방식

```text
Saga (패턴 — "쪼개고 보상한다")
 ├── 오케스트레이션 방식   중앙 조율자가 순서를 안다
 └── 코레오그래피 방식     각자 이벤트를 듣고 스스로 결정한다
```

**비용/트레이드오프** — 롤백의 원자성을 잃는 대신 락·단일 장애점·가용성 곱셈에서 벗어난다.

---

## 오케스트레이션 (Orchestration)

> 출처: `jun-bank/docs/study/06-orchestration-vs-choreography/README.md` — §3

**언제 쓰나** — 흐름을 사람이 설명해야 하고, 실패 시 정확히 되돌려야 하며, 결과를 즉시 알려줘야 할 때(예: 결제 승인, 계좌 이체).

### 정의

**중앙 조율자(Orchestrator)** 가 각 서비스를 순서대로 호출하고, 실패 시 보상까지 지휘한다.\
지휘자가 있는 오케스트라를 떠올리면 된다.

```text
        요청
         ↓
   ┌──────────────┐
   │  Saga 조율자   │   순서를 아는 단 하나의 주체
   └──────────────┘
         ↓ ① 한도 확인
      [카드 서비스]
         ↓ ② 잔액 홀딩
      [계좌 서비스]
         ↓ ③ 원장 기록
      [원장 서비스]
         ↓
       완료 응답
```

### 코드 — 흐름과 보상이 한 곳에 있다

```java
@Service
@RequiredArgsConstructor
public class PaymentSagaOrchestrator {

    private final CardServicePort cardService;
    private final AccountServicePort accountService;
    private final LedgerServicePort ledgerService;
    private final SagaStateRepository sagaRepository;

    public AuthorizationResult execute(AuthorizeCommand command) {

        // Saga 상태를 먼저 저장한다 — 도중에 죽어도 복구할 수 있어야 하므로
        PaymentSaga saga = sagaRepository.save(PaymentSaga.start(command));

        try {
            LimitHoldId limitHold = cardService.holdLimit(command.cardId(), command.amount());
            saga.markStepCompleted(SagaStep.LIMIT_HELD, limitHold);
            sagaRepository.save(saga);

            BalanceHoldId balanceHold = accountService.hold(command.accountId(), command.amount());
            saga.markStepCompleted(SagaStep.BALANCE_HELD, balanceHold);
            sagaRepository.save(saga);

            LedgerEntryId entry = ledgerService.postHold(command.toLedgerSpec());
            saga.markStepCompleted(SagaStep.LEDGER_POSTED, entry);

            saga.complete();
            sagaRepository.save(saga);
            return AuthorizationResult.approved(saga.authorizationId());

        } catch (Exception e) {
            compensate(saga);                       // 보상
            sagaRepository.save(saga);
            throw PaymentException.authorizationFailed(e);
        }
    }

    /** 완료된 단계만 역순으로 되돌린다 */
    private void compensate(PaymentSaga saga) {
        saga.markCompensating();
        if (saga.isCompleted(SagaStep.LEDGER_POSTED)) ledgerService.reverse(saga.ledgerEntryId());
        if (saga.isCompleted(SagaStep.BALANCE_HELD)) accountService.releaseHold(saga.balanceHoldId());
        if (saga.isCompleted(SagaStep.LIMIT_HELD))   cardService.releaseLimit(saga.limitHoldId());
        saga.markCompensated();
    }
}
```

### 조율자를 어디에 두는가

| 방식 | 설명 | 평가 |
|---|---|---|
| **전용 서비스** | Saga만 담당하는 서비스를 만든다 | 관심사가 명확하나 서비스가 하나 는다 |
| **시작 서비스가 겸함** | 흐름을 시작한 서비스가 조율 | 가장 흔함 |
| **워크플로 엔진** | Camunda, Temporal 등 외부 엔진 | 강력하나 학습·운영 비용 |

### 강점 / 약점 (비용)

| 강점 | 약점 |
|---|---|
| **흐름이 코드 한 곳에 있다** — 읽으면 전체가 보인다 | 조율자가 **단일 장애점** |
| 상태 추적이 쉽다 (Saga 상태 하나만 보면 됨) | 조율자가 모든 참여자를 **알아야** 한다 → 결합 증가 |
| 보상 순서 제어가 명시적 | 흐름이 늘면 조율자가 **God Service**로 비대해짐 |
| 디버깅·테스트가 상대적으로 쉽다 | 참여자 추가 시 조율자를 수정 (OCP 위반 경향) |

---

## 코레오그래피 (Choreography)

> 출처: `jun-bank/docs/study/06-orchestration-vs-choreography/README.md` — §4

**언제 쓰나** — 부수적이고 순서가 덜 중요한 짧은 흐름(예: "결제됐으니 포인트 적립하고 알림 보내라").

### 정의

중앙 조율자가 없다. 각 서비스가 **이벤트를 듣고 스스로 다음 행동을 결정**한다.\
안무를 익힌 무용수들이 지휘자 없이 함께 춤추는 모습에서 온 이름이다.

```text
   [카드 서비스]   한도 홀딩 → LimitHeld 발행
        ↓  (이벤트를 듣고)
   [계좌 서비스]   잔액 홀딩 → BalanceHeld 발행
        ↓  (이벤트를 듣고)
   [원장 서비스]   원장 기록 → LedgerPosted 발행
        ↓  (이벤트를 듣고)
   [알림 서비스]   알림 발송
```

### 코드 — 각자 이벤트를 듣고, 실패도 이벤트로 알린다

```java
// ① 시작 서비스 — 다음에 무슨 일이 일어날지 모른다
@Transactional
public void holdLimit(AuthorizeCommand command) {
    Card card = cardRepository.findById(command.cardId()).orElseThrow();
    card.holdLimit(command.amount());
    cardRepository.save(card);
    outbox.append(new LimitHeldEvent(          // Outbox — 같은 트랜잭션에 기록
        command.authorizationId(), command.accountId(), command.amount()));
}

// ② 다음 서비스 — LimitHeld를 듣고 자기 일을 한다
@KafkaListener(topics = "payment.limit-held")
@Transactional
public void on(LimitHeldEvent event) {
    if (processedEventStore.exists(event.eventId())) return;   // 멱등성 (at-least-once 대비)
    try {
        Account account = accountRepository.findById(event.accountId()).orElseThrow();
        account.hold(event.amount());
        accountRepository.save(account);
        outbox.append(new BalanceHeldEvent(event.authorizationId(), event.amount()));
    } catch (InsufficientBalanceException e) {
        outbox.append(new BalanceHoldFailedEvent(event.authorizationId(), e.getMessage()));  // 실패도 이벤트로
    }
    processedEventStore.save(event.eventId());
}

// ③ 앞 서비스 — 실패 이벤트를 듣고 스스로 보상한다
@KafkaListener(topics = "payment.balance-hold-failed")
@Transactional
public void on(BalanceHoldFailedEvent event) {
    Card card = cardRepository.findByAuthorizationId(event.authorizationId()).orElseThrow();
    card.releaseLimit(event.authorizationId());     // 보상
    cardRepository.save(card);
}
```

**주목할 점**: 어느 클래스에도 **"승인은 한도확인 → 잔액홀딩 → 원장기록 순서로 진행된다"는 문장이 없다.**\
흐름은 이벤트 연결로만 존재한다. 이게 코레오그래피의 본질이자 최대 약점이다.

### 강점 / 약점 (비용)

| 강점 | 약점 |
|---|---|
| **결합도가 매우 낮다** — 서로를 모른다 | **전체 흐름이 어디에도 없다** |
| 참여자 추가가 기존 코드를 안 건드림 | 장애 추적이 극도로 어렵다 |
| 단일 장애점 없음 | **순환 의존** 위험 (A→B→C→A) |
| 확장성이 좋다 | "지금 어디까지 갔나"를 알기 어렵다 |
| | 보상 로직이 여러 서비스에 흩어짐 |

---

## 오케스트레이션 vs 코레오그래피 — 비교

> 출처: `jun-bank/docs/study/06-orchestration-vs-choreography/README.md` — §5

| 축 | 오케스트레이션 | 코레오그래피 |
|---|---|---|
| **결합도** | 높음 (조율자가 전부 안다) | **낮음** |
| **흐름 가시성** | **높음** (코드 한 곳) | 낮음 (흩어짐) |
| **장애 추적** | **쉬움** (Saga 상태 조회) | 어려움 (분산 추적 필수) |
| **변경 시 파급** | 조율자 수정 필요 | 관련 서비스만 |
| **순환 의존 위험** | 없음 | **있음** |
| **단일 장애점** | **있음** (조율자) | 없음 |
| **테스트 난이도** | 낮음 | 높음 |
| **참여자 추가** | 조율자 수정 | **구독만 추가** |
| **적합한 흐름 길이** | **긴 흐름 (3단계 이상)** | 짧은 흐름 (1~2단계) |

### 실무 판단 기준

> **흐름을 사람이 설명해야 하면 오케스트레이션, 알림처럼 흘려보내면 되면 코레오그래피.**

- 결제 승인처럼 **결과를 즉시 알려줘야 하고 실패 시 정확히 되돌려야 하는 흐름** → 오케스트레이션\
- "결제됐으니 포인트 적립하고 알림 보내라"처럼 **부수적이고 순서가 중요하지 않은 흐름** → 코레오그래피

**한 시스템 안에서 섞어도 된다.** 오히려 그게 정상이다.

---

## 어려운 부분들 — Saga가 남긴 숙제

> 출처: `jun-bank/docs/study/06-orchestration-vs-choreography/README.md` — §6

### 보상이 불가능한 작업

**언제 나오나** — 이미 되돌릴 수 없는 부작용(발송·출금·외부 승인)이 흐름에 섞일 때.

| 작업 | 보상 가능? | 대응 |
|---|---|---|
| DB 레코드 삽입 | ✅ 삭제 또는 역분개 | |
| 잔액 차감 | ✅ 환입 | |
| **이메일·SMS 발송** | ❌ | 취소 안내를 **추가 발송** |
| **외부 카드사 승인** | △ | 취소 전문(망취소) 전송 — **상대가 받아줘야 함** |
| **현금 출금** | ❌ | 애초에 마지막 단계로 배치 |

**설계 원칙(비용)**: **되돌릴 수 없는 작업은 Saga의 마지막에 둔다.**\
그러면 그 앞이 다 성공한 뒤에만 실행되므로 보상할 일이 없다.

### 피벗 트랜잭션 (Pivot Transaction)

Saga를 세 구간으로 나누는 개념이다.

```text
[보상 가능 구간]   실패하면 앞의 것들을 전부 보상
      ↓
   ★ 피벗 ★        이 선을 넘으면 되돌리지 않는다 (결정의 순간)
      ↓
[재시도 구간]      실패해도 보상 없이 성공할 때까지 재시도
```

- **피벗 이전**: 실패하면 전체 보상\
- **피벗**: 이 지점을 넘으면 되돌리지 않는다\
- **피벗 이후**: 실패해도 보상하지 않고 **성공할 때까지 재시도**한다

결제에서는 **"승인 확정"이 피벗**이다.\
승인이 확정된 뒤 알림 발송이 실패했다고 승인을 취소하지 않는다 — 알림을 재시도할 뿐이다.

### 격리성 부재에 대한 대응

Saga에는 격리성이 없어 **중간 상태가 다른 요청에 보인다.**

```text
이체 중간 상태
   출금됨:  -10,000   (T1 커밋)
   입금:    아직       (T2 미실행)
      ↓
   이 순간 잔액 조회
      ↓
   돈이 사라진 것처럼 보인다   ← 격리성 부재의 실제 증상
```

대표적 대응책.

| 기법 | 설명 |
|---|---|
| **시맨틱 락 (Semantic Lock)** | 처리 중임을 나타내는 상태를 둔다 (예: `PENDING`). 다른 요청이 보고 판단 |
| **교환적 업데이트** | 순서에 무관한 연산만 쓴다 (절대값 설정 ❌, 증감 ⭕) |
| **비관적 뷰** | 조회 시 **최악을 가정**해 보여준다 (홀딩된 금액을 이미 나간 것으로 표시) |
| **값 재확인** | 커밋 직전에 읽은 값이 그대로인지 다시 확인 |

**현장에서 만나는 상황**: 결제 승인에서 흔한 **홀딩(Hold)** 개념이 정확히 **시맨틱 락 + 비관적 뷰**다.\
승인만 되고 매입은 안 된 금액을 가용잔액에서 미리 빼서 보여주는 것.

### Outbox 패턴 — 이벤트 유실 막기

**문제**: DB 커밋과 이벤트 발행은 서로 다른 시스템이라 원자적이지 않다.

```text
직접 발행 (원자적이지 않음)           Outbox (한 트랜잭션)
+---------------------------+       +---------------------------+
| ① DB 커밋 성공             |       | ① 상태 변경                |
| ② 브로커에 발행            |       | ② 이벤트도 같은 DB에 저장   |
|    ↑ 여기서 브로커 죽으면   |       |   → ①②가 함께 커밋/롤백     |
|      이벤트 영구 유실       |       | ③ 별도 프로세스가 읽어 발행  |
+---------------------------+       +---------------------------+
  → 유실 가능                         → 유실 없음, 대신 중복 발행 가능
```

```java
@Transactional
public void hold(AuthorizeCommand command) {
    Account account = accountRepository.findById(command.accountId()).orElseThrow();
    account.hold(command.amount());
    accountRepository.save(account);                        // ① 상태 변경
    outboxRepository.save(OutboxEvent.of(                   // ② 이벤트도 같은 DB, 같은 트랜잭션
        "balance.held", new BalanceHeldEvent(...)));
}   // ①②가 함께 커밋되거나 함께 롤백된다

@Scheduled(fixedDelay = 1000)   // 별도 프로세스가 outbox를 읽어 발행한다
@Transactional
public void publishOutbox() {
    for (OutboxEvent event : outboxRepository.findPending(100)) {
        kafkaTemplate.send(event.topic(), event.payload());
        event.markPublished();       // 실패하면 다음 주기에 재시도된다
    }
}
```

**대가(비용)**: 발행이 **최소 한 번(at-least-once)** 보장이므로 **중복 발행이 가능하다.**\
따라서 **소비 측이 반드시 멱등해야 한다.**

> 이 대가는 피할 수 없다. "정확히 한 번(exactly-once)"은 분산 환경에서 매우 비싸거나 불가능하다.\
> **at-least-once + 멱등 소비**가 실무의 정답이다.

### 멱등성 — 어느 쪽에서 더 중요한가

**둘 다 똑같이 중요하다.** 다만 이유가 다르다.

- **오케스트레이션**: 조율자가 재시도할 때 참여자가 중복 처리하면 안 된다\
- **코레오그래피**: 브로커가 이벤트를 중복 전달할 수 있다 (at-least-once)

```java
@Transactional
public AuthorizationResult authorize(AuthorizeCommand command) {
    // 1) 이미 처리했으면 최초 결과를 그대로 반환한다 — 재처리하지 않는다
    Optional<AuthorizationResult> previous = idempotencyStore.find(command.idempotencyKey());
    if (previous.isPresent()) return previous.get();

    AuthorizationResult result = doAuthorize(command);

    // 2) 결과를 키와 함께 저장 (같은 트랜잭션에)
    idempotencyStore.save(command.idempotencyKey(), result);
    return result;
}
```

**주의점(비용)**:

- 멱등키에 **유니크 제약**을 걸어야 동시 요청에서도 안전하다.\
- **저장과 처리가 같은 트랜잭션**이어야 한다.\
- 멱등키의 **보관 기간** 정책이 필요하다 (영원히 둘 수 없다).

---

## 현장에서 만나는 상황

> 원본은 특정 은행 서비스의 실제 흐름들을 점검했다. 그 판단 재료를 이름을 지우고 일반화해 옮긴다.

한 시스템 안에서 **흐름마다 방식이 제각각**인 경우가 흔하다.\
어떤 흐름은 이벤트(코레오그래피)로, 어떤 흐름은 동기 호출로 되어 있다.\
점검 질문은 하나다 — **의도된 선택인가, 그때그때 결정한 결과인가.**

특히 위험한 안티패턴 하나가 자주 보인다 — **`@Transactional` 안에서 다른 서비스를 동기 호출(HTTP/RPC)하는 것.** 이건 Saga도 2PC도 아니다.

```text
@Transactional 열림
   ↓
로컬 DB 작업 (커넥션 점유)
   ↓
원격 서비스 동기 호출 ──▶ 네트워크 대기   ← DB 커넥션을 쥔 채 기다린다
   ↓
로컬 커밋
```

- **DB 커넥션을 쥔 채 네트워크를 기다린다** → 커넥션 풀이 마른다.\
- **원격 성공 후 로컬 커밋이 실패하면 고아 레코드가 남는다** (원격에는 만들어졌는데 이쪽엔 없음).\
- **멱등키가 없으면 재시도 시 중복 생성**된다.

또 하나 — **Outbox가 일부 서비스에만 있는** 상황.\
이벤트를 쓰는 서비스인데 try-catch로 삼키고 자체 재시도 테이블을 쓰면, 유실 시나리오를 통과하지 못한다.\
**Outbox는 "이벤트를 쓰는 모든 곳"에 필요하다** — 한 곳이라도 빠지면 그 지점이 유실 구멍이다.

---

## 핵심 문장

- **분산 환경에서는 ACID를 "포기"하고 Saga를 쓴다 — 공짜 대체재가 아니라 트레이드오프다.**
- **Saga는 패턴(쪼개고 보상한다), 오케스트레이션·코레오그래피는 그 순서를 누가 아느냐의 구현 방식이다.**
- **오케스트레이션은 흐름 가시성을 얻고 단일 장애점·결합을 감수한다. 코레오그래피는 그 반대다.**
- **흐름을 사람이 설명해야 하면 오케스트레이션, 알림처럼 흘려보내면 코레오그래피 — 한 시스템에서 섞는 게 정상이다.**
- **되돌릴 수 없는 작업은 Saga의 마지막(피벗 이후)에 둔다.**
- **Outbox는 at-least-once를 대가로 유실을 막고, 그래서 소비 측 멱등성이 필수다.**

---

## 관련 자료

- 원본 학습 노트: `jun-bank/docs/study/06-orchestration-vs-choreography/README.md` — 특정 시스템 적용 검토 표(§8)는 이관 시 「현장에서 만나는 상황」으로 일반화했다.
- 형제 주제 후보: 결과적 일관성·이벤트 기반 아키텍처·CQRS (`systems/` 내에서 이어질 주제들). *(Claude 보강 — 실존 경로 아님, 추출 후보)*

---

## 용어 풀이

- **분산 트랜잭션** — 여러 시스템(DB)에 걸친 하나의 논리적 작업.
- **2PC (Two-Phase Commit)** — 조율자가 모든 참여자에게 "준비됐나?" 물은 뒤 전원 OK면 커밋시키는 프로토콜.
- **ACID** — Atomicity(원자성)·Consistency(일관성)·Isolation(격리성)·Durability(지속성).
- **Saga** — 긴 트랜잭션을 여러 로컬 트랜잭션으로 쪼개고, 실패 시 보상으로 되돌리는 패턴.
- **보상 트랜잭션 (Compensating Transaction)** — 이미 커밋된 작업을 **의미적으로** 되돌리는 별도 트랜잭션.
- **오케스트레이션 (Orchestration)** — 중앙 조율자가 각 서비스를 순서대로 호출하고 보상까지 지휘하는 방식.
- **코레오그래피 (Choreography)** — 조율자 없이 각 서비스가 이벤트를 듣고 스스로 다음 행동을 결정하는 방식.
- **God Service** — 흐름이 늘수록 모든 것을 아는 비대한 조율자로 커지는 안티패턴.
- **피벗 트랜잭션 (Pivot Transaction)** — 이 지점을 넘으면 보상하지 않고 재시도로만 가는 결정의 경계.
- **시맨틱 락 (Semantic Lock)** — 처리 중임을 나타내는 상태(예: `PENDING`)로 다른 요청이 판단하게 하는 격리 대응.
- **비관적 뷰** — 조회 시 최악을 가정해 보여주는 것(홀딩 금액을 이미 나간 것으로 표시).
- **멱등성 (Idempotency)** — 같은 요청을 여러 번 처리해도 결과가 한 번 처리한 것과 같은 성질.
- **Outbox 패턴** — 상태 변경과 이벤트 발행을 같은 DB 트랜잭션으로 묶어 유실을 막는 패턴.
- **at-least-once / exactly-once** — 메시지가 최소 한 번 전달됨(중복 가능) / 정확히 한 번 전달됨(분산에선 매우 비쌈).
- **결과적 일관성 (Eventual Consistency)** — 지금은 어긋나 있어도 결국 같아지는 일관성.
- **단일 장애점 (SPOF)** — 그것 하나가 죽으면 전체가 멈추는 지점.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **Saga라는 이름의 출처.** Hector Garcia-Molina와 Kenneth Salem의 1987년 논문 "Sagas"에서 나왔다. 원래는 단일 DB에서 오래 걸리는 트랜잭션이 락을 오래 잡는 문제를 풀려던 개념이고, 마이크로서비스가 이를 분산 환경으로 가져와 재해석했다. *(확인 필요 — 논문 연도)*
- **프로세스 매니저 (Process Manager).** 코레오그래피에서 "지금 어디까지 갔나"를 알기 어려운 문제의 실무 대응이다. 흩어진 이벤트를 한 곳에서 구독해 진행 상태를 모으는 별도 컴포넌트로, 순수 코레오그래피와 오케스트레이션의 중간 형태다.
- **CDC 기반 Outbox.** 위 코드는 스케줄러가 Outbox 테이블을 폴링하는 방식이지만, 실무에서는 DB의 변경 로그(binlog 등)를 읽는 CDC(Change Data Capture, 예: Debezium)로 Outbox를 발행하는 방식도 널리 쓴다. 폴링 지연 없이 트랜잭션 로그에서 바로 이벤트를 뽑는다.
- **왜 exactly-once가 "환상"에 가까운가.** 발신자·네트워크·수신자 어느 하나가 언제든 죽을 수 있으므로, "전달"과 "처리 확정"을 하나의 원자 단위로 묶는 것이 근본적으로 불가능에 가깝다. 그래서 실무는 전달을 at-least-once로 두고, 소비 측 멱등성으로 "결과적 exactly-once(effectively-once)"를 만든다. 결과는 같아 보여도 메커니즘이 다르다.
