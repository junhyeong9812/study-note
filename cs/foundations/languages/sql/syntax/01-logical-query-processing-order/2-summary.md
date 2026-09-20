# sql/01-논리적 질의 처리 순서 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-C](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — 여덟 절 자체는 두 엔진 모두 오래전부터 있다. 이 주제에서 버전에 갈리는 것은 없다.\
> 방언 차이가 나는 자리는 「PG / MySQL」 두 칸을 나란히 두고, **양쪽 실제 출력을 같이 싣는다.**

## 한눈에 — 쉽게 말하면

**SQL 질의 = 여덟 칸짜리 컨베이어 벨트. 적는 순서와 일하는 순서가 다르다.**

- 서류를 한 장 냈다고 하자.\
  접수 창구는 여덟 개고, 서류는 1번 창구부터 8번 창구까지 **차례로** 지나간다.
- 그런데 내가 **서류에 적는 칸 순서**는 창구 순서와 다르다.\
  맨 윗줄에 「원하는 것」(SELECT)을 적지만, 그건 **다섯 번째 창구**에서야 처리된다.
- 두 번째 창구(WHERE)가 「원하는 것」 칸에서 내가 새로 붙인 별명을 모르는 건 당연하다.\
  **그 별명은 아직 만들어지지 않았다.**
- 반대로 일곱 번째 창구(ORDER BY)는 다섯 번째가 만든 별명을 안다. 이미 지나왔으니까.

```text
내가 적는 순서                    엔진이 일하는 순서
─────────────                    ─────────────
SELECT   ...   (1번째로 적음)      1. FROM      표를 만든다
FROM     ...                      2. WHERE     행을 버린다
WHERE    ...                      3. GROUP BY  행을 묶는다
GROUP BY ...                      4. HAVING    그룹을 버린다
HAVING   ...                      5. SELECT    열을 만든다  <- 별칭이 여기서 태어난다
ORDER BY ...                      6. DISTINCT  중복 행을 지운다
LIMIT    ...   (마지막으로 적음)    7. ORDER BY  줄을 세운다
                                  8. LIMIT     자른다
```

이 컨베이어가 **똑같은 구조로** SQL 엔진이다.\
"왜 안 되지"의 태반이 이 그림 하나로 설명된다 — `WHERE` 에서 별칭이 안 되는 것, `WHERE` 와 `HAVING` 이 갈리는 것, 윈도우 함수를 `WHERE` 로 못 거르는 것이 전부 **"아직 안 만들어졌다"** 한 마디다.

> **논리적 처리 순서(logical query processing order)** — 엔진이 결과를 *정의*하는 순서. 실제 실행 계획은 옵티마이저가 순서를 바꿔도 되지만, **결과는 이 순서대로 계산한 것과 같아야** 한다.\
> 예: `WHERE` 를 조인보다 먼저 밀어 넣는 최적화를 해도, 결과 집합은 "조인 다음에 걸렀을 때"와 같아야 한다.

> **별칭(alias)** — `AS` 로 붙이는 새 이름. 열 별칭(`salary * 12 AS annual`)과 테이블 별칭(`FROM emp e`)이 있다.\
> 예: `annual` 은 5번 창구에서 태어나므로 2번 창구(`WHERE`)에는 없는 이름이다.

## 예시 테이블 — SQL 네 주제가 같이 쓰는 데이터

이 폴더의 `01` · `04` · `16` · `52` 는 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

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

NULL 을 두 군데에 심은 것은 의도한 것이다 — `salary NULL` 은 04번에서, `dept_id NULL` 은 16번에서 각각 사고를 일으킨다.

<details>
<summary>표를 만드는 문 (PostgreSQL)</summary>

```sql
CREATE TABLE dept (
  id   int PRIMARY KEY,
  name text UNIQUE NOT NULL
);
CREATE TABLE emp (
  id      int PRIMARY KEY,
  name    text NOT NULL,
  dept_id int,
  salary  int
);
INSERT INTO dept VALUES (10,'sales'), (20,'dev'), (30,'hr');
INSERT INTO emp  VALUES (1,'ann',10,300), (2,'bob',10,500), (3,'cho',20,NULL), (4,'dan',NULL,400);
```

