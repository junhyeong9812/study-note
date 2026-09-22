# sql/23-`GROUPING SETS`·`ROLLUP`·`CUBE` 와 `GROUPING()` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · GROUPING SETS, CUBE, and ROLLUP](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · GROUP BY Modifiers](https://dev.mysql.com/doc/refman/8.4/en/group-by-modifiers.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — PG 는 셋 다 있다. MySQL 8.4.10 은 **`ROLLUP` 만** 있고 `GROUPING SETS` 는 문법 오류, `CUBE` 는 **다른 이유로 거부**된다(5번). 도입 버전은 두 매뉴얼에서 확인하지 못해 적지 않는다.\
> **선행** — [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/). **거기서 배운 「`NULL` 도 한 그룹」이 여기서 함정이 된다.**\
> **뒤 주제** — [24 조건부 집계](../24-conditional-aggregation-filter-case/) · [25 조인 팬아웃](../25-join-fan-out/).

## 한눈에 — 쉽게 말하면

**영수증 한 장에 「품목별 금액」과 「소계」와 「총계」가 같이 찍혀 나오는 것.**

- `GROUP BY dept_id` 는 **부서별 한 줄씩**만 준다. 총계는 질의를 또 던져야 한다.
- `GROUP BY ROLLUP(dept_id)` 는 **부서별 줄 + 총계 줄을 한 번에** 준다.
- 그리고 ★ **총계 줄의 부서 칸은 `NULL` 로 찍힌다.** 「부서가 없다」가 아니라 「부서를 안 따졌다」는 뜻인데, **화면에서는 똑같이 `NULL` 이다.**

| 비유 | 실체 | 하는 일 |
|---|---|---|
| 소계 줄을 위에서부터 벗겨 가며 찍기 | `ROLLUP(a, b)` | `(a,b)` → `(a)` → `()` — **앞에서부터 벗긴다** |
| 가능한 모든 조합을 다 찍기 | `CUBE(a, b)` | `(a,b)` `(a)` `(b)` `()` — **부분집합 전부** |
| 내가 고른 줄만 찍기 | `GROUPING SETS (…)` | 적은 것만. 위 둘은 이것의 줄임말이다 |
| 「이 칸은 안 따진 칸」 도장 | `GROUPING(열)` | 그 행에서 그 열을 **접었으면 1**, 실제 값이면 **0** |

```text
GROUP BY dept_id            GROUP BY ROLLUP(dept_id)
+---------+------+          +---------+------+
| dept_id |  s   |          | dept_id |  s   |
+---------+------+          +---------+------+
|      10 |  800 |          |      10 |  800 |
|      20 | NULL |   ──>    |      20 | NULL |
|    NULL |  400 |          |    NULL |  400 |  <- dan 의 그룹 (데이터가 NULL)
+---------+------+          |    NULL | 1200 |  <- 총계    (접어서 NULL)
     3행                    +---------+------+
                                 4행 — NULL 이 둘, 뜻이 다르다
```

**이 영수증이 똑같은 구조로** 소계·총계 질의다.\
★ 그리고 **`NULL` 이 두 뜻을 갖게 되는 것**이 이 주제의 전부다. 그것을 가르는 도장이 `GROUPING()` 이다.

> **그룹 집합(grouping set)** — 한 질의 안에서 쓰이는 **하나의 `GROUP BY` 목록**.\
> 예: `ROLLUP(dept_id)` 는 그룹 집합이 둘이다 — `(dept_id)` 와 `()`.

> **소계 행(super-aggregate row)** — 어떤 열을 **안 따지고** 접어서 만든 행. 그 열 자리에 `NULL` 이 찍힌다.\
> 예: 총계 줄의 `dept_id`. 데이터의 `NULL` 이 아니라 **「접었다」는 표시**다.

## 이 주제가 답하려는 질문

1. **세 문법이 각각 무엇을 한 번에 내나?** — 그리고 셋이 사실 하나의 줄임말이라는 것.
2. **★ 결과의 `NULL` 이 「값 없음」인지 「소계 행」인지 어떻게 아나?** — 값만 봐서는 못 안다.
3. **MySQL 에서 어디까지 되나?** — 「미지원」이라 적기 전에 던져 봐야 한다.

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

