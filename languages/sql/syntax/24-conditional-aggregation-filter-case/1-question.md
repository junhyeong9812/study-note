# sql/24-조건부 집계 — `FILTER` 와 `CASE` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다.\
★ **`cho` 의 급여가 `NULL` 이라 `dept_id=20` 그룹은 「조건에 맞는 행이 0개」가 된다.**

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

### 1. `WHERE` 로는 왜 안 되나 (왜)

- 「급여 400 이상 / 미만 / 없음」을 한 줄에 내려는데 `WHERE` 로는 왜 한 번에 안 되는가?

### 2. ★ 계수기 다섯 (예측)

```sql
SELECT COUNT(*) AS total,
       COUNT(*) FILTER (WHERE salary >= 400)  AS hi,
       COUNT(*) FILTER (WHERE salary <  400)  AS lo,
       COUNT(*) FILTER (WHERE salary IS NULL) AS unknown
FROM emp;
```

- 네 값은 각각 얼마이고, `hi + lo` 가 `total` 이 되는가?

### 3. `FILTER` 를 MySQL 에 (예측)

- 2번 질의를 MySQL 8.4.10 에 던지면 어떻게 되는가? 설정으로 켤 수 있는가?

### 4. ★ 네 형태의 갈림 (예측)

```sql
SELECT dept_id,
       SUM  (CASE WHEN salary >= 400 THEN 1 ELSE 0 END) AS sum_else0,
       SUM  (CASE WHEN salary >= 400 THEN 1 END)        AS sum_noelse,
       COUNT(CASE WHEN salary >= 400 THEN 1 END)        AS cnt_case,
       COUNT(CASE WHEN salary >= 400 THEN 1 ELSE 0 END) AS cnt_case_else0
FROM emp GROUP BY dept_id;
```

- `dept_id=10` 과 `dept_id=20` 행에서 네 값은 각각 얼마인가?

### 5. `COUNT` 에 `ELSE 0` (왜)

- 4번에서 `cnt_case_else0` 가 틀린 값을 내는 이유는 무엇이고, 그 값은 무엇과 같아지는가?

### 6. ★ `AVG` 에 `ELSE 0` (예측)

```sql
SELECT dept_id,
       AVG(CASE WHEN salary >= 400 THEN salary END)        AS a_noelse,
       AVG(CASE WHEN salary >= 400 THEN salary ELSE 0 END) AS a_else0
FROM emp GROUP BY dept_id;
```

- `dept_id=10` 행의 두 값은 각각 얼마이고 왜 다른가?

### 7. `SUM` 에서는 왜 안 갈리나 (경계)

- 같은 `ELSE 0` 이 `SUM` 에서는 답을 안 바꾸는데 `AVG` 에서는 바꾸는 이유는?

### 8. 맞는 행이 0개인 그룹 (예측)

- `dept_id=20` 에서 `COUNT(*) FILTER (WHERE salary >= 400)` 과 `SUM(salary) FILTER (WHERE salary >= 400)` 은 각각 얼마인가?

### 9. ★ 이식 규칙 (연결)

- `FILTER (WHERE c)` 를 `CASE` 로 옮기는 기계적 규칙은 무엇인가?

### 10. 그래도 `FILTER` 를 쓰는 이유 (왜)

- `CASE` 로 똑같이 쓸 수 있는데도 PG 에서 `FILTER` 를 쓰는 이유는 무엇인가?

### 11. `WHERE` 와 같이 쓰면 (예측)

```sql
SELECT COUNT(*) AS all_rows, COUNT(*) FILTER (WHERE dept_id = 10) AS d10
FROM emp WHERE salary IS NOT NULL;
```

- 두 값은 각각 얼마인가?

### 12. 언제 안 쓰나 (경계)

- 조건부 집계를 쓰면 안 되는 경우를 둘 들면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