MySQL 은 `text` → `varchar(20)` 만 바꾸면 같다.

</details>

## 동작 방식

이 절이 이 문서의 본문이다. **여덟 칸을 하나씩, 「무엇이 들어와서 무엇이 나가는가」로만** 본다.

아래 질의 하나를 여덟 칸에 통과시킨다.

```sql
SELECT   dept_id, COUNT(*) AS cnt
FROM     emp
WHERE    salary IS NOT NULL
GROUP BY dept_id
HAVING   COUNT(*) >= 1
ORDER BY cnt DESC
LIMIT    1;
```

실제 결과 — **돌린 것이다**:

```text
PG 18.6                          MySQL 8.4.10
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   2                   +---------+-----+
(1 row)                          |      10 |   2 |
                                 +---------+-----+
```

한 행이 나왔다. 그 한 행이 **여덟 칸을 어떻게 지나왔는지**를 이제 칸마다 그린다.

---

### 1. FROM — 표 하나를 만든다

**언제 쓰나** — 모든 질의의 첫 칸. 읽을 표가 무엇인지 정하고, 표가 여럿이면 **먼저 붙여 하나로 만든다.**

```text
(전) 디스크에 있는 emp 테이블
+----+------+---------+--------+
|  1 | ann  |      10 |    300 |
|  2 | bob  |      10 |    500 |
|  3 | cho  |      20 |   NULL |
|  4 | dan  |    NULL |    400 |
+----+------+---------+--------+
   ↓ FROM emp
(후) 작업 중인 행 집합 — 4행
```

표가 둘이면 이 칸에서 **모든 짝을 만든 뒤 `ON` 으로 거른다.**

```text
(전) emp 4행 · dept 3행
   ↓ FROM emp e CROSS JOIN dept d
(후) 4 x 3 = 12행
```

```text
### SQL: SELECT COUNT(*) AS cross_rows FROM emp e CROSS JOIN dept d;
--- PG 18.6 ---
 cross_rows
------------
         12
--- MySQL 8.4.10 ---
+------------+
| cross_rows |
+------------+
|         12 |
+------------+
```

그림 해설 — `FROM` 이 끝난 시점에 **행 수가 최대**가 된다. 뒤의 칸들은 전부 이 행 수를 줄이거나 묶는 일만 한다.\
대가 — 조인 조건을 빠뜨리면 여기서 만들어진 12행(일반적으로 N x M)이 그대로 다음 칸으로 간다. 표가 10만 x 10만이면 100억 행이다.

> 조인의 형태별 규칙은 이 주제 밖이다 — 목록의 12~20번, 그중 `FULL OUTER` 는 [16번](../16-full-outer-join/)이 정본이다.

---

### 2. WHERE — 행을 버린다

**언제 쓰나** — 개별 행 하나만 보고 판정할 수 있는 조건. 그룹을 아직 만들지 않았으므로 **집계 함수는 여기 못 온다.**

```text
(전) 4행                          (후) 3행
+----+------+--------+           +----+------+--------+
|  1 | ann  |    300 |           |  1 | ann  |    300 |
|  2 | bob  |    500 |  WHERE    |  2 | bob  |    500 |
|  3 | cho  |   NULL |  ------>  |  4 | dan  |    400 |
|  4 | dan  |    400 |  salary   +----+------+--------+
+----+------+--------+  IS NOT
                        NULL        cho 가 사라졌다
```

```text
### SQL: SELECT COUNT(*) AS step2_where FROM emp WHERE salary IS NOT NULL;
--- PG 18.6 ---
 step2_where
-------------
           3
--- MySQL 8.4.10 ---
+-------------+
| step2_where |
+-------------+
|           3 |
+-------------+
```

