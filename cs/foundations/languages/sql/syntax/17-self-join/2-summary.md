# sql/17-SELF JOIN — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions (Joined Tables)](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 상사-부하 절의 `staff` 표는 **기존 `emp` 에서 만들어 트랜잭션 안에서 쓰고 롤백**했다(MySQL 은 `CREATE` → 질의 → `DROP`). 만드는 문은 그 절에 적어 두었다.\
> **`emp`·`dept` 는 한 행도 바꾸지 않았다.**\
> **버전** — `SELF JOIN` 은 전용 문법이 아니라 **같은 표를 두 별칭으로 여는 사용법**이다. 도입 버전이라는 것이 없어 **버전은 적지 않는다.**\
> **선행** — [13 INNER JOIN](../13-inner-join/). 여기서 붙이는 두 표가 **같은 표일 뿐**이다.

## 한눈에 — 쉽게 말하면

**`SELF JOIN` = 같은 명단을 두 장 복사해서 왼쪽 명단과 오른쪽 명단을 맞춰 보는 것. 새 문법은 하나도 없다 — 별칭 두 개가 전부다.**

- 반 아이들의 **짝을 정한다**고 하자. 명단은 하나뿐이다.
- 그런데 짝을 지으려면 **"고르는 쪽"과 "골라지는 쪽"** 두 목록이 필요하다.
- 그래서 같은 명단을 **두 장 복사**한다. 한 장은 `a`, 한 장은 `b` 라고 이름 붙인다.
- 이제 `a` 의 누군가와 `b` 의 누군가를 조건으로 맞추면 된다.

```text
 표는 하나뿐이다                두 별칭으로 열면
 +----------+                   +----------+        +----------+
 |   emp    |                   | emp AS a |        | emp AS b |
 |  4행     |       ───▶        |   4행    |  JOIN  |   4행    |
 +----------+                   +----------+        +----------+
                                      └──── ON a.? = b.? ────┘
                                                ↓
                                  같은 표의 행끼리 비교할 수 있다
```

이 명단 두 장이 **똑같은 구조로** `SELF JOIN` 이다.

| 비유 | 실체 |
|---|---|
| 명단 한 장 | `emp` 테이블 |
| 복사한 두 장 | 두 별칭 `a`·`b` |
| 왼쪽 장에서 고른 사람 | `a` 쪽 행 |
| 오른쪽 장에서 고른 사람 | `b` 쪽 행 |
| "같은 반인 다른 사람" | `ON a.dept_id = b.dept_id AND a.id <> b.id` |
| 복사하지 않고 한 장으로 짝 짓기 | **별칭 없이 조인** → 에러 |

> **`SELF JOIN`(자체 조인)** — 같은 표를 서로 다른 별칭으로 두 번 열어 조인하는 것.\
> 예: `FROM emp a JOIN emp b ON a.dept_id = b.dept_id` — 같은 부서 사람끼리 짝짓기.

**`SELF JOIN` 이라는 키워드는 SQL 에 없다.** `JOIN` 문법 그대로이고, 붙이는 대상이 같은 표일 뿐이다.

## 이 주제가 답하려는 질문

1. **별칭이 없으면 왜 안 되나?** — 에러 메시지가 무엇을 말해 주나.
2. **자기 자신과 짝이 되는 것과 같은 쌍이 두 번 나오는 것**을 어떻게 막나? — `<>` 와 `<` 의 차이.
3. **자기 참조 열이 없는 표에서도** 계층을 다룰 수 있나?

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

**문제 하나 — `emp` 에는 「상사」 열이 없다.**\
`SELF JOIN` 의 교과서 예제인 상사-부하 관계를 보려면 **자기 자신을 가리키는 열**이 필요하다.\
그래서 아래 3번 절에서 **기존 `emp` 에서 `staff` 를 만들어** 쓰고, **트랜잭션으로 되돌린다.**\
`emp` 와 `dept` 는 **한 행도 바꾸지 않는다.**

```text
staff — emp 의 네 행에 mgr_id 한 칸을 더한 것 (3번 절에서만 쓴다)
+----+------+---------+--------+--------+
| id | name | dept_id | salary | mgr_id |
+----+------+---------+--------+--------+
|  1 | ann  |      10 |    300 |   NULL |   <- ann 이 꼭대기
|  2 | bob  |      10 |    500 |      1 |   <- bob 의 상사는 ann
|  3 | cho  |      20 |   NULL |      1 |   <- cho 의 상사도 ann
|  4 | dan  |    NULL |    400 |      2 |   <- dan 의 상사는 bob
+----+------+---------+--------+--------+
```

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

