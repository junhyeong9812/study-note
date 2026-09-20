# sql/04-NULL 의 3값 논리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> 문서 근거는 [PG 18 비교 연산자](https://www.postgresql.org/docs/18/functions-comparison.html) · [MySQL 8.4 NULL 다루기](https://dev.mysql.com/doc/refman/8.4/en/working-with-null.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. (A)와 (B)의 합이 전체와 같은가

**같지 않다. 1 + 2 = 3 인데 전체는 4다.**

```text
 id | salary | salary > 400 | salary <= 400 | 어디에 들어가나
----+--------+--------------+---------------+----------------
  1 |    300 | FALSE        | TRUE          | (B)
  2 |    500 | TRUE         | FALSE         | (A)
  3 |   NULL | UNKNOWN      | UNKNOWN       | 어느 쪽도 아니다  <- cho
  4 |    400 | FALSE        | TRUE          | (B)
```

```text
### SQL: SELECT COUNT(*) AS gt FROM emp WHERE salary > 400;
--- PG 18.6 ---   --- MySQL 8.4.10 ---
 gt               +----+
----              | gt |
  1               +----+
                  |  1 |
                  +----+

### SQL: SELECT COUNT(*) AS le FROM emp WHERE salary <= 400;
--- PG 18.6 ---   --- MySQL 8.4.10 ---
 le               +----+
----              | le |
  2               +----+
                  |  2 |
                  +----+

### SQL: SELECT COUNT(*) AS total FROM emp;
--- PG 18.6 ---   --- MySQL 8.4.10 ---
 total            +-------+
-------           | total |
     4            +-------+
                  |     4 |
                  +-------+
```

**원인은 `WHERE` 가 `TRUE` 만 통과시킨다는 것 하나다.**\
`cho` 의 조건 판정은 두 질의 모두 `UNKNOWN` 이었고, `WHERE` 는 `UNKNOWN` 을 `FALSE` 와 똑같이 버린다.

> **`UNKNOWN`** — 「판정 불가」 진릿값. `NULL` 이 비교에 끼면 나오고, 화면에는 `NULL` 로 찍힌다.\
> 예: `NULL > 400` 의 결과.

**전체를 둘로 정확히 가르고 싶으면 `UNKNOWN` 을 한쪽으로 눌러야 한다.**

```text
### SQL: SELECT COUNT(*) AS c FROM emp WHERE (salary > 400) IS NOT TRUE;
--- PG 18.6 ---   --- MySQL 8.4.10 ---
 c                +---+
---               | c |
 3                +---+
                  | 3 |
                  +---+
```

이제 `1 + 3 = 4` 다. 다만 이건 **「모름」을 「아니오」로 취급하기로 결정한 것**이다 — 도메인상 그게 맞는지는 SQL 이 답해 주지 않는다.

이 사고가 위험한 이유는 **에러가 안 나기 때문**이다. 두 질의 모두 정상 종료하고, 리포트에 한 건이 조용히 빈다.

---

### 2. `TRUE AND NULL`, `FALSE AND NULL`, `TRUE OR NULL`, `FALSE OR NULL`, `NOT NULL`

**순서대로 `UNKNOWN`, `FALSE`, `TRUE`, `UNKNOWN`, `UNKNOWN`.**

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

**규칙 한 줄 — `UNKNOWN` 은 결과가 아직 안 정해졌을 때만 번진다.**

```text
AND                                 OR
모르는 쪽이 무엇이든                모르는 쪽이 무엇이든
결과가 FALSE 로 정해지면 FALSE      결과가 TRUE 로 정해지면 TRUE

FALSE AND ?  = FALSE   (안 번짐)    TRUE  OR ?  = TRUE    (안 번짐)
TRUE  AND ?  = ?       (번짐)       FALSE OR ?  = ?       (번짐)
```

전체 진리표로 쓰면 이렇다.

| a | b | `a AND b` | `a OR b` |
|---|---|---|---|
| TRUE | UNKNOWN | UNKNOWN | **TRUE** |
| FALSE | UNKNOWN | **FALSE** | UNKNOWN |
| UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

`NOT UNKNOWN = UNKNOWN` 은 직관적이다 — **모르는 것을 뒤집어도 모른다.**\
이 한 줄이 1번의 "조건을 뒤집어도 안 돌아온다"의 근거이기도 하다.

