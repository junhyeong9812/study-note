# sql/10-FROM 절 — 테이블 별칭·파생 테이블 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · Derived Tables](https://dev.mysql.com/doc/refman/8.4/en/derived-tables.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> **버전** — 테이블 별칭·파생 테이블 자체는 두 엔진 모두 오래전부터 있다. 아래에서 갈리는 것은 **별칭 의무**와 **`VALUES` 리스트 문법**이고, 두 매뉴얼 어느 쪽도 「몇 버전부터」를 적지 않아 **도입 버전은 적지 않는다.**\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/). `FROM` 이 **1번 칸**이라는 것이 이 주제의 전부다.\
> **경계** — 바깥 행을 참조하는 서브쿼리(상관 서브쿼리)는 목록의 **11번 주제**, `FROM` 안에서 그것을 하는 `LATERAL` 은 목록의 **20번 주제**다. 여기서는 **경계선이 어디인지**까지만 보여 준다.

## 한눈에 — 쉽게 말하면

**`FROM` 은 「작업대에 무엇을 올릴까」이고, 별칭은 「올린 것에 이름표를 붙이는 일」이다.**

- 작업대에 상자를 올린다. 상자 겉면에 원래 적힌 이름이 길면 **이름표를 새로 붙인다**(`FROM emp e`).
- 이름표를 붙이면 **원래 이름은 가려진다.** 그 뒤로는 `e` 로만 부를 수 있고 `emp` 로는 못 부른다.
- 상자를 통째로 올리는 대신, **그 자리에서 내용물을 골라 새 상자를 만들어** 올릴 수도 있다(파생 테이블).
- 그렇게 만든 상자는 **이름이 없으므로** 이름표가 필요하다 — 이름 없는 상자를 가리킬 방법이 없다.

```text
FROM 에 올릴 수 있는 것 세 가지

(1) 저장된 표           (2) 파생 테이블            (3) 상수 행 목록
+-----------+          +---------------------+    +-----------+
| emp       |          | (SELECT ... ) AS t  |    | VALUES ...|
| (디스크)   |          |  그 자리에서 조립     |    | (적어 넣음)|
+-----------+          +---------------------+    +-----------+
      \                          |                      /
       \                         |                     /
        +----------> 1번 칸 FROM 이 이 셋을 <----------+
                     "행 집합 하나"로 만든다
```

이 작업대가 **똑같은 구조로** `FROM` 절이다.\
그리고 여기서 붙인 이름표는 **1번 칸에서 생기므로 나머지 일곱 칸 전부에서 보인다** — 5번 칸에서 태어나는 열 별칭과 결정적으로 다른 점이다([01번](../01-logical-query-processing-order/)).

> **테이블 별칭(table alias)** — `FROM` 에 올린 것에 붙이는 새 이름.\
> 예: `FROM emp e` 의 `e`. 붙이는 순간 `emp` 라는 이름은 그 질의에서 못 쓴다.

> **파생 테이블(derived table) · 인라인 뷰(inline view)** — `FROM` 안에 괄호로 적은 `SELECT`. 결과를 표처럼 쓴다.\
> 예: `FROM (SELECT id FROM emp WHERE salary >= 400) AS t` — `t` 는 2행짜리 표가 된다.

## 이 주제가 답하려는 질문

1. **테이블 별칭은 언제부터 유효하고, 왜 열 별칭과 다른가?** — 하나는 1번 칸에서 생기고 하나는 5번 칸에서 생긴다.
2. **서브쿼리를 표처럼 쓰려면 무엇이 더 필요한가?** — 별칭 의무가 엔진마다 다르다.
3. **파생 테이블은 바깥을 볼 수 있는가?** — 못 본다. 그 경계선이 `LATERAL` 이 존재하는 이유다.

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

**이 주제에서 쓸모가 큰 것은 두 표가 `id` 와 `name` 을 **둘 다** 갖고 있다는 점**이다.\
그래서 별칭 없이 `SELECT id` 라고 쓰면 두 엔진 다 「어느 `id` 냐」고 되묻는다(아래 8번).

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

