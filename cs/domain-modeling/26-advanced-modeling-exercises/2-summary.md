# domain-modeling/26-advanced-modeling-exercises — 심화 모델링 연습 30편 트랙 안내 — 정리 (힌트)

## 해결하는 문제

기초 트랙([15](../15-basic-modeling-exercises/2-summary.md))은 "한 줄 규칙의 빈칸"을 한두 개씩 찾았다. 실제 업무 규칙은 빈칸이 **여러 축으로 겹치고**, 시간이 지나면서 규칙·데이터·결과가 **바뀐다**.

```text
  기초 트랙                                  심화 트랙
  "하루 최대 2만 원" — 하루가 뭐지?         "7일 이내 환불" — 첫날을 세나? × 할인은 어떻게 나누나? × 반품 배송비는?
     결정 1~2개                               결정 3축 → 조합 18개 (04)
  지금 한 번 계산                            정책이 바뀌었다 · 정정이 소급됐다 · 마감 뒤 거래가 왔다 · 재시도 결과를 모른다
                                              → "그때의 답"과 "지금의 답"이 갈린다 (09·10·15·17)
```

- 이 트랙의 30편은 [`advanced/`](../advanced/) 컬렉션에 그대로 있다. 이 노트는 그 컬렉션을 어떤 순서로, 무엇을 연습하려고 푸는지 안내한다. 문제 원문은 각 편에 있다.

쉬운 예: 장보기 영수증 한 장의 합계를 내는 것과, 한 달 치 가계부를 마감하는 것의 차이다. 마감에는 "늦게 온 카드 명세", "환불이 다음 달에 들어온 것", "지난달 숫자를 고쳐야 하나"가 붙는다.

똑같은 구조다: 결정 축마다 enum을 만들고, 축의 **조합**을 같은 코드로 돌려 결과가 얼마나 벌어지는지 잰다. 그리고 결과에 **근거(어느 판·어느 시점·어느 단계)** 를 함께 남긴다.

실무 예: 급여 가산, 다중 쿠폰, 요금제 변경, 다통화, 부가세, 할부, 지연 배상, 정책 버전, 가격 이력, 재고 홀드, 계약 갱신, 마일리지 소멸, 월 마감, 감사 재생, 배치 재시도, 정산 대사, 결재선, 레이트 리밋, 합포장, 창고 출고, 근무표, 추첨, 랜덤 굿즈, A/B 배정, 권한, 통관, 거래처 등급.

## 동작·원리

### 1. 한 편의 구조 — 기초와 같은 틀, 축이 셋

```text
  1-question.md                        2-summary.md
  0. 규칙 한 줄(시작 계산)               해결하는 문제: 빈칸 = enum 축 셋
  1~n. TODO + 주어진 계약(record)   ─►   동작·원리: 축별 규칙
  측정 — 조합별로 답이 갈리는 정도        장애: 함정 → 올바른 처리 표
  함정                                  핵심 문장: "한 줄에 결정 셋"
```

- 많은 편이 결정 축 셋의 **데카르트 곱**을 측정한다(예: 04 환불 2×3×3 = 18조합 — 금액을 가르는 측정은 그중 3×3 = 아홉 조합, 08 지연 배상 2×3×2 = 12조합, 17 배치 재시도 3×3×2 = 18조합, 20 결재선 2×3×3 = 18조합, 29 통관 8조합).
  - *데카르트 곱*: 축마다 하나씩 고른 모든 조합. 축이 셋이면 조합 수는 세 축 크기의 곱이다.
- **주어진 계약**(record·주어진 코드)이 따로 있다. 구현할 부분(TODO)과 이미 정해진 모양을 구분해 읽는 연습이다.

### 2. 개념 지도 — 기초 트랙에 무엇이 더해졌나

