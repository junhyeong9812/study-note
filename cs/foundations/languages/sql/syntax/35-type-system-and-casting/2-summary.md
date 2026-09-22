# sql/35-타입 체계와 캐스팅 (명시 변환·암시 변환) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Type Conversion](https://www.postgresql.org/docs/18/typeconv.html) · [PostgreSQL 18 · Data Types](https://www.postgresql.org/docs/18/datatype.html) · [MySQL 8.4 · Type Conversion in Expression Evaluation](https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html) · [MySQL 8.4 · Cast Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/cast-functions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — 이 주제에서 다루는 동작에 「어느 버전부터」가 붙는 것은 없다. 두 매뉴얼에도 릴리스 노트에도 도입 버전이 없어 **버전을 적지 않는다.**\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) · 이어지는 것은 [36 수치](../36-numeric-types-and-functions/) · [37 문자열](../37-string-functions-and-concatenation/) · [40 날짜·시간](../40-date-time-types-and-functions/) 이고, 인덱스 쪽 귀결은 [목록의 **47번 주제**](../47-when-indexes-are-used/)다.

## 한눈에 — 쉽게 말하면

**타입 변환 = 엔진이 「이 둘을 같은 자로 재겠다」고 정하는 것.**

자를 맞추는 방법은 둘뿐이다.

- **명시 변환** — 내가 적는다. `CAST(x AS 타입)`.
- **암시 변환** — 내가 안 적어도 엔진이 한다. `WHERE code = 123` 에서 `code` 가 문자열이면 누군가는 변해야 한다.

문제는 **엔진이 「변할 수 없다」를 만났을 때 무엇을 하느냐**다.

```text
'abc' + 1  을 던졌다

PostgreSQL 18.6                      MySQL 8.4.10
─────────────                        ────────────
"abc 를 정수로 읽을 수 없다"           "읽을 수 있는 데까지 읽겠다"
       ↓                                     ↓
   문을 죽인다                          'abc' -> 0 으로 보고
   ERROR                                    0 + 1 = 1
       ↓                                     ↓
  나는 즉시 안다                       경고 한 줄만 남고 1 이 나온다
                                       (SHOW WARNINGS 를 안 치면 안 보인다)
```

| 비유 | 실체 |
|---|---|
| 자(尺)를 맞춘다 | 두 값을 같은 타입으로 맞춘다 |
| 「이건 센티미터로 읽어라」라고 내가 말한다 | `CAST(x AS ...)` — 명시 변환 |
| 상대가 알아서 맞춘다 | 암시 변환 |
| 못 읽는 눈금을 만나면 자를 내려놓는다 | PG — 에러로 문을 죽인다 |
| 못 읽는 눈금은 0 으로 보고 계속 잰다 | MySQL — 경고를 남기고 진행한다 |

> **타입(type)** — 값이 무엇으로 읽히는지, 그 값에 어떤 연산이 되는지를 정하는 꼬리표.\
> 예: `'10'` 은 문자열이라 `'10' > '9'` 가 **거짓**이고, `10` 은 정수라 `10 > 9` 가 참이다.

> **암시 변환(implicit conversion)** — 내가 적지 않았는데 엔진이 끼워 넣는 변환.\
> 예: `WHERE code = 123` 에서 `code` 가 `varchar` 면 MySQL 은 **열 전체**를 수치로 바꿔 비교한다.

암시 변환이 비싼 이유는 여기 있다 — **열 쪽이 변하면 그 열의 인덱스는 못 쓴다.**

```text
인덱스는 "code 의 원래 값" 순서로 정렬돼 있다
        ↓
질의가 "code 를 수치로 바꾼 값" 을 찾는다
        ↓
정렬 순서가 다른 자료를 뒤지는 셈이라 -> 인덱스를 버리고 전부 훑는다
```

## 이 주제가 답하려는 질문

1. **엔진은 언제 타입을 알아서 맞추고, 언제 거부하나?**
2. **비교에서 어느 쪽이 변하나?** — 그 선택이 인덱스를 살리고 죽인다.
3. **`NULL` 에는 타입이 있나?**

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 주제들이 공유하는 두 표다. 이 주제는 `emp`·`dept` 를 **읽기만** 한다.

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

인덱스 실험만 별도 표 `t35` 를 쓴다. 두 엔진에 같은 모양으로 만들었고 **끝나고 지웠다**.

```sql
CREATE TABLE t35 (id int PRIMARY KEY, code varchar(20) NOT NULL);  -- code 에 인덱스
-- 20,000 행: (1,'C000001') (2,'C000002') ... (20000,'C020000')
```

## 동작 방식

### 1. 명시 변환 — `CAST` 의 **타입 이름이 갈린다**

**언제 쓰나** — 내가 타입을 정하고 싶을 때. 그리고 **이식할 때 맨 먼저 깨지는 자리**다.

```text
CAST( 값 AS 타입이름 )
           ^^^^^^^^
        여기가 방언이다
```

