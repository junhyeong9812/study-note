# sql/54-RETURNING 과 변경문을 품은 CTE — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Returning Data from Modified Rows](https://www.postgresql.org/docs/18/dml-returning.html) · [PostgreSQL 18 · WITH Queries (CTE)](https://www.postgresql.org/docs/18/queries-with.html) · [PostgreSQL 18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/) · [MySQL 8.4 · WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **한쪽에서만 결론이 서는 주제다.** MySQL 8.4.10 에는 `RETURNING` 도, 변경문을 품은 CTE 도 **없다** —\
> MySQL 쪽 출력은 **`ERROR 1064` 세 개와 「읽기 전용 CTE 는 된다」는 통과 하나**가 전부이고, 동작 근거는 **PostgreSQL 18.6** 이다.\
> **버전** — `RETURNING` 자체는 PG 에 오래전부터 있다. ★ **`OLD`/`NEW` 별칭은 PG 18 부터**다([18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)). `MERGE` 에 `RETURNING` 이 붙은 것은 17 부터다([53번](../53-merge/)).\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 `t54_a`·`t54_log` 를 만들었고 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> **선행** — [32 CTE(`WITH`)](../32-cte-with-clause/)(이름·가시성·최적화 장벽의 정본) · [49 INSERT](../49-insert-multi-row-and-insert-select/).

## 한눈에 — 쉽게 말하면

**`RETURNING` = 「고친 행을 그 자리에서 돌려받는 것」.**

```text
RETURNING 없이                          RETURNING 으로
─────────────                           ──────────────
① UPDATE t SET qty = qty+1 WHERE ...    ① UPDATE t SET qty = qty+1 WHERE ...
② SELECT * FROM t WHERE ...                  RETURNING id, qty;
   ^^^ 다시 읽어야 한다                      ^^^ 한 번에 받는다
   ★ 그 사이 다른 세션이 또 고쳤을 수도
```

일상 비유로 바꾸면 **창구에서 접수증을 받는 것**이다.

```text
접수만 하고 나오면       -> 나중에 "내 번호 뭐였지?" 하고 다시 물어야 한다
접수증을 받아 나오면     -> 그 자리에서 번호를 안다. 그 사이 바뀔 일이 없다
```

**그리고 그 접수증을 「다음 창구에 그대로 낼」 수 있다** — 변경문을 품은 CTE 다.

```text
WITH moved AS (DELETE FROM t54_a WHERE qty >= 30 RETURNING *)   <- 지우면서 받아
INSERT INTO t54_log SELECT id, name, qty, 'moved' FROM moved;   <- 그대로 넣는다
```

"똑같은 구조다" — **지우기와 넣기가 한 문 안에서 원자적으로** 일어난다.

| 비유 | 실체 |
|---|---|
| 접수증 | `RETURNING` 이 돌려주는 행 |
| 접수증을 다음 창구에 낸다 | `WITH x AS (DELETE … RETURNING *) INSERT … FROM x` |
| 접수 전 명부의 사본 | ★ **같은 문 안의 다른 조각이 보는 「변경 전 스냅숏」** |
| 접수증 두 장을 받아도 접수는 한 번 | 변경 CTE 는 **참조 횟수와 무관하게 한 번만** 실행된다 |
| 접수증을 아무도 안 받아 가도 접수는 됐다 | 참조되지 않는 변경 CTE 도 **실행된다** |

★ **이 편에서 가장 값비싼 한 줄** — **같은 문 안의 다른 CTE 는 변경 전 상태를 본다.**\
지우면서 세면 **지우기 전 개수**가 나온다(4번). PG 문서가 그것을 문장으로 적는다.

## 이 주제가 답하려는 질문

1. **`RETURNING` 은 어느 문에 붙고 무엇을 돌려주나?** — `INSERT`·`UPDATE`·`DELETE` 가 각각 다른가.
2. **한 문 안에서 여러 표를 바꾸면 서로의 변경이 보이나?** — 보인다면 어느 시점의 것인가.
3. **MySQL 로 옮기면 무엇이 안 되나?** — 무엇으로 대신하나.

## 예시 데이터 — 이 편이 만든 표

`emp`·`dept` 는 **한 줄도 쓰지 않았다.**

```text
t54_a (본 표)                    t54_log (보관 표)
+----+------+-----+              +----+------+-----+-------+
| id | name | qty |              | id | name | qty | note  |
+----+------+-----+              +----+------+-----+-------+
|  1 | ann  |  10 |              (비어 있다)
|  2 | bob  |  20 |
|  3 | cho  |  30 |   <- qty >= 30
|  4 | dan  |  40 |   <- qty >= 30
+----+------+-----+
```

```sql
CREATE TABLE t54_a   (id int PRIMARY KEY, name varchar(10), qty int);
CREATE TABLE t54_log (id int, name varchar(10), qty int, note varchar(10));
```

