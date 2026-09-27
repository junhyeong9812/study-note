# sql/31-윈도우 함수의 평가 시점과 `WINDOW` 절 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 모든 질의는 [1-question.md](1-question.md) 머리의 `WITH emp8 AS (...)` CTE 를 앞에 붙여 돌렸다.\
> 문서 근거는 [PG 18 Window Functions](https://www.postgresql.org/docs/18/tutorial-window.html) · [MySQL 8.4 Window Function Concepts and Syntax](https://dev.mysql.com/doc/refman/8.4/en/window-functions-usage.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 셋 다 에러다 — **PG 는 절 이름을 대 주고 MySQL 은 한 문장으로 묶는다**

**출력**

```text
### SQL: SELECT name FROM emp8 WHERE ROW_NUMBER() OVER (ORDER BY id) <= 2;
--- PG 18.6 ---
ERROR:  window functions are not allowed in WHERE
LINE 7: ) SELECT name FROM emp8 WHERE ROW_NUMBER() OVER (ORDER BY id...
                                      ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'row_number' in this context.'
```

```text
### SQL: SELECT dept_id, COUNT(*) FROM emp8 GROUP BY dept_id HAVING ROW_NUMBER() OVER (ORDER BY dept_id) = 1;
--- PG 18.6 ---
ERROR:  window functions are not allowed in HAVING
LINE 7: ...pt_id, COUNT(*) FROM emp8 GROUP BY dept_id HAVING ROW_NUMBER...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'row_number' in this context.'
```

```text
### SQL: SELECT name FROM emp8 GROUP BY ROW_NUMBER() OVER (ORDER BY id);
--- PG 18.6 ---
ERROR:  window functions are not allowed in GROUP BY
LINE 7: ) SELECT name FROM emp8 GROUP BY ROW_NUMBER() OVER (ORDER BY...
                                         ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'row_number' in this context.'
```

**왜 그런가**

```text
PG   : "not allowed in WHERE" / "in HAVING" / "in GROUP BY"  -> 어느 칸인지 말해 준다
MySQL: 세 번 다 "in this context"                            -> 어느 칸인지 말해 주지 않는다
```

★ **거부한다는 사실은 같고, 무엇이라 부르는지가 다르다.** [26번](../26-window-functions-vs-aggregates/) 6번의 중첩 에러도 **같은 `ERROR 3593`** 이었다 —\
MySQL 은 「윈도우를 쓸 수 없는 자리」 전부를 이 한 번호로 묶는다.

두 문서가 규정을 적는다.\
PG: *"Window functions are permitted only in the `SELECT` list and the `ORDER BY` clause of the query. They are forbidden elsewhere, such as in `GROUP BY`, `HAVING` and `WHERE` clauses."*\
MySQL: *"Window functions are permitted only in the select list and `ORDER BY` clause."*

> **`ERROR 3593`** — MySQL 이 「윈도우 함수를 쓸 수 없는 자리」에 쓰는 한 덩어리 메시지.\
> 예: `WHERE`·`HAVING`·`GROUP BY`·중첩이 전부 이 번호다.

---

### 2. `WHERE` 는 **2번 칸**이고 윈도우는 **5번 칸**에서 태어나기 때문이다

```text
1. FROM      표를 만든다
2. WHERE     행을 버린다        <- 여기서 rn 을 달라고 했다
3. GROUP BY  행을 묶는다
4. HAVING    그룹을 버린다
5. SELECT    열을 만든다        <- rn 은 여기서 태어난다
6. DISTINCT
7. ORDER BY
8. LIMIT

2번 칸이 5번 칸의 결과를 볼 수 없다 -> "아직 안 만들어졌다"
```

PG 문서가 이유를 한 문장으로 적는다: *"This is because they logically execute after the processing of those clauses."*

★ **[01번](../01-logical-query-processing-order/)이 「별칭을 `WHERE` 에서 못 쓴다」고 설명한 것과 한 글자도 다르지 않다.**\
별칭도 윈도우도 **5번 칸에서 태어난다** — 그래서 앞 칸에서는 없고 뒤 칸에서는 있다.\
[01번](../01-logical-query-processing-order/)의 「어디서 틀리나」가 이 에러를 한 줄로 예고하고 있다.

★ **`HAVING` 도 마찬가지다.** 4번 칸이 5번보다 앞이므로 같은 이유로 막힌다 —\
「집계는 `HAVING` 에서 되는데 윈도우는 왜 안 되나」의 답이 「**집계는 3·4번 칸, 윈도우는 5번 칸**」이다([03번](../03-where-vs-having/)).

---

### 3. `ORDER BY` 는 **7번 칸**이라 5번을 이미 지나왔기 때문이다

**출력**

```text
### SQL: SELECT name, salary FROM emp8 ORDER BY ROW_NUMBER() OVER (ORDER BY salary DESC, id);
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   +------+--------+
------+--------                  | name | salary |
 cho  |   NULL                   +------+--------+
 bob  |    500                   | bob  |    500 |
 fay  |    500                   | fay  |    500 |
 dan  |    400                   | dan  |    400 |
 gus  |    400                   | gus  |    400 |
 hui  |    400                   | hui  |    400 |
 ann  |    300                   | ann  |    300 |
 eve  |    300                   | eve  |    300 |
(8 rows)                         | cho  |   NULL |
                                 +------+--------+
```

**왜 그런가**

```text
5. SELECT    <- rn 이 태어난다
6. DISTINCT
7. ORDER BY  <- 이미 있다. 쓸 수 있다
```

★ **`ORDER BY` 안에 또 `OVER (ORDER BY ...)` 가 들어간 모양이 어색해 보이지만 자연스럽다.**\
바깥은 **출력 정렬**, 안쪽은 **창 안 정렬**이다 — 서로 다른 일이다([27번](../27-partition-by-and-window-order-by/) 4번).

★ **결과 행 순서가 두 엔진에서 다른 것은 평가 시점 문제가 아니다.**\
`ROW_NUMBER` 가 매긴 번호가 이미 다르기 때문이다 — PG 는 `NULL` 을 `DESC` 에서 맨 앞에 놓는다([29번](../29-ranking-functions/) 9번).

---

### 4. (A)는 **5**, (B)는 **8** — 창은 `WHERE` 를 통과한 행만 본다

**출력**

```text
### SQL: SELECT name, salary, COUNT(*) OVER () AS c FROM emp8 WHERE salary >= 400 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | c               +------+--------+---+
------+--------+---              | name | salary | c |
 bob  |    500 | 5               +------+--------+---+
 dan  |    400 | 5               | bob  |    500 | 5 |
 fay  |    500 | 5               | dan  |    400 | 5 |
 gus  |    400 | 5               | fay  |    500 | 5 |
 hui  |    400 | 5               | gus  |    400 | 5 |
(5 rows)                         | hui  |    400 | 5 |
                                 +------+--------+---+
```

```text
### SQL: SELECT name, salary, COUNT(*) OVER () AS c FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | c               +------+--------+---+
------+--------+---              | name | salary | c |
 ann  |    300 | 8               +------+--------+---+
 bob  |    500 | 8               | ann  |    300 | 8 |
 cho  |   NULL | 8               | bob  |    500 | 8 |
 dan  |    400 | 8               | cho  |   NULL | 8 |
 eve  |    300 | 8               | dan  |    400 | 8 |
 fay  |    500 | 8               | eve  |    300 | 8 |
 gus  |    400 | 8               | fay  |    500 | 8 |
 hui  |    400 | 8               | gus  |    400 | 8 |
(8 rows)                         | hui  |    400 | 8 |
                                 +------+--------+---+
```

**왜 그런가**

```text
emp8 8행
   |
   v  2번 칸: WHERE salary >= 400   -> 3행을 버린다
 5행
   |
   v  5번 칸: COUNT(*) OVER ()      -> 창은 이 5행이다
   5
```

★★ **`OVER ()` 의 「전체」는 「표 전체」가 아니라 「`WHERE` 를 통과한 전체」다.**\
「전체 대비 내 비중」을 구하면서 `WHERE` 로 기간을 잘라 두면 분모가 **그 기간의 합**이 된다 —\
그게 의도였는지는 질의문이 말해 주지 않는다. **에러도 경고도 없이** 다른 답이 나온다.

표 전체가 분모여야 하면 **`WHERE` 를 바깥으로 뺀다.**

```sql
SELECT * FROM (SELECT name, salary, COUNT(*) OVER () AS c FROM emp8) t WHERE salary >= 400;
--                                                                      ^^^^^^^^^^^^^^^^^
--                                        창은 8행을 봤고, 거르기는 그 뒤다 -> c 는 8 이다
```

**두 엔진의 값이 한 자리도 안 갈렸다** — 평가 시점은 양쪽이 같다.

---

### 5. **한 겹 감싼다.** 서브쿼리와 CTE 가 **같은 답**을 낸다

**출력**

```text
### SQL: SELECT name, salary, rn FROM (SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn FROM emp8) t
         WHERE rn <= 2 ORDER BY rn;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rn              +------+--------+----+
------+--------+----             | name | salary | rn |
 cho  |   NULL |  1              +------+--------+----+
 bob  |    500 |  2              | bob  |    500 |  1 |
(2 rows)                         | fay  |    500 |  2 |
                                 +------+--------+----+
```

```text
### SQL: WITH ranked AS (SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn FROM emp8)
         SELECT name, salary, rn FROM ranked WHERE rn <= 2 ORDER BY rn;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rn              +------+--------+----+
------+--------+----             | name | salary | rn |
 cho  |   NULL |  1              +------+--------+----+
 bob  |    500 |  2              | bob  |    500 |  1 |
(2 rows)                         | fay  |    500 |  2 |
                                 +------+--------+----+
```

**왜 그런가**

```text
안쪽 질의                                 바깥 질의
FROM -> WHERE -> ... -> SELECT            FROM (안쪽) -> WHERE -> ...
                        ^^^^^^                 ^^^^^^^^^^^^^^^^
                   rn 이 여기서 태어나고        여기서 rn 은 그냥 열이다
                   안쪽 질의는 거기서 끝난다     -> WHERE 에서 쓸 수 있다
```

PG 문서가 이 우회를 그대로 권한다: *"If there is a need to filter or group rows after the window calculations are performed, you can use a sub-select."*

**어느 쪽을 쓰나** — 답은 같으므로 **읽기 편한 쪽**이다.

| | 언제 |
|---|---|
| **CTE(`WITH`)** | 단계가 둘 이상이거나 이름이 있으면 읽히는 질의. 재사용도 된다 |
| **서브쿼리** | 한 번 쓰고 마는 짧은 질의 |

★ **MySQL 은 파생 테이블에 별칭 `t` 가 필수**다([10번](../10-from-clause-aliases-derived-tables/)). CTE 에는 이름이 이미 있으니 그 문제가 없다.

---

### 6. PG 는 **`cho`·`bob`**, MySQL 은 **`bob`·`fay`** — 원인은 **이 주제의 규칙이 아니다**

5번 출력을 다시 보라. 「상위 2명」인데 두 엔진의 답이 다르다.

```text
ORDER BY salary DESC, id 로 창을 세우면

PG   : NULL 이 가장 큰 값 -> cho 가 1번, bob 이 2번   -> 급여가 없는 사람이 1등이다
MySQL: NULL 이 가장 작은 값 -> bob 이 1번, fay 가 2번
```

★★ **감싸는 것이 틀린 게 아니다.** 안쪽 `ROW_NUMBER` 가 이미 다른 번호를 매겼을 뿐이다.\
원인은 **[08번](../08-order-by-null-position-stability/)의 `NULL` 위치 규칙**이고, [29번](../29-ranking-functions/) 9번이 같은 출력을 다뤘다.

★ **진단을 나눠서 하라.**

| 증상 | 의심할 자리 |
|---|---|
| **에러가 난다** | 평가 시점 — 이 주제 |
| **에러는 없는데 답이 엔진마다 다르다** | `ORDER BY` 가 끝까지 안 정해졌다 — [08번](../08-order-by-null-position-stability/)·[29번](../29-ranking-functions/) |

**고치면 양쪽이 같아진다.**

```sql
WITH ranked AS (
  SELECT name, salary, ROW_NUMBER() OVER (ORDER BY (salary IS NULL), salary DESC, id) AS rn
  FROM emp8
)
SELECT name, salary, rn FROM ranked WHERE rn <= 2;
```

★ **「거르는 법」만 배우고 넘어가면 다음 사고가 여기서 난다.** 우회가 되는지 확인하는 것과\
**우회한 결과가 맞는지 확인하는 것**은 다른 일이다.

---

### 7. 단순 「상위 2명」은 **같은 답**이다. 「부서마다 1명」은 **`LIMIT` 로 못 쓴다**

**출력**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn FROM emp8 ORDER BY rn LIMIT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rn              +------+--------+----+
------+--------+----             | name | salary | rn |
 cho  |   NULL |  1              +------+--------+----+
 bob  |    500 |  2              | bob  |    500 |  1 |
(2 rows)                         | fay  |    500 |  2 |
                                 +------+--------+----+
```

**왜 그런가**

```text
창이 하나뿐이면          LIMIT 2 == WHERE rn <= 2      (5번과 답이 같다)

PARTITION BY 가 붙으면   LIMIT 은 "결과 전체" 에서 자른다
                         -> "부서마다 1명" 은 못 쓴다
                         -> 8번 칸은 하나뿐이고, 그룹마다 돌지 않는다
```

★ **「부서마다 상위 1명」은 감싸는 수밖에 없다.**

```sql
WITH ranked AS (
  SELECT dept_id, name, salary,
         ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC, id) AS rn
  FROM emp8 WHERE salary IS NOT NULL
)
SELECT dept_id, name, salary FROM ranked WHERE rn = 1;
```

그 출력은 [29번](../29-ranking-functions/) 10번에 있다 — **3행**이 나온다.

★ **`LIMIT` 은 「결과에서 앞 n 개」이고 `WHERE rn <= n` 은 「창마다 앞 n 개**」다.\
창이 하나일 때만 두 말이 같은 뜻이 된다.

---

### 8. 아니다 — **`LIMIT` 은 8번 칸**이라 윈도우는 이미 8행 전부에 대해 계산됐다

```text
5. SELECT   <- 8행 전부에 대해 ROW_NUMBER 를 매긴다
6. DISTINCT
7. ORDER BY <- 그 번호로 정렬한다
8. LIMIT    <- 이제서야 2행만 남긴다

