# sql/14-LEFT·RIGHT OUTER JOIN — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions (Joined Tables)](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `LEFT`·`RIGHT [OUTER] JOIN` 은 두 엔진 모두 오래전부터 있고, **이 주제에서 갈리는 것은 없다.** 아래 모든 출력이 양쪽에서 같았다.\
> **선행** — [13 INNER JOIN](../13-inner-join/). **13번이 버린 행을 되살리는 것이 이 주제다.**\
> **뒤 주제** — [15 ON 과 WHERE 의 차이](../15-on-vs-where-in-outer-join/)(같은 조건의 자리가 여기서 결과를 바꾼다) · [16 FULL OUTER JOIN](../16-full-outer-join/)(양쪽 다 되살린다).

## 한눈에 — 쉽게 말하면

**`LEFT JOIN` = 「왼쪽 명단은 한 명도 빼지 않는다」는 약속. 짝을 못 찾은 사람은 오른쪽 칸을 빈칸으로 둔 채 남는다.**

- 출석부(왼쪽)에 회비 납부 기록(오른쪽)을 붙인다고 하자.
- **`INNER JOIN`** — 「왔고 냈다」인 사람만. 안 낸 사람은 **출석부에서도 사라진다.** 이건 이상하다.
- **`LEFT JOIN`** — **출석부 전원이 남는다.** 안 낸 사람의 납부란만 빈칸이 된다.
- 그 빈칸이 SQL 의 `NULL` 이다. 그리고 **그 `NULL` 이 다음 사고의 씨앗이다.**

```text
13번이 버린 것을 14번이 되살린다

 카티션곱 12행 ──ON──> INNER 3행
                          │
                          ├── + 짝 못 찾은 왼쪽(dan)을 NULL 로 되살림 ──> LEFT  4행
                          ├── + 짝 못 찾은 오른쪽(hr)을 NULL 로 되살림 ──> RIGHT 4행
                          └── + 양쪽 다 되살림 ────────────────────────> FULL  5행  (16번)
```

이 출석부가 **똑같은 구조로** 외부 조인이다.\
그런데 ★ **되살린 행에는 `NULL` 이 들어 있다.** 그 순간 [04번](../04-null-three-valued-logic/)의 3값 논리가 **조인 결과 위에서 되살아난다** — 아래 4번이 이 주제의 중심이다.

> **외부 조인(outer join)** — 짝 못 찾은 행을 버리지 않고 **반대쪽 열을 전부 `NULL` 로 채워** 남기는 조인.\
> 예: `dan` 은 부서가 없어도 `LEFT JOIN` 결과에 남고 `dept` 쪽 열이 전부 `NULL` 이 된다.

> **보존 측(preserved side)** — 「한 행도 안 버린다」고 약속된 쪽.\
> 예: `A LEFT JOIN B` 의 보존 측은 `A`. `A RIGHT JOIN B` 의 보존 측은 `B`.

## 이 주제가 답하려는 질문

1. **`LEFT JOIN` 이 무엇을 보장하나?** — 왼쪽 행 수의 하한이다. 그리고 그 보장이 언제 깨지나.
2. **조인이 만든 `NULL` 과 원래 있던 `NULL` 을 구분할 수 있나?** — 값만 봐서는 못 한다.
3. **`RIGHT JOIN` 은 왜 실무에서 덜 쓰이나?** — 뒤집으면 같은 것인데 읽는 순서가 어긋난다.

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

**이 두 표가 외부 조인을 설명하기에 딱 맞다** — 왼쪽에만 있는 행(`dan`)과 오른쪽에만 있는 행(`hr`)이 하나씩 있다.\
`dan` 은 `LEFT JOIN` 이 되살리고 `hr` 은 `RIGHT JOIN` 이 되살린다. 둘 다 되살리는 것이 [16번](../16-full-outer-join/)이다.

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

### 1. `LEFT JOIN` — 왼쪽을 다 남기고 빈칸을 `NULL` 로 채운다

**언제 쓰나** — 「기준이 되는 표」가 분명하고 그 표의 행을 하나도 잃으면 안 될 때. 실무 조회의 절반이 이것이다.

```text
(전) INNER JOIN 3행                   (후) LEFT JOIN 4행
+-----+-------+                       +-----+-------+
| ann | sales |                       | ann | sales |
| bob | sales |                       | bob | sales |
| cho | dev   |                       | cho | dev   |
+-----+-------+                       | dan | NULL  |   <- 되살아났다
   dan 이 없다                        +-----+-------+
                                         오른쪽 열이 전부 NULL 로 채워진다
```

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT OUTER JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
 dan | NULL                      | cho | dev   |
