# sql/27-`PARTITION BY` 와 윈도우 `ORDER BY` — 질문

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
emp8                                파티션으로 보면
+----+------+---------+--------+
| id | name | dept_id | salary |    dept_id = 10   : ann(300) bob(500) eve(300) fay(500)
+----+------+---------+--------+    dept_id = 20   : cho(NULL) gus(400) hui(400)
|  1 | ann  |      10 |    300 |    dept_id = NULL : dan(400)
|  2 | bob  |      10 |    500 |
|  3 | cho  |      20 |   NULL |
|  4 | dan  |    NULL |    400 |
|  5 | eve  |      10 |    300 |
|  6 | fay  |      10 |    500 |
|  7 | gus  |      20 |    400 |
|  8 | hui  |      20 |    400 |
+----+------+---------+--------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 칸막이는 사람을 내보내나 (예측)

```sql
SELECT name, dept_id, SUM(salary) OVER () AS all_sum,
       SUM(salary) OVER (PARTITION BY dept_id) AS dept_sum
FROM emp8;
```

- 결과는 몇 행이고, `dan` 행의 `dept_sum` 은 얼마인가?

### 2. 묶기와 세기의 `NULL` (연결)

- `PARTITION BY dept_id` 에서 `NULL` 이 한 칸이 되는 것은, `COUNT(DISTINCT dept_id)` 가 `NULL` 을 안 세는 것과 어떻게 다른가?

### 3. ★ `ORDER BY` 하나로 값이 바뀐다 (예측)

```sql
SELECT name, dept_id,
       SUM(salary) OVER (PARTITION BY dept_id) AS no_order,
       SUM(salary) OVER (PARTITION BY dept_id ORDER BY id) AS with_order
FROM emp8;
```

- `dept_id = 10` 네 행의 `no_order` 와 `with_order` 는 각각 무엇이고, 왜 달라지는가?

### 4. 순서가 없으면 프레임은 무엇인가 (왜)

- 윈도우 `ORDER BY` 를 안 적으면 프레임이 파티션 전체가 되는 이유를 「피어」라는 말로 설명하면?

### 5. 두 개의 `ORDER BY` (경계)

- `SUM(salary) OVER (ORDER BY id)` 를 쓰면서 질의 끝에 `ORDER BY salary DESC` 를 적으면, 두 순서는 서로 간섭하는가?

### 6. ★ 동률이 있는 열로 줄 세우면 (예측)

```sql
SELECT name, salary, SUM(salary) OVER (PARTITION BY dept_id ORDER BY salary) AS running
FROM emp8;
```

- `dept_id = 10` 의 `ann`(300)과 `eve`(300)의 `running` 은 각각 얼마이고, 왜 그런가?

### 7. ★ 방언 — 창 안의 `NULL` 은 어디에 서나 (예측)

```sql
SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary) AS rn FROM emp8;
```

- `cho`(salary `NULL`)의 `rn` 은 PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 얼마인가?

### 8. `NULL` 위치 때문에 값까지 갈리는 자리 (연결)

- 6번 질의에서 `cho` 의 `running` 이 두 엔진에서 각각 무엇이 되고, 그 차이의 뿌리는 어느 규칙인가?

### 9. 양쪽에서 같은 답을 내려면 (연결)

- 창 안의 `NULL` 위치를 두 엔진에서 똑같이 고정하려면 `ORDER BY` 를 어떻게 적는가?

### 10. `OVER` 절의 별칭 (예측)

```sql
SELECT salary * 12 AS annual, SUM(salary) OVER (PARTITION BY annual) AS s FROM emp8;
```

- 이 문은 두 엔진에서 각각 어떻게 되고, MySQL 이 `HAVING` 에서는 별칭을 받아 주는 것과 어떻게 어긋나는가?

### 11. 파티션 축은 무엇으로 잡나 (경계)

- `PARTITION BY salary` 처럼 키가 아닌 열로 창을 나눌 수 있는가? `cho` 의 `COUNT(*) OVER (PARTITION BY salary)` 는 얼마인가?

### 12. 칸이 바뀔 때 (왜)

- 누적합이 부서 경계에서 다시 0부터 쌓이는 이유는 무엇이고, 이어서 쌓게 하려면 무엇을 빼는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