★ **`dan` 의 `dept_id` 가 `NULL` 인 것이 이 주제에서 결정적이다.**\
소계 행도 `dept_id` 를 `NULL` 로 찍으므로, **`dan` 의 그룹과 총계 줄이 화면에서 똑같이 보인다.**\
이 표가 없었으면 「소계 `NULL` 과 데이터 `NULL` 이 섞인다」를 말로만 설명하게 된다.

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

### 1. `ROLLUP` 은 여러 `GROUP BY` 를 한 번에 돌린 것과 같다

**언제 쓰나** — 「부서별 + 전체」처럼 **집계 수준이 여럿**인 표를 한 화면에 내야 할 때.

```text
 GROUP BY ROLLUP(dept_id) 가 하는 일

   GROUP BY dept_id     ──>  10 | 800
                             20 | NULL
                           NULL | 400
        +  (UNION ALL)
   GROUP BY ()          ──>  NULL | 1200      <- 그룹 키가 없는 그룹 = 표 전체
        =
   한 결과 4행
```

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

그림 해설 — **`dept_id` 가 `NULL` 인 행이 둘이다.** 하나는 `dan` 의 그룹(400), 하나는 총계(1200).\
`ORDER BY dept_id` 로는 **두 행의 순서조차 엔진마다 다르다** — 정렬 키가 둘 다 `NULL` 이라 구분이 안 되기 때문이다.

PG 문서가 확장 규칙을 그대로 적는다 — `ROLLUP(e1, e2, e3)` 은 *"the given list of expressions and all prefixes of the list including the empty list"* 이다.

```text
ROLLUP(a, b, c)  =  GROUPING SETS ( (a,b,c), (a,b), (a), () )
                                       ^^^^^^^^^^^^^^^^^^^^
                          앞에서부터 하나씩 벗긴다 — 계층이 있을 때 쓴다
```

비용 — 그룹 집합 하나당 집계를 한 번씩 하는 셈이지만 **스캔은 한 번**이다. 질의를 두 번 던지는 것보다 싸다.\
정확한 계획은 [목록의 **58번 주제**](../58-explain-plan-tree/)에서 읽는다. **여기서는 재지 않았다.**

---

### 2. ★ 소계 행의 `NULL` 과 데이터의 `NULL` 을 가르는 법 — `GROUPING()`

**언제 쓰나** — `ROLLUP`·`CUBE`·`GROUPING SETS` 를 쓸 때마다. **예외 없이.**

```text
 결과에 NULL 이 있다. 어디서 왔나?
 +---------------------------+     +---------------------------+
 | 데이터가 NULL 이다        |     | 이 행에서 그 열을 접었다   |
 | (dan 은 소속이 없다)      |     | (부서를 안 따진 총계 줄)   |
 +---------------------------+     +---------------------------+
              |                                 |
              +------------- 화면에서는 둘 다 NULL -----+
                                    |
                            GROUPING(dept_id) 로만 갈린다
                               0 이면 데이터 · 1 이면 접은 것
```

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

그림 해설 — ★ **`g`=0 인 `NULL` 은 `dan` 의 그룹이고, `g`=1 인 `NULL` 은 총계다.**\
`c` 열이 그것을 뒷받침한다 — `g`=1 행의 `COUNT(*)` 이 **4**(표 전체)다.

**MySQL 도 `GROUPING()` 을 그대로 지원한다.** 문서가 적는다: *"to test whether `NULL` values in the result represent super-aggregate values, the `GROUPING()` function is available for use in the select list, `HAVING` clause, and `ORDER BY` clause."*

**사람이 읽을 표로 만들려면 `CASE` 와 함께 쓴다.**

