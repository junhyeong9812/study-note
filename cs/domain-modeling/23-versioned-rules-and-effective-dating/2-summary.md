# domain-modeling/23-versioned-rules-and-effective-dating — 규칙의 판과 유효 일자: 적용 기준 시각·버전 스탬프·미래 발효 — 정리 (힌트)

## 해결하는 문제

요율표·세율·정책·가격표는 바뀐다. 바뀔 때 **덮어쓰면**, 과거에 계산한 결과를 다시 설명할 수 없다.

```text
  덮어쓰기                                  판(version)으로 쌓기
  fee_rate: card = 0.0300                   v1 0.0300 [1/1, 7/1)
     7/1 UPDATE → 0.0350                    v2 0.0350 [7/1, 11/1)
                                            v3 0.0400 [11/1, ∞)   ← 미래 발효 예약
  3월 주문을 지금 다시 계산하면              3월 주문 → v1 → 계산 당시와 같다
  → 0.0350 으로 계산됨 (당시는 0.0300)       결과 행에 (card, v1) 스탬프
```

- 판을 쌓아도 질문이 둘 더 남는다.
  - **적용 기준 시각**: 6/30 23:59 주문, 7/1 00:00 결제. 주문 시각인가 결제 시각인가?
  - **발효 시각**: "11/1부터"는 배포 시각인가, 데이터에 적힌 시각인가?
  - *유효 일자(effective dating)*: 데이터에 "이 값이 언제부터 언제까지 유효한가"를 붙이는 것. Fowler는 이 생각을 **Effectivity**("Add a time period to an object to show when it is effective")와 **Temporal Property**로 정리했다(martinfowler.com eaaDev, 2004-03-07, 저자가 초안이라고 밝힌 글).

쉬운 예: 버스 요금이 7월 1일에 올랐다.
- 6월에 낸 영수증을 7월에 다시 뽑으면 6월 요금이 찍혀야 한다.
- 6월 30일 밤 11시 59분에 탄 사람이 자정을 넘겨 내리면 어느 요금인지 정해 둬야 한다.

똑같은 구조다.\
규칙은 **판 + 유효 구간**으로 쌓고, 계산은 **정해진 기준 시각**으로 판을 고르며, 결과 행에는 **고른 판**을 찍는다.

실무 예: 카드 수수료율 개정, 부가세율 변경, 배송비 정책, 포인트 적립률, 환불 규정, 보험 요율표.

- 기초(정책 판 고르기·기준 날짜 3택·처리 시점의 위험)는 연습 문제 [advanced/09-policy-version](../advanced/09-policy-version/2-summary.md) 규칙 ①②에 있다. 정정 이력(두 시간축)은 [advanced/10-price-history](../advanced/10-price-history/2-summary.md)와 [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md)에 있다. 이 노트는 **저장 구조(DB 제약)·버전 스탬프·미래 발효·배포와 발효의 분리**를 채운다.

## 동작·원리

### 1. 판과 유효 구간 — 반열린 구간 `[from, to)`

```text
  시간 ─────────────────────────────────────────────────────────▶
        1/1            7/1                 11/1
        ├──── v1 3.00% ──┤├──── v2 3.50% ────┤├──── v3 4.00% ─────▶
        [               )[                  )[
                         ^ 7/1 00:00:00 은 v2 에만 속한다
```

- *반열린 구간 `[from, to)`*: 시작은 포함, 끝은 제외. 맞닿은 두 판이 경계 시각을 나눠 갖지 않는다.
- 불변식 두 개
  - **겹침 없음**: 같은 규칙에서 어떤 시각에 유효한 판은 많아야 하나다.
  - **빈틈 없음**(필요한 구간 안에서): 계산해야 하는 시각에 유효한 판이 적어도 하나 있다. 첫 판 이전 시각은 "판 없음"을 어떻게 다룰지 정한다(adv/09의 `MissingPolicy`).
- 판 행은 **고치지 않는다**. 요율을 잘못 넣었으면 새 판으로 정정하고, 정정 이력이 필요하면 기록 시간축을 둔다(db/50 바이템포럴).

### 2. 적용 기준 시각 — 어느 시각으로 판을 고르나

