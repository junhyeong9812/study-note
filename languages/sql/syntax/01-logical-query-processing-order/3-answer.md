# sql/01-논리적 질의 처리 순서 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> 문서 근거는 [PG 18 SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 SELECT](https://dev.mysql.com/doc/refman/8.4/en/select.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `SELECT` 를 맨 위에 적는데 엔진은 왜 다섯 번째에 처리하는가?

**적는 순서는 사람이 읽기 좋으라고 정해진 것이고, 처리 순서는 「무엇이 무엇의 입력인가」로 정해지기 때문이다.**

`SELECT` 는 「무엇을 내보낼까」를 정하는 칸이다.\
그런데 무엇을 내보낼지 고르려면 **고를 대상인 행 집합이 먼저 있어야** 한다.\
행 집합은 `FROM` 이 만들고, `WHERE` 가 줄이고, `GROUP BY` 가 묶고, `HAVING` 이 또 줄인다.\
그 네 칸이 끝나야 `SELECT` 가 일할 재료가 확정된다.

```text
칸       무엇을 받나              무엇을 내놓나
────     ──────────────           ──────────────
1 FROM   테이블(들)               행 집합           <- 재료를 만든다
2 WHERE  행 집합                  더 작은 행 집합
3 GROUP  행 집합                  그룹의 집합
4 HAVING 그룹의 집합              더 작은 그룹의 집합
5 SELECT 확정된 (행|그룹) 집합    출력 열            <- 여기서 처음 "열"이 생긴다
6 DISTINCT 출력 행               중복 없는 출력 행
7 ORDER BY 출력 행               순서 있는 출력 행
8 LIMIT  순서 있는 출력 행        앞 n 행
```

각 칸의 「내놓는 것」이 다음 칸의 「받는 것」과 정확히 맞물린다.\
`SELECT` 를 2번에 두면 아직 존재하지 않는 행 집합에서 열을 만들어야 하므로 성립하지 않는다.

> **논리적 처리 순서** — 결과를 *정의*하는 순서. 옵티마이저는 실행 순서를 바꿔도 되지만 **결과는 이 순서로 계산한 것과 같아야** 한다.\
> 예: `WHERE` 를 조인 안쪽으로 밀어 넣는 최적화를 해도 결과 집합은 그대로여야 한다.

그래서 이 순서는 **성능 이야기가 아니다.** 실제로 무엇을 먼저 했는지는 `EXPLAIN` 이 말한다([목록의 **58번 주제**](../58-explain-plan-tree/)).

---

### 2. `SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;` 이 에러인 이유

**`annual` 이라는 이름은 5번 칸에서 태어나는데, `WHERE` 는 2번 칸이라 아직 그 이름이 없다.**

```text
2번 칸에서 보이는 것            5번 칸에서 보이는 것
+--------------------+        +--------------------+
| emp 의 실제 열들    |        | emp 의 실제 열들    |
|  id, name,         |        |  id, name,         |
|  dept_id, salary   |        |  dept_id, salary   |
+--------------------+        | + 방금 만든 출력 열  |
                              |   annual           |
   annual 은 없다              +--------------------+
```

두 엔진 다 "그런 열 없다"로 거부한다 — 문법 오류가 아니라 **이름 해석 실패**다.

```text
### SQL: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 1: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
                                                    ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22): Unknown column 'annual' in 'where clause'
```

