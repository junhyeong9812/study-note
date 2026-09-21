# sql/21-집계 함수와 `COUNT` 의 세 형태 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html) · [PG 18 Aggregate Expressions](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `COUNT` 세 형태 — (A) 4 / 3 / 2, (B) 4 / 3 / 3

**출력**

```text
### SQL: SELECT COUNT(*) AS c_star, COUNT(dept_id) AS c_col, COUNT(DISTINCT dept_id) AS c_dist FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c_star | c_col | c_dist         +--------+-------+--------+
--------+-------+--------        | c_star | c_col | c_dist |
      4 |     3 |      2         +--------+-------+--------+
(1 row)                          |      4 |     3 |      2 |
                                 +--------+-------+--------+
```

```text
### SQL: SELECT COUNT(*) AS c_star, COUNT(salary) AS c_col, COUNT(DISTINCT salary) AS c_dist FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c_star | c_col | c_dist         +--------+-------+--------+
--------+-------+--------        | c_star | c_col | c_dist |
      4 |     3 |      3         +--------+-------+--------+
(1 row)                          |      4 |     3 |      3 |
                                 +--------+-------+--------+
```

**왜 그런가**

```text
(A) dept_id = [10, 10, 20, NULL]        (B) salary = [300, 500, NULL, 400]
    COUNT(*)      -> 4                      COUNT(*)      -> 4
    COUNT(열)     -> 3   NULL 하나 뺌        COUNT(열)     -> 3   NULL 하나 뺌
    COUNT(DISTINCT) -> 2  10 이 둘 -> 하나    COUNT(DISTINCT) -> 3  뺄 중복이 없다
                          ^^^^^^^^^^^^^                             ^^^^^^^^^^^^^
```

★ **(B)에서 뒤의 둘이 같아진 것은 함수가 같아서가 아니라 데이터에 중복이 없어서다.**\
`salary` 의 남은 세 값 `300·500·400` 은 전부 다르므로 접을 게 없다.\
**「예전에 같은 답이 나왔으니 `COUNT(열)` 로 충분하다」가 사고의 시작이다** — `salary` 가 같은 사람이 하나만 들어와도 갈린다.

> **`COUNT(*)`** — **행**을 세는 형태. 인자의 값을 보지 않는다.\
> 예: `emp` 에서 4. `dept_id` 가 `NULL` 인 `dan` 도 한 행으로 센다.

> **`COUNT(DISTINCT 식)`** — `NULL` 을 버린 뒤 **서로 다른 값**의 가짓수를 세는 형태.\
> 예: `COUNT(DISTINCT dept_id)` 는 `10`·`20` 두 가지라 2다.

---

### 2. `COUNT(DISTINCT dept_id)` 가 2인 이유

**체가 둘이고, `NULL` 을 버리는 체가 먼저 온다.**

```text
입력 4행                  체 1: NULL 버리기        체 2: 중복 접기
+------------+            +------------+           +------------+
| 10         |            | 10         |           | 10         |
| 10         |  COUNT(*)  | 10         |           | 20         |
| 20         |  는 여기서 | 20         |           +------------+
| NULL       |  세고 끝    +------------+            -> 2
+------------+                -> 3
   -> 4        COUNT(열) 은 체 1 까지    COUNT(DISTINCT 열) 은 체 2 까지
```

★ **순서가 답을 정한다.** 중복을 먼저 접고 `NULL` 을 나중에 버렸다면 `[10, 20, NULL]` → `[10, 20]` 으로 **답은 같다**.\
하지만 **`NULL` 이 「한 가지 값」으로 세어지느냐**가 다르다 — 세 형태 어디에서도 `NULL` 은 한 가지로 세어지지 않는다.

**이 규칙은 `GROUP BY` 와 정반대다.**

