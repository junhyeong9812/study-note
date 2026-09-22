# sql/54-RETURNING 과 변경문을 품은 CTE — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **한쪽에서만 결론이 서는 주제다.** MySQL 쪽 출력은 **`ERROR 1064` 세 개와 「읽기 CTE 는 된다」는 통과 하나**뿐이고,\
> 동작 근거는 전부 **PostgreSQL 18.6** 이다.\
> **버전** — `OLD`/`NEW` 별칭은 **PG 18 부터**다([18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)).\
> 이 편이 만든 표(`t54_a`·`t54_log`)는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> ★ **이 파일 끝에 DML 묶음 다섯 편(49·50·51·53·54)의 최종 뒷정리 출력**이 있다.\
> 문서 근거는 [PG 18 RETURNING](https://www.postgresql.org/docs/18/dml-returning.html) · [PG 18 WITH Queries](https://www.postgresql.org/docs/18/queries-with.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `RETURNING` 이 붙는 문 — **PG 는 셋 다 / MySQL 은 셋 다 `ERROR 1064`**

**출력**

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

**왜 그런가** — `RETURNING` 은 변경문에 **결과 집합을 붙이는** 절이다.\
그 행은 **다시 읽은 것이 아니라 그 문이 실제로 건드린 행**이라, 그 사이 다른 세션이 끼어들 틈이 없다.

`SELECT` 목록처럼 식·상수·`*` 도 쓸 수 있다.

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

`MERGE` 에도 붙는다 — **PG 17 부터**다([53 번 9절](../53-merge/)).

---

### 2. 별칭 없는 열 — **`INSERT`/`UPDATE` 는 뒤 값, `DELETE` 는 앞 값**

**출력** (1번의 것을 다시 읽는다)

```text
UPDATE t54_a SET qty = qty + 1 WHERE id <= 2 RETURNING id, name, qty;
 id | name | qty 
----+------+-----
  1 | ann  |  11        <- 10 + 1. ★ 더한 뒤 값이다
  2 | bob  |  21        <- 20 + 1

DELETE FROM t54_a WHERE id = 5 RETURNING id, name, qty;
 id | name | qty 
----+------+-----
  5 | eve  |  50        <- ★ 지우기 전 값이다 (지운 뒤에는 행이 없다)
```

**왜 그런가 — 문마다 「자연스러운 쪽」이 다르다.**

```text
INSERT  넣기 전에는 행이 없다   -> 뒤 값 (기본값·생성 열·자동 증가가 채워진 것)
UPDATE  둘 다 있다             -> 뒤 값 (기본값)
DELETE  지운 뒤에는 행이 없다   -> 앞 값
```

★ **PG 18 릴리스 노트가 이 규칙을 「이전 동작」으로 적어 두었다** — 3번을 보라.

---

### 3. ★ `OLD` 와 `NEW` — **한쪽이 없는 문에서는 `NULL` 이다. PG 18 부터**

**출력**

```text
### SQL: UPDATE t54_a SET qty = qty*2 WHERE id <= 2 RETURNING id, OLD.qty AS before, NEW.qty AS after;
--- PG 18.6 ---
 id | before | after 
----+--------+-------
  1 |     10 |    20
  2 |     20 |    40
(2 rows)
UPDATE 2

### SQL: INSERT INTO t54_a VALUES (9,'new',90) RETURNING id, OLD.qty AS before, NEW.qty AS after;
--- PG 18.6 ---
 id | before | after 
----+--------+-------
  9 |        |    90        <- OLD 가 NULL
(1 row)
INSERT 0 1

### SQL: DELETE FROM t54_a WHERE id=4 RETURNING id, OLD.qty AS before, NEW.qty AS after;
--- PG 18.6 ---
 id | before | after 
----+--------+-------
  4 |     40 |              <- NEW 가 NULL
(1 row)
DELETE 1
```

**왜 그런가**

```text
              OLD            NEW
INSERT        NULL           넣은 행
UPDATE        고치기 전       고친 뒤
DELETE        지우기 전       NULL
```

**버전 — PG 18 부터다.**

> "Add `OLD`/`NEW` support to `RETURNING` in DML queries (Dean Rasheed) … **Previously `RETURNING` only returned new values for INSERT and UPDATE, and old values for DELETE**; `MERGE` would return the appropriate value for the internal query executed. This new syntax allows the `RETURNING` list of `INSERT`/`UPDATE`/`DELETE`/`MERGE` to explicitly return old and new values by using the special aliases `old` and `new`. These aliases can be renamed to avoid identifier conflicts."\
> — [PostgreSQL 18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)

★ **PG 17 이하에서는 이 문법을 못 쓴다.**\
**이 머신에 PG 17 이하 컨테이너가 없어 그 거부는 직접 재현하지 못했다** — 근거는 릴리스 노트다.

★ **이것으로 변경 이력을 트리거 없이 한 문에 남길 수 있다** — 감사 로그의 가장 싼 형태다.

---

### 4. 변경문을 `FROM` 에 놓으면 — **둘 다 에러. 둘째 에러가 규칙을 말해 준다**

**출력**

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

**왜 그런가**

```text
변경문을 놓을 수 있는 자리
  FROM 안에 직접          -> ★ 안 된다 (파서가 DELETE 를 거기서 기대하지 않는다)
  최상위 WITH 의 조각      -> ★ 된다
  서브쿼리 안의 WITH       -> ★ 안 된다 (must be at the top level)
```

★ **둘째 에러 문구가 규칙 자체다.** 왜 이렇게 제한했는지는 6번(스냅숏)과 이어진다 —\
서브쿼리 안이면 **그 변경문이 몇 번 도는지**가 바깥 질의의 형태에 달리게 된다.

---

### 5. ★★ 같은 문 안에서 세면 — **4 · 2 · 2. 문이 끝난 뒤에는 2행**

**출력**

```text
--- PG 18.6 ---
BEGIN;
SELECT count(*) AS a_before FROM t54_a;
 a_before 
----------
        4
(1 row)

WITH moved AS (DELETE FROM t54_a WHERE qty >= 30 RETURNING *),
     ins   AS (INSERT INTO t54_log SELECT id, name, qty, 'moved' FROM moved RETURNING *)
SELECT (SELECT count(*) FROM t54_a)   AS a_seen_in_same_stmt,
       (SELECT count(*) FROM moved)   AS moved_rows,
       (SELECT count(*) FROM ins)     AS logged_rows;
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

**왜 그런가 — 세 숫자를 나란히 읽는다.**

```text
a_before             = 4     문 이전
a_seen_in_same_stmt  = 4     ★ 같은 문 안에서 센 값 — 두 행을 지우는 중인데도 4다
moved_rows           = 2     DELETE ... RETURNING 이 실제로 건드린 행
logged_rows          = 2     INSERT ... RETURNING 이 실제로 넣은 행
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

★ **`moved` 와 `ins` 만이 「새 정보」다.** 그 둘은 `RETURNING` 이 돌려준 행이라\
**변경문 자신이 무엇을 했는지**를 말한다. 표를 직접 세는 조각(`SELECT count(*) FROM t54_a`)은 **옛 상태**다.

★ **「지우면서 다른 표에 넣기」는 한 문이므로 원자적이다.** 「지웠는데 못 넣은」 상태가 안 생긴다.

---

### 6. 왜 그런가 — **모든 조각이 같은 스냅숏을 본다(문서)**

> "The sub-statements in `WITH` are executed concurrently with each other and with the main query. Therefore, **when using data-modifying statements in `WITH`, the order in which the specified updates actually happen is unpredictable.** All the statements are executed with the same _snapshot_ (see Chapter 13), so **they cannot "see" one another's effects on the target tables.**"\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

**설계 이유를 그 문장에서 읽는다.**

```text
① "실행 순서가 예측 불가하다"
      WITH a AS (DELETE ...), b AS (UPDATE ...) SELECT ...
      -> 누가 먼저 도는지 정해져 있지 않다

② 그런데 서로의 결과가 보이면?
      -> 답이 실행 순서에 따라 달라진다. 같은 문이 판마다 다른 값을 낸다

③ 그래서 아예 안 보이게 한다
      -> ★ 모두 같은 스냅숏을 본다 -> 순서와 무관하게 답이 하나로 고정된다
```

**그래서 「바꾼 뒤 남은 개수」는 같은 문에서 셀 수 없다.** 문을 나눠야 한다.

★ 같은 성질을 [49 번 11절](../49-insert-multi-row-and-insert-select/)이 더 작은 규모로 보여 준다 —\
`INSERT INTO t SELECT … FROM t` 가 3행짜리 표에서 3행만 넣고 멈춘 것이 **같은 스냅숏 규칙**이다.

---

### 7. 두 번 참조하면 — **`c1=1, c2=1`. 한 행만 지워진다**

**출력**

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
         3
(1 row)
ROLLBACK;
```

**왜 그런가** — 문서가 한 문장으로 답한다.

> "Data-modifying statements in `WITH` are **executed exactly once, and always to completion**, independently of whether the primary query reads all (or indeed any) of their output."\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

```text
"exactly once"  -> 두 번 참조해도 DELETE 는 한 번
                   c1 과 c2 는 "그 한 번의 결과" 를 둘 다 읽은 것이다
remaining = 3   -> 4행 중 하나만 지워졌다
```

---

### 8. ★ 아무도 안 읽으면 — **그래도 지워진다**

**출력**

```text
--- PG 18.6 ---
BEGIN;
WITH gone AS (DELETE FROM t54_a WHERE id=4 RETURNING *)
SELECT 1 AS dummy;
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
(3 rows)                   <- ★ id=4 가 지워졌다
ROLLBACK;
```

**왜 그런가** — 7번과 같은 문장의 뒷부분이다.

> "… **always to completion, independently of whether the primary query reads all (or indeed any) of their output.**"

★ **「안 쓰니까 안 돌겠지」가 틀린 자리다.** `WITH` 에 적어 두면 **돈다.**\
읽기 전용 CTE 는 안 쓰면 계획에서 사라질 수 있지만, 변경 CTE 는 다르다 — 9번이 그 설명이다.

---

### 9. [32 번](../32-cte-with-clause/)의 인라인 규칙과의 관계 — **적용되지 않는다**

**왜 그런가** — 인라인 조건에 「부작용 없음」이 들어 있다.

> "if a `WITH` query is non-recursive and **side-effect-free** (that is, it is a `SELECT` containing no volatile functions) then it can be folded into the parent query… By default, this happens if the parent query references the `WITH` query just once, but not if it references the `WITH` query more than once."\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

```text
읽기 전용 CTE   참조 1회 -> 인라인될 수 있다 (바깥 질의에 접힌다)
                참조 2회 -> PG 는 벽을 세운다 (한 번 평가하고 재사용)
                ★ "몇 번 평가되나" 가 참조 횟수에 달렸다

변경 CTE        ★ side-effect-free 가 아니다 -> 인라인 후보가 아니다
                ★ 참조 횟수와 무관하게 정확히 한 번, 끝까지 실행된다
```

★ **두 규칙이 정반대 방향으로 보이지만 근거는 같은 문단이다.**\
「접을 수 있는가」를 묻는 것이 읽기 CTE 의 규칙이고, **접을 수 없는 것에는 「정확히 한 번」이라는 별도 보장**이 붙는다.\
`MATERIALIZED`/`NOT MATERIALIZED` 와 인라인 실측은 [32 번](../32-cte-with-clause/)이 정본이다.

---

### 10. 같은 행을 두 조각이 — **하나만 먹는다. 기대하면 안 된다**

**출력**

```text
--- PG 18.6 ---
BEGIN;
WITH u1 AS (UPDATE t54_a SET qty = 100 WHERE id=1 RETURNING id),
     u2 AS (UPDATE t54_a SET qty = 200 WHERE id=1 RETURNING id)
SELECT (SELECT count(*) FROM u1) AS u1_rows, (SELECT count(*) FROM u2) AS u2_rows;
 u1_rows | u2_rows 
---------+---------
       1 |       0
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

**왜 그런가** — 문서가 직접 적는다.

> "**Trying to update the same row twice in a single statement is not supported. Only one of the modifications takes place, but it is not easy (and sometimes not possible) to reliably predict which one.**"\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

★ **세 판을 돌려 봤고 모두 `u1` 이 이겼다.**

```text
판 1:  u1_rows=1 · u2_rows=0 · qty=100
판 2:  u1_rows=1 · u2_rows=0 · qty=100
판 3:  u1_rows=1 · u2_rows=0 · qty=100
```

★★ **그런데도 기대하면 안 된다.** 문서가 「신뢰할 수 있게 예측하기 쉽지 않고 때로는 불가능하다」고 적었다.\
**반복 실행이 같았다는 사실은 보장의 근거가 아니라 오히려 더 위험한 근거**다\
([작성법 §2-1](../../../../../../reference/study-note-guide.md)의 「같은 값이 나와 보장된다고 오해한다」).

★ **에러가 아니라는 점이 이 자리의 위험이다.**

```text
같은 행을 한 문에서 두 번 건드렸을 때

MERGE                  -> ★ ERROR: cannot affect row a second time   (53번)
INSERT ... ON CONFLICT -> ★ ERROR: cannot affect row a second time   (52번)
변경 CTE 두 조각       -> ★ 에러 없음. 조용히 하나만 적용된다
```

**처방** — 한 문 안에서 같은 표의 같은 행을 두 조각이 건드리지 않도록 설계한다.

---

### 11. MySQL 에 무엇이 있고 무엇이 없나 — **(a) 없다 / (b) 있다**

**출력**

```text
### SQL: WITH moved AS (DELETE FROM t54_a WHERE qty >= 30 RETURNING *) SELECT * FROM moved;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'DELETE FROM t54_a WHERE qty >= 30 RETURNING *) SELECT * FROM moved' at line 1

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

**왜 그런가 — 「CTE 가 없는 것」이 아니라 「CTE 안에 변경문을 못 넣는 것」이다.**

```text
MySQL 8.4.10
  WITH 자체                  -> ★ 있다 (8.0 부터. 32번)
  변경문 앞에 읽기 CTE        -> ★ 된다  (위 (b))
  CTE 안에 변경문             -> ★ 없다  (ERROR 1064)
  RETURNING                  -> ★ 없다  (ERROR 1064, 1번)
```

★ **(b) 가 통과한 것이 중요하다.** 「MySQL 에는 CTE 를 DML 에 못 쓴다」는 **틀린 요약**이다 —\
못 쓰는 것은 **CTE 안의 변경문**이다.

---

### 12. MySQL 에서 「옮기기」 — **문 둘. 복사를 먼저, 삭제를 나중에**

```sql
START TRANSACTION;
INSERT INTO t54_log SELECT id, name, qty, 'moved' FROM t54_a WHERE qty >= 30;   -- ① 먼저 복사
DELETE FROM t54_a WHERE qty >= 30;                                               -- ② 그 다음 삭제
COMMIT;
```

**왜 그런가**

```text
순서를 바꾸면 ( ② 먼저 )
  DELETE 로 행이 사라진다 -> INSERT ... SELECT 가 읽을 행이 0개 -> 조용히 0행 적재
  ★ 에러가 안 난다 (49번 10절의 INSERT 0 0)

문이 둘이면 스냅숏도 둘이다
  PG 의 한 문 판은 두 조각이 같은 스냅숏을 보므로 순서 고민 자체가 없다 (5번)
```

★ **조건(`qty >= 30`)이 두 문에 두 번 적힌다.**\
그 사이에 조건에 걸리는 행이 새로 들어오면 **`DELETE` 는 지우는데 `INSERT` 는 못 복사한 행**이 생긴다.\
격리 수준이 그것을 막는지는 [56 격리 수준](../56-isolation-levels-read-phenomena-mvcc/) 주제이고,\
★ **이 경쟁 상황은 이 편에서 재현하지 않았다** — 동시 세션 실험을 하지 않았다.

**한 문 판과 두 문 판의 차이**

```text
PG (한 문)                              MySQL (두 문 + 트랜잭션)
+-----------------------------+         +-----------------------------+
| 조건을 한 번 적는다          |         | 조건을 두 번 적는다          |
| 순서 고민이 없다             |         | ★ 순서를 틀리면 조용히 0행   |
| 같은 스냅숏이 보장된다       |         | 격리 수준에 달린다           |
+-----------------------------+         +-----------------------------+
```

---

### 13. 자동 생성 키 회수 — **`LAST_INSERT_ID()`. 동등물이 아니다**

```text
PG    : INSERT INTO t (...) VALUES (...), (...) RETURNING id;
        -> 들어간 행의 id 를 ★ 전부, 실제 값으로 돌려준다

MySQL : INSERT INTO t (...) VALUES (...), (...);
        SELECT LAST_INSERT_ID();
        -> ★ 배치의 "첫" 번호 하나만
```

[49 번 12절](../49-insert-multi-row-and-insert-select/)의 실측이 그 근거다.

```text
### SQL: INSERT INTO t49_ai (v) VALUES ('d'),('e'); SELECT LAST_INSERT_ID() AS last_id;
--- MySQL 8.4.10 ---
+---------+
| last_id |
+---------+
|       4 |      <- 'd' 가 4, 'e' 가 5 인데 4 만 준다
+---------+
```

**왜 동등물이 아닌가 — 셋이 다르다.**

```text
① 개수   : RETURNING 은 모든 행, LAST_INSERT_ID() 는 하나
② 정확성 : 나머지 번호는 "첫 번호 + ROW_COUNT() - 1" 로 ★ 계산해야 한다 (추정이다)
③ 범위   : RETURNING 은 id 말고 다른 열·식도 준다 (기본값·생성 열이 채운 값까지)
```

★ **게다가 `LAST_INSERT_ID()` 는 `INSERT` 에만 있다.**\
`UPDATE`·`DELETE` 가 무엇을 건드렸는지 돌려받는 수단은 MySQL 8.4.10 에 **없다** — 다시 `SELECT` 해야 한다.

---

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 표 2개 생성·삭제 | PG 18.6 · MySQL 8.4.10 | 각 2회 | `t54_a`·`t54_log` |
| `RETURNING` 세 문 (1번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **MySQL 은 셋 다 `ERROR 1064`** |
| `RETURNING` 에 식·`*` (1번) | PG 18.6 | 2회 | `qty/2`·`'done'`·`*` |
| 앞 값 / 뒤 값 (2번) | PG 18.6 | (1번의 출력) | `UPDATE` 는 11·21, `DELETE` 는 50 |
| ★ `OLD`/`NEW` 세 문 (3번) | PG 18.6 | 3회 | **`INSERT` 는 OLD 가, `DELETE` 는 NEW 가 `NULL`** |
| 변경문을 `FROM` 에 (4번) | PG 18.6 | 1회 | `syntax error at or near "FROM"` |
| 서브쿼리 안의 변경 CTE (4번) | PG 18.6 | 1회 | **`must be at the top level` — 에러 문구가 규칙이다** |
| ★★ 가시성 (5번) | PG 18.6 | **5회** | `a_before` → `WITH` 문 → `a_after` → 두 표 확인 |
| 두 번 참조 (7번) | PG 18.6 | 2회 | **`c1=1, c2=1`, 한 행만 삭제** |
| ★ 참조 안 해도 실행 (8번) | PG 18.6 | 2회 | **`id=4` 가 지워졌다** |
| 같은 행 두 조각 (10번) | PG 18.6 | **3판** | **세 판 다 `u1` 이 이겼다 — 그러나 문서는 「예측 불가」** |
| 삭제 대 갱신 충돌 (10번) | PG 18.6 | 2회 | `deleted=1, updated=0` |
| MySQL 의 변경 CTE (11번) | MySQL 8.4.10 | 1회 | `ERROR 1064` |
| ★ MySQL 의 읽기 CTE + `DELETE` (11번) | MySQL 8.4.10 | 2회 | **통과했다 — 「CTE 를 DML 에 못 쓴다」는 틀린 요약** |
| `LAST_INSERT_ID()` (13번) | MySQL 8.4.10 | (49편 12절) | **배치의 첫 번호** |

**실행으로 확인하지 않은 것 — 근거가 문서인 자리**

| 항목 | 근거 |
|---|---|
| 3번 **`OLD`/`NEW` 의 도입 버전** | [PG 18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/) — **PG 17 이하 컨테이너가 없다** |
| 6번 **같은 스냅숏인 이유** | [PG 18 WITH Queries](https://www.postgresql.org/docs/18/queries-with.html) — 관찰(5번)은 있고, 「왜」는 문서다 |
| 9번 **인라인 조건** | 〃 의 「side-effect-free」 문장 |
| 10번 **어느 쪽이 이기나** | 〃 의 「predict which one」 문장 — **관찰 3판은 근거가 아니다** |
| 12번 **두 문 사이의 경쟁** | 동시 세션 실험을 하지 않았다([56 격리 수준](../56-isolation-levels-read-phenomena-mvcc/)) |

**구현 의존 항목** — 1·11번의 **에러 번호**, 10번의 **실제로 어느 조각이 이기나**.\
외울 것은 문구가 아니라 **「같은 문의 조각들은 같은 스냅숏을 본다」**·「**변경 CTE 는 정확히 한 번 돈다**」는 성질이다.

**언어 보장 항목** — 5·6·7·8·9·10번.\
같은 스냅숏, 정확히 한 번·끝까지 실행, 인라인 조건, 같은 행 두 번의 결과는 **PG 문서가 문장으로 정한 것**이다.\
★ **MySQL 쪽에는 이 항목들에 대응하는 보장이 존재하지 않는다** — 문법 자체가 없다.

**버전을 적은 자리** — 3번(`OLD`/`NEW` = PG 18+) · `MERGE` 의 `RETURNING`(PG 17+, [53번](../53-merge/)).\
**버전을 못 적은 자리** — `RETURNING` 자체의 도입 버전(문서에 없어 적지 않는다) · MySQL 의 도입 예고(없다).

**돌려 보지 않은 것** — ① PG 17 이하에서의 `OLD`/`NEW` 거부 ② 트리거가 `RETURNING` 값을 바꾸는 경우\
③ 12번의 동시 세션 경쟁 ④ 커서로 `RETURNING` 읽기 ⑤ SQL Server `OUTPUT`·Oracle `RETURNING INTO`(엔진이 없다).

---

## ★ DML 묶음(49·50·51·53·54)의 최종 뒷정리

다섯 편이 만든 표는 **`t49_`·`t50_`·`t51_`·`t53_`·`t54_` 접두사**를 붙여 `study` DB 안에만 만들었고,\
제출 직전에 두 엔진에서 **전부 삭제**했다. 아래는 그 확인 출력이다.

```text
--- PG 18.6 ---
\dt
          List of tables
 Schema | Name | Type  |  Owner   
--------+------+-------+----------
 public | dept | table | postgres
 public | emp  | table | postgres
(2 rows)

SELECT count(*) AS emp_rows FROM emp;      SELECT count(*) AS dept_rows FROM dept;
 emp_rows                                   dept_rows 
----------                                 -----------
        4                                           3
(1 row)                                    (1 row)

SELECT * FROM emp ORDER BY id;             SELECT * FROM dept ORDER BY id;
 id | name | dept_id | salary               id | name  
----+------+---------+--------              ----+-------
  1 | ann  |      10 |    300                10 | sales
  2 | bob  |      10 |    500                20 | dev
  3 | cho  |      20 |                       30 | hr
  4 | dan  |         |    400               (3 rows)
(4 rows)
```

```text
--- MySQL 8.4.10 ---
SHOW TABLES;
+-----------------+
| Tables_in_study |
+-----------------+
| dept            |
| emp             |
+-----------------+

SELECT count(*) AS emp_rows FROM emp;    SELECT count(*) AS dept_rows FROM dept;
+----------+                             +-----------+
| emp_rows |                             | dept_rows |
+----------+                             +-----------+
|        4 |                             |         3 |
+----------+                             +-----------+

SELECT * FROM emp ORDER BY id;           SELECT * FROM dept ORDER BY id;
+----+------+---------+--------+         +----+-------+
| id | name | dept_id | salary |         | id | name  |
+----+------+---------+--------+         +----+-------+
|  1 | ann  |      10 |    300 |         | 10 | sales |
|  2 | bob  |      10 |    500 |         | 20 | dev   |
|  3 | cho  |      20 |   NULL |         | 30 | hr    |
|  4 | dan  |    NULL |    400 |         +----+-------+
+----+------+---------+--------+
```

**두 엔진에 `emp`(4행)·`dept`(3행) 만 남았고 내용도 처음 그대로다.**\
다섯 편의 모든 실험은 **자기 표에서만** 했다 — `emp`·`dept` 는 **읽지도 쓰지도 않았다.**

★ **삭제 방식** — PG 는 `DROP TABLE IF EXISTS … CASCADE` 한 문,\
MySQL 은 **DDL 이 암묵 커밋이라 롤백이 안 되므로**([51 번 2절](../51-delete-and-truncate/))\
`SET FOREIGN_KEY_CHECKS=0` → `DROP TABLE IF EXISTS …` → `SET FOREIGN_KEY_CHECKS=1` 로 직접 지웠다.
