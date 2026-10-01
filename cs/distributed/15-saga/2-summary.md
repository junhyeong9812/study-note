# distributed/15-saga — 사가: 보상 트랜잭션, 역방향·순방향 복구 — 정리 (힌트)

## 해결하는 문제

주문 하나가 재고·결제·배송 세 서비스를 거친다. 서비스마다 DB가 따로라 한 트랜잭션으로 묶을 수 없다.

```text
  재고 차감 ✓ (inventory DB 커밋)
  결제 승인 ✓ (payment DB 커밋)
  배송 예약 ✗
  → 재고는 빠졌고 돈은 나갔는데 물건은 안 간다. 예외는 한 번 나고 끝이다
```

- 2PC(14)로 묶을 수도 있지만, 서비스 사이·외부 결제사 사이에서는 참가자가 XA를 지원하지 않거나, 블로킹과 락 보유를 감당할 수 없다.
- *사가(saga)*: 긴 작업을 로컬 트랜잭션 T1, T2, …, Tn의 연속으로 쪼개고, 각 Ti에 보상 트랜잭션 Ci를 짝지어 두는 방식(Garcia-Molina·Salem 1987).
  - *보상 트랜잭션(compensating transaction)*: Ti가 한 일을 **의미상** 되돌리는 새 트랜잭션. 롤백이 아니다.
- 논문이 정한 보장: 사가는 `T1, T2, …, Tn` 전부 실행되거나, `T1, …, Tj, Cj, …, C1`으로 끝난다.

쉬운 예: 비행기·호텔·공연을 차례로 예약하다 공연이 매진이면, 호텔 취소 → 비행기 취소를 예약의 반대 순서로 직접 한다. "여행 전체 취소" 버튼은 없다.

똑같은 구조다. 실무 예: 주문(재고·결제·배송), 여행 패키지, 여러 은행 시스템에 걸친 이체, 회원 탈퇴(여러 서비스의 개인정보 삭제).

기초 설명(보상 순서, 실패한 걸음은 되돌리지 않는 이유, `success / compensated / stuck` 결과 타입)은 원본 [ops-patterns/08-saga](../../ops-patterns/08-saga/2-summary.md)에 있다. 이 노트는 원논문의 모델, 동시성에서의 보상, 보상 실패·보상 불가 작업, 실험을 더한다.

## 동작·원리

### 1. 원논문의 모델 — 긴 트랜잭션을 쪼갠다

```text
  긴 트랜잭션(LLT) 하나:  [──────────── 락을 오래 쥔다 ────────────]
  사가:                   [T1] [T2] [T3] … [Tn]   ← 각자 짧게 커밋, 사이에 다른 트랜잭션이 끼어들 수 있다
  실패 시:                [T1] [T2] [T3]✗ → [C2] [C1]
```

- 원래 문제는 단일 DB에서 오래 걸리는 트랜잭션(LLT, long-lived transaction)이 락을 오래 쥐는 것이었다. 사가는 이를 짧은 트랜잭션들로 쪼개 **다른 트랜잭션과 끼워 실행되게** 한다(Garcia-Molina·Salem 1987, 초록).
- 마이크로서비스는 같은 생각을 "서비스마다 DB가 다른" 상황에 가져왔다(microservices.io "Saga").
- 대가: **격리(I)가 없다.** T2가 커밋된 뒤 T3 전에 남이 중간 상태를 본다.

### 2. 보상은 "옛 값으로 되돌리기"가 아니다

- 원논문의 비행기 좌석 예: Ti가 좌석을 예약하면 Ci는 예약 수에서 1을 빼고 다른 확인을 한다. **Ti 실행 당시의 좌석 수를 그냥 저장해 되돌리면 안 된다.** 그사이 다른 트랜잭션이 좌석 수를 바꿨을 수 있기 때문이다(논문 1절 서론).
- Azure "Compensating Transaction" 패턴도 같은 말을 한다. 원래 상태로 복원하면 다른 인스턴스의 동시 변경을 덮어쓸 수 있다.

