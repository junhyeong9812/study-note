# distributed/23-orchestration-vs-choreography — 오케스트레이션 vs 코레오그래피: 사가를 누가 조정하나 — 정리 (힌트)

## 해결하는 문제

사가(15)는 여러 서비스의 로컬 트랜잭션을 차례로 잇는다. 그런데 "다음에 누가 무엇을 할지"는 누가 아나?

```text
  오케스트레이션                              코레오그래피
        [조정자]  ← 흐름·상태를 안다              주문 ─OrderCreated─> 결제 ─PaymentCompleted─> 주문
       ↙   ↓   ↘                                 (각자 이벤트를 듣고 다음 행동을 스스로 정한다)
     주문  결제  배송                              흐름은 이벤트 연결 속에만 있다
```

- *오케스트레이션(orchestration)*: 조정자(orchestrator)가 참가자에게 무엇을 할지 명령하고, 응답을 받아 다음 걸음을 정한다.
- *코레오그래피(choreography)*: 중앙 조정자 없이, 각 서비스가 도메인 이벤트를 발행하고 다른 서비스가 그 이벤트에 반응한다.
- 두 방식은 사가를 **구현하는 방법**이다. 사가는 "쪼개고 보상한다", 이 둘은 "그 순서를 누가 아나"다(microservices.io "Saga").

쉬운 예: 지휘자가 있는 오케스트라와, 앞 사람 동작을 보고 자기 차례를 아는 군무.
- 지휘자는 악보 전체를 안다. 지휘자가 쓰러지면 연주가 멈춘다.
- 군무는 지휘자가 없다. 한 명이 신호를 놓치면 그 뒤가 조용히 멈추고, 전체 순서를 아는 사람이 없다.

똑같은 구조다. 실무 예: 결제 승인(한도 → 잔액 홀드 → 원장, 오케스트레이션이 흔하다), "결제됐으니 포인트 적립·알림"(코레오그래피가 흔하다).

기초(정의·코드 예·장단점 비교표·피벗·격리 대응책·Outbox·멱등성)는 원본 [systems/orchestration-choreography](../../systems/orchestration-choreography/2-summary.md)에 있다. 이 노트는 두 방식이 **크래시를 만났을 때** 무엇이 보이고 무엇이 안 보이는지를 실험으로 보이고, 조정자 상태 기계와 운영 진단을 더한다.

참고: 원본 「격리성 부재에 대한 대응」 표의 "비관적 뷰 — 조회 시 최악을 가정해 보여준다"는 다른 개념에 가깝다. Azure "Saga" 패턴의 *pessimistic view*는 dirty read 위험이 있는 갱신을 재시도 트랜잭션 쪽으로 옮기도록 **사가의 걸음 순서를 바꾸는** 대응책이다. 원본이 말한 "홀딩 금액을 가용잔액에서 미리 빼서 보여 주기"는 시맨틱 락 쪽 설명에 가깝다.

## 동작·원리

### 1. 메시지 흐름 비교

```text
  오케스트레이션 (명령 / 응답)                     코레오그래피 (이벤트)
  조정자 ── ReserveCredit ──> 결제                 주문 ── OrderCreated ──────> 결제
  조정자 <─ CreditReserved ── 결제                 결제 ── PaymentCompleted ──> 주문
  조정자: saga 표 step=PAID 기록                   주문: status=COMPLETED
  조정자 ── ApproveOrder ───> 주문                 (흐름 = "누가 무엇을 구독하나"의 합)
```

- microservices.io "Saga"의 예
  - 코레오그래피: 주문 서비스가 `PENDING` 주문을 만들고 `OrderCreated`를 발행 → 고객 서비스가 신용을 예약하고 결과 이벤트 발행 → 주문 서비스가 승인·거절.
  - 오케스트레이션: 주문 서비스가 사가 조정자를 만들고, 조정자가 `Reserve Credit` 명령을 보내고 응답을 받아 승인·거절.
- 두 방식 모두 각 걸음은 "로컬 트랜잭션 + 메시지 발행"이다. 그래서 둘 다 outbox(16)와 멱등 소비가 필요하다.

### 2. 조정자는 영속 상태 기계다

```text
  saga 표 (order_id, step, updated_at)
  ┌───────────────────┐ 결제 응답 ┌──────┐ 주문 승인 ┌──────┐
  │ PAYMENT_REQUESTED │────────>│ PAID │────────>│ DONE │
  └─────────┬─────────┘         └──────┘         └──────┘
            │ 실패 응답
            ▼
       COMPENSATING ──> COMPENSATED / STUCK
  재시작 시: step <> 'DONE' 인 사가를 기록된 step부터 이어 간다
```

