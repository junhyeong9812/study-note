# database/04-sql-joins-and-aggregation — 정답

## 정답

### 1. 논리 처리 순서

- WITH → FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT 목록(윈도 함수 포함) → DISTINCT → 집합 연산 → ORDER BY → LIMIT/OFFSET(PostgreSQL 17 SELECT "Description").
- 별칭: WHERE는 SELECT 목록보다 먼저라 SELECT 별칭을 모른다. `WHERE c = 'kim'` → `column "c" does not exist`. ORDER BY는 뒤라 쓸 수 있다. PostgreSQL은 GROUP BY에서도 출력 열 이름을 허용한다.
- 윈도 함수: SELECT 단계에서 계산되므로 WHERE에 못 쓴다(`42P20`). 거르려면 서브쿼리·CTE로 감싼다(05번).
- 실제 실행은 다르다. 이 순서는 "결과가 같아야 한다"는 의미론이고, 옵티마이저는 WHERE를 조인 아래로 내리는 등 순서를 바꾼다.

### 2. 팬아웃 계산

- 주문 1은 3 × 2 = 6행이 된다. `sum(qty)` = (1+2+1) × 2 = **8**, `sum(amount)` = (60+40) × 3 = **300**(로컬 재현 그대로).
- 올바른 값: qty 4, 결제 100.

```sql
SELECT o.id, i.qty, p.paid
FROM ord o
LEFT JOIN (SELECT order_id, sum(qty) qty FROM ord_item GROUP BY order_id) i ON i.order_id = o.id
LEFT JOIN (SELECT order_id, sum(amount) paid FROM payment GROUP BY order_id) p ON p.order_id = o.id;
```

### 3. NOT IN vs NOT EXISTS

- `NOT IN` → **0건**. `NOT EXISTS` → **2건**(kim, park). PostgreSQL 17.11과 MySQL 8.4.10 모두 `NOT IN`이 0건이었다.
- kim의 경우: `kim NOT IN ('lee', NULL)` = `kim <> 'lee' AND kim <> NULL` = `TRUE AND UNKNOWN` = UNKNOWN. WHERE는 TRUE만 남기므로 버린다. lee는 `lee <> 'lee'`가 FALSE라 버린다.
- `NOT EXISTS`는 "`b.customer = o.customer`인 행이 있나"만 본다. NULL 행은 어떤 고객과도 같지 않으므로 kim·park에 짝이 없다 → 남는다.

### 4. ON vs WHERE

- ON에 조건: 1(60), 2(50), **3(NULL)** — 조건에 맞는 결제만 붙이고, 짝 없는 주문 3도 남긴다.
- WHERE에 조건: 1(60), 2(50) — 조인 뒤 `p.amount >= 50`이 주문 3의 NULL에서 UNKNOWN → 버려진다.
- PostgreSQL 17 7.2.1.1: ON 조건은 조인 전, WHERE 조건은 조인 뒤에 처리된다. 외부 조인에서만 차이가 난다.
- 흔적: WHERE 쪽 쿼리의 계획이 `Hash Left Join`이 아니라 `Hash Join`이었다(로컬 재현). 옵티마이저가 외부 조인을 내부 조인으로 바꿨다.

### 5. 집계와 NULL

| | NULL 처리 | 전부 NULL일 때 |
|---|---|---|
| `count(*)` | 행 수 (NULL도 셈) | 행 수 |
| `count(col)` | NULL 제외 | 0 |
| `sum(col)` | NULL 제외 | **NULL** |
| `avg(col)` | NULL 제외 (분모에서도) | NULL |

- 로컬 재현(예시, PostgreSQL 17.11): `{'lee', NULL}`에서 `count(*)` 2, `count(customer)` 1. 전부 NULL인 두 행에서 sum NULL, avg NULL, count 0.
- 합계를 0으로 보이려면 `COALESCE(sum(x), 0)`.

### 6. 비집계 열

- PostgreSQL 17: `ERROR 42803 column "ord.total" must appear in the GROUP BY clause or be used in an aggregate function`.
- MySQL 8.4: `ERROR 1055 (42000) … incompatible with sql_mode=only_full_group_by`. 8.4 기본 `sql_mode`에 `ONLY_FULL_GROUP_BY`가 있다.
- `GROUP BY id`면 허용된다. id가 PK라 `id → customer` 함수 종속이 있어 그룹마다 customer가 하나로 정해진다. 두 제품 모두 이를 감지한다(PostgreSQL 7.2.3, MySQL 14.19.3).

### 7. `SUM(DISTINCT)`가 틀린 이유

- 반례: 주문 2에 50원 결제가 두 건이면 진짜 합은 100인데 `sum(DISTINCT amount)`는 50이다(로컬 재현 그대로).
- DISTINCT는 "복제된 행"이 아니라 "같은 값"을 없앤다. 우연히 값이 같은 서로 다른 사실도 지운다.
- 올바른 방법
  1. 다 쪽을 먼저 주문 단위로 집계한 뒤 조인한다(2번 쿼리).
  2. 존재 확인이면 조인하지 말고 `EXISTS`·`IN` 세미 조인으로 거른다. 또는 `LATERAL` 서브쿼리로 주문마다 집계한다.

### 8. 발송 대상 0명

- 의심: `NOT IN` 서브쿼리 결과에 NULL이 들어왔다.
- 확인

```sql
SELECT count(*) FROM blacklist WHERE customer IS NULL;           -- 0보다 크면 원인
SELECT count(*) FROM member m
WHERE NOT EXISTS (SELECT 1 FROM blacklist b WHERE b.customer = m.customer);   -- 기대 건수와 비교
```

- 고치기: `NOT EXISTS`로 바꾼다. 블랙리스트 열에 `NOT NULL` 제약을 걸고, NULL이 들어온 적재 경로를 막는다.

### 9. 계획과 의미

- `NOT EXISTS` → 로컬 재현(PostgreSQL 17.11)에서 `Hash Anti Join`(짝이 없는 왼쪽 행만 내는 해시 조인).
- `NOT IN` → `Seq Scan … Filter: (NOT (ANY (customer = (hashed SubPlan 1).col1)))`. 서브쿼리 결과를 해시한 필터로 남았다.
- `NOT IN`은 오른쪽에 NULL이 있으면 UNKNOWN을 내야 하므로, NULL을 모르는 보통의 안티 조인과 의미가 다르다. 로컬 재현의 PostgreSQL 17.11은 이 쿼리를 안티 조인으로 바꾸지 않았다. 의미를 `NOT EXISTS`로 바로 쓰면 안티 조인 계열 전략(해시·병합·중첩 루프)을 쓸 수 있다.
