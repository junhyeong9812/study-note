# sql/31-윈도우 함수의 평가 시점과 `WINDOW` 절 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Window Functions (튜토리얼)](https://www.postgresql.org/docs/18/tutorial-window.html) · [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · Window Function Concepts and Syntax](https://dev.mysql.com/doc/refman/8.4/en/window-functions-usage.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `WINDOW` 절은 윈도우 함수와 같이 들어왔다(PG 8.4 · MySQL 8.0).\
> **이 주제에서 두 엔진의 결과가 갈린 자리는 `NULL` 위치 하나**다(4번) — 평가 시점 자체는 양쪽이 같다.\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/)(**이 주제의 뼈대**) · [26 윈도우 함수의 개념](../26-window-functions-vs-aggregates/).\
> **이 주제는 목록 README 의 31번 제목(「평가 시점과 `WINDOW` 절」)대로 `WINDOW` 절까지 다룬다**(8번).

## 한눈에 — 쉽게 말하면

**[01번](../01-logical-query-processing-order/)의 여덟 칸짜리 컨베이어에서, 윈도우 함수는 다섯 번째 칸에서 태어난다.**

```text
내가 적는 순서                    엔진이 일하는 순서
─────────────                    ─────────────
SELECT   ...                      1. FROM      표를 만든다
FROM     ...                      2. WHERE     행을 버린다        <- 여기선 아직 없다
WHERE    ...                      3. GROUP BY  행을 묶는다        <- 여기서도 아직 없다
GROUP BY ...                      4. HAVING    그룹을 버린다      <- 여기서도 아직 없다
HAVING   ...                      5. SELECT    열을 만든다        <- ★ 윈도우가 여기서 태어난다
WINDOW   ...                      6. DISTINCT  중복 행을 지운다
ORDER BY ...                      7. ORDER BY  줄을 세운다        <- 이미 있으니 쓸 수 있다
LIMIT    ...                      8. LIMIT     자른다
```

- **`WHERE` 에서 윈도우를 못 쓰는 이유** — 2번 칸이 5번 칸의 결과를 볼 수 없다. **아직 안 만들어졌다.**
- **`HAVING` 에서도 못 쓰는 이유** — 같다. 4번 칸도 5번보다 앞이다.
- **`ORDER BY` 에서는 쓸 수 있는 이유** — 7번 칸은 5번을 이미 지나왔다.
- **거르려면** — **한 겹 감싼다.** 안쪽 질의의 5번 칸이 끝나면, 바깥 질의의 1번 칸(`FROM`)에는 그냥 **열**로 들어온다.

★ **이것은 [01번](../01-logical-query-processing-order/)이 「별칭을 `WHERE` 에서 못 쓴다」고 설명한 것과 한 글자도 다르지 않은 구조다.**\
별칭도 윈도우도 **5번 칸에서 태어나고**, 그래서 앞 칸에서는 없고 뒤 칸에서는 있다.

| 비유 | 실체 | 결과 |
|---|---|---|
| 2번 창구가 5번 창구의 서류를 달라고 한다 | `WHERE ROW_NUMBER() OVER (...) = 1` | **에러** |
| 4번 창구가 그런다 | `HAVING ROW_NUMBER() OVER (...) = 1` | **에러** |
| 7번 창구가 그런다 | `ORDER BY ROW_NUMBER() OVER (...)` | **된다** |
| 서류를 다 처리한 뒤 새 창구에 낸다 | `SELECT ... FROM (SELECT ..., ROW_NUMBER() OVER (...) AS rn ...) t WHERE rn = 1` | **된다** |

> **논리적 처리 순서(logical query processing order)** — 엔진이 결과를 *정의*하는 순서. 실행 계획과는 다를 수 있다.\
> 예: 옵티마이저가 순서를 바꿔도 결과는 이 순서대로 계산한 것과 같아야 한다([01번](../01-logical-query-processing-order/)).

> **한 겹 감싸기(wrapping)** — 질의를 서브쿼리나 CTE 로 만들어 바깥에서 다시 고르는 것.\
> 예: `SELECT ... FROM (윈도우 질의) t WHERE rn = 1`. 안쪽의 계산 결과가 바깥에서는 **그냥 열**이다.

## 이 주제가 답하려는 질문

1. **윈도우 결과를 `WHERE` 로 왜 못 거르나?** — [01번](../01-logical-query-processing-order/)의 순서에서 `WHERE` 가 `SELECT` 보다 앞이기 때문이다.
2. **그럼 어떻게 거르나?** — 한 겹 감싼다. 서브쿼리든 CTE 든 같다.
3. **`WHERE` 가 먼저 돌면 창은 무엇을 보나?** — **남은 행만** 본다. 같은 `COUNT(*) OVER ()` 가 8과 5로 갈린다(3번).

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

