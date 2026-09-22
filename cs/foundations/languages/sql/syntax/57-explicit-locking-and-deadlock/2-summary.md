# sql/57-명시적 잠금과 교착 — `FOR UPDATE`·`SKIP LOCKED`·`NOWAIT` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · SELECT — The Locking Clause](https://www.postgresql.org/docs/18/sql-select.html#SQL-FOR-UPDATE-SHARE) · [Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html) · [MySQL 8.4 · Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html) · [InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html) · [Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **이 주제는 설정에 달려 있다** — 잠금 대기 제한과 교착 감지가 전부 설정이다. 그래서 「환경 확인」이 본문 앞에 있다.\
> ★★ **대기·교착은 반드시 타임아웃을 먼저 걸고 시험했다.** 두 접속 모두 `lock_timeout = '3s'` / `innodb_lock_wait_timeout = 3` 을 첫 줄로 깔았다.\
> **맨몸으로 무한 대기를 걸지 않았고, 강제로 끊은 세션도 없다**(3-answer 의 「실행 검증」).\
> ★ **정본 경계** — 여러 인스턴스를 조율하는 **분산 락은 [`ops-patterns/11-distributed-lock`](../../../../../ops-patterns/11-distributed-lock/) 이 정본**이다.\
> **여기는 한 DB 안의 행 잠금 문법과 그 잠금이 실제로 어디에 걸리는가까지**다.\
> **이 편이 만든 객체와 그 뒷정리** — 표 `t57_q`(4행) · `t57_lk`(3행, 인덱스 없음) · `t57_ix`(3행, `grp` 에 인덱스).\
> **끝나고 두 엔진에서 `DROP` 했다**(3-answer).\
> ★ **기존 `emp`·`dept` 는 읽지도 잠그지도 않았다.** 다른 사람이 쓰는 표를 잠그면 그 사람이 멈춘다.\
> **선행** — [56 격리 수준과 읽기 이상 현상·MVCC](../56-isolation-levels-read-phenomena-mvcc/). 잠금 읽기가 스냅샷과 다르게 도는 이유가 거기 있다.

## 한눈에 — 쉽게 말하면

**`FOR UPDATE` 는 「이 줄 내가 고칠 거니까 손대지 마」라고 읽으면서 표시해 두는 것이다.**

- 도서관 열람실에 자리가 넷 있다. 네 사람이 동시에 들어온다.
- **표시 없이 읽기만 하면** — 넷이 같은 자리를 보고 「비었네」 하고 넷 다 앉는다.
- **`FOR UPDATE`** — 자리를 보면서 **의자에 가방을 올려 둔다.** 다른 사람은 그 자리에 못 앉는다.
- **기본 동작** — 뒷사람은 **가방이 치워질 때까지 서서 기다린다.**
- **`NOWAIT`** — 기다리지 않고 **즉시 「자리 없음」이라고 돌아선다.**
- **`SKIP LOCKED`** — 가방 있는 자리는 **그냥 건너뛰고** 다음 빈자리에 앉는다.
- **교착** — 둘이 서로의 가방을 기다린다. **DB 가 한쪽을 강제로 일으켜 세운다.**

| 비유 | 실체 |
|---|---|
| 자리를 보면서 가방을 올려 둔다 | `SELECT … FOR UPDATE` |
| 남이 못 고치되 읽기는 된다 | `SELECT … FOR SHARE` |
| 가방이 치워질 때까지 서 있는다 | **기본 동작 — 대기** |
| 서 있다가 지쳐 포기한다 | **잠금 타임아웃** (`lock_timeout` · `innodb_lock_wait_timeout`) |
| 즉시 돌아선다 | `NOWAIT` |
| 가방 있는 자리는 건너뛴다 | `SKIP LOCKED` |
| 서로의 가방을 기다린다 | **교착(deadlock)** |
| 한쪽을 강제로 일으켜 세운다 | **희생자 선정 — 한 트랜잭션이 롤백된다** |

```text
        SKIP LOCKED 없음                     SKIP LOCKED 있음
        ────────────────                     ────────────────
 워커 A  [1] 잠금                      워커 A  [1] 잠금
 워커 B  [1] ... 대기 ... 타임아웃      워커 B  [1] 건너뜀 -> [2] 잠금
 워커 C  [1] ... 대기 ... 타임아웃      워커 C  [1][2] 건너뜀 -> [3] 잠금

 한 줄에 셋이 몰려 둘이 죽는다           셋이 서로 다른 일을 집어 간다
```

**똑같은 구조다** — 「큐 테이블에서 일감을 꺼내는 워커를 3대로 늘렸더니 오히려 느려졌다」의 답이 위 왼쪽 그림이다.

> **명시적 잠금(explicit locking)** — 엔진이 알아서 거는 잠금 말고, 내가 문법으로 **직접 요청하는** 잠금.\
> 예: `SELECT … FOR UPDATE` 는 「읽으면서 잠가 달라」는 요청이다.

> **잠금 읽기(locking read)** — `FOR UPDATE`·`FOR SHARE` 를 붙인 `SELECT`. 일반 `SELECT` 와 달리 **행을 잠근다.**\
> 예: 좌석 선점에서 「빈자리 확인」과 「내 것으로 만들기」 사이의 틈을 없앤다.

> **교착(deadlock)** — 두 트랜잭션이 서로가 쥔 잠금을 기다려 둘 다 못 나아가는 상태.\
> 예: A 가 1번을 쥐고 2번을 기다리는데, B 가 2번을 쥐고 1번을 기다린다.

## 이 주제가 답하려는 질문

1. **잠금 읽기는 무엇을 막고, 못 잡으면 어떻게 되나** — 대기·타임아웃·즉시 실패·건너뛰기의 네 갈래.
2. **잠금은 「행」에 걸리나** — ★ 아니다. **인덱스에 걸린다.** 그래서 인덱스가 없으면 무엇이 넓어지나.
3. **교착은 어떻게 생기고 누가 죽나** — 그리고 그 기록을 어디서 읽나.

