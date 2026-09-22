# sql/55-트랜잭션 경계 — `COMMIT`·`ROLLBACK`·`SAVEPOINT` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · BEGIN](https://www.postgresql.org/docs/18/sql-begin.html) · [COMMIT](https://www.postgresql.org/docs/18/sql-commit.html) · [ROLLBACK](https://www.postgresql.org/docs/18/sql-rollback.html) · [SAVEPOINT](https://www.postgresql.org/docs/18/sql-savepoint.html) · [MySQL 8.4 · START TRANSACTION, COMMIT, and ROLLBACK](https://dev.mysql.com/doc/refman/8.4/en/commit.html) · [SAVEPOINT, ROLLBACK TO SAVEPOINT, RELEASE SAVEPOINT](https://dev.mysql.com/doc/refman/8.4/en/savepoint.html) · [Statements That Cause an Implicit Commit](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **이 주제는 설정에 달려 있다** — 자동 커밋이 어디에 사는지가 두 엔진에서 다르다. 그래서 「환경 확인」이 본문 앞에 있다.\
> ★ **두 세션이 필요한 실험이 있다.** 이름 붙인 FIFO 로 두 접속을 열어 두고 한 줄씩 먹였다(맨 끝 「실행 검증」에 방법 그대로).\
> **이 편이 만든 객체와 그 뒷정리** — 표 `t55_acct`(2행) · `t55_tmp`(MySQL 의 암묵 커밋 실험용). **끝나고 둘 다 `DROP` 했다**(3-answer 의 「실행 검증」).\
> ★ **기존 `emp`·`dept` 는 이 편에서 읽지도 잠그지도 않았다.** 트랜잭션 자체가 실험 대상이라 `ROLLBACK` 에 기댈 수 없는 자리가 많아, 공용 표를 아예 건드리지 않았다.\
> **선행** — [49 INSERT](../49-insert-multi-row-and-insert-select/). 넣는 문이 있어야 「되돌린다」가 성립한다.

## 한눈에 — 쉽게 말하면

**트랜잭션은 「여기서부터 여기까지는 전부 되거나 전부 안 된 것으로 쳐라」는 괄호다.**

- 이사할 때 짐을 옮긴다. 침대는 새집, 냉장고는 트럭, 옷장은 아직 옛집에 있다.
- 중간에 이사가 엎어지면 **반쯤 옮겨진 상태**가 남는다 — 이게 제일 나쁘다.
- 트랜잭션은 「전부 새집 아니면 전부 옛집」을 강제한다. `COMMIT` 이 「이사 끝」, `ROLLBACK` 이 「전부 제자리」다.
- `SAVEPOINT` 는 이사 중간에 찍는 **표식**이다. 「거실까지는 괜찮았으니 거기로만 되돌리자」.

| 비유 | 실체 |
|---|---|
| 이사 시작 | `BEGIN` / `START TRANSACTION` |
| 이사 끝 — 확정 | `COMMIT` |
| 전부 제자리 | `ROLLBACK` |
| 거실까지 끝난 시점의 표식 | `SAVEPOINT sp1` |
| 그 표식으로만 되돌린다 | `ROLLBACK TO SAVEPOINT sp1` |
| 표식을 뗀다 (되돌리기는 안 한다) | `RELEASE SAVEPOINT sp1` |
| 짐 하나 옮길 때마다 바로 확정 | **자동 커밋** — 두 엔진의 **기본값** |

```text
자동 커밋 (기본)                     명시적 트랜잭션
─────────────────                    ─────────────────
UPDATE ... ;  -> 즉시 확정           BEGIN;
UPDATE ... ;  -> 즉시 확정             UPDATE ... ;   <- 아직 내 눈에만 보인다
                                       UPDATE ... ;   <- 아직 내 눈에만 보인다
문 하나 = 트랜잭션 하나               COMMIT;          <- 이 순간 둘 다 남에게 보인다
                                     (또는 ROLLBACK;  <- 이 순간 둘 다 사라진다)
```

**똑같은 구조다** — 「계좌에서 빼고 다른 계좌에 넣는다」가 둘로 쪼개져 중간에 죽으면 돈이 증발한다.\
트랜잭션 괄호는 그 「중간」을 **다른 접속이 볼 수 없는 시간**으로 만든다.

> **트랜잭션(transaction)** — 전부 반영되거나 전부 안 된 것으로 치는 문들의 묶음.\
> 예: 출금 `UPDATE` 와 입금 `UPDATE` 둘을 한 괄호에 넣으면, 둘 다 되거나 둘 다 안 된다.

