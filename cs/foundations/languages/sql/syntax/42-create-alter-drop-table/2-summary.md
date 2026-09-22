# sql/42-테이블 정의와 변경 (CREATE·ALTER·DROP) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · CREATE TABLE](https://www.postgresql.org/docs/18/sql-createtable.html) · [PostgreSQL 18 · ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html) · [PostgreSQL 18 · DROP TABLE](https://www.postgresql.org/docs/18/sql-droptable.html) · [MySQL 8.4 · CREATE TABLE](https://dev.mysql.com/doc/refman/8.4/en/create-table.html) · [MySQL 8.4 · ALTER TABLE](https://dev.mysql.com/doc/refman/8.4/en/alter-table.html) · [MySQL 8.4 · Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·**경고(Note)** 는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `ALTER TABLE ... ALGORITHM=INSTANT` 는 MySQL 8.0 부터다. 그 밖의 동작에는 「어느 버전부터」가 붙는 것을 두 매뉴얼에서 찾지 못해 **적지 않는다.**\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 `t42_a`·`t42_b`·`t42_tx` 와 뷰 `v42_a` 를 만들었고 **전부 지웠다.** `emp`·`dept` 는 **한 줄도 건드리지 않았다.**\
> **선행** — [35 타입 체계와 캐스팅](../35-type-system-and-casting/) · 이어지는 것은 [43 기본키·UNIQUE](../43-primary-key-unique-and-null/) · [45 CHECK·DEFAULT·생성 열](../45-check-not-null-default-generated-columns/) · [46 인덱스 정의](../46-index-definition-composite-partial-expression/) 다.

## 한눈에 — 쉽게 말하면

**`CREATE TABLE` = 「앞으로 들어올 값이 지켜야 할 약속」을 엔진에 맡기는 것.**

약속을 나중에 바꾸는 것이 `ALTER`, 약속을 없애는 것이 `DROP` 이다.\
쉬운 쪽은 `CREATE` 다. 값어치는 **나머지 둘이 운영 중에 무슨 일을 벌이느냐**에 있다.

```text
빈 창고에 선반을 짠다            = CREATE TABLE  (아무도 안 쓰는 중이라 싸다)
        ↓
물건이 20,000개 들어찬다
        ↓
선반 규격을 바꾼다               = ALTER TABLE   (★ 창고 문을 잠그느냐가 전부다)
        ↓
선반을 통째로 들어낸다            = DROP TABLE    (★ 그 선반을 가리키던 표지판은?)
```

| 비유 | 실체 |
|---|---|
| 선반 규격표 | 표 정의 — 열 이름·타입·NULL 허용·기본값 |
| 선반을 짠다 | `CREATE TABLE` |
| 규격을 바꾼다 | `ALTER TABLE` |
| **창고 문을 잠그고 바꾼다** | **표를 다시 쓰는(rewrite) `ALTER` — 그동안 아무도 못 읽는다** |
| 라벨만 고쳐 붙인다 | 메타데이터만 바꾸는 `ALTER` — 순식간에 끝난다 |
| 선반을 들어낸다 | `DROP TABLE` |
| 그 선반을 가리키던 표지판 | 의존 객체(뷰·외래키) |

> **DDL(Data Definition Language)** — 데이터가 아니라 **데이터의 모양**을 바꾸는 문. `CREATE`·`ALTER`·`DROP` 이 여기다.\
> 예: `INSERT` 는 행을 넣지만 `ALTER TABLE ... ADD COLUMN` 은 **모든 행의 모양**을 바꾼다.

이 주제의 값어치가 몰린 한 문장은 이것이다.

```text
PostgreSQL          DDL 이 트랜잭션 안에 든다   -> BEGIN ... ROLLBACK 으로 되돌릴 수 있다
MySQL               DDL 이 암묵 커밋이다        -> ROLLBACK 해도 표가 남는다
```

## 이 주제가 답하려는 질문

1. **`CREATE TABLE` 이 정하는 축은 무엇인가?** — 열 이름·타입·NULL 허용·기본값·제약.
2. **운영 중 `ALTER TABLE` 은 무엇을 잠그나?** — 여기가 이 주제의 실무 값어치다.
3. **`DROP` 했을 때 그 표를 가리키던 객체는 어떻게 되나?**

## 예시 데이터 — 이 묶음이 공유하는 것

DDL 이 주제라 **읽기만 하는 공유 표로는 예제가 서지 않는다.** 그래서 이 편은 표를 **직접 만들었다가 지운다.**

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |    <- 이 둘은 이 편에서 읽지도 않는다
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

이 편이 쓴 표는 전부 `t42_` 로 시작한다.