실험은 전부 `BEGIN`/`ROLLBACK` 으로 감쌌다 — 기준 상태는 매번 위 그림과 같다.

## 동작 방식

### 1. `RETURNING` 이 붙는 문 — 셋 다 붙는다

**언제 쓰나** — 바꾼 행의 값이 곧바로 필요할 때. 자동 생성된 키가 대표다.

```text
### SQL: INSERT INTO t54_a VALUES (5,'eve',50) RETURNING id, name, qty;
--- PG 18.6 ---
 id | name | qty 
----+------+-----
  5 | eve  |  50
(1 row)
INSERT 0 1
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'RETURNING id, name, qty' at line 1

### SQL: UPDATE t54_a SET qty = qty + 1 WHERE id <= 2 RETURNING id, name, qty;
--- PG 18.6 ---
 id | name | qty 
----+------+-----
  1 | ann  |  11
  2 | bob  |  21
(2 rows)
UPDATE 2
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... right syntax to use near 'RETURNING id, name, qty' at line 1

### SQL: DELETE FROM t54_a WHERE id = 5 RETURNING id, name, qty;
--- PG 18.6 ---
 id | name | qty 
----+------+-----
  5 | eve  |  50
(1 row)
DELETE 1
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... right syntax to use near 'RETURNING id, name, qty' at line 1
```

```text
             무엇을 돌려주나 (별칭 없이 열 이름만 썼을 때)
INSERT       ★ 넣은 뒤의 행  (기본값·생성 열·자동 증가가 채워진 값)
UPDATE       ★ 고친 뒤의 행  (qty 가 11 · 21 이다)
DELETE       ★ 지우기 전의 행 (지운 뒤에는 행이 없으니 당연하다)
```

그림 해설 — **문마다 「자연스러운 쪽」을 돌려준다.** `MERGE` 도 17 부터 붙는다([53번](../53-merge/)).\
비용 — **결과 집합이 생기므로** 애플리케이션이 그것을 읽어야 한다. 안 읽어도 문은 실행된다.

★ **`RETURNING` 은 `SELECT` 목록처럼 쓸 수 있다** — 식·상수·`*` 가 다 된다.

```text
### SQL: UPDATE t54_a SET qty = qty*2 WHERE id=1 RETURNING id, qty, qty/2 AS half, 'done' AS tag;
--- PG 18.6 ---
 id | qty | half | tag  
----+-----+------+------
  1 |  20 |   10 | done
(1 row)
UPDATE 1

### SQL: DELETE FROM t54_a WHERE id=4 RETURNING *;
--- PG 18.6 ---
 id | name | qty 
----+------+-----
  4 | dan  |  40
(1 row)
DELETE 1
```

> **`RETURNING`** — 변경한 행을 그 문의 결과로 돌려받는 절.\
> 예: `INSERT … RETURNING id` 로 자동 생성된 키를 조회 없이 받는다.

### 2. ★ PG 18 의 `OLD`/`NEW` — 전후를 같이 받는다

**언제 쓰나** — 「무엇이 무엇으로 바뀌었나」를 기록할 때. **PG 18 부터다.**

```text
### SQL: UPDATE t54_a SET qty = qty*2 WHERE id <= 2 RETURNING id, OLD.qty AS before, NEW.qty AS after;
--- PG 18.6 ---
 id | before | after 
----+--------+-------
  1 |     10 |    20
  2 |     20 |    40
(2 rows)
UPDATE 2
```

**`INSERT` 와 `DELETE` 에서는 한쪽이 없다.**

```text
### SQL: INSERT INTO t54_a VALUES (9,'new',90) RETURNING id, OLD.qty AS before, NEW.qty AS after;
--- PG 18.6 ---
 id | before | after 
----+--------+-------
  9 |        |    90        <- OLD 가 NULL 이다 (전에 없던 행이다)
(1 row)
INSERT 0 1

### SQL: DELETE FROM t54_a WHERE id=4 RETURNING id, OLD.qty AS before, NEW.qty AS after;
--- PG 18.6 ---
 id | before | after 
----+--------+-------
  4 |     40 |              <- NEW 가 NULL 이다 (뒤에 남는 행이 없다)
(1 row)
DELETE 1
```

```text
              OLD            NEW
INSERT        NULL           넣은 행
UPDATE        고치기 전       고친 뒤
DELETE        지우기 전       NULL

★ 별칭 없이 그냥 qty 라고 쓰면 위 1번의 "자연스러운 쪽" 이 나온다
```

릴리스 노트가 그 이전 동작까지 적는다.

