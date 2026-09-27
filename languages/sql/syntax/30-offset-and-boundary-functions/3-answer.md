# sql/30-오프셋·경계 함수 — `LAG`·`LEAD`·`FIRST_VALUE`·`LAST_VALUE` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> MySQL 의 경고는 **`SHOW WARNINGS` 로 따로 물어서** 받았다(11번).\
> 모든 질의는 [1-question.md](1-question.md) 머리의 `WITH emp8 AS (...)` CTE 를 앞에 붙여 돌렸다.\
> 문서 근거는 [PG 18 Window Functions](https://www.postgresql.org/docs/18/functions-window.html) · [MySQL 8.4 Window Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 넷 다 `NULL` 이지만 **뜻이 두 가지**다 — 경계 둘, 값이 `NULL` 둘

**출력**

```text
### SQL: SELECT name, salary, LAG(salary) OVER w AS prev, LEAD(salary) OVER w AS next,
                salary - LAG(salary) OVER w AS diff
         FROM emp8 WINDOW w AS (ORDER BY id) ORDER BY id;
--- PG 18.6 ---
 name | salary | prev | next | diff
------+--------+------+------+------
 ann  |    300 | NULL |  500 | NULL
 bob  |    500 |  300 | NULL |  200
 cho  |   NULL |  500 |  400 | NULL
 dan  |    400 | NULL |  300 | NULL
 eve  |    300 |  400 |  500 | -100
 fay  |    500 |  300 |  400 |  200
 gus  |    400 |  500 |  400 | -100
 hui  |    400 |  400 | NULL |    0
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+------+------+------+
| name | salary | prev | next | diff |
+------+--------+------+------+------+
| ann  |    300 | NULL |  500 | NULL |
| bob  |    500 |  300 | NULL |  200 |
| cho  |   NULL |  500 |  400 | NULL |
| dan  |    400 | NULL |  300 | NULL |
| eve  |    300 |  400 |  500 | -100 |
| fay  |    500 |  300 |  400 |  200 |
| gus  |    400 |  500 |  400 | -100 |
| hui  |    400 |  400 | NULL |    0 |
+------+--------+------+------+------+
```

**왜 그런가**

```text
 id 순:  ann(300) bob(500) cho(NULL) dan(400) eve(300) fay(500) gus(400) hui(400)
          ^                  ^^^^^                                          ^
          창의 첫 행          값이 NULL                                  창의 마지막 행

 ann.prev = NULL   <- 앞 행이 없다        (경계)
 hui.next = NULL   <- 뒤 행이 없다        (경계)
 bob.next = NULL   <- 뒤 행은 cho 다. 그 행의 값이 NULL   (값)
 dan.prev = NULL   <- 앞 행은 cho 다. 그 행의 값이 NULL   (값)
```

★★ **화면에서 네 개가 똑같이 `NULL`** 이다. `bob` 을 마지막 행으로 오해하기 딱 좋은데 **뒤에 다섯 행이 더 있다.**

구분하려면 **`NULL` 일 수 없는 열을 같이 가져온다.**

```sql
LEAD(id) OVER (ORDER BY id)   -- 이게 NULL 이면 진짜 마지막 행이다
```

`hui` 의 `diff` 가 **0**인 것도 읽을거리다 — `gus`(400)와 같은 값이라 차이가 0이다.\
**`NULL` 은 「모른다」, 0은 「안 변했다**」로 뜻이 전혀 다르다([21번](../21-aggregate-functions-count-forms/)과 같은 대비).

> **경계의 `NULL`** — 가져올 행 자체가 없어서 나온 `NULL`.\
> 예: 첫 행의 `LAG`. 값이 `NULL` 인 경우와 화면에서 구분되지 않는다.

---

### 2. `ann` 은 **0**, `dan` 은 **`NULL`** — 기본값은 「행이 없을 때」만 쓰인다

**출력**

```text
### SQL: SELECT name, salary, LAG(salary, 2) OVER (ORDER BY id) AS lag2,
                LAG(salary, 1, 0) OVER (ORDER BY id) AS lag_def,
                LEAD(salary, 1, -1) OVER (ORDER BY id) AS lead_def
         FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | salary | lag2 | lag_def | lead_def
------+--------+------+---------+----------
 ann  |    300 | NULL |       0 |      500
 bob  |    500 | NULL |     300 |     NULL
 cho  |   NULL |  300 |     500 |      400
 dan  |    400 |  500 |    NULL |      300
 eve  |    300 | NULL |     400 |      500
 fay  |    500 |  400 |     300 |      400
 gus  |    400 |  300 |     500 |      400
 hui  |    400 |  500 |     400 |       -1
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+------+---------+----------+
| name | salary | lag2 | lag_def | lead_def |
+------+--------+------+---------+----------+
| ann  |    300 | NULL |       0 |      500 |
| bob  |    500 | NULL |     300 |     NULL |
| cho  |   NULL |  300 |     500 |      400 |
| dan  |    400 |  500 |    NULL |      300 |
| eve  |    300 | NULL |     400 |      500 |
| fay  |    500 |  400 |     300 |      400 |
| gus  |    400 |  300 |     500 |      400 |
| hui  |    400 |  500 |     400 |       -1 |
+------+--------+------+---------+----------+
```

**왜 그런가**

```text
ann : 앞 행이 없다        -> 기본값 0 이 쓰인다        -> 0
dan : 앞 행은 cho 다. 있다 -> 기본값이 안 쓰인다
                          -> cho 의 salary 를 그대로 -> NULL
```

★ **기본값을 줬다고 모든 `NULL` 이 사라지지 않는다.** 1번의 두 `NULL` 이 **여기서 행동으로 갈린다** —\
경계의 `NULL` 만 메워지고 값의 `NULL` 은 그대로다.

`lag2` 의 `eve` 가 `NULL` 인 것도 같은 이유다 — 두 칸 앞은 `cho` 이고 **`cho` 는 있는데 값이 `NULL`** 이다.\
`ann`·`bob` 의 `lag2` 만 진짜 경계다.

`lead_def` 의 `hui` 가 **-1** 인 것이 기본값이 쓰인 또 하나의 자리다 — 마지막 행이라 뒤 행이 없다.

**두 엔진이 한 자리도 안 갈렸다.**

---

### 3. `lv` 열이 **`salary` 열과 똑같다** — 두 엔진 모두 그렇다

**출력**

```text
### SQL: SELECT name, salary,
                LAST_VALUE(salary) OVER (ORDER BY salary) AS lv_default,
                LAST_VALUE(salary) OVER (ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lv_fixed
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary | lv_default | lv_fixed
------+--------+------------+----------
 ann  |    300 |        300 |      500
 eve  |    300 |        300 |      500
 dan  |    400 |        400 |      500
 gus  |    400 |        400 |      500
 hui  |    400 |        400 |      500
 bob  |    500 |        500 |      500
 fay  |    500 |        500 |      500
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+------------+----------+
| name | salary | lv_default | lv_fixed |
+------+--------+------------+----------+
| ann  |    300 |        300 |      500 |
| eve  |    300 |        300 |      500 |
| dan  |    400 |        400 |      500 |
| gus  |    400 |        400 |      500 |
| hui  |    400 |        400 |      500 |
| bob  |    500 |        500 |      500 |
| fay  |    500 |        500 |      500 |
+------+--------+------------+----------+
```

**왜 그런가**

★★ **「마지막 값」을 물었는데 자기 값이 나왔다.** 정확히는 「**자기 피어의 마지막 값**」이다 —\
`gus`·`hui` 가 둘 다 400 인 것이 그 증거다(자기 값이라면 어차피 같지만, `dan` 도 400 인 것이 피어 때문이다).

★ **이것은 방언이 아니다.** 두 엔진이 **똑같이** 그렇게 한다 — 엔진을 바꿔도 안 고쳐진다.\
PG 문서가 이 함정을 직접 적는다: *"This is likely to give unhelpful results for `last_value` and sometimes also `nth_value`."*

오른쪽 `lv_fixed` 열이 고친 것이다 — 프레임을 창 전체로 열면 전부 **500** 이다.

---

### 4. 기본 프레임이 「**시작 ~ 내 마지막 피어**」라서, 그 끝이 곧 나이기 때문이다

```text
OVER (ORDER BY salary)
  == OVER (ORDER BY salary RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)   <- 28번

salary 오름차순:  ann300  eve300  dan400  gus400  hui400  bob500  fay500

dan 의 프레임 = [ann eve dan gus hui]
                 ^^^                ^^^
        FIRST_VALUE = 300     LAST_VALUE = 400
                              ^^^^^^^^^^^^^^^
                       프레임의 끝이다. 창의 끝이 아니다.
                       bob·fay 는 프레임 밖이라 안 보인다
```

★ **`LAST_VALUE` 는 창을 보는 함수가 아니라 프레임을 보는 함수다.**\
PG 문서가 그렇게 적는다: *"`first_value`, `last_value`, and `nth_value` consider only the rows within the "window frame""*.

★ **동률이 한 겹 더 깊게 만든다.** 프레임 끝이 「나」가 아니라 「**내 마지막 피어**」라서,\
`dan`(첫 400)도 `gus`·`hui` 를 프레임에 넣고 있다. 그래서 셋이 전부 400 이다.\
`RANGE` 를 `ROWS` 로 바꾸면 이번엔 **동률 안의 순서가 비결정적**이 된다([28번](../28-window-frames-rows-range-groups/) 3번) — 그쪽으로 도망가면 안 된다.

---

### 5. 기본 프레임의 **시작**이 이미 `UNBOUNDED PRECEDING` 이기 때문이다

```text
기본 프레임 = [ UNBOUNDED PRECEDING  ...  CURRENT ROW ]
                ^^^^^^^^^^^^^^^^^^^        ^^^^^^^^^^^
                창의 처음 그대로            여기가 문제다

FIRST_VALUE 는 왼쪽 끝을 본다 -> 창의 처음 -> 기대대로
LAST_VALUE  는 오른쪽 끝을 본다 -> 나 자신  -> 기대와 다르다
```

**출력으로 확인한다.**

```text
### SQL: SELECT name, salary, FIRST_VALUE(salary) OVER w AS fv, LAST_VALUE(salary) OVER w AS lv,
                NTH_VALUE(salary, 2) OVER w AS nv
         FROM emp8 WHERE salary IS NOT NULL WINDOW w AS (ORDER BY salary) ORDER BY salary, id;
--- PG 18.6 ---
 name | salary | fv  | lv  | nv
------+--------+-----+-----+-----
 ann  |    300 | 300 | 300 | 300
 eve  |    300 | 300 | 300 | 300
 dan  |    400 | 300 | 400 | 300
 gus  |    400 | 300 | 400 | 300
 hui  |    400 | 300 | 400 | 300
 bob  |    500 | 300 | 500 | 300
 fay  |    500 | 300 | 500 | 300
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+------+------+------+
| name | salary | fv   | lv   | nv   |
+------+--------+------+------+------+
| ann  |    300 |  300 |  300 |  300 |
| eve  |    300 |  300 |  300 |  300 |
| dan  |    400 |  300 |  400 |  300 |
| gus  |    400 |  300 |  400 |  300 |
| hui  |    400 |  300 |  400 |  300 |
| bob  |    500 |  300 |  500 |  300 |
| fay  |    500 |  300 |  500 |  300 |
+------+--------+------+------+------+
```

★ **`fv` 는 전부 300 으로 한 번도 안 흔들린다.** `lv` 만 행마다 다르다.

★ **`FIRST_VALUE` 가 멀쩡한 것은 운이다.** 이름과 계약이 우연히 겹쳤을 뿐,\
프레임을 `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW` 같은 것으로 바꾸면 **`FIRST_VALUE` 도 「창의 처음」이 아니게 된다.**\
**외울 것은 「`LAST_VALUE` 가 이상하다」가 아니라 「이 셋은 프레임을 본다**」다.

---

### 6. 프레임을 열거나 · `ORDER BY` 를 뒤집거나 · 애초에 `MAX` 를 쓴다

```sql
-- (1) 프레임을 창 전체로 연다
LAST_VALUE(salary) OVER (ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)

-- (2) 끝만 연다 — 필요한 것은 끝이지 시작이 아니다
LAST_VALUE(salary) OVER (ORDER BY salary RANGE BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)

-- (3) ORDER BY 를 뒤집고 FIRST_VALUE 를 쓴다 — 프레임을 안 건드린다
FIRST_VALUE(salary) OVER (ORDER BY salary DESC)
```

(2)를 실제로 던졌다.

```text
### SQL: SELECT name, salary, LAST_VALUE(salary) OVER (ORDER BY salary RANGE BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) AS lv_alt
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | lv_alt          +------+--------+--------+
------+--------+--------         | name | salary | lv_alt |
 ann  |    300 |    500          +------+--------+--------+
 eve  |    300 |    500          | ann  |    300 |    500 |
 dan  |    400 |    500          | eve  |    300 |    500 |
 gus  |    400 |    500          | dan  |    400 |    500 |
 hui  |    400 |    500          | gus  |    400 |    500 |
 bob  |    500 |    500          | hui  |    400 |    500 |
 fay  |    500 |    500          | bob  |    500 |    500 |
(7 rows)                         | fay  |    500 |    500 |
                                 +------+--------+--------+
```

★ **네 번째 방법이 사실 제일 흔한 정답이다 — `MAX(salary) OVER ()`.**\
「마지막 행의 값」이 아니라 「**최댓값**」이 진짜 요구인 경우가 많다. 그러면 프레임을 기억할 필요가 없다.

★ **`LAST_VALUE` 가 꼭 필요한 자리는 「끝 행의 *다른* 열**」이다 — 최고 연봉자의 **이름**처럼.\
그때도 (3)의 `FIRST_VALUE` + `DESC` 가 더 안전하다(10번에서 그 형태를 쓴다).

---

### 7. **`FIRST_VALUE`·`LAST_VALUE`·`NTH_VALUE` 가 프레임을 본다.** `LAG`·`LEAD` 는 안 본다

**출력**

```text
### SQL: SELECT name, salary, LAG(salary) OVER (ORDER BY id ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS lag_framed,
                LAG(salary) OVER (ORDER BY id) AS lag_plain
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
 name | salary | lag_framed | lag_plain     +------+--------+------------+-----------+
------+--------+------------+-----------    | name | salary | lag_framed | lag_plain |
 ann  |    300 |       NULL |      NULL     +------+--------+------------+-----------+
 bob  |    500 |        300 |       300     | ann  |    300 |       NULL |      NULL |
 cho  |   NULL |        500 |       500     | bob  |    500 |        300 |       300 |
 dan  |    400 |       NULL |      NULL     | cho  |   NULL |        500 |       500 |
 eve  |    300 |        400 |       400     | dan  |    400 |       NULL |      NULL |
 fay  |    500 |        300 |       300     | eve  |    300 |        400 |       400 |
 gus  |    400 |        500 |       500     | fay  |    500 |        300 |       300 |
 hui  |    400 |        400 |       400     | gus  |    400 |        500 |       500 |
(8 rows)                                    | hui  |    400 |        400 |       400 |
                                            +------+--------+------------+-----------+
```

**왜 그런가**

```text
프레임을 본다   : FIRST_VALUE · LAST_VALUE · NTH_VALUE · 집계(SUM·AVG·COUNT·MIN·MAX)
프레임을 안 본다: LAG · LEAD · ROW_NUMBER · RANK · DENSE_RANK · NTILE · PERCENT_RANK · CUME_DIST
                  ^^^^^^^^^^
        "다른 행의 값을 가져온다" 는 점은 LAST_VALUE 와 같은데 갈린다
```

PG 문서가 프레임에 의존하지 않는 함수를 목록으로 묶어 적는다 —\
`row_number`·`rank`·`dense_rank`·`percent_rank`·`cume_dist`·`ntile`·`lag`·`lead`.

★ **두 열이 같다는 것은 「에러가 아니라 무시된다」는 뜻이다.** 적어 놓고 넘어가기 쉬운 자리다([29번](../29-ranking-functions/) 11번과 같다).

★ **이 비대칭이 이 주제의 뼈대다.** `LAG` 는 안 틀리고 `LAST_VALUE` 만 틀리는 이유가 여기 있다.

---

### 8. `n3` 는 전부 `NULL` 이다 — 그런데 **「3번째 행이 없다」가 아니다**

**출력**

```text
### SQL: SELECT name, salary, NTH_VALUE(salary, 3) OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS n3
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary |  n3             +------+--------+------+
------+--------+------           | name | salary | n3   |
 ann  |    300 | NULL            +------+--------+------+
 bob  |    500 | NULL            | ann  |    300 | NULL |
 cho  |   NULL | NULL            | bob  |    500 | NULL |
 dan  |    400 | NULL            | cho  |   NULL | NULL |
 eve  |    300 | NULL            | dan  |    400 | NULL |
 fay  |    500 | NULL            | eve  |    300 | NULL |
 gus  |    400 | NULL            | fay  |    500 | NULL |
 hui  |    400 | NULL            | gus  |    400 | NULL |
(8 rows)                         | hui  |    400 | NULL |
                                 +------+--------+------+
```

**왜 그런가**

```text
프레임 = 창 전체 = 8행   -> 3번째 행은 분명히 있다
3번째 행 = cho           -> cho 의 salary 가 NULL
                         -> NTH_VALUE 는 그 값을 그대로 돌려준다

"행이 없어서 NULL" 이 아니라 "행의 값이 NULL"
```

★ **1번의 혼동이 여기서 되풀이된다.** `NTH_VALUE` 도 두 가지 이유로 `NULL` 을 준다 —\
**프레임에 n 번째 행이 없을 때**와 **그 행의 값이 `NULL` 일 때**. 화면에서 구분이 안 된다.

확인하려면 **`NULL` 일 수 없는 열**로 같이 뽑는다 — `NTH_VALUE(id, 3) OVER (...)` 가 `NULL` 이면 진짜로 행이 없는 것이다.

★ **프레임을 안 열었으면 이야기가 또 달라진다.** 기본 프레임에서는 앞 두 행(`ann`·`bob`)의 프레임 크기가 3 미만이라\
그 행들은 **진짜로 「3번째가 없어서」** `NULL` 이 된다. 같은 `NULL` 인데 행마다 이유가 다른 셈이다.

---

### 9. **두 엔진 다 거부한다** — PG 는 파서에서, MySQL 은 실행에서

**출력**

```text
### SQL: SELECT name, salary, LAG(salary) IGNORE NULLS OVER (ORDER BY id) AS lag_ign FROM emp8 ORDER BY id;
--- PG 18.6 ---
ERROR:  syntax error at or near "NULLS"
LINE 7: ) SELECT name, salary, LAG(salary) IGNORE NULLS OVER (ORDER ...
                                                  ^
--- MySQL 8.4.10 ---
ERROR 1235 (42000) at line 1: This version of MySQL doesn't yet support 'IGNORE NULLS'
```

```text
### SQL: SELECT name, salary, LAST_VALUE(salary) IGNORE NULLS OVER (ORDER BY id) AS lv_ign FROM emp8 ORDER BY id;
--- PG 18.6 ---
ERROR:  syntax error at or near "NULLS"
LINE 7: ) SELECT name, salary, LAST_VALUE(salary) IGNORE NULLS OVER ...
                                                         ^
--- MySQL 8.4.10 ---
ERROR 1235 (42000) at line 1: This version of MySQL doesn't yet support 'IGNORE NULLS'
```

**왜 그런가**

| | 무엇이라 하나 | 어디서 걸리나 | 무슨 뜻인가 |
|---|---|---|---|
| PG 18.6 | `syntax error at or near "NULLS"` | **파서** | 문법에 그 낱말 자리가 **아예 없다** |
| MySQL 8.4.10 | `doesn't yet support 'IGNORE NULLS'` | **실행** | 파서는 알아보고 **아직 구현이 없다** |

★ **MySQL 의 `ERROR 1235` 가 [28번](../28-window-frames-rows-range-groups/)의 `GROUPS`·`EXCLUDE` 와 같은 번호**다.\
「파싱은 되는데 구현이 없는 것들」이 한 번호로 묶여 있고, **`yet` 이라는 낱말이 앞으로의 여지를 말한다.**

**우회 — 요구가 허락하면 `NULL` 인 행을 아예 뺀다.**

```sql
SELECT name, salary, LAG(salary) OVER (ORDER BY id) FROM emp8 WHERE salary IS NOT NULL;
```

더 일반적인 우회(마지막 비`NULL` 값을 끌고 내려오기)는 **「값이 있는 구간에 번호를 매겨 그 구간의 첫 값을 가져오는」** 관용구인데,\
**이 주제에서 던져 보지 않았다.** 형태만 적고 실행 근거를 붙이지 않는다.

---

### 10. `dept 10` 은 PG `fay` / MySQL `bob`, `dept 20` 은 PG `cho` / MySQL `gus`

**출력**

```text
### SQL: SELECT name, salary, FIRST_VALUE(name) OVER (PARTITION BY dept_id ORDER BY salary DESC) AS top_earner
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | top_earner      +------+--------+------------+
------+--------+------------     | name | salary | top_earner |
 ann  |    300 | fay             +------+--------+------------+
 bob  |    500 | fay             | ann  |    300 | bob        |
 cho  |   NULL | cho             | bob  |    500 | bob        |
 dan  |    400 | dan             | cho  |   NULL | gus        |
 eve  |    300 | fay             | dan  |    400 | dan        |
 fay  |    500 | fay             | eve  |    300 | bob        |
 gus  |    400 | cho             | fay  |    500 | bob        |
 hui  |    400 | cho             | gus  |    400 | gus        |
(8 rows)                         | hui  |    400 | gus        |
                                 +------+--------+------------+
```

**왜 그런가 — 갈릴 자리가 두 군데다**

```text
dept 10 : bob(500) fay(500)  <- 동률. 누가 먼저 서는지 ORDER BY 가 안 정했다
          PG -> fay 가 앞      MySQL -> bob 이 앞        (29번 3번)

dept 20 : cho(NULL) gus(400) hui(400)
          ORDER BY salary DESC 에서
          PG -> NULL 이 가장 큰 값 -> cho 가 맨 앞 -> top_earner = cho
          MySQL -> NULL 이 가장 작은 값 -> cho 가 맨 뒤 -> top_earner = gus   (08번)
```

★★ **PG 에서 「최고 연봉자」 칸에 급여가 `NULL` 인 사람의 이름이 찍힌다.** 에러도 경고도 없다.

**고치는 법 — 갈릴 자리 둘을 둘 다 막는다.**

```sql
FIRST_VALUE(name) OVER (PARTITION BY dept_id ORDER BY (salary IS NULL), salary DESC, id)
--                                            ^^^^^^^^^^^^^^^^^^^^^^^  ^^^^
--                                            NULL 을 뒤로            동률을 깨는 고유 키
```

★ **진단은 언제나 같다 — 「`FIRST_VALUE` 가 이상하다」가 아니라 「`ORDER BY` 가 답을 끝까지 안 정했다」.**\
[08번](../08-order-by-null-position-stability/)·[27번](../27-partition-by-and-window-order-by/)·[29번](../29-ranking-functions/)의 처방이 이 한 줄에 다 들어 있다.

---

### 11. PG 는 **에러**, MySQL 은 **통과** — 그리고 `+ 0` 을 하면 **경고 `1292`** 가 나온다

**출력**

```text
### SQL: SELECT name, LEAD(salary, 1, 'x') OVER (ORDER BY id) AS l FROM emp8 ORDER BY id;
--- PG 18.6 ---
ERROR:  invalid input syntax for type integer: "x"
LINE 7: ) SELECT name, LEAD(salary, 1, 'x') OVER (ORDER BY id) AS l ...
                                       ^
--- MySQL 8.4.10 ---
+------+------+
| name | l    |
+------+------+
| ann  | 500  |
| bob  | NULL |
| cho  | 400  |
| dan  | 300  |
| eve  | 500  |
| fay  | 400  |
| gus  | 400  |
| hui  | x    |
+------+------+
```

```text
### SQL: SELECT name, LEAD(salary, 1, 'x') OVER (ORDER BY id) + 0 AS l FROM emp8 ORDER BY id; SHOW WARNINGS;
--- MySQL 8.4.10 ---
+------+------+
| name | l    |
+------+------+
| ann  |  500 |
| bob  | NULL |
| cho  |  400 |
| dan  |  300 |
| eve  |  500 |
| fay  |  400 |
| gus  |  400 |
| hui  |    0 |
+------+------+
+---------+------+---------------------------------------+
| Level   | Code | Message                               |
+---------+------+---------------------------------------+
| Warning | 1292 | Truncated incorrect DOUBLE value: 'x' |
+---------+------+---------------------------------------+
```

**왜 그런가**

```text
PG    : default 는 value 와 타입이 맞아야 한다 -> 'x' 를 integer 로 못 읽는다 -> 에러
MySQL : 통과시킨다 -> 숫자와 'x' 가 한 열에 섞인다 (hui 행)
        그 열로 계산하면 'x' -> 0 으로 잘린다 -> 경고 1292
                              ^^^^^^^^^^^^^^
                    화면에는 그럴듯한 0 만 남는다.
                    "다음 급여가 없다" 가 "다음 급여가 0" 으로 읽힌다
```

PG 문서가 규정을 적는다: *"instead returns `default` (which must be of a type compatible with `value`)"*.

★ **이 실험은 한쪽에서만 결론이 선다 — 그래서 그렇게 적는다.**

| 출력 | 무엇의 근거인가 |
|---|---|
| PG 의 `ERROR: invalid input syntax for type integer: "x"` | **「기본값은 타입이 맞아야 한다」의 근거**다 |
| MySQL 의 정상 표 | 「통과한다」의 근거일 뿐 **「안전하다」의 근거가 아니다** |
| MySQL 의 `Warning 1292` | 통과한 쪽이 **조용히 값을 바꿨다**는 근거다 |

★ **경고는 `SHOW WARNINGS` 를 물어야 보인다.** 애플리케이션 드라이버가 경고를 안 읽으면\
**에러도 없고 로그도 없이 0이 들어간다** — [21번](../21-aggregate-functions-count-forms/)에서 본 무음 실패와 같은 종류다.

기본값에 표시 문자열을 넣고 싶으면 **바깥에서 문자열로 바꾼다** — `COALESCE(CAST(lead_col AS CHAR), '없음')` 처럼.\
(이 형태는 **던져 보지 않았다.** 타입 변환 규칙은 [35번](../35-type-system-and-casting/)이 정본이다.)

---

### 12. 오프셋 0은 **양쪽에서 자기 자신**, 음수는 **PG 에서 `LEAD`, MySQL 에서 문법 오류**

**출력**

```text
### SQL: SELECT name, salary, LAG(salary, 0) OVER (ORDER BY id) AS lag0 FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | lag0            +------+--------+------+
------+--------+------           | name | salary | lag0 |
 ann  |    300 |  300            +------+--------+------+
 bob  |    500 |  500            | ann  |    300 |  300 |
 cho  |   NULL |  NULL           | bob  |    500 |  500 |
 dan  |    400 |  400            | cho  |   NULL | NULL |
 eve  |    300 |  300            | dan  |    400 |  400 |
 fay  |    500 |  500            | eve  |    300 |  300 |
 gus  |    400 |  400            | fay  |    500 |  500 |
 hui  |    400 |  400            | gus  |    400 |  400 |
(8 rows)                         | hui  |    400 |  400 |
                                 +------+--------+------+
```

```text
### SQL: SELECT name, salary, LAG(salary, -1) OVER (ORDER BY id) AS lag_neg FROM emp8 ORDER BY id;
--- PG 18.6 ---
 name | salary | lag_neg
------+--------+---------
 ann  |    300 |     500
 bob  |    500 |    NULL
 cho  |   NULL |     400
 dan  |    400 |     300
 eve  |    300 |     500
 fay  |    500 |     400
 gus  |    400 |     400
 hui  |    400 |    NULL
(8 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '-1) OVER (ORDER BY id) AS lag_neg FROM emp8 ORDER BY id' at line 7
```

**왜 그런가**

```text
LAG(식, 0)  : 0 칸 앞 = 자기 자신 -> salary 열과 같아진다 (cho 는 NULL 그대로)
LAG(식, -1) : "-1 칸 앞" = 1 칸 뒤 -> PG 에서는 LEAD 와 같은 값이 나온다
                                      (1번의 next 열과 대조해 보라 — 같다)
              MySQL 은 파서가 부호 없는 정수만 받는다 -> ERROR 1064
```

★ **[29번](../29-ranking-functions/) 4번의 `NTILE(-1)` 과 정확히 같은 자리다.**\
MySQL 의 파서는 이런 인자 자리에 **부호 없는 정수 리터럴만** 받고, PG 는 **식**으로 받아 계산한다.

★ **PG 쪽이 「관대하다」가 아니라 「조용히 다른 함수가 된다**」로 읽어야 한다.\
`LAG(salary, -1)` 을 의도해서 쓰는 사람은 없다 — 변수에 음수가 흘러 들어간 것이고, **MySQL 은 그것을 막았다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `LAG`/`LEAD` 기본형 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`NULL` 네 개의 뜻이 두 가지** |
| 오프셋·기본값 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `ann`=0 · `dan`=`NULL` |
| ★★ `LAST_VALUE` 함정 (3·4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진이 똑같이 「자기 피어의 마지막」** |
| `FIRST_VALUE`·`NTH_VALUE` (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `fv` 는 전부 300 |
| 프레임 끝만 열기 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `RANGE BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING` |
| 프레임 무시 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `lag_framed` = `lag_plain` |
| `NTH_VALUE` 의 `NULL` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 3번째 행이 `cho` 다 |
| ★ `IGNORE NULLS` (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 다 거부 — 걸리는 단계가 다르다** |
| ★ `FIRST_VALUE` 그룹 대표 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진이 다른 사람을 줬다** |
| ★ 기본값 타입 + 경고 (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`SHOW WARNINGS` 로 `Warning 1292` 확인** |
| 오프셋 0·음수 (12번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL `-1` 은 `ERROR 1064`** |

**구현 의존 항목** — 동률·`NULL` 에서 `FIRST_VALUE` 가 고르는 행(10번)과 **기본값 타입 검사**(11번), **음수 오프셋**(12번).\
**`LAST_VALUE` 함정은 구현 의존이 아니다** — 두 엔진이 똑같이 그렇게 하고, 문서가 그렇게 규정한다.

**방언 항목** — 10·11·12번. **`IGNORE NULLS`(9번)는 「양쪽 미지원」이라 방언이 아니다** — 걸리는 단계만 다르다.\
**언어 보장 항목** — 1~8번. 기본 오프셋·기본값, 경계 함수의 프레임 의존, `LAG`/`LEAD` 의 프레임 무시는\
두 문서가 같은 모양으로 적고 두 엔진의 출력도 같았다.

**버전** — 다섯 함수 모두 PG 8.4 · MySQL 8.0 부터다.\
다음 버전에서 다시 찍을 것은 **9번**이다 — MySQL 이 *"doesn't **yet** support"* 라고 답했다.

**재지 않은 것** — `LAG`/`LEAD` 와 경계 함수의 비용 차이. **측정하지 않았으므로 적지 않았다.**\
**던져 보지 않은 것** — 9번의 일반 우회(구간 번호 매기기)와 11번의 `CAST` + `COALESCE` 형태. 둘 다 **형태만 적었다.**