**표시 차이 — 방언이지만 의미는 같다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `TRUE` 의 표시 | `t` | `1` |
| `FALSE` 의 표시 | `f` | `0` |
| `UNKNOWN` 의 표시 | `NULL` | `NULL` |
| 근거 | 진짜 `boolean` 타입 | `BOOLEAN` 은 `TINYINT(1)` 의 다른 이름 |

**판정 결과는 양쪽이 완전히 같다.** 타입 체계 이야기는 목록의 35번이다.

---

### 3. `WHERE salary <> 300` 에 `cho` 가 들어오는가

**들어오지 않는다.** 결과는 `bob` 과 `dan` 두 행이다.

```text
 id | salary | salary <> 300 | 처분
----+--------+---------------+------
  1 |    300 | FALSE         | 버림
  2 |    500 | TRUE          | 통과
  3 |   NULL | UNKNOWN       | 버림   <- cho. "300 이 아닌 게 확실한가?" -> 모른다
  4 |    400 | TRUE          | 통과
```

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

**`<>` 는 「같지 않다」가 아니라 「같지 않음이 확인된다」로 읽어야 한다.**\
`cho` 의 급여를 모르니 300 과 다르다고 확인할 수 없고, 그래서 `UNKNOWN` 이다.

`NOT` 으로 감싸도 같다.

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

`cho` 를 같이 데려오려면 **`NULL` 을 명시적으로 부른다.**

```sql
SELECT id, name FROM emp WHERE salary <> 300 OR salary IS NULL;
-- 또는
SELECT id, name FROM emp WHERE (salary <> 300) IS NOT FALSE;
```

이 자리에서 `= NULL` 을 시도하는 것이 초보자의 첫 실수다 — **에러가 안 나서** 잘못된 줄 모른다.

```text
### SQL: SELECT NULL = NULL AS eq, NULL <> NULL AS ne, NULL = 0 AS eq0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  eq  |  ne  | eq0               +------+------+------+
------+------+------             | eq   | ne   | eq0  |
 NULL | NULL | NULL              +------+------+------+
(1 row)                          | NULL | NULL | NULL |
                                 +------+------+------+
```

`NULL = 0` 도 `UNKNOWN` 이라는 점을 같이 기억한다 — **`NULL` 은 0 이 아니다.**

---

### 4. `SELECT id, name FROM dept WHERE id NOT IN (SELECT dept_id FROM emp);` 의 행 수

**0행이다. 그리고 그것은 오답이다** — 의도한 답은 `hr` 한 행이었다.

서브쿼리가 내놓는 목록은 `{10, 10, 20, NULL}` 이다. `dan` 의 `dept_id NULL` 이 들어 있다.

```text
30 NOT IN (10, 20, NULL)
  = NOT (30 = 10  OR  30 = 20  OR  30 = NULL)
  = NOT (FALSE    OR  FALSE    OR  UNKNOWN  )
  = NOT (         UNKNOWN                   )     <- FALSE OR UNKNOWN = UNKNOWN (2번)
  =               UNKNOWN                          <- NOT UNKNOWN = UNKNOWN
                     ↓
              WHERE 가 버린다
```

10 과 20 도 같은 식으로 전개하면 `NOT (TRUE OR ...) = FALSE` 라 역시 버려진다.\
**결국 세 행 모두 통과하지 못한다.**

```text
### SQL: SELECT id, name FROM dept WHERE id NOT IN (SELECT dept_id FROM emp);
--- PG 18.6 ---
 id | name
----+------
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

식만으로 확인하고 싶으면 리터럴로 던져 볼 수 있다.

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

`NULL` 이 없을 때(`in_no_null`)는 `FALSE` 가 제대로 나오고, `NULL` 이 하나 끼자 `UNKNOWN` 이 된다.

**일반화 — 목록에 `NULL` 이 하나라도 있으면 `NOT IN` 은 절대 `TRUE` 가 될 수 없다.** 결과는 언제나 0행이다.

**`IN` 쪽은 멀쩡하다**는 것이 이 함정을 더 위험하게 만든다.

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

`IN` 으로 테스트해 맞는 걸 확인하고 `NOT IN` 을 배포하면 **조용히 빈 결과**가 나간다.

---

### 5. `NOT EXISTS` 로 쓰면 달라지는가

**달라진다. `hr` 한 행이 제대로 나온다.**

```text
(A) NOT IN — 0행                      (B) NOT EXISTS — 1행
--- PG 18.6 ---                        --- PG 18.6 ---
 id | name                              id | name
