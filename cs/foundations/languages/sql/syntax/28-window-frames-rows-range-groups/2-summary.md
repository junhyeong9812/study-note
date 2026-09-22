# sql/28-프레임 — `ROWS`·`RANGE`·`GROUPS` 와 기본 프레임 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) · [MySQL 8.4 · Window Function Frame Specification](https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `ROWS`·`RANGE` 는 PG 8.4 · MySQL 8.0 부터. **`GROUPS` 와 `EXCLUDE` 는 PG 11 부터이고 MySQL 8.4 에는 없다**(4·5번에서 에러로 확인했다).\
> **이 주제는 방언 차이가 큰 자리다** — 목록 README 의 표기(`ROWS`/`RANGE`/`GROUPS`+`EXCLUDE` 대 `ROWS`/`RANGE`)가 **맞았다.**\
> **선행** — [27 PARTITION BY 와 윈도우 ORDER BY](../27-partition-by-and-window-order-by/). **뒤 주제** — [30 오프셋·경계 함수](../30-offset-and-boundary-functions/).

## 한눈에 — 쉽게 말하면

**줄 서 있는 사람들 사이에서, 내가 「몇 명까지 뒤돌아볼 것인가」를 정하는 규칙이다.**

- 기본값은 「**내 앞 전부 + 나랑 똑같은 사람들까지**」다.\
  키 순으로 줄을 섰는데 내 앞에 **나와 키가 같은 사람**이 있으면, 그 사람도 **내 뒤에 선 동명이인**도 함께 센다.
- 「**사람 수**로 세겠다 — 앞에서 두 명」이 `ROWS` 다.
- 「**값**으로 세겠다 — 나와 같은 값은 전부 한 덩어리」가 `RANGE` 다(기본값).
- 「**덩어리 수**로 세겠다 — 앞 덩어리 하나까지」가 `GROUPS` 다. **PG 에만 있다.**

★ **동률이 없으면 셋이 전부 같은 답을 낸다.** 갈리는 것은 **동률이 있을 때뿐**이고, 그래서 이 주제의 예시 데이터에 동률을 세 덩어리 심었다.

| 비유 | 실체 | `emp8` 에서 `ann`(300)의 프레임 |
|---|---|---|
| 나와 값이 같은 사람까지 통째로 | `RANGE`(기본) | `[ann, eve]` — 합 **600** |
| 앞에서부터 **행 수**로 | `ROWS` | `[ann]` 하나 — 합 **300** |
| 앞 **덩어리** 단위로 | `GROUPS`(PG 전용) | `[ann, eve]` — 합 **600** |

```text
ORDER BY salary 로 줄을 세우면 (salary NULL 인 cho 는 뺐다)

  300   300   400   400   400   500   500
  ann   eve   dan   gus   hui   bob   fay
  \_____/     \_________________/     \_____/
   덩어리1          덩어리2            덩어리3
   (peer)          (peer)             (peer)

RANGE  : 덩어리 경계에서 끊는다   -> 같은 덩어리는 전부 같은 값
ROWS   : 행 하나하나로 끊는다     -> 덩어리 안에서도 값이 달라진다
GROUPS : 덩어리를 단위로 센다     -> "앞 덩어리 하나까지" 같은 말이 가능해진다
```

> **프레임(frame)** — 창 안에서 **실제로 계산에 쓰이는 범위**. 파티션이 「누구와 비교하나」면 프레임은 「그중 어디까지」다.\
> 예: `ann` 의 창은 7행이지만 기본 프레임은 `[ann, eve]` 두 행이라 합이 600이다.

> **피어(peer)** — 윈도우 `ORDER BY` 가 **같다고 판정한** 행들. `RANGE` 는 피어를 쪼개지 않는다.\
> 예: `ORDER BY salary` 에서 `dan`·`gus`·`hui`(전부 400)는 서로 피어다.

## 이 주제가 답하려는 질문

1. **`ORDER BY` 를 적었을 뿐인데 왜 값이 바뀌나?** — 순서가 **기본 프레임**을 켜기 때문이다.
2. **누적합이 동률 행에서 왜 「튀나」?** — 기본 프레임이 `RANGE` 라 피어를 통째로 넣기 때문이다.
3. **`ROWS` 로 바꾸면 항상 더 나은가?** — 아니다. **동률이 있으면 `ROWS` 의 답은 비결정적**이다(3번).

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
emp8 을 salary 로 줄 세운 모습 (이 주제의 주인공)

  salary:  300   300   400   400   400   500   500  | NULL
  name  :  ann   eve   dan   gus   hui   bob   fay  | cho
           \_____/     \_________________/   \_____/  \___/
            2행            3행                2행      1행