(4 rows)                         | dan | NULL  |
                                 +-----+-------+
```

**채워지는 것은 한 열이 아니라 오른쪽 열 전부다.** `dept` 의 열을 둘 다 뽑아 보면 보인다.

```text
### SQL: SELECT e.name AS emp, d.id AS d_id, d.name AS dept
         FROM emp e LEFT JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | d_id | dept               +-----+------+-------+
-----+------+-------             | emp | d_id | dept  |
 ann |   10 | sales              +-----+------+-------+
 bob |   10 | sales              | ann |   10 | sales |
 cho |   20 | dev                | bob |   10 | sales |
 dan | NULL | NULL               | cho |   20 | dev   |
(4 rows)                         | dan | NULL | NULL  |
                                 +-----+------+-------+
```

그림 해설 — `dan` 행의 `d_id` 와 `dept` 가 **둘 다** `NULL` 이다. **일부만 채워지는 일은 없다.**\
대가 — 결과에 `NULL` 이 들어온다. 그 `NULL` 은 **원본 데이터의 `NULL` 과 구분되지 않는다**(3번) 그리고 **뒤에 오는 조건을 망가뜨린다**(4번).

★ **`LEFT JOIN` 이 보장하는 것은 행 수의 하한이다** — 결과 행 수 ≥ 왼쪽 행 수. 4행 이상이다.\
`INNER` 였다면 3행, 즉 **보장이 없다.** 이 한 줄이 `LEFT` 를 쓰는 이유 전부다.

---

### 2. `RIGHT JOIN` 은 `LEFT` 를 뒤집은 것이다

**언제 쓰나** — 기준 표가 `FROM` 의 오른쪽에 적혀 있을 때. 그리고 **대개는 안 쓴다**(아래).

```text
LEFT — 왼쪽을 보존                    RIGHT — 오른쪽을 보존
 emp  LEFT JOIN dept                  emp  RIGHT JOIN dept
   dan 이 남는다 (왼쪽만 있는 행)        hr 이 남는다 (오른쪽만 있는 행)
       4행                                  4행
```

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e RIGHT OUTER JOIN dept d ON e.dept_id = d.id ORDER BY d.id, e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp  | dept                     +------+-------+
------+-------                   | emp  | dept  |
 ann  | sales                    +------+-------+
 bob  | sales                    | ann  | sales |
 cho  | dev                      | bob  | sales |
 NULL | hr                       | cho  | dev   |
(4 rows)                         | NULL | hr    |
                                 +------+-------+
```

**표의 순서를 바꾸면 `RIGHT` 가 `LEFT` 와 같은 답을 낸다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM dept d RIGHT JOIN emp e ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
 dan | NULL                      | cho | dev   |
(4 rows)                         | dan | NULL  |
                                 +-----+-------+
```

두 그림의 결론 — **`A LEFT JOIN B` 와 `B RIGHT JOIN A` 는 같은 결과다.** 열 순서만 내가 `SELECT` 에서 정한다.\
대가 — **읽는 순서가 어긋난다.** `FROM dept d RIGHT JOIN emp e` 는 「`dept` 를 읽다가 사실은 `emp` 가 기준이었구나」로 되짚게 만든다.

★ **실무에서 `RIGHT` 를 덜 쓰는 이유가 이것이다** — 문법이 나쁜 게 아니라 **읽는 방향이 뒤집히기** 때문이다.\
기준 표를 `FROM` 바로 뒤에 놓고 `LEFT` 로 쓰면, 질의가 「무엇의 목록인가」를 첫 줄에서 말한다.\
조인이 셋 넷으로 늘면 차이가 커진다 — `LEFT` 만 쓰면 기준이 계속 첫 표이고, `RIGHT` 가 섞이면 매번 어느 쪽이 보존 측인지 따져야 한다.

---

### 3. 결과의 `NULL` 은 어느 쪽에서 왔는가

**언제 쓰나** — 외부 조인 결과를 읽을 때마다. 이 주제가 [04번](../04-null-three-valued-logic/)에 걸리는 첫 자리다.

```text
LEFT JOIN 결과 4행에서 NULL 이 있는 자리

 emp | e_dept | d_id | dept    의미
