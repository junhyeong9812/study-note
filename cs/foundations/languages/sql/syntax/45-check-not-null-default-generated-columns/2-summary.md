# sql/45-CHECK·NOT NULL·DEFAULT·생성 열·자동 증가 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) · [PostgreSQL 18 · Generated Columns](https://www.postgresql.org/docs/18/ddl-generated-columns.html) · [PostgreSQL 18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/) · [MySQL 8.4 · CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html) · [MySQL 8.4 · CREATE TABLE and Generated Columns](https://dev.mysql.com/doc/refman/8.4/en/create-table-generated-columns.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **환경 확인** — MySQL 의 `sql_mode` 는 `ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION` 이다. `STRICT_TRANS_TABLES` 가 꺼지면 아래 `NOT NULL` 절의 결론이 달라지므로 먼저 밝힌다.\
> **버전** — ★ **PostgreSQL 18 부터 생성 열의 기본이 `VIRTUAL` 이다**(그 전에는 `STORED` 만 있었다 — [18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)). MySQL 의 `CHECK` 강제는 8.0.16 부터다.\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 `t45_chk`·`t45_def`·`t45_gs`·`t45_gv`·`t45_gd`·`t45_ai`·`t45_ai2`·`t45_ai3`·`t45_cn` 을 만들었고 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> **선행** — [42 테이블 정의와 변경](../42-create-alter-drop-table/) · [04 NULL 의 3값 논리](../04-null-three-valued-logic/) 가 3번 절의 뿌리다.

## 한눈에 — 쉽게 말하면

**이 주제는 「열 하나에 붙일 수 있는 것」의 목록이다.** 넷이 성질이 다르다.

```text
        무엇을 하나                        언제 작동하나
─────────────────────────────────────────────────────────────
NOT NULL   빈칸을 막는다                   쓸 때마다
CHECK      값의 범위를 막는다               쓸 때마다
DEFAULT    안 쓴 자리를 채운다              ★ 값을 안 줬을 때만
생성 열     다른 열에서 값을 만든다          ★ 내가 쓰는 것을 막는다
자동 증가   비어 있으면 다음 번호를 준다      ★ 값을 안 줬을 때만
```

일상 비유로 바꾸면 이렇다 — **서류 양식의 칸**이다.

```text
빈칸으로 두면 안 되는 칸          = NOT NULL
"1 이상만" 이라고 적힌 칸         = CHECK (qty > 0)
안 쓰면 'B' 로 처리되는 칸        = DEFAULT 'B'
직원이 계산해 넣는 칸 (내가 못 씀) = GENERATED ALWAYS AS (...)
접수 번호 칸 (창구에서 찍어 준다)  = 자동 증가
```

"똑같은 구조다" — 그래서 **애플리케이션이 아니라 엔진에 맡길 수 있는 불변식**의 목록이 된다.

| 비유 | 실체 |
|---|---|
| 빈칸 금지 | `NOT NULL` |
| 「1 이상만」 | `CHECK (qty > 0)` |
| ★ 「모름」 이라고 쓴 칸은 검사를 통과한다 | **`CHECK` 는 `NULL` 을 막지 않는다** |
| 안 쓰면 알아서 채워지는 칸 | `DEFAULT` |
| 직원이 계산하는 칸 | 생성 열 |
| 접수 번호 | 자동 증가 |

★ **이 편에서 가장 값비싼 한 줄** — **`CHECK (qty > 0)` 는 `qty` 가 `NULL` 인 행을 통과시킨다.**\
[04 의 3값 논리](../04-null-three-valued-logic/)가 제약에서 나타나는 두 번째 자리다([첫 번째는 43번](../43-primary-key-unique-and-null/)).

## 이 주제가 답하려는 질문

1. **★ `CHECK` 는 `NULL` 을 어떻게 다루나?** — 막는가, 통과시키는가.
2. **`DEFAULT` 는 언제 계산되나?** — 표를 만들 때인가, 행을 넣을 때인가.
3. **생성 열의 `STORED` 와 `VIRTUAL` 은 어디가 다르고, 두 엔진에서 어디까지 되나?**

## 예시 데이터 — 이 묶음이 공유하는 것

이 편도 표를 직접 만들었다가 지운다. **열 하나에 제약 하나씩** 붙여 고립시켰다.

