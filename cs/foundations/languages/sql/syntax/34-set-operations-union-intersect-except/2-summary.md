# sql/34-집합 연산 — `UNION`·`INTERSECT`·`EXCEPT` 와 `ALL` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Combining Queries (UNION, INTERSECT, EXCEPT)](https://www.postgresql.org/docs/18/queries-union.html) · [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · Set Operations with UNION, INTERSECT, and EXCEPT](https://dev.mysql.com/doc/refman/8.4/en/set-operations.html) · [MySQL 8.0.31 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-31.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·실행 계획은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 두 개만 썼다. **새로 만든 표가 없다.**\
> **버전** — `UNION` 은 두 엔진 모두 오래전부터 있다. **`INTERSECT`/`EXCEPT` 는 MySQL 8.0.31 부터**다 — 매뉴얼에 도입 버전이 없어 **릴리스 노트로 접지**했다(아래 인용). PG 는 오래전부터 있다.\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) · [07 DISTINCT 와 중복 제거](../07-distinct-and-duplicate-removal/).

## 한눈에 — 쉽게 말하면

**집합 연산은 「두 결과를 세로로 쌓는 것」이고, `ALL` 이 없으면 쌓은 뒤 중복을 지운다.**

조인과 헷갈리기 쉬운데, 방향이 아예 다르다.

```text
 조인 = 옆으로 붙인다 (열이 늘어난다)      집합 연산 = 아래로 쌓는다 (행이 늘어난다)
 +------+   +------+                       +------+
 | emp  | + | dept | = | emp | dept |      | emp  |
 +------+   +------+                       +------+
                                                ↓ 그 아래에
                                           +------+
                                           | dept |
                                           +------+
                                           열 개수·타입이 맞아야 한다
```

- **비유** — 두 반의 출석부를 합치는 일이다.\
  **`UNION ALL`** = 두 출석부를 **그냥 겹쳐 놓는다**. 두 반에 다 있는 학생은 두 번 적힌다.\
  **`UNION`** = 겹쳐 놓고 **같은 줄을 지운다**. 한 번씩만 남는다.\
  **`INTERSECT`** = 두 출석부에 **다 있는 학생만**.\
  **`EXCEPT`** = 1반에는 있는데 **2반에는 없는 학생만**.
- **똑같은 구조다** — 그런데 "같은 줄"의 기준이 **줄 전체**다.\
  이름만 같고 번호가 다르면 다른 줄이고, **이름과 번호가 둘 다 같으면 다른 사람이어도 한 줄로 접힌다.**\
  그것이 아래 3번 절의 함정이고, [16번](../16-full-outer-join/)이 `FULL OUTER JOIN` 우회에서 당한 바로 그것이다.

| 비유 | 실체 |
|---|---|
| 두 출석부를 겹쳐 놓는다 | `UNION ALL` — 중복 제거 없음 |
| 겹쳐 놓고 같은 줄을 지운다 | `UNION` — 중복 제거 있음 |
| 두 출석부에 다 있는 학생 | `INTERSECT` |
| 1반에만 있는 학생 | `EXCEPT` (PG·MySQL 8.0.31+) |
| 줄 전체가 같아야 같은 줄 | 중복 판정 기준 = **출력 행 전체**([07번](../07-distinct-and-duplicate-removal/)) |
| 칸 수가 다르면 못 겹친다 | 열 개수 불일치 → 에러 |
| 정렬은 다 합친 뒤에 한 번 | `ORDER BY` 는 **맨 끝에 한 번만** |

> **집합 연산(set operation)** — 두 질의의 결과를 **행 단위로 합치거나 빼는** 연산. `UNION`·`INTERSECT`·`EXCEPT` 셋이다.\
> 예: `SELECT dept_id FROM emp UNION SELECT id FROM dept` — 두 목록을 합쳐 중복을 지운다.

## 이 주제가 답하려는 질문

1. **`ALL` 이 있고 없고가 무엇을 바꾸나?** — 행 수만인가, 비용도인가.
2. **왜 「열 개수·타입이 맞아야」 하나?** — 안 맞으면 두 엔진이 **같은 반응**을 하나.
3. **`UNION` 이 조용히 행을 접는 사고는 어떻게 생기나?** — [16번](../16-full-outer-join/)이 당한 것을 일반화할 수 있나.

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
        +------------- ann 과 bob 은 dept_id 가 둘 다 10 이다
```

**왜 이 데이터가 이 주제에 맞나.**

- ★ **`ann` 과 `bob` 의 `dept_id` 가 둘 다 `10`** 이다. 그래서 `SELECT dept_id FROM emp` 는 **중복을 품은 목록**이고,\
  `UNION` 을 붙이는 순간 **묻지도 않았는데 그 둘이 한 줄로 접힌다**(3번 절). **중복이 없는 표로는 이 함정이 안 보인다.**
- **`dan.dept_id` 가 `NULL`** 이다. 집합 연산의 중복 판정은 **`NULL` 을 같은 값으로 본다** — `=` 규칙([04번](../04-null-three-valued-logic/))과 정반대라, 이 한 행이 그 사실을 드러낸다.
- **`dept.id`(10·20·30)와 `emp.dept_id`(10·10·20·NULL)가 절반만 겹친다.** `INTERSECT` 는 2행, `EXCEPT` 는 양방향이 서로 달라져 **세 연산이 한 데이터에서 전부 구분된다.**
- **열 타입이 `integer`(`id`·`dept_id`)와 문자열(`name`)로 갈린다.** 타입 불일치 실험을 **표를 새로 만들지 않고** 그대로 할 수 있다(5번 절) — 그 자리에서 **두 엔진이 가장 크게 갈린다.**

## 동작 방식

### 1. 셋의 의미 — 같은 데이터에 셋을 다 던져 본다

**언제 쓰나** — 두 목록을 비교할 때. "합집합·교집합·차집합" 중 무엇을 원하는지 먼저 정한다.

```text
 emp.dept_id = {10, 10, 20, NULL}        dept.id = {10, 20, 30}

  UNION            INTERSECT          EXCEPT (emp - dept)     EXCEPT (dept - emp)
  {10,20,30,NULL}  {10,20}            {NULL}                  {30}
  4행              2행                1행                     1행