`VALUES (…),(…)` 를 안 쓴 이유는 **두 엔진이 서로의 행 생성자 문법을 정확히 거부**하기 때문이다([10번](../10-from-clause-aliases-derived-tables/)).\
★ **이 CTE 자체가 이 주제의 소재이기도 하다** — 윈도우를 거르는 표준 우회가 바로 CTE 한 겹이다(5번).

```text
emp8
+----+------+---------+--------+    salary >= 400 인 행 : bob dan fay gus hui   (5행)
| id | name | dept_id | salary |    salary < 400 인 행  : ann eve               (2행)
+----+------+---------+--------+    salary 가 NULL 인 행 : cho                  (1행)
|  1 | ann  |      10 |    300 |
|  2 | bob  |      10 |    500 |    dept_id = 10   : 4행
|  3 | cho  |      20 |   NULL |    dept_id = 20   : 3행
|  4 | dan  |    NULL |    400 |    dept_id = NULL : 1행   -> GROUP BY 하면 3그룹
|  5 | eve  |      10 |    300 |
|  6 | fay  |      10 |    500 |
|  7 | gus  |      20 |    400 |
|  8 | hui  |      20 |    400 |
+----+------+---------+--------+
```

**왜 이 데이터가 이 주제에 맞는가.**

- **`WHERE salary >= 400` 이 8행을 5행으로 줄인다.** 그래서 `COUNT(*) OVER ()` 가 **8과 5로 눈에 보이게** 갈린다(3번).\
  조건이 아무 행도 안 거르면 「`WHERE` 가 먼저 돈다」를 보여 줄 수 없다.
- **`GROUP BY dept_id` 가 8행을 3행으로 접는다.** `COUNT(*) OVER ()` 가 **3** 이 되어\
  「윈도우의 입력은 접힌 뒤의 행」이 드러난다(6번).
- **동률이 있어 「1위 한 행」 뽑기가 의미를 갖는다** — `bob`·`fay` 가 둘 다 500 이다.\
  그래서 거르는 우회에서 **고유 키를 넣어야 하는 이유**까지 같이 보인다([29번](../29-ranking-functions/)).
- **`cho` 의 `salary` 가 `NULL` 이다** — 「상위 2명」을 뽑으면 PG 에서 **급여 미기록자가 1등**으로 딸려 온다(4번).\
  거르는 법을 배우면서 **거른 결과가 엔진마다 다를 수 있다**는 것까지 같이 본다.

## 동작 방식

---

### 1. ★ `WHERE`·`HAVING`·`GROUP BY` — 세 칸 모두 거부한다

**언제 쓰나** — 「순위 1위만 보고 싶다」를 처음 써 볼 때. 거의 모두가 여기서 한 번 막힌다.

```text
FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> LIMIT
         (2)       (3)        (4)       (5)
         ^^^^^^^^^^^^^^^^^^^^^^^^^      ^^^
         이 세 칸은 5번 칸보다 앞이다     윈도우가 태어나는 칸
         -> 아직 없는 것을 달라고 한 것
```

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn
         FROM emp8 WHERE ROW_NUMBER() OVER (ORDER BY salary DESC, id) <= 2;
--- PG 18.6 ---
ERROR:  window functions are not allowed in WHERE
LINE 7: ... (ORDER BY salary DESC, id) AS rn FROM emp8 WHERE ROW_NUMBER...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'row_number' in this context.'
```

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp8 GROUP BY dept_id HAVING ROW_NUMBER() OVER (ORDER BY dept_id) = 1;
--- PG 18.6 ---
ERROR:  window functions are not allowed in HAVING
LINE 7: ..., COUNT(*) AS c FROM emp8 GROUP BY dept_id HAVING ROW_NUMBER...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'row_number' in this context.'
```

```text
### SQL: SELECT name, salary FROM emp8 GROUP BY ROW_NUMBER() OVER (ORDER BY id);
--- PG 18.6 ---
ERROR:  window functions are not allowed in GROUP BY
LINE 7: ) SELECT name, salary FROM emp8 GROUP BY ROW_NUMBER() OVER (...
                                                 ^
--- MySQL 8.4.10 ---
ERROR 3593 (HY000) at line 1: You cannot use the window function 'row_number' in this context.'
```

그림 해설 — ★ **PG 는 어느 절인지 이름을 대 준다**(`in WHERE` / `in HAVING` / `in GROUP BY`).\
**MySQL 은 세 경우에 `ERROR 3593` 한 문장**을 쓴다 — `in this context` 가 어느 칸인지는 말해 주지 않는다.

