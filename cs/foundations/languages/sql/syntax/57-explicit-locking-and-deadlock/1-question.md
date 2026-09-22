# sql/57-명시적 잠금과 교착 — `FOR UPDATE`·`SKIP LOCKED`·`NOWAIT` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.\
> **엔진** — PostgreSQL 18.6 · MySQL 8.4.10. **두 엔진의 답이 다른 문항이 많다** — 양쪽을 다 말해야 정답이다.\
> ★ **직접 돌려 볼 거면 먼저 타임아웃을 걸어라** — `SET lock_timeout='3s';` / `SET SESSION innodb_lock_wait_timeout=3;`

```text
t57_q (큐 · 4행)                 t57_lk / t57_ix (3행씩 · 같은 데이터)
+----+---------+-------+         +----+-----+------+
| id | payload | state |         | id | grp | memo |
+----+---------+-------+         +----+-----+------+
|  1 | job-a   | ready |         |  1 |  10 | x    |
|  2 | job-b   | ready |         |  2 |  20 | y    |
|  3 | job-c   | ready |         |  3 |  30 | z    |
|  4 | job-d   | ready |         +----+-----+------+
+----+---------+-------+         t57_ix 에만 grp 인덱스가 있다
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 잠금 대기의 기본값 (경계)

```sql
SHOW lock_timeout;                        -- PG
SELECT @@innodb_lock_wait_timeout;        -- MySQL
```

- 두 엔진의 기본값은 각각 얼마이고, 그것이 실험할 때 무슨 뜻인가?

### 2. ★ 남이 쥔 행을 그냥 `FOR UPDATE` 로 집으면 (예측)

```text
A: BEGIN; SELECT ... WHERE id = 1 FOR UPDATE;
B: BEGIN; SELECT ... WHERE id = 1 FOR UPDATE;
```

- 타임아웃을 3초로 걸어 뒀을 때 B 는 두 엔진에서 각각 무엇을 받는가?

### 3. ★ `NOWAIT` 을 붙이면 (예측)

```sql
SELECT id, payload FROM t57_q WHERE id = 1 FOR UPDATE NOWAIT;
```

- 두 엔진에서 각각 무슨 에러가 나오고, 2번과 무엇이 다른가?

### 4. ★ `SKIP LOCKED` 를 붙이면 (예측)

```sql
SELECT id, payload FROM t57_q WHERE state = 'ready' ORDER BY id FOR UPDATE SKIP LOCKED;
```

- A 가 1번을 쥔 상태에서 B 는 무엇을 받는가?

### 5. 큐 소비 — 두 워커가 무엇을 집나 (예측)

```sql
SELECT id, payload FROM t57_q WHERE state='ready' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED;
```

- 두 워커가 거의 동시에 이 질의를 던지면 각각 무엇을 집는가?

### 6. `SKIP LOCKED` 없이 같은 큐를 돌리면 (예측)

- 5번에서 `SKIP LOCKED` 만 빼면 두 번째 워커는 어떻게 되는가?

### 7. ★ `SKIP LOCKED` 를 일반 조회에 쓰면 (왜)

- `SELECT count(*) … FOR UPDATE SKIP LOCKED` 같은 질의가 위험한 이유는 무엇인가?

### 8. `SKIP LOCKED` 와 `NOWAIT` 을 같이 쓰면 (예측)

```sql
SELECT id FROM t57_lk WHERE id = 1 FOR UPDATE SKIP LOCKED NOWAIT;
```

- 두 엔진에서 각각 어떻게 되는가?

### 9. ★ 인덱스 없는 열로 잠그면 (예측)

```text
A: BEGIN; SELECT id, grp FROM t57_lk WHERE grp = 10 FOR UPDATE;   -- grp 에 인덱스 없음, 1행만 맞는다
B: BEGIN; SELECT id, grp FROM t57_lk WHERE id  = 3  FOR UPDATE;
```

- MySQL 에서 B 는 어떻게 되고, 같은 것을 `t57_ix`(인덱스 있음)로 하면 어떻게 되는가?

### 10. `data_locks` 의 `INDEX_NAME` 칸이 말하는 것 (연결)

- 9번에서 잠금이 걸린 대상이 무엇인지, 그 칸이 어떻게 알려 주는가?

### 11. 같은 실험을 PostgreSQL 에서 하면 (예측)

- PG 에서 B 는 막히는가? 그리고 `pg_locks` 에는 무엇이 보이는가?

### 12. ★ 잠긴 범위에 남이 `INSERT` 하면 (예측)

```text
A: BEGIN; SELECT id, grp FROM t57_ix WHERE grp BETWEEN 10 AND 20 FOR UPDATE;   -> 2행
B: BEGIN; INSERT INTO t57_ix VALUES (5, 15, 'new');
A: 같은 SELECT 를 다시
```

- MySQL 과 PG 에서 B 의 `INSERT` 와 A 의 재조회는 각각 어떻게 되는가?

### 13. PG 를 `REPEATABLE READ` 로 올려 12번을 하면 (예측)

- A 의 재조회는 몇 행인가?

### 14. ★ 교착을 일부러 만들면 (예측)

```text
A: BEGIN; SELECT ... id = 1 FOR UPDATE;
B: BEGIN; SELECT ... id = 2 FOR UPDATE;
A: SELECT ... id = 2 FOR UPDATE;
B: SELECT ... id = 1 FOR UPDATE;
```

- 두 엔진에서 각각 누가 무슨 에러를 받고, 나머지 한쪽은 어떻게 되는가?

### 15. `SHOW ENGINE INNODB STATUS` 에서 건질 것 (연결)

- 이 출력의 `LATEST DETECTED DEADLOCK` 절에서 읽어 낼 수 있는 것을 셋 대라.

### 16. 교착을 줄이는 처방 (연결)

- 14번의 교착을 애초에 안 나게 하려면 무엇을 바꾸는가?

### 17. 잠금 단계의 수 (경계)

```sql
SELECT id FROM t57_lk WHERE id = 1 FOR NO KEY UPDATE;
```

- 두 엔진에서 각각 어떻게 되는가?

### 18. 집계와 함께 쓰면 (예측)

```sql
SELECT count(*) FROM t57_lk FOR UPDATE;
```

- 두 엔진에서 각각 무엇이 나오는가?

### 19. 외부 조인의 NULL 쪽에 붙이면 (예측)

```sql
SELECT id FROM t57_lk LEFT JOIN t57_ix USING (id) FOR UPDATE;
```

- 두 엔진에서 각각 어떻게 되고, PG 에서는 무엇으로 고치는가?

### 20. 자동 커밋으로 `FOR UPDATE` 를 던지면 (왜)

- `BEGIN` 없이 잠금 읽기를 하면 잠금은 언제까지 유지되는가?

### 21. 잠금으로 못 막는 것 (연결)

- `FOR UPDATE` 로는 못 막는 경쟁이 있다. 무엇이고 무엇으로 막는가?

### 22. 분산 락과의 경계 (연결)

- 이 편의 행 잠금으로 해결되지 않는 자리는 어디이고, 그 자리의 정본은 어느 문서인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