```text
  주문 1001   ordered_at 6/30 23:59:30   paid_at 7/1 00:00:30
                   │                        │
                   ▼                        ▼
                  v1 (3.00% → 3,000원)      v2 (3.50% → 3,500원)
```

| 기준 시각 후보(예시) | 장점 | 위험 |
|---|---|---|
| 주문(계약) 시각 | 고객이 본 조건과 같다 | 주문 후 오래 지나 결제되면 옛 판이 오래 쓰인다 |
| 결제(승인) 시각 | 돈이 움직인 시점과 같다 | 경계 근처 주문의 금액이 결제 지연에 따라 달라진다 |
| 처리(정산) 시각 | 구하기 쉽다 | 처리가 늦을수록 결과가 바뀐다 — adv/09 규칙 ②가 측정 |

- 어느 쪽이 맞는지는 약관·법·계약이 정한다. 코드가 할 일은 기준 시각을 **이름으로 드러내고**(`Anchor.ORDERED`), 그 시각을 결과 행에 함께 남기는 것이다.
- 기준 시각도 순간이다. "11/1 00:00부터"는 **어느 지역의 자정**인지 정해야 한다(아래 실험은 모두 `+09`). 시간대 문제는 [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md).

### 3. 결과 행에 버전 스탬프

```text
  orders
  ┌──────┬─────────────────────┬────────┬─────┬─────────┬──────────────┐
  │ id   │ ordered_at          │ amount │ fee │ rule_id │ rule_version │
  ├──────┼─────────────────────┼────────┼─────┼─────────┼──────────────┤
  │ 1001 │ 2026-06-30 23:59:30 │ 100000 │3000 │ card    │ 1            │ ──FK──▶ fee_rule_version
  └──────┴─────────────────────┴────────┴─────┴─────────┴──────────────┘
```

- 스탬프가 있으면 재계산은 "그 판으로 다시 계산해 같은가"라는 단순 비교가 된다. 기준 시각으로 판을 다시 찾을 필요도 없다.
- 결정 하나를 재현하는 데 필요한 것(입력 스냅숏·규칙 ID와 판·중간 산출·결정 시각)을 한 레코드로 남기는 일반형은 [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md)가 다룬다.

### 4. 미래 발효 예약 — 공표 시각 ≠ 발효 시각 ≠ 배포 시각

```text
  10/3 10:00          10/15 배포        11/1 00:00         11/1 03:00
  v3 공표(데이터 입력)   (코드 변경 없음)  v3 발효(데이터)    ← 코드 상수 방식이면 여기서야 바뀐다
  published_at                           lower(effective)    배포 지연 3시간 = 구 요율 3시간
```

- 데이터 방식: 판을 미리 넣어 두면, 같은 조회 쿼리가 조회 시각만 달라져 새 판을 고른다. 배포와 무관하다.
- 코드 상수 방식: `RATE = 0.035`를 바꿔 배포한다. "배포 시각 = 발효 시각"을 가정하게 되고, 배포가 늦으면 그 사이 주문이 구 요율로 계산된다.
- 반대 상황도 있다. 규칙이 **계산 로직 자체**(새 공식, 새 입력 필드)라면 데이터만으로 바꿀 수 없다. 그때는 새 로직을 미리 배포하고 판 데이터의 발효 시각에 맞춰 켜지게(기능 플래그 + 발효 시각) 한다.

### 실험: PostgreSQL 17로 덮어쓰기 vs 판, 경계, 미래 발효, 배포 지연

스키마(핵심, `scratchpad/dm/12/exp23.sql`):

```sql
CREATE EXTENSION btree_gist;
CREATE TABLE fee_rule_version (
  rule_id text NOT NULL, version int NOT NULL, rate numeric(6,4) NOT NULL,
  effective tstzrange NOT NULL, published_at timestamptz NOT NULL,
  PRIMARY KEY (rule_id, version),
  EXCLUDE USING gist (rule_id WITH =, effective WITH &&)      -- 같은 규칙의 구간 겹침 금지
);
-- v1 [2026-01-01, 2026-07-01) 0.0300 / v2 [2026-07-01, 2026-11-01) 0.0350 / v3 [2026-11-01, ∞) 0.0400 (모두 +09)
CREATE TABLE fee_rate_overwrite (rule_id text PRIMARY KEY, rate numeric(6,4) NOT NULL);  -- 비교용: 덮어쓰기 모델
-- 1~10월 주문 1000건(결정적) + 경계 주문 2건. 주문 시각으로 판을 골라 수수료와 판 번호를 찍는다
UPDATE orders o SET fee = round(o.amount * v.rate), rule_id = v.rule_id, rule_version = v.version
FROM fee_rule_version v WHERE v.rule_id = 'card' AND v.effective @> o.ordered_at;
-- 덮어쓰기 모델의 요율이 7/1에 0.0350 으로 UPDATE 됐다고 하고, 세 방법으로 재계산해 비교
UPDATE fee_rate_overwrite SET rate = 0.0350 WHERE rule_id = 'card';
```