그림 해설 — `WHERE` 는 조건이 **`TRUE` 인 행만** 통과시킨다. `FALSE` 와 `UNKNOWN` 은 똑같이 버린다.\
대가 — 여기서 못 거른 행은 3·4·5번 칸을 전부 거쳐야 한다. 거를 수 있는 조건을 `HAVING` 으로 미루면 그만큼 일이 늘어난다.

집계 함수를 여기 쓰면 두 엔진 다 거부한다.

```text
### SQL: SELECT dept_id FROM emp WHERE COUNT(*) > 1 GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  aggregate functions are not allowed in WHERE
--- MySQL 8.4.10 ---
ERROR 1111 (HY000): Invalid use of group function
```

> **UNKNOWN** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
> 예: `NULL IS NOT NULL` 은 `FALSE` 지만, `NULL > 400` 은 `UNKNOWN` 이다. 왜 그런지는 [04번](../04-null-three-valued-logic/)이 정본이다.

---

### 3. GROUP BY — 행을 묶어 그룹 하나당 한 행으로 만든다

**언제 쓰나** — 여러 행을 하나로 접어야 할 때. 이 칸을 지나면 **행의 단위가 바뀐다** — 사원 한 명이 아니라 부서 한 개가 한 행이다.

```text
(전) 3행                          (후) 2그룹
+----+------+---------+          dept_id=10  { ann, bob }
|  1 | ann  |      10 |   GROUP  dept_id=NULL { dan }
|  2 | bob  |      10 |  ------>
|  4 | dan  |    NULL |   BY
+----+------+---------+   dept_id
```

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp
         WHERE salary IS NOT NULL GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---
 dept_id | cnt
---------+-----
      10 |   2
    NULL |   1
--- MySQL 8.4.10 ---
+---------+-----+
| dept_id | cnt |
+---------+-----+
|    NULL |   1 |
|      10 |   2 |
+---------+-----+
```

그림 해설 — `dept_id` 가 `NULL` 인 행들은 **하나의 그룹으로 묶인다.** 비교에서는 `NULL = NULL` 이 참이 아닌데 여기서는 같은 그룹이다 — `GROUP BY` 는 등호가 아니라 *구별 불가능성*으로 묶기 때문이다.\
대가 — 묶고 나면 **묶이기 전의 개별 행은 더 못 본다.** 그래서 다음 칸부터는 「그룹 키」와 「집계 결과」만 쓸 수 있다.

묶이지 않은 열을 `SELECT` 에 두면 두 엔진 다 거부한다.

```text
### SQL: SELECT dept_id, name FROM emp GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  column "emp.name" must appear in the GROUP BY clause or be used in an aggregate function
--- MySQL 8.4.10 ---
ERROR 1055 (42000): Expression #2 of SELECT list is not in GROUP BY clause and contains
  nonaggregated column 'study.emp.name' which is not functionally dependent on columns in
  GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

MySQL 이 거부하는 근거가 **`sql_mode=only_full_group_by`** 라는 점은 기억해 둘 값어치가 있다 — 그건 *설정*이라 끌 수 있다. 자세한 규칙은 목록의 22번 주제다.

---

### 4. HAVING — 그룹을 버린다

**언제 쓰나** — 「그룹 전체를 봐야」 판정되는 조건. `COUNT(*) >= 2`, `MAX(salary) >= 400` 처럼.

```text
(전) 2그룹                        (후) 2그룹 (이번엔 아무것도 안 잘림)
dept_id=10   cnt=2   HAVING      dept_id=10   cnt=2
dept_id=NULL cnt=1   ------->    dept_id=NULL cnt=1
                     COUNT(*)>=1
```

`WHERE` 와 `HAVING` 은 **같은 말을 해도 다른 답을 낸다.** 같은 데이터에 둘을 나란히 돌린 결과다.

