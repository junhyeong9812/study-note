# sql/20-LATERAL 조인 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions (LATERAL Subqueries)](https://www.postgresql.org/docs/18/queries-table-expressions.html#QUERIES-LATERAL) · [MySQL 8.4 · Lateral Derived Tables](https://dev.mysql.com/doc/refman/8.4/en/lateral-derived-tables.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 버전은 `SELECT VERSION()` 으로 두 서버에서 직접 확인했다(`PostgreSQL 18.6 …` · `8.4.10`).\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 두 개만 썼다. **새로 만든 표가 없다.**\
> **버전** — `LATERAL` 은 **PostgreSQL 9.3 부터**, **MySQL 8.0.14 부터**다. 두 도입 버전은 **릴리스 노트**에서 확인한 것이고 매뉴얼 본문에는 없다([주제 목록](../README.md)의 「버전 기준」 참조).\
> **선행** — [11 서브쿼리](../11-subquery-scalar-correlated-any-all/) · [13 INNER JOIN](../13-inner-join/) · [10 FROM 절](../10-from-clause-aliases-derived-tables/).\
> **이 주제의 출발점** — [10번](../10-from-clause-aliases-derived-tables/)의 「파생 테이블은 바깥을 못 본다」. **그 벽에 난 문이 `LATERAL` 이다.**

## 한눈에 — 쉽게 말하면

**`LATERAL` = `FROM` 안의 서브쿼리에게 「앞에 있는 표의 현재 행을 봐도 된다」고 허락하는 표시.**

`FROM` 의 항목들은 원래 **서로를 모르는 형제**다.

```text
 LATERAL 없이 (기본)                     LATERAL 을 붙이면
 FROM dept d, (SELECT … WHERE ? = d.id)  FROM dept d, LATERAL (SELECT … WHERE ? = d.id)
            └──── d 를 못 본다 ────┘                └──── d 를 본다 ────┘

  형제는 동시에 만들어진다                왼쪽을 먼저 만들고, 그 행마다 오른쪽을 만든다
  -> "d 의 현재 행" 같은 게 없다          -> "d 의 현재 행" 이 생긴다
```

- 비유하면 **줄 서 있는 사람에게 서류를 나눠 주는 일**이다.
- 보통은 **같은 서류를 전원에게** 준다(파생 테이블). 누가 받든 내용이 같다.
- `LATERAL` 은 **사람마다 다른 서류를 그 자리에서 만들어** 준다. 앞사람이 누구였는지를 보고 만든다.

| 비유 | 실체 |
|---|---|
| 전원에게 같은 서류 | 일반 파생 테이블 — 한 번 만들어 모두에게 |
| 사람마다 다른 서류 | `LATERAL` — 왼쪽 행마다 다시 만든다 |
| 앞사람 이름을 보고 만든다 | 서브쿼리가 왼쪽 열을 참조한다 |
| 서류가 **여러 장**일 수 있다 | `LATERAL` 은 **여러 행**을 돌려줄 수 있다 |
| 서류에 **칸이 여러 개** | **여러 열**을 돌려줄 수 있다 |
| 앞사람이 아직 안 정해졌는데 서류를 만들라 | **`LATERAL` 없이 참조 → 에러** |

**똑같은 구조다** — 상관 서브쿼리([11번](../11-subquery-scalar-correlated-any-all/))도 "행마다 다시 계산"하지만 **1행 1열**만 낼 수 있다.\
`LATERAL` 은 그 제약을 푼 것이다. **행마다 여러 행·여러 열**을 붙일 수 있다.

> **`LATERAL`** — `FROM` 의 서브쿼리가 **왼쪽에 있는 항목의 현재 행**을 참조할 수 있게 하는 키워드.\
> 예: `FROM dept d CROSS JOIN LATERAL (SELECT … WHERE e.dept_id = d.id LIMIT 2) t` — 부서마다 상위 2명.

## 이 주제가 답하려는 질문

1. **`LATERAL` 없이는 왜 안 되나?** — 에러 메시지가 그 이유를 말해 주나.
2. **상관 서브쿼리로 못 하는 것을 `LATERAL` 이 하나?** — 무엇이 가능해지나.
3. **MySQL 도 되나?** — 문법과 제약이 같은가.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들은 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

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
        ^          ^
        |          +-- dan 은 소속이 없다
        +------------- cho 는 급여가 없다 (NULL)