(실험, PostgreSQL 17.11 postgres:17 일회용 컨테이너 `--cpus=2`, 세션 TimeZone Asia/Seoul, 2026-10-03)

```text
--- 겹치는 판 삽입 시도
ERROR:  conflicting key value violates exclusion constraint "fee_rule_version_rule_id_effective_excl"
DETAIL:  Key (rule_id, effective)=(card, ["2026-06-15 00:00:00+09","2026-08-01 00:00:00+09")) conflicts with existing key (rule_id, effective)=(card, ["2026-01-01 00:00:00+09","2026-07-01 00:00:00+09")).
--- 판별 주문 수
 rule_version | count 
--------------+-------
            1 |   599
            2 |   403

--- 재계산 비교: 덮어쓴 요율 vs 주문 시각의 판 vs 찍어 둔 판 번호
 overwrite_mismatch | overwrite_diff_won | by_ordered_at_mismatch | by_stamp_mismatch 
--------------------+--------------------+------------------------+-------------------
                599 |             155998 |                      0 |                 0

--- 적용 기준 시각: 주문 시각 vs 결제 시각이 다른 판을 고르는 주문
  id  |       ordered_at       |        paid_at         | by_ordered | by_paid | fee_ordered | fee_paid 
------+------------------------+------------------------+------------+---------+-------------+----------
 1001 | 2026-06-30 23:59:30+09 | 2026-07-01 00:00:30+09 |          1 |       2 |        3000 |     3500

--- 반열린 구간 경계: 정확히 7/1 00:00 과 그 1마이크로초 전
               t               | matching 
-------------------------------+----------
 2026-06-30 23:59:59.999999+09 | {1}
 2026-07-01 00:00:00+09        | {2}

--- 미래 발효: 같은 쿼리, 조회 시각만 다름
           t            | version |  rate  
------------------------+---------+--------
 2026-10-31 23:59:59+09 |       2 | 0.0350
 2026-11-01 00:00:00+09 |       3 | 0.0400

--- 배포 시각 = 발효 시각 가정: 코드 상수가 11/1 03:00 배포로 바뀌었다면 (11/1 00:00~05:59 주문 72건)
 mismatched_orders | undercharged_won 
-------------------+------------------
                36 |             9226
```

관찰과 해석:
- 겹치는 판(6/15~8/1)은 `EXCLUDE` 제약이 거절했다. 겹침 없음 불변식을 DB가 지킨다. 제약 문법·`tstzrange` 기본 `[)` 동작은 [database/50](../../database/50-temporal-and-bitemporal-tables/2-summary.md) §3·§5.
- 덮어쓰기 모델로 재계산하면 v1 시기 주문 **599건 전부**가 달라졌고 합계 155,998원 차이였다. 판 + 주문 시각, 판 스탬프로 재계산하면 0건이었다.
- 경계 주문 1001은 기준 시각에 따라 3,000원 vs 3,500원이다. 정확히 7/1 00:00은 v2에만 속한다(반열린 구간).
- 미래 판 v3는 미리 들어 있었고, 조회 시각이 11/1 00:00이 되자 같은 쿼리가 v3를 골랐다.
- 코드 상수를 03:00에 배포했다고 가정하면, 00:00~02:59 주문 36건이 구 요율로 계산돼 9,226원을 덜 받았다.

빈틈과 "판 없음":

