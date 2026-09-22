# sql/03-WHERE 와 HAVING 의 차이 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> **버전** — `WHERE`·`HAVING` 두 절 자체는 두 엔진 모두 오래전부터 있다. 버전에 갈리는 것은 없다.\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/). **이 주제는 01 의 그림 하나로 전부 설명된다** — `WHERE` 는 2번 칸, `HAVING` 은 4번 칸이다.

## 한눈에 — 쉽게 말하면

**`WHERE` 는 사람을 떨어뜨리고 `HAVING` 은 팀을 떨어뜨린다.**

- 사내 대회 신청을 받는다고 하자. 심사 창구가 둘이다.
- **2번 창구(`WHERE`)** — 지원자 **한 명씩** 본다. "이 사람 경력이 3년 미만이면 탈락."\
  아직 팀을 안 짰으니 "팀 평균 경력"은 물어볼 수 없다.
- 그 뒤에 팀을 짠다(`GROUP BY`).
- **4번 창구(`HAVING`)** — **팀 단위로** 본다. "이 팀 평균 경력이 3년 미만이면 팀째 탈락."\
  이미 팀이 만들어졌으니 팀 전체를 볼 수 있다.

```text
01 의 여덟 칸 중 이 주제가 다루는 것은 2번과 4번이다

1. FROM      표를 만든다
2. WHERE     행을 버린다        <- 사람 한 명씩 본다
3. GROUP BY  행을 묶는다        <- 여기서 팀이 생긴다
4. HAVING    그룹을 버린다      <- 팀 단위로 본다
5. SELECT    열을 만든다
6. DISTINCT  중복을 지운다
7. ORDER BY  줄을 세운다
8. LIMIT     자른다
```

이 두 창구가 **똑같은 구조로** `WHERE` 와 `HAVING` 이다.\
"둘 다 조건을 거는 절인데 뭐가 다르냐"의 답은 **"사이에 3번 칸이 끼어 있다"** 한 마디다.\
3번 칸이 **행의 단위를 사람에서 팀으로 바꾸기 때문에**, 같은 문장을 어디에 쓰느냐로 대상이 달라진다.

> **행(row)과 그룹(group)** — `GROUP BY` 를 지나기 전의 한 줄은 **행**, 지난 뒤의 한 줄은 **그룹**이다.\
> 예: `emp` 4행이 `GROUP BY dept_id` 를 지나면 그룹 3개가 된다. 그 뒤로 한 줄은 사원이 아니라 부서다.

> **술어(predicate)** — 참/거짓을 판정하는 조건식.\
> 예: `salary >= 400` 은 행 하나로 판정되는 술어, `MAX(salary) >= 400` 은 그룹 전체를 봐야 판정되는 술어다.

## 이 주제가 답하려는 질문

1. **같은 뜻처럼 보이는 조건을 `WHERE` 에 둘 때와 `HAVING` 에 둘 때, 결과는 언제 갈리고 언제 같은가?**
2. **결과가 같을 때 비용도 같은가?** — 엔진이 알아서 옮겨 주는가, 아니면 내가 적은 대로 도는가.
3. **두 절에서 쓸 수 있는 이름의 범위가 왜 다른가?** — 집계 함수·비집계 열·열 별칭이 각각 어디서 되나.

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

**이 주제에서 일을 내는 것은 `cho` 다.** [01번](../01-logical-query-processing-order/)에서 `cho` 는 `WHERE salary IS NOT NULL` 에 걸려 탈락했다.\
여기서는 그 탈락이 **`WHERE` 에서 일어나느냐 `HAVING` 에서 일어나느냐**로 답이 갈린다.

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

### 1. 두 칸에 무엇이 들어와서 무엇이 나가나

**언제 쓰나** — 조건을 어디에 적을지 고를 때마다. 이 그림 하나가 나머지 전부의 근거다.

