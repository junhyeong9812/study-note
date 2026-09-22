# sql/05-NULL 비교 — IS NULL·IS DISTINCT FROM·NULL 안전 등호 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> 문서 근거는 [PG 18 Comparison Operators](https://www.postgresql.org/docs/18/functions-comparison.html) · [MySQL 8.4 Comparison Operators](https://dev.mysql.com/doc/refman/8.4/en/comparison-operators.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `WHERE salary = NULL` 의 결과 행 수와 그 위험

**출력**

```text
### SQL: SELECT id, name FROM emp WHERE salary = NULL;
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

**0행이다. 그리고 `salary` 가 `NULL` 인 `cho` 조차 안 나온다.**

**왜 그런가** — `=` 는 값끼리 견주는 연산인데 한쪽에 값이 없다. 견줄 수 없으니 답은 `UNKNOWN` 이다.

```text
 id | salary | salary = NULL | WHERE 의 처분
----+--------+---------------+---------------
  1 |    300 | UNKNOWN       | 버림
  2 |    500 | UNKNOWN       | 버림
  3 |   NULL | UNKNOWN       | 버림          <- 모르는 것끼리도 같다고 하지 않는다
  4 |    400 | UNKNOWN       | 버림
```

**위험한 것은 0행이 아니라 「에러가 아니라는 것」이다.**

```text
문법 검사        통과    <- SELECT ... WHERE salary = NULL 은 완벽한 문장이다
타입 검사        통과
정적 분석        통과
실행             0행
읽는 사람의 결론  "조건에 맞는 데이터가 없나 보다"
```

에러였다면 배포 전에 잡혔다. 조용한 0행이라 **「데이터가 없다」는 오답이 그대로 리포트에 실린다.**

---

### 2. `<> NULL` 로 뒤집으면 달라지는가

**아니다. 이쪽도 0행이다.**

```text
### SQL: SELECT id, name FROM emp WHERE salary <> NULL;
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

**왜 그런가** — `<>` 도 값끼리 견주는 연산이다. 한쪽에 값이 없으면 「다르다」고도 말할 수 없다.

```text
   =  NULL  ->  UNKNOWN  ->  0행
  <>  NULL  ->  UNKNOWN  ->  0행
   >  NULL  ->  UNKNOWN  ->  0행
  <=  NULL  ->  UNKNOWN  ->  0행
                             ^^^
              어떤 비교 연산자를 써도 결과가 같다
```

「`= NULL` 이 안 되면 `<> NULL` 로 뒤집으면 되겠지」가 이 주제에서 두 번째로 흔한 오답이다.\
**뒤집는 것으로는 못 빠져나온다.** 연산자의 종류가 아니라 **값을 견준다는 성질** 자체가 문제이기 때문이다.

---

### 3. `NULL IS NULL` 만 확실한 답을 내는 이유

**출력**

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

**`eq`·`ne` 는 `NULL`(= `UNKNOWN`), `isnull` 은 `t`/`1`(= 확실한 참)이다.**

**왜 그런가** — 앞의 둘은 **값을 견주는 연산**, 셋째는 **상태를 묻는 술어**다.

```text
비교 연산자                          술어 IS NULL
+---------------------------+      +---------------------------+
| "이 두 값이 같은가?"        |      | "이 자리에 값이 없는가?"    |
| 값이 있어야 답할 수 있다     |      | 있는지 없는지는 언제나 안다  |
|   -> 없으면 UNKNOWN        |      |   -> 항상 TRUE 또는 FALSE  |
+---------------------------+      +---------------------------+
```

> **술어(predicate)** — 참/거짓을 내놓는 문법 요소. SQL 의 술어 중 일부는 `UNKNOWN` 을 내지 않는다.\
> 예: `IS NULL`·`IS DISTINCT FROM`·`EXISTS`.

그래서 **`WHERE` 와 궁합이 맞는 것은 술어 쪽이다.** `WHERE` 는 `TRUE` 만 통과시키므로([01번](../01-logical-query-processing-order/)), `UNKNOWN` 을 낼 수 없는 연산자라야 「고른다」는 일이 제대로 된다.

`IS NULL` 은 **양쪽 엔진에서 문법도 결과도 같다** — 이 주제에서 방언 차이가 없는 유일한 자리다.

---