```

```text
### SQL: SELECT dept_id FROM emp UNION SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
                                 +---------+
      10                         |      10 |
      30                         |      20 |
      20                         |    NULL |
(4 rows)                         |      30 |
                                 +---------+

### SQL: SELECT dept_id FROM emp INTERSECT SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      20                         |      10 |
(2 rows)                         |      20 |
                                 +---------+

### SQL: SELECT dept_id FROM emp EXCEPT SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
                                 +---------+
(1 row)                          |    NULL |
                                 +---------+

### SQL: SELECT id FROM dept EXCEPT SELECT dept_id FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +------+
----                             | id   |
 30                              +------+
(1 row)                          |   30 |
                                 +------+
```

그림 해설 — **`EXCEPT` 는 방향이 있다.** `A EXCEPT B` 와 `B EXCEPT A` 가 서로 다른 답을 냈다(`NULL` 대 `30`).\
PG 의 빈 칸은 `NULL` 이다 — psql 이 그렇게 찍을 뿐이고, MySQL 은 `NULL` 이라고 쓴다.\
비용 — `ALL` 없는 셋은 **전부 중복 제거를 한다.** 그 비용이 6번 절에 계획으로 나온다.

★ **세 연산이 두 엔진에서 한 자리도 안 갈렸다.** 갈리는 것은 **버전**(4번 절)과 **타입 불일치**(5번 절)다.

---

### 2. `ALL` — 중복을 지우지 않는다

**언제 쓰나** — 중복이 **의미가 있을 때**. 로그·거래 내역·측정값처럼 같은 값이 여러 번 나오는 것이 사실일 때.

```text
 UNION            emp: 10,10,20,NULL   dept: 10,20,30
   → 합친다       10,10,20,NULL,10,20,30  (7행)
   → 중복 지운다  10,20,30,NULL           (4행)  <- 3행이 사라졌다

 UNION ALL
   → 합친다       10,10,20,NULL,10,20,30  (7행)
   → 끝           (7행)
```

```text
### SQL: SELECT dept_id FROM emp UNION ALL SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      10                         |      10 |
      20                         |      10 |
                                 |      20 |
      10                         |    NULL |
      20                         |      20 |
      30                         |      30 |
(7 rows)                         |      10 |
                                 +---------+
```

`INTERSECT ALL`·`EXCEPT ALL` 도 있다. **개수를 세는 방식**이 달라진다.

```text
### SQL: SELECT dept_id FROM emp INTERSECT ALL SELECT dept_id FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
                                 +---------+
      10                         |      10 |
      10                         |      10 |
      20                         |      20 |
(4 rows)                         |    NULL |
                                 +---------+

### SQL: SELECT dept_id FROM emp EXCEPT ALL SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
                                 +---------+
      10                         |      10 |
(2 rows)                         |    NULL |
                                 +---------+
```

그림 해설 — `EXCEPT ALL` 에서 `10` 이 **하나만** 남았다. 왼쪽에 `10` 이 둘, 오른쪽에 하나라 **2 − 1 = 1** 이다.\
`ALL` 이 붙으면 집합이 아니라 **다중집합**(multiset)의 연산이 된다 — "있나 없나"가 아니라 "**몇 개인가**"를 뺀다.\
비용 — **`ALL` 이 싸다.** 중복 제거는 정렬이나 해시를 부르고, 그것이 6번 절의 계획 차이다.

> **다중집합(multiset, 가방)** — 같은 원소가 여러 번 들어갈 수 있는 집합.\
> 예: `{10, 10, 20}` 은 집합으로는 `{10, 20}` 이지만 다중집합으로는 원소가 셋이다.

---

### 3. ★ **`UNION` 이 조용히 행을 접는다** — 16번이 당한 함정

**언제 쓰나** — `UNION` 을 "두 결과를 합치는 것"으로만 알고 쓸 때. **여기가 이 주제에서 가장 조용한 사고다.**

[16번 FULL OUTER JOIN](../16-full-outer-join/)이 MySQL 우회를 만들다가 정확히 이것에 당했다. **같은 질의를 다시 던져 본다.**

```text
(A) 흔한 우회 — LEFT UNION RIGHT              (B) 올바른 우회 — UNION ALL + 반조인
SELECT e.dept_id AS e_dept, d.id AS d_id       SELECT e.dept_id AS e_dept, d.id AS d_id
FROM emp e LEFT JOIN dept d ON e.dept_id=d.id  FROM emp e LEFT JOIN dept d ON e.dept_id=d.id
UNION                                          UNION ALL
SELECT e.dept_id, d.id                         SELECT e.dept_id, d.id
FROM emp e RIGHT JOIN dept d ON e.dept_id=d.id FROM emp e RIGHT JOIN dept d ON e.dept_id=d.id
                                               WHERE e.id IS NULL;
--- PG 18.6 ---                                --- PG 18.6 ---
 e_dept | d_id                                  e_dept | d_id
