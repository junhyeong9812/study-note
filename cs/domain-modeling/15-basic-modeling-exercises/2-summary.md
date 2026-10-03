# domain-modeling/15-basic-modeling-exercises — 기초 모델링 연습 30편 트랙 안내 — 정리 (힌트)

## 해결하는 문제

엔티티·값 객체·애그리거트·정책 같은 말은 읽으면 이해되지만, 빈 화면에 요구사항 한 줄을 받으면 어디서부터 모델을 세울지 막힌다. 개념 노트(01~14)만 읽고 넘어가면 "설명은 할 수 있는데 짜지는 못하는" 상태로 남는다.

```text
  개념 노트(01~14)                       연습 트랙(basic 30편)
  "정책은 값으로 올려라"            ─►    "10분까지 무료, 하루 최대 2만 원" — 무엇이 정책 값인가?
  "구간은 반열린으로"               ─►    체크아웃 날은 숙박일인가?
  "상태는 전이 표로"                ─►    배송 중 주문을 취소하면?
  "금액은 BigDecimal, 반올림은 한 번" ─►   청구 + 환불이 월 요금과 같아야 한다
```

- 이 트랙의 30편은 [`basic/`](../basic/) 컬렉션에 그대로 있다. 이 노트는 그 컬렉션을 **어떤 순서로, 무엇을 연습하려고** 푸는지 안내한다. 문제 원문은 각 편에 있다.

쉬운 예: 운전 교본을 다 읽어도 주차는 직접 해 봐야 는다. 교본의 "핸들을 끝까지 돌린다"가 실제 차에서 언제인지는 해 봐야 안다.

똑같은 구조다: 30편은 모두 **"요구사항 한 줄 → 그 줄이 말하지 않는 결정 찾기 → 결정을 정책 값·enum으로 올리기 → 두 해석을 같은 코드로 돌려 갈리는 건수 재기"** 를 반복한다.

실무 예: 기획서의 "5만원 이상 무료 배송", "7일 이내 환불", "밤에는 알림 금지" 같은 한 줄이 실제로 들어오는 모양이다. 이 트랙의 주제(주차·예약·구독·쿠폰·세금·정산·배차)가 전부 그런 한 줄에서 시작한다.

## 동작·원리

### 1. 한 편의 구조 — 모든 문제가 같은 틀

```text
  1-question.md                 2-summary.md                  3-answer.md
  A. 과제: 규칙 + TODO 1~6  ─►   해결하는 문제(빈칸)       ─►   TODO 정답 + 측정 해석
  B. 개념: 측정·함정·연결        동작·원리(규칙별)
  C. 통일 골격 질문              장애(경계·모서리 표)
```

- 문제는 TODO 단위로 나뉜다(예: 01번은 `minutesParked`·`feeForMinutes`·`charge`·`nextWindowEnd`·`chargeFor` 다섯 TODO).
- **대조군 구현**이 거의 모든 편에 있다. 틀린 해석(예: 자정 무시, 두 번 반올림, 안정성 없는 비교자)을 일부러 남겨 두고 무작위 입력에서 답이 갈리는 건수를 센다.
  - *대조군*: 비교하려고 일부러 다른 규칙으로 짠 구현. 갈림이 "구석"인지 "본체"인지를 숫자로 보여준다.

### 2. 개념 지도 — 30편이 연습하는 것

```text
                        ┌───────────── 정책을 값으로 올리기 (거의 전부) ─────────────┐
                        │                                                         │
  시간·구간               상태·수명 주기           돈·계산 순서              검증·판정 결과
  01 주차 요금            09 주문 상태             06 구독 일할              15 쿠폰 사유
  04 숙박(반열린 구간)     10 결제 취소(멱등)        17 장바구니 할인          16 프로모 코드
  05 근태(짝짓기)         11 배송 추적(두 시각)     18 배송비                 21 대출 심사(결측)
  07 알림(조용 시간)       13 재고(예약/확정)        19 누진세                 27 메뉴 옵션(집행)
  08 회의 시간 찾기        14 포인트(덩어리 장부)    20 보험료(나이 기준)
  29 환승 요금            12 게임 버프(중첩 규칙)    22 정산(잔돈 배분)
                                                 23 매출 보고(취소 귀속)
  순서·배정                                       계층·그래프
  02 좌석(연속 블록)  03 대기열(굶주림·안정성)     25 조직도(순환)  26 카테고리(경로)
  24 순위(동점)      30 배차(처리 순서)            28 친구 추천(빼는 규칙)
```

