# sql/21-집계 함수와 `COUNT` 의 세 형태 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html) · [PostgreSQL 18 · Aggregate Expressions](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 · Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `COUNT`·`SUM`·`AVG`·`MIN`·`MAX` 와 `DISTINCT` 는 두 엔진 모두 오래전부터 있다.\
> 갈리는 자리는 **`COUNT(DISTINCT 열1, 열2)` 하나**다(아래 6번) — 서로의 문법을 정확히 거부한다.\
> **선행** — [04 NULL 의 3값 논리](../04-null-three-valued-logic/). **집계 함수가 `NULL` 을 다루는 방식이 이 주제의 전부다.**\
> **뒤 주제** — [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) · [24 조건부 집계](../24-conditional-aggregation-filter-case/) · [25 조인 팬아웃](../25-join-fan-out/).

## 한눈에 — 쉽게 말하면

**설문지를 상자에 모아 놓고 「몇 장인가」를 묻는 방법이 셋인데, 셋이 서로 다른 답을 낸다.**

- 「**몇 장 걷혔나**」 — 백지든 뭐든 종이 장수를 센다. 이게 `COUNT(*)` 이다.
- 「**그 칸에 뭐라도 적힌 게 몇 장인가**」 — 빈칸으로 낸 사람은 안 센다. 이게 `COUNT(열)` 이다.
- 「**적힌 답이 몇 가지인가**」 — 같은 답을 쓴 사람은 한 번만 센다. 이게 `COUNT(DISTINCT 열)` 이다.

| 비유 | 실체 | `emp.dept_id` 로 세면 |
|---|---|---|
| 걷힌 종이 장수 | `COUNT(*)` — 행을 센다 | **4** |
| 뭐라도 적힌 장수 | `COUNT(dept_id)` — `NULL` 아닌 값을 센다 | **3** (`dan` 이 빠진다) |
| 적힌 답의 가짓수 | `COUNT(DISTINCT dept_id)` — 서로 다른 값을 센다 | **2** (`10`·`20`) |

```text
emp.dept_id = [10, 10, 20, NULL]

COUNT(*)                 -> 4    종이 장수.  값은 아예 안 본다
COUNT(dept_id)           -> 3    NULL 한 장을 뺀다
COUNT(DISTINCT dept_id)  -> 2    NULL 을 빼고, 남은 [10,10,20] 을 [10,20] 으로 접는다
                                  ^^^^^^^^^^^^  뺀 다음에 접는다. 순서가 중요하다
```

「빈칸은 안 센다」와 「같은 건 한 번만」이 **각각 한 번씩 적용되는 것**이 세 형태의 전부다.\
그런데 **똑같은 구조로** `SUM`·`AVG`·`MIN`·`MAX` 도 「빈칸은 건너뛴다」를 쓴다 —\
그래서 **`AVG` 의 분모가 `COUNT(*)` 이 아니다**(2번). 이 한 줄이 실무에서 가장 조용히 틀리는 자리다.

> **집계 함수(aggregate function)** — 여러 행을 값 하나로 접는 함수.\
> 예: `SUM(salary)` 는 4행의 급여를 합계 하나로 접는다.

> **`NULL` 을 건너뛴다(ignores nulls)** — 입력 값이 `NULL` 인 행을 **계산에 넣지 않는** 것. 0으로 치환하는 게 아니다.\
> 예: `SUM(salary)` 는 `cho` 의 `NULL` 을 0으로 더하는 게 아니라 **아예 안 더한다**.

## 이 주제가 답하려는 질문

1. **`COUNT` 의 세 형태는 각각 무엇을 세나?** — 그리고 어느 형태가 `NULL` 을 세고 어느 형태가 안 세나.
2. **`COUNT` 가 0인데 `SUM` 이 `NULL` 인 것은 모순인가?** — 아니다. 둘의 「빈 입력」 규칙이 다르다.
3. **「건수」를 세려고 `COUNT(*)` 을 썼는데 왜 실제보다 많이 나오나?** — 외부 조인이 만든 행까지 세기 때문이다.

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

**이 표가 집계를 설명하기에 딱 맞다** — `NULL` 이 **두 열에 하나씩** 있고, 중복 값(`dept_id=10` 둘)도 있다.

