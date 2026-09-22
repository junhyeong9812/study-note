# sql/27-`PARTITION BY` 와 윈도우 `ORDER BY` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) · [PostgreSQL 18 · Window Functions (튜토리얼)](https://www.postgresql.org/docs/18/tutorial-window.html) · [MySQL 8.4 · Window Function Concepts and Syntax](https://dev.mysql.com/doc/refman/8.4/en/window-functions-usage.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `PARTITION BY`·윈도우 `ORDER BY` 는 윈도우 함수와 같이 들어왔다(PG 8.4 · MySQL 8.0).\
> **갈리는 자리는 `NULL` 의 위치 하나**다(6번) — 그런데 그것 때문에 **값까지 달라진다.**\
> **선행** — [26 윈도우 함수의 개념](../26-window-functions-vs-aggregates/). **뒤 주제** — [28 프레임](../28-window-frames-rows-range-groups/) · [29 순위 함수](../29-ranking-functions/) · [30 오프셋·경계 함수](../30-offset-and-boundary-functions/) · [31 평가 시점](../31-window-evaluation-timing/).

## 한눈에 — 쉽게 말하면

**창문을 몇 개로 나누고, 그 안에서 사람을 어떻게 줄 세울 것인가.**

- 강당에 8명이 있다. 창문 하나로 **전체**를 보면 `OVER ()` 다([26번](../26-window-functions-vs-aggregates/)).
- **부서별로 칸막이를 치면** 창문이 셋이 된다. 각자는 **자기 칸 안만** 본다. 이게 `PARTITION BY` 다.
- 칸 안에서 **키 순으로 줄을 세우면** 「나보다 앞에 선 사람」이라는 말이 비로소 뜻을 갖는다.\
  이게 윈도우 `ORDER BY` 이고, **누적합·순위·이전 행**이 전부 여기서 나온다.

★ **칸막이는 사람을 내보내지 않는다.** 8명은 계속 8명이다 — 이것이 `GROUP BY` 와 다른 점이다.

| 비유 | 실체 | `emp8` 에 대고 실행하면 |
|---|---|---|
| 창문 하나로 전체를 본다 | `OVER ()` | 창 1개 · 8행 |
| 부서별로 칸막이를 친다 | `OVER (PARTITION BY dept_id)` | 창 3개(4·3·1행) · 결과는 **여전히 8행** |
| 칸 안에서 줄을 세운다 | `OVER (PARTITION BY dept_id ORDER BY id)` | 창 3개 · 행마다 **자기 앞까지의 누적** |

```text
PARTITION BY dept_id          한 칸 안에서 ORDER BY id 를 걸면

+-- 10 -----------+           +-- 10 -----------+
| ann bob eve fay |  4행      | ann -> 300      |  자기까지의 누적
+-----------------+           | bob -> 800      |
+-- 20 -----------+           | eve -> 1100     |
| cho gus hui     |  3행      | fay -> 1600     |
+-----------------+           +-----------------+
+-- NULL ---------+            순서가 없으면 전부 1600 이다
| dan             |  1행       순서가 생겨야 "자기 앞"이 정의된다
+-----------------+
  결과는 4+3+1 = 8행 — 한 행도 안 줄었다
```

> **파티션(partition)** — `PARTITION BY` 가 나눈 창 한 칸. 계산은 칸 안에서만 일어난다.\
> 예: `PARTITION BY dept_id` 는 `emp8` 을 `10`(4행)·`20`(3행)·`NULL`(1행) 세 칸으로 나눈다.

> **윈도우 `ORDER BY`** — 창 **안**의 줄 세우기. 질의 맨 끝의 `ORDER BY`(출력 정렬)와 **다른 것**이다.\
> 예: `OVER (ORDER BY id)` 는 창 안을 `id` 순으로 세우고, 출력 순서는 건드리지 않는다.

## 이 주제가 답하려는 질문

