# sql/39-collation (문자열 비교와 정렬의 기준) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Collation Support](https://www.postgresql.org/docs/18/collation.html) · [PostgreSQL 18 · CREATE COLLATION](https://www.postgresql.org/docs/18/sql-createcollation.html) · [MySQL 8.4 · Character Sets and Collations](https://dev.mysql.com/doc/refman/8.4/en/charset.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·계획은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **이 주제는 환경이 곧 답이다.** 아래 「환경 확인」 절에 두 서버의 설정을 **직접 찍은 출력**으로 실었다.\
> 다른 설정의 서버에서는 **같은 질의가 다른 답을 낸다** — 그것이 이 주제의 요점이다.\
> **버전** — 도입 버전이 확인된 것은 없어 **버전을 적지 않는다.**\
> **선행** — [37 문자열 함수와 연결 연산](../37-string-functions-and-concatenation/) · 짝이 되는 주제는 [38 패턴 매칭](../38-pattern-matching-like-regex/)

## 한눈에 — 쉽게 말하면

**collation = 「두 문자열 중 어느 것이 먼저인가, 그리고 둘이 같은가」를 정하는 규칙집.**

```text
'abc' = 'ABC'  를 두 서버에 던졌다

PostgreSQL 18.6                      MySQL 8.4.10
(이 DB: en_US.utf8, 결정적)          (기본: utf8mb4_0900_ai_ci)
      거짓                                  참
        ↑                                    ↑
 대소문자가 다르면 다른 값            ci = case insensitive
```

**질의도 데이터도 같은데 답이 다르다.** 바뀐 것은 **설정 하나**다.

| 비유 | 실체 |
|---|---|
| 도서관의 책 꽂는 규칙 | collation |
| 「띄어쓰기·부호는 무시하고 꽂는다」 | 악센트·구두점을 무시하는 collation |
| 「대문자 책과 소문자 책은 같은 칸」 | 대소문자 무시(`_ci`) |
| 「글자 코드 번호 순서로 꽂는다」 | `C` / `utf8mb4_bin` — 바이트 순서 |
| 규칙이 바뀌면 책을 다시 꽂아야 한다 | collation 이 바뀌면 인덱스를 못 쓴다 |

> **collation** — 문자열을 비교·정렬하는 규칙의 이름.\
> 예: `utf8mb4_0900_ai_ci` 에서는 `'abc' = 'ABC'` 가 참이고, `C` 에서는 거짓이다.

**collation 이 정하는 것이 생각보다 넓다.**

```text
= 비교          -> 'abc' = 'ABC' 의 답
ORDER BY        -> 줄 세우는 순서
LIKE / REGEXP   -> 패턴 매칭의 대소문자 판정 (38번)
UNIQUE 제약     -> 'abc' 가 있을 때 'ABC' 를 넣을 수 있나
GROUP BY / DISTINCT -> 같은 그룹으로 접히나
인덱스          -> 어떤 순서로 정렬해 저장했나
```

**마지막 줄이 값비싸다** — 질의에서 collation 을 바꾸면 **그 인덱스를 못 쓴다.**

## 환경 확인 — 이 문서의 결과가 나온 자리

★ **먼저 이것부터 찍어야 한다.** 이 주제에서 「PG 는 ~하다」는 말은 **설정을 밝히지 않으면 거짓**이다.

**PostgreSQL 18.6**

```text
SELECT datname, datcollate, datctype, datlocprovider FROM pg_database WHERE datname='study';
 datname | datcollate |  datctype  | datlocprovider 
---------+------------+------------+----------------
 study   | en_US.utf8 | en_US.utf8 | c
(1 row)

SHOW server_encoding;
 server_encoding 
-----------------
 UTF8
(1 row)

\dO
                                List of collations
 Schema | Name | Provider | Collate | Ctype | Locale | ICU Rules | Deterministic? 
--------+------+----------+---------+-------+--------+-----------+----------------
(0 rows)

SELECT count(*) AS total FROM pg_collation;
 total 
-------
   880
(1 row)

SELECT collname, collprovider, collisdeterministic FROM pg_collation
 WHERE collname IN ('default','C','POSIX','ucs_basic','en_US.utf8','en-US-x-icu') ORDER BY collname;
  collname   | collprovider | collisdeterministic 
-------------+--------------+---------------------
 C           | c            | t
 POSIX       | c            | t
 default     | d            | t
 en-US-x-icu | i            | t
 en_US.utf8  | c            | t
 ucs_basic   | b            | t
(6 rows)
```

읽는 법.

- **`datcollate = en_US.utf8`** — 이 데이터베이스의 기본 비교·정렬 규칙이다.
- **`datlocprovider = c`** — 제공자가 **libc**(운영체제의 로케일)다. `i` 면 ICU, `b` 면 PG 내장이다.
- **`\dO` 가 0행** — `\dO` 는 **사용자 스키마의 collation 만** 보여 준다. 시스템 것은 `pg_collation` 에 880개 있다.\
  「**없다」가 아니라 「내가 만든 것이 아직 없다**」는 뜻이다. 이 구분을 놓치면 환경 보고가 틀린다.
- **`collisdeterministic = t`** — 전부 **결정적**이다. 이 말의 뜻은 아래 5번에서 푼다.

