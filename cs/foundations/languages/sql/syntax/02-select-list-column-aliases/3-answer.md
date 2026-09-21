# sql/02-SELECT 목록과 열 별칭의 유효 범위 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> 문서 근거는 [PG 18 SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 SELECT](https://dev.mysql.com/doc/refman/8.4/en/select.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 별칭이 `WHERE` 에서는 안 보이고 `ORDER BY` 에서는 보이는 이유

**별칭은 5번 칸(`SELECT`)에서 만들어지는 이름이기 때문이다.** `WHERE` 는 2번 칸이라 그 이름이 아직 없고, `ORDER BY` 는 7번 칸이라 이미 있다.

```text
칸                무엇을 받나            annual 이 있나
────              ────────────          ──────────────
1 FROM            emp 테이블             없다
2 WHERE           행 집합                없다      <- "column annual does not exist"
3 GROUP BY        행 집합                (특례로 받아 준다)
4 HAVING          그룹 집합              엔진마다 다르다
5 SELECT          확정된 집합            ★ 여기서 태어난다
6 DISTINCT        출력 행                있다
7 ORDER BY        출력 행                있다      <- 쓸 수 있다
8 LIMIT           순서 있는 출력 행       있다
```

```text
### SQL: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 1: SELECT salary * 12 AS annual FROM emp WHERE annual > 4000;
                                                    ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'annual' in 'where clause'
```

```text
### SQL: SELECT salary * 12 AS annual FROM emp ORDER BY annual;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual                          +--------+
--------                         | annual |
   3600                          +--------+
   4800                          |   NULL |
   6000                          |   3600 |
   NULL                          |   4800 |
(4 rows)                         |   6000 |
                                 +--------+
```

에러 문구가 **「문법이 틀렸다」가 아니라 「그런 열이 없다」**인 것이 핵심이다.\
문장 구조는 완벽하고, **이름을 찾는 데 실패**한 것이다.

> **이름 해석(name resolution)** — 질의문에 적힌 이름이 무엇을 가리키는지 정하는 일.\
> 예: `WHERE annual` 은 그 시점의 후보 목록(테이블 열들)에서 `annual` 을 찾다가 실패한다.

---

### 2. `SELECT salary * 12 AS annual, annual / 12 AS back FROM emp;` 는 통과하는가

**아니다. 두 엔진 다 거부한다.**

```text
### SQL: SELECT salary * 12 AS annual, annual / 12 AS back FROM emp;
--- PG 18.6 ---
ERROR:  column "annual" does not exist
LINE 1: SELECT salary * 12 AS annual, annual / 12 AS back FROM emp;
                                      ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'annual' in 'field list'
```

**왜 그런가** — `SELECT` 목록의 항목들은 **서로 순서가 없다.** 한 칸 안에서 동시에 평가되는 식들이지, 위에서 아래로 실행되는 문장이 아니다.

```text
잘못된 머릿속 그림                      실제
─────────────                        ────
1) annual 을 계산한다                 SELECT 목록 = { salary*12, annual/12 }
2) 그 값으로 back 을 계산한다             두 식이 같은 시점에 평가된다
                                        -> 둘째 식이 첫째 식의 "이름"을 볼 방법이 없다
```

MySQL 이 에러 위치를 **`'field list'`**(= `SELECT` 목록)라고 찍는 것이 그 증거다.

고치는 법은 한 겹 감싸는 것이다.

```text
### SQL: WITH t AS (SELECT id, salary * 12 AS annual FROM emp)
         SELECT id, annual FROM t WHERE annual > 4000 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | annual                     +----+--------+
----+--------                    | id | annual |
  2 |   6000                     +----+--------+
  4 |   4800                     |  2 |   6000 |
(2 rows)                         |  4 |   4800 |
                                 +----+--------+
```

---

### 3. `ORDER BY salary` 와 `ORDER BY salary + 0` 의 행 순서

**출력**

```text
(A)
### SQL: SELECT id AS salary FROM emp ORDER BY salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
      1                          +--------+
      2                          |      1 |
      3                          |      2 |
      4                          |      3 |
(4 rows)                         |      4 |
                                 +--------+

(B)
### SQL: SELECT id AS salary FROM emp ORDER BY salary + 0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 salary                          +--------+
--------                         | salary |
      1                          +--------+
      4                          |      3 |
      2                          |      1 |
      3                          |      4 |
(4 rows)                         |      2 |
                                 +--------+
```

