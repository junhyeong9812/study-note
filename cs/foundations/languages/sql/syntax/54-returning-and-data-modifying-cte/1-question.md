# sql/54-RETURNING 과 변경문을 품은 CTE — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

★ **이 주제는 한쪽에서만 결론이 선다.** MySQL 8.4.10 에는 `RETURNING` 도, CTE 안의 변경문도 없다.\
아래 동작 문항의 답은 전부 PostgreSQL 18.6 의 것이다.

```text
t54_a                            t54_log
+----+------+-----+              +----+------+-----+-------+
| id | name | qty |              | id | name | qty | note  |
+----+------+-----+              +----+------+-----+-------+
|  1 | ann  |  10 |              (비어 있다)
|  2 | bob  |  20 |
|  3 | cho  |  30 |   <- qty >= 30
|  4 | dan  |  40 |   <- qty >= 30
+----+------+-----+
```

아래 질의는 전부 `BEGIN`/`ROLLBACK` 으로 감싸 돌린다 — 매번 위 상태에서 시작한다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `RETURNING` 은 어느 문에 붙나 (예측)

```sql
INSERT INTO t54_a VALUES (5,'eve',50)        RETURNING id, name, qty;
UPDATE t54_a SET qty = qty + 1 WHERE id <= 2 RETURNING id, name, qty;
DELETE FROM t54_a WHERE id = 5               RETURNING id, name, qty;
```

- 세 문이 두 엔진에서 각각 어떻게 되고, PG 에서 각각 무엇을 돌려주는가?

### 2. 별칭 없이 쓴 열은 앞 값인가 뒤 값인가 (경계)

- 1번의 `UPDATE` 가 돌려준 `qty` 는 `+1` 하기 전인가 후인가? `DELETE` 는?

### 3. ★ `OLD` 와 `NEW` (예측)

```sql
UPDATE t54_a SET qty = qty*2 WHERE id <= 2 RETURNING id, OLD.qty AS before, NEW.qty AS after;
INSERT INTO t54_a VALUES (9,'new',90)      RETURNING id, OLD.qty AS before, NEW.qty AS after;
DELETE FROM t54_a WHERE id=4               RETURNING id, OLD.qty AS before, NEW.qty AS after;
```

- 세 문의 `before`·`after` 는 각각 무엇인가? 이 문법은 어느 버전부터인가?

### 4. 변경문을 `FROM` 에 놓으면 (경계)

```sql
SELECT * FROM (DELETE FROM t54_a WHERE id=4 RETURNING *) AS d;
SELECT (SELECT count(*) FROM (WITH d AS (DELETE FROM t54_a WHERE id=4 RETURNING *) SELECT * FROM d) AS s) AS n;
```

- 두 문은 각각 어떻게 되는가?

### 5. ★★ 같은 문 안에서 세면 (예측)

```sql
WITH moved AS (DELETE FROM t54_a WHERE qty >= 30 RETURNING *),
     ins   AS (INSERT INTO t54_log SELECT id, name, qty, 'moved' FROM moved RETURNING *)
SELECT (SELECT count(*) FROM t54_a) AS a_seen_in_same_stmt,
       (SELECT count(*) FROM moved) AS moved_rows,
       (SELECT count(*) FROM ins)   AS logged_rows;
```

- 세 숫자는 각각 얼마인가? 문이 끝난 뒤 `t54_a` 는 몇 행인가?

### 6. 왜 그런가 (왜)

- 5번처럼 설계한 이유는 무엇인가? PostgreSQL 문서는 그것을 어떻게 적는가?

### 7. 두 번 참조하면 두 번 도나 (예측)

```sql
WITH d AS (DELETE FROM t54_a WHERE id=4 RETURNING *)
SELECT (SELECT count(*) FROM d) AS c1, (SELECT count(*) FROM d) AS c2;
```

- `c1`·`c2` 는 각각 얼마이고, 몇 행이 지워지는가?

### 8. ★ 아무도 안 읽으면 (예측)

```sql
WITH gone AS (DELETE FROM t54_a WHERE id=4 RETURNING *)
SELECT 1 AS dummy;
```

- `id=4` 는 지워지는가?

### 9. [32 번](../32-cte-with-clause/)의 인라인 규칙과의 관계 (연결)

- 읽기 전용 CTE 는 참조가 한 번이면 인라인되고 둘이면 벽이 선다. 변경 CTE 에도 그 규칙이 적용되는가?

### 10. 같은 행을 두 조각이 건드리면 (예측)

```sql
WITH u1 AS (UPDATE t54_a SET qty = 100 WHERE id=1 RETURNING id),
     u2 AS (UPDATE t54_a SET qty = 200 WHERE id=1 RETURNING id)
SELECT (SELECT count(*) FROM u1) AS u1_rows, (SELECT count(*) FROM u2) AS u2_rows;
```

- 끝난 뒤 `id=1` 의 `qty` 는 얼마인가? 그 값을 코드에서 기대해도 되는가?

### 11. MySQL 에 무엇이 있고 무엇이 없나 (경계)

```sql
WITH moved AS (DELETE FROM t54_a WHERE qty >= 30 RETURNING *) SELECT * FROM moved;   -- (a)
WITH moved AS (SELECT * FROM t54_a WHERE qty >= 30) DELETE FROM t54_a WHERE id IN (SELECT id FROM moved);  -- (b)
```

- MySQL 8.4.10 에서 두 문은 각각 어떻게 되는가?

### 12. MySQL 에서 「옮기기」를 쓰면 (연결)

- 3번 절의 「지우면서 보관 표에 넣기」를 MySQL 로 옮기면 몇 문이 되고, 순서를 어떻게 잡아야 하는가?

### 13. 자동 생성 키 회수 (연결)

- `INSERT … RETURNING id` 를 MySQL 에서 무엇으로 대신하고, 그것이 왜 동등물이 아닌가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