> **자동 커밋(autocommit)** — 문 하나하나를 각각 하나의 트랜잭션으로 보고 끝나면 바로 확정하는 모드.\
> 예: `BEGIN` 없이 던진 `UPDATE` 는 끝나는 순간 이미 남이 볼 수 있다 — 되돌릴 방법이 없다.

> **커밋(commit)** — 트랜잭션 안의 변경을 확정해 다른 접속에게도 보이게 하는 것.\
> 예: `COMMIT;` 을 친 뒤에야 옆 세션의 `SELECT` 가 새 값을 읽는다.

## 이 주제가 답하려는 질문

1. **괄호를 안 치면 어떻게 되나** — 두 엔진의 기본값은 무엇이고, 그 기본값이 어디에 사는가.
2. **괄호 안에서 문 하나가 실패하면 나머지는 어떻게 되나** — ★ 여기서 두 엔진이 **정반대로 갈린다.**
3. **괄호 전체가 아니라 일부만 되돌리려면** — `SAVEPOINT` 가 무엇을 되돌리고 무엇을 안 되돌리나.

## 환경 확인 — 물어보고 시작한다

이 주제는 **설정을 안 밝히면 본문 전체가 검증 불가**다. 외우지 말고 찍어 본다.

```text
### SQL: (PG) SHOW default_transaction_isolation;  SHOW transaction_isolation;
--- PG 18.6 ---
 default_transaction_isolation
-------------------------------
 read committed

 transaction_isolation
-----------------------
 read committed
```

★ **PostgreSQL 에는 `autocommit` 이라는 서버 설정이 없다.** 던져 보면 이렇게 답한다.

```text
### SQL: (PG) SHOW autocommit;
--- PG 18.6 ---
SHOW autocommit;
ERROR:  unrecognized configuration parameter "autocommit"
```

자동 커밋은 **클라이언트 쪽 동작**이다. `psql` 의 변수로 산다.

```text
### psql: \echo :AUTOCOMMIT
--- PG 18.6 ---
on
```

MySQL 은 반대로 **서버 세션 변수**다.

```text
### SQL: (MySQL) SELECT VERSION(); SELECT @@transaction_isolation, @@autocommit, @@innodb_lock_wait_timeout;
--- MySQL 8.4.10 ---
VERSION(): 8.4.10
   @@transaction_isolation: REPEATABLE-READ
              @@autocommit: 1
@@innodb_lock_wait_timeout: 50
```

| 물어본 것 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 기본 격리 수준 | `read committed` | `REPEATABLE-READ` |
| 자동 커밋 | **서버 설정이 아니다** (`ERROR: unrecognized configuration parameter`) — 클라이언트(`psql` 의 `:AUTOCOMMIT`)가 `on` | **서버 세션 변수** `@@autocommit = 1` |
| 잠금 대기 제한 | `lock_timeout = 0` (무제한) | `innodb_lock_wait_timeout = 50` (초) |

★ **두 엔진 다 「기본은 자동 커밋」이 맞다.** 다만 **그것을 끌 수 있는 손잡이가 서로 다른 층에 있다** —\
PG 에서 「자동 커밋을 껐다」는 말은 **드라이버·클라이언트 이야기**이고, MySQL 에서는 **서버에 물어볼 수 있는 값**이다.\
격리 수준 기본값이 다른 것은 [56번](../56-isolation-levels-read-phenomena-mvcc/)의 주제다.

## 예시 데이터 — 이 묶음이 공유하는 것

★ **이 편은 `emp`·`dept` 를 쓰지 않는다.** 트랜잭션을 일부러 깨뜨리는 실험이라 공용 표를 잠글 수 없다.

```sql
CREATE TABLE t55_acct (id int PRIMARY KEY, owner text, bal int);   -- MySQL 은 text -> varchar(10)
INSERT INTO t55_acct VALUES (1,'ann',1000),(2,'bob',1000);
```

```text
t55_acct (계좌 · 2행)
+----+-------+------+
| id | owner | bal  |
+----+-------+------+
|  1 | ann   | 1000 |
|  2 | bob   | 1000 |
+----+-------+------+
```

## 동작 방식

### 1. 괄호가 없으면 — 문 하나가 곧 트랜잭션 하나

**언제 쓰나** — 아무 생각 없이 `UPDATE` 를 던질 때. **이미 트랜잭션 안이고, 이미 끝났다.**

두 세션을 동시에 띄워 확인한다. `A` 가 쓰고 `B` 가 읽는다.

