# sql/18-USING 과 NATURAL JOIN — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 10·11번의 `deptx` 는 **기존 `dept` 에서 만들어** 트랜잭션 안에서 쓰고 롤백했다(MySQL 은 `CREATE` → 질의 → `DROP`).\
> **`emp`·`dept` 는 한 행도 바꾸지 않았다.**\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `ON` 과 `USING` 의 결과

**행 수는 둘 다 3 으로 같다. 열이 6 에서 5 로 줄고, 합쳐진 `dept_id` 가 맨 앞으로 간다.**

```text
### SQL: SELECT * FROM emp e JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d
         ON e.dept_id = d.dept_id ORDER BY e.id;
--- PG 18.6 ---
 id | name | dept_id | salary | dept_id | dept_name 
----+------+---------+--------+---------+-----------
  1 | ann  |      10 |    300 |      10 | sales
  2 | bob  |      10 |    500 |      10 | sales
  3 | cho  |      20 |        |      20 | dev
(3 rows)
--- MySQL 8.4.10 ---
+----+------+---------+--------+---------+-----------+
| id | name | dept_id | salary | dept_id | dept_name |
+----+------+---------+--------+---------+-----------+
|  1 | ann  |      10 |    300 |      10 | sales     |
|  2 | bob  |      10 |    500 |      10 | sales     |
|  3 | cho  |      20 |   NULL |      20 | dev       |
+----+------+---------+--------+---------+-----------+

### SQL: SELECT * FROM emp e JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d
         USING (dept_id) ORDER BY e.id;
--- PG 18.6 ---
 dept_id | id | name | salary | dept_name 
---------+----+------+--------+-----------
      10 |  1 | ann  |    300 | sales
      10 |  2 | bob  |    500 | sales
      20 |  3 | cho  |        | dev
(3 rows)
--- MySQL 8.4.10 ---
+---------+----+------+--------+-----------+
| dept_id | id | name | salary | dept_name |
+---------+----+------+--------+-----------+
|      10 |  1 | ann  |    300 | sales     |
|      10 |  2 | bob  |    500 | sales     |
|      20 |  3 | cho  |   NULL | dev       |
+---------+----+------+--------+-----------+
```

**왜 그런가**

```text
 ON 으로 붙였을 때의 열 목록
   emp 의 것 네 개          d 의 것 두 개
   id  name  dept_id  salary  |  dept_id  dept_name
                       ↑              ↑
                 같은 값이 두 번 찍힌다

 USING 으로 붙였을 때
   dept_id  |  id  name  salary  |  dept_name
      ↑                     ↑
  합쳐진 칸 하나가 맨 앞    나머지는 왼쪽 → 오른쪽 순서 그대로
```

| | `ON` | `USING` |
|---|---|---|
| 행 수 | 3 | **3 — 같다** |
| 열 수 | 6 | **5** |
| 합쳐진 열의 자리 | — | **맨 앞** |
| 두 엔진이 같은가 | 같다 | **같다** — 개수도 순서도 |

★ **`USING` 은 조건이 아니라 투영을 바꾼다.** 어느 행이 남는지는 `ON` 과 똑같고, **어느 열이 나오는지**만 다르다.

**대가** — `SELECT *` 를 **열 위치로** 읽는 코드가 있으면 `ON` ↔ `USING` 교체가 그대로 깨진다.

---

### 2. 한정자 없이 공통 열 부르기

**`ON` 이면 에러, `USING` 이면 통과한다.**

```text
### SQL: SELECT dept_id FROM emp e JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d
         ON e.dept_id = d.dept_id;
--- PG 18.6 ---
ERROR:  column reference "dept_id" is ambiguous
LINE 1: SELECT dept_id FROM emp e JOIN (SELECT id AS dept_id, name A...
               ^
--- MySQL 8.4.10 ---
ERROR 1052 (23000) at line 1: Column 'dept_id' in field list is ambiguous

### SQL: SELECT dept_id, e.dept_id AS from_e, d.dept_id AS from_d
         FROM emp e JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d USING (dept_id) ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | from_e | from_d       +---------+--------+--------+
---------+--------+--------      | dept_id | from_e | from_d |
      10 |     10 |     10       +---------+--------+--------+
      10 |     10 |     10       |      10 |     10 |     10 |
      20 |     20 |     20       |      10 |     10 |     10 |
(3 rows)                         |      20 |     20 |     20 |
                                 +---------+--------+--------+
```