```text
  재고 10
  사가 A: 읽음 10 → 차감 → 9         사가 B: 차감 → 8
  사가 A 실패, 보상 "재고 = 10(읽었던 값)"  → 10   ← B의 차감이 사라졌다
  사가 A 실패, 보상 "재고 += 1"            →  9   ← 맞다
```

참고: 원본 [ops-patterns/08-saga](../../ops-patterns/08-saga/2-summary.md) 「설계 — 걸음과 보상이 지켜야 할 계약」의 "보상은 절대값으로(재고를 원래 값으로)"는 사가가 하나만 돌 때만 맞다. 동시에 여러 사가가 같은 행을 바꾸면 남의 변경을 지운다(원논문 1절, 아래 실험). 재시도 안전성은 절대값이 아니라 **보상 ID로 중복을 거르는 방식**으로 얻는다.

### 3. 역방향 복구 vs 순방향 복구

```text
  역방향(backward):  T1 T2 T3✗ → C2 C1          "없던 일로" (의미상)
  순방향(forward):   T1 T2 T3✗ → T3 재시도 → T4 … Tn   "끝까지 밀어붙인다"
  섞어 쓰기:         [보상 가능 T1 T2] ─ 피벗 T3 ─ [재시도 T4 T5]
                      실패 → 역방향        여기서 결정    실패 → 순방향(재시도)
```

- 원논문: 사가가 중단되면 두 선택이 있다. 실행된 것을 보상하는 *역방향 복구*, 남은 것을 실행하는 *순방향 복구*. 순방향을 하려면 시스템이 "어디까지 했나"(save-point)와 남은 트랜잭션의 코드를 안정적으로 가져야 한다.
- 실무 용어(Richardson 『Microservices Patterns』 4장, Azure "Saga" 패턴)
  - *보상 가능 트랜잭션(compensable)*: 실패하면 보상으로 되돌린다.
  - *피벗 트랜잭션(pivot)*: 돌아올 수 없는 지점. 이것이 성공하면 사가는 끝까지 가야 한다.
  - *재시도 트랜잭션(retryable)*: 피벗 뒤에 온다. 멱등하게 만들어 성공할 때까지 재시도한다.
- 되돌릴 수 없는 일(메일·문자 발송, 물리 출고, 외부 확정 결제)은 **피벗 뒤**에 둔다. 앞에 두면 그 뒤 실패를 보상할 수 없다.

### 4. 사가 상태 기계

```text
  ┌─────────┐ T1..Tk 성공 ┌───────────┐ 피벗 성공 ┌──────────────┐ 재시도 끝 ┌───────────┐
  │ STARTED │───────────>│ RUNNING   │─────────>│ PAST_PIVOT   │─────────>│ COMPLETED │
  └─────────┘            └─────┬─────┘          └──────────────┘          └───────────┘
                               │ Tj 실패
                               ▼
                         ┌──────────────┐ Cj..C1 성공 ┌─────────────┐
                         │ COMPENSATING │───────────>│ COMPENSATED │
                         └──────┬───────┘            └─────────────┘
                                │ Ci 계속 실패
                                ▼
                         ┌──────────────┐
                         │ STUCK (사람)  │   ← 원논문 6절: 보상이 버그로 실패하면 "the system is stuck"
                         └──────────────┘
```

- 상태는 **영속**해야 한다. 조정자가 죽으면 메모리의 "어디까지 했나"가 사라진다(23번 실험에서 사가 표로 복구).
- 원논문 6절: 보상 트랜잭션 자체에 버그가 있으면 다시 돌려도 같은 오류가 난다. 중단도 완료도 할 수 없는 상태가 된다. 그래서 STUCK은 **사람에게 가는 경로**가 있어야 한다.

### 실험: 보상 없음 vs 절대값 보상 vs 상대값 보상 vs 중복 보상

- 환경: 전용 일회용 PostgreSQL 17.11 한 대 안의 서로 다른 DB 세 개(`inventory`·`payment`·`shipping`)를 서비스 셋으로 본다. DB가 다르니 공통 트랜잭션이 없다. Java 21, 스레드 8개로 사가 200개를 동시에 돌린다. 2026-10-01.
- 각 사가: 재고 1 차감 → 결제 `CAPTURED` → 배송 예약. 사가 id 끝자리가 0·1·2이면 배송이 실패한다(30%, 결정적).
- 보상 방식 네 가지