```

**이 주제의 과녁은 「부서별 상위 N명」이다.**

```text
 sales : bob(500), ann(300)   -> 상위 2명이 둘 다 있다
 dev   : cho(NULL)            -> 한 명뿐이고 급여가 NULL 이다
 hr    : (없음)               -> LEFT 로 붙여야 남는다
        ↑
  세 부서가 각각 다른 경계 사례다 — 한 질의로 셋을 다 본다
```

<details>
<summary>표를 만드는 문 (PostgreSQL)</summary>

```sql
CREATE TABLE dept (
  id   int PRIMARY KEY,
  name text UNIQUE NOT NULL
);
CREATE TABLE emp (
  id      int PRIMARY KEY,
  name    text NOT NULL,
  dept_id int,
  salary  int
);
INSERT INTO dept VALUES (10,'sales'), (20,'dev'), (30,'hr');
INSERT INTO emp  VALUES (1,'ann',10,300), (2,'bob',10,500), (3,'cho',20,NULL), (4,'dan',NULL,400);
```

MySQL 은 `text` → `varchar(20)` 만 바꾸면 같다.

</details>

## 동작 방식

### 1. `LATERAL` 없이 참조하면 — **벽에 부딪힌다**

**언제 쓰나** — "부서마다 다른 서브쿼리를 돌리고 싶다"가 떠올랐을 때. **그 순간 이 에러를 만난다.**

```text
### SQL: SELECT d.name AS dept, t.name AS emp FROM dept d
         JOIN (SELECT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id ORDER BY e.id LIMIT 1) AS t ON true;
--- PG 18.6 ---
ERROR:  invalid reference to FROM-clause entry for table "d"
LINE 1: ...CT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id ORDER...
                                                             ^
DETAIL:  There is an entry for table "d", but it cannot be referenced from this part of the query.
HINT:  To reference that table, you must mark this subquery with LATERAL.
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'd.id' in 'where clause'
```

```text
 왜 막는가

 FROM 의 항목들은 서로 "형제"다
        ↓
 d 와 t 가 동시에 만들어진다
        ↓
 t 를 만들 시점에는 "d 의 현재 행" 이라는 것이 아직 없다
        ↓
 d.id 가 무엇을 가리켜야 할지 정할 수 없다   ->   거부
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `LATERAL` 없이 왼쪽 참조 | `invalid reference to FROM-clause entry` + **`HINT: … mark this subquery with LATERAL`** | `ERROR 1054 … Unknown column 'd.id' in 'where clause'` |

그림 해설 — **PG 의 `HINT` 가 이 주제의 이름을 직접 말해 준다.** "참조하려면 `LATERAL` 로 표시하라."\
MySQL 은 그냥 "모르는 열"이라고 한다 — **같은 벽인데 한쪽만 문을 알려 준다.**\
비용 — 없다. **이 벽은 의도된 것**이다. 벽이 있어서 엔진이 `FROM` 항목을 어떤 순서로든 계산할 수 있다.

이 벽 자체는 [10번](../10-from-clause-aliases-derived-tables/)이 정본이다. **여기서는 그 문을 연다.**

---

### 2. `LATERAL` 을 붙이면 — 왼쪽 행마다 다시 만든다

**언제 쓰나** — 왼쪽 행의 값으로 오른쪽을 좁혀야 할 때.

```text
(전) dept 3행                        (후) 부서마다 서브쿼리를 한 번씩

 d = sales(10)  ->  (SELECT … WHERE e.dept_id = 10 ORDER BY salary DESC LIMIT 1)  -> bob
 d = dev(20)    ->  (SELECT … WHERE e.dept_id = 20 …)                             -> cho
 d = hr(30)     ->  (SELECT … WHERE e.dept_id = 30 …)                             -> (0행)
```

```text
### SQL: SELECT d.name AS dept, t.name AS emp, t.salary FROM dept d
         CROSS JOIN LATERAL (SELECT e.name, e.salary FROM emp e WHERE e.dept_id = d.id
                             ORDER BY e.salary DESC LIMIT 1) AS t ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp | salary           +-------+-----+--------+
-------+-----+--------          | dept  | emp | salary |
 sales | bob |    500           +-------+-----+--------+
 dev   | cho |                  | sales | bob |    500 |
(2 rows)                        | dev   | cho |   NULL |
                                +-------+-----+--------+
```

**`hr` 이 없다.** `CROSS JOIN LATERAL` 은 서브쿼리가 0행이면 그 왼쪽 행을 버린다 — **내부 조인과 같다.**

`LEFT JOIN LATERAL … ON true` 로 바꾸면 남는다.

