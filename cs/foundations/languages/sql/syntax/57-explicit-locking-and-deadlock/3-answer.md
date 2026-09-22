# sql/57-명시적 잠금과 교착 — `FOR UPDATE`·`SKIP LOCKED`·`NOWAIT` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 **두 접속을 동시에 띄워** 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> **출력 형식** — PG 는 `psql -a`(입력 에코) 그대로다. MySQL 은 `mysql -v -t` 의 문장 에코를 쓰되\
> 에코를 감싸는 `--------------` 구분선만 지웠다. **결과·에러 문자열은 한 글자도 손대지 않았다.**\
> ★★ **대기·교착 실험에는 먼저 타임아웃을 걸었다** — `lock_timeout = '3s'` / `innodb_lock_wait_timeout = 3`.\
> **강제로 끊은 세션은 없다** — 모든 대기가 3초 타임아웃으로 스스로 끝났다(맨 끝 「실행 검증」).\
> ★ **기존 `emp`·`dept` 는 읽지도 잠그지도 않았다.** 다른 사람이 쓰는 표를 잠그면 그 사람이 멈춘다.\
> **정본 경계** — 분산 락은 [`ops-patterns/11-distributed-lock`](../../../../../ops-patterns/11-distributed-lock/). 여기는 **한 DB 안의 행 잠금**이다.\
> 문서 근거는 [PG 18 The Locking Clause](https://www.postgresql.org/docs/18/sql-select.html#SQL-FOR-UPDATE-SHARE) · [MySQL 8.4 Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. PG 는 0(무제한), MySQL 은 50초

**출력**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
 lock_timeout                               @@innodb_lock_wait_timeout: 50
--------------                                     @@lock_wait_timeout: 31536000
 0                                            @@innodb_deadlock_detect: 1
(1 row)                                       @@transaction_isolation: REPEATABLE-READ

 statement_timeout     deadlock_timeout
-------------------   ------------------
 0                     1s
```

**왜 그런가** — **PG 의 `0` 은 「기다리지 않는다」가 아니라 「무제한으로 기다린다**」이다.\
잠금 실험을 맨몸으로 하면 그 세션이 **영원히 선다** — 클라이언트를 닫아도 서버에 남을 수 있고,\
그 표를 쓰는 다른 사람까지 막는다.

★ 그래서 이 편의 모든 실험은 **두 접속 모두에 타임아웃을 먼저 깔고** 돌렸다.\
MySQL 의 50초도 실험에는 너무 길어 3초로 낮췄다.

---

### 2. ★ 3초 기다리다 에러 — 메시지가 서로 다르다

**출력**

```text
--- PG 18.6 · 세션 B ---
SELECT id, payload FROM t57_q WHERE id = 1 FOR UPDATE;
ERROR:  canceling statement due to lock timeout
CONTEXT:  while locking tuple (0,1) in relation "t57_q"
ERROR:  current transaction is aborted, commands ignored until end of transaction block
```

```text
--- MySQL 8.4.10 · 세션 B ---
SELECT id, payload FROM t57_q WHERE id = 1 FOR UPDATE
ERROR 1205 (HY000) at line 3: Lock wait timeout exceeded; try restarting transaction
```

**왜 그런가** — 기본 동작은 **대기**다. 타임아웃이 그 대기를 끊었다.

★ **PG 쪽 세 번째 줄을 보라.** 타임아웃 에러가 [55번](../55-transaction-boundaries-commit-rollback-savepoint/)의 **트랜잭션 중단**을 일으켰다.\
그래서 그 뒤에 던진 `NOWAIT`·`SKIP LOCKED` 질의가 **전부 무시됐다** — 실험을 분리해 다시 돌려야 했다.\
**MySQL 은 그렇지 않다.** 1205 뒤에도 같은 트랜잭션에서 다음 질의가 정상으로 돈다.

---

### 3. ★ 즉시 실패 — `NOWAIT` 전용 에러가 따로 있다

**출력**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
SELECT id, payload FROM t57_q             SELECT id, payload FROM t57_q
  WHERE id = 1 FOR UPDATE NOWAIT;           WHERE id = 1 FOR UPDATE NOWAIT
ERROR:  could not obtain lock on row      ERROR 3572 (HY000) at line 4: Statement
        in relation "t57_q"                 aborted because lock(s) could not be
                                            acquired immediately and NOWAIT is set.
```

**왜 그런가** — 2번과 **다른 에러**다. 기다린 시간이 0 인 것이 아니라 **실패의 종류가 다르다.**

| 상황 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 기다리다 포기 | `canceling statement due to lock timeout` | `ERROR 1205 … Lock wait timeout exceeded` |
| `NOWAIT` 즉시 실패 | `could not obtain lock on row in relation "…"` | `ERROR 3572 … NOWAIT is set.` |

★ **분기 코드가 한쪽만 보면 나머지에서 잘못 동작한다.**\
「잠금 경합이면 사용자에게 안내」를 짜려면 **세 가지**(타임아웃·`NOWAIT`·교착)를 다 잡아야 한다.

---

### 4. ★ 1번이 결과에서 빠진 3행 — 에러가 아니다

**출력**

```text
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
```

**왜 그런가** — `SKIP LOCKED` 는 **에러를 내지 않는다.** 잠긴 행을 **결과에서 빼고** 나머지를 준다.\
`state = 'ready'` 인 행은 4개인데 **3행이 나왔다.** 그런데 「4개 중 3개」라는 표시는 어디에도 없다.\
**두 엔진의 답이 한 자리도 안 갈렸다.**

---

### 5. A 는 `job-a`, B 는 `job-b`

**출력**

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

**왜 그런가** — B 의 `LIMIT 1` 은 「첫 행」이 아니라 「**잠기지 않은 첫 행**」을 집는다.\
1번이 A 에게 잠겨 있으므로 후보에서 빠졌고, 2번이 첫 행이 됐다.\
**이것이 큐 테이블의 표준 소비 패턴이다** — 워커를 N 대로 늘려도 서로를 안 막는다.

★ 주의할 것 두 가지.

- **순서 보장이 약해진다.** 「먼저 들어온 일감이 먼저 끝난다」가 깨진다.
- **트랜잭션이 길면 잠금도 길다.** 일감 처리 전체를 한 괄호에 넣으면 다른 워커가 그만큼 오래 건너뛴다.

---

### 6. 두 번째 워커는 1번을 기다리다 죽는다

**출력**

```text
--- PG 18.6 · 워커 B ---
SELECT id, payload FROM t57_q WHERE state='ready' ORDER BY id LIMIT 1 FOR UPDATE;
ERROR:  canceling statement due to lock timeout
CONTEXT:  while locking tuple (0,9) in relation "t57_q"
```

**왜 그런가** — `ORDER BY id LIMIT 1` 은 **모든 워커에게 같은 행을 가리킨다.**\
그래서 워커를 늘릴수록 **한 행에 줄을 서게** 된다. 3대면 둘이 기다리고, 10대면 아홉이 기다린다.\
**「워커를 늘렸는데 처리량이 안 는다」의 전형적인 원인이 이 한 줄이다.**

---

### 7. 답이 조용히 줄어들기 때문이다

**왜 그런가** — 4번 출력이 근거다. **4개 중 3개가 나왔는데 에러도 경고도 없었다.**

| 쓰는 자리 | 괜찮은가 |
|---|---|
| 큐에서 일감 하나 꺼내기 | **괜찮다** — 「아무거나 하나」면 되는 일이다 |
| 목록 조회·건수·합계 | **사고다** — 남이 잠근 행이 통째로 빠진 채 성공한다 |
| 정산·대사 | **사고다** — 매번 다른 답이 나오고 재현도 안 된다 |

★ **동시성 실패의 전형이다** — 에러가 없고, 단일 워커 테스트에서는 항상 맞는다.\
([`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 「실패가 조용하다 · 재현이 안 된다 · 부하가 올라야 나타난다」가 한 줄에 다 있다.)

---

### 8. 둘 다 구문 오류다

**출력**

```text
--- PG 18.6 ---
ERROR:  syntax error at or near "NOWAIT"
LINE 1: ...ECT id FROM t57_lk WHERE id=1 FOR UPDATE SKIP LOCKED NOWAIT;
                                                                ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 4: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NOWAIT' at line 1
```

**왜 그런가** — 둘은 **못 잡았을 때 무엇을 할지**를 정하는 옵션이고, 서로 배타적이다.\
「건너뛰되 없으면 즉시 실패」를 원한다면 `SKIP LOCKED` 로 받아서 **결과가 0행인지 애플리케이션이 확인**한다.

---

### 9. ★ 인덱스가 없으면 B 가 막히고, 있으면 안 막힌다

**출력**

```text
--- MySQL 8.4.10 · t57_lk (grp 에 인덱스 없음) ---
[세션 B] SELECT id, grp FROM t57_lk WHERE id = 3 FOR UPDATE
ERROR 1205 (HY000) at line 3: Lock wait timeout exceeded; try restarting transaction
```

```text
--- MySQL 8.4.10 · t57_ix (grp 에 인덱스 있음) ---
[세션 B] SELECT id, grp FROM t57_ix WHERE id = 3 FOR UPDATE
+----+------+
| id | grp  |
+----+------+
|  3 |   30 |
+----+------+
```

**왜 그런가** — 세션 A 의 질의는 **양쪽에서 1행만 돌려줬다.** 그런데 잠긴 범위가 다르다.

인덱스가 없으면 엔진은 `grp = 10` 을 판정하려고 **모든 행을 훑어야** 하고, **훑은 자리를 전부 잠근다.**\
조건에 안 맞는 2·3번 행도, 심지어 **마지막 행 뒤의 빈 자리**(`supremum`)까지.

★ **「1행만 골랐으니 1행만 잠겼겠지」가 틀리는 자리다.**

---

### 10. `INDEX_NAME` 이 「어느 인덱스 위에 걸렸나」를 그대로 적는다

**출력**

```text
--- MySQL 8.4.10 · t57_lk (인덱스 없음) ---
SELECT INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_DATA FROM performance_schema.data_locks WHERE OBJECT_NAME='t57_lk';
+------------+-----------+-----------+------------------------+
| INDEX_NAME | LOCK_TYPE | LOCK_MODE | LOCK_DATA              |
+------------+-----------+-----------+------------------------+
| NULL       | TABLE     | IX        | NULL                   |
| PRIMARY    | RECORD    | X         | supremum pseudo-record |
| PRIMARY    | RECORD    | X         | 1                      |
| PRIMARY    | RECORD    | X         | 2                      |
| PRIMARY    | RECORD    | X         | 3                      |
+------------+-----------+-----------+------------------------+
```

```text
--- MySQL 8.4.10 · t57_ix (인덱스 있음) ---
+------------+-----------+---------------+-----------+
| INDEX_NAME | LOCK_TYPE | LOCK_MODE     | LOCK_DATA |
+------------+-----------+---------------+-----------+
| NULL       | TABLE     | IX            | NULL      |
| t57_ix_grp | RECORD    | X,GAP         | 20, 2     |
| t57_ix_grp | RECORD    | X             | 10, 1     |
| PRIMARY    | RECORD    | X,REC_NOT_GAP | 1         |
+------------+-----------+---------------+-----------+
```

**왜 그런가** — **잠금은 표가 아니라 인덱스 위의 자리에 걸린다.**

| 칸 | 읽는 법 |
|---|---|
| `INDEX_NAME` | **어느 인덱스**의 자리인가. `NULL` 인 줄은 표 수준 잠금(`IX` = 의도 잠금)이다 |
| `LOCK_TYPE` | `TABLE`(표 수준) / `RECORD`(인덱스 레코드) |
| `LOCK_MODE` | `X`(배타) · `X,GAP`(빈 구간만) · `X,REC_NOT_GAP`(레코드만) |
| `LOCK_DATA` | 그 자리의 **키 값**. `10, 1` 은 보조 인덱스의 `(grp, id)` 쌍이다 |

★ **인덱스 없는 쪽은 `PRIMARY` 의 1·2·3 과 `supremum` 이 전부 잠겼다** — 사실상 표 전체다.\
인덱스 있는 쪽은 `t57_ix_grp` 의 한 자리와 그 앞 구간, 그리고 `PRIMARY` 의 한 자리뿐이다.

**[46 인덱스 정의](../46-index-definition-composite-partial-expression/)·[47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)가 여기로 이어진다.**\
47번이 「인덱스를 못 타면 **느려진다**」라면, 이 편은 「인덱스를 못 타면 잠금이 **넓어진다**」를 더한다.\
느린 것은 나만의 문제이고, **잠금이 넓은 것은 남까지 멈추는 문제다.**

---

### 11. PG 에서는 B 가 안 막히고, `pg_locks` 에는 표 수준 잠금만 보인다

**출력**

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
(1 row)

[세션 B] SELECT locktype, relation::regclass AS rel, mode FROM pg_locks WHERE relation = 't57_lk'::regclass;
 locktype |  rel   |     mode
----------+--------+--------------
 relation | t57_lk | RowShareLock
 relation | t57_lk | RowShareLock
(2 rows)
```

**왜 그런가** — PG 는 **질의가 고른 행에만** 잠금을 남긴다. 인덱스가 없어도 B 가 안 막혔다.

★ **그리고 `pg_locks` 에는 행 잠금이 안 보인다.** 보이는 것은 두 세션이 각각 잡은 **표 수준 `RowShareLock`** 둘뿐이다.\
PG 의 행 잠금은 **행 자체에 표시**로 남기 때문이다.\
**「`pg_locks` 가 비었으니 잠금이 없다」는 틀린 추론이다.**

두 엔진을 나란히 놓으면 이렇다.

```text
 MySQL                                     PostgreSQL
 인덱스 설계 = 동시성 설계                   인덱스와 잠금 범위의 결합이 약하다
   -> 인덱스 하나 빠뜨리면 표가 멈춘다          -> 고른 행만 잠긴다
 잠금이 data_locks 에 낱낱이 보인다          행 잠금이 pg_locks 에 안 보인다
   -> 무엇이 잠겼는지 조회로 확인된다           -> 누가 누구를 막는지 따로 봐야 한다
```

---

### 12. ★ MySQL 은 `INSERT` 를 막고, PG 는 통과시킨 뒤 팬텀을 보여 준다

**출력**

```text
--- MySQL 8.4.10 · REPEATABLE READ ---
[세션 A] SELECT id, grp FROM t57_ix WHERE grp BETWEEN 10 AND 20 FOR UPDATE
+----+------+
| id | grp  |
+----+------+
|  1 |   10 |
|  2 |   20 |
+----+------+
[세션 B] INSERT INTO t57_ix VALUES (5, 15, 'new')
ERROR 1205 (HY000) at line 3: Lock wait timeout exceeded; try restarting transaction
[세션 A] (같은 SELECT 를 다시)
+----+------+
| id | grp  |
+----+------+
|  1 |   10 |
|  2 |   20 |
+----+------+
```

```text
--- PG 18.6 · READ COMMITTED ---
[세션 A] SELECT id, grp FROM t57_ix WHERE grp BETWEEN 10 AND 20 FOR UPDATE;
 id | grp
----+-----
  1 |  10
  2 |  20
(2 rows)

[세션 B] INSERT INTO t57_ix VALUES (5, 15, 'new');
INSERT 0 1
[세션 B] COMMIT;
COMMIT
[세션 A] (같은 SELECT 를 다시)
 id | grp
----+-----
  1 |  10
  2 |  20
  5 |  15
(3 rows)
```

**왜 그런가** — MySQL 은 **잠근 범위 안의 빈 구간까지** 잠근다(10번 출력의 `X,GAP`).\
그래서 `grp = 15` 가 그 구간에 못 들어간다.\
PG 는 **존재하는 행만** 잠근다. 없는 행은 잠글 수 없으므로 `INSERT` 가 통과하고, A 의 재조회에 **없던 행이 나타난다.**

★ **「범위를 확인하고 그 범위에 넣는」 코드가 엔진을 옮기면 조용히 깨지는 자리다.**

---

### 13. 2행이다 — 잠금 읽기인데도 스냅샷을 따른다

**출력**

```text
--- PG 18.6 · REPEATABLE READ · 세션 A ---
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT id, grp FROM t57_ix WHERE grp BETWEEN 10 AND 20 FOR UPDATE;
 id | grp
----+-----
  1 |  10
  2 |  20
(2 rows)

(세션 B 가 INSERT 하고 COMMIT 한 뒤)
SELECT id, grp FROM t57_ix WHERE grp BETWEEN 10 AND 20 FOR UPDATE;
 id | grp
----+-----
  1 |  10
  2 |  20
(2 rows)

COMMIT;
SELECT id, grp FROM t57_ix ORDER BY id;     -- 트랜잭션 밖
 id | grp
----+-----
  1 |  10
  2 |  20
  3 |  30
  5 |  15
(4 rows)
```

**왜 그런가** — **PG 의 `REPEATABLE READ` 는 잠금 읽기도 스냅샷을 따른다.**\
행은 실제로 들어갔지만(마지막 출력이 4행) A 는 끝까지 못 봤다.

★ **[56번](../56-isolation-levels-read-phenomena-mvcc/)의 MySQL 과 정반대다.** 거기서는 `REPEATABLE READ` 의 잠금 읽기가 **최신을 봤다.**\
세 경우를 한 표로 놓으면 이렇다.

| | 남의 `INSERT` 가 되나 | A 의 재조회 |
|---|---|---|
| MySQL `REPEATABLE READ` + `FOR UPDATE` | **안 된다** (`ERROR 1205`) | 2행 — 팬텀 없음 |
| PG `READ COMMITTED` + `FOR UPDATE` | 된다 | **3행 — 팬텀** |
| PG `REPEATABLE READ` + `FOR UPDATE` | 된다 | 2행 — 스냅샷 |

**세 줄이 서로 다른 이유로 같거나 다른 답을 낸다.** 「어느 엔진이 안전한가」로 요약되지 않는다.

---

### 14. ★ 한쪽만 죽는다 — 그리고 희생자를 엔진이 고른다

**출력**

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

--- 세션 A 는 그대로 진행했다 ---
SELECT id, memo FROM t57_lk WHERE id = 2 FOR UPDATE
+----+------+
| id | memo |
+----+------+
|  2 | y    |
+----+------+
```

**왜 그런가** — 교착은 **둘 다 멈추는 것이 아니다.** 엔진이 사이클을 감지하고 **한쪽을 롤백시켜 사이클을 끊는다.**

★ **이 판에서 PG 는 A 를, MySQL 은 B 를 골랐다.** 같은 순서의 같은 실험인데 다른 쪽이 죽었다.\
**누가 죽을지 예측하고 코드를 짜면 안 된다.** 죽는 쪽은 언제나 **재시도**해야 한다.

PG 의 `DETAIL:` 은 **사이클 자체**를 적는다 — 20289 가 20288 을, 20288 이 20289 를 기다린다.\
그리고 PG 는 `deadlock_timeout = 1s` 를 기다린 **뒤에야** 검사한다(1번 출력). 교착보다 **그 1초가 더 비싸다.**

---

### 15. 질의 · 잠긴 대상 · 희생자

**출력** (레코드 덤프의 바이트 나열만 줄였고 나머지는 그대로다)

```text
--- MySQL 8.4.10 · SHOW ENGINE INNODB STATUS\G ---
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

**왜 그런가** — 세 가지를 **추측 없이** 읽을 수 있다.

1. **서로를 문 질의 두 개가 그대로 찍힌다** — `WHERE id = 2` 와 `WHERE id = 1`. 순서가 엇갈린 것이 바로 보인다.
2. **`index PRIMARY of table study.t57_lk`** — 9·10번의 결론이 여기 또 있다. **잠금은 인덱스 위에 있다.**\
   `lock_mode X locks rec but not gap` 은 **레코드만 잠그고 빈 구간은 안 잠갔다**는 뜻이다.
3. **`*** WE ROLL BACK TRANSACTION (2)`** — 엔진이 **누구를 죽였는지 직접 적는다.**

★ **한계도 같이 안다** — 이 절은 **마지막 교착 하나만** 보관한다. 그 전 것은 덮여 사라진다.\
반복되는 교착을 추적하려면 서버 로그 쪽 설정이 필요하다 *(이 편에서는 확인하지 않았다)*.

---

### 16. 잠그는 순서를 코드의 규약으로 고정한다

**왜 그런가** — 14번의 사이클은 **순서가 엇갈려서** 생겼다.\
둘 다 `id` 오름차순으로 잠그면 나중에 온 쪽이 1번에서 먼저 막히고, **사이클이 안 생긴다.**

```text
 사이클이 생긴 순서                         사이클이 안 생기는 순서
 A: 1 -> 2                                 A: 1 -> 2
 B: 2 -> 1                                 B: 1 -> 2
    ^^^^^^ 반대                                ^^^^^^ 같다
 A 가 2 를 기다리고                          B 는 1 에서 그냥 기다린다
 B 가 1 을 기다린다 = 사이클                  A 가 끝나면 B 가 1, 2 를 차례로 잡는다
```

그 밖에 줄일 수 있는 것.

- **트랜잭션을 짧게** — 쥐고 있는 시간이 짧으면 부딪힐 확률도 준다.
- **잠그는 행 수를 줄인다** — 9번이 그 이야기다. 인덱스가 없으면 필요 없는 행까지 잠긴다.
- **그래도 남는 교착은 재시도로 받는다** — 두 엔진의 메시지가 똑같이 `try restarting transaction` 이라고 말한다.

★ **「교착을 0 으로 만든다」는 목표가 아니다.** 빈도를 낮추고 **재시도로 흡수**하는 것이 설계다.

---

### 17. PG 는 4단계, MySQL 은 2단계다

**출력**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
SELECT id FROM t57_lk WHERE id=1            SELECT id FROM t57_lk WHERE id=1
  FOR NO KEY UPDATE;                          FOR NO KEY UPDATE
 id                                         ERROR 1064 (42000) at line 4: You have an
----                                          error in your SQL syntax; ... near
  1                                           'NO KEY UPDATE' at line 1
(1 row)

SELECT id FROM t57_lk WHERE id=1 FOR KEY SHARE;
 id
----
  1
(1 row)
```

**왜 그런가** — 잠금의 **세기**를 고를 수 있는 폭이 다르다.

| 세기 | PostgreSQL 18 | MySQL 8.4 |
|---|---|---|
| 가장 강함 | `FOR UPDATE` | `FOR UPDATE` |
| 그다음 | `FOR NO KEY UPDATE` | **없다** |
| 그다음 | `FOR SHARE` | `FOR SHARE` (`LOCK IN SHARE MODE` 도 통과한다) |
| 가장 약함 | `FOR KEY SHARE` | **없다** |

대상 지정(`FOR UPDATE OF <별칭>`)은 **두 엔진 다 된다.**

---

### 18. PG 는 거부하고, MySQL 은 3을 준다

**출력**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
SELECT count(*) FROM t57_lk FOR UPDATE;     SELECT count(*) FROM t57_lk FOR UPDATE
ERROR:  FOR UPDATE is not allowed with      +----------+
        aggregate functions                 | count(*) |
                                            +----------+
                                            |        3 |
                                            +----------+
```

**왜 그런가** — 집계는 **행을 접어 버린다.** 접힌 결과에는 잠글 행이 없다.\
PG 는 그 모순을 **거부**하고, MySQL 은 **통과시킨다**(읽으면서 훑은 행을 잠근 채 개수만 돌려준다).

★ **MySQL 쪽이 더 위험하다** — 「잠갔다고 믿는데 무엇을 잠갔는지 모르는」 상태가 조용히 만들어진다.

---

### 19. PG 는 거부하고, MySQL 은 통과한다 — PG 는 `OF` 로 고친다

**출력**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
SELECT id FROM t57_lk                       SELECT id FROM t57_lk
  LEFT JOIN t57_ix USING (id) FOR UPDATE;     LEFT JOIN t57_ix USING (id) FOR UPDATE
ERROR:  FOR UPDATE cannot be applied to     +----+
        the nullable side of an outer join  | id |
                                            +----+
--- PG 18.6 · 대상을 지목하면 통과한다 ---   |  1 |
SELECT l.id FROM t57_lk l                   |  2 |
  LEFT JOIN t57_ix i USING (id)             |  3 |
  FOR UPDATE OF l;                          +----+
 id
----
  1
  2
  3
(3 rows)
```

**왜 그런가** — 외부 조인의 NULL 쪽 행은 **존재하지 않을 수 있다.** 없는 행은 잠글 수 없다.\
PG 는 그것을 **에러로 알려 주고**, `FOR UPDATE OF l` 로 **잠글 표를 지목하면** 통과시킨다.\
MySQL 은 지목 없이도 통과한다.

**[14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/)·[15 ON 과 WHERE 의 차이](../15-on-vs-where-in-outer-join/)의 「외부 조인의 NULL 쪽」이 여기서 다시 나온다** — 그쪽은 *결과*의 문제였고, 여기는 *잠금 대상*의 문제다.

---

### 20. 그 문이 끝나는 순간 풀린다

**왜 그런가** — 잠금은 **트랜잭션이 끝날 때** 풀린다. 자동 커밋이면 **문 하나가 곧 트랜잭션**이므로\
`SELECT … FOR UPDATE` 가 돌아온 시점에 **이미 잠금이 없다**([55번](../55-transaction-boundaries-commit-rollback-savepoint/)).

그래서 이런 코드는 아무것도 안 지킨다.

```text
(잘못) SELECT ... FOR UPDATE;          <- 여기서 잠금이 풀린다
       (애플리케이션이 값을 보고 판단)     <- 이 사이에 남이 끼어든다
       UPDATE ...;

(맞음) BEGIN;
       SELECT ... FOR UPDATE;
       (판단)
       UPDATE ...;
       COMMIT;                         <- 여기서 잠금이 풀린다
```

★ **「잠갔다」와 「쥐고 있다」는 다르다.** 쥐고 있으려면 괄호가 필요하다.

---

### 21. 아직 없는 행 — 유니크 제약과 upsert 로 막는다

**왜 그런가** — `FOR UPDATE` 는 **존재하는 행만** 잠근다.\
12번의 PG 쪽 그림이 그 증거다 — `grp = 15` 인 행이 없으므로 아무것도 못 잠갔고, B 의 `INSERT` 가 통과했다.

| 경쟁 | 막는 수단 |
|---|---|
| 있는 행을 둘이 고친다 | `FOR UPDATE` · 조건부 갱신 · 낙관적 락 |
| **없는 행을 둘이 넣는다** | **유니크 제약 + upsert**([52번](../52-upsert/)) |
| 범위 안에 남이 넣는다 | MySQL 은 갭 락이 일부 막는다 — **엔진·격리 수준에 의존하므로 이식성이 없다** |

★ [52번](../52-upsert/)이 적은 것과 같은 결론이다 — **「없는 행은 잠글 수 없다.」**

---

### 22. 여러 인스턴스·여러 저장소를 조율하는 자리

**왜 그런가** — 이 편의 잠금은 **한 DB 안에서만** 유효하다.\
그 DB 밖의 것(외부 API 호출 횟수, 파일, 여러 저장소에 걸친 작업)을 조율하려면 다른 수단이 필요하다.

**그 자리의 정본은 [`ops-patterns/11-distributed-lock`](../../../../../ops-patterns/11-distributed-lock/) 이다.**\
그리고 [`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 가 그 수단의 한계를 못 박는다 — **「분산 락은 정확성 보장이 아니다.」**\
TTL 만료·GC 정지·네트워크 지연으로 **두 프로세스가 동시에 락을 가졌다고 믿을 수 있다.**

★ **거꾸로 읽어도 된다** — 한 DB 안에서 끝나는 일이라면 **이 편의 행 잠금이 분산 락보다 강하다.**\
DB 가 잠금의 소유권을 직접 알고 있고, 트랜잭션이 끝나면 확실히 풀리기 때문이다.

---

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 환경 확인(잠금 타임아웃·교착 감지·격리 수준) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **제출 직전 재확인** |
| ★ 대기 → 타임아웃 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **두 세션** · 3초 |
| ★ `NOWAIT` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | PG 는 트랜잭션을 나눠 다시 돌렸다 |
| ★ `SKIP LOCKED` (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 4행 중 3행 |
| ★ 큐 소비 두 워커 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **서로 다른 행을 집는 것 확인** · 끝나고 `state` 되돌림 |
| `SKIP LOCKED` 없는 큐 (6번) | PG 18.6 | 1회 | `ERROR: canceling statement due to lock timeout` |
| `SKIP LOCKED` + `NOWAIT` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 둘 다 구문 오류 |
| ★ 인덱스 유무와 잠금 범위 (9·10번) | MySQL 8.4.10 | **각 1회** | `t57_lk` / `t57_ix` · `data_locks` 조회 |
| ★ 같은 실험 PG (11번) | PG 18.6 | 1회 | `pg_locks` 조회 |
| ★ 갭 락과 `INSERT` (12번) | MySQL 8.4.10 · PG 18.6 | 각 1회 | PG 쪽은 넣은 행을 `DELETE` 로 되돌림 |
| ★ PG `REPEATABLE READ` 잠금 읽기 (13번) | PG 18.6 | 1회 | 트랜잭션 안 2행 / 밖 4행 |
| ★ 교착 (14번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **희생자가 서로 달랐다** |
| ★ `SHOW ENGINE INNODB STATUS` (15번) | MySQL 8.4.10 | 2회 | 교착 직후 |
| 잠금 세기 문법 (17번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `FOR NO KEY UPDATE`·`FOR KEY SHARE`·`LOCK IN SHARE MODE`·`FOR UPDATE OF` |
| 집계·외부 조인 (18·19번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | PG 만 거부 |
| 뒷정리 확인 | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\dt` · `SHOW FULL TABLES` · **`emp` 4행 · `dept` 3행 재확인** |

**두 세션을 어떻게 띄웠나** — 이름 붙인 FIFO 두 개를 만들어 각 접속의 표준입력에 물리고, 한 줄씩 순서대로 먹였다.\
**이 주제는 순서가 곧 내용**이라 대기(`W <초>`)를 스크립트에 명시적으로 넣었다.

```bash
mkfifo "$D/a.in" "$D/b.in"
docker exec -i study-mysql84 mysql -uroot -p<pw> study -v -t --force < "$D/a.in" > "$D/a.out" 2>&1 &
docker exec -i study-mysql84 mysql -uroot -p<pw> study -v -t --force < "$D/b.in" > "$D/b.out" 2>&1 &
exec 3>"$D/a.in" 4>"$D/b.in"
# 스크립트 줄: "A <sql>" -> fd 3, "B <sql>" -> fd 4, "W 4" -> sleep 4 (타임아웃 3초보다 길게)
```

★★ **대기·교착 실험에는 타임아웃을 먼저 걸었다.** 두 접속 모두 첫 줄이 이것이다.

```sql
-- PG
SET lock_timeout = '3s'; SET statement_timeout = '10s';
-- MySQL
SET SESSION innodb_lock_wait_timeout = 3; SET SESSION max_execution_time = 10000;
```

★ **강제로 끊은 세션은 하나도 없다.** 모든 대기가 3초 타임아웃으로 스스로 끝났고,\
스크립트가 끝나면서 FIFO 가 닫혀 두 접속이 정상 종료됐다. **`pg_terminate_backend`·`KILL` 을 쓴 적이 없다.**\
제출 전에 **두 엔진의 잔류 세션·잠금이 0인 것**을 `pg_stat_activity`·`pg_locks` 와 `SHOW PROCESSLIST`·`information_schema.innodb_trx` 로 확인했다.

**뒷정리** — 트랜잭션 자체가 실험 대상이라 `ROLLBACK` 에 기댈 수 없었다. **두 엔진 모두 `DROP TABLE` 로 직접 지웠다.**

```sql
DROP TABLE IF EXISTS t57_q;
DROP TABLE IF EXISTS t57_lk;
DROP TABLE IF EXISTS t57_ix;
```

**구현 의존 항목** — 9·10·11·12·13·14·17·18·19번. **인덱스가 없을 때 잠금이 얼마나 넓어지는가**,\
**갭 락의 유무**, **잠금 세기의 단계 수**, **집계·외부 조인에 붙일 수 있는가**, **누가 희생되는가**는 전부 **엔진의 선택**이다.\
에러 번호(`1205`·`1213`·`3572`·`1064`)와 PG 의 `CONTEXT:` 줄 형식, `LOCK_DATA` 표기도 구현 세부다 — **문자열로 분기하지 마라.**

★ **희생자 선정은 같은 판에서도 바뀔 수 있다.** 이 편의 관찰(PG=A, MySQL=B)은 **한 판의 결과**이지 규칙이 아니다.\
재현되는 것은 「**누군가 하나는 죽고 하나는 통과한다**」는 성질이다.

**언어 보장 항목** — 3·4·5·8번. `NOWAIT`·`SKIP LOCKED` 의 **문법과 의미**, 큐 소비의 결과,\
`SKIP LOCKED` + `NOWAIT` 동시 사용 거부는 **두 엔진에서 한 자리도 안 갈렸다.**

**한쪽에서만 결론이 서는 실험** — 10번(`data_locks` 로 잠금의 대상을 확인하는 것)은 **MySQL 에서만** 가능하다.\
PG 의 행 잠금은 `pg_locks` 에 안 나오므로 **같은 방식의 확인이 성립하지 않는다**(11번).\
그래서 「잠금은 인덱스에 걸린다」는 결론의 **직접 근거는 MySQL 출력뿐**이고,\
PG 쪽은 **「인덱스가 없어도 B 가 안 막혔다」는 행동 관찰**이 근거다 — **근거의 종류가 다르다는 것까지 같이 외운다.**

**버전** — PG 18 · MySQL 8.4 에서 확인한 것이다. 잠금 대기 기본값은 **서버 설정으로 바뀌므로**,\
다른 환경에서는 **1번의 환경 확인부터 다시 돌린다.**
