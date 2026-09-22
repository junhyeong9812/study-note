# sql/02-SELECT 목록과 열 별칭의 유효 범위 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — 별칭 규칙 자체는 두 엔진 모두 오래전부터 있다. 이 주제에서 버전에 갈리는 것은 없다.\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/). 이 주제는 01의 여덟 칸 중 **5번 칸 하나를 확대한 것**이다.

## 한눈에 — 쉽게 말하면

**별칭은 「출구에 붙이는 이름표」다. 출구 앞을 지나는 칸은 그 이름표를 못 본다.**

- 공장 컨베이어를 생각하자. 상자가 여덟 개 작업대를 차례로 지난다.
- **다섯 번째 작업대**가 상자에 **이름표를 붙이는 일**을 한다.
- 두 번째 작업대의 검사원에게 "이름표가 `annual` 인 상자를 빼내라"고 하면?\
  그 검사원은 **아직 이름표가 없는 상자**를 보고 있다. "그런 이름 없는데요"가 나온다.
- 일곱 번째 작업대는 이름표를 본다. 이미 다섯 번째를 지나왔으니까.

| 비유 | 실체 |
|---|---|
| 컨베이어 여덟 작업대 | 논리적 질의 처리 순서(`FROM`→…→`LIMIT`) |
| 다섯 번째 작업대 | `SELECT` 목록 |
| 이름표 | 열 별칭(`AS annual`) |
| 이름표를 못 보는 앞쪽 검사원 | `WHERE`(2번 칸) |
| 이름표를 보는 뒤쪽 검사원 | `ORDER BY`(7번 칸) |
| 상자에 원래 찍혀 있는 각인 | 테이블의 실제 열 이름 |

```text
      적는 순서                        이름표가 존재하는 구간
      ─────────                        ──────────────────
1행   SELECT salary*12 AS annual  ──┐
2행   FROM   emp                    │   FROM     (1)  annual 없음
3행   WHERE  annual > 4000          │   WHERE    (2)  annual 없음  <- 여기서 터진다
4행   GROUP BY ...                  │   GROUP BY (3)  annual 있음* (특례)
5행   HAVING ...                    │   HAVING   (4)  엔진마다 다름
6행   ORDER BY annual               │   SELECT   (5)  ★ 여기서 태어난다
                                    └─> ORDER BY (7)  annual 있음
```

이 이름표가 **똑같은 구조로** SQL 의 열 별칭이다.\
「그런 열 없다」는 에러의 거의 전부가 이 그림 한 장이다.

> **열 별칭(column alias)** — `SELECT` 목록의 한 항목에 `AS` 로 붙이는 **출력 열의 이름**.\
> 예: `salary * 12 AS annual` 의 `annual`. 테이블에는 그런 열이 없고, 결과에만 있다.

> **출력 열(output column)** — 질의 결과가 내보내는 열. `SELECT` 목록이 정한다.\
> 예: `SELECT id, salary*12 AS annual FROM emp` 의 출력 열은 `id` 와 `annual` 둘이다.

## 이 주제가 답하려는 질문

1. **별칭은 어느 절에서 보이고 어느 절에서 안 보이나** — 그리고 그 경계선이 왜 거기인가.
2. **같은 이름이 테이블 열과 별칭 양쪽에 있을 때 어느 쪽이 이기나** — 절마다 답이 다른가.
3. **`SELECT *` 와 `ORDER BY 1` 처럼 이름을 안 쓰는 지정**은 무엇을 대가로 편한가.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들이 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |  <- 사원이 없는 부서
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
        ^          ^
        |          +-- dan 은 소속이 없다 (dept_id NULL)
        +------------- cho 는 급여가 없다 (salary NULL)
```

이 주제에서는 **`salary` 라는 이름 자체**가 무기가 된다 — 실제 열 이름이면서, 별칭으로도 붙일 수 있는 이름이기 때문이다.

## 동작 방식

이 절이 이 문서의 본문이다. **「어느 칸에서 이 이름이 보이나」** 하나만 칸마다 따라간다.

### 1. 별칭은 `SELECT` 칸에서 태어난다

**언제 쓰나** — 식에 이름을 붙일 때마다. `salary * 12`, `COUNT(*)` 처럼 열 이름이 없는 결과에는 별칭이 사실상 필수다.

```text
(전) 2번 칸 WHERE 가 보는 이름들      (후) 5번 칸 SELECT 가 만든 뒤의 이름들
+---------------------------+       +---------------------------+
| emp.id                    |       | emp.id                    |
| emp.name                  |       | emp.name                  |
| emp.dept_id               |       | emp.dept_id               |
| emp.salary                |       | emp.salary                |
+---------------------------+       | + annual   <- 방금 생김    |
   annual 은 아직 없다               +---------------------------+
