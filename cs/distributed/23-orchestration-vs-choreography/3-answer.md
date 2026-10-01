# distributed/23-orchestration-vs-choreography — 정답

## 정답

### 1. 정의와 사가와의 관계

- 오케스트레이션: 조정자가 참가자에게 무엇을 할지 명령하고 응답을 받아 다음 걸음을 정한다. 순서는 조정자가 안다.
- 코레오그래피: 조정자 없이 각 서비스가 이벤트를 발행·구독하며 스스로 다음 행동을 정한다. 순서는 구독 관계 속에만 있다.
- 사가는 "로컬 트랜잭션의 연속 + 보상"이라는 패턴이고, 두 방식은 그 사가를 조정하는 구현 방법이다(microservices.io "Saga").

### 2. 시퀀스와 상태 위치

```text
  오케스트레이션:  조정자 ─ReserveCredit→ 결제 ─CreditReserved→ 조정자 ─ApproveOrder→ 주문
                   상태: 조정자의 사가 표 (step)
  코레오그래피:    주문 ─OrderCreated→ 결제 ─PaymentCompleted→ 주문
                   상태: 각 서비스의 자기 표뿐 (orders.status, payments)
```

- 코레오그래피에서는 흐름 전체를 보는 컴포넌트가 없다(Azure "Choreography").

### 3. skip-dup의 결과

- 결제는 100건 모두 됐지만 주문 10건(10, 20, …, 100)이 영원히 `PENDING`이다.
- 두 컨슈머 그룹 모두 LAG 0이었다(`w14-order-created 100/100`, `w14-payment-completed 90/90`). 지표상 정상이라 멈춘 사가가 어디에도 경보로 나타나지 않는다.
- 근거: 실험(전용 PostgreSQL 17.11 + Kafka 4.1.0, 2026-10-01).

### 4. reemit-dup과 멱등의 뜻

- 100건 모두 `COMPLETED`. 재전달된 메시지에서 결과 이벤트를 다시 내 흐름이 이어졌다.
- 배운 것: 멱등 처리는 **효과(결제)를 두 번 내지 않는 것**이다. 결과 응답·이벤트까지 생략하면, 앞선 시도가 응답 직전에 죽은 경우 흐름이 끊긴다.

### 5. 오케스트레이터 복구

- 최종: 100건 모두 `DONE`, 주문 100건 `COMPLETED`, 결제 100건(멱등 키로 중복 없음).
- 죽어 있는 동안 사가 표: `DONE 49`, `PAYMENT_REQUESTED 1` — 어디서 멈췄는지 정확히 보인다.
- 대가: 조정자가 죽어 있는 동안 새 사가와 진행 중 사가가 모두 멈춘다(단일 장애점). 조정자 상태 영속·다중 인스턴스·참가자 멱등이 필요하다.

### 6. 인자 없는 `commitSync()`

- `commitSync()`는 마지막 `poll()`이 돌려준 **묶음 전체의 위치**를 커밋한다(Kafka 4.1 Javadoc). 첫 레코드를 처리하고 커밋하는 순간 아직 처리하지 않은 레코드까지 소비된 것으로 기록됐다.
- 10번째에서 죽자 11~100번은 다시 오지 않았다. 결과: 결제 10건, `PENDING` 91건, LAG 0.
- 고치기: 처리한 레코드마다 `commitSync(Map.of(tp, new OffsetAndMetadata(offset + 1)))`, 또는 묶음 전체를 처리한 뒤에 커밋한다.

### 7. 멈춘 사가 찾기

```sql
SELECT id, status, now() - updated_at AS stuck_for
FROM orders
WHERE status = 'PENDING' AND updated_at < now() - interval '10 minutes';
```

- 장치 셋
  - 위 같은 타임아웃 스캔 + 알람(실험에서 멈춘 10건은 LAG가 아니라 이것으로만 보였다).
  - 모든 이벤트에 correlation ID를 싣고 분산 추적.
  - 각 걸음의 발행을 outbox로(커밋 후 발행 전 유실을 닫음). 그리고 중복 시 결과 이벤트 재발행.

### 8. pessimistic view

- Azure "Saga": dirty read 위험을 줄이도록 **사가의 걸음 순서를 바꿔**, 위험한 갱신을 재시도 트랜잭션 쪽에서 하게 하는 대응책이다.
- 원본의 "홀딩 금액을 가용잔액에서 미리 빼서 보여 주기"는 진행 중 상태를 데이터에 표시해 다른 요청이 판단하게 하는 시맨틱 락 쪽 설명에 더 가깝다.

### 9. 섞어 쓰기

- 결제 승인: 실패 시 정확히 되돌리고 결과를 요청자에게 알려야 하므로 오케스트레이션.
- 포인트 적립·알림: 부수 효과이고 참가자가 늘기 쉬우므로 코레오그래피.
- 잇는 법: 오케스트레이터가 사가를 끝내면 `PaymentApproved`(또는 `OrderCompleted`) 이벤트를 outbox로 발행하고, 적립·알림 서비스가 구독한다.
