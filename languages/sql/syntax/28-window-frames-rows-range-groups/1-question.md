# sql/28-프레임 — `ROWS`·`RANGE`·`GROUPS` 와 기본 프레임 — 질문

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

아래 질문의 대부분은 **`WHERE salary IS NOT NULL` 로 `cho` 를 뺀 7행**을 쓴다.\
`NULL` 위치 차이가 프레임 차이 위에 겹치면 무엇 때문에 갈렸는지 알 수 없기 때문이다.

```text
emp8 을 salary 로 줄 세운 모습 (cho 제외)

  salary:  300   300   400   400   400   500   500
  name  :  ann   eve   dan   gus   hui   bob   fay
           \_____/     \_________________/   \_____/
            덩어리1          덩어리2          덩어리3
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 기본 프레임은 무엇인가 (예측)

```sql
SELECT name, salary,
       SUM(salary) OVER (ORDER BY salary) AS implicit,
       SUM(salary) OVER (ORDER BY salary RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS explicit_range
FROM emp8 WHERE salary IS NOT NULL;
```

- 두 열은 같은가 다른가, 그리고 `ann`(300)의 값은 얼마인가?

### 2. `ORDER BY` 가 없으면 (왜)

- 윈도우 `ORDER BY` 를 안 적으면 프레임이 창 전체가 되는 것을, 1번의 기본값과 **같은 규칙 하나**로 설명하면?

### 3. ★ `ROWS` 로 바꾸면 (예측)

```sql
SELECT name, salary,
       SUM(salary) OVER (ORDER BY salary) AS range_sum,
       SUM(salary) OVER (ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_sum
FROM emp8 WHERE salary IS NOT NULL;
```

- `ann`·`eve`(둘 다 300)의 두 열 값은 각각 얼마이고, PostgreSQL 과 MySQL 에서 같은 답이 나오는가?

### 4. `RANGE` 가 기본값인 이유 (왜)

- 동률이 있을 때 `ROWS` 의 답이 질의문으로 정해지지 않는 이유는 무엇인가?

### 5. 한 행씩 늘어나는 누적합을 원하면 (연결)

- 동률이 있는 열로 「한 행씩 늘어나는 누적합」을 안전하게 뽑으려면 `OVER` 절을 어떻게 적는가?

### 6. ★ 방언 — `GROUPS` (예측)

```sql
SELECT name, salary, SUM(salary) OVER (ORDER BY salary GROUPS BETWEEN 1 PRECEDING AND CURRENT ROW) AS g
FROM emp8 WHERE salary IS NOT NULL;
```

- 이 문은 두 엔진에서 각각 어떻게 되고, `bob`(500)의 값은 얼마인가?

### 7. `GROUPS` 로만 되는 일 (경계)

- 「나와 앞 등수 하나까지」를 `ROWS` 나 `RANGE` 로 적을 수 없는 이유는 무엇인가?

### 8. `EXCLUDE` 세 형태 (경계)

- `EXCLUDE CURRENT ROW`·`EXCLUDE GROUP`·`EXCLUDE TIES` 는 각각 무엇을 빼고, `ann` 에서 값이 어떻게 갈리는가?

### 9. ★ 오프셋 `RANGE` 의 제약 (예측)

```sql
-- (A)
SELECT name, SUM(salary) OVER (ORDER BY salary RANGE BETWEEN 100 PRECEDING AND 100 FOLLOWING) FROM emp8 WHERE salary IS NOT NULL;
-- (B)
SELECT name, SUM(salary) OVER (ORDER BY salary, id RANGE BETWEEN 1 PRECEDING AND CURRENT ROW) FROM emp8 WHERE salary IS NOT NULL;
-- (C)
SELECT name, SUM(salary) OVER (ORDER BY name RANGE BETWEEN 1 PRECEDING AND CURRENT ROW) FROM emp8;
```

- 셋 중 도는 것은 무엇이고, 안 도는 둘은 두 엔진이 각각 뭐라고 하는가?

### 10. 이동 평균의 분모 (예측)

```sql
SELECT name, salary, AVG(salary) OVER (ORDER BY id ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) AS moving
FROM emp8;
```

- `bob` 행의 프레임은 몇 행이고 `moving` 은 얼마인가? 둘이 안 맞는다면 왜인가?

### 11. `ORDER BY` 없이 프레임만 적으면 (경계)

- `OVER (ROWS BETWEEN 1 PRECEDING AND CURRENT ROW)` 는 에러인가? 에러가 아니라면 무엇이 문제인가?

### 12. 순위 함수와 프레임 (연결)

- `RANK() OVER (ORDER BY salary ROWS UNBOUNDED PRECEDING)` 처럼 순위 함수에 프레임을 적으면 값이 달라지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
