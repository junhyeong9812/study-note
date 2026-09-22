# sql/08-ORDER BY — 정렬 키·NULL 위치·정렬 안정성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · SELECT · ORDER BY Clause](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · ORDER BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/order-by-optimization.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **반복 실행** — 동률 순서는 **각 엔진에서 같은 질의를 10회씩** 돌려 확인했다. 결과는 5절에 있다.\
> **버전** — `NULLS FIRST`/`NULLS LAST` 는 PG 에 있고 MySQL 8.4.10 에는 문법이 없다(`ERROR 1064`).\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/)(`ORDER BY` 가 7번 칸) · [04 NULL 의 3값 논리](../04-null-three-valued-logic/).

## 한눈에 — 쉽게 말하면

**`ORDER BY` 는 「줄을 세우는 규칙」이다. 규칙이 정하지 않은 것은 아무렇게나 된다.**

- 학생들을 **키 순서**로 세운다고 하자. 키가 같은 두 명은? **규칙이 말해 주지 않았다.**
- 오늘은 우연히 번호 순으로 섰고, 내일은 반대로 설 수 있다.\
  **「오늘 잘 섰다」가 「내일도 그렇다」를 뜻하지 않는다.**
- 그리고 **키를 안 잰 학생**은 어디에 세우나? 맨 앞인가 맨 뒤인가?\
  이것도 규칙이 말해 줘야 하는데, **말 안 하면 엔진이 자기 마음대로 정한다** — 그리고 두 엔진이 반대로 정했다.

| 비유 | 실체 |
|---|---|
| 키 순서로 세우기 | `ORDER BY salary` |
| 키가 같은 두 명의 앞뒤 | 동률(tie)의 순서 — **보장 없음** |
| 키를 안 잰 학생 | `NULL` |
| 안 잰 학생을 앞/뒤에 세우라는 지시 | `NULLS FIRST` / `NULLS LAST` |
| 그 지시를 안 했을 때 | 엔진 기본값 — **PG 는 뒤, MySQL 은 앞** |
| 번호까지 같이 부르기 | 마지막 정렬 키에 고유 열을 더하는 것 |

```text
ORDER BY salary            PG 18.6                MySQL 8.4.10
                           ---------              ------------
  emp 4행                   300                    NULL   <- NULL 이 작은 값
   300                      400                     300
   500                      500                     400
  NULL                     NULL   <- NULL 이        500
   400                             큰 값
```

이 줄 세우기가 **똑같은 구조로** `ORDER BY` 다.\
「페이지마다 같은 행이 또 나온다」·「PG 로 옮겼더니 `NULL` 이 맨 뒤로 갔다」가 전부 이 두 가지 빈칸에서 나온다.

> **정렬 안정성(sort stability)** — 값이 같은 행들의 **원래 순서가 유지되는가**.\
> 예: 안정 정렬이면 `ann`·`bob` 의 급여가 같을 때 입력 순서대로 나온다. **SQL 은 이것을 보장하지 않는다.**

> **동률(tie)** — 정렬 키의 값이 같아 순서를 정할 수 없는 행들.\
> 예: `ORDER BY dept_id` 에서 `dept_id = 10` 인 `ann`·`bob`.

## 이 주제가 답하려는 질문

1. **`NULL` 은 어디에 서나** — 그리고 왜 두 엔진이 반대로 정했나.
2. **값이 같은 행들의 순서는 보장되나** — 안 바뀌는 것을 열 번 봐도 보장이 아닌 이유.
3. **정렬 기준은 무엇이 정하나** — 같은 문자열이 엔진마다 다르게 줄 서는 이유.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들이 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

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

이 주제에서는 **`cho` 의 `salary NULL`** 이 「어디에 서나」를, **`ann`·`bob` 의 `dept_id = 10`** 이 「동률의 순서」를 맡는다.

## 동작 방식

### 1. `NULL` 의 기본 위치 — 두 엔진이 반대다

**언제 쓰나** — `NULL` 이 있을 수 있는 열로 정렬할 때마다. **즉 거의 항상.**

