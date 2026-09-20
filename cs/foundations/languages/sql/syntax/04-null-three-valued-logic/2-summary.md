# sql/04-NULL 의 3값 논리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html) · [MySQL 8.4 · Working with NULL Values](https://dev.mysql.com/doc/refman/8.4/en/working-with-null.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — 3값 논리 자체는 두 엔진 모두 오래전부터 있다. 버전에 갈리는 것은 없다.\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/). 「`WHERE` 가 어느 칸인가」를 알아야 이 주제의 절반이 설명된다.

## 한눈에 — 쉽게 말하면

**`NULL` 은 「없음」이 아니라 「모름」이다. 그래서 답이 「예/아니오」가 아니라 「모르겠다」가 세 번째로 생긴다.**

- 봉투에 카드가 한 장 들어 있는데 **아직 뒤집어 보지 않았다**고 하자.
- "이 카드가 하트인가?" — 답은 **예도 아니고 아니오도 아니다.** 「모른다」다.
- "이 카드가 저 봉투의 카드와 같은가?" — 둘 다 안 봤으면 역시 **「모른다」**.\
  둘 다 안 봤다고 해서 **같다고 할 수는 없다.**
- 그런데 SQL 의 `WHERE` 는 **「예」인 행만 통과**시킨다.\
  「아니오」와 「모른다」는 **똑같이 버린다.**

```text
조건 판정 결과            WHERE 의 처분
-----------------        --------------
TRUE    (예)      ---->  통과
FALSE   (아니오)  ---->  버린다
UNKNOWN (모른다)  ---->  버린다   <- 이 줄이 "사라진 행"의 정체다
```

이 봉투가 **똑같은 구조로** SQL 의 `NULL` 이다.\
실무에서 「조건을 뒤집었는데 행 수가 안 맞는다」·「`NOT IN` 이 한 행도 안 준다」·「`COUNT` 와 `SUM` 이 어긋난다」가 전부 이 세 번째 값 하나에서 나온다.

> **3값 논리(three-valued logic)** — 진릿값이 `TRUE`·`FALSE`·`UNKNOWN` 셋인 논리.\
> 예: `500 > 400` 은 `TRUE`, `300 > 400` 은 `FALSE`, `NULL > 400` 은 `UNKNOWN`.

> **`UNKNOWN`** — 「판정 불가」를 나타내는 진릿값. `NULL` 이 비교에 끼면 나온다.\
> 예: `NULL = NULL` 도 `TRUE` 가 아니라 `UNKNOWN` 이다 — 모르는 것 둘이 같은지도 모른다.

## 예시 테이블 — SQL 네 주제가 같이 쓰는 데이터

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

이 주제에서 사고를 일으키는 것은 주로 **`cho` 의 `salary NULL`** 과 **`dan` 의 `dept_id NULL`** 이다.

## 동작 방식

### 1. `NULL` 이 비교에 들어가면 `UNKNOWN` 이 나온다

**언제 쓰나** — `=`·`<>`·`<`·`>` 같은 비교 연산의 한쪽에 `NULL` 이 올 때. 즉 **거의 항상**.

```text
(전) 비교 식                       (후) 진릿값
  500 = 500      ------>  TRUE
  500 = 300      ------>  FALSE
 NULL = NULL     ------>  UNKNOWN    <- 같다고 하지 않는다
 NULL = 0        ------>  UNKNOWN    <- 0 도 아니다
 NULL <> NULL    ------>  UNKNOWN    <- 다르다고도 하지 않는다
```

```text
### SQL: SELECT NULL = NULL AS eq, NULL <> NULL AS ne, NULL = 0 AS eq0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  eq  |  ne  | eq0               +------+------+------+
------+------+------             | eq   | ne   | eq0  |
 NULL | NULL | NULL              +------+------+------+
(1 row)                          | NULL | NULL | NULL |
                                 +------+------+------+
```

그림 해설 — 진릿값 `UNKNOWN` 은 화면에 **`NULL` 로 표시된다.** SQL 에서 `UNKNOWN` 과 `NULL` 은 표기가 같다.\
대가 — `= NULL` 은 **문법 오류가 아니다.** 그래서 조용히 0행을 준다. 에러가 났으면 오히려 안전했을 자리다.