```text
### SQL: SELECT d.name AS dept, t.name AS emp, t.salary FROM dept d
         LEFT JOIN LATERAL (SELECT e.name, e.salary FROM emp e WHERE e.dept_id = d.id
                            ORDER BY e.salary DESC LIMIT 1) AS t ON true ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp | salary           +-------+------+--------+
-------+-----+--------          | dept  | emp  | salary |
 sales | bob |    500           +-------+------+--------+
 dev   | cho |                  | sales | bob  |    500 |
 hr    |     |                  | dev   | cho  |   NULL |
(3 rows)                        | hr    | NULL |   NULL |
                                +-------+------+--------+
```

그림 해설 — **`ON true` 가 관용구다.** 조인 조건은 이미 서브쿼리 `WHERE` 안에 있으므로 `ON` 에는 쓸 것이 없다.\
그래도 `LEFT JOIN` 에는 문법상 `ON` 이 필요해서 `true` 를 적는다. **두 엔진 다 `ON true` 를 받는다.**\
비용 — 왼쪽 행마다 서브쿼리가 돈다. 행이 많고 안쪽이 인덱스를 못 타면 그대로 곱해진다.

쉼표 표기도 된다(`CROSS JOIN LATERAL` 과 같다).

```text
### SQL: SELECT d.name AS dept, t.name AS emp FROM dept d,
         LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id ORDER BY e.id LIMIT 2) AS t
         ORDER BY d.id, t.name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp                     +-------+-----+
-------+-----                    | dept  | emp |
 sales | ann                     +-------+-----+
 sales | bob                     | sales | ann |
 dev   | cho                     | sales | bob |
(3 rows)                         | dev   | cho |
                                 +-------+-----+
```

---

### 3. **무엇이 가능해지나** — 상관 서브쿼리가 못 하는 두 가지

**언제 쓰나** — "상관 서브쿼리로 되는데 굳이 `LATERAL` 을 쓸 이유가 있나"가 떠오를 때.

```text
 상관 서브쿼리 (SELECT 칸)          LATERAL (FROM 칸)
 +--------------------------+      +--------------------------+
 | 1행 1열만 낼 수 있다      |      | 여러 행 · 여러 열         |
 +--------------------------+      +--------------------------+
```

**(가) 여러 행** — 부서별 상위 **2명**.

```text
### SQL: SELECT d.name AS dept, (SELECT e.name FROM emp e WHERE e.dept_id = d.id
                                 ORDER BY e.salary DESC, e.id LIMIT 2) AS top FROM dept d ORDER BY d.id;
--- PG 18.6 ---
ERROR:  more than one row returned by a subquery used as an expression
--- MySQL 8.4.10 ---
ERROR 1242 (21000) at line 1: Subquery returns more than 1 row

### SQL: SELECT d.name AS dept, t.name AS emp, t.salary FROM dept d
         LEFT JOIN LATERAL (SELECT e.name, e.salary FROM emp e WHERE e.dept_id = d.id
                            ORDER BY e.salary DESC, e.id LIMIT 2) AS t ON true
         ORDER BY d.id, t.salary DESC;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp | salary           +-------+------+--------+
-------+-----+--------          | dept  | emp  | salary |
 sales | bob |    500           +-------+------+--------+
 sales | ann |    300           | sales | bob  |    500 |
 dev   | cho |                  | sales | ann  |    300 |
 hr    |     |                  | dev   | cho  |   NULL |
(4 rows)                        | hr    | NULL |   NULL |
                                +-------+------+--------+
```

★ **같은 의도, 한쪽은 에러 한쪽은 4행.** 스칼라 서브쿼리의 **1행 계약**([11번](../11-subquery-scalar-correlated-any-all/))이 바로 여기서 막는다.

**(나) 여러 열** — 개수와 합계를 한 번에.

```text
### SQL: SELECT d.name AS dept, s.cnt, s.total FROM dept d
         CROSS JOIN LATERAL (SELECT COUNT(*) AS cnt, SUM(e.salary) AS total FROM emp e
                             WHERE e.dept_id = d.id) AS s ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | cnt | total             +-------+-----+-------+
-------+-----+-------            | dept  | cnt | total |
 sales |   2 |   800             +-------+-----+-------+
 dev   |   1 |                   | sales |   2 |   800 |
 hr    |   0 |                   | dev   |   1 |  NULL |
(3 rows)                         | hr    |   0 |  NULL |
                                 +-------+-----+-------+
```

```text
 상관 서브쿼리로 같은 것을 쓰면                LATERAL 로 쓰면
 (SELECT COUNT(*) …) AS cnt,                  서브쿼리를 한 번만 적는다
 (SELECT SUM(salary) …) AS total
        ↑                                            ↑
  같은 서브쿼리를 두 번 적는다                 한 번 적고 열 둘을 꺼낸다
  (엔진이 합칠 수도 있지만 보장은 없다)
```