```text
(A) WHERE 로 거른다 — 행을 먼저 버린다
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp
         WHERE salary >= 400 GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   1                   +---------+-----+
    NULL |   1                   |    NULL |   1 |
(2 rows)                         |      10 |   1 |
                                 +---------+-----+

(B) HAVING 으로 거른다 — 그룹을 통째로 남긴다
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

두 그림의 결론 — **`dept_id=10` 의 `cnt` 가 1과 2로 갈린다.**\
(A)는 `ann`(300)을 **먼저 버리고** 셌고, (B)는 `ann` 을 포함해 센 뒤 그룹을 **통째로 살릴지** 정했다.\
대가 — `HAVING` 은 그룹을 다 만든 뒤에 버린다. 행 단위로 판정 가능한 조건을 `HAVING` 에 두면 만들 필요 없던 그룹까지 만든다.

---

### 5. SELECT — 열을 만든다 (별칭이 여기서 태어난다)

**언제 쓰나** — 앞 칸들이 확정한 행 집합에서 **무엇을 내보낼지** 고르고 계산하는 자리. 다섯 번째다.

```text
(전) 2그룹 (키 + 집계값)          (후) 2행 x 2열, 두 번째 열에 이름 cnt 가 붙는다
dept_id=10   [rows: ann,bob]     +---------+-----+
dept_id=NULL [rows: dan]         | dept_id | cnt |
        ↓ SELECT dept_id,        +---------+-----+
          COUNT(*) AS cnt        |      10 |   2 |
                                 |    NULL |   1 |
                                 +---------+-----+
                                            ^
                                    이 이름이 지금 생겼다
```

그림 해설 — **`cnt` 라는 이름은 이 칸에서 처음 존재하게 된다.** 2번 칸(`WHERE`)·4번 칸(`HAVING`)은 이미 지나갔다.\
대가 — 별칭을 앞 칸에서 쓰려면 식을 **다시 적어야** 한다(`WHERE salary * 12 > 4000`).

**별칭을 `WHERE` 에서 쓰면** — 두 엔진 다 "그런 열 없다"고 한다.

```text
### SQL: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 1: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
                                                    ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22): Unknown column 'annual' in 'where clause'
```

**별칭을 `ORDER BY` 에서 쓰면** — 된다. 7번 칸은 5번 칸 뒤에 있으니까.

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

> **덤으로 보이는 차이** — 같은 `ORDER BY annual` 인데 `NULL` 의 자리가 반대다.\
> PG 는 `ASC` 에서 `NULL` 을 **맨 뒤**(큰 값 취급), MySQL 은 **맨 앞**(작은 값 취급)에 둔다.\
> 이건 순서 주제가 아니라 정렬 주제다 — 목록의 08번.

#### 방언 — `HAVING` 에서 별칭이 되나

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `WHERE` 에서 별칭 | ✗ | ✗ |
| `GROUP BY` 에서 별칭 | ✓ | ✓ |
| `HAVING` 에서 별칭 | **✗** | **✓** |
| `ORDER BY` 에서 별칭 | ✓ | ✓ |

같은 문 하나를 양쪽에 던진 실제 출력이다.

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

PG 문서는 이 규칙을 한 문장으로 적어 두었다 — 출력 열 이름은 `ORDER BY`·`GROUP BY` 에서 쓸 수 있고 `WHERE`·`HAVING` 에서는 못 쓴다([SELECT 페이지](https://www.postgresql.org/docs/18/sql-select.html)).\
**MySQL 에서 돌아가던 질의를 PG 로 옮기면 여기서 깨진다.** 반대 방향은 안 깨진다.

`GROUP BY` 에서 별칭이 되는 것도 양쪽 다 확인했다.

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

> `ORDER BY` 가 없으니 행 순서는 **보장되지 않는다.** 위 두 출력의 줄 순서가 다른 것은 그 탓이지 방언 차이가 아니다.

---

### 6. DISTINCT — 남은 행에서 중복을 지운다

**언제 쓰나** — `SELECT` 가 만든 **결과 행**에서 똑같은 것을 하나로 접을 때.

```text
(전) SELECT 가 만든 salary 열     (후) DISTINCT
   300                              300
   500                              500
  NULL                             NULL   <- NULL 끼리는 하나로 접힌다
   400                              400