LIMIT 은 앞 칸의 일을 줄여 주지 않는다
```

★ **[01번](../01-logical-query-processing-order/)의 「`LIMIT` 을 붙이면 빨라질 거라 믿는다」와 같은 자리다.**\
순위를 매기려면 **전부에 번호를 매겨야** 하므로 원리적으로도 줄일 수 없다 —\
「1등이 누구인가」는 전원을 봐야 알 수 있다.

★ **실행 계획은 다른 이야기다.** 옵티마이저가 정렬을 「상위 n 개만 유지」로 바꾸는 최적화는 가능하고,\
그것은 결과가 아니라 **비용**의 문제다. **이 주제에서 계획을 찍지 않았다** — 계획 읽는 법은 [목록의 **58번 주제**](../58-explain-plan-tree/)다.\
★ **계획은 관찰이지 보장이 아니다.**

---

### 9. 돈다 — 창은 **접힌 뒤의 3행**을 본다

**출력**

```text
### SQL: SELECT dept_id, COUNT(*) AS c, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rn
         FROM emp8 GROUP BY dept_id ORDER BY rn;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c | rn                +---------+---+----+
---------+---+----               | dept_id | c | rn |
      10 | 4 |  1                +---------+---+----+
      20 | 3 |  2                |      10 | 4 |  1 |
    NULL | 1 |  3                |      20 | 3 |  2 |