```text
세기(COUNT DISTINCT)에서는         묶기(GROUP BY · DISTINCT)에서는
NULL  ->  아예 안 센다              NULL 끼리  ->  한 그룹이 된다
   -> COUNT(DISTINCT dept_id) = 2      -> GROUP BY dept_id 는 3그룹 (10 · 20 · NULL)
```

같은 열인데 하나는 2, 하나는 3이다. **「세기」와 「묶기」를 나눠서 외운다**([22번](../22-group-by-nonaggregated-columns/)·[04번](../04-null-three-valued-logic/)).

`NULL` 도 한 가지로 세고 싶으면 **실제 데이터에 없는 값**으로 채워야 한다.

```sql
SELECT COUNT(DISTINCT COALESCE(dept_id, -1)) FROM emp;   -- -1 이 실데이터에 있으면 조용히 틀린다
```

---

### 3. `COUNT(1)` · `COUNT('x')` · `COUNT(NULL)`

**출력**

```text
### SQL: SELECT COUNT(*) AS star, COUNT(1) AS one, COUNT('x') AS lit, COUNT(NULL) AS n FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 star | one | lit | n            +------+-----+-----+---+
------+-----+-----+---           | star | one | lit | n |
    4 |   4 |   4 | 0            +------+-----+-----+---+
(1 row)                          |    4 |   4 |   4 | 0 |
                                 +------+-----+-----+---+
```

**왜 그런가**

```text
COUNT(1)     매 행에서 1 을 평가한다 -> 전부 NULL 이 아니다 -> 4
COUNT('x')   매 행에서 'x' 를 평가한다 -> 전부 NULL 이 아니다 -> 4
COUNT(NULL)  매 행에서 NULL 을 평가한다 -> 전부 NULL 이다 -> 0
                                                            ^^^
                                         같은 규칙의 극단. 체 1 이 전부를 거른다
```

★ **셋 다 `COUNT(식)` 형태이고, 규칙은 하나뿐이다 — 「그 식이 `NULL` 이 아닌 행을 센다」.**\
`COUNT(1)` 이 `COUNT(*)` 과 답이 같은 것은 **우연이 아니라 1 이 절대 `NULL` 이 아니기 때문**이다.

**`COUNT(1)` 이 더 빠른가** — **이 주제에서 재지 않았다.** 속설은 적지 않는다.\
계획을 읽어 비교하는 법은 목록의 **58번 주제**, 스캔·집계 연산자는 **59번 주제**다.

---

### 4. `AVG(salary)` 는 400 — `1200` 을 **3**으로 나눈 것이다

**출력**

```text
### SQL: SELECT COUNT(*) AS c_star, COUNT(salary) AS c_col, SUM(salary) AS s, AVG(salary) AS a FROM emp;
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

**왜 그런가**

```text
       틀린 이해                        맞는 이해
 AVG = SUM / COUNT(*)              AVG = SUM / COUNT(열)
     = 1200 / 4 = 300                  = 1200 / 3 = 400
                                              ^
                            cho 는 급여가 NULL 이라 분자에도 분모에도 없다
```

★ **「평균 급여 400」은 「4명의 평균」이 아니라 「급여가 기록된 3명의 평균」이다.**\
PG 문서가 `avg` 를 *"the average (arithmetic mean) of all the non-null input values"* 라고 적는다 — **non-null 이 분모의 정의다.**

**이 사고는 숫자가 그럴듯해서 리뷰에서 안 잡힌다.** 300도 400도 「있을 법한 평균 급여」다.\
그래서 실무 규칙 한 줄 — **`AVG` 를 뽑을 때 `COUNT(*)` 과 `COUNT(열)` 을 같이 뽑아 분모를 눈으로 본다.**

소수 자릿수가 두 엔진에서 다른 것은 **결과 타입의 차이**다(PG `numeric` · MySQL `DECIMAL`). **값은 같다.**\
수치 타입은 [목록의 **36번 주제**](../36-numeric-types-and-functions/)다.

> **분모(denominator)** — `AVG` 가 합을 나누는 수. **`COUNT(열)` 이다.**\
> 예: `AVG(salary)` 는 `1200 / 3` 이라 400 이다.

---

### 5. 0행 집계 — `COUNT` 만 0이고 나머지는 전부 `NULL` 이다. 모순이 아니다

**출력**

```text
### SQL: SELECT COUNT(*) AS c, SUM(salary) AS s, AVG(salary) AS a, MIN(salary) AS mn, MAX(salary) AS mx
         FROM emp WHERE 1 = 0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c |  s   |  a   |  mn  |  mx    +---+------+------+------+------+
