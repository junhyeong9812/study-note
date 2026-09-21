# sql/23-`GROUPING SETS`·`ROLLUP`·`CUBE` 와 `GROUPING()` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 GROUPING SETS, CUBE, ROLLUP](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 GROUP BY Modifiers](https://dev.mysql.com/doc/refman/8.4/en/group-by-modifiers.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. **4행**이다 — `GROUP BY dept_id`(3행)에 **총계 줄 하나**가 더 있다

**출력**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY ROLLUP(dept_id) ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  s                    +---------+------+
---------+------                 | dept_id | s    |
      10 |  800                  +---------+------+
      20 | NULL                  |    NULL |  400 |
    NULL | 1200                  |    NULL | 1200 |
    NULL |  400                  |      10 |  800 |
(4 rows)                         |      20 | NULL |
                                 +---------+------+
```

**왜 그런가**

```text
 GROUP BY ROLLUP(dept_id) = 두 질의를 한 번에 돌린 것

   GROUP BY dept_id     ──>  10 | 800
                             20 | NULL
                           NULL | 400
        +  (UNION ALL)
   GROUP BY ()          ──>  NULL | 1200      <- 그룹 키가 없는 그룹 = 표 전체
        =
   4행
```

PG 문서가 확장 규칙을 그대로 적는다 — `ROLLUP(e1, e2, e3)` 은 *"the given list of expressions and all prefixes of the list including the empty list"* 이다.

★ **행 순서에 주의하라.** `ORDER BY dept_id` 를 걸었는데도 두 엔진의 줄 순서가 다르다.\
`dept_id` 가 `NULL` 인 행이 **둘**이라 정렬 키만으로는 둘의 앞뒤가 정해지지 않기 때문이다.\
(`NULL` 이 앞이냐 뒤냐 자체도 엔진마다 다르다 — [목록의 **8번 주제**](../08-order-by-null-position-stability/).)

> **그룹 집합(grouping set)** — 한 질의 안에서 쓰이는 하나의 `GROUP BY` 목록.\
> 예: `ROLLUP(dept_id)` 는 `(dept_id)` 와 `()` 두 개다.

---

### 2. 하나는 **`dan` 의 그룹**, 하나는 **총계**다 — `GROUPING()` 으로만 갈린다

**출력**

```text
### SQL: SELECT dept_id, GROUPING(dept_id) AS g, SUM(salary) AS s, COUNT(*) AS c
         FROM emp GROUP BY ROLLUP(dept_id) ORDER BY GROUPING(dept_id), dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | g |  s   | c          +---------+------+------+---+
---------+---+------+---         | dept_id | g    | s    | c |
      10 | 0 |  800 | 2          +---------+------+------+---+
      20 | 0 | NULL | 1          |    NULL |    0 |  400 | 1 |
    NULL | 0 |  400 | 1          |      10 |    0 |  800 | 2 |
    NULL | 1 | 1200 | 4          |      20 |    0 | NULL | 1 |
(4 rows)                         |    NULL |    1 | 1200 | 4 |
                                 +---------+------+------+---+
```

**왜 그런가**

```text
 결과에 NULL 이 있다. 어디서 왔나?
 +---------------------------+     +---------------------------+
 | 데이터가 NULL 이다        |     | 이 행에서 그 열을 접었다   |
 | (dan 은 소속이 없다)      |     | (부서를 안 따진 총계 줄)   |
 | g = 0 · COUNT(*) = 1      |     | g = 1 · COUNT(*) = 4      |
 +---------------------------+     +---------------------------+
              |                                 |
              +------------- 화면에서는 둘 다 NULL -----+
