# sql/29-순위 함수 — `ROW_NUMBER`·`RANK`·`DENSE_RANK`·`NTILE` — 질문

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
emp8 을 salary DESC 로 줄 세운 모습

  500  500 | 400  400  400 | 300  300 |  NULL
  bob  fay | dan  gus  hui | ann  eve |  cho
  (dept10)   (20 20 없음*)   (10 10)    (20)
             * dan 은 dept_id 가 NULL 이다
```

1~5번은 **`WHERE salary IS NOT NULL` 로 `cho` 를 뺀 7행**을 쓴다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 네 함수를 나란히 (예측)

```sql
SELECT name, salary, ROW_NUMBER() OVER w AS rn, RANK() OVER w AS rk,
       DENSE_RANK() OVER w AS drk, NTILE(3) OVER w AS nt
FROM emp8 WHERE salary IS NOT NULL WINDOW w AS (ORDER BY salary DESC);
```

- `rk` 와 `drk` 열은 각각 어떤 수열이 되고, `rk` 가 3 다음에 6 으로 뛰는 이유는 무엇인가?

### 2. 「3등까지 상을 준다」 (경계)

- 이 요구를 `RANK <= 3` 으로 쓸 때와 `DENSE_RANK <= 3` 으로 쓸 때 상을 받는 사람 수는 각각 몇 명인가?

### 3. ★ `ROW_NUMBER` 를 열 번 돌리면 (예측)

```sql
SELECT name, ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn FROM emp8 WHERE salary IS NOT NULL;
```

- 한 엔진에서 10회 돌리면 결과가 같은가? 그리고 두 엔진의 결과는 같은가?

### 4. 비결정성의 조건 (왜)

- `ROW_NUMBER` 가 비결정적이 되는 조건 두 가지는 무엇이고, `RANK` 에는 왜 그 문제가 없는가?

### 5. 고치는 법 (연결)

- 「부서별 최고 연봉자 한 명」을 두 엔진에서 항상 같은 사람으로 뽑으려면 `OVER` 절을 어떻게 적는가?

### 6. ★ `NTILE` 의 나머지 (예측)

```sql
SELECT name, NTILE(3) OVER (ORDER BY id) AS nt, NTILE(5) OVER (ORDER BY id) AS nt5 FROM emp8;
```

- 8행을 3조·5조로 나누면 각 조의 크기는 얼마이고, 나머지는 앞 조에 붙는가 뒤 조에 붙는가?

### 7. 조 개수가 행 수보다 크면 (경계)

- `NTILE(20)` 을 8행에 쓰면 어떻게 되고, 그 사실을 결과만 보고 알 수 있는가?

### 8. ★ 방언 — `NTILE` 의 인자 (예측)

```sql
-- (A)
SELECT NTILE(0)    OVER (ORDER BY salary) FROM emp8;
-- (B)
SELECT NTILE(-1)   OVER (ORDER BY salary) FROM emp8;
-- (C)
SELECT NTILE(NULL) OVER (ORDER BY salary) FROM emp8;
```

- 셋은 PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 어떻게 되는가?

### 9. ★ 방언 — `NULL` 은 몇 등인가 (예측)

```sql
SELECT name, salary, RANK() OVER (ORDER BY salary DESC) AS rk FROM emp8;
```

- `cho`(salary `NULL`)의 `rk` 와 `bob`(500)의 `rk` 는 두 엔진에서 각각 얼마인가?

### 10. 그룹별 1위 — 행 수가 다르다 (예측)

- 「부서별 1위」를 `ROW_NUMBER ... = 1` 로 뽑을 때와 `RANK ... = 1` 로 뽑을 때 결과는 각각 몇 행인가?

### 11. 프레임을 적으면 (경계)

- `RANK() OVER (ORDER BY salary ROWS UNBOUNDED PRECEDING)` 은 에러인가, 값이 달라지는가?

### 12. `ORDER BY` 를 빠뜨리면 (경계)

- `RANK() OVER ()` 와 `ROW_NUMBER() OVER ()` 는 각각 무엇을 돌려주는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