```text
(전) WHERE 가 받는 것 — 행 4개              (전) HAVING 이 받는 것 — 그룹 3개
+----+------+---------+--------+           dept_id=10   { ann(300), bob(500) }
|  1 | ann  |      10 |    300 |           dept_id=20   { cho(NULL) }
|  2 | bob  |      10 |    500 |           dept_id=NULL { dan(400) }
|  3 | cho  |      20 |   NULL |
|  4 | dan  |    NULL |    400 |
+----+------+---------+--------+
   ↓ 행 하나씩 판정                            ↓ 그룹 하나씩 판정
(후) 더 작은 행 집합                         (후) 더 작은 그룹 집합
```

그림 해설 — **두 절이 보는 대상 자체가 다르다.** `WHERE` 는 `salary` 라는 *값 하나*를 보고, `HAVING` 은 `{300, 500}` 이라는 *값 묶음*을 본다.\
그래서 `HAVING` 에서는 묶음을 하나로 접는 함수(`MAX`·`COUNT`·`SUM`)가 필요하고, `WHERE` 에서는 그 함수가 쓸 대상 자체가 없다.\
비용 — `WHERE` 는 3번 칸 앞이라 여기서 버린 행은 **묶일 일조차 없다.** `HAVING` 은 4번 칸이라 **묶은 뒤에** 버린다.

집계 함수를 `WHERE` 에 쓰면 두 엔진 다 거부한다. 「아직 그룹이 없다」는 말을 에러로 하는 것이다.

```text
### SQL: SELECT dept_id FROM emp WHERE COUNT(*) > 1 GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  aggregate functions are not allowed in WHERE
LINE 1: SELECT dept_id FROM emp WHERE COUNT(*) > 1 GROUP BY dept_id;
                                      ^
--- MySQL 8.4.10 ---
ERROR 1111 (HY000) at line 1: Invalid use of group function
```

---

### 2. 결과가 갈리는 자리 — 같은 말처럼 들리는 두 문

**언제 쓰나** — 「급여 400 이상」 같은 조건을 집계 질의에 붙일 때. **여기가 이 주제의 중심이다.**

같은 데이터에 두 문을 나란히 던진다. 둘 다 "400 이상"이라고 말하고 있다.

```text
(A) WHERE 로 거른다 — 사람을 먼저 버린다        (B) HAVING 으로 거른다 — 팀째 남긴다
                                                (400 이상인 사람이 한 명이라도 있으면)

emp 4행                                         emp 4행
  ↓ WHERE salary >= 400                           ↓ GROUP BY dept_id
[bob 500] [dan 400]                             {10:[ann,bob]} {20:[cho]} {NULL:[dan]}
  (ann 300 탈락 · cho NULL 탈락)                  ↓ HAVING MAX(salary) >= 400
  ↓ GROUP BY dept_id                            {10:[ann,bob]} {NULL:[dan]}
{10:[bob]} {NULL:[dan]}                           (20 은 MAX(salary)=NULL 이라 탈락)
  ↓                                               ↓
dept_id=10 의 cnt = 1                           dept_id=10 의 cnt = 2
```

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp WHERE salary >= 400 GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   1                   +---------+-----+
    NULL |   1                   |    NULL |   1 |
(2 rows)                         |      10 |   1 |
                                 +---------+-----+

### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING MAX(salary) >= 400 ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   2                   +---------+-----+
    NULL |   1                   |    NULL |   1 |
(2 rows)                         |      10 |   2 |
                                 +---------+-----+