```text
시간   세션 A                                   세션 B
 │
 1     UPDATE t55_acct SET bal = 900 WHERE id=1;
 │     (BEGIN 없음)
 2                                              SELECT bal ... id=1;  -> 900
 │                                                                       ^^^ 벌써 보인다
 3     BEGIN;
 4     UPDATE t55_acct SET bal = 800 WHERE id=1;
 5                                              SELECT bal ... id=1;  -> 900
 │                                                                       ^^^ 800 이 아니다
 6     ROLLBACK;
 7                                              SELECT bal ... id=1;  -> 900
```

**실제 출력 — 세션 B (PG 18.6)**

```text
SELECT bal FROM t55_acct WHERE id = 1;
 bal
-----
 900
(1 row)

SELECT bal FROM t55_acct WHERE id = 1;
 bal
-----
 900
(1 row)

SELECT bal FROM t55_acct WHERE id = 1;
 bal
-----
 900
(1 row)
```

**실제 출력 — 세션 B (MySQL 8.4.10)**

```text
SELECT bal FROM t55_acct WHERE id = 1
+------+
| bal  |
+------+
|  900 |
+------+
(세 번 다 같은 출력)
```

★ **세션 B 는 세 번 다 `BEGIN` 없이 읽었다** — 읽기마다 트랜잭션이 새로 열리고 닫힌다.\
그래서 MySQL 의 기본 격리 수준(`REPEATABLE READ`)이 값을 가린 것이 아니다. 스냅샷은 매번 새로 잡혔다([56번](../56-isolation-levels-read-phenomena-mvcc/)).

그림 해설 — 1번 `UPDATE` 는 **되돌릴 방법이 없다.** 문이 끝난 순간 확정됐다.\
4번 `UPDATE` 는 A 안에서만 산다. B 는 그 존재를 모른다.\
6번 `ROLLBACK` 이 그것을 지웠으므로 B 의 세 번째 읽기도 900 이다.\
비용 — 자동 커밋은 문마다 커밋 비용(로그 플러시)을 낸다. 대신 잠금을 오래 쥐지 않는다.

### 2. ★ 괄호 안에서 문 하나가 실패하면 — 두 엔진이 정반대다

**언제 쓰나** — 배치 중간에 제약 위반이 나올 때. **이 주제에서 가장 비싼 차이다.**

같은 다섯 줄을 양쪽에 던진다. 가운데 `INSERT` 가 기본키를 위반한다.

```sql
BEGIN;                                       -- MySQL: START TRANSACTION;
UPDATE t55_acct SET bal = 111 WHERE id = 1;  -- 성공
INSERT INTO t55_acct VALUES (1, 'dup', 0);   -- 실패 (기본키 중복)
UPDATE t55_acct SET bal = 222 WHERE id = 2;  -- ?
SELECT id, bal FROM t55_acct ORDER BY id;    -- ?
COMMIT;                                      -- ?
```

```text
(A) PostgreSQL 18.6                          (B) MySQL 8.4.10
ERROR:  duplicate key value violates          ERROR 1062 (23000) at line 3: Duplicate
  unique constraint "t55_acct_pkey"             entry '1' for key 't55_acct.PRIMARY'
DETAIL:  Key (id)=(1) already exists.
UPDATE t55_acct SET bal = 222 WHERE id = 2;   UPDATE t55_acct SET bal = 222 WHERE id = 2
SELECT id, bal FROM t55_acct ORDER BY id;     SELECT id, bal FROM t55_acct ORDER BY id
ERROR:  current transaction is aborted,       +----+------+
  commands ignored until end of               | id | bal  |
  transaction block                           +----+------+
COMMIT;                                       |  1 |  111 |
ROLLBACK                                      |  2 |  222 |
ERROR:  current transaction is aborted,       +----+------+
  commands ignored until end of               COMMIT
  transaction block
--- 끝나고 표를 다시 보면 ---                  --- 끝나고 표를 다시 보면 ---
 id | bal                                     +----+------+
----+------                                   | id | bal  |
  1 |  900                                    +----+------+
  2 | 1000                                    |  1 |  111 |
                                              |  2 |  222 |
                                              +----+------+
  -> 앞의 UPDATE 도 **사라졌다**                 -> 앞뒤 UPDATE 둘 다 **살아남았다**
  -> 뒤의 문은 아예 실행되지 않았다               -> 실패한 INSERT 만 취소됐다
  -> COMMIT 이 ROLLBACK 으로 찍혔다
```

