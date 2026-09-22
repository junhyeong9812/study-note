# sql/29-순위 함수 — `ROW_NUMBER`·`RANK`·`DENSE_RANK`·`NTILE` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Window Functions](https://www.postgresql.org/docs/18/functions-window.html) · [MySQL 8.4 · Window Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **반복 실행** — `ROW_NUMBER` 의 동률 순서는 **각 엔진에서 같은 질의를 10회씩** 돌려 확인했다. 결과는 3번에 있다.\
> **버전** — 네 함수 모두 PG 8.4 · MySQL 8.0 부터. **갈리는 자리는 `NTILE` 의 인자 검사와 `NULL` 위치**다(4·6번).\
> **선행** — [27 PARTITION BY 와 윈도우 ORDER BY](../27-partition-by-and-window-order-by/) · [08 ORDER BY — 정렬 키·NULL 위치·동률](../08-order-by-null-position-stability/).\
> **뒤 주제** — [31 윈도우 함수의 평가 시점](../31-window-evaluation-timing/) — 「그룹별 1위 한 행」을 실제로 거르는 법.

## 한눈에 — 쉽게 말하면

**달리기 시합에서 동시에 들어온 두 사람에게 번호를 어떻게 줄 것인가.**

- **`ROW_NUMBER`** — 「그래도 번호는 달라야 한다」. 1, 2 를 **억지로** 나눠 준다. **누가 1인지는 아무도 안 정했다.**
- **`RANK`** — 「둘 다 1등」. 그다음 사람은 **3등**이다. 자리를 건너뛴다(올림픽 방식).
- **`DENSE_RANK`** — 「둘 다 1등」. 그다음 사람은 **2등**이다. 자리를 안 건너뛴다.
- **`NTILE(n)`** — 등수가 아니라 **조 나누기**. 「상위 3분의 1」 같은 말을 만든다.

★ **동률이 없으면 셋이 같은 값**을 낸다. 셋을 구분할 일이 생기는 건 동률이 있을 때뿐이다.

| 비유 | 실체 | `500·500·400·400·400·300·300` 에 매기면 |
|---|---|---|
| 번호는 무조건 다르게 | `ROW_NUMBER` | `1 2 3 4 5 6 7` — **동률 안의 순서는 보장 없음** |
| 공동 등수, 자리는 건너뜀 | `RANK` | `1 1 3 3 3 6 6` |
| 공동 등수, 자리는 안 건너뜀 | `DENSE_RANK` | `1 1 2 2 2 3 3` |
| 조 나누기 | `NTILE(3)` | 크기 `3·2·2` — **나머지는 앞 조에** |

```text
       salary:  500  500  400  400  400  300  300
       name  :  bob  fay  dan  gus  hui  ann  eve

ROW_NUMBER :      1    2    3    4    5    6    7    다 다르다
RANK       :      1    1    3    3    3    6    6    건너뛴다 (2·4·5 가 없다)
DENSE_RANK :      1    1    2    2    2    3    3    안 건너뛴다
NTILE(3)   :    [ 1    1    1 ][ 2    2 ][ 3    3 ]  3·2·2
                 ^^^^^^^^^^^^^
                 나머지 1 이 첫 조에 붙는다
```

> **동률(tie)/피어(peer)** — 윈도우 `ORDER BY` 가 같다고 판정한 행들.\
> 예: `ORDER BY salary DESC` 에서 `bob`(500)과 `fay`(500).

> **순위 함수(ranking function)** — 값이 아니라 **줄 선 자리**로 결과를 내는 윈도우 함수.\
> 예: `RANK() OVER (ORDER BY salary DESC)`. 인자가 없고 `OVER` 없이는 못 쓴다.

## 이 주제가 답하려는 질문

1. **세 순위 함수는 동률을 어떻게 다르게 세나?** — `1 2 3` / `1 1 3` / `1 1 2` 한 줄이 전부다.
2. **`ROW_NUMBER` 가 비결정적이라는 말은 무슨 뜻인가?** — 동률이 있고 고유 키가 없으면 **질의문이 답을 정하지 않는다.**
3. **`NTILE` 은 나누어떨어지지 않는 나머지를 어디에 붙이나?** — **앞 조**에 하나씩 붙인다.

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
emp8 을 salary DESC 로 줄 세운 모습

  500  500 | 400  400  400 | 300  300 |  NULL
  bob  fay | dan  gus  hui | ann  eve |  cho
  \_______/  \___________/  \_______/   \___/
   동률 2      동률 3         동률 2     NULL 하나
```

**왜 이 데이터가 순위 주제에 맞는가.** 동률과 `NULL` 이 없으면 이 주제는 성립하지 않는다.

- **동률 덩어리가 셋이고 크기가 2·3·2 다.** 크기가 다르므로 `RANK` 가 **얼마나** 건너뛰는지 보인다(1 → 3 → 6).\
  **동률이 없으면 세 함수가 전부 `1 2 3 4 …`** 로 같아져서 구분할 것이 없다.
- **고유한 키(`id`)가 따로 있다.** `ORDER BY salary` 만 쓰면 `ROW_NUMBER` 가 비결정적이고,\
  `ORDER BY salary, id` 로 고치면 결정적이 된다 — **같은 데이터로 고치기 전후를 나란히** 볼 수 있다(3번).
- **행이 8개다.** `NTILE(3)` → `3·3·2`, `NTILE(5)` → `2·2·2·1·1` 로 **나머지가 앞 조에 붙는 것**이 보인다(5번).
- **`cho` 의 `salary` 가 `NULL` 이다** — 「급여 순위」에서 급여가 **없는** 사람이 몇 등이 되는지가 두 엔진에서 갈린다(6번).
- **부서가 셋이다**(`10`·`20`·`NULL`) — 「부서별 1등」이라는 요구를 만들 수 있다(7번).

`cho` 가 섞이면 무엇 때문에 갈렸는지 흐려지므로, 1~5번은 **`WHERE salary IS NOT NULL` 로 7행**을 쓴다.

## 동작 방식

---

### 1. ★ 세 함수는 동률을 세 가지로 센다

**언제 쓰나** — 「등수」라는 말을 들을 때마다. **요구가 셋 중 어느 것인지 먼저 정해야 한다.**

```text
동률 앞에서 각자가 하는 일

