# sql/07-DISTINCT 와 중복 제거 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> 문서 근거는 [PG 18 SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 DISTINCT Optimization](https://dev.mysql.com/doc/refman/8.4/en/distinct-optimization.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `SELECT DISTINCT dept_id` 와 `SELECT DISTINCT dept_id, salary` 의 행 수

**출력**

```text
(A)
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      20                         |    NULL |
    NULL                         |      10 |
(3 rows)                         |      20 |
                                 +---------+

(B)
### SQL: SELECT DISTINCT dept_id, salary FROM emp ORDER BY dept_id, salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | salary                +---------+--------+
---------+--------               | dept_id | salary |
      10 |    300                +---------+--------+
      10 |    500                |    NULL |    400 |
      20 |   NULL                |      10 |    300 |
    NULL |    400                |      10 |    500 |
(4 rows)                         |      20 |   NULL |
                                 +---------+--------+
```

**(A)는 3행, (B)는 4행이다.**

**왜 그런가** — `DISTINCT` 의 기준은 **출력 행 전체**다. 열이 늘면 「같다」의 조건이 까다로워진다.

```text
(A) 기준 = (dept_id)             (B) 기준 = (dept_id, salary)
  (10)   ┐                         (10, 300)
  (10)   ┘ 같다 -> 하나            (10, 500)   <- salary 가 달라서 안 접힌다
  (20)                             (20, NULL)
  (NULL)                           (NULL, 400)
   -> 3행                           -> 4행
```

**「`DISTINCT` 를 붙였는데 중복이 그대로다」의 원인 1위가 이것이다.** 열을 하나 더 뽑고 있었던 것이다.\
극단적으로 `SELECT DISTINCT *` 에서는 기본키 때문에 **한 행도 안 접힌다.**

```text
### SQL: SELECT DISTINCT * FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary    +----+------+---------+--------+
----+------+---------+--------   | id | name | dept_id | salary |
  1 | ann  |      10 |    300    +----+------+---------+--------+
  2 | bob  |      10 |    500    |  1 | ann  |      10 |    300 |
  3 | cho  |      20 |   NULL    |  2 | bob  |      10 |    500 |
  4 | dan  |    NULL |    400    |  3 | cho  |      20 |   NULL |
(4 rows)                         |  4 | dan  |    NULL |    400 |
                                 +----+------+---------+--------+
```

---

### 2. `DISTINCT(dept_id), salary` 는 어느 쪽과 같은가

**(B)와 같다. 괄호는 아무 일도 하지 않는다.**

```text
### SQL: SELECT DISTINCT(dept_id), salary FROM emp ORDER BY dept_id, salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | salary                +---------+--------+
---------+--------               | dept_id | salary |
      10 |    300                +---------+--------+
      10 |    500                |    NULL |    400 |
      20 |   NULL                |      10 |    300 |
    NULL |    400                |      10 |    500 |
(4 rows)                         |      20 |   NULL |
                                 +---------+--------+
```

**1번의 (B)와 한 글자도 다르지 않다.**

**왜 그런가** — `DISTINCT` 는 **함수가 아니라 절**이다. `SELECT` 바로 뒤에 한 번 오고, 언제나 목록 전체에 걸린다.

```text
쓴 사람의 머릿속                     파서가 읽은 것
SELECT DISTINCT(dept_id), salary     SELECT DISTINCT   (dept_id), salary
       └──── 함수 호출? ────┘               └ 절 ┘     └ 그냥 괄호 ┘
                                                        (dept_id) = dept_id
```

**에러가 안 나는 것이 문제다.** 문법적으로 완전히 정상이라 리뷰에서도 안 걸린다.\
「`DISTINCT` 를 분명히 걸었는데 왜 중복이지」로 나타나고, 원인을 찾는 데 오래 걸린다.

---

### 3. `NULL` 이 한 행으로 접히는 이유

**`DISTINCT` 는 「같은가」가 아니라 「구별할 수 있는가」를 기준으로 쓰기 때문이다.**

```text
비교(=)         "이 두 값이 같은 값인가?"        모르면 모른다고 해야 한다  -> UNKNOWN
묶기(DISTINCT)  "이 두 행을 구별할 수 있는가?"   둘 다 모르면 구별 불가     -> 한 행
```

```text
### SQL: SELECT DISTINCT salary FROM emp ORDER BY salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
    300                          +--------+
    400                          |   NULL |
    500                          |    300 |
   NULL   <- 한 행               |    400 |
(4 rows)                         |    500 |
                                 +--------+
```

