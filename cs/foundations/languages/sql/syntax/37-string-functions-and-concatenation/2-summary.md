# sql/37-문자열 함수와 연결 연산 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · String Functions and Operators](https://www.postgresql.org/docs/18/functions-string.html) · [MySQL 8.4 · String Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/string-functions.html) · [MySQL 8.4 · Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **설정 조건** — PG `server_encoding` = `UTF8` · MySQL `character_set_server` = `utf8mb4`, 클라이언트도 `--default-character-set=utf8mb4` 로 붙였다.\
> MySQL `sql_mode` 는 기본값이고 **`PIPES_AS_CONCAT` 이 들어 있지 않다**(아래 1번에서 실제 값을 찍었다).\
> **버전** — 도입 버전이 확인된 것은 없어 **버전을 적지 않는다.** 단 MySQL 이 `||` 에 대해 내는 **deprecated 경고는 그대로 싣는다.**\
> **선행** — [35 타입 체계와 캐스팅](../35-type-system-and-casting/) · 이어지는 것은 [38 패턴 매칭](../38-pattern-matching-like-regex/) · [39 collation](../39-collation/)

## 한눈에 — 쉽게 말하면

**문자열 연산에서 두 엔진이 갈리는 자리는 셋이다.**

```text
(1) || 이 무엇인가
    PG:    'a' || 'b'  ->  'ab'      연결 연산자다
    MySQL: 'a' || 'b'  ->  0         ★ 논리 OR 다

(2) NULL 이 섞이면 CONCAT 이 무엇을 하나
    PG:    CONCAT('a', NULL)  ->  'a'     NULL 을 건너뛴다
    MySQL: CONCAT('a', NULL)  ->  NULL    ★ 통째로 NULL 이 된다

(3) LENGTH 가 무엇을 세나
    PG:    LENGTH('한글abc')  ->  5      글자 수
    MySQL: LENGTH('한글abc')  ->  9      ★ 바이트 수
```

| 비유 | 실체 |
|---|---|
| 종이 두 장을 풀로 붙인다 | 문자열 연결 |
| 같은 기호가 가게마다 다른 뜻 | `\|\|` 가 PG 에서는 연결, MySQL 에서는 OR |
| 한 장이 백지면 결과도 백지 | `NULL` 이 섞인 연결 — PG 의 `\|\|`, MySQL 의 `CONCAT` |
| 백지는 빼고 붙인다 | PG 의 `CONCAT` — `NULL` 을 건너뛴다 |
| 「몇 장인가」와 「몇 그램인가」 | 글자 수와 바이트 수 |

> **연결(concatenation)** — 문자열을 이어 붙이는 것.\
> 예: `'010'` 과 `'1234'` 를 붙여 `'0101234'` 로 만드는 것.

**(1)이 가장 위험하다.** 에러가 안 나고 **`0` 이라는 그럴듯한 값**이 나오기 때문이다.

```text
SELECT 'a' || 'b';   를 MySQL 에 던지면

'a' 를 수치로 읽는다 -> 0        (경고 1292)
'b' 를 수치로 읽는다 -> 0        (경고 1292)
0 OR 0                -> 0        (경고 1287: || 는 deprecated)
                          ↓
                    결과는 0 이다
```

세 경고가 다 남지만 **결과만 보면 아무 표시가 없다.**

## 이 주제가 답하려는 질문

1. **문자열을 붙이는 연산자는 무엇인가?** — 같은 기호가 다른 뜻이 되는 자리는 어디인가.
2. **`NULL` 이 섞이면 결과가 `NULL` 이 되나 무시되나?**
3. **`LENGTH` 는 무엇을 세나** — 글자인가 바이트인가.

## 예시 데이터 — 이 묶음이 공유하는 것

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

이 주제는 `dept.name`(문자열)과 `emp.salary`(`NULL` 이 있는 수치)를 읽기만 한다.\
멀티바이트 실험은 리터럴 `'한글abc'` 로 한다 — 표를 안 건드린다.

## 동작 방식

### 1. ★ `||` — 같은 기호, 다른 연산자

**언제 쓰나** — 문자열을 붙일 때. **이 주제에서 가장 비싼 차이다.**

