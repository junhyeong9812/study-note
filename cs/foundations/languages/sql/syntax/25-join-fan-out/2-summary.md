# sql/25-조인 팬아웃 — 행 수와 집계가 틀어지는 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Joined Tables](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — 이 주제에서 버전·방언에 갈리는 것은 **없다.** 세 처방(선집계·`COUNT(DISTINCT)`·`LATERAL`)이 **두 엔진에서 같은 답을 냈다.**\
> **선행** — [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) · [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/).\
> **이 묶음의 정점이다** — [21](../21-aggregate-functions-count-forms/)·[22](../22-group-by-nonaggregated-columns/)에서 배운 것이 [13](../13-inner-join/)·[14](../14-left-right-outer-join/)의 조인 위에서 어떻게 틀어지나.

## 한눈에 — 쉽게 말하면

**사원 명단에 「참여 프로젝트」 표를 붙이면, 두 프로젝트에 낀 사람은 명단에 **두 줄**이 된다.\
그리고 그 두 줄에 **급여가 각각 딸려 온다.** 합치면 그 사람 급여가 **두 번** 더해진다.**

- 사원 4명의 총 인건비는 **1,200** 이다.
- 프로젝트 배정표를 `LEFT JOIN` 으로 붙이면 행이 **6개**가 된다.
- 그 위에서 `SUM(salary)` 를 하면 — **2,000** 이 나온다. **800 이 허공에서 생겼다.**

| 비유 | 실체 | 결과 |
|---|---|---|
| 명단에 사람이 여러 줄 생김 | **팬아웃** — 1:N 조인이 보존 측 행을 복제 | 4행 → 6행 |
| 줄마다 급여가 딸려 옴 | 복제된 행에 원래 열이 그대로 실린다 | `ann` 의 300 이 두 줄에 |
| 그걸 다 더함 | `SUM` 이 중복을 모른다 | 1,200 → **2,000** |
| 사람 수만 셈 | `COUNT(DISTINCT e.id)` 는 중복을 접는다 | **4** — 안 부푼다 |

```text
조인 전 (emp 4행)                  조인 후 (6행)
+----+------+--------+             +----+------+--------+------+
| id | name | salary |             | id | name | salary | proj |
+----+------+--------+             +----+------+--------+------+
|  1 | ann  |    300 |             |  1 | ann  |    300 | p1   |  <- 300 이
|  2 | bob  |    500 |   ──LEFT    |  1 | ann  |    300 | p2   |  <- 두 줄에
|  3 | cho  |   NULL |    JOIN──>  |  2 | bob  |    500 | p1   |
|  4 | dan  |    400 |             |  2 | bob  |    500 | p3   |
+----+------+--------+             |  3 | cho  |   NULL | p2   |
   SUM(salary) = 1200              |  4 | dan  |    400 | p1   |
                                   +----+------+--------+------+
                                      SUM(salary) = 2000   <- 틀린 값
```

**이 명단이 똑같은 구조로** 조인 팬아웃이다.\
★ **문법은 한 글자도 틀리지 않았고 에러도 안 난다.** 숫자만 조용히 커진다 — **그래서 이 주제가 위험하다.**

> **팬아웃(fan-out)** — 1:N 조인에서 한쪽 행이 상대의 짝 수만큼 **복제**되는 현상.\
> 예: `ann` 이 프로젝트 둘에 끼어 있어 조인 결과에 두 줄이 된다.

> **부풀린 집계(inflated aggregate)** — 복제된 행을 그대로 더해 실제보다 커진 합계.\
> 예: 인건비 1,200 이 2,000 으로 나온 것. **에러가 아니라 「맞게 계산된 틀린 값」이다.**

## 이 주제가 답하려는 질문

1. **조인이 행을 몇 배로 늘리나?** — 그리고 그걸 **미리 알 수 있나.**
2. **★ 어느 집계가 부풀고 어느 집계가 안 부푸나?** — `SUM` 은 부풀고 `COUNT(DISTINCT)` 는 안 부푼다.
3. **고치는 법이 무엇이고, 어느 상황에 어느 것을 쓰나?** — 셋이 있고 셋이 다른 값을 한다.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들은 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

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
```

**팬아웃을 보이려면 1:N 이 필요한데 `emp`·`dept` 는 그걸 못 만든다** — 사원 한 명이 부서 하나에만 속하기 때문이다.\
★ 그래서 **표를 새로 만들지 않고 CTE 로 배정표를 얹는다.** `study` DB 에는 아무것도 남지 않는다.

```sql
WITH asg(emp_id, proj) AS (
  SELECT 1,'p1' UNION ALL SELECT 1,'p2'      -- ann : 2 개
  UNION ALL SELECT 2,'p1' UNION ALL SELECT 2,'p3'  -- bob : 2 개
  UNION ALL SELECT 3,'p2'                    -- cho : 1 개
  UNION ALL SELECT 4,'p1')                   -- dan : 1 개
```

```text
### SQL: WITH asg(...) AS (...) SELECT * FROM asg ORDER BY emp_id, proj;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp_id | proj                   +--------+------+
--------+------                  | emp_id | proj |
      1 | p1                     +--------+------+
      1 | p2                     |      1 | p1   |
      2 | p1                     |      1 | p2   |
      2 | p3                     |      2 | p1   |
      3 | p2                     |      2 | p3   |
      4 | p1                     |      3 | p2   |
(6 rows)                         |      4 | p1   |
                                 +--------+------+