두 문서가 규정을 같은 모양으로 적는다.\
PG: *"Window functions are permitted only in the `SELECT` list and the `ORDER BY` clause of the query. They are forbidden elsewhere, such as in `GROUP BY`, `HAVING` and `WHERE` clauses."* 그리고 이유까지 — *"This is because they logically execute after the processing of those clauses."*\
MySQL: *"Window functions are permitted only in the select list and `ORDER BY` clause."*

★ **에러 세 개가 전부 같은 한 문장으로 설명된다** — 「5번 칸의 결과를 2·3·4번 칸이 못 본다」.\
[01번](../01-logical-query-processing-order/)이 별칭으로 설명한 것과 **똑같은 구조**다.

비용 — 없다. 파싱·분석 단계에서 막힌다.

---

### 2. `ORDER BY` 에서는 **쓸 수 있다** — 7번 칸은 5번을 지나왔다

**언제 쓰나** — 계산한 순위대로 화면을 정렬할 때.

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

그림 해설 — **에러가 아니다.** 1번의 세 절과 달리 `ORDER BY` 는 통과한다.\
`ORDER BY` 안에 또 `OVER (ORDER BY ...)` 가 들어간 모양이 어색해 보이지만, **바깥은 출력 정렬, 안쪽은 창 안 정렬**이다([27번](../27-partition-by-and-window-order-by/) 4번).

★ **결과 행 순서가 두 엔진에서 다르다** — `cho`(salary `NULL`)가 PG 에서 맨 앞, MySQL 에서 맨 뒤다.\
`ROW_NUMBER` 가 매긴 번호가 이미 다르기 때문이다([29번](../29-ranking-functions/) 9번). **평가 시점이 아니라 `NULL` 위치의 문제다.**

비용 — 창을 만든 뒤 그 값으로 다시 정렬한다.

---

### 3. ★ `WHERE` 가 **먼저** 돈다 — 창은 살아남은 행만 본다

**언제 쓰나** — 「전체 대비 비율」을 구했는데 분모가 이상할 때. 원인이 거의 언제나 이것이다.

```text
emp8 8행
   |
   v  WHERE salary >= 400      <- 2번 칸. 여기서 3행이 버려진다
 5행 [bob dan fay gus hui]
   |
   v  SELECT ... COUNT(*) OVER ()   <- 5번 칸. 창은 이 5행이 전부다
 COUNT(*) OVER () = 5   ( 8 이 아니다 )
```

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

두 그림의 결론 — ★ **같은 `COUNT(*) OVER ()` 가 5와 8이다.** `WHERE` 한 줄이 창의 크기를 바꿨다.\
「전체」가 「**표 전체」가 아니라 「`WHERE` 를 통과한 전체**」라는 뜻이다.

★ **이게 실무에서 조용히 틀리는 자리다.** 「전체 대비 내 비중」을 구하면서 `WHERE` 로 기간을 잘라 놓으면,\
분모가 **그 기간의 합**이 된다 — 그게 의도였는지는 질의문이 말해 주지 않는다.\
표 전체가 분모여야 하면 **`WHERE` 를 바깥으로 빼서 한 겹 감싼다**(5번의 구조를 거꾸로 쓴다).

비용 — `WHERE` 가 먼저 돌아 창이 작아지므로 **대개 더 싸다.** 문제는 비용이 아니라 의미다.

---

### 4. 거르는 법 — **한 겹 감싼다**(서브쿼리든 CTE 든 같다)

**언제 쓰나** — 1번에서 막힌 뒤 곧바로.

```text
안쪽 질의                          바깥 질의
FROM -> WHERE -> ... -> SELECT     FROM (안쪽) -> WHERE -> ...
                        ^^^^^^          ^^^^^^^^^^^^^^^^
                    rn 이 여기서 태어나고   여기서는 rn 이 그냥 열이다
                                        -> WHERE 에서 쓸 수 있다
```

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

**CTE 로 써도 같다.**

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

그림 해설 — **두 형태가 완전히 같은 답을 낸다.** 「서브쿼리냐 CTE 냐」는 **읽기 편한 쪽**을 고르는 문제다.\
PG 문서가 이 우회를 한 문장으로 권한다: *"If there is a need to filter or group rows after the window calculations are performed, you can use a sub-select."*

★★ **그런데 두 엔진의 답이 다르다.** PG 는 `cho`(급여 `NULL`)와 `bob`, MySQL 은 `bob` 과 `fay` 다.\
**감싸는 것이 틀린 게 아니다** — 안쪽 `ROW_NUMBER` 가 이미 다른 번호를 매겼기 때문이다([29번](../29-ranking-functions/) 9번).\
「상위 2명」을 뽑았더니 **급여가 없는 사람이 1등**으로 딸려 왔다.

