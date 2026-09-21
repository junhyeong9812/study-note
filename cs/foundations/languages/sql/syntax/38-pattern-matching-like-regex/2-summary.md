# sql/38-패턴 매칭 (LIKE·ESCAPE·정규식) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Pattern Matching](https://www.postgresql.org/docs/18/functions-matching.html) · [PostgreSQL 18 · Operator Classes](https://www.postgresql.org/docs/18/indexes-opclass.html) · [MySQL 8.4 · String Comparison Functions](https://dev.mysql.com/doc/refman/8.4/en/string-comparison-functions.html) · [MySQL 8.4 · Regular Expressions](https://dev.mysql.com/doc/refman/8.4/en/regexp.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·계획은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **환경 조건** — PG 데이터베이스 collate 는 **`en_US.utf8`**(libc 제공자) · MySQL 기본 collation 은 **`utf8mb4_0900_ai_ci`**.\
> ★ **이 설정이 이 주제의 절반을 정한다** — 대소문자 판정도, `LIKE` 가 인덱스를 타는지도 여기서 갈린다(아래 4·5번).\
> **버전** — 도입 버전이 확인된 것은 없어 **버전을 적지 않는다.**\
> **선행** — [37 문자열 함수와 연결 연산](../37-string-functions-and-concatenation/) · 짝이 되는 주제는 [39 collation](../39-collation/)

## 한눈에 — 쉽게 말하면

**`LIKE` = 「이런 모양이면 다 잡아라」.** 모양을 적는 기호가 둘뿐이다.

```text
%  ->  아무 글자 0개 이상
_  ->  아무 글자 정확히 1개

'abc' LIKE 'a%'   ->  참   (a 로 시작하면 뒤는 아무거나)
'abc' LIKE '_b_'  ->  참   (세 글자이고 가운데가 b)
'abc' LIKE 'a_'   ->  거짓 (두 글자여야 한다)
```

**그런데 이 두 기호가 데이터에 들어 있으면?**

```text
'100%' 라는 값을 찾고 싶다.  LIKE '100%' 라고 쓰면

'100%'  ->  잡힌다  (원하는 것)
'1000'  ->  잡힌다  (★ 원하지 않는 것 — % 가 와일드카드로 읽혔다)
```

그래서 **「이 `%` 는 글자다」**라고 표시하는 장치가 `ESCAPE` 다.

| 비유 | 실체 |
|---|---|
| 「김씨 성을 가진 사람 전부」 | `LIKE '김%'` |
| 「가운데 글자만 모르는 세 글자 이름」 | `LIKE '김_수'` |
| 「이 별표는 진짜 별표다」라고 표시 | `ESCAPE` |
| 앞 글자를 아는 이름은 명부를 뒤지기 쉽다 | 앞이 고정된 `LIKE 'abc%'` — 인덱스를 쓸 수 있다 |
| 「끝이 -수인 사람」은 명부를 전부 읽어야 한다 | `LIKE '%수'` — **인덱스를 못 쓴다** |

> **와일드카드(wildcard)** — 「아무 글자」를 뜻하는 기호.\
> 예: `LIKE 'a%'` 의 `%` 는 뒤에 무엇이 와도 좋다는 뜻이다.

그리고 **`LIKE` 는 엔진마다 다른 답을 낸다.** 함수가 달라서가 아니라 **비교 규칙(collation)이 달라서**다.

```text
'abc' LIKE 'A%'

PG (en_US.utf8, 결정적)       MySQL (utf8mb4_0900_ai_ci)
      거짓                           참
        ↑                             ↑
  대소문자가 다르면 다르다       ci = case insensitive
```

## 이 주제가 답하려는 질문

1. **`%` 와 `_` 를 글자로 찾으려면 어떻게 쓰나?**
2. **같은 `LIKE` 가 왜 두 엔진에서 다른 답을 내나?**
3. **어떤 패턴이 인덱스를 타고 어떤 패턴이 못 타나?**

## 예시 데이터 — 이 묶음이 공유하는 것

패턴 판정은 리터럴로 한다. 인덱스 실험만 별도 표 `t38` 을 쓰고, **두 엔진에 같은 모양으로 만들었다가 지웠다.**

```sql
CREATE TABLE t38 (id int PRIMARY KEY, code varchar(20) NOT NULL);  -- code 에 인덱스
-- 20,000 행: (1,'C000001') (2,'C000002') ... (20000,'C020000')
```

`emp`·`dept` 는 읽기만 하고 바꾸지 않는다.

## 동작 방식

### 1. `%` 와 `_` — 두 기호가 전부다