```

- `asg` 는 **`emp_id` 와 `proj` 어느 쪽도 유일하지 않다** — 진짜 다대다다(`p1` 에 세 명, `ann` 에 두 프로젝트).
- ★ **`WITH … AS (SELECT … UNION ALL …)` 형태가 두 엔진에서 그대로 돈다.** `VALUES` 행 생성자는 **PG 와 MySQL 이 서로를 거부**하므로([10번](../10-from-clause-aliases-derived-tables/)) 이식 가능한 이 형태를 골랐다.
- **표를 만들지 않았으므로 지울 것도 없다.** 롤백도 필요 없다.

<details>
<summary>emp·dept 를 만드는 문 (PostgreSQL)</summary>

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

### 1. 조인이 행을 늘린다 — 몇 배인지 먼저 센다

**언제 쓰나** — 조인 뒤에 집계를 씌우기 전에. **매번.**

```text
 emp 4행                     asg 6행                 조인 결과 6행
+----+--------+             +--------+------+       +----+--------+------+
|  1 |    300 |             |      1 | p1   |       |  1 |    300 | p1   |
|  2 |    500 |  ON e.id =  |      1 | p2   |  ==>  |  1 |    300 | p2   |
|  3 |   NULL |  a.emp_id   |      2 | p1   |       |  2 |    500 | p1   |
|  4 |    400 |             |      2 | p3   |       |  2 |    500 | p3   |
+----+--------+             |      3 | p2   |       |  3 |   NULL | p2   |
                            |      4 | p1   |       |  4 |    400 | p1   |
                            +--------+------+       +----+--------+------+
   왼쪽 한 행이 오른쪽 짝 수만큼 복제된다 (ann 2 · bob 2 · cho 1 · dan 1)
```

```text
### SQL: WITH asg(...) AS (...)
         SELECT e.id, e.name, e.salary, a.proj FROM emp e LEFT JOIN asg a ON a.emp_id = e.id
         ORDER BY e.id, a.proj;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | salary | proj       +----+------+--------+------+
----+------+--------+------      | id | name | salary | proj |
  1 | ann  |    300 | p1         +----+------+--------+------+
  1 | ann  |    300 | p2         |  1 | ann  |    300 | p1   |
  2 | bob  |    500 | p1         |  1 | ann  |    300 | p2   |
  2 | bob  |    500 | p3         |  2 | bob  |    500 | p1   |
  3 | cho  |   NULL | p2         |  2 | bob  |    500 | p3   |
  4 | dan  |    400 | p1         |  3 | cho  |   NULL | p2   |
(6 rows)                         |  4 | dan  |    400 | p1   |
                                 +----+------+--------+------+
```

그림 해설 — ★ **`ann` 의 급여 300 이 두 줄에 실려 있다.** 복제된 것은 행 전체이지 키만이 아니다.\
[13번](../13-inner-join/)에서 「한쪽에 짝이 여럿이면 행이 분다」를 배웠고, [14번](../14-left-right-outer-join/)에서 「`LEFT` 여도 는다」를 봤다. **여기서 그 행들이 집계로 들어간다.**

**행 수를 세는 것이 첫 습관이다.**

```text
### SQL: WITH asg(...) AS (...)
         SELECT (SELECT COUNT(*) FROM emp) AS before_join, COUNT(*) AS after_join
         FROM emp e LEFT JOIN asg a ON a.emp_id = e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 before_join | after_join        +-------------+------------+
-------------+------------       | before_join | after_join |
           4 |          6        +-------------+------------+
(1 row)                          |           4 |          6 |
                                 +-------------+------------+
```

★ **4 → 6 이면 팬아웃이 있다.** 같으면 1:1 이라 집계가 안전하다.\
비용 — 질의 하나. **이 한 줄을 안 던져서 나는 사고가 이 주제의 전부다.**

---

### 2. ★ `SUM` 은 부풀고 `COUNT(DISTINCT)` 는 안 부푼다

**언제 쓰나** — 조인 결과 위에서 집계를 볼 때. **이 절이 이 주제의 중심이다.**

먼저 **참값**을 본다.

```text
### SQL: SELECT SUM(salary) AS payroll, COUNT(*) AS c FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 payroll | c                     +---------+---+
---------+---                    | payroll | c |
    1200 | 4                     +---------+---+
(1 row)                          |    1200 | 4 |
                                 +---------+---+
```

**같은 질문을 조인 뒤에 던진다.**

```text
### SQL: WITH asg(...) AS (...)
         SELECT SUM(e.salary) AS payroll, COUNT(*) AS c, COUNT(e.id) AS c_id, COUNT(DISTINCT e.id) AS c_dist
         FROM emp e LEFT JOIN asg a ON a.emp_id = e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 payroll | c | c_id | c_dist     +---------+---+------+--------+
---------+---+------+--------    | payroll | c | c_id | c_dist |
    2000 | 6 |    6 |      4     +---------+---+------+--------+
(1 row)                          |    2000 | 6 |    6 |      4 |
                                 +---------+---+------+--------+
```

그림 해설 — ★★ **`payroll` 이 1,200 에서 2,000 으로 뛰었다. 에러는 없다.**

```text
 무엇이 부풀었나

 SUM(e.salary)        300+300 + 500+500 + NULL + 400 = 2000   부풀었다 (참값 1200)
 COUNT(*)             6                                        부풀었다 (참값 4)
 COUNT(e.id)          6                                        부풀었다 (참값 4)
 COUNT(DISTINCT e.id) 4                                        안 부풀었다
                             ^^^^^^^^^^^^^^^^^^^^^^
            DISTINCT 가 복제된 id 를 도로 접는다
