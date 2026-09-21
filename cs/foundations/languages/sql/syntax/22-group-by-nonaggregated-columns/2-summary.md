# sql/22-`GROUP BY` 와 비집계 열 규칙 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · GROUP BY and HAVING Clauses](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · MySQL Handling of GROUP BY](https://dev.mysql.com/doc/refman/8.4/en/group-by-handling.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `ANY_VALUE()` 는 PostgreSQL **16 부터**다([PG 16 릴리스 노트](https://www.postgresql.org/docs/release/16.0/)가 *"Add aggregate function `ANY_VALUE()`"* 로 적는다). MySQL 은 8.4 매뉴얼의 GROUP BY 처리 페이지에 있고 도입 버전은 확인하지 못해 적지 않는다.\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) · [21 집계 함수와 COUNT 의 세 형태](../21-aggregate-functions-count-forms/).\
> **바로 옆** — [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/). **거기는 「어느 절에서 거르나」, 여기는 「그 절들이 보는 것이 왜 그룹인가」다.**\
> **뒤 주제** — [23 GROUPING SETS·ROLLUP·CUBE](../23-grouping-sets-rollup-cube/) · [24 조건부 집계](../24-conditional-aggregation-filter-case/) · [25 조인 팬아웃](../25-join-fan-out/).

## 한눈에 — 쉽게 말하면

**`GROUP BY` 는 명단을 반별로 접어 봉투에 넣는 것이다. 접고 나면 봉투 겉면만 보인다.**

- 4명의 명단을 부서별로 접어 봉투 3개에 넣었다.
- 봉투 겉면에 쓸 수 있는 것은 **둘뿐**이다 — **봉투 이름**(부서 번호)과 **봉투 안을 집계한 값**(인원수·급여 합계).
- 「이 봉투에 든 사람 **이름**」은 겉면에 못 쓴다. **안에 둘이 들었으면 어느 쪽을 쓸 건가?**

| 비유 | 실체 | 예 |
|---|---|---|
| 봉투 이름 | **그룹 키** — `GROUP BY` 에 적은 것 | `dept_id` |
| 봉투 안을 세어 적은 수 | **집계 함수의 결과** | `COUNT(*)`·`SUM(salary)` |
| 봉투 안에서 아무거나 꺼낸 쪽지 | **비집계 열** — 값이 하나로 정해지지 않는다 | `name` |

```text
접기 전 4행                        접은 뒤 3그룹
+----+------+---------+            +---------+---------------------+
| id | name | dept_id |            | dept_id |   이 봉투 안        |
+----+------+---------+            +---------+---------------------+
|  1 | ann  |      10 |  ──GROUP   |      10 | ann(300) · bob(500) |
|  2 | bob  |      10 |    BY──>   |      20 | cho(NULL)           |
|  3 | cho  |      20 |            |    NULL | dan(400)            |
|  4 | dan  |    NULL |            +---------+---------------------+
+----+------+---------+               ^                ^
                                 겉면에 쓸 수 있다   못 쓴다 (둘 중 누구?)
```

**이 봉투가 똑같은 구조로** `GROUP BY` 다.\
★ 그리고 **[01번](../01-logical-query-processing-order/)의 처리 순서에서 `GROUP BY` 가 3번 칸**이라, **그 뒤의 칸들**(`HAVING`·`SELECT`·`ORDER BY`)은 **봉투만 본다.**\
「`SELECT` 에서 왜 그 열을 못 쓰지」가 전부 이 한 줄로 설명된다.

> **그룹 키(group key)** — `GROUP BY` 에 적은 식. 한 그룹 안에서는 값이 **하나로 정해진다.**\
> 예: `GROUP BY dept_id` 면 `dept_id=10` 그룹 안의 모든 행이 `dept_id` 가 10이다.

> **비집계 열(non-aggregated column)** — 집계 함수로 감싸지 않은 열. 그룹 키가 아니면 **값이 하나로 안 정해진다.**\
> 예: `dept_id=10` 그룹의 `name` 은 `ann` 과 `bob` 둘이다.

## 이 주제가 답하려는 질문

1. **`GROUP BY` 뒤에는 왜 그룹만 보이나?** — 처리 순서의 3번 칸이 입력을 통째로 바꾼다.
2. **비집계 열을 쓰면 엔진이 왜 거부하나 — 또는 왜 조용히 허용하나?** — 여기서 두 엔진이 갈린다.
3. **허용된 그 값은 무엇인가?** — 「아무 값」이고 **보장이 아니다.** 그것을 어떻게 보일 수 있나.

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
        ^          ^
        |          +-- dan 은 소속이 없다 (dept_id NULL)
        +------------- cho 는 급여가 없다 (salary NULL)