> "Add `OLD`/`NEW` support to `RETURNING` in DML queries (Dean Rasheed) … **Previously `RETURNING` only returned new values for INSERT and UPDATE, and old values for DELETE**; `MERGE` would return the appropriate value for the internal query executed. This new syntax allows the `RETURNING` list of `INSERT`/`UPDATE`/`DELETE`/`MERGE` to explicitly return old and new values by using the special aliases `old` and `new`."\
> — [PostgreSQL 18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)

★ **버전을 적는 자리다.** **PG 17 이하에서는 `OLD`/`NEW` 를 못 쓴다.**\
**이 머신에 PG 17 이하 컨테이너가 없어 그 거부는 직접 재현하지 못했다** — 근거는 릴리스 노트다.

비용 — 감사 로그·변경 이력을 **트리거 없이** 한 문으로 만들 수 있다.

### 3. 변경문을 품은 CTE — 접수증을 다음 창구에 낸다

**언제 쓰나** — 「옮기기」. 한쪽에서 지우고 다른 쪽에 넣는 작업이다.

```text
WITH moved AS (DELETE FROM t54_a WHERE qty >= 30 RETURNING *)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
     이름 붙인 조각이 "지우면서 돌려준 행" 이 된다
INSERT INTO t54_log SELECT id, name, qty, 'moved' FROM moved;
                                                      ^^^^^ 그 행을 그대로 쓴다
```

```text
(전)                              (후)
t54_a                             t54_a
+----+------+-----+               +----+------+-----+
|  1 | ann  |  10 |               |  1 | ann  |  10 |
|  2 | bob  |  20 |               |  2 | bob  |  20 |
|  3 | cho  |  30 |      →        +----+------+-----+
|  4 | dan  |  40 |
+----+------+-----+               t54_log
t54_log = 비어 있다               +----+------+-----+-------+
                                  |  3 | cho  |  30 | moved |
                                  |  4 | dan  |  40 | moved |
                                  +----+------+-----+-------+
```

**한 문이므로 원자적이다.** 「지웠는데 못 넣은」 상태가 생기지 않는다.

`WITH` 의 이름·범위·앞뒤 참조 규칙은 [32 번](../32-cte-with-clause/)이 정본이다 — 여기서는 **변경문이 들어갔을 때만** 다룬다.

★ **놓을 수 있는 자리가 정해져 있다.**

```text
### SQL: SELECT * FROM (DELETE FROM t54_a WHERE id=4 RETURNING *) AS d;
--- PG 18.6 ---
ERROR:  syntax error at or near "FROM"
LINE 1: SELECT * FROM (DELETE FROM t54_a WHERE id=4 RETURNING *) AS ...
                              ^

### SQL: SELECT (SELECT count(*) FROM (WITH d AS (DELETE FROM t54_a WHERE id=4 RETURNING *) SELECT * FROM d) AS s) AS n;
--- PG 18.6 ---
ERROR:  WITH clause containing a data-modifying statement must be at the top level
LINE 1: ... SELECT (SELECT count(*) FROM (WITH d AS (DELETE FROM ...
                                              ^
```

**변경문은 `FROM` 에 직접 못 놓고, 그것을 담은 `WITH` 는 최상위에만** 놓을 수 있다.\
두 번째 에러 문구가 규칙을 그대로 말해 준다.

### 4. ★★ 가시성 — **같은 문 안의 다른 조각은 변경 전을 본다**

**언제 쓰나** — 한 문에서 바꾸고 세야 할 때. **이 편의 핵심이고, 가장 자주 틀리는 자리다.**

지우면서 **같은 문 안에서 본 표를 센다.**

```sql
WITH moved AS (DELETE FROM t54_a WHERE qty >= 30 RETURNING *),
     ins   AS (INSERT INTO t54_log SELECT id, name, qty, 'moved' FROM moved RETURNING *)
SELECT (SELECT count(*) FROM t54_a) AS a_seen_in_same_stmt,
       (SELECT count(*) FROM moved) AS moved_rows,
       (SELECT count(*) FROM ins)   AS logged_rows;
```

```text
--- PG 18.6 ---
BEGIN;
SELECT count(*) AS a_before FROM t54_a;
 a_before 
----------
        4
(1 row)

(위 WITH 문)
 a_seen_in_same_stmt | moved_rows | logged_rows 
---------------------+------------+-------------
                   4 |          2 |           2
(1 row)

SELECT count(*) AS a_after FROM t54_a;
 a_after 
---------
       2
(1 row)

SELECT * FROM t54_a ORDER BY id;          SELECT * FROM t54_log ORDER BY id;
 id | name | qty                           id | name | qty | note  
----+------+-----                         ----+------+-----+-------
  1 | ann  |  10                            3 | cho  |  30 | moved
  2 | bob  |  20                            4 | dan  |  40 | moved
(2 rows)                                   (2 rows)
ROLLBACK;
```

★ **세 숫자를 나란히 읽는다.**