ROW_NUMBER : "자리 하나에 한 사람" -> 동률이어도 억지로 쪼갠다
RANK       : "같은 값이면 같은 등수" -> 다음 등수는 "내 앞에 몇 명 있나" + 1
DENSE_RANK : "같은 값이면 같은 등수" -> 다음 등수는 "내 앞에 몇 종류 있나" + 1
```

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER w AS rn, RANK() OVER w AS rk,
                DENSE_RANK() OVER w AS drk, NTILE(3) OVER w AS nt
         FROM emp8 WHERE salary IS NOT NULL
         WINDOW w AS (ORDER BY salary DESC) ORDER BY salary DESC, id;
--- PG 18.6 ---
 name | salary | rn | rk | drk | nt
------+--------+----+----+-----+----
 bob  |    500 |  1 |  1 |   1 |  1
 fay  |    500 |  2 |  1 |   1 |  1
 dan  |    400 |  5 |  3 |   2 |  2
 gus  |    400 |  3 |  3 |   2 |  1
 hui  |    400 |  4 |  3 |   2 |  2
 ann  |    300 |  7 |  6 |   3 |  3
 eve  |    300 |  6 |  6 |   3 |  3
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+----+----+-----+----+
| name | salary | rn | rk | drk | nt |
+------+--------+----+----+-----+----+
| bob  |    500 |  1 |  1 |   1 |  1 |
| fay  |    500 |  2 |  1 |   1 |  1 |
| dan  |    400 |  3 |  3 |   2 |  1 |
| gus  |    400 |  4 |  3 |   2 |  2 |
| hui  |    400 |  5 |  3 |   2 |  2 |
| ann  |    300 |  6 |  6 |   3 |  3 |
| eve  |    300 |  7 |  6 |   3 |  3 |
+------+--------+----+----+-----+----+
```

그림 해설 — **`rk` 와 `drk` 열은 두 엔진에서 한 자리도 안 다르다.** `1 1 3 3 3 6 6` 과 `1 1 2 2 2 3 3` 이다.\
**`rn` 과 `nt` 열은 갈렸다** — 동률 안에서 누가 먼저인지를 질의문이 안 정했기 때문이다(3번).

`RANK` 가 `3` 다음에 `6` 으로 뛴 것에 주목하라 — **400 인 사람이 셋**이라 `3+3=6` 이다.\
`DENSE_RANK` 는 `2` 다음이 `3` 이다 — **값의 종류**만 센다.

★ **`WINDOW w AS (...)` 로 창에 이름을 붙였다.** 같은 창을 네 번 적으면 오타 하나로 다른 창이 된다([31번](../31-window-evaluation-timing/)).

비용 — 창을 한 번 정렬하고 한 번 훑는다. 세 함수를 같이 뽑아도 정렬은 한 번이다(같은 창이므로).

---

### 2. `RANK` 와 `DENSE_RANK` 중 무엇을 쓰나 — 요구가 정한다

**언제 쓰나** — 「3등까지 상을 준다」·「상위 3개 등급」 같은 말을 들었을 때.

```text
"3등까지 상을 준다"

RANK       : 1 1 3 3 3 6 6  -> rk <= 3 이면 다섯 명이 받는다
DENSE_RANK : 1 1 2 2 2 3 3  -> drk <= 3 이면 일곱 명 전부가 받는다
                                ^^^^^^^^^^^^^^^^^^^^^^
                                같은 문장이 전혀 다른 결과를 낸다
```

그림 해설 — **둘 중 무엇을 쓸지는 SQL 이 정해 주지 않는다.** 「3등까지」라는 말이 애매한 것이지 함수가 애매한 게 아니다.\
요구를 받을 때 「**동점자가 나오면 몇 명까지 주나**」를 물어야 한다.

★ **랭킹 도메인의 규칙**(동점 처리 정책·재집계·보상 배분)은 여기가 정본이 아니다 —\
[`domain-modeling/basic/24-leaderboard`](../../../../../domain-modeling/basic/24-leaderboard/)와 [`advanced/19-leaderboard-recount`](../../../../../domain-modeling/advanced/19-leaderboard-recount/)가 그 자리다.\
**여기서는 함수가 무엇을 돌려주는지까지만** 다룬다.

비용 — 같다. 둘 다 정렬 한 번이다.

---

### 3. ★ `ROW_NUMBER` 가 비결정적인 자리 — 동률 + 고유 키 없음

**언제 쓰나** — 「각 그룹에서 한 행만」을 뽑을 때. 그리고 그 한 행이 **매번 같은 행인지** 물을 때.

**먼저 반복 실행.** 각 엔진에서 **같은 질의를 10회씩** 돌렸다.

```text
### SQL: SELECT name, ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn FROM emp8 WHERE salary IS NOT NULL;
         (결과를 한 줄로 이어 붙여 10회 비교)
--- PG 18.6 · 10회 ---
bob:1 fay:2 gus:3 hui:4 dan:5 eve:6 ann:7      <- 10회 전부 같았다
--- MySQL 8.4.10 · 10회 ---
bob:1 fay:2 dan:3 gus:4 hui:5 ann:6 eve:7      <- 10회 전부 같았다
```

그림 해설 — ★ **각 엔진 안에서는 10회가 전부 같았다. 그런데 두 엔진의 답이 다르다.**\
`gus`·`hui`·`dan` 의 자리와 `ann`·`eve` 의 자리가 서로 다르다.

★ **「10회 같았다」는 보장이 아니다.** 같은 계획을 열 번 썼을 뿐이다 — **반증은 엔진을 바꿨을 때 나왔다.**

