# sql/18-USING 과 NATURAL JOIN — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions (Joined Tables)](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 「열을 하나 추가했더니 결과가 바뀐다」 절의 `deptx` 표는 **기존 `dept` 에서 만들어 트랜잭션 안에서 쓰고 롤백**했다(MySQL 은 `CREATE` → 질의 → `DROP`).\
> **`emp`·`dept` 는 한 행도 바꾸지 않았다.**\
> **버전** — `USING`·`NATURAL JOIN` 모두 두 엔진에 오래전부터 있고, 두 매뉴얼에 도입 버전이 없어 **버전은 적지 않는다.**\
> **선행** — [13 INNER JOIN](../13-inner-join/). 13편이 보인 **`NATURAL JOIN` 의 0행**을 여기서 파고든다.

## 한눈에 — 쉽게 말하면

**`USING` = 「이 이름으로 붙여라」라고 **내가 지목**하는 것. `NATURAL JOIN` = 「이름이 같은 건 알아서 다 붙여라」라고 **엔진에 맡기는** 것.**

서류 두 뭉치를 맞춰 붙인다고 하자.

```text
 ON — 어느 칸과 어느 칸인지 다 적는다
   "왼쪽 서류의 부서번호 칸과 오른쪽 서류의 번호 칸을 맞춰라"
       -> 길지만 틀릴 데가 없다

 USING — 칸 이름 하나만 적는다 (양쪽 이름이 같을 때)
   "부서번호 칸으로 맞춰라"
       -> 짧고, 지목은 내가 한다.  그리고 그 칸이 하나로 합쳐진다

 NATURAL — 아무것도 안 적는다
   "이름이 같은 칸은 전부 알아서 맞춰라"
       -> 가장 짧다.  그리고 무엇으로 붙었는지 질의만 봐서는 알 수 없다
```

| 비유 | 실체 |
|---|---|
| 맞출 칸을 다 적는다 | `ON e.dept_id = d.id` |
| 칸 이름 하나만 적는다 | `USING (dept_id)` — **내가 지목** |
| 알아서 맞추라고 한다 | `NATURAL JOIN` — **엔진이 이름으로 고른다** |
| 합쳐진 칸 하나 | `USING`/`NATURAL` 이 만든 **공통 열 한 개** |
| 서류 양식에 칸이 하나 늘었다 | 테이블에 열이 추가됐다 |
| **그랬더니 붙는 규칙이 바뀌었다** | **`NATURAL JOIN` 의 결과가 조용히 바뀐다** |

**똑같은 구조다** — 양식이 바뀌면 "알아서 맞춰라"의 뜻도 바뀐다. 그런데 **지시서(질의)는 한 글자도 안 바뀐다.**\
그래서 무엇이 바뀌었는지 **코드 리뷰로는 못 잡는다.**

> **`USING` 절** — 양쪽에 같은 이름으로 있는 열을 지목해 조인 조건으로 삼는 축약형. **공통 열은 결과에서 하나로 합쳐진다.**\
> 예: `JOIN d USING (dept_id)` 는 `ON e.dept_id = d.dept_id` 와 같은 행을 주지만 **열 목록이 다르다.**

> **`NATURAL JOIN`** — 양쪽에 **이름이 같은 열 전부**를 자동으로 조인 조건으로 삼는 조인.\
> 예: `emp NATURAL JOIN dept` 는 `id` 와 `name` **둘 다**로 붙어 0행이 된다.

## 이 주제가 답하려는 질문

1. **`USING` 은 `ON` 과 무엇이 다른가?** — 행은 같은데 **열**이 다르다. 그 차이가 어디서 드러나나.
2. **`NATURAL JOIN` 이 왜 위험한가?** — [13번](../13-inner-join/)이 보인 0행이 **왜** 나왔나.
3. **열을 하나 추가하면 무슨 일이 일어나나?** — 질의를 안 고쳤는데 결과가 바뀌는 것을 실측으로.

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

★ **이 두 표가 이 주제의 실험 장치다.**

```text
 emp 의 열 :  id   name   dept_id   salary
 dept 의 열:  id   name
              ↑     ↑
        이름이 겹치는 열이 둘 — 그런데 의미는 전혀 다르다

   emp.id   = 사원 번호 (1~4)        dept.id   = 부서 번호 (10~30)
   emp.name = 사람 이름              dept.name = 부서 이름
```