- `salary` 로 세면 **4 / 3 / 3** — `NULL` 만 갈린다(중복이 없다).
- `dept_id` 로 세면 **4 / 3 / 2** — **세 형태가 전부 다른 답**을 낸다. 아래 1번이 이 열을 쓴다.
- `hr` 은 사원이 하나도 없어서 **「0건인데 1행」** 함정을 만든다(4번).

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

### 1. ★ `COUNT` 세 형태가 `NULL` 과 중복을 각각 한 번씩 거른다

**언제 쓰나** — 「몇 건인가」를 물을 때마다. 즉 거의 매번.

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

```text
### SQL: SELECT COUNT(*) AS c_star, COUNT(dept_id) AS c_col, COUNT(DISTINCT dept_id) AS c_dist FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c_star | c_col | c_dist         +--------+-------+--------+
--------+-------+--------        | c_star | c_col | c_dist |
      4 |     3 |      2         +--------+-------+--------+
(1 row)                          |      4 |     3 |      2 |
                                 +--------+-------+--------+
```

그림 해설 — **체가 둘이고, 세 형태는 「몇 번째 체까지 통과시키나」로만 다르다.**\
`COUNT(*)` 은 체를 하나도 안 쓰고, `COUNT(열)` 은 첫째 체까지, `COUNT(DISTINCT 열)` 은 둘째 체까지 쓴다.

★ **순서가 중요하다 — `NULL` 을 버린 다음에 중복을 접는다.**\
그래서 `COUNT(DISTINCT dept_id)` 는 **2**이지 3이 아니다. `NULL` 은 「하나의 값」으로 세어지지 않는다.\
(값을 **묶을** 때는 `NULL` 끼리 한 그룹이 된다 — 규칙이 정반대다. 그건 [22번](../22-group-by-nonaggregated-columns/)과 [04번](../04-null-three-valued-logic/)에 있다.)

같은 세 형태를 `salary` 로 던지면 **중복이 없어서 뒤의 둘이 붙는다.**

```text
### SQL: SELECT COUNT(*) AS c_star, COUNT(salary) AS c_col, COUNT(DISTINCT salary) AS c_dist FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c_star | c_col | c_dist         +--------+-------+--------+
--------+-------+--------        | c_star | c_col | c_dist |
      4 |     3 |      3         +--------+-------+--------+
(1 row)                          |      4 |     3 |      3 |
                                 +--------+-------+--------+
```

★ **두 형태가 같은 값을 냈다고 같은 함수인 게 아니다.** 데이터에 중복이 없었을 뿐이다.\
「예전에 같은 답이 나왔으니 `COUNT(열)` 을 써도 된다」가 사고의 시작이다 — 데이터가 늘면 갈린다.

**`COUNT(*)` 은 인자를 아예 안 본다.** 상수를 넣어도 같다.

```text
### SQL: SELECT COUNT(*) AS star, COUNT(1) AS one, COUNT('x') AS lit, COUNT(NULL) AS n FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 star | one | lit | n            +------+-----+-----+---+
------+-----+-----+---           | star | one | lit | n |
    4 |   4 |   4 | 0            +------+-----+-----+---+
(1 row)                          |    4 |   4 |   4 | 0 |
                                 +------+-----+-----+---+
```

그림 해설 — `COUNT(1)` 은 **「1 이라는 `NULL` 아닌 값이 매 행에 있다」**를 세는 것이라 `COUNT(*)` 과 답이 같다.\
`COUNT(NULL)` 은 **0**이다 — 매 행이 `NULL` 이므로 첫째 체에서 전부 걸러진다. 같은 규칙의 극단이다.\
비용 — `COUNT(1)` 이 `COUNT(*)` 보다 빠르다는 속설이 있지만 **이 주제에서 측정하지 않았다.** 적지 않는다.

---

### 2. `SUM`·`AVG` 도 `NULL` 을 건너뛴다 — 그래서 `AVG` 의 분모가 다르다

**언제 쓰나** — `AVG` 를 쓸 때마다. 그리고 그 결과를 사람에게 보여 줄 때마다.

```text
emp.salary = [300, 500, NULL, 400]

COUNT(*)      -> 4      행을 센다
COUNT(salary) -> 3      NULL 아닌 값을 센다    <- AVG 의 분모가 이것이다
SUM(salary)   -> 1200   300+500+400.  NULL 을 0 으로 더하는 게 아니라 안 더한다
AVG(salary)   -> 400    1200 / 3 이다.   1200 / 4 = 300 이 아니다
```

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

