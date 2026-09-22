# sql/27-`PARTITION BY` 와 윈도우 `ORDER BY` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 모든 질의는 [1-question.md](1-question.md) 머리의 `WITH emp8 AS (...)` CTE 를 앞에 붙여 돌렸다.\
> 문서 근거는 [PG 18 Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 Window Function Frame Specification](https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 8행 그대로다 — `dan` 의 `dept_sum` 은 **400**

**출력**

```text
### SQL: SELECT name, dept_id, salary, SUM(salary) OVER () AS all_sum,
                SUM(salary) OVER (PARTITION BY dept_id) AS dept_sum
         FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | dept_id | salary | all_sum | dept_sum
------+---------+--------+---------+----------
 ann  |      10 |    300 |    2800 |     1600
 bob  |      10 |    500 |    2800 |     1600
 cho  |      20 |   NULL |    2800 |      800
 dan  |    NULL |    400 |    2800 |      400
 eve  |      10 |    300 |    2800 |     1600
 fay  |      10 |    500 |    2800 |     1600
 gus  |      20 |    400 |    2800 |      800
 hui  |      20 |    400 |    2800 |      800
(8 rows)
--- MySQL 8.4.10 ---
+------+---------+--------+---------+----------+
| name | dept_id | salary | all_sum | dept_sum |
+------+---------+--------+---------+----------+
| ann  |      10 |    300 |    2800 |     1600 |
| bob  |      10 |    500 |    2800 |     1600 |
| cho  |      20 |   NULL |    2800 |      800 |
| dan  |    NULL |    400 |    2800 |      400 |
| eve  |      10 |    300 |    2800 |     1600 |
| fay  |      10 |    500 |    2800 |     1600 |
| gus  |      20 |    400 |    2800 |      800 |
| hui  |      20 |    400 |    2800 |      800 |
+------+---------+--------+---------+----------+
```

**왜 그런가**

```text
PARTITION BY dept_id 가 만든 칸

+-- 10 ---------------+  +-- 20 --------+  +-- NULL --+
| ann bob eve fay     |  | cho gus hui  |  | dan      |
| 합 1600             |  | 합 800       |  | 합 400   |
+---------------------+  +--------------+  +----------+
         4행                    3행             1행     = 8행 (한 행도 안 줄었다)
```

★ **`dept_id` 가 `NULL` 인 `dan` 이 버려지지 않고 자기 칸을 차지했다.** 그래서 `dept_sum` 이 400이다.\
`all_sum`(창 하나)과 `dept_sum`(창 셋)이 **같은 질의 안에 나란히** 있는 것도 `GROUP BY` 로는 안 되는 일이다.

> **파티션(partition)** — `PARTITION BY` 가 나눈 창 한 칸. 계산은 칸 안에서만 일어난다.\
> 예: `PARTITION BY dept_id` 는 `emp8` 을 4행·3행·1행 세 칸으로 나눈다.

---

### 2. **「묶기」와 「세기」의 규칙이 정반대**다

```text
세기 (COUNT DISTINCT)              묶기 (PARTITION BY · GROUP BY · DISTINCT)
NULL -> 아예 안 센다                NULL 끼리 -> 한 칸이 된다

COUNT(DISTINCT dept_id) = 2         PARTITION BY dept_id -> 칸 3개 (10 · 20 · NULL)
   (10 · 20 만)                                              ^^^^^^^^^^
                                                   dan 이 여기 들어간다
```

- **「세기」** — `NULL` 은 「값이 아니다」라고 보고 체에서 거른다([21번](../21-aggregate-functions-count-forms/)).
- **「묶기」** — `NULL` 은 「서로 구별할 수 없는 같은 것」으로 보고 한 칸에 넣는다([22번](../22-group-by-nonaggregated-columns/)).

★ **같은 열에 같은 `NULL` 인데 답이 2와 3이다.** 두 규칙을 **따로 외워야** 한다 — 하나로 통일되어 있지 않다.

이 규칙 덕분에 `dan` 이 사라지지 않는다. 「소속 없는 사람들」도 하나의 비교 집단이 되는 것이다.

---

### 3. `no_order` 는 네 행 다 **1600**, `with_order` 는 **300 → 800 → 1100 → 1600**

**출력**

```text
### SQL: SELECT name, dept_id, salary, SUM(salary) OVER (PARTITION BY dept_id) AS no_order,
                SUM(salary) OVER (PARTITION BY dept_id ORDER BY id) AS with_order
         FROM emp8 ORDER BY dept_id, id;
--- PG 18.6 ---
 name | dept_id | salary | no_order | with_order
------+---------+--------+----------+------------
 ann  |      10 |    300 |     1600 |        300
 bob  |      10 |    500 |     1600 |        800
 eve  |      10 |    300 |     1600 |       1100
 fay  |      10 |    500 |     1600 |       1600
 cho  |      20 |   NULL |      800 |       NULL
 gus  |      20 |    400 |      800 |        400
 hui  |      20 |    400 |      800 |        800
 dan  |    NULL |    400 |      400 |        400
(8 rows)
--- MySQL 8.4.10 ---
+------+---------+--------+----------+------------+
| name | dept_id | salary | no_order | with_order |
+------+---------+--------+----------+------------+
| dan  |    NULL |    400 |      400 |        400 |
| ann  |      10 |    300 |     1600 |        300 |
| bob  |      10 |    500 |     1600 |        800 |
| eve  |      10 |    300 |     1600 |       1100 |
| fay  |      10 |    500 |     1600 |       1600 |
| cho  |      20 |   NULL |      800 |       NULL |
| gus  |      20 |    400 |      800 |        400 |
| hui  |      20 |    400 |      800 |        800 |
+------+---------+--------+----------+------------+
```

**왜 그런가**

```text
순서가 없으면                       순서가 있으면 (ORDER BY id)
프레임 = 칸 전체                     프레임 = 칸의 시작 ~ 나까지

ann [ann bob eve fay] -> 1600       ann [ann]             -> 300
bob [ann bob eve fay] -> 1600       bob [ann bob]         -> 800
eve [ann bob eve fay] -> 1600       eve [ann bob eve]     -> 1100
fay [ann bob eve fay] -> 1600       fay [ann bob eve fay] -> 1600
```

★ **함수도 파티션도 안 바꿨다. `ORDER BY id` 다섯 글자를 적었을 뿐인데 값이 바뀌었다.**\
**순서가 프레임을 만들기 때문**이다 — 「자기 앞」이라는 말은 순서가 있어야 뜻을 갖는다.

`cho` 의 `with_order` 가 `NULL` 인 것은 `SUM(NULL)` 이 `NULL` 이기 때문이다 —\
`cho` 가 자기 칸에서 첫 행이고 더할 값이 `NULL` 하나뿐이다([21번](../21-aggregate-functions-count-forms/) 3번).

출력 **행 순서**가 두 엔진에서 다른 것은 `ORDER BY dept_id` 의 `NULL` 규칙이다. **값은 한 자리도 안 갈렸다.**

> **프레임(frame)** — 창 안에서 실제로 계산에 쓰이는 범위.\
> 예: `ORDER BY id` 를 걸면 `bob` 의 프레임이 `[ann, bob]` 이라 합이 800이다.

---

### 4. 순서가 없으면 **모든 행이 서로의 피어**이기 때문이다

```text
기본 프레임 = "파티션 시작 ~ 현재 행의 마지막 피어"

피어(peer) = 윈도우 ORDER BY 가 "같다"고 판정한 행

ORDER BY 를 안 적었다 -> 비교할 키가 없다 -> 모든 행이 "같다"
                      -> 모든 행이 피어   -> 마지막 피어 = 칸의 마지막 행
                      -> 프레임 = 칸 전체
```

PG 문서가 그대로 적는다: *"Without `ORDER BY`, this means all rows of the partition are included in the window frame, since all rows become peers of the current row."*\
MySQL 문서도 같은 논리다: *"Without `ORDER BY`: The default frame includes all partition rows (because, without `ORDER BY`, all partition rows are peers)."*

★ **「순서가 없으니 전체를 본다」가 특례가 아니다.** 기본 프레임 규칙을 그대로 적용한 **자연스러운 결과**다.\
규칙이 하나이고 갈래가 없다는 것이 이 설명의 요점이다.

> **피어(peer)** — 윈도우 `ORDER BY` 가 같다고 판정한 행들.\
> 예: `ORDER BY salary` 에서 `ann`(300)과 `eve`(300). `ORDER BY` 가 없으면 칸의 모든 행이 피어다.

---

### 5. 간섭하지 않는다 — **다른 일을 하는 두 순서**다

**출력**

```text
### SQL: SELECT name, salary, SUM(salary) OVER (ORDER BY id) AS running FROM emp8 ORDER BY salary DESC, id;
--- PG 18.6 ---
 name | salary | running
------+--------+---------
 cho  |   NULL |     800
 bob  |    500 |     800
 fay  |    500 |    2000
 dan  |    400 |    1200
 gus  |    400 |    2400
 hui  |    400 |    2800
 ann  |    300 |     300
 eve  |    300 |    1500
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+---------+
| name | salary | running |
+------+--------+---------+
| bob  |    500 |     800 |
| fay  |    500 |    2000 |
| dan  |    400 |    1200 |
| gus  |    400 |    2400 |
| hui  |    400 |    2800 |
| ann  |    300 |     300 |
| eve  |    300 |    1500 |
| cho  |   NULL |     800 |
+------+--------+---------+
```

**왜 그런가**

```text
OVER (ORDER BY id)    ->  값을 정한다.  id 순으로 쌓은 누적합
ORDER BY salary DESC  ->  줄을 정한다.  화면에 뿌릴 순서

그래서 running 열이 위에서 아래로 증가하지 않는다 — 증가할 이유가 없다
```

★ **`running` 값 자체는 두 엔진에서 한 자리도 안 갈렸다.** `ann`=300 · `bob`=800 · `hui`=2800 그대로다.\
갈린 것은 `cho` 행이 맨 위냐 맨 아래냐인데, 그건 **출력 `ORDER BY` 의 `NULL` 규칙**이다([08번](../08-order-by-null-position-stability/)).

실무 요구가 정확히 이 모양으로 온다 — 「**입사순**으로 누적하되 **급여순**으로 보여 달라」. 두 순서를 따로 적으면 된다.

---

### 6. `ann` 도 600, `eve` 도 600 — **동률은 서로를 프레임에 넣는다**

**출력**

```text
### SQL: SELECT name, dept_id, salary, SUM(salary) OVER (PARTITION BY dept_id ORDER BY salary) AS running
         FROM emp8 ORDER BY (dept_id IS NULL), dept_id, salary, id;
--- PG 18.6 ---
 name | dept_id | salary | running
------+---------+--------+---------
 ann  |      10 |    300 |     600
 eve  |      10 |    300 |     600
 bob  |      10 |    500 |    1600
 fay  |      10 |    500 |    1600
 gus  |      20 |    400 |     800
 hui  |      20 |    400 |     800
 cho  |      20 |   NULL |     800
 dan  |    NULL |    400 |     400
(8 rows)
--- MySQL 8.4.10 ---
+------+---------+--------+---------+
| name | dept_id | salary | running |
+------+---------+--------+---------+
| ann  |      10 |    300 |     600 |
| eve  |      10 |    300 |     600 |
| bob  |      10 |    500 |    1600 |
| fay  |      10 |    500 |    1600 |
| cho  |      20 |   NULL |    NULL |
| gus  |      20 |    400 |     800 |
| hui  |      20 |    400 |     800 |
| dan  |    NULL |    400 |     400 |
+------+---------+--------+---------+
```

**왜 그런가**

```text
dept 10 칸을 salary 로 줄 세우면

  [ ann 300 ][ eve 300 ] [ bob 500 ][ fay 500 ]
   \___피어___/           \___피어___/

ann 의 프레임 = 시작 ~ "ann 의 마지막 피어" = [ann, eve] -> 300+300 = 600
eve 의 프레임 = 시작 ~ "eve 의 마지막 피어" = [ann, eve] -> 600  (같다)
bob·fay 의 프레임 = [ann,eve,bob,fay]                   -> 1600 (같다)
```

★ **「자기까지의 누적」이라고 외우면 여기서 틀린다.** 정확히는 「**자기의 마지막 피어까지**」다.\
PG 문서의 문장이 정확히 그것이다: *"With `ORDER BY`, this sets the frame to be all rows from the partition start up through the current row's last `ORDER BY` peer."*

한 행씩 늘어나게 하려면 두 가지 방법이 있다.

```sql
-- (1) 프레임 단위를 ROWS 로 바꾼다 (28번)
SUM(salary) OVER (PARTITION BY dept_id ORDER BY salary ROWS UNBOUNDED PRECEDING)
-- (2) 동률을 없앤다 — 고유 키를 ORDER BY 에 더한다
SUM(salary) OVER (PARTITION BY dept_id ORDER BY salary, id)
```

---

### 7. PG 는 **8**, MySQL 은 **1** — `NULL` 의 자리가 반대다

**출력**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary) AS rn FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rn              +------+--------+----+
------+--------+----             | name | salary | rn |
 ann  |    300 |  1              +------+--------+----+
 bob  |    500 |  7              | ann  |    300 |  2 |
 cho  |   NULL |  8              | bob  |    500 |  7 |
 dan  |    400 |  3              | cho  |   NULL |  1 |
 eve  |    300 |  2              | dan  |    400 |  4 |
 fay  |    500 |  6              | eve  |    300 |  3 |
 gus  |    400 |  5              | fay  |    500 |  8 |
 hui  |    400 |  4              | gus  |    400 |  5 |
