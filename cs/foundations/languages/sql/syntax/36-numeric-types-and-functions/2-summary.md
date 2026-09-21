# sql/36-수치 타입과 수치 함수 (정수 나눗셈·반올림·정밀도) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Numeric Types](https://www.postgresql.org/docs/18/datatype-numeric.html) · [PostgreSQL 18 · Mathematical Functions](https://www.postgresql.org/docs/18/functions-math.html) · [MySQL 8.4 · Numeric Types](https://dev.mysql.com/doc/refman/8.4/en/numeric-types.html) · [MySQL 8.4 · Arithmetic Operators](https://dev.mysql.com/doc/refman/8.4/en/arithmetic-functions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **설정 조건** — MySQL `sql_mode` = `ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION`(기본값) · `div_precision_increment` = 4(기본값).\
> **버전** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 두 매뉴얼·릴리스 노트에서 찾지 못해 **버전을 적지 않는다.**\
> **선행** — [35 타입 체계와 캐스팅](../35-type-system-and-casting/)

## 한눈에 — 쉽게 말하면

**수치 타입은 「어디까지 정확할 것인가」를 미리 고르는 일이다.**

- **`INTEGER`** — 소수점이 없다. 나누면 **소수가 사라진다.**
- **`NUMERIC` / `DECIMAL`** — 십진수를 **자릿수 그대로** 담는다. 돈에 쓴다.
- **`FLOAT` / `DOUBLE`** — 빠르고 범위가 넓다. 대신 **`0.1` 이 정확히 `0.1` 이 아니다.**

```text
0.1 + 0.2 를 던졌다

NUMERIC 으로 계산하면                 DOUBLE 로 계산하면
─────────────────                     ──────────────
 0.3                                   0.30000000000000004
  ↑                                     ↑
십진수 자릿수를 그대로 더한다           2진 분수로 근사한 값을 더한다
= 0.3 과 비교하면 참                   = 0.3 과 비교하면 거짓
```

| 비유 | 실체 |
|---|---|
| 자로 재면서 「mm 까지만」이라고 정한다 | 타입을 고른다 |
| 눈금이 아예 없는 자(정수) | `INTEGER` — 나눗셈에서 소수가 버려진다 |
| mm 눈금이 새겨진 자 | `NUMERIC(p,s)` — 자릿수가 명시돼 있다 |
| 「대충 이쯤」을 아주 빠르게 재는 도구 | `DOUBLE` — 근사값이고 오차가 쌓인다 |

> **정밀도(precision)와 스케일(scale)** — `NUMERIC(5,2)` 는 **전체 5자리, 소수점 아래 2자리**라는 뜻이다.\
> 예: `123.45` 는 들어가고 `1234.5` 는 전체 자릿수를 넘어 거부된다.

그리고 **엔진이 갈리는 자리는 딱 두 종류**다.

```text
(가) 같은 문장이 다른 타입을 돌려준다
     SELECT 7/2;   PG -> 3 (정수)      MySQL -> 3.5000 (DECIMAL)

(나) 같은 사고에서 한쪽만 죽는다
     SELECT 1/0;   PG -> ERROR         MySQL -> NULL + 경고 1365
     2147483647+1  PG -> ERROR         MySQL -> 2147483648
```

## 이 주제가 답하려는 질문

1. **정수끼리 나누면 소수는 어디로 가나?** — 그리고 두 엔진이 왜 다른 답을 내나.
2. **`0.5` 를 반올림하면 `1` 인가 `0` 인가?** — 무엇이 그 답을 정하나.
3. **정밀도가 넘치거나 0 으로 나누면 무슨 일이 생기나?**

## 예시 데이터 — 이 묶음이 공유하는 것

이 주제는 표가 거의 필요 없다. 리터럴과 `CAST` 만으로 전부 재현된다.\
열 타입이 관련된 실험만 임시 표를 쓰고, **트랜잭션으로 감싸 롤백했다.**

```sql
CREATE TEMP TABLE t36b (d numeric(5,2));           -- PG
CREATE TEMPORARY TABLE t36b (d DECIMAL(5,2));      -- MySQL
```

`emp`·`dept` 는 읽기만 하고 바꾸지 않는다.

## 동작 방식

### 1. ★ 정수 나눗셈 — 같은 문장, 다른 타입

**언제 쓰나** — 비율·평균을 `/` 로 계산할 때. **이 주제에서 가장 흔한 사고다.**

```text
(입력) 7 / 2

PostgreSQL 18.6                      MySQL 8.4.10
─────────────                        ────────────
양쪽이 integer 다                     / 는 언제나 DECIMAL 을 돌려준다
       ↓                                     ↓
integer 나눗셈 -> 0 방향으로 절단       스케일을 붙여 계산한다
       ↓                                     ↓
      3                                   3.5000
```

