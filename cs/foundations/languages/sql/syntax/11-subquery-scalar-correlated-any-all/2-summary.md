# sql/11-서브쿼리 — 스칼라·상관·ANY/ALL — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Subquery Expressions](https://www.postgresql.org/docs/18/functions-subquery.html) · [PostgreSQL 18 · Scalar Subqueries](https://www.postgresql.org/docs/18/sql-expressions.html#SQL-SYNTAX-SCALAR-SUBQUERIES) · [MySQL 8.4 · Subqueries](https://dev.mysql.com/doc/refman/8.4/en/subqueries.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 두 개만 썼다. **새로 만든 표가 없다.**\
> **버전** — 이 주제의 문법은 두 엔진 모두 오래전부터 있고, 두 매뉴얼에 도입 버전이 적혀 있지 않아 **버전은 적지 않는다.**\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) · [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/).\
> **복선** — 상관 서브쿼리를 `FROM` 으로 끌어내린 것이 [20 LATERAL](../20-lateral-join/)이고, `EXISTS`/`IN` 만 따로 떼어 본 것이 [19 세미·안티 조인](../19-semi-anti-join/)이다.

## 한눈에 — 쉽게 말하면

**서브쿼리 = 질의 안에 넣은 작은 질의. 그 작은 질의가 「값 하나」를 내느냐 「목록」을 내느냐 「표」를 내느냐로 놓을 자리가 정해진다.**

계산기에 비유하면 이렇다.

```text
 값 하나를 내는 서브쿼리        목록을 내는 서브쿼리          표를 내는 서브쿼리
 (스칼라)                      (IN · ANY · ALL)             (파생 테이블)
+------------------+          +------------------+         +------------------+
| (SELECT MAX(..)) |          | IN (SELECT id ..)|         | FROM (SELECT ..) |
|        ↓         |          |        ↓         |         |        ↓         |
|   숫자 500 처럼  |          |  값 목록처럼     |         |   표 하나처럼    |
|   쓸 수 있다     |          |  비교에 쓴다     |         |   조인할 수 있다 |
+------------------+          +------------------+         +------------------+
 SELECT · WHERE 어디든         WHERE · HAVING               FROM 안에서만
```

- **비유** — 편지 안에 끼워 넣은 쪽지다. 쪽지에 **숫자 하나**만 적혀 있으면 그 자리에 숫자처럼 끼워 쓴다.\
  쪽지에 **이름 목록**이 적혀 있으면 "이 목록 안에 있나"를 물을 수 있다.\
  쪽지가 **표 한 장**이면 그건 이제 쪽지가 아니라 **또 하나의 서류**라서, 서류를 놓는 자리(`FROM`)에만 놓을 수 있다.
- **똑같은 구조다** — 쪽지에 숫자 하나만 적혀 있어야 할 자리에 **두 줄이 적혀 있으면** 읽는 쪽이 멈춘다. 그게 아래의 「2행 이상」 에러다.

| 비유 | 실체 |
|---|---|
| 숫자 하나 적힌 쪽지 | 스칼라 서브쿼리 — **1행 1열** |
| 쪽지가 비어 있다 | 0행을 돌려주는 스칼라 서브쿼리 → **`NULL`** |
| 쪽지에 두 줄이 적혀 있다 | 2행 이상 → **실행 시 에러** |
| 편지를 한 장 쓸 때마다 쪽지를 새로 받아 온다 | **상관 서브쿼리** — 바깥 행마다 다시 돈다 |
| 이름 목록 쪽지 | `IN`/`ANY`/`ALL` 의 서브쿼리 |
| 표 한 장짜리 서류 | 파생 테이블([10번](../10-from-clause-aliases-derived-tables/)) |

> **서브쿼리(subquery)** — 다른 질의 안에 괄호로 들어간 `SELECT` 문.\
> 예: `SELECT name, (SELECT MAX(salary) FROM emp) FROM emp` 의 괄호 안이 서브쿼리다.

## 이 주제가 답하려는 질문

1. **스칼라 서브쿼리가 2행을 돌려주면 왜 에러인가?** — 그리고 그 에러는 **언제** 나나(파싱할 때? 돌릴 때?).
2. **상관 서브쿼리는 정말 바깥 행마다 다시 도나?** — 계획에서 그것을 어떻게 확인하나.
3. **`ANY`/`ALL` 에 `NULL` 이 섞이면 무슨 일이 일어나나?** — 그리고 **빈 집합**일 때는?

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
        |          +-- dan 은 소속이 없다 (dept_id NULL)
        +------------- cho 는 급여가 없다 (salary NULL)
```

**이 주제에서 사고를 내는 것은 `cho` 다.** `cho.salary` 가 `NULL` 이라, `dev` 부서의 급여 목록은 `(NULL)` 한 칸짜리가 된다.\
`ANY`/`ALL` 이 그 목록 위에서 **어떤 값을 넣어도 `TRUE` 가 안 되는** 상태가 된다 — 아래 6번 절이 그것이다.\
`dan` 은 [19번](../19-semi-anti-join/)에서 `NOT IN` 을 무너뜨리는 쪽으로 다시 나온다.

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

### 1. 서브쿼리가 놓이는 자리는 **무엇을 돌려주느냐**로 정해진다

**언제 쓰나** — 서브쿼리를 어디에 적을지 고를 때. 자리를 고르는 게 아니라 **모양이 자리를 정한다.**

```text
서브쿼리가 돌려주는 것       놓을 수 있는 자리            형태
--------------------------   --------------------------   ------------------------
1행 1열 (스칼라)             SELECT · WHERE · ON · ...    (SELECT MAX(salary) ...)
N행 1열 (목록)               WHERE ... IN / ANY / ALL     IN (SELECT id FROM dept)
N행 N열 (표)                 FROM 안에서만                FROM (SELECT ...) AS t
있는지 없는지만              WHERE ... EXISTS             EXISTS (SELECT 1 ...)
```

같은 문 하나에 세 자리를 다 채워 봤다.

```text
### SQL: SELECT COUNT(*) AS n, (SELECT COUNT(*) FROM dept) AS d FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n | d                           +---+------+
---+---                          | n | d    |
 4 | 3                           +---+------+