### 2. `UNKNOWN` 이 `AND`·`OR`·`NOT` 을 지나며 번진다

**언제 쓰나** — `WHERE a AND b` 처럼 조건을 여러 개 엮을 때.

`UNKNOWN` 은 무조건 번지지 않는다. **결과가 이미 정해지는 자리에서는 사라진다.**

```text
AND — 하나라도 FALSE 면 끝났다          OR — 하나라도 TRUE 면 끝났다
+---------------------------+          +---------------------------+
| TRUE  AND UNKNOWN = UNKNOWN|         | TRUE  OR UNKNOWN = TRUE    |  <- 번지지 않는다
| FALSE AND UNKNOWN = FALSE  | <- 번지지 않는다
|                            |         | FALSE OR UNKNOWN = UNKNOWN |
+---------------------------+          +---------------------------+

NOT — 뒤집어도 모르는 건 모른다
   NOT UNKNOWN = UNKNOWN
```

```text
### SQL: SELECT TRUE AND NULL AS t_and_n, FALSE AND NULL AS f_and_n,
                TRUE OR NULL AS t_or_n, FALSE OR NULL AS f_or_n, NOT NULL AS not_n;
--- PG 18.6 ---
 t_and_n | f_and_n | t_or_n | f_or_n | not_n
---------+---------+--------+--------+-------
 NULL    | f       | t      | NULL   | NULL
(1 row)
--- MySQL 8.4.10 ---
+---------+---------+--------+--------+-------+
| t_and_n | f_and_n | t_or_n | f_or_n | not_n |
+---------+---------+--------+--------+-------+
|    NULL |       0 |      1 |   NULL |  NULL |
+---------+---------+--------+--------+-------+
```

그림 해설 — `FALSE AND UNKNOWN` 이 `FALSE` 인 이유는 **모르는 쪽이 무엇이든 결과가 `FALSE`** 이기 때문이다. 같은 이유로 `TRUE OR UNKNOWN` 은 `TRUE` 다.\
대가 — 「`UNKNOWN` 은 전염된다」로 외우면 위 두 칸에서 틀린다. **「결과가 아직 안 정해졌을 때만 번진다」**가 맞다.

> **표시 차이(방언)** — 같은 값인데 PG 는 `t`/`f`, MySQL 은 `1`/`0` 으로 찍는다.\
> PG 는 진짜 `boolean` 타입이 있고, MySQL 의 `BOOLEAN` 은 `TINYINT(1)` 의 다른 이름이기 때문이다.\
> **판정 결과는 같다.** 타입 체계 이야기는 목록의 35번이다.

### 3. `WHERE` 는 `TRUE` 만 통과시킨다

**언제 쓰나** — 언제나. 이것이 이 주제가 [01번](../01-logical-query-processing-order/) 에 걸리는 이유다.

```text
emp 4행이 WHERE salary > 400 을 지난다

 id | salary | salary > 400 | 처분
----+--------+--------------+------
  1 |    300 | FALSE        | 버림
  2 |    500 | TRUE         | 통과
  3 |   NULL | UNKNOWN      | 버림   <- cho
  4 |    400 | FALSE        | 버림
                              ↓
                          1행 (bob)
```

여기서 조건을 **정반대로 뒤집으면** 나머지 3행이 와야 할 것 같지만, 실제로는 2행만 온다.

```text
(A) salary > 400                  (B) salary <= 400
### SQL: SELECT COUNT(*) AS gt     ### SQL: SELECT COUNT(*) AS le
         FROM emp WHERE salary>400;         FROM emp WHERE salary<=400;
--- PG 18.6 ---                    --- PG 18.6 ---
 gt                                 le
----                               ----
  1                                  2
--- MySQL 8.4.10 ---               --- MySQL 8.4.10 ---
+----+                             +----+
| gt |                             | le |
+----+                             +----+
|  1 |                             |  2 |
+----+                             +----+

         1 + 2 = 3  ≠  4 (전체)
### SQL: SELECT COUNT(*) AS total FROM emp;
--- PG 18.6 ---   --- MySQL 8.4.10 ---
 total            +-------+
-------           | total |
     4            +-------+
                  |     4 |
                  +-------+
```