1. **`PARTITION BY` 는 `GROUP BY` 와 무엇이 다른가?** — 그룹이 아니라 **창**을 나눈다. 행은 안 줄어든다.
2. **윈도우 `ORDER BY` 를 적으면 왜 값이 바뀌나?** — 순서가 **프레임**(볼 범위)을 만들기 때문이다.
3. **창 안의 `ORDER BY` 와 질의 끝의 `ORDER BY` 는 같은 것인가?** — 다르다. 같이 써도 서로 간섭하지 않는다.

## 예시 데이터 — 이 묶음이 공유하는 것

26~31 여섯 주제는 **`study` DB 의 `emp`·`dept` 두 표를 그대로** 쓴다. 새 표는 만들지 않았다.\
윈도우는 4행으로 좁으므로 **CTE 로 4행을 얹어 `emp8`** 을 만든다.

```sql
WITH emp8 AS (
  SELECT id, name, dept_id, salary FROM emp
  UNION ALL SELECT 5, 'eve', 10, 300
  UNION ALL SELECT 6, 'fay', 10, 500
  UNION ALL SELECT 7, 'gus', 20, 400
  UNION ALL SELECT 8, 'hui', 20, 400
)
```

`VALUES (…),(…)` 를 안 쓴 이유는 **두 엔진이 서로의 행 생성자 문법을 정확히 거부**하기 때문이다([10번](../10-from-clause-aliases-derived-tables/)).

```text
emp8 (emp 4행 + CTE 가 얹은 4행)      파티션으로 보면
+----+------+---------+--------+
| id | name | dept_id | salary |      dept_id = 10   : ann(300) bob(500) eve(300) fay(500)  4행
+----+------+---------+--------+      dept_id = 20   : cho(NULL) gus(400) hui(400)          3행
|  1 | ann  |      10 |    300 |      dept_id = NULL : dan(400)                             1행
|  2 | bob  |      10 |    500 |
|  3 | cho  |      20 |   NULL |      salary 로 줄 세우면
|  4 | dan  |    NULL |    400 |       300 : ann eve      <- 동률 2
|  5 | eve  |      10 |    300 |       400 : dan gus hui  <- 동률 3
|  6 | fay  |      10 |    500 |       500 : bob fay      <- 동률 2
|  7 | gus  |      20 |    400 |      NULL : cho          <- 위치가 엔진마다 다르다
|  8 | hui  |      20 |    400 |
+----+------+---------+--------+
```

**왜 이 데이터가 이 주제에 맞는가.**

- **`dept_id` 에 `NULL` 이 있다**(`dan`) — `PARTITION BY` 가 `NULL` 을 **버리지 않고 한 칸으로 묶는** 것을 보여 준다.\
  「세기」에서는 `NULL` 을 안 세는데([21번](../21-aggregate-functions-count-forms/)) **「묶기」에서는 한 칸이 된다** — 규칙이 정반대다.
- **칸 크기가 4·3·1 로 다르다** — 칸마다 계산이 따로 도는 것이 한눈에 보인다.
- **`salary` 에 동률이 세 덩어리 있다** — 윈도우 `ORDER BY` 를 걸었을 때 **동률 행이 서로를 보는지**가 드러난다(5번).\
  이것이 [28번](../28-window-frames-rows-range-groups/)의 기본 프레임으로 이어지는 복선이다.
- **`salary` 에 `NULL` 이 하나 있다**(`cho`) — 창 안 줄 세우기에서 `NULL` 이 **앞/뒤 어디에 서는지**가 두 엔진에서 갈린다(6번).

## 동작 방식

---

### 1. ★ `PARTITION BY` 는 그룹이 아니라 **창**을 나눈다

**언제 쓰나** — 「자기 부서 합계」·「자기 등급 안에서의 순위」처럼 **비교 대상을 좁히고 싶을 때**.

```text
GROUP BY dept_id          PARTITION BY dept_id
8행 -> 3행                8행 -> 8행
칸마다 결과 한 줄            칸마다 계산하고, 그 값을 칸 안 모든 행에 붙인다

+-- 10 --+                +-- 10 -----------------+
| 합 1600|                | ann 300 -> 1600       |
+--------+                | bob 500 -> 1600       |
+-- 20 --+                | eve 300 -> 1600       |
| 합  800|                | fay 500 -> 1600       |
+--------+                +-----------------------+
+- NULL -+                +-- 20 -----------------+ ...
| 합  400|
+--------+
```

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

