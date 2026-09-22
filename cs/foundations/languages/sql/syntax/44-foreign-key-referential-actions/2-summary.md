# sql/44-외래키와 참조 동작 (ON DELETE·ON UPDATE) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Constraints (Foreign Keys)](https://www.postgresql.org/docs/18/ddl-constraints.html#DDL-CONSTRAINTS-FK) · [PostgreSQL 18 · CREATE TABLE](https://www.postgresql.org/docs/18/sql-createtable.html) · [MySQL 8.4 · FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **환경 확인** — MySQL 의 `@@foreign_key_checks` 는 **`1`(켜짐)** 이었다. 이 값이 `0` 이면 아래 본문 전체가 성립하지 않으므로 먼저 밝힌다.\
> **버전** — 이 주제의 동작에 「어느 버전부터」가 붙는 것을 두 매뉴얼에서 찾지 못해 **적지 않는다.**\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 `t44_p`·`t44_c`·`t44_noaction`·`t44_restrict`·`t44_cascade`·`t44_setnull`·`t44_snn`·`t44_np`·`t44_up`·`t44_uc`·`t44_dp`·`t44_dna`·`t44_dre` 를 만들었고 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> **선행** — [43 기본키·UNIQUE 제약과 NULL](../43-primary-key-unique-and-null/) — 외래키는 거기서 만든 키를 가리킨다.

## 한눈에 — 쉽게 말하면

**외래키 = 「저쪽에 없는 것을 가리키지 않겠다」는 약속.**

```text
도서관 대출 장부                        책 목록
+------+---------+                     +------+--------+
| 대출 | 책번호  |  ──가리킨다──>      | 번호 | 제목   |
|   1  |   10    |                     |  10  | SQL    |
|   2  |   99    |  ← ★ 없는 책        |  20  | 자료구조|
+------+---------+                     +------+--------+

"똑같은 구조다"

주문 상세 -> 주문 · 사원 -> 부서 · 댓글 -> 게시글
```

약속을 지키는 방법은 셋뿐이다. **누군가 부모를 지우려 할 때 무엇을 하느냐**가 전부다.

```text
                      부모 행을 지우려 한다
                              ↓
           ┌──────────────────┼──────────────────┐
           ↓                  ↓                  ↓
      막는다              같이 지운다          끊는다
  NO ACTION/RESTRICT      CASCADE            SET NULL
```

| 비유 | 실체 |
|---|---|
| 책 목록 | 부모 표 — 참조당하는 쪽 |
| 대출 장부 | 자식 표 — 참조하는 쪽 |
| 없는 책 번호를 적는다 | FK 위반 — 삽입 쪽 |
| 대출 중인 책을 목록에서 뺀다 | FK 위반 — 삭제 쪽 |
| 「대출 중이라 못 뺍니다」 | `NO ACTION` / `RESTRICT` |
| 「책을 빼면서 대출 기록도 지웁니다」 | `CASCADE` |
| 「대출 기록은 두되 책번호를 비웁니다」 | `SET NULL` |

> **참조 무결성(referential integrity)** — 자식이 가리키는 부모가 **반드시 존재한다**는 성질.\
> 예: `orders.customer_id` 에 든 값은 전부 `customers.id` 에 있어야 한다.

★ **이 편에서 가장 값비싼 한 줄** — MySQL 에서 **외래키를 열 뒤에 붙이면 아무 일도 안 일어난다.**\
문법 에러도 경고도 없이 **제약이 사라진다.** 아래 1번에서 실측했다.

## 이 주제가 답하려는 질문

1. **외래키는 무엇을 막나?** — 삽입 쪽과 삭제 쪽 **둘 다** 막는다.
2. **★ `ON DELETE` 네 동작은 각각 무엇을 하나?** — `NO ACTION`/`RESTRICT`/`CASCADE`/`SET NULL`.
3. **외래키는 인덱스를 요구하나?** — 한 엔진은 만들어 주고 한 엔진은 안 만든다.

## 예시 데이터 — 이 묶음이 공유하는 것

이 편도 표를 직접 만들었다가 지운다. **부모 하나에 자식 여럿**이라는 모양이다.

```text
t44_p (부모)                자식들 — ON DELETE 만 서로 다르다
+----+-------+              t44_c          (절 없음 = 기본)
| id | name  |              t44_noaction   ON DELETE NO ACTION
+----+-------+              t44_restrict   ON DELETE RESTRICT
| 10 | sales |              t44_cascade    ON DELETE CASCADE
| 20 | dev   |              t44_setnull    ON DELETE SET NULL
| 30 | a     |
| 40 | b     |              네 자식이 각각 다른 부모 행을 가리키게 해서
| 50 | c     |              한 동작만 따로 발동시킬 수 있게 했다
| 60 | d     |                t44_noaction -> 30   t44_cascade -> 50
+----+-------+                t44_restrict -> 40   t44_setnull -> 60
```

## 동작 방식

### 1. ★★ MySQL 의 **열 뒤 `REFERENCES` 는 무시된다** — 제약이 조용히 사라진다

**언제 쓰나** — 외래키를 선언할 때. **이 절을 모르면 이 주제 전체가 무의미해진다.**

PG 문법을 그대로 MySQL 에 던졌다.