**고치면 양쪽이 같아진다.**

```sql
WITH ranked AS (
  SELECT name, salary, ROW_NUMBER() OVER (ORDER BY (salary IS NULL), salary DESC, id) AS rn
  FROM emp8
)
SELECT name, salary, rn FROM ranked WHERE rn <= 2;
```

★ **거르는 법을 배우는 자리에서 「거른 결과가 엔진마다 다르다」를 같이 본다.**\
우회가 되는지만 확인하고 넘어가면, 그 다음 사고는 **`ORDER BY` 쪽**에서 난다.

비용 — 파생 테이블 한 겹. **행을 두 번 훑는 것이 아니라 계획 상으로는 한 파이프라인**인 경우가 많지만,\
그 판단은 계획을 봐야 한다 — **이 주제에서 계획을 찍지 않았다**(계획 읽는 법은 [목록의 **58번 주제**](../58-explain-plan-tree/)).

---

### 5. `LIMIT` 은 8번 칸 — 감싸는 것과 **결과가 다르다**

**언제 쓰나** — 「상위 2명」을 `LIMIT 2` 로 쓸까 `WHERE rn <= 2` 로 쓸까 고를 때.

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

그림 해설 — **4번과 답이 같다.** 창을 나누지 않은 단순한 「상위 N」이면 `LIMIT` 로 충분하다.

★ **갈리는 것은 `PARTITION BY` 가 붙을 때다.** 「부서마다 상위 1명」은 `LIMIT` 로 못 쓴다 —\
`LIMIT` 은 **결과 전체에서** 잘라 내지 **그룹마다** 잘라 내지 않기 때문이다(8번 칸은 하나다).\
그때는 감싸는 수밖에 없다([29번](../29-ranking-functions/) 10번이 그 형태다).

★ **`LIMIT` 은 창을 줄여 주지 않는다.** 5번 칸이 8번 칸보다 앞이므로 **윈도우는 8행 전부에 대해 이미 계산됐다.**\
[01번](../01-logical-query-processing-order/)의 「`LIMIT` 을 붙이면 빨라질 거라 믿는다」와 같은 자리다.

비용 — `LIMIT` 은 앞 칸의 일을 줄이지 않는다.

---

### 6. 윈도우의 입력은 **접힌 뒤의 행**이다 — 집계와 같이 쓸 때

**언제 쓰나** — 「부서별 인원수」를 뽑고 그 옆에 「인원수 순위」를 붙일 때.

```text
FROM -> WHERE -> GROUP BY -> HAVING -> SELECT
                 ^^^^^^^^              ^^^^^^
                 8행 -> 3행             창은 이 3행이다
```

```text
### SQL: SELECT dept_id, COUNT(*) AS c, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rn
         FROM emp8 GROUP BY dept_id ORDER BY rn;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c | rn                +---------+---+----+
---------+---+----                | dept_id | c | rn |
      10 | 4 |  1                +---------+---+----+
      20 | 3 |  2                |      10 | 4 |  1 |
    NULL | 1 |  3                |      20 | 3 |  2 |
(3 rows)                         |    NULL | 1 |  3 |
                                 +---------+---+----+
```

그림 해설 — ★ **`OVER (ORDER BY COUNT(*) DESC)` 가 돈다.** 창 안의 `ORDER BY` 에 **집계 함수**를 쓴 것이다.\
집계는 3·4번 칸에서 끝났고 윈도우는 5번 칸이므로, **윈도우가 집계 결과를 입력으로 받는 것은 순서에 맞다.**

★ **반대는 안 된다** — 집계 안에 윈도우를 넣으면 에러다([26번](../26-window-functions-vs-aggregates/) 6번).

```text
집계 -> 윈도우 : 된다   (3·4번 칸 -> 5번 칸)
윈도우 -> 집계 : 에러   (5번 칸의 결과를 3번 칸이 못 받는다)
```

★ **`GROUP BY` 가 있으면 `COUNT(*) OVER ()` 가 그룹 수**가 되는 것도 같은 이유다([26번](../26-window-functions-vs-aggregates/) 4번).

비용 — 접힌 3행 위에서 도는 계산이라 입력이 이미 작다.

---

### 7. `DISTINCT` 는 **6번 칸** — 윈도우가 이미 계산된 뒤에 중복을 지운다

**언제 쓰나** — 윈도우로 뽑은 열을 `DISTINCT` 로 접으려 할 때.

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

그림 해설 — **돈다.** 8행에 대해 창을 계산한 뒤, 같은 `(dept_id, c)` 쌍을 하나로 접어 3행이 됐다.

