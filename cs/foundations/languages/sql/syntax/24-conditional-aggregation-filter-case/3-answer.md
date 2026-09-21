# sql/24-조건부 집계 — `FILTER` 와 `CASE` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 Aggregate Expressions](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `WHERE` 는 **모든 열에 같이** 걸리기 때문이다

```text
FROM ──> WHERE ──> GROUP BY ──> SELECT
           ^
   여기를 지난 행은 "모든 열에 대해" 같은 행이다
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

```text
 WHERE 로 세기 (3 번 훑는다)          조건부 집계 (1 번 훑는다)
 +---------------------------+       +-----------------------------------+
 | 질의 3 개                  |       | 질의 1 개                         |
 | 답이 따로따로              |  ──>  | 한 줄에 열로 나란히               |
 | 앱에서 합쳐야 한다         |       | total 과의 관계가 눈에 보인다     |
 +---------------------------+       +-----------------------------------+
```

★ **`WHERE` 를 쓰지 말라는 뜻이 아니다.** 「전부 이 조건 안의 이야기」면 `WHERE` 가 맞고 **더 싸다** — 인덱스로 행을 아예 안 읽을 수 있다.\
조건부 집계는 **같은 모집단을 여러 각도로 쪼갤 때**다.

---

### 2. `total`=4 · `hi`=2 · `lo`=1 · `unknown`=1 — **`hi + lo` 는 `total` 이 아니다**

**출력**

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

**왜 그런가**

```text
 salary = [300, 500, NULL, 400]

 salary >= 400  ->  FALSE TRUE  UNKNOWN TRUE   -> 2 개
 salary <  400  ->  TRUE  FALSE UNKNOWN FALSE  -> 1 개
                                 ^^^^^^^
                    NULL 은 양쪽 어디에도 안 들어간다
                    2 + 1 = 3 != 4
```

★ **`FILTER` 의 `WHERE` 도 `TRUE` 인 행만 통과시킨다** — `FALSE` 와 `UNKNOWN` 을 **같이 버린다.**\
[04번](../04-null-three-valued-logic/)의 3값 논리가 집계 인자 자리에서 그대로 작동한다.

```text
 실무 습관
 +--------------------------------------------------+
 | unknown 계수기를 따로 둔다                        |
 |   -> hi + lo + unknown == total 을 눈으로 검산    |
 |   -> 안 맞으면 조건이 겹치거나 빠진 것이다         |
 +--------------------------------------------------+