**왜 그런가**

```text
 ON 으로 붙이면         이름 dept_id 를 가진 열이 둘       -> 어느 쪽인지 못 정한다 -> 에러
 USING 으로 붙이면      이름 dept_id 를 가진 열이 하나     -> 정할 것이 없다 -> 통과
                        (양쪽을 따로 보려면 한정자를 붙인다)
```

★ **`USING` 의 진짜 값은 이것이다** — 조인 뒤에 공통 열을 여러 번 쓰는 질의에서 한정자를 다 붙일 필요가 없어진다.\
내부 조인에서는 `dept_id`·`from_e`·`from_d` 셋이 항상 같다 — 그것이 조인 조건이었기 때문이다.

모호한 열 참조 자체의 정본은 [10번](../10-from-clause-aliases-derived-tables/)이다.

---

### 3. 외부 조인에서 합쳐진 열

**`dept_id` = 30 · `from_e` = `NULL` · `from_d` = 30 이다.**

```text
### SQL: SELECT dept_id, e.dept_id AS from_e, d.dept_id AS from_d
         FROM emp e RIGHT JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d
         USING (dept_id) ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | from_e | from_d       +---------+--------+--------+
---------+--------+--------      | dept_id | from_e | from_d |
      10 |     10 |     10       +---------+--------+--------+
      10 |     10 |     10       |      10 |     10 |     10 |
      20 |     20 |     20       |      10 |     10 |     10 |
      30 |        |     30       |      20 |     20 |     20 |
(4 rows)                         |      30 |   NULL |     30 |
                                 +---------+--------+--------+
```

**왜 그런가**

```text
 hr (30번) 은 사원이 없어 짝이 없다.  RIGHT JOIN 이 그 행을 남긴다.

 e 쪽은 통째로 NULL 로 채워진다        ->  from_e = NULL
 d 쪽은 원래 값 그대로                 ->  from_d = 30
 합쳐진 칸은?                          ->  30      <- "있는 쪽 값"이 들어간다
                                             ↑
              COALESCE(e.dept_id, d.dept_id) 와 같은 모양이다
```

**두 엔진이 같은 값을 냈다.** 이것은 옵티마이저의 선택이 아니라 **결과의 정의**다.

---

### 4. 그것이 왜 문제인가

**합쳐진 열만 보면 짝이 없었다는 사실이 사라진다. 한정자 붙인 열로 봐야 한다.**

```text
 SELECT * 로 본 hr 행                   실제로는
 dept_id = 30 (멀쩡한 값)                왼쪽에 짝이 없어서 NULL 로 채워진 행
       ↑
  "부서 30 의 사원 정보가 있다"로 읽힌다
```

```text
 짝 유무를 보려면                       왜
 WHERE e.dept_id IS NULL                합쳐진 열이 아니라 한쪽 열을 본다
       ↑
  이것이 곧 안티 조인이다 — 19번 주제
```

★ **`USING` 은 두 열을 하나로 합치면서 「둘이 달랐는지」가 아니라 「어느 쪽이 없었는지」를 지운다.**\
내부 조인에서는 잃을 정보가 없지만(양쪽이 항상 같다), **외부 조인에서는 잃는다.**

```text
 ON 으로 썼다면                          USING 으로 썼다면
 +---------------------------+          +--------------------+
 | e.dept_id | d.dept_id     |          | dept_id            |
 |   NULL    |    30         |          |   30               |
 +---------------------------+          +--------------------+
   한쪽이 NULL 인 게 바로 보인다           안 보인다
```

**그래서 외부 조인에서 짝 유무가 중요하면 `ON` 을 쓴다.**\
짝 없는 행만 뽑는 형태(`LEFT JOIN … IS NULL`)는 [19번](../19-semi-anti-join/)이 정본이고, `ON` 과 `WHERE` 의 자리 문제는 [15번](../15-on-vs-where-in-outer-join/)이다.

---

### 5. `USING` 에 없는 열을 적으면

**두 엔진 다 즉시 에러다.**

```text
### SQL: SELECT * FROM emp e JOIN dept d USING (dept_id);
--- PG 18.6 ---
ERROR:  column "dept_id" specified in USING clause does not exist in right table
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'dept_id' in 'from clause'
```