`INTEGER` 는 표준스럽게 생겼지만 MySQL 이 거부한다.

```text
### SQL: SELECT CAST('123' AS INTEGER) + 1 AS r;
--- PG 18.6 ---
  r  
-----
 124
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'INTEGER) + 1 AS r' at line 1
```

MySQL 이 받는 이름은 `SIGNED` 다. 그리고 그 이름을 PG 가 거부한다.

```text
### SQL: SELECT CAST('123' AS SIGNED) + 1 AS r;
--- PG 18.6 ---
ERROR:  type "signed" does not exist
LINE 1: SELECT CAST('123' AS SIGNED) + 1 AS r;
                             ^
--- MySQL 8.4.10 ---
+-----+
| r   |
+-----+
| 124 |
+-----+
```

문자열로 갈 때도 마찬가지다 — PG 는 `TEXT`, MySQL 은 `CHAR` 다.

```text
### SQL: SELECT CAST(123 AS TEXT) AS r;
--- PG 18.6 ---
  r  
-----
 123
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near 'TEXT) AS r' at line 1
```

**★ 여기서 조용한 사고가 난다.** `CAST(123 AS CHAR)` 는 **양쪽 다 통과하는데 답이 다르다.**

```text
### SQL: SELECT CAST(123 AS CHAR) AS r;
--- PG 18.6 ---
 r 
---
 1
(1 row)

--- MySQL 8.4.10 ---
+------+
| r    |
+------+
| 123  |
+------+
```

그림 해설 — PG 의 `CHAR` 는 **길이를 안 적으면 `char(1)`** 이라 `123` 이 `1` 로 **잘린다.**\
MySQL 의 `CHAR` 는 `CAST` 안에서 길이 제한 없는 문자열을 뜻한다.\
대가 — **에러가 안 나므로 테스트가 통과한다.** 이식 사고 중 가장 늦게 발견되는 종류다.

**★ 한 자리 값으로 테스트하면 안 드러난다.**

```text
### SQL: SELECT CAST(10 AS CHAR) AS r;
--- PG 18.6 ---
 r 
---
 1
(1 row)

--- MySQL 8.4.10 ---
+------+
| r    |
+------+
| 10   |
+------+
```

`CAST(5 AS CHAR)` 였다면 **양쪽 다 `5`** 다. **두 자리부터 갈린다.**

**길이를 적거나 `VARCHAR` 를 쓰면 PG 에서는 안 잘린다 — 그런데 `VARCHAR` 를 MySQL 이 거부한다.**

```text
### SQL: SELECT CAST(10 AS CHAR(10)) AS r;
--- PG 18.6 ---
     r      
------------
 10        
(1 row)

--- MySQL 8.4.10 ---
+------+
| r    |
+------+
| 10   |
+------+
```

```text
### SQL: SELECT CAST(10 AS VARCHAR) AS r;
--- PG 18.6 ---
 r  
----
 10
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near 'VARCHAR) AS r' at line 1
```

`CAST(10 AS VARCHAR(10))` 도 같다 — PG `10`, MySQL `ERROR 1064`.

```text
이식 가능성 표
                        PG 18.6   MySQL 8.4.10
CAST(10 AS CHAR)          1          10       <- 둘 다 통과, 답이 다르다 ★
CAST(10 AS CHAR(10))      '10  ...'  10       <- 둘 다 통과, 답이 같다  ✅
CAST(10 AS VARCHAR)       10         ERROR 1064
CAST(10 AS VARCHAR(10))   10         ERROR 1064
CAST(10 AS TEXT)          10         ERROR 1064
```

**양쪽에서 같은 답을 내는 것은 `CHAR(n)` 하나뿐이다.**\
(PG 의 `char(10)` 은 공백으로 채워지므로 뒤 공백이 붙는다 — 위 출력의 넓은 칸이 그것이다.\
필요하면 `TRIM` 한다. 뒤 공백 비교 규칙은 [39 collation](../39-collation/) 4번.)

**`::` 축약도 같은 함정을 갖는다.**

```text
--- PG 18.6 ---
SELECT 10::text AS r, 10::char AS r2, 10::varchar AS r3;
 r  | r2 | r3 
----+----+----
 10 | 1  | 10
(1 row)
```

`10::char` 가 **`1`** 이다. 짧게 쓰려다 값을 잃는다.

둘 다 받는 이름은 `DECIMAL(p,s)` 하나뿐이다.

```text
### SQL: SELECT CAST('123' AS DECIMAL(10,2)) AS r;
--- PG 18.6 ---
   r    
--------
 123.00
(1 row)

--- MySQL 8.4.10 ---
+--------+
| r      |
+--------+
| 123.00 |
+--------+
```

PG 에는 축약 표기 `::` 가 있다. **MySQL 파서는 이 기호를 모른다.**

```text
### SQL: SELECT '123'::int + 1 AS r;
--- PG 18.6 ---
  r  
-----
 124
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near '::int + 1 AS r' at line 1
```

