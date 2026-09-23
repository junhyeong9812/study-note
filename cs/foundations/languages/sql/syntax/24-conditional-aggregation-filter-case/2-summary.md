# sql/24-조건부 집계 — `FILTER` 와 `CASE` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Aggregate Expressions](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 · Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `FILTER` 는 **PostgreSQL 에만** 있다. MySQL 8.4.10 은 `ERROR 1064` 로 **파싱조차 못 한다**(3번). 도입 버전은 PG 매뉴얼에서 확인하지 못해 적지 않는다.\
> **선행** — [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) · [목록의 **6번 주제**](../06-conditional-expressions-case-coalesce/)(조건 식 — `CASE`·`COALESCE`·`NULLIF`).\
> **바로 앞** — [21 집계 함수와 COUNT 의 세 형태](../21-aggregate-functions-count-forms/). **거기서 배운 「집계는 `NULL` 을 건너뛴다」가 여기서 세 형태를 가른다.**\
> **뒤 주제** — [25 조인 팬아웃](../25-join-fan-out/).

## 한눈에 — 쉽게 말하면

**한 번 훑으면서 손에 든 계수기 여러 개를 조건별로 따로 누르는 것.**

- 「급여 400 이상 몇 명」을 `WHERE` 로 세면 **훑기 한 번에 답 하나**다. 세 가지를 알려면 **세 번 훑는다.**
- 조건부 집계는 **한 번 훑으면서** 계수기마다 다른 조건을 건다. 답이 **열로 나란히** 나온다.
- ★ 그런데 **계수기를 만드는 법이 셋**이고, **`NULL` 에서 답이 갈린다.**

| 비유 | 실체 | 하는 일 |
|---|---|---|
| 훑는 대상을 줄이는 문지기 | `WHERE` | 행을 아예 버린다. **모든 계수기에 같이 적용**된다 |
| 계수기마다 붙인 조건표 | `agg(...) FILTER (WHERE …)` | 그 계수기에만 걸린다. **PG 전용** |
| 조건이 아니면 빈칸을 넣기 | `agg(CASE WHEN … THEN … END)` | 안 맞으면 `NULL` → 집계가 건너뛴다. **양쪽에서 돈다** |
| 조건이 아니면 0을 넣기 | `agg(CASE WHEN … THEN … ELSE 0 END)` | 안 맞아도 **0이 계산에 들어간다** ← 여기가 함정 |

```text
WHERE 로 세기 (3 번 훑는다)          조건부 집계 (1 번 훑는다)
+---------------------------+       +-----------------------------------+
| WHERE salary >= 400  -> 2 |       | total | hi | lo | unknown | in10  |
| WHERE salary <  400  -> 1 |  ──>  |     4 |  2 |  1 |       1 |    2  |
| WHERE salary IS NULL -> 1 |       +-----------------------------------+
+---------------------------+                한 줄에 다 나온다
     답이 따로따로 나온다              그리고 total 과의 관계가 눈에 보인다
```

**이 계수기가 똑같은 구조로** 조건부 집계다.\
★ 그리고 **`hi`(2) + `lo`(1) 이 `total`(4) 이 안 되는 것**이 이 주제의 첫 교훈이다 — `cho` 의 `NULL` 은 **어느 조건에도 안 걸린다**([04번](../04-null-three-valued-logic/)).

> **조건부 집계(conditional aggregation)** — 한 번의 스캔으로 **조건이 다른 여러 집계**를 동시에 뽑는 것.\
> 예: `COUNT(*) FILTER (WHERE salary >= 400)` 과 `COUNT(*)` 을 한 질의에 나란히 두는 것.

> **`FILTER` 절** — 그 집계 함수 **하나에만** 걸리는 행 조건. PG 문서: *"only the input rows for which the filter_clause evaluates to true are fed to the aggregate function; other rows are discarded."*\
> 예: `SUM(salary) FILTER (WHERE dept_id = 10)`.

## 이 주제가 답하려는 질문

1. **`WHERE` 로는 왜 한 번에 못 하나?** — `WHERE` 는 모든 열에 같이 걸린다.
2. **★ 세 형태의 답이 어디서 갈리나?** — 조건에 맞는 행이 **하나도 없는 그룹**에서, 그리고 `AVG` 에서.
3. **MySQL 에는 `FILTER` 가 없는데 무엇으로 쓰나?** — 그리고 그 대체가 정확히 같은가.

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

★ **`cho`(급여 `NULL`)가 이 주제의 시험지다.**

- `dept_id=20` 그룹은 **`salary >= 400` 에 맞는 행이 하나도 없다** — 세 형태가 여기서 갈린다(4번).
- `dept_id=10` 그룹은 **둘 중 하나만** 맞는다 — `AVG` 가 여기서 갈린다(5번).
- 표 전체에서 `hi + lo ≠ total` 이 된다 — `cho` 가 양쪽 어디에도 안 걸리기 때문이다.

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

