# sql/26-윈도우 함수의 개념 — 집계와 무엇이 다른가 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 데이터는 26~31 여섯 주제가 공유한다. **표는 `emp`·`dept` 그대로**이고, 행이 모자라는 만큼만 CTE 로 얹는다.

```sql
WITH emp8 AS (
  SELECT id, name, dept_id, salary FROM emp
  UNION ALL SELECT 5, 'eve', 10, 300
  UNION ALL SELECT 6, 'fay', 10, 500
  UNION ALL SELECT 7, 'gus', 20, 400
  UNION ALL SELECT 8, 'hui', 20, 400
)
```

```text
emp8                                dept
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |  <- 사원이 없는 부서
|  4 | dan  |    NULL |    400 |    +----+-------+
|  5 | eve  |      10 |    300 |
|  6 | fay  |      10 |    500 |
|  7 | gus  |      20 |    400 |
|  8 | hui  |      20 |    400 |
+----+------+---------+--------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 접느냐 안 접느냐 (예측)

```sql
-- (A)
SELECT AVG(salary) FROM emp8;
-- (B)
SELECT name, salary, AVG(salary) OVER () FROM emp8;
```

- (A)와 (B)는 각각 몇 행을 돌려주고, `AVG` 의 값은 서로 같은가?

### 2. 빈 괄호의 뜻 (왜)

- `OVER ()` 의 빈 괄호는 「무엇을 안 적었다」는 뜻이고, 그래서 창은 무엇이 되는가?

### 3. ★ `GROUP BY` 로는 왜 못 쓰나 (왜)

- `salary - AVG(salary) OVER ()` 와 같은 열을 `GROUP BY` + 집계로 만들 수 없는 이유는 무엇인가?

### 4. `cho` 의 편차 (경계)

- `salary - AVG(salary) OVER ()` 가 `cho` 행에서 어떤 값이 되고, 그 값은 「평균과 같다」는 뜻인가?

### 5. ★ `GROUP BY` 와 같이 쓰면 (예측)

```sql
SELECT dept_id, COUNT(*) AS c, SUM(COUNT(*)) OVER () AS total_rows, COUNT(*) OVER () AS group_cnt
FROM emp8 GROUP BY dept_id;
```

- `total_rows` 와 `group_cnt` 는 각각 얼마이고, 왜 둘이 다른가?

### 6. ★ 중첩 규칙 (예측)

```sql
-- (A)
SELECT SUM(COUNT(*)) OVER () FROM emp8 GROUP BY dept_id;
-- (B)
SELECT SUM(ROW_NUMBER() OVER ()) FROM emp8;
-- (C)
SELECT SUM(SUM(salary) OVER ()) OVER () FROM emp8;
```

- 셋 중 도는 것은 무엇이고, 안 도는 것은 두 엔진이 각각 뭐라고 하는가?

### 7. 창에 섞인 빈 행 (예측)

```sql
SELECT d.name AS dept, COUNT(*) OVER (PARTITION BY d.id) AS star,
       COUNT(e.id) OVER (PARTITION BY d.id) AS emp_cnt
FROM dept d LEFT JOIN emp8 e ON e.dept_id = d.id;
```

- `hr` 행의 `star` 와 `emp_cnt` 는 각각 얼마이고, 두 값이 다른 이유는 무엇인가?

### 8. 무엇을 세야 인원수인가 (연결)

- 외부 조인 뒤의 창에서 「사원 수」를 세려면 어느 열을 세고, 그 열이 만족해야 할 조건은 무엇인가?

### 9. 어디에 쓸 수 있나 (경계)

- 윈도우 함수를 쓸 수 있는 절은 어디어디이고, 쓸 수 없는 절은 어디인가?

### 10. ★ 방언 — `FILTER` 와 `OVER` (예측)

```sql
SELECT name, salary, SUM(salary) FILTER (WHERE salary > 300) OVER () AS s FROM emp8;
```

- 이 문은 PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 어떻게 되는가?

### 11. 도입 버전 (경계)

- 윈도우 함수는 PostgreSQL 과 MySQL 에서 각각 어느 버전부터 쓸 수 있는가?

### 12. 그래도 `GROUP BY` 를 쓰는 자리 (왜)

- 윈도우로 다 되는데도 `GROUP BY` 를 써야 하는 요구는 어떤 모양인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