(3 rows)                         |    NULL | 1 |  3 |
                                 +---------+---+----+
```

**왜 그런가**

```text
3. GROUP BY  8행 -> 3행
4. HAVING
5. SELECT    창은 이 3행이다 -> ROW_NUMBER 가 1·2·3 을 준다
             창 안 ORDER BY 에 COUNT(*) 를 쓸 수 있다 — 3·4번 칸에서 이미 계산됐으니까
```

★ **방향이 하나뿐이다.**

```text
집계 -> 윈도우 : 된다   (3·4번 칸의 결과를 5번 칸이 받는다)
윈도우 -> 집계 : 에러   (5번 칸의 결과를 3번 칸이 못 받는다)  — 26번 6번
```

★ **`COUNT(*) OVER ()` 가 여기서 8이 아니라 3이 되는 것**도 같은 이유다([26번](../26-window-functions-vs-aggregates/) 4번).\
**두 엔진의 값이 한 자리도 안 갈렸다.**

---

### 10. **3행**이 된다 — `GROUP BY` 와 결과는 같지만 **하는 일이 다르다**

**출력**

```text
### SQL: SELECT DISTINCT dept_id, COUNT(*) OVER (PARTITION BY dept_id) AS c FROM emp8;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c                     +---------+---+
---------+---                    | dept_id | c |
      10 | 4                     +---------+---+
      20 | 3                     |    NULL | 1 |
    NULL | 1                     |      10 | 4 |