```text
a_before             = 4     문 이전
a_seen_in_same_stmt  = 4     ★ 같은 문 안에서 센 값 — 두 행을 지우는 중인데도 4다
moved_rows           = 2     실제로 지워진 행
a_after              = 2     문이 끝난 뒤
```

```text
문 밖에서 보면                          같은 문 안에서 보면
+---------------------------+           +---------------------------+
| 전: 4행                   |           | t54_a 를 세면 ★ 4         |
| 후: 2행                   |           | (DELETE 가 도는 중인데도)  |
+---------------------------+           +---------------------------+
  -> 변경이 보인다                          -> ★ 변경 전 스냅숏을 본다
```

PG 문서가 그 규칙을 문장으로 적는다 — 인용한다.

> "The sub-statements in `WITH` are executed concurrently with each other and with the main query. Therefore, when using data-modifying statements in `WITH`, the order in which the specified updates actually happen is unpredictable. **All the statements are executed with the same _snapshot_ (see Chapter 13), so they cannot "see" one another's effects on the target tables.**"\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

**그래서 「지운 뒤 남은 개수」를 같은 문에서 셀 수 없다.** 문을 나눠야 한다.

```text
왜 이렇게 설계했나 — 순서가 정해져 있지 않기 때문이다

  WITH a AS (DELETE ...), b AS (UPDATE ...)  SELECT ...
       ^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^
       누가 먼저 도는지 문서가 "unpredictable" 이라고 적는다
       -> 서로의 결과가 보이면 답이 실행 순서에 따라 달라진다
       -> ★ 아예 안 보이게 해서 답을 하나로 고정한다
```

비용 — **읽기 조각은 언제나 문 시작 시점의 표를 본다.** 그 점은 일관되고 예측 가능하다.\
대신 **「바꾸고 그 결과를 같은 문에서 다시 읽기」는 불가능**하다.

★ 같은 성질을 [49 번 11절의 자기 표 삽입](../49-insert-multi-row-and-insert-select/)이 더 작은 규모로 보여 준다 —\
`INSERT INTO t SELECT … FROM t` 가 새로 넣은 행을 다시 안 읽는 것이 **같은 스냅숏 규칙**이다.

### 5. ★ 한 번만 실행되고, 안 읽어도 실행된다

**언제 쓰나** — 변경 CTE 를 여러 번 참조하거나, 아예 참조하지 않을 때.

**(a) 두 번 참조해도 한 번만 실행된다.**

```text
--- PG 18.6 ---
BEGIN;
WITH d AS (DELETE FROM t54_a WHERE id=4 RETURNING *)
SELECT (SELECT count(*) FROM d) AS c1, (SELECT count(*) FROM d) AS c2;
 c1 | c2 
----+----
  1 |  1
(1 row)
SELECT count(*) AS remaining FROM t54_a;
 remaining 
-----------
         3          <- ★ 한 행만 지워졌다. 두 번 지워지지 않았다
(1 row)
ROLLBACK;
```

**(b) 아무도 안 읽어도 실행된다.**

```text
--- PG 18.6 ---
BEGIN;
WITH gone AS (DELETE FROM t54_a WHERE id=4 RETURNING *)
SELECT 1 AS dummy;                          -- gone 을 어디서도 안 쓴다
 dummy 
-------
     1
(1 row)
SELECT * FROM t54_a ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |  10
  2 | bob  |  20
  3 | cho  |  30
(3 rows)                                    <- ★ id=4 가 지워졌다
ROLLBACK;
```

문서가 두 가지를 한 문장으로 적는다.

> "Data-modifying statements in `WITH` are executed exactly once, and always to completion, **independently of whether the primary query reads all (or indeed any) of their output.**"\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

★ [**32 번의 최적화 장벽 이야기와 정확히 갈리는 자리다.**](../32-cte-with-clause/)\
읽기 전용 CTE 는 **참조가 한 번이면 인라인되고 두 번이면 벽이 선다**(PG 12+ 규칙).\
**변경 CTE 에는 그 규칙이 적용되지 않는다** — 인라인 후보 조건이 「side-effect-free」이기 때문이다.

```text
읽기 전용 CTE   참조 1회 -> 인라인될 수 있다 (여러 번 평가될 수도 있다)
                참조 2회 -> PG 는 벽을 세운다 (한 번 평가)
변경 CTE        ★ 참조 횟수와 무관하게 정확히 한 번, 끝까지 실행된다
```

비용 — **`WITH` 에 변경문을 적어 두고 「안 쓰니까 안 돌겠지」로 생각하면 안 된다.** 돈다.

### 6. ★ 같은 표를 두 조각이 바꾸면 — 하나만 먹는다

**언제 쓰나** — 한 문에서 같은 행을 두 번 건드리게 됐을 때.