그림 해설 — **`hr` 의 `cnt` 가 0 이고 `total` 이 `NULL` 이다.** 집계는 0행 위에서도 `COUNT` 는 0, `SUM` 은 `NULL` 을 낸다.\
그래서 `CROSS JOIN LATERAL` 인데도 `hr` 이 남았다 — **서브쿼리가 1행을 냈기 때문**이다.\
비용 — 집계 서브쿼리는 언제나 1행을 내므로 `CROSS` 로 써도 왼쪽 행이 안 사라진다. **`LIMIT` 서브쿼리와 다른 점이다.**

```text
 LATERAL 안이 집계면     -> 언제나 1행  -> CROSS JOIN LATERAL 이 안전하다
 LATERAL 안이 LIMIT 이면 -> 0행 가능    -> LEFT JOIN LATERAL … ON true 를 쓴다
```

---

### 4. `LATERAL` 은 **왼쪽만** 본다

**언제 쓰나** — `FROM` 의 순서를 바꾸고 싶을 때. **순서가 뜻을 가진다.**

```text
 FROM  A  ,  LATERAL (… A 참조 …)      OK — A 가 왼쪽에 있다
 FROM  LATERAL (… A 참조 …)  ,  A      X  — A 가 아직 안 나왔다
```

```text
### SQL: SELECT d.name, t.name FROM LATERAL (SELECT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id) AS t, dept d;
--- PG 18.6 ---
ERROR:  missing FROM-clause entry for table "d"
LINE 1: ...CT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id) AS t...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'd.id' in 'where clause'
```

그림 해설 — **`LATERAL` 은 순서 의존이다.** 일반 `FROM` 항목은 순서를 바꿔도 뜻이 같지만 `LATERAL` 은 아니다.\
비용 — 그래서 `LATERAL` 이 들어간 `FROM` 절은 **읽는 순서가 실행 순서**가 된다. 읽기에는 오히려 좋다.

**왼쪽에 항목이 여럿이면 전부 참조할 수 있다.**

```text
### SQL: SELECT d.name AS dept, e.name AS emp, t.n FROM dept d
         JOIN emp e ON e.dept_id = d.id
         CROSS JOIN LATERAL (SELECT COUNT(*) AS n FROM emp x
                             WHERE x.dept_id = d.id AND x.salary > e.salary) AS t ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp | n                 +-------+-----+---+
-------+-----+---                | dept  | emp | n |
 sales | ann | 1                 +-------+-----+---+
 sales | bob | 0                 | sales | ann | 1 |
 dev   | cho | 0                 | sales | bob | 0 |
(3 rows)                         | dev   | cho | 0 |
                                 +-------+-----+---+
```

`d` 와 `e` **둘 다** 참조했다. `ann` 보다 급여가 높은 같은 부서 사원은 `bob` 하나라 1 이다.

---

### 5. `LATERAL` 에는 `RIGHT JOIN` 을 못 쓴다

**언제 쓰나** — 조인 방향을 뒤집고 싶을 때. **PG 가 이유를 문장으로 알려 준다.**

```text
### SQL: SELECT d.name, t.name FROM dept d RIGHT JOIN LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id) AS t ON true;
--- PG 18.6 ---
ERROR:  invalid reference to FROM-clause entry for table "d"
LINE 1: ...TERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id) AS t...
                                                             ^
DETAIL:  The combining JOIN type must be INNER or LEFT for a LATERAL reference.
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'd.id' in 'where clause'
```

```text
 왜 안 되나

 RIGHT JOIN 은 "오른쪽을 다 남긴다" 는 뜻이다
        ↓
 오른쪽(LATERAL)을 만들려면 왼쪽 행이 필요한데
 왼쪽 행이 없는 경우에도 오른쪽을 내놓아야 한다
        ↓
 "왼쪽 행이 없을 때의 d.id" 를 정의할 방법이 없다   ->  거부
```

그림 해설 — **PG 의 `DETAIL` 이 규칙을 그대로 말한다** — `The combining JOIN type must be INNER or LEFT for a LATERAL reference.`\
이것은 [주제 목록](../README.md)이 MySQL 쪽에 적어 둔 제약(`INNER/CROSS/LEFT` 에만)과 **같은 내용**이고, **PG 도 똑같다.**\
비용 — 없다. 방향을 뒤집고 싶으면 **왼쪽과 오른쪽을 바꿔 적는다.**

