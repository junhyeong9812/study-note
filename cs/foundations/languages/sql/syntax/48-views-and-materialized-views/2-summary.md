# sql/48-뷰와 구체화 뷰 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · CREATE VIEW](https://www.postgresql.org/docs/18/sql-createview.html) · [PostgreSQL 18 · CREATE MATERIALIZED VIEW](https://www.postgresql.org/docs/18/sql-creatematerializedview.html) · [MySQL 8.4 · CREATE VIEW](https://dev.mysql.com/doc/refman/8.4/en/create-view.html) · [MySQL 8.4 · Updatable and Insertable Views](https://dev.mysql.com/doc/refman/8.4/en/view-updatability.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **이 편이 만든 객체와 그 뒷정리** — 표 `t48_emp`·`t48_high_snap`, 뷰 `v48_high`·`v48_high_chk`·`v48_agg`·`v48_star`,
> 구체화 뷰 `mv48_high`. PG 는 전부 `BEGIN … ROLLBACK` 안에서 만들었고, MySQL 은 DDL 이 암묵 커밋이라
> `DROP VIEW` / `DROP TABLE` 로 직접 지웠다. **기존 `emp`·`dept` 는 한 글자도 바꾸지 않았다.**\
> **버전** — 구체화 뷰는 PG 9.3 부터 있고 **MySQL 8.4.10 에는 없다**(파서가 키워드를 모른다 — 2절에서 던져 본다).\
> **선행** — [32 CTE(WITH)](../32-cte-with-clause/) · [42 CREATE·ALTER·DROP TABLE](../42-create-alter-drop-table/). **두 폴더 모두 이 배치 작업 중에 생겨 링크로 전환했다.**

## 한눈에 — 쉽게 말하면

**뷰는 「저장된 질의」이고, 구체화 뷰는 「저장된 결과」다.**

- 요리책에 **레시피**를 적어 두는 것과 **도시락을 만들어 냉장고에 넣어 두는 것**의 차이다.
- 레시피는 부피가 0이다. 대신 **먹을 때마다 처음부터 요리해야 한다.**
- 도시락은 **꺼내면 바로 먹는다.** 대신 **냉장고 자리를 차지하고, 시간이 지나면 상한다** — 다시 만들어 넣어야 한다.
- 재료(=기반 표)가 바뀌었을 때 **레시피는 자동으로 새 재료를 쓰지만, 도시락 안의 재료는 어제 것 그대로**다.

| 비유 | 실체 |
|---|---|
| 레시피를 적어 둔 종이 | 뷰(`CREATE VIEW`) — 질의문만 저장 |
| 먹을 때마다 요리한다 | 뷰를 읽을 때마다 기반 표를 다시 돈다 |
| 만들어 둔 도시락 | 구체화 뷰(`CREATE MATERIALIZED VIEW`) — 결과 행을 저장 |
| 냉장고 자리 | 디스크 공간 |
| 도시락이 상한다 | 낡음(staleness) — 기반 표가 바뀌어도 안 따라온다 |
| 도시락을 새로 만들어 넣기 | `REFRESH MATERIALIZED VIEW` |

```text
 뷰 (저장된 질의)                        구체화 뷰 (저장된 결과)
 +----------------------------+         +----------------------------+
 | 저장된 것: SELECT … 문      |         | 저장된 것: 행 3개           |
 | 읽을 때: 기반 표를 다시 돈다 |         | 읽을 때: 저장된 행을 읽는다  |
 | 기반 표 UPDATE 후: 따라온다  |         | 기반 표 UPDATE 후: 안 따라온다|
 +----------------------------+         +----------------------------+
   항상 최신 · 매번 비용           빠름 · 낡을 수 있음 · REFRESH 필요
```

**똑같은 구조다** — 「어제 집계해 둔 일일 통계 표」가 구체화 뷰이고, 「볼 때마다 다시 세는 통계 화면」이 뷰다.\
실무에서 대시보드가 느리면 뷰를 구체화 뷰로 바꾸고, 대시보드가 틀리면 구체화 뷰의 `REFRESH` 를 의심한다.

> **뷰(view)** — 이름이 붙은 `SELECT` 문. 표처럼 읽히지만 **행을 저장하지 않는다.**\
> 예: `CREATE VIEW v AS SELECT id FROM emp WHERE salary >= 400;` 은 `SELECT` 문장만 카탈로그에 넣는다.

> **구체화 뷰(materialized view)** — 질의 **결과 행**을 실제로 저장해 두는 객체.\
> 예: `CREATE MATERIALIZED VIEW mv AS SELECT …;` 은 그 시점의 결과를 디스크에 쓴다. 이후 기반 표가 바뀌어도 그대로다.

## 이 주제가 답하려는 질문

