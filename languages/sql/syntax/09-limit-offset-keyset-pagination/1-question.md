# sql/09-LIMIT·OFFSET·FETCH FIRST 와 키셋 페이지네이션 — 질문

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

비용 측정 문항(6·7번)은 `study` 안에 만든 **20만 행 세션 임시 표**(`big(id PK, val)`)를 쓴다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `LIMIT` 이 일을 줄여 주나 (왜)

```sql
SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 1;
```

- `ann`(id 1)은 이 질의에서 어디까지 참여했는가?

### 2. `FETCH FIRST` 방언 (예측)

```sql
SELECT id, name FROM emp ORDER BY id FETCH FIRST 2 ROWS ONLY;
```

- 두 엔진 중 어느 쪽이 받아 주는가?

### 3. `LIMIT 1, 2` 방언 (예측)

```sql
SELECT id, name FROM emp ORDER BY id LIMIT 1, 2;
```

- PostgreSQL 18.6 의 에러 메시지에 무엇이 들어 있는가?

### 4. `OFFSET` 단독과 `LIMIT ALL` (경계)

```sql
SELECT id FROM emp ORDER BY id OFFSET 2;    -- (A)
SELECT id FROM emp ORDER BY id LIMIT ALL;   -- (B)
```

- 두 질의는 각각 어느 엔진에서 도는가?

### 5. `WITH TIES` (예측)

```sql
SELECT id, dept_id FROM emp ORDER BY dept_id FETCH FIRST 1 ROWS WITH TIES;
```

- 「1행만」이라고 했는데 몇 행이 나오는가?

### 6. ★ `OFFSET` 이 깊어지면 (예측)

```sql
EXPLAIN ANALYZE SELECT id FROM big ORDER BY id LIMIT 10 OFFSET 100000;
```

- 계획에서 **자식 노드의 `actual rows`** 는 얼마인가?

### 7. ★ 키셋으로 바꾸면 (예측)

```sql
EXPLAIN ANALYZE SELECT id FROM big WHERE id > 100000 ORDER BY id LIMIT 10;
```

- 6번과 결과 행은 같은데 자식 노드의 `actual rows` 는 얼마인가?

### 8. ★ 페이지 사이에 행이 들어오면 (예측)

```sql
-- page1
SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 0;
INSERT INTO emp VALUES (0,'zed',10,100);
-- page2
SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 2;
```

- page2 에 무엇이 나오고, 1페이지와 겹치는 행이 있는가?

### 9. 행이 삭제되면 (예측)

- 8번에서 `INSERT` 대신 `DELETE FROM emp WHERE id = 1` 이 일어나면 page2 에 무엇이 나오는가?

### 10. 키셋이 8·9번을 고치나 (연결)

```sql
SELECT id, name FROM emp WHERE id > 2 ORDER BY id LIMIT 2;
```

- 같은 시점에 이 질의는 무엇을 주는가, 왜 영향을 안 받는가?

### 11. 복합 키 키셋 (경계)

```sql
SELECT id, dept_id FROM emp WHERE (dept_id, id) > (10, 1) ORDER BY dept_id, id LIMIT 2;
```

- 결과는 무엇이고, `dan`(dept_id NULL)이 안 나오는 이유는 무엇인가?

### 12. 키셋이 못 고치는 것 (연결)

- 키셋으로 바꾸면 포기해야 하는 기능 둘은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
