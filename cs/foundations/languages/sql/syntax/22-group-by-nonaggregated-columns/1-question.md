# sql/22-`GROUP BY` 와 비집계 열 규칙 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다.\
`emp.id` 는 기본키, `dept.name` 은 `UNIQUE NOT NULL` 이다.

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

### 1. 왜 그룹만 보이나 (왜)

- `GROUP BY` 뒤의 칸에서 원래 행을 못 보는 이유를 [01번](../01-logical-query-processing-order/)의 처리 순서로 설명하면?

### 2. ★ 비집계 열 (예측)

```sql
SELECT dept_id, name FROM emp GROUP BY dept_id;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 에서 각각 어떻게 되는가?

### 3. `GROUP BY` 가 없으면 (예측)

```sql
SELECT name, COUNT(*) FROM emp;
```

- `GROUP BY` 가 아예 없는데도 거부되는가? MySQL 의 에러 번호는 2번과 같은가?

### 4. 같은 규칙이 걸리는 세 자리 (경계)

- 비집계 열 규칙이 걸리는 절은 `SELECT` 말고 또 어디인가?

### 5. ★ 설정을 끄면 (예측)

```sql
SET SESSION sql_mode = REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', '');
SELECT dept_id, name FROM emp GROUP BY dept_id;
```

- 돌아가는가? `dept_id=10` 그룹에서 `name` 은 무엇이 나오고, 그 값은 보장되는가?

### 6. ★ 10회 돌려 같았다면 (왜)

- 같은 질의를 10회 돌려 값이 한 번도 안 바뀌었다면 「안정적」이라고 적어도 되는가?

### 7. `ORDER BY` 로 고를 수 있나 (경계)

- 5번에서 `bob` 이 나오게 하려고 `ORDER BY name DESC` 를 붙이면 되는가?

### 8. 기본키로 묶기 (예측)

```sql
SELECT id, name, dept_id, salary, COUNT(*) FROM emp GROUP BY id;
```

- 이 문은 두 엔진에서 도는가? 돈다면 왜 허용되는가?

### 9. ★ 종속성의 경계 (예측)

```sql
-- (A) dept.name 은 UNIQUE NOT NULL 이다
SELECT d.id, d.name FROM dept d GROUP BY d.name;
-- (B) e.id 가 정해지면 d.name 도 하나로 정해진다
SELECT e.id, e.name, d.name FROM emp e JOIN dept d ON e.dept_id = d.id GROUP BY e.id;
```

- (A)와 (B)는 두 엔진에서 각각 어떻게 되는가?

### 10. 설정을 끄는 대신 (연결)

- 비집계 열이 정말 아무거나 좋을 때 두 엔진 모두에서 쓸 수 있는 형태는 무엇인가?

### 11. `GROUP BY` 에 쓸 수 있는 것 (경계)

- `GROUP BY` 에 표현식·`SELECT` 의 열 별칭·서수·집계 함수를 각각 쓸 수 있는가?

### 12. `NULL` 은 몇 그룹인가 (연결)

- `GROUP BY dept_id` 는 몇 그룹이고 `COUNT(DISTINCT dept_id)` 는 얼마인가? 왜 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
