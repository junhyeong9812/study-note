# sql/05-NULL 비교 — IS NULL·IS DISTINCT FROM·NULL 안전 등호 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html) · [MySQL 8.4 · Comparison Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/comparison-operators.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — 비교 연산자 자체는 두 엔진 모두 오래전부터 있다. 이 주제에서 버전에 갈리는 것은 없다.\
> **선행** — [04 NULL 의 3값 논리](../04-null-three-valued-logic/). 왜 `UNKNOWN` 이 생기는지는 그쪽이 정본이고, **여기는 그래서 무슨 연산자를 쓰나**를 다룬다.

## 한눈에 — 쉽게 말하면

**`= NULL` 은 「모르는 것과 같은가?」를 묻는 것이다. 답은 「예」도 「아니오」도 아니라 「모른다」다.**

- 봉투 두 개가 있다. 둘 다 **안 열어 봤다**.
- "이 둘이 같은 카드인가?" — 모른다. **둘 다 모른다고 해서 같다고 할 수 없다.**
- 그런데 `WHERE` 는 「예」만 통과시킨다. 그래서 `= NULL` 은 **한 행도 못 고른다.**
- 그래서 SQL 에는 도구가 둘 따로 있다.\
  「**이 봉투가 안 열린 상태인가?**」를 묻는 `IS NULL` 과,\
  「**둘 다 안 열렸으면 같다고 치자**」는 `NULL` 안전 등호다.

| 비유 | 실체 |
|---|---|
| 안 열어 본 봉투 | `NULL` |
| "같은 카드인가?" → 모른다 | `a = b` 가 `UNKNOWN` |
| "봉투가 안 열린 상태인가?" | `IS NULL` — 답이 언제나 예/아니오 |
| "둘 다 안 열렸으면 같다고 치자" | `IS NOT DISTINCT FROM`(PG) · `<=>`(MySQL) |
| 봉투 목록에 안 열린 게 하나라도 있으면 | `NOT IN` 이 통째로 무너지는 자리 |

```text
연산자별로 나올 수 있는 답
                       TRUE   FALSE   UNKNOWN
  a = b                 O       O        O      <- NULL 이 끼면 UNKNOWN
  a <> b                O       O        O
  a IS NULL             O       O        -      <- 언제나 예/아니오
  a IS DISTINCT FROM b  O       O        -      <- 언제나 예/아니오
                                        ^^^
                                  WHERE 가 버리는 값
```

이 봉투가 **똑같은 구조로** SQL 의 `NULL` 비교다.\
그리고 이 주제에서 가장 비싼 사고 하나가 **`NOT IN` 목록에 `NULL` 이 섞이면 결과가 통째로 빈다**는 것이다.

> **`NULL` 안전 등호(NULL-safe equality)** — `NULL` 끼리를 **같다고 보는** 비교. 결과가 `UNKNOWN` 이 되지 않는다.\
> 예: MySQL 의 `NULL <=> NULL` 은 `1`(참). 같은 식의 `NULL = NULL` 은 `NULL` 이다.

> **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. 화면에는 `NULL` 로 찍힌다.\
> 예: `salary = NULL` 의 결과. `WHERE` 는 이것을 `FALSE` 와 똑같이 버린다([04번](../04-null-three-valued-logic/)).

## 이 주제가 답하려는 질문

1. **`= NULL` 이 왜 에러가 아니라 「0행」인가** — 에러였으면 오히려 안전했을 자리다.
2. **`NULL` 을 같은 값으로 보고 비교해야 할 때 무엇을 쓰나** — 그리고 그것이 왜 두 엔진에서 다른 이름인가.
3. **`NOT IN` 목록에 `NULL` 이 하나 섞이면 왜 결과가 전부 사라지나** — 그리고 처방은 무엇인가.

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

이 주제의 사고는 전부 **`dan` 의 `dept_id NULL`** 하나에서 난다 — 그 `NULL` 이 `NOT IN` 의 목록에 섞여 들어간다.\
`hr`(사원이 없는 부서)은 **찾아내야 하는 정답** 역할이다.

## 동작 방식

### 1. `= NULL` 은 문법 오류가 아니다 — 조용히 0행이다

**언제 쓰나** — 실수로. 다른 언어의 `== null` 습관이 그대로 넘어온다.