1. **뷰를 읽을 때 엔진은 무엇을 하나** — 저장된 것이 결과가 아니라 질의라면, 비용은 어디로 가나.
2. **어떤 뷰에 `INSERT`/`UPDATE` 를 할 수 있나** — 그리고 넣은 행이 뷰에서 안 보이면 무슨 일이 생기나.
3. **구체화 뷰는 언제 낡나** — 그리고 구체화 뷰가 없는 엔진에서는 그 자리를 무엇이 메우나.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들이 **같은 두 표**를 쓴다.

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |  <- 사원이 없는 부서
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

이 편은 **뷰를 통해 행을 넣고 바꾸는 실험**을 하므로 `emp` 를 직접 쓰지 않는다.\
대신 **같은 4행을 담은 `t48_emp`** 를 만들어 거기에 뷰를 건다. `emp`·`dept` 는 건드리지 않는다.

```sql
CREATE TABLE t48_emp (id int PRIMARY KEY, name text, dept_id int, salary int);
INSERT INTO t48_emp VALUES (1,'ann',10,300),(2,'bob',10,500),(3,'cho',20,NULL),(4,'dan',NULL,400);
CREATE VIEW v48_high AS SELECT id, name, salary FROM t48_emp WHERE salary >= 400;
```

## 동작 방식

### 1. ★ 뷰가 저장하는 것은 결과가 아니라 질의다

**언제 쓰나** — 같은 `SELECT` 를 여러 곳에서 쓸 때. **읽을 때마다 그 `SELECT` 가 다시 돈다.**

```text
CREATE VIEW v48_high AS SELECT … WHERE salary >= 400
        ↓
카탈로그에 「문장」이 들어간다 (행은 0개 저장)
        ↓
SELECT * FROM v48_high  를 던지면
        ↓
엔진이 그 자리에 저장된 문장을 펼쳐 넣고 (인라인)
        ↓
t48_emp 를 그때 다시 읽는다
```

```text
### SQL: SELECT * FROM v48_high ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | salary              +----+------+--------+
----+------+--------             | id | name | salary |
  2 | bob  |    500              +----+------+--------+
  4 | dan  |    400              |  2 | bob  |    500 |
(2 rows)                         |  4 | dan  |    400 |
                                 +----+------+--------+
```

**저장된 것을 되읽어 보면 문장이 나온다.**

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

그림 해설 — 양쪽 다 **행이 아니라 문장**이 나왔다. MySQL 은 거기에 `ALGORITHM`·`DEFINER`·`SQL SECURITY` 까지 붙여 저장한다.\
비용 — 뷰 자체의 저장 비용은 문장 하나. **읽기 비용은 기반 질의 그대로**다. 뷰로 감쌌다고 빨라지지 않는다.

**계획을 찍어 보면 뷰 이름이 사라진다** — 엔진이 뷰를 펼쳐 넣었다는 증거다.

```text
### SQL: EXPLAIN SELECT * FROM v48_p WHERE id = 2;   -- v48_p 는 emp 위에 만든 같은 모양의 뷰
--- PG 18.6 ---
 Index Scan using emp_pkey on emp  (cost=0.15..8.17 rows=1 width=40)
   Index Cond: (id = 2)
   Filter: (salary >= 400)
```

**계획에 `v48_p` 가 없다.** `emp` 의 기본키 인덱스를 탔고, 뷰의 `WHERE` 는 `Filter` 로, 바깥의 `WHERE id = 2` 는 `Index Cond` 로 내려갔다.\
계획 트리를 읽는 법은 [58번](../58-explain-plan-tree/)에서 다룬다.

MySQL 은 이 「펼쳐 넣기」를 **`ALGORITHM`** 으로 고를 수 있다.

```text
### SQL: EXPLAIN SELECT * FROM v48_m WHERE id = 2;   -- ALGORITHM=MERGE
--- MySQL 8.4.10 ---
| id | select_type | table | type  | key     | rows | Extra |
|  1 | SIMPLE      | emp   | const | PRIMARY |    1 | NULL  |

### SQL: EXPLAIN SELECT * FROM v48_t WHERE id = 2;   -- ALGORITHM=TEMPTABLE
--- MySQL 8.4.10 ---
| id | select_type | table      | type   | key     | rows | Extra |
|  1 | PRIMARY     | <derived2> | system | NULL    |    1 | NULL  |
|  2 | DERIVED     | emp        | const  | PRIMARY |    1 | NULL  |
```

> **표 테두리를 지웠다.** MySQL 의 `EXPLAIN` 표는 12칸이라 그대로 실으면 화면을 넘는다.
> 위 두 블록은 실제 출력에서 `partitions`·`possible_keys`·`key_len`·`ref`·`filtered` 칸과 `+---+` 테두리만 지운 것이다.

그림 해설 — `MERGE` 는 PG 처럼 뷰를 펼쳐 넣어 `emp` 가 직접 보이고, `TEMPTABLE` 은 **뷰를 임시 표(`<derived2>`)로 먼저 만든 뒤** 거기서 조건을 건다.\
대가 — `TEMPTABLE` 은 바깥 조건이 안쪽으로 못 내려가므로 **인덱스를 놓칠 수 있다.** 기본값 `UNDEFINED` 는 엔진이 고른다.

---

