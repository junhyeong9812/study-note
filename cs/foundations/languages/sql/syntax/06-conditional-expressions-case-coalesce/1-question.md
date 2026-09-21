# sql/06-조건 식 — CASE·COALESCE·NULLIF·GREATEST/LEAST — 질문

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

### 1. 두 가지 `CASE` (왜)

- 단순 `CASE` 와 검색 `CASE` 는 무엇이 다르고, 단순형이 내부적으로 무슨 연산을 쓰는가?

### 2. ★ 단순 `CASE` 로 `NULL` 잡기 (예측)

```sql
SELECT id, CASE dept_id WHEN NULL THEN 'matched NULL' ELSE 'not matched' END FROM emp;
```

- `dan`(dept_id NULL)의 결과는 무엇인가?

### 3. `ELSE` 를 빼면 (예측)

```sql
SELECT id, CASE WHEN salary > 400 THEN 'high' END AS c FROM emp;
```

- 네 행의 `c` 값을 적을 수 있고, `cho` 와 `ann` 이 구별되는가?

### 4. `CASE` 의 단락 평가 (예측)

```sql
SELECT CASE WHEN 1 = 0 THEN 1/0 ELSE 99 END AS r;
```

- 두 엔진에서 각각 무엇이 나오고, MySQL 의 결과가 단락 평가의 증거가 되는가?

### 5. ★ 집계가 낀 `CASE` (예측)

```sql
SELECT CASE WHEN COUNT(*) < 0 THEN MIN(1/(salary-300)) ELSE 0 END AS r FROM emp;
```

- `COUNT(*) < 0` 은 절대 참이 아닌데, PostgreSQL 18.6 은 무엇을 돌려주는가?

### 6. 결과 타입 통일 (경계)

```sql
SELECT CASE WHEN TRUE THEN 1 ELSE 'x' END AS r;
```

- 조건이 `TRUE` 라 `ELSE` 는 쓰이지도 않는데 거부하는 엔진이 있는가?

### 7. `COALESCE` 가 `NULL` 을 없애 주는가 (예측)

```sql
SELECT COALESCE(NULL, NULL, NULL) AS all_null;
```

- 결과는 무엇이고, 이 함수에 대한 어떤 믿음이 깨지는가?

### 8. `COALESCE` 인자의 타입이 섞이면 (예측)

```sql
SELECT COALESCE(salary, 'none') AS r FROM emp;
```

- 두 엔진의 결과는 각각 무엇인가?

### 9. `NULLIF` 로 0 나눗셈 막기 (연결)

```sql
SELECT id, 1000 / NULLIF(salary, 0) AS ratio FROM emp;
```

- `NULLIF` 가 무엇을 무엇으로 바꿔서 나눗셈을 안전하게 만드는가?

### 10. ★ `GREATEST`/`LEAST` 에 `NULL` (예측)

```sql
SELECT GREATEST(1, 2, NULL) AS g, LEAST(1, 2, NULL) AS l;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 이 각각 무엇을 돌려주는가?

### 11. MySQL 전용 축약형 (경계)

```sql
SELECT IFNULL(salary, 0), IF(salary IS NULL, 'unknown', 'known') FROM emp;
```

- 이 둘의 이식 가능한 대체는 각각 무엇인가?

### 12. `COALESCE` 를 어디에 두나 (연결)

- 「값이 없으면 0」을 저장 시점·계산 중간·출력 직전 중 어디에서 적용하는 것이 나은가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