```text
t45_chk                                   t45_gs / t45_gv / t45_gd (생성 열)
+-------+------------------------+        +-------+--------------------------+
| id    | int PRIMARY KEY        |        | id    | int PRIMARY KEY          |
| qty   | int CHECK (qty > 0)    |        | price | int                      |
| name  | varchar(10) NOT NULL   |        | qty   | int                      |
| grade | varchar(5) DEFAULT 'B' |        | total | GENERATED AS (price*qty) |
+-------+------------------------+        +-------+--------------------------+
                                            gs = STORED · gv = VIRTUAL · gd = 키워드 없음
t45_def
+----+----------------------------------+
| id | int PRIMARY KEY                  |
| ts | timestamp DEFAULT CURRENT_TIMESTAMP |
| g  | varchar(5) DEFAULT 'B'           |
+----+----------------------------------+
```

## 동작 방식

### 1. ★★ `CHECK` 는 `NULL` 을 통과시킨다 — **`UNKNOWN` 은 위반이 아니다**

**언제 쓰나** — 값의 범위를 엔진에 맡길 때. **이 절이 이 주제의 핵심**이다.

```sql
CREATE TABLE t45_chk (id int PRIMARY KEY, qty int CHECK (qty > 0),
                      name varchar(10) NOT NULL, grade varchar(5) DEFAULT 'B');
```

**범위를 벗어난 값은 막힌다.**

```text
### SQL: INSERT INTO t45_chk (id,qty,name) VALUES (1,-5,'ann');
--- PG 18.6 ---
ERROR:  new row for relation "t45_chk" violates check constraint "t45_chk_qty_check"
DETAIL:  Failing row contains (1, -5, ann, B).
--- MySQL 8.4.10 ---
ERROR 3819 (HY000) at line 1: Check constraint 't45_chk_chk_1' is violated.
```

★ **그런데 `NULL` 은 통과한다.**

```text
### SQL: INSERT INTO t45_chk (id,qty,name) VALUES (2,NULL,'bob');
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
(성공)
```

```text
### SQL: SELECT * FROM t45_chk;
--- PG 18.6 ---                      --- MySQL 8.4.10 ---
 id | qty | name | grade             +----+------+------+-------+
----+-----+------+-------            | id | qty  | name | grade |
  2 |     | bob  | B                 +----+------+------+-------+
(1 row)                              |  2 | NULL | bob  | B     |
                                     +----+------+------+-------+
```

**왜 그런가 — 규칙이 한 줄이다.**

```text
CHECK 는 조건이 FALSE 일 때만 막는다. TRUE 와 UNKNOWN 은 통과시킨다

  qty = -5   ->  -5 > 0   =  FALSE    -> 막는다
  qty = 10   ->  10 > 0   =  TRUE     -> 통과
  qty = NULL ->  NULL > 0 =  UNKNOWN  -> ★ 통과
```

[04 의 3값 논리](../04-null-three-valued-logic/)가 그대로다 — **`WHERE` 는 `UNKNOWN` 행을 버리지만 `CHECK` 는 통과시킨다.**\
같은 `UNKNOWN` 을 두 절이 반대로 다룬다.

```text
WHERE  절 : TRUE 인 행만 남긴다       -> UNKNOWN 은 버려진다
CHECK 제약 : FALSE 인 행만 막는다      -> UNKNOWN 은 통과한다
```

대가 — **「`qty` 는 항상 양수다」가 거짓이 된다.**\
`qty` 가 `NULL` 인 행이 쌓여도 제약은 한 번도 안 걸린다.

**처방** — 정말 양수만 허용하려면 **`NOT NULL` 을 같이 걸거나 조건에 `NULL` 을 적는다.**

```sql
qty int NOT NULL CHECK (qty > 0)
-- 또는
qty int CHECK (qty IS NOT NULL AND qty > 0)
```

### 2. `NOT NULL` 을 어기면

**언제 쓰나** — 1번의 짝. **`NOT NULL` 만이 `NULL` 을 막는 유일한 수단**이다.

```text
### SQL: INSERT INTO t45_chk (id,qty,name) VALUES (3,5,NULL);
--- PG 18.6 ---
ERROR:  null value in column "name" of relation "t45_chk" violates not-null constraint
DETAIL:  Failing row contains (3, 5, null, B).
--- MySQL 8.4.10 ---
ERROR 1048 (23000) at line 1: Column 'name' cannot be null
```

[43 번의 PK 에 `NULL`](../43-primary-key-unique-and-null/) 과 **똑같은 에러**다 — PK 가 `NOT NULL` 을 포함하기 때문이다.

★ **`DETAIL` 에 `grade` 가 `B` 로 채워져 있다.** 기본값이 **검사 전에 이미 적용됐다**는 뜻이다.