```

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

그림 해설 — `DISTINCT` 는 **`SELECT` 가 내놓은 열만** 본다. `SELECT` 목록에 없는 열은 이 시점에 이미 없다.\
그래서 `SELECT` 에 없는 열로 정렬하려 하면 두 엔진 다 막는다.

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
--- PG 18.6 ---
ERROR:  for SELECT DISTINCT, ORDER BY expressions must appear in select list
--- MySQL 8.4.10 ---
ERROR 3065 (HY000): Expression #1 of ORDER BY clause is not in SELECT list, references
  column 'study.emp.salary' which is not in SELECT list; this is incompatible with DISTINCT
```

이 에러 하나가 **순서를 증명한다** — `DISTINCT`(6) 가 `ORDER BY`(7) 보다 먼저라서, 정렬할 때는 `salary` 가 이미 사라진 뒤다.\
대가 — 중복 제거는 정렬이나 해시를 부른다. 결과가 크면 여기가 병목이 된다.

---

### 7. ORDER BY — 줄을 세운다

**언제 쓰나** — 결과의 **행 순서**를 정할 때. 이 칸이 없으면 순서는 **보장이 없다.**

```text
(전) 순서 보장 없음               (후) cnt 내림차순
 dept_id | cnt                    dept_id | cnt
    NULL |   1        ORDER BY       10   |   2
      10 |   2        ------>      NULL   |   1
                      cnt DESC
```

`ORDER BY` 는 5번 칸을 지난 뒤라서 **별칭·서수·`SELECT` 에 없는 열**까지 쓸 수 있다(단 `DISTINCT` 가 없을 때).

```text
### SQL: SELECT dept_id, COUNT(*) FROM emp GROUP BY dept_id ORDER BY 2 DESC, 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | count                 +---------+----------+
---------+-------                | dept_id | COUNT(*) |
      10 |     2                 +---------+----------+
      20 |     1                 |      10 |        2 |
    NULL |     1                 |    NULL |        1 |
(3 rows)                         |      20 |        1 |
                                 +---------+----------+
```

그림 해설 — `2` 는 「출력 두 번째 열」, `1` 은 「출력 첫 번째 열」이다. 서수가 되는 것도 별칭이 되는 것과 같은 이유다 — 출력 열이 **이미 만들어져 있다.**\
같은 `cnt=1` 인 두 행의 순서가 엔진마다 다른 것은 앞서 본 `NULL` 정렬 차이다(PG 는 `NULL` 이 큼, MySQL 은 작음).\
대가 — 정렬은 결과 전체를 봐야 끝난다. `LIMIT 10` 을 붙여도 **정렬은 전부 해야** 상위 10개를 안다.

---

### 8. LIMIT — 잘라낸다

**언제 쓰나** — 마지막 칸. 정렬된 결과에서 앞 n 개만 가져온다.

```text
(전) 2행                          (후) 1행
 dept_id | cnt        LIMIT 1      dept_id | cnt
      10 |   2        ------>           10 |   2
    NULL |   1
```

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

그림 해설 — `OFFSET 1` 은 **정렬 뒤**에 1행을 건너뛴다. 「건너뛴다」는 건 만들긴 다 만들었다는 뜻이다.\
대가 — `LIMIT` 은 **일을 줄여 주지 않는다.** 앞 일곱 칸은 다 돌았다. `OFFSET 100000` 이 느린 이유가 이것이다(목록의 09번).

> `ORDER BY` 없는 `LIMIT` 은 **어느 행이 올지 정해지지 않는다.** 같은 질의가 같은 답을 준다는 보장이 없다.

## 문법 — 형태와 규칙

여덟 절의 **적는 순서**는 고정이다. 순서를 바꿔 적으면 파싱 자체가 안 된다.

```sql
SELECT   [DISTINCT] <출력 열 목록>
FROM     <표 또는 조인>
WHERE    <행 조건>
GROUP BY <그룹 키>
HAVING   <그룹 조건>
ORDER BY <정렬 키> [ASC|DESC]
LIMIT    <개수> [OFFSET <건너뛸 수>]
```