```

★ **`COUNT(DISTINCT)` 만 살아남는 이유** — 복제된 행의 `e.id` 는 **값이 같다.** `DISTINCT` 가 그것을 한 번으로 접는다.\
`SUM` 에는 그런 장치가 없다. **같은 값을 여러 번 더하는 것이 `SUM` 의 정의**이기 때문이다.

**그룹별로 보면 배율이 정확히 보인다.**

```text
### SQL: WITH asg(...) AS (...)
         SELECT e.dept_id, SUM(e.salary) AS payroll, COUNT(*) AS c, COUNT(DISTINCT e.id) AS heads
         FROM emp e LEFT JOIN asg a ON a.emp_id = e.id GROUP BY e.dept_id ORDER BY e.dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | payroll | c | heads   +---------+---------+---+-------+
---------+---------+---+-------  | dept_id | payroll | c | heads |
      10 |    1600 | 4 |     2   +---------+---------+---+-------+
      20 |    NULL | 1 |     1   |    NULL |     400 | 1 |     1 |
    NULL |     400 | 1 |     1   |      10 |    1600 | 4 |     2 |
(3 rows)                         |      20 |    NULL | 1 |     1 |
                                 +---------+---------+---+-------+
```

```text
 sales(dept_id=10) 부서
   참값 인건비 = ann 300 + bob 500 = 800
   나온 값     = 1600                      정확히 2 배
       ^
   ann 도 bob 도 프로젝트가 2 개씩이라 둘 다 두 번 더해졌다
```

★ **`heads`(2)는 맞고 `payroll`(1600)은 틀렸다.** 같은 질의, 같은 줄인데 한 칸은 맞고 한 칸은 틀렸다.\
대가 — **검산할 기준이 없으면 못 잡는다.** 「인건비가 1,600 이다」는 그 자체로 이상해 보이지 않는다.

---

### 3. 조인이 둘이면 배율이 **곱해진다**

**언제 쓰나** — 조인이 셋 이상인 질의를 볼 때. 실무 질의는 대개 그렇다.

「참여 프로젝트」에 더해 「보유 기술」을 하나 더 붙인다.

```sql
skl(emp_id, skill) AS (
  SELECT 1,'java' UNION ALL SELECT 1,'sql' UNION ALL SELECT 1,'go'   -- ann : 3 개
  UNION ALL SELECT 2,'sql'                                            -- bob : 1 개
  UNION ALL SELECT 3,'go'                                             -- cho : 1 개
  UNION ALL SELECT 4,'sql')                                           -- dan : 1 개
```

```text
### SQL: WITH asg(...) AS (...), skl(...) AS (...)
         SELECT COUNT(*) AS rows_out, SUM(e.salary) AS payroll, COUNT(DISTINCT e.id) AS heads,
                COUNT(DISTINCT a.proj) AS projs, COUNT(DISTINCT s.skill) AS skills
         FROM emp e LEFT JOIN asg a ON a.emp_id = e.id LEFT JOIN skl s ON s.emp_id = e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 rows_out | payroll | heads | projs | skills
----------+---------+-------+-------+--------
       10 |    3200 |     4 |     3 |      3
(1 row)
+----------+---------+-------+-------+--------+
| rows_out | payroll | heads | projs | skills |
+----------+---------+-------+-------+--------+
|       10 |    3200 |     4 |     3 |      3 |
+----------+---------+-------+-------+--------+
```

```text
 사람마다 몇 줄이 되나 — 두 표의 짝 수가 곱해진다

 ann  프로젝트 2 x 기술 3 = 6 줄  ->  300 x 6 = 1800
 bob  프로젝트 2 x 기술 1 = 2 줄  ->  500 x 2 = 1000
 cho  프로젝트 1 x 기술 1 = 1 줄  ->  NULL
 dan  프로젝트 1 x 기술 1 = 1 줄  ->  400 x 1 =  400
                     합 10 줄            합   = 3200     (참값 1200)
```

★★ **배율이 더해지는 게 아니라 곱해진다.** 4행이 10행, 1,200 이 3,200 이 됐다.\
`ann` 한 사람이 **6줄**이고 그 급여가 여섯 번 더해졌다.

★ **`heads`·`projs`·`skills` 는 전부 맞다**(4·3·3). `COUNT(DISTINCT)` 는 조인이 몇 겹이든 안 부푼다.\
대가 — **`SUM` 만 못 쓴다.** 그리고 그 사실이 화면에 안 나타난다.

이것이 **[12번](../12-cartesian-product-cross-join/)의 카티션곱이 작게 되풀이되는 모습**이다 — 조인 조건이 있어도 **한쪽이 유일하지 않으면** 곱이 남는다.

---

### 4. 처방 하나 — 붙이기 전에 미리 접는다 (선집계 서브쿼리)

**언제 쓰나** — **기본 처방이다.** 상대 표에서 필요한 것이 「집계값」일 때 언제나.

```text
 팬아웃이 생기는 순서                 선집계로 막는 순서
 emp 4행                              emp 4행
   + asg 6행 (1:N)                      + (asg 를 emp_id 로 미리 접은) 4행 (1:1)
   = 6행  <- 여기서 부푼다               = 4행  <- 안 부푼다
   -> SUM 2000                          -> SUM 1200