그림 해설 — **「평균 급여 400」은 「4명의 평균」이 아니라 「급여가 기록된 3명의 평균」**이다.\
소수 자릿수가 두 엔진에서 다른 것은 `AVG` 의 결과 타입 차이다(값은 같다). 수치 타입은 [목록의 **36번 주제**](../36-numeric-types-and-functions/).\
대가 — 이 차이는 **숫자가 그럴듯해서** 리뷰에서 안 잡힌다. `AVG` 를 쓸 때는 `COUNT(*)` 과 `COUNT(열)` 을 **같이 뽑아 분모를 눈으로 확인**하는 편이 낫다.

`MIN`·`MAX` 도 같다 — `NULL` 을 건너뛴다.

```text
### SQL: SELECT MIN(salary) AS mn, MAX(salary) AS mx, MIN(name) AS mn_t, MAX(name) AS mx_t FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 mn  | mx  | mn_t | mx_t         +------+------+------+------+
-----+-----+------+------        | mn   | mx   | mn_t | mx_t |
 300 | 500 | ann  | dan          +------+------+------+------+
(1 row)                          |  300 |  500 | ann  | dan  |
                                 +------+------+------+------+
```

`NULL` 이 「가장 작은 값」으로도 「가장 큰 값」으로도 뽑히지 않았다.\
(`ORDER BY` 에서는 `NULL` 에 크기가 붙는다 — 그 규칙은 [목록의 **8번 주제**](../08-order-by-null-position-stability/)다. **정렬과 집계가 다르다.**)

★ **경계: [04번](../04-null-three-valued-logic/)이 「집계는 `NULL` 을 건너뛴다」는 사실까지, 여기는 그 사실이 세 `COUNT` 형태와 `AVG` 의 분모로 어떻게 갈라지나부터.**

비용 — 없다. 이건 정의다. 다만 `DISTINCT` 가 붙으면 중복 제거를 위해 정렬이나 해시가 한 겹 더 들어간다(계획은 목록의 **59번 주제**).

---

### 3. 0행에 대한 집계 — `COUNT` 는 0이고 나머지는 `NULL` 이다

**언제 쓰나** — 조건에 맞는 행이 하나도 없을 수 있는 집계를 쓸 때. 즉 거의 매번.

```text
      입력 0행
          |
   +------+------+
   |             |
COUNT(*)      SUM/AVG/MIN/MAX
   |             |
   v             v
   0            NULL      <- 여기가 갈린다. "합계 0" 이 아니다
```

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

그림 해설 — PG 문서가 이것을 한 문장으로 적는다: *"except for `count`, these functions return a null value when no rows are selected. In particular, `sum` of no rows returns null, not zero as one might expect"*.\
MySQL 문서도 같다: *"If there are no matching rows, `SUM()` returns `NULL`."*

**입력 행이 있어도 값이 전부 `NULL` 이면 결과가 같다.** 0행과 구분되지 않는다.

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

★ **`c`=1 인데 `s`=`NULL` 이다.** 「행이 있다」와 「더할 값이 있다」가 다른 질문이라는 뜻이다.\
합계를 0으로 보이고 싶으면 `COALESCE(SUM(salary), 0)` 을 쓴다. 뒤집어 `SUM(COALESCE(salary,0))` 도 같은 답을 낸다.

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

**두 형태가 `SUM` 에서는 같은 답을 낸다.** 하지만 `AVG` 로 바꾸면 갈린다 — `COALESCE` 를 안쪽에 두면 **`NULL` 이 0으로 분모에 합류**한다. 그 대비는 [24번](../24-conditional-aggregation-filter-case/)이 정본이다.

★ **`GROUP BY` 가 붙으면 「0행」의 의미가 또 달라진다** — 행이 없으면 **그룹 자체가 안 생겨서 결과가 0행**이다.

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp WHERE 1 = 0 GROUP BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c                     (아무 줄도 출력되지 않는다 — 빈 결과)
---------+---
(0 rows)
```

```text
### SQL: SELECT COUNT(*) AS c FROM emp WHERE 1 = 0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c                               +---+
---                              | c |
 0                               +---+
(1 row)                          | 0 |
                                 +---+