- 조정자가 진행 상태를 **메모리에만** 두면, 죽는 순간 진행 중인 사가가 모두 사라진다. 그래서 걸음마다 사가 표에 기록한다(원논문의 save-point와 같은 역할, 15).
- 재시작 시 같은 걸음을 다시 부를 수 있으므로 참가자 호출에는 멱등 키(사가 id + 걸음)가 필요하다.
- 커리큘럼 🔧 칸의 "워크플로 상태 기계"가 이것이다. Temporal·Camunda 같은 워크플로 엔진은 이 상태 저장·재시도·타이머를 엔진이 맡는다.

### 3. 코레오그래피에서는 상태가 어디에 있나

- 흐름 전체의 상태는 **아무 데도 없다.** 각 서비스는 자기 표의 상태(`orders.status = PENDING`)만 안다.
- Azure "Choreography" 패턴: 중앙 조정자가 전체 트랜잭션 상태를 쥐지 않으므로, 진행 중인 업무 흐름을 온전히 보는 컴포넌트가 없다. 분산 추적과 correlation ID를 일관되게 써야 관측할 수 있다.
- 반대로 Azure는 조정자가 부하 아래 병목이 되고 단일 장애점(SPoF)이 될 수 있으며, 조정자가 실패하면 그 실패가 하위 서비스로 번질 수 있다고 적는다.

### 실험: 결제 직후 크래시 — 코레오그래피의 멈춘 사가 vs 오케스트레이션의 복구

- 환경: 전용 일회용 PostgreSQL 17.11 + Kafka 4.1.0(KRaft 단일 노드), Java 21. 주문 100건. 2026-10-01.
- 크래시: 주문 id가 10의 배수이면 결제 커밋 **직후**·다음 메시지/기록 **전**에 프로세스를 `Runtime.halt()`로 죽인다(주문마다 한 번). 셸이 프로세스를 다시 띄운다.
- 코레오그래피 결제 서비스는 처리한 레코드의 다음 오프셋만 커밋한다(처리 후 커밋, at-least-once). 두 변형:
  - `skip-dup`: 결제가 이미 있으면 아무것도 안 하고 넘어간다 — 흔히 보는 "멱등 처리".
  - `reemit-dup`: 결제가 이미 있어도 `PaymentCompleted`를 다시 발행한다.

```java
// 코레오그래피 결제 서비스 핸들러
int inserted = c.createStatement().executeUpdate(
        "insert into payments(order_id) values (" + id + ") on conflict do nothing");   // 결제 커밋
if (inserted == 0 && variant.equals("skip-dup")) return;      // 중복이면 끝 — 발행도 건너뜀
if (id % 10 == 0) crashOnce("payment-" + id);                  // 커밋 후, 발행 전 죽음
pr.send(new ProducerRecord<>("w14-payment-completed", "" + id, "PaymentCompleted:" + id)).get();

// 오케스트레이터 (사가 표에 단계 기록)
insert saga(order_id, step='PAYMENT_REQUESTED') on conflict do nothing
insert payments(order_id) on conflict do nothing              // 멱등 키 = 주문 id
if (id % 10 == 0) crashOnce("orch-" + id);                    // 결제 후, 단계 기록 전 죽음
update saga set step='PAID' → update orders set status='COMPLETED' → update saga set step='DONE'
```

(실험, PostgreSQL 17.11 + Kafka 4.1.0, 2026-10-01) 컨슈머 그룹 줄은 `TOPIC PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG`:

```text
=== 코레오그래피, 결제 서비스 variant=skip-dup (주문 100건, id%10==0에서 결제 커밋 직후 1회 halt)
결제 서비스 재시작 10 회
[chor-skip-dup] 주문 COMPLETED 90, PENDING 10 | 결제 행 100 | 결제됐는데 PENDING인 주문: 10,20,30,40,50,60,70,80,90,100
w14-order-created 0 100 100 0
w14-payment-completed 0 90 90 0
=== 코레오그래피, 결제 서비스 variant=reemit-dup (주문 100건, id%10==0에서 결제 커밋 직후 1회 halt)
결제 서비스 재시작 10 회
[chor-reemit-dup] 주문 COMPLETED 100, PENDING 0 | 결제 행 100 | 결제됐는데 PENDING인 주문: null
w14-order-created 0 100 100 0
w14-payment-completed 0 100 100 0
=== 오케스트레이션 (주문 100건, id%10==0에서 결제 직후·단계 기록 전 1회 halt → 재시작 시 recover 후 이어서)
resume 10 from PAYMENT_REQUESTED
resume 20 from PAYMENT_REQUESTED
resume 30 from PAYMENT_REQUESTED
resume 40 from PAYMENT_REQUESTED
--- 오케스트레이터가 죽어 있는 동안 (id 50에서 정지)
DONE|49
PAYMENT_REQUESTED|1
resume 50 from PAYMENT_REQUESTED
… (60·70·80·90·100도 같은 형태)
[orch] 주문 COMPLETED 100, PENDING 0 | 결제 행 100 | 결제됐는데 PENDING인 주문: null
DONE|100
```