---+------+------+------+-----   | c | s    | a    | mn   | mx   |
 0 | NULL | NULL | NULL | NULL   +---+------+------+------+------+
(1 row)                          | 0 | NULL | NULL | NULL | NULL |
                                 +---+------+------+------+------+
```

**왜 그런가**

```text
      입력 0행
          |
   +------+------+
   |             |
COUNT(*)      SUM/AVG/MIN/MAX
"몇 개냐"      "얼마냐"
   |             |
   v             v
   0            NULL
 0 개는          더할 값이 없으면 합이 "0" 이 아니라
 답이 된다       "말할 수 없다" 이다
```

PG 문서가 이것을 못 박는다: *"except for `count`, these functions return a null value when no rows are selected. In particular, `sum` of no rows returns null, not zero as one might expect"*.\
MySQL 문서도 같다: *"If there are no matching rows, `SUM()` returns `NULL`."*

**모순이 아니라 서로 다른 질문의 답이다.** 「몇 건인가」에는 0이라는 답이 있고, 「합이 얼마인가」에는 답이 없다.

**행이 있어도 값이 전부 `NULL` 이면 결과가 같다** — 0행과 구분되지 않는다.

```text
### SQL: SELECT COUNT(*) AS c, COUNT(salary) AS cs, SUM(salary) AS s, AVG(salary) AS a
         FROM emp WHERE salary IS NULL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c | cs |  s   |  a              +---+----+------+------+
---+----+------+------           | c | cs | s    | a    |
 1 |  0 | NULL | NULL            +---+----+------+------+
(1 row)                          | 1 |  0 | NULL | NULL |
                                 +---+----+------+------+
```

`c`=1 인데 `s`=`NULL` 이다. **「행이 있다」와 「더할 값이 있다」가 다른 질문**이라는 뜻이고, 그 구분을 해 주는 것이 `COUNT(열)`(`cs`=0)이다.

> **빈 입력(no rows selected)** — 집계에 들어온 행이 하나도 없는 상태.\
> 예: `WHERE 1 = 0`. `COUNT`=0 이지만 나머지는 `NULL` 이다.

---

### 6. `GROUP BY` 를 붙이면 **0행**이 된다

**출력**

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp WHERE 1 = 0 GROUP BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c                     (아무 줄도 출력되지 않는다 — 빈 결과)
---------+---
(0 rows)
```

**왜 그런가**

```text
 GROUP BY 가 없을 때                  GROUP BY 가 있을 때
 +---------------------+              +---------------------+
 | 표 전체 = 한 그룹    |              | 그룹은 데이터가 만든다 |
 | 행이 0 개여도        |              | 행이 0 개면           |
 | 그룹은 1 개다        |              | 그룹도 0 개다         |
 +---------------------+              +---------------------+
   -> 결과 1행 (c = 0)                   -> 결과 0행
```

★ **`GROUP BY` 는 「있을 법한 그룹」을 만들어 주지 않는다. 실제로 들어온 행에서만 그룹을 만든다.**\
그래서 「사원이 0명인 부서」를 `HAVING COUNT(*) = 0` 으로 못 찾는다 — 그 그룹 자체가 없다([03번](../03-where-vs-having/)).\
없는 그룹을 표에 남기려면 **`dept` 를 보존 측으로 두는 외부 조인**이 필요하다([14번](../14-left-right-outer-join/)). 그게 7번이다.

