# sql/04-NULL 의 3값 논리 — 질문

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

### 1. 두 조건이 전체를 가르는가 (예측)

```sql
SELECT COUNT(*) FROM emp WHERE salary > 400;   -- (A)
SELECT COUNT(*) FROM emp WHERE salary <= 400;  -- (B)
```

- (A)와 (B)의 합이 `SELECT COUNT(*) FROM emp` 와 같은가?

### 2. `UNKNOWN` 은 언제 번지고 언제 안 번지나 (왜)

```sql
SELECT TRUE AND NULL, FALSE AND NULL, TRUE OR NULL, FALSE OR NULL, NOT NULL;
```

- 다섯 값을 순서대로 적을 수 있는가?

### 3. `<>` 가 `NULL` 행을 데려오는가 (예측)

```sql
SELECT id, name FROM emp WHERE salary <> 300;
```

- `cho`(salary NULL)는 이 결과에 들어오는가?

### 4. `NOT IN` 에 `NULL` 이 섞였을 때 (예측)

```sql
SELECT id, name FROM dept WHERE id NOT IN (SELECT dept_id FROM emp);
```

- 이 질의의 결과 행 수는 몇인가, 그리고 그 수가 나온 이유를 식으로 전개할 수 있는가?

### 5. 같은 의도를 `NOT EXISTS` 로 쓰면 (경계)

```sql
SELECT id, name FROM dept d
WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id);
```

- 4번과 결과가 달라지는가, 달라진다면 `EXISTS` 의 무엇이 안전하게 만드는가?

### 6. 집계 함수가 `NULL` 을 어떻게 다루나 (예측)

```sql
SELECT COUNT(*), COUNT(salary), SUM(salary), AVG(salary) FROM emp;
```

- 네 값을 적을 수 있는가, 그리고 `AVG` 의 분모는 무엇인가?

### 7. 전부 `NULL` 인 그룹의 합 (예측)

```sql
SELECT dept_id, COUNT(*), SUM(salary) FROM emp GROUP BY dept_id;
```

- `dept_id = 20` 그룹의 `SUM(salary)` 은 무엇인가?

### 8. 비교 규칙과 묶기 규칙 (경계)

- `NULL = NULL` 은 참이 아닌데 `GROUP BY dept_id` 는 왜 `dept_id NULL` 인 행들을 한 그룹으로 묶는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