```

두 그림의 결론 — **`dept_id=10` 의 `cnt` 가 1과 2로 갈린다.**\
(A)는 `ann`(300)을 세지 않았고, (B)는 `ann` 을 **포함해서** 셌다. (B)에서 `ann` 은 조건을 만족하지 않지만 **팀이 살아남았으므로 같이 살아남는다.**

**두 문은 다른 질문에 답하고 있다.**

| | 무엇을 묻는가 | `dept_id=10` 의 답 |
|---|---|---|
| (A) `WHERE salary >= 400` | 급여 400 이상인 사람이 부서마다 **몇 명**인가 | 1명 (`bob`) |
| (B) `HAVING MAX(salary) >= 400` | **한 명이라도** 400 이상인 부서의 **전체 인원**은 | 2명 (`ann`, `bob`) |

비용 — (A)는 4행 중 2행만 묶는다. (B)는 4행을 전부 묶은 뒤 그룹 하나를 버린다. **(A)가 싸고, 그리고 답이 다르다.**

> `dept_id=20`(`cho`) 이 (B)에서 빠진 것은 `MAX(NULL)` 이 `NULL` 이고 `NULL >= 400` 이 `UNKNOWN` 이기 때문이다.\
> `HAVING` 도 `WHERE` 와 똑같이 **`TRUE` 만 통과시킨다** — [04번](../04-null-three-valued-logic/)의 규칙이 4번 칸에서도 그대로 작동한다.

---

### 3. 결과가 같은 자리 — 그룹 키에 건 조건

**언제 쓰나** — 조건이 **`GROUP BY` 에 적은 열**에 걸릴 때. 이때는 두 절이 같은 답을 준다.

```text
(A) WHERE dept_id = 10                     (B) HAVING dept_id = 10
emp 4행                                    emp 4행
  ↓ 행 2개만 통과 (ann, bob)                 ↓ 그룹 3개를 전부 만든다
  ↓ 그룹 1개를 만든다                        ↓ 그룹 2개를 버린다
{10:[ann,bob]}                             {10:[ann,bob]}
   같은 결과                                   같은 결과
```

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp WHERE dept_id = 10 GROUP BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  s                    +---------+------+
---------+-----                  | dept_id | s    |
      10 | 800                   +---------+------+
(1 row)                          |      10 |  800 |
                                 +---------+------+

### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY dept_id HAVING dept_id = 10;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  s                    +---------+------+
---------+-----                  | dept_id | s    |
      10 | 800                   +---------+------+
(1 row)                          |      10 |  800 |
                                 +---------+------+
```

그림 해설 — **그룹 키는 그룹 안의 모든 행에서 같은 값**이므로, 행 단위 판정과 그룹 단위 판정이 어긋날 수 없다.\
그래서 이 경우에 한해 `HAVING` 에 비집계 열을 써도 결과가 맞는다.\
비용 — **결과는 같지만 하는 일이 같지는 않다.** 다음 절에서 계획을 찍어 본다.

---

### 4. 비용은 갈리나 — 계획을 찍어 본다

**언제 쓰나** — "`WHERE` 가 `HAVING` 보다 빠르다"를 믿기 전에. **엔진마다 답이 다르다.**

3번 절의 두 문(`WHERE dept_id = 10` / `HAVING dept_id = 10`)을 그대로 `EXPLAIN ANALYZE` 에 건다.

```text
### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp WHERE dept_id = 10 GROUP BY dept_id;
--- PG 18.6 ---
 GroupAggregate  (cost=0.00..24.15 rows=1 width=12) (actual time=0.012..0.012 rows=1.00 loops=1)
   Buffers: shared hit=1
   ->  Seq Scan on emp  (cost=0.00..24.12 rows=6 width=4) (actual time=0.009..0.010 rows=2.00 loops=1)
         Filter: (dept_id = 10)
         Rows Removed by Filter: 2
         Buffers: shared hit=1

### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp GROUP BY dept_id HAVING dept_id = 10;
--- PG 18.6 ---
 GroupAggregate  (cost=0.00..24.15 rows=1 width=12) (actual time=0.010..0.011 rows=1.00 loops=1)
   Buffers: shared hit=1
   ->  Seq Scan on emp  (cost=0.00..24.12 rows=6 width=4) (actual time=0.007..0.008 rows=2.00 loops=1)
         Filter: (dept_id = 10)
         Rows Removed by Filter: 2
         Buffers: shared hit=1
```

**PG 18.6 에서 두 계획은 한 글자도 다르지 않다.** `HAVING dept_id = 10` 이 `Seq Scan` 의 `Filter` 로 **내려갔다.**\
옵티마이저가 「그룹 키에 대한 조건은 묶기 전에 걸러도 결과가 같다」를 알고 스스로 옮긴 것이다.