```text
(전) emp 4행이 WHERE salary = NULL 을 지난다
 id | salary | salary = NULL | 처분
----+--------+---------------+------
  1 |    300 | UNKNOWN       | 버림
  2 |    500 | UNKNOWN       | 버림
  3 |   NULL | UNKNOWN       | 버림   <- cho 조차 못 고른다
  4 |    400 | UNKNOWN       | 버림
                               ↓
                             0행
```

```text
### SQL: SELECT id, name FROM emp WHERE salary = NULL;
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

`<>` 로 뒤집어도 같다.

```text
### SQL: SELECT id, name FROM emp WHERE salary <> NULL;
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

그림 해설 — **`= NULL` 과 `<> NULL` 이 둘 다 0행이다.** 어느 쪽도 참이 되지 않는다.\
대가 — **에러가 아니라는 것이 이 자리의 가장 큰 위험이다.** 문법 검사도, 정적 분석도 통과한다. 「조건에 맞는 게 없나 보다」로 넘어간다.

`IS NULL` 은 바로 답한다.

```text
### SQL: SELECT id, name FROM emp WHERE salary IS NULL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  3 | cho                        +----+------+
(1 row)                          |  3 | cho  |
                                 +----+------+
```

---

### 2. `IS NULL` 은 왜 `UNKNOWN` 을 내지 않나

**언제 쓰나** — 「값이 없는 상태인지」를 물을 때. 이 주제에서 **유일하게 방언 차이가 없는 연산자**다.

```text
비교 연산자 (=, <>, <, >)           술어 (IS NULL, IS NOT NULL)
+---------------------------+      +---------------------------+
| 값끼리 견준다              |      | 상태를 본다                |
| 값이 없으면 견줄 수 없다    |      | 없다는 것 자체가 답이다     |
|   -> UNKNOWN              |      |   -> TRUE 또는 FALSE       |
+---------------------------+      +---------------------------+
```

```text
### SQL: SELECT NULL = NULL AS eq, NULL <> NULL AS ne, NULL IS NULL AS isnull;
--- PG 18.6 ---
  eq  |  ne  | isnull
------+------+--------
 NULL | NULL | t
(1 row)
--- MySQL 8.4.10 ---
+------+------+--------+
| eq   | ne   | isnull |
+------+------+--------+
| NULL | NULL |      1 |
+------+------+--------+
```

그림 해설 — `NULL = NULL` 은 `NULL`(= `UNKNOWN`)인데 `NULL IS NULL` 은 **`t`/`1`**, 즉 확실한 참이다.\
`IS NULL` 은 **값을 견주는 연산이 아니라 상태를 묻는 술어**라서 3번째 답이 없다.\
대가 — 없다. 다만 `IS NULL` 로는 「둘이 같은가」를 물을 수 없다 — 그건 다음 절의 연산자가 한다.

> **술어(predicate)** — 참/거짓을 내놓는 문법 요소. SQL 의 술어 중 일부는 `UNKNOWN` 을 내지 않는다.\
> 예: `IS NULL`·`IS DISTINCT FROM`·`EXISTS` 는 언제나 `TRUE`/`FALSE` 둘 중 하나다.

---

### 3. `NULL` 안전 등호 — 두 엔진이 서로의 문법을 거부한다

**언제 쓰나** — 「값이 바뀌었나」를 볼 때. `NULL` → `300` 도 변경이고 `300` → `NULL` 도 변경인데, `<>` 로는 둘 다 못 잡는다.

```text
   old   new    old <> new    IS DISTINCT FROM / <=> 로 본 "달라졌나"
  -----  -----  ----------    ------------------------------------
   300    300   FALSE          다르지 않다
   300    500   TRUE           다르다
   300   NULL   UNKNOWN  <-    다르다        <- <> 는 이 두 줄을 놓친다
  NULL    300   UNKNOWN  <-    다르다
  NULL   NULL   UNKNOWN        다르지 않다
```

PG 는 `IS [NOT] DISTINCT FROM`, MySQL 은 `<=>` 다. **서로의 문법을 문법 오류로 거부한다.**

```text
### SQL: SELECT 1 IS DISTINCT FROM 1 AS a, 1 IS DISTINCT FROM 2 AS b,
                1 IS DISTINCT FROM NULL AS c, NULL IS DISTINCT FROM NULL AS d;
--- PG 18.6 ---
 a | b | c | d
---+---+---+---
 f | t | t | f
(1 row)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'DISTINCT FROM 1 AS a, 1 IS DISTINCT FROM 2 AS b, 1 IS DISTINCT FROM NULL AS c, N' at line 1
```