### 4. `IS DISTINCT FROM` 과 `<=>` — 두 엔진의 답

**출력**

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

**왜 그런가** — 두 연산자는 **묻는 방향이 반대**다. 그래서 출력이 서로의 부정으로 보인다.

| 견주는 두 값 | PG `IS DISTINCT FROM` (「다른가」) | MySQL `<=>` (「같은가」) |
|---|---|---|
| `1`, `1` | `f` | `1` |
| `1`, `2` | `t` | `0` |
| `1`, `NULL` | `t` | `0` |
| `NULL`, `NULL` | **`f`** | **`1`** |

마지막 줄이 이 연산자들의 존재 이유다 — **`NULL` 둘을 「같다」로 판정한다.** 일반 `=` 였다면 `UNKNOWN` 이다.

**그리고 서로의 문법을 거부한다.** PG 는 `<=>` 를 「그런 연산자 없음」으로, MySQL 은 `IS DISTINCT FROM` 을 **`ERROR 1064` 문법 오류**로 막는다.\
PG 쪽 에러가 「문법 오류」가 아니라 「연산자 없음」인 것도 의미가 있다 — PG 는 `<=>` 를 **사용자가 정의할 수도 있는 연산자 이름**으로 읽는다.

---

### 5. 두 엔진 모두에서 도는 `NULL` 안전 비교

**있다 — 풀어 쓰면 된다. 다만 `SELECT` 에 쓰면 `FALSE` 대신 `NULL` 이 나오는 한계가 있다.**

```sql
(a = b) OR (a IS NULL AND b IS NULL)
```

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

**한계가 3행(`cho`)에 보인다.**

```text
cho: salary 는 NULL, 상수는 300

  (NULL = 300)                    -> UNKNOWN
  OR (NULL IS NULL AND 300 IS NULL)
     ( TRUE          AND FALSE   ) -> FALSE
  UNKNOWN OR FALSE                 -> UNKNOWN      <- f 가 아니라 NULL 이 나온다
```

| 쓰는 자리 | 문제가 되나 |
|---|---|
| `WHERE` | **안 된다** — `UNKNOWN` 과 `FALSE` 를 똑같이 버리므로 결과가 맞다 |
| `SELECT` 목록 · `CASE` 의 조건 | **된다** — `FALSE` 를 기대한 자리에 `NULL` 이 온다 |

`SELECT` 에서도 `TRUE`/`FALSE` 만 원하면 한 번 더 누른다 — `((a = b) OR (a IS NULL AND b IS NULL)) IS TRUE`.\
`IS TRUE` 가 `UNKNOWN` 을 `FALSE` 쪽으로 누르는 술어라는 것은 [04번](../04-null-three-valued-logic/)에서 본 것이다.

더 강한 해법은 **애초에 `NULL` 을 안 만드는 것**이다 — 열에 `NOT NULL` 제약을 건다([목록의 **45번 주제**](../45-check-not-null-default-generated-columns/)).

---

### 6. `NOT IN` 에 `NULL` 이 섞였을 때의 행 수와 전개

**출력**

```text
### SQL: SELECT id, name FROM dept WHERE id NOT IN (SELECT dept_id FROM emp);
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

**0행이다. 그런데 정답은 `hr`(30) 한 행이다.**

**왜 그런가** — 서브질의가 내놓는 목록에 `dan` 의 `NULL` 이 섞여 있다.

```text
emp.dept_id 목록 = {10, 10, 20, NULL}
                                ^^^^ dan

 30 NOT IN (10, 20, NULL)
   = NOT (30 = 10  OR  30 = 20  OR  30 = NULL)
   = NOT (FALSE    OR  FALSE    OR  UNKNOWN  )
   = NOT (UNKNOWN)                               <- FALSE OR UNKNOWN = UNKNOWN
   = UNKNOWN                                     <- WHERE 가 버린다