```text
### SQL: SELECT 7/2 AS a, 5/2 AS b, -5/2 AS c, 1/3 AS d;
--- PG 18.6 ---
 a | b | c  | d 
---+---+----+---
 3 | 2 | -2 | 0
(1 row)

--- MySQL 8.4.10 ---
+--------+--------+---------+--------+
| a      | b      | c       | d      |
+--------+--------+---------+--------+
| 3.5000 | 2.5000 | -2.5000 | 0.3333 |
+--------+--------+---------+--------+
```

그림 해설 — PG 의 `-5/2` 가 `-3` 이 아니라 **`-2`** 인 것을 보라. 내림이 아니라 **0 방향 절단**이다.\
대가 — `SELECT count_a / count_b` 로 비율을 뽑으면 PG 에서는 **거의 항상 0 이나 1** 이 나온다.

MySQL 에서 PG 처럼 자르려면 **다른 연산자**를 쓴다.

```text
### SQL: SELECT 7 DIV 2 AS a, -5 DIV 2 AS b;
--- PG 18.6 ---
ERROR:  syntax error at or near "2"
LINE 1: SELECT 7 DIV 2 AS a, -5 DIV 2 AS b;
                     ^
--- MySQL 8.4.10 ---
+------+------+
| a    | b    |
+------+------+
|    3 |   -2 |
+------+------+
```

**PG 에서 MySQL 처럼 소수를 얻으려면 한쪽을 십진수로 만든다.**

```text
### SQL: SELECT 3/5 AS a, 3.0/5 AS b, 3.00/5 AS c, 10/4 AS d;
--- PG 18.6 ---
 a |           b            |           c            | d 
---+------------------------+------------------------+---
 0 | 0.60000000000000000000 | 0.60000000000000000000 | 2
(1 row)

--- MySQL 8.4.10 ---
+--------+---------+----------+--------+
| a      | b       | c        | d      |
+--------+---------+----------+--------+
| 0.6000 | 0.60000 | 0.600000 | 2.5000 |
+--------+---------+----------+--------+
```

그림 해설 — **소수 자릿수마저 다르다.** PG 는 `numeric` 나눗셈에 20자리를 붙이고,\
MySQL 은 **「피제수의 스케일 + `div_precision_increment`(기본 4)」**만큼 붙인다.\
`3/5` 는 피제수 스케일이 0 이라 `0.6000`, `3.0/5` 는 1 이라 `0.60000` 이다.

```text
--- MySQL 8.4.10 ---
SELECT @@div_precision_increment;
+---------------------------+
| @@div_precision_increment |
+---------------------------+
|                         4 |
+---------------------------+

CREATE TEMPORARY TABLE tt AS SELECT 3/5 AS a;
DESCRIBE tt;
+-------+--------------+------+-----+---------+-------+
| Field | Type         | Null | Key | Default | Extra |
+-------+--------------+------+-----+---------+-------+
| a     | decimal(5,4) | YES  |     | NULL    | NULL  |
+-------+--------------+------+-----+---------+-------+
```

대가 — 자릿수가 **설정에 달려 있다.** `div_precision_increment` 를 바꾼 서버에서는 같은 질의가 다른 자릿수를 낸다.

### 2. `NUMERIC` 대 `FLOAT` — `0.1 + 0.2` 로 재 본다

**언제 쓰나** — 돈·수량을 더할 때. 잘못 고르면 **총합이 1원씩 어긋난다.**

먼저 리터럴. **소수 리터럴은 두 엔진 다 십진수다**(35번 7번 참조).

```text
### SQL: SELECT 0.1 + 0.2 AS r;
--- PG 18.6 ---
  r  
-----
 0.3
(1 row)

--- MySQL 8.4.10 ---
+-----+
| r   |
+-----+
| 0.3 |
+-----+
```

같은 식을 부동소수로 바꾸면 **두 엔진이 똑같이 어긋난다.**

```text
### SQL: SELECT CAST(0.1 AS DOUBLE PRECISION) + CAST(0.2 AS DOUBLE PRECISION) AS r;
--- PG 18.6 ---
          r          
---------------------
 0.30000000000000004
(1 row)

--- MySQL 8.4.10 ---
+---------------------+
| r                   |
+---------------------+
| 0.30000000000000004 |
+---------------------+
```

그림 해설 — **여기는 방언이 아니다.** 두 엔진이 같은 IEEE 754 배정밀도를 쓰기 때문이다.\
왜 `0.1` 이 정확히 담기지 않는지는 [`foundations/data-representation`](../../../../data-representation/)이 정본이고,\
여기서는 **그 결과가 SQL 질의에서 어떻게 드러나는지**만 본다.

비교에 넣으면 행이 사라진다.

