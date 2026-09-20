# sql/10-FROM 절 — 테이블 별칭·파생 테이블 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 Derived Tables](https://dev.mysql.com/doc/refman/8.4/en/derived-tables.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `SELECT emp.id, emp.name FROM emp e WHERE emp.salary >= 400;` 는 통과하는가

**통과하지 않는다. 별칭을 붙이면 원래 이름은 가려진다.**

```text
### SQL: SELECT emp.id, emp.name FROM emp e WHERE emp.salary >= 400;
--- PG 18.6 ---
ERROR:  invalid reference to FROM-clause entry for table "emp"
LINE 1: SELECT emp.id, emp.name FROM emp e WHERE emp.salary >= 400;
               ^
HINT:  Perhaps you meant to reference the table alias "e".
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'emp.id' in 'field list'
```

**왜 그런가** — 별칭은 이름을 *추가*하는 게 아니라 **갈아 끼운다.**

```text
(전) FROM 을 읽기 전            (후) FROM emp e 를 읽은 뒤
+---------------------+       +---------------------+
| 아는 이름: (없음)    |       | 아는 이름: e         |
+---------------------+       |            emp -> X  |
                              +---------------------+
```

PG 의 `HINT` 가 이걸 그대로 말해 준다 — **"별칭 `e` 를 부르려던 것 아닌가."**\
MySQL 은 힌트 없이 "그런 열 없다"고만 한다. 같은 판정인데 안내가 다르다.

별칭을 붙이면 **전부 별칭으로 통일**한다. 섞어 쓸 방법은 없다.

```text
### SQL: SELECT e.id, e.name FROM emp e WHERE e.salary >= 400 ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  2 | bob                        +----+------+
  4 | dan                        |  2 | bob  |
(2 rows)                         |  4 | dan  |
                                 +----+------+
```

---

### 2. `WHERE e.salary` 는 되고 `WHERE annual` 은 안 되는 이유

**테이블 별칭은 1번 칸에서 태어나고 열 별칭은 5번 칸에서 태어나기 때문이다.**

```text
칸       테이블 별칭 e     열 별칭 annual
1 FROM      태어난다           -
2 WHERE       보인다        안 보인다     <- 갈리는 자리
3 GROUP BY    보인다          보인다
4 HAVING      보인다      PG X / MySQL O
5 SELECT      보인다        태어난다
6 DISTINCT    보인다          보인다
7 ORDER BY    보인다          보인다
8 LIMIT       보인다          보인다
```

**「별칭」이라는 한 낱말에 성질이 다른 두 가지가 들어 있다.**

| | 어디서 태어나나 | 어디서 보이나 |
|---|---|---|
| 테이블 별칭 `FROM emp e` | 1번 칸 | 2~8번 칸 **전부** |
| 열 별칭 `salary * 12 AS annual` | 5번 칸 | 6~8번 칸 (+ `GROUP BY` 는 확장) |

```text
### SQL: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 1: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
                                                    ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'annual' in 'where clause'
```

여덟 칸의 순서 자체는 [01번](../01-logical-query-processing-order/)이 정본이다.\
**경계: 거기는 칸의 순서까지, 여기는 1번 칸이 이름 공간을 어떻게 만드나부터.**

---

### 3. 열 별칭을 `WHERE` 에서 쓰는 방법

**한 겹 감싼다.** 안쪽 질의가 1번 칸으로 내려가면, 바깥에서 `annual` 은 별칭이 아니라 **열**이다.

```text
     겹치기 전                          한 겹 감싼 뒤
+------------------------+       +---------------------------------+
| 1 FROM   emp           |       | 1 FROM  (안쪽 질의 전체) AS t    |
| 2 WHERE  annual > 4000 | X     |         -> 여기서 annual 은      |
| 5 SELECT ... AS annual |       |            이미 "t 의 열"이다     |
+------------------------+       | 2 WHERE  t.annual > 4000        | O
   annual 이 아직 없다            +---------------------------------+
```

```text
### SQL: SELECT t.annual FROM (SELECT salary * 12 AS annual FROM emp) AS t
         WHERE t.annual > 4000 ORDER BY t.annual;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual                          +--------+
--------                         | annual |
   4800                          +--------+
   6000                          |   4800 |
(2 rows)                         |   6000 |
                                 +--------+
```

같은 처방이 **집계 결과를 다시 거를 때**도 쓰인다. `HAVING` 에서 별칭이 PG 에서 안 되는 문제([03번](../03-where-vs-having/))도 이렇게 풀린다.