```sql
CREATE TABLE t44_c (id int PRIMARY KEY, pid int REFERENCES t44_p(id), name varchar(10));
```

**두 엔진 다 `CREATE TABLE` 이 성공했다.** 그런데 만들어진 것이 다르다.

```text
--- PG 18.6 ---
\d t44_c
Foreign-key constraints:
    "t44_c_pid_fkey" FOREIGN KEY (pid) REFERENCES t44_p(id)

--- MySQL 8.4.10 ---
SHOW CREATE TABLE t44_c\G
Create Table: CREATE TABLE `t44_c` (
  `id` int NOT NULL,
  `pid` int DEFAULT NULL,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        ↑
   ★ 외래키가 없다. REFERENCES 구절이 통째로 사라졌다
```

**결과를 던져 확인했다.**

```text
### SQL: INSERT INTO t44_c VALUES (3,99,'cho');      (부모에 99 는 없다)
--- PG 18.6 ---
ERROR:  insert or update on table "t44_c" violates foreign key constraint "t44_c_pid_fkey"
DETAIL:  Key (pid)=(99) is not present in table "t44_p".
--- MySQL 8.4.10 ---
(성공 — 고아 행이 들어갔다)

### SQL: DELETE FROM t44_p WHERE id=10;              (자식이 가리키는 중이다)
--- PG 18.6 ---
ERROR:  update or delete on table "t44_p" violates foreign key constraint "t44_c_pid_fkey"
  on table "t44_c"
DETAIL:  Key (id)=(10) is still referenced from table "t44_c".
--- MySQL 8.4.10 ---
(성공 — 부모가 지워졌다)
```

```text
--- MySQL 8.4.10 ---  그 뒤 상태
SELECT * FROM t44_c;              SELECT * FROM t44_p;
+----+------+------+              +----+------+
| id | pid  | name |              | id | name |
+----+------+------+              +----+------+
|  1 |   10 | ann  |              | 20 | dev  |
|  2 |   20 | bob  |              +----+------+
|  3 |   99 | cho  |  <- 고아
+----+------+------+                 ↑ id=10 이 사라졌는데 pid=10 인 자식이 남았다

SELECT @@foreign_key_checks;
+----------------------+
| @@foreign_key_checks |
+----------------------+
|                    1 |          <- 검사는 켜져 있다. 검사할 제약이 없는 것이다
+----------------------+
```

그림 해설 — **`foreign_key_checks` 가 켜져 있는데도 아무 일도 안 일어났다.**\
검사가 꺼진 것이 아니라 **검사할 외래키가 처음부터 만들어지지 않은 것**이다.

대가 — **가장 나쁜 종류의 조용한 실패다.** 문법 에러도, 경고도, `SHOW WARNINGS` 조차 없다.\
스키마 리뷰에서 `REFERENCES` 라는 글자를 보고 「외래키가 있다」고 읽게 된다.

**처방 — 표 수준 `FOREIGN KEY` 절로 쓴다.** 이렇게 쓰면 MySQL 도 만든다.

```sql
CREATE TABLE t44_c (id int PRIMARY KEY, pid int, name varchar(10),
                    FOREIGN KEY (pid) REFERENCES t44_p(id));
```

```text
--- MySQL 8.4.10 ---
Create Table: CREATE TABLE `t44_c` (
  `id` int NOT NULL,
  `pid` int DEFAULT NULL,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pid` (`pid`),                                              <- ★ 3번에서 다룬다
  CONSTRAINT `t44_c_ibfk_1` FOREIGN KEY (`pid`) REFERENCES `t44_p` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

★ **확인 방법이 답의 절반이다** — MySQL 에서 외래키를 선언했으면 **`SHOW CREATE TABLE` 로 실재를 확인한다.**

### 2. 외래키가 막는 두 방향

**언제 쓰나** — 표 수준 `FOREIGN KEY` 로 제대로 만든 뒤. 여기서부터가 정상 동작이다.

```text
(A) 삽입 쪽 — 없는 부모를 가리킨다        (B) 삭제 쪽 — 가리켜지는 부모를 지운다

INSERT INTO t44_c VALUES (3,99,'cho');   DELETE FROM t44_p WHERE id=10;

부모: 10, 20                              부모: 10, 20
자식: -> 99  ← 없다                       자식: -> 10  ← 이게 남는다
        ↓                                         ↓
     막는다                                    막는다
```

```text
### SQL: INSERT INTO t44_c VALUES (3,99,'cho');
--- PG 18.6 ---
ERROR:  insert or update on table "t44_c" violates foreign key constraint "t44_c_pid_fkey"
DETAIL:  Key (pid)=(99) is not present in table "t44_p".
--- MySQL 8.4.10 ---
ERROR 1452 (23000) at line 1: Cannot add or update a child row: a foreign key constraint
  fails (`study`.`t44_c`, CONSTRAINT `t44_c_ibfk_1` FOREIGN KEY (`pid`) REFERENCES `t44_p` (`id`))
```

```text
### SQL: DELETE FROM t44_p WHERE id=10;
--- PG 18.6 ---
ERROR:  update or delete on table "t44_p" violates foreign key constraint "t44_c_pid_fkey"
  on table "t44_c"
DETAIL:  Key (id)=(10) is still referenced from table "t44_c".
--- MySQL 8.4.10 ---
ERROR 1451 (23000) at line 1: Cannot delete or update a parent row: a foreign key constraint
  fails (`study`.`t44_c`, CONSTRAINT `t44_c_ibfk_1` FOREIGN KEY (`pid`) REFERENCES `t44_p` (`id`))
```

