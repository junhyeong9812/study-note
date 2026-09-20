# sql/12-카티션곱과 CROSS JOIN — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions (Joined Tables)](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> **버전** — `CROSS JOIN` 자체는 두 엔진 모두 오래전부터 있다. 아래 **`CROSS JOIN … ON`** 의 처리는 갈리는데, 두 매뉴얼에 도입 버전이 없어 **버전은 적지 않는다.**\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/)(조인은 **1번 칸**에서 일어난다) · [10 FROM 절](../10-from-clause-aliases-derived-tables/)(별칭과 파생 테이블).\
> **이 주제는 조인 전체의 밑동이다** — [13 INNER JOIN](../13-inner-join/) · [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) · [16 FULL OUTER JOIN](../16-full-outer-join/) 이 전부 여기서 시작한다.

## 한눈에 — 쉽게 말하면

**카티션곱 = 「모든 짝을 다 만들어 본 것」. 조인은 그 짝 더미에서 조건에 맞는 것만 남긴 것이다.**

- 남자 4명, 여자 3명이 있는 소개팅에서 **가능한 모든 짝**을 적어 보면 4 × 3 = 12쌍이다.
- 이 12쌍이 **아직 아무 조건도 안 건 상태**다. 누가 누구와 맞는지는 따지지 않았다.
- 여기에 "같은 동네 사람끼리만"이라는 조건을 걸면 12쌍 중 몇 쌍만 남는다. **이것이 `INNER JOIN` 이다.**
- 조건을 **깜빡 잊으면** 12쌍이 그대로 남는다. 이게 사고의 카티션곱이다.

```text
조인을 읽는 단 하나의 그림

    emp 4행                dept 3행
      │                      │
      └────── 모든 짝 ───────┘
                 ↓
          4 x 3 = 12행         <- 카티션곱. CROSS JOIN 이 여기서 멈춘다
                 ↓
           ON 조건으로 거른다
                 ↓
              3행              <- INNER JOIN (13번)
                 ↓
        짝 못 찾은 행을 NULL 로 되살린다
                 ↓
           4행 / 4행 / 5행     <- LEFT / RIGHT / FULL OUTER (14·16번)
```

이 소개팅 명단이 **똑같은 구조로** 조인이다.\
그래서 **조인의 모든 형태는 「12행에서 무엇을 남기고 무엇을 되살리나」의 변주**다. 12라는 수를 먼저 붙잡아야 나머지가 읽힌다.

> **카티션곱(Cartesian product) · 교차곱(cross product)** — 두 집합의 모든 조합.\
> 예: `{ann,bob,cho,dan} × {sales,dev,hr}` = 12쌍. 행 수가 **더하기가 아니라 곱하기**로 는다.

> **`CROSS JOIN`** — 카티션곱을 **일부러** 만드는 문법. 조인 조건이 없다.\
> 예: `FROM emp CROSS JOIN dept` 는 12행을 준다.

## 이 주제가 답하려는 질문

1. **카티션곱은 왜 생기나?** — 일부러 만들 때와 조인 조건을 빠뜨렸을 때, 결과는 똑같다.
2. **행 수를 예측할 수 있나?** — 더하기가 아니라 곱하기다. 표가 셋이면 세 번 곱한다.
3. **`CROSS JOIN` 을 일부러 쓰는 자리는 어디인가?** — 달력 생성과 조합 만들기.

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

**이 주제가 붙잡을 수는 `4 × 3 = 12` 다.**\
[13번](../13-inner-join/)의 3행, [14번](../14-left-right-outer-join/)의 4행, [16번](../16-full-outer-join/)의 5행이 전부 이 12행에서 출발한다.

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

### 1. 12행이 어떻게 만들어지나

**언제 쓰나** — 조인이라는 단어가 나올 때마다. 이 그림이 12·13·14·16 네 주제의 공통 출발선이다.