## 환경 확인 — 물어보고 시작한다

★ **이 절을 건너뛰면 아래의 모든 「기다렸다 실패했다」가 검증 불가가 된다.**

```text
### SQL: (PG) SHOW lock_timeout;  SHOW statement_timeout;  SHOW deadlock_timeout;  SHOW transaction_isolation;
--- PG 18.6 ---
 lock_timeout        statement_timeout     deadlock_timeout     transaction_isolation
--------------      -------------------   ------------------   -----------------------
 0                   0                     1s                   read committed
```

```text
### SQL: (MySQL) SELECT @@innodb_lock_wait_timeout, @@lock_wait_timeout, @@innodb_deadlock_detect, @@transaction_isolation;
--- MySQL 8.4.10 ---
@@innodb_lock_wait_timeout: 50
       @@lock_wait_timeout: 31536000
  @@innodb_deadlock_detect: 1
   @@transaction_isolation: REPEATABLE-READ
```

| 물어본 것 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| **행 잠금 대기 제한** | `lock_timeout = 0` — ★ **무제한** | `innodb_lock_wait_timeout = 50` 초 |
| 문 전체 시간 제한 | `statement_timeout = 0` — 무제한 | (`max_execution_time` · 기본 0) |
| 메타데이터 잠금 대기 | — | `lock_wait_timeout = 31536000` 초(1년) |
| 교착 감지 | `deadlock_timeout = 1s` 뒤 검사 | `innodb_deadlock_detect = 1` |
| 격리 수준 | `read committed` | `REPEATABLE-READ` |

★ **PG 의 기본값은 무제한이다.** 잠금 실험을 맨몸으로 하면 **세션이 영원히 남는다.**\
그래서 아래 실험은 **전부 이렇게 시작한다.**

```sql
-- PG (두 접속 모두)
SET lock_timeout = '3s';
SET statement_timeout = '10s';
-- MySQL (두 접속 모두)
SET SESSION innodb_lock_wait_timeout = 3;
SET SESSION max_execution_time = 10000;
```

## 예시 데이터 — 이 묶음이 공유하는 것

```sql
CREATE TABLE t57_q  (id int PRIMARY KEY, payload text, state text);    -- 큐
INSERT INTO t57_q VALUES (1,'job-a','ready'),(2,'job-b','ready'),(3,'job-c','ready'),(4,'job-d','ready');

CREATE TABLE t57_lk (id int PRIMARY KEY, grp int, memo text);          -- grp 에 인덱스 없음
CREATE TABLE t57_ix (id int PRIMARY KEY, grp int, memo text);          -- grp 에 인덱스 있음
INSERT INTO t57_lk VALUES (1,10,'x'),(2,20,'y'),(3,30,'z');
INSERT INTO t57_ix VALUES (1,10,'x'),(2,20,'y'),(3,30,'z');
CREATE INDEX t57_ix_grp ON t57_ix (grp);
```

```text
t57_q (큐 · 4행)                 t57_lk / t57_ix (3행씩 · 같은 데이터)
+----+---------+-------+         +----+-----+------+
| id | payload | state |         | id | grp | memo |
+----+---------+-------+         +----+-----+------+
|  1 | job-a   | ready |         |  1 |  10 | x    |
|  2 | job-b   | ready |         |  2 |  20 | y    |
|  3 | job-c   | ready |         |  3 |  30 | z    |
|  4 | job-d   | ready |         +----+-----+------+
+----+---------+-------+         차이는 딱 하나 — t57_ix 에만 grp 인덱스가 있다
```

★ **`t57_lk` 와 `t57_ix` 는 데이터가 같고 인덱스만 다르다.** 2번 절의 실험대다.

## 동작 방식

### 1. 못 잡았을 때의 네 갈래 — 대기 · 타임아웃 · `NOWAIT` · `SKIP LOCKED`

**언제 쓰나** — 두 워커가 같은 행을 노릴 때. **무엇을 고르느냐가 곧 설계다.**

```text
세션 A: BEGIN;  SELECT ... WHERE id = 1 FOR UPDATE;     <- 1번 행을 쥐었다
세션 B: BEGIN;  SELECT ... WHERE id = 1 FOR UPDATE ... ;  <- 어떻게 되나?
```

```text
(A) 그냥 FOR UPDATE — 기다리다 타임아웃      (B) FOR UPDATE NOWAIT — 즉시 실패
--- PG 18.6 ---                             --- PG 18.6 ---
ERROR:  canceling statement due to           ERROR:  could not obtain lock on row
        lock timeout                                 in relation "t57_q"
CONTEXT:  while locking tuple (0,1)
          in relation "t57_q"                --- MySQL 8.4.10 ---
                                            ERROR 3572 (HY000) at line 4: Statement
--- MySQL 8.4.10 ---                          aborted because lock(s) could not be
ERROR 1205 (HY000) at line 3: Lock wait       acquired immediately and NOWAIT is set.
  timeout exceeded; try restarting
  transaction                                 -> 3초도 안 기다린다. 바로 돌아선다
 -> 3초를 서 있다가 포기했다
```

```text
(C) FOR UPDATE SKIP LOCKED — 건너뛴다
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
SELECT id, payload FROM t57_q               SELECT id, payload FROM t57_q
  WHERE state = 'ready' ORDER BY id           WHERE state = 'ready' ORDER BY id
  FOR UPDATE SKIP LOCKED;                     FOR UPDATE SKIP LOCKED
 id | payload                                +----+---------+
----+---------                               | id | payload |
  2 | job-b                                  +----+---------+
  3 | job-c                                  |  2 | job-b   |
  4 | job-d                                  |  3 | job-c   |
(3 rows)                                     |  4 | job-d   |
                                             +----+---------+
  -> 1번이 결과에서 통째로 빠졌다               -> 두 엔진의 답이 같다
```