```text
### SQL: SELECT CASE WHEN GROUPING(dept_id) = 1 THEN '(total)'
                     WHEN dept_id IS NULL THEN '(no dept)'
                     ELSE CAST(dept_id AS CHAR(10)) END AS dept,
                SUM(salary) AS s, COUNT(*) AS c
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

★ **`CASE` 의 순서가 중요하다 — `GROUPING()` 을 먼저 본다.**\
`dept_id IS NULL` 을 먼저 쓰면 **총계 줄도 「(no dept)」가 된다.** 총계 줄의 `dept_id` 도 `NULL` 이기 때문이다.

대가 — 열이 하나 늘고 `CASE` 가 붙는다. 그 대신 **표를 읽는 사람이 틀리지 않는다.**\
`CASE` 자체는 [목록의 **6번 주제**](../06-conditional-expressions-case-coalesce/)가 정본이다.

---

### 3. 열이 둘이 되면 소계 층이 생긴다 — `GROUPING()` 은 비트마스크다

**언제 쓰나** — 「부서별 → 부서 안 사람별 → 전체」처럼 **계층이 둘 이상**일 때.

```text
ROLLUP(dept_id, name) 이 만드는 그룹 집합 셋

 (dept_id, name)  ──> 사람별 줄
 (dept_id)        ──> 부서 소계 줄     name 칸이 NULL
 ()               ──> 총계 줄          둘 다 NULL
```

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

그림 해설 — ★ **`NULL | NULL` 인 행이 둘이고, `gd` 로만 갈린다.**

| 행 | `gd` | `gn` | 뜻 |
|---|---|---|---|
| `NULL / dan` | 0 | 0 | **소속 없는 `dan` 본인**의 줄 |
| `NULL / NULL` | **0** | 1 | **「소속 없음」 부서의 소계** — 실제 그룹이다 |
| `NULL / NULL` | **1** | 1 | **총계** |

**가운데 행이 이 주제의 핵심이다.** `dept_id` 는 진짜 `NULL`(소속 없음)이고 `name` 만 접힌 것이다.\
`gd`·`gn` 을 안 뽑으면 **이 세 행을 구분할 방법이 없다.**

**`GROUPING()` 에 인자를 여럿 주면 비트마스크가 된다.**

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
(8 rows)                         |      20 | NULL |    1 | NULL |
                                 |    NULL | NULL |    3 | 1200 |
                                 +---------+------+------+------+
```

```text
 GROUPING(dept_id, name) 의 비트 배치

   bit 1   bit 0
  dept_id   name      값    뜻
     0        0    ->  0    둘 다 실제 값 (가장 안쪽 줄)
     0        1    ->  1    name 만 접었다 (부서 소계)
     1        1    ->  3    둘 다 접었다  (총계)
```

★ **왼쪽 인자가 높은 비트다.** 두 엔진에서 **0·1·3 이 한 자리도 같았다.**\
대가 — 비트를 읽어야 한다. 열이 둘이면 `GROUPING(a)`·`GROUPING(b)` 를 따로 뽑는 쪽이 읽기 쉽다.

---

### 4. `CUBE` 와 `GROUPING SETS` — 모든 조합, 그리고 고른 것만

**언제 쓰나** — `CUBE` 는 **축이 서로 독립**일 때(지역 × 제품), `GROUPING SETS` 는 **필요한 줄만** 뽑을 때.

```text
ROLLUP(a, b)                 CUBE(a, b)
 (a,b)                        (a,b)
 (a)                          (a)
 ()                           (b)     <- ROLLUP 에는 없는 줄
                              ()
   계층 (앞에서부터 벗김)        모든 부분집합
```

PG 문서: `CUBE(e1, e2, ...)` 는 *"the given list and all of its possible subsets (i.e., the power set)"* 이다.

```text
### SQL: SELECT dept_id, name, GROUPING(dept_id) AS gd, GROUPING(name) AS gn, SUM(salary) AS s
         FROM emp GROUP BY CUBE(dept_id, name) ORDER BY gd, gn, dept_id, name;
--- PG 18.6 ---
 dept_id | name | gd | gn |  s
---------+------+----+----+------
      10 | ann  |  0 |  0 |  300
      10 | bob  |  0 |  0 |  500
      20 | cho  |  0 |  0 | NULL
    NULL | dan  |  0 |  0 |  400
      10 | NULL |  0 |  1 |  800
      20 | NULL |  0 |  1 | NULL
    NULL | NULL |  0 |  1 |  400
    NULL | ann  |  1 |  0 |  300
    NULL | bob  |  1 |  0 |  500
    NULL | cho  |  1 |  0 | NULL
    NULL | dan  |  1 |  0 |  400
    NULL | NULL |  1 |  1 | 1200
(12 rows)
```