★ **서브쿼리가 왼쪽을 실제로 참조하지 않으면** `RIGHT JOIN LATERAL` 도 통과한다 — 제약은 **문법이 아니라 참조**에 걸린다.

---

### 6. 계획에서 「행마다 돈다」를 확인한다

**언제 쓰나** — `LATERAL` 이 비싼지 판단할 때.

```text
### SQL: EXPLAIN SELECT d.name, t.name FROM dept d
         CROSS JOIN LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id ORDER BY e.salary DESC LIMIT 1) AS t;
--- PG 18.6 ---
 Nested Loop  (cost=24.16..30728.13 rows=1270 width=64)
   ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)
   ->  Limit  (cost=24.16..24.16 rows=1 width=36)
         ->  Sort  (cost=24.16..24.17 rows=6 width=36)
               Sort Key: e.salary DESC
               ->  Seq Scan on emp e  (cost=0.00..24.12 rows=6 width=36)
                     Filter: (dept_id = d.id)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Nested loop inner join  (cost=11.9 rows=4)
    -> Invalidate materialized tables (row from d)  (cost=0.65 rows=4)
        -> Covering index scan on d using name  (cost=0.65 rows=4)
    -> Table scan on t  (cost=2.96..2.96 rows=1)
        -> Materialize (invalidate on row from d)  (cost=0.45..0.45 rows=1)
            -> Limit: 1 row(s)  (cost=0.35 rows=1)
                -> Sort: e.salary DESC, limit input to 1 row(s) per chunk  (cost=0.35 rows=3)
                    -> Filter: (e.dept_id = d.id)  (cost=0.35 rows=3)
                        -> Table scan on e  (cost=0.35 rows=3)
```

★ **MySQL 이 이 주제의 동작을 계획에 문장으로 쓴다** — `Invalidate materialized tables (row from d)` · `Materialize (invalidate on row from d)`.\
**"`d` 의 행이 바뀌면 만들어 둔 것을 버린다"** — 그것이 `LATERAL` 이다.\
PG 는 `Nested Loop` 안쪽의 `Filter: (dept_id = d.id)` 로 같은 사실을 보인다.

**몇 번 돌았는지까지 센다.**

```text
### SQL: EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF, BUFFERS OFF)
         SELECT d.name, t.name FROM dept d
         CROSS JOIN LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id ORDER BY e.salary DESC LIMIT 1) AS t;
--- PG 18.6 ---
 Nested Loop (actual rows=2.00 loops=1)
   ->  Seq Scan on dept d (actual rows=3.00 loops=1)
   ->  Limit (actual rows=0.67 loops=3)
         ->  Sort (actual rows=0.67 loops=3)
               Sort Key: e.salary DESC
               Sort Method: quicksort  Memory: 25kB
               ->  Seq Scan on emp e (actual rows=1.00 loops=3)
                     Filter: (dept_id = d.id)
                     Rows Removed by Filter: 3
```

★ **`loops=3`.** `dept` 가 3행이니 서브쿼리가 **세 번** 돌았다.\
`actual rows=0.67` 은 **평균**이다 — 세 번 중 두 번만 1행을 냈다(`hr` 이 0행). 0.67 × 3 = 2행이 최종 결과다.

그림 해설 — **`LATERAL` 은 중첩 루프를 강제하는 성질이 있다.** 왼쪽 행이 정해져야 오른쪽을 만들 수 있기 때문이다.\
비용 — 왼쪽이 100만 행이면 서브쿼리가 100만 번 돈다. **안쪽이 인덱스를 타는지가 전부다**(목록의 **47번 주제**).