```text
(입력) SELECT 'a' || 'b';

PostgreSQL 18.6                      MySQL 8.4.10
─────────────                        ────────────
|| 는 연결 연산자다                   || 는 논리 OR 의 비표준 동의어다
       ↓                                     ↓
   'a' 와 'b' 를 잇는다                'a' 와 'b' 를 불리언으로 읽는다
       ↓                                     ↓
      'ab'                            0 OR 0 -> 0
```

```text
### SQL: SELECT 'a' || 'b' AS r;
--- PG 18.6 ---
 r  
----
 ab
(1 row)

--- MySQL 8.4.10 ---
+---+
| r |
+---+
| 0 |
+---+
```

MySQL 은 **경고 셋**으로 말해 준다.

```text
--- MySQL 8.4.10 ---
SELECT 'a' || 'b' AS r;
SHOW WARNINGS;
+---------+------+--------------------------------------------------------------------+
| Level   | Code | Message                                                            |
+---------+------+--------------------------------------------------------------------+
| Warning | 1287 | '|| as a synonym for OR' is deprecated and will be removed in a    |
|         |      | future release. Please use OR instead                              |
| Warning | 1292 | Truncated incorrect DOUBLE value: 'a'                              |
| Warning | 1292 | Truncated incorrect DOUBLE value: 'b'                              |
+---------+------+--------------------------------------------------------------------+
```

(줄바꿈만 폭에 맞게 접었고, 문구는 서버가 낸 그대로다.)

그림 해설 — 1287 은 **「`||` 는 OR 이고, 그것도 없앨 예정」**이라는 뜻이고,\
1292 둘은 35번에서 본 **문자열→수치 변환 실패**다. 같은 사고의 조합이다.\
대가 — `SELECT last || first AS full_name` 이 MySQL 에서 **전부 `0`** 이 된다. 에러가 안 난다.

값이 수치로 읽히면 진짜 OR 이 된다.

```text
--- MySQL 8.4.10 ---
SELECT 1 || 0 AS a, 0 || 0 AS b, 'x' || 1 AS c;
+---+---+---+
| a | b | c |
+---+---+---+
| 1 | 0 | 1 |
+---+---+---+
```

`1 || 0` 이 `1` 인 것이 증거다 — **OR 이 맞다.**

**모드를 켜면 연결이 된다.** 다만 기본값에는 없다.

```text
--- MySQL 8.4.10 ---
SET SESSION sql_mode = CONCAT(@@sql_mode, ',PIPES_AS_CONCAT');
SELECT @@session.sql_mode\G
@@session.sql_mode: PIPES_AS_CONCAT,ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,
                    NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,
                    NO_ENGINE_SUBSTITUTION
SELECT 'a' || 'b' AS r_pipes;
+---------+
| r_pipes |
+---------+
| ab      |
+---------+
```

(줄바꿈만 폭에 맞게 접었다. `PIPES_AS_CONCAT` 이 앞에 붙은 것 말고는 기본값과 같다 — 즉 **기본에는 없었다.**)

대가 — **서버 설정에 의존하는 질의**가 된다. 같은 SQL 이 서버마다 다른 뜻이 되므로,\
이식할 코드에는 **`CONCAT()`** 을 쓴다. `CONCAT` 은 양쪽 다 있다.

```text
### SQL: SELECT CONCAT('a','b') AS r;
--- PG 18.6 ---
 r  
----
 ab
(1 row)

--- MySQL 8.4.10 ---
+------+
| r    |
+------+
| ab   |
+------+
```

수치를 섞으면 PG 의 `||` 가 문자열로 바꿔 붙인다.

```text
### SQL: SELECT 'a' || 1 AS r;
--- PG 18.6 ---
 r  
----
 a1
(1 row)

--- MySQL 8.4.10 ---
+---+
| r |
+---+
| 1 |
+---+
```

MySQL 의 `1` 은 `'a'`(→0) `OR` `1` = `1` 이다. **여기도 OR 이다.**

### 2. ★ `NULL` 이 섞이면 — 두 엔진이 **반대**다

**언제 쓰나** — 선택 입력 항목(중간이름·상세주소)을 이어 붙일 때.

먼저 `||` 쪽. **PG 에서 연결에 `NULL` 이 하나라도 있으면 결과가 통째로 `NULL`** 이다.