```sql
t42_a   -- 정의·ALTER·DROP 실험용
t42_b   -- MySQL 의 ALGORITHM/LOCK 절 실험용
t42_tx  -- 트랜잭션 안의 DDL 실험용
v42_a   -- t42_a 에 의존하는 뷰
```

**전부 지웠다.** 뒷정리 확인은 이 문서 끝의 「실행 검증」이 아니라 [3-answer.md](3-answer.md) 의 마지막 절에 출력째 실려 있다.

## 동작 방식

### 1. `CREATE TABLE` — 열 하나가 정하는 네 가지

**언제 쓰나** — 표를 처음 만들 때. 그리고 **이 네 칸을 여기서 안 정하면 나중에 `ALTER` 로 정하게 된다**(그쪽이 비싸다).

```text
CREATE TABLE t42_a (
    id         int          PRIMARY KEY,                    -- (1) 이름  (2) 타입
    name       varchar(20)  NOT NULL,                       --          (3) NULL 허용
    note       text,
    created_at timestamp    DEFAULT CURRENT_TIMESTAMP       --          (4) 기본값
);
```

두 엔진이 이 문을 그대로 받는다. **받은 뒤 서로 다르게 적어 둔다.**

```text
--- PG 18.6 ---
\d t42_a
                                Table "public.t42_a"
   Column   |            Type             | Collation | Nullable |      Default      
------------+-----------------------------+-----------+----------+-------------------
 id         | integer                     |           | not null | 
 name       | character varying(20)       |           | not null | 
 note       | text                        |           |          | 
 created_at | timestamp without time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "t42_a_pkey" PRIMARY KEY, btree (id)

--- MySQL 8.4.10 ---
SHOW CREATE TABLE t42_a\G
Create Table: CREATE TABLE `t42_a` (
  `id` int NOT NULL,
  `name` varchar(20) NOT NULL,
  `note` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

그림 해설 — 셋을 읽어 낼 수 있다.

```text
                      PG                          MySQL
PRIMARY KEY 의 효과   id 가 not null 이 됐다        id 가 NOT NULL 이 됐다   <- 양쪽 같다 (43번)
timestamp 의 정체     without time zone 이라 명시   그냥 timestamp
표 수준 속성          없다                          ENGINE·CHARSET·COLLATE 가 표에 붙는다
```

비용 — **표를 만드는 것 자체는 싸다.** 값어치는 이 정의가 **나중에 틀렸을 때** 치르는 값에 있다(아래 2번).

> **`SHOW CREATE TABLE`** — MySQL 이 **자기가 이해한 정의를 다시 SQL 로 뱉어 주는** 명령.\
> 예: 내가 `serial` 이라고 썼는데 서버가 `bigint unsigned ... AUTO_INCREMENT` 로 적어 두었다면 이 출력에서 드러난다(45번).

### 2. ★ `IF NOT EXISTS` — 두 엔진 다 되는데, **조용해지는 방식이 다르다**

**언제 쓰나** — 마이그레이션 스크립트를 여러 번 돌릴 때. **여기가 이 편에서 가장 많이 쓰이게 될 문법**이다.

먼저 **없을 때 어떻게 되는지**부터 던진다.

```text
### SQL: CREATE TABLE t42_a (id int);      (t42_a 가 이미 있는 상태)
--- PG 18.6 ---
ERROR:  relation "t42_a" already exists
--- MySQL 8.4.10 ---
ERROR 1050 (42S01) at line 1: Table 't42_a' already exists
```

`IF NOT EXISTS` 를 붙이면 둘 다 통과한다. **그런데 통과하는 모습이 다르다.**

```text
### SQL: CREATE TABLE IF NOT EXISTS t42_a (id int);
--- PG 18.6 ---
NOTICE:  relation "t42_a" already exists, skipping
CREATE TABLE
--- MySQL 8.4.10 ---
(아무 출력 없음)
```

★ **MySQL 의 「아무 출력 없음」은 「아무 일도 없었다」가 아니다.**

```text
--- MySQL 8.4.10 ---
CREATE TABLE IF NOT EXISTS t42_a (id int);
SHOW WARNINGS;
+-------+------+------------------------------+
| Level | Code | Message                      |
+-------+------+------------------------------+
| Note  | 1050 | Table 't42_a' already exists |
+-------+------+------------------------------+
```

그림 해설 — 두 엔진이 **같은 정보를 다른 통로로** 준다.

```text
                이미 있을 때 무엇을 말하나
