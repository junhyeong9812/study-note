# sql/11-서브쿼리 — 스칼라·상관·ANY/ALL — 질문

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

`dev` 부서의 사원은 `cho` 하나뿐이고 그 급여가 `NULL` 이라는 것이 여러 문항의 열쇠다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 스칼라 서브쿼리의 세 가지 결말 (예측)

```sql
-- (A)
SELECT name, (SELECT MAX(salary) FROM emp) AS top FROM emp;
-- (B)
SELECT (SELECT id FROM dept WHERE name = 'nope') AS zero_rows;
-- (C)
SELECT name, (SELECT id FROM dept) AS d FROM emp;
```

- 세 문장은 각각 무엇을 돌려주는가(값 · `NULL` · 에러 중)?

### 2. 열이 둘이면 (경계)

- `(SELECT id, name FROM dept WHERE id = 10)` 처럼 **열이 둘**인 스칼라 서브쿼리는 어떻게 되는가?

### 3. 그 에러는 언제 나는가 (왜)

- 「2행 이상」 에러와 「2열 이상」 에러 중 **하나만** 파싱 단계에서 잡히는 이유는 무엇인가?

### 4. 상관 서브쿼리의 결과 (예측)

```sql
SELECT e.name, (SELECT d.name FROM dept d WHERE d.id = e.dept_id) AS dept FROM emp e;
```

- 결과 행 수는 몇이고, `dan` 의 행은 어떻게 되는가?

### 5. 계획에서 상관을 알아보기 (연결)

- 같은 질의를 `EXPLAIN` 으로 찍었을 때, 서브쿼리가 **상관인지 아닌지**를 두 엔진의 계획에서 각각 어느 낱말로 구분하는가?

### 6. 한정자를 뺐을 때 (예측)

```sql
SELECT d.name, (SELECT COUNT(*) FROM emp e WHERE e.dept_id = id) AS n FROM dept d;
```

- 의도는 부서별 사원 수(`2, 1, 0`)였다. 실제 결과는 무엇이고 왜 그런가?

### 7. 바깥에서 안쪽 별칭 부르기 (경계)

- 서브쿼리 안에서 붙인 별칭(`SELECT 1 FROM dept d …` 의 `d`)을 바깥 `WHERE` 에서 쓰면 어떻게 되는가?

### 8. `ANY` 와 `ALL` (예측)

```sql
-- (A)
SELECT name FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 10);
-- (B)
SELECT name FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 10);
```

- 두 질의는 각각 누구를 돌려주는가?

### 9. 목록에 `NULL` 이 섞이면 (예측)

```sql
-- (A)
SELECT name FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 20);
-- (B)
SELECT name FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 20);
```

- 두 질의의 결과 행 수는 각각 몇이고, 그 사실이 무엇을 알려 주는가?

### 10. 목록이 비어 있으면 (예측)

```sql
-- (A)
SELECT name FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 99);
-- (B)
SELECT name FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 99);
```

- 두 질의의 결과 행 수는 각각 몇이고, 급여가 `NULL` 인 `cho` 는 어느 쪽에 들어가는가?

### 11. `IN` 과 `= ANY` (연결)

- `IN`·`NOT IN` 을 `ANY`/`ALL` 로 바꿔 쓰면 각각 무엇이 되는가?

### 12. `FROM` 안에서 바깥을 참조하면 (경계)

```sql
SELECT d.name, t.name
FROM dept d JOIN (SELECT e.name FROM emp e WHERE e.dept_id = d.id LIMIT 1) AS t ON true;
```

- 이 질의는 통과하는가? 같은 참조가 `SELECT` 칸에서는 왜 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