```text
PG: NULL 을 "가장 큰 값" 으로 본다     MySQL: NULL 을 "가장 작은 값" 으로 본다
  ASC  ->  300 400 500 NULL              ASC  ->  NULL 300 400 500
  DESC ->  NULL 500 400 300              DESC ->  500 400 300 NULL
```

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | salary                     +----+--------+
----+--------                    | id | salary |
  1 |    300                     +----+--------+
  4 |    400                     |  3 |   NULL |
  2 |    500                     |  1 |    300 |
  3 |   NULL                     |  4 |    400 |
(4 rows)                         |  2 |    500 |
                                 +----+--------+
```

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary DESC;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | salary                     +----+--------+
----+--------                    | id | salary |
  3 |   NULL                     +----+--------+
  2 |    500                     |  2 |    500 |
  4 |    400                     |  4 |    400 |
  1 |    300                     |  1 |    300 |
(4 rows)                         |  3 |   NULL |
                                 +----+--------+
```

그림 해설 — **`ASC` 든 `DESC` 든 `cho` 가 정확히 반대편에 선다.** 두 엔진 각자는 일관적이다(PG 는 항상 「큰 값」, MySQL 은 항상 「작은 값」).\
대가 — 「급여 상위 3명」을 `ORDER BY salary DESC LIMIT 3` 으로 뽑으면 **PG 에서는 1등이 `cho`(급여 모름)** 다. 에러 없이 리포트가 틀린다.

---

### 2. `NULLS FIRST`/`NULLS LAST` — PG 에만 있는 문법

**언제 쓰나** — `NULL` 위치를 **명시**할 때. 기본값에 기대지 않는 것이 이 주제의 첫 번째 처방이다.

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary NULLS FIRST;
--- PG 18.6 ---
 id | salary
----+--------
  3 |   NULL
  1 |    300
  4 |    400
  2 |    500
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NULLS FIRST' at line 1
```

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary DESC NULLS LAST;
--- PG 18.6 ---
 id | salary
----+--------
  2 |    500
  4 |    400
  1 |    300
  3 |   NULL
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NULLS LAST' at line 1
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `ASC` 기본 `NULL` 위치 | **맨 뒤** (큰 값 취급) | **맨 앞** (작은 값 취급) |
| `DESC` 기본 `NULL` 위치 | **맨 앞** | **맨 뒤** |
| `NULLS FIRST`/`NULLS LAST` | **있다** | **`ERROR 1064`** — 문법 없음 |

그림 해설 — PG 의 `DESC NULLS LAST` 결과가 **MySQL 의 `DESC` 기본값과 같다.** 즉 MySQL 기본값을 PG 에서 재현하려면 항상 한 마디를 더 써야 한다.\
대가 — 이 문법을 쓰면 PG 전용 질의가 된다. 양쪽에서 돌아야 하면 다음 절의 방법을 쓴다.

---

### 3. 양쪽에서 도는 `NULL` 위치 제어 — 키를 하나 더 만든다

**언제 쓰나** — 이식 가능한 질의를 쓸 때. **정렬 키를 하나 앞에 더 붙이는** 방식이다.

```text
ORDER BY (salary IS NULL), salary
          ^^^^^^^^^^^^^^^^
     TRUE/FALSE 가 나온다. FALSE(0) 가 앞, TRUE(1) 가 뒤
     -> NULL 인 행이 뒤로 간다 (NULLS LAST 와 같은 효과)
```

```text
### SQL: SELECT id, salary FROM emp ORDER BY (salary IS NULL), salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | salary                     +----+--------+
----+--------                    | id | salary |
  1 |    300                     +----+--------+
  4 |    400                     |  1 |    300 |
  2 |    500                     |  4 |    400 |
  3 |   NULL                     |  2 |    500 |
(4 rows)                         |  3 |   NULL |
                                 +----+--------+
```

`CASE` 로 쓰면 의도가 더 드러나고 순서도 마음대로 정할 수 있다.

```text
### SQL: SELECT id, name, salary FROM emp ORDER BY CASE WHEN salary IS NULL THEN 0 ELSE 1 END, salary DESC;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | salary              +----+------+--------+
----+------+--------             | id | name | salary |
  3 | cho  |   NULL              +----+------+--------+
  2 | bob  |    500              |  3 | cho  |   NULL |
  4 | dan  |    400              |  2 | bob  |    500 |
  1 | ann  |    300              |  4 | dan  |    400 |
