# sql/26-윈도우 함수의 개념 — 집계와 무엇이 다른가 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 모든 질의는 [1-question.md](1-question.md) 머리의 `WITH emp8 AS (...)` CTE 를 앞에 붙여 돌렸다.\
> 문서 근거는 [PG 18 Window Functions](https://www.postgresql.org/docs/18/tutorial-window.html) · [PG 18 Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 Window Functions](https://dev.mysql.com/doc/refman/8.4/en/window-functions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. (A) 1행 · (B) 8행 — 값은 둘 다 400 이다

**출력**

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

**왜 그런가**

```text
 (A) 집계                          (B) 윈도우
 8행 -> [접는다] -> 1행             8행 -> [열을 붙인다] -> 8행
 원래 행이 사라진다                  원래 행이 그대로 남는다
```

★ **달라진 것은 행 수 하나뿐이다.** 값은 둘 다 `400` — 같은 `AVG` 를 같은 8행에 대고 계산했기 때문이다.\
PG 문서가 이 차이를 한 문장으로 적는다: *"window functions do not cause rows to become grouped into a single output row like non-window aggregate calls would. Instead, the rows retain their separate identities."*

소수 자릿수가 다른 것은 `AVG` 결과 타입의 차이다(PG `numeric` · MySQL `DECIMAL`). **값은 같다.**

> **윈도우 함수(window function)** — 행을 접지 않고 행마다 값을 붙이는 계산. `OVER (...)` 가 붙는다.\
> 예: `AVG(salary) OVER ()` 는 8행을 그대로 두고 8행 전부에 `400` 을 붙인다.

---

### 2. 「창을 어떻게 나눌지를 안 적었다」 — 그래서 결과 행 전부가 한 창이다

`OVER` 괄호 안에 쓸 수 있는 것은 셋이다.

```text
OVER ( [PARTITION BY ...] [ORDER BY ...] [ROWS/RANGE/GROUPS ...] )
         창을 나눈다        창 안에 줄을 세운다   창 안에서 볼 범위

OVER ()  = 셋 다 안 적음 = 나누지도, 줄 세우지도, 좁히지도 않는다
         = "이 질의가 내놓을 행 전부"가 창
```

그래서 `COUNT(*) OVER ()` 는 **창의 행 수**를 센다.

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

★ **「결과 행 전부」이지 「표의 행 전부」가 아니다.** `WHERE` 가 걸렀으면 걸러진 뒤가 창이고,\
`GROUP BY` 가 접었으면 접힌 뒤가 창이다(5번). 그 순서는 [31번](../31-window-evaluation-timing/)이 정본이다.

> **창(window)** — 한 행이 값을 계산할 때 들여다보는 행 묶음.\
> 예: `OVER ()` 의 창은 이 질의가 내놓을 8행.

---

### 3. 접는 순간 `salary` 가 없어지기 때문이다

```text
요구: name · salary · (salary - 전체평균) 을 한 행에 놓아라

GROUP BY 로 하면                    윈도우로 하면
8행 -> 접는다 -> 평균 1개            8행 -> 평균을 8행에 붙인다
      ^^^^^^^^                            ^^^^^^^^^^^^^^^^^^
      이때 name·salary 가 버려진다       name·salary 가 살아 있다
      뺄셈할 상대가 없다                  같은 행에서 뺄 수 있다
```

집계 질의에서 그룹 키가 아닌 열을 `SELECT` 에 두면 두 엔진이 거부한다.

```text
### SQL: SELECT name, dept_id, salary FROM emp8 GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  column "emp8.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 7: ) SELECT name, dept_id, salary FROM emp8 GROUP BY dept_id;
                 ^
--- MySQL 8.4.10 ---
ERROR 1055 (42000) at line 1: Expression #1 of SELECT list is not in GROUP BY clause and contains nonaggregated column 'emp8.name' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

★ **이 규칙이 [22번](../22-group-by-nonaggregated-columns/)의 본문이고, 윈도우에는 이 규칙 자체가 없다.**\
「그룹 안에 여러 값이 있는데 어느 것을 내놓을 거냐」라는 질문이 **애초에 생기지 않기 때문**이다 — 행을 안 접으니까.

우회로 `GROUP BY name, dept_id, salary` 를 적으면 에러는 사라지지만 **그룹이 8개**가 되어 평균이 각자 자기 급여가 된다.\
「전체 평균」을 잃는다. 요구를 만족하는 `GROUP BY` 형태는 없다.

> **접는다(collapse)** — 여러 행을 결과 한 행으로 합치는 것.\
> 예: `GROUP BY dept_id` 는 8행을 `10`·`20`·`NULL` 세 행으로 접는다.

---

### 4. `NULL` 이다 — 「평균과 같다」가 아니라 「**답이 없다**」는 뜻이다

2번 출력의 `cho` 행을 보라. `diff` 가 `NULL` 이다.

```text
cho 의 salary = NULL
NULL - 400  ->  NULL        산술에 NULL 이 하나라도 끼면 결과는 NULL 이다

같은 행의 avg_sal 은 400 이다 -- 평균 계산에서는 cho 가 그냥 빠졌을 뿐이다
                                 (AVG 는 NULL 입력을 건너뛴다 — 21번)
```

★ **0 과 `NULL` 을 구분하라.** `dan`·`gus`·`hui` 의 `diff` 는 **0**이고, 이건 「평균과 같다」는 뜻이다.\
`cho` 의 `NULL` 은 「비교할 값이 없다」는 뜻이다. 화면에서는 둘 다 그럴듯해 보이지만 의미가 완전히 다르다.

3값 논리는 [04번](../04-null-three-valued-logic/), 집계가 `NULL` 을 건너뛰는 규칙은 [21번](../21-aggregate-functions-count-forms/)이 정본이다.

---

### 5. `total_rows`=8 · `group_cnt`=3 — 윈도우의 입력은 **접힌 뒤의 3행**이다

**출력**

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

**왜 그런가**

```text
emp8 8행
   |
   v  GROUP BY dept_id
3행 [ (10,4) (20,3) (NULL,1) ]   <- 윈도우가 보는 창은 여기서부터다
   |
   +-- COUNT(*) OVER ()      -> 창의 행 수 = 3        (그룹이 3개)
   +-- SUM(COUNT(*)) OVER () -> 4 + 3 + 1 = 8        (각 그룹의 인원을 다 더함)
```

★ **`COUNT(*) OVER ()` 가 8이 아니라 3인 것이 이 문제의 전부다.**\
「표의 행 수」를 세는 게 아니라 「**윈도우에 들어온 행 수**」를 센다. `GROUP BY` 가 먼저 접었으므로 3이다.

`SUM(COUNT(*)) OVER ()` 는 **윈도우 안에 집계를 넣은 것**이다. 바깥의 `SUM ... OVER ()` 는 접힌 3행의 `c` 값을 더한다.\
MySQL 문서가 그 순서를 적는다: *"Query result rows are determined from the `FROM` clause, after `WHERE`, `GROUP BY`, and `HAVING` processing, and windowing execution occurs before `ORDER BY`, `LIMIT`, and `SELECT DISTINCT`."*

출력 행의 **순서**가 두 엔진에서 다른 것은 `ORDER BY dept_id` 의 `NULL` 규칙 때문이다 — 값은 한 자리도 안 갈렸다([08번](../08-order-by-null-position-stability/)).

---

### 6. (A)만 돈다 — 윈도우 안의 집계는 되고, 나머지 둘은 에러다

**출력**

(A)는 5번 출력의 `total_rows` 열이다 — **8**을 돌려준다.

```text
### SQL: SELECT SUM(ROW_NUMBER() OVER ()) FROM emp8;
--- PG 18.6 ---
ERROR:  aggregate function calls cannot contain window function calls
LINE 7: ) SELECT SUM(ROW_NUMBER() OVER ()) FROM emp8;
                     ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'row_number' in this context.'