```

**이 표가 `GROUP BY` 를 설명하기에 딱 맞다.**

- `dept_id=10` 그룹에 **행이 둘**이라 「`name` 을 쓰면 누구?」가 바로 보인다(`ann` 대 `bob`).
- `dan` 의 `dept_id` 가 `NULL` 이라 **`NULL` 이 한 그룹으로 묶이는 것**을 확인할 수 있다(6번).
- `emp.id` 가 기본키이고 `dept.name` 이 `UNIQUE NOT NULL` 이라, **함수 종속성 예외를 두 방향으로 시험**할 수 있다(4번).

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

### 1. 처리 순서의 3번 칸이 입력을 통째로 바꾼다

**언제 쓰나** — 「`SELECT` 에서 이 열을 왜 못 쓰지」가 막힐 때. 답은 항상 여기에 있다.

```text
FROM ──> WHERE ──> GROUP BY ──> HAVING ──> SELECT ──> ORDER BY
  1        2          3            4          5          6
                      ^
              여기서 입력이 "행" 에서 "그룹" 으로 바뀐다
              이 선을 넘은 칸들은 원래 행을 못 본다
```

```text
  3번 칸의 입력 (행 4개)            3번 칸의 출력 (그룹 3개)
+----+------+---------+--------+   +---------+------------------------+
| id | name | dept_id | salary |   | 그룹 키 | 그 안에 있는 행들       |
+----+------+---------+--------+   +---------+------------------------+
|  1 | ann  |      10 |    300 |   |      10 | (1,ann,300) (2,bob,500)|
|  2 | bob  |      10 |    500 |-->|      20 | (3,cho,NULL)           |
|  3 | cho  |      20 |   NULL |   |    NULL | (4,dan,400)            |
|  4 | dan  |    NULL |    400 |   +---------+------------------------+
+----+------+---------+--------+
                                     4번(HAVING)·5번(SELECT) 이 보는 것은 이 표다
```

그림 해설 — ★ **4번 칸부터는 행이 없다. 그룹만 있다.**\
그래서 `SELECT name` 은 「봉투 하나에서 이름 하나를 꺼내라」인데 **봉투에 둘이 들어 있을 수 있어** 답이 정해지지 않는다.

**집계 없이 `GROUP BY` 만 쓰면 `DISTINCT` 와 같아진다.** 그룹 키만 보이므로 당연하다.

```text
### SQL: SELECT dept_id FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      20                         |    NULL |
    NULL                         |      10 |
(3 rows)                         |      20 |
                                 +---------+
```

(행 순서가 다른 것은 `NULL` 의 정렬 위치 차이다 — PG 는 ASC 에서 뒤, MySQL 은 앞. [목록의 **8번 주제**](../08-order-by-null-position-stability/)다.)

비용 — 그룹을 만들려면 정렬이나 해시가 필요하다. 계획에 뜨는 이름은 목록의 **59번 주제**다.

★ **경계: [01번](../01-logical-query-processing-order/)이 여덟 칸 전체의 좌표계까지, [03번](../03-where-vs-having/)이 2번 칸과 4번 칸의 대비까지, 여기는 3번 칸이 입력을 무엇으로 바꾸나부터.**

---

### 2. ★ 비집계 열 — PG 는 거부하고, MySQL 은 기본 설정에서 거부한다

**언제 쓰나** — `GROUP BY` 를 쓴 질의를 처음 돌릴 때. 대부분 여기서 한 번은 막힌다.

```text
 SELECT dept_id, name FROM emp GROUP BY dept_id;
                ^^^^
        dept_id=10 봉투 안에는 ann 과 bob 이 있다.  어느 쪽?
```

```text
### SQL: SELECT dept_id, name FROM emp GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  column "emp.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT dept_id, name FROM emp GROUP BY dept_id;
                        ^
--- MySQL 8.4.10 ---
ERROR 1055 (42000) at line 1: Expression #2 of SELECT list is not in GROUP BY clause and contains nonaggregated column 'study.emp.name' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

그림 해설 — **두 엔진의 메시지가 말하는 것이 다르다.**

| | 메시지가 제시하는 탈출구 |
|---|---|
| PostgreSQL 18.6 | **둘** — `GROUP BY` 에 넣거나 집계로 감싸라 |
| MySQL 8.4.10 | **셋** — 그것 둘에 더해 **「함수 종속이 아니다」**와 **`sql_mode=only_full_group_by`** 를 지목한다 |

★ **MySQL 의 메시지가 설정 이름을 말해 주는 것**이 이 주제의 분기점이다. 그 설정은 **끌 수 있다**(3번).

**`GROUP BY` 가 아예 없어도 집계가 하나라도 있으면 같은 규칙이 걸린다.** 표 전체가 한 그룹이기 때문이다.

```text
### SQL: SELECT name, COUNT(*) FROM emp;
--- PG 18.6 ---
ERROR:  column "emp.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT name, COUNT(*) FROM emp;
               ^
--- MySQL 8.4.10 ---
ERROR 1140 (42000) at line 1: In aggregated query without GROUP BY, expression #1 of SELECT list contains nonaggregated column 'study.emp.name'; this is incompatible with sql_mode=only_full_group_by
```

★ **MySQL 은 에러 번호까지 다르다 — `1055`(`GROUP BY` 있음) 대 `1140`(`GROUP BY` 없음).**\
PG 는 **두 경우에 한 글자도 같은 메시지**를 낸다. PG 쪽에서는 이것이 **같은 규칙의 두 모습**이라는 게 메시지에서도 드러난다.