(4 rows)                         |  1 | ann  |    300 |
                                 +----+------+--------+
```

그림 해설 — **두 엔진의 출력이 네 줄 모두 같다.** 기본값에 기대지 않았기 때문이다.\
대가 — 정렬 키가 하나 늘어 **인덱스 정렬을 못 쓰게 될 수 있다.** 큰 표에서는 계획을 확인한다(목록의 [**47**](../47-when-indexes-are-used/)·[**58**](../58-explain-plan-tree/)번 주제).

---

### 4. 여러 키·표현식·서수·별칭

**언제 쓰나** — 1차 키로 동률이 남을 때, 또는 계산한 값으로 줄 세울 때.

```text
ORDER BY dept_id DESC, salary ASC
         ^^^^^^^^^^^^  ^^^^^^^^^^
         1차 키         1차가 같을 때만 본다

방향은 키마다 따로 붙는다. DESC 하나가 뒤 전체에 걸리지 않는다
```

```text
### SQL: SELECT name FROM emp ORDER BY dept_id DESC, salary ASC;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 dan                             +------+
 cho                             | cho  |
 ann                             | ann  |
 bob                             | bob  |
(4 rows)                         | dan  |
                                 +------+
```

그림 해설 — 가운데 두 행(`ann`·`bob`)은 양쪽이 같다. **다른 것은 `dan`(`dept_id NULL`)의 자리뿐**이고, 그것도 1절의 규칙 그대로다.

`ORDER BY` 는 **7번 칸**이라 `SELECT` 목록에 없는 열도 쓸 수 있고(위 질의가 그 예다 — `dept_id`·`salary` 를 안 뽑았다), 표현식·서수·별칭도 받는다.

```text
### SQL: SELECT id, name FROM emp ORDER BY LENGTH(name) DESC, name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  1 | ann                        +----+------+
  2 | bob                        |  1 | ann  |
  3 | cho                        |  2 | bob  |
  4 | dan                        |  3 | cho  |
(4 rows)                         |  4 | dan  |
                                 +----+------+
```

(네 이름의 길이가 모두 3이라 1차 키로는 아무것도 안 갈리고, 2차 키 `name` 이 순서를 정했다.)

```text
### SQL: SELECT dept_id, COUNT(*) FROM emp GROUP BY 1 ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | count                 +---------+----------+
---------+-------                | dept_id | COUNT(*) |
      10 |     2                 +---------+----------+
      20 |     1                 |    NULL |        1 |
    NULL |     1                 |      10 |        2 |
(3 rows)                         |      20 |        1 |
                                 +---------+----------+
```

대가 — 서수는 `SELECT` 목록을 고치면 **조용히 다른 열을 가리킨다**([02번](../02-select-list-column-aliases/)).

> **`DISTINCT` 가 있으면 이 자유가 사라진다** — `ORDER BY` 키가 `SELECT` 목록 안에 있어야 한다([07번](../07-distinct-and-duplicate-removal/)).

---

### 5. ★ 동률의 순서는 보장되지 않는다 — 열 번 같아도

**언제 쓰나** — 정렬 키가 고유하지 않을 때. **페이지네이션 사고의 뿌리다.**

`ORDER BY dept_id` 에서 `ann`·`bob` 은 둘 다 `dept_id = 10` 이다. 누가 먼저 오나?

각 엔진에서 **같은 질의를 10회씩** 돌렸다.

```text
=== PG 18.6 — SELECT name FROM emp ORDER BY dept_id;  (10회) ===
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan

=== MySQL 8.4.10 — 같은 질의 (10회) ===
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
```

**10/10 동일했다. 그래도 보장이 아니다.**\
(`dan` 의 자리가 다른 것은 `NULL` 정렬 차이고, 우리가 볼 것은 `ann`·`bob` 의 앞뒤다.)

**「안 바뀌더라」가 보장이 아닌 이유를 반증으로 보인다.** 같은 `ORDER BY dept_id` 인데 **입력 순서만 바꾸면 동률의 순서가 뒤집힌다.**

```text
### SQL: SELECT name, dept_id FROM (SELECT * FROM emp ORDER BY id DESC) t ORDER BY dept_id;
--- PG 18.6 ---
 name | dept_id
