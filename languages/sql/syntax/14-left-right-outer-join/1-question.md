# sql/14-LEFT·RIGHT OUTER JOIN — 질문

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

### 1. 되살아나는 행 (예측)

```sql
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id;
```

- 결과 행 수는 몇이고, `INNER JOIN` 과 비교해 어느 행이 더 있는가?

### 2. 몇 개의 열이 `NULL` 이 되나 (경계)

- `dan` 의 행에서 `dept` 쪽 열 중 몇 개가 `NULL` 인가?

### 3. `LEFT` 가 보장하는 것 (왜)

- 「`LEFT JOIN` 을 쓰면 결과 행 수가 왼쪽 행 수와 같다」는 맞는가?

### 4. `RIGHT` 와 뒤집기 (예측)

```sql
-- (A)
SELECT e.name, d.name FROM emp e LEFT  JOIN dept d ON e.dept_id = d.id;
-- (B)
SELECT e.name, d.name FROM dept d RIGHT JOIN emp e ON e.dept_id = d.id;
```

- (A)와 (B)의 결과는 같은가?

### 5. `RIGHT` 를 덜 쓰는 이유 (왜)

- 문법상 대칭인데도 실무에서 `RIGHT JOIN` 을 덜 쓰는 이유는 무엇인가?

### 6. 어느 `NULL` 인가 (연결)

- 「짝을 못 찾았다」를 판정할 때 `WHERE d.name IS NULL` 이 아니라 `WHERE d.id IS NULL` 을 써야 하는 이유는?

### 7. ★ `WHERE` 에 부등호 (예측)

```sql
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE d.id <> 10;
```

- 「10번 부서가 아닌 사원」을 뽑으려던 이 질의의 결과는 무엇이고, 왜 그런가?

### 8. ★ `WHERE` 에 등호 (예측)

```sql
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE d.name = 'sales';
```

- 결과 행 수는 몇이고, 그것이 어떤 조인의 결과와 같은 모양인가?

### 9. 7번을 고치려면 (연결)

- 7번에서 `dan` 을 살리려면 무엇을 더하는가?

### 10. 0건을 세기 (예측)

```sql
SELECT d.name, COUNT(*) AS star, COUNT(e.id) AS emp_cnt
FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name;
```

- `hr` 행의 `star` 와 `emp_cnt` 는 각각 얼마인가?

### 11. 방언 (경계)

- 이 주제에서 PostgreSQL 18.6 과 MySQL 8.4.10 의 출력이 다른 자리가 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