```

```text
### SQL: WITH asg(...) AS (...)
         SELECT e.dept_id, SUM(e.salary) AS payroll, SUM(a.n) AS proj_cnt
         FROM emp e LEFT JOIN (SELECT emp_id, COUNT(*) AS n FROM asg GROUP BY emp_id) a
              ON a.emp_id = e.id
         GROUP BY e.dept_id ORDER BY e.dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | payroll | proj_cnt    +---------+---------+----------+
---------+---------+----------   | dept_id | payroll | proj_cnt |
      10 |     800 |        4    +---------+---------+----------+
      20 |    NULL |        1    |    NULL |     400 |        1 |
    NULL |     400 |        1    |      10 |     800 |        4 |
(3 rows)                         |      20 |    NULL |        1 |
                                 +---------+---------+----------+
```

그림 해설 — ★ **`payroll` 이 800 으로 돌아왔다.** 그리고 `proj_cnt` 도 같이 얻었다(sales 부서 4건).\
서브쿼리가 `asg` 를 `emp_id` 당 한 행으로 접었기 때문에 **조인이 1:1 이 되고 복제가 없다.**

```text
 서브쿼리가 만든 표
 +--------+---+
 | emp_id | n |     이제 emp_id 가 유일하다
 +--------+---+     -> 조인해도 emp 의 행이 안 는다
 |      1 | 2 |
 |      2 | 2 |
 |      3 | 1 |
 |      4 | 1 |
 +--------+---+
```

대가 — **상대 표를 한 번 더 훑는다.** 그리고 **필요한 집계를 미리 정해야 한다** — 나중에 다른 각도가 필요하면 서브쿼리를 고쳐야 한다.\
파생 테이블의 별칭 규칙은 [10번](../10-from-clause-aliases-derived-tables/)이 정본이다(MySQL 은 별칭 **필수**).

---

### 5. 처방 둘 — `COUNT(DISTINCT)`. 단 `SUM(DISTINCT)` 은 **함정**이다

**언제 쓰나** — 세는 것이 목적일 때. **더하는 것이 목적이면 쓰면 안 된다.**

2번에서 봤듯 `COUNT(DISTINCT e.id)` 는 팬아웃을 견딘다. **그래서 「`DISTINCT` 를 붙이면 되는구나」로 넘어가기 쉽다.**

```text
### SQL: WITH asg(...) AS (...)
         SELECT SUM(DISTINCT e.salary) AS sum_dist, SUM(e.salary) AS sum_plain
         FROM emp e LEFT JOIN asg a ON a.emp_id = e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 sum_dist | sum_plain            +----------+-----------+
----------+-----------           | sum_dist | sum_plain |
     1200 |      2000            +----------+-----------+
(1 row)                          |     1200 |      2000 |
                                 +----------+-----------+
```

★ **1,200 이 나왔다. 참값과 같다. 그런데 이건 우연이다.**\
`emp` 의 급여가 `300·500·NULL·400` 으로 **전부 달랐기 때문**이다.

**급여가 같은 두 사람을 넣어 보면 무너진다.**

```text
### SQL: WITH two(id, name, salary) AS (SELECT 1,'ann',300 UNION ALL SELECT 2,'eve',300),
              asg(emp_id, proj) AS (SELECT 1,'p1' UNION ALL SELECT 1,'p2' UNION ALL SELECT 2,'p1')
         SELECT SUM(t.salary) AS fanned, SUM(DISTINCT t.salary) AS sum_dist, COUNT(DISTINCT t.id) AS heads
         FROM two t JOIN asg a ON a.emp_id = t.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 fanned | sum_dist | heads       +--------+----------+-------+
--------+----------+-------      | fanned | sum_dist | heads |
    900 |      300 |     2       +--------+----------+-------+
(1 row)                          |    900 |      300 |     2 |
                                 +--------+----------+-------+
```

```text
 두 사람 다 급여 300, 참값 = 600

 SUM(t.salary)          900   부풀었다 (ann 이 두 줄)
 SUM(DISTINCT t.salary) 300   더 틀렸다 — eve 를 통째로 지웠다
 COUNT(DISTINCT t.id)     2   맞다
```

★★ **`SUM(DISTINCT)` 은 「중복 행」이 아니라 「중복 값」을 지운다.** 서로 다른 사람의 같은 급여를 한 번만 더한다.\
**팬아웃을 고치는 도구가 아니다.** 실데이터에서 값이 겹치는 순간 **부푼 값보다 더 틀린 값**을 낸다.

**세는 것이 목적이면 `COUNT(DISTINCT 키)` 가 맞다.**

```text
### SQL: WITH asg(...) AS (...)
         SELECT e.dept_id, COUNT(*) AS rows_out, COUNT(DISTINCT e.id) AS heads,
                COUNT(a.proj) AS asg_cnt, COUNT(DISTINCT a.proj) AS proj_kinds
         FROM emp e LEFT JOIN asg a ON a.emp_id = e.id GROUP BY e.dept_id ORDER BY e.dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | rows_out | heads | asg_cnt | proj_kinds
---------+----------+-------+---------+------------
      10 |        4 |     2 |       4 |          3
      20 |        1 |     1 |       1 |          1
    NULL |        1 |     1 |       1 |          1