**MySQL 8.4.10**

```text
SELECT @@character_set_server, @@collation_server, @@collation_connection, @@collation_database;
+------------------------+--------------------+------------------------+----------------------+
| @@character_set_server | @@collation_server | @@collation_connection | @@collation_database |
+------------------------+--------------------+------------------------+----------------------+
| utf8mb4                | utf8mb4_0900_ai_ci | utf8mb4_0900_ai_ci     | utf8mb4_0900_ai_ci   |
+------------------------+--------------------+------------------------+----------------------+

SHOW COLLATION WHERE Charset='utf8mb4' AND Collation IN
  ('utf8mb4_0900_ai_ci','utf8mb4_0900_as_ci','utf8mb4_0900_as_cs','utf8mb4_bin',
   'utf8mb4_general_ci','utf8mb4_ja_0900_as_cs');
+-----------------------+---------+-----+---------+----------+---------+---------------+
| Collation             | Charset | Id  | Default | Compiled | Sortlen | Pad_attribute |
+-----------------------+---------+-----+---------+----------+---------+---------------+
| utf8mb4_0900_ai_ci    | utf8mb4 | 255 | Yes     | Yes      |       0 | NO PAD        |
| utf8mb4_0900_as_ci    | utf8mb4 | 305 |         | Yes      |       0 | NO PAD        |
| utf8mb4_0900_as_cs    | utf8mb4 | 278 |         | Yes      |       0 | NO PAD        |
| utf8mb4_bin           | utf8mb4 |  46 |         | Yes      |       1 | PAD SPACE     |
| utf8mb4_general_ci    | utf8mb4 |  45 |         | Yes      |       1 | PAD SPACE     |
| utf8mb4_ja_0900_as_cs | utf8mb4 | 303 |         | Yes      |       0 | NO PAD        |
+-----------------------+---------+-----+---------+----------+---------+---------------+

SELECT COUNT(*) AS total_collations FROM information_schema.COLLATIONS;
+------------------+
| total_collations |
+------------------+
|              286 |
+------------------+

SELECT COUNT(*) AS utf8mb4_collations FROM information_schema.COLLATIONS WHERE CHARACTER_SET_NAME='utf8mb4';
+--------------------+
| utf8mb4_collations |
+--------------------+
|                 89 |
+--------------------+
```

읽는 법.

- **`Default: Yes` 가 `utf8mb4_0900_ai_ci`** — 이것이 이 서버의 기본값이다.
- **이름이 규칙이다** — `ai` = accent insensitive(악센트 무시) · `ci` = case insensitive(대소문자 무시) ·\
  `as` = accent sensitive · `cs` = case sensitive · `bin` = 바이트값 비교.
- **`Pad_attribute`** — `PAD SPACE` 는 **뒤 공백을 무시**하고 비교한다. 0900 계열은 `NO PAD` 다(아래 4번).
- ★ **`collation_connection` 이 중요하다.** 클라이언트를 `--default-character-set=utf8mb4` 없이 붙이면\
  이 값이 `latin1_swedish_ci` 로 나온다(실제로 처음 붙였을 때 그랬다). **연결 설정이 답을 바꾼다.**

**이 문서의 모든 출력은 위 환경에서 나온 것이다.**

## 이 주제가 답하려는 질문

1. **같은 `=` 비교가 왜 두 엔진에서 다른 답을 내나?**
2. **정렬 순서는 누가 정하나?** — 그리고 그것을 한 질의에서 바꿀 수 있나.
3. **collation 을 바꾸면 무엇을 잃나?**

## 예시 데이터 — 이 묶음이 공유하는 것

정렬·비교는 리터럴 목록으로 본다. 인덱스 실험만 별도 표 `t39` 를 쓰고 **작업 후 지웠다.**

```text
정렬 실험용 여섯 값
  'apple'  'Banana'  'apricot'  'BANANA'  '_x'  'Zebra'
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   대소문자가 섞였고, 구두점으로 시작하는 값이 하나 있다
```

```sql
CREATE TABLE t39 (id int PRIMARY KEY, code varchar(20) NOT NULL);  -- code 에 인덱스, 20,000행
```

`emp`·`dept` 는 읽기만 하고 바꾸지 않는다.

## 동작 방식

### 1. ★ `=` 비교 — 같은 질의, 다른 답

**언제 쓰나** — 문자열을 비교하는 모든 자리. **이 주제의 출발점이다.**

```text
### SQL: SELECT 'abc' = 'ABC' AS same_case, 'e' = 'é' AS accent, 'a' = 'a ' AS trailing_space;
--- PG 18.6 ---
 same_case | accent | trailing_space 
-----------+--------+----------------
 f         | f      | f
(1 row)

--- MySQL 8.4.10 ---
+-----------+--------+----------------+
| same_case | accent | trailing_space |
+-----------+--------+----------------+
|         1 |      1 |              0 |
+-----------+--------+----------------+
```

```text
                       PG(en_US.utf8)   MySQL(utf8mb4_0900_ai_ci)
'abc' = 'ABC'                거짓              참    <- ci: 대소문자 무시
'e'   = 'é'                  거짓              참    <- ai: 악센트 무시
'a'   = 'a '                 거짓              거짓  <- NO PAD: 뒤 공백을 안 무시
```

