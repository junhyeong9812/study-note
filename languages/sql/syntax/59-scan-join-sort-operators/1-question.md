# sql/59-스캔·조인·정렬 연산자 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

이 편만은 `emp`·`dept`(4행·3행)를 못 쓴다 — 표가 작으면 엔진이 언제나 전체 스캔을 고른다.

```text
t59_big  (200,000행)                t59_mid (50,000행)      t59_small (10행)
+--------+-------+-------+-----+    +-------+------+-----+  +------+------+
| id PK  | grp   | val   | pad |    | id PK | ref  | val |  | id   | ref  |
+--------+-------+-------+-----+    +-------+------+-----+  +------+------+
| 1      | 1     | 1     | xx… |    | 1     | 2    | 1   |  | 1    | 3    |
| …      | …     | …     |     |    | …     | …    | …   |  | …    | …    |
| 200000 | 0     | 0     | xx… |    | 50000 | 1e5  | 5e4 |  | 10   | 30   |
+--------+-------+-------+-----+    +-------+------+-----+  +------+------+
  grp: 값마다 200행 · 인덱스 있음       ref·val 에는 인덱스가 없다
  val: 값마다 4행   · 인덱스 없음
```

PG 계획은 전부 `max_parallel_workers_per_gather = 0`(병렬 끔)에서 찍은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 스캔 연산자 네 가지 (연결)

- 표의 행에 닿는 방법 넷은 무엇이고, 그중 하나는 어느 엔진에만 있는가?

### 2. 0.1% 를 고르면 (예측)

```sql
EXPLAIN SELECT * FROM t59_big WHERE grp = 7;     -- 200행 / 200,000
```

- PostgreSQL 과 MySQL 의 계획은 각각 무엇인가?

### 3. ★ 90% 를 고르면 (예측)

```sql
EXPLAIN SELECT * FROM t59_big WHERE grp < 900;   -- 180,000행 / 200,000
```

- 인덱스가 걸려 있는데도 무엇이 뽑히고, MySQL 의 `possible_keys` 와 `key` 칸은 각각 무엇인가?

### 4. ★ 어디서 갈리나 (예측)

- `grp < N` 의 N 을 키워 갈 때 PostgreSQL 은 몇 % 근처에서, MySQL 은 몇 % 근처에서 인덱스를 놓는가?

### 5. 두 엔진의 전환점이 다른 이유 (왜)

- PostgreSQL 이 훨씬 늦게까지 인덱스를 쓰는 이유는 무엇인가?

### 6. ★ 전환점 근처에서 같은 스크립트를 8번 돌리면 (예측)

- 같은 서버·같은 버전·같은 생성 코드로 `grp < 520` 의 계획을 8판 찍으면 결과가 어떻게 나오는가?

### 7. 6번의 원인 (왜)

- 데이터도 버전도 안 바꿨는데 연산자가 갈린 원인은 무엇이고, 그러면 계획을 근거로 쓸 때 어느 칸을 보아야 하는가?

### 8. 표를 아예 안 읽는 스캔 (경계)

```sql
EXPLAIN SELECT grp FROM t59_big WHERE grp = 7;
```

- MySQL 의 `Extra` 칸에 무엇이 뜨고, PostgreSQL 에서는 그것이 무슨 이름인가?

### 9. ★ 바깥 표를 10행에서 50,000행으로 키우면 (예측)

```sql
EXPLAIN SELECT s.id, b.pad FROM t59_small s JOIN t59_big b ON b.id = s.ref;   -- (A) 바깥 10행
EXPLAIN SELECT m.id, b.pad FROM t59_mid m   JOIN t59_big b ON b.id = m.ref;   -- (B) 바깥 50,000행
```

- PostgreSQL 은 (A)와 (B)에 각각 어떤 조인 연산자를 고르는가?

### 10. 중첩 루프의 비용 구조 (왜)

```sql
SET enable_mergejoin = off;
EXPLAIN SELECT s.id, b.pad FROM t59_small s JOIN t59_big b ON b.id = s.ref;
-- Nested Loop (cost=0.42..85.48 …)
--   -> Seq Scan on t59_small s (cost=0.00..1.10 rows=10 …)
--   -> Index Scan using t59_big_pkey on t59_big b (cost=0.42..8.44 rows=1 …)
```

- 85.48 이라는 숫자는 계획의 어느 숫자들에서 나오는가?

### 11. 양쪽 조인 키에 인덱스가 있으면 (예측)

```sql
EXPLAIN SELECT b.id, m.ref FROM t59_big b JOIN t59_mid m ON m.id = b.id;   -- 둘 다 기본키
```

- 5만 행짜리 조인인데 무엇이 뽑히고, 계획에 없는 노드는 무엇인가?

### 12. 해시 표는 어느 쪽으로 만드나 (경계)

```sql
EXPLAIN SELECT count(*) FROM t59_mid m JOIN t59_big b ON b.val = m.val;   -- val 에 인덱스 없음
```

- 계획의 `Hash` 노드 아래에 있는 표는 20만 행짜리인가 5만 행짜리인가?

### 13. ★ MySQL 에서 머지 조인을 찾으면 (경계)

- 9·11번 질의를 MySQL 에 던지면 각각 무슨 연산자가 나오는가?

### 14. MySQL 의 해시 조인 추정 (예측)

```sql
EXPLAIN FORMAT=TREE SELECT count(*) FROM t59_mid m JOIN t59_big b ON b.val = m.val;
```

- `Inner hash join` 의 추정 행 수는 얼마이고, 실제로 세어 보면 몇 행인가?

### 15. `GROUP BY` 가 정렬을 해 주나 (예측)

```sql
EXPLAIN SELECT grp, count(*) FROM t59_big GROUP BY grp;              -- (A)
EXPLAIN SELECT grp, count(*) c FROM t59_big GROUP BY grp ORDER BY grp; -- (B)
```

- (A)의 결과는 `grp` 순서로 나오는가, (B)에는 어떤 노드가 더 붙는가?

### 16. 해시 집계를 끄면 (예측)

```sql
SET enable_hashagg = off;
EXPLAIN SELECT grp, count(*) FROM t59_big GROUP BY grp;
```

- 집계 노드만 바뀌는가, 그 아래 스캔도 바뀌는가?

### 17. `SELECT DISTINCT grp` 에서 두 엔진이 읽는 행 수 (예측)

```sql
EXPLAIN SELECT DISTINCT grp FROM t59_big;
```

- PostgreSQL 과 MySQL 이 각각 몇 행을 읽는다고 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