> **재현 주** — 위 계획의 추정 행 수(`rows=1270`·`rows=6`)는 **통계가 없을 때의 기본값**이다.\
> **여기서 볼 것은 비용 수치가 아니라 `loops` 와 연산자 이름**이다.\
> ★ **같은 서버·같은 버전에서 두 번 찍었더니 MySQL 의 추정 행 수가 `rows=4` 에서 `rows=3` 으로 바뀌어 있었다**(PG 는 한 글자도 안 달라졌다).\
> 계획의 **모양과 `Invalidate materialized tables` 표기는 두 번 다 같았다.** 위에 실은 것은 **제출 전 재확인 시점의 출력**이다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
FROM 왼쪽 CROSS JOIN LATERAL (SELECT …) AS t          -- 0행이면 왼쪽 행이 사라진다
FROM 왼쪽 , LATERAL (SELECT …) AS t                   -- 위와 같다 (쉼표 표기)
FROM 왼쪽 JOIN  LATERAL (SELECT …) AS t ON true        -- 위와 같다
FROM 왼쪽 LEFT JOIN LATERAL (SELECT …) AS t ON true    -- 0행이어도 왼쪽 행이 남는다
FROM 왼쪽 RIGHT JOIN LATERAL (…)                       -- 왼쪽을 참조하면 에러
FROM 왼쪽 CROSS JOIN generate_series(1, 왼쪽.n) AS g(i) -- PG: 함수 앞에서는 LATERAL 생략 가능
```

규칙 일곱.

1. **`LATERAL` 은 왼쪽 항목의 현재 행을 참조할 수 있게 한다.** 없으면 에러다.
2. **왼쪽만 본다.** `FROM` 에서 앞에 나온 항목만이다 — **순서가 뜻을 가진다.**
3. **`INNER`·`CROSS`·`LEFT` 에만 쓸 수 있다.** `RIGHT` 에서 왼쪽을 참조하면 PG 가 `DETAIL` 로 거부한다.
4. **`LEFT JOIN LATERAL` 에는 `ON true` 를 쓴다.** 조건은 이미 서브쿼리 안에 있다.
5. **`LIMIT` 서브쿼리는 0행이 가능하다** → `LEFT`. **집계 서브쿼리는 언제나 1행**이다 → `CROSS` 로도 안전하다.
6. **여러 행·여러 열을 돌려줄 수 있다.** 이것이 상관 서브쿼리와의 차이다.
7. **계획은 중첩 루프**가 된다. 왼쪽 행 수만큼 안쪽이 돈다.

읽을 때 붙잡을 것은 **"왼쪽 행 하나에 대해 이 서브쿼리가 무엇을 내나"** 하나다.

```text
 왼쪽 행 하나  ->  서브쿼리가 0행     ->  CROSS 면 사라지고, LEFT 면 NULL 로 남는다
 왼쪽 행 하나  ->  서브쿼리가 1행     ->  한 줄이 된다
 왼쪽 행 하나  ->  서브쿼리가 N행     ->  N 줄이 된다      <- 행이 는다