```

행마다 진릿값을 찍으면 그대로 보인다 — **`TRUE` 인 행이 하나도 없다.**

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

**`30` 행의 `not_in_any` 가 `NULL`** 이다. 이 한 칸이 0행의 정체다.

가장 무서운 성질은 **시간차**다.

```text
어제: emp 에 소속 없는 사원이 없었다   ->  목록에 NULL 없음  ->  질의가 정상 동작
오늘: dan 이 입사했고 부서 배정 전이다  ->  목록에 NULL 하나  ->  결과가 통째로 0행
```

코드는 한 글자도 안 바뀌었고, 에러도 경고도 없다.

---

### 7. `IN` 은 왜 멀쩡한가

**`IN` 은 `TRUE` 하나로 판정이 끝나고, `NOT IN` 은 전부 확인해야 참이 되기 때문이다.**

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

```text
10 IN (10, 20, NULL)                    10 NOT IN (10, 20, NULL)
 = TRUE OR FALSE OR UNKNOWN              = NOT (TRUE OR FALSE OR UNKNOWN)
 = TRUE            <- 확정, 번지지 않는다  = NOT TRUE = FALSE     <- 확정

30 IN (10, 20, NULL)                    30 NOT IN (10, 20, NULL)
 = FALSE OR FALSE OR UNKNOWN             = NOT UNKNOWN
 = UNKNOWN         <- 여기서 무너진다     = UNKNOWN              <- 여기서 무너진다
```

**`OR` 는 `TRUE` 를 만나면 나머지를 안 봐도 된다**([04번](../04-null-three-valued-logic/)의 `TRUE OR UNKNOWN = TRUE`).\
그래서 목록에 짝이 **있는** 행은 `NULL` 의 영향을 안 받는다. 짝이 **없는** 행만 `UNKNOWN` 에 빠지는데, **하필 그 행들이 `NOT IN` 이 찾으려는 답**이다.

```text
IN 이 찾는 것        = 짝이 있는 행      -> NULL 의 영향 없음  -> 잘 돈다
NOT IN 이 찾는 것    = 짝이 없는 행      -> 전부 UNKNOWN      -> 전멸
```

**그래서 `IN` 으로 테스트하고 안심한 뒤 `NOT IN` 을 배포하는 사고가 난다.** 두 연산자는 서로의 여집합처럼 보이지만 안전성이 완전히 다르다.

---

### 8. 탐침 쪽이 `NULL` 일 때 — `IN` + `NOT IN` 이 4가 되는가

**출력**

```text
(A)
### SQL: SELECT id, name FROM emp WHERE dept_id IN (10, 20, 30) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  1 | ann                        +----+------+
  2 | bob                        |  1 | ann  |
  3 | cho                        |  2 | bob  |
(3 rows)                         |  3 | cho  |
                                 +----+------+

(B)
### SQL: SELECT id, name FROM emp WHERE dept_id NOT IN (10, 20, 30) ORDER BY id;
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

**3 + 0 = 3 ≠ 4 다.** `dan` 이 어느 쪽에도 없다.

**왜 그런가** — 이번엔 목록이 깨끗하다(`10, 20, 30` 에 `NULL` 없음). **왼쪽 탐침 값**이 `NULL` 이다.

```text
dan.dept_id = NULL

  NULL IN (10, 20, 30)
    = (NULL=10) OR (NULL=20) OR (NULL=30)
    = UNKNOWN OR UNKNOWN OR UNKNOWN
    = UNKNOWN                              -> (A)에서 탈락

  NULL NOT IN (10, 20, 30)
    = NOT UNKNOWN
    = UNKNOWN                              -> (B)에서도 탈락
```

> **탐침 값(probe value)** — `IN`/`NOT IN` 에서 목록과 견주는 왼쪽 값.\
> 예: `dept_id NOT IN (10,20,30)` 의 `dept_id`. 이쪽이 `NULL` 이면 그 행은 양쪽 결과에서 다 빠진다.

**정리하면 위험한 자리가 둘이다.**

| `NULL` 이 어디 있나 | `IN` | `NOT IN` |
|---|---|---|
| 목록(서브질의 결과)에 | 영향 없음 | **전멸** |
| 탐침 값(왼쪽 열)에 | 그 행만 빠짐 | 그 행만 빠짐 |

**양쪽 다 `NOT NULL` 일 때만** `NOT IN` 이 `IN` 의 여집합이 된다.

---

### 9. `NOT IN` 사고를 고치는 방법 셋

**(A) `NOT EXISTS` 로 바꾼다 · (B) 목록에서 `NULL` 을 거른다 · (C) 열에 `NOT NULL` 제약을 건다.**

```text
(A) NOT EXISTS
### SQL: SELECT id, name FROM dept d
         WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
 30 | hr                         +----+------+
(1 row)                          | 30 | hr   |
                                 +----+------+
```

