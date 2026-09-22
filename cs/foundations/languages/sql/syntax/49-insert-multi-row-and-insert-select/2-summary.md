# sql/49-INSERT — 다중 행·INSERT SELECT·기본값 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · INSERT](https://www.postgresql.org/docs/18/sql-insert.html) · [MySQL 8.4 · INSERT Statement](https://dev.mysql.com/doc/refman/8.4/en/insert.html) · [MySQL 8.4 · INSERT ... SELECT](https://dev.mysql.com/doc/refman/8.4/en/insert-select.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **환경 확인** — MySQL 의 `sql_mode` 는 `ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION` 이고 `autocommit=1` 이다.\
> **`STRICT_TRANS_TABLES` 가 꺼지면 7번 절의 결론이 통째로 달라지므로** 먼저 밝힌다.\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 `t49_a`·`t49_src`·`t49_p`·`t49_c`·`t49_d`·`t49_ai` 를 만들었고 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> **선행** — [45 CHECK·NOT NULL·DEFAULT·생성 열·자동 증가](../45-check-not-null-default-generated-columns/)가 **기본값과 생성 열의 정본**이다. 여기서는 그것이 `INSERT` 문에서 어떻게 나타나나만 쓴다.\
> **이어지는 것** — [50 UPDATE](../50-update-with-join-and-subquery/) · [52 UPSERT](../52-upsert/) · [54 RETURNING](../54-returning-and-data-modifying-cte/).

## 한눈에 — 쉽게 말하면

**`INSERT` 는 「행을 만들어 넣는 문」이지만, 값의 출처가 셋이다.**

```text
        값을 어디서 가져오나
────────────────────────────────────────────────
VALUES 목록     내가 문장에 직접 적는다
SELECT 결과     다른 질의가 만든 행을 그대로 붓는다
★ 엔진          내가 안 적은 자리를 엔진이 채운다 (DEFAULT · 자동 증가 · 생성 열)
```

일상 비유로 바꾸면 **창구에 내는 신청서**다.

```text
칸을 손으로 채워 내는 것          = VALUES (1,'ann')
명부를 복사해 그대로 제출하는 것   = INSERT ... SELECT
안 쓴 칸을 직원이 채워 주는 것     = DEFAULT
접수 번호 칸 (내가 쓰면 안 된다)   = 자동 증가 · 생성 열
```

"똑같은 구조다" — 그래서 **내가 적지 않은 칸에 무엇이 들어갔는지 모르면 `INSERT` 를 모른 것**이다.

| 비유 | 실체 |
|---|---|
| 손으로 채운 칸 | `VALUES` 목록의 값 |
| 명부 복사 제출 | `INSERT ... SELECT` |
| 직원이 채우는 칸 | `DEFAULT` · 자동 증가 |
| ★ 내가 쓰면 반려되는 칸 | **생성 열** — 값을 주면 에러다 |
| ★ 서류 한 장이라도 틀리면 **전부 반려** | 다중 행 `INSERT` 의 원자성 |
| ★ 「틀린 건 빼고 접수해 주세요」 | **MySQL 의 `IGNORE`** — 여기서 사고가 난다 |

★ **이 편에서 가장 값비싼 한 줄** — **`INSERT` 한 문은 전부 들어가거나 하나도 안 들어간다.**\
그런데 **MySQL 의 `INSERT IGNORE` 가 그 성질을 깬다** — 세 행 중 두 행만 들어가고, 에러 대신 경고만 남는다(7번).

## 이 주제가 답하려는 질문

1. **여러 행 중 하나가 실패하면 앞의 것이 남나?** — 원자성이 문 단위인가 행 단위인가.
2. **내가 안 적은 자리는 언제 무엇으로 채워지나?** — `DEFAULT` 키워드·생략·생성 열이 각각 다른가.
3. **`INSERT` 를 막는 것은 무엇인가?** — `NOT NULL`·FK·타입·길이 중 어디서 어떤 에러가 나나.

## 예시 데이터 — 이 편이 만든 표

`emp`·`dept` 는 **한 줄도 쓰지 않았다.** 이 편은 자기 표를 만들어 쓰고 지운다.

```text
t49_a  (INSERT 대상 — 값의 출처 네 가지를 한 표에 모았다)
+-------+---------------------------------------+
| id    | int PRIMARY KEY                       |  내가 적는다
| name  | varchar(10) NOT NULL                  |  내가 적어야만 한다
| grade | varchar(5)  DEFAULT 'B'               |  안 적으면 'B'
| price | int         DEFAULT 100               |  안 적으면 100
| qty   | int         DEFAULT 1                 |  안 적으면 1
| total | GENERATED ALWAYS AS (price*qty) STORED|  ★ 적으면 에러
+-------+---------------------------------------+

t49_src (INSERT ... SELECT 의 원본)       t49_p / t49_c (FK 실험)
+-----+-------+-------+                   t49_p(id PK, name)
| id  | name  | price |                   t49_c(id PK, p_id -> t49_p.id, memo)
+-----+-------+-------+
| 101 | src-a |    10 |
| 102 | src-b |    20 |
| 103 | src-c |    30 |
+-----+-------+-------+
```

두 엔진에서 **같은 `CREATE TABLE` 문이 그대로 통과**했다.

```sql
CREATE TABLE t49_a (id int PRIMARY KEY, name varchar(10) NOT NULL,
                    grade varchar(5) DEFAULT 'B', price int DEFAULT 100, qty int DEFAULT 1,
                    total int GENERATED ALWAYS AS (price*qty) STORED);
CREATE TABLE t49_src (id int PRIMARY KEY, name varchar(10), price int);
```