> **`::`** — PG 전용 캐스팅 축약. `x::int` 는 `CAST(x AS int)` 와 같다.\
> 예: `'123'::int + 1` → `124`. MySQL 에 붙여 넣으면 `ERROR 1064` 다.

### 2. ★ 암시 변환 — 같은 입력이 한쪽은 에러, 한쪽은 답

**언제 쓰나** — 문자열과 수치를 섞어 쓸 때. **이 주제에서 가장 비싼 차이다.**

```text
(입력) 'abc' + 1

PG: 산술 연산자 + 를 보고 양쪽을 수치로 맞추려 한다
     'abc' 를 integer 로 읽는다 -> 실패 -> 문 전체를 중단
MySQL: 산술 문맥이면 문자열을 앞에서부터 읽을 수 있는 만큼만 읽는다
     'abc' -> 숫자가 하나도 없다 -> 0 -> 0 + 1 = 1
```

```text
### SQL: SELECT 'abc' + 1 AS r;
--- PG 18.6 ---
ERROR:  invalid input syntax for type integer: "abc"
LINE 1: SELECT 'abc' + 1 AS r;
               ^
--- MySQL 8.4.10 ---
+---+
| r |
+---+
| 1 |
+---+
```

MySQL 이 조용한 것은 아니다 — **물어보면 말해 준다.**

```text
START TRANSACTION 없이 두 문을 이어 쳤다.
SELECT 'abc' + 1 AS r;
+---+
| r |
+---+
| 1 |
+---+
SHOW WARNINGS;
+---------+------+-----------------------------------------+
| Level   | Code | Message                                 |
+---------+------+-----------------------------------------+
| Warning | 1292 | Truncated incorrect DOUBLE value: 'abc' |
+---------+------+-----------------------------------------+
```

그림 해설 — **경고 1292 가 유일한 신호다.** 애플리케이션 드라이버는 대개 경고를 안 읽는다.\
대가 — 오타 하나(`WHERE amount = 'l0'`)가 **0 과의 비교**가 되어 조용히 엉뚱한 행을 고른다.

읽을 수 있는 앞부분이 있으면 거기까지만 읽는다.

```text
### SQL: SELECT 1 + '1' AS r;
--- PG 18.6 ---
 r 
---
 2
(1 row)

--- MySQL 8.4.10 ---
+---+
| r |
+---+
| 2 |
+---+
```

**여기는 같다.** PG 도 `'1'` 은 정수로 읽히므로 변환에 성공한다.\
갈리는 것은 **성공할 때가 아니라 실패할 때**다.

비교 연산자에서도 똑같이 갈린다.

```text
### SQL: SELECT 1 = 'abc' AS r;
--- PG 18.6 ---
ERROR:  invalid input syntax for type integer: "abc"
LINE 1: SELECT 1 = 'abc' AS r;
                   ^
--- MySQL 8.4.10 ---
+---+
| r |
+---+
| 0 |
+---+
```

그림 해설 — MySQL 의 `0` 은 「다르다」로 읽히지만 실제로는 「**abc 를 0 으로 보고 1 과 비교했다**」다.\
`SELECT 0 = 'abc'` 였다면 **참**이 나온다 — 같은 규칙의 반대편이다.

### 3. ★ 비교에서 **어느 쪽이 변하나** — 인덱스가 여기서 죽는다

**언제 쓰나** — 문자열 열을 수치와 비교할 때. [목록의 **47번 주제**](../47-when-indexes-are-used/)로 이어지는 자리다.

`t35.code` 는 `varchar(20)` 이고 인덱스가 걸려 있다. 정상 질의는 인덱스를 탄다.

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t35 WHERE code = 'C000123';
                   QUERY PLAN                   
------------------------------------------------
 Index Scan using t35_code_idx on t35
   Index Cond: ((code)::text = 'C000123'::text)
(2 rows)

--- MySQL 8.4.10 ---
EXPLAIN SELECT * FROM t35 WHERE code = 'C000123';
+----+-------------+-------+------+---------------+--------------+---------+-------+------+-------------+
| id | select_type | table | type | possible_keys | key          | key_len | ref   | rows | Extra       |
+----+-------------+-------+------+---------------+--------------+---------+-------+------+-------------+
|  1 | SIMPLE      | t35   | ref  | t35_code_idx  | t35_code_idx | 82      | const |    1 | Using index |
+----+-------------+-------+------+---------------+--------------+---------+-------+------+-------------+
```

(폭에 맞춰 `partitions`·`filtered` 칸을 뺀 것 말고는 서버가 낸 그대로다.)

이제 따옴표 하나를 지운다. `code = 123`.

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
EXPLAIN (COSTS OFF)                        EXPLAIN
  SELECT * FROM t35 WHERE code = 123;        SELECT * FROM t35 WHERE code = 123;

--- 실제 출력 ---                          --- 실제 출력 ---
ERROR:  operator does not exist:           type: index   (인덱스 전부 훑기)
  character varying = integer              key:  t35_code_idx
LINE 1: ... WHERE code = 123;              rows: 19905
                       ^                   Extra: Using where; Using index
HINT:  No operator matches the given
  name and argument types. You might
  need to add explicit type casts.

  -> 문이 서지 않는다. 비교 자체가 없다       -> 돈다. 그런데 rows 가 1 -> 19905 로 늘었다
```