```text
--- 판 사이 빈틈 점검 (빈틈이 있으면 그 구간 주문은 판을 못 찾는다)
 version |                      effective                      | contiguous_with_next 
---------+-----------------------------------------------------+----------------------
       1 | ["2026-01-01 00:00:00+09","2026-07-01 00:00:00+09") | t
       2 | ["2026-07-01 00:00:00+09","2026-11-01 00:00:00+09") | t
       3 | ["2026-11-01 00:00:00+09",)                         | 

--- 판을 못 찾은 주문 (첫 판 이전 주문 1건 추가 후)
  id  |       ordered_at       
------+------------------------
 1003 | 2025-12-31 23:00:00+09
```

- `EXCLUDE`는 겹침만 막는다. 빈틈은 막지 않는다. 빈틈은 `lead()`로 이웃 판과 맞닿는지 점검하고, 판을 못 찾는 주문은 `LEFT JOIN … IS NULL`로 찾는다. 내부 조인으로 계산하면 이런 주문은 **조용히 빠진다**.

## 쓰이는 자료구조·알고리즘

- **구간 탐색 = "시각 ≤ t 인 시작 중 가장 늦은 것"**: 판이 시작 시각 순으로 정렬돼 있으면 이진 탐색(upper bound − 1)이다. Java `TreeMap.floorEntry(t)`가 이것이다. → [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)

(실험, JDK 21.0.12 temurin — 시작 시각을 키로 둔 `TreeMap`)

```text
== 23. TreeMap.floorEntry 로 판 고르기
  2025-12-31T14:59:59Z -> 판 없음(null)
  2026-06-30T14:59:59.999999Z -> v1 3.00%
  2026-06-30T15:00:00Z -> v2 3.50%
  2026-10-31T15:00:00Z -> v3 4.00%
```

  - `floorEntry`는 끝 시각을 보지 않는다. 빈틈이 있을 수 있으면 고른 판의 끝(`to`)도 확인해야 한다.
- **GiST 인덱스 + 범위 연산자**: PostgreSQL은 `effective @> t`를 제외 제약이 만든 GiST 인덱스로 찾는다. 판 1만 개로 늘린 뒤의 계획:

```text
 Index Scan using fee_rule_version_rule_id_effective_excl on fee_rule_version
   Index Cond: ((rule_id = 'r42'::text) AND (effective @> '2020-02-15 12:00:00+09'::timestamp with time zone))
```

- **구간 트리**: 메모리에서 "t를 포함하는 구간"·"겹치는 구간"을 찾는 자료구조. → [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)
- **이웃 비교(윈도 함수 `lead`)**: 정렬된 구간에서 `upper(현재) = lower(다음)`이면 맞닿음, `<`면 빈틈, `>`면 겹침.

## 적용 — 풀어나가는 법

### 1. 쉬운 예 — 메모리 안의 판 목록

```java
public record RuleVersion(String ruleId, int version, BigDecimal rate, Instant from, Instant to /* null = 무기한 */) {
  boolean contains(Instant t) { return !t.isBefore(from) && (to == null || t.isBefore(to)); }   // [from, to)
}

public final class FeeSchedule {
  private final NavigableMap<Instant, RuleVersion> byStart = new TreeMap<>();
  public FeeSchedule(List<RuleVersion> versions) {
    for (RuleVersion v : versions) {
      Map.Entry<Instant, RuleVersion> prev = byStart.floorEntry(v.from());
      if (prev != null && prev.getValue().contains(v.from())) throw new IllegalArgumentException("겹치는 판: " + v);
      byStart.put(v.from(), v);
    }
    // 단순화: 뒤에 오는 판과의 겹침 검사는 생략했다 — 판을 시작 순으로 넣는다는 전제. 순서가 무작위면 정렬 후 이웃 비교로 바꾼다.
  }
  /** 기준 시각 t 에 유효한 판. 없으면 예외 — 조용히 0 이나 최신 판을 쓰지 않는다. */
  public RuleVersion at(Instant t) {
    Map.Entry<Instant, RuleVersion> e = byStart.floorEntry(t);
    if (e == null || !e.getValue().contains(t)) throw new IllegalStateException("판 없음: " + t);
    return e.getValue();
  }
}

// 계산은 기준 시각을 이름으로 받고, 결과에 판을 찍는다
enum Anchor { ORDERED, PAID, PROCESSED }   // 기준 시각의 이름 (adv/09 규칙 ②)
public record FeeResult(long fee, String ruleId, int ruleVersion, Instant anchorTime, Anchor anchor) {}
```