**입력 순서를 바꾸면 한 엔진 안에서도 뒤집힌다.**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn
         FROM (SELECT * FROM emp8 WHERE salary IS NOT NULL ORDER BY name DESC LIMIT 7) t ORDER BY rn;
--- PG 18.6 ---
 name | salary | rn
------+--------+----
 bob  |    500 |  1
 fay  |    500 |  2
 gus  |    400 |  3
 hui  |    400 |  4
 dan  |    400 |  5
 eve  |    300 |  6
 ann  |    300 |  7
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+----+
| name | salary | rn |
+------+--------+----+
| fay  |    500 |  1 |
| bob  |    500 |  2 |
| hui  |    400 |  3 |
| gus  |    400 |  4 |
| dan  |    400 |  5 |
| eve  |    300 |  6 |
| ann  |    300 |  7 |
+------+--------+----+
```

★ **이 실험은 한쪽에서만 결론이 선다 — 그렇게 밝힌다.**

| 엔진 | 10회 반복 | 입력 순서 바꾸기 | 이 엔진 안에서 반증이 났나 |
|---|---|---|---|
| PG 18.6 | 전부 같음 | **기본 판과 같음** | **안 났다** |
| MySQL 8.4.10 | 전부 같음 | **`bob`/`fay`·`gus`/`hui` 가 뒤집혔다** | **났다** |

**한 엔진 안의 반증은 MySQL 쪽에서만 나왔다.** PG 는 세 판이 전부 같았다.\
그래도 결론은 선다 — **두 엔진의 기본 판이 이미 다르기 때문**이다(위 10회 비교). 근거 둘의 성격이 다르므로 나눠 적는다.

**고치는 법 — 고유 키를 `ORDER BY` 에 더한다.**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn
         FROM emp8 WHERE salary IS NOT NULL ORDER BY rn;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rn              +------+--------+----+
------+--------+----             | name | salary | rn |
 bob  |    500 |  1              +------+--------+----+
 fay  |    500 |  2              | bob  |    500 |  1 |
 dan  |    400 |  3              | fay  |    500 |  2 |
 gus  |    400 |  4              | dan  |    400 |  3 |
 hui  |    400 |  5              | gus  |    400 |  4 |
 ann  |    300 |  6              | hui  |    400 |  5 |
 eve  |    300 |  7              | ann  |    300 |  6 |
(7 rows)                         | eve  |    300 |  7 |
                                 +------+--------+----+
```

그림 해설 — **`, id` 여섯 글자로 두 엔진이 한 자리도 안 갈리게 됐다.**\
[08번](../08-order-by-null-position-stability/) 5번의 처방과 같은 것이다 — **고유한 열을 마지막 키로 더한다.**

★ **`RANK`·`DENSE_RANK` 는 이 문제가 없다.** 동률에 같은 값을 주므로 **내부 순서를 알 필요가 없기** 때문이다.\
[28번](../28-window-frames-rows-range-groups/) 3번의 `ROWS` 대 `RANGE` 와 **똑같은 구조**다 — 행을 세느냐 값을 보느냐.

비용 — 정렬 키가 하나 는다. 그 대신 답이 정해진다.

---

### 4. ★ `NTILE` 의 인자 — 0·음수·`NULL` 을 던져 보면 갈린다

**언제 쓰나** — 「상위 25%」·「사분위」처럼 **조 나누기**가 필요할 때. 그리고 조 개수가 **변수로 들어올 때**.

```text
### SQL: SELECT name, salary, NTILE(0) OVER (ORDER BY salary) AS nt FROM emp8;
--- PG 18.6 ---
ERROR:  argument of ntile must be greater than zero
--- MySQL 8.4.10 ---
ERROR 1210 (HY000) at line 1: Incorrect arguments to ntile
```

```text
### SQL: SELECT name, salary, NTILE(-1) OVER (ORDER BY salary) AS nt FROM emp8;
--- PG 18.6 ---
ERROR:  argument of ntile must be greater than zero
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '-1) OVER (ORDER BY salary) AS nt FROM emp8' at line 7
```

```text
### SQL: SELECT name, salary, NTILE(NULL) OVER (ORDER BY salary) AS nt FROM emp8;
--- PG 18.6 ---
 name | salary |  nt
------+--------+------
 ann  |    300 | NULL
 eve  |    300 | NULL
 dan  |    400 | NULL
 hui  |    400 | NULL
 gus  |    400 | NULL
 fay  |    500 | NULL
 bob  |    500 | NULL
 cho  |   NULL | NULL
(8 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NULL) OVER (ORDER BY salary) AS nt FROM emp8' at line 7
```

그림 해설 — ★ **세 경우가 서로 다른 방식으로 갈린다.**

| 인자 | PG 18.6 | MySQL 8.4.10 | 어디서 걸리나 |
|---|---|---|---|
| `0` | `ERROR: argument of ntile must be greater than zero` | `ERROR 1210` 잘못된 인자 | **둘 다 실행 단계** |
| `-1` | 같은 `ERROR`(0과 동일) | **`ERROR 1064` 문법 오류** | PG 는 실행, **MySQL 은 파서** |
| `NULL` | **돈다 — 전 행이 `NULL`** | **`ERROR 1064` 문법 오류** | PG 는 값으로, **MySQL 은 파서** |

★ **MySQL 의 파서는 `NTILE` 자리에 「부호 없는 정수 리터럴」만 받는다.** `-1` 도 `NULL` 도 문법 오류다.\
PG 는 **식**을 받으므로 `NULL` 이 들어가면 값으로 계산해 **전 행에 `NULL`** 을 돌려준다.

★ **PG 의 `NTILE(NULL)` 이 에러가 아니라는 점이 더 위험하다.** 조 개수를 파라미터로 받는 코드에서\
`NULL` 이 흘러 들어오면 **에러 없이 조 번호가 통째로 `NULL`** 이 된다. MySQL 이라면 파서가 막았을 자리다.