**언제 쓰나** — 부분 일치 검색. `LIKE` 문법의 90% 가 이 두 기호다.

```text
(패턴) 'a%'                (패턴) '_b_'               (패턴) '%'
 a 로 시작                  세 글자, 가운데가 b        아무거나 (빈 문자열 포함)
   ↓                           ↓                          ↓
'abc'  -> 참               'abc'  -> 참              'abc' -> 참
'bac'  -> 거짓             'ab'   -> 거짓            ''    -> 참
```

```text
### SQL: SELECT 'abc' LIKE 'a%' AS a, 'abc' LIKE '_b_' AS b, 'abc' LIKE '%' AS c, 'abc' LIKE 'A%' AS d;
--- PG 18.6 ---
 a | b | c | d 
---+---+---+---
 t | t | t | f
(1 row)

--- MySQL 8.4.10 ---
+---+---+---+---+
| a | b | c | d |
+---+---+---+---+
| 1 | 1 | 1 | 1 |
+---+---+---+---+
```

그림 해설 — **앞의 셋은 같고 `d` 만 갈렸다.** `'abc' LIKE 'A%'` 가 PG 에서 거짓, MySQL 에서 참이다.\
대가 — 이 한 칸이 **검색 결과의 개수를 바꾼다.** 대소문자를 섞어 쓰는 코드값에서 바로 물린다.\
왜 갈리는지는 4번, 그리고 정본은 [39 collation](../39-collation/)이다.

`NULL` 은 어느 쪽에도 안 걸린다.

```text
### SQL: SELECT NULL LIKE 'a%' AS a, 'abc' LIKE NULL AS b;
--- PG 18.6 ---
 a | b 
---+---
   | 
(1 row)

--- MySQL 8.4.10 ---
+------+------+
| a    | b    |
+------+------+
| NULL | NULL |
+------+------+
```

그림 해설 — 결과가 `FALSE` 가 아니라 **`NULL`** 이다. `WHERE` 는 `NULL` 행을 버리므로 **결과는 같아 보인다.**\
그런데 `NOT LIKE` 로 뒤집어도 여전히 `NULL` 이라 **여전히 버려진다.** [04 NULL 의 3값 논리](../04-null-three-valued-logic/)가 정본이다.

### 2. ★ `%` 를 글자로 찾기 — `ESCAPE`

**언제 쓰나** — 검색어를 사용자가 입력할 때. **`%` 를 입력하면 전부 잡힌다.**

```text
(전) 찾고 싶은 값: '100%' 라는 문자열 그 자체

LIKE '100%' 라고 쓰면
   '100%'  -> 잡힌다
   '1000'  -> 잡힌다   ★ % 가 "아무 글자" 로 읽혔다
```

```text
### SQL: SELECT '100%' LIKE '100%' AS a, '1000' LIKE '100%' AS b;
--- PG 18.6 ---
 a | b 
---+---
 t | t
(1 row)

--- MySQL 8.4.10 ---
+---+---+
| a | b |
+---+---+
| 1 | 1 |
+---+---+
```

`ESCAPE` 로 「다음 한 글자는 글자다」를 표시한다.

```text
LIKE '100!%' ESCAPE '!'
          ^^
          !  다음의 % 는 와일드카드가 아니라 글자다
```

```text
### SQL: SELECT '100%' LIKE '100!%' ESCAPE '!' AS a, '1000' LIKE '100!%' ESCAPE '!' AS b;
--- PG 18.6 ---
 a | b 
---+---
 t | f
(1 row)

--- MySQL 8.4.10 ---
+---+---+
| a | b |
+---+---+
| 1 | 0 |
+---+---+
```

그림 해설 — **`'1000'` 이 이제 안 잡힌다.** 이것이 `ESCAPE` 가 한 일의 전부다.\
**두 엔진의 답이 같다** — `ESCAPE` 절 자체는 방언이 아니다.

`ESCAPE` 를 안 써도 **역슬래시가 기본 이스케이프**다. 양쪽 다 그렇다.

```text
### SQL: SELECT '100%' LIKE '100\%' AS a;
--- PG 18.6 ---
 a 
---
 t
(1 row)

--- MySQL 8.4.10 ---
+---+
| a |
+---+
| 1 |
+---+
```

`_` 도 같다.

```text
### SQL: SELECT 'a_b' LIKE 'a\_b' AS esc_underscore, 'axb' LIKE 'a\_b' AS should_be_false;
--- PG 18.6 ---
 esc_underscore | should_be_false 
----------------+-----------------
 t              | f
(1 row)

--- MySQL 8.4.10 ---
+----------------+-----------------+
| esc_underscore | should_be_false |
+----------------+-----------------+
|              1 |               0 |
+----------------+-----------------+
```

