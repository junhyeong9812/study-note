# sql/56-격리 수준과 읽기 이상 현상·MVCC — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 **두 접속을 동시에 띄워** 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> **출력 형식** — PG 는 `psql -a`(입력 에코) 그대로다. MySQL 은 `mysql -v -t` 의 문장 에코를 쓰되\
> 에코를 감싸는 `--------------` 구분선만 지웠다. **결과·에러 문자열은 한 글자도 손대지 않았다.**\
> ★ **대기 실험에는 먼저 타임아웃을 걸었다** — `lock_timeout = '3s'` / `innodb_lock_wait_timeout = 3`.\
> ★ **기존 `emp`·`dept` 는 읽지도 잠그지도 않았다.** 이 편은 `t56_item`·`t56_duty` 만 쓴다.\
> **정본 경계** — 개념·도구 선택은 [`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md). 여기는 문법과 **이 두 서버의 실제 동작**이다.\
> 문서 근거는 [PG 18 Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html) · [MySQL 8.4 Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. PG 는 `read committed`, MySQL 은 `REPEATABLE-READ`

**출력**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
 default_transaction_isolation                 @@transaction_isolation: REPEATABLE-READ
-------------------------------                           @@autocommit: 1
 read committed                             @@innodb_lock_wait_timeout: 50
                                              @@innodb_deadlock_detect: 1
 transaction_isolation
-----------------------
 read committed

 lock_timeout        deadlock_timeout
--------------      ------------------
 0                   1s
```

**왜 그런가** — **이 한 칸 차이가 이 편 전체의 출발점이다.**\
아무 설정도 안 한 애플리케이션이 PG 에서는 「문마다 새로 본다」, MySQL 에서는 「시작 시점으로 고정해서 본다」로 돈다.\
같은 코드가 엔진을 옮기는 순간 **조용히 다르게 동작한다.**

잠금 기본값도 다르다 — PG 의 `lock_timeout = 0` 은 **무제한 대기**다.\
그래서 이 편의 모든 실험은 두 접속에 **먼저 타임아웃을 걸고** 돌렸다.

---

### 2. ★ MySQL 은 999 를 읽고, PG 는 5 를 읽는다

**출력**

```text
--- MySQL 8.4.10 ---                        --- PG 18.6 ---
SELECT @@transaction_isolation AS lvl,      SHOW transaction_isolation;
       qty FROM t56_item WHERE id = 1        transaction_isolation
+------------------+------+                 -----------------------
| lvl              | qty  |                  read uncommitted
+------------------+------+                 (1 row)
| READ-UNCOMMITTED |  999 |
+------------------+------+                 SELECT qty FROM t56_item WHERE id = 1;
                                             qty
(A 가 ROLLBACK 한 뒤)                        -----
+------+                                        5
| qty  |                                    (1 row)
+------+
|    5 |
+------+
```

**왜 그런가** — MySQL 의 `READ UNCOMMITTED` 는 **정말로 더티 리드를 한다.**\
A 가 `ROLLBACK` 했으므로 999 는 **DB 어디에도 존재한 적 없는 값**이다. 그 값으로 계산한 결과는 근거가 없다.\
PG 는 같은 수준을 요청해도 커밋된 값(5)만 준다.

---

### 3. PG 는 그 수준을 `READ COMMITTED` 로 취급한다

**왜 그런가** — PG 는 네 수준을 **전부 받아들이고 그 이름으로 보고**까지 한다. 그런데 **관찰된 동작은 `READ COMMITTED` 와 같다.**

근거는 두 가지 출력이다.

1. 위 2번 — `read uncommitted` 라고 보고하면서 **더티 리드가 안 났다.**
2. 같은 트랜잭션 안에서 A 가 `COMMIT` 한 뒤 다시 읽으면 **값이 바뀐다.**

```text
--- PG 18.6 · READ UNCOMMITTED ---
SELECT qty FROM t56_item WHERE id = 1;    ->  5      (A 가 아직 커밋 전)
SELECT qty FROM t56_item WHERE id = 1;    ->  999    (A 가 COMMIT 한 뒤)
```

**두 번째 출력이 결정적이다** — 더티 리드는 안 나는데 **반복 불가능 읽기는 난다.**\
그것이 곧 `READ COMMITTED` 의 모양이다. 「PG 에서 수준을 낮춰 성능을 얻었다」는 설명은 **근거가 없다.**

---

### 4. PG 는 `50 / 3`, MySQL 은 `5 / 2`

**출력**

```text
(A) PG 18.6 · READ COMMITTED (기본)         (B) MySQL 8.4.10 · REPEATABLE READ (기본)
 transaction_isolation                      +-----------------+
-----------------------                     | lvl             |
 read committed                             +-----------------+
                                            | REPEATABLE-READ |
첫 읽기:   qty = 5    count = 2             +-----------------+
두 번째:   qty = 50   count = 3             첫 읽기:   qty = 5   count = 2
                                            두 번째:   qty = 5   count = 2
 qty          n
-----        ---                            +------+        +---+
  50          3                             | qty  |        | n |
(1 row)      (1 row)                        +------+        +---+
                                            |    5 |        | 2 |
  -> 반복 불가능 읽기 O, 팬텀 O               +------+        +---+
                                              -> 둘 다 안 난다
```

**왜 그런가** — **아무 설정도 안 했는데 답이 다르다.** 기본 수준이 한 칸 다르기 때문이다.\
수준을 서로 바꿔 주면 결과도 뒤집힌다 — PG 를 `REPEATABLE READ` 로 올리면 `5 / 2`, MySQL 을 `READ COMMITTED` 로 내리면 `50 / 3` 이다.\
**전체 격자는 2-summary 의 5번 절에 있다.**

---

### 5. ★ (가)는 2, (나)는 3

**출력**

```text
--- MySQL 8.4.10 · REPEATABLE READ · 한 트랜잭션 안 ---
SELECT count(*) AS n FROM t56_item WHERE grp = 10
+---+
| n |
+---+
| 2 |            <- (가) 일반 읽기
+---+
SELECT count(*) AS n_locking FROM t56_item WHERE grp = 10 FOR SHARE
+-----------+
| n_locking |
+-----------+
|         3 |     <- (나) 잠금 읽기
+-----------+
SELECT id, qty FROM t56_item WHERE grp = 10 FOR SHARE
+----+------+
| id | qty  |
+----+------+
|  1 |   50 |     <- 스냅샷은 5 라고 했는데 50 이다
|  2 |    7 |
|  4 |    1 |     <- 스냅샷에 없던 행이다
+----+------+
```

**왜 그런가** — **같은 트랜잭션이 두 개의 시계를 쓴다.**

| 무엇을 읽었나 | 무엇을 보는가 |
|---|---|
| `SELECT …` | **스냅샷** — 트랜잭션의 첫 읽기 시점 |
| `SELECT … FOR SHARE` / `FOR UPDATE` | **최신 커밋 상태** — 잠글 행을 알아야 하므로 |

PostgreSQL 의 `REPEATABLE READ` 는 **잠금 읽기도 스냅샷을 따른다**([57번](../57-explicit-locking-and-deadlock/)에서 같은 실험을 했다).\
**두 엔진의 MVCC 가 실제로 갈리는 자리가 여기다.**

---

### 6. 「읽는 방식에 달렸다」가 정답이다

**왜 그런가** — 하나로 답할 수 없다. 관찰된 것은 이렇다.

```text
 팬텀이 안 난 경로                          팬텀이 난 경로
 ─────────────                              ─────────────
 일반 SELECT 를 두 번        (스냅샷)        잠금 읽기로 처음 본 범위     (최신)
   -> 2행, 2행                                 -> 3행

 범위를 먼저 FOR UPDATE 로 잠갔다 (갭 락)
   -> 남이 그 범위에 INSERT 하려다 ERROR 1205
   -> 다시 읽어도 2행
```

**갭 락 쪽 실제 출력**(실험 전체는 [57번](../57-explicit-locking-and-deadlock/)에 있다).

```text
--- MySQL 8.4.10 · REPEATABLE READ ---
--- 세션 A ---                              --- 세션 B ---
SELECT id, grp FROM t57_ix                  INSERT INTO t57_ix VALUES (5, 15, 'new')
  WHERE grp BETWEEN 10 AND 20 FOR UPDATE    ERROR 1205 (HY000) at line 3: Lock wait
+----+------+                                 timeout exceeded; try restarting transaction
| id | grp  |
+----+------+
|  1 |   10 |
|  2 |   20 |
+----+------+
(다시 읽어도 같은 2행)
```

**그래서 정답은 세 문장이다.**

1. 일반 읽기는 **스냅샷이라 애초에 안 보인다.**
2. 내가 **먼저 잠근 범위**에는 남이 못 넣는다 — 갭 락이 여기서 일한다.
3. ★ **아직 안 잠근 범위를 잠금 읽기로 처음 읽으면 새 행이 보인다**(5번).

「MySQL 의 RR 은 갭 락으로 팬텀까지 막는다」는 말은 **2번만 말한 것**이고, 3번을 빠뜨린다.

---

### 7. ★ 두 엔진 다 깨진다 — 에러 하나 없이

**출력**

```text
--- PG 18.6 · REPEATABLE READ ---           --- MySQL 8.4.10 · REPEATABLE READ (기본) ---
A: COMMIT;  ->  COMMIT                      A: COMMIT
B: COMMIT;  ->  COMMIT                      B: COMMIT

 id | name | on_duty                        +----+------+---------+
----+------+---------                       | id | name | on_duty |
  1 | ann  | f                              +----+------+---------+
  2 | bob  | f                              |  1 | ann  |       0 |
(2 rows)                                    |  2 | bob  |       0 |
                                            +----+------+---------+
```

**왜 그런가** — 둘은 **서로 다른 행**을 고쳤다. 행 충돌이 없으므로 잠금도 안 부딪힌다.\
각자의 스냅샷에서는 「다른 당직자가 있다」가 참이었고, **그 판단이 커밋 시점에 거짓이 됐다는 것을 아무도 검사하지 않는다.**

★ **`REPEATABLE READ` 는 「내가 읽은 것이 그 사이에 바뀌었나」를 안 본다.**\
[`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 가 「격리 수준만으로 lost update 는 안 막힌다」고 적은 자리가 정확히 이것이다.

---

### 8. ★ PG 는 B 의 `COMMIT` 이, MySQL 은 B 의 `UPDATE` 가 죽는다

**출력**

```text
--- PG 18.6 · SERIALIZABLE ---
세션 A: COMMIT;
COMMIT
세션 B: COMMIT;
ERROR:  could not serialize access due to read/write dependencies among transactions
DETAIL:  Reason code: Canceled on identification as a pivot, during commit attempt.
HINT:  The transaction might succeed if retried.

(끝나고)
 id | name | on_duty
----+------+---------
  1 | ann  | f
  2 | bob  | t
(2 rows)
```

```text
--- MySQL 8.4.10 · SERIALIZABLE ---
세션 B: ERROR 1213 (40001) at line 5: Deadlock found when trying to get lock; try restarting transaction
        (5번째 줄 = B 의 UPDATE)

(끝나고)
+----+------+---------+
| id | name | on_duty |
+----+------+---------+
|  1 | ann  |       0 |
|  2 | bob  |       1 |
+----+------+---------+
```

**왜 그런가** — **결과는 같은데 막는 방식이 다르고, 실패하는 줄도 다르다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 어디서 죽나 | **`COMMIT`** | **`UPDATE`** |
| 무슨 에러 | `could not serialize access due to read/write dependencies` | `ERROR 1213 … Deadlock found` |
| 어떻게 막았나 | 커밋 시점에 **읽기·쓰기 의존 관계를 판정**해 거부 | **`SELECT` 가 잠금을 잡아** 서로 기다리다 교착 |
| 읽기가 쓰기를 막나 | 안 막는다 | **막는다** |

★ **같은 이름의 수준이 두 엔진에서 다른 물건이다.**\
MySQL 쪽은 교착이 나기 전 단계에서 **읽기가 쓰기를 통째로 막는 것**도 관찰된다 — 격자 아래의 `ERROR 1205` 두 줄이 그것이다.

---

### 9. **재시도하라**

**출력** — 두 메시지의 마지막 줄이 같은 말을 한다.

```text
PG:     HINT:  The transaction might succeed if retried.
MySQL:  ERROR 1213 (40001) ... try restarting transaction
```

**왜 그런가** — 높은 격리 수준은 「**충돌을 막아 주겠다」가 아니라 「충돌하면 하나를 죽이겠다**」는 계약이다.\
그러니 그 계약을 받는 쪽(애플리케이션)에 **재시도 루프가 없으면 그냥 실패율만 올라간 시스템**이 된다.

재시도를 쓸 때 조심할 것 — 재시도 **안에서 다시 읽어야** 한다. 옛 스냅샷의 값을 들고 재시도하면 같은 판단을 반복한다.\
그리고 재시도 횟수에 상한을 둬야 한다(무한 루프 방지).

---

### 10. ★ PG 는 에러, `READ COMMITTED` 와 MySQL 은 기다렸다 성공

**출력**

```text
--- PG 18.6 · REPEATABLE READ ---           --- PG 18.6 · READ COMMITTED ---
세션 B:                                     세션 B:
UPDATE t56_item SET qty = qty - 1           UPDATE t56_item SET qty = qty - 1
  WHERE id = 1;                               WHERE id = 1;
ERROR:  could not serialize access          UPDATE 1
        due to concurrent update            COMMIT;
COMMIT;                                     COMMIT
ROLLBACK
                                            최종 qty = 3   (5 에서 둘 다 빠졌다)
최종 qty = 4   (A 의 -1 만 반영)
```

```text
--- MySQL 8.4.10 · REPEATABLE READ (기본) ---
세션 B:
UPDATE t56_item SET qty = qty - 1 WHERE id = 1     (에러 없음 — 기다렸다 성공)
SELECT qty AS b_sees_snapshot FROM t56_item WHERE id = 1
+-----------------+
| b_sees_snapshot |
+-----------------+
|               3 |     <- 스냅샷은 5 라고 했는데 3 이다
+-----------------+
최종 qty = 3
```

**왜 그런가**

- **PG `REPEATABLE READ`** — B 의 스냅샷에서 그 행은 아직 5 다. 그런데 실제 행은 A 가 이미 바꿨다.\
  PG 는 「**네가 본 버전이 더 이상 최신이 아니다**」를 이유로 거부한다. **B 의 변경은 통째로 사라진다.**
- **PG `READ COMMITTED`** — B 는 A 를 기다렸다가 **새 값(4) 위에서** `qty - 1` 을 다시 계산한다. 그래서 3 이다.
- **MySQL `REPEATABLE READ`** — PG 와 달리 에러를 내지 않고 `READ COMMITTED` 처럼 **최신 값 위에서** 계산한다. 역시 3 이다.

★ **그리고 마지막 출력이 중요하다** — B 의 일반 `SELECT` 가 **스냅샷(5)이 아니라 3** 을 준다.\
**자기가 쓴 것은 언제나 보인다.** 스냅샷은 「남의 변경」에만 적용된다.

---

### 11. 「같은 행」이냐 「읽은 것의 의존」이냐

| 에러 | 언제 나오나 | 어느 수준에서 |
|---|---|---|
| `could not serialize access due to **concurrent update**` | 두 트랜잭션이 **같은 행**을 고칠 때, 나중 쪽 | `REPEATABLE READ` 이상 |
| `could not serialize access due to **read/write dependencies** among transactions` | **서로 다른 행**이어도 읽기·쓰기 의존이 순서를 만들 수 없을 때 | `SERIALIZABLE` 에서만 |

**왜 그런가** — 앞쪽은 **행 단위 충돌**이라 감지가 싸다. 뒤쪽은 **무엇을 읽었는지까지 추적**해야 하므로 `SERIALIZABLE` 에서만 한다.\
그래서 7번의 쓰기 왜곡은 `REPEATABLE READ` 에서 **에러 없이 통과한다** — 같은 행을 안 건드렸기 때문이다.

---

### 12. ★ 변수는 `REPEATABLE-READ` 라 하고, 실제로는 `READ UNCOMMITTED` 로 돈다

**출력**

```text
--- MySQL 8.4.10 ---  (세션 A 가 id=3 을 888 로 바꾸고 커밋하지 않은 상태)
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED
START TRANSACTION
SELECT @@transaction_isolation AS reported, qty FROM t56_item WHERE id = 3
+-----------------+------+
| reported        | qty  |
+-----------------+------+
| REPEATABLE-READ |  888 |
+-----------------+------+

COMMIT
START TRANSACTION
SELECT qty AS second_tx FROM t56_item WHERE id = 3
+-----------+
| second_tx |
+-----------+
|         9 |
+-----------+
```

**왜 그런가** — `SESSION`·`GLOBAL` 을 안 붙인 `SET TRANSACTION` 은 **다음 트랜잭션 하나**에만 적용된다.\
그런데 `@@transaction_isolation` 은 **세션 값**을 보고한다. 그래서 변수는 `REPEATABLE-READ` 인데 **888(미커밋 값)이 읽힌다.**\
두 번째 트랜잭션에서는 설정이 소진돼 다시 9 가 나온다.

★ **이 자리는 변수를 믿으면 안 되고 동작으로 확인해야 한다.**\
그리고 **「다음 트랜잭션」에는 자동 커밋 문 하나도 포함된다** — 설정과 `START TRANSACTION` 사이에 `SELECT` 를 하나 끼우면\
**그 `SELECT` 가 설정을 먹어 버린다.** (그래서 위 출력에서는 사이에 아무것도 넣지 않았다.)

---

### 13. 에러다 — 첫 질의 전에 쳐야 한다

**출력**

```text
--- PG 18.6 ---
BEGIN;
BEGIN
SELECT 1;
 ?column?
----------
        1
(1 row)

SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
ERROR:  SET TRANSACTION ISOLATION LEVEL must be called before any query
```

**왜 그런가** — 수준은 **스냅샷을 어떻게 잡을지**를 정한다. 이미 읽었으면 스냅샷이 잡힌 뒤라 바꿀 수 없다.\
그리고 그 설정은 **그 트랜잭션에서만** 산다.

```text
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SHOW transaction_isolation;   ->  serializable
COMMIT;
SHOW transaction_isolation;   ->  read committed
```

---

### 14. PG 만 받는다 — MySQL 은 `SET TRANSACTION` 을 먼저 친다

**출력**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
BEGIN ISOLATION LEVEL REPEATABLE READ;      ERROR 1064 (42000) at line 9: You have an error
BEGIN                                         in your SQL syntax; ... near 'ISOLATION LEVEL
SHOW transaction_isolation;                   REPEATABLE READ' at line 1
 transaction_isolation
-----------------------
 repeatable read
(1 row)
```

**왜 그런가** — PG 는 `BEGIN`/`START TRANSACTION` 에 트랜잭션 모드를 붙일 수 있다.\
MySQL 은 **별도의 문**으로만 지정한다.

| 범위 | PostgreSQL 18 | MySQL 8.4 |
|---|---|---|
| 이 트랜잭션 | `BEGIN ISOLATION LEVEL <수준>;` — 또는 첫 질의 전 `SET TRANSACTION …` | `SET TRANSACTION ISOLATION LEVEL <수준>;` (다음 트랜잭션 하나) |
| 이 세션 | `SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL <수준>;` | `SET SESSION TRANSACTION ISOLATION LEVEL <수준>;` |
| 서버 | `default_transaction_isolation` | `SET GLOBAL TRANSACTION ISOLATION LEVEL <수준>;` |

---

### 15. ★ 77 을 본다 — 스냅샷은 `BEGIN` 이 아니라 **첫 읽기**에서 찍힌다

**출력**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
BEGIN ISOLATION LEVEL REPEATABLE READ;      START TRANSACTION
BEGIN
SELECT qty AS first_read_after_others_commit SELECT qty AS first_read_after_others_commit
  FROM t56_item WHERE id = 2;                  FROM t56_item WHERE id = 2
 first_read_after_others_commit              +--------------------------------+
--------------------------------             | first_read_after_others_commit |
                             77              +--------------------------------+
(1 row)                                      |                             77 |
                                             +--------------------------------+
SELECT qty AS second_read ...;               SELECT qty AS second_read ...
 second_read                                 +-------------+
-------------                                | second_read |
          77                                 +-------------+
(1 row)                                      |          77 |
                                             +-------------+
```

**왜 그런가** — `BEGIN` 전의 값은 7 이었다. 그 뒤 A 가 77 로 바꾸고 커밋했고, **B 의 첫 읽기가 77 을 봤다.**\
그다음 A 가 88 로 또 바꿨지만 **두 번째 읽기는 77 이다** — 찍힌 뒤에는 고정이다.\
**두 엔진의 답이 같다.**

★ 「트랜잭션을 미리 열어 두면 그 시점이 고정된다」는 믿음이 여기서 틀린다.\
고정하고 싶으면 **여는 즉시 한 번 읽어야** 한다.

---

### 16. `SERIALIZABLE` 부터 — 그런데 그 전에 조건부 갱신을 본다

**왜 그런가** — 이 편의 실측이 답이다.

| 수단 | 7번의 불변식을 지켰나 |
|---|---|
| `READ COMMITTED` | 아니다 |
| `REPEATABLE READ` | **아니다** (PG·MySQL 둘 다 깨졌다) |
| `SERIALIZABLE` | 그렇다 — 대신 **한쪽이 실패한다** |

그런데 **격리 수준을 올리는 것이 첫 선택지가 아니다.**\
[`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 「선택 순서」를 그대로 따르면 이렇다.

```text
1. 애초에 경합을 없앨 수 있나        (키 분산·파티셔닝)
        ↓
2. 조건부 업데이트로 되나            UPDATE ... WHERE qty >= 1   <- 가장 저렴하고 강력
        ↓                            영향 행 0 이면 실패로 친다
3. 낙관적 락으로 되나                version 열 비교
        ↓
4. 비관적 락이 필요한가              SELECT ... FOR UPDATE  (57번)
        ↓
5. 그리고 항상: DB 제약을 최후 방어선으로
```

★ **격리 수준은 이 목록 어디에도 1번으로 나오지 않는다.**\
「확인과 변경이 한 문 안에서 일어나면」 그 사이에 남이 끼어들 틈이 없다 — 틈을 없애는 쪽이 먼저다.

---

### 17. 불변식이 깨졌는데 아무도 말해 주지 않았다

**왜 그런가** — 7번 실행에는 **에러가 0건**이다. 두 `COMMIT` 이 다 성공했다.\
그런데 `on_duty` 인 사람이 0명이 됐다 — **당직 없는 밤이 만들어졌다.**

★ **동시성에서는 통과한 실행이 가장 위험한 근거다.**\
「돌려 봤는데 안 터졌다」로 결론 내면 안 되고, **불변식을 직접 다시 읽어서 확인**해야 한다.\
([`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 「실패가 조용하다 — 며칠 뒤 정산이 안 맞아서 발견한다」가 이 모양이다.)

이 편에서 **표를 다시 읽지 않았으면 못 봤을 사고**가 둘이다 — 7번의 쓰기 왜곡과 10번의 「B 의 변경이 통째로 사라진 것」.

---

### 18. 실패율 · 처리량 · 저장소

1. **실패율** — `SERIALIZABLE` 은 정상 흐름에서 에러를 낸다(8번). 재시도 코드가 없으면 그냥 실패다.
2. **처리량** — MySQL 의 `SERIALIZABLE` 에서는 **읽기가 쓰기를 막는다.** 위 격자의 `ERROR 1205` 두 줄이 그 증거다.
3. **저장소와 정리 비용** — 스냅샷을 오래 들고 있으면 엔진이 **옛 버전을 못 버린다.**\
   긴 트랜잭션이 곧 긴 스냅샷이고, 그것이 저장소를 부풀린다.

그리고 **대가 없이 얻는 것도 있다** — 기본값을 정확히 아는 것. 그것은 공짜이고, 이 편에서 가장 값싼 교훈이다.

---

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 환경 확인(기본 격리 수준·자동 커밋·타임아웃) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **제출 직전 재확인** |
| ★ 더티 리드 (2·3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **두 세션** · A 는 `ROLLBACK`·`COMMIT` 둘 다 |
| ★ 격자 8칸 (4번·2-summary 5절) | PG 18.6(4수준) · MySQL 8.4.10(4수준) | **각 1회** | 같은 하네스로 8판 |
| ★ 잠금 읽기와 스냅샷의 분리 (5·6번) | MySQL 8.4.10 | 2회 | `FOR SHARE` 를 같은 트랜잭션에서 |
| ★ 갭 락이 INSERT 를 막는다 (6번) | MySQL 8.4.10 · PG 18.6 | 각 1회 | [57번](../57-explicit-locking-and-deadlock/)과 공유한 실험 |
| ★ 쓰기 왜곡 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `REPEATABLE READ` · **표를 다시 읽어 확인** |
| ★ `SERIALIZABLE` (8·9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | PG = 직렬화 실패, MySQL = 교착 |
| ★ 같은 행 동시 갱신 (10·11번) | PG 18.6(RR·RC) · MySQL 8.4.10(RR) | 각 1회 | 세 경우 전부 |
| ★ `SET TRANSACTION` 범위 (12번) | MySQL 8.4.10 | 2회 | 변수와 동작이 어긋나는 것 확인 |
| `SET TRANSACTION` 자리 제약 (13번) | PG 18.6 | 1회 | `must be called before any query` |
| `BEGIN ISOLATION LEVEL` (14번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | MySQL 은 `ERROR 1064` |
| ★ 스냅샷 시점 (15번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 다 첫 읽기였다** |
| 뒷정리 확인 | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\dt` · `SHOW FULL TABLES` · **`emp` 4행 · `dept` 3행 재확인** |

**두 세션을 어떻게 띄웠나** — 이름 붙인 FIFO 두 개를 만들어 각 접속의 표준입력에 물리고, 한 줄씩 순서대로 먹였다.\
**이 주제는 순서가 곧 내용**이라 대기(`W <초>`)를 스크립트에 명시적으로 넣었다.

```bash
mkfifo "$D/a.in" "$D/b.in"
docker exec -i study-pg18 psql -U postgres -d study -a -P pager=off < "$D/a.in" > "$D/a.out" 2>&1 &
docker exec -i study-pg18 psql -U postgres -d study -a -P pager=off < "$D/b.in" > "$D/b.out" 2>&1 &
exec 3>"$D/a.in" 4>"$D/b.in"
# 스크립트 줄: "A <sql>" -> fd 3, "B <sql>" -> fd 4, "W 0.5" -> sleep 0.5
```

★ **대기·교착 실험에는 먼저 타임아웃을 걸었다.** 두 접속 모두 첫 줄이 이것이다.

```sql
-- PG
SET lock_timeout = '3s'; SET statement_timeout = '10s';
-- MySQL
SET SESSION innodb_lock_wait_timeout = 3; SET SESSION max_execution_time = 10000;
```

**무한 대기로 끊어야 했던 세션은 없었다** — 모든 대기가 3초 타임아웃으로 스스로 끝났고,\
스크립트가 끝나면서 FIFO 가 닫혀 두 접속이 정상 종료됐다. **`pg_terminate_backend`·`KILL` 을 쓴 적이 없다.**

**뒷정리** — 트랜잭션 자체가 실험 대상이라 `ROLLBACK` 에 기댈 수 없었다. **두 엔진 모두 `DROP TABLE` 로 직접 지웠다.**

```sql
DROP TABLE IF EXISTS t56_duty;
DROP TABLE IF EXISTS t56_item;
```

**구현 의존 항목** — 1·2·3·5·8·10·12번. **기본 격리 수준**·**`READ UNCOMMITTED` 의 실제 동작**·\
**잠금 읽기가 스냅샷을 따르는가**·**`SERIALIZABLE` 이 무엇으로 막는가**는 전부 **엔진의 선택**이다.\
에러 번호(`1205`·`1213`·`1064`)와 PG 의 `Reason code:` 문구도 구현 세부다 — **문자열로 분기하지 마라.**

**언어 보장 항목** — 15번(스냅샷은 첫 읽기에 찍힌다)과 네 수준의 **이름**은 두 엔진에서 같았다.\
4번의 「수준을 맞춰 주면 결과도 같아진다」도 양쪽에서 확인했다 — **다른 것은 기본값이지 문법이 아니다.**

**한쪽에서만 결론이 서는 실험** — 5·6번(잠금 읽기와 스냅샷의 분리)은 **MySQL 에서만** 관찰된다.\
PG 에서 같은 것을 던지면 잠금 읽기도 스냅샷을 따르므로 **현상 자체가 없다**([57번](../57-explicit-locking-and-deadlock/)).\
반대로 3번은 **PG 출력만이 근거**다 — MySQL 에는 「이름만 있고 동작이 다른 수준」이 없다.

**버전** — PG 18 · MySQL 8.4 에서 확인한 것이다. 기본 격리 수준은 **서버 설정으로 바뀔 수 있으므로**,\
다른 환경에서는 **1번의 환경 확인부터 다시 돌린다.** 이 편의 본문 전체가 그 값 위에 서 있다.
