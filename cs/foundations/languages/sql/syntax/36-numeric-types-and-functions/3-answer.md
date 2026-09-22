# sql/36-수치 타입과 수치 함수 (정수 나눗셈·반올림·정밀도) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다. **손계산으로 유도한 값은 하나도 없다.**\
> 표를 쓴 실험은 전부 트랜잭션으로 감싸 **롤백**했고, `emp`·`dept` 는 읽기만 했다.\
> **MySQL 조건** — `sql_mode` 기본값(`STRICT_TRANS_TABLES`·`ERROR_FOR_DIVISION_BY_ZERO` 포함) · `div_precision_increment` = 4.\
> 문서 근거는 [PG 18 Numeric Types](https://www.postgresql.org/docs/18/datatype-numeric.html) · [PG 18 Math Functions](https://www.postgresql.org/docs/18/functions-math.html) · [MySQL 8.4 Arithmetic Operators](https://dev.mysql.com/doc/refman/8.4/en/arithmetic-functions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. ★ 정수 나눗셈 — **PG 는 정수, MySQL 은 `DECIMAL`**

**출력**

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

**왜 그런가**

```text
PostgreSQL                          MySQL
피연산자 타입을 따른다               / 는 결과 타입이 정해져 있다
  integer / integer = integer          어떤 입력이든 DECIMAL
        ↓                                    ↓
  소수를 버린다 (0 방향)               소수 자릿수를 붙여 계산한다
        ↓                                    ↓
   7/2 -> 3,  -5/2 -> -2              7/2 -> 3.5000
```

**`-5/2` 가 `-2` 인 것이 요점이다.** 내림이면 `-3` 이어야 한다.\
PG 문서가 말하는 것은 **0 방향 절단**이다 — 양수는 내림처럼, 음수는 올림처럼 보인다.

`1/3 → 0` 이 실무에서 물린다. **비율이 전부 0 이 된다.**

MySQL 에서 PG 처럼 자르려면 연산자를 바꾼다.

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

**`DIV` 는 PG 에서 구문 오류다.** 서로 전용 문법이라 이식에서 조용히 지나가지 않는다.

---

### 2. 소수 자릿수 — **PG 는 20자리, MySQL 은 설정값이 정한다**

**출력**

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

**왜 그런가**

MySQL 은 결과 스케일을 「**피제수의 스케일 + `div_precision_increment`**」로 정한다.

```text
3    / 5   피제수 스케일 0  ->  0 + 4 = 4 자리  ->  0.6000
3.0  / 5   피제수 스케일 1  ->  1 + 4 = 5 자리  ->  0.60000
3.00 / 5   피제수 스케일 2  ->  2 + 4 = 6 자리  ->  0.600000
```

서버가 직접 확인해 준다.

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

`decimal(5,4)` — 스케일이 정확히 4다.

**PG 쪽은 피연산자에 소수점이 있으면 `numeric` 이 되고**, `numeric` 나눗셈은 훨씬 많은 자릿수를 남긴다.\
`3.0/5` 와 `3.00/5` 가 **같은 자릿수**인 것을 보라 — PG 는 피제수 스케일을 따라가지 않는다.

**이식할 때 무엇이 물리나** — 자릿수가 다르면 **`ROUND` 하기 전의 중간값이 달라진다.**\
연쇄 계산에서 마지막 자리가 어긋나는 사고가 여기서 난다.

> **스케일(scale)** — 소수점 아래 자릿수.\
> 예: `3.0` 의 스케일은 1, `3` 의 스케일은 0이다.

---

### 3. ★ `0.1 + 0.2` — **타입이 답을 정하고, 두 엔진은 같다**

**출력**

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

**왜 그런가**

소수 리터럴은 **두 엔진 다 십진수 타입**이다(35번 7번에서 `pg_typeof(1.5)` = `numeric`, MySQL `DESCRIBE` = `decimal(2,1)` 을 확인했다).\
십진수는 자릿수를 그대로 더하므로 `0.3` 이 나온다.

`DOUBLE PRECISION` 으로 바꾸면 **2진 분수 근사**가 된다. 두 엔진이 같은 IEEE 754 배정밀도를 쓰므로 **마지막 자리까지 같다.**

```text
십진수(numeric/decimal)              부동소수(double precision)
"0.1" 이라는 자릿수를 담는다          "0.1 에 가장 가까운 2진 분수" 를 담는다
       ↓                                     ↓
 0.1 + 0.2 = 0.3  (정확)              두 근사값을 더하면 0.3 의 근사값이 아니다
                                            ↓
                                      0.30000000000000004
```

왜 `0.1` 이 2진수로 딱 떨어지지 않는지는 [`foundations/data-representation`](../../../../data-representation/)이 정본이다.

**비교에 넣으면 행이 사라진다.**

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

**더할수록 쌓인다.** `0.1` 을 열 번 더했다.

```text
--- PG 18.6 ---                        --- MySQL 8.4.10 ---
       f_sum        | d_sum            +--------------------+-------+
--------------------+-------           | f_sum              | d_sum |
 0.9999999999999999 |   1.0            +--------------------+-------+
(1 row)                                | 0.9999999999999999 | 1.0   |
                                       +--------------------+-------+
```

열 번에 이미 1 보다 작다. **돈에 `float` 을 쓰면 안 되는 이유가 이 한 줄이다.**

---

### 4. ★ 반올림의 경계 — **엔진이 아니라 타입이 가른다**

**출력**

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

**왜 그런가**

```text
십진수 인자                          부동소수 인자
0.5 -> 1   1.5 -> 2   2.5 -> 3      0.5 -> 0   1.5 -> 2   2.5 -> 2   3.5 -> 4
-0.5 -> -1  -2.5 -> -3                ↑          ↑          ↑          ↑
   ↑                                  0          2          2          4
0 에서 먼 쪽으로                     가까운 짝수로
(half away from zero)                (banker's rounding)
```

**두 엔진이 네 값 모두 같았다.** 이 주제에서 가장 자주 오해되는 자리인데, **방언이 아니다.**

> **짝수 반올림(banker's rounding)** — 정확히 절반일 때 가까운 **짝수**로 보내는 규칙.\
> 예: 부동소수 `2.5 → 2`, `3.5 → 4`. 한쪽으로만 올리면 합계가 위로 치우치는 것을 막는다.

**갈리는 것은 2인자 형태다.**

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

PG 는 `round(numeric, int)` 만 갖고 있다. **「부동소수를 소수 n자리로」가 의미가 없다**는 입장이다.\
`numeric` 이면 둘 다 된다.

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

---

### 5. 넘치면 — **식에서 갈리고 열에서 같다**

**출력 (a) — 식만**

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

**출력 (b) — 열에 담아서**

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

**왜 그런가**

```text
(a) 리터럴의 타입이 다르다
    PG:    2147483647 을 integer 로 굳힌다 -> integer 덧셈 -> 범위 초과 -> ERROR
    MySQL: 더 넓은 정수로 읽는다           -> 덧셈이 그냥 된다 -> 2147483648

(b) 열 타입이 int 로 고정돼 있다
    양쪽 다 int 에 안 들어가는 값이므로 -> 둘 다 거부
```

**MySQL 이 오버플로를 무시하는 엔진이 아니다.** (a)에서 통과한 것은 **오버플로가 아니었기 때문**이다.

**읽을 것** — 「MySQL 은 관대하다」는 요약은 여기서 틀린다.\
관대한 것은 **타입이 안 정해진 자리**뿐이고, 열 타입이 걸리면 두 엔진이 같이 막는다.

---

### 6. 0 으로 나누면 — **PG 는 늘 에러, MySQL 은 자리에 따라 다르다**

**출력 (a) — `SELECT`**

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
--- MySQL 8.4.10 ---
SELECT 1/0 AS r;
SHOW WARNINGS;
+---------+------+---------------+
| Level   | Code | Message       |
+---------+------+---------------+
| Warning | 1365 | Division by 0 |
+---------+------+---------------+
```

**출력 (b) — `INSERT`**

```text
--- MySQL 8.4.10 ---
START TRANSACTION;
CREATE TEMPORARY TABLE t36z (v INT);
INSERT INTO t36z VALUES (1/0);
ERROR 1365 (22012) at line 3: Division by 0
```

PG 는 (b)에서도 같은 `ERROR: division by zero` 다.

**왜 그런가**

```text
MySQL 의 sql_mode 가 갈림길이다
  SELECT 1/0                -> 값이 필요한 자리 -> NULL + 경고 1365
  INSERT ... VALUES (1/0)   -> 열에 쓰는 자리   -> STRICT_TRANS_TABLES 가 경고를 에러로 올린다
                                                  + ERROR_FOR_DIVISION_BY_ZERO
                                                  -> ERROR 1365
```

이 서버의 `sql_mode` 에 둘 다 들어 있다(머리말 참조). **설정이 다르면 (b)도 조용히 `NULL` 이 들어간다.**

**대가** — **조회로 검증한 식이 적재에서 터진다.** 반대 방향(적재는 되는데 조회가 틀림)보다는 낫지만,\
테스트를 `SELECT` 로만 하면 이 차이를 못 본다.

**양쪽에서 안전한 처방은 하나다.**

```sql
SELECT total / NULLIF(cnt, 0) AS avg_v FROM ...;
```

분모가 0 이면 `NULL` 이 되어 두 엔진 모두 에러 없이 `NULL` 을 돌려준다.\
`NULL` 이 그 뒤로 어떻게 퍼지는지는 [04 NULL 의 3값 논리](../04-null-three-valued-logic/)가 정본이다.

`%` 도 같다.

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

---

### 7. 자릿수가 넘치는 두 가지 — **소수부는 반올림, 정수부는 거부**

**출력 — 소수부 초과 (양쪽 다 조용히 반올림)**

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

**출력 — 정수부 초과 (양쪽 다 거부)**

```text
--- PG 18.6 ---
INSERT INTO t36b VALUES (12345.6);
ERROR:  numeric field overflow
DETAIL:  A field with precision 5, scale 2 must round to an absolute value less than 10^3.

--- MySQL 8.4.10 ---
INSERT INTO t36b VALUES (12345.6);
ERROR 1264 (22003) at line 1: Out of range value for column 'd' at row 1
```

**왜 그런가**

```text
NUMERIC(5, 2)
        ^  ^
        |  +-- 소수점 아래 2자리:  넘치면 반올림해서 담는다 (손실이지만 에러 아님)
        +----- 전체 5자리:        정수부는 5-2 = 3자리뿐. 넘으면 거부한다
```

PG 의 `DETAIL` 이 그 계산을 그대로 말해 준다 — `must round to an absolute value less than 10^3`.

**읽을 것 둘.**

- **소수부 초과는 에러가 아니다.** `1.005` 를 넣었는데 `1.01` 이 들어가 있다. **값이 조용히 바뀐다.**
- `1.005 → 1.01`, `1.025 → 1.03` 은 **짝수 반올림이 아니다.** 십진수라 0 에서 먼 쪽이다(4번과 같은 규칙).

---

### 8. 올림의 방향 — **`CEIL(-2.1)` 은 `-2` 다**

**출력**

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

**왜 그런가**

```text
수직선에 놓고 보면 헷갈리지 않는다

   -3      -2.9   -2.1   -2       0        2      2.1     2.9      3
   ─┼───────┼──────┼──────┼───────┼────────┼───────┼───────┼───────┼─>
    ^              ^      ^                        ^               ^
 FLOOR(-2.9)   CEIL(-2.1) 은 여기          CEIL(2.1) 은 저기 -> 3
   = -3        = -2 (더 큰 쪽)

CEIL  = 항상 오른쪽(큰 쪽)
FLOOR = 항상 왼쪽(작은 쪽)
```

**정수 나눗셈과 무엇이 다른가**

```text
-5/2 = -2.5 를 처리하는 세 규칙
  0 방향 절단 (PG 의 / )  -> -2     오른쪽으로 갔다
  내림      (FLOOR)      -> -3     왼쪽으로 갔다
  올림      (CEIL)       -> -2     오른쪽으로 갔다
```

`-5/2` 와 `CEIL(-2.5)` 이 **둘 다 `-2` 라서 같은 규칙처럼 보이지만 아니다.**\
양수에서 갈린다 — `5/2 = 2`(절단) 인데 `CEIL(2.5) = 3`(올림) 이다.

---

### 9. 부동소수 열을 `=` 로 못 찾는 이유

**출력**

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
(1 row)                                      |      1 |
                                             +--------+
```

(`t36f` 는 `(f float8/DOUBLE, d numeric(4,2)/DECIMAL(4,2))` 에 `(0.1,0.1),(0.2,0.2)` 두 행. 트랜잭션으로 감싸 롤백했다.)

**왜 그런가**

```text
저장된 값        WHERE 의 0.3
0.30000000000000004  vs  0.3     -> 다르다 -> 0행
      ↑
"0.1 의 근사 + 0.2 의 근사" 는
"0.3 의 근사" 와 같지 않다
```

**에러도 경고도 없다.** 질의는 정상 종료하고 **결과만 비어 있다.**\
35번 4번의 「20,000행을 훑고 0행」과 같은 종류의 사고다 — **조용한 0행.**

처방 셋.

1. **타입을 바꾼다.** 돈·수량이면 `NUMERIC`/`DECIMAL` 로. 이게 진짜 답이다.
2. **범위로 비교한다.** `WHERE s BETWEEN 0.3 - 1e-9 AND 0.3 + 1e-9`.
3. **반올림한 뒤 비교한다.** `WHERE ROUND(s::numeric, 2) = 0.30` — 단 **열에 함수를 씌우면 인덱스를 못 탄다**(35번 8번).

---

### 10. 이식할 때 조용한 자리 — **`/` 와 `ROUND` 의 인자 타입**

**대부분은 시끄럽다.**

| 옮기면 | 무슨 일이 | 조용한가 |
|---|---|---|
| `DIV` → PG | `syntax error at or near` | 시끄럽다 |
| `ROUND(double, n)` → PG | `function round(double precision, integer) does not exist` | 시끄럽다 |
| `2147483647 + 1` → PG | `integer out of range` | 시끄럽다 |
| `SELECT 1/0` → PG | `division by zero` | 시끄럽다 |
| **`a / b` (둘 다 정수)** | **답이 `3.5000` → `3` 으로 바뀐다** | **★ 조용하다** |
| **`a / b` 의 소수 자릿수** | **`0.6000` → `0.6000...0`(20자리)** | **★ 조용하다** |

**조용한 둘의 성격이 다르다.**

```text
(가) 정수 나눗셈 — 값이 통째로 바뀐다
     MySQL: SELECT 7/2  -> 3.5000
     PG:    SELECT 7/2  -> 3          <- 소수가 사라졌다. 에러 없음

(나) 자릿수 — 중간값이 달라진다
     MySQL: 3/5 -> 0.6000              (4자리)
     PG:    3.0/5 -> 0.6000...0        (20자리)
     -> 이 값을 다시 곱하고 반올림하면 마지막 자리가 어긋난다
```

**(가)를 찾는 방법**은 하나다 — **`/` 양쪽의 열 타입을 전부 확인한다.**\
둘 다 정수 타입이면 PG 에서 의미가 바뀐다. 처방은 `a * 1.0 / b` 나 `CAST(a AS numeric) / b` 다.

**반대 방향(PG → MySQL)은 덜 위험하다.** 정수 나눗셈이 소수 나눗셈이 되므로 **정보가 늘어나기** 때문이다.\
다만 `INT` 열에 담으면 다시 잘리므로, 적재 경로까지 봐야 한다.

---

### 11. 어떤 타입을 고르나

**한 줄 기준** — 「**마지막 자리가 틀리면 누가 화를 내나**」로 정한다.

| 용도 | 타입 | 이유 |
|---|---|---|
| 금액·수량·재고 | **`NUMERIC(p,s)` / `DECIMAL(p,s)`** | 합계가 정확히 맞아야 한다. `float` 은 열 번만 더해도 어긋난다(3번) |
| 식별자·카운트 | `INTEGER` / `BIGINT` | 소수가 의미 없다. 단 **`/` 로 나누는 순간 1번의 사고**가 난다 |
| 비율·백분율 (표시용) | `NUMERIC` 으로 계산 후 `ROUND` | 계산은 십진수로, 반올림은 **한 번만** |
| 과학·통계·좌표 | `DOUBLE PRECISION` | 범위가 넓고 빠르다. 마지막 자리가 중요하지 않은 영역 |
| 평균·표준편차 | `DOUBLE` 로 계산 가능 | 어차피 무리수다. 단 **표시 전에 반올림**한다 |

**고를 때 같이 정할 것 셋.**

1. **자릿수를 어디서 정하나.** `NUMERIC(p,s)` 의 `s` 는 **요구사항**이지 기술 선택이 아니다.\
   「원 단위인가 전 단위인가」를 사람이 답해야 한다.
2. **반올림을 몇 번 하나.** 행마다 반올림한 뒤 합치는 것과, 합친 뒤 한 번 반올림하는 것은 **결과가 다르다.**
3. **분모가 0 일 수 있나.** 있으면 `NULLIF` 를 **처음부터** 넣는다. 나중에 넣으면 6번의 (b)에서 터진다.

**`float` 을 고르면 따라오는 것**

```text
쓰지 말 것              대신 쓸 것
─────────               ─────────
WHERE f = 0.3           WHERE f BETWEEN 0.3-1e-9 AND 0.3+1e-9
SUM(f) 로 대사          SUM(numeric 열) 을 따로 두고 대조
GROUP BY f              반올림한 값을 열로 만들어 그걸로 묶는다
DISTINCT f              같은 이유로 위험하다 — 같아 보이는 값이 안 접힌다
```

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 정수 나눗셈 4식 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `-5/2 → -2` 확인 |
| `DIV` (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 구문 오류가 근거다** |
| 나눗셈 자릿수 4식 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `div_precision_increment` 조회 포함 |
| 결과 타입 `DESCRIBE` (2번) | MySQL 8.4.10 | 1회 | `decimal(5,4)` — `TEMPORARY` 표 |
| `0.1+0.2` 십진수·부동소수 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **두 엔진 동일** |
| `0.1` 열 번 합 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `0.9999999999999999` — **두 엔진 동일** |
| `ROUND` 십진수 5값 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 동일** |
| `ROUND` 부동소수 4값 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 동일** — 갈린 것은 타입 |
| `ROUND(double, n)` (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 함수 없음 에러가 근거다** |
| 식 오버플로 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 열 오버플로 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 트랜잭션 롤백 |
| `1/0` · `1%0` (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 경고 1365 포함 |
| `INSERT (1/0)` (6번) | MySQL 8.4.10 | 1회 | **`ERROR 1365` 가 근거다** |
| `numeric(5,2)` 반올림·초과 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG `DETAIL` 이 근거다** |
| `CEIL`·`FLOOR` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 동일** |
| `float` 열 `=` 비교 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **0행이 근거다** — 트랜잭션 롤백 |
| `ABS`·`MOD`·`POWER`·`SQRT` | PG 18.6 · MySQL 8.4.10 | 각 1회 | **마지막 자리까지 동일** |

**같은 값을 여러 번 돌린 이유** — 「두 엔진이 같다」를 주장하는 자리(3·4·7·8번)는 **확증이 아니라 반증을 찾기 위해** 반복했다.\
반복해도 갈리지 않았고, 갈릴 근거도 없다 — 두 엔진이 같은 IEEE 754 배정밀도와 같은 십진 반올림 규칙을 쓰기 때문이다.

**설정 의존 항목** — 2번(`div_precision_increment` = 4) · 6번의 (b)(`sql_mode` 의 `STRICT_TRANS_TABLES`·`ERROR_FOR_DIVISION_BY_ZERO`).\
**이 둘은 서버 설정이 바뀌면 답이 바뀐다.** 머리말에 적은 값에서 나온 결과다.

**구현·표현 의존 항목** — 3·4·9번의 부동소수 값.\
이것은 엔진의 선택이 아니라 **IEEE 754 배정밀도**의 성질이다. 표현 자체는 [`foundations/data-representation`](../../../../data-representation/)이 정본이다.

**언어 보장 항목** — 1·5·7·8번. `/` 의 결과 타입, 절단 방향, 자릿수 초과 처리, 올림·내림의 방향은 두 매뉴얼이 정한 것이다.

**버전을 적지 않은 이유** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 **두 매뉴얼에서도 릴리스 노트에서도 찾지 못했다.**

**DB 잔재** — 없다. 실험 표(`t36`·`t36b`·`t36f`·`t36z`·`tt`)는 전부 임시 표이거나 롤백됐고, `emp`·`dept` 는 읽기만 했다.