--------+------                                --------+------
        |                                           10 |   10
        |   30                                      10 |   10   <- 두 행이 살아 있다
     20 |   20                                      20 |   20
     10 |   10   <- 두 행이 한 행으로 접혔다            |
(4 rows)                                              |   30
                                               (5 rows)
--- MySQL 8.4.10 ---                           --- MySQL 8.4.10 ---
+--------+------+                              +--------+------+
| e_dept | d_id |                              | e_dept | d_id |
+--------+------+                              +--------+------+
|     10 |   10 |                              |     10 |   10 |
|     20 |   20 |                              |     10 |   10 |
|   NULL | NULL |                              |     20 |   20 |
|   NULL |   30 |                              |   NULL | NULL |
+--------+------+                              |   NULL |   30 |
  4행 — PG 와 같다                              +--------+------+
                                                 5행 — PG 와 같다
```

그림 해설 — **`ann` 과 `bob` 이 둘 다 `(10, 10)` 이라 한 행으로 접혔다.** 4행과 5행, **사원 하나가 사라졌다.**\
에러도 경고도 없다. 그리고 **`name` 열을 뽑을 때는 `ann ≠ bob` 이라 안 접힌다** — **뽑는 열에 따라 행 수가 달라진다.**

**일반화하면 규칙은 이렇다.**

```text
 UNION 은 "두 가지" 중복을 동시에 지운다

  (1) 가지 사이의 중복   <- 대개 이것을 의도한다
  (2) 한 가지 안의 중복  <- 이것은 묻지도 않았다  ★ 사고는 여기서 난다
```

한 가지 안의 중복도 지운다는 것을 **한 줄로 확인할 수 있다.**

```text
### SQL: SELECT dept_id FROM emp WHERE dept_id = 10 UNION SELECT dept_id FROM emp WHERE dept_id = 10;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
(1 row)                          |      10 |
                                 +---------+

### SQL: SELECT dept_id FROM emp WHERE dept_id = 10 UNION ALL SELECT dept_id FROM emp WHERE dept_id = 10;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      10                         |      10 |
      10                         |      10 |
      10                         |      10 |
(4 rows)                         |      10 |
                                 +---------+
```

★ **각 가지가 2행씩이라 `UNION ALL` 은 4행인데, `UNION` 은 1행이다.** 가지 사이만 지운 것이 아니라 **가지 안의 중복까지** 지웠다.\
비용 — 그래서 **판정 규칙은 하나다.**

> **행 수를 보존해야 하는 자리에는 `UNION` 을 쓰지 마라.** `UNION ALL` 로 합치고, 겹치는 부분은 **조건으로 직접 잘라내라.**

그 "직접 잘라내기"가 (B) 의 `WHERE e.id IS NULL`(반조인, [19번](../19-semi-anti-join/))이다.\
같은 함정이 **감사 로그 합치기·여러 소스 집계·페이지네이션 목록 합치기**에서 그대로 재현된다 — **값이 같은 두 행이 실제로는 다른 사건일 때** 언제나.

---

### 4. 열 개수·타입 — **개수는 둘 다 막고, 타입은 갈린다**

**언제 쓰나** — 가지를 나중에 하나 더 붙일 때. 열을 하나 빠뜨리기 쉽다.

```text
### SQL: SELECT id, name FROM emp UNION SELECT id FROM dept;
--- PG 18.6 ---
ERROR:  each UNION query must have the same number of columns
LINE 1: SELECT id, name FROM emp UNION SELECT id FROM dept;
                                              ^
--- MySQL 8.4.10 ---
ERROR 1222 (21000) at line 1: The used SELECT statements have a different number of columns
```

그림 해설 — **개수는 두 엔진이 똑같이 막는다.** 문장만 봐도 알 수 있으니 파싱 단계에서 잡힌다.\
비용 — 이 에러는 **친절한 편**이다. 다음 절의 타입 쪽이 훨씬 위험하다.

---

### 5. ★ **타입이 안 맞으면 — PG 는 죽이고 MySQL 은 문자열로 만든다**

**언제 쓰나** — 서로 다른 표의 "비슷해 보이는" 열을 합칠 때. **두 엔진이 가장 크게 갈리는 자리다.**

```text
### SQL: SELECT id FROM emp UNION SELECT name FROM dept;
--- PG 18.6 ---
ERROR:  UNION types integer and text cannot be matched
LINE 1: SELECT id FROM emp UNION SELECT name FROM dept;
                                        ^
--- MySQL 8.4.10 ---
+-------+
| id    |
+-------+
| 1     |
| 2     |
| 3     |
| 4     |
| dev   |
| hr    |
| sales |
+-------+
```

그림 해설 — **MySQL 은 통과시켰다.** 결과 열이 문자열이 됐고, 정렬도 문자열 순(`1,2,3,4,dev,hr,sales`)이다.\
**정수 열과 이름 열이 한 칸에 섞인 결과**가 에러 없이 나왔다 — 프로그램은 이것을 그냥 받는다.

**숫자끼리는 양쪽 다 맞춰 준다.**

```text
### SQL: SELECT id FROM dept UNION SELECT '40';
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +----+
----                             | id |
 10                              +----+
 30                              | 20 |
 40                              | 30 |
 20                              | 10 |
(4 rows)                         | 40 |
                                 +----+

### SQL: SELECT 1 AS v UNION ALL SELECT 1.5;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  v                              +-----+
-----                            | v   |
   1                             +-----+
 1.5                             | 1.0 |
(2 rows)                         | 1.5 |
                                 +-----+