(3 rows)                         |      20 | 3 |
                                 +---------+---+
```

**왜 그런가**

```text
5. SELECT    8행 전부에 창을 계산한다 -> (10,4) x4 · (20,3) x3 · (NULL,1) x1
6. DISTINCT  같은 쌍을 하나로 접는다  -> 3행
             ^^^^^^^^^^^^^^^^^^^^^
             8행을 만들고 5행을 버린 것이다

GROUP BY 로 쓰면 애초에 3행만 만든다
```

MySQL 문서가 `DISTINCT` 의 자리를 명시한다: *"windowing execution occurs before `ORDER BY`, `LIMIT`, and `SELECT DISTINCT`."*

★ **결과가 같다고 같은 일이 아니다.** 「접는 것이 목적」이면 `GROUP BY` 가 맞다([26번](../26-window-functions-vs-aggregates/) 12번).

★ **출력 순서가 두 엔진에서 다른 것은 `ORDER BY` 를 안 적었기 때문**이다 — **순서에 아무 보장이 없다**([08번](../08-order-by-null-position-stability/) 6번).\
`DISTINCT` 가 순서를 정해 주지 않는다.

---

### 11. `WINDOW w AS (...)` 로 정의하고 `OVER w` 로 쓴다 — 자리는 **`HAVING` 뒤, `ORDER BY` 앞**

**출력**

```text
### SQL: SELECT name, salary, SUM(salary) OVER w AS s, AVG(salary) OVER w AS a, COUNT(*) OVER w AS c
         FROM emp8 WINDOW w AS (PARTITION BY dept_id ORDER BY id) ORDER BY id;