```text
--- PG 18.6 ---
BEGIN;
WITH u1 AS (UPDATE t54_a SET qty = 100 WHERE id=1 RETURNING id),
     u2 AS (UPDATE t54_a SET qty = 200 WHERE id=1 RETURNING id)
SELECT (SELECT count(*) FROM u1) AS u1_rows, (SELECT count(*) FROM u2) AS u2_rows;
 u1_rows | u2_rows 
---------+---------
       1 |       0        <- ★ 한쪽만 먹었다
(1 row)
SELECT id, qty FROM t54_a WHERE id=1;
 id | qty 
----+-----
  1 | 100
(1 row)
ROLLBACK;
```

한쪽이 지우고 한쪽이 고쳐도 같다.

```text
--- PG 18.6 ---
BEGIN;
WITH d AS (DELETE FROM t54_a WHERE id=2 RETURNING id),
     u AS (UPDATE t54_a SET qty=999 WHERE id=2 RETURNING id)
SELECT (SELECT count(*) FROM d) AS deleted, (SELECT count(*) FROM u) AS updated;
 deleted | updated 
---------+---------
       1 |       0
(1 row)
SELECT * FROM t54_a ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |  10
  3 | cho  |  30
  4 | dan  |  40
(3 rows)
ROLLBACK;
```

문서가 이 경우를 명시한다.

> "**Trying to update the same row twice in a single statement is not supported. Only one of the modifications takes place, but it is not easy (and sometimes not possible) to reliably predict which one.**"\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

★ **이 실험에서 세 판 모두 `u1` 이 이겼다.** 그러나 **문서가 「예측할 수 없다」고 적었으므로\
그것은 관찰이지 보장이 아니다** — [작성법 §2-1](../../../../../../reference/study-note-guide.md)의 「같은 값이 나와 보장으로 오해한다」가 그대로 적용된다.

★ **에러가 아니라는 점이 위험하다.** [53 번의 `MERGE`](../53-merge/)나 [52 번의 `ON CONFLICT`](../52-upsert/)는\
같은 행을 두 번 건드리면 **거부**한다. 변경 CTE 는 **조용히 하나만 적용**한다.

대가 — **한 문 안에서 같은 표를 두 조각이 건드리지 않도록 설계한다.**

### 7. MySQL 로 옮기면 — **무엇이 없고 무엇이 있나**

**언제 쓰나** — 이식할 때. **없는 것과 있는 것을 정확히 나눈다.**

```text
### SQL: WITH moved AS (DELETE FROM t54_a WHERE qty >= 30 RETURNING *) SELECT * FROM moved;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'DELETE FROM t54_a WHERE qty >= 30 RETURNING *) SELECT * FROM moved' at line 1
```

★ **그런데 `WITH` 자체는 `DELETE` 에 붙는다** — CTE 안이 **읽기 전용**이면 된다.

```text
### SQL: WITH moved AS (SELECT * FROM t54_a WHERE qty >= 30) DELETE FROM t54_a WHERE id IN (SELECT id FROM moved);
--- MySQL 8.4.10 ---
(성공)
### SQL: SELECT count(*) AS n FROM t54_a;
--- MySQL 8.4.10 ---
+---+
| n |
+---+
| 2 |
+---+
```

```text
MySQL 8.4.10 에서
  CTE 안에 변경문          -> ★ 없다 (ERROR 1064)
  변경문 앞에 읽기 CTE     -> ★ 된다
  RETURNING                -> ★ 없다 (ERROR 1064)
```

**「옮기기」를 MySQL 로 쓰면 문이 둘이 되고, 트랜잭션이 필요해진다.**

```sql
START TRANSACTION;
INSERT INTO t54_log SELECT id, name, qty, 'moved' FROM t54_a WHERE qty >= 30;   -- ① 먼저 복사
DELETE FROM t54_a WHERE qty >= 30;                                               -- ② 그 다음 삭제
COMMIT;
```

★ **순서가 중요하다.** ②를 먼저 하면 ①이 읽을 행이 없다 — **문이 둘이면 스냅숏이 둘**이기 때문이다.\
PG 의 한 문 판은 그 순서 고민이 아예 없다.

★ **그리고 조건이 두 문에 두 번 적힌다.** 그 사이에 조건에 걸리는 행이 새로 들어오면\
**`DELETE` 는 지우는데 `INSERT` 는 못 복사한 행**이 생긴다 — 격리 수준이 그것을 막는지는 [56 격리 수준](../56-isolation-levels-read-phenomena-mvcc/) 주제다.\
(★ **이 경쟁 상황은 이 편에서 재현하지 않았다.**)

**자동 생성 키를 받는 것도 대체물이 다르다.**

```text
PG    : INSERT ... RETURNING id           -> 실제 값을 그대로
MySQL : SELECT LAST_INSERT_ID()           -> ★ 배치의 "첫" 번호만 (49번 12절)
```