그림 해설 — **기본은 대기다.** 그리고 타임아웃이 없으면 **영원히** 기다린다(PG 기본이 그렇다).\
`NOWAIT` 은 「대기 시간 0」이 아니라 **다른 에러**다 — 에러 번호도 메시지도 타임아웃과 다르다.\
`SKIP LOCKED` 는 **에러가 아니다.** 결과 집합이 조용히 줄어든다.\
비용 — `SKIP LOCKED` 는 **「전부 처리한다」는 보장을 포기하고 처리량을 산다.** 「한 건도 놓치면 안 되는」 조회에 쓰면 사고다.

> **`NOWAIT`** — 잠금을 즉시 못 잡으면 기다리지 않고 에러를 내는 옵션.\
> 예: 화면에서 「지금 다른 사람이 수정 중입니다」를 바로 띄우고 싶을 때.

> **`SKIP LOCKED`** — 잠긴 행을 **결과에서 빼고** 나머지만 돌려주는 옵션.\
> 예: 큐에서 일감을 꺼낼 때 남이 잡은 일은 건너뛰고 다음 것을 집는다.

★ **`SKIP LOCKED` 와 `NOWAIT` 은 같이 못 쓴다** — 두 엔진이 똑같이 거부한다.

```text
### SQL: SELECT id FROM t57_lk WHERE id=1 FOR UPDATE SKIP LOCKED NOWAIT;
--- PG 18.6 ---
ERROR:  syntax error at or near "NOWAIT"
LINE 1: ...ECT id FROM t57_lk WHERE id=1 FOR UPDATE SKIP LOCKED NOWAIT;
                                                                ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 4: ... near 'NOWAIT' at line 1
```

### 2. ★ 큐 소비 — 두 워커가 서로 다른 일을 집는다

**언제 쓰나** — 작업 큐를 표로 구현했을 때. **`SKIP LOCKED` 가 푸는 문제가 정확히 이것이다.**

```text
시간   워커 A                                     워커 B
 1     BEGIN;
 2     SELECT ... WHERE state='ready'
         ORDER BY id LIMIT 1
         FOR UPDATE SKIP LOCKED;   -> job-a (id=1)
 3                                               BEGIN;
 4                                               (같은 질의)  -> ?
 5     UPDATE ... state='done' WHERE id=1;
 6                                               UPDATE ... state='done' WHERE id=2;
 7     COMMIT;                                   COMMIT;
```

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
[워커 A]                                     [워커 A]
 id | payload                                +----+---------+
----+---------                               | id | payload |
  1 | job-a                                  +----+---------+
(1 row)                                      |  1 | job-a   |
                                             +----+---------+
[워커 B]
 id | payload                                [워커 B]
----+---------                               +----+---------+
  2 | job-b                                  | id | payload |
(1 row)                                      +----+---------+
                                             |  2 | job-b   |
[끝난 뒤]                                     +----+---------+
 id | state
----+-------                                 [끝난 뒤]
  1 | done                                   +----+-------+
  2 | done                                   | id | state |
  3 | ready                                  +----+-------+
  4 | ready                                  |  1 | done  |
(4 rows)                                     |  2 | done  |
                                             |  3 | ready |
                                             |  4 | ready |
                                             +----+-------+
```

그림 해설 — **B 의 `LIMIT 1` 이 2번을 집었다.** 1번이 잠겨 있어 후보에서 빠졌기 때문이다.\
`SKIP LOCKED` 가 없으면 B 는 **1번을 기다리다 죽는다** — 아래가 그 출력이다.

```text
### SQL: (SKIP LOCKED 없이) SELECT ... ORDER BY id LIMIT 1 FOR UPDATE;
--- PG 18.6 · 워커 B ---
ERROR:  canceling statement due to lock timeout
CONTEXT:  while locking tuple (0,9) in relation "t57_q"
```

비용 — 순서 보장이 약해진다. **「먼저 들어온 일감이 먼저 처리된다」가 깨진다.**\
그리고 트랜잭션이 길면 잠금도 길다 — **일감 처리 전체를 한 트랜잭션에 넣으면** 다른 워커가 그만큼 오래 건너뛴다.

### 3. ★ 잠금은 행이 아니라 인덱스에 걸린다

**언제 쓰나** — 「한 줄만 잠갔는데 왜 다른 줄까지 멈추지?」일 때. **이 절이 이 편의 가장 비싼 부분이다.**

데이터가 같고 **인덱스만 다른** 두 표에 같은 질의를 던진다. `grp = 10` 인 행은 **하나뿐**이다.

```text
세션 A: BEGIN;  SELECT ... WHERE grp = 10 FOR UPDATE;   -> 1행 (id=1)
세션 B: BEGIN;  SELECT ... WHERE id  = 3  FOR UPDATE;   -> 되나?
```

**(A) MySQL 8.4.10 · `t57_lk` — `grp` 에 인덱스가 없다**

```text
### 세션 A: SELECT id, grp FROM t57_lk WHERE grp = 10 FOR UPDATE;   -> 1행 (id=1)
### 세션 A: SELECT INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_DATA FROM performance_schema.data_locks WHERE OBJECT_NAME='t57_lk';
+------------+-----------+-----------+------------------------+
| INDEX_NAME | LOCK_TYPE | LOCK_MODE | LOCK_DATA              |
+------------+-----------+-----------+------------------------+
| NULL       | TABLE     | IX        | NULL                   |
| PRIMARY    | RECORD    | X         | supremum pseudo-record |
| PRIMARY    | RECORD    | X         | 1                      |
| PRIMARY    | RECORD    | X         | 2                      |
| PRIMARY    | RECORD    | X         | 3                      |
+------------+-----------+-----------+------------------------+
### 세션 B: SELECT id, grp FROM t57_lk WHERE id = 3 FOR UPDATE;
ERROR 1205 (HY000) at line 3: Lock wait timeout exceeded; try restarting transaction
```

**(B) MySQL 8.4.10 · `t57_ix` — `grp` 에 인덱스가 있다 (질의는 한 글자도 같다)**

```text
### 세션 A: SELECT id, grp FROM t57_ix WHERE grp = 10 FOR UPDATE;   -> 1행 (id=1)
### 세션 A: SELECT INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_DATA FROM performance_schema.data_locks WHERE OBJECT_NAME='t57_ix';
+------------+-----------+---------------+-----------+
| INDEX_NAME | LOCK_TYPE | LOCK_MODE     | LOCK_DATA |
+------------+-----------+---------------+-----------+
| NULL       | TABLE     | IX            | NULL      |
| t57_ix_grp | RECORD    | X,GAP         | 20, 2     |
| t57_ix_grp | RECORD    | X             | 10, 1     |
| PRIMARY    | RECORD    | X,REC_NOT_GAP | 1         |
+------------+-----------+---------------+-----------+
### 세션 B: SELECT id, grp FROM t57_ix WHERE id = 3 FOR UPDATE;
+----+------+
| id | grp  |
+----+------+
|  3 |   30 |
+----+------+
```

```text
 인덱스 없음 (t57_lk)                     인덱스 있음 (t57_ix)
 +---------------------------+            +---------------------------+
 | PRIMARY 의 1, 2, 3 전부   |            | t57_ix_grp 의 "10" 한 칸  |
 | + supremum (맨 끝 뒤)     |            | + 그 다음 칸 앞의 빈 구간  |
 |                           |            | + PRIMARY 의 1 한 칸      |
 +---------------------------+            +---------------------------+
   -> 세션 B 가 3번 행을 못 잡는다            -> 세션 B 가 3번 행을 잡는다
   -> 한 행을 골랐는데 표 전체가 멈췄다         -> 고른 행만 멈춘다