### 2. ★ 구체화 뷰는 저장된 결과다 — 그래서 낡는다

**언제 쓰나** — 무거운 집계를 여러 번 읽을 때. **대가는 낡음이다.**

```text
 t48_emp 에서 ann 의 급여를 900 으로 올렸다
        ↓
 뷰 v48_high        구체화 뷰 mv48_high
 (질의를 다시 돈다)   (만들 때의 결과 그대로)
        ↓                   ↓
 ann 이 나타난다      ann 이 없다 (아직)
        ↓                   ↓
                     REFRESH MATERIALIZED VIEW
                            ↓
                     비로소 같아진다
```

`ann` 의 급여를 900 으로 올리고 **그 시점에 구체화 뷰를 만들었다.** 그 다음 `ann` 을 100 으로 내렸다.

```text
### SQL: SELECT * FROM v48_high ORDER BY id;          -- 뷰
--- PG 18.6 ---
 id | name | salary
----+------+--------
  2 | bob  |    500
  4 | dan  |    400
(2 rows)

### SQL: SELECT * FROM mv48_high ORDER BY id;         -- 구체화 뷰 (낡았다)
--- PG 18.6 ---
 id | name | salary
----+------+--------
  1 | ann  |    900      <- 이미 100 으로 바뀐 값
  2 | bob  |    500
  4 | dan  |    400
(3 rows)
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

그림 해설 — **같은 순간에 두 객체가 서로 다른 답을 줬다.** 뷰는 2행, 구체화 뷰는 3행이었다.\
비용 — 읽기는 싸지만 **`REFRESH` 는 질의를 통째로 다시 돈다.** 그동안 기본 `REFRESH` 는 **읽기까지 막는다**(배타 잠금).

읽기를 막지 않으려면 `CONCURRENTLY` 인데, **조건이 있다.**

```text
### SQL: REFRESH MATERIALIZED VIEW CONCURRENTLY mv48_high;
--- PG 18.6 ---
ERROR:  cannot refresh materialized view "public.mv48_high" concurrently
HINT:  Create a unique index with no WHERE clause on one or more columns of the materialized view.
```

**에러가 조건을 그대로 알려 준다** — 구체화 뷰 위에 `WHERE` 없는 고유 인덱스가 있어야 한다.

**구체화 뷰는 표가 아니다 — 직접 넣을 수 없다.**

```text
### SQL: INSERT INTO mv48_high VALUES (9,'zed',999);
--- PG 18.6 ---
ERROR:  cannot change materialized view "mv48_high"
```

---

### 3. ★ MySQL 8.4.10 에는 구체화 뷰가 없다 — 던져서 확인한다

**언제 쓰나** — 「MySQL 에도 있겠지」라고 생각할 때. **없다고 단정하기 전에 던진다.**

```text
### SQL: CREATE MATERIALIZED VIEW mv48_high AS SELECT id FROM emp;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'MATERIALIZED VIEW mv48_high AS SELECT id FROM emp' at line 1

### SQL: REFRESH MATERIALIZED VIEW mv48_high;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'REFRESH MATERIALIZED VIEW mv48_high' at line 1
```

그림 해설 — **`ERROR 1064` 는 문법 오류다.** 「권한이 없다」도 「지원하지 않는다」도 아니라 **파서가 `MATERIALIZED` 라는 낱말을 모른다.**\
에러 메시지의 `near 'MATERIALIZED VIEW …'` 가 파서가 멈춘 지점을 가리킨다 — `CREATE` 다음에 올 수 있는 낱말이 아니었다.

**그 자리를 메우는 것은 「표 + 배치」다.**

```text
 PostgreSQL                         MySQL 8.4.10
 +--------------------------+       +---------------------------------+
 | CREATE MATERIALIZED VIEW |       | CREATE TABLE … AS SELECT …      |
 | REFRESH MATERIALIZED …   |       | TRUNCATE + INSERT … SELECT …    |
 |  (엔진이 낡음을 안다)      |       |  (낡음 관리는 전부 내 책임)       |
 +--------------------------+       +---------------------------------+