```text
### SQL: SELECT 'a_b' LIKE 'a#_b' ESCAPE '#' AS a, 'axb' LIKE 'a#_b' ESCAPE '#' AS b;
--- PG 18.6 ---
 a | b 
---+---
 t | f
(1 row)

--- MySQL 8.4.10 ---
+---+---+
| a | b |
+---+---+
| 1 | 0 |
+---+---+
```

대가 — **역슬래시에 기대면 문자열 리터럴 규칙과 얽힌다.** 애플리케이션 드라이버, 쉘, 파일 등을 지나며\
역슬래시가 몇 개가 될지 추적하기 어렵다. **`ESCAPE '!'` 처럼 안 쓰는 문자를 지정하는 편**이 안전하다.

> **`ESCAPE`** — `LIKE` 패턴에서 「다음 한 글자는 와일드카드가 아니다」를 표시할 문자를 정하는 절.\
> 예: `LIKE '100!%' ESCAPE '!'` 는 `'100%'` 만 잡고 `'1000'` 은 안 잡는다.

### 3. 정규식 — **연산자 이름이 서로 없다**

**언제 쓰나** — `%`·`_` 로 표현이 안 되는 모양을 찾을 때.

```text
PostgreSQL                          MySQL
 ~   정규식 일치 (대소문자 구분)      REGEXP  /  RLIKE
 ~*  정규식 일치 (대소문자 무시)      (대응 연산자 없음 — collation 이 정한다)
```

서로를 정확히 거부한다.

```text
### SQL: SELECT 'abc' ~ '^a' AS a, 'abc' ~* '^A' AS b;
--- PG 18.6 ---
 a | b 
---+---
 t | t
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near '~ '^a' AS a, 'abc' ~* '^A' AS b' at line 1
```

```text
### SQL: SELECT 'abc' REGEXP '^a' AS a, 'abc' RLIKE '^A' AS b;
--- PG 18.6 ---
ERROR:  syntax error at or near "'^a'"
LINE 1: SELECT 'abc' REGEXP '^a' AS a, 'abc' RLIKE '^A' AS b;
                            ^
--- MySQL 8.4.10 ---
+---+---+
| a | b |
+---+---+
| 1 | 1 |
+---+---+
```

그림 해설 — **둘 다 구문 오류다.** 이식하면 배포 전에 터지므로 **조용하지 않다.**

★ **그런데 이름이 같은 함수가 있고, 그게 답이 다르다.**

```text
### SQL: SELECT REGEXP_LIKE('abc','^A') AS a, REGEXP_REPLACE('abc-123','[0-9]+','N') AS b;
--- PG 18.6 ---
 a |   b   
---+-------
 f | abc-N
(1 row)

--- MySQL 8.4.10 ---
+---+-------+
| a | b     |
+---+-------+
| 1 | abc-N |
+---+-------+
```

```text
REGEXP_LIKE('abc', '^A')
  PG    -> f    ^A 는 대문자 A 로 시작하라는 뜻. 'abc' 는 소문자다
  MySQL -> 1    기본 collation 이 대소문자를 무시하므로 'a' 가 'A' 와 같다
```

**문법도 함수 이름도 같은데 답이 다르다.** 3번에서 가장 조용한 자리다.\
`REGEXP_REPLACE` 는 같은 답을 냈다 — **치환 자체는 갈리지 않는다.**

대가 — 정규식은 **엔진마다 방언이 더 있다**(look-ahead 지원 여부 등). 여기서는 두 엔진에서 확인한 것만 적는다.

### 4. ★ 대소문자 — `ILIKE` 와 collation

**언제 쓰나** — 「대소문자 무시하고 찾아라」를 구현할 때.

PG 는 **전용 연산자**를 준다.

```text
### SQL: SELECT 'abc' ILIKE 'A%' AS r;
--- PG 18.6 ---
 r 
---
 t
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near ''A%' AS r' at line 1
```

MySQL 에는 `ILIKE` 가 없다 — **필요가 없기 때문**이다. 기본 collation 이 이미 무시한다.