```text
(전) 두 표                                (후) 모든 짝 — 12행
 emp                 dept                 ann-sales  ann-dev  ann-hr
 ann                 sales                bob-sales  bob-dev  bob-hr
 bob                 dev                  cho-sales  cho-dev  cho-hr
 cho                 hr                   dan-sales  dan-dev  dan-hr
 dan
                                          왼쪽 행마다 오른쪽 전부를 붙인다
   ↓ CROSS JOIN                           4 x 3 = 12
```

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e CROSS JOIN dept d ORDER BY e.id, d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 ann | dev                       | ann | sales |
 ann | hr                        | ann | dev   |
 bob | sales                     | ann | hr    |
 bob | dev                       | bob | sales |
 bob | hr                        | bob | dev   |
 cho | sales                     | bob | hr    |
 cho | dev                       | cho | sales |
 cho | hr                        | cho | dev   |
 dan | sales                     | cho | hr    |
 dan | dev                       | dan | sales |
 dan | hr                        | dan | dev   |
(12 rows)                        | dan | hr    |
                                 +-----+-------+
```

그림 해설 — **`NULL` 도 짝지어진다.** `dan` 의 `dept_id` 가 `NULL` 인데도 12행 안에 `dan-sales`·`dan-dev`·`dan-hr` 이 다 있다.\
카티션곱은 **값을 보지 않는다.** 값을 보기 시작하는 것은 `ON` 부터다.\
비용 — **행 수가 곱으로 는다.** 10만 × 10만이면 100억 행이고, 그 100억 행을 만든 뒤에 거른다(고 정의된다).

---

### 2. 쉼표와 `CROSS JOIN` 은 같은 것이다

**언제 쓰나** — 옛 문법으로 쓰인 질의를 읽을 때.

```text
FROM emp, dept              FROM emp CROSS JOIN dept
      │                              │
      └──── 결과가 같다 ──────────────┘
```

```text
### SQL: SELECT COUNT(*) AS rows_comma FROM emp, dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 rows_comma                      +------------+
------------                     | rows_comma |
         12                      +------------+
(1 row)                          |         12 |
                                 +------------+

### SQL: SELECT COUNT(*) AS rows_cross FROM emp CROSS JOIN dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 rows_cross                      +------------+
------------                     | rows_cross |
         12                      +------------+
(1 row)                          |         12 |
                                 +------------+
```

그림 해설 — **둘은 같은 것이고, 그래서 위험하다.** 쉼표는 "표를 나열했다"처럼 보이지 "모든 짝을 만들었다"처럼 안 보인다.\
비용 — 쉼표 표기는 **의도와 사고를 구분할 수 없게** 만든다. 12행이 나왔을 때 그게 일부러인지 실수인지 문장만 봐서는 모른다.

★ **그래서 일부러 만들 때는 `CROSS JOIN` 이라고 적는다.** 읽는 사람에게 "이건 실수가 아니다"라고 말하는 유일한 방법이다.

---

### 3. 조인 조건을 빠뜨리면 — 같은 12행이 나온다

**언제 쓰나** — 결과 행 수가 이상하게 많을 때 가장 먼저 의심할 것.

```text
(의도) 사원마다 부서명 붙이기        (실수) WHERE 를 빠뜨렸다
FROM emp e, dept d                  FROM emp e, dept d
WHERE e.dept_id = d.id              (조건 없음)
        ↓                                   ↓
       3행                                 12행
   맞는 짝만 남았다                    모든 짝이 남았다
```

```text
### SQL: SELECT COUNT(*) FROM emp e, dept d WHERE e.dept_id = d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 count                           +----------+
-------                          | COUNT(*) |
     3                           +----------+
(1 row)                          |        3 |
                                 +----------+
```

표가 **셋 이상**일 때 조건을 하나만 빠뜨리면 눈에 잘 안 띈다.

```text
### SQL: SELECT COUNT(*) AS n FROM emp e, dept d, dept d2 WHERE e.dept_id = d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 9                               +---+
(1 row)                          | 9 |
                                 +---+
