# sql/35-타입 체계와 캐스팅 (명시 변환·암시 변환) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 표를 만든 실험은 전부 **끝나고 지웠다**(`t35`·`t35b`). `emp`·`dept` 는 읽기만 했다.\
> 문서 근거는 [PG 18 Type Conversion](https://www.postgresql.org/docs/18/typeconv.html) · [MySQL 8.4 Type Conversion](https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html) · [MySQL 8.4 Cast Functions](https://dev.mysql.com/doc/refman/8.4/en/cast-functions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `CAST` 의 타입 이름 — **서로를 정확히 거부한다**

**`INTEGER` 는 PG 만, `SIGNED` 는 MySQL 만 받는다.**

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

두 에러의 **성격이 다르다.**

```text
MySQL: ERROR 1064  = 문법 오류. 파서가 INTEGER 라는 토큰을 그 자리에서 못 받는다
PG:    type "signed" does not exist = 문법은 맞다. 그런 이름의 타입이 카탈로그에 없다
```

> **`ERROR 1064`** — MySQL 의 문법 오류 코드. 파서가 문장을 읽다 멈춘 자리를 `near '...'` 로 알려 준다.\
> 예: `near 'INTEGER) + 1 AS r'` 은 `INTEGER` 부터 읽지 못했다는 뜻이다.

**둘 다 받는 이름은 `DECIMAL(p,s)`** 이다 — 이식 가능한 유일한 수치 캐스트다.

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

PG 의 축약 `::` 도 MySQL 파서가 모른다.

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

---

### 2. ★ `CAST(123 AS CHAR)` — **PG 는 `1`, MySQL 은 `123`**

**에러가 안 난다. 값이 조용히 잘린다.**

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

```text
PostgreSQL                          MySQL
CHAR 에 길이를 안 적으면            CAST 안의 CHAR 는
  char(1) 이다                        길이 제한 없는 문자열이다
       ↓                                    ↓
  '123' 을 char(1) 에 넣는다           '123' 그대로
       ↓                                    ↓
     '1'                                  '123'
```

**왜 이게 위험한가** — 1번의 두 에러는 **배포 전에 터진다.** 이것은 안 터진다.\
`CAST(order_no AS CHAR)` 를 MySQL 에서 PG 로 옮기면, 주문번호가 **첫 글자 한 자**가 되어 조회가 조용히 빈다.

**★ 한 자리 값으로는 안 드러난다.** 이것이 이 사고가 오래 사는 이유다.

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

`CAST(5 AS CHAR)` 였다면 **양쪽 다 `5`** 다. **테스트 데이터가 한 자리면 통과한다.**

**그럼 무엇으로 바꾸나 — 네 후보를 전부 던져 봤다.**

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

`CAST(10 AS VARCHAR(10))` 도 같은 `ERROR 1064` 이고, `CAST(123 AS TEXT)` 도 그렇다.

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

**표로 놓으면 답이 하나로 좁혀진다.**

| 쓰는 법 | PG 18.6 | MySQL 8.4.10 | 판정 |
|---|---|---|---|
| `CAST(10 AS CHAR)` | **`1`** | `10` | ★ 둘 다 통과, **답이 다르다** |
| `CAST(10 AS CHAR(10))` | `10`(뒤 공백 채움) | `10` | ✅ **유일하게 같다** |
| `CAST(10 AS VARCHAR)` | `10` | `ERROR 1064` | 이식 불가(시끄럽다) |
| `CAST(10 AS VARCHAR(10))` | `10` | `ERROR 1064` | 이식 불가(시끄럽다) |
| `CAST(123 AS TEXT)` | `123` | `ERROR 1064` | 이식 불가(시끄럽다) |

**이식 가능한 것은 `CHAR(n)` 하나뿐이다.**\
다만 PG 의 `char(10)` 은 **공백으로 채워진다**(위 출력의 넓은 칸). 필요하면 `TRIM` 한다.\
뒤 공백이 비교에서 무시되는지는 collation 이 정한다 — [39 collation](../39-collation/) 5번.

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

**잘린 뒤에는 길이 검증도 무의미해진다** — 37번으로 이어지는 자리다.

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

**PG 의 `len` 이 `1` 이다.** 일곱 자리 값을 넣었는데 길이가 1 로 나온다 —\
`LENGTH` 가 틀린 게 아니라 **이미 잘린 값을 잰 것**이다.\
「길이가 맞는지 검사했으니 괜찮다」가 여기서 무너진다.

**그래서 결론** — 문자열 캐스트는 **질의 밖으로 빼는 편**이 낫다.\
꼭 질의에서 해야 하면 **`CAST(x AS CHAR(n))` 으로 길이를 명시**하고, PG 쪽 뒤 공백을 감안한다.

---

### 3. 변환이 실패하면 — **PG 는 죽고, MySQL 은 `0` 으로 읽는다**

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

**MySQL 의 `0` 을 「다르다」로 읽으면 안 된다.**

```text
MySQL 이 실제로 한 일
  'abc' 를 앞에서부터 수치로 읽는다 -> 읽을 숫자가 없다 -> 0
  1 = 0 -> 거짓 -> 0

그래서 이렇게 된다
  SELECT 0 = 'abc';   -> 1 (참!)
```

경고가 유일한 신호다.

```text
--- MySQL 8.4.10 ---
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

**변환이 성공하는 경우는 두 엔진이 같다** — 이것까지 갈린다고 외우면 과잉이다.

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

---

### 4. ★ 따옴표 하나 — **PG 는 문이 안 서고, MySQL 은 20,000행을 훑어 0행을 돌려준다**

먼저 정상 질의(a). 양쪽 다 인덱스를 탄다.

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

(b) 는 이렇게 갈린다.

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
EXPLAIN (COSTS OFF)                        EXPLAIN
  SELECT * FROM t35 WHERE code = 123;        SELECT * FROM t35 WHERE code = 123;

--- 실제 출력 ---                          --- 실제 출력 ---
ERROR:  operator does not exist:           type:          index
  character varying = integer              possible_keys: t35_code_idx
LINE 1: ... WHERE code = 123;              key:           t35_code_idx
                       ^                   rows:          19905
HINT:  No operator matches the given       filtered:      10.00
  name and argument types. You might       Extra:         Using where; Using index
  need to add explicit type casts.

  -> 비교 자체가 존재하지 않는다              -> rows 가 1 -> 19905 로 늘었다
```

MySQL 은 인덱스를 포기한 이유를 **그 자리에서** 말해 준다.

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

**그리고 답이 비어 있다.**

```text
--- MySQL 8.4.10 ---
SELECT COUNT(*) AS matched FROM t35 WHERE code = 123;
+---------+
| matched |
+---------+
|       0 |
+---------+
```

```text
왜 0 행인가
  'C000001' 을 수치로 읽는다 -> 앞 글자가 'C' -> 0
  'C000123' 을 수치로 읽는다 -> 0
  ...
  20,000 행이 전부 0 이 된다.  0 = 123 은 어디서도 참이 아니다
```

**느린 것보다 나쁜 것은 틀린 것이다.** 여기선 둘 다 일어난다.

> **`type: index`(MySQL `EXPLAIN`)** — 인덱스를 **처음부터 끝까지 훑는** 접근. 「인덱스를 썼다」가 아니라 **「전부 읽었다」**에 가깝다.\
> 예: `ref`(값 하나를 짚음, rows 1) → `index`(전부 훑음, rows 19905).

---

### 5. `BOOLEAN` — **PG 는 타입, MySQL 은 `tinyint(1)` 의 별칭**

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

**열로 선언해 보면 MySQL 이 무엇으로 바꾸는지 보인다.**

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

SELECT b::int AS as_int FROM t35b;
 as_int 
--------
      1
      0
(2 rows)
```

**실무에 미치는 차이 셋.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `SUM(flag)` | 에러 — `b::int` 로 명시해야 | 그냥 된다 |
| `flag = 2` 인 행 | 넣을 수 없다 | 넣을 수 있다 — `IS TRUE` 에는 걸린다 |
| 값의 표시 | `t` / `f` | `1` / `0` |

MySQL 쪽의 편의에는 **「불리언이 아닌 값이 들어갈 수 있다」**는 대가가 붙는다.

---

### 6. `UNION` 의 열 타입 — **PG 는 거부, MySQL 은 문자열로 올린다**

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

```text
PostgreSQL                          MySQL
첫 가지의 타입 integer 로 맞춘다     둘 다 담을 수 있는 문자열로 올린다
       ↓                                    ↓
  'a' 를 integer 로 읽는다 -> 실패      1 이 '1' 이 되고 'a' 는 그대로
       ↓                                    ↓
      ERROR                            두 행이 다 나온다
```

**MySQL 쪽 결과의 함정** — 나온 `1` 은 정수가 아니라 **문자열 `'1'`** 이다.\
이 결과를 정렬하면 문자열 순서라서 `'10'` 이 `'9'` 앞에 온다(9번 참조).

집합 연산의 나머지 규칙(열 개수·`ALL` 의 중복 제거)은 목록의 **34번 주제**가 정본이다.

---

### 7. `NULL` 의 타입 — **문맥이 정한다**

**PG 는 `unknown`, MySQL 은 `varbinary(0)` 으로 굳힌다.**

```text
--- PG 18.6 ---
SELECT pg_typeof(NULL) AS t, pg_typeof(NULL::int) AS t2, pg_typeof(1) AS t3,
       pg_typeof(1.5) AS t4, pg_typeof('x') AS t5;
    t    |   t2    |   t3    |   t4    |   t5    
---------+---------+---------+---------+---------
 unknown | integer | integer | numeric | unknown
(1 row)
```

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

**읽을 것이 둘 더 있다.**

- `1.5` 가 양쪽 다 **십진수**다(`numeric` / `decimal(2,1)`) — 부동소수가 **아니다.**\
  36번에서 `0.1 + 0.2` 가 딱 `0.3` 으로 나오는 이유가 바로 이것이다.
- PG 의 `'x'` 도 `unknown` 이다. 문자열 리터럴조차 **주변이 정해 준다.**

**언제 이게 물리나** — 뷰·CTE·`CREATE TABLE AS` 의 열 타입이 내 의도와 달라질 때다.\
처방은 하나다. `SELECT CAST(NULL AS int) AS x` 처럼 **못 박는다.**

`NULL` 의 비교·논리 규칙 자체는 [04 NULL 의 3값 논리](../04-null-three-valued-logic/)가 정본이다.

---

### 8. 암시 변환이 언제나 인덱스를 죽이나 — **아니다. 「열 쪽이 변할 때」만이다**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t35 WHERE id = 123::bigint;
             QUERY PLAN             
------------------------------------
 Index Scan using t35_pkey on t35
   Index Cond: (id = '123'::bigint)
(2 rows)
```

`id` 는 `int` 이고 값은 `bigint` 다. **타입이 다른데 인덱스를 탔다.**

```text
살아남는 쪽                          죽는 쪽
─────────                            ──────
값을 열의 타입으로 맞춘다             열을 값의 타입으로 맞춘다
  123::bigint -> int 범위로 판정        code -> 수치로 변환
        ↓                                    ↓
인덱스의 정렬이 그대로 쓰인다          인덱스의 정렬과 다른 값을 찾게 된다
        ↓                                    ↓
   Index Scan                          Seq Scan / type: index
```

**열을 직접 건드려도 똑같이 죽는다.** 이건 두 엔진 공통이다.

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t35 WHERE substr(code,2)::int = 123;
                      QUERY PLAN                      
------------------------------------------------------
 Seq Scan on t35
   Filter: ((substr((code)::text, 2))::integer = 123)
(2 rows)
```

그래서 규칙은 **「암시냐 명시냐」가 아니라 「열이 원래 모습대로 비교되나」**다.\
이 기준은 39번의 `COLLATE` 사고에도, 38번의 `LIKE '%x'` 에도 똑같이 적용된다.\
인덱스를 타고 못 타는 판단 전반은 목록의 **47번 주제**가 정본이다.

> **인덱스 조건(`Index Cond`)** — PG 가 인덱스를 뒤질 때 직접 쓴 조건.\
> 예: `Filter:` 로 내려간 조건은 **행을 다 읽은 뒤** 거른 것이라 인덱스를 못 쓴 것이다.

---

### 9. `'10' > '9'` 가 거짓인 이유 — **양쪽이 문자열이면 변환이 일어나지 않는다**

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

```text
문자열 비교는 글자를 앞에서부터 본다

  '10'          '9'
   ^             ^
  '1'  vs       '9'      -> '1' 이 '9' 보다 앞이다 -> '10' < '9'
  (뒤는 볼 필요가 없다)
```

**변환은 「양쪽 타입이 다를 때」만 일어난다.** 둘 다 문자열이면 엔진이 손댈 이유가 없다.

여기서 배울 것은 값 하나가 아니라 **규칙의 출발점**이다.

```text
양쪽 타입이 같다  -> 그 타입의 규칙으로 비교한다 (변환 없음)
양쪽 타입이 다르다 -> 한쪽을 바꾼다  <- 여기서 2·3·4번의 모든 일이 벌어진다
```

그래서 `'10' > 9` 는 **참**이 된다(MySQL 기준 — 한쪽이 수치라 문자열이 수치로 변한다).\
같은 두 값이 **따옴표 하나로 뒤집힌다.**

---

### 10. 조용히 넘어간 것을 알아내는 통로 — **`SHOW WARNINGS`**

**MySQL 은 결과에 싣지 않고 경고로만 남긴다. 명시적으로 물어야 한다.**

| 무엇 | 코드 | 언제 | 결과에 보이나 |
|---|---|---|---|
| 문자열을 수치로 못 읽음 | **1292** | `'abc' + 1`, `1 = 'abc'` | 안 보인다 — 값만 나온다 |
| 타입·collation 때문에 인덱스 포기 | **1739** | `varchar 열 = 정수` | 안 보인다 — `EXPLAIN` 의 `type` 이 바뀔 뿐 |
| 0 으로 나눔 | 1365 | `SELECT 1/0` | `NULL` 로만 보인다(36번) |
| `\|\|` 를 OR 로 해석 | 1287 | `'a' \|\| 'b'` | `0` 으로만 보인다(37번) |
| 잘못된 날짜 | 1292 | `CAST('2026-02-30' AS DATE)` | `NULL` 로만 보인다(40번) |

**한 줄로 요약하면** — MySQL 에서 「에러가 안 났다」는 「문제가 없었다」가 아니다.

쓰는 법은 단순하다. **바로 다음 문**으로 쳐야 한다.

```text
--- MySQL 8.4.10 ---
SELECT 'abc' + 1 AS r;
SHOW WARNINGS;
+---------+------+-----------------------------------------+
| Level   | Code | Message                                 |
+---------+------+-----------------------------------------+
| Warning | 1292 | Truncated incorrect DOUBLE value: 'abc' |
+---------+------+-----------------------------------------+
```

**PG 에는 대응물이 없다** — 대응물이 필요 없다. 같은 상황에서 문이 죽기 때문이다.\
PG 쪽에서 봐야 할 것은 경고가 아니라 **`EXPLAIN` 의 `Index Cond` 대 `Filter`** 다.

---

### 11. 그래서 어떻게 고치나

**살리는 처방과 못 살리는 처방이 갈린다. 기준은 8번과 같다 — 열을 건드렸나.**

```text
(나쁨) 열을 바꾼다                      (좋음) 값을 바꾼다
WHERE code = 123                        WHERE code = '000123'
WHERE CAST(code AS SIGNED) = 123        WHERE code = CAST(123 AS CHAR(20))
WHERE substr(code,2)::int = 123
        ↓                                        ↓
  인덱스 버림 · 전부 훑기                  인덱스 그대로
```

순서대로 적으면 이렇다.

1. **먼저 스키마를 의심한다.** 숫자만 담는 열이 `varchar` 라면 진짜 처방은 **열 타입 수정**이다(목록의 42번 주제).\
   질의를 고치는 것은 그 다음이다.
2. **값 쪽을 열의 타입에 맞춘다.** `WHERE code = '000123'`. 애플리케이션에서 문자열로 넘긴다.
3. **열을 꼭 변환해야 한다면 표현식 인덱스를 만든다.** PG 는 `CREATE INDEX ... ON t (substr(code,2))`,\
   MySQL 은 생성 열에 인덱스를 건다(목록의 45번·46번 주제).
4. **MySQL 은 고친 뒤 `EXPLAIN` 과 `SHOW WARNINGS` 를 다시 본다.** `type` 이 `index` → `ref` 로 돌아왔는지,\
   1739 가 사라졌는지가 **고쳐졌다는 유일한 증거**다.

**이식할 때의 순서도 하나 있다.**

```text
MySQL -> PG 로 옮긴다
  1. CAST(... AS SIGNED) 를 전부 찾는다     -> PG 에서 즉시 에러. 안전하다
  2. CAST(... AS CHAR) 를 전부 찾는다       -> ★ 에러가 안 난다. 길이를 확인한다
  3. 문자열 열을 수치와 비교하는 곳을 찾는다  -> PG 에서 에러. 그 에러가 버그 리포트다
```

**2번만 조용하다.** 나머지는 PG 가 문을 세워 주지 않으므로 배포 전에 드러난다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `CAST` 타입 이름 4종 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | `INTEGER`·`SIGNED`·`TEXT`·`CHAR` |
| `CHAR`·`CHAR(n)`·`VARCHAR`·`VARCHAR(n)` (2번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | **한 자리 값과 두 자리 값을 둘 다 던졌다** |
| `::char`·`::varchar`·`::text` (2번) | PG 18.6 | 1회 | 축약도 같은 함정 |
| `LENGTH(CAST(1234567 AS CHAR))` (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG `1` 대 MySQL `7`** — 37번으로 이어진다 |
| `::` 축약 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL `ERROR 1064` 가 근거다** |
| `DECIMAL(10,2)` 캐스트 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 유일하게 같은 이름 |
| `'abc' + 1` · `1 = 'abc'` (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 에러 메시지가 근거다** |
| 경고 1292 (3·10번) | MySQL 8.4.10 | 1회 | `SHOW WARNINGS` |
| `1 + '1'` · `1 = '1'` (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **같은 결과** — 갈리는 것은 실패할 때뿐 |
| `EXPLAIN` 4종 (4·8번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | 20,000행 `t35`, `ANALYZE` 직후 |
| 경고 1739 (4번) | MySQL 8.4.10 | 1회 | `SHOW WARNINGS` |
| `code = 123` 의 행 수 (4번) | MySQL 8.4.10 | 1회 | **0행이 근거다** |
| `TRUE + TRUE` · `CAST(1 AS BOOLEAN)` (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 에러가 근거다** |
| `SHOW CREATE TABLE` 의 `tinyint(1)` (5번) | MySQL 8.4.10 | 1회 | 표는 만들고 **지웠다** |
| `UNION` 타입 결정 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `pg_typeof` · `DESCRIBE` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | MySQL 은 `TEMPORARY` 표 |
| `'10' > '9'` (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **같은 결과** |

**구현 의존 항목** — **`EXPLAIN` 출력 전부**(4·8번).\
계획은 그 순간의 통계·행 수·서버 설정이 정한 것이라 **보장이 아니라 관찰**이다.\
`rows: 19905` 는 추정치이고 실제 행 수는 20,000 이다 — 추정과 실측의 차이는 목록의 **60번 주제**가 다룬다.\
행 수를 줄이면 인덱스가 있어도 순차 스캔이 뽑힐 수 있다.

**언어 보장 항목** — 1·2·3·5·6·7·9번.\
`CAST` 가 받는 타입 이름, 변환 실패 시의 처리, `BOOLEAN` 이 MySQL 에서 `tinyint(1)` 이라는 것,\
`UNION` 의 타입 결정, 같은 타입끼리는 변환이 없다는 것 — 전부 두 매뉴얼의 타입 변환 페이지가 정한 것이다.

**버전을 적지 않은 이유** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 **두 매뉴얼에서도 릴리스 노트에서도 찾지 못했다.**\
목록 README 의 규칙대로, 확인하지 못한 도입 버전은 적지 않았다.

**DB 잔재** — 없다. `t35`·`t35b`·`t35n` 은 실험 후 삭제했고, `emp`·`dept` 는 읽기만 했다.