`ORDER BY` 에 비집계 열을 써도 같다 — **3번 칸 뒤의 칸은 전부 그룹만 본다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY dept_id ORDER BY name;
--- PG 18.6 ---
ERROR:  column "emp.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: ...t_id, COUNT(*) AS c FROM emp GROUP BY dept_id ORDER BY name;
                                                                  ^
--- MySQL 8.4.10 ---
ERROR 1055 (42000) at line 1: Expression #1 of ORDER BY clause is not in GROUP BY clause and contains nonaggregated column 'study.emp.name' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

MySQL 문서가 이 세 자리를 한 문장에 담는다: *"MySQL rejects queries for which the select list, `HAVING` condition, or `ORDER BY` list refer to nonaggregated columns …"*.

★ **경계: `HAVING` 에서의 같은 거부는 [03번](../03-where-vs-having/)이 정본이다** — 거기 에러 메시지와 별칭 방언까지 있다. 여기서는 **그 규칙이 `SELECT`·`ORDER BY` 에도 똑같이 걸린다는 것**까지.

비용 — 없다. **거부는 값이다.** 여기서 안 막히면 3번의 「조용히 틀린 값」을 받게 된다.

---

### 3. ★ MySQL 의 `only_full_group_by` 를 끄면 — 「아무 값」이 나온다

**언제 쓰나** — 옛 코드베이스를 옮길 때. 그리고 그 결정을 되돌려야 하나 판단할 때.

```text
### SQL: SELECT @@sql_mode;  (MySQL 8.4.10 기본값)
ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION
```

**기본 `sql_mode` 에 들어 있다.** 세션에서 빼면 2번의 질의가 **에러 없이 돈다.**

```sql
SET SESSION sql_mode = REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', '');
SELECT dept_id, name, salary FROM emp GROUP BY dept_id ORDER BY dept_id;
```

```text
--- MySQL 8.4.10 (only_full_group_by 를 끈 세션) ---
+---------+------+--------+
| dept_id | name | salary |
+---------+------+--------+
|    NULL | dan  |    400 |
|      10 | ann  |    300 |
|      20 | cho  |   NULL |
+---------+------+--------+
```

`dept_id=10` 그룹에서 **`ann` 이 나왔다.** `bob` 이 아니라. **왜 `ann` 인가?**

★ **같은 질의를 10회 돌려 봤다. 10회 모두 `ann` 이었다.**

```text
 run 1 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 2 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 ... (중략)
 run 10: NULL dan 400 | 10 ann 300 | 20 cho NULL
   -> 10 / 10 동일
```

★★ **그런데 이것은 「보장」이 아니라 「이번에 이랬다」이다.**\
MySQL 문서가 직접 적는다: *"the server is free to choose any value from each group, so unless they are the same, the values chosen are nondeterministic"*.\
그리고 **`ORDER BY` 로 고를 수 없다**고도 적는다: *"the selection of values from each group cannot be influenced by adding an `ORDER BY` clause"*.

실제로 확인했다 — **`ORDER BY name DESC` 를 붙여도, 안쪽 파생 테이블을 역순으로 정렬해도, `FORCE INDEX(PRIMARY)` 를 걸어도 `ann` 이 나왔다.**

**그러면 언제 바뀌나 — 엔진이 행을 만나는 순서가 바뀌면 바뀐다.**\
같은 두 행을 **입력 순서만 뒤집어** 넣어 보면 값이 따라 바뀐다.

```text
### SQL: (only_full_group_by 를 끈 세션)
SELECT dept_id, name FROM (SELECT * FROM emp WHERE id=2 UNION ALL SELECT * FROM emp WHERE id=1) t GROUP BY dept_id;
--- MySQL 8.4.10 ---
+---------+------+
| dept_id | name |
+---------+------+
|      10 | bob  |     <- bob 이 먼저 오면 bob 이 나온다
+---------+------+

### SQL: SELECT dept_id, name FROM (SELECT * FROM emp WHERE id=1 UNION ALL SELECT * FROM emp WHERE id=2) t GROUP BY dept_id;
--- MySQL 8.4.10 ---
+---------+------+
| dept_id | name |
+---------+------+
|      10 | ann  |     <- ann 이 먼저 오면 ann 이 나온다
+---------+------+
```

두 그림의 결론 — **같은 두 행, 같은 그룹인데 나오는 값이 다르다.**\
★ 즉 이 값은 **데이터의 성질이 아니라 「엔진이 먼저 만난 행」**이다. 계획이 바뀌면(인덱스가 생기면·통계가 바뀌면·행이 늘면) 같이 바뀐다.

```text
 "10회 돌려서 같았다" 가 말해 주는 것          말해 주지 않는 것
 +-------------------------------+            +-------------------------------+
 | 이 데이터 · 이 계획에서는      |            | 다음 배포에서도 같을 것        |
 | ann 이 나왔다                  |            | 행이 늘어도 같을 것            |
 +-------------------------------+            | 인덱스를 추가해도 같을 것      |
   관찰이다                                    +-------------------------------+
                                                 보장이 아니다 — 문서가 부정한다
```

대가 — 끄면 **에러가 사라지고 틀린 값이 남는다.** 가장 나쁜 교환이다.\
★ **설정을 끄는 대신 `ANY_VALUE()` 로 「아무거나 좋다」를 코드에 적어라**(4번). 그러면 읽는 사람이 의도를 안다.