그림 해설 — **결과가 8행 그대로다.** `all_sum`(창 하나)과 `dept_sum`(창 셋)이 **같은 질의 안에 나란히** 있다.\
`GROUP BY` 로는 이게 안 된다 — 한 질의에 그룹 기준을 둘 둘 수 없기 때문이다([23번](../23-grouping-sets-rollup-cube/)의 `GROUPING SETS` 가 그 자리의 다른 답이다).

★ **`dan` 의 `dept_sum` 이 400 이다.** `dept_id` 가 `NULL` 인 행이 **버려지지 않고 자기 칸을 하나 차지**했다.\
「세기」에서 `NULL` 이 안 세어지는 것([21번](../21-aggregate-functions-count-forms/))과 **반대 규칙**이다 — 묶을 때는 `NULL` 끼리 한 칸이 된다.

비용 — 칸마다 정렬 또는 해시가 한 번씩 돈다. 칸이 잘게 쪼개질수록 각 계산은 싸진다.

---

### 2. 파티션 기준은 아무 식이나 된다 — `GROUP BY` 와 무관하다

**언제 쓰나** — 「나와 같은 급여를 받는 사람이 몇 명인가」처럼 **키가 아닌 값**으로 비교 대상을 잡을 때.

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

그림 해설 — **한 질의에 서로 다른 축의 창 둘이 동시에 있다.** `dept_id` 축과 `salary` 축이다.\
`cho` 의 `same_salary` 가 **1**인 것에 주목하라 — `salary` 가 `NULL` 인 사람이 자기 혼자라 **`NULL` 칸의 크기가 1**이다.\
`dan`·`gus`·`hui` 는 급여가 전부 400이라 **부서가 달라도 같은 칸**에 들어가 3이 됐다.

★ **파티션 축은 질의의 `GROUP BY` 와 아무 관계가 없다.** 원하는 만큼, 서로 다르게 잡을 수 있다.

비용 — `OVER` 절이 서로 다르면 **창마다 따로 정렬**해야 한다. 같은 `OVER` 를 여러 번 쓰면 한 번만 돈다.

---

### 3. ★ 윈도우 `ORDER BY` 를 적는 순간 **값이 바뀐다**

**언제 쓰나** — 누적합·순위·이전 행처럼 **「자기 앞」이라는 말이 필요한** 계산 전부.

```text
PARTITION BY dept_id              PARTITION BY dept_id ORDER BY id
(순서 없음)                        (순서 있음)

칸 전체가 프레임                    "칸의 처음 ~ 나까지" 가 프레임
ann -> 1600                       ann -> 300
bob -> 1600                       bob -> 300+500      = 800
eve -> 1600                       eve -> 800+300      = 1100
fay -> 1600                       fay -> 1100+500     = 1600
      ^^^^                              ^^^^^^^^^^^^
      전부 같다                          행마다 다르다
```

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

그림 해설 — ★ **`ORDER BY` 를 적었을 뿐인데 `SUM` 이 「칸 전체 합」에서 「자기까지의 누적」으로 바뀌었다.**\
함수도 안 바꿨고 파티션도 안 바꿨다. **순서를 적었다는 사실 하나가 「볼 범위」를 바꾼 것이다.**

**왜 그런가 — 순서가 「프레임」을 만든다.**

```text
ORDER BY 가 없으면   프레임 = 파티션 전체 (모두가 서로의 동률이다)
ORDER BY 가 있으면   프레임 = 파티션 시작 ~ "현재 행의 마지막 동률" 까지
                                              ^^^^^^^^^^^^^^^^^^^^^
                     이 기본값의 정체가 28번의 본문이다
```

PG 문서가 그대로 적는다: *"Without `ORDER BY`, this means all rows of the partition are included in the window frame, since all rows become peers of the current row."*\
MySQL 문서도 같은 말을 한다 — *"Without `ORDER BY`: The default frame includes all partition rows (because, without `ORDER BY`, all partition rows are peers)."*

