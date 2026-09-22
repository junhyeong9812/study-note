# sql/56-격리 수준과 읽기 이상 현상·MVCC — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html) · [SET TRANSACTION](https://www.postgresql.org/docs/18/sql-set-transaction.html) · [MySQL 8.4 · Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html) · [SET TRANSACTION](https://dev.mysql.com/doc/refman/8.4/en/set-transaction.html) · [Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **이 주제는 설정에 달려 있다** — **두 엔진의 기본 격리 수준이 다르다.** 그래서 「환경 확인」이 본문 앞에 있다.\
> ★ **읽기 이상 현상은 두 세션이 있어야 보인다.** 이름 붙인 FIFO 로 두 접속을 열어 두고 한 줄씩 먹였다(3-answer 의 「실행 검증」).\
> ★ **정본 경계** — 격리 수준의 **개념·트레이드오프·도구 선택은 [`engineering-axes/concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 가 정본**이다.\
> **여기는 `SET TRANSACTION` 문법과 두 엔진의 기본값·실제 동작까지**다.\
> **이 편이 만든 객체와 그 뒷정리** — 표 `t56_item`(3행) · `t56_duty`(2행). **끝나고 두 엔진에서 `DROP` 했다**(3-answer).\
> ★ **기존 `emp`·`dept` 는 읽지도 잠그지도 않았다.**\
> **선행** — [55 트랜잭션 경계](../55-transaction-boundaries-commit-rollback-savepoint/). 괄호가 있어야 「괄호 안에서 남의 것이 보이나」를 물을 수 있다.

## 한눈에 — 쉽게 말하면

**격리 수준은 「내 트랜잭션이 남의 작업 중인 책상을 얼마나 들여다보나」의 눈금이다.**

- 도서관에서 책을 읽는다. 옆 사람이 같은 책의 내용을 고치고 있다.
- **가장 헐렁한 눈금** — 옆 사람이 지우개로 지우다 만 자리까지 그대로 읽는다. 그 사람이 마음을 바꾸면 내가 읽은 건 없던 글이 된다.
- **중간 눈금** — 옆 사람이 「다 고쳤다」고 도장 찍은 것만 읽는다. 대신 내가 페이지를 다시 펼 때마다 내용이 바뀌어 있다.
- **빡빡한 눈금** — 내가 책을 펴는 순간 **사진을 찍어** 두고, 끝까지 그 사진만 본다. 옆 사람이 뭘 하든 내 사진은 안 변한다.
- **가장 빡빡한 눈금** — 사진을 보다가 「이 순서로는 둘 다 맞을 수가 없다」가 드러나면 **내 작업을 무효로 만든다.**

| 비유 | 실체 |
|---|---|
| 지우다 만 자리까지 읽는다 | **더티 리드** — `READ UNCOMMITTED` |
| 도장 찍은 것만 읽는다 | `READ COMMITTED` — **PostgreSQL 의 기본값** |
| 같은 페이지를 다시 폈더니 내용이 다르다 | **반복 불가능 읽기** |
| 다시 폈더니 **없던 줄이 생겼다** | **팬텀 리드** |
| 펴는 순간 찍은 사진 | **스냅샷** — `REPEATABLE READ`, **MySQL 의 기본값** |
| 둘 다 맞을 수 없으니 하나를 무효로 | **직렬화 실패** — `SERIALIZABLE` |
| 사진을 여러 장 보관해 두는 방식 | **MVCC** |

```text
느슨함 ────────────────────────────────────────────────> 빡빡함

READ UNCOMMITTED   READ COMMITTED    REPEATABLE READ    SERIALIZABLE
커밋 안 된 것도 본다  커밋된 것만 본다    시작 시점만 본다    + 순서가 안 맞으면 무효
                     ^^^ PG 기본        ^^^ MySQL 기본

동시성 높다 ────────────────────────────────────────> 동시성 낮다
```

**똑같은 구조다** — 「테스트에서는 맞았는데 운영에서 잔액이 안 맞는다」의 답이 대개 이 눈금이다.\
**같은 코드가 PG 와 MySQL 에서 다르게 도는 이유**도 여기 있다 — **기본 눈금이 한 칸 다르다.**

> **격리 수준(isolation level)** — 내 트랜잭션이 다른 트랜잭션의 중간 상태를 얼마나 보는지의 등급.\
> 예: `READ COMMITTED` 면 남이 커밋한 것은 바로 보이고, `REPEATABLE READ` 면 내가 시작한 시점 그대로 보인다.

> **MVCC(Multi-Version Concurrency Control · 다중 버전 동시성 제어)** — 행을 덮어쓰지 않고 **버전을 여러 개 남겨** 각 트랜잭션에 맞는 버전을 보여 주는 방식.\
> 예: 내가 읽는 동안 남이 고쳐도 나는 **내가 시작할 때의 버전**을 계속 읽는다 — 그래서 읽기가 쓰기를 막지 않는다.

> **스냅샷(snapshot)** — 어느 시점의 데이터 상태를 찍어 둔 것. MVCC 가 「어느 버전을 보여 줄까」를 정하는 기준.\
> 예: `REPEATABLE READ` 트랜잭션은 첫 읽기 시점의 스냅샷을 끝까지 쓴다.

## 이 주제가 답하려는 질문

1. **네 수준은 무엇을 막나** — 그리고 **말로 막는다고 한 것과 실제로 막히는 것이 같은가.**
2. **두 엔진의 기본값이 다르면 무엇이 달라지나** — 같은 코드가 어디서 갈리나.
3. **가장 빡빡한 수준에서도 남는 일은 무엇인가** — 그리고 애플리케이션은 무엇을 해야 하나.

## 환경 확인 — 물어보고 시작한다

★ **이 절을 건너뛰면 아래 본문이 통째로 검증 불가가 된다.** 두 엔진의 기본값이 다르기 때문이다.

```text
### SQL: (PG) SHOW default_transaction_isolation;  SHOW transaction_isolation;  SHOW lock_timeout;  SHOW deadlock_timeout;
--- PG 18.6 ---
 default_transaction_isolation
-------------------------------
 read committed

 transaction_isolation
-----------------------
 read committed

 lock_timeout
--------------
 0

 deadlock_timeout
------------------
 1s
```

```text
### SQL: (MySQL) SELECT @@transaction_isolation, @@autocommit, @@innodb_lock_wait_timeout, @@innodb_deadlock_detect;
--- MySQL 8.4.10 ---
   @@transaction_isolation: REPEATABLE-READ
              @@autocommit: 1
@@innodb_lock_wait_timeout: 50
  @@innodb_deadlock_detect: 1
```

| 물어본 것 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| **기본 격리 수준** | **`read committed`** | **`REPEATABLE-READ`** |
| 자동 커밋 | 서버 설정 없음 (클라이언트가 `on`) | `@@autocommit = 1` |
| 잠금 대기 제한 | `lock_timeout = 0` — **무제한** | `innodb_lock_wait_timeout = 50` 초 |
| 교착 감지 | `deadlock_timeout = 1s` 뒤 검사 | `innodb_deadlock_detect = 1` |

★ **아래 실험은 전부 두 세션 모두에 타임아웃을 먼저 걸고 돌렸다** — `lock_timeout = '3s'` / `innodb_lock_wait_timeout = 3`.\
**맨몸으로 무한 대기를 걸면 세션이 남는다.**

## 예시 데이터 — 이 묶음이 공유하는 것

```sql
CREATE TABLE t56_item (id int PRIMARY KEY, grp int, qty int);
INSERT INTO t56_item VALUES (1,10,5),(2,10,7),(3,20,9);

CREATE TABLE t56_duty (id int PRIMARY KEY, name text, on_duty boolean);  -- MySQL: varchar(10), tinyint(1)
INSERT INTO t56_duty VALUES (1,'ann',true),(2,'bob',true);
```

```text
t56_item (재고)                 t56_duty (당직)
+----+-----+-----+              +----+------+---------+
| id | grp | qty |              | id | name | on_duty |
+----+-----+-----+              +----+------+---------+
|  1 |  10 |   5 |              |  1 | ann  | true    |
|  2 |  10 |   7 |              |  2 | bob  | true    |
|  3 |  20 |   9 |              +----+------+---------+
+----+-----+-----+
```

- `t56_item` — **반복 불가능 읽기**(`id=1` 의 `qty`)와 **팬텀**(`grp=10` 의 행 수)을 한 표에서 본다.
- `t56_duty` — **쓰기 왜곡**을 본다. 불변식은 「**`on_duty` 인 사람이 최소 한 명**」이다.

## 동작 방식

### 1. 더티 리드 — 두 엔진 중 한쪽만 보여 준다

**언제 쓰나** — 「`READ UNCOMMITTED` 로 내리면 빨라진다」는 말을 들었을 때. **PG 에서는 아무 효과가 없다.**

```text
시간   세션 A                                세션 B (READ UNCOMMITTED)
 │
 1     BEGIN;
 2     UPDATE t56_item SET qty=999 WHERE id=1;
 │     (커밋 안 함)
 3                                           BEGIN;
 4                                           SELECT qty ... id=1;   -> ?
 5     ROLLBACK;   (또는 COMMIT)
 6                                           SELECT qty ... id=1;   -> ?
```

```text
(A) MySQL 8.4.10 — 본다                     (B) PostgreSQL 18.6 — 못 본다
SELECT @@transaction_isolation AS lvl,      SHOW transaction_isolation;
       qty FROM t56_item WHERE id = 1        transaction_isolation
+------------------+------+                 -----------------------
| lvl              | qty  |                  read uncommitted
+------------------+------+                 (1 row)
| READ-UNCOMMITTED |  999 |
+------------------+------+                 SELECT qty FROM t56_item WHERE id = 1;
   ^^^ 커밋된 적 없는 값이다                  qty
                                            -----
(A 가 ROLLBACK 한 뒤)                          5      <- 남의 미커밋 값이 아니다
SELECT qty FROM t56_item WHERE id = 1                (1 row)
+------+
| qty  |                                    (A 가 COMMIT 한 뒤)
+------+                                    SELECT qty FROM t56_item WHERE id = 1;
|    5 |   <- 999 는 없던 값이 됐다            qty
+------+                                    -----
                                             999
                                            (1 row)
```

두 그림의 결론 — **MySQL 의 `READ UNCOMMITTED` 는 정말로 더티 리드를 한다.**\
**PG 는 `READ UNCOMMITTED` 를 받아들이고 그 이름으로 보고까지 하면서, 동작은 `READ COMMITTED` 다.**\
★ **PG 쪽 그림을 잘 봐라** — 같은 트랜잭션 안에서 두 번째 읽기가 999 로 바뀌었다.\
더티 리드는 안 났지만 **반복 불가능 읽기는 났다.** 이름은 가장 헐렁한데 동작은 한 칸 위다.

> **더티 리드(dirty read)** — 남이 아직 커밋하지 않은 값을 읽는 것. 그 트랜잭션이 롤백하면 **읽은 값이 존재한 적 없는 값**이 된다.\
> 예: 위 MySQL 출력의 `999` — A 가 `ROLLBACK` 했으므로 DB 어디에도 없던 값이다.

비용 — PG 에서 `READ UNCOMMITTED` 를 쓰는 것은 **아무 이득이 없다.** MVCC 는 어차피 버전을 골라 읽는다.

### 2. 반복 불가능 읽기와 팬텀 — 같은 트랜잭션, 다른 답

**언제 쓰나** — 트랜잭션 안에서 같은 것을 두 번 읽을 때. **보고서·정산·검증 로직이 전부 이 모양이다.**

```text
시간   세션 B (읽는 쪽)                       세션 A (쓰는 쪽)
 │
 1     BEGIN;
 2     SELECT qty ... id=1;        -> 5
 3     SELECT count(*) ... grp=10; -> 2
 4                                            UPDATE t56_item SET qty=50 WHERE id=1;
 5                                            INSERT INTO t56_item VALUES (4,10,1);
 │                                            (자동 커밋 — 즉시 확정)
 6     SELECT qty ... id=1;        -> ?       <- 반복 불가능 읽기
 7     SELECT count(*) ... grp=10; -> ?       <- 팬텀
```

```text
(A) PG 18.6 · READ COMMITTED (기본)         (B) PG 18.6 · REPEATABLE READ
 transaction_isolation                       transaction_isolation
-----------------------                     -----------------------
 read committed                              repeatable read

2번:  qty = 5      count = 2                2번:  qty = 5      count = 2
6번:  qty = 50     count = 3                6번:  qty = 5      count = 2
      ^^^^^^^^     ^^^^^^^^^                      ^^^^^^^      ^^^^^^^^^
      바뀌었다      늘었다                          그대로       그대로

  -> 반복 불가능 읽기 O, 팬텀 O               COMMIT 뒤 다시 읽으면: qty = 50, count = 3
                                              -> 트랜잭션 밖에서는 새 값이 보인다
```

그림 해설 — `READ COMMITTED` 는 **문마다 새 스냅샷**을 쓴다. 그래서 같은 트랜잭션 안에서도 답이 바뀐다.\
`REPEATABLE READ` 는 **트랜잭션의 첫 읽기 시점 스냅샷**을 끝까지 쓴다. 두 현상이 한꺼번에 사라진다.\
비용 — 스냅샷을 오래 들고 있으면 엔진이 **옛 버전을 못 버린다.** 긴 트랜잭션이 저장소를 부풀리는 이유다.

> **반복 불가능 읽기(non-repeatable read)** — 같은 행을 두 번 읽었는데 값이 다른 것.\
> 예: 위 6번에서 `qty` 가 5 에서 50 으로 바뀌었다.

> **팬텀 리드(phantom read)** — 같은 조건으로 두 번 읽었는데 **행 수**가 다른 것.\
> 예: 위 7번에서 `grp = 10` 인 행이 2개에서 3개가 됐다.

MySQL 쪽도 같은 실험을 돌렸다 — **기본값이 `REPEATABLE READ` 라서 기본 상태가 오른쪽 그림이다.**

```text
(C) MySQL 8.4.10 · REPEATABLE READ (기본)   (D) MySQL 8.4.10 · READ COMMITTED
+-----------------+                         +----------------+
| lvl             |                         | lvl            |
+-----------------+                         +----------------+
| REPEATABLE-READ |                         | READ-COMMITTED |
+-----------------+                         +----------------+
2번:  qty = 5      count = 2                2번:  qty = 5      count = 2
6번:  qty = 5      count = 2                6번:  qty = 50     count = 3

  -> 둘 다 안 난다                            -> 둘 다 난다
```

★ **그래서 같은 애플리케이션 코드가 두 엔진에서 다르게 돈다.**\
PG 의 기본은 (A), MySQL 의 기본은 (C) 다 — **아무 설정도 안 건드렸을 때의 이야기다.**

### 3. ★ MySQL 의 `REPEATABLE READ` 가 팬텀을 막는가 — 관찰한 그대로

**언제 쓰나** — 「MySQL 은 갭 락 때문에 RR 에서 팬텀도 막는다」는 말을 들었을 때.\
**결론을 미리 정하지 말고 두 가지를 다 던져 봐야 한다.**

같은 트랜잭션 안에서 **일반 `SELECT`** 와 **잠금 읽기(`FOR SHARE`)** 를 나란히 던졌다.

```text
시간   세션 B (REPEATABLE READ)              세션 A
 │
 1     START TRANSACTION;
 2     SELECT count(*) ... grp=10;  -> 2
 3                                            UPDATE ... qty=50 WHERE id=1;
 4                                            INSERT INTO t56_item VALUES (4,10,1);
 5     SELECT count(*) ... grp=10;  -> ?      <- 일반 읽기
 6     SELECT count(*) ... grp=10 FOR SHARE;  <- 잠금 읽기
```

**실제 출력 (MySQL 8.4.10) — 한 트랜잭션 안에서 두 답이 나왔다**

```text
SELECT count(*) AS n FROM t56_item WHERE grp = 10
+---+
| n |
+---+
| 2 |            <- 일반 읽기: 스냅샷. 팬텀 없음
+---+
SELECT count(*) AS n_locking FROM t56_item WHERE grp = 10 FOR SHARE
+-----------+
| n_locking |
+-----------+
|         3 |     <- 잠금 읽기: 최신. 팬텀이 보인다
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

★ **관찰한 그대로 적는다 — MySQL 의 `REPEATABLE READ` 에서 팬텀은 「막힌다/안 막힌다」로 갈리지 않았다.**\
**읽는 방식에 따라 갈렸다.**

| 무엇을 읽었나 | 결과 | 무엇을 보는가 |
|---|---|---|
| `SELECT …` (일반) | 2행 · `qty = 5` | **스냅샷** — 트랜잭션 시작 시점 |
| `SELECT … FOR SHARE` (잠금) | **3행** · `qty = 50` | **최신 커밋 상태** |

PostgreSQL 의 `REPEATABLE READ` 에서 같은 실험을 하면 **잠금 읽기도 스냅샷을 따른다**([57번](../57-explicit-locking-and-deadlock/)에서 실측했다).\
**여기가 두 엔진의 MVCC 가 실제로 갈리는 자리다.**

그러면 「갭 락」은 어디서 일하나 — **내가 먼저 잠근 범위에 남이 넣으려 할 때**다.\
그 실험은 잠금 문법이 필요하므로 [57번](../57-explicit-locking-and-deadlock/)에 있다. 거기서 관찰한 것만 옮기면 이렇다.

```text
MySQL RR — B 가 범위를 먼저 잠근 경우        PG RC — 같은 순서
A: SELECT ... WHERE grp BETWEEN 10 AND 20    A: SELECT ... WHERE grp BETWEEN 10 AND 20
     FOR UPDATE;            -> 2행                FOR UPDATE;            -> 2행
B: INSERT ... (5, 15, 'new');                B: INSERT ... (5, 15, 'new');  -> 성공
   ERROR 1205 (HY000): Lock wait timeout     B: COMMIT;
     exceeded; try restarting transaction
A: 다시 읽으면 -> 2행 (팬텀 없음)             A: 다시 읽으면 -> 3행 (팬텀 O)
```

**정리 — MySQL 의 RR 이 팬텀을 막는 방식은 두 겹이다.**\
① 일반 읽기는 **스냅샷**이라 애초에 새 행이 안 보인다.\
② 잠금 읽기는 최신을 보지만, **내가 이미 잠근 범위에는 남이 못 넣는다**(갭 락).\
★ **①과 ② 사이에 틈이 있다** — 위 출력처럼 **아직 안 잠근 범위를 잠금 읽기로 처음 읽으면 새 행이 보인다.**

### 4. ★ 쓰기 왜곡 — `REPEATABLE READ` 로는 안 막힌다

**언제 쓰나** — 「조건을 확인하고 내 것만 바꾼다」는 코드. 둘이 동시에 하면 불변식이 깨진다.

불변식은 「**당직자가 최소 한 명**」이다. 둘이 동시에 퇴근을 시도한다.

```text
시간   세션 A                                세션 B
 │
 1     BEGIN;                                BEGIN;
 2     SELECT count(*) WHERE on_duty; -> 2
 3                                           SELECT count(*) WHERE on_duty; -> 2
 │     "나 말고 한 명 더 있네"                 "나 말고 한 명 더 있네"
 4     UPDATE ... on_duty=false WHERE id=1;
 5                                           UPDATE ... on_duty=false WHERE id=2;
 6     COMMIT;
 7                                           COMMIT;   -> ?
```

```text
(A) PG 18.6 · REPEATABLE READ                (B) PG 18.6 · SERIALIZABLE
A: COMMIT;  -> COMMIT                        A: COMMIT;  -> COMMIT
B: COMMIT;  -> COMMIT                        B: COMMIT;
                                             ERROR:  could not serialize access due to
 id | name | on_duty                                 read/write dependencies among transactions
----+------+---------                        DETAIL:  Reason code: Canceled on identification
  1 | ann  | f                                        as a pivot, during commit attempt.
  2 | bob  | f                                HINT:  The transaction might succeed if retried.
(2 rows)
                                              id | name | on_duty
  -> 둘 다 퇴근했다. 당직자 0명.              ----+------+---------
     불변식이 깨졌는데 에러가 없다               1 | ann  | f
                                                2 | bob  | t
                                             (2 rows)

                                              -> 한 명이 남았다. B 는 다시 시도해야 한다
```

두 그림의 결론 — **`REPEATABLE READ` 는 쓰기 왜곡을 못 막는다.** 둘이 **서로 다른 행**을 고쳤으므로 충돌이 없다.\
`SERIALIZABLE` 만이 **「B 가 읽은 것을 A 가 바꿨다」는 의존을 추적**해 커밋 시점에 거부한다.

★ **`HINT: The transaction might succeed if retried.` 가 이 수준의 계약이다.**\
`SERIALIZABLE` 을 쓰면 **애플리케이션이 재시도 루프를 가져야 한다.** 재시도가 없으면 그냥 실패하는 시스템이 된다.

> **쓰기 왜곡(write skew)** — 각자 조건을 확인하고 각자 다른 행을 바꿨는데, 합치면 불변식이 깨지는 것.\
> 예: 위 그림 — 둘 다 「다른 당직자가 있다」를 확인하고 둘 다 퇴근했다.

MySQL 에서 같은 시나리오를 던지면 **또 다른 답이 나온다.**

```text
(C) MySQL 8.4.10 · REPEATABLE READ (기본)   (D) MySQL 8.4.10 · SERIALIZABLE
A: COMMIT   B: COMMIT                        B: ERROR 1213 (40001) at line 5: Deadlock found
                                                when trying to get lock; try restarting
+----+------+---------+                          transaction
| id | name | on_duty |
+----+------+---------+                      +----+------+---------+
|  1 | ann  |       0 |                      | id | name | on_duty |
|  2 | bob  |       0 |                      +----+------+---------+
+----+------+---------+                      |  1 | ann  |       0 |
                                             |  2 | bob  |       1 |
  -> PG 의 RR 과 똑같이 깨진다                 +----+------+---------+

                                              -> 막히긴 했는데 **교착으로** 막혔다
```

★ **결론이 같아 보이지만 막는 방식이 다르다.**\
PG 의 `SERIALIZABLE` 은 **커밋 시점에 의존 관계를 판정**해 거부한다(잠금을 더 걸지 않는다).\
MySQL 의 `SERIALIZABLE` 은 **일반 `SELECT` 를 잠금 읽기로 바꿔** 버리고, 그 결과 **교착**이 났다.\
그래서 MySQL 쪽은 실패가 **`SELECT` 단계가 아니라 `UPDATE` 단계**에서 나고, 에러도 교착 에러다.

**둘 다 「재시도하라」고 말한다** — PG 는 `HINT` 로, MySQL 은 `try restarting transaction` 으로.

### 5. 격자 — 네 수준 × 세 현상, 관찰한 대로

**언제 쓰나** — 「이 수준이면 무엇이 막히나」를 한눈에 확인할 때.\
★ **교과서 격자가 아니라 이 두 서버에서 실제로 나온 결과다.** 표준이 무엇이라 하든, 이 판에서는 이렇게 나왔다.

**실험은 하나다.** 세션 A 가 ① 미커밋 `qty = 999` 를 만들었다 되돌리고 ② `qty = 50` 으로 바꾸고 ③ `grp = 10` 인 행을 하나 더 넣는다.\
세션 B 는 그 사이에 같은 것을 두 번 읽는다. **출발값은 `qty = 5` · `grp = 10` 인 행 2개다.**

| 수준 | 더티 리드 — 미커밋 999 가 보이나 | 반복 불가능 읽기 — `qty` 5 → ? | 팬텀 — 행 수 2 → ? |
|---|---|---|---|
| PG `READ UNCOMMITTED` | 안 난다 (**5**) | **난다** (**50**) | **난다** (**3**) |
| PG `READ COMMITTED` ← 기본 | 안 난다 (**5**) | **난다** (**50**) | **난다** (**3**) |
| PG `REPEATABLE READ` | 안 난다 (**5**) | 안 난다 (**5**) | 안 난다 (**2**) |
| PG `SERIALIZABLE` | 안 난다 (**5**) | 안 난다 (**5**) | 안 난다 (**2**) |
| MySQL `READ UNCOMMITTED` | **난다** (**999**) | **난다** (**50**) | **난다** (**3**) |
| MySQL `READ COMMITTED` | 안 난다 (**5**) | **난다** (**50**) | **난다** (**3**) |
| MySQL `REPEATABLE READ` ← 기본 | 안 난다 (**5**) | 안 난다 (**5**) | 안 난다 (**2**) |
| MySQL `SERIALIZABLE` | ★ **읽기가 막힌다** — `ERROR 1205` | 안 난다 (**5**) | 안 난다 (**2**) |

★ **MySQL `SERIALIZABLE` 줄만 성격이 다르다.** 「안 보인다」가 아니라 **아무도 못 들어온다**이다.\
같은 시나리오를 다시 던졌더니 이번에는 **쓰는 쪽**이 막혔다.

```text
### MySQL 8.4.10 · SERIALIZABLE — B 가 먼저 읽고 A 가 쓰려 하면
--- 세션 A ---
UPDATE t56_item SET qty = 50 WHERE id = 1
ERROR 1205 (HY000) at line 2: Lock wait timeout exceeded; try restarting transaction
INSERT INTO t56_item VALUES (4, 10, 1)
ERROR 1205 (HY000) at line 3: Lock wait timeout exceeded; try restarting transaction
--- 세션 B ---
first_read = 5   n = 2        (그리고 reread = 5   n2 = 2)
```

★ **PG 의 `SERIALIZABLE` 은 A 를 막지 않았다** — A 는 통과하고, 대신 **B 의 커밋이 거부될 수 있다**(4번).\
두 엔진이 같은 이름으로 **다른 물건**을 판다.

★ **이 격자에는 「잠금 읽기」 칸이 없다.** 그것을 넣으면 MySQL `REPEATABLE READ` 의 팬텀 칸이 **뒤집힌다**(3번).\
그리고 이 격자에는 **쓰기 왜곡** 칸이 없다 — 그것은 `REPEATABLE READ` 까지 **두 엔진 다 난다**(4번).

```text
 격자가 말해 주는 것                       격자가 말해 주지 않는 것
 ─────────────────                        ────────────────────────
 일반 SELECT 를 두 번 했을 때               잠금 읽기(FOR UPDATE/FOR SHARE)를 섞었을 때
 같은 답이 나오는가                          -> MySQL RR 에서 답이 달라진다 (3번)

 PG 와 MySQL 의 기본값이                     불변식이 여러 행에 걸쳐 있을 때
 한 칸 다르다는 것                            -> RR 로는 못 막는다 (4번)
```

비용 — 아래로 갈수록 동시성이 준다. 그리고 **맨 아래 두 줄은 「실패가 늘어난다」는 대가**를 추가로 낸다.

## 문법 — 형태와 규칙

SQL 에서 이 절의 본체는 「**이 설정이 언제부터 언제까지 유효한가**」다.

| 범위 | PostgreSQL 18 | MySQL 8.4 |
|---|---|---|
| **이 트랜잭션 하나** | `BEGIN ISOLATION LEVEL <수준>;` — 또는 첫 질의 전에 `SET TRANSACTION ISOLATION LEVEL <수준>;` | `SET TRANSACTION ISOLATION LEVEL <수준>;` — **다음 트랜잭션 하나에만** |
| **이 세션** | `SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL <수준>;` | `SET SESSION TRANSACTION ISOLATION LEVEL <수준>;` |
| **서버 전체** | `default_transaction_isolation` 설정 | `SET GLOBAL TRANSACTION ISOLATION LEVEL <수준>;` |
| 현재 값 확인 | `SHOW transaction_isolation;` | `SELECT @@transaction_isolation;` |
| 수준 이름 | `READ UNCOMMITTED` · `READ COMMITTED` · `REPEATABLE READ` · `SERIALIZABLE` | 같다 |

★ **`BEGIN ISOLATION LEVEL …` 은 PG 문법이다.** MySQL 에 던지면 구문 오류다.

```text
### SQL: BEGIN ISOLATION LEVEL REPEATABLE READ;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 9: ... near 'ISOLATION LEVEL REPEATABLE READ' at line 1
```

★ **PG 의 `SET TRANSACTION` 은 「첫 질의 전」이라는 자리 제약이 있다.**

```text
### SQL: BEGIN; SELECT 1; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
--- PG 18.6 ---
SELECT 1;
 ?column?
----------
        1
(1 row)

SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
ERROR:  SET TRANSACTION ISOLATION LEVEL must be called before any query
```

그리고 그 설정은 **그 트랜잭션에서만** 산다 — `COMMIT` 뒤에 다시 물으면 기본값으로 돌아와 있다.

```text
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SHOW transaction_isolation;   ->  serializable
COMMIT;
SHOW transaction_isolation;   ->  read committed
```

## 어디서 틀리나

### ㄱ. ★ MySQL 의 `@@transaction_isolation` 이 사실을 말하지 않는 자리가 있다

`SESSION`·`GLOBAL` 없이 그냥 `SET TRANSACTION ISOLATION LEVEL …` 을 치면 **다음 트랜잭션 하나에만** 적용된다.\
그런데 **변수는 세션 값을 계속 보고한다.**

```text
### 세션 B: SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;  (SESSION 없이)
###        START TRANSACTION;  SELECT @@transaction_isolation, qty ...
--- MySQL 8.4.10 ---  (세션 A 가 id=3 을 888 로 바꾸고 커밋하지 않은 상태)
+-----------------+------+
| reported        | qty  |
+-----------------+------+
| REPEATABLE-READ |  888 |
+-----------------+------+
     ^^^^^^^^^^^^^   ^^^
     변수는 RR 이라 한다  그런데 미커밋 값을 읽었다 = 실제로는 READ UNCOMMITTED 다

(COMMIT 뒤 두 번째 트랜잭션)
SELECT qty AS second_tx FROM t56_item WHERE id = 3
+-----------+
| second_tx |
+-----------+
|         9 |   <- 설정이 소진됐다. 다시 스냅샷을 읽는다
+-----------+
```

★ **변수를 믿지 말고 동작으로 확인해야 하는 자리다.**\
그리고 **「다음 트랜잭션」은 자동 커밋 문 하나도 포함한다** — 설정과 `START TRANSACTION` 사이에 `SELECT` 를 하나 끼우면 그 `SELECT` 가 설정을 먹는다.

### ㄴ. PG 의 `READ UNCOMMITTED` 를 「더 빠른 모드」로 아는 것

PG 는 그 수준을 **받아들이고 그 이름으로 보고까지 한다.** 그런데 동작은 `READ COMMITTED` 다(1번).\
「더티 리드를 허용해서 성능을 얻었다」는 설명은 PG 에서 **아무 근거가 없다.**

### ㄷ. 「격리 수준을 올리면 lost update 도 막힌다」

★ **[`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 가 콕 집어 아니라고 한 자리**이고, 실행 결과도 그렇다.\
`REPEATABLE READ` 에서 **쓰기 왜곡은 그대로 난다**(4번 그림 A·C).\
막으려면 `SERIALIZABLE` 이거나, 아니면 **조건부 갱신·명시적 잠금**이다([57번](../57-explicit-locking-and-deadlock/)).

### ㄹ. ★ PG 의 `REPEATABLE READ` 에서 같은 행을 고치면 — 에러다

두 `REPEATABLE READ` 트랜잭션이 **같은 행**을 고치면, 나중 것이 이렇게 죽는다.

```text
### 세션 B: UPDATE t56_item SET qty = qty - 1 WHERE id = 1;   (A 가 먼저 같은 행을 고치고 커밋)
--- PG 18.6 ---
UPDATE t56_item SET qty = qty - 1 WHERE id = 1;
ERROR:  could not serialize access due to concurrent update
COMMIT;
ROLLBACK
```

★ **4번의 `SERIALIZABLE` 에러와 문구가 다르다.** 같은 「직렬화 실패」 계열이지만 원인이 다르다.

| 에러 | 언제 | 어느 수준 |
|---|---|---|
| `could not serialize access due to **concurrent update**` | **같은 행**을 두 트랜잭션이 고칠 때 | `REPEATABLE READ` 이상 |
| `could not serialize access due to **read/write dependencies** among transactions` | 읽은 것과 쓴 것의 **의존 관계**가 순서를 만들 수 없을 때 | `SERIALIZABLE` |

같은 실험을 `READ COMMITTED` 에서 하면 **에러가 없다** — B 는 기다렸다가 새 값 위에서 다시 계산한다.

```text
--- PG 18.6 · READ COMMITTED ---            --- MySQL 8.4.10 · REPEATABLE READ ---
UPDATE t56_item SET qty = qty - 1 ...       UPDATE t56_item SET qty = qty - 1 ...
UPDATE 1                                    (에러 없음)
최종 qty = 3   (5 에서 둘 다 빠졌다)          최종 qty = 3   (5 에서 둘 다 빠졌다)
```

★ **MySQL 의 `REPEATABLE READ` 는 PG 와 달리 이 자리에서 에러를 내지 않는다.**\
그리고 **B 가 자기 `UPDATE` 뒤에 읽으면 스냅샷(5)이 아니라 3 이 나온다** — 자기가 쓴 것은 언제나 보인다.

### ㅁ. ★ `BEGIN` 을 쳤다고 스냅샷이 찍힌 것은 아니다

`REPEATABLE READ` 로 열어 두고 **아무것도 안 읽은 채** 기다리는 동안 남이 커밋하면, 그 값이 보인다.

```text
시간   세션 B (REPEATABLE READ)              세션 A
 1     BEGIN;                    (읽지 않음)
 2                                           UPDATE t56_item SET qty=77 WHERE id=2;  (자동 커밋)
 3     SELECT qty ... id=2;  -> ?            <- 첫 읽기
 4                                           UPDATE t56_item SET qty=88 WHERE id=2;  (자동 커밋)
 5     SELECT qty ... id=2;  -> ?
```

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
 first_read_after_others_commit             +--------------------------------+
--------------------------------            | first_read_after_others_commit |
                             77             +--------------------------------+
(1 row)                                     |                             77 |
                                            +--------------------------------+
 second_read                                +-------------+
-------------                               | second_read |
          77                                +-------------+
(1 row)                                     |          77 |
                                            +-------------+
```

★ **`BEGIN` 전의 값(7)이 아니라 77 이 나왔다 — 스냅샷은 3번 줄에서 찍혔다.**\
그리고 4번의 88 은 안 보인다 — 찍힌 뒤에는 고정이다. **두 엔진의 답이 같다.**\
「트랜잭션을 미리 열어 두면 그 시점이 고정된다」고 믿는 코드가 여기서 틀린다.

### ㅂ. 「안 터졌다」가 「안전하다」가 아니다

4번의 그림 A·C 는 **에러가 하나도 없는 실행**이다. 그런데 불변식은 깨졌다.\
**동시성 실패는 조용하다** — 통과한 실행이 가장 위험한 근거다.\
그래서 이 주제에서는 **「에러 없이 돌았다」를 결론으로 쓰면 안 되고, 표를 다시 읽어야 한다.**

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 |
|---|---|
| 네 수준의 **이름** | 두 엔진이 같다 |
| 네 수준의 **기본값** | **갈린다.** PG = `read committed`, MySQL = `REPEATABLE-READ` |
| `READ UNCOMMITTED` 가 **더티 리드를 하는가** | **갈린다.** PG = 안 한다(RC 로 동작), MySQL = 한다 |
| `REPEATABLE READ` 의 **잠금 읽기가 스냅샷을 따르는가** | **갈린다.** PG = 따른다, MySQL = 최신을 본다 |
| `SERIALIZABLE` 이 **무엇으로 막는가** | **갈린다.** PG = 커밋 시점 판정(직렬화 실패), MySQL = 잠금(교착) |
| 같은 행 동시 갱신 시 **에러가 나는가** | **갈린다.** PG RR = `could not serialize access`, MySQL RR = 기다렸다 성공 |
| 에러 **번호·문구**(`ERROR 1213`, `Reason code: …`) | 구현 세부다. 문자열 매칭 금지 |
| **스냅샷이 언제 잡히나** | **두 엔진이 같다** — 「트랜잭션의 첫 읽기」다. `BEGIN`/`START TRANSACTION` 자체가 아니다(아래 ㅁ) |

## 언제 쓰고 언제 안 쓰나

- **기본값 그대로 쓴다 — 대부분의 경우.** 올리기 전에 **무엇이 깨지는지**부터 말할 수 있어야 한다.
- **올린다 — 한 트랜잭션에서 여러 번 읽고 그 값들이 서로 맞아야 할 때.** 정산·보고서·대사(reconciliation).
- **`SERIALIZABLE` 을 쓴다 — 불변식이 여러 행에 걸쳐 있고 값이 비쌀 때.** 단 **재시도 루프가 반드시 있어야 한다.**
- **안 올린다 — 「일단 안전하게」.** 스냅샷을 오래 들고 있으면 옛 버전이 쌓이고, 직렬화 실패가 늘고, 처리량이 준다.
- **격리 수준 대신 다른 것을 쓴다 — lost update.** 조건부 갱신(`UPDATE … WHERE qty >= 1`)이 더 싸고 확실하다\
  ([`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 「선택 순서」).
- **엔진을 옮길 때는 기본값부터 맞춘다.** MySQL → PG 이관에서 조용히 깨지는 코드가 여기서 나온다.

## 핵심 문장

- **기본값이 다르다 — PostgreSQL 은 `read committed`, MySQL 은 `REPEATABLE READ` 다. 같은 코드가 다르게 돈다.**
- **PG 의 `READ UNCOMMITTED` 는 이름만 있고 동작은 `READ COMMITTED` 다 — 더티 리드가 안 난다.**
- **MySQL 의 `REPEATABLE READ` 에서 팬텀은 읽는 방식에 달렸다 — 일반 읽기는 스냅샷, 잠금 읽기는 최신이다.**
- **`REPEATABLE READ` 로는 쓰기 왜곡이 안 막힌다 — 에러 하나 없이 불변식이 깨진다.**
- **`SERIALIZABLE` 은 실패를 애플리케이션에 넘기는 계약이다 — 재시도 루프가 없으면 쓰는 의미가 없다.**

## 관련 자료

- [`engineering-axes/concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) — ★ **개념·실패 유형 카탈로그·도구 선택·규모별 방어는 거기가 정본**이다.\
  **여기는 `SET TRANSACTION` 문법과 두 엔진이 실제로 어떻게 도는가까지**다 — 거기의 「격리 수준만으로 lost update 는 안 막힌다」를 **이 편이 실행으로 보인다**(4번).
- [55 트랜잭션 경계](../55-transaction-boundaries-commit-rollback-savepoint/) — 괄호를 여닫는 문법. 이 편의 선행이다.
- [57 명시적 잠금과 교착](../57-explicit-locking-and-deadlock/) — 격리 수준으로 못 막는 것을 **잠금으로 막는 쪽**. 갭 락 실험도 거기 있다.
- [52 UPSERT](../52-upsert/) — 「확인하고 넣기」의 틈을 **문 하나로** 없애는 쪽.
- [60 `EXPLAIN ANALYZE`](../60-explain-analyze-estimates-vs-actuals/) — ★ **PG 에서 `EXPLAIN ANALYZE` 는 변경문을 실제로 돌린다.**\
  이 편처럼 두 세션을 띄운 상태에서 무심코 던지면 **실험 자체가 오염된다.**

## 용어 풀이

- **격리 수준(isolation level)** — 내 트랜잭션이 남의 중간 상태를 얼마나 보는지의 등급.
- **더티 리드(dirty read)** — 남이 아직 커밋하지 않은 값을 읽는 것.
- **반복 불가능 읽기(non-repeatable read)** — 같은 행을 두 번 읽었는데 값이 다른 것.
- **팬텀 리드(phantom read)** — 같은 조건으로 두 번 읽었는데 행 수가 다른 것.
- **쓰기 왜곡(write skew)** — 각자 조건을 확인하고 각자 다른 행을 바꿨는데 합치면 불변식이 깨지는 것.
- **MVCC(다중 버전 동시성 제어)** — 행의 버전을 여러 개 남겨 트랜잭션마다 맞는 버전을 보여 주는 방식.
- **스냅샷(snapshot)** — 어느 시점의 데이터 상태. MVCC 가 어느 버전을 보여 줄지 정하는 기준.
- **일관된 읽기(consistent read)** — 스냅샷을 보는 일반 `SELECT`. 잠금을 걸지 않는다.
- **잠금 읽기(locking read)** — `FOR UPDATE`·`FOR SHARE` 를 붙인 `SELECT`. **최신 상태를 보고 행을 잠근다**([57번](../57-explicit-locking-and-deadlock/)).
- **직렬화 실패(serialization failure)** — 동시에 돈 트랜잭션들을 어떤 순서로도 설명할 수 없어 하나를 거부하는 것.
- **갭 락(gap lock)** — InnoDB 가 **행 사이의 빈 구간**에 거는 잠금. 그 구간에 새 행을 못 넣게 한다.
- **교착(deadlock)** — 서로가 쥔 잠금을 기다려 둘 다 못 나아가는 상태.

## 더 들어가면

- **PG 의 `SERIALIZABLE` 은 SSI(Serializable Snapshot Isolation)다.** 잠금을 더 거는 대신 **읽기·쓰기 의존을 추적**해\
  커밋 시점에 사이클이 보이면 하나를 취소한다. 그래서 **읽기가 여전히 쓰기를 막지 않는다** — 대신 **실패율이 올라간다.**
- **MySQL 의 `SERIALIZABLE` 은 잠금 쪽으로 보인다.** 위 실험에서 실패가 **직렬화 에러가 아니라 교착**(`ERROR 1213`)으로 났고,\
  교착이 나려면 **일반 `SELECT` 가 잠금을 잡았어야** 한다. 관찰은 여기까지이고, 내부 구현은 이 편에서 확인하지 않았다.
- **★ 스냅샷은 `BEGIN` 이 아니라 첫 읽기에서 잡힌다 — 두 엔진 다 그렇다(실측).**\
  `BEGIN` 만 쳐 두고 그 사이에 남이 커밋한 뒤 처음 읽으면, **그 커밋된 값이 보인다.**
- **긴 트랜잭션의 진짜 비용은 저장소다.** 아무도 안 보는 옛 버전을 엔진이 못 버린다 — PG 는 `VACUUM`, InnoDB 는 언두 로그가 커진다.\
  구조 자체는 [`data-structure/`](../../../../../data-structure/) 와 [`systems/`](../../../../../systems/) 의 몫이고, 여기서는 「**긴 괄호가 비싸다**」까지만 안다.