---

### 4. 함수 종속성 예외 — 두 엔진이 인정하는 범위가 다르다

**언제 쓰나** — 「기본키로 묶었는데 왜 다른 열을 못 쓰지」가 막힐 때.

```text
 GROUP BY 에 기본키가 들어 있으면
 그룹 하나 = 행 하나다 -> 나머지 열도 값이 하나로 정해진다
 이것을 "함수 종속" 이라 부르고, 두 엔진 다 예외로 인정한다
```

```text
### SQL: SELECT id, name, dept_id, salary, COUNT(*) AS c FROM emp GROUP BY id ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary | c    +----+------+---------+--------+---+
----+------+---------+--------+---   | id | name | dept_id | salary | c |
  1 | ann  |      10 |    300 | 1    +----+------+---------+--------+---+
  2 | bob  |      10 |    500 | 1    |  1 | ann  |      10 |    300 | 1 |
  3 | cho  |      20 |   NULL | 1    |  2 | bob  |      10 |    500 | 1 |
  4 | dan  |    NULL |    400 | 1    |  3 | cho  |      20 |   NULL | 1 |
(4 rows)                             |  4 | dan  |    NULL |    400 | 1 |
                                     +----+------+---------+--------+---+
```

**여기까지는 양쪽이 같다.** 갈리는 곳은 **어디까지를 종속으로 보나**다.

**(가) `UNIQUE NOT NULL` 열로 묶기** — `dept.name` 은 `UNIQUE NOT NULL` 이다.

```text
### SQL: SELECT d.id, d.name FROM dept d GROUP BY d.name ORDER BY d.name;
--- PG 18.6 ---
ERROR:  column "d.id" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT d.id, d.name FROM dept d GROUP BY d.name ORDER BY d.n...
               ^
--- MySQL 8.4.10 ---
+----+-------+
| id | name  |
+----+-------+
| 20 | dev   |
| 30 | hr    |
| 10 | sales |
+----+-------+
```

**(나) 조인 건너편의 열** — `e.id` 로 묶으면 `d.name` 도 하나로 정해진다(`e.id` → `e.dept_id` → `d.id` → `d.name`).

```text
### SQL: SELECT e.id, e.name, d.name AS dept, COUNT(*) AS c
         FROM emp e JOIN dept d ON e.dept_id = d.id GROUP BY e.id ORDER BY e.id;
--- PG 18.6 ---
ERROR:  column "d.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT e.id, e.name, d.name AS dept, COUNT(*) AS c FROM emp ...
                             ^
--- MySQL 8.4.10 ---
+----+------+-------+---+
| id | name | dept  | c |
+----+------+-------+---+
|  1 | ann  | sales | 1 |
|  2 | bob  | sales | 1 |
|  3 | cho  | dev   | 1 |
+----+------+-------+---+
```

두 그림의 결론 — ★ **MySQL 의 종속성 탐지가 PG 보다 넓다.**

| 그룹 키 | 다른 열 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|---|
| **같은 표의 기본키**(`emp.id`) | 같은 표의 열 | **허용** | **허용** |
| `UNIQUE NOT NULL` 열(`dept.name`) | 같은 표의 열 | **거부** | **허용** |
| 기본키(`emp.id`) | **조인 건너편**(`d.name`) | **거부** | **허용** |

MySQL 문서가 종속의 근거를 적는다 — **기본키**이거나 **`UNIQUE NOT NULL` 열**이면 종속으로 본다.\
PG 는 **`GROUP BY` 에 그 표의 기본키가 들어 있을 때, 그 표의 열**만 인정한다. 조인 건너편은 안 따라간다.

**양쪽에서 도는 형태는 `ANY_VALUE()` 다 — 그리고 PG 18.6 에도 있다.**

```text
### SQL: SELECT dept_id, ANY_VALUE(name) AS a_name, COUNT(*) AS c FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | a_name | c            +---------+--------+---+
---------+--------+---           | dept_id | a_name | c |
      10 | ann    | 2            +---------+--------+---+
      20 | cho    | 1            |    NULL | dan    | 1 |
    NULL | dan    | 1            |      10 | ann    | 2 |
(3 rows)                         |      20 | cho    | 1 |
                                 +---------+--------+---+
```

★ **`ANY_VALUE` 는 「아무 값」을 **고르는** 함수가 아니라 「아무 값이어도 좋다」를 **선언하는** 함수다.**\
값 자체는 3번과 똑같이 보장되지 않는다. 달라지는 것은 **읽는 사람이 그것을 안다**는 점이다.\
PG 문서가 *"Returns an arbitrary value from the non-null input values"* 라고 적는다 — **arbitrary** 가 계약이다.

비용 — 없다. 타이핑 몇 글자로 **「이 열은 아무거나 좋다」는 의도를 코드에 박는 것**이 전부의 값이다.

---

### 5. `GROUP BY` 에 무엇을 적을 수 있나 — 표현식·별칭·서수

**언제 쓰나** — 계산된 값으로 묶어야 할 때. 그리고 같은 식을 두 번 쓰기 싫을 때.