`cho` 의 `with_order` 가 **`NULL`** 인 것은 `SUM(NULL)` 이 `NULL` 이기 때문이다 — `cho` 가 자기 칸에서 첫 행이고\
더할 값이 `NULL` 하나뿐이다([21번](../21-aggregate-functions-count-forms/) 3번). **`dan` 의 `no_order`·`with_order` 가 둘 다 400** 인 것도 같은 이치다 — 칸에 자기 혼자다.

비용 — 칸마다 정렬이 필요해진다. 대신 「자기 앞」이라는 개념이 생긴다.

---

### 4. 창 안의 `ORDER BY` 와 질의 끝의 `ORDER BY` 는 **다른 것**이다

**언제 쓰나** — 「입사순으로 누적합을 구하되 급여 높은 순으로 보여 달라」 같은 요구.

```text
SELECT ..., SUM(salary) OVER (ORDER BY id) ...   <- 창 안의 줄 세우기 (값을 정한다)
FROM emp8
ORDER BY salary DESC, id;                        <- 출력 줄 세우기 (보이는 순서만 정한다)
        ^^^^^^^^^^^^^^^
        서로 간섭하지 않는다
```

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

그림 해설 — **`running` 열이 위에서 아래로 증가하지 않는다.** 당연하다 — 그 값은 `id` 순으로 계산됐고,\
화면은 `salary DESC` 로 정렬돼 있다. **두 순서가 다른 일을 한다**는 것이 이 출력의 전부다.

★ **`running` 값 자체는 두 엔진에서 한 자리도 안 갈렸다.** 갈린 것은 `cho` 행이 맨 위냐 맨 아래냐뿐이고,\
그것은 **출력 `ORDER BY` 의 `NULL` 규칙**이다([08번](../08-order-by-null-position-stability/) — PG 는 `NULL` 을 큰 값, MySQL 은 작은 값으로 본다).

비용 — 정렬이 두 번 필요할 수 있다(창용 한 번, 출력용 한 번).

---

### 5. ★ 동률은 서로를 본다 — 윈도우 `ORDER BY` 의 기준이 동률이면

**언제 쓰나** — 급여·점수처럼 **같은 값이 여러 행에 있는 열**로 창 안을 줄 세울 때. 즉 거의 매번.

```text
PARTITION BY dept_id ORDER BY salary   (dept 10 칸)

         ann(300)  eve(300)   bob(500)  fay(500)
             \       /            \       /
              동률 한 덩어리        동률 한 덩어리

ann 의 프레임 = [ann, eve]        -> 600   (자기 동률까지 포함한다)
eve 의 프레임 = [ann, eve]        -> 600   (같다)
bob 의 프레임 = [ann,eve,bob,fay] -> 1600
fay 의 프레임 = [ann,eve,bob,fay] -> 1600
```

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

그림 해설 — ★ **`ann` 과 `eve` 가 둘 다 600 이다.** 「자기까지의 누적」이면 300과 600이어야 할 텐데 그렇지 않다.\
**동률 행은 서로를 프레임 안에 넣는다.** 기본 프레임이 *"up through the current row's last `ORDER BY` peer"* 이기 때문이다(PG 문서).

> **동률/피어(peer)** — 윈도우 `ORDER BY` 가 **같다고 판정한** 행들. 서로의 프레임에 들어간다.\
> 예: `ORDER BY salary` 에서 `ann`(300)과 `eve`(300)는 서로의 피어다.

★ **`dept 20` 칸에서 두 엔진의 값이 갈린다.**

| | `cho`(salary `NULL`) | 왜 |
|---|---|---|
| PG | `running` = **800** | `NULL` 이 칸의 **맨 뒤**에 선다 → 앞의 `gus`·`hui` 가 프레임에 들어온다 |
| MySQL | `running` = **NULL** | `NULL` 이 칸의 **맨 앞**에 선다 → 프레임이 자기 혼자 → `SUM(NULL)` = `NULL` |

