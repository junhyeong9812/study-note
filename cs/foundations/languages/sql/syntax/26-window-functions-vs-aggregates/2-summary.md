# sql/26-윈도우 함수의 개념 — 집계와 무엇이 다른가 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Window Functions (튜토리얼)](https://www.postgresql.org/docs/18/tutorial-window.html) · [PostgreSQL 18 · Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 · Window Functions](https://dev.mysql.com/doc/refman/8.4/en/window-functions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — 윈도우 함수는 **PG 8.4 부터** · **MySQL 8.0 부터**다(MySQL 5.7 에는 없다).\
> 이 주제에서 두 엔진의 **결과가 갈린 자리는 없다** — 갈린 것은 에러 메시지뿐이다(6번).\
> **선행** — [21 집계 함수와 `COUNT` 의 세 형태](../21-aggregate-functions-count-forms/) · [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/).\
> **이 주제는 그 둘과의 대비가 본문이다** — 「접는다」와 「안 접는다」.\
> **뒤 주제** — [27 PARTITION BY 와 윈도우 ORDER BY](../27-partition-by-and-window-order-by/) · [28 프레임](../28-window-frames-rows-range-groups/) · [29 순위 함수](../29-ranking-functions/) · [30 오프셋·경계 함수](../30-offset-and-boundary-functions/) · [31 평가 시점](../31-window-evaluation-timing/).

## 한눈에 — 쉽게 말하면

**성적표를 걷어서 반 평균을 구하는 두 가지 방법이 있다.**

- 방법 A — 종이를 전부 걷어 **한 장으로 접고** 거기에 「반 평균 400」이라고 적는다.\
  개인 성적은 사라진다. 이게 `GROUP BY` + 집계다.
- 방법 B — 종이를 **그대로 두고** 각자의 종이 귀퉁이에 「반 평균 400」을 **도장처럼 찍는다**.\
  8장은 그대로 8장이다. 이게 윈도우 함수다.

방법 B 라야 「**내 점수 - 반 평균**」을 같은 종이에서 계산할 수 있다.\
방법 A 는 개인 점수를 이미 버렸으므로 그 뺄셈을 할 종이가 없다.

| 비유 | 실체 | `emp8` 8행에 대고 실행하면 |
|---|---|---|
| 종이를 한 장으로 접는다 | `SELECT AVG(salary) FROM emp8` | 결과 **1행** |
| 종이마다 도장을 찍는다 | `SELECT name, AVG(salary) OVER () FROM emp8` | 결과 **8행**, 모든 행에 `400` |
| 도장 찍고 바로 빼 본다 | `salary - AVG(salary) OVER ()` | 행마다 `-100`·`100`·`0` … |

```text
집계 (GROUP BY)                       윈도우 (OVER)
입력 8행                              입력 8행
+------+--------+                     +------+--------+
| ann  |    300 | ─┐                  | ann  |    300 | -> 400 을 붙여 준다
| bob  |    500 |  │                  | bob  |    500 | -> 400
| cho  |   NULL |  │                  | cho  |   NULL | -> 400
| dan  |    400 |  ├─> 접는다          | dan  |    400 | -> 400
| eve  |    300 |  │                  | eve  |    300 | -> 400
| fay  |    500 |  │                  | fay  |    500 | -> 400
| gus  |    400 |  │                  | gus  |    400 | -> 400
| hui  |    400 | ─┘                  | hui  |    400 | -> 400
+------+--------+                     +------+--------+
       v                                     v
   1행 [400]                            8행 (원래 행 + 열 하나)
   원래 행은 사라진다                     원래 행이 그대로 남는다
```

PG 문서가 이 대비를 한 문장으로 적는다 —
*"window functions do not cause rows to become grouped into a single output row like non-window aggregate calls would. Instead, the rows retain their separate identities."*\
MySQL 문서도 같다 — *"whereas an aggregate operation groups query rows into a single result row, a window function produces a result for each query row."*

> **윈도우 함수(window function)** — 행을 **접지 않고**, 행마다 「관련된 행 묶음」을 보고 값 하나를 붙이는 계산.\
> 예: `AVG(salary) OVER ()` 는 8행을 그대로 두고 8행 전부에 `400` 을 붙인다.

> **창(window)** — 한 행이 값을 계산할 때 **들여다보는 행 묶음**.\
> 예: `OVER ()` 는 빈 창 — 「이 질의가 내놓을 행 전부」가 창이다.

## 이 주제가 답하려는 질문

1. **집계와 윈도우는 무엇이 다른가?** — 「행을 접느냐 안 접느냐」 한 줄이고, 나머지는 전부 그 결과다.
2. **`OVER ()` 라는 빈 괄호는 무엇을 뜻하나?** — 「창을 안 나눈다」 = 결과 행 전부가 한 창이다.
3. **`GROUP BY` 로 못 푸는 요구는 무엇이고 왜 못 푸나?** — 「행마다 전체와 비교」는 접은 뒤에는 할 수 없다.