두 그림의 결론 — **`cho` 는 어느 쪽에도 들어가지 않는다.** 두 조건이 「전체를 반으로 가른다」는 직관이 `NULL` 하나로 깨진다.\
대가 — 이 어긋남은 **에러 없이** 일어난다. 집계 리포트가 조용히 한 건씩 비는 사고가 여기서 난다.

`NOT` 으로 뒤집어도 마찬가지다 — `NOT UNKNOWN` 은 여전히 `UNKNOWN` 이다.

```text
### SQL: SELECT id, name FROM emp WHERE NOT (salary > 400) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  1 | ann                        +----+------+
  4 | dan                        |  1 | ann  |
(2 rows)                         |  4 | dan  |
                                 +----+------+
```

`<>` 도 같다 — `salary <> 300` 이 `cho` 를 데려오지 않는다.

```text
### SQL: SELECT id, name FROM emp WHERE salary <> 300 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  2 | bob                        +----+------+
  4 | dan                        |  2 | bob  |
(2 rows)                         |  4 | dan  |
                                 +----+------+
```

### 4. 그래서 `IS NULL` 이 따로 있다

**언제 쓰나** — 「값이 모르는 상태인가」를 **물어야** 할 때. `= NULL` 은 절대 못 한다.

```text
        판정 불가를 만드는 연산       판정 가능한 연산
        +---------------------+      +---------------------+
        | salary = NULL       |      | salary IS NULL      |
        | salary <> NULL      |      | salary IS NOT NULL  |
        |   -> 전부 UNKNOWN    |      |   -> TRUE 또는 FALSE |
        +---------------------+      +---------------------+
           WHERE 가 다 버린다            WHERE 가 고를 수 있다
```

```text
### SQL: SELECT id, name FROM emp WHERE salary IS NULL ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  3 | cho                        +----+------+
(1 row)                          |  3 | cho  |
                                 +----+------+
```

`IS TRUE` / `IS NOT TRUE` 계열도 같은 쓸모가 있다 — **`UNKNOWN` 을 `FALSE` 쪽으로 눌러** 두 갈래로 만든다.

```text
### SQL: SELECT NULL IS TRUE AS a, NULL IS NOT TRUE AS b, NULL IS FALSE AS c;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 a | b | c                       +---+---+---+
---+---+---                      | a | b | c |
 f | t | f                       +---+---+---+
(1 row)                          | 0 | 1 | 0 |
                                 +---+---+---+
```

```text
### SQL: SELECT COUNT(*) AS c FROM emp WHERE (salary > 400) IS NOT TRUE;
--- PG 18.6 ---   --- MySQL 8.4.10 ---
 c                +---+
---               | c |
 3                +---+
                  | 3 |
                  +---+
```

그림 해설 — `1 + 3 = 4`. `IS NOT TRUE` 로 누르니 이제 **전체가 둘로 정확히 갈린다.**\
대가 — 눌렀다는 건 「모름」을 「아니오」로 취급하기로 **결정**했다는 뜻이다. 그 결정이 도메인상 맞는지는 SQL 이 답해 주지 않는다.

### 5. `NOT IN` 에 `NULL` 이 섞이면 결과가 통째로 빈다

**언제 쓰나** — 「저쪽 목록에 없는 것」을 찾을 때. 이 주제에서 가장 비싼 함정이다.

`dept` 의 세 부서 중 사원이 없는 부서(`hr`)를 찾고 싶다.

```text
(의도) dept.id 가 emp.dept_id 목록에 없는 행
       emp.dept_id 목록 = {10, 10, 20, NULL}
                                      ^^^^ dan 때문에 NULL 이 들어 있다

30 NOT IN (10, 20, NULL)
  = NOT (30 = 10 OR 30 = 20 OR 30 = NULL)
  = NOT (FALSE   OR FALSE   OR UNKNOWN)
  = NOT (UNKNOWN)                          <- FALSE OR UNKNOWN = UNKNOWN
  = UNKNOWN                                <- WHERE 가 버린다
```