(1 row)                          | 4 |    3 |
                                 +---+------+
```

그림 해설 — `SELECT` 칸의 `(SELECT COUNT(*) FROM dept)` 는 **숫자 3 을 적어 둔 것과 똑같이** 동작했다.\
비용 — 자리마다 계약이 다르다. **`SELECT` 칸은 1행 1열을 요구하고, `FROM` 칸은 별칭을 요구한다**([10번](../10-from-clause-aliases-derived-tables/)).

---

### 2. 스칼라 서브쿼리 — **1행 1열**이 계약이다

**언제 쓰나** — 집계값 하나를 여러 행에 나란히 붙일 때. "전체 최고 급여를 매 행에 같이 보여 줘" 같은 요구.

```text
(전) emp 4행                     서브쿼리가 내놓은 것      (후) 4행에 같은 값이 붙는다
+------+--------+                +-----+                  +------+-----+
| ann  |    300 |                | 500 |  <- 1행 1열      | ann  | 500 |
| bob  |    500 |                +-----+                  | bob  | 500 |
| cho  |   NULL |                   ↑                     | cho  | 500 |
| dan  |    400 |            SELECT MAX(salary) FROM emp  | dan  | 500 |
+------+--------+                                         +------+-----+
```

```text
### SQL: SELECT name, (SELECT MAX(salary) FROM emp) AS top FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | top                      +------+------+
------+-----                     | name | top  |
 ann  | 500                      +------+------+
 bob  | 500                      | ann  |  500 |
 cho  | 500                      | bob  |  500 |
 dan  | 500                      | cho  |  500 |
(4 rows)                         | dan  |  500 |
                                 +------+------+
```

**계약을 깨면 두 방향으로 터진다.** 행이 많아도, 열이 많아도 터진다.

```text
### SQL: SELECT name, (SELECT id FROM dept) AS d FROM emp ORDER BY id;
--- PG 18.6 ---
ERROR:  more than one row returned by a subquery used as an expression
--- MySQL 8.4.10 ---
ERROR 1242 (21000) at line 1: Subquery returns more than 1 row

### SQL: SELECT (SELECT id, name FROM dept WHERE id = 10) AS two_cols;
--- PG 18.6 ---
ERROR:  subquery must return only one column
LINE 1: SELECT (SELECT id, name FROM dept WHERE id = 10) AS two_cols...
               ^
--- MySQL 8.4.10 ---
ERROR 1241 (21000) at line 1: Operand should contain 1 column(s)
```

| 깨뜨린 계약 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 2행 이상 | `more than one row returned by a subquery used as an expression` | `ERROR 1242 … Subquery returns more than 1 row` |
| 2열 이상 | `subquery must return only one column` | `ERROR 1241 … Operand should contain 1 column(s)` |

그림 해설 — **두 엔진이 같은 두 계약을 같은 두 방향으로 지킨다.** 문구만 다르다.\
비용 — 열 개수는 **문장만 봐도 알 수 있어** 파싱 단계에서 잡히지만, **행 개수는 데이터에 달렸다.** 그래서 다음 절의 사고가 난다.

---

### 3. **2행 에러는 「돌릴 때」 난다** — 오늘 되던 질의가 내일 터진다

**언제 쓰나** — "이 서브쿼리는 항상 1행이야"라고 믿고 스칼라로 쓸 때.

```text
 오늘 — 데이터가 1행                 내일 — 같은 문, 데이터가 2행
 (SELECT x.id FROM (…) x             (SELECT x.id FROM (…) x
    WHERE x.id >= 20)                   WHERE x.id >= 10)
        ↓                                       ↓
       20                              ERROR: more than one row
        ↑                                       ↑
 문장은 한 글자도 안 바뀌었다 — 바뀐 것은 걸린 행의 수다
```

```text
### SQL: SELECT (SELECT x.id FROM (SELECT 10 AS id UNION ALL SELECT 20) AS x WHERE x.id >= 20) AS ok;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 ok                              +------+
----                             | ok   |
 20                              +------+
(1 row)                          |   20 |
                                 +------+

### SQL: SELECT (SELECT x.id FROM (SELECT 10 AS id UNION ALL SELECT 20) AS x WHERE x.id >= 10) AS boom;
--- PG 18.6 ---
ERROR:  more than one row returned by a subquery used as an expression
--- MySQL 8.4.10 ---
ERROR 1242 (21000) at line 1: Subquery returns more than 1 row
```

그림 해설 — **같은 문장이 조건 하나 차이로 통과하기도 하고 터지기도 한다.** 스칼라 계약은 **문법이 아니라 실행 시 검사**다.\
비용 — 테스트 데이터에서는 1행이라 통과하고, 운영 데이터에서 2행이 되면 터진다. **가장 흔한 야간 장애 패턴 중 하나다.**

★ **1행이 보장되지 않으면 스칼라로 쓰지 않는다.** `LIMIT 1` 을 붙이거나(어느 행인지 `ORDER BY` 로 정하고), 애초에 조인이나 `IN` 으로 쓴다.

---

### 4. **0행이면 에러가 아니라 `NULL`** 이다

**언제 쓰나** — 서브쿼리가 아무것도 못 찾았을 때 무엇이 나오는지 예측할 때.

```text
 0행           ->  NULL        (에러가 아니다)
 1행 1열       ->  그 값
 2행 이상      ->  에러
 ↑
 0 과 2 의 처분이 다르다는 것이 이 절의 전부다