```text
GROUP BY <열>        가장 흔한 형태
GROUP BY <표현식>    salary * 12 같은 계산 결과로 묶는다
GROUP BY <별칭>      SELECT 에서 붙인 이름을 다시 쓴다   <- 양쪽 다 된다
GROUP BY <서수>      SELECT 목록의 N 번째              <- 양쪽 다 된다
GROUP BY <집계>      금지                              <- 양쪽 다 에러
```

```text
### SQL: SELECT salary * 12 AS annual, COUNT(*) AS c FROM emp GROUP BY salary * 12 ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual | c                      +--------+---+
--------+---                     | annual | c |
   3600 | 1                      +--------+---+
   4800 | 1                      |   NULL | 1 |
   6000 | 1                      |   3600 | 1 |
   NULL | 1                      |   4800 | 1 |
(4 rows)                         |   6000 | 1 |
                                 +--------+---+
```

**같은 질의를 별칭으로 써도 양쪽에서 돈다.**

```text
### SQL: SELECT salary * 12 AS annual, COUNT(*) AS c FROM emp GROUP BY annual ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual | c                      +--------+---+
--------+---                     | annual | c |
   3600 | 1                      +--------+---+
   4800 | 1                      |   NULL | 1 |
   6000 | 1                      |   3600 | 1 |
   NULL | 1                      |   4800 | 1 |
(4 rows)                         |   6000 | 1 |
                                 +--------+---+
```

★ **`GROUP BY` 의 별칭은 양쪽에서 된다** — 갈리는 것은 `HAVING` 이다([01번](../01-logical-query-processing-order/)·[03번](../03-where-vs-having/)이 정본).\
`WHERE` 는 **양쪽 다 안 된다.** 별칭은 5번 칸(`SELECT`)에서 태어나는데 `WHERE` 는 2번 칸이기 때문이다.

**서수도 양쪽에서 된다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY 1 ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c                     +---------+---+
---------+---                    | dept_id | c |
      10 | 2                     +---------+---+
      20 | 1                     |    NULL | 1 |
    NULL | 1                     |      10 | 2 |
(3 rows)                         |      20 | 1 |
                                 +---------+---+
```

**집계 함수는 못 쓴다.** 그룹을 만드는 칸이 그룹의 집계 결과를 입력으로 받을 수 없다.

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY COUNT(*);
--- PG 18.6 ---
ERROR:  aggregate functions are not allowed in GROUP BY
LINE 1: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY COUNT(*);
                                                        ^
--- MySQL 8.4.10 ---
ERROR 1056 (42000) at line 1: Can't group on 'c'
```

그림 해설 — MySQL 이 별칭 `'c'` 로 부르는 것은 **MySQL 이 `GROUP BY` 에서 출력 열 이름을 먼저 찾기** 때문이다.\
**거부한다는 사실은 같다.** 자세한 대비는 [21번](../21-aggregate-functions-count-forms/)에 있다.

대가 — 서수는 짧지만 **`SELECT` 목록을 고치면 조용히 다른 열로 묶인다.** 읽는 사람이 위를 세어야 한다.

---

### 6. `NULL` 은 한 그룹으로 묶인다 — 비교 규칙과 정반대다

**언제 쓰나** — 그룹 결과에 `NULL` 행이 보일 때. 그리고 [21번](../21-aggregate-functions-count-forms/)의 `COUNT(DISTINCT)` 와 견줄 때.

```text
 비교에서는                        묶기에서는
 NULL = NULL  ->  UNKNOWN          NULL 과 NULL  ->  같은 그룹
 (같다고 하지 않는다)                (하나로 접는다)
```

```text
### SQL: SELECT dept_id, COUNT(*) AS c, SUM(salary) AS s FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c |  s                +---------+---+------+
---------+---+------             | dept_id | c | s    |
      10 | 2 |  800              +---------+---+------+
      20 | 1 | NULL              |    NULL | 1 |  400 |
    NULL | 1 |  400              |      10 | 2 |  800 |
(3 rows)                         |      20 | 1 | NULL |
                                 +---------+---+------+
```

그림 해설 — **`dept_id=NULL` 이 버려지지 않고 한 그룹으로 남았다.** `dan` 이 거기 들어 있다.\
`dept_id=20` 의 `SUM` 이 `NULL` 인 것은 **`cho` 의 급여가 없어서**다([21번](../21-aggregate-functions-count-forms/)).

★ **같은 열에 두 규칙이 동시에 적용된다.**

```text
 dept_id = [10, 10, 20, NULL]

 GROUP BY dept_id            -> 3 그룹   (10 · 20 · NULL)     NULL 도 한 그룹
 COUNT(DISTINCT dept_id)     -> 2        (10 · 20)            NULL 은 안 센다
                                  ^^^
              같은 데이터, 같은 열. 3 과 2 다.  규칙이 다르기 때문이다
```

대가 — 「`NULL` 은 무조건 서로 다르다」로 외우면 여기서 틀린다. **비교는 `UNKNOWN`, 묶기는 같은 것 취급.**\
그리고 **`NULL` 그룹은 「소속 없음」이라는 뜻이 있는 그룹**이다. [23번](../23-grouping-sets-rollup-cube/)에서 **소계 행의 `NULL`** 과 이 `NULL` 이 한 화면에 섞인다 — 거기가 이 묶음의 정점 중 하나다.