```text
### SQL: SELECT 'a' || NULL AS pipe, CONCAT('a', NULL) AS con, CONCAT_WS('-','a',NULL,'b') AS ws;
--- PG 18.6 ---
 pipe | con | ws  
------+-----+-----
      | a   | a-b
(1 row)

--- MySQL 8.4.10 ---
+------+------+------+
| pipe | con  | ws   |
+------+------+------+
| NULL | NULL | a-b  |
+------+------+------+
```

(PG 의 빈 칸이 `NULL` 이다 — psql 은 `NULL` 을 빈 칸으로 그린다.)

**한 표로 정리하면 대칭이 깨진 것이 보인다.**

| 식 | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `'a' \|\| NULL` | **`NULL`** | `NULL` (단, OR 의 결과로서의 `NULL`) |
| `CONCAT('a', NULL)` | **`'a'`** | **`NULL`** |
| `CONCAT_WS('-','a',NULL,'b')` | `'a-b'` | `'a-b'` |

```text
PostgreSQL                          MySQL
||     -> NULL 이 전파된다           CONCAT -> NULL 이 전파된다
CONCAT -> NULL 을 건너뛴다           CONCAT_WS -> NULL 을 건너뛴다
CONCAT_WS -> NULL 을 건너뛴다
```

그림 해설 — **`CONCAT` 의 의미가 정확히 반대다.** PG 의 `CONCAT` 은 `NULL` 을 빈 문자열처럼 다루고,\
MySQL 의 `CONCAT` 은 `NULL` 하나로 전체를 `NULL` 로 만든다.\
대가 — 「중간이름이 없는 사람의 이름이 통째로 사라지는」 사고가 **MySQL 쪽에서만** 난다.

**양쪽에서 같은 답을 내는 방법은 둘이다.**

```sql
-- (a) COALESCE 로 NULL 을 미리 없앤다  — 가장 확실하다
SELECT CONCAT(COALESCE(a,''), COALESCE(b,'')) FROM t;

-- (b) CONCAT_WS 를 쓴다  — 구분자가 필요할 때. 두 엔진 다 NULL 을 건너뛴다
SELECT CONCAT_WS('-', a, b) FROM t;
```

`NULL` 이 왜 전파되는지 자체는 [04 NULL 의 3값 논리](../04-null-three-valued-logic/)가 정본이다.

실제 열로 확인하면 이렇다.

```text
### SQL: SELECT COALESCE(salary, 0) AS s, CAST(salary AS CHAR(10)) AS c FROM emp ORDER BY id;
--- PG 18.6 ---
  s  |     c      
-----+------------
 300 | 300       
 500 | 500       
   0 | 
 400 | 400       
(4 rows)

--- MySQL 8.4.10 ---
+-----+------+
| s   | c    |
+-----+------+
| 300 | 300  |
| 500 | 500  |
|   0 | NULL |
| 400 | 400  |
+-----+------+
```

`cho` 의 `salary` 가 `NULL` 이라 **캐스팅해도 `NULL` 이다.** 문자열로 바뀌지 않는다.\
(PG 쪽 `c` 열이 넓은 것은 `CHAR(10)` 이라 공백으로 채워졌기 때문이다.)

### 3. ★ `LENGTH` — 글자인가 바이트인가

**언제 쓰나** — 입력 길이를 검증할 때. **한글·이모지에서 바로 물린다.**

```text
### SQL: SELECT LENGTH('한글abc') AS len, CHAR_LENGTH('한글abc') AS clen, OCTET_LENGTH('한글abc') AS olen;
--- PG 18.6 ---
 len | clen | olen 
-----+------+------
   5 |    5 |    9
(1 row)

--- MySQL 8.4.10 ---
+-----+------+------+
| len | clen | olen |
+-----+------+------+
|   9 |    5 |    9 |
+-----+------+------+
```

```text
'한글abc' 를 UTF-8 로 담으면

 한       글       a    b    c
 3바이트  3바이트  1    1    1     -> 합계 9바이트
 1글자    1글자    1    1    1     -> 합계 5글자

PG 의 LENGTH   -> 5   (CHAR_LENGTH 와 같다)
MySQL 의 LENGTH -> 9  (OCTET_LENGTH 와 같다)
```