**왜 그런가** — `dept` 에는 `dept_id` 열이 없다. `USING` 은 **양쪽에 다 있는 이름**만 받는다.

★ **이것이 `USING` 의 안전장치다.** 이름을 내가 적었으므로, 그 이름이 사라지면 **에러로 드러난다.**

```text
 USING (dept_id)                          NATURAL JOIN
 한쪽에서 dept_id 가 없어졌다             한쪽에서 열이 없어졌다
        ↓                                        ↓
     에러로 터진다                        조건이 하나 줄어든 채 조용히 돈다
        ↑                                        ↑
   이름을 적었기 때문                     적을 이름이 없기 때문
```

**PG 의 문구가 더 구체적이다** — `does not exist in right table` 이라고 **어느 쪽인지**까지 알려 준다.

---

### 6. `NATURAL JOIN` 의 0행

**`id` 와 `name` 둘 다로 붙었기 때문이다. 엔진이 만든 조건은 `ON emp.id = dept.id AND emp.name = dept.name` 이다.**

```text
### SQL: SELECT COUNT(*) AS n FROM emp NATURAL JOIN dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 0                               +---+
(1 row)                          | 0 |
                                 +---+
```

**왜 그런가 — 엔진이 한 일을 순서대로**

```text
 1) 양쪽 열 이름을 모은다
      emp  : id  name  dept_id  salary
      dept : id  name
 2) 겹치는 이름을 전부 고른다
      id, name
 3) AND 로 이어 조건을 만든다
      ON emp.id = dept.id AND emp.name = dept.name
 4) 돌린다
      emp.id 는 1~4,  dept.id 는 10~30   -> 겹치는 값이 하나도 없다
 5) 0행
```

★ **의도했던 `emp.dept_id` 는 조건에 들어가지도 않았다.** 이름이 안 겹치기 때문이다.

같은 조건을 손으로 적어 확인할 수 있다 — `USING (id, name)` 이 그것이고, **결과도 0행으로 같다**(아래 12번).

```text
 "부서를 붙인다"는 의도                  실제로 만들어진 조건
 emp.dept_id = dept.id                   emp.id = dept.id AND emp.name = dept.name
        ↑                                        ↑
   이름이 다르므로 후보에도 없다          이름만 같고 뜻은 전혀 다른 두 쌍
```

**이 결과 자체는 [13번](../13-inner-join/)에서 이미 봤다. 여기서 새로 인출할 것은 「조건이 어떻게 만들어졌나」다.**

---

### 7. `NATURAL LEFT JOIN`

**4행이고 열은 `id, name, dept_id, salary` 넷이다. `SELECT * FROM emp` 과 구분되지 않는다.**

```text
### SQL: SELECT * FROM emp NATURAL LEFT JOIN dept ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary     +----+------+---------+--------+
----+------+---------+--------    | id | name | dept_id | salary |
  1 | ann  |      10 |    300     +----+------+---------+--------+
  2 | bob  |      10 |    500     |  1 | ann  |      10 |    300 |
  3 | cho  |      20 |            |  2 | bob  |      10 |    500 |
  4 | dan  |         |    400     |  3 | cho  |      20 |   NULL |
(4 rows)                          |  4 | dan  |    NULL |    400 |
                                  +----+------+---------+--------+
```

**왜 그런가**

```text
 dept 의 열은 id, name 둘뿐이다
 그 둘이 전부 공통 열로 합쳐졌다
        ↓
 결과에 dept 쪽 열이 하나도 안 남는다
        ↓
 LEFT JOIN 이라 emp 4행은 다 남는다
        ↓
 SELECT * FROM emp 과 글자 하나 안 다른 결과
```

```text
 6번 (NATURAL JOIN)                7번 (NATURAL LEFT JOIN)
 +--------------------------+      +--------------------------+
 | 0행                      |      | 4행 — 평소와 똑같아 보인다 |
 | "뭔가 이상하다"가 보인다  |      | 아무도 이상하다고 안 한다  |
 +--------------------------+      +--------------------------+
        ↓                                   ↓
   눈에 띄는 실패                      완전한 무음 실패
```

★ **0행보다 4행이 훨씬 위험하다.** "부서명을 붙였다"고 믿고 이 결과를 넘기면, 부서명 칸이 아예 없다는 것도 **`SELECT *` 라 안 보인다.**

---

### 8. 공통 열이 하나도 없으면

