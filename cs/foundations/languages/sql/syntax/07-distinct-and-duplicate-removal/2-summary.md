# sql/07-DISTINCT 와 중복 제거 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · SELECT · DISTINCT Clause](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · DISTINCT Optimization](https://dev.mysql.com/doc/refman/8.4/en/distinct-optimization.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `DISTINCT` 자체는 두 엔진 모두 오래전부터 있다. `DISTINCT ON` 은 PG 전용이고 MySQL 에는 문법이 없다.\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/)(`DISTINCT` 가 6번 칸) · [04 NULL 의 3값 논리](../04-null-three-valued-logic/)(`NULL` 을 하나로 묶는 예외).

## 한눈에 — 쉽게 말하면

**`DISTINCT` 는 「열 하나를 고유하게」가 아니라 「출력 행 전체가 같으면 하나로」다.**

- 도서관에서 대출 기록 카드를 한 무더기 받았다고 하자.
- "중복 빼 주세요"라고 하면 사서는 **카드 한 장 전체를 비교**한다.\
  이름만 같고 날짜가 다르면 **다른 카드**다.
- "이름만 고유하게 해 주세요"는 다른 요구다 — 그건 **이름별로 카드 하나만 고르라**는 뜻이고,\
  **어느 카드를 남길지**를 따로 말해 줘야 한다.
- 그리고 사서는 **이름 칸이 비어 있는 카드끼리는 「같은 카드」로 본다.**\
  "빈 칸 둘이 같은 이름인가?"라고 묻지 않고, **구별할 수 없으니 하나로 친다.**

| 비유 | 실체 |
|---|---|
| 카드 한 장 전체 | 출력 행(= `SELECT` 목록이 만든 열 전부) |
| 카드 전체가 같으면 한 장 | `SELECT DISTINCT` |
| 이름별로 한 장만, 무엇을 남길지 지정 | `DISTINCT ON (...)` (PG 전용) · 윈도우 함수 |
| 빈 칸끼리 같은 카드로 본다 | `NULL` 을 구별 불가능한 것으로 묶는다 |
| 이름 칸이 빈 카드는 세지 않는다 | `COUNT(DISTINCT 열)` 은 `NULL` 을 안 센다 |

```text
DISTINCT 가 보는 것 = SELECT 가 만든 결과 행 전체

SELECT dept_id           SELECT dept_id, salary
  10                       10 | 300
  10   -> 접힌다            10 | 500   -> 안 접힌다 (salary 가 다르다)
  20                       20 | NULL
  NULL                     NULL | 400
```

이 카드 무더기가 **똑같은 구조로** `DISTINCT` 다.\
「`DISTINCT` 를 붙였는데 중복이 그대로다」의 거의 전부가 **열을 하나 더 뽑고 있었던 것**이다.

> **중복 제거(deduplication)** — 결과에서 똑같은 행을 하나만 남기는 것.\
> 예: `SELECT DISTINCT dept_id FROM emp` 는 `10` 이 둘이어도 한 행만 낸다.

> **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 묶기 기준.\
> 예: `NULL` 둘은 같다고 말할 수 없지만 구별할 수도 없으므로 한 행으로 접힌다([04번](../04-null-three-valued-logic/)).

## 이 주제가 답하려는 질문

1. **`DISTINCT` 는 무엇을 기준으로 지우나** — 열 하나인가 행 전체인가.
2. **`NULL` 은 왜 비교 규칙을 거슬러 하나로 묶이나** — `COUNT(DISTINCT ...)` 는 또 왜 다른가.
3. **「키마다 한 행」이 필요할 때 무엇을 쓰나** — 그리고 왜 `DISTINCT` 로는 안 되나.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들이 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

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

이 주제의 과녁은 **`dept_id` 열**이다 — `10` 이 둘(중복), `20` 이 하나, `NULL` 이 하나.\
중복과 `NULL` 이 한 열에 같이 있어서 「접힌다」와 「안 센다」를 한 열로 다 볼 수 있다.

## 동작 방식

### 1. `DISTINCT` 는 출력 행 전체를 본다

**언제 쓰나** — 결과에 똑같은 행이 여럿 나올 때. **그 「똑같다」의 기준이 이 절의 전부다.**

