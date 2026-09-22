# sql/33-재귀 CTE — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 SQL 주제들이 공유한다. **새로 만드는 표는 없다** — 계층은 **CTE 안에서** 만든다.

```sql
-- 이 파일의 모든 문항이 이 둘 중 하나를 머리에 달고 있다
staff AS (SELECT id, name, CASE id WHEN 1 THEN NULL WHEN 2 THEN 1
                                   WHEN 3 THEN 1 WHEN 4 THEN 3 END AS mgr_id FROM emp)
cyc   AS (SELECT id, name, CASE id WHEN 1 THEN 4    WHEN 2 THEN 1
                                   WHEN 3 THEN 1 WHEN 4 THEN 3 END AS mgr_id FROM emp)
```

```text
 staff — 나무                       cyc — 고리
      ann(1)                        ann(1) -> cho(3) -> dan(4) -> ann(1) -> ...
      /    \                              \
  bob(2)  cho(3)                          bob(2)
             \
            dan(4)
```

★ **아래에 무한 재귀를 묻는 문항이 있다. 직접 돌려 볼 때는 반드시 안전장치를 먼저 건다** —\
MySQL 은 `SET SESSION cte_max_recursion_depth = 5;`, PG 는 `SET statement_timeout = '300ms';`.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 조각과 회차 (예측)

```sql
WITH RECURSIVE staff AS (...), tree AS (
  SELECT id, name, mgr_id, 1 AS lvl FROM staff WHERE mgr_id IS NULL
  UNION ALL
  SELECT s.id, s.name, s.mgr_id, t.lvl + 1 FROM staff s JOIN tree t ON s.mgr_id = t.id
) SELECT lvl, id, name FROM tree ORDER BY lvl, id;
```

- 결과의 `lvl` 열은 무엇이 나오고, 엔진은 **몇 회차**를 돌고 **왜** 멈추는가?

### 2. `RECURSIVE` 를 빼면 (예측)

- 위 질의에서 `RECURSIVE` 만 지우면 두 엔진은 각각 무엇을 말하는가? **MySQL 쪽 메시지가 위험한 이유**는?

### 3. 고리에 `UNION` (예측)

```sql
WITH RECURSIVE cyc AS (...), t AS (
  SELECT id, name FROM cyc WHERE id = 1
  UNION
  SELECT c.id, c.name FROM cyc c JOIN t ON c.mgr_id = t.id
) SELECT * FROM t;
```

- 이 질의는 끝나는가? 끝난다면 **무엇이 끝나게 했는가**?

### 4. 같은 질의를 `UNION ALL` 로 (경계)

- 위에서 `UNION` 을 `UNION ALL` 로 바꾸면 무슨 일이 일어나고, 그것을 **안전하게** 시험하려면 무엇을 먼저 해야 하는가?

### 5. 두 엔진이 끊는 방식 (연결)

- `SHOW cte_max_recursion_depth` 를 두 엔진에 던지면 각각 무엇이 나오고, 그 사실이 **운영에서 무엇을 뜻하는가**?

### 6. 깊이 열로 끊기 (예측)

```sql
WITH RECURSIVE cyc AS (...), t AS (
  SELECT id, name, 1 AS lvl FROM cyc WHERE id = 1
  UNION ALL
  SELECT c.id, c.name, t.lvl + 1 FROM cyc c JOIN t ON c.mgr_id = t.id WHERE t.lvl < 4
) SELECT * FROM t;
```

- 몇 행이 나오고, 그 결과에서 **사이클을 어떻게 알아보는가**?

### 7. 깊이 열과 `UNION` 을 같이 쓰면 (왜)

- 깊이 열을 붙인 질의에서 `UNION` 이 고리를 못 끊는 이유는 무엇인가?

### 8. `LIMIT` 이 멈춰 주나 (예측)

```sql
-- (A) 바깥 LIMIT
WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t) SELECT * FROM t LIMIT 5;
-- (B) 본문 안 LIMIT
WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t LIMIT 5) SELECT * FROM t;
```

- 두 엔진 × 두 형태, 네 칸의 결과는 각각 무엇인가?

### 9. 재귀 항에 못 쓰는 것 (경계)

- `FROM t a, t b` · `SELECT MAX(n)+1 FROM t` · `LEFT JOIN t` 셋은 각각 왜 거부되는가?

### 10. MySQL 만 터지는 자리 (예측)

```sql
WITH RECURSIVE p(n, path) AS (
  SELECT 1, 'a' UNION ALL SELECT n+1, CONCAT(path,'b') FROM p WHERE n < 5
) SELECT * FROM p;
```

- 두 엔진의 결과는 무엇이고, MySQL 쪽은 어떻게 고치는가?

### 11. PG 전용 문법 (연결)

- `SEARCH DEPTH FIRST BY id SET ord` 와 `CYCLE id SET is_cycle USING path` 는 각각 무엇을 해 주고, MySQL 에 던지면 무엇이 나오는가?

### 12. 방향 뒤집기 (예측)

- 「`dan` 의 상사들을 전부」를 뽑으려면 조인 조건을 어떻게 바꾸고, 그 재귀는 **무엇 때문에** 멈추는가?

### 13. 어디까지가 이 주제인가 (경계)

- 「최단 경로를 재귀 CTE 로 구하라」는 요구가 오면 이 주제와 `algorithm/11-bfs`·`12-dfs` 중 어디를 봐야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
