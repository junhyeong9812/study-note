# database/04-sql-joins-and-aggregation — 조인·집계·NULL: 에러 없이 틀리는 숫자들 — 정리 (힌트)

## 해결하는 문제

정규화(03번)로 쪼갠 테이블을 다시 이어 붙이고(조인), 여러 행을 한 줄로 요약(집계)해야 보고서가 나온다.\
앱에서 루프로 하면 이렇다.

```text
  for order in orders:                  # N번
      items = query(order.id)           # N번 왕복
      total += sum(items.qty)
```

- SQL은 이것을 한 문장으로 선언한다. DB가 조인 방법과 순서를 고른다(01번).
- 대신 SQL 문장은 **틀려도 에러가 나지 않는다.** 행이 불어나거나(팬아웃), NULL 때문에 조건이 조용히 거짓이 되거나, 외부 조인이 내부 조인으로 바뀐다. 결과는 그럴듯한 숫자다.

쉬운 예: 반 학생 명단과 동아리 가입 명단을 이어 붙여 "반 학생 수"를 셌다. 동아리 두 개 든 학생이 두 번 세어져 인원이 늘었다.

똑같은 구조다.\
조인은 짝이 맞는 **모든 조합**을 만든다. 집계는 그 조합 위에서 센다. 어떤 행이 몇 번 만들어졌는지 모르면 합계는 틀린다.

실무 예:
- 주문에 상세 3줄, 결제 2건이 있다. 셋을 한 번에 조인해 `SUM(paid)`를 내자 결제액이 3배가 된다.
- 블랙리스트에 NULL 한 줄이 섞이자 `NOT IN` 조회 결과가 0건이 된다.
- 쿠폰 미사용 주문까지 보려고 `LEFT JOIN coupon`을 했는데 `WHERE coupon.type = 'X'` 한 줄로 미사용 주문이 사라진다.

## 동작·원리

### 1. 논리 처리 순서 — 쓰는 순서와 계산 순서가 다르다

```text
  쓰는 순서                 논리 처리 순서 (PostgreSQL 17 SELECT "Description")
  WITH …                    1  WITH          CTE 계산
  SELECT 목록 (윈도 함수)     2  FROM / JOIN   곱·조인 (ON은 조인 중에)
  FROM … JOIN … ON          3  WHERE         행 거르기 (집계 전)
  WHERE                     4  GROUP BY      묶기 + 집계 함수 계산
  GROUP BY                  5  HAVING        그룹 거르기
  HAVING                    6  SELECT 목록   출력 식 계산 (윈도 함수는 여기, 05번)
  (DISTINCT는 SELECT 옆)     7  DISTINCT
  UNION/INTERSECT/EXCEPT    8  집합 연산
  ORDER BY                  9  ORDER BY
  LIMIT / OFFSET            10 LIMIT / OFFSET
```

- "논리" 순서다. 결과가 이 순서로 계산한 것과 **같아야** 한다는 뜻이다. 실제 실행은 옵티마이저가 바꾼다(예: WHERE를 조인 아래로 내림).
- 결과로 드러나는 규칙(로컬 재현, PostgreSQL 17.11)
  - `SELECT customer AS c FROM ord WHERE c = 'kim'` → `column "c" does not exist`. WHERE는 SELECT 목록보다 먼저라 별칭을 모른다.
  - `WHERE row_number() OVER () = 1` → `42P20 window functions are not allowed in WHERE`.
  - `GROUP BY c`(별칭)는 PostgreSQL이 허용한다. SELECT 레퍼런스 "GROUP BY Clause"가 GROUP BY 요소로 출력 열(SELECT 목록 항목)의 이름이나 번호를 쓸 수 있다고 적는다. 이름이 모호하면 출력 열이 아니라 입력 열로 해석한다.

### 2. 조인 — 어떤 짝을 남기나