## 예시 데이터 — 이 묶음이 공유하는 것

26~31 여섯 주제는 **`study` DB 의 `emp`·`dept` 두 표를 그대로** 쓴다. 새 표는 만들지 않았다.\
다만 **윈도우는 4행으로는 좁다** — 동률·프레임·순위가 보이려면 행이 더 필요하다.\
그래서 표를 만드는 대신 **CTE 로 4행을 얹어 `emp8` 을 만든다.**

```sql
WITH emp8 AS (
  SELECT id, name, dept_id, salary FROM emp
  UNION ALL SELECT 5, 'eve', 10, 300
  UNION ALL SELECT 6, 'fay', 10, 500
  UNION ALL SELECT 7, 'gus', 20, 400
  UNION ALL SELECT 8, 'hui', 20, 400
)
```

`VALUES (…),(…)` 행 생성자를 쓰지 않은 이유가 있다 — **두 엔진이 서로의 문법을 정확히 거부한다**([10번](../10-from-clause-aliases-derived-tables/)).\
`UNION ALL` 은 양쪽에서 한 글자도 안 고치고 돈다. 아래 모든 질의가 이 CTE 로 시작한다.

```text
emp (표 — 그대로)                   dept (표 — 그대로)
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

emp8 (CTE — emp 4행 + UNION ALL 로 얹은 4행)
+----+------+---------+--------+
| id | name | dept_id | salary |
+----+------+---------+--------+
|  1 | ann  |      10 |    300 |  \
|  2 | bob  |      10 |    500 |   |  emp 표 그대로 (cho·dan 의 NULL 이 여기 있다)
|  3 | cho  |      20 |   NULL |   |
|  4 | dan  |    NULL |    400 |  /
|  5 | eve  |      10 |    300 |  \
|  6 | fay  |      10 |    500 |   |  CTE 가 얹은 4행 (동률을 만들려고 넣었다)
|  7 | gus  |      20 |    400 |   |
|  8 | hui  |      20 |    400 |  /
+----+------+---------+--------+
```

**왜 이 데이터가 윈도우 주제에 맞는가** — 넷을 일부러 심었다.

- **동률이 세 덩어리다** — `300`(ann·eve) · `400`(dan·gus·hui) · `500`(bob·fay).\
  동률이 없으면 [29번](../29-ranking-functions/)의 `RANK`·`DENSE_RANK`·`ROW_NUMBER` 가 **전부 같은 값**을 내서 셋을 구분할 수 없다.\
  [28번](../28-window-frames-rows-range-groups/)의 `ROWS` 대 `RANGE` 도 **동률이 있어야만 갈린다.**
- **`salary` 에 `NULL` 이 하나 있다**(`cho`) — 창 안에서 `NULL` 이 앞에 서는지 뒤에 서는지가 두 엔진에서 갈린다([08번](../08-order-by-null-position-stability/)).
- **`dept_id` 에 `NULL` 이 하나 있다**(`dan`) — `PARTITION BY dept_id` 가 `NULL` 을 **한 칸으로 묶는다**([27번](../27-partition-by-and-window-order-by/)).
- **행이 8개다** — `NTILE(3)` 이 `3/3/2` 로 갈려 **나머지를 어디에 붙이나**가 보인다([29번](../29-ranking-functions/)).

`dept` 의 `hr`(사원 0명)은 이 주제 5번에서 다시 쓴다 — **창에 「조인이 만든 행」이 섞이는 자리**다.

## 동작 방식

이 절의 과녁은 하나다 — **「접는다」와 「안 접는다」가 결과의 어디를 바꾸는가.**

---

### 1. ★ 집계는 행을 접고, 윈도우는 접지 않는다

**언제 쓰나** — 「전체 평균」 같은 값을 **원래 행 옆에 놓고 싶을 때**. 즉 비교가 필요할 때마다.

```text
SELECT AVG(salary) FROM emp8;          SELECT name, AVG(salary) OVER () FROM emp8;

  8행 -> [접는다] -> 1행                  8행 -> [열을 하나 붙인다] -> 8행
                                          행 수가 변하지 않는 것이 정의다
```

```text
### SQL: SELECT AVG(salary) AS avg_sal FROM emp8;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
       avg_sal                   +----------+
----------------------           | avg_sal  |
 400.0000000000000000            +----------+
(1 row)                          | 400.0000 |
                                 +----------+
```