### 1. 테이블 별칭 — 이름을 붙이는 게 아니라 **갈아 끼운다**

**언제 쓰나** — 표 이름이 길거나, 같은 표를 두 번 올리거나, 열 이름이 겹칠 때.

```text
(전) FROM 절을 읽기 전                (후) FROM emp e 를 읽은 뒤
+--------------------------+        +--------------------------+
| 질의가 아는 이름          |        | 질의가 아는 이름          |
|   (아직 없다)             |        |   e   -> emp 의 행들      |
+--------------------------+        |   emp -> 없다  <- 가려졌다 |
                                    +--------------------------+
```

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

별칭을 붙인 뒤 **원래 이름으로 부르면 두 엔진 다 거부한다.** 「덮어쓰기」가 아니라 「갈아 끼우기」다.

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

그림 해설 — PG 는 **"`emp` 를 `FROM` 에서 찾긴 했는데 이 이름으로는 못 부른다"** 고 힌트까지 준다. MySQL 은 **"그런 열이 없다"** 고만 한다.\
비용 — 없다. 다만 **한 질의 안에서 두 이름을 섞어 쓸 수 없다**는 뜻이라, 별칭을 붙였으면 전부 별칭으로 통일해야 한다.

같은 표를 두 번 올리려면 **별칭이 필수**다.

```text
### SQL: SELECT * FROM emp, emp;
--- PG 18.6 ---
ERROR:  table name "emp" specified more than once
--- MySQL 8.4.10 ---
ERROR 1066 (42000) at line 1: Not unique table/alias: 'emp'
```

같은 표를 두 별칭으로 올려 행끼리 비교하는 형태는 목록의 **17번 주제**(SELF JOIN)가 정본이다.

---

### 2. 테이블 별칭은 **어느 칸에서 보이나** — 열 별칭과의 대비

**언제 쓰나** — 「이 이름이 여기서 되나」가 막힐 때. SQL 에서 외울 것은 형태가 아니라 가시성이다.

```text
칸       테이블 별칭 e     열 별칭 annual
1 FROM      태어난다           -
2 WHERE       보인다        안 보인다      <- 갈린다
3 GROUP BY    보인다          보인다 *
4 HAVING      보인다      PG 안 보임 / MySQL 보임
5 SELECT      보인다        태어난다
6 DISTINCT    보인다          보인다
7 ORDER BY    보인다          보인다
8 LIMIT       보인다          보인다
                          * 두 엔진 모두 확장으로 허용한다
```

그림 해설 — **테이블 별칭은 1번 칸에서 태어나므로 뒤의 일곱 칸 전부에서 보인다.** 열 별칭은 5번 칸에서 태어나므로 2번·4번 칸에서 안 보인다.\
그래서 `WHERE e.salary >= 400` 은 되고 `WHERE annual > 4000` 은 안 된다. **같은 「별칭」이라는 말에 성질이 다른 두 가지가 들어 있다.**\
비용 — 없다. 하지만 이 표를 모르면 [01번](../01-logical-query-processing-order/)·[03번](../03-where-vs-having/)의 에러를 계속 만난다.

★ **열 별칭이 `WHERE` 에서 안 되는 문제의 정공법이 바로 이 주제다** — 한 겹 감싸면 안쪽이 「이전 칸」이 되어 바깥에서는 그냥 열이다.

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

바깥 질의의 `FROM`(1번 칸)이 안쪽 질의를 **통째로 먼저 끝내기** 때문에, 바깥의 `WHERE`(2번 칸)에서는 `annual` 이 이미 **열**이다.

---

### 3. 파생 테이블 — `FROM` 안에서 표를 조립한다

**언제 쓰나** — 저장된 표 그대로가 아니라 **가공한 결과**를 조인 대상·필터 대상으로 삼을 때.