```

★ **`COUNT(*)` 이 뒷받침한다** — `g`=1 행의 `COUNT(*)` 이 **4**(표 전체)다. `g`=0 행은 1(`dan` 하나)이다.\
하지만 **`COUNT(*)` 이 우연히 같을 수도 있다** — 6번에서 합계까지 똑같은 두 행을 본다. **그래서 `GROUPING()` 이 필요하다.**

MySQL 문서도 같은 목적으로 적는다: *"to test whether `NULL` values in the result represent super-aggregate values, the `GROUPING()` function is available …"*

> **소계 행(super-aggregate row)** — 어떤 열을 **접어서** 만든 행. 그 열 자리에 `NULL` 이 찍힌다.\
> 예: 총계 줄의 `dept_id`. 데이터의 `NULL` 이 아니라 「접었다」는 표시다.

---

### 3. `dan` 의 그룹까지 「전체」가 된다

**출력**

```text
### SQL: SELECT COALESCE(CAST(dept_id AS CHAR(10)), '(all)') AS dept, SUM(salary) AS s
         FROM emp GROUP BY ROLLUP(dept_id) ORDER BY GROUPING(dept_id), dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
    dept    |  s                 +-------+------+
------------+------              | dept  | s    |
 10         |  800               +-------+------+
 20         | NULL               | (all) |  400 |
 (all)      |  400               | 10    |  800 |
 (all)      | 1200               | 20    | NULL |
(4 rows)                         | (all) | 1200 |
                                 +-------+------+
```

**왜 그런가**

```text
 COALESCE 가 보는 것              GROUPING 이 보는 것
 +---------------------+          +---------------------+
 | 값이 NULL 인가       |          | 이 열을 접었는가     |
 +---------------------+          +---------------------+
   두 NULL 이 똑같이 보인다         두 NULL 이 갈린다
```

★ **`COALESCE`·`IFNULL`·`IS NULL` 은 전부 「값이 `NULL` 인가」만 본다.**\
소계 `NULL` 과 데이터 `NULL` 은 **값으로는 같은 것**이라 이 도구들로 가를 수 없다.\
**`GROUPING()` 은 값이 아니라 「이 행이 어느 그룹 집합에서 왔나」를 본다.** 그래서 갈 수 있다.

「(all)」이 둘이 되어 **같은 라벨에 400 과 1200 이 붙었다.** 표를 읽는 사람은 이것을 오류로 읽지 않는다 — **조용한 오답**이다.

---

### 4. `IS NULL` 을 먼저 봐서 **총계 줄까지 「(no dept)」가 됐다**

**출력**

```text
### SQL: SELECT CASE WHEN dept_id IS NULL THEN '(no dept)'
                     WHEN GROUPING(dept_id) = 1 THEN '(total)'
                     ELSE CAST(dept_id AS CHAR(10)) END AS dept, SUM(salary) AS s
         FROM emp GROUP BY ROLLUP(dept_id) ORDER BY GROUPING(dept_id), dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
    dept    |  s                 +-----------+------+
------------+------              | dept      | s    |
 10         |  800               +-----------+------+
 20         | NULL               | (no dept) |  400 |
 (no dept)  |  400               | 10        |  800 |
 (no dept)  | 1200               | 20        | NULL |
(4 rows)                         | (no dept) | 1200 |
                                 +-----------+------+
```

**왜 그런가**

```text
 총계 줄이 CASE 를 지나가는 길
   dept_id = NULL · GROUPING(dept_id) = 1
        |
   WHEN dept_id IS NULL  ->  TRUE      <- 여기서 잡혀 버린다
        |                               두 번째 WHEN 까지 못 간다
   결과: '(no dept)'
```

★ **`CASE` 는 위에서부터 첫 `TRUE` 에서 멈춘다.** 총계 줄도 `dept_id` 가 `NULL` 이므로 첫 줄에 걸린다.\
`(total)` 가지는 **영원히 도달하지 않는다.**

**고치는 법 — `GROUPING()` 을 먼저 본다.**

```text
### SQL: SELECT CASE WHEN GROUPING(dept_id) = 1 THEN '(total)'
                     WHEN dept_id IS NULL THEN '(no dept)'
                     ELSE CAST(dept_id AS CHAR(10)) END AS dept, SUM(salary) AS s, COUNT(*) AS c
         FROM emp GROUP BY ROLLUP(dept_id) ORDER BY GROUPING(dept_id), dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
    dept    |  s   | c           +-----------+------+---+
