# sql/03-WHERE 와 HAVING 의 차이 — 질문

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

### 1. 두 절의 자리 (왜)

- `WHERE` 와 `HAVING` 사이에 어느 절이 끼어 있고, 그것이 두 절의 판정 대상을 어떻게 바꾸는가?

### 2. 같은 조건을 옮겼을 때 (예측)

```sql
-- (A)
SELECT dept_id, COUNT(*) AS cnt FROM emp WHERE salary >= 400 GROUP BY dept_id;
-- (B)
SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING MAX(salary) >= 400;
```

- 두 질의의 결과 행과 `dept_id=10` 의 `cnt` 를 각각 적을 수 있는가?

### 3. `dev` 부서는 어디로 갔나 (연결)

- 2번의 (B)에서 `dept_id=20`(`cho`) 이 결과에 없는 이유는 무엇인가?

### 4. 그룹 키에 건 조건 (경계)

```sql
-- (A)
SELECT dept_id, SUM(salary) AS s FROM emp WHERE dept_id = 10 GROUP BY dept_id;
-- (B)
SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY dept_id HAVING dept_id = 10;
```

- 두 질의의 결과는 같은가, 그리고 왜 이 경우에만 같은가?

### 5. 그 둘의 실행 계획 (예측)

- 4번의 (A)와 (B)를 `EXPLAIN ANALYZE` 에 걸면 PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 다른가?

### 6. 집계 함수를 `WHERE` 에 (예측)

```sql
SELECT dept_id FROM emp WHERE COUNT(*) > 1 GROUP BY dept_id;
```

- 이 질의는 무엇을 돌려주는가?

### 7. `HAVING` 에 비집계 열 (예측)

```sql
SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING salary >= 400;
```

- 두 엔진이 각각 무엇을 말하는가, 그리고 두 메시지가 왜 다른가?

### 8. `HAVING` 의 열 별칭 (경계)

```sql
SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 2;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 나오고, 이식성 있는 형태는 무엇인가?

### 9. `GROUP BY` 없는 `HAVING` (예측)

```sql
SELECT COUNT(*) AS cnt FROM emp HAVING COUNT(*) > 100;
```

- 이 질의의 결과 행 수는 몇인가?

### 10. 사원이 없는 부서 찾기 (경계)

```sql
SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING COUNT(*) = 0;
```

- 이 질의로 「사원이 없는 부서」를 찾을 수 있는가?

### 11. 어느 절에 적을지 고르는 기준 (왜)

- 조건 하나를 손에 들었을 때, `WHERE` 와 `HAVING` 중 어디에 적을지 한 문장으로 판정하는 기준은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