```

**왜 이 데이터가 프레임 주제에 맞는가.**

- **동률이 세 덩어리, 크기가 2·3·2 로 다르다.** 크기가 다 같으면 「덩어리 단위」와 「행 단위」의 차이가 안 보인다.\
  **동률이 하나도 없으면 `ROWS`·`RANGE`·`GROUPS` 가 전부 같은 답**을 내서 이 주제가 성립하지 않는다.
- **덩어리 하나가 3행이다**(`400`) — `ROWS` 로 세면 그 안에서 값이 세 단계로 갈라지는 것이 보인다.
- **`cho` 의 `salary` 가 `NULL` 이다** — 프레임 본문에서는 `WHERE salary IS NOT NULL` 로 **일부러 뺐다.**\
  `NULL` 이 섞이면 두 엔진의 `NULL` 위치 차이([27번](../27-partition-by-and-window-order-by/) 6번)가 프레임 차이 위에 겹쳐 **무엇 때문에 갈렸는지 알 수 없게 된다.**\
  여기서는 프레임 하나만 보려고 뺐고, `NULL` 이 섞인 판은 [27번](../27-partition-by-and-window-order-by/)에 있다.
- 그래서 본문 대부분의 창은 **7행**이다(`emp8` 8행 - `cho` 1행).

## 동작 방식

---

### 1. ★ 기본 프레임 — `ORDER BY` 가 있으면 `RANGE UNBOUNDED PRECEDING AND CURRENT ROW`

**언제 쓰나** — 윈도우 `ORDER BY` 를 적을 때마다. **적는 순간 이 프레임이 자동으로 켜진다.**

```text
아무것도 안 적었을 때 엔진이 채워 넣는 것

