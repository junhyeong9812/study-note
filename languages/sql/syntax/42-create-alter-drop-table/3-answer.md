# sql/42-테이블 정의와 변경 (CREATE·ALTER·DROP) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 이 편이 만든 표(`t42_a`·`t42_b`·`t42_c`·`t42_tx`·뷰 `v42_a`)는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> 문서 근거는 [PG 18 CREATE TABLE](https://www.postgresql.org/docs/18/sql-createtable.html) · [PG 18 ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html) · [MySQL 8.4 ALTER TABLE](https://dev.mysql.com/doc/refman/8.4/en/alter-table.html) · [MySQL 8.4 Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 이미 있는 표를 또 만들면 — **양쪽 다 에러, 양쪽 다 `IF NOT EXISTS` 지원**

**출력**

```text
### SQL: CREATE TABLE t42_a (id int);          (t42_a 가 이미 있다)
--- PG 18.6 ---
ERROR:  relation "t42_a" already exists
--- MySQL 8.4.10 ---
ERROR 1050 (42S01) at line 1: Table 't42_a' already exists
```

```text
### SQL: CREATE TABLE IF NOT EXISTS t42_a (id int);
--- PG 18.6 ---
NOTICE:  relation "t42_a" already exists, skipping
CREATE TABLE
--- MySQL 8.4.10 ---
(아무 출력 없음)
```

**왜 그런가**

`IF NOT EXISTS` 는 **두 엔진 다 지원한다.** 「미지원」을 단정하기 전에 던져 본 결과다.\
갈리는 것은 **건너뛴 사실을 어떻게 알리느냐**다.

```text
PG     : NOTICE 를 표준 출력 경로로 항상 찍는다
MySQL  : Note 1050 을 경고 버퍼에 넣고 화면에는 아무것도 안 낸다
```

`DROP` 쪽도 대칭으로 지원된다.

```text
### SQL: DROP TABLE t42_nope;
--- PG 18.6 ---
ERROR:  table "t42_nope" does not exist
--- MySQL 8.4.10 ---
ERROR 1051 (42S02) at line 1: Unknown table 'study.t42_nope'

### SQL: DROP TABLE IF EXISTS t42_nope;
--- PG 18.6 ---
NOTICE:  table "t42_nope" does not exist, skipping
DROP TABLE
--- MySQL 8.4.10 ---
(아무 출력 없음)
```

---

### 2. ★ MySQL 이 「아무 말 없이」 통과했을 때 — **`SHOW WARNINGS` 가 유일한 통로다**

**출력**

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

`DROP TABLE IF EXISTS t42_nope;` 뒤에도 같은 통로로 나온다.

```text
--- MySQL 8.4.10 ---
+-------+------+--------------------------------+
| Level | Code | Message                        |
+-------+------+--------------------------------+
| Note  | 1051 | Unknown table 'study.t42_nope' |
+-------+------+--------------------------------+
```

**왜 그런가**

MySQL 은 **`Note` 수준의 진단을 결과에 안 싣는다.** 화면에 아무것도 안 나온 것은\
「아무 일도 없었다」가 아니라 「**할 말이 있는데 물어보지 않았다**」이다.

```text
마이그레이션 스크립트가 조용히 끝났다
        ↓
(a) 새로 만들었다   (b) 이미 있어서 건너뛰었다
        ↓
결과만 봐서는 구분이 안 된다 -> SHOW WARNINGS 로 물어야 한다
```

같은 성질의 사고를 [35 타입 체계](../35-type-system-and-casting/)(경고 1292·1739)와\
[39 collation](../39-collation/)(경고 1739)에서도 봤다 — **MySQL 에서 「조용함」은 신호가 아니다.**

---

### 3. ★ 트랜잭션 안에서 표를 만들고 되돌리면 — **PG 는 사라지고 MySQL 은 남는다**

**출력**

```text
--- PG 18.6 ---
BEGIN
CREATE TABLE
 visible_inside 
----------------
              1
(1 row)
ROLLBACK
 visible_after_rollback 
------------------------
                      0
(1 row)
```

```text
--- MySQL 8.4.10 ---
START TRANSACTION; CREATE TABLE t42_tx (id int); ROLLBACK;
SELECT count(*) AS visible_after_rollback FROM information_schema.tables
  WHERE table_schema='study' AND table_name='t42_tx';
+------------------------+
| visible_after_rollback |
+------------------------+
|                      1 |
+------------------------+
```

**왜 그런가**

PG 의 DDL 은 **다른 문과 똑같이 트랜잭션의 일부**다. 카탈로그 변경도 MVCC 로 관리된다.\
MySQL 의 DDL 은 **암묵 커밋**이라 `ROLLBACK` 의 사정권 밖에 있다.

