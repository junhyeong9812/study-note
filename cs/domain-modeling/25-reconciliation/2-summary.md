# domain-modeling/25-reconciliation — 대사: 두 장부를 키로 맞추고 차이를 분류해 처리한다 — 정리 (힌트)

## 해결하는 문제

결제 한 건은 우리 원장과 PG(결제대행사) 장부 **두 곳**에 따로 적힌다. 두 장부가 같은 이야기를 하는지 맞춰보지 않으면, 어긋난 줄은 고객 민원으로 처음 드러난다.

```text
  우리 원장                       PG 장부
  O101  ? (타임아웃 — 결과 모름)    T101  O101  5,171  APPROVED   ← 돈은 빠졌는데 주문이 없다
  O202  PAID  4,519               (없음)                         ← 우리는 받았다고 믿는다
  O303  PAID  2,651               T303 / T303-dup  두 번 승인    ← 고객 이중 청구
  O404  PAID  2,405               T404  2,404                   ← 1원 차이
  ...                             ...
            총액만 비교: 5,581,182 vs 5,598,055 — "다르다"는 알지만 어느 줄인지는 모른다
```

- 타임아웃은 "실패"가 아니라 "모름"이다([distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md)). 모름 상태의 요청을 **최종 확정하는 경로**가 대사다.
  - *대사(reconciliation)*: 같은 사건을 따로 기록한 두 장부를 키로 맞춰 보고, 차이를 찾아 분류·처리하는 일.

쉬운 예: 카드 명세서와 가계부를 맞춰 보는 일이다.
- 명세서에는 있는데 가계부에 없는 줄(적는 걸 잊었다), 가계부에는 있는데 명세서에 없는 줄(결제가 안 됐다), 금액이 다른 줄(팁을 더 냈다), 두 번 찍힌 줄(이중 결제)을 찾는다.
- 합계만 맞춰 보면 서로 상쇄된 차이는 안 보인다.

똑같은 구조다: 두 집합을 **같은 키**로 맞추고, 짝이 없거나 값이 다른 줄을 **종류별로** 나눈다.

실무 예:
- PG 거래 파일 vs 주문·결제 원장(일 단위).
- 은행 입금 내역 vs 판매자 지급 원장 — 파트너가 보낸 입금 줄을 우리 판매 기록에 붙인다([advanced/18-settlement-match](../advanced/18-settlement-match/2-summary.md)).
- Stripe는 "Payout reconciliation" 보고서로 은행에 들어온 지급 한 건을 그 지급에 묶인 거래 묶음과 맞추게 한다(Stripe Docs — 자동 지급(automatic payouts)을 켠 계정용이고, 수동 지급이면 Balance 보고서를 쓰라고 안내한다).

## 동작·원리

### 1. 흐름 — 적재 → 키 맞추기 → 분류 → 사건으로 남기기 → 처리

```text
  외부 파일(원본 그대로 적재) ─┐
                              ├─► 키로 맞추기 ─► 분류 ─► recon_break(사건) ─► 자동 확정(좁게)
  내부 원장(같은 기간·같은 기준)┘   (FULL OUTER       │                      └► 사람 검토 → 조정 분개
                                    JOIN)            └─► MATCHED (끝)
```

- **원본 그대로 적재**: 외부 파일을 고치지 않고 줄 번호와 함께 넣는다. 나중에 "PG가 그때 뭐라고 보냈나"를 다시 볼 수 있어야 한다.
- **키**: 양쪽이 공유하는 식별자. 보통 우리가 PG에 보낸 주문 ID와 PG가 돌려준 거래 ID(`pg_tx_id`).
  - *대사 키*: 두 장부의 줄을 짝짓는 열. 금액·시각은 키가 아니라 **비교할 값**이다.
- **같은 기간·같은 기준**: 양쪽을 같은 시간대·같은 경계로 자른다(§4).
- **사건으로 남기기**: 차이를 바로 고치지 않고 먼저 기록한다(§3).

### 2. 분류 — 차이는 종류마다 원인과 처리가 다르다