```text
### SQL: SELECT 30 IN (10,20) AS in_no_null, 30 IN (10,20,NULL) AS in_with_null,
                30 NOT IN (10,20,NULL) AS notin_with_null;
--- PG 18.6 ---
 in_no_null | in_with_null | notin_with_null
------------+--------------+-----------------
 f          | NULL         | NULL
(1 row)
--- MySQL 8.4.10 ---
+------------+--------------+-----------------+
| in_no_null | in_with_null | notin_with_null |
+------------+--------------+-----------------+
|          0 |         NULL |            NULL |
+------------+--------------+-----------------+
```

그림 해설 — `NULL` 이 목록에 하나라도 있으면 **어떤 값을 넣어도 `NOT IN` 이 `TRUE` 가 될 수 없다.** 결과는 **항상 0행**이다.

```text
(A) NOT IN — 0행                      (B) NOT EXISTS — 1행
### SQL: SELECT id, name FROM dept     ### SQL: SELECT id, name FROM dept d
         WHERE id NOT IN                        WHERE NOT EXISTS (SELECT 1 FROM emp e
         (SELECT dept_id FROM emp);                WHERE e.dept_id = d.id) ORDER BY id;
--- PG 18.6 ---                        --- PG 18.6 ---
 id | name                              id | name
----+------                            ----+------
(0 rows)                                30 | hr
--- MySQL 8.4.10 ---                   (1 row)
(빈 결과 — 한 줄도 찍히지 않는다)        --- MySQL 8.4.10 ---
                                       +----+------+
                                       | id | name |
                                       +----+------+
                                       | 30 | hr   |
                                       +----+------+
```

두 그림의 결론 — **(A)가 0행인 것이 "없다"는 답이 아니다.** 답은 `hr` 이고, (A)는 그걸 `UNKNOWN` 에 삼켰다.\
대가 — `IN` 은 멀쩡하다. 반대로 뒤집은 `NOT IN` 만 터진다. 그래서 `IN` 으로 테스트해 보고 안심한 뒤 `NOT IN` 을 배포하는 사고가 난다.

```text
### SQL: SELECT id, name FROM dept WHERE id IN (SELECT dept_id FROM emp) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+-------+
----+-------                     | id | name  |
 10 | sales                      +----+-------+
 20 | dev                        | 10 | sales |
(2 rows)                         | 20 | dev   |
                                 +----+-------+
```

처방은 셋이다 — **`NOT EXISTS` 로 바꾼다**(권장) · 서브쿼리에 `WHERE dept_id IS NOT NULL` 을 건다 · 그 열에 `NOT NULL` 제약을 건다.\
`EXISTS` 계열이 안전한 이유는 「행이 있나 없나」만 보기 때문이다 — **진릿값이 두 개뿐**이라 `UNKNOWN` 이 끼어들 자리가 없다.

### 6. 집계 함수는 `NULL` 을 건너뛴다 — 단 `COUNT(*)` 은 아니다

**언제 쓰나** — `SUM`·`AVG`·`COUNT(열)` 을 쓸 때마다.

```text
emp.salary = [300, 500, NULL, 400]

COUNT(*)      -> 4     행을 센다. 값은 안 본다
COUNT(salary) -> 3     NULL 이 아닌 값만 센다
SUM(salary)   -> 1200  NULL 을 건너뛰고 더한다 (300+500+400)
AVG(salary)   -> 400   1200 / 3 이다.  1200 / 4 = 300 이 아니다
```

```text
### SQL: SELECT COUNT(*) AS c_star, COUNT(salary) AS c_col,
                SUM(salary) AS s, AVG(salary) AS a FROM emp;
--- PG 18.6 ---
 c_star | c_col |  s   |          a
--------+-------+------+----------------------
      4 |     3 | 1200 | 400.0000000000000000
(1 row)
--- MySQL 8.4.10 ---
+--------+-------+------+----------+
| c_star | c_col | s    | a        |
+--------+-------+------+----------+
|      4 |     3 | 1200 | 400.0000 |
+--------+-------+------+----------+
```

그림 해설 — **`AVG` 의 분모가 `COUNT(*)` 이 아니라 `COUNT(열)` 이다.** 「평균 급여 400」이 「4명의 평균」이 아니라 「급여가 기록된 3명의 평균」이라는 뜻이다.\
대가 — 이 차이는 **숫자가 그럴듯해서** 리뷰에서 안 잡힌다. `AVG` 를 쓸 때는 `COUNT(*)` 과 `COUNT(열)` 을 같이 뽑아 분모를 눈으로 확인하는 편이 낫다.