------------+------+---          | dept      | s    | c |
 10         |  800 | 2           +-----------+------+---+
 20         | NULL | 1           | (no dept) |  400 | 1 |
 (no dept)  |  400 | 1           | 10        |  800 | 2 |
 (total)    | 1200 | 4           | 20        | NULL | 1 |
(4 rows)                         | (total)   | 1200 | 4 |
                                 +-----------+------+---+
```

★ **규칙 한 줄: 소계 판별이 값 판별보다 먼저다.** `GROUPING()` → `IS NULL` → `ELSE` 순서로 고정한다.\
`CASE` 자체의 평가 규칙은 [목록의 **6번 주제**](../06-conditional-expressions-case-coalesce/)가 정본이다.

---

### 5. `ROLLUP`·`CUBE` 는 `GROUPING SETS` 의 **줄임말**이다

```text
ROLLUP(a, b, c)  =  GROUPING SETS ( (a,b,c), (a,b), (a), () )
                                    앞에서부터 하나씩 벗긴다 (계층)

CUBE(a, b)       =  GROUPING SETS ( (a,b), (a), (b), () )
                                    부분집합 전부 (독립 축)

GROUPING SETS    =  원형. 필요한 것만 직접 적는다
```

PG 문서가 그대로 적는다 — `CUBE(e1, e2, ...)` 는 *"the given list and all of its possible subsets (i.e., the power set)"* 이다.

**실측으로 확인했다** — `GROUPING SETS ((dept_id), ())` 가 `ROLLUP(dept_id)` 과 **한 글자도 같은 결과**를 낸다.

```text
### SQL: SELECT dept_id, SUM(salary) AS s, COUNT(*) AS c
         FROM emp GROUP BY GROUPING SETS ((dept_id), ()) ORDER BY GROUPING(dept_id), dept_id;
--- PG 18.6 ---
 dept_id |  s   | c
---------+------+---
      10 |  800 | 2
      20 | NULL | 1
    NULL |  400 | 1
    NULL | 1200 | 4
(4 rows)
```

```text
 언제 무엇을 고르나
 계층이 있다 (연 > 월 > 일)        -> ROLLUP
 축이 독립이다 (지역 x 제품)        -> CUBE
 필요한 줄이 몇 개뿐이다            -> GROUPING SETS
```

★ **`CUBE(a,b,c)` 는 그룹 집합이 8개**(2의 3승)가 된다. 열이 늘면 급격히 커지므로 **필요한 것만 적는 쪽**이 대개 낫다.

---

### 6. ★ `NULL | dan | 400` 인 행이 **둘** 나온다

**출력**

```text
### SQL: SELECT dept_id, name, GROUPING(dept_id) AS gd, GROUPING(name) AS gn, SUM(salary) AS s
         FROM emp GROUP BY CUBE(dept_id, name) ORDER BY gd, gn, dept_id, name;
--- PG 18.6 ---
 dept_id | name | gd | gn |  s
---------+------+----+----+------
      10 | ann  |  0 |  0 |  300
      10 | bob  |  0 |  0 |  500
      20 | cho  |  0 |  0 | NULL
    NULL | dan  |  0 |  0 |  400     <- (가)
      10 | NULL |  0 |  1 |  800
      20 | NULL |  0 |  1 | NULL
    NULL | NULL |  0 |  1 |  400
    NULL | ann  |  1 |  0 |  300
    NULL | bob  |  1 |  0 |  500
    NULL | cho  |  1 |  0 | NULL
    NULL | dan  |  1 |  0 |  400     <- (나)
    NULL | NULL |  1 |  1 | 1200