```java
// 보상: 역순 — 결제 취소 → 재고 복구
pay.createStatement().executeUpdate("update charge set status='REFUNDED' where saga_id=" + id);
switch (comp) {
  case "absolute" -> inv.createStatement().executeUpdate(          // 차감 전에 읽어 둔 값으로 덮어쓰기
          "update stock set qty = " + before + " where sku='X'");
  case "relative" -> inv.createStatement().executeUpdate("update stock set qty = qty + 1 where sku='X'");
  case "relative-dedup" -> {                                          // 보상 ID 기록과 복구를 한 로컬 트랜잭션에
      inv.setAutoCommit(false);
      int n = inv.createStatement().executeUpdate("insert into comp_done values (" + id + ") on conflict do nothing");
      if (n == 1) inv.createStatement().executeUpdate("update stock set qty = qty + 1 where sku='X'");
      inv.commit(); inv.setAutoCommit(true);
  }
}
```

(실험, PostgreSQL 17.11 + Java 21, 사가 200개·스레드 8, 2026-10-01) 같은 설정으로 두 번 실행:

```text
--- run 1
mode=naive comp=none dupComp=false | 성공 140, 보상 0, 보상없이 멈춤 60 | 재고 800 (기대 860, 차이 -60) | 결제 CAPTURED 200 (기대 140), REFUNDED 0
mode=saga comp=absolute dupComp=false | 성공 140, 보상 60, 보상없이 멈춤 0 | 재고 920 (기대 860, 차이 +60) | 결제 CAPTURED 140 (기대 140), REFUNDED 60
mode=saga comp=relative dupComp=false | 성공 140, 보상 60, 보상없이 멈춤 0 | 재고 860 (기대 860, 차이 +0) | 결제 CAPTURED 140 (기대 140), REFUNDED 60
mode=saga comp=relative dupComp=true | 성공 140, 보상 60, 보상없이 멈춤 0 | 재고 920 (기대 860, 차이 +60) | 결제 CAPTURED 140 (기대 140), REFUNDED 60
mode=saga comp=relative-dedup dupComp=true | 성공 140, 보상 60, 보상없이 멈춤 0 | 재고 860 (기대 860, 차이 +0) | 결제 CAPTURED 140 (기대 140), REFUNDED 60
--- run 2
mode=naive comp=none dupComp=false | 성공 140, 보상 0, 보상없이 멈춤 60 | 재고 800 (기대 860, 차이 -60) | 결제 CAPTURED 200 (기대 140), REFUNDED 0
mode=saga comp=absolute dupComp=false | 성공 140, 보상 60, 보상없이 멈춤 0 | 재고 923 (기대 860, 차이 +63) | 결제 CAPTURED 140 (기대 140), REFUNDED 60
mode=saga comp=relative dupComp=false | 성공 140, 보상 60, 보상없이 멈춤 0 | 재고 860 (기대 860, 차이 +0) | 결제 CAPTURED 140 (기대 140), REFUNDED 60
mode=saga comp=relative dupComp=true | 성공 140, 보상 60, 보상없이 멈춤 0 | 재고 920 (기대 860, 차이 +60) | 결제 CAPTURED 140 (기대 140), REFUNDED 60
mode=saga comp=relative-dedup dupComp=true | 성공 140, 보상 60, 보상없이 멈춤 0 | 재고 860 (기대 860, 차이 +0) | 결제 CAPTURED 140 (기대 140), REFUNDED 60
```