```text
### SQL: SELECT t.dept_id, t.cnt FROM (SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id) AS t
         WHERE t.cnt >= 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   2                   +---------+-----+
(1 row)                          |      10 |   2 |
                                 +---------+-----+
```

**이 한 형태가 SQL 에서 「칸 순서 때문에 막히는」 문제 대부분의 해법이다.**

---

### 4. 별칭 없는 파생 테이블 — 두 엔진에서 각각

**PG 18.6 은 통과하고, MySQL 8.4.10 은 `ERROR 1248` 이다.**

```text
### SQL: SELECT * FROM (SELECT id, name FROM emp WHERE salary >= 400) ORDER BY id;
--- PG 18.6 ---
 id | name 
----+------
  2 | bob
  4 | dan
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1248 (42000) at line 1: Every derived table must have its own alias
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 별칭 없는 파생 테이블 | **통과** | **`ERROR 1248`** |

MySQL 의 에러 문구가 곧 규칙이다 — **"모든 파생 테이블은 자기 별칭을 가져야 한다."**

**깨지는 방향이 한쪽뿐이다.**

```text
PG 에서 쓴 질의를 MySQL 로            MySQL 에서 쓴 질의를 PG 로
        │                                    │
        ▼                                    ▼
 별칭이 없으면 ERROR 1248             깨지지 않는다
```

★ **그러므로 언제나 붙인다.** 양쪽에서 돌고, 열을 가리킬 때도 읽기 쉽다.

```text
### SQL: SELECT * FROM (SELECT id, name FROM emp WHERE salary >= 400) AS t ORDER BY t.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  2 | bob                        +----+------+
  4 | dan                        |  2 | bob  |
(2 rows)                         |  4 | dan  |
                                 +----+------+
```

> **버전 주의** — 두 매뉴얼 어느 쪽도 이 규칙이 「몇 버전부터」인지 적지 않는다.\
> 위 판정은 **PG 18.6 과 MySQL 8.4.10 에서 실제로 돌려 본 것**이고, 다른 버전은 다시 돌려 봐야 한다.

---

### 5. 파생 테이블 안에서 바깥 행을 참조하면

**통과하지 않는다. 그리고 PostgreSQL 이 문을 알려 준다 — `LATERAL` 로 표시하라고.**

```text
### SQL: SELECT * FROM emp e, (SELECT * FROM dept WHERE id = e.dept_id) AS d;
--- PG 18.6 ---
ERROR:  invalid reference to FROM-clause entry for table "e"
LINE 1: ...LECT * FROM emp e, (SELECT * FROM dept WHERE id = e.dept_id)...
                                                             ^
DETAIL:  There is an entry for table "e", but it cannot be referenced from this part of the query.
HINT:  To reference that table, you must mark this subquery with LATERAL.
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'e.dept_id' in 'where clause'
```

**왜 그런가** — `FROM` 에 나란히 적힌 항목들은 **형제**다. 형제는 서로를 모른다.

```text
FROM emp e ,  (SELECT ... WHERE id = e.dept_id) AS d
      │                              │
      └──────── 형제 관계 ───────────┘
      둘이 "동시에" 만들어진다 — d 를 만들 때 e 의 "현재 행" 같은 건 없다
```

**이 벽은 의도된 것이다.** 형제가 서로를 모르기 때문에 엔진이 `FROM` 항목을 **어떤 순서로든** 계산할 수 있다.\
순서를 자유롭게 고를 수 있어야 조인 순서 최적화가 성립한다.

두 에러의 성격이 다르다는 점도 볼 값어치가 있다.

| | 무슨 말인가 |
|---|---|
| PG 18.6 | **"그 표는 있다. 다만 이 자리에서는 못 부른다. 부르려면 `LATERAL` 을 써라."** — 벽과 문을 둘 다 알려 준다 |
| MySQL 8.4.10 | **"`e.dept_id` 라는 열을 모른다."** — 벽만 있고 문 얘기는 없다 |

벽에 난 문이 `LATERAL` 이고 목록의 **20번 주제**다. 바깥 행마다 도는 서브쿼리 일반은 목록의 **11번 주제**다.\
여기서 인출할 것은 **"`FROM` 의 형제끼리는 서로를 모른다"** 한 줄이다.

---

### 6. 파생 테이블 안의 별칭을 바깥에서 부를 수 있는가

**못 부른다. 괄호가 이름 공간의 벽이다.**

```text
### SQL: SELECT e1.name FROM (SELECT * FROM (SELECT * FROM emp) AS e1) AS e2;
--- PG 18.6 ---
ERROR:  missing FROM-clause entry for table "e1"
LINE 1: SELECT e1.name FROM (SELECT * FROM (SELECT * FROM emp) AS e1...
               ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'e1.name' in 'field list'
```

```text
SELECT e1.name                                       <- 여기서 부를 수 있는 이름: e2 뿐
FROM ( SELECT *                                      <- 이 안에서 부를 수 있는 이름: e1
       FROM ( SELECT * FROM emp ) AS e1
     ) AS e2

   바깥이 보는 것은 e2 의 "출력 열"이지 e2 안의 별칭이 아니다
```

**왜 이게 좋은가** — 격벽이 있어서 안쪽 이름을 바깥과 겹치게 지어도 안전하다.\
중첩 질의를 조립할 때 이름 충돌을 걱정하지 않아도 된다.

중첩 자체는 잘 돈다 — 안쪽부터 바깥으로 차례로 끝난다.

```text
### SQL: SELECT e2.name FROM (SELECT * FROM (SELECT * FROM emp WHERE salary IS NOT NULL) AS e1
         WHERE e1.dept_id IS NOT NULL) AS e2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 ann                             +------+
 bob                             | ann  |