### 2. 실무 예 — 순서

1. 규칙마다 **판 테이블**을 만든다: `(rule_id, version)` 기본 키, `effective tstzrange`, `published_at`, `EXCLUDE (rule_id WITH =, effective WITH &&)`.
2. 판 행은 INSERT만 한다. UPDATE·DELETE를 막는다(권한 회수 또는 트리거). 정정은 새 판 + 이유 기록.
3. 계산 지점마다 **기준 시각**을 정해 이름 붙인다(주문·결제·출고 등). 약관 문구와 같은 말을 쓴다.
4. 결과 행에 `rule_id`·`rule_version`(FK)과 기준 시각을 함께 저장한다.
5. 발효는 데이터로 예약한다. 계산 로직이 바뀌는 경우만 미리 배포 + 발효 시각에 켜지는 분기.
6. 운영 점검(배치·알람)
   - 빈틈: 이웃 판이 맞닿는지(`lead`).
   - 판 없음: 계산 대상 중 판을 못 찾는 행(`LEFT JOIN … IS NULL`).
   - 재현성: 스탬프된 판으로 다시 계산해 저장값과 다른 행(실험의 `by_stamp_mismatch`, 0이어야 한다).

```sql
-- 재현성 점검: 0 행이어야 한다
SELECT o.id, o.fee, round(o.amount * v.rate) AS recalculated
FROM orders o JOIN fee_rule_version v ON (v.rule_id, v.version) = (o.rule_id, o.rule_version)
WHERE round(o.amount * v.rate) <> o.fee;
```

- PostgreSQL 18은 `PRIMARY KEY (rule_id, effective WITHOUT OVERLAPS)`로 같은 제약을 선언할 수 있다(18 릴리스 노트, db/50 §4). 17에서는 위의 `EXCLUDE`를 쓴다.

## 장애 시나리오와 대처

### 1. 요율표를 덮어썼다 → 과거 주문 재계산 금액이 다르다 (⚠)
- 현상: 환불·분쟁 대응으로 과거 주문을 다시 계산하면 당시 청구액과 다르다.
- 보이는 형태: 에러 없음. 실험에서 v1 시기 599건 전부, 합 155,998원 차이.
- 원인: 요율이 한 칸이라 "그때의 요율"이 남아 있지 않다.
- 대처: 판 테이블로 옮기고 결과 행에 판을 찍는다. 이미 덮어쓴 이력은 변경 로그·배포 기록·감사 로그로 판을 복원하고, 복원 못 한 구간은 "당시 저장된 금액을 정본으로" 둔다.

### 2. 적용 기준 시각이 불명확 → 경계 시각 주문에서 분쟁 (⚠)
- 현상: 개정 직전 주문·직후 결제 건에서 고객이 구 요율을 주장한다. 서비스마다 다른 판을 고른다.
- 보이는 형태: 실험 주문 1001 — 주문 시각 기준 3,000원, 결제 시각 기준 3,500원. 주문 화면과 영수증 금액이 다르다.
- 원인: 기준 시각이 코드 곳곳에서 "구하기 쉬운 시각"으로 암묵적으로 정해졌다.
- 대처: 약관에 기준 시각을 적고, 코드에 `Anchor`로 드러내고, 결과 행에 기준 시각과 판을 남긴다. 경계 테스트는 `[from, to)`의 `from` 정각과 1단위 전.

### 3. "배포 시각 = 발효 시각"으로 가정 → 배포가 늦어 구 요율로 결제 (⚠)
- 현상: 개정 첫날 새벽 주문 일부가 구 요율이다.
- 보이는 형태: 실험 — 03:00 배포 가정에서 36건, 9,226원 덜 청구. 배포 로그 시각과 요율 전환 시각이 일치한다.
- 원인: 요율이 코드 상수다. 발효를 배포로 표현했다.
- 대처: 요율을 판 데이터로 미리 넣고 발효 시각을 데이터에 둔다. 이미 생긴 차이는 판 스탬프가 없으면 주문 시각으로 영향 범위를 특정해 조정한다(조정은 불가역 데이터 변경이라 사용자 고지·승인 절차를 거친다).

