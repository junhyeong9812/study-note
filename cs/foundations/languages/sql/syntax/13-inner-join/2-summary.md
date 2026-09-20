# sql/13-INNER JOIN — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions (Joined Tables)](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 팬아웃 절의 `proj`·`emp_proj` 두 표는 **트랜잭션 안에서 만들고 롤백**했다 — DB 에 남기지 않았다. 만드는 문은 그 절에 적어 두었다.\
> **버전** — `INNER JOIN` 자체는 두 엔진 모두 오래전부터 있다. 아래 **`JOIN` 에 `ON` 을 빠뜨렸을 때**의 처리가 갈리는데, 두 매뉴얼에 도입 버전이 없어 **버전은 적지 않는다.**\
> **선행** — [12 카티션곱과 CROSS JOIN](../12-cartesian-product-cross-join/). **12행을 거르는 것이 이 주제다.**\
> **복선** — `ON` 과 `WHERE` 가 **여기서는 결과가 같다.** 그것이 왜 [15번](../15-on-vs-where-in-outer-join/)에서 달라지는지가 이 묶음의 정점이다.

## 한눈에 — 쉽게 말하면

**`INNER JOIN` = 소개팅 12쌍 중 「양쪽 다 맞는」 쌍만 남긴 것. 맞는 짝이 없는 사람은 명단에서 통째로 사라진다.**

- [12번](../12-cartesian-product-cross-join/)에서 모든 짝 12쌍을 만들었다.
- 거기에 "부서 번호가 같은 쌍만"이라는 조건(`ON`)을 걸면 **3쌍**이 남는다.
- 남지 못한 사람은 **행 자체가 없다.** `dan`(소속 없음)과 `hr`(사원 없음)이 결과에서 **조용히 사라진다.**
- 사라졌다는 사실은 **결과만 봐서는 알 수 없다.** 3행이 나왔을 뿐이다.

```text
              emp 4행                dept 3행
                 │                      │
                 └──── 모든 짝 12행 ─────┘        <- 12번
                            ↓
                  ON e.dept_id = d.id
                            ↓
                          3행                    <- 이 주제
                   ann | sales
                   bob | sales
                   cho | dev
                            ↑
             dan 과 hr 은 여기에 없다 — 버려졌다
```

이 명단 추리기가 **똑같은 구조로** `INNER JOIN` 이다.\
실무에서 「행 수가 줄었다」는 사고의 태반이 여기다 — **`INNER JOIN` 은 조용히 버린다.**

> **`INNER JOIN`(내부 조인)** — `ON` 조건을 만족하는 짝만 남기는 조인. 짝 없는 행은 버린다.\
> 예: `FROM emp e JOIN dept d ON e.dept_id = d.id` 는 3행. `dan` 과 `hr` 은 없다.

> **`ON` 절** — 두 표의 행을 **짝짓는 규칙**. 내부 조인에서는 짝을 못 지으면 곧 탈락이다.\
> 예: `ON e.dept_id = d.id`.

## 이 주제가 답하려는 질문

1. **`INNER JOIN` 은 어느 행을 버리나?** — 그리고 버렸다는 걸 결과만 봐서 알 수 있나?
2. **`ON` 과 `WHERE` 는 여기서 같은가?** — 같다. 그럼 [15번](../15-on-vs-where-in-outer-join/)에서는 왜 달라지나?
3. **조건을 걸었는데도 행이 늘 수 있나?** — 는다. 1:N 관계에서 곱해진다(팬아웃).

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

**이 주제에서 버려지는 것은 `dan` 과 `hr` 둘이다.**\
[01번](../01-logical-query-processing-order/)에서 `cho` 가 `WHERE` 에 걸려 탈락한 것과 성격이 같다 — **버려진 행은 결과에 흔적을 남기지 않는다.**\
그 둘을 되살리는 것이 [14번](../14-left-right-outer-join/)과 [16번](../16-full-outer-join/)이다.

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

### 1. 12행이 3행이 되는 자리

**언제 쓰나** — 관계가 있는 두 표를 붙일 때. SQL 에서 가장 많이 쓰는 조인이다.