--- PG 18.6 ---
 name | salary |  s   |          a           | c
------+--------+------+----------------------+---
 ann  |    300 |  300 | 300.0000000000000000 | 1
 bob  |    500 |  800 | 400.0000000000000000 | 2
 cho  |   NULL | NULL |                 NULL | 1
 dan  |    400 |  400 | 400.0000000000000000 | 1
 eve  |    300 | 1100 | 366.6666666666666667 | 3
 fay  |    500 | 1600 | 400.0000000000000000 | 4
 gus  |    400 |  400 | 400.0000000000000000 | 2
 hui  |    400 |  800 | 400.0000000000000000 | 3
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+------+----------+---+
| name | salary | s    | a        | c |
+------+--------+------+----------+---+
| ann  |    300 |  300 | 300.0000 | 1 |
| bob  |    500 |  800 | 400.0000 | 2 |
| cho  |   NULL | NULL |     NULL | 1 |
| dan  |    400 |  400 | 400.0000 | 1 |
| eve  |    300 | 1100 | 366.6667 | 3 |
| fay  |    500 | 1600 | 400.0000 | 4 |
| gus  |    400 |  400 | 400.0000 | 2 |
| hui  |    400 |  800 | 400.0000 | 3 |
+------+--------+------+----------+---+
```

**왜 그런가 — 그리고 상속도 된다**

```text
SELECT ...
FROM ...
[WHERE ...] [GROUP BY ...] [HAVING ...]
WINDOW w AS (...)            <- 여기다
ORDER BY ...
LIMIT ...
```

```text
### SQL: SELECT name, SUM(salary) OVER (w1 ORDER BY id) AS s FROM emp8 WINDOW w1 AS (PARTITION BY dept_id) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name |  s                       +------+------+
------+------                    | name | s    |
 ann  |  300                     +------+------+
 bob  |  800                     | ann  |  300 |
 cho  | NULL                     | bob  |  800 |
 dan  |  400                     | cho  | NULL |
 eve  | 1100                     | dan  |  400 |
 fay  | 1600                     | eve  | 1100 |
 gus  |  400                     | fay  | 1600 |
 hui  |  800                     | gus  |  400 |