```text
(전) 저장된 emp 4행                   (후) 파생 테이블 t — 2행짜리 새 표
+----+------+---------+--------+     +----+------+
|  1 | ann  |      10 |    300 |     |  2 | bob  |
|  2 | bob  |      10 |    500 |     |  4 | dan  |
|  3 | cho  |      20 |   NULL |     +----+------+
|  4 | dan  |    NULL |    400 |
+----+------+---------+--------+        이 표에는 이름이 없다
   ↓ (SELECT id, name FROM emp          -> 그래서 AS t 가 붙는다
      WHERE salary >= 400) AS t
```

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

파생 테이블은 **조인 대상**이 된다. 「먼저 좁힌 뒤 붙인다」를 문장 하나로 쓸 수 있다.

```text
### SQL: SELECT e.name, d.name AS dept
         FROM (SELECT * FROM emp WHERE salary >= 400) AS e JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | dept                     +------+-------+
------+-------                   | name | dept  |
 bob  | sales                    +------+-------+
(1 row)                          | bob  | sales |
                                 +------+-------+
```

중첩도 된다. 안쪽부터 바깥으로 차례로 끝난다.

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

그림 해설 — 파생 테이블은 **이름 공간의 격벽**이다. 안쪽에서 만든 별칭(`e1`)은 안쪽에서만 쓰이고, 바깥은 `e2` 의 **출력 열**만 본다.\
비용 — 엔진이 평탄화할 수 있으면 공짜에 가깝고, 못 하면 중간 결과를 물질화한다(아래 「구현 세부사항 대 언어 보장」).

---

### 4. 별칭 의무 — **MySQL 은 필수, PG 는 아니다**

**언제 쓰나** — 파생 테이블을 쓸 때마다. **이 주제에서 가장 실용적인 방언 차이다.**

같은 문 하나를 두 엔진에 던진 실제 출력이다.

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
| 파생 테이블에 별칭이 없으면 | **통과한다** | **`ERROR 1248`** — "Every derived table must have its own alias" |
| 별칭이 있으면 | 통과 | 통과 |

그림 해설 — MySQL 의 에러 문구가 규칙 그 자체다. **파생 테이블은 각자 자기 별칭을 가져야 한다.**\
비용 — 없다. 하지만 **PG 에서 쓴 질의를 MySQL 로 옮기면 여기서 깨진다.** 반대는 안 깨진다.

★ **그러므로 언제나 별칭을 붙인다.** 양쪽에서 돌고, 열을 가리킬 때도 읽기 쉽다.

열 이름까지 새로 붙이는 형태는 **양쪽 다 된다.**

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

---

### 5. 상수 행 목록 — `VALUES` 의 문법이 크게 갈린다

**언제 쓰나** — 표에 없는 값 목록을 조인 대상으로 삼을 때(등급표·기준표·테스트 입력).

**행 생성자 문법이 두 엔진에서 서로를 거부한다.** 같은 문 둘을 양쪽에 던졌다.

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

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `VALUES (1,'x'),(2,'y')` | ✓ | **✗ `ERROR 1064`** |
| `VALUES ROW(1,'x'),ROW(2,'y')` | **✗ 구문 오류** | ✓ |

그림 해설 — **정확히 서로를 거부한다.** 한쪽에서 돌던 질의가 다른 쪽에서 문법 오류가 되는, 이 묶음에서 가장 깨끗한 대칭 사고다.\
비용 — 이식성이 필요하면 `VALUES` 를 쓰지 않는다. **`SELECT ... UNION ALL SELECT ...` 는 양쪽 다 돈다.**

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

이런 **상수 표 × 실제 표** 조합이 `CROSS JOIN` 의 정당한 용도다 — [12번](../12-cartesian-product-cross-join/)이 정본이다.

---

### 6. 파생 테이블은 **바깥을 못 본다** — 여기가 `LATERAL` 의 경계선

**언제 쓰나** — "바깥 행마다 다른 서브쿼리를 돌리고 싶다"가 떠올랐을 때. 그 순간 이 벽에 부딪힌다.