PG     : NOTICE 를 항상 찍는다              -> 로그를 안 봐도 보인다
MySQL  : Note 1050 을 경고 버퍼에 넣는다     -> ★ SHOW WARNINGS 를 쳐야 보인다
```

대가 — **MySQL 에서 「마이그레이션이 조용히 통과했다」는 「적용됐다」의 근거가 못 된다.**\
이미 있어서 건너뛴 것인지 새로 만든 것인지가 **결과에 안 나온다.**

`DROP` 쪽도 대칭이다.

```text
### SQL: DROP TABLE t42_nope;              (없는 표)
--- PG 18.6 ---
ERROR:  table "t42_nope" does not exist
--- MySQL 8.4.10 ---
ERROR 1051 (42S02) at line 1: Unknown table 'study.t42_nope'

### SQL: DROP TABLE IF EXISTS t42_nope;
--- PG 18.6 ---
NOTICE:  table "t42_nope" does not exist, skipping
DROP TABLE
--- MySQL 8.4.10 ---
(아무 출력 없음 — SHOW WARNINGS 에 Note 1051 Unknown table 'study.t42_nope')
```

### 3. ★ DDL 이 트랜잭션에 드나 — **이 한 줄이 운영 절차를 가른다**

**언제 쓰나** — 마이그레이션을 여러 문으로 쪼갤 때. 중간에 실패하면 어떻게 되는지가 여기서 갈린다.

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
BEGIN;                                     START TRANSACTION;
CREATE TABLE t42_tx (id int);              CREATE TABLE t42_tx (id int);
SELECT count(*) FROM information_schema    ROLLBACK;
  .tables WHERE table_name='t42_tx';       SELECT count(*) ... ;

--- 실제 출력 ---                          --- 실제 출력 ---
 visible_inside                            +------------------------+
----------------                           | visible_after_rollback |
              1                            +------------------------+
ROLLBACK                                   |                      1 |
 visible_after_rollback                    +------------------------+
------------------------
                      0                     -> ROLLBACK 했는데 표가 남아 있다
 -> 흔적 없이 사라졌다
```

두 그림의 결론 — **PG 는 DDL 을 되돌릴 수 있고 MySQL 은 못 되돌린다.**\
MySQL 의 DDL 은 **암묵 커밋(implicit commit)** 이다 — 문을 받는 순간 열려 있던 트랜잭션이 커밋되고 DDL 이 확정된다.

> **암묵 커밋(implicit commit)** — 내가 `COMMIT` 을 안 썼는데 엔진이 대신 커밋하는 것.\
> 예: MySQL 에서 `START TRANSACTION; INSERT ...; CREATE TABLE ...;` 을 치면 **`INSERT` 까지 커밋된 뒤** 표가 만들어진다.

대가 — **실험 절차가 달라진다.** PG 에서는 `BEGIN ... ROLLBACK` 이 뒷정리이고,\
MySQL 에서는 `DROP TABLE IF EXISTS` 로 **직접 지우는 것 말고는 방법이 없다.**\
이 문서의 실험을 그렇게 돌렸다.

### 4. ★ `ALTER TABLE` 이 무엇을 잠그나 — 엔진이 서로 다른 말을 한다

**언제 쓰나** — 운영 중인 표를 고칠 때. **이 절이 이 주제의 실무 값어치 전부**다.

**PG 는 내가 물어보면 잠금을 보여 준다.**

```text
--- PG 18.6 ---
BEGIN;
ALTER TABLE t42_a ADD COLUMN memo text;
SELECT l.locktype, l.mode, l.granted FROM pg_locks l
  JOIN pg_class c ON c.oid=l.relation WHERE c.relname='t42_a';
 locktype |        mode         | granted 
----------+---------------------+---------
 relation | AccessExclusiveLock | t
(1 row)
ROLLBACK;
```

> **`AccessExclusiveLock`** — PG 에서 **가장 센 표 잠금**. 그 표에 대한 `SELECT` 까지 막는다.\
> 예: 이 잠금을 쥔 `ALTER` 가 5초 걸리면 그 5초 동안 그 표를 읽는 질의가 전부 대기한다.

**그런데 PG 의 `ALTER` 가 전부 비싼 것은 아니다.** 잠금은 같아도 **표를 다시 쓰느냐**가 다르다.

```text
--- PG 18.6 ---
SELECT pg_relation_filepath('t42_a') AS before;
      before      
------------------
 base/16384/16693

ALTER TABLE t42_a ADD COLUMN c1 int DEFAULT 7;
SELECT pg_relation_filepath('t42_a') AS after_add_default;
 after_add_default 
-------------------
 base/16384/16693        <- 같다. 파일을 안 다시 썼다

ALTER TABLE t42_a ALTER COLUMN c1 TYPE bigint;
SELECT pg_relation_filepath('t42_a') AS after_type_change;
 after_type_change 
-------------------
 base/16384/16705        <- 바뀌었다. 표를 통째로 다시 썼다
```

그림 해설 — **파일 경로가 바뀌었으면 그 `ALTER` 는 표 전체를 복사한 것**이다.

