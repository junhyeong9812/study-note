# sql/30-오프셋·경계 함수 — `LAG`·`LEAD`·`FIRST_VALUE`·`LAST_VALUE` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Window Functions](https://www.postgresql.org/docs/18/functions-window.html) · [MySQL 8.4 · Window Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·**경고**는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> MySQL 의 경고는 **`SHOW WARNINGS` 로 따로 물어서** 받았다(8번) — 안 물으면 안 보인다.\
> **버전** — 네 함수 모두 PG 8.4 · MySQL 8.0 부터. `NTH_VALUE` 도 같다.\
> **갈리는 자리는 인자 검사**다(2·8번) — `IGNORE NULLS` 는 **양쪽 다 거부**한다(6번).\
> **목록 README 의 30번 행은 `LAG`·`LEAD`·`FIRST_VALUE`·`NTH_VALUE` 로 적혀 있다.**\
> 이 문서는 **`LAST_VALUE` 를 포함해 다섯 함수**를 다룬다 — 이 갈래 최대 함정이 `LAST_VALUE` 에 있기 때문이다(3번).\
> (README 의 「무엇을 인출하게 되나」 칸도 `LAST_VALUE` 를 든다. 제목 칸만 `NTH_VALUE` 다.)\
> **선행** — [28 프레임 — ROWS·RANGE·GROUPS](../28-window-frames-rows-range-groups/). **이 주제의 함정 셋 중 둘이 프레임에서 나온다.**

## 한눈에 — 쉽게 말하면

**줄 서 있는 사람에게 「앞사람 이름」·「맨 앞사람 이름」을 물어보는 함수들이다.**

- **`LAG`** — 「내 **앞사람**은?」. 맨 앞 사람은 **답이 없다**(`NULL`).
- **`LEAD`** — 「내 **뒷사람**은?」. 맨 뒤 사람은 답이 없다.
- **`FIRST_VALUE`** — 「이 **줄의 맨 앞** 사람은?」
- **`LAST_VALUE`** — 「이 **줄의 맨 뒤** 사람은?」 ← ★ **여기가 함정이다. 대개 「나 자신」이 나온다.**

★ **함정의 정체 한 줄** — `LAST_VALUE` 는 **줄 전체가 아니라 「프레임」의 끝**을 본다.\
그런데 [기본 프레임](../28-window-frames-rows-range-groups/)은 「**시작 ~ 나까지**」라서, **프레임의 끝이 곧 나 자신**이다.

| 비유 | 실체 | `salary` 오름차순 7행에서 |
|---|---|---|
| 내 앞사람 | `LAG(salary)` | 맨 앞은 `NULL` |
| 내 뒷사람 | `LEAD(salary)` | 맨 뒤는 `NULL` |
| 줄의 맨 앞 | `FIRST_VALUE(salary)` | 전부 **300** — 기대대로 |
| 줄의 맨 뒤 | `LAST_VALUE(salary)` | **행마다 자기 값** — 기대와 다르다 ★ |
| 줄의 맨 뒤 (고친 것) | `LAST_VALUE(...) OVER (... ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)` | 전부 **500** |

```text
salary 오름차순:  300  300  400  400  400  500  500
                  ann  eve  dan  gus  hui  bob  fay

dan 의 기본 프레임 = [ann eve dan gus hui]      <- "시작 ~ 내 마지막 피어"
                     ^^^^              ^^^^
              FIRST_VALUE = 300   LAST_VALUE = 400  <- 500 이 아니다!
                                                       프레임 밖은 안 보인다
```

> **오프셋 함수(offset function)** — 현재 행에서 **몇 칸 떨어진 행**의 값을 가져오는 함수. `LAG`·`LEAD`.\
> 예: `LAG(salary)` 는 한 칸 앞 행의 `salary` 다. **프레임을 보지 않는다.**

> **경계 함수** — 프레임의 **처음·끝·n 번째** 값을 가져오는 함수. `FIRST_VALUE`·`LAST_VALUE`·`NTH_VALUE`.\
> 예: `LAST_VALUE(salary)` 는 **프레임**의 마지막 행의 `salary` 다. **창 전체가 아니다.**

## 이 주제가 답하려는 질문