```text
FROM emp e, (SELECT * FROM dept WHERE id = e.dept_id) AS d
            └────────── 이 안에서 e 를 볼 수 있나? ──────────┘
                              답: 못 본다

이유 — FROM 의 항목들은 서로 "형제"다. 형제는 서로를 모른다.
       e 와 d 가 동시에 만들어지므로, d 를 만들 때 e 의 "현재 행" 같은 건 없다.
```

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

그림 해설 — **PG 의 에러가 이 주제의 경계선을 문장으로 알려 준다** — "그 표는 있지만 이 자리에서는 못 부른다. 부르려면 `LATERAL` 로 표시하라."\
MySQL 은 그냥 "모르는 열"이라고 한다. 같은 벽인데 한쪽은 문을 알려 주고 한쪽은 안 알려 준다.\
비용 — 없다. 이 벽은 **의도된 것**이다. 벽이 있어서 `FROM` 항목들을 어떤 순서로든 계산할 수 있다.

**그 벽에 난 문이 `LATERAL` 이고, 목록의 20번 주제다.** 상관 서브쿼리 일반은 목록의 **11번 주제**다.\
여기서 인출할 것은 **"`FROM` 의 형제끼리는 서로를 모른다"** 한 줄이다.

---

### 7. 파생 테이블 안에서 만든 이름은 **밖에서 안 보인다**

**언제 쓰나** — 중첩 파생 테이블을 읽을 때.

```text
SELECT e2.name
FROM ( SELECT *
       FROM ( SELECT * FROM emp WHERE salary IS NOT NULL ) AS e1   <- e1 은 여기 안에서만
       WHERE e1.dept_id IS NOT NULL ) AS e2                        <- e2 는 바깥에서 쓴다

  바깥에서 e1 을 부르면?  -> 그런 이름 없다
```

```text
### SQL: SELECT e1.name FROM (SELECT * FROM (SELECT * FROM emp) AS e1) AS e2;
--- PG 18.6 ---
ERROR:  missing FROM-clause entry for table "e1"
LINE 1: SELECT e1.name FROM (SELECT * FROM (SELECT * FROM emp) AS e1...
               ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'e1.name' in 'field list'
```

그림 해설 — 별칭의 유효 범위는 **그 별칭이 선언된 질의 블록 안**이다. 괄호를 나가면 사라진다.\
비용 — 없다. 오히려 이 격벽 덕분에 안쪽 이름을 바깥과 겹치게 지어도 안전하다.

---

### 8. 이름이 겹치면 — 모호하다고 거부한다

**언제 쓰나** — 두 표를 붙였는데 같은 열 이름이 양쪽에 있을 때. `emp` 와 `dept` 는 `id` 와 `name` 을 **둘 다** 갖고 있다.

```text
FROM emp e JOIN dept d ON ...
                ↓
     이름 공간에 id 가 둘 (e.id, d.id)
                ↓
     SELECT id  ->  어느 쪽?  ->  거부
```

```text
### SQL: SELECT id FROM emp e JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---
ERROR:  column reference "id" is ambiguous
LINE 1: SELECT id FROM emp e JOIN dept d ON e.dept_id = d.id;
               ^
--- MySQL 8.4.10 ---
ERROR 1052 (23000) at line 1: Column 'id' in field list is ambiguous

### SQL: SELECT name FROM emp e JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---
ERROR:  column reference "name" is ambiguous
LINE 1: SELECT name FROM emp e JOIN dept d ON e.dept_id = d.id;
               ^
--- MySQL 8.4.10 ---
ERROR 1052 (23000) at line 1: Column 'name' in field list is ambiguous
```

그림 해설 — **두 엔진이 같은 판정을 한다.** 이건 「시끄러운 실패」라 다행인 자리다 — 어느 쪽을 골라 주는 엔진이 있었다면 훨씬 위험했다.\
비용 — 없다. **그래서 조인이 있는 질의는 모든 열에 별칭을 붙인다.** 지금 안 겹쳐도 나중에 열이 추가되면 겹친다.