```

```text
### SQL: SELECT (SELECT id FROM dept WHERE name = 'nope') AS zero_rows;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 zero_rows                       +-----------+
-----------                      | zero_rows |
                                 +-----------+
(1 row)                          |      NULL |
                                 +-----------+
```

**PG 의 빈 칸과 MySQL 의 `NULL` 은 같은 값이다** — psql 은 `NULL` 을 빈 칸으로 찍는다.

이 `NULL` 이 바깥 조건에 들어가면 **`UNKNOWN` 이 되어 행이 사라진다**([04번](../04-null-three-valued-logic/)).

```text
### SQL: SELECT name FROM emp WHERE dept_id = (SELECT dept_id FROM emp WHERE name = 'zzz');
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            (빈 결과 — 출력이 한 줄도 없다)
------
(0 rows)
```

그림 해설 — 서브쿼리가 `NULL` 을 내놨고, `dept_id = NULL` 이 모든 행에서 `UNKNOWN` 이 되어 **4행이 전부 떨어졌다.**\
비용 — **에러도 경고도 없다.** "조건에 맞는 게 없구나"로 읽히지만 실제로는 **비교 자체가 성립하지 않은 것**이다.

---

### 5. 상관 서브쿼리 — **바깥 행마다 다시 돈다**

**언제 쓰나** — 행마다 다른 값을 계산해 붙일 때. "각자 자기 부서의 최고 급여와 비교"처럼.

> **상관 서브쿼리(correlated subquery)** — 바깥 질의의 열을 참조하는 서브쿼리.\
> 예: `(SELECT d.name FROM dept d WHERE d.id = e.dept_id)` — `e.dept_id` 가 바깥 것이다.

```text
 비상관 서브쿼리                      상관 서브쿼리
 (SELECT MAX(salary) FROM emp)        (SELECT d.name FROM dept d
                                        WHERE d.id = e.dept_id)
        ↓                                      ↓
 바깥을 안 본다                        e.dept_id 가 바깥 것이다
        ↓                                      ↓
 한 번만 돌면 된다                     바깥 행이 바뀌면 답도 바뀐다
        ↓                                      ↓
 계획에 InitPlan / "run only once"     계획에 SubPlan / "dependent"
```

```text
### SQL: SELECT e.name, (SELECT d.name FROM dept d WHERE d.id = e.dept_id) AS dept FROM emp e ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | dept                     +------+-------+
------+-------                   | name | dept  |
 ann  | sales                    +------+-------+
 bob  | sales                    | ann  | sales |
 cho  | dev                      | bob  | sales |
 dan  |                          | cho  | dev   |
(4 rows)                         | dan  | NULL  |
                                 +------+-------+
```

`dan` 은 `dept_id` 가 `NULL` 이라 서브쿼리가 **0행 → `NULL`**(4번 절). **행은 남았다** — 조인이었다면 사라졌을 자리다([13번](../13-inner-join/)).

**「행마다 다시 돈다」를 실행 계획으로 확인한다.**

```text
### SQL: EXPLAIN SELECT e.name, (SELECT MAX(salary) FROM emp) AS top FROM emp e;   -- 비상관
--- PG 18.6 ---
 Seq Scan on emp e  (cost=24.14..45.44 rows=1130 width=36)
   InitPlan 1
     ->  Aggregate  (cost=24.12..24.14 rows=1 width=4)
           ->  Seq Scan on emp  (cost=0.00..21.30 rows=1130 width=4)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Table scan on e  (cost=0.55 rows=3)
-> Select #2 (subquery in projection; run only once)
    -> Aggregate: max(emp.salary)  (cost=0.85 rows=1)
        -> Table scan on emp  (cost=0.55 rows=3)
### SQL: EXPLAIN SELECT e.name, (SELECT d.name FROM dept d WHERE d.id = e.dept_id) AS dept FROM emp e;   -- 상관
--- PG 18.6 ---
 Seq Scan on emp e  (cost=0.00..9253.40 rows=1130 width=64)
   SubPlan 1
     ->  Index Scan using dept_pkey on dept d  (cost=0.15..8.17 rows=1 width=32)
           Index Cond: (id = e.dept_id)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Table scan on e  (cost=0.55 rows=3)
-> Select #2 (subquery in projection; dependent)
    -> Single-row index lookup on d using PRIMARY (id=e.dept_id)  (cost=0.35 rows=1)
```

★ **두 엔진이 같은 구분을 자기 낱말로 찍어 준다** — PG 는 `InitPlan` 대 `SubPlan`, MySQL 은 `run only once` 대 `dependent`.

**몇 번 돌았는지까지 셀 수 있다.**

```text
### SQL: EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF, BUFFERS OFF)
         SELECT e.name, (SELECT d.name FROM dept d WHERE d.id = e.dept_id) FROM emp e;
