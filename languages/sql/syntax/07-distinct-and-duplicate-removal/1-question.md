# sql/07-DISTINCT 와 중복 제거 — 질문

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

### 1. ★ 무엇을 기준으로 지우나 (예측)

```sql
-- (A)
SELECT DISTINCT dept_id FROM emp;
-- (B)
SELECT DISTINCT dept_id, salary FROM emp;
```

- (A)와 (B)의 결과 행 수는 각각 몇인가?

### 2. 괄호는 무슨 일을 하나 (예측)

```sql
SELECT DISTINCT(dept_id), salary FROM emp;
```

- 이 질의의 결과는 1번의 (A)와 (B) 중 어느 쪽과 같은가?

### 3. `NULL` 이 접히는 이유 (왜)

- `NULL = NULL` 이 참이 아닌데 `SELECT DISTINCT dept_id` 는 왜 `NULL` 을 한 행만 내는가?

### 4. ★ 세는 것과 접는 것 (예측)

```sql
SELECT COUNT(*), COUNT(dept_id), COUNT(DISTINCT dept_id) FROM emp;
```

- 세 값을 적을 수 있고, 그중 어느 것이 `SELECT DISTINCT dept_id` 의 행 수와 다른가?

### 5. 여러 열의 조합 세기 — 방언 (예측)

```sql
-- (A)
SELECT COUNT(DISTINCT dept_id, salary) FROM emp;
-- (B)
SELECT COUNT(DISTINCT (dept_id, salary)) FROM emp;
```

- 두 엔진에서 (A)와 (B)가 각각 무엇을 돌려주고, 숫자가 다르다면 왜 다른가?

### 6. `DISTINCT` 와 `ORDER BY` 의 충돌 (경계)

```sql
SELECT DISTINCT dept_id FROM emp ORDER BY salary;
```

- 이 질의가 거부되는 것이 여덟 칸 중 어느 두 칸의 순서를 증명하는가?

### 7. 「목록에 있어야 한다」의 엄격도 (예측)

```sql
SELECT DISTINCT dept_id FROM emp ORDER BY dept_id * 1;
```

- 두 엔진 중 어느 쪽이 받아 주는가?

### 8. `DISTINCT` 대 `GROUP BY` (연결)

- 같은 중복 제거를 두 방식으로 썼을 때 계획이 다른가, 무엇을 기준으로 고르는가?

### 9. ★ 「부서마다 급여 1위 한 명」 (예측)

```sql
SELECT DISTINCT ON (dept_id) dept_id, id, name, salary FROM emp ORDER BY dept_id, salary DESC;
```

- PostgreSQL 18.6 의 결과 세 행은 무엇이고, `dept_id = 20` 의 대표가 그 사람인 이유는 무엇인가?

### 10. MySQL 에서 같은 요구를 (연결)

- MySQL 8.4.10 에서 9번과 같은 결과를 얻는 방법은 무엇이고, 왜 한 겹 감싸야 하는가?

### 11. `DISTINCT ON` 의 `ORDER BY` 규칙 (경계)

```sql
SELECT DISTINCT ON (dept_id) dept_id, id FROM emp ORDER BY id;
```

- 이 질의가 거부되는 이유는 무엇인가?

### 12. 언제 쓰면 안 되나 (연결)

- 조인 결과에 중복이 보여 `DISTINCT` 를 붙이고 싶을 때, 먼저 의심해야 하는 것은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