```

```text
### SQL: SELECT name, SUM(SUM(salary) OVER ()) OVER () AS x FROM emp8;
--- PG 18.6 ---
ERROR:  window function calls cannot be nested
LINE 7: ) SELECT name, SUM(SUM(salary) OVER ()) OVER () AS x FROM em...
                           ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'sum' in this context.'
```

**왜 그런가**

```text
 SUM( COUNT(*) ) OVER ()        (A) 된다   집계가 먼저 끝나고, 그 결과 위에서 창이 돈다
 SUM( ROW_NUMBER() OVER () )    (B) 에러   집계는 창보다 먼저 계산된다 — 아직 없는 값을 못 받는다
 SUM( SUM(...) OVER () ) OVER () (C) 에러  창은 한 단계다. 같은 단계를 자기 입력으로 못 쓴다
```

★ **되는 방향이 하나뿐인 것은 순서 때문이다** — 집계가 먼저, 윈도우가 나중이다([31번](../31-window-evaluation-timing/)).

★ **두 엔진의 「무엇이라 부르는지」가 다르다.** PG 는 (B)와 (C)에 **서로 다른 문장**을 주고,\
MySQL 은 셋을 `ERROR 3593` 한 덩어리로 묶는다. **거부한다는 사실은 같다 — 방언 차이가 아니라 메시지 차이다.**\
([21번](../21-aggregate-functions-count-forms/) 5번의 `ERROR 1111` 이 같은 성격이었다.)

고치는 법은 **한 겹 감싸는 것**이다.

```sql
SELECT SUM(rn) FROM (SELECT ROW_NUMBER() OVER () AS rn FROM emp8) t;
```

> **중첩(nesting)** — 함수 안에 같은 종류의 함수를 넣는 것.\
> 예: `SUM(SUM(salary) OVER ()) OVER ()`. 두 엔진 모두 거부한다.

---

### 7. `star`=1 · `emp_cnt`=0 — 창에 **조인이 만든 행** 하나가 들어 있다

**출력**

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

**왜 그런가**

```text
hr 의 창
+---------------------+
| d.name='hr'         |   LEFT JOIN 이 짝 없는 hr 을 살리려고
| e.name=NULL         |   오른쪽을 NULL 로 채운 행 하나
| e.id  =NULL         |
+---------------------+
   COUNT(*)     -> 1    행이 하나 있으니까
   COUNT(e.id)  -> 0    e.id 가 NULL 이라 값 체에서 걸린다