그림 해설 — **`CHAR_LENGTH` 와 `OCTET_LENGTH` 는 두 엔진에서 같다.** 갈리는 것은 `LENGTH` 라는 **이름 하나**다.\
대가 — `WHERE LENGTH(name) <= 10` 이 한글 이름에서 **세 배 엄격**해진다. MySQL 에서 한글 세 글자가 9 로 세어진다.

**처방은 `LENGTH` 를 아예 안 쓰는 것이다.**

```sql
-- 글자 수를 세고 싶다  -> CHAR_LENGTH  (두 엔진 동일)
-- 바이트를 세고 싶다   -> OCTET_LENGTH (두 엔진 동일)
```

**★ 그런데 길이를 재기 전에 값이 이미 잘려 있을 수 있다.**

```text
### SQL: SELECT LENGTH(CAST(1234567 AS CHAR)) AS len, CAST(1234567 AS CHAR) AS v;
--- PG 18.6 ---
 len | v 
-----+---
   1 | 1
(1 row)

--- MySQL 8.4.10 ---
+------+---------+
| len  | v       |
+------+---------+
|    7 | 1234567 |
+------+---------+
```

그림 해설 — PG 의 `len` 이 **`1`** 이다. `LENGTH` 가 틀린 게 아니라 **`CAST(x AS CHAR)` 가 `char(1)` 로 잘라 놓은 것**이다(35번 2번).\
대가 — **「길이를 검사했으니 괜찮다」가 무너진다.** 검사 대상이 이미 잘린 값이기 때문이다.\
길이를 재기 전에 **값이 온전한지**부터 본다.

인코딩 자체(한글이 왜 3바이트인가)는 [`foundations/data-representation`](../../../../data-representation/)이 정본이다.

### 4. 잘라내기 — `SUBSTRING` 의 경계가 갈린다

**언제 쓰나** — 코드값에서 앞 몇 자리를 뽑을 때.

정상 범위는 두 엔진이 같다. 그리고 **두 표기가 다 통한다.**

```text
### SQL: SELECT SUBSTRING('abcdef' FROM 2 FOR 3) AS s1, SUBSTRING('abcdef', 2, 3) AS s2;
--- PG 18.6 ---
 s1  | s2  
-----+-----
 bcd | bcd
(1 row)

--- MySQL 8.4.10 ---
+------+------+
| s1   | s2   |
+------+------+
| bcd  | bcd  |
+------+------+
```

**경계를 벗어나면 갈린다.**

```text
### SQL: SELECT SUBSTRING('abcdef', 0, 3) AS zero_start, SUBSTRING('abcdef', -2) AS neg;
--- PG 18.6 ---
 zero_start |  neg   
------------+--------
 ab         | abcdef
(1 row)

--- MySQL 8.4.10 ---
+------------+------+
| zero_start | neg  |
+------------+------+
|            | ef   |
+------------+------+
```

```text
SUBSTRING('abcdef', 0, 3)        PG                      MySQL
  0번부터 3글자                  가상의 0번 자리부터      1부터 세므로 0은 범위 밖
                                 세어 'a','b' 가 남는다   -> 빈 문자열
                                 -> 'ab'

SUBSTRING('abcdef', -2)          PG                      MySQL
  -2번부터 끝까지                왼쪽 밖에서 시작해       뒤에서 2번째부터
                                 전부 포함 -> 'abcdef'    -> 'ef'
```

그림 해설 — **두 엔진 다 「1부터 센다」는 같다.** 갈리는 것은 **범위 밖 인덱스의 해석**이다.\
대가 — 오프셋을 계산해서 넣는 코드(`SUBSTRING(s, pos - 1, n)`)는 `pos = 1` 일 때 **조용히 다른 답**을 낸다.\
처방은 `GREATEST(pos, 1)` 로 **1 미만을 막는 것**이다.

### 5. 갈리지 않는 것들 — 여기까지 외우면 과잉이다

**언제 쓰나** — 「문자열 함수는 전부 방언이다」라는 인상을 교정할 때.

```text
### SQL: SELECT TRIM('  x  ') AS t, TRIM(BOTH 'x' FROM 'xxaxx') AS t2, LTRIM('  x') AS l, RTRIM('x  ') AS r;
--- PG 18.6 ---
 t | t2 | l | r 
---+----+---+---
 x | a  | x | x
(1 row)

--- MySQL 8.4.10 ---
+------+------+------+------+
| t    | t2   | l    | r    |
+------+------+------+------+
| x    | a    | x    | x    |
+------+------+------+------+
```

