# sql/48-뷰와 구체화 뷰 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

이 편은 기존 `emp`·`dept` 를 바꾸지 않기 위해 **같은 4행을 담은 `t48_emp`** 를 따로 만들어 쓴다.

```text
t48_emp                             emp (기존 · 건드리지 않는다)
+----+------+---------+--------+    +----+------+---------+--------+
| id | name | dept_id | salary |    | id | name | dept_id | salary |
+----+------+---------+--------+    +----+------+---------+--------+
|  1 | ann  |      10 |    300 |    |  1 | ann  |      10 |    300 |
|  2 | bob  |      10 |    500 |    |  2 | bob  |      10 |    500 |
|  3 | cho  |      20 |   NULL |    |  3 | cho  |      20 |   NULL |
|  4 | dan  |    NULL |    400 |    |  4 | dan  |    NULL |    400 |
+----+------+---------+--------+    +----+------+---------+--------+
```

```sql
CREATE VIEW v48_high AS SELECT id, name, salary FROM t48_emp WHERE salary >= 400;
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 뷰는 무엇을 저장하나 (왜)

```sql
CREATE VIEW v48_high AS SELECT id, name, salary FROM t48_emp WHERE salary >= 400;
SELECT pg_get_viewdef('v48_high', true);
```

- 두 번째 줄이 돌려주는 것은 행인가 문장인가, 그것이 성능에 뜻하는 바는 무엇인가?

### 2. 뷰에 대고 `EXPLAIN` 을 찍으면 (예측)

```sql
EXPLAIN SELECT * FROM v48_p WHERE id = 2;   -- v48_p: emp 위에 만든 같은 모양의 뷰
```

- 계획에 `v48_p` 라는 이름이 나오는가?

### 3. ★ 같은 순간의 뷰와 구체화 뷰 (예측)

```sql
UPDATE t48_emp SET salary = 900 WHERE name = 'ann';
CREATE MATERIALIZED VIEW mv48_high AS SELECT id, name, salary FROM t48_emp WHERE salary >= 400;
UPDATE t48_emp SET salary = 100 WHERE name = 'ann';
SELECT * FROM v48_high;      -- (A)
SELECT * FROM mv48_high;     -- (B)
```

- (A)와 (B)는 각각 몇 행인가?

### 4. 구체화 뷰에 행을 넣으면 (예측)

```sql
INSERT INTO mv48_high VALUES (9,'zed',999);
```

- 무엇이 출력되는가?

### 5. ★ MySQL 에 구체화 뷰를 만들면 (예측)

```sql
CREATE MATERIALIZED VIEW mv48_high AS SELECT id FROM emp;
```

- MySQL 8.4.10 이 돌려주는 것은 무엇이고, 그 에러 번호가 뜻하는 바는 무엇인가?

### 6. 구체화 뷰가 없는 엔진에서 그 자리를 메우는 법 (연결)

- MySQL 에서 「어제 집계해 둔 결과를 빠르게 읽는다」를 만들려면 무엇과 무엇을 쓰고, PG 의 `REFRESH` 자리에는 무엇이 오는가?

### 7. 집계 뷰에 `INSERT` (예측)

```sql
CREATE VIEW v48_agg AS SELECT dept_id, count(*) AS cnt FROM t48_emp GROUP BY dept_id;
INSERT INTO v48_agg VALUES (30, 1);
```

- 두 엔진의 에러는 각각 무엇을 말해 주는가?

### 8. 어떤 뷰가 갱신 가능한지 외우지 않고 아는 법 (연결)

- 카탈로그의 어느 표에 무엇을 물으면 되는가?

### 9. ★ `WITH CHECK OPTION` 이 없을 때 (예측)

```sql
INSERT INTO v48_high VALUES (6,'fox',100);   -- v48_high 는 salary >= 400 만 보여 준다
SELECT * FROM v48_high;
SELECT * FROM t48_emp WHERE id = 6;
```

- 세 문의 결과는 각각 무엇이고, 무엇이 「조용한」가?

### 10. `WITH CHECK OPTION` 을 붙이면 (예측)

```sql
CREATE VIEW v48_high_chk AS SELECT id, name, salary FROM t48_emp WHERE salary >= 400 WITH CHECK OPTION;
INSERT INTO v48_high_chk VALUES (7,'gil',100);
UPDATE v48_high_chk SET salary = 10 WHERE id = 2;
```

- 두 문은 각각 어떻게 되는가?

### 11. ★ 뷰가 참조하는 표를 지우면 (예측)

```sql
DROP TABLE t48_emp;
```

- PostgreSQL 18.6 과 MySQL 8.4.10 의 반응은 어떻게 갈리는가?

### 12. MySQL 에서 뷰가 쓰는 열을 지운 뒤 (예측)

```sql
ALTER TABLE t48_emp DROP COLUMN salary;
SELECT * FROM v48_high;
```

- 두 문 중 어느 쪽에서 무엇이 터지는가?

### 13. `SELECT *` 로 만든 뷰에 열을 추가하면 (경계)

```sql
CREATE VIEW v48_star AS SELECT * FROM t48_emp;
ALTER TABLE t48_emp ADD COLUMN memo text;
SELECT * FROM v48_star;
```

- `memo` 열이 보이는가, 왜인가?

### 14. `REFRESH … CONCURRENTLY` 의 조건 (경계)

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv48_high;
```

- 무엇이 출력되고, 무엇을 만들어야 통과하는가?

### 15. 뷰로 감싸면 빨라지나 (왜)

- 무거운 조인을 뷰로 감쌌을 때 읽기 비용은 어떻게 되는가, 그러면 뷰의 값어치는 어디에 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