그림 해설 — **앞의 둘이 갈리고 셋째는 같다.** 셋째가 같은 이유는 0900 계열이 `NO PAD` 이기 때문이다(4번).\
대가 — 「같은 값인가」의 판정이 다르면 **`UNIQUE`·`GROUP BY`·`DISTINCT`·`JOIN` 이 전부 다르게 돈다**(3번).

### 2. ★ 정렬 — 같은 여섯 값, 네 가지 순서

**언제 쓰나** — `ORDER BY` 결과가 예상과 다를 때. **페이지네이션이 여기서 깨진다.**

```text
(A) PostgreSQL 18.6                     (B) MySQL 8.4.10
기본 (en_US.utf8)                        기본 (utf8mb4_0900_ai_ci)
SELECT v FROM (VALUES ('apple'),        SELECT v FROM ( ... 같은 여섯 값 ... ) t
  ('Banana'),('apricot'),('BANANA'),      ORDER BY v;
  ('_x'),('Zebra')) t(v) ORDER BY v;
--- 실제 출력 ---                       --- 실제 출력 ---
    v                                   +---------+
---------                               | v       |
 apple                                  +---------+
 apricot                                | _x      |   <- 맨 앞
 Banana                                 | apple   |
 BANANA                                 | apricot |
 _x        <- ★ 여기 있다               | Banana  |
 Zebra                                  | BANANA  |
(6 rows)                                | Zebra   |
                                        +---------+
```

두 그림의 결론 — **`'_x'` 의 자리가 다르다.**\
PG 의 `en_US.utf8` 은 **구두점을 1차 비교에서 무시**하므로 `'_x'` 가 사실상 `'x'` 로 취급되어\
`BANANA` 와 `Zebra` 사이에 온다. MySQL 은 `_` 에 자기 무게를 줘서 맨 앞에 놓는다.

**바이트 순서로 바꾸면 두 엔진이 같아진다.**

```text
(A) PostgreSQL 18.6                     (B) MySQL 8.4.10
... ORDER BY v COLLATE "C";             ... ORDER BY v COLLATE utf8mb4_bin;
--- 실제 출력 ---                       --- 실제 출력 ---
    v                                   +---------+
---------                               | v       |
 BANANA                                 +---------+
 Banana                                 | BANANA  |
 Zebra                                  | Banana  |
 _x                                     | Zebra   |
 apple                                  | _x      |
 apricot                                | apple   |
(6 rows)                                | apricot |
                                        +---------+
```

두 그림의 결론 — **한 줄도 안 갈렸다.** 대문자가 전부 앞, 그다음 `_`, 그다음 소문자 —\
이것이 **ASCII 코드값 순서**다.

```text
네 순서를 한자리에 놓으면

PG 기본        apple  apricot  Banana  BANANA  _x     Zebra
MySQL 기본     _x     apple    apricot Banana  BANANA Zebra
PG COLLATE C   BANANA Banana   Zebra   _x      apple  apricot
MySQL bin      BANANA Banana   Zebra   _x      apple  apricot
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
               아래 둘은 같고, 위 둘은 서로도 다르고 아래와도 다르다
```

그림 해설 — **「사람이 보기 좋은 순서」는 서로 다르고, 「바이트 순서」는 하나다.**\
대가 — 키셋 페이지네이션([목록의 **09번 주제**](../09-limit-offset-keyset-pagination/))은 **정렬 순서가 안정적이어야** 성립한다.\
서버를 옮기거나 locale 이 바뀌면 **같은 데이터가 다르게 줄 서서 페이지가 어긋난다.**

### 3. ★ 같은 DDL, 다른 결과 — `UNIQUE` 제약

**언제 쓰나** — 아이디·이메일·코드에 유니크 제약을 걸 때. **가장 비싼 차이다.**

```text
(A) PostgreSQL 18.6                     (B) MySQL 8.4.10
BEGIN;                                   START TRANSACTION;
CREATE TEMP TABLE t39b (v text UNIQUE);  CREATE TEMPORARY TABLE t39 (v varchar(10) UNIQUE);
INSERT INTO t39b VALUES ('abc');         INSERT INTO t39 VALUES ('abc');
INSERT INTO t39b VALUES ('ABC');         INSERT INTO t39 VALUES ('ABC');
SELECT * FROM t39b ORDER BY v;           ROLLBACK;
ROLLBACK;
--- 실제 출력 ---                        --- 실제 출력 ---
INSERT 0 1                               ERROR 1062 (23000) at line 4:
INSERT 0 1                                 Duplicate entry 'ABC' for key 't39.v'
  v  
-----
 abc
 ABC
(2 rows)
```

두 그림의 결론 — **사실상 같은 DDL 인데 한쪽은 두 행이 들어가고 한쪽은 거부된다.**\
「대소문자가 다른 아이디를 허용할 것인가」가 **문서 어디에도 안 적힌 채** 엔진 기본값으로 정해진다.

대가 — MySQL 을 쓰다 PG 로 옮기면 **`'Admin'` 과 `'admin'` 이 둘 다 가입된다.**\
반대로 PG 에서 MySQL 로 옮기면 **기존 데이터가 적재 중 `ERROR 1062` 로 막힌다.**