```

`in10`=2 는 다른 열(`dept_id`)로 건 조건이다 — **계수기마다 조건 열이 달라도 된다.** `WHERE` 로는 못 하는 일이다.

> **`FILTER` 절** — 그 집계 함수 하나에만 걸리는 행 조건.\
> 예: `COUNT(*) FILTER (WHERE salary >= 400)` 은 2를 냈다.

---

### 3. `ERROR 1064` 다 — **문법 자체가 없고 설정으로 켤 수 없다**

**출력**

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

**왜 그런가**

★ **에러가 `FILTER` 가 아니라 그 다음의 `(WHERE …` 에서 났다.**\
MySQL 파서는 `FILTER` 를 **평범한 식별자**로 읽었고, 괄호가 나오자 말이 안 된다고 판단했다.\
MySQL 8.4 매뉴얼의 집계 함수 문법에도 `FILTER` 절이 **없다** — `[over_clause]` 만 있다.

```text
 "없다" 에도 종류가 있다
 +------------------------------+   +------------------------------+
 | ERROR 1064  (여기)            |   | ERROR 3889  (23번 CUBE)      |
 | 파서가 모르는 말이다          |   | 파서는 안다                  |
 | 어떤 설정으로도 못 켠다       |   | 실행할 엔진이 없을 뿐이다     |
 +------------------------------+   +------------------------------+
```

★ **[23번](../23-grouping-sets-rollup-cube/)의 `CUBE` 와 대비하라** — **에러 번호가 「없음의 종류」를 말해 준다.**\
「미지원」이라 적기 전에 던져 보면 **어떤 미지원인지**를 알 수 있다.

---

### 4. `dept_id=10` 은 **1 / 1 / 1 / 2**, `dept_id=20` 은 **0 / NULL / 0 / 1**

**출력**

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

**왜 그런가**

```text
 dept_id=10  salary = [300, 500]        dept_id=20  salary = [NULL]

 CASE ... THEN 1 ELSE 0 END -> [0, 1]     -> [0]
 CASE ... THEN 1       END  -> [NULL, 1]  -> [NULL]

 SUM([0,1])      = 1                       SUM([0])      = 0
 SUM([NULL,1])   = 1                       SUM([NULL])   = NULL   <- 더할 값이 없다
 COUNT([NULL,1]) = 1                       COUNT([NULL]) = 0
 COUNT([0,1])    = 2   <- 0 도 센다        COUNT([0])    = 1      <- 0 도 센다
```

**갈리는 자리가 둘이다.**

| 자리 | 무엇이 갈렸나 | 왜 |
|---|---|---|
| `dept_id=20` | `sum_else0`=**0** 대 `sum_noelse`=**NULL** | 맞는 행 0개 → `SUM` 의 입력이 빈 것 → `NULL`([21번](../21-aggregate-functions-count-forms/)) |
| `dept_id=10` | `cnt_case`=**1** 대 `cnt_case_else0`=**2** | `ELSE 0` 이 만든 0이 `NULL` 이 아니라서 세어졌다 |

★ **두 엔진의 숫자가 한 자리도 안 갈렸다.** 이것은 방언이 아니라 **`CASE` 와 집계의 정의**다.

---

### 5. **0은 `NULL` 이 아니라서 `COUNT` 가 센다** — 결과가 `COUNT(*)` 이 된다

```text
 COUNT 의 규칙: 인자가 NULL 이 아닌 행을 센다

 CASE WHEN c THEN 1 ELSE 0 END
      조건이 맞으면 1, 아니면 0
      -> 어느 쪽이든 NULL 이 아니다
      -> 모든 행이 세어진다
      -> COUNT(*) 과 똑같아진다.  조건이 통째로 무의미하다
```

**증거는 4번 출력에 있다** — `cnt_case_else0` 가 그룹별로 **2 / 1 / 1** 이고, 이는 각 그룹의 `COUNT(*)` 과 같다.

```text
 dept_id | 그룹 인원 | cnt_case_else0 | 같은가
---------+-----------+----------------+--------
      10 |         2 |              2 | 같다
      20 |         1 |              1 | 같다
    NULL |         1 |              1 | 같다
```

★ **규칙 한 줄: `COUNT` 에 `ELSE` 를 절대 붙이지 않는다.**\
개수를 세는 방법은 둘뿐이다.

```sql
COUNT(CASE WHEN c THEN 1 END)          -- NULL 로 빠뜨려 안 세게 한다
SUM  (CASE WHEN c THEN 1 ELSE 0 END)   -- 0 을 더해 안 늘게 한다
```

★ **둘의 차이는 「맞는 행이 0개일 때」 하나뿐이다** — 앞은 **0**, 뒤도 **0**.\
`SUM(CASE WHEN c THEN 1 END)`(`ELSE` 없는 `SUM`)만 **`NULL`** 이다. 셋을 헷갈리지 않으려면 **`COUNT` + `ELSE` 없음**으로 고정한다.

---

### 6. `a_noelse`=**500**, `a_else0`=**250** — 분모가 달라졌다

**출력**

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

**왜 그런가**

```text
 dept_id=10  salary = [300, 500],  조건 salary >= 400

 CASE ... THEN salary END        -> [NULL, 500]
     AVG 의 분모 = COUNT(열) = 1  -> 500 / 1 = 500     "400 이상인 사람들의 평균"
 CASE ... THEN salary ELSE 0 END -> [0, 500]
     AVG 의 분모 = COUNT(열) = 2  -> 500 / 2 = 250     "0 원을 받는 사람을 끼워 넣은 평균"
```

★★ **`ELSE 0` 은 「없는 사람」을 「0원 받는 사람」으로 바꾼다.** 그 사람이 분모에 들어간다.\
[21번](../21-aggregate-functions-count-forms/)의 「`AVG` 의 분모는 `COUNT(열)` 이다」가 여기서 값을 바꾼 것이다.

**이 사고가 위험한 이유는 250 도 「있을 법한 평균」이라서다.** 숫자만 보면 아무도 못 잡는다.

```text
 규칙 고정
 +------------------------------------------+
 | AVG 에 ELSE 는 없다                       |
 | SUM 에는 뜻을 골라서 쓴다 (7번)           |
 | COUNT 에는 절대 안 쓴다 (5번)             |
 +------------------------------------------+
```

---

### 7. **`SUM` 은 0을 더해도 합이 안 바뀌고, `AVG` 는 분모가 늘어난다**

```text
 SUM 에서                          AVG 에서
 +---------------------------+     +---------------------------+
 | 0 을 더해도 합은 그대로    |     | 0 도 "값 하나" 라          |
 | 500 + 0 = 500             |     | 분모가 1 -> 2 로 늘어난다  |
 +---------------------------+     +---------------------------+
   두 형태가 같은 답 (500·500)       두 형태가 다른 답 (500·250)
```

**6번 출력의 `s_noelse`·`s_else0` 가 그 증거다** — `dept_id=10` 에서 **둘 다 500** 이다.

★ **그래서 `SUM` 에서 `ELSE 0` 을 쓰는 습관이 생기고, 그 습관이 `AVG` 로 옮겨 가 사고가 난다.**\
「`SUM` 에서 아무 문제 없었으니 `AVG` 에서도 괜찮겠지」가 정확히 틀린 추론이다.

**단 `SUM` 에서도 한 자리는 갈린다 — 맞는 행이 0개인 그룹이다.**

```text
 dept_id=20
 s_noelse = NULL     "더할 값이 하나도 없다"
 s_else0  = 0        "0 원짜리를 하나 더했다"
```

★ **둘 다 맞는 답이고 뜻이 다르다.** 「집계할 대상이 없었다」를 보이고 싶으면 `NULL`,\
「합계는 0원이다」를 보이고 싶으면 `ELSE 0` 이다. **고르는 것이지 옳고 그름이 아니다.**

---

### 8. `COUNT(*) FILTER` 는 **0**, `SUM(salary) FILTER` 는 **`NULL`**

**출력**

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

**왜 그런가**

```text
 dept_id=20 그룹에 FILTER 를 건다
   원래 행 1 개 (cho, salary=NULL)
        |
   FILTER (WHERE salary >= 400)  ->  NULL >= 400 은 UNKNOWN -> 버린다
        |
   그 집계의 입력은 0 행
        |
   +----+----------------+
   |    |                |
 COUNT            SUM / AVG / MIN / MAX
   0                   NULL
```

★ **새 규칙이 아니다.** [21번](../21-aggregate-functions-count-forms/)의 「빈 입력에서 `COUNT` 만 0이고 나머지는 `NULL`」이 그대로다.\
`FILTER` 는 **그 집계의 입력 행을 0으로 만드는** 방법이고, 그다음은 이미 아는 규칙이다.

```text
 "조건에 맞는 게 없다" 를 어떻게 보일까
 +--------------------------------------------------+
 | 건수  -> 0 이 자연스럽다.  COUNT 가 그렇게 한다   |
 | 합계  -> NULL 이 기본.  0 으로 보이려면          |
 |          COALESCE(SUM(...) , 0) 을 쓴다          |
 +--------------------------------------------------+
```

**`c`=1 인데 `hi`=0 인 것**에 주목하라 — 그룹에 행은 있고 **조건에 맞는 행만 없다.**\
[21번](../21-aggregate-functions-count-forms/)의 `hr`(그룹에 행이 아예 없음)과는 다른 상황이고, **보이는 숫자는 비슷하다.**

---

### 9. **`FILTER (WHERE c)` 를 인자 자리의 `CASE WHEN c THEN … END` 로 옮긴다. `ELSE` 는 붙이지 않는다**

```text
COUNT(*)    FILTER (WHERE c)   ==  COUNT(CASE WHEN c THEN 1 END)
COUNT(열)   FILTER (WHERE c)   ==  COUNT(CASE WHEN c THEN 열 END)
SUM(열)     FILTER (WHERE c)   ==  SUM(CASE WHEN c THEN 열 END)
AVG(열)     FILTER (WHERE c)   ==  AVG(CASE WHEN c THEN 열 END)
COUNT(DISTINCT 열) FILTER (WHERE c) == COUNT(DISTINCT CASE WHEN c THEN 열 END)
                                                ^^^^^^^^^^^^^^^^^^^^^^^
                                            ELSE 는 절대 붙이지 않는다
```

**출력 — 열마다 대조했다**

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

★ **세 쌍이 열마다 한 글자도 같다. `NULL` 인 자리까지 같다.**\
**이식은 기계적이다** — 형태만 옮기면 값이 안 바뀐다. **단 `ELSE` 를 끼워 넣는 순간 4·6번의 사고가 난다.**

```text
 이식할 때 실수가 나는 지점
 FILTER (WHERE c)  ->  CASE WHEN c THEN 1 ELSE 0 END   <- 틀렸다 (COUNT 이면)
 FILTER (WHERE c)  ->  CASE WHEN c THEN 1 END          <- 맞다
```

---

### 10. **읽히기 때문이다** — 무엇을 세는지가 앞에 있다

```text
 FILTER 형태                          CASE 형태
 COUNT(*) FILTER (WHERE salary>=400)  COUNT(CASE WHEN salary>=400 THEN 1 END)
   ^^^^^^^^        ^^^^^^^^^^^^^^^      ^^^^^^          ^^^^^^^^^^^^^^^  ^^^^^^
   "행을 센다"      "이 조건으로"        "센다"           "이 조건"      THEN 1 ???
                                                                          |
                                              읽는 사람이 "1 이 무슨 뜻이지" 를
                                              한 번 해석해야 한다
```

- **`THEN 1` 은 의미 없는 값이다.** 세기 위한 더미일 뿐인데 코드에는 값처럼 보인다.
- **조건이 길어질수록 차이가 커진다.** `CASE` 형태는 조건이 괄호 안쪽 깊이 묻힌다.
- **`ELSE` 를 잘못 넣을 자리가 아예 없다.** `FILTER` 에는 `ELSE` 가 없다 — **4·6번의 사고가 구조적으로 불가능하다.**

★ **그래서 「PG 전용이라도 `FILTER` 를 쓴다」가 합리적인 선택이 된다** — 단 **이식할 일이 없을 때**다.

```text
 고르는 기준
 +--------------------------------------------------+
 | PG 만 쓴다            -> FILTER                   |
 | 두 엔진을 다 지원한다 -> 처음부터 CASE 로 통일     |
 | 섞어 쓰지 않는다 — 한 코드베이스에 두 형태가      |
 |   섞이면 리뷰에서 ELSE 실수를 못 잡는다            |
 +--------------------------------------------------+
```

---

### 11. `all_rows`=**3**, `d10`=**2**

**출력**

```text
### SQL: SELECT COUNT(*) AS all_rows, COUNT(*) FILTER (WHERE dept_id = 10) AS d10
         FROM emp WHERE salary IS NOT NULL;
--- PG 18.6 ---
 all_rows | d10
----------+-----
        3 |   2
(1 row)
```

**왜 그런가**

```text
 emp 4행
   |
   WHERE salary IS NOT NULL   -> ann bob dan (3행)     <- all_rows = 3   (4 가 아니다)
   |
   FILTER (WHERE dept_id=10)  -> ann bob    (2행)      <- d10 = 2
```

```text
FROM ──> WHERE ──> GROUP BY ──> 집계 계산 (여기서 FILTER 가 걸린다)
           ^                            ^
   모든 계수기의 공통 모집단      계수기마다 추가로 거른다
```

★ **`WHERE` 를 좁히면 「전체」라고 이름 붙인 열도 같이 좁아진다.**\
`all_rows` 가 4가 아니라 3인 것이 그것이다 — `cho` 는 **어느 계수기에도 도달하지 못했다.**

**그래서 `total` 열을 같이 뽑아 두는 습관이 값을 한다.** 이름과 값이 어긋나는 것이 바로 보인다.

★ **`WHERE` 가 싼 이유도 여기 있다** — 행을 아예 안 읽을 수 있다(인덱스). `FILTER`·`CASE` 는 **읽은 뒤에** 판정한다.\
인덱스를 타고 안 타고는 목록의 **47번 주제**다. **여기서는 재지 않았다.**

---

### 12. **조건이 런타임에 정해질 때**와 **조건 수가 아주 많을 때**

```text
 (가) 조건이 런타임에 정해진다
 +--------------------------------------------------+
 | 열 이름이 질의문에 박혀 있다                      |
 |   -> 조건도 질의문에 박혀 있어야 한다             |
 |   -> 사용자가 고르는 구간에는 못 쓴다             |
 | 대신: GROUP BY 로 행을 내고 앱에서 피벗한다        |
 +--------------------------------------------------+

 (나) 조건 수가 아주 많다
 +--------------------------------------------------+
 | 열이 스무 개가 되면 질의가 안 읽힌다              |
 | 리뷰에서 ELSE 실수를 못 잡는다                    |
 | 대신: 23번처럼 행으로 내거나 GROUP BY 로 편다      |
 +--------------------------------------------------+
```

**세 번째로 흔한 것 — 「전부 한 조건 안의 이야기」일 때.**

```text
 "지난달 매출만 본다"
   -> 조건부 집계로 쓸 이유가 없다
   -> WHERE 로 좁히는 게 맞고 더 싸다 (11번)
```

★ **판단 기준 한 줄: 「이 조건 밖의 행도 결과에 쓰이나?」**\
`total` 이나 다른 구간과 **비교해야 하면** 조건부 집계, **안 쓰면** `WHERE` 다.

**「행으로 낼까 열로 펼까」**는 [23번](../23-grouping-sets-rollup-cube/)과 이 주제가 각각 한쪽을 맡는다.

```text
 23번 (ROLLUP)                       24번 (FILTER · CASE)
 +---------------------------+       +---------------------------+
 | 집계 수준을 행으로 쌓는다  |       | 조건을 열로 편다          |
 | 수준이 늘어도 질의가 짧다  |       | 조건이 늘면 질의가 길어진다|
 | NULL 함정이 있다 (GROUPING)|       | ELSE 함정이 있다          |
 +---------------------------+       +---------------------------+
```

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `WHERE` 로 나눠 세기 (1번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 세 조건을 각각 |
| `FILTER` 계수기 다섯 (2번) | PG 18.6 | 1회 | `hi + lo != total` 확인 |
| ★ `FILTER` 를 MySQL 에 (3번) | MySQL 8.4.10 | 2회 | **`ERROR 1064` — 두 형태 모두** |
| ★ 네 `CASE` 형태 (4·5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 숫자가 전부 같음** |
| ★ `AVG` 의 `ELSE 0` (6·7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **500 대 250** |
| 맞는 행 0개인 그룹 (8번) | PG 18.6 | 1회 | `hi`=0 · `hi_sum`=`NULL` |
| ★ `FILTER` ≡ `CASE` 대조 (9번) | PG 18.6 | 2회 | 6열 대조 + `DISTINCT` 대조 |
| `WHERE` + `FILTER` (11번) | PG 18.6 | 1회 | `all_rows`=3 |

**구현 의존 항목** — `AVG` 결과의 소수 자릿수(PG `numeric` · MySQL `DECIMAL`). **값은 같다.**\
**방언 항목** — **`FILTER` 의 존재 여부 하나다.** `CASE` 형태는 두 엔진에서 숫자가 한 자리도 안 갈렸다.\
**언어 보장 항목** — 1·2·4~9·11번. `FILTER` 의 의미, `CASE` 의 `ELSE` 규칙, 빈 입력 규칙은 문서에 있다.

**버전** — `FILTER` 의 PG 도입 버전은 **매뉴얼에서 확인하지 못해 적지 않았다.**\
**재지 않은 것** — 「조건부 집계가 질의 N번보다 빠른가」. **스캔 횟수의 이야기이지 측정이 아니다.**\
다음 버전에서 다시 볼 것 — **3번(MySQL 에 `FILTER` 가 생겼는지)**이다.