-----+--------+------+-------  ----------------------------------------
 ann |     10 |   10 | sales   짝을 찾았다
 bob |     10 |   10 | sales   짝을 찾았다
 cho |     20 |   20 | dev     짝을 찾았다
 dan |   NULL | NULL | NULL    왼쪽 e_dept 는 원래부터 NULL (데이터)
                               오른쪽 d_id·dept 는 조인이 만든 NULL
```

**두 `NULL` 이 화면에서 똑같이 보인다.** 그래서 「짝을 못 찾았나」를 판정할 때는 **`NULL` 일 수 없는 열**을 봐야 한다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.id IS NULL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+------+
-----+------                     | emp | dept |
 dan | NULL                      +-----+------+
(1 row)                          | dan | NULL |
                                 +-----+------+
```

그림 해설 — `d.id` 는 `dept` 의 **기본키**라 원본에 `NULL` 이 절대 없다.\
**그러므로 여기가 `NULL` 이면 그건 조인이 만든 것** — 즉 짝을 못 찾은 행이다. 이것이 반조인의 표준 형태다.\
대가 — `d.name` 처럼 `NULL` 이 들어갈 수 있는 열로 판정하면 **「짝이 없다」와 「부서명이 원래 `NULL` 이다」를 구분하지 못한다.**

`COUNT` 로도 같은 함정이 나온다. **기준 표를 보존하면 「0건」이 「1행」으로 세어진다.**

```text
### SQL: SELECT d.name AS dept, COUNT(*) AS star, COUNT(e.id) AS emp_cnt
         FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | star | emp_cnt          +-------+------+---------+
-------+------+---------         | dept  | star | emp_cnt |
 sales |    2 |       2          +-------+------+---------+
 dev   |    1 |       1          | sales |    2 |       2 |
 hr    |    1 |       0          | dev   |    1 |       1 |
(3 rows)                         | hr    |    1 |       0 |
                                 +-------+------+---------+
```

`hr` 의 `COUNT(*)` 은 **1**(조인이 만든 행 하나), `COUNT(e.id)` 는 **0**이다.\
★ **외부 조인 뒤의 `COUNT(*)` 은 「몇 건인가」의 답이 아니다.** 보존 측 열이 아니라 **상대 측의 `NULL` 아닌 열**을 세야 한다(목록의 **21번 주제**).

---

### 4. ★ `WHERE` 에 오른쪽 열 조건을 걸면 — 04번이 되살아난다

**언제 쓰나** — `LEFT JOIN` 결과를 더 거를 때. **이 주제에서 가장 많이 일어나는 사고다.**

「10번 부서가 **아닌** 사원」을 뽑으려 한다. 답은 `cho`(20번)와 `dan`(소속 없음) 둘이어야 할 것 같다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.id <> 10 ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+------+
-----+------                     | emp | dept |
 cho | dev                       +-----+------+
(1 row)                          | cho | dev  |
                                 +-----+------+
```

**`dan` 이 사라졌다.** `LEFT JOIN` 으로 애써 되살린 행이 `WHERE` 에서 다시 죽었다.

```text
LEFT JOIN 이 만든 4행이 WHERE d.id <> 10 을 지난다

 emp | d.id |  d.id <> 10  | WHERE 의 처분
-----+------+--------------+---------------
 ann |   10 | FALSE        | 버림
 bob |   10 | FALSE        | 버림
 cho |   20 | TRUE         | 통과
 dan | NULL | UNKNOWN      | 버림    <- 조인이 만든 NULL 이 여기서 일한다
                              ↑
              "모르는 값이 10 이 아닌가?" — 답할 수 없다
```

★ **`dan` 의 `d.id` 는 조인이 만든 `NULL` 이다.** 원본 `dept` 에는 `NULL` 인 `id` 가 없는데도, **조인 결과에는 `NULL` 이 생겼고** 그것이 3값 논리에 걸렸다.\
[04번](../04-null-three-valued-logic/)에서 `WHERE` 가 `UNKNOWN` 행을 버린다고 배운 그 규칙이, **조인이 만들어 낸 `NULL` 위에서 똑같이 작동한다.**

**고치는 법 — `NULL` 인 경우를 명시적으로 허용한다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.id <> 10 OR d.id IS NULL ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+------+
-----+------                     | emp | dept |
 cho | dev                       +-----+------+
 dan | NULL                      | cho | dev  |
(2 rows)                         | dan | NULL |
                                 +-----+------+
```