------+---------
 bob  |      10       <- ann 과 bob 이 뒤바뀌었다
 ann  |      10
 cho  |      20
 dan  |    NULL
(4 rows)
--- MySQL 8.4.10 ---
+------+---------+
| name | dept_id |
+------+---------+
| dan  |    NULL |
| ann  |      10 |    <- MySQL 에서는 이 판에서 안 뒤바뀌었다
| bob  |      10 |
| cho  |      20 |
+------+---------+
```

```text
### SQL: SELECT name, dept_id FROM (SELECT * FROM emp ORDER BY name DESC LIMIT 4) t ORDER BY dept_id;
--- MySQL 8.4.10 ---
+------+---------+
| name | dept_id |
+------+---------+
| dan  |    NULL |
| bob  |      10 |      <- 이번엔 MySQL 에서도 뒤바뀌었다
| ann  |      10 |
| cho  |      20 |
+------+---------+
```

두 그림의 결론 — **바깥 `ORDER BY` 는 한 글자도 안 바뀌었는데 `ann`·`bob` 의 앞뒤가 달라졌다.**\
정렬 키가 같은 행들의 순서는 「**엔진이 그 행들을 어떤 순서로 집어넣었나**」를 따라간다. 질의문이 정하는 것이 아니다.\
대가 — **재현 실험이 「안 바뀐다」를 열 번 보여 줘도 보장이 안 된다.** 계획이 바뀌면 바뀐다.

> ⚠️ 위 두 실측에서 **PG 는 `ORDER BY id DESC` 만으로도 뒤집혔고, MySQL 은 `LIMIT` 이 붙은 판에서 뒤집혔다.**\
> MySQL 은 `LIMIT` 없는 파생 테이블의 `ORDER BY` 를 지키지 않아도 된다고 문서가 말한다 — 그래서 첫 판에서는 순서가 그대로였다.\
> **어느 쪽이든 결론은 같다** — 동률 순서는 질의문 밖의 사정으로 정해진다.

**처방은 하나다 — 마지막 정렬 키에 고유한 열을 더한다.**

```text
### SQL: SELECT name, dept_id FROM emp ORDER BY dept_id, name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | dept_id                  +------+---------+
------+---------                 | name | dept_id |
 ann  |      10                  +------+---------+
 bob  |      10                  | dan  |    NULL |
 cho  |      20                  | ann  |      10 |
 dan  |    NULL                  | bob  |      10 |
(4 rows)                         | cho  |      20 |
                                 +------+---------+
```

이제 `ann`·`bob` 의 앞뒤가 **질의문에 적혀 있다.** 계획이 어떻게 바뀌어도 같다.\
(`dan` 의 자리는 여전히 `NULL` 규칙을 따른다 — 그것까지 고정하려면 3절의 방법을 함께 쓴다.)

---

### 6. `ORDER BY` 가 없으면 순서는 아무 보장이 없다

**언제 쓰나** — 5절의 더 센 판. **데이터를 건드리기만 해도 순서가 바뀐다.**

PG 에서 **값을 바꾸지 않는 갱신**(`name = name`)을 한 번 하고 같은 질의를 다시 던졌다.

```text
--- (A) 갱신 전: ORDER BY 없는 SELECT ---
### SQL: SELECT id, name FROM emp;
--- PG 18.6 ---
 id | name
----+------
  1 | ann
  2 | bob
  3 | cho
  4 | dan
(4 rows)

--- UPDATE emp SET name = name WHERE id = 1;  (값은 그대로) ---

--- (B) 같은 질의를 다시 ---
### SQL: SELECT id, name FROM emp;
--- PG 18.6 ---
 id | name
----+------
  2 | bob
  3 | cho
  4 | dan
  1 | ann       <- ann 이 맨 뒤로 갔다
