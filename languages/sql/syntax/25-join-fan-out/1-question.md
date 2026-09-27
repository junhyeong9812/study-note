# sql/25-조인 팬아웃 — 행 수와 집계가 틀어지는 자리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다.\
팬아웃을 보이려면 1:N 이 필요해서 **배정표 `asg` 를 CTE 로 얹는다**(표를 새로 만들지 않았다).

```text
emp (사원)                          asg (프로젝트 배정)
+----+------+---------+--------+    +--------+------+
| id | name | dept_id | salary |    | emp_id | proj |
+----+------+---------+--------+    +--------+------+
|  1 | ann  |      10 |    300 |    |      1 | p1   |   ann : 2 개
|  2 | bob  |      10 |    500 |    |      1 | p2   |
|  3 | cho  |      20 |   NULL |    |      2 | p1   |   bob : 2 개
|  4 | dan  |    NULL |    400 |    |      2 | p3   |
+----+------+---------+--------+    |      3 | p2   |   cho : 1 개
   SUM(salary) = 1200               |      4 | p1   |   dan : 1 개
                                    +--------+------+
```

```sql
WITH asg(emp_id, proj) AS (
  SELECT 1,'p1' UNION ALL SELECT 1,'p2'
  UNION ALL SELECT 2,'p1' UNION ALL SELECT 2,'p3'
  UNION ALL SELECT 3,'p2'
  UNION ALL SELECT 4,'p1')
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 조인이 행을 몇 개로 만드나 (예측)

- `emp LEFT JOIN asg ON asg.emp_id = emp.id` 의 결과는 몇 행이고, 왜 그 수인가?

### 2. ★ 인건비가 얼마로 나오나 (예측)

```sql
SELECT SUM(e.salary) AS payroll, COUNT(*) AS c, COUNT(DISTINCT e.id) AS heads
FROM emp e LEFT JOIN asg a ON a.emp_id = e.id;
```

- 세 값은 각각 얼마이고, 참값과 다른 것은 어느 것인가?

### 3. `COUNT(DISTINCT)` 만 살아남는 이유 (왜)

- 같은 질의에서 `SUM` 은 부푸는데 `COUNT(DISTINCT e.id)` 는 왜 안 부푸는가?

### 4. ★ 부서별 인건비 (예측)

```sql
SELECT e.dept_id, SUM(e.salary) AS payroll, COUNT(DISTINCT e.id) AS heads
FROM emp e LEFT JOIN asg a ON a.emp_id = e.id GROUP BY e.dept_id;
```

- `dept_id=10`(sales) 행의 두 값은 각각 얼마이고, 참값의 몇 배인가?

### 5. ★ 조인을 하나 더 붙이면 (예측)

기술 보유표 `skl` 을 더 붙인다 — `ann` 3개, 나머지 각 1개.

- 결과 행 수와 `SUM(e.salary)` 는 각각 얼마가 되는가? 배율은 더해지는가 곱해지는가?

### 6. 처방 하나 — 선집계 (연결)

- 조인 전에 `asg` 를 어떻게 바꾸면 인건비가 800 으로 돌아오는가?

### 7. ★ `SUM(DISTINCT)` 은 처방인가 (예측)

```sql
-- 급여가 같은 두 사람 (둘 다 300), ann 은 프로젝트 2 개 eve 는 1 개. 참값은 600
SELECT SUM(t.salary) AS fanned, SUM(DISTINCT t.salary) AS sum_dist, COUNT(DISTINCT t.id) AS heads
FROM two t JOIN asg a ON a.emp_id = t.id;
```

- 세 값은 각각 얼마이고, `SUM(DISTINCT)` 는 팬아웃 처방이 되는가?

### 8. `SELECT DISTINCT` 로 되돌리기 (경계)

- 조인 결과를 `SELECT DISTINCT` 로 접어 집계할 때 반드시 포함시켜야 하는 열은 무엇인가?

### 9. 처방 셋 — `LATERAL` (연결)

- `LATERAL` 이 팬아웃을 막는 이유는 무엇이고, 언제 선집계보다 나은가?

### 10. 건수와 종류 수 (경계)

- `COUNT(a.proj)` 와 `COUNT(DISTINCT a.proj)` 가 sales 부서에서 각각 얼마이고 왜 다른가?

### 11. 계획에서 찾기 (연결)

- `EXPLAIN ANALYZE` 출력에서 팬아웃이 일어난 자리를 어떻게 짚는가?

### 12. 방언 (경계)

- 이 주제에서 PostgreSQL 18.6 과 MySQL 8.4.10 의 값이 갈리는 자리가 있는가?

### 13. 첫 습관 (왜)

- 조인 뒤에 집계를 쓰기 전에 매번 던져야 할 질의 한 줄은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