```text
PG      BEGIN ─ CREATE TABLE ─ ROLLBACK   -> 카탈로그 변경까지 되감긴다
MySQL   BEGIN ─ CREATE TABLE ─ ROLLBACK
                      ↑
              여기서 이미 커밋됐다. ROLLBACK 이 되감을 것이 없다
```

**이 한 줄이 실험 절차를 정한다** — 12번 참조.

---

### 4. ★ 이 `ALTER` 가 표를 다시 쓰나 — **`DEFAULT` 추가는 안 쓰고, 타입 변경은 쓴다**

**출력**

```text
--- PG 18.6 ---
SELECT pg_relation_filepath('t42_a') AS before;
      before      
------------------
 base/16384/16693
(1 row)

ALTER TABLE
 after_add_default 
-------------------
 base/16384/16693
(1 row)

ALTER TABLE
 after_type_change 
-------------------
 base/16384/16705
(1 row)
```

**왜 그런가**

확인 수단이 답의 절반이다 — **`pg_relation_filepath()` 가 바뀌었는지 본다.**

```text
ADD COLUMN c1 int DEFAULT 7
  -> 카탈로그에 「이 열의 기본값은 7」만 적는다
  -> 기존 행의 바이트는 그대로. 읽을 때 없는 값을 7 로 보여 준다
  -> 파일 경로 그대로:  base/16384/16693

ALTER COLUMN c1 TYPE bigint
  -> int 4바이트를 bigint 8바이트로 바꿔 적어야 한다
  -> 모든 행을 새 파일로 복사한다
  -> 파일 경로가 바뀐다:  base/16384/16693 -> base/16384/16705
```

> **`pg_relation_filepath(표)`** — 그 표의 데이터 파일 경로를 돌려주는 PG 함수.\
> 예: `ALTER` 전후 값이 다르면 그 `ALTER` 는 표를 통째로 복사한 것이다.

**주의** — 이것은 **PG 의 구현 세부이고 관찰이다.** 「파일 경로가 안 바뀌면 싸다」는 이 서버에서 본 것이고,\
어떤 `ALTER` 가 다시 쓰는지는 버전에 따라 달라진다(`ADD COLUMN ... DEFAULT` 가 싼 것은 PG 11 부터다 — **PG 10 을 직접 던져 보지는 못했다**).

---

### 5. ★ MySQL 에게 방법을 지정하면 — **거절 세 번이 사다리를 이룬다**

**출력**

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

**왜 그런가**

세 에러를 이어 읽으면 **그 `ALTER` 의 비용 견적서**가 된다.

```text
INSTANT 로?  -> 안 된다. 표를 다시 지어야 한다
INPLACE 로?  -> 안 된다. 타입 변경은 INPLACE 가 못 한다
COPY 로,     -> 된다.
  잠금 없이?  -> 안 된다. COPY 는 잠금이 필요하다
        ↓
결론: 이 ALTER 는 "표 전체 복사 + 잠금" 이다. 운영 중에 치면 안 된다
```

★ **이것이 「에러도 출력이다」의 실무형이다.** 거절 문구가 계획서 역할을 한다.

같은 요구를 PG 에 던지면 **그런 절이 없다.**

```text
--- PG 18.6 ---
ALTER TABLE t42_a ALTER COLUMN c1 TYPE bigint, ALGORITHM=COPY;
ERROR:  syntax error at or near "ALGORITHM"
LINE 1: ALTER TABLE t42_a ALTER COLUMN c1 TYPE bigint, ALGORITHM=COP...
                                                       ^
```

**`INSTANT` 에는 `LOCK` 을 같이 못 쓴다** — 잠그지 않기 때문이다.

```text
--- MySQL 8.4.10 ---
ALTER TABLE t42_b ADD COLUMN x int, ALGORITHM=INSTANT, LOCK=NONE;
ERROR 1221 (HY000) at line 1: Incorrect usage of ALGORITHM=INSTANT and LOCK=NONE/SHARED/EXCLUSIVE

ALTER TABLE t42_b ADD COLUMN y int, ALGORITHM=INPLACE, LOCK=NONE;
(성공 — 아무 출력 없음)

ALTER TABLE t42_b ADD INDEX (v), ALGORITHM=INPLACE, LOCK=NONE;
(성공 — 아무 출력 없음)
```

---

### 6. PG 의 `ALTER TABLE` 은 무엇을 잠그나 — **`AccessExclusiveLock`. 읽기까지 막힌다**

**출력**

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