```text
### SQL: SELECT name, salary, AVG(salary) OVER () AS avg_sal FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | salary |       avg_sal
------+--------+----------------------
 ann  |    300 | 400.0000000000000000
 bob  |    500 | 400.0000000000000000
 cho  |   NULL | 400.0000000000000000
 dan  |    400 | 400.0000000000000000
 eve  |    300 | 400.0000000000000000
 fay  |    500 | 400.0000000000000000
 gus  |    400 | 400.0000000000000000
 hui  |    400 | 400.0000000000000000
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+----------+
| name | salary | avg_sal  |
+------+--------+----------+
| ann  |    300 | 400.0000 |
| bob  |    500 | 400.0000 |
| cho  |   NULL | 400.0000 |
| dan  |    400 | 400.0000 |
| eve  |    300 | 400.0000 |
| fay  |    500 | 400.0000 |
| gus  |    400 | 400.0000 |
| hui  |    400 | 400.0000 |
+------+--------+----------+
```

그림 해설 — **같은 `AVG(salary)` 인데 `OVER ()` 다섯 글자가 붙자 결과가 1행에서 8행이 됐다.**\
값은 둘 다 `400` 으로 같다. 달라진 것은 **행 수**뿐이고, 이 주제는 그 한 가지가 전부다.\
소수 자릿수가 다른 것은 `AVG` 의 결과 타입 차이다([21번](../21-aggregate-functions-count-forms/) 2번과 같은 자리 — 값은 같다).

비용 — 윈도우 함수는 **정렬이나 해시를 한 겹 더** 쓴다. 대신 원본 행을 다시 조인해 붙이는 수고가 없어진다.\
(어느 쪽이 빠른지는 **이 주제에서 측정하지 않았다.** 적지 않는다.)

---

### 2. `OVER ()` — 빈 창은 「나누지 않은 한 창」이다

**언제 쓰나** — 전체에 대한 값(합계·평균·건수)을 **행마다** 붙일 때.

```text
OVER ( 여기에 세 가지를 적을 수 있다 )
        │
        ├── PARTITION BY ...   창을 나눈다      (27번)
        ├── ORDER BY ...       창 안에 줄을 세운다 (27번)
        └── ROWS/RANGE/GROUPS  창 안에서 볼 범위  (28번)

OVER ()  = 셋을 다 안 적었다 = "질의가 내놓을 행 전부가 한 창"
```

```text
### SQL: SELECT name, salary, COUNT(*) OVER () AS rows_in_window, SUM(salary) OVER () AS total,
                salary - AVG(salary) OVER () AS diff
         FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | salary | rows_in_window | total |         diff
------+--------+----------------+-------+-----------------------
 ann  |    300 |              8 |  2800 | -100.0000000000000000
 bob  |    500 |              8 |  2800 |  100.0000000000000000
 cho  |   NULL |              8 |  2800 |                  NULL
 dan  |    400 |              8 |  2800 |    0.0000000000000000
 eve  |    300 |              8 |  2800 | -100.0000000000000000
 fay  |    500 |              8 |  2800 |  100.0000000000000000
 gus  |    400 |              8 |  2800 |    0.0000000000000000
 hui  |    400 |              8 |  2800 |    0.0000000000000000
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+----------------+-------+-----------+
| name | salary | rows_in_window | total | diff      |
+------+--------+----------------+-------+-----------+
| ann  |    300 |              8 |  2800 | -100.0000 |
| bob  |    500 |              8 |  2800 |  100.0000 |
| cho  |   NULL |              8 |  2800 |      NULL |
| dan  |    400 |              8 |  2800 |    0.0000 |
| eve  |    300 |              8 |  2800 | -100.0000 |
| fay  |    500 |              8 |  2800 |  100.0000 |
| gus  |    400 |              8 |  2800 |    0.0000 |
| hui  |    400 |              8 |  2800 |    0.0000 |
+------+--------+----------------+-------+-----------+
```

그림 해설 — ★ **`diff` 열이 이 주제가 존재하는 이유다.**\
`salary` 와 `AVG(salary) OVER ()` 가 **같은 행에 동시에 살아 있어야** 뺄셈이 된다.\
`GROUP BY` 로 접으면 `salary` 가 이미 사라졌으므로 그 뺄셈을 할 자리가 없다(3번에서 에러로 확인한다).

**`cho` 의 `diff` 가 `NULL`** 인 것에 주목하라 — `NULL - 400` 은 `NULL` 이다([04번](../04-null-three-valued-logic/)).\
「평균에서 얼마나 벗어났나」를 물었을 때 **급여가 없는 사람은 답이 없다**는 뜻이지 0이 아니다.

비용 — 창을 안 나누면 결과 행 전부를 한 번 훑어 값을 만들고, 그 값을 모든 행에 복사한다.

---

### 3. `GROUP BY` 로는 못 하는 것 — 접은 다음에는 원래 행이 없다