**PG 에서 MySQL 처럼 만들려면 비결정적 collation 을 만든다**(5번).

```text
--- PG 18.6 ---
CREATE COLLATION nd_ci (provider = icu, locale = 'und-u-ks-level2', deterministic = false);
BEGIN;
CREATE TEMP TABLE t39 (v text COLLATE nd_ci UNIQUE);
INSERT INTO t39 VALUES ('abc');
INSERT INTO t39 VALUES ('ABC');
ERROR:  duplicate key value violates unique constraint "t39_v_key"
DETAIL:  Key (v)=(ABC) already exists.
ROLLBACK;
```

그림 해설 — **이제 PG 도 거부한다.** `DETAIL` 이 `Key (v)=(ABC)` 라고 알려 준다 —\
`'abc'` 와 `'ABC'` 를 **같은 키로 본 것**이다.

### 4. 뒤 공백 — `PAD SPACE` 와 `NO PAD`

**언제 쓰나** — 입력에 공백이 섞일 때. 그리고 **collation 을 고를 때 같이 보게 되는 칸**이다.

```text
--- MySQL 8.4.10 ---
SELECT 'a' = 'a ' COLLATE utf8mb4_general_ci AS pad_space,
       'a' = 'a ' COLLATE utf8mb4_0900_ai_ci AS no_pad;
+-----------+--------+
| pad_space | no_pad |
+-----------+--------+
|         1 |      0 |
+-----------+--------+
```

```text
환경 확인 절의 SHOW COLLATION 출력과 맞춰 읽는다

utf8mb4_general_ci  Pad_attribute = PAD SPACE  ->  'a' = 'a ' 이 참
utf8mb4_0900_ai_ci  Pad_attribute = NO PAD     ->  'a' = 'a ' 이 거짓
```

그림 해설 — **같은 서버, 같은 문장인데 collation 하나로 뒤집힌다.**\
1번에서 `trailing_space` 가 두 엔진 다 거짓이었던 것은 **기본이 `NO PAD` 이기 때문**이지\
「MySQL 이 공백을 구분한다」는 성질이 아니다.

PG 쪽은 `text`/`varchar` 에서 뒤 공백을 구분한다.

```text
--- PG 18.6 ---
SELECT 'a' = 'a ' AS trailing_space;
 trailing_space 
----------------
 f
(1 row)
```

대가 — `char(n)` 은 얘기가 다르다. 37번에서 본 대로 **`char` 는 공백으로 채워지고 비교에서 무시**된다.\
「공백이 의미 있나」는 **타입과 collation 둘 다** 보고 판단해야 한다.

### 5. 한 질의에서 바꾸기 — `COLLATE` 절

**언제 쓰나** — 특정 비교·정렬만 규칙을 바꾸고 싶을 때.

```text
--- PG 18.6 ---
SELECT 'abc' = 'ABC' COLLATE "C" AS c_cmp;
 c_cmp 
-------
 f
(1 row)

CREATE COLLATION nd_ci (provider = icu, locale = 'und-u-ks-level2', deterministic = false);
SELECT 'abc' = 'ABC' COLLATE nd_ci AS ci_cmp;
 ci_cmp 
--------
 t
(1 row)

SELECT 'e' = 'é' COLLATE nd_ci AS accent_level2;
 accent_level2 
---------------
 f
(1 row)

CREATE COLLATION nd_ai (provider = icu, locale = 'und-u-ks-level1', deterministic = false);
SELECT 'e' = 'é' COLLATE nd_ai AS accent_level1, 'abc' = 'ABC' COLLATE nd_ai AS case_level1;
 accent_level1 | case_level1 
---------------+-------------
 t             | t
(1 row)
```

```text
ICU 의 "강도(strength) 레벨" 이 무엇을 무시할지 정한다

level1 (primary)   글자 자체만 본다        -> 악센트도 대소문자도 무시
level2 (secondary) 악센트까지 본다        -> 대소문자만 무시
level3 (tertiary)  대소문자까지 본다      -> 기본값. 아무것도 무시 안 한다
```

그림 해설 — `nd_ci`(level2)는 **대소문자만** 무시하고 악센트는 구분한다.\
`nd_ai`(level1)는 **둘 다** 무시한다 — MySQL 의 `ai_ci` 와 같은 자리다.

> **결정적 collation(deterministic)** — 「바이트가 다르면 다른 값」을 보장하는 collation.\
> 예: PG 의 기본 collation 은 전부 결정적이라 `'abc' = 'ABC'` 가 거짓이다.\
> 대소문자를 무시하게 하려면 **결정적이기를 포기**해야 한다(`deterministic = false`).

MySQL 쪽도 `COLLATE` 절이 있다.

```text
--- MySQL 8.4.10 ---
SELECT 'abc' COLLATE utf8mb4_0900_as_cs = 'ABC' AS cs_cmp;
+--------+
| cs_cmp |
+--------+
|      0 |
+--------+
```

**규칙 이름은 서로 모른다.**

```text
### SQL: SELECT 'abc' LIKE 'A%' COLLATE utf8mb4_0900_as_cs AS r;
--- PG 18.6 ---
ERROR:  collation "utf8mb4_0900_as_cs" for encoding "UTF8" does not exist
LINE 1: SELECT 'abc' LIKE 'A%' COLLATE utf8mb4_0900_as_cs AS r;
                               ^
--- MySQL 8.4.10 ---
+------+
| r    |
+------+
|    0 |
+------+
```