```text
  ord            payment               INNER JOIN ON p.order_id = o.id
  id cust        order_id amount       → 짝이 있는 조합만       (1,60) (1,40) (2,50)
  1  kim         1        60
  2  lee         1        40           LEFT JOIN
  3  park        2        50           → 왼쪽은 전부, 짝 없으면 오른쪽 NULL
                                         (1,60) (1,40) (2,50) (3,NULL)

  세미 조인  EXISTS (…)      : 짝이 하나라도 있는 왼쪽 행을 "한 번만"   → 1, 2
  안티 조인  NOT EXISTS (…)  : 짝이 하나도 없는 왼쪽 행              → 3
```

- *내부 조인(inner join)*: 조건을 만족하는 조합만 남긴다. 짝 없는 행은 사라진다.
- *외부 조인(outer join)*: 한쪽(LEFT/RIGHT) 또는 양쪽(FULL)의 짝 없는 행도 남기고 반대쪽을 NULL로 채운다.
- *세미 조인 / 안티 조인*: 결과에 오른쪽 열을 붙이지 않고, 짝의 존재 여부로만 왼쪽을 거른다. 왼쪽 행이 **불어나지 않는다**.

### 3. `ON` vs `WHERE` — 외부 조인에서만 다르다

```text
  (예시, PostgreSQL 17.11)
  LEFT JOIN payment p ON p.order_id = o.id AND p.amount >= 50     LEFT JOIN payment p ON p.order_id = o.id
                                                                  WHERE p.amount >= 50
  id | amount                                                    id | amount
   1 |     60                                                     1 |     60
   2 |     50                                                     2 |     50
   3 |          <- 짝 없는 주문도 남는다                              (3이 사라졌다)
```

- PostgreSQL 17 7.2.1.1: ON의 조건은 조인 **전에**, WHERE의 조건은 조인 **뒤에** 처리된다. 내부 조인에서는 차이가 없고 외부 조인에서 크다.
- 오른쪽 열에 대한 WHERE 조건이 NULL에서 참이 될 수 없는 것(`p.amount >= 50`, `=` 등)이면 NULL로 채운 행을 모두 떨어뜨린다. `p.amount IS NULL`처럼 NULL에서 참인 조건은 그 행을 남긴다(MySQL 8.4 10.2.1.10 Outer Join Simplification의 "null-rejected"). 로컬 재현에서 PostgreSQL은 그 쿼리의 계획을 아예 `Hash Join`(내부 조인)으로 바꿨다. 외부 조인이 의미를 잃었다는 것을 옵티마이저도 안다.

### 4. NULL과 3치 논리

```text
  비교에 NULL이 끼면 결과는 TRUE/FALSE가 아니라 UNKNOWN(NULL)

  AND   | T  F  U         OR    | T  F  U         NOT
  T     | T  F  U         T     | T  T  T         T → F
  F     | F  F  F         F     | T  F  U         F → T
  U     | U  F  U         U     | T  U  U         U → U

  WHERE·HAVING은 TRUE인 행·그룹만 남긴다 (FALSE와 UNKNOWN은 버린다)
  ON은 TRUE인 짝만 맺는다 (외부 조인이면 짝 없는 쪽 행은 NULL로 채워 남는다)
```

- 로컬 재현(예시, PostgreSQL 17.11): `NULL = NULL` → NULL, `NULL IS NULL` → true, `1 NOT IN (2, NULL)` → NULL, `1 IN (1, NULL)` → true, `NULL AND false` → false, `NULL OR true` → true.
- `NOT IN`의 정체

```text
  x NOT IN (a, b, NULL)
  = x <> a AND x <> b AND x <> NULL
  = …      AND …      AND UNKNOWN
  → 짝이 없어도 결과는 FALSE가 아니라 UNKNOWN → WHERE가 버린다 → 0건
```

- PostgreSQL 17 9.24.3: 같은 값이 없고 오른쪽에 NULL이 하나라도 있으면 `NOT IN`의 결과는 true가 아니라 null이다.
- 로컬 재현: `blacklist = {'lee', NULL}`일 때 `NOT IN`은 **0건**, `NOT EXISTS`는 **2건**(kim, park). MySQL 8.4.10도 `NOT IN`이 0건이었다.
- `WHERE NOT (customer = 'kim')`도 customer가 NULL인 행을 남기지 않는다. `NOT UNKNOWN = UNKNOWN`이다.