규칙을 넷으로 줄이면 이렇다.

1. **`SELECT` 목록의 별칭은 `SELECT` 이후 칸에서만 보인다.**\
   보이는 곳: `ORDER BY` · `GROUP BY`(양쪽 엔진) · `HAVING`(MySQL 만).\
   안 보이는 곳: `WHERE`(양쪽 엔진) · `HAVING`(PG).
2. **집계 함수는 `WHERE` 에 못 쓴다.** 그룹이 아직 없기 때문이다. 같은 이유로 윈도우 함수도 못 쓴다.
3. **`GROUP BY` 뒤에는 「그룹 키」와 「집계값」만 남는다.** 그 외 열을 `SELECT` 에 두면 거부된다.
4. **`ORDER BY` 는 `DISTINCT` 뒤다.** `DISTINCT` 가 있으면 정렬 키가 `SELECT` 목록 안에 있어야 한다.

`SELECT` 목록에서 별칭이 **기존 열 이름을 가리는 경우**가 특히 헷갈린다. 던져 봤다.

```text
(A) WHERE 에서는 원래 열을 본다 — 별칭은 아직 없으니까
### SQL: SELECT id AS salary FROM emp WHERE salary > 400;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
      2                          +--------+
(1 row)                          |      2 |
                                 +--------+
  -> salary > 400 은 emp.salary(=500, bob) 로 판정됐고, 출력된 값 2 는 bob 의 id 다

(B) ORDER BY 에서는 별칭을 본다 — 이미 만들어졌으니까
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
  -> id 순(1,2,3,4)이다. salary 순(300,400,500,NULL)이 아니다
```

두 그림의 결론 — **같은 이름 `salary` 가 2번 칸에서는 원래 열, 7번 칸에서는 별칭을 가리킨다.** 순서를 모르면 이 질의는 읽을 수 없다.

## 어디서 틀리나

- **별칭을 `WHERE` 에 쓴다.**\
  가장 흔하다. 고치는 법은 두 가지 — 식을 다시 적거나, 서브쿼리/CTE 로 한 겹 감싸 별칭을 「이전 칸의 결과」로 만든다.
- **`HAVING` 별칭이 MySQL 에서만 된다는 걸 모른다.**\
  MySQL 로 개발하고 PG 로 배포하면 여기서 깨진다. 위 출력이 그 증거다.
- **거를 수 있는 조건을 `HAVING` 에 둔다.**\
  결과가 같아 보여도 다르다 — `WHERE salary >= 400` 과 `HAVING MAX(salary) >= 400` 은 위에서 봤듯 `cnt` 가 1과 2로 갈린다.
- **`LIMIT` 을 붙이면 빨라질 거라 믿는다.**\
  여덟 번째 칸이다. 앞 일곱 칸의 일은 그대로다.
- **`ORDER BY` 없이 `LIMIT` 을 쓴다.**\
  "지금은 잘 나오는데요"는 보장이 아니다. 계획이 바뀌면 다른 행이 온다.
- **윈도우 함수 결과를 `WHERE` 로 거르려 한다.**\
  윈도우 함수는 `SELECT` 칸에서 계산된다. 두 엔진 다 거부한다.

```text
### SQL: SELECT name, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM emp
         WHERE ROW_NUMBER() OVER (ORDER BY id) = 1;
--- PG 18.6 ---
ERROR:  window functions are not allowed in WHERE
--- MySQL 8.4.10 ---
ERROR 3593 (HY000): You cannot use the window function 'row_number' in this context.'
```

  고치는 법은 한 겹 감싸는 것이다 — 안쪽 질의가 「이전 칸」이 되면 바깥에서는 그냥 열이다(목록의 31번).

## 언제 쓰고 언제 안 쓰나

이 주제는 「쓸지 말지」를 고르는 문법이 아니라 **다른 모든 SQL 주제를 읽는 좌표계**다. 그래서 판단 기준은 이렇다.