```

```text
### SQL: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 1: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
                                                    ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'annual' in 'where clause'
```

그림 해설 — 두 엔진 다 **문법 오류가 아니라 「이름 해석 실패**」로 거부한다. 문장 구조는 멀쩡하고 이름이 없는 것이다.\
대가 — 별칭을 앞 칸에서 쓰려면 식을 **한 번 더 적어야** 한다(`WHERE salary * 12 > 4000`). 식이 길면 두 군데가 어긋날 위험이 생긴다.

**같은 `SELECT` 목록 안에서도** 앞 항목의 별칭을 뒤 항목이 못 쓴다.

```text
### SQL: SELECT salary * 12 AS annual, annual / 12 AS back FROM emp;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 1: SELECT salary * 12 AS annual, annual / 12 AS back FROM emp;
                                      ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'annual' in 'field list'
```

MySQL 의 에러 위치가 `'field list'` 라는 점이 힌트다 — **`SELECT` 목록 전체가 한 덩어리로 평가되고, 항목 사이에 순서가 없다.**\
「위에서 아래로 계산한다」는 절차형 언어의 직관이 여기서 안 통한다.

---

### 2. `ORDER BY` 는 별칭을 본다 — 그리고 별칭이 이긴다

**언제 쓰나** — 계산한 값으로 정렬할 때. 7번 칸이라 5번 칸의 결과를 이미 갖고 있다.

```text
(전) 5번 칸이 만든 출력                (후) 7번 칸이 annual 로 줄 세움
+--------+                            +--------+
| annual |                            | annual |
|   3600 |   ORDER BY annual          |   3600 |
|   6000 |   ---------------->        |   4800 |
|   NULL |                            |   6000 |
|   4800 |                            |   NULL |   <- PG 기준
+--------+                            +--------+
```

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

그림 해설 — 양쪽 다 통과한다. `NULL` 의 자리가 반대인 것은 별칭과 무관한 **정렬 주제**다([08번](../08-order-by-null-position-stability/)).\
대가 — 없다. 오히려 `ORDER BY` 에서는 식을 다시 적는 것보다 별칭이 낫다.

**이름이 겹치면 `ORDER BY` 에서는 별칭이 이긴다.**

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
  -> id 순(1,2,3,4)이다. 급여 순(300,400,500,NULL)이 아니다
```

**그런데 그 별칭을 식 안에 넣는 순간 결과가 뒤집힌다.**

```text
### SQL: SELECT id AS salary FROM emp ORDER BY salary + 0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
      1                          +--------+
      4                          |      3 |
      2                          |      1 |
      3                          |      4 |
(4 rows)                         |      2 |
                                 +--------+
  -> PG:    1(ann 300), 4(dan 400), 2(bob 500), 3(cho NULL)  = emp.salary 순
  -> MySQL: 3(cho NULL), 1(300), 4(400), 2(500)              = emp.salary 순 (NULL 앞)
```

두 그림의 결론 — **`ORDER BY salary` 는 별칭, `ORDER BY salary + 0` 은 테이블 열 `emp.salary` 를 가리킨다.**\
규칙은 「별칭은 **홀로 선 이름**일 때만 보인다」이다. 식의 일부가 되면 일반 이름 해석 규칙으로 돌아가 테이블 열이 이긴다.\
대가 — 기존 열 이름과 같은 별칭을 붙이면 **한 질의 안에서 같은 글자가 두 가지를 뜻하게 된다.** 이 규칙을 모르면 읽을 수 없는 질의가 된다.

---

### 3. `GROUP BY` 는 별칭도 받지만, 이름이 겹치면 **테이블 열**이 이긴다

**언제 쓰나** — 계산한 값으로 묶을 때. 3번 칸인데도 별칭이 통하는 **예외 구간**이다.