```text
INSERT (id, qty, name) 만 줬는데
        ↓
DEFAULT 로 grade='B' 를 채운다
        ↓
그 다음에 NOT NULL·CHECK 를 검사한다
        ↓
Failing row contains (3, 5, null, B)   <- B 가 이미 있다
```

### 3. `DEFAULT` 는 **행을 넣을 때** 계산된다

**언제 쓰나** — `CURRENT_TIMESTAMP` 같은 기본값을 쓸 때. 「언제의 시각인가」가 여기서 정해진다.

```sql
CREATE TABLE t45_def (id int PRIMARY KEY, ts timestamp DEFAULT CURRENT_TIMESTAMP,
                      g varchar(5) DEFAULT 'B');
```

`INSERT` 를 **2초 간격**으로 두 번 던졌다.

```text
### SQL: SELECT id, ts FROM t45_def ORDER BY id;
--- PG 18.6 ---
 id |             ts             
----+----------------------------
  1 | 2026-09-21 06:45:13.104959
  2 | 2026-09-21 06:45:15.302151
(2 rows)

--- MySQL 8.4.10 ---
+----+---------------------+
| id | ts                  |
+----+---------------------+
|  1 | 2026-09-21 06:45:13 |
|  2 | 2026-09-21 06:45:15 |
+----+---------------------+
```

그림 해설 — **값이 다르다.** `DEFAULT` 식은 `CREATE TABLE` 때 **한 번 계산돼 박히는 것이 아니라**\
`INSERT` 마다 다시 계산된다.

```text
CREATE TABLE 시점 : "CURRENT_TIMESTAMP 를 쓰겠다" 는 식(expression)만 저장한다
INSERT 시점       : 그 식을 실행해 값을 만든다
```

★ **덤으로 정밀도 차이가 보인다** — PG 는 마이크로초, MySQL 의 `timestamp` 는 **기본이 초 단위**다.\
초 미만이 필요하면 MySQL 에서는 `timestamp(6)` 으로 적어야 한다([40 날짜·시간](../40-date-time-types-and-functions/)이 정본이다).

**`DEFAULT` 를 바꿔도 기존 행은 안 바뀐다.**

```text
ALTER TABLE t45_def ALTER COLUMN g SET DEFAULT 'Z';    -- ★ 양쪽 다 받는 문법이다
INSERT INTO t45_def (id) VALUES (3);

### SQL: SELECT id, g FROM t45_def ORDER BY id;
--- PG 18.6 ---        --- MySQL 8.4.10 ---
 id | g                +----+------+
----+---               | id | g    |
  1 | B                +----+------+
  2 | B                |  1 | B    |
  3 | Z                |  2 | B    |
(3 rows)               |  3 | Z    |
                       +----+------+
```

**기본값은 「그 순간 행에 복사되는 값**」이지 열에 계속 붙어 있는 규칙이 아니다.\
바뀐 기본값은 **그 뒤 `INSERT` 에만** 적용된다.

비용 — **기본값 변경은 과거를 고치지 않는다.** 과거 행을 바꾸려면 `UPDATE` 가 따로 필요하다.

### 4. ★ `CHECK` 에 못 쓰는 것 — 두 엔진이 다르게 막는다

**언제 쓰나** — `CHECK` 를 설계할 때. 「**행 하나만 보고 판정 가능한가**」가 기준이다.

**서브쿼리는 둘 다 거부한다.**

```text
### SQL: CREATE TABLE t45_cs (id int, CHECK (id IN (SELECT id FROM t45_chk)));
--- PG 18.6 ---
ERROR:  cannot use subquery in check constraint
LINE 1: CREATE TABLE t45_cs (id int, CHECK (id IN (SELECT id FROM t4...
                                               ^
--- MySQL 8.4.10 ---
ERROR 3815 (HY000) at line 1: An expression of a check constraint 't45_cs_chk_1' contains
  disallowed function.
```

★ **비결정 함수에서는 갈린다.**

```text
### SQL: CREATE TABLE t45_cn (d date, CHECK (d <= CURRENT_DATE));
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
ERROR 3814 (HY000) at line 1: An expression of a check constraint 't45_cn_chk_1' contains
  disallowed function: curdate.
```

**PG 는 받아 준다. 그리고 그것이 함정이다.**

```text
--- PG 18.6 ---
INSERT INTO t45_cn VALUES (DATE '2026-09-21');
INSERT 0 1
SELECT * FROM t45_cn;
     d      
------------
 2026-09-21
(1 row)
```