```text
(전) SELECT 가 만든 4행            (후) DISTINCT 가 접은 3행
 dept_id                            dept_id
 -------                            -------
   10   ┐                             10
   10   ┘ 같다 -> 하나로               20
   20                                NULL
  NULL
```

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      20                         |    NULL |
    NULL                         |      10 |
(3 rows)                         |      20 |
                                 +---------+
```

**열을 하나 더 뽑으면 기준이 바뀐다.** 같은 데이터인데 4행이 된다.

```text
### SQL: SELECT DISTINCT dept_id, salary FROM emp ORDER BY dept_id, salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | salary                +---------+--------+
---------+--------               | dept_id | salary |
      10 |    300                +---------+--------+
      10 |    500                |    NULL |    400 |
      20 |   NULL                |      10 |    300 |
    NULL |    400                |      10 |    500 |
(4 rows)                         |      20 |   NULL |
                                 +---------+--------+
```

그림 해설 — `dept_id = 10` 두 행이 **살아남았다.** `salary` 가 300과 500으로 다르기 때문이다.\
대가 — **「중복이 안 지워진다」는 대개 열을 하나 더 뽑고 있었던 것이다.** `DISTINCT` 는 열 단위 지시가 아니다.

`SELECT *` 에 붙이면 기준이 **테이블의 모든 열**이 된다 — `emp` 는 `id` 가 기본키라 한 행도 안 접힌다.

```text
### SQL: SELECT DISTINCT * FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary    +----+------+---------+--------+
----+------+---------+--------   | id | name | dept_id | salary |
  1 | ann  |      10 |    300    +----+------+---------+--------+
  2 | bob  |      10 |    500    |  1 | ann  |      10 |    300 |
  3 | cho  |      20 |   NULL    |  2 | bob  |      10 |    500 |
  4 | dan  |    NULL |    400    |  3 | cho  |      20 |   NULL |
(4 rows)                         |  4 | dan  |    NULL |    400 |
                                 +----+------+---------+--------+
```

---

### 2. `DISTINCT(열)` 은 함수가 아니다

**언제 쓰나** — 절대 안 쓴다. **가장 널리 퍼진 오해**라서 절을 따로 세운다.

```text
쓴 사람의 머릿속                    실제 파싱
SELECT DISTINCT(dept_id), salary    SELECT DISTINCT (dept_id), salary
       ^^^^^^^^^^^^^^^^^                   ^^^^^^^^ ^^^^^^^^^
   "dept_id 만 고유하게"              DISTINCT 는 절, 괄호는 그냥 괄호
```

```text
### SQL: SELECT DISTINCT(dept_id), salary FROM emp ORDER BY dept_id, salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | salary                +---------+--------+
---------+--------               | dept_id | salary |
      10 |    300                +---------+--------+
      10 |    500                |    NULL |    400 |
      20 |   NULL                |      10 |    300 |
    NULL |    400                |      10 |    500 |
(4 rows)                         |      20 |   NULL |
                                 +---------+--------+
```

그림 해설 — **1절의 두 열짜리 결과와 한 글자도 다르지 않다.** 괄호는 아무 일도 하지 않았다.\
대가 — 에러가 안 난다. 「`DISTINCT` 를 걸었는데 왜 중복이지」가 여기서 나온다.\
`DISTINCT` 는 **`SELECT` 바로 뒤에 한 번** 오는 절이고, 언제나 **목록 전체**에 걸린다.

---

### 3. `NULL` 은 하나로 접힌다 — 비교 규칙의 예외

**언제 쓰나** — 위 결과를 볼 때마다. `=` 규칙과 **정반대**라 헷갈린다.

```text
비교에서는                        묶기에서는
NULL = NULL  ->  UNKNOWN          NULL 과 NULL  ->  구별할 수 없다  ->  한 행
(같다고 하지 않는다)                (같다고 말하지 않으면서 하나로 접는다)
```

```text
### SQL: SELECT DISTINCT salary FROM emp ORDER BY salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
    300                          +--------+
    400                          |   NULL |
    500                          |    300 |
   NULL   <- 한 행               |    400 |
(4 rows)                         |    500 |
                                 +--------+
