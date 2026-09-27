# sql/30-오프셋·경계 함수 — `LAG`·`LEAD`·`FIRST_VALUE`·`LAST_VALUE` — 질문

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
id 순서 (LAG·LEAD 가 쓰는 줄)
  1     2     3      4     5     6     7     8
 ann   bob   cho    dan   eve   fay   gus   hui
 300   500   NULL   400   300   500   400   400
              ^^^^ 한가운데에 NULL 이 있다

salary 오름차순 (경계 함수가 쓰는 줄, cho 제외)
 300  300 | 400  400  400 | 500  500
 ann  eve | dan  gus  hui | bob  fay
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ `LAG`·`LEAD` 와 네 개의 `NULL` (예측)

```sql
SELECT name, salary, LAG(salary) OVER w AS prev, LEAD(salary) OVER w AS next
FROM emp8 WINDOW w AS (ORDER BY id);
```

- `ann` 의 `prev`·`bob` 의 `next`·`dan` 의 `prev`·`hui` 의 `next` 는 각각 무엇이고, 네 `NULL` 의 뜻은 같은가?

### 2. 기본값은 어디에 쓰이나 (예측)

```sql
SELECT name, salary, LAG(salary, 1, 0) OVER (ORDER BY id) AS lag_def FROM emp8;
```

- `ann` 과 `dan` 의 `lag_def` 는 각각 얼마이고, 왜 다른가?

### 3. ★★ `LAST_VALUE` 함정 (예측)

```sql
SELECT name, salary, LAST_VALUE(salary) OVER (ORDER BY salary) AS lv
FROM emp8 WHERE salary IS NOT NULL;
```

- `lv` 열은 어떤 값들이 되고, 그 값은 어느 엔진에서 그런가?

### 4. 함정의 이유 (왜)

- `LAST_VALUE` 가 3번처럼 나오는 이유를 「기본 프레임」이라는 말로 설명하면?

### 5. `FIRST_VALUE` 는 왜 멀쩡한가 (왜)

- 같은 기본 프레임인데 `FIRST_VALUE` 는 기대대로 나오는 이유는 무엇인가?

### 6. 고치는 법 셋 (연결)

- 「창 전체의 마지막 값」을 얻는 세 가지 방법은 각각 무엇인가?

### 7. ★ 프레임을 보는 함수와 안 보는 함수 (경계)

- `LAG`·`LEAD`·`FIRST_VALUE`·`LAST_VALUE`·`NTH_VALUE` 중 프레임에 의존하는 것은 어느 것인가?

### 8. `NTH_VALUE` 의 `NULL` (예측)

```sql
SELECT name, NTH_VALUE(salary, 3) OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS n3
FROM emp8;
```

- `n3` 는 무엇이 되고, 그것은 「3번째 행이 없다」는 뜻인가?

### 9. ★ 방언 — `IGNORE NULLS` (예측)

```sql
SELECT name, LAG(salary) IGNORE NULLS OVER (ORDER BY id) FROM emp8;
```

- 이 문은 PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 어떻게 되는가?

### 10. ★ 그룹 대표를 뽑으면 (예측)

```sql
SELECT name, salary, FIRST_VALUE(name) OVER (PARTITION BY dept_id ORDER BY salary DESC) AS top_earner
FROM emp8;
```

- `dept_id = 10` 과 `dept_id = 20` 의 `top_earner` 는 두 엔진에서 각각 누구인가?

### 11. ★ 방언 — 기본값의 타입과 경고 (예측)

```sql
SELECT name, LEAD(salary, 1, 'x') OVER (ORDER BY id) AS l FROM emp8;
```

- 두 엔진에서 각각 어떻게 되고, 통과하는 쪽에서 그 열에 `+ 0` 을 하면 무엇이 나오는가?

### 12. 오프셋 0과 음수 (경계)

- `LAG(salary, 0)` 과 `LAG(salary, -1)` 은 두 엔진에서 각각 어떻게 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