(8 rows)                         | hui  |    400 |  6 |
                                 +------+--------+----+
```

**왜 그런가**

```text
PG :   300 300 400 400 400 500 500 [NULL]   NULL 을 가장 큰 값으로 본다 -> 8번
MySQL: [NULL] 300 300 400 400 400 500 500   NULL 을 가장 작은 값으로 본다 -> 1번
```

★ **「급여 낮은 순」 목록을 만들면 MySQL 에서는 맨 앞에 급여 미기록자가 온다.**\
화면은 멀쩡하고 에러도 없다. **값이 조용히 다른 사고**다.

이 규칙은 창이 만든 것이 아니라 **엔진의 `ORDER BY` `NULL` 규칙이 창 안으로 그대로 들어온 것**이다([08번](../08-order-by-null-position-stability/)).\
동률(`ann`/`eve`, `dan`/`gus`/`hui`, `bob`/`fay`)의 **내부 순서도 두 엔진에서 다르다** — 그건 [29번](../29-ranking-functions/)의 주제다.

---

### 8. PG 는 **800**, MySQL 은 **`NULL`** — 뿌리는 7번의 `NULL` 위치 규칙이다

6번 출력의 `cho` 행을 보라.

```text
PG (NULL 이 뒤)                      MySQL (NULL 이 앞)
dept 20 칸: gus(400) hui(400) cho    dept 20 칸: cho gus(400) hui(400)
                              ^^^                 ^^^