```

그림 해설 — `e`·`d` 는 조건으로 3행으로 좁혀졌는데, `d2` 는 아무 조건이 없어 **그 3행 각각에 3행이 곱해져 9행**이 됐다.\
조건을 N개 표에 대해 N−1개 걸어야 하는데 하나가 빠지면 **그 표의 행 수만큼 곱해진다.**\
비용 — **결과가 틀리는 게 아니라 부풀려진다.** 그래서 `COUNT` 나 `SUM` 을 씌우면 조용히 틀린 값이 나온다.\
같은 부풀림이 조인 조건이 **있어도** 1:N 관계에서 일어난다 — [13번](../13-inner-join/)의 팬아웃이다.

```text
행 수 예측 공식

 조건 없음        : |A| x |B|             4 x 3 = 12
 표 셋, 조건 하나 : |A| x |B| x |C| 중
                    한 쌍만 좁혀짐         3 x 3 = 9
 조건 다 걸림     : 짝이 맞는 것만          3
```

---

### 4. `CROSS JOIN … ON` — 두 엔진이 갈린다

**언제 쓰나** — `CROSS JOIN` 이라고 써 놓고 조건을 붙이고 싶어질 때. **여기서 방언이 갈린다.**

```text
### SQL: SELECT e.name, d.name FROM emp e CROSS JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---
ERROR:  syntax error at or near "ON"
LINE 1: ...ELECT e.name, d.name FROM emp e CROSS JOIN dept d ON e.dept_...
                                                             ^
--- MySQL 8.4.10 ---
+------+-------+
| name | name  |
+------+-------+
| ann  | sales |
| bob  | sales |
| cho  | dev   |
+------+-------+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `CROSS JOIN … ON …` | **✗ 구문 오류** — `CROSS` 는 조건을 받지 않는다 | **✓ `INNER JOIN` 처럼 동작한다** — 3행 |