1. **`LAG` 가 `NULL` 을 돌려주면 「앞 행이 없다」는 뜻인가?** — 아니다. **「앞 행의 값이 `NULL` 이다」일 수도 있다**(1번).
2. **`LAST_VALUE` 가 왜 「나 자신」을 돌려주나?** — 기본 프레임의 끝이 나이기 때문이다. **프레임을 고쳐야 한다**(3번).
3. **`NULL` 을 건너뛰고 앞 값을 가져오려면?** — `IGNORE NULLS` 인데 **두 엔진 모두 거부한다**(6번).

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
id 순서 (LAG·LEAD 가 쓰는 줄)
  1     2     3      4     5     6     7     8
 ann   bob   cho    dan   eve   fay   gus   hui
 300   500   NULL   400   300   500   400   400
              ^^^^
              한가운데에 NULL 이 있다 — 이게 1번의 함정을 만든다

salary 오름차순 (FIRST_VALUE·LAST_VALUE 가 쓰는 줄, cho 제외)
 300  300 | 400  400  400 | 500  500
 ann  eve | dan  gus  hui | bob  fay
 \_______/  \___________/  \_______/
  동률 2      동률 3         동률 2
```

**왜 이 데이터가 이 주제에 맞는가.**

- **`cho` 의 `salary` 가 `NULL` 이고 줄의 한가운데(3번째)에 있다.** 그래서 `LAG`/`LEAD` 가\
  **「경계라서 `NULL`」과 「앞 행의 값이 `NULL`」을 구분할 수 없다**는 것을 한 출력에서 보여 준다(1번).\
  `NULL` 이 맨 끝에 있었다면 이 함정이 안 보인다.
- **동률이 세 덩어리 있다.** `LAST_VALUE` 함정이 **동률 때문에 한 겹 더 깊어진다** —\
  프레임 끝이 「나」가 아니라 「**내 마지막 피어**」라서 `gus` 도 `hui` 도 400을 본다(3번).
- **`emp` 표의 `id` 가 기본키다.** `ORDER BY id` 로 줄을 세우면 동률이 없어 `LAG`/`LEAD` 가 결정적이다 —\
  **오프셋 함수를 볼 때는 순서를 고정**하고, 동률 효과는 프레임 절(3번)에서만 켠다.
- **`dept_id` 가 셋이다**(`10`·`20`·`NULL`) — 「부서별 최고 연봉자 이름」을 `FIRST_VALUE` 로 뽑는 관용구를 쓸 수 있고,\
  거기서 **두 엔진이 다른 사람을 준다**(7번).

## 동작 방식

---

### 1. ★ `LAG`·`LEAD` — 기본 오프셋은 1, 기본값은 `NULL`. 그런데 그 `NULL` 이 두 가지다

**언제 쓰나** — 「전월 대비」·「직전 상태와 비교」. 시계열 질의의 절반이 이것이다.

```text
ORDER BY id 로 줄을 세우면

 ann(300) bob(500) cho(NULL) dan(400) eve(300) fay(500) gus(400) hui(400)
    |        |        |         |
  앞이 없다  앞=300   앞=500    앞=cho 의 값 = NULL
    v                            v
  LAG = NULL                   LAG = NULL     <- 화면에서 둘이 똑같다
  "행이 없다"                   "값이 NULL 이다"
```

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

그림 해설 — ★ **`NULL` 이 네 군데 있는데 뜻이 세 가지다.**

| 행 | 값 | 뜻 |
|---|---|---|
| `ann` 의 `prev` | `NULL` | **앞 행이 없다**(창의 첫 행) |
| `hui` 의 `next` | `NULL` | **뒤 행이 없다**(창의 마지막 행) |
| `bob` 의 `next` · `dan` 의 `prev` | `NULL` | **그 행은 있는데 값이 `NULL`** 이다(`cho`) |
| `cho`·`ann`·`dan` 의 `diff` | `NULL` | 뺄셈에 `NULL` 이 껴서([04번](../04-null-three-valued-logic/)) |

★★ **「경계라서 `NULL`」과 「값이 `NULL`」을 화면에서 구분할 수 없다.**\
`bob` 을 마지막 행으로 오해하기 딱 좋다 — `bob` 뒤에는 다섯 행이 더 있다.\
구분하려면 `LEAD(id)` 처럼 **`NULL` 일 수 없는 열**을 같이 뽑거나, `COUNT(*) OVER ()` 로 자리를 확인해야 한다.

`diff` 가 `hui` 에서 **0**인 것도 읽을거리다 — `gus`(400)와 `hui`(400)가 같은 값이라 차이가 0이다.\
**`NULL` 과 0을 구분하라** — 앞은 「모른다」, 뒤는 「안 변했다」다.

비용 — 창을 한 번 훑는다. `LAG`/`LEAD` 는 **프레임을 보지 않으므로** 프레임 계산이 없다(5번).

---

### 2. 오프셋과 기본값 — `LAG(식, n, 기본값)`

**언제 쓰나** — 「2주 전과 비교」처럼 n 칸 떨어진 값이 필요할 때. 그리고 경계의 `NULL` 을 0으로 보이고 싶을 때.

```text
LAG( 식 , 오프셋 , 기본값 )
       |     |        |
       |     |        +-- 그 자리에 행이 없을 때 대신 줄 값. 안 적으면 NULL
       |     +----------- 몇 칸 앞인가. 안 적으면 1
       +----------------- 가져올 값