그림 해설 — ★ **4번째 행과 11번째 행을 보라.**

```text
 dept_id | name | gd | gn |  s
 --------+------+----+----+-----
    NULL | dan  |  0 |  0 | 400     <- dan 의 실제 그룹 (소속 없음)
    NULL | dan  |  1 |  0 | 400     <- "이름이 dan 인 사람 전체" 소계
              ^^^^^^^^^^^^^^^^
   보이는 값이 한 글자도 같다.  gd 만 다르다
```

★★ **`GROUPING()` 없이는 이 두 행을 구분할 수 없다.** 이것이 `GROUPING()` 이 있는 이유 전부다.\
합계까지 같아서 **눈으로도, 값 비교로도 못 가른다.**

**`GROUPING SETS` 는 필요한 줄만 고른다.** `ROLLUP(dept_id)` 과 같은 결과를 손으로 적으면 이렇다.

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

**2번의 `ROLLUP(dept_id)` 결과와 한 글자도 같다.** `ROLLUP`·`CUBE` 는 `GROUPING SETS` 의 **줄임말**이다.

대가 — `CUBE(a,b,c)` 는 그룹 집합이 **8개**가 된다(2의 3승). 열이 늘면 급격히 커진다.\
사전 집계를 **저장해 두는 운영 전략**은 [`systems/timeseries-resolution-tiers`](../../../../../systems/timeseries-resolution-tiers/)가 정본이다 — **경계: 거기는 무엇을 미리 말아 둘지, 여기는 한 질의로 뽑는 문법.**

---

### 5. ★ MySQL 지원 범위 — 「미지원」이라 적기 전에 던져 봤다

**언제 쓰나** — 이식성을 판단할 때. 그리고 **문서에 없는 것을 「없다」로 단정하기 전에.**

**(가) `WITH ROLLUP` — MySQL 전용 문법이다.**

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

**(나) `ROLLUP(...)` 함수형 — 양쪽에서 돈다.** 2번의 출력이 그 증거다.\
MySQL 문서도 *"MySQL supports an additional, alternative syntax for this modifier"* 로 두 형태를 다 적는다.\
★ **이식할 거면 `GROUP BY ROLLUP(dept_id)` 를 쓴다.** `WITH ROLLUP` 은 PG 에서 문법 오류다.

**(다) `GROUPING SETS` — MySQL 은 파싱조차 못 한다.**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY GROUPING SETS ((dept_id), ()) ORDER BY dept_id;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'SETS ((dept_id), ()) ORDER BY dept_id' at line 1
```

`GROUPING` 까지는 아는 이름이라 통과하고 **`SETS` 에서 걸렸다.** 순수한 문법 오류다.

**(라) ★ `CUBE` — 에러가 `1064` 가 아니다.**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY CUBE(dept_id) ORDER BY dept_id;
--- MySQL 8.4.10 ---
ERROR 3889 (HY000) at line 1: Secondary engine operation failed. Reason: "No secondary engine defined for at least one of the query tables".
```

★★ **이것이 이 주제에서 가장 강한 근거다.**\
`CUBE` 는 **문법 오류가 아니다** — 파서가 알아들었다. 거부한 것은 「**이 질의를 돌릴 보조 엔진(secondary engine)이 붙어 있지 않다**」는 이유다.

```text
 GROUPING SETS                      CUBE
 ERROR 1064 (문법 오류)              ERROR 3889 (보조 엔진 없음)
 +------------------------+          +------------------------+
 | 파서가 모르는 말이다    |          | 파서는 안다            |
 | "없는 기능" 이다        |          | 실행할 엔진이 없을 뿐  |
 +------------------------+          +------------------------+
     -> 서버 설정으로 켤 수 없다         -> 기본 InnoDB 에서는 못 쓴다
```

