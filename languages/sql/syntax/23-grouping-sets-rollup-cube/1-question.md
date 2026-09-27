# sql/23-`GROUPING SETS`·`ROLLUP`·`CUBE` 와 `GROUPING()` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다.\
★ **`dan` 의 `dept_id` 가 `NULL` 인 것이 이 주제에서 결정적이다.**

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ `ROLLUP` 이 무엇을 더 주나 (예측)

```sql
SELECT dept_id, SUM(salary) FROM emp GROUP BY ROLLUP(dept_id);
```

- 결과는 몇 행이고, `GROUP BY dept_id` 와 무엇이 다른가?

### 2. ★ `NULL` 이 둘인데 (왜)

- 1번 결과에서 `dept_id` 가 `NULL` 인 행이 둘이다. 둘은 각각 무슨 뜻이고 어떻게 구분하는가?

### 3. `COALESCE` 로 되나 (경계)

- `COALESCE(dept_id, '전체')` 로 총계 줄을 라벨링하면 무엇이 잘못되는가?

### 4. ★ 라벨 붙이기 (예측)

```sql
SELECT CASE WHEN dept_id IS NULL THEN '(no dept)'
            WHEN GROUPING(dept_id) = 1 THEN '(total)'
            ELSE CAST(dept_id AS CHAR(10)) END AS dept, SUM(salary)
FROM emp GROUP BY ROLLUP(dept_id);
```

- 이 `CASE` 의 결과는 무엇이 틀렸는가?

### 5. 셋의 관계 (연결)

- `ROLLUP(a,b)` · `CUBE(a,b)` · `GROUPING SETS (…)` 는 서로 어떤 관계인가?

### 6. ★ 구분이 불가능한 두 행 (예측)

```sql
SELECT dept_id, name, SUM(salary) FROM emp GROUP BY CUBE(dept_id, name);
```

- 이 결과에서 **보이는 값이 한 글자도 같은** 두 행이 나온다. 어느 행이고 왜 그런가?

### 7. 두 열을 접으면 (경계)

- `ROLLUP(dept_id, name)` 결과에서 `dept_id`·`name` 이 둘 다 `NULL` 인 행이 몇이고 각각 무슨 뜻인가?

### 8. `GROUPING()` 의 인자가 여럿이면 (예측)

- `GROUPING(dept_id, name)` 은 무엇을 돌려주고, `ROLLUP(dept_id, name)` 에서 어떤 값들이 나오는가?

### 9. `GROUPING()` 을 쓸 수 있는 절 (경계)

- `GROUPING()` 은 `SELECT`·`WHERE`·`HAVING`·`ORDER BY` 중 어디에서 쓸 수 있는가?

### 10. ★ MySQL 에서 어디까지 (예측)

```sql
-- (A)
SELECT dept_id, SUM(salary) FROM emp GROUP BY dept_id WITH ROLLUP;
-- (B)
SELECT dept_id, SUM(salary) FROM emp GROUP BY ROLLUP(dept_id);
-- (C)
SELECT dept_id, SUM(salary) FROM emp GROUP BY GROUPING SETS ((dept_id), ());
-- (D)
SELECT dept_id, SUM(salary) FROM emp GROUP BY CUBE(dept_id);
```

- 네 문은 PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 어떻게 되는가?

### 11. ★ 에러 번호가 다른 이유 (왜)

- 10번에서 MySQL 이 (C)와 (D)에 **다른 에러**를 낸다. 두 에러가 말하는 것은 어떻게 다른가?

### 12. `ROLLUP` 없이 `GROUPING()` (경계)

- `GROUP BY dept_id` 에 `GROUPING(dept_id)` 를 붙이면 두 엔진에서 각각 어떻게 되는가?

### 13. 이식하려면 (연결)

- 두 엔진에서 같이 도는 소계 문법은 무엇이고, MySQL 에서 `GROUPING SETS` 가 필요하면 무엇으로 대신하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
