# sql/39-collation (문자열 비교와 정렬의 기준) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·계획은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **환경 조건** — PG `datcollate` = `en_US.utf8`(`datlocprovider` = `c`, libc) · MySQL `collation_server`·`collation_connection` = `utf8mb4_0900_ai_ci`.\
> **다른 설정의 서버에서는 같은 질의가 다른 답을 낸다.** 0번에 확인 방법과 실제 출력을 실었다.\
> 실험 표 `t39` 와 임시 collation(`nd_ci`·`nd_ai`)은 **작업 후 전부 지웠다.** `emp`·`dept` 는 읽기만 했다.\
> 문서 근거는 [PG 18 Collation Support](https://www.postgresql.org/docs/18/collation.html) · [PG 18 CREATE COLLATION](https://www.postgresql.org/docs/18/sql-createcollation.html) · [MySQL 8.4 Character Sets and Collations](https://dev.mysql.com/doc/refman/8.4/en/charset.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 0. 환경 확인 — **이것을 안 찍으면 아래 답은 전부 거짓이다**

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
```

**왜 이걸 먼저 하나**

```text
"PG 는 대소문자를 구분한다"  <- 언어의 성질처럼 들리지만 아니다
        ↓
정확히는 "이 DB 의 datcollate 가 결정적 collation 이라 구분한다"
        ↓
비결정적 collation 을 쓰면 PG 도 안 구분한다 (4번에서 실측한다)
```

★ **MySQL 은 연결 설정도 봐야 한다.** `--default-character-set=utf8mb4` 없이 붙였을 때\
이 서버의 `@@collation_connection` 은 **`latin1_swedish_ci`** 였다. 서버 설정이 아니라 **연결이 답을 바꾼다.**

---

### 1. ★ 같은 비교, 다른 답

**출력**

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

**왜 그런가**

```text
MySQL 의 기본 collation 이름을 읽으면 답이 나온다

  utf8mb4_0900_ai_ci
                ^^ ^^
                |  +-- ci = case insensitive   -> 'abc' = 'ABC'  참
                +----- ai = accent insensitive -> 'e'   = 'é'    참

  Pad_attribute = NO PAD            -> 'a' = 'a ' 은 거짓
```

PG 의 `en_US.utf8` 은 **결정적**(`collisdeterministic = t`)이라 바이트가 다르면 다른 값이다.

```text
                       PG        MySQL     갈리나
'abc' = 'ABC'          거짓      참        ★ 갈린다
'e'   = 'é'            거짓      참        ★ 갈린다
'a'   = 'a '           거짓      거짓      같다 (둘 다 NO PAD 계열)
```

**셋째가 같은 것이 중요하다.** 「MySQL 은 느슨하다」로 외우면 여기서 틀린다.\
0900 계열은 뒤 공백을 **무시하지 않는다.** 무시하는 collation 도 같은 서버에 있다(5번).

---

### 2. ★ 정렬 — **네 가지 순서, 그중 둘만 같다**

**출력 (a) — 기본**

```text
(A) PostgreSQL 18.6 (en_US.utf8)        (B) MySQL 8.4.10 (utf8mb4_0900_ai_ci)
SELECT v FROM (VALUES ('apple'),        SELECT v FROM ( ... 같은 여섯 값 ... ) t
  ('Banana'),('apricot'),('BANANA'),      ORDER BY v;
  ('_x'),('Zebra')) t(v) ORDER BY v;
--- 실제 출력 ---                       --- 실제 출력 ---
    v                                   +---------+
---------                               | v       |
 apple                                  +---------+
 apricot                                | _x      |
 Banana                                 | apple   |
 BANANA                                 | apricot |
 _x                                     | Banana  |
 Zebra                                  | BANANA  |
(6 rows)                                | Zebra   |
                                        +---------+
```

**출력 (b) — 바이트 순서**

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

**왜 그런가**

```text
PG 기본(en_US.utf8) 에서 '_x' 가 BANANA 와 Zebra 사이에 있다

  apple  apricot  Banana  BANANA  _x  Zebra
                                  ^^
                            _ 를 1차 비교에서 무시하므로
                            사실상 'x' 로 취급된다 -> b 와 z 사이

MySQL 기본에서는 '_' 에 자기 무게가 있어 맨 앞이다
```

**바이트 순서에서는 두 엔진이 한 줄도 안 갈렸다.**

```text
ASCII 코드값
  'B'(66) 'Z'(90)  <  '_'(95)  <  'a'(97)
     대문자             밑줄          소문자
       ↓                 ↓             ↓
  BANANA Banana Zebra   _x      apple apricot
```

**네 순서를 한자리에 놓으면**

```text
PG 기본        apple  apricot  Banana  BANANA  _x     Zebra
MySQL 기본     _x     apple    apricot Banana  BANANA Zebra
PG COLLATE C   BANANA Banana   Zebra   _x      apple  apricot
MySQL bin      BANANA Banana   Zebra   _x      apple  apricot
```

**「사람이 보기 좋은 순서」는 서로 다르고, 「바이트 순서」는 하나다.**

**어디서 물리나** — 키셋 페이지네이션([목록의 **09번 주제**](../09-limit-offset-keyset-pagination/))은 **정렬이 안정적이어야** 성립한다.\
`WHERE (name, id) > ('Banana', 7) ORDER BY name, id` 같은 조건은\
정렬 규칙이 바뀌면 **다른 행을 가리킨다.** 서버 이전·OS 업그레이드에서 실제로 일어난다(10번).

---

### 3. ★ 같은 DDL, 다른 결과 — **`UNIQUE` 의 의미가 갈린다**

**출력**

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

**왜 그런가**

```text
UNIQUE 제약은 "같은 값이 둘 있으면 안 된다" 이다
        ↓
"같다" 의 정의가 collation 이다
        ↓
PG   : 'abc' != 'ABC'  ->  다른 값 -> 둘 다 들어간다
MySQL: 'abc' == 'ABC'  ->  같은 값 -> 두 번째가 거부된다
```

**이것이 이 주제에서 가장 비싼 차이다.**

```text
MySQL -> PG 이전              PG -> MySQL 이전
'Admin' 과 'admin' 이           기존 데이터에 'Admin'/'admin' 이 있으면
둘 다 가입 가능해진다            적재가 ERROR 1062 로 멈춘다
       ↓                              ↓
조용하다. 보안 사고가 된다       시끄럽다. 하지만 데이터를 먼저 정리해야 한다
```

**「아이디는 대소문자를 구분하지 않는다」가 요구사항이면 그것을 스키마에 적어야 한다**(11번).\
적지 않으면 **엔진 기본값이 대신 정하고**, 이전할 때 드러난다.

---

### 4. PG 에서 대소문자를 무시하려면 — **결정적이기를 포기한다**

**출력**

```text
--- PG 18.6 ---
SELECT 'abc' = 'ABC' COLLATE "C" AS c_cmp;
 c_cmp 
-------
 f
(1 row)

CREATE COLLATION nd_ci (provider = icu, locale = 'und-u-ks-level2', deterministic = false);
CREATE COLLATION
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

**왜 그런가**

```text
ICU 의 강도(strength) 레벨

level1 (primary)    글자 자체만 본다      -> 악센트·대소문자 둘 다 무시   = MySQL 의 ai_ci
level2 (secondary)  악센트까지 본다       -> 대소문자만 무시              = MySQL 의 as_ci
level3 (tertiary)   대소문자까지 본다     -> 기본. 아무것도 무시 안 한다  = MySQL 의 as_cs
```

`nd_ci`(level2)가 **대소문자는 같다 하고 악센트는 다르다** 한 것이 그 증거다.

**`deterministic = false` 가 왜 필요한가**

```text
"'abc' 와 'ABC' 는 같다" 고 선언하면
        ↓
같은 키에 서로 다른 바이트열이 들어간다
        ↓
"이 키의 값은 정확히 무엇인가" 에 답이 하나가 아니다
        ↓
PG 는 그 성질을 "결정성" 이라 부르고, 포기한다고 명시하게 한다
```

**UNIQUE 도 MySQL 처럼 된다.**

```text
--- PG 18.6 ---
BEGIN;
CREATE TEMP TABLE t39 (v text COLLATE nd_ci UNIQUE);
INSERT INTO t39 VALUES ('abc');
INSERT 0 1
INSERT INTO t39 VALUES ('ABC');
ERROR:  duplicate key value violates unique constraint "t39_v_key"
DETAIL:  Key (v)=(ABC) already exists.
ROLLBACK;
```

`DETAIL` 이 `Key (v)=(ABC) already exists` 라고 한다 — **`'abc'` 를 이미 있는 것으로 본 것**이다.

`LIKE` 도 이 collation 을 따른다.

```text
--- PG 18.6 ---
SELECT 'abc' LIKE 'ABC' COLLATE nd_ci AS like_nd;
 like_nd 
---------
 t
(1 row)
```

**안 되는 것을 단정하기 전에 던져 본 결과다.** 이 서버·이 collation 에서는 돌았다.

---

### 5. 뒤 공백 — **`Pad_attribute` 가 정한다**

**출력**

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

**왜 그런가 — 0번의 `SHOW COLLATION` 출력과 맞춰 읽는다**

```text
| utf8mb4_general_ci | ... | PAD SPACE |   ->  비교 전에 뒤 공백을 떼고 본다  ->  'a' = 'a ' 참
| utf8mb4_0900_ai_ci | ... | NO PAD    |   ->  공백도 글자다                ->  'a' = 'a ' 거짓
```

**같은 서버, 같은 문장, 같은 데이터인데 collation 하나로 뒤집혔다.**

**1번의 `trailing_space` 를 다시 읽으면** — 두 엔진 다 거짓이었던 것은\
「MySQL 이 공백을 구분한다」는 성질이 아니라 **기본 collation 이 `NO PAD` 라서**다.\
`utf8mb4_general_ci` 를 기본으로 쓰는 서버(오래된 스키마에 흔하다)에서는 **참이 된다.**

PG 쪽은 `text`/`varchar` 에서 구분한다.

```text
--- PG 18.6 ---
SELECT 'a' = 'a ' AS trailing_space;
 trailing_space 
----------------
 f
(1 row)
```

**단 `char(n)` 은 다르다.** 37번에서 본 대로 `char` 는 공백으로 채워지고 비교에서 그 공백이 무시된다.\
「공백이 의미 있나」는 **타입과 collation 둘 다** 보고 판단한다.

---

### 6. 섞으면 — **양쪽 다 거부한다**

**출력**

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

**왜 그런가**

```text
비교하려면 규칙이 하나여야 한다
  왼쪽은 "바이트로 비교하라"
  오른쪽은 "en_US 규칙으로 비교하라"
        ↓
둘 다 명시적이라 우선순위를 못 정한다 -> 거부한다
```

**임의로 한쪽을 고르지 않는 것이 옳다.** 골랐다면 어느 쪽인지 아무도 모르는 채 답이 달라졌을 것이다.

**MySQL 의 `EXPLICIT` 이라는 말이 힌트다.** collation 에는 우선순위(coercibility)가 있어서,\
한쪽만 명시적이면 그쪽이 이긴다. **둘 다 명시적일 때만** 이 에러가 난다.

**어디서 물리나** — 서로 다른 collation 의 **열을 조인할 때**다.

```text
users.login  varchar COLLATE utf8mb4_0900_ai_ci
logs.login   varchar COLLATE utf8mb4_bin        <- 나중에 만든 표가 다르게 선언됐다
        ↓
JOIN ... ON users.login = logs.login   ->  ERROR 1267
```

**스키마가 커진 뒤에 드러나므로 고치기 비싸다.** 열 정의를 처음부터 맞춘다.

---

### 7. ★ `COLLATE` 의 대가 — **인덱스를 잃는다**

**출력 — PG**

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

**출력 — MySQL**

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

**왜 그런가**

```text
인덱스는 "어떤 순서로 정렬해 저장했나" 이다

  t39_code_idx 는 en_US.utf8 (PG) / utf8mb4_0900_ai_ci (MySQL) 순서다
        ↓
  질의가 "C 순서로" / "bin 순서로" 비교하라고 한다
        ↓
  다른 순서의 자료다 -> 그 정렬을 쓸 수 없다
```

**PG 는 완전히 버렸고**(`Index Scan` → `Seq Scan`),\
**MySQL 은 `ref` 를 버리고 `range` 로 내려갔다**(경고 1739 가 `ref` 만 언급한다).\
이 표·이 통계에서는 `rows` 가 1 그대로였지만, **접근 방식이 바뀐 것은 계획에 그대로 적혀 있다.**

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

**설명이 반증 가능했고, 반증되지 않았다.** 「순서가 맞는 인덱스를 주면 탄다」가 확인됐다.

**같은 경고 1739 를 35번에서는 타입 변환으로 봤다.** 원인이 둘(타입·collation)이고 **결과는 하나**다 —\
열이 원래 모습대로 비교되지 않으면 인덱스를 잃는다.

---

### 8. 이름 읽는 법 — `utf8mb4_0900_as_ci`

```text
utf8mb4  _  0900  _  as  _  ci
   ^         ^       ^      ^
   |         |       |      +-- case insensitive  : 대소문자를 무시한다
   |         |       +--------- accent sensitive  : 악센트는 구분한다
   |         +----------------- Unicode CLDR 판본 번호
   +--------------------------- 문자셋(인코딩)
```

**답** — **악센트는 구분하고 대소문자는 무시한다.**

```text
'abc' = 'ABC'   ->  참   (ci)
'e'   = 'é'     ->  거짓 (as)
```

**세 이름을 나란히 놓으면 축이 둘임이 보인다.**

| 이름 | 악센트 | 대소문자 | PG 대응(ICU 강도) |
|---|---|---|---|
| `utf8mb4_0900_ai_ci` | 무시 | 무시 | level1 |
| `utf8mb4_0900_as_ci` | 구분 | 무시 | level2 |
| `utf8mb4_0900_as_cs` | 구분 | 구분 | level3(기본) |
| `utf8mb4_bin` | 구분 | 구분 | `C`(바이트 그대로) |

**`as_cs` 와 `bin` 이 「둘 다 구분」인데 다른 이유**는 **정렬 순서**다.\
`as_cs` 는 언어 규칙대로 줄 세우고, `bin` 은 바이트값대로 줄 세운다 — 2번의 (a)와 (b)의 차이다.

**「둘 다 `ci` 니까 같겠지」도 틀린다.** `utf8mb4_general_ci` 와 `utf8mb4_0900_ai_ci` 는\
둘 다 `ci` 지만 **`Pad_attribute` 가 다르고**(5번) **정렬 규칙 판본도 다르다.**

---

### 9. `\dO` 가 0행인 것 — **「없다」가 아니다**

**출력을 다시 본다.**

```text
--- PG 18.6 ---
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
```

**답** — **아니다.** `\dO` 는 **사용자 스키마의 collation 만** 보여 준다.\
시스템 스키마(`pg_catalog`)의 것은 `pg_collation` 에 **880개** 들어 있다.

```text
\dO 가 0행이다
        ↓
(틀린 읽기)  이 서버에는 collation 이 없다
(맞는 읽기)  내가 CREATE COLLATION 으로 만든 것이 아직 없다
```

**실제로 4번에서 collation 둘을 만든 뒤 다시 찍으면 나타난다.**

```text
--- PG 18.6 ---
\dO
                                     List of collations
 Schema | Name  | Provider | Collate | Ctype |     Locale      | ICU Rules | Deterministic? 
--------+-------+----------+---------+-------+-----------------+-----------+----------------
 public | nd_ai | icu      |         |       | und-u-ks-level1 |           | no
 public | nd_ci | icu      |         |       | und-u-ks-level2 |           | no
(2 rows)
```

`Deterministic?` 칸이 **`no`** 인 것을 보라 — 4번에서 `deterministic = false` 로 만든 그것이다.

**왜 이 구분이 중요한가** — 환경 보고가 틀리면 **그 위의 모든 결론이 틀린다.**\
「collation 이 없어서 기본값으로 돈다」는 보고는 사실이 아니고,\
「880개 중 `en_US.utf8` 이 이 DB 의 기본으로 쓰인다」가 사실이다.

MySQL 쪽 대응물은 `SHOW COLLATION` 과 `information_schema.COLLATIONS` 다 — 이쪽은 **286개를 다 보여 준다.**

---

### 10. 정렬이 불안정한 이유

**세 층에서 바뀔 수 있다.**

```text
(1) 질의가 바꾼다         ORDER BY v COLLATE "C"      <- 내가 적었으니 보인다
(2) 스키마가 바꾼다       열·DB 의 collation 설정      <- 이전할 때 안 맞을 수 있다
(3) ★ 운영체제가 바꾼다   PG 의 libc 제공자            <- 아무도 안 적었는데 바뀐다
```

**(3)이 조용하다.** 0번의 출력을 다시 본다.

```text
 datname | datcollate |  datctype  | datlocprovider 
---------+------------+------------+----------------
 study   | en_US.utf8 | en_US.utf8 | c
                                      ^
                          c = libc = 운영체제의 로케일 라이브러리
```

**PG 자신이 정렬 규칙을 갖고 있는 게 아니라 OS 에서 빌려 쓴다.**\
그래서 같은 PG 버전이라도 **OS 나 glibc 판이 다르면 정렬이 달라질 수 있다.**\
이 문서의 2번 결과는 **이 컨테이너 이미지**(`postgres:18`, Debian)에서 나온 것이다.

**무엇이 깨지나**

```text
정렬이 바뀌면
  -> 그 순서로 만든 인덱스가 실제 순서와 안 맞는다
  -> 범위 조건이 행을 빠뜨릴 수 있다
  -> 키셋 페이지네이션이 어긋난다 ([목록의 **09번 주제**](../09-limit-offset-keyset-pagination/))
  -> UNIQUE 인덱스가 중복을 못 잡을 수 있다
```

**처방 둘.**

1. **정렬이 중요한 열에는 ICU 제공자를 쓴다.** ICU 는 PG 와 함께 판본이 관리되므로 OS 에 덜 묶인다.
2. **식별자 열에는 `C`/`bin` 을 쓴다.** 바이트 순서는 **어디서도 안 바뀐다** — 2번에서 두 엔진이 같았던 그 순서다.

---

### 11. 요구사항을 어디에 적나 — **질의가 아니라 스키마에**

**「아이디는 대소문자를 구분하지 않는다」**

```sql
-- MySQL: 기본이 이미 그렇다. 그래도 명시한다
CREATE TABLE users (
  login varchar(64) COLLATE utf8mb4_0900_ai_ci NOT NULL UNIQUE
);

-- PG: 비결정적 collation 을 만들고 열에 붙인다
CREATE COLLATION login_ci (provider = icu, locale = 'und-u-ks-level2', deterministic = false);
CREATE TABLE users (
  login text COLLATE login_ci NOT NULL UNIQUE
);
```

**왜 열에 붙이나**

| 어디에 | 비교가 맞나 | 인덱스가 사나 | UNIQUE 가 맞나 |
|---|---|---|---|
| 질의에 `COLLATE` | ✅ | **✗**(7번) | **✗** — 제약은 열 정의를 따른다 |
| `WHERE UPPER(login) = ...` | ✅ | **✗** | **✗** |
| **열 정의에 `COLLATE`** | ✅ | ✅ | ✅ |

**질의에 적으면 `UNIQUE` 가 안 고쳐진다.** 3번의 사고가 그대로 남는다 —\
조회는 대소문자를 무시하는데 **가입은 `'Admin'` 과 `'admin'` 을 둘 다 받는다.**

**명시하는 것 자체가 중요하다.** MySQL 은 기본값이 이미 `ai_ci` 라 안 적어도 되지만,\
안 적으면 **요구사항인지 우연인지 코드에서 구분이 안 된다.** 다음 사람이 서버를 옮길 때 사라진다.

**같이 정할 것 셋.**

1. **악센트도 무시할 것인가.** `ai` 와 `as` 는 다른 결정이다(8번). 「대소문자 무시」만 들었다면 `as_ci`/level2 가 맞다.
2. **뒤 공백을 어떻게 볼 것인가**(5번). 입력 단계에서 `TRIM` 하는 편이 대개 낫다.
3. **조인 상대 열의 collation 을 맞췄나**(6번). 안 맞으면 나중에 `ERROR 1267` 이다.

**반대 요구(「구분한다」)도 똑같이 적는다.**

```sql
-- MySQL: 기본이 무시이므로 반드시 적어야 한다
CREATE TABLE tokens (v varchar(64) COLLATE utf8mb4_bin NOT NULL UNIQUE);
-- PG: 기본이 구분이지만 바이트 순서를 원하면 적는다
CREATE TABLE tokens (v text COLLATE "C" NOT NULL UNIQUE);
```

토큰·해시·코드처럼 **바이트가 곧 값**인 열은 `bin`/`C` 가 맞다.

**덤이 하나 있다 — 38번의 PG 접두사 인덱스 문제가 사라진다.**

```text
--- PG 18.6 ---
CREATE TABLE t39c (id int PRIMARY KEY, code varchar(20) COLLATE "C" NOT NULL);
-- 20,000행 적재 후 code 에 평범한 인덱스 하나
CREATE INDEX t39c_code_idx ON t39c (code);
ANALYZE t39c;
EXPLAIN (COSTS OFF) SELECT * FROM t39c WHERE code LIKE 'C00012%';
                                      QUERY PLAN                                      
--------------------------------------------------------------------------------------
 Index Scan using t39c_code_idx on t39c
   Index Cond: (((code)::text >= 'C00012'::text) AND ((code)::text < 'C00013'::text))
   Filter: ((code)::text ~~ 'C00012%'::text)
(3 rows)
```

38번에서는 `varchar_pattern_ops` 인덱스를 따로 만들어야 했다. 여기서는 **평범한 인덱스로 탔고**,\
`Index Cond` 도 `~>=~` 가 아니라 **평범한 `>=`·`<`** 다 — 열 자체가 이미 바이트 순서이기 때문이다.\
(이 표도 실험 후 지웠다.)

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 환경 조회 (0번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | `pg_database`·`\dO`·`pg_collation` / `SHOW COLLATION`·시스템 변수 |
| `collation_connection` 대조 (0번) | MySQL 8.4.10 | 2회 | **기본 접속과 `utf8mb4` 접속을 둘 다 찍었다** |
| `=` 비교 3식 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | |
| `ORDER BY` 기본 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 여섯 값 |
| `ORDER BY` 바이트 순서 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 동일** |
| `UNIQUE` + `'abc'`/`'ABC'` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 트랜잭션 롤백 · **`ERROR 1062` 가 근거다** |
| `CREATE COLLATION` + 비교 (4번) | PG 18.6 | 4회 | level1·level2 각각 |
| 비결정적 collation + `UNIQUE` (4번) | PG 18.6 | 1회 | **`DETAIL: Key (v)=(ABC)` 가 근거다** |
| 비결정적 collation + `LIKE` (4번) | PG 18.6 | 1회 | **안 될 것으로 단정하지 않고 던져 봤다** |
| `PAD SPACE` 대 `NO PAD` (5번) | MySQL 8.4.10 | 1회 | 한 문에서 둘 다 |
| collation 섞기 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **양쪽 에러가 근거다** |
| `EXPLAIN` 4종 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 20,000행 `t39`, `ANALYZE` 직후 |
| 경고 1739 (7번) | MySQL 8.4.10 | 1회 | `SHOW WARNINGS` |
| collation 전용 인덱스 (7번) | PG 18.6 | 1회 | **인덱스 추가 전후를 둘 다 실었다** |
| `COLLATE utf8mb4_...` 를 PG 에 (6·8번) | PG 18.6 | 1회 | **이름 없음 에러가 근거다** |
| `\dO` 재조회 (9번) | PG 18.6 | 2회 | **collation 생성 전후를 둘 다 실었다** |
| `C` collation 열의 접두사 `LIKE` (11번) | PG 18.6 | 1회 | 38번의 반대 사례 — 표는 **실험 후 삭제** |

**★ 설정 의존 항목 — 1·2·3·5·7번, 즉 이 주제의 거의 전부.**\
머리말과 0번에 적은 환경에서 나온 결과다. **다른 설정의 서버에서는 같은 질의가 다른 답을 낸다.**\
그래서 0번을 첫 문항으로 두었다 — 환경을 안 찍고 collation 을 말하면 그 진술은 검증 불가능하다.

**운영체제 의존 항목** — 2번의 PG 정렬. `datlocprovider = c`(libc)라 **OS 의 로케일 라이브러리**를 쓴다.\
이 결과는 `postgres:18`(Debian) 이미지에서 나온 것이고, 다른 OS·glibc 판에서는 달라질 수 있다(10번).

**옵티마이저 의존 항목** — 7번의 `EXPLAIN` 출력. 계획은 관찰이지 보장이 아니다.\
MySQL 이 `ref` 를 포기하고도 `range` 를 쓴 것은 이 표·이 통계에서의 판단이다.

**언어 보장 항목** — 4번(`deterministic` 옵션의 의미)·6번(섞이면 에러)·8번(이름 규칙).\
두 매뉴얼의 collation 페이지가 정한 것이다.

**버전을 적지 않은 이유** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 **두 매뉴얼에서도 릴리스 노트에서도 찾지 못했다.**\
`utf8mb4_0900_*` 이름의 `0900` 은 **Unicode CLDR 판본 번호**이지 MySQL 버전이 아니다 — 혼동하기 쉬워 적어 둔다.

**DB 잔재** — 없다. `t39`(와 인덱스 둘)·`t39c` 는 삭제했고, PG 에 만든 collation `nd_ci`·`nd_ai` 도 삭제했다.\
`emp`·`dept` 는 읽기만 했다.