> `NATURAL JOIN` 은 이 겹침을 **조용히** 이용한다 — `emp` 와 `dept` 를 `NATURAL JOIN` 하면 `id` 와 `name` **둘 다**로 붙어 0행이 나온다. 목록의 **18번 주제**가 정본이고, [13번](../13-inner-join/)에 실행 출력이 있다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
FROM 표          [AS] 별칭              -- AS 는 생략 가능
FROM 표          [AS] 별칭 (열1, 열2)   -- 열 이름까지 새로 붙인다
FROM (SELECT …)  AS 별칭                -- 파생 테이블. MySQL 은 별칭 필수
FROM (VALUES …)  AS 별칭 (열1, 열2)     -- 행 생성자 문법이 방언마다 다르다
FROM 표 e1, 표 e2                       -- 같은 표를 두 번 올릴 때는 별칭 필수
```

규칙 여섯.

1. **별칭을 붙이면 원래 이름은 가려진다.** `FROM emp e` 뒤에 `emp.id` 는 에러다.
2. **테이블 별칭은 1번 칸에서 태어나 나머지 전부에서 보인다.** 열 별칭(5번 칸)과 다르다.
3. **파생 테이블은 MySQL 에서 별칭이 필수**(`ERROR 1248`), PG 18.6 에서는 없어도 통과한다. **언제나 붙인다.**
4. **`FROM` 의 형제 항목끼리는 서로를 모른다.** 바깥 행을 참조하려면 `LATERAL`(목록의 20번 주제).
5. **파생 테이블 안의 별칭은 괄호 밖에서 안 보인다.** 이름 공간이 닫힌다.
6. **`VALUES` 행 생성자는 PG `(a,b)` · MySQL `ROW(a,b)` 로 서로 배타적이다.** 이식성이 필요하면 `UNION ALL` 을 쓴다.

파생 테이블을 언제 쓰는지는 **네 가지로 줄어든다.**

```sql
-- (1) 열 별칭을 WHERE 에서 쓰고 싶을 때 (5번 칸 결과를 1번 칸으로 내린다)
SELECT t.annual FROM (SELECT salary * 12 AS annual FROM emp) AS t WHERE t.annual > 4000;

-- (2) 집계 결과를 다시 거를 때 (HAVING 으로 못 쓰는 조건도 쓸 수 있다)
SELECT t.dept_id FROM (SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id) AS t WHERE t.cnt >= 2;

-- (3) 먼저 좁힌 뒤 조인할 때 (팬아웃을 막는 처방 — 13번)
SELECT e.name, d.name FROM (SELECT * FROM emp WHERE salary >= 400) AS e JOIN dept d ON e.dept_id = d.id;