MySQL 이 **아무 줄도 출력하지 않는 것**도 출력이다 — 헤더조차 없다. PG 는 헤더와 `(0 rows)` 를 찍는다.\
같은 「0행」을 두 클라이언트가 다르게 그리는 것이고, **결과는 같다.**

---

### 7. `dev` 는 1 / 1 / 0, `hr` 은 1 / 0 / 0

**출력**

```text
### SQL: SELECT d.name AS dept, COUNT(*) AS star, COUNT(e.id) AS emp_cnt, COUNT(e.salary) AS sal_cnt,
                SUM(e.salary) AS sum_sal
         FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name ORDER BY d.id;
--- PG 18.6 ---
 dept  | star | emp_cnt | sal_cnt | sum_sal
-------+------+---------+---------+---------
 sales |    2 |       2 |       2 |     800
 dev   |    1 |       1 |       0 |    NULL
 hr    |    1 |       0 |       0 |    NULL
(3 rows)
--- MySQL 8.4.10 ---
+-------+------+---------+---------+---------+
| dept  | star | emp_cnt | sal_cnt | sum_sal |
+-------+------+---------+---------+---------+
| sales |    2 |       2 |       2 |     800 |
| dev   |    1 |       1 |       0 |    NULL |
| hr    |    1 |       0 |       0 |    NULL |
+-------+------+---------+---------+---------+
```

**왜 그런가**

```text
 dev 그룹의 1행                        hr 그룹의 1행
+---------------------------+         +---------------------------+
| d.name = dev              |         | d.name = hr               |
| e.id   = 3      <- 실제 값 |         | e.id   = NULL  <- 조인 산물|
| e.salary = NULL <- 데이터 |         | e.salary = NULL <- 조인 산물|
+---------------------------+         +---------------------------+
  사원 cho 가 있다.                      사원이 없다.
  급여만 기록이 없다.                     조인이 만든 빈 행 하나가 있을 뿐이다
```

| | `star` | `emp_cnt` | `sal_cnt` | 무슨 뜻인가 |
|---|---|---|---|---|
| `dev` | 1 | **1** | 0 | 사원이 **있다**(`cho`). 급여만 기록이 없다 |
| `hr` | 1 | **0** | 0 | 사원이 **없다**. 세어진 1은 조인이 만든 행이다 |

★ **`COUNT(*)` 만 보면 두 행이 똑같이 1이다.** 세 열을 나란히 뽑아야 갈린다.\
[14번](../14-left-right-outer-join/)이 `hr` 의 `COUNT(*)`=1 을 함정으로 들었고, **`sal_cnt` 를 더해 `dev` 와 갈라 놓은 것이 이 주제의 몫**이다.

`sum_sal` 도 보라 — `dev` 와 `hr` 이 **둘 다 `NULL`** 이다. 「합계가 없다」와 「사원이 없다」가 여기서도 뭉친다(5번).

---

### 8. 「사원 수」는 **상대 측의 `NULL` 일 수 없는 열**을 센다

**보통 기본키다.** 조건은 한 줄이다 — **원본 데이터에 `NULL` 이 절대 없는 열**이어야 한다.

```text
 왜 e.id 인가
 emp.id 는 기본키다 -> 원본에 NULL 이 없다
      그러므로 결과에서 e.id 가 NULL 이면
      그건 "데이터가 NULL" 이 아니라 "조인이 채운 NULL" 이다
      -> 짝을 못 찾은 행이다 -> 세지 않는다 -> 0
```

```text
 쓰면 안 되는 열               왜
 COUNT(*)                     조인이 만든 행까지 센다 -> hr 이 1
 COUNT(e.salary)              cho 처럼 값이 없는 사원을 빠뜨린다 -> dev 가 0
 COUNT(e.name)                emp.name 이 NOT NULL 이면 되지만,
                              제약이 풀리는 순간 조용히 틀린다
```