```text
### SQL: SELECT 1 <=> 1 AS a, 1 <=> 2 AS b, 1 <=> NULL AS c, NULL <=> NULL AS d;
--- PG 18.6 ---
ERROR:  operator does not exist: integer <=> integer
LINE 1: SELECT 1 <=> 1 AS a, 1 <=> 2 AS b, 1 <=> NULL AS c, NULL <=>...
                 ^
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+---+---+---+---+
| a | b | c | d |
+---+---+---+---+
| 1 | 0 | 0 | 1 |
+---+---+---+---+
```

그림 해설 — 두 출력은 **정확히 서로의 부정**이다. `IS DISTINCT FROM` 은 「다른가」, `<=>` 는 「같은가」를 묻는다.

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 「같다」(NULL 안전) | `a IS NOT DISTINCT FROM b` | `a <=> b` |
| 「다르다」(NULL 안전) | `a IS DISTINCT FROM b` | `NOT (a <=> b)` |
| 상대 방언을 던지면 | `<=>` → **연산자 없음** | `IS DISTINCT FROM` → **`ERROR 1064`** |

실제 열에 걸어 본 결과도 정확히 대응한다 — **같은 3행**(`bob`·`cho`·`dan`)이 나온다.

```text
### SQL: SELECT id, name, salary FROM emp WHERE salary IS DISTINCT FROM 300 ORDER BY id;
--- PG 18.6 ---
 id | name | salary
----+------+--------
  2 | bob  |    500
  3 | cho  |   NULL
  4 | dan  |    400
(3 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'DISTINCT FROM 300 ORDER BY id' at line 1
```

```text
### SQL: SELECT id, name, salary FROM emp WHERE NOT (salary <=> 300) ORDER BY id;
--- PG 18.6 ---
ERROR:  operator does not exist: integer <=> integer
LINE 1: ...ELECT id, name, salary FROM emp WHERE NOT (salary <=> 300) O...
                                                             ^
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+----+------+--------+
| id | name | salary |
+----+------+--------+
|  2 | bob  |    500 |
|  3 | cho  |   NULL |
|  4 | dan  |    400 |
+----+------+--------+
```

`cho`(salary `NULL`)가 **들어온 것이 핵심**이다. 같은 자리에 `salary <> 300` 을 쓰면 `cho` 가 빠진다([04번](../04-null-three-valued-logic/)에서 확인한 것).\
대가 — **양쪽에서 다 도는 표현은 없다.** 이식이 필요하면 풀어 쓴다.

```text
### SQL: SELECT (salary = 300) OR (salary IS NULL AND 300 IS NULL) AS portable, id FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 portable | id                   +----------+----+
----------+----                  | portable | id |
 t        |  1                   +----------+----+
 f        |  2                   |        1 |  1 |
 NULL     |  3                   |        0 |  2 |
 f        |  4                   |     NULL |  3 |
(4 rows)                         |        0 |  4 |
                                 +----------+----+
```

> ⚠️ **이 풀어 쓴 형태는 완전한 대체가 아니다.** 위 출력의 3행(`cho`)이 `NULL` 이다 —\
> 상수 `300` 이 `NULL` 이 아니므로 `(salary IS NULL AND 300 IS NULL)` 이 `FALSE` 가 되고, 앞항의 `UNKNOWN` 이 살아남는다.\
> `WHERE` 에 쓰면 **버려지므로 결과는 맞지만**, `SELECT` 에 쓰면 `FALSE` 가 아니라 `NULL` 이 보인다.\
> 진짜로 `TRUE`/`FALSE` 만 필요하면 `(...) IS TRUE` 로 한 번 더 눌러야 한다([04번](../04-null-three-valued-logic/)).

#### 방언 — `ISNULL` 이라는 이름이 양쪽에 있는데 문법이 다르다

이름이 같아서 더 위험한 자리다. PG 는 **후위 연산자**, MySQL 은 **함수**다.

```text
### SQL: SELECT salary ISNULL AS pg_style FROM emp ORDER BY id;
--- PG 18.6 ---
 pg_style
----------
 f
 f
 t
 f
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'AS pg_style FROM emp ORDER BY id' at line 1
```