그림 해설 — 오늘 넣을 때는 `d <= CURRENT_DATE` 가 참이라 통과한다.\
**그런데 이 제약은 「행이 들어올 때」만 검사된다.** 내일이 되면 조건은 그대로인데\
**표 안에는 그 조건을 새로 검사하면 통과 못 할 행**이 생길 수 있다\
(미래 날짜를 넣지 못했을 뿐, 과거에 통과한 행이 나중에 조건을 어기는 방향의 제약이면 그렇게 된다).

```text
MySQL : 비결정 함수를 아예 못 쓰게 한다        -> 이 문제가 생길 수 없다
PG    : 쓸 수 있다                            -> "언제 검사되나" 를 내가 알아야 한다
```

대가 — PG 에서 덤프를 복원하거나 `ALTER TABLE ... VALIDATE` 를 돌리면 **그때 다시 검사**되므로\
**과거에 통과했던 행이 복원 때 거부될 수 있다.**\
(이 실험에서는 하루를 넘기지 않아 **그 거부 자체는 재현하지 못했다** — 재현하려면 날짜를 넘겨야 한다.)

**규칙** — **`CHECK` 에는 「그 행의 값만으로 영원히 판정되는 것」만 쓴다.**

### 5. ★ 생성 열 — PostgreSQL 18 에서 판이 바뀌었다

**언제 쓰나** — 다른 열에서 계산되는 값을 열처럼 쓰고 싶을 때. **인덱스를 걸 수 있는 것이 이 기능의 값어치**다(46번).

```sql
CREATE TABLE t45_gs (id int PRIMARY KEY, price int, qty int,
                     total int GENERATED ALWAYS AS (price*qty) STORED);    -- (a)
CREATE TABLE t45_gv (... GENERATED ALWAYS AS (price*qty) VIRTUAL);          -- (b)
CREATE TABLE t45_gd (... GENERATED ALWAYS AS (price*qty));                  -- (c) 키워드 없음
```

**세 문 다 두 엔진에서 성공했다.**

```text
--- PG 18.6 ---
CREATE TABLE      (a)
CREATE TABLE      (b)   <- ★ VIRTUAL 이 통과한다
CREATE TABLE      (c)
--- MySQL 8.4.10 ---
(세 문 다 성공)
```

**키워드를 안 쓰면 무엇이 되나 — 카탈로그에 물었다.**

```text
--- PG 18.6 ---
SELECT c.relname, a.attgenerated FROM pg_attribute a
  JOIN pg_class c ON c.oid=a.attrelid WHERE a.attname='total';
 relname | attgenerated 
---------+--------------
 t45_gd  | v                <- 키워드 없음 -> VIRTUAL
 t45_gs  | s
 t45_gv  | v

--- MySQL 8.4.10 ---
SELECT table_name, extra FROM information_schema.columns
  WHERE table_schema='study' AND table_name LIKE 't45_g%' AND column_name='total';
+------------+-------------------+
| TABLE_NAME | EXTRA             |
+------------+-------------------+
| t45_gd     | VIRTUAL GENERATED |     <- 키워드 없음 -> VIRTUAL
| t45_gs     | STORED GENERATED  |
| t45_gv     | VIRTUAL GENERATED |
+------------+-------------------+
```

★ **두 엔진이 같아졌다.** `VIRTUAL` 지원도, 키워드 없을 때의 기본값도 같다.

**★ 버전이 붙는 자리다.** PostgreSQL 은 **18 부터** 가상 생성 열을 지원하고 **기본이 `VIRTUAL`** 이다\
([18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)). 17 이하에서는 `STORED` 만 있었고 키워드를 빼면 에러였다.\
**이 머신에 PG 17 컨테이너가 없어 그 에러를 직접 던져 보지는 못했다** — 18.6 의 관찰만 실었다.

```text
                STORED                          VIRTUAL
저장            디스크에 값을 쓴다               안 쓴다
읽기            그냥 읽는다                     읽을 때마다 계산한다
쓰기 비용       INSERT/UPDATE 마다 계산+저장     없다
공간            열 하나만큼 든다                 안 든다
인덱스          걸 수 있다                      ★ 엔진에 따라 다르다 (46번)
```

**두 가지 다 「내가 못 쓴다」는 점은 같다** — 6번.

### 6. ★ 생성 열에 직접 대입하면

**언제 쓰나** — 애플리케이션이 계산값을 같이 보낼 때. **ORM 이 여기서 자주 깨진다.**