### 1. 별칭이 없으면 **문이 서지 않는다**

**언제 쓰나** — `SELF JOIN` 을 처음 쓸 때. 여기서 막히고, 그 에러가 이 주제의 출발점이다.

```text
 FROM emp JOIN emp ON emp.id = emp.id
           ↑        ↑     ↑        ↑
           |        |     └────────┴── 이 emp 는 어느 쪽인가?
           └────────┴───────────────── 이름이 하나뿐이라 구별이 안 된다
```

```text
### SQL: SELECT * FROM emp JOIN emp ON emp.id = emp.id;
--- PG 18.6 ---
ERROR:  table name "emp" specified more than once
--- MySQL 8.4.10 ---
ERROR 1066 (42000) at line 1: Not unique table/alias: 'emp'
```

쉼표 표기도 마찬가지다 — 이 결과는 [10번](../10-from-clause-aliases-derived-tables/)에서 이미 확인한 것이다.

```text
### SQL: SELECT * FROM emp, emp;
--- PG 18.6 ---
ERROR:  table name "emp" specified more than once
--- MySQL 8.4.10 ---
ERROR 1066 (42000) at line 1: Not unique table/alias: 'emp'
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 같은 표를 별칭 없이 두 번 | `table name "emp" specified more than once` | `ERROR 1066 … Not unique table/alias: 'emp'` |

그림 해설 — **막는 이유는 "중복"이 아니라 "이름이 안 정해짐"이다.** MySQL 의 문구가 그것을 더 정확히 말한다 — `Not unique table/alias`.\
`FROM` 은 이름 공간을 만드는 칸이고, 한 이름에 두 대상을 넣을 수 없다([10번](../10-from-clause-aliases-derived-tables/)).\
비용 — 없다. **이 벽은 시끄럽게 막아 준다** — 이 주제에서 조용한 실패는 별칭이 아니라 뒤의 `ON` 조건에서 난다.

★ **별칭을 붙이면 그 순간 두 개의 독립된 표가 된다.**

---

### 2. 별칭 둘을 붙이면 — 같은 부서 짝짓기

**언제 쓰나** — 같은 표의 행끼리 비교할 때. "같은 부서 동료", "같은 날 주문한 다른 건" 같은 요구.

```text
(전) a 4행 × b 4행 = 16 짝            (후) ON 으로 거른다
 a\b   ann  bob  cho  dan
 ann    .    +    -    -              ON a.dept_id = b.dept_id AND a.id < b.id
 bob    -    .    -    -                            ↓
 cho    -    -    .    -                       ann - bob  1쌍
 dan    -    -    -    .
        ↑
   . = 자기 자신 · + = 통과 · - = 탈락
```

먼저 **16 짝이 만들어지는 것**을 세어 본다.

```text
### SQL: SELECT COUNT(*) AS n FROM emp a CROSS JOIN emp b;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +----+
----                             | n  |
 16                              +----+
(1 row)                          | 16 |
                                 +----+
```

**4 × 4 = 16.** `SELF JOIN` 은 [12번](../12-cartesian-product-cross-join/)의 카티션곱을 **같은 표에 대고** 만든 뒤 거르는 것이다.

**자기 자신을 막는 조건을 빼면** 자기 짝이 섞여 들어온다.

```text
### SQL: SELECT a.name, b.name FROM emp a JOIN emp b ON a.dept_id = b.dept_id ORDER BY a.id, b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | name                     +------+------+
------+------                    | name | name |
 ann  | ann                      +------+------+
 ann  | bob                      | ann  | ann  |
 bob  | ann                      | ann  | bob  |
 bob  | bob                      | bob  | ann  |
 cho  | cho                      | bob  | bob  |
(5 rows)                         | cho  | cho  |
                                 +------+------+
```

**`ann-ann`·`bob-bob`·`cho-cho` 세 줄이 자기 짝이다.** `dan` 은 `dept_id` 가 `NULL` 이라 자기 자신과도 안 붙는다 — `NULL = NULL` 도 `UNKNOWN` 이다([04번](../04-null-three-valued-logic/)).

`<>` 로 거르면 **같은 쌍이 두 번** 나온다.

```text
### SQL: SELECT a.name, b.name FROM emp a JOIN emp b
         ON a.dept_id = b.dept_id AND a.id <> b.id ORDER BY a.id, b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | name                     +------+------+