```

실제로 돌려 보면 **같은 낡음 현상이 그대로 재현된다.**

```text
### SQL: CREATE TABLE t48_high_snap AS SELECT id, name, salary FROM t48_emp WHERE salary >= 400;
###      UPDATE t48_emp SET salary = 900 WHERE name='ann';
--- MySQL 8.4.10 · 뷰는 따라온다 ---
+----+------+--------+
| id | name | salary |
+----+------+--------+
|  1 | ann  |    900 |
|  2 | bob  |    500 |
|  4 | dan  |    400 |
+----+------+--------+
--- MySQL 8.4.10 · 스냅샷 표는 낡은 채다 ---
+----+------+--------+
| id | name | salary |
+----+------+--------+
|  2 | bob  |    500 |
|  4 | dan  |    400 |
+----+------+--------+
```

```text
### SQL: TRUNCATE t48_high_snap;
###      INSERT INTO t48_high_snap SELECT id, name, salary FROM t48_emp WHERE salary >= 400;
--- MySQL 8.4.10 (PG 의 REFRESH 자리) ---
+----+------+--------+
| id | name | salary |
+----+------+--------+
|  1 | ann  |    900 |
|  2 | bob  |    500 |
|  4 | dan  |    400 |
+----+------+--------+
```

그림 해설 — 결과는 `REFRESH` 와 같다. **다른 것은 「누가 낡음을 관리하나」다.**\
대가 — `TRUNCATE` 와 `INSERT` 사이에 읽는 사람은 **빈 표를 본다.** PG 의 `REFRESH` 는 그 틈이 없다(트랜잭션 안에서 바꾼다).\
운영에서 사전 집계 계층을 어떻게 쌓고 언제 굽는지는 [`timeseries-resolution-tiers`](../../../../../systems/timeseries-resolution-tiers/) 가 정본이다.

---

### 4. 갱신 가능한 뷰 — 어떤 뷰에 넣을 수 있나

**언제 쓰나** — 뷰를 「진짜 표처럼」 쓰려 할 때. **조건이 꽤 빡빡하다.**

```text
 넣을 수 있는 뷰                      넣을 수 없는 뷰
 +---------------------------+       +---------------------------+
 | 표 하나에서                |       | GROUP BY · 집계 함수       |
 | 열을 골라 오고             |       | DISTINCT                  |
 | WHERE 로 거른 것           |       | UNION 등 집합 연산         |
 +---------------------------+       | (엔진마다 목록이 더 있다)   |
   -> 행이 1:1 로 되짚어진다           +---------------------------+
                                       -> 어느 원본 행을 바꿀지 정해지지 않는다
```

**단순 뷰에는 들어간다.**

```text
### SQL: INSERT INTO v48_high VALUES (5,'eve',700);  SELECT * FROM t48_emp ORDER BY id;
--- PG 18.6 ---
INSERT 0 1
 id | name | dept_id | salary
----+------+---------+--------
  1 | ann  |      10 |    300
  2 | bob  |      10 |    500
  3 | cho  |      20 |
  4 | dan  |         |    400
  5 | eve  |         |    700       <- 뷰에 없는 열 dept_id 는 NULL
(5 rows)
```

MySQL 도 똑같이 들어간다(양쪽 다 `dept_id` 는 `NULL`).

**집계 뷰에는 못 넣는다 — 에러가 이유를 말해 준다.**

```text
### SQL: INSERT INTO v48_agg VALUES (30, 1);
--- PG 18.6 ---
ERROR:  cannot insert into view "v48_agg"
DETAIL:  Views containing GROUP BY are not automatically updatable.
HINT:  To enable inserting into the view, provide an INSTEAD OF INSERT trigger or an unconditional ON INSERT DO INSTEAD rule.
--- MySQL 8.4.10 ---
ERROR 1471 (HY000) at line 28: The target table v48_agg of the INSERT is not insertable-into
```

그림 해설 — **PG 는 이유(`GROUP BY`)와 우회로(`INSTEAD OF` 트리거)까지 적어 준다.** MySQL 은 「넣을 수 없는 대상」이라고만 한다.\
PG 의 `HINT` 가 이 주제의 경계를 그린다 — **자동 갱신이 안 될 뿐, 트리거를 달면 넣을 수 있다.**

**어느 뷰가 갱신 가능한지는 외우는 게 아니라 카탈로그에 묻는다.**

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

**양쪽 다 `information_schema.views` 에 답이 있다.** PG 에만 `is_insertable_into` 가 따로 있다.

---

### 5. ★ `WITH CHECK OPTION` — 넣었는데 안 보이는 행을 막는다

**언제 쓰나** — 뷰를 「부분 표」처럼 쓸 때. **없으면 조용히 사라지는 행이 생긴다.**

```text
 CHECK OPTION 없음                     WITH CHECK OPTION
 +----------------------------+       +----------------------------+
 | INSERT (6,'fox',100)       |       | INSERT (7,'gil',100)       |
 |   -> 성공 (INSERT 0 1)     |       |   -> ERROR                 |
 |   -> 뷰에서 안 보인다       |       |   -> 아무것도 안 들어간다   |
 |   -> 기반 표에는 있다       |       |                            |
 +----------------------------+       +----------------------------+
   조용히 「사라진」 행                  시끄럽게 막힌 행
```

`v48_high` 는 `salary >= 400` 인 행만 보여 준다. 거기에 `salary = 100` 인 행을 넣었다.

```text
### SQL: INSERT INTO v48_high VALUES (6,'fox',100);
--- PG 18.6 ---
INSERT 0 1                     <- 성공했다

### SQL: SELECT * FROM v48_high ORDER BY id;
--- PG 18.6 ---
 id | name | salary
----+------+--------
  2 | bob  |    500
  4 | dan  |    400
  5 | eve  |    700
(3 rows)                        <- fox 가 없다

### SQL: SELECT id,name,salary FROM t48_emp WHERE id=6;
--- PG 18.6 ---
 id | name | salary