(4 rows)
```

(전부 트랜잭션 안에서 하고 `ROLLBACK` 했다. 롤백 후 다시 던지니 원래 순서로 돌아왔다.)

MySQL 에서 같은 절차를 밟으면 **순서가 그대로**였다 — `1 ann / 2 bob / 3 cho / 4 dan`.

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 갱신 후 `ORDER BY` 없는 순서 | **바뀐다**(`ann` 이 맨 뒤로) | 그대로 |

그림 해설 — **데이터의 값은 하나도 안 바뀌었다.** 바뀐 것은 저장 위치뿐인데 결과의 줄 순서가 달라졌다.\
PG 는 갱신된 행을 원래 자리에 두지 않고 새 자리에 쓰고, `ORDER BY` 가 없으면 그 순서가 그대로 나온다.\
MySQL(InnoDB)은 기본키로 묶인 구조라 제자리를 지킨 것이다.\
대가 — **「지금 잘 나온다」가 가장 위험한 근거다.** 운영 중 한 번의 `UPDATE` 로 순서가 바뀐다.

---

### 7. 정렬 기준 자체가 엔진마다 다르다 — collation

**언제 쓰나** — 문자열로 정렬·비교할 때. **숫자와 달리 「순서」가 설정에 달려 있다.**

네 문자열 `B`·`a`·`A`·`b` 를 같은 질의로 줄 세웠다.

```text
### SQL: SELECT x FROM (SELECT 'B' AS x UNION ALL SELECT 'a' UNION ALL SELECT 'A' UNION ALL SELECT 'b') t ORDER BY x;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 x                               +---+
---                              | x |
 a                               +---+
 A                               | a |
 b                               | A |
 B                               | B |
(4 rows)                         | b |
                                 +---+
```

**세 번째·네 번째가 다르다** — PG 는 `b`, `B`, MySQL 은 `B`, `b`.\
이유는 비교 자체가 다르기 때문이다.

```text
### SQL: SELECT 'a' < 'B' AS a_lt_B, 'A' = 'a' AS a_eq_A;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 a_lt_b | a_eq_a                 +--------+--------+
--------+--------                | a_lt_B | a_eq_A |
 t      | f                      +--------+--------+
(1 row)                          |      1 |      1 |
                                 +--------+--------+
```

| | PostgreSQL 18.6 (`en_US.utf8`) | MySQL 8.4.10 (`utf8mb4_0900_ai_ci`) |
|---|---|---|
| `'A' = 'a'` | **`f`** — 다른 값이다 | **`1`** — 같은 값이다 |
| `A`·`a` 의 정렬 | 사전순으로 나란히, 순서 고정 | **동률** — 순서는 보장 없음 |

그림 해설 — MySQL 기본 collation 은 **대소문자를 무시**(`ai_ci`)한다. 그래서 `A` 와 `a` 는 **동률**이고, 5절의 규칙이 그대로 적용된다 — **앞뒤가 보장되지 않는다.**\
대가 — 「이름순 정렬」이 두 엔진에서 다르게 나오고, MySQL 에서는 **같은 엔진 안에서도 보장이 없다.**\
(PG 쪽 출력 열 이름이 `a_lt_b` 로 소문자인 것은 별칭 접힘이다 — [02번](../02-select-list-column-aliases/).)

**`COLLATE` 로 기준을 명시하면 두 엔진이 같아진다.**

```text
### SQL: SELECT x FROM (SELECT 'B' AS x UNION ALL SELECT 'a' UNION ALL SELECT 'A' UNION ALL SELECT 'b') t ORDER BY x COLLATE "C";
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 x                               ERROR 1273 (HY000) at line 1: Unknown collation: 'C'
---
 A
 B
 a
 b
(4 rows)
```

```text
### SQL: SELECT x FROM (SELECT 'B' AS x UNION ALL SELECT 'a' UNION ALL SELECT 'A' UNION ALL SELECT 'b') t ORDER BY x COLLATE utf8mb4_bin;
--- PG 18.6 ---                                            --- MySQL 8.4.10 ---
ERROR:  collation "utf8mb4_bin" for encoding "UTF8" does    +---+
  not exist                                                 | x |
                                                            +---+
                                                            | A |
                                                            | B |
                                                            | a |
                                                            | b |
                                                            +---+
