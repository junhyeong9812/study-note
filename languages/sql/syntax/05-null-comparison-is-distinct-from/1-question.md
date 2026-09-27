# sql/05-NULL 비교 — IS NULL·IS DISTINCT FROM·NULL 안전 등호 — 질문

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

### 1. `= NULL` 은 왜 에러가 아닌가 (왜)

```sql
SELECT id, name FROM emp WHERE salary = NULL;
```

- 이 질의의 결과 행 수는 몇이고, 에러가 아닌 것이 왜 위험한가?

### 2. 뒤집어도 같은가 (예측)

```sql
SELECT id, name FROM emp WHERE salary <> NULL;
```

- 1번과 결과가 달라지는가?

### 3. `IS NULL` 만 `UNKNOWN` 을 안 내는 이유 (왜)

```sql
SELECT NULL = NULL AS eq, NULL <> NULL AS ne, NULL IS NULL AS isnull;
```

- 세 값을 적을 수 있고, 셋째만 다른 이유를 한 문장으로 말할 수 있는가?

### 4. ★ `NULL` 안전 등호의 방언 (예측)

```sql
-- (A)
SELECT 1 IS DISTINCT FROM 1, 1 IS DISTINCT FROM 2, 1 IS DISTINCT FROM NULL, NULL IS DISTINCT FROM NULL;
-- (B)
SELECT 1 <=> 1, 1 <=> 2, 1 <=> NULL, NULL <=> NULL;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 (A)와 (B)가 각각 무엇을 돌려주는가?

### 5. 이식 가능한 형태 (연결)

- 두 엔진 모두에서 도는 `NULL` 안전 비교를 쓸 수 있는가, 그 형태의 한계는 무엇인가?

### 6. ★ `NOT IN` 에 `NULL` 이 섞였을 때 (예측)

```sql
SELECT id, name FROM dept WHERE id NOT IN (SELECT dept_id FROM emp);
```

- 결과 행 수는 몇이고, 그 수가 나온 과정을 진릿값으로 전개할 수 있는가?

### 7. `IN` 은 왜 멀쩡한가 (왜)

```sql
SELECT id, name FROM dept WHERE id IN (SELECT dept_id FROM emp);
```

- 6번과 달리 이쪽은 왜 제대로 도는가?

### 8. 탐침 쪽이 `NULL` 일 때 (예측)

```sql
-- (A)
SELECT id, name FROM emp WHERE dept_id IN (10, 20, 30);
-- (B)
SELECT id, name FROM emp WHERE dept_id NOT IN (10, 20, 30);
```

- (A)와 (B)의 행 수를 더하면 4가 되는가?

### 9. 처방 셋 (연결)

- 6번을 고치는 방법 셋은 각각 무엇이고, 어느 것이 가장 강한가?

### 10. `ISNULL` 이라는 이름 (경계)

```sql
-- (A) SELECT salary ISNULL FROM emp;
-- (B) SELECT ISNULL(salary) FROM emp;
```

- (A)와 (B)는 각각 어느 엔진에서 도는가?

### 11. 인덱스를 타나 (예측)

- `WHERE v IS NULL` 과 `NULL` 안전 등호는 각각 인덱스를 타는가, 두 엔진에서 같은가?

### 12. 비교와 묶기 (경계)

- `NULL = NULL` 이 참이 아닌데 `DISTINCT` 는 왜 `NULL` 인 행들을 한 행으로 접는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