OVER (ORDER BY salary)
  == OVER (ORDER BY salary RANGE UNBOUNDED PRECEDING)
  == OVER (ORDER BY salary RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                           ^^^^^                          ^^^^^^^^^^^
                           단위가 RANGE 다                RANGE 의 CURRENT ROW 는
                                                          "내 마지막 피어" 를 뜻한다
```

**증명은 셋을 나란히 뽑는 것이다** — 안 적은 것과 적은 것이 같은 답을 내면 기본값이 그것이다.

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

그림 해설 — ★ **`implicit` 열과 `explicit_range` 열이 두 엔진에서 한 자리도 안 다르다.**\
「안 적으면 `RANGE ... CURRENT ROW` 가 켜진다」가 이 두 열의 일치로 확인된다.

두 문서가 같은 말을 적는다.\
PG: *"The default framing option is `RANGE UNBOUNDED PRECEDING`, which is the same as `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`."*\
MySQL: *"With `ORDER BY`: The default frame includes rows from the partition start through the current row, including all peers of the current row."*

`explicit_rows` 열은 3번의 주인공이다 — **지금은 「셋째 열만 다르다」는 것까지만** 보면 된다.

비용 — `RANGE` 는 피어 경계를 찾아야 해서 정렬 결과를 한 번 더 훑는다. `ROWS` 는 그 훑기가 없다.

---

### 2. `ORDER BY` 가 없으면 프레임은 **창 전체**다

**언제 쓰나** — 「칸 전체 합계」를 행마다 붙일 때. `OVER ()` 와 `OVER (PARTITION BY ...)` 가 여기 해당한다.

```text
ORDER BY 가 없다 -> 비교할 키가 없다 -> 모든 행이 서로의 피어
                 -> "내 마지막 피어" = 칸의 마지막 행
                 -> 프레임 = 칸 전체

그래서 OVER () 는 사실상
  OVER (RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) 과 같다
```

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

그림 해설 — **두 열이 같다.** MySQL 문서가 이 경우를 따로 적는다:\
*"Without `ORDER BY`: The default frame includes all partition rows … equivalent to … `RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`."*

★ **여기서도 규칙은 하나뿐이다.** 「`ORDER BY` 없으면 전체」가 특례가 아니라,\
**「내 마지막 피어까지」라는 같은 규칙이 「모두가 피어」인 상황에 적용된 결과**다([27번](../27-partition-by-and-window-order-by/) 4번).

비용 — 칸을 한 번 훑어 값을 만들고 모든 행에 복사한다.

---

### 3. ★ `ROWS` 대 `RANGE` — 동률에서 갈리고, `ROWS` 의 답은 **비결정적**이다

**언제 쓰나** — 누적합을 쓸 때마다. 그리고 그 누적합이 동률 행에서 「튄다」는 말을 들을 때마다.

```text
ORDER BY salary 로 세운 7행

  ann300 eve300 | dan400 gus400 hui400 | bob500 fay500
  \____덩어리1___/ \______덩어리2_______/ \___덩어리3___/

RANGE (기본)                       ROWS
덩어리 단위로 끊는다                 행 단위로 끊는다
ann -> 600   (300+300)             ann -> 300
eve -> 600   (같다)                 eve -> 600
dan -> 1800  (600+1200)            dan -> 1000
gus -> 1800  (같다)                 gus -> 1400
hui -> 1800  (같다)                 hui -> 1800
bob -> 2800                        bob -> 2300
fay -> 2800  (같다)                 fay -> 2800
      ^^^^^^                             ^^^^^^^^
      피어끼리 값이 같다                  피어끼리 값이 다르다
```

1번 출력의 `explicit_rows` 열을 **두 엔진에서 나란히 놓고** 보라.

```text
             PG 18.6      MySQL 8.4.10
 ann  300  |    600     |     300      <- 다르다
 eve  300  |    300     |     600      <- 다르다
 dan  400  |   1000     |    1000
 gus  400  |   1800     |    1400      <- 다르다
 hui  400  |   1400     |    1800      <- 다르다
 bob  500  |   2800     |    2300      <- 다르다
 fay  500  |   2300     |    2800      <- 다르다
           |  RANGE 열은 두 엔진이 600/600/1800/1800/1800/2800/2800 로 똑같았다
```

그림 해설 — ★★ **`RANGE` 는 두 엔진이 같고 `ROWS` 는 갈렸다.** 이유는 하나다.

```text
ROWS 는 "몇 번째 행인가" 를 센다
  -> 동률 안에서 누가 먼저인지 알아야 한다
  -> 그런데 ORDER BY salary 는 그 순서를 정하지 않는다  (08번의 동률 불안정)
  -> 엔진이 알아서 정한다 -> 엔진마다 다르다

RANGE 는 "어떤 값인가" 를 센다
  -> 동률 안의 순서를 알 필요가 없다
  -> 그래서 답이 하나로 정해진다
```

★ **`ROWS` 가 「더 정확한 누적합」이라는 인상은 틀렸다.** 동률이 있으면 **`ROWS` 의 답은 질의문이 정하지 않는다.**\
`RANGE` 는 「튀는」 것이 아니라 **질의문이 시킨 대로 정직하게** 답한 것이다 — 시킨 순서로는 그 둘을 구별할 수 없으니까.

**고치는 법** — 원하는 것이 「한 행씩 늘어나는 누적」이면 **동률을 없애야 한다.**

```sql
-- ORDER BY 에 고유 키를 더한다 -> 동률이 사라지고 ROWS 와 RANGE 가 같아진다
SUM(salary) OVER (ORDER BY salary, id ROWS UNBOUNDED PRECEDING)
```

행 수로 보면 더 선명하다.

```text
### SQL: SELECT name, salary,
                COUNT(*) OVER (ORDER BY salary) AS cnt_range,
                COUNT(*) OVER (ORDER BY salary ROWS UNBOUNDED PRECEDING) AS cnt_rows,
                COUNT(*) OVER (ORDER BY salary GROUPS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cnt_groups
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary | cnt_range | cnt_rows | cnt_groups
------+--------+-----------+----------+------------
 ann  |    300 |         2 |        2 |          2
 eve  |    300 |         2 |        1 |          2
 dan  |    400 |         5 |        3 |          5
 gus  |    400 |         5 |        5 |          5
 hui  |    400 |         5 |        4 |          5
 bob  |    500 |         7 |        7 |          7
 fay  |    500 |         7 |        6 |          7
(7 rows)
--- MySQL 8.4.10 ---
ERROR 1235 (42000) at line 1: This version of MySQL doesn't yet support 'GROUPS'
```

★ **이 질의는 `GROUPS` 때문에 MySQL 에서 통째로 거부됐다 — 그래서 `cnt_range`·`cnt_rows` 는 PG 쪽에서만 읽을 수 있다.**\
「`RANGE` 와 `GROUPS` 가 같고 `ROWS` 만 다르다」는 **PG 한쪽에서만 선 결론**이고,\
`ROWS` 와 `RANGE` 가 **두 엔진에서 다 갈린다**는 결론은 위의 `explicit_rows` 비교(양쪽 출력이 다 있다)가 근거다.

`cnt_rows` 열이 **프레임 크기 = 내부 순서에서의 내 자리**임을 보여 준다 — `eve` 가 1이면 `eve` 가 첫 행이라는 뜻이다.

비용 — `ROWS` 가 가장 싸다. 피어 경계를 안 찾아도 되기 때문이다. 대신 답이 흔들린다.

---

### 4. ★ `GROUPS` — 덩어리를 단위로 센다. **PG 11+ 전용이다**

**언제 쓰나** — 「앞 등수 하나까지」처럼 **행 수도 값 범위도 아닌 「덩어리 수**」로 범위를 잡고 싶을 때.

```text
GROUPS BETWEEN 1 PRECEDING AND CURRENT ROW

  덩어리1 [ann eve]   덩어리2 [dan gus hui]   덩어리3 [bob fay]

  ann·eve 의 프레임 = 덩어리1            -> 600
  dan·gus·hui 의 프레임 = 덩어리1+2      -> 600 + 1200 = 1800
  bob·fay 의 프레임 = 덩어리2+3          -> 1200 + 1000 = 2200
                     ^^^^^^^^^^
                     덩어리1 이 빠진다 — "앞 한 덩어리" 이므로
```

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

그림 해설 — ★ **MySQL 은 「아직 지원하지 않는다」고 말한다.** 「문법이 없다」(`ERROR 1064`)가 아니라\
**파서는 낱말을 알아보고 실행 단계에서 거부**한다. `doesn't yet support` 의 **`yet`** 이 앞으로 바뀔 여지를 말하고 있다.

★ **`GROUPS` 로만 되는 일이 있다** — 「나와 앞 등수까지」는 `ROWS` 로도 `RANGE` 로도 못 적는다.\
`ROWS 2 PRECEDING` 은 덩어리 크기가 3이면 모자라고, `RANGE 100 PRECEDING` 은 값 간격에 기대야 한다.

비용 — 피어 경계를 알아야 하므로 `RANGE` 와 같은 급이다.

---

### 5. `EXCLUDE` — 「나 자신을 빼고」. 이것도 PG 전용이다

**언제 쓰나** — 「나를 뺀 나머지의 평균」처럼 **자기 자신이 계산에 끼면 안 되는** 지표를 만들 때.

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

그림 해설 — `ann` 의 `600` 이 `300` 이 됐다 — **자기 급여 300 이 빠졌다.**\
`dan`·`gus`·`hui` 는 `1800` 이 `1400` 이다 — 각자 자기 400 만 빠졌고 **다른 피어는 남아 있다**(`EXCLUDE CURRENT ROW` 이므로).\
피어를 통째로 빼려면 `EXCLUDE GROUP`, **피어만 빼고 자기는 남기려면** `EXCLUDE TIES` 다. 셋 다 던져 봤다.

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

★ **`ann` 의 `ex_group` 이 `NULL` 이다** — 자기 덩어리를 통째로 빼면 **프레임이 비고**, 빈 입력의 `SUM` 은 `NULL` 이다([21번](../21-aggregate-functions-count-forms/) 3번).\
`ex_ties` 는 300 이다 — **피어(`eve`)만 빠지고 자기(300)는 남았다.** 셋의 차이가 이 한 행에 다 보인다.

★ MySQL 의 거부 메시지가 4번과 **같은 `ERROR 1235`** 다. 두 기능이 같은 방식으로 빠져 있다는 뜻이다.

비용 — 프레임을 만든 뒤 한 번 더 걸러 낸다.

---

### 6. `RANGE` 에 **오프셋**을 쓰면 — `ORDER BY` 키가 하나여야 하고 타입도 가려 받는다

**언제 쓰나** — 「내 급여 ±100 안에 있는 사람들」처럼 **값의 범위**로 프레임을 잡을 때.

```text
RANGE BETWEEN 100 PRECEDING AND 100 FOLLOWING
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              "행 수"가 아니라 "salary 값이 내 값 ±100 안" 이라는 뜻

ann(300) 의 프레임 = salary 가 200~400 인 행 = [ann eve dan gus hui] -> 1800
bob(500) 의 프레임 = salary 가 400~600 인 행 = [dan gus hui bob fay] -> 2200
```

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

**두 엔진이 똑같다.** 그런데 **키가 둘이면 둘 다 거부한다.**

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

**문자열 키를 주면 갈라진다.**

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

그림 해설 — ★ **거부하는 이유는 같고 부르는 이름이 다르다.**\
`300 - 1` 은 뜻이 있지만 `'ann' - 1` 은 뜻이 없다 — **값에서 오프셋을 빼야 하므로 뺄 수 있는 타입이어야 한다.**\
PG 는 **두 사유를 두 메시지로** 나누고(키 개수 / 타입), MySQL 은 **한 메시지에 둘 다** 적는다(`ERROR 3587`).

★ **`ROWS` 에는 이 제약이 없다.** 행 수를 세는 데는 키 개수도 타입도 상관없기 때문이다.

비용 — 값 범위를 찾으려면 정렬된 창을 양쪽으로 훑어야 한다.

---

### 7. 실무에서 가장 많이 쓰는 프레임 — 이동 평균

**언제 쓰나** — 「최근 3개의 평균」처럼 **앞뒤로 몇 칸**을 보는 지표를 만들 때.

```text
ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING   (id 순)

 ann  [     ann bob ]  -> (300+500)/2         = 400
 bob  [ ann bob cho ]  -> (300+500)/2         = 400    cho 의 NULL 은 안 더하고 분모에도 안 넣는다
 cho  [ bob cho dan ]  -> (500+400)/2         = 450
 dan  [ cho dan eve ]  -> (400+300)/2         = 350
```

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

그림 해설 — ★ **`cho` 의 `NULL` 때문에 분모가 조용히 줄어든다.** `bob` 행의 프레임은 3행인데 평균의 분모는 2다.\
[21번](../21-aggregate-functions-count-forms/)의 「**`AVG` 의 분모는 `COUNT(열)` 이다**」가 프레임 안에서도 그대로다.\
`gus` 의 `433.33` 은 `(500+400+400)/3` 이다 — 그 행은 `NULL` 이 안 껴서 분모가 3이다.

**끝에서는 프레임이 짧아진다** — `ann` 은 앞이 없어 2행, `hui` 는 뒤가 없어 2행이다. 에러가 아니다.\
「처음 두 행의 이동평균은 신뢰할 수 없다」는 판단은 **질의가 아니라 사람이** 해야 한다.

값은 두 엔진에서 같고 **소수 자릿수만 다르다.**

비용 — 창을 한 번 훑으면서 슬라이딩으로 계산된다. 프레임 폭에 비례하지 않는다.

---

### 8. `ORDER BY` 없이 `ROWS` 를 쓰면 — **돌지만 뜻이 없다**

**언제 쓰나** — 안 쓰는 것이 답이다. 이 절은 **무엇이 안 막히는지**를 보여 주려고 있다.

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

그림 해설 — ★ **에러가 안 난다. 그리고 두 엔진의 값이 한 자리도 안 갈렸다.**\
그런데 **이 일치는 보장이 아니다.** `ORDER BY` 가 없으면 「내 앞 행」이 무엇인지 질의문이 정하지 않았고,\
엔진은 **아무 순서나** 쓸 수 있다. 지금 같은 답이 나온 것은 두 엔진이 **우연히 같은 순서로 읽었기 때문**이다.

★ **「안 터졌다」와 「두 엔진이 같았다」는 둘 다 보장이 아니다.** 계획이 바뀌면 답이 바뀐다 —\
같은 종류의 함정을 [08번](../08-order-by-null-position-stability/) 6번이 `ORDER BY` 없는 `SELECT` 로 다뤘다.

**규칙 한 줄: `ROWS`·`RANGE`·`GROUPS` 를 적을 거면 `ORDER BY` 를 반드시 같이 적는다.**

비용 — 정렬이 없어 싸다. 그 대가가 답이 정해지지 않는 것이다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
OVER (
  [PARTITION BY ...]
  [ORDER BY ...]
  { ROWS | RANGE | GROUPS } 프레임범위 [EXCLUDE ...]
)

프레임범위:
  UNBOUNDED PRECEDING                              -- 시작부터 나까지 (짧은 형태)
  BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW      -- 같은 뜻
  BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING  -- 창 전체
  BETWEEN n PRECEDING AND n FOLLOWING              -- 앞뒤 n
  BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING      -- 나부터 끝까지
```

규칙 일곱.

1. **`ORDER BY` 가 있으면 기본 프레임은 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`** 다.
2. **`ORDER BY` 가 없으면 프레임은 창 전체**다. 규칙이 하나이고 갈래가 없다.
3. **`RANGE` 의 `CURRENT ROW` 는 「내 마지막 피어**」다. 행 하나가 아니다.
4. **동률이 없으면 `ROWS`·`RANGE`·`GROUPS` 가 같은 답**을 낸다. 갈리는 것은 동률이 있을 때뿐이다.
5. **동률이 있으면 `ROWS` 의 답은 질의문이 정하지 않는다.** 엔진이 정한다 — 두 엔진이 실제로 갈렸다.
6. **`RANGE` 에 오프셋을 쓰면 `ORDER BY` 키가 정확히 하나여야 하고 뺄 수 있는 타입이어야 한다.** `ROWS` 에는 그 제약이 없다.
7. **`GROUPS` 와 `EXCLUDE` 는 PG 11+ 전용**이다. MySQL 8.4 는 `ERROR 1235` 로 거부한다.

실전 형태는 넷이다.

```sql
-- (1) 한 행씩 늘어나는 진짜 누적합 (동률이 있어도 안전하게)
SUM(salary) OVER (ORDER BY salary, id ROWS UNBOUNDED PRECEDING)

-- (2) 피어를 묶는 누적합 (등수별 누계)
SUM(salary) OVER (ORDER BY salary)                      -- 기본 프레임 = RANGE

-- (3) 이동 평균
AVG(salary) OVER (ORDER BY id ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)

-- (4) 창 전체 (LAST_VALUE 를 제대로 쓰려면 필수 — 30번)
LAST_VALUE(salary) OVER (ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
```

## 어디서 틀리나

- **★ 기본 프레임이 `ROWS` 라고 믿는다.**\
  `RANGE` 다. 그래서 동률 행이 같은 값을 갖는다. 「누적합이 튄다」는 말의 정체가 이것이다.
- **★ `ROWS` 로 바꾸면 정확해진다고 믿는다.**\
  동률이 있으면 **답이 엔진마다 다르다.** PG 와 MySQL 이 실제로 갈렸다(3번). 고유 키를 `ORDER BY` 에 더해야 한다.
- **★ `ORDER BY` 를 「정렬하려고」 적는다.**\
  적는 순간 프레임이 켜져 `SUM` 이 전체합에서 누적합으로 **값이 바뀐다**([27번](../27-partition-by-and-window-order-by/) 3번).
- **`GROUPS` 를 MySQL 로 이식한다.**\
  `ERROR 1235 … doesn't yet support 'GROUPS'`. `EXCLUDE` 도 같다.
- **`RANGE n PRECEDING` 에 `ORDER BY` 키를 둘 적는다.**\
  둘 다 에러다. 오프셋 `RANGE` 는 키가 하나여야 한다.
- **`RANGE n PRECEDING` 을 문자열 키에 쓴다.**\
  PG 는 「타입이 안 된다」, MySQL 은 「숫자·시간 타입이어야 한다」고 한다. `ROWS` 로 바꾸면 된다.
- **`ORDER BY` 없이 `ROWS` 를 쓴다.**\
  에러가 안 나고 지금은 두 엔진이 같은 답을 냈다 — **그래서 더 위험하다.** 순서가 안 정해졌을 뿐이다.
- **이동 평균의 분모를 프레임 크기로 생각한다.**\
  `NULL` 이 끼면 `AVG` 의 분모가 조용히 줄어든다(7번의 `bob` — 3행 프레임에 분모는 2).

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 기본 프레임 = `RANGE … CURRENT ROW` | **정의** | 언어 — PG·MySQL 문서가 **같은 문장**으로 적는다(1번) |
| `ORDER BY` 없으면 프레임 = 창 전체 | **정의** | 언어 — 두 문서가 명시한다(2번) |
| `RANGE` 의 `CURRENT ROW` = 마지막 피어 | **정의** | 언어 — PG *"the current row's last `ORDER BY` peer"* |
| **동률에서 `ROWS` 의 값** | **비결정** | **아무도 보장 안 한다** — PG 와 MySQL 이 실제로 갈렸다(3번) |
| `RANGE` 의 값이 동률에서 하나로 정해짐 | **정의** | 언어 — 두 엔진 출력이 같았고, 정의상 순서를 안 본다 |
| `GROUPS`·`EXCLUDE` | **방언** | PG 11+ 에만. MySQL 8.4 는 `ERROR 1235`(4·5번) |
| 오프셋 `RANGE` 의 키 개수·타입 제약 | **정의** | 언어 — 두 엔진이 같은 이유로 거부. **메시지만 다르다**(6번) |
| `ORDER BY` 없는 `ROWS` 의 행 순서 | **비결정** | **아무도 보장 안 한다** — 지금 같은 답이 난 것은 관찰이다(8번) |
| `AVG` 결과의 소수 자릿수 | 결과 타입 | 엔진 — 값은 같다 |

- **이 주제에서 값이 갈린 자리는 3번 하나**다. 그런데 그것은 방언 차이가 아니라 **질의문이 답을 정하지 않은 자리**다.
- **`EXCLUDE GROUP`·`EXCLUDE TIES` 는 던져 보지 않았다.** `EXCLUDE CURRENT ROW` 만 확인했다.

## 언제 쓰고 언제 안 쓰나

- **기본 프레임을 그냥 쓴다 — 동률이 없는 키(기본키·타임스탬프)로 줄 세울 때.** 셋이 다 같으므로 고민할 것이 없다.
- **`ROWS` 를 쓴다 — 「앞 n 행」이 요구 그대로일 때.** 이동 평균·직전 3건. **단 `ORDER BY` 에 고유 키를 포함시킨다.**
- **`RANGE` 를 쓴다 — 「같은 값은 한 덩어리」가 요구 그대로일 때.** 등수별 누계·같은 날짜의 합.
- **오프셋 `RANGE` 를 쓴다 — 「값 ±n」이 요구일 때.** 날짜 범위(`RANGE BETWEEN INTERVAL '7' DAY PRECEDING …`)가 대표적이다.
- **`GROUPS` 를 쓴다 — 「앞 등수 몇 개」가 요구일 때.** **PG 전용이므로 이식 계획을 먼저 본다.**
- **안 쓴다 — `ORDER BY` 없이 프레임만.** 답이 정해지지 않는다.
- **안 쓴다 — 순위 함수에 프레임.** `RANK`·`ROW_NUMBER` 는 프레임을 보지 않는다([29번](../29-ranking-functions/)).

## 핵심 문장

- ★ **기본 프레임은 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`** 이고, `ORDER BY` 를 적는 순간 켜진다.
- **`ORDER BY` 가 없으면 프레임은 창 전체**다 — 모두가 서로의 피어이기 때문이다. 규칙은 하나다.
- **`RANGE` 의 `CURRENT ROW` 는 「내 마지막 피어**」다. 그래서 동률 행이 같은 값을 갖는다.
- ★ **동률이 없으면 `ROWS`·`RANGE`·`GROUPS` 가 같은 답**을 낸다. 갈리는 것은 동률이 있을 때뿐이다.
- ★★ **동률이 있으면 `ROWS` 의 답을 질의문이 정하지 않는다** — PG 와 MySQL 이 실제로 다른 값을 냈다.\
  고치려면 **`ORDER BY` 에 고유 키를 더해** 동률 자체를 없앤다.
- **`GROUPS`·`EXCLUDE` 는 PG 11+ 전용**이다. MySQL 8.4 는 `ERROR 1235 … doesn't yet support` 로 거부한다.
- **오프셋 `RANGE` 는 `ORDER BY` 키가 정확히 하나**여야 하고 **뺄 수 있는 타입**이어야 한다. `ROWS` 에는 그 제약이 없다.
- **`ORDER BY` 없는 `ROWS` 는 에러가 안 나고 지금은 두 엔진이 같았다 — 그래서 더 위험하다.**

## 관련 자료

- [PostgreSQL 18 · Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html) — `frame_clause` 의 기본값과 `RANGE`/`GROUPS` 의 피어 정의가 여기 있다.
- [MySQL 8.4 · Window Function Frame Specification](https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html) — 기본 프레임 두 경우를 나눠 적은 페이지.
- [27 PARTITION BY 와 윈도우 ORDER BY](../27-partition-by-and-window-order-by/) — **경계: 그쪽은 「순서를 적으면 값이 바뀐다」는 사실까지, 여기는 그 프레임의 기본값과 세 단위부터.**
- [08 ORDER BY — 정렬 키·NULL 위치·동률](../08-order-by-null-position-stability/) — **경계: 그쪽은 동률의 출력 순서가 보장되지 않는다는 것까지, 여기는 그 불안정이 `ROWS` 의 값을 흔드는 것부터.**
- [21 집계 함수와 `COUNT` 의 세 형태](../21-aggregate-functions-count-forms/) — 7번의 `AVG` 분모가 프레임 안에서도 같은 규칙인 자리.
- [30 오프셋·경계 함수](../30-offset-and-boundary-functions/) — **경계: 여기는 프레임 자체까지, 프레임 때문에 `LAST_VALUE` 가 이상해지는 것은 거기.**
- [29 순위 함수](../29-ranking-functions/) — **경계: 여기는 프레임이 값을 바꾸는 함수들까지, 프레임을 아예 안 보는 함수들은 거기.**
- [10 FROM 절 — 테이블 별칭·파생 테이블·VALUES 리스트](../10-from-clause-aliases-derived-tables/) — `VALUES` 대신 `UNION ALL` 을 쓴 이유.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **프레임(frame)** — 창 안에서 실제로 계산에 쓰이는 범위.\
  예: `ann` 의 창은 7행이지만 기본 프레임은 `[ann, eve]` 두 행이다.
- **피어(peer)** — 윈도우 `ORDER BY` 가 같다고 판정한 행들.\
  예: `ORDER BY salary` 에서 `dan`·`gus`·`hui`(전부 400).
- **`ROWS`** — 프레임을 **행 수**로 세는 단위.\
  예: `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW` 는 「앞 한 행 + 나」다.
- **`RANGE`** — 프레임을 **값**으로 세는 단위. 기본값이다.\
  예: `RANGE BETWEEN 100 PRECEDING AND CURRENT ROW` 는 「내 값 -100 이상인 행들」이다.
- **`GROUPS`** — 프레임을 **피어 덩어리 수**로 세는 단위. **PG 11+ 전용.**\
  예: `GROUPS 1 PRECEDING` 은 「앞 덩어리 하나 + 내 덩어리」다.
- **`UNBOUNDED PRECEDING`** — 창의 맨 처음.\
  예: `ROWS UNBOUNDED PRECEDING` 은 「창의 처음부터 나까지」다.
- **`CURRENT ROW`** — 단위에 따라 뜻이 다르다. `ROWS` 면 **나 하나**, `RANGE`/`GROUPS` 면 **내 마지막 피어**다.\
  예: 같은 `CURRENT ROW` 인데 `ann` 의 프레임이 1행이 되기도 2행이 되기도 한다.
- **`EXCLUDE CURRENT ROW`** — 프레임을 만든 뒤 자기 행만 빼는 지시. **PG 전용.**\
  예: `ann` 의 `600` 이 `300` 이 된다(자기 300 이 빠진다).
- **오프셋 프레임(offset frame)** — `n PRECEDING`/`n FOLLOWING` 처럼 숫자를 준 프레임.\
  예: `RANGE BETWEEN 100 PRECEDING AND 100 FOLLOWING`. `ORDER BY` 키가 하나여야 한다.
- **비결정적(non-deterministic)** — 같은 질의·같은 데이터인데 답이 하나로 정해지지 않는 것.\
  예: 동률이 있는 `ROWS` 누적합. PG 와 MySQL 이 서로 다른 값을 냈다.

## 더 들어가면

- **왜 표준이 `RANGE` 를 기본으로 골랐나.** `ROWS` 를 기본으로 하면 **동률의 순서가 답에 새어 들어간다.**\
  정렬이 안정적이라는 보장이 없으므로([08번](../08-order-by-null-position-stability/)), 기본값이 `ROWS` 였다면 **기본 동작 자체가 비결정적**이 된다.\
  `RANGE` 는 순서를 안 보므로 답이 하나로 정해진다 — **안전한 쪽을 기본값으로 골랐다**고 읽을 수 있다.\
  (이 해석은 **문서에 적힌 근거가 아니라 위 실측에서 끌어낸 추론**이다.)
- **`GROUPS` 가 PG 11(2018)에야 들어온 이유**는 셋 중 가장 늦게 표준에 자리 잡았기 때문이다.\
  `ROWS`·`RANGE` 만으로 못 적는 요구가 실제로 있고(4번), 그래서 별도 단위가 되었다.
- **날짜 범위 프레임**(`RANGE BETWEEN INTERVAL '7' DAY PRECEDING AND CURRENT ROW`)이 오프셋 `RANGE` 의 실전 용도다.\
  `emp`·`dept` 에 날짜 열이 없어 이 주제에서는 **숫자 오프셋으로만** 확인했다(6번) — 날짜 타입은 [40번](../40-date-time-types-and-functions/)이 정본이다.\
  MySQL 의 `ERROR 3587` 이 *"of numeric or temporal type"* 이라 적은 것이 **날짜도 받는다**는 표시다.
- **프레임과 성능** — `ROWS` 는 슬라이딩으로 계산되고 `RANGE`/`GROUPS` 는 피어 경계를 찾아야 한다.\
  **이 주제에서 측정하지 않았다.** 계획 읽는 법은 [목록의 **58번 주제**](../58-explain-plan-tree/)다.
