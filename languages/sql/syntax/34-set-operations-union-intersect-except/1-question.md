# sql/34-집합 연산 — `UNION`·`INTERSECT`·`EXCEPT` 와 `ALL` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다. **새로 만드는 표는 없다.**

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

`ann` 과 `bob` 의 `dept_id` 가 **둘 다 10** 이라는 것과 `dan` 의 `dept_id` 가 **`NULL`** 이라는 것이 여러 문항의 열쇠다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 셋의 행 수 (예측)

```sql
-- (A) SELECT dept_id FROM emp UNION     SELECT id FROM dept;
-- (B) SELECT dept_id FROM emp INTERSECT SELECT id FROM dept;
-- (C) SELECT dept_id FROM emp EXCEPT    SELECT id FROM dept;
-- (D) SELECT id FROM dept EXCEPT        SELECT dept_id FROM emp;
```

- 네 질의의 결과 행 수와 값은 각각 무엇인가?

### 2. `ALL` 을 붙이면 (예측)

```sql
-- (A) SELECT dept_id FROM emp UNION ALL     SELECT id      FROM dept;
-- (B) SELECT dept_id FROM emp EXCEPT ALL    SELECT id      FROM dept;
-- (C) SELECT dept_id FROM emp INTERSECT ALL SELECT dept_id FROM emp;
```

- 세 질의는 각각 몇 행이고, `ALL` 이 붙으면 무엇을 세는 연산이 되는가?

### 3. `UNION` 이 접는 것 (예측)

```sql
-- (A)
SELECT dept_id FROM emp WHERE dept_id = 10 UNION     SELECT dept_id FROM emp WHERE dept_id = 10;
-- (B)
SELECT dept_id FROM emp WHERE dept_id = 10 UNION ALL SELECT dept_id FROM emp WHERE dept_id = 10;
```

- 두 질의의 행 수는 각각 몇이고, 그 차이가 알려 주는 **`UNION` 의 성질**은 무엇인가?

### 4. 16번이 당한 함정 (연결)

```sql
SELECT e.dept_id AS e_dept, d.id AS d_id FROM emp e LEFT  JOIN dept d ON e.dept_id = d.id
UNION
SELECT e.dept_id,           d.id        FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id;
```

- 이 질의는 몇 행인가? 같은 질의를 `name` 열로 바꿔 뽑으면 왜 행 수가 달라지는가?

### 5. 열 개수가 다르면 (경계)

- `SELECT id, name FROM emp UNION SELECT id FROM dept` 는 두 엔진에서 각각 무엇이라고 하는가?

### 6. 타입이 다르면 (예측)

```sql
SELECT id FROM emp UNION SELECT name FROM dept;
```

- 두 엔진은 각각 무엇을 돌려주는가? **한쪽이 통과한다면 결과 열의 타입은 무엇이 되는가?**

### 7. 중복 제거의 값 (왜)

- `UNION` 과 `UNION ALL` 의 실행 계획은 어느 낱말로 갈리는가? 두 엔진에서 각각.

### 8. `ORDER BY` 의 자리 (경계)

```sql
-- (A) SELECT name FROM emp ORDER BY name UNION SELECT name FROM dept;
-- (B) SELECT name FROM emp UNION SELECT name FROM dept ORDER BY name;
-- (C) SELECT name AS a FROM emp UNION SELECT name AS b FROM dept ORDER BY b;
```

- 셋 중 통과하는 것은 무엇이고, 실패하는 것들은 각각 왜 실패하는가?

### 9. 결과 열의 이름 (예측)

- `SELECT id AS first_name FROM dept UNION ALL SELECT id AS second_name FROM emp` 의 결과 열 이름은 무엇인가?

### 10. `NULL` 은 합쳐지나 (예측)

- `SELECT NULL INTERSECT SELECT NULL` 은 몇 행인가? 그 답이 `WHERE` 의 `NULL = NULL` 과 어떻게 어긋나는가?

### 11. 우선순위 (예측)

```sql
-- (A) SELECT 1 AS v UNION SELECT 2 INTERSECT SELECT 2;
-- (B) (SELECT 1 AS v UNION SELECT 2) INTERSECT SELECT 2;
```

- 두 질의의 결과는 각각 무엇이고, 그 차이가 알려 주는 우선순위는?

### 12. 버전 (연결)

- MySQL 에서 `INTERSECT`/`EXCEPT` 는 어느 버전부터 쓸 수 있고, 그 근거는 매뉴얼인가 릴리스 노트인가?

### 13. 없는 낱말 (경계)

- `MINUS` 와 `CORRESPONDING` 을 두 엔진에 던지면 각각 무엇이 나오는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
