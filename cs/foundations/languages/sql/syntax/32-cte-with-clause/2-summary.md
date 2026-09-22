# sql/32-CTE(`WITH`) — 이름 붙인 서브질의와 가시성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · WITH Queries (CTE)](https://www.postgresql.org/docs/18/queries-with.html) · [PostgreSQL 12 릴리스 노트](https://www.postgresql.org/docs/release/12.0/) · [MySQL 8.4 · WITH (Common Table Expressions)](https://dev.mysql.com/doc/refman/8.4/en/with.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·실행 계획은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 두 개만 썼다. **새로 만든 표가 없다.**\
> **버전** — `WITH` 자체는 두 엔진 모두 오래전부터 있다. 갈리는 것은 **`MATERIALIZED`/`NOT MATERIALIZED`** 로, PG 는 **12 부터**다(릴리스 노트 확인). MySQL 매뉴얼에는 이 문법이 없고 **실제로 `ERROR 1064`** 다.\
> **선행** — [11 서브쿼리 — 스칼라·상관·ANY/ALL](../11-subquery-scalar-correlated-any-all/) · [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/).\
> **이어지는 것** — [33 재귀 CTE](../33-recursive-cte/)가 같은 `WITH` 에 `RECURSIVE` 를 붙인 것이다.

## 한눈에 — 쉽게 말하면

**CTE 는 서브질의에 「이름」을 붙이는 것뿐이다. 새 표를 만드는 것도, 결과를 어딘가에 저장하는 것도 아니다.**

요리로 치면 이렇다.

```text
 파생 테이블 (10번)                       CTE (이 주제)
 = 볶을 때마다 양파를 다시 썬다            = 양파를 한 번 썰어 그릇에 담고 이름표를 붙인다
+---------------------------+            +---------------------------+
| FROM (SELECT ...) a       |            | WITH 썬양파 AS (SELECT ...)|
| JOIN (SELECT ...) b       |            | ... FROM 썬양파 a          |
|       ^^^^^^^^^^          |            |     JOIN 썬양파 b          |
|   똑같은 문장을 두 번 적는다|            |     ^^^^^^   ^^^^^^        |
+---------------------------+            |   이름을 두 번 부를 뿐이다 |
                                         +---------------------------+
```

- **비유** — 긴 문장에 붙이는 **별명**이다. "지난달 매출이 100만 원을 넘은 지점들"이라고 매번 말하는 대신 "**우수지점**"이라고 한 번 정해 두는 것.
- **똑같은 구조다** — 별명을 정했다고 해서 그 목록이 어디 적혀 있는 건 아니다.\
  누가 "우수지점 몇 개야?"라고 물으면 **그때 다시 세어 볼 수도 있고**, 아까 센 것을 기억해 둘 수도 있다.\
  그 "다시 세나, 기억해 두나"가 아래 **최적화 장벽** 절이고, **엔진과 참조 횟수가 그것을 정한다.**

| 비유 | 실체 |
|---|---|
| 별명을 정한다 | `WITH 이름 AS (질의)` |
| 별명은 이 대화 안에서만 통한다 | CTE 이름은 **그 문장 하나** 안에서만 산다 |
| 별명을 정하기 **전에는** 못 쓴다 | 앞의 CTE 만 참조할 수 있다(전방 참조 금지) |
| 별명이 원래 이름을 덮는다 | CTE 이름이 **같은 이름의 실제 표를 가린다** |
| 한 번 세어 두고 계속 쓴다 | **물질화(materialize)** — 최적화 장벽이 선다 |
| 물어볼 때마다 다시 센다 | **인라인(inline)** — 바깥 조건이 안쪽으로 내려간다 |

> **CTE(Common Table Expression, 공통 테이블 식)** — `WITH 이름 AS (SELECT …)` 로 질의 앞에 붙여 두는, **그 문장 안에서만 사는 이름 붙은 서브질의**.\
> 예: `WITH big AS (SELECT * FROM emp WHERE salary >= 400) SELECT * FROM big` 의 `big`.

## 이 주제가 답하려는 질문

1. **CTE 는 파생 테이블([10번](../10-from-clause-aliases-derived-tables/))과 무엇이 다른가?** — 이름이 붙는다는 것 말고, 실제로 달라지는 것이 있나.
2. **CTE 의 이름은 어디서부터 어디까지 보이나?** — 앞의 CTE? 뒤의 CTE? 다음 문장?
3. **CTE 는 최적화 장벽인가?** — 그 답이 **엔진과 버전과 참조 횟수**에 달려 있다는 것을 계획으로 확인할 수 있나.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들은 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

**왜 이 데이터가 이 주제에 맞나.**

