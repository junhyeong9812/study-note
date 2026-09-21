# sql/38-패턴 매칭 (LIKE·ESCAPE·정규식) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·계획은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **환경 조건** — PG 데이터베이스 collate = **`en_US.utf8`**(libc 제공자, 결정적) · MySQL 기본 collation = **`utf8mb4_0900_ai_ci`**.\
> 이 설정이 1·3·4번의 답과 5번의 PG 계획을 정한다. 확인 방법은 [39 collation](../39-collation/)에 있다.\
> 인덱스 실험용 표 `t38`(20,000행)은 두 엔진에 같은 모양으로 만들었다가 **작업 후 지웠다.** `emp`·`dept` 는 읽기만 했다.\
> 문서 근거는 [PG 18 Pattern Matching](https://www.postgresql.org/docs/18/functions-matching.html) · [PG 18 Operator Classes](https://www.postgresql.org/docs/18/indexes-opclass.html) · [MySQL 8.4 String Comparison](https://dev.mysql.com/doc/refman/8.4/en/string-comparison-functions.html) · [MySQL 8.4 Regular Expressions](https://dev.mysql.com/doc/refman/8.4/en/regexp.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 와일드카드 넷 — **앞의 셋은 같고 `d` 만 갈린다**

**출력**

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

**왜 그런가**

```text
a: 'a%'   a 로 시작하면 뒤는 아무거나          -> 'abc' 는 참
b: '_b_'  정확히 세 글자이고 가운데가 b        -> 'abc' 는 참
c: '%'    0글자 이상 아무거나                  -> 무엇이든 참 (빈 문자열도)
d: 'A%'   대문자 A 로 시작                     -> ★ 여기서 갈린다
```

```text
d 가 갈리는 이유
PG   : DB collate 가 en_US.utf8 이고 결정적이다 -> 'a' 와 'A' 는 다른 값 -> 거짓
MySQL: 기본 collation 이 utf8mb4_0900_ai_ci     -> ci = 대소문자 무시   -> 참
```

**`LIKE` 라는 연산자가 갈린 게 아니다.** 갈린 것은 **글자 둘이 같은지 판정하는 규칙**이다.\
그래서 이 차이는 `=`·`ORDER BY`·`REGEXP_LIKE` 에도 똑같이 나타난다(39번).

`NULL` 은 6번에서 따로 본다.

---

### 2. ★ `ESCAPE` — **두 엔진에서 같게 동작한다**

**출력 — `ESCAPE` 없이**

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

**출력 — `ESCAPE '!'` 로**

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

**왜 그런가**

```text
(전) LIKE '100%'                    (후) LIKE '100!%' ESCAPE '!'
패턴을 이렇게 읽는다                 패턴을 이렇게 읽는다
  1 0 0 [아무거나]                     1 0 0 %
                                            ^ 글자로서의 %
       ↓                                    ↓
'100%' 잡힌다  ✓                     '100%' 잡힌다  ✓
'1000' 잡힌다  ✗ 원치 않음            '1000' 안 잡힌다 ✓
```

**`b` 가 참에서 거짓으로 바뀐 것**이 `ESCAPE` 가 한 일의 전부다.\
그리고 **네 값 모두 두 엔진이 같다** — `ESCAPE` 는 방언이 아니다.

역슬래시가 기본 이스케이프인 것도 양쪽 공통이다.

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

**`should_be_false` 가 거짓인 것이 근거다.** 이스케이프가 안 됐다면 `_` 가 「아무 한 글자」라 `'axb'` 가 잡혔을 것이다.

---

### 3. 정규식 연산자 — **둘은 서로 없고, 하나는 이름이 같은데 답이 다르다**

**출력 (a) — PG 전용 `~`**

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

**출력 (b) — MySQL 전용 `REGEXP`/`RLIKE`**

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

**출력 (c) — ★ 양쪽에 있는 `REGEXP_LIKE`**

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

**왜 그런가**

```text
(a)(b)  연산자가 서로의 파서에 없다 -> 구문 오류
        ★ 시끄럽다. 이식하면 배포 전에 터진다

(c)     함수 이름도 인자도 같다 -> 둘 다 돈다
        '^A' 는 "대문자 A 로 시작" 인데
          PG    : 'a' != 'A'  -> f
          MySQL : 'a' == 'A'  -> 1     (기본 collation 이 대소문자를 무시)
        ★ 조용하다. 아무 표시 없이 답만 다르다
```

`REGEXP_REPLACE` 는 **두 엔진이 같은 답**을 냈다 — `'abc-N'`.\
갈리는 것은 **일치 판정**이지 치환 자체가 아니다.

**MySQL 의 `RLIKE '^A'` 가 `1` 인 것**도 같은 이유다. `~*`(PG 의 대소문자 무시 연산자)를 쓴 게 아닌데도 참이다.

---

### 4. ★ 대소문자 무시 — **기본값이 정반대다**

**출력 (a) — `ILIKE`**

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

**출력 (b) — `COLLATE`**

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

**왜 그런가**

```text
(A) PostgreSQL                          (B) MySQL
기본: 대소문자를 구분한다                 기본: 대소문자를 무시한다
  'abc' LIKE 'A%'  -> f                    'abc' LIKE 'A%'  -> 1
       ↓                                        ↓
무시하고 싶으면 ILIKE 를 쓴다             구분하고 싶으면 COLLATE 로 바꾼다
  'abc' ILIKE 'A%' -> t                    ... COLLATE utf8mb4_0900_as_cs -> 0
                                                        ^^^^^
                                                 as = accent sensitive
                                                 cs = case sensitive
```

**두 에러가 대칭이다.** PG 에는 MySQL 의 collation 이름이 없고, MySQL 에는 `ILIKE` 가 없다.\
둘 다 **구문/이름 오류라 시끄럽다** — 이식에서 조용히 지나가지 않는다.

**실무에서 물리는 것은 반대 방향이다.**

```sql
-- PG 습관을 MySQL 로 가져가면
WHERE UPPER(name) LIKE UPPER('ann%')
```

- MySQL 에서 **아무것도 안 바꾼다** — 이미 무시하고 있었다.
- 그런데 **열에 함수를 씌웠으므로 인덱스를 잃는다**(35번 8번 · 37번 11번).
- **에러도 경고도 없다.** 느려질 뿐이다.

---

### 5. ★ 인덱스 — **앞이 고정됐나, 그리고 collation 이 맞나**

**출력 — MySQL (교과서대로다)**

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

**출력 — PG (예상과 다르다)**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t38 WHERE code LIKE 'C00012%';
                 QUERY PLAN                  
---------------------------------------------
 Seq Scan on t38
   Filter: ((code)::text ~~ 'C00012%'::text)
(2 rows)

EXPLAIN (COSTS OFF) SELECT * FROM t38 WHERE code LIKE '%00123';
                 QUERY PLAN                 
--------------------------------------------
 Seq Scan on t38
   Filter: ((code)::text ~~ '%00123'::text)
(2 rows)
```

**왜 그런가**

```text
인덱스는 code 값의 정렬이다

  C000001
  ...        LIKE 'C00012%'  -> "C00012 로 시작" 은 정렬의 연속 구간   -> 좁힐 수 있다
  C000123
  ...        LIKE '%00123'   -> "끝이 00123" 은 정렬 전체에 흩어져 있다 -> 못 좁힌다
  C020000
```

MySQL 은 이 규칙대로 갈렸다.

```text
                앞이 고정   앞이 열림
type            range       index      <- 구간 탐색 -> 전부 훑기
possible_keys   인덱스      NULL       <- 후보에서 아예 빠졌다
rows            10          20418
```

**PG 가 앞이 고정된 패턴에서도 버린 이유는 collation 이다.**\
이 DB 의 collate 는 `en_US.utf8` 이고, 그런 collation 의 정렬 순서는 **바이트 순서와 다르다.**\
`LIKE` 의 접두사 판정은 바이트 기준이라, PG 는 「이 인덱스로는 범위를 못 만든다」고 보고 포기한다.

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

**`Index Cond` 를 읽어라.** PG 가 `LIKE 'C00012%'` 를 **범위 조건 둘**로 바꿨다.

```text
LIKE 'C00012%'
      ↓ 변환
code >= 'C00012'  AND  code < 'C00013'
                              ^^^^^^^
                     마지막 글자를 하나 올린 값이 상한이다
```

`~>=~`·`~<~` 는 **바이트 순서 비교 연산자**다. 일반 `>=`·`<` 와 다른 기호를 쓰는 것이 그 증거다.

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

**이것이 두 엔진 공통의 한계다.**

---

### 6. `NULL LIKE 'a%'` — **참도 거짓도 아니다**

**출력**

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

(psql 은 `NULL` 을 빈 칸으로 그린다.)

**왜 그런가**

```text
NULL 은 "모르는 값" 이다
  모르는 값이 'a' 로 시작하는지?  -> 모른다 -> UNKNOWN(NULL)
  'abc' 가 모르는 패턴에 맞는지?  -> 모른다 -> UNKNOWN(NULL)
```

**`NOT LIKE` 로 뒤집어도 안 잡힌다.**

```text
WHERE code LIKE 'a%'       -> NULL 행은 UNKNOWN -> WHERE 가 버린다
WHERE code NOT LIKE 'a%'   -> NOT UNKNOWN = UNKNOWN -> 여전히 버린다
                                  ↑
                        "뒤집으면 나머지 전부" 가 성립하지 않는다
```

그래서 「`'a'` 로 시작하지 않는 행 전부」를 원하면 이렇게 쓴다.

```sql
WHERE code NOT LIKE 'a%' OR code IS NULL
```

3값 논리의 정본은 [04 NULL 의 3값 논리](../04-null-three-valued-logic/)다.\
이 주제에서 기억할 것은 **`LIKE` 의 결과가 불리언 둘이 아니라 셋**이라는 것 하나다.

---

### 7. 정규식으로 접두사를 찾으면 — **양쪽 다 못 탄다**

**출력**

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

**왜 그런가**

```text
사람 눈           옵티마이저
'^C00012'   ->   "정규식이다"
   ↑              ↓
접두사로 보인다   임의의 정규식에서 안전하게 접두사를 뽑는 것은 어렵고,
                  틀리면 행을 빠뜨린다 -> 보수적으로 포기한다
```

**MySQL 의 `possible_keys: NULL` 이 결정적 근거다.** 「쓸 수 있는 인덱스가 없다」고 판단한 것이다.\
5번의 `LIKE 'C00012%'` 에서는 같은 칸이 `t38_code_idx` 였다 — **같은 표, 같은 인덱스, 같은 의미의 조건인데 갈렸다.**

**처방** — 접두사면 `LIKE 'C00012%'` 로 쓴다. 정규식은 `%`·`_` 로 표현이 안 될 때만 쓴다.

---

### 8. PG 가 기본 인덱스를 버린 이유 — **정렬 기준이 다르기 때문**

**한 줄로** — 인덱스는 **`en_US.utf8` 순서**로 정렬돼 있고, `LIKE` 접두사 판정은 **바이트 순서**를 요구한다.

```text
LIKE 'C00012%' 를 범위로 바꾸려면
  "code >= 'C00012' 이고 code < 'C00013' 인 것만 보면 된다"
   가 참이어야 한다.
        ↓
  이 명제는 인덱스가 바이트 순서로 정렬돼 있을 때만 성립한다.
        ↓
  en_US.utf8 같은 collation 은 구두점을 무시하는 등
  바이트와 다른 순서를 쓴다 -> 명제가 안 성립한다 -> 인덱스를 못 쓴다
```

39번에서 실측한 정렬이 그 증거다.

```text
--- PG 18.6, 기본 collation(en_US.utf8) ---
 apple / apricot / Banana / BANANA / _x / Zebra     <- '_x' 가 'x' 자리로 갔다

--- PG 18.6, COLLATE "C" ---
 BANANA / Banana / Zebra / _x / apple / apricot     <- 바이트 순서
```

두 순서가 **완전히 다르다.** 그래서 한쪽 순서로 만든 인덱스로 다른 쪽 판정을 할 수 없다.

**그리고 이 설명이 맞다는 증거는 같은 문서 안에 있다.**

```text
--- PG 18.6 ---
CREATE INDEX t38_code_pat_idx ON t38 (code varchar_pattern_ops);
EXPLAIN (COSTS OFF) SELECT * FROM t38 WHERE code LIKE 'C00012%';
 Index Scan using t38_code_pat_idx on t38
   Index Cond: (((code)::text ~>=~ 'C00012'::text) AND ((code)::text ~<~ 'C00013'::text))
```

**바이트 순서로 정렬한 인덱스를 주자 바로 탔다.** 반증 가능한 설명이고, 반증되지 않았다.

**MySQL 은 왜 이 문제가 없나** — 인덱스 정렬과 `LIKE` 비교가 **같은 collation** 을 쓰기 때문이다.\
대신 **collation 을 바꾸면 인덱스를 잃는다.** 39번에서 경고 1739 로 확인한다. **대칭인 대가다.**

---

### 9. 역슬래시가 되는데도 `ESCAPE` 를 명시하는 이유

**역슬래시는 두 군데에서 해석된다.**

```text
내가 쓰고 싶은 패턴:  100 다음에 진짜 % 한 글자

애플리케이션 문자열 리터럴  ->  "100\\%"   (언어의 이스케이프)
        ↓
SQL 문자열 리터럴          ->  '100\%'    (SQL 의 이스케이프)
        ↓
LIKE 패턴                  ->  100 + 글자로서의 %
```

**층이 둘 이상이면 역슬래시 개수를 추적해야 한다.** 그리고 층은 더 늘어난다 —\
쉘, 설정 파일, ORM, 로그. 어디서 하나가 먹히면 **패턴이 조용히 달라진다.**

`ESCAPE` 를 명시하면 그 사슬에서 빠져나온다.

```sql
-- 쓰지 않는 문자를 이스케이프로 지정한다
WHERE code LIKE :pattern ESCAPE '!'
```

**그리고 입력 치환도 같이 해야 한다.**

```text
사용자가 입력한 것        패턴에 넣기 전에
  %      ->  !%
  _      ->  !_
  !      ->  !!      <- 이스케이프 문자 자신을 먼저 치환한다 (순서가 중요하다)
```

**`!` 를 먼저 치환해야 한다.** 나중에 하면 앞서 만든 `!%` 의 `!` 까지 다시 치환된다.

**이것을 안 하면** 사용자가 `%` 하나만 입력해도 **표 전체가 잡힌다.**\
2번에서 본 `'1000' LIKE '100%'` 가 참이었던 것이 바로 그 현상이다.

---

### 10. 이식할 때 조용한 자리 — **대소문자 판정 전부**

| 옮기면 | 무슨 일이 | 조용한가 |
|---|---|---|
| `ILIKE` → MySQL | `ERROR 1064` | 시끄럽다 |
| `~` / `~*` → MySQL | `ERROR 1064` | 시끄럽다 |
| `REGEXP` / `RLIKE` → PG | `syntax error at or near` | 시끄럽다 |
| `COLLATE utf8mb4_...` → PG | `collation ... does not exist` | 시끄럽다 |
| **`LIKE 'A%'`** | **PG 거짓 / MySQL 참** | **★ 조용하다** |
| **`REGEXP_LIKE(x,'^A')`** | **PG `f` / MySQL `1`** | **★ 조용하다** |
| **`LIKE 'abc%'` 의 인덱스 사용** | **MySQL `range` / PG `Seq Scan`** | **★ 조용하다 — 느려질 뿐** |

```text
시끄러운 것 4개: 전부 "연산자·이름이 없다" 류 -> 파서가 잡는다
조용한 것 3개:  전부 "collation 이 정하는 것" -> 아무도 안 잡는다
```

**찾는 방법**

1. **대소문자가 섞인 데이터가 있는 열**을 먼저 센다. 거기 걸린 `LIKE`·`REGEXP_LIKE` 가 전부 대상이다.
2. **두 엔진에 같은 질의를 던져 행 수를 대조한다.** 개수가 다르면 그 자리다.
3. **PG 로 옮겼으면 `EXPLAIN` 을 전부 다시 본다.** `Seq Scan` 이 늘었으면 `varchar_pattern_ops` 인덱스를 고려한다.

---

### 11. 검색 기능을 어떻게 만드나

**`LIKE` 로 해결되는 것과 안 되는 것이 갈린다.**

```text
해결된다                                 해결 안 된다
────────                                 ───────────
접두사 검색  code LIKE 'ABC%'            부분 문자열  LIKE '%키워드%'
  -> 인덱스로 좁힌다                        -> 표 전체를 읽는다. 행 수에 비례해 느려진다
  -> PG 는 varchar_pattern_ops 필요

정확한 코드 조회  code = 'ABC123'        단어 단위·형태소·순위
  -> 그냥 인덱스                            -> LIKE 로 표현할 수 없다

패턴이 고정된 형식 검증                   오타 허용·유사도
  -> REGEXP / ~ (느리지만 정확하다)         -> LIKE 의 영역이 아니다
```

**순서대로 정하면 이렇다.**

1. **접두사로 충분한가?** 충분하면 `LIKE 'x%'` + 인덱스로 끝난다. **가장 싸다.**
2. **부분 문자열이 꼭 필요한가?** 그렇다면 `LIKE '%x%'` 는 **임시방편**임을 인정하고 시작한다.\
   행이 적을 때는 돈다. 늘면 안 돈다. **언제 안 돌지를 미리 정해 둔다.**
3. **본격 검색이면 색인을 따로 만든다.** 구조와 비용은 [`data-structure/32-inverted-index`](../../../../../data-structure/32-inverted-index/)가 정본이다.
4. **입력 치환과 `ESCAPE` 는 어느 경우에나 한다**(9번). 이건 성능이 아니라 **정확성** 문제다.

**같이 정할 것 둘.**

- **대소문자를 어떻게 다룰 것인가.** 엔진 기본값에 맡기면 이식할 때 4번·10번의 사고가 난다.\
  요구사항이 「무시」면 **열의 collation 으로 못 박는 편**이 낫다(39번). 함수로 하면 인덱스를 잃는다.
- **`NULL` 을 어떻게 다룰 것인가.** 6번에서 본 대로 `LIKE` 에도 `NOT LIKE` 에도 안 걸린다.\
  「미입력」을 `NULL` 로 둘지 `''` 로 둘지는 **스키마 설계 결정**이다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 와일드카드 4식 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `'A%'` 만 갈렸다 |
| `%` 를 글자로 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `ESCAPE` 유무 대비 |
| 역슬래시 이스케이프 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `%` 와 `_` 각각 |
| `ESCAPE '#'` (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 동일** |
| `~` / `~*` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL `ERROR 1064` 가 근거다** |
| `REGEXP` / `RLIKE` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 구문 오류가 근거다** |
| `REGEXP_LIKE`·`REGEXP_REPLACE` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **이름이 같고 답이 다른 자리** |
| `ILIKE` (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL `ERROR 1064` 가 근거다** |
| `COLLATE ... as_cs` (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 의 collation 없음 에러가 근거다** |
| `LIKE` 접두사·후위 `EXPLAIN` (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 20,000행 `t38`, `ANALYZE` 직후 |
| `varchar_pattern_ops` 인덱스 (5·8번) | PG 18.6 | 2회 | **인덱스 추가 전후를 둘 다 실었다** |
| `NULL LIKE` (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 동일** |
| 정규식 `EXPLAIN` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`possible_keys: NULL` 이 근거다** |
| collation 별 `ORDER BY` (8번) | PG 18.6 | 2회 | 39번에서 쓴 것과 같은 실측 |

**collation 의존 항목** — 1번의 `d` · 3번의 (c) · 4번 전부 · 5번의 PG 계획 · 8번.\
**이 주제의 절반이 여기 걸려 있다.** 머리말의 환경(PG `en_US.utf8` / MySQL `utf8mb4_0900_ai_ci`)에서 나온 결과이고,\
설정이 다르면 **같은 엔진에서도 답이 달라진다.** 확인 방법과 정본은 [39 collation](../39-collation/)이다.

**옵티마이저 의존 항목** — 5·7번의 `EXPLAIN` 출력 전부.\
계획은 통계·행 수·서버 설정이 정하는 **관찰**이지 보장이 아니다. `rows: 20418` 은 추정치이고 실제는 20,000 이다.\
행 수를 줄이면 인덱스가 있어도 순차 스캔이 뽑힐 수 있다.

**언어 보장 항목** — 2번(`ESCAPE` 의 동작) · 3번의 (a)(b)(연산자의 소속) · 6번(`NULL` 의 결과).\
두 매뉴얼의 패턴 매칭 페이지가 정한 것이다.

**「PG 가 인덱스를 못 탔다」를 보장으로 읽지 않는다** — 관찰이다.\
다만 `varchar_pattern_ops` 인덱스를 주자 바로 탔으므로, **원인이 collation 이라는 설명은 같은 문서 안에서 검증됐다**(8번).

**버전을 적지 않은 이유** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 **두 매뉴얼에서도 릴리스 노트에서도 찾지 못했다.**

**DB 잔재** — 없다. `t38`(과 그 인덱스 둘)은 두 엔진에서 **작업 후 삭제**했고, `emp`·`dept` 는 읽기만 했다.