```

★ **「행이 있다」와 「사원이 있다」가 다른 질문이다.** 윈도우로 바꿔도 이 함정은 그대로다 —\
[21번](../21-aggregate-functions-count-forms/) 4번에서 집계로 본 것과 **같은 자리이고 같은 답**이다.

두 엔진의 출력이 한 자리도 안 갈렸다.

> **조인이 만든 `NULL`(join-generated NULL)** — 원본에 없었는데 외부 조인이 채워 넣은 `NULL`.\
> 예: `hr` 행의 `e.id`. `emp.id` 는 기본키라 원본에는 `NULL` 이 없다.

---

### 8. 상대 측의 **`NULL` 일 수 없는 열**을 센다 — 보통 기본키다

```text
규칙 한 줄:
  외부 조인 뒤에 "몇 건인가"를 세려면, 원본에 NULL 이 없는 열을 센다.
  그 열이 NULL 이면 그것은 "조인이 만든 행"이라는 뜻이기 때문이다.

emp.id 는 PRIMARY KEY -> 원본에 NULL 이 없다 -> COUNT(e.id) 가 0 이면 사원이 0명이다
```

★ **`e.name` 을 세도 이번에는 맞는다**(`NOT NULL` 이다). 하지만 **기본키가 안전한 기본값**이다 —\
`NOT NULL` 이 나중에 풀리면 조용히 틀리기 시작한다. 「틀려도 에러가 안 나는」 종류의 사고다.

`COUNT` 세 형태의 `NULL` 규칙은 [21번](../21-aggregate-functions-count-forms/)이 정본이다.

---

### 9. `SELECT` 목록과 `ORDER BY` 에만 쓸 수 있다

```text
FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> LIMIT
                                        ^^^^^^                ^^^^^^^^
                                        여기서 계산된다        이미 있으니 쓸 수 있다
         ^^^^^    ^^^^^^^^    ^^^^^^
         아직 계산되지 않았다 -> 쓸 수 없다
```

PG 문서가 그대로 적는다: *"Window functions are permitted only in the `SELECT` list and the `ORDER BY` clause of the query. They are forbidden elsewhere, such as in `GROUP BY`, `HAVING` and `WHERE` clauses."*\
MySQL 문서도 같다: *"Window functions are permitted only in the select list and `ORDER BY` clause."*

★ **거르고 싶으면 한 겹 감싼다.** 안쪽 질의가 「이전 칸」이 되면 바깥에서는 그냥 열이다.\
실제 에러 출력과 우회 형태는 [31번](../31-window-evaluation-timing/)이 정본이다.

---

### 10. PG 는 돌고(2200) MySQL 은 `ERROR 1064` 다

**출력**

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

**왜 그런가**

```text
전체 합계 2800
  - ann 300
  - eve 300
  = 2200      FILTER 가 300 인 두 명을 계산에서 뺀다 (행은 8행 그대로다)