```text
(A) PostgreSQL 18.6                     (B) MySQL 8.4.10
    DB collate = en_US.utf8 (결정적)        기본 collation = utf8mb4_0900_ai_ci

SELECT 'abc' LIKE 'A%';                 SELECT 'abc' LIKE 'A%';
--- 실제 출력 ---                       --- 실제 출력 ---
 ?column?                               +----------+
----------                              | ...      |
 f                                      +----------+
(1 row)                                 |        1 |
                                        +----------+
SELECT 'abc' ILIKE 'A%';                (ILIKE 는 없다. COLLATE 로 바꾼다)
 ?column?                               SELECT 'abc' LIKE 'A%'
----------                                COLLATE utf8mb4_0900_as_cs;
 t                                      +------+
(1 row)                                 | r    |
                                        +------+
                                        |    0 |
                                        +------+
   -> 대소문자 구분이 기본.                -> 대소문자 무시가 기본.
      무시하려면 ILIKE                        구분하려면 COLLATE 로 바꾼다
```

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

두 그림의 결론 — **기본값이 정반대라, 「추가로 무엇을 써야 하나」도 정반대다.**\
PG 는 무시하려고 쓰고, MySQL 은 구분하려고 쓴다.

대가 — 「대소문자 무시 검색」을 PG 습관대로 `ILIKE`·`UPPER()` 로 구현하면\
MySQL 에서는 **불필요하고** 게다가 **인덱스를 잃는다**(5번). collation 의 정본은 [39 collation](../39-collation/)이다.

### 5. ★ 인덱스 — 앞이 고정됐나

**언제 쓰나** — `LIKE` 가 느릴 때. 이 주제의 실무 값어치가 여기 있다.

```text
인덱스는 code 의 값 순서로 정렬돼 있다

  C000001
  C000002
  ...          LIKE 'C00012%'  -> "C00012 로 시작" = 정렬에서 연속 구간이다 -> 좁힐 수 있다
  C000123
  ...          LIKE '%00123'   -> 끝이 00123 인 것은 정렬 어디에나 있다     -> 좁힐 수 없다
  C020000
```

**MySQL 이 이 규칙을 교과서대로 보여 준다.**

```text
--- MySQL 8.4.10 ---
EXPLAIN SELECT * FROM t38 WHERE code LIKE 'C00012%';
+----+-------+-------+---------------+--------------+---------+------+------+--------------------------+
| id | table | type  | possible_keys | key          | key_len | ref  | rows | Extra                    |
+----+-------+-------+---------------+--------------+---------+------+------+--------------------------+
|  1 | t38   | range | t38_code_idx  | t38_code_idx | 82      | NULL |   10 | Using where; Using index |
+----+-------+-------+---------------+--------------+---------+------+------+--------------------------+

EXPLAIN SELECT * FROM t38 WHERE code LIKE '%00123';
+----+-------+-------+---------------+--------------+---------+------+-------+--------------------------+
| id | table | type  | possible_keys | key          | key_len | ref  | rows  | Extra                    |
+----+-------+-------+---------------+--------------+---------+------+-------+--------------------------+
|  1 | t38   | index | NULL          | t38_code_idx | 82      | NULL | 20418 | Using where; Using index |
+----+-------+-------+---------------+--------------+---------+------+-------+--------------------------+
```

(폭에 맞춰 `select_type`·`partitions`·`filtered` 칸을 뺀 것 말고는 서버가 낸 그대로다.)

그림 해설 — 두 줄을 나란히 읽으면 셋이 바뀌었다.

```text
                앞이 고정   앞이 열림
type            range       index      <- 구간 탐색 -> 전부 훑기
possible_keys   인덱스      NULL       <- 후보에서 아예 빠졌다
rows            10          20418      <- 전부 훑는다
```

★ **그런데 PG 는 앞이 고정된 패턴에서도 인덱스를 안 탔다.**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t38 WHERE code LIKE 'C00012%';
                 QUERY PLAN                  
---------------------------------------------
 Seq Scan on t38
   Filter: ((code)::text ~~ 'C00012%'::text)
(2 rows)
```

**이유는 collation 이다.** 이 데이터베이스의 collate 는 `en_US.utf8` 인데,\
그런 collation 에서는 **인덱스의 정렬 순서와 `LIKE` 의 접두사 비교가 같지 않다.**\
PG 는 「이 인덱스로는 `LIKE` 범위를 못 만든다」고 판단하고 버린다.

**전용 연산자 클래스로 인덱스를 하나 더 만들면 탄다.**

```text
--- PG 18.6 ---
CREATE INDEX t38_code_pat_idx ON t38 (code varchar_pattern_ops);
ANALYZE t38;
EXPLAIN (COSTS OFF) SELECT * FROM t38 WHERE code LIKE 'C00012%';
                                        QUERY PLAN                                        