cho 의 프레임 = [gus,hui,cho]        cho 의 프레임 = [cho]
             -> 400+400+NULL         -> NULL 하나
             -> 800                  -> SUM(NULL) = NULL
```

★ **문법이 다른 게 아니다. 같은 질의가 같은 데이터에서 다른 값을 낸다.**\
`NULL` 위치 규칙 하나가 **프레임의 구성원을 바꾸고**, 프레임이 바뀌니 합이 바뀐다.

`SUM` 이 `NULL` 을 건너뛰는 규칙([21번](../21-aggregate-functions-count-forms/))은 두 엔진이 같다 — PG 의 800 은 `400+400` 이고 `NULL` 은 안 더해졌다.\
갈린 것은 **누가 프레임 안에 있느냐**뿐이다.

★ **이 자리가 이 주제에서 두 엔진의 값이 갈린 유일한 자리다.** 나머지 출력은 값이 전부 같았다.

---

### 9. 키를 하나 더 만든다 — `ORDER BY (salary IS NULL), salary`

```sql
-- 양쪽에서 도는 형태
SELECT name, salary, ROW_NUMBER() OVER (ORDER BY (salary IS NULL), salary) AS rn FROM emp8;

-- PG 에서만 도는 형태
SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary NULLS LAST) AS rn FROM emp8;
```

```text
(salary IS NULL) 은 불리언이다

  salary 가 있으면  -> false (0) -> 앞
  salary 가 NULL 이면 -> true (1) -> 뒤