```

두 그림의 결론 — **`INDEX_NAME` 칸을 보라.** 잠금은 **표가 아니라 인덱스 위의 자리**에 걸린다.\
인덱스가 없으면 엔진은 **훑은 모든 자리**를 잠근다. 조건에 안 맞는 행까지 전부다.\
인덱스가 있으면 **인덱스에서 짚은 자리만** 잠근다.

★ **[46 인덱스 정의](../46-index-definition-composite-partial-expression/)·[47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)가 여기로 이어진다.**\
47번이 「인덱스를 못 타면 느려진다」를 다룬다면, **이 편은 「인덱스를 못 타면 잠금이 넓어진다**」를 더한다.\
느려지는 것은 나 혼자의 문제이고, **잠금이 넓어지는 것은 남까지 멈추는 문제다.**

**PostgreSQL 에서는 같은 실험이 다르게 나온다.**

```text
--- PG 18.6 · t57_lk (인덱스 없음) ---
[세션 A] SELECT id, grp FROM t57_lk WHERE grp = 10 FOR UPDATE;
 id | grp
----+-----
  1 |  10
(1 row)

[세션 B] SELECT id, grp FROM t57_lk WHERE id = 3 FOR UPDATE;
 id | grp
----+-----
  3 |  30
(1 row)                 <- 막히지 않는다

[세션 B] SELECT locktype, relation::regclass AS rel, mode FROM pg_locks WHERE relation = 't57_lk'::regclass;
 locktype |  rel   |     mode
----------+--------+--------------
 relation | t57_lk | RowShareLock
 relation | t57_lk | RowShareLock
(2 rows)
```

★ **PG 는 인덱스가 없어도 B 를 막지 않았다.** 그리고 `pg_locks` 에는 **표 수준 잠금 둘만** 보인다.\
PG 의 행 잠금은 **행 자체에 표시로 남기 때문에** 이 뷰에 안 나온다 — **「잠금이 안 보인다」가 「잠금이 없다」가 아니다.**

비용 — MySQL 쪽은 **인덱스 설계가 곧 동시성 설계**다. PG 쪽은 그 결합이 약한 대신,\
**`pg_locks` 만 봐서는 누가 무슨 행을 쥐었는지 알 수 없다.**

> **넥스트 키 락(next-key lock)** — InnoDB 가 **인덱스 레코드 하나 + 그 앞의 빈 구간**을 함께 잠그는 형태.\
> 예: 위 `X` (레코드) 와 `X,GAP` (빈 구간) 이 나란히 잡힌 것이 그 모습이다.

> **`supremum pseudo-record`** — InnoDB 가 인덱스의 **맨 끝 뒤**를 가리키려고 두는 가상의 레코드.\
> 예: 위 왼쪽 표에 그것이 잠긴 것은 **「마지막 행보다 큰 모든 자리」까지 잠갔다**는 뜻이다.

### 4. ★ 갭 락 — 내가 잠근 범위에 남이 못 들어온다

**언제 쓰나** — 「범위를 확인하고 그 범위에 넣는」 코드. 예약·중복 검사가 전부 이 모양이다.

```text
세션 A: BEGIN;  SELECT ... WHERE grp BETWEEN 10 AND 20 FOR UPDATE;   -> 2행
세션 B: BEGIN;  INSERT INTO t57_ix VALUES (5, 15, 'new');            -> 되나?
세션 A: 같은 SELECT 를 다시                                          -> 몇 행?
```

```text
(A) MySQL 8.4.10 · REPEATABLE READ          (B) PG 18.6 · READ COMMITTED
[A] 첫 읽기                                  [A] 첫 읽기
+----+------+                                id | grp
| id | grp  |                               ----+-----
+----+------+                                 1 |  10
|  1 |   10 |                                 2 |  20
|  2 |   20 |                               (2 rows)
+----+------+
                                            [B] INSERT INTO t57_ix VALUES (5,15,'new');