**왜 그런가** — 같은 글자 `salary` 가 (A)에서는 **별칭**, (B)에서는 **테이블 열 `emp.salary`** 를 가리킨다.

```text
(A) ORDER BY salary        홀로 선 이름 -> 출력 열 이름이 먼저 검사된다
    별칭 salary = emp.id   -> id 순: 1, 2, 3, 4

(B) ORDER BY salary + 0    식의 일부 -> 일반 이름 해석 -> emp.salary
    emp.salary 순:
      PG    300(ann=1), 400(dan=4), 500(bob=2), NULL(cho=3)   -> 1, 4, 2, 3
      MySQL NULL(cho=3), 300(1), 400(4), 500(2)               -> 3, 1, 4, 2
```

두 엔진이 (B)에서 서로 다른 줄 순서를 내는 것은 **`NULL` 의 정렬 위치 차이**다 — PG 는 `ASC` 에서 `NULL` 을 맨 뒤, MySQL 은 맨 앞에 둔다([08번](../08-order-by-null-position-stability/)). **이름 해석 자체는 양쪽이 같다.**

**외울 것은 「별칭은 홀로 선 이름일 때만 보인다」**이다.\
그래서 실무 규칙은 하나로 줄어든다 — **기존 열 이름과 같은 별칭을 붙이지 않는다.**

---

### 4. `GROUP BY salary` 에서 이름이 겹칠 때

**거부된다. 그리고 에러가 지목하는 열은 `dept_id` 다.**

```text
### SQL: SELECT dept_id AS salary, COUNT(*) AS c FROM emp GROUP BY salary ORDER BY 1;
--- PG 18.6 ---
ERROR:  column "emp.dept_id" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT dept_id AS salary, COUNT(*) AS c FROM emp GROUP BY sa...
               ^
--- MySQL 8.4.10 ---
ERROR 1055 (42000) at line 1: Expression #1 of SELECT list is not in GROUP BY clause and contains nonaggregated column 'study.emp.dept_id' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

**왜 그런가** — 에러가 `salary` 가 아니라 **`dept_id` 를 지목한 것이 답**이다.

```text
만약 GROUP BY salary 가 별칭으로 잡혔다면
   -> GROUP BY dept_id 와 같은 뜻
   -> SELECT dept_id 는 그룹 키니까 통과했어야 한다

실제로는 거부됐고, 에러가 dept_id 를 지목했다
   -> GROUP BY salary 가 emp.salary 로 잡혔다는 뜻
   -> 그러면 dept_id 는 묶이지 않은 열이 된다
```

즉 **`GROUP BY` 에서는 테이블 열이 별칭을 이긴다.** 겹치지 않을 때만 별칭이 잡힌다.

```text
### SQL: SELECT salary * 12 AS annual FROM emp GROUP BY annual ORDER BY annual;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual                          +--------+
--------                         | annual |
   3600                          +--------+
   4800                          |   NULL |
   6000                          |   3600 |
   NULL                          |   4800 |
(4 rows)                         |   6000 |
                                 +--------+
  -> annual 은 emp 에 없는 이름이라 별칭으로 잡힌다. 양쪽 다 통과
```

| 이름이 겹칠 때 이기는 쪽 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `ORDER BY` | **별칭** | **별칭** |
| `GROUP BY` | **테이블 열** | **테이블 열** |

(`only_full_group_by` 규칙 자체는 이 주제가 아니라 [22번](../22-group-by-nonaggregated-columns/)이다. 여기서는 **이름이 어느 쪽으로 해석됐는지의 증거**로만 쓴다.)

---

### 5. `HAVING cnt >= 1` — 두 엔진의 답과 이식 방향

**PG 18.6 은 에러, MySQL 8.4.10 은 정상 동작한다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 1;
--- PG 18.6 ---
ERROR:  column "cnt" does not exist
LINE 1: ..., COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 1;
                                                              ^
--- MySQL 8.4.10 ---
+---------+-----+
| dept_id | cnt |
+---------+-----+
|      10 |   2 |
|      20 |   1 |
|    NULL |   1 |
+---------+-----+
```

**이식 방향은 비대칭이다.**

```text
MySQL -> PG                         PG -> MySQL
    │                                   │
    ▼                                   ▼
 HAVING 별칭이 있으면 깨진다          깨지지 않는다
 (PG 가 더 좁다)                     (MySQL 이 상위집합)
```