`NTILE` 은 값이 아니라 **순서**로 조를 나누므로 `cho`(salary `NULL`)도 조에 들어간다 — 어느 조인지는 6번의 `NULL` 위치가 정한다.

비용 — 창의 행 수를 알아야 하므로 창을 한 번 다 훑는다.

---

### 5. `NTILE` 의 나머지는 **앞 조**에 붙는다

**언제 쓰나** — 행 수가 조 개수로 나누어떨어지지 않을 때. 즉 거의 매번.

```text
8행을 3조로: 8 = 3*2 + 2  -> 나머지 2 를 앞 두 조에 하나씩
                              -> 3 · 3 · 2

8행을 5조로: 8 = 5*1 + 3  -> 나머지 3 을 앞 세 조에 하나씩
                              -> 2 · 2 · 2 · 1 · 1
```

```text
### SQL: SELECT name, salary, NTILE(3) OVER (ORDER BY id) AS nt, NTILE(4) OVER (ORDER BY id) AS nt4,
                NTILE(5) OVER (ORDER BY id) AS nt5
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | nt | nt4 | nt5  +------+--------+----+-----+-----+
------+--------+----+-----+----- | name | salary | nt | nt4 | nt5 |
 ann  |    300 |  1 |   1 |   1  +------+--------+----+-----+-----+
 bob  |    500 |  1 |   1 |   1  | ann  |    300 |  1 |   1 |   1 |
 cho  |   NULL |  1 |   2 |   2  | bob  |    500 |  1 |   1 |   1 |
 dan  |    400 |  2 |   2 |   2  | cho  |   NULL |  1 |   2 |   2 |
 eve  |    300 |  2 |   3 |   3  | dan  |    400 |  2 |   2 |   2 |
 fay  |    500 |  2 |   3 |   3  | eve  |    300 |  2 |   3 |   3 |
 gus  |    400 |  3 |   4 |   4  | fay  |    500 |  2 |   3 |   3 |
 hui  |    400 |  3 |   4 |   5  | gus  |    400 |  3 |   4 |   4 |
(8 rows)                         | hui  |    400 |  3 |   4 |   5 |
                                 +------+--------+----+-----+-----+
```

그림 해설 — **`ORDER BY id` 로 고유 키를 썼더니 두 엔진이 한 자리도 안 갈렸다.**\
조 크기를 세어 보면 `NTILE(3)` → **3·3·2**, `NTILE(4)` → **2·2·2·2**, `NTILE(5)` → **2·2·2·1·1** 이다.

★ **나머지는 뒤가 아니라 앞에 붙는다.** PG 문서가 *"dividing the partition as equally as possible"* 이라고만 적으므로\
**「가능한 한 고르게」의 구체적 배분은 실행으로 확인한 것**이다. 두 엔진이 같았다.

**조 개수가 행 수보다 많으면** 앞에서부터 한 행씩 들어가고 **뒤쪽 조는 빈다.**

```text
### SQL: SELECT name, salary, NTILE(20) OVER (ORDER BY id) AS nt FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | nt              +------+--------+----+
------+--------+----             | name | salary | nt |
 ann  |    300 |  1              +------+--------+----+
 bob  |    500 |  2              | ann  |    300 |  1 |
 cho  |   NULL |  3              | bob  |    500 |  2 |
 dan  |    400 |  4              | cho  |   NULL |  3 |
 eve  |    300 |  5              | dan  |    400 |  4 |
 fay  |    500 |  6              | eve  |    300 |  5 |
 gus  |    400 |  7              | fay  |    500 |  6 |
 hui  |    400 |  8              | gus  |    400 |  7 |
(8 rows)                         | hui  |    400 |  8 |
                                 +------+--------+----+
```

★ **9~20조는 결과에 아예 안 나온다.** 「20분위로 나눴다」고 적어 놓고 실제로는 8개 조뿐인 것을\
**결과만 봐서는 모른다** — `MAX(nt)` 를 같이 뽑아야 드러난다.

비용 — 창 전체를 한 번 훑는다.

---

### 6. ★ 방언 — 「급여 순위」에서 급여 없는 사람이 몇 등인가

**언제 쓰나** — `NULL` 이 있을 수 있는 열로 순위를 매길 때. 즉 대부분의 실데이터에서.

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER w AS rn, RANK() OVER w AS rk,
                DENSE_RANK() OVER w AS drk, NTILE(3) OVER w AS nt
         FROM emp8 WINDOW w AS (ORDER BY salary DESC) ORDER BY salary DESC, id;
--- PG 18.6 ---
 name | salary | rn | rk | drk | nt
------+--------+----+----+-----+----
 cho  |   NULL |  1 |  1 |   1 |  1
 bob  |    500 |  2 |  2 |   2 |  1
 fay  |    500 |  3 |  2 |   2 |  1
 dan  |    400 |  6 |  4 |   3 |  2
 gus  |    400 |  4 |  4 |   3 |  2
 hui  |    400 |  5 |  4 |   3 |  2
 ann  |    300 |  8 |  7 |   4 |  3
 eve  |    300 |  7 |  7 |   4 |  3
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+----+----+-----+----+
| name | salary | rn | rk | drk | nt |
+------+--------+----+----+-----+----+
| bob  |    500 |  1 |  1 |   1 |  1 |
| fay  |    500 |  2 |  1 |   1 |  1 |
| dan  |    400 |  3 |  3 |   2 |  1 |
| gus  |    400 |  4 |  3 |   2 |  2 |
| hui  |    400 |  5 |  3 |   2 |  2 |
| ann  |    300 |  6 |  6 |   3 |  2 |
| eve  |    300 |  7 |  6 |   3 |  3 |
| cho  |   NULL |  8 |  8 |   4 |  3 |
+------+--------+----+----+-----+----+
```

그림 해설 — ★★ **PG 에서 `cho` 가 1등이다.** 급여가 **없는** 사람이 「급여 높은 순」의 맨 앞에 섰다.

```text
ORDER BY salary DESC

