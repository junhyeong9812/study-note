# data-engineering/13-data-vault — 정답

## 정답

### 1. 스타 스키마 직접 적재의 어려움과 볼트의 분리

- 원천 컬럼이 추가·교체되면 차원과 적재 로직을 다시 짜야 한다.
- 원천 추출본을 따로 보존하지 않고 스타 스키마에 맞추려고 정제(cleansing)하면 원천이 보낸 원래 값이 사라진다. "그때 원천이 뭐라고 보냈나"에 답할 수 없다.
- 데이터 볼트는 **구조**(Hub의 비즈니스 키, Link의 관계)와 **서술**(Satellite의 속성 이력)을 뗀다.
  - 새 원천이 기존 키에 속성만 더하면 Satellite를 하나 더 붙인다. 새 비즈니스 키·관계가 있으면 Hub·Link도 더한다. 어느 쪽이든 기존 표는 그대로다.
  - 행마다 record source·load date를 붙여 원천까지 추적한다(Wikipedia "Data vault modeling").
  - 정제는 Raw Vault가 아니라 그 바깥(Business Vault의 업무 규칙이나 마트)에서 한다.

### 2. Hub·Link·Satellite 그림

```text
  hub_customer(customer_hk PK, customer_bk, load_ts, record_source)
  hub_order(order_hk PK, order_bk, load_ts, record_source)
  link_customer_order(link_hk PK, customer_hk, order_hk, load_ts, record_source)
  sat_customer_crm(customer_hk, load_ts  PK, hashdiff, tier, region, record_source)
  sat_customer_billing(customer_hk, load_ts PK, hashdiff, credit_limit, record_source)
  sat_order(order_hk, load_ts PK, hashdiff, amount, record_source)
```

- 공통 메타데이터: `load_ts`(적재 시각), `record_source`(원천).
- Hub·Link에는 속성이 없다. 일반 Satellite의 기본 키는 (부모 해시 키, load_ts)다.
  - Multi-Active Satellite(고객의 전화번호 여러 개처럼 같은 시각에 유효한 행이 여럿)는 child dependent key를 기본 키에 더한다(AutomateDV "Multi-Active Satellites").

### 3. 정규화 없음 vs 있음

- `md5(customer_id)`: Hub 3행(`' c001 '`, `'C001'`, `'C002'`). 고객별 매출은 `' c001 '` 200, `'C001'` 100, `'C002'` 50.
- `md5(upper(trim(customer_id)))`: Hub 2행(C001, C002). 고객별 매출은 C001 300, C002 50.
- 총합 350은 두 경우 같다. 그래서 총액만 보는 대시보드로는 이 오류를 못 잡는다.
- 실험(PostgreSQL 17.11) 출력이 위와 같았다. 해시 값: `'C001'` → `928c6512…`, `' c001 '` → `059f750f…`.

### 4. hashdiff 적재와 Satellite 곱 조인

- CRM Satellite: day1·day3·day5에만 새 행 → 3행.
- BILLING Satellite: day1·day4에만 새 행 → 2행.
- Hub 키만으로 두 Satellite를 조인하면 3 × 2 = 6행이다. 한도는 1000이 3행, 3000이 3행이다. 합은 12000이다. 현재 한도는 3000이다.
- 실험 출력: `crm 1,0,1,0,1`, `billing 1,0,0,1,0`, `joined_rows 6`, `naive_sum_credit_limit 12000`.
- 고치는 법: PIT 좌표 `(hk, ldts)`로 조인하거나 Satellite마다 최신 행 하나를 고른다.

### 5. 해시 키의 경계

- 적재 순서: 시퀀스 대리 키는 Hub를 먼저 적재해 ID를 받은 뒤에야 Link·Satellite가 그 ID를 쓴다(Wikipedia "Loading practices"). 해시 키는 비즈니스 키만으로 계산하므로 Hub·Link·Satellite를 같은 스테이징에서 나란히 적재할 수 있다(해석).
- 보안: 아니다. AutomateDV 문서는 해시를 최적화·유일성 용도로 쓴다고 밝히고, 소금 없는 해시된 PII는 무차별 대입으로 되돌릴 수 있다고 경고한다.
- 충돌 vs 정규화: 생일 근사로 128비트 해시에 키 10¹⁰개를 넣을 때 충돌 확률은 약 1.5 × 10⁻¹⁹이다(계산). 무작위 입력에서는 정규화 누락이 훨씬 현실적인 위험이다(해석). 공격자가 키를 고를 수 있으면 MD5의 충돌 저항이 깨져 있다는 점은 따로 따진다.