[B] INSERT INTO t57_ix VALUES (5,15,'new')  INSERT 0 1
ERROR 1205 (HY000) at line 3: Lock wait     [B] COMMIT;   -> COMMIT
  timeout exceeded; try restarting
  transaction                                [A] 다시 읽으면
                                             id | grp
[A] 다시 읽으면                              ----+-----
+----+------+                                 1 |  10
| id | grp  |                                 2 |  20
+----+------+                                 5 |  15     <- 없던 행이 생겼다
|  1 |   10 |                               (3 rows)
|  2 |   20 |
+----+------+                                 -> 팬텀이 났다
  -> 같은 2행. 팬텀이 안 났다
```

두 그림의 결론 — **MySQL 은 잠긴 범위 안의 빈 구간까지 잠가** 남의 `INSERT` 를 막는다.\
**PG 는 존재하는 행만 잠근다.** 없는 행은 잠글 수 없으므로 `INSERT` 가 통과하고, **팬텀이 난다.**

★ **PG 에서 같은 것을 `REPEATABLE READ` 로 올리면 또 달라진다.**

```text
--- PG 18.6 · REPEATABLE READ · 세션 A ---
첫 읽기:   2행 (1, 2)
(B 가 INSERT 하고 COMMIT)
다시 읽기: 2행 (1, 2)          <- 잠금 읽기인데도 스냅샷을 따른다
COMMIT 뒤 밖에서 읽기: 4행      <- 1, 2, 3, 5
```

**세 가지 답이 나왔다 — 읽는 방식과 수준에 따라 전부 다르다.**

| | 남의 `INSERT` 가 되나 | A 의 재조회 |
|---|---|---|
| MySQL `REPEATABLE READ` + `FOR UPDATE` | **안 된다** (`ERROR 1205`) | 2행 — 팬텀 없음 |
| PG `READ COMMITTED` + `FOR UPDATE` | 된다 | **3행 — 팬텀** |
| PG `REPEATABLE READ` + `FOR UPDATE` | 된다 | 2행 — 스냅샷을 따른다 |

★ **[56번](../56-isolation-levels-read-phenomena-mvcc/)의 「MySQL RR 이 팬텀을 막나」에 대한 답의 절반이 이 표다.**\
거기의 나머지 절반은 — **아직 안 잠근 범위를 잠금 읽기로 처음 읽으면 새 행이 보인다**는 것이다.

> **갭 락(gap lock)** — 인덱스 레코드 **사이의 빈 구간**에 거는 잠금. 그 구간에 새 행을 못 넣게 한다.\
> 예: 위 `X,GAP` — 값 20 앞의 빈 구간을 잠갔으므로 `grp = 15` 가 들어갈 수 없다.

### 5. ★ 교착 — 일부러 만들어 본다

**언제 쓰나** — 두 트랜잭션이 **같은 두 행을 반대 순서로** 잠글 때. 실무에서 가장 흔한 모양이다.

```text
시간   세션 A                              세션 B
 1     BEGIN;                              BEGIN;
 2     SELECT ... id = 1 FOR UPDATE;  OK
 3                                         SELECT ... id = 2 FOR UPDATE;  OK
 4     SELECT ... id = 2 FOR UPDATE;  <- B 가 쥐고 있다. 대기
 5                                         SELECT ... id = 1 FOR UPDATE;  <- A 가 쥐고 있다. 대기
                                              => 사이클 완성
```

```text
--- PG 18.6 · 세션 A 가 희생됐다 ---
SELECT id, memo FROM t57_lk WHERE id = 2 FOR UPDATE;
ERROR:  deadlock detected
DETAIL:  Process 20289 waits for ShareLock on transaction 1221; blocked by process 20288.
Process 20288 waits for ShareLock on transaction 1220; blocked by process 20289.
HINT:  See server log for query details.
CONTEXT:  while locking tuple (0,2) in relation "t57_lk"

--- 세션 B 는 그대로 진행했다 ---
SELECT id, memo FROM t57_lk WHERE id = 1 FOR UPDATE;
 id | memo
----+------
  1 | x
(1 row)
```

```text
--- MySQL 8.4.10 · 세션 B 가 희생됐다 ---
ERROR 1213 (40001) at line 4: Deadlock found when trying to get lock; try restarting transaction
        (4번째 줄 = B 의 두 번째 SELECT)

--- 세션 A 는 그대로 진행했다 ---
SELECT id, memo FROM t57_lk WHERE id = 2 FOR UPDATE
+----+------+
| id | memo |
+----+------+
|  2 | y    |
+----+------+
```

그림 해설 — **둘 다 한쪽만 죽이고 한쪽은 통과시킨다.** 「둘 다 멈춤」이 아니다.\
누가 죽는지는 **엔진이 고른다** — 이 판에서는 PG 가 A 를, MySQL 이 B 를 골랐다.\
★ **어느 쪽이 죽을지 예측하고 코드를 짜면 안 된다.** 죽는 쪽은 **재시도해야 한다.**\
비용 — 교착 자체보다 **감지 대기 시간**이 비싸다. PG 는 `deadlock_timeout = 1s` 를 기다린 뒤에야 검사한다.

★ **MySQL 은 마지막 교착을 통째로 보여 준다.** `SHOW ENGINE INNODB STATUS` 의 한 절이다.

```text
### SQL: SHOW ENGINE INNODB STATUS\G   (LATEST DETECTED DEADLOCK 절만)
--- MySQL 8.4.10 ---
LATEST DETECTED DEADLOCK
------------------------
2026-09-21 07:43:01 125253711812160
*** (1) TRANSACTION:
TRANSACTION 4506, ACTIVE 1 sec starting index read
mysql tables in use 1, locked 1
LOCK WAIT 3 lock struct(s), heap size 1128, 2 row lock(s)
MySQL thread id 2508, OS thread handle 125253801014848, query id 10871 localhost root statistics
SELECT id, memo FROM t57_lk WHERE id = 2 FOR UPDATE