- 이 주제는 **데이터가 아니라 「같은 조각을 두 번 쓰는가**」를 본다. 표가 4행·3행으로 작아야 **`EXPLAIN` 한 화면에 계획 전체가 들어온다** — 이 주제의 본문 절반이 계획이다.
- `emp` 에 **기본키 인덱스(`emp_pkey`)가 하나 있다.** 그래서 「바깥 조건이 CTE 안으로 내려갔나」를 **`Index Scan` 이 뜨나 안 뜨나**로 한눈에 구분할 수 있다 — 인덱스가 없으면 둘 다 `Seq Scan` 이라 구분이 안 된다.
- `salary >= 400` 이 **정확히 2행**(`bob`·`dan`)을 고른다. CTE 를 자기 자신과 조인했을 때 답이 1행으로 딱 떨어져, **"두 번 참조"가 제대로 됐는지**를 눈으로 검산할 수 있다.
- `cho.salary` 가 `NULL`, `dan.dept_id` 가 `NULL` 인 것은 여기서는 쓰지 않는다 — [33번](../33-recursive-cte/)의 뿌리 판정(`mgr_id IS NULL`)과 [34번](../34-set-operations-union-intersect-except/)의 중복 접힘에서 다시 쓴다.

## 동작 방식

### 1. CTE 는 **이름을 붙일 뿐**이다

**언제 쓰나** — 서브질의가 길어져 `FROM` 안이 읽히지 않을 때. 먼저 이름을 정하고, 그다음 본문을 쓴다.

```text
(전) 읽는 순서가 안쪽부터다            (후) 읽는 순서가 위에서 아래다
+----------------------------+        +------------------------------+
| SELECT ...                 |        | WITH big AS (                |
|   FROM (SELECT ... ) a     |        |   SELECT ... WHERE salary>=400|
|        ^^^^^^^^^^^         |        | )                            |
|        여기를 먼저 읽어야   |        | SELECT ... FROM big          |
|        바깥이 이해된다      |        |        ^ 이름만 읽으면 된다  |
+----------------------------+        +------------------------------+
```

```text
### SQL: WITH big AS (SELECT id, name, salary FROM emp WHERE salary >= 400) SELECT * FROM big ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | salary              +----+------+--------+
----+------+--------             | id | name | salary |
  2 | bob  |    500              +----+------+--------+
  4 | dan  |    400              |  2 | bob  |    500 |
(2 rows)                         |  4 | dan  |    400 |
                                 +----+------+--------+
```

그림 해설 — **결과는 파생 테이블과 한 행도 다르지 않다.** 달라진 것은 읽는 순서뿐이다.\
비용 — 이름 하나가 늘어난다. 그 이름이 **문장 하나 안에서만** 산다(4번 절).

---

### 2. 이름이 붙으니 **한 번 쓰고 여러 번 참조**할 수 있다 — 10번과 갈리는 자리

**언제 쓰나** — 같은 중간 결과를 두 군데 이상에서 쓸 때. **이것이 파생 테이블로는 안 되는 유일한 것**이다.

```text
 파생 테이블 (10번)                        CTE (이 주제)
 FROM (SELECT ... salary>=400) a           WITH big AS (SELECT ... salary>=400)
 JOIN (SELECT ... salary>=400) b           SELECT ... FROM big a JOIN big b
      ^^^^^^^^^^^^^^^^^^^^^^^^                              ^^^     ^^^
      같은 문장을 통째로 두 번 적었다         이름을 두 번 불렀을 뿐이다
      -> 한쪽만 고치면 조용히 어긋난다        -> 정의가 한 군데라 어긋날 수 없다
```

```text
### SQL: WITH big AS (SELECT id, name, salary FROM emp WHERE salary >= 400)
         SELECT a.name AS x, b.name AS y FROM big a JOIN big b ON a.id < b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  x  |  y                        +-----+-----+
-----+-----                      | x   | y   |
 bob | dan                       +-----+-----+
(1 row)                          | bob | dan |
                                 +-----+-----+

### SQL: SELECT a.name AS x, b.name AS y
         FROM (SELECT id, name, salary FROM emp WHERE salary >= 400) a
         JOIN (SELECT id, name, salary FROM emp WHERE salary >= 400) b ON a.id < b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  x  |  y                        +-----+-----+
-----+-----                      | x   | y   |
 bob | dan                       +-----+-----+
 (1 row)                         | bob | dan |
                                 +-----+-----+
```

그림 해설 — **두 방식의 결과가 같다.** 다른 것은 **정의가 한 군데냐 두 군데냐**다.\
비용 — 정의가 한 군데라 유지보수가 싸진다. 대신 **PG 에서는 참조가 둘이 되는 순간 계획이 달라진다**(7번 절) — 싸진 대가가 계획에 청구된다.

**경계 한 줄** — `FROM` 안에 직접 놓는 서브질의(파생 테이블)의 **별칭 규칙·`VALUES` 문법**은 [10번](../10-from-clause-aliases-derived-tables/)이 정본이고, 여기서는 **이름이 붙었을 때 무엇이 달라지나**만 다룬다.

---

### 3. 이름은 **앞에서 뒤로만** 보인다

**언제 쓰나** — CTE 를 여러 개 이어 쓸 때. 단계마다 이름을 붙여 파이프라인처럼 쓴다.

```text
 WITH a AS ( ... )        <- a 를 정의
    , b AS ( ... a ... )  <- b 는 a 를 볼 수 있다   (뒤에서 앞을 본다)
 SELECT ... FROM b

 WITH a AS ( ... b ... )  <- a 는 b 를 못 본다      (앞에서 뒤를 못 본다)
    , b AS ( ... )
```