--- PG 18.6 ---
 Seq Scan on emp e (actual rows=4.00 loops=1)
   SubPlan 1
     ->  Index Scan using dept_pkey on dept d (actual rows=0.75 loops=4)
           Index Cond: (id = e.dept_id)
           Index Searches: 3
```

그림 해설 — **`loops=4`.** `emp` 가 4행이니 서브쿼리가 **네 번** 돌았다. `Index Searches: 3` 은 `dan` 의 `NULL` 은 찾아볼 것도 없이 건너뛰었다는 뜻이다.\
비용 — 바깥 행이 100만이면 서브쿼리가 100만 번 돈다. **안쪽이 인덱스를 못 타면 그대로 곱해진다.**\
다만 **항상 곱해지는 것은 아니다** — `EXISTS` 형태는 옵티마이저가 조인으로 바꿔 버린다([19번](../19-semi-anti-join/)).

**상관 서브쿼리를 `WHERE` 에 쓰면 「행마다 다른 기준」을 만들 수 있다.**

```text
### SQL: SELECT e.name FROM emp e
         WHERE e.salary > (SELECT AVG(x.salary) FROM emp x WHERE x.dept_id = e.dept_id) ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 bob                             +------+
(1 row)                          | bob  |
                                 +------+
```

`sales` 의 평균은 400 이라 `bob`(500) 만 넘는다. `cho` 는 급여가 `NULL` 이라 비교가 `UNKNOWN` 이고, `dan` 은 같은 부서가 자기뿐인데 급여가 400 이라 평균도 400 — `400 > 400` 은 `FALSE` 다.

---

### 6. 상관 서브쿼리의 **별칭 범위** — 안쪽이 이긴다 (조용한 사고)

**언제 쓰나** — 서브쿼리 안에서 열 이름을 **한정자 없이** 쓸 때. 여기가 이 주제에서 가장 조용한 함정이다.

```text
안쪽 SELECT 가 이름을 찾는 순서
   1) 자기 FROM 의 표에서 먼저 찾는다        <- 여기서 찾으면 끝
   2) 없으면 한 겹 바깥으로 나가 찾는다
   ↑
 "안쪽이 이긴다" — 양쪽에 같은 이름이 있으면 바깥은 쳐다보지도 않는다
```

**의도**: 부서마다 사원 수를 센다. `id` 는 `dept.id` 를 뜻한 것이었다.

```text
### SQL: SELECT d.name, (SELECT COUNT(*) FROM emp e WHERE e.dept_id = id) AS n FROM dept d ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name  | n                       +-------+------+
-------+---                      | name  | n    |
 sales | 0                       +-------+------+
 dev   | 0                       | sales |    0 |
 hr    | 0                       | dev   |    0 |
(3 rows)                         | hr    |    0 |
                                 +-------+------+
```

**한정자를 붙이면 맞는 답이 나온다.**

```text
### SQL: SELECT d.name, (SELECT COUNT(*) FROM emp e WHERE e.dept_id = d.id) AS n FROM dept d ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name  | n                       +-------+------+
-------+---                      | name  | n    |
 sales | 2                       +-------+------+
 dev   | 1                       | sales |    2 |
 hr    | 0                       | dev   |    1 |
(3 rows)                         | hr    |    0 |
                                 +-------+------+
```

```text
 쓴 것                  엔진이 읽은 것                결과
 e.dept_id = id     ->  e.dept_id = e.id        ->  0, 0, 0   <- emp 에도 id 가 있다
 e.dept_id = d.id   ->  e.dept_id = d.id        ->  2, 1, 0
                              ↑
              두 문장 다 에러가 없다. 틀린 쪽만 값이 다르다
```

그림 해설 — `emp` 에도 `id` 열이 있으므로 **안쪽에서 이미 찾아졌다.** 바깥의 `dept.id` 는 후보에도 안 올랐다.\
비용 — **에러가 안 난다.** `0, 0, 0` 은 "그런 사원이 없구나"로 읽히고, 타입도 맞고 값도 그럴듯하다. **silent failure 다.**

★ **상관 서브쿼리에서는 모든 열에 한정자를 붙인다.** 이것이 별칭을 쓰는 진짜 이유다 — 짧게 쓰려는 게 아니라 **어느 표의 열인지 못 헷갈리게** 하려는 것이다.

반대 방향, 즉 **바깥에서 안쪽 별칭을 부르는 것은 막힌다.**

```text
### SQL: SELECT e.name FROM emp e WHERE EXISTS (SELECT 1 FROM dept d WHERE d.id = e.dept_id) AND d.name = 'sales';
--- PG 18.6 ---
ERROR:  missing FROM-clause entry for table "d"
LINE 1: ...(SELECT 1 FROM dept d WHERE d.id = e.dept_id) AND d.name = '...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'd.name' in 'EXISTS subquery'
```

**범위는 한 방향이다 — 안쪽은 바깥을 보고, 바깥은 안쪽을 못 본다.**\
[10번](../10-from-clause-aliases-derived-tables/)의 「파생 테이블 안에서 만든 이름은 밖에서 안 보인다」와 같은 벽이다.

---

### 7. `ANY` 와 `ALL` — 목록 전체에 대고 비교한다

**언제 쓰나** — "이 목록 중 **아무거나** 보다 크면" 또는 "이 목록 **전부**보다 크면"을 물을 때.

```text
 x > ANY (목록)   목록 중 하나라도 x 보다 작으면 TRUE   = "최솟값보다 크면"
 x > ALL (목록)   목록 전부가 x 보다 작아야 TRUE        = "최댓값보다 크면"

 x = ANY (목록)  ==  x IN (목록)
 x <> ALL (목록) ==  x NOT IN (목록)