## 동작 방식

### 1. 한 문으로 여러 행 — `VALUES` 목록

**언제 쓰나** — 행 여러 개를 넣을 때. **행마다 문을 나누면 왕복이 행 수만큼 늘어난다.**

```text
INSERT INTO t49_a (id,name) VALUES (1,'ann'),(2,'bob'),(3,'cho');
                                    ^^^^^^^^  ^^^^^^^^  ^^^^^^^^
                                    괄호 하나 = 행 하나. 쉼표로 잇는다

(전) t49_a        비어 있다
   ↓  한 문
(후) t49_a
+----+------+-------+-------+-----+-------+
| id | name | grade | price | qty | total |
+----+------+-------+-------+-----+-------+
|  1 | ann  | B     |   100 |   1 |   100 |   <- 적지 않은 네 칸이 채워졌다
|  2 | bob  | B     |   100 |   1 |   100 |
|  3 | cho  | B     |   100 |   1 |   100 |
+----+------+-------+-------+-----+-------+
```

```text
### SQL: INSERT INTO t49_a (id,name) VALUES (1,'ann'),(2,'bob'),(3,'cho');
--- PG 18.6 ---
INSERT 0 3
--- MySQL 8.4.10 ---
(성공 — 배치 모드에서는 출력이 없다)
```

```text
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

그림 해설 — **열 목록에 없는 열은 「안 준 것」으로 처리**돼 `DEFAULT` 가 적용됐다(3번).\
비용 — 왕복이 1회로 줄고, 엔진 안에서도 한 번의 제약 검사 경로를 탄다. **다만 행 하나가 틀리면 전부 반려된다**(2번).

> **다중 행 `VALUES`(multi-row VALUES)** — 한 `INSERT` 문의 `VALUES` 뒤에 괄호 묶음을 여럿 나열하는 형태.\
> 예: `VALUES (1,'ann'),(2,'bob')` 은 두 행을 한 문으로 넣는다.

### 2. ★★ 부분 실패 — **앞의 행이 남나**

**언제 쓰나** — 배치 적재를 설계할 때. **「어디까지 들어갔지?」를 물어야 하는지 아닌지가 여기서 갈린다.**

세 행 중 **가운데 행만** 기본키를 어기게 만들어 던졌다.

```text
INSERT INTO t49_a (id,name) VALUES (20,'v20'), (1,'dup'), (21,'v21');
                                    ^^^^^^^^^   ^^^^^^^    ^^^^^^^^^
                                    새 키        ★ 중복      새 키
```

```text
### SQL: INSERT INTO t49_a (id,name) VALUES (20,'v20'),(1,'dup'),(21,'v21');
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t49_a_pkey"
DETAIL:  Key (id)=(1) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry '1' for key 't49_a.PRIMARY'
```

★ **에러가 났다는 것만으로는 부족하다 — 몇 행이 남았는지 세어야 한다.**

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

두 그림의 결론 — **20 도 21 도 안 들어갔다. 두 엔진이 같다.**

```text
문 하나 = 원자 단위

  [20 넣기] [1 넣기 -> 위반] [21 넣기]
      ↓          ↓
   다 되돌린다 <──┘         21 은 시도조차 안 한다
```

비용 — 「어디까지 들어갔나」를 물을 필요가 없다. **재시도가 안전하다.**\
★ 이 성질은 **행 단위 처리에 비해 비싼 대신 정확**하다 — 5만 행 중 하나가 틀리면 5만 행이 되돌아간다.

★ **그런데 두 엔진 다 이 성질을 깨는 손잡이가 있다.** PG 는 [`ON CONFLICT DO NOTHING`](../52-upsert/), MySQL 은 `INSERT IGNORE` 다(7번).

```text
### SQL: INSERT INTO t49_a (id,name) VALUES (20,'v20'),(1,'dup'),(21,'v21') ON CONFLICT DO NOTHING;
--- PG 18.6 ---
INSERT 0 2                  <- ★ 3행을 시도해 2행이 들어갔다
### SQL: SELECT id,name FROM t49_a WHERE id IN (1,20,21) ORDER BY id;
--- PG 18.6 ---
 id | name 
----+------
  1 | ann
 20 | v20                   <- 들어갔다
 21 | v21                   <- 들어갔다
(3 rows)
```

**「원자성」은 `INSERT` 의 성질이 아니라 「충돌 처리를 안 적었을 때」의 성질이다.**

### 3. 값을 안 준 자리 — `DEFAULT` 를 적는 세 가지 방법

**언제 쓰나** — 열 일부만 줄 때. 세 방법이 **같은 결과**를 낸다.

```text
(a) 열 목록에서 뺀다            INSERT INTO t49_a (id,name) VALUES (4,'dan')
(b) DEFAULT 키워드를 적는다     INSERT INTO t49_a (id,name,grade) VALUES (4,'dan',DEFAULT)
(c) 전체 열에 DEFAULT 를 섞는다 INSERT INTO t49_a VALUES (5,'eve',DEFAULT,7,3,DEFAULT)
```

```text
### SQL: INSERT INTO t49_a (id,name,grade,price,qty) VALUES (4,'dan',DEFAULT,DEFAULT,5);
--- PG 18.6 ---            --- MySQL 8.4.10 ---
INSERT 0 1                 (성공)

### SQL: INSERT INTO t49_a VALUES (5,'eve',DEFAULT,7,3,DEFAULT);
--- PG 18.6 ---            --- MySQL 8.4.10 ---
INSERT 0 1                 (성공)
```

```text
### SQL: SELECT * FROM t49_a ORDER BY id;
--- PG 18.6 ---                              --- MySQL 8.4.10 ---
 id | name | grade | price | qty | total     +----+------+-------+-------+------+-------+