두 그림의 결론 — **PG 는 트랜잭션을 통째로 「중단 상태」로 만든다.**\
그 안에서는 어떤 문도 안 돌고, `COMMIT` 조차 `ROLLBACK` 으로 처리된다(위 출력의 `COMMIT;` 아래 `ROLLBACK` 한 줄이 그 증거다).\
**MySQL 은 실패한 그 문만 되돌리고(문 단위 롤백) 트랜잭션은 계속 산다.** 그래서 `COMMIT` 이 앞뒤 변경을 **확정한다.**

> **중단된 트랜잭션(aborted transaction)** — PG 에서 에러가 난 뒤의 트랜잭션 상태. 끝낼 수만 있고 아무것도 못 한다.\
> 예: 위 출력의 `current transaction is aborted, commands ignored until end of transaction block`.

> **문 단위 롤백(statement rollback)** — 실패한 문 하나가 한 것만 되돌리고 트랜잭션은 유지하는 것. MySQL 의 기본 동작이다.\
> 예: 위 MySQL 출력에서 `INSERT` 만 없던 일이 되고 두 `UPDATE` 는 남았다.

비용 — PG 쪽은 **시끄럽지만 안전하다.** 「에러를 무시하고 커밋」이 불가능하다.\
MySQL 쪽은 **조용하지만 위험하다.** 애플리케이션이 에러를 삼키면 **반쯤 적용된 트랜잭션이 커밋된다.**

### 3. `SAVEPOINT` — 괄호 안에 표식을 찍는다

**언제 쓰나** — 긴 트랜잭션 안에서 「여기부터는 실패해도 괜찮다」는 구간이 있을 때.

```text
(전) t55_acct              BEGIN;
+----+------+              UPDATE id=1 : bal -100      -> 1:900  2:1000
|  1 | 1000 |              SAVEPOINT sp1;                   <- 여기 표식
|  2 | 1000 |              UPDATE id=2 : bal -500      -> 1:900  2:500
+----+------+              ROLLBACK TO SAVEPOINT sp1;       <- 표식으로 되돌림
                                                       -> 1:900  2:1000
                           RELEASE SAVEPOINT sp1;            <- 표식만 뗀다
```

**실제 출력 (PG 18.6)**

```text
BEGIN;
UPDATE t55_acct SET bal = bal - 100 WHERE id = 1;
UPDATE 1
SAVEPOINT sp1;
SAVEPOINT
UPDATE t55_acct SET bal = bal - 500 WHERE id = 2;
UPDATE 1
SELECT id, bal FROM t55_acct ORDER BY id;
 id | bal
----+-----
  1 | 800
  2 | 500
(2 rows)

ROLLBACK TO SAVEPOINT sp1;
ROLLBACK
SELECT id, bal FROM t55_acct ORDER BY id;
 id | bal
----+------
  1 |  800
  2 | 1000
(2 rows)
```

**실제 출력 (MySQL 8.4.10)** — 같은 값이 나온다.

```text
SELECT id, bal FROM t55_acct ORDER BY id
+----+------+
| id | bal  |
+----+------+
|  1 |  800 |
|  2 |  500 |
+----+------+
ROLLBACK TO SAVEPOINT sp1
SELECT id, bal FROM t55_acct ORDER BY id
+----+------+
| id | bal  |
+----+------+
|  1 |  800 |
|  2 | 1000 |
+----+------+
```

그림 해설 — `ROLLBACK TO` 는 **표식 이후의 변경만** 지운다. 표식 이전의 `-100` 은 그대로다.\
★ `ROLLBACK TO` 는 **트랜잭션을 끝내지 않는다.** 괄호는 계속 열려 있고, 그 뒤에 `COMMIT` 이든 `ROLLBACK` 이든 따로 쳐야 한다.\
`RELEASE` 는 **되돌리지 않는다** — 표식만 떼서 더 이상 그 이름으로 못 돌아가게 한다.\
비용 — 세이브포인트마다 엔진이 상태를 더 들고 있어야 한다. 루프마다 찍으면 트랜잭션이 무거워진다.

> **`SAVEPOINT`** — 트랜잭션 안에 이름을 붙인 되돌림 지점.\
> 예: `SAVEPOINT sp1;` 뒤의 변경만 `ROLLBACK TO SAVEPOINT sp1;` 으로 지운다.

> **`RELEASE SAVEPOINT`** — 그 이름을 지우는 것. 변경은 그대로 둔다.\
> 예: `RELEASE` 한 뒤 같은 이름으로 `ROLLBACK TO` 하면 「그런 세이브포인트 없다」 에러다(아래 「어디서 틀리나」).

