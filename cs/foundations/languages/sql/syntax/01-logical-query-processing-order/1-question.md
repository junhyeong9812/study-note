# sql/01-논리적 질의 처리 순서 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 네 주제가 공유한다.

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

### 1. 여덟 칸의 순서 (왜)

- `SELECT` 를 맨 위에 적는데 엔진은 왜 다섯 번째에 처리하는가?

### 2. 별칭이 `WHERE` 에서 안 되는 이유 (왜)

```sql
SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
```

- 이 질의가 에러인 이유를 처리 순서 한 문장으로 설명할 수 있는가?

### 3. 같은 별칭을 `ORDER BY` 로 옮기면 (예측)

```sql
SELECT salary * 12 AS annual FROM emp ORDER BY annual;
```

- 이 질의는 통과하는가, 통과한다면 네 행이 어떤 순서로 나오는가?

### 4. 별칭이 열 이름을 가릴 때 (예측)

```sql
SELECT id AS salary FROM emp WHERE salary > 400;
```

- 이 질의의 결과 행 수와 출력 값은 무엇인가?

### 5. 같은 조건을 `WHERE` 에 둘 때와 `HAVING` 에 둘 때 (예측)

```sql
-- (A)
SELECT dept_id, COUNT(*) AS cnt FROM emp WHERE salary >= 400 GROUP BY dept_id;
-- (B)
SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING MAX(salary) >= 400;
```

- `dept_id = 10` 인 행의 `cnt` 는 (A)와 (B)에서 각각 얼마인가?

### 6. `DISTINCT` 와 `ORDER BY` 의 앞뒤 (경계)

```sql
SELECT DISTINCT dept_id FROM emp ORDER BY salary;
```

- 이 질의가 거부되는 것이 여덟 칸 중 어느 두 칸의 순서를 증명하는가?

### 7. `HAVING` 의 별칭 — 방언 (연결)

```sql
SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 1;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 나오는가?

### 8. `LIMIT` 이 일을 줄여 주는가 (경계)

```sql
SELECT dept_id, COUNT(*) AS cnt FROM emp
GROUP BY dept_id ORDER BY cnt DESC LIMIT 1;
```

- `LIMIT 1` 을 붙였으니 엔진이 한 행만 만들고 멈출 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
