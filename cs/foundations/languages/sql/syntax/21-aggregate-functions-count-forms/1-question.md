# sql/21-집계 함수와 `COUNT` 의 세 형태 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다.

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

### 1. ★ `COUNT` 세 형태 (예측)

```sql
-- (A)
SELECT COUNT(*), COUNT(dept_id), COUNT(DISTINCT dept_id) FROM emp;
-- (B)
SELECT COUNT(*), COUNT(salary), COUNT(DISTINCT salary) FROM emp;
```

- (A)와 (B)의 세 값은 각각 얼마이고, 왜 (B)에서는 뒤의 둘이 같아지는가?

### 2. `NULL` 은 한 가지인가 (왜)

- `COUNT(DISTINCT dept_id)` 가 3이 아니라 2인 이유를 「체 두 개」의 순서로 설명하면?

### 3. `COUNT(1)` 과 `COUNT(NULL)` (경계)

- `COUNT(*)` · `COUNT(1)` · `COUNT('x')` · `COUNT(NULL)` 은 `emp` 에서 각각 얼마인가?

### 4. ★ `AVG` 의 분모 (예측)

```sql
SELECT COUNT(*), COUNT(salary), SUM(salary), AVG(salary) FROM emp;
```

- `AVG(salary)` 는 얼마이고, 그 값은 무엇을 무엇으로 나눈 것인가?

### 5. ★ 0행에 대한 집계 (예측)

```sql
SELECT COUNT(*), SUM(salary), AVG(salary), MIN(salary), MAX(salary) FROM emp WHERE 1 = 0;
```

- 다섯 값은 각각 얼마이고, `COUNT` 가 0인데 `SUM` 이 `NULL` 인 것은 모순인가?

### 6. `GROUP BY` 를 붙이면 (경계)

- 5번 질의에 `GROUP BY dept_id` 를 붙이면 결과가 몇 행이 되고, 왜 그런가?

### 7. ★ `hr` 과 `dev` 를 가르기 (예측)

```sql
SELECT d.name, COUNT(*) AS star, COUNT(e.id) AS emp_cnt, COUNT(e.salary) AS sal_cnt
FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name;
```

- `dev` 행과 `hr` 행의 세 값은 각각 얼마이고, 두 행의 의미는 어떻게 다른가?

### 8. 무엇을 세야 「사원 수」인가 (왜)

- 외부 조인 뒤에 「사원 수」를 세려면 어느 열을 세야 하고, 그 열이 만족해야 할 조건은 무엇인가?

### 9. 합계를 0으로 보이려면 (연결)

- `hr` 의 `SUM(e.salary)` 가 `NULL` 인데 이것을 0으로 보이려면 무엇을 쓰는가?

### 10. 집계 안의 집계 (예측)

```sql
SELECT AVG(COUNT(*)) FROM emp GROUP BY dept_id;
```

- 이 문은 도는가? 안 돈다면 두 엔진이 각각 뭐라고 하고, 고치려면 어떻게 쓰는가?

### 11. ★ 방언 — 여러 열의 조합 세기 (예측)

```sql
-- (A)
SELECT COUNT(DISTINCT dept_id, salary) FROM emp;
-- (B)
SELECT COUNT(DISTINCT (dept_id, salary)) FROM emp;
```

- (A)와 (B)는 PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 어떻게 되는가?

### 12. 이식 가능한 형태 (연결)

- 11번을 두 엔진에서 같은 답이 나오게 쓰려면 어떤 형태로 바꾸는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