----+------                            ----+------
(0 rows)                                30 | hr
--- MySQL 8.4.10 ---                   (1 row)
(빈 결과)                               --- MySQL 8.4.10 ---
                                       +----+------+
                                       | id | name |
                                       +----+------+
                                       | 30 | hr   |
                                       +----+------+
```

(B)의 실제 질의:

```sql
SELECT id, name FROM dept d
WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id)
ORDER BY id;
```

**안전한 이유 — `EXISTS` 의 진릿값은 둘뿐이다.**

```text
NOT IN 이 묻는 것                     NOT EXISTS 가 묻는 것
"이 값이 저 목록의 어느 것과도          "이 조건을 만족하는 행이
 같지 않음이 확인되는가?"                하나라도 있는가?"
   -> 값끼리 비교한다                     -> 행을 센다
   -> NULL 과 비교하면 UNKNOWN            -> 0행이냐 1행 이상이냐, 둘뿐
   -> 진릿값 셋                           -> 진릿값 둘. UNKNOWN 이 낄 자리가 없다
```

`dept.id = 30` 에 대해 안쪽 질의는 `emp` 를 훑는다.\
`dan` 의 `dept_id NULL` 과 비교한 `NULL = 30` 은 `UNKNOWN` 이고, 안쪽 `WHERE` 가 그 행을 **버린다.**\
남은 행이 0개 → `EXISTS` 는 `FALSE` → `NOT EXISTS` 는 `TRUE`. **`UNKNOWN` 이 바깥으로 새 나가지 못한다.**

> **`EXISTS`** — 서브쿼리가 한 행이라도 내면 `TRUE`, 아니면 `FALSE` 인 술어. 행의 *내용*은 안 본다.\
> 예: `SELECT 1` 을 쓰든 `SELECT *` 를 쓰든 결과가 같다.

처방을 셋으로 정리하면 이렇다.

| 처방 | 언제 | 대가 |
|---|---|---|
| `NOT EXISTS` 로 바꾼다 | 기본 선택 | 없음. 상관 서브쿼리라 읽기가 조금 길다 |
| 서브쿼리에 `WHERE ... IS NOT NULL` 을 건다 | `NOT IN` 형태를 유지해야 할 때 | 누가 나중에 지우면 다시 터진다 |
| 그 열에 `NOT NULL` 제약을 건다 | 도메인상 `NULL` 이 의미 없을 때 | 스키마 변경이 필요하다 |

세 번째가 근본 처방이다 — **`NULL` 이 들어올 수 없으면 이 함정 자체가 생기지 않는다.**

---

### 6. `COUNT(*)`, `COUNT(salary)`, `SUM(salary)`, `AVG(salary)`

**4, 3, 1200, 400 이다. 그리고 `AVG` 의 분모는 `COUNT(salary)`(=3) 이다.**

```text
emp.salary = [300, 500, NULL, 400]

COUNT(*)      -> 4      행을 센다. 값을 안 본다
COUNT(salary) -> 3      NULL 이 아닌 값만 센다
SUM(salary)   -> 1200   NULL 을 건너뛰고 더한다 (300 + 500 + 400)
AVG(salary)   -> 400    1200 / 3.   1200 / 4 = 300 이 아니다
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

두 엔진의 값이 완전히 같다. **소수 자릿수만 다르다** — `AVG` 의 결과 타입 차이일 뿐 값은 400 으로 같다(수치 타입은 목록의 36번).

**규칙 한 줄 — 집계는 `NULL` 을 건너뛴다. 예외는 `COUNT(*)` 하나다.**

```text
        값을 보는 집계                    행을 세는 집계
        +--------------------+           +--------------------+
        | COUNT(열)          |           | COUNT(*)           |
        | SUM · AVG · MIN    |           |                    |
        | MAX · STRING_AGG   |           |                    |
        +--------------------+           +--------------------+
          NULL 을 건너뛴다                  NULL 이든 아니든 센다
```