> **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 기준. `GROUP BY`·`DISTINCT` 가 이 기준을 쓴다.\
> 예: `NULL` 둘은 같다고 말할 수 없지만 구별할 수도 없으므로 한 그룹이 된다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
SELECT <그룹 키> , <집계 함수>          -- 이 둘만 쓸 수 있다
FROM   <표>
WHERE  <행 조건>                        -- 그룹 만들기 전. 별칭 불가
GROUP  BY <열 | 표현식 | 별칭 | 서수>    -- 집계 함수는 불가
HAVING <그룹 조건>                       -- 그룹 만든 뒤 (03번이 정본)
ORDER  BY <그룹 키 | 집계 | 별칭>
```

규칙 여덟.

1. **`GROUP BY` 뒤의 칸은 그룹만 본다.** `HAVING`·`SELECT`·`ORDER BY` 가 전부 같은 제약을 받는다.
2. **쓸 수 있는 것은 그룹 키와 집계 결과 둘뿐이다.** 나머지는 비집계 열이고 값이 안 정해진다.
3. **`GROUP BY` 가 없어도 집계가 하나 있으면 표 전체가 한 그룹**이라 같은 규칙이 걸린다(MySQL `ERROR 1140`).
4. **PG 는 예외 없이 거부한다.** 예외는 **그 표의 기본키가 `GROUP BY` 에 있을 때, 그 표의 열**뿐이다.
5. **MySQL 은 `only_full_group_by` 에 달렸다.** 기본 `sql_mode` 에 들어 있어 기본은 거부다.
6. **MySQL 의 종속성 탐지가 더 넓다** — `UNIQUE NOT NULL` 열, 조인 건너편까지 따라간다.
7. **`ANY_VALUE()` 는 양쪽에 있다**(PG 는 16부터). 설정을 끄는 것보다 이쪽이 낫다.
8. **`NULL` 은 한 그룹으로 묶인다.** `COUNT(DISTINCT)` 가 `NULL` 을 안 세는 것과 **정반대**다.

실전 형태는 사실상 **셋**이다.

```sql
-- (1) 그룹 키 + 집계 — 표준형
SELECT dept_id, COUNT(*), SUM(salary) FROM emp GROUP BY dept_id;

-- (2) 부속 정보가 필요하면 GROUP BY 에 같이 넣는다 (값이 같은 열끼리)
SELECT d.id, d.name, COUNT(e.id) FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name;