★ **목록 README 는 이것을 「매뉴얼에 CUBE 미지원이라 명시된 문장은 찾지 못했다 — 문서 부재로 판단」이라고 적어 두었다.**\
**에러를 던져 보니 「문서 부재」가 아니라 「파싱은 되고 실행 경로가 없다」였다.** 이 근거로 README 의 해당 칸을 고쳤다.\
같은 열 조합으로 `CUBE(dept_id, name)` 을 던져도 **같은 `ERROR 3889`** 였다.

**(마) `GROUPING()` 을 `ROLLUP` 없이 쓰면 — 여기서도 갈린다.**

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

그림 해설 — **PG 는 「접은 열이 없으니 전부 0」이라고 답하고, MySQL 은 거부한다.**\
MySQL 문서가 `GROUPING()` 을 *"For `GROUP BY ... WITH ROLLUP` queries"* 라는 조건 아래 설명한다 — **`ROLLUP` 이 있을 때만 쓰는 함수**로 정의한 것이다.

**`GROUPING()` 을 `WHERE` 에 쓰면 양쪽 다 거부한다.**

```text
### SQL: SELECT dept_id FROM emp WHERE GROUPING(dept_id) = 1 GROUP BY ROLLUP(dept_id);
--- PG 18.6 ---
ERROR:  grouping operations are not allowed in WHERE
LINE 1: SELECT dept_id FROM emp WHERE GROUPING(dept_id) = 1 GROUP BY...
                                      ^
--- MySQL 8.4.10 ---
ERROR 1111 (HY000) at line 1: Invalid use of group function
```

**`HAVING` 에서는 양쪽 다 된다.**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY ROLLUP(dept_id) HAVING GROUPING(dept_id) = 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  s                    +---------+------+
---------+------                 | dept_id | s    |
    NULL | 1200                  +---------+------+
(1 row)                          |    NULL | 1200 |
                                 +---------+------+
```

★ **뿌리는 [01번](../01-logical-query-processing-order/)의 처리 순서다** — `GROUPING()` 은 그룹이 만들어진 뒤에야 답이 있다. `WHERE`(2번 칸)에는 아직 그룹이 없다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
-- 표준형 (양쪽에서 돈다)
GROUP BY ROLLUP(a, b)            -- (a,b) (a) ()
GROUP BY CUBE(a, b)              -- (a,b) (a) (b) ()          PG 만
GROUP BY GROUPING SETS ((a,b), (a), ())  -- 고른 것만          PG 만

-- MySQL 전용
GROUP BY a, b WITH ROLLUP        -- PG 에서는 syntax error

-- 소계 판별
GROUPING(a)        -- 그 행에서 a 를 접었으면 1, 아니면 0
GROUPING(a, b)     -- 비트마스크. 왼쪽이 높은 비트
```

규칙 여덟.

1. **`ROLLUP`·`CUBE` 는 `GROUPING SETS` 의 줄임말이다.** 셋을 따로 외울 필요가 없다.
2. **`ROLLUP` 은 앞에서부터 벗긴다** — 계층이 있을 때(연 → 월 → 일).
3. **`CUBE` 는 부분집합 전부** — 축이 독립일 때. 열 N개면 그룹 집합이 2의 N승이다.
4. ★ **접힌 열 자리에는 `NULL` 이 찍힌다.** 데이터의 `NULL` 과 **구분되지 않는다.**
5. ★ **`GROUPING(열)` 이 유일한 판별 수단이다** — 접었으면 1, 실제 값이면 0.
6. **`GROUPING()` 은 `SELECT`·`HAVING`·`ORDER BY` 에서 쓸 수 있고 `WHERE` 에서는 못 쓴다**(양쪽 동일).
7. **`GROUPING()` 을 `ROLLUP` 없이 쓰면 PG 는 0을 내고 MySQL 은 `ERROR 1111`** 이다.
8. **MySQL 8.4.10 은 `ROLLUP` 만 된다.** `GROUPING SETS` 는 `ERROR 1064`, `CUBE` 는 `ERROR 3889` 다.

실전 형태는 사실상 **셋**이다.