같은 사고가 **등호 조건**에서는 더 세게 온다. 조건에 맞는 행만 남고 **보존 측 보장이 통째로 사라진다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+
```

**4행이 2행이 됐다.** `LEFT JOIN` 이라고 써 놓고 `INNER JOIN` 결과를 받은 것이다.

```text
      의도                                    실제
 "모든 사원 + 그 중 sales 인 사람의 부서명"     "sales 부서 사원만"
        4행                                     2행
```

**같은 조건을 `ON` 에 두면 4행이 유지된다** — 그 대비가 [15번](../15-on-vs-where-in-outer-join/)의 전부다.\
**경계: 여기는 「`WHERE` 가 보존을 깬다」는 사실과 `IS NULL` 처방까지, `ON` 과 `WHERE` 의 규칙 자체는 15번.**

---

### 5. `LEFT JOIN` 도 행이 늘어난다

**언제 쓰나** — `LEFT JOIN` 뒤에 집계를 씌울 때. 「왼쪽을 다 남긴다」가 「왼쪽 행 수와 같다」는 뜻이 아니다.

```text
LEFT JOIN 이 보장하는 것              보장하지 않는 것
 결과 행 수 >= 왼쪽 행 수              결과 행 수 = 왼쪽 행 수
        ↑                                    ↑
  최소한 한 번은 나온다              오른쪽에 짝이 여럿이면 여러 번 나온다
```

`dept` 를 왼쪽에 두면 바로 보인다 — `sales` 는 사원이 둘이라 **두 줄**이 된다.

```text
### SQL: SELECT d.name AS dept, e.name AS emp FROM dept d LEFT JOIN emp e ON e.dept_id = d.id
         ORDER BY d.id, e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp                     +-------+------+
-------+------                   | dept  | emp  |
 sales | ann                     +-------+------+
 sales | bob                     | sales | ann  |
 dev   | cho                     | sales | bob  |
 hr    | NULL                    | dev   | cho  |
(4 rows)                         | hr    | NULL |
                                 +-------+------+
```

그림 해설 — `dept` 3행이 결과 4행이 됐다. **하나도 안 잃었고(3 ≥ 3), 하나는 늘었다.**\
대가 — [13번](../13-inner-join/)의 팬아웃이 외부 조인에서도 그대로 일어난다. `LEFT` 를 썼다고 `SUM` 이 안전해지지 않는다.\
그래서 **집계 전에 행 수를 센다**는 습관이 여기서도 유효하다(목록의 **25번 주제**).

## 문법 — 어느 절에서 무엇이 보이나

```sql
FROM 왼쪽표 LEFT  [OUTER] JOIN 오른쪽표 ON <조건>   -- 왼쪽 보존
FROM 왼쪽표 RIGHT [OUTER] JOIN 오른쪽표 ON <조건>   -- 오른쪽 보존
```

규칙 여섯.

1. **`OUTER` 는 생략 가능하다.** `LEFT JOIN` = `LEFT OUTER JOIN`.
2. **보존 측 행은 한 행도 안 버려진다** — `ON` 단계에서는. **`WHERE` 는 그 보장을 안 지킨다**(4번).
3. **짝 없는 행의 반대쪽 열은 전부 `NULL`** 이다. 일부만 채워지는 일은 없다.
4. **짝 여부 판정은 `NULL` 일 수 없는 열로 한다** — 보통 기본키. 다른 열은 원본 `NULL` 과 구분이 안 된다.
5. **`A LEFT JOIN B` = `B RIGHT JOIN A`.** 실무에서는 기준 표를 앞에 놓고 `LEFT` 로 통일한다.
6. **결과 행 수 ≥ 보존 측 행 수.** 같다는 뜻이 아니다 — 1:N 이면 는다.

`LEFT JOIN` 의 실전 형태는 사실상 **셋**이다.

```sql
-- (1) 붙이기 — 기준 표를 다 남기고 정보를 덧붙인다
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id;

-- (2) 반조인 — 짝이 없는 것만 고른다 (NULL 일 수 없는 열로 판정)
SELECT e.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE d.id IS NULL;