(2 rows)                         | bob  |
                                 +------+
```

`cho`(급여 `NULL`) 는 안쪽에서, `dan`(부서 `NULL`) 은 중간에서 잘렸다.

---

### 7. `VALUES` 리스트 — (A)와 (B)는 각각 어디서 도는가

**(A)는 PG 에서만, (B)는 MySQL 에서만 돈다. 서로를 정확히 거부한다.**

```text
### SQL: SELECT * FROM (VALUES (1,'x'),(2,'y')) AS v(a,b);
--- PG 18.6 ---
 a | b 
---+---
 1 | x
 2 | y
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  '(1,'x'),(2,'y')) AS v(a,b)' at line 1

### SQL: SELECT * FROM (VALUES ROW(1,'x'),ROW(2,'y')) AS v(a,b);
--- PG 18.6 ---
ERROR:  syntax error at or near "1"
LINE 1: SELECT * FROM (VALUES ROW(1,'x'),ROW(2,'y')) AS v(a,b);
                                  ^
--- MySQL 8.4.10 ---
+---+---+
| a | b |
+---+---+
| 1 | x |
| 2 | y |
+---+---+
```

| 행 생성자 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `VALUES (1,'x'),(2,'y')` | ✓ | **✗ `ERROR 1064`** |
| `VALUES ROW(1,'x'),ROW(2,'y')` | **✗ 구문 오류** | ✓ |

**둘 다 `ERROR 1064` 급 문법 오류다** — 파서가 상대의 표기를 아예 모른다. 시끄럽게 터지는 것이 다행이다.

**이식성이 필요하면 `VALUES` 를 쓰지 않는다.** `SELECT ... UNION ALL SELECT ...` 는 양쪽 다 돈다.

```text
### SQL: SELECT d.name AS dept, q.q FROM dept d
         CROSS JOIN (SELECT 1 AS q UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) AS q
         ORDER BY d.id, q.q;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | q                       +-------+---+
-------+---                      | dept  | q |
 sales | 1                       +-------+---+
 sales | 2                       | sales | 1 |
 sales | 3                       | sales | 2 |
 sales | 4                       | sales | 3 |
 dev   | 1                       | sales | 4 |
 dev   | 2                       | dev   | 1 |
 dev   | 3                       | dev   | 2 |
 dev   | 4                       | dev   | 3 |
 hr    | 1                       | dev   | 4 |
 hr    | 2                       | hr    | 1 |
 hr    | 3                       | hr    | 2 |
 hr    | 4                       | hr    | 3 |
(12 rows)                        | hr    | 4 |
                                 +-------+---+
```

3 × 4 = 12행. 상수 표를 조인 대상으로 쓰는 것은 [12번](../12-cartesian-product-cross-join/)이 정본이다.

---

### 8. `SELECT id FROM emp e JOIN dept d ON e.dept_id = d.id;` 의 결과

**두 엔진 다 「모호하다」고 거부한다.**

```text
### SQL: SELECT id FROM emp e JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---
ERROR:  column reference "id" is ambiguous
LINE 1: SELECT id FROM emp e JOIN dept d ON e.dept_id = d.id;
               ^
--- MySQL 8.4.10 ---
ERROR 1052 (23000) at line 1: Column 'id' in field list is ambiguous
```

`name` 도 마찬가지다 — 두 표에 똑같이 있다.

```text
### SQL: SELECT name FROM emp e JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---
ERROR:  column reference "name" is ambiguous
LINE 1: SELECT name FROM emp e JOIN dept d ON e.dept_id = d.id;
               ^