**언제 쓰나** — 「행마다 전체와 비교」·「내 부서에서 내 등수」 같은 요구를 받았을 때.

```text
요구: "사원마다 이름과 급여를 보여 주고, 옆에 전체 평균을 붙여라"

GROUP BY 로 하면          SELECT name, salary, AVG(salary) FROM emp8 GROUP BY ??
                                 ^^^^  ^^^^^^
                          그룹 키가 아닌 열은 SELECT 에 둘 수 없다 -> 에러
```

```text
### SQL: SELECT name, dept_id, salary FROM emp8 GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  column "emp8.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 7: ) SELECT name, dept_id, salary FROM emp8 GROUP BY dept_id;
                 ^
--- MySQL 8.4.10 ---
ERROR 1055 (42000) at line 1: Expression #1 of SELECT list is not in GROUP BY clause and contains nonaggregated column 'emp8.name' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

★ **이 에러가 [22번](../22-group-by-nonaggregated-columns/)의 규칙 그대로다** — 그룹 키가 결과 행을 정의하므로, 그룹 안에서 여러 값을 가질 수 있는 열은 못 내놓는다.\
**윈도우에는 이 규칙 자체가 없다.** 접지 않으니 「그룹 안의 여러 값」이라는 상황이 생기지 않는다.

```text
### SQL: SELECT name, dept_id, COUNT(*) OVER (PARTITION BY dept_id) AS c,
                SUM(salary) OVER (PARTITION BY dept_id) AS s
         FROM emp8 ORDER BY dept_id, id;
--- PG 18.6 ---
 name | dept_id | c |  s
------+---------+---+------
 ann  |      10 | 4 | 1600
 bob  |      10 | 4 | 1600
 eve  |      10 | 4 | 1600
 fay  |      10 | 4 | 1600
 cho  |      20 | 3 |  800
 gus  |      20 | 3 |  800
 hui  |      20 | 3 |  800
 dan  |    NULL | 1 |  400
(8 rows)
--- MySQL 8.4.10 ---
+------+---------+---+------+
| name | dept_id | c | s    |
+------+---------+---+------+
| dan  |    NULL | 1 |  400 |
| ann  |      10 | 4 | 1600 |
| bob  |      10 | 4 | 1600 |
| eve  |      10 | 4 | 1600 |
| fay  |      10 | 4 | 1600 |
| cho  |      20 | 3 |  800 |
| gus  |      20 | 3 |  800 |
| hui  |      20 | 3 |  800 |
+------+---------+---+------+
```

그림 해설 — `name` 이 그대로 있고 부서별 합계가 **행마다 붙었다.** 같은 요구를 `GROUP BY` 로 쓰면 위 에러가 난다.\
**두 엔진의 값은 한 자리도 안 갈렸다.** 갈린 것은 `dan`(부서 `NULL`) 행의 **위치**뿐이다 —\
PG 는 `ORDER BY dept_id` 에서 `NULL` 을 뒤에, MySQL 은 앞에 놓는다([08번](../08-order-by-null-position-stability/)). **창이 아니라 출력 정렬의 문제다.**

비용 — 부서별 합계를 `GROUP BY` 로 따로 구해 **다시 조인**하는 것과 결과가 같다. 윈도우는 그 조인을 없앤다.

---

### 4. 둘을 같이 쓸 수 있다 — 윈도우는 **접힌 뒤의 행** 위에서 돈다

**언제 쓰나** — 「부서별 인원수」를 뽑고 그 **옆에 전체 인원수·그룹 개수**를 붙일 때.

```text
FROM -> WHERE -> GROUP BY -> HAVING -> [여기서 행이 3개로 접혔다] -> SELECT
                                                                      │
                                                    윈도우는 이 3행을 입력으로 받는다
```

```text
### SQL: SELECT dept_id, COUNT(*) AS c, SUM(COUNT(*)) OVER () AS total_rows,
                COUNT(*) OVER () AS group_cnt
         FROM emp8 GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---
 dept_id | c | total_rows | group_cnt
---------+---+------------+-----------
      10 | 4 |          8 |         3
      20 | 3 |          8 |         3
    NULL | 1 |          8 |         3