```text
### SQL: SELECT salary * 12 AS annual FROM emp GROUP BY annual ORDER BY annual;
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

3번 칸은 5번 칸보다 **앞**인데 왜 되나? **문법이 허용하는 편의**다 — 표준과 두 엔진 모두 `GROUP BY` 에서 출력 열 이름을 받아 준다.\
순서 모형이 틀린 게 아니라, `GROUP BY` 가 그 이름을 **식으로 되돌려 해석**한다고 읽으면 된다.

**그런데 같은 이름의 테이블 열이 있으면 그쪽이 이긴다.** 양쪽 엔진 모두 거부하는 것으로 증명된다.

```text
### SQL: SELECT dept_id AS salary, COUNT(*) AS c FROM emp GROUP BY salary ORDER BY 1;
--- PG 18.6 ---
ERROR:  column "emp.dept_id" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT dept_id AS salary, COUNT(*) AS c FROM emp GROUP BY sa...
               ^
--- MySQL 8.4.10 ---
ERROR 1055 (42000) at line 1: Expression #1 of SELECT list is not in GROUP BY clause and contains nonaggregated column 'study.emp.dept_id' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

그림 해설 — 에러가 `dept_id` 를 지목한다. 즉 `GROUP BY salary` 가 **별칭(=`dept_id`)이 아니라 `emp.salary` 로 해석됐고**, 그래서 `dept_id` 가 묶이지 않은 열이 된 것이다.\
대가 — 「`GROUP BY` 에서 별칭이 된다」를 무조건으로 외우면 여기서 틀린다. **테이블 열 이름과 겹치지 않을 때만** 별칭이 잡힌다.

---

### 4. `HAVING` — 두 엔진이 갈리는 유일한 칸

**언제 쓰나** — 그룹 조건에 집계 별칭을 쓰고 싶을 때. 이 주제에서 이식성이 깨지는 자리다.

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

네 칸을 표로 정리하면 **`HAVING` 한 칸만 다르다.**

| 별칭을 쓸 수 있나 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `WHERE` | ✗ `column "annual" does not exist` | ✗ `ERROR 1054 Unknown column` |
| `GROUP BY` | ✓ (겹치지 않을 때) | ✓ (겹치지 않을 때) |
| `HAVING` | **✗ `column "cnt" does not exist`** | **✓ 정상 출력** |
| `ORDER BY` | ✓ (홀로 선 이름일 때) | ✓ (홀로 선 이름일 때) |

```text
MySQL 에서 쓴 질의를 PG 로              PG 에서 쓴 질의를 MySQL 로
        │                                      │
        ▼                                      ▼
 HAVING 에 별칭이 있으면 깨진다           깨지지 않는다
 (PG 가 더 좁다)                         (MySQL 이 PG 의 상위집합)
```

그림 해설 — **방향이 비대칭이다.** MySQL 로 개발하고 PG 로 배포하는 팀이 여기서 사고를 낸다.\
대가 — 이식성을 지키려면 `HAVING` 에는 **식을 그대로** 적는다(`HAVING COUNT(*) >= 1`). 양쪽 다 돈다.

---

### 5. 서수 — 이름 대신 출력 열 번호

**언제 쓰나** — 긴 식으로 정렬·그룹할 때 식을 다시 안 적으려고. `ORDER BY 1` 은 「출력 첫 번째 열」이다.

```text
출력 열:      1        2
          +---------+-------+
          | dept_id | count |
          +---------+-------+
ORDER BY 2 DESC  ──> count 내림차순
GROUP BY 1       ──> dept_id 로 묶기
```

```text
### SQL: SELECT dept_id, COUNT(*) FROM emp GROUP BY 1 ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | count                 +---------+----------+
---------+-------                | dept_id | COUNT(*) |
      10 |     2                 +---------+----------+
      20 |     1                 |    NULL |        1 |
    NULL |     1                 |      10 |        2 |
(3 rows)                         |      20 |        1 |
                                 +---------+----------+
```

`ORDER BY` 와 `GROUP BY` **둘 다** 서수를 받는다(양쪽 엔진). 범위를 벗어나면 즉시 거부한다.

```text
### SQL: SELECT id, name FROM emp ORDER BY 3;
--- PG 18.6 ---
ERROR:  ORDER BY position 3 is not in select list
LINE 1: SELECT id, name FROM emp ORDER BY 3;
                                          ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column '3' in 'order clause'
```