**12행이다. 두 엔진 다 막지 않는다.**

```text
### SQL: SELECT COUNT(*) AS n FROM emp NATURAL JOIN (SELECT id AS d_id, name AS d_name FROM dept) x;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +----+
----                             | n  |
 12                              +----+
(1 row)                          | 12 |
                                 +----+

### SQL: SELECT * FROM emp NATURAL JOIN (SELECT id AS d_id, name AS d_name FROM dept) x ORDER BY id, d_id;
--- PG 18.6 ---
 id | name | dept_id | salary | d_id | d_name 
----+------+---------+--------+------+--------
  1 | ann  |      10 |    300 |   10 | sales
  1 | ann  |      10 |    300 |   20 | dev
  1 | ann  |      10 |    300 |   30 | hr
  2 | bob  |      10 |    500 |   10 | sales
  2 | bob  |      10 |    500 |   20 | dev
  2 | bob  |      10 |    500 |   30 | hr
  3 | cho  |      20 |        |   10 | sales
  3 | cho  |      20 |        |   20 | dev
  3 | cho  |      20 |        |   30 | hr
  4 | dan  |         |    400 |   10 | sales
  4 | dan  |         |    400 |   20 | dev
  4 | dan  |         |    400 |   30 | hr
(12 rows)
--- MySQL 8.4.10 ---
+----+------+---------+--------+------+--------+
| id | name | dept_id | salary | d_id | d_name |
+----+------+---------+--------+------+--------+
|  1 | ann  |      10 |    300 |   10 | sales  |
|  1 | ann  |      10 |    300 |   20 | dev    |
|  1 | ann  |      10 |    300 |   30 | hr     |
|  2 | bob  |      10 |    500 |   10 | sales  |
|  2 | bob  |      10 |    500 |   20 | dev    |
|  2 | bob  |      10 |    500 |   30 | hr     |
|  3 | cho  |      20 |   NULL |   10 | sales  |
|  3 | cho  |      20 |   NULL |   20 | dev    |
|  3 | cho  |      20 |   NULL |   30 | hr     |
|  4 | dan  |    NULL |    400 |   10 | sales  |
|  4 | dan  |    NULL |    400 |   20 | dev    |
|  4 | dan  |    NULL |    400 |   30 | hr     |
+----+------+---------+--------+------+--------+
```

**왜 그런가**

```text
 겹치는 이름이 하나도 없다
        ↓
 조인 조건을 만들 재료가 없다
        ↓
 조건이 빈 조인 = 모든 짝
        ↓
 4 x 3 = 12행        <- 12번 주제의 카티션곱 그대로
```

★ **에러가 아니다.** `NATURAL JOIN` 은 "겹치는 이름으로 붙인다"고만 정의돼 있고, 겹치는 이름이 0개여도 그 정의를 만족한다.

**어느 쪽도 안 막아 준다** — [13번](../13-inner-join/)의 `JOIN … ON` 누락은 PG 가 구문 오류로 막았지만, 이쪽은 두 엔진 다 통과시킨다.

---

### 9. 조건 없는 조인의 세 경로

```text
 (A) CROSS JOIN               의도한 것이다                    -> 12번
 (B) MySQL 의 JOIN … ON 누락  PG 는 구문 오류로 막는다         -> 13번
 (C) 공통 열 없는 NATURAL     두 엔진 다 안 막는다   <- 가장 조용하다
```

| 경로 | PostgreSQL 18.6 | MySQL 8.4.10 | 조용한 정도 |
|---|---|---|---|
| (A) `CROSS JOIN` | 통과 (의도) | 통과 (의도) | — 의도한 것이다 |
| (B) `JOIN` 에 `ON` 누락 | **구문 오류** | 12행 | 한쪽이 막아 준다 |
| (C) 공통 열 없는 `NATURAL` | **12행** | **12행** | **아무도 안 막는다** |

**왜 (C) 가 가장 조용한가**

```text
 (B) 는 "조건을 안 적었다"가 질의에 보인다
       FROM emp e JOIN dept d          <- ON 이 없는 게 눈에 띈다

 (C) 는 "조건을 안 적는 것"이 정상 문법이다
       FROM emp NATURAL JOIN deptx     <- 아무 이상이 없어 보인다
                    ↑
   조건이 없는 게 아니라 "보이지 않는" 것이다
```

