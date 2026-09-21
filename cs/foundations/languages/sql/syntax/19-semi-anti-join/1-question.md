# sql/19-세미·안티 조인 — EXISTS·IN·NOT IN·NOT EXISTS — 질문

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
|  3 | cho  |      20 |   NULL |    | 30 | hr    |  <- 사원이 없는 부서
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
        ^
        +-- dan 의 dept_id 가 NULL 이다
```

```text
 emp.dept_id 를 목록으로 만들면   (10, 10, 20, NULL)    <- NULL 이 있다
 dept.id   를 목록으로 만들면     (10, 20, 30)          <- PRIMARY KEY 라 NULL 이 없다
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세미 조인의 세 표기 (예측)

```sql
-- (A)
SELECT d.id, d.name FROM dept d WHERE d.id IN (SELECT e.dept_id FROM emp e);
-- (B)
SELECT d.id, d.name FROM dept d WHERE EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id);
-- (C)
SELECT d.id, d.name FROM dept d JOIN emp e ON e.dept_id = d.id;
```

- 세 질의의 결과 행 수는 각각 몇인가?

### 2. `EXISTS` 의 `SELECT` 목록 (예측)

```sql
SELECT d.id FROM dept d WHERE EXISTS (SELECT 1/0 FROM emp e WHERE e.dept_id = d.id);
```

- 0 으로 나누는 식이 있는데 이 질의는 터지는가?

### 3. 안티 조인의 세 표기 (예측)

```sql
-- (A)
SELECT d.id, d.name FROM dept d WHERE d.id NOT IN (SELECT e.dept_id FROM emp e);
-- (B)
SELECT d.id, d.name FROM dept d WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id);
-- (C)
SELECT d.id, d.name FROM dept d LEFT JOIN emp e ON e.dept_id = d.id WHERE e.id IS NULL;
```

- 세 질의의 결과는 각각 무엇인가?

### 4. `NOT IN` 이 비는 이유 (왜)

```sql
SELECT 30 IN (10,20,NULL) AS in_res, 30 NOT IN (10,20,NULL) AS notin_res, 10 IN (10,20,NULL) AS hit;
```

- 세 칸의 값은 각각 무엇이고, `NOT IN` 이 `TRUE` 가 될 수 없는 계산 과정을 쓸 수 있는가?

### 5. `IN` 은 왜 멀쩡한가 (왜)

- 같은 목록에서 `IN` 은 제대로 동작하는데 `NOT IN` 만 무너지는 이유는 무엇인가?

### 6. 목록이 깨끗하면 안전한가 (예측)

```sql
SELECT e.name FROM emp e WHERE e.dept_id NOT IN (SELECT d.id FROM dept d);
```

- `dept.id` 는 기본키라 `NULL` 이 없다. 이 질의는 「부서가 없는 사원」(`dan`)을 제대로 찾는가?

### 7. `NOT EXISTS` 가 안전한 이유 (왜)

- `NOT EXISTS` 에서는 `NULL` 이 어디서 처리되기에 바깥까지 영향을 안 주는가?

### 8. `IS NULL` 을 걸 열 고르기 (예측)

```sql
SELECT d.id, d.name FROM dept d LEFT JOIN emp e ON e.dept_id = d.id WHERE e.salary IS NULL;
```

- `e.id IS NULL` 대신 `e.salary IS NULL` 로 쓰면 결과가 어떻게 되는가?

### 9. `IN` 과 `EXISTS` 의 계획 (예측)

- 1번의 (A) 와 (B) 를 `EXPLAIN` 으로 찍으면 두 엔진에서 각각 계획이 같은가, 다른가?

### 10. `JOIN + DISTINCT` 의 계획 (연결)

- `SELECT DISTINCT … JOIN …` 의 계획은 (A)·(B) 와 어디가 다른가?

### 11. `NOT EXISTS` 와 `NOT IN` 의 계획 (예측)

- 3번의 (A) 와 (B) 를 `EXPLAIN` 으로 찍으면 두 엔진이 각각 어떤 연산자를 쓰는가?

### 12. `NOT IN` 이 그 연산자를 못 쓰는 이유 (왜)

- 옵티마이저가 `NOT IN` 을 안티 조인으로 바꾸지 못하는 이유를 「느려서」가 아닌 말로 설명할 수 있는가?

### 13. `LEFT JOIN … IS NULL` 의 계획 (경계)

- 3번의 (C) 를 `EXPLAIN` 으로 찍으면 두 엔진의 계획이 같은가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