**섞으면 양쪽 다 거부한다.**

```text
--- PG 18.6 ---
SELECT ('abc' COLLATE "C") = ('ABC' COLLATE "en_US.utf8") AS r;
ERROR:  collation mismatch between explicit collations "C" and "en_US.utf8"
LINE 1: SELECT ('abc' COLLATE "C") = ('ABC' COLLATE "en_US.utf8") AS...
                                            ^

--- MySQL 8.4.10 ---
SELECT ('abc' COLLATE utf8mb4_0900_as_cs) = ('ABC' COLLATE utf8mb4_general_ci) AS r;
ERROR 1267 (HY000) at line 1: Illegal mix of collations
  (utf8mb4_0900_as_cs,EXPLICIT) and (utf8mb4_general_ci,EXPLICIT) for operation '='
```

그림 해설 — **두 엔진 다 「어느 규칙으로 비교할지 못 정하겠다」고 한다.** 임의로 한쪽을 고르지 않는다.\
대가 — 서로 다른 collation 의 열을 조인하면 **런타임에 터진다.** 스키마 단계에서 맞춰야 한다.

### 6. ★ collation 을 바꾸면 인덱스를 잃는다

**언제 쓰나** — `COLLATE` 를 처방으로 쓰기 전에. **공짜가 아니다.**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t39 WHERE code = 'C000123';
                   QUERY PLAN                   
------------------------------------------------
 Index Scan using t39_code_idx on t39
   Index Cond: ((code)::text = 'C000123'::text)
(2 rows)

EXPLAIN (COSTS OFF) SELECT * FROM t39 WHERE code COLLATE "C" = 'C000123';
                 QUERY PLAN                 
--------------------------------------------
 Seq Scan on t39
   Filter: ((code)::text = 'C000123'::text)
(2 rows)
```

그림 해설 — **`COLLATE "C"` 를 붙였더니 `Index Scan` 이 `Seq Scan` 이 됐다.**\
인덱스는 `en_US.utf8` 순서로 정렬돼 있는데, 질의는 `C` 순서의 비교를 요구한다 — **쓸 수가 없다.**

**그 collation 으로 인덱스를 따로 만들면 다시 탄다.**

```text
--- PG 18.6 ---
CREATE INDEX t39_code_c_idx ON t39 (code COLLATE "C");
ANALYZE t39;
EXPLAIN (COSTS OFF) SELECT * FROM t39 WHERE code COLLATE "C" = 'C000123';
                   QUERY PLAN                   
------------------------------------------------
 Index Scan using t39_code_c_idx on t39
   Index Cond: ((code)::text = 'C000123'::text)
(2 rows)
```

**MySQL 도 같은 일이 일어나고, 경고로 말해 준다.**

```text
--- MySQL 8.4.10 ---
EXPLAIN SELECT * FROM t39 WHERE code = 'C000123';
+----+-------+------+---------------+--------------+---------+-------+------+-------------+
| id | table | type | possible_keys | key          | key_len | ref   | rows | Extra       |
+----+-------+------+---------------+--------------+---------+-------+------+-------------+
|  1 | t39   | ref  | t39_code_idx  | t39_code_idx | 82      | const |    1 | Using index |
+----+-------+------+---------------+--------------+---------+-------+------+-------------+

EXPLAIN SELECT * FROM t39 WHERE code = 'C000123' COLLATE utf8mb4_bin;
+----+-------+-------+---------------+--------------+---------+------+------+--------------------------+
| id | table | type  | possible_keys | key          | key_len | ref  | rows | Extra                    |
+----+-------+-------+---------------+--------------+---------+------+------+--------------------------+
|  1 | t39   | range | t39_code_idx  | t39_code_idx | 82      | NULL |    1 | Using where; Using index |
+----+-------+-------+---------------+--------------+---------+------+------+--------------------------+

SHOW WARNINGS;
+---------+------+-----------------------------------------------------------------------+
| Level   | Code | Message                                                               |
+---------+------+-----------------------------------------------------------------------+
| Warning | 1739 | Cannot use ref access on index 't39_code_idx' due to type or          |
|         |      | collation conversion on field 'code'                                  |
+---------+------+-----------------------------------------------------------------------+
```

(폭에 맞춰 `select_type`·`partitions`·`filtered` 칸을 뺐고, 경고는 줄바꿈만 접었다. 문구는 서버가 낸 그대로다.)

그림 해설 — `type` 이 **`ref` → `range`** 로 내려갔고 **경고 1739** 가 떴다.\
여기서는 `range` 접근이 남아 `rows` 가 1 그대로지만, **`ref` 접근은 포기됐다**고 서버가 명시한다.\
같은 경고를 35번에서는 타입 변환으로 봤다 — **원인은 달라도 결과는 같다.**

대가 — 「대소문자 무시 검색」을 질의마다 `COLLATE` 로 처리하면 **그때마다 인덱스를 잃는다.**\
제대로 된 처방은 **열의 collation 자체를 요구사항에 맞게 정하는 것**이다.

## 문법 — 형태와 규칙

collation 은 「**어디에 붙일 수 있나**」로 읽는다.

```sql
-- 열에 붙인다 (스키마 단계 — 인덱스가 이 규칙으로 만들어진다)
CREATE TABLE t (v text COLLATE "en_US.utf8");              -- PG
CREATE TABLE t (v varchar(10) COLLATE utf8mb4_0900_as_cs); -- MySQL