```text
(B) 목록에서 NULL 제거
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

**(A)가 안전한 이유** — `EXISTS` 는 값을 견주지 않는다. 「행이 있나 없나」만 본다.

```text
NOT IN                              NOT EXISTS
값끼리 견준다                        행의 존재만 본다
진릿값 3개 (T/F/UNKNOWN)             진릿값 2개 (T/F)
   -> UNKNOWN 이 낄 자리가 있다          -> UNKNOWN 이 낄 자리가 없다
```

**셋의 강도는 이 순서다.**

| 처방 | 강도 | 약점 |
|---|---|---|
| (B) 목록에서 `NULL` 제거 | 약함 | **사람이 기억해야 유지된다.** 다음 사람이 「불필요해 보여서」 지우면 재발 |
| (A) `NOT EXISTS` | 중간 | 습관이 되면 안전. 다만 새 질의를 쓸 때마다 다시 선택해야 한다 |
| (C) `NOT NULL` 제약 | **가장 강함** | **엔진이 강제한다.** 데이터가 들어올 수 없으므로 질의를 어떻게 쓰든 안전 |

(C)가 가장 강한 이유는 **방어선이 질의가 아니라 스키마에 있기 때문**이다. 질의는 수백 개지만 제약은 한 줄이다.\
제약 문법 자체는 [목록의 **45번 주제**](../45-check-not-null-default-generated-columns/), 반조인의 형태는 [19 SEMI·ANTI 조인](../19-semi-anti-join/)이 정본이다.

---

### 10. `salary ISNULL` 과 `ISNULL(salary)` — 어느 엔진에서 도나

**출력**

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

**(A) 후위 연산자 `x ISNULL` 은 PG 전용 · (B) 함수 `ISNULL(x)` 는 MySQL 전용이다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `x ISNULL` | **후위 연산자로 동작** | `ERROR 1064` 문법 오류 |
| `ISNULL(x)` | **`function isnull(integer) does not exist`** | **함수로 동작** |
| `x IS NULL` | ✓ | ✓ |

**왜 그런가** — 둘 다 **표준이 아니라 각 엔진의 편의 확장**이다. 이름만 같고 문법 범주가 다르다(연산자 / 함수).

**교훈은 「어느 쪽이 맞나」가 아니라 「둘 다 쓰지 마라**」다.\
`IS NULL` 은 양쪽에서 문법도 결과도 같고, 인덱스도 탄다(11번). 비표준 별명을 쓸 이유가 없다.

---

### 11. `IS NULL` 과 `NULL` 안전 등호는 인덱스를 타나

**`IS NULL` 은 양쪽 다 탄다. `NULL` 안전 등호는 MySQL 만 탄다.**

10만 행짜리 세션 임시 표에 `v` 인덱스를 걸고 계획을 찍은 것이다(`study` 안에서 만들고 롤백·삭제해 잔재 없음).

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
--- MySQL 8.4.10 ---  (EXPLAIN 의 type/key/rows 열)
WHERE v IS NULL        ->  type=ref    key=v   rows=100       Using where; Using index
WHERE v = 5            ->  type=ref    key=v   rows=1         Using index
WHERE v <=> 5          ->  type=ref    key=v   rows=1         Using where; Using index
WHERE NOT (v <=> 5)    ->  type=index  key=v   rows=100649    Using where; Using index
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `IS NULL` | **`Index Cond`** — 탐색으로 내려간다 | **`type=ref`** — 탐색 |
| `= 5` | **`Index Cond`** | **`type=ref`, `rows=1`** |
| `NULL` 안전 등호 | **`Seq Scan` + `Filter`** — 못 탄다 | **`type=ref`, `rows=1`** — 탄다 |
| 그 부정 | — | `type=index` — 인덱스 전체 훑기 |

**왜 그런가** — `IS NULL` 은 두 엔진 모두 인덱스가 `NULL` 을 담고 색인 조건으로 내려보낼 수 있는 형태다.\
`IS NOT DISTINCT FROM` 은 PG 에서 **색인 조건으로 내려가지 못해** 스캔 후 필터가 됐다.

**실무 함의** — PG 에서 큰 표의 `WHERE` 에 `IS NOT DISTINCT FROM` 을 쓰면 그 자체가 장애 원인이 된다.\
대안은 인덱스가 탈 수 있는 형태로 푸는 것이다 — `(v = 5 OR v IS NULL)`.

**이 항목은 구현 의존이다.** 통계·버전·데이터 분포가 바뀌면 계획도 바뀐다. 계획 읽기의 정본은 [목록의 **58번 주제**](../58-explain-plan-tree/), 인덱스를 타고 안 타고는 [**47번 주제**](../47-when-indexes-are-used/)다.

---

### 12. `NULL = NULL` 이 참이 아닌데 `DISTINCT` 는 왜 한 행으로 접나

**`DISTINCT` 는 「같은가」가 아니라 「구별할 수 있는가」를 기준으로 쓰기 때문이다.**

```text
비교에서는                        묶기에서는
NULL = NULL  ->  UNKNOWN          NULL 과 NULL  ->  구별할 수 없다  ->  한 행
(같다고 하지 않는다)                (같다고 말하지 않으면서 하나로 접는다)
```

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      20                         |    NULL |
    NULL   <- 한 행              |      10 |
(3 rows)                         |      20 |
                                 +---------+
```