PG   : NULL 을 "가장 큰 값" 으로 본다 -> DESC 에서 맨 앞 -> cho 가 1등
MySQL: NULL 을 "가장 작은 값" 으로 본다 -> DESC 에서 맨 뒤 -> cho 가 8등
```

★ **그 한 행 때문에 모든 등수가 하나씩 밀린다.** `bob` 이 PG 에서 2등, MySQL 에서 1등이다.\
「1등에게 상을 준다」는 질의가 **엔진을 바꾸면 다른 사람에게 상을 준다.**

**뿌리는 [08번](../08-order-by-null-position-stability/)의 `NULL` 위치 규칙 하나**다 — 창 안에 그대로 들어왔다([27번](../27-partition-by-and-window-order-by/) 6번).

**고치는 법 둘.**

```sql
-- (1) 순위에서 빼는 것이 요구에 맞으면 — 가장 정직하다
SELECT ... FROM emp8 WHERE salary IS NOT NULL;

-- (2) 남겨야 하면 NULL 을 맨 뒤로 고정한다 (두 엔진 모두에서 돈다)
RANK() OVER (ORDER BY (salary IS NULL), salary DESC)
```

★ **PG 의 `NULLS LAST` 는 MySQL 에서 `ERROR 1064`** 다. 이식할 질의에는 `(열 IS NULL)` 키를 쓴다([08번](../08-order-by-null-position-stability/) 3번).

비용 — 정렬 키가 하나 는다.

---

### 7. 「그룹별 1위」 — `ROW_NUMBER` 와 `RANK` 가 다른 답을 낸다

**언제 쓰나** — 「부서별 최고 연봉자」·「고객별 최근 주문」. 실무에서 가장 흔한 윈도우 용도다.

```text
요구: "부서마다 최고 연봉자"

ROW_NUMBER ... rn = 1  ->  부서마다 정확히 한 행     (동률이면 누구인지는 안 정해진다)
RANK       ... rk = 1  ->  부서마다 동률 전부        (두 명일 수도 있다)
```

```text
### SQL: WITH ranked AS (SELECT dept_id, name, salary,
                ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC, id) AS rn
                FROM emp8 WHERE salary IS NOT NULL)
         SELECT dept_id, name, salary FROM ranked WHERE rn = 1 ORDER BY (dept_id IS NULL), dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | name | salary         +---------+------+--------+
---------+------+--------        | dept_id | name | salary |
      10 | bob  |    500         +---------+------+--------+
      20 | gus  |    400         |      10 | bob  |    500 |
    NULL | dan  |    400         |      20 | gus  |    400 |
(3 rows)                         |    NULL | dan  |    400 |
                                 +---------+------+--------+
```

```text
### SQL: WITH ranked AS (SELECT dept_id, name, salary,
                RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rk
                FROM emp8 WHERE salary IS NOT NULL)
         SELECT dept_id, name, salary, rk FROM ranked WHERE rk = 1 ORDER BY (dept_id IS NULL), dept_id, name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | name | salary | rk    +---------+------+--------+----+
---------+------+--------+---    | dept_id | name | salary | rk |
      10 | bob  |    500 |  1    +---------+------+--------+----+
      10 | fay  |    500 |  1    |      10 | bob  |    500 |  1 |
      20 | gus  |    400 |  1    |      10 | fay  |    500 |  1 |
      20 | hui  |    400 |  1    |      20 | gus  |    400 |  1 |
    NULL | dan  |    400 |  1    |      20 | hui  |    400 |  1 |
(5 rows)                         |    NULL | dan  |    400 |  1 |
                                 +---------+------+--------+----+
```

두 그림의 결론 — ★ **`ROW_NUMBER` 는 3행, `RANK` 는 5행이다.** 같은 「1위」인데 행 수가 다르다.\
`sales` 의 `bob`·`fay` 와 `dev` 의 `gus`·`hui` 가 각각 동률이기 때문이다.

★ **`ROW_NUMBER` 쪽에 `, id` 를 넣은 것에 주목하라.** 안 넣으면 `bob` 이 올지 `fay` 가 올지 **정해지지 않는다**(3번).\
「한 행만」이 요구라면 **어느 한 행인지도 요구가 정해야** 한다 — 안 정하면 질의가 몰래 정한다.

★ **`WHERE rn = 1` 이 바깥 질의에 있는 것**도 필수다. 윈도우 결과는 `WHERE` 에서 못 거른다([31번](../31-window-evaluation-timing/)).

비용 — CTE 한 겹. 계획상으로는 정렬 + 필터다.

---

### 8. 순위 함수는 **프레임을 보지 않는다** · `ORDER BY` 없이도 돈다

**언제 쓰나** — 프레임을 적어 놓고 「뭔가 달라졌겠지」라고 믿을 때. 그리고 `ORDER BY` 를 빠뜨렸을 때.

```text
### SQL: SELECT name, salary, RANK() OVER () AS rk, DENSE_RANK() OVER () AS drk,
                ROW_NUMBER() OVER () AS rn
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rk | drk | rn   +------+--------+----+-----+----+
------+--------+----+-----+----  | name | salary | rk | drk | rn |
 ann  |    300 |  1 |   1 |  1   +------+--------+----+-----+----+
 bob  |    500 |  1 |   1 |  2   | ann  |    300 |  1 |   1 |  1 |
 cho  |   NULL |  1 |   1 |  3   | bob  |    500 |  1 |   1 |  2 |
 dan  |    400 |  1 |   1 |  4   | cho  |   NULL |  1 |   1 |  3 |
 eve  |    300 |  1 |   1 |  5   | dan  |    400 |  1 |   1 |  4 |
 fay  |    500 |  1 |   1 |  6   | eve  |    300 |  1 |   1 |  5 |
 gus  |    400 |  1 |   1 |  7   | fay  |    500 |  1 |   1 |  6 |
 hui  |    400 |  1 |   1 |  8   | gus  |    400 |  1 |   1 |  7 |