**진짜로 붙여야 할 짝(`emp.dept_id` ↔ `dept.id`)은 이름이 다르고, 이름이 같은 두 쌍은 붙이면 안 된다.**\
`USING`·`NATURAL` 이 **정확히 반대로 동작하는** 표본이다.

`USING` 이 제대로 도는 모습을 보려면 이름을 맞춰 줘야 한다. 그래서 아래에서는 `dept` 를 **파생 테이블로 한 번 감싸** 이름만 바꿔 쓴다 — **`dept` 자체는 건드리지 않는다.**

```text
(SELECT id AS dept_id, name AS dept_name FROM dept)  AS d

 d 의 열: dept_id   dept_name
          ↑
   이제 emp.dept_id 와 이름이 같다
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

### 1. `USING` 은 **행이 아니라 열**을 바꾼다

**언제 쓰나** — 양쪽 열 이름이 같을 때. `ON a.x = b.x` 를 `USING (x)` 로 줄인다.

```text
 ON 으로 붙이면                       USING 으로 붙이면
 +---------------------------+       +---------------------------+
 | 두 열이 그대로 둘 다 남는다 |       | 두 열이 하나로 합쳐진다     |
 | … dept_id | dept_id …     |       | dept_id  (맨 앞으로 간다)  |
 +---------------------------+       +---------------------------+
   같은 값이 두 번 찍힌다               한 번만 찍힌다
```

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

| | `ON` | `USING` |
|---|---|---|
| 행 수 | 3 | **3 — 같다** |
| 열 수 | 6 | **5 — `dept_id` 가 하나로 합쳐졌다** |
| 합쳐진 열의 자리 | — | **맨 앞** |

그림 해설 — **두 엔진이 열 개수도 열 순서도 똑같이 바꿨다.** 이것은 취향이 아니라 규칙이다.\
비용 — `SELECT *` 를 쓰는 코드에서는 **열 목록이 달라진다.** 인덱스로 열을 읽는 클라이언트라면 여기서 깨진다.

---

### 2. 합쳐진 열은 **모호하지 않다** — 그것이 `USING` 의 값이다

**언제 쓰나** — 조인 뒤에 공통 열을 한정자 없이 쓰고 싶을 때.

`ON` 으로 붙이면 같은 이름의 열이 둘이라 **한정자 없이는 못 부른다.**

```text
### SQL: SELECT dept_id FROM emp e JOIN (SELECT id AS dept_id, name AS dept_name FROM dept) d
         ON e.dept_id = d.dept_id;
