# sql/20-LATERAL 조인 — 질문

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
```

```text
 부서별로 보면
   sales : bob(500), ann(300)    상위 2명이 둘 다 있다
   dev   : cho(NULL)             한 명뿐이고 급여가 NULL
   hr    : (없음)                사원이 0명
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `LATERAL` 없이 왼쪽 참조 (예측)

```sql
SELECT d.name, t.name FROM dept d
JOIN (SELECT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id ORDER BY e.id LIMIT 1) AS t ON true;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 나오는가?

### 2. 막는 이유 (왜)

- `FROM` 안의 서브쿼리가 왼쪽 항목을 못 보게 막는 이유는 무엇인가?

### 3. `CROSS JOIN LATERAL` 의 결과 (예측)

```sql
SELECT d.name AS dept, t.name AS emp, t.salary FROM dept d
CROSS JOIN LATERAL (SELECT e.name, e.salary FROM emp e WHERE e.dept_id = d.id
                    ORDER BY e.salary DESC LIMIT 1) AS t;
```

- 결과 행 수는 몇이고, `dept` 의 어느 행이 결과에 없는가?

### 4. 그것을 되살리려면 (연결)

- 3번에서 빠진 행을 되살리는 형태는 무엇이고, 그 형태에서 `ON` 자리에 무엇을 적는가?

### 5. 상관 서브쿼리로는 안 되는 것 (예측)

```sql
SELECT d.name, (SELECT e.name FROM emp e WHERE e.dept_id = d.id ORDER BY e.salary DESC, e.id LIMIT 2) FROM dept d;
```

- 이 질의는 무엇을 돌려주는가?

### 6. 여러 열 (연결)

- 부서마다 사원 수와 급여 합계를 **한 번의 서브쿼리로** 받으려면 어떻게 쓰고, `hr` 의 두 칸에는 각각 무엇이 들어가는가?

### 7. `CROSS` 로 써도 되는 경우 (경계)

- `LATERAL` 안이 집계일 때는 `CROSS JOIN LATERAL` 을 써도 왼쪽 행이 안 사라진다. 왜인가?

### 8. 순서를 바꾸면 (예측)

```sql
SELECT d.name, t.name FROM LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id) AS t, dept d;
```

- 이 질의는 통과하는가?

### 9. `RIGHT JOIN LATERAL` (예측)

```sql
SELECT d.name, t.name FROM dept d
RIGHT JOIN LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id) AS t ON true;
```

- 이 질의는 통과하는가, PostgreSQL 은 어떤 이유를 대는가?

### 10. 계획에서 확인하기 (예측)

- 3번 질의를 `EXPLAIN` / `EXPLAIN ANALYZE` 로 찍으면 「왼쪽 행마다 돈다」가 어느 숫자·어느 낱말로 드러나는가?

### 11. 버전 (경계)

- `LATERAL` 은 두 엔진에서 각각 어느 버전부터인가, 그 근거는 매뉴얼인가 릴리스 노트인가?

### 12. 언제 안 쓰나 (연결)

- 「그룹별 상위 N」을 `LATERAL` 말고 무엇으로 쓸 수 있고, 이 주제와의 경계는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