```text
### SQL: SELECT ISNULL(salary) AS fn_style, id FROM emp ORDER BY id;
--- PG 18.6 ---
ERROR:  function isnull(integer) does not exist
LINE 1: SELECT ISNULL(salary) AS fn_style, id FROM emp ORDER BY id;
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+----------+----+
| fn_style | id |
+----------+----+
|        0 |  1 |
|        0 |  2 |
|        1 |  3 |
|        0 |  4 |
+----------+----+
```

두 그림의 결론 — **둘 다 쓰지 말고 `IS NULL` 을 쓴다.** 표준이고 양쪽에서 같은 문법이다.

---

### 4. `NOT IN` 에 `NULL` 이 섞이면 결과가 통째로 빈다

**언제 쓰나** — 「저쪽 목록에 없는 것」을 찾을 때. **이 주제에서 가장 비싼 사고다.**

의도는 「사원이 한 명도 없는 부서」를 찾는 것이다. 답은 `hr`(30)이다.

```text
(전) emp.dept_id 목록을 뽑는다
     {10, 10, 20, NULL}
                  ^^^^ dan 때문에 NULL 이 들어 있다

(후) dept 의 세 행을 그 목록에 대고 NOT IN 으로 본다

 30 NOT IN (10, 20, NULL)
   = NOT (30 = 10  OR  30 = 20  OR  30 = NULL)
   = NOT (FALSE    OR  FALSE    OR  UNKNOWN  )
   = NOT (UNKNOWN)                                <- FALSE OR UNKNOWN = UNKNOWN
   = UNKNOWN                                      <- WHERE 가 버린다
```

행마다 진릿값을 찍어 보면 그대로 보인다.

```text
### SQL: SELECT d.id, d.id IN (SELECT dept_id FROM emp) AS in_any,
                d.id NOT IN (SELECT dept_id FROM emp) AS not_in_any
         FROM dept d ORDER BY d.id;
--- PG 18.6 ---
 id | in_any | not_in_any
----+--------+------------
 10 | t      | f
 20 | t      | f
 30 | NULL   | NULL
(3 rows)
--- MySQL 8.4.10 ---
+----+--------+------------+
| id | in_any | not_in_any |
+----+--------+------------+
| 10 |      1 |          0 |
| 20 |      1 |          0 |
| 30 |   NULL |       NULL |
+----+--------+------------+
```

그림 해설 — **`10`·`20` 은 `f`(거짓), `30` 만 `NULL`(= `UNKNOWN`)이다.**\
즉 `NOT IN` 이 `TRUE` 인 행이 **하나도 없다.** `WHERE` 에 걸면 0행이 나온다.

```text
### SQL: SELECT id, name FROM dept WHERE id NOT IN (SELECT dept_id FROM emp);
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

**이 0행은 「없다」는 답이 아니다.** 답은 `hr` 인데 `UNKNOWN` 에 삼켜진 것이다.\
대가 — 에러도 경고도 없다. 그리고 **`emp` 에 소속 없는 사원이 한 명도 없던 동안에는 이 질의가 정상 동작했다.** 데이터 하나가 들어오면서 조용히 망가진다.

> **반조인(anti join)** — 「저쪽에 짝이 없는 행」만 남기는 연산.\
> 예: 「사원이 없는 부서」. 조인 형태로서의 정본은 [19 SEMI·ANTI 조인](../19-semi-anti-join/)이다.

---

### 5. `IN` 은 멀쩡한데 `NOT IN` 만 터진다

**언제 쓰나** — 위 사고를 리뷰에서 놓치는 이유를 설명할 때.

```text
30 IN (10, 20, NULL)                    30 NOT IN (10, 20, NULL)
 = FALSE OR FALSE OR UNKNOWN             = NOT (FALSE OR FALSE OR UNKNOWN)
 = UNKNOWN                               = NOT UNKNOWN = UNKNOWN

10 IN (10, 20, NULL)                    10 NOT IN (10, 20, NULL)
 = TRUE  OR FALSE OR UNKNOWN             = NOT (TRUE OR ...)
 = TRUE            <- 번지지 않는다       = FALSE           <- 확실한 거짓