**왜 그런가**

`AccessExclusiveLock` 은 PG 의 **가장 센 표 잠금**이라 `SELECT` 까지 막는다.\
그래서 PG 의 `ALTER TABLE` 은 **등급으로는 전부 똑같이 비싸다.**

```text
잠금 "등급"   : 어떤 ALTER 든 AccessExclusiveLock   <- 같다
잠금 "시간"   : 표를 다시 쓰면 행 수에 비례          <- 여기가 갈린다 (4번)
```

그래서 PG 쪽 실무 규칙은 「**잠금을 약하게」가 아니라 「잠근 시간을 짧게**」다.\
표를 다시 쓰지 않는 형태(`ADD COLUMN ... DEFAULT`)를 고르는 것이 처방이다.

(같은 문서 안의 반증 — `CREATE INDEX` 는 `ALTER TABLE` 이 아니라서 더 약한 `ShareLock` 을 잡는다.\
[46 인덱스 정의](../46-index-definition-composite-partial-expression/)에 출력이 실려 있다.)

---

### 7. ★ 행이 있는 표에 `NOT NULL` 열을 추가하면 — **PG 는 거부, MySQL 은 `0` 으로 채운다**

**출력**

```text
### SQL: ALTER TABLE t42_a ADD COLUMN req int NOT NULL;      (행이 1개 있는 상태)
--- PG 18.6 ---
ERROR:  column "req" of relation "t42_a" contains null values
--- MySQL 8.4.10 ---
(아무 출력 없음 — 성공했다)
```

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

**왜 그런가**

MySQL 은 기존 행을 **타입의 암묵 기본값**으로 채운다. `int` 는 `0`, `varchar` 는 빈 문자열이다.\
★ **`sql_mode` 에 `STRICT_TRANS_TABLES` 가 켜져 있는데도 경고조차 없다** — 이 서버의 `sql_mode` 는

```text
ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,
ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION
```

이다. 엄격 모드는 **`INSERT`/`UPDATE` 의 값 검사**에 걸리는 것이고, **`ALTER` 의 열 추가에는 걸리지 않는다.**

무엇이 나쁜가 —

```text
req = 0 이 들어간 뒤에는
  "아직 값을 안 정한 행"과 "진짜로 0 인 행"이 구분되지 않는다
        ↓
나중에 이 열로 집계하면 조용히 틀린 답이 나온다
```

**처방** — 기본값을 명시한다. 그러면 `0` 은 **내가 고른 값**이 된다.

```text
### SQL: ALTER TABLE t42_a ADD COLUMN req int NOT NULL DEFAULT 0;
--- PG 18.6 ---
ALTER TABLE
--- MySQL 8.4.10 ---
(성공)
```

---

### 8. ★ 표를 가리키는 뷰가 있는데 표를 지우면 — **PG 는 거절, MySQL 은 방치**

**출력**

```text
### SQL: CREATE VIEW v42_a AS SELECT id, name FROM t42_a;
--- PG 18.6 ---
CREATE VIEW
--- MySQL 8.4.10 ---
(성공)
```

```text
### SQL: DROP TABLE t42_a;
--- PG 18.6 ---
ERROR:  cannot drop table t42_a because other objects depend on it
DETAIL:  view v42_a depends on table t42_a
HINT:  Use DROP ... CASCADE to drop the dependent objects too.
--- MySQL 8.4.10 ---
(아무 출력 없음 — 지워졌다)
```

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

**왜 그런가**

PG 는 **카탈로그에 의존 그래프를 갖고 있고** `DROP` 때 그것을 검사한다.\
MySQL 의 뷰는 **정의 문자열을 저장할 뿐** 표와 묶여 있지 않다. 그래서 표만 사라지고 뷰는 남는다.

**MySQL 의 깨진 뷰는 목록에도 보이고 상태를 물어야만 드러난다.**

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

★ **피해 시점이 어긋난다.** 표를 지운 배포는 성공하고, **다음에 그 뷰를 읽는 사람이 장애를 만난다.**

---

### 9. `CASCADE` 는 어디까지 지우나 — **의존 객체까지. `NOTICE` 로 이름을 댄다**

**출력**

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

**왜 그런가**

`CASCADE` 는 **「의존 객체까지 지워도 좋다」는 허가**다. PG 는 지우기 전에 **무엇이 같이 사라지는지 이름을 댄다.**

```text
DROP TABLE t CASCADE
        ↓
NOTICE: drop cascades to view v42_a    <- 여기가 유일한 사전 고지다
        ↓
표 + 뷰가 함께 사라진다 (커밋되면 복구 불가)
```