```text
(전) 카티션곱 12행 — ON 판정                        (후) 3행
 emp.dept_id | dept.id | ON 판정 | 처분
-------------+---------+---------+------            +-----+-------+
   10 (ann)  |  10     | TRUE    | 남김             | ann | sales |
   10 (ann)  |  20, 30 | FALSE   | 버림             | bob | sales |
   10 (bob)  |  10     | TRUE    | 남김             | cho | dev   |
   10 (bob)  |  20, 30 | FALSE   | 버림             +-----+-------+
   20 (cho)  |  20     | TRUE    | 남김
   20 (cho)  |  10, 30 | FALSE   | 버림
 NULL (dan)  |  10,20,30| UNKNOWN| 버림   <- 세 행 전부
                                                     hr 은 애초에
                                                     TRUE 인 짝이 없었다
```

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
(3 rows)                         | cho | dev   |
                                 +-----+-------+
```

그림 해설 — **`ON` 도 `TRUE` 만 통과시킨다.** `FALSE` 와 `UNKNOWN` 을 똑같이 버리는 것이 `WHERE` 와 같다([04번](../04-null-three-valued-logic/)).\
그래서 `dan` 은 `NULL = 10` 이 `UNKNOWN` 이라 버려졌고, `hr` 은 `TRUE` 를 만들어 줄 왼쪽 행이 없어 버려졌다.\
대가 — **버렸다는 흔적이 결과에 없다.** 3행을 받아 든 사람은 원래 4명이었다는 걸 모른다.

`INNER` 키워드는 생략할 수 있다. `JOIN` 만 적으면 내부 조인이다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e INNER JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
(3 rows)                         | cho | dev   |
                                 +-----+-------+
```

---

### 2. 조건을 어디에 적어도 **여기서는** 같다

**언제 쓰나** — 조인 조건을 `ON` 과 `WHERE` 중 어디에 적을지 고민될 때. **내부 조인이라면 고민할 필요가 없다.**

같은 조건을 세 자리에 적어 봤다. **세 문장의 결과가 전부 같다.**

```text
(A) ON 에 적는다                     (B) ON TRUE + WHERE      (C) 쉼표 + WHERE
FROM emp e JOIN dept d               FROM emp e JOIN dept d   FROM emp e, dept d
  ON e.dept_id = d.id                  ON TRUE                WHERE e.dept_id = d.id
                                     WHERE e.dept_id = d.id
```

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d ON TRUE
         WHERE e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
(3 rows)                         | cho | dev   |
                                 +-----+-------+

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e, dept d WHERE e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
(3 rows)                         | cho | dev   |
                                 +-----+-------+
```

추가 조건도 마찬가지다. `ON` 에 붙이든 `WHERE` 에 붙이든 2행이 나온다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d
         ON e.dept_id = d.id AND d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d
         ON e.dept_id = d.id WHERE d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+
```

그림 해설 — **왜 같은가.** 내부 조인은 **짝을 못 지은 행을 어차피 버린다.**\
`ON` 에서 떨어뜨리나 `WHERE` 에서 떨어뜨리나 **떨어지는 건 같다.** `AND` 로 이어진 조건의 순서를 바꾼 것과 다를 바 없다.\
대가 — **이 습관이 외부 조인에서 사고가 된다.** 외부 조인은 짝을 못 지어도 행을 **남기므로**, `ON` 에서 떨어진 행과 `WHERE` 에서 떨어진 행의 운명이 갈린다.

```text
INNER JOIN                          OUTER JOIN
 ON 에서 탈락 -> 행이 사라진다        ON 에서 탈락 -> NULL 로 채워 남는다
 WHERE 에서 탈락 -> 행이 사라진다     WHERE 에서 탈락 -> 행이 사라진다
        ↓                                   ↓
     결과 같음                            결과 다름   <- 15번
```

★ **그래도 `ON` 에 적는다.** 조인 조건과 필터 조건이 눈으로 분리되고, 나중에 `LEFT JOIN` 으로 바꿀 때 **뜻이 안 변한다.**

---

### 3. `JOIN` 에 `ON` 을 빠뜨리면 — 두 엔진이 갈린다