*** (1) HOLDS THE LOCK(S):
RECORD LOCKS space id 107 page no 4 n bits 72 index PRIMARY of table `study`.`t57_lk` trx id 4506 lock_mode X locks rec but not gap

*** (1) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 107 page no 4 n bits 72 index PRIMARY of table `study`.`t57_lk` trx id 4506 lock_mode X locks rec but not gap waiting

*** (2) TRANSACTION:
TRANSACTION 4507, ACTIVE 1 sec starting index read
MySQL thread id 2507, OS thread handle 125254200391232, query id 10872 localhost root statistics
SELECT id, memo FROM t57_lk WHERE id = 1 FOR UPDATE

*** (2) HOLDS THE LOCK(S):
RECORD LOCKS space id 107 page no 4 n bits 72 index PRIMARY of table `study`.`t57_lk` trx id 4507 lock_mode X locks rec but not gap

*** (2) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 107 page no 4 n bits 72 index PRIMARY of table `study`.`t57_lk` trx id 4507 lock_mode X locks rec but not gap waiting

*** WE ROLL BACK TRANSACTION (2)
```

★ **이 출력에서 건질 것이 셋이다.**

1. **두 질의가 그대로 찍힌다** — 어떤 문이 서로를 물었는지 추측할 필요가 없다.
2. **`index PRIMARY of table study.t57_lk`** — 3번 절의 결론이 여기 또 있다. **잠금은 인덱스 위에 있다.**
3. **`*** WE ROLL BACK TRANSACTION (2)`** — 누가 희생됐는지 엔진이 직접 적는다.

(위 블록은 가운데의 레코드 덤프 — `0: len 4; hex 80000001; asc ;;` 같은 바이트 나열 — 만 줄였다. 나머지는 출력 그대로다.)

## 문법 — 형태와 규칙

SQL 에서 이 절의 본체는 「**어느 문에 붙일 수 있나」와 「무엇과 무엇을 같이 못 쓰나**」다.

| 하는 일 | PostgreSQL 18 | MySQL 8.4 |
|---|---|---|
| 쓰기 잠금 | `FOR UPDATE` | `FOR UPDATE` |
| 읽기 잠금 | `FOR SHARE` | `FOR SHARE` · `LOCK IN SHARE MODE`(옛 표기 — 8.4.10 에서도 경고 없이 통과했다) |
| 약한 쓰기 잠금 | `FOR NO KEY UPDATE` | **없다** — `ERROR 1064` |
| 약한 읽기 잠금 | `FOR KEY SHARE` | **없다** |
| 대상 표 지정 | `FOR UPDATE OF <별칭>` | `FOR UPDATE OF <별칭>` |
| 기다리지 않기 | `NOWAIT` | `NOWAIT` |
| 건너뛰기 | `SKIP LOCKED` | `SKIP LOCKED` |
| 둘을 같이 | **구문 오류** | **`ERROR 1064`** |
| 대기 제한 설정 | `SET lock_timeout = '3s';` | `SET SESSION innodb_lock_wait_timeout = 3;` |

★ **PG 는 네 단계, MySQL 은 두 단계다.**

```text
### SQL: SELECT id FROM t57_lk WHERE id=1 FOR NO KEY UPDATE;
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
 id                                         ERROR 1064 (42000) at line 4: You have an error
----                                          in your SQL syntax; ... near 'NO KEY UPDATE'
  1                                           at line 1
(1 row)
```

★ **집계와 함께 쓰면 PG 만 거부한다.**

```text
### SQL: SELECT count(*) FROM t57_lk FOR UPDATE;
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
ERROR:  FOR UPDATE is not allowed with      +----------+
        aggregate functions                 | count(*) |
                                            +----------+
                                            |        3 |
                                            +----------+
```

★ **외부 조인의 NULL 쪽도 PG 만 거부한다.**

```text
### SQL: SELECT id FROM t57_lk LEFT JOIN t57_ix USING (id) FOR UPDATE;
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
ERROR:  FOR UPDATE cannot be applied to     +----+
        the nullable side of an outer join  | id |
                                            +----+
(PG 에서는 대상을 지목하면 통과한다)          |  1 |
SELECT l.id FROM t57_lk l                   |  2 |
  LEFT JOIN t57_ix i USING (id)             |  3 |
  FOR UPDATE OF l;    -> 3행                +----+
