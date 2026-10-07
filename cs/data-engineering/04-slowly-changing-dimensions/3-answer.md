# data-engineering/04-slowly-changing-dimensions — 정답

## 정답

### 1. 팩트가 그대로인데 과거 숫자가 바뀌는 이유

- 리포트는 팩트를 차원 속성으로 묶는다. 차원 속성을 덮어쓰면 같은 팩트가 다른 묶음으로 간다.
- as-was: 사건이 일어난 그때의 속성으로 묶는다("8월에 서울 고객이 산 것").
- as-is: 지금의 속성으로 묶는다("지금 부산 고객들이 8월에 산 것").
- 덮어쓰기(Type 1)는 as-is밖에 남기지 않는다. 그래서 지난달 리포트를 다시 뽑으면 as-is로 바뀌어 나온다.

### 2. Type 1 vs Type 2 (실험)

- Type 1, 10/1 조회: busan 1000 · daegu 1100. seoul 행이 사라진다(300이 부산으로 옮겨 감).
- Type 2
  - as-was(대리 키 조인): busan 700 · daegu 1100 · seoul 300 — 9/1과 같다.
  - as-is(내구 키 → 현재 행 조인): busan 1000 · daegu 1100 — Type 1 결과와 같다.

### 3. Type 2 타임라인

```text
  user_001  (자연 키 'user_001', 내구 키 1)
  key=1    seoul  [2026-01-01, 2026-09-15)  is_current=f
  key=101  busan  [2026-09-15, ∞)           is_current=t
```

- 대리 키: 버전마다 새 값(1, 101). 팩트가 가리킨다.
- 내구 키: 고객마다 하나(1). 버전이 바뀌어도 그대로.
- 자연 키: 원천의 `user_001`.
- Kimball Group Type 2 페이지가 권하는 최소 세 컬럼: 행 유효 시작 일자(시각), 행 만료 일자(시각), 현재 행 표시.

### 4. 유형 구분

| 유형 | 한 줄 |
|---|---|
| 0 | 처음 값을 바꾸지 않는다 |
| 1 | 덮어쓴다(이력 소실) |
| 2 | 새 대리 키로 새 행, 옛 행은 닫는다 |
| 3 | 직전 값 컬럼을 하나 더 둔다 |
| 4 | 자주 바뀌는 속성 묶음을 미니 차원으로 떼고, 팩트가 기본·미니 차원 키를 둘 다 가진다 |
| 5 | 4 + 기본 차원에 "현재 미니 차원 키"를 Type 1으로(4 + 1) |
| 6 | Type 2 행에 현재 값 컬럼을 두고 같은 내구 키의 전 행을 덮어쓴다(2 + 3 + 1) |
| 7 | 팩트에 대리 키와 내구 키를 둘 다 둔다 |

- Type 6은 차원 행 안에 현재 값을 **물리적으로 덮어써** 둔다. Type 7은 덮어쓰지 않고, 팩트의 **내구 키로 현재 행을 조인**해 같은 결과를 낸다(Design Tip #152).

### 5. 진단 SQL

```sql
-- 겹침
SELECT a.customer_dk, a.customer_key, b.customer_key
FROM dim_customer a JOIN dim_customer b
  ON a.customer_dk = b.customer_dk AND a.customer_key < b.customer_key
 AND tstzrange(a.valid_from, a.valid_to) && tstzrange(b.valid_from, b.valid_to);

-- 이웃 행 대조 (겹침·빈틈)
SELECT customer_dk, customer_key, valid_to, next_start,
       CASE WHEN next_start < valid_to THEN 'overlap' ELSE 'gap' END
FROM (SELECT *, lead(valid_from) OVER (PARTITION BY customer_dk ORDER BY valid_from) AS next_start
      FROM dim_customer) x
WHERE next_start IS NOT NULL AND next_start <> valid_to;

-- 현재 행 중복
SELECT customer_dk, count(*) FROM dim_customer WHERE is_current GROUP BY 1 HAVING count(*) > 1;

-- 현재 행 없음 (마지막 행만 닫힌 멤버 — 이웃 행 대조는 다음 행이 없어 못 잡는다)
SELECT customer_dk, max(valid_to) FROM dim_customer GROUP BY 1 HAVING count(*) FILTER (WHERE is_current) = 0;
```

- 구분: 시작 순으로 정렬한 이웃 행에서 "다음 시작 < 이 끝"이면 겹침, "다음 시작 > 이 끝"이면 빈틈. 반열린 구간이면 정상은 "다음 시작 = 이 끝"이다.
- 실험 출력: `3 | 3 | infinity | 2026-09-10 | overlap`, `5 | 5 | 2026-09-01 | 2026-09-05 | gap`.

### 6. 겹침·빈틈과 기간 조인 (실험)

- user_003 구매 900: 차원 두 행에 맞아(`matched_rows 2`) 1800으로 세진다.
- user_005 구매 800: 맞는 행이 없어(`matched_rows 0`) 빠진다. inner join이면 행이 사라지고, left join이면 지역이 NULL이다.

### 7. 적재 시점 제약

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE dim_customer ADD CONSTRAINT no_overlap
  EXCLUDE USING gist (customer_dk WITH =, tstzrange(valid_from, valid_to) WITH &&);
CREATE UNIQUE INDEX one_current ON dim_customer(customer_dk) WHERE is_current;
```

- 실험: 겹치는 행은 `violates exclusion constraint "no_overlap"`, 두 번째 현재 행은 `violates unique constraint "one_current"`로 거부되었다.
- 막지 못하는 것: 빈틈과 현재 행 0개. 두 행이 겹치지 않으면 제약은 만족하고, 부분 유일 인덱스는 "최대 하나"만 건다. 이웃 행 대조와 "현재 행 없음" 검사를 적재 후 검사로 돈다(마지막 행만 닫힌 멤버는 이웃 행 대조에 0행으로 나온다).

### 8. 늦게 온 팩트

- `is_current`로 찾으면 지금 행(key 102, busan)을 가리킨다. 8월 매출이 부산으로 잡힌다. 에러는 없다(실험).
- 올바른 조건: 사건 시각으로 as-of 조회.

```sql
SELECT customer_key FROM dim_customer
WHERE customer_id = :customer_id AND :sold_at >= valid_from AND :sold_at < valid_to;
-- 실험: key 2, seoul
```

- 이 조회는 자연 키 `customer_id`가 바뀌지 않는다고 가정한다. 자연 키가 바뀌는 원천이면 매핑으로 내구 키를 먼저 찾고 `customer_dk`로 조회한다(Kimball Design Tip #147).

- 차원 변경 자체가 늦게 도착하면, 차원에 새 행을 넣고 영향받은 팩트를 다시 써야 한다(Kimball, Late Arriving Dimensions 페이지).

### 9. Type 2와 유효 시간

- Type 2의 `[valid_from, valid_to)`는 "이 속성 값이 현실에서 언제부터 언제까지 참이었나"를 담는다. database/50의 유효 시간과 같은 축이다.
- 다만 보통의 Type 2는 기록 시간(DB가 언제 알았나)을 따로 두지 않는다. 소급 정정을 하면 "그때 알던 기준" 리포트는 재현할 수 없다. 그것이 필요하면 바이템포럴로 간다([database/50](../../database/50-temporal-and-bitemporal-tables/2-summary.md)).
- 반열린 구간 이유: 경계 시각(9/15 00:00)에 정확히 한 행만 유효하다. 옛 행의 끝과 새 행의 시작에 같은 값을 쓰면 겹침도 빈틈도 생기지 않는다. Java as-of 실행에서 9/15 00:00은 새 행(102)으로 판정되었다.