(소수 자릿수가 두 엔진에서 다른 것은 `AVG` 의 결과 타입 차이다 — 값은 같다. 수치 타입 이야기는 목록의 36번이다.)

**전부 `NULL` 인 그룹의 `SUM` 은 `0` 이 아니라 `NULL` 이다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS c, SUM(salary) AS s
         FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c |  s                +---------+---+------+
---------+---+------             | dept_id | c | s    |
      10 | 2 |  800              +---------+---+------+
      20 | 1 | NULL   <- cho     |    NULL | 1 |  400 |
    NULL | 1 |  400              |      10 | 2 |  800 |
(3 rows)                         |      20 | 1 | NULL |
                                 +---------+---+------+
```

`dept_id=20` 의 `SUM` 이 `NULL` 이다 — 더할 값이 하나도 없었기 때문이다. 합계를 0으로 보이고 싶으면 `COALESCE(SUM(salary), 0)` 을 쓴다.

### 7. `GROUP BY` 와 `DISTINCT` 는 `NULL` 끼리를 하나로 묶는다

**언제 쓰나** — 위 결과를 볼 때마다. 비교 규칙과 **정반대**라서 헷갈린다.

```text
비교에서는                        묶기에서는
NULL = NULL  ->  UNKNOWN          NULL 과 NULL  ->  같은 그룹
(같다고 하지 않는다)                (하나로 접는다)
```

```text
### SQL: SELECT DISTINCT salary FROM emp ORDER BY salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
    300                          +--------+
    400                          |   NULL |
    500                          |    300 |
   NULL   <- 한 행만             |    400 |
(4 rows)                         |    500 |
                                 +--------+
```

위 6번의 `GROUP BY dept_id` 결과에서도 `dept_id=NULL` 이 **한 그룹**으로 나왔다.\
대가 — 「`NULL` 은 무조건 서로 다르다」로 외우면 여기서 틀린다. **비교는 `UNKNOWN`, 묶기는 같은 것 취급**으로 나눠서 외운다.

> **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 기준. `GROUP BY`·`DISTINCT` 가 이 기준을 쓴다.\
> 예: `NULL` 둘은 같다고 말할 수는 없지만 서로 구별할 수도 없으므로 한 그룹이 된다.

## 문법 — 형태와 규칙

```sql
<식> IS NULL          -- 값이 NULL 인가 (TRUE 또는 FALSE, UNKNOWN 없음)
<식> IS NOT NULL
<불린식> IS TRUE      -- UNKNOWN 을 FALSE 로 눌러 두 갈래로 만든다
<불린식> IS NOT TRUE
COALESCE(a, b, ...)   -- 앞에서부터 NULL 이 아닌 첫 값. 전부 NULL 이면 NULL
```

규칙 넷.

1. **`NULL` 과의 비교는 전부 `UNKNOWN`** 이다 — `= NULL`·`<> NULL`·`> NULL` 모두. 문법 오류가 아니라 조용히 0행이다.
2. **`WHERE`·`ON`·`HAVING` 은 `TRUE` 만 통과**시킨다. `FALSE` 와 `UNKNOWN` 을 구분하지 않는다.
3. **`UNKNOWN` 은 결과가 안 정해졌을 때만 번진다** — `FALSE AND UNKNOWN = FALSE`, `TRUE OR UNKNOWN = TRUE`.
4. **집계는 `NULL` 을 건너뛴다.** 예외는 `COUNT(*)` 하나 — 값이 아니라 행을 센다.

`COALESCE` 는 「모름」을 **명시적으로** 특정 값으로 바꾸는 유일하게 안전한 방법이다.

```text
### SQL: SELECT id, name, COALESCE(salary, 0) AS sal0 FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | sal0                +----+------+------+
----+------+------               | id | name | sal0 |
  1 | ann  |  300                +----+------+------+
  2 | bob  |  500                |  1 | ann  |  300 |
  3 | cho  |    0                |  2 | bob  |  500 |
  4 | dan  |  400                |  3 | cho  |    0 |
(4 rows)                         |  4 | dan  |  400 |
                                 +----+------+------+