----+------+--------
  6 | fox  |    100
(1 row)                         <- 기반 표에는 있다
```

**「성공했는데 결과에 없다」** — 이것이 `WITH CHECK OPTION` 이 막는 사고다.

```text
### SQL: CREATE VIEW v48_high_chk AS SELECT id, name, salary FROM t48_emp WHERE salary >= 400 WITH CHECK OPTION;
###      INSERT INTO v48_high_chk VALUES (7,'gil',100);
--- PG 18.6 ---
ERROR:  new row violates check option for view "v48_high_chk"
DETAIL:  Failing row contains (7, gil, null, 100).
--- MySQL 8.4.10 ---
ERROR 1369 (HY000) at line 23: CHECK OPTION failed 'study.v48_high_chk'
```

**`UPDATE` 로 행을 뷰 밖으로 밀어내는 것도 같이 막힌다.**

```text
### SQL: UPDATE v48_high_chk SET salary = 10 WHERE id = 2;
--- PG 18.6 ---
ERROR:  new row violates check option for view "v48_high_chk"
DETAIL:  Failing row contains (2, bob, 10, 10).
```

그림 해설 — PG 의 `DETAIL` 은 **막힌 행의 전체 모습**을 보여 준다(뷰에 없는 `dept_id` 칸까지).\
비용 — 넣고 바꿀 때마다 조건을 한 번 더 평가한다. 그 대가로 **「넣었는데 안 보인다」가 사라진다.**

> **`WITH CHECK OPTION`** — 뷰를 통해 들어가거나 바뀌는 행이 **뷰의 `WHERE` 를 만족해야 한다**는 제약.\
> 예: `WHERE salary >= 400 WITH CHECK OPTION` 인 뷰에 `salary=100` 을 넣으면 거부된다.

> **`LOCAL` / `CASCADED`** — 뷰 위에 뷰를 얹었을 때 **어느 층의 조건까지 검사하나**를 정하는 수식어.\
> 예: `WITH LOCAL CHECK OPTION` 은 이 뷰의 조건만, `CASCADED` 는 아래 뷰의 조건까지 본다. 기본값은 두 엔진 모두 `CASCADED` 다.

---

### 6. ★ 기반 표를 부수면 — PG 는 막고 MySQL 은 통과시킨다

**언제 쓰나** — 스키마를 바꿀 때. **여기가 이 주제에서 두 엔진이 가장 크게 갈리는 자리다.**

```text
 PostgreSQL 18.6                      MySQL 8.4.10
 +-----------------------------+     +-----------------------------+
 | DROP TABLE t48_emp;         |     | DROP TABLE t48_emp;         |
 |   -> ERROR (의존 객체 나열)  |     |   -> 성공 (조용히)           |
 |   -> 뷰는 절대 안 깨진다     |     |   -> 뷰가 깨진 채 남는다     |
 +-----------------------------+     +-----------------------------+
   깨질 수 있는 시점: DDL 순간          깨진 것을 아는 시점: 읽을 때
```

```text
### SQL: DROP TABLE t48_emp;
--- PG 18.6 ---
ERROR:  cannot drop table t48_emp because other objects depend on it
DETAIL:  view v48_high depends on table t48_emp
materialized view mv48_high depends on table t48_emp
view v48_high_chk depends on table t48_emp
view v48_agg depends on table t48_emp
HINT:  Use DROP ... CASCADE to drop the dependent objects too.
```

**열 하나만 지우려 해도 같다.**

```text
### SQL: ALTER TABLE t48_emp DROP COLUMN salary;
--- PG 18.6 ---
ERROR:  cannot drop column salary of table t48_emp because other objects depend on it
DETAIL:  view v48_high depends on column salary of table t48_emp
materialized view mv48_high depends on column salary of table t48_emp
view v48_high_chk depends on column salary of table t48_emp
HINT:  Use DROP ... CASCADE to drop the dependent objects too.
```

MySQL 에서 같은 문을 던지면 **아무 말 없이 통과한다.** 깨진 것은 **읽을 때** 드러난다.

```text
### SQL: ALTER TABLE t48_emp DROP COLUMN salary;      -- 성공
### SQL: SELECT * FROM v48_high;
--- MySQL 8.4.10 ---
ERROR 1356 (HY000) at line 1: View 'study.v48_high' references invalid table(s) or column(s) or function(s) or definer/invoker of view lack rights to use them
```

```text
### SQL: CHECK TABLE v48_high;
--- MySQL 8.4.10 ---
| Table          | Op    | Msg_type | Msg_text                                                          |
| study.v48_high | check | Error    | View 'study.v48_high' references invalid table(s) or column(s) … |
| study.v48_high | check | error    | Corrupt                                                           |
```

> **표 테두리를 지웠다.** `CHECK TABLE` 출력의 `Msg_text` 칸이 길어 테두리째 실으면 화면을 넘는다.
> 위는 `+---+` 테두리만 지운 것이고, `Msg_text` 뒷부분(`or definer/invoker …`)은 `…` 로 줄였다 — 전문은 바로 위 `ERROR 1356` 과 같은 문장이다.

그림 해설 — **MySQL 의 뷰는 깨진 채 카탈로그에 남는다.** `CHECK TABLE` 이 `Corrupt` 라고 답한다.\
비용 — PG 는 DDL 을 어렵게 만드는 대신 **읽기가 절대 안 깨진다.** MySQL 은 DDL 이 자유로운 대신 **배포 뒤 첫 조회에서 터진다.**\
대가 — MySQL 쪽 사고는 조용하다. 표를 지운 배포가 성공으로 보고되고, 며칠 뒤 그 뷰를 읽는 화면에서만 터진다.

---

### 7. `SELECT *` 는 뷰를 만들 때 펼쳐진다

**언제 쓰나** — `SELECT *` 로 뷰를 만들고 나중에 열을 추가할 때.

```text
CREATE VIEW v48_star AS SELECT * FROM t48_emp;   (이때 열 4개)
        ↓