```text
### SQL: SELECT REPLACE('a-b-c','-','+') AS r, UPPER('aBc') AS u, LOWER('aBc') AS lo;
--- PG 18.6 ---
   r   |  u  | lo  
-------+-----+-----
 a+b+c | ABC | abc
(1 row)

--- MySQL 8.4.10 ---
+-------+------+------+
| r     | u    | lo   |
+-------+------+------+
| a+b+c | ABC  | abc  |
+-------+------+------+
```

```text
### SQL: SELECT LPAD('7', 3, '0') AS l, RPAD('7', 3, '0') AS r, REPEAT('ab', 3) AS rep, REVERSE('abc') AS rv;
--- PG 18.6 ---
  l  |  r  |  rep   | rv  
-----+-----+--------+-----
 007 | 700 | ababab | cba
(1 row)

--- MySQL 8.4.10 ---
+------+------+--------+------+
| l    | r    | rep    | rv   |
+------+------+--------+------+
| 007  | 700  | ababab | cba  |
+------+------+--------+------+
```

```text
### SQL: SELECT POSITION('c' IN 'abcabc') AS p;
--- PG 18.6 ---
 p 
---
 3
(1 row)

--- MySQL 8.4.10 ---
+---+
| p |
+---+
| 3 |
+---+
```

**`TRIM`·`REPLACE`·`UPPER`/`LOWER`·`LPAD`/`RPAD`·`REPEAT`·`REVERSE`·`POSITION` 은 한 자리도 안 갈렸다.**\
방언 경계는 **`||`·`CONCAT` 의 `NULL`·`LENGTH`·`SUBSTRING` 의 범위 밖** 넷에 몰려 있다.

### 6. 이 주제가 넘겨주는 것 — 대소문자는 함수가 아니라 collation 이 정한다

**언제 쓰나** — `UPPER` 로 대소문자를 맞춰 비교하려 할 때. **그 전에 39번을 봐야 한다.**

```text
### SQL: SELECT 'abc' = 'ABC' AS same_case;
--- PG 18.6 ---
 same_case 
-----------
 f
(1 row)

--- MySQL 8.4.10 ---
+-----------+
| same_case |
+-----------+
|         1 |
+-----------+
```

그림 해설 — **`UPPER` 를 안 썼는데도** MySQL 은 같다고 한다. 비교 규칙이 collation 에 있기 때문이다.\
대가 — PG 습관으로 `WHERE UPPER(name) = UPPER(:v)` 를 쓰면 MySQL 에서는 **불필요하고**,\
게다가 **열에 함수를 씌워 인덱스를 죽인다**(35번 8번).

이 갈래의 정본은 [39 collation](../39-collation/)이다. 여기서는 **문자열 함수의 결과만** 다룬다.

## 문법 — 형태와 규칙

SQL 문자열 문법은 「어느 이름이 어느 엔진에 있나」로 읽는다.

```sql
-- 연결
a || b              -- PG: 연결 / MySQL: 논리 OR (PIPES_AS_CONCAT 모드에서만 연결)
CONCAT(a, b, ...)   -- 양쪽 공통. 단 NULL 처리가 반대다
CONCAT_WS(sep, ...) -- 양쪽 공통. 양쪽 다 NULL 을 건너뛴다

-- 길이
LENGTH(s)           -- PG: 글자 수 / MySQL: 바이트 수     <- 이름이 같고 뜻이 다르다
CHAR_LENGTH(s)      -- 양쪽 공통: 글자 수
OCTET_LENGTH(s)     -- 양쪽 공통: 바이트 수

-- 자르기
SUBSTRING(s FROM p FOR n)   -- 양쪽 공통
SUBSTRING(s, p, n)          -- 양쪽 공통. 단 p < 1 의 해석이 갈린다
```

규칙 일곱.