```

`sales` 부서의 급여 목록은 `(300, 500)` 이다.

```text
### SQL: SELECT name, salary FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 10) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   +------+--------+
------+--------                  | name | salary |
 bob  |    500                   +------+--------+
 dan  |    400                   | bob  |    500 |
(2 rows)                         | dan  |    400 |
                                 +------+--------+

### SQL: SELECT name, salary FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 10) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   (빈 결과 — 출력이 한 줄도 없다)
------+--------
(0 rows)
```

그림 해설 — `> ANY (300,500)` 은 **300 보다 크면 통과**라서 `bob`(500)·`dan`(400) 이 남았다.\
`> ALL (300,500)` 은 **500 보다 커야** 하는데 그런 사원이 없다. `bob` 자신도 `500 > 500` 이 `FALSE` 다.

`= ANY` 가 `IN` 과 같은 것을 확인한다. `SOME` 은 `ANY` 의 다른 이름이다.

```text
### SQL: SELECT name FROM emp WHERE dept_id = ANY (SELECT id FROM dept) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 ann                             +------+
 bob                             | ann  |
 cho                             | bob  |
(3 rows)                         | cho  |
                                 +------+

### SQL: SELECT name FROM emp WHERE dept_id = SOME (SELECT id FROM dept) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 ann                             +------+
 bob                             | ann  |
 cho                             | bob  |
(3 rows)                         | cho  |
                                 +------+