```

★ **`FILTER` 는 「행을 거르는 것」이 아니라 「집계에 넣을 값을 거르는 것」이다.** 출력은 여전히 8행이다.\
MySQL 에는 `FILTER` 문법이 아예 없어 **파서 단계에서 `ERROR 1064`** 다 — `CASE` 로 쓴다.\
그 대비는 [24번](../24-conditional-aggregation-filter-case/)이 정본이고, 여기서 확인한 것은 **`FILTER` 가 `OVER` 와 같이 쓰인다**는 사실이다.

---

### 11. PostgreSQL 8.4 · MySQL 8.0

- **PostgreSQL** — 8.4(2009)부터. 이 배치는 **18.6** 에서 돌렸다.
- **MySQL** — 8.0(2018)부터. **5.7 에는 문법 자체가 없다.** 이 배치는 **8.4.10** 에서 돌렸다.
- `GROUPS` 프레임과 `EXCLUDE` 는 **PG 11 부터**이고 **MySQL 8.4 에는 아직 없다**([28번](../28-window-frames-rows-range-groups/)에서 에러로 확인한다).

★ **「MySQL 8.x 면 다 된다」가 아니다.** 프레임 단위와 `IGNORE NULLS` 는 8.4 에서도 거부된다([30번](../30-offset-and-boundary-functions/)).

---

### 12. 결과를 **정말 접어야** 할 때 — 행 수가 곧 답인 요구

```text
"부서별 인원수를 보여 줘"          -> 결과는 3행이어야 한다   -> GROUP BY
"사원마다 자기 부서 인원수를 보여 줘" -> 결과는 8행이어야 한다   -> 윈도우
```

- **`GROUP BY`** — 원래 행을 **버리는 것이 목적**일 때. 리포트·집계 화면·요약 API.
- **윈도우** — 원래 행을 **남기는 것이 목적**일 때. 비교·순위·이전 행과의 차이.

★ **윈도우로 뽑고 `DISTINCT` 로 접는 것은 같은 일을 두 번 하는 것이다.**\
행 8개를 만들고 다시 3개로 줄이느니 처음부터 3개를 만드는 편이 싸다.\
(다만 `SELECT DISTINCT dept_id, COUNT(*) OVER (PARTITION BY dept_id)` 는 **돈다** — [31번](../31-window-evaluation-timing/)에서 그 순서를 본다.)

판단은 한 줄로 선다 — **「결과가 몇 행이어야 하나」를 먼저 정하고 도구를 고른다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `AVG` 대 `AVG() OVER ()` (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 1행 대 8행 |
| `OVER ()` 의 세 열 (2·4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `diff` 의 `cho` = `NULL` |
| `GROUP BY` 비집계 열 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **둘 다 에러 — 메시지를 그대로 실었다** |
| `GROUP BY` + 윈도우 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `group_cnt`=3 · `total_rows`=8 |
| 중첩 규칙 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 두 종 — PG 는 문장이 둘, MySQL 은 `3593` 하나** |
| `hr` 의 창 (7·8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `dept LEFT JOIN emp8` |
| `FILTER` + `OVER` (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL `ERROR 1064`** |
| 부서별 창 (본문 3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 값 동일, `dan` 행 위치만 다름 |

**구현 의존 항목** — `AVG` 결과의 소수 자릿수(PG `numeric` · MySQL `DECIMAL`)와 **에러 메시지 문구**.\
**값은 두 엔진에서 한 자리도 안 갈렸다.**

**방언 항목** — **10번 하나다.** `FILTER` 는 PG 에만 있다.\
**언어 보장 항목** — 1~9·12번. 「접지 않는다」·`OVER ()` 의 의미·중첩 금지·쓸 수 있는 절은 두 문서가 같은 모양으로 적는다.

**버전** — 윈도우 함수 자체는 PG 8.4 · MySQL 8.0 부터다. 다음 버전에서 다시 확인할 것은 **10번**과,\
[28번](../28-window-frames-rows-range-groups/)·[30번](../30-offset-and-boundary-functions/)에서 MySQL 이 *"doesn't yet support"* 라고 답한 항목들이다 — **`yet` 이라는 낱말이 바뀔 여지를 말하고 있다.**

**재지 않은 것** — 윈도우와 집계의 속도, 윈도우가 쓰는 정렬·해시의 비용. **측정하지 않았으므로 적지 않았다.**