## 문법 — 어느 절에서 무엇이 갈리나

```sql
-- PG 만
INSERT INTO t ... RETURNING { * | 식 [AS 별칭] [, ...] };
UPDATE t SET ... WHERE ... RETURNING ...;
DELETE FROM t WHERE ... RETURNING ...;
MERGE INTO t ... RETURNING merge_action(), ...;          -- PG 17+ (53번)

-- PG 18+
... RETURNING id, OLD.qty AS before, NEW.qty AS after;

-- 변경문을 품은 CTE (PG 만) — ★ 최상위 WITH 에만
WITH moved AS (DELETE FROM t WHERE ... RETURNING *)
INSERT INTO log SELECT ... FROM moved;

-- MySQL 8.4.10
WITH x AS (SELECT ...) DELETE FROM t WHERE id IN (SELECT id FROM x);   -- ★ 읽기 CTE 는 된다
-- RETURNING 은 없다. 변경문을 CTE 안에 넣을 수 없다
```

규칙 일곱.

1. **`RETURNING` 은 `INSERT`·`UPDATE`·`DELETE`·`MERGE`(17+) 에 붙는다.**
2. **별칭 없이 열 이름만 쓰면** `INSERT`/`UPDATE` 는 **뒤**, `DELETE` 는 **앞** 값이다.
3. **`OLD`/`NEW` 별칭은 PG 18 부터**다. 한쪽이 없는 문에서는 그쪽이 `NULL` 이다.
4. **변경문은 `FROM` 에 직접 못 놓는다.** `WITH` 로 이름을 붙여야 한다.
5. **변경문을 담은 `WITH` 는 최상위에만** 놓을 수 있다 — 서브쿼리 안이면 에러다.
6. ★ **변경 CTE 는 참조 횟수와 무관하게 정확히 한 번, 끝까지** 실행된다.
7. ★ **같은 문의 조각들은 같은 스냅숏을 본다** — 서로의 변경이 안 보인다.

읽을 때 붙잡을 것은 **「이 조각이 보는 표는 언제의 표인가」** 하나다.

```text
 문 밖의 SELECT      -> 문이 끝난 뒤의 표
 문 안의 어떤 조각도 -> ★ 문이 시작될 때의 표
 RETURNING 이 준 행  -> ★ 그 변경문이 실제로 건드린 행 (유일하게 "새" 정보다)
```

#### 방언 요약

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `RETURNING` | 있다(`INSERT`/`UPDATE`/`DELETE`/`MERGE`) | **없다** — `ERROR 1064` |
| `OLD`/`NEW` 별칭 | **18 부터** | — |
| CTE 안의 변경문 | 있다 | **없다** — `ERROR 1064` |
| 변경문 앞의 읽기 CTE | 있다 | ★ **있다** |
| 변경 CTE 실행 횟수 | **정확히 한 번, 끝까지** | — |
| 같은 문 안의 가시성 | **같은 스냅숏 — 서로 안 보인다** | — |
| 같은 행을 두 번 | **하나만 적용. 어느 쪽인지 예측 불가**(문서) | — |
| 자동 키 회수 | `RETURNING id` — 실제 값 | `LAST_INSERT_ID()` — 배치의 첫 번호([49번](../49-insert-multi-row-and-insert-select/)) |

## 어디서 틀리나

1. ★★ **같은 문 안에서 「지운 뒤 남은 개수」를 센다.**\
   **변경 전 개수가 나온다**(4번). 문서가 「서로의 효과를 볼 수 없다」고 적는다.
2. ★ **`WITH` 에 적어 둔 변경문이 「안 쓰면 안 돈다」고 생각한다.**\
   **돈다**(5번 b). 참조 여부와 무관하다.
3. **변경 CTE 를 두 번 참조하면 두 번 실행될 것이라 기대한다.** **한 번이다**(5번 a).
4. **[32 번의 인라인 규칙](../32-cte-with-clause/)을 변경 CTE 에도 적용한다.**\
   그 규칙의 조건이 「side-effect-free」다 — 변경 CTE 는 해당이 없다.
5. **한 문에서 같은 행을 두 조각이 건드린다.**\
   **에러가 아니라 하나만 적용되고, 어느 쪽인지 예측할 수 없다**(6번).
6. **변경문을 `FROM` 에 직접 놓는다.** 구문 오류다(3번).
7. **변경 CTE 를 서브쿼리 안에 쓴다.** `must be at the top level` 이다(3번).
8. **`OLD`/`NEW` 를 PG 17 이하에서 쓴다.** **18 부터**다(2번).
9. **`RETURNING` 쓴 코드를 MySQL 로 옮긴다.** `ERROR 1064` 다(7번).
10. **MySQL 에서 「옮기기」를 `DELETE` → `INSERT` 순서로 쓴다.**\
    먼저 지우면 복사할 행이 없다 — **문이 둘이면 스냅숏도 둘**이다(7번).