```

「모름을 0으로 본다」는 **도메인 결정**이다. 급여가 기록되지 않은 사람을 급여 0원으로 보는 게 맞는지는 SQL 밖의 문제다.

#### 방언 — `NULL` 을 같은 값으로 보고 비교하는 연산자

두 엔진에 **둘 다 있지만 이름과 문법이 다르다.** 같은 질의를 양쪽에 던져 확인했다.

```text
### SQL: SELECT NULL IS NOT DISTINCT FROM NULL AS pg_style;
--- PG 18.6 ---
 pg_style
----------
 t
(1 row)
--- MySQL 8.4.10 ---
ERROR 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds
  to your MySQL server version for the right syntax to use near 'DISTINCT FROM NULL AS pg_style' at line 1

### SQL: SELECT NULL <=> NULL AS mysql_style;
--- PG 18.6 ---
ERROR:  operator does not exist: unknown <=> unknown
LINE 1: SELECT NULL <=> NULL AS mysql_style;
                    ^
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+-------------+
| mysql_style |
+-------------+
|           1 |
+-------------+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `NULL` 안전 등호 | `a IS NOT DISTINCT FROM b` | `a <=> b` |
| 반대 | `a IS DISTINCT FROM b` | `NOT (a <=> b)` |
| 상대 방언의 문법 | `<=>` 는 **연산자 없음** 에러 | `IS NOT DISTINCT FROM` 은 **문법 오류** |

**양쪽에서 다 도는 표현은 없다.** 이식이 필요하면 `(a = b) OR (a IS NULL AND b IS NULL)` 로 풀어 쓴다.\
자세한 비교는 목록의 05번 주제다.

## 어디서 틀리나

- **`= NULL` 로 쓴다.**\
  에러가 안 난다. 조용히 0행이다. `IS NULL` 이 유일한 방법이다.
- **조건을 뒤집으면 나머지가 다 온다고 믿는다.**\
  `salary > 400` 과 `salary <= 400` 을 더해도 전체가 안 된다. 위에서 1 + 2 = 3 ≠ 4 를 봤다.
- **`NOT IN` 의 서브쿼리에 `NULL` 이 섞인다.**\
  결과가 **항상 0행**이 된다. 에러도 경고도 없다. `NOT EXISTS` 로 바꾼다.
- **`AVG` 의 분모를 행 수로 안다.**\
  분모는 `COUNT(열)` 이다. 위에서 `1200 / 3 = 400` 이었지 `1200 / 4 = 300` 이 아니었다.
- **`SUM` 이 `NULL` 을 줄 수 있다는 걸 잊는다.**\
  전부 `NULL` 인 그룹의 합은 `0` 이 아니라 `NULL` 이다. 애플리케이션에서 `NullPointerException` 으로 튀어나온다.
- **`UNKNOWN` 이 무조건 번진다고 외운다.**\
  `FALSE AND UNKNOWN` 은 `FALSE` 다. 결과가 정해진 자리에서는 안 번진다.
- **`NULL` 은 서로 다르다고만 외운다.**\
  `GROUP BY`·`DISTINCT` 에서는 하나로 묶인다. 비교 규칙과 묶기 규칙은 다르다.
- **`OUTER JOIN` 이 만든 `NULL` 을 원래 데이터의 `NULL` 과 구분하지 않는다.**\
  짝이 없어서 채워진 `NULL` 인지, 원래 값이 없던 `NULL` 인지는 결과만 봐서는 같다([16번](../16-full-outer-join/)).

## 언제 쓰고 언제 안 쓰나

- **`NULL` 을 허용할지는 스키마 설계 시점의 결정이다.** 「모름」이 도메인상 의미가 있을 때만 허용한다.\
  「아직 입력 안 함」·「해당 없음」·「0」을 전부 `NULL` 하나로 표현하면 나중에 구분할 방법이 없다.
- **조인 키에는 되도록 `NOT NULL` 을 건다.** `NOT IN`·`OUTER JOIN`·집계가 전부 조용해진다.
- **`COALESCE` 로 덮는 것은 마지막 수단이다.** 덮으면 「몰랐다」는 사실 자체가 사라진다.\
  보고서 출력 직전에 덮고, 계산 중간에는 `NULL` 을 그대로 흘려보내는 편이 안전하다.
