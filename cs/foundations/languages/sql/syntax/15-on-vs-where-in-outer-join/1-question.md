# sql/15-OUTER JOIN 에서 ON 과 WHERE 의 차이 — 질문

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

### 1. ★ 같은 조건, 다른 자리 (예측)

```sql
-- (A)
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id AND d.name = 'sales';
-- (B)
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE d.name = 'sales';
```

- (A)와 (B)의 결과 행 수는 각각 몇인가?

### 2. 왜 갈리나 (왜)

- 1번의 차이를 [01번](../01-logical-query-processing-order/)의 처리 순서로 설명할 수 있는가?

### 3. `ON FALSE` (경계)

```sql
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON FALSE;
```

- 아무 짝도 못 짓게 했는데 결과 행 수는 몇인가?

### 4. `dan` 은 왜 죽었나 (연결)

- 1번의 (B)에서 `dan` 이 사라진 이유를 진릿값 한 낱말로 설명할 수 있는가?

### 5. 내부 조인에서는 왜 같았나 (왜)

- [13번](../13-inner-join/)에서 `ON` 과 `WHERE` 의 결과가 같았던 이유는 무엇인가?

### 6. 조건이 보존 측 열에 걸리면 (예측)

```sql
-- (A)
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id AND e.salary >= 400;
-- (B)
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE e.salary >= 400;
```

- (A)와 (B)의 결과는 각각 무엇이고, 이번엔 어느 쪽이 의도한 것일 가능성이 높은가?

### 7. 판정표 (연결)

- 조건이 걸린 열이 보존 측이냐 상대 측이냐에 따라 `ON`·`WHERE` 네 칸에 무엇이 들어가는가?

### 8. `RIGHT JOIN` 에서도 같은가 (예측)

```sql
-- (A)
SELECT e.name, d.name FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id AND e.salary >= 400;
-- (B)
SELECT e.name, d.name FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id WHERE e.salary >= 400;
```

- (A)와 (B)의 결과 행 수는 각각 몇인가?

### 9. 옵티마이저는 아는가 (예측)

```sql
EXPLAIN SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE d.name = 'sales';
```

- PostgreSQL 18.6 의 계획 맨 윗줄에 무엇이 뜨고, MySQL 8.4.10 의 계획에서는 무엇이 사라지는가?

### 10. 고치는 법 셋 (연결)

- 1번의 (B)를 고치는 방법 셋은 각각 무엇이고, 셋이 같은 답을 주는가?

### 11. 어디서 틀리나 (경계)

- 질의를 눈으로 훑을 때 이 사고를 잡아내는 신호 한 가지는 무엇인가?

### 12. 방언 (경계)

- 이 주제에서 PostgreSQL 18.6 과 MySQL 8.4.10 의 **결과**가 다른 자리가 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