```text
ADD COLUMN ... DEFAULT 7   : 카탈로그에 「기본값 7」만 적는다   -> 행 수와 무관하게 순식간
ALTER COLUMN TYPE bigint   : 모든 행을 새 파일로 옮겨 적는다    -> 행 수에 비례해 오래 잠근다
```

**MySQL 은 반대로 — 내가 「이 방법으로 하라」고 요구하면 엔진이 거절하며 이유를 말한다.**

```text
--- MySQL 8.4.10 ---
ALTER TABLE t42_a ADD COLUMN c1 int DEFAULT 7, ALGORITHM=INSTANT;
(성공 — 아무 출력 없음)

ALTER TABLE t42_a MODIFY COLUMN c1 bigint, ALGORITHM=INSTANT;
ERROR 1846 (0A000) at line 1: ALGORITHM=INSTANT is not supported. Reason: Need to rebuild
  the table to change column type. Try ALGORITHM=COPY/INPLACE.

ALTER TABLE t42_a MODIFY COLUMN c1 bigint, ALGORITHM=INPLACE, LOCK=NONE;
ERROR 1846 (0A000) at line 1: ALGORITHM=INPLACE is not supported. Reason: Cannot change
  column type INPLACE. Try ALGORITHM=COPY.

ALTER TABLE t42_a MODIFY COLUMN c1 bigint, ALGORITHM=COPY, LOCK=NONE;
ERROR 1846 (0A000) at line 1: LOCK=NONE is not supported. Reason: COPY algorithm requires
  a lock. Try LOCK=SHARED.
```

(줄바꿈만 폭에 맞게 접었고, 문구는 서버가 낸 그대로다.)

★ **에러 네 줄이 사다리를 이룬다.** 「타입을 바꾸려면 표를 다시 지어야 한다 → INPLACE 로도 안 된다 → COPY 로만 된다 → COPY 는 잠금이 필요하다.」\
**요구를 거절당하는 것이 곧 그 `ALTER` 의 비용 견적서**다.

같은 요구를 PG 에 던지면 **문법 자체가 없다.**

```text
--- PG 18.6 ---
ALTER TABLE t42_a ALTER COLUMN c1 TYPE bigint, ALGORITHM=COPY;
ERROR:  syntax error at or near "ALGORITHM"
LINE 1: ALTER TABLE t42_a ALTER COLUMN c1 TYPE bigint, ALGORITHM=COP...
                                                       ^
```

두 엔진의 대비는 이렇게 읽는다.

```text
PG                                        MySQL
「무엇을 하겠다」만 적는다                  「무엇을 어떤 방법으로 하겠다」를 적는다
잠금 등급은 문서와 pg_locks 로 확인한다     엔진이 못 하겠다고 거절하며 알려 준다
안전장치 = 사전에 알아보고 가는 것           안전장치 = ALGORITHM/LOCK 을 명시해 두는 것
```

비용 — MySQL 쪽 처방이 하나 있다. **`ALGORITHM`·`LOCK` 을 항상 명시해 두면 비싼 `ALTER` 가 배포 스크립트에서 에러로 멈춘다.**\
안 적으면 엔진이 알아서 COPY 를 골라 **운영 중에 조용히 표를 잠근다.**

> **`ALGORITHM=INSTANT`** — MySQL 8.0 이 도입한, **메타데이터만 고치고 끝내는** `ALTER` 방식.\
> 예: 맨 뒤에 열을 추가하는 것은 행을 하나도 안 건드리므로 INSTANT 로 끝난다.

★ **`INSTANT` 에는 `LOCK` 을 같이 못 쓴다.** 잠그지 않기 때문이다.

```text
--- MySQL 8.4.10 ---
ALTER TABLE t42_b ADD COLUMN x int, ALGORITHM=INSTANT, LOCK=NONE;
ERROR 1221 (HY000) at line 1: Incorrect usage of ALGORITHM=INSTANT and LOCK=NONE/SHARED/EXCLUSIVE

ALTER TABLE t42_b ADD COLUMN y int, ALGORITHM=INPLACE, LOCK=NONE;
(성공 — 아무 출력 없음)
```

### 5. ★ `NOT NULL` 열을 추가하면 — **한쪽만 막는다**

**언제 쓰나** — 이미 행이 있는 표에 필수 열을 추가할 때. **실무에서 가장 자주 만나는 마이그레이션**이다.

`t42_a` 에 행이 하나 있는 상태에서 기본값 없이 `NOT NULL` 열을 붙인다.

```text
### SQL: ALTER TABLE t42_a ADD COLUMN req int NOT NULL;
--- PG 18.6 ---
ERROR:  column "req" of relation "t42_a" contains null values
--- MySQL 8.4.10 ---
(아무 출력 없음 — 성공했다)
```