두 그림의 결론 — **PG 에는 「문자열 열 = 정수」 연산자가 아예 없다.** 조용히 느려질 기회가 없다.\
MySQL 은 돌지만, **열 쪽을 수치로 바꿔** 비교하므로 인덱스의 정렬이 쓸모없어진다.

MySQL 은 그 사실을 **경고로 정확히 말해 준다.**

```text
SHOW WARNINGS;
+---------+------+-------------------------------------------------------------------------+
| Level   | Code | Message                                                                 |
+---------+------+-------------------------------------------------------------------------+
| Warning | 1739 | Cannot use ref access on index 't35_code_idx' due to type or collation |
|         |      | conversion on field 'code'                                              |
| Warning | 1739 | Cannot use range access on index 't35_code_idx' due to type or          |
|         |      | collation conversion on field 'code'                                    |
+---------+------+-------------------------------------------------------------------------+
```

(줄바꿈만 폭에 맞게 접었고, 문구는 서버가 낸 그대로다.)

그리고 그 질의의 **결과는 0행**이다.

```text
SELECT COUNT(*) AS matched FROM t35 WHERE code = 123;
+---------+
| matched |
+---------+
|       0 |
+---------+
```

그림 해설 — `'C000123'` 을 수치로 읽으면 `0` 이다. `0 = 123` 은 거짓이라 **전부 훑고 아무것도 못 찾는다.**\
20,000행을 읽고 0행을 돌려주는 질의가 **에러 없이** 완주한다.\
대가 — 느린 것보다 나쁜 것은 **답이 틀린 것**이다. 여기선 둘 다 일어난다.

**PG 에서 같은 사고를 내려면 내가 열에 손을 대야 한다.**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t35 WHERE substr(code,2)::int = 123;
                      QUERY PLAN                      
------------------------------------------------------
 Seq Scan on t35
   Filter: ((substr((code)::text, 2))::integer = 123)
(2 rows)
```

열에 함수를 씌우면 인덱스가 죽는다 — **이것은 두 엔진 공통 규칙**이다.\
차이는 **누가 함수를 씌우느냐**다. PG 는 내가, MySQL 은 엔진이 씌운다.

**수치 타입끼리는 폭이 달라도 인덱스가 산다.**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t35 WHERE id = 123::bigint;
             QUERY PLAN             
------------------------------------
 Index Scan using t35_pkey on t35
   Index Cond: (id = '123'::bigint)
(2 rows)
```

그림 해설 — `int` 열과 `bigint` 값의 비교는 **값 쪽을 좁히면 되므로** 인덱스가 산다.\
「암시 변환은 무조건 인덱스를 죽인다」는 **틀린 요약**이다. 죽는 것은 **열 쪽이 변할 때**다.

### 4. `NULL` 의 타입 — 「아직 정해지지 않았다」

**언제 쓰나** — `NULL` 을 그대로 `INSERT`·`UNION`·함수 인자에 넣을 때.

PG 는 리터럴의 타입을 보여 준다.

```text
--- PG 18.6 ---
SELECT pg_typeof(NULL) AS t, pg_typeof(NULL::int) AS t2, pg_typeof(1) AS t3,
       pg_typeof(1.5) AS t4, pg_typeof('x') AS t5;
    t    |   t2    |   t3    |   t4    |   t5    
---------+---------+---------+---------+---------
 unknown | integer | integer | numeric | unknown
(1 row)
```

그림 해설 — `NULL` 과 따옴표 리터럴은 **`unknown`** 이다. 「타입이 없다」가 아니라 「**주변을 보고 정하겠다**」다.\
`1.5` 가 `numeric` 인 것도 기억할 값어치가 있다 — 36번에서 `0.1 + 0.2` 가 딱 떨어지는 이유가 여기다.

MySQL 에는 `pg_typeof` 가 없다. **표를 만들어 보면 정해진 타입이 보인다.**

```text
--- MySQL 8.4.10 ---
CREATE TEMPORARY TABLE t35n AS SELECT NULL AS c1, 1 AS c2, 1.5 AS c3, 'x' AS c4, TRUE AS c5;
DESCRIBE t35n;
+-------+--------------+------+-----+---------+-------+
| Field | Type         | Null | Key | Default | Extra |
+-------+--------------+------+-----+---------+-------+
| c1    | varbinary(0) | YES  |     | NULL    | NULL  |
| c2    | int          | NO   |     | 0       | NULL  |
| c3    | decimal(2,1) | NO   |     | 0.0     | NULL  |
| c4    | varchar(1)   | NO   |     |         | NULL  |
| c5    | int          | NO   |     | 0       | NULL  |
+-------+--------------+------+-----+---------+-------+
```

