# sql/16-FULL OUTER JOIN — 질문

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

### 1. 네 형태의 행 수 (예측)

```sql
FROM emp e <조인> dept d ON e.dept_id = d.id
```

- `INNER` · `LEFT` · `RIGHT` · `FULL OUTER` 네 형태의 결과 행 수를 각각 적을 수 있는가?

### 2. 방언 (경계)

```sql
SELECT e.name, d.name FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id;
```

- 이 문을 PostgreSQL 18.6 과 MySQL 8.4.10 에 각각 던지면 무엇이 오는가?

### 3. 어느 `NULL` 인가 (왜)

```sql
SELECT e.dept_id AS e_dept, d.id AS d_id
FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id;
```

- 결과에 `(NULL, NULL)` 인 행이 나오는데, 그 두 `NULL` 은 각각 어디서 온 것인가?

### 4. 짝 없는 행만 뽑기 (경계)

- 「어느 한쪽에만 있는 행」을 고를 때 `WHERE d.name IS NULL` 이 아니라 `WHERE d.id IS NULL` 을 써야 하는 이유는?

### 5. MySQL 우회 — `UNION` 으로 충분한가 (예측)

```sql
SELECT e.dept_id, d.id FROM emp e LEFT  JOIN dept d ON e.dept_id = d.id
UNION
SELECT e.dept_id, d.id FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id;
```

- 이 질의의 결과 행 수는 PG 의 `FULL OUTER JOIN` 과 같은가?

### 6. 올바른 우회 (연결)

- 5번을 고쳐 PG 의 `FULL OUTER JOIN` 과 정확히 같은 결과를 내려면 무엇을 바꾸는가?

### 7. `WHERE` 를 붙이면 (예측)

```sql
SELECT e.name, d.name FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id
WHERE d.name = 'sales';
```

- 이 질의의 결과 행 수는 몇이고, 그것이 어떤 조인의 결과와 같은 모양인가?

### 8. PG 의 제약 (경계)

```sql
SELECT e.name, d.name FROM emp e FULL OUTER JOIN dept d ON e.dept_id > d.id;
```

- PostgreSQL 18.6 이 이 질의를 받아들이는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