-- 식에 붙인다 (질의 단계 — 인덱스를 잃는다)
... WHERE v COLLATE "C" = 'x'                              -- PG
... WHERE v = 'x' COLLATE utf8mb4_bin                      -- MySQL
... ORDER BY v COLLATE "C"                                 -- PG
... ORDER BY v COLLATE utf8mb4_bin                         -- MySQL

-- 인덱스에 붙인다 (그 규칙 전용 인덱스를 만든다)
CREATE INDEX i ON t (v COLLATE "C");                       -- PG
```

규칙 여덟.

1. **collation 이 `=`·`ORDER BY`·`LIKE`·`UNIQUE`·`GROUP BY`·`DISTINCT` 를 전부 정한다.**
2. **PG 기본 collation 은 결정적**이라 `'abc' = 'ABC'` 가 거짓이다.
3. **MySQL 기본은 `utf8mb4_0900_ai_ci`** 라 대소문자·악센트를 무시한다.
4. **대소문자 무시를 PG 에서 하려면 `deterministic = false` collation 이 필요하다.**
5. **이름 규칙** — `ai`/`as`(악센트) · `ci`/`cs`(대소문자) · `bin`(바이트).
6. **`Pad_attribute`** 가 뒤 공백을 무시할지 정한다. 0900 계열은 `NO PAD` 다.
7. **서로 다른 collation 을 명시적으로 섞으면 양쪽 다 에러**다(PG `collation mismatch` / MySQL `ERROR 1267`).
8. **식에 `COLLATE` 를 붙이면 그 열의 인덱스를 못 쓴다.** 열이나 인덱스에 붙여야 산다.

#### 방언 요약

| 자리 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 기본 규칙 | DB 의 `datcollate`(이 서버: `en_US.utf8`, libc) | `utf8mb4_0900_ai_ci` |
| `'abc' = 'ABC'` | **`f`** | **`1`** |
| `'e' = 'é'` | **`f`** | **`1`** |
| `'a' = 'a '` | `f` | `0` — **같다**(`NO PAD`) |
| `'a' = 'a ' COLLATE 일반ci` | 해당 이름 없음 | `1` (`PAD SPACE`) |
| 정렬에서 `'_x'` 의 자리 | `BANANA` 와 `Zebra` 사이(구두점 무시) | 맨 앞 |
| 바이트 순서 이름 | `C` / `POSIX` / `ucs_basic` | `utf8mb4_bin` |
| 바이트 순서 정렬 결과 | `BANANA Banana Zebra _x apple apricot` | **한 줄도 안 갈림** |
| `varchar UNIQUE` 에 `'abc'`+`'ABC'` | **둘 다 들어간다** | **`ERROR 1062`** |
| 대소문자 무시 만들기 | `CREATE COLLATION ... deterministic = false` | 기본이 그렇다 |
| 대소문자 구분 만들기 | 기본이 그렇다 | `COLLATE utf8mb4_0900_as_cs` |
| collation 섞기 | `ERROR: collation mismatch` | **`ERROR 1267`** Illegal mix of collations |
| 식에 `COLLATE` → 인덱스 | `Index Scan` → `Seq Scan` | `ref` → `range` + 경고 1739 |
| 그 collation 전용 인덱스 | `CREATE INDEX ... (v COLLATE "C")` | 열의 collation 을 바꿔야 한다 |
| 목록 보기 | `\dO`(사용자 것만) · `pg_collation`(880개) | `SHOW COLLATION`(286개) |

## 어디서 틀리나

- **「PG 는 대소문자를 구분한다」를 언어의 성질로 외운다.**\
  **DB 의 collation 이 정한다.** 비결정적 collation 을 쓰면 PG 도 무시한다(5번). 서버 설정부터 확인한다.
- **`\dO` 가 0행인 것을 「collation 이 없다」로 읽는다.**\
  `\dO` 는 **사용자 스키마의 것만** 보여 준다. 시스템 것은 `pg_collation` 에 880개 있다.
- **MySQL 클라이언트 설정을 안 본다.**\
  `--default-character-set` 없이 붙으면 `collation_connection` 이 `latin1_swedish_ci` 가 된다.\
  **서버 설정이 아니라 연결 설정이 비교 결과를 바꾼다.**
- **`UNIQUE` 제약의 의미가 같다고 믿는다.**\
  같은 DDL 이 PG 에서는 `'abc'`/`'ABC'` 둘 다 허용하고 MySQL 에서는 `ERROR 1062` 다.\
  **요구사항을 스키마에 적어야** 한다 — 엔진 기본값에 맡기면 이식할 때 드러난다.
- **질의마다 `COLLATE` 로 해결한다.**\
  **그때마다 인덱스를 잃는다.** 열 정의를 고치거나 그 collation 전용 인덱스를 만든다.
- **다른 collation 의 열을 조인한다.**\
  `ERROR 1267`(MySQL) / `collation mismatch`(PG). 스키마가 커진 뒤에 드러나므로 고치기 비싸다.
- **정렬 결과가 안정적이라고 믿는다.**\
  같은 데이터가 collation 에 따라 **네 가지 순서**로 줄 섰다(2번). 키셋 페이지네이션이 여기서 깨진다.
- **`UPPER()` 로 대소문자를 맞춘다.**\
  열에 함수를 씌우면 인덱스를 잃는다(37번 11번). MySQL 에서는 **애초에 불필요**하다.
- **`ai`(악센트 무시)를 대소문자와 헷갈린다.**\
  `utf8mb4_0900_as_ci` 는 **악센트는 구분하고 대소문자만 무시**한다. 이름 두 칸을 따로 읽는다.

## 구현 세부사항 대 언어 보장

- **언어(문서)가 정한 것** — `COLLATE` 절의 문법, collation 이 비교·정렬·제약을 정한다는 규칙,\
  결정적/비결정적의 의미, 섞였을 때 에러가 난다는 것. 두 매뉴얼의 collation 페이지가 정본이다.
- **★ 설정이 정하는 것 — 이 주제의 결과 거의 전부.**\
  1·2·3번의 답은 **이 서버의 collation** 이 낸 것이다. 다른 설정이면 **같은 엔진에서도 다른 답**이 나온다.\
  그래서 이 문서는 「환경 확인」 절을 본문 앞에 두었다.
- **운영체제가 정하는 것** — PG 의 libc 제공자(`datlocprovider = c`)는 **OS 의 로케일 라이브러리**를 쓴다.\
  같은 PG 버전이라도 **OS·glibc 판이 다르면 정렬이 달라질 수 있다.** 그래서 ICU 제공자가 있는 것이다.\
  이 문서의 2번 결과는 **이 컨테이너 이미지**(`postgres:18`, Debian)에서 나온 것이다.
- **옵티마이저가 정하는 것** — 6번의 `EXPLAIN` 출력. 계획은 관찰이지 보장이 아니다.\
  MySQL 이 `ref` 를 포기하고도 `range` 를 쓴 것은 이 표·이 통계에서의 판단이다.
- **인코딩과 collation 은 다른 것이다.** 인코딩은 「글자를 바이트로 어떻게 쓰나」,\
  collation 은 「그 글자들을 어떻게 비교·정렬하나」다. 인코딩은 [`foundations/data-representation`](../../../../data-representation/)이 정본이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 열 정의에 collation 을 명시한다.** 「대소문자를 무시할 것인가」는 **요구사항**이다. 스키마에 적는다.
- **쓴다 — 식별자 열에 `bin`/`C` 계열.** 코드·토큰·해시처럼 **바이트가 곧 값**인 열은 바이트 순서가 맞다.\
  덤으로 38번의 `LIKE` 접두사 인덱스 문제도 사라진다.
- **쓴다 — 사람이 읽는 이름 열에 언어별 collation.** 정렬이 사용자에게 보이는 곳.
- **안 쓴다 — 질의마다 `COLLATE`.** 인덱스를 잃는다. 한 번 쓰는 보고서 질의라면 괜찮다.
- **안 쓴다 — `UPPER()`/`LOWER()` 로 대소문자 무시.** 같은 이유다.
- **조심한다 — collation 변경은 인덱스 재구축이다.** 운영 중이면 큰 작업이다([목록의 **42번 주제**](../42-create-alter-drop-table/)).
- **조심한다 — 조인하는 열들의 collation.** 다르면 런타임 에러이거나 조용히 느려진다.

## 핵심 문장

- collation 은 **「같은가」와 「누가 먼저인가」를 정하는 규칙집**이고, 엔진 기본값이 정반대다.
- **PG 기본은 결정적**(`'abc' ≠ 'ABC'`), **MySQL 기본은 `ai_ci`**(`'abc' = 'ABC'`).
- 같은 여섯 값이 **네 가지 순서**로 줄 선다. **바이트 순서(`C`·`bin`)에서만 두 엔진이 같다.**
- **같은 `varchar UNIQUE` DDL 이 PG 에서는 `'abc'`/`'ABC'` 둘 다 받고 MySQL 에서는 `ERROR 1062`** 다.
- PG 에서 대소문자를 무시하려면 **`deterministic = false`** collation 을 만들어야 한다.
- 이름 규칙은 **`ai`/`as`(악센트) · `ci`/`cs`(대소문자) · `bin`(바이트)** 이다.
- **collation 을 섞으면 양쪽 다 에러**다 — PG `collation mismatch`, MySQL `ERROR 1267`.
- **식에 `COLLATE` 를 붙이면 인덱스를 잃는다** — PG 는 `Seq Scan`, MySQL 은 경고 1739.
- **환경을 안 밝힌 collation 주장은 거짓이다.** `pg_database`·`SHOW COLLATION` 을 먼저 찍는다.

## 관련 자료

- [PostgreSQL 18 · Collation Support](https://www.postgresql.org/docs/18/collation.html) — 제공자·결정성·`COLLATE` 절.
- [PostgreSQL 18 · CREATE COLLATION](https://www.postgresql.org/docs/18/sql-createcollation.html) — `deterministic` 옵션.
- [MySQL 8.4 · Character Sets, Collations, Unicode](https://dev.mysql.com/doc/refman/8.4/en/charset.html) — 이름 규칙과 `PAD` 속성.
- [`foundations/data-representation`](../../../../data-representation/) — **경계**: 글자를 바이트로 어떻게 쓰는가(인코딩·코드포인트)는 **거기가 정본**이고,\
  여기는 **그 글자들을 SQL 이 어떤 규칙으로 비교·정렬하는가**만 다룬다. 인코딩 규칙은 한 줄도 쓰지 않는다.
- [37 문자열 함수와 연결 연산](../37-string-functions-and-concatenation/) — 문자열을 만들고 자르는 연산.
- [38 패턴 매칭](../38-pattern-matching-like-regex/) — `LIKE` 의 대소문자 판정과, PG 의 접두사 인덱스 문제가 여기서 온다.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — 경고 1739 의 다른 원인(타입 변환).
- [SQL 주제 목록](../README.md) — 08(ORDER BY) · 09(키셋 페이지네이션) · 42(테이블 정의) · 43(UNIQUE) · 47(인덱스를 언제 타나) 가 이웃이다.

## 용어 풀이

- **collation** — 문자열을 비교·정렬하는 규칙의 이름.\
  예: `utf8mb4_0900_ai_ci` 에서 `'abc' = 'ABC'` 가 참이다.
- **인코딩(character set)** — 글자를 바이트로 적는 방식. collation 과 다른 층이다.\
  예: `utf8mb4` 는 인코딩, `utf8mb4_0900_ai_ci` 는 그 위의 비교 규칙이다.
- **결정적 collation(deterministic)** — 「바이트가 다르면 다른 값」을 보장하는 collation.\
  예: PG 기본 collation 은 전부 결정적이라 `'abc' = 'ABC'` 가 거짓이다.
- **`ai` / `as`** — accent insensitive / sensitive. 악센트를 무시하나 구분하나.\
  예: `ai` 에서 `'e' = 'é'` 가 참이다.
- **`ci` / `cs`** — case insensitive / sensitive. 대소문자를 무시하나 구분하나.\
  예: `cs` 인 `utf8mb4_0900_as_cs` 에서 `'abc' = 'ABC'` 가 거짓이다.
- **`bin` / `C`** — 바이트값 그대로 비교하는 규칙.\
  예: 두 엔진에서 정렬 결과가 한 줄도 안 갈린 유일한 규칙이다.
- **`PAD SPACE` / `NO PAD`** — 비교할 때 뒤 공백을 무시하나 안 하나.\
  예: `utf8mb4_general_ci`(PAD SPACE)에서 `'a' = 'a '` 가 참, `utf8mb4_0900_ai_ci`(NO PAD)에서 거짓.
- **제공자(collation provider)** — PG 에서 규칙을 어디서 가져오는가. `c`=libc · `i`=ICU · `b`=내장.\
  예: 이 DB 는 `c` 라 **OS 의 로케일**을 따른다.
- **ICU 강도 레벨(strength)** — 몇 번째 차이까지 볼지 정하는 단계.\
  예: `level1` 은 악센트·대소문자를 둘 다 무시하고, `level2` 는 악센트만 구분한다.
- **`ERROR 1267`** — MySQL 이 서로 다른 collation 을 섞었다고 거부하는 에러.\
  예: `Illegal mix of collations (utf8mb4_0900_as_cs,EXPLICIT) and (utf8mb4_general_ci,EXPLICIT)`.
- **경고 1739** — MySQL 이 타입·collation 변환 때문에 인덱스 접근을 포기했다고 알리는 경고.\
  예: `Cannot use ref access on index 't39_code_idx' ...`.

## 더 들어가면

- **PG 가 대소문자 무시를 「비결정적」이라 부르는 이유**는 정직하다.\
  `'abc'` 와 `'ABC'` 를 같다고 하면, **같은 키에 서로 다른 바이트열이 들어간다.**\
  그러면 「이 키의 값은 정확히 무엇인가」에 답이 하나가 아니게 된다 — 그 성질을 포기한다고 이름에 적은 것이다.
- **그래서 비결정적 collation 에는 제약이 따른다.** PG 문서가 몇 가지 연산의 제한을 적어 둔다.\
  다만 이 서버에서 `'abc' LIKE 'ABC' COLLATE nd_ci` 는 **참으로 돌았다** — 안 되는 것과 되는 것을 **직접 던져 확인**한다.
- **MySQL 의 `0900` 은 Unicode CLDR 판본 번호**에서 온 이름이다. 그래서 `utf8mb4_general_ci`(옛 규칙)와\
  `utf8mb4_0900_ai_ci`(새 규칙)의 **정렬 결과가 다르다.** 「둘 다 ci 니까 같겠지」가 틀린다.
- **collation 은 인덱스의 일부다.** 이것이 6번의 모든 현상을 설명한다 —\
  인덱스는 「어떤 순서로 정렬해 저장했나」이고, 질의가 다른 순서를 요구하면 **그 정렬은 쓸모가 없다.**\
  38번에서 PG 가 접두사 `LIKE` 를 못 탄 것도, 35번에서 타입 변환으로 인덱스를 잃은 것도 **같은 한 문장**이다.