> **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 묶기 기준.\
> 예: `NULL` 둘은 같다고 말할 수 없지만 구별할 수도 없으므로 한 행이 된다.

**이 기준을 쓰는 것이 `DISTINCT` 혼자가 아니다.**

| 연산 | 쓰는 기준 | `NULL` 둘을 |
|---|---|---|
| `=` · `<>` | 같은가 | **구별하지 못해 `UNKNOWN`** |
| `DISTINCT` · `GROUP BY` · `UNION` | 구별할 수 있는가 | **하나로 접는다** |
| `IS NOT DISTINCT FROM`(PG) · `<=>`(MySQL) | 구별할 수 있는가 | **같다고 판정** |

마지막 줄이 재미있다 — PG 의 `IS NOT DISTINCT FROM` 은 이름 그대로 **묶기 기준을 비교 연산자로 꺼내 쓴 것**이다([05번](../05-null-comparison-is-distinct-from/)).

**외울 때는 둘로 나눠서** — **비교는 `UNKNOWN`, 묶기는 같은 것 취급.**

---

### 4. `COUNT(*)`·`COUNT(dept_id)`·`COUNT(DISTINCT dept_id)` 세 값

**출력**

```text
### SQL: SELECT COUNT(*) AS c_star, COUNT(dept_id) AS c_col, COUNT(DISTINCT dept_id) AS c_dist FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c_star | c_col | c_dist         +--------+-------+--------+
--------+-------+--------        | c_star | c_col | c_dist |
      4 |     3 |      2         +--------+-------+--------+
(1 row)                          |      4 |     3 |      2 |
                                 +--------+-------+--------+
```

**4 · 3 · 2 다. 그리고 `SELECT DISTINCT dept_id` 의 행 수(3)와 다른 것은 `COUNT(DISTINCT dept_id)`(2) 이다.**

**왜 그런가** — 세는 것과 접는 것이 `NULL` 을 다르게 다룬다.

```text
dept_id = [10, 10, 20, NULL]

COUNT(*)                 -> 4    행을 센다. 값은 안 본다
COUNT(dept_id)           -> 3    NULL 아닌 값을 센다
COUNT(DISTINCT dept_id)  -> 2    NULL 아닌 값을 접어서 센다  -> {10, 20}
SELECT DISTINCT dept_id  -> 3행  접기만 한다. NULL 도 한 행   -> {10, 20, NULL}
                            ^^^
                        여기서 1 차이가 난다
```

`COUNT` 가 **집계 함수**이고 집계는 `NULL` 을 건너뛰기 때문이다([04번](../04-null-three-valued-logic/)).\
`DISTINCT` 는 **`SELECT` 절의 지시**라 `NULL` 을 버리지 않고 접기만 한다.

**실무 함의** — 「고유 부서 수」를 `COUNT(DISTINCT dept_id)` 로 뽑으면 **소속 없는 사원의 존재가 지표에서 사라진다.**\
「소속 미정」을 한 범주로 세야 한다면 `COUNT(DISTINCT COALESCE(dept_id, -1))` 처럼 명시해야 한다.

다른 집계도 `DISTINCT` 를 받는다.

```text
### SQL: SELECT SUM(DISTINCT dept_id) AS sd, SUM(dept_id) AS s, COUNT(DISTINCT dept_id) AS cd FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 sd | s  | cd                    +------+------+----+
----+----+----                   | sd   | s    | cd |
 30 | 40 |  2                    +------+------+----+
(1 row)                          |   30 |   40 |  2 |
                                 +------+------+----+
```

`10 + 20 = 30` 과 `10 + 10 + 20 = 40` 이다.

---

### 5. `COUNT(DISTINCT a, b)` 와 `COUNT(DISTINCT (a, b))`

**출력**

```text
(A)
### SQL: SELECT COUNT(DISTINCT dept_id, salary) AS c FROM emp;
--- PG 18.6 ---
ERROR:  function count(integer, integer) does not exist
LINE 1: SELECT COUNT(DISTINCT dept_id, salary) AS c FROM emp;
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+---+
| c |
+---+
| 2 |
+---+

(B)
### SQL: SELECT COUNT(DISTINCT (dept_id, salary)) AS c FROM emp;
--- PG 18.6 ---
 c
---
 4
(1 row)
--- MySQL 8.4.10 ---
ERROR 1241 (21000) at line 1: Operand should contain 1 column(s)
```