```sql
-- (1) 소계 + 총계 한 장
SELECT dept_id, SUM(salary) FROM emp GROUP BY ROLLUP(dept_id);

-- (2) 사람이 읽을 라벨 (GROUPING 을 먼저 본다)
SELECT CASE WHEN GROUPING(dept_id) = 1 THEN '(total)'
            WHEN dept_id IS NULL THEN '(no dept)'
            ELSE CAST(dept_id AS CHAR(10)) END AS dept, SUM(salary)
FROM emp GROUP BY ROLLUP(dept_id);

-- (3) 소계 줄만 뽑기
SELECT dept_id, SUM(salary) FROM emp GROUP BY ROLLUP(dept_id) HAVING GROUPING(dept_id) = 1;
```

## 어디서 틀리나

- **★ 소계 행의 `NULL` 을 데이터로 읽는다.**\
  `dan` 의 그룹과 총계 줄이 **둘 다 `dept_id = NULL`** 이다. `CUBE` 에서는 **합계까지 같은 두 행**이 나왔다.
- **★ `CASE` 에서 `IS NULL` 을 `GROUPING()` 보다 먼저 본다.**\
  총계 줄도 「(no dept)」가 된다. **`GROUPING()` 을 먼저 본다.**
- **`COALESCE(dept_id, '전체')` 로 총계를 라벨링한다.**\
  `dan` 의 그룹도 「전체」가 된다. **`COALESCE` 로는 두 `NULL` 을 못 가른다** — 그게 `GROUPING()` 이 있는 이유다.
- **`WHERE GROUPING(...) = 1` 로 소계만 거른다.**\
  양쪽 다 에러다. `HAVING` 에 쓴다.
- **`ORDER BY dept_id` 만 걸고 소계 줄 위치를 기대한다.**\
  `NULL` 이 둘이라 순서가 안 정해진다. `ORDER BY GROUPING(dept_id), dept_id` 로 **접힌 것을 뒤로** 보낸다.
- **`WITH ROLLUP` 을 이식한다.**\
  PG 에서 `syntax error at or near "WITH"` 다. `GROUP BY ROLLUP(...)` 을 쓴다.
- **「MySQL 에 `CUBE` 가 없다」고 적는다.**\
  ★ **없는 게 아니라 `ERROR 3889` 로 보조 엔진을 요구한다.** 결과는 「기본 구성에서 못 쓴다」로 같지만 **이유가 다르고**, 「문서에 없어서 없다고 봤다」와 **근거의 강도가 다르다.**
- **`CUBE` 를 열 넷에 쓴다.**\
  그룹 집합이 16개가 된다. `GROUPING SETS` 로 필요한 것만 적는다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `ROLLUP`/`CUBE` 의 확장 규칙 | **정의** | 언어 — PG 문서가 등가 `GROUPING SETS` 로 적는다 |
| 접힌 열 자리가 `NULL` 이 되는 것 | **정의** | 언어 — PG 문서 *"replaced by null values in result rows"* |
| `GROUPING()` 이 0/1 을 내는 것 | **정의** | 언어 — 두 문서가 같은 모양으로 적는다 |
| `GROUPING(a, b)` 의 비트 배치 | **정의** | 언어 — 0·1·3 이 두 엔진에서 같았다 |
| `GROUPING()` 을 `WHERE` 에 못 쓰는 것 | **정의**(처리 순서) | 언어 — 메시지는 다르고 거부는 같다 |
| `ROLLUP` 없이 `GROUPING()` | **방언** | PG 는 0, MySQL 은 `ERROR 1111` |
| MySQL 의 `CUBE` | **구성 의존** | `ERROR 3889` — 보조 엔진이 있어야 한다. 이 환경에서는 못 쓴다 |
| 소계 행이 **어디에 놓이나** | 아무도 보장 안 함 | `ORDER BY` 없이는 위치가 안 정해진다. `NULL` 이 둘이면 `ORDER BY dept_id` 로도 부족하다 |