### 3. 문제 → 개념 표

| 문제 | 핵심 개념 | 이어지는 새 leaf |
|---|---|---|
| [01-parking-fee](../basic/01-parking-fee/2-summary.md) | "하루"·"까지"의 뜻을 정책 값으로, 창 단위 조각내기 | [03-ubiquitous-language](../03-ubiquitous-language/2-summary.md) · [08-domain-services-and-policies](../08-domain-services-and-policies/2-summary.md) · [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| [02-seat-reservation](../basic/02-seat-reservation/2-summary.md) | 배정 우선 규칙, 전부 아니면 전무, 단편화 지표 | [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md) · [08](../08-domain-services-and-policies/2-summary.md) |
| [03-waiting-queue](../basic/03-waiting-queue/2-summary.md) | 우선순위 + 노화, 힙의 불안정성 → 발권 순서 2차 키 | [08](../08-domain-services-and-policies/2-summary.md) |
| [04-hotel-booking](../basic/04-hotel-booking/2-summary.md) | 반열린 구간 `[in, out)`, 겹침 정의, 스위핑 | [04-entities-and-value-objects](../04-entities-and-value-objects/2-summary.md) · [12-time-money-and-units](../12-time-money-and-units/2-summary.md) |
| [05-attendance](../basic/05-attendance/2-summary.md) | 시작/끝 이벤트 짝짓기, 버린 것 세기, 자정 분할 | [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| [06-subscription](../basic/06-subscription/2-summary.md) | 일할 분모·포함 여부·반올림, 환불 = 월 요금 − 청구 | [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| [07-notification](../basic/07-notification/2-summary.md) | 자정 걸침 구간(AND→OR), 처리 순서가 계약 | [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [08](../08-domain-services-and-policies/2-summary.md) |
| [08-meeting-slot](../basic/08-meeting-slot/2-summary.md) | 구간 병합·빼기, 합계 지표 vs 조각 | [04](../04-entities-and-value-objects/2-summary.md) |
| [09-order-state](../basic/09-order-state/2-summary.md) | 전이 표, 빈칸의 의미, APPLIED/IGNORED/REJECTED | [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md) · [06-anemic-vs-rich-model](../06-anemic-vs-rich-model/2-summary.md) |
| [10-payment](../basic/10-payment/2-summary.md) | 멱등키, 상태를 금액에서 파생 | [04](../04-entities-and-value-objects/2-summary.md) · [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) |
| [11-delivery-tracking](../basic/11-delivery-tracking/2-summary.md) | 일어난 시각 vs 받은 시각, 중복 키 | [09-domain-events](../09-domain-events/2-summary.md) |
| [12-game-buff](../basic/12-game-buff/2-summary.md) | 중첩·합산 규칙 enum, 만료 정리 순서 | [08](../08-domain-services-and-policies/2-summary.md) |
| [13-inventory](../basic/13-inventory/2-summary.md) | 예약/확정 분리, 총·물리·가용 세 수량 | [05](../05-aggregates-and-invariants/2-summary.md) · [11](../11-state-machines-in-domain/2-summary.md) |
| [14-points](../basic/14-points/2-summary.md) | 잔액 = 덩어리(lot)의 파생값, 사용 장부 | [24](../24-double-entry-ledger/2-summary.md) |
| [15-coupon](../basic/15-coupon/2-summary.md) | boolean 대신 `List<Reason>`, 고칠 수 있는 사유 | [06](../06-anemic-vs-rich-model/2-summary.md) |
| [16-promo-code](../basic/16-promo-code/2-summary.md) | 정규화 → 검산 → 저장소, 저장·조회 양쪽 정규화 | [04](../04-entities-and-value-objects/2-summary.md) |
| [17-cart-discount](../basic/17-cart-discount/2-summary.md) | 할인 순서·정률 기준·반올림 시점, 적용 내역 | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) · [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) |
| [18-shipping-fee](../basic/18-shipping-fee/2-summary.md) | 무료 기준 금액·판매자별·부분 취소 차액 | [08](../08-domain-services-and-policies/2-summary.md) |
| [19-tax](../basic/19-tax/2-summary.md) | 누진 구간표, 걸친 금액에만 세율 | [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) |
| [20-insurance](../basic/20-insurance/2-summary.md) | 만·연·보험 나이, 하루 차이 절벽 탐지 | [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [03](../03-ubiquitous-language/2-summary.md) |
| [21-loan-scoring](../basic/21-loan-scoring/2-summary.md) | 결측 점수 `Optional` + 대체 정책, 판정 4값 | [22](../22-decision-log-and-provenance/2-summary.md) · [08](../08-domain-services-and-policies/2-summary.md) |
| [22-settlement](../basic/22-settlement/2-summary.md) | 내림 배분 + 잔돈 규칙(최대 잔여법) | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| [23-sales-report](../basic/23-sales-report/2-summary.md) | 취소를 어느 날에서 빼나, 시점 술어 | [21-cqrs](../21-cqrs/2-summary.md) · [25-reconciliation](../25-reconciliation/2-summary.md) |
| [24-leaderboard](../basic/24-leaderboard/2-summary.md) | 정렬과 등수 분리, 동점 규칙 3종 | [03](../03-ubiquitous-language/2-summary.md) |
| [25-org-chart](../basic/25-org-chart/2-summary.md) | 부모 포인터 트리, 전체를 가진 쪽이 순환 검증 | [05](../05-aggregates-and-invariants/2-summary.md) · [10-repositories-and-factories](../10-repositories-and-factories/2-summary.md) |
| [26-category-tree](../basic/26-category-tree/2-summary.md) | 경로 계산 vs 저장(워크로드), 경로가 식별자 | [10](../10-repositories-and-factories/2-summary.md) · [21](../21-cqrs/2-summary.md) |
| [27-menu-option](../basic/27-menu-option/2-summary.md) | 규칙과 집행 방식(거부·교체·확정) 분리 | [11](../11-state-machines-in-domain/2-summary.md) |
| [28-friend-suggestion](../basic/28-friend-suggestion/2-summary.md) | 세는 규칙보다 빼는 규칙, 방향 있는 차단 | [08](../08-domain-services-and-policies/2-summary.md) |
| [29-transfer-fare](../basic/29-transfer-fare/2-summary.md) | 환승 기준점·경계값·한도 처리, 여정 묶기 | [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| [30-dispatch](../basic/30-dispatch/2-summary.md) | 배타 자원 배정에서 처리 순서가 답의 일부 | [08](../08-domain-services-and-policies/2-summary.md) |

## 쓰이는 자료구조·알고리즘

각 편의 「쓰이는 자료구조·알고리즘」 절에서 모았다.

| 자료구조·알고리즘 | 나오는 편 | cs 노트 |
|---|---|---|
| 정책 레코드(불변 record, 생성 시 검증) | 01 `FeePolicy` · 06 `ProrationPolicy` · 07 `QuietHours` · 18 `ShippingPolicy` · 29 `FareRule` | [software-design/19-immutability-and-value-objects](../../software-design/19-immutability-and-value-objects/2-summary.md) |
| 반열린 구간 `[start, end)`·겹침 판정 | 04 · 06 · 08 · 12 · 14 | [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md) |
| 스위핑(이벤트 정렬 + 누적)·구간 병합 | 04 · 08 | [algorithm/30-sweeping](../../algorithm/30-sweeping/2-summary.md) |
| 창 단위 조각내기 루프(자정 분할) | 01 · 05 | — |
| 우선순위 큐(이진 힙) + 2단 비교자 | 03 | [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) |
| 전이 표(인접 리스트) + BFS 도달성 | 09 | [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) |
| 멱등키 저장소(집합 + 맵) | 10 · 11 | [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) |
| 덩어리(lot) 목록 + 사용 장부 | 14 | [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) |
| `BigDecimal` + `RoundingMode`, 최대 잔여법 | 06 · 12 · 17 · 19 · 20 · 22 | [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| 누적합·구간표 | 19 · 20 | [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md) |
| 정렬 맵(`TreeMap<LocalDate, …>`) 집계 | 05 · 23 | — |
| 다중 키 정렬·등수 | 24 · 28 · 30 | — |
| 부모 포인터 트리·순환 탐지·BFS | 25 · 26 | [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) |
| 그래프 2단 탐색·해시맵 카운팅 | 28 | [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) |
| 탐욕 배정 | 02 · 30 | [algorithm/23-greedy](../../algorithm/23-greedy/2-summary.md) |
| 슬라이딩 창(연속 k칸) | 02 | [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md) |

## 적용 — 풀어나가는 법

### 1. 한 편을 푸는 순서

1. 1-question의 "규칙" 줄만 읽고, **그 줄이 정하지 않은 결정**을 먼저 적는다(예: 01번이면 "까지"의 포함 여부, 초과 1분의 올림, "하루"의 기준).
2. 결정마다 정책 값·enum 이름을 붙인다. 아직 코드는 쓰지 않는다.
3. TODO를 순서대로 구현한다. 생성자·팩터리에서 말이 안 되는 값을 거부한다.
4. 대조군과 함께 돌려 **갈리는 건수**를 센다. 갈림이 구석이 아니라 본체인 편이 많다(예: 01번은 무작위 주차 1,000건에서 네 가지 해석 차이가 각각 444~943건 갈렸다 — 01 §측정 표).
   - 참고: 01 §측정의 "넷 다 절반이 넘었다"는 같은 표의 444/1,000(올림 vs 버림)과 맞지 않는다. 절반을 넘은 것은 넷 중 셋이다.
5. 2-summary의 장애 표(경계·모서리)로 내 구현을 점검한다.
6. 3-answer로 채점하고, 측정 해석을 내 말로 다시 쓴다.

### 2. 권장 풀이 순서 — 6단계

번호 순서(01→30)로 풀어도 된다. 개념이 쌓이는 순서로 묶으면 다음과 같다. 선행은 [12-time-money-and-units](../12-time-money-and-units/2-summary.md)(커리큘럼 기준).

**1단계 — 빈칸을 정책 값으로 (시간·구간)**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [01](../basic/01-parking-fee/1-question.md) | 요금 세 줄이 해석마다 다른 금액 | 무료·기본·단위를 끊는 순서, 자정 vs 24시간 상한 |
| [04](../basic/04-hotel-booking/1-question.md) | 같은 날 교체 vs 하루 비우기 | 반열린 구간, 동률 정렬 = 업무 규칙, peak 계산 |
| [08](../basic/08-meeting-slot/1-question.md) | 다 같이 비는 시간 찾기 | 여유 붙이기 → 병합 → 빼기, 합계가 숨기는 조각 |
| [05](../basic/05-attendance/1-question.md) | 기기 기록의 누락·중복·순서 섞임 | 사원별 짝짓기, 버린 줄 세기 |
| [07](../basic/07-notification/1-question.md) | 밤 알림 금지 한 줄 | 자정 걸침 판정, 중복 제거와 미루기의 순서 |
| [29](../basic/29-transfer-fare/1-question.md) | 환승 30분·최대 4회 | 기준점·`<=` vs `<`·한도 처리 |

**2단계 — 돈은 한 번만 반올림**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [06](../basic/06-subscription/1-question.md) | 중도 해지 일할 환불 | 분모·포함 여부·반올림 4결정, 환불을 뺄셈으로 |
| [22](../basic/22-settlement/1-question.md) | 비율 배분의 잔돈 | 내림 + 잔돈 규칙, 합계 보존 |
| [17](../basic/17-cart-discount/1-question.md) | 쿠폰 두 장의 순서 | 순서·정률 기준·반올림 시점을 매개변수로 |
| [18](../basic/18-shipping-fee/1-question.md) | 무료 배송 기준 | 기준 금액·판매자별·부분 취소 차액 |
| [19](../basic/19-tax/1-question.md) | 누진세 구간표 | 걸친 금액에만 세율, 두 계산법 교차 검증 |
| [20](../basic/20-insurance/1-question.md) | 같은 사람의 세 나이 | 나이 기준 enum, 하루 차이 절벽 |

**3단계 — 상태와 장부**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [09](../basic/09-order-state/1-question.md) | 상태 64칸 표의 빈칸 | 전이 표, 결과 3갈래, 판정 순서 |
| [10](../basic/10-payment/1-question.md) | 재시도되는 취소 | 멱등키를 금액보다 먼저, 파생 상태 |
| [11](../basic/11-delivery-tracking/1-question.md) | 늦게 올라온 스캔 | 일어난 시각으로 판정, 중복 키에 수신 시각 금지 |
| [13](../basic/13-inventory/1-question.md) | 언제 재고를 빼나 | 예약/확정, 세 수량 파생 |
| [14](../basic/14-points/1-question.md) | 만료가 다른 포인트 | 덩어리 목록, 차감 순서, 취소 시 되돌릴 곳 |
| [12](../basic/12-game-buff/1-question.md) | 같은 버프를 또 걸면 | 중첩·합산 규칙 enum, 만료 정리 순서 |
| [23](../basic/23-sales-report/1-question.md) | 취소를 어느 날에서 빼나 | 소급 vs 당일, 과거 수치가 바뀐 날 세기 |

**4단계 — 판정 결과를 값으로**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [15](../basic/15-coupon/1-question.md) | 쿠폰을 못 쓰는 이유 | `List<Reason>`, 사유 순서 = 화면 |
| [16](../basic/16-promo-code/1-question.md) | 손으로 친 코드 | 정규화 → 검산 → 조회, 가드 순서 |
| [21](../basic/21-loan-scoring/1-question.md) | 점수가 없는 항목 | `Optional` + 결측 정책, 결격 → 심사 불가 → 점수 |
| [27](../basic/27-menu-option/1-question.md) | 같이 못 고르는 옵션 | 규칙과 집행(거부·교체·확정) 분리 |

**5단계 — 순서와 배정**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [03](../basic/03-waiting-queue/1-question.md) | 우대 손님 먼저 | 노화, 힙 안정성 → 발권 순서 2차 키, 3명 이상 테스트 |
| [02](../basic/02-seat-reservation/1-question.md) | 일행 붙여 앉히기 | 통로·우선순위·부분 배정, 고아 좌석 |
| [24](../basic/24-leaderboard/1-question.md) | 동점자의 등수 | 정렬과 등수 분리, 동점·경계 규칙 |
| [30](../basic/30-dispatch/1-question.md) | 가장 가까운 기사 | 처리 순서 전략, 총합·최악·미배차 함께 재기 |

**6단계 — 계층과 그래프**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [25](../basic/25-org-chart/1-question.md) | 상사 사번 한 칸 | 전체 순환 검증, 지울 때 밑을 어떻게 |
| [26](../basic/26-category-tree/1-question.md) | 카테고리 경로 | 계산 vs 저장 손익분기, 형제 이름 중복 |
| [28](../basic/28-friend-suggestion/1-question.md) | 친구의 친구 추천 | 빼는 규칙, 방향 있는 차단, 동점 순서 |

### 3. 막히면

- 결정을 못 찾겠으면 2-summary의 「해결하는 문제」 그림만 본다. 대부분 "같은 한 줄 → 두 해석 → 다른 결과" 그림이다.
- 측정 결과를 외우지 않는다. "왜 갈림이 이렇게 큰가"를 설명할 수 있으면 된다.

## 장애 시나리오와 대처

연습에서 자주 틀리는 모델링 실수다. 각 편 장애 절(경계·모서리 표)에서 같은 모양이 반복된다.

### 1. 구간 끝을 포함한다 — 하루·한 칸이 어긋난다

- 현상: 2박 숙박이 3일로 계산된다. 맞닿은 회의 사이에 길이 0 빈 구간이 생겨 예외가 난다.
- 보이는 형태: 경계 날짜에서만 테스트 실패(04 체크아웃 날, 06 말일 해지, 08 맞닿은 구간).
- 원인: 닫힌 구간 `[start, end]`로 생각했다.
- 대처: 반열린 구간 `[start, end)`로 통일하고, "딱 경계" 값을 테스트에 넣는다. 일부러 포함하는 규칙(01 "10분까지" 포함)은 이름으로 드러낸다.

### 2. 두 번 반올림한다 — 합이 원래 금액과 안 맞는다

- 현상: 청구 + 환불 ≠ 월 요금, 몫의 합 ≠ 총액.
- 보이는 형태: 대량 무작위 입력에서 1원 차이가 다수 건(06번 측정: 1,000건 중 635건).
- 원인: 두 값을 각각 계산해 각각 반올림했다.
- 대처: 한 번만 반올림하고 나머지는 뺄셈으로 만든다(06). 잔돈은 이름 붙은 규칙으로 준다(22). → [14](../14-money-arithmetic-rounding-allocation/2-summary.md)

### 3. 판정 순서를 정하지 않는다 — 같은 입력이 경로마다 다른 답

- 현상: 중복 이벤트가 성공으로 세지거나 거절로 세진다. 미뤄진 알림끼리 서로를 지운다.
- 보이는 형태: 자기 전이·중복 키가 있는 경우에만 갈린다(09, 07, 10, 16).
- 원인: "같은 상태인가 → 표에 있나 → 거부", "중복 제거 → 조용 시간" 같은 순서가 코드에 암묵적으로 정해졌다.
- 대처: 판정 순서를 계약으로 적고 테스트로 고정한다.

### 4. 조용히 버린다 — 숫자가 왜 작은지 아무도 모른다

- 현상: 근무 시간·알림 수가 실제보다 적다.
- 보이는 형태: 오류 없음. 합계만 작다(05 짝 안 맞는 줄 — 9,723줄 중 1,109줄).
- 비슷한 모양: 12는 만료된 버프를 치우지 않아도 합계가 같아 결과 테스트가 못 잡는다(만료 정리를 지워도 테스트가 안 깨졌다 — 12 규칙 4). 그래서 보유 개수 `stored()`를 관측 창으로 연다.
- 원인: 처리 못 한 입력을 건너뛰기만 하고 세지 않았다.
- 대처: 버리는 건 정책이지만 **센다**(`unpairedCount` 같은 관측 창). 실패를 숨기지 않는다.

### 5. 결과를 boolean 하나로 준다 — "왜 안 되나"에 답할 수 없다

- 현상: 쿠폰을 못 쓰는 이유를 하나씩만 알려줘 손님이 여러 번 시도한다. 재시도가 장애 경보를 울린다.
- 보이는 형태: 호출자가 false의 의미를 추측한다(15, 09, 13).
- 원인: 답할 질문이 둘 이상(바뀌었나·오류인가·고칠 수 있나)인데 한 비트로 줄였다.
- 대처: 결과 enum(APPLIED/IGNORED/REJECTED)이나 사유 목록을 반환 타입으로 만든다.

## 핵심 문장

- 30편이 반복해서 가르치는 것은 하나다 — **요구사항 한 줄이 말하지 않는 결정을 찾아 이름 붙은 값으로 올리고, 해석을 바꿔 돌려 갈리는 건수를 잰다.**
- 갈림은 구석이 아니라 본체인 경우가 많다 — 재보기 전에는 모른다.
- 경계(구간 끝·반올림 위치·판정 순서)를 명시하지 않으면 코드가 몰래 정한다.
- 버리는 것·실패한 것·고칠 수 있는 사유를 **값으로 드러내는** 것이 모델링의 절반이다.

## 관련 주제·근거

### 선행·후속

- 선행: [12-time-money-and-units](../12-time-money-and-units/2-summary.md) — 커리큘럼상 이 트랙의 선행
- 개념 leaf(위 문제 → 개념 표에서 편별로 연결): [01-domain-vs-application-logic](../01-domain-vs-application-logic/2-summary.md) · [02-pojo-and-persistence-ignorance](../02-pojo-and-persistence-ignorance/2-summary.md) · [03](../03-ubiquitous-language/2-summary.md) · [04](../04-entities-and-value-objects/2-summary.md) · [05](../05-aggregates-and-invariants/2-summary.md) · [06](../06-anemic-vs-rich-model/2-summary.md) · [07-domain-logic-patterns-and-service-layer](../07-domain-logic-patterns-and-service-layer/2-summary.md) · [08](../08-domain-services-and-policies/2-summary.md) · [09](../09-domain-events/2-summary.md) · [10](../10-repositories-and-factories/2-summary.md) · [11](../11-state-machines-in-domain/2-summary.md) · [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [14](../14-money-arithmetic-rounding-allocation/2-summary.md)
- 추적성 단원으로 이어지는 편: 17·21 → [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) · 19 → [23](../23-versioned-rules-and-effective-dating/2-summary.md) · 10·14 → [24](../24-double-entry-ledger/2-summary.md) · 23 → [25](../25-reconciliation/2-summary.md)
- 후속: [26-advanced-modeling-exercises](../26-advanced-modeling-exercises/2-summary.md) — 같은 틀을 정책 버전·기간 마감·감사 재생 등 시간·이력이 얽힌 도메인으로 확장
- 컬렉션: [basic/](../basic/) · [basic/index.md](../basic/index.md) · 영역 표 [curriculum.md](../curriculum.md)

### 근거

- 각 편의 1-question·2-summary·3-answer(컬렉션 안내: [basic/README.md](../basic/README.md))
- 커리큘럼 §13.4 연습 트랙 행(`docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`)
- 이 노트는 트랙 안내라 별도 실험을 두지 않았다. 측정 수치는 각 편 노트에 실린 값을 편 번호와 함께 옮겼다.