두 엔진 모두 false < true 이므로, 첫 키 하나로 NULL 을 뒤로 고정할 수 있다
```

★ **`NULLS FIRST`/`NULLS LAST` 는 PG 에만 있는 문법**이다. MySQL 에서는 `ERROR 1064` 가 난다.\
그래서 **이식할 질의에는 `(열 IS NULL)` 키를 쓴다.** 이 방법의 실행 확인은 [08번](../08-order-by-null-position-stability/) 3번에 있다.

더 간단한 길도 있다 — **`WHERE salary IS NOT NULL` 로 먼저 거르는 것**이다.\
「급여 기록이 없는 사람은 순위에 넣지 않는다」가 요구에 맞는다면 그게 가장 정직한 답이다.

---

### 10. 두 엔진 다 에러다 — MySQL 도 `OVER` 절에서는 별칭을 안 받는다

**출력**

```text
### SQL: SELECT salary * 12 AS annual, SUM(salary) OVER (PARTITION BY annual) AS s FROM emp8;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 7: ...ry * 12 AS annual, SUM(salary) OVER (PARTITION BY annual) AS...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'annual' in 'window partition by'
```

**왜 그런가**

```text
SELECT salary * 12 AS annual, SUM(salary) OVER (PARTITION BY annual)
       ^^^^^^^^^^^^^^^^^^^^^                                 ^^^^^^
       별칭은 이 칸에서 태어난다                    그런데 이 자리도 같은 칸 안이다
                                          -> 자기가 만드는 이름을 자기가 쓸 수 없다