(12 rows)
```

**왜 그런가**

```text
 (가)  dept_id=NULL  name=dan  s=400     그룹 집합 (dept_id, name)
        -> "소속이 없는 dan" 이라는 실제 그룹.  dept_id 는 데이터가 NULL

 (나)  dept_id=NULL  name=dan  s=400     그룹 집합 (name)
        -> "이름이 dan 인 사람 전체" 소계.  dept_id 는 접혀서 NULL

 보이는 세 칸(dept_id · name · s)이 한 글자도 같다.  gd 만 0 과 1 로 다르다
```

★★ **합계까지 같다.** `dan` 이 한 명뿐이라 「소속 없는 dan」과 「dan 전체」가 같은 400 이다.\
**눈으로도, 값 비교로도, `COUNT(*)` 으로도 못 가른다.** `GROUPING()` 이 유일한 수단이다.

```text
 이것이 GROUPING() 이 언어에 있는 이유다
 +-------------------------------------------------+
 | 결과 집합 안에 "구분 불가능한 두 행" 이 생길 수   |
 | 있고, 그 구분은 값이 아니라 "어느 그룹 집합에서   |
 | 왔나" 에만 담겨 있다                             |
 +-------------------------------------------------+
```

**MySQL 에서는 이 질의 자체가 안 돈다** — `CUBE` 가 `ERROR 3889` 다(10·11번).

---

### 7. **둘**이다 — 「소속 없음」 부서의 소계와, 총계

**출력**

```text
### SQL: SELECT dept_id, name, GROUPING(dept_id) AS gd, GROUPING(name) AS gn, SUM(salary) AS s
         FROM emp GROUP BY ROLLUP(dept_id, name)
         ORDER BY GROUPING(dept_id), dept_id, GROUPING(name), name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | name | gd | gn |  s   +---------+------+------+------+------+
---------+------+----+----+----- | dept_id | name | gd   | gn   | s    |
      10 | ann  |  0 |  0 |  300 +---------+------+------+------+------+
      10 | bob  |  0 |  0 |  500 |    NULL | dan  |    0 |    0 |  400 |
      10 | NULL |  0 |  1 |  800 |    NULL | NULL |    0 |    1 |  400 |
      20 | cho  |  0 |  0 | NULL |      10 | ann  |    0 |    0 |  300 |
      20 | NULL |  0 |  1 | NULL |      10 | bob  |    0 |    0 |  500 |
    NULL | dan  |  0 |  0 |  400 |      10 | NULL |    0 |    1 |  800 |
    NULL | NULL |  0 |  1 |  400 |      20 | cho  |    0 |    0 | NULL |
    NULL | NULL |  1 |  1 | 1200 |      20 | NULL |    0 |    1 | NULL |
(8 rows)                         |    NULL | NULL |    1 |    1 | 1200 |
                                 +---------+------+------+------+------+
```

**왜 그런가**

| 행 | `gd` | `gn` | 뜻 |
|---|---|---|---|
| `NULL / dan` | 0 | 0 | **소속 없는 `dan` 본인**의 줄 |
| `NULL / NULL` | **0** | 1 | **「소속 없음」 부서의 소계** — `dept_id` 는 진짜 `NULL` 이고 `name` 만 접혔다 |
| `NULL / NULL` | **1** | 1 | **총계** — 둘 다 접혔다 |

```text
 ROLLUP(dept_id, name) 의 세 층

   (dept_id, name)  ──> 사람별 줄             gd=0 gn=0
   (dept_id)        ──> 부서 소계 줄          gd=0 gn=1   <- "소속 없음" 도 한 부서다
   ()               ──> 총계 줄               gd=1 gn=1