```text
  내부 \ 외부        없음                 1건                       2건 이상
  없음              —                    MISSING_INTERNAL          MISSING_INTERNAL
  있음(UNKNOWN)     MISSING_EXTERNAL*    RESOLVE_UNKNOWN           DUPLICATE_EXTERNAL
  있음(PAID)        MISSING_EXTERNAL     금액 다름 → AMOUNT_MISMATCH  DUPLICATE_EXTERNAL
                                         상태 다름 → STATUS_MISMATCH
                                         같음 → MATCHED
```

| 분류 | 흔한 원인 | 처리 |
|---|---|---|
| MISSING_INTERNAL | 승인 후 콜백·응답 유실, 우리 쪽 저장 실패 | 주문 생성 또는 PG 취소(환불) — 업무 결정 |
| MISSING_EXTERNAL | PG 승인 실패를 성공으로 처리, 파일 지연 | 다음 파일까지 보류 → 계속 없으면 내부 취소 |
| RESOLVE_UNKNOWN | 타임아웃으로 결과를 몰랐다 | 외부 승인·금액이 같으면 내부 확정 |
| DUPLICATE_EXTERNAL | 재시도에 멱등키 없음 | 중복분 PG 취소 + 고객 안내 |
| AMOUNT_MISMATCH | 반올림·할인 배분 차이, 부분 취소 미반영 | 원인 확인 후 조정 분개 |
| STATUS_MISMATCH | 우리 쪽 취소가 PG에 안 감 | PG 취소 재시도 또는 내부 상태 정정 |

- `*` 실험 쿼리는 외부가 없으면 내부 상태와 무관하게 MISSING_EXTERNAL로 둔다. 내부가 UNKNOWN이면 "PG 미승인(실패 후보)"이라는 뜻이라, 처리는 다음 파일까지 보류 → 내부 FAILED 확정이다.
- 분류 판정에는 **순서**가 있다. 중복은 금액 비교보다 먼저 본다. 중복된 주문의 외부 금액 합(5,302)은 내부 금액(2,651)과 다르지만, 원인은 금액이 아니라 중복이다(실험 O303).

### 3. 차이는 고치기 전에 사건으로 — 자동 처리는 좁게

```text
  분류 결과 ──► recon_break(run_date, order_id, result, int_amt, ext_amt, ext_tx, state, resolution)
                 state: OPEN ──(자동 규칙 or 사람)──► RESOLVED (+ 근거 문장)
```

- 차이를 발견 즉시 내부 값을 외부에 맞춰 덮어쓰면, 왜 달랐는지(우리 버그인지 PG 오류인지)가 사라진다. 같은 원인이 매일 반복돼도 아무도 모른다.
- 자동 확정은 **결과를 모르던 요청(UNKNOWN)** 처럼 원인이 정해진 분류에만 둔다. 나머지는 사람이 원인을 보고 조정 분개를 넣는다.
  - *조정 분개(adjusting entry)*: 차이를 메우려고 새로 넣는 전표. 원 전표를 고치지 않는다([24-double-entry-ledger](../24-double-entry-ledger/2-summary.md)의 역분개·재분개).

### 4. 날짜 경계 — 시간대가 다르면 매일 가짜 차이

```text
  UTC  10-01 15:00 ─────────────── 10-02 00:00 ─────────────── 10-02 15:00 ─── 10-03 00:00
  KST  10-02 00:00 ─────────────── 10-02 09:00 ─────────────── 10-03 00:00
       |<──────────── 내부 배치: KST 10-02 하루 ────────────>|
                                   |<──────────── 외부 파일: UTC 10-02 하루 ───────────>|
       |<── 9시간: 내부에만 있음 ──>|                            |<── 외부에만 있음 ──>|
```