```

★ **MySQL 이 `HAVING` 에서 별칭을 받아 주는 것과 어긋나 보이지만**([02번](../02-select-list-column-aliases/)) 어긋나지 않는다.\
`HAVING` 은 `SELECT` **바깥의 다른 절**이고, MySQL 은 거기서 출력 열 이름을 먼저 찾아 주는 확장을 했다.\
`OVER` 절은 **`SELECT` 목록 안에 들어 있는 식의 일부**라 그 확장이 닿지 않는다 — 에러 문구의 `'window partition by'` 가 그 자리를 꼭 집어 말한다.

고치는 법 둘.

```sql
SELECT salary * 12 AS annual, SUM(salary) OVER (PARTITION BY salary * 12) AS s FROM emp8;     -- 다시 적는다
SELECT annual, SUM(salary) OVER (PARTITION BY annual) AS s
FROM (SELECT salary, salary * 12 AS annual FROM emp8) t;                                       -- 한 겹 감싼다
```

---

### 11. 된다 — `cho` 의 `COUNT(*) OVER (PARTITION BY salary)` 는 **1**

**출력**

```text
### SQL: SELECT name, dept_id, salary, COUNT(*) OVER (PARTITION BY dept_id) AS in_dept,
                COUNT(*) OVER (PARTITION BY salary) AS same_salary
         FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | dept_id | salary | in_dept | same_salary
------+---------+--------+---------+-------------
 ann  |      10 |    300 |       4 |           2
 bob  |      10 |    500 |       4 |           2
 cho  |      20 |   NULL |       3 |           1
 dan  |    NULL |    400 |       1 |           3
 eve  |      10 |    300 |       4 |           2
 fay  |      10 |    500 |       4 |           2
 gus  |      20 |    400 |       3 |           3
 hui  |      20 |    400 |       3 |           3
(8 rows)
--- MySQL 8.4.10 ---
+------+---------+--------+---------+-------------+
| name | dept_id | salary | in_dept | same_salary |
+------+---------+--------+---------+-------------+
| ann  |      10 |    300 |       4 |           2 |
| bob  |      10 |    500 |       4 |           2 |
| cho  |      20 |   NULL |       3 |           1 |
| dan  |    NULL |    400 |       1 |           3 |
| eve  |      10 |    300 |       4 |           2 |
| fay  |      10 |    500 |       4 |           2 |
| gus  |      20 |    400 |       3 |           3 |
| hui  |      20 |    400 |       3 |           3 |
+------+---------+--------+---------+-------------+
```

**왜 그런가**

```text
PARTITION BY salary 가 만든 칸

 300  : ann eve            -> 2
 400  : dan gus hui        -> 3   <- 부서가 달라도 같은 칸이다
 500  : bob fay            -> 2
 NULL : cho                -> 1   <- NULL 끼리 한 칸인데, NULL 인 사람이 혼자다