```

★ **잠금 읽기는 트랜잭션 안에서만 뜻이 있다.** 자동 커밋으로 던지면 **문이 끝나는 순간 잠금도 풀린다.**\
「잠갔다」와 「쥐고 있다」는 다르다 — 쥐고 있으려면 [55번](../55-transaction-boundaries-commit-rollback-savepoint/)의 괄호가 필요하다.

## 어디서 틀리나

### ㄱ. ★ 대기 제한을 안 걸고 실험하는 것

PG 의 `lock_timeout` 기본값은 **0**(무제한)이다. 잠긴 행을 `FOR UPDATE` 로 건드리면 **영원히 선다.**\
그 세션은 클라이언트를 끊어도 서버에 남을 수 있고, **다른 사람의 작업까지 막는다.**\
**실험 전에 두 접속 모두에 타임아웃을 건다** — 이 편은 그렇게 했고, 그래서 **강제로 끊은 세션이 하나도 없다.**

### ㄴ. `NOWAIT` 과 타임아웃을 같은 것으로 아는 것

에러가 다르다. **분기 코드가 한쪽만 보면 나머지 한쪽에서 잘못 동작한다.**

| 상황 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 기다리다 포기 | `ERROR: canceling statement due to lock timeout` | `ERROR 1205 … Lock wait timeout exceeded` |
| `NOWAIT` 즉시 실패 | `ERROR: could not obtain lock on row in relation "…"` | `ERROR 3572 … NOWAIT is set.` |
| 교착 | `ERROR: deadlock detected` | `ERROR 1213 … Deadlock found` |

### ㄷ. ★ `SKIP LOCKED` 를 일반 조회에 쓰는 것

`SKIP LOCKED` 는 **결과가 조용히 줄어든다.** 에러도 경고도 없다.\
「전체 목록」·「합계」·「건수」에 붙이면 **답이 틀린 채 성공한다** — 동시성 실패의 전형적인 모양이다.\
쓰는 자리는 **「아무거나 하나 집어서 처리하면 되는」 큐뿐**이다.

### ㄹ. ★ 인덱스 없는 열로 잠그는 것 (MySQL)

3번 절이 그대로 사고다. `WHERE grp = 10` 한 줄로 **표 전체가 잠겼다.**\
`EXPLAIN` 으로 그 질의가 인덱스를 타는지부터 확인한다([47번](../47-when-indexes-are-used/)).\
★ **느린 질의는 나만 느리지만, 잠금이 넓은 질의는 남까지 멈춘다.**

### ㅁ. 잠그는 순서가 제각각인 것

5번의 교착은 **순서를 맞추기만 해도 안 난다.** 둘 다 `id` 오름차순으로 잠그면 사이클이 안 생긴다.\
그래서 처방은 「교착을 없앤다」가 아니라 「**잠그는 순서를 코드의 규약으로 고정한다**」이다.\
그래도 남는 교착은 **재시도**로 받는다 — 두 엔진의 메시지가 똑같이 그렇게 말한다(`try restarting transaction`).

### ㅂ. 트랜잭션을 길게 쥐고 있는 것

잠금은 `COMMIT`/`ROLLBACK` 까지 유지된다. 괄호 안에 **외부 API 호출·사람의 확인·파일 업로드**가 들어가면\
그 시간만큼 남이 기다린다([`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 자문 체크리스트 마지막 항목).

### ㅅ. `pg_locks` 가 비었다고 잠금이 없다고 믿는 것

PG 의 행 잠금은 **행 자체에 표시**로 남는다. 3번 절의 `pg_locks` 출력에 보이는 것은 **표 수준 `RowShareLock` 둘뿐**이었다.\
**「안 보인다」가 「없다」가 아니다.**

### ㅇ. 잠금으로 「없는 행」을 막으려는 것