★ **`COUNT(e.salary)` 를 쓰면 `dev` 가 0명이 된다** — 사원은 있는데 급여가 없을 뿐인데.\
이것이 [14번](../14-left-right-outer-join/)의 「짝 여부는 기본키로 판정한다」가 집계에서 되풀이되는 자리다.

> **조인이 만든 `NULL`(join-generated NULL)** — 원본에 없었는데 외부 조인이 채워 넣은 `NULL`.\
> 예: `hr` 행의 `e.id`. `emp.id` 는 기본키라 원본에는 `NULL` 이 없다.

---

### 9. `COALESCE(SUM(e.salary), 0)` 을 쓴다

**출력**

```text
### SQL: SELECT d.name AS dept, COALESCE(SUM(e.salary), 0) AS payroll, SUM(COALESCE(e.salary, 0)) AS payroll2
         FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | payroll | payroll2      +-------+---------+----------+
-------+---------+----------     | dept  | payroll | payroll2 |
 sales |     800 |      800      +-------+---------+----------+
 dev   |       0 |        0      | sales |     800 |      800 |
 hr    |       0 |        0      | dev   |       0 |        0 |
(3 rows)                         | hr    |       0 |        0 |
                                 +-------+---------+----------+
```

**왜 그런가**

```text
 바깥에 두기                          안쪽에 두기
 COALESCE(SUM(salary), 0)             SUM(COALESCE(salary, 0))
 "합이 없으면 0 이라고 쓰자"            "없는 급여를 0 원으로 치고 더하자"
        |                                    |
   SUM 은 그대로 NULL 을 건너뛴다        NULL 이 0 이 되어 계산에 합류한다
        |                                    |
   SUM 에서는 답이 같다                 SUM 에서는 답이 같다
                                              |
                                        AVG 로 바꾸면 갈린다
```

★ **`SUM` 에서는 두 형태가 같은 답을 내지만 `AVG` 에서는 갈린다.**\
`AVG(COALESCE(salary,0))` 은 **`NULL` 을 0으로 분모에 합류시켜** 평균을 끌어내린다.\
그 대비는 [24번](../24-conditional-aggregation-filter-case/)이 정본이다 — 거기서 `AVG` 가 400 과 200 으로 갈리는 실측을 본다.

**표현의 문제이지 집계의 문제가 아니다.** `COALESCE`·`NULLIF`·`CASE` 는 [목록의 **6번 주제**](../06-conditional-expressions-case-coalesce/)가 정본이다.

---

### 10. 안 돈다 — 두 엔진 모두 거부한다. 파생 테이블로 감싼다

**출력**

```text
### SQL: SELECT COUNT(COUNT(*)) FROM emp GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  aggregate function calls cannot be nested
LINE 1: SELECT COUNT(COUNT(*)) FROM emp GROUP BY dept_id;
                     ^
--- MySQL 8.4.10 ---
ERROR 1111 (HY000) at line 1: Invalid use of group function
```

```text
### SQL: SELECT SUM(AVG(salary)) FROM emp;
--- PG 18.6 ---
ERROR:  aggregate function calls cannot be nested
LINE 1: SELECT SUM(AVG(salary)) FROM emp;
                   ^
--- MySQL 8.4.10 ---
ERROR 1111 (HY000) at line 1: Invalid use of group function
```

**왜 그런가**

```text
 집계의 입력은 "행" 이다
 +--------+        +----------+        +--------+
 |  행들  | -----> |   집계   | -----> |  값 1개 |
 +--------+        +----------+        +--------+
                                            |
                        이 값을 다시 집계에 넣으려면
                        "행" 으로 되돌려야 한다 -> 한 겹 감싸는 이유
```

**고치는 법 — 1단계 집계를 파생 테이블로 만들고 그 위에 2단계를 얹는다**([10번](../10-from-clause-aliases-derived-tables/)).