**값이 다른 것이지 문법이 다른 것이 아니다.** 같은 질의, 같은 데이터, 다른 답이다.\
뿌리는 [08번](../08-order-by-null-position-stability/)에 적힌 그 규칙 하나다 — **PG 는 `NULL` 을 큰 값, MySQL 은 작은 값으로 본다.**

비용 — 동률을 찾으려면 정렬 결과를 한 번 더 훑어야 한다. `ROWS` 로 바꾸면 그 훑기가 없어진다([28번](../28-window-frames-rows-range-groups/)).

---

### 6. ★ 창 안의 `NULL` 위치가 두 엔진에서 반대다

**언제 쓰나** — 순위·누적·이전 행을 **`NULL` 이 섞인 열**로 계산할 때.

```text
ORDER BY salary (오름차순)

PG :   300 300 400 400 400 500 500 [NULL]      NULL 을 "가장 큰 값" 취급 -> 뒤
MySQL: [NULL] 300 300 400 400 400 500 500      NULL 을 "가장 작은 값" 취급 -> 앞
```

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

그림 해설 — ★ **`cho` 가 PG 에서는 8등, MySQL 에서는 1등이다.** 급여가 **없는** 사람이 MySQL 에서 1등을 차지했다.\
「급여 낮은 순」 목록을 만들면 MySQL 에서는 **맨 앞에 급여 미기록자가 온다.** 조용히 틀리는 자리다.

★ **`PARTITION BY` 에서는 `NULL` 위치가 문제가 되지 않는다** — 칸을 나눌 뿐 줄을 세우지 않기 때문이다.\
`NULL` 위치는 **윈도우 `ORDER BY` 를 적은 순간에만** 생기는 문제다.

**고치는 법** — PG 는 `NULLS LAST`/`NULLS FIRST` 를 창 안에도 쓸 수 있다. MySQL 은 그 문법이 없으므로\
**키를 하나 더 만든다** — `ORDER BY (salary IS NULL), salary`. 두 엔진 모두에서 돈다([08번](../08-order-by-null-position-stability/) 3번).

비용 — 정렬 키가 하나 늘어난다. 대신 답이 엔진에 안 휘둘린다.

---

### 7. `PARTITION BY` 에는 `SELECT` 별칭을 못 쓴다

**언제 쓰나** — 계산한 값으로 창을 나누고 싶을 때. 별칭을 재사용하려다 여기서 막힌다.

```text
### SQL: SELECT salary * 12 AS annual, SUM(salary) OVER (PARTITION BY annual) AS s FROM emp8;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 7: ...ry * 12 AS annual, SUM(salary) OVER (PARTITION BY annual) AS...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'annual' in 'window partition by'
```

그림 해설 — ★ **두 엔진 다 거부한다.** 별칭은 `SELECT` 칸에서 태어나는데, `OVER` 절은 **그 칸 안에 있다** —\
자기 자신이 만드는 이름을 자기가 쓸 수는 없다([01번](../01-logical-query-processing-order/)·[02번](../02-select-list-column-aliases/)).

★ **MySQL 이 `'window partition by'` 라고 자리를 꼭 집어 말하는 것**에 주목하라.\
MySQL 은 `HAVING`·`GROUP BY` 에서는 별칭을 허용하지만([02번](../02-select-list-column-aliases/)) **`OVER` 절에서는 PG 와 같이 거부한다.**

**고치는 법** — 식을 다시 적거나(`PARTITION BY salary * 12`) 한 겹 감싼다.

```sql
SELECT annual, SUM(salary) OVER (PARTITION BY annual) AS s
FROM (SELECT salary, salary * 12 AS annual FROM emp8) t;
```