**왜 이렇게 나눠 놨나** — 두 기준은 **다른 질문에 답한다.**

```text
비교(=)         "이 두 값이 같은 값인가?"        모르면 모른다고 해야 한다
묶기(DISTINCT)  "이 두 행을 구별할 수 있는가?"   둘 다 모르면 구별할 수 없다
```

「모르는 값 둘이 같다」고 말하는 것과 「모르는 값 둘을 구별할 수 없다」고 말하는 것은 다르다.\
`GROUP BY`·`DISTINCT`·`UNION` 은 후자를 쓰고, `=`·`<>` 는 전자를 쓴다.

> **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 묶기 기준.\
> 예: `NULL` 둘은 같다고 말할 수 없지만 서로 구별할 수도 없으므로 한 행이 된다.

**외울 때는 둘로 나눠서** — **비교는 `UNKNOWN`, 묶기는 같은 것 취급.**\
그리고 이름이 통하는 자리가 있다 — PG 의 `IS NOT DISTINCT FROM` 이 바로 **묶기 기준을 비교 연산자로 꺼내 쓴 것**이다.\
중복 제거 쪽 규칙의 정본은 [07번](../07-distinct-and-duplicate-removal/)이다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `= NULL` · `<> NULL` (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러가 아니라 0행이라는 것이 근거** |
| `IS NULL` 진릿값 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | |
| ★ `IS DISTINCT FROM` / `<=>` (4번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **상호 거부 에러 메시지가 근거** |
| 이식 형태와 그 한계 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `SELECT` 에서 `NULL` 이 남는 것 확인 |
| ★ `NOT IN` + `NULL` (6번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 행별 진릿값 표 + 0행 |
| `IN` 대조 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | |
| 탐침 쪽 `NULL` (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **3 + 0 ≠ 4** |
| 처방 셋 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `NOT EXISTS` · `IS NOT NULL` 필터 |
| `ISNULL` 방언 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 에러 메시지가 근거** |
| 인덱스 사용 (11번) | PG 18.6 · MySQL 8.4.10 | 각 3~4회 | **구현 의존** — 10만 행 임시 표, 롤백·삭제 확인 |
| `DISTINCT` 와 `NULL` (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 07번과 공유 |

**구현 의존 항목** — 11번의 계획뿐이다. `Seq Scan` 대 `Index Scan` 도, MySQL 의 `type=ref` 도 옵티마이저의 선택이다.\
다만 **`IS NOT DISTINCT FROM` 이 색인 조건으로 안 내려간 것은 우연이 아니다** — 인덱스 접근 경로가 지원하는 연산자 집합의 문제다.

**언어 보장 항목** — 1~10·12번. `NULL` 비교가 `UNKNOWN` 인 것, `IS NULL` 이 확실한 답을 내는 것,\
`NOT IN` 목록에 `NULL` 이 있으면 `TRUE` 가 안 나오는 것, `EXISTS` 에 `UNKNOWN` 이 없는 것은 **두 엔진에서 같았다.**

**버전** — 이 주제에서 버전에 갈리는 것은 없다. 다음 버전에서는 **11번(계획)만** 다시 돌리면 된다.