- 내부는 KST 날짜로, 외부 파일은 UTC 날짜로 자르면 9시간치가 매일 한쪽에만 있다. 다음 날 반대쪽에서 다시 나타나 "저절로 풀리는" 가짜 차이가 된다.
- Stripe 보고서의 날짜 열은 요청한 시간대로, 지정하지 않으면 UTC로 나온다(payout reconciliation 보고서 열 설명). Dashboard 보고서는 항상 하루 단위다.
- 토스페이먼츠 정산 조회 API(`GET /v1/settlements`)는 `dateType`으로 `soldDate`(매출일)·`paidOutDate`(지급일) 중 기준을 고른다(토스페이먼츠 API 레퍼런스). **어느 날짜 기준인지**도 경계의 일부다.
- 시각 저장·변환 규칙은 [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md), PostgreSQL `timestamptz` 동작은 [database/27](../../database/27-temporal-types-and-session-timezone/2-summary.md).

### 실험: PostgreSQL 17 대사 — EXCEPT, 분류 FULL OUTER JOIN, 총액 비교

정상 결제 1,000건(내부 `payment`, 외부 `pg_settlement`에 같은 내용)을 만들고 사고 7가지를 주입했다.

```sql
UPDATE payment SET pg_tx_id = NULL, status = 'UNKNOWN' WHERE order_id = 'O101';  -- ① 타임아웃
DELETE FROM pg_settlement WHERE order_id = 'O202';                               -- ② 외부 누락
INSERT INTO pg_settlement SELECT 2001, 'T303-dup', order_id, amount, 'APPROVED', approved_at + interval '3 seconds'
  FROM pg_settlement WHERE order_id = 'O303';                                    -- ③ 이중 승인
UPDATE pg_settlement SET amount = amount - 1 WHERE order_id = 'O404';            -- ④ 1원 차이
UPDATE payment SET status = 'CANCELLED' WHERE order_id = 'O505';                 -- ⑤ 상태 불일치
INSERT INTO pg_settlement VALUES (2002, 'TX001', 'X001', 5000, 'APPROVED', timestamptz '2026-10-02 03:00:00+00'); -- ⑥ 내부에 없음
-- ⑦ O606·O607의 외부 금액을 서로 바꿈(합은 그대로)
```

분류 쿼리 — 외부를 **주문 단위로 먼저 접고**(중복 탐지) FULL OUTER JOIN.

```sql
WITH ext AS (
  SELECT order_id, count(*) AS n, sum(amount) AS amount, min(status) AS status,
         string_agg(pg_tx_id, ',' ORDER BY line_no) AS tx
  FROM pg_settlement GROUP BY order_id)
SELECT coalesce(p.order_id, e.order_id) AS order_id, p.status AS internal, e.status AS external,
       p.amount AS int_amt, e.amount AS ext_amt, e.tx,
  CASE WHEN p.order_id IS NULL THEN 'MISSING_INTERNAL'
       WHEN e.order_id IS NULL THEN 'MISSING_EXTERNAL'
       WHEN e.n > 1 THEN 'DUPLICATE_EXTERNAL'
       WHEN p.status = 'UNKNOWN' THEN 'RESOLVE_UNKNOWN'
       WHEN p.amount <> e.amount THEN 'AMOUNT_MISMATCH'
       WHEN (p.status = 'PAID') <> (e.status = 'APPROVED') THEN 'STATUS_MISMATCH'
       ELSE 'MATCHED' END AS result
FROM payment p FULL OUTER JOIN ext e ON e.order_id = p.order_id
WHERE /* MATCHED가 아닌 줄만 */ ...;
```

(실험, PostgreSQL 17.11 일회용 컨테이너, 2026-10-03) — 출력 발췌.