- **코레오그래피 skip-dup**: 결제는 100건 다 됐는데 주문 10건이 영원히 `PENDING`이다. 재시작한 결제 서비스는 메시지를 다시 받았지만(커밋 전이었으니) "이미 결제함 → 끝"으로 넘어가서 `PaymentCompleted`를 다시 내지 않았다.
  - 그런데 **두 컨슈머 그룹의 LAG는 모두 0**이다. Kafka 지표만 보면 모든 것이 정상이다. 멈춘 사가를 알려 주는 곳이 없다 — 커리큘럼 ⚠ "흐름 추적 불가 → 멈춘 사가 방치".
- **코레오그래피 reemit-dup**: 같은 크래시에서 100건 모두 완료. 재전달된 메시지에서 "이미 했으면 결과 이벤트를 다시 낸다"가 사가를 이어 줬다. 멱등 처리는 "효과를 두 번 내지 않기"이지 "응답을 생략하기"가 아니다.
- **오케스트레이션**: 조정자가 10번 죽었다. 죽어 있는 동안 사가 표는 정확히 어디서 멈췄는지 보여 줬다(`DONE 49`, `PAYMENT_REQUESTED 1`). 재시작한 조정자가 그 단계부터 이어 가 100건 모두 `DONE`.
  - 대신 조정자가 하나뿐이면, 죽어 있는 동안 **새 사가가 진행되지 않는다.** 이 실험에서는 셸이 곧바로 다시 띄웠지만, 실제로는 그 시간만큼 주문이 멈춘다 — 커리큘럼 ⚠ "오케스트레이터 단일 장애점".

### 실험에서 만난 버그: 인자 없는 `commitSync()`

- 처음 실험에서는 레코드마다 `consumer.commitSync()`(인자 없음)를 불렀다. 결과(같은 환경, skip-dup):

```text
결제 서비스 재시작 1 회
[chor-skip-dup] 주문 COMPLETED 9, PENDING 91 | 결제 행 10 | 결제됐는데 PENDING인 주문: 10
w14-order-created 0 100 100 0
w14-payment-completed 0 9 9 0
```

- 첫 레코드를 처리하고 커밋하는 순간 **poll이 돌려준 묶음 전체(100건)의 위치**가 커밋됐다. 10번째에서 죽자 11~100번은 처리되지 않은 채 "소비 완료"가 됐다. 결제 90건이 사라졌는데 LAG는 0이다.
- Kafka 4.1 `KafkaConsumer` 문서: `commitSync()`는 "Commit offsets returned on the last poll() for all the subscribed list of topics and partitions". 레코드 단위로 커밋하려면 `commitSync(Map<TopicPartition, OffsetAndMetadata>)`에 `offset + 1`을 넘긴다. 위 본 실험은 이렇게 고친 코드다. 상세는 18(소비자 실패 처리).

## 쓰이는 자료구조·알고리즘

- **워크플로 상태 기계 + 영속 상태 표** — 조정자의 사가 표(`order_id, step`). 재시작 시 `step <> 'DONE'`을 스캔해 이어 간다. 커리큘럼 🔧 칸.
- **이벤트 구독 그래프** — 코레오그래피의 흐름은 "어떤 서비스가 어떤 이벤트를 구독해 어떤 이벤트를 내나"의 방향 그래프다. 순환(A → B → C → A)이 생기면 무한 연쇄가 될 수 있다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **멱등 키(사가 id + 걸음)** — 조정자 재시도·메시지 재전달에서 효과를 한 번만 낸다. 응답·결과 이벤트는 다시 낸다.
- **correlation ID** — 흩어진 이벤트를 한 사가로 묶어 추적한다(Azure "Choreography").
- **타임아웃 스캔(지연 큐)** — "일정 시간 넘게 PENDING"인 사가를 찾는 주기 작업. 코레오그래피의 멈춘 사가를 찾는 유일한 수단인 경우가 많다.

## 적용 — 풀어나가는 법

### 1. 고르는 기준

