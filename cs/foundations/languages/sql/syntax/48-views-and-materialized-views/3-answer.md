# sql/48-뷰와 구체화 뷰 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> **이 편이 만든 객체** — `t48_emp`·`t48_high_snap`·`v48_high`·`v48_high_chk`·`v48_agg`·`v48_star`·`mv48_high`.\
> PG 는 `BEGIN … ROLLBACK` 으로 감쌌고 MySQL 은 `DROP VIEW`/`DROP TABLE` 로 지웠다. **`emp`·`dept` 는 안 건드렸다.**\
> 문서 근거는 [PG 18 CREATE VIEW](https://www.postgresql.org/docs/18/sql-createview.html) · [PG 18 CREATE MATERIALIZED VIEW](https://www.postgresql.org/docs/18/sql-creatematerializedview.html) · [MySQL 8.4 View Updatability](https://dev.mysql.com/doc/refman/8.4/en/view-updatability.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 뷰는 결과가 아니라 질의를 저장한다

**출력**

```text
### SQL: SELECT pg_get_viewdef('v48_high', true);
--- PG 18.6 ---
     pg_get_viewdef
------------------------
  SELECT id,           +
     name,             +
     salary            +
    FROM t48_emp       +
   WHERE salary >= 400;
(1 row)
```

```text
### SQL: SHOW CREATE VIEW v48_high\G
--- MySQL 8.4.10 ---
*************************** 1. row ***************************
                View: v48_high
         Create View: CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v48_high` AS select `t48_emp`.`id` AS `id`,`t48_emp`.`name` AS `name`,`t48_emp`.`salary` AS `salary` from `t48_emp` where (`t48_emp`.`salary` >= 400)
character_set_client: latin1
collation_connection: latin1_swedish_ci
```

**왜 그런가** — 돌려준 것은 **문장**이다. 행이 아니다.

```text
CREATE VIEW  ->  카탈로그에 SELECT 문 하나가 들어간다 (행 0개)
SELECT FROM v ->  그 문장을 꺼내 바깥 질의에 펼쳐 넣고 기반 표를 그때 읽는다
```

성능에 뜻하는 바는 명확하다 — **뷰는 저장 공간을 거의 안 쓰고, 읽기 비용을 전혀 줄이지 않는다.**\
「느린 질의를 뷰로 감쌌더니 빨라지겠지」는 여기서 무너진다(15번).

---

### 2. 계획에 뷰 이름은 안 나온다

**출력**

```text
### SQL: EXPLAIN SELECT * FROM v48_p WHERE id = 2;
--- PG 18.6 ---
 Index Scan using emp_pkey on emp  (cost=0.15..8.17 rows=1 width=40)
   Index Cond: (id = 2)
   Filter: (salary >= 400)
```

**왜 그런가** — 엔진이 뷰를 **펼쳐 넣었기(인라인)** 때문이다. 계획에 남는 것은 실제로 읽는 표 `emp` 다.

```text
SELECT * FROM v48_p WHERE id = 2
        ↓ 뷰 정의를 그 자리에 펼친다
SELECT * FROM (SELECT id,name,salary FROM emp WHERE salary >= 400) WHERE id = 2
        ↓ 옵티마이저가 조건을 합친다
emp 의 기본키로 id=2 를 찾고, salary >= 400 을 Filter 로 남긴다
```

**바깥 조건이 안쪽으로 내려갔다** — `id = 2` 가 `Index Cond` 가 됐다. 뷰가 인덱스를 막지 않았다는 뜻이다.

MySQL 은 이 동작을 `ALGORITHM` 으로 고를 수 있고, **고르는 것에 따라 계획이 갈린다.**

```text
### SQL: EXPLAIN SELECT * FROM v48_m WHERE id = 2;     -- ALGORITHM=MERGE
--- MySQL 8.4.10 ---
| id | select_type | table | type  | key     | rows | Extra |
|  1 | SIMPLE      | emp   | const | PRIMARY |    1 | NULL  |

### SQL: EXPLAIN SELECT * FROM v48_t WHERE id = 2;     -- ALGORITHM=TEMPTABLE
--- MySQL 8.4.10 ---
| id | select_type | table      | type   | key     | rows | Extra |
|  1 | PRIMARY     | <derived2> | system | NULL    |    1 | NULL  |
|  2 | DERIVED     | emp        | const  | PRIMARY |    1 | NULL  |
```

> **표 테두리를 지웠다.** MySQL `EXPLAIN` 의 12칸 표는 그대로 실으면 화면을 넘는다.
> `partitions`·`possible_keys`·`key_len`·`ref`·`filtered` 칸과 `+---+` 테두리만 지웠다.

`TEMPTABLE` 쪽은 뷰가 `<derived2>` 라는 **임시 결과**로 먼저 만들어진다. 계획이 두 줄이 된 것이 그 증거다.

---

### 3. 뷰는 2행, 구체화 뷰는 3행이다

**출력**

```text
### SQL: SELECT * FROM v48_high ORDER BY id;          -- (A) 뷰
--- PG 18.6 ---
 id | name | salary
----+------+--------
  2 | bob  |    500
  4 | dan  |    400
(2 rows)

### SQL: SELECT * FROM mv48_high ORDER BY id;         -- (B) 구체화 뷰
--- PG 18.6 ---
 id | name | salary
----+------+--------
  1 | ann  |    900
  2 | bob  |    500
  4 | dan  |    400
(3 rows)
```

**왜 그런가** — **같은 순간에 두 객체가 다른 답을 줬다.** 시간 순서를 그려 보면 이유가 하나다.

```text
t1  ann 의 salary = 900              v48_high: ann 보임        mv48_high: 아직 없음
t2  CREATE MATERIALIZED VIEW         v48_high: ann 보임        mv48_high: ann 900 을 저장
t3  ann 의 salary = 100              v48_high: ann 사라짐      mv48_high: ann 900 그대로  <- 낡음
t4  REFRESH MATERIALIZED VIEW        v48_high: 2행             mv48_high: 2행
```

```text
### SQL: REFRESH MATERIALIZED VIEW mv48_high;  SELECT * FROM mv48_high ORDER BY id;
--- PG 18.6 ---
REFRESH MATERIALIZED VIEW
 id | name | salary
----+------+--------
  2 | bob  |    500
  4 | dan  |    400
(2 rows)
```

구체화 뷰가 담고 있던 `ann | 900` 은 **t2 시점의 사진**이다. 그 사이 t3 가 일어났는데 사진은 안 바뀐다.\
★ **이것이 「저장된 결과」의 대가다** — 빠른 대신, 언제 찍은 사진인지를 사람이 관리해야 한다.

---

### 4. 구체화 뷰는 표가 아니다

**출력**

```text
### SQL: INSERT INTO mv48_high VALUES (9,'zed',999);
--- PG 18.6 ---
ERROR:  cannot change materialized view "mv48_high"
```

**왜 그런가** — 구체화 뷰의 내용은 **정의된 질의의 결과**다. 직접 행을 넣으면 그 질의와 어긋난 행이 생긴다.\
PG 는 그래서 `INSERT`·`UPDATE`·`DELETE` 를 통째로 막는다. 내용을 바꾸는 길은 `REFRESH` 하나뿐이다.

「구체화 뷰를 조금만 고쳐 쓰고 싶다」면 그것은 **표가 필요한 것**이다 — 구체화 뷰가 아니라 표를 만든다.

---

### 5. MySQL 은 `MATERIALIZED` 라는 낱말을 모른다

**출력**

```text
### SQL: CREATE MATERIALIZED VIEW mv48_high AS SELECT id FROM emp;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'MATERIALIZED VIEW mv48_high AS SELECT id FROM emp' at line 1

### SQL: REFRESH MATERIALIZED VIEW mv48_high;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'REFRESH MATERIALIZED VIEW mv48_high' at line 1
```

**왜 그런가** — `ERROR 1064` 는 **문법 오류**다. `42000` 은 문법·접근 규칙 위반을 뜻하는 SQLSTATE 다.

```text
 "지원하지 않습니다"                  실제로 받은 것
 +---------------------------+       +---------------------------+
 | 기능은 알지만 못 해 준다    |       | ERROR 1064 — 문법 오류     |
 |  (권한·버전·설정 문제)      |       | near 'MATERIALIZED VIEW …'|
 +---------------------------+       +---------------------------+
                                       파서가 낱말 자체를 모른다
```

`near '…'` 가 파서가 멈춘 지점이다. `CREATE` 다음에 `MATERIALIZED` 가 올 수 있는 낱말이 아니었다는 뜻이고,\
`REFRESH` 는 **문장 첫 낱말부터** 모른다. **「미지원」을 단정하기 전에 던져서 받은 답이 이것이다.**

---

### 6. 표 + 배치가 그 자리다

**출력** — 실제로 돌려 보면 낡음 현상까지 똑같이 재현된다.

```text
### SQL: CREATE TABLE t48_high_snap AS SELECT id, name, salary FROM t48_emp WHERE salary >= 400;
###      UPDATE t48_emp SET salary = 900 WHERE name='ann';
--- MySQL 8.4.10 · 뷰 v48_high ---        --- MySQL 8.4.10 · 스냅샷 표 t48_high_snap ---
+----+------+--------+                    +----+------+--------+
| id | name | salary |                    | id | name | salary |
+----+------+--------+                    +----+------+--------+
|  1 | ann  |    900 |                    |  2 | bob  |    500 |
|  2 | bob  |    500 |                    |  4 | dan  |    400 |
|  4 | dan  |    400 |                    +----+------+--------+
+----+------+--------+                      낡았다
```

```text
### SQL: TRUNCATE t48_high_snap;
###      INSERT INTO t48_high_snap SELECT id, name, salary FROM t48_emp WHERE salary >= 400;
--- MySQL 8.4.10 ---
+----+------+--------+
| id | name | salary |
+----+------+--------+
|  1 | ann  |    900 |
|  2 | bob  |    500 |
|  4 | dan  |    400 |
+----+------+--------+
```

**왜 그런가** — 구체화 뷰가 하는 일은 결국 「**질의 결과를 표에 담아 두고 가끔 다시 담기**」다.\
PG 가 그것을 한 문법으로 감싸 준 것뿐이고, MySQL 에서는 그 두 조각을 직접 쓴다.

| PostgreSQL | MySQL 8.4.10 | 무엇이 달라지나 |
|---|---|---|
| `CREATE MATERIALIZED VIEW` | `CREATE TABLE … AS SELECT …` | 없음 |
| `REFRESH MATERIALIZED VIEW` | `TRUNCATE` + `INSERT … SELECT …` | **그 틈에 읽는 사람은 빈 표를 본다** |
| 엔진이 「이건 구체화 뷰」라고 안다 | 그냥 표다 | 낡음을 **사람이** 관리한다 |
| 정의가 카탈로그에 남는다 | 남지 않는다 | 「이 표가 무슨 질의의 결과였나」를 잃는다 |

**빈 표 틈을 없애려면** 새 표를 따로 채운 뒤 `RENAME TABLE` 로 바꿔 끼우는 방식을 쓴다.\
*(이 편에서는 `RENAME TABLE` 방식을 돌려 보지 않았다 — 위 표의 두 줄만 실측이다.)*

---

### 7. 집계 뷰에는 못 넣는다 — PG 는 이유까지 말한다

**출력**

```text
### SQL: INSERT INTO v48_agg VALUES (30, 1);
--- PG 18.6 ---
ERROR:  cannot insert into view "v48_agg"
DETAIL:  Views containing GROUP BY are not automatically updatable.
HINT:  To enable inserting into the view, provide an INSTEAD OF INSERT trigger or an unconditional ON INSERT DO INSTEAD rule.
--- MySQL 8.4.10 ---
ERROR 1471 (HY000) at line 28: The target table v48_agg of the INSERT is not insertable-into
```

**왜 그런가** — 집계 뷰의 한 행은 **여러 원본 행에서 왔다.**

```text
 v48_agg 의 한 행                    t48_emp 의 원본 행
 +----------------+                 +--------------------------+
 | dept_id=10     |  <--- 어느 행?  | (1, ann, 10, 300)        |
 | cnt=2          |                 | (2, bob, 10, 500)        |
 +----------------+                 +--------------------------+
  (30, 1) 을 넣으라니 — 어떤 행을 몇 개 만들라는 말인가?
```

되짚을 원본 행이 정해지지 않으므로 엔진이 거부한다.

**두 에러의 성격이 다르다.**

- PG — `DETAIL` 이 **원인**(`GROUP BY`)을, `HINT` 가 **우회로**(`INSTEAD OF` 트리거)를 준다.
- MySQL — 「넣을 수 있는 대상이 아니다」라고만 한다. 이유는 매뉴얼에서 찾아야 한다.

★ **PG 의 `HINT` 는 경계도 그려 준다** — *자동* 갱신이 안 될 뿐, 트리거를 달면 넣을 수 있다.

---

### 8. `information_schema.views` 에 묻는다

**출력**

```text
### SQL: SELECT table_name, is_updatable, is_insertable_into FROM information_schema.views WHERE table_name LIKE 'v48%' ORDER BY table_name;
--- PG 18.6 ---
  table_name  | is_updatable | is_insertable_into
--------------+--------------+--------------------
 v48_agg      | NO           | NO
 v48_high     | YES          | YES
 v48_high_chk | YES          | YES
(3 rows)
--- MySQL 8.4.10 ---
+--------------+--------------+
| TABLE_NAME   | IS_UPDATABLE |
+--------------+--------------+
| v48_agg      | NO           |
| v48_high     | YES          |
| v48_high_chk | YES          |
+--------------+--------------+
```

**왜 그런가** — 갱신 가능 조건의 정확한 목록은 **엔진마다 다르고 버전마다 는다.** 외우면 틀린다.\
두 엔진 모두 `information_schema.views` 에 판정 결과를 이미 계산해 놓는다.

- PG 는 `is_updatable`(UPDATE/DELETE)과 `is_insertable_into`(INSERT)를 **나눠** 준다.
- MySQL 은 `IS_UPDATABLE` 하나다. 열 이름의 대소문자 표기도 다르다(PG 소문자 · MySQL 대문자).

「이 뷰에 넣어도 되나」가 궁금하면 **문서가 아니라 이 표에 묻는 것**이 이 주제의 실무 동작이다.

---

### 9. `INSERT` 는 성공하고, 뷰에서는 안 보인다

**출력**

```text
### SQL: INSERT INTO v48_high VALUES (6,'fox',100);
--- PG 18.6 ---
INSERT 0 1

### SQL: SELECT * FROM v48_high ORDER BY id;
--- PG 18.6 ---
 id | name | salary
----+------+--------
  2 | bob  |    500
  4 | dan  |    400
  5 | eve  |    700
(3 rows)

### SQL: SELECT id,name,salary FROM t48_emp WHERE id=6;
--- PG 18.6 ---
 id | name | salary
----+------+--------
  6 | fox  |    100
(1 row)
```

**왜 그런가** — 뷰는 **쓰기 통로일 뿐 필터가 아니다.** 들어간 곳은 `t48_emp` 이고, 뷰의 `WHERE` 는 **읽을 때** 적용된다.

```text
INSERT INTO v48_high VALUES (6,'fox',100)
        ↓ 뷰를 통과해 기반 표로
t48_emp 에 (6, fox, NULL, 100) 이 들어간다      <- 성공
        ↓ 나중에 읽을 때
SELECT * FROM v48_high  ->  WHERE salary >= 400 를 적용  ->  fox 탈락
```

**무엇이 조용한가** — 세 가지가 전부 조용하다.

1. `INSERT 0 1` — 엔진은 **성공이라고 답한다.**
2. 뷰를 읽으면 **없다** — 애플리케이션이 「안 들어갔나?」 하고 한 번 더 넣는다.
3. 기반 표에는 **있다** — 중복 행이 쌓이고, 그 행은 아무 화면에도 안 보인다.

★ 이 편에서 가장 위험한 동작이 이것이다. **에러가 없다.**

---

### 10. `WITH CHECK OPTION` 은 둘 다 막는다

**출력**

```text
### SQL: INSERT INTO v48_high_chk VALUES (7,'gil',100);
--- PG 18.6 ---
ERROR:  new row violates check option for view "v48_high_chk"
DETAIL:  Failing row contains (7, gil, null, 100).
--- MySQL 8.4.10 ---
ERROR 1369 (HY000) at line 23: CHECK OPTION failed 'study.v48_high_chk'
```

```text
### SQL: UPDATE v48_high_chk SET salary = 10 WHERE id = 2;
--- PG 18.6 ---
ERROR:  new row violates check option for view "v48_high_chk"
DETAIL:  Failing row contains (2, bob, 10, 10).
```

**왜 그런가** — `WITH CHECK OPTION` 은 **들어가거나 바뀐 뒤의 행이 뷰의 `WHERE` 를 만족하는지** 검사한다.

```text
 INSERT (7,'gil',100)                UPDATE bob 의 salary 를 10 으로
 +---------------------------+       +---------------------------+
 | 새 행: salary = 100       |       | 바뀐 행: salary = 10       |
 | 뷰 조건: salary >= 400    |       | 뷰 조건: salary >= 400     |
 | -> 불만족 -> 거부          |       | -> 불만족 -> 거부           |
 +---------------------------+       +---------------------------+
   "안 보이는 행을 만들지 마라"        "보이던 행을 밀어내지 마라"
```

**두 방향을 다 막는다** — 없던 행이 안 보이게 들어오는 것도, 보이던 행이 밖으로 나가는 것도.

PG 의 `DETAIL` 은 **막힌 행의 전체 모습**을 보여 준다 — 뷰에 없는 `dept_id` 칸까지 나온다(`(2, bob, 10, 10)`).\
MySQL 은 뷰 이름만 알려 준다. 어느 행이 막혔는지는 직접 찾아야 한다.

- 만족하는 행은 그냥 들어간다 — `INSERT INTO v48_high_chk VALUES (7,'gil',800);` 은 통과했다.
- 수식어 `LOCAL` / `CASCADED` 는 **뷰 위에 뷰를 얹었을 때** 어느 층까지 검사할지를 정한다. 두 엔진 다 기본값은 `CASCADED` 다.

---

### 11. PG 는 막고, MySQL 은 통과시킨다

**출력**

```text
### SQL: DROP TABLE t48_emp;
--- PG 18.6 ---
ERROR:  cannot drop table t48_emp because other objects depend on it
DETAIL:  view v48_high depends on table t48_emp
materialized view mv48_high depends on table t48_emp
view v48_high_chk depends on table t48_emp
view v48_agg depends on table t48_emp
HINT:  Use DROP ... CASCADE to drop the dependent objects too.
--- MySQL 8.4.10 ---
(아무 출력 없음 — 성공했다)
```

`CASCADE` 를 붙이면 PG 도 지우는데, **무엇을 함께 지웠는지 말해 준다.**

```text
### SQL: DROP TABLE t48_emp CASCADE;
--- PG 18.6 ---
NOTICE:  drop cascades to 4 other objects
DETAIL:  drop cascades to view v48_high
drop cascades to materialized view mv48_high
drop cascades to view v48_high_chk
drop cascades to view v48_agg
DROP TABLE
```

MySQL 에서는 표가 사라지고 **뷰만 남는다.** 그 뷰를 읽으면:

```text
### SQL: SELECT * FROM v48_agg;
--- MySQL 8.4.10 ---
ERROR 1356 (HY000) at line 43: View 'study.v48_agg' references invalid table(s) or column(s) or function(s) or definer/invoker of view lack rights to use them
```

**왜 그런가** — 두 엔진이 **의존 관계를 언제 검사하나**가 다르다.

```text
 PostgreSQL                            MySQL 8.4.10
 DDL 시점에 검사한다                    읽는 시점에 검사한다
 +-----------------------------+       +-----------------------------+
 | DROP TABLE -> ERROR         |       | DROP TABLE -> 성공          |
 | 뷰는 항상 읽힌다             |       | 배포는 초록불                |
 +-----------------------------+       +-----------------------------+
   스키마 변경이 번거롭다                 며칠 뒤 그 화면에서만 터진다
```

★ **MySQL 쪽이 조용하다.** 마이그레이션이 성공으로 기록되고, 깨진 것은 **그 뷰를 읽는 사람이** 발견한다.

---

### 12. `ALTER` 는 통과하고, `SELECT` 에서 터진다

**출력**

```text
### SQL: ALTER TABLE t48_emp DROP COLUMN salary;
--- PG 18.6 ---
ERROR:  cannot drop column salary of table t48_emp because other objects depend on it
DETAIL:  view v48_high depends on column salary of table t48_emp
materialized view mv48_high depends on column salary of table t48_emp
view v48_high_chk depends on column salary of table t48_emp
HINT:  Use DROP ... CASCADE to drop the dependent objects too.
--- MySQL 8.4.10 ---
(아무 출력 없음 — 성공했다)

### SQL: SELECT * FROM v48_high;
--- MySQL 8.4.10 ---
ERROR 1356 (HY000) at line 1: View 'study.v48_high' references invalid table(s) or column(s) or function(s) or definer/invoker of view lack rights to use them
```

**왜 그런가** — 11번과 같은 구조가 **열 단위**에서도 그대로다. PG 는 열 하나에도 의존을 건다.

**MySQL 에서는 깨진 뷰를 미리 찾을 수 있다.**

```text
### SQL: CHECK TABLE v48_high;
--- MySQL 8.4.10 ---
| Table          | Op    | Msg_type | Msg_text                                                          |
| study.v48_high | check | Error    | View 'study.v48_high' references invalid table(s) or column(s) … |
| study.v48_high | check | error    | Corrupt                                                           |
```

> **표 테두리를 지웠다.** `Msg_text` 칸이 길어 테두리째 실으면 화면을 넘는다.
> `+---+` 테두리를 지우고 `Msg_text` 뒷부분을 `…` 로 줄였다 — 전문은 위 `ERROR 1356` 과 같은 문장이다.

`Msg_type` 이 `Error`, 판정이 **`Corrupt`** 다. 스키마를 바꾼 뒤 **모든 뷰에 `CHECK TABLE` 을 돌리는 것**이 MySQL 쪽 방어선이다.\
PG 에는 이 점검이 필요 없다 — 깨질 수 있는 시점에 이미 막혔다.

---

### 13. `memo` 는 안 보인다 — `*` 는 만들 때 펼쳐진다

**출력**

```text
### SQL: SELECT pg_get_viewdef('v48_star', true);
--- PG 18.6 ---
  SELECT id,
     name,
     dept_id,
     salary
    FROM t48_emp;

### SQL: SELECT * FROM v48_star ORDER BY id LIMIT 2;
--- PG 18.6 ---
 id | name | dept_id | salary
----+------+---------+--------
  1 | ann  |      10 |    300
  2 | bob  |      10 |    500
(2 rows)
```

```text
### SQL: SHOW CREATE VIEW v48_star\G
--- MySQL 8.4.10 ---
         Create View: CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v48_star` AS select `t48_emp`.`id` AS `id`,`t48_emp`.`name` AS `name`,`t48_emp`.`dept_id` AS `dept_id`,`t48_emp`.`salary` AS `salary` from `t48_emp`
```

**왜 그런가** — 저장된 정의에 **`*` 가 없다.** 네 열 이름이 적혀 있다.

```text
CREATE VIEW v48_star AS SELECT * FROM t48_emp     (그때 열은 4개)
        ↓ 엔진이 * 를 그 자리에서 펼쳐 저장한다
저장된 것: SELECT id, name, dept_id, salary FROM t48_emp
        ↓
ALTER TABLE t48_emp ADD COLUMN memo text          (열이 5개가 됐다)
        ↓
뷰는 여전히 네 열 — 정의에 memo 가 없으니까
```

**양쪽 엔진에서 같았다.** 고치려면 뷰를 다시 만든다 — PG·MySQL 모두 `CREATE OR REPLACE VIEW v48_star AS SELECT * FROM t48_emp;`.

「뷰가 새 열을 안 보여 준다」는 신고의 정체가 대개 이것이고, **열 이름을 명시해 뷰를 만들면** 이 혼란 자체가 안 생긴다.

---

### 14. 고유 인덱스가 있어야 한다

**출력**

```text
### SQL: REFRESH MATERIALIZED VIEW CONCURRENTLY mv48_high;
--- PG 18.6 ---
ERROR:  cannot refresh materialized view "public.mv48_high" concurrently
HINT:  Create a unique index with no WHERE clause on one or more columns of the materialized view.
```

**왜 그런가** — `CONCURRENTLY` 는 **통째로 갈아 끼우지 않고 달라진 행만 바꿔 넣는다.** 그러려면 어느 행이 어느 행인지 짚을 수 있어야 한다.

```text
 기본 REFRESH                          REFRESH CONCURRENTLY
 +-----------------------------+      +-----------------------------+
 | 결과를 새로 만들어 통째 교체  |      | 새 결과와 옛 결과를 비교      |
 | 그동안 읽기까지 막힌다        |      | 달라진 행만 갱신              |
 | 행을 짚을 필요가 없다         |      | -> 행을 짚을 키가 필요하다     |
 +-----------------------------+      +-----------------------------+
```

**에러의 `HINT` 가 조건을 그대로 말해 준다** — `WHERE` 없는 고유 인덱스를 구체화 뷰 위에 만들면 된다.\
예: `CREATE UNIQUE INDEX ON mv48_high (id);` *(이 편에서는 인덱스를 만들어 다시 돌려 보지 않았다 — 위 에러까지가 실측이다.)*

`CONCURRENTLY` 는 공짜가 아니다 — 비교 때문에 기본 `REFRESH` 보다 느리다. 읽기를 막지 않는 대가다.

---

### 15. 안 빨라진다 — 뷰의 값어치는 이름이다

**왜 그런가** — 1번과 2번이 이미 답했다.

```text
저장된 것: 질의문                    읽을 때: 그 질의를 다시 돈다
        ↓                                   ↓
디스크를 거의 안 쓴다                  비용은 원래 질의 그대로
```

2번의 계획에서 뷰 이름이 사라진 것이 결정적 증거다 — 엔진이 보는 것은 **펼쳐진 원래 질의**이고, 그 질의의 비용을 그대로 낸다.

| | 뷰 | 구체화 뷰 |
|---|---|---|
| 저장 | 질의문 | 결과 행 |
| 읽기 비용 | **원 질의 그대로** | 저장된 행을 읽는 비용 |
| 최신성 | 항상 최신 | **낡는다** |
| 디스크 | 거의 0 | 결과 크기만큼 |
| 바꾸기 | 갱신 가능한 뷰면 가능 | **불가** — `REFRESH` 만 |

**그래서 뷰의 값어치는 세 가지다.**

```text
1. 이름   — 복잡한 조인에 이름을 붙여 호출부를 읽히게 만든다
2. 경계   — 「이 화면이 보는 데이터는 이것」이라는 계약을 한 곳에 둔다
3. 권한   — 민감한 열을 뺀 뷰만 내어 준다 (열 단위 접근 제어)
```

**속도가 목적이면 뷰가 아니라 인덱스([46 인덱스 정의](../46-index-definition-composite-partial-expression/) · [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/))나 구체화 뷰를 본다.**\
어느 연산자가 뽑혀서 느린지는 [59번](../59-scan-join-sort-operators/)에서, 추정이 틀려서 느린지는 [60번](../60-explain-analyze-estimates-vs-actuals/)에서 가른다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 뷰 정의 되읽기 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `pg_get_viewdef` · `SHOW CREATE VIEW` |
| ★ 뷰의 계획 (2번) | PG 18.6 · MySQL 8.4.10 | **각 2회** | **제출 직전 재확인 포함** · `ALGORITHM` 두 종 |
| ★ 뷰 대 구체화 뷰 (3번) | PG 18.6 | 2회 | `REFRESH` 전/후 |
| 구체화 뷰에 INSERT (4번) | PG 18.6 | 1회 | **에러가 근거** |
| ★ MySQL 구체화 뷰 (5번) | MySQL 8.4.10 | 2회 | **`ERROR 1064` 두 문장이 근거** |
| 표 + 배치 대체 (6번) | MySQL 8.4.10 | 1회 | `TRUNCATE` + `INSERT … SELECT` |
| 집계 뷰 INSERT (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **양쪽 에러가 근거** |
| 카탈로그 조회 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `information_schema.views` |
| ★ CHECK OPTION 없는 INSERT (9번) | PG 18.6 | 1회 | **에러가 안 난다는 것이 근거** |
| ★ WITH CHECK OPTION (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | INSERT · UPDATE 두 방향 |
| ★ 기반 표 DROP (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **양쪽이 갈린 자리** · `CASCADE` 포함 |
| ★ 열 DROP 뒤 조회 (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `CHECK TABLE` 로 `Corrupt` 확인 |
| `SELECT *` 뷰 (13번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 양쪽 같았다 |
| `REFRESH CONCURRENTLY` (14번) | PG 18.6 | 1회 | **`HINT` 가 조건을 준다** |
| 뒷정리 확인 | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\dtvm` · `SHOW FULL TABLES` |

**구현 의존 항목** — 2번의 계획이다. 뷰가 인라인되는 것도, MySQL 의 `UNDEFINED` 가 어느 알고리즘을 고르는 것도\
**옵티마이저의 선택**이지 보장이 아니다. 계획을 근거로 쓸 때는 시간이 아니라 **노드 이름과 `Index Cond`** 를 본다.\
★ **2번의 두 계획은 제출 직전에 다시 찍어 대조했고, PG·MySQL 모두 한 글자도 달라지지 않았다.**

**언어 보장 항목** — 1·3·4·5·7·9·10·11·12·13·14번. 「뷰가 질의를 저장한다」·「구체화 뷰가 낡는다」·\
「`*` 가 생성 시점에 펼쳐진다」·「`WITH CHECK OPTION` 이 양방향을 막는다」는 두 엔진에서 같았고, 문서에도 그렇게 적혀 있다.\
**엔진 차이**는 5·11·12번(구체화 뷰의 존재, DDL 의존 검사 시점)이고, 그 차이는 **양쪽 출력으로 고정**했다.

**한쪽에서만 결론이 서는 실험** — 3·4·14번은 **PG 에서만** 돌렸다. MySQL 에 구체화 뷰가 없어서(5번) 던질 문장 자체가 없다.\
이 셋의 근거는 **PG 출력뿐**이고, MySQL 쪽의 대응물은 6번의 「표 + 배치」다.

**버전** — 구체화 뷰는 PG 9.3 부터, `WITH CHECK OPTION` 은 두 엔진에 오래 있었고 매뉴얼에 도입 버전이 없어 적지 않는다.\
MySQL 에 구체화 뷰가 생기면 **5·6·11·12번**을 다시 돌린다.