같은 두 문을 MySQL 에 던지면 **그렇지 않다.**

```text
### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp WHERE dept_id = 10 GROUP BY dept_id;
--- MySQL 8.4.10 ---  (출력의 표 테두리는 지웠다 — 폭이 200자를 넘는다)
-> Group aggregate: count(0)  (cost=0.75 rows=1) (actual time=0.0341..0.0342 rows=1 loops=1)
    -> Filter: (emp.dept_id = 10)  (cost=0.65 rows=1) (actual time=0.0259..0.0303 rows=2 loops=1)
        -> Table scan on emp  (cost=0.65 rows=4) (actual time=0.0238..0.0266 rows=4 loops=1)

### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp GROUP BY dept_id HAVING dept_id = 10;
--- MySQL 8.4.10 ---
-> Filter: (emp.dept_id = 10)  (actual time=0.053..0.0539 rows=1 loops=1)
    -> Table scan on <temporary>  (actual time=0.0491..0.0497 rows=3 loops=1)
        -> Aggregate using temporary table  (actual time=0.0482..0.0482 rows=3 loops=1)
            -> Table scan on emp  (cost=0.65 rows=4) (actual time=0.0206..0.0235 rows=4 loops=1)
```

두 그림의 결론 — **MySQL 8.4.10 은 조건을 안 내린다.** 임시 테이블을 만들어 그룹 **3개를 전부 만든 뒤**(`rows=3`) 걸러 1개를 남겼다.\
`WHERE` 쪽은 걸러진 **2행만** 집계로 들어갔다(`rows=2`).

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 그룹 키 조건을 `HAVING` 에 두면 | `Seq Scan` 의 `Filter` 로 **내려간다** — `WHERE` 와 계획이 동일 | **안 내려간다** — 임시 테이블에 그룹 3개를 만든 뒤 거른다 |
| 집계 조건(`MAX(...)`)을 `HAVING` 에 두면 | 내릴 수 없다 — 집계 노드의 `Filter` 가 된다 | 내릴 수 없다 |

★ **이것은 구현 세부사항이지 언어 보장이 아니다.** 아래 「구현 세부사항 대 언어 보장」 절에서 다시 짚는다.

집계에 건 조건은 어느 엔진도 못 내린다. PG 에서 그 모습은 이렇게 보인다.

```text
### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp GROUP BY dept_id HAVING MAX(salary) >= 400;
--- PG 18.6 ---
 HashAggregate  (cost=29.78..32.28 rows=67 width=12) (actual time=0.029..0.031 rows=2.00 loops=1)
   Group Key: dept_id
   Filter: (max(salary) >= 400)
   Batches: 1  Memory Usage: 32kB
   Rows Removed by Filter: 1
   Buffers: shared hit=1
   ->  Seq Scan on emp  (cost=0.00..21.30 rows=1130 width=8) (actual time=0.010..0.011 rows=4.00 loops=1)
         Buffers: shared hit=1
```

`Filter` 가 `Seq Scan` 이 아니라 **`HashAggregate` 에 붙어 있고**, 스캔은 `rows=4.00` — **4행을 전부 읽었다.**\
2번 절의 `WHERE salary >= 400` 은 같은 자리에서 `rows=2.00` 이었다. 이것이 그림으로 본 「묶기 전에 버리기」와 「묶은 뒤에 버리기」다.

---

### 5. 각 절에서 무엇을 쓸 수 있나

**언제 쓰나** — 「이 이름이 여기서 되나」가 막힐 때. SQL 은 형태가 아니라 **가시성**이 본체인 언어다.

```text
             집계 함수   비집계 열      SELECT 의 열 별칭
             COUNT(*)   salary        AS cnt
           +----------+-------------+------------------+
  WHERE    |    X     |      O      |        X         |  <- 양쪽 엔진 동일
  HAVING   |    O     | 그룹 키만 O  |  PG X / MySQL O  |  <- 여기만 갈린다
           +----------+-------------+------------------+
```