```text
### SQL: SELECT CAST(0.1 AS DOUBLE PRECISION) + CAST(0.2 AS DOUBLE PRECISION) = 0.3 AS eq;
--- PG 18.6 ---
 eq 
----
 f
(1 row)

--- MySQL 8.4.10 ---
+----+
| eq |
+----+
|  0 |
+----+
```

**열에 담고 집계하면 같은 일이 조용히 일어난다.**

```text
(A) PostgreSQL 18.6                         (B) MySQL 8.4.10
BEGIN;                                       START TRANSACTION;
CREATE TEMP TABLE t36f                       CREATE TEMPORARY TABLE t36f
  (f float8, d numeric(4,2));                  (f DOUBLE, d DECIMAL(4,2));
INSERT INTO t36f VALUES (0.1,0.1),(0.2,0.2); INSERT INTO t36f VALUES (0.1,0.1),(0.2,0.2);
SELECT SUM(f) AS fsum, SUM(d) AS dsum        SELECT SUM(f) AS fsum, SUM(d) AS dsum
  FROM t36f;                                   FROM t36f;
ROLLBACK;                                    ROLLBACK;
--- 실제 출력 ---                            --- 실제 출력 ---
        fsum         | dsum                  +---------------------+------+
---------------------+------                 | fsum                | dsum |
 0.30000000000000004 | 0.30                  +---------------------+------+
(1 row)                                      | 0.30000000000000004 | 0.30 |
                                             +---------------------+------+
```

두 그림의 결론 — **두 엔진이 한 자리도 안 갈렸다.** 갈리는 것은 엔진이 아니라 **타입**이다.

그 합을 `WHERE` 에 넣으면 이렇게 된다.

```text
--- PG 18.6 ---                              --- MySQL 8.4.10 ---
SELECT COUNT(*) AS float_eq FROM             SELECT COUNT(*) AS float_eq FROM
  (SELECT SUM(f) AS s FROM t36f) x             (SELECT SUM(f) AS s FROM t36f) x
  WHERE s = 0.3;                               WHERE s = 0.3;
 float_eq                                    +----------+
----------                                   | float_eq |
        0                                    +----------+
(1 row)                                      |        0 |
                                             +----------+
SELECT COUNT(*) AS num_eq FROM               SELECT COUNT(*) AS num_eq FROM
  (SELECT SUM(d) AS s FROM t36f) x             (SELECT SUM(d) AS s FROM t36f) x
  WHERE s = 0.3;                               WHERE s = 0.3;
 num_eq                                      +--------+
--------                                     | num_eq |
      1                                      +--------+
(1 row)                                      |      1  |
                                             +--------+
```

대가 — **「합계가 0.3 인 행」이 `float` 열에서는 존재하지 않는다.** 에러도 경고도 없다.

오차는 **더할수록 쌓인다.** `0.1` 을 열 번 더해 봤다.

```text
### SQL: SELECT SUM(CAST(0.1 AS DOUBLE PRECISION)) AS f_sum,
###             SUM(CAST(0.1 AS DECIMAL(3,1))) AS d_sum FROM (열 행짜리 목록) s;
--- PG 18.6 ---
       f_sum        | d_sum 
--------------------+-------
 0.9999999999999999 |   1.0
(1 row)

--- MySQL 8.4.10 ---
+--------------------+-------+
| f_sum              | d_sum |
+--------------------+-------+
| 0.9999999999999999 |   1.0 |
+--------------------+-------+
```

그림 해설 — 열 번 더했더니 **1 보다 작아졌다.** 행이 백만 개면 어긋남도 그만큼 커진다.\
대가 — 돈에 `float` 을 쓰면 **대사(reconciliation)가 매번 실패**한다. `NUMERIC`/`DECIMAL` 을 쓴다.

### 3. ★ 반올림의 경계 — 갈리는 것은 **엔진이 아니라 타입**이다

**언제 쓰나** — `ROUND` 를 쓸 때마다. 그리고 「엔진마다 다르다」고 외우기 전에.

```text
### SQL: SELECT ROUND(0.5) AS a, ROUND(1.5) AS b, ROUND(2.5) AS c, ROUND(-0.5) AS d, ROUND(-2.5) AS e;
--- PG 18.6 ---
 a | b | c | d  | e  
---+---+---+----+----
 1 | 2 | 3 | -1 | -3
(1 row)

--- MySQL 8.4.10 ---
+---+---+---+----+----+
| a | b | c | d  | e  |
+---+---+---+----+----+
| 1 | 2 | 3 | -1 | -3 |
+---+---+---+----+----+
```

**한 자리도 안 갈렸다.** 소수 리터럴이 양쪽 다 십진수 타입이고, 십진수 반올림은 **0 에서 먼 쪽으로**(half away from zero) 간다.

같은 값을 부동소수로 바꾸면 **양쪽이 같이 바뀐다.**