★ **(C) 의 사고는 질의를 아무리 읽어도 안 보인다.** 읽어야 할 것은 질의가 아니라 **양쪽 표의 열 목록**이다.

---

### 10. 열 하나를 추가하면

**3 에서 0 이 된다. 질의는 한 글자도 안 바뀌었다.**

```text
### SQL: (전) SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;    -- deptx 열 = dept_id, dept_name
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 3                               +---+
(1 row)                          | 3 |
                                 +---+

### SQL: ALTER TABLE deptx ADD COLUMN name …;
         (후) SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;    -- 같은 문
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 0                               +---+
(1 row)                          | 0 |
                                 +---+
```

<details>
<summary>deptx 를 만드는 문 — 기존 dept 에서 만들고 롤백했다</summary>

```sql
-- PostgreSQL
BEGIN;
CREATE TABLE deptx (dept_id int PRIMARY KEY, dept_name text);
INSERT INTO deptx SELECT id, name FROM dept;      -- dept 는 읽기만 한다
SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;  -- 3
ALTER TABLE deptx ADD COLUMN name text;
SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;  -- 0
ROLLBACK;
```

```sql
-- MySQL: DDL 에 트랜잭션이 안 걸리므로 CREATE -> 질의 -> DROP
CREATE TABLE deptx (dept_id int PRIMARY KEY, dept_name varchar(20));
INSERT INTO deptx SELECT id, name FROM dept;
SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;
ALTER TABLE deptx ADD COLUMN name varchar(20);
SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;
DROP TABLE deptx;
```

**두 DB 모두 실험 뒤 표가 남아 있지 않다.**

</details>

**왜 그런가**

```text
 (전) 겹치는 이름: dept_id                 (후) 겹치는 이름: dept_id, name
        ↓                                         ↓
 ON emp.dept_id = deptx.dept_id            ON emp.dept_id = deptx.dept_id
                                              AND emp.name = deptx.name
        ↓                                         ↓
       3행                                   name 이 전부 NULL -> UNKNOWN -> 0행
```

**왜 코드 리뷰로 안 잡히나**

```text
 바뀐 파일              바뀌지 않은 파일
 +------------------+   +--------------------------------+
 | 마이그레이션 SQL  |   | 질의가 들어 있는 애플리케이션   |
 | ALTER TABLE …     |   | SELECT … NATURAL JOIN deptx     |
 | ADD COLUMN name   |   | (한 글자도 안 바뀐다)           |
 +------------------+   +--------------------------------+
        ↑                            ↑
  리뷰어는 열 추가를 본다      리뷰어는 이 파일을 볼 이유가 없다
                                     ↓
          두 파일을 같이 보는 사람이 없으면 아무도 못 잡는다
```

★ **깨지는 지점과 원인이 다른 파일·다른 사람·다른 시점에 있다.** 이것이 「조용히 깨진다」의 정확한 뜻이다.\
테스트가 잡으려면 **그 질의의 행 수를 고정하는 테스트**가 있어야 하는데, `NATURAL JOIN` 을 쓰는 코드베이스는 대개 그런 테스트도 없다.

---

### 11. `USING` 이었다면

**열이 추가돼도 3행 그대로이고, 지목한 열이 사라지면 에러로 터진다.**

**10번과 같은 `deptx` 에 같은 순서로 손을 대며 `USING (dept_id)` 를 돌렸다.**

```text
### SQL: (전) SELECT COUNT(*) AS n FROM emp JOIN deptx USING (dept_id);   -- deptx 열 = dept_id, dept_name
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 3                               +---+
(1 row)                          | 3 |
                                 +---+

### SQL: ALTER TABLE deptx ADD COLUMN name …;   뒤에 같은 문을 다시
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 3                               +---+
(1 row)                          | 3 |
                                 +---+

### SQL: ALTER TABLE deptx RENAME COLUMN dept_id TO did;   뒤에 같은 문을 다시
--- PG 18.6 ---
ERROR:  column "dept_id" specified in USING clause does not exist in right table
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 7: Unknown column 'dept_id' in 'from clause'
```

```text
 NATURAL JOIN        3  ->  0        (조용히 바뀐다)
 USING (dept_id)     3  ->  3        (불변)
                        ->  ERROR    (지목한 열이 사라지면)
                              ↑
              스키마 변경의 결과가 "불변" 아니면 "에러" 둘 중 하나다
```

