# sql/50-UPDATE — 조인·서브쿼리를 쓰는 갱신 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

★ 이 편은 **`WHERE` 없는 `UPDATE` 가 주제**이므로 자기 표를 만들어 쓴다. `emp`·`dept` 는 건드리지 않는다.

```text
t50_emp                                        t50_dept
+----+------+---------+--------+-----------+   +----+-------+-------+
| id | name | dept_id | salary | dept_name |   | id | name  | bonus |
+----+------+---------+--------+-----------+   +----+-------+-------+
|  1 | ann  |      10 |    300 | NULL      |   | 10 | sales |    50 |
|  2 | bob  |      10 |    500 | NULL      |   | 20 | dev   |    70 |
|  3 | cho  |      20 |   NULL | NULL      |   | 30 | hr    |    10 |
|  4 | dan  |    NULL |    400 | NULL      |   +----+-------+-------+
+----+------+---------+--------+-----------+

★ id=4 (dan) 은 dept_id 가 NULL 이다 — 어떤 부서와도 안 붙는다.

t50_map                       t50_u
+---------+-------+           +----+----+
|      10 | AAA   |           |  1 | 10 |
|      10 | ZZZ   |           |  2 | 20 |
+---------+-------+           |  3 | 30 |
                              +----+----+
```

아래 질의는 전부 `BEGIN`/`ROLLBACK`(MySQL 은 `START TRANSACTION`/`ROLLBACK`) 으로 감싸 돌린다 — 매번 위 상태에서 시작한다.\
환경 — PostgreSQL 18.6 · MySQL 8.4.10, MySQL 의 `sql_safe_updates` 기본값은 `0` 이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 서로의 문법을 던지면 (예측)

```sql
-- MySQL 에 던진다
UPDATE t50_emp e SET dept_name = d.name FROM t50_dept d WHERE d.id = e.dept_id;
-- PG 에 던진다
UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.dept_name = d.name;
```

- 각각 어떻게 되는가?

### 2. 조인형이 건드리는 행 (예측)

```sql
UPDATE t50_emp SET dept_name = '(old)';            -- 먼저 전부 (old) 로
UPDATE t50_emp e SET dept_name = d.name FROM t50_dept d WHERE d.id = e.dept_id;
```

- 끝난 뒤 `id=4`(dan) 의 `dept_name` 은 무엇인가?

### 3. ★★ 같은 의도, 서브쿼리로 쓰면 (예측)

```sql
UPDATE t50_emp SET dept_name = '(old)';
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id);
```

- 끝난 뒤 `id=4`(dan) 의 `dept_name` 은 무엇이고, 그것이 2번과 왜 다른가?

### 4. 그 차이를 없애려면 (연결)

- 3번의 문을 2번과 같은 결과로 만들려면 무엇을 붙여야 하는가?

### 5. 영향 행 수가 갈리는 자리 (경계)

```sql
-- dept_name 이 전부 NULL 인 상태에서
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id);
```

- PG 는 `UPDATE n`, MySQL 은 `ROW_COUNT()` 로 각각 얼마를 보고하는가?

### 6. 짝이 둘이면 (예측)

```sql
-- t50_map 에는 dept_id=10 이 두 행 있다 (AAA, ZZZ)
UPDATE t50_emp e SET dept_name = m.label FROM t50_map m WHERE m.dept_id = e.dept_id;   -- 조인형
UPDATE t50_emp e SET dept_name = (SELECT m.label FROM t50_map m WHERE m.dept_id = e.dept_id);  -- 서브쿼리형
```

- 두 형태가 각각 어떻게 되는가?

### 7. ★★ `SET` 목록 안에서 서로 참조하면 (예측)

```sql
-- id=1 은 dept_id=10, salary=300 이다
UPDATE t50_emp SET dept_id = salary, salary = dept_id WHERE id = 1;
```

- 두 엔진에서 `(dept_id, salary)` 가 각각 무엇이 되는가?

### 8. `WHERE` 를 빠뜨리면 (예측)

```sql
UPDATE t50_emp SET salary = 0;
```

- 몇 행이 바뀌고, 무엇이 막아 주는가?

### 9. ★ 안전 모드가 막는 것 (경계)

```sql
SET sql_safe_updates = 1;
UPDATE t50_emp SET salary = 0;                        -- (a)
UPDATE t50_emp SET salary = 0 WHERE name = 'ann';     -- (b)
UPDATE t50_emp SET salary = 0 WHERE id = 1;           -- (c)
UPDATE t50_emp SET salary = 0 WHERE salary > 0 LIMIT 10;  -- (d)
```

- 네 문 중 통과하는 것은 무엇이고, 그 기준은 「몇 행을 바꾸나」인가?

### 10. PG 에 같은 변수가 있나 (경계)

- PostgreSQL 18.6 에서 `SET sql_safe_updates = 1` 은 도는가?

### 11. `UPDATE` 가 중간에 제약을 어기면 (예측)

```sql
-- t50_u 는 id 가 기본키다
UPDATE t50_u SET id = 99 WHERE v >= 20;     -- 두 행이 다 99 가 되려 한다
```

- 두 엔진에서 각각 무엇이 일어나고, 끝난 뒤 표는 어떤 모습인가?

### 12. 거기에 `IGNORE` 를 붙이면 (예측)

```sql
UPDATE IGNORE t50_u SET id = 99 WHERE v >= 20;
SHOW WARNINGS;
```

- MySQL 8.4.10 에서 표가 어떻게 되는가?

### 13. `ORDER BY`·`LIMIT` 은 어디에 붙나 (경계)

```sql
UPDATE t50_emp SET salary = 0 ORDER BY id LIMIT 1;                                  -- (a)
UPDATE t50_emp e JOIN t50_dept d ON d.id=e.dept_id SET e.salary = 0 ORDER BY e.id LIMIT 1;  -- (b)
```

- 두 문은 두 엔진에서 각각 어떻게 되는가?

### 14. 두 열을 안전하게 교환하려면 (연결)

- 7번의 관용구를 쓰지 않고 두 열의 값을 교환하려면 무엇을 쓰는가? 그 방법은 이식 가능한가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