### 1. `WHERE` 로는 한 번에 못 한다 — 문지기는 하나뿐이다

**언제 쓰나** — 「이 조건 몇 개, 저 조건 몇 개」를 한 표로 내야 할 때.

```text
FROM ──> WHERE ──> GROUP BY ──> SELECT
           ^
   여기를 지난 행은 모든 열에 대해 같은 행이다
   열마다 다른 조건을 걸 자리가 아니다
```

`WHERE` 로 하려면 **질의를 나눠야 한다.**

```text
### SQL: SELECT COUNT(*) AS c FROM emp WHERE salary >= 400;
--- PG 18.6 ---    --- MySQL 8.4.10 ---
 c                 +---+
---                | c |
 2                 +---+
(1 row)            | 2 |
                   +---+

### SQL: SELECT COUNT(*) AS c FROM emp WHERE salary < 400;
--- PG 18.6 ---    --- MySQL 8.4.10 ---
 c                 +---+
---                | c |
 1                 +---+
(1 row)            | 1 |
                   +---+

### SQL: SELECT COUNT(*) AS c FROM emp WHERE salary IS NULL;
--- PG 18.6 ---    --- MySQL 8.4.10 ---
 c                 +---+
---                | c |
 1                 +---+
(1 row)            | 1 |
                   +---+
```

그림 해설 — **세 번 훑어서 세 숫자를 얻었고, 그 셋을 한 화면에 놓으려면 앱에서 합쳐야 한다.**\
대가 — 스캔이 세 번이고, **세 답이 같은 시점의 데이터라는 보장도 없다**(트랜잭션 밖이면).

★ **`WHERE` 를 쓰지 말라는 게 아니다.** 「전부 이 조건 안의 이야기」이면 `WHERE` 가 맞고 **더 싸다** — 행을 아예 안 읽는다.\
조건부 집계는 「**같은 모집단을 여러 각도로 쪼갤 때**」다. 둘을 같이 쓰기도 한다(7번).

---

### 2. `FILTER` — 계수기마다 조건을 붙인다 (PostgreSQL)

**언제 쓰나** — PG 에서 조건부 집계를 쓸 때. 읽기 가장 좋은 형태다.

```text
COUNT(*) FILTER (WHERE salary >= 400)
  ^^^^^^        ^^^^^^^^^^^^^^^^^^^^^
  이 계수기만    이 조건으로 거른 행을 받는다
```

```text
### SQL: SELECT COUNT(*) AS total,
                COUNT(*) FILTER (WHERE salary >= 400)  AS hi,
                COUNT(*) FILTER (WHERE salary <  400)  AS lo,
                COUNT(*) FILTER (WHERE salary IS NULL) AS unknown,
                COUNT(*) FILTER (WHERE dept_id = 10)   AS in10
         FROM emp;
--- PG 18.6 ---
 total | hi | lo | unknown | in10
-------+----+----+---------+------
     4 |  2 |  1 |       1 |    2
(1 row)
```

그림 해설 — **한 번 훑고 다섯 계수기를 동시에 눌렀다.** 1번의 세 질의가 한 줄이 됐다.

★ **`hi`(2) + `lo`(1) = 3 이지 4가 아니다.**

```text
 salary = [300, 500, NULL, 400]

 salary >= 400  ->  FALSE TRUE  UNKNOWN TRUE   -> 2 개
 salary <  400  ->  TRUE  FALSE UNKNOWN FALSE  -> 1 개
                                 ^^^^^^^
                    NULL 은 양쪽 어디에도 안 들어간다
                    FILTER 는 "TRUE 인 행" 만 통과시킨다 (FALSE 와 UNKNOWN 을 같이 버린다)
```

[04번](../04-null-three-valued-logic/)의 3값 논리가 **`FILTER` 의 `WHERE` 안에서도 그대로 작동한다.**\
그래서 `unknown` 계수기를 **따로 두는 것**이 실무 습관이다 — 합이 `total` 이 되는지 눈으로 검산할 수 있다.

**그룹별로도 같다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS c,
                COUNT(*) FILTER (WHERE salary >= 400)    AS hi,
                SUM(salary) FILTER (WHERE salary >= 400) AS hi_sum
         FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---
 dept_id | c | hi | hi_sum
---------+---+----+--------
      10 | 2 |  1 |    500
      20 | 1 |  0 |   NULL
    NULL | 1 |  1 |    400