```

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

두 그림의 결론 — **`IN` 은 짝이 있으면 `TRUE` 가 확정되므로 `NULL` 이 번지지 않는다.**\
`NOT IN` 은 **모든 항목을 다 확인해야** 참이 되므로 `UNKNOWN` 하나가 전체를 물들인다.\
대가 — `IN` 으로 테스트해 보고 안심한 뒤 `NOT IN` 을 배포하는 사고가 여기서 난다.

---

### 6. 탐침 값 쪽이 `NULL` 이어도 사라진다

**언제 쓰나** — 목록에는 `NULL` 이 없는데 결과가 이상할 때. **방향이 반대인 같은 사고**다.

```text
dan 의 dept_id 는 NULL 이다
  NULL NOT IN (10, 20, 30)
    = NOT (NULL=10 OR NULL=20 OR NULL=30)
    = NOT (UNKNOWN OR UNKNOWN OR UNKNOWN)
    = UNKNOWN                                  <- dan 이 사라진다
```

```text
### SQL: SELECT id, name FROM emp WHERE dept_id NOT IN (10, 20, 30) ORDER BY id;
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

```text
### SQL: SELECT id, name FROM emp WHERE dept_id IN (10, 20, 30) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  1 | ann                        +----+------+
  2 | bob                        |  1 | ann  |
  3 | cho                        |  2 | bob  |
(3 rows)                         |  3 | cho  |
                                 +----+------+
```

두 그림의 결론 — `IN` 은 3행, `NOT IN` 은 0행이다. **3 + 0 ≠ 4.** 빠진 한 행이 `dan` 이다.\
「`IN` 의 여집합이 `NOT IN`」이라는 직관이 여기서 깨진다.\
대가 — 목록에 `NULL` 이 없어도 안전하지 않다. **양쪽 다 `NOT NULL` 이어야** `NOT IN` 이 여집합이 된다.

---

### 7. 처방 — `NOT EXISTS` 가 왜 안전한가

**언제 쓰나** — 반조인을 쓸 때마다. 기본 선택지로 삼는다.

```text
NOT IN                              NOT EXISTS
+---------------------------+      +---------------------------+
| 값끼리 견준다              |      | 행이 있나 없나만 본다        |
| NULL 이 끼면 UNKNOWN       |      | 진릿값이 TRUE/FALSE 둘뿐    |
|   -> WHERE 가 버린다        |      |   -> UNKNOWN 이 낄 자리 없음 |
+---------------------------+      +---------------------------+
```

```text
### SQL: SELECT id, name FROM dept d
         WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
 30 | hr                         +----+------+
(1 row)                          | 30 | hr   |
                                 +----+------+
```

두 번째 처방은 **목록에서 `NULL` 을 걸러 내는 것**이다.

```text
### SQL: SELECT d.id, d.id NOT IN (SELECT dept_id FROM emp WHERE dept_id IS NOT NULL) AS fixed
         FROM dept d ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | fixed                      +----+-------+
----+-------                     | id | fixed |
 10 | f                          +----+-------+
 20 | f                          | 10 |     0 |
 30 | t                          | 20 |     0 |
(3 rows)                         | 30 |     1 |
                                 +----+-------+
```

그림 해설 — `30` 이 `t`/`1` 로 바뀌었다. `NULL` 하나를 뺐을 뿐인데 답이 돌아왔다.\
대가 — **이 처방은 사람이 기억해야 유지된다.** 다음 사람이 `WHERE dept_id IS NOT NULL` 을 「불필요해 보여서」 지우면 다시 무너진다. 그래서 세 번째 처방이 제일 강하다 — **열에 `NOT NULL` 제약을 건다**([목록의 **45번 주제**](../45-check-not-null-default-generated-columns/)).

## 문법 — 형태와 규칙

SQL 은 형태가 아니라 **「어느 연산자가 어떤 답을 낼 수 있나」가 본체**인 언어다.

```sql
<식> IS NULL                      -- 양쪽 엔진 동일. TRUE/FALSE 만 낸다
<식> IS NOT NULL
<식> IS [NOT] DISTINCT FROM <식>  -- PostgreSQL. TRUE/FALSE 만 낸다
<식> <=> <식>                     -- MySQL. TRUE/FALSE 만 낸다
<식> [NOT] IN (<목록 | 서브질의>)  -- NULL 이 끼면 UNKNOWN 이 날 수 있다
[NOT] EXISTS (<서브질의>)          -- 양쪽 엔진 동일. TRUE/FALSE 만 낸다
```

규칙 다섯.