```

★ **가운데 행이 이 문제의 핵심이다.**\
「소속 없음」은 `GROUP BY` 가 만드는 **정상적인 한 그룹**이고([22번](../22-group-by-nonaggregated-columns/)), `ROLLUP` 은 **그 그룹에도 소계 줄을 만든다.**\
그래서 `NULL / NULL` 이 두 번 나오고, 둘의 `s` 는 400 과 1200 으로 다르다.

★ **두 엔진의 값이 한 자리도 안 갈렸다.** 갈린 것은 줄 순서뿐이다(`ORDER BY` 키가 `NULL` 로 겹치는 자리).

---

### 8. **비트마스크**다 — `ROLLUP(dept_id, name)` 에서 **0 · 1 · 3** 이 나온다

**출력**

```text
### SQL: SELECT dept_id, name, GROUPING(dept_id, name) AS bits, SUM(salary) AS s
         FROM emp GROUP BY ROLLUP(dept_id, name) ORDER BY GROUPING(dept_id, name), dept_id, name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | name | bits |  s      +---------+------+------+------+
---------+------+------+-----    | dept_id | name | bits | s    |
      10 | ann  |    0 |  300    +---------+------+------+------+
      10 | bob  |    0 |  500    |    NULL | dan  |    0 |  400 |
      20 | cho  |    0 | NULL    |      10 | ann  |    0 |  300 |
    NULL | dan  |    0 |  400    |      10 | bob  |    0 |  500 |
      10 | NULL |    1 |  800    |      20 | cho  |    0 | NULL |
      20 | NULL |    1 | NULL    |    NULL | NULL |    1 |  400 |
    NULL | NULL |    1 |  400    |      10 | NULL |    1 |  800 |
    NULL | NULL |    3 | 1200    |      20 | NULL |    1 | NULL |
(8 rows)                         |    NULL | NULL |    3 | 1200 |
                                 +---------+------+------+------+
```

**왜 그런가**

```text
 GROUPING(dept_id, name) 의 비트 배치

   bit 1   bit 0
  dept_id   name      값    뜻
     0        0    ->  0    둘 다 실제 값 (가장 안쪽 줄)
     0        1    ->  1    name 만 접었다 (부서 소계)
     1        1    ->  3    둘 다 접었다  (총계)
```

★ **왼쪽 인자가 높은 비트다.** `ROLLUP` 은 앞에서부터 벗기므로 **2(=`10`)는 나오지 않는다** — `dept_id` 만 접고 `name` 은 안 접는 그룹 집합이 없기 때문이다.\
`CUBE(dept_id, name)` 이었다면 **2도 나온다**(6번의 `gd`=1 `gn`=0 행들이 그것이다).

**두 엔진에서 0·1·3 이 한 자리도 같았다.**

대가 — 비트를 읽어야 한다. **열이 둘이면 `GROUPING(a)`·`GROUPING(b)` 를 따로 뽑는 쪽이 읽기 쉽다**(7번의 형태).\
비트마스크는 열이 셋 이상이라 열을 늘리기 싫을 때 쓴다.

> **비트마스크(bitmask)** — 여러 참/거짓을 한 정수의 비트로 담은 것.\
> 예: 3은 2진수 `11` 이라 두 열 모두 접혔다는 뜻이다.

---

### 9. `SELECT`·`HAVING`·`ORDER BY` 는 되고, **`WHERE` 는 안 된다**

**출력 — `WHERE`**

```text
### SQL: SELECT dept_id FROM emp WHERE GROUPING(dept_id) = 1 GROUP BY ROLLUP(dept_id);
--- PG 18.6 ---
ERROR:  grouping operations are not allowed in WHERE
LINE 1: SELECT dept_id FROM emp WHERE GROUPING(dept_id) = 1 GROUP BY...
                                      ^
--- MySQL 8.4.10 ---
ERROR 1111 (HY000) at line 1: Invalid use of group function
```

**출력 — `HAVING`**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY ROLLUP(dept_id) HAVING GROUPING(dept_id) = 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  s                    +---------+------+
---------+------                 | dept_id | s    |
    NULL | 1200                  +---------+------+
(1 row)                          |    NULL | 1200 |
                                 +---------+------+
```