**언제 쓰나** — 조인 조건을 깜빡했을 때. **한쪽은 막아 주고 한쪽은 안 막아 준다.**

```text
### SQL: SELECT e.name, d.name FROM emp e JOIN dept d;
--- PG 18.6 ---
ERROR:  syntax error at or near ";"
LINE 1: SELECT e.name, d.name FROM emp e JOIN dept d;
                                                    ^
--- MySQL 8.4.10 ---
+------+-------+
| name | name  |
+------+-------+
| dan  | dev   |
| cho  | dev   |
| bob  | dev   |
| ann  | dev   |
| dan  | hr    |
| cho  | hr    |
| bob  | hr    |
| ann  | hr    |
| dan  | sales |
| cho  | sales |
| bob  | sales |
| ann  | sales |
+------+-------+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `JOIN` 에 `ON` 이 없으면 | **✗ 구문 오류** — `JOIN` 은 조건을 요구한다 | **✓ 12행** — 카티션곱이 된다 |

그림 해설 — PG 는 `JOIN` 에 `ON` 이나 `USING` 을 **의무화**해서, 조건을 깜빡한 질의가 **문법 단계에서 터진다.**\
MySQL 은 `JOIN`·`INNER JOIN`·`CROSS JOIN` 을 동의어로 다루므로 조건이 없어도 통과시킨다 — **12행짜리 카티션곱이 조용히 나온다.**\
대가 — MySQL 에서는 이 사고가 **시끄럽지 않다.** 행 수가 이상하다는 것을 사람이 알아채야 한다.

반대 방향 사고(`CROSS JOIN` 에 `ON` 을 붙이는 것)는 [12번](../12-cartesian-product-cross-join/)에 있다. **두 사고가 서로 대칭이다.**

```text
        PG                                  MySQL
 JOIN 에 ON 없음      -> 구문 오류      -> 12행 (조용)
 CROSS JOIN 에 ON 있음 -> 구문 오류      -> 3행 (내부 조인)
        ↑                                    ↑
  형태와 조건이 1:1 로 묶여 있다        세 이름이 전부 같은 것이다
```

★ **양쪽에서 도는 습관** — 조건이 있으면 `JOIN … ON`, 없으면 `CROSS JOIN`. 섞지 않는다.

---

### 4. 조건을 걸었는데 행이 **느는** 자리 — 팬아웃

**언제 쓰나** — 1:N 관계를 조인한 뒤 집계를 씌울 때. **이 주제에서 가장 조용한 사고다.**

`emp` 와 `dept` 는 N:1 이라 행이 늘지 않는다. 늘어나는 것을 보려면 **다대다 관계**가 필요하다.

<details>
<summary>팬아웃 확인용 표 — 트랜잭션 안에서 만들고 롤백했다 (PostgreSQL)</summary>

```sql
BEGIN;
CREATE TABLE proj (id int PRIMARY KEY, name text NOT NULL);
CREATE TABLE emp_proj (emp_id int, proj_id int, PRIMARY KEY (emp_id, proj_id));
INSERT INTO proj     VALUES (100,'atlas'), (200,'beta');
INSERT INTO emp_proj VALUES (1,100), (1,200), (2,100);
-- 아래 질의들을 여기서 돌린다
ROLLBACK;
```

`ann`(id 1)은 프로젝트 **둘**에, `bob`(id 2)은 **하나**에 속한다. `cho`·`dan` 은 프로젝트가 없다.\
MySQL 은 DDL 에 트랜잭션이 안 걸리므로 `CREATE` → 질의 → `DROP TABLE` 로 확인했다. 두 DB 모두 실험 뒤 표가 남아 있지 않다.

</details>

```text
(전) emp 4행                        (후) emp JOIN emp_proj — 3행
+------+--------+                   +-----+---------+--------+
| ann  |    300 |                   | ann |     100 |    300 |
| bob  |    500 |                   | ann |     200 |    300 |  <- ann 이 두 줄
| cho  |   NULL |                   | bob |     100 |    500 |
| dan  |    400 |                   +-----+---------+--------+
+------+--------+                      cho·dan 은 사라졌다 (INNER)
```

```text
### SQL: SELECT e.name AS emp, ep.proj_id, e.salary
         FROM emp e JOIN emp_proj ep ON e.id = ep.emp_id ORDER BY e.id, ep.proj_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | proj_id | salary          +-----+---------+--------+