```

★ **파티션 축은 질의의 `GROUP BY` 나 키와 아무 관계가 없다.** 아무 식이나 쓸 수 있고, 서로 다른 축을 여러 개 둘 수 있다.\
`dan`(부서 `NULL`)이 `gus`·`hui`(부서 20)와 **같은 급여 칸**에 들어간 것이 그 증거다.

`cho` 의 1은 「**급여가 `NULL` 인 사람은 자기밖에 없다**」는 뜻이다 — `NULL` 이 세어지지 않아 0이 된 게 아니다.\
`COUNT(*)` 은 행을 세고, 파티션은 `NULL` 을 한 칸으로 묶기 때문이다([21번](../21-aggregate-functions-count-forms/)과 2번).

---

### 12. 파티션 경계에서 계산이 **초기화**된다 — 이어 쌓으려면 `PARTITION BY` 를 뺀다

3번 출력을 다시 보라.

```text
PARTITION BY dept_id ORDER BY id          PARTITION BY 없이 ORDER BY id
ann  300                                  ann  300
bob  800                                  bob  800
eve 1100                                  cho  800    (NULL 은 안 더해진다)
fay 1600   <- 칸 끝                        dan 1200
cho NULL   <- 새 칸, 다시 시작              eve 1500
gus  400                                  fay 2000
hui  800                                  gus 2400
dan  400   <- 또 새 칸                     hui 2800
```

```text
창은 칸 밖을 보지 못한다 -> 칸이 바뀌면 "자기 앞"에 아무것도 없다 -> 처음부터 쌓는다
```

★ **이건 버그가 아니라 `PARTITION BY` 의 정의 그대로다.** 「부서별 누적」을 요구했으니 부서마다 다시 세는 게 맞다.

「부서가 바뀌어도 이어서 쌓이는 전체 누적」이 필요하면 **`PARTITION BY` 를 빼면 된다**(위 오른쪽).\
둘 다 필요하면 **두 열을 나란히** 뽑는다 — 같은 질의에 창 둘을 두는 것은 1번에서 이미 했다.

```sql
SELECT name, dept_id,
       SUM(salary) OVER (PARTITION BY dept_id ORDER BY id) AS dept_running,
       SUM(salary) OVER (ORDER BY id)                      AS all_running
FROM emp8;
```

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `OVER ()` 대 `PARTITION BY` (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 8행 유지 · `dan`=400 |
| 서로 다른 축의 창 둘 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `cho` 의 `same_salary`=1 |
| `ORDER BY` 유무 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 1600 → 300·800·1100·1600 |
| 창 순서 대 출력 순서 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `running` 값 동일 |
| ★ 동률의 프레임 (6·8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`cho` 가 800 대 `NULL` — 유일한 값 차이** |
| ★ 창 안 `NULL` 위치 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `cho` 가 8등 대 1등 |
| `OVER` 절의 별칭 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **둘 다 에러 — 메시지를 그대로 실었다** |
| `(salary IS NULL)` 키 (9번) | — | — | 형태만 제시. **실행 확인은 [08번](../08-order-by-null-position-stability/) 3번에 있다** |

**구현 의존 항목** — **창 안 `NULL` 의 위치**(PG 뒤 / MySQL 앞)와 에러 메시지 문구, 그리고 동률 행의 내부 순서([29번](../29-ranking-functions/)).

**방언 항목** — **6·7·8번이 한 뿌리다.** `NULL` 위치 하나가 순위와 누적합을 동시에 바꾼다.\
`NULLS FIRST`/`LAST` 문법이 PG 에만 있는 것도 같은 자리다.\
**언어 보장 항목** — 1\~5·10\~12번. 파티션이 행을 안 버리는 것, `NULL` 이 한 칸이 되는 것, 기본 프레임이 피어까지인 것,\
`OVER` 절이 별칭을 안 받는 것은 두 문서가 같은 모양으로 적고 두 엔진의 출력도 같았다.

**버전** — `PARTITION BY`·윈도우 `ORDER BY` 는 PG 8.4 · MySQL 8.0 부터다. 버전이 오르면 **7번만 다시 찍으면 된다.**\
**재지 않은 것** — 창마다 드는 정렬 횟수와 비용. **측정하지 않았으므로 적지 않았다.**