**`ORDER BY` 에서 쓰는 것**은 1·2·7·8번의 모든 질의가 실증한다 — `ORDER BY GROUPING(dept_id), dept_id`.

**왜 그런가**

```text
FROM ──> WHERE ──> GROUP BY ──> HAVING ──> SELECT ──> ORDER BY
  1        2          3            4          5          6
           ^                       ^          ^          ^
    아직 그룹이 없다          여기부터 GROUPING() 이 답을 가진다
```

★ **`GROUPING()` 은 「이 행이 어느 그룹 집합에서 왔나」를 묻는 함수다.**\
`WHERE`(2번 칸)에서는 그룹이 아직 만들어지지 않았으니 **물을 것 자체가 없다**([01번](../01-logical-query-processing-order/)).

MySQL 문서도 *"available for use in the select list, `HAVING` clause, and `ORDER BY` clause"* 로 **세 자리만** 든다.\
메시지는 다르다 — PG 는 `grouping operations are not allowed in WHERE`, MySQL 은 집계 오용에 쓰는 한 덩어리 `ERROR 1111` 이다. **거부는 같다.**

---

### 10. ★ (A) MySQL 만 · (B) **양쪽** · (C) MySQL 문법 오류 · (D) MySQL 보조 엔진 요구

**출력 — (A) `WITH ROLLUP`**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY dept_id WITH ROLLUP;
--- PG 18.6 ---
ERROR:  syntax error at or near "WITH"
LINE 1: ...pt_id, SUM(salary) AS s FROM emp GROUP BY dept_id WITH ROLLU...
                                                             ^
--- MySQL 8.4.10 ---
+---------+------+
| dept_id | s    |
+---------+------+
|    NULL |  400 |
|      10 |  800 |
|      20 | NULL |
|    NULL | 1200 |
+---------+------+
```

**(B) `ROLLUP(...)`** — 1번의 출력이 그대로 답이다. **양쪽에서 돈다.**\
MySQL 문서도 *"MySQL supports an additional, alternative syntax for this modifier"* 로 두 형태를 다 적는다.

**출력 — (C) `GROUPING SETS`**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY GROUPING SETS ((dept_id), ()) ORDER BY dept_id;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'SETS ((dept_id), ()) ORDER BY dept_id' at line 1
```

**출력 — (D) `CUBE`**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY CUBE(dept_id) ORDER BY dept_id;
--- MySQL 8.4.10 ---
ERROR 3889 (HY000) at line 1: Secondary engine operation failed. Reason: "No secondary engine defined for at least one of the query tables".
```

**왜 그런가**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| (A) `GROUP BY a WITH ROLLUP` | ✗ `syntax error at or near "WITH"` | **✓** |
| (B) `GROUP BY ROLLUP(a)` | **✓** | **✓** |
| (C) `GROUP BY GROUPING SETS (…)` | **✓** | ✗ `ERROR 1064` |
| (D) `GROUP BY CUBE(a)` | **✓** | ✗ `ERROR 3889` |

★ **(B)만이 두 엔진에서 같이 도는 형태다.** 이식할 거면 이것을 쓴다.\
`CUBE(dept_id, name)` 처럼 **열을 둘로 늘려도 MySQL 은 같은 `ERROR 3889`** 였다.

---

### 11. ★ `1064` 는 **「모르는 말」**, `3889` 는 **「알지만 돌릴 곳이 없다」**

```text
 (C) GROUPING SETS                  (D) CUBE
 ERROR 1064 (42000)                 ERROR 3889 (HY000)
 +------------------------------+   +------------------------------+
 | 파서가 SETS 에서 걸렸다       |   | 파서는 CUBE 를 알아들었다     |
 | "syntax to use near 'SETS…'" |   | 실행 단계에서 거부했다        |
 | 그 문법이 언어에 없다         |   | 보조 엔진이 붙어 있어야 한다  |
 +------------------------------+   +------------------------------+
      -> 어떤 설정으로도 못 켠다        -> 기본 InnoDB 구성에서는 못 쓴다