### 5. 집계 — 묶고, NULL은 건너뛴다

```text
  (예시, PostgreSQL 17.11) blacklist = {'lee', NULL}
  count(*) = 2        <- 행 수
  count(customer) = 1 <- NULL이 아닌 값 수

  모두 NULL인 열: sum = NULL, avg = NULL, count = 0
```

- `count(col)`·`sum`·`avg`·`max`·`min` 같은 대부분의 집계는 NULL 입력을 무시한다. `count(*)`는 행을 세고, PostgreSQL 17 `array_agg`·`json_agg`는 NULL도 결과에 넣는다(9.21). 빈 입력(또는 전부 NULL)의 `sum`은 0이 아니라 NULL이다. 합계를 0으로 보이려면 `COALESCE(sum(x), 0)`을 쓴다.
- 비집계 열 규칙
  - `SELECT customer, total FROM ord GROUP BY customer`
    - PostgreSQL 17: `42803 column "ord.total" must appear in the GROUP BY clause or be used in an aggregate function`.
    - MySQL 8.4: `ERROR 1055 (42000) … incompatible with sql_mode=only_full_group_by`. MySQL 8.4 기본 `sql_mode`에 `ONLY_FULL_GROUP_BY`가 들어 있다(로컬 재현 `SELECT @@sql_mode`).
  - `GROUP BY id`(PK)면 `customer`를 SELECT에 써도 된다. id가 customer를 함수적으로 결정하기 때문이다(03번 함수 종속). 두 제품 모두 허용했다(PostgreSQL 7.2.3, MySQL 14.19.3).

### 6. 조인 팬아웃 — 합계가 부푸는 구조

```text
  주문 1에 상세 3줄, 결제 2건 → ord ⋈ item ⋈ payment 에서 주문 1은 3 × 2 = 6행

  o.id  item.qty  pay.amount
  1     1         60
  1     1         40
  1     2         60
  1     2         40
  1     1         60
  1     1         40
  sum(qty)    = (1+2+1) × 2 = 8     (진짜 4)
  sum(amount) = (60+40) × 3 = 300   (진짜 100)
```

- 로컬 재현(예시, PostgreSQL 17.11): 위 쿼리가 `1 | 8 | 300`을 냈다. 주문 합계 `SUM(o.total)`을 상세와 조인한 뒤 구하자 150이어야 할 값이 350이었다.
- 원인은 "일 대 다" 조인이 **한 쪽 행을 여러 번** 복제하는 것이다. 다(多) 쪽이 둘이면 서로 곱해진다.

## 쓰이는 자료구조·알고리즘

- **조인 알고리즘**: 중첩 루프(인덱스로 짝 찾기), 해시 조인(작은 쪽으로 해시 테이블을 만들고 큰 쪽을 탐색), 정렬 병합 조인. 로컬 재현 계획에 `Hash Join`, `Hash Anti Join`이 나왔다. 상세는 [11-join-algorithms](../11-join-algorithms/2-summary.md). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)
- **해시 집계 / 정렬 집계**: `GROUP BY`는 키별 해시 버킷에 누적하거나, 정렬 후 인접한 같은 키를 모은다([41-sorting-and-aggregation](../41-sorting-and-aggregation/2-summary.md)).
- **안티 조인과 NULL**: `NOT EXISTS`는 안티 조인으로 바로 바뀐다(어느 조인 알고리즘인지는 계획이 정한다. 로컬 재현에서는 `Hash Anti Join`). `NOT IN`은 NULL 의미가 달라 로컬 재현에서 `hashed SubPlan` 필터로 남았다. 의미가 다르면 쓸 수 있는 알고리즘도 달라진다.
- **3치 논리 진리표**: 비교·논리 연산이 {TRUE, FALSE, UNKNOWN} 위에서 정의된다. 위 표가 그 전부다.

## 적용 — 풀어나가는 법

### 1. 조인 전에 "결과 한 행의 뜻(grain)"을 정한다

```text
  "결과 한 행 = 주문 1건"   → 주문보다 잘게 쪼개는 조인(상세·결제)은 먼저 집계해 주문 단위로 맞춘다
  "결과 한 행 = 상세 1줄"   → 주문 금액 같은 주문 단위 값은 합하지 않는다
```