**이 차이가 위험한 이유는 숫자가 그럴듯해서다.**\
「평균 급여 400」은 「4명의 평균」처럼 읽히지만 실제로는 「급여가 기록된 3명의 평균」이다.\
`AVG` 를 쓸 때는 `COUNT(*)` 과 `COUNT(열)` 을 같이 뽑아 **분모를 눈으로 확인**하는 편이 안전하다.

`COUNT` 의 세 형태(`COUNT(*)`·`COUNT(열)`·`COUNT(DISTINCT 열)`)는 목록의 21번이 정본이다.

---

### 7. `dept_id = 20` 그룹의 `SUM(salary)`

**`0` 이 아니라 `NULL` 이다.**

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

`dept_id=20` 그룹에는 `cho` 한 명이 있고 그 사람의 급여가 `NULL` 이다.\
`SUM` 은 `NULL` 을 건너뛰므로 **더할 값이 하나도 남지 않고**, 그때의 결과는 0 이 아니라 `NULL` 이다.

```text
SUM([300, 500])      -> 800      값이 있다
SUM([400])           -> 400      값이 있다
SUM([NULL])          -> NULL     건너뛰고 나니 아무것도 없다  <- 0 이 아니다
SUM(빈 그룹)          -> NULL     (행이 아예 없어도 같다)
```

「0원을 더한 것」과 「더할 것이 없었던 것」은 다르다 — SQL 은 **후자를 `NULL` 로 표현**한다.

**이것이 애플리케이션에서 터지는 자리다.**\
`int` 로 받으면 `NullPointerException`, 자동 언박싱이 있는 언어에서는 더 조용히 터진다.

```sql
SELECT dept_id, COALESCE(SUM(salary), 0) AS s FROM emp GROUP BY dept_id;
```

`COALESCE` 를 씌우면 0 으로 보인다. 다만 그건 「합계 0원」과 「기록 없음」을 **같은 것으로 합치기로 결정**한 것이다.

참고로 `COUNT` 는 이 문제가 없다 — **값이 없으면 0을 준다.** 집계 중 `COUNT` 만 빈 입력에 `NULL` 이 아닌 값을 낸다.

`dept_id=NULL` 그룹(=`dan`)이 존재한다는 점도 같이 본다 — 8번으로 이어진다.

---

### 8. `NULL = NULL` 이 참이 아닌데 `GROUP BY` 는 왜 한 그룹으로 묶는가

**비교의 기준과 묶기의 기준이 다르기 때문이다.**\
비교는 **「같은가」**를 묻고, `GROUP BY`·`DISTINCT` 는 **「구별할 수 있는가」**를 묻는다.

```text
비교 (WHERE·ON·HAVING)              묶기 (GROUP BY·DISTINCT)
+---------------------------+       +---------------------------+
| 묻는 것: 같다고 말할 수    |       | 묻는 것: 서로 구별할 수    |
|          있는가            |       |          있는가            |
| NULL = NULL -> UNKNOWN     |       | NULL 과 NULL -> 구별 불가  |
| (같다고 말할 수 없다)       |       | (그러므로 한 그룹)         |
+---------------------------+       +---------------------------+
```

두 규칙은 **모순이 아니다.** 「같다고 확인할 수 없다」와 「서로 다르다고 확인할 수 없다」는 둘 다 참이다.

`GROUP BY` 쪽은 7번 출력에서 이미 봤다 — `dept_id NULL` 인 행(`dan`)이 **하나의 그룹**으로 나왔다.\
`DISTINCT` 도 같다.

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

`emp` 에는 `NULL` 인 `salary` 가 하나뿐이라 접힌 게 안 보이지만, 둘 이상이어도 **한 행**으로 나온다.

> **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 기준.\
> 예: `GROUP BY`·`DISTINCT`·`UNION` 의 중복 제거가 전부 이 기준을 쓴다.

**이 기준을 비교에서도 쓰고 싶을 때** 쓰라고 있는 것이 `NULL` 안전 등호다. 그런데 **문법이 방언마다 다르다.**

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
| 상대 문법을 던지면 | `<=>` → 연산자 없음 에러 | `IS NOT DISTINCT FROM` → 문법 오류 |

**양쪽에서 다 도는 표현은 없다.**\
이식이 필요하면 `(a = b) OR (a IS NULL AND b IS NULL)` 로 풀어 쓴다 — 길지만 두 엔진 다 돈다.

비교 연산자 쪽의 자세한 규칙은 목록의 05번이 정본이다.