```

두 그림의 결론 — **`A B a b` 로 결과가 같아졌다.** 다만 **collation 이름 자체는 서로 못 알아본다** — `COLLATE` 절은 이식되지 않는다.\
collation 의 정본은 [39번](../39-collation/)이다. 여기서는 「**정렬 기준이 데이터 밖에 있다**」만 인출하면 된다.

## 문법 — 형태와 규칙

```sql
ORDER BY <식 | 별칭 | 서수> [ASC | DESC] [NULLS FIRST | NULLS LAST]
       , <식> [ASC | DESC] ...
```

규칙 여섯.

1. **`ORDER BY` 는 7번 칸이다.** `SELECT` 목록에 없는 열·별칭·서수를 다 쓸 수 있다(`DISTINCT` 가 없을 때).
2. **방향은 키마다 따로다.** `ORDER BY a, b DESC` 에서 `a` 는 `ASC` 다.
3. **`NULL` 기본 위치는 엔진이 정한다** — PG 는 큰 값, MySQL 은 작은 값.
4. **`NULLS FIRST`/`NULLS LAST` 는 PG 에만 있다.** MySQL 은 `ERROR 1064`.
5. **동률의 순서는 보장되지 않는다.** 고정하려면 **고유한 열을 마지막 키로** 더한다.
6. **`ORDER BY` 가 없으면 순서는 아무 보장이 없다.** 지금 맞는 것은 우연이다.

양쪽에서 도는 `NULL` 위치 제어는 **키를 하나 더 만드는 것**이다.

```sql
-- NULLS LAST 와 같은 효과 (양쪽 엔진)
ORDER BY (salary IS NULL), salary

