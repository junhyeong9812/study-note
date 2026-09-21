# sql/17-SELF JOIN — 질문

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

계층 문항(6~9번)에서만 `staff` 한 표를 더 쓴다. **`emp` 에 `mgr_id` 한 칸을 더한 것**이고,\
기존 `emp` 에서 만들어 트랜잭션으로 되돌렸다 — 만드는 문은 정답 파일에 있다.

```text
staff
+----+------+---------+--------+--------+
| id | name | dept_id | salary | mgr_id |
+----+------+---------+--------+--------+
|  1 | ann  |      10 |    300 |   NULL |   <- 꼭대기
|  2 | bob  |      10 |    500 |      1 |
|  3 | cho  |      20 |   NULL |      1 |
|  4 | dan  |    NULL |    400 |      2 |
+----+------+---------+--------+--------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 별칭 없이 같은 표를 두 번 (예측)

```sql
SELECT * FROM emp JOIN emp ON emp.id = emp.id;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 나오는가?

### 2. 막는 이유 (왜)

- 1번을 막는 이유를 「중복이라서」가 아닌 다른 말로 설명할 수 있는가?

### 3. 짝의 개수 (예측)

```sql
SELECT COUNT(*) FROM emp a CROSS JOIN emp b;
```

- 결과는 몇이고, 그 수가 어떻게 나오는가?

### 4. `<>` 와 `<` (예측)

```sql
-- (A)
SELECT a.name, b.name FROM emp a JOIN emp b ON a.dept_id = b.dept_id AND a.id <> b.id;
-- (B)
SELECT a.name, b.name FROM emp a JOIN emp b ON a.dept_id = b.dept_id AND a.id < b.id;
```

- 두 질의의 결과 행 수는 각각 몇이고, 차이가 나는 이유는 무엇인가?

### 5. 조건을 아예 빼면 (경계)

- `ON a.dept_id = b.dept_id` 만 쓰고 자기 자신을 막는 조건을 빼면 무엇이 섞여 들어오는가?

### 6. 상사 붙이기 (예측)

```sql
SELECT e.name AS emp, m.name AS mgr FROM staff e JOIN staff m ON e.mgr_id = m.id;
```

- 결과 행 수는 몇이고, `staff` 의 어느 행이 결과에 없는가?

### 7. 그것을 되살리려면 (연결)

- 6번에서 빠진 행을 되살리려면 무엇을 바꿔야 하고, 왜 계층 조회는 거의 항상 그 형태인가?

### 8. 두 단계 위 (예측)

```sql
SELECT e.name, m.name, g.name FROM staff e
LEFT JOIN staff m ON e.mgr_id = m.id
LEFT JOIN staff g ON m.mgr_id = g.id;
```

- `grand` 칸에 값이 들어가는 행은 누구 하나뿐인가, 그리고 이 방식의 한계는 무엇인가?

### 9. 부하 수 세기 (경계)

```sql
SELECT m.name, COUNT(*) FROM staff m LEFT JOIN staff e ON e.mgr_id = m.id GROUP BY m.id, m.name;
```

- 이 질의로 「부하 0명」을 표현할 수 있는가? 안 된다면 무엇으로 바꾸는가?

### 10. 연속 행 비교 (예측)

```sql
SELECT a.name AS lower, b.name AS higher, b.salary - a.salary AS gap
FROM emp a JOIN emp b ON b.salary = (SELECT MIN(x.salary) FROM emp x WHERE x.salary > a.salary);
```

- 결과 행 수는 몇이고, `bob` 과 `cho` 는 왜 `lower` 칸에 없는가?

### 11. 더 싼 방법 (연결)

- 10번과 같은 「이웃 행 비교」를 `SELF JOIN` 대신 무엇으로 쓰면 되고, 이 주제와의 경계는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