11. **`LAST_INSERT_ID()` 를 `RETURNING id` 의 동등물로 쓴다.**\
    **배치의 첫 번호만** 준다([49 번 12절](../49-insert-multi-row-and-insert-select/)).

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| `RETURNING` 의 존재 | — | ★ **전부** — PG 에만 있다 |
| 별칭 없는 열의 의미 | PG 18 릴리스 노트가 이전 동작까지 적는다 | — |
| `OLD`/`NEW` | PG 18+ 의 문서화된 문법 | — |
| 변경 CTE 실행 횟수 | **PG 문서: 정확히 한 번, 끝까지** | — |
| 같은 문 안의 가시성 | **PG 문서: 같은 스냅숏** | — |
| 같은 행 두 번 | **PG 문서: 하나만, 어느 쪽인지 예측 불가** | ★ 실제로 어느 쪽이 이기나 |
| CTE 조각의 실행 순서 | **PG 문서: unpredictable** | 실제 순서 |

- ★ **6번의 「세 판 다 `u1` 이 이겼다」는 관찰이다.** 문서가 명시적으로 「예측할 수 없다」고 적었으므로\
  **반복 실행이 같았다는 사실이 보장의 근거가 되지 않는다.**
- ★ **이 편의 MySQL 쪽 근거는 `ERROR 1064` 세 개와 「읽기 CTE 는 된다」는 통과 하나**뿐이다.\
  그 밖의 모든 동작 설명은 **PG 출력과 PG 문서**에서 나왔다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 자동 생성 키 회수.** `INSERT … RETURNING id` 하나면 추정이 필요 없다.
- **쓴다 — 바꾼 행을 눈으로 확인하며 트랜잭션 안에서 돌릴 때.**\
  [50 번의 `WHERE` 빠뜨린 `UPDATE`](../50-update-with-join-and-subquery/)·[51 번의 대량 삭제](../51-delete-and-truncate/)에서 그것이 안전장치가 된다.
- **쓴다 — 「옮기기」.** 지우면서 보관 표에 넣는 작업이 한 문이 된다(3번).
- **쓴다 — 변경 이력.** `OLD`/`NEW` 로 전후를 한 번에 받는다(PG 18+).
- **안 쓴다 — 같은 문에서 바꾼 결과를 다시 읽기.** 안 보인다(4번). 문을 나눈다.
- **안 쓴다 — 한 문에서 같은 행을 두 조각이 건드리기.** 조용히 하나만 먹는다(6번).
- **안 쓴다 — MySQL 을 같이 쓰는 코드베이스에서.** 한쪽에서 안 돈다(7번).
- **조심한다 — `RETURNING` 이 큰 결과를 만들 때.** 대량 `DELETE … RETURNING *` 은 행 전부를 돌려준다.\
  필요한 열만 적는다.

## 핵심 문장

- **`RETURNING` 은 `INSERT`·`UPDATE`·`DELETE`(그리고 `MERGE`, 17+)에 붙고, MySQL 8.4.10 에는 없다.**
- **별칭 없이 쓰면 `INSERT`/`UPDATE` 는 뒤 값, `DELETE` 는 앞 값**이다. `OLD`/`NEW` 는 **PG 18 부터**다.
- **변경문은 `FROM` 에 못 놓고, 그것을 담은 `WITH` 는 최상위에만** 놓을 수 있다.
- ★ **변경 CTE 는 참조 횟수와 무관하게 정확히 한 번, 끝까지 실행된다** — 안 읽어도 돈다.
- ★★ **같은 문의 조각들은 같은 스냅숏을 본다** — 지우면서 세면 **지우기 전 개수**가 나온다.
- **같은 행을 두 조각이 건드리면 하나만 적용되고, 어느 쪽인지 예측할 수 없다**(문서).
- **MySQL 에서 「옮기기」는 문이 둘이 된다** — 복사를 먼저, 삭제를 나중에, 한 트랜잭션에서.

## 관련 자료