-- NULLS FIRST 와 같은 효과 (양쪽 엔진)
ORDER BY CASE WHEN salary IS NULL THEN 0 ELSE 1 END, salary DESC
```

## 어디서 틀리나

- **`NULL` 기본 위치가 같을 거라 본다.**\
  PG 는 `ASC` 에서 맨 뒤, MySQL 은 맨 앞이다. 「상위 N명」 리포트가 **에러 없이** 틀린다.
- **`NULLS LAST` 를 MySQL 에 쓴다.**\
  `ERROR 1064` 다. `(salary IS NULL)` 키를 앞에 붙이는 방식으로 바꾼다.
- **동률 순서가 안정적이라고 믿는다.**\
  10회 돌려 같아도 보장이 아니다. 입력 순서가 바뀌면 뒤집히는 것을 위에서 봤다.
- **`ORDER BY` 없이 「대충 들어간 순서로 나오겠지」 한다.**\
  PG 에서는 **값 안 바뀌는 `UPDATE` 한 번**으로 순서가 바뀐다.
- **정렬 키가 고유하지 않은 채 페이지를 나눈다.**\
  같은 행이 두 페이지에 나오거나 아예 빠진다([09번](../09-limit-offset-keyset-pagination/)).
- **`DISTINCT` 와 함께 목록 밖의 열로 정렬한다.**\
  두 엔진 다 막는다. 「`ORDER BY` 는 뭐든 쓸 수 있다」는 `DISTINCT` 앞에서 깨진다([07번](../07-distinct-and-duplicate-removal/)).
- **문자열 정렬이 엔진과 무관하다고 본다.**\
  MySQL 기본 collation 은 대소문자를 무시한다 — `'A' = 'a'` 가 **참**이고, 둘의 순서는 **동률**이다.
- **`COLLATE` 절을 그대로 이식한다.**\
  이름이 서로 다르다. PG 의 `"C"` 는 MySQL 에서 `Unknown collation`, MySQL 의 `utf8mb4_bin` 은 PG 에서 `does not exist` 다.
- **`ORDER BY` 서수를 저장되는 질의에 쓴다.**\
  `SELECT` 목록을 고치면 조용히 다른 열로 정렬된다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `ORDER BY` 가 `SELECT` 밖의 열을 쓰는 것 | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| 방향이 키마다 따로인 것 | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| `NULL` 기본 위치 | **엔진 선택** | PG 뒤 / MySQL 앞 |
| `NULLS FIRST`/`LAST` 문법 | **PG 의 확장** | MySQL `ERROR 1064` |
| **동률의 순서** | **아무도 보장 안 한다** | 입력 순서를 바꾸니 뒤집혔다 |
| `ORDER BY` 없는 결과의 순서 | **아무도 보장 안 한다** | PG 는 `UPDATE` 후 바뀜 |
| 갱신된 행이 뒤로 가는 것 | **저장 구조 구현** | PG 는 바뀌고 MySQL 은 안 바뀜 |
| 문자열 비교·정렬 기준 | **collation 설정** | `'A' = 'a'` 가 PG `f` / MySQL `1` |

정리하면 — **「어느 키로 줄 세우나」만 언어 보장이고, 「같은 값끼리의 앞뒤」와 「`NULL` 의 자리」와 「문자열의 대소 관계」는 전부 밖에서 정해진다.**

## 언제 쓰고 언제 안 쓰나

- **결과의 순서가 의미를 가지면 `ORDER BY` 를 반드시 적는다.** 화면·API·페이지네이션·비교 테스트가 전부 여기 걸린다.
- **정렬 키에는 고유한 열을 마지막에 더한다.** 대개 기본키 한 열이면 된다. 비용은 거의 없고 사고 하나가 통째로 사라진다.
- **`NULL` 이 있을 수 있는 열이면 위치를 명시한다.** PG 전용이면 `NULLS LAST`, 이식이 필요하면 `(x IS NULL)` 키.
- **문자열 정렬이 계약이면 `COLLATE` 를 명시하거나 열 정의에서 고정한다.** 기본값에 기대면 환경마다 다르다.
- **정렬 없이 `LIMIT` 을 쓰지 않는다.** 「아무거나 하나」가 요구사항인 경우는 거의 없다([09번](../09-limit-offset-keyset-pagination/)).
- **큰 표에서는 정렬 키와 인덱스를 맞춘다.** 정렬 키를 표현식으로 감싸면 인덱스 정렬을 못 쓴다(목록의 [**46**](../46-index-definition-composite-partial-expression/)·[**47**](../47-when-indexes-are-used/)번 주제).

## 핵심 문장

- **`NULL` 기본 위치가 반대다** — PG 는 큰 값(`ASC` 에서 맨 뒤), MySQL 은 작은 값(맨 앞).
- **`NULLS FIRST`/`LAST` 는 PG 에만 있다.** 이식하려면 `(x IS NULL)` 키를 앞에 붙인다.
- **동률의 순서는 아무도 보장하지 않는다.** 10회 같아도 보장이 아니고, 입력 순서가 바뀌면 뒤집힌다.
- **`ORDER BY` 가 없으면 순서는 보장이 없다** — PG 는 값 안 바뀌는 `UPDATE` 한 번으로도 달라진다.
- **처방은 하나** — 마지막 정렬 키에 **고유한 열**을 더한다.
- **문자열의 대소 관계는 데이터가 아니라 collation 이 정한다** — MySQL 기본값은 `'A' = 'a'` 가 참이다.

## 관련 자료

- [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) — `ORDER BY` 와 `NULLS FIRST`/`LAST` 가 같은 페이지에 있다.
- [MySQL 8.4 · ORDER BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/order-by-optimization.html)
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 `ORDER BY` 가 7번 칸이라는 것까지, 여기는 그 칸이 무엇을 정하고 무엇을 안 정하나부터.**
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `NULL` 이 비교에서 `UNKNOWN` 이라는 것까지, 여기는 정렬에서 `NULL` 이 크고 작다는 별개 규칙부터.**
- [02 SELECT 목록과 열 별칭](../02-select-list-column-aliases/) — **경계: 그쪽은 `ORDER BY` 가 별칭을 본다는 것까지, 여기는 그래서 어떤 순서가 나오나부터.**
- [07 DISTINCT 와 중복 제거](../07-distinct-and-duplicate-removal/) — `DISTINCT` 가 있으면 `ORDER BY` 의 자유가 줄어든다. `DISTINCT ON` 의 대표 행도 여기 규칙에 걸린다.
- [09 LIMIT·OFFSET 와 키셋 페이지네이션](../09-limit-offset-keyset-pagination/) — **경계: 여기는 「순서가 안 정해진다」까지, 그쪽은 그 위에서 페이지를 자를 때 무엇이 깨지나부터.**
- [39 collation — 문자열 비교와 정렬의 기준](../39-collation/) — **경계: 그쪽이 collation 의 정본이고, 여기는 「정렬 기준이 데이터 밖에 있다」까지.**
- **정렬과 인덱스**는 목록의 **46·47번 주제**, **계획 읽기**는 [**58번 주제**](../58-explain-plan-tree/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **동률(tie)** — 정렬 키의 값이 같아 순서를 정할 수 없는 행들.\
  예: `ORDER BY dept_id` 에서 `dept_id = 10` 인 `ann`·`bob`.
- **정렬 안정성(sort stability)** — 값이 같은 행들의 원래 순서가 유지되는가.\
  예: SQL 은 이것을 보장하지 않는다. 파생 테이블의 순서를 바꾸니 `ann`·`bob` 이 뒤집혔다.
- **`NULLS FIRST` / `NULLS LAST`** — `NULL` 을 맨 앞/맨 뒤에 두라는 지시. PG 에만 있다.\
  예: `ORDER BY salary DESC NULLS LAST` 는 MySQL 의 `DESC` 기본 동작과 같아진다.
- **collation(조합 순서)** — 문자열의 비교·정렬 기준을 정하는 규칙 묶음.\
  예: MySQL 기본 `utf8mb4_0900_ai_ci` 는 대소문자를 무시해 `'A' = 'a'` 가 참이다.
- **`ai_ci`** — accent-insensitive · case-insensitive. 악센트와 대소문자를 무시한다는 표시.\
  예: 그래서 `A` 와 `a` 가 정렬에서 **동률**이 된다.
- **서수(ordinal)** — 이름 대신 쓰는 출력 열 번호.\
  예: `ORDER BY 2 DESC`. 목록을 고치면 다른 열을 가리킨다.
- **결정적 정렬(deterministic order)** — 같은 데이터면 언제나 같은 순서가 나오는 정렬.\
  예: 마지막 키에 기본키를 더하면 결정적이 된다.
- **키셋(keyset)** — 「마지막으로 본 행의 키」를 기준으로 다음 페이지를 뽑는 방식.\
  예: `WHERE id > 2 ORDER BY id LIMIT 2`. 정렬이 결정적이어야 성립한다([09번](../09-limit-offset-keyset-pagination/)).

## 더 들어가면

- **왜 표준이 동률 순서를 정하지 않았나.** 정하면 엔진이 **정렬 알고리즘을 자유롭게 고를 수 없다.** 병렬 정렬·해시 집계·인덱스 스캔은 모두 입력 순서를 흩뜨리고, 안정성을 요구하면 그중 상당수를 못 쓴다. **자유를 준 대가를 질의문이 치르는 구조**이고, 그래서 고유 키를 하나 더 적는 것이 계약을 완성하는 일이 된다.
- **PG 에서 `UPDATE` 후 순서가 바뀌는 것은 MVCC 의 부산물이다.** 갱신은 제자리 수정이 아니라 **새 판본을 쓰고 옛 판본을 죽은 것으로 표시**하는 일이라 새 위치가 생긴다. 순서가 바뀐 것은 버그가 아니라 저장 구조가 드러난 것이다. MVCC 의 정본은 [목록의 **56번 주제**](../56-isolation-levels-read-phenomena-mvcc/)다.
- **정렬은 조기 종료가 안 된다.** 「가장 큰 것 하나」를 알려면 전부 봐야 한다 — 그래서 `ORDER BY ... LIMIT 1` 도 정렬 자체는 다 한다. 예외는 **정렬 키에 인덱스가 있어서 이미 순서대로 읽을 수 있을 때**뿐이고, 그것이 [09번](../09-limit-offset-keyset-pagination/)의 키셋 페이지네이션이 서는 토대다.