★ **`GROUP BY` 로 쓴 것과 결과가 같지만 하는 일이 다르다.** 이쪽은 **8행을 만들고 5행을 버린다.**\
「접는 것이 목적」이면 `GROUP BY` 가 맞다([26번](../26-window-functions-vs-aggregates/) 12번).

MySQL 문서가 `DISTINCT` 의 자리를 명시한다: *"windowing execution occurs before `ORDER BY`, `LIMIT`, and `SELECT DISTINCT`."*\
★ **출력 순서가 두 엔진에서 다른 것**은 `ORDER BY` 를 안 적었기 때문이다 — **순서에 아무 보장이 없다**([08번](../08-order-by-null-position-stability/) 6번).

비용 — 창을 만든 뒤 중복 제거가 한 겹 더 든다.

---

### 8. `WINDOW` 절 — 창에 **이름**을 붙인다

**언제 쓰나** — 같은 `OVER (...)` 를 두 번 넘게 적을 때. 오타 하나가 다른 창을 만든다.

```text
SELECT ..., f1() OVER w, f2() OVER w, f3() OVER w
FROM ...
WINDOW w AS (PARTITION BY dept_id ORDER BY id)      <- 정의를 한 곳에 모은다
ORDER BY ...
```

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

그림 해설 — **세 함수가 한 창을 공유한다.** `cho` 의 `a` 가 `NULL` 인데 `c` 가 1인 것에 주목하라 —\
행은 하나 있고 값이 `NULL` 이라 평균을 낼 수 없다([21번](../21-aggregate-functions-count-forms/) 3번).

**이름 붙인 창을 상속해 고쳐 쓸 수 있다.**

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

그림 해설 — **`OVER (w1 ORDER BY id)` 는 「`w1` 에 `ORDER BY` 를 덧붙인 창**」이다.\
`WINDOW` 절 안에서도 상속이 된다 — `WINDOW w1 AS (PARTITION BY dept_id), w2 AS (w1 ORDER BY id)` 형태가 양쪽에서 돌았다.

★ **`WINDOW` 절은 문법 설탕이 아니라 오타 방지 장치다.** `OVER` 를 복사해 붙이면\
한 글자 차이로 **다른 창**이 되고, 결과는 **에러 없이** 달라진다.

★ **적는 자리가 정해져 있다** — `HAVING` 뒤, `ORDER BY` 앞이다. 이름은 창이지 열이 아니므로 `SELECT` 에서 못 쓴다.

비용 — 없다. 같은 창이면 엔진이 한 번만 계산한다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
SELECT   ... 윈도우함수() OVER (...) ...     -- ★ 여기서 태어난다
FROM     ...
WHERE    ...                                  -- 윈도우 금지
GROUP BY ...                                  -- 윈도우 금지
HAVING   ...                                  -- 윈도우 금지
WINDOW   w AS (...) [, w2 AS (w ...)]         -- 창에 이름을 붙인다
ORDER BY ... 윈도우함수() OVER (...) ...      -- 쓸 수 있다
LIMIT    ...
```

규칙 일곱.

1. **윈도우 함수는 `SELECT` 목록과 `ORDER BY` 에서만** 쓸 수 있다. 두 문서가 같은 문장으로 적는다.
2. **`WHERE`·`GROUP BY`·`HAVING` 은 전부 금지**다. 셋 다 5번 칸보다 앞이기 때문이다.
3. **거르려면 한 겹 감싼다.** 서브쿼리와 CTE 가 같은 답을 낸다.
4. **`WHERE` 가 먼저 돌아 창을 줄인다.** `COUNT(*) OVER ()` 가 8이 아니라 5가 될 수 있다.
5. **`GROUP BY` 가 접은 뒤가 창**이다. 그래서 창 안 `ORDER BY` 에 집계 함수를 쓸 수 있다.
6. **`LIMIT` 은 8번 칸**이라 창을 줄여 주지 않는다. 「부서마다 1명」은 `LIMIT` 로 못 쓴다.
7. **`WINDOW` 절은 `HAVING` 뒤 `ORDER BY` 앞**에 적고, 다른 이름 창을 상속할 수 있다.

실전 형태는 넷이다.

```sql
-- (1) 순위로 거르기 — CTE 한 겹
WITH ranked AS (SELECT ..., ROW_NUMBER() OVER (PARTITION BY k ORDER BY v DESC, id) AS rn FROM t)
SELECT * FROM ranked WHERE rn = 1;

-- (2) 순위로 정렬하기 — 감쌀 필요 없다
SELECT ... FROM t ORDER BY RANK() OVER (ORDER BY v DESC);