ALTER TABLE t48_emp ADD COLUMN memo text;        (열 5개가 됐다)
        ↓
뷰는 여전히 열 4개 — * 가 만들 때 펼쳐졌기 때문이다
```

```text
### SQL: SELECT pg_get_viewdef('v48_star', true);
--- PG 18.6 ---
  SELECT id,
     name,
     dept_id,
     salary
    FROM t48_emp;          <- memo 가 없다. 저장된 것은 * 가 아니라 열 목록이다

### SQL: SELECT * FROM v48_star ORDER BY id LIMIT 2;
--- PG 18.6 ---
 id | name | dept_id | salary
----+------+---------+--------
  1 | ann  |      10 |    300
  2 | bob  |      10 |    500
(2 rows)
```

MySQL 도 같다 — `SHOW CREATE VIEW v48_star` 가 `select …id…, …name…, …dept_id…, …salary… from t48_emp` 로 **네 열을 펼쳐** 보여 주고, `memo` 는 없다.

그림 해설 — **`*` 는 저장되지 않는다.** 뷰 정의 시점의 열 목록으로 굳는다.\
대가 — 「뷰가 새 열을 안 보여 준다」는 버그 신고의 정체가 대개 이것이다. 고치려면 뷰를 다시 만든다(`CREATE OR REPLACE VIEW`).

## 문법 — 어느 절에서 무엇이 보이나

SQL 에서 이 절의 본체는 형태가 아니라 「**뷰 이름이 어디까지 표처럼 쓰이나**」다.

```sql
-- 공통
CREATE VIEW v AS SELECT …;
CREATE OR REPLACE VIEW v AS SELECT …;   -- 열 개수·이름·타입이 같아야 한다
DROP VIEW v;
DROP VIEW IF EXISTS v;
CREATE VIEW v (a, b) AS SELECT x, y FROM t;      -- 열 이름을 따로 준다
CREATE VIEW v AS SELECT … WITH CHECK OPTION;     -- LOCAL / CASCADED

-- PostgreSQL 에만
CREATE MATERIALIZED VIEW mv AS SELECT …;
CREATE MATERIALIZED VIEW mv AS SELECT … WITH NO DATA;   -- 만들되 비워 둔다
REFRESH MATERIALIZED VIEW mv;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv;              -- 고유 인덱스 필요
DROP MATERIALIZED VIEW mv;