- **값은 두 엔진에서 갈리지 않았다.** `ROLLUP` 이 도는 자리에서는 숫자가 전부 같았다.
- **갈리는 것은 「무엇이 도느냐」다** — `GROUPING SETS`·`CUBE`·`WITH ROLLUP`·`ROLLUP 없는 GROUPING()`.
- ★ **에러 번호가 근거다.** `1064`(문법 없음) 와 `3889`(실행 경로 없음) 는 **다른 말**이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 리포트 한 장에 여러 집계 수준이 필요할 때.** 질의를 두 번 던지고 앱에서 합치는 것보다 스캔이 한 번이다.
- **쓴다 — 계층이 분명할 때 `ROLLUP`.** 연/월/일, 대분류/소분류.
- **쓴다 — 축이 독립일 때 `CUBE`**(PG 한정). 지역 × 제품 × 채널.
- **쓴다 — 필요한 줄만 뽑을 때 `GROUPING SETS`.** `CUBE` 가 만드는 줄의 대부분이 안 쓰이면 이쪽이다.
- **안 쓴다 — 이식이 필요한데 `ROLLUP` 을 넘어설 때.** MySQL 에서는 `UNION ALL` 로 손으로 적는다.
- **안 쓴다 — 미리 말아 둘 수 있는 집계.** 매번 전체 스캔이 도는 리포트라면 사전 집계가 답이고 그건 [`systems/timeseries-resolution-tiers`](../../../../../systems/timeseries-resolution-tiers/)다.
- **`GROUPING()` 은 선택이 아니다.** 데이터에 `NULL` 이 있을 수 있는 열을 접으면 **반드시** 같이 뽑는다.

## 핵심 문장

- `ROLLUP`·`CUBE` 는 **`GROUPING SETS` 의 줄임말**이다 — 앞에서부터 벗기기 대 부분집합 전부.
- **한 질의가 여러 집계 수준을 한 번에 낸다.** 스캔은 한 번이다.
- ★ **접힌 열 자리에 `NULL` 이 찍히고, 데이터의 `NULL` 과 구분되지 않는다.**
- ★ **`GROUPING(열)` 이 유일한 판별 수단이다** — 접었으면 1, 실제 값이면 0. `COALESCE` 로는 못 가른다.
- `CUBE(dept_id, name)` 에서 **`NULL / dan / 400`** 인 행이 **둘** 나왔다. `gd` 하나만 다르고 나머지가 전부 같았다.
- **`CASE` 는 `GROUPING()` 을 먼저 본다.** `IS NULL` 을 먼저 쓰면 총계가 「소속 없음」이 된다.
- **`GROUPING()` 은 `SELECT`·`HAVING`·`ORDER BY` 에서 되고 `WHERE` 에서는 안 된다**(양쪽 동일).
- **MySQL 8.4.10 은 `ROLLUP` 만 된다.** `GROUPING SETS` 는 `ERROR 1064`(문법 없음).
- ★ **`CUBE` 는 `ERROR 3889` — 「보조 엔진이 없다」다.** 파서는 알아듣는다. **「미지원」과 다른 말이다.**
- **이식하려면 `GROUP BY ROLLUP(...)`** 를 쓴다. `WITH ROLLUP` 은 PG 에서 문법 오류다.

## 관련 자료