★ **MySQL 은 통과했다.** 무엇이 들어갔는지 본다.

```text
--- MySQL 8.4.10 ---
SELECT id, name, req FROM t42_a;
+----+------+-----+
| id | name | req |
+----+------+-----+
|  1 | ann  |   0 |
+----+------+-----+

SHOW WARNINGS;
(아무 행도 없다)
```

그림 해설 — 기존 행의 `req` 가 **`0` 으로 채워졌다.** 내가 쓴 적 없는 값이다.\
`sql_mode` 에 `STRICT_TRANS_TABLES` 가 켜져 있는데도 **경고 한 줄 없다.**

```text
(A) PostgreSQL 18.6                    (B) MySQL 8.4.10
"기존 행을 NULL 로 채울 수 없다"        "타입의 암묵 기본값으로 채우겠다"
        ↓                                      ↓
   문이 서지 않는다                        req = 0 이 20,000행에 들어간다
        ↓                                      ↓
 나는 즉시 안다 — 기본값을 정하라          에러도 경고도 없다
                                              ↓
                                    ★ 「0 은 미지정」인지 「0 이 실제 값」인지
                                       구분할 방법이 사라진다
```

두 그림의 결론 — **PG 는 결정을 나에게 돌려주고 MySQL 은 대신 결정한다.**\
대가 — MySQL 쪽 사고는 **배포가 성공한 것처럼 보이는 상태로** 시작된다.

처방은 양쪽 다 같다. **기본값을 명시한다.**

```text
### SQL: ALTER TABLE t42_a ADD COLUMN req int NOT NULL DEFAULT 0;
--- PG 18.6 ---
ALTER TABLE
--- MySQL 8.4.10 ---
(성공)
```

이때 **`0` 은 내가 고른 값**이다. 앞 그림의 `0` 과 글자는 같아도 성질이 다르다.

### 6. ★ `DROP` 과 의존 객체 — **거절이냐 방치냐**

**언제 쓰나** — 표를 지울 때. 그 표를 가리키던 뷰·외래키가 있으면 여기서 갈린다.

`t42_a` 를 보는 뷰를 하나 만들고 표를 지운다.

```sql
CREATE VIEW v42_a AS SELECT id, name FROM t42_a;
DROP TABLE t42_a;
```

```text
(A) PostgreSQL 18.6                       (B) MySQL 8.4.10
ERROR:  cannot drop table t42_a           (아무 출력 없음 — 지워졌다)
  because other objects depend on it
DETAIL:  view v42_a depends on
  table t42_a
HINT:  Use DROP ... CASCADE to drop
  the dependent objects too.
        ↓                                          ↓
  표가 남아 있다. 뷰도 멀쩡하다               표가 없어졌다. 뷰는 「남아 있다」
```

**남아 있는 MySQL 의 뷰를 써 보면** 그때 터진다.

```text
### SQL: SELECT * FROM v42_a;
--- PG 18.6 ---
 id | name 
----+------
  1 | ann
(1 row)
--- MySQL 8.4.10 ---
ERROR 1356 (HY000) at line 1: View 'study.v42_a' references invalid table(s) or column(s)
  or function(s) or definer/invoker of view lack rights to use them
```

**뷰의 상태를 물어보면 「손상」이라고 답한다.**

```text
--- MySQL 8.4.10 ---
CHECK TABLE v42_a\G
   Table: study.v42_a
      Op: check
Msg_type: Error
Msg_text: View 'study.v42_a' references invalid table(s) or column(s) or function(s) or
          definer/invoker of view lack rights to use them
   Table: study.v42_a
      Op: check
Msg_type: error
Msg_text: Corrupt
```

그림 해설 — **MySQL 은 뷰의 의존성을 `DROP` 시점에 검사하지 않는다.**\
깨진 뷰는 `SHOW TABLES` 에 그대로 보이고, **쓰는 순간까지 아무도 모른다.**\
대가 — 배포 때 지운 표의 피해가 **다음 조회 때** 드러난다. 시점이 어긋난다.

**PG 에서 진짜로 지우려면 `CASCADE` 로 의도를 밝혀야 한다.**

```text
--- PG 18.6 ---
DROP TABLE t42_a CASCADE;
NOTICE:  drop cascades to view v42_a
DROP TABLE

SELECT * FROM v42_a;
ERROR:  relation "v42_a" does not exist
LINE 1: SELECT * FROM v42_a;
                      ^
```

**`NOTICE` 가 무엇이 같이 사라졌는지 이름을 대 준다.** 이것이 PG 쪽 안전장치다.

비용 — `CASCADE` 는 **되돌릴 수 없는 삭제를 한 단어로 허가하는 것**이다.\
PG 에서도 `BEGIN; DROP ... CASCADE;` 로 먼저 `NOTICE` 만 읽고 `ROLLBACK` 하는 것이 값싸다(3번).