그림 해설 — PG 는 「위치 3은 목록에 없다」로, MySQL 은 「`3` 이라는 열을 모른다」로 말한다. **거부한다는 사실은 같다.**\
대가 — 서수는 **`SELECT` 목록을 고치면 조용히 다른 열을 가리킨다.** 에러가 아니라 *다른 정답*이 나오므로 리뷰에서 안 잡힌다.

같은 `ORDER BY 2` 가 목록 순서만 바꿔도 다른 열을 뜻하는 것을 직접 보인 것이다.

```text
### SQL: SELECT * FROM (SELECT name, id FROM emp) t ORDER BY 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | id                       +------+----+
------+----                      | name | id |
 ann  |  1                       +------+----+
 bob  |  2                       | ann  |  1 |
 cho  |  3                       | bob  |  2 |
 dan  |  4                       | cho  |  3 |
(4 rows)                         | dan  |  4 |
                                 +------+----+
  -> 2번 열이 id 라서 id 순이다. 목록을 (id, name) 으로 바꾸면 같은 "ORDER BY 2" 가 name 순이 된다
```

---

### 6. `SELECT *` — 이름을 안 적는 대가

**언제 쓰나** — 탐색적 질의·콘솔에서. **저장되는 질의(뷰·애플리케이션 코드)에는 쓰지 않는다.**

```text
문제 1. 열이 몇 개인지, 어떤 순서인지가 질의문에 안 적혀 있다
        -> 테이블에 열이 하나 추가되면 결과 모양이 조용히 바뀐다

문제 2. 조인하면 같은 이름의 열이 둘이 된다
        emp.id, emp.name  +  dept.id, dept.name   ->   id, name, dept_id, salary, id, name
                                                        ^^                        ^^
```

```text
### SQL: SELECT e.*, d.* FROM emp e JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---
 id | name | dept_id | salary | id | name
----+------+---------+--------+----+-------
  1 | ann  |      10 |    300 | 10 | sales
  2 | bob  |      10 |    500 | 10 | sales
  3 | cho  |      20 |   NULL | 20 | dev
(3 rows)
--- MySQL 8.4.10 ---
+----+------+---------+--------+----+-------+
| id | name | dept_id | salary | id | name  |
+----+------+---------+--------+----+-------+
|  1 | ann  |      10 |    300 | 10 | sales |
|  2 | bob  |      10 |    500 | 10 | sales |
|  3 | cho  |      20 |   NULL | 20 | dev   |
+----+------+---------+--------+----+-------+
```

**출력 열 이름이 `id` 두 개, `name` 두 개다.** 결과만 받은 쪽에서는 어느 쪽이 무엇인지 알 수 없다.\
한 겹 감싸는 순간 두 엔진이 **서로 다른 방식으로** 거부한다.

```text
### SQL: SELECT id FROM (SELECT * FROM emp e JOIN dept d ON e.dept_id = d.id) t;
--- PG 18.6 ---
ERROR:  column reference "id" is ambiguous
LINE 1: SELECT id FROM (SELECT * FROM emp e JOIN dept d ON e.dept_id...
               ^
--- MySQL 8.4.10 ---
ERROR 1060 (42S21) at line 1: Duplicate column name 'id'
```

#### 방언 — 중복 열 이름을 가진 파생 테이블 자체가 성립하나

에러 메시지가 다른 것에는 이유가 있다. **바깥에서 `id` 를 안 골라도** 결과가 갈린다.

```text
### SQL: SELECT * FROM (SELECT * FROM emp e JOIN dept d ON e.dept_id = d.id) t;
--- PG 18.6 ---
 id | name | dept_id | salary | id | name
----+------+---------+--------+----+-------
  1 | ann  |      10 |    300 | 10 | sales
  2 | bob  |      10 |    500 | 10 | sales
  3 | cho  |      20 |   NULL | 20 | dev
(3 rows)
--- MySQL 8.4.10 ---
ERROR 1060 (42S21) at line 1: Duplicate column name 'id'
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 중복 열 이름을 가진 파생 테이블 | **만들어진다** — 꺼내 쓸 때만 `ambiguous` | **만드는 순간 거부** `ERROR 1060 Duplicate column name` |
| 최상위 `SELECT` 의 중복 출력 열 이름 | 허용 | 허용 |

그림 해설 — **PG 는 늦게, MySQL 은 이르게 막는다.** PG 쪽이 더 오래 버티는 만큼 사고가 더 멀리 간다.\
대가 — 어느 쪽이든 고치는 법은 같다 — `SELECT *` 대신 **필요한 열을 별칭과 함께 적는다**(`e.id AS emp_id, d.id AS dept_id`).

---

### 7. 별칭 이름 자체의 규칙 — 대소문자와 예약어

**언제 쓰나** — 애플리케이션이 결과 열 이름으로 값을 찾을 때. 이름이 한 글자만 달라도 못 찾는다.

```text
### SQL: SELECT id AS MyCol FROM emp ORDER BY id LIMIT 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 mycol                           +-------+
-------                          | MyCol |
     1                           +-------+