```

그림 해설 — `emp` 에는 `salary NULL` 인 행이 하나뿐이라 접히는 게 눈에 안 보이지만, `dept_id` 쪽 `NULL` 도 1절에서 **한 행**으로 나왔다.\
`GROUP BY` 도 같은 기준을 쓴다 — [04번](../04-null-three-valued-logic/)의 `GROUP BY dept_id` 결과에서 `NULL` 그룹이 하나였다.\
대가 — **「`NULL` 은 무조건 서로 다르다」로 외우면 여기서 틀린다.** 비교는 `UNKNOWN`, 묶기는 같은 것 취급이다.

---

### 4. `COUNT(DISTINCT 열)` 은 `NULL` 을 세지 않는다

**언제 쓰나** — 「서로 다른 값이 몇 개인가」를 셀 때. **3절과 규칙이 또 다르다.**

```text
dept_id = [10, 10, 20, NULL]

SELECT DISTINCT dept_id  ->  3행 (10, 20, NULL)      <- NULL 도 한 행
COUNT(DISTINCT dept_id)  ->  2                        <- NULL 은 안 센다
COUNT(dept_id)           ->  3                        <- NULL 아닌 값의 개수
COUNT(*)                 ->  4                        <- 행의 개수
```

```text
### SQL: SELECT COUNT(*) AS c_star, COUNT(dept_id) AS c_col, COUNT(DISTINCT dept_id) AS c_dist FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c_star | c_col | c_dist         +--------+-------+--------+
--------+-------+--------        | c_star | c_col | c_dist |
      4 |     3 |      2         +--------+-------+--------+
(1 row)                          |      4 |     3 |      2 |
                                 +--------+-------+--------+
```

그림 해설 — **`SELECT DISTINCT` 는 3행인데 `COUNT(DISTINCT)` 는 2다.** 둘은 같은 수가 아니다.\
`COUNT` 가 **집계 함수**이고 집계는 `NULL` 을 건너뛰기 때문이다([04번](../04-null-three-valued-logic/)).\
대가 — 「고유 부서 수」를 `COUNT(DISTINCT dept_id)` 로 뽑으면 **소속 없는 사원의 존재가 통계에서 사라진다.** 그게 맞는지는 도메인 질문이다.

다른 집계에도 `DISTINCT` 를 붙일 수 있다.

```text
### SQL: SELECT SUM(DISTINCT dept_id) AS sd, SUM(dept_id) AS s, COUNT(DISTINCT dept_id) AS cd FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 sd | s  | cd                    +------+------+----+
----+----+----                   | sd   | s    | cd |
 30 | 40 |  2                    +------+------+----+
(1 row)                          |   30 |   40 |  2 |
                                 +------+------+----+
```

`SUM(DISTINCT dept_id)` 는 `10 + 20 = 30`, `SUM(dept_id)` 는 `10 + 10 + 20 = 40` 이다.

#### 방언 — 여러 열의 조합을 세기

```text
### SQL: SELECT COUNT(DISTINCT dept_id, salary) AS c FROM emp;
--- PG 18.6 ---
ERROR:  function count(integer, integer) does not exist
LINE 1: SELECT COUNT(DISTINCT dept_id, salary) AS c FROM emp;
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+---+
| c |
+---+
| 2 |
+---+
```

```text
### SQL: SELECT COUNT(DISTINCT (dept_id, salary)) AS c FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c                               ERROR 1241 (21000) at line 1: Operand should contain 1 column(s)
---
 4
(1 row)
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `COUNT(DISTINCT a, b)` | **없다** — `function count(integer, integer) does not exist` | **있다** → `2` |
| `COUNT(DISTINCT (a, b))` (행 생성자) | **있다** → `4` | **`ERROR 1241`** |

그림 해설 — **문법이 서로 배타적일 뿐 아니라 결과 숫자도 다르다.**

```text
네 행: (10,300) (10,500) (20,NULL) (NULL,400)

MySQL COUNT(DISTINCT a, b) = 2
   -> 어느 한쪽이라도 NULL 인 행은 세지 않는다
   -> (10,300), (10,500) 만 남는다

PG COUNT(DISTINCT (a, b)) = 4
   -> (a,b) 를 "행 값" 하나로 본다. 행 자체는 NULL 이 아니다
   -> 네 조합이 전부 서로 다르다
```

대가 — **같은 의도를 적었는데 답이 2와 4로 갈린다.** 이식할 때 이 차이를 모르면 지표가 조용히 바뀐다.\
양쪽에서 같게 하려면 **`NULL` 을 먼저 없애거나**(`COALESCE`) **부분질의로 접은 뒤 센다** — `SELECT COUNT(*) FROM (SELECT DISTINCT a, b FROM t) x`.

