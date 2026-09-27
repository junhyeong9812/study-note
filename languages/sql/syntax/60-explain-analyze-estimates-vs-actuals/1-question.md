# sql/60-`EXPLAIN ANALYZE` — 추정과 실측의 어긋남 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

```text
emp (사원 · 4행)                    dept (부서 · 3행)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

통계 실험은 **일부러 치우치게 만든 표**로 한다.

```sql
-- 1단계: grp 0~9 가 각 100행. 여기서 통계를 잡는다
CREATE TABLE t60_skew AS SELECT g AS id, (g % 10) AS grp FROM generate_series(1,1000) g;
CREATE INDEX t60_skew_grp ON t60_skew (grp);
ANALYZE t60_skew;

-- 2단계: grp=7 만 190,000행을 몰아넣는다. ANALYZE 는 하지 않는다
INSERT INTO t60_skew SELECT 1000+g, 7 FROM generate_series(1,190000) g;
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `EXPLAIN` 과 `EXPLAIN ANALYZE` 의 차이 (왜)

- 계획 한 줄에서 어느 칸이 추가되고, 그 칸들은 무엇을 말하는가?

### 2. 4행짜리 표의 추정 (예측)

```sql
EXPLAIN ANALYZE SELECT * FROM emp WHERE salary > 100;
```

- `rows=` 와 `actual rows=` 는 각각 얼마이고, 그 어긋남이 문제가 되는가?

### 3. `Rows Removed by Filter: 1` 이 버린 행 (연결)

- 2번 출력에서 버려진 한 행은 무엇이고, 왜 버려졌는가?

### 4. ★ 통계를 낡게 만든 직후 (예측)

```sql
-- 2단계 직후, ANALYZE 없이
EXPLAIN ANALYZE SELECT count(*) FROM t60_skew WHERE grp = 7;
```

- PostgreSQL 의 `rows=` 와 `actual rows=` 는 각각 얼마인가?

### 5. ★ 어긋남이 고치는 것은 숫자뿐인가 (왜)

- 4번에서 추정이 18배 빗나갔을 때, 계획에서 **숫자 말고** 무엇이 잘못됐는가?

### 6. `ANALYZE` 를 돌린 뒤 (예측)

```sql
ANALYZE t60_skew;
EXPLAIN ANALYZE SELECT count(*) FROM t60_skew WHERE grp = 7;
```

- 추정은 얼마가 되고, 연산자는 무엇으로 바뀌는가?

### 7. ★ MySQL 에서 같은 세 장면 (예측)

- MySQL 8.4.10 의 추정은 장면 2(통계 낡음)와 장면 3(`ANALYZE TABLE` 뒤)에서 각각 얼마이고, 실측은 얼마인가?

### 8. `ANALYZE TABLE` 이 고친 것과 못 고친 것 (경계)

```sql
SELECT table_rows FROM information_schema.tables WHERE table_name='t60_skew';
SHOW INDEX FROM t60_skew;
```

- 두 조회의 값은 `ANALYZE TABLE` 전후로 어떻게 달라지고, 그래도 안 고쳐진 것은 무엇인가?

### 9. ★ `actual rows=1.00 loops=10` (경계)

```text
->  Index Scan using t60_big_pkey on t60_big b  (cost=0.42..8.44 rows=1 width=8) (actual rows=1.00 loops=10)
```

- 이 노드는 모두 몇 행을 내놓았는가?

### 10. `Buffers: shared hit=37 read=3` (왜)

- `hit` 과 `read` 는 각각 무엇이고, 같은 질의를 두 번 돌리면 어느 쪽이 어떻게 변하는가?

### 11. 계획을 시간으로 비교하면 (경계)

- `actual time` 으로 두 계획을 비교하면 안 되는 이유는 무엇이고, 대신 어느 칸을 보는가?

### 12. ★ `EXPLAIN ANALYZE DELETE` 를 던지면 (예측)

```sql
BEGIN;
EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS OFF) DELETE FROM emp WHERE id = 1;
SELECT count(*) FROM emp;
ROLLBACK;
SELECT count(*) FROM emp;
```

- 두 `SELECT count(*)` 는 각각 얼마를 돌려주는가?

### 13. `Delete on emp (actual rows=0.00)` (경계)

- 12번 계획의 맨 윗줄이 `actual rows=0.00` 인데, 그러면 아무것도 안 지운 것인가?

### 14. `EXPLAIN` 만 쓰면 (예측)

```sql
EXPLAIN INSERT INTO t60_tx SELECT g FROM generate_series(101,105) g;
SELECT count(*) FROM t60_tx;
```

- 행이 들어가는가?

### 15. ★ MySQL 에서 `EXPLAIN ANALYZE UPDATE` (예측)

```sql
EXPLAIN ANALYZE UPDATE t59_small SET ref = 1 WHERE id = 1;
EXPLAIN ANALYZE INSERT INTO t59_small VALUES (98, 98);
```

- 각각 무엇이 출력되고, 데이터는 바뀌는가?

### 16. 정렬이 디스크로 넘쳤는지 보는 법 (연결)

```sql
SET work_mem = '64kB';   -- (A)
SET work_mem = '64MB';   -- (B)
EXPLAIN ANALYZE SELECT id FROM t60_s ORDER BY pad, id;
```

- (A)와 (B)에서 계획의 어느 줄이 어떻게 달라지는가?

### 17. 「느리다」의 진단 순서 (연결)

- `EXPLAIN ANALYZE` 출력을 받았을 때 무엇을 어떤 순서로 보는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