- **보상 없음**: 60건이 "재고 빠짐 + 결제 완료 + 배송 없음"으로 남았다(재고 -60, `CAPTURED` 200).
- **절대값 보상**: 재고가 기대보다 +60, +63 많다. 차이는 실행마다 다르다(스레드 끼어들기에 따라). 절대값 보상만 따로 세 번 더 돌렸을 때 +60, +61, +56이었고, 나머지 네 줄은 매번 위와 같았다. 보상이 남의 차감을 덮어써 **없던 재고가 생겼다.**
- **상대값 보상**: 동시성에서는 맞다(+0). 그러나 보상 메시지가 두 번 오면(`dupComp=true`) +60 — 실패 60건이 모두 두 번 복구됐다.
- **상대값 + 보상 ID 중복 제거**: 두 번 와도 +0. 결제 쪽 `status='REFUNDED'`는 같은 값을 쓰는 갱신이라 원래 멱등이었다.
- 결론: 보상은 **교환 가능한(commutative) 상대 연산 + 멱등 키**로 만든다. Azure "Saga" 패턴이 꼽는 대응책 중 *교환적 갱신(commutative updates)* 과 같다.

## 쓰이는 자료구조·알고리즘

- **상태 기계** — `STARTED → RUNNING → (PAST_PIVOT → COMPLETED) | (COMPENSATING → COMPENSATED | STUCK)`. 위 4절. 커리큘럼 🔧 칸.
- **스택(LIFO)** — 실행한 걸음을 쌓고 거꾸로 보상한다. [data-structure/03-stack](../../data-structure/03-stack/2-summary.md)
  - Azure 문서는 보상이 꼭 정확한 역순일 필요는 없고 일부는 병렬로 할 수 있다고 덧붙인다. 의존이 있는 걸음끼리만 역순이면 된다.