-- (3) 정말 아무거나 좋으면 그렇게 적는다
SELECT dept_id, ANY_VALUE(name), COUNT(*) FROM emp GROUP BY dept_id;
```

(2)에서 `d.name` 을 `GROUP BY` 에 같이 넣는 것이 **양쪽 엔진에서 도는 유일한 이식 형태**다 — PG 가 조인 건너편 종속을 안 따라가기 때문이다.

## 어디서 틀리나

- **★ `SELECT` 에 비집계 열을 넣는다.**\
  가장 흔하다. PG 는 즉시 거부하고 MySQL 도 기본 설정에서는 거부한다. **거부가 정상이다.**
- **★ MySQL 에서 `only_full_group_by` 를 꺼서 「고친다」.**\
  에러가 사라지고 **틀린 값이 남는다.** 10회 돌려 같았다고 보장이 아니다 — 입력 순서만 바꿔도 `ann` 이 `bob` 이 됐다.
- **★ 「10회 돌려 같았으니 안정적이다」로 결론 낸다.**\
  문서가 *nondeterministic* 이라고 못 박는다. 관찰은 관찰로, 보장은 문서로만 적는다.
- **PG 에서 되던 것이 MySQL 에서도 되리라 믿는다 — 반대 방향이 더 위험하다.**\
  MySQL 에서 돌던 종속성 질의(`UNIQUE NOT NULL`·조인 건너편)가 **PG 에서 깨진다.**
- **`ORDER BY` 로 그룹 대표 행을 고르려 한다.**\
  MySQL 문서가 *"cannot be influenced by adding an `ORDER BY` clause"* 라고 적는다. 실행으로도 확인했다.\
  「그룹별 1위 한 행」이 필요하면 **순위 함수**를 쓴다(목록의 **29번 주제**).
- **`GROUP BY` 서수를 쓰고 `SELECT` 목록을 고친다.**\
  조용히 다른 열로 묶인다. 서수는 짧은 임시 질의에만.
- **`NULL` 그룹이 빠졌다고 생각한다.**\
  안 빠진다. 한 그룹으로 남는다. 빠지는 것은 `COUNT(DISTINCT)` 쪽이다.
- **`GROUP BY` 로 0건 그룹을 기대한다.**\
  `GROUP BY` 는 들어온 행에서만 그룹을 만든다. 0건을 보이려면 외부 조인이다([14번](../14-left-right-outer-join/)·[21번](../21-aggregate-functions-count-forms/)).

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `GROUP BY` 뒤의 칸이 그룹만 본다 | **결과의 정의** | 언어 — 두 문서가 같은 모양으로 적는다 |
| 그룹 키와 집계 결과만 쓸 수 있다 | **결과의 정의** | 언어 |
| `NULL` 끼리 한 그룹이 된다 | **결과의 정의** | 언어 |
| 기본키가 `GROUP BY` 에 있을 때의 예외 | **정의된 예외** | 언어 — 다만 **범위가 엔진마다 다르다**(4번) |
| `UNIQUE NOT NULL`·조인 건너편 종속 | 엔진의 탐지 능력 | **MySQL 만** 인정한다. 이식되지 않는다 |
| `only_full_group_by` 를 끈 뒤의 **값** | **아무것도 보장 안 함** | 문서가 *nondeterministic* 이라고 명시 |
| 끈 상태에서 10회 같은 값이 나온 것 | **관찰** | 보장 아님 — 입력 순서만 바꿔도 달라졌다 |
| `ANY_VALUE()` 가 돌려주는 값 | **arbitrary** | 함수의 계약이 「아무 값」이다. 특정 값을 약속하지 않는다 |
| 결과 **행 순서** | 아무도 보장 안 함 | `ORDER BY` 없이는 어느 엔진도 순서를 약속하지 않는다 |

- **이 주제는 두 엔진이 가장 크게 갈리는 자리 중 하나다.** 2·3·4번이 전부 방언이다.
- **갈리는 방향이 한쪽이다** — MySQL 에서 돌던 것이 PG 에서 깨진다. 반대는 거의 없다.
- **에러 메시지는 근거로 쓸 수 있다.** `1055`·`1140`·`1056` 세 번호가 각각 다른 자리를 가리킨다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 「무엇별 몇 개」가 필요할 때.** 그룹 키를 먼저 정하고 나머지는 전부 집계로 감싼다.
- **쓴다 — 중복 제거에.** 집계 없는 `GROUP BY` 는 `DISTINCT` 와 같다. 뒤에 집계를 붙일 계획이면 `GROUP BY` 가 읽기 낫다([목록의 **7번 주제**](../07-distinct-and-duplicate-removal/)).
- **안 쓴다 — 행마다 값을 붙여야 할 때.** 그룹으로 접으면 원래 행이 사라진다. 그건 **윈도우 함수**다(목록의 **26번 주제**).
- **안 쓴다 — 「그룹별 상위 N개」.** `GROUP BY` 는 그룹당 한 행이다. 순위 함수를 쓴다(목록의 **29번 주제**).
- **`ANY_VALUE` 는 의도가 진짜 「아무거나」일 때만.** 「대표값」이 필요하면 `MIN`/`MAX` 로 **무엇인지 적어라.**
- **`only_full_group_by` 는 끄지 않는다.** 옮기는 중이라면 끈 채로 두지 말고 질의를 고쳐 나간다.

## 핵심 문장

- `GROUP BY` 는 처리 순서의 **3번 칸**이고, 거기서 **입력이 행에서 그룹으로 바뀐다.**
- 그 뒤 칸(`HAVING`·`SELECT`·`ORDER BY`)에서 쓸 수 있는 것은 **그룹 키와 집계 결과 둘뿐**이다.
- **비집계 열이 거부되는 이유는 「값이 하나로 안 정해져서」다** — `dept_id=10` 봉투에 `ann` 과 `bob` 이 있다.
- **PG 는 거부하고, MySQL 은 `only_full_group_by` 에 달렸다**(기본 `sql_mode` 에 포함 = 기본 거부).
- ★ **끈 상태의 값은 보장이 아니다.** 10회 같았지만 **입력 순서만 바꾸니 `ann` 이 `bob` 이 됐다.**
- ★ **`ORDER BY` 로는 그 값을 못 고른다** — 문서가 그렇게 적고, 실행으로도 확인했다.
- **MySQL 의 함수 종속성 탐지가 더 넓다** — `UNIQUE NOT NULL` 열과 **조인 건너편**까지 따라간다. PG 는 안 따라간다.
- **`ANY_VALUE()` 는 양쪽에 있다**(PG 16+). 설정을 끄는 대신 **「아무거나 좋다」를 코드에 적는** 쪽이다.
- **`NULL` 은 한 그룹으로 묶인다** — `COUNT(DISTINCT)` 가 `NULL` 을 안 세는 것과 **정반대**다(3그룹 대 2).

## 관련 자료

- [PostgreSQL 18 · Table Expressions (GROUP BY and HAVING)](https://www.postgresql.org/docs/18/queries-table-expressions.html) — 그룹 키와 집계만 쓸 수 있다는 규칙, 기본키 예외.
- [MySQL 8.4 · MySQL Handling of GROUP BY](https://dev.mysql.com/doc/refman/8.4/en/group-by-handling.html) — `ONLY_FULL_GROUP_BY`·함수 종속성 탐지·`ANY_VALUE()`·*nondeterministic* 문장이 전부 이 페이지에 있다.
- [PostgreSQL 16 릴리스 노트](https://www.postgresql.org/docs/release/16.0/) — `ANY_VALUE()` 추가.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 여덟 칸 전체의 좌표계까지, 여기는 3번 칸이 입력을 무엇으로 바꾸나부터.**
- [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/) — **경계: 거기는 2번 칸과 4번 칸의 대비와 `HAVING` 의 별칭 방언까지, 여기는 같은 규칙이 `SELECT`·`ORDER BY` 에도 걸린다는 것부터.** 중복해 적지 않는다.
- [21 집계 함수와 COUNT 의 세 형태](../21-aggregate-functions-count-forms/) — **경계: 그쪽은 집계 함수 하나하나의 의미까지, 여기는 그 함수들이 무엇 위에서 도나부터.**
- [23 GROUPING SETS·ROLLUP·CUBE](../23-grouping-sets-rollup-cube/) — **경계: 여기는 그룹이 하나의 집합일 때까지, 여러 집합을 한 번에 내는 것은 거기.**
- [24 조건부 집계 — FILTER 와 CASE](../24-conditional-aggregation-filter-case/) — 그룹 안에서 **조건별로 나눠 세는** 법.
- [25 조인 팬아웃](../25-join-fan-out/) — **경계: 여기는 한 표를 묶을 때까지, 조인이 행을 늘린 뒤의 집계는 거기.**
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — 「비교는 `UNKNOWN`, 묶기는 한 그룹」의 뿌리.
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — 「0건인 그룹」을 표에 남기는 법.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **그룹 키(group key)** — `GROUP BY` 에 적은 식. 한 그룹 안에서 값이 **하나로 정해진다.**\
  예: `GROUP BY dept_id` 의 `dept_id`. 그래서 `SELECT dept_id` 가 허용된다.
- **비집계 열(non-aggregated column)** — 집계 함수로 감싸지 않은 열. 그룹 키가 아니면 값이 안 정해진다.\
  예: `dept_id=10` 그룹의 `name` 은 `ann` 과 `bob` 둘이다.
- **`ONLY_FULL_GROUP_BY`** — MySQL 의 `sql_mode` 항목. 비집계 열을 **거부**하게 만든다. **8.4 기본값에 들어 있다.**\
  예: 끄면 `SELECT dept_id, name … GROUP BY dept_id` 가 돌고, 나오는 `name` 은 보장되지 않는다.
- **함수 종속(functional dependency)** — 한 열의 값이 정해지면 다른 열의 값도 하나로 정해지는 관계.\
  예: `emp.id` 가 정해지면 `emp.name` 도 하나다. 그래서 `GROUP BY id` 뒤에 `name` 을 쓸 수 있다.
- **`ANY_VALUE()`** — 그룹에서 **아무 값 하나**를 돌려주는 집계 함수. 값은 보장되지 않는다.\
  예: `ANY_VALUE(name)` 은 `dept_id=10` 에서 `ann` 을 냈지만 `bob` 이어도 규칙 위반이 아니다.
- **비결정적(nondeterministic)** — 같은 입력에 같은 답이 나온다고 **약속되지 않은** 것.\
  예: `only_full_group_by` 를 끈 뒤의 `name`. 10회 같았지만 입력 순서를 바꾸니 달라졌다.
- **`sql_mode`** — MySQL 의 동작 방식을 바꾸는 설정 묶음. 세션 단위로도 바꿀 수 있다.\
  예: `SET SESSION sql_mode = REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', '')`.