-----+---------+--------         | emp | proj_id | salary |
 ann |     100 |    300          +-----+---------+--------+
 ann |     200 |    300          | ann |     100 |    300 |
 bob |     100 |    500          | ann |     200 |    300 |
(3 rows)                         | bob |     100 |    500 |
                                 +-----+---------+--------+
```

**`ann` 의 급여 300 이 두 줄에 들어 있다.** 여기에 `SUM` 을 씌우면 두 번 세어진다.

```text
### SQL: SELECT SUM(e.salary) AS total FROM emp e JOIN emp_proj ep ON e.id = ep.emp_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 total                           +-------+
-------                          | total |
  1100                           +-------+
(1 row)                          |  1100 |
                                 +-------+
```

**1100 이다. 정답은 800 이다**(`ann` 300 + `bob` 500).

```text
 맞는 계산                          팬아웃된 계산
 ann 300                           ann 300  (프로젝트 atlas 행)
 bob 500                           ann 300  (프로젝트 beta 행)   <- 두 번째
-------                            bob 500
 800                              -------
                                   1100                <- 300 이 더 들어갔다
```

사원별로 쪼개 보면 어디서 늘었는지가 보인다.

```text
### SQL: SELECT e.name AS emp, COUNT(*) AS rows_per_emp, SUM(e.salary) AS salary_sum
         FROM emp e JOIN emp_proj ep ON e.id = ep.emp_id GROUP BY e.name ORDER BY e.name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | rows_per_emp | salary_sum  +-----+--------------+------------+
-----+--------------+------------ | emp | rows_per_emp | salary_sum |
 ann |            2 |        600  +-----+--------------+------------+
 bob |            1 |        500  | ann |            2 |        600 |
(2 rows)                          | bob |            1 |        500 |
                                  +-----+--------------+------------+
```

그림 해설 — **조인이 잘못된 게 아니다.** 3행은 「사원-프로젝트 배정」이라는 단위에서 정확하다.\
틀린 것은 **그 단위 위에 사원 단위 집계를 씌운 것**이다. `SUM(e.salary)` 는 「배정마다 급여」를 더했다.\
대가 — **에러가 안 난다.** 결과 타입도 맞고 값도 그럴듯하다. 이것이 silent failure 다.

**처방 둘 — 행을 늘리지 않거나, 늘리기 전에 접는다.**

```text
### SQL: SELECT SUM(e.salary) AS total FROM emp e
         WHERE EXISTS (SELECT 1 FROM emp_proj ep WHERE ep.emp_id = e.id);
--- PG 18.6 ---
 total 
-------
   800
(1 row)

### SQL: SELECT SUM(salary) AS total FROM emp WHERE id IN (SELECT emp_id FROM emp_proj);
--- MySQL 8.4.10 ---
+-------+
| total |
+-------+
|   800 |
+-------+
```

```text
### SQL: SELECT e.name AS emp, e.salary, p.n AS proj_cnt FROM emp e
         JOIN (SELECT emp_id, COUNT(*) AS n FROM emp_proj GROUP BY emp_id) p ON p.emp_id = e.id
         ORDER BY e.id;
--- PG 18.6 ---
 emp | salary | proj_cnt 
-----+--------+----------
 ann |    300 |        2
 bob |    500 |        1
(2 rows)
```

| 처방 | 무엇을 하나 | 언제 |
|---|---|---|
| `EXISTS` / `IN` | **행을 아예 안 늘린다** — 「있는지만」 본다 | 상대 표의 값이 필요 없을 때 |
| 선집계 후 조인 | 상대 표를 **먼저 1행으로 접고** 붙인다 | 개수·합계 같은 요약값이 필요할 때 |

팬아웃 자체와 그 처방 전체는 목록의 **25번 주제**가 정본이다. `EXISTS`/`IN` 은 목록의 **19번 주제**다.\
**경계: 여기서는 「조인이 행을 늘린다」는 사실까지, 처방의 선택 기준은 25번.**

---

### 5. `ON` 에 등호가 아닌 것도 쓸 수 있다

**언제 쓰나** — 범위 매칭(구간표·이력 테이블)처럼 등호로 안 붙는 관계.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d ON e.dept_id > d.id ORDER BY e.id, d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 cho | sales                     +-----+-------+
(1 row)                          | cho | sales |
                                 +-----+-------+
```