```

비용 — ★ **이것은 [35번](../35-type-system-and-casting/)이 찾은 성격 차이가 집합 연산에서 다시 나타난 것이다.**\
그쪽의 한 줄이 이렇다 — **"PG 는 못 읽으면 문을 죽이고, MySQL 은 읽을 수 있는 데까지 읽고 경고만 남긴다."**\
여기서는 경고조차 없었다. **MySQL 에서 `UNION` 을 쓸 때는 타입을 직접 맞춰라**(`CAST`).

---

### 6. 비용 — 중복 제거가 계획에 보인다

**언제 쓰나** — 큰 목록을 합칠 때. `ALL` 을 붙일 수 있으면 붙인다.

```text
### SQL: EXPLAIN (COSTS OFF) SELECT dept_id FROM emp UNION SELECT id FROM dept;
--- PG 18.6 ---
          QUERY PLAN          
------------------------------
 HashAggregate               <- 중복 제거
   Group Key: emp.dept_id
   ->  Append
         ->  Seq Scan on emp
         ->  Seq Scan on dept
(5 rows)
--- MySQL 8.4.10 ---
+----------------------------------------------------------------------------------+
| EXPLAIN                                                                          |
+----------------------------------------------------------------------------------+
| -> Table scan on <union temporary>  (cost=2.27..4.49 rows=7)
    -> Union materialize with deduplication  (cost=1.9..1.9 rows=7)
        -> Table scan on emp  (cost=0.55 rows=3)
        -> Covering index scan on dept using name  (cost=0.65 rows=4)
 |
+----------------------------------------------------------------------------------+

### SQL: EXPLAIN (COSTS OFF) SELECT dept_id FROM emp UNION ALL SELECT id FROM dept;
--- PG 18.6 ---
       QUERY PLAN       
------------------------
 Append                     <- 그냥 이어 붙인다
   ->  Seq Scan on emp
   ->  Seq Scan on dept
(3 rows)
--- MySQL 8.4.10 ---
+----------------------------------------------------------------------------------+
| EXPLAIN                                                                          |
+----------------------------------------------------------------------------------+
| -> Append  (cost=1.2 rows=7)
    -> Stream results  (cost=0.55 rows=3)
        -> Table scan on emp  (cost=0.55 rows=3)
    -> Stream results  (cost=0.65 rows=4)
        -> Covering index scan on dept using name  (cost=0.65 rows=4)
 |
+----------------------------------------------------------------------------------+
```

그림 해설 — **낱말이 그대로 답이다.** PG 는 `HashAggregate` 가 붙고 빠지며, MySQL 은 `Union materialize with deduplication` 대 `Append` 다.\
`ALL` 쪽 MySQL 계획의 **`Stream results`** 는 **모아 두지 않고 흘려보낸다**는 뜻이다 — 첫 행이 일찍 나온다.\
비용 — ★ **계획은 관찰이지 보장이 아니다.** 여기서 볼 것은 수치가 아니라 "**중복 제거 노드가 있나 없나**"다.

---

### 7. `ORDER BY` 는 **전체에 한 번만**

**언제 쓰나** — 합친 결과를 정렬할 때. **가지 안에 넣으면 문법 오류다.**

```text
 X 가지 안에 ORDER BY                     O 맨 끝에 한 번
 SELECT name FROM emp ORDER BY name       SELECT name FROM emp
 UNION                                    UNION
 SELECT name FROM dept;                   SELECT name FROM dept
                                          ORDER BY name;
```

```text
### SQL: SELECT name FROM emp ORDER BY name UNION SELECT name FROM dept;
--- PG 18.6 ---
ERROR:  syntax error at or near "UNION"
LINE 1: SELECT name FROM emp ORDER BY name UNION SELECT name FROM de...
                                           ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'UNION SELECT name FROM dept' at line 1

### SQL: SELECT name FROM emp UNION SELECT name FROM dept ORDER BY name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +-------+
-------                          | name  |
 ann                             +-------+
 bob                             | ann   |
 cho                             | bob   |
 dan                             | cho   |
 dev                             | dan   |
 hr                              | dev   |
 sales                           | hr    |
(7 rows)                         | sales |
                                 +-------+
```

**정렬 키로 쓸 수 있는 이름은 첫 가지의 것뿐이다.**

```text
### SQL: SELECT name AS a FROM emp UNION SELECT name AS b FROM dept ORDER BY b;
--- PG 18.6 ---
ERROR:  column "b" does not exist
LINE 1: ...e AS a FROM emp UNION SELECT name AS b FROM dept ORDER BY b;
                                                                     ^
DETAIL:  There is a column named "b" in table "*SELECT* 2", but it cannot be referenced from this part of the query.
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'b' in 'order clause'

### SQL: SELECT id AS first_name FROM dept UNION ALL SELECT id AS second_name FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 first_name                      +------------+
------------                     | first_name |
         10                      +------------+
         20                      |         20 |
         30                      |         30 |
          1                      |         10 |
          2                      |          1 |
          3                      |          2 |
          4                      |          3 |
(7 rows)                         |          4 |
                                 +------------+
```

그림 해설 — **결과 열 이름은 첫 가지가 정한다.** 둘째 가지의 `second_name` 은 어디에도 안 나온다.\
★ **MySQL 쪽 순서를 보라 — `20, 30, 10, 1, 2, 3, 4` 다.** `ORDER BY` 가 없으면 **순서는 보장되지 않는다**([08번](../08-order-by-null-position-stability/)).\
비용 — `ORDER BY` 대신 **서수**(`ORDER BY 2`)를 쓰면 이름 문제를 피할 수 있다.

```text
### SQL: SELECT name, id FROM dept UNION ALL SELECT name, id FROM emp ORDER BY 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name  | id                      +-------+----+
-------+----                     | name  | id |
 ann   |  1                      +-------+----+
 bob   |  2                      | ann   |  1 |
 cho   |  3                      | bob   |  2 |
 dan   |  4                      | cho   |  3 |
 sales | 10                      | dan   |  4 |
 dev   | 20                      | sales | 10 |
 hr    | 30                      | dev   | 20 |