--- PG 18.6 ---
ERROR:  column reference "dept_id" is ambiguous
LINE 1: SELECT dept_id FROM emp e JOIN (SELECT id AS dept_id, name A...
               ^
--- MySQL 8.4.10 ---
ERROR 1052 (23000) at line 1: Column 'dept_id' in field list is ambiguous
```

`USING` 으로 붙이면 **열이 하나뿐이라 모호할 것이 없다.** 한정자를 붙여 양쪽을 따로 볼 수도 있다.

```text
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

그림 해설 — **합쳐진 열은 「양쪽 값이 같은 칸」이라서 셋이 같다.** 내부 조인에서는 당연하다.\
비용 — 없다. **`USING` 이 `ON` 보다 나은 자리가 정확히 여기다.**

---

### 3. 외부 조인에서 합쳐진 열은 **`COALESCE` 처럼** 동작한다

**언제 쓰나** — `LEFT`/`RIGHT JOIN` 에 `USING` 을 쓸 때. **여기서 `ON` 과 결과가 진짜로 달라진다.**

```text
 RIGHT JOIN 에서 짝 없는 행 (hr, dept_id=30)

 ON 으로 붙이면              USING 으로 붙이면
 e.dept_id = NULL            dept_id = 30        <- 합쳐진 칸에는 있는 쪽 값이 들어간다
 d.dept_id = 30
```

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

그림 해설 — **마지막 줄을 보라.** `from_e` 는 `NULL` 인데 합쳐진 `dept_id` 는 **30** 이다.\
합쳐진 열은 "왼쪽 값"도 "오른쪽 값"도 아니라 「**있는 쪽 값**」이다.\
비용 — `SELECT *` 만 보면 짝이 없었다는 사실이 **안 보인다.** `hr` 행의 `dept_id` 가 30 으로 멀쩡히 찍힌다.\
짝 유무를 알려면 **한정자 붙인 열**(`e.dept_id IS NULL`)을 봐야 한다([19번](../19-semi-anti-join/)의 안티 조인이 정확히 그것이다).

★ **`ON` 이었다면 열이 둘이라 한쪽이 `NULL` 인 게 바로 보인다.** `USING` 은 그것을 덮는다.

---

### 4. `USING` 은 **없는 열을 지목하면 시끄럽게 막는다**

**언제 쓰나** — 한쪽에만 있는 이름을 `USING` 에 적었을 때.

```text
### SQL: SELECT * FROM emp e JOIN dept d USING (dept_id);
--- PG 18.6 ---
ERROR:  column "dept_id" specified in USING clause does not exist in right table
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'dept_id' in 'from clause'
```

**`dept` 에는 `dept_id` 열이 없다.** 두 엔진 다 즉시 거부한다.

그림 해설 — **`USING` 은 내가 이름을 적기 때문에 오타·스키마 변경이 에러로 드러난다.**\
비용 — 없다. **이것이 다음 절의 `NATURAL JOIN` 과 갈리는 결정적 지점이다** — `NATURAL` 은 이름을 안 적으므로 **막아 줄 근거 자체가 없다.**

---

### 5. `NATURAL JOIN` 이 **왜** 0행인가 — 13편의 결과를 파고든다

**언제 쓰나** — "이름이 같으니 알아서 붙겠지"라고 쓸 때.

[13번](../13-inner-join/)에서 이 출력을 이미 봤다. **여기서는 그 이유를 판다.**

```text
### SQL: SELECT COUNT(*) AS n FROM emp NATURAL JOIN dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 0                               +---+
(1 row)                          | 0 |
                                 +---+
```

```text
 엔진이 한 일

 1) 양쪽 열 이름을 모은다
      emp  : id, name, dept_id, salary
      dept : id, name
 2) 겹치는 이름을 전부 고른다
      id, name           <- 둘 다 겹친다
 3) 그것을 AND 로 이어 조인 조건을 만든다
      ON emp.id = dept.id AND emp.name = dept.name
 4) 돌린다
      emp.id 는 1~4, dept.id 는 10~30        -> 겹치는 값이 없다
      게다가 name 까지 같아야 한다
 5) 0행
```

★ **의도했던 `emp.dept_id` 는 조건에 들어가지도 않았다.** 이름이 안 겹치기 때문이다.

**`NATURAL LEFT JOIN` 으로 바꾸면 더 나쁘다.**

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

```text
 이 결과는                      실제로는
 SELECT * FROM emp 과           아무것도 안 붙은 것이다
 한 글자도 다르지 않다           (dept 의 열은 전부 공통 열로 합쳐져 사라졌다)
        ↑
  "부서명을 붙였다"고 믿고 이 결과를 쓰면 아무도 못 알아챈다
```

그림 해설 — `dept` 의 열이 `id`·`name` 둘뿐인데 **둘 다 공통 열로 합쳐졌다.** 그래서 오른쪽 표가 결과에 **흔적조차 없다.**\
비용 — **0행은 그나마 눈에 띈다. 4행이 나오는 이 경우가 훨씬 위험하다.**

---

### 6. **열 하나를 추가했더니 결과가 바뀐다** — 질의는 그대로인데

**언제 쓰나** — `NATURAL JOIN` 을 쓴 코드가 있고, 누군가 표에 열을 하나 추가했을 때. **이것이 이 주제의 중심이다.**

이름이 안 겹치게 만든 표 `deptx` 를 두고, **질의를 고정한 채 열만 하나 추가**한다.

<details>
<summary>확인용 표 — 기존 dept 에서 만들고 롤백했다 (PostgreSQL)</summary>

```sql
BEGIN;
CREATE TABLE deptx (dept_id int PRIMARY KEY, dept_name text);
INSERT INTO deptx SELECT id, name FROM dept;      -- dept 는 읽기만 한다
SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;  -- (전)
ALTER TABLE deptx ADD COLUMN name text;            -- 열 하나 추가
SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;  -- (후) — 질의는 한 글자도 안 바뀌었다
ROLLBACK;
```

MySQL 은 DDL 에 트랜잭션이 안 걸리므로 `CREATE` → 질의 → `DROP TABLE deptx` 로 확인했다.\
**두 DB 모두 실험 뒤 표가 남아 있지 않다.**

</details>

```text
 (전) deptx 의 열 = dept_id, dept_name       (후) deptx 의 열 = dept_id, dept_name, name
 emp 와 겹치는 이름: dept_id                  emp 와 겹치는 이름: dept_id, name
        ↓                                            ↓
 ON emp.dept_id = deptx.dept_id              ON emp.dept_id = deptx.dept_id
                                                AND emp.name = deptx.name      <- 늘었다
        ↓                                            ↓
       3행                                          0행
```

```text
### SQL: (전) SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 3                               +---+
(1 row)                          | 3 |
                                 +---+

### SQL: (후) ALTER TABLE deptx ADD COLUMN name …;  뒤에 같은 문을 다시
         SELECT COUNT(*) AS n FROM emp NATURAL JOIN deptx;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 0                               +---+
(1 row)                          | 0 |
                                 +---+
```

그림 해설 — **질의는 한 글자도 안 바뀌었다.** 바뀐 것은 다른 사람이 다른 파일에서 한 `ALTER TABLE` 하나다.\
비용 — **코드 리뷰·테스트 diff 어디에도 안 나온다.** 배포된 질의 문자열이 같으므로 "이 질의는 안 건드렸다"가 사실이면서 결과는 틀린다.

★ **이것이 「조용히 깨진다」의 정확한 뜻이다** — 깨지는 지점과 원인이 **다른 파일, 다른 사람, 다른 시점**에 있다.

**`USING` 으로 쓰면 어떻게 되나 — 같은 `deptx` 에 같은 순서로 손을 대 봤다.**

```text
### SQL: SELECT COUNT(*) AS n FROM emp JOIN deptx USING (dept_id);   -- (전)
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
 NATURAL JOIN        3  ->  0        조용히 바뀐다
 USING (dept_id)     3  ->  3        불변
                        ->  ERROR    지목한 열이 사라지면 시끄럽게 터진다
        ↑
  내가 이름을 적었기 때문에, 스키마 변경이 "불변" 아니면 "에러"로 나온다
```

---

### 7. 공통 열이 **하나도 없으면** `NATURAL JOIN` 은 카티션곱이 된다

**언제 쓰나** — 이름이 겹치지 않는 두 표에 `NATURAL JOIN` 을 쓸 때. **가장 조용한 형태다.**

```text
### SQL: SELECT COUNT(*) AS n FROM emp NATURAL JOIN (SELECT id AS d_id, name AS d_name FROM dept) x;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +----+
----                             | n  |
 12                              +----+
(1 row)                          | 12 |
                                 +----+
```

```text
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

```text
 공통 열이 없다
        ↓
 조인 조건을 만들 재료가 없다
        ↓
 조건 없는 조인 = 카티션곱        <- 12번 주제
        ↓
 4 x 3 = 12행이 조용히 나온다
```

그림 해설 — **`NATURAL JOIN` 은 공통 열이 없어도 에러를 내지 않는다.** 조건이 빈 조인이 될 뿐이다.\
비용 — [13번](../13-inner-join/)에서 본 **MySQL 의 `JOIN … ON` 누락**과 같은 사고인데, **이쪽은 PG 에서도 막히지 않는다.**

```text
 조건 없는 조인이 카티션곱이 되는 세 경로

 (A) CROSS JOIN               -> 의도한 것이다                   12번
 (B) MySQL 의 JOIN … ON 누락  -> PG 는 구문 오류로 막는다        13번
 (C) 공통 열 없는 NATURAL     -> 두 엔진 다 안 막는다   <- 여기
```

★ **(C) 가 셋 중 가장 조용하다.**

---

### 8. `USING` 으로도 이름만 같고 뜻이 다른 열을 지목할 수 있다

**언제 쓰나** — `USING` 이 안전장치라고 과신할 때. **지목이 틀리면 `USING` 도 똑같이 조용하다.**

```text
### SQL: SELECT * FROM emp e JOIN dept d USING (id, name) ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary    (빈 결과 — 출력이 한 줄도 없다)
----+------+---------+--------
(0 rows)
```

**열이 넷뿐이다.** `dept` 의 `id`·`name` 이 둘 다 합쳐져 사라졌다 — `NATURAL JOIN` 과 같은 모양이다.

그림 해설 — **`USING (id, name)` 은 `emp NATURAL JOIN dept` 를 손으로 쓴 것**이다. 결과도 0행으로 같다.\
비용 — `USING` 의 안전은 "**엔진이 고르지 않는다**"에서 오지, "**내가 고른 것이 옳다**"를 보장하지는 않는다.

★ **`USING` 이 막아 주는 것은 「스키마가 바뀌어 조건이 달라지는 것」이지 「내가 틀린 열을 고른 것」이 아니다.**

## 문법 — 어느 절에서 무엇이 보이나

```sql
FROM 왼쪽 JOIN 오른쪽 ON 왼쪽.a = 오른쪽.b     -- 다 적는다. 열은 둘 다 남는다
FROM 왼쪽 JOIN 오른쪽 USING (a)                -- 이름이 같을 때. a 가 하나로 합쳐진다
FROM 왼쪽 JOIN 오른쪽 USING (a, b)             -- 여러 개 지목 가능
FROM 왼쪽 NATURAL JOIN 오른쪽                  -- 겹치는 이름 전부. 조건을 적지 않는다
FROM 왼쪽 NATURAL LEFT JOIN 오른쪽             -- 외부 조인과도 조합된다
```

규칙 일곱.

1. **`USING` 은 행을 안 바꾸고 열을 바꾼다.** 공통 열이 **하나로 합쳐져 맨 앞**에 온다.
2. **합쳐진 열은 모호하지 않다.** `ON` 이었으면 `ambiguous` 가 날 자리에서 그냥 쓸 수 있다.
3. **외부 조인에서 합쳐진 열은 「있는 쪽 값**」이다. 짝이 없었다는 사실이 그 열에는 안 남는다.
4. **`USING` 에 없는 열을 적으면 에러**다. 두 엔진 다 즉시 막는다.
5. **`NATURAL` 은 겹치는 이름 전부로 붙는다.** 의도한 열이 들어간다는 보장이 없다.
6. **공통 열이 없으면 `NATURAL` 은 카티션곱**이다. 에러가 아니다.
7. **`USING (겹치는 이름 전부)` 는 `NATURAL JOIN` 과 같다.** `USING` 의 안전은 지목의 **고정**에서 오지 지목의 **정확성**에서 오지 않는다.

읽을 때 붙잡을 것은 **"조인 조건이 어디에 적혀 있나"** 하나다.

```text
 ON      -> 질의에 다 적혀 있다        스키마가 바뀌어도 조건은 그대로
 USING   -> 질의에 이름이 적혀 있다    이름이 사라지면 에러로 드러난다
 NATURAL -> 질의에 아무것도 없다       조건은 그때그때 스키마가 정한다   <- 위험의 근원
```

## 어디서 틀리나

- **`NATURAL JOIN` 으로 짧게 쓴다.**\
  `emp NATURAL JOIN dept` 는 `id` 와 `name` **둘 다**로 붙어 **0행**이다. 의도한 `dept_id` 는 조건에 없다.
- **`NATURAL LEFT JOIN` 으로 "안전하게" 쓴다.**\
  4행이 나오는데 **`SELECT * FROM emp` 와 똑같다.** 오른쪽 표가 통째로 없는 것을 아무도 못 알아챈다.
- **공통 열이 없는 두 표에 `NATURAL` 을 쓴다.**\
  **12행 카티션곱**이 조용히 나온다. 두 엔진 다 안 막는다.
- **열을 추가하고 `NATURAL JOIN` 을 쓴 질의를 확인 안 한다.**\
  3행이 0행이 됐다. **질의는 한 글자도 안 바뀌었다.**
- **`SELECT *` 를 `ON` 에서 `USING` 으로 바꾼다.**\
  행은 같지만 **열 개수와 순서가 바뀐다.** 열 위치로 값을 읽는 클라이언트가 깨진다.
- **외부 조인 + `USING` 에서 합쳐진 열로 짝 유무를 판단한다.**\
  `hr` 의 `dept_id` 가 30 으로 찍힌다. **짝이 없었다는 사실은 한정자 붙인 열에만 남는다.**
- **`USING` 이 무조건 안전하다고 생각한다.**\
  `USING (id, name)` 은 `NATURAL JOIN` 을 손으로 쓴 것이고 결과도 0행으로 같다.
- **`USING` 과 `ON` 에서 같은 이름의 열을 헷갈린다.**\
  `ON` 에서는 `SELECT dept_id` 가 `ambiguous` 에러이고, `USING` 에서는 통과한다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `USING` 이 공통 열을 하나로 합친다 | **결과의 정의** | 언어 — 두 엔진이 열 개수·순서까지 같았다 |
| 합쳐진 열이 맨 앞에 온다 | **결과의 정의** | 언어 — 두 엔진이 같았다 |
| 외부 조인에서 합쳐진 열이 「있는 쪽 값」 | **결과의 정의** | 언어 — 두 엔진이 같았다 |
| `NATURAL` 이 겹치는 이름 **전부**로 붙는다 | **결과의 정의** | 언어 |
| 공통 열이 없을 때 카티션곱 | **결과의 정의** | 언어 — 조건이 빈 조인이 되는 것 |
| **그래서 지금 무엇으로 붙는가** | **현재 스키마** | **아무도** — 다음 `ALTER TABLE` 이 바꾼다 |
| 에러 문구 | 그 엔진의 표기 | 다르다 — PG 는 `USING clause does not exist in right table`, MySQL 은 `Unknown column … in 'from clause'` |

- ★ **`NATURAL JOIN` 의 「결과」는 언어가 보장하지만 「무엇으로 붙는지」는 스키마가 정한다.**\
  이 구분이 이 주제의 핵심이다 — **동작은 완벽하게 정의돼 있는데 결과는 예측할 수 없다.**
- **결과의 순서는 보장되지 않는다.** 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.
- `USING` 의 열 합치기는 **투영(projection) 규칙**이지 저장 형태와 무관하다. 두 표의 물리 구조는 그대로다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — `USING`, 양쪽 열 이름이 같고 그것이 의미적으로도 같은 열일 때.** `orders JOIN order_items USING (order_id)`.
- **쓴다 — `USING`, 조인 뒤 공통 열을 한정자 없이 여러 번 쓸 때.** `ambiguous` 를 피할 수 있다.
- **안 쓴다 — `NATURAL JOIN`, 언제나.** 이 주제의 결론이다.\
  짧아지는 것은 몇 글자인데, 대가는 **스키마 변경에 조용히 깨지는 질의**다.
- **안 쓴다 — `USING`, 외부 조인에서 짝 유무를 봐야 할 때.** 합쳐진 열이 그 정보를 덮는다.
- **안 쓴다 — `USING`, `SELECT *` 를 열 위치로 읽는 코드가 있을 때.** 열 개수·순서가 바뀐다.
- **주의 — 이름은 같은데 뜻이 다른 열.** `emp.id` 와 `dept.id` 가 그렇다. **`USING` 도 이 실수는 못 막는다.**

## 핵심 문장

- **`USING` 은 행이 아니라 열을 바꾼다** — 공통 열이 하나로 합쳐지고 맨 앞으로 간다. 행 수는 `ON` 과 같다.
- **합쳐진 열은 모호하지 않다.** `ON` 이면 `ambiguous` 가 날 자리에서 `USING` 은 통과한다.
- **외부 조인에서 합쳐진 열은 「있는 쪽 값**」이다 — `hr` 의 `dept_id` 가 30 으로 찍혀 **짝이 없었다는 사실을 덮는다.**
- **`NATURAL JOIN` 은 겹치는 이름 전부로 붙는다.** `emp NATURAL JOIN dept` 가 0행인 것은 `id` 와 `name` **둘 다**로 붙었기 때문이다.
- **공통 열이 없으면 `NATURAL` 은 카티션곱**이다. 조건 없는 조인이 되는 세 경로 중 **가장 조용하다.**
- **열 하나를 추가하면 결과가 3행에서 0행이 된다.** 질의는 한 글자도 안 바뀐 채로.
- **`USING` 의 안전은 지목을 고정하는 데서 온다.** `USING (id, name)` 처럼 틀리게 지목하면 `NATURAL` 과 똑같이 조용하다.

## 관련 자료

- [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) — `USING`·`NATURAL` 의 열 합치기 규칙이 여기 있다.
- [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html) — 같은 규칙을 같은 페이지에서 다룬다.
- [13 INNER JOIN](../13-inner-join/) — **경계: 그쪽은 「`NATURAL JOIN` 이 조용히 0행을 준다」는 사실까지, 여기는 왜 그렇게 됐는지와 스키마 변경 위험부터.**
- [12 카티션곱과 CROSS JOIN](../12-cartesian-product-cross-join/) — 공통 열이 없을 때 나오는 12행의 정본.
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — 3번 절의 `RIGHT JOIN` 이 무엇을 남기나.
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — **경계: 그쪽은 이름이 겹칠 때의 `ambiguous` 까지, 여기는 그 겹침을 `USING` 이 어떻게 없애나부터.**
- [19 세미·안티 조인](../19-semi-anti-join/) — 짝 유무를 제대로 보는 형태.
- [02 SELECT 목록과 열 별칭의 유효 범위](../02-select-list-column-aliases/) — **경계: 그쪽은 `SELECT` 목록과 별칭의 규칙까지, 여기는 조인이 그 목록을 어떻게 바꾸나부터.**
- **스키마 변경(`ALTER TABLE`)** 자체는 [목록의 **42번 주제**](../42-create-alter-drop-table/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **`USING` 절** — 양쪽에 같은 이름으로 있는 열을 지목해 조인 조건으로 삼는 축약형. 그 열은 결과에서 하나로 합쳐진다.\
  예: `JOIN d USING (dept_id)` — 행은 `ON` 과 같고 열이 하나 줄어든다.
- **`NATURAL JOIN`** — 겹치는 이름의 열 **전부**를 자동으로 조인 조건으로 삼는 조인.\
  예: `emp NATURAL JOIN dept` 는 `id` 와 `name` 둘 다로 붙어 0행이다.
- **공통 열(common column)** — 양쪽에 같은 이름으로 있는 열. `USING`/`NATURAL` 이 하나로 합친다.\
  예: `dept_id` — 합쳐진 뒤 결과 맨 앞에 온다.
- **열 합치기(column merging)** — 두 열을 결과에서 한 칸으로 내보내는 것. 외부 조인에서는 「있는 쪽 값」이 들어간다.\
  예: `hr` 행의 `dept_id` 가 30 — 왼쪽은 `NULL` 인데도.
- **모호한 열 참조(ambiguous column reference)** — 같은 이름의 열이 둘이라 어느 것인지 정할 수 없는 상태.\
  예: `ON` 으로 붙인 뒤 `SELECT dept_id` — 두 엔진 다 에러다.
- **카티션곱(Cartesian product)** — 조건 없이 모든 짝을 만든 결과.\
  예: 공통 열이 없는 `NATURAL JOIN` 이 12행을 냈다. [목록의 **12번 주제**](../12-cartesian-product-cross-join/).
- **스키마 변경(schema change)** — 열 추가·삭제·이름 변경처럼 표의 구조를 바꾸는 것.\
  예: `ALTER TABLE deptx ADD COLUMN name` — 이것 하나로 3행이 0행이 됐다.
- **silent failure(무음 실패)** — 에러 없이 틀린 값이 나오는 실패.\
  예: `NATURAL LEFT JOIN` 이 `SELECT * FROM emp` 과 똑같은 4행을 준 것.
- **투영(projection)** — 결과에 어느 열을 어떤 순서로 내보낼지 정하는 것.\
  예: `USING` 은 조건이 아니라 투영을 바꾼다 — 행이 아니라 열이 달라지는 이유다.

## 더 들어가면

- **`SELECT *` 를 쓰지 않으면 `USING` 의 열 합치기 효과가 대부분 사라진다.** 필요한 열을 적어 쓰는 코드에서는 `ON` 과 `USING` 의 실질 차이가 「모호성 해소」 하나로 줄어든다.
- **`NATURAL JOIN` 을 막는 도구가 있다** — 대부분의 SQL 린터가 기본 경고 규칙으로 잡는다. 스키마 변경으로 깨지는 성질이라 **코드 리뷰로는 못 잡기 때문**이다.
- **이름 규칙이 `NATURAL JOIN` 의 안전을 정한다.** 모든 표가 자기 기본키를 `id` 로 부르는 규칙이면 `NATURAL JOIN` 은 거의 항상 틀린다 — `emp.id`·`dept.id` 가 그 예다.