### 4. ★ MySQL 의 DDL 은 트랜잭션 한가운데서 앞의 것을 커밋한다

**언제 쓰나** — 마이그레이션 스크립트에서 `CREATE TABLE` 과 `UPDATE` 를 한 파일에 섞을 때.

같은 다섯 줄을 양쪽에 던진다.

```sql
BEGIN;                                        -- MySQL: START TRANSACTION;
UPDATE t55_acct SET bal = 555 WHERE id = 1;
CREATE TABLE t55_tmp (x int);                 -- <- DDL
UPDATE t55_acct SET bal = 666 WHERE id = 2;
ROLLBACK;
```

```text
(A) PostgreSQL 18.6 — DDL 도 되돌아간다       (B) MySQL 8.4.10 — DDL 이 커밋해 버린다
SELECT id, bal FROM t55_acct ORDER BY id;     SELECT id, bal FROM t55_acct ORDER BY id
 id | bal                                     +----+------+
----+------                                   | id | bal  |
  1 |  900                                    +----+------+
  2 | 1000                                    |  1 |  555 |
(2 rows)                                      |  2 |  666 |
                                              +----+------+
SELECT to_regclass('t55_tmp');                SHOW TABLES LIKE 't55%'
 t55_tmp_exists                               +------------------------+
----------------                              | Tables_in_study (t55%) |
                                              +------------------------+
(1 row)   <- NULL. 표가 없다                   | t55_acct               |
                                              | t55_tmp                |   <- 남아 있다
                                              +------------------------+
  -> ROLLBACK 이 UPDATE 도 CREATE 도 지웠다      -> ROLLBACK 이 아무것도 못 지웠다
```

두 그림의 결론 — MySQL 에서 **`CREATE TABLE` 이 앞의 `UPDATE`(555)를 암묵 커밋했다.**\
그리고 DDL 은 트랜잭션을 **끝내기까지** 하므로, 그 뒤의 `UPDATE`(666)는 **자동 커밋으로 혼자 돌아** 역시 확정됐다.\
`ROLLBACK` 은 지울 것이 하나도 남아 있지 않은 상태에서 돌았다 — **에러도 경고도 없이.**

> **암묵 커밋(implicit commit)** — 어떤 문이 실행될 때 엔진이 진행 중인 트랜잭션을 대신 커밋해 버리는 것.\
> 예: MySQL 의 `CREATE`·`ALTER`·`DROP`·`TRUNCATE`·`RENAME` 같은 DDL 과 두 번째 `START TRANSACTION`.

비용 — PG 는 DDL 을 트랜잭션 안에 넣을 수 있어 **마이그레이션 전체를 한 괄호**로 묶을 수 있다.\
MySQL 은 못 묶는다 — 스크립트 중간에서 실패하면 **반쯤 적용된 스키마**가 남는다.

## 문법 — 형태와 규칙

SQL 에서 이 절은 「형태」가 아니라 「**어느 문이 어디서 유효한가**」가 본체다.

| 하는 일 | PostgreSQL 18 | MySQL 8.4 |
|---|---|---|
| 괄호 열기 | `BEGIN;` · `START TRANSACTION;` · `BEGIN ISOLATION LEVEL …;` | `START TRANSACTION;` · `BEGIN;` (동의어) |
| 확정 | `COMMIT;` · `END;` · `COMMIT AND CHAIN;` | `COMMIT;` · `COMMIT AND CHAIN;` |
| 되돌리기 | `ROLLBACK;` · `ABORT;` | `ROLLBACK;` |
| 표식 찍기 | `SAVEPOINT 이름;` | `SAVEPOINT 이름;` |
| 표식으로 되돌리기 | `ROLLBACK TO SAVEPOINT 이름;` (`SAVEPOINT` 생략 가능) | `ROLLBACK TO SAVEPOINT 이름;` (`SAVEPOINT` 생략 가능) |
| 표식 떼기 | `RELEASE SAVEPOINT 이름;` | `RELEASE SAVEPOINT 이름;` |
| 자동 커밋 끄기 | **서버 문법 없음** — 클라이언트 설정 | `SET autocommit = 0;` |

★ **`BEGIN ISOLATION LEVEL …` 은 PG 문법이고 MySQL 에서는 구문 오류다.**

```text
### SQL: BEGIN ISOLATION LEVEL REPEATABLE READ;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 9: You have an error in your SQL syntax; ... near 'ISOLATION LEVEL REPEATABLE READ' at line 1
```

