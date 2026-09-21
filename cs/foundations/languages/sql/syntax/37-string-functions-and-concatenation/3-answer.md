# sql/37-문자열 함수와 연결 연산 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> **환경 조건** — PG `server_encoding` = `UTF8` · MySQL `character_set_server` = `utf8mb4`, 클라이언트도 `--default-character-set=utf8mb4`.\
> MySQL `sql_mode` 는 기본값이고 **`PIPES_AS_CONCAT` 이 없다**(8번에서 실제 값을 찍었다).\
> `emp`·`dept` 는 읽기만 했고 바꾸지 않았다.\
> 문서 근거는 [PG 18 String Functions](https://www.postgresql.org/docs/18/functions-string.html) · [MySQL 8.4 String Functions](https://dev.mysql.com/doc/refman/8.4/en/string-functions.html) · [MySQL 8.4 Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. ★ `'a' || 'b'` — **PG 는 `'ab'`, MySQL 은 `0`**

**출력**

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

**왜 그런가**

```text
PostgreSQL                          MySQL
|| 는 연결 연산자다                  || 는 논리 OR 의 비표준 동의어다
       ↓                                     ↓
  두 문자열을 잇는다                  두 값을 불리언으로 읽는다
       ↓                                     ↓
      'ab'                           'a' -> 0,  'b' -> 0
                                            ↓
                                        0 OR 0 -> 0
```

**에러가 아니라 값이 나온다.** 이것이 이 차이가 비싼 이유다.\
`SELECT last_name || first_name AS full_name` 을 MySQL 에 던지면 **모든 행의 이름이 `0`** 이 된다.

서버는 경고 셋을 남긴다.

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

**1287 이 결정적인 근거다.** 「`||` 는 OR 의 동의어」라고 서버가 직접 말한다 — 추측이 아니다.\
1292 둘은 35번에서 본 **문자열→수치 변환 실패**와 같은 경고다.

---

### 2. `1 || 0` 이 `1` 인 것이 증거다

**출력**

```text
--- MySQL 8.4.10 ---
SELECT 1 || 0 AS a, 0 || 0 AS b, 'x' || 1 AS c;
+---+---+---+
| a | b | c |
+---+---+---+
| 1 | 0 | 1 |
+---+---+---+
```

**왜 그런가**

```text
만약 || 가 연결이라면            실제 답
  1 || 0  -> '10'                  1
  0 || 0  -> '00'                  0
  'x' || 1 -> 'x1'                 1

OR 로 읽으면 전부 맞는다
  1 OR 0  -> 1
  0 OR 0  -> 0
  'x'(->0) OR 1 -> 1
```

**`0 || 0` 이 `0` 이고 `1 || 0` 이 `1` 인 것**이 OR 임을 확정한다.\
연결이라면 `'00'` 과 `'10'` 이 나와야 하고, 둘 다 수치로 읽어도 `0` 과 `10` 이지 `0` 과 `1` 이 아니다.

PG 쪽은 수치를 섞으면 문자열로 바꿔 붙인다.

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

**같은 문장이 한쪽은 `'a1'`, 한쪽은 `1`** 이다. 타입도 뜻도 다르다.

---

### 3. ★ `NULL` 이 섞이면 — **`CONCAT` 의 의미가 정확히 반대다**

**출력**

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

(psql 은 `NULL` 을 빈 칸으로 그린다 — PG 의 `pipe` 는 `NULL` 이다.)

**왜 그런가**

| 식 | PG 18.6 | MySQL 8.4.10 | 규칙 |
|---|---|---|---|
| `'a' \|\| NULL` | `NULL` | `NULL` | PG: 연결에 `NULL` 이 섞이면 전파 / MySQL: `0 OR NULL` = `NULL` |
| `CONCAT('a', NULL)` | **`'a'`** | **`NULL`** | ★ 반대다 |
| `CONCAT_WS('-','a',NULL,'b')` | `'a-b'` | `'a-b'` | 양쪽 다 `NULL` 을 건너뛴다 |

```text
PostgreSQL 의 입장                  MySQL 의 입장
"빈 것은 빼고 붙인다"                "모르는 것이 섞이면 결과도 모른다"
  CONCAT('a', NULL) -> 'a'            CONCAT('a', NULL) -> NULL
       ↓                                   ↓
  실무에 편하다                       NULL 의 원래 의미에 가깝다
```

**둘 다 일관된 입장이라 더 헷갈린다.** 어느 한쪽이 버그가 아니다.

**같은 `NULL` 이 `'a' || NULL` 에서는 두 엔진이 같은 답을 낸다** — 그런데 **이유가 다르다.**\
PG 는 연결의 `NULL` 전파, MySQL 은 `OR` 의 3값 논리(`0 OR NULL` = `NULL`)다.\
`OR` 의 3값 논리는 [04 NULL 의 3값 논리](../04-null-three-valued-logic/)가 정본이다.

실제 열로 보면 이렇다. `cho` 의 `salary` 가 `NULL` 이다.

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

**캐스팅해도 `NULL` 은 `NULL` 이다.** 문자열로 바뀌지 않는다 — 그래서 `COALESCE` 가 먼저다.\
(PG 의 `c` 열이 넓은 것은 `CHAR(10)` 이 공백으로 채워지기 때문이다. 35번 2번 참조.)

---

### 4. ★ `LENGTH` — **PG 는 5, MySQL 은 9**

**출력**

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

**왜 그런가**

```text
'한글abc' 를 UTF-8 로 담으면

  한        글        a     b     c
 3바이트   3바이트    1     1     1      -> 9바이트
 1글자     1글자      1     1     1      -> 5글자

PG 의 LENGTH    = 글자 수  -> 5   (CHAR_LENGTH 와 같다)
MySQL 의 LENGTH = 바이트 수 -> 9   (OCTET_LENGTH 와 같다)
```

**`CHAR_LENGTH` 와 `OCTET_LENGTH` 는 두 엔진에서 한 자리도 안 갈렸다.**\
갈리는 것은 `LENGTH` 라는 **이름 하나**다.

**어디서 물리나**

```sql
-- 요구사항: 이름은 10글자까지
WHERE LENGTH(name) <= 10
```

- PG — 한글 10글자까지 통과한다. 의도대로다.
- MySQL — 한글은 글자당 3으로 세므로 **3글자까지만** 통과한다.

`'가나다라마'`(5글자)가 MySQL 에서 **15** 로 세어져 거부된다. **에러가 아니라 조건이 틀어진 것**이다.

**★ 그리고 길이를 재기 전에 값이 이미 잘려 있을 수 있다.**

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

```text
PG 에서 무슨 일이 일어났나
  CAST(1234567 AS CHAR)  ->  CHAR 에 길이가 없다 -> char(1) -> '1'   (35번 2번)
        ↓
  LENGTH('1')  ->  1
        ↓
  ★ LENGTH 는 정확히 일했다. 이미 잘린 값을 잰 것이다
```

**「길이를 검사했으니 괜찮다」가 여기서 무너진다.** 검사 대상이 원본이 아니기 때문이다.

한글이 왜 UTF-8 에서 3바이트인지는 [`foundations/data-representation`](../../../../data-representation/)이 정본이다.\
여기서 외울 것은 **「어느 함수가 무엇을 세나」**와 **「무엇을 재고 있나」** 둘이다.

---

### 5. 범위 밖 인덱스 — **시작이 1 미만이면 갈린다**

**출력**

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

**왜 그런가**

```text
SUBSTRING('abcdef', 0, 3)
  PG    : 0번 자리(문자열 앞의 가상 자리)부터 3칸을 세고
          그중 실재하는 것만 남긴다 -> 0,1,2 중 1,2 가 실재 -> 'ab'
  MySQL : 위치는 1부터 센다. 0 은 유효한 시작이 아니다 -> '' (빈 문자열)

SUBSTRING('abcdef', -2)
  PG    : -2 부터 끝까지 -> 왼쪽 밖에서 시작하므로 전부 -> 'abcdef'
  MySQL : 음수는 "뒤에서부터" 를 뜻한다 -> 뒤에서 2번째부터 -> 'ef'
```

**정상 범위에서는 두 엔진이 같다.** 두 표기 모두 통한다.

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

**어디서 물리나** — 오프셋을 계산해서 넣을 때다.

```sql
SELECT SUBSTRING(code, pos - 1, 3) FROM t;   -- pos = 1 이면 시작이 0 이 된다
```

`pos = 1` 인 행에서 PG 는 `'ab'` 비슷한 것을, MySQL 은 **빈 문자열**을 준다. **에러가 안 난다.**\
처방은 `SUBSTRING(code, GREATEST(pos - 1, 1), 3)` 로 **1 미만을 막는 것**이다.

---

### 6. `'abc' = 'ABC'` — **함수가 아니라 collation 이 정한다**

**출력**

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

**왜 그런가**

```text
PostgreSQL (이 서버: en_US.utf8, 결정적)   MySQL (이 서버: utf8mb4_0900_ai_ci)
대소문자가 다르면 다른 값이다               ai = accent insensitive (악센트 무시)
       ↓                                    ci = case insensitive  (대소문자 무시)
      거짓                                         ↓
                                                   참
```

**`UPPER` 를 쓰지 않았는데 MySQL 은 같다고 한다.** 비교 규칙이 문자열 함수 바깥에 있기 때문이다.

이 갈래의 정본은 [39 collation](../39-collation/)이다. 거기서 환경(`SHOW COLLATION` 출력)까지 확인한다.\
여기서 넘겨받을 것은 하나다 — **대소문자 무시를 `UPPER` 로 구현하려 하기 전에 collation 을 보라.**

---

### 7. 갈리지 않는 것 — **일곱 다 같다**

**출력**

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

**왜 이걸 확인하는가** — 「SQL 문자열 함수는 전부 방언」이라는 인상이 생기면 **불필요한 방어 코드**를 쓰게 된다.

이 주제의 방언 경계는 **넷에 몰려 있다.**

```text
갈린다                          안 갈린다
──────                          ────────
||                              TRIM / LTRIM / RTRIM
CONCAT 의 NULL                  REPLACE
LENGTH                          UPPER / LOWER
SUBSTRING 의 1 미만 인덱스       LPAD / RPAD / REPEAT / REVERSE
                                POSITION
                                CONCAT_WS
                                SUBSTRING 의 정상 범위
                                CHAR_LENGTH / OCTET_LENGTH
```

`POSITION` 이 `3` 인 것도 읽어 둘 값어치가 있다 — **두 엔진 다 1부터 세고, 첫 번째 일치를 돌려준다.**

---

### 8. 설정으로 고칠 수 있나 — **된다. 그래서 더 위험하다**

**출력**

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

(줄바꿈만 폭에 맞게 접었다.)

**왜 처방으로 삼지 않나**

```text
이 출력이 증명하는 것 둘

(1) PIPES_AS_CONCAT 을 켜면 || 가 연결이 된다          -> 고칠 수는 있다
(2) 내가 CONCAT 으로 "덧붙였는데" 목록에 새로 생겼다   -> ★ 기본값에는 없었다
```

그래서 이렇게 된다.

```text
개발 서버 (모드 켬)            운영 서버 (기본값)
SELECT a || b  ->  'ab'        SELECT a || b  ->  0
       ↓                              ↓
  테스트 통과                    조용히 0 이 쌓인다
```

**질의의 의미가 서버 설정에 달리는 것**이 문제다. 36번의 `div_precision_increment`·`sql_mode` 와 같은 종류의 함정이다.

**처방은 `CONCAT()` 이다.** 설정과 무관하고 두 엔진에 다 있다.

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

---

### 9. 두 엔진에서 같게 만들려면 — **`NULL` 을 먼저 없앤다**

**두 방법이 있고, 고르는 기준이 다르다.**

```sql
-- (a) COALESCE 로 NULL 을 빈 문자열로 확정한다
SELECT CONCAT(COALESCE(last_name,''), COALESCE(first_name,'')) AS full_name FROM t;

-- (b) 구분자가 필요하면 CONCAT_WS
SELECT CONCAT_WS(' ', last_name, middle_name, first_name) AS full_name FROM t;
```

**왜 이 둘인가**

| 방법 | PG | MySQL | 비고 |
|---|---|---|---|
| `a \|\| b` | 연결 (`NULL` 전파) | **OR** | 쓰면 안 된다 |
| `CONCAT(a, b)` | `NULL` 건너뜀 | **`NULL` 전파** | 그대로 쓰면 갈린다 |
| `CONCAT(COALESCE(a,''), COALESCE(b,''))` | 같다 | 같다 | ✅ |
| `CONCAT_WS(sep, a, b)` | `NULL` 건너뜀 | `NULL` 건너뜀 | ✅ |

**(b)를 고를 때 주의** — `CONCAT_WS` 는 `NULL` 은 건너뛰지만 **빈 문자열은 건너뛰지 않는다.**\
`middle_name` 이 `''` 이면 구분자가 두 번 들어간다. 「없음」을 `NULL` 로 쓸지 `''` 로 쓸지는 **스키마 설계 결정**이다.

**세 번째 선택지도 있다 — DB 에서 안 붙이는 것.**\
표시용 문자열 조립은 애플리케이션이 하는 편이 대개 낫다.\
DB 에서 붙이면 그 결과로 필터하거나 정렬할 때 **인덱스를 못 쓰게** 되기 쉽다(11번).

---

### 10. 길이 검증 — **`CHAR_LENGTH` 하나로 통일한다**

```sql
-- 요구사항: 이름은 10글자까지
WHERE CHAR_LENGTH(name) <= 10     -- 두 엔진 동일
```

**왜 `LENGTH` 가 아닌가** — 4번에서 본 대로 MySQL 에서 바이트를 세기 때문이다.

```text
'가나다라마' (5글자)

LENGTH       PG -> 5      MySQL -> 15    ★ 갈린다
CHAR_LENGTH  PG -> 5      MySQL -> 5     같다
OCTET_LENGTH PG -> 15     MySQL -> 15    같다
```

**그런데 `WHERE` 에 쓰면 인덱스를 못 탄다.** 열에 함수를 씌우는 것이기 때문이다(11번).

**그래서 길이 검증의 자리는 셋 중 하나다.**

1. **열 타입으로 강제한다** — `varchar(10)`. 가장 싸고 확실하다.\
   단 **MySQL 의 `varchar(10)` 은 10 글자**다(바이트가 아니다). 이건 `LENGTH` 와 반대라 헷갈린다.
2. **`CHECK` 제약으로 강제한다** — `CHECK (CHAR_LENGTH(name) <= 10)`.\
   MySQL 의 `CHECK` 는 8.0.16 부터 실제로 강제된다(목록 README 의 릴리스 노트 근거).
3. **애플리케이션에서 검증한다** — 사용자에게 메시지를 돌려줘야 하면 어차피 여기서도 해야 한다.

**조회 조건으로 길이를 쓰는 것은 마지막 수단**이다. 그런 요구가 나오면 대개 **열 설계가 잘못된 것**이다.

---

### 11. `WHERE UPPER(name) = 'ANN'` 이 잃는 것

**두 가지를 잃는다 — 그리고 엔진마다 잃는 것이 다르다.**

```text
공통으로 잃는 것: 인덱스
  name 의 인덱스는 "name 의 원래 값" 순서다
  질의는 "UPPER(name)" 을 찾는다
        ↓
  정렬이 다른 자료를 뒤지는 셈 -> 전부 훑는다
```

35번 8번에서 PG 로 실측한 모양과 같다.

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t35 WHERE substr(code,2)::int = 123;
                      QUERY PLAN                      
------------------------------------------------------
 Seq Scan on t35
   Filter: ((substr((code)::text, 2))::integer = 123)
(2 rows)
```

`Index Cond` 가 아니라 `Filter` 로 내려간 것이 **인덱스를 못 썼다는 증거**다.

**MySQL 에서는 그 위에 하나를 더 잃는다 — 필요가 없는 일을 한다.**

```text
### SQL: SELECT 'abc' = 'ABC' AS same_case;
--- MySQL 8.4.10 ---
+-----------+
| same_case |
+-----------+
|         1 |
+-----------+
```

기본 collation 이 이미 대소문자를 무시하므로 **`UPPER` 가 아무것도 안 바꾼다.**\
비용만 내고 인덱스만 잃는다.

**처방**

| 상황 | 처방 |
|---|---|
| MySQL, 기본 collation | **아무것도 안 한다.** `WHERE name = 'ANN'` 으로 충분하다 |
| PG, 대소문자 무시가 필요 | 비결정적 ICU collation 을 쓰거나(39번), **표현식 인덱스**를 만든다 |
| 양쪽 공통 | 정규화한 값을 **열로 저장**한다(`name_normalized`) — 인덱스가 산다 |

`CREATE INDEX ... ON t (upper(name))` 같은 표현식 인덱스는 목록의 **46번 주제**,\
인덱스를 타고 못 타는 판단 전반은 목록의 **47번 주제**가 정본이다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `'a' \|\| 'b'` (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **경고 1287 이 근거다** |
| `SHOW WARNINGS` (1번) | MySQL 8.4.10 | 1회 | 1287 + 1292×2 |
| `1\|\|0`·`0\|\|0`·`'x'\|\|1` (2번) | MySQL 8.4.10 | 1회 | **OR 임을 확정하는 근거** |
| `'a' \|\| 1` (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `\|\|`·`CONCAT`·`CONCAT_WS` 의 `NULL` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **세 값을 한 문에서** |
| `emp` 의 `NULL` 캐스팅 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 읽기만 — 표 변경 없음 |
| `LENGTH`·`CHAR_LENGTH`·`OCTET_LENGTH` (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 리터럴 `'한글abc'` |
| `LENGTH(CAST(1234567 AS CHAR))` (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG `1` 대 MySQL `7`** — 35번의 잘림이 여기로 번진다 |
| `SUBSTRING` 정상 범위 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 두 표기 모두 |
| `SUBSTRING` 범위 밖 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL 빈 문자열이 근거다** |
| `'abc' = 'ABC'` (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 39번으로 넘김 |
| `TRIM` 4형태 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **전부 같다** |
| `REPLACE`·`UPPER`·`LOWER` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **전부 같다** |
| `LPAD`·`RPAD`·`REPEAT`·`REVERSE` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **전부 같다** |
| `POSITION` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **같다** |
| `PIPES_AS_CONCAT` (8번) | MySQL 8.4.10 | 1회 | `sql_mode` 실제 값 확인 포함 |
| `CONCAT('a','b')` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `EXPLAIN` 의 `Filter` (11번) | PG 18.6 | 1회 | 35번의 `t35` 표 — **실험 후 삭제** |

**설정 의존 항목** — 1·8번(`sql_mode` 의 `PIPES_AS_CONCAT`) · 4번(문자셋이 `utf8mb4`/`UTF8`).\
**인코딩이 다르면 4번의 `9` 가 달라진다.** 머리말에 적은 환경에서 나온 결과다.

**collation 의존 항목** — 6번. 이 서버의 MySQL 기본 collation 은 `utf8mb4_0900_ai_ci` 이고,\
PG 는 `en_US.utf8`(결정적)이다. 근거와 확인 방법은 [39 collation](../39-collation/)에 있다.

**구현 의존 항목** — 11번의 `EXPLAIN` 출력. 계획은 통계·행 수가 정하는 **관찰**이지 보장이 아니다.

**언어 보장 항목** — 1·2·3·4·5·7·8번.\
`||` 의 의미, `CONCAT`/`CONCAT_WS` 의 `NULL` 처리, `LENGTH` 가 무엇을 세는지, `SUBSTRING` 의 범위 밖 해석,\
`TRIM` 계열의 동작 — 전부 두 매뉴얼의 문자열 함수 페이지가 정한 것이다.

**버전을 적지 않은 이유** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 **두 매뉴얼에서도 릴리스 노트에서도 찾지 못했다.**\
MySQL 이 `||` 를 **deprecated** 로 표시한다는 사실은 서버가 직접 낸 경고 1287 로만 적었고, **제거 예정 버전은 적지 않았다**(서버도 말하지 않는다).

**DB 잔재** — 없다. 이 주제는 `emp`·`dept` 를 읽기만 했고, 11번에서 쓴 `t35` 는 35번의 실험 표로 **작업 후 삭제**했다.