```text
  실패 시 정확히 되돌려야 하고, 결과를 요청자에게 알려야 하고, 걸음이 많은가?  ─> 오케스트레이션
  부수 효과(알림·적립·검색 색인)를 느슨하게 붙이고, 참가자가 자주 늘어나는가?  ─> 코레오그래피
  섞기: 핵심 흐름은 오케스트레이션, 끝난 뒤 "OrderCompleted" 이벤트에 부수 효과를 코레오그래피로
```

- 원본의 판단 문장: "흐름을 사람이 설명해야 하면 오케스트레이션, 알림처럼 흘려보내면 되면 코레오그래피." 한 시스템에서 섞는 것이 보통이다.
- 원본 비교표의 "긴 흐름(3단계 이상) / 짧은 흐름(1~2단계)"은 경험칙이다. 출처가 있는 기준은 아니다 [?].

### 2. 코레오그래피를 쓰면 둘 것

```sql
-- 멈춘 사가 탐지: 소유 서비스의 상태 표에서 오래 머문 것
SELECT id, status, now() - updated_at AS stuck_for
FROM orders
WHERE status = 'PENDING' AND updated_at < now() - interval '10 minutes'
ORDER BY updated_at;
```

- 이 질의를 주기적으로 돌려 알람을 건다. 위 실험에서 Kafka LAG는 0이었고, 멈춘 10건은 이 질의로만 보였다.
- 모든 이벤트에 correlation ID(주문 id)를 싣고 분산 추적에 남긴다.
- 핸들러는 "이미 처리했으면 효과는 생략하되 결과 이벤트는 다시 낸다".
- 각 서비스의 "DB 갱신 + 이벤트 발행"은 outbox로 한다(16). 실험의 크래시 지점(커밋 후·발행 전)이 outbox가 닫는 지점이다. outbox였다면 skip-dup이어도 `PaymentCompleted`가 outbox에 남아 발행됐다.

### 3. 오케스트레이션을 쓰면 둘 것

```java
// 재시작 시 복구 — 기록된 단계부터 이어 간다
@EventListener(ApplicationReadyEvent.class)
public void resumeInFlightSagas() {
    for (SagaInstance s : sagaRepository.findByStepNot(Step.DONE)) {
        executor.submit(() -> orchestrator.resume(s));        // 각 참가자 호출은 멱등 키(sagaId + step)
    }
}
```

- 조정자 상태는 영속 저장소에. 조정자는 여러 인스턴스로 띄우되 한 사가는 한 인스턴스만 맡게 한다(사가 단위 락·리스).
- 조정자가 한 인스턴스면 조정자 가용성이 곧 새 사가의 가용성이다. 헬스 체크·자동 재시작·다중 인스턴스.
- 참가자 추가 시 조정자를 고쳐야 한다(원본 표의 약점). 흐름이 커지면 조정자가 모든 것을 아는 "God Service"가 되지 않게 사가 단위로 나눈다.

## 장애 시나리오와 대처

### 1. 코레오그래피 흐름 추적 불가 → 멈춘 사가 방치 (커리큘럼 ⚠)

- **현상**: 결제는 됐는데 주문이 몇 시간째 "처리 중"이다. 고객 문의로 처음 안다.
- **보이는 형태**: Kafka 컨슈머 그룹 LAG 0, 오류 로그 없음(실험: 두 그룹 모두 LAG 0, 주문 10건 `PENDING`). `orders.status = PENDING`이 오래된 행.
- **원인**: 한 서비스가 커밋 후 발행 전에 죽었고, 재전달된 메시지를 "중복이니 무시"하며 결과 이벤트도 생략했다. 흐름 전체를 보는 컴포넌트가 없어서 아무도 모른다.
- **대처**: outbox로 발행 유실을 닫는다. 중복 처리 시 결과 이벤트를 다시 낸다. 멈춘 사가 탐지 질의 + 알람. correlation ID로 추적. 흐름이 핵심 업무면 오케스트레이션으로 옮기는 것도 검토한다.

### 2. 오케스트레이터 단일 장애점 (커리큘럼 ⚠)

- **현상**: 조정자 배포·장애 동안 신규 주문이 전부 진행되지 않는다. 진행 중인 사가도 멈춘다.
- **보이는 형태**: 사가 표에서 `PAYMENT_REQUESTED` 같은 중간 단계가 쌓인다(실험: 조정자 정지 중 `DONE 49 / PAYMENT_REQUESTED 1`). 조정자 헬스 체크 실패.
- **원인**: 흐름 진행이 조정자 하나에 달려 있다(Azure "Choreography": 조정자가 SPoF·병목이 될 수 있음).
- **대처**: 조정자 다중 인스턴스 + 사가 단위 소유권. 상태를 영속해 재시작 시 이어 가기(실험: 100건 모두 `DONE`). 엔진(Temporal 등)을 쓰면 상태 영속·재시도를 엔진이 맡는다.