- **서수(ordinal)** — `SELECT` 목록의 N 번째를 가리키는 숫자.\
  예: `GROUP BY 1` 은 첫 열로 묶는다. 목록을 고치면 가리키는 열이 바뀐다.
- **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 기준.\
  예: `GROUP BY` 가 이 기준을 써서 `NULL` 둘을 한 그룹으로 만든다.
- **`ERROR 1055` · `ERROR 1140`** — MySQL 이 비집계 열을 거부할 때 쓰는 두 번호.\
  예: `GROUP BY` 가 있으면 1055, 집계만 있고 `GROUP BY` 가 없으면 1140 이다.

## 더 들어가면

- **왜 표준이 이렇게 엄격한가** — 그룹 하나에 값이 여럿일 때 **어느 것을 고를지 정의할 방법이 없기 때문**이다.\
  MySQL 이 옛날에 허용했던 것은 표준을 넓힌 게 아니라 **답을 정의하지 않은 채 값을 돌려준 것**이고, 그래서 8.0 부터 기본을 거부로 바꿨다.
- **「그룹별 대표 행 전체」가 필요하면 `GROUP BY` 가 아니다.**\
  `ANY_VALUE` 를 여러 열에 쓰면 **서로 다른 행에서 온 값이 한 줄에 섞일 수 있다** — 그 조합은 실제로 존재한 적이 없는 행이 된다.\
  「그룹별 급여 1위의 이름과 급여」가 필요하면 순위 함수(목록의 **29번 주제**)나 `LATERAL`([20번](../20-lateral-join/))이다.
- **`GROUP BY` 의 계획은 두 갈래다** — 정렬 후 묶기(sort + group) 와 해시로 묶기(hash aggregate).\
  둘 중 무엇이 뽑히는지는 목록의 **59번 주제**, 그 판단을 읽는 법은 **58번 주제**다. **여기서는 재지 않았다.**
- **`GROUPING SETS` 를 쓰면 한 질의가 여러 그룹 집합을 동시에 낸다** — 그때 `NULL` 의 의미가 하나 더 생긴다([23번](../23-grouping-sets-rollup-cube/)).