(8 rows)                         | hui  |    400 |  1 |   1 |  8 |
                                 +------+--------+----+-----+----+
```

그림 해설 — ★ **에러가 아니다.** `ORDER BY` 가 없으면 **모두가 서로의 피어**이므로 `RANK` 는 전부 1이다([28번](../28-window-frames-rows-range-groups/) 2번).\
`ROW_NUMBER` 만 `1~8` 을 주는데, **그 순서가 무엇인지는 아무도 안 정했다.**

**프레임을 적어도 순위는 안 바뀐다.**

```text
### SQL: SELECT name, salary, RANK() OVER (ORDER BY salary) AS plain,
                RANK() OVER (ORDER BY salary ROWS UNBOUNDED PRECEDING) AS framed
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | plain | framed  +------+--------+-------+--------+
------+--------+-------+-------  | name | salary | plain | framed |
 ann  |    300 |     1 |      1  +------+--------+-------+--------+
 eve  |    300 |     1 |      1  | ann  |    300 |     1 |      1 |
 dan  |    400 |     3 |      3  | eve  |    300 |     1 |      1 |
 gus  |    400 |     3 |      3  | dan  |    400 |     3 |      3 |
 hui  |    400 |     3 |      3  | gus  |    400 |     3 |      3 |
 bob  |    500 |     6 |      6  | hui  |    400 |     3 |      3 |
 fay  |    500 |     6 |      6  | bob  |    500 |     6 |      6 |
(7 rows)                         | fay  |    500 |     6 |      6 |
                                 +------+--------+-------+--------+
```

그림 해설 — **두 열이 같다.** PG 문서가 `row_number`·`rank`·`dense_rank`·`percent_rank`·`cume_dist`·`ntile`·`lag`·`lead` 를\
**프레임에 의존하지 않는 함수**로 묶어 적는다. **에러가 아니라 무시된다** — 그래서 적어 놓고 넘어가기 쉽다.

★ **`FIRST_VALUE`·`LAST_VALUE`·`NTH_VALUE` 는 반대로 프레임을 본다.** 그 비대칭이 [30번](../30-offset-and-boundary-functions/)의 함정을 만든다.

비용 — 없다. 무시되는 절이다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
ROW_NUMBER()  OVER (PARTITION BY ... ORDER BY ...)   -- 인자 없음
RANK()        OVER (...)                             -- 인자 없음
DENSE_RANK()  OVER (...)                             -- 인자 없음
NTILE(n)      OVER (...)                             -- n = 조 개수, 1 이상
PERCENT_RANK() · CUME_DIST()  OVER (...)             -- 비율로 주는 형태
```

규칙 일곱.

1. **순위 함수는 `OVER` 없이 못 쓴다.** 집계 함수와 달리 「그냥 함수」로 쓰이는 형태가 없다.
2. **`ROW_NUMBER` 는 `1 2 3`, `RANK` 는 `1 1 3`, `DENSE_RANK` 는 `1 1 2`** 다. 동률이 없으면 셋이 같다.
3. **`ROW_NUMBER` 는 동률 + 고유 키 없음에서 비결정적**이다. `ORDER BY` 에 고유 키를 더한다.
4. **`RANK`·`DENSE_RANK` 는 비결정적일 수 없다.** 동률에 같은 값을 주므로 내부 순서가 필요 없다.
5. **`NTILE` 의 나머지는 앞 조에 붙는다.** 8행 3조 → `3·3·2`.
6. **순위 함수는 프레임을 무시한다.** 적어도 에러가 아니고 값도 안 바뀐다.
7. **`ORDER BY` 가 없으면 `RANK`·`DENSE_RANK` 는 전부 1** 이고 `ROW_NUMBER` 만 번호를 준다(순서는 보장 없음).

실전 형태는 넷이다.

```sql
-- (1) 그룹별 1위 한 행 — 어느 한 행인지까지 정한다
ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC, id)

-- (2) 그룹별 1위 전부 — 동률을 다 남긴다
RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC)

-- (3) 등급 — 값의 종류로 센다
DENSE_RANK() OVER (ORDER BY salary DESC)

-- (4) 분위 — 조 나누기
NTILE(4) OVER (ORDER BY salary DESC)
```

## 어디서 틀리나

- **★ 「등수」를 듣고 함수를 먼저 고른다.**\
  「3등까지」가 `RANK<=3`(5명)인지 `DENSE_RANK<=3`(7명)인지 **요구가 정해야** 한다. 물어보지 않으면 조용히 틀린다.
- **★ `ROW_NUMBER` 로 그룹별 1위를 뽑으면서 고유 키를 안 넣는다.**\
  동률이면 **누가 뽑힐지 정해지지 않는다.** 두 엔진이 실제로 다른 사람을 뽑았다(3번).
- **★ 「열 번 돌려 봤는데 같더라」를 근거로 쓴다.**\
  PG·MySQL 각각 10회가 전부 같았다. **그런데 두 엔진의 답이 서로 달랐다.** 반복은 보장이 아니다.
- **★ `NULL` 이 있는 열로 순위를 매긴다.**\
  PG 는 `DESC` 에서 `NULL` 이 1등이다. 「최고 연봉자」가 **급여 미기록자**가 된다(6번).
- **`NTILE` 의 조 개수를 변수로 받는다.**\
  PG 에서 `NTILE(NULL)` 은 **에러가 아니라 전 행 `NULL`** 이다. MySQL 은 파서가 막는다. 0·음수는 양쪽 다 거부다.
- **`NTILE(n)` 에서 n 이 행 수보다 크다.**\
  뒤쪽 조가 조용히 비어 결과에 안 나온다. 「20분위」라고 적고 8개 조만 있는 것을 결과만 봐서는 모른다.