(8 rows)                         | hui  |  800 |
                                 +------+------+
```

★ **`OVER (w1 ORDER BY id)` 는 「`w1` 에 순서를 덧붙인 창**」이다.\
`WINDOW` 절 안에서도 상속이 된다 — `WINDOW w1 AS (PARTITION BY dept_id), w2 AS (w1 ORDER BY id)` 가 양쪽에서 돌았다.

★ **`WINDOW` 절은 문법 설탕이 아니라 오타 방지 장치다.** `OVER (...)` 를 복사해 붙이면\
한 글자 차이로 **다른 창**이 되고, 결과는 **에러 없이** 달라진다.

★ **이름은 창이지 열이 아니다.** `SELECT w` 같은 것은 안 된다. 쓸 수 있는 자리는 `OVER` 뒤뿐이다.

첫 출력의 `cho` 행이 `a`=`NULL` 인데 `c`=1 인 것도 읽을거리다 — **행은 하나 있고 값이 `NULL`** 이다([21번](../21-aggregate-functions-count-forms/) 3번).

---

### 12. 둘 다 에러인데 **뜻이 다르다** — PG 는 문법에 없고, MySQL 은 **문법에 있는데 실행 경로가 없다**

**출력**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn FROM emp8 QUALIFY rn <= 2;
--- PG 18.6 ---
ERROR:  syntax error at or near "rn"
LINE 7: ... (ORDER BY salary DESC, id) AS rn FROM emp8 QUALIFY rn <= 2;
                                                               ^
--- MySQL 8.4.10 ---
ERROR 6037 (HY000) at line 1: 'QUALIFY clause' can be used only if the hypergraph optimizer is enabled.
```

**MySQL 이 시키는 대로 켜 보면 한 겹 더 막힌다.**

```text
### SQL: SET SESSION optimizer_switch='hypergraph_optimizer=on'; (위 질의)
--- MySQL 8.4.10 ---
ERROR 3999 (42000) at line 1: The hypergraph optimizer does not yet support 'use in non-debug builds'
```

**PG 의 에러는 다른 뜻이다.**

```text
### SQL: SELECT 1 QUALIFY 2;
--- PG 18.6 ---
ERROR:  syntax error at or near "2"
LINE 1: SELECT 1 QUALIFY 2;
                         ^
--- MySQL 8.4.10 ---
ERROR 6037 (HY000) at line 1: 'QUALIFY clause' can be used only if the hypergraph optimizer is enabled.
```

  ★ **이 보조 실험에서 근거가 되는 것은 PG 쪽 출력뿐이다.** MySQL 은 절을 아는 쪽이라  같은 `ERROR 6037` 을 한 번 더 낼 뿐, 「별칭으로 먹혔나」를 말해 주지 않는다.