----+------+-------+-------+-----+-------    | id | name | grade | price | qty  | total |
  1 | ann  | B     |   100 |   1 |   100     +----+------+-------+-------+------+-------+
  2 | bob  | B     |   100 |   1 |   100     |  1 | ann  | B     |   100 |    1 |   100 |
  3 | cho  | B     |   100 |   1 |   100     |  2 | bob  | B     |   100 |    1 |   100 |
  4 | dan  | B     |   100 |   5 |   500     |  3 | cho  | B     |   100 |    1 |   100 |
  5 | eve  | B     |     7 |   3 |    21     |  4 | dan  | B     |   100 |    5 |   500 |
(5 rows)                                     |  5 | eve  | B     |     7 |    3 |    21 |
                                             +----+------+-------+-------+------+-------+
```

그림 해설 — `id=4` 의 `qty` 는 5 이고 `price` 는 기본값 100 이라 `total` 이 **500** 으로 계산됐다.\
`id=5` 는 `price=7 · qty=3` 이라 **21** 이다. **생성 열은 내가 준 값이 아니라 계산된 값**이다.

★ **「전부 기본값인 한 행」을 넣는 문법은 두 엔진이 서로를 거부한다.**

```text
### SQL: INSERT INTO t49_d DEFAULT VALUES;          (t49_d(id int DEFAULT 7, g varchar(5) DEFAULT 'B'))
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
```

```text
### SQL: SELECT * FROM t49_d;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 id | g                    +------+------+
----+---                   | id   | g    |
  7 | B                    +------+------+
(1 row)                    |    7 | B    |
                           +------+------+
```

**같은 한 행을 만드는 두 문법이 서로를 정확히 거부한다.**\
[21 번의 `COUNT(DISTINCT …)`](../21-aggregate-functions-count-forms/)·[45 번의 자동 증가 문법](../45-check-not-null-default-generated-columns/)과 같은 구조다.

MySQL 매뉴얼이 후자를 그대로 적는다.

> "If both the column list and the `VALUES` list are empty, `INSERT` creates a row with each column set to its default value: `INSERT INTO tbl_name () VALUES();`"\
> — [MySQL 8.4 · INSERT Statement](https://dev.mysql.com/doc/refman/8.4/en/insert.html)

★ **값 개수를 덜 적으면 여기서도 갈린다.**

```text
### SQL: INSERT INTO t49_p VALUES (3);          (t49_p 는 열이 둘: id, name)
--- PG 18.6 ---
INSERT 0 1                 <- ★ 통과한다. 남은 열은 기본값(없으면 NULL)
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

대가 — **PG 쪽이 조용하다.** 열을 하나 추가한 날, 열 목록 없이 쓰던 `INSERT` 가 **에러 없이 `NULL` 을 남기기 시작한다.**\
처방은 방언과 무관하게 하나다 — **열 목록을 항상 적는다.**

> **`DEFAULT` 키워드** — 값 자리에 적어 「이 칸은 기본값으로」라고 명시하는 것.\
> 예: `VALUES (4,'dan',DEFAULT)` 는 `grade` 열을 생략한 것과 같다.

### 4. ★ 생성 열에는 못 넣는다 — 두 엔진이 같다

**언제 쓰나** — 애플리케이션이 계산값을 같이 보낼 때. **ORM 이 여기서 깨진다.**

```text
### SQL: INSERT INTO t49_a (id,name,total) VALUES (9,'gen',999);
--- PG 18.6 ---
ERROR:  cannot insert a non-DEFAULT value into column "total"
DETAIL:  Column "total" is a generated column.
--- MySQL 8.4.10 ---
ERROR 3105 (HY000) at line 1: The value specified for generated column 'total' in table
  't49_a' is not allowed.
```

**그런데 `DEFAULT` 키워드는 받는다**(3번의 `(5,'eve',DEFAULT,7,3,DEFAULT)` 가 그 증거다).

```text
생성 열에 줄 수 있는 것
  DEFAULT    -> 받는다 (「계산해 넣어라」)
  그 밖의 값  -> 에러  (PG: cannot insert a non-DEFAULT value / MySQL: ERROR 3105)
```

★ **이 결론은 [45 번](../45-check-not-null-default-generated-columns/)에 이미 실측돼 있다.** 여기서는 **`INSERT` 문에서 그것이 어떤 모양인지**만 다시 던져 확인했고, 45 와 **에러 문구가 한 글자도 같았다.**\
생성 열의 `STORED`/`VIRTUAL` 차이와 **PostgreSQL 18 부터 기본이 `VIRTUAL`** 이라는 사실은 45 가 정본이다.

비용 — `INSERT` 문을 자동 생성하는 계층(ORM·스크립트)이 그 열을 **읽기 전용으로 표시하지 않으면 모든 저장이 실패한다.**

### 5. `INSERT ... SELECT` — 질의 결과를 그대로 붓는다

**언제 쓰나** — 표를 복사하거나 걸러 옮길 때. **값이 클라이언트를 거치지 않는다.**

```text
INSERT INTO t49_a (id, name, price)
SELECT id, name, price FROM t49_src WHERE price >= 20;
       ^^^^^^^^^^^^^^^^
       열 순서가 위의 열 목록과 1:1 로 맞아야 한다 (이름이 아니라 순서다)
```

```text
### SQL: INSERT INTO t49_a (id,name,price) SELECT id, name, price FROM t49_src WHERE price >= 20;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
INSERT 0 2                 (성공)
```

