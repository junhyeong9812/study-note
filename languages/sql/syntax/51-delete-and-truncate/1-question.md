# sql/51-DELETE 와 TRUNCATE — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

★ 이 편은 **`WHERE` 없는 삭제와 `TRUNCATE` 가 주제**이므로 자기 표를 만들어 쓴다. `emp`·`dept` 는 건드리지 않는다.

```text
t51_a (자동 증가)      t51_p / t51_c (FK — 참조 동작 없음)
+----+---+             t51_p(id PK, name)              : (1,'p1'), (2,'p2')
|  1 | a |             t51_c(id PK, p_id -> t51_p.id)  : (11,1), (12,1), (13,2)
|  2 | b |
|  3 | c |             t51_pc / t51_cc (FK — ON DELETE CASCADE)
|  4 | d |             t51_pc(id PK, name)             : (1,'p1'), (2,'p2')
|  5 | e |             t51_cc(id PK, p_id -> t51_pc.id ON DELETE CASCADE) : (11,1),(12,1),(13,2)
+----+---+
                       t51_big : id 1..50000, v = 'row-N'
```

환경 — PostgreSQL 18.6 · MySQL 8.4.10(**InnoDB**), `autocommit=1`, `sql_safe_updates=0`.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `DELETE` 는 되돌아오나 (예측)

```sql
BEGIN;  DELETE FROM t51_a;  SELECT count(*) FROM t51_a;  ROLLBACK;
SELECT count(*) FROM t51_a;
```

- 두 엔진에서 마지막 `count(*)` 는 각각 얼마인가?

### 2. ★★ `TRUNCATE` 는 되돌아오나 (예측)

```sql
BEGIN;  TRUNCATE t51_a;  SELECT count(*) FROM t51_a;  ROLLBACK;
SELECT count(*) FROM t51_a;
```

- 두 엔진에서 마지막 `count(*)` 는 각각 얼마인가?

### 3. 왜 그런가 (왜)

- 2번의 차이는 무엇 때문인가? 그 차이가 **`TRUNCATE` 앞에서 한 `INSERT`** 에는 어떤 영향을 주는가?

### 4. 비운 뒤 다음 번호 (예측)

```sql
-- 두 엔진 다 "다음 번호 6" 인 상태에서 시작한다
(a) DELETE FROM t51_a;                  INSERT INTO t51_a (v) VALUES ('new');
(b) TRUNCATE t51_a;                     INSERT INTO t51_a (v) VALUES ('new');
(c) TRUNCATE t51_a RESTART IDENTITY;    INSERT INTO t51_a (v) VALUES ('new');
```

- 세 경우의 새 행 `id` 는 두 엔진에서 각각 얼마인가?

### 5. 롤백하면 번호도 돌아오나 (경계)

```sql
BEGIN; INSERT INTO t51_a (v) VALUES ('x'); ROLLBACK;
INSERT INTO t51_a (v) VALUES ('y');
SELECT * FROM t51_a ORDER BY id;
```

- `'y'` 의 `id` 는 얼마인가?

### 6. ★ FK 자식이 있는 표를 비우면 (예측)

```sql
DELETE FROM t51_p WHERE id = 1;   -- (a)
TRUNCATE t51_p;                   -- (b)
DELETE FROM t51_c;                -- 자식을 전부 비운 뒤
TRUNCATE t51_p;                   -- (c) 다시 던지면?
```

- (a)·(b)·(c) 가 각각 어떻게 되는가?

### 7. 두 개의 `CASCADE` (경계)

```sql
TRUNCATE t51_pc CASCADE;                    -- (a)  t51_cc 는 ON DELETE CASCADE 자식이다
DELETE FROM t51_pc WHERE id = 1;            -- (b)
```

- 두 문이 `t51_cc` 에 남기는 행 수는 각각 얼마이고, 두 `CASCADE` 는 같은 것인가?

### 8. 영향 행 수를 믿어도 되나 (경계)

- 7번 (b) 의 `DELETE n` / `ROW_COUNT()` 는 얼마이고, 실제로 사라진 행은 몇 개인가?

### 9. ★ MySQL 의 FK 우회 (예측)

```sql
SET FOREIGN_KEY_CHECKS=0;  TRUNCATE t51_p;  SET FOREIGN_KEY_CHECKS=1;
SELECT (SELECT count(*) FROM t51_p) AS p, (SELECT count(*) FROM t51_c) AS c;
```

- `p` 와 `c` 는 각각 얼마이고, 무엇이 깨졌는가?

### 10. 비운 뒤 디스크는 줄어드나 (예측)

```sql
-- 5만 행짜리 t51_big
DELETE FROM t51_big;      -- 뒤에 표 크기는?
TRUNCATE t51_big;         -- 뒤에 표 크기는?
```

- 두 엔진에서 각각 어떻게 되는가?

### 11. 얼마나 빠른가 (예측)

- 5만 행에서 `TRUNCATE` 가 `DELETE` 보다 몇 배 빨랐는가? 두 엔진에서 **결론의 강도가 같은가**?

### 12. ★ 대량 삭제를 왜 나누나 (왜)

```sql
START TRANSACTION; DELETE FROM t51_big;
SELECT COUNT(*) FROM performance_schema.data_locks;
ROLLBACK;
```

- 이 숫자는 얼마이고, `LIMIT 10000` 을 붙이면 어떻게 달라지는가?

### 13. 나눠 도는 문법 (경계)

```sql
DELETE FROM t51_big LIMIT 10000;
```

- 두 엔진에서 각각 어떻게 되고, 안 되는 쪽은 무엇으로 대신하는가?

### 14. ★★ 안전 모드가 막는 것 (예측)

```sql
SET sql_safe_updates=1;
DELETE FROM t51_c;        -- (a)
TRUNCATE t51_c;           -- (b)
```

- 두 문은 각각 통과하는가?

### 15. 조인을 쓰는 삭제 (연결)

```sql
DELETE FROM t51_c USING t51_p WHERE t51_p.id = t51_c.p_id AND t51_p.name='p1';   -- (a)
DELETE c FROM t51_c c JOIN t51_p p ON p.id = c.p_id WHERE p.name='p1';           -- (b)
```

- 두 문은 두 엔진에서 각각 어떻게 되고, 이식 가능한 형태는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
