# sql/36-수치 타입과 수치 함수 (정수 나눗셈·반올림·정밀도) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.

MySQL 쪽 조건을 밝혀 둔다 — 이 답들은 이 설정에서 나온 것이다.

```text
sql_mode = ONLY_FULL_GROUP_BY, STRICT_TRANS_TABLES, NO_ZERO_IN_DATE,
           NO_ZERO_DATE, ERROR_FOR_DIVISION_BY_ZERO, NO_ENGINE_SUBSTITUTION   (기본값)
div_precision_increment = 4                                                    (기본값)
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 정수끼리 나누면 (예측)

```sql
SELECT 7/2 AS a, 5/2 AS b, -5/2 AS c, 1/3 AS d;
```

- 두 엔진에서 각각 무엇이 나오는가?

### 2. 소수 자릿수는 누가 정하나 (예측)

```sql
SELECT 3/5 AS a, 3.0/5 AS b;
```

- 두 엔진에서 각각 무엇이 나오고, 그 자릿수를 정하는 것은 무엇인가?

### 3. ★ `0.1 + 0.2` (예측)

```sql
SELECT 0.1 + 0.2 AS r;
SELECT CAST(0.1 AS DOUBLE PRECISION) + CAST(0.2 AS DOUBLE PRECISION) AS r;
```

- 두 문이 두 엔진에서 각각 무엇을 돌려주는가?

### 4. ★ 반올림의 경계 (예측)

```sql
SELECT ROUND(0.5) AS a, ROUND(1.5) AS b, ROUND(2.5) AS c;
SELECT ROUND(CAST(0.5 AS DOUBLE PRECISION)) AS a,
       ROUND(CAST(2.5 AS DOUBLE PRECISION)) AS c;
```

- 네 값이 두 엔진에서 각각 무엇인가 — 그리고 답을 가르는 것은 무엇인가?

### 5. 넘치면 (예측)

```sql
SELECT 2147483647 + 1 AS r;              -- (a) 식만
-- (b) int 열에 2147483647 을 넣고 UPDATE t SET i = i + 1;
```

- (a) 와 (b) 가 두 엔진에서 각각 어떻게 되는가?

### 6. 0 으로 나누면 (예측)

```sql
SELECT 1/0 AS r;                          -- (a)
INSERT INTO t36z VALUES (1/0);            -- (b) t36z (v INT)
```

- (a) 와 (b) 가 두 엔진에서 각각 어떻게 되는가?

### 7. 자릿수가 넘치는 두 가지 (경계)

- `NUMERIC(5,2)` 열에 `1.005` 를 넣을 때와 `12345.6` 을 넣을 때 무엇이 다른가?

### 8. 올림의 방향 (경계)

- `CEIL(-2.1)` 은 `-2` 인가 `-3` 인가 — 그리고 그것이 `-5/2` 의 규칙과 어떻게 다른가?

### 9. 왜 부동소수 열은 `=` 로 못 찾나 (왜)

- `float` 열의 합계가 `0.3` 인 행을 `WHERE s = 0.3` 으로 찾으면 왜 0행인가?

### 10. 이식할 때 어디가 조용한가 (연결)

- MySQL 질의를 PG 로 옮길 때, 수치 쪽에서 **에러 없이 답만 달라지는** 자리는 어디인가?

### 11. 그래서 어떤 타입을 고르나 (연결)

- 돈·비율·과학 계산에 각각 어떤 수치 타입을 고르고, 그 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
