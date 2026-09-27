# sql/58-`EXPLAIN` 읽기 — 계획 트리의 구조 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

구조를 보는 질의는 기존 `emp`·`dept` 를 읽고, 숫자 칸은 20만 행짜리 `t58_big` 을 쓴다.

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

t58_big : id(PK) 1..200000 · grp = id % 1000 · pad = 'x' 20개
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 계획 트리를 읽는 방향 (왜)

```text
 Limit
   ->  Sort
         ->  HashAggregate
               ->  Hash Join
                     ->  Seq Scan on emp e
                     ->  Hash
                           ->  Seq Scan on dept d
```

- 가장 먼저 도는 노드와 가장 나중에 도는 노드는 각각 무엇인가?

### 2. ★ 01 의 논리 순서와 어긋나는 자리 (연결)

```sql
EXPLAIN SELECT d.name, count(*) FROM emp e JOIN dept d ON e.dept_id = d.id
WHERE e.salary > 100 GROUP BY d.name;
```

- 계획에 `WHERE` 에 해당하는 **독립 노드**가 있는가, 없다면 그 조건은 어디로 갔는가?

### 3. `cost=0.00..3472.00 rows=200000 width=29` (왜)

- 네 숫자는 각각 무엇을 뜻하고, 엔진 자신에게 그 이름을 물어보는 방법은 무엇인가?

### 4. `cost` 의 단위 (경계)

- `cost=3472.00` 은 몇 초인가?

### 5. `SELECT *` 를 `SELECT id` 로 줄이면 (예측)

```sql
EXPLAIN SELECT * FROM t58_big;    -- (A)
EXPLAIN SELECT id FROM t58_big;   -- (B)
```

- (A)와 (B)에서 `cost` 와 `width` 는 각각 어떻게 달라지는가?

### 6. ★ 정렬에 `LIMIT 1` 을 붙이면 (예측)

```sql
EXPLAIN SELECT id FROM t58_big ORDER BY pad;           -- (A)
EXPLAIN SELECT id FROM t58_big ORDER BY pad LIMIT 1;   -- (B)
```

- (B)에서 `Limit` 의 **전체 비용**은 자식 `Sort` 의 어느 숫자와 같은가, 왜인가?

### 7. 정렬 키에 인덱스가 있으면 (예측)

```sql
EXPLAIN SELECT id FROM t58_big ORDER BY id LIMIT 1;
```

- 자식 노드의 전체 비용이 6679 인데 `Limit` 의 전체 비용은 얼마쯤인가?

### 8. ★ 같은 질의, 두 엔진의 출력 형식 (예측)

```sql
EXPLAIN SELECT d.name, count(*) AS c FROM emp e JOIN dept d ON e.dept_id = d.id
WHERE e.salary > 100 GROUP BY d.name ORDER BY c DESC LIMIT 2;
```

- PostgreSQL 의 출력은 몇 줄이고 MySQL 의 출력은 몇 줄인가, 무엇이 그 차이를 만드는가?

### 9. MySQL 표에서 정렬과 집계는 어디에 나오나 (경계)

- 8번의 MySQL 출력에 `Sort`·`Aggregate` 같은 줄이 없는데, 그 두 연산은 어느 칸에서 확인하는가?

### 10. MySQL `type` 칸 (연결)

- `type=ALL` 에 `key=NULL` 이면 무슨 뜻이고, `eq_ref` 는 무엇을 보장하는가?

### 11. `Using filesort` (경계)

- `Extra` 칸의 `Using filesort` 는 디스크에 쓴다는 뜻인가?

### 12. ★ `Index Cond` 와 `Filter` (왜)

```sql
EXPLAIN SELECT grp, count(*) c FROM t58_big WHERE id < 5000
GROUP BY grp HAVING count(*) > 4 ORDER BY c DESC LIMIT 3;
```

- `WHERE id < 5000` 은 계획에서 `Index Cond` 로 나타났다. 그것이 `Filter` 였다면 무엇이 달라지는가?

### 13. `HAVING` 이 붙는 자리 (예측)

- 12번 질의에서 `HAVING count(*) > 4` 는 PostgreSQL 과 MySQL 의 계획에서 각각 어디에 나타나는가?

### 14. `SELECT` 목록은 계획 어디에 있나 (경계)

- 12번 계획에서 `SELECT grp, count(*)` 에 해당하는 노드는 무엇인가?

### 15. 없는 표에 `EXPLAIN` (예측)

```sql
EXPLAIN SELECT * FROM nope;
EXPLAIN SELECT id FROM emp WHERE salay > 1;
```

- 계획이 나오는가, 아니면 무엇이 나오는가?

### 16. `EXPLAIN` 은 질의를 돌리나 (경계)

- `EXPLAIN SELECT` 와 `EXPLAIN ANALYZE SELECT` 는 각각 질의를 실행하는가?

### 17. 한 번 본 계획을 믿어도 되나 (연결)

- 같은 서버·같은 버전·같은 데이터인데 계획이 달라질 수 있는가, 그러면 계획을 근거로 쓸 때 어느 칸을 보아야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