------+------                    | name | name |
 ann  | bob                      +------+------+
 bob  | ann                      | ann  | bob  |
(2 rows)                         | bob  | ann  |
                                 +------+------+
```

`<` 로 거르면 **한 번만** 나온다.

```text
### SQL: SELECT a.name, b.name FROM emp a JOIN emp b
         ON a.dept_id = b.dept_id AND a.id < b.id ORDER BY a.id, b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | name                     +------+------+
------+------                    | name | name |
 ann  | bob                      +------+------+
(1 row)                          | ann  | bob  |
                                 +------+------+
```

```text
 조건            자기 자신   (ann,bob)   (bob,ann)   결과
 -------------   ---------   ---------   ---------   -----
 (조건 없음)     들어온다      O           O         4 + 2 = …
 a.id <> b.id    막힌다        O           O         2행   <- 같은 쌍이 두 번
 a.id < b.id     막힌다        O           X         1행   <- 한 번만
```

그림 해설 — **`<>` 는 자기 자신만 막고, `<` 는 자기 자신과 뒤집은 쌍을 함께 막는다.**\
`<` 를 쓰면 `a` 쪽이 항상 작은 id 라서 **순서까지 고정**된다.\
비용 — `<` 는 **등호가 아니라서** 조인 알고리즘 선택이 좁아진다. 다만 `AND` 로 묶인 등호 조건(`a.dept_id = b.dept_id`)이 있으면 그쪽으로 붙고 부등호는 필터로 남는다.

★ **어느 쪽을 쓸지는 요구사항이 정한다** — "모든 (사람, 동료) 조합"이면 `<>`, "중복 없는 쌍 목록"이면 `<`.

---

### 3. 계층 — 상사와 부하

**언제 쓰나** — 한 표 안에서 행이 같은 표의 다른 행을 가리킬 때(조직도·카테고리 트리·답글).

`emp` 에는 자기 참조 열이 없으므로, `emp` 에서 `staff` 를 만들어 쓴다.

<details>
<summary>계층 확인용 표 — 기존 emp 에서 만들고 롤백했다 (PostgreSQL)</summary>

```sql
BEGIN;
CREATE TABLE staff (id int PRIMARY KEY, name text, dept_id int, salary int, mgr_id int);
INSERT INTO staff (id, name, dept_id, salary, mgr_id)
SELECT e.id, e.name, e.dept_id, e.salary, v.mgr
FROM emp e JOIN (VALUES (1,NULL::int),(2,1),(3,1),(4,2)) AS v(id,mgr) ON v.id = e.id;
-- 아래 질의들을 여기서 돌린다
ROLLBACK;
```

MySQL 은 DDL 에 트랜잭션이 안 걸리므로 `CREATE` → 질의 → `DROP TABLE staff` 로 확인했다.\
`VALUES (…),(…)` 행 생성자도 MySQL 에서는 안 되므로([10번](../10-from-clause-aliases-derived-tables/)) `SELECT … UNION ALL SELECT …` 로 바꿨다.

```sql
CREATE TABLE staff (id int PRIMARY KEY, name varchar(20), dept_id int, salary int, mgr_id int);
INSERT INTO staff (id, name, dept_id, salary, mgr_id)
SELECT e.id, e.name, e.dept_id, e.salary, v.mgr
FROM emp e JOIN (SELECT 1 AS id, NULL AS mgr UNION ALL SELECT 2,1
                 UNION ALL SELECT 3,1 UNION ALL SELECT 4,2) AS v ON v.id = e.id;
```

**두 DB 모두 실험 뒤 표가 남아 있지 않다.** `emp`·`dept` 는 읽기만 했다.

</details>

```text
staff 의 mgr_id 가 만드는 그림

        ann (1)              mgr_id = NULL   <- 꼭대기
        /     \
     bob (2)  cho (3)        mgr_id = 1
      /
   dan (4)                   mgr_id = 2
```

**한 단계 — 부하와 상사를 한 줄에 놓는다.**

```text
### SQL: SELECT e.name AS emp, m.name AS mgr FROM staff e JOIN staff m ON e.mgr_id = m.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | mgr                       +------+------+
-----+-----                      | emp  | mgr  |
 bob | ann                       +------+------+
 cho | ann                       | bob  | ann  |
 dan | bob                       | cho  | ann  |