### 6. Satellite vs SCD Type 2, 두 시각

- 같은 점: 덮어쓰지 않고 새 행을 추가해 이력을 남긴다(Wikipedia는 "Type-II history와 효과가 비슷하다"고 적는다).
- 다른 점
  - SCD Type 2는 차원 테이블 하나에 대리 키·유효 기간·현재 플래그를 둔다. 분석용 모양이다.
  - Satellite는 원천별로 나뉘고, AutomateDV 구조에는 끝 시각 컬럼이 없다. 구간은 다음 행이나 PIT로 계산한다. 통합·감사용 모양이다.
- `load_ts`: "우리가 언제 알았나"(적재 시각).
- `EFFECTIVE_FROM`: "현실에서 언제부터 유효했나"(업무 시각). AutomateDV는 이것을 DV 2.0 표준 밖의 선택 컬럼으로 둔다.
- 두 축은 database/50의 기록 시간·유효 시간 구분과 같다.

### 7. 리포트가 느려진다 — Satellite 폭증

- 원인: 원천·변경 속도별로 Satellite를 계속 나눠, 리포트 하나가 볼트를 직접 수십 번 조인한다. PIT 없이 조회하면 최신 행 고르기(시각별 `max(load_ts)`)도 Satellite마다 반복한다. 아래 실험은 PIT를 쓴 상태에서 조인 수만 늘린 측정이라, 이 비용은 재지 않았다.
- PIT: 기준 시각마다 각 Satellite의 `(hk, load_ts)` 좌표를 미리 계산해 둔다. 리포트는 등가 조인만 한다(AutomateDV "Point In Time (PIT) tables").
- 더 줄이려면 자주 쓰는 모양을 마트 테이블로 물질화한다.
- 측정: `EXPLAIN (ANALYZE, SUMMARY)`의 Planning Time·Execution Time. 실험에서 k=2 → 32로 늘리자 계획 0.65~1.67ms → 45.0~60.7ms, 실행 6.5~10.8ms → 156~206ms였다(두 번 돌린 6회 범위). 물질화한 마트는 실행 1.6~1.9ms였다(2,000행, 한 호스트).

### 8. Satellite가 매일 전 행을 쌓는다

- 원인 후보
  1. hashdiff 입력에 적재 시각·추출 시각처럼 매번 바뀌는 컬럼이 섞였다.
  2. 컬럼 순서가 원천·버전마다 달라 같은 값이 다른 해시가 된다.
  3. NULL과 빈 문자열, 공백·대소문자 표기가 매번 다르게 들어와 다른 해시가 된다.
- 확인 쿼리: 연속 두 행의 payload가 같은데 행이 생긴 곳을 찾는다.

```sql
SELECT customer_hk, load_ts
FROM (SELECT *, lag(row(tier, region)) OVER w AS prev FROM sat_customer_crm
      WINDOW w AS (PARTITION BY customer_hk ORDER BY load_ts)) x
WHERE prev IS NOT DISTINCT FROM row(tier, region);
```

- 로컬 재현에서 같은 payload 행을 일부러 하나 넣자 이 쿼리가 그 1행을 찾았다.

### 9. 볼트만 있고 마트가 없다

- 빠진 것: 정보 마트(스타 스키마)와 그 변환.
- 볼트 계층은 질의 성능에 최적화되어 있지 않다. BI 도구는 차원 모델을 기대한다(Wikipedia "Data vault and dimensional modelling").
- Hub와 그 Satellite를 차원으로, Link와 그 Satellite를 팩트로 뷰를 먼저 만들고, 느린 것만 물질화한다.
- 첫 릴리스에 마트 한두 개를 같이 내야 분석가가 운영 DB에서 떠난다.