```text
### SQL: SELECT ROUND(CAST(0.5 AS DOUBLE PRECISION)) AS a, ROUND(CAST(1.5 AS DOUBLE PRECISION)) AS b,
###             ROUND(CAST(2.5 AS DOUBLE PRECISION)) AS c, ROUND(CAST(3.5 AS DOUBLE PRECISION)) AS d;
--- PG 18.6 ---
 a | b | c | d 
---+---+---+---
 0 | 2 | 2 | 4
(1 row)

--- MySQL 8.4.10 ---
+---+---+---+---+
| a | b | c | d |
+---+---+---+---+
| 0 | 2 | 2 | 4 |
+---+---+---+---+
```

```text
십진수(NUMERIC / DECIMAL)           부동소수(DOUBLE PRECISION)
0.5 -> 1    1.5 -> 2   2.5 -> 3    0.5 -> 0    1.5 -> 2   2.5 -> 2   3.5 -> 4
  ↑                                   ↑
0 에서 먼 쪽으로                     가까운 짝수로 (banker's rounding)
```

두 그림의 결론 — **`ROUND(0.5)` 의 답은 엔진이 아니라 타입이 정한다.**\
같은 서버에서 `1` 도 나오고 `0` 도 나온다. 어느 쪽이 나올지는 **인자의 타입**에 달렸다.