```

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

그림 해설 — **두 엔진이 한 자리도 안 갈렸다.**

★ **기본값은 「경계에서만」 쓰인다.** `lag_def` 의 `ann` 은 **0**(경계라서 기본값)이고 `dan` 은 **`NULL`**(값이 `NULL`)이다.\
**기본값을 줘도 「값이 `NULL`」인 경우는 안 메워진다** — 1번의 두 `NULL` 이 여기서 **행동으로** 갈린다.

★ **`eve` 의 `lag2` 가 `NULL`** 인 것에 주의하라. 두 칸 앞은 `cho` 이고 `cho` 의 급여가 `NULL` 이다 —\
「두 칸 앞이 없다」가 아니다. `ann`·`bob` 의 `NULL` 만 경계다.

비용 — 없다. 같은 훑기 안에서 계산된다.

---

### 3. ★★ `LAST_VALUE` 함정 — 기본 프레임 때문에 「나 자신」이 나온다

**언제 쓰나** — 「이 그룹의 최고값」·「기간의 마지막 값」을 가져올 때. **이 갈래에서 가장 많이 틀리는 자리다.**

```text
salary 오름차순:  ann300  eve300  dan400  gus400  hui400  bob500  fay500

dan 의 기본 프레임 = [ann eve dan gus hui]     "시작 ~ 내 마지막 피어" (28번)
                      ^^^                ^^^
             FIRST_VALUE = 300      LAST_VALUE = 400
                                    ^^^^^^^^^^^^^^^
                            500 이 아니다. 프레임 밖은 안 보인다