(3 rows)
```

★ **`dept_id=20` 을 보라 — `hi`=0 인데 `hi_sum`=`NULL` 이다.**\
[21번](../21-aggregate-functions-count-forms/)의 규칙 그대로다 — **빈 입력에서 `COUNT` 만 0이고 `SUM` 은 `NULL`** 이다.\
`FILTER` 가 행을 다 걸러 내면 그 집계의 입력이 0행이 된다. 새 규칙이 아니라 같은 규칙이다.

비용 — 스캔 한 번. PG 문서가 *"other rows are discarded"* 라고만 적고 **성능은 말하지 않는다.** 여기서도 **재지 않았다.**

---

### 3. MySQL 에는 `FILTER` 가 없다 — 문법 자체가 없다

**언제 쓰나** — 이식성을 판단할 때. 「미지원」이라 적기 전에 던져 봤다.

```text
### SQL: SELECT COUNT(*) FILTER (WHERE salary >= 400) AS hi FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 hi                              ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '(WHERE salary >= 400) AS hi FROM emp' at line 1
----
  2
(1 row)
```

```text
### SQL: SELECT dept_id, COUNT(*) AS c, COUNT(*) FILTER (WHERE salary >= 400) AS hi,
                SUM(salary) FILTER (WHERE salary >= 400) AS hi_sum
         FROM emp GROUP BY dept_id ORDER BY dept_id;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '(WHERE salary >= 400) AS hi, SUM(salary) FILTER (WHERE salary >= 400) AS hi_sum ' at line 1