-- MySQL 에만
CREATE ALGORITHM=MERGE|TEMPTABLE|UNDEFINED VIEW v AS SELECT …;
SHOW CREATE VIEW v;
CHECK TABLE v;
```

- **뷰를 쓸 수 있는 자리** — `FROM`·조인 대상·서브쿼리. 표가 오는 자리면 대개 온다.
- **못 쓰는 자리** — `CREATE INDEX` 의 대상(PG 는 **구체화 뷰에는 인덱스를 걸 수 있다**), 외래키의 참조 대상.
- **`CREATE OR REPLACE VIEW`** 는 열을 **추가**할 수는 있어도(뒤에 붙이는 것만) 기존 열의 이름·타입·순서는 못 바꾼다.
- 구체화 뷰는 **표처럼 생겼지만 표가 아니다** — `INSERT`/`UPDATE`/`DELETE` 가 전부 막힌다(2절).

## 어디서 틀리나

| 틀리는 자리 | 무슨 일이 일어나나 | 근거 |
|---|---|---|
| 뷰로 감싸면 빨라질 것 같다 | **안 빨라진다.** 저장된 것은 질의뿐이라 읽을 때마다 다시 돈다 | 1절의 `pg_get_viewdef` |
| 구체화 뷰를 만들어 두고 `REFRESH` 를 안 건다 | 화면이 **조용히 낡은 값**을 보여 준다 | 2절 (같은 순간 2행 대 3행) |
| MySQL 에도 구체화 뷰가 있겠지 | `ERROR 1064` — **파서가 낱말을 모른다** | 3절 |
| 집계 뷰에 `INSERT` | `cannot insert into view` / `ERROR 1471` | 4절 |
| `WITH CHECK OPTION` 없이 부분 뷰에 넣는다 | `INSERT 0 1` 인데 **뷰에서 안 보인다** | 5절 |
| MySQL 에서 뷰가 쓰는 열을 `DROP` | **DDL 은 통과하고 첫 조회에서 `ERROR 1356`** | 6절 |
| `SELECT *` 뷰에 열을 추가하면 보일 것 같다 | **안 보인다.** `*` 는 만들 때 펼쳐진다 | 7절 |
| `REFRESH … CONCURRENTLY` 를 그냥 건다 | 고유 인덱스가 없으면 에러 | 2절 |
| `REFRESH` 중에 읽으려 한다 | 기본 `REFRESH` 는 **읽기를 막는다**(`CONCURRENTLY` 가 그것을 푼다) | PG 문서 |

★ **가장 조용한 것은 5절과 6절이다.** 둘 다 **문이 성공한다.** 틀린 것은 나중에 다른 화면에서 드러난다.

## 구현 세부사항 대 언어 보장

| 항목 | 성격 | 근거 |
|---|---|---|
| 뷰가 「저장된 질의」라는 것 | **양쪽 공통** — 정의를 되읽으면 문장이 나온다 | 1절 (`pg_get_viewdef` · `SHOW CREATE VIEW`) |
| `SELECT *` 가 생성 시점에 펼쳐지는 것 | **양쪽 공통** | 7절 |
| `WITH CHECK OPTION` 이 `INSERT`·`UPDATE` 를 막는 것 | **양쪽 공통** (에러 코드는 다르다) | 5절 |
| 계획에서 뷰 이름이 사라지는 것 | **옵티마이저의 선택** — MySQL 은 `ALGORITHM` 으로 바뀐다 | 1절 |
| 구체화 뷰의 존재 | **엔진 차이** — PG 에만 있다 | 3절 |
| 기반 표 DDL 을 막느냐 | **엔진 차이** — PG 는 막고 MySQL 은 안 막는다 | 6절 |
| 어떤 뷰가 갱신 가능한가의 정확한 목록 | **엔진마다 다르다** — 카탈로그에 물어야 한다 | 4절 |

★ **이 편의 계획 블록(1절)은 「관찰」이지 보장이 아니다.** 통계가 흔들리면 계획은 바뀐다 —
[19번](../19-semi-anti-join/)에 같은 서버·같은 버전에서 계획이 두 번 달랐던 실측이 있다.
1절의 두 계획은 **제출 직전에 다시 찍어 대조했고, 두 번 다 같았다.**

## 언제 쓰고 언제 안 쓰나

```text
 뷰를 쓴다                            구체화 뷰를 쓴다
 +---------------------------+       +---------------------------+
 | 같은 SELECT 가 여러 곳에   |       | 집계가 무겁고               |
 | 권한을 열 단위로 자르고 싶다|       | 몇 분 낡아도 괜찮고          |
 | 항상 최신이어야 한다        |       | 읽기가 쓰기보다 훨씬 잦다    |
 +---------------------------+       +---------------------------+

 뷰를 안 쓴다                         구체화 뷰를 안 쓴다
 +---------------------------+       +---------------------------+
 | 뷰 위에 뷰를 여러 겹       |       | 결과가 항상 최신이어야 한다  |
 |  (계획이 읽기 어려워진다)   |       | 갱신 주기를 정할 수 없다     |
 | 성능을 기대하고 감싼다      |       | REFRESH 를 걸 곳이 없다     |
 +---------------------------+       +---------------------------+