**비집계 열** — `HAVING` 에서 그룹 키가 아닌 열을 부르면 거부된다. 다만 **거부하는 말이 다르다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING salary >= 400;
--- PG 18.6 ---
ERROR:  column "emp.salary" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: ... COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING salary >= ...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'salary' in 'having clause'
```

그림 해설 — PG 는 **"그 열은 GROUP BY 에 있거나 집계 안에 있어야 한다"**, MySQL 은 **"그런 열이 없다"** 고 한다.\
MySQL 쪽 말이 더 정확한 묘사다 — MySQL 의 `HAVING` 은 이름을 **출력 열 목록에서 먼저 찾기** 때문에, 거기 없는 `salary` 는 말 그대로 *모르는 이름*이다.

**열 별칭** — 바로 그 탐색 순서 때문에 방언이 갈린다.

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 2;
--- PG 18.6 ---
ERROR:  column "cnt" does not exist
LINE 1: ..., COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 2;
                                                              ^
--- MySQL 8.4.10 ---
+---------+-----+
| dept_id | cnt |
+---------+-----+
|      10 |   2 |
+---------+-----+
```

식을 그대로 적으면 **양쪽 다** 돈다. 이식성을 원하면 이 형태를 쓴다.

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING COUNT(*) >= 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   2                   +---------+-----+
(1 row)                          |      10 |   2 |
                                 +---------+-----+
```

| 별칭을 쓸 수 있나 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `WHERE` | ✗ | ✗ |
| `HAVING` | **✗ `column "cnt" does not exist`** | **✓ 정상 출력** |

비용 — 없다. 이식성 문제다. **MySQL 에서 돌던 질의가 PG 에서 깨지는 방향**이고 반대는 안 깨진다.

---

### 6. `GROUP BY` 가 없는 `HAVING` — 표 전체가 한 그룹이다

**언제 쓰나** — 드물지만 문법상 허용되고, **결과가 직관과 다르다.**

```text
(전) GROUP BY 가 없다                      (후) 표 전체가 그룹 "하나"다
+----+------+---------+--------+           +---------------------------+
|  1 | ann  |      10 |    300 |           | { ann, bob, cho, dan }    |
|  2 | bob  |      10 |    500 |  집계가    |   COUNT(*) = 4            |
|  3 | cho  |      20 |   NULL |  있으면    +---------------------------+
|  4 | dan  |    NULL |    400 |  ------>      그룹 1개 -> 결과 1행
+----+------+---------+--------+
                                            ↓ HAVING 이 이 한 그룹을 판정한다
                                            통과하면 1행, 떨어지면 0행
```

```text
### SQL: SELECT COUNT(*) AS cnt FROM emp HAVING COUNT(*) > 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 cnt                             +-----+
-----                            | cnt |
   4                             +-----+
(1 row)                          |   4 |
                                 +-----+

### SQL: SELECT COUNT(*) AS cnt FROM emp HAVING COUNT(*) > 100;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 cnt                             (빈 결과 — 출력이 한 줄도 없다)
-----
(0 rows)
```

그림 해설 — 집계만 있고 `GROUP BY` 가 없는 질의는 **항상 1행**을 준다. 그런데 `HAVING` 이 그 한 그룹을 떨어뜨리면 **0행**이 된다.\
「집계 질의는 행이 없어도 한 줄은 나온다」는 상식이 `HAVING` 앞에서만 깨진다.\
비용 — 표 전체를 집계한 뒤 버리는 것이라 **가장 비싼 0행**이다.

「행이 없어도 한 줄」 쪽도 던져서 확인했다.

```text
### SQL: SELECT COUNT(*) AS cnt FROM emp WHERE 1 = 0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 cnt                             +-----+
-----                            | cnt |
   0                             +-----+
(1 row)                          |   0 |
                                 +-----+
```

반대로 **`GROUP BY` 가 있으면 빈 그룹 자체가 만들어지지 않는다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING COUNT(*) = 0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   (빈 결과 — 출력이 한 줄도 없다)
---------+-----
(0 rows)
```