### 3. 오프셋 커밋 실수로 메시지가 통째로 "소비됨"이 된다

- **현상**: 결제 서비스 재시작 후 많은 주문이 결제조차 안 됐다. LAG는 0이다.
- **보이는 형태**: 실험 첫 실행: 결제 10건, `PENDING` 91건, LAG 0.
- **원인**: 인자 없는 `commitSync()`가 poll 묶음 전체 위치를 커밋했다.
- **대처**: 레코드(또는 처리 완료 범위) 단위로 `offset + 1`을 명시 커밋. 18번 참고.

### 4. 코레오그래피 순환·폭주

- **현상**: 이벤트 수가 갑자기 늘고 같은 주문의 이벤트가 끝없이 오간다.
- **보이는 형태**: 같은 correlation ID로 A → B → C → A 이벤트가 반복된다.
- **원인**: 서비스 C가 A가 구독하는 이벤트를 내도록 바뀌었다. 흐름이 한곳에 없어 아무도 순환을 검토하지 않았다(원본 표의 "순환 의존 위험").
- **대처**: 이벤트 구독 관계를 문서·카탈로그로 관리하고 순환을 검사한다. 이벤트에 단계·홉 수를 실어 비정상 반복을 끊는다 [?].

## 핵심 문장

- 오케스트레이션은 조정자가 흐름과 상태를 쥐고, 코레오그래피는 흐름이 이벤트 구독 관계 속에만 있다.
- 코레오그래피에서는 멈춘 사가가 어떤 지표에도 안 보일 수 있다. 실험에서 LAG는 0인데 주문 10건이 영원히 PENDING이었다. 상태 표 타임아웃 스캔과 correlation ID가 필요하다.
- 멱등 처리는 효과를 두 번 내지 않는 것이지 결과 응답을 생략하는 것이 아니다. 재전달에 결과 이벤트를 다시 내면 멈춘 흐름이 이어진다.
- 오케스트레이터는 상태를 영속하면 크래시에서 이어 갈 수 있지만, 한 인스턴스뿐이면 죽어 있는 동안 새 사가가 멈추는 단일 장애점이다.
- 두 방식 모두 각 걸음의 "DB 갱신 + 메시지"는 outbox로, 소비는 멱등하게 해야 한다.

## 관련 주제·근거

- 선행
  - [15-saga](../15-saga/2-summary.md) — 보상·피벗·사가 상태 기계
  - 원본 [systems/orchestration-choreography](../../systems/orchestration-choreography/2-summary.md) — 정의·코드·비교표·피벗·격리 대응책
- 연결
  - [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 커밋 후 발행 전 유실을 닫기
  - [18-consumer-failure-handling](../18-consumer-failure-handling/2-summary.md) — 오프셋 커밋 순서·재시도
  - [ops-patterns/08-saga](../../ops-patterns/08-saga/2-summary.md) — 오케스트레이션식 사가 구현
- 근거
  - microservices.io "Pattern: Saga" — 코레오그래피·오케스트레이션 정의와 주문/고객 예 <https://microservices.io/patterns/data/saga.html>
  - Azure Architecture Center "Choreography pattern" — 조정자의 병목·SPoF, 중앙 상태가 없어 진행 중 흐름을 온전히 보는 컴포넌트가 없음, 분산 추적·correlation ID, 이벤트 스키마 진화 <https://learn.microsoft.com/en-us/azure/architecture/patterns/choreography>
  - Azure Architecture Center "Saga distributed transactions pattern" — pessimistic view 등 대응책 정의 <https://learn.microsoft.com/en-us/azure/architecture/patterns/saga>
  - Kafka 4.1 `KafkaConsumer` Javadoc — `commitSync()`는 마지막 poll이 돌려준 오프셋을 커밋 <https://kafka.apache.org/41/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html>
  - Richardson, 『Microservices Patterns』(2018) 4장 — 사가 조정 방식
- 실험 목록
  - `FlowExp.java` + `exp23.sh` — 전용 PostgreSQL 17.11 + Kafka 4.1.0, Java 21, 주문 100건·id%10==0에서 1회 halt. 코레오그래피 skip-dup → COMPLETED 90·PENDING 10·LAG 0 / reemit-dup → COMPLETED 100 / 오케스트레이션 → 정지 중 사가 표 `DONE 49·PAYMENT_REQUESTED 1`, 복구 후 `DONE 100`
  - `exp23.sh buggy` — 인자 없는 `commitSync()`: 결제 10건, PENDING 91, LAG 0