(7 rows)                         | hr    | 30 |
                                 +-------+----+
```

`LIMIT` 도 같다 — **가지마다 붙이려면 괄호가 필요하다.**

```text
### SQL: SELECT name FROM emp LIMIT 1 UNION ALL SELECT name FROM dept LIMIT 1;
--- PG 18.6 ---
ERROR:  syntax error at or near "UNION"
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... near 'UNION ALL SELECT name FROM dept LIMIT 1' at line 1

### SQL: (SELECT name FROM emp ORDER BY id LIMIT 1) UNION ALL (SELECT name FROM dept ORDER BY id LIMIT 1);
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +-------+
-------                          | name  |
 ann                             +-------+
 sales                           | ann   |
(2 rows)                         | sales |
                                 +-------+
```

---

### 8. `NULL` 은 **하나의 값으로 취급된다**

**언제 쓰나** — `NULL` 이 섞인 목록을 합칠 때. **`=` 규칙과 정반대라 놀란다.**

```text
### SQL: SELECT NULL AS v INTERSECT SELECT NULL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 v                               +------+
---                              | v    |
                                 +------+
(1 row)                          | NULL |
                                 +------+
```

```text
 WHERE 의 비교 규칙                집합 연산의 중복 판정
 NULL = NULL  ->  UNKNOWN          NULL 과 NULL  ->  같다
   -> 행이 사라진다                  -> 한 행으로 접힌다 / 교집합에 남는다
 (04번 · 05번)                     (07번의 DISTINCT 와 같은 기준)
```

그림 해설 — `INTERSECT` 가 `NULL` 을 **양쪽에 다 있는 값**으로 인정했다.\
1번 절의 `EXCEPT` 에서 `NULL` 이 남은 것도 같은 규칙이다 — `dept.id` 에 `NULL` 이 없으니 "빼이지 않고" 남았다.\
비용 — **`NULL` 을 "값 없음"이 아니라 "특별한 값 하나"로 다룬다.** [07번](../07-distinct-and-duplicate-removal/)의 `DISTINCT` 와 같은 기준이고, [05번](../05-null-comparison-is-distinct-from/)의 `IS NOT DISTINCT FROM` 이 그 기준을 연산자로 꺼내 쓴 것이다.

---

### 9. 우선순위와 괄호

**언제 쓰나** — 셋을 섞어 쓸 때. **`INTERSECT` 가 더 세게 붙는다.**

```text
### SQL: SELECT 1 AS v UNION SELECT 2 INTERSECT SELECT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 v                               +---+
---                              | v |
 1                               +---+
 2                               | 1 |
(2 rows)                         | 2 |
                                 +---+

### SQL: (SELECT 1 AS v UNION SELECT 2) INTERSECT SELECT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 v                               +---+
---                              | v |
 2                               +---+
(1 row)                          | 2 |
                                 +---+
```

```text
 괄호 없이:  1 UNION (2 INTERSECT 2)  =  1 UNION {2}  =  {1, 2}
 괄호 주면:  (1 UNION 2) INTERSECT 2  =  {1,2} INTERSECT {2}  =  {2}
```

그림 해설 — **두 엔진이 같은 우선순위를 쓴다.** MySQL 8.0.31 릴리스 노트도 "`INTERSECT` groups before `EXCEPT` or `UNION`" 이라고 적는다.\
비용 — **섞어 쓸 때는 괄호를 친다.** 우선순위를 외우는 것보다 싸다.

**비표준 낱말은 둘 다 거부한다.**

```text
### SQL: SELECT id FROM dept MINUS SELECT dept_id FROM emp;
--- PG 18.6 ---
ERROR:  syntax error at or near "SELECT"
LINE 1: SELECT id FROM dept MINUS SELECT dept_id FROM emp;
                                  ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... near 'SELECT dept_id FROM emp' at line 1

### SQL: SELECT id, name FROM emp UNION CORRESPONDING SELECT name, id FROM dept;
--- PG 18.6 ---
ERROR:  syntax error at or near "CORRESPONDING"
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... near 'CORRESPONDING SELECT name, id FROM dept' at line 1
```

`MINUS` 는 다른 엔진의 `EXCEPT` 동의어이고, `CORRESPONDING` 은 **이름이 같은 열끼리 맞춰 주는** 문법이다.\
**두 엔진 다 없다** — 열 순서는 **직접 맞춰야 한다.**

---

### 10. 버전 — `INTERSECT`/`EXCEPT` 는 MySQL 8.0.31 부터

**언제 쓰나** — 5.7 이나 8.0 초기 버전을 쓰는 곳에 질의를 보낼 때.

MySQL 매뉴얼에는 도입 버전이 안 적혀 있으므로 **릴리스 노트로 접지한다.**

> "In this release MySQL adds support for the SQL standard `INTERSECT` and `EXCEPT` table operators."\
> — [MySQL 8.0.31 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-31.html)

같은 노트가 `DISTINCT`/`ALL` 지원과 우선순위도 함께 적는다 — 위 2번·9번 절의 실행 결과가 그것과 일치한다.

```text
 MySQL 8.0.30 이하        MySQL 8.0.31+ · 8.4         PostgreSQL
 UNION 만                 UNION · INTERSECT · EXCEPT  UNION · INTERSECT · EXCEPT
 -> INTERSECT 는 NOT EXISTS/                          (전부 오래전부터)
    EXISTS 로 우회했다 (19번)