- **`WHERE` 에 `NULL` 안전 비교를 남발하지 않는다.** `IS DISTINCT FROM`·`<=>` 는 인덱스를 못 타는 경우가 많다(목록의 47번).

## 핵심 문장

- `NULL` 은 **「없음」이 아니라 「모름」**이다. 그래서 진릿값이 셋이 된다.
- `WHERE` 는 **`TRUE` 만** 통과시킨다. `FALSE` 와 `UNKNOWN` 을 구분하지 않는다.
- 그래서 **조건을 뒤집어도 사라진 행은 안 돌아온다.**
- `NOT IN` 의 목록에 `NULL` 이 하나라도 있으면 결과는 **항상 0행**이다. `NOT EXISTS` 로 바꾼다.
- 집계는 `NULL` 을 건너뛴다 — **`AVG` 의 분모는 행 수가 아니다.** `COUNT(*)` 만 예외다.
- **비교는 `NULL` 을 구별하지 못하고, `GROUP BY`·`DISTINCT` 는 하나로 묶는다.** 두 규칙은 다르다.

## 관련 자료

- [PostgreSQL 18 · Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html)
- [MySQL 8.4 · Working with NULL Values](https://dev.mysql.com/doc/refman/8.4/en/working-with-null.html)
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — `WHERE` 가 어느 칸인지가 이 주제의 절반이다.
- [16 FULL OUTER JOIN](../16-full-outer-join/) — 조인이 **없던 `NULL` 을 만들어 낸다.**
- [SQL 주제 목록](../README.md) — 05(NULL 비교 연산자) · 19(`NOT IN` 과 반조인) · 21(`COUNT` 세 형태) · 43(UNIQUE 와 NULL) 이 이 주제를 이어받는다.

## 용어 풀이

- **`NULL`** — 「값을 모른다」를 나타내는 표시. 값이 아니라 **값이 없음의 표시**다.\
  예: `cho` 의 `salary NULL` 은 「급여 0원」이 아니라 「급여를 모른다」다.
- **3값 논리** — 진릿값이 `TRUE`·`FALSE`·`UNKNOWN` 셋인 논리.\
  예: `NULL > 400` 은 셋 중 `UNKNOWN`.
- **`UNKNOWN`** — 판정 불가 진릿값. 화면에는 `NULL` 로 찍힌다.\
  예: `NULL = NULL` 의 결과.
- **`IS NULL`** — 값이 `NULL` 인지 묻는 술어. 결과는 언제나 `TRUE` 아니면 `FALSE` 다.\
  예: `WHERE salary IS NULL` 은 `cho` 한 행을 고른다.
- **`IS NOT TRUE`** — `UNKNOWN` 을 `FALSE` 쪽으로 눌러 두 갈래로 만드는 술어.\
  예: `WHERE (salary > 400) IS NOT TRUE` 는 3행(`ann`·`cho`·`dan`)을 준다.
- **`COALESCE`** — 인자를 앞에서부터 보아 `NULL` 이 아닌 첫 값을 돌려주는 함수.\
  예: `COALESCE(salary, 0)` 은 `cho` 의 급여를 0으로 보이게 한다.
- **`NOT EXISTS`** — 서브쿼리가 한 행도 안 낼 때 `TRUE` 인 술어. 진릿값이 둘뿐이라 `NULL` 에 안전하다.\
  예: `NOT IN` 이 0행을 줄 자리에서 `hr` 을 제대로 찾아낸다.
- **`NULL` 안전 등호** — `NULL` 끼리를 같다고 보는 비교. PG 는 `IS NOT DISTINCT FROM`, MySQL 은 `<=>`.\
  예: `NULL <=> NULL` 은 MySQL 에서 `1`.
- **구별 불가능성** — 「같다」가 아니라 「서로 구별할 수 없다」는 묶기 기준.\
  예: `GROUP BY` 가 `NULL` 인 행들을 한 그룹으로 만드는 근거.
- **`COUNT(*)` 과 `COUNT(열)`** — 앞은 행을 세고 뒤는 `NULL` 아닌 값을 센다.\
  예: `emp` 에서 각각 4와 3.