-- (3) 0 포함 집계 — 건수가 0인 것도 표에 남긴다
SELECT d.name, COUNT(e.id) FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name;
```

## 어디서 틀리나

- **★ `LEFT JOIN` 결과에 `WHERE 오른쪽열 = 값` 을 건다.**\
  가장 흔하다. 4행이 2행이 되고, `LEFT` 가 `INNER` 로 무너진다. 조건을 `ON` 으로 옮긴다([15번](../15-on-vs-where-in-outer-join/)).
- **★ `WHERE 오른쪽열 <> 값` 으로 「아닌 것」을 고른다.**\
  조인이 만든 `NULL` 이 `UNKNOWN` 이 되어 **되살린 행이 다시 죽는다.** `OR 오른쪽열 IS NULL` 을 같이 쓴다.
- **짝 여부를 `NULL` 가능한 열로 판정한다.**\
  `WHERE d.name IS NULL` 은 「짝이 없다」와 「부서명이 원래 `NULL` 이다」를 구분하지 못한다. 기본키를 본다.
- **외부 조인 뒤에 `COUNT(*)` 을 쓴다.**\
  `hr` 의 `COUNT(*)` 이 1 이었다. 0건인데 1로 세어진다. `COUNT(상대측 NULL 아닌 열)` 을 쓴다.
- **`LEFT JOIN` 이면 행 수가 그대로일 거라 믿는다.**\
  1:N 이면 는다. `dept` 3행이 4행이 됐다. 하한 보장이지 등식이 아니다.
- **`RIGHT JOIN` 을 섞어 쓴다.**\
  문법이 나쁜 게 아니라 **읽는 방향이 뒤집힌다.** 조인이 셋 넷이면 보존 측을 매번 따져야 한다.
- **`SELECT *` 로 외부 조인 결과를 본다.**\
  `NULL` 로 채워진 열이 여럿이라 어느 게 데이터고 어느 게 조인 산물인지 화면에서 구분이 안 된다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 보존 측 행이 `ON` 단계에서 안 버려진다 | **결과의 정의** | 언어 — 두 문서가 같은 모양으로 적는다 |
| 짝 없는 행의 반대쪽 열이 **전부** `NULL` 이 된다 | **결과의 정의** | 언어 |
| `A LEFT JOIN B` = `B RIGHT JOIN A` | **결과의 정의** | 언어 |
| 엔진이 `LEFT JOIN` 을 `INNER JOIN` 으로 바꿔 실행한다 | 옵티마이저의 선택 | 결과가 같을 때만 허용된다 — [15번](../15-on-vs-where-in-outer-join/)에 계획이 있다 |
| 결과 **행 순서** | 아무도 보장 안 함 | `ORDER BY` 없이는 어느 엔진도 순서를 약속하지 않는다 |

- **이 주제에서는 두 엔진의 출력이 전부 같았다.** 방언이 갈리는 자리가 없다.\
  갈리는 것은 `FULL OUTER JOIN` 부터이고 그건 [16번](../16-full-outer-join/)이다.
- **행 순서는 예외다.** [16번](../16-full-outer-join/)에서 `RIGHT JOIN` 의 동률 행이 두 엔진에서 다른 순서로 나왔다 — **방언 차이가 아니라 순서 무보장**이다.
- **`WHERE` 가 외부 조인을 내부 조인으로 무너뜨리는 것은 구현이 아니라 정의다.** 옵티마이저가 그걸 알아차려 계획까지 바꾸는 것은 구현이다([15번](../15-on-vs-where-in-outer-join/)).

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 기준 표가 분명할 때.** 「모든 사원 + (있으면) 부서명」. 기준을 `FROM` 바로 뒤에 놓고 `LEFT`.
- **쓴다 — 0건을 표에 남겨야 할 때.** 「부서별 인원수」에서 인원 0인 부서를 보이려면 `dept LEFT JOIN emp` + `COUNT(e.id)`.
- **쓴다 — 반조인.** 「부서가 없는 사원」은 `LEFT JOIN … WHERE d.id IS NULL`.
- **안 쓴다 — 양쪽 다 있는 것만 필요할 때.** 그건 `INNER JOIN` 이다([13번](../13-inner-join/)). 불필요한 `LEFT` 는 옵티마이저에 줄 정보를 가린다.
- **안 쓴다 — 양쪽의 짝 없는 행을 다 봐야 할 때.** 그건 `FULL OUTER JOIN` 이다([16번](../16-full-outer-join/)).
- **`RIGHT` 는 거의 안 쓴다.** 표 순서를 바꿔 `LEFT` 로 적는다. 읽는 방향이 일정해진다.
- **대안을 먼저 본다.** 「짝이 있는지만」 알면 되면 `EXISTS` 가 낫다 — 행이 안 는다(목록의 **19번 주제**).

## 핵심 문장

- `LEFT JOIN` 은 **왼쪽을 다 남기고** 짝 못 찾은 쪽을 **`NULL` 로 채운다.** 채워지는 것은 그쪽 열 **전부**다.
- 보장은 **행 수의 하한**이다 — 결과 ≥ 왼쪽. 1:N 이면 는다. **등식이 아니다.**
- **조인이 만든 `NULL` 과 원본 `NULL` 은 구분되지 않는다.** 짝 여부는 **기본키**로 판정한다.
- ★ **`WHERE` 에 오른쪽 열 조건을 걸면 되살린 행이 다시 죽는다** — `= 값` 이면 `INNER` 로 무너지고, `<> 값` 이면 `UNKNOWN` 에 걸려 사라진다.
- 그 사고의 뿌리가 [04번](../04-null-three-valued-logic/)이다. **3값 논리가 조인 결과 위에서 되살아난다.**
- **`A LEFT JOIN B` = `B RIGHT JOIN A`.** `RIGHT` 를 덜 쓰는 이유는 문법이 아니라 **읽는 방향**이다.
- 외부 조인 뒤의 **`COUNT(*)` 은 건수가 아니다.** `hr` 이 0건인데 1로 세어졌다.

## 관련 자료

- [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) — 조인 형태별 정의.
- [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html) — 외부 조인은 `{LEFT|RIGHT} [OUTER] JOIN` 두 가지다.
- [13 INNER JOIN](../13-inner-join/) — **경계: 그쪽은 어느 행이 버려지나까지, 여기는 그 버려진 행을 되살리는 것부터.**
- [15 OUTER JOIN 에서 ON 과 WHERE 의 차이](../15-on-vs-where-in-outer-join/) — **경계: 여기는 「`WHERE` 가 보존을 깬다」는 사실까지, 두 자리의 규칙과 계획은 거기.**
- [16 FULL OUTER JOIN](../16-full-outer-join/) — **경계: 여기는 한쪽 보존까지, 양쪽 보존과 MySQL 우회는 거기.**
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `UNKNOWN` 의 계산 규칙까지, 여기는 조인이 만든 `NULL` 이 그 규칙에 어떻게 걸리나부터.**
- [12 카티션곱과 CROSS JOIN](../12-cartesian-product-cross-join/) — 12행에서 출발하는 전체 그림.
- **`COUNT` 의 세 형태**는 목록의 **21번 주제**, **`EXISTS`/`NOT EXISTS`** 는 **19번 주제**, **팬아웃 처방**은 **25번 주제**가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **외부 조인(outer join)** — 짝 못 찾은 행을 버리지 않고 반대쪽 열을 `NULL` 로 채워 남기는 조인.\
  예: `dan` 은 부서가 없어도 `LEFT JOIN` 결과에 남는다.
- **보존 측(preserved side)** — 「한 행도 안 버린다」고 약속된 쪽.\
  예: `emp LEFT JOIN dept` 의 보존 측은 `emp`. `WHERE` 는 이 약속을 안 지킨다.
- **`LEFT [OUTER] JOIN`** — 왼쪽 표를 보존하는 외부 조인.\
  예: `emp LEFT JOIN dept` 는 4행 — `dan` 이 `NULL` 과 함께 남는다.
- **`RIGHT [OUTER] JOIN`** — 오른쪽 표를 보존하는 외부 조인. `LEFT` 의 대칭이다.\
  예: `emp RIGHT JOIN dept` 는 4행 — `hr` 이 `NULL` 과 함께 남는다.
- **조인이 만든 `NULL`(join-generated NULL)** — 원본에 없었는데 외부 조인이 채워 넣은 `NULL`.\
  예: `dan` 행의 `d.id`. `dept.id` 는 기본키라 원본에는 `NULL` 이 없다.
- **반조인(anti join)** — 「저쪽에 짝이 없는 행」만 남기는 조인.\
  예: `LEFT JOIN … WHERE d.id IS NULL` 은 부서 없는 사원만 준다.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
  예: `NULL <> 10`. `WHERE` 는 이것을 `FALSE` 와 똑같이 버린다 — 그래서 `dan` 이 사라졌다.
- **팬아웃(fan-out)** — 1:N 조인으로 보존 측 행이 여러 줄로 불어나는 현상.\
  예: `sales` 부서에 사원이 둘이라 `dept LEFT JOIN emp` 에서 두 줄이 됐다.
- **`COUNT(*)` 과 `COUNT(열)`** — 앞은 행을 세고 뒤는 **`NULL` 이 아닌 값**을 센다.\
  예: `hr` 행에서 `COUNT(*)`=1, `COUNT(e.id)`=0.