```

두 그림의 결론 — **`GROUP BY` 가 없으면 표 전체가 한 그룹이라 「0」이 한 행 나오고, `GROUP BY` 가 있으면 그룹이 0개라 아무 행도 안 나온다.**\
그래서 「0건인 부서를 찾겠다」를 `HAVING COUNT(*) = 0` 으로 쓰면 영원히 안 맞는다([03번](../03-where-vs-having/)).

---

### 4. ★ `hr` 부서 — `COUNT(*)`=1 인데 `COUNT(e.id)`=0

**언제 쓰나** — 외부 조인 뒤에 건수를 셀 때. [14번](../14-left-right-outer-join/)이 든 함정을 여기서 끝까지 판다.

`dept LEFT JOIN emp` 는 사원이 없는 `hr` 을 **`NULL` 로 채운 한 행**으로 남긴다.\
그 행은 **존재하는 행**이므로 `COUNT(*)` 이 1로 센다. 사원은 0명인데 1이다.

```text
LEFT JOIN 결과 4행

 d.name | e.id | e.salary      COUNT(*)  COUNT(e.id)  COUNT(e.salary)  SUM(e.salary)
--------+------+----------     --------  -----------  ---------------  -------------
 sales  |    1 |      300  ─┐
 sales  |    2 |      500  ─┴─>   2           2              2              800
 dev    |    3 |     NULL  ───>   1           1              0             NULL
 hr     | NULL |     NULL  ───>   1           0              0             NULL
                                  ^           ^              ^
                       조인이 만든 행까지  사원 수    급여가 기록된 사원 수
```

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

그림 해설 — ★ **`dev` 와 `hr` 을 견줘 보라. `star` 는 둘 다 1인데 의미가 완전히 다르다.**

| | `star` | `emp_cnt` | `sal_cnt` | 무슨 뜻인가 |
|---|---|---|---|---|
| `dev` | 1 | **1** | 0 | 사원 `cho` 가 **있다**. 급여만 기록이 없다 |
| `hr` | 1 | **0** | 0 | 사원이 **없다**. 조인이 만든 빈 행 하나가 세어졌다 |

**`COUNT(*)` 만 보면 둘이 똑같이 「1」이다.** 세 열을 나란히 뽑아야 구분된다.\
[14번](../14-left-right-outer-join/)이 여기까지 왔고, **`sal_cnt` 열을 더해 `dev` 와 `hr` 을 갈라 놓은 것이 이 주제의 몫**이다.

★ **규칙 한 줄: 외부 조인 뒤에 「건수」를 세려면 상대 측의 `NULL` 일 수 없는 열을 센다.** 보통 기본키다.\
`e.id` 는 `emp` 의 기본키라 원본에 `NULL` 이 없다 — **그러므로 거기가 `NULL` 이면 조인이 만든 행이다.**

대가 — 열 하나를 더 골라야 한다. 그 대신 「0건」이 0으로 나온다.\
`SUM` 도 같이 본다 — `dev`·`hr` 모두 `NULL` 이다. **「합계가 없다」와 「합계가 0이다」는 다른 답**이고, 화면에서는 `NULL` 하나로 뭉쳐 있다(3번).

---

### 5. 집계 안에 집계는 못 넣는다 — 두 엔진이 다른 말로 거부한다

**언제 쓰나** — 「부서별 인원수의 평균」처럼 **두 단계 집계**가 필요할 때. 한 번에 쓰려다 여기서 막힌다.

```text
 하고 싶은 것                        한 문으로 쓰면
 1단계: 부서별 COUNT(*)              SELECT AVG(COUNT(*)) ...
 2단계: 그 값들의 AVG                        ^^^^^^^^^^
                                      집계의 입력은 "행"이지 "집계 결과"가 아니다
```

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

그림 해설 — **PG 는 「중첩할 수 없다」고 이유를 말하고, MySQL 은 「그룹 함수를 잘못 썼다」고만 한다.**\
MySQL 의 `ERROR 1111` 은 **자리를 잘못 쓴 모든 집계**에 붙는 한 덩어리 메시지라, 무엇이 문제인지 덜 말해 준다.\
두 엔진 모두 **거부한다는 사실은 같다** — 이건 방언 차이가 아니라 메시지 차이다.

**고치는 법 — 한 겹 감싼다.** 1단계 집계를 파생 테이블로 만들고 그 위에 2단계를 얹는다([10번](../10-from-clause-aliases-derived-tables/)).

```sql
SELECT AVG(c) FROM (SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY dept_id) t;
```

같은 이유로 **`GROUP BY` 에도 집계 함수를 못 쓴다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY COUNT(*);
--- PG 18.6 ---
ERROR:  aggregate functions are not allowed in GROUP BY
LINE 1: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY COUNT(*);
                                                        ^
--- MySQL 8.4.10 ---
ERROR 1056 (42000) at line 1: Can't group on 'c'
```