## 문법 — 어느 절에서 무엇이 갈리나

SQL 의 DDL 은 **형태가 거의 같고 「받아 주느냐」만 다르다.** 그래서 갈리는 자리만 모아 둔다.

```sql
-- 표 만들기
CREATE TABLE t (...);                      -- 양쪽
CREATE TABLE IF NOT EXISTS t (...);        -- 양쪽 (PG 는 NOTICE, MySQL 은 Note 1050)
CREATE TABLE t (...) ENGINE=InnoDB;        -- MySQL 만
CREATE TEMPORARY TABLE t (...);            -- 양쪽 (PG 는 TEMP 도 됨)

-- 열 추가·변경·삭제
ALTER TABLE t ADD COLUMN c int;                           -- 양쪽
ALTER TABLE t ADD COLUMN IF NOT EXISTS c int;             -- PG 만
ALTER TABLE t ALTER COLUMN c TYPE bigint;                 -- PG
ALTER TABLE t MODIFY COLUMN c bigint;                     -- MySQL
ALTER TABLE t ALTER COLUMN c SET DEFAULT 'Z';             -- ★ 양쪽 다 받는다 (45번)
ALTER TABLE t ALTER COLUMN c SET NOT NULL;                -- PG
ALTER TABLE t MODIFY COLUMN c bigint NOT NULL;            -- MySQL (타입을 다시 적어야 한다)
ALTER TABLE t DROP COLUMN c;                              -- 양쪽
ALTER TABLE t RENAME COLUMN a TO b;                       -- 양쪽
ALTER TABLE t ..., ALGORITHM=INPLACE, LOCK=NONE;          -- MySQL 만

-- 표 지우기
DROP TABLE t;                              -- 양쪽
DROP TABLE IF EXISTS t;                    -- 양쪽
DROP TABLE t CASCADE;                      -- PG 만 (MySQL 은 파서가 받되 아무 일도 안 한다)
DROP TABLE t1, t2;                         -- 양쪽
```

- **`MODIFY COLUMN` 은 열 정의를 통째로 다시 쓴다.** MySQL 에서 타입만 바꾸려다 `NOT NULL` 을 빠뜨리면 **제약이 사라진다.**
- PG 의 `ALTER TABLE` 은 **한 문에 여러 액션을 쉼표로 이어 붙일 수 있고, 그것이 한 트랜잭션에서 원자적으로 적용**된다.

## 어디서 틀리나

1. **「`ROLLBACK` 했으니 없던 일이다」 — MySQL 에서 틀린다.**\
   DDL 은 암묵 커밋이다(3번). 실험을 했으면 **`DROP TABLE IF EXISTS` 로 직접 지운다.**
2. **「마이그레이션이 에러 없이 끝났다」 = 「적용됐다」가 아니다.**\
   `IF NOT EXISTS` 가 건너뛴 것일 수 있다. MySQL 은 **`SHOW WARNINGS` 의 Note 1050 이 유일한 통로**다(2번).
3. **「열 하나 추가는 싸다」 — 어디에 무엇을 추가하느냐에 달렸다.**\
   PG 는 `DEFAULT` 가 붙어도 파일을 안 다시 쓴다. **타입 변경은 다시 쓴다**(4번).\
   MySQL 은 `ALGORITHM=INSTANT` 가 되는지 **던져서 물어볼 수 있다.**
4. **`NOT NULL` 열 추가 — MySQL 은 막지 않는다.**\
   기존 행이 **암묵 기본값(`int` 는 `0`)** 으로 채워지고 **경고도 없다**(5번).
5. **`DROP TABLE` 후 뷰 — MySQL 은 방치한다.**\
   깨진 뷰가 `SHOW TABLES` 에 그대로 보인다. 쓰는 순간 `ERROR 1356` 이다(6번).
6. **`DROP TABLE ... CASCADE` 를 MySQL 에 썼는데 아무 일도 안 일어난다.**\
   MySQL 의 파서는 `RESTRICT`/`CASCADE` 를 **받되 무시한다.** 이식할 때 조용히 의미가 사라진다.
7. **`ALTER TABLE ... MODIFY` 로 타입만 바꾸려다 제약을 지운다.**\
   MySQL 의 `MODIFY` 는 **열 정의 전체를 교체**한다. `NOT NULL`·`DEFAULT` 를 다시 적어야 한다.