```

## 어디서 틀리나

- **`LATERAL` 을 빼고 왼쪽을 참조한다.**\
  PG 는 `HINT` 로 답을 알려 주지만 MySQL 은 `Unknown column` 이라고만 한다. **MySQL 쪽이 헤맬 여지가 크다.**
- **`CROSS JOIN LATERAL` 에 `LIMIT` 서브쿼리를 쓴다.**\
  짝이 없는 왼쪽 행이 **조용히 사라진다.** `hr` 이 그렇게 빠졌다. `LEFT JOIN … ON true` 로 쓴다.
- **`FROM` 의 순서를 바꾼다.**\
  `LATERAL` 이 왼쪽만 보므로 순서를 바꾸면 에러가 난다. 일반 `FROM` 항목의 직관이 안 통한다.
- **`RIGHT JOIN LATERAL` 로 방향을 뒤집으려 한다.**\
  왼쪽을 참조하면 거부된다. 항목 순서를 바꿔 적는 것이 답이다.
- **`LEFT JOIN LATERAL` 에 `ON` 조건을 넣고 그것으로 거른다.**\
  된다. 다만 `ON` 에서 떨어진 행은 **`NULL` 로 채워져 남는다**([15번](../15-on-vs-where-in-outer-join/)) — 서브쿼리 `WHERE` 로 거른 것과 뜻이 다르다.
- **상관 서브쿼리로 여러 행을 받으려 한다.**\
  `more than one row returned` 로 터진다. 거기가 `LATERAL` 의 자리다.
- **`LATERAL` 이 느리다고 단정하거나, 빠르다고 단정한다.**\
  중첩 루프라 **안쪽이 인덱스를 타면 매우 빠르고 아니면 매우 느리다.** 계획을 보고 판단한다.
- **MySQL 에서 `NULLS LAST` 를 쓴다.**\
  `LATERAL` 과 무관하게 MySQL 에는 그 문법이 없다([08번](../08-order-by-null-position-stability/)). `LATERAL` 안의 `ORDER BY` 에서 걸린다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `LATERAL` 없이 왼쪽 참조가 안 된다 | **문법의 규칙** | 언어 — 두 엔진이 같은 이유로 막는다 |
| 왼쪽 항목만 참조할 수 있다 | **문법의 규칙** | 언어 |
| `RIGHT JOIN` 에서 왼쪽 참조 불가 | **문법의 규칙** | 언어 — PG 가 `DETAIL` 로 명시한다 |
| 서브쿼리가 0행일 때 `CROSS` 는 버리고 `LEFT` 는 남긴다 | **결과의 정의** | 언어 |
| 여러 행·여러 열을 낼 수 있다 | **결과의 정의** | 언어 |
| **중첩 루프로 돈다** | 옵티마이저의 선택 | 아무도 — 다만 `LATERAL` 의 의미상 사실상 강제된다 |
| `loops=3` 같은 실제 반복 횟수 | 실행 결과 | 아무도 — 통계·계획에 달렸다 |
| `LATERAL` 이 있는 버전 | **버전** | **PG 9.3+ · MySQL 8.0.14+** (릴리스 노트로 확인) |
| 에러 문구 | 그 엔진의 표기 | 다르다 — **PG 만 `LATERAL` 을 알려 준다** |

- ★ **동작과 문법 제약은 두 엔진이 같았다.** 갈린 것은 **에러 문구의 질**과 **PG 전용 부가 기능**(아래)뿐이다.
- **PG 에는 함수 앞에서 `LATERAL` 키워드를 생략하는 편의가 있다.** MySQL 에는 그 문법 자체가 없다(아래 「더 들어가면」).
- **결과의 순서는 보장되지 않는다.** 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 그룹별 상위 N개.** 가장 전형적인 용도다. 「부서별 최고 연봉자」·「고객별 최근 주문 3건」.
- **쓴다 — 행마다 여러 값을 한 번에 계산할 때.** 개수·합계·최댓값을 서브쿼리 하나에서 꺼낸다.
- **쓴다 — 왼쪽 값을 인자로 받는 함수/집합 반환 함수를 붙일 때**(PG).
- **쓴다 — 계산 결과를 이름 붙여 재사용할 때.** `SELECT` 칸에서 같은 식을 세 번 쓰는 대신 `LATERAL` 로 한 번 계산한다.
- **안 쓴다 — 값 하나면 될 때.** 상관 서브쿼리가 짧다([11번](../11-subquery-scalar-correlated-any-all/)).
- **안 쓴다 — 「그룹별 상위 N」을 큰 표에서 뽑을 때.** 왼쪽 행마다 도는 비용이 크면 윈도우 함수 `ROW_NUMBER` 가 나을 수 있다(목록의 **29번 주제**).
- **주의 — `CROSS` 와 `LEFT` 의 선택.** 서브쿼리가 0행일 수 있으면 `LEFT … ON true` 다.

## 핵심 문장

- **`LATERAL` 은 `FROM` 의 서브쿼리에게 「왼쪽 행을 봐도 된다」고 허락하는 표시**다. 없으면 두 엔진 다 거부한다.
- **PG 의 에러가 답을 알려 준다** — `HINT: To reference that table, you must mark this subquery with LATERAL.`
- **상관 서브쿼리는 1행 1열, `LATERAL` 은 여러 행 여러 열**이다. 부서별 상위 2명은 스칼라로는 `more than one row` 다.
- **왼쪽만 본다.** `FROM` 의 순서가 뜻을 가지고, `RIGHT JOIN` 에서는 참조할 수 없다.
- **`LIMIT` 서브쿼리는 0행이 가능하므로 `LEFT … ON true`**, 집계 서브쿼리는 언제나 1행이라 `CROSS` 로도 안전하다.
- **계획은 중첩 루프**다 — PG 는 `loops=3`, MySQL 은 `Invalidate materialized tables (row from d)` 로 그 사실을 찍는다.
- **`LATERAL` 은 PG 9.3+ · MySQL 8.0.14+** 이고, 두 엔진에서 **문법과 제약이 같았다.**

## 관련 자료

- [PostgreSQL 18 · LATERAL Subqueries](https://www.postgresql.org/docs/18/queries-table-expressions.html#QUERIES-LATERAL) — 키워드의 의미와 함수 앞 생략 규칙.
- [MySQL 8.4 · Lateral Derived Tables](https://dev.mysql.com/doc/refman/8.4/en/lateral-derived-tables.html) — 쓸 수 있는 조인 종류.
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — **경계: 그쪽은 「`FROM` 형제끼리는 서로를 모른다」는 벽까지, 여기는 그 벽에 난 문부터.**
- [11 서브쿼리 — 스칼라·상관·ANY/ALL](../11-subquery-scalar-correlated-any-all/) — **경계: 그쪽은 값 자리의 상관 참조(1행 1열)까지, 여기는 그 제약을 푸는 것부터.**
- [13 INNER JOIN](../13-inner-join/) — `CROSS JOIN LATERAL` 이 왜 짝 없는 행을 버리나.
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — `LEFT JOIN LATERAL` 이 `hr` 을 살리는 근거.
- [15 OUTER JOIN 에서 ON 과 WHERE 의 차이](../15-on-vs-where-in-outer-join/) — `LEFT JOIN LATERAL … ON <조건>` 에서 조건의 자리.
- [19 세미·안티 조인](../19-semi-anti-join/) — 「있는지만」 볼 때는 `LATERAL` 이 아니라 `EXISTS` 다.
- **「그룹별 상위 N」의 다른 해법**(`ROW_NUMBER`)은 목록의 **29번 주제**, **`EXPLAIN` 읽기**는 **58번 주제**, **인덱스를 타는지**는 **47번 주제**가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **`LATERAL`** — `FROM` 의 서브쿼리가 왼쪽 항목의 현재 행을 참조할 수 있게 하는 키워드.\
  예: `FROM dept d CROSS JOIN LATERAL (SELECT … WHERE e.dept_id = d.id LIMIT 1) t`.
- **파생 테이블(derived table)** — `FROM` 에 놓인 서브쿼리. **`LATERAL` 이 없으면 바깥을 못 본다.**\
  예: `FROM (SELECT id FROM emp) AS t`. 목록의 10번 주제.
- **상관 서브쿼리(correlated subquery)** — 바깥 열을 참조하는 서브쿼리. 값 자리에서는 **1행 1열**만 낼 수 있다.\
  예: `(SELECT d.name FROM dept d WHERE d.id = e.dept_id)`. 11번 주제.
- **`ON true`** — `LEFT JOIN LATERAL` 에서 쓰는 관용구. 조건이 이미 서브쿼리 안에 있어 `ON` 에 쓸 것이 없을 때.\
  예: `LEFT JOIN LATERAL (…) AS t ON true`.
- **그룹별 상위 N(top-N per group)** — 그룹마다 정렬해 앞의 N개만 뽑는 요구.\
  예: 부서별 최고 연봉자. `LATERAL` 의 대표 용도다.
- **중첩 루프(nested loop)** — 왼쪽 행마다 오른쪽을 훑는 조인 알고리즘.\
  예: `Nested Loop … loops=3` — `dept` 3행마다 한 번씩.
- **`loops`** — `EXPLAIN ANALYZE` 가 찍는, 그 노드가 몇 번 실행됐는지의 수.\
  예: `loops=3`. 옆의 `actual rows` 는 **한 번당 평균**이다.
- **집합 반환 함수(set-returning function)** — 행 여러 개를 돌려주는 함수.\
  예: PG 의 `generate_series(1, 3)`. MySQL 에는 없다. 목록의 12번 주제.
- **`Invalidate materialized tables`** — MySQL 계획에 뜨는, 「왼쪽 행이 바뀌면 만들어 둔 것을 버린다」는 표시.\
  예: `Materialize (invalidate on row from d)` — `LATERAL` 의 동작이 그대로 찍힌 것이다.

## 더 들어가면

- **PG 는 함수 앞에서 `LATERAL` 키워드를 생략할 수 있다.** 아래 두 문장이 같은 결과를 냈다(MySQL 은 `generate_series` 자체가 없어 둘 다 `ERROR 1064` 다 — [12번](../12-cartesian-product-cross-join/)).

```text
### SQL: SELECT d.name AS dept, g.i FROM dept d CROSS JOIN generate_series(1, d.id / 10) AS g(i) ORDER BY d.id, g.i;
--- PG 18.6 ---
 dept  | i 
-------+---
 sales | 1
 dev   | 1
 dev   | 2
 hr    | 1
 hr    | 2
 hr    | 3
(6 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '(1, d.id / 10) AS g(i) ORDER BY d.id, g.i' at line 1
```

  **`d.id / 10` 이 왼쪽 행의 값이다** — `LATERAL` 이라고 적지 않았는데 상관 참조가 통했다. 함수 호출은 자동으로 lateral 하게 취급된다.

- **`RIGHT JOIN LATERAL` 도 왼쪽을 참조하지 않으면 통과한다.** 제약은 문법 형태가 아니라 **실제 참조**에 걸린다 — PG 의 `DETAIL` 이 "for a LATERAL reference" 라고 조건을 단 이유다.
- **「그룹별 상위 N」은 세 가지로 쓸 수 있다** — 상관 서브쿼리(N=1 만) · `LATERAL` · `ROW_NUMBER`(목록의 **29번 주제**). 큰 표에서 어느 쪽이 빠른지는 **인덱스가 정렬 순서를 만들어 주느냐**에 달렸다.
