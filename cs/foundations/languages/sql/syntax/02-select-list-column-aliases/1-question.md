# sql/02-SELECT 목록과 열 별칭의 유효 범위 — 질문

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

### 1. 별칭은 어디서 태어나나 (왜)

- 열 별칭이 `WHERE` 에서는 안 보이고 `ORDER BY` 에서는 보이는 것을 [01번](../01-logical-query-processing-order/)의 여덟 칸으로 설명할 수 있는가?

### 2. 같은 목록 안에서 앞 별칭 쓰기 (예측)

```sql
SELECT salary * 12 AS annual, annual / 12 AS back FROM emp;
```

- 이 질의는 통과하는가, 아니면 무엇으로 거부되는가?

### 3. ★ 별칭이 열 이름을 가릴 때 — 홀로 설 때와 식에 들어갈 때 (예측)

```sql
-- (A)
SELECT id AS salary FROM emp ORDER BY salary;
-- (B)
SELECT id AS salary FROM emp ORDER BY salary + 0;
```

- (A)와 (B)의 행 순서는 각각 어떻게 되는가?

### 4. `GROUP BY` 에서 이름이 겹치면 (예측)

```sql
SELECT dept_id AS salary, COUNT(*) AS c FROM emp GROUP BY salary;
```

- 이 질의는 통과하는가, 거부된다면 에러가 지목하는 열은 무엇인가?

### 5. `HAVING` 의 별칭 — 방언 (연결)

```sql
SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 1;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 무엇이 나오고, 이식 방향은 어느 쪽이 깨지는가?

### 6. 서수의 범위 밖 (경계)

```sql
SELECT id, name FROM emp ORDER BY 3;
```

- 이 질의가 거부되는 이유를 한 줄로 말할 수 있는가?

### 7. ★ `SELECT *` 가 만든 중복 열 이름 (예측)

```sql
SELECT * FROM (SELECT * FROM emp e JOIN dept d ON e.dept_id = d.id) t;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 이 각각 무엇을 돌려주는가?

### 8. 별칭 이름의 대소문자 (예측)

```sql
SELECT id AS MyCol FROM emp ORDER BY id LIMIT 1;
```

- 두 엔진의 출력 열 이름은 각각 무엇인가?

### 9. 예약어를 별칭으로 (경계)

```sql
SELECT id AS from FROM emp ORDER BY id LIMIT 1;
```

- 두 엔진 중 어느 쪽이 받아 주는가?

### 10. 별칭을 `WHERE` 에서 쓰고 싶을 때 (연결)

- 고치는 방법 둘은 각각 무엇이고, 한 겹 감싸는 쪽이 왜 통하는가?

### 11. `AS` 를 빠뜨리면 (경계)

- `SELECT id, name FROM emp` 에서 쉼표 하나를 빠뜨려 `SELECT id name FROM emp` 가 되면 무엇이 일어나는가?

### 12. 이 주제에서 갈리는 자리 (연결)

- PostgreSQL 18.6 과 MySQL 8.4.10 의 **결과가 다른 자리**를 네 개 들 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