```text
### SQL: SELECT * FROM t49_a ORDER BY id;
--- PG 18.6 ---                                 --- MySQL 8.4.10 ---
 id  | name  | grade | price | qty | total      +-----+-------+-------+-------+------+-------+
-----+-------+-------+-------+-----+-------     | id  | name  | grade | price | qty  | total |
   1 | ann   | B     |   100 |   1 |   100      +-----+-------+-------+-------+------+-------+
   2 | bob   | B     |   100 |   1 |   100      |   1 | ann   | B     |   100 |    1 |   100 |
   3 | cho   | B     |   100 |   1 |   100      |   2 | bob   | B     |   100 |    1 |   100 |
   4 | dan   | B     |   100 |   5 |   500      |   3 | cho   | B     |   100 |    1 |   100 |
   5 | eve   | B     |     7 |   3 |    21      |   4 | dan   | B     |   100 |    5 |   500 |
 102 | src-b | B     |    20 |   1 |    20      |   5 | eve   | B     |     7 |    3 |    21 |
 103 | src-c | B     |    30 |   1 |    30      | 102 | src-b | B     |    20 |    1 |    20 |
(7 rows)                                        | 103 | src-c | B     |    30 |    1 |    30 |
                                                +-----+-------+-------+-------+------+-------+
```

그림 해설 — **`SELECT` 가 안 준 열(`grade`·`qty`)에도 기본값이 적용된다.** `VALUES` 와 규칙이 같다.

**0행을 돌려주는 `SELECT` 는 에러가 아니다.**

```text
### SQL: INSERT INTO t49_a (id,name) SELECT id, name FROM t49_src WHERE price > 999;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
INSERT 0 0                 (성공 — 0행)
```

★ **「에러가 안 났다」가 「행이 들어갔다」는 아니다.** 적재 스크립트가 여기서 조용히 아무것도 안 한다.\
**넣은 행 수를 반드시 다시 읽어라** — PG 는 `INSERT 0 0`, MySQL 은 `ROW_COUNT()` 다.

★ **자기 표에서 읽어 자기 표에 넣어도 무한히 돌지 않는다.**

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

**3행을 읽어 3행을 넣었다.** 새로 넣은 행을 다시 읽지 않는다 — `SELECT` 가 보는 것은 **문이 시작될 때의 상태**다.\
같은 성질을 [54 번의 변경문 CTE](../54-returning-and-data-modifying-cte/)가 훨씬 극적으로 보여 준다.

비용 — 대량이면 한 문이 길어진다. **잠금과 되돌릴 양이 행 수에 비례해 쌓인다**([51 번](../51-delete-and-truncate/)이 그것을 수치로 잰다).

### 6. ★ 제약이 `INSERT` 를 막는 자리 — 에러가 다 다르다

**언제 쓰나** — 적재가 실패했을 때 **어느 제약이 막았는지** 읽어야 할 때.

**(a) `NOT NULL` — MySQL 은 두 에러를 구분한다.**

```text
### SQL: INSERT INTO t49_a (id) VALUES (10);            -- 열을 아예 안 줬다
--- PG 18.6 ---
ERROR:  null value in column "name" of relation "t49_a" violates not-null constraint
DETAIL:  Failing row contains (10, null, B, 100, 1, 100).
--- MySQL 8.4.10 ---
ERROR 1364 (HY000) at line 1: Field 'name' doesn't have a default value

### SQL: INSERT INTO t49_a (id,name) VALUES (11,NULL);  -- 열을 주고 NULL 을 넣었다
--- PG 18.6 ---
ERROR:  null value in column "name" of relation "t49_a" violates not-null constraint
DETAIL:  Failing row contains (11, null, B, 100, 1, 100).
--- MySQL 8.4.10 ---
ERROR 1048 (23000) at line 1: Column 'name' cannot be null
```

```text
              "열을 안 줬다"            "NULL 을 줬다"
PG 18.6       같은 에러 (not-null 위반)  같은 에러
MySQL 8.4.10  ERROR 1364 (기본값 없음)   ERROR 1048 (NULL 불가)
```

두 그림의 결론 — **MySQL 은 「값을 안 줬다」와 「`NULL` 을 줬다」를 다른 사건으로 본다.**\
★ `1364` 는 **`NOT NULL` 이 아니어도 난다** — 7번에서 이 에러가 경고로 내려앉는 것을 본다.

★ **PG 의 `DETAIL` 에 `B, 100, 1, 100` 이 이미 채워져 있다** — **기본값과 생성 열이 제약 검사보다 먼저 적용된다**는 뜻이다([45 번](../45-check-not-null-default-generated-columns/)의 같은 관찰).

**(b) 외래키 — 그런데 MySQL 에서는 제약이 안 만들어질 수 있다.**

★ **열 뒤에 `REFERENCES` 를 쓴 표로 먼저 던졌다.**

```sql
CREATE TABLE t49_c (id int PRIMARY KEY, p_id int REFERENCES t49_p(id), memo varchar(10));
```

```text
### SQL: INSERT INTO t49_c VALUES (100, 99, 'orphan');     -- t49_p 에 99 는 없다
--- PG 18.6 ---
ERROR:  insert or update on table "t49_c" violates foreign key constraint "t49_c_p_id_fkey"
DETAIL:  Key (p_id)=(99) is not present in table "t49_p".
--- MySQL 8.4.10 ---
(성공)
```

```text
### SQL: INSERT INTO t49_c VALUES (101,1,'ok1'),(102,99,'bad'),(103,2,'ok2');
--- PG 18.6 ---
ERROR:  insert or update on table "t49_c" violates foreign key constraint "t49_c_p_id_fkey"
DETAIL:  Key (p_id)=(99) is not present in table "t49_p".
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT count(*) AS n FROM t49_c;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 n                         +---+
---                        | n |
 0                         +---+
(1 row)                    | 4 |
                           +---+
```