그림 해설 — [MySQL 8.4 JOIN 페이지](https://dev.mysql.com/doc/refman/8.4/en/join.html)는 `JOIN`·`INNER JOIN`·`CROSS JOIN` 을 **문법적 동의어**로 다룬다. 그래서 `CROSS JOIN` 에 `ON` 을 붙이면 그냥 내부 조인이 된다.\
PG 는 `CROSS JOIN` 을 「조건 없는 조인」으로 못 박아 두어 `ON` 자체를 파싱하지 않는다.\
비용 — **MySQL 에서 쓴 `CROSS JOIN … ON` 을 PG 로 옮기면 구문 오류로 깨진다.** 반대는 안 깨진다.

★ **그래서 조건이 있으면 `JOIN … ON` 이라고 적는다.** `CROSS JOIN` 은 조건이 **없을 때만** 쓰는 말로 두면 양쪽에서 돈다.

같은 성질의 사고가 반대 방향으로도 있다 — [13번](../13-inner-join/)의 `JOIN` 에 `ON` 을 빠뜨리는 경우다.

---

### 5. 일부러 쓰는 자리 (1) — 없는 행을 만들어 낸다

**언제 쓰나** — 「모든 부서 × 모든 분기」처럼 **데이터에 없는 조합까지** 표에 있어야 할 때.

```text
(전) 실적이 있는 부서·분기만          (후) 모든 부서 x 모든 분기
 sales Q1   sales Q3                 sales Q1  sales Q2  sales Q3  sales Q4
 dev   Q2                            dev   Q1  dev   Q2  dev   Q3  dev   Q4
                                     hr    Q1  hr    Q2  hr    Q3  hr    Q4
   실적 없는 칸이 "행 자체가 없다"        빈 칸이 0 으로 보인다
```

```text
### SQL: SELECT d.name AS dept, q.q FROM dept d
         CROSS JOIN (SELECT 1 AS q UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) AS q
         ORDER BY d.id, q.q;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | q                       +-------+---+
-------+---                      | dept  | q |
 sales | 1                       +-------+---+
 sales | 2                       | sales | 1 |
 sales | 3                       | sales | 2 |
 sales | 4                       | sales | 3 |
 dev   | 1                       | sales | 4 |
 dev   | 2                       | dev   | 1 |
 dev   | 3                       | dev   | 2 |
 dev   | 4                       | dev   | 3 |
 hr    | 1                       | dev   | 4 |
 hr    | 2                       | hr    | 1 |
 hr    | 3                       | hr    | 2 |
 hr    | 4                       | hr    | 3 |
(12 rows)                        | hr    | 4 |
                                 +-------+---+
```

그림 해설 — 이 12행을 **뼈대**로 삼고 여기에 실적을 `LEFT JOIN` 으로 붙이면, 실적 없는 칸이 `NULL`(또는 `COALESCE` 로 0)이 되어 **표에서 안 사라진다.**\
「데이터가 없는 구간이 보고서에서 통째로 빠지는」 사고의 정석 처방이다.\
비용 — 뼈대 행 수가 곧 결과 행 수의 하한이다. 부서 1,000개 × 365일이면 36만 5천 행이 **항상** 만들어진다.

**분기 목록을 만드는 방법은 방언이 갈린다.** PG 에는 전용 함수가 있다.

```text
### SQL: SELECT d.name AS dept, m AS month FROM dept d CROSS JOIN generate_series(1,3) AS m ORDER BY d.id, m;
--- PG 18.6 ---
 dept  | month 
-------+-------
 sales |     1
 sales |     2
 sales |     3
 dev   |     1
 dev   |     2
 dev   |     3
 hr    |     1
 hr    |     2
 hr    |     3
(9 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near '(1,3) AS m' at line 1
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `generate_series(1,3)` | ✓ 3행을 만든다 | **✗ `ERROR 1064`** — 그런 함수가 없다 |

MySQL 에서는 `UNION ALL` 목록이나 재귀 CTE 로 만든다(목록의 **33번 주제**).\
`VALUES` 리스트로 만들려 하면 **행 생성자 문법까지 갈린다** — [10번](../10-from-clause-aliases-derived-tables/)이 정본이다.

---

### 6. 일부러 쓰는 자리 (2) — 조합을 만든다

**언제 쓰나** — 같은 표의 행끼리 **쌍을 만들어야** 할 때. 중복 비교·거리 계산·대진표.

```text
(전) emp 4명                          (후) 순서 없는 쌍 6개
 ann bob cho dan                      ann-bob  ann-cho  ann-dan
                                               bob-cho  bob-dan
   ↓ CROSS JOIN 자기 자신 = 16쌍                        cho-dan
   ↓ WHERE a.id < b.id
                                      16 쌍에서 6 쌍만 남았다
```

```text
### SQL: SELECT a.name AS x, b.name AS y FROM emp a CROSS JOIN emp b WHERE a.id < b.id ORDER BY a.id, b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  x  |  y                        +-----+-----+
-----+-----                      | x   | y   |
 ann | bob                       +-----+-----+
 ann | cho                       | ann | bob |
 ann | dan                       | ann | cho |
 bob | cho                       | ann | dan |
 bob | dan                       | bob | cho |
 cho | dan                       | bob | dan |
(6 rows)                         | cho | dan |
                                 +-----+-----+
```

그림 해설 — `a.id < b.id` 한 줄이 **두 가지를 동시에 처리한다.** 자기 자신과의 짝(`ann-ann`)을 빼고, `ann-bob` 과 `bob-ann` 중 하나만 남긴다.\
16 = 4², 자기 짝 4개를 빼면 12, 순서를 무시해 반으로 나누면 6. 실제로 6행이 나왔다.\
비용 — **N² 이다.** 1,000행짜리 표면 100만 쌍이다. 조합을 만들 때는 **먼저 좁히고** 나서 곱한다.

`<>` 로 쓰면 **순서만 다른 쌍이 둘 다 남아** 12쌍이 된다. 자기 짝 4개만 빠진 것이다.

```text
### SQL: SELECT COUNT(*) AS n FROM emp a CROSS JOIN emp b WHERE a.id <> b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +----+
----                             | n  |
 12                              +----+
(1 row)                          | 12 |
                                 +----+
```

같은 표를 두 별칭으로 올리는 형태 일반은 목록의 **17번 주제**(SELF JOIN)가 정본이다.

---

### 7. 일부러 쓰는 자리 (3) — 한 행짜리 값을 모든 행에 붙인다

**언제 쓰나** — 「전체 평균」·「총합」 같은 값 하나를 모든 행 옆에 놓고 비교할 때.

```text
(전) 한 행짜리 표                    (후) 4행 x 1행 = 4행
+-----------+                       +------+--------+---------+
| avg = 400 |                       | ann  |    300 |     400 |
+-----------+                       | bob  |    500 |     400 |
      x                             | cho  |   NULL |     400 |
 emp 4행                            | dan  |    400 |     400 |
                                    +------+--------+---------+
                                      같은 값이 모든 행에 붙는다
```

```text
### SQL: SELECT e.name, e.salary, avg_t.avg_sal FROM emp e
         CROSS JOIN (SELECT AVG(salary) AS avg_sal FROM emp) AS avg_t ORDER BY e.id;
--- PG 18.6 ---                                 --- MySQL 8.4.10 ---
 name | salary |       avg_sal                  +------+--------+----------+
------+--------+----------------------          | name | salary | avg_sal  |
 ann  |    300 | 400.0000000000000000           +------+--------+----------+
 bob  |    500 | 400.0000000000000000           | ann  |    300 | 400.0000 |
 cho  |   NULL | 400.0000000000000000           | bob  |    500 | 400.0000 |
 dan  |    400 | 400.0000000000000000           | cho  |   NULL | 400.0000 |
(4 rows)                                        | dan  |    400 | 400.0000 |
                                                +------+--------+----------+
```

그림 해설 — **오른쪽이 1행이면 곱해도 행 수가 안 는다.** `4 × 1 = 4`. 그래서 이 용법은 안전하다.`AVG` 값이 `300+500+400)/3 = 400` 인 것은 `cho` 의 `NULL` 을 집계가 건너뛰었기 때문이다([04번](../04-null-three-valued-logic/)).비용 — 한 행짜리 표를 붙이는 것이라 거의 공짜다. 같은 일을 윈도우 함수로도 할 수 있다(목록의 **26번 주제**).

> **덤으로 보이는 차이** — 같은 `AVG` 인데 PG 는 소수 16자리, MySQL 은 4자리로 찍는다.> 수치 타입과 정밀도 이야기는 이 주제가 아니라 목록의 **36번 주제**다.

## 문법 — 형태와 규칙

```sql
-- 카티션곱을 만드는 두 표기 (결과가 같다)
FROM 표A, 표B
FROM 표A CROSS JOIN 표B