★ **MySQL 은 두 방향을 코드로 구분한다** — `1452`(자식 쪽) 와 `1451`(부모 쪽).

**`NULL` 은 어느 쪽도 위반이 아니다.**

```text
### SQL: INSERT INTO t44_c VALUES (4,NULL,'dan');
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
(성공)
```

[43 의 3값 논리](../43-primary-key-unique-and-null/)와 같은 자리다 — **`NULL` 은 「아무것도 가리키지 않는다**」이지\
「없는 것을 가리킨다」가 아니다. 그래서 검사 대상이 아니다.

**부모 쪽 열이 유일하지 않으면 외래키를 못 만든다.**

```text
### SQL: CREATE TABLE t44_np (id int, v int);
        CREATE TABLE t44_nc (id int PRIMARY KEY, pid int, FOREIGN KEY (pid) REFERENCES t44_np(id));
--- PG 18.6 ---
ERROR:  there is no unique constraint matching given keys for referenced table "t44_np"
--- MySQL 8.4.10 ---
ERROR 6125 (HY000) at line 1: Failed to add the foreign key constraint. Missing unique key
  for constraint 't44_nc_ibfk_1' in the referenced table 't44_np'
```

**「부모를 하나로 짚을 수 있어야」 참조가 성립한다** — [43번](../43-primary-key-unique-and-null/)이 선행인 이유다.

### 3. ★ 외래키가 인덱스를 요구하나 — **MySQL 은 만들고 PG 는 안 만든다**

**언제 쓰나** — 외래키를 만든 직후. **이 차이가 운영에서 성능 사고로 나타난다.**

같은 `FOREIGN KEY (pid) REFERENCES t44_p(id)` 를 선언한 뒤 인덱스를 본다.

```text
(A) PostgreSQL 18.6                       (B) MySQL 8.4.10
\d t44_c                                  SHOW CREATE TABLE t44_c\G
Indexes:                                    PRIMARY KEY (`id`),
    "t44_c_pkey" PRIMARY KEY, btree (id)    KEY `pid` (`pid`),          <- ★ 자동 생성
Foreign-key constraints:                    CONSTRAINT `t44_c_ibfk_1`
    "t44_c_pid_fkey" FOREIGN KEY (pid)        FOREIGN KEY (`pid`)
      REFERENCES t44_p(id)                    REFERENCES `t44_p` (`id`)

 -> pid 에 인덱스가 없다                   -> pid 에 인덱스가 생겼다
```

**MySQL 은 그 인덱스를 지키기까지 한다.**

```text
### SQL: DROP INDEX pid ON t44_cascade;
--- MySQL 8.4.10 ---
ERROR 1553 (HY000) at line 1: Cannot drop index 'pid': needed in a foreign key constraint
```

그림 해설 — **자식 쪽 인덱스는 부모를 지울 때 쓰인다.**

```text
DELETE FROM t44_p WHERE id=10;
        ↓
엔진: "이 부모를 가리키는 자식이 있나?"
        ↓
    SELECT ... FROM 자식 WHERE pid = 10     <- 이 조회가 인덱스를 탈 수 있나?
        ↓
MySQL : KEY(pid) 가 있으니 바로 짚는다
PG    : 인덱스가 없으면 자식 표 전체를 훑는다   <- 부모 한 행 지우는 데 자식 전체 스캔
```

대가 — PG 에서 **자식 표가 큰데 FK 열에 인덱스가 없으면 부모 삭제가 급격히 느려진다.**\
「탈지 말지」의 판단은 [47번](../47-when-indexes-are-used/)이고, 여기서는 **인덱스를 직접 만들어야 한다**는 사실만 기억한다.

```sql
-- PG 에서는 외래키를 만들면 이것도 같이 만든다
CREATE INDEX t44_c_pid_idx ON t44_c (pid);
```

### 4. ★★ `ON DELETE` 네 동작 — 전부 던져 봤다

**언제 쓰나** — 외래키를 선언할 때 **반드시 고르게 되는 것**이다. 안 쓰면 기본값이 골라진다.

네 자식 표가 각각 다른 부모 행을 가리키게 해서 **한 동작씩 따로 발동**시켰다.

**(1) `NO ACTION` — 막는다**

```text
### SQL: DELETE FROM t44_p WHERE id=30;     (t44_noaction 이 30 을 가리킨다)
--- PG 18.6 ---
ERROR:  update or delete on table "t44_p" violates foreign key constraint
  "t44_noaction_pid_fkey" on table "t44_noaction"
DETAIL:  Key (id)=(30) is still referenced from table "t44_noaction".
--- MySQL 8.4.10 ---
ERROR 1451 (23000) at line 1: Cannot delete or update a parent row: a foreign key constraint
  fails (`study`.`t44_noaction`, CONSTRAINT `t44_noaction_ibfk_1` FOREIGN KEY (`pid`)
  REFERENCES `t44_p` (`id`))
```