```sql
SELECT AVG(c) FROM (SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY dept_id) t;
```

같은 이유로 `GROUP BY` 에도 집계를 못 쓴다.

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY COUNT(*);
--- PG 18.6 ---
ERROR:  aggregate functions are not allowed in GROUP BY
LINE 1: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY COUNT(*);
                                                        ^
--- MySQL 8.4.10 ---
ERROR 1056 (42000) at line 1: Can't group on 'c'
```

★ **뿌리는 [01번](../01-logical-query-processing-order/)의 처리 순서다** — 집계는 `GROUP BY` 가 그룹을 만든 **뒤**에 계산되므로, `GROUP BY` 자신이 그 결과를 입력으로 받을 수 없다.

**두 엔진의 메시지 성격이 다르다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 중첩 집계 | `aggregate function calls cannot be nested` — **무엇이 문제인지 말한다** | `ERROR 1111 Invalid use of group function` — **자리를 잘못 쓴 모든 집계에 붙는 한 덩어리** |
| `GROUP BY` 에 집계 | `aggregate functions are not allowed in GROUP BY` | `ERROR 1056 Can't group on 'c'` — **별칭 `c`** 로 가리킨다 |

MySQL 이 `'c'` 라는 **출력 열 별칭**을 부르는 데 주목하라 — MySQL 은 `GROUP BY`·`HAVING` 에서 출력 열 이름을 먼저 찾는다([03번](../03-where-vs-having/)).\
**거부한다는 사실은 같다.** 방언 차이가 아니라 메시지 차이다.

> **중첩 집계(nested aggregate)** — 집계 함수의 인자로 다른 집계를 쓰는 것.\
> 예: `AVG(COUNT(*))`. 두 엔진 모두 에러이고 파생 테이블로 푼다.

---

### 11. ★ 서로의 문법을 정확히 거부하고, 돌아가는 쪽끼리도 답이 다르다

**출력**

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
--- PG 18.6 ---
 c
---
 4
(1 row)
--- MySQL 8.4.10 ---
ERROR 1241 (21000) at line 1: Operand should contain 1 column(s)
```

**왜 그런가**

| | (A) `COUNT(DISTINCT a, b)` | (B) `COUNT(DISTINCT (a, b))` |
|---|---|---|
| PostgreSQL 18.6 | **에러** — `function count(integer, integer) does not exist` | **4** |
| MySQL 8.4.10 | **2** | **에러** — `Operand should contain 1 column(s)` |

```text
입력 (dept_id, salary) 네 쌍
 (10, 300)   (10, 500)   (20, NULL)   (NULL, 400)

MySQL  COUNT(DISTINCT dept_id, salary) -> 2
       "한 칸이라도 NULL 인 행은 세지 않는다"
       (20,NULL) 과 (NULL,400) 을 버리고 남은 둘이 서로 달라서 2

PG     COUNT(DISTINCT (dept_id, salary)) -> 4
       괄호가 "행 값" 하나를 만든다. 그 행 값 자체는 NULL 이 아니다
       넷 다 세고, 넷이 서로 달라서 4
```

MySQL 문서가 그대로 적는다: *"Returns a count of the number of rows with different non-`NULL` expr values."*\
**「한 칸이라도 `NULL` 이면 그 행은 없는 셈」**이 이 형태의 규칙이다.

PG 쪽은 인자가 **하나**다 — `(dept_id, salary)` 라는 합성 값이다. 그래서 `COUNT(DISTINCT 한 값)` 의 규칙이 그대로 적용되고, **행 값은 `NULL` 이 아니므로** 체 1에 안 걸린다.

★ **목록 README 의 21번 방언 칸이 `표준` 이었는데 이 자리 때문에 `차이` 로 정정했다.** 근거는 위 두 에러와 2 대 4다.

> **행 값(row value)** — 괄호로 여러 열을 묶어 만든 한 개의 합성 값.\
> 예: PG 의 `(dept_id, salary)`. 안쪽에 `NULL` 이 있어도 합성 값 자체는 `NULL` 이 아니다.

---

### 12. 파생 테이블에서 `DISTINCT` 를 먼저 하고 `COUNT(*)` 을 센다

**출력**

```sql
SELECT COUNT(*) FROM (SELECT DISTINCT dept_id, salary FROM emp) t;
```

```text
### SQL: SELECT COUNT(*) AS c FROM (SELECT DISTINCT dept_id, salary FROM emp) t;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c                               +---+
---                              | c |
 4                               +---+