---

### 5. `DISTINCT` 는 `ORDER BY` 보다 앞이다

**언제 쓰나** — 중복을 지우면서 정렬할 때. 6번 칸과 7번 칸의 순서가 여기서 드러난다.

```text
5 SELECT   -> 출력 열은 dept_id 하나. salary 는 여기서 버려졌다
6 DISTINCT -> dept_id 기준으로 접는다 (10 이 둘 -> 하나)
7 ORDER BY -> 이제 salary 로 정렬하라고? 그 열은 두 칸 전에 사라졌다
```

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
--- PG 18.6 ---
ERROR:  for SELECT DISTINCT, ORDER BY expressions must appear in select list
LINE 1: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
                                                  ^
--- MySQL 8.4.10 ---
ERROR 3065 (HY000) at line 1: Expression #1 of ORDER BY clause is not in SELECT list, references column 'study.emp.salary' which is not in SELECT list; this is incompatible with DISTINCT
```

그림 해설 — `DISTINCT` 가 `ann`(300)과 `bob`(500)을 한 행으로 접은 뒤에는 **그 행의 `salary` 가 무엇인지 정할 방법이 없다.** 그래서 문법 차원에서 막는다.\
대가 — `DISTINCT` 없이는 같은 질의가 통과한다. 「`ORDER BY` 는 `SELECT` 밖의 열도 쓸 수 있다」와 「`DISTINCT` 가 있으면 못 쓴다」가 충돌하지 않는 이유가 이 순서다.

#### 방언 — 「목록에 있어야 한다」의 엄격도

식으로 감싸면 갈린다.

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY dept_id * 1;
--- PG 18.6 ---
ERROR:  for SELECT DISTINCT, ORDER BY expressions must appear in select list
LINE 1: SELECT DISTINCT dept_id FROM emp ORDER BY dept_id * 1;
                                                  ^
--- MySQL 8.4.10 ---
+---------+
| dept_id |
+---------+
|    NULL |
|      10 |
|      20 |
+---------+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `ORDER BY <목록에 없는 열>` | 에러 | 에러 |
| `ORDER BY <목록 열로 만든 식>` | **에러** | **통과** |

그림 해설 — PG 는 「**식 자체**가 목록에 있어야 한다」, MySQL 은 「**목록 열로 만들어졌으면** 된다」로 읽는다.\
대가 — MySQL 에서 돌던 질의가 PG 에서 깨진다. 반대 방향은 안 깨진다.\
해결은 그 식을 **`SELECT` 목록에 넣는 것**이다 — 양쪽에서 돈다.

별칭으로 정렬하는 것은 양쪽 다 된다.

```text
### SQL: SELECT DISTINCT salary * 12 AS annual FROM emp ORDER BY annual;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual                          +--------+
--------                         | annual |
   3600                          +--------+
   4800                          |   NULL |
   6000                          |   3600 |
   NULL                          |   4800 |
(4 rows)                         |   6000 |
                                 +--------+
```

---

### 6. `DISTINCT` 와 `GROUP BY` — 계획까지 같다

**언제 쓰나** — 둘 중 무엇을 쓸지 고를 때. **결론은 「같은 일이면 아무거나**」다.

```text
### SQL: SELECT DISTINCT dept_id FROM emp;         ### SQL: SELECT dept_id FROM emp GROUP BY dept_id;
--- PG 18.6 (EXPLAIN COSTS OFF) ---               --- PG 18.6 (EXPLAIN COSTS OFF) ---
 HashAggregate                                     HashAggregate
   Group Key: dept_id                                Group Key: dept_id
   ->  Seq Scan on emp                               ->  Seq Scan on emp
```

```text
--- MySQL 8.4.10 (EXPLAIN FORMAT=TREE) ---
DISTINCT 판                                       GROUP BY 판
-> Table scan on <temporary>  (cost=1.76..3.81)   -> Table scan on <temporary>  (cost=1.76..3.81)
    -> Temporary table with deduplication          -> Temporary table with deduplication
        -> Table scan on emp                           -> Table scan on emp