```sql
-- 팬아웃 없는 주문별 수량·결제액: 다(多) 쪽을 먼저 주문 단위로 집계한 뒤 조인
SELECT o.id, i.qty, p.paid
FROM ord o
LEFT JOIN (SELECT order_id, sum(qty) AS qty FROM ord_item GROUP BY order_id) i ON i.order_id = o.id
LEFT JOIN (SELECT order_id, sum(amount) AS paid FROM payment GROUP BY order_id) p ON p.order_id = o.id;
-- (예시, PostgreSQL 17.11) 1 | 4 | 100,  2 | 5 | 50,  3 | NULL | NULL
```

- `SUM(DISTINCT amount)`로 때우지 않는다. 같은 금액 결제가 두 건이면 하나로 합쳐진다. 로컬 재현: 주문 2에 50원 결제 두 건 → `sum(DISTINCT)` 50, 진짜 100.
- "상세가 있는 주문의 합계"는 조인 대신 세미 조인으로 쓴다: `WHERE id IN (SELECT order_id FROM ord_item)` 또는 `EXISTS`(로컬 재현: 350 → 150).

### 2. 존재 여부는 `EXISTS` / `NOT EXISTS`

```sql
SELECT * FROM ord o
WHERE NOT EXISTS (SELECT 1 FROM blacklist b WHERE b.customer = o.customer);
-- NOT IN을 꼭 쓰려면 서브쿼리에서 NULL을 걸러 낸다
-- (ord.customer 쪽에도 NULL이 없어야 위 NOT EXISTS와 결과가 같다: 왼쪽이 NULL이면 NOT IN은 UNKNOWN)
SELECT * FROM ord WHERE customer NOT IN (SELECT customer FROM blacklist WHERE customer IS NOT NULL);
```

### 3. 외부 조인의 오른쪽 조건은 `ON`에

```sql
SELECT o.id, c.code
FROM ord o
LEFT JOIN coupon_use c ON c.order_id = o.id AND c.type = 'X';   -- 미사용 주문도 남는다
```

- "짝이 없는 것만"을 원할 때만 WHERE에 `c.order_id IS NULL`을 쓴다(안티 조인).

### 4. 검증 쿼리 — 조인이 행을 불렸나

```sql
SELECT count(*) AS rows, count(DISTINCT o.id) AS orders
FROM ord o JOIN ord_item i ON i.order_id = o.id;      -- rows > orders 이면 주문 단위 합계는 부푼다
```

```sql
-- 계획과 행 수: 조인 노드의 actual rows가 입력보다 크면 팬아웃
EXPLAIN (ANALYZE, BUFFERS) SELECT …;            -- PostgreSQL
EXPLAIN ANALYZE SELECT …;                       -- MySQL 8.4 (FORMAT=TREE)
```

- 문법 세부는 [sql/01](../../../languages/sql/syntax/01-logical-query-processing-order/2-summary.md) · [sql/04 NULL 3치 논리](../../../languages/sql/syntax/04-null-three-valued-logic/2-summary.md) · [sql/15 ON vs WHERE](../../../languages/sql/syntax/15-on-vs-where-in-outer-join/2-summary.md) · [sql/19 세미·안티 조인](../../../languages/sql/syntax/19-semi-anti-join/2-summary.md) · [sql/25 조인 팬아웃](../../../languages/sql/syntax/25-join-fan-out/2-summary.md).

## 장애 시나리오와 대처

### 1. 조인 팬아웃 → `SUM`이 부푼다 (⚠ 커리큘럼)

- **현상**: 대시보드 매출·결제액이 실제보다 몇 배 크다. 상세가 많은 주문일수록 심하다.
- **보이는 형태**: 에러 없음. 원장 합계와 불일치. 검증 쿼리에서 `count(*) > count(DISTINCT order_id)`.
- **원인**: 일 대 다 조인이 주문 행을 상세 수만큼 복제했다. 다 쪽이 둘이면 곱해진다(로컬 재현: 결제 100 → 300).
- **대처**: 결과 grain을 정하고, 다 쪽을 먼저 그 grain으로 집계한 뒤 조인한다. 존재 확인은 `EXISTS`. `SUM(DISTINCT)`는 쓰지 않는다.