그림 해설 — MySQL 은 `NULL` 리터럴을 **`varbinary(0)`** 으로 굳힌다.\
`1.5` 는 `decimal(2,1)` — PG 의 `numeric` 과 같은 성격이다.\
대가 — 타입이 문맥으로 정해지므로, **`SELECT NULL AS x` 로 만든 뷰·CTE 의 열 타입은 내 의도가 아니다.** 필요하면 `CAST` 로 못 박는다.

### 5. `BOOLEAN` — PG 는 타입, MySQL 은 별칭

**언제 쓰나** — 플래그 열을 만들 때. 그리고 `TRUE` 에 산술을 걸 때.

```text
### SQL: SELECT TRUE AS t, FALSE AS f, TRUE + TRUE AS sum;
--- PG 18.6 ---
ERROR:  operator does not exist: boolean + boolean
LINE 1: SELECT TRUE AS t, FALSE AS f, TRUE + TRUE AS sum;
                                           ^
HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+---+---+-----+
| t | f | sum |
+---+---+-----+
| 1 | 0 |   2 |
+---+---+-----+
```

열로 선언하면 MySQL 이 무엇으로 바꾸는지 보인다.

```text
--- MySQL 8.4.10 ---
CREATE TABLE t35b (b BOOLEAN, n INT);
SHOW CREATE TABLE t35b\G
Create Table: CREATE TABLE `t35b` (
  `b` tinyint(1) DEFAULT NULL,
  `n` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

```text
--- PG 18.6 ---
CREATE TEMP TABLE t35b (b boolean, n int);
INSERT INTO t35b VALUES (TRUE, 5), (FALSE, 6);
SELECT b, n > 0 AS cmp FROM t35b;
 b | cmp 
---+-----
 t | t
 f | t
(2 rows)
```

그림 해설 — PG 는 `t`/`f` 로 **다른 종류의 값**임을 보여 준다. MySQL 은 `1`/`0` — **정수다.**\
대가 — MySQL 에서 `SUM(is_active)` 가 그냥 된다. 편하지만, **`is_active = 2` 인 행도 참으로 읽힌다.**\
PG 에서 boolean 을 세려면 `SUM(b::int)` 나 `COUNT(*) FILTER (WHERE b)` 로 **의도를 적어야** 한다.

```text
--- PG 18.6 ---
SELECT b::int AS as_int FROM t35b;
 as_int 
--------
      1
      0
(2 rows)
```

MySQL 에는 `CAST(1 AS BOOLEAN)` 이 없다.

```text
### SQL: SELECT CAST(1 AS BOOLEAN) AS b;
--- PG 18.6 ---
 b 
---
 t
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near 'BOOLEAN) AS b' at line 1
```

### 6. 집합 연산에서의 타입 결정

**언제 쓰나** — `UNION` 으로 여러 질의를 붙일 때. 열 타입이 맞지 않으면 여기서 드러난다.

```text
### SQL: SELECT 1 AS c UNION SELECT 'a' AS c;
--- PG 18.6 ---
ERROR:  invalid input syntax for type integer: "a"
LINE 1: SELECT 1 AS c UNION SELECT 'a' AS c;
                                   ^
--- MySQL 8.4.10 ---
+---+
| c |
+---+
| 1 |
| a |
+---+
```

그림 해설 — PG 는 **첫 가지의 타입(`integer`)으로 맞추려다** 실패한다.\
MySQL 은 **둘 다 담을 수 있는 문자열**로 올려 맞춘다 — 그래서 `1` 이 `'1'` 이 되어 나온다.\
대가 — MySQL 쪽 결과를 정렬하면 **문자열 순서**다. `10` 이 `9` 앞에 온다(37번·39번으로 이어진다).\
집합 연산 자체는 [목록의 **34번 주제**](../34-set-operations-union-intersect-except/)가 정본이다.

## 문법 — 형태와 규칙

SQL 에서 타입 문법은 「선언 형태」가 아니라 「**어느 자리에서 무엇이 변하나**」로 읽는다.

```sql
-- 명시 변환 (양쪽 공통 형태)
CAST(expr AS type)

-- PG 전용 축약
expr::type