```text
### SQL: WITH a AS (SELECT id FROM dept), b AS (SELECT id + 1 AS id FROM a) SELECT * FROM b ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +----+
----                             | id |
 11                              +----+
 21                              | 11 |
 31                              | 21 |
(3 rows)                         | 31 |
                                 +----+

### SQL: WITH a AS (SELECT id FROM b), b AS (SELECT id FROM dept) SELECT * FROM a;
--- PG 18.6 ---
ERROR:  relation "b" does not exist
LINE 1: WITH a AS (SELECT id FROM b), b AS (SELECT id FROM dept) SEL...
                                  ^
DETAIL:  There is a WITH item named "b", but it cannot be referenced from this part of the query.
HINT:  Use WITH RECURSIVE, or re-order the WITH items to remove forward references.
--- MySQL 8.4.10 ---
ERROR 1146 (42S02) at line 1: Table 'study.b' doesn't exist
```

그림 해설 — **PG 의 `DETAIL`·`HINT` 가 이 주제의 두 규칙을 문장으로 말해 준다** — "그런 이름의 `WITH` 항목은 있는데 여기서는 못 본다", "순서를 바꾸거나 `WITH RECURSIVE` 를 쓰라".\
MySQL 은 **그냥 "그런 표 없다**"고만 한다. 같은 벽인데 한쪽만 문을 알려 준다.\
비용 — **MySQL 쪽 메시지는 오타와 구분이 안 된다.** `Table 'study.b' doesn't exist` 만 보고 표 이름을 찾으러 가면 시간을 버린다.

> **전방 참조(forward reference)** — 아직 정의하지 않은 이름을 먼저 쓰는 것.\
> 예: `WITH a AS (SELECT … FROM b), b AS (…)` 에서 `a` 가 `b` 를 부르는 것. **`RECURSIVE` 가 없으면 금지**다([33번](../33-recursive-cte/)).

---

### 4. 이름의 수명은 **문장 하나**다

**언제 쓰나** — "앞에서 만든 CTE 를 다음 질의에서도 쓰자"는 생각이 들 때. **안 된다.**

```text
 문장 1                                문장 2
 WITH t AS (...) SELECT 1;             SELECT * FROM t;
 └─ t 는 여기서 태어나                      ↑
    이 세미콜론에서 죽는다                  없는 이름이다
```

```text
### SQL: WITH t AS (SELECT id FROM dept) SELECT 1;   -- 첫 문장
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 ?column?                        +---+
----------                       | 1 |
        1                        +---+
(1 row)                          | 1 |
                                 +---+

### SQL: SELECT * FROM t;   -- 바로 다음 문장
--- PG 18.6 ---
ERROR:  relation "t" does not exist
LINE 1: ... AS (SELECT id FROM dept) SELECT 1; SELECT * FROM t;
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1146 (42S02) at line 1: Table 'study.t' doesn't exist
```

그림 해설 — **CTE 는 임시 표가 아니다.** 아무 데도 저장되지 않으므로 세미콜론을 넘기면 사라진다.\
반대로 **서브질의 안에 `WITH` 를 또 쓸 수는 있다** — 그 `WITH` 의 이름은 그 괄호 안에서만 산다.

```text
### SQL: SELECT (SELECT COUNT(*) FROM (WITH x AS (SELECT id FROM dept) SELECT * FROM x) AS s) AS n;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +------+
---                              | n    |
 3                               +------+
(1 row)                          |    3 |
                                 +------+
```

비용 — 문장을 넘겨 재사용하고 싶으면 **뷰**([48번 주제](../48-views-and-materialized-views/))나 임시 표다. CTE 로는 못 한다.

---

### 5. CTE 이름은 **같은 이름의 실제 표를 가린다**

**언제 쓰나** — 절대 일부러 쓰지 않는다. **사고로만 일어난다.**

```text
 실제 emp 표                      WITH emp AS (...) 를 쓴 문장 안
+----+------+                    +----+-------+
|  1 | ann  |                    | 99 | ghost |   <- CTE 가 이긴다
|  2 | bob  |   ...              +----+-------+
+----+------+                    실제 emp 는 이 문장에서 보이지 않는다
```

```text
### SQL: WITH emp AS (SELECT 99 AS id, 'ghost' AS name) SELECT * FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+-------+
----+-------                     | id | name  |
 99 | ghost                      +----+-------+
(1 row)                          | 99 | ghost |
                                 +----+-------+
```

그림 해설 — **에러가 나지 않는다.** 두 엔진 모두 조용히 CTE 를 골랐다.\
비용 — **무음 실패다.** 긴 질의 위쪽에 `WITH orders AS (…)` 를 얹어 놓고 아래에서 진짜 `orders` 표를 쓴 줄 알면, 타입도 열 이름도 맞고 값만 틀린다.\
처방 — **CTE 이름에 접두어를 붙인다**(`cte_orders`·`x_orders`). [11번](../11-subquery-scalar-correlated-any-all/)의 "한정자를 붙인다"와 같은 처방이다.

---

### 6. 최적화 장벽 — **PG 는 참조가 한 번이면 인라인한다**(12 부터)

**언제 쓰나** — CTE 로 감쌌더니 느려졌을 때, 혹은 빨라졌을 때. **그 원인이 여기다.**