**왜 그런가**

```text
PG    : QUALIFY 를 "열 별칭" 으로 읽어 버린다
        -> SELECT 1 QUALIFY  까지는 통과 (1 에 QUALIFY 라는 별명을 붙였다)
        -> 그다음 낱말 2 에서 막힌다
        => 문법에 QUALIFY 절이 없다

MySQL : 파서가 'QUALIFY clause' 라고 이름을 부른다
        -> 문법에는 있다
        -> 실행할 옵티마이저가 없다 (그리고 그 옵티마이저는 비디버그 빌드에서 못 켠다)
```

★★ **「미지원」을 단정하기 전에 던져 본 값이 여기 있다.** 「둘 다 없다」로 뭉뚱그리면\
**MySQL 이 이미 파서에 그 절을 갖고 있다**는 사실을 놓친다. `ERROR 6037` 은 그 사실의 증거다.

★ **`yet` 이 붙은 메시지는 「다음 버전에서 다시 찍을 자리」 표시다.**\
[28번](../28-window-frames-rows-range-groups/)의 `GROUPS`·`EXCLUDE`, [30번](../30-offset-and-boundary-functions/)의 `IGNORE NULLS` 와 같은 성격이다.

★ **결론은 실무적으로 같다 — 지금은 두 엔진 다 감싸야 한다**(5번).

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `WHERE`·`HAVING`·`GROUP BY` (1번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **전부 에러 — PG 는 절 이름, MySQL 은 `3593` 하나** |
| `ORDER BY` 에서 허용 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 통과. 행 순서만 갈렸다 |
| ★ `WHERE` 가 창을 줄인다 (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`c` 가 5 대 8** |
| 서브쿼리·CTE 우회 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **두 형태가 같은 답** |
| ★ 감싼 뒤의 결과 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG `cho`·`bob` / MySQL `bob`·`fay`** |
| `LIMIT` 과의 대비 (7·8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 창이 하나면 같은 답 |
| 집계 위의 윈도우 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 창이 3행 |
| `DISTINCT` 와의 순서 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 3행. **출력 순서는 보장 없음** |
| `WINDOW` 절·상속 (11번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 이름 창 · `OVER (w1 ...)` · `w2 AS (w1 ...)` |
| ★ `QUALIFY` (12번) | PG 18.6 · MySQL 8.4.10 | 각 2회 + MySQL 1회 | **`ERROR 6037` → `ERROR 3999` → PG 별칭 확인** |

**구현 의존 항목** — **에러 메시지 문구**와 **`NULL` 위치가 만든 결과 차이**(6번),\
그리고 `ORDER BY` 없는 질의의 **출력 순서**(10번).

**방언 항목** — 12번(`QUALIFY` 를 PG 는 모르고 MySQL 은 안다)과 에러 메시지의 구체성.\
**6번은 이 주제의 방언이 아니다** — [08번](../08-order-by-null-position-stability/)의 규칙이 드러난 것이다.\
**언어 보장 항목** — 1\~5·7\~11번. **평가 시점 자체는 두 엔진이 완전히 같았다.**\
두 문서가 「`SELECT` 와 `ORDER BY` 에서만」·「`DISTINCT`·`ORDER BY`·`LIMIT` 보다 먼저」를 같은 모양으로 적는다.

**버전** — `WINDOW` 절은 PG 8.4 · MySQL 8.0 부터다.\
다음 버전에서 다시 찍을 것은 **12번**이다 — MySQL 이 *"does not **yet** support"* 라고 답했다.

**재지 않은 것** — 감싸기의 비용, `LIMIT` 이 정렬을 줄이는지. **계획을 찍지 않았으므로 적지 않았다.**\
**던져 보지 않은 것** — 겹을 둘 이상 쌓은 형태(「윈도우로 거르고 다시 윈도우」). 형태만 적었고, CTE 규칙은 [목록의 **32번 주제**](../32-cte-with-clause/)가 정본이다.