`FOR UPDATE` 는 **존재하는 행만** 잠근다. 신규 삽입 경쟁에는 안 통한다(PG 쪽 4번 그림이 그것이다).\
그 자리는 **유니크 제약 + upsert** 가 맡는다([52 UPSERT](../52-upsert/)).\
MySQL 의 갭 락은 그 틈을 일부 메우지만, **엔진과 격리 수준에 의존하는 방어**라 이식성이 없다.

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 |
|---|---|
| `FOR UPDATE`·`FOR SHARE`·`NOWAIT`·`SKIP LOCKED` 의 **문법과 의미** | 두 엔진이 같다 |
| `SKIP LOCKED` 의 **결과**(잠긴 행이 빠진다) | 두 엔진이 같다 — 큐 실험에서 한 자리도 안 갈렸다 |
| `SKIP LOCKED` + `NOWAIT` **동시 사용 거부** | 두 엔진이 같다 |
| **잠금 단계의 수** | **갈린다.** PG 4단계(`FOR UPDATE`/`NO KEY UPDATE`/`SHARE`/`KEY SHARE`), MySQL 2단계 |
| **인덱스가 없을 때 잠금 범위** | **갈린다.** MySQL = 훑은 자리 전부, PG = 고른 행만 |
| **갭 락의 유무** | **갈린다.** MySQL = 있다, PG = 없다 |
| 집계·외부 조인 NULL 쪽에 붙이기 | **갈린다.** PG = 에러, MySQL = 통과 |
| **누가 희생되나** | **엔진이 고른다.** 이 판에서는 PG 가 A, MySQL 이 B 를 골랐다 — **예측하면 안 된다** |
| 대기 제한 **기본값** | **갈린다.** PG = 0(무제한), MySQL = 50초 |
| 에러 번호(`1205`·`1213`·`3572`·`1064`) · `CONTEXT:` 형식 · `LOCK_DATA` 표기 | 구현 세부다. **문자열 매칭 금지** |

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 큐에서 일감 꺼내기.** `FOR UPDATE SKIP LOCKED` + `LIMIT`. 이 편의 2번이 그 모양 그대로다.
- **쓴다 — 좌석·재고 선점.** 확인과 차지 사이의 틈을 없앤다.
- **쓴다 — 「지금 다른 사람이 수정 중」을 즉시 알려야 할 때.** `NOWAIT`.
- **안 쓴다 — 조건부 갱신으로 되는 일.** `UPDATE … WHERE qty >= 1` 한 문이 더 싸고 확실하다\
  ([`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 「선택 순서」 2단계 — 잠금은 4단계다).
- **안 쓴다 — 충돌이 드물 때.** 낙관적 락(version 열)이 처리량을 덜 깎는다.
- **안 쓴다 — 없는 행을 막는 일.** 유니크 제약과 upsert 의 몫이다([52번](../52-upsert/)).
- **안 쓴다 — 여러 인스턴스·여러 저장소를 조율하는 일.** 그것은 분산 락 주제이고,\
  [`ops-patterns/11-distributed-lock`](../../../../../ops-patterns/11-distributed-lock/) 가 「**분산 락은 정확성 보장이 아니다**」까지 다룬다.

## 핵심 문장

- **`FOR UPDATE` 는 기본이 무한 대기다 — PostgreSQL 의 `lock_timeout` 기본값은 0 이다.**
- **`NOWAIT`·타임아웃·교착은 서로 다른 에러다 — 한쪽만 잡는 코드는 나머지에서 잘못 동작한다.**
- **`SKIP LOCKED` 는 에러 대신 결과를 줄인다 — 큐 말고 다른 곳에 쓰면 답이 조용히 틀린다.**
- **잠금은 행이 아니라 인덱스에 걸린다 — MySQL 에서 인덱스 없는 열로 잠그면 훑은 자리가 전부 잠긴다.**
- **교착은 한쪽만 죽고 한쪽은 통과한다 — 누가 죽을지는 엔진이 고르므로 죽는 쪽은 재시도해야 한다.**

## 관련 자료

- [`ops-patterns/11-distributed-lock`](../../../../../ops-patterns/11-distributed-lock/) — ★ **여러 인스턴스를 조율하는 분산 락은 거기가 정본**이다.\
  **여기는 한 DB 안의 행 잠금 문법과 잠금이 걸리는 자리까지**다. 「DB 행 잠금으로 안 되는 일」이 그쪽 출발점이다.
- [`engineering-axes/concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) — **도구 선택 순서와 트레이드오프는 거기가 정본**이다.\
  거기의 「비관적 락 — 처리량 저하, 데드락」이 **이 편에서 실행으로 보인 것**이다.
- [56 격리 수준과 읽기 이상 현상·MVCC](../56-isolation-levels-read-phenomena-mvcc/) — **선행.** 잠금 읽기가 스냅샷과 다르게 도는 이유.
- [55 트랜잭션 경계](../55-transaction-boundaries-commit-rollback-savepoint/) — 잠금을 **언제까지 쥐고 있나**를 정하는 괄호.
- [46 인덱스 정의](../46-index-definition-composite-partial-expression/) · [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/) — ★ **잠금이 그 인덱스 위에 걸린다.**\
  47번이 「안 타면 느려진다」라면 여기는 「**안 타면 잠금이 넓어진다**」다.
- [52 UPSERT](../52-upsert/) — **없는 행은 잠글 수 없다.** 신규 삽입 경쟁은 그쪽 몫이다.
- [51 DELETE 와 TRUNCATE](../51-delete-and-truncate/) — 대량 삭제를 나눠 도는 이유 중 하나가 잠금 범위다.

## 용어 풀이

- **명시적 잠금(explicit locking)** — 문법으로 직접 요청하는 잠금.
- **잠금 읽기(locking read)** — `FOR UPDATE`·`FOR SHARE` 를 붙인 `SELECT`. 최신 상태를 보고 행을 잠근다.
- **비관적 락(pessimistic lock)** — 충돌이 잦다고 보고 읽는 순간부터 잠그는 전략. `FOR UPDATE` 가 그 수단이다.
- **`NOWAIT`** — 잠금을 즉시 못 잡으면 기다리지 않고 에러를 내는 옵션.
- **`SKIP LOCKED`** — 잠긴 행을 결과에서 빼고 나머지만 돌려주는 옵션.
- **잠금 타임아웃(lock timeout)** — 잠금을 기다리는 시간의 상한. PG `lock_timeout`, MySQL `innodb_lock_wait_timeout`.
- **교착(deadlock)** — 서로가 쥔 잠금을 기다려 둘 다 못 나아가는 상태.
- **희생자(victim)** — 교착을 풀려고 엔진이 골라 롤백시키는 트랜잭션.
- **갭 락(gap lock)** — 인덱스 레코드 사이의 빈 구간에 거는 잠금. 그 구간에 새 행을 못 넣게 한다.
- **넥스트 키 락(next-key lock)** — 인덱스 레코드 하나와 그 앞의 빈 구간을 함께 잠그는 형태.
- **`supremum pseudo-record`** — InnoDB 가 인덱스의 맨 끝 뒤를 가리키려고 두는 가상 레코드.
- **의도 잠금(intention lock · `IX`)** — 「이 표 안의 어떤 행을 배타적으로 잠글 것」이라고 표 수준에 미리 알리는 표시.
- **`RowShareLock`** — PG 가 잠금 읽기를 할 때 표 수준에 거는 약한 잠금. 다른 잠금 읽기와는 충돌하지 않는다.

## 더 들어가면

- **잠금을 들여다보는 도구가 엔진마다 다르다.** MySQL 은 `performance_schema.data_locks` 와\
  `SHOW ENGINE INNODB STATUS`, PG 는 `pg_locks` 와 `pg_stat_activity` 의 `wait_event` 다.\
  **PG 쪽은 행 잠금이 `pg_locks` 에 안 나오므로**, 누가 누구를 기다리는지는 `pg_blocking_pids()` 로 본다\
  *(이 편에서는 돌려 보지 않았다)*.
- **표 수준 잠금은 따로 있다.** PG 의 `LOCK TABLE`, MySQL 의 `LOCK TABLES` 는 행 잠금과 다른 물건이다.\
  `ALTER TABLE` 이 부르는 잠금은 [42 테이블 정의와 변경](../42-create-alter-drop-table/)이 맡는다.
- **권고 잠금(advisory lock).** PG 에는 표와 무관한 이름표를 잠그는 `pg_advisory_lock` 이 있다.\
  「이 배치는 한 번에 하나만」 같은 조율에 쓰이고, 분산 환경의 한계는 [`ops-patterns/11-distributed-lock`](../../../../../ops-patterns/11-distributed-lock/) 이 다룬다.
- **교착은 `UPDATE` 만으로도 난다.** 이 편은 `FOR UPDATE` 로 만들었지만, `UPDATE` 두 문이 순서만 엇갈려도 같은 사이클이 생긴다.\
  실제로 [56번](../56-isolation-levels-read-phenomena-mvcc/)의 MySQL `SERIALIZABLE` 실험에서는 **일반 `SELECT` 가 교착의 한 변**이 됐다.