비용 — 식을 두 번 적거나 파생 테이블이 한 겹 는다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
OVER (
  PARTITION BY 식 [, 식 ...]     -- 창을 나눈다. 없으면 창은 하나
  ORDER BY 식 [ASC|DESC] [NULLS FIRST|LAST]   -- 창 안의 순서. NULLS 절은 PG 에만
  [ROWS|RANGE|GROUPS ...]       -- 볼 범위. 28번
)
```

규칙 일곱.

1. **`PARTITION BY` 는 행을 안 버린다.** 결과 행 수는 `OVER` 를 어떻게 적든 그대로다.
2. **`PARTITION BY` 에서 `NULL` 끼리는 한 칸**이다. 「세기」의 규칙과 반대다.
3. **윈도우 `ORDER BY` 는 값을 바꾼다.** 순서가 프레임을 만들기 때문이다.
4. **`ORDER BY` 가 없으면 프레임은 파티션 전체**다 — 모두가 서로의 피어이기 때문이다.
5. **동률은 서로의 프레임에 들어간다.** `ann`·`eve` 가 둘 다 600 이었던 이유다.
6. **창 안의 `NULL` 위치가 두 엔진에서 반대**다. 고정하려면 `(열 IS NULL)` 키를 앞에 더한다.
7. **`OVER` 절에는 `SELECT` 별칭을 못 쓴다.** 두 엔진 모두 거부한다.

실전 형태는 넷이다.

```sql
-- (1) 칸 전체 값을 행마다
SELECT name, SUM(salary) OVER (PARTITION BY dept_id) AS dept_sum FROM emp8;

-- (2) 칸 안의 누적
SELECT name, SUM(salary) OVER (PARTITION BY dept_id ORDER BY id) AS running FROM emp8;

-- (3) 서로 다른 축의 창 둘을 한 질의에
SELECT name, COUNT(*) OVER (PARTITION BY dept_id) AS a, COUNT(*) OVER (PARTITION BY salary) AS b FROM emp8;