- **"왜 이 열이 여기서 안 되지"** 를 만났을 때 — 먼저 이 순서를 떠올린다. 답의 대부분이 "그 칸에서는 아직/이미 없다"다.
- **결과 행 수가 예상과 다를 때** — 어느 칸에서 행 수가 변했는지 칸마다 잘라 세어 본다(`FROM` → `WHERE` → `GROUP BY` 순으로 `COUNT(*)`).
- **성능이 문제일 때는 이 순서를 그대로 믿지 않는다.** 이건 *결과의 정의*이지 *실행 계획*이 아니다. 실제로 무엇을 먼저 했는지는 `EXPLAIN` 이 말한다(목록의 58번).

## 핵심 문장

- SQL 은 **적는 순서와 일하는 순서가 다르다** — `FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT`.
- 별칭은 **5번 칸(`SELECT`)에서 태어난다.** 그래서 2번 칸에서는 없고 7번 칸에서는 있다.
- `WHERE` 는 **행**을 버리고 `HAVING` 은 **그룹**을 버린다. 같은 말을 해도 답이 갈린다.
- `LIMIT` 은 **마지막 칸**이다. 앞의 일을 줄여 주지 않는다.
- 이 순서는 **결과의 정의**이지 실행 계획이 아니다.

## 관련 자료

- [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) — 처리 순서와 출력 열 이름 규칙이 같은 페이지에 있다.
- [MySQL 8.4 · SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html)
- [SQL 주제 목록](../README.md) — 이 주제를 선행으로 거는 것이 13개다.
- 같은 예시 테이블을 쓰는 형제 주제: [04 NULL 의 3값 논리](../04-null-three-valued-logic/) · [16 FULL OUTER JOIN](../16-full-outer-join/) · [52 UPSERT](../52-upsert/)

## 용어 풀이

- **논리적 처리 순서** — 엔진이 결과를 정의하는 여덟 칸의 순서. 실행 순서와는 다를 수 있다.\
  예: 옵티마이저가 `WHERE` 를 조인 안쪽으로 밀어 넣어도 결과는 같아야 한다.
- **별칭(alias)** — `AS` 로 붙인 새 이름. 열 별칭과 테이블 별칭이 있다.\
  예: `COUNT(*) AS cnt` 의 `cnt`.
- **집계 함수(aggregate function)** — 여러 행을 하나의 값으로 접는 함수.\
  예: `COUNT(*)`·`SUM(salary)`·`MAX(salary)`.
- **윈도우 함수(window function)** — 행을 접지 않고 **행마다** 값을 붙이는 계산. `OVER (...)` 가 붙는다.\
  예: `ROW_NUMBER() OVER (ORDER BY id)` 는 행마다 1, 2, 3 을 붙인다.
- **그룹 키(group key)** — `GROUP BY` 에 적은 열. 결과 행 하나가 무엇을 뜻하는지 정한다.\
  예: `GROUP BY dept_id` 면 결과 한 행 = 부서 하나.
- **서수(ordinal)** — `ORDER BY 2` 처럼 열 이름 대신 쓰는 출력 열 번호.\
  예: `ORDER BY 2 DESC` = 두 번째 출력 열 내림차순.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
  예: `NULL > 400` 의 결과. `WHERE` 는 이것을 `FALSE` 와 똑같이 버린다.
- **카티션곱(Cartesian product)** — 두 표의 모든 행 조합. `FROM` 에서 조인 조건이 없을 때 나온다.\
  예: 4행 x 3행 = 12행.
- **`sql_mode`** — MySQL 의 문법·검사 엄격도 설정 묶음.\
  예: `only_full_group_by` 가 켜져 있어야 묶이지 않은 열을 거부한다. 8.4 기본값에는 들어 있다.
- **`OFFSET`** — 정렬된 결과에서 앞의 n 행을 건너뛰는 지시.\
  예: `LIMIT 2 OFFSET 1` 은 2번째·3번째 행을 준다. 1번째도 만들긴 만든다.