★ **`COMMIT AND CHAIN` 은 양쪽 다 된다** — 커밋하자마자 같은 설정으로 새 트랜잭션을 연다.

```text
### SQL: START TRANSACTION; SELECT 1; COMMIT AND CHAIN; SELECT 2; COMMIT;
--- PG 18.6 ---       COMMIT AND CHAIN;  ->  COMMIT      (뒤의 SELECT 2 는 새 트랜잭션 안)
--- MySQL 8.4.10 ---  COMMIT AND CHAIN   ->  (출력 없음)  (뒤의 SELECT 2 는 새 트랜잭션 안)
```

★ **MySQL 에서 `SET autocommit = 0` 은 「괄호가 항상 열려 있는 모드」다.**

```text
### SQL: (MySQL) SET autocommit = 0; UPDATE t55_acct SET bal = 1234 WHERE id = 1; ROLLBACK; SELECT ...
--- MySQL 8.4.10 ---
SELECT @@autocommit AS ac_now
+--------+
| ac_now |
+--------+
|      0 |
+--------+
SELECT id,bal FROM t55_acct ORDER BY id
+----+------+
| id | bal  |
+----+------+
|  1 | 1000 |   <- 1234 가 아니다. ROLLBACK 이 먹혔다
|  2 | 1000 |
+----+------+
```

## 어디서 틀리나

### ㄱ. ★ PG — 에러 하나가 그 뒤 전부를 삼킨다

`current transaction is aborted` 를 본 순간 **그 트랜잭션은 이미 죽었다.**\
스크립트가 에러를 무시하고 계속 던지면 **뒤 문장이 전부 무시된 채 롤백된다** — 그런데 클라이언트는 「끝까지 돌았다」고 본다.\
처방은 둘이다. ① 에러에서 멈춘다(`psql` 의 `ON_ERROR_STOP=1`) ② 실패해도 되는 구간을 `SAVEPOINT` 로 감싼다.

### ㄴ. ★ MySQL — 에러를 삼키면 반쯤 적용된 트랜잭션이 커밋된다

위 2번의 오른쪽 그림이 그대로 사고다. `INSERT` 가 죽었는데 `COMMIT` 이 성공했고, 두 `UPDATE` 는 남았다.\
**드라이버의 예외를 잡아서 로그만 찍고 넘어가는 코드**가 이 모양을 만든다.

### ㄷ. `RELEASE` 한 표식으로 `ROLLBACK TO` 하면

두 엔진 다 에러이고, **에러 뒤의 처리가 다르다.**

```text
### SQL: RELEASE SAVEPOINT sp1;  ROLLBACK TO SAVEPOINT sp1;  COMMIT;
--- PG 18.6 ---
RELEASE SAVEPOINT sp1;
RELEASE
ROLLBACK TO SAVEPOINT sp1;
ERROR:  savepoint "sp1" does not exist
COMMIT;
ROLLBACK                                   <- COMMIT 이 ROLLBACK 으로 찍혔다
SELECT id, bal FROM t55_acct ORDER BY id;
 id | bal
----+------
  1 |  900                                 <- -100 도 사라졌다
  2 | 1000
```

```text
--- MySQL 8.4.10 ---
ERROR 1305 (42000) at line 9: SAVEPOINT sp1 does not exist
```

★ **PG 쪽 결과를 잘 봐라** — 세이브포인트 하나 잘못 불렀다고 **트랜잭션 전체가 날아갔다.**

### ㄹ. 트랜잭션 밖에서 `SAVEPOINT` 를 치면

**여기서 두 엔진이 또 갈린다.**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
SAVEPOINT sp1;                              SAVEPOINT sp9
ERROR:  SAVEPOINT can only be used in       (에러 없음 — 통과한다)
        transaction blocks                  ROLLBACK TO SAVEPOINT sp9
                                            ERROR 1305 (42000) at line 1:
                                              SAVEPOINT sp9 does not exist
  -> 그 자리에서 막는다                        -> 그 자리는 통과하고 나중에 터진다