(3 rows)
--- MySQL 8.4.10 ---
+---------+---+------------+-----------+
| dept_id | c | total_rows | group_cnt |
+---------+---+------------+-----------+
|    NULL | 1 |          8 |         3 |
|      10 | 4 |          8 |         3 |
|      20 | 3 |          8 |         3 |
+---------+---+------------+-----------+
```

그림 해설 — ★ **`COUNT(*) OVER ()` 가 8이 아니라 3이다.**\
윈도우의 입력은 「표의 행」이 아니라 「**`GROUP BY` 가 내놓은 행**」이기 때문이다. 그 행은 3개다.\
`SUM(COUNT(*)) OVER ()` 는 **집계 결과를 윈도우가 다시 더한** 것이라 8이 나온다 — 이것이 창이 보는 값이다.

**[21번](../21-aggregate-functions-count-forms/) 5번의 `AVG(COUNT(*))` 는 에러였다.** 집계 안에 집계는 못 넣는다.\
그런데 **윈도우 안에 집계는 된다.** 두 계산이 같은 단계에 있지 않기 때문이다 — 자세한 순서는 [31번](../31-window-evaluation-timing/).

비용 — 없다. 접힌 3행 위에서 도는 계산이라 입력이 이미 작다.

---

### 5. 창에 「조인이 만든 행」이 섞인다 — `hr` 함정은 윈도우에도 그대로 있다

**언제 쓰나** — 외부 조인 결과에 윈도우를 얹을 때. [21번](../21-aggregate-functions-count-forms/) 4번과 **같은 함정**이다.

```text
dept LEFT JOIN emp8 의 창(PARTITION BY d.id)

 sales : ann bob eve fay      -> 4행, 전부 진짜 사원
 dev   : cho gus hui          -> 3행, 전부 진짜 사원
 hr    : (NULL)               -> 1행, 조인이 만든 빈 행   <- 사원은 0명인데 창에 1행이 있다
```

```text
### SQL: SELECT d.name AS dept, e.name AS emp, COUNT(*) OVER (PARTITION BY d.id) AS star,
                COUNT(e.id) OVER (PARTITION BY d.id) AS emp_cnt
         FROM dept d LEFT JOIN emp8 e ON e.dept_id = d.id ORDER BY d.id, e.id;
--- PG 18.6 ---
 dept  | emp  | star | emp_cnt
-------+------+------+---------
 sales | ann  |    4 |       4
 sales | bob  |    4 |       4
 sales | eve  |    4 |       4
 sales | fay  |    4 |       4
 dev   | cho  |    3 |       3
 dev   | gus  |    3 |       3
 dev   | hui  |    3 |       3
 hr    | NULL |    1 |       0
(8 rows)
--- MySQL 8.4.10 ---
+-------+------+------+---------+
| dept  | emp  | star | emp_cnt |
+-------+------+------+---------+
| sales | ann  |    4 |       4 |
| sales | bob  |    4 |       4 |
| sales | eve  |    4 |       4 |
| sales | fay  |    4 |       4 |
| dev   | cho  |    3 |       3 |
| dev   | gus  |    3 |       3 |
| dev   | hui  |    3 |       3 |
| hr    | NULL |    1 |       0 |
+-------+------+------+---------+
```

그림 해설 — ★ **`hr` 행에서 `star`=1, `emp_cnt`=0 이다.** 창에 행이 하나 있지만 **사원은 없다.**\
윈도우로 바꿨다고 이 함정이 사라지지 않는다 — **「행을 세나, 값이 있는 것을 세나」는 집계 때와 똑같은 질문**이다.\
규칙도 같다: **상대 측의 `NULL` 일 수 없는 열(보통 기본키)을 센다.**

비용 — 열을 하나 더 골라야 한다. 그 대신 0명인 부서가 0으로 나온다.

---

### 6. 윈도우 안에 윈도우는 못 넣는다 — 집계와 규칙이 같다

**언제 쓰나** — 「누적합의 누적합」처럼 **두 단계 윈도우**를 한 문에 쓰려 할 때.

```text
### SQL: SELECT name, SUM(SUM(salary) OVER ()) OVER () AS x FROM emp8;
--- PG 18.6 ---
ERROR:  window function calls cannot be nested
LINE 7: ) SELECT name, SUM(SUM(salary) OVER ()) OVER () AS x FROM em...
                           ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'sum' in this context.'
```

**집계 안에 윈도우를 넣는 것도 거부한다.** 방향이 반대인데 결과도 반대가 아니다.

```text
### SQL: SELECT SUM(ROW_NUMBER() OVER ()) FROM emp8;
--- PG 18.6 ---
ERROR:  aggregate function calls cannot contain window function calls
LINE 7: ) SELECT SUM(ROW_NUMBER() OVER ()) FROM emp8;
                     ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'row_number' in this context.'
```

그림 해설 — **되는 방향은 하나뿐이다.**

```text
 SUM( COUNT(*) OVER () )  ->  에러   집계 안에 윈도우 : 안 된다
 SUM( COUNT(*) )  OVER () ->  된다   윈도우 안에 집계 : 된다 (4번에서 8 이 나왔다)
 SUM( SUM(...) OVER () ) OVER () -> 에러  윈도우 안에 윈도우 : 안 된다