(1 row)                          | 4 |
                                 +---+
```

**왜 그런가**

```text
 COUNT(DISTINCT ...) 를 쓰면            DISTINCT 를 안쪽으로 내리면
 "NULL 을 어떻게 볼 것인가" 가          SELECT DISTINCT 는 묶기 규칙을 쓴다
 엔진마다 다르다 (2 vs 4)                -> NULL 끼리 한 값으로 본다
                                         -> 두 엔진이 같은 4 를 낸다
```

★ **이식성의 값은 「같은 문법이 돈다」가 아니라 「같은 답이 나온다」다.**\
(A)를 고쳐 (B)로 옮겨 적는 것만으로는 2가 4가 되어 **조용히 값이 바뀐다.**

**문자열로 이어 붙이지 마라** — `CONCAT(dept_id, '|', salary)` 류는 두 가지를 동시에 깨뜨린다.\
`NULL` 이 섞이면 결과 전체가 `NULL` 이 되거나(PG 의 `||`) 구분자가 값에 들어 있으면 서로 다른 조합이 같아진다.\
문자열 연결의 방언은 [목록의 **37번 주제**](../37-string-functions-and-concatenation/)다.

파생 테이블에 **별칭 `t` 가 붙어 있는 것**에 주목하라 — MySQL 은 별칭이 **필수**이고 PG 는 없어도 통과한다([10번](../10-from-clause-aliases-derived-tables/)).

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `COUNT` 세 형태 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `dept_id`·`salary` 두 열로 |
| `COUNT(1)`·`COUNT(NULL)` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `SUM`·`AVG` 의 분모 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `MIN`/`MAX` 까지 같이 |
| 0행·전부 `NULL` 집계 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `WHERE 1=0` · `WHERE salary IS NULL` |
| `GROUP BY` 의 0그룹 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | MySQL 은 **아무 줄도 출력 안 함** |
| `hr` 대 `dev` (7·8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 다섯 열을 한 질의에 |
| `COALESCE` 두 위치 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `SUM` 에서는 같은 답 |
| 중첩 집계·`GROUP BY` 집계 (10번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **전부 에러 — 메시지를 그대로 실었다** |
| `COUNT(DISTINCT a, b)` (11·12번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **서로를 거부** + 2 대 4 + 파생 테이블 4 |

**구현 의존 항목** — `AVG` 결과의 소수 자릿수(PG `numeric` · MySQL `DECIMAL`)와 `COUNT` 의 반환 타입(PG 는 `pg_typeof` 로 `bigint` 확인).\
**값은 두 엔진에서 같았다.**

**방언 항목** — **11번 하나다.** `COUNT(DISTINCT 열1, 열2)` 는 문법도 결과도 갈린다.\
**언어 보장 항목** — 1~10·12번. 세 `COUNT` 형태의 정의, `NULL` 건너뛰기, 0행 규칙, 중첩 금지는 두 문서가 같은 모양으로 적는다.

**버전** — 이 주제에서 버전에 갈리는 것은 없다. 다음 버전에서도 **11번만 다시 확인하면 된다.**\
**재지 않은 것** — `COUNT(1)` 대 `COUNT(*)` 의 속도, `COUNT(DISTINCT)` 의 비용. **측정하지 않았으므로 적지 않았다.**