(3 rows)                         | dan  | bob  |
                                 +------+------+
```

**`ann` 이 없다.** `ann.mgr_id` 가 `NULL` 이라 `NULL = m.id` 가 `UNKNOWN` 이고, 내부 조인은 `TRUE` 만 통과시킨다([13번](../13-inner-join/)).

```text
### SQL: SELECT e.name AS emp, m.name AS mgr FROM staff e LEFT JOIN staff m ON e.mgr_id = m.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | mgr                       +------+------+
-----+-----                      | emp  | mgr  |
 ann |                           +------+------+
 bob | ann                       | ann  | NULL |
 cho | ann                       | bob  | ann  |
 dan | bob                       | cho  | ann  |
(4 rows)                         | dan  | bob  |
                                 +------+------+
```

그림 해설 — **계층에서 `SELF JOIN` 은 거의 항상 `LEFT JOIN` 이다.** 꼭대기 행의 상사 열은 `NULL` 일 수밖에 없고, 내부 조인은 그 행을 버린다([14번](../14-left-right-outer-join/)).\
비용 — 없다. **다만 `INNER` 를 쓰면 꼭대기가 사라진 것을 결과만 보고는 알 수 없다.**

**두 단계 — 별칭을 셋 붙이면 할아버지까지 간다.**

```text
### SQL: SELECT e.name AS emp, m.name AS mgr, g.name AS grand FROM staff e
         LEFT JOIN staff m ON e.mgr_id = m.id
         LEFT JOIN staff g ON m.mgr_id = g.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | mgr | grand               +------+------+-------+
-----+-----+-------              | emp  | mgr  | grand |
 ann |     |                     +------+------+-------+
 bob | ann |                     | ann  | NULL | NULL  |
 cho | ann |                     | bob  | ann  | NULL  |
 dan | bob | ann                 | cho  | ann  | NULL  |
(4 rows)                         | dan  | bob  | ann   |
                                 +------+------+-------+
```

```text
 별칭 하나 = 계층 한 단계
 e        ->  본인
 e, m     ->  본인 + 상사          (별칭 2개)
 e, m, g  ->  본인 + 상사 + 상사의 상사   (별칭 3개)
             ↑
   깊이가 N 이면 별칭이 N 개 필요하다 — 이것이 SELF JOIN 의 한계다
```

그림 해설 — **깊이를 모르면 `SELF JOIN` 으로는 못 푼다.** 조직도가 몇 단인지 질의를 쓸 때 정해져야 한다.\
비용 — 깊이가 **미지수**이면 재귀 CTE 로 간다([목록의 **33번 주제**](../33-recursive-cte/)). **경계: 여기는 깊이가 고정일 때까지, 거기는 깊이가 미지수일 때부터.**

**방향을 뒤집으면 부하 수를 센다.**

```text
### SQL: SELECT m.name AS mgr, COUNT(e.id) AS reports FROM staff m
         LEFT JOIN staff e ON e.mgr_id = m.id GROUP BY m.id, m.name ORDER BY m.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 mgr | reports                   +------+---------+
-----+---------                  | mgr  | reports |
 ann |       2                   +------+---------+
 bob |       1                   | ann  |       2 |
 cho |       0                   | bob  |       1 |
 dan |       0                   | cho  |       0 |
(4 rows)                         | dan  |       0 |
                                 +------+---------+
```

★ **`COUNT(e.id)` 이지 `COUNT(*)` 가 아니다.** `LEFT JOIN` 으로 남은 `cho`·`dan` 의 행은 오른쪽이 전부 `NULL` 인데, `COUNT(*)` 는 그 행도 1 로 세어 **0 이어야 할 자리에 1 을 찍는다**([21번](../21-aggregate-functions-count-forms/)).

---

### 4. 연속 행 비교 — 「바로 다음 값」과 짝짓기

**언제 쓰나** — 정렬한 이웃끼리 차이를 볼 때(급여 사다리·날짜별 증감·연속 로그).

같은 표를 두 번 열고, `b` 쪽에서 **`a` 보다 큰 값 중 가장 작은 것**을 고른다.

```text
 급여를 줄 세우면        각자의 "바로 위"는
 300 (ann)              ann -> 400 (dan)
 400 (dan)              dan -> 500 (bob)
 500 (bob)              bob -> 없음
 NULL (cho)             cho -> 비교 자체가 UNKNOWN