그림 해설 — `cho` 의 `dept_id` 가 20 이고 `sales.id` 가 10 이라 `20 > 10` 이 `TRUE` 다. 나머지 짝은 전부 `FALSE` 거나 `UNKNOWN` 이다.\
**`ON` 은 조건식이지 등호 전용 문법이 아니다.**\
대가 — 등호가 아니면 해시 조인을 못 쓴다. 큰 표에서는 중첩 루프가 되어 느려진다(목록의 **59번 주제**).\
그리고 [16번](../16-full-outer-join/)에서 봤듯 **`FULL OUTER JOIN` 은 PG 에서 아예 거부한다** — 부등호는 머지·해시 조인에 안 맞기 때문이다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
FROM 왼쪽표 [INNER] JOIN 오른쪽표 ON <조건>      -- INNER 는 생략 가능
FROM 왼쪽표 [INNER] JOIN 오른쪽표 USING (공통열)  -- 목록의 18번 주제
FROM 왼쪽표, 오른쪽표 WHERE <조건>               -- 옛 표기. 결과는 같다
```

규칙 여섯.

1. **`INNER` 는 생략 가능하다.** `JOIN` 만 적으면 내부 조인이다.
2. **`ON` 은 `TRUE` 만 통과시킨다.** `FALSE` 와 `UNKNOWN` 을 똑같이 버린다 — `WHERE` 와 같은 규칙이다.
3. **짝 없는 행은 사라진다.** 양쪽 다. 그리고 **결과에 흔적이 없다.**
4. **`ON` 과 `WHERE` 는 내부 조인에서 결과가 같다.** 그래도 `ON` 에 적는다 — [15번](../15-on-vs-where-in-outer-join/)에서 달라지기 때문이다.
5. **`JOIN` 에 `ON` 이 없으면 PG 는 구문 오류, MySQL 은 카티션곱**이다. 조건이 없으면 `CROSS JOIN` 이라고 적는다.
6. **1:N 을 조인하면 행이 는다.** 그 위에 집계를 씌우기 전에 행 수를 센다.

읽을 때 붙잡을 수는 언제나 **행 수**다.

```text
 붙이기 전    emp 4행 · dept 3행
 붙인 뒤      3행                      <- 줄었다: 짝 없는 행이 버려졌다
 붙인 뒤      3행 (emp_proj 와)        <- 사원 2명이 3행: 늘었다 (팬아웃)

 "줄었나 늘었나"를 먼저 세고 나서 집계를 씌운다
```

## 어디서 틀리나

- **`INNER JOIN` 이 조용히 버리는 것을 잊는다.**\
  「사원 목록에 부서명을 붙였을 뿐」인데 `dan` 이 사라진다. 기준 표를 다 남기려면 [14번](../14-left-right-outer-join/)의 `LEFT JOIN` 이다.
- **`NULL` 인 외래키가 조인에서 살아남을 거라 생각한다.**\
  `ON NULL = 10` 은 `UNKNOWN` 이다. `dan` 의 세 짝이 전부 떨어졌다([04번](../04-null-three-valued-logic/)).
- **1:N 조인 위에 `SUM` 을 씌운다.**\
  위에서 800 이어야 할 합이 1100 이 됐다. **에러가 안 난다.** 조인 뒤 행 수를 먼저 센다.
- **`COUNT(*)` 로 「사원 수」를 센다.**\
  조인 뒤의 `COUNT(*)` 은 사원 수가 아니라 **행 수**다. `COUNT(DISTINCT e.id)` 가 사원 수다(목록의 **21번 주제**).
- **`JOIN` 에 `ON` 을 빠뜨린다(MySQL).**\
  12행이 조용히 나온다. PG 에서는 구문 오류로 막힌다.
- **조인 질의에서 열에 별칭을 안 붙인다.**\
  `emp` 와 `dept` 는 `id`·`name` 을 둘 다 갖고 있어 `ambiguous` 가 난다([10번](../10-from-clause-aliases-derived-tables/)).
- **`NATURAL JOIN` 으로 짧게 쓰려 한다.**\
  이름이 같은 열 **전부**로 붙는다. `emp` 와 `dept` 는 `id` 와 `name` 이 겹쳐 **0행**이 나온다.

```text
### SQL: SELECT COUNT(*) AS n FROM emp NATURAL JOIN dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 0                               +---+
(1 row)                          | 0 |
                                 +---+