**(2) `RESTRICT` — 막는다. ★ PG 는 에러 문구가 다르다**

```text
### SQL: DELETE FROM t44_p WHERE id=40;     (t44_restrict 가 40 을 가리킨다)
--- PG 18.6 ---
ERROR:  update or delete on table "t44_p" violates RESTRICT setting of foreign key constraint
  "t44_restrict_pid_fkey" on table "t44_restrict"
DETAIL:  Key (id)=(40) is referenced from table "t44_restrict".
--- MySQL 8.4.10 ---
ERROR 1451 (23000) at line 1: Cannot delete or update a parent row: a foreign key constraint
  fails (`study`.`t44_restrict`, CONSTRAINT `t44_restrict_ibfk_1` FOREIGN KEY (`pid`)
  REFERENCES `t44_p` (`id`) ON DELETE RESTRICT)
```

★ **PG 는 `violates RESTRICT setting of` 라고 따로 적는다.** `NO ACTION` 쪽 문구와 글자가 다르다.\
MySQL 은 **같은 `ERROR 1451`** 이고 괄호 안에 선언문이 그대로 복사될 뿐이다. 5번이 그 이유다.

**(3) `CASCADE` — 자식도 같이 지운다**

```text
### SQL: DELETE FROM t44_p WHERE id=50;     (t44_cascade 가 50 을 가리킨다)
--- PG 18.6 ---
DELETE 1
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT count(*) FROM t44_cascade;
--- PG 18.6 ---        --- MySQL 8.4.10 ---
 count                 +-----+
-------                | n   |
     0                 +-----+
(1 row)                |   0 |
                       +-----+
```

★ **`DELETE 1` 은 부모 한 행을 말한다.** 자식이 같이 지워졌다는 것은 **결과에 안 나온다** — 세어 봐야 안다.

**(4) `SET NULL` — 자식의 참조 열을 비운다**

```text
### SQL: DELETE FROM t44_p WHERE id=60;     (t44_setnull 이 60 을 가리킨다)
--- PG 18.6 ---
DELETE 1
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT * FROM t44_setnull;
--- PG 18.6 ---        --- MySQL 8.4.10 ---
 id | pid              +----+------+
----+-----             | id | pid  |
  1 |                  +----+------+
(1 row)                |  1 | NULL |
                       +----+------+
```

**행은 남고 참조만 끊겼다.**

**네 동작을 한 표로**

| `ON DELETE` | 부모 삭제 | 자식 행 | 두 엔진 |
|---|---|---|---|
| `NO ACTION`(기본) | **막힌다** | 그대로 | 같다 |
| `RESTRICT` | **막힌다** | 그대로 | 같다 (PG 만 에러 문구가 다르다) |
| `CASCADE` | 된다 | **같이 지워진다** | 같다 |
| `SET NULL` | 된다 | **남고 참조 열이 `NULL`** | 같다 |
| `SET DEFAULT` | **PG 는 된다 / MySQL 은 막힌다** | PG 는 기본값으로 · MySQL 은 그대로 | ★ **다르다**(4-b) |

비용 — **`CASCADE` 는 되돌릴 수 없는 연쇄 삭제**다. 자식의 자식까지 타고 내려간다.\
「부모 하나 지웠는데 수천 행이 사라졌다」가 여기서 나온다.

### 4-b. ★ 다섯째 동작 `SET DEFAULT` — **MySQL 은 적어 두고 안 지킨다**

**언제 쓰나** — 「부모가 사라지면 기본 부서로 옮긴다」 같은 요구가 있을 때. **함정이 하나 있다.**

```sql
CREATE TABLE t44_sd (id int PRIMARY KEY, pid int DEFAULT 20,
  FOREIGN KEY (pid) REFERENCES t44_p(id) ON DELETE SET DEFAULT);
```

**두 엔진 다 `CREATE TABLE` 이 성공했다.** MySQL 은 카탈로그에도 제대로 적어 둔다.

```text
--- MySQL 8.4.10 ---
SHOW CREATE TABLE t44_sd\G
  CONSTRAINT `t44_sd_ibfk_1` FOREIGN KEY (`pid`) REFERENCES `t44_p` (`id`) ON DELETE SET DEFAULT

SELECT constraint_name, delete_rule FROM information_schema.referential_constraints
  WHERE constraint_schema='study' AND table_name='t44_sd';
+-----------------+-------------+
| CONSTRAINT_NAME | DELETE_RULE |
+-----------------+-------------+
| t44_sd_ibfk_1   | SET DEFAULT |         <- 분명히 SET DEFAULT 로 저장돼 있다
+-----------------+-------------+
```

**그런데 실제로 부모를 지우면 갈린다.**

```text
### SQL: DELETE FROM t44_p WHERE id=80;      (t44_sd 가 80 을 가리키는 중, pid 의 DEFAULT 는 20)
--- PG 18.6 ---
DELETE 1
--- MySQL 8.4.10 ---
ERROR 1451 (23000) at line 1: Cannot delete or update a parent row: a foreign key constraint
  fails (`study`.`t44_sd`, CONSTRAINT `t44_sd_ibfk_1` FOREIGN KEY (`pid`) REFERENCES `t44_p` (`id`))
```