(3 rows)
+---------+----------+-------+---------+------------+
| dept_id | rows_out | heads | asg_cnt | proj_kinds |
+---------+----------+-------+---------+------------+
|    NULL |        1 |     1 |       1 |          1 |
|      10 |        4 |     2 |       4 |          3 |
|      20 |        1 |     1 |       1 |          1 |
+---------+----------+-------+---------+------------+
```

★ **네 열이 각각 다른 질문의 답이다** — 「줄 수」·「사람 수」·「배정 건수」·「프로젝트 종류 수」.\
`asg_cnt`(4)와 `proj_kinds`(3)가 다른 것은 `p1` 이 두 번 나오기 때문이다. **어느 쪽이 원하는 답인지 먼저 정해야 한다.**

**행을 되돌린 뒤 집계하는 형태도 된다.**

```text
### SQL: WITH asg(...) AS (...)
         SELECT SUM(salary) AS payroll, COUNT(*) AS c
         FROM (SELECT DISTINCT e.id, e.salary FROM emp e LEFT JOIN asg a ON a.emp_id = e.id) t;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 payroll | c                     +---------+---+
---------+---                    | payroll | c |
    1200 | 4                     +---------+---+
(1 row)                          |    1200 | 4 |
                                 +---------+---+
```

★ **`DISTINCT` 를 `id` 와 함께 쓴 것이 요점이다** — `SELECT DISTINCT salary` 였다면 급여가 같은 두 사람이 한 행으로 접혔을 것이다.\
**기본키를 포함시키면 안전하다.** 대가는 중복 제거 비용이고, 4번보다 대개 비싸다.

---

### 6. 처방 셋 — `LATERAL` 로 행마다 따로 센다

**언제 쓰나** — 「사람마다 최근 N건」처럼 **행별로 다른 것을 뽑아야** 할 때. 집계 하나면 4번이 더 단순하다.

```text
 선집계 서브쿼리                      LATERAL
 상대 표를 한 번에 다 접는다           바깥 행 하나마다 안쪽을 다시 돈다
 (emp_id 전부에 대해 GROUP BY)        (e.id 를 참조해 그 사람 것만)
```

```text
### SQL: WITH asg(...) AS (...)
         SELECT e.name, x.n FROM emp e
         LEFT JOIN LATERAL (SELECT COUNT(*) AS n FROM asg a WHERE a.emp_id = e.id) x ON TRUE
         ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | n                        +------+------+
------+---                       | name | n    |
 ann  | 2                        +------+------+
 bob  | 2                        | ann  |    2 |
 cho  | 1                        | bob  |    2 |
 dan  | 1                        | cho  |    1 |
(4 rows)                         | dan  |    1 |
                                 +------+------+
```

**집계까지 씌워도 안 부푼다.**

```text
### SQL: WITH asg(...) AS (...)
         SELECT e.dept_id, SUM(e.salary) AS payroll, SUM(x.n) AS proj_cnt
         FROM emp e LEFT JOIN LATERAL (SELECT COUNT(*) AS n FROM asg a WHERE a.emp_id = e.id) x ON TRUE
         GROUP BY e.dept_id ORDER BY e.dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | payroll | proj_cnt    +---------+---------+----------+
---------+---------+----------   | dept_id | payroll | proj_cnt |
      10 |     800 |        4    +---------+---------+----------+
      20 |    NULL |        1    |    NULL |     400 |        1 |
    NULL |     400 |        1    |      10 |     800 |        4 |
(3 rows)                         |      20 |    NULL |        1 |
                                 +---------+---------+----------+
```

그림 해설 — **4번과 한 글자도 같은 결과다.** `LATERAL` 서브쿼리가 **행 하나를 돌려주므로** 조인이 1:1 이다.\
`ON TRUE` 가 붙는 이유는 조인 조건이 이미 안쪽 `WHERE` 에 들어가 있기 때문이다.

★ **두 엔진에서 다 돌았다.** `LATERAL` 의 문법·버전 세부는 [20번](../20-lateral-join/)이 정본이다 — **경계: 거기는 `LATERAL` 자체, 여기는 그것이 팬아웃 처방이 되는 이유.**

대가 — 바깥 행마다 안쪽을 돈다. **행이 많으면 비싸질 수 있다.** 집계 하나만 필요하면 4번이 낫다.\
★ **`LATERAL` 이 유일한 답이 되는 자리는 「행마다 상위 N건」이다** — 그건 집계로 접을 수 없다.

---

### 7. 계획에서 행이 어디서 불어나는지 보인다

**언제 쓰나** — 질의가 크고 어느 조인이 범인인지 모를 때.

```text
### SQL: EXPLAIN ANALYZE WITH asg(...) AS (...)
         SELECT SUM(e.salary) FROM emp e LEFT JOIN asg a ON a.emp_id = e.id;
--- PG 18.6 --- (필요한 세 줄만 옮긴 것이다)
 Aggregate  (cost=28.59..28.60 rows=1 width=8) (actual time=0.037..0.043 rows=1.00 loops=1)
   ->  Hash Left Join  (cost=0.17..25.76 rows=1130 width=4) (actual time=0.029..0.037 rows=6.00 loops=1)
         ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=8) (actual time=0.005..0.006 rows=4.00 loops=1)
```

```text
 계획을 아래에서 위로 읽는다

 Seq Scan on emp        rows=4.00     <- 표에서 4행을 읽었다
        |
 Hash Left Join         rows=6.00     <- 조인이 6행을 냈다.  여기서 불었다
        |
 Aggregate              rows=1.00     <- 그 6행을 하나로 접었다 (2000)
