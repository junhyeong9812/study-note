# sql/08-ORDER BY — 정렬 키·NULL 위치·정렬 안정성 — 질문

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

### 1. ★ `NULL` 은 어디에 서나 (예측)

```sql
SELECT id, salary FROM emp ORDER BY salary;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 의 행 순서를 각각 적을 수 있는가?

### 2. `DESC` 로 뒤집으면 (예측)

```sql
SELECT id, salary FROM emp ORDER BY salary DESC;
```

- 「급여 상위 1명」을 이 질의로 뽑으면 두 엔진에서 각각 누가 나오는가?

### 3. `NULLS FIRST` 문법 (경계)

```sql
SELECT id, salary FROM emp ORDER BY salary NULLS FIRST;
```

- 두 엔진 중 어느 쪽이 받아 주는가?

### 4. 이식 가능한 `NULL` 위치 제어 (연결)

- `NULLS LAST` 를 쓸 수 없는 엔진에서 같은 효과를 내려면 무엇을 정렬 키로 추가하는가?

### 5. ★ 동률의 순서는 보장되나 (경계)

```sql
SELECT name FROM emp ORDER BY dept_id;
```

- `ann` 과 `bob` 의 앞뒤는 보장되는가, 같은 질의를 열 번 돌려 같으면 보장된 것인가?

### 6. ★ 같은 `ORDER BY` 인데 순서가 바뀌는 판 (예측)

```sql
SELECT name, dept_id FROM (SELECT * FROM emp ORDER BY id DESC) t ORDER BY dept_id;
```

- 바깥 `ORDER BY` 는 그대로인데 PostgreSQL 18.6 에서 무엇이 달라지는가?

### 7. 순서를 고정하는 법 (연결)

- 동률 순서를 질의문 안에서 확정하려면 무엇을 하는가, 그러면 `NULL` 자리도 같이 고정되는가?

### 8. ★ `ORDER BY` 가 없을 때 (예측)

```sql
SELECT id, name FROM emp;                  -- (A)
UPDATE emp SET name = name WHERE id = 1;   -- 값은 그대로
SELECT id, name FROM emp;                  -- (B)
```

- PostgreSQL 18.6 에서 (A)와 (B)의 행 순서가 같은가?

### 9. 여러 키와 방향 (예측)

```sql
SELECT name FROM emp ORDER BY dept_id DESC, salary ASC;
```

- 두 엔진의 결과에서 **다른 자리는 어디 하나뿐**인가?

### 10. `SELECT` 밖의 열로 정렬 (경계)

- `ORDER BY` 가 `SELECT` 목록에 없는 열을 쓸 수 있는 이유와, 그 자유가 사라지는 조건은 무엇인가?

### 11. ★ 문자열 정렬의 기준 (예측)

```sql
SELECT 'a' < 'B' AS a_lt_B, 'A' = 'a' AS a_eq_A;
```

- 두 엔진의 답이 각각 무엇이고, 그것이 이름순 정렬에 어떤 결과를 낳는가?

### 12. `COLLATE` 로 맞추기 (연결)

- 두 엔진의 문자열 정렬을 같게 만들 수 있는가, 그 방법이 이식되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