**값싼 절차** — PG 의 DDL 은 트랜잭션에 드니까(3번) 이렇게 먼저 읽는다.

```sql
BEGIN;
DROP TABLE t CASCADE;     -- NOTICE 로 무엇이 딸려 나가는지 읽는다
ROLLBACK;                 -- 실제로는 안 지운다
```

**MySQL 에서는 `CASCADE` 가 아무 의미가 없다.** 파서는 받지만 동작이 달라지지 않는다.

```text
### SQL: DROP TABLE t42_c CASCADE;
--- PG 18.6 ---
DROP TABLE
--- MySQL 8.4.10 ---
(성공 — 그냥 지워졌다. 의존 객체 검사 자체가 없으므로 CASCADE 가 바꿀 것이 없다)
```

---

### 10. MySQL 에서 타입만 바꾸려 했는데 — **`NOT NULL` 과 `DEFAULT` 가 사라진다**

**출력**

```text
--- MySQL 8.4.10 ---
CREATE TABLE t42_c (id int NOT NULL DEFAULT 5, v varchar(5));
ALTER TABLE t42_c MODIFY COLUMN id bigint;
SHOW CREATE TABLE t42_c\G
Create Table: CREATE TABLE `t42_c` (
  `id` bigint DEFAULT NULL,
  `v` varchar(5) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

**왜 그런가**

MySQL 의 `MODIFY COLUMN` 은 **열 정의를 통째로 교체**한다. 안 적은 것은 지워진다.

```text
(내가 쓴 것)                      (서버가 이해한 것)
MODIFY COLUMN id bigint     =     "id 의 정의는 이제 'bigint' 뿐이다"
                                   -> NOT NULL 없음, DEFAULT 없음
```

PG 의 `ALTER COLUMN ... TYPE` 은 **타입만 건드리고 나머지는 유지**한다 — 성격이 다르다.

★ **에러도 경고도 없다.** `SHOW CREATE TABLE` 을 다시 읽는 것이 유일한 확인 통로다.\
처방은 하나 — **`MODIFY` 에는 원래 정의를 전부 다시 적는다.**

```sql
ALTER TABLE t42_c MODIFY COLUMN id bigint NOT NULL DEFAULT 5;
```

---

### 11. 이식할 때 먼저 찾을 것 — **에러 나는 쪽이 안전하다**

**에러가 나서 안전한 것** (배포 전에 드러난다)

```text
PG 문법                                    MySQL 에서
─────────────────────────────────────      ──────────────────────────────────────
ALTER TABLE t ALTER COLUMN c TYPE ...      문법 에러 -> MODIFY 로 고쳐야 한다
ALTER TABLE t ADD COLUMN IF NOT EXISTS c   ERROR 1064 (지원 안 함)
CREATE INDEX ... (lower(v))                ERROR 1064 (46번)
CREATE INDEX ... WHERE ...                 ERROR 1064 (부분 인덱스 — 46번)
UNIQUE ... NULLS NOT DISTINCT              ERROR 1064 (43번)
```

실제 출력 하나를 둔다.

```text
### SQL: ALTER TABLE t42_c ADD COLUMN IF NOT EXISTS w int;
--- PG 18.6 ---
ALTER TABLE
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'IF NOT EXISTS w int' at line 1
```

**★ 에러가 안 나서 위험한 것** (배포는 성공하고 의미만 달라진다)

```text
1. DROP TABLE t CASCADE          MySQL 은 받되 아무 일도 안 한다 (9번)
2. NOT NULL 열 추가              PG 는 거부, MySQL 은 0 으로 채운다 (7번)
3. ALTER ... MODIFY 로 타입 변경  제약이 조용히 사라진다 (10번)
4. DROP TABLE 후 남은 뷰          MySQL 은 깨진 채 방치한다 (8번)
5. CREATE TABLE IF NOT EXISTS    MySQL 은 건너뛴 사실을 화면에 안 낸다 (2번)
```

**둘의 성질이 다르다.** 위 다섯은 **전부 결과가 「성공」으로 보인다.**\
같은 구조의 함정을 [35 타입 체계](../35-type-system-and-casting/)의 `CAST(123 AS CHAR)` 에서도 봤다 —\
**양쪽 다 통과하는데 답이 다른 것**이 가장 늦게 발견된다.

---

### 12. 실험 뒷정리는 어떻게 하나 — **PG 는 롤백, MySQL 은 직접 삭제**

**3번이 이 답의 근거다.**

```text
PostgreSQL                                  MySQL
BEGIN;                                      -- 트랜잭션은 소용없다
  CREATE TABLE t42_x (...);                 CREATE TABLE t42_x (...);
  ... 실험 ...                              ... 실험 ...