1. **`||` 를 쓰지 않는다.** 이식할 코드에는 `CONCAT()` 을 쓴다.
2. **MySQL 의 `||` 는 `0`/`1` 을 돌려준다.** 에러가 아니라 **그럴듯한 값**이라 더 위험하다.
3. **`CONCAT` 의 `NULL` 처리가 반대다.** PG 는 건너뛰고, MySQL 은 전체를 `NULL` 로 만든다.
4. **양쪽에서 같게 만들려면 `COALESCE` 로 `NULL` 을 먼저 없앤다.**
5. **`LENGTH` 를 안 쓴다.** 글자 수는 `CHAR_LENGTH`, 바이트는 `OCTET_LENGTH` — 둘 다 공통이다.
6. **`SUBSTRING` 의 시작 위치를 1 미만으로 넘기지 않는다.** `GREATEST(p, 1)` 로 막는다.
7. **대소문자 비교는 함수가 아니라 collation 이 정한다**(39번).

#### 방언 요약

| 자리 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `'a' \|\| 'b'` | `'ab'` — 연결 | **`0`** — 논리 OR + 경고 1287·1292×2 |
| `'a' \|\| 1` | `'a1'` | `1` (OR) |
| `1 \|\| 0` | (타입 오류) | `1` — OR 임이 드러난다 |
| `PIPES_AS_CONCAT` | 해당 없음 | 모드를 켜면 `\|\|` 가 연결. **기본 `sql_mode` 에 없다** |
| `'a' \|\| NULL` | `NULL` | `NULL` (OR 의 결과) |
| `CONCAT('a', NULL)` | **`'a'`** | **`NULL`** |
| `CONCAT_WS('-','a',NULL,'b')` | `'a-b'` | `'a-b'` — **같다** |
| `LENGTH('한글abc')` | **`5`** (글자) | **`9`** (바이트) |
| `CHAR_LENGTH` / `OCTET_LENGTH` | `5` / `9` | `5` / `9` — **같다** |
| `SUBSTRING('abcdef', 0, 3)` | `'ab'` | `''` (빈 문자열) |
| `SUBSTRING('abcdef', -2)` | `'abcdef'` | `'ef'` |
| `SUBSTRING(s FROM p FOR n)` | 된다 | 된다 — **같다** |
| `TRIM`·`REPLACE`·`UPPER`·`LPAD`·`REPEAT`·`REVERSE`·`POSITION` | 전부 같다 | 전부 같다 |
| `'abc' = 'ABC'` | `f` | `1` — collation 이 정한다(39번) |

## 어디서 틀리나

- **`SELECT last_name \|\| first_name` 을 MySQL 에서 돌린다.**\
  에러가 아니라 **전부 `0`** 이 나온다. 경고 1287·1292 를 안 읽으면 표시가 없다.
- **`CONCAT` 이 두 엔진에서 같다고 믿는다.**\
  `NULL` 이 하나라도 섞이면 **정확히 반대**다. PG 는 `'a'`, MySQL 은 `NULL`.
- **`LENGTH(name) <= 10` 으로 입력을 검증한다.**\
  MySQL 에서 한글 이름은 글자당 3으로 세어진다. 세 글자 이름이 9 다. `CHAR_LENGTH` 를 쓴다.
- **`PIPES_AS_CONCAT` 을 켜서 해결한다.**\
  그 질의는 **서버 설정에 의존**하게 된다. 다른 서버로 옮기면 다시 `0` 이 된다.
- **`SUBSTRING(s, pos-1, n)` 처럼 계산한 오프셋을 넘긴다.**\
  `pos = 1` 이면 PG 는 앞에서 자르고 MySQL 은 빈 문자열을 준다. **에러가 안 난다.**
- **`WHERE UPPER(name) = 'ANN'` 으로 대소문자를 무시한다.**\
  MySQL 에서는 기본 collation 이 이미 무시하므로 불필요하고, **열에 함수를 씌워 인덱스를 죽인다.**
- **`||` 가 표준이라고 믿고 MySQL 을 탓한다.**\
  MySQL 매뉴얼은 `||` 를 **OR 의 비표준 동의어**로 설명하고 deprecated 로 표시한다. 그게 그쪽 문서의 입장이다.
- **잘린 값의 길이를 잰다.**\
  `LENGTH(CAST(1234567 AS CHAR))` 가 PG 에서 **`1`** 이다 — `CAST` 가 `char(1)` 로 잘랐기 때문이다(35번).\
  길이 검증 전에 **값이 온전한지** 확인한다.
- **`CHAR` 열의 공백을 잊는다.**\
  `char(5)` 에 `'ab'` 를 넣으면 두 엔진 다 `LENGTH` 는 2 로 나오지만, 출력에서는 공백으로 채워져 보인다.

