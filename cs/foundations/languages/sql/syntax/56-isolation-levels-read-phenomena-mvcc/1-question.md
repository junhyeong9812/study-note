# sql/56-격리 수준과 읽기 이상 현상·MVCC — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.\
> **엔진** — PostgreSQL 18.6 · MySQL 8.4.10. **두 엔진의 답이 다른 문항이 많다** — 양쪽을 다 말해야 정답이다.\
> **개념·트레이드오프는 [`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 가 정본이다.** 여기서 묻는 것은 **문법과 실제 동작**이다.

```text
t56_item (재고 · 3행)              t56_duty (당직 · 2행)
+----+-----+-----+                 +----+------+---------+
| id | grp | qty |                 | id | name | on_duty |
+----+-----+-----+                 +----+------+---------+
|  1 |  10 |   5 |                 |  1 | ann  | true    |
|  2 |  10 |   7 |                 |  2 | bob  | true    |
|  3 |  20 |   9 |                 +----+------+---------+
+----+-----+-----+                 불변식: on_duty 인 사람이 최소 한 명
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 두 엔진의 기본 격리 수준 (경계)

```sql
SHOW transaction_isolation;          -- PG
SELECT @@transaction_isolation;      -- MySQL
```

- 아무 설정도 안 했을 때 각각 무엇이 나오는가?

### 2. ★ `READ UNCOMMITTED` 로 남의 미커밋 값을 읽으면 (예측)

```text
세션 A: BEGIN; UPDATE t56_item SET qty = 999 WHERE id = 1;   (커밋 안 함)
세션 B: BEGIN <READ UNCOMMITTED>; SELECT qty FROM t56_item WHERE id = 1;
```

- 두 엔진에서 B 는 각각 무엇을 읽는가?

### 3. PG 가 `read uncommitted` 라고 보고하는데 더티 리드가 안 나는 이유 (왜)

- `SHOW transaction_isolation` 이 `read uncommitted` 를 돌려주는데도 999 가 안 보이는 것을 어떻게 설명하는가?

### 4. 반복 불가능 읽기와 팬텀 — 기본값에서 (예측)

```text
세션 B: BEGIN;  SELECT qty ... id=1;  SELECT count(*) ... grp=10;
세션 A: UPDATE ... qty=50 WHERE id=1;  INSERT INTO t56_item VALUES (4,10,1);   (자동 커밋)
세션 B: SELECT qty ... id=1;  SELECT count(*) ... grp=10;
```

- **아무 설정도 안 한 상태**에서 B 의 두 번째 읽기는 두 엔진에서 각각 얼마인가?

### 5. ★ MySQL `REPEATABLE READ` 에서 일반 읽기와 잠금 읽기를 나란히 던지면 (예측)

```sql
SELECT count(*) FROM t56_item WHERE grp = 10;             -- (가)
SELECT count(*) FROM t56_item WHERE grp = 10 FOR SHARE;   -- (나)
```

- 4번 상황의 같은 트랜잭션 안에서 (가)와 (나)는 각각 몇을 돌려주는가?

### 6. 그러면 MySQL 의 `REPEATABLE READ` 는 팬텀을 막는가 (경계)

- 5번의 결과를 근거로 「막는다/안 막는다」 중 무엇이라고 답해야 하는가?

### 7. ★ 쓰기 왜곡 — 둘이 동시에 퇴근하면 (예측)

```text
A: BEGIN; SELECT count(*) FROM t56_duty WHERE on_duty;  -> 2
B: BEGIN; SELECT count(*) FROM t56_duty WHERE on_duty;  -> 2
A: UPDATE t56_duty SET on_duty = false WHERE id = 1;    A: COMMIT;
B: UPDATE t56_duty SET on_duty = false WHERE id = 2;    B: COMMIT;
```

- `REPEATABLE READ` 에서 두 엔진의 최종 표는 각각 어떻게 되는가?

### 8. ★ 같은 시나리오를 `SERIALIZABLE` 로 올리면 (예측)

- PG 와 MySQL 에서 각각 **누가 어느 줄에서 무슨 에러**를 받는가?

### 9. 두 에러가 공통으로 시키는 것 (연결)

- 8번의 두 에러 메시지가 애플리케이션에 요구하는 것은 무엇인가?

### 10. ★ PG 의 `REPEATABLE READ` 에서 같은 행을 둘이 고치면 (예측)

```text
A: BEGIN ISOLATION LEVEL REPEATABLE READ; SELECT qty ... id=1;
B: BEGIN ISOLATION LEVEL REPEATABLE READ; SELECT qty ... id=1;
A: UPDATE t56_item SET qty = qty - 1 WHERE id = 1;  A: COMMIT;
B: UPDATE t56_item SET qty = qty - 1 WHERE id = 1;
```

- B 의 `UPDATE` 는 어떻게 되고, 같은 것을 `READ COMMITTED` 와 MySQL 에서 하면 어떻게 되는가?

### 11. 두 가지 `could not serialize access` (경계)

- PG 가 내는 `concurrent update` 쪽과 `read/write dependencies` 쪽은 각각 언제 나오는가?

### 12. ★ `SET TRANSACTION` 을 `SESSION` 없이 치면 (예측)

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;   -- MySQL, SESSION 없이
START TRANSACTION;
SELECT @@transaction_isolation, qty FROM t56_item WHERE id = 3;
```

- 변수는 무엇을 보고하고, 실제 동작은 어느 수준인가?

### 13. PG 에서 `SET TRANSACTION` 을 늦게 치면 (예측)

```sql
BEGIN;
SELECT 1;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

- 마지막 줄은 어떻게 되는가?

### 14. `BEGIN ISOLATION LEVEL …` (경계)

- 두 엔진 중 어느 쪽이 이 문법을 받고, 안 받는 쪽은 무엇으로 대신하는가?

### 15. ★ 스냅샷은 언제 찍히나 (예측)

```text
B: BEGIN <REPEATABLE READ>;            (아무것도 안 읽는다)
A: UPDATE t56_item SET qty = 77 WHERE id = 2;   (자동 커밋)
B: SELECT qty ... id=2;                <- 첫 읽기
```

- B 는 `BEGIN` 이전 값을 보는가, 77 을 보는가?

### 16. 격리 수준으로 lost update 를 막을 수 있나 (연결)

- 막을 수 있다면 어느 수준부터이고, 그 전에 검토할 더 싼 수단은 무엇인가?

### 17. 「에러 없이 돌았다」의 함정 (왜)

- 7번의 `REPEATABLE READ` 실행은 에러가 하나도 없었다. 그런데 무엇이 잘못됐는가?

### 18. 수준을 올리는 대가 (연결)

- 격리 수준을 올릴 때 내는 대가를 세 가지 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