```

  **에러가 아니라 0행이다.** `emp.id = dept.id AND emp.name = dept.name` 으로 붙었고 그런 짝이 없었다.\
  `USING (id)` 도 같은 함정이다 — `emp.id` 와 `dept.id` 는 의미가 다른 열인데 이름만 같다.

```text
### SQL: SELECT * FROM emp JOIN dept USING (id);
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary | name    (빈 결과 — 출력이 한 줄도 없다)
----+------+---------+--------+------
(0 rows)
```

  `USING`·`NATURAL` 은 목록의 **18번 주제**가 정본이다. **여기서 인출할 것은 "조용히 0행이 나온다" 하나다.**

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `ON` 을 통과한 짝만 남는다 | **결과의 정의** | 언어 |
| `ON` 과 `WHERE` 가 **내부 조인에서** 같다 | **결과의 정의** | 언어 — 짝 없는 행을 어차피 버리기 때문 |
| 엔진이 해시 조인을 고른다 / 중첩 루프를 고른다 | 옵티마이저의 선택 | 아무도 — 통계·인덱스·행 수에 달렸다 |
| `JOIN` 에 `ON` 이 없을 때의 처리 | **문법의 차이** | 두 엔진이 다르다 — PG 구문 오류, MySQL 카티션곱 |

- **결과의 순서는 보장되지 않는다.** 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.\
  [16번](../16-full-outer-join/)에서 `RIGHT JOIN` 의 줄 순서가 두 엔진에서 달랐던 것도 같은 이유였다.
- **조인 알고리즘은 결과를 바꾸지 않는다.** 해시든 머지든 중첩 루프든 답은 같다(목록의 **59번 주제**).
- **예외가 하나 있다** — PG 의 `FULL OUTER JOIN` 은 **알고리즘 제약이 문법 제약처럼 드러난다.** 부등호 `ON` 을 거부한다([16번](../16-full-outer-join/)).\
  내부 조인에는 그런 제약이 없다(위 5번에서 부등호가 통했다).

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 양쪽에 다 있는 것만 필요할 때.** 「부서가 있는 사원의 목록」.
- **쓴다 — 외래키로 붙이는 대부분의 조회.** 외래키가 `NOT NULL` 이면 `LEFT JOIN` 과 결과가 같고, `INNER` 쪽이 옵티마이저에 정보를 더 준다.
- **안 쓴다 — 기준 표를 다 남겨야 할 때.** 「모든 사원」·「모든 부서」가 화면 요구사항이면 [14번](../14-left-right-outer-join/)이다.
- **안 쓴다 — 상대 표의 값이 필요 없을 때.** 「프로젝트가 있는 사원」만 알면 되면 `EXISTS` 가 낫다. **행이 안 늘어난다**(목록의 **19번 주제**).
- **안 쓴다 — 외래키가 `NULL` 을 허용하는데 그 행도 필요할 때.** `dan` 이 바로 그 경우다.
- **주의 — 조인 뒤 집계.** `INNER JOIN` 을 쓰든 말든, 1:N 이면 행이 는다. 집계 전에 행 수를 센다(목록의 **25번 주제**).

## 핵심 문장

- `INNER JOIN` 은 **12행 중 `ON` 을 통과한 3행**만 남긴다. 짝 없는 행은 **양쪽 다 조용히 사라진다.**
- `ON` 도 **`TRUE` 만 통과**시킨다. `dan` 은 `NULL = 10` 이 `UNKNOWN` 이라 떨어졌다.
- **`ON` 과 `WHERE` 는 내부 조인에서 결과가 같다.** 짝 없는 행을 어차피 버리기 때문이다 — 그래서 [15번](../15-on-vs-where-in-outer-join/)에서 달라진다.
- **`JOIN` 에 `ON` 이 없으면 PG 는 구문 오류, MySQL 은 12행**이다. 조건이 없으면 `CROSS JOIN` 이라고 적는다.
- **조건이 있어도 행은 늘 수 있다** — 1:N 팬아웃. 합계가 800 대신 1100 이 나온다. **에러가 안 난다.**
- `NATURAL JOIN` 은 이름이 같은 열 **전부**로 붙어 **조용히 0행**을 준다.

## 관련 자료

- [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) — 조인 형태별 정의.
- [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html) — `JOIN`·`INNER JOIN`·`CROSS JOIN` 을 문법적 동의어로 다룬다.
- [12 카티션곱과 CROSS JOIN](../12-cartesian-product-cross-join/) — **경계: 그쪽은 12행이 어떻게 생기나까지, 여기는 그 12행을 거르는 것부터.**
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — 여기서 버린 `dan`·`hr` 을 되살린다.
- [15 OUTER JOIN 에서 ON 과 WHERE 의 차이](../15-on-vs-where-in-outer-join/) — **여기서 같았던 두 자리가 거기서 갈린다.**
- [16 FULL OUTER JOIN](../16-full-outer-join/) — 양쪽 다 되살린다.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `UNKNOWN` 의 계산까지, 여기는 그것이 `ON` 에서 행을 어떻게 지우나부터.**
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — 모호한 열 이름과 선집계 처방.
- **`USING`·`NATURAL`** 은 목록의 **18번 주제**, **`EXISTS`/`IN`** 은 **19번 주제**, **팬아웃 처방**은 **25번 주제**가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **`INNER JOIN`(내부 조인)** — `ON` 을 만족하는 짝만 남기는 조인. 짝 없는 행은 버린다.\
  예: `emp JOIN dept ON e.dept_id = d.id` 는 3행. `dan` 과 `hr` 은 없다.
- **`ON` 절** — 두 표의 행을 짝짓는 규칙. 내부 조인에서는 탈락이 곧 소멸이다.\
  예: `ON e.dept_id = d.id`.
- **`USING` 절** — 양쪽에 이름이 같은 열로 붙이는 축약형. 공통 열이 하나로 합쳐진다.\
  예: `JOIN dept USING (id)` — 여기서는 의미가 안 맞아 0행이 나온다. 목록의 18번 주제.
- **`NATURAL JOIN`** — 이름이 같은 열 **전부**를 조인 조건으로 삼는 조인.\
  예: `emp NATURAL JOIN dept` 는 `id` 와 `name` **둘 다**로 붙어 0행이다.
- **팬아웃(fan-out)** — 1:N 조인으로 왼쪽 행이 여러 줄로 불어나는 현상.\
  예: `ann` 이 프로젝트 둘에 속하면 `ann` 의 급여가 두 줄에 들어간다.
- **silent failure(무음 실패)** — 에러 없이 틀린 값이 나오는 실패.\
  예: 팬아웃된 `SUM` 이 800 대신 1100 을 준다. 타입도 맞고 값도 그럴듯하다.
- **반조인(semi join)** — 「저쪽에 짝이 있는지만」 보는 조인. 행이 안 늘어난다.\
  예: `WHERE EXISTS (SELECT 1 FROM emp_proj ep WHERE ep.emp_id = e.id)`. 목록의 19번 주제.
- **선집계(pre-aggregation)** — 조인 전에 상대 표를 1행으로 접는 것.\
  예: `JOIN (SELECT emp_id, COUNT(*) AS n FROM emp_proj GROUP BY emp_id) p ON …`.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값.\
  예: `NULL = 10`. `ON` 은 이것을 `FALSE` 와 똑같이 버린다.
- **중첩 루프 / 해시 조인** — 왼쪽 행마다 오른쪽을 훑거나, 해시 표를 만들어 맞추는 조인 알고리즘.\
  예: 등호 조건이면 해시를 쓸 수 있고, 부등호면 못 쓴다. 목록의 59번 주제.