## 구현 세부사항 대 언어 보장

- **언어(문서)가 정한 것** — `||` 의 의미, `CONCAT`/`CONCAT_WS` 의 `NULL` 처리,\
  `LENGTH`/`CHAR_LENGTH`/`OCTET_LENGTH` 가 무엇을 세는지, `SUBSTRING` 의 범위 밖 해석.\
  두 매뉴얼의 문자열 함수 페이지가 정본이다.
- **설정이 정하는 것** — **MySQL 의 `||`**(`sql_mode` 의 `PIPES_AS_CONCAT`).\
  이 문서의 출력은 **기본 `sql_mode`** 에서 나온 것이고, 실제 값을 위 1번에 찍어 두었다.
- **인코딩이 정하는 것** — `LENGTH` 의 바이트 수.\
  `'한글'` 이 6바이트인 것은 **UTF-8 의 성질**이지 MySQL 의 선택이 아니다.\
  다른 인코딩(예: EUC-KR)이면 같은 `LENGTH` 가 다른 수를 낸다. 인코딩 자체는 [`foundations/data-representation`](../../../../data-representation/)이 정본이다.
- **collation 이 정하는 것** — `=`·`UPPER` 의 결과가 대소문자를 구분하는지(39번).
- **경고 코드 번호**(1287·1292)는 MySQL 구현의 것이다. 외울 것은 번호가 아니라 **「경고로만 알려 준다」**는 성질이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — `CONCAT_WS`.** 구분자가 있고 빈 항목을 건너뛰고 싶을 때. **두 엔진에서 같게 동작하는 유일한 연결 함수**다.
- **쓴다 — `COALESCE` + `CONCAT`.** `NULL` 을 빈 문자열로 확정해 두면 방언이 사라진다.
- **쓴다 — `CHAR_LENGTH`.** 길이 검증은 언제나 이것으로.
- **안 쓴다 — `||`.** PG 전용 코드가 아니면 쓰지 않는다.
- **안 쓴다 — `LENGTH`.** 이름이 같고 뜻이 다른 함수는 읽는 사람을 속인다.
- **안 쓴다 — `WHERE` 의 열에 문자열 함수.** `UPPER(col)`·`SUBSTRING(col,...)` 은 인덱스를 죽인다(목록의 47번 주제).\
  꼭 필요하면 표현식 인덱스를 만든다(목록의 46번 주제).
- **조심한다 — 애플리케이션에서 붙이는 편이 나은 경우.** 표시용 문자열 조립은 DB 가 할 일이 아닐 때가 많다.

## 핵심 문장

- **MySQL 의 `||` 는 연결이 아니라 논리 OR** 이다. `'a' || 'b'` 는 `0` 이고 **에러가 아니다.**
- 이식할 연결에는 **`CONCAT()`** 을 쓴다. `PIPES_AS_CONCAT` 모드는 **기본 `sql_mode` 에 없다.**
- **`CONCAT` 의 `NULL` 처리는 두 엔진이 반대다** — PG 는 건너뛰고 MySQL 은 전체를 `NULL` 로 만든다.
- **`CONCAT_WS` 만 양쪽에서 같다** — 둘 다 `NULL` 을 건너뛴다.
- **`LENGTH` 는 PG 에서 글자, MySQL 에서 바이트**다. `CHAR_LENGTH`·`OCTET_LENGTH` 는 공통이다.
- `SUBSTRING` 은 **1부터 세는 것이 같고, 1 미만 인덱스의 해석이 갈린다.**
- `TRIM`·`REPLACE`·`UPPER`·`LPAD`·`REPEAT`·`REVERSE`·`POSITION` 은 **한 자리도 안 갈린다.**
- `'abc' = 'ABC'` 의 답은 **문자열 함수가 아니라 collation** 이 정한다(39번).

## 관련 자료