**문법이 서로 배타적이고, 도는 쪽의 답도 2와 4로 다르다.**

**왜 숫자가 다른가** — 네 행은 `(10,300) (10,500) (20,NULL) (NULL,400)` 이다.

```text
MySQL  COUNT(DISTINCT a, b) = 2
   인자 중 하나라도 NULL 인 행은 세지 않는다
   -> (20,NULL) 과 (NULL,400) 탈락
   -> (10,300), (10,500) 두 조합

PG     COUNT(DISTINCT (a, b)) = 4
   (a,b) 를 "행 값" 하나로 본다. 행 자체는 NULL 이 아니다
   -> 네 조합이 전부 서로 다르다
```

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `COUNT(DISTINCT a, b)` | **문법 없음** — `function count(integer, integer) does not exist` | `2` |
| `COUNT(DISTINCT (a, b))` | `4` | **`ERROR 1241 Operand should contain 1 column(s)`** |

**같은 의도를 적었는데 지표가 2배 차이 난다.** 그리고 이식하는 쪽은 **에러를 보고 문법만 바꾸다가** 숫자가 바뀐 것을 놓친다.

양쪽에서 같게 하려면 **접은 뒤에 센다.**

```text
### SQL: SELECT COUNT(*) AS c FROM (SELECT DISTINCT dept_id, salary FROM emp) x;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c                               +---+
---                              | c |
 4                               +---+
(1 row)                          | 4 |
                                 +---+
```

이 형태는 `SELECT DISTINCT` 의 규칙(=`NULL` 도 한 행)을 따르므로 **양쪽에서 4** 다.\
「`NULL` 이 든 조합을 셀 것인가」를 **질의문이 아니라 지표 정의에서** 먼저 정해야 한다는 신호다.

---

### 6. `SELECT DISTINCT dept_id ... ORDER BY salary` 가 증명하는 순서

**6번 칸 `DISTINCT` 가 7번 칸 `ORDER BY` 보다 앞이라는 것**을 증명한다.

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
--- PG 18.6 ---
ERROR:  for SELECT DISTINCT, ORDER BY expressions must appear in select list
LINE 1: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
                                                  ^
--- MySQL 8.4.10 ---
ERROR 3065 (HY000) at line 1: Expression #1 of ORDER BY clause is not in SELECT list, references column 'study.emp.salary' which is not in SELECT list; this is incompatible with DISTINCT
```

**왜 그런가** — 접고 난 뒤에는 그 행의 `salary` 를 정할 방법이 없다.

```text
5 SELECT   -> 출력 열은 dept_id 하나. salary 는 여기서 버려진다
6 DISTINCT -> ann(300) 과 bob(500) 이 (10) 한 행으로 접힌다
7 ORDER BY -> 이 한 행의 salary 는 300 인가 500 인가?   <- 정할 수 없다
```

**`DISTINCT` 가 없으면 같은 질의가 통과한다.** `ORDER BY` 는 원래 `SELECT` 목록 밖의 열도 쓸 수 있다([01번](../01-logical-query-processing-order/)).\
두 규칙이 충돌하지 않는 이유가 바로 이 순서다 — **접힌 뒤에는 그 열이 없다.**

MySQL 의 에러 문구가 친절하다 — `this is incompatible with DISTINCT`. **`DISTINCT` 때문**이라고 명시한다.

---

### 7. `ORDER BY dept_id * 1` 을 받아 주는 엔진

**MySQL 8.4.10 만 받아 준다.**

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY dept_id * 1;
--- PG 18.6 ---
ERROR:  for SELECT DISTINCT, ORDER BY expressions must appear in select list
LINE 1: SELECT DISTINCT dept_id FROM emp ORDER BY dept_id * 1;
                                                  ^
--- MySQL 8.4.10 ---
+---------+
| dept_id |
+---------+
|    NULL |
|      10 |
|      20 |
+---------+
```

**왜 그런가** — 「목록에 있어야 한다」를 읽는 방식이 다르다.

```text
PG 의 기준                             MySQL 의 기준
"ORDER BY 의 식 자체가 목록에 있나"     "그 식이 목록의 열들로만 만들어졌나"
  dept_id * 1 은 목록에 없다            dept_id * 1 은 dept_id 로 만들어졌다
  -> 에러                               -> 통과
```

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `ORDER BY <목록에 없는 열>` | 에러 | 에러 |
| `ORDER BY <목록 열로 만든 식>` | **에러** | **통과** |

