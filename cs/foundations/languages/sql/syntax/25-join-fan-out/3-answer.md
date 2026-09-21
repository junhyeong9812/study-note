# sql/25-조인 팬아웃 — 행 수와 집계가 틀어지는 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 예시의 `asg`·`skl`·`two` 는 **전부 CTE** 다 — `study` DB 에는 표를 만들지 않았다.\
> 문서 근거는 [PG 18 Joined Tables](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. **6행**이다 — 사람마다 「자기 프로젝트 수」만큼 복제된다

**출력**

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

**왜 그런가**

```text
 ann 2 + bob 2 + cho 1 + dan 1 = 6

 왼쪽 한 행이 오른쪽 짝 수만큼 복제된다.
 복제되는 것은 키가 아니라 "행 전체" 다 -> salary 도 같이 복제된다
```

★ **`ann` 의 급여 300 이 두 줄에 실려 있다.** 이것이 다음 문제 전부의 원인이다.

**행 수를 세면 한 줄로 확인된다.**

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

> **팬아웃(fan-out)** — 1:N 조인에서 한쪽 행이 상대의 짝 수만큼 복제되는 현상.\
> 예: `ann` 이 프로젝트 둘에 끼어 있어 조인 결과에 두 줄이 된다.

---

### 2. `payroll`=**2000** · `c`=**6** · `heads`=**4** — **`payroll` 과 `c` 가 틀렸다**

**출력 — 먼저 참값**

```text
### SQL: SELECT SUM(salary) AS payroll, COUNT(*) AS c FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 payroll | c                     +---------+---+
---------+---                    | payroll | c |
    1200 | 4                     +---------+---+
(1 row)                          |    1200 | 4 |
                                 +---------+---+
```

**출력 — 조인 뒤**

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

**왜 그런가**

```text
 SUM(e.salary)        300+300 + 500+500 + NULL + 400 = 2000   부풀었다 (참값 1200)
 COUNT(*)             6                                        부풀었다 (참값 4)
 COUNT(e.id)          6                                        부풀었다 (참값 4)
 COUNT(DISTINCT e.id) 4                                        안 부풀었다
```

★★ **에러도 경고도 없다. 문법은 한 글자도 안 틀렸고 숫자만 조용히 800 커졌다.**\
**이것이 「맞게 계산된 틀린 값」이다** — 엔진은 시킨 대로 했고, 시킨 것이 틀렸다.

> **부풀린 집계(inflated aggregate)** — 복제된 행을 그대로 더해 실제보다 커진 합계.\
> 예: 인건비 1,200 이 2,000 으로 나온 것.

---

### 3. **복제된 `e.id` 는 값이 같아서 `DISTINCT` 가 도로 접기 때문이다**

```text
 조인 결과의 e.id 열
 [1, 1, 2, 2, 3, 4]
       |
   DISTINCT  ->  [1, 2, 3, 4]  ->  COUNT = 4     맞다
       |
   DISTINCT 가 없으면 -> COUNT = 6                틀렸다

 조인 결과의 e.salary 열
 [300, 300, 500, 500, NULL, 400]
       |
    SUM 에는 그런 장치가 없다 -> 2000
       "같은 값을 여러 번 더하는 것" 이 SUM 의 정의다
```

★ **`SUM` 이 「고장 난」 게 아니다.** 300 을 두 번 더하라고 시켰고 그대로 했다.\
`COUNT(DISTINCT)` 가 살아남는 것은 **중복을 접는 규칙이 이미 함수 안에 있기** 때문이다([21번](../21-aggregate-functions-count-forms/)).

```text
 팬아웃을 견디나
 +---------------------------+---------+
 | SUM(열) · AVG(열)          | 부푼다  |
 | COUNT(*) · COUNT(열)       | 부푼다  |
 | COUNT(DISTINCT 키)         | 안 부푼다|
 | MIN(열) · MAX(열)          | 안 부푼다 (같은 값이 여러 번 와도 최대·최소는 그대로) |
 +---------------------------+---------+
```

★ **`MIN`/`MAX` 도 견딘다** — 복제는 **새 값을 만들지 않으므로** 최대·최소가 안 변한다.\
하지만 **「몇 건인가」와 「얼마인가」는 전부 무너진다.** 실무에서 필요한 것이 대개 그쪽이다.

---

### 4. `payroll`=**1600**(참값 800 의 **2배**) · `heads`=**2**(맞다)

**출력**

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

**왜 그런가**

```text
 sales (dept_id = 10)
   참값  = ann 300 + bob 500 = 800
   나온 값 = 300 + 300 + 500 + 500 = 1600        정확히 2 배
                ^         ^
       ann 도 bob 도 프로젝트가 2 개씩이라 둘 다 두 번 더해졌다
```

★★ **같은 줄에서 한 칸은 맞고 한 칸은 틀렸다.**

```text
 dept_id=10 행
 +---------+-----+-------+
 | payroll |  c  | heads |
 |  1600   |  4  |   2   |
 +---------+-----+-------+
     틀림   틀림   맞음
```

**「인건비 1,600」은 그 자체로 이상해 보이지 않는다.** 참값을 따로 알지 못하면 아무도 못 잡는다.\
대가 — 그래서 **검산 기준**(조인 전 값·`heads`)을 같이 뽑아 두는 습관이 필요하다.

`dept_id=20` 의 `payroll` 이 `NULL` 인 것은 팬아웃과 무관하다 — `cho` 의 급여가 없기 때문이다([21번](../21-aggregate-functions-count-forms/)).

---

### 5. **10행**이 되고 `SUM` 은 **3200** 이다 — 배율은 **곱해진다**

**출력**

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

**왜 그런가**

```text
 사람마다 몇 줄이 되나 — 두 표의 짝 수가 곱해진다

 ann  프로젝트 2 x 기술 3 = 6 줄  ->  300 x 6 = 1800
 bob  프로젝트 2 x 기술 1 = 2 줄  ->  500 x 2 = 1000
 cho  프로젝트 1 x 기술 1 = 1 줄  ->  NULL
 dan  프로젝트 1 x 기술 1 = 1 줄  ->  400 x 1 =  400
                     합 10 줄            합   = 3200     (참값 1200)
```

★★ **더해지지 않는다. 곱해진다.**\
조인 하나로는 1,200 → 2,000 이었는데 둘이 되니 **3,200** 이다. 조인이 셋이면 더 심해진다.

★ **`heads`·`projs`·`skills` 는 전부 맞다**(4·3·3) — `COUNT(DISTINCT)` 는 조인이 몇 겹이든 견딘다.

```text
 이것은 12번의 카티션곱이 작게 되풀이되는 것이다
 +----------------------------------------------------+
 | ON 조건이 있어도                                    |
 |   한쪽이 유일하지 않으면                            |
 |   그 안에서 다시 "모든 짝" 이 만들어진다             |
 | ann 의 6 줄 = 프로젝트 2 개 x 기술 3 개의 카티션곱  |
 +----------------------------------------------------+
```

---

### 6. **조인하기 전에 `asg` 를 `emp_id` 당 한 행으로 접는다**(선집계)

**출력**

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

**왜 그런가**

```text
 팬아웃이 생기는 순서                 선집계로 막는 순서
 emp 4행                              emp 4행
   + asg 6행 (1:N)                      + (asg 를 emp_id 로 접은) 4행 (1:1)
   = 6행  <- 여기서 부푼다               = 4행  <- 안 부푼다
   -> SUM 2000                          -> SUM 1200 · sales 800
```

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

★ **`payroll` 이 800 으로 돌아왔고 `proj_cnt`(4건)까지 같이 얻었다.**\
원하던 두 가지가 한 질의에 다 있다 — **집계를 잃지 않고 팬아웃만 없앴다.**

대가 — 상대 표를 한 번 더 훑고, **필요한 집계를 미리 정해야 한다.**\
파생 테이블 별칭은 **MySQL 에서 필수**다([10번](../10-from-clause-aliases-derived-tables/)) — 위 질의의 `a` 가 그것이다.

> **선집계(pre-aggregation)** — 조인하기 **전에** 상대 표를 키 하나당 한 행으로 접는 것.\
> 예: `(SELECT emp_id, COUNT(*) AS n FROM asg GROUP BY emp_id)`.

---

### 7. ★ `fanned`=**900** · `sum_dist`=**300** · `heads`=**2** — **처방이 아니다. 더 틀린다**

**출력 — 먼저 `emp` 에서는 우연히 맞는다**

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

**출력 — 급여가 같은 두 사람을 넣으면 무너진다**

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

**왜 그런가**

```text
 두 사람 다 급여 300.  참값 = 600

 SUM(t.salary)           900   부풀었다 (ann 이 두 줄이라 300 이 세 번)
 SUM(DISTINCT t.salary)  300   더 틀렸다 — eve 를 통째로 지웠다
 COUNT(DISTINCT t.id)      2   맞다
```

```text
 DISTINCT 가 무엇을 접는가
 +-------------------------------+   +-------------------------------+
 | COUNT(DISTINCT e.id)          |   | SUM(DISTINCT e.salary)        |
 | 접는 대상 = 키                |   | 접는 대상 = 값                |
 | 같은 키 = 같은 행이다          |   | 같은 값 = 다른 사람일 수 있다  |
 | -> 맞다                       |   | -> 틀린다                     |
 +-------------------------------+   +-------------------------------+
```

★★ **`emp` 에서 1,200 이 나온 것이 가장 위험한 순간이다.** 참값과 같아서 「고쳤다」고 믿게 된다.\
`emp` 의 급여가 `300·500·NULL·400` 으로 **전부 달랐기 때문**일 뿐이다.

★ **이것이 「예시 데이터에서 맞았다」가 보장이 아닌 이유의 실례다.** 반례를 만들어 던져야 안다.

---

### 8. **기본키(또는 행을 유일하게 하는 열)를 포함시킨다**

**출력**

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

**왜 그런가**

```text
 SELECT DISTINCT e.id, e.salary          SELECT DISTINCT e.salary
 +----+--------+                         +--------+
 |  1 |    300 |                         |    300 |
 |  2 |    500 |                         |    500 |
 |  3 |   NULL |                         |   NULL |
 |  4 |    400 |                         |    400 |
 +----+--------+                         +--------+
    4 행 -> SUM 1200   맞다                 이 데이터에서는 우연히 같다
                                            급여가 같은 두 사람이 있으면 한 줄로 접힌다
                                            -> 7 번과 같은 사고
```

★ **`id` 를 넣는 것이 요점이다.** `id` 가 기본키라 **두 사람이 한 행으로 접히는 일이 없다.**\
「`DISTINCT` 를 붙였으니 안전하다」가 아니라 **「무엇을 기준으로 유일하게 만들었나」**가 판정 기준이다.

대가 — **중복 제거 비용**이 든다. 조인 결과가 클수록 비싸고, 대개 6번의 선집계가 낫다.\
★ **마지막 수단으로 두는 이유** — 집계를 나중에 하므로 **중간 결과가 조인 결과만큼 커진다.**

---

### 9. **`LATERAL` 서브쿼리가 행 하나를 돌려주므로 조인이 1:1 이 되기 때문이다**

**출력**

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

**왜 그런가**

```text
 선집계 서브쿼리                      LATERAL
 상대 표를 한 번에 다 접는다           바깥 행 하나마다 안쪽을 다시 돈다
 (emp_id 전부에 대해 GROUP BY)        (e.id 를 참조해 그 사람 것만)
        |                                    |
   결과가 1:1 이라 안 분다              안쪽이 1 행이라 안 분다
```

★ **6번과 한 글자도 같은 결과다**(800 · `NULL` · 400, 4 · 1 · 1). 두 엔진 모두에서 돌았다.\
`ON TRUE` 가 붙는 이유는 조인 조건이 이미 안쪽 `WHERE a.emp_id = e.id` 에 들어가 있기 때문이다.

```text
 언제 LATERAL 이 나은가
 +--------------------------------------------------+
 | "행마다 상위 N 건" — 집계로 접을 수 없다          |
 |   예: 사원마다 최근 프로젝트 2 개                 |
 | 바깥 행마다 계산이 달라야 할 때                   |
 +--------------------------------------------------+
 언제 선집계가 나은가
 +--------------------------------------------------+
 | 집계값 하나만 필요할 때 — 더 단순하고             |
 |   바깥 행마다 안쪽을 다시 돌지 않는다             |
 +--------------------------------------------------+
```

★ **경계: `LATERAL` 자체의 문법과 의미는 [20번](../20-lateral-join/)이 정본이다.** 여기서는 **팬아웃 처방으로서만** 다룬다.

---

### 10. `COUNT(a.proj)`=**4**, `COUNT(DISTINCT a.proj)`=**3** — **다른 질문의 답이다**

**출력**

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

**왜 그런가**

```text
 sales 부서의 배정 네 건
 ann-p1 · ann-p2 · bob-p1 · bob-p3

 COUNT(a.proj)          4   "배정이 몇 건인가"
 COUNT(DISTINCT a.proj) 3   "프로젝트가 몇 종류인가"  (p1 · p2 · p3)
                                              ^^^^^
                            p1 이 두 번 나오므로 한 번으로 접힌다
```

★ **넷이 전부 다른 질문의 답이다.**

| 열 | 값 | 무엇을 묻나 |
|---|---|---|
| `rows_out` | 4 | 조인 결과의 줄 수 — **집계에 쓰면 안 되는 수** |
| `heads` | 2 | 사람 수 |
| `asg_cnt` | 4 | 배정 건수 |
| `proj_kinds` | 3 | 프로젝트 종류 수 |

★ **`rows_out` 과 `asg_cnt` 가 우연히 둘 다 4다.** 이 데이터에서는 배정이 없는 사원이 없기 때문이다.\
`hr` 처럼 짝이 없는 행이 섞이면 갈라진다 — `COUNT(*)` 은 세고 `COUNT(a.proj)` 은 안 센다([21번](../21-aggregate-functions-count-forms/)).

**어느 쪽이 원하는 답인지 먼저 정하는 것**이 이 주제에서 제일 중요한 습관이다.

---

### 11. **`actual … rows=` 를 아래에서 위로 비교한다**

**출력**

```text
### SQL: EXPLAIN ANALYZE WITH asg(...) AS (...)
         SELECT SUM(e.salary) FROM emp e LEFT JOIN asg a ON a.emp_id = e.id;
--- PG 18.6 --- (필요한 세 줄만 옮긴 것이다)
 Aggregate  (cost=28.59..28.60 rows=1 width=8) (actual time=0.037..0.043 rows=1.00 loops=1)
   ->  Hash Left Join  (cost=0.17..25.76 rows=1130 width=4) (actual time=0.029..0.037 rows=6.00 loops=1)
         ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=8) (actual time=0.005..0.006 rows=4.00 loops=1)
```

**왜 그런가**

```text
 계획을 아래에서 위로 읽는다

 Seq Scan on emp        rows=4.00     <- 표에서 4행을 읽었다
        |
 Hash Left Join         rows=6.00     <- 조인이 6행을 냈다.  여기서 불었다
        |
 Aggregate              rows=1.00     <- 그 6행을 하나로 접었다 (2000)
```

★ **자식 노드의 `rows` 보다 부모 노드의 `rows` 가 크면 그 노드가 행을 늘린 것이다.**\
조인이 여럿인 질의에서 **어느 조인이 범인인지** 이 한 가지로 짚을 수 있다.

```text
 여기서 보는 것 / 안 보는 것
 +-----------------------------+   +-----------------------------+
 | actual ... rows=            |   | cost=  ·  time=             |
 | "행이 어디서 늘었나"        |   | 이 주제에서 해석하지 않는다  |
 +-----------------------------+   +-----------------------------+
```

★ **경계: 계획 읽기 자체는 목록의 58번 주제, 연산자 이름(`Hash Left Join` 등)은 59번 주제, 추정 대 실측의 격차는 60번 주제다.**\
`rows=1130` 이라는 **추정치**가 실제 4와 크게 다른 것도 거기서 다룰 이야기다 — **여기서는 `actual` 만 본다.**

---

### 12. **없다. 값이 한 자리도 안 갈렸다**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 조인 뒤 행 수 (1번) | 6 | 6 |
| 부푼 `SUM` (2번) | 2000 | 2000 |
| `COUNT(DISTINCT e.id)` (2번) | 4 | 4 |
| 부서별 부푼 값 (4번) | 1600 | 1600 |
| 이중 팬아웃 (5번) | 10행 · 3200 | 10행 · 3200 |
| 선집계 처방 (6번) | 800 | 800 |
| `SUM(DISTINCT)` 의 오답 (7번) | 300 | 300 |
| `DISTINCT` 되돌리기 (8번) | 1200 | 1200 |
| `LATERAL` 처방 (9번) | 800 | 800 |
| 건수 대 종류 수 (10번) | 4 · 3 | 4 · 3 |

★ **팬아웃은 방언이 아니라 조인의 정의다.** 어느 엔진이든 짝마다 행을 만들고, `SUM` 은 그 행을 그대로 더한다.\
★ **처방 셋도 두 엔진에서 다 돌았다** — `LATERAL` 포함.

**갈린 것은 `ORDER BY` 가 없는 자리의 줄 순서뿐**이고(`NULL` 그룹의 위치 — [목록의 **8번 주제**](../08-order-by-null-position-stability/)), 값은 아니다.

★ **한 번 재현되지 않은 관찰이 하나 있다.** 9번 첫 질의(`ORDER BY e.id`)를 MySQL 에서 처음 돌렸을 때 `ann · cho · bob · dan` 순으로 나왔고,\
같은 문을 **8회 더 돌렸지만 전부 `ann · bob · cho · dan`** 이었다. **원인을 규명하지 못했다.**\
본문에는 **재현된 출력**을 실었다 — 설명하지 못하는 것을 단정하지 않는다.

---

### 13. **조인 전후의 행 수를 세는 한 줄**

```sql
SELECT (SELECT COUNT(*) FROM emp) AS before_join, COUNT(*) AS after_join
FROM emp e LEFT JOIN asg a ON a.emp_id = e.id;
```

```text
### SQL: (위 질의)
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 before_join | after_join        +-------------+------------+
-------------+------------       | before_join | after_join |
           4 |          6        +-------------+------------+
(1 row)                          |           4 |          6 |
                                 +-------------+------------+
```

```text
 before == after  ->  1:1 조인이다.  집계를 그냥 써도 된다
 before <  after  ->  팬아웃이 있다. SUM · AVG · COUNT 를 쓰기 전에 처방을 고른다
```

★ **이 한 줄이 이 주제의 모든 사고를 막는다.**\
2번의 2,000 도, 4번의 1,600 도, 5번의 3,200 도 **전부 「4가 6이 됐다」에서 출발했다.**

**더 이른 방어도 있다 — 제약을 보는 것이다.**

```text
 조인 키가 상대 표에서 UNIQUE(또는 기본키)인가?
   예   -> 1:1 이다. 구조적으로 안전하다
   아니오 -> 1:N 이다. 집계를 조심한다
```

제약 정의는 목록의 **43번 주제**다. **「짝이 있는지만」 보면 되는 경우에는 `EXISTS` 가 행을 아예 안 늘린다**([목록의 **19번 주제**](../19-semi-anti-join/)).

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `asg` CTE 확인 (예시 데이터) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **표를 만들지 않았다** |
| 조인 결과 6행 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 행 나열 + 전후 행 수 |
| ★ 부푼 `SUM` (2·3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 참값 1200 → **2000** |
| 부서별 배율 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | sales 800 → **1600** |
| ★ 이중 팬아웃 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 4행 → **10행**, 1200 → **3200** |
| 처방 1 — 선집계 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 800 으로 복구 |
| ★ `SUM(DISTINCT)` 반례 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `emp` 에서 우연히 맞고, 반례에서 **300** |
| 처방 2 — `DISTINCT` 되돌리기 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 기본키 포함 |
| 처방 3 — `LATERAL` (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **두 엔진 모두 돌았다** |
| 건수 대 종류 수 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 4 대 3 |
| `EXPLAIN ANALYZE` (11번) | PG 18.6 | 1회 | `rows=4.00` → `rows=6.00` |
| ★ 순서 이상 재확인 (12번) | MySQL 8.4.10 | **8회** | **재현 실패 — 원인 미상으로 기록** |

**구현 의존 항목** — 계획의 연산자 이름(`Hash Left Join`)과 추정 행 수(`rows=1130`). **이 주제에서 해석하지 않는다.**\
**방언 항목** — **없다.** 값이 한 자리도 안 갈렸고 세 처방이 모두 두 엔진에서 돌았다.\
**언어 보장 항목** — 1~11·13번 전부. 팬아웃은 조인의 정의에서 나온다.

**재지 않은 것** — 세 처방의 **비용 비교**. 스캔 구조만 적었고 **수치는 적지 않았다.**\
**버전** — 갈리는 것이 없다. 다음 버전에서는 **9번(MySQL 의 `LATERAL`)만** 다시 확인하면 된다.\
**DB 잔재** — `asg`·`skl`·`two` 는 전부 CTE 다. `study` 에는 여전히 `emp`·`dept` 둘뿐이다.