```

세 문장(`IN`·`= ANY`·`= SOME`)이 **같은 3행**을 준다. `dan` 은 `dept_id` 가 `NULL` 이라 빠졌다.

열이 둘이면 여기서도 거부한다 — 2번 절의 계약이 그대로다.

```text
### SQL: SELECT name FROM emp WHERE dept_id > ANY (SELECT id, name FROM dept);
--- PG 18.6 ---
ERROR:  subquery has too many columns
LINE 1: SELECT name FROM emp WHERE dept_id > ANY (SELECT id, name FR...
                                           ^
--- MySQL 8.4.10 ---
ERROR 1241 (21000) at line 1: Operand should contain 1 column(s)
```

---

### 8. `NULL` 이 섞이면 `ANY`·`ALL` 이 **둘 다 0행**이 된다

**언제 쓰나** — 비교 대상 목록에 `NULL` 이 있을 수 있을 때. 이 주제의 가장 비싼 함정이다.

`dev` 부서의 급여 목록은 `cho` 하나뿐이고 그 값이 `NULL` 이다 — 즉 목록은 `(NULL)` 이다.

```text
 목록 = (NULL)

 400 > NULL   ->  UNKNOWN
       ↓
 ANY : "하나라도 TRUE 인가?"  -> TRUE 가 하나도 없다 -> TRUE 아님 -> 행 탈락
 ALL : "전부 TRUE 인가?"      -> UNKNOWN 이 섞였다   -> TRUE 아님 -> 행 탈락
       ↓
 반대 방향인 둘이 같은 답(0행)을 낸다 — 이것이 신호다
```

```text
### SQL: SELECT name, salary FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 20) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   (빈 결과 — 출력이 한 줄도 없다)
------+--------
(0 rows)

### SQL: SELECT name, salary FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 20) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   (빈 결과 — 출력이 한 줄도 없다)
------+--------
(0 rows)
```

그림 해설 — **`> ANY` 와 `> ALL` 은 서로 반대인데 결과가 똑같이 0행이다.**\
논리적으로 반대인 두 연산이 같은 답을 내면 그것은 **세 번째 진릿값이 끼어든 흔적**이다([04번](../04-null-three-valued-logic/)).\
비용 — 에러가 없다. "그런 사원이 없구나"로 읽힌다. `<> ALL` 로 쓴 안티 조인이 통째로 비는 것도 같은 이유다([19번](../19-semi-anti-join/)).

★ **처방은 [19번](../19-semi-anti-join/)과 같다** — 목록에서 `NULL` 을 빼거나(`WHERE ... IS NOT NULL`), 그 열에 `NOT NULL` 제약을 걸거나, `EXISTS` 형태로 바꾼다.

---

### 9. **빈 집합**에서는 `ALL` 이 `TRUE`, `ANY` 가 `FALSE` 다

**언제 쓰나** — 서브쿼리가 한 행도 안 낼 수 있을 때. 8번과 **반대로 갈린다.**

```text
 목록 = ()  (빈 집합)

 ALL : "전부 TRUE 인가?"  -> 반례가 없다 -> TRUE    <- 모든 행이 통과한다
 ANY : "하나라도 TRUE?"   -> 후보가 없다 -> FALSE   <- 모든 행이 탈락한다
```

```text
### SQL: SELECT name, salary FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 99) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   +------+--------+
------+--------                  | name | salary |
 ann  |    300                   +------+--------+
 bob  |    500                   | ann  |    300 |
 cho  |                          | bob  |    500 |
 dan  |    400                   | cho  |   NULL |
(4 rows)                         | dan  |    400 |
                                 +------+--------+

### SQL: SELECT name, salary FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 99) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   (빈 결과 — 출력이 한 줄도 없다)
------+--------
(0 rows)
```

★ **`cho` 가 살아남은 것에 주목하라.** `cho.salary` 는 `NULL` 인데도 `> ALL (빈 집합)` 이 `TRUE` 라 통과했다.\
**비교가 한 번도 일어나지 않았기 때문이다** — 비교할 상대가 없으면 `NULL` 도 걸리지 않는다.

```text
 같은 > ALL 인데            목록 = (NULL)   ->  0행    <- 8번
                            목록 = ()       ->  4행    <- 9번
                                  ↑
      "빈 목록"과 "NULL 한 칸짜리 목록"은 전혀 다르다
```

그림 해설 — 이 두 절을 붙여 놓는 이유가 여기 있다. **둘 다 "아무 값도 없다"처럼 보이지만 결과가 정반대다.**\
비용 — "서브쿼리가 비면 아무것도 안 나오겠지"라는 직관이 `ALL` 에서 **정확히 반대로** 틀린다.

---

### 10. `FROM` 의 파생 테이블과의 경계

**언제 쓰나** — 서브쿼리를 표처럼 쓰고 싶을 때. **그 순간 규칙이 바뀐다.**

```text
 값 자리의 서브쿼리                    FROM 자리의 서브쿼리 (파생 테이블)
 (SELECT …)                            FROM (SELECT …) AS t
   - 1행 1열 계약이 있다                 - 행·열 제한이 없다
   - 바깥 행을 참조할 수 있다 (상관)      - 바깥을 못 본다   <- 여기가 다르다
   - 별칭이 필요 없다                    - MySQL 은 별칭이 필수
```

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

그림 해설 — **같은 상관 참조가 `SELECT` 칸에서는 되고 `FROM` 칸에서는 안 된다.**\
`SELECT` 칸의 서브쿼리는 이미 만들어진 바깥 행 위에서 계산되지만, `FROM` 항목들은 **서로 형제**라 아직 "바깥 행"이라는 게 없다([10번](../10-from-clause-aliases-derived-tables/)).\
비용 — 그래서 `FROM` 에서 상관 참조를 하려면 **`LATERAL` 로 따로 표시**해야 한다 — PG 의 `HINT` 가 그 말을 문장으로 해 준다([20번](../20-lateral-join/)).

**경계 한 줄** — 파생 테이블의 별칭·`VALUES` 문법은 [10번](../10-from-clause-aliases-derived-tables/)이 정본이고, 여기서는 **값 자리의 서브쿼리**만 다룬다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
-- 값 자리 (스칼라) — 1행 1열
SELECT name, (SELECT MAX(salary) FROM emp) FROM emp;
WHERE  salary > (SELECT AVG(salary) FROM emp)

-- 목록 자리 — N행 1열
WHERE  dept_id IN  (SELECT id FROM dept)
WHERE  salary  > ANY (SELECT salary FROM emp WHERE dept_id = 10)   -- SOME 은 동의어
WHERE  salary  > ALL (SELECT salary FROM emp WHERE dept_id = 10)

-- 표 자리 — 파생 테이블 (10번 주제)
FROM   (SELECT ...) AS t
```

규칙 일곱.

1. **스칼라 서브쿼리는 1행 1열**이다. 2열 이상은 파싱 단계, **2행 이상은 실행 단계**에서 터진다.
2. **0행은 에러가 아니라 `NULL`** 이다. 그 `NULL` 이 바깥 조건에 들어가면 행이 조용히 사라진다.
3. **상관 서브쿼리는 바깥 행마다 다시 돈다.** 계획에 `SubPlan`(PG) / `dependent`(MySQL) 로 찍힌다.
4. **이름은 안쪽부터 찾는다.** 안쪽 표에 같은 이름이 있으면 바깥은 보지도 않는다 — **한정자를 붙인다.**
5. **범위는 한 방향이다.** 안쪽은 바깥을 보고, 바깥은 안쪽 별칭을 못 본다.
6. **`= ANY` 는 `IN`, `<> ALL` 은 `NOT IN`** 이다. `SOME` 은 `ANY` 의 동의어다.
7. **`NULL` 이 섞인 목록에서는 `ANY` 도 `ALL` 도 0행**, **빈 목록에서는 `ALL` 이 전부 통과**다.

읽을 때 붙잡을 것은 **"이 서브쿼리가 몇 행 몇 열을 내나"** 하나다.

```text
 몇 열인가   ->  2열 이상이면 값 자리에 못 쓴다 (파싱 때 터진다)
 몇 행인가   ->  0 이면 NULL · 1 이면 그 값 · 2 이상이면 에러 (돌릴 때 터진다)
 바깥을 보나 ->  보면 상관 — 바깥 행마다 다시 돈다
```

## 어디서 틀리나

- **"항상 1행"이라고 믿고 스칼라로 쓴다.**\
  테스트에서는 1행이라 통과하고 운영에서 2행이 되면 `more than one row returned` 로 터진다. **행 수가 보장되지 않으면 쓰지 않는다.**
- **0행을 에러로 기대한다.**\
  0행은 조용히 `NULL` 이다. 그 뒤의 `= NULL` 비교가 전부 `UNKNOWN` 이 되어 결과가 통째로 빈다.
- **상관 서브쿼리에서 한정자를 뺀다.**\
  `WHERE e.dept_id = id` 가 안쪽 `emp.id` 로 붙어 `0, 0, 0` 이 나왔다. **에러가 안 난다.**
- **바깥에서 안쪽 별칭을 부른다.**\
  `EXISTS (SELECT 1 FROM dept d …) AND d.name = 'sales'` 는 `missing FROM-clause entry for table "d"` 다.
- **`NULL` 이 섞인 목록에 `ANY`/`ALL` 을 쓴다.**\
  **둘 다 0행**이 된다. 반대인 두 연산이 같은 답을 내면 `NULL` 을 의심한다.
- **빈 목록에서 `ALL` 이 0행일 거라 생각한다.**\
  정반대로 **전부 통과**한다. `> ALL (빈 집합)` 은 `cho` 의 `NULL` 급여까지 통과시켰다.
- **`FROM` 안의 서브쿼리에서 바깥 열을 참조한다.**\
  `LATERAL` 없이는 안 된다([20번](../20-lateral-join/)). PG 는 `HINT` 로 그 말을 해 주고 MySQL 은 `Unknown column` 이라고만 한다.
- **상관 서브쿼리가 느리다고 단정한다.**\
  `EXISTS` 형태는 옵티마이저가 세미 조인으로 바꾼다([19번](../19-semi-anti-join/)). **계획을 보고 판단한다.**

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 스칼라 서브쿼리가 1행 1열이어야 한다 | **결과의 정의** | 언어 — 두 엔진이 같은 두 계약을 지킨다 |
| 0행이면 `NULL` | **결과의 정의** | 언어 |
| `NULL` 이 섞인 `ANY`/`ALL` 이 0행 | **결과의 정의** | 언어 — 3값 논리에서 따라 나온다 |
| 빈 집합에서 `ALL` 이 `TRUE` | **결과의 정의** | 언어 |
| 상관 서브쿼리를 **실제로 N번 도는가** | 옵티마이저의 선택 | 아무도 — 조인으로 바꿔 한 번에 끝낼 수도 있다 |
| 계획에 `InitPlan`/`SubPlan` 중 무엇이 찍히나 | **그 엔진의 표기** | PG 의 표기다. MySQL 은 `run only once`/`dependent` 라고 쓴다 |
| 2행 에러가 **언제** 나는가 | 실행 시점 | 언어 — 행 수는 데이터에 달렸으므로 파싱으로는 못 잡는다 |

- **「바깥 행마다 다시 돈다」는 의미론이지 실행 방식이 아니다.** 결과가 그렇게 정의된다는 뜻이고, 엔진은 같은 답이 나오는 한 어떻게 돌든 자유다.\
  위 `loops=4` 는 **이 데이터·이 통계에서 PG 가 고른 방법**이다. 통계가 바뀌면 다른 계획이 나올 수 있다.
- 위 `EXPLAIN` 의 추정 행 수(`rows=1130`·`rows=1270`)는 **통계가 없을 때의 기본값**이다. 여기서 볼 것은 **비용 수치가 아니라 계획의 모양**이다.\
  ★ **같은 서버·같은 버전에서 두 번 찍었더니 MySQL 의 추정 행 수가 `rows=4` 에서 `rows=3` 으로 바뀌어 있었다**(PG 쪽은 한 글자도 안 달라졌다).\
  계획은 **버전이 아니라 통계에 달렸다** — 위에 실은 것은 **제출 전 재확인 시점의 출력**이고, `InitPlan`/`SubPlan`·`run only once`/`dependent` 구분은 두 번 다 같았다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 집계값 하나를 행마다 붙일 때.** `(SELECT MAX(salary) FROM emp)` 는 조인보다 읽기 쉽다.
- **쓴다 — 행마다 기준이 다를 때.** "자기 부서 평균보다 높은 사원"은 상관 서브쿼리가 가장 곧다.
- **쓴다 — 값 하나만 필요할 때.** 조인은 **행을 늘리지만** 스칼라 서브쿼리는 안 늘린다([13번](../13-inner-join/)의 팬아웃).
- **안 쓴다 — 여러 열이 필요할 때.** 스칼라는 1열이라 두 번 써야 한다. 그땐 조인이나 [`LATERAL`](../20-lateral-join/)이다.
- **안 쓴다 — 1행이 보장 안 될 때.** `LIMIT 1` 로 덮지 말고 요구사항을 다시 본다 — **어느 행인지**가 정해지지 않은 것이다.
- **안 쓴다 — "있는지만" 물을 때.** `EXISTS` 가 정확한 도구다([19번](../19-semi-anti-join/)).
- **주의 — `ANY`/`ALL` 은 `NULL` 에 약하다.** 목록에 `NULL` 이 섞일 수 있으면 `EXISTS` 형태를 쓴다.

## 핵심 문장

- 서브쿼리가 놓일 자리는 **무엇을 돌려주느냐**가 정한다 — 1행 1열이면 값 자리, 목록이면 `IN`/`ANY`/`ALL`, 표면 `FROM`.
- **2열 이상은 파싱 때, 2행 이상은 돌릴 때** 터진다. 그래서 스칼라 서브쿼리의 사고는 **운영에서 처음 난다.**
- **0행은 에러가 아니라 `NULL`** 이다. 그 `NULL` 이 바깥 비교를 전부 `UNKNOWN` 으로 만들어 결과를 비운다.
- 상관 서브쿼리는 **바깥 행마다 다시 돈다** — PG 는 `SubPlan`·`loops=4`, MySQL 은 `dependent` 로 찍어 준다.
- **이름은 안쪽부터 찾는다.** 한정자를 빼면 `0, 0, 0` 이 **에러 없이** 나온다.
- **`NULL` 이 섞인 목록에서는 `> ANY` 도 `> ALL` 도 0행**이고, **빈 목록에서는 `> ALL` 이 전부 통과**한다.
- `FROM` 안의 서브쿼리는 **바깥을 못 본다.** 그 벽에 난 문이 [`LATERAL`](../20-lateral-join/)이다.

## 관련 자료

- [PostgreSQL 18 · Subquery Expressions](https://www.postgresql.org/docs/18/functions-subquery.html) — `EXISTS`·`IN`·`ANY`/`SOME`·`ALL` 의 정의.
- [PostgreSQL 18 · Scalar Subqueries](https://www.postgresql.org/docs/18/sql-expressions.html#SQL-SYNTAX-SCALAR-SUBQUERIES) — 1행 1열 계약과 0행의 `NULL`.
- [MySQL 8.4 · Subqueries](https://dev.mysql.com/doc/refman/8.4/en/subqueries.html) — 스칼라·비교 연산자·`ANY`/`ALL` 이 한 장에 있다.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 여덟 칸의 순서까지, 여기는 그 칸 안에 질의를 하나 더 넣었을 때부터.**
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `UNKNOWN` 의 계산 규칙까지, 여기는 그것이 `ANY`/`ALL` 을 어떻게 무너뜨리나부터.**
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — **경계: 그쪽은 `FROM` 자리의 서브쿼리(별칭·`VALUES`)까지, 여기는 값 자리의 서브쿼리부터.**
- [13 INNER JOIN](../13-inner-join/) — 조인은 행을 늘리고 스칼라 서브쿼리는 안 늘린다.
- [19 세미·안티 조인](../19-semi-anti-join/) — **경계: 여기는 서브쿼리 일반의 계약까지, 거기는 `EXISTS`/`IN`/`NOT IN` 의 선택과 계획부터.**
- [20 LATERAL 조인](../20-lateral-join/) — **경계: 여기는 값 자리의 상관 참조까지, 거기는 그 상관 참조를 `FROM` 으로 내리는 것부터.**
- [05 NULL 비교 — IS NULL·IS DISTINCT FROM·NULL 안전 등호](../05-null-comparison-is-distinct-from/) — **경계: 그쪽은 `NULL` 을 비교하는 연산자까지, 여기는 그 `NULL` 이 `ANY`/`ALL` 을 어떻게 무너뜨리나부터.**
- **CTE(`WITH`)** 는 목록의 **32번 주제**가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **서브쿼리(subquery)** — 다른 질의 안에 괄호로 들어간 `SELECT` 문.\
  예: `SELECT name, (SELECT MAX(salary) FROM emp) FROM emp` 의 괄호 안.
- **스칼라 서브쿼리(scalar subquery)** — **1행 1열**을 돌려주어 값처럼 쓰이는 서브쿼리.\
  예: `(SELECT MAX(salary) FROM emp)` 가 `500` 자리에 끼워진다.
- **상관 서브쿼리(correlated subquery)** — 바깥 질의의 열을 참조하는 서브쿼리. 바깥 행마다 답이 달라진다.\
  예: `(SELECT d.name FROM dept d WHERE d.id = e.dept_id)` — `e.dept_id` 가 바깥 것이다.
- **비상관 서브쿼리(uncorrelated subquery)** — 바깥을 참조하지 않아 한 번만 돌면 되는 서브쿼리.\
  예: `(SELECT MAX(salary) FROM emp)` — 바깥이 어떤 행이든 답이 같다.
- **파생 테이블(derived table)** — `FROM` 에 놓인 서브쿼리. 표처럼 쓰이고 **바깥을 못 본다.**\
  예: `FROM (SELECT id, name FROM emp) AS t`. 목록의 10번 주제.
- **`ANY` / `SOME`** — 목록 중 **하나라도** 비교가 `TRUE` 면 `TRUE`. 둘은 같은 뜻이다.\
  예: `salary > ANY (300,500)` 은 300 보다 크면 통과한다.
- **`ALL`** — 목록 **전부**에 대해 비교가 `TRUE` 여야 `TRUE`.\
  예: `salary > ALL (300,500)` 은 500 보다 커야 통과한다.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
  예: `400 > NULL`. `WHERE` 는 이것을 `FALSE` 와 똑같이 버린다.
- **`InitPlan` / `SubPlan`** — PostgreSQL 계획에서 비상관 / 상관 서브쿼리에 붙는 이름.\
  예: `SubPlan 1 … loops=4` 는 바깥 4행마다 한 번씩 돌았다는 뜻이다.
- **`loops`** — `EXPLAIN ANALYZE` 가 찍는, 그 노드가 몇 번 실행됐는지의 수.\
  예: `loops=4` — `emp` 4행마다 한 번씩.
- **silent failure(무음 실패)** — 에러 없이 틀린 값이 나오는 실패.\
  예: 한정자를 빼서 사원 수가 `0, 0, 0` 으로 나온 것. 타입도 맞고 값도 그럴듯하다.
- **한정자(qualifier)** — 열 이름 앞에 붙이는 표·별칭 이름.\
  예: `id` 대신 `d.id`. 상관 서브쿼리에서는 이것이 필수다.

## 더 들어가면

- **`EXISTS` 는 `SELECT` 목록을 아예 계산하지 않는다.** `SELECT 1/0` 을 넣어도 0 으로 나누지 않는다 — 그 증거는 [19번](../19-semi-anti-join/)에 있다.
- **상관 서브쿼리를 `FROM` 으로 내리면** 여러 열·여러 행을 한 번에 받을 수 있다. 그것이 [`LATERAL`](../20-lateral-join/)이다.
- **「행마다 상위 N개」는 세 가지로 쓸 수 있다** — 상관 서브쿼리 · `LATERAL` · 윈도우 함수(`ROW_NUMBER`, 목록의 **29번 주제**). 셋의 선택 기준은 29번이 정본이다.