- **사가 로그(영속 상태 표)** — 걸음 시작·완료를 기록하는 append·갱신 표. 원논문의 save-point와 같은 역할이다. 재시작 시 여기서 이어 간다.
- **멱등 키 집합** — `comp_done(saga_id)` 같은 처리 기록 표에 PK로 넣어 중복 보상을 거른다. 기록과 효과를 **같은 로컬 트랜잭션**에 넣어야 한다. [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
- **교환 가능한 연산** — `qty = qty + 1`처럼 순서와 무관하게 같은 결과를 내는 갱신. 절대값 쓰기는 교환 가능하지 않다.
- **시맨틱 락** — 주문 상태 `PENDING`처럼 "진행 중"을 데이터에 표시해 다른 요청이 판단하게 하는 응용 수준 락(Azure "Saga" 대응책).

## 적용 — 풀어나가는 법

### 1. 설계 순서

```text
  ① 걸음을 나눈다 — 각 걸음 = 한 서비스의 로컬 트랜잭션(전부 아니면 전무)
  ② 걸음마다 분류 — 보상 가능 / 피벗 / 재시도
  ③ 되돌릴 수 없는 일(메일·출고·확정 결제)을 피벗 뒤로 옮긴다
  ④ 보상을 쓴다 — 상대 연산 + 보상 ID 멱등, 업무 규칙 반영(취소 수수료 등)
  ⑤ 사가 상태를 영속한다 — 재시작 시 이어 가기
  ⑥ STUCK이 사람에게 닿는 경로 — 알림·대시보드·수동 처리 런북
```

- 결제는 *승인(authorize)* 과 *확정(capture)* 을 나누면 확정을 피벗으로 미룰 수 있다. 승인 취소(void)는 보상 가능 걸음이 된다.
- 재고는 *예약*으로 잡고 마지막에 확정하면 중간 상태 노출이 줄어든다(시맨틱 락).

### 2. 보상 코드 모양 (Java)

```java
// 재고 서비스의 보상 핸들러 — 보상 ID 멱등 + 상대 연산 + 같은 로컬 트랜잭션
@Transactional
public void compensateReserve(String sagaId, String sku, int qty) {
    int inserted = jdbc.update(
        "INSERT INTO compensation_done(saga_id, step) VALUES (?, 'RESERVE') ON CONFLICT DO NOTHING", sagaId);
    if (inserted == 0) return;                                  // 이미 보상함 — 효과 없이 성공으로 응답
    jdbc.update("UPDATE stock SET qty = qty + ? WHERE sku = ?", qty, sku);
}
```

- 보상이 "대상 없음"(예: 결제 취소가 결제 승인보다 먼저 도착)으로 실패하면, 그 사실을 기록해 두고 뒤늦은 승인을 즉시 취소한다. 원본 08-saga 장애 2번 참고.

### 3. 진단 질의 — 멈춘 사가 찾기

```sql
-- 사가 상태 표가 있다면: 오래 머문 사가
SELECT state, count(*), min(updated_at)
FROM saga_instance
WHERE state NOT IN ('COMPLETED', 'COMPENSATED')
  AND updated_at < now() - interval '10 minutes'
GROUP BY state;

-- 보상까지 실패한 사가 (사람 확인 대상)
SELECT saga_id, last_error, updated_at FROM saga_instance WHERE state = 'STUCK' ORDER BY updated_at;
```

- Temporal·Camunda 같은 워크플로 엔진, AWS Step Functions(`Catch`로 보상 상태로 넘기는 흐름)를 쓰면 상태 영속·재시도·타임아웃을 엔진이 맡는다. 보상 로직과 멱등은 여전히 애플리케이션 책임이다.

## 장애 시나리오와 대처

### 1. 보상 실패 → 반쯤 된 주문 (커리큘럼 ⚠)

- **현상**: 결제는 환불됐는데 재고가 복구되지 않았다. 또는 그 반대.
- **보이는 형태**: 사가 표에 `COMPENSATING`이 오래 머문다. 재고 서비스 로그에 같은 보상 요청이 계속 실패(`500`, 제약 위반).
- **원인**: 보상 트랜잭션도 실패할 수 있다(Azure "Compensating Transaction"). 일시 장애면 재시도로 풀리지만, 보상 코드 버그면 몇 번을 돌려도 같다(원논문 6절의 "stuck").
- **대처**
  - 보상은 재시도 가능하게(멱등) 만들고, 지수 백오프로 재시도한다.
  - 재시도 상한을 넘으면 `STUCK`으로 올리고 사람에게 알린다. 조용히 넘기면 대사에서야 발견된다.
  - 실험에서처럼 절대값 보상은 "성공"으로 보이면서 데이터를 틀리게 만든다. 이 경우 오류 로그조차 없다.

### 2. 보상 불가 작업을 앞에 둔 설계 누락 (커리큘럼 ⚠)

- **현상**: "주문 완료" 메일이 나갔는데 결제가 실패해 주문이 취소됐다. 고객 문의가 온다.
- **보이는 형태**: 메일 발송 로그 시각이 결제 실패보다 앞선다. 정정 메일이 한 통 더 나간다.
- **원인**: 메일 발송은 보상할 수 없다. 정정 메일을 한 번 더 보낼 수 있을 뿐이다. 이런 걸음을 피벗 앞에 두었다.
- **대처**: 걸음을 보상 가능 / 피벗 / 재시도로 분류하고, 보상 불가 작업을 피벗 뒤 재시도 구간으로 옮긴다. 메일은 "주문 확정" 이벤트를 받아 보내는 별도 단계로 만든다.

### 3. 동시 사가가 서로의 변경을 덮는다 (lost update)

- **현상**: 재고 합계가 실제 창고 수량보다 많다. 취소가 몰린 날 더 벌어진다.
- **보이는 형태**: 오류 없음. 대사에서만 차이가 난다(실험: +56~+63).
- **원인**: 보상이 "읽어 둔 옛 값"을 쓴다. 사가에는 격리가 없어 그사이 다른 사가가 같은 행을 바꿨다.
- **대처**: 상대 연산(교환 가능 갱신)으로 바꾼다. 꼭 값을 비교해야 하면 버전 조건부 갱신(`WHERE version = ?`)으로 다시 읽고 판단한다(Azure의 *reread values*).

### 4. 조정자가 죽어 어디까지 했는지 모른다

- **현상**: 재시작 뒤 같은 주문의 결제가 두 번 시도되거나, 반대로 영원히 `PENDING`이다.
- **보이는 형태**: 같은 주문 id로 걸음 로그가 처음부터 다시 찍힌다. 또는 아무 로그도 없이 멈춰 있다.
- **원인**: 진행 상태가 메모리에만 있었다.
- **대처**: 걸음 전후로 사가 표에 기록하고, 재시작 시 `DONE`이 아닌 사가를 기록된 단계부터 이어 간다. 참가자 호출에 멱등 키(사가 id + 걸음)를 붙인다. 23번 실험에서 이 방식으로 halt 10번 뒤에도 100건이 모두 완료됐다.

## 핵심 문장

- 사가는 로컬 트랜잭션 T1…Tn을 차례로 커밋하고, 실패하면 보상 Cj…C1을 거꾸로 실행한다. 결과는 "전부" 또는 "의미상 없던 일"이다.
- 보상은 옛 값을 복원하는 것이 아니다. 그사이 남이 바꾼 값을 덮지 않도록 상대 연산으로, 그리고 보상 ID로 멱등하게 쓴다.
- 사가에는 격리가 없다. 중간 상태가 보이고, 동시 사가끼리 lost update가 난다. 시맨틱 락·교환적 갱신·재확인으로 막는다.
- 되돌릴 수 없는 일은 피벗 뒤에 둔다. 피벗을 넘으면 보상이 아니라 재시도로 끝까지 간다.
- 보상도 실패한다. 재시도 상한을 넘은 사가는 STUCK으로 올려 사람에게 보낸다.

## 관련 주제·근거

- 선행
  - [14-two-phase-commit](../14-two-phase-commit/2-summary.md) — 원자적 커밋을 프로토콜로 얻는 방법과 그 비용
  - 원본 [ops-patterns/08-saga](../../ops-patterns/08-saga/2-summary.md) — 보상 순서·결과 타입·기초 장애
- 후속·연결
  - [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 각 걸음이 "DB 갱신 + 다음 걸음 메시지"를 원자적으로 하는 방법
  - [23-orchestration-vs-choreography](../23-orchestration-vs-choreography/2-summary.md) — 사가를 누가 조정하나, 조정자 크래시 복구 실험
  - [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md) — 보상 멱등의 저장소
  - [systems/orchestration-choreography](../../systems/orchestration-choreography/2-summary.md) — 피벗·격리 대응책을 다룬 원고
  - [database/14-isolation-levels-and-anomalies](../../database/14-isolation-levels-and-anomalies/2-summary.md) — lost update의 정의
- 논문·교재
  - Garcia-Molina, Salem, "Sagas", SIGMOD 1987 — LLT 문제, 사가 정의, 보장 `T1..Tn` 또는 `T1..Tj, Cj..C1`, 보상은 의미상 되돌림이며 옛 좌석 수를 저장해 복원하면 안 됨(1절 서론), 역방향·순방향 복구와 save-point, 보상 오류 시 "the system is stuck"(6절) <https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf>
  - Richardson, 『Microservices Patterns』(2018) 4장 — 보상 가능·피벗·재시도 트랜잭션, 격리 대응책
  - microservices.io "Pattern: Saga" — 로컬 트랜잭션의 연속, 자동 롤백 없음·격리 없음, 코레오그래피·오케스트레이션 <https://microservices.io/patterns/data/saga.html>
  - Azure Architecture Center "Compensating Transaction pattern" — 원래 상태 복원은 동시 변경을 덮을 수 있음, 보상도 실패할 수 있음, 진행 기록·멱등 <https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction>
  - Azure Architecture Center "Saga distributed transactions pattern" — compensable·pivot·retryable, lost update·dirty read·fuzzy read, semantic lock·commutative updates·pessimistic view·reread values·version files <https://learn.microsoft.com/en-us/azure/architecture/patterns/saga>
- 실험 목록
  - `SagaExp.java` + `exp15.sh` — 전용 PostgreSQL 17.11 컨테이너 안 DB 3개, Java 21, 사가 200개·스레드 8·배송 실패 30%. 보상 없음(-60) / 절대값 보상(실행마다 다름, +56~+63) / 상대값(+0) / 상대값 + 중복 보상(+60) / 상대값 + 보상 ID 멱등 + 중복 보상(+0). 절대값 줄은 다섯 번, 나머지는 두 번 실행.