```text
--- MySQL 8.4.10 ---
CREATE TABLE t42_c (id int NOT NULL DEFAULT 5, v varchar(5));
ALTER TABLE t42_c MODIFY COLUMN id bigint;      -- 타입만 바꿀 생각이었다
SHOW CREATE TABLE t42_c\G
Create Table: CREATE TABLE `t42_c` (
  `id` bigint DEFAULT NULL,                     <- ★ NOT NULL 과 DEFAULT 5 가 사라졌다
  `v` varchar(5) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

   에러도 경고도 없다. **`SHOW CREATE TABLE` 을 다시 읽는 것이 유일한 확인 통로**다.
8. **PG 의 `ALTER TABLE` 은 어떤 액션이든 `AccessExclusiveLock` 이다.**\
   「빠른 `ALTER`」도 잠금 등급은 같다. 다른 것은 **잠근 채로 얼마나 오래 있느냐**다.

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| `IF NOT EXISTS` | 이미 있으면 에러 대신 건너뛴다 | 건너뛴 사실을 **NOTICE 로 주나 경고 버퍼로 주나** |
| DDL 과 트랜잭션 | — | **PG 는 롤백 가능, MySQL 은 암묵 커밋** |
| `ALTER TABLE` | 결과 스키마가 어떻게 되는지 | **무엇을 얼마나 잠그나 · 표를 다시 쓰나** |
| `NOT NULL` 열 추가 | 추가 후 그 열은 NULL 을 못 받는다 | **기존 행을 무엇으로 채우나(또는 거부하나)** |
| `DROP TABLE` | 표가 사라진다 | **의존 객체를 막나 · 방치하나 · 같이 지우나** |

- **`pg_relation_filepath` 가 바뀌었다**는 것은 PG 의 구현 세부다. 「표를 다시 썼다」는 **관찰이지 문서의 보장이 아니다.**
- **MySQL 의 `ERROR 1846` 문구**(「Try ALGORITHM=COPY/INPLACE」)도 버전에 따라 달라질 수 있는 구현 세부다.\
  외울 것은 문구가 아니라 「**타입 변경은 표를 다시 짓는다**」는 성질이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 마이그레이션에 `IF NOT EXISTS`/`IF EXISTS`.** 재실행 가능해진다.\
  단 **적용됐는지 여부는 따로 확인**한다(MySQL 은 `SHOW WARNINGS`).
- **쓴다 — MySQL 에서 `ALGORITHM`·`LOCK` 명시.** 비싼 `ALTER` 가 **배포 전에 에러로 멈춘다.**
- **쓴다 — PG 에서 `BEGIN; DDL; ROLLBACK;` 으로 먼저 던져 본다.** `NOTICE` 와 에러를 공짜로 읽는다.
- **안 쓴다 — 운영 중 표에 타입 변경.** 양쪽 다 표를 다시 쓴다. 새 열을 추가해 옮기는 쪽이 싸다.
- **안 쓴다 — 기본값 없는 `NOT NULL` 열 추가.** PG 는 막고 MySQL 은 **조용히 `0` 을 넣는다.**
- **조심한다 — `DROP TABLE ... CASCADE`.** PG 에서 **뷰·외래키가 한 단어로 같이 사라진다.**
- **조심한다 — MySQL 에서 표를 지운 뒤 뷰.** 깨진 채 남는다. 지운 표를 가리키는 뷰를 **같이 찾아 지운다.**

## 핵심 문장

- **`CREATE TABLE` 은 싸고 `ALTER TABLE` 은 비싸다.** 비용은 크기가 아니라 **표를 다시 쓰느냐**에 달렸다.
- **PG 의 DDL 은 트랜잭션에 들고 MySQL 의 DDL 은 암묵 커밋이다.** 실험 뒷정리 방법이 여기서 갈린다.
- **PG 의 `ALTER TABLE` 은 언제나 `AccessExclusiveLock` 이다.** 다른 것은 잠근 시간이다.
- **MySQL 은 `ALGORITHM`/`LOCK` 을 요구하면 못 하겠다고 거절하며 이유를 말한다** — 그 에러가 곧 비용 견적서다.
- **기본값 없는 `NOT NULL` 열 추가를 PG 는 막고 MySQL 은 `0` 으로 채운다 — 경고도 없다.**
- **`DROP` 의 의존성 검사를 PG 는 하고 MySQL 은 안 한다.** MySQL 의 뷰는 깨진 채 남는다.

## 관련 자료

- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — 열 타입을 잘못 고르면 무슨 일이 나는지가 거기다.\
  **거기는 「값이 어떻게 변환되나」까지, 여기는 「그 타입을 스키마에 어떻게 적나」부터.**
- [43 기본키·UNIQUE 제약과 NULL](../43-primary-key-unique-and-null/) — `CREATE TABLE` 에 붙는 제약의 첫 갈래.
- [45 CHECK·NOT NULL·DEFAULT·생성 열](../45-check-not-null-default-generated-columns/) — 열 하나에 붙는 나머지 제약 전부.
- [46 인덱스 정의](../46-index-definition-composite-partial-expression/) — 표에 붙는 객체 중 제약이 아닌 것.
- [`systems/partitioning-vs-sharding`](../../../../../systems/partitioning-vs-sharding/) — **그쪽은 표를 여러 조각·여러 노드로 나누는 전략까지, 여기는 표 하나의 정의 문법까지.**\
  「표가 커지면 어떻게 쪼개나」는 한 줄도 여기서 다루지 않는다.
- [SQL 주제 목록](../README.md) — 44(외래키) · 48(뷰) · 49(INSERT) 가 이웃이다.

## 용어 풀이

- **DDL(Data Definition Language)** — 데이터가 아니라 데이터의 모양을 바꾸는 문. `CREATE`·`ALTER`·`DROP`.\
  예: `DELETE FROM t` 는 행을 비우고 `DROP TABLE t` 는 표 자체를 없앤다.
- **암묵 커밋(implicit commit)** — 내가 `COMMIT` 을 안 썼는데 엔진이 대신 커밋하는 것.\
  예: MySQL 에서 DDL 을 치면 열려 있던 트랜잭션이 그 자리에서 커밋된다.
- **`AccessExclusiveLock`** — PG 의 가장 센 표 잠금. 그 표에 대한 `SELECT` 까지 막는다.\
  예: 이 잠금을 5초 쥐면 그 5초 동안 그 표를 읽는 질의가 전부 대기한다.
- **표 다시 쓰기(rewrite)** — 모든 행을 새 파일에 복사해 옮기는 것.\
  예: `ALTER COLUMN ... TYPE bigint` 는 int 4바이트를 bigint 8바이트로 바꿔 적어야 하므로 전부 옮긴다.
- **`pg_relation_filepath(표)`** — PG 에서 그 표의 데이터 파일 경로를 돌려주는 함수.\
  예: `ALTER` 전후로 값이 바뀌었으면 표를 다시 쓴 것이다.
- **`ALGORITHM=INSTANT` / `INPLACE` / `COPY`** — MySQL 이 `ALTER` 를 수행하는 세 방식.\
  예: 맨 뒤에 열을 붙이는 것은 `INSTANT`, 타입을 바꾸는 것은 `COPY` 로만 된다.
- **`ERROR 1846`** — MySQL 이 「요구한 ALGORITHM/LOCK 으로는 못 한다」고 거절하는 코드.\
  예: `Reason: Need to rebuild the table to change column type` 은 그 `ALTER` 가 비싸다는 뜻이다.
- **의존 객체(dependent object)** — 그 표를 가리키는 다른 객체. 뷰·외래키·시퀀스가 대표적이다.\
  예: `CREATE VIEW v AS SELECT ... FROM t` 의 `v` 는 `t` 에 의존한다.
- **`CASCADE`** — 의존 객체까지 같이 지우겠다는 선언.\
  예: PG 의 `DROP TABLE t CASCADE` 는 `t` 를 보던 뷰도 함께 지우고 `NOTICE` 로 이름을 알려 준다.
- **`ERROR 1356`** — MySQL 에서 **깨진 뷰**를 조회할 때 나는 에러.\
  예: 뷰가 보던 표가 사라졌는데 뷰는 남아 있을 때 나온다.
- **`STRICT_TRANS_TABLES`** — MySQL 의 `sql_mode` 값 중 하나. 잘못된 값 입력을 에러로 올린다.\
  예: 이 모드가 켜져 있어도 **`ALTER` 의 열 추가에는 적용되지 않는다**(5번에서 실측).

## 더 들어가면

- **PG 의 `ADD COLUMN ... DEFAULT` 가 싼 것은 PG 11 부터다.** 그 전에는 표를 다시 썼다.\
  이 머신에 PG 10 컨테이너가 없어 **직접 던져 보지 못했다** — 18.6 의 관찰만 실었다.
- **PG 의 `ALTER TABLE` 은 잠금 등급이 일정하지만, 잠금을 *기다리는* 동안 뒤의 질의가 전부 막힌다.**\
  그래서 운영에서는 `lock_timeout` 을 짧게 걸고 실패하면 재시도하는 절차를 쓴다.
- **MySQL 의 `ALGORITHM=INSTANT` 는 표당 누적 한도가 있다.** 열을 계속 INSTANT 로 붙이면 언젠가 거절당한다.\
  그때의 에러 문구는 **이 실험에서 재현하지 못했다**(한도에 도달할 만큼 열을 붙이지 않았다).
- **`DROP TABLE` 은 어느 엔진에서도 롤백의 대상이 아니라 「복구의 대상**」이다.\
  PG 에서 `BEGIN` 안이라면 되돌아가지만, 커밋된 뒤에는 백업에서 되살리는 수밖에 없다.