------------------------------------------------------------------------------------------
 Index Scan using t38_code_pat_idx on t38
   Index Cond: (((code)::text ~>=~ 'C00012'::text) AND ((code)::text ~<~ 'C00013'::text))
   Filter: ((code)::text ~~ 'C00012%'::text)
(3 rows)
```

그림 해설 — `Index Cond` 에 **`>= 'C00012' AND < 'C00013'`** 이 생겼다.\
PG 가 `LIKE` 패턴을 **범위 조건 둘로 바꿔** 인덱스를 좁힌 것이다. `~>=~`·`~<~` 는 **바이트 순서 비교 연산자**다.\
대가 — 인덱스가 하나 더 필요하다. 저장 공간과 쓰기 비용이 는다.

**앞이 열린 패턴은 새 인덱스로도 못 탄다.**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t38 WHERE code LIKE '%00123';
                 QUERY PLAN                 
--------------------------------------------
 Seq Scan on t38
   Filter: ((code)::text ~~ '%00123'::text)
(2 rows)
```

**정규식도 마찬가지다.** 양쪽 다 전부 훑는다.

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t38 WHERE code ~ '^C00012';
                 QUERY PLAN                 
--------------------------------------------
 Seq Scan on t38
   Filter: ((code)::text ~ '^C00012'::text)
(2 rows)

--- MySQL 8.4.10 ---
EXPLAIN SELECT * FROM t38 WHERE code REGEXP '^C00012';
+----+-------+-------+---------------+--------------+---------+------+-------+--------------------------+
| id | table | type  | possible_keys | key          | key_len | ref  | rows  | Extra                    |
+----+-------+-------+---------------+--------------+---------+------+-------+--------------------------+
|  1 | t38   | index | NULL          | t38_code_idx | 82      | NULL | 20418 | Using where; Using index |
+----+-------+-------+---------------+--------------+---------+------+-------+--------------------------+
```

그림 해설 — `^C00012` 는 사람 눈에 접두사지만, **옵티마이저는 정규식을 그렇게 분해하지 않는다.**\
`possible_keys` 가 `NULL` 인 것이 그 증거다.\
대가 — **접두사 검색에 정규식을 쓰면 인덱스를 버린다.** 같은 뜻이면 `LIKE 'C00012%'` 로 쓴다.

> **연산자 클래스(operator class)** — PG 에서 인덱스가 값을 어떤 규칙으로 비교할지 정하는 것.\
> 예: `varchar_pattern_ops` 는 collation 을 무시하고 **바이트 순서**로 비교해, `LIKE` 접두사 검색에 쓸 수 있게 한다.

## 문법 — 형태와 규칙

```sql
-- LIKE (양쪽 공통)
expr LIKE pattern [ESCAPE 'c']
expr NOT LIKE pattern [ESCAPE 'c']
--   %  = 0글자 이상 아무거나
--   _  = 정확히 1글자

-- 대소문자 무시
expr ILIKE pattern                          -- PG 전용
expr LIKE pattern COLLATE <collation>       -- MySQL 쪽 방법 (39번)