```

```text
### SQL: SELECT a.name AS lower, b.name AS higher, b.salary - a.salary AS gap
         FROM emp a JOIN emp b ON b.salary = (SELECT MIN(x.salary) FROM emp x WHERE x.salary > a.salary)
         ORDER BY a.salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 lower | higher | gap             +-------+--------+------+
-------+--------+-----            | lower | higher | gap  |
 ann   | dan    | 100             +-------+--------+------+
 dan   | bob    | 100             | ann   | dan    |  100 |
(2 rows)                          | dan   | bob    |  100 |
                                  +-------+--------+------+
```

그림 해설 — `ON` 안에 **상관 서브쿼리**가 들어갔다([11번](../11-subquery-scalar-correlated-any-all/)). `a` 행마다 "그보다 큰 것 중 최솟값"을 계산한다.\
`bob` 은 자기보다 큰 값이 없어 서브쿼리가 0행 → `NULL` 이 되고, `b.salary = NULL` 이 `UNKNOWN` 이라 탈락했다.\
`cho` 는 `salary` 가 `NULL` 이라 `x.salary > NULL` 이 모두 `UNKNOWN` 이라 애초에 시작도 못 했다.\
비용 — `a` 행마다 서브쿼리가 돈다. **이 형태는 행이 많아지면 비싸다.**

★ **같은 일을 윈도우 함수 `LAG`/`LEAD` 로 하면 한 번만 훑는다**([목록의 **30번 주제**](../30-offset-and-boundary-functions/)).\
**경계: 여기는 「같은 표를 두 별칭으로 여는 형태」까지, 거기는 「한 번 훑으며 이웃을 보는 함수」부터.**

## 문법 — 어느 절에서 무엇이 보이나

```sql
FROM emp a JOIN emp b ON <a 와 b 를 잇는 조건>       -- 별칭 둘이 필수
FROM emp a, emp b WHERE <조건>                       -- 옛 표기. 결과는 같다
FROM staff e LEFT JOIN staff m ON e.mgr_id = m.id    -- 계층은 LEFT 가 기본
FROM staff e LEFT JOIN staff m ON …                  -- 별칭 하나 = 계층 한 단계
     LEFT JOIN staff g ON …
```

규칙 여섯.

1. **`SELF JOIN` 이라는 키워드는 없다.** 그냥 `JOIN` 이고, 두 쪽이 같은 표일 뿐이다.
2. **별칭 둘이 필수**다. 없으면 `specified more than once`(PG) / `Not unique table/alias`(MySQL) 다.
3. **모든 열에 한정자를 붙인다.** `id` 라고만 쓰면 어느 쪽인지 정해지지 않는다.
4. **자기 자신과의 짝은 `ON` 이 막아야 한다.** `<>` 는 자기만, `<` 는 자기와 뒤집힌 쌍까지 막는다.
5. **계층은 `LEFT JOIN`** 이다. 꼭대기 행은 부모가 `NULL` 이라 내부 조인이 버린다.
6. **깊이만큼 별칭이 필요하다.** 깊이가 미지수면 재귀 CTE([목록의 **33번 주제**](../33-recursive-cte/))다.

읽을 때 붙잡을 것은 **"a 쪽은 누구이고 b 쪽은 누구인가"** 하나다.

```text
 a 쪽 = 부하      b 쪽 = 상사        ON a.mgr_id = b.id
 a 쪽 = 상사      b 쪽 = 부하        ON b.mgr_id = a.id     <- 방향이 뒤집힌다
        ↑
  같은 표라서 어느 쪽이 어느 역할인지 이름으로는 알 수 없다 —
  별칭을 e/m, child/parent 처럼 역할로 짓는다