### 2. `NOT IN (… NULL …)` → 빈 결과 (⚠ 커리큘럼)

- **현상**: "블랙리스트에 없는 고객" 발송 대상이 어느 날 0명이다.
- **보이는 형태**: 에러 없음. 로컬 재현: PostgreSQL 17.11·MySQL 8.4.10 모두 `NOT IN` 0건, `NOT EXISTS` 2건.
- **원인**: 서브쿼리 결과에 NULL이 한 줄 들어왔다(입력 누락, LEFT JOIN 결과 등). `x <> NULL`이 UNKNOWN이라 모든 행이 WHERE에서 버려진다.
- **대처**: `NOT EXISTS`로 바꾼다. 서브쿼리 열에 `NOT NULL` 제약을 둔다(02번).

### 3. `LEFT JOIN` + 오른쪽 열 `WHERE` → 행이 사라진다 (⚠ 커리큘럼)

- **현상**: "모든 주문과 쿠폰 사용 여부" 리포트에 쿠폰 안 쓴 주문이 없다.
- **보이는 형태**: 에러 없음. 행 수가 주문 수보다 적다. PostgreSQL 계획이 `Hash Left Join`이 아니라 `Hash Join`이다(로컬 재현).
- **원인**: WHERE는 조인 뒤에 적용된다. 짝 없는 행의 오른쪽 열은 NULL이라 `c.type = 'X'`가 UNKNOWN → 버려진다. 결과적으로 내부 조인이 된다.
- **대처**: 오른쪽 테이블 조건은 `ON`으로 옮긴다. 리뷰 때 "LEFT JOIN 뒤 WHERE에 오른쪽 테이블 열이 있나"를 본다.

### 4. MySQL 비집계 열 — 업그레이드 뒤 1055, 또는 임의 값

- **현상**: 옛 서버에서 돌던 리포트 쿼리가 MySQL 8.x 전환 뒤 실패한다. 또는 `ONLY_FULL_GROUP_BY`를 끈 서버에서 그룹마다 엉뚱한 이름이 나온다.
- **보이는 형태**: `ERROR 1055 (42000): Expression #2 of SELECT list is not in GROUP BY clause and contains nonaggregated column … incompatible with sql_mode=only_full_group_by`.
- **원인**: GROUP BY에 없고 함수적으로 결정되지도 않는 열을 SELECT에 썼다. 그룹 안에 값이 여러 개면 어느 값을 낼지 정해지지 않는다. MySQL은 이 모드가 꺼져 있으면 그중 아무 값을 고를 수 있다(MySQL 8.4 14.19.3).
- **대처**: 그 열을 GROUP BY에 넣거나, 집계(`MAX`)하거나, 정말 아무 값이나 괜찮으면 `ANY_VALUE()`로 의도를 드러낸다. 모드를 끄는 것은 틀린 숫자를 숨기는 일이다.

### 5. `count(col)`·`avg`가 NULL을 빼서 비율이 틀린다

- **현상**: "응답률 = count(answer) / count(*)"는 맞는데 "평균 점수"가 생각보다 높다.
- **보이는 형태**: 에러 없음. `avg(score)`가 미응답(NULL)을 분모에서 뺐다.
- **원인**: `avg`·`count(col)`은 NULL을 건너뛴다. 미응답을 0점으로 볼지 제외할지는 업무 결정인데 SQL 기본값이 대신 결정했다.
- **대처**: 의도를 식에 쓴다. 미응답을 0점으로 보려면 `avg(COALESCE(score, 0))`. `sum(score) / count(*)`는 대신 쓰지 않는다 — 전부 NULL인 그룹에서 NULL이 되고, PostgreSQL에서 `score`가 정수면 정수 나눗셈으로 소수가 잘린다(PostgreSQL 17 9.3, 정수 `/`는 0 쪽으로 자름). 리포트 정의서에 NULL 처리 규칙을 적는다.

## 핵심 문장