★ **뿌리는 [01번](../01-logical-query-processing-order/)의 처리 순서다** — 집계는 `GROUP BY` 가 그룹을 만든 **뒤**에 계산되므로, 그 결과를 `GROUP BY` 자신이 입력으로 받을 수 없다.\
MySQL 이 `'c'` 라는 **별칭**으로 가리키는 것에 주목하라 — MySQL 은 `GROUP BY` 에서 출력 열 이름을 먼저 찾는다([03번](../03-where-vs-having/)이 같은 탐색 순서를 `HAVING` 에서 다룬다).

---

### 6. ★ 방언 — `COUNT(DISTINCT 열1, 열2)` 는 서로를 정확히 거부한다

**언제 쓰나** — 「(부서, 급여) 조합이 몇 가지인가」처럼 **여러 열의 조합**을 셀 때.

```text
MySQL 형태                          PostgreSQL 형태
COUNT(DISTINCT dept_id, salary)     COUNT(DISTINCT (dept_id, salary))
        ^                                            ^
  인자를 나열한다                          괄호로 묶어 "행 값" 하나를 만든다
```

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

**서로의 문법을 정확히 거부한다.** 그리고 ★ **돌아가는 쪽끼리도 답이 다르다 — 2 대 4.**

```text
입력 (dept_id, salary) 네 쌍
 (10, 300)  (10, 500)  (20, NULL)  (NULL, 400)

MySQL: COUNT(DISTINCT dept_id, salary)  -> 2
   "한 칸이라도 NULL 인 행은 안 센다"  -> (20,NULL) 과 (NULL,400) 을 버린다 -> 2 가지

PG: COUNT(DISTINCT (dept_id, salary))   -> 4
   괄호가 만든 "행 값" 자체는 NULL 이 아니다 -> 넷 다 세고, 서로 달라서 4 가지
```

그림 해설 — MySQL 문서가 그대로 적는다: *"Returns a count of the number of rows with different non-`NULL` expr values."*\
**`NULL` 이 하나라도 낀 행은 통째로 빠진다.** PG 쪽은 `COUNT(DISTINCT 한 값)` 이고, 그 「한 값」이 행 값이라 `NULL` 체에 안 걸린다.

대가 — ★ **이식할 수 없다.** 두 엔진에서 같은 답을 원하면 **열을 문자열로 잇지 말고**(그건 구분자 사고를 부른다) 파생 테이블로 푼다.

```sql
SELECT COUNT(*) FROM (SELECT DISTINCT dept_id, salary FROM emp) t;   -- 양쪽에서 4
```

★ **이 자리 때문에 목록 README 의 21번 방언 칸을 `표준` → `차이` 로 정정했다.** 근거는 위 두 에러와 2 대 4다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
COUNT(*)                          -- 행을 센다. 인자를 보지 않는다
COUNT(식)                         -- 식이 NULL 이 아닌 행을 센다
COUNT(DISTINCT 식)                -- NULL 을 버린 뒤 서로 다른 값을 센다
SUM(식) · AVG(식) · MIN(식) · MAX(식)   -- NULL 인 입력을 건너뛴다
SUM(DISTINCT 식) · AVG(DISTINCT 식)     -- 중복을 접은 뒤 계산한다 (양쪽 엔진 모두 있다)
```

규칙 일곱.

1. **`COUNT(*)` 만 행을 세고, 나머지는 전부 값을 센다.** 이 한 줄이 세 형태의 뿌리다.
2. **`NULL` 을 버리는 것이 먼저, 중복을 접는 것이 나중.** 그래서 `COUNT(DISTINCT)` 는 `NULL` 을 한 가지로 세지 않는다.
3. **`COUNT` 만 0행에서 0을 낸다.** `SUM`·`AVG`·`MIN`·`MAX` 는 `NULL` 이다.
4. **`AVG` 의 분모는 `COUNT(열)` 이다.** `COUNT(*)` 이 아니다.
5. **집계 안에 집계를 못 넣는다.** 두 단계면 파생 테이블로 한 겹 감싼다.
6. **`GROUP BY` 가 있으면 0행 입력은 0그룹**이다 — 결과가 아예 비어 있다.
7. **`COUNT(DISTINCT 열1, 열2)` 는 MySQL 형태**다. PG 는 `COUNT(DISTINCT (열1, 열2))` 이고 **답도 다르다.**

`COUNT` 의 실전 형태는 사실상 **넷**이다.

```sql
-- (1) 행 수 — "이 조건에 맞는 행이 몇 개인가"
SELECT COUNT(*) FROM emp WHERE salary >= 400;