```text
--- (1) EXCEPT: 양쪽에 같은 (주문, 금액)이 없는 줄 — 빠르지만 왜 다른지는 안 알려준다
 order_id | amount            ← 내부 PAID EXCEPT 외부 APPROVED
 O202     |   4519
 O404     |   2405
 O606     |   9499
 O607     |   6558
 order_id | amount            ← 외부 APPROVED EXCEPT 내부 PAID
 O101     |   5171
 O404     |   2404
 O505     |   8571
 O606     |   6558
 O607     |   9499
 X001     |   5000
--- (2) 분류 대사: 주문 단위로 외부를 먼저 접고 FULL OUTER JOIN
 order_id | internal  | external | int_amt | ext_amt |      tx       |       result
----------+-----------+----------+---------+---------+---------------+--------------------
 O101     | UNKNOWN   | APPROVED |    5171 |    5171 | T101          | RESOLVE_UNKNOWN
 O202     | PAID      |          |    4519 |         |               | MISSING_EXTERNAL
 O303     | PAID      | APPROVED |    2651 |    5302 | T303,T303-dup | DUPLICATE_EXTERNAL
 O404     | PAID      | APPROVED |    2405 |    2404 | T404          | AMOUNT_MISMATCH
 O505     | CANCELLED | APPROVED |    8571 |    8571 | T505          | STATUS_MISMATCH
 O606     | PAID      | APPROVED |    9499 |    6558 | T606          | AMOUNT_MISMATCH
 O607     | PAID      | APPROVED |    6558 |    9499 | T607          | AMOUNT_MISMATCH
 X001     |           | APPROVED |         |    5000 | TX001         | MISSING_INTERNAL
--- (3) 분류별 건수(정상 포함)
 AMOUNT_MISMATCH    |     3
 DUPLICATE_EXTERNAL |     1
 MATCHED            |   993
 MISSING_EXTERNAL   |     1
 MISSING_INTERNAL   |     1
 RESOLVE_UNKNOWN    |     1
 STATUS_MISMATCH    |     1
--- (4) 총액만 비교하면
 internal_paid_sum | external_sum
-------------------+--------------
           5581182 |      5598055
--- (5) ⑦만 놓고 보면: 두 줄 합은 같다
 internal | 16057
 external | 16057
```

- 관찰 1: `EXCEPT`는 차이가 **있다**는 것만 알려준다. O303(이중 승인)은 두 결과 어디에도 없다 — `EXCEPT`는 `ALL` 없이 쓰면 중복을 지운다(PostgreSQL 17 문서 7.4). 같은 (주문, 금액) 줄이 외부에 두 번 있어도 하나로 본다. 중복은 키로 접어서(`count(*)`) 따로 봐야 한다.
  - `EXCEPT ALL`로 바꾸면 남는 한 줄이 보인다. 아래 사건 처리 실험 뒤(O101이 PAID로 확정된 상태)에 외부 `EXCEPT ALL` 내부를 돌리자 `O303 | 2651`, `O404 | 2404`, `O505 | 8571`, `O606 | 6558`, `O607 | 9499`, `X001 | 5000` 6줄이 나왔다(PostgreSQL 17.11, 2026-10-03). 그래도 "왜 다른지"는 여전히 분류 쿼리가 알려준다.
- 관찰 2: 분류 쿼리는 주입한 7가지를 모두 찾았고(8줄 — ⑦이 두 줄), 993건이 MATCHED다.
- 관찰 3: 총액 차이 16,873원은 O101 5,171 + O303 중복 2,651 + O505 8,571 + X001 5,000 − O202 4,519 − O404 1로 정확히 설명된다. 하지만 총액만으로는 이 분해를 알 수 없다. ⑦은 총액에 전혀 나타나지 않는다(16,057 = 16,057).

### 실험: 날짜 경계를 다르게 자르면

(실험, PostgreSQL 17.11, 2026-10-03) — 내부 1,000건은 KST 10-02 하루(= 10-01 15:00Z ~ 10-02 15:00Z)에 고르게 있다.

```text
--- (6) 날짜 경계: 내부는 KST 10-02 하루, 외부 파일은 UTC 10-02 하루로 잘랐다
 internal_rows | external_rows | only_internal | only_external
---------------+---------------+---------------+---------------
          1000 |           625 |           376 |             1
--- (7) 같은 기준(둘 다 KST 10-02 = [10-01 15:00Z, 10-02 15:00Z))으로 자르면
 internal_rows | external_rows | only_internal | only_external
---------------+---------------+---------------+---------------
          1000 |          1000 |             1 |             1
```

- 경계가 9시간 어긋나자 376건이 "내부에만 있음"으로 나왔다. 진짜 차이(O202 누락, X001)는 그 속에 묻힌다.
- 같은 경계(`timestamptz` 반열린 구간 `[시작, 끝)`)로 자르자 남은 차이는 주입한 2건뿐이다.