```

비용 — 8.0.31 이전 MySQL 을 지원해야 하면 **`INTERSECT` 는 `EXISTS`, `EXCEPT` 는 `NOT EXISTS`** 로 쓴다([19번](../19-semi-anti-join/)).\
★ **단 그 우회는 `ALL` 의 개수 의미를 재현하지 못한다** — `EXCEPT ALL` 의 "2 − 1 = 1" 은 세미 조인으로 안 나온다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
-- 기본형
SELECT a, b FROM t1
UNION [ALL]        -- INTERSECT [ALL] · EXCEPT [ALL] 도 같은 자리
SELECT c, d FROM t2
ORDER BY 1         -- ★ 맨 끝에 한 번만. 이름은 첫 가지의 것
LIMIT 10;          -- ★ 전체에 걸린다

-- 가지마다 정렬·제한하려면 괄호
(SELECT name FROM emp ORDER BY id LIMIT 1)
UNION ALL
(SELECT name FROM dept ORDER BY id LIMIT 1);

-- 섞어 쓸 때는 괄호 (INTERSECT 가 더 세게 붙는다)
(SELECT 1 UNION SELECT 2) INTERSECT SELECT 2;
```

금지 사례 — **문법이 맞아 보이는데 거부되는 것들.**

```sql
-- X 가지 안의 ORDER BY / LIMIT (괄호 없이)   -> 양쪽 syntax error
SELECT name FROM emp ORDER BY name UNION SELECT name FROM dept;
-- X 열 개수 불일치                            -> PG: same number of columns / MySQL: ERROR 1222
SELECT id, name FROM emp UNION SELECT id FROM dept;
-- X 둘째 가지의 별칭으로 정렬                 -> PG: column "b" does not exist / MySQL: ERROR 1054
SELECT name AS a FROM emp UNION SELECT name AS b FROM dept ORDER BY b;
-- X MINUS · CORRESPONDING                     -> 양쪽 syntax error
SELECT ... MINUS SELECT ... ;
-- △ 타입 불일치                               -> PG 는 에러, MySQL 은 조용히 문자열로 합친다
SELECT id FROM emp UNION SELECT name FROM dept;
```

규칙 여덟.

1. **집합 연산은 행을 세로로 쌓는다.** 조인은 옆으로 붙인다.
2. **`ALL` 이 없으면 중복을 지운다.** 셋 다 그렇다.
3. **중복 판정 기준은 출력 행 전체**다([07번](../07-distinct-and-duplicate-removal/)).
4. **`UNION` 은 가지 안의 중복도 지운다** — 묻지 않아도.
5. **열 개수는 두 엔진 다 막고, 타입은 PG 만 막는다.**
6. **`ORDER BY`·`LIMIT` 은 전체에 한 번.** 가지마다는 괄호.
7. **결과 열 이름은 첫 가지가 정한다.**
8. **`NULL` 은 하나의 값으로 취급된다** — `=` 규칙과 반대다.

읽을 때 붙잡을 것은 **"행 수가 보존되어야 하나"** 하나다.

```text
 행 수가 의미를 갖나?
   ├─ 그렇다 (로그·거래·사원 목록)   -> UNION ALL. 겹침은 조건으로 잘라낸다
   └─ 아니다 (고유 키 목록)          -> UNION. 그래도 어느 가지에서 접혔는지 세어 보라
```

## 어디서 틀리나

- ★ **`UNION` 으로 두 목록을 합쳤는데 행이 줄어든다.**\
  [16번](../16-full-outer-join/)이 당한 그것이다. **뽑는 열이 바뀌면 행 수가 바뀐다** — 이름을 뽑으면 안 접히고, 부서 번호를 뽑으면 접힌다.
- **"가지 사이의 중복만 지운다"고 믿는다.**\
  **한 가지 안의 중복도 지운다.** 2행짜리 가지 둘이 `UNION` 으로 1행이 됐다(3번 절).
- **MySQL 에서 타입을 안 맞춘다.**\
  **에러도 경고도 없이** 정수와 문자열이 한 칸에 섞인다. **PG 에서 돌던 질의가 MySQL 에서 조용히 다른 답을 낸다.**
