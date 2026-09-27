# sql/10-FROM 절 — 테이블 별칭·파생 테이블 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다. **두 표가 `id` 와 `name` 을 둘 다 갖고 있다**는 점이 이 주제에서 쓰인다.

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

### 1. 별칭을 붙인 뒤 원래 이름 (예측)

```sql
SELECT emp.id, emp.name FROM emp e WHERE emp.salary >= 400;
```

- 이 질의는 통과하는가?

### 2. 테이블 별칭과 열 별칭의 유효 범위 (왜)

- `WHERE e.salary >= 400` 은 되는데 `WHERE annual > 4000` 은 안 되는 이유를 처리 순서 한 문장으로 설명할 수 있는가?

### 3. 열 별칭을 `WHERE` 에서 쓰는 방법 (연결)

- 「`WHERE` 에서 열 별칭을 못 쓴다」를 파생 테이블로 어떻게 푸는가?

### 4. 별칭 없는 파생 테이블 (예측)

```sql
SELECT * FROM (SELECT id, name FROM emp WHERE salary >= 400) ORDER BY id;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 나오는가?

### 5. 파생 테이블 안에서 바깥 행 참조 (예측)

```sql
SELECT * FROM emp e, (SELECT * FROM dept WHERE id = e.dept_id) AS d;
```

- 이 질의는 통과하는가, 통과하지 않는다면 PostgreSQL 이 무엇을 알려 주는가?

### 6. 파생 테이블 안의 별칭 (경계)

```sql
SELECT e1.name FROM (SELECT * FROM (SELECT * FROM emp) AS e1) AS e2;
```

- `e1` 을 바깥에서 부를 수 있는가?

### 7. `VALUES` 리스트 (예측)

```sql
-- (A)
SELECT * FROM (VALUES (1,'x'),(2,'y')) AS v(a,b);
-- (B)
SELECT * FROM (VALUES ROW(1,'x'),ROW(2,'y')) AS v(a,b);
```

- (A)와 (B)는 어느 엔진에서 각각 도는가?

### 8. 이름이 겹칠 때 (예측)

```sql
SELECT id FROM emp e JOIN dept d ON e.dept_id = d.id;
```

- 이 질의의 결과는 무엇인가?

### 9. 열 이름까지 새로 붙이기 (경계)

```sql
SELECT * FROM (SELECT id, name FROM emp WHERE salary >= 400) AS t(eid, ename) ORDER BY eid;
```

- 이 형태는 두 엔진에서 다 도는가?

### 10. 파생 테이블은 최적화 장벽인가 (예측)

```sql
EXPLAIN SELECT t.name FROM (SELECT * FROM emp WHERE salary >= 400) AS t WHERE t.id = 2;
```

- PostgreSQL 18.6 의 계획에 `Subquery Scan` 노드가 뜨는가?

### 11. 파생 테이블과 CTE 의 갈림 (연결)

- 같은 중간 결과를 두 번 참조해야 할 때 파생 테이블 대신 무엇을 쓰고, 그 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