-- (4) NULL 위치를 양쪽에서 고정
SELECT name, ROW_NUMBER() OVER (ORDER BY (salary IS NULL), salary) AS rn FROM emp8;
```

## 어디서 틀리나

- **★ `PARTITION BY` 를 `GROUP BY` 로 읽는다.**\
  칸막이는 사람을 내보내지 않는다. 결과 행 수를 먼저 세면 절대 안 헷갈린다.
- **★ 윈도우 `ORDER BY` 를 「보기 좋으라고」 적는다.**\
  적는 순간 `SUM` 이 전체합에서 누적합으로 **값이 바뀐다.** 출력 정렬이 목적이면 질의 끝에 적는다.
- **★ 동률이 있는데 「자기까지의 누적」이라고 믿는다.**\
  `ann`·`eve` 가 둘 다 600이다. 한 행씩 늘어나길 원하면 `ROWS` 를 명시하거나 고유 키를 `ORDER BY` 에 더한다([28번](../28-window-frames-rows-range-groups/)).
- **★ `NULL` 이 섞인 열로 창 안을 줄 세운다.**\
  PG 는 뒤, MySQL 은 앞이다. 값까지 달라진다(5번의 `cho` — 800 대 `NULL`).
- **`PARTITION BY` 에 `SELECT` 별칭을 쓴다.**\
  두 엔진 다 에러다. 식을 다시 적거나 한 겹 감싼다.
- **창을 여러 개 쓰면서 `OVER` 절을 매번 복사한다.**\
  오타 하나로 다른 창이 된다. 같은 창이면 `WINDOW` 절로 이름을 붙인다([31번](../31-window-evaluation-timing/)).
- **`ORDER BY` 없는 `OVER` 에서 「첫 행」·「마지막 행」을 기대한다.**\
  순서가 없으면 「첫」이 정의되지 않는다. `FIRST_VALUE` 가 무엇을 줄지 보장이 없다([30번](../30-offset-and-boundary-functions/)).

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `PARTITION BY` 가 행을 안 버린다 | **정의** | 언어 — 두 문서가 같은 모양으로 적는다 |
| `PARTITION BY` 에서 `NULL` 이 한 칸 | **정의** | 언어 — 두 엔진 실행 결과가 같다(1번) |
| `ORDER BY` 없으면 프레임 = 파티션 전체 | **정의** | 언어 — PG *"all rows become peers"* · MySQL 동일 문장 |
| 동률이 서로의 프레임에 든다 | **정의** | 언어 — PG *"up through the current row's last `ORDER BY` peer"* |
| **창 안 `NULL` 의 위치** | **방언** | 엔진 — PG 뒤 / MySQL 앞. **값까지 갈린다**(5·6번) |
| `NULLS FIRST`/`LAST` 문법 | **방언** | PG 에만 있다. MySQL 은 `(열 IS NULL)` 키로 대신한다 |
| `OVER` 절의 별칭 거부 | **정의** | 언어 — 두 엔진 모두 거부(7번). 메시지만 다르다 |
| 창마다 정렬을 몇 번 하나 | 계획의 문제 | 엔진 — **이 주제에서 재지 않았다** |

- **이 주제에서 두 엔진의 값이 갈린 자리는 `NULL` 위치 하나다.** 그런데 그 하나가 `cho` 의 누적합을 800과 `NULL` 로 갈랐다.
- **「값이 안 갈렸다」와 「보장된다」는 다르다** — 1~4번의 일치는 관찰이고, 보장은 위 표의 「정의」 칸이 말한다.

## 언제 쓰고 언제 안 쓰나

- **`PARTITION BY` 를 쓴다 — 비교 대상을 좁혀야 할 때.** 「자기 부서 안에서」·「같은 등급 안에서」.
- **`PARTITION BY` 를 안 쓴다 — 비교 대상이 전체일 때.** `OVER ()` 로 충분하다.
- **윈도우 `ORDER BY` 를 쓴다 — 「자기 앞」이 필요할 때.** 누적·순위·이전 행.
- **윈도우 `ORDER BY` 를 안 쓴다 — 칸 전체 값이 목적일 때.** 적으면 값이 바뀐다.
- **`NULL` 이 섞인 열로는 그냥 줄 세우지 않는다.** `(열 IS NULL)` 를 앞에 두거나 `WHERE` 로 먼저 거른다.
- **칸이 아주 잘게 쪼개지면 다시 생각한다.** 칸마다 1행이면 창을 쓸 이유가 없다(`dan` 이 그 경우다).

## 핵심 문장

- `PARTITION BY` 는 **그룹이 아니라 창**을 나눈다. 8행은 계속 8행이다.
- **`PARTITION BY` 에서 `NULL` 끼리는 한 칸**이 된다 — 「세기」의 규칙과 반대다(`dan` 의 `dept_sum`=400).
- ★ **윈도우 `ORDER BY` 를 적으면 값이 바뀐다** — 순서가 **프레임**을 만들기 때문이다. `1600` 이 `300·800·1100·1600` 이 됐다.
- **`ORDER BY` 가 없으면 프레임은 파티션 전체**다. 순서가 없으면 모두가 서로의 피어이기 때문이다.
- ★ **동률은 서로를 프레임에 넣는다** — `ann`·`eve` 가 둘 다 600 이다. 한 행씩 늘려면 [28번](../28-window-frames-rows-range-groups/)의 `ROWS`.
- 창 안의 `ORDER BY` 와 질의 끝의 `ORDER BY` 는 **다른 일**을 한다. 같이 써도 간섭하지 않는다.
- ★ **창 안의 `NULL` 위치가 두 엔진에서 반대**다 — `cho` 가 PG 8등, MySQL 1등이고 누적합도 800 대 `NULL` 이다.
- **`OVER` 절에는 `SELECT` 별칭을 못 쓴다.** MySQL 도 여기서는 거부한다.

## 관련 자료

- [PostgreSQL 18 · Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) — `PARTITION BY`·`ORDER BY`·프레임 기본값이 같은 페이지에 있다.
- [PostgreSQL 18 · Window Functions (튜토리얼)](https://www.postgresql.org/docs/18/tutorial-window.html) — 파티션 개념과 `WINDOW` 절.
- [MySQL 8.4 · Window Function Concepts and Syntax](https://dev.mysql.com/doc/refman/8.4/en/window-functions-usage.html) — 파티션과 순서의 정의.
- [26 윈도우 함수의 개념](../26-window-functions-vs-aggregates/) — **경계: 그쪽은 「접지 않는다」와 `OVER ()` 빈 창까지, 여기는 창을 나누고 줄 세우는 것부터.**
- [28 프레임 — ROWS·RANGE·GROUPS](../28-window-frames-rows-range-groups/) — **경계: 여기는 「순서가 프레임을 만든다」는 사실까지, 그 프레임의 기본값과 세 단위는 거기.**
- [08 ORDER BY — 정렬 키·NULL 위치·동률](../08-order-by-null-position-stability/) — **경계: 그쪽은 출력 정렬의 `NULL` 위치와 동률 불안정까지, 여기는 그 규칙이 창 안에 들어와 값을 바꾸는 것부터.**
- [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) — **경계: 그쪽은 그룹이 결과 행을 정의하는 것까지, 여기는 파티션이 그러지 않는다는 것부터.**
- [02 SELECT 목록과 열 별칭의 유효 범위](../02-select-list-column-aliases/) — 7번의 별칭 거부가 나온 자리.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **파티션(partition)** — `PARTITION BY` 가 나눈 창 한 칸. 계산은 칸 안에서만 일어난다.\
  예: `PARTITION BY dept_id` 는 `emp8` 을 4행·3행·1행 세 칸으로 나눈다.
- **창(window)** — 한 행이 값을 계산할 때 들여다보는 행 묶음. 파티션과 프레임으로 정해진다.\
  예: `PARTITION BY dept_id ORDER BY id` 에서 `bob` 의 창은 `[ann, bob]` 이다.
- **윈도우 `ORDER BY`** — 창 **안**의 줄 세우기. 출력 정렬과 다른 것이다.\
  예: `OVER (ORDER BY id)` 를 적어도 화면 순서는 안 바뀐다(4번).
- **동률/피어(peer)** — 윈도우 `ORDER BY` 가 같다고 판정한 행들. 서로의 프레임에 들어간다.\
  예: `ORDER BY salary` 에서 `ann`(300)과 `eve`(300).
- **프레임(frame)** — 창 안에서 **실제로 계산에 쓰이는 범위**. 기본값은 「시작 ~ 내 마지막 피어」다.\
  예: `ORDER BY salary` 에서 `ann` 의 프레임은 `[ann, eve]` 라서 합이 600이다([28번](../28-window-frames-rows-range-groups/)).
- **누적합(running total)** — 앞에서부터 자기까지 더해 온 합.\
  예: `SUM(salary) OVER (PARTITION BY dept_id ORDER BY id)` 가 `300 → 800 → 1100 → 1600`.
- **`NULLS FIRST`/`NULLS LAST`** — `NULL` 을 앞에 둘지 뒤에 둘지 지정하는 절. **PG 에만 있다.**\
  예: `ORDER BY salary NULLS LAST`. MySQL 에서는 `ERROR 1064` 가 난다([08번](../08-order-by-null-position-stability/)).
- **별칭(alias)** — `AS` 로 붙인 새 이름. `SELECT` 칸에서 태어난다.\
  예: `salary * 12 AS annual`. `OVER` 절에서는 못 쓴다(7번).

## 더 들어가면

- **`PARTITION BY` 에 여러 열을 적을 수 있다** — `PARTITION BY dept_id, salary` 는 두 값의 조합으로 칸을 나눈다.\
  칸이 잘게 쪼개질수록 각 칸의 행이 줄고, 결국 칸마다 1행이 되면 계산의 뜻이 없어진다.
- **같은 `OVER` 절을 여러 번 적으면 엔진이 한 번만 계산한다** — 다만 **한 글자라도 다르면 다른 창**이다.\
  그래서 `WINDOW` 절로 이름을 붙이는 편이 안전하다. 그 문법은 [31번](../31-window-evaluation-timing/)에 있다.
- **파티션 경계에서 계산이 초기화된다** — 누적합이 칸이 바뀔 때 다시 0부터 쌓인다(3번의 `gus` 가 400 부터 시작한 것).\
  「부서가 바뀌어도 이어서 쌓이는 누적」이 필요하면 `PARTITION BY` 를 빼야 한다.
- **`ORDER BY` 의 방향(`DESC`)도 프레임을 뒤집는다** — 「자기 앞」이 「나보다 큰 값」이 된다.\
  순위 함수에서 이 방향이 곧 1등의 정의가 된다([29번](../29-ranking-functions/)).