```text
### SQL: SELECT * FROM t44_sd;
--- PG 18.6 ---        --- MySQL 8.4.10 ---
 id | pid              +----+------+
----+-----             | id | pid  |
  1 |  20              +----+------+
(1 row)                |  1 |   80 |
                       +----+------+
   ↑ DEFAULT 20 으로 바뀌었다     ↑ 그대로다. 부모 삭제 자체가 막혔다
```

그림 해설 — **MySQL 의 InnoDB 는 `SET DEFAULT` 를 저장만 하고 `NO ACTION` 처럼 행동했다.**

★ **에러 문구를 4번 (2) 의 `RESTRICT` 와 나란히 읽으면 증거가 하나 더 보인다.**

```text
RESTRICT 일 때     : ... REFERENCES `t44_p` (`id`) ON DELETE RESTRICT)   <- 절이 인용된다
SET DEFAULT 일 때  : ... REFERENCES `t44_p` (`id`))                      <- ★ 절이 안 보인다
```

대가 — **`SHOW CREATE TABLE` 도 `information_schema` 도 「SET DEFAULT 가 걸려 있다」고 말한다.**\
스키마만 읽어서는 **틀린 것을 알 수 없다.** 실제로 부모를 지워 봐야 드러난다.\
그래서 이 주제에서 「선언됐다」와 「수행된다」는 **따로 확인해야 하는 두 가지**다.

### 5. ★ MySQL 의 `NO ACTION` 이 `RESTRICT` 와 같은가 — **같다. 그리고 PG 에서는 다르다**

**언제 쓰나** — 둘 중 무엇을 쓸지 고를 때. **표준에서는 둘이 다른 것**이라 헷갈린다.

두 엔진이 카탈로그에는 **둘을 구분해서 저장한다.**

```text
--- MySQL 8.4.10 ---
SELECT constraint_name, delete_rule FROM information_schema.referential_constraints
  WHERE constraint_schema='study' AND table_name LIKE 't44%';
+---------------------+-------------+
| CONSTRAINT_NAME     | DELETE_RULE |
+---------------------+-------------+
| t44_c_ibfk_1        | NO ACTION   |     <- 절을 안 썼을 때의 기본값
| t44_cascade_ibfk_1  | CASCADE     |
| t44_noaction_ibfk_1 | NO ACTION   |
| t44_restrict_ibfk_1 | RESTRICT    |
| t44_setnull_ibfk_1  | SET NULL    |
+---------------------+-------------+

--- PG 18.6 ---
SELECT conname, confdeltype FROM pg_constraint WHERE conname LIKE 't44%' AND contype='f';
        conname        | confdeltype 
-----------------------+-------------
 t44_c_pid_fkey        | a               <- a = NO ACTION
 t44_cascade_pid_fkey  | c
 t44_noaction_pid_fkey | a
 t44_restrict_pid_fkey | r               <- r = RESTRICT
 t44_setnull_pid_fkey  | n
```

**차이는 「검사를 미룰 수 있느냐」에서만 드러난다.** 그래서 지연 검사를 던져 봤다.

```text
--- PG 18.6 ---  NO ACTION + 지연
CREATE TABLE t44_dna (id int PRIMARY KEY, pid int,
  FOREIGN KEY (pid) REFERENCES t44_dp(id) ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED);

BEGIN;
DELETE FROM t44_dp  WHERE id=1;     -- 부모를 먼저 지운다
DELETE 1
DELETE FROM t44_dna WHERE id=1;     -- 그 다음 자식을 지운다
DELETE 1
COMMIT;
COMMIT                               <- ★ 통과했다
```

```text
--- PG 18.6 ---  RESTRICT + 지연 (같은 선언, 같은 순서)
BEGIN;
DELETE FROM t44_dp WHERE id=2;
ERROR:  update or delete on table "t44_dp" violates RESTRICT setting of foreign key
  constraint "t44_dre_pid_fkey" on table "t44_dre"
DETAIL:  Key (id)=(2) is referenced from table "t44_dre".
ERROR:  current transaction is aborted, commands ignored until end of transaction block
ROLLBACK
```

그림 해설 — **`DEFERRABLE INITIALLY DEFERRED` 를 똑같이 붙였는데 결과가 갈렸다.**

```text
NO ACTION  : 검사를 COMMIT 까지 미룰 수 있다
             -> 그 사이에 자식을 정리하면 통과한다
RESTRICT   : 미룰 수 없다. DELETE 를 실행하는 그 자리에서 검사한다
             -> 자식을 정리할 틈이 없다
```

**MySQL 에는 미룰 수단 자체가 없다.**

```text
### SQL: CREATE TABLE t44_dna (... ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED);
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'DEFERRABLE INITIALLY DEFERRED)' at line 1
```

**결론** — **MySQL 에서 `NO ACTION` 과 `RESTRICT` 는 실질적으로 같다.**\
둘이 갈릴 수 있는 유일한 자리(지연 검사)가 **MySQL 에 존재하지 않기 때문**이다.

★ **한쪽에서만 결론이 서는 실험이다.**\
PG 쪽 출력(통과 / 즉시 에러)은 **「둘이 다르다」의 근거**다.\
MySQL 쪽 출력(`ERROR 1064`)은 **「미룰 문법이 없다」의 근거**일 뿐, 「NO ACTION 이 즉시 검사다」를 직접 증명하지는 않는다.\
그 직접 근거는 **4번 (1)의 `ERROR 1451`** 이다 — 문을 실행한 그 자리에서 터졌다.

