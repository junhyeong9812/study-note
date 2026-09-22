# sql/28-프레임 — `ROWS`·`RANGE`·`GROUPS` 와 기본 프레임 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 모든 질의는 [1-question.md](1-question.md) 머리의 `WITH emp8 AS (...)` CTE 를 앞에 붙여 돌렸다.\
> 문서 근거는 [PG 18 Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 Window Function Frame Specification](https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 두 열은 **같다** — `ann` 은 **600**. 기본 프레임이 `RANGE … CURRENT ROW` 이기 때문이다

**출력**

```text
### SQL: SELECT name, salary,
                SUM(salary) OVER (ORDER BY salary) AS implicit,
                SUM(salary) OVER (ORDER BY salary RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS explicit_range,
                SUM(salary) OVER (ORDER BY salary ROWS  BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS explicit_rows
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary | implicit | explicit_range | explicit_rows
------+--------+----------+----------------+---------------
 ann  |    300 |      600 |            600 |           600
 eve  |    300 |      600 |            600 |           300
 dan  |    400 |     1800 |           1800 |          1000
 gus  |    400 |     1800 |           1800 |          1800
 hui  |    400 |     1800 |           1800 |          1400
 bob  |    500 |     2800 |           2800 |          2800
 fay  |    500 |     2800 |           2800 |          2300
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+----------+----------------+---------------+
| name | salary | implicit | explicit_range | explicit_rows |
+------+--------+----------+----------------+---------------+
| ann  |    300 |      600 |            600 |           300 |
| eve  |    300 |      600 |            600 |           600 |
| dan  |    400 |     1800 |           1800 |          1000 |
| gus  |    400 |     1800 |           1800 |          1400 |
| hui  |    400 |     1800 |           1800 |          1800 |
| bob  |    500 |     2800 |           2800 |          2300 |
| fay  |    500 |     2800 |           2800 |          2800 |
+------+--------+----------+----------------+---------------+
```

**왜 그런가**

```text
OVER (ORDER BY salary)
  가 실제로는
OVER (ORDER BY salary RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)

ann 의 프레임 = 시작 ~ "ann 의 마지막 피어"
             = [ann(300), eve(300)]
             -> 600     ( 300 이 아니다 )
```

★ **「안 적은 것」과 「적은 것」이 두 엔진에서 한 자리도 안 다르다.** 이것이 기본값의 증명이다.

PG 문서: *"The default framing option is `RANGE UNBOUNDED PRECEDING`, which is the same as `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. With `ORDER BY`, this sets the frame to be all rows from the partition start up through the current row's last `ORDER BY` peer."*

셋째 열(`explicit_rows`)은 3번의 주인공이다 — **여기서는 「기본값이 `ROWS` 가 아니다」는 사실까지만** 읽는다.

> **프레임(frame)** — 창 안에서 실제로 계산에 쓰이는 범위.\
> 예: `ann` 의 창은 7행이지만 기본 프레임은 `[ann, eve]` 두 행이라 합이 600이다.

---

### 2. 규칙은 하나다 — 「**내 마지막 피어까지**」가 「모두가 피어」인 상황에 적용된 것이다

```text
기본 프레임 = 파티션 시작 ~ 현재 행의 마지막 피어

ORDER BY 가 있다  -> 키로 비교 -> 같은 값끼리만 피어 -> 프레임이 중간에서 끊긴다
ORDER BY 가 없다  -> 비교할 키가 없다 -> "모든 행이 같다" -> 전원이 피어
                                       -> 마지막 피어 = 칸의 마지막 행
                                       -> 프레임 = 칸 전체
```

**출력으로 확인한다** — `OVER ()` 와 「창 전체」를 명시한 것이 같은 답을 낸다.

```text
### SQL: SELECT name, salary, SUM(salary) OVER () AS no_order,
                SUM(salary) OVER (ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS explicit_all
         FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | salary | no_order | explicit_all
------+--------+----------+--------------
 ann  |    300 |     2800 |         2800
 bob  |    500 |     2800 |         2800
 cho  |   NULL |     2800 |         2800
 dan  |    400 |     2800 |         2800
 eve  |    300 |     2800 |         2800
 fay  |    500 |     2800 |         2800
 gus  |    400 |     2800 |         2800
 hui  |    400 |     2800 |         2800
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+----------+--------------+
| name | salary | no_order | explicit_all |
+------+--------+----------+--------------+
| ann  |    300 |     2800 |         2800 |
| bob  |    500 |     2800 |         2800 |
| cho  |   NULL |     2800 |         2800 |
| dan  |    400 |     2800 |         2800 |
| eve  |    300 |     2800 |         2800 |
| fay  |    500 |     2800 |         2800 |
| gus  |    400 |     2800 |         2800 |
| hui  |    400 |     2800 |         2800 |
+------+--------+----------+--------------+
```

★ **「`ORDER BY` 없으면 전체」는 특례가 아니다.** 규칙이 하나이고 갈래가 없다는 것이 이 답의 요점이다.\
MySQL 문서가 괄호로 그 이유를 적는다: *"(because, without `ORDER BY`, all partition rows are peers)"*.

---

### 3. `ann`/`eve` 의 `range_sum` 은 둘 다 **600**, `rows_sum` 은 **두 엔진에서 서로 반대**다

**출력**

```text
### SQL: SELECT name, salary, SUM(salary) OVER (ORDER BY salary) AS range_sum,
                SUM(salary) OVER (ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_sum
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary | range_sum | rows_sum
------+--------+-----------+----------
 ann  |    300 |       600 |      600
 eve  |    300 |       600 |      300
 dan  |    400 |      1800 |     1000
 gus  |    400 |      1800 |     1800
 hui  |    400 |      1800 |     1400
 bob  |    500 |      2800 |     2800
 fay  |    500 |      2800 |     2300
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+-----------+----------+
| name | salary | range_sum | rows_sum |
+------+--------+-----------+----------+
| ann  |    300 |       600 |      300 |
| eve  |    300 |       600 |      600 |
| dan  |    400 |      1800 |     1000 |
| gus  |    400 |      1800 |     1400 |
| hui  |    400 |      1800 |     1800 |
| bob  |    500 |      2800 |     2300 |
| fay  |    500 |      2800 |     2800 |
+------+--------+-----------+----------+
```

**왜 그런가**

```text
            PG        MySQL
 ann  300 |  600  |   300     <- 서로 반대
 eve  300 |  300  |   600     <- 서로 반대
 gus  400 | 1800  |  1400     <- 다르다
 hui  400 | 1400  |  1800     <- 다르다
 bob  500 | 2800  |  2300     <- 다르다
 fay  500 | 2300  |  2800     <- 다르다

 range_sum 열은 두 엔진이 600/600/1800/1800/1800/2800/2800 으로 똑같았다
```

★★ **`RANGE` 는 같고 `ROWS` 만 갈렸다.** 이유 한 줄 —\
**`ROWS` 는 「몇 번째 행인가」를 세는데, 동률 안의 순서를 질의문이 정하지 않았다.**\
`ORDER BY salary` 는 `ann` 과 `eve` 를 구별하지 못하므로, 누가 먼저인지는 **엔진이 정한다.**

`RANGE` 는 「어떤 값인가」만 보므로 동률 안의 순서를 알 필요가 없다 — 그래서 답이 하나로 정해진다.

★ **「누적합이 동률에서 튄다」는 불평은 `RANGE` 를 오해한 것이다.**\
`RANGE` 는 튀는 게 아니라 **질의문이 시킨 만큼만 정직하게** 답한 것이다.

---

### 4. 동률 안의 순서를 **질의문이 말하지 않았기** 때문이다

```text
ORDER BY salary 가 말한 것        말하지 않은 것
"300 < 400 < 500"               "ann 과 eve 중 누가 먼저인가"
                                          ^^^^^^^^^^^^^^^^^^
                                  ROWS 는 이걸 알아야 답할 수 있다
                                  RANGE 는 알 필요가 없다
```

[08번](../08-order-by-null-position-stability/) 5번이 같은 것을 정렬에서 보였다 — **동률의 순서는 아무도 보장하지 않는다.**\
거기서는 「행이 섞여 보인다」는 표시 문제였는데, 여기서는 **누적합의 값이 바뀐다.** 같은 뿌리에서 나온 더 무거운 증상이다.

★ **근거의 강도를 구분하라.**

| 근거 | 무엇을 말하나 |
|---|---|
| PG 와 MySQL 의 `rows_sum` 이 다르다 | **`ROWS` 의 답이 하나로 정해지지 않는다**는 반증. 양쪽 출력이 다 있다 |
| 한 엔진에서 여러 번 돌려 같았다 | **보장이 아니다.** 같은 계획을 썼을 뿐이다 |

그래서 이 결론은 **「두 엔진이 갈렸다」는 사실**에 걸려 있고, 한쪽만 보면 세지 않는다.

---

### 5. `ORDER BY` 에 **고유 키를 더한다** — 동률 자체를 없앤다

**출력**

```text
### SQL: SELECT name, salary, SUM(salary) OVER (ORDER BY salary, id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_sum
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rows_sum        +------+--------+----------+
------+--------+----------       | name | salary | rows_sum |
 ann  |    300 |      300        +------+--------+----------+
 eve  |    300 |      600        | ann  |    300 |      300 |
 dan  |    400 |     1000        | eve  |    300 |      600 |
 gus  |    400 |     1400        | dan  |    400 |     1000 |
 hui  |    400 |     1800        | gus  |    400 |     1400 |
 bob  |    500 |     2300        | hui  |    400 |     1800 |
 fay  |    500 |     2800        | bob  |    500 |     2300 |
(7 rows)                         | fay  |    500 |     2800 |
                                 +------+--------+----------+
```

**왜 그런가**

```text
ORDER BY salary      -> ann 과 eve 가 동률 -> ROWS 의 답이 엔진에 달렸다
ORDER BY salary, id  -> 동률이 사라진다     -> ROWS 의 답이 하나로 정해진다
                        ^^^^^^^^^^^^^^
                        id 가 기본키라 같은 값이 없다
```

★ **3번에서 갈렸던 두 엔진이 여기서는 한 자리도 안 갈린다.** 고친 것은 `ORDER BY` 에 `, id` 를 더한 것뿐이다.

★ **`RANGE` 도 같이 바뀐다** — 동률이 없으니 `RANGE` 와 `ROWS` 가 이제 같은 답을 낸다.\
「어느 프레임을 쓸까」로 고민하기 전에 **「동률이 있나」를 먼저 본다**가 순서다.

---

### 6. PG 는 돌고(`bob`=**2200**) MySQL 은 `ERROR 1235` 다

**출력**

```text
### SQL: SELECT name, salary, SUM(salary) OVER (ORDER BY salary GROUPS BETWEEN 1 PRECEDING AND CURRENT ROW) AS g
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary |  g
------+--------+------
 ann  |    300 |  600
 eve  |    300 |  600
 dan  |    400 | 1800
 gus  |    400 | 1800
 hui  |    400 | 1800
 bob  |    500 | 2200
 fay  |    500 | 2200
(7 rows)
--- MySQL 8.4.10 ---
ERROR 1235 (42000) at line 1: This version of MySQL doesn't yet support 'GROUPS'
```

**왜 그런가**

```text
덩어리1 [ann eve] = 600    덩어리2 [dan gus hui] = 1200    덩어리3 [bob fay] = 1000

GROUPS BETWEEN 1 PRECEDING AND CURRENT ROW = "앞 덩어리 하나 + 내 덩어리"

 ann·eve : 덩어리1 만           -> 600            (앞 덩어리가 없다)
 dan 무리: 덩어리1 + 덩어리2     -> 600 + 1200 = 1800
 bob·fay : 덩어리2 + 덩어리3     -> 1200 + 1000 = 2200   <- 덩어리1 이 빠진다
```

★ **MySQL 의 거부 문구가 `ERROR 1064`(문법 없음)가 아니다.** 파서는 `GROUPS` 라는 낱말을 알아보고,\
**실행 단계에서** *"doesn't yet support"* 라고 말한다. **`yet`** 이라는 낱말이 앞으로의 여지를 말하고 있다.

목록 README 의 방언 표기(`ROWS`/`RANGE`/**`GROUPS`**(PG 11+) + `EXCLUDE` 대 `ROWS`/`RANGE` 만)가 **이 출력으로 확인됐다.**

---

### 7. `ROWS` 는 **덩어리 크기를 모르고**, `RANGE` 는 **값 간격에 기대야** 하기 때문이다

```text
요구: "나와 앞 등수 하나까지"

ROWS n PRECEDING 으로 적으려면   n = 앞 덩어리의 행 수 + 내 앞 피어 수
                                 -> 행마다 다르다. 상수로 못 적는다
                                 (덩어리2 는 3행이고 덩어리1 은 2행이다)

RANGE n PRECEDING 으로 적으려면  n = 등수 사이의 값 차이
                                 -> 300·400·500 이면 100 이지만
                                    300·400·900 이면 안 맞는다
                                 -> 값이 고르다는 가정에 기대게 된다

GROUPS 1 PRECEDING               -> "덩어리 하나" 라고 그대로 적는다
```

★ **`GROUPS` 는 「세는 단위」가 하나 더 있는 것**이지 다른 두 개의 편의 문법이 아니다.\
요구가 「등수」·「같은 날짜 묶음」처럼 **덩어리 단위**로 오면 `GROUPS` 만이 그대로 옮겨 적힌다.

**PG 전용이므로** 이식 계획이 있으면 미리 판단해야 한다. MySQL 로 옮길 거면 `DENSE_RANK` 로 등수를 먼저 만들고\
그 등수를 키로 `RANGE 1 PRECEDING` 을 쓰는 우회가 있다 — **이 우회는 던져 보지 않았다.** 형태만 적는다.

---

### 8. `CURRENT ROW` 는 나만, `GROUP` 은 내 덩어리 통째로, `TIES` 는 피어만 (나는 남김)

**출력**

```text
### SQL: SELECT name, salary,
                SUM(salary) OVER (ORDER BY salary RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW EXCLUDE CURRENT ROW) AS r
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary |  r
------+--------+------
 ann  |    300 |  300
 eve  |    300 |  300
 dan  |    400 | 1400
 gus  |    400 | 1400
 hui  |    400 | 1400
 bob  |    500 | 2300
 fay  |    500 | 2300
(7 rows)
--- MySQL 8.4.10 ---
ERROR 1235 (42000) at line 1: This version of MySQL doesn't yet support 'EXCLUDE'
```

*(이 출력은 [2-summary.md](2-summary.md) 5번의 것과 같은 질의다. 기본 프레임의 `600/600/1800/1800/1800/2800/2800` 과 견주어 보라.)*

```text
### SQL: SELECT name, salary,
                SUM(salary) OVER (ORDER BY salary RANGE UNBOUNDED PRECEDING EXCLUDE GROUP) AS ex_group,
                SUM(salary) OVER (ORDER BY salary RANGE UNBOUNDED PRECEDING EXCLUDE TIES)  AS ex_ties
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary | ex_group | ex_ties
------+--------+----------+---------
 ann  |    300 |     NULL |     300
 eve  |    300 |     NULL |     300
 dan  |    400 |      600 |    1000
 gus  |    400 |      600 |    1000
 hui  |    400 |      600 |    1000
 bob  |    500 |     1800 |    2300
 fay  |    500 |     1800 |    2300
(7 rows)
--- MySQL 8.4.10 ---
ERROR 1235 (42000) at line 1: This version of MySQL doesn't yet support 'EXCLUDE'
```

**왜 그런가 — `ann` 한 행에 셋의 차이가 다 보인다**

```text
ann 의 기본 프레임 = [ann(300), eve(300)] -> 600

EXCLUDE CURRENT ROW : [eve]        -> 300    나만 뺀다
EXCLUDE TIES        : [ann]        -> 300    피어(eve)만 빼고 나는 남긴다
EXCLUDE GROUP       : []           -> NULL   덩어리 통째로 -> 프레임이 빈다
                                      ^^^^
                        빈 입력의 SUM 은 NULL 이다 (21번 3번)
```

★ **`EXCLUDE CURRENT ROW` 와 `EXCLUDE TIES` 가 `ann` 에서 우연히 같은 300 이다** — 둘 다 한 행씩 남았기 때문이다.\
`dan` 무리(3행)를 보면 갈린다 — `ex_ties` 는 1000(`600+400`, 자기만 남김), `ex_group` 은 600(덩어리 통째로 빠짐)이다.

**셋 다 PG 전용**이다. MySQL 은 `GROUPS` 와 **같은 `ERROR 1235`** 로 거부한다 — 두 기능이 같은 방식으로 빠져 있다.

---

### 9. (A)만 돈다 — (B)·(C)는 두 엔진 다 에러이고 **메시지의 나눔이 다르다**

**출력**

```text
### SQL: SELECT name, salary, SUM(salary) OVER (ORDER BY salary RANGE BETWEEN 100 PRECEDING AND 100 FOLLOWING) AS r
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary |  r              +------+--------+------+
------+--------+------           | name | salary | r    |
 ann  |    300 | 1800            +------+--------+------+
 eve  |    300 | 1800            | ann  |    300 | 1800 |
 dan  |    400 | 2800            | eve  |    300 | 1800 |
 gus  |    400 | 2800            | dan  |    400 | 2800 |
 hui  |    400 | 2800            | gus  |    400 | 2800 |
 bob  |    500 | 2200            | hui  |    400 | 2800 |
 fay  |    500 | 2200            | bob  |    500 | 2200 |
(7 rows)                         | fay  |    500 | 2200 |
                                 +------+--------+------+
```

```text
### SQL: SELECT name, salary, SUM(salary) OVER (ORDER BY salary, id RANGE BETWEEN 1 PRECEDING AND CURRENT ROW) AS r
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
ERROR:  RANGE with offset PRECEDING/FOLLOWING requires exactly one ORDER BY column
LINE 7: ) SELECT name, salary, SUM(salary) OVER (ORDER BY salary, id...
                                                ^
--- MySQL 8.4.10 ---
ERROR 3587 (HY000) at line 1: Window '<unnamed window>' with RANGE N PRECEDING/FOLLOWING frame requires exactly one ORDER BY expression, of numeric or temporal type
```

```text
### SQL: SELECT name, salary, SUM(salary) OVER (ORDER BY name RANGE BETWEEN 1 PRECEDING AND CURRENT ROW) AS r
         FROM emp8 ORDER BY id;
--- PG 18.6 ---
ERROR:  RANGE with offset PRECEDING/FOLLOWING is not supported for column type text
LINE 7: ...ry, SUM(salary) OVER (ORDER BY name RANGE BETWEEN 1 PRECEDIN...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 3587 (HY000) at line 1: Window '<unnamed window>' with RANGE N PRECEDING/FOLLOWING frame requires exactly one ORDER BY expression, of numeric or temporal type
```

**왜 그런가**

```text
RANGE n PRECEDING 은 "내 키 값에서 n 을 뺀 값" 을 경계로 삼는다

  300 - 100  -> 200      뜻이 있다
  'ann' - 1  -> ???      뜻이 없다                     -> (C) 거부
  (300,1) - 1 -> ???     두 값에서 무엇을 빼나          -> (B) 거부
```

★ **거부하는 이유는 같고 메시지를 나누는 방식이 다르다.**\
PG 는 **두 사유를 두 문장**으로 나눈다(키 개수 / 타입). MySQL 은 **한 문장에 둘 다** 적는다(`ERROR 3587`).\
그래서 MySQL 에서 (C)를 만나면 *"exactly one"* 이라는 문구에 속아 키 개수를 의심하게 된다 — **실제 원인은 타입**이다.

★ **`ROWS` 에는 이 제약이 없다.** 행 수를 세는 데는 키 개수도 타입도 상관없기 때문이다.

(A)의 값 검산 — `ann`(300)의 프레임은 `salary` 가 200~400 인 행 `[ann eve dan gus hui]` 이라 `300+300+400+400+400 = 1800` 이다.

---

### 10. 프레임은 **3행**인데 `moving` 은 **400** 이다 — `NULL` 이 분모에서 빠졌다

**출력**

```text
### SQL: SELECT name, salary, AVG(salary) OVER (ORDER BY id ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) AS moving
         FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | salary |        moving
------+--------+----------------------
 ann  |    300 | 400.0000000000000000
 bob  |    500 | 400.0000000000000000
 cho  |   NULL | 450.0000000000000000
 dan  |    400 | 350.0000000000000000
 eve  |    300 | 400.0000000000000000
 fay  |    500 | 400.0000000000000000
 gus  |    400 | 433.3333333333333333
 hui  |    400 | 400.0000000000000000
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+----------+
| name | salary | moving   |
+------+--------+----------+
| ann  |    300 | 400.0000 |
| bob  |    500 | 400.0000 |
| cho  |   NULL | 450.0000 |
| dan  |    400 | 350.0000 |
| eve  |    300 | 400.0000 |
| fay  |    500 | 400.0000 |
| gus  |    400 | 433.3333 |
| hui  |    400 | 400.0000 |
+------+--------+----------+
```

**왜 그런가**

```text
bob 의 프레임 = [ann(300), bob(500), cho(NULL)]   행은 3개다

AVG 의 분모는 COUNT(*) 가 아니라 COUNT(열) 이다  (21번 2번)
  -> NULL 인 cho 는 더해지지도, 분모에 세어지지도 않는다
  -> (300 + 500) / 2 = 400
                   ^
                   3 이 아니다
```

★ **화면에서 이 차이가 안 보인다.** 「최근 3건의 이동 평균」이라고 이름 붙여 놓고 실제로는 2건의 평균인 행이 섞인다.\
**「`NULL` 이 0으로 더해졌나 / 아예 빠졌나」를 매번 물어야 하는 자리**이고, 답은 언제나 「빠졌다」다.

**끝 행에서도 프레임이 짧아진다** — `ann` 은 앞이 없어 2행, `hui` 는 뒤가 없어 2행이다. **에러가 아니다.**\
「처음·마지막 행의 이동 평균은 신뢰할 수 없다」는 판단은 질의가 아니라 사람이 해야 한다.

`gus` 의 `433.33` 은 `(500+400+400)/3` 이다 — 그 행의 프레임에는 `NULL` 이 없어 분모가 3이다.

---

### 11. **에러가 아니다** — 그래서 더 위험하다

**출력**

```text
### SQL: SELECT name, salary, SUM(salary) OVER (ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS r
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary |  r              +------+--------+------+
------+--------+-----            | name | salary | r    |
 ann  |    300 | 300             +------+--------+------+
 bob  |    500 | 800             | ann  |    300 |  300 |
 cho  |   NULL | 500             | bob  |    500 |  800 |
 dan  |    400 | 400             | cho  |   NULL |  500 |
 eve  |    300 | 700             | dan  |    400 |  400 |
 fay  |    500 | 800             | eve  |    300 |  700 |
 gus  |    400 | 900             | fay  |    500 |  800 |
 hui  |    400 | 800             | gus  |    400 |  900 |
(8 rows)                         | hui  |    400 |  800 |
                                 +------+--------+------+
```

**왜 그런가**

```text
ROWS 는 "내 앞 행" 을 센다
  -> 그런데 ORDER BY 가 없으면 "앞" 이 정의되지 않았다
  -> 엔진이 읽은 순서를 그냥 쓴다
  -> 계획이 바뀌면 답이 바뀐다
```

★ **두 엔진의 값이 한 자리도 안 갈렸다. 그런데 그것은 보장이 아니라 관찰이다.**\
지금 두 엔진이 **우연히 같은 순서로 읽었을** 뿐이고, 인덱스가 생기거나 병렬 스캔이 붙으면 달라질 수 있다.\
[08번](../08-order-by-null-position-stability/) 6번이 `ORDER BY` 없는 `SELECT` 에서 같은 성격의 함정을 다뤘다.

★ **3번과 견줘 보라.** 3번은 두 엔진이 **갈려서** 비결정성이 드러났고, 여기는 **안 갈려서** 안 드러났다.\
**드러나지 않은 비결정성이 더 나쁘다** — 테스트를 통과하고 운영에서 터진다.

**규칙 한 줄: 프레임을 적을 거면 `ORDER BY` 를 반드시 같이 적는다.**

---

### 12. 달라지지 않는다 — **순위 함수는 프레임을 보지 않는다**

**출력**

```text
### SQL: SELECT name, salary, RANK() OVER (ORDER BY salary) AS plain,
                RANK() OVER (ORDER BY salary ROWS UNBOUNDED PRECEDING) AS framed,
                ROW_NUMBER() OVER (ORDER BY salary ROWS UNBOUNDED PRECEDING) AS rn_framed
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary | plain | framed | rn_framed
------+--------+-------+--------+-----------
 ann  |    300 |     1 |      1 |         2
 eve  |    300 |     1 |      1 |         1
 dan  |    400 |     3 |      3 |         3
 gus  |    400 |     3 |      3 |         5
 hui  |    400 |     3 |      3 |         4
 bob  |    500 |     6 |      6 |         7
 fay  |    500 |     6 |      6 |         6
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+-------+--------+-----------+
| name | salary | plain | framed | rn_framed |
+------+--------+-------+--------+-----------+
| ann  |    300 |     1 |      1 |         1 |
| eve  |    300 |     1 |      1 |         2 |
| dan  |    400 |     3 |      3 |         3 |
| gus  |    400 |     3 |      3 |         4 |
| hui  |    400 |     3 |      3 |         5 |
| bob  |    500 |     6 |      6 |         6 |
| fay  |    500 |     6 |      6 |         7 |
+------+--------+-------+--------+-----------+
```

**왜 그런가**

```text
plain 과 framed 가 두 엔진 모두에서 한 자리도 안 다르다
  -> 프레임 지정이 RANK 의 값에 아무 영향을 주지 않았다
  -> "에러가 아니라 무시된다"  <- 이 점이 함정이다
```

PG 문서가 명시한다 — `row_number`·`rank`·`dense_rank`·`percent_rank`·`cume_dist`·`ntile`·`lag`·`lead` 는 **프레임에 의존하지 않는다.**

★ **`ROWS` 를 적어도 에러가 안 나고 값도 안 바뀐다.** 「적었으니 뭔가 달라졌겠지」라고 믿으면 그대로 넘어간다.

★ **`rn_framed` 열은 여전히 두 엔진에서 갈린다.** 그건 프레임 때문이 아니라 **동률 순서** 때문이다([29번](../29-ranking-functions/)).\
**프레임을 의심할 자리와 동률을 의심할 자리를 구분**하는 것이 이 출력의 값이다.

★ 다만 **`lag`/`lead` 는 프레임을 무시하는데 `first_value`/`last_value`/`nth_value` 는 프레임을 본다** —\
그 비대칭이 [30번](../30-offset-and-boundary-functions/)의 `LAST_VALUE` 함정을 만든다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 기본 프레임 = `RANGE` (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `implicit` = `explicit_range` |
| `ORDER BY` 없을 때 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `OVER ()` = 창 전체 |
| ★ `ROWS` 대 `RANGE` (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`ROWS` 가 두 엔진에서 갈렸다 — 이 주제의 핵심 근거** |
| 고유 키를 더한 `ROWS` (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **갈림이 사라졌다** |
| `GROUPS` (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL `ERROR 1235 … 'GROUPS'`** |
| `EXCLUDE` 세 형태 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL `ERROR 1235 … 'EXCLUDE'`** · `ex_group` 이 `NULL` |
| 오프셋 `RANGE` (9번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 값 범위 1회 + **에러 2회** |
| 이동 평균 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 분모가 `NULL` 로 줄어드는 행 확인 |
| `ORDER BY` 없는 `ROWS` (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 없음 · 두 엔진 같음 — 관찰이지 보장 아님** |
| 순위 함수 + 프레임 (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `plain` = `framed` |

**구현 의존 항목** — **동률이 있을 때 `ROWS` 프레임의 값**과 **`ORDER BY` 없는 `ROWS` 의 행 순서**.\
둘 다 **아무도 보장하지 않는다.** 앞의 것은 두 엔진이 갈려서 드러났고, 뒤의 것은 **안 갈려서 안 드러났다.**

**방언 항목** — **`GROUPS` 와 `EXCLUDE`**(PG 11+ 전용, MySQL `ERROR 1235`)와 오프셋 `RANGE` 의 **에러 메시지 나눔**(6·8·9번).\
**언어 보장 항목** — 1·2·10·12번. 기본 프레임, `ORDER BY` 없을 때의 창 전체, `AVG` 의 분모, 순위 함수의 프레임 무시는\
두 문서가 같은 모양으로 적고 두 엔진의 출력도 같았다.

**버전** — `ROWS`·`RANGE` 는 PG 8.4 · MySQL 8.0, `GROUPS`·`EXCLUDE` 는 PG 11 부터다.\
다음 버전에서 다시 찍을 것은 **6·8번**이다 — MySQL 이 *"doesn't **yet** support"* 라고 답했기 때문이다.

**재지 않은 것** — `ROWS` 와 `RANGE` 의 계산 비용 차이, 프레임 폭이 성능에 주는 영향. **측정하지 않았으므로 적지 않았다.**\
**던져 보지 않은 것** — 7번에 적은 `DENSE_RANK` + `RANGE 1 PRECEDING` 우회(형태만 적었다)와 날짜 `INTERVAL` 프레임(날짜 열이 없다).