**왜 그런가** — PG 문서는 출력 열 이름을 **`ORDER BY`·`GROUP BY` 에서만** 쓸 수 있고 `WHERE`·`HAVING` 에서는 식을 그대로 적어야 한다고 못박는다([SELECT 페이지](https://www.postgresql.org/docs/18/sql-select.html)). MySQL 은 `HAVING` 까지 넓혀 놓았다.

이식성을 원하면 **`HAVING COUNT(*) >= 1`** 처럼 식을 적는다. 양쪽 다 돈다.

---

### 6. `ORDER BY 3` 이 거부되는 이유

**출력 열이 둘뿐인데 세 번째를 가리켰기 때문이다.** 서수는 테이블 열 번호가 아니라 **출력 열 번호**다.

```text
### SQL: SELECT id, name FROM emp ORDER BY 3;
--- PG 18.6 ---
ERROR:  ORDER BY position 3 is not in select list
LINE 1: SELECT id, name FROM emp ORDER BY 3;
                                          ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column '3' in 'order clause'
```

```text
SELECT id, name FROM emp
       ^^  ^^^^
        1    2        <- 출력 열은 둘뿐이다. emp 에 열이 넷 있는 것과 무관하다
```

PG 는 「위치 3은 목록에 없다」, MySQL 은 「`3` 이라는 열을 모른다」로 말한다 — **표현이 다를 뿐 거부한다는 사실은 같다.**

서수가 위험한 진짜 이유는 이 에러가 아니라 **에러가 안 나는 경우**다.

```text
### SQL: SELECT * FROM (SELECT name, id FROM emp) t ORDER BY 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | id                       +------+----+
------+----                      | name | id |
 ann  |  1                       +------+----+
 bob  |  2                       | ann  |  1 |
 cho  |  3                       | bob  |  2 |
 dan  |  4                       | cho  |  3 |
(4 rows)                         | dan  |  4 |
                                 +------+----+
```

목록을 `(id, name)` 으로 바꾸면 **같은 `ORDER BY 2` 가 `name` 순**이 된다. 에러가 아니라 다른 정답이 나온다.

---

### 7. 중복 열 이름을 가진 파생 테이블 — 두 엔진의 답

**PG 18.6 은 결과를 돌려주고, MySQL 8.4.10 은 거부한다.**

```text
### SQL: SELECT * FROM (SELECT * FROM emp e JOIN dept d ON e.dept_id = d.id) t;
--- PG 18.6 ---
 id | name | dept_id | salary | id | name
----+------+---------+--------+----+-------
  1 | ann  |      10 |    300 | 10 | sales
  2 | bob  |      10 |    500 | 10 | sales
  3 | cho  |      20 |   NULL | 20 | dev
(3 rows)
--- MySQL 8.4.10 ---
ERROR 1060 (42S21) at line 1: Duplicate column name 'id'
```

**왜 그런가** — 검사 시점이 다르다.

```text
PG                                     MySQL
파생 테이블을 만든다 (중복 허용)         파생 테이블을 만들 때 열 이름을 검사한다
       ↓                                      ↓
바깥에서 id 를 부를 때 비로소 막는다      만드는 순간 거부한다
```

바깥에서 `id` 를 부르면 PG 도 막는다.

```text
### SQL: SELECT id FROM (SELECT * FROM emp e JOIN dept d ON e.dept_id = d.id) t;
--- PG 18.6 ---
ERROR:  column reference "id" is ambiguous
LINE 1: SELECT id FROM (SELECT * FROM emp e JOIN dept d ON e.dept_id...
               ^
--- MySQL 8.4.10 ---
ERROR 1060 (42S21) at line 1: Duplicate column name 'id'
```

**PG 쪽이 더 오래 버티는 만큼 사고가 더 멀리 간다.** 중간 단계에서는 잘 돌다가, 나중에 열 하나를 꺼내 쓰는 순간 터진다.

최상위 `SELECT` 에서는 양쪽 다 중복 이름을 허용한다 — 위 PG 출력의 `id`·`name` 이 두 번씩 나온 것이 그 증거다.\
고치는 법은 하나다 — **`*` 대신 열을 적고 별칭을 붙인다**(`e.id AS emp_id, d.id AS dept_id`).

---

### 8. `AS MyCol` 의 출력 열 이름

**출력**

```text
### SQL: SELECT id AS MyCol FROM emp ORDER BY id LIMIT 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 mycol                           +-------+
-------                          | MyCol |
     1                           +-------+
(1 row)                          |     1 |
                                 +-------+
```

**PG 는 `mycol`, MySQL 은 `MyCol` 이다.**

**왜 그런가** — PG 는 따옴표 없는 식별자를 **전부 소문자로 접는다.** MySQL 은 접지 않는다.

큰따옴표로 감싸면 PG 도 보존한다.

```text
### SQL: SELECT id AS "MyCol" FROM emp ORDER BY id LIMIT 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 MyCol                           +-------+
-------                          | MyCol |
     1                           +-------+
(1 row)                          |     1 |
                                 +-------+
```

> **식별자 접힘(identifier folding)** — 따옴표 없는 이름의 대소문자를 한쪽으로 통일하는 것.\
> 예: PG 는 `MyCol` → `mycol`. 그래서 `rs.getInt("MyCol")` 이 PG 에서만 못 찾는 사고가 난다.

실무 처방 — **이식할 질의의 별칭은 소문자로 쓴다.** 따옴표에 기대면 이번엔 MySQL 쪽 백틱과 어긋난다.

---

### 9. `AS from` 을 받아 주는 엔진

**PostgreSQL 18.6 만 받아 준다.**

```text
### SQL: SELECT id AS from FROM emp ORDER BY id LIMIT 1;
--- PG 18.6 ---
 from
------
    1
(1 row)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'from FROM emp ORDER BY id LIMIT 1' at line 1
```

**왜 그런가** — `AS` 뒤에 올 수 있는 낱말의 범위가 파서마다 다르다. PG 는 `AS` 직후를 넓게 받아 주고, MySQL 은 예약어를 막는다.

두 규칙을 합치면 이렇다.

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `AS MyCol` | `mycol` 로 접힘 | `MyCol` 보존 |
| `AS from` | **통과** | **`ERROR 1064`** |
| 안전한 선택 | 소문자 · 비예약어 | 소문자 · 비예약어 |

**외울 것은 어느 낱말이 예약어인지가 아니라 「예약어 목록이 엔진마다 다르다」**는 사실이다.\
목록을 외우는 대신 별칭에 평범한 소문자 이름을 쓰면 이 자리가 통째로 사라진다.

---

### 10. 별칭을 `WHERE` 에서 쓰고 싶을 때 고치는 법 둘

**(A) 식을 다시 적는다 · (B) 한 겹 감싼다.**

```sql
-- (A) 식을 다시 적는다
SELECT salary * 12 AS annual FROM emp WHERE salary * 12 > 4000;

-- (B) 한 겹 감싼다 — CTE 또는 파생 테이블
WITH t AS (SELECT id, salary * 12 AS annual FROM emp)
SELECT id, annual FROM t WHERE annual > 4000;
```

```text
### SQL: WITH t AS (SELECT id, salary * 12 AS annual FROM emp)
         SELECT id, annual FROM t WHERE annual > 4000 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | annual                     +----+--------+
----+--------                    | id | annual |
  2 |   6000                     +----+--------+
  4 |   4800                     |  2 |   6000 |
(2 rows)                         |  4 |   4800 |
                                 +----+--------+
```

**(B)가 통하는 이유도 처리 순서다.**

```text
바깥 질의의 칸        무엇을 하나
──────────────      ────────────
1 FROM   t          안쪽 질의를 통째로 끝낸다  <- 여기서 annual 이 "이미 있는 열"이 된다
2 WHERE  annual>... 그 열을 그냥 본다
```

안쪽의 5번 칸이 바깥의 **1번 칸 안에서** 먼저 끝난다. 그래서 바깥 2번 칸에는 `annual` 이 이미 존재한다.

**(A)와 (B)의 대가**

| | 대가 |
|---|---|
| (A) 식 반복 | 두 군데를 같이 고쳐야 한다. 한쪽만 고치면 **에러 없이 답이 틀린다** |
| (B) 감싸기 | 질의가 한 겹 깊어진다. 계획은 대개 같지만 엔진·버전에 따라 다를 수 있다 |

---

### 11. `SELECT id name FROM emp` — 쉼표를 빠뜨리면

**에러가 아니다. `name` 이 `id` 의 별칭이 되어, 열 이름은 `name` 인데 값은 `id` 인 결과가 나온다.**

```text
### SQL: SELECT id name FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
    1                            +------+
    2                            |    1 |
    3                            |    2 |
    4                            |    3 |
(4 rows)                         |    4 |
                                 +------+
```

**왜 그런가** — `AS` 는 생략할 수 있다. `id name` 은 `id AS name` 과 같은 뜻이다.

```text
적은 것            파서가 읽은 것
──────            ─────────────
SELECT id, name   두 항목: id, name
SELECT id name    한 항목: id AS name     <- 쉼표 하나 차이
```

**이것이 무음 실패다.** 에러도 경고도 없고, 열 이름이 `name` 이라서 결과만 봐서는 맞아 보인다.\
`emp` 의 `name` 은 문자열이고 `id` 는 정수라 여기서는 눈에 띄지만, 타입이 같으면 배포될 때까지 안 잡힌다.

별칭을 안 붙였을 때 열 이름이 어떻게 되는지도 같이 봐 두면 좋다.

```text
### SQL: SELECT salary * 12 FROM emp ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 ?column?                        +-------------+
----------                       | salary * 12 |
     3600                        +-------------+
     4800                        |        NULL |
     6000                        |        3600 |
     NULL                        |        4800 |
(4 rows)                         |        6000 |
                                 +-------------+
```

PG 는 `?column?`, MySQL 은 **식 문자열 자체**를 열 이름으로 쓴다. 결과를 이름으로 찾는 코드가 있으면 **별칭은 선택이 아니라 필수**다.

---

### 12. 이 주제에서 두 엔진의 결과가 다른 자리 넷

| # | 자리 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|---|
| 1 | `HAVING` 에서 별칭 | ✗ `column "cnt" does not exist` | ✓ 정상 출력 |
| 2 | 따옴표 없는 별칭의 대소문자 | `MyCol` → **`mycol`** | **`MyCol`** 보존 |
| 3 | 예약어 별칭 `AS from` | **통과** | **`ERROR 1064`** |
| 4 | 중복 열 이름 파생 테이블 | **만들어진다**(참조 시 `ambiguous`) | **정의 시 `ERROR 1060`** |

반대로 **같았던 자리**도 적어 둔다 — 이쪽이 더 많다.

- `WHERE` 에서 별칭 불가 — 양쪽 에러(문구만 다름).
- `SELECT` 목록 안에서 앞 별칭 참조 불가 — 양쪽 에러.
- `GROUP BY`·`ORDER BY` 에서 별칭 가능 — 양쪽 통과.
- 이름이 겹칠 때 `ORDER BY` 는 별칭이, `GROUP BY` 는 테이블 열이 이기는 것 — 양쪽 동일.
- 서수(`GROUP BY 1`·`ORDER BY 2`) 지원과 범위 밖 거부 — 양쪽 동일.
- `AS` 생략 — 양쪽 동일.

**그래서 이식 규칙은 셋으로 줄어든다** — `HAVING` 에는 식을 적고, 별칭은 **소문자 · 비예약어**로 쓰고, `SELECT *` 대신 열을 적는다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `WHERE` 별칭 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거** |
| `SELECT` 목록 내 별칭 참조 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거** |
| ★ 별칭 대 테이블 열 (3번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `ORDER BY salary` / `salary + 0` 대조 |
| `GROUP BY` 이름 충돌 (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러가 `dept_id` 를 지목한 것이 근거** |
| `HAVING` 별칭 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 01번의 결과를 재확인 |
| 서수 범위 밖 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거** |
| ★ 중복 열 이름 파생 테이블 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **목록 README 에 없던 방언 차이** |
| 별칭 대소문자 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 따옴표 유무 양쪽 |
| 예약어 별칭 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거** |
| CTE 로 감싸기 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 쉼표 누락 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **무음 실패** — 에러 없음 |
| 별칭 없는 열 이름 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `?column?` / 식 문자열 |

**구현 의존 항목** — 8·9번(식별자 접힘·예약어 목록)과 7번(검사 시점)은 **파서 구현**이다. 버전이 오르면 다시 찍어야 한다.\
특히 예약어 목록은 버전마다 늘어난다 — 「이 낱말은 되더라」를 외우지 말고 **평범한 소문자 이름**을 쓴다.

**언어 보장 항목** — 1·2·3·4·6·10·11번. 별칭이 `SELECT` 에서 태어난다는 것, 목록 항목 사이에 순서가 없다는 것,\
`ORDER BY` 는 별칭이 `GROUP BY` 는 테이블 열이 이긴다는 것, 서수가 출력 열 번호라는 것은 **두 엔진에서 같았다.**

**버전** — 이 주제에서 버전에 갈리는 것은 없다. 다음 버전에서는 **7·8·9번과 12번의 대조표만** 다시 돌리면 된다.