--- MySQL 8.4.10 ---
ERROR 1052 (23000) at line 1: Column 'name' in field list is ambiguous
```

```text
FROM emp e JOIN dept d
        ↓
이름 공간:  e.id  e.name  e.dept_id  e.salary
            d.id  d.name
        ↓
SELECT id  ->  후보가 둘  ->  엔진이 고르지 않고 거부한다
```

**고쳐 주지 않는 것이 다행이다.** 어느 한쪽을 임의로 골라 주는 엔진이었다면, 열이 추가되는 순간 결과가 **조용히** 바뀌었을 것이다.

★ **그래서 조인이 있는 질의는 모든 열에 별칭을 붙인다.** 지금 안 겹쳐도 열이 추가되면 그때 깨진다.\
이 규칙을 안 지킨 대가가 가장 크게 나오는 곳이 `NATURAL JOIN` 이다 — 겹치는 이름으로 **조용히** 붙는다(목록의 **18번 주제**, 실행 출력은 [13번](../13-inner-join/)에 있다).

---

### 9. `AS t(eid, ename)` 는 두 엔진에서 다 도는가

**돈다.**

```text
### SQL: SELECT * FROM (SELECT id, name FROM emp WHERE salary >= 400) AS t(eid, ename) ORDER BY eid;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 eid | ename                     +-----+-------+
-----+-------                    | eid | ename |
   2 | bob                       +-----+-------+
   4 | dan                       |   2 | bob   |
(2 rows)                         |   4 | dan   |
                                 +-----+-------+
```

**언제 쓸모 있나 — 이름이 겹칠 때 한 번에 바꾼다.**

```text
안쪽 SELECT 에서 하나씩 바꾸기            바깥에서 한 번에 바꾸기
(SELECT id AS eid, name AS ename         (SELECT id, name FROM emp) AS t(eid, ename)
 FROM emp) AS t
   -> 열이 늘면 AS 도 늘어난다             -> 목록 한 줄로 끝난다
```

`VALUES` 리스트와 함께 쓰면 특히 읽기 좋다 — `AS v(a, b)` 가 없으면 열 이름이 엔진이 정한 것이 된다.\
다만 **열 개수가 안 맞으면 에러**이므로, 안쪽 `SELECT *` 와 같이 쓰지 않는다.

---

### 10. 파생 테이블은 최적화 장벽인가 — `Subquery Scan` 이 뜨는가

**안 뜬다. PG 18.6 은 단순한 파생 테이블을 통째로 없앤다.**

```text
### SQL: EXPLAIN SELECT t.name FROM (SELECT * FROM emp WHERE salary >= 400) AS t WHERE t.id = 2;
--- PG 18.6 ---
 Index Scan using emp_pkey on emp  (cost=0.15..8.17 rows=1 width=32)
   Index Cond: (id = 2)
   Filter: (salary >= 400)
```

`Subquery Scan` 노드가 없다. 바깥의 `t.id = 2` 가 **안쪽으로 내려가 인덱스까지 탔다.**

**집계가 들어가면 사라지지 않는다.**

```text
### SQL: EXPLAIN SELECT t.dept_id FROM (SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id) AS t
         WHERE t.cnt >= 2;
--- PG 18.6 ---
 Subquery Scan on t  (cost=26.95..30.12 rows=67 width=4)
   ->  HashAggregate  (cost=26.95..29.45 rows=67 width=12)
         Group Key: emp.dept_id
         Filter: (count(*) >= 2)
         ->  Seq Scan on emp  (cost=0.00..21.30 rows=1130 width=4)
```

★ 여기서 **바깥의 `WHERE t.cnt >= 2` 가 `HashAggregate` 의 `Filter` 가 됐다** — `HAVING COUNT(*) >= 2` 라고 쓴 것과 같은 자리다([03번](../03-where-vs-having/)).

MySQL 도 두 경우가 갈린다.

```text
### SQL: EXPLAIN FORMAT=TREE SELECT t.name FROM (SELECT * FROM emp WHERE salary >= 400) AS t WHERE t.id = 2;
--- MySQL 8.4.10 ---  (출력의 표 테두리는 지웠다)
-> Rows fetched before execution  (cost=0..0 rows=1)

### SQL: EXPLAIN FORMAT=TREE SELECT t.dept_id FROM (SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id) AS t
         WHERE t.cnt >= 2;
--- MySQL 8.4.10 ---
-> Table scan on t  (cost=2.5..2.5 rows=0)
    -> Materialize  (cost=0..0 rows=0)
        -> Filter: (count(0) >= 2)
            -> Table scan on <temporary>
                -> Aggregate using temporary table
                    -> Table scan on emp  (cost=0.65 rows=4)