### 실험: 차이를 사건으로 남기고, 자동 확정은 UNKNOWN만

```sql
-- 외부 승인이 금액까지 같으면 '결과를 모르던' 내부 결제를 확정한다
WITH r AS (
  UPDATE payment p SET status = 'PAID', pg_tx_id = b.ext_tx
    FROM recon_break b
   WHERE b.result = 'RESOLVE_UNKNOWN' AND b.order_id = p.order_id
     AND b.int_amt = b.ext_amt AND p.status = 'UNKNOWN'
  RETURNING p.order_id)
UPDATE recon_break b SET state = 'RESOLVED',
       resolution = 'external APPROVED '||b.ext_tx||' → internal PAID'
  FROM r WHERE r.order_id = b.order_id;
```

(실험, PostgreSQL 17.11, 2026-10-03)

```text
 order_id |       result       |  state   |               resolution
----------+--------------------+----------+----------------------------------------
 O101     | RESOLVE_UNKNOWN    | RESOLVED | external APPROVED T101 → internal PAID
 O202     | MISSING_EXTERNAL   | OPEN     | (사람 검토 대기)
 O303     | DUPLICATE_EXTERNAL | OPEN     | (사람 검토 대기)
 ...
 X001     | MISSING_INTERNAL   | OPEN     | (사람 검토 대기)
```

- 타임아웃 났던 O101이 외부 기록으로 확정됐다. 이것이 "결과를 모르는 요청의 최종 확정 경로"다.
- 나머지 7줄은 OPEN으로 남는다. 자동으로 외부 값에 맞추지 않았기 때문에 원인(중복 승인, 1원 차이, 취소 미전달)이 그대로 보인다.

## 쓰이는 자료구조·알고리즘

