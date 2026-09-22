# sql/32-CTE(`WITH`) — 이름 붙인 서브질의와 가시성 — 질문

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

`emp` 에는 기본키 인덱스 `emp_pkey` 가 있다 — **계획에 `Index Scan` 이 뜨나 안 뜨나**가 여러 문항의 열쇠다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. CTE 와 파생 테이블의 결과 (예측)

```sql
-- (A)
WITH big AS (SELECT id, name, salary FROM emp WHERE salary >= 400)
SELECT a.name AS x, b.name AS y FROM big a JOIN big b ON a.id < b.id;
-- (B)
SELECT a.name AS x, b.name AS y
FROM (SELECT id, name, salary FROM emp WHERE salary >= 400) a
JOIN (SELECT id, name, salary FROM emp WHERE salary >= 400) b ON a.id < b.id;
```

- 두 질의의 **결과**는 같은가, 다른가? 그리고 **무엇이 달라졌는가**?

### 2. 파생 테이블로는 못 하는 것 (왜)

- 서브질의에 **이름을 붙였을 때만** 가능해지는 것은 무엇인가?

### 3. CTE 끼리 서로 보기 (예측)

```sql
-- (A)
WITH a AS (SELECT id FROM dept), b AS (SELECT id + 1 AS id FROM a) SELECT * FROM b;
-- (B)
WITH a AS (SELECT id FROM b), b AS (SELECT id FROM dept) SELECT * FROM a;
```

- 두 질의는 각각 통과하는가? 실패하는 쪽은 두 엔진이 **각각 무엇이라고 말하는가**?

### 4. 이름의 수명 (경계)

```sql
WITH t AS (SELECT id FROM dept) SELECT 1;
SELECT * FROM t;
```

- 두 번째 문장은 어떻게 되는가? CTE 는 어디에 저장되는가?

### 5. 이름이 겹치면 (예측)

```sql
WITH emp AS (SELECT 99 AS id, 'ghost' AS name) SELECT * FROM emp;
```

- 실제 `emp` 표가 있는데 같은 이름의 CTE 를 만들면 무엇이 나오는가? **에러인가?**

### 6. 최적화 장벽이 서나 (예측)

```sql
-- (A)
EXPLAIN (COSTS OFF) WITH c AS (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
-- (B)
EXPLAIN (COSTS OFF) WITH c AS MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
```

- PostgreSQL 18.6 에서 두 계획은 같은가 다른가? 다르다면 **어느 낱말로** 구분하는가?

### 7. "CTE 는 최적화 장벽이다"는 언제부터 틀렸나 (연결)

- 이 문장이 참이었던 PostgreSQL 버전과 거짓이 된 버전의 경계는 어디이고, **무엇이 바뀌었는가**?

### 8. 참조를 하나 더 늘리면 (예측)

```sql
EXPLAIN (COSTS OFF) WITH c AS (SELECT * FROM emp)
SELECT a.name, b.name FROM c a JOIN c b ON a.id < b.id;
```

- PG 18.6 과 MySQL 8.4.10 의 계획에서 **CTE 라는 이름이 남아 있는 쪽은 어디인가**?

### 9. `MATERIALIZED` 를 MySQL 에 (경계)

- MySQL 8.4.10 에 `WITH c AS MATERIALIZED (...)` 를 던지면 무엇이 나오는가? MySQL 쪽의 대체 수단은 무엇인가?

### 10. `NOT MATERIALIZED` 가 안 먹는 경우 (예측)

```sql
EXPLAIN (COSTS OFF) WITH c AS NOT MATERIALIZED (SELECT random() AS r FROM emp) SELECT * FROM c;
```

- 이 계획에 `CTE Scan` 이 뜨는가 안 뜨는가? 그 이유는 성능인가 정확성인가?

### 11. 열 이름 다시 붙이기 (경계)

- `WITH d(k, v) AS (SELECT id, name FROM dept)` 의 `(k, v)` 는 무엇을 하는가? 두 엔진에서 같은가?

### 12. 계획을 근거로 써도 되나 (왜)

- 이 주제의 `EXPLAIN` 출력들은 **보장**인가 **관찰**인가? 무엇을 외우고 무엇을 외우면 안 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