```

그림 해설 — ★ **`ERROR 1064` 는 「파서가 모르는 말」이라는 뜻이다.**\
에러가 `FILTER` 다음의 `(WHERE …` 에서 났다 — `FILTER` 까지는 **평범한 식별자로 읽었다가** 괄호에서 걸린 것이다.\
MySQL 8.4 매뉴얼의 집계 함수 문법에도 `FILTER` 절이 **없다.** 설정으로 켤 수 있는 것이 아니다.

★ **[23번](../23-grouping-sets-rollup-cube/)의 `CUBE` 와 대비하라** — 거기는 `ERROR 3889`(파서는 알아듣고 실행 경로가 없다)였고, 여기는 `1064`(말 자체가 없다)다.\
**「없다」의 종류가 다르고, 에러 번호가 그것을 말해 준다.**

대가 — 이식하려면 `CASE` 로 써야 하고, **그때 형태 선택에서 사고가 난다**(4·5번).

---

### 4. ★ 세 형태가 `NULL` 에서 갈린다

**언제 쓰나** — `CASE` 로 조건부 집계를 쓸 때마다. **이 주제의 중심이다.**

```text
 같은 뜻처럼 들리는 네 가지

 (A) SUM(CASE WHEN c THEN 1 ELSE 0 END)     안 맞으면 0 을 더한다
 (B) SUM(CASE WHEN c THEN 1 END)            안 맞으면 NULL -> 안 더한다
 (C) COUNT(CASE WHEN c THEN 1 END)          안 맞으면 NULL -> 안 센다
 (D) COUNT(CASE WHEN c THEN 1 ELSE 0 END)   안 맞으면 0 -> 0 도 값이라 센다   <- 거의 항상 버그
```

```text
### SQL: SELECT dept_id,
                SUM(CASE WHEN salary >= 400 THEN 1 ELSE 0 END)   AS sum_else0,
                SUM(CASE WHEN salary >= 400 THEN 1 END)          AS sum_noelse,
                COUNT(CASE WHEN salary >= 400 THEN 1 END)        AS cnt_case,
                COUNT(CASE WHEN salary >= 400 THEN 1 ELSE 0 END) AS cnt_case_else0
         FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---
 dept_id | sum_else0 | sum_noelse | cnt_case | cnt_case_else0
---------+-----------+------------+----------+----------------
      10 |         1 |          1 |        1 |              2
      20 |         0 |       NULL |        0 |              1
    NULL |         1 |          1 |        1 |              1
(3 rows)
--- MySQL 8.4.10 ---
+---------+-----------+------------+----------+----------------+
| dept_id | sum_else0 | sum_noelse | cnt_case | cnt_case_else0 |
+---------+-----------+------------+----------+----------------+
|    NULL |         1 |          1 |        1 |              1 |
|      10 |         1 |          1 |        1 |              2 |
|      20 |         0 |       NULL |        0 |              1 |
+---------+-----------+------------+----------+----------------+
```

그림 해설 — **두 자리에서 갈렸다.**

| 자리 | 무엇이 갈렸나 | 왜 |
|---|---|---|
| `dept_id=20` | `sum_else0`=**0** 대 `sum_noelse`=**NULL** | 맞는 행이 0개 → `SUM` 의 입력이 0행 → `NULL`([21번](../21-aggregate-functions-count-forms/)) |
| `dept_id=10` | `cnt_case`=**1** 대 `cnt_case_else0`=**2** | `ELSE 0` 이 만든 **0도 `NULL` 이 아니라서 세어진다** |

```text
 dept_id=10 그룹  salary = [300, 500]

 CASE WHEN salary >= 400 THEN 1 END        -> [NULL, 1]
     COUNT 은 NULL 을 안 센다              -> 1   맞다
 CASE WHEN salary >= 400 THEN 1 ELSE 0 END -> [0, 1]
     COUNT 은 0 을 센다 (0 은 NULL 이 아니다) -> 2   틀렸다. 이건 COUNT(*) 이다
```

★★ **`COUNT` 과 `ELSE 0` 을 같이 쓰면 조건이 통째로 무의미해진다.** 결과가 항상 `COUNT(*)` 이다.\
`dept_id=10` 에서 2가 나온 것이 그 증거다 — 그 그룹 인원수와 같다.

```text
 무엇을 쓸까
 +--------------------------------------------------+
 | 개수를 센다            -> COUNT(CASE WHEN c THEN 1 END)
 |                          또는 SUM(CASE WHEN c THEN 1 ELSE 0 END)
 | 값을 더한다            -> SUM(CASE WHEN c THEN 값 END)
 | COUNT 에 ELSE 는 절대 붙이지 않는다
 +--------------------------------------------------+
```

**「0이냐 `NULL` 이냐」는 고르는 것이다.** 「맞는 게 없으면 0건」으로 보이려면 `SUM(... ELSE 0)`,\
「맞는 게 없으면 값 없음」으로 두려면 `SUM(... END)` 또는 `COUNT(... END)`. **둘 다 맞는 답이고 뜻이 다르다.**

대가 — `ELSE 0` 을 쓰면 `SUM` 은 0으로 보이지만, **같은 습관이 `AVG` 에 옮겨 가면 값이 틀린다**(5번).

---

### 5. ★ `AVG` 에서 `ELSE 0` 은 **분모를 오염시킨다**

**언제 쓰나** — 조건부 평균을 낼 때. 4번의 습관이 여기서 사고가 된다.

```text
 dept_id=10 그룹  salary = [300, 500],  조건: salary >= 400

 CASE WHEN c THEN salary END        -> [NULL, 500]
     AVG 의 분모 = COUNT(열) = 1     -> 500 / 1 = 500
 CASE WHEN c THEN salary ELSE 0 END -> [0, 500]
     AVG 의 분모 = COUNT(열) = 2     -> 500 / 2 = 250     <- 사람이 하나 더 세어졌다
```

```text
### SQL: SELECT dept_id,
                SUM(CASE WHEN salary >= 400 THEN salary END)        AS s_noelse,
                SUM(CASE WHEN salary >= 400 THEN salary ELSE 0 END) AS s_else0,
                AVG(CASE WHEN salary >= 400 THEN salary END)        AS a_noelse,
                AVG(CASE WHEN salary >= 400 THEN salary ELSE 0 END) AS a_else0
         FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---
 dept_id | s_noelse | s_else0 |       a_noelse       |        a_else0
---------+----------+---------+----------------------+------------------------
      10 |      500 |     500 | 500.0000000000000000 |   250.0000000000000000
      20 |     NULL |       0 |                 NULL | 0.00000000000000000000
    NULL |      400 |     400 | 400.0000000000000000 |   400.0000000000000000
(3 rows)
--- MySQL 8.4.10 ---
+---------+----------+---------+----------+----------+
| dept_id | s_noelse | s_else0 | a_noelse | a_else0  |
+---------+----------+---------+----------+----------+
|    NULL |      400 |     400 | 400.0000 | 400.0000 |
|      10 |      500 |     500 | 500.0000 | 500.0000 |
|      20 |     NULL |       0 |     NULL |   0.0000 |
+---------+----------+---------+----------+----------+
```

★ **`SUM` 은 `s_noelse`·`s_else0` 가 같은데(500·500) `AVG` 는 500 과 250 으로 갈렸다.**\
[21번](../21-aggregate-functions-count-forms/)의 「`AVG` 의 분모는 `COUNT(열)` 이다」가 여기서 값을 바꾼다.

```text
 SUM 에서                        AVG 에서
 0 을 더해도 합은 그대로다        0 을 더하면 분모가 늘어난다
 -> 두 형태가 같은 답             -> 두 형태가 다른 답
        |                              |
  그래서 안심하고 ELSE 0 을         그 습관을 그대로 옮겨 오면
  쓰는 습관이 생긴다               조용히 평균이 내려간다
```

★★ **이 사고가 위험한 이유는 「평균이 내려간다」가 그럴듯해 보이기 때문이다.** 250도 「있을 법한 평균」이다.\
대가 — 없다. **`AVG` 에는 `ELSE` 를 쓰지 않는다**로 고정하면 끝이다.

★ **경계: 「`AVG` 의 분모」 자체는 [21번](../21-aggregate-functions-count-forms/)이 정본이다. 여기는 조건부 집계에서 그 분모가 어떻게 오염되나부터.**

---

### 6. `FILTER` 는 **`ELSE` 없는 `CASE`** 와 정확히 같다

**언제 쓰나** — PG 질의를 MySQL 로 옮길 때. 무엇으로 바꿔야 하는지의 답이다.

```text
COUNT(*)    FILTER (WHERE c)   ==  COUNT(CASE WHEN c THEN 1 END)
COUNT(열)   FILTER (WHERE c)   ==  COUNT(CASE WHEN c THEN 열 END)
SUM(열)     FILTER (WHERE c)   ==  SUM(CASE WHEN c THEN 열 END)
AVG(열)     FILTER (WHERE c)   ==  AVG(CASE WHEN c THEN 열 END)
                                             ^^^^^^^^^^^^^^^^^
                                        ELSE 는 절대 붙이지 않는다
```

```text
### SQL: SELECT dept_id,
                COUNT(*) FILTER (WHERE salary >= 400)        AS f_star,
                COUNT(CASE WHEN salary >= 400 THEN 1 END)    AS c_case,
                SUM(salary) FILTER (WHERE salary >= 400)     AS f_sum,
                SUM(CASE WHEN salary >= 400 THEN salary END) AS c_sum,
                AVG(salary) FILTER (WHERE salary >= 400)     AS f_avg,
                AVG(CASE WHEN salary >= 400 THEN salary END) AS c_avg
         FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---
 dept_id | f_star | c_case | f_sum | c_sum |        f_avg         |        c_avg
---------+--------+--------+-------+-------+----------------------+----------------------
      10 |      1 |      1 |   500 |   500 | 500.0000000000000000 | 500.0000000000000000
      20 |      0 |      0 |  NULL |  NULL |                 NULL |                 NULL
    NULL |      1 |      1 |   400 |   400 | 400.0000000000000000 | 400.0000000000000000
(3 rows)
```

그림 해설 — **세 쌍이 열마다 한 글자도 같다.** `NULL` 인 자리까지 같다.\
**이식은 기계적으로 된다** — `FILTER (WHERE c)` 를 인자 자리의 `CASE WHEN c THEN … END` 로 옮기면 그만이다.

**`DISTINCT` 와도 같이 쓸 수 있고, 그것도 대응된다.**

```text
### SQL: SELECT COUNT(DISTINCT salary) FILTER (WHERE dept_id = 10) AS d_f,
                COUNT(DISTINCT CASE WHEN dept_id = 10 THEN salary END) AS d_c
         FROM emp;
--- PG 18.6 ---
 d_f | d_c
-----+-----
   2 |   2
(1 row)
```

★ **그래도 `FILTER` 를 쓸 값이 있다 — 읽힌다.**\
`COUNT(*) FILTER (WHERE …)` 는 「무엇을 세는지」가 앞에 있고 조건이 뒤에 있다.\
`COUNT(CASE WHEN … THEN 1 END)` 는 **`THEN 1` 이라는 의미 없는 값**을 읽는 사람이 해석해야 한다.

대가 — 이식성. **PG 전용 코드가 된다.** 두 엔진을 다 지원해야 하면 처음부터 `CASE` 로 통일하는 편이 낫다.

---

### 7. `WHERE` 와 `FILTER` 는 **순서가 있다**

**언제 쓰나** — 둘을 같이 쓸 때. 「이미 걸렀는데 또 거른다」가 헷갈릴 때.

```text
FROM ──> WHERE ──> GROUP BY ──> 집계 계산 (여기서 FILTER 가 걸린다)
           ^                            ^
   모든 계수기의 공통 모집단      계수기마다 추가로 거른다
```

```text
### SQL: SELECT COUNT(*) AS all_rows, COUNT(*) FILTER (WHERE dept_id = 10) AS d10
         FROM emp WHERE salary IS NOT NULL;
--- PG 18.6 ---
 all_rows | d10
----------+-----
        3 |   2
(1 row)
```

그림 해설 — `WHERE salary IS NOT NULL` 이 **먼저** `cho` 를 버려 모집단이 3이 됐고,\
그 위에서 `FILTER` 가 `dept_id=10` 인 둘을 셌다.

```text
 emp 4행
   |
   WHERE salary IS NOT NULL  -> ann bob dan (3행)     <- all_rows = 3
   |
   FILTER (WHERE dept_id=10) -> ann bob    (2행)      <- d10 = 2
```

★ **`WHERE` 를 좁히면 `FILTER` 의 모집단도 같이 좁아진다.** 「전체」라고 이름 붙인 열이 사실 전체가 아닐 수 있다.\
대가 — 그래서 **`total` 열을 같이 뽑아 두는 습관**이 값을 한다. 위에서 `all_rows` 가 4가 아니라 3인 것이 바로 보인다.

`WHERE` 가 싼 이유도 여기 있다 — **행을 아예 안 읽을 수 있다**(인덱스). `FILTER`·`CASE` 는 읽은 뒤에 판정한다.\
인덱스를 타고 안 타고는 [목록의 **47번 주제**](../47-when-indexes-are-used/)다. **여기서는 재지 않았다.**

## 문법 — 어느 절에서 무엇이 보이나

```sql
-- PostgreSQL 전용
집계함수([DISTINCT] 인자) FILTER (WHERE 조건)

-- 양쪽에서 도는 형태
COUNT(CASE WHEN 조건 THEN 1 END)          -- 개수
SUM  (CASE WHEN 조건 THEN 1 ELSE 0 END)   -- 개수 (0 으로 보이고 싶을 때)
SUM  (CASE WHEN 조건 THEN 값 END)         -- 값의 합
AVG  (CASE WHEN 조건 THEN 값 END)         -- 조건에 맞는 것들의 평균
```

규칙 여덟.

1. **`WHERE` 는 모든 계수기에 같이 걸리고, `FILTER`/`CASE` 는 그 계수기에만 걸린다.**
2. **`FILTER` 는 PG 전용이다.** MySQL 8.4.10 은 `ERROR 1064` — 문법 자체가 없다.
3. **`FILTER (WHERE c)` ≡ 인자 자리의 `CASE WHEN c THEN … END`.** 열마다 값이 같았다.
4. ★ **`COUNT` 에 `ELSE 0` 을 붙이면 안 된다.** 0도 세어져서 `COUNT(*)` 이 된다.
5. ★ **`AVG` 에 `ELSE 0` 을 붙이면 분모가 오염된다.** 500 이 250 이 됐다.
6. **`SUM` 에서는 `ELSE 0` 유무가 「0으로 보일지 `NULL` 로 둘지」의 선택**이다. 둘 다 맞는 답이다.
7. **조건에 맞는 행이 0개면 `COUNT` 는 0, `SUM`·`AVG` 는 `NULL`** 이다([21번](../21-aggregate-functions-count-forms/)).
8. **`NULL` 은 어느 조건에도 안 걸린다.** `hi + lo` 가 `total` 이 안 된다 — `unknown` 계수기를 따로 둔다.

실전 형태는 사실상 **셋**이다.

```sql
-- (1) 구간별 인원 한 줄로 (양쪽)
SELECT COUNT(*) AS total,
       SUM(CASE WHEN salary >= 400 THEN 1 ELSE 0 END) AS hi,
       SUM(CASE WHEN salary <  400 THEN 1 ELSE 0 END) AS lo,
       SUM(CASE WHEN salary IS NULL THEN 1 ELSE 0 END) AS unknown
FROM emp;

-- (2) 조건별 합계·평균 (양쪽) — ELSE 없음
SELECT dept_id,
       SUM(CASE WHEN salary >= 400 THEN salary END) AS hi_sum,
       AVG(CASE WHEN salary >= 400 THEN salary END) AS hi_avg
FROM emp GROUP BY dept_id;

-- (3) 같은 것을 PG 에서 읽기 좋게
SELECT dept_id,
       SUM(salary) FILTER (WHERE salary >= 400) AS hi_sum,
       AVG(salary) FILTER (WHERE salary >= 400) AS hi_avg
FROM emp GROUP BY dept_id;
```

## 어디서 틀리나

- **★ `COUNT(CASE WHEN c THEN 1 ELSE 0 END)` 를 쓴다.**\
  0도 세어져 **항상 `COUNT(*)`** 이 된다. `dept_id=10` 에서 1이 아니라 2가 나왔다.
- **★ `AVG(CASE WHEN c THEN 값 ELSE 0 END)` 를 쓴다.**\
  분모에 0이 합류해 평균이 내려간다. 500 이 250 이 됐다. **`AVG` 에 `ELSE` 는 없다.**
- **★ `hi + lo` 가 `total` 일 거라 믿는다.**\
  `NULL` 은 양쪽 어디에도 안 걸린다. `unknown` 계수기를 따로 두고 합을 검산한다.
- **조건에 안 맞는 그룹의 `SUM` 이 0일 거라 믿는다.**\
  `NULL` 이다. 0으로 보이려면 `ELSE 0` 을 쓰거나 `COALESCE` 로 감싼다.
- **`FILTER` 를 MySQL 에 이식한다.**\
  `ERROR 1064` 다. 설정으로 켤 수 없다. `CASE` 로 옮긴다.
- **`WHERE` 로 좁혀 놓고 `total` 이라 이름 붙인다.**\
  `WHERE` 가 이미 버린 행은 어떤 계수기에도 안 들어온다. 이름이 거짓말이 된다.
- **조건 열에 함수를 씌운다.**\
  `CASE WHEN YEAR(hired) = 2026` 류는 인덱스를 못 탄다 — 다만 조건부 집계는 대개 전체 스캔이라 **여기서는 큰 문제가 아니다.** 인덱스 이야기는 [목록의 **47번 주제**](../47-when-indexes-are-used/).
- **조건이 런타임에 정해지는데 열로 박는다.**\
  조건부 집계는 **조건이 미리 고정**돼 있어야 한다. 아니면 [23번](../23-grouping-sets-rollup-cube/)처럼 행으로 내거나 앱에서 조립한다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `FILTER` 가 `TRUE` 인 행만 넘기는 것 | **정의** | 언어(PG) — *"only the input rows for which the filter_clause evaluates to true"* |
| `CASE` 의 `ELSE` 가 없으면 `NULL` 인 것 | **정의** | 언어 — 양쪽 문서가 같은 모양으로 적는다 |
| 집계가 `NULL` 입력을 건너뛰는 것 | **정의** | 언어([21번](../21-aggregate-functions-count-forms/)) |
| `FILTER` ≡ `ELSE` 없는 `CASE` | **결과의 동치** | 실행으로 열마다 대조했다 — 정의에서 따라 나온다 |
| MySQL 에 `FILTER` 가 없는 것 | **문법 부재** | `ERROR 1064` — 설정으로 켤 수 없다 |
| `AVG` 결과의 소수 자릿수 | 결과 타입의 선택 | 엔진 — 값은 같다 |
| 한 스캔으로 도는지 | 옵티마이저 | **재지 않았다.** 적지 않는다 |

- **값이 갈린 자리는 없다.** `CASE` 형태는 두 엔진에서 숫자가 전부 같았다.
- **갈리는 것은 `FILTER` 의 존재 여부 하나다.**
- ★ **에러 번호가 근거다.** `1064`(문법 없음)는 [23번](../23-grouping-sets-rollup-cube/)의 `3889`(실행 경로 없음)와 **다른 말**이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 같은 모집단을 여러 각도로 쪼갤 때.** 「전체 / 이번 달 / 지난 달」을 한 줄에.
- **쓴다 — 피벗(가로 표).** 「부서 × 등급」 표를 행이 아니라 열로 낸다.
- **쓴다 — 비율.** `COUNT(*) FILTER (WHERE …) * 1.0 / COUNT(*)` 처럼 분자와 분모를 한 질의에.
- **안 쓴다 — 전부 한 조건 안의 이야기일 때.** 그건 `WHERE` 이고 **더 싸다.** 인덱스로 행을 아예 안 읽을 수 있다.
- **안 쓴다 — 조건이 런타임에 정해질 때.** 열 이름이 고정이라 조건도 고정이어야 한다.
- **안 쓴다 — 조건 수가 아주 많을 때.** 열이 수십 개가 되면 읽히지 않는다. 그때는 **행으로 내고**([23번](../23-grouping-sets-rollup-cube/)) 앱에서 돌린다.
- **두 엔진을 다 지원하면 `CASE` 로 통일한다.** `FILTER` 는 PG 전용 코드를 만든다.

## 핵심 문장

- **`WHERE` 는 모집단을 줄이고, `FILTER`/`CASE` 는 계수기마다 조건을 건다.** 스캔 한 번에 답이 여럿 나온다.
- **`FILTER` 는 PG 전용**이다. MySQL 8.4.10 은 `ERROR 1064` — **문법 자체가 없다.**
- **`FILTER (WHERE c)` ≡ 인자 자리의 `CASE WHEN c THEN … END`.** 열마다 `NULL` 자리까지 같았다.
- ★ **`COUNT` 에 `ELSE 0` 을 붙이면 0도 세어져 `COUNT(*)` 이 된다** — 1이 아니라 2가 나왔다.
- ★ **`AVG` 에 `ELSE 0` 을 붙이면 분모가 오염된다** — 500 이 250 이 됐다.
- **`SUM` 에서는 `ELSE 0` 유무가 「0으로 보일지 `NULL` 로 둘지」의 선택**이다. 둘 다 맞는 답이다.
- **조건에 맞는 행이 0개면 `COUNT` 는 0, `SUM`·`AVG` 는 `NULL`** — [21번](../21-aggregate-functions-count-forms/)의 규칙 그대로다.
- ★ **`NULL` 은 어느 조건에도 안 걸린다** — `hi`(2) + `lo`(1) 이 `total`(4)이 아니었다. `unknown` 계수기를 따로 둔다.
- **`WHERE` 와 `FILTER` 는 순서가 있다.** `WHERE` 로 좁히면 「전체」 열도 같이 좁아진다.

## 관련 자료

- [PostgreSQL 18 · Aggregate Expressions](https://www.postgresql.org/docs/18/sql-expressions.html) — `FILTER` 절의 문법과 *"other rows are discarded"* 문장.
- [MySQL 8.4 · Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html) — 집계 함수 문법에 **`FILTER` 가 없다.**
- [21 집계 함수와 COUNT 의 세 형태](../21-aggregate-functions-count-forms/) — **경계: 그쪽은 집계가 `NULL` 을 어떻게 다루나와 `AVG` 의 분모까지, 여기는 그 분모가 조건식으로 어떻게 오염되나부터.**
- [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) — 조건부 집계도 그룹 위에서 돈다.
- [23 GROUPING SETS·ROLLUP·CUBE](../23-grouping-sets-rollup-cube/) — **경계: 거기는 집계 수준을 행으로 쌓는 법, 여기는 조건을 열로 펴는 법.** 같은 요구의 두 방향이다.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `FILTER` 의 `WHERE` 안에서도 `UNKNOWN` 은 버려진다.
- [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/) — 「조건을 어느 칸에 두나」의 원형.
- **`CASE`·`COALESCE`·`NULLIF` 자체**는 [목록의 **6번 주제**](../06-conditional-expressions-case-coalesce/)가 정본이다 — 여기서는 **집계의 인자로 쓸 때**만 다룬다.
- [25 조인 팬아웃](../25-join-fan-out/) — 조건부 집계도 조인이 행을 늘리면 같이 부푼다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **조건부 집계(conditional aggregation)** — 한 번의 스캔으로 조건이 다른 여러 집계를 동시에 뽑는 것.\
  예: `total`·`hi`·`lo`·`unknown` 을 한 줄에 놓는 것.
- **`FILTER` 절** — 그 집계 함수 **하나에만** 걸리는 행 조건. PostgreSQL 전용.\
  예: `COUNT(*) FILTER (WHERE salary >= 400)` 은 2를 냈다.
- **`CASE` 식** — 조건에 따라 값을 고르는 식. `ELSE` 가 없으면 안 맞을 때 `NULL` 이다.\
  예: `CASE WHEN salary >= 400 THEN 1 END` 은 `ann` 에게 `NULL` 을 준다.
- **`ELSE 0` 함정** — 안 맞는 행에 0을 넣어 **집계의 입력에 합류시키는** 것.\
  예: `COUNT` 에 쓰면 0이 세어지고, `AVG` 에 쓰면 분모가 늘어난다.
- **분모 오염** — `AVG` 의 분모(`COUNT(열)`)에 뜻 없는 값이 들어가 평균이 바뀌는 것.\
  예: `AVG(CASE WHEN c THEN salary ELSE 0 END)` 이 500 대신 250 을 냈다.
- **모집단(population)** — 집계가 보는 행의 전체. `WHERE` 가 이것을 정한다.\
  예: `WHERE salary IS NOT NULL` 뒤에는 `COUNT(*)` 이 4가 아니라 3이다.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
  예: `NULL >= 400`. `FILTER` 도 `WHERE` 처럼 이것을 버린다 — 그래서 `hi + lo ≠ total` 이다.
- **`ERROR 1064`** — MySQL 의 문법 오류. **파서가 모르는 말**이라는 뜻이다.\
  예: `FILTER (WHERE …)`. 설정으로 켤 수 있는 것이 아니다.
- **피벗(pivot)** — 값을 행이 아니라 **열로** 펴서 가로 표를 만드는 것.\
  예: 부서를 행, 등급을 열로 놓고 칸마다 인원수를 세는 표.

## 더 들어가면

- **비율을 한 질의에 낼 때 정수 나눗셈에 걸린다.**\
  `COUNT(*) FILTER (…) / COUNT(*)` 은 PG 에서 정수끼리라 0이 되고 MySQL 은 `DECIMAL` 을 돌려준다 —\
  **두 엔진이 갈리는 자리**이고 [목록의 **36번 주제**](../36-numeric-types-and-functions/)가 정본이다. `* 1.0` 을 곱해 두는 것이 안전하다.
- **`FILTER` 는 윈도우 함수에도 붙는다**(PG). 다만 윈도우 자체는 목록의 [**26**](../26-window-functions-vs-aggregates/)~[**31**](../31-window-evaluation-timing/)번 주제이고 여기서는 다루지 않는다.
- **열이 많아지면 읽히지 않는다.** 조건이 열 스무 개가 되면 `GROUP BY` 로 행을 내고 앱에서 피벗하는 편이 낫다.\
  「행으로 낼까 열로 펼까」는 [23번](../23-grouping-sets-rollup-cube/)과 이 주제가 각각 한쪽을 맡는다.
- **성능은 재지 않았다.** 「조건부 집계가 질의 N번보다 빠르다」는 **스캔 횟수의 이야기**이지 측정 결과가 아니다.\
  실제 계획과 비용은 [목록의 **58번 주제**](../58-explain-plan-tree/)에서 읽는다.