```

★ **PG 는 무엇이 문제인지 말하고**(`cannot be nested` / `cannot contain window function calls`),\
**MySQL 은 세 경우를 `ERROR 3593` 한 덩어리로 묶는다.** 「거부한다」는 같고 **무엇이라 부르는지**가 다르다.\
([21번](../21-aggregate-functions-count-forms/) 5번의 `ERROR 1111` 과 같은 성격이다 — MySQL 은 자리를 잘못 쓴 함수에 한 메시지를 돌려쓴다.)

**고치는 법** — 한 겹 감싼다. 안쪽 질의의 결과가 바깥에서는 그냥 열이 된다([31번](../31-window-evaluation-timing/)).

비용 — 파생 테이블이 한 겹 늘어난다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
집계함수(인자) OVER ( [PARTITION BY ...] [ORDER BY ...] [프레임] )
순위함수()     OVER ( ... )          -- ROW_NUMBER·RANK·DENSE_RANK·NTILE (29번)
오프셋함수(...) OVER ( ... )          -- LAG·LEAD·FIRST_VALUE·LAST_VALUE (30번)
```

규칙 일곱.

1. **`OVER` 가 붙으면 윈도우 함수다.** 같은 `COUNT`·`SUM`·`AVG` 라도 `OVER` 유무로 성격이 바뀐다.
2. **윈도우는 행을 접지 않는다.** 입력 행 수 = 출력 행 수다. 이것이 정의이고 나머지는 결과다.
3. **`OVER ()` 는 「질의가 내놓을 행 전부」가 한 창**이라는 뜻이다.
4. **`GROUP BY` 가 있으면 윈도우의 입력은 「접힌 뒤의 행**」이다 — `COUNT(*) OVER ()` 가 그룹 수를 센다.
5. **윈도우 안에 집계는 되고, 집계 안에 윈도우는 안 된다.** 윈도우 안에 윈도우도 안 된다.
6. **`NULL` 처리는 집계와 같다** — `AVG`·`SUM` 은 `NULL` 인 입력을 건너뛴다([21번](../21-aggregate-functions-count-forms/)).
7. **윈도우 함수는 `SELECT` 와 `ORDER BY` 에서만 쓸 수 있다.** `WHERE`·`GROUP BY`·`HAVING` 은 안 된다([31번](../31-window-evaluation-timing/)).

실전 형태는 넷이다.

```sql
-- (1) 전체 값을 행마다 붙이기
SELECT name, salary, AVG(salary) OVER () AS avg_all FROM emp8;

-- (2) 전체와 비교하기  <- GROUP BY 로는 불가능한 자리
SELECT name, salary - AVG(salary) OVER () AS diff FROM emp8;

-- (3) 그룹 값을 행마다 붙이기
SELECT name, dept_id, SUM(salary) OVER (PARTITION BY dept_id) AS dept_sum FROM emp8;

-- (4) 집계 결과 위에 다시 윈도우 얹기
SELECT dept_id, COUNT(*) AS c, SUM(COUNT(*)) OVER () AS total FROM emp8 GROUP BY dept_id;
```

## 어디서 틀리나

- **★ 윈도우를 「`GROUP BY` 의 다른 표기」로 안다.**\
  `GROUP BY` 는 행을 **버리고** 윈도우는 **남긴다.** 결과 행 수를 먼저 세어 보면 절대 안 헷갈린다.
- **★ `COUNT(*) OVER ()` 가 언제나 표의 행 수라고 믿는다.**\
  `GROUP BY` 가 있으면 **그룹 수**이고(4번), `WHERE` 가 걸렀으면 **남은 행 수**다([31번](../31-window-evaluation-timing/)).
- **외부 조인 뒤에 `COUNT(*) OVER (...)` 로 「인원수」를 센다.**\
  `hr` 이 0명인데 1로 세어진다(5번). 상대 측 기본키를 센다.
- **집계 안에 윈도우를 넣는다.**\
  `SUM(ROW_NUMBER() OVER ())` 는 두 엔진 모두 에러다. 반대 방향(`SUM(COUNT(*)) OVER ()`)은 된다.
- **윈도우 결과를 `WHERE` 로 거르려 한다.**\
  두 엔진 모두 거부한다. 한 겹 감싸야 한다 — [31번](../31-window-evaluation-timing/)이 정본이다.
- **`NULL` 이 0으로 계산될 거라 믿는다.**\
  `salary - AVG(salary) OVER ()` 는 `cho` 에서 `NULL` 이다. 집계와 같은 규칙이다([21번](../21-aggregate-functions-count-forms/)).
- **MySQL 5.7 을 염두에 두고 쓴다.**\
  윈도우 함수는 **MySQL 8.0 부터**다. 5.7 에는 문법 자체가 없다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 윈도우가 행을 접지 않는다 | **정의** | 언어 — PG *"the rows retain their separate identities"* · MySQL *"produces a result for each query row"* |