```text
### SQL: INSERT INTO t45_gs (id,price,qty,total) VALUES (2,100,3,999);
--- PG 18.6 ---
ERROR:  cannot insert a non-DEFAULT value into column "total"
DETAIL:  Column "total" is a generated column.
--- MySQL 8.4.10 ---
ERROR 3105 (HY000) at line 1: The value specified for generated column 'total' in table
  't45_gs' is not allowed.
```

```text
### SQL: UPDATE t45_gs SET total=999 WHERE id=1;
--- PG 18.6 ---
ERROR:  column "total" can only be updated to DEFAULT
DETAIL:  Column "total" is a generated column.
--- MySQL 8.4.10 ---
ERROR 3105 (HY000) at line 1: The value specified for generated column 'total' in table
  't45_gs' is not allowed.
```

★ **PG 의 두 에러 문구가 다르다** — `cannot insert a non-DEFAULT value` 와 `can only be updated to DEFAULT`.\
둘 다 **`DEFAULT` 키워드는 허용한다**는 말이다. 던져서 확인했다.

```text
### SQL: INSERT INTO t45_gs (id,price,qty,total) VALUES (3,10,2,DEFAULT);
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
(성공)
```

**기반 열을 바꾸면 따라 바뀐다.**

```text
### SQL: UPDATE t45_gs SET qty=5 WHERE id=1;   (price=100, total 은 300 이었다)
--- PG 18.6 ---
UPDATE 1
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT * FROM t45_gs ORDER BY id;
--- PG 18.6 ---                       --- MySQL 8.4.10 ---
 id | price | qty | total             +----+-------+------+-------+
----+-------+-----+-------            | id | price | qty  | total |
  1 |   100 |   5 |   500             +----+-------+------+-------+
  3 |    10 |   2 |    20             |  1 |   100 |    5 |   500 |
(2 rows)                              |  3 |    10 |    2 |    20 |
                                      +----+-------+------+-------+
```

비용 — **애플리케이션 코드에서 그 열을 빼야 한다.** `INSERT` 문을 자동 생성하는 ORM 은\
그 열을 「읽기 전용」으로 표시하지 않으면 **모든 저장이 실패한다.**

### 7. 자동 증가 — **이름이 셋, 그중 하나는 함정**

**언제 쓰나** — 대리키를 만들 때([43번](../43-primary-key-unique-and-null/)).

```text
### SQL: CREATE TABLE t45_ai (id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, v varchar(5));
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'IDENTITY PRIMARY KEY, v varchar(5))' at line 1
```

```text
### SQL: CREATE TABLE t45_ai3 (id int AUTO_INCREMENT PRIMARY KEY, v varchar(5));
--- PG 18.6 ---
ERROR:  syntax error at or near "AUTO_INCREMENT"
LINE 1: CREATE TABLE t45_ai3 (id int AUTO_INCREMENT PRIMARY KEY, v v...
                                     ^
--- MySQL 8.4.10 ---
(성공)
```

**서로를 정확히 거부한다** — [35 번의 `CAST` 타입 이름](../35-type-system-and-casting/)과 같은 구조다.

★ **그런데 `serial` 은 양쪽 다 통과한다. 그리고 결과가 다르다.**

```text
### SQL: CREATE TABLE t45_ai2 (id serial PRIMARY KEY, v varchar(5));
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
(성공)
```

```text
--- PG 18.6 ---
\d t45_ai2
 Column |         Type         | Collation | Nullable |               Default               
--------+----------------------+-----------+----------+-------------------------------------
 id     | integer              |           | not null | nextval('t45_ai2_id_seq'::regclass)
 v      | character varying(5) |           |          | 

--- MySQL 8.4.10 ---
Create Table: CREATE TABLE `t45_ai2` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `v` varchar(5) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

그림 해설 — 같은 글자에서 **다른 세 가지**가 나왔다.

```text
              PG 의 serial              MySQL 의 SERIAL