| 스키마에 생긴 일 | `NATURAL JOIN` | `USING (dept_id)` |
|---|---|---|
| 관계없는 열이 추가됨 | **조건이 늘어 결과가 바뀐다** | 불변 |
| 이름이 겹치는 열이 추가됨 | **조건이 늘어 결과가 바뀐다** | 불변 |
| 지목한 열이 사라짐 | **조건이 줄어 결과가 바뀐다** | **에러** |
| 지목한 열의 이름이 바뀜 | **조건이 바뀐다** | **에러** |

★ **`USING` 은 「조용히 바뀐다」를 「에러」로 바꾼다.** 그것이 이 둘의 유일하면서 결정적인 차이다.

그리고 `ON` 은 한 걸음 더 간다 — **열 이름이 같을 필요조차 없으므로** 이름 규칙 변화에 아예 무관해진다.

---

### 12. `USING` 도 조용할 수 있나

**할 수 있다. `USING (id, name)` 은 0행이고, 이것은 `emp NATURAL JOIN dept` 를 손으로 쓴 것이다.**

```text
### SQL: SELECT * FROM emp e JOIN dept d USING (id, name) ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary    (빈 결과 — 출력이 한 줄도 없다)
----+------+---------+--------
(0 rows)
```

**열이 넷뿐이다.** `dept` 의 `id`·`name` 이 둘 다 합쳐져 사라졌다 — 7번의 `NATURAL LEFT JOIN` 과 같은 모양이다.

**한 줄로** — **`USING` 이 보장하는 것은 「엔진이 조건을 고르지 않는다」이지 「내가 고른 조건이 옳다」가 아니다.**

```text
 USING 이 막아 주는 것                 USING 이 못 막는 것
 +-------------------------------+     +-------------------------------+
 | 스키마가 바뀌어 조건이 달라짐  |     | 내가 처음부터 틀린 열을 지목함 |
 |   -> 불변 또는 에러            |     |   -> 조용히 0행               |
 +-------------------------------+     +-------------------------------+
```

★ **`emp.id` 와 `dept.id` 처럼 이름만 같고 뜻이 다른 열**은 어떤 문법도 못 막는다.\
막는 것은 **이름 규칙**이다 — 기본키를 `emp_id`·`dept_id` 로 부르면 `NATURAL JOIN` 조차 옳게 붙는다.\
다만 그 규칙에 기대는 순간 **규칙을 바꾸는 사람이 질의를 깨뜨릴 수 있게 된다.** 그래서 결론은 그대로다 — **`NATURAL JOIN` 은 쓰지 않는다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `ON` 대 `USING` 열 목록 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **열 개수·순서가 두 엔진에서 같았다** |
| 모호한 열 참조 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거다** |
| 외부 조인 + `USING` (3·4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `hr` 행의 30 / `NULL` / 30 |
| `USING` 에 없는 열 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거다** |
| `NATURAL JOIN` 0행 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | [13번](../13-inner-join/) 결과의 재확인 |
| `NATURAL LEFT JOIN` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **4행 — `SELECT * FROM emp` 과 동일** |
| 공통 열 없는 `NATURAL` (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **12행 — 두 엔진 다 안 막는다** |
| 열 추가 전/후 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `deptx` — 트랜잭션 롤백 / `DROP` · **3 → 0** |
| `USING` 의 스키마 내성 (11번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `deptx` — 열 추가·열 이름 변경. **3 → 3 → 에러** |
| `USING (id, name)` (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 0행 |
| `deptx` 잔재 확인 | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\dt` · `SHOW TABLES` 로 확인 |

**구현 의존 항목** — 없다. 열 합치기·합쳐진 열의 위치·외부 조인에서의 값까지 두 엔진이 한 자리도 안 갈렸다.\
**방언이 갈리는 항목** — **없다.** 다른 것은 **에러 문구**뿐이다(PG 가 `does not exist in right table` 로 더 구체적이다).\
목록 README 의 `18 … 표준` 표기는 **실행으로 확인됐다.**

**순서 보장** — 없다. 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.\
**`emp`·`dept` 변경** — 없다. `deptx` 만 만들었고 실험 뒤 남아 있지 않다.

**11번도 실측이다** — 같은 `deptx` 에 열 추가·열 이름 변경을 차례로 걸고 `USING (dept_id)` 를 세 번 돌렸다(3 → 3 → 에러).