```

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

그림 해설 — ★★ **`lv_default` 열이 `salary` 열과 똑같다.** 「마지막 값」을 물었는데 **자기 값**이 나왔다.\
정확히는 「자기 값」이 아니라 「**자기 피어의 마지막 값**」이다 — 그래서 `gus`·`hui` 도 400 이다.

**두 엔진이 똑같이 그렇게 한다.** 이건 버그도 방언도 아니고 **프레임의 정의 그대로**다.\
PG 문서가 이 함정을 직접 적는다: *"Note that `first_value`, `last_value`, and `nth_value` consider only the rows within the "window frame" … This is likely to give unhelpful results for `last_value` and sometimes also `nth_value`."*

★ **`FIRST_VALUE` 는 왜 멀쩡한가.** 기본 프레임의 **시작**이 이미 `UNBOUNDED PRECEDING`(창의 처음)이기 때문이다.\
**문제는 끝**이다. 그래서 **`LAST_VALUE` 만 골라서 틀린다.**

**고치는 법 — 프레임을 창 전체로 열어 준다.**

```sql
LAST_VALUE(salary) OVER (ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
```

**끝만 열어도 된다** — 필요한 것은 끝이지 시작이 아니다.

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

★ **더 쉬운 길이 있다 — `ORDER BY` 를 뒤집고 `FIRST_VALUE` 를 쓴다.**\
`FIRST_VALUE(salary) OVER (ORDER BY salary DESC)` 는 프레임을 안 건드려도 500 을 준다.\
**「프레임을 기억해야 하는 코드」보다 「기억 안 해도 되는 코드」가 낫다.**

★ **더 쉬운 길이 또 있다 — 그냥 `MAX(salary) OVER ()`.** 「마지막 행의 값」이 아니라 「최댓값」이 진짜 요구라면 그쪽이 맞다.\
`LAST_VALUE` 는 「**정렬했을 때 끝에 오는 행의 *다른* 열**」이 필요할 때 쓰는 함수다(예: 최고 연봉자의 **이름**).

비용 — 프레임을 창 전체로 열면 창을 한 번 더 훑는다.

---

### 4. `FIRST_VALUE`·`NTH_VALUE` 도 같은 프레임을 본다

**언제 쓰나** — 「그룹의 첫 값」·「두 번째로 높은 값」.

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

그림 해설 — **`fv` 는 전부 300 으로 기대대로**다. 프레임 **시작**이 창의 처음이기 때문이다.\
`nv`(2번째)도 전부 300 인데, 프레임의 두 번째 행이 언제나 `eve`(300) 또는 `ann`(300)이기 때문이다.\
**`nv` 가 프레임에 의존한다는 사실은 `lv` 가 갈리는 것과 같은 이유**이고, PG 문서가 *"sometimes also `nth_value`"* 라고 적은 자리다.

★ **`NTH_VALUE` 가 `NULL` 을 돌려주는 두 경우가 있다.**

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

그림 해설 — **프레임은 8행이라 3번째 행이 분명히 있다.** 그 3번째 행이 `cho` 이고 **`cho` 의 급여가 `NULL`** 일 뿐이다.\
「3번째 행이 없다」가 아니라 「**3번째 행의 값이 `NULL`**」이다 — 1번의 두 `NULL` 과 **같은 종류의 혼동**이다.

비용 — `FIRST_VALUE` 는 프레임 시작만 보면 되고, `LAST_VALUE`·`NTH_VALUE` 는 프레임을 더 훑는다.

---

### 5. `LAG`·`LEAD` 는 프레임을 **무시한다** — 경계 함수와 갈리는 자리

**언제 쓰나** — 프레임을 적어 놓고 `LAG` 가 달라졌을 거라 믿을 때.

```text
### SQL: SELECT name, salary, LAG(salary) OVER (ORDER BY id ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS lag_framed,
                LAG(salary) OVER (ORDER BY id) AS lag_plain
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | lag_framed | lag_plain    +------+--------+------------+-----------+
------+--------+------------+-----------   | name | salary | lag_framed | lag_plain |
 ann  |    300 |       NULL |      NULL    +------+--------+------------+-----------+
 bob  |    500 |        300 |       300    | ann  |    300 |       NULL |      NULL |
 cho  |   NULL |        500 |       500    | bob  |    500 |        300 |       300 |
 dan  |    400 |       NULL |      NULL    | cho  |   NULL |        500 |       500 |
 eve  |    300 |        400 |       400    | dan  |    400 |       NULL |      NULL |
 fay  |    500 |        300 |       300    | eve  |    300 |        400 |       400 |
 gus  |    400 |        500 |       500    | fay  |    500 |        300 |       300 |
 hui  |    400 |        400 |       400    | gus  |    400 |        500 |       500 |
(8 rows)                                   | hui  |    400 |        400 |       400 |
                                           +------+--------+------------+-----------+
```

그림 해설 — **두 열이 같다.** PG 문서가 `lag`·`lead` 를 **프레임에 의존하지 않는 함수** 목록에 넣는다\
(`row_number`·`rank`·`dense_rank`·`percent_rank`·`cume_dist`·`ntile`·`lag`·`lead`).

★ **이 절의 값은 「비대칭을 외우는 것」이다.**

```text
프레임을 본다      : FIRST_VALUE · LAST_VALUE · NTH_VALUE · 집계(SUM·AVG·COUNT·MIN·MAX)
프레임을 안 본다   : LAG · LEAD · ROW_NUMBER · RANK · DENSE_RANK · NTILE
                     ^^^^^^^^^^
                     같은 "다른 행을 보는 함수" 인데 갈린다
```

「다른 행의 값을 가져온다」는 점은 `LAG` 와 `LAST_VALUE` 가 같다. 그런데 **한쪽만 프레임에 걸린다.**\
그래서 `LAST_VALUE` 만 골라서 틀리고, `LAG` 는 안 틀린다.

비용 — `LAG`/`LEAD` 가 더 싸다. 프레임 경계를 안 찾는다.

---

### 6. ★ `IGNORE NULLS` — **두 엔진 모두 거부한다. 거부하는 방식이 다르다**

**언제 쓰나** — 「마지막으로 값이 있었던 행의 값」을 가져올 때. 1번의 `cho` 함정을 푸는 표준 문법이다.

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

그림 해설 — ★ **거부는 같은데 「어디서」가 다르다.**

| | 무엇이라 하나 | 어디서 걸리나 | 무슨 뜻인가 |
|---|---|---|---|
| PG 18.6 | `syntax error at or near "NULLS"` | **파서** | 문법에 그 낱말 자리가 **아예 없다** |
| MySQL 8.4.10 | `doesn't yet support 'IGNORE NULLS'` | **실행** | 파서는 알아보고 **아직 구현이 없다** |

★ **MySQL 쪽 메시지의 `yet` 이 정보다.** [28번](../28-window-frames-rows-range-groups/)의 `GROUPS`·`EXCLUDE` 와 **같은 `ERROR 1235`** 이고,\
「파싱은 되는데 구현이 없는 것들」이 같은 번호로 묶여 있다는 뜻이다.

**우회 — 값이 있는 행끼리만 이웃으로 만든다.**

```sql
-- NULL 인 행을 아예 빼고 LAG 를 건다 (요구가 허락하면 가장 간단하다)
SELECT name, salary, LAG(salary) OVER (ORDER BY id) FROM emp8 WHERE salary IS NOT NULL;
```

더 일반적인 우회(마지막 비`NULL` 값을 끌고 내려오는 것)는 **「값이 바뀐 구간에 번호를 매겨 그 구간의 첫 값을 가져오는」** 관용구인데,\
**이 주제에서 던져 보지 않았다.** 형태만 적고 실행 근거를 붙이지 않는다.

비용 — 우회는 대개 창을 한 번 더 쓴다.

---

### 7. 「부서별 최고 연봉자 이름」 — 두 엔진이 **다른 사람**을 준다

**언제 쓰나** — `FIRST_VALUE` 로 그룹 대표를 뽑는 관용구. 실무에서 아주 흔하다.

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

그림 해설 — ★★ **`dept 10` 에서 PG 는 `fay`, MySQL 은 `bob` 이라고 답한다.**\
둘 다 급여 500 이고 **동률**이라, 누가 먼저 서는지가 엔진에 달렸다([29번](../29-ranking-functions/) 3번).

★★ **`dept 20` 에서 PG 는 `cho` 라고 답한다 — `cho` 는 급여가 `NULL` 인 사람이다.**\
`ORDER BY salary DESC` 에서 PG 는 `NULL` 을 맨 앞에 놓기 때문이다([08번](../08-order-by-null-position-stability/)).\
**「최고 연봉자」 칸에 급여 미기록자의 이름이 찍힌다.** 에러도 경고도 없다.

**고치는 법 — 갈릴 자리 둘을 둘 다 막는다.**

```sql
FIRST_VALUE(name) OVER (PARTITION BY dept_id ORDER BY (salary IS NULL), salary DESC, id)
--                                            ^^^^^^^^^^^^^^^^^^^^^^^  ^^^^
--                                            NULL 을 뒤로            동률을 깨는 고유 키
```

★ **이 한 줄에 [08번](../08-order-by-null-position-stability/)·[27번](../27-partition-by-and-window-order-by/)·[29번](../29-ranking-functions/)의 처방이 다 들어 있다.**\
「`FIRST_VALUE` 가 이상하다」가 아니라 「**`ORDER BY` 가 답을 끝까지 안 정했다**」가 매번 같은 진단이다.

비용 — 정렬 키 둘이 는다.

---

### 8. ★ 기본값의 타입 — PG 는 거부하고 MySQL 은 **경고로만** 말한다

**언제 쓰나** — `LAG`/`LEAD` 의 기본값을 문자열로 주려 할 때(`'없음'` 같은 표시값).

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

그림 해설 — ★ **MySQL 은 통과시킨다.** 숫자와 `'x'` 가 **한 열에 섞인** 결과가 나왔다(`hui` 행).\
PG 는 *"default … must be of a type compatible with value"* 라는 문서 규정대로 **거부**한다.

★★ **그 섞인 열로 계산을 하면 그때서야 경고가 나온다 — 그리고 `SHOW WARNINGS` 를 물어야 보인다.**

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

그림 해설 — ★ **`'x'` 가 조용히 `0` 이 됐다.** 화면에는 그럴듯한 숫자만 남고, **경고를 따로 묻지 않으면 아무 신호가 없다.**\
`hui` 는 마지막 행이라 「다음 행이 없다」가 요점이었는데, 결과는 「**다음 급여가 0**」처럼 읽힌다.

★ **이 실험은 한쪽에서만 결론이 선다 — 그렇게 밝힌다.**\
「기본값 타입이 맞아야 한다」는 **PG 쪽 출력이 근거**다(에러가 명시적이다).\
MySQL 쪽 출력은 「통과한다」는 사실의 근거일 뿐 **안전하다는 근거가 아니다** — 경고 `1292` 가 그것을 말한다.

비용 — 없다. 대가는 조용히 틀린 값이다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
LAG(식 [, 오프셋 [, 기본값]])   OVER (PARTITION BY ... ORDER BY ...)
LEAD(식 [, 오프셋 [, 기본값]])  OVER (...)
FIRST_VALUE(식)                 OVER (... [프레임])
LAST_VALUE(식)                  OVER (... [프레임])   -- 프레임을 반드시 의식한다
NTH_VALUE(식, n)                OVER (... [프레임])
```

규칙 일곱.

1. **`LAG`/`LEAD` 의 기본 오프셋은 1, 기본값은 `NULL`** 이다.
2. **기본값은 「행이 없을 때」만 쓰인다.** 「행은 있는데 값이 `NULL`」은 안 메워진다.
3. **`LAG`/`LEAD` 는 프레임을 무시**하고 **`FIRST_VALUE`/`LAST_VALUE`/`NTH_VALUE` 는 프레임을 본다.** 이 비대칭이 핵심이다.
4. ★ **`LAST_VALUE` 는 기본 프레임에서 「내 마지막 피어」를 준다.** 창 전체를 보려면 프레임을 열어야 한다.
5. **`FIRST_VALUE` 는 기본 프레임에서 멀쩡하다.** 시작이 이미 창의 처음이기 때문이다.
6. **`IGNORE NULLS` 는 두 엔진 모두 거부한다.** PG 는 파서, MySQL 은 실행 단계에서.
7. **기본값의 타입** — PG 는 맞지 않으면 에러, MySQL 은 통과시키고 **나중에 경고**만 낸다.

실전 형태는 넷이다.

```sql
-- (1) 직전 값과의 차이
salary - LAG(salary) OVER (ORDER BY id)

-- (2) 경계를 0으로 보이기 (값이 NULL 인 경우는 안 메워진다)
LAG(salary, 1, 0) OVER (ORDER BY id)

-- (3) 창 전체의 마지막 값 — 프레임을 반드시 연다
LAST_VALUE(salary) OVER (ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)

-- (4) 그룹 대표 — ORDER BY 를 끝까지 정한다
FIRST_VALUE(name) OVER (PARTITION BY dept_id ORDER BY (salary IS NULL), salary DESC, id)
```

## 어디서 틀리나

- **★ `LAST_VALUE` 를 「창의 마지막 값」으로 안다.**\
  기본 프레임에서는 **내 마지막 피어**다. 두 엔진이 똑같이 그렇게 한다. 프레임을 열거나 `FIRST_VALUE` + `DESC` 로 바꾼다.
- **★ `LAG` 의 `NULL` 을 「앞 행이 없다」로 읽는다.**\
  「앞 행의 값이 `NULL`」일 수도 있다. `bob` 의 `next` 가 `NULL` 이지만 `bob` 뒤에 다섯 행이 더 있다.
- **★ 기본값을 주면 모든 `NULL` 이 메워질 거라 믿는다.**\
  경계에서만 쓰인다. `dan` 의 `lag_def` 는 기본값 0이 아니라 `NULL` 이었다.
- **★ `FIRST_VALUE` 로 그룹 대표를 뽑으면서 `ORDER BY` 를 끝까지 안 정한다.**\
  동률과 `NULL` 때문에 **두 엔진이 다른 사람을 준다**(7번). `(열 IS NULL)` + 고유 키를 더한다.
- **`LAG` 에 프레임을 적고 뭔가 달라졌다고 믿는다.**\
  무시된다. 에러도 안 난다.
- **`IGNORE NULLS` 를 쓴다.**\
  PG 는 문법 오류, MySQL 은 `doesn't yet support` 다. 둘 다 안 된다.
- **기본값을 문자열로 준다.**\
  PG 는 에러, MySQL 은 **통과시킨다.** 그 열로 계산하면 `'x'` 가 조용히 0이 되고 경고는 따로 물어야 보인다.
- **「마지막 값」이 아니라 「최댓값」이 요구인데 `LAST_VALUE` 를 쓴다.**\
  `MAX(salary) OVER ()` 가 맞다. `LAST_VALUE` 는 **끝 행의 다른 열**이 필요할 때 쓴다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `LAG`/`LEAD` 의 기본 오프셋 1·기본값 `NULL` | **정의** | 언어 — PG 문서 *"offset defaults to 1 and default to `NULL`"* |
| `LAG`/`LEAD` 가 프레임을 무시 | **정의** | 언어 — PG 문서가 함수 목록으로 명시. 두 엔진 출력이 같았다 |
| `LAST_VALUE` 가 프레임을 본다 | **정의** | 언어 — PG 문서 *"This is likely to give unhelpful results for `last_value`"* |
| 프레임을 열면 창 전체의 마지막 값 | **정의** | 언어 — 두 엔진이 똑같이 500 을 줬다 |
| **`IGNORE NULLS`** | **양쪽 미지원** | PG 는 문법에 없고, MySQL 은 `doesn't yet support`(6번) |
| **기본값의 타입 검사** | **방언** | PG 는 거부, MySQL 은 통과 + 나중에 `Warning 1292`(8번) |
| **동률·`NULL` 에서 `FIRST_VALUE` 가 고르는 행** | **비결정 + 방언** | `ORDER BY` 가 안 정한 자리. 두 엔진이 다른 사람을 줬다(7번) |
| `NTH_VALUE` 가 `NULL` 을 주는 경우 | **정의** | 「행이 없다」와 「값이 `NULL`」 둘 다. 두 엔진 출력이 같았다(4번) |

- **이 주제에서 값이 갈린 자리는 7·8번 둘**이다. 7번은 `ORDER BY` 미결정, 8번은 타입 검사 차이다.
- **`LAST_VALUE` 함정은 방언이 아니다** — 두 엔진이 **똑같이** 그렇게 한다. 그래서 「엔진을 바꾸면 고쳐질」 성격이 아니다.

## 언제 쓰고 언제 안 쓰나

- **`LAG`/`LEAD` 를 쓴다 — 「직전/다음 행과 비교」가 요구 그대로일 때.** 증감·간격·상태 전이 탐지.
- **`FIRST_VALUE` 를 쓴다 — 「그룹 대표 행의 다른 열」이 필요할 때.** 최고 연봉자의 **이름**.
- **`LAST_VALUE` 를 쓴다 — 쓸 거면 프레임을 반드시 명시한다.** 아니면 `FIRST_VALUE` + `DESC` 로 바꾼다.
- **안 쓴다 — 최댓값·최솟값이 요구일 때.** `MAX`/`MIN` + `OVER` 가 맞다. 프레임을 기억할 필요가 없다.
- **안 쓴다 — 오프셋이 「몇 칸」이 아니라 「얼마 전」일 때.** 날짜가 듬성듬성하면 `LAG(1)` 은 「어제」가 아니다.\
  그때는 값 범위 프레임(`RANGE`)이나 달력 표와의 조인이 맞다([28번](../28-window-frames-rows-range-groups/) 6번).
- **안 쓴다 — `NULL` 을 건너뛴 「마지막 값」이 필요할 때.** `IGNORE NULLS` 가 없으니 우회를 설계해야 한다.

## 핵심 문장

- ★★ **`LAST_VALUE` 는 기본 프레임 때문에 「내 마지막 피어」를 준다** — `lv_default` 열이 `salary` 열과 똑같았다.\
  **두 엔진이 똑같이 그렇게 한다** — 방언이 아니라 프레임의 정의다.
- **고치는 법 셋** — 프레임을 열거나(`ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`),\
  `FIRST_VALUE` + `ORDER BY ... DESC` 로 뒤집거나, 요구가 최댓값이면 `MAX(...) OVER ()` 를 쓴다.
- **`FIRST_VALUE` 는 멀쩡하다** — 기본 프레임의 **시작**이 이미 창의 처음이기 때문이다. **문제는 끝이다.**
- ★ **`LAG` 의 `NULL` 은 두 가지 뜻**이다 — 「앞 행이 없다」와 「앞 행의 값이 `NULL`」. 화면에서 구분이 안 된다.
- **기본값은 경계에서만 쓰인다.** `LAG(salary, 1, 0)` 이 `dan` 에서 0이 아니라 `NULL` 이었다.
- ★ **`LAG`·`LEAD` 는 프레임을 무시하고 `FIRST_VALUE`·`LAST_VALUE`·`NTH_VALUE` 는 프레임을 본다.** 이 비대칭이 함정의 뿌리다.
- **`IGNORE NULLS` 는 양쪽 다 안 된다** — PG 는 `syntax error`, MySQL 은 `doesn't yet support`.
- ★ **`FIRST_VALUE` 로 「부서별 최고 연봉자」를 뽑으면 두 엔진이 다른 사람을 준다** — 동률과 `NULL` 위치 때문이다.
- ★ **`LEAD(salary,1,'x')` 는 PG 에서 에러이고 MySQL 에서는 통과한다.** 그 열로 계산하면 `'x'` 가 조용히 0이 되고,\
  경고 `1292` 는 **`SHOW WARNINGS` 를 물어야** 보인다.

## 관련 자료

- [PostgreSQL 18 · Window Functions](https://www.postgresql.org/docs/18/functions-window.html) — *"This is likely to give unhelpful results for `last_value`"* 와 프레임 무시 함수 목록이 여기 있다.
- [MySQL 8.4 · Window Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html) — `LAG`·`LEAD`·`NTH_VALUE` 설명.
- [28 프레임 — ROWS·RANGE·GROUPS](../28-window-frames-rows-range-groups/) — **경계: 그쪽은 프레임이 무엇이고 기본값이 무엇인지까지, 여기는 그 기본값 때문에 `LAST_VALUE` 가 이상해지는 것부터.**
- [29 순위 함수](../29-ranking-functions/) — **경계: 그쪽은 동률을 번호로 세는 것까지, 여기는 동률 때문에 `FIRST_VALUE` 가 다른 사람을 고르는 것부터.**
- [08 ORDER BY — 정렬 키·NULL 위치·동률](../08-order-by-null-position-stability/) — 7번의 두 처방(`(열 IS NULL)` 키·고유 키)이 나온 자리.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `diff` 가 `NULL` 이 되는 이유.
- [21 집계 함수와 `COUNT` 의 세 형태](../21-aggregate-functions-count-forms/) — 「`NULL` 과 0을 구분하라」가 같은 뿌리인 자리.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — **경계: 8번의 암시 변환 규칙 일반은 거기, 여기는 `LAG`/`LEAD` 기본값 자리에서 그것이 드러나는 것.**
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **오프셋 함수(offset function)** — 현재 행에서 몇 칸 떨어진 행의 값을 가져오는 함수.\
  예: `LAG(salary)` 는 한 칸 앞 행의 급여. 프레임을 보지 않는다.
- **경계 함수** — 프레임의 처음·끝·n 번째 값을 가져오는 함수.\
  예: `LAST_VALUE(salary)` 는 **프레임**의 마지막 행의 급여. 창 전체가 아니다.
- **`LAG(식, 오프셋, 기본값)`** — 오프셋만큼 앞 행의 값. 그 자리에 행이 없으면 기본값.\
  예: `LAG(salary, 1, 0)` 은 첫 행에서 0을 준다. 값이 `NULL` 인 경우는 안 메워진다.
- **`LEAD`** — `LAG` 의 반대 방향.\
  예: `LEAD(salary)` 는 한 칸 뒤 행의 급여. 마지막 행에서 `NULL` 이다.
- **`FIRST_VALUE`** — 프레임의 첫 행의 값. 기본 프레임에서도 창의 처음이라 기대대로 동작한다.\
  예: `salary` 오름차순에서 전부 300.
- **`LAST_VALUE`** — 프레임의 마지막 행의 값. **기본 프레임에서는 「내 마지막 피어**」다.\
  예: `dan`(400)에서 500이 아니라 400이 나온다.
- **`NTH_VALUE(식, n)`** — 프레임의 n 번째 행의 값.\
  예: 3번째 행이 `cho` 면 `cho` 의 급여 `NULL` 을 그대로 돌려준다 — 「행이 없다」가 아니다.
- **`IGNORE NULLS`** — `NULL` 인 행을 건너뛰고 값을 찾으라는 지시. **두 엔진 모두 거부한다.**\
  예: `LAG(salary) IGNORE NULLS`. PG 는 `syntax error`, MySQL 은 `ERROR 1235` 다.
- **경계의 `NULL`** — 가져올 행 자체가 없어서 나온 `NULL`.\
  예: 첫 행의 `LAG`. **값이 `NULL` 인 경우와 화면에서 구분되지 않는다.**
- **경고(warning)** — 에러가 아니라 「이상하지만 진행했다」는 신호. **MySQL 은 `SHOW WARNINGS` 로 물어야 보인다.**\
  예: `Warning 1292 Truncated incorrect DOUBLE value: 'x'`.

## 더 들어가면

- **`LAG`/`LEAD` 의 오프셋에 0과 음수를 넣으면** 두 엔진이 갈린다. 던져 봤다.

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

  **오프셋 0은 양쪽에서 「자기 자신**」이다. **음수는 PG 에서 `LEAD` 가 되고 MySQL 에서는 문법 오류**다 —\
  [29번](../29-ranking-functions/) 4번의 `NTILE(-1)` 과 **같은 자리**다. MySQL 의 파서는 이 자리에 부호 없는 정수만 받는다.
- **`LAST_VALUE` 함정이 왜 이렇게 유명한가.** 「마지막」이라는 낱말이 **창의 마지막**을 뜻할 거라고 읽히는데,\
  실제 계약은 **프레임의 마지막**이기 때문이다. **이름이 계약보다 넓게 읽히는** 전형적인 자리다.\
  `FIRST_VALUE` 는 이름과 계약이 우연히 겹쳐서 안 틀린다 — **운이 좋은 것이지 더 잘 설계된 것이 아니다.**
- **`LAG` 로 「구간 나누기」를 한다** — 이전 행과 값이 달라진 자리에 1을 세우고 그것을 누적합하면 구간 번호가 된다.\
  `IGNORE NULLS` 우회(6번)도 이 관용구를 쓴다. **이 주제에서 던져 보지 않았다** — 형태만 적는다.