- **`EXCEPT` 의 방향을 뒤집어 쓴다.** `A EXCEPT B` 와 `B EXCEPT A` 는 다른 답이다(1번 절에서 `NULL` 대 `30`).
- **가지 안에 `ORDER BY` 를 쓴다.** 괄호 없이는 문법 오류다. 괄호를 쳐도 **전체 순서는 맨 끝 `ORDER BY`** 가 정한다.
- **둘째 가지의 별칭으로 정렬한다.** 결과 열 이름은 첫 가지의 것뿐이다.
- **`ORDER BY` 없이 순서를 기대한다.** MySQL 이 `20, 30, 10` 을 돌려준 것을 보라(7번 절).
- **`NULL` 이 안 합쳐질 거라 생각한다.** `=` 로는 안 맞지만 집합 연산에서는 **하나의 값**이다.
- **8.0.31 이전 MySQL 에 `INTERSECT` 를 보낸다.** 문법이 없다. `EXISTS` 로 우회하되 **`ALL` 의 개수 의미는 재현되지 않는다.**
- **큰 목록에 습관적으로 `UNION` 을 쓴다.** 중복 제거가 공짜가 아니다(6번 절의 `HashAggregate`).

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `ALL` 유무가 중복 제거를 가른다 | **결과의 정의** | 언어 — 두 엔진 같다 |
| 중복 판정 기준이 출력 행 전체 | **결과의 정의** | 언어 — 두 엔진 같다 |
| `NULL` 이 하나의 값으로 취급된다 | **결과의 정의** | 언어 — 두 엔진 같다 |
| `EXCEPT ALL` 의 개수 빼기 | **결과의 정의** | 언어 — 두 엔진 같다 |
| 결과 열 이름이 첫 가지의 것 | **결과의 정의** | 언어 — 두 엔진 같다 |
| `INTERSECT` 의 우선순위 | **문법의 정의** | 언어 — 두 엔진 같다(릴리스 노트도 명시) |
| 열 개수 불일치가 에러 | **문법의 정의** | 언어 — 두 엔진 같다 |
| **타입 불일치의 처리** | **엔진의 정책** | 갈린다 — PG 는 에러, MySQL 은 문자열로 합친다 |
| `INTERSECT`/`EXCEPT` 가 있나 | **버전** | MySQL 은 **8.0.31 부터**(릴리스 노트) |
| **결과의 순서** | 아무것도 아니다 | **아무도** — `ORDER BY` 만이 순서를 정한다 |
| 계획에 `HashAggregate`/`Union materialize` 가 뜨나 | **그 엔진의 표기** | 각 엔진 — 낱말이 다르다 |

- ★ **순서는 보장되지 않는다.** 이 주제에서 실제로 흔들린 것을 봤다 — MySQL 이 `SELECT id FROM dept UNION ALL …` 에 **`20, 30, 10`** 을 돌려줬다(7번 절).\
  `dept` 의 기본키 순서도, 삽입 순서도 아니다. **출력 순서로 무엇을 추론하지 마라.**
- ★ **계획은 관찰이지 보장이 아니다.** 6번 절의 계획은 **작성 중 한 번, 제출 직전 한 번** 찍었고 **두 번 다 같았다.**\
  볼 것은 비용 수치가 아니라 **중복 제거 노드의 유무**다.
- MySQL 계획에 `Covering index scan on dept using name` 이 뜬 것은 **`dept.name` 에 `UNIQUE` 가 있어서**다 — 데이터·스키마에 달린 선택이지 집합 연산의 성질이 아니다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — `UNION ALL` 로 여러 소스를 쌓을 때.** 월별 파티션·여러 지점·여러 로그를 한 결과로.
- **쓴다 — 고유 목록을 만들 때.** "이 시스템에 등장하는 모든 부서 번호" 같은 것은 `UNION` 이 정확하다.
- **쓴다 — 두 목록의 차이를 볼 때.** `EXCEPT` 로 "한쪽에만 있는 것"을 뽑는 것이 조인보다 곧다.
- **쓴다 — MySQL 에서 `FULL OUTER JOIN` 을 흉내 낼 때.** **`UNION ALL` + 반조인**이다([16번](../16-full-outer-join/)).
- **쓴다 — 재귀 CTE 의 뼈대.** `UNION ALL` 이 기본이고, `UNION` 은 고리를 끊는 장치가 된다([33번](../33-recursive-cte/)).
- **안 쓴다 — 같은 표를 조건만 바꿔 여러 번 읽을 때.** 한 번 읽고 `CASE`/`FILTER` 로 나누는 편이 싸다([24번](../24-conditional-aggregation-filter-case/)).
- **안 쓴다 — "있는지만" 물을 때.** `EXISTS` 가 정확한 도구다([19번](../19-semi-anti-join/)).
- **주의 — 행 수가 의미를 가지면 `UNION` 금지.** 3번 절의 함정이 그대로 재현된다.
- **주의 — MySQL 에서는 타입을 직접 맞춘다.** `CAST` 를 쓴다.

## 핵심 문장

- 집합 연산은 **행을 세로로 쌓는 것**이고, 조인은 **열을 옆으로 붙이는 것**이다.
- **`ALL` 이 없으면 중복을 지운다** — `UNION`·`INTERSECT`·`EXCEPT` 셋 다.
- ★ **`UNION` 은 가지 사이뿐 아니라 가지 안의 중복까지 지운다.** 묻지 않아도.
- **행 수가 의미를 가지면 `UNION` 을 쓰지 마라** — `UNION ALL` + 조건으로 잘라낸다.
- **중복 판정 기준은 출력 행 전체**이고, **`NULL` 은 하나의 값**으로 취급된다.
- **열 개수는 두 엔진 다 막지만, 타입 불일치는 PG 만 막는다** — MySQL 은 조용히 문자열로 합친다.
- **`ORDER BY`·`LIMIT` 은 전체에 한 번**, 결과 열 이름은 **첫 가지**가 정한다.
- **MySQL 의 `INTERSECT`/`EXCEPT` 는 8.0.31 부터**다(릴리스 노트).

## 관련 자료