ROLLBACK;                                   DROP TABLE IF EXISTS t42_x;
   ↓                                            ↓
흔적 없이 사라진다                            직접 지워야 사라진다
```

**그래도 PG 에서도 실제로는 `DROP` 을 같이 쓴다.** 이유가 둘이다.

1. `CREATE INDEX CONCURRENTLY` 처럼 **트랜잭션 안에서 아예 못 도는 문**이 있다(46번).
2. `psql -c` 로 문을 하나씩 던지면 **문마다 트랜잭션이 따로 열리고 닫힌다** — `BEGIN` 이 이어지지 않는다.

**확인이 뒷정리의 일부다.** 지웠다고 믿지 말고 목록을 찍는다.

```text
--- PG 18.6 ---
\dt
          List of tables
 Schema | Name | Type  |  Owner   
--------+------+-------+----------
 public | dept | table | postgres
 public | emp  | table | postgres
(2 rows)
```

(이 편의 최종 뒷정리 확인 출력은 이 묶음의 마지막 편인\
[47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)의 「실행 검증」에 두 엔진 것이 함께 실려 있다.)

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `CREATE TABLE` + 정의 조회 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `\d` · `SHOW CREATE TABLE` |
| `IF NOT EXISTS` (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 다 지원 — 던져서 확인했다** |
| `DROP TABLE IF EXISTS` (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 없는 표에 던졌다 |
| Note 1050 · Note 1051 (2번) | MySQL 8.4.10 | 2회 | **`SHOW WARNINGS` 가 근거다** |
| 트랜잭션 안의 DDL (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL 의 잔존 표가 근거다** |
| `pg_relation_filepath` 전후 (4번) | PG 18.6 | 3회 | 같은 세션에서 연속 조회 |
| `ALGORITHM`·`LOCK` 절 (5번) | MySQL 8.4.10 | 6회 | **에러 1846 세 줄 + 1221 이 근거다** |
| `ALGORITHM` 을 PG 에 (5번) | PG 18.6 | 1회 | 문법 에러 |
| `pg_locks` 조회 (6번) | PG 18.6 | 1회 | `BEGIN ... ROLLBACK` 안에서 |
| `NOT NULL` 열 추가 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL 의 `req=0` 과 빈 `SHOW WARNINGS` 가 근거다** |
| `sql_mode` 조회 (7번) | MySQL 8.4.10 | 1회 | `STRICT_TRANS_TABLES` 켜져 있음을 확인 |
| 뷰 + `DROP TABLE` (8번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **에러 1356 · `CHECK TABLE` 이 근거다** |
| `DROP ... CASCADE` (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 의 NOTICE 가 근거다** |
| `MODIFY COLUMN` (10번) | MySQL 8.4.10 | 1회 | **`SHOW CREATE TABLE` 대조가 근거다** |
| `ADD COLUMN IF NOT EXISTS` (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `RENAME COLUMN` (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **양쪽 다 된다** |
| `CREATE TEMPORARY TABLE` (문법표) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 양쪽 다 된다 |
| 표 목록 확인 (12번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 실험 전·후 |

**구현 의존 항목** — 4번(`pg_relation_filepath`)·5번(`ERROR 1846` 문구)·6번(잠금 등급)·7번(암묵 기본값).\
문구와 파일 경로는 버전에 따라 바뀔 수 있다. 외울 것은 「**타입 변경은 표를 다시 짓는다**」는 성질이다.

**언어 보장 항목** — 1·3·8·9·10·11번.\
`IF NOT EXISTS` 의 의미, DDL 의 트랜잭션 취급, 의존 객체 검사 여부, `MODIFY` 가 정의를 교체한다는 것은\
두 매뉴얼의 `CREATE TABLE`·`ALTER TABLE`·`DROP TABLE` 페이지가 정한 것이다.

**버전을 적은 자리** — `ALGORITHM=INSTANT` 는 MySQL 8.0 부터다.\
**버전을 못 적은 자리** — `ADD COLUMN ... DEFAULT` 가 표를 안 다시 쓰는 것이 PG 몇 버전부터인지는\
**이 머신에 옛 버전 컨테이너가 없어 직접 확인하지 못했다.** 릴리스 노트를 열지 않았으므로 단정하지 않는다.

**DB 잔재** — 없다. `t42_a`·`t42_b`·`t42_c`·`t42_tx` 와 뷰 `v42_a` 는 전부 삭제했고,\
`emp`·`dept` 는 **읽지도 쓰지도 않았다.**