```

**왜 이 구분이 중요한가**

★ **목록 README 는 이것을 「매뉴얼에 `CUBE` 미지원이라고 명시된 문장은 찾지 못했다 — 문서 부재로 판단한 것」이라고 적어 두었다.**\
**던져 보니 「문서 부재」가 아니었다.** 파서가 알아듣고 실행 경로가 없다고 답했다. 근거의 강도가 다르다.

```text
 "문서에 없어서 없다고 봤다"        "던져 봤더니 이렇게 답했다"
 +---------------------------+      +---------------------------+
 | 추정이다                   |      | 관찰이다                  |
 | 다음 버전에 조용히 생겨도  |      | 에러 번호가 이유까지       |
 |   알 수 없다               |      |   말해 준다               |
 +---------------------------+      +---------------------------+
```

**이 근거로 README 의 23번 방언 칸을 고쳤다.** 결론(「기본 구성에서 못 쓴다」)은 같지만 **이유가 다르다.**

★ **이것이 「에러도 출력이다」의 실례다.** 「미지원」을 단정하기 전에 던져 보면 **다른 답**이 나온다.

---

### 12. PG 는 **전부 0**을 내고, MySQL 은 **`ERROR 1111`** 이다

**출력**

```text
### SQL: SELECT dept_id, GROUPING(dept_id) AS g FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | g                     ERROR 1111 (HY000) at line 1: Invalid use of group function
---------+---
      10 | 0
      20 | 0
    NULL | 0
(3 rows)
```

**왜 그런가**

```text
 PG 의 해석                          MySQL 의 해석
 +----------------------------+      +----------------------------+
 | GROUPING() 은 "접었는가" 를 |      | GROUPING() 은 ROLLUP 질의의 |
 | 묻는 일반 함수다            |      | 함수다                     |
 | 접은 열이 없으면 전부 0     |      | ROLLUP 이 없으면 쓸 자리가  |
 |                            |      |   아니다 -> 거부            |
 +----------------------------+      +----------------------------+
```

MySQL 문서가 `GROUPING()` 을 *"For `GROUP BY ... WITH ROLLUP` queries"* 라는 조건 아래 설명한다 — **`ROLLUP` 이 있을 때 쓰는 함수**로 정의한 것이다.

★ **PG 의 0 은 「접은 적이 없다」는 정확한 답이다.** 의미가 없는 게 아니라 **항상 같은 답이 나오는 질문**을 한 것이다.\
그래서 실무에서는 **`GROUPING()` 의 인자를 `GROUP BY` 에 실제로 나온 식으로 맞춘다** — 아니면 그 열은 접힌 적이 없으니 언제나 0이다.

**이식 규칙 한 줄: `GROUPING()` 은 `ROLLUP`·`CUBE`·`GROUPING SETS` 와 함께만 쓴다.**

---

### 13. `GROUP BY ROLLUP(...)` 를 쓰고, `GROUPING SETS` 는 `UNION ALL` 로 편다

```text
 이식 가능한 것                       이식 안 되는 것
 +-------------------------+          +-------------------------+
 | GROUP BY ROLLUP(a, b)   |          | GROUP BY a WITH ROLLUP  | <- PG 문법 오류
 | GROUPING(a)             |          | GROUPING SETS (...)     | <- MySQL 1064
 | GROUPING(a, b)          |          | CUBE(...)               | <- MySQL 3889
 | HAVING GROUPING(a) = 1  |          | ROLLUP 없는 GROUPING()  | <- MySQL 1111
 +-------------------------+          +-------------------------+