-- 타입 이름이 갈리는 자리
--                PG              MySQL
--   정수         int/integer     SIGNED / UNSIGNED
--   문자열       text            CHAR            ← 길이 없는 CHAR 은 PG 에서 char(1) 이다
--   십진수       numeric/decimal DECIMAL         ← 둘 다 DECIMAL(p,s) 를 받는다
--   불리언       boolean         (없음 — tinyint(1))
```

규칙 여섯.

1. **`CAST(x AS INTEGER)` 는 MySQL 에서 문법 오류다.** `SIGNED` 를 쓴다.
2. **`CAST(x AS CHAR)` 는 양쪽 다 통과하고 답이 다르다.** PG 는 `char(1)` 로 잘린다.\
   양쪽에서 같은 답을 내는 것은 **`CHAR(n)`** 뿐이다 — `VARCHAR`·`TEXT` 는 MySQL 이 거부한다.
3. **`::` 는 PG 전용이다.** 이식할 코드에는 `CAST` 를 쓴다.
4. **비교·산술에서 변환이 실패하면 PG 는 에러, MySQL 은 `0`(경고 1292)** 이다.
5. **PG 에는 `varchar = integer` 연산자가 없다.** 문자열 열을 수치와 비교하려면 내가 캐스팅해야 한다.
6. **열 쪽이 변하면 그 열의 인덱스는 버려진다.** 값 쪽만 변하면 산다.

두 엔진이 **같은** 자리도 적어 둔다 — 여기까지 갈린다고 외우면 과잉이다.

```text
### SQL: SELECT 1 = '1' AS r;
--- PG 18.6 ---
 r 
---
 t
(1 row)

--- MySQL 8.4.10 ---
+---+
| r |
+---+
| 1 |
+---+
```

```text
### SQL: SELECT '10' > '9' AS str_cmp, 10 > 9 AS num_cmp;
--- PG 18.6 ---
 str_cmp | num_cmp 
---------+---------
 f       | t
(1 row)