**논리적으로는 MySQL 쪽도 안전하다** — `dept_id` 가 같으면 `dept_id * 1` 도 같으므로 접힌 행에 모호함이 없다.\
다만 **PG 로 옮기면 깨진다.** 반대 방향은 안 깨진다.

해결은 그 식을 `SELECT` 목록에 넣는 것이다 — 양쪽에서 돈다. 별칭으로 정렬하는 것도 양쪽 다 된다.

```text
### SQL: SELECT DISTINCT salary * 12 AS annual FROM emp ORDER BY annual;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual                          +--------+
--------                         | annual |
   3600                          +--------+
   4800                          |   NULL |
   6000                          |   3600 |
   NULL                          |   4800 |
(4 rows)                         |   6000 |
                                 +--------+
```

---

### 8. `DISTINCT` 와 `GROUP BY` — 계획이 다른가

**두 엔진 모두 계획이 같다. 고르는 기준은 성능이 아니라 의도다.**

```text
--- PG 18.6 ---
### SQL: EXPLAIN (COSTS OFF) SELECT DISTINCT dept_id FROM emp;
 HashAggregate
   Group Key: dept_id
   ->  Seq Scan on emp

### SQL: EXPLAIN (COSTS OFF) SELECT dept_id FROM emp GROUP BY dept_id;
 HashAggregate
   Group Key: dept_id
   ->  Seq Scan on emp
```

```text
--- MySQL 8.4.10 (EXPLAIN FORMAT=TREE) ---
DISTINCT 판                                       GROUP BY 판
-> Table scan on <temporary>  (cost=1.76..3.81)   -> Table scan on <temporary>  (cost=1.76..3.81)
    -> Temporary table with deduplication          -> Temporary table with deduplication
        -> Table scan on emp                           -> Table scan on emp
```

**네 계획이 두 쌍 모두 한 글자도 같다.** 「`DISTINCT` 가 느리다」는 이 형태에서는 근거가 없다.

**그래서 무엇으로 고르나 — 할 수 있는 일과 읽히는 의도다.**

| | `SELECT DISTINCT` | `GROUP BY` |
|---|---|---|
| 중복 제거 | ✓ | ✓ |
| 집계값(`COUNT`·`SUM`) | ✗ | ✓ |
| 그룹 조건(`HAVING`) | ✗ | ✓ |
| 읽는 사람이 받는 신호 | 「중복만 지운다」 | 「그룹 단위로 본다」 |

집계가 없으면 `DISTINCT`, 있으면 `GROUP BY` — **의도를 드러내는 쪽**을 고른다.

> ⚠️ **이 계획은 4행짜리 표의 결과다.** 큰 표·인덱스가 있는 열에서는 정렬 기반 `Unique` 나 인덱스 스캔이 뽑힐 수 있다.\
> 「계획이 같다」는 **이 조건에서의 관찰**이지 보장이 아니다. 계획 읽기의 정본은 [목록의 **58번 주제**](../58-explain-plan-tree/)다.

---

### 9. `DISTINCT ON (dept_id)` 의 세 행과 `dept_id = 20` 의 대표

**출력**

```text
### SQL: SELECT DISTINCT ON (dept_id) dept_id, id, name, salary FROM emp ORDER BY dept_id, salary DESC;
--- PG 18.6 ---
 dept_id | id | name | salary
---------+----+------+--------
      10 |  2 | bob  |    500
      20 |  3 | cho  |   NULL
    NULL |  4 | dan  |    400
(3 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'ON (dept_id) dept_id, id, name, salary FROM emp ORDER BY dept_id, salary DESC' at line 1
```

**세 행은 `bob`(10) · `cho`(20) · `dan`(NULL) 이다.**

**왜 그런가** — `DISTINCT ON` 은 **정렬한 뒤 키가 바뀔 때마다 첫 행만** 남긴다.

```text
ORDER BY dept_id, salary DESC 로 줄을 세운다 (PG 기준)

 dept_id | salary | 남기나
---------+--------+--------
      10 |    500 | ★ 첫 행 -> bob
      10 |    300 |   버림
      20 |   NULL | ★ 첫 행 -> cho      <- PG 는 DESC 에서 NULL 이 맨 앞이다
    NULL |    400 | ★ 첫 행 -> dan
```

**`dept_id = 20` 의 대표가 `cho` 인 이유는 「급여가 가장 높아서」가 아니다.**\
`dev` 부서에는 `cho` 한 명뿐이라 어차피 대표지만, **더 중요한 것은 PG 가 `DESC` 에서 `NULL` 을 큰 값으로 본다**는 점이다([08번](../08-order-by-null-position-stability/)).

