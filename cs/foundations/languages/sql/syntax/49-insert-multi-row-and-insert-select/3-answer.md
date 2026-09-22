# sql/49-INSERT — 다중 행·INSERT SELECT·기본값 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **환경** — MySQL 의 `sql_mode` 에 `STRICT_TRANS_TABLES` 가 켜져 있고 `autocommit=1` 이다.\
> 이 편이 만든 표(`t49_a`·`t49_src`·`t49_p`·`t49_c`·`t49_d`·`t49_ai`)는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> 문서 근거는 [PG 18 INSERT](https://www.postgresql.org/docs/18/sql-insert.html) · [MySQL 8.4 INSERT](https://dev.mysql.com/doc/refman/8.4/en/insert.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 안 적은 칸은 무엇이 되나 — **`DEFAULT` 세 칸 + 계산된 `total`**

**출력**

```text
### SQL: INSERT INTO t49_a (id,name) VALUES (1,'ann'),(2,'bob'),(3,'cho');
--- PG 18.6 ---
INSERT 0 3
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT * FROM t49_a ORDER BY id;
--- PG 18.6 ---                              --- MySQL 8.4.10 ---
 id | name | grade | price | qty | total     +----+------+-------+-------+------+-------+
----+------+-------+-------+-----+-------    | id | name | grade | price | qty  | total |
  1 | ann  | B     |   100 |   1 |   100     +----+------+-------+-------+------+-------+
  2 | bob  | B     |   100 |   1 |   100     |  1 | ann  | B     |   100 |    1 |   100 |
  3 | cho  | B     |   100 |   1 |   100     |  2 | bob  | B     |   100 |    1 |   100 |
(3 rows)                                     |  3 | cho  | B     |   100 |    1 |   100 |
                                             +----+------+-------+-------+------+-------+
```

**왜 그런가** — **열 목록에 없는 열 = 「값을 안 준 것**」이다. 엔진이 순서대로 채운다.

```text
열 목록에 있나 -> 예   : 그 값
              -> 아니오: DEFAULT 가 있나 -> 예 : 그 식을 평가한 값 (grade='B', price=100, qty=1)
                                        -> 아니오: 자동 증가가 있나 -> 다음 번호
                                                                  -> 없으면 NULL
                        생성 열이면    : price*qty 를 계산 (100*1 = 100)
```

`DEFAULT` 가 **`CREATE TABLE` 때가 아니라 `INSERT` 때 평가된다**는 것은 [45 번](../45-check-not-null-default-generated-columns/)이 정본이다.

---

### 2. ★★ 부분 실패 — **(b) 하나도 안 남는다. 두 엔진이 같다**

**출력**

```text
### SQL: INSERT INTO t49_a (id,name) VALUES (20,'v20'),(1,'dup'),(21,'v21');
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t49_a_pkey"
DETAIL:  Key (id)=(1) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry '1' for key 't49_a.PRIMARY'
```

★ **에러가 났다는 것만으로 끝내면 안 된다 — 세어서 확인했다.**

```text
### SQL: SELECT id,name FROM t49_a WHERE id IN (20,21) ORDER BY id;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 id | name                 (출력 없음 — 0행)
----+------
(0 rows)

### SQL: SELECT count(*) AS n FROM t49_a;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 n                         +---+
---                        | n |
 7                         +---+
(1 row)                    | 7 |
                           +---+
```

**왜 그런가** — **문 하나가 원자 단위**다. 문이 실패하면 그 문이 만든 변경이 전부 취소된다.

```text
 [20 넣기 시도] -> [1 넣기 시도 -> PK 위반] -> 문 전체 취소
                                              21 은 시도조차 안 한다
```

그래서 **「어디까지 들어갔나」를 물을 필요가 없다.** 같은 문을 그대로 재시도할 수 있다.

★ 단 **이 성질은 「충돌 처리를 안 적었을 때」의 성질**이다. PG 에서 `ON CONFLICT DO NOTHING` 을 붙이면 깨진다.

```text
### SQL: INSERT INTO t49_a (id,name) VALUES (20,'v20'),(1,'dup'),(21,'v21') ON CONFLICT DO NOTHING;
--- PG 18.6 ---
INSERT 0 2
### SQL: SELECT id,name FROM t49_a WHERE id IN (1,20,21) ORDER BY id;
--- PG 18.6 ---
 id | name 
----+------
  1 | ann
 20 | v20
 21 | v21
(3 rows)
```

---

### 3. ★★ `IGNORE` 를 붙이면 — **MySQL 은 2행이 들어간다 / PG 는 문법 오류**

**출력**

```text
### SQL: INSERT IGNORE INTO t49_a (id,name) VALUES (20,'v20'),(1,'dup'),(21,'v21'); SHOW WARNINGS;
--- MySQL 8.4.10 ---
+---------+------+---------------------------------------------+
| Level   | Code | Message                                     |
+---------+------+---------------------------------------------+
| Warning | 1062 | Duplicate entry '1' for key 't49_a.PRIMARY' |
+---------+------+---------------------------------------------+

### SQL: SELECT id,name FROM t49_a WHERE id IN (1,20,21) ORDER BY id;
--- MySQL 8.4.10 ---
+----+------+
| id | name |
+----+------+
|  1 | ann  |
| 20 | v20  |
| 21 | v21  |
+----+------+
```

영향 행 수도 따로 읽었다.

```text
### SQL: INSERT IGNORE INTO t49_a (id,name) VALUES (22,'v22'),(1,'dup'),(23,'v23'); SELECT ROW_COUNT() AS affected;
--- MySQL 8.4.10 ---
+----------+
| affected |
+----------+
|        2 |
+----------+
```

PG 에는 그런 낱말이 없다.

```text
### SQL: INSERT IGNORE INTO t49_a (id,name) VALUES (40,'x');
--- PG 18.6 ---
ERROR:  syntax error at or near "IGNORE"
LINE 1: INSERT IGNORE INTO t49_a (id,name) VALUES (40,'x')
               ^
```

**왜 그런가** — `IGNORE` 는 **무시할 수 있는 에러를 경고로 낮춘다.** 에러가 아니게 되면 문이 안 죽고,\
문이 안 죽으면 **나머지 행이 계속 들어간다.**

```text
2번 (IGNORE 없음)                       3번 (IGNORE 있음)
+----------------------------+          +----------------------------+
| ERROR 1062 — 문이 죽는다   |          | 에러 없음. 경고 1062        |
| 표에 남은 것: 0행          |          | 표에 남은 것: 2행           |
+----------------------------+          +----------------------------+
  -> 호출자가 실패를 안다                  -> ★ 호출자는 성공으로 읽는다
```

★ **정확한 이해** — `IGNORE` 는 「중복을 무시한다」가 아니라 「**이 문의 원자성을 포기한다**」다.\
`SHOW WARNINGS` 를 안 읽으면 **몇 행이 빠졌는지 어디에도 안 남는다.**

---

### 4. ★ `IGNORE` 와 `NOT NULL` — **행이 들어간다. `name` 은 빈 문자열이다**

**출력**

```text
### SQL: INSERT IGNORE INTO t49_a (id) VALUES (30); SHOW WARNINGS;
--- MySQL 8.4.10 ---
+---------+------+-------------------------------------------+
| Level   | Code | Message                                   |
+---------+------+-------------------------------------------+
| Warning | 1364 | Field 'name' doesn't have a default value |
+---------+------+-------------------------------------------+

### SQL: SELECT id, CONCAT('[',name,']') AS name_shown, LENGTH(name) AS len, grade FROM t49_a WHERE id=30;
--- MySQL 8.4.10 ---
+----+------------+-----+-------+
| id | name_shown | len | grade |
+----+------------+-----+-------+
| 30 | []         |   0 | B     |
+----+------------+-----+-------+
```

**왜 그런가** — 8번에서 **에러였던 `1364`** 가 `IGNORE` 때문에 경고로 내려앉았다.\
그리고 엔진은 「가장 가까운 값」으로 칸을 채운다 — 문자열 열이면 **빈 문자열**이다.

```text
NOT NULL 이 막는 것 :  NULL
NOT NULL 이 못 막는 것: ''  (빈 문자열)  <- ★ 여기로 들어왔다
```

★ **불변식은 지켜졌고 데이터는 틀렸다.** `WHERE name IS NULL` 로는 이 행을 찾을 수 없다.\
**이것이 이 편에서 가장 비싼 한 줄이다** — 문은 통과했고, 경고를 안 읽으면 아무 흔적이 없다.

같은 성격의 사고가 [44 번의 `ON DELETE SET DEFAULT`](../44-foreign-key-referential-actions/)와 [45 번의 `serial`](../45-check-not-null-default-generated-columns/)에도 있다.

---

### 5. 생성 열 — **(a) 값을 주면 둘 다 에러 / (b) `DEFAULT` 는 통과, `total` 은 21**

**출력**

```text
### SQL: INSERT INTO t49_a (id,name,total) VALUES (9,'gen',999);
--- PG 18.6 ---
ERROR:  cannot insert a non-DEFAULT value into column "total"
DETAIL:  Column "total" is a generated column.
--- MySQL 8.4.10 ---
ERROR 3105 (HY000) at line 1: The value specified for generated column 'total' in table
  't49_a' is not allowed.

### SQL: INSERT INTO t49_a VALUES (5,'eve',DEFAULT,7,3,DEFAULT);
--- PG 18.6 ---            --- MySQL 8.4.10 ---
INSERT 0 1                 (성공)
```

```text
### SQL: SELECT * FROM t49_a WHERE id IN (4,5) ORDER BY id;
--- PG 18.6 ---
 id | name | grade | price | qty | total 
----+------+-------+-------+-----+-------
  4 | dan  | B     |   100 |   5 |   500
  5 | eve  | B     |     7 |   3 |    21      <- 7 * 3
(2 rows)
```

**왜 그런가** — 생성 열의 값은 **식이 정한다.** 내가 준 `999` 는 그 식과 어긋날 수 있으므로 엔진이 거부한다.\
`DEFAULT` 키워드는 「**계산해 넣어라**」는 뜻이라 허용된다.

[45 번](../45-check-not-null-default-generated-columns/)이 이 결론의 정본이고, **여기서 다시 던져 보니 에러 문구가 한 글자도 같았다.**

---

### 6. 「전부 기본값인 한 행」 — **서로를 정확히 거부한다**

**출력**

```text
### SQL: INSERT INTO t49_d DEFAULT VALUES;
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'DEFAULT VALUES' at line 1

### SQL: INSERT INTO t49_d VALUES ();
--- PG 18.6 ---
ERROR:  syntax error at or near ")"
LINE 1: INSERT INTO t49_d VALUES ()
                                  ^
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT * FROM t49_d;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 id | g                    +------+------+
----+---                   | id   | g    |
  7 | B                    +------+------+
(1 row)                    |    7 | B    |
                           +------+------+
```

**왜 그런가** — 같은 한 행을 만드는 문법이 방언마다 다르다. 결과는 같고 **글자만 다르다.**

MySQL 매뉴얼이 후자를 명시한다.

> "If both the column list and the `VALUES` list are empty, `INSERT` creates a row with each column set to its default value: `INSERT INTO tbl_name () VALUES();`"\
> — [MySQL 8.4 · INSERT Statement](https://dev.mysql.com/doc/refman/8.4/en/insert.html)

**이식 가능한 우회**는 하나다 — 열 하나만 명시해 기본값을 적는다: `INSERT INTO t49_d (id) VALUES (DEFAULT)`.

---

### 7. 값 개수가 모자라면 — **PG 는 통과, MySQL 은 `ERROR 1136`**

**출력**

```text
### SQL: INSERT INTO t49_p VALUES (3);
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
ERROR 1136 (21S01) at line 1: Column count doesn't match value count at row 1

### SQL: SELECT * FROM t49_p ORDER BY id;
--- PG 18.6 ---
 id | name 
----+------
  1 | p1
  2 | p2
  3 |          <- name 이 NULL 이다
(3 rows)
```

반대로 **값이 더 많으면 둘 다 막는다.**

```text
### SQL: INSERT INTO t49_p (id,name) VALUES (3,'p3','extra');
--- PG 18.6 ---
ERROR:  INSERT has more expressions than target columns
LINE 1: INSERT INTO t49_p (id,name) VALUES (3,'p3','extra')
                                                   ^
--- MySQL 8.4.10 ---
ERROR 1136 (21S01) at line 1: Column count doesn't match value count at row 1
```

**왜 그런가** — PG 는 **덜 준 값을 「안 준 것」으로 읽어** 기본값을 채운다. MySQL 은 개수가 정확히 맞기를 요구한다.

★ **PG 쪽이 조용해서 더 위험하다.** 열을 하나 추가한 날, 열 목록 없이 쓰던 `INSERT` 가\
**에러 없이 `NULL` 을 남기기 시작한다.** 처방은 방언과 무관하다 — **열 목록을 항상 적는다.**

---

### 8. `NOT NULL` 을 어기는 두 방법 — **PG 는 같은 에러, MySQL 은 다른 에러**

**출력**

```text
### SQL: INSERT INTO t49_a (id) VALUES (10);
--- PG 18.6 ---
ERROR:  null value in column "name" of relation "t49_a" violates not-null constraint
DETAIL:  Failing row contains (10, null, B, 100, 1, 100).
--- MySQL 8.4.10 ---
ERROR 1364 (HY000) at line 1: Field 'name' doesn't have a default value

### SQL: INSERT INTO t49_a (id,name) VALUES (11,NULL);
--- PG 18.6 ---
ERROR:  null value in column "name" of relation "t49_a" violates not-null constraint
DETAIL:  Failing row contains (11, null, B, 100, 1, 100).
--- MySQL 8.4.10 ---
ERROR 1048 (23000) at line 1: Column 'name' cannot be null
```

**왜 그런가**

```text
            "열을 아예 안 줬다"             "열을 주고 NULL 을 넣었다"
PG 18.6     열이 없으면 NULL 로 채운 뒤     -> 같은 not-null 위반
            not-null 을 검사한다
MySQL       ERROR 1364 (기본값이 없다)      ERROR 1048 (NULL 을 못 넣는다)
            ^^^^^^^^^^ 사건이 다르다
```

★ **`1364` 는 `NOT NULL` 전용 에러가 아니다** — 「기본값이 없는 열에 값을 안 줬다」는 뜻이고,\
4번에서 본 것처럼 `IGNORE` 를 만나면 **경고로 내려앉는다.**

★ **PG 의 `DETAIL` 에 이미 `B, 100, 1, 100` 이 있다.**\
**기본값과 생성 열이 제약 검사보다 먼저 적용됐다**는 뜻이다 — [45 번의 같은 관찰](../45-check-not-null-default-generated-columns/).

---

### 9. ★ 외래키를 어기는 삽입 — **PG 만 막는다. MySQL 은 제약이 없었다**

**출력**

```text
### SQL: INSERT INTO t49_c VALUES (100, 99, 'orphan');
--- PG 18.6 ---
ERROR:  insert or update on table "t49_c" violates foreign key constraint "t49_c_p_id_fkey"
DETAIL:  Key (p_id)=(99) is not present in table "t49_p".
--- MySQL 8.4.10 ---
(성공)
```

★ **통과했으니 몇 행이 들어갔는지 세어야 한다.**

```text
### SQL: INSERT INTO t49_c VALUES (101,1,'ok1'),(102,99,'bad'),(103,2,'ok2');
--- PG 18.6 ---
ERROR:  insert or update on table "t49_c" violates foreign key constraint "t49_c_p_id_fkey"
DETAIL:  Key (p_id)=(99) is not present in table "t49_p".
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT * FROM t49_c ORDER BY id;
--- MySQL 8.4.10 ---
+-----+------+--------+
| id  | p_id | memo   |
+-----+------+--------+
| 100 |   99 | orphan |
| 101 |    1 | ok1    |
| 102 |   99 | bad    |
| 103 |    2 | ok2    |
+-----+------+--------+
```

**왜 그런가** — `INSERT` 문의 문제가 아니라 **`CREATE TABLE` 이 제약을 안 만든 것**이다.

```text
--- MySQL 8.4.10 ---
SHOW CREATE TABLE t49_c\G
Create Table: CREATE TABLE `t49_c` (
  `id` int NOT NULL,
  `p_id` int DEFAULT NULL,
  `memo` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)                 <- ★ FOREIGN KEY 가 없다
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

**MySQL 은 열 뒤 `REFERENCES` 를 파싱하고 무시한다** — [44 번](../44-foreign-key-referential-actions/)이 정본이다.

**표 수준 `FOREIGN KEY` 절로 다시 만들면 두 엔진이 같이 막는다.**

```text
### SQL: INSERT INTO t49_c VALUES (101,1,'ok1'),(102,99,'bad'),(103,2,'ok2');   -- CONSTRAINT t49_c_fk 판
--- PG 18.6 ---
ERROR:  insert or update on table "t49_c" violates foreign key constraint "t49_c_fk"
DETAIL:  Key (p_id)=(99) is not present in table "t49_p".
--- MySQL 8.4.10 ---
ERROR 1452 (23000) at line 1: Cannot add or update a child row: a foreign key constraint fails
  (`study`.`t49_c`, CONSTRAINT `t49_c_fk` FOREIGN KEY (`p_id`) REFERENCES `t49_p` (`id`))

### SQL: SELECT count(*) AS n FROM t49_c;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 n                         +---+
---                        | n |
 0                         +---+
(1 row)                    | 0 |
                           +---+
```

정상 행 둘도 안 들어갔다 — **2번의 원자성이 FK 위반에서도 같다.**

---

### 10. `SELECT` 가 0행이면 — **에러가 아니다. 0행을 넣는다**

**출력**

```text
### SQL: INSERT INTO t49_a (id,name) SELECT id, name FROM t49_src WHERE price > 999;
--- PG 18.6 ---
INSERT 0 0
--- MySQL 8.4.10 ---
(성공 — 0행)
```

**왜 그런가** — `INSERT ... SELECT` 는 **`SELECT` 가 돌려준 행을 넣는다.** 0행이면 0행을 넣는다.\
이것은 **정상 동작**이다.

★ **적재 스크립트가 놓치는 것** — 「에러가 안 났으니 적재됐다」로 읽으면\
**원본 조건이 틀려 하루치가 통째로 안 들어간 사실**을 아무도 모른다.\
**넣은 행 수를 반드시 다시 읽어라** — PG 는 `INSERT 0 0` 문자열, MySQL 은 `ROW_COUNT()` 다.

---

### 11. 자기 표에서 읽어 자기 표에 — **3행이 들어간다**

**출력**

```text
### SQL: INSERT INTO t49_src (id,name,price) SELECT id+100, name, price FROM t49_src;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
INSERT 0 3                 (성공)

### SQL: SELECT * FROM t49_src ORDER BY id;
--- PG 18.6 ---                    --- MySQL 8.4.10 ---
 id  | name  | price               +-----+-------+-------+
-----+-------+-------               | id  | name  | price |
 101 | src-a |    10               +-----+-------+-------+
 102 | src-b |    20               | 101 | src-a |    10 |
 103 | src-c |    30               | 102 | src-b |    20 |
 201 | src-a |    10               | 103 | src-c |    30 |
 202 | src-b |    20               | 201 | src-a |    10 |
 203 | src-c |    30               | 202 | src-b |    20 |
(6 rows)                           | 203 | src-c |    30 |
                                   +-----+-------+-------+
```

**왜 그런가** — **`SELECT` 가 보는 것은 문이 시작될 때의 표**다. 새로 넣은 행이 다시 읽히지 않는다.

```text
문 시작                문이 보는 원본            문이 만드는 것
t49_src = 3행   ->    101,102,103         ->    201,202,203
                      (201~203 은 안 보인다)
```

같은 성질을 [54 번의 변경문 CTE](../54-returning-and-data-modifying-cte/)가 훨씬 극적으로 보인다 —\
**같은 문 안의 다른 조각이 변경 전 스냅숏을 본다.**

---

### 12. `LAST_INSERT_ID()` — **4 다. 마지막이 아니라 「첫」 번호다**

**출력**

```text
### SQL: INSERT INTO t49_ai (v) VALUES ('d'),('e'); SELECT LAST_INSERT_ID() AS last_id;
--- MySQL 8.4.10 ---
+---------+
| last_id |
+---------+
|       4 |
+---------+
```

직전 상태는 이랬다.

```text
### SQL: SELECT * FROM t49_ai ORDER BY id;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 id | v                    +----+------+
----+---                   | id | v    |
  1 | a                    +----+------+
  2 | b                    |  1 | a    |
  3 | c                    |  2 | b    |
(3 rows)                   |  3 | c    |
                           +----+------+
```

**왜 그런가** — `'d'` 가 4, `'e'` 가 5 로 들어갔는데 함수는 **4** 를 돌려줬다.\
이름은 「last」지만 **배치에서 처음 발급된 번호**다.

```text
배치로 넣은 행들의 번호 = LAST_INSERT_ID() 부터 LAST_INSERT_ID() + ROW_COUNT() - 1 까지
                          = 4 부터 4 + 2 - 1 = 5 까지
```

★ **이것은 추정이다.** PG 쪽 대응물인 [`RETURNING`](../54-returning-and-data-modifying-cte/)은 **실제 값을 그대로 돌려준다** —\
`INSERT ... RETURNING id` 하나면 계산이 필요 없다. MySQL 8.4.10 에는 그 절이 없다.

---

### 13. 길이를 넘기면 — **둘 다 막는다. 단 MySQL 은 `sql_mode` 에 달렸다**

**출력**

```text
### SQL: INSERT INTO t49_a (id,name) VALUES (31,'abcdefghijklmno');
--- PG 18.6 ---
ERROR:  value too long for type character varying(10)
--- MySQL 8.4.10 ---
ERROR 1406 (22001) at line 1: Data too long for column 'name' at row 1
```

★ **MySQL 이 막는 근거는 `STRICT_TRANS_TABLES` 다.** 같은 문에 `IGNORE` 만 붙이면 결과가 뒤집힌다.

```text
### SQL: INSERT IGNORE INTO t49_a (id,name) VALUES (31,'abcdefghijklmno'); SHOW WARNINGS;
--- MySQL 8.4.10 ---
+---------+------+-------------------------------------------+
| Level   | Code | Message                                   |
+---------+------+-------------------------------------------+
| Warning | 1265 | Data truncated for column 'name' at row 1 |
+---------+------+-------------------------------------------+

### SQL: SELECT id, name, LENGTH(name) AS len FROM t49_a WHERE id=31;
--- MySQL 8.4.10 ---
+----+------------+-----+
| id | name       | len |
+----+------------+-----+
| 31 | abcdefghij |  10 |
+----+------------+-----+
```

**다섯 글자가 사라졌고 문은 성공했다.**

★ **이 실험에서 `sql_mode` 자체를 꺼 보지는 않았다** — 공유 서버의 설정을 바꾸지 않기 위해서다.\
대신 **같은 결과를 내는 `IGNORE`** 로 「경고로 내려앉으면 무슨 일이 생기나」를 확인했다.\
**근거가 되는 쪽은 `IGNORE` 출력**이고, 「모드를 끄면 평문 `INSERT` 도 이렇게 된다」는 **매뉴얼 근거의 추론**이다.

---

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `sql_mode`·`autocommit` 조회 (머리말) | MySQL 8.4.10 | 1회 | `STRICT_TRANS_TABLES` 확인 |
| 표 6개 생성·삭제 | PG 18.6 · MySQL 8.4.10 | 각 6회 | `t49_a`·`t49_src`·`t49_p`·`t49_c`·`t49_d`·`t49_ai` |
| 다중 행 `VALUES` (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 삽입 + `SELECT` 확인 |
| ★ 부분 실패 원자성 (2번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **에러 + `IN (20,21)` + `count(*)` — 둘 다 0행** |
| `ON CONFLICT DO NOTHING` 부분 삽입 (2번) | PG 18.6 | 2회 | **2행 들어갔다 — 원자성이 깨진다** |
| ★ `INSERT IGNORE` 다중 행 (3번) | MySQL 8.4.10 | 3회 | **`SHOW WARNINGS` + `SELECT` + `ROW_COUNT()`** |
| PG 에 `INSERT IGNORE` (3번) | PG 18.6 | 1회 | `syntax error at or near "IGNORE"` |
| ★ `IGNORE` + `NOT NULL` (4번) | MySQL 8.4.10 | 2회 | **경고 1364 + `LENGTH(name)=0`** |
| 생성 열 직접 대입 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 45번과 **에러 문구가 같았다** |
| 생성 열에 `DEFAULT` (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 삽입 + `total` 값 확인 |
| `DEFAULT VALUES` / `VALUES ()` (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **서로를 거부. 결과 행은 같다** |
| 값 개수 부족·초과 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 는 부족을 통과시킨다** |
| `NOT NULL` 두 형태 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL 만 에러가 둘(1364·1048)** |
| ★ 열 뒤 `REFERENCES` FK (9번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **MySQL 은 제약이 없어 4행이 들어갔다** |
| `SHOW CREATE TABLE` 확인 (9번) | MySQL 8.4.10 | 1회 | **FK 행이 없는 것이 근거다** |
| 표 수준 `FOREIGN KEY` FK (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **둘 다 `ERROR`, 둘 다 0행** |
| `INSERT ... SELECT` (10번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 2행 적재 · 0행 적재 · 결과 확인 |
| 자기 표 삽입 (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **3행 — 새 행을 다시 안 읽는다** |
| `LAST_INSERT_ID()` (12번) | MySQL 8.4.10 | 1회 | **4 — 배치의 첫 번호** |
| 자동 증가 다중 행 (12번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 둘 다 `1,2,3` |
| 길이 초과 (13번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `ERROR 1406` / `value too long` |
| ★ `IGNORE` + 길이 초과 (13번) | MySQL 8.4.10 | 2회 | **경고 1265 + 10자로 잘림** |

**구현 의존 항목** — 2·8·9·13번의 **에러 코드·문구**, 6·7번의 **문법 수용 여부**, 3·4·13번의 **`IGNORE` 가 삼키는 범위**.\
외울 것은 문구가 아니라 **「문 하나가 원자 단위다」**·「**`IGNORE` 는 그 단위를 포기한다**」는 성질이다.

**언어 보장 항목** — 1·2·5·10·11번.\
기본값이 `INSERT` 때 채워지는 것, 실패한 문의 변경이 취소되는 것, 생성 열에 대입할 수 없는 것,\
`SELECT` 가 문 시작 시점의 표를 보는 것은 두 매뉴얼이 정한 것이다.

**버전을 적은 자리** — 없다. 이 편의 문법은 두 엔진 모두 오래전부터 있는 것이고,\
**매뉴얼에 도입 버전이 없어 적지 않았다**(목록 README 의 규칙).\
**버전을 못 적은 자리** — `IGNORE` 의 동작 범위가 8.x 안에서 바뀌었는지는 확인하지 못했다.

**돌려 보지 않은 것** — ① `sql_mode` 에서 `STRICT_TRANS_TABLES` 를 **끄고** 평문 `INSERT` 의 잘림을 보는 것(공유 서버 설정을 바꾸지 않기 위해 생략했고, 같은 결과를 `IGNORE` 로 확인했다) ② **동시 세션**에서 자동 증가 번호가 연속인지(세션 하나로만 확인했다) ③ PG 의 `OVERRIDING SYSTEM VALUE`.

**DB 잔재** — 없다. `t49_` 로 시작하는 표를 두 엔진에서 전부 삭제했고 `emp`·`dept` 는 **읽지도 쓰지도 않았다.**\
두 엔진의 최종 표 목록은 [54 편의 「실행 검증」](../54-returning-and-data-modifying-cte/3-answer.md)에 있다.