| `OVER ()` 가 결과 행 전부를 한 창으로 본다 | **정의** | 언어 — 두 문서가 같은 모양으로 적는다 |
| `GROUP BY` 뒤의 윈도우 입력이 「접힌 행」 | **정의** | 언어 — MySQL 문서가 *"after `WHERE`, `GROUP BY`, and `HAVING` processing"* 이라 적는다 |
| 윈도우 안에 윈도우 금지 | **정의** | 언어 — 두 엔진 모두 거부한다(6번) |
| 거부할 때의 **에러 메시지** | 엔진 | PG 는 세 문장, MySQL 은 `ERROR 3593` 하나다 |
| `AVG` 결과의 소수 자릿수 | 결과 타입의 선택 | 엔진 — PG `numeric` · MySQL `DECIMAL`. **값은 같다** |
| 윈도우 함수의 **도입 버전** | 엔진 | PG 8.4 · MySQL 8.0 |
| 윈도우가 집계보다 빠른가 | **측정 안 함** | 이 주제에서 재지 않았다. 적지 않는다 |

- **이 주제에서 두 엔진의 값이 갈린 자리는 없다.** 갈린 것은 에러 메시지와 `dan` 행의 출력 위치뿐이다.
- 출력 위치 차이는 **창이 아니라 `ORDER BY` 의 `NULL` 규칙**이다([08번](../08-order-by-null-position-stability/)).

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 「행마다 전체(또는 그룹)와 비교**」가 요구에 들어 있을 때. 이게 윈도우의 본령이다.
- **쓴다 — 집계 결과를 다시 조인해 붙이던 질의.** 조인 한 겹이 통째로 없어진다.
- **쓴다 — 순위·이전 행과의 차이.** [29번](../29-ranking-functions/)·[30번](../30-offset-and-boundary-functions/)이 그 자리다.
- **안 쓴다 — 결과를 정말 접어야 할 때.** 「부서별 인원수 3행」이 목적이면 `GROUP BY` 가 맞다.\
  윈도우로 뽑고 `DISTINCT` 로 접는 것은 같은 일을 두 번 하는 것이다.
- **안 쓴다 — 조건으로 거르는 것이 목적일 때.** 윈도우는 거르는 도구가 아니다. 거르려면 한 겹 감싸야 한다([31번](../31-window-evaluation-timing/)).
- **안 쓴다 — MySQL 5.7 을 지원해야 할 때.** 문법이 없다.

## 핵심 문장

- **집계는 행을 접고 윈도우는 접지 않는다.** 이 한 줄이 주제의 전부이고 나머지는 결과다.
- 같은 `AVG(salary)` 가 `OVER ()` 다섯 글자로 **1행에서 8행**이 됐다. 값은 둘 다 400이다.
- ★ **`salary - AVG(salary) OVER ()` 는 `GROUP BY` 로 못 쓴다** — 접으면 `salary` 가 이미 없다.
- `OVER ()` 는 「**질의가 내놓을 행 전부가 한 창**」이라는 뜻이다. 빈 괄호는 「창을 안 나눈다」다.
- ★ **`GROUP BY` 가 있으면 `COUNT(*) OVER ()` 는 그룹 수**다(8이 아니라 3). 윈도우의 입력은 접힌 뒤의 행이다.
- **윈도우 안에 집계는 되고 집계 안에 윈도우는 안 된다.** 윈도우 안에 윈도우도 안 된다.
- 외부 조인 뒤의 **`hr` 함정은 윈도우에도 그대로 있다** — `star`=1, `emp_cnt`=0.
- 윈도우 함수는 **PG 8.4 · MySQL 8.0** 부터다.

## 관련 자료