1. **`NULL` 과의 비교(`=`·`<>`·`<`·`>`)는 전부 `UNKNOWN`** 이다. 문법 오류가 아니라 조용한 0행이다.
2. **`IS NULL` 은 값을 견주지 않고 상태를 묻는다.** 그래서 `UNKNOWN` 이 없다. 양쪽 엔진 문법이 같다.
3. **`NULL` 안전 등호는 이름이 다르다** — PG `IS NOT DISTINCT FROM`, MySQL `<=>`. **양쪽에서 다 도는 표현은 없다.**
4. **`NOT IN` 은 양쪽 모두 `NOT NULL` 일 때만 `IN` 의 여집합이다.** 한쪽에라도 `NULL` 이 있으면 행이 사라진다.
5. **반조인의 기본 선택지는 `NOT EXISTS`** 다. `EXISTS` 계열에는 `UNKNOWN` 이 낄 자리가 없다.

#### 방언 — 인덱스를 타나

`NULL` 안전 비교가 **얼마나 비싼가**는 두 엔진에서 갈린다.\
10만 행 임시 표에 `v` 인덱스를 걸고 계획을 찍은 것이다(`study` 안의 세션 임시 표 — 롤백·삭제로 잔재 없음).

```text
--- PG 18.6 ---
=== (A) WHERE v IS NULL ===
 Index Scan using t_v_idx on t
   Index Cond: (v IS NULL)
=== (B) WHERE v = 5 ===
 Index Scan using t_v_idx on t
   Index Cond: (v = 5)
=== (C) WHERE v IS NOT DISTINCT FROM 5 ===
 Seq Scan on t
   Filter: (NOT (v IS DISTINCT FROM 5))
```