```text
만약 dev 에 salary 400 인 사원이 한 명 더 있었다면
   ORDER BY salary DESC  ->  NULL(cho) 이 먼저 온다
   -> 대표가 "급여를 모르는 사람" 이 된다     <- 거의 확실히 의도가 아니다
```

처방은 `NULLS LAST` 를 명시하는 것이다 — `ORDER BY dept_id, salary DESC NULLS LAST`.\
**`DISTINCT ON` 의 정확성은 `ORDER BY` 의 `NULL` 처리에 통째로 걸려 있다.**

---

### 10. MySQL 에서 같은 결과를 얻는 방법

**윈도우 함수 `ROW_NUMBER()` 로 순위를 매기고, 한 겹 감싼 뒤 `WHERE rn = 1` 로 거른다.**

```text
### SQL: SELECT dept_id, id, name, salary FROM (SELECT e.*, ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rn FROM emp e) t
         WHERE rn = 1 ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | id | name | salary    +---------+----+------+--------+
---------+----+------+--------   | dept_id | id | name | salary |
      10 |  2 | bob  |    500    +---------+----+------+--------+
      20 |  3 | cho  |   NULL    |    NULL |  4 | dan  |    400 |
    NULL |  4 | dan  |    400    |      10 |  2 | bob  |    500 |
(3 rows)                         |      20 |  3 | cho  |   NULL |
                                 +---------+----+------+--------+
```

**같은 세 행이 나온다.** 줄 순서만 `NULL` 정렬 차이로 다르다.

**왜 한 겹 감싸야 하나** — 윈도우 함수는 **5번 칸(`SELECT`)에서 계산**되는데 `WHERE` 는 2번 칸이다.

```text
안쪽 질의                          바깥 질의
1 FROM     emp                     1 FROM   (안쪽을 통째로 끝낸다)  <- rn 이 이미 있는 열이 된다
...                                2 WHERE  rn = 1
5 SELECT   e.*, ROW_NUMBER() ...
           ^^^^^^^^^^^^^^^^^^
           rn 이 여기서 태어난다
```

`WHERE ROW_NUMBER() OVER (...) = 1` 을 직접 쓰면 두 엔진 다 거부한다([01번](../01-logical-query-processing-order/)에서 확인한 것).

**두 방식의 대가**

| | `DISTINCT ON` (PG) | 윈도우 함수 (양쪽) |
|---|---|---|
| 이식성 | **PG 전용** | 양쪽에서 돈다 |
| 문장 길이 | 짧다 | 한 겹 더 |
| 「상위 2개」로 확장 | **불가** | `WHERE rn <= 2` 한 글자 |
| 동률 처리 | 첫 행 하나 | `RANK`/`DENSE_RANK` 로 고를 수 있다 |

윈도우 함수 자체의 정본은 목록의 [**26**](../26-window-functions-vs-aggregates/)~[**29**](../29-ranking-functions/)번 주제다.

---

### 11. `DISTINCT ON (dept_id) ... ORDER BY id` 가 거부되는 이유

**`DISTINCT ON` 의 식이 `ORDER BY` 의 맨 앞과 일치해야 하는데 다르기 때문이다.**

```text
### SQL: SELECT DISTINCT ON (dept_id) dept_id, id FROM emp ORDER BY id;
--- PG 18.6 ---
ERROR:  SELECT DISTINCT ON expressions must match initial ORDER BY expressions
LINE 1: SELECT DISTINCT ON (dept_id) dept_id, id FROM emp ORDER BY i...
                            ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'ON (dept_id) dept_id, id FROM emp ORDER BY id'
```

**왜 그런가** — `DISTINCT ON` 은 **정렬된 흐름을 훑으며 키가 바뀔 때 첫 행을 집는** 방식이다.

```text
정렬이 dept_id 로 시작하지 않으면
  id 순: (1,10) (2,10) (3,20) (4,NULL)
  -> dept_id 가 10, 10, 20, NULL 로 흩어져 있을 수도 있다
  -> "키가 바뀌는 지점" 을 한 번 훑어서 알 수 없다
```

그래서 **`ORDER BY` 의 맨 앞이 `DISTINCT ON` 의 식과 같아야 한다**는 제약이 붙는다.\
그 뒤에 오는 항목들이 「**그룹 안에서 누구를 남길지**」를 정한다.