`GROUP BY` 는 **행이 있는 그룹만** 만든다. 그래서 `COUNT(*) = 0` 인 그룹은 영원히 나오지 않는다 — 사원이 없는 `hr` 부서는 `emp` 에 행이 없어 그룹이 서지도 않았다.

## 문법 — 형태와 규칙

SQL 에서 외울 것은 형태가 아니라 **어느 절에서 무엇이 보이나**다.

```sql
SELECT   <출력 열>
FROM     <표>
WHERE    <행 술어>        -- 집계 함수 금지 · 열 별칭 금지
GROUP BY <그룹 키>
HAVING   <그룹 술어>      -- 집계 함수 가능 · 비집계 열은 그룹 키만 · 열 별칭은 MySQL 만
ORDER BY <정렬 키>
```

규칙 다섯.

1. **`WHERE` 는 3번 칸 앞, `HAVING` 은 3번 칸 뒤다.** 나머지 전부가 이 한 줄에서 나온다.
2. **집계 함수는 `WHERE` 에 못 쓴다.** 그룹이 아직 없다. 두 엔진 모두 에러다.
3. **`HAVING` 의 비집계 열은 그룹 키만 허용된다.** 그 외 열은 거부된다 — 거부하는 *말*만 엔진마다 다르다.
4. **`HAVING` 에서 열 별칭은 MySQL 만 된다.** 이식성을 원하면 식을 그대로 적는다.
5. **`GROUP BY` 없이 `HAVING` 을 쓰면 표 전체가 한 그룹**이고, 그 그룹이 탈락하면 결과가 0행이다.

판단 규칙은 한 문장으로 줄어든다.

```text
이 조건을 판정하는 데 "같은 그룹의 다른 행"이 필요한가?
        │                              │
       아니오                          예
        ↓                              ↓
     WHERE                          HAVING
 (행 하나로 판정됨)            (그룹 전체를 봐야 판정됨)
```

## 어디서 틀리나

- **`WHERE` 와 `HAVING` 이 "같은데 성능만 다른 것"이라고 믿는다.**\
  `WHERE salary >= 400` 과 `HAVING MAX(salary) >= 400` 은 **다른 질문**이다. 위에서 `cnt` 가 1과 2로 갈렸다.\
  바꿔 써도 되는 것은 **조건이 그룹 키에 걸릴 때뿐**이다.
- **행 단위로 판정 가능한 조건을 `HAVING` 에 둔다.**\
  PG 에서는 옵티마이저가 내려 줘서 티가 안 난다. **MySQL 에서는 안 내려 준다** — 위 계획에서 그룹 3개를 다 만든 뒤 걸렀다.\
  엔진에 기대지 말고 **뜻이 같으면 `WHERE` 에 적는다.**
- **`HAVING` 에서 열 별칭을 쓴다.**\
  MySQL 로 개발하고 PG 로 배포하면 `column "cnt" does not exist` 로 깨진다. 식을 그대로 적으면 양쪽 다 돈다.
- **`HAVING` 이 `NULL` 을 통과시킬 거라 생각한다.**\
  `HAVING` 도 `TRUE` 만 통과시킨다. `MAX(salary)` 가 `NULL` 인 `dev` 부서는 `HAVING MAX(salary) >= 400` 에서 조용히 사라졌다([04번](../04-null-three-valued-logic/)).
- **`HAVING COUNT(*) = 0` 으로 "빈 그룹"을 찾으려 한다.**\
  `GROUP BY` 는 **행이 있는 그룹만** 만든다. 행이 0개인 그룹은 애초에 생기지 않으므로 `COUNT(*) = 0` 은 영원히 안 맞는다.\
  「사원이 없는 부서」를 찾으려면 그룹이 아니라 조인이 필요하다 — [14번](../14-left-right-outer-join/)의 `LEFT JOIN ... WHERE 키 IS NULL`.
- **`GROUP BY` 없는 `HAVING` 이 0행을 줄 수 있다는 걸 모른다.**\
  애플리케이션이 "집계 질의는 항상 한 줄"을 가정하고 있으면 여기서 `NoResultException` 이 난다.