```text
--- MySQL 8.4.10 ---  (EXPLAIN 의 type/key 열만 옮긴다)
WHERE v IS NULL        ->  type=ref    key=v      rows=100     Using where; Using index
WHERE v = 5            ->  type=ref    key=v      rows=1       Using index
WHERE v <=> 5          ->  type=ref    key=v      rows=1       Using where; Using index
WHERE NOT (v <=> 5)    ->  type=index  key=v      rows=100649  Using where; Using index
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `IS NULL` | **인덱스 탄다** (`Index Cond: v IS NULL`) | **인덱스 탄다** (`type=ref`) |
| `NULL` 안전 등호 | **못 탄다** — `Seq Scan` + `Filter` | **탄다** — `type=ref`, `rows=1` |

그림 해설 — **같은 의미의 연산인데 비용이 다르다.** MySQL 의 `<=>` 는 인덱스 탐색으로 내려가고, PG 의 `IS NOT DISTINCT FROM` 은 전체 스캔 후 필터가 됐다.\
대가 — PG 에서 `NULL` 안전 등호를 `WHERE` 에 남발하면 인덱스가 죽는다. 대안은 `(v = 5 OR v IS NULL)` 처럼 **인덱스가 탈 수 있는 형태로 푸는 것**이다.\
(계획은 통계·버전에 따라 달라질 수 있다 — 계획 읽기의 정본은 [목록의 **58번 주제**](../58-explain-plan-tree/)다.)

## 어디서 틀리나

- **`= NULL` 로 쓴다.**\
  에러가 안 난다. 조용히 0행이다. `IS NULL` 이 유일한 방법이다.
- **`<> NULL` 로 「NULL 이 아닌 것」을 찾는다.**\
  이것도 0행이다. `IS NOT NULL` 을 쓴다.
- **`NOT IN` 의 목록에 `NULL` 이 섞인다.**\
  결과가 **항상 0행**이다. 그리고 `NULL` 이 들어오기 전까지는 잘 돌았다.
- **`IN` 이 잘 도니까 `NOT IN` 도 괜찮다고 본다.**\
  `IN` 은 `TRUE` 하나로 확정되고 `NOT IN` 은 전부 확인해야 한다. 안전성이 다르다.
- **탐침 쪽 `NULL` 을 잊는다.**\
  목록이 깨끗해도 `dan.dept_id` 가 `NULL` 이면 `dan` 이 사라진다. 위에서 `IN` 3행 + `NOT IN` 0행 = 3 ≠ 4 를 봤다.
- **`<=>` 와 `IS DISTINCT FROM` 이 양쪽에서 다 되는 줄 안다.**\
  서로를 문법 오류로 거부한다. 이식 코드에는 둘 다 못 쓴다.
- **`ISNULL` 을 쓴다.**\
  PG 는 후위 연산자 `x ISNULL`, MySQL 은 함수 `ISNULL(x)` 다. 이름만 같고 문법이 다르다. `IS NULL` 을 쓴다.
- **PG 에서 `IS NOT DISTINCT FROM` 을 `WHERE` 에 남발한다.**\
  인덱스를 못 탄다(위 계획). 큰 표에서는 이게 곧 장애다.
- **`(a = b) OR (a IS NULL AND b IS NULL)` 이 완전한 대체라고 본다.**\
  `WHERE` 에서는 맞지만 `SELECT` 에서는 `FALSE` 대신 `NULL` 이 나온다. 위 출력의 3행이 그 증거다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `= NULL` 이 `UNKNOWN` 인 것 | **표준 3값 논리** — 양쪽 문서 | 두 엔진 동일 출력 |
| `IS NULL` 의 문법과 의미 | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| `NOT IN` + `NULL` 이 0행인 것 | **3값 논리에서 따라 나온다** | 두 엔진 동일 출력 |
| `NOT EXISTS` 가 안전한 것 | **`EXISTS` 의 정의** — 진릿값이 둘뿐 | 두 엔진 동일 출력 |
| `IS DISTINCT FROM` / `<=>` 의 이름 | **각 엔진의 선택** | 서로를 문법 오류로 거부 |
| `ISNULL` 의 형태 | **각 엔진의 비표준 확장** | 후위 연산자 / 함수 |
| `NULL` 안전 등호가 인덱스를 타나 | **옵티마이저 구현** | PG `Seq Scan` / MySQL `type=ref` |

정리하면 — **「`NULL` 비교는 `UNKNOWN`」과 「`IS NULL` 로 물어라」만 언어 보장이고, 안전 등호의 이름과 비용은 엔진마다 다르다.**

## 언제 쓰고 언제 안 쓰나

- **「값이 없나」를 물을 때는 무조건 `IS NULL`.** 양쪽에서 같고 인덱스도 탄다.
- **「바뀌었나」를 볼 때만 `NULL` 안전 등호를 쓴다.** 변경 감지·업서트 비교·중복 판정이 그 자리다.
- **반조인은 `NOT EXISTS` 를 기본으로.** `NOT IN` 은 양쪽 열이 `NOT NULL` 임을 **스키마가 보장할 때만** 쓴다.
- **조인·반조인에 쓰는 열에는 `NOT NULL` 을 건다.** 이 주제의 사고 전부가 한꺼번에 사라진다.
- **PG 에서 큰 표에 `IS NOT DISTINCT FROM` 을 `WHERE` 조건으로 쓰지 않는다.** 필요하면 `(a = b OR (a IS NULL AND b IS NULL))` 로 풀어 인덱스를 살린다.
- **이식할 코드에는 안전 등호를 쓰지 않는다.** 대신 `NOT NULL` 제약이나 `COALESCE` 로 `NULL` 자체를 없앤다 — 다만 `COALESCE` 는 「몰랐다」는 사실을 지운다([06번](../06-conditional-expressions-case-coalesce/)).

## 핵심 문장

- `= NULL` 은 **에러가 아니라 0행**이다. 그래서 위험하다.
- `IS NULL` 은 **값을 견주지 않고 상태를 묻는다.** 그래서 `UNKNOWN` 이 없다.
- `NULL` 안전 등호는 **PG `IS NOT DISTINCT FROM` · MySQL `<=>`** 이고 **양쪽에서 다 도는 표현은 없다.**
- **`NOT IN` 목록에 `NULL` 이 하나라도 있으면 결과는 항상 0행이다.** 탐침 쪽이 `NULL` 이어도 그 행이 사라진다.
- `IN` 은 멀쩡한데 `NOT IN` 만 터진다 — **`TRUE` 하나로 끝나는 쪽과 전부 확인해야 하는 쪽**의 차이다.
- 처방은 셋 — **`NOT EXISTS`** · 목록에서 `NULL` 제거 · **`NOT NULL` 제약**. 마지막이 가장 강하다.

## 관련 자료

- [PostgreSQL 18 · Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html) — `IS DISTINCT FROM` 과 `ISNULL` 이 같은 페이지에 있다.
- [MySQL 8.4 · Comparison Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/comparison-operators.html) — `<=>` 와 `ISNULL()`.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `UNKNOWN` 이 왜 생기고 어떻게 번지나까지, 여기는 그래서 어떤 연산자를 고르나부터.**
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — `WHERE` 가 `TRUE` 만 통과시키는 것이 이 주제의 전제다.
- [06 조건 식 — CASE·COALESCE·NULLIF](../06-conditional-expressions-case-coalesce/) — **경계: 여기는 `NULL` 을 「비교」하는 법, 그쪽은 `NULL` 을 「다른 값으로 바꾸는」 법.**
- [07 DISTINCT 와 중복 제거](../07-distinct-and-duplicate-removal/) — `DISTINCT` 는 `NULL` 끼리를 **같은 값으로 묶는다.** 비교 규칙과 정반대인 자리다.
- [19 SEMI·ANTI 조인 — EXISTS·IN·NOT IN·NOT EXISTS](../19-semi-anti-join/) — **경계: 그쪽은 `EXISTS`/`IN` 을 조인 형태로 보는 것까지, 여기는 연산자의 진릿값까지.**
- **`NOT NULL` 제약**은 [목록의 **45번 주제**](../45-check-not-null-default-generated-columns/), **인덱스를 타고 안 타고**는 [**47번 주제**](../47-when-indexes-are-used/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **`NULL`** — 「값을 모른다」를 나타내는 표시. 값이 아니라 **값이 없음의 표시**다.\
  예: `cho` 의 `salary NULL` 은 「급여 0원」이 아니라 「급여를 모른다」다.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. 화면에는 `NULL` 로 찍힌다.\
  예: `salary = NULL` 의 결과. `WHERE` 가 `FALSE` 와 똑같이 버린다.
- **술어(predicate)** — 참/거짓을 내놓는 문법 요소.\
  예: `IS NULL`·`IS DISTINCT FROM`·`EXISTS` 는 `UNKNOWN` 을 내지 않는 술어다.
- **`IS NULL`** — 값이 `NULL` 인지 묻는 술어. 답은 언제나 `TRUE` 또는 `FALSE`.\
  예: `WHERE salary IS NULL` 은 `cho` 한 행을 고른다.
- **`NULL` 안전 등호** — `NULL` 끼리를 같다고 보는 비교.\
  예: MySQL `NULL <=> NULL` → `1`, PG `NULL IS NOT DISTINCT FROM NULL` → `t`.
- **`IS DISTINCT FROM`** — 「`NULL` 을 포함해 서로 다른가」를 묻는 PG 의 술어.\
  예: `1 IS DISTINCT FROM NULL` → `t`. 같은 식의 `1 <> NULL` 은 `NULL` 이다.
- **`<=>`** — MySQL 의 `NULL` 안전 등호 연산자.\
  예: `1 <=> NULL` → `0`(거짓). `1 = NULL` 은 `NULL` 이다.
- **반조인(anti join)** — 「저쪽에 짝이 없는 행」만 남기는 연산.\
  예: 사원이 없는 부서 `hr` 을 찾는 것. `NOT EXISTS` 가 안전한 형태다.
- **`NOT EXISTS`** — 서브질의가 한 행도 안 낼 때 `TRUE` 인 술어.\
  예: `NOT IN` 이 0행을 줄 자리에서 `hr` 을 제대로 찾아낸다.
- **탐침 값(probe value)** — `IN`/`NOT IN` 에서 목록과 견주는 왼쪽 값.\
  예: `dept_id NOT IN (10,20,30)` 의 `dept_id`. 이쪽이 `NULL` 이어도 행이 사라진다.

## 더 들어가면

- **왜 `NOT IN` 을 이렇게 정의했나.** `a NOT IN (S)` 는 정의상 `NOT (a = s1 OR a = s2 OR ...)` 이다. 이 전개를 알면 규칙을 외울 필요가 없다 — 3값 논리의 `OR` 표 한 장이면 결과가 따라 나온다([04번](../04-null-three-valued-logic/)).
- **`NULL` 안전 등호를 왜 따로 두었나.** 표준은 「`NULL` 은 값이 아니다」를 일관되게 밀어붙였고, 그 결과 「두 행이 같은가」를 직접 물을 방법이 사라졌다. `IS DISTINCT FROM` 은 그 구멍을 메우려고 나중에 들어온 술어다.
- **`GROUP BY`·`DISTINCT`·`UNION` 은 이 규칙을 안 따른다.** 그쪽은 「같다」가 아니라 「**구별할 수 없다**」를 기준으로 삼아 `NULL` 끼리를 한 덩어리로 묶는다([07번](../07-distinct-and-duplicate-removal/)). 같은 문서 안에 규칙이 둘 있는 셈이라 헷갈리는데, **비교는 `UNKNOWN`, 묶기는 같은 것 취급**으로 나눠 외우면 된다.