### 6. `ON UPDATE` — 부모 키가 바뀔 때

**언제 쓰나** — 자연키를 PK 로 썼을 때([43번의 대리키 이야기](../43-primary-key-unique-and-null/)).

```sql
CREATE TABLE t44_uc (id int PRIMARY KEY, pid int,
  FOREIGN KEY (pid) REFERENCES t44_up(id) ON UPDATE CASCADE ON DELETE CASCADE);
```

```text
### SQL: UPDATE t44_up SET id=7 WHERE id=1;    (자식 t44_uc 가 1 을 가리키는 중)
--- PG 18.6 ---
UPDATE 1
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT * FROM t44_uc;
--- PG 18.6 ---          --- MySQL 8.4.10 ---
 id  | pid               +-----+------+
-----+-----              | id  | pid  |
 100 |   7               +-----+------+
(1 row)                  | 100 |    7 |
                         +-----+------+
```

그림 해설 — **자식의 `pid` 가 `1` 에서 `7` 로 따라 바뀌었다.**\
`ON UPDATE` 는 `ON DELETE` 와 **같은 네 동작**을 갖고, 기본값도 `NO ACTION` 으로 같다(5번의 카탈로그 출력 참조).

비용 — `ON UPDATE CASCADE` 가 필요하다는 것은 **PK 가 바뀌는 값이라는 뜻**이다.\
대리키를 쓰면 이 절이 필요 없어진다.

### 7. ★ `SET NULL` 인데 자식 열이 `NOT NULL` 이면 — **검사 시점이 갈린다**

**언제 쓰나** — `SET NULL` 을 고를 때. **모순된 선언을 언제 잡느냐**가 다르다.

```sql
CREATE TABLE t44_snn (id int PRIMARY KEY, pid int NOT NULL,
  FOREIGN KEY (pid) REFERENCES t44_p(id) ON DELETE SET NULL);
```

```text
(A) PostgreSQL 18.6                    (B) MySQL 8.4.10
CREATE TABLE                           ERROR 1830 (HY000) at line 1: Column 'pid' cannot
        ↓                                be NOT NULL: needed in a foreign key constraint
   만들어졌다                             't44_snn_ibfk_1' SET NULL
        ↓                                        ↓
 실제로 DELETE 를 해 보면                    선언하는 순간 막혔다
```

**PG 는 실행 시점에 터진다.**

```text
--- PG 18.6 ---
INSERT INTO t44_snn VALUES (1,70);
INSERT 0 1

DELETE FROM t44_p WHERE id=70;
ERROR:  null value in column "pid" of relation "t44_snn" violates not-null constraint
DETAIL:  Failing row contains (1, null).
CONTEXT:  SQL statement "UPDATE ONLY "public"."t44_snn" SET "pid" = NULL
          WHERE $1 OPERATOR(pg_catalog.=) "pid""
```

★ **`CONTEXT` 에 엔진이 내부적으로 실행한 `UPDATE ... SET "pid" = NULL` 이 보인다.**\
`SET NULL` 이 **실제로 `UPDATE` 로 구현되어 있다**는 증거다.

두 그림의 결론 — **MySQL 은 선언 시점에, PG 는 실행 시점에 잡는다.**\
MySQL 쪽이 빨리 잡아서 낫고, PG 쪽은 **운영 중 첫 삭제 시도에서 장애로 나타난다.**

## 문법 — 어느 절에서 무엇이 갈리나

```sql
-- ★ 열 뒤에 붙이는 형태
CREATE TABLE c (pid int REFERENCES p(id));              -- PG: 만들어진다
                                                        -- ★ MySQL: 조용히 무시된다 (1번)

-- 표 수준 (양쪽 다 확실한 유일한 형태)
CREATE TABLE c (pid int, FOREIGN KEY (pid) REFERENCES p(id));                  -- 양쪽
CREATE TABLE c (pid int, CONSTRAINT c_pid_fk FOREIGN KEY (pid) REFERENCES p(id));  -- 양쪽

-- 참조 동작
... REFERENCES p(id) ON DELETE CASCADE                  -- 양쪽
... REFERENCES p(id) ON DELETE SET NULL                 -- 양쪽
... REFERENCES p(id) ON DELETE RESTRICT                 -- 양쪽
... REFERENCES p(id) ON DELETE NO ACTION                -- 양쪽 (기본값)
... REFERENCES p(id) ON UPDATE CASCADE                  -- 양쪽
... REFERENCES p(id) ON DELETE SET DEFAULT              -- ★ 양쪽 다 「받는다」. 동작은 다르다 (4-b)

-- 검사를 미룬다
... REFERENCES p(id) DEFERRABLE INITIALLY DEFERRED      -- ★ PG 만 (MySQL 은 ERROR 1064)

-- 나중에 붙이기·떼기
ALTER TABLE c ADD CONSTRAINT c_pid_fk FOREIGN KEY (pid) REFERENCES p(id);      -- 양쪽
ALTER TABLE c DROP CONSTRAINT c_pid_fk;                 -- 양쪽 (43번에서 확인)
ALTER TABLE c DROP FOREIGN KEY c_pid_fk;                -- MySQL
```