```

**MySQL 에서 `GROUPING SETS` 가 필요하면 그룹 집합마다 질의를 하나씩 써서 잇는다.**

```sql
-- GROUPING SETS ((dept_id), ()) 를 손으로 편 것
SELECT dept_id,      SUM(salary) AS s FROM emp GROUP BY dept_id
UNION ALL
SELECT NULL AS dept_id, SUM(salary) AS s FROM emp;
```

```text
 ROLLUP 을 쓸 때                     UNION ALL 로 펼 때
 +---------------------------+       +---------------------------+
 | 스캔 1 회                  |       | 그룹 집합 수만큼 스캔     |
 | 소계 판별은 GROUPING()     |       | 소계 판별을 직접 적는다   |
 |                           |       |   (상수 열을 하나 더 둔다) |
 +---------------------------+       +---------------------------+
   -> ROLLUP 의 값이 정확히 여기 있다
```

★ **`UNION ALL` 로 펼 때는 소계 표시 열을 스스로 만들어야 한다** — `GROUPING()` 이 없으니\
`SELECT ..., 0 AS is_total` / `SELECT ..., 1 AS is_total` 처럼 상수로 박는다.\
그러지 않으면 3번의 함정(두 `NULL` 이 섞인다)을 그대로 만난다.

**대안 — 아예 열을 늘린다.** 소계를 행으로 쌓는 대신 **조건별 집계를 열로 나란히 놓는** 방법이 있고, 그것이 [24번](../24-conditional-aggregation-filter-case/)이다.\
행이 안 늘어 읽기 쉽고 `NULL` 함정도 없다. **대신 조건이 미리 고정돼 있어야 한다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `ROLLUP(dept_id)` (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `ORDER BY dept_id` 로도 줄 순서가 갈렸다 |
| `GROUPING()` 으로 가르기 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `COUNT(*)` 까지 같이 |
| `COALESCE` 라벨링 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **「(all)」이 둘** — 조용한 오답 |
| 틀린 `CASE` · 맞는 `CASE` (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 순서만 바꿔 양쪽 다 |
| `GROUPING SETS` = `ROLLUP` (5번) | PG 18.6 | 1회 | 1번 출력과 문자 단위 대조 |
| ★ `CUBE` 의 구분 불가 두 행 (6번) | PG 18.6 | 2회 | `GROUPING` 열 유무로 두 번 |
| 2단 `ROLLUP` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **값은 한 자리도 안 갈렸다** |
| `GROUPING()` 비트마스크 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 0·1·3 이 양쪽 같음 |
| `WHERE`/`HAVING` 가부 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`WHERE` 는 양쪽 에러** |
| ★ MySQL 지원 범위 (10·11번) | PG 18.6 · MySQL 8.4.10 | 각 5회 | `WITH ROLLUP`·`ROLLUP()`·`GROUPING SETS`·`CUBE(a)`·`CUBE(a,b)` |
| `ROLLUP` 없는 `GROUPING()` (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 0 / MySQL 1111** |

**구현 의존 항목** — **행 순서.** `NULL` 이 둘인 자리에서는 `ORDER BY dept_id` 만으로 순서가 안 정해진다.\
그래서 이 주제의 대부분 질의에 **`ORDER BY GROUPING(...)` 을 먼저** 걸었다.

**방언 항목** — 10·11·12번. `WITH ROLLUP`(MySQL 만) · `GROUPING SETS`·`CUBE`(PG 만) · `ROLLUP` 없는 `GROUPING()`.\
**언어 보장 항목** — 1~9·13번. 확장 규칙, 접힌 열의 `NULL`, `GROUPING()` 의 0/1 과 비트 배치는 두 문서가 같은 모양으로 적는다.

**버전** — 두 매뉴얼에서 **도입 버전을 확인하지 못해 적지 않았다.**\
다음 버전에서 다시 볼 것 — **10번(MySQL 의 `CUBE` 가 `3889` 인 채인지)**과 **12번**이다.

**README 정정** — 23번 방언 칸의 「문서 부재로 판단」을 **`ERROR 3889` 실측**으로 바꿨다(11번).