- **`WHERE` 에 집계를 쓰고 에러 메시지를 안 읽는다.**\
  `Invalid use of group function`(MySQL)·`aggregate functions are not allowed in WHERE`(PG) 는 **정확히 "그룹이 아직 없다"는 말**이다.

## 구현 세부사항 대 언어 보장

이 주제에는 **관찰한 것을 보장으로 착각하기 쉬운 자리**가 하나 있다.

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `WHERE` 는 그룹 만들기 **전**, `HAVING` 은 **후**에 판정된다 | **결과의 정의** | 언어 — 두 엔진 문서가 같은 모양으로 적는다 |
| `HAVING` 의 그룹 키 조건을 스캔 필터로 **내려 준다** | **옵티마이저의 재주** | 아무도 보장 안 함 — PG 18.6 은 내리고 MySQL 8.4.10 은 안 내렸다 |
| 그래서 "`HAVING` 은 항상 느리다" | **틀린 일반화** | PG 에서는 계획이 한 글자도 안 달랐다 |

- **결과는 논리적 순서가 정의한다.** 옵티마이저가 조건을 어디로 옮기든 **결과는 순서대로 계산한 것과 같아야** 한다([01번](../01-logical-query-processing-order/)).
- **비용은 엔진이 정한다.** 위 표 둘째 줄은 이 머신의 이 버전에서 관찰한 것이고, 버전이 오르면 달라질 수 있다.\
  다른 버전·다른 데이터 분포에서도 같으리라는 보장은 없다.
- 그래서 **적을 때는 뜻이 같은 쪽 중 싼 쪽(`WHERE`)에 적는다.** 옵티마이저를 믿는 것은 이식성 있는 습관이 아니다.
- 계획을 읽는 법 자체는 이 주제 밖이다 — [목록의 **58번 주제**](../58-explain-plan-tree/)·[**60번 주제**](../60-explain-analyze-estimates-vs-actuals/).

## 언제 쓰고 언제 안 쓰나

- **`WHERE` 를 쓴다 — 행 하나로 판정되는 모든 조건.** 기본값이다.\
  「급여가 400 이상인」·「입사일이 올해인」·「부서가 10번인」.
- **`HAVING` 을 쓴다 — 그룹 전체를 봐야 판정되는 조건.**\
  「인원이 2명 이상인 부서」·「급여 합이 1000 넘는 부서」·「최고 급여가 400 이상인 부서」.
- **둘 다 쓴다 — 흔하다.** 행을 먼저 좁히고(`WHERE`), 남은 것으로 그룹을 만든 뒤 그룹을 좁힌다(`HAVING`).\
  `WHERE dept_id IS NOT NULL ... GROUP BY dept_id HAVING COUNT(*) >= 2` 처럼.
- **`HAVING` 을 안 쓴다 — 그룹 키 조건.** 같은 답인데 MySQL 에서 더 비싸고, 읽는 사람도 헷갈린다.
- **`HAVING` 결과를 다시 거르고 싶으면** 한 겹 감싼다 — 파생 테이블로 만들면 바깥에서는 그냥 열이다([10번](../10-from-clause-aliases-derived-tables/)).

## 핵심 문장

- `WHERE` 는 **행**을 버리고 `HAVING` 은 **그룹**을 버린다. 사이에 `GROUP BY` 가 끼어 있다.
- 조건이 **그룹 키**에 걸리면 두 절의 결과가 같고, **집계**에 걸리면 애초에 `WHERE` 에 쓸 수 없다.\
  **결과가 갈리는 것은 「같은 뜻으로 보이는 다른 조건」을 양쪽에 쓸 때다** — `WHERE salary >= 400` 대 `HAVING MAX(salary) >= 400`.