```

- **뷰의 값은 성능이 아니라 이름이다.** 복잡한 조인에 이름을 붙여 호출부를 읽히게 만드는 것.
- **구체화 뷰를 쓰기로 했으면 「누가 언제 `REFRESH` 하나」를 같이 정한다.** 정하지 않으면 낡은 값이 정답인 척한다.
- MySQL 이라면 **표 + 배치**가 같은 자리다(3절). 낡음 관리가 전부 내 책임이 된다는 것만 다르다.

## 핵심 문장

1. **뷰는 결과가 아니라 질의를 저장한다** — 그래서 항상 최신이고, 읽을 때마다 비용을 낸다.
2. **구체화 뷰는 질의가 아니라 결과를 저장한다** — 그래서 빠르고, 낡는다. `REFRESH` 가 그 대가다.
3. **MySQL 8.4.10 에는 구체화 뷰가 없다** — `ERROR 1064`, 즉 파서가 낱말을 모른다. 자리는 「표 + 배치」가 메운다.
4. **갱신 가능한 뷰는 행이 1:1 로 되짚어지는 뷰뿐이다** — 집계·`DISTINCT`·집합 연산이 섞이면 막힌다.
5. **`WITH CHECK OPTION` 이 없으면 「넣었는데 안 보이는 행」이 조용히 생긴다.**
6. **PG 는 뷰를 깨는 DDL 을 막고, MySQL 은 통과시킨 뒤 읽을 때 `ERROR 1356` 으로 터뜨린다.**

## 관련 자료

- [`systems/timeseries-resolution-tiers`](../../../../../systems/timeseries-resolution-tiers/) — **그쪽은 사전 집계를 어느 해상도로 몇 계층 쌓고 언제 굽고 언제 버리나(운영 설계)까지, 여기는 그 계층을 담는 「객체」를 SQL 로 정의하는 문법부터다.** 「일 단위 롤업을 만들까」는 그쪽, 「그것을 구체화 뷰로 쓸까 표로 쓸까」는 여기.
- [58번 `EXPLAIN` 읽기](../58-explain-plan-tree/) — 1절에서 뷰 이름이 계획에서 사라지는 것을 봤다. 그 계획을 읽는 법.
- [19번 세미·안티 조인](../19-semi-anti-join/) — 계획이 같은 서버에서 두 번 달랐던 실측. 「계획은 관찰이다」의 근거.
- [32 CTE(WITH)](../32-cte-with-clause/) — 이름 붙인 서브질의. 뷰가 **저장되는** 이름이라면 CTE 는 **그 질의 안에서만 사는** 이름이다.
- [42 CREATE·ALTER·DROP TABLE](../42-create-alter-drop-table/) — 구체화 뷰의 대체 수단이 표라는 것(3절)이 그 주제와 맞닿는다.

## 용어 풀이

- **뷰(view)** — 이름이 붙은 `SELECT` 문. 행을 저장하지 않는다. 예: `CREATE VIEW v AS SELECT id FROM emp;`
- **구체화 뷰(materialized view)** — 질의 결과 행을 실제로 저장하는 객체. 예: PG 의 `CREATE MATERIALIZED VIEW`.
- **낡음(staleness)** — 저장된 결과가 기반 데이터와 어긋난 상태. 예: `ann` 의 급여를 바꿨는데 구체화 뷰는 옛 값을 준다.
- **`REFRESH`** — 구체화 뷰의 질의를 다시 돌려 저장된 결과를 갈아 끼우는 명령. 예: `REFRESH MATERIALIZED VIEW mv;`
- **갱신 가능한 뷰(updatable view)** — 뷰를 통해 `INSERT`/`UPDATE`/`DELETE` 를 할 수 있는 뷰. 예: 표 하나에 `WHERE` 만 건 뷰.
- **`WITH CHECK OPTION`** — 뷰로 들어가는 행이 뷰의 조건을 만족하도록 강제하는 수식어. 예: `salary >= 400` 뷰에 `100` 을 넣으면 거부.
- **`ALGORITHM=MERGE` / `TEMPTABLE`**(MySQL) — 뷰를 바깥 질의에 펼쳐 넣을지, 임시 표로 먼저 만들지를 정하는 선택. 예: `TEMPTABLE` 이면 계획에 `<derived2>` 가 뜬다.
- **인라인(inline)** — 뷰의 정의를 바깥 질의 안에 펼쳐 넣는 것. 예: 계획에 뷰 이름 대신 `emp` 가 나온다.
- **의존(dependency)** — 어떤 객체가 다른 객체 없이는 못 사는 관계. 예: 뷰는 자기가 읽는 표에 의존한다.
- **카탈로그(catalog)** — 엔진이 객체 정의를 담아 두는 시스템 표. 예: `information_schema.views`.
- **`CASCADE`** — 의존하는 객체까지 함께 지우라는 수식어. 예: `DROP TABLE t CASCADE;` 는 그 표를 읽던 뷰도 지운다.
- **암묵 커밋(implicit commit)** — DDL 을 던지면 열려 있던 트랜잭션이 자동으로 커밋되는 것. 예: MySQL 에서 `CREATE VIEW` 는 되돌릴 수 없다.

## 더 들어가면

- **`WITH NO DATA`** — PG 는 구체화 뷰를 **비운 채** 만들 수 있다. 이때 읽으려 하면 「아직 채워지지 않았다」는 에러가 나고, `REFRESH` 를 해야 쓸 수 있다. 배포 시점과 첫 적재 시점을 떼어 놓는 용도다. *(이 편에서는 돌려 보지 않았다 — 본문 실험의 범위 밖이다.)*
- **증분 갱신(incremental / fast refresh)** — 「바뀐 부분만 다시 계산하기」는 PG 의 `REFRESH` 에 없다(전량 재계산이다). Oracle 의 fast refresh, 일부 확장·다른 엔진이 지원한다.
- **`INSTEAD OF` 트리거** — 4절의 PG `HINT` 가 가리키는 길. 갱신 불가능한 뷰에도 「이 뷰에 `INSERT` 가 오면 실제로는 이렇게 하라」를 직접 쓸 수 있다.
- **권한의 도구로서의 뷰** — 「급여 열은 빼고 나머지만」 같은 열 단위 접근 제어를 뷰로 만든다. MySQL 의 `SQL SECURITY DEFINER`(1절 출력에 보인다)가 그때 누구의 권한으로 읽을지를 정한다.