```

MySQL 쪽 출력을 그대로 읽으면 — **`SAVEPOINT` 문 자체는 통과했고, 바로 다음 줄에서 그 이름이 없다고 한다.**\
자동 커밋 상태라 그 문이 곧 하나의 트랜잭션이었고, 트랜잭션이 끝나면 표식도 남지 않는다는 뜻으로 읽힌다.

### ㅁ. 괄호를 두 번 열면 — PG 는 경고, MySQL 은 조용히 커밋

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
BEGIN;                                      START TRANSACTION
BEGIN                                       UPDATE t55_acct SET bal = 777 WHERE id = 1
BEGIN;                                      START TRANSACTION          <- 여기서 암묵 커밋
WARNING:  there is already a                ROLLBACK
          transaction in progress           SELECT id, bal ...
BEGIN                                       +----+------+
COMMIT;                                     | id | bal  |
COMMIT                                      +----+------+
COMMIT;                                     |  1 |  777 |   <- 살아남았다
WARNING:  there is no transaction           |  2 | 1000 |
          in progress                       +----+------+
COMMIT                                      SHOW WARNINGS
                                            (빈 결과 — 경고가 하나도 없다)
```

★ **MySQL 은 경고조차 안 준다.** `SHOW WARNINGS` 를 따로 물어도 비어 있다.\
중첩 트랜잭션을 흉내 내려던 코드가 **앞 구간을 커밋해 버리는** 자리가 정확히 여기다.\
진짜 중첩이 필요하면 **`SAVEPOINT` 가 유일한 수단**이다 — 두 엔진 다 트랜잭션은 중첩되지 않는다.

### ㅂ. 「에러 없이 돌았다」가 「되돌릴 수 있다」는 아니다