```

그림 해설 — **두 엔진 모두 계획이 한 글자도 같다.** 「`DISTINCT` 가 느리다」·「`GROUP BY` 가 빠르다」는 이 형태에서는 근거가 없다.\
대가 — 둘은 **할 수 있는 일이 다르다.** 집계값이 필요하면 `GROUP BY` 여야 한다.

| | `SELECT DISTINCT` | `GROUP BY` |
|---|---|---|
| 중복 제거 | ✓ | ✓ |
| 집계값(`COUNT`·`SUM`) | ✗ | ✓ |
| 그룹 조건(`HAVING`) | ✗ | ✓ |
| 읽는 사람에게 주는 신호 | 「중복만 지우려는 것」 | 「그룹 단위로 볼 것」 |

**의도를 드러내는 쪽을 고른다** — 집계가 없으면 `DISTINCT`, 있으면 `GROUP BY`.\
(계획은 데이터 크기·인덱스·통계에 따라 달라질 수 있다. 계획 읽기의 정본은 [목록의 **58번 주제**](../58-explain-plan-tree/)다.)

---

### 7. 「키마다 한 행」은 `DISTINCT` 로 안 된다 — `DISTINCT ON`(PG 전용)

**언제 쓰나** — 「부서마다 급여가 가장 높은 사원 한 명」처럼 **그룹마다 대표 행 하나**를 뽑을 때.

```text
DISTINCT 로는 왜 안 되나
  SELECT DISTINCT dept_id, name FROM emp
    -> dept_id 10 에 ann, bob 두 행이 남는다
    -> "둘 중 누구를 남길지" 를 말할 방법이 DISTINCT 문법에 없다

DISTINCT ON 은 그 말을 ORDER BY 로 한다
  SELECT DISTINCT ON (dept_id) ... ORDER BY dept_id, salary DESC
                     ^^^^^^^^^                ^^^^^^^  ^^^^^^^^^^^
                     묶는 키                   같아야 함  누구를 남길지
```

```text
### SQL: SELECT DISTINCT ON (dept_id) dept_id, id, name, salary FROM emp ORDER BY dept_id, salary DESC;
--- PG 18.6 ---
 dept_id | id | name | salary
---------+----+------+--------
      10 |  2 | bob  |    500
      20 |  3 | cho  |   NULL
    NULL |  4 | dan  |    400