```

단순한 쪽은 파생 테이블의 흔적이 없고, 집계 쪽은 **`Materialize`** — 중간 결과를 실제로 만든다.

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 파생 테이블이 **표처럼 동작한다** | 결과의 정의 | 언어 |
| 파생 테이블이 **평탄화된다 / 물질화된다** | 옵티마이저의 선택 | 아무도 — 버전·데이터에 따라 달라진다 |

**결과는 어느 쪽이든 같다.** 계획 노드를 읽는 법은 목록의 **58번 주제**·**59번 주제**다.

---

### 11. 같은 중간 결과를 두 번 참조할 때는 무엇을 쓰나

**CTE(`WITH`)를 쓴다. 이유는 둘 — 문법적으로 한 번만 적고, 계산도 한 번으로 줄일 여지가 생긴다.**

파생 테이블로 하면 **같은 것을 두 번 적어야 한다.**

```sql
SELECT a.dept_id, b.dept_id
FROM (SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY dept_id) a
JOIN (SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY dept_id) b ON a.dept_id = b.dept_id;
```

그리고 **PG 18.6 에서는 실제로 두 번 계산된다.**

```text
### SQL: EXPLAIN (위 질의)
--- PG 18.6 ---
 Hash Join  (cost=54.75..59.29 rows=200 width=8)
   Hash Cond: (emp.dept_id = b.dept_id)
   ->  HashAggregate  (cost=24.12..26.12 rows=200 width=12)
         Group Key: emp.dept_id
         ->  Seq Scan on emp  (cost=0.00..21.30 rows=1130 width=4)
   ->  Hash  (cost=28.12..28.12 rows=200 width=4)
         ->  Subquery Scan on b  (cost=24.12..28.12 rows=200 width=4)
               ->  HashAggregate  (cost=24.12..26.12 rows=200 width=12)
                     Group Key: emp_1.dept_id
                     ->  Seq Scan on emp emp_1  (cost=0.00..21.30 rows=1130 width=4)
```

`HashAggregate` 가 **두 개**, `Seq Scan on emp` 도 **두 개**다. 같은 집계를 두 번 돌렸다.

```text
파생 테이블로 두 번                     CTE 로 한 번
+---------------------------+          +---------------------------+
| (집계 질의) AS a           |          | WITH g AS (집계 질의)      |
| (집계 질의) AS b           |          | SELECT ... FROM g a        |
|   같은 글자를 두 번 적는다  |          |   JOIN g b ON ...          |
+---------------------------+          +---------------------------+
   -> 고칠 때 두 군데를 고친다            -> 이름 하나를 고친다
```

**읽는 방향도 달라진다.** 파생 테이블은 안쪽부터 되짚어 읽어야 하고, CTE 는 위에서 아래로 읽힌다.\
세 겹을 넘어가면 CTE 로 펴는 편이 거의 항상 낫다.

CTE 의 범위·참조 규칙과 `MATERIALIZED` 같은 부가 문법은 목록의 **32번 주제**가 정본이다.\
**경계: 거기는 CTE 의 가시성과 재귀까지, 여기는 「언제 파생 테이블을 그만 쓰나」까지.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 별칭 갈아 끼우기 (1번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **에러 메시지가 근거다** (PG 의 `HINT` 포함) |
| 파생 테이블 기본형·중첩 (3·6번) | PG 18.6 · MySQL 8.4.10 | 각 5회 | |
| 별칭 의무 (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`ERROR 1248` 이 근거다** · 도입 버전은 두 매뉴얼에 없어 적지 않았다 |
| `LATERAL` 경계 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 의 `HINT` 가 근거다** |
| `VALUES` 행 생성자 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 구문 오류가 근거다** |
| 모호한 열 이름 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거다** |
| 열 별칭 목록 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 평탄화·물질화 계획 (10·11번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **구현 의존** — 버전이 오르면 다시 찍어야 한다 |

**구현 의존 항목** — 10번과 11번의 계획. 평탄화·물질화·중복 계산은 전부 옵티마이저의 선택이다.\
**언어 보장 항목** — 1~9번. 이름 가시성과 별칭 의무, 행 생성자 문법은 문서가 정한 것이다.\
단 4번(별칭 의무)과 7번(`VALUES`)은 **버전 표기를 적지 않았다** — 두 매뉴얼 어디에도 도입 버전이 없어서다.\
다른 버전에서 쓸 때는 그 버전에서 다시 던져 본다.