MySQL 의 DDL(4번), 두 번째 `START TRANSACTION`(ㅁ), `SET autocommit=1` 로의 전환은 **전부 조용히 커밋한다.**\
`ROLLBACK` 이 성공 응답을 줘도 **지울 것이 없었을 뿐**일 수 있다. 되돌아갔는지는 **표를 다시 읽어서** 확인한다.

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 |
|---|---|
| `BEGIN`·`COMMIT`·`ROLLBACK`·`SAVEPOINT`·`ROLLBACK TO`·`RELEASE` 의 **의미** | 두 엔진이 같다. 문서로 보장된다 |
| **기본이 자동 커밋**이라는 것 | 두 엔진이 같다 |
| 자동 커밋을 **어디서 끄나** | 갈린다 — PG 는 클라이언트, MySQL 은 서버 세션 변수(`@@autocommit`) |
| 에러 뒤 트랜잭션이 **사는가 죽는가** | **갈린다.** PG = 중단, MySQL = 문 단위 롤백 후 계속 |
| **DDL 이 트랜잭션 안에 들어가는가** | **갈린다.** PG = 들어간다, MySQL = 암묵 커밋 |
| 중첩 `BEGIN` 의 처리 | **갈린다.** PG = 경고 + 무시, MySQL = 암묵 커밋 + 무경고 |
| 트랜잭션 밖 `SAVEPOINT` | **갈린다.** PG = 에러, MySQL = 통과 |
| `ERROR 1062` / `ERROR 1305` 같은 **번호** | MySQL 구현 세부다. 번호로 분기하는 코드는 버전에 묶인다 |
| PG 의 `CONTEXT:` 줄 형식 | 구현 세부다. 문자열 매칭 금지 |

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 두 문 이상이 하나의 사실을 이룰 때.** 출금과 입금, 주문과 재고 차감, 본문과 첨부.
- **쓴다 — 여러 행을 같은 기준으로 한꺼번에 바꿀 때.** 절반만 바뀐 상태가 의미 없는 경우.
- **쓴다 — 실패해도 되는 구간이 섞여 있을 때.** 그 구간만 `SAVEPOINT` 로 감싼다.
- **안 쓴다 — 문 하나로 끝나는 일.** 자동 커밋이 이미 원자적이다. 괄호는 비용만 는다.
- **안 쓴다 — 괄호 안에 외부 API 호출을 넣는 것.** 잠금 유지 시간이 네트워크 지연만큼 늘어난다\
  ([`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 자문 체크리스트 마지막 항목).
- **조심 — MySQL 에서 DDL 을 섞는 마이그레이션.** 괄호가 안 먹으므로 **되돌리는 스크립트를 따로 준비**한다.

## 핵심 문장

- **두 엔진 다 기본은 자동 커밋이다 — 괄호를 안 치면 문 하나가 이미 트랜잭션 하나이고 이미 끝났다.**
- **PG 는 에러 하나에 트랜잭션 전체가 중단되고, MySQL 은 그 문만 되돌리고 계속 산다 — 같은 코드가 한쪽에서는 전부 취소, 한쪽에서는 절반 커밋이 된다.**
- **`ROLLBACK TO SAVEPOINT` 는 표식 이후만 지우고 트랜잭션은 끝내지 않는다. `RELEASE` 는 아무것도 되돌리지 않는다.**
- **MySQL 의 DDL 과 두 번째 `START TRANSACTION` 은 진행 중이던 트랜잭션을 경고 없이 커밋한다.**
- **`ROLLBACK` 이 성공했다고 되돌아간 것이 아니다 — 지울 것이 없었을 수도 있다. 표를 다시 읽어 확인한다.**

## 관련 자료

- [`ops-patterns/07-outbox`](../../../../../ops-patterns/07-outbox/) — **발행 패턴은 거기**(왜 메시지를 표에 먼저 적고 나중에 보내나).\
  **여기는 그 패턴이 딛고 서는 트랜잭션 문법까지**다 — 「같은 트랜잭션에 넣는다」가 실제로 어떤 문인가.
- [`engineering-axes/concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) — **동시성의 개념·도구 선택은 거기가 정본**이다.\
  **여기는 트랜잭션 경계 문법까지**이고, 격리 수준은 [56번](../56-isolation-levels-read-phenomena-mvcc/)이 맡는다.
- [56 격리 수준과 읽기 이상 현상·MVCC](../56-isolation-levels-read-phenomena-mvcc/) — 괄호 **안에서 남의 변경이 보이는 정도**.
- [57 명시적 잠금과 교착](../57-explicit-locking-and-deadlock/) — 괄호가 **무엇을 쥐고 있나**.
- [52 UPSERT](../52-upsert/) — 「`SELECT` 후 `INSERT`」의 틈을 **문 하나로** 없애는 쪽.
- [49 INSERT](../49-insert-multi-row-and-insert-select/) · [51 DELETE 와 TRUNCATE](../51-delete-and-truncate/) — MySQL 의 `TRUNCATE` 도 암묵 커밋이다.

## 용어 풀이

- **트랜잭션(transaction)** — 전부 반영되거나 전부 안 된 것으로 치는 문들의 묶음.
- **자동 커밋(autocommit)** — 문 하나를 트랜잭션 하나로 보고 끝나면 바로 확정하는 모드. 두 엔진의 기본값.
- **커밋(commit)** — 트랜잭션의 변경을 확정해 다른 접속에게 보이게 하는 것.
- **롤백(rollback)** — 트랜잭션의 변경을 전부 없던 일로 만드는 것.
- **원자성(atomicity)** — 묶음이 전부 되거나 전부 안 되는 성질. 트랜잭션이 지키는 첫 번째 것.
- **세이브포인트(savepoint)** — 트랜잭션 안에 이름을 붙인 되돌림 지점.
- **중단된 트랜잭션(aborted transaction)** — PG 에서 에러 뒤의 상태. 끝내는 것 말고는 아무것도 못 한다.
- **문 단위 롤백(statement rollback)** — 실패한 문만 되돌리고 트랜잭션은 유지하는 것. MySQL 의 기본 동작.
- **암묵 커밋(implicit commit)** — 어떤 문이 진행 중인 트랜잭션을 대신 커밋해 버리는 것. MySQL 의 DDL 이 대표.
- **DDL(Data Definition Language)** — `CREATE`·`ALTER`·`DROP` 처럼 **스키마를 바꾸는 문**.
- **DML(Data Manipulation Language)** — `INSERT`·`UPDATE`·`DELETE` 처럼 **행을 바꾸는 문**.

## 더 들어가면

- **`COMMIT` 은 공짜가 아니다.** 커밋 시점에 변경 로그를 디스크로 내려야 내구성이 생긴다.\
  10만 행을 한 행씩 자동 커밋으로 넣는 것과 한 괄호에 넣는 것의 차이가 여기서 난다.
- **긴 트랜잭션의 대가.** 괄호가 열려 있는 동안 엔진은 옛 버전의 행을 못 버린다([56번](../56-isolation-levels-read-phenomena-mvcc/)의 MVCC).\
  「사람이 화면에서 확인 버튼을 누를 때까지 트랜잭션을 열어 두는」 설계가 DB 를 조용히 부풀린다.
- **`AND CHAIN` 의 쓸모.** 배치 루프에서 커밋 뒤 **같은 격리 수준으로** 다음 묶음을 시작하고 싶을 때 한 줄로 줄인다.
- **2단계 커밋(`PREPARE TRANSACTION`).** PG 에는 분산 트랜잭션용 2단계 커밋 문법이 따로 있다.\
  이 편의 범위 밖이고, 분산 조율의 위험은 [`ops-patterns/11-distributed-lock`](../../../../../ops-patterns/11-distributed-lock/) 쪽 이야기다.