(3 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'ON (dept_id) dept_id, id, name, salary FROM emp ORDER BY dept_id, salary DESC' at line 1
```

그림 해설 — `dept_id = 10` 에서 `bob`(500)이 남았다. `ORDER BY ... salary DESC` 가 「누구를 남길지」를 정했다.\
`dept_id = 20` 의 `cho` 는 `salary` 가 `NULL` 인데 남았다 — PG 는 `DESC` 에서 `NULL` 을 **맨 앞**(큰 값)에 두기 때문이다([08번](../08-order-by-null-position-stability/)). **의도한 게 아니라면 여기서 사고가 난다.**

**`ORDER BY` 앞부분이 `DISTINCT ON` 과 일치해야 한다.**

```text
### SQL: SELECT DISTINCT ON (dept_id) dept_id, id FROM emp ORDER BY id;
--- PG 18.6 ---
ERROR:  SELECT DISTINCT ON expressions must match initial ORDER BY expressions
LINE 1: SELECT DISTINCT ON (dept_id) dept_id, id FROM emp ORDER BY i...
                            ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'ON (dept_id) dept_id, id FROM emp ORDER BY id'
```

**MySQL 에는 이 문법이 없다.** 양쪽에서 도는 대체는 윈도우 함수다.

```text
### SQL: SELECT dept_id, id, name, salary FROM (SELECT e.*, ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rn FROM emp e) t
         WHERE rn = 1 ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | id | name | salary    +---------+----+------+--------+
---------+----+------+--------   | dept_id | id | name | salary |
      10 |  2 | bob  |    500    +---------+----+------+--------+
      20 |  3 | cho  |   NULL    |    NULL |  4 | dan  |    400 |
    NULL |  4 | dan  |    400    |      10 |  2 | bob  |    500 |
(3 rows)                         |      20 |  3 | cho  |   NULL |
                                 +---------+----+------+--------+
```

두 그림의 결론 — **같은 세 행이 나온다.** 줄 순서만 `NULL` 정렬 차이로 다르다.\
대가 — 윈도우 함수 판은 한 겹 감싸야 한다(윈도우 결과를 `WHERE` 로 못 거르므로 — [01번](../01-logical-query-processing-order/)). 대신 **양쪽에서 돌고, 「2위까지」 같은 확장이 쉽다.**\
윈도우 함수 자체의 정본은 목록의 [**26**](../26-window-functions-vs-aggregates/)~[**29**](../29-ranking-functions/)번 주제다.

## 문법 — 형태와 규칙

```sql
SELECT DISTINCT <출력 열 목록>        -- 목록 전체가 기준. 괄호는 의미 없다
SELECT DISTINCT ON (<식>) <목록>      -- PostgreSQL 전용
  ...
  ORDER BY <위 식과 같은 것>, <누구를 남길지>
COUNT(DISTINCT <열>)                  -- 집계. NULL 을 세지 않는다
SUM(DISTINCT <열>) · AVG(DISTINCT <열>)
```

규칙 여섯.

1. **`DISTINCT` 는 `SELECT` 바로 뒤에 한 번** 온다. 열 하나에 붙이는 지시가 아니다.
2. **기준은 출력 행 전체**다. 열을 하나 더 뽑으면 접히던 행이 안 접힌다.
3. **`DISTINCT(열)` 의 괄호는 아무 일도 안 한다.** 에러도 안 난다.
4. **`NULL` 끼리는 하나로 접힌다** — 비교 규칙(`NULL = NULL` 은 `UNKNOWN`)과 정반대다.
5. **`COUNT(DISTINCT 열)` 은 `NULL` 을 안 센다** — 그래서 `SELECT DISTINCT` 의 행 수보다 작을 수 있다.
6. **`DISTINCT` 가 있으면 `ORDER BY` 는 `SELECT` 목록 안의 것만** 쓸 수 있다(엄격도는 엔진마다 다르다).

`DISTINCT` 에 `LIMIT` 을 붙이면 **접은 뒤에** 자른다 — 8번 칸이 6번 칸보다 뒤이기 때문이다.

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY dept_id LIMIT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      20                         |    NULL |
(2 rows)                         |      10 |
                                 +---------+
```

(두 엔진의 답이 다른 것은 `NULL` 정렬 위치 차이다 — `DISTINCT` 와 무관하다.)

## 어디서 틀리나

- **`DISTINCT` 가 열 하나에 걸린다고 믿는다.**\
  `SELECT DISTINCT a, b` 는 `(a, b)` 쌍이 기준이다. 「중복이 안 지워진다」의 원인 1위.
- **`DISTINCT(열)` 로 쓴다.**\
  괄호는 아무 일도 안 한다. 에러도 안 나서 더 오래 산다.
- **`SELECT *` 에 `DISTINCT` 를 붙인다.**\
  기본키가 있으면 **한 행도 안 접힌다.** 비용만 든다.
- **`SELECT DISTINCT x` 의 행 수와 `COUNT(DISTINCT x)` 가 같다고 본다.**\
  `NULL` 이 있으면 1 차이가 난다. 위에서 3행 대 2 를 봤다.
- **`COUNT(DISTINCT a, b)` 를 PG 에 쓴다.**\
  PG 에는 그 문법이 없고, 행 생성자 판은 **답이 다르다**(2 대 4).
- **`DISTINCT` 로 「키마다 한 행」을 뽑으려 한다.**\
  「누구를 남길지」를 말할 문법이 없다. `DISTINCT ON`(PG) 이나 윈도우 함수를 쓴다.
- **`DISTINCT ON` 의 `ORDER BY` 첫 항목을 다르게 적는다.**\
  PG 가 `must match initial ORDER BY expressions` 로 막는다.
- **`DISTINCT ON` 의 `ORDER BY ... DESC` 에서 `NULL` 을 잊는다.**\
  PG 는 `DESC` 에서 `NULL` 이 맨 앞이라 **`NULL` 인 행이 대표로 뽑힌다**(위의 `cho`).
- **`DISTINCT` 를 「중복이 있을지도 모르니 일단」 붙인다.**\
  중복이 생기는 진짜 원인은 대개 **조인 팬아웃**이다. 덮으면 원인이 안 보이고 비용만 든다([25번](../25-join-fan-out/)).

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| 기준이 출력 행 전체인 것 | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| `NULL` 끼리 접히는 것 | **표준의 「구별 불가능성」** | 두 엔진 동일 출력 |
| `COUNT(DISTINCT)` 가 `NULL` 을 안 세는 것 | **집계의 `NULL` 규칙** | 두 엔진 동일 출력 |
| `DISTINCT` 가 `ORDER BY` 보다 앞인 것 | **양쪽 문서가 정한 순서** | 두 엔진 모두 에러 |
| `ORDER BY` 식의 허용 범위 | **엔진 선택** | PG 에러 / MySQL 통과 |
| `COUNT(DISTINCT a, b)` 문법 | **엔진 선택** | PG 없음 / MySQL 있음 |
| `DISTINCT ON` | **PG 전용 확장** | MySQL `ERROR 1064` |
| `DISTINCT` 와 `GROUP BY` 의 계획이 같은 것 | **옵티마이저 구현** | 두 엔진 모두 같은 계획 |

정리하면 — **「행 전체가 기준」과 「`NULL` 은 하나로」만 언어 보장이고, 문법 확장과 비용은 엔진마다 다르다.**

## 언제 쓰고 언제 안 쓰나

- **중복이 「데이터의 성질」일 때만 `DISTINCT`.** 예: 「사원이 있는 부서 목록」.
- **중복이 「질의가 만든 것」이면 원인을 고친다.** 조인 팬아웃을 `DISTINCT` 로 덮으면 행 수가 맞는 것처럼 보일 뿐이다([25번](../25-join-fan-out/)).
- **집계가 필요하면 `GROUP BY`.** 계획이 같아도 의도가 다르게 읽힌다.
- **「키마다 한 행」은 윈도우 함수를 기본으로.** `DISTINCT ON` 은 PG 안에서 쓸 때만.
- **`COUNT(DISTINCT ...)` 는 비싸다.** 큰 표에서는 근사 계수(HLL 류)를 검토한다 — 근사 계수의 정본은 [`data-structure/19-probabilistic-counting`](../../../../../data-structure/19-probabilistic-counting/)이다.
- **`SELECT *` 에는 붙이지 않는다.** 기본키가 있으면 아무것도 안 지우면서 비용만 든다.

## 핵심 문장

- `DISTINCT` 의 기준은 **출력 행 전체**다. 열 하나가 아니다.
- **`DISTINCT(열)` 의 괄호는 아무 일도 안 한다.**
- **`NULL` 끼리는 하나로 접힌다** — 비교 규칙과 정반대다.
- **`COUNT(DISTINCT 열)` 은 `NULL` 을 안 센다** — `SELECT DISTINCT` 의 행 수와 다를 수 있다.
- `DISTINCT` 는 **6번 칸**, `ORDER BY` 는 7번 칸이다. 그래서 목록 밖의 열로 정렬할 수 없다.
- **`DISTINCT` 와 `GROUP BY` 는 계획까지 같다** — 고르는 기준은 성능이 아니라 의도다.
- **「키마다 한 행」은 `DISTINCT` 가 못 한다** — `DISTINCT ON`(PG) 또는 윈도우 함수다.

## 관련 자료

- [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) — `DISTINCT` 와 `DISTINCT ON` 이 같은 페이지에 있다.
- [MySQL 8.4 · DISTINCT Optimization](https://dev.mysql.com/doc/refman/8.4/en/distinct-optimization.html)
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 `DISTINCT` 가 6번 칸이라는 것까지, 여기는 그래서 무엇을 기준으로 지우나부터.**
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `NULL` 이 묶기에서 하나가 된다는 사실까지, 여기는 그 규칙이 `COUNT(DISTINCT)` 에서 또 갈리는 것부터.**
- [05 NULL 비교](../05-null-comparison-is-distinct-from/) — PG 의 `IS NOT DISTINCT FROM` 이 **이 주제의 묶기 기준을 비교 연산자로 꺼내 쓴 것**이다.
- [08 ORDER BY](../08-order-by-null-position-stability/) — `DISTINCT ON` 의 대표 행을 `ORDER BY` 가 정한다. `NULL` 위치가 거기서 사고를 만든다.
- [`data-structure/19-probabilistic-counting`](../../../../../data-structure/19-probabilistic-counting/) — **경계: 근사 계수(HLL 류)는 거기, 여기는 정확 계수의 문법과 `NULL` 처리.**
- [21 집계 함수와 COUNT 의 세 형태](../21-aggregate-functions-count-forms/) — **경계: 그쪽은 세 형태의 `NULL`·중복 처리, 여기는 `DISTINCT` 가 접는 기준.**
- [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) — **경계: 그쪽은 그룹 키가 결과 행을 정의하는 규칙, 여기는 같은 계획이 나와도 의도가 다르다는 것.**
- [25 조인 팬아웃](../25-join-fan-out/) — **경계: 중복이 조인에서 생겼을 때의 처방은 그쪽, 여기는 `DISTINCT` 가 그 증상을 덮는다는 것까지.**
- **윈도우 함수**는 목록의 [**26**](../26-window-functions-vs-aggregates/)~[**29**](../29-ranking-functions/)번 주제, **집합 연산의 `UNION`/`UNION ALL`** 은 [**34번 주제**](../34-set-operations-union-intersect-except/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **중복 제거(deduplication)** — 결과에서 똑같은 행을 하나만 남기는 것.\
  예: `SELECT DISTINCT dept_id FROM emp` 가 `10` 두 행을 한 행으로 만든다.
- **출력 행(output row)** — `SELECT` 목록이 만든 열들로 이루어진 결과 한 줄.\
  예: `SELECT dept_id, salary` 면 출력 행은 두 칸짜리다. `DISTINCT` 는 이 두 칸을 다 본다.
- **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 묶기 기준.\
  예: `NULL` 둘이 한 행으로 접히는 근거.
- **`DISTINCT ON`** — 지정한 식마다 첫 행 하나만 남기는 PG 전용 문법.\
  예: `SELECT DISTINCT ON (dept_id) ... ORDER BY dept_id, salary DESC` 는 부서마다 최고 급여 행을 남긴다.
- **행 생성자(row constructor)** — 여러 값을 묶어 「행 값」 하나로 만드는 표기.\
  예: PG 의 `COUNT(DISTINCT (a, b))` 에서 `(a, b)`. MySQL 은 이 자리를 `ERROR 1241` 로 막는다.
- **집계 함수(aggregate function)** — 여러 행을 값 하나로 접는 함수.\
  예: `COUNT`·`SUM`. `NULL` 을 건너뛴다는 규칙이 `COUNT(DISTINCT)` 에도 적용된다.
- **윈도우 함수(window function)** — 행을 접지 않고 행마다 값을 붙이는 계산.\
  예: `ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC)` 로 `DISTINCT ON` 을 대신한다.
- **조인 팬아웃(join fan-out)** — 1:N 조인으로 한쪽 행이 여러 번 복제되는 현상.\
  예: `DISTINCT` 로 덮으면 행 수는 맞아 보이지만 `SUM` 은 여전히 부풀어 있다.
- **`HashAggregate`** — PG 계획에서 해시로 묶어 중복을 지우는 연산자 이름.\
  예: `DISTINCT` 와 `GROUP BY` 가 둘 다 이 노드로 나왔다.

## 더 들어가면

- **`DISTINCT` 는 「비용이 드는 정정」이다.** 중복이 나오는 자리를 고치는 대신 결과에서 지우는 것이라, 엔진은 **결과 전체를 모아 정렬하거나 해시**해야 한다. 스트리밍으로 흘려보낼 수 없다는 뜻이고, 그래서 큰 결과에서는 여기가 병목이 된다.
- **`UNION` 이 조용히 `DISTINCT` 를 한다.** `UNION ALL` 과 달리 `UNION` 은 중복을 지운다 — [16번](../16-full-outer-join/)에서 MySQL 의 `FULL OUTER JOIN` 우회를 `UNION` 으로 짜면 값이 같은 행이 접혀 결과가 줄어드는 사고가 그것이다. 집합 연산의 정본은 [목록의 **34번 주제**](../34-set-operations-union-intersect-except/)다.
- **`COUNT(DISTINCT)` 두 판의 답이 2와 4로 갈린 것**은 문법 차이가 아니라 **「`NULL` 이 든 조합을 셀 것인가」라는 설계 판단의 차이**다. 두 엔진 중 어느 쪽이 옳다기보다, 지표를 정의할 때 그 질문에 먼저 답해야 한다는 신호로 읽는 편이 낫다.