```text
  ┌──────────── 결정 축 셋을 enum으로, 조합을 측정으로 (거의 전부) ────────────┐
  │                                                                       │
  돈 계산의 순서                시간·버전·이력                   잡아두기·배정
  01 급여 가산                  09 정책 버전(시행일 판)           11 재고 홀드(TTL)
  02 다중 쿠폰                  10 가격 이력(바이템포럴)          12 좌석 홀드(연석)
  03 요금제 변경 일할            13 계약 갱신(통지 기한)           22 합포장(빈 패킹)
  04 환불(초일·할인 배분)        15 월 마감(늦은 거래)             23 창고 출고(창고 간)
  05 다통화(최소 단위)           19 순위 재집계(기준 시점)          26 랜덤 굿즈(세트 보장)
  06 부가세(과세·면세 배분)      24 근무표(주 경계·야간)
  07 할부(나머지 회차)           30 거래처 등급(창·하락)
  08 지연 배상(근거 담은 결과)
                                재생·재시도·대사                 흐름·권한·한도
                                14 마일리지 소멸(사건 재생)        20 결재선(정족수)
                                16 감사 재생(중복·REVERSE)         21 레이트 리밋(창)
                                17 배치 재시도(결과 모름)          25 추첨(1인의 정의)
                                18 정산 대사(짝 찾기)              27 A/B 배정(해시)
                                                                28 권한(메타 규칙)
                                                                29 통관(판정 금액·묶음)
```

### 3. 문제 → 개념 표