-- (2) 값이 있는 행 수 — "급여가 기록된 사람이 몇 명인가"
SELECT COUNT(salary) FROM emp;

-- (3) 가짓수 — "서로 다른 부서가 몇 개인가"
SELECT COUNT(DISTINCT dept_id) FROM emp;

-- (4) 외부 조인 뒤의 건수 — "부서별 사원 수(0명 포함)"
SELECT d.name, COUNT(e.id) FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name;
```

## 어디서 틀리나

- **★ 「몇 명인가」에 `COUNT(*)` 을 쓴다.**\
  외부 조인이 섞이면 **0명이 1로 세어진다**(`hr`). 상대 측 기본키를 센다.
- **★ `COUNT(열)` 과 `COUNT(DISTINCT 열)` 을 같은 것으로 안다.**\
  `salary` 로는 둘 다 3이었지만 `dept_id` 로는 3 과 2 다. 데이터에 중복이 없었을 뿐이다.
- **★ `AVG` 의 분모를 `COUNT(*)` 으로 생각한다.**\
  4명의 평균을 봤다고 생각했는데 3명의 평균이었다. 숫자가 그럴듯해서 안 걸린다.
- **`SUM` 이 0으로 나올 거라 믿는다.**\
  0행이든 전부 `NULL` 이든 `SUM` 은 `NULL` 이다. `COALESCE(SUM(...), 0)` 을 쓴다.
- **`COUNT(DISTINCT 열)` 이 `NULL` 을 한 가지로 셀 거라 믿는다.**\
  안 센다. `NULL` 도 세고 싶으면 `COUNT(DISTINCT COALESCE(열, -1))` 처럼 **실제로 안 나오는 값**으로 채워야 한다 — 그 값이 실제 데이터에 있으면 조용히 틀린다.
- **`HAVING COUNT(*) = 0` 으로 「0건」을 찾는다.**\
  `GROUP BY` 는 행이 없는 그룹을 만들지 않는다. 외부 조인 + `COUNT(상대측 키) = 0` 이다([03번](../03-where-vs-having/)·[14번](../14-left-right-outer-join/)).
- **두 단계 집계를 한 문에 쓴다.**\
  `AVG(COUNT(*))` 은 두 엔진 모두 에러다. 파생 테이블로 감싼다.
- **`COUNT(DISTINCT a, b)` 를 이식한다.**\
  PG 에서 **함수가 없다**는 에러가 난다. 고쳐 써도 `NULL` 처리가 달라 답이 갈린다(2 대 4).

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `COUNT(*)` 이 행을 센다 | **정의** | 언어 — 두 문서가 같은 모양으로 적는다 |
| `COUNT(열)` 이 `NULL` 을 안 센다 | **정의** | 언어 — PG *"in which the input value is not null"* · MySQL *"non-`NULL` values"* |
| `SUM`·`AVG`·`MIN`·`MAX` 가 `NULL` 을 건너뛴다 | **정의** | 언어 |
| 0행에서 `COUNT`=0, 나머지=`NULL` | **정의** | 언어 — PG 문서가 *"not zero as one might expect"* 라고 못 박는다 |
| `AVG` 결과의 **소수 자릿수** | 결과 타입의 선택 | 엔진 — PG `numeric`, MySQL `DECIMAL`. **값은 같고 표기가 다르다** |
| `COUNT` 가 돌려주는 **타입** | 엔진 — PG 는 `bigint`(`pg_typeof` 로 확인) | 값의 범위 문제일 뿐 결과는 같다 |
| `COUNT(1)` 이 `COUNT(*)` 보다 빠른가 | **측정 안 함** | 이 주제에서 재지 않았다. 적지 않는다 |
| `COUNT(DISTINCT 열1, 열2)` | **방언** | 문법도 결과도 갈린다(6번) |

- **이 주제에서 두 엔진의 결과가 갈린 자리는 6번 하나다.** 나머지 출력은 값이 전부 같았다(표기만 다르다).
- **에러 메시지는 전부 다르다.** 「거부한다」는 같고 **무엇이라 부르는지**가 다르다 — 5번의 `1111` 대 `cannot be nested`.

## 언제 쓰고 언제 안 쓰나

- **`COUNT(*)` — 「행이 몇 개인가」가 진짜 묻는 것일 때.** 존재 확인·페이지 수 계산.
- **`COUNT(열)` — 「값이 기록된 것이 몇 개인가」일 때.** 결측률 보기에 좋다(`COUNT(*) - COUNT(열)`).
- **`COUNT(DISTINCT 열)` — 「가짓수」일 때.** 방문자 수·품목 수.
- **안 쓴다 — 「있기만 하면 되는」 존재 확인에 `COUNT(*) > 0`.** `EXISTS` 가 낫다([목록의 **19번 주제**](../19-semi-anti-join/)) — 첫 행에서 멈출 수 있다.
- **안 쓴다 — 대규모 근사 계수에 `COUNT(DISTINCT)`.** 정확값이 필요 없으면 HLL 류가 훨씬 싸다 — 그건 [`19-probabilistic-counting`](../../../../../data-structure/19-probabilistic-counting/)이다.
- **조인 뒤에는 그냥 쓰지 않는다.** 행이 불었는지 먼저 본다([25번](../25-join-fan-out/)).

## 핵심 문장

- `COUNT` 의 세 형태는 **체 둘**(`NULL` 버리기 → 중복 접기)을 **몇 개까지 통과시키나**로만 다르다 — 4 / 3 / 2.
- **`NULL` 을 버리는 것이 먼저다.** 그래서 `COUNT(DISTINCT)` 는 `NULL` 을 한 가지로 세지 않는다.
- `SUM`·`AVG`·`MIN`·`MAX` 도 `NULL` 을 **건너뛴다.** 0으로 치환하는 게 아니다.
- ★ **`AVG` 의 분모는 `COUNT(열)` 이다** — 「4명의 평균 400」이 아니라 「3명의 평균 400」이었다.
- **0행에서 `COUNT` 만 0이고 나머지는 `NULL` 이다.** `COUNT`=0 인데 `SUM`=`NULL` 은 모순이 아니다.
- ★ **외부 조인 뒤의 `COUNT(*)` 은 건수가 아니다** — `hr` 이 0명인데 1로 세어졌다. **상대 측 기본키**를 센다.
- `dev`(1명·급여 없음)와 `hr`(0명)은 `COUNT(*)` 으로는 **둘 다 1**이다. `COUNT(e.id)` 를 같이 봐야 갈린다.
- **집계 안에 집계는 두 엔진 모두 에러다.** 파생 테이블로 한 겹 감싼다.
- **`COUNT(DISTINCT a, b)` 는 MySQL 형태**이고 PG 형태와 **답까지 다르다**(2 대 4).

## 관련 자료

- [PostgreSQL 18 · Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html) — `count`·`sum`·`avg` 의 `NULL` 규칙과 *"sum of no rows returns null"* 문장이 여기 있다.
- [PostgreSQL 18 · Aggregate Expressions](https://www.postgresql.org/docs/18/sql-expressions.html) — `DISTINCT`·`FILTER` 를 포함한 집계 호출 문법.
- [MySQL 8.4 · Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html) — `COUNT(DISTINCT expr,[expr...])` 의 *"different non-`NULL` expr values"* 문장.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `UNKNOWN` 의 계산 규칙과 「집계는 `NULL` 을 건너뛴다」는 사실까지, 여기는 그 사실이 세 `COUNT` 형태와 `AVG` 분모로 어떻게 갈라지나부터.**
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — **경계: 그쪽은 `hr` 의 `COUNT(*)`=1 을 함정으로 드는 데까지, 여기는 `dev` 와 `hr` 을 세 열로 갈라 보는 것부터.**
- [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) — **경계: 여기는 집계 함수 하나하나의 의미까지, 「그룹이 무엇이고 무엇이 보이나」는 거기.**
- [24 조건부 집계 — FILTER 와 CASE](../24-conditional-aggregation-filter-case/) — **경계: 여기는 집계의 기본 형태까지, 「조건을 붙인 집계」는 거기.**
- [25 조인 팬아웃](../25-join-fan-out/) — **경계: 여기는 한 표 위의 집계까지, 조인이 행을 늘린 뒤의 집계는 거기.**
- [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/) — 「0건인 그룹」을 `HAVING` 으로 못 찾는 이유.
- [`data-structure/19-probabilistic-counting`](../../../../../data-structure/19-probabilistic-counting/) — **경계: 근사 계수(HLL 류)의 자료구조는 거기, 여기는 정확 계수의 문법과 `NULL` 처리.**
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **집계 함수(aggregate function)** — 여러 행을 값 하나로 접는 함수.\
  예: `SUM(salary)` 는 4행을 `1200` 하나로 접는다.
- **`COUNT(*)`** — **행**을 세는 형태. 인자의 값을 보지 않는다.\
  예: `emp` 에서 4. `COUNT(1)`·`COUNT('x')` 도 같은 답을 낸다.
- **`COUNT(식)`** — 식이 `NULL` 이 **아닌** 행을 세는 형태.\
  예: `COUNT(dept_id)` 는 3 — `dan` 이 빠진다.
- **`COUNT(DISTINCT 식)`** — `NULL` 을 버린 뒤 **서로 다른 값**의 가짓수를 세는 형태.\
  예: `COUNT(DISTINCT dept_id)` 는 2 — `10`·`20`. `NULL` 은 한 가지로 안 센다.
- **`NULL` 을 건너뛴다(ignores nulls)** — 입력이 `NULL` 인 행을 계산에 **안 넣는** 것. 0으로 바꾸는 게 아니다.\
  예: `SUM(salary)` 는 `cho` 의 `NULL` 을 더하지 않아 `1200` 이다.
- **분모(denominator)** — `AVG` 가 합을 나누는 수. **`COUNT(열)` 이다.**\
  예: `AVG(salary)` 는 `1200 / 3` 이라 400 이다. `1200 / 4` = 300 이 아니다.
- **빈 입력(no rows selected)** — 집계에 들어온 행이 하나도 없는 상태.\
  예: `WHERE 1 = 0` 에서 `COUNT(*)`=0 이지만 `SUM`·`AVG`·`MIN`·`MAX` 는 전부 `NULL` 이다.
- **`COALESCE`** — 인자 중 처음으로 `NULL` 이 아닌 값을 돌려주는 식.\
  예: `COALESCE(SUM(salary), 0)` 은 `hr` 의 `NULL` 합계를 0으로 보인다.
- **조인이 만든 `NULL`(join-generated NULL)** — 원본에 없었는데 외부 조인이 채워 넣은 `NULL`.\
  예: `hr` 행의 `e.id`. `emp.id` 는 기본키라 원본에는 `NULL` 이 없다.
- **중첩 집계(nested aggregate)** — 집계 함수의 인자로 다른 집계를 쓰는 것. **두 엔진 모두 거부한다.**\
  예: `AVG(COUNT(*))`. PG 는 `cannot be nested`, MySQL 은 `ERROR 1111` 이다.
- **행 값(row value)** — 괄호로 여러 열을 묶어 만든 한 개의 합성 값.\
  예: PG 의 `COUNT(DISTINCT (dept_id, salary))` 에서 `(dept_id, salary)` 가 행 값이다. 안쪽에 `NULL` 이 있어도 행 값 자체는 `NULL` 이 아니다.

## 더 들어가면

- **`COUNT(*)` 이 「빠른 연산」이라는 인상은 엔진에 따라 다르다.** PG 는 MVCC 때문에 전체 `COUNT(*)` 에도 가시성 확인이 필요하다.\
  이 주제에서는 **재지 않았다.** 계획을 읽는 법은 목록의 **58번 주제**, 스캔 연산자는 **59번 주제**다.
- **`SUM(DISTINCT 식)`·`AVG(DISTINCT 식)` 도 두 엔진에 있다**(실행 확인 — `SUM(DISTINCT salary)`=1200 · `AVG(DISTINCT salary)`=400).\
  하지만 **거의 항상 함정**이다. 값이 같은 두 행을 한 번만 더하는 게 의도인 경우는 드물다 — [25번](../25-join-fan-out/)에 그 실측이 있다.
- **「없음」을 어떻게 보일지는 집계가 아니라 표현의 문제다.** `COALESCE`·`NULLIF`·`CASE` 는 [목록의 **6번 주제**](../06-conditional-expressions-case-coalesce/)가 정본이다.