```text
### SQL: SELECT * FROM t49_c ORDER BY id;
--- MySQL 8.4.10 ---
+-----+------+--------+
| id  | p_id | memo   |
+-----+------+--------+
| 100 |   99 | orphan |    <- ★ 부모 없는 행이 들어갔다
| 101 |    1 | ok1    |
| 102 |   99 | bad    |    <- ★ 여기도
| 103 |    2 | ok2    |
+-----+------+--------+
```

★★ **「통과했는데 안 한 것」이다.** `CREATE TABLE` 도 통과했고 `INSERT` 도 통과했는데,\
**MySQL 에서는 외래키 제약 자체가 만들어지지 않았다.** 카탈로그가 그렇게 말한다.

```text
--- MySQL 8.4.10 ---
SHOW CREATE TABLE t49_c\G
Create Table: CREATE TABLE `t49_c` (
  `id` int NOT NULL,
  `p_id` int DEFAULT NULL,
  `memo` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)                 <- ★ FOREIGN KEY 행이 없다
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

[**44 번이 이미 잡아 둔 사고다**](../44-foreign-key-referential-actions/) — MySQL 은 **열 뒤 `REFERENCES` 를 파싱하고 무시**한다.\
표 수준 `FOREIGN KEY` 절로 다시 만들면 **두 엔진이 같이 막는다.**

```sql
CREATE TABLE t49_c (id int PRIMARY KEY, p_id int, memo varchar(10),
                    CONSTRAINT t49_c_fk FOREIGN KEY (p_id) REFERENCES t49_p(id));
```

```text
### SQL: INSERT INTO t49_c VALUES (101,1,'ok1'),(102,99,'bad'),(103,2,'ok2');
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

**정상 행 둘도 안 들어갔다** — 2번의 원자성이 FK 위반에서도 같다.

**(c) 길이 초과 — 둘 다 막는다.**

```text
### SQL: INSERT INTO t49_a (id,name) VALUES (31,'abcdefghijklmno');   -- name 은 varchar(10)
--- PG 18.6 ---
ERROR:  value too long for type character varying(10)
--- MySQL 8.4.10 ---
ERROR 1406 (22001) at line 1: Data too long for column 'name' at row 1
```

★ **MySQL 이 막는 근거는 `sql_mode` 의 `STRICT_TRANS_TABLES` 다** — 머리말의 환경 확인이 여기서 쓰인다.\
그 모드가 꺼져 있으면 **이 문이 경고로 통과하며 문자열이 잘린다.**\
(이 머신에서는 **모드를 끄고 확인하지는 않았다** — 서버 설정을 바꾸지 않기 위해서다. 대신 같은 결과를 내는 `IGNORE` 로 7번에서 확인했다.)

### 7. ★★ MySQL 의 `IGNORE` — **무엇을 삼키나**

**언제 쓰나** — 「틀린 행은 건너뛰고 나머지는 넣어라」를 시킬 때. **이 편에서 가장 위험한 절이다.**

★ **먼저: PG 에는 이 낱말이 없다.**

```text
### SQL: INSERT IGNORE INTO t49_a (id,name) VALUES (40,'x');
--- PG 18.6 ---
ERROR:  syntax error at or near "IGNORE"
LINE 1: INSERT IGNORE INTO t49_a (id,name) VALUES (40,'x')
               ^
```

**(a) 원자성을 깬다.** 2번과 **완전히 같은 입력**이다.

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
| 20 | v20  |     <- ★ 들어갔다
| 21 | v21  |     <- ★ 들어갔다
+----+------+
```

```text
### SQL: INSERT IGNORE INTO t49_a (id,name) VALUES (22,'v22'),(1,'dup'),(23,'v23'); SELECT ROW_COUNT() AS affected;
--- MySQL 8.4.10 ---
+----------+
| affected |
+----------+
|        2 |     <- 3행을 던져 2행이 들어갔다
+----------+
```

```text
2번 (IGNORE 없음)                      7번 (IGNORE 있음)
+---------------------------+          +---------------------------+
| ERROR 1062 — 문이 죽는다  |          | 에러 없음. 경고 1062      |
| 표에 남은 것: 0행         |          | 표에 남은 것: 2행         |
+---------------------------+          +---------------------------+
  -> "무엇이 잘못됐나"를 묻게 된다        -> ★ 아무도 안 묻는다
```

두 그림의 결론 — **`IGNORE` 는 「중복을 무시한다」가 아니라 「문의 원자성을 포기한다**」는 뜻이다.

**(b) `NOT NULL` 을 통과시킨다.** ★ **이것이 「통과했는데 안 한 것」의 정점이다.**

```text
### SQL: INSERT IGNORE INTO t49_a (id) VALUES (30); SHOW WARNINGS;
--- MySQL 8.4.10 ---
+---------+------+-------------------------------------------+
| Level   | Code | Message                                   |
+---------+------+-------------------------------------------+
| Warning | 1364 | Field 'name' doesn't have a default value |
+---------+------+-------------------------------------------+
```

6번에서 **에러였던 `1364` 가 경고로 내려앉았다.** 그러면 그 행의 `name` 에는 무엇이 들어갔나?

```text
### SQL: SELECT id, CONCAT('[',name,']') AS name_shown, LENGTH(name) AS len, grade FROM t49_a WHERE id=30;
--- MySQL 8.4.10 ---
+----+------------+-----+-------+
| id | name_shown | len | grade |
+----+------------+-----+-------+
| 30 | []         |   0 | B     |     <- ★ NOT NULL 열에 빈 문자열이 들어갔다
+----+------------+-----+-------+
```

**`NULL` 은 아니다 — 그래서 `NOT NULL` 제약은 어겨지지 않았다.** 대신 **빈 문자열**이 들어갔다.\
`WHERE name IS NULL` 로는 이 행을 못 찾는다. **불변식은 지켜졌고 데이터는 틀렸다.**

**(c) 조용히 자른다.**

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
| 31 | abcdefghij |  10 |    <- 15자가 10자로 잘렸다
+----+------------+-----+
```