타입          integer (4바이트)          bigint unsigned (8바이트)
구현          별도 시퀀스 객체            AUTO_INCREMENT
덤            —                          ★ UNIQUE KEY 가 하나 더 생긴다 (PK 와 중복)
```

★ **에러가 안 나서 가장 위험한 자리다.** [42 번의 이식 목록](../42-create-alter-drop-table/)에 넣을 항목이 하나 더 늘었다.\
**MySQL 쪽에는 쓸모없는 인덱스가 하나 더 생기고**, 타입 폭도 두 배가 된다.

## 문법 — 어느 절에서 무엇이 갈리나

```sql
-- 열 뒤에 붙는 것들
c int NOT NULL                                     -- 양쪽
c int CHECK (c > 0)                                -- 양쪽 (MySQL 은 8.0.16 부터 실제로 강제)
c int DEFAULT 0                                    -- 양쪽
c timestamp DEFAULT CURRENT_TIMESTAMP              -- 양쪽
c int GENERATED ALWAYS AS (a*b) STORED             -- 양쪽
c int GENERATED ALWAYS AS (a*b) VIRTUAL            -- ★ 양쪽 (PG 는 18 부터)
c int GENERATED ALWAYS AS (a*b)                    -- 양쪽 — 기본은 VIRTUAL

-- 자동 증가
c int GENERATED ALWAYS AS IDENTITY                 -- PG (MySQL 은 ERROR 1064)
c serial                                           -- ★ 양쪽 다 받는다. 결과가 다르다
c int AUTO_INCREMENT                               -- MySQL (PG 는 문법 에러)

-- 표 수준 CHECK (여러 열을 함께 본다)
CONSTRAINT c_range CHECK (lo <= hi)                -- 양쪽

-- 기본값 바꾸기
ALTER TABLE t ALTER COLUMN g SET DEFAULT 'Z';      -- ★ 양쪽 다 받는다
ALTER TABLE t ALTER COLUMN g DROP DEFAULT;         -- ★ 양쪽 다 받는다
```

- **`CHECK` 는 열 뒤에도 표 수준에도 쓸 수 있다.** 두 열을 비교하는 조건은 표 수준으로 쓴다.

```text
### SQL: CREATE TABLE t45_tc (lo int, hi int, g varchar(5) DEFAULT 'B',
                              CONSTRAINT t45_tc_range CHECK (lo <= hi));
        INSERT INTO t45_tc (lo,hi) VALUES (5,3);