(1 row)                          |     1 |
                                 +-------+
  -> PG 는 따옴표 없는 이름을 전부 소문자로 접는다. MySQL 은 적은 그대로 둔다
```

```text
### SQL: SELECT id AS "MyCol" FROM emp ORDER BY id LIMIT 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 MyCol                           +-------+
-------                          | MyCol |
     1                           +-------+
(1 row)                          |     1 |
                                 +-------+
  -> 큰따옴표로 감싸면 PG 도 대소문자를 보존한다
```

예약어를 별칭으로 쓸 때도 갈린다.

```text
### SQL: SELECT id AS from FROM emp ORDER BY id LIMIT 1;
--- PG 18.6 ---
 from
------
    1
(1 row)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'from FROM emp ORDER BY id LIMIT 1' at line 1
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 따옴표 없는 `AS MyCol` | **`mycol`** 로 접힌다 | **`MyCol`** 그대로 |
| 대소문자 보존 문법 | `AS "MyCol"` | 원래 보존 (`` AS `MyCol` `` 도 가능) |
| `AS from` (예약어) | **통과** | **`ERROR 1064` 문법 오류** |

그림 해설 — PG 는 `AS` 뒤를 넓게 받아 주는 대신 **소문자로 접고**, MySQL 은 보존하는 대신 **예약어를 막는다.**\
대가 — 애플리케이션이 `rs.getInt("MyCol")` 로 찾는다면 PG 에서 못 찾는다. 이식할 질의에는 **소문자 별칭**을 쓰는 것이 가장 안전하다.

## 문법 — 형태와 규칙

SQL 은 형태가 아니라 **「어느 절에서 무엇이 보이나」가 본체**인 언어다. 형태부터 적으면 이렇다.

```sql
SELECT <식> [AS] <별칭>      -- AS 는 생략 가능
     , <식> AS "대소문자 보존"
FROM   <표>
WHERE  <조건>                -- 별칭 사용 불가 (양쪽 엔진)
GROUP BY <식 | 별칭 | 서수>
HAVING <조건>                -- 별칭: PG 불가 / MySQL 가능
ORDER BY <식 | 별칭 | 서수>
```

규칙 다섯.

1. **별칭은 5번 칸(`SELECT`)에서 태어난다.** 그래서 `WHERE`(2번)에서는 없고 `ORDER BY`(7번)에서는 있다.
2. **`SELECT` 목록 안에는 순서가 없다.** 앞 항목의 별칭을 뒤 항목이 못 쓴다 — 양쪽 엔진 모두 에러다.
3. **별칭은 「홀로 선 이름」일 때만 보인다.** `ORDER BY salary` 는 별칭, `ORDER BY salary + 0` 은 테이블 열이다.
4. **이름이 겹칠 때 이기는 쪽이 칸마다 다르다** — `ORDER BY` 는 별칭, `GROUP BY` 는 테이블 열, `WHERE` 는 애초에 별칭이 없다.
5. **`AS` 는 생략할 수 있다.** `salary * 12 annual` 도 같은 뜻이다 — 다만 쉼표를 빠뜨렸을 때 **에러가 아니라 별칭으로 붙어 버리는** 사고가 있다.

`AS` 생략이 같은 뜻임을 확인한 출력이다.

```text
### SQL: SELECT salary * 12 annual FROM emp ORDER BY annual;
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

별칭을 앞 칸에서 쓰고 싶으면 **한 겹 감싼다.** 안쪽 질의가 바깥의 「1번 칸」이 되면 별칭은 그냥 열이다.

```text
### SQL: WITH t AS (SELECT id, salary * 12 AS annual FROM emp)
         SELECT id, annual FROM t WHERE annual > 4000 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | annual                     +----+--------+
----+--------                    | id | annual |
  2 |   6000                     +----+--------+
  4 |   4800                     |  2 |   6000 |