| 문제 | 핵심 개념 | 이어지는 새 leaf |
|---|---|---|
| [01-payroll](../advanced/01-payroll/2-summary.md) | 한 분에 겹친 가산의 합산 규칙, 자정 넘는 근무 | [08-domain-services-and-policies](../08-domain-services-and-policies/2-summary.md) · [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| [02-promotion](../advanced/02-promotion/2-summary.md) | 적용 순서·배타 규칙, 정률이 끼면 순서가 계약 | [08](../08-domain-services-and-policies/2-summary.md) · [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| [03-subscription-change](../advanced/03-subscription-change/2-summary.md) | 분모·바꾼 날 소유·다운그레이드, 변경과 해지가 같은 식 공유 | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) · [12-time-money-and-units](../12-time-money-and-units/2-summary.md) |
| [04-refund](../advanced/04-refund/2-summary.md) | 초일 산입·할인 배분·반품 배송비, 거절을 값으로 | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) · [06-anemic-vs-rich-model](../06-anemic-vs-rich-model/2-summary.md) |
| [05-multi-currency](../advanced/05-multi-currency/2-summary.md) | 최소 단위 정수 + 통화, 환율 그래프, 반올림 위치 | [04-entities-and-value-objects](../04-entities-and-value-objects/2-summary.md) · [12](../12-time-money-and-units/2-summary.md) · [14](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| [06-tax](../advanced/06-tax/2-summary.md) | 과세·면세·영세율 할인 배분, 마지막 몫은 빼기 | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| [07-installment](../advanced/07-installment/2-summary.md) | 내림 몫 + 나머지 회차, 원리금 균등 vs 애드온 | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| [08-delay-compensation](../advanced/08-delay-compensation/2-summary.md) | 날 세기·면책·상한 기준, 결과에 세 단계 날 수 | [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) |
| [09-policy-version](../advanced/09-policy-version/2-summary.md) | 시행일 붙은 판 쌓기, 기준 날짜(Anchor) | [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) |
| [10-price-history](../advanced/10-price-history/2-summary.md) | 유효 시각 + 기록 시각(바이템포럴), 소급 정정 | [23](../23-versioned-rules-and-effective-dating/2-summary.md) |
| [11-stock-reservation](../advanced/11-stock-reservation/2-summary.md) | HELD → CONFIRMED/RELEASED, TTL 경계, 지연 판정 vs 배치 | [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md) · [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md) |
| [12-seat-hold](../advanced/12-seat-hold/2-summary.md) | 모양이 상품, first/best fit, 전부 아니면 전무 | [05](../05-aggregates-and-invariants/2-summary.md) |
| [13-contract-renewal](../advanced/13-contract-renewal/2-summary.md) | 통지 기준일·유예 상태·갱신 길이, `plusYears` | [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [11](../11-state-machines-in-domain/2-summary.md) |
| [14-mileage-expiry](../advanced/14-mileage-expiry/2-summary.md) | 적립분 목록 + 사건 재생, 빼는 순서·되돌릴 곳 | [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) |
| [15-period-close](../advanced/15-period-close/2-summary.md) | 발생·도착 두 시각, 마감 시각, 늦은 거래 따로 세기 | [25-reconciliation](../25-reconciliation/2-summary.md) · [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| [16-audit-replay](../advanced/16-audit-replay/2-summary.md) | 줄 세우기·중복·되돌리기 규칙으로 재생 | [24](../24-double-entry-ledger/2-summary.md) · [22](../22-decision-log-and-provenance/2-summary.md) |
| [17-batch-retry](../advanced/17-batch-retry/2-summary.md) | 실패 규칙 × 재시도 범위 × 모르는 결과 | [25](../25-reconciliation/2-summary.md) |
| [18-settlement-match](../advanced/18-settlement-match/2-summary.md) | 참조값 없는 금액 매칭의 함정, 대사 | [25](../25-reconciliation/2-summary.md) |
| [19-leaderboard-recount](../advanced/19-leaderboard-recount/2-summary.md) | 종료 시점 vs 지금 기준 순위, 동점 | [22](../22-decision-log-and-provenance/2-summary.md) · [23](../23-versioned-rules-and-effective-dating/2-summary.md) |
| [20-approval-chain](../advanced/20-approval-chain/2-summary.md) | 순서·정족수·금액 변경, 버린 클릭 세기 | [11](../11-state-machines-in-domain/2-summary.md) · [09-domain-events](../09-domain-events/2-summary.md) |
| [21-throttle](../advanced/21-throttle/2-summary.md) | 창 자르기·세는 키·막힌 요청 카운트 | [08](../08-domain-services-and-policies/2-summary.md) |
| [22-parcel-split](../advanced/22-parcel-split/2-summary.md) | 무게·부피 두 축 상한, 담는 순서 | [08](../08-domain-services-and-policies/2-summary.md) |
| [23-warehouse-pick](../advanced/23-warehouse-pick/2-summary.md) | 합계는 충분한데 한 창고엔 모자람, 걸침 처리 | [05](../05-aggregates-and-invariants/2-summary.md) · [08](../08-domain-services-and-policies/2-summary.md) |
| [24-shift-roster](../advanced/24-shift-roster/2-summary.md) | 주 경계·야간 근무 귀속·연속 세기 | [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| [25-lottery-draw](../advanced/25-lottery-draw/2-summary.md) | "1인"의 정의, 시드 고정으로 재현 가능한 추첨 | [03-ubiquitous-language](../03-ubiquitous-language/2-summary.md) · [22](../22-decision-log-and-provenance/2-summary.md) |
| [26-photocard-set](../advanced/26-photocard-set/2-summary.md) | 보장 방식 × 중복 허용 × 나머지 고르기 | [08](../08-domain-services-and-policies/2-summary.md) |
| [27-ab-assign](../advanced/27-ab-assign/2-summary.md) | 열쇠 × 씨앗 해시 버킷, 비율 인상 시 이동 | [08](../08-domain-services-and-policies/2-summary.md) |
| [28-authorization](../advanced/28-authorization/2-summary.md) | 겹치는 규칙의 심판·기본값·상속 | [08](../08-domain-services-and-policies/2-summary.md) |
| [29-customs-clearance](../advanced/29-customs-clearance/2-summary.md) | 판정 금액·묶음·과세 범위 | [08](../08-domain-services-and-policies/2-summary.md) · [14](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| [30-b2b-tier](../advanced/30-b2b-tier/2-summary.md) | 창(연·롤링)·하락 규칙·집계 시점 | [23](../23-versioned-rules-and-effective-dating/2-summary.md) |

## 쓰이는 자료구조·알고리즘

각 편의 「쓰이는 자료구조·알고리즘」 절에서 모았다.

| 자료구조·알고리즘 | 나오는 편 | cs 노트 |
|---|---|---|
| enum 축의 데카르트 곱(전략 선택) | 거의 전부(04·06·07·08·17·20·29 등) | — |
| 비례배분(곱하기 먼저·나누기 한 번), 마지막 몫은 빼기 | 03·04·06·29 | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| 고정 소수점 정수(minor units)·`BigDecimal` | 04·05·07·29 | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| 방향 있는 가중 그래프(환율표) | 05 | [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) |
| 버전 스택(append-only) + "≤ 날짜 중 가장 늦은 판" 탐색 | 09 | [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md) |
| 바이템포럴 레코드(유효 시각 + 기록 시각) | 10 | [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md) |
| 유한 상태 기계 | 11·12·20 (TTL 만료는 11·12) | — |
| 메모리 할당자의 first fit / best fit, 단편화 지표 | 12 | [data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md) |
| 빈 패킹 first-fit decreasing | 22 | — |
| 이벤트 재생(event sourcing)·멱등 키 집합 | 14·16·20 (17은 멱등 키가 *없어서* 이중 반영이 나는 예) | [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md) |
| 그리디 매칭·재귀 조합 탐색 | 18·23·26 | [algorithm/23-greedy](../../algorithm/23-greedy/2-summary.md) · [algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md) |
| 슬라이딩 로그(덱)·고정 창 | 21·30 | [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md) |
| 시드 고정 의사난수·가중 무작위(누적합) | 19·25·26 | [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md) |
| FNV-1a 해시 + 모듈러 버킷 | 27 | — |
| 부모 포인터 상향 탐색 + 방문 집합 | 28 | — |
| 정렬 맵 주별 집계·연속 구간 세기 | 24 | — |

## 적용 — 풀어나가는 법

### 1. 한 편을 푸는 순서

1. "규칙 한 줄"에서 결정 축을 **셋** 찾는다. 대부분의 편이 축 셋으로 설계돼 있다. 2-summary를 열기 전에 먼저 적어 본다.
2. 축마다 enum 값을 정한다. 한 축 안의 값이 서로 다른 결과를 내는 예를 하나씩 손으로 계산한다(02·04는 1-question에 "손계산" 항목이 있다).
3. 주어진 계약(record·주어진 코드)을 먼저 읽는다. 생성자 검증이 이미 무엇을 막는지 확인한다.
4. TODO를 구현하고 조합 전체를 돌린다. 측정은 "어느 조합이 맞나"가 아니라 "조합 사이가 얼마나 벌어지나"를 본다.
5. 장애 표(함정 → 올바른 처리)로 점검한다. 특히 **개발 자료로만 검증한 함정**(지연 0%·취소 없음·같은 소멸 기간)을 본다.
6. 결과 값에 근거가 남는지 확인한다(08 세 단계 날 수, 09 적용 판, 16 거부된 사건 목록).

### 2. 권장 풀이 순서 — 5단계

커리큘럼 선행은 [21-cqrs](../21-cqrs/2-summary.md)와 [15](../15-basic-modeling-exercises/2-summary.md)다. 번호 순서로 풀어도 된다.

**1단계 — 돈 계산의 순서와 배분**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [01](../advanced/01-payroll/1-question.md) | 연장·야간이 겹친 분 | 합산/곱/최대 규칙, 연장은 481분째부터 |
| [02](../advanced/02-promotion/1-question.md) | 쿠폰 여러 장 | 정액·정률 순서, 배타 쿠폰 선택 |
| [03](../advanced/03-subscription-change/1-question.md) | 월 중간 요금제 변경 | 분모·바꾼 날 소유·다운그레이드, 변경과 해지의 공유 식 |
| [04](../advanced/04-refund/1-question.md) | 7일 이내 환불 | 초일 산입, 할인 배분, 거절을 값으로 |
| [05](../advanced/05-multi-currency/1-question.md) | 통화 섞인 장바구니 | 최소 단위 정수, 역수 환율 금지, 경유 반올림 |
| [06](../advanced/06-tax/1-question.md) | 과세·면세 섞인 주문 | 배분 후 마지막 몫 빼기, 포함가 역산 |
| [07](../advanced/07-installment/1-question.md) | 할부 상환표 | 내림 몫 + 나머지 회차, 이자율 0, 마지막 잔액 |
| [08](../advanced/08-delay-compensation/1-question.md) | 지연 배상 | 날 세기·면책·상한, 결과에 설명 담기 |

**2단계 — 시간·버전·이력**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [09](../advanced/09-policy-version/1-question.md) | 정책 개정 전후 주문 | 시행일 판, 주문·신청·처리 중 기준일 |
| [10](../advanced/10-price-history/1-question.md) | 소급 가격 정정 | 유효·기록 두 시각, `asOf` 조회 |
| [13](../advanced/13-contract-renewal/1-question.md) | 자동 갱신 계약 | 통지 기한, 유예 상태, 윤년과 `plusYears` |
| [15](../advanced/15-period-close/1-question.md) | 월 마감 | 발생·도착 기준, 마감 시각, 늦은 거래 |
| [19](../advanced/19-leaderboard-recount/1-question.md) | 종료 후 취소 | 기준 시점 스냅샷, 동점 |
| [24](../advanced/24-shift-roster/1-question.md) | 야간 근무 주간 집계 | 주 첫날, 야간 귀속, 연속 일수 |
| [30](../advanced/30-b2b-tier/1-question.md) | 거래처 등급 | 연·롤링 창, 하락 규칙, 집계 시점 |

**3단계 — 잡아두기와 배정**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [11](../advanced/11-stock-reservation/1-question.md) | 결제 전 10분 홀드 | 가용 재고 정의, 만료 반영 시점, 만료 정각 |
| [12](../advanced/12-seat-hold/1-question.md) | 일행 좌석 홀드 | 연석 찾기, 단편화, 부분 홀드 금지 |
| [22](../advanced/22-parcel-split/1-question.md) | 상자 나누기 | 두 축 상한, 넘는 물건, 담는 순서 |
| [23](../advanced/23-warehouse-pick/1-question.md) | 여러 창고 출고 | 창고 선택, 걸침, 주문 처리 순서 |
| [26](../advanced/26-photocard-set/1-question.md) | 랜덤 굿즈 세트 보장 | 보장 방식·중복·나머지 |

**4단계 — 재생·재시도·대사**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [14](../advanced/14-mileage-expiry/1-question.md) | 마일리지 소멸 | 적립분 목록, 사건 재생, 취소 시 되돌릴 곳 |
| [16](../advanced/16-audit-replay/1-question.md) | 감사 로그 재생 | 줄 세우기 기준, 중복 규칙, REVERSE |
| [17](../advanced/17-batch-retry/1-question.md) | 배치 중간 실패 | 재시도 범위, UNKNOWN 처리, 회차 소진 |
| [18](../advanced/18-settlement-match/1-question.md) | 입금 내역 맞추기 | 참조값 우선, 날짜 창, 부호 있는 차이 |

**5단계 — 흐름·권한·한도**

| 편 | 요지 | 연습 포인트 |
|---|---|---|
| [20](../advanced/20-approval-chain/1-question.md) | 결재선 | 순서·정족수·금액 변경, 버린 클릭 |
| [21](../advanced/21-throttle/1-question.md) | 초당 요청 한도 | 창 자르기, 세는 키, 막힌 요청도 세나 |
| [25](../advanced/25-lottery-draw/1-question.md) | 가중 추첨 | 1인의 키, 비복원 추출, 시드 고정 |
| [27](../advanced/27-ab-assign/1-question.md) | A/B 배정 | 해시 키·씨앗, 비율 인상 시 이동 수 |
| [28](../advanced/28-authorization/1-question.md) | 권한 규칙 충돌 | 구체성·우선 효과, 기본값, 상속 |
| [29](../advanced/29-customs-clearance/1-question.md) | 면세 한도 | 판정 금액, 묶음, 과세 범위 |

### 3. 기초와 다른 점 — 읽을 때 주의

- 기초는 "한 축의 두 해석"을 비교했다. 심화는 **조합**을 비교한다. 한 축만 바꿔 보는 것으로는 조합의 상호작용(예: 17의 STOP + FAILED_ONLY, SKIP + WHOLE_BATCH)을 못 본다.
- 여러 편이 결론을 "고를 수 있는 것은 어느 방향으로 틀릴 것인가뿐"(17)처럼 맺는다. 정답 조합이 없는 문제도 있다는 것을 받아들인다.

## 장애 시나리오와 대처

연습에서 자주 틀리는 모델링 실수다.

### 1. 덮어쓴다 — 과거의 답이 스스로 바뀐다

- 현상: 정책 값을 바꾸자 지난달 주문의 재계산 금액이 달라진다. 소급 정정 뒤 과거 영수증이 바뀐다.
- 보이는 형태: 같은 주문을 다시 계산하면 다른 숫자(09·10). 이미 발표한 순위가 말없이 바뀐다(19).
- 원인: 판·기록을 수정 가능한 값 하나로 들었다. 기준 시점을 정하지 않았다.
- 대처: 시행일 붙은 판·기록 시각을 붙인 줄로 **쌓는다**. 결과에 적용한 판·기준 시점을 남긴다. → [23](../23-versioned-rules-and-effective-dating/2-summary.md) · [22](../22-decision-log-and-provenance/2-summary.md)

### 2. 결과를 모르는 호출을 한쪽으로 뭉갠다

- 현상: 안 돌린 건이 성공으로 보고되거나, 이미 된 건이 두 번 반영된다.
- 보이는 형태: 배치 총액이 어긋나는데 실패 건수는 0(17).
- 원인: 응답 없음(UNKNOWN)을 성공 또는 실패 중 하나로 처리했다.
- 대처: 결과를 세 갈래로 두고, 모름은 멱등 키 재시도나 대사로 확정한다. → [25](../25-reconciliation/2-summary.md)

### 3. 총액이 맞으면 짝도 맞다고 믿는다

- 현상: 대사표가 매일 깨끗한데 개별 주문의 입금이 엉뚱한 주문에 붙어 있다.
- 보이는 형태: 미대사 0건. 감사에서 짝 오류(18 측정: 금액 매칭이 6,000줄 중 2,893줄을 엉뚱하게 붙였다).
- 원인: 참조값 없이 금액으로 짝을 찾았다.
- 대처: 참조값을 키로 먼저 쓰고, 금액은 비교 값으로만. → [25](../25-reconciliation/2-summary.md)

### 4. 개발 자료로만 검증한다 — 규칙이 배포 뒤에 처음 돈다

- 현상: 유예·늦은 거래·취소 규칙이 운영에서 처음 실행된다.
- 보이는 형태: 개발 환경(지연 0%, 취소 없음, 같은 소멸 기간)에서 규칙 갈래가 통째로 안 돌거나 조합이 전부 같은 답을 낸다(13 유예 0일, 14 소멸 기간이 모두 같은 자료, 15 지연 없는 자료, 16 지연 0%, 20 순서대로 + 금액 안 고침).
- 원인: 갈림을 만드는 입력이 테스트 자료에 없었다.
- 대처: 측정용 자료에 지연·취소·경계 시각을 분포로 넣는다. "조합이 전부 같은 답"이면 자료부터 의심한다.

### 5. 1년·한 달을 날 수로 더한다

- 현상: 계약 갱신일이 윤년마다 하루씩 밀린다. 월말을 하드코딩한 마감이 2월(28/29일)·30일인 달에서 어긋난다.
- 보이는 형태: 특정 연도·달에서만 하루 차이(13·15).
- 원인: `plusDays(365)`, 월말 상수.
- 대처: 달력 산술(`plusYears`·`plusMonths`·`YearMonth.atEndOfMonth`)을 쓴다. → [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md)

## 핵심 문장

- 심화 30편은 **결정 축 셋을 enum으로 꺼내 조합을 측정한다** — 한 축씩 바꿔서는 조합의 상호작용이 안 보인다.
- 시간이 지나면 규칙·데이터·결과가 바뀐다 — 덮어쓰지 말고 판·기록 시각·기준 시점을 붙여 쌓아야 "그때의 답"을 다시 낼 수 있다.
- 결과를 모르는 호출이 있으면 맞는 조합이 없을 수도 있다 — 그때 고를 것은 어느 방향으로 틀릴지와, 나중에 확정할 경로다.
- 개발 자료에서 모든 조합이 같은 답이면 규칙이 아니라 자료를 의심한다.

## 관련 주제·근거

### 선행·후속

- 선행: [21-cqrs](../21-cqrs/2-summary.md) · [15-basic-modeling-exercises](../15-basic-modeling-exercises/2-summary.md) — 커리큘럼상 이 트랙의 선행
- 개념 leaf(위 문제 → 개념 표에서 편별로 연결): [03](../03-ubiquitous-language/2-summary.md) · [04](../04-entities-and-value-objects/2-summary.md) · [05](../05-aggregates-and-invariants/2-summary.md) · [06](../06-anemic-vs-rich-model/2-summary.md) · [08](../08-domain-services-and-policies/2-summary.md) · [09](../09-domain-events/2-summary.md) · [11](../11-state-machines-in-domain/2-summary.md) · [12](../12-time-money-and-units/2-summary.md) · [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [14](../14-money-arithmetic-rounding-allocation/2-summary.md)
- 추적성 단원(13.3b)과 가장 가까운 편: 08·16·19·25 → [22](../22-decision-log-and-provenance/2-summary.md) · 09·10·30 → [23](../23-versioned-rules-and-effective-dating/2-summary.md) · 14·16 → [24](../24-double-entry-ledger/2-summary.md) · 15·17·18 → [25](../25-reconciliation/2-summary.md)
- 다른 영역: [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)(21) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)(16·17) · [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md)(10) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)(14·16·20) · [api-design/06-refund](../../api-design/06-refund/2-summary.md)(04)
- 후속: [27-dm-symptom-index](../27-dm-symptom-index/2-summary.md) · 컬렉션 [advanced/](../advanced/) · [advanced/index.md](../advanced/index.md) · 영역 표 [curriculum.md](../curriculum.md)

### 근거

- 각 편의 1-question·2-summary·3-answer(컬렉션 안내: [advanced/README.md](../advanced/README.md))
- 커리큘럼 §13.4 연습 트랙 행(`docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`)
- 이 노트는 트랙 안내라 별도 실험을 두지 않았다. 측정 수치는 각 편 노트에 실린 값을 편 번호와 함께 옮겼다.