- [PostgreSQL 18 · String Functions and Operators](https://www.postgresql.org/docs/18/functions-string.html) — `||`·`concat`·`length` 의 정의.
- [MySQL 8.4 · String Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/string-functions.html) — `CONCAT` 의 `NULL` 규칙과 `LENGTH` 가 바이트라는 것.
- [MySQL 8.4 · Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html) — `PIPES_AS_CONCAT`.
- [`foundations/data-representation`](../../../../data-representation/) — **경계**: 글자가 바이트로 어떻게 놓이는지(UTF-8 의 가변 길이·코드포인트)는 **거기가 정본**이고,\
  여기는 **SQL 함수가 무엇을 세어 무엇을 돌려주는가**만 다룬다. 인코딩 규칙은 한 줄도 쓰지 않는다.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — `'a' + 1` 이 왜 `1` 이 되는지(경고 1292)는 거기.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `NULL` 이 전파되는 규칙.
- [38 패턴 매칭](../38-pattern-matching-like-regex/) — 문자열을 **찾는** 연산은 거기.
- [39 collation](../39-collation/) — 문자열을 **비교·정렬**하는 규칙은 거기.
- [SQL 주제 목록](../README.md) — 06(`COALESCE`) · 46(인덱스 정의) · 47(인덱스를 언제 타나) 이 이웃이다.

## 용어 풀이

- **연결(concatenation)** — 문자열을 이어 붙이는 것.\
  예: `CONCAT('010','1234')` → `'0101234'`.
- **`\|\|`** — PG 에서는 연결 연산자, MySQL 에서는 논리 OR 의 비표준 동의어.\
  예: `'a' \|\| 'b'` 가 PG 에서 `'ab'`, MySQL 에서 `0`.
- **`PIPES_AS_CONCAT`** — MySQL 의 `sql_mode` 플래그. 켜면 `\|\|` 가 연결이 된다.\
  예: 이 서버의 기본 `sql_mode` 에는 들어 있지 않다.
- **경고 1287** — MySQL 이 deprecated 문법을 썼다고 알리는 경고.\
  예: `'\|\| as a synonym for OR' is deprecated`.
- **`CONCAT_WS`** — 구분자(separator)를 앞에 받는 연결 함수. `NULL` 인자를 건너뛴다.\
  예: `CONCAT_WS('-','a',NULL,'b')` → `'a-b'`(두 엔진 동일).
- **글자 수(character length)** — 사람이 세는 글자 개수.\
  예: `'한글abc'` 는 5글자다. 두 엔진 다 `CHAR_LENGTH` 가 이것을 센다.
- **바이트 수(octet length)** — 저장에 쓰이는 바이트 개수.\
  예: UTF-8 에서 `'한글abc'` 는 9바이트다. MySQL 의 `LENGTH` 가 이것을 센다.
- **`COALESCE`** — 인자 중 처음으로 `NULL` 이 아닌 값을 돌려주는 함수.\
  예: `COALESCE(middle_name, '')` 로 연결 전에 `NULL` 을 없앤다.
- **collation** — 문자열을 비교·정렬하는 규칙의 이름.\
  예: MySQL 기본 `utf8mb4_0900_ai_ci` 에서는 `'abc' = 'ABC'` 가 참이다(39번).

## 더 들어가면

- **`||` 는 원래 표준 SQL 의 연결 연산자다.** MySQL 이 그 자리에 OR 을 놓은 것은 오래된 선택이고,\
  매뉴얼도 **비표준 동의어**라고 적으며 deprecated 표시를 달아 두었다. 서버가 직접 그 경고를 낸다(위 1번).
- **`CONCAT` 의 `NULL` 처리 차이는 「어느 쪽이 맞나」의 문제가 아니다.**\
  PG 는 「빈 것은 빼고 붙인다」, MySQL 은 「모르는 것이 섞이면 결과도 모른다」는 입장이다.\
  후자가 `NULL` 의 원래 의미에 가깝고, 전자가 실무에 편하다. **둘 다 일관적이라 더 헷갈린다.**
- **`LENGTH` 가 바이트인 것은 MySQL 의 역사다.** 문자셋이 단일 바이트였을 때는 두 수가 같았다.\
  멀티바이트가 기본이 된 지금도 이름이 남아 있는 것 — **이름은 바뀌지 않고 세상이 바뀐 사례**다.
- **문자열 조립을 어디서 할 것인가**는 설계 결정이다. DB 에서 붙이면 인덱스를 못 쓰게 되기 쉽고,\
  애플리케이션에서 붙이면 왕복이 늘어난다. **필터에 쓰이는 문자열은 조립하지 않고 열로 저장하는 편**이 대개 낫다.