- [PostgreSQL 18 · GROUPING SETS, CUBE, and ROLLUP](https://www.postgresql.org/docs/18/queries-table-expressions.html) — 확장 규칙과 *"replaced by null values in result rows"* 문장.
- [PostgreSQL 18 · Grouping Operations](https://www.postgresql.org/docs/18/functions-aggregate.html) — `GROUPING()` 의 정의.
- [MySQL 8.4 · GROUP BY Modifiers](https://dev.mysql.com/doc/refman/8.4/en/group-by-modifiers.html) — `WITH ROLLUP`·대체 `ROLLUP(...)` 문법·`GROUPING()`. **`CUBE`·`GROUPING SETS` 는 이 페이지에 없다.**
- [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) — **경계: 그쪽은 그룹 집합이 하나일 때의 규칙까지, 여기는 그것이 여럿이 되는 것부터.**
- [21 집계 함수와 COUNT 의 세 형태](../21-aggregate-functions-count-forms/) — 소계 줄의 `SUM` 이 `NULL` 인 이유.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — `GROUPING()` 을 `WHERE` 에 못 쓰는 이유.
- [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/) — 소계 줄만 거를 때 `HAVING` 을 쓰는 이유.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — 「비교는 `UNKNOWN`」이 소계 `NULL` 에도 그대로 걸린다.
- [24 조건부 집계 — FILTER 와 CASE](../24-conditional-aggregation-filter-case/) — 소계 대신 **열을 늘려** 여러 조건을 나란히 놓는 법.
- [`systems/timeseries-resolution-tiers`](../../../../../systems/timeseries-resolution-tiers/) — **경계: 사전 집계를 어떤 해상도로 저장할지의 운영 전략은 거기, 여기는 한 질의로 뽑는 문법.**
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **그룹 집합(grouping set)** — 한 질의 안에서 쓰이는 하나의 `GROUP BY` 목록.\
  예: `ROLLUP(dept_id)` 는 `(dept_id)` 와 `()` 두 개다.
- **`ROLLUP(a, b)`** — `(a,b)`·`(a)`·`()` 세 그룹 집합. **앞에서부터 벗긴다.**\
  예: 연/월 매출에서 월별 줄, 연 소계 줄, 총계 줄이 한 번에 나온다.
- **`CUBE(a, b)`** — `(a,b)`·`(a)`·`(b)`·`()` 네 그룹 집합. **부분집합 전부.**\
  예: 지역별·제품별·지역×제품별·전체가 한 번에 나온다.
- **`GROUPING SETS (…)`** — 원하는 그룹 집합만 직접 적는 형태. 위 둘의 원형이다.\
  예: `GROUPING SETS ((dept_id), ())` 는 `ROLLUP(dept_id)` 과 같은 결과를 냈다.
- **소계 행(super-aggregate row)** — 어떤 열을 접어서 만든 행. 그 열 자리에 `NULL` 이 찍힌다.\
  예: 총계 줄의 `dept_id`. `COUNT(*)` 이 4(표 전체)인 것으로 확인된다.
- **`GROUPING(열)`** — 그 행에서 그 열을 **접었으면 1**, 실제 값이면 **0** 을 내는 함수.\
  예: `dan` 의 그룹은 0, 총계 줄은 1. 이것만이 두 `NULL` 을 가른다.
- **비트마스크(bitmask)** — 여러 참/거짓을 한 정수의 비트로 담은 것.\
  예: `GROUPING(dept_id, name)` 이 3이면 둘 다 접었다는 뜻이다(2진수 `11`).
- **`WITH ROLLUP`** — MySQL 의 `GROUP BY` 수식어. **PG 에는 없다.**\
  예: `GROUP BY dept_id WITH ROLLUP`. PG 에서는 `syntax error at or near "WITH"` 다.
- **`ERROR 1064`** — MySQL 의 문법 오류. **파서가 모르는 말**이라는 뜻이다.\
  예: `GROUPING SETS` 는 `SETS` 에서 이 에러가 났다.
- **`ERROR 3889` · 보조 엔진(secondary engine)** — 질의를 대신 돌리는 별도 실행 엔진이 필요한데 없다는 뜻.\
  예: MySQL 8.4.10 의 `CUBE`. **파서는 알아듣고 실행에서 막혔다.**

## 더 들어가면

- **MySQL 에서 `GROUPING SETS` 가 필요하면 `UNION ALL` 로 손으로 적는다.**\
  그룹 집합마다 질의를 하나씩 쓰고 잇는다. 대가는 **스캔이 그 수만큼 돈다**는 것이다 — `ROLLUP` 의 값이 정확히 거기 있다.
- **소계 줄을 위로 올리려면 정렬 키를 하나 더 만든다.**\
  `ORDER BY GROUPING(dept_id) DESC, dept_id` 처럼. `NULL` 의 정렬 위치 자체는 [목록의 **8번 주제**](../08-order-by-null-position-stability/)이고 두 엔진이 다르다.
- **`GROUPING_ID()` 같은 이름이 다른 엔진에도 있지만 여기서는 확인하지 않았다.** 두 매뉴얼에서 본 것만 적는다.
- **`GROUPING()` 의 인자는 `GROUP BY` 에 나온 식이어야 한다.** 아무 열이나 넣으면 의미가 없다 — 접힌 적이 없으니 항상 0이다.\
  PG 가 `ROLLUP` 없는 질의에서 전부 0을 낸 것이 그 모습이다(5번 (마)).