- ★ **`REFERENCES` 를 열 뒤에 쓰는 형태는 MySQL 에서 쓰지 않는다.** 1번이 그 근거다.
- ★ **`ON DELETE SET DEFAULT` 는 「받아들이는 것」과 「수행하는 것」이 다르다** — 4-b 절에 출력이 있다.

## 어디서 틀리나

1. ★ **MySQL 에서 `pid int REFERENCES p(id)` 라고 쓴다.** 외래키가 **안 만들어진다**(1번).\
   `SHOW CREATE TABLE` 로 실재를 확인하지 않으면 끝까지 모른다.
2. **`CASCADE` 를 기본값으로 착각한다.** 기본값은 **`NO ACTION`**(막는다)이다(5번의 카탈로그).
3. **`CASCADE` 의 범위를 과소평가한다.** 자식의 자식까지 타고 내려간다. 되돌릴 수 없다.
4. **`DELETE 1` 을 보고 한 행만 지워졌다고 읽는다.** `CASCADE` 로 사라진 자식은 **출력에 안 나온다**(4번).
5. **PG 에서 FK 열에 인덱스를 안 만든다.** MySQL 습관이 그대로 넘어오면 **부모 삭제가 느려진다**(3번).
6. **`NO ACTION` 과 `RESTRICT` 가 항상 같다고 생각한다.** **PG 에서는 지연 검사에서 갈린다**(5번).
7. **`SET NULL` 을 `NOT NULL` 열에 건다.** MySQL 은 `ERROR 1830` 으로 즉시 막고,\
   **PG 는 만들어 놓고 삭제할 때 터진다**(7번).
8. **`NULL` 인 FK 열이 위반이라고 생각한다.** 위반이 아니다 — 아무것도 안 가리키는 것이다(2번).
9. **부모 열이 `UNIQUE` 가 아닌데 FK 를 만들려 한다.** 둘 다 거부한다(2번).
10. ★ **`ON DELETE SET DEFAULT` 를 선언해 놓고 스키마만 확인한다.**\
    MySQL 은 `SHOW CREATE TABLE` 에도 `information_schema` 에도 적어 두지만 **수행하지 않는다**(4-b).\
    선언됐는지와 수행되는지는 **따로 확인한다.**

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| 참조 무결성 | 자식이 없는 부모를 못 가리킨다 | **열 뒤 `REFERENCES` 를 받아들이는지**(★ MySQL 이 무시한다) |
| `ON DELETE` 네 동작 | 각각의 의미 | 에러 코드·문구 |
| `NO ACTION` 대 `RESTRICT` | 표준상 「지연 가능/불가」로 갈린다 | **지연 검사를 지원하는지**(MySQL 은 안 한다) |
| FK 와 인덱스 | — | **MySQL 자동 생성 · PG 수동** |
| `SET NULL` + `NOT NULL` | 모순된 조합 | **선언 시점(MySQL) 대 실행 시점(PG)** |

- **`CONTEXT:  SQL statement "UPDATE ONLY ..."`**(7번)는 **PG 의 구현 세부**다.\
  외울 것은 문구가 아니라 「**`SET NULL` 은 내부적으로 `UPDATE` 다**」라는 성질이다.
- **`t44_c_ibfk_1` 같은 자동 이름**은 MySQL 의 구현 세부다. 파싱해서 쓰지 않는다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 표 수준 `FOREIGN KEY` 절.** 두 엔진에서 확실히 만들어지는 유일한 형태다.
- **쓴다 — `ON DELETE` 를 명시.** 기본값(`NO ACTION`)이 원하는 것이더라도 적어 두면 의도가 남는다.
- **쓴다 — PG 에서 FK 열에 인덱스.** 부모 삭제·조인이 둘 다 빨라진다.
- **안 쓴다 — 로그·이력처럼 부모가 지워져도 남아야 하는 자식에 `CASCADE`.** 감사 기록이 사라진다.
- **안 쓴다 — 자연키 PK + `ON UPDATE CASCADE`.** 대리키로 바꾸면 그 절이 필요 없다.
- **조심한다 — `SET NULL`.** 자식 열이 `NOT NULL` 이면 안 된다(7번).\
  그리고 `NULL` 이 된 자식을 **누가 치우는지** 설계에 넣는다.
- **조심한다 — 대량 삭제에 `CASCADE`.** 부모 1,000행 삭제가 자식 수십만 행 삭제가 된다.

## 핵심 문장

- ★ **MySQL 에서 열 뒤 `REFERENCES` 는 조용히 무시된다.** 에러도 경고도 없이 제약이 사라진다.
- **외래키는 삽입 쪽(`1452`)과 삭제 쪽(`1451`) 둘 다 막는다.**
- **`ON DELETE` 의 기본값은 `NO ACTION`** — 막는 쪽이지 지우는 쪽이 아니다.
- **네 동작: 막는다(`NO ACTION`·`RESTRICT`) / 같이 지운다(`CASCADE`) / 참조만 끊는다(`SET NULL`).**
- **MySQL 에서 `NO ACTION` 과 `RESTRICT` 는 같다** — 둘이 갈리는 자리(지연 검사)가 MySQL 에 없기 때문이다.
- **MySQL 은 FK 열에 인덱스를 자동으로 만들고 PG 는 안 만든다.**
- **`SET NULL` + `NOT NULL` 은 MySQL 이 선언 시점에, PG 가 실행 시점에 잡는다.**
- ★ **`SET DEFAULT` 는 MySQL 이 적어만 두고 안 지킨다** — 카탈로그를 믿지 말고 실제로 부모를 지워 본다.