### 4. 판 사이 빈틈 → 계산에서 주문이 조용히 빠진다
- 현상: 특정 기간 주문의 수수료가 정산에 없다. 또는 기본값 0이 들어갔다.
- 보이는 형태: 실험 — 첫 판 이전 주문 1003이 `LEFT JOIN … IS NULL`로만 보인다. 내부 조인 집계에는 아예 안 나타난다.
- 원인: 새 판의 시작을 이전 판 끝과 맞추지 않았다(예: 끝을 `6/30 23:59:59`로 넣음). `EXCLUDE`는 빈틈을 막지 않는다.
- 대처: 구간은 반열린으로 넣고, 빈틈 점검 쿼리를 배치·배포 검증에 넣는다. 판을 못 찾으면 예외를 낸다(`FeeSchedule.at`).

### 5. 판 행을 UPDATE로 고쳤다 → 스탬프의 뜻이 바뀐다
- 현상: 스탬프 기준 재현성 점검이 갑자기 수백 건 불일치를 낸다.
- 보이는 형태: `by_stamp_mismatch`가 0이 아니다. 판 테이블의 `rate`가 최근에 바뀌었다.
- 원인: "같은 판 번호 = 같은 규칙"이라는 전제를 UPDATE가 깼다.
- 대처: 판 행 변경 권한을 막는다. 잘못 넣은 판은 새 판으로 정정하고, 그 판이 이미 쓰였다면 영향 받은 결과의 처리(재계산·유지)를 따로 결정한다.

## 핵심 문장

- 요율·세율·가격표는 덮어쓰지 않고 판 + 유효 구간 `[from, to)`로 쌓는다. 판 행은 고치지 않는다.
- 판을 고르는 기준 시각(주문·결제·처리)은 약관이 정하고, 코드는 그것을 이름으로 드러낸다.
- 결과 행에 규칙 ID와 판을 찍으면, 재계산은 "그 판으로 다시 계산해 같은가"라는 비교가 된다.
- 발효는 배포가 아니라 데이터로 예약한다. 같은 조회가 조회 시각만으로 새 판을 고른다.
- PostgreSQL 17 `EXCLUDE … WITH &&`는 겹침을 막지만 빈틈은 막지 않는다. 빈틈과 "판 없음"은 따로 점검한다.

## 관련 주제·근거

- 선행
  - [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) — 결정 기록
  - [12-time-money-and-units](../12-time-money-and-units/2-summary.md) — 개관
- 연결
  - [advanced/09-policy-version](../advanced/09-policy-version/2-summary.md) — 판 고르기·기준 날짜 3택·첫 판 이전 정책(연습)
  - [advanced/10-price-history](../advanced/10-price-history/2-summary.md) — 유효일과 기록일 두 시간축(연습)
  - [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md) — SQL:2011, `EXCLUDE`, PG 18 `WITHOUT OVERLAPS`, 바이템포럴
  - [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md) — 발효 자정은 어느 시간대인가
  - [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md) — 요율 곱셈의 반올림
  - [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) · [25-reconciliation](../25-reconciliation/2-summary.md) — 판이 바뀐 뒤의 정정·대사
  - [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md) · [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)
- 근거
  - Fowler, "Effectivity"(2004-03-07) <https://martinfowler.com/eaaDev/Effectivity.html> · "Temporal Property"(2004-03-07) <https://martinfowler.com/eaaDev/TemporalProperty.html> — 날짜 인자로 값 조회, 과거(소급)·현재·미래(예약) 변경, 바이템포럴. 둘 다 저자가 초안이라고 밝힌 글이다.
  - PostgreSQL 17 문서 — 8.17 Range Types(`tstzrange`, `@>`, `&&`), CREATE TABLE `EXCLUDE`, F.8 btree_gist <https://www.postgresql.org/docs/17/rangetypes.html>
  - Java SE 21 API — `java.util.TreeMap.floorEntry`
- 실험 목록
  - `exp23.sql` — PostgreSQL 17.11(postgres:17 일회용 컨테이너 `sn-dm-w12-pg`, `--cpus=2`, 포트 미개방): 겹침 거절, 덮어쓰기 vs 판 vs 스탬프 재계산(1,002건), 기준 시각 경계, 반열린 경계, 미래 발효, 배포 지연(72건), 빈틈·판 없음, GiST 계획(판 1만 개)
  - `Extra.java` — JDK 21.0.12: `TreeMap.floorEntry` 판 고르기