-- 정규식
expr ~ pattern     expr ~* pattern          -- PG 전용
expr REGEXP pattern   expr RLIKE pattern    -- MySQL 전용
REGEXP_LIKE(expr, pattern)                  -- 양쪽에 있다. 단 답이 collation 에 달렸다
REGEXP_REPLACE(expr, pattern, repl)         -- 양쪽에 있다
```

규칙 여덟.

1. **`%`·`_` 가 와일드카드다.** 그 밖의 글자는 전부 그냥 글자다.
2. **`ESCAPE` 절은 방언이 아니다.** 두 엔진에서 같게 동작한다.
3. **역슬래시가 기본 이스케이프다** — 양쪽 공통. 하지만 리터럴 규칙과 얽히므로 `ESCAPE` 를 명시하는 편이 낫다.
4. **`NULL LIKE ...` 는 `NULL` 이다.** `FALSE` 가 아니라서 `NOT LIKE` 로도 안 걸린다.
5. **`ILIKE`·`~`·`~*` 는 PG 전용, `REGEXP`·`RLIKE` 는 MySQL 전용이다.** 서로 구문 오류를 낸다.
6. **`REGEXP_LIKE` 는 양쪽에 있고 답이 다르다.** collation 이 정한다.
7. **앞이 고정된 `LIKE` 만 인덱스를 좁힐 수 있다.** `LIKE '%x'` 는 어느 엔진에서도 못 탄다.
8. **PG 는 비 C collation 에서 접두사 `LIKE` 도 못 탄다.** `varchar_pattern_ops` 인덱스가 필요하다.

#### 방언 요약

| 자리 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `'abc' LIKE 'a%'`·`'_b_'`·`'%'` | 전부 참 | 전부 참 — **같다** |
| `'abc' LIKE 'A%'` | **거짓** | **참** (기본 collation) |
| `ESCAPE` 절 | 된다 | 된다 — **같다** |
| 역슬래시 기본 이스케이프 | 된다 | 된다 — **같다** |
| `NULL LIKE 'a%'` | `NULL` | `NULL` — **같다** |
| 대소문자 무시 연산자 | **`ILIKE`** | 없다 — 기본이 무시 |
| 대소문자 구분하기 | 기본이 구분 | `COLLATE utf8mb4_0900_as_cs` |
| 정규식 연산자 | **`~` / `~*`** | **`REGEXP` / `RLIKE`** (서로 구문 오류) |
| `REGEXP_LIKE('abc','^A')` | `f` | `1` — **이름이 같고 답이 다르다** |
| `REGEXP_REPLACE` | `abc-N` | `abc-N` — **같다** |
| `LIKE 'C00012%'` 의 계획 | **`Seq Scan`** (기본 인덱스로는 못 탄다) | `range`, rows 10 |
| `LIKE 'C00012%'` + 전용 인덱스 | `Index Scan`(`varchar_pattern_ops`) | 해당 없음 — 기본 인덱스로 된다 |
| `LIKE '%00123'` 의 계획 | `Seq Scan` | `index`(전부 훑기), rows 20418 |
| 정규식의 계획 | `Seq Scan` | `index`, `possible_keys` = `NULL` |

## 어디서 틀리나

- **사용자 입력을 그대로 `LIKE` 패턴에 넣는다.**\
  `%` 하나만 입력해도 **전부 잡힌다.** 입력의 `%`·`_`·이스케이프 문자를 먼저 치환하고 `ESCAPE` 를 명시한다.
- **`LIKE '%검색어%'` 로 전문검색을 구현한다.**\
  두 엔진 모두 **표를 전부 읽는다.** 행이 늘면 그대로 느려진다.\
  진짜 처방은 전문검색 색인이고, 그 자료구조는 [`data-structure/32-inverted-index`](../../../../../data-structure/32-inverted-index/)가 정본이다.
- **PG 에서 `LIKE 'abc%'` 가 인덱스를 탈 거라고 믿는다.**\
  DB collate 가 `en_US.utf8` 같은 비 C collation 이면 **안 탄다.** `varchar_pattern_ops` 인덱스가 필요하다.
- **접두사 검색에 정규식을 쓴다.**\
  `~ '^abc'` 는 사람 눈에 접두사지만 옵티마이저는 못 알아본다. `LIKE 'abc%'` 로 쓴다.
- **`REGEXP_LIKE` 가 양쪽에서 같다고 믿는다.**\
  이름도 인자도 같은데 **대소문자 판정이 다르다.** 이식에서 가장 조용한 자리다.
- **MySQL 에 `ILIKE` 를 쓴다.**\
  `ERROR 1064` 다 — 시끄러우므로 오히려 안전하다. 반대로 **PG 습관으로 `UPPER()` 를 쓰는 것이 조용히 인덱스를 죽인다.**
- **`NOT LIKE` 로 「안 맞는 것 전부」를 찾는다.**\
  값이 `NULL` 인 행은 `LIKE` 에도 `NOT LIKE` 에도 안 걸린다. `OR col IS NULL` 을 붙여야 한다.
- **역슬래시 이스케이프에 기댄다.**\
  드라이버·쉘·리터럴 규칙을 지나며 역슬래시 개수가 변한다. `ESCAPE '!'` 처럼 명시한다.

## 구현 세부사항 대 언어 보장

- **언어(문서)가 정한 것** — `%`·`_` 의 의미, `ESCAPE` 절의 동작, `NULL` 이 섞였을 때의 결과,\
  각 정규식 연산자가 어느 엔진에 있는지. 두 매뉴얼의 패턴 매칭 페이지가 정본이다.
- **collation 이 정하는 것** — **대소문자 판정 전부.** `LIKE 'A%'` 도 `REGEXP_LIKE(...,'^A')` 도 여기서 갈린다.\
  이 문서의 결과는 **PG `en_US.utf8`(결정적) · MySQL `utf8mb4_0900_ai_ci`** 에서 나온 것이다(머리말).\
  설정이 다르면 **같은 서버에서도 답이 달라진다.** 정본은 [39 collation](../39-collation/)이다.
- **옵티마이저가 정하는 것** — **`EXPLAIN` 출력 전부.**\
  20,000행·`ANALYZE` 직후·이 서버의 판단이다. 행 수가 적으면 인덱스가 있어도 순차 스캔이 뽑힌다.\
  `rows: 20418` 는 추정치이고 실제는 20,000 이다.
- **PG 의 `Seq Scan`(5번)은 「인덱스를 못 만든다」가 아니라 「이 인덱스로는 못 한다」**이다.\
  같은 질의가 `varchar_pattern_ops` 인덱스에서는 `Index Scan` 이 됐다 — **같은 문서에서 반증을 실었다.**
- 매칭 **알고리즘**(KMP·Boyer-Moore 등)은 [`algorithm/25-string-matching`](../../../../../algorithm/25-string-matching/)이 정본이고,\
  여기서는 **연산자가 무엇을 돌려주고 인덱스를 쓰는지**만 다룬다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 접두사 검색.** `LIKE 'abc%'` 는 인덱스로 좁힐 수 있는 유일한 형태다(PG 는 전용 인덱스 필요).
- **쓴다 — `ESCAPE` 를 명시한 사용자 입력 검색.** 입력의 와일드카드를 치환하고 `ESCAPE` 문자를 정한다.
- **쓴다 — `REGEXP_REPLACE` 로 정제.** 두 엔진에서 같게 돌았다. 다만 **행마다 돌므로 대량에서는 비싸다.**
- **안 쓴다 — `LIKE '%키워드%'` 를 검색 기능으로.** 전문검색 색인이나 검색 엔진의 자리다.
- **안 쓴다 — 접두사에 정규식.** 인덱스를 버린다.
- **안 쓴다 — 대소문자 무시를 `UPPER()` 로.** 열에 함수를 씌우면 인덱스를 잃는다. collation 으로 해결한다(39번).
- **조심한다 — `varchar_pattern_ops` 인덱스.** `LIKE` 에는 쓰이지만 **일반 `=`·`ORDER BY` 에는 안 쓰인다.**\
  같은 열에 인덱스 둘을 두게 되므로 쓰기 비용을 감안한다.

## 핵심 문장

- 와일드카드는 **`%`(0글자 이상)와 `_`(정확히 1글자) 둘뿐**이다.
- **`ESCAPE` 절은 두 엔진에서 같게 동작한다.** 역슬래시 기본 이스케이프도 같다.
- `'abc' LIKE 'A%'` 는 **PG 거짓 · MySQL 참** — 갈리는 것은 `LIKE` 가 아니라 **collation** 이다.
- **`ILIKE`·`~`·`~*` 는 PG 전용, `REGEXP`·`RLIKE` 는 MySQL 전용**이고 서로 구문 오류를 낸다.
- **`REGEXP_LIKE` 는 양쪽에 있고 답이 다르다** — 이식에서 가장 조용한 자리다.
- **앞이 고정된 `LIKE` 만 인덱스를 좁힌다.** `LIKE '%x'` 는 어느 엔진에서도 전부 훑는다.
- **PG 는 비 C collation 에서 접두사 `LIKE` 도 기본 인덱스로 못 탄다** — `varchar_pattern_ops` 가 필요하다.
- **정규식은 접두사여도 인덱스를 못 탄다.** `possible_keys` 가 `NULL` 인 것이 증거다.

## 관련 자료

- [PostgreSQL 18 · Pattern Matching](https://www.postgresql.org/docs/18/functions-matching.html) — `LIKE`·`ILIKE`·`~`·`regexp_like` 의 정의.
- [PostgreSQL 18 · Operator Classes and Operator Families](https://www.postgresql.org/docs/18/indexes-opclass.html) — `varchar_pattern_ops` 가 왜 필요한지.
- [MySQL 8.4 · String Comparison Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/string-comparison-functions.html) — `LIKE` 와 `ESCAPE`.
- [MySQL 8.4 · Regular Expressions](https://dev.mysql.com/doc/refman/8.4/en/regexp.html) — `REGEXP`·`RLIKE`·`REGEXP_LIKE`.
- [`algorithm/25-string-matching`](../../../../../algorithm/25-string-matching/) — **경계**: 문자열을 어떻게 빨리 찾는가(KMP·Boyer-Moore 등)는 **거기가 정본**이고,\
  여기는 **SQL 연산자가 무엇을 돌려주고 인덱스를 쓰는가**만 다룬다. 알고리즘은 한 줄도 쓰지 않는다.
- [`data-structure/32-inverted-index`](../../../../../data-structure/32-inverted-index/) — **경계**: 전문검색 색인의 구조와 비용은 **거기가 정본**이고,\
  여기는 **`LIKE '%x%'` 가 왜 못 쓰는지**까지만 다룬다.
- [37 문자열 함수와 연결 연산](../37-string-functions-and-concatenation/) — 문자열을 **만들고 자르는** 연산은 거기.
- [39 collation](../39-collation/) — 대소문자 판정을 정하는 규칙의 정본.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `NULL LIKE ...` 가 `NULL` 인 이유.
- [SQL 주제 목록](../README.md) — 46(인덱스 정의) · 47(인덱스를 언제 타나) · 58(EXPLAIN 읽기) 이 이웃이다.

## 용어 풀이

- **와일드카드(wildcard)** — 「아무 글자」를 뜻하는 기호.\
  예: `LIKE 'a%'` 의 `%` 는 뒤에 무엇이 와도 좋다는 뜻이다.
- **`ESCAPE`** — 「다음 한 글자는 와일드카드가 아니다」를 표시할 문자를 정하는 절.\
  예: `LIKE '100!%' ESCAPE '!'` 는 `'100%'` 만 잡고 `'1000'` 은 안 잡는다.
- **`ILIKE`** — PG 전용. 대소문자를 무시하는 `LIKE`.\
  예: `'abc' ILIKE 'A%'` → 참. MySQL 에 쓰면 `ERROR 1064`.
- **`REGEXP` / `RLIKE`** — MySQL 의 정규식 일치 연산자(서로 동의어).\
  예: `'abc' REGEXP '^a'` → 1. PG 에 쓰면 구문 오류다.
- **`~` / `~*`** — PG 의 정규식 일치 연산자. `~*` 는 대소문자를 무시한다.\
  예: `'abc' ~* '^A'` → 참. MySQL 에 쓰면 `ERROR 1064`.
- **접두사 검색(prefix search)** — 앞부분이 고정된 검색.\
  예: `LIKE 'C00012%'` — 인덱스의 연속 구간이라 좁힐 수 있다.
- **연산자 클래스(operator class)** — PG 에서 인덱스가 값을 어떤 규칙으로 비교할지 정하는 것.\
  예: `varchar_pattern_ops` 는 바이트 순서로 비교해 `LIKE` 접두사 검색을 가능하게 한다.
- **`possible_keys`(MySQL `EXPLAIN`)** — 옵티마이저가 쓸 수 있다고 본 인덱스 목록.\
  예: 정규식 조건에서는 `NULL` 이다 — **후보에도 못 들었다**는 뜻이다.
- **`Index Cond` 대 `Filter`(PG `EXPLAIN`)** — 인덱스가 직접 쓴 조건과, 행을 읽은 뒤 거른 조건.\
  예: `LIKE 'C00012%'` 가 `Index Cond: (... ~>=~ 'C00012' AND ... ~<~ 'C00013')` 로 바뀐 것이 인덱스를 썼다는 증거다.
- **collation** — 문자열을 비교·정렬하는 규칙의 이름.\
  예: MySQL 기본 `utf8mb4_0900_ai_ci` 에서 `'abc' LIKE 'A%'` 가 참이 된다.

## 더 들어가면

- **PG 가 접두사 `LIKE` 를 범위 둘로 바꾸는 것**이 5번의 `Index Cond` 에 그대로 보인다.\
  `>= 'C00012' AND < 'C00013'` — **마지막 글자를 하나 올린 값이 상한**이다.\
  이 변환이 성립하려면 인덱스의 정렬이 바이트 순서여야 하고, 그래서 `varchar_pattern_ops` 가 필요하다.
- **MySQL 이 같은 문제를 안 겪는 이유**는 인덱스 정렬과 `LIKE` 비교가 **같은 collation** 을 쓰기 때문이다.\
  대신 **collation 을 바꾸면 인덱스를 잃는다** — 39번에서 경고 1739 로 확인한다. **대칭이다.**
- **`LIKE '%x%'` 를 빠르게 하는 길**이 아주 없지는 않다. PG 에는 trigram 색인이,\
  MySQL 에는 전문검색 색인이 있다. 다만 **문법이 아니라 색인 설계**의 영역이라 여기서 다루지 않는다.
- **정규식을 옵티마이저가 분해하지 않는 것**은 게으름이 아니라 **비용 문제**다.\
  임의의 정규식에서 안전하게 접두사를 뽑아내는 것은 일반적으로 어렵고, 틀리면 **행을 빠뜨린다.**\
  인덱스 최적화는 **틀리면 안 되는 쪽**이라 보수적으로 포기한다.