(2 rows)                         |  4 |   4800 |
                                 +----+--------+
```

## 어디서 틀리나

- **별칭을 `WHERE` 에 쓴다.**\
  이 주제에서 가장 흔하다. 고치는 법은 둘 — 식을 다시 적거나 CTE·파생 테이블로 한 겹 감싼다.
- **`SELECT` 목록 안에서 앞 별칭을 뒤에서 쓴다.**\
  `SELECT a*2 AS x, x+1 AS y` 는 양쪽 엔진 다 에러다. 목록 항목 사이에는 순서가 없다.
- **`HAVING` 별칭이 MySQL 에서만 되는 걸 모른다.**\
  MySQL 로 개발하고 PG 로 배포하면 여기서 깨진다. 반대 방향은 안 깨진다.
- **기존 열 이름과 같은 별칭을 붙인다.**\
  같은 글자가 칸마다 다른 것을 가리킨다. `ORDER BY salary` 와 `ORDER BY salary + 0` 의 답이 달라진다.
- **`GROUP BY` 별칭이 항상 되는 줄 안다.**\
  같은 이름의 테이블 열이 있으면 **테이블 열이 이긴다.** 에러 메시지가 엉뚱한 열을 지목해 더 헷갈린다.
- **서수(`ORDER BY 2`)를 저장되는 질의에 쓴다.**\
  `SELECT` 목록을 고치면 **에러 없이 다른 열로 정렬된다.**
- **`SELECT *` 를 뷰·애플리케이션 코드에 쓴다.**\
  조인하면 중복 이름이 생기고, 열이 추가되면 결과 모양이 조용히 바뀐다.\
  PG 는 꺼내 쓸 때 `ambiguous`, MySQL 은 파생 테이블을 만드는 순간 `ERROR 1060` 이다.
- **PG 에서 대소문자 섞인 별칭을 쓰고 그 이름으로 조회한다.**\
  따옴표가 없으면 소문자로 접힌다. `MyCol` 로 찾으면 못 찾는다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| 별칭이 `WHERE` 에서 안 보이는 것 | **양쪽 문서가 정한 규칙** | PG SELECT 페이지의 출력 열 이름 규칙 · 두 엔진 에러 |
| 별칭이 `ORDER BY`·`GROUP BY` 에서 보이는 것 | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| `HAVING` 에서 별칭이 되는 것 | **MySQL 쪽 확장** — 이식성 없음 | PG 는 에러, MySQL 은 정상 |
| 별칭 대소문자 접힘 | **PG 의 식별자 규칙** | `AS MyCol` → `mycol` |
| 예약어를 별칭으로 쓰는 것 | **파서 구현 차이** | PG 통과 / MySQL `ERROR 1064` |
| 중복 열 이름 파생 테이블 | **엔진의 검사 시점 차이** | PG 는 참조 시, MySQL 은 정의 시 |
| `ORDER BY` 결과의 `NULL` 위치 | **엔진 기본값** — 이 주제 밖 | [08번](../08-order-by-null-position-stability/) |

정리하면 — **「별칭은 `SELECT` 에서 태어난다」만 언어 보장이고, 나머지 네 칸의 세부는 엔진마다 다르다.**

## 언제 쓰고 언제 안 쓰나

- **별칭은 식에 무조건 붙인다.** 안 붙이면 출력 열 이름이 엔진 마음대로다(PG 는 `?column?`, MySQL 은 식 문자열).
- **기존 열 이름과 같은 별칭은 붙이지 않는다.** 한 질의 안에서 같은 글자가 두 뜻이 된다.
- **서수는 콘솔에서만.** 저장되는 질의에는 이름을 적는다.
- **`SELECT *` 는 탐색할 때만.** 뷰·애플리케이션·`INSERT ... SELECT` 에는 열을 명시한다.
- **이식할 질의는 `HAVING` 에 식을 적고, 별칭은 소문자로 쓴다.** 두 규칙만 지키면 이 주제에서 갈리는 자리가 없어진다.

## 핵심 문장

- 별칭은 **5번 칸(`SELECT`)에서 태어난다.** 그 앞 칸은 그 이름을 모른다.
- **`SELECT` 목록 안에는 순서가 없다** — 앞 별칭을 뒤 항목이 못 쓴다.
- 별칭은 **홀로 선 이름일 때만** 보인다. 식에 들어가면 테이블 열이 이긴다.
- 이름이 겹치면 **`ORDER BY` 는 별칭, `GROUP BY` 는 테이블 열**이 이긴다.
- `HAVING` 별칭은 **MySQL 만** 된다 — PG 로 옮기면 깨진다.
- 서수와 `SELECT *` 는 **에러 없이 다른 답**을 만드는 지정 방식이다.

## 관련 자료

- [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) — 출력 열 이름을 어느 절에서 쓸 수 있는지가 이 페이지에 있다.
- [MySQL 8.4 · SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html)
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 여덟 칸 전체의 순서까지, 여기는 5번 칸이 만든 이름의 유효 범위부터.**
- [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/) — **경계: 그쪽은 두 절의 의미 차이까지, 여기는 두 절에서 이름이 보이나 안 보이나부터.**
- [08 ORDER BY](../08-order-by-null-position-stability/) — **경계: 여기는 `ORDER BY` 가 별칭을 본다는 것까지, 그쪽은 그래서 어떤 순서로 나오나부터.**
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — **경계: 그쪽은 테이블 별칭, 여기는 열 별칭.**
- [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) — **경계: 그쪽이 그 규칙의 정본이고, 여기서는 그 에러를 「이름 해석의 증거」로만 쓴다.**
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **열 별칭(column alias)** — `SELECT` 목록의 항목에 붙이는 출력 열 이름.\
  예: `salary * 12 AS annual` 의 `annual`. 테이블에는 없고 결과에만 있다.
- **출력 열(output column)** — 질의가 내보내는 열. `SELECT` 목록이 정한다.\
  예: `SELECT id, COUNT(*) AS c ...` 의 출력 열은 `id`·`c` 둘.
- **이름 해석(name resolution)** — 질의문에 적힌 이름이 무엇을 가리키는지 정하는 일.\
  예: `ORDER BY salary` 에서 `salary` 가 별칭인지 `emp.salary` 인지 정하는 것.
- **서수(ordinal)** — 이름 대신 쓰는 출력 열 번호.\
  예: `ORDER BY 2` 는 두 번째 출력 열 기준 정렬.
- **식별자 접힘(identifier folding)** — 따옴표 없는 이름의 대소문자를 한쪽으로 통일하는 것.\
  예: PG 는 `MyCol` 을 `mycol` 로 접는다. MySQL 은 접지 않는다.
- **예약어(reserved word)** — 문법에서 특별한 뜻을 가져 이름으로 쓰기 어려운 낱말.\
  예: `from`. PG 는 `AS from` 을 받고 MySQL 은 거부한다.
- **파생 테이블(derived table)** — `FROM` 안에 놓인 서브쿼리.\
  예: `FROM (SELECT ...) t` 의 `t`. 자세한 규칙은 [10번](../10-from-clause-aliases-derived-tables/).
- **모호한 참조(ambiguous reference)** — 같은 이름의 후보가 둘 이상이라 고를 수 없는 상태.\
  예: 두 표를 `SELECT *` 로 붙인 뒤 `id` 를 부르면 PG 가 `ambiguous` 라고 한다.
- **CTE(`WITH`)** — 질의 앞에 이름 붙여 두는 서브질의.\
  예: `WITH t AS (...) SELECT ... FROM t`. 별칭을 「이전 칸의 결과」로 만드는 데 쓴다.

## 더 들어가면

- **별칭을 안 붙이면 열 이름이 엔진 마음대로다.** PG 는 계산식에 `?column?` 을 붙이고, MySQL 은 식 문자열 자체를 열 이름으로 쓴다(`COUNT(*)` 출력에서 확인된다). 결과를 이름으로 찾는 코드가 있으면 별칭은 선택이 아니라 필수다.
- **`SELECT *` 의 진짜 비용은 성능이 아니라 계약이다.** 열이 추가되면 결과의 모양이 바뀌고, 그 변화가 에러 없이 전파된다. public contract 로 나가는 질의에서 `*` 를 쓰지 않는 이유가 그것이다.
- **서수와 별칭 중 무엇이 나은가**는 취향이 아니다. 별칭은 `SELECT` 목록을 고쳐도 같은 것을 가리키고, 서수는 안 그렇다. 다만 `GROUP BY 1` 은 긴 식을 두 번 적는 것을 피하려는 실용적 선택으로 널리 쓰인다 — **콘솔·일회성 질의로 한정**하면 대가가 없다.
