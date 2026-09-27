# sql/13-INNER JOIN — 질문

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

팬아웃 문항(8·9번)에서만 표 둘이 더 쓰인다. 만드는 문은 정답 파일에 있다.

```text
proj (프로젝트)          emp_proj (사원-프로젝트)
+-----+-------+          +--------+---------+
| id  | name  |          | emp_id | proj_id |
+-----+-------+          +--------+---------+
| 100 | atlas |          |      1 |     100 |   <- ann 은 두 프로젝트
| 200 | beta  |          |      1 |     200 |
+-----+-------+          |      2 |     100 |   <- bob 은 하나
                         +--------+---------+       cho·dan 은 없다
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 어느 행이 사라지나 (예측)

```sql
SELECT e.name, d.name FROM emp e JOIN dept d ON e.dept_id = d.id;
```

- 결과 행 수는 몇이고, `emp`·`dept` 의 어느 행이 결과에 없는가?

### 2. `dan` 이 사라진 이유 (왜)

- `dan` 의 세 짝(`dan-sales`·`dan-dev`·`dan-hr`)이 전부 떨어진 이유를 진릿값 한 낱말로 설명할 수 있는가?

### 3. 사라진 것을 알 수 있나 (경계)

- 결과 3행만 받아 든 사람이 「원래 사원이 4명이었다」를 알 수 있는가?

### 4. `ON` 과 `WHERE` (예측)

```sql
-- (A)
SELECT e.name, d.name FROM emp e JOIN dept d ON e.dept_id = d.id AND d.name = 'sales';
-- (B)
SELECT e.name, d.name FROM emp e JOIN dept d ON e.dept_id = d.id WHERE d.name = 'sales';
```

- 두 질의의 결과는 같은가?

### 5. 그런데 왜 `ON` 에 적나 (연결)

- 4번에서 결과가 같은데도 조인 조건을 `ON` 에 적기를 권하는 이유는 무엇인가?

### 6. `JOIN` 에 `ON` 이 없으면 (예측)

```sql
SELECT e.name, d.name FROM emp e JOIN dept d;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 나오는가?

### 7. `ON` 에 부등호 (경계)

```sql
SELECT e.name, d.name FROM emp e JOIN dept d ON e.dept_id > d.id;
```

- 이 질의는 통과하는가, 통과한다면 결과는 무엇인가?

### 8. 조인했는데 행이 늘었다 (예측)

```sql
SELECT e.name, ep.proj_id, e.salary FROM emp e JOIN emp_proj ep ON e.id = ep.emp_id;
```

- 결과 행 수는 몇이고, `ann` 의 행이 몇 개인가?

### 9. 그 위에 `SUM` 을 씌우면 (예측)

```sql
SELECT SUM(e.salary) FROM emp e JOIN emp_proj ep ON e.id = ep.emp_id;
```

- 결과는 얼마이고, 「프로젝트가 있는 사원의 급여 합」의 정답은 얼마인가?

### 10. 팬아웃 처방 (연결)

- 9번을 정답이 나오게 고치는 방법 둘을 각각 언제 쓰는가?

### 11. `NATURAL JOIN` (예측)

```sql
SELECT COUNT(*) FROM emp NATURAL JOIN dept;
```

- 결과는 몇이고, 왜 그런가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