--- MySQL 8.4.10 ---
+---------+---------+
| str_cmp | num_cmp |
+---------+---------+
|       0 |       1 |
+---------+---------+
```

그림 해설 — **양쪽 다 문자열이면 두 엔진 모두 문자열로 비교한다.** `'10' > '9'` 는 거짓이다.\
변환은 **양쪽 타입이 다를 때만** 일어난다. 이것이 규칙의 출발점이다.

#### 방언 요약

| 자리 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `CAST` 의 정수 이름 | `int` / `integer` | **`SIGNED`** (`INTEGER` 는 `ERROR 1064`) |
| `CAST` 의 문자열 이름 | `text` | **`CHAR`** (`TEXT` 는 `ERROR 1064`) |
| `CAST(123 AS CHAR)` | `1` — `char(1)` 로 잘린다 | `123` |
| `CAST(10 AS CHAR(10))` | `10`(뒤 공백 채움) | `10` — **유일하게 답이 같다** |
| `CAST(10 AS VARCHAR)` / `VARCHAR(10)` | `10` | **`ERROR 1064`** |
| `10::char` / `10::varchar` | `1` / `10` | 해당 없음 — `::` 가 없다 |
| 축약 표기 | `x::type` | **없다** — `ERROR 1064` |
| `'abc' + 1` | `ERROR: invalid input syntax` | `1` + 경고 1292 |
| `1 = 'abc'` | `ERROR: invalid input syntax` | `0` |
| `varchar 열 = 정수` | **연산자 없음** — 에러 | 돈다 — 인덱스 버림 + 경고 1739 |
| `NULL` 리터럴의 타입 | `unknown` | `varbinary(0)` |
| 소수 리터럴의 타입 | `numeric` | `decimal` |
| `BOOLEAN` | 진짜 타입 (`t`/`f`) | `tinyint(1)` 의 별칭 (`1`/`0`) |
| `TRUE + TRUE` | 에러 — 연산자 없음 | `2` |
| `SELECT 1 UNION SELECT 'a'` | 에러 | 문자열로 올려 둘 다 반환 |

## 어디서 틀리나

- **`CAST(x AS CHAR)` 를 PG 에 그대로 옮긴다.**\
  에러가 안 난다. **값이 첫 글자로 잘린다.** `CAST(123 AS CHAR)` → `1`. 길이를 적거나 `text` 를 쓴다.\
  ★ **한 자리 값으로 테스트하면 통과한다** — `CAST(5 AS CHAR)` 는 양쪽 다 `5` 다. 두 자리부터 갈린다.
- **잘린 값의 길이를 잰다.**\
  `LENGTH(CAST(1234567 AS CHAR))` 가 PG 에서 **`1`**, MySQL 에서 **`7`** 이다(37번).\
  길이 검증이 통째로 무의미해진다.
- **`WHERE 문자열열 = 숫자` 를 쓴다.**\
  MySQL 은 **전부 훑고 0행**을 돌려준다. `EXPLAIN` 의 `type` 이 `ref` → `index` 로 바뀌고 경고 1739 가 뜬다.\
  PG 는 연산자가 없어 문이 서지 않으므로 **여기서만은 PG 가 안전하다.**
- **「암시 변환은 인덱스를 죽인다」로 외운다.**\
  죽는 것은 **열 쪽이 변할 때**다. `int` 열 = `bigint` 값은 인덱스를 탄다(위 3번).
- **MySQL 의 경고를 안 읽는다.**\
  1292(`Truncated incorrect DOUBLE value`)·1739(인덱스 포기)는 **결과에 안 나온다.** `SHOW WARNINGS` 가 유일한 통로다.
- **`NULL` 을 그대로 `SELECT` 해 뷰·CTE 의 열로 쓴다.**\
  PG 는 `unknown`, MySQL 은 `varbinary(0)` 이다. 의도한 타입을 `CAST` 로 못 박는다.
- **MySQL 에서 `flag = 1` 과 `flag IS TRUE` 를 같다고 본다.**\
  `tinyint(1)` 이라 `2` 도 들어간다. `flag = 2` 인 행은 `IS TRUE` 에는 걸리고 `= 1` 에는 안 걸린다.
- **`UNION` 의 열 타입을 첫 가지로만 판단한다.**\
  PG 는 첫 가지 타입으로 맞추다 에러를 내고, MySQL 은 문자열로 올린다. 정렬 결과가 바뀐다.
- **비교 한쪽에 따옴표를 습관적으로 붙인다.**\
  `WHERE id = '123'` 은 수치 열이라 양쪽 다 인덱스를 탄다(값 쪽이 변한다). 반대 방향만 위험하다.

## 구현 세부사항 대 언어 보장

- **언어(문서)가 정한 것** — `CAST` 의 존재와 형태, 변환 실패 시 각 엔진의 처리 방식,\
  `varchar`/`int` 비교 연산자의 유무, `BOOLEAN` 이 MySQL 에서 `tinyint(1)` 이라는 사실.\
  두 매뉴얼의 타입 변환 페이지가 정본이다.
- **옵티마이저가 정하는 것** — **인덱스를 쓸지 말지.**\
  위 `EXPLAIN` 출력은 「20,000행·통계 수집 직후·이 서버」의 판단이다.\
  행 수가 적으면 인덱스가 있어도 순차 스캔이 더 싸서 계획이 달라진다 — **계획은 관찰이지 보장이 아니다.**
- **경고 코드 번호**(1292·1739)는 MySQL 구현의 것이다. 코드가 아니라 **「경고로만 알려 준다」는 성질**을 외운다.
- **`rows` 추정치**(19905)는 통계에서 나온 **추정**이다. 실제 행 수 20,000 과 다르다 — [목록의 **60번 주제**](../60-explain-analyze-estimates-vs-actuals/)의 소재다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 경계에서 한 번 명시한다.** 애플리케이션이 넘긴 값의 타입이 의심스러우면 **질의 밖에서** 맞춘다.
- **쓴다 — `CAST` 를 값 쪽에.** `WHERE code = CAST(123 AS CHAR(20))` 처럼 **열이 아니라 값**을 바꾼다.
- **안 쓴다 — 열에 `CAST` 를 씌운다.** `WHERE CAST(code AS SIGNED) = 123` 은 인덱스를 확실히 죽인다.\
  꼭 필요하면 **표현식 인덱스**를 따로 만든다([목록의 **46번 주제**](../46-index-definition-composite-partial-expression/)).
- **안 쓴다 — 암시 변환에 기댄다.** 두 엔진에서 답이 갈리는 자리다. 짧아지는 것은 문장뿐이고 늘어나는 것은 사고다.
- **조심한다 — 스키마가 틀렸을 때.** 숫자만 담는 열이 `varchar` 라면 진짜 처방은 캐스팅이 아니라 **열 타입 수정**이다([목록의 **42번 주제**](../42-create-alter-drop-table/)).

## 핵심 문장

- 타입 변환은 「**같은 자로 재겠다**」는 선언이고, 갈리는 것은 **변환이 실패할 때의 처리**다.
- **PG 는 못 읽으면 문을 죽이고**, **MySQL 은 읽을 수 있는 데까지 읽고 경고만 남긴다.**
- `CAST` 의 **타입 이름이 방언**이다 — `INTEGER`/`SIGNED`, `TEXT`/`CHAR`. `::` 는 PG 전용이다.
- **`CAST(123 AS CHAR)` 는 양쪽 다 통과하고 답이 다르다** — PG 는 `1`, MySQL 은 `123`.
- 인덱스가 죽는 조건은 「암시 변환」이 아니라 「**열 쪽이 변하는 것**」이다.
- MySQL 은 인덱스를 포기할 때 **경고 1739 로 말해 준다.** 안 읽으면 안 보인다.
- `NULL` 리터럴은 **타입이 없는 게 아니라 문맥이 정한다** — PG `unknown`, MySQL `varbinary(0)`.
- MySQL 의 `BOOLEAN` 은 **`tinyint(1)` 의 다른 이름**이다. 진짜 3값 불리언은 PG 에만 있다.

## 관련 자료

- [PostgreSQL 18 · Type Conversion](https://www.postgresql.org/docs/18/typeconv.html) — 연산자·`UNION` 의 타입 결정 규칙.
- [PostgreSQL 18 · Data Types](https://www.postgresql.org/docs/18/datatype.html) — `char` 의 기본 길이가 1 이라는 것.
- [MySQL 8.4 · Type Conversion in Expression Evaluation](https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html) — 비교에서 어느 쪽이 변하는지.
- [MySQL 8.4 · Cast Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/cast-functions.html) — `CAST` 가 받는 타입 이름 목록.
- [`foundations/data-representation`](../../../../data-representation/) — **경계**: 값이 비트로 어떻게 놓이는지(2의 보수·IEEE 754·인코딩)는 **거기가 정본**이고,\
  여기는 **SQL 이 두 값을 비교·연산할 때 어느 타입으로 맞추는가**만 다룬다. 비트 배치는 한 줄도 쓰지 않는다.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — 변환이 일어나는 자리(`WHERE`·`SELECT`)의 평가 순서.
- [36 수치 타입과 수치 함수](../36-numeric-types-and-functions/) — `numeric` 과 `float` 의 차이는 거기.
- [37 문자열 함수와 연결 연산](../37-string-functions-and-concatenation/) — 문자열로의 변환이 일어나는 자리.
- [40 날짜·시간 타입과 함수](../40-date-time-types-and-functions/) — 날짜 문자열의 변환은 거기.
- [SQL 주제 목록](../README.md) — 34(집합 연산) · 42(테이블 정의) · 46(인덱스 정의) · 47(인덱스를 언제 타나) 이 이웃이다.

## 용어 풀이

- **타입(type)** — 값이 무엇으로 읽히고 어떤 연산이 되는지를 정하는 꼬리표.\
  예: `'10' > '9'` 는 거짓이고 `10 > 9` 는 참이다.
- **명시 변환(explicit cast)** — 내가 `CAST(x AS 타입)` 으로 적는 변환.\
  예: `CAST('123' AS DECIMAL(10,2))` → `123.00`(두 엔진 동일).
- **암시 변환(implicit conversion)** — 적지 않았는데 엔진이 끼워 넣는 변환.\
  예: MySQL 의 `'abc' + 1` 에서 `'abc'` → `0`.
- **`::`** — PG 전용 캐스팅 축약. `x::int` = `CAST(x AS int)`.\
  예: MySQL 에 붙여 넣으면 `ERROR 1064` 다.
- **`SIGNED`** — MySQL `CAST` 의 정수 타입 이름. PG 에는 없는 이름이다.\
  예: `CAST('123' AS SIGNED)` → `124`. PG 는 `type "signed" does not exist`.
- **`unknown` 타입** — PG 에서 아직 타입이 정해지지 않은 리터럴의 상태.\
  예: `pg_typeof(NULL)` · `pg_typeof('x')` 가 둘 다 `unknown` 이다.
- **인덱스(index)** — 열 값을 정렬해 따로 저장해 둔 것. 찾는 값의 위치를 바로 짚게 해 준다.\
  예: `t35_code_idx` 덕에 20,000행 중 1행을 골라내는 데 전부 읽지 않는다.
- **`ref` / `index` (MySQL `EXPLAIN` 의 `type`)** — `ref` 는 인덱스로 값을 짚는 것, `index` 는 **인덱스를 처음부터 끝까지 훑는 것**.\
  예: 같은 질의가 따옴표 하나로 `ref`(rows 1) → `index`(rows 19905) 로 바뀌었다.
- **경고 1292** — MySQL 이 문자열을 수치로 못 읽고 잘라 읽었을 때 남기는 경고.\
  예: `Truncated incorrect DOUBLE value: 'abc'`.
- **경고 1739** — MySQL 이 타입·collation 변환 때문에 인덱스 접근을 포기했다고 알리는 경고.\
  예: `Cannot use ref access on index 't35_code_idx' ...`.
- **`tinyint(1)`** — 1바이트 정수. MySQL 의 `BOOLEAN` 은 이것의 다른 이름이다.\
  예: `SHOW CREATE TABLE` 이 `BOOLEAN` 으로 선언한 열을 `tinyint(1)` 로 보여 준다.

## 더 들어가면

- **PG 의 변환은 「캐스트 카탈로그」에 등록된 것만 일어난다.** `pg_cast` 에 어떤 변환이 암시로 허용되는지가 행으로 들어 있고,\
  등록되지 않은 조합은 **연산자를 찾지 못해** 위 3번의 에러가 된다. 「엔진이 똑똑하지 않아서」가 아니라 **의도된 설계**다.
- **MySQL 의 비교 규칙은 「어느 쪽이 무엇이냐」의 표로 되어 있다.** 한쪽이 수치면 다른 쪽도 수치로, 둘 다 문자열이면 문자열로.\
  그래서 `'10' > '9'` 는 거짓이고 `'10' > 9` 는 참이다 — **같은 두 값이 따옴표 하나로 뒤집힌다.**
- **인덱스를 살리는 일반 처방은 「열을 건드리지 않는 것**」이다. 함수든 암시 변환이든 collation 이든,\
  열이 원래 모습 그대로 비교되면 산다. 39번의 `COLLATE` 사고도 정확히 같은 모양이다.
