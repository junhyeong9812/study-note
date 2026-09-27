# sql/31-윈도우 함수의 평가 시점과 `WINDOW` 절 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 데이터는 26~31 여섯 주제가 공유한다. **표는 `emp`·`dept` 그대로**이고, 행이 모자라는 만큼만 CTE 로 얹는다.

```sql
WITH emp8 AS (
  SELECT id, name, dept_id, salary FROM emp
  UNION ALL SELECT 5, 'eve', 10, 300
  UNION ALL SELECT 6, 'fay', 10, 500
  UNION ALL SELECT 7, 'gus', 20, 400
  UNION ALL SELECT 8, 'hui', 20, 400
)
```

```text
emp8                                salary >= 400  : bob dan fay gus hui  (5행)
+----+------+---------+--------+    salary < 400   : ann eve              (2행)
| id | name | dept_id | salary |    salary IS NULL : cho                  (1행)
+----+------+---------+--------+
|  1 | ann  |      10 |    300 |    dept_id = 10   : 4행
|  2 | bob  |      10 |    500 |    dept_id = 20   : 3행
|  3 | cho  |      20 |   NULL |    dept_id = NULL : 1행
|  4 | dan  |    NULL |    400 |
|  5 | eve  |      10 |    300 |
|  6 | fay  |      10 |    500 |
|  7 | gus  |      20 |    400 |
|  8 | hui  |      20 |    400 |
+----+------+---------+--------+
```

[01번 주제](../01-logical-query-processing-order/)의 여덟 칸이 이 주제의 좌표계다.

```text
1. FROM  2. WHERE  3. GROUP BY  4. HAVING  5. SELECT  6. DISTINCT  7. ORDER BY  8. LIMIT
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 세 절에 던지면 (예측)

```sql
-- (A)
SELECT name FROM emp8 WHERE ROW_NUMBER() OVER (ORDER BY id) <= 2;
-- (B)
SELECT dept_id, COUNT(*) FROM emp8 GROUP BY dept_id HAVING ROW_NUMBER() OVER (ORDER BY dept_id) = 1;
-- (C)
SELECT name FROM emp8 GROUP BY ROW_NUMBER() OVER (ORDER BY id);
```

- 셋은 두 엔진에서 각각 어떻게 되고, 두 엔진의 메시지는 어떻게 다른가?

### 2. 왜 못 쓰나 (왜)

- 윈도우 함수를 `WHERE` 에서 못 쓰는 이유를 01번의 여덟 칸으로 설명하면?

### 3. `ORDER BY` 는 왜 되나 (왜)

- 같은 윈도우 함수를 `ORDER BY` 에서는 쓸 수 있는 이유는 무엇인가?

### 4. ★ `WHERE` 가 창을 줄인다 (예측)

```sql
-- (A)
SELECT name, COUNT(*) OVER () AS c FROM emp8 WHERE salary >= 400;
-- (B)
SELECT name, COUNT(*) OVER () AS c FROM emp8;
```

- (A)와 (B)의 `c` 는 각각 얼마이고, 그 차이가 뜻하는 것은 무엇인가?

### 5. 거르는 법 (연결)

- 「순위 2위까지」를 뽑으려면 질의를 어떻게 고치는가? 서브쿼리와 CTE 중 무엇이 맞는가?

### 6. ★ 감쌌는데 답이 다르다 (예측)

```sql
WITH ranked AS (SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn FROM emp8)
SELECT name, salary, rn FROM ranked WHERE rn <= 2;
```

- 두 엔진에서 각각 누가 뽑히고, 그 차이의 원인은 이 주제의 규칙인가 다른 주제의 규칙인가?

### 7. `LIMIT` 로 대신할 수 있나 (경계)

- 「상위 2명」을 `ORDER BY ... LIMIT 2` 로 쓰면 6번과 같은 답이 나오는가? 「부서마다 1명」도 그렇게 쓸 수 있는가?

### 8. `LIMIT` 이 계산을 줄여 주나 (왜)

- `LIMIT 2` 를 붙이면 윈도우 계산이 두 행에 대해서만 일어나는가?

### 9. 집계와 윈도우의 순서 (예측)

```sql
SELECT dept_id, COUNT(*) AS c, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rn
FROM emp8 GROUP BY dept_id;
```

- 이 문은 도는가? 돈다면 창은 몇 행을 보는가?

### 10. `DISTINCT` 와의 순서 (경계)

- `SELECT DISTINCT dept_id, COUNT(*) OVER (PARTITION BY dept_id)` 는 몇 행이 되고, `GROUP BY` 로 쓴 것과 무엇이 다른가?

### 11. `WINDOW` 절 (연결)

- 같은 창을 세 함수가 쓸 때 `WINDOW` 절을 어떻게 적고, 그 절은 질의의 어느 자리에 오는가?

### 12. ★ `QUALIFY` 를 던지면 (예측)

```sql
SELECT name, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn FROM emp8 QUALIFY rn <= 2;
```

- 두 엔진에서 각각 어떤 에러가 나고, 두 에러의 뜻은 같은가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