- **해시 조인** — 한쪽(보통 작은 쪽)을 키로 해시 테이블에 넣고 다른 쪽을 훑으며 찾는다. 실험의 분류 쿼리를 `EXPLAIN (COSTS OFF)`로 보면 PostgreSQL 17.11은 `Hash Full Join`으로 실행했다. 외부 쪽 주문 단위 접기는 `Sort` + `GroupAggregate`였다 — `string_agg(… ORDER BY line_no)`처럼 정렬이 필요한 집계가 있어서다(해석). `string_agg`를 빼면 같은 데이터에서 `HashAggregate`로 바뀌었다(점검 재실행, ANALYZE 전후 같음). 조인 알고리즘은 [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md).
- **정렬 병합 조인** — 양쪽을 키로 정렬한 뒤 두 포인터로 함께 훑는다. 파일이 메모리보다 크면 외부 정렬 + k-way 병합으로 정렬한다([algorithm 11-external-sort-and-k-way-merge](../../algorithm/curriculum.md) — 미작성, 두 포인터는 [algorithm/08-two-pointers](../../algorithm/08-two-pointers/2-summary.md)).
- **두 집합의 차집합** — `A EXCEPT B`, `B EXCEPT A`. 빠른 "차이 있음" 신호. 단, 집합 의미라 중복을 지운다(실험 관찰 1).
- **group-by 접기 후 조인** — 외부를 키로 `count(*)`·`sum()`으로 접어야 중복이 "2건 이상"으로 보인다. 접지 않고 조인하면 내부 한 줄이 외부 두 줄과 짝지어져 행이 늘어난다.
- **반열린 시간 구간** — `[시작, 끝)`을 같은 `timestamptz` 경계로. 날짜 문자열로 자르지 않는다.
- **상태 기계** — 결제의 성공·실패·모름(UNKNOWN) 세 상태, 그리고 대사 사건의 OPEN → RESOLVED([11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md), 연습은 [basic/09-order-state](../basic/09-order-state/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. **대사 키를 저장한다** — 결제 요청 전에 주문 ID를 PG에 보내고, 응답의 거래 ID를 저장한다. 타임아웃으로 응답이 없으면 주문 ID가 유일한 키다. 키가 없으면 금액·시각으로 붙이게 되고, 합은 맞는데 짝은 틀린다([advanced/18-settlement-match](../advanced/18-settlement-match/2-summary.md)의 측정: 금액 매칭이 6,000줄 중 2,893줄을 엉뚱하게 붙였다).
2. **결제 상태에 UNKNOWN을 둔다** — 타임아웃을 FAILED로 두지 않는다. UNKNOWN은 조회 API나 대사로만 빠져나간다.
3. **외부 파일을 원본 그대로 적재한다** — 줄 번호·파일명·받은 시각과 함께.
4. **경계를 맞춘다** — 외부 파일의 날짜 기준(시간대, 매출일/지급일)을 문서로 확인하고 내부 추출을 같은 `timestamptz` 구간으로 자른다.
5. **분류 쿼리를 돌리고 사건 테이블에 남긴다** — MATCHED 수와 분류별 건수를 지표로 낸다.
6. **자동 처리 규칙은 좁게** — UNKNOWN 확정처럼 원인이 정해진 것만. 나머지는 담당자 큐로.
7. **조정은 분개로** — 원장의 원 전표를 고치지 않고 조정 전표를 넣는다([24](../24-double-entry-ledger/2-summary.md)).
8. **대사가 돌았는지 감시한다** — 파일이 안 오거나 배치가 실패하면 "차이 0건"처럼 보인다(reliability/04 F-21 "대사 + 대사가 도는지 감시").

### 2. 타임아웃 → 조회 → 대사의 두 단계 확정

```java
enum PaymentStatus { PENDING, PAID, FAILED, UNKNOWN }

PaymentStatus approve(Order order) {
    try {
        PgResponse r = pg.approve(order.id(), order.amount());    // 주문 ID를 PG에 보낸다
        order.markPaid(r.txId());                                 // 대사 키 저장
        return PaymentStatus.PAID;
    } catch (PgTimeoutException e) {
        order.markUnknown();                                      // 실패가 아니라 "모름"
        return PaymentStatus.UNKNOWN;                             // 재시도·취소를 바로 하지 않는다
    }
}

// 1단계(분 단위): 조회 API로 확정 — 예: 토스페이먼츠 GET /v1/payments/orders/{orderId}
// 2단계(일 단위): 조회로도 못 정한 것은 대사가 확정 — 외부 파일에 승인이 있으면 PAID, 없으면 FAILED 후보
```

- 조회 API는 빠르지만 그 호출도 타임아웃날 수 있다. 대사는 늦지만 외부 장부 전체를 본다. 둘은 대체가 아니라 단계다.
- 멱등키로 재시도하는 길도 있다. 다만 키 보존 기간이 유한하다 — Stripe 문서는 키를 최소 24시간 뒤 정리할 수 있고, 정리된 뒤 같은 키를 쓰면 새 요청으로 처리한다고 적는다. 키가 정리된 뒤의 재시도는 대사로 넘긴다([reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)).

### 3. 진단 쿼리

```sql
-- 중복 승인: 외부를 키로 접어 2건 이상
SELECT order_id, count(*), string_agg(pg_tx_id, ',') FROM pg_settlement GROUP BY order_id HAVING count(*) > 1;
-- 대사 키 없는 내부 결제(UNKNOWN이 오래 남아 있나)
SELECT order_id, paid_at FROM payment WHERE pg_tx_id IS NULL AND status = 'UNKNOWN' AND paid_at < now() - interval '1 day';
-- 차이가 매일 "저절로 풀리는가" — 경계 문제의 신호
SELECT run_date, result, count(*) FROM recon_break GROUP BY 1, 2 ORDER BY 1, 2;
```

## 장애 시나리오와 대처

### 1. PG는 승인했는데 내부 호출이 타임아웃났다 → 돈은 빠졌는데 주문이 없다 (⚠)

- 현상: 고객 카드에서 돈이 나갔는데 주문 내역이 없다. 고객이 다시 결제한다.
- 보이는 형태: 내부 로그에 PG 호출 타임아웃. PG 관리 화면에는 같은 주문 ID의 승인. 고객 민원 "두 번 빠졌다".
- 원인: 타임아웃을 실패로 처리하고 주문을 닫았다. 결과를 확정하는 경로(조회·대사)가 없었다.
- 대처: 타임아웃은 UNKNOWN으로 둔다. 조회 API로 1차 확정, 대사로 2차 확정한다(실험 O101). 방치된 UNKNOWN은 PG 취소 또는 주문 생성으로 처리한다. 재결제는 새 주문 ID로 들어오므로 주문 ID 키 대사의 DUPLICATE_EXTERNAL로는 잡히지 않는다(원 주문은 STATUS_MISMATCH나 RESOLVE_UNKNOWN으로 드러난다). 같은 고객·같은 금액·가까운 시각의 결제를 "이중 청구 후보"로 따로 묶어 사람이 확인한 뒤 한쪽을 취소·환불한다.

### 2. 대사를 하지 않는다 → 누락이 고객 민원으로 발견된다 (⚠)

- 현상: 몇 주 뒤 고객이 "결제했는데 상품이 안 왔다"고 연락한다. 확인해 보니 같은 유형이 수십 건이다.
- 보이는 형태: 민원 티켓이 먼저, 데이터 이상은 나중. 내부 지표는 모두 정상.
- 원인: 내부 원장만 보고 있었다. 외부와의 차이를 찾는 정기 절차가 없었다.
- 대처: 일 단위 대사를 배치로 돌리고 분류별 건수를 지표·경보로 낸다. 대사 배치가 돌지 않은 날도 경보한다.

### 3. 대사 키(외부 거래 ID)를 저장하지 않았다 → 수작업으로 매칭한다 (⚠)

- 현상: 정산 담당자가 엑셀로 금액·시각을 눈으로 맞춘다. 같은 금액 결제가 많은 날은 끝나지 않는다.
- 보이는 형태: 금액이 같은 후보가 여럿. 짝을 잘못 붙여도 합계는 맞는다.
- 원인: PG 응답의 거래 ID를 버렸거나, 우리 주문 ID를 PG 요청에 싣지 않았다.
- 대처: 요청 시 주문 ID 전달, 응답의 거래 ID 저장을 결제 흐름의 필수 단계로 둔다(UNIQUE). 과거 데이터는 PG 조회 API로 주문 ID → 거래 ID를 채운다. 금액 매칭은 "후보"로만 쓰고 확정하지 않는다.

### 4. 날짜 경계(시간대)가 외부와 달라 매일 가짜 차이가 난다 (⚠)

- 현상: 매일 수백 건의 "내부에만 있음"이 나오고, 다음 날 반대쪽에서 비슷한 수가 나와 상쇄된다. 담당자가 차이를 무시하기 시작한다.
- 보이는 형태: 차이 시각이 특정 시간대(예: KST 00:00~09:00)에 몰린다. 실험에서 경계를 9시간 어긋나게 자르자 1,000건 중 376건이 "내부에만 있음"으로 나왔고, 그중 375건이 가짜 차이였다(나머지 1건은 진짜 누락 O202).
- 원인: 내부는 로컬 날짜, 외부 파일은 UTC 날짜(또는 매출일 vs 지급일). 경계가 다르다.
- 대처: 외부 문서로 기준을 확인한다(Stripe 보고서는 시간대 미지정 시 UTC). 내부 추출을 같은 `timestamptz` 반열린 구간으로 자른다. 경계 근처는 하루 겹쳐 가져와 키로 맞춘 뒤 기간 귀속을 따로 판단한다.

### 5. 차이를 자동 보정한다 → 원인이 은폐된다 (⚠)

- 현상: 대사 차이 0건이 몇 달 이어진다. 감사에서 내부 결제 금액이 수시로 외부 값으로 덮어써진 것이 드러난다.
- 보이는 형태: 대사 지표는 깨끗하다. 원장에 설명 없는 조정이 많다. 같은 1원 차이가 매일 같은 상품에서 난다.
- 원인: "외부가 정본"이라며 차이를 발견 즉시 내부를 외부에 맞췄다. 우리 쪽 반올림 버그·PG 쪽 오류가 둘 다 지워졌다.
- 대처: 차이는 먼저 사건(recon_break)으로 남긴다. 자동 처리는 원인이 정해진 분류만(실험: UNKNOWN 확정). 보정은 근거 문장이 붙은 조정 분개로 한다. 같은 원인의 반복은 원인 수정 작업으로 올린다.

## 핵심 문장

- 대사는 총액이 아니라 **키로 줄을 맞추는 일**이다 — 실험에서 금액이 서로 뒤바뀐 두 줄은 총액에 전혀 나타나지 않았다.
- 타임아웃은 실패가 아니라 모름이고, 모름을 **최종 확정하는 경로가 대사**다.
- 차이는 종류마다 원인과 처리가 다르다 — 누락·중복·금액·상태를 나누고, 중복은 금액 비교보다 먼저 본다.
- 두 장부는 **같은 시간대·같은 기준 날짜**로 잘라야 한다 — 경계가 9시간 어긋나자 1,000건 중 375건이 가짜 차이로 나와 진짜 누락 1건을 덮었다.
- 차이를 발견 즉시 덮어쓰면 원인이 사라진다 — 먼저 사건으로 남기고, 자동 처리는 원인이 정해진 분류에만 둔다.

## 관련 주제·근거

### 선행·후속

- 선행: [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) · [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md)
- 같은 영역: [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md)(날짜 경계) · [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md)(1원 차이의 원인) · [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) · [27-dm-symptom-index](../27-dm-symptom-index/2-summary.md)("504인데 결제됨")
- 다른 영역: [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md) · [database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md)(FULL OUTER JOIN·NULL) · [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md) · [reliability/04-failure-modes-catalog](../../reliability/04-failure-modes-catalog/2-summary.md)(결제 F-20 이중 결제·F-21 정산 불일치 탐지 지연·F-23 전표 누락·중복) · [distributed/20-data-ownership-and-cross-service-queries](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md) · [api-design/04-settlement-report](../../api-design/25-case-settlement-report/2-summary.md)
- 연습 문제: [advanced/18-settlement-match](../advanced/18-settlement-match/2-summary.md)(참조값 없는 금액 매칭의 함정) · [advanced/17-batch-retry](../advanced/17-batch-retry/2-summary.md)(결과를 모르는 호출) · [advanced/15-period-close](../advanced/15-period-close/2-summary.md)(발생 시각·도착 시각, 마감 뒤 늦은 거래) · [basic/10-payment](../basic/10-payment/2-summary.md)(멱등키)

### 근거

- Stripe Docs, "Payout reconciliation report" — https://docs.stripe.com/reports/payout-reconciliation (지급 한 건과 거래 묶음을 맞춤, Dashboard 보고서는 하루 단위, 보고서 데이터는 별도 처리 일정) · 열 설명 https://docs.stripe.com/reports/report-types/payout-reconciliation ("Dates in the requested timezone, or UTC if not provided")
- Stripe API Reference, "Idempotent requests" — https://docs.stripe.com/api/idempotent_requests (첫 결과 저장·같은 키는 같은 결과, 키는 최소 24시간 뒤 정리 가능)
- 토스페이먼츠 API 레퍼런스 — https://docs.tosspayments.com/reference (`GET /v1/payments/orders/{orderId}` 주문 ID로 결제 조회, `GET /v1/settlements`의 `dateType` = `soldDate`/`paidOutDate`)
- PostgreSQL 17 문서 — 7.2.1.1 Joined Tables(FULL OUTER JOIN), 7.4 Combining Queries("duplicates are eliminated unless EXCEPT ALL is used") https://www.postgresql.org/docs/17/queries-union.html
- 결제사별 정산 파일 형식·지연 시간은 계약·상품마다 다르다 [?] — 이 노트는 위 공개 문서로 확인한 범위만 적었다.

### 실험 목록

- 대사 분류(EXCEPT·FULL OUTER JOIN·총액 비교·뒤바뀐 금액) — PostgreSQL 17.11 일회용 컨테이너, `recon_setup.sql` + `recon_query.sql`
- 날짜 경계(KST vs UTC) — 같은 환경, `recon_tz.sql`
- 사건 테이블 + UNKNOWN 자동 확정 — 같은 환경, `recon_resolve.sql`