6번에서 **에러 `1406` 이었던 것**이 경고 `1265` 가 됐고, **다섯 글자가 사라졌다.**

매뉴얼이 이 범위를 그대로 적는다 — 「중복만」이 아니다.

> "If you use the `IGNORE` modifier, ignorable errors that occur while executing the `INSERT` statement are ignored. … Ignored errors generate warnings instead. … Data conversions that would trigger errors abort the statement if `IGNORE` is not specified. With `IGNORE`, invalid values are adjusted to the closest values and inserted; warnings are produced but the statement does not abort."\
> — [MySQL 8.4 · INSERT Statement](https://dev.mysql.com/doc/refman/8.4/en/insert.html)

대가 — **`IGNORE` 를 쓴 문은 「성공」을 돌려주고도 데이터가 틀려 있을 수 있다.**\
★ **`SHOW WARNINGS` 를 안 읽으면 그 사실이 어디에도 안 남는다.**

★ **중복만 무시하고 싶다면 범위가 더 좁은 형태가 있다.**

```text
MySQL : INSERT ... ON DUPLICATE KEY UPDATE id = id      -- 중복 키에서만 동작한다
PG    : INSERT ... ON CONFLICT DO NOTHING               -- 52번
```

둘의 문법과 충돌 대상 지정은 [52 UPSERT](../52-upsert/)가 정본이다.

## 문법 — 어느 절에서 무엇이 갈리나

```sql
-- 공통 (두 엔진 다 통과)
INSERT INTO t (a, b) VALUES (1, 'x');
INSERT INTO t (a, b) VALUES (1,'x'), (2,'y'), (3,'z');     -- 다중 행
INSERT INTO t (a, b) SELECT a, b FROM s WHERE ...;         -- INSERT ... SELECT
INSERT INTO t (a, b) VALUES (1, DEFAULT);                  -- DEFAULT 키워드

-- 서로를 거부하는 자리
INSERT INTO t DEFAULT VALUES;      -- PG 만.    MySQL 은 ERROR 1064
INSERT INTO t VALUES ();           -- MySQL 만. PG 는 syntax error
INSERT IGNORE INTO t ...;          -- MySQL 만. PG 는 syntax error
INSERT INTO t VALUES (1) ;         -- ★ PG 는 열이 더 많아도 통과. MySQL 은 ERROR 1136
INSERT INTO t ... RETURNING ...;   -- PG 만 (54번). MySQL 은 ERROR 1064

-- MySQL 의 행 생성자 (10·12번에서 본 것)
INSERT INTO t VALUES ROW(1,'x'), ROW(2,'y');   -- MySQL. PG 는 구문 오류
```

규칙 일곱.

1. **열 목록을 항상 적는다.** 안 적으면 열 순서에 묶이고, PG 에서는 개수가 모자라도 통과한다.
2. **`INSERT ... SELECT` 는 이름이 아니라 순서로 맞춘다.** `SELECT` 의 별칭은 아무 영향이 없다.
3. **한 문은 전부 들어가거나 하나도 안 들어간다** — `IGNORE`·`ON CONFLICT` 가 없는 한.
4. **생성 열에는 `DEFAULT` 만 줄 수 있다.** 값을 주면 양쪽 다 에러다.
5. **기본값은 제약 검사보다 먼저 적용된다**(PG 의 `DETAIL` 이 근거).
6. **MySQL 의 `IGNORE` 는 중복만 삼키는 것이 아니다.** 원자성·`NOT NULL`·길이까지 삼킨다.
7. **`RETURNING` 은 PG 전용**이다 — [54 번](../54-returning-and-data-modifying-cte/).

읽을 때 붙잡을 것은 **「내가 안 적은 칸은 누가 채우나」** 하나다.

```text
 적었나 -> 예       : 그 값이 들어간다 (생성 열이면 에러)
        -> 아니오   : DEFAULT -> 자동 증가 -> 아무것도 없으면 NULL -> NOT NULL 이면 에러
 IGNORE 를 썼나     -> 위 에러가 전부 경고로 내려앉는다 (MySQL)
```

## 어디서 틀리나

1. ★ **「`INSERT` 가 에러를 냈으니 아무것도 안 들어갔겠지」를 `IGNORE` 에도 적용한다.**\
   `IGNORE` 는 **에러를 내지 않으면서** 일부만 넣는다(7번). **행 수를 다시 세야 한다.**
2. ★ **`SHOW WARNINGS` 를 안 읽는다.** MySQL 의 사고는 전부 경고로만 드러난다 — `1062`·`1364`·`1265`.
3. **`INSERT 0 0` 을 실패로 읽거나, 반대로 안 읽는다.**\
   `SELECT` 가 0행이면 `INSERT` 도 0행이다. **에러가 아니므로 적재 스크립트가 조용히 지나간다.**
4. **열 목록 없이 `INSERT INTO t VALUES (...)` 를 쓴다.**\
   열을 추가·재배치한 날 깨진다. PG 에서는 **깨지지도 않고 `NULL` 이 들어간다.**
5. **생성 열을 `INSERT` 문에 포함시킨다.** 양쪽 다 에러다(4번) — [45 번](../45-check-not-null-default-generated-columns/).
6. **MySQL 에서 열 뒤 `REFERENCES` 로 외래키를 만들었다고 믿는다.**\
   **만들어지지 않는다**(6번 b) — [44 번](../44-foreign-key-referential-actions/)이 정본이다. 표 수준 `FOREIGN KEY` 절을 쓴다.
7. **`DEFAULT VALUES` 를 이식 가능한 문법으로 쓴다.** MySQL 은 `ERROR 1064` 다(3번).
8. **대량 `INSERT ... SELECT` 를 한 문으로 던진다.**\
   되돌릴 양과 잠금이 행 수만큼 쌓인다 — [51 번](../51-delete-and-truncate/)이 그 수치를 잰다.
9. **`NOT NULL` 열에 `''` 가 들어갈 수 있다는 것을 잊는다.**\
   `IGNORE` 가 그렇게 만든다(7번 b). **`NOT NULL` 은 빈 문자열을 막지 않는다.**

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| 다중 행 원자성 | 문이 실패하면 그 문의 변경이 전부 취소된다 | — (두 엔진이 같았다) |
| 값 개수가 모자랄 때 | — | ★ **PG 는 통과 / MySQL 은 `ERROR 1136`** |
| 「전부 기본값」 문법 | — | ★ **`DEFAULT VALUES`(PG) 대 `VALUES ()`(MySQL)** |
| `NOT NULL` 위반 에러 | 막는다는 것 | **에러가 하나인가 둘인가**(PG 하나 / MySQL `1364`·`1048`) |
| 열 뒤 `REFERENCES` | 표준 문법으로 보이는 형태 | ★ **MySQL 은 제약을 만들지 않는다**(44번) |
| 길이 초과 | — | **MySQL 은 `sql_mode` 에 달렸다** |
| `IGNORE` | — | **MySQL 전용. 삼키는 범위도 MySQL 이 정한다** |

- **「문 하나가 원자 단위」는 두 엔진에서 같았지만, 그것을 깨는 손잡이가 양쪽에 다 있다** — PG 의 `ON CONFLICT DO NOTHING`, MySQL 의 `IGNORE`.
- **`t49_a_pkey` 대 `t49_a.PRIMARY` 같은 제약 이름 표기**는 구현 세부다. 외울 것은 「**중복 키에서 문 전체가 취소된다**」는 성질이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 다중 행 `VALUES`.** 행 수만큼의 왕복을 한 번으로 줄인다.
- **쓴다 — `INSERT ... SELECT`.** 값이 클라이언트를 왕복하지 않는다. 표 복사·아카이브 이동에 가장 싸다.
- **쓴다 — `DEFAULT` 키워드.** 「이 칸은 일부러 기본값」이라는 의도가 문장에 남는다.
- **안 쓴다 — 열 목록 생략.** 스키마가 바뀐 날 조용히 틀린다.
- **안 쓴다 — `INSERT IGNORE` 를 「중복만 무시」로.** 범위가 훨씬 넓다(7번). 중복만이면 [52 번](../52-upsert/)의 형태를 쓴다.
- **조심한다 — 대량 한 문.** 잠금·되돌릴 양이 행 수에 비례한다. 나눠 도는 기준은 [51 번](../51-delete-and-truncate/)에 있다.
- **조심한다 — 자동 증가와 배치.** MySQL 의 `LAST_INSERT_ID()` 는 **배치의 첫 번호**를 돌려준다(「더 들어가면」).

## 핵심 문장

- **`INSERT` 한 문은 전부 들어가거나 하나도 안 들어간다** — 두 엔진이 같았다.
- ★ **`INSERT IGNORE` 는 그 성질을 깬다.** 3행 중 2행이 들어가고 에러 대신 경고만 남는다.
- ★ **`IGNORE` 는 중복만 삼키지 않는다** — `NOT NULL` 을 빈 문자열로, 15자를 10자로 바꿔 넣는다.
- **내가 안 적은 칸은 `DEFAULT` → 자동 증가 → `NULL` 순으로 채워지고, 그 뒤에 제약이 검사된다.**
- **생성 열에는 `DEFAULT` 키워드만 줄 수 있다** — [45 번](../45-check-not-null-default-generated-columns/)의 결론이 `INSERT` 에서도 같다.
- ★ **「전부 기본값 한 행」은 `DEFAULT VALUES`(PG) 와 `VALUES ()`(MySQL) 로 서로를 거부한다.**
- ★ **MySQL 에서 열 뒤 `REFERENCES` 는 외래키를 만들지 않는다** — `INSERT` 가 고아 행을 통과시킨다.

## 관련 자료

- [PostgreSQL 18 · INSERT](https://www.postgresql.org/docs/18/sql-insert.html) — `DEFAULT VALUES`·`OVERRIDING`·`RETURNING` 의 문법.
- [MySQL 8.4 · INSERT Statement](https://dev.mysql.com/doc/refman/8.4/en/insert.html) — `IGNORE` 가 삼키는 범위, `VALUES ()` 형태.
- [MySQL 8.4 · INSERT ... SELECT](https://dev.mysql.com/doc/refman/8.4/en/insert-select.html)
- [45 CHECK·NOT NULL·DEFAULT·생성 열·자동 증가](../45-check-not-null-default-generated-columns/) — **그쪽은 「기본값·생성 열이 무엇이고 언제 계산되나」까지, 여기는 「`INSERT` 문에서 그것이 어떤 에러·어떤 값이 되나」부터.** `STORED`/`VIRTUAL` 과 버전 이야기는 한 줄도 여기서 다시 쓰지 않는다.
- [44 외래키와 참조 동작](../44-foreign-key-referential-actions/) — **열 뒤 `REFERENCES` 가 MySQL 에서 무시되는 것의 정본.** 여기서는 그것이 `INSERT` 를 안 막는 장면만 보인다.
- [43 기본키·UNIQUE 제약과 NULL](../43-primary-key-unique-and-null/) — 2번의 중복 키 에러가 어디서 오나.
- [52 UPSERT](../52-upsert/) — **충돌을 정상 흐름으로 바꾸는 문법은 거기.** 여기는 **충돌이 문을 죽이는 기본 동작**까지.
- [54 RETURNING 과 변경문을 품은 CTE](../54-returning-and-data-modifying-cte/) — 넣은 행을 그 자리에서 받는 법.
- [50 UPDATE](../50-update-with-join-and-subquery/) · [51 DELETE 와 TRUNCATE](../51-delete-and-truncate/) — 같은 DML 묶음.
- [SQL 주제 목록](../README.md) — 55(트랜잭션 경계)가 「문 하나의 원자성」을 「여러 문의 원자성」으로 넓히는 이웃이다.

## 용어 풀이

- **DML(data manipulation language)** — 행을 넣고 고치고 지우는 문의 묶음. `INSERT`·`UPDATE`·`DELETE` 등.\
  예: `CREATE TABLE` 은 DML 이 아니라 DDL 이다.
- **다중 행 `VALUES`** — 한 `INSERT` 의 `VALUES` 뒤에 괄호 묶음을 여럿 나열하는 형태.\
  예: `VALUES (1,'a'),(2,'b')` 은 두 행을 한 문으로 넣는다.
- **`INSERT ... SELECT`** — 값 목록 대신 질의 결과를 넣는 형태. 값이 서버 밖으로 나가지 않는다.\
  예: `INSERT INTO arch SELECT * FROM t WHERE ts < '2026-01-01'`.
- **문 원자성(statement atomicity)** — 한 문이 실패하면 그 문이 만든 변경이 전부 취소되는 성질.\
  예: 3행 중 2행째가 중복이면 1행째도 안 남는다.
- **`DEFAULT` 키워드** — 값 자리에 적어 「이 칸은 기본값으로」라고 명시하는 것.\
  예: `VALUES (4,'dan',DEFAULT)` 는 그 열을 생략한 것과 같다.
- **생성 열(generated column)** — 다른 열에서 계산되는 열. 직접 값을 쓸 수 없다([45번](../45-check-not-null-default-generated-columns/)).\
  예: `total int GENERATED ALWAYS AS (price*qty) STORED`.
- **`IGNORE` 수식어** — MySQL 에서 「무시할 수 있는 에러」를 경고로 낮추는 수식어.\
  예: `INSERT IGNORE` 는 중복 키·값 변환 실패·기본값 없음을 전부 경고로 바꾼다.
- **`STRICT_TRANS_TABLES`** — MySQL 의 `sql_mode` 값. 잘못된 값을 경고가 아니라 에러로 만든다.\
  예: 이 모드가 없으면 `varchar(10)` 에 15자를 넣어도 문이 통과하고 잘린다.
- **`ERROR 1364`** — MySQL 이 「이 열은 기본값이 없는데 값을 안 줬다」고 거절하는 코드.\
  예: `IGNORE` 를 붙이면 같은 번호가 **경고**로 내려앉는다.
- **`ROW_COUNT()`** — MySQL 에서 직전 문이 바꿨다고 보고하는 행 수를 돌려주는 함수.\
  예: `INSERT IGNORE` 뒤에 이것을 읽어야 몇 행이 들어갔는지 안다.
- **고아 행(orphan row)** — 참조하는 부모 행이 없는 자식 행.\
  예: `t49_c.p_id = 99` 인데 `t49_p` 에 `id=99` 가 없는 행.

## 더 들어가면

- **MySQL 의 `LAST_INSERT_ID()` 는 배치의 「첫」 번호를 돌려준다.** 마지막이 아니다.

```text
### SQL: INSERT INTO t49_ai (v) VALUES ('d'),('e'); SELECT LAST_INSERT_ID() AS last_id;
--- MySQL 8.4.10 ---
+---------+
| last_id |
+---------+
|       4 |     <- 'd' 가 4, 'e' 가 5 다. 이름과 달리 「첫」 번호다
+---------+
```

  두 행 다 받으려면 **`4` 부터 `4 + ROW_COUNT() - 1`** 까지로 읽어야 한다.\
  PG 쪽 대응물은 [`RETURNING`](../54-returning-and-data-modifying-cte/)이고, 추정이 아니라 **실제 값**을 돌려준다.
- **자동 증가 번호는 두 엔진 모두 다중 행 삽입에서 연속으로 붙었다**(`1,2,3`).\
  다만 **동시 삽입이 섞이면 그 보장은 없다** — 이것은 **돌려 보지 않았다**(동시 세션 실험을 하지 않았다).
- **`INSERT ... SELECT` 에 `ORDER BY` 를 붙이는 이유**는 결과 순서가 아니라 **자동 증가 번호를 정렬 순서로 붙이려는 것**이다.\
  `SELECT` 결과 자체의 순서는 표에 저장되지 않는다([08 번](../08-order-by-null-position-stability/)).
- **PG 의 `OVERRIDING SYSTEM VALUE`** 는 `GENERATED ALWAYS AS IDENTITY` 열에 값을 강제로 넣는 절이다.\
  **이 편에서는 던져 보지 않았다** — 45 번이 자동 증가의 정본이라 그쪽으로 넘긴다.