- **순위 함수에 프레임을 적고 뭔가 달라졌다고 믿는다.**\
  에러도 안 나고 값도 안 바뀐다. 무시된다.
- **윈도우 결과를 `WHERE rn = 1` 로 바로 거른다.**\
  두 엔진 다 에러다. 한 겹 감싸야 한다([31번](../31-window-evaluation-timing/)).

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `RANK` 가 `1 1 3`, `DENSE_RANK` 가 `1 1 2` | **정의** | 언어 — 두 엔진 출력이 한 자리도 안 갈렸다 |
| **동률에서 `ROW_NUMBER` 의 번호** | **비결정** | **아무도 보장 안 한다** — 두 엔진이 갈렸고 MySQL 은 입력 순서로도 뒤집혔다 |
| `ORDER BY` 에 고유 키를 더하면 결정적 | **정의** | 언어 — 동률이 없으면 순서가 하나로 정해진다(3번) |
| **`NULL` 의 순위 위치** | **방언** | 엔진 — PG `DESC` 에서 1등 / MySQL 8등(6번) |
| `NTILE` 의 나머지가 앞 조에 | 문서는 *"as equally as possible"* 까지만 | **실행으로 확인**했다 — 두 엔진이 같았다(5번) |
| `NTILE(0)` 거부 | **정의** | 언어 — 둘 다 실행 단계에서 거부. 메시지는 다르다 |
| **`NTILE(-1)`·`NTILE(NULL)`** | **방언** | MySQL 은 **파서**가 막고(`1064`), PG 는 식으로 받는다 |
| 순위 함수가 프레임을 무시 | **정의** | 언어 — PG 문서가 함수 목록으로 명시. 두 엔진 출력이 같았다 |
| `RANK` 와 `DENSE_RANK` 중 무엇을 쓰나 | **요구의 문제** | SQL 이 아니라 도메인이 정한다(2번) |

- **이 주제에서 값이 갈린 자리는 셋이다** — `ROW_NUMBER` 의 동률 순서(3번) · `NULL` 의 위치(6번) · `NTILE` 인자 검사(4번).
- 앞의 둘은 **같은 뿌리**다 — `ORDER BY` 가 답을 끝까지 정하지 않은 자리.

## 언제 쓰고 언제 안 쓰나

- **`ROW_NUMBER` 를 쓴다 — 「딱 한 행」이 필요할 때.** 중복 제거·그룹별 최신 1건·페이지 번호.\
  **반드시 고유 키를 `ORDER BY` 에 포함시킨다.**
- **`RANK` 를 쓴다 — 동률을 공동 등수로 보고, 그만큼 뒤 등수를 밀어야 할 때.** 시상·리그 순위.
- **`DENSE_RANK` 를 쓴다 — 「등급」처럼 값의 종류를 세야 할 때.** 「상위 3개 급여 구간」.
- **`NTILE` 을 쓴다 — 「상위 몇 %」가 요구일 때.** 사분위·십분위.
- **안 쓴다 — 최댓값 한 개만 필요할 때.** `MAX` + `LIMIT` 가 더 싸다(정렬 전체가 필요 없다).
- **안 쓴다 — 순위 자체가 도메인 규칙일 때.** 동점 정책·재집계는 [`24-leaderboard`](../../../../../domain-modeling/basic/24-leaderboard/)가 정본이다.
- **안 쓴다 — `WHERE` 로 바로 거르려 할 때.** 안 된다. 한 겹 감싼다([31번](../31-window-evaluation-timing/)).

## 핵심 문장

- **`ROW_NUMBER` 는 `1 2 3`, `RANK` 는 `1 1 3`, `DENSE_RANK` 는 `1 1 2`** — 동률이 없으면 셋이 같다.
- `RANK` 가 3 다음 6 으로 뛴 것은 **400 인 사람이 셋**이기 때문이다. `DENSE_RANK` 는 **값의 종류**만 센다.
- ★ **`ROW_NUMBER` 는 동률 + 고유 키 없음에서 비결정적**이다 — PG 와 MySQL 이 서로 다른 번호를 줬다.
- ★ **각 엔진에서 10회가 전부 같았다. 그래서 더 위험하다** — 반복은 보장이 아니고, 반증은 엔진을 바꿨을 때 나왔다.
- **고치는 법은 `ORDER BY salary DESC, id`** — 고유 키 하나로 두 엔진이 같아졌다([08번](../08-order-by-null-position-stability/)과 같은 처방).
- ★ **`NULL` 이 섞이면 PG 는 `DESC` 에서 `NULL` 이 1등**이고 MySQL 은 8등이다. 등수가 통째로 밀린다.
- **`NTILE` 의 나머지는 앞 조**에 붙는다 — 8행 3조는 `3·3·2` 다. 조 개수가 행 수보다 크면 뒤쪽 조는 빈다.
- **`NTILE(0)` 은 둘 다 거부**하지만 **`NTILE(-1)`·`NTILE(NULL)` 은 MySQL 만 파서가 막는다** — PG 는 전 행 `NULL` 을 준다.
- **순위 함수는 프레임을 무시한다.** 에러가 아니라 무시다.
- **「그룹별 1위」는 `ROW_NUMBER` 면 3행, `RANK` 면 5행**이다. 요구가 어느 쪽인지 먼저 정한다.

## 관련 자료