```

★ **`actual … rows=` 를 위아래로 비교하면 어느 노드가 행을 늘렸는지 보인다.**\
`4.00` → `6.00` 이 팬아웃이고, 그 위의 `Aggregate` 가 부푼 입력을 그대로 받았다.

**경계: 계획을 읽는 법 자체는 [목록의 58번 주제](../58-explain-plan-tree/), 연산자 이름은 59번 주제, 추정 대 실측의 격차는 60번 주제다.**\
여기서는 **「행이 어디서 늘었나」 한 가지만** 본다. `cost=` 와 `time=` 은 **이 주제에서 해석하지 않는다.**

## 문법 — 어느 절에서 무엇이 보이나

```sql
-- 위험한 형태 — 조인 결과 위에 바로 집계
SELECT SUM(e.salary) FROM emp e JOIN asg a ON a.emp_id = e.id;

-- (1) 선집계 — 상대 표를 미리 1행으로 접어 붙인다             <- 기본 처방
SELECT e.dept_id, SUM(e.salary)
FROM emp e LEFT JOIN (SELECT emp_id, COUNT(*) AS n FROM asg GROUP BY emp_id) a ON a.emp_id = e.id
GROUP BY e.dept_id;

-- (2) COUNT(DISTINCT 키) — 세는 것이 목적일 때
SELECT COUNT(DISTINCT e.id) FROM emp e JOIN asg a ON a.emp_id = e.id;