- [PostgreSQL 18 · Window Functions (튜토리얼)](https://www.postgresql.org/docs/18/tutorial-window.html) — *"the rows retain their separate identities"* 문장이 여기 있다.
- [PostgreSQL 18 · Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) — `OVER` 의 문법과 프레임 기본값.
- [MySQL 8.4 · Window Functions](https://dev.mysql.com/doc/refman/8.4/en/window-functions.html) — *"produces a result for each query row"* 문장.
- [21 집계 함수와 `COUNT` 의 세 형태](../21-aggregate-functions-count-forms/) — **경계: 그쪽은 접는 계산 하나하나의 의미(`NULL`·중복·0행)까지, 여기는 그 계산을 접지 않고 쓰는 것부터.**
- [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) — **경계: 그쪽은 「그룹이 결과 행을 정의한다」와 비집계 열 거부까지, 여기는 그 거부가 왜 윈도우에는 없나부터.**
- [27 PARTITION BY 와 윈도우 ORDER BY](../27-partition-by-and-window-order-by/) — **경계: 여기는 창을 안 나눈 `OVER ()` 까지, 창을 나누고 줄 세우는 것은 거기.**
- [31 윈도우 함수의 평가 시점](../31-window-evaluation-timing/) — **경계: 여기는 「윈도우는 `SELECT` 에서만 쓴다」는 사실까지, 그 이유와 우회는 거기.**
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — 「접는 칸」과 「붙이는 칸」이 어디인지의 좌표계.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `cho` 의 `diff` 가 `NULL` 인 이유.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **윈도우 함수(window function)** — 행을 접지 않고 행마다 값을 붙이는 계산. `OVER (...)` 가 붙는다.\
  예: `AVG(salary) OVER ()` 는 8행을 8행 그대로 두고 8행 모두에 `400` 을 붙인다.
- **창(window)** — 한 행이 계산할 때 들여다보는 행 묶음.\
  예: `OVER ()` 의 창은 「질의가 내놓을 행 전부」 = `emp8` 에서 8행.
- **`OVER` 절** — 창을 어떻게 만들지 적는 자리. `PARTITION BY`·`ORDER BY`·프레임 셋을 적을 수 있다.\
  예: `OVER ()` 는 셋을 다 안 적은 것이다.
- **접는다(collapse/group)** — 여러 행을 결과 한 행으로 합치는 것. 집계의 본질이다.\
  예: `GROUP BY dept_id` 는 8행을 3행으로 접는다.
- **집계 함수(aggregate function)** — 여러 행을 값 하나로 접는 함수.\
  예: `SUM(salary)` 는 8행의 급여를 `2800` 하나로 접는다.
- **`PARTITION BY`** — 창을 여러 칸으로 나누는 지시. 계산은 칸 안에서만 일어난다.\
  예: `PARTITION BY dept_id` 는 창을 `10`·`20`·`NULL` 세 칸으로 나눈다([27번](../27-partition-by-and-window-order-by/)).
- **중첩(nesting)** — 함수 안에 같은 종류의 함수를 넣는 것.\
  예: `SUM(SUM(salary) OVER ()) OVER ()`. 두 엔진 모두 거부한다.
- **조인이 만든 `NULL`(join-generated NULL)** — 원본에 없었는데 외부 조인이 채워 넣은 `NULL`.\
  예: `hr` 행의 `e.id`. 그래서 `COUNT(e.id) OVER (...)` 가 0이다.
- **`sql_mode`** — MySQL 의 문법·검사 엄격도 설정 묶음.\
  예: `only_full_group_by` 가 3번의 `ERROR 1055` 를 내는 주체다. 8.4 기본값에 들어 있다.

## 더 들어가면

- **왜 윈도우 함수가 늦게 들어왔나.** 집계는 행을 버리면서 계산할 수 있지만 윈도우는 **원본 행을 붙들고** 있어야 한다.\
  정렬 버퍼나 해시를 한 겹 더 써야 하고, 그래서 MySQL 에는 8.0(2018)에야 들어왔다.
- **`OVER ()` 와 상관 서브쿼리의 관계.** `(SELECT AVG(salary) FROM emp8)` 로도 같은 열을 만들 수 있다.\
  차이는 **바깥 행마다 다시 도느냐**다 — 상관 서브쿼리의 구조는 [목록의 **11번 주제**](../11-subquery-scalar-correlated-any-all/)가 정본이다.
- **집계 함수는 거의 전부 윈도우로 쓸 수 있다.** `SUM`·`AVG`·`COUNT`·`MIN`·`MAX` 는 물론\
  `STRING_AGG`/`GROUP_CONCAT` 같은 것도 `OVER` 를 받는다. 반대로 **순위 함수는 `OVER` 없이 못 쓴다**([29번](../29-ranking-functions/)).
- **`FILTER (WHERE ...)` 는 윈도우에도 붙는다 — PG 에만.** 던져서 확인했다.

```text
### SQL: SELECT name, salary, SUM(salary) FILTER (WHERE salary > 300) OVER () AS s FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | salary |  s
------+--------+------
 ann  |    300 | 2200
 bob  |    500 | 2200
 cho  |   NULL | 2200
 dan  |    400 | 2200
 eve  |    300 | 2200
 fay  |    500 | 2200
 gus  |    400 | 2200
 hui  |    400 | 2200
(8 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '(WHERE salary > 300) OVER () AS s FROM emp8 ORDER BY id' at line 7
```

  `2200` 은 `300` 인 두 명을 뺀 합이다. MySQL 은 `FILTER` 자체가 없어 **`CASE` 로 쓴다** —\
  그 대비는 [24번](../24-conditional-aggregation-filter-case/)이 정본이고, 여기서는 **`OVER` 와 같이 쓸 수 있다는 사실만** 본다.