## 관련 자료

- [43 기본키·UNIQUE 제약과 NULL](../43-primary-key-unique-and-null/) — **그쪽은 「부모를 하나로 짚는 키를 어떻게 만드나」까지,\
  여기는 「그 키를 가리키는 쪽」부터.** 부모 열이 `UNIQUE` 여야 하는 이유가 거기 있다.
- [42 테이블 정의와 변경](../42-create-alter-drop-table/) — 의존 객체와 `DROP` 의 관계. 외래키도 의존 객체다.
- [46 인덱스 정의](../46-index-definition-composite-partial-expression/) — 3번에서 만들라고 한 인덱스의 문법.
- [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/) — **FK 열 인덱스가 실제로 쓰이는지의 판단은 거기.**
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `NULL` 인 FK 열이 왜 위반이 아닌가.
- [SQL 주제 목록](../README.md) — 45(CHECK·DEFAULT) · 51(DELETE) 이 이웃이다.

## 용어 풀이

- **외래키(foreign key)** — 다른 표의 키를 가리키는 열. 가리키는 값이 실제로 있어야 한다.\
  예: `orders.customer_id` 가 `customers.id` 를 가리킨다.
- **참조 무결성(referential integrity)** — 자식이 가리키는 부모가 반드시 존재한다는 성질.\
  예: 이 성질이 깨진 행을 「고아 행」이라 부른다.
- **고아 행(orphan row)** — 가리키는 부모가 없는 자식 행.\
  예: `pid=99` 인데 부모 표에 `99` 가 없는 행. 1번에서 MySQL 이 조용히 만들었다.
- **`NO ACTION`** — 참조가 남아 있으면 부모 변경을 막는다. **`ON DELETE`/`ON UPDATE` 의 기본값**이다.\
  예: PG 에서는 이 검사를 `COMMIT` 까지 미룰 수 있다.
- **`RESTRICT`** — `NO ACTION` 과 같이 막되 **미룰 수 없다.** 문을 실행하는 그 자리에서 검사한다.\
  예: PG 에서 `DEFERRABLE INITIALLY DEFERRED` 를 붙여도 즉시 터진다(5번).
- **`CASCADE`** — 부모가 사라지면 자식도 같이 사라진다(`ON UPDATE` 면 값이 따라 바뀐다).\
  예: 게시글을 지우면 댓글도 지워진다.
- **`SET NULL`** — 부모가 사라지면 자식의 참조 열을 `NULL` 로 만든다. 자식 행은 남는다.\
  예: 부서가 없어져도 사원 기록은 남고 `dept_id` 만 비워진다.
- **지연 검사(deferred check)** — 제약 검사를 문 실행 시점이 아니라 `COMMIT` 시점에 하는 것.\
  예: 부모를 먼저 지우고 자식을 나중에 지워도 한 트랜잭션 안이면 통과한다(PG, `NO ACTION` 한정).
- **`ERROR 1451` / `ERROR 1452`** — MySQL 의 FK 위반 코드. `1451` 은 부모 쪽, `1452` 는 자식 쪽이다.\
  예: 부모를 지우려다 막히면 `1451`, 없는 부모를 가리키는 자식을 넣으려다 막히면 `1452`.
- **`ERROR 1830`** — MySQL 이 「`NOT NULL` 열에 `SET NULL` 은 안 된다」고 거절하는 코드.\
  예: 선언하는 `CREATE TABLE` 에서 바로 나온다.
- **`@@foreign_key_checks`** — MySQL 에서 FK 검사를 켜고 끄는 세션 변수.\
  예: `0` 으로 두고 대량 적재를 한 뒤 다시 `1` 로 올리는 절차가 있다. 이 실험에서는 **계속 `1`** 이었다.

## 더 들어가면

- **`foreign_key_checks=0` 은 검사를 끄는 것이지 데이터를 고치는 것이 아니다.**\
  끄고 넣은 고아 행은 다시 켜도 **그대로 남는다.** 이 실험에서는 끄지 않았다.
- **PG 의 `DEFERRABLE` 은 순환 참조를 푸는 정규 수단이다.** A 가 B 를, B 가 A 를 가리키는 두 행을\
  한 트랜잭션에서 넣을 수 있다. MySQL 에는 이 수단이 없어 **한쪽을 `NULL` 로 넣고 나중에 `UPDATE`** 해야 한다.
- **참조 무결성을 애플리케이션에서만 보장하려는 설계**가 있다(마이크로서비스에서 표가 다른 DB 에 있을 때).\
  그때는 **고아 행을 주기적으로 찾아내는 질의**가 FK 를 대신한다 —\
  `SELECT ... FROM c LEFT JOIN p ON c.pid=p.id WHERE c.pid IS NOT NULL AND p.id IS NULL`\
  ([19 SEMI·ANTI 조인](../19-semi-anti-join/)의 안티 조인이 그것이다).