-- (3) 집계 위에 윈도우 얹기
SELECT k, COUNT(*) AS c, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rn FROM t GROUP BY k;

-- (4) 창 이름 붙이기
SELECT SUM(v) OVER w, AVG(v) OVER w FROM t WINDOW w AS (PARTITION BY k ORDER BY id);
```

## 어디서 틀리나

- **★ 윈도우 결과를 `WHERE` 로 거른다.**\
  두 엔진 다 에러다. PG 는 절 이름을 대 주고 MySQL 은 `ERROR 3593` 한 문장만 준다.
- **★ `HAVING` 이면 될 줄 안다.**\
  `HAVING` 도 5번 칸보다 앞이다. 집계는 되고 윈도우는 안 되는 이유가 이것이다.
- **★ 「전체 대비 비율」의 분모가 표 전체인 줄 안다.**\
  `WHERE` 가 먼저 돌아 **창이 줄어 있다**. 8이 아니라 5였다(3번).
- **`LIMIT` 을 붙이면 윈도우 계산이 줄 거라 믿는다.**\
  8번 칸이다. 이미 8행 전부에 대해 계산했다.
- **「부서마다 상위 1명」을 `LIMIT 1` 로 쓴다.**\
  `LIMIT` 은 결과 전체에서 자른다. 감싸야 한다.
- **감싸기만 하고 `ORDER BY` 를 끝까지 안 정한다.**\
  「상위 2명」이 두 엔진에서 다른 사람이 됐다(4번). `(열 IS NULL)` 과 고유 키를 더한다.
- **같은 `OVER (...)` 를 복사해 붙인다.**\
  한 글자 차이로 다른 창이 되고 **에러 없이** 값이 달라진다. `WINDOW` 절을 쓴다.
- **`WINDOW` 절을 `SELECT` 앞이나 `ORDER BY` 뒤에 적는다.**\
  자리가 정해져 있다 — `HAVING` 뒤, `ORDER BY` 앞이다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `WHERE`·`GROUP BY`·`HAVING` 에서 금지 | **정의** | 언어 — PG 문서가 절 이름까지 들어 적는다. 두 엔진 모두 거부 |
| `SELECT`·`ORDER BY` 에서 허용 | **정의** | 언어 — 두 문서가 같은 문장으로 적는다 |
| 평가 시점이 `HAVING` 뒤·`DISTINCT` 앞 | **정의** | 언어 — MySQL 문서가 *"windowing execution occurs before `ORDER BY`, `LIMIT`, and `SELECT DISTINCT`"* |
| `WHERE` 가 창을 줄인다 | **정의** | 언어 — 순서의 직접적 결과. 두 엔진 출력이 같았다(3번) |
| 서브쿼리·CTE 우회 | **정의** | 언어 — PG 문서가 *"you can use a sub-select"* 로 권한다 |
| 거부 **메시지** | 엔진 | PG 는 절 이름, MySQL 은 `ERROR 3593` 하나 |
| **감싼 뒤의 결과** | **방언 + 비결정** | `ORDER BY` 를 끝까지 안 정하면 엔진마다 다른 행이 남는다(4번) |
| `WINDOW` 절과 창 상속 | **정의** | 언어 — 두 엔진에서 같은 형태가 돌았다(8번) |
| 우회의 **비용** | 계획의 문제 | **이 주제에서 계획을 찍지 않았다** |

- **평가 시점 자체는 두 엔진이 완전히 같다.** 갈린 것은 **에러 메시지**와 **`NULL` 위치가 만든 결과 차이**뿐이다.
- 4번의 차이는 **이 주제의 규칙이 아니라 [08번](../08-order-by-null-position-stability/)의 규칙**이 드러난 것이다.

## 언제 쓰고 언제 안 쓰나

- **감싼다 — 윈도우 결과로 행을 걸러야 할 때.** 선택의 여지가 없다.
- **CTE 를 고른다 — 이름이 있는 편이 읽히는 질의.** 단계가 둘 이상이면 거의 언제나 이쪽이다([32 CTE(WITH)](../32-cte-with-clause/)).
- **서브쿼리를 고른다 — 한 번 쓰고 마는 짧은 질의.**
- **안 감싼다 — 정렬만 하면 될 때.** `ORDER BY` 에서는 그냥 쓸 수 있다.
- **안 감싼다 — 단순 「상위 N」.** `ORDER BY` + `LIMIT` 이 더 짧다. **단 `PARTITION BY` 가 붙으면 못 쓴다.**
- **`WINDOW` 절을 쓴다 — 같은 창을 두 번 넘게 적을 때.** 오타로 다른 창이 되는 사고를 막는다.

## 핵심 문장

- **윈도우 함수는 [01번](../01-logical-query-processing-order/) 순서의 5번 칸(`SELECT`)에서 태어난다.** 그래서 2·3·4번 칸에서는 없고 7번 칸에서는 있다.
- ★ **`WHERE`·`GROUP BY`·`HAVING` 셋 다 에러**다 — PG 는 절 이름을 대 주고 MySQL 은 `ERROR 3593` 하나로 묶는다.
- **`ORDER BY` 에서는 쓸 수 있다.** 7번 칸은 5번을 이미 지나왔다.
- ★ **`WHERE` 가 먼저 돌아 창을 줄인다** — 같은 `COUNT(*) OVER ()` 가 **8과 5**였다.\
  「전체 대비 비율」의 분모가 표 전체가 아닐 수 있다.
- **거르려면 한 겹 감싼다.** 서브쿼리와 CTE 가 같은 답을 낸다.
- ★ **감싸는 법만 배우고 끝내면 안 된다** — 「상위 2명」이 PG 에서 `cho`(급여 `NULL`)·`bob`, MySQL 에서 `bob`·`fay` 였다.
- **`LIMIT` 은 8번 칸**이라 창을 줄여 주지 않고, **「그룹마다 1명」은 `LIMIT` 로 못 쓴다.**
- **`GROUP BY` 가 접은 뒤가 창**이라 창 안 `ORDER BY` 에 `COUNT(*)` 를 쓸 수 있다. 반대(집계 안의 윈도우)는 에러다.
- **`WINDOW` 절은 `HAVING` 뒤 `ORDER BY` 앞**에 적고, 다른 창을 상속할 수 있다.

## 관련 자료

- [PostgreSQL 18 · Window Functions (튜토리얼)](https://www.postgresql.org/docs/18/tutorial-window.html) — *"They are forbidden elsewhere …"* 와 *"you can use a sub-select"*, `WINDOW` 절 설명이 한 페이지에 있다.
- [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) — `WINDOW` 절의 문법 자리.
- [MySQL 8.4 · Window Function Concepts and Syntax](https://dev.mysql.com/doc/refman/8.4/en/window-functions-usage.html) — *"windowing execution occurs before `ORDER BY`, `LIMIT`, and `SELECT DISTINCT`"* 문장.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 여덟 칸의 순서 자체와 별칭 규칙까지, 여기는 그 순서에서 윈도우가 어느 칸인가부터.**\
  01번의 「어디서 틀리나」가 이 에러를 한 줄로 예고하고 있다.
- [26 윈도우 함수의 개념](../26-window-functions-vs-aggregates/) — **경계: 그쪽은 「접지 않는다」와 중첩 규칙까지, 여기는 그 계산이 언제 일어나고 그래서 어디서 못 쓰나부터.**
- [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/) — **경계: 그쪽은 행과 그룹을 거르는 두 칸의 차이까지, 여기는 그 두 칸이 **둘 다** 윈도우를 못 보는 것부터.**
- [29 순위 함수](../29-ranking-functions/) — **경계: 그쪽은 순위 값을 만드는 데까지, 여기는 그 값으로 거르는 것.**
- [08 ORDER BY — 정렬 키·NULL 위치·동률](../08-order-by-null-position-stability/) — 4번에서 두 엔진이 다른 사람을 뽑은 이유.
- [10 FROM 절 — 테이블 별칭·파생 테이블·VALUES 리스트](../10-from-clause-aliases-derived-tables/) — 감쌀 때 쓰는 파생 테이블의 별칭 규칙.
- [SQL 주제 목록](../README.md) — CTE 자체는 [목록의 **32번 주제**](../32-cte-with-clause/)다.

## 용어 풀이

- **논리적 처리 순서** — 엔진이 결과를 정의하는 여덟 칸의 순서. 실행 계획과는 다를 수 있다.\
  예: `WHERE` 는 2번, `SELECT` 는 5번, `ORDER BY` 는 7번 칸이다.
- **평가 시점(evaluation time)** — 어느 칸에서 그 값이 만들어지는가.\
  예: 윈도우 함수는 5번 칸이라 2번 칸에서는 아직 없다.
- **한 겹 감싸기(wrapping)** — 질의를 서브쿼리나 CTE 로 만들어 바깥에서 다시 고르는 것.\
  예: `SELECT * FROM (윈도우 질의) t WHERE rn = 1`.
- **파생 테이블(derived table)** — `FROM` 절에 놓인 서브쿼리.\
  예: `FROM (SELECT ... ) t`. **MySQL 은 별칭 `t` 가 필수**다([10번](../10-from-clause-aliases-derived-tables/)).
- **CTE(`WITH` 절)** — 질의 앞에 이름을 붙여 정의하는 임시 결과.\
  예: `WITH ranked AS (...) SELECT ... FROM ranked`. 서브쿼리와 같은 답을 낸다.
- **`WINDOW` 절** — 창에 이름을 붙이는 절. `HAVING` 뒤, `ORDER BY` 앞에 적는다.\
  예: `WINDOW w AS (PARTITION BY dept_id ORDER BY id)` 를 정의하고 `OVER w` 로 쓴다.
- **창 상속** — 이름 붙인 창에 절을 덧붙여 새 창을 만드는 것.\
  예: `OVER (w1 ORDER BY id)` 는 `w1` 의 `PARTITION BY` 에 순서를 더한 창이다.
- **`ERROR 3593`** — MySQL 이 「윈도우 함수를 쓸 수 없는 자리」에 쓰는 한 덩어리 메시지.\
  예: `WHERE`·`HAVING`·`GROUP BY`·중첩이 전부 이 번호다. 어느 칸인지는 말해 주지 않는다.

## 더 들어가면

- **왜 표준이 윈도우를 `SELECT` 칸에 뒀나.** 윈도우는 「**결과 집합이 확정된 뒤**」에만 계산할 수 있다.\
  「내 등수」는 **누가 남아 있는지 다 정해져야** 정해지기 때문이다. `WHERE` 가 아직 돌고 있는 중에는 창이 확정되지 않는다.\
  (이 설명은 **문서에 적힌 근거가 아니라 위 실측과 순서에서 끌어낸 추론**이다.)
- **그래서 「윈도우로 거르고 다시 윈도우」가 필요하면 겹을 더 쌓는다.**\
  `WITH a AS (...윈도우...), b AS (SELECT ... FROM a WHERE ... 윈도우 ...) SELECT ...` 처럼.\
  **이 형태는 던져 보지 않았다** — 겹을 쌓는 규칙 자체는 [목록의 **32번 주제**](../32-cte-with-clause/)(CTE)가 정본이다.
- **옵티마이저는 이 순서를 그대로 실행하지 않아도 된다.** 결과만 같으면 된다 —\
  예컨대 `WHERE rn = 1` 을 안쪽으로 밀어 넣는 최적화가 가능한지는 **엔진과 버전에 달렸고,\
  이 주제에서 계획을 찍지 않았다.** 계획을 읽는 법은 [목록의 **58번 주제**](../58-explain-plan-tree/), 추정과 실측의 차이는 [**60번 주제**](../60-explain-analyze-estimates-vs-actuals/)다.\
  ★ **계획은 관찰이지 보장이 아니다** — 통계가 흔들리기만 해도 바뀐다.
- ★ **`QUALIFY` 라는 절이 있는 방언이 있다**(윈도우 결과를 **감싸지 않고** 바로 거르는 전용 절).\
  「두 엔진에 없다」고 단정하기 전에 **던져 봤고, 예상과 달랐다.**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn FROM emp8 QUALIFY rn <= 2;
--- PG 18.6 ---
ERROR:  syntax error at or near "rn"
LINE 7: ... (ORDER BY salary DESC, id) AS rn FROM emp8 QUALIFY rn <= 2;
                                                               ^
--- MySQL 8.4.10 ---
ERROR 6037 (HY000) at line 1: 'QUALIFY clause' can be used only if the hypergraph optimizer is enabled.
```

  ★★ **MySQL 8.4.10 의 파서는 `QUALIFY` 를 알아본다.** 「문법이 없다」가 아니라 **옵티마이저를 켜라**고 한다.\
  켜 보면 한 겹 더 막힌다.

```text
### SQL: SET SESSION optimizer_switch='hypergraph_optimizer=on'; (위 질의)
--- MySQL 8.4.10 ---
ERROR 3999 (42000) at line 1: The hypergraph optimizer does not yet support 'use in non-debug builds'
```

  **PG 쪽 에러는 뜻이 다르다.** PG 는 `QUALIFY` 를 **테이블 별칭으로 읽고** 그다음 `rn` 에서 막힌 것이다 — 확인해 보면 이렇다.

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

  `QUALIFY` 하나만 붙였을 때는 안 막히고 **그다음 낱말에서** 막힌다 — **`QUALIFY` 가 그냥 이름으로 먹혔다**는 뜻이다.\
  ★ **결론: 두 엔진 모두 지금은 못 쓴다.** 다만 **이유가 다르다** — PG 는 **문법에 없고**, MySQL 은 **문법에 있는데 실행 경로가 없다**.\
  MySQL 쪽은 *"does not **yet** support"* 이므로 **버전이 오르면 다시 찍을 자리**다.