- [PostgreSQL 18 · Returning Data from Modified Rows](https://www.postgresql.org/docs/18/dml-returning.html) — `RETURNING` 의 정본.
- [PostgreSQL 18 · WITH Queries (CTE)](https://www.postgresql.org/docs/18/queries-with.html) — 「Data-Modifying Statements in WITH」 절이 4·5·6번의 근거다.
- [PostgreSQL 18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/) — `OLD`/`NEW` 별칭 도입.
- [MySQL 8.4 · WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html) — CTE 를 `DELETE`/`UPDATE` 앞에 쓰는 형태.
- [32 CTE(`WITH`) — 이름 붙인 서브질의와 가시성](../32-cte-with-clause/) — ★ **그쪽은 이름·범위·전방 참조·최적화 장벽(`MATERIALIZED`)까지, 여기는 그 `WITH` 안에 변경문이 들어갔을 때부터.**\
  인라인 규칙·이름 가리기는 한 줄도 여기서 다시 쓰지 않는다.
- [49 INSERT](../49-insert-multi-row-and-insert-select/) — **11절의 자기 표 삽입이 4번과 같은 스냅숏 규칙**이고, 12절의 `LAST_INSERT_ID()` 가 7번의 대체물이다.
- [50 UPDATE](../50-update-with-join-and-subquery/) · [51 DELETE 와 TRUNCATE](../51-delete-and-truncate/) — `RETURNING` 이 안전장치가 되는 자리.
- [52 UPSERT](../52-upsert/) — `RETURNING` 으로 「삽입인지 갱신인지」를 가리는 예가 거기 있다.
- [53 MERGE](../53-merge/) — `merge_action()` 이 붙은 `RETURNING`(PG 17+).
- [SQL 주제 목록](../README.md) — 55(트랜잭션 경계)·56(격리 수준)이 7번 이식 형태의 이웃이다.

## 용어 풀이

- **`RETURNING`** — 변경한 행을 그 문의 결과로 돌려받는 절.\
  예: `INSERT … RETURNING id` 로 자동 생성된 키를 조회 없이 받는다.
- **변경문을 품은 CTE(data-modifying CTE)** — `WITH` 의 조각이 `SELECT` 가 아니라 `INSERT`/`UPDATE`/`DELETE` 인 것.\
  예: `WITH moved AS (DELETE … RETURNING *) INSERT INTO log SELECT … FROM moved`.
- **스냅숏(snapshot)** — 한 문(또는 트랜잭션)이 「지금 표가 이렇게 생겼다」고 보는 고정된 상태.\
  예: 같은 문의 모든 조각이 **같은** 스냅숏을 보므로 서로의 변경이 안 보인다.
- **`OLD`/`NEW` 별칭** — `RETURNING` 에서 변경 전·후 행을 각각 가리키는 이름(PG 18+).\
  예: `RETURNING OLD.qty AS before, NEW.qty AS after`.
- **최상위 `WITH`(top level)** — 문장의 맨 앞에 붙은 `WITH`. 서브쿼리 안이 아니다.\
  예: 변경 CTE 를 서브쿼리 안에 넣으면 `must be at the top level` 에러다.
- **부작용 없음(side-effect-free)** — 표를 바꾸지 않고 휘발성 함수도 안 쓰는 것.\
  예: PG 가 CTE 를 인라인하는 조건이고, 변경 CTE 는 여기 해당하지 않는다([32번](../32-cte-with-clause/)).
- **원자적(atomic)** — 전부 일어나거나 하나도 안 일어나는 성질.\
  예: 한 문 안의 삭제와 삽입은 원자적이라 「지웠는데 못 넣은」 상태가 없다.
- **`LAST_INSERT_ID()`** — MySQL 에서 자동 증가 번호를 돌려주는 함수.\
  예: 배치에서는 **첫** 번호를 준다 — `RETURNING id` 의 동등물이 아니다([49번](../49-insert-multi-row-and-insert-select/)).
- **`ERROR 1064`** — MySQL 의 구문 오류. 파서가 그 문법을 모른다는 뜻이다.\
  예: `RETURNING` 도, CTE 안의 `DELETE` 도 여기서 막힌다.

## 더 들어가면

- **`RETURNING` 은 트리거·규칙이 바꾼 값도 반영한다**(PG 문서). 그래서 「실제로 저장된 값」을 보는 창이 된다.\
  **이 편에서는 트리거를 만들지 않았다** — 저장 프로그램은 이 목록의 축 밖이다([README](../README.md)의 「뺀 것」).
- **변경 CTE 여러 개를 사슬로 이을 수 있다** — 4번의 `moved → ins` 가 그 예다.\
  사슬이 길어지면 **모두 같은 스냅숏을 본다**는 사실이 더 중요해진다.
- **`RETURNING` 의 결과를 다시 `RETURNING` 할 수는 없다** — CTE 로 이름을 붙여야 한다(3번의 문법 제약).
- **PG 의 `RETURNING` 은 커서로도 읽을 수 있다** — 대량 변경에서 결과를 한 번에 안 받는 방법이다.\
  **이 편에서는 던져 보지 않았다.**
- **다른 엔진의 대응물** — SQL Server 의 `OUTPUT`, Oracle 의 `RETURNING INTO`, MariaDB 의 `RETURNING`.\
  **이 머신에 그 엔진들이 없어 확인하지 않았다.** 이 편의 결론은 **PG 18.6 과 MySQL 8.4.10 에 한정**한다.
