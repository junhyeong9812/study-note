# sql/55-트랜잭션 경계 — `COMMIT`·`ROLLBACK`·`SAVEPOINT` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.\
> **엔진** — PostgreSQL 18.6 · MySQL 8.4.10. **두 엔진의 답이 다른 문항이 많다** — 양쪽을 다 말해야 정답이다.

```text
t55_acct (계좌 · 2행)
+----+-------+------+
| id | owner | bal  |
+----+-------+------+
|  1 | ann   | 1000 |
|  2 | bob   | 1000 |
+----+-------+------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 자동 커밋이 어디에 사나 (경계)

```sql
SHOW autocommit;            -- PG
SELECT @@autocommit;        -- MySQL
```

- 두 엔진은 각각 무엇을 돌려주는가?

### 2. 괄호 없는 `UPDATE` 를 옆 세션이 보는 시점 (예측)

```text
세션 A: UPDATE t55_acct SET bal = 900 WHERE id = 1;   (BEGIN 없음)
세션 B: SELECT bal FROM t55_acct WHERE id = 1;
```

- B 는 900 을 보는가, 1000 을 보는가?

### 3. ★ 괄호 안에서 문 하나가 실패하면 (예측)

```sql
BEGIN;                                       -- MySQL: START TRANSACTION;
UPDATE t55_acct SET bal = 111 WHERE id = 1;
INSERT INTO t55_acct VALUES (1, 'dup', 0);   -- 기본키 중복
UPDATE t55_acct SET bal = 222 WHERE id = 2;
COMMIT;
```

- 끝나고 표를 읽으면 두 엔진에서 각각 어떤 값이 나오는가?

### 4. `current transaction is aborted` 뒤의 `COMMIT` (예측)

- 3번의 PG 쪽에서 마지막 `COMMIT;` 은 무엇으로 찍히는가?

### 5. `SAVEPOINT` 가 되돌리는 범위 (예측)

```sql
BEGIN;
UPDATE t55_acct SET bal = bal - 100 WHERE id = 1;
SAVEPOINT sp1;
UPDATE t55_acct SET bal = bal - 500 WHERE id = 2;
ROLLBACK TO SAVEPOINT sp1;
SELECT id, bal FROM t55_acct ORDER BY id;
```

- 마지막 `SELECT` 의 두 행은 각각 얼마인가?

### 6. `ROLLBACK TO` 뒤에 트랜잭션은 살아 있나 (경계)

- 5번의 `ROLLBACK TO SAVEPOINT sp1;` 이 끝난 시점에 괄호는 닫혔는가?

### 7. `RELEASE SAVEPOINT` 는 무엇을 되돌리나 (왜)

- `RELEASE` 한 뒤 표의 값은 어떻게 되는가?

### 8. ★ `RELEASE` 한 이름으로 `ROLLBACK TO` 하면 (예측)

```sql
RELEASE SAVEPOINT sp1;
ROLLBACK TO SAVEPOINT sp1;
COMMIT;
```

- 두 엔진에서 각각 무엇이 출력되고, **PG 에서는 표의 값이 어떻게 되는가?**

### 9. 트랜잭션 밖에서 `SAVEPOINT` 를 치면 (예측)

```sql
SAVEPOINT sp9;
ROLLBACK TO SAVEPOINT sp9;
```

- 두 엔진에서 각각 어느 줄이 에러를 내는가?

### 10. ★ `BEGIN` 을 두 번 치면 (예측)

```text
(MySQL)  START TRANSACTION;
         UPDATE t55_acct SET bal = 777 WHERE id = 1;
         START TRANSACTION;
         ROLLBACK;
         SELECT id, bal FROM t55_acct ORDER BY id;
```

- `bal` 은 얼마이고, 그 이유를 말해 주는 경고가 나오는가?

### 11. ★ 트랜잭션 한가운데의 `CREATE TABLE` (예측)

```sql
BEGIN;                                       -- MySQL: START TRANSACTION;
UPDATE t55_acct SET bal = 555 WHERE id = 1;
CREATE TABLE t55_tmp (x int);
UPDATE t55_acct SET bal = 666 WHERE id = 2;
ROLLBACK;
```

- 두 엔진에서 **표의 값**과 **`t55_tmp` 의 존재 여부**는 각각 어떻게 되는가?

### 12. 666 은 왜 살아남았나 (왜)

- 11번의 MySQL 에서 `CREATE TABLE` **뒤에** 나온 `UPDATE` 까지 확정된 이유는 무엇인가?

### 13. `BEGIN ISOLATION LEVEL REPEATABLE READ;` (경계)

- 두 엔진 중 어느 쪽이 이 문법을 받는가?

### 14. `SET autocommit = 0` 은 무슨 모드인가 (연결)

- MySQL 에서 이 값을 0 으로 두면 `BEGIN` 없이 던진 `UPDATE` 를 `ROLLBACK` 할 수 있는가?

### 15. 진짜 중첩 트랜잭션 (연결)

- 트랜잭션 안에 트랜잭션을 넣고 싶을 때 두 엔진에서 쓸 수 있는 수단은 무엇인가?

### 16. 「`ROLLBACK` 이 성공했다」의 함정 (경계)

- `ROLLBACK;` 이 에러 없이 끝났는데도 변경이 남아 있을 수 있는 경우를 두 가지 대라.

### 17. 괄호를 언제 안 치나 (연결)

- 트랜잭션으로 감싸지 **않는** 것이 나은 경우는 언제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