- 비용은 **엔진이 정한다** — PG 18.6 은 그룹 키 조건을 스캔 필터로 내렸고, MySQL 8.4.10 은 안 내렸다.
- `HAVING` 도 **`TRUE` 만 통과**시킨다. `MAX` 가 `NULL` 인 그룹은 조용히 사라진다.
- `HAVING` 에서 **열 별칭은 MySQL 만** 된다. 식을 그대로 적으면 양쪽 다 돈다.
- `GROUP BY` 없는 `HAVING` 은 **표 전체를 한 그룹**으로 보고, 탈락하면 **0행**이 된다.

## 관련 자료

- [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) — `HAVING` 절의 정의와 출력 열 이름 규칙이 같은 페이지에 있다.
- [MySQL 8.4 · SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html)
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 여덟 칸 전체의 좌표계까지, 여기는 2번 칸과 4번 칸의 대비부터.**
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `UNKNOWN` 의 계산 규칙까지, 여기는 그 규칙이 `HAVING` 에서 어떻게 보이나부터.**
- [10 FROM 절 — 테이블 별칭·파생 테이블](../10-from-clause-aliases-derived-tables/) — `HAVING` 결과를 다시 거를 때 감싸는 방법.
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — 「행이 0개인 그룹」은 `HAVING` 이 아니라 외부 조인으로 찾는다.
- [15 OUTER JOIN 에서 ON 과 WHERE 의 차이](../15-on-vs-where-in-outer-join/) — **같은 「조건을 어디 두나」 문제의 조인판**이다.
- **`GROUP BY` 의 비집계 열 규칙**은 [목록의 **22번 주제**](../22-group-by-nonaggregated-columns/)가 정본이다 — 여기서는 `HAVING` 이 그 규칙을 그대로 받는다는 것까지만.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **`WHERE` 절** — 논리적 처리 순서 **2번 칸**. 행 하나씩 판정해 `TRUE` 인 행만 통과시킨다.\
  예: `WHERE salary >= 400` 은 `bob`(500)과 `dan`(400)만 남긴다.
- **`HAVING` 절** — 논리적 처리 순서 **4번 칸**. 그룹 하나씩 판정해 `TRUE` 인 그룹만 통과시킨다.\
  예: `HAVING COUNT(*) >= 2` 는 인원 2명 이상인 부서만 남긴다.
- **술어(predicate)** — 참/거짓을 판정하는 조건식.\
  예: `salary >= 400` 은 행 술어, `MAX(salary) >= 400` 은 그룹 술어다.
- **집계 함수(aggregate function)** — 여러 행을 값 하나로 접는 함수.\
  예: `COUNT(*)`·`SUM(salary)`·`MAX(salary)`.
- **그룹 키(group key)** — `GROUP BY` 에 적은 열. 그룹 안의 모든 행에서 값이 같다.\
  예: `GROUP BY dept_id` 면 `dept_id` 가 그룹 키이고, 그래서 `HAVING dept_id = 10` 이 허용된다.
- **비집계 열(non-aggregated column)** — 집계 함수로 감싸지 않은 열.\
  예: `HAVING salary >= 400` 의 `salary`. 그룹 키가 아니면 거부된다.
- **조건 내리기(predicate pushdown)** — 옵티마이저가 조건을 더 이른 단계로 옮기는 최적화.\
  예: PG 18.6 이 `HAVING dept_id = 10` 을 `Seq Scan` 의 `Filter` 로 내렸다. **보장이 아니라 재주다.**
- **`EXPLAIN ANALYZE`** — 질의를 실제로 돌리고 **계획과 실측 행 수**를 함께 보여 주는 명령.\
  예: `rows=2` 와 `rows=4` 의 차이가 「묶기 전에 버렸나 뒤에 버렸나」를 말해 준다.
- **임시 테이블(temporary table)** — MySQL 이 그룹 결과를 잠깐 담는 내부 저장소.\
  예: `Table scan on <temporary>` 가 계획에 뜨면 그룹을 **다 만든 뒤** 걸렀다는 뜻이다.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
  예: `MAX(salary)` 가 `NULL` 인 그룹에서 `NULL >= 400` 은 `UNKNOWN` 이고, `HAVING` 은 그 그룹을 버린다.