> **최적화 장벽(optimization fence)** — 옵티마이저가 **벽 너머로 조건을 옮기지 못하게** 되는 경계.\
> 예: 벽이 있으면 `WHERE id = 1` 이 CTE 안으로 못 내려가 **네 행을 다 만든 뒤** 거른다.

PG 문서가 규칙을 문장으로 적는다 — 인용한다.

> "if a `WITH` query is non-recursive and side-effect-free (that is, it is a `SELECT` containing no volatile functions) then it can be folded into the parent query… By default, this happens if the parent query references the `WITH` query just once, but not if it references the `WITH` query more than once."\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

그리고 **이 규칙 자체가 PG 12 에서 들어왔다.**

> "Specifically, CTEs are automatically inlined if they have no side-effects, are not recursive, and are referenced only once in the query… **Previously, CTEs were never inlined and were always evaluated before the rest of the query.**"\
> — [PostgreSQL 12 릴리스 노트](https://www.postgresql.org/docs/release/12.0/)

실제로 계획이 갈린다. **같은 질의, `MATERIALIZED` 한 낱말 차이다.**

```text
 (A) 기본 — 참조 1회 -> 인라인            (B) MATERIALIZED -> 벽이 선다
 WITH c AS (SELECT * FROM emp)            WITH c AS MATERIALIZED (SELECT * FROM emp)
 SELECT * FROM c WHERE id = 1;            SELECT * FROM c WHERE id = 1;
 --- PG 18.6 ---                          --- PG 18.6 ---
  Index Scan using emp_pkey on emp         CTE Scan on c
    Index Cond: (id = 1)                     Filter: (id = 1)
                                             CTE c
                                               ->  Seq Scan on emp
 조건이 CTE 안으로 내려가 인덱스를 탔다     네 행을 다 만든 뒤 걸렀다
```

```text
### SQL: EXPLAIN (COSTS OFF) WITH c AS (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
--- PG 18.6 ---
            QUERY PLAN            
----------------------------------
 Index Scan using emp_pkey on emp
   Index Cond: (id = 1)
(2 rows)
--- MySQL 8.4.10 ---
+-------------------------------------------------------+
| EXPLAIN                                               |
+-------------------------------------------------------+
| -> Rows fetched before execution  (cost=0..0 rows=1)
 |
+-------------------------------------------------------+

### SQL: EXPLAIN (COSTS OFF) WITH c AS MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
--- PG 18.6 ---
       QUERY PLAN        
-------------------------
 CTE Scan on c
   Filter: (id = 1)
   CTE c
     ->  Seq Scan on emp
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1' at line 1

### SQL: EXPLAIN (COSTS OFF) WITH c AS NOT MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
--- PG 18.6 ---
            QUERY PLAN            
----------------------------------
 Index Scan using emp_pkey on emp
   Index Cond: (id = 1)
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NOT MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1' at line 1
```

그림 해설 — **`Index Cond` 와 `Filter` 의 차이가 벽의 유무다.** `Index Cond` 는 인덱스가 걸러 준 것이고, `Filter` 는 이미 만들어진 행을 하나씩 본 것이다.\
MySQL 은 **`MATERIALIZED`·`NOT MATERIALIZED` 를 둘 다 문법 오류로 거부**한다 — 이 손잡이가 아예 없다.\
비용 — ★ **계획은 관찰이지 보장이 아니다.** 위 계획은 **이 데이터·이 통계·이 버전에서 이 옵티마이저가 고른 것**이다. 통계가 바뀌면 달라질 수 있다(「구현 세부사항 대 언어 보장」 절).

---

### 7. **참조가 둘이면 PG 는 벽을 세우고, MySQL 8.4 는 안 세운다**

**언제 쓰나** — CTE 를 두 번 이상 참조할 때. **여기가 두 엔진이 가장 크게 갈리는 자리다.**

```text
### SQL: EXPLAIN (COSTS OFF) WITH c AS (SELECT * FROM emp)
         SELECT a.name, b.name FROM c a JOIN c b ON a.id < b.id;
--- PG 18.6 ---
          QUERY PLAN          
------------------------------
 Nested Loop
   Join Filter: (a.id < b.id)
   CTE c                        <- 한 번만 만들고
     ->  Seq Scan on emp
   ->  CTE Scan on c a          <- 두 번 읽는다
   ->  CTE Scan on c b
(6 rows)
--- MySQL 8.4.10 ---
+---------------------------------------------------------------------------+
| EXPLAIN                                                                   |
+---------------------------------------------------------------------------+
| -> Nested loop inner join  (cost=1.7 rows=3)
    -> Table scan on emp  (cost=0.55 rows=3)
    -> Filter: (emp.id < emp.id)  (cost=0.117 rows=1)
        -> Index range scan on emp (re-planned for each iteration)  (cost=0.117 rows=3)
 |
+---------------------------------------------------------------------------+
```

그림 해설 — **PG 는 `CTE c` 라는 노드를 하나 세우고 두 번 읽었다.** 계획에 `CTE` 라는 낱말이 뜨면 벽이 선 것이다.\
**MySQL 8.4.10 은 `c` 라는 이름이 계획에서 아예 사라졌다** — `emp` 를 두 번 스캔한다. 벽이 없다.

**단 MySQL 도 무조건 펴지는 않는다.** CTE 에 집계가 들어가면 물질화한다.

```text
### SQL: EXPLAIN … WITH s AS (SELECT dept_id, SUM(salary) AS tot FROM emp GROUP BY dept_id)
         SELECT a.dept_id, b.dept_id FROM s a JOIN s b ON a.tot < b.tot;
--- PG 18.6 ---
            QUERY PLAN            
----------------------------------
 Nested Loop
   Join Filter: (a.tot < b.tot)
   CTE s
     ->  HashAggregate
           Group Key: emp.dept_id
           ->  Seq Scan on emp
   ->  CTE Scan on s a
   ->  CTE Scan on s b
(8 rows)
--- MySQL 8.4.10 ---
+----------------------------------------------------------------------------------+
| EXPLAIN                                                                          |
+----------------------------------------------------------------------------------+
| -> Filter: (a.tot < b.tot)  (cost=5.04 rows=0)
    -> Inner hash join (no condition)  (cost=5.04 rows=0)
        -> Table scan on b  (cost=2.5..2.5 rows=0)
            -> Materialize CTE s if needed (query plan printed elsewhere)  (cost=0..0 rows=0)
        -> Hash
            -> Table scan on a  (cost=2.5..2.5 rows=0)
                -> Materialize CTE s if needed  (cost=0..0 rows=0)
                    -> Table scan on <temporary>
                        -> Aggregate using temporary table
                            -> Table scan on emp  (cost=0.55 rows=3)
 |
+----------------------------------------------------------------------------------+
```

비용 — **MySQL 의 `Materialize CTE s if needed` 라는 낱말이 그대로 답이다** — "필요하면 물질화한다". 옵티마이저가 그때그때 정한다.

---

### 8. **`NOT MATERIALIZED` 는 요청이지 명령이 아니다**

**언제 쓰나** — "벽을 치워 달라"고 적었는데 계획이 안 바뀔 때.

PG 문서의 조건은 「**비재귀 + 부작용 없음**」이 먼저다. 그 조건이 깨지면 `NOT MATERIALIZED` 를 적어도 벽이 남는다.

```text
### SQL: EXPLAIN (COSTS OFF) WITH c AS NOT MATERIALIZED (SELECT random() AS r FROM emp) SELECT * FROM c;
--- PG 18.6 ---
       QUERY PLAN        
-------------------------
 CTE Scan on c           <- NOT MATERIALIZED 를 적었는데도 벽이 남았다
   CTE c
     ->  Seq Scan on emp
(3 rows)
```

그리고 그 벽에는 **결과에 걸린 의미**가 있다.

```text
### SQL: WITH c AS NOT MATERIALIZED (SELECT random() AS r) SELECT (SELECT r FROM c) = (SELECT r FROM c) AS same;
--- PG 18.6 ---
 same 
------
 t
(1 row)
```

그림 해설 — `random()` 을 두 번 읽었는데 **같은 값**이 나왔다. 인라인됐다면 두 번 계산돼 달라졌을 수 있다.\
비용 — **휘발성 함수가 든 CTE 는 「몇 번 계산되나」가 결과를 바꾼다.** 그래서 엔진이 인라인을 거부한다 — 성능이 아니라 **정확성** 때문이다.

> **휘발성 함수(volatile function)** — 같은 인자로 불러도 값이 달라질 수 있는 함수.\
> 예: `random()`·`now()`. 몇 번 부르는지가 결과를 바꾸므로 옵티마이저가 함부로 복제·삭제하지 못한다.

---

### 9. MySQL 쪽의 손잡이 — **옵티마이저 힌트**

**언제 쓰나** — MySQL 에서 CTE 를 물질화시키고 싶을 때. `MATERIALIZED` 키워드가 없으니 힌트로 한다.

```text
### SQL: EXPLAIN FORMAT=TREE WITH c AS (SELECT * FROM emp) SELECT /*+ NO_MERGE(c) */ * FROM c WHERE salary >= 400;
--- MySQL 8.4.10 ---
+--------------------------------------------------------------------------+
| EXPLAIN                                                                  |
+--------------------------------------------------------------------------+
| -> Table scan on c  (cost=3.16..3.16 rows=1)
    -> Materialize CTE c  (cost=0.65..0.65 rows=1)
        -> Filter: (emp.salary >= 400)  (cost=0.55 rows=1)
            -> Table scan on emp  (cost=0.55 rows=3)
 |
+--------------------------------------------------------------------------+
```

힌트가 없을 때는 이렇다.

```text
### SQL: EXPLAIN FORMAT=TREE WITH c AS (SELECT * FROM emp) SELECT * FROM c WHERE salary >= 400;
--- MySQL 8.4.10 ---
+--------------------------------------------------------------------------+
| EXPLAIN                                                                  |
+--------------------------------------------------------------------------+
| -> Filter: (emp.salary >= 400)  (cost=0.55 rows=1)
    -> Table scan on emp  (cost=0.55 rows=3)
 |
+--------------------------------------------------------------------------+
```

그림 해설 — `NO_MERGE(c)` 를 주니 `Materialize CTE c` 가 떴다. **벽이 섰다.**\
★ 그런데 **벽 안쪽에 `Filter: (emp.salary >= 400)` 이 여전히 있다** — 조건은 내려갔다. PG 의 `MATERIALIZED` 와 **같은 낱말이 아니다.**\
비용 — 힌트 이름(`MERGE`/`NO_MERGE`)도, 효과의 범위도 PG 와 다르다. **두 엔진의 「장벽」을 같은 것으로 외우면 틀린다.**

## 문법 — 어느 절에서 무엇이 보이나

```sql
-- 기본형
WITH 이름 AS ( SELECT ... )
SELECT ... FROM 이름;

-- 열 이름을 다시 붙인다
WITH d(k, v) AS (SELECT id, name FROM dept)
SELECT k, v FROM d;

-- 여러 개 — 뒤의 것이 앞의 것을 본다 (그 반대는 안 된다)
WITH a AS ( ... ), b AS ( ... a ... )
SELECT ... FROM b;

-- PG 전용 손잡이 (PG 12+)
WITH c AS MATERIALIZED     ( ... )   -- 벽을 세운다
WITH c AS NOT MATERIALIZED ( ... )   -- 벽을 치워 달라고 요청한다

-- MySQL 쪽 손잡이는 힌트다
SELECT /*+ NO_MERGE(c) */ ... FROM c;
```

열 이름 다시 붙이기는 두 엔진에서 같다.

```text
### SQL: WITH d(k, v) AS (SELECT id, name FROM dept) SELECT k, v FROM d ORDER BY k;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 k  |   v                        +----+-------+
----+-------                     | k  | v     |
 10 | sales                      +----+-------+
 20 | dev                        | 10 | sales |
 30 | hr                         | 20 | dev   |
(3 rows)                         | 30 | hr    |
                                 +----+-------+
```

규칙 일곱.

1. **CTE 이름은 그 문장 하나 안에서만 산다.** 세미콜론을 넘기면 없다.
2. **앞의 CTE 만 볼 수 있다.** 전방 참조는 `RECURSIVE` 없이는 금지다([33번](../33-recursive-cte/)).
3. **한 번 정의하고 여러 번 참조**할 수 있다. 파생 테이블과 갈리는 자리가 여기 하나다.
4. **CTE 이름이 같은 이름의 실제 표를 가린다.** 에러 없이.
5. **열 이름은 `이름(a, b)` 로 다시 붙일 수 있다.**
6. **`MATERIALIZED`/`NOT MATERIALIZED` 는 PG 12+ 전용**이다. MySQL 은 `ERROR 1064`.
7. **CTE 는 표가 아니다.** 저장되지 않고, 인덱스를 걸 수 없고, 다음 문장에서 못 쓴다.

읽을 때 붙잡을 것은 **"이 이름이 몇 번 불리나"** 하나다.

```text
 이름이 몇 번 불리나 -> 1 회: PG 는 편다(인라인) · MySQL 도 편다
                     -> 2 회 이상: PG 는 벽을 세운다 · MySQL 8.4 는 그래도 편다
 안에 휘발성이 있나  -> 있으면 PG 는 NOT MATERIALIZED 를 적어도 안 편다
 이름이 표와 겹치나  -> 겹치면 CTE 가 이긴다 (조용히)
```

## 어디서 틀리나

- **CTE 를 임시 표로 착각한다.**\
  다음 문장에서 `SELECT * FROM t` 하면 `relation "t" does not exist` 다. 저장되는 것이 아니다.
- **"CTE 로 감싸면 최적화 장벽이 선다"고 외운다.**\
  **PG 12 부터 틀렸다.** 참조가 한 번이면 편다 — 위 6번 절의 `Index Scan` 이 그 증거다. **버전을 확인하라.**
- **거꾸로 "CTE 는 그냥 이름일 뿐 계획이 같다"고 믿는다.**\
  PG 에서 **참조를 둘로 늘리는 순간** 벽이 선다(7번 절). 같은 CTE 를 한 번 더 부르는 것만으로 계획이 바뀐다.
- **PG 의 `MATERIALIZED` 를 MySQL 로 옮긴다.** `ERROR 1064` 다. MySQL 은 `/*+ NO_MERGE() */` 힌트다.
- **CTE 이름을 실제 표 이름과 같게 짓는다.**\
  **에러가 안 난다.** 두 엔진 다 조용히 CTE 를 고른다 — 무음 실패다.
- **전방 참조를 한다.**\
  PG 는 `HINT` 로 알려 주지만 **MySQL 은 `Table 'study.b' doesn't exist` 라고만 한다** — 오타로 오인하고 표를 찾으러 간다.
- **CTE 안에서 `ORDER BY` 를 하고 바깥 순서를 기대한다.**\
  CTE 의 순서는 보장되지 않는다. 순서는 **가장 바깥 `ORDER BY`** 가 정한다([08번](../08-order-by-null-position-stability/)).
- **CTE 에 인덱스를 기대한다.** CTE 결과에는 인덱스가 없다. 물질화되면 **그 중간 결과 전체를 훑는다.**

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| CTE 이름이 문장 하나 안에서만 산다 | **문법의 정의** | 언어 — 두 엔진 같다 |
| 앞의 CTE 만 참조할 수 있다 | **문법의 정의** | 언어 — 두 엔진 같다(에러 문구만 다르다) |
| CTE 이름이 실제 표를 가린다 | **이름 해석 규칙** | 언어 — 두 엔진 같다 |
| 결과 자체(행·값) | **결과의 정의** | 언어 — 파생 테이블과 한 행도 다르지 않다 |
| **인라인되나 물질화되나** | **옵티마이저의 선택** | 아무도 — 같은 답이 나오는 한 자유다 |
| PG 가 참조 1회면 편다는 것 | **PG 12+ 의 기본 규칙** | PG 문서가 문장으로 적는다. **다른 엔진·다른 버전에는 적용되지 않는다** |
| `MATERIALIZED` 로 벽을 세우는 것 | **PG 의 지시** | PG — 문서가 "force separate calculation" 이라고 적는다 |
| `NOT MATERIALIZED` 로 벽을 치우는 것 | **요청** | 아무도 — 휘발성이 있으면 벽이 남는다(8번 절 실측) |
| MySQL 이 참조 2회에도 편다는 것 | **8.4.10 옵티마이저의 선택** | 아무도 — 매뉴얼에 그런 약속이 없다 |
| 계획에 `CTE Scan`·`Materialize CTE` 가 찍히는 것 | **그 엔진의 표기** | 각 엔진 — 낱말이 서로 다르다 |

- ★ **실행 계획은 관찰이지 보장이 아니다.** 이 절의 계획은 **작성 중 한 번, 제출 직전 한 번** 같은 서버·같은 버전에서 찍었다.\
  **두 번의 출력이 한 글자도 달라지지 않았다** — 통계가 흔들리지 않았다는 뜻이지, 다음에도 같다는 뜻이 아니다.\
  버전이 오르거나 데이터가 커지면 **같은 문장에서 다른 계획이 나올 수 있다.** 외울 것은 계획의 모양이 아니라 "**참조 횟수와 휘발성이 그것을 정한다**"는 규칙이다.
- `EXPLAIN (COSTS OFF)` 로 찍은 것은 그 때문이다 — **비용 수치가 아니라 노드의 모양**이 볼 것이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 중첩 서브질의를 펼 때.** 안쪽부터 읽어야 하던 문장이 위에서 아래로 읽힌다.
- **쓴다 — 같은 중간 결과를 두 번 이상 쓸 때.** 파생 테이블로는 문장을 두 번 적어야 하고, **한쪽만 고치면 조용히 어긋난다.**
- **쓴다 — 단계를 이름으로 남기고 싶을 때.** `WITH 월별매출 AS …, 상위지점 AS …` 는 주석보다 낫다.
- **쓴다 — 재귀가 필요할 때.** `WITH RECURSIVE` 는 CTE 로만 쓸 수 있다([33번](../33-recursive-cte/)).
- **안 쓴다 — 한 번만 쓰는 짧은 서브질의.** 이름 하나가 오히려 읽기를 늘린다.
- **안 쓴다 — 문장을 넘겨 재사용해야 할 때.** 그건 뷰([48번 주제](../48-views-and-materialized-views/))다.
- **주의 — PG 에서 큰 CTE 를 두 번 참조할 때.** 벽이 서서 **중간 결과 전체가 만들어진다.** 조건이 안 내려가므로, 필요하면 `NOT MATERIALIZED` 를 시험해 보고 계획을 확인한다.
- **주의 — 「CTE 로 감싸면 빨라진다/느려진다」는 이식되지 않는다.** PG 에서 얻은 결론을 MySQL 로 옮기지 마라(7번 절).

## 핵심 문장

- CTE 는 **이름을 붙일 뿐**이다 — 표를 만들지도, 저장하지도 않는다.
- 파생 테이블과 갈리는 자리는 하나다 — **한 번 정의하고 여러 번 참조**할 수 있다.
- 이름은 **앞에서 뒤로만** 보이고, 수명은 **문장 하나**다.
- **CTE 이름이 실제 표를 조용히 가린다.** 에러가 안 난다.
- **PG 12 부터 참조가 한 번이면 인라인한다** — "CTE 는 최적화 장벽"은 그 전 버전의 사실이다.
- **참조를 둘로 늘리면 PG 는 벽을 세우고, MySQL 8.4 는 그래도 편다.**
- `MATERIALIZED`/`NOT MATERIALIZED` 는 **PG 전용**이고, **`NOT` 쪽은 요청이지 명령이 아니다.**
- **계획은 관찰이지 보장이 아니다** — 외울 것은 계획이 아니라 참조 횟수·휘발성이라는 규칙이다.

## 관련 자료

- [PostgreSQL 18 · WITH Queries (CTE)](https://www.postgresql.org/docs/18/queries-with.html) — 인라인 규칙과 `MATERIALIZED` 가 한 페이지에 있다.
- [PostgreSQL 12 릴리스 노트](https://www.postgresql.org/docs/release/12.0/) — 인라인이 **12 부터**라는 문장.
- [MySQL 8.4 · WITH (Common Table Expressions)](https://dev.mysql.com/doc/refman/8.4/en/with.html) — MySQL 쪽 `WITH` 의 전부가 이 한 장이다.
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — **경계: 그쪽은 `FROM` 자리에 직접 놓는 서브질의의 별칭 의무·`VALUES` 문법까지, 여기는 그 서브질의에 이름을 붙여 여러 번 부르는 것부터.**
- [11 서브쿼리 — 스칼라·상관·ANY/ALL](../11-subquery-scalar-correlated-any-all/) — **경계: 그쪽은 값 자리의 서브질의(1행 1열 계약)까지, 여기는 표 자리의 서브질의에 이름을 붙이는 것부터.**
- [33 재귀 CTE](../33-recursive-cte/) — **경계: 여기는 `WITH` 의 이름·가시성·장벽까지, 거기는 그 이름이 자기 자신을 부를 때부터.**
- [34 집합 연산 — UNION·INTERSECT·EXCEPT 와 ALL](../34-set-operations-union-intersect-except/) — CTE 의 본문을 `UNION ALL` 로 쓰는 형태가 33번의 뼈대다.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 한 질의 안 여덟 칸의 순서까지, 여기는 그 질의 앞에 이름을 붙여 세우는 것부터.**
- [08 ORDER BY — 정렬 키·NULL 위치·동률](../08-order-by-null-position-stability/) — CTE 안의 `ORDER BY` 가 바깥 순서를 보장하지 않는 이유.
- **뷰와 구체화 뷰**는 [48번 주제](../48-views-and-materialized-views/), **변경문을 품은 CTE**(`RETURNING`)는 [목록의 **54번 주제**](../54-returning-and-data-modifying-cte/), **`EXPLAIN` 계획 트리 읽는 법**은 [58번 주제](../58-explain-plan-tree/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **CTE(Common Table Expression, 공통 테이블 식)** — `WITH 이름 AS (SELECT …)` 로 질의 앞에 붙이는, 그 문장 안에서만 사는 이름 붙은 서브질의.\
  예: `WITH big AS (SELECT * FROM emp WHERE salary >= 400) SELECT * FROM big`.
- **파생 테이블(derived table)** — `FROM` 에 직접 놓은 서브질의. 이름이 없어 별칭을 붙인다.\
  예: `FROM (SELECT id FROM emp) AS t`. [목록의 **10번 주제**](../10-from-clause-aliases-derived-tables/).
- **전방 참조(forward reference)** — 아직 정의하지 않은 이름을 먼저 쓰는 것.\
  예: `WITH a AS (SELECT … FROM b), b AS (…)`. `RECURSIVE` 없이는 금지다.
- **인라인(inline, 펴기)** — 서브질의를 바깥 질의에 녹여 **한 덩어리로 최적화**하는 것.\
  예: `WHERE id = 1` 이 CTE 안으로 내려가 `Index Cond` 가 된 것.
- **물질화(materialize)** — 중간 결과를 **먼저 통째로 만들어 놓고** 바깥이 그것을 읽게 하는 것.\
  예: 계획의 `CTE c` 노드. 그 아래를 다 돌린 뒤 `CTE Scan` 이 읽는다.
- **최적화 장벽(optimization fence)** — 옵티마이저가 벽 너머로 조건을 못 옮기게 되는 경계.\
  예: 벽이 있으면 `WHERE id = 1` 이 `Filter` 로 남아 네 행을 다 본 뒤 거른다.
- **휘발성 함수(volatile function)** — 같은 인자로 불러도 값이 달라질 수 있는 함수.\
  예: `random()`·`now()`. 몇 번 부르는지가 결과를 바꾼다.
- **`CTE Scan`** — PostgreSQL 계획에서 **물질화된 CTE 를 읽는** 노드 이름.\
  예: `CTE Scan on c` 가 뜨면 그 CTE 는 인라인되지 않았다.
- **`Materialize CTE … if needed`** — MySQL `EXPLAIN FORMAT=TREE` 의 표기. "필요하면 물질화한다".\
  예: 집계가 든 CTE 를 두 번 참조했을 때 떴다.
- **옵티마이저 힌트(optimizer hint)** — 질의 안에 `/*+ … */` 로 적어 옵티마이저의 선택을 돌리는 주석.\
  예: MySQL 의 `/*+ NO_MERGE(c) */`.
- **무음 실패(silent failure)** — 에러 없이 틀린 값이 나오는 실패.\
  예: CTE 이름이 실제 표를 가려 엉뚱한 데이터가 나온 것.

## 더 들어가면

- **변경문을 CTE 에 넣을 수 있다** — `WITH moved AS (DELETE FROM a RETURNING *) INSERT INTO b SELECT * FROM moved`. 이건 PG 쪽 이야기이고 [목록의 **54번 주제**](../54-returning-and-data-modifying-cte/)가 정본이다.
- **`WITH` 는 `SELECT` 앞에만 붙는 게 아니다** — `INSERT`/`UPDATE`/`DELETE` 앞에도 붙는다. 같은 54번 주제.
- **PG 14 부터 `SEARCH`/`CYCLE` 이 붙는다** — 재귀 CTE 전용 문법이라 [33번](../33-recursive-cte/)에서 실행 결과와 함께 본다.
- **CTE 가 물질화되면 그 중간 결과에는 인덱스가 없다.** 큰 CTE 를 반복 조인하면 매번 전체를 훑는다 — 그때는 실제 임시 표를 만들고 인덱스를 거는 편이 빠를 수 있다([46번 주제](../46-index-definition-composite-partial-expression/)).