```sql
SELECT DISTINCT ON (dept_id) dept_id, id, name, salary
FROM emp
ORDER BY dept_id,        -- 필수: DISTINCT ON 과 같아야 한다
         salary DESC;    -- 선택: 누구를 남길지
```

(MySQL 의 에러는 `DISTINCT ON` 문법 자체가 없어서 나는 `ERROR 1064` 다 — 9번과 같은 이유다.)

---

### 12. 조인 결과에 중복이 보일 때 먼저 의심할 것

**조인 팬아웃이다.** `DISTINCT` 는 증상을 가릴 뿐 원인을 안 고친다.

```text
증상만 덮는다                        원인을 고친다
SELECT DISTINCT e.name, d.name       왜 행이 늘었나?
FROM ... JOIN ...                      -> 1:N 조인이었나
  -> 행 수는 맞아 보인다                -> 조인 조건을 빠뜨렸나
  -> 그런데 SUM 은 여전히 부풀어 있다    -> 선집계·EXISTS 로 바꾼다
```

> **조인 팬아웃(join fan-out)** — 1:N 조인으로 한쪽 행이 여러 번 복제되는 현상.\
> 예: 사원 1명에 발령 이력 3건이 붙으면 그 사원의 급여가 `SUM` 에서 3번 더해진다.

**`DISTINCT` 로 덮으면 안 되는 이유는 「지워지지 않는 것」이 남기 때문이다.**

```text
DISTINCT 가 고쳐 주는 것     DISTINCT 가 못 고치는 것
  중복된 "행"                  이미 부풀어 있는 집계값 (SUM·AVG·COUNT)
                              값이 달라서 안 접히는 중복 (id 가 섞여 있으면 그대로)
```

**판단 순서는 이렇다.**

1. **행이 왜 늘었는지 먼저 센다** — 조인 전후로 `COUNT(*)` 를 찍어 어느 단계에서 늘었는지 본다.
2. **원인이 팬아웃이면 구조를 바꾼다** — 필요한 쪽을 먼저 집계하거나(선집계), 존재 여부만 필요하면 `EXISTS` 로 바꾼다.
3. **중복이 데이터의 성질이면** 그때 `DISTINCT` 를 쓴다 — 예: 「사원이 있는 부서 목록」.

조인 팬아웃의 정본은 [25 조인 팬아웃](../25-join-fan-out/), `EXISTS` 형태는 [19 SEMI·ANTI 조인](../19-semi-anti-join/)이다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| ★ 열 개수에 따른 기준 변화 (1번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 한 열 · 두 열 · `*` |
| `DISTINCT(열)` 괄호 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **1번 (B)와 출력이 동일한 것이 근거** |
| `NULL` 접힘 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `dept_id`·`salary` 양쪽 |
| ★ `COUNT` 세 형태 (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `SUM(DISTINCT)` 포함 |
| ★ `COUNT(DISTINCT a,b)` (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 에러 + 2 대 4** — 목록 README 에 없던 방언 차이 |
| `DISTINCT` + `ORDER BY` 충돌 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거** |
| `ORDER BY` 식 엄격도 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 에러 / MySQL 통과** — 새 방언 차이 |
| 계획 대조 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **구현 의존** — 4행짜리 표 기준 |
| ★ `DISTINCT ON` (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | MySQL 은 `ERROR 1064` |
| 윈도우 함수 대체 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 같은 세 행 확인 |
| `DISTINCT ON` 의 `ORDER BY` 규칙 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거** |
| `DISTINCT` + `LIMIT` | PG 18.6 · MySQL 8.4.10 | 각 1회 | 접은 뒤 자르는 것 확인 |

**구현 의존 항목** — 8번의 계획이다. **4행짜리 표에서 관찰한 것**이라 큰 표·인덱스가 있는 열에서는 달라질 수 있다.\
「`DISTINCT` 와 `GROUP BY` 의 계획이 같았다」는 이 조건에서의 관찰이지 보장이 아니다.

**언어 보장 항목** — 1~6·9·11번. 기준이 출력 행 전체인 것, `NULL` 이 접히는 것,\
`COUNT(DISTINCT)` 가 `NULL` 을 안 세는 것, `DISTINCT` 가 `ORDER BY` 보다 앞인 것은 **두 엔진에서 같았다.**

**버전** — `DISTINCT ON` 은 PG 전용이고 MySQL 8.4.10 에는 문법이 없다(`ERROR 1064`).\
다음 버전에서는 **5·7·8번**(방언·계획)을 다시 돌린다.