-- (4) 표에 없는 값 목록을 조인 대상으로 삼을 때
SELECT d.name, q.q FROM dept d CROSS JOIN (SELECT 1 AS q UNION ALL SELECT 2) AS q;
```

## 어디서 틀리나

- **별칭을 붙여 놓고 원래 이름으로 부른다.**\
  `FROM emp e ... WHERE emp.salary >= 400` 은 에러다. PG 는 힌트까지 준다 — `Perhaps you meant to reference the table alias "e"`.
- **파생 테이블에 별칭을 안 붙인다.**\
  PG 에서 돌던 질의가 MySQL 에서 `ERROR 1248` 로 깨진다. 습관으로 언제나 붙인다.
- **파생 테이블 안에서 바깥 행을 참조한다.**\
  "행마다 상위 N개"를 파생 테이블로 쓰려다 만나는 벽이다. `LATERAL`(목록의 20번 주제) 또는 상관 서브쿼리(목록의 11번 주제)로 간다.
- **`VALUES` 문법을 옮겨 쓴다.**\
  PG 의 `(1,'x')` 와 MySQL 의 `ROW(1,'x')` 는 서로 문법 오류다. 이식성이 필요하면 `UNION ALL`.
- **조인 질의에서 열에 별칭을 안 붙인다.**\
  `SELECT id FROM emp e JOIN dept d ...` 는 `ambiguous` 다. 지금 안 겹쳐도 **열이 추가되면 그때 깨진다.**
- **`SELECT *` 를 파생 테이블 안에 둔다.**\
  안쪽 표에 열이 추가되면 바깥의 이름 공간이 조용히 바뀐다. 겹치는 이름이 생기면 그때서야 `ambiguous` 가 난다.
- **파생 테이블이 공짜라고 믿는다.**\
  평탄화되면 공짜지만, 집계·`DISTINCT`·`LIMIT` 이 들어가면 물질화된다(아래 절).

## 구현 세부사항 대 언어 보장

파생 테이블에는 **결과의 정의**와 **엔진이 실제로 하는 일**이 크게 갈리는 자리가 있다.

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 파생 테이블이 **하나의 표처럼 동작한다** | 결과의 정의 | 언어 — 두 문서가 같은 모양으로 적는다 |
| 파생 테이블이 **중간 결과로 만들어진다** | 아무도 보장 안 함 | 옵티마이저가 평탄화하면 만들어지지 않는다 |
| 파생 테이블이 **최적화 장벽이다** | **틀린 일반화** | 아래 계획이 반증한다 |

단순한 파생 테이블은 PG 에서 **통째로 사라진다.**

```text
### SQL: EXPLAIN SELECT t.name FROM (SELECT * FROM emp WHERE salary >= 400) AS t WHERE t.id = 2;
--- PG 18.6 ---
 Index Scan using emp_pkey on emp  (cost=0.15..8.17 rows=1 width=32)
   Index Cond: (id = 2)
   Filter: (salary >= 400)