- SQL의 논리 처리 순서는 FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT다. 별칭·윈도 함수를 어디서 쓸 수 있는지가 여기서 정해진다.
- 조인은 짝이 맞는 모든 조합을 만든다. 일 대 다 조인은 한쪽 행을 복제하고, 다 쪽이 둘이면 곱해져 합계가 부푼다.
- 외부 조인에서 NULL에서 참이 될 수 없는 오른쪽 조건을 WHERE에 두면 NULL 행이 버려져 내부 조인이 된다. ON은 조인 전, WHERE는 조인 뒤다.
- NULL이 낀 비교는 UNKNOWN이고, WHERE는 TRUE만 남긴다. 그래서 NULL 하나가 `NOT IN`을 0건으로 만든다. 존재 여부는 `NOT EXISTS`로 쓴다.
- `sum`·`avg`·`count(col)` 등 대부분의 집계는 NULL을 건너뛴다(`count(*)`는 행을 센다). 빈 합계는 0이 아니라 NULL이다.

## 관련 주제·근거

- 선행: [01-relational-model-and-algebra](../01-relational-model-and-algebra/2-summary.md)
- 연결
  - [03-normalization](../03-normalization/2-summary.md) — 쪼갠 테이블, 함수 종속과 GROUP BY
  - [05-window-functions-and-cte](../05-window-functions-and-cte/2-summary.md) — 행을 접지 않는 집계
  - [02-keys-and-constraints](../02-keys-and-constraints/2-summary.md) — NOT NULL로 3치 논리 함정 줄이기
  - [11-join-algorithms](../11-join-algorithms/2-summary.md) · [12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md) · [41-sorting-and-aggregation](../41-sorting-and-aggregation/2-summary.md)
  - data-engineering `03-dimensional-modeling`(grain 선언, 팬아웃으로 합계 2배) — 미작성, [data-engineering/README](../../data-engineering/README.md)
- 문법 세부(languages/sql): [sql/01](../../../languages/sql/syntax/01-logical-query-processing-order/2-summary.md) · [sql/04](../../../languages/sql/syntax/04-null-three-valued-logic/2-summary.md) · [sql/15](../../../languages/sql/syntax/15-on-vs-where-in-outer-join/2-summary.md) · [sql/19](../../../languages/sql/syntax/19-semi-anti-join/2-summary.md) · [sql/25](../../../languages/sql/syntax/25-join-fan-out/2-summary.md)
- 교재: CMU 15-445 Fall 2024 Lecture #02 "Modern SQL" 노트 — SQL은 백 기반, 집계, GROUP BY·HAVING(HAVING에서 별칭 참조는 표준 아님), 중첩 쿼리(IN = ANY, EXISTS), LATERAL <https://15445.courses.cs.cmu.edu/fall2024/notes/02-modernsql.pdf>
- PostgreSQL 17
  - SELECT "Description"(처리 순서) <https://www.postgresql.org/docs/17/sql-select.html>
  - 7.2 Table Expressions — 7.2.1.1 조인 종류와 ON vs WHERE 예, 7.2.3 GROUP BY와 함수 종속 <https://www.postgresql.org/docs/17/queries-table-expressions.html>
  - 9.24 Subquery Expressions — 9.24.3 NOT IN과 NULL <https://www.postgresql.org/docs/17/functions-subquery.html>
- MySQL 8.4: 14.19.3 MySQL Handling of GROUP BY(`ONLY_FULL_GROUP_BY`, 함수 종속 감지, `ANY_VALUE`) <https://dev.mysql.com/doc/refman/8.4/en/group-by-handling.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): 팬아웃 합계(350 vs 150, 8/300 vs 4/100), 선집계 교정, `SUM(DISTINCT)` 오류, `NOT IN` 0건 vs `NOT EXISTS` 2건(두 제품), ON vs WHERE 결과와 계획(Hash Join으로 변환), 3치 논리 식 값, `count(*)`/`count(col)`, 전부 NULL의 sum/avg/count, 비집계 열 42803·1055와 PK 그룹 허용, 별칭·윈도 함수 WHERE 오류, `@@sql_mode` 기본값