-- 조건이 있으면 이것 (12번이 아니라 13번의 형태다)
FROM 표A JOIN 표B ON <조건>
```

규칙 다섯.

1. **결과 행 수 = 왼쪽 행 수 × 오른쪽 행 수.** 더하기가 아니다. 표가 셋이면 세 번 곱한다.
2. **쉼표와 `CROSS JOIN` 은 같다.** 일부러 만들 때만 `CROSS JOIN` 이라고 적어 의도를 남긴다.
3. **`CROSS JOIN` 은 `ON` 을 받지 않는다** — PG 는 구문 오류, **MySQL 은 받아서 내부 조인으로 만든다.** 조건이 있으면 `JOIN … ON` 을 쓴다.
4. **`NULL` 도 짝지어진다.** 카티션곱은 값을 보지 않는다.
5. **조인 조건은 표 개수보다 하나 적게** 필요하다. 표 3개면 조건 2개. 하나 빠지면 그 표의 행 수만큼 곱해진다.

조인 형태를 이 12행 기준으로 한 줄씩 적으면 이렇다.

```text
             12행에서 무엇을 하나                결과 행 수   정본
CROSS JOIN   아무것도 안 한다                        12       이 주제
INNER JOIN   ON 으로 거른다                           3       13번
LEFT  JOIN   + 짝 못 찾은 왼쪽을 NULL 로 되살린다       4       14번
RIGHT JOIN   + 짝 못 찾은 오른쪽을 NULL 로 되살린다     4       14번
FULL  OUTER  + 양쪽 다 되살린다                        5       16번
```

## 어디서 틀리나

- **쉼표 표기를 「나열」로 읽는다.**\
  `FROM emp, dept` 는 나열이 아니라 **곱하기**다. 조건은 `WHERE` 어딘가에 있어야 한다.
- **표 셋 이상에서 조인 조건을 하나 빠뜨린다.**\
  위에서 9행이 나왔다. 결과가 **틀리는 게 아니라 부풀려지므로** 집계를 씌우면 조용히 틀린다.
- **행 수를 더하기로 어림한다.**\
  4 + 3 = 7 이 아니라 4 × 3 = 12 다. 큰 표에서는 이 착각 하나로 디스크가 찬다.
- **`CROSS JOIN … ON` 을 쓴다.**\
  MySQL 에서 돌던 것이 PG 에서 구문 오류다. 조건이 있으면 `JOIN … ON` 이라고 적는다.
- **`CROSS JOIN` 뒤에 `WHERE` 로 조건을 건 것을 「카티션곱이라 느리다」고 판단한다.**\
  논리적으로는 12행을 만들지만, **실제 실행은 옵티마이저가 정한다**(아래 절). 느린지 아닌지는 계획을 봐야 안다.
- **조합을 만들 때 `a.id <> b.id` 를 쓴다.**\
  `<>` 는 자기 짝만 뺀다 — `ann-bob` 과 `bob-ann` 이 **둘 다** 남아 12쌍이 된다. 순서를 없애려면 `<` 를 쓴다.
- **`generate_series` 가 어디서나 되는 줄 안다.**\
  MySQL 8.4.10 에는 없다 — `ERROR 1064` 다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 조인 결과 = **모든 짝을 만든 뒤 조건으로 거른 것** | **결과의 정의** | 언어 — 두 문서가 같은 모양으로 적는다 |
| 엔진이 실제로 **12행을 만들어 본다** | 아무도 보장 안 함 | 옵티마이저가 조건을 먼저 밀어 넣는다 |
| 그래서 "`CROSS JOIN` + `WHERE` 는 항상 느리다" | **틀린 일반화** | 계획을 봐야 안다 |

- **결과는 정의가 정한다.** [01번](../01-logical-query-processing-order/)의 말대로, 옵티마이저가 순서를 바꿔도 **결과는 이 순서대로 계산한 것과 같아야** 한다.
- **비용은 엔진이 정한다.** `FROM a, b WHERE a.k = b.k` 를 해시 조인으로 처리하면 12행은 **한 번도 만들어지지 않는다.**
- ★ **그러므로 「카티션곱」은 성능 경고가 아니라 의미 모델이다.** 성능이 궁금하면 `EXPLAIN` 을 본다(목록의 **58번 주제**).
- 진짜 위험한 것은 **조건이 아예 없어서** 옵티마이저도 줄일 수 없는 경우다. 그건 정의도 실행도 12행이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 없는 행을 만들어야 할 때.** 부서 × 기간, 상품 × 사이즈. 뼈대를 만들고 실적을 `LEFT JOIN` 으로 붙인다.
- **쓴다 — 조합·쌍을 만들 때.** `a.id < b.id` 로 순서 없는 쌍을 만든다.
- **쓴다 — 한 행짜리 값을 모든 행에 붙일 때.** 「전체 평균」 같은 스칼라를 `CROSS JOIN` 으로 붙이면 모든 행에 같은 값이 온다.
- **안 쓴다 — 관계가 있는 두 표를 붙일 때.** 그건 `JOIN … ON` 이다. `CROSS JOIN` 으로 쓰면 조건이 `WHERE` 로 흩어져 읽기 어렵다.
- **안 쓴다 — 큰 표 두 개.** 행 수가 곱이다. 먼저 좁히고 나서 곱한다.
- **쉼표 표기는 안 쓴다.** 의도와 사고가 구분되지 않는다.

## 핵심 문장

- **조인 = 모든 짝을 만든 뒤 조건으로 거르는 것.** `CROSS JOIN` 은 그 「모든 짝」에서 멈춘 것이다.
- 행 수는 **곱하기**다. `emp` 4행 × `dept` 3행 = **12행**. 이 12가 13·14·16번의 출발선이다.
- **쉼표와 `CROSS JOIN` 은 같다.** 일부러 만들 때만 `CROSS JOIN` 이라고 적어 의도를 남긴다.
- **`CROSS JOIN … ON` 은 PG 구문 오류 · MySQL 내부 조인**이다. 조건이 있으면 `JOIN … ON` 을 쓴다.
- 표가 셋이면 조인 조건이 **둘** 필요하다. 하나 빠지면 그 표의 행 수만큼 **조용히 곱해진다.**
- `CROSS JOIN` 의 정당한 용도는 **뼈대 만들기**와 **조합 만들기** 둘이다.
- 「카티션곱」은 **의미 모델이지 성능 경고가 아니다.** 옵티마이저는 12행을 안 만들 수도 있다.

## 관련 자료

- [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) — `CROSS JOIN` 이 「조건 없는 조인」으로 정의돼 있다.
- [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html) — `JOIN`·`INNER JOIN`·`CROSS JOIN` 을 문법적 동의어로 다룬다.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 여덟 칸 전체까지, 여기는 1번 칸 안에서 행 수가 어떻게 정해지나부터.**
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — **경계: 그쪽은 `FROM` 에 무엇을 올리나까지, 여기는 올린 것 둘이 어떻게 곱해지나부터.**
- [13 INNER JOIN](../13-inner-join/) — 이 12행을 `ON` 으로 거른 것.
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) · [16 FULL OUTER JOIN](../16-full-outer-join/) — 거른 뒤 되살리는 것.
- **같은 표를 두 번 올리는 형태**는 목록의 **17번 주제**, **`USING`·`NATURAL`** 은 목록의 **18번 주제**, **조인 팬아웃**은 목록의 **25번 주제**가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **카티션곱(Cartesian product)** — 두 집합의 모든 조합. 행 수가 곱으로 는다.\
  예: 4행 × 3행 = 12행.
- **`CROSS JOIN`** — 카티션곱을 일부러 만드는 문법. 조인 조건이 없다.\
  예: `FROM emp CROSS JOIN dept` 는 12행.
- **쉼표 조인(comma join)** — `FROM a, b` 표기. `CROSS JOIN` 과 결과가 같다.\
  예: `FROM emp, dept` 도 12행. 의도가 안 보이는 것이 단점이다.
- **조인 조건(join condition)** — 짝을 남길지 정하는 술어. `ON` 이나 `WHERE` 에 적는다.\
  예: `ON e.dept_id = d.id`. 표 N개에 조건 N−1개가 필요하다.
- **뼈대 표(spine · calendar table)** — 결과에 반드시 있어야 할 행들을 미리 만든 표.\
  예: 부서 3개 × 분기 4개 = 12행. 여기에 실적을 `LEFT JOIN` 으로 붙인다.
- **조합(combination)** — 순서를 무시한 쌍.\
  예: `a.id < b.id` 로 만든 6쌍. `ann-bob` 만 있고 `bob-ann` 은 없다.
- **`generate_series`** — 연속된 수·날짜를 행으로 만들어 주는 PostgreSQL 함수.\
  예: `generate_series(1,3)` 은 1·2·3 세 행. **MySQL 8.4.10 에는 없다.**
- **팬아웃(fan-out)** — 조인 조건이 있는데도 1:N 관계 때문에 행이 불어나는 현상.\
  예: 사원 한 명이 프로젝트 둘에 속하면 그 사원의 행이 둘이 된다. [13번](../13-inner-join/)·목록의 25번 주제.