```

`Subquery Scan` 노드가 없다. 바깥의 `t.id = 2` 가 **안쪽으로 내려가 인덱스까지 탔다.**

집계가 들어가면 **사라지지 않는다.**

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

★ 재미있는 것은 **바깥의 `WHERE t.cnt >= 2` 가 `HashAggregate` 의 `Filter` 가 됐다**는 점이다 — 내가 `HAVING COUNT(*) >= 2` 라고 쓴 것과 같은 자리다([03번](../03-where-vs-having/)).

MySQL 쪽도 두 경우가 갈린다.

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

- **결과는 어느 쪽이든 같다.** 평탄화되든 물질화되든 답은 정의대로다.
- **비용은 엔진이 정한다.** 위는 이 버전·이 데이터에서 관찰한 것이고 보장이 아니다.
- 계획 노드 이름을 읽는 법은 목록의 **58번 주제**·**59번 주제**가 정본이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 5번 칸 결과를 앞 칸에서 쓰고 싶을 때.** 열 별칭을 `WHERE` 에, 집계 결과를 다시 거를 때.
- **쓴다 — 조인 전에 한쪽을 좁힐 때.** 특히 1:N 조인에서 행이 불어나는 것을 막는 처방으로([13번](../13-inner-join/)).
- **쓴다 — 표에 없는 값 목록이 필요할 때.** 등급표·기준표를 질의 안에 적는다.
- **안 쓴다 — 두 번 이상 참조할 때.** 같은 파생 테이블을 두 번 적으면 두 번 계산된다. 그때는 CTE(`WITH`)가 낫다 — 목록의 **32번 주제**.
- **안 쓴다 — 세 겹을 넘어갈 때.** 읽는 사람이 안쪽부터 되짚어야 한다. CTE 로 펴면 위에서 아래로 읽힌다.
- **안 쓴다 — 바깥 행을 참조해야 할 때.** 그건 `LATERAL`(목록의 20번 주제) 또는 상관 서브쿼리(목록의 11번 주제)다.

## 핵심 문장

- 테이블 별칭은 **1번 칸에서 태어나** 나머지 일곱 칸 전부에서 보인다. 열 별칭(5번 칸)과 성질이 다르다.
- 별칭을 붙이면 **원래 이름은 가려진다.** 섞어 쓸 수 없다.
- 파생 테이블은 **MySQL 에서 별칭이 필수**(`ERROR 1248`), PG 18.6 은 없어도 통과한다. 언제나 붙인다.
- **`FROM` 의 형제 항목끼리는 서로를 모른다.** 벽에 난 문이 `LATERAL` 이다.
- `VALUES` 행 생성자는 **PG `(a,b)` · MySQL `ROW(a,b)`** 로 서로를 거부한다. 이식성이 필요하면 `UNION ALL`.
- 조인 질의에서 열 이름이 겹치면 **두 엔진 다 `ambiguous` 로 막는다.** 조용히 고르지 않는 것이 다행이다.
- 파생 테이블은 **최적화 장벽이 아니다** — 단순하면 평탄화되고, 집계가 들어가면 물질화된다.

## 관련 자료

- [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) — `FROM` 항목·별칭·서브쿼리가 한 페이지에 있다.
- [MySQL 8.4 · Derived Tables](https://dev.mysql.com/doc/refman/8.4/en/derived-tables.html) — 별칭 의무를 문장으로 적는다.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 여덟 칸의 순서까지, 여기는 1번 칸이 이름 공간을 어떻게 만드나부터.**
- [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/) — **경계: 그쪽은 조건을 어느 절에 두나까지, 여기는 그 제약을 한 겹 감싸서 푸는 법부터.**
- [12 카티션곱과 CROSS JOIN](../12-cartesian-product-cross-join/) — 상수 표를 조인 대상으로 쓰는 자리.
- [13 INNER JOIN](../13-inner-join/) — 파생 테이블로 먼저 좁혀 팬아웃을 막는 처방.
- **상관 서브쿼리**(스칼라·`ANY`/`ALL`)는 목록의 **11번 주제**, **`LATERAL`** 은 목록의 **20번 주제**, **CTE(`WITH`)** 는 목록의 **32번 주제**가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **테이블 별칭(table alias)** — `FROM` 에 올린 것에 붙이는 새 이름. 1번 칸에서 생긴다.\
  예: `FROM emp e` 의 `e`. 붙이면 `emp` 는 그 질의에서 못 쓴다.
- **파생 테이블(derived table)** — `FROM` 안에 괄호로 적은 `SELECT`. 그 결과를 표처럼 쓴다.\
  예: `FROM (SELECT id FROM emp WHERE salary >= 400) AS t`.
- **인라인 뷰(inline view)** — 파생 테이블의 다른 이름. 뷰처럼 쓰이지만 저장되지 않는다.\
  예: 위의 `t`. 질의가 끝나면 사라진다.
- **행 생성자(row constructor)** — 값 여러 개를 한 행으로 묶는 표기.\
  예: PG 는 `(1,'x')`, MySQL 은 `ROW(1,'x')`. 서로 문법 오류다.
- **이름 공간(name space)** — 어느 자리에서 어떤 이름을 부를 수 있는지의 범위.\
  예: 파생 테이블 괄호 안에서 만든 별칭은 괄호 밖에서 안 보인다.
- **모호한 참조(ambiguous reference)** — 같은 이름이 둘 이상이라 어느 것인지 정할 수 없는 상태.\
  예: `emp` 와 `dept` 를 붙인 뒤의 `id`. 두 엔진 다 에러로 막는다.
- **평탄화(flattening · subquery pull-up)** — 옵티마이저가 파생 테이블을 없애고 바깥 질의에 녹이는 최적화.\
  예: PG 계획에서 `Subquery Scan` 이 안 뜨고 `Index Scan` 만 남은 것.
- **물질화(materialization)** — 중간 결과를 실제로 만들어 두고 쓰는 것.\
  예: MySQL 계획의 `Materialize`. 집계가 든 파생 테이블에서 나온다.
- **`LATERAL`** — `FROM` 항목이 **앞 항목의 현재 행**을 참조할 수 있게 하는 표시.\
  예: PG 의 에러 힌트가 가리킨 그것. 목록의 20번 주제다.
- **`ERROR 1248`** — MySQL 의 "Every derived table must have its own alias" 오류 번호.\
  예: `FROM (SELECT …)` 에 `AS t` 를 안 붙이면 온다.