PG 문서가 이 규칙을 한 문장으로 적어 두었다 — 출력 열 이름은 `ORDER BY`·`GROUP BY` 에서는 쓸 수 있지만 `WHERE`·`HAVING` 에서는 쓸 수 없고, 거기서는 식을 그대로 적어야 한다([SELECT 페이지](https://www.postgresql.org/docs/18/sql-select.html)).

**고치는 법 두 가지.**

```sql
-- (A) 식을 다시 적는다
SELECT salary * 12 AS annual FROM emp WHERE salary * 12 > 4000;

-- (B) 한 겹 감싼다 — 안쪽이 "이전 칸"이 되면 바깥에서는 그냥 열이다
SELECT * FROM (SELECT salary * 12 AS annual FROM emp) t WHERE t.annual > 4000;
```

(B)가 되는 이유도 같은 순서다 — 바깥 질의의 `FROM`(1번 칸)이 안쪽 질의를 통째로 **먼저** 끝내기 때문이다.

---

### 3. `SELECT salary * 12 AS annual FROM emp ORDER BY annual;` 는 통과하는가

**통과한다.** `ORDER BY` 는 7번 칸이라 5번 칸이 만든 `annual` 을 이미 볼 수 있다.

```text
### SQL: SELECT salary * 12 AS annual FROM emp ORDER BY annual;
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

값 자체는 양쪽이 같다 — `300*12=3600`, `400*12=4800`, `500*12=6000`, 그리고 `NULL*12 = NULL`(`cho`).

**그런데 `NULL` 의 자리가 반대다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `ORDER BY ... ASC` 에서 `NULL` | **맨 뒤** (큰 값 취급) | **맨 앞** (작은 값 취급) |
| `NULLS FIRST` / `NULLS LAST` 지정 | **가능** | **문법 없음** |

지정 문법 유무도 직접 확인했다.

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary NULLS FIRST;
--- PG 18.6 ---
 id | salary
----+--------
  3 |   NULL
  1 |    300
  4 |    400
  2 |    500
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds
  to your MySQL server version for the right syntax to use near 'NULLS FIRST' at line 1
```

정렬과 `NULL` 위치는 이 주제가 아니라 [목록의 **08번 주제**](../08-order-by-null-position-stability/)이다. 여기서는 **"별칭이 `ORDER BY` 에서는 보인다"** 만 인출하면 된다.

---

### 4. `SELECT id AS salary FROM emp WHERE salary > 400;` 의 결과

**1행이 나오고, 출력 값은 `2` 다.**

이유는 두 칸이 서로 다른 `salary` 를 보기 때문이다.

```text
WHERE (2번 칸)                    SELECT (5번 칸)
별칭은 아직 없다                   별칭이 방금 생겼다
  -> salary = emp.salary            -> 출력 열 이름이 salary 이고
  -> 500 > 400 인 bob 만 통과          그 값은 emp.id 다
```

```text
### SQL: SELECT id AS salary FROM emp WHERE salary > 400;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
      2                          +--------+
(1 row)                          |      2 |
                                 +--------+
```

`2` 는 `bob` 의 `id` 다. 「급여가 400 초과인 사람의 id」인데 열 이름이 `salary` 로 보이는 것뿐이다.

같은 질의에서 `ORDER BY salary` 로 바꾸면 이번엔 **별칭이 이긴다.**

```text
### SQL: SELECT id AS salary FROM emp ORDER BY salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
      1                          +--------+
      2                          |      1 |
      3                          |      2 |
      4                          |      3 |
(4 rows)                         |      4 |
                                 +--------+
```

`id` 순(1,2,3,4)이다. 급여 순(300,400,500,NULL)이 아니다.

두 그림의 결론 — **같은 글자 `salary` 가 2번 칸에서는 테이블 열, 7번 칸에서는 출력 별칭을 가리킨다.**\
그래서 실무에서는 **기존 열 이름과 같은 별칭을 붙이지 않는다.** 읽는 사람이 칸마다 다른 것을 떠올려야 한다.

---

### 5. `dept_id = 10` 의 `cnt` 는 (A)와 (B)에서 각각 얼마인가

**(A) `WHERE` 는 1, (B) `HAVING` 은 2 다.**

```text
(A) WHERE salary >= 400 — 행을 먼저 버린다
emp 4행 --WHERE--> [bob 500, dan 400] --GROUP BY dept_id--> {10:[bob]}   -> cnt 1
                    (ann 300 탈락,                          {NULL:[dan]}
                     cho NULL 탈락)

(B) HAVING MAX(salary) >= 400 — 그룹을 통째로 판정한다
emp 4행 --GROUP BY dept_id--> {10:[ann,bob], 20:[cho], NULL:[dan]}
        --HAVING MAX>=400--> {10:[ann,bob], NULL:[dan]}                  -> cnt 2
                             (20 은 MAX(salary)=NULL 이라 탈락)
```

```text
(A)
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp
         WHERE salary >= 400 GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   1                   +---------+-----+
    NULL |   1                   |    NULL |   1 |
(2 rows)                         |      10 |   1 |
                                 +---------+-----+

(B)
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp
         GROUP BY dept_id HAVING MAX(salary) >= 400 ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   2                   +---------+-----+
    NULL |   1                   |    NULL |   1 |
(2 rows)                         |      10 |   2 |
                                 +---------+-----+
```

**두 문장은 다른 질문에 답하고 있다.**

| | 무엇을 묻는가 | 10번 부서의 답 |
|---|---|---|
| (A) `WHERE` | 급여 400 이상인 사람이 부서마다 **몇 명**인가 | 1명(`bob`) |
| (B) `HAVING` | **한 명이라도** 400 이상인 부서의 **전체 인원**은 | 2명(`ann`, `bob`) |

그래서 "`WHERE` 든 `HAVING` 이든 되는데 `WHERE` 가 빠르다"는 말은 **반쪽만 맞다.**\
행 단위로 판정 가능한 같은 조건이면 `WHERE` 가 맞지만, 위처럼 **의미가 다르면 둘은 바꿔 쓸 수 있는 것이 아니다.**

참고로 (B)에서 `dept_id=20`(`cho`) 이 빠진 것은 `MAX(NULL) = NULL` 이고 `NULL >= 400` 이 `UNKNOWN` 이라서다 — [04번](../04-null-three-valued-logic/) 의 규칙이 여기서도 작동한다.

---

### 6. `SELECT DISTINCT dept_id FROM emp ORDER BY salary;` 가 증명하는 순서

**6번 칸 `DISTINCT` 가 7번 칸 `ORDER BY` 보다 앞이라는 것**을 증명한다.

```text
5 SELECT   -> 출력 열은 dept_id 하나뿐이다. salary 는 여기서 버려졌다
6 DISTINCT -> dept_id 기준으로 중복을 접는다 (10 이 둘 -> 하나)
7 ORDER BY -> 이제 salary 로 정렬하라고? 그 열은 두 칸 전에 사라졌다
```

`DISTINCT` 가 `dept_id=10` 인 두 행(`ann`·`bob`)을 한 행으로 접은 뒤에는, 그 한 행의 `salary` 가 300 인지 500 인지 **정할 방법이 없다.** 그래서 문법 차원에서 막는다.

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
--- PG 18.6 ---
ERROR:  for SELECT DISTINCT, ORDER BY expressions must appear in select list
LINE 1: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
                                                  ^
--- MySQL 8.4.10 ---
ERROR 3065 (HY000): Expression #1 of ORDER BY clause is not in SELECT list, references
  column 'study.emp.salary' which is not in SELECT list; this is incompatible with DISTINCT
```

**`DISTINCT` 가 없으면 같은 질의가 통과한다** — 그때는 `ORDER BY` 가 `SELECT` 에 없는 열도 쓸 수 있다.\
「`ORDER BY` 는 `SELECT` 목록 밖의 열을 쓸 수 있다」와 「`DISTINCT` 가 있으면 못 쓴다」가 충돌하지 않는 이유가 이 순서다.

참고로 `DISTINCT` 는 `NULL` 끼리를 **같은 값으로 보고 접는다.**

```text
### SQL: SELECT DISTINCT salary FROM emp ORDER BY salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
    300                          +--------+
    400                          |   NULL |
    500                          |    300 |
   NULL                          |    400 |
(4 rows)                         |    500 |
                                 +--------+
```

`NULL = NULL` 이 참이 아닌데도 한 행으로 접힌다 — `DISTINCT` 와 `GROUP BY` 는 등호가 아니라 *구별 불가능성*으로 묶기 때문이다([04번](../04-null-three-valued-logic/)).

---

### 7. `HAVING cnt >= 1` — PG 와 MySQL 에서 각각 무엇이 나오는가

**PG 18.6 은 에러, MySQL 8.4.10 은 정상 동작한다.** 이 주제에서 두 엔진이 갈리는 유일한 자리다.

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 1;
--- PG 18.6 ---
ERROR:  column "cnt" does not exist
LINE 1: ..., COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 1;
                                                              ^
--- MySQL 8.4.10 ---
+---------+-----+
| dept_id | cnt |
+---------+-----+
|      10 |   2 |
|      20 |   1 |
|    NULL |   1 |
+---------+-----+
```

네 칸을 표로 정리하면 이렇다 — **`HAVING` 칸 하나만 다르다.**

| 별칭을 쓸 수 있나 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `WHERE` | ✗ `column "annual" does not exist` | ✗ `ERROR 1054 Unknown column` |
| `GROUP BY` | ✓ | ✓ |
| `HAVING` | **✗ `column "cnt" does not exist`** | **✓ 정상 출력** |
| `ORDER BY` | ✓ | ✓ |

`GROUP BY` 에서 되는 것도 양쪽에서 확인했다.

```text
### SQL: SELECT salary * 12 AS annual, COUNT(*) FROM emp GROUP BY annual;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual | count                  +--------+----------+
--------+-------                 | annual | COUNT(*) |
   NULL |     1                  +--------+----------+
   6000 |     1                  |   3600 |        1 |
   4800 |     1                  |   6000 |        1 |
   3600 |     1                  |   NULL |        1 |
(4 rows)                         |   4800 |        1 |
                                 +--------+----------+
```

(`ORDER BY` 가 없으므로 줄 순서는 보장되지 않는다. 두 출력의 줄 순서가 다른 것은 방언 차이가 아니다.)

**이 차이의 방향이 중요하다.**

```text
MySQL 에서 쓴 질의를 PG 로              PG 에서 쓴 질의를 MySQL 로
        │                                      │
        ▼                                      ▼
 HAVING 에 별칭이 있으면 깨진다           깨지지 않는다
 (PG 가 더 좁다)                         (MySQL 이 PG 의 상위집합)
```

이식성을 원하면 **`HAVING` 에는 식을 그대로 적는다**(`HAVING COUNT(*) >= 1`). 양쪽 다 돈다.

---

### 8. `LIMIT 1` 을 붙였으니 엔진이 한 행만 만들고 멈출 수 있는가

**아니다. `LIMIT` 은 여덟 번째 칸이라 앞의 일곱 칸은 이미 다 돌았다.**

```text
FROM     emp 4행을 읽는다                   <- 다 읽어야 한다
WHERE    (없음)
GROUP BY 3그룹을 만든다                     <- 다 묶어야 한다
HAVING   (없음)
SELECT   3행 x 2열                          <- 다 만들어야 한다
ORDER BY cnt DESC 로 3행을 정렬한다          <- 전부 봐야 1등을 안다
LIMIT    앞에서 1행만 꺼낸다                 <- 여기서 2행을 버린다
```

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp WHERE salary IS NOT NULL
         GROUP BY dept_id HAVING COUNT(*) >= 1 ORDER BY cnt DESC LIMIT 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   2                   +---------+-----+
(1 row)                          |      10 |   2 |
                                 +---------+-----+
```

한 행이 나왔지만, 그 한 행을 고르기 위해 **행 4개를 읽고 그룹 2개를 만들고 정렬까지** 했다.

> **정렬은 조기 종료가 안 된다** — 「가장 큰 것 하나」를 알려면 전부 봐야 한다.\
> 예: `ORDER BY cnt DESC LIMIT 1` 에서 마지막에 읽은 그룹이 1등일 수도 있다.

단 **하나 예외가 있다.** `ORDER BY` 의 키에 **인덱스가 있어서 정렬 없이 순서대로 읽을 수 있으면**, 엔진은 n 행만 읽고 멈출 수 있다. 그건 실행 계획 차원의 최적화이고, 논리적 순서가 바뀐 것은 아니다(목록의 [**46**](../46-index-definition-composite-partial-expression/)·[**47**](../47-when-indexes-are-used/)·[**58**](../58-explain-plan-tree/)번).

같은 이유로 `OFFSET` 도 공짜가 아니다 — 건너뛴다는 건 **만들긴 다 만들었다**는 뜻이다.

```text
### SQL: SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  2 | bob                        +----+------+
  3 | cho                        |  2 | bob  |
(2 rows)                         |  3 | cho  |
                                 +----+------+
```

`id=1` 인 `ann` 도 정렬까지는 참여했고, 마지막 칸에서 버려졌다.\
`OFFSET 100000` 이 느린 이유가 이것이다 — 버리려고 10만 행을 만든다([목록의 **09번 주제**](../09-limit-offset-keyset-pagination/) 키셋 페이지네이션).

**마지막으로, `ORDER BY` 없는 `LIMIT` 은 어느 행이 올지 정해지지 않는다.**\
지금 잘 나오는 것은 보장이 아니라 우연이다. 계획이 바뀌면 다른 행이 온다.

## 실행 검증

**원저자가 몇 번 돌렸는지는 문서에 남아 있지 않아 모른다.** 아래 「몇 번」은 **2026-09-21 재검증에서 실제로 돌린 횟수**다 —\
본문의 실행 블록을 **전부 다시 던져** 문서 값과 대조했고, **어긋난 블록은 0건**이었다.

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 여덟 칸 통과 질의 (8번·「동작 방식」 머리) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `dept_id=10 · cnt=2` 한 행 |
| `FROM` 의 카티션곱 (동작 방식 1) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 4 × 3 = **12** |
| `WHERE` 뒤 행 수 (동작 방식 2) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 3 |
| 집계 함수를 `WHERE` 에 (동작 방식 2) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러가 근거다** — `not allowed in WHERE` / `ERROR 1111` |
| `GROUP BY` 뒤 그룹 (동작 방식 3) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `NULL` 이 한 그룹 |
| 묶이지 않은 열 (동작 방식 3) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `ERROR 1055` — 근거가 **설정**(`only_full_group_by`)이다 |
| 별칭을 `WHERE` 에 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `column "annual" does not exist` / `ERROR 1054` |
| 별칭을 `ORDER BY` 에 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | ★ `NULL` 의 자리가 **반대**로 나온다 |
| `NULLS FIRST` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | ★ **MySQL 의 `ERROR 1064` 가 근거다** |
| 별칭이 열 이름을 가릴 때 (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `WHERE` 판 1행(값 2) · `ORDER BY` 판 id 순 |
| `WHERE` 대 `HAVING` (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `cnt` 가 **1과 2로 갈린다** |
| `DISTINCT` + `ORDER BY` (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러가 6번↔7번 순서를 증명한다** |
| `DISTINCT salary` (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `NULL` 이 한 행으로 접힌다 |
| ★ `HAVING` 에서 별칭 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **한쪽에서만 결론이 서는 자리** — PG 에러 / MySQL 3행 |
| `GROUP BY` 에서 별칭 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 양쪽 통과 |
| 서수 `ORDER BY 2 DESC, 1` (동작 방식 7) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `LIMIT 2 OFFSET 1` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 윈도우 함수를 `WHERE` 에 (어디서 틀리나) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `ERROR 3593` |

(위 질의를 PG 에는 **한 세션에 묶어 한 번 더** 던졌다 — 그래서 PG 쪽은 각 2회, MySQL 쪽은 각 1회다.\
두 판의 **값이 같았다**. 첫 판은 `NULL` 표시 설정만 달라 빈칸으로 찍혔다 — 서버가 다른 답을 준 것이 아니다.)

**구현 의존 항목** — 3·7번. **`HAVING` 에서 별칭이 되는가**와 **`ORDER BY` 에서 `NULL` 이 어디에 서는가**는 표준이 정한 것이 아니라 **엔진의 선택**이다.\
에러 번호·문구(`1054`·`1055`·`1064`·`1111`·`3065`·`3593`)도 구현 세부다 — **문자열로 분기하지 마라.**\
특히 3번의 `only_full_group_by` 는 **끌 수 있는 설정**이라, 같은 MySQL 서버에서도 답이 달라질 수 있다.

**언어 보장 항목** — 1·2·4·5·6·8번. 여덟 칸의 순서, 별칭이 `WHERE` 에 없다는 것, 별칭이 기존 열 이름을 가리는 규칙,\
`WHERE`(행)와 `HAVING`(그룹)의 의미 차이, `DISTINCT` 가 `ORDER BY` 보다 앞이라는 것, `LIMIT` 이 마지막 칸이라는 것은\
**두 엔진에서 같았고**(문구만 다르다) PG 의 SELECT 페이지가 규칙으로 적어 두었다.

**방언이 갈리는 항목 — 버전이 오르면 다시 찍을 자리** — ① `HAVING` 별칭(PG ✗ / MySQL ✓) ② `ORDER BY` 의 `NULL` 자리와 `NULLS FIRST|LAST` 문법 유무\
③ 에러 번호·문구 ④ `sql_mode` 기본값. **이 넷 말고는 이 주제에서 갈리는 것이 없다.**

**순서 보장** — 없다. `ORDER BY` 가 없는 출력(`GROUP BY annual` 판)의 줄 순서는 보장되지 않는다 —\
두 출력의 줄 순서가 다른 것은 **방언 차이가 아니다.** 재검증에서도 같은 줄 순서가 다시 나왔지만, **같았다는 것은 보장이 아니다.**

**DB 잔재** — 없다. 이 주제는 **`emp`·`dept` 를 읽기만 했다.** 두 엔진의 최종 표 목록은 [52 UPSERT](../52-upsert/)의 「실행 검증」에 있다.