--- PG 18.6 ---
CREATE TABLE
ERROR:  new row for relation "t45_tc" violates check constraint "t45_tc_range"
DETAIL:  Failing row contains (5, 3, B).
--- MySQL 8.4.10 ---
ERROR 3819 (HY000) at line 1: Check constraint 't45_tc_range' is violated.
```

  ★ **이름을 직접 주면 두 엔진이 같은 이름을 에러에 찍는다** — 1번의 자동 이름(`t45_chk_qty_check` 대 `t45_chk_chk_1`)과 대비된다.
- **`DEFAULT` 는 식(expression)이다.** 저장되는 것은 결과가 아니라 식이다(3번).

## 어디서 틀리나

1. ★ **`CHECK (qty > 0)` 이 `NULL` 을 막는다고 생각한다.** 막지 않는다(1번).\
   `UNKNOWN` 은 위반이 아니다. **`NOT NULL` 을 같이 걸어야 한다.**
2. **`WHERE` 와 `CHECK` 가 `UNKNOWN` 을 같이 다룬다고 생각한다.** 반대다.\
   `WHERE` 는 **`TRUE` 만 남기고**, `CHECK` 는 **`FALSE` 만 막는다.**
3. **`DEFAULT CURRENT_TIMESTAMP` 가 표 만들 때의 시각으로 고정된다고 생각한다.** `INSERT` 마다 계산된다(3번).
4. **`DEFAULT` 를 바꾸면 기존 행도 바뀔 것이라 기대한다.** 안 바뀐다(3번).
5. **PG 의 `CHECK` 에 `CURRENT_DATE` 를 쓴다.** MySQL 이 막는 이유가 있다(4번).\
   **넣을 때만 검사되므로** 시간이 지나면 제약과 데이터가 어긋날 수 있다.
6. **생성 열을 `INSERT` 문에 포함시킨다.** 양쪽 다 에러다(6번). ORM 설정에서 읽기 전용으로 표시한다.
7. **`serial` 이 이식 가능한 문법이라고 생각한다.** 양쪽 다 통과하지만 **타입·구현·부가 인덱스가 다르다**(7번).
8. **「PG 는 `VIRTUAL` 생성 열이 없다」로 외운다.** **18 부터 있고 기본값이다**(5번).\
   17 이하를 쓰는 환경이면 반대이므로 **버전을 확인해야 한다.**
9. **`NOT NULL` 을 `CHECK (c IS NOT NULL)` 로 대신한다.** 동작은 비슷하지만\
   최적화기가 `NOT NULL` 을 더 잘 활용하고, 카탈로그 표시(`\d` 의 `Nullable`)도 달라진다.

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| `CHECK` 와 `NULL` | `UNKNOWN` 은 위반이 아니다 | — (두 엔진이 같았다) |
| `CHECK` 에 쓸 수 있는 식 | 행 하나로 판정 가능해야 한다 | **비결정 함수 허용 여부**(PG 허용 / MySQL 거부) |
| `DEFAULT` 평가 시점 | `INSERT` 때 | 시간 타입의 **정밀도**(PG 마이크로초 / MySQL 초) |
| 생성 열 | 직접 대입 불가 | **`VIRTUAL` 지원 여부와 기본값**(PG 는 18 부터) |
| 자동 증가 | — | **문법 이름 전부**(`IDENTITY`/`serial`/`AUTO_INCREMENT`) |

- **「`CHECK` 가 `NULL` 을 통과시킨다」는 두 엔진에서 같았지만, 근거는 같은 출력이 아니라 3값 논리다.**\
  조건식의 결과가 `UNKNOWN` 이고 제약은 `FALSE` 일 때만 막는다 — [04번](../04-null-three-valued-logic/)이 정본이다.
- **`t45_chk_chk_1` 같은 자동 제약 이름**은 MySQL 의 구현 세부다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — `NOT NULL` 을 기본자세로.** 「빌 수 있다」는 설계상의 결정이어야지 기본값이면 안 된다.
- **쓴다 — `CHECK` 로 값의 범위.** 애플리케이션이 여럿이어도 엔진 하나가 막아 준다.
- **쓴다 — 생성 열 + 인덱스.** 계산값으로 검색해야 할 때. 표현식 인덱스와 같은 효과다(46·47번).
- **안 쓴다 — `CHECK` 만으로 `NULL` 막기.** 안 막힌다(1번).
- **안 쓴다 — `CHECK` 에 비결정 함수.** PG 는 받아 주지만 나중에 어긋난다(4번).
- **안 쓴다 — `serial` 을 이식 가능한 문법으로.** 엔진마다 다른 것이 만들어진다(7번).
- **조심한다 — `STORED` 생성 열.** 쓰기마다 계산되고 공간을 쓴다. 읽기가 훨씬 잦을 때만 유리하다.
- **조심한다 — `VIRTUAL` 생성 열의 인덱스.** 되는지는 엔진에 달렸다(46번).

## 핵심 문장

- ★ **`CHECK` 는 `FALSE` 만 막는다.** `NULL` 이 만든 `UNKNOWN` 은 통과한다 — `NOT NULL` 을 같이 걸어야 한다.
- **`WHERE` 는 `TRUE` 만 남기고 `CHECK` 는 `FALSE` 만 막는다** — 같은 `UNKNOWN` 을 반대로 다룬다.
- **`DEFAULT` 는 `INSERT` 마다 계산된다.** 바꿔도 기존 행은 안 바뀐다.
- **MySQL 은 `CHECK` 에 비결정 함수를 금지하고 PG 는 허용한다** — PG 쪽이 함정이다.
- **생성 열은 양쪽 다 직접 대입을 거부한다.** `DEFAULT` 키워드만 허용한다.
- ★ **PostgreSQL 18 부터 생성 열의 기본이 `VIRTUAL` 이다** — MySQL 과 같아졌다.
- **`serial` 은 양쪽 다 통과하는데 만들어지는 것이 다르다** — 가장 조용한 이식 함정이다.

## 관련 자료

- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **그쪽은 `UNKNOWN` 의 계산 규칙까지,\
  여기는 그 규칙이 `CHECK` 에서 어떻게 나타나나부터.** 진리표는 한 줄도 여기서 다시 쓰지 않는다.
- [42 테이블 정의와 변경](../42-create-alter-drop-table/) — 이 제약들을 붙이고 떼는 `ALTER` 의 비용.
- [43 기본키·UNIQUE 제약과 NULL](../43-primary-key-unique-and-null/) — 같은 3값 논리의 첫 번째 나타남.
- [46 인덱스 정의](../46-index-definition-composite-partial-expression/) — **생성 열에 인덱스를 거는 것**이 거기다.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — `serial` 이 어느 타입이 되는지가 왜 문제인가.
- [40 날짜·시간 타입과 함수](../40-date-time-types-and-functions/) — `timestamp` 정밀도의 정본.
- [SQL 주제 목록](../README.md) — 49(INSERT — 기본값·생성 열이 어떻게 채워지나) 가 이웃이다.

## 용어 풀이

- **`CHECK` 제약** — 행 하나의 값이 조건을 만족하는지 검사하는 제약. **`FALSE` 일 때만 막는다.**\
  예: `CHECK (qty > 0)` 은 `qty = -5` 를 막지만 `qty = NULL` 은 통과시킨다.
- **`UNKNOWN`** — 참도 거짓도 아닌 세 번째 진릿값. `NULL` 이 낀 비교의 결과다.\
  예: `NULL > 0` 은 `FALSE` 가 아니라 `UNKNOWN` 이다.
- **`NOT NULL`** — 그 열이 비어 있으면 안 된다는 제약. **`NULL` 을 막는 유일한 수단**이다.\
  예: `CHECK (c IS NOT NULL)` 로도 비슷한 효과가 나지만 카탈로그 표시가 달라진다.
- **`DEFAULT`** — 값을 안 준 자리를 채우는 **식**. 결과가 아니라 식이 저장된다.\
  예: `DEFAULT CURRENT_TIMESTAMP` 는 `INSERT` 마다 그때의 시각을 만든다.
- **비결정 함수(non-deterministic function)** — 같은 입력에 대해 호출 때마다 다른 값을 낼 수 있는 함수.\
  예: `CURRENT_DATE`·`RANDOM()`. MySQL 은 `CHECK` 에 이런 것을 금지한다.
- **생성 열(generated column)** — 다른 열에서 계산되는 열. 직접 값을 쓸 수 없다.\
  예: `total int GENERATED ALWAYS AS (price*qty) STORED`.
- **`STORED`** — 생성 열의 값을 디스크에 저장하는 방식. 쓸 때 계산하고 읽을 때는 그냥 읽는다.\
  예: 읽기가 쓰기보다 훨씬 잦고 인덱스가 필요할 때 고른다.
- **`VIRTUAL`** — 생성 열을 저장하지 않고 **읽을 때마다 계산**하는 방식. **PostgreSQL 18 부터 기본값**이다.\
  예: 공간을 안 쓰는 대신 조회 때마다 계산 비용이 든다.
- **`ERROR 3105`** — MySQL 이 「생성 열에 값을 지정했다」고 거절하는 코드.\
  예: `INSERT` 목록에 그 열을 넣으면 나온다.
- **`ERROR 3814` / `ERROR 3815`** — MySQL 이 `CHECK` 식에 허용되지 않는 함수·서브쿼리가 있다고 거절하는 코드.\
  예: `3814` 는 함수 이름을 `disallowed function: curdate` 처럼 찍어 준다.
- **`serial`** — 자동 증가 열을 만드는 축약. ★ **PG 는 `integer`+시퀀스, MySQL 은 `bigint unsigned`+`AUTO_INCREMENT`+`UNIQUE`.**\
  예: 같은 글자가 두 엔진에서 다른 스키마를 만든다.
- **시퀀스(sequence)** — 번호를 순서대로 발급하는 독립 객체. PG 의 `serial` 이 뒤에서 이것을 만든다.\
  예: `nextval('t45_ai2_id_seq')` 가 기본값으로 박힌다.

## 더 들어가면

- **`CHECK` 제약은 `NOT VALID` 로 붙였다가 나중에 검증할 수 있다**(PG).\
  큰 표에 제약을 붙일 때 전체 스캔을 뒤로 미루는 운영 기법이다 — [42 번의 `ALTER` 잠금](../42-create-alter-drop-table/)과 이어진다.\
  **이 실험에서 `NOT VALID` 를 던져 보지는 않았다.**
- **MySQL 의 `CHECK` 는 8.0.16 이전에는 파싱만 하고 무시했다.**\
  [44 번의 열 뒤 `REFERENCES`](../44-foreign-key-referential-actions/) 와 **같은 종류의 조용한 무시**였다.\
  8.4.10 에서는 실제로 강제된다(1번의 `ERROR 3819` 가 근거다).\
  **옛 버전 컨테이너가 없어 무시되던 동작은 직접 재현하지 못했다.**
- **`VIRTUAL` 생성 열은 「열처럼 보이는 식**」이다. 뷰로도 같은 것을 만들 수 있지만,\
  생성 열은 **그 표의 일부라서 인덱스·제약을 걸 수 있다**는 점이 다르다(46번).
- **`DEFAULT` 와 생성 열은 「안 주면 채운다」와 「줄 수 없다」로 갈린다.**\
  둘을 한 열에 같이 쓸 수는 없다 — 생성 열은 값의 출처가 이미 정해져 있다.