- [PostgreSQL 18 · Window Functions](https://www.postgresql.org/docs/18/functions-window.html) — 네 함수의 정의와 *"do not depend on frame specifications"* 목록이 여기 있다.
- [MySQL 8.4 · Window Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html) — `NTILE`·`RANK`·`DENSE_RANK` 설명.
- [27 PARTITION BY 와 윈도우 ORDER BY](../27-partition-by-and-window-order-by/) — **경계: 그쪽은 창을 나누고 줄 세우는 것까지, 여기는 그 줄에 번호를 매기는 네 방식부터.**
- [08 ORDER BY — 정렬 키·NULL 위치·동률](../08-order-by-null-position-stability/) — **경계: 그쪽은 동률의 출력 순서가 보장되지 않는다는 것과 `NULL` 위치까지, 여기는 그 둘이 순위 값 자체를 바꾸는 것부터.**
- [28 프레임 — ROWS·RANGE·GROUPS](../28-window-frames-rows-range-groups/) — **경계: 그쪽은 프레임이 값을 바꾸는 함수들까지, 여기는 프레임을 아예 안 보는 함수들부터.**
- [31 윈도우 함수의 평가 시점](../31-window-evaluation-timing/) — **경계: 여기는 순위 값을 만드는 데까지, 그 값으로 행을 거르는 법은 거기.**
- [`domain-modeling/basic/24-leaderboard`](../../../../../domain-modeling/basic/24-leaderboard/) · [`advanced/19-leaderboard-recount`](../../../../../domain-modeling/advanced/19-leaderboard-recount/) — **경계: 랭킹의 도메인 규칙(동점 정책·재집계·보상)은 거기, 여기는 함수가 무엇을 돌려주는가.**
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **순위 함수(ranking function)** — 값이 아니라 줄 선 자리로 결과를 내는 윈도우 함수.\
  예: `RANK() OVER (ORDER BY salary DESC)`. `OVER` 없이는 못 쓴다.
- **동률(tie)/피어(peer)** — 윈도우 `ORDER BY` 가 같다고 판정한 행들.\
  예: `ORDER BY salary DESC` 에서 `bob`(500)과 `fay`(500).
- **`ROW_NUMBER`** — 창 안에서 1부터 하나씩 매기는 함수. **동률에도 다른 번호**를 준다.\
  예: `bob`=1, `fay`=2. 누가 1인지는 `ORDER BY` 에 고유 키가 있어야 정해진다.
- **`RANK`** — 동률에 같은 등수를 주고 **그만큼 건너뛰는** 함수.\
  예: `1 1 3` — 1등이 둘이면 다음은 3등이다.
- **`DENSE_RANK`** — 동률에 같은 등수를 주고 **안 건너뛰는** 함수.\
  예: `1 1 2` — 1등이 둘이어도 다음은 2등이다.
- **`NTILE(n)`** — 창을 n 개 조로 나누고 조 번호를 주는 함수.\
  예: `NTILE(3)` 은 8행을 `3·3·2` 로 나눈다. 나머지는 앞 조에 붙는다.
- **비결정적(non-deterministic)** — 같은 질의·같은 데이터인데 답이 하나로 정해지지 않는 것.\
  예: 동률이 있고 고유 키가 없는 `ROW_NUMBER`. PG 와 MySQL 이 다른 번호를 줬다.
- **고유 키(unique key)** — 같은 값이 없는 열. `ORDER BY` 마지막에 두면 동률이 사라진다.\
  예: `emp.id` 는 기본키라 `ORDER BY salary DESC, id` 가 순서를 끝까지 정한다.
- **`PERCENT_RANK`·`CUME_DIST`** — 등수를 0~1 비율로 주는 함수.\
  예: 7행에서 1등의 `PERCENT_RANK` 는 0이다. 두 엔진 출력이 같았다(아래 「더 들어가면」).

## 더 들어가면

- **`PERCENT_RANK` 와 `CUME_DIST` 도 던져 봤다.** 두 엔진의 값이 소수점 끝자리까지 같았다.

```text
### SQL: SELECT name, salary, PERCENT_RANK() OVER (ORDER BY salary) AS pr, CUME_DIST() OVER (ORDER BY salary) AS cd
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary |         pr         |         cd
------+--------+--------------------+--------------------
 ann  |    300 |                  0 | 0.2857142857142857
 eve  |    300 |                  0 | 0.2857142857142857
 dan  |    400 | 0.3333333333333333 | 0.7142857142857143
 gus  |    400 | 0.3333333333333333 | 0.7142857142857143
 hui  |    400 | 0.3333333333333333 | 0.7142857142857143
 bob  |    500 | 0.8333333333333334 |                  1
 fay  |    500 | 0.8333333333333334 |                  1
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+--------------------+--------------------+
| name | salary | pr                 | cd                 |
+------+--------+--------------------+--------------------+
| ann  |    300 |                  0 | 0.2857142857142857 |
| eve  |    300 |                  0 | 0.2857142857142857 |
| dan  |    400 | 0.3333333333333333 | 0.7142857142857143 |
| gus  |    400 | 0.3333333333333333 | 0.7142857142857143 |
| hui  |    400 | 0.3333333333333333 | 0.7142857142857143 |
| bob  |    500 | 0.8333333333333334 |                  1 |
| fay  |    500 | 0.8333333333333334 |                  1 |
+------+--------+--------------------+--------------------+
```

  둘 다 **`RANK` 계열이라 동률에 같은 값**을 준다 — 그래서 `ROW_NUMBER` 같은 비결정성이 없다.\
  `cd`(누적 분포)는 「나 이하인 행의 비율」이라 `2/7 = 0.2857…` 이다. 손으로 유도한 값이 아니라 **출력에 있는 값**이다.
- **`ROW_NUMBER` 로 중복 제거**를 하는 관용구가 있다 — `ROW_NUMBER() OVER (PARTITION BY 키 ORDER BY ...) = 1`.\
  `DISTINCT` 와 다른 점은 **어느 행을 남길지 고를 수 있다**는 것이다. `DISTINCT` 자체는 [07번](../07-distinct-and-duplicate-removal/)이 정본이다.
- **순위를 미리 저장할 것인가** 는 SQL 문법이 아니라 설계 문제다. 조회마다 정렬하면 데이터가 클수록 비싸지고,\
  저장하면 갱신이 늦는다. 그 트레이드오프는 [`advanced/19-leaderboard-recount`](../../../../../domain-modeling/advanced/19-leaderboard-recount/)가 다룬다.\
  **이 주제에서 비용을 측정하지 않았다.**
