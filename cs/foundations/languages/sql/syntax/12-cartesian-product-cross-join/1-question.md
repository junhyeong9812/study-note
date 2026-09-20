# sql/12-카티션곱과 CROSS JOIN — 질문

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

### 1. 행 수 (예측)

```sql
SELECT COUNT(*) FROM emp CROSS JOIN dept;
```

- 결과는 몇인가?

### 2. `NULL` 도 짝지어지나 (경계)

- `dan` 의 `dept_id` 가 `NULL` 인데, 카티션곱 결과에 `dan` 의 행이 몇 개 들어 있는가?

### 3. 쉼표와 `CROSS JOIN` (왜)

```sql
-- (A)
SELECT COUNT(*) FROM emp, dept;
-- (B)
SELECT COUNT(*) FROM emp CROSS JOIN dept;
```

- 두 결과는 같은가, 그리고 그럼에도 (B)로 적는 이유는 무엇인가?

### 4. 조건을 하나 빠뜨리면 (예측)

```sql
SELECT COUNT(*) AS n FROM emp e, dept d, dept d2 WHERE e.dept_id = d.id;
```

- 결과는 몇인가?

### 5. `CROSS JOIN … ON` (예측)

```sql
SELECT e.name, d.name FROM emp e CROSS JOIN dept d ON e.dept_id = d.id;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 나오는가?

### 6. 뼈대 만들기 (연결)

- 「실적이 없는 부서·분기가 보고서에서 통째로 빠지는」 문제를 `CROSS JOIN` 으로 어떻게 고치는가?

### 7. `generate_series` (경계)

```sql
SELECT d.name, m FROM dept d CROSS JOIN generate_series(1,3) AS m;
```

- 이 질의는 두 엔진에서 다 도는가?

### 8. 조합 만들기 — `<` 와 `<>` (예측)

```sql
-- (A)
SELECT COUNT(*) FROM emp a CROSS JOIN emp b WHERE a.id < b.id;
-- (B)
SELECT COUNT(*) FROM emp a CROSS JOIN emp b WHERE a.id <> b.id;
```

- (A)와 (B)의 결과는 각각 몇이고, 왜 다른가?

### 9. 한 행짜리 표를 곱하면 (예측)

```sql
SELECT e.name, avg_t.avg_sal
FROM emp e CROSS JOIN (SELECT AVG(salary) AS avg_sal FROM emp) AS avg_t;
```

- 결과 행 수는 몇이고, `avg_sal` 값은 왜 그렇게 나오는가?

### 10. 카티션곱은 성능 경고인가 (왜)

- `FROM a, b WHERE a.k = b.k` 에서 엔진이 반드시 `|a| × |b|` 행을 만들어 보는가?

### 11. 12행이 무엇의 출발선인가 (연결)

- `INNER`·`LEFT`·`RIGHT`·`FULL OUTER` 네 형태를 이 12행 기준으로 한 줄씩 설명할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