-- (3) LATERAL — 행마다 따로 계산할 때
SELECT e.name, x.n
FROM emp e LEFT JOIN LATERAL (SELECT COUNT(*) AS n FROM asg a WHERE a.emp_id = e.id) x ON TRUE;
```

규칙 여덟.

1. **조인 뒤 집계 전에 행 수를 센다.** `COUNT(*)` 이 조인 전후로 같으면 안전하다.
2. **배율 = 상대 표의 짝 수.** 조인이 둘이면 **곱해진다**(2 × 3 = 6줄).
3. ★ **`SUM`·`AVG`·`COUNT(*)`·`COUNT(열)` 은 부푼다.** 복제된 행을 구분할 방법이 없다.
4. ★ **`COUNT(DISTINCT 키)` 는 안 부푼다.** 복제된 키는 값이 같아 접힌다.
5. ★ **`SUM(DISTINCT)` 은 처방이 아니다.** 「중복 행」이 아니라 「중복 값」을 지운다 — 600 이 300 이 됐다.
6. **선집계 서브쿼리가 기본 처방이다.** 상대를 1:1 로 만들면 문제가 사라진다.
7. **`SELECT DISTINCT` 로 되돌릴 거면 기본키를 포함시킨다.** 값만으로 접으면 다른 행이 사라진다.
8. **`LATERAL` 은 「행마다 다른 것」이 필요할 때.** 집계 하나면 6번이 단순하다.

## 어디서 틀리나

- **★ 조인 뒤에 `SUM` 을 그냥 쓴다.**\
  1,200 이 2,000 이 됐다. **에러도 경고도 없다.** 조인 전후 행 수를 세는 것이 유일한 방어다.
- **★ 「`LEFT JOIN` 이니까 왼쪽 행 수 그대로」라고 믿는다.**\
  `LEFT` 는 **하한**만 보장한다([14번](../14-left-right-outer-join/)). 1:N 이면 는다.
- **★ `SUM(DISTINCT)` 으로 고친다.**\
  예시 데이터에서 **우연히 맞아** 넘어가기 쉽다. 값이 겹치는 순간 **더 크게 틀린다**(600 → 300).
- **조인을 하나 더 붙이면 배율이 더해질 거라 생각한다.**\
  **곱해진다.** 2 × 3 = 6줄이고 급여가 여섯 번 더해졌다.
- **`COUNT(DISTINCT)` 가 맞았으니 다른 집계도 괜찮다고 본다.**\
  같은 줄에서 `heads`=2 는 맞고 `payroll`=1600 은 틀렸다. **칸마다 따로 판정해야 한다.**
- **`SELECT DISTINCT` 를 값 열만으로 건다.**\
  급여가 같은 두 사람이 한 행으로 접힌다. **기본키를 포함시킨다.**
- **`COUNT(a.proj)` 와 `COUNT(DISTINCT a.proj)` 를 같은 것으로 본다.**\
  4와 3이었다. 「배정 건수」와 「프로젝트 종류 수」는 다른 질문이다([21번](../21-aggregate-functions-count-forms/)).
- **조인 조건이 있으니 카티션곱은 없다고 믿는다.**\
  조건이 있어도 **한쪽이 유일하지 않으면** 곱이 남는다([12번](../12-cartesian-product-cross-join/)).
- **ORM 이 만든 질의를 안 읽는다.**\
  컬렉션 두 개를 한 번에 `JOIN FETCH` 하면 정확히 3번의 곱이 일어난다 — 그 이야기는 [`data-access/jpa.md`](../../../../../engineering/data-access/jpa.md)다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 1:N 조인이 보존 측 행을 복제하는 것 | **결과의 정의** | 언어 — 조인의 정의에서 따라 나온다 |
| 복제된 행에 원래 열이 그대로 실리는 것 | **결과의 정의** | 언어 |
| `SUM` 이 복제를 못 알아보는 것 | **정의** | 언어 — `SUM` 은 입력 행을 그대로 더한다 |
| `COUNT(DISTINCT 키)` 가 안 부푸는 것 | **정의** | 언어 — 같은 값이 한 번으로 접힌다 |
| 세 처방이 같은 답을 내는 것 | **결과의 동치** | 실행으로 확인했다 — 800·400·`NULL` 이 세 형태에서 같았다 |
| 계획에 뜨는 조인 **연산자 이름** | 옵티마이저의 선택 | `Hash Left Join` 은 이번 계획일 뿐이다([목록의 **59번 주제**](../59-scan-join-sort-operators/)) |
| 세 처방의 **비용 차이** | **재지 않았다** | 스캔 구조만 적었고 수치는 적지 않는다 |
| 결과 **행 순서** | 아무도 보장 안 함 | `ORDER BY` 없이는 어느 엔진도 순서를 약속하지 않는다 |

- ★ **이 주제에서 두 엔진의 값이 한 자리도 안 갈렸다.** 팬아웃은 **방언이 아니라 조인의 정의**다.
- **갈린 것은 `ORDER BY` 가 없는 자리의 줄 순서뿐**이다(그룹 결과에서 `NULL` 이 앞이냐 뒤냐 — [목록의 **8번 주제**](../08-order-by-null-position-stability/)).
- ★ **한 번 재현되지 않은 관찰이 있다.** 6번 첫 질의(`ORDER BY e.id`)를 MySQL 에서 처음 돌렸을 때 `ann · cho · bob · dan` 순으로 나왔고,\
  그 뒤 **같은 문을 8회 더 돌렸지만 전부 `ann · bob · cho · dan`** 이었다. **원인을 규명하지 못했다.**\
  본문에는 **재현된 출력**을 실었고, 이 관찰은 「정렬 키가 있어도 한 번 어긋나 보인 일이 있었다」로만 남긴다 — **설명 없이 단정하지 않는다.**

## 언제 쓰고 언제 안 쓰나

- **선집계 서브쿼리 — 기본으로 쓴다.** 상대에서 필요한 것이 집계값이면 거의 항상 맞다.
- **`COUNT(DISTINCT 키)` — 세는 것이 전부일 때.** 조인을 안 고쳐도 되니 가장 싸게 끝난다.
- **`LATERAL` — 「행마다 상위 N건」처럼 접을 수 없는 것.** 집계 하나면 과하다.
- **`SELECT DISTINCT` 로 되돌리기 — 마지막 수단.** 중복 제거 비용이 들고 기본키를 빠뜨리면 조용히 틀린다.
- **`EXISTS` — 「짝이 있는지만」 보면 된다면.** 행이 아예 안 는다([목록의 **19번 주제**](../19-semi-anti-join/)). **팬아웃을 원천에서 없앤다.**
- **안 고쳐도 되는 경우 — 1:1 조인.** 조인 전후 `COUNT(*)` 이 같으면 아무 처방도 필요 없다.
- **윈도우 함수로 푸는 길도 있다** — 그룹으로 접지 않고 행마다 값을 붙인다([목록의 **26번 주제**](../26-window-functions-vs-aggregates/)). 이 주제 밖이다.

## 핵심 문장

- **팬아웃 = 1:N 조인이 보존 측 행을 짝 수만큼 복제하는 것.** 복제된 행에는 **원래 열이 그대로** 실린다.
- ★ **그 위에서 `SUM` 을 하면 조용히 부푼다** — 인건비 1,200 이 **2,000**, sales 부서 800 이 **1,600**(정확히 2배).
- **에러도 경고도 없다.** 문법은 맞고 값만 틀리다.
- ★ **조인이 둘이면 배율이 곱해진다** — 4행이 **10행**, 1,200 이 **3,200**. `ann` 한 명이 6줄이었다.
- ★ **`COUNT(DISTINCT 키)` 는 안 부푼다.** 복제된 키는 값이 같아 접힌다. 같은 줄에서 `heads` 는 맞고 `payroll` 은 틀렸다.
- ★ **`SUM(DISTINCT)` 은 처방이 아니다.** 「중복 값」을 지운다 — 급여가 같은 두 사람에서 600 이 **300** 이 됐다.
- **처방 셋 — 선집계 서브쿼리 · `COUNT(DISTINCT)` · `LATERAL`.** 세 형태가 **두 엔진에서 같은 답**을 냈다.
- **기본은 선집계다.** 상대 표를 미리 1행으로 접으면 조인이 1:1 이 되어 문제가 사라진다.
- **첫 습관은 행 수 세기다** — 조인 전 4, 조인 후 6. 이 한 줄이 이 주제의 모든 사고를 막는다.
- **계획에서도 보인다** — `Seq Scan rows=4` → `Hash Left Join rows=6`.

## 관련 자료

- [PostgreSQL 18 · Joined Tables](https://www.postgresql.org/docs/18/queries-table-expressions.html) — 조인이 짝마다 행을 만든다는 정의.
- [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)
- [13 INNER JOIN](../13-inner-join/) — **경계: 그쪽은 「짝이 여럿이면 행이 분다」까지, 여기는 그 행들이 집계에 들어가면 무슨 일이 나나부터.**
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — **경계: 그쪽은 「`LEFT` 도 행이 는다」는 사실까지, 여기는 그 증가가 값을 어떻게 바꾸나부터.**
- [12 카티션곱과 CROSS JOIN](../12-cartesian-product-cross-join/) — 팬아웃은 **조건이 남긴 작은 카티션곱**이다.
- [21 집계 함수와 COUNT 의 세 형태](../21-aggregate-functions-count-forms/) — **경계: 그쪽은 한 표 위의 집계까지, 여기는 조인이 행을 늘린 뒤부터.** `COUNT(열)` 대 `COUNT(DISTINCT 열)` 의 의미는 거기.
- [22 GROUP BY 와 비집계 열 규칙](../22-group-by-nonaggregated-columns/) — 그룹이 무엇 위에서 만들어지나.
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — 선집계 서브쿼리의 별칭 규칙(MySQL 은 필수).
- [20 LATERAL 조인](../20-lateral-join/) — **경계: 거기는 `LATERAL` 자체의 문법과 의미, 여기는 그것이 팬아웃 처방이 되는 이유.**
- [`engineering/data-access/jpa.md`](../../../../../engineering/data-access/jpa.md) — **경계: ORM 이 SQL 을 만들어 내는 비용(N+1·숨은 SQL)은 거기, 여기는 SQL 자체의 행 수 계산.**
- **`EXISTS`/`NOT EXISTS`** 는 [목록의 **19번 주제**](../19-semi-anti-join/), **윈도우 함수**는 [**26번 주제**](../26-window-functions-vs-aggregates/), **계획 읽기**는 [**58번 주제**](../58-explain-plan-tree/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **팬아웃(fan-out)** — 1:N 조인에서 한쪽 행이 상대의 짝 수만큼 복제되는 현상.\
  예: `ann` 이 프로젝트 둘에 끼어 있어 조인 결과에 두 줄이 된다.
- **부풀린 집계(inflated aggregate)** — 복제된 행을 그대로 더해 실제보다 커진 합계.\
  예: 인건비 1,200 이 2,000 으로 나온 것. **에러가 아니라 「맞게 계산된 틀린 값」이다.**
- **선집계(pre-aggregation)** — 조인하기 **전에** 상대 표를 키 하나당 한 행으로 접는 것.\
  예: `(SELECT emp_id, COUNT(*) AS n FROM asg GROUP BY emp_id)` 를 붙이면 조인이 1:1 이 된다.
- **1:1 조인** — 양쪽에서 조인 키가 유일해 행이 안 느는 조인.\
  예: 선집계 뒤의 `emp` ↔ `a` 조인. 조인 전후 `COUNT(*)` 이 4로 같다.
- **`COUNT(DISTINCT 키)`** — 복제된 키를 접어 원래 개수를 돌려주는 형태.\
  예: 조인 뒤에도 `COUNT(DISTINCT e.id)` 가 4였다.
- **`SUM(DISTINCT)`** — **중복 값**을 한 번만 더하는 형태. **팬아웃 처방이 아니다.**\
  예: 급여 300 인 두 사람에서 600 이 아니라 300 을 냈다.
- **`LATERAL`** — 바깥 행의 값을 참조할 수 있는 `FROM` 절 서브쿼리.\
  예: `LEFT JOIN LATERAL (SELECT COUNT(*) FROM asg a WHERE a.emp_id = e.id) x ON TRUE`.
- **`ON TRUE`** — `LATERAL` 에서 조인 조건이 이미 안쪽 `WHERE` 에 있을 때 쓰는 자리 채우기.\
  예: 위 질의. `LEFT JOIN` 은 `ON` 이 문법상 필요하다([13번](../13-inner-join/)).
- **보존 측(preserved side)** — 외부 조인에서 「한 행도 안 버린다」고 약속된 쪽.\
  예: `emp LEFT JOIN asg` 의 `emp`. **안 버린다는 약속이지 안 는다는 약속이 아니다.**
- **`actual rows`** — `EXPLAIN ANALYZE` 가 찍는 **실제로 나온 행 수**.\
  예: `Seq Scan … rows=4.00` 과 `Hash Left Join … rows=6.00`. 그 사이가 팬아웃이다.

## 더 들어가면

- **팬아웃을 미리 아는 법은 제약을 보는 것이다.** 조인 키가 상대 표에서 `UNIQUE`(또는 기본키)면 1:1 이라 안전하다.\
  아니면 1:N 이고, 그때부터 집계를 조심한다. 제약 정의는 [목록의 **43번 주제**](../43-primary-key-unique-and-null/)다.
- **`EXISTS` 는 팬아웃을 원천에서 없앤다.** 「그 프로젝트에 낀 사람들의 인건비」라면\
  `WHERE EXISTS (SELECT 1 FROM asg a WHERE a.emp_id = e.id AND a.proj = 'p1')` 이 행을 안 늘린다([목록의 **19번 주제**](../19-semi-anti-join/)).
- **집계를 여러 상대 표에서 각각 얻어야 하면 선집계를 각각 붙인다.** 3번의 곱셈이 그렇게 사라진다 —\
  `asg` 를 접은 표와 `skl` 을 접은 표를 **따로** `LEFT JOIN` 하면 둘 다 1:1 이라 곱이 안 생긴다.
- **세 처방의 비용 비교는 하지 않았다.** 스캔 구조는 적었지만 **수치는 재지 않았고 적지 않는다.**\
  실제 비교는 `EXPLAIN ANALYZE` 로 하고, 읽는 법은 목록의 [**58**](../58-explain-plan-tree/)·[**60**](../60-explain-analyze-estimates-vs-actuals/)번 주제다.
- **`GROUP BY` 를 쓰지 않고 행마다 값을 붙이는 길**이 윈도우 함수다([목록의 **26번 주제**](../26-window-functions-vs-aggregates/)).\
  팬아웃 위에서는 윈도우 함수도 똑같이 부푼다 — **먼저 행을 바로잡는 것이 순서다.**