- [PostgreSQL 18 · Combining Queries](https://www.postgresql.org/docs/18/queries-union.html) — 셋의 의미와 `ALL` 이 한 페이지에 있다.
- [MySQL 8.4 · Set Operations with UNION, INTERSECT, and EXCEPT](https://dev.mysql.com/doc/refman/8.4/en/set-operations.html)
- [MySQL 8.0.31 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-31.html) — `INTERSECT`/`EXCEPT` 도입 문장. **매뉴얼에는 버전이 없다.**
- [07 DISTINCT 와 중복 제거](../07-distinct-and-duplicate-removal/) — **경계: 그쪽은 한 결과 안의 중복을 지우는 기준(행 전체·`NULL`)까지, 여기는 그 기준이 두 결과를 합칠 때 어떻게 쓰이나부터.**
- [16 FULL OUTER JOIN](../16-full-outer-join/) — **경계: 그쪽은 양쪽 짝 없는 행을 남기는 조인까지, 여기는 그 우회에서 `UNION` 이 행을 접은 이유부터.** 3번 절이 그 실험의 재인용이다.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 한 질의 안 여덟 칸까지, 여기는 그 질의를 둘 이상 쌓았을 때 `ORDER BY` 가 어디 붙나부터.**
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) · [05 NULL 비교](../05-null-comparison-is-distinct-from/) — **경계: 그쪽은 `NULL` 의 비교 규칙까지, 여기는 그 규칙이 집합 연산에서 뒤집히는 것부터.**
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — **경계: 그쪽은 두 값을 비교·연산할 때 어느 타입으로 맞추나까지, 여기는 두 결과의 열 타입을 맞출 때 무엇이 에러가 되나부터.**
- [19 세미·안티 조인](../19-semi-anti-join/) — 8.0.31 이전 MySQL 에서 `INTERSECT`/`EXCEPT` 를 우회하는 도구.
- [33 재귀 CTE](../33-recursive-cte/) — **경계: 여기는 `UNION` 과 `UNION ALL` 의 의미·비용까지, 거기는 그 차이가 무한 루프를 막느냐부터.**
- [24 조건부 집계 — FILTER 와 CASE](../24-conditional-aggregation-filter-case/) — 같은 표를 여러 번 읽는 `UNION` 대신 한 번 읽는 처방.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **집합 연산(set operation)** — 두 질의 결과를 행 단위로 합치거나 빼는 연산. `UNION`·`INTERSECT`·`EXCEPT`.\
  예: `SELECT dept_id FROM emp UNION SELECT id FROM dept`.
- **`UNION`** — 두 결과를 합치고 **중복을 지운다**.\
  예: `{10,10,20,NULL}` 과 `{10,20,30}` 을 합쳐 `{10,20,30,NULL}` 4행.
- **`UNION ALL`** — 합치기만 하고 **중복을 안 지운다**.\
  예: 같은 두 목록이 7행 그대로 나온다.
- **`INTERSECT`** — 양쪽에 **다 있는** 행만 남긴다.\
  예: `{10,10,20,NULL}` ∩ `{10,20,30}` = `{10,20}`.
- **`EXCEPT`** — 왼쪽에는 있고 오른쪽에는 **없는** 행만 남긴다. **방향이 있다.**\
  예: `emp.dept_id EXCEPT dept.id` = `{NULL}`, 반대로 하면 `{30}`.
- **다중집합(multiset, 가방)** — 같은 원소가 여러 번 들어갈 수 있는 집합. `ALL` 이 붙으면 이쪽 연산이 된다.\
  예: `EXCEPT ALL` 에서 왼쪽 `10` 둘 − 오른쪽 `10` 하나 = `10` 하나.
- **가지(branch, 갈래)** — 집합 연산으로 이어진 각 `SELECT` 문.\
  예: `A UNION B` 에서 `A` 와 `B` 가 각각 한 가지다.
- **중복 판정 기준** — 두 행이 같은지 보는 기준. **출력 행 전체**이고 `NULL` 은 같은 값으로 본다.\
  예: `(10, 10)` 두 행이 한 행으로 접힌 것.
- **`HashAggregate`** — PostgreSQL 계획에서 **해시로 묶어 중복을 지우는** 노드.\
  예: `UNION` 에는 뜨고 `UNION ALL` 에는 안 뜬다.
- **`Union materialize with deduplication`** — MySQL `EXPLAIN FORMAT=TREE` 의 표기. 모아 두고 중복을 지운다.\
  예: `UNION ALL` 에서는 `Append` + `Stream results` 로 바뀐다.
- **반조인(anti join)** — "짝이 없는 행만" 고르는 조인. `WHERE 키 IS NULL` 이나 `NOT EXISTS` 로 쓴다.\
  예: `FULL OUTER JOIN` 우회의 `WHERE e.id IS NULL`. [목록의 **19번 주제**](../19-semi-anti-join/).
- **`CORRESPONDING`** — 이름이 같은 열끼리 맞춰 주는 표준 문법. **두 엔진 다 없다.**\
  예: `UNION CORRESPONDING` → 양쪽 syntax error.

## 더 들어가면

- **`UNION` 대신 `UNION ALL` + `GROUP BY`** 를 쓰면, 어느 가지에서 온 행인지 세면서 중복을 지울 수 있다 — 3번 절의 사고를 **보이게** 만드는 방법이다.
- **`EXCEPT` 로 두 질의 결과가 같은지 검사**할 수 있다 — `(A EXCEPT B) UNION ALL (B EXCEPT A)` 가 0행이면 집합으로 같다. 리팩터링 전후 비교에 쓴다.
- **`UNION ALL` 은 정렬을 요구하지 않아 첫 행이 일찍 나온다**(MySQL 계획의 `Stream results`). 페이지네이션과 궁합이 좋다([09번](../09-limit-offset-keyset-pagination/)).
- **집합 연산 결과에는 인덱스가 없다.** 큰 결과를 다시 조인할 거면 CTE 로 이름을 붙여 [32번](../32-cte-with-clause/)의 물질화 이야기로 넘어간다.
- **`INTERSECT`/`EXCEPT` 에도 `ALL` 이 있다**는 것은 잘 안 알려져 있다. 두 엔진 다 지원하고(2번 절), 개수를 세는 의미가 된다.