> **짝수 반올림(banker's rounding)** — 정확히 절반일 때 **가까운 짝수** 쪽으로 보내는 규칙.\
> 예: `0.5 → 0`, `1.5 → 2`, `2.5 → 2`, `3.5 → 4`. 한 방향으로만 올리면 합계가 위로 치우치는 것을 막는다.

**자릿수를 지정하는 형태는 방언이다.**

```text
### SQL: SELECT ROUND(CAST(2.675 AS DOUBLE PRECISION), 2) AS a;
--- PG 18.6 ---
ERROR:  function round(double precision, integer) does not exist
LINE 1: SELECT ROUND(CAST(2.675 AS DOUBLE PRECISION), 2) AS a;
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+------+
| a    |
+------+
| 2.68 |
+------+
```

그림 해설 — **PG 에는 2인자 `round(double, int)` 자체가 없다.** 「부동소수를 소수 n자리로 반올림」이 의미가 없다는 입장이다.\
`numeric` 이면 두 엔진 다 된다.

```text
### SQL: SELECT ROUND(2.675, 2) AS a;
--- PG 18.6 ---
  a   
------
 2.68
(1 row)

--- MySQL 8.4.10 ---
+------+
| a    |
+------+
| 2.68 |
+------+
```

**올림·내림은 갈리지 않는다.**

```text
### SQL: SELECT CEIL(2.1) AS c, FLOOR(2.9) AS f, CEIL(-2.1) AS cn, FLOOR(-2.9) AS fn;
--- PG 18.6 ---
 c | f | cn | fn 
---+---+----+----
 3 | 2 | -2 | -3
(1 row)

--- MySQL 8.4.10 ---
+---+---+----+----+
| c | f | cn | fn |
+---+---+----+----+
| 3 | 2 | -2 | -3 |
+---+---+----+----+
```

`CEIL(-2.1)` 이 `-2` 인 것을 보라 — **올림은 「큰 쪽」이지 「0 에서 먼 쪽」이 아니다.**\
1번의 정수 나눗셈(`-5/2 → -2`)과 **방향이 다르다.**

### 4. 넘치면 — 한쪽만 죽는다

**언제 쓰나** — 큰 수를 더할 때, 그리고 열 정의를 정할 때.

```text
### SQL: SELECT 2147483647 + 1 AS r;
--- PG 18.6 ---
ERROR:  integer out of range
--- MySQL 8.4.10 ---
+------------+
| r          |
+------------+
| 2147483648 |
+------------+
```

그림 해설 — **MySQL 이 오버플로를 무시한 게 아니다.** 리터럴 `2147483647` 을 더 넓은 정수로 읽었을 뿐이다.\
PG 는 리터럴을 `integer` 로 굳혀서 `integer` 덧셈을 하다 범위를 넘었다.

**열에 담으면 양쪽 다 죽는다.**

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
BEGIN;                                      START TRANSACTION;
CREATE TEMP TABLE t36 (i int, ...);         CREATE TEMPORARY TABLE t36 (i int, ...);
INSERT INTO t36 VALUES (2147483647, ...);   INSERT INTO t36 VALUES (2147483647, ...);
UPDATE t36 SET i = i + 1;                   UPDATE t36 SET i = i + 1;
ROLLBACK;                                   ROLLBACK;
--- 실제 출력 ---                          --- 실제 출력 ---
ERROR:  integer out of range                ERROR 1264 (22003) at line 4:
                                              Out of range value for column 'i' at row 1
```

두 그림의 결론 — **열 타입이 걸리면 두 엔진이 같이 막아 준다.** 식만 계산할 때는 MySQL 이 통과시킨다.

자릿수가 넘칠 때도 마찬가지다.

```text
--- PG 18.6 ---
INSERT INTO t36b VALUES (12345.6);          -- t36b (d numeric(5,2))
ERROR:  numeric field overflow
DETAIL:  A field with precision 5, scale 2 must round to an absolute value less than 10^3.

--- MySQL 8.4.10 ---
INSERT INTO t36b VALUES (12345.6);          -- t36b (d DECIMAL(5,2))
ERROR 1264 (22003) at line 1: Out of range value for column 'd' at row 1
```

그림 해설 — PG 의 `DETAIL` 이 **왜 안 되는지까지 알려 준다.** 전체 5자리 중 2자리가 소수라 정수부는 3자리뿐이다.

**소수부가 넘치는 것은 에러가 아니라 반올림이다** — 양쪽 다 조용히 반올림한다.

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
CREATE TEMP TABLE t36b (d numeric(5,2));   CREATE TEMPORARY TABLE t36b (d DECIMAL(5,2));
INSERT INTO t36b VALUES                    INSERT INTO t36b VALUES
  (1.005),(1.015),(1.025),(123.456);         (1.005),(1.015),(1.025),(123.456);
SELECT * FROM t36b;                        SELECT * FROM t36b;
--- 실제 출력 ---                          --- 실제 출력 ---
   d                                       +--------+
--------                                   | d      |
   1.01                                    +--------+
   1.02                                    |   1.01 |
   1.03                                    |   1.02 |
 123.46                                    |   1.03 |
(4 rows)                                   | 123.46 |
                                           +--------+
```

두 그림의 결론 — **한 자리도 안 갈렸다.** 그리고 `1.005 → 1.01` 은 **짝수 반올림이 아니다** — 십진수라 0 에서 먼 쪽이다.

### 5. 0 으로 나누면 — PG 는 에러, MySQL 은 자리에 따라 다르다

**언제 쓰나** — 분모가 데이터에서 오는 모든 계산에서.

```text
### SQL: SELECT 1/0 AS r;
--- PG 18.6 ---
ERROR:  division by zero
--- MySQL 8.4.10 ---
+------+
| r    |
+------+
| NULL |
+------+
```

```text
### SQL: SELECT 1 % 0 AS r;
--- PG 18.6 ---
ERROR:  division by zero
--- MySQL 8.4.10 ---
+------+
| r    |
+------+
| NULL |
+------+
```

MySQL 의 `NULL` 에도 경고가 붙는다.

```text
--- MySQL 8.4.10 ---
SELECT 1/0 AS r;
SHOW WARNINGS;
+---------+------+---------------+
| Level   | Code | Message       |
+---------+------+---------------+
| Warning | 1365 | Division by 0 |
+---------+------+---------------+
```

**그런데 같은 식을 `INSERT` 에 쓰면 MySQL 도 죽는다.**

```text
--- MySQL 8.4.10 ---
START TRANSACTION;
CREATE TEMPORARY TABLE t36z (v INT);
INSERT INTO t36z VALUES (1/0);
ERROR 1365 (22012) at line 3: Division by 0
```

그림 해설 — `sql_mode` 에 `STRICT_TRANS_TABLES` 와 `ERROR_FOR_DIVISION_BY_ZERO` 가 **둘 다 켜져 있어야** 이렇게 된다.\
이 서버의 기본 `sql_mode` 에 둘 다 있다(머리말 참조).\
대가 — **`SELECT` 에서는 통과하고 `INSERT` 에서는 죽는다.** 조회로 검증한 식이 적재에서 터진다.

**양쪽 다 안전하게 쓰려면 분모를 `NULL` 로 만든다.**

```sql
SELECT total / NULLIF(cnt, 0) AS avg_v FROM ...;
```

`NULLIF` 자체는 목록의 **06번 주제**가 정본이다. `NULL` 이 퍼지는 규칙은 [04 NULL 의 3값 논리](../04-null-three-valued-logic/)다.

### 6. 갈리지 않는 것들 — 여기까지 외우면 과잉이다

**언제 쓰나** — 「SQL 수치는 전부 방언이다」라는 인상을 교정할 때.

```text
### SQL: SELECT ABS(-3) AS a, MOD(7,3) AS m, POWER(2,10) AS p, SQRT(2) AS s;
--- PG 18.6 ---
 a | m |  p   |         s          
---+---+------+--------------------
 3 | 1 | 1024 | 1.4142135623730951
(1 row)

--- MySQL 8.4.10 ---
+---+------+------+--------------------+
| a | m    | p    | s                  |
+---+------+------+--------------------+
| 3 |    1 | 1024 | 1.4142135623730951 |
+---+------+------+--------------------+
```

`SQRT(2)` 가 **마지막 자리까지 같다.** 두 엔진 모두 같은 부동소수 표현을 쓰기 때문이다.\
그리고 이것이 「여러 판이 같아도 보장은 아니다」의 반대 사례가 아님에 주의한다 —\
**같은 IEEE 754 배정밀도라는 근거가 있어서 같은 것**이지, 우연히 같은 것이 아니다.

## 문법 — 형태와 규칙

SQL 의 수치 문법은 형태가 단순하다. 외울 것은 **「어느 타입이 나오나」**다.

```sql
-- 나눗셈
a / b          -- PG: 양쪽 정수면 정수(0 방향 절단) / MySQL: 언제나 DECIMAL
a DIV b        -- MySQL 전용 정수 나눗셈. PG 는 구문 오류
a % b          -- 나머지 (양쪽 공통)

-- 반올림
ROUND(x)       -- 인자가 십진수면 0 에서 먼 쪽 / 부동소수면 짝수 반올림
ROUND(x, n)    -- PG 는 numeric 에만 있다. double 에 쓰면 함수 없음 에러

-- 타입 이름
NUMERIC(p,s) = DECIMAL(p,s)          -- 양쪽 공통
DOUBLE PRECISION                      -- 양쪽 공통 (MySQL 은 DOUBLE 도 된다)
```

규칙 일곱.

1. **`/` 의 결과 타입이 방언이다.** PG 는 피연산자를 따르고, MySQL 은 언제나 `DECIMAL` 이다.
2. **PG 의 정수 나눗셈은 0 방향 절단이다.** `-5/2 → -2`. 내림(`-3`)이 아니다.
3. **MySQL 의 나눗셈 자릿수는 `div_precision_increment`(기본 4)가 정한다.** 설정 의존이다.
4. **`ROUND` 의 경계는 인자 타입이 정한다.** 십진수는 0 에서 먼 쪽, 부동소수는 짝수 쪽.
5. **`ROUND(double, n)` 은 PG 에 없다.** `numeric` 으로 캐스팅하거나 MySQL 쪽 코드를 고친다.
6. **오버플로는 식에서 갈리고 열에서 같다.** 열 타입에 넣는 순간 양쪽 다 거부한다.
7. **0 나눗셈은 PG 가 늘 에러, MySQL 은 `SELECT` 에서 `NULL` · `INSERT` 에서 에러다.**

#### 방언 요약

| 자리 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `7/2` | `3` (정수 절단) | `3.5000` (DECIMAL) |
| `-5/2` | `-2` (0 방향) | `-2.5000` |
| `3/5` | `0` | **`0.6000`** (decimal(5,4)) |
| `3.0/5` | `0.60000000000000000000` | `0.60000` |
| 정수 나눗셈 전용 연산자 | 없음 — `/` 가 그 역할 | **`DIV`** |
| 나눗셈 자릿수 | numeric 은 20자리까지 | `피제수 스케일 + 4` (설정) |
| `ROUND(0.5)` | `1` | `1` — **같다** |
| `ROUND(0.5::double)` | `0` | `0` — **같다** |
| `ROUND(double, n)` | **없다** — 함수 없음 에러 | 된다 |
| `2147483647 + 1` | `ERROR: integer out of range` | `2147483648` |
| `int` 열 오버플로 | `ERROR: integer out of range` | `ERROR 1264` |
| `numeric(5,2)` 자릿수 초과 | `ERROR: numeric field overflow` + `DETAIL` | `ERROR 1264` |
| `SELECT 1/0` | `ERROR: division by zero` | `NULL` + 경고 1365 |
| `INSERT ... VALUES (1/0)` | `ERROR: division by zero` | `ERROR 1365` (strict 모드) |
| `0.1+0.2` (십진수) | `0.3` | `0.3` — **같다** |
| `0.1+0.2` (부동소수) | `0.30000000000000004` | `0.30000000000000004` — **같다** |

## 어디서 틀리나

- **`SELECT a / b` 로 비율을 뽑는다.**\
  PG 에서 둘 다 정수면 **거의 항상 0 이나 1** 이다. `a * 1.0 / b` 나 `CAST(a AS numeric) / b` 로 쓴다.
- **「MySQL 은 소수가 나오니까 안전하다」고 믿는다.**\
  자릿수가 `div_precision_increment` 에 묶여 있다. `1/3 → 0.3333` 은 **네 자리에서 잘린 값**이다.
- **「`ROUND(0.5)` 는 엔진마다 다르다」고 외운다.**\
  **엔진이 아니라 타입이다.** 같은 서버에서 `1` 도 나오고 `0` 도 나온다.
- **돈을 `float`/`double` 에 담는다.**\
  `0.1` 을 열 번 더하면 `0.9999999999999999` 다. 합계 비교가 영영 안 맞는다.
- **`WHERE 부동소수열 = 값` 을 쓴다.**\
  에러 없이 0행이다. 범위 비교(`BETWEEN v-eps AND v+eps`)로 바꾸거나 타입을 `NUMERIC` 으로 바꾼다.
- **`SELECT` 로 검증한 식을 그대로 `INSERT` 에 넣는다.**\
  MySQL 은 `1/0` 을 `SELECT` 에서 `NULL` 로 넘기고 `INSERT` 에서 `ERROR 1365` 로 죽인다.
- **`CEIL(-2.1)` 을 `-3` 으로 예상한다.**\
  올림은 **큰 쪽**이라 `-2` 다. 0 방향 절단(`-5/2 → -2`)과 **우연히 같은 값**이지만 규칙이 다르다.
- **MySQL 의 경고를 안 읽는다.**\
  1365(0 나눗셈)는 `NULL` 로만 보인다. `SHOW WARNINGS` 가 유일한 통로다(35번 10번 참조).
- **`ROUND(x, 2)` 를 MySQL 에서 PG 로 그대로 옮긴다.**\
  인자가 부동소수면 PG 는 **함수를 못 찾는다.** `ROUND(x::numeric, 2)` 로 고친다.

## 구현 세부사항 대 언어 보장

- **언어(문서)가 정한 것** — `/` 의 결과 타입, PG 정수 나눗셈의 절단 방향,\
  `NUMERIC(p,s)` 의 자릿수 초과 거부, 0 나눗셈의 처리, `DIV` 의 존재 여부. 두 매뉴얼의 수치 타입 페이지가 정본이다.
- **설정이 정하는 것** — **MySQL 나눗셈의 소수 자릿수**(`div_precision_increment`)와\
  **0 나눗셈이 에러가 되는지**(`sql_mode` 의 `STRICT_TRANS_TABLES`·`ERROR_FOR_DIVISION_BY_ZERO`).\
  이 문서의 출력은 머리말에 적은 **기본 `sql_mode`** 에서 나온 것이다. 설정이 다르면 답도 다르다.
- **하드웨어·표현이 정하는 것** — 부동소수의 자릿수와 짝수 반올림.\
  이것은 두 엔진의 선택이 아니라 **IEEE 754 배정밀도**의 성질이라, 두 엔진이 같은 값을 낸 것이 우연이 아니다.\
  표현 자체는 [`foundations/data-representation`](../../../../data-representation/)이 정본이다.
- **에러 코드 번호**(1264·1365)는 MySQL 구현의 것이다. 외울 것은 번호가 아니라 **「어디서 막고 어디서 안 막나」**다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 돈·수량에 `NUMERIC`/`DECIMAL`.** 자릿수를 명시하고, 합계가 정확히 맞아야 하는 모든 곳.
- **쓴다 — 과학 계산·통계에 `DOUBLE`.** 범위가 넓고 빨라야 하며, 마지막 자리가 중요하지 않을 때.
- **쓴다 — 비율 계산 전에 한쪽을 십진수로.** `count_a * 1.0 / count_b` 가 두 엔진에서 같은 뜻이 된다.
- **안 쓴다 — 부동소수를 `=` 로 비교.** 두 엔진 모두 0행이 나온다.
- **안 쓴다 — 정수 나눗셈으로 평균.** PG 에서 조용히 절단된다.
- **조심한다 — `DIV` 와 `::`.** 각각 MySQL·PG 전용이라 이식에서 문이 안 선다. 그래서 **안전한 편**이다.
- **조심한다 — `sql_mode` 가 다른 서버.** 개발 서버와 운영 서버의 `sql_mode` 가 다르면 **같은 `INSERT` 가 한쪽에서만 죽는다.**

## 핵심 문장

- **`SELECT 7/2` 는 PG 에서 `3`, MySQL 에서 `3.5000`** 이다 — 결과 타입 자체가 갈린다.
- PG 의 정수 나눗셈은 **0 방향 절단**이다. `-5/2 → -2`, 내림이 아니다.
- **`ROUND(0.5)` 의 답을 정하는 것은 엔진이 아니라 인자의 타입**이다 — 십진수 `1`, 부동소수 `0`.
- `0.1 + 0.2` 는 **십진수면 `0.3`, 부동소수면 `0.30000000000000004`** 이고, **두 엔진이 똑같다.**
- 오버플로는 **식에서 갈리고**(PG 에러 / MySQL 통과) **열에서 같다**(둘 다 거부).
- `1/0` 은 PG 에서 늘 에러, MySQL 에서 **`SELECT` 는 `NULL`(경고 1365) · `INSERT` 는 에러**다.
- MySQL 나눗셈의 자릿수는 **`div_precision_increment` 설정**이 정한다. `3/5` 는 `0.6000` 이다.
- 돈에 `float` 을 쓰면 **열 번만 더해도 어긋난다**(`0.9999999999999999`).

## 관련 자료

- [PostgreSQL 18 · Numeric Types](https://www.postgresql.org/docs/18/datatype-numeric.html) — `numeric` 의 자릿수 규칙과 부동소수의 경고.
- [PostgreSQL 18 · Mathematical Functions and Operators](https://www.postgresql.org/docs/18/functions-math.html) — `round` 의 인자 타입별 목록.
- [MySQL 8.4 · Numeric Data Types](https://dev.mysql.com/doc/refman/8.4/en/numeric-types.html) — `DECIMAL` 의 자릿수와 반올림.
- [MySQL 8.4 · Arithmetic Operators](https://dev.mysql.com/doc/refman/8.4/en/arithmetic-functions.html) — `/` 와 `DIV`, `div_precision_increment`.
- [`foundations/data-representation`](../../../../data-representation/) — **경계**: `0.1` 이 왜 2진수로 딱 떨어지지 않는지, 부호·지수·가수가 어떻게 놓이는지는 **거기가 정본**이고,\
  여기는 **그 표현이 SQL 질의 결과로 어떻게 드러나는가**만 다룬다. 비트 배치는 한 줄도 쓰지 않는다.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — 리터럴의 타입이 무엇으로 정해지는지는 거기.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `1/0` 이 `NULL` 이 된 뒤의 전파 규칙.
- [SQL 주제 목록](../README.md) — 06(`NULLIF`·`COALESCE`) · 21(집계 함수) · 45(`CHECK` 제약) 이 이웃이다.

## 용어 풀이

- **정수 나눗셈(integer division)** — 몫에서 소수를 버리는 나눗셈.\
  예: PG 의 `7/2` → `3`. MySQL 은 같은 뜻을 `7 DIV 2` 로 쓴다.
- **0 방향 절단(truncation toward zero)** — 소수를 버릴 때 **0 쪽으로** 보내는 것.\
  예: `-5/2` 가 `-3`(내림)이 아니라 `-2` 다.
- **정밀도(precision)·스케일(scale)** — `NUMERIC(5,2)` 의 5와 2. 전체 자릿수와 소수점 아래 자릿수.\
  예: 정수부는 3자리뿐이라 `12345.6` 은 거부된다.
- **부동소수(floating point)** — 값을 2진 분수의 근사로 담는 표현. 빠르고 범위가 넓지만 정확하지 않다.\
  예: `0.1` 을 열 번 더하면 `0.9999999999999999` 다.
- **짝수 반올림(banker's rounding)** — 정확히 절반일 때 가까운 짝수로 보내는 규칙.\
  예: 부동소수 `0.5 → 0`, `2.5 → 2`, `3.5 → 4`.
- **`div_precision_increment`** — MySQL 이 나눗셈 결과에 붙일 소수 자릿수를 정하는 설정(기본 4).\
  예: `3/5` 는 피제수 스케일 0 + 4 = `0.6000`.
- **`sql_mode`** — MySQL 의 동작을 바꾸는 플래그 모음. 엄격 모드가 여기 들어 있다.\
  예: `STRICT_TRANS_TABLES` 때문에 `INSERT INTO t VALUES (1/0)` 이 에러가 된다.
- **오버플로(overflow)** — 값이 타입의 범위를 벗어나는 것.\
  예: `int` 열에 `2147483648` 을 넣으면 `ERROR 1264`(MySQL) / `integer out of range`(PG).
- **경고 1365** — MySQL 이 0 으로 나눴다고 남기는 경고. 결과는 `NULL` 이다.\
  예: `SELECT 1/0` 뒤에 `SHOW WARNINGS` 를 치면 보인다.
- **`NULLIF(a, b)`** — `a` 와 `b` 가 같으면 `NULL`, 아니면 `a`.\
  예: `total / NULLIF(cnt, 0)` 은 분모가 0 일 때 에러 대신 `NULL` 을 만든다.

## 더 들어가면

- **PG 의 `numeric` 은 「십진 자릿수 배열」로 저장된다.** 그래서 자릿수가 늘면 연산이 느려지고,\
  `float8` 보다 수십 배 느린 경우가 흔하다. **정확성의 대가는 속도**다.
- **MySQL 의 `DECIMAL` 도 같은 성격이다.** 다만 나눗셈에서 자릿수를 설정으로 끊기 때문에,\
  **PG 보다 일찍 잘린 값**이 나온다. 연쇄 계산에서는 그 차이가 누적된다.
- **`FLOAT` 을 쓰되 안전하게 쓰는 법**은 「비교하지 않는 것」이다.\
  `=` 대신 범위로, 합계 검증은 십진수 열을 따로 두고 대조한다.
- **`ROUND` 이 아니라 「어디서 반올림할 것인가」가 진짜 설계 결정**이다.\
  행마다 반올림한 뒤 합치는 것과, 합친 뒤 한 번 반올림하는 것은 **결과가 다르다.** 요구사항이 정해야 할 자리다.