```

## 어디서 틀리나

- **별칭을 빼고 쓴다.**\
  `Not unique table/alias` 로 막힌다. **이 에러는 친절하다** — 조용히 지나가지 않는다.
- **`ON` 에 자기 자신을 막는 조건을 빼먹는다.**\
  모든 행이 자기 자신과 짝이 되어 결과에 섞인다. 같은 부서 짝짓기에서 `ann-ann` 이 나온다.
- **`<>` 와 `<` 를 구분하지 않는다.**\
  `<>` 는 `(ann,bob)` 과 `(bob,ann)` 을 **둘 다** 준다. 쌍 목록을 원했다면 두 배로 나온다.
- **계층에 `INNER JOIN` 을 쓴다.**\
  꼭대기(`mgr_id IS NULL`)가 조용히 사라진다. 위에서 `ann` 이 사라졌다.
- **`COUNT(*)` 로 부하 수를 센다.**\
  `LEFT JOIN` 뒤의 `COUNT(*)` 는 짝 없는 행도 1 로 센다. `COUNT(부하쪽 열)` 을 쓴다.
- **깊이가 미지수인 계층을 `SELF JOIN` 으로 푼다.**\
  별칭을 몇 개 붙여야 할지 질의를 쓸 때 정해져야 한다. 미지수면 재귀 CTE 다.
- **별칭을 `a`·`b` 로만 짓는다.**\
  조건이 길어지면 어느 쪽이 상사인지 헷갈린다. `e`(employee)·`m`(manager) 처럼 **역할로 짓는다.**
- **`SELF JOIN` 이 특별한 비용을 쓴다고 생각한다.**\
  같은 표를 두 번 읽을 뿐이고, 계획은 보통의 조인과 같은 연산자로 짜인다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 별칭 없이 같은 표를 두 번 못 연다 | **문법의 규칙** | 언어 — 두 엔진이 같은 이유로 막는다 |
| 두 별칭이 서로 독립된 표처럼 동작한다 | **결과의 정의** | 언어 |
| `a.id < b.id` 가 중복 쌍을 없앤다 | **결과의 정의** | 언어 — 조건식일 뿐이다 |
| 계층 깊이만큼 별칭이 필요하다 | **문법의 한계** | 언어 — `JOIN` 개수는 질의에 적혀야 한다 |
| 같은 표를 두 번 **실제로 읽는가** | 옵티마이저의 선택 | 아무도 — 한 번 읽고 재사용할 수도 있다 |
| 에러 문구 | 그 엔진의 표기 | 다르다 — PG `specified more than once`, MySQL `Not unique table/alias` |

- **`SELF JOIN` 에는 전용 문법도 전용 연산자도 없다.** 그래서 「지원 여부」라는 질문이 성립하지 않는다.
- **결과의 순서는 보장되지 않는다.** 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.
- 4번 절의 `gap` 계산은 **정수 뺄셈**이라 두 엔진에서 같다. 나눗셈이었다면 갈렸다([36번](../36-numeric-types-and-functions/)).

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 같은 표 안의 관계를 따라갈 때.** 조직도·카테고리 트리·답글의 부모.
- **쓴다 — 같은 표의 행끼리 짝지을 때.** "같은 부서 동료 목록", "같은 날 겹친 예약".
- **쓴다 — 깊이가 고정인 계층.** 2~3단이면 `LEFT JOIN` 을 그만큼 쓰는 게 가장 읽기 쉽다.
- **안 쓴다 — 깊이가 미지수일 때.** 재귀 CTE 다([목록의 **33번 주제**](../33-recursive-cte/)).
- **안 쓴다 — 이웃 행 한 개만 필요할 때.** `LAG`/`LEAD` 가 훨씬 싸다([목록의 **30번 주제**](../30-offset-and-boundary-functions/)).
- **안 쓴다 — "있는지만" 볼 때.** `EXISTS` 로 쓰면 행이 안 늘어난다([19번](../19-semi-anti-join/)).
- **주의 — 짝짓기는 행이 제곱으로 는다.** 4행이면 16 짝이지만 1만 행이면 1억 짝이다. **`ON` 이 먼저 좁혀야 한다.**

## 핵심 문장

- **`SELF JOIN` 은 문법이 아니라 사용법이다.** 같은 표를 두 별칭으로 열면 그것이 `SELF JOIN` 이다.
- **별칭이 없으면 문이 서지 않는다** — `specified more than once`(PG) / `Not unique table/alias`(MySQL).
- **`ON` 이 자기 자신을 막아야 한다.** `<>` 는 자기만, `<` 는 뒤집힌 쌍까지 막는다.
- **계층은 `LEFT JOIN`** 이다. 꼭대기의 부모는 `NULL` 이고 내부 조인은 그 행을 버린다.
- **별칭 하나가 계층 한 단계**다. 깊이가 미지수면 재귀 CTE 로 간다.
- **짝짓기는 행이 제곱으로 는다.** `emp` 4행이 16 짝이 됐다.

## 관련 자료

- [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) — 조인 문법과 별칭.
- [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html) — 별칭 규칙이 같은 페이지에 있다.
- [13 INNER JOIN](../13-inner-join/) — **경계: 그쪽은 다른 두 표를 붙이는 규칙까지, 여기는 그 두 쪽이 같은 표일 때부터.**
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — 계층의 꼭대기를 살리는 것이 여기의 `LEFT` 다.
- [12 카티션곱과 CROSS JOIN](../12-cartesian-product-cross-join/) — 16 짝이 어디서 나오나.
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — **경계: 그쪽은 별칭이 이름 공간을 어떻게 바꾸나까지, 여기는 그 별칭을 둘 붙여 쓰는 것부터.**
- [11 서브쿼리 — 스칼라·상관·ANY/ALL](../11-subquery-scalar-correlated-any-all/) — 4번 절의 `ON` 안 상관 서브쿼리.
- [19 세미·안티 조인](../19-semi-anti-join/) — "있는지만" 보는 형태.
- [21 집계 함수와 COUNT 의 세 형태](../21-aggregate-functions-count-forms/) — **경계: 그쪽은 `COUNT` 세 형태의 의미까지, 여기는 `LEFT JOIN` 뒤에 그것이 왜 0 을 못 만드나부터.**
- **깊이가 미지수인 계층**은 [목록의 **33번 주제**](../33-recursive-cte/), **이웃 행 비교**는 [**30번 주제**](../30-offset-and-boundary-functions/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **`SELF JOIN`(자체 조인)** — 같은 표를 서로 다른 별칭으로 두 번 열어 조인하는 것. 전용 키워드는 없다.\
  예: `FROM emp a JOIN emp b ON a.dept_id = b.dept_id`.
- **별칭(alias)** — `FROM` 에서 표에 붙이는 다른 이름. 같은 표를 두 번 열 때는 **필수**다.\
  예: `FROM emp a JOIN emp b` 의 `a`·`b`.
- **자기 참조 열(self-referencing column)** — 같은 표의 다른 행을 가리키는 열.\
  예: `staff.mgr_id` 가 `staff.id` 를 가리킨다.
- **계층(hierarchy)** — 부모-자식 관계가 여러 단으로 이어진 구조.\
  예: `ann → bob → dan` 세 단.
- **꼭대기 행(root)** — 부모가 없는 행. 자기 참조 열이 `NULL` 이다.\
  예: `ann` 의 `mgr_id` 는 `NULL` — 내부 조인이 이 행을 버린다.
- **짝짓기(pairing)** — 같은 표의 두 행을 한 줄에 놓는 것.\
  예: 같은 부서 동료 목록. 행이 제곱으로 는다.
- **중복 쌍** — `(ann,bob)` 과 `(bob,ann)` 처럼 순서만 다른 같은 쌍.\
  예: `a.id <> b.id` 는 둘 다 주고, `a.id < b.id` 는 하나만 준다.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
  예: `ann.mgr_id = m.id` 에서 `NULL = 1` — 내부 조인이 `FALSE` 처럼 버린다.
- **재귀 CTE(recursive CTE)** — 깊이를 모르는 계층을 펴는 `WITH RECURSIVE` 문법.\
  예: 조직도가 몇 단인지 모를 때. [목록의 **33번 주제**](../33-recursive-cte/).
- **`LAG` / `LEAD`** — 정렬된 이웃 행의 값을 가져오는 윈도우 함수.\
  예: 급여 사다리를 한 번만 훑고 계산한다. [목록의 **30번 주제**](../30-offset-and-boundary-functions/).

## 더 들어가면

- **`SELF JOIN` 은 「같은 표를 두 번 스캔한다」는 뜻이 아니다.** 엔진이 한 번 읽어 양쪽에 쓸 수도 있다 — 계획을 보고 판단한다([목록의 **58번 주제**](../58-explain-plan-tree/)).
- **`staff` 에 외래키를 걸 수 있다** — `mgr_id` 가 같은 표의 `id` 를 참조하는 자기 참조 외래키([목록의 **44번 주제**](../44-foreign-key-referential-actions/)). 그러면 없는 상사를 가리키는 행이 막힌다.
- **짝짓기에서 `a.id < b.id` 대신 `a.name < b.name` 을 쓰면** 이름 비교가 collation 에 달라지고, 엔진 설정에 따라 결과가 갈릴 수 있다([39번](../39-collation/)).
