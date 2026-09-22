# sql/44-외래키와 참조 동작 (ON DELETE·ON UPDATE) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **환경** — MySQL 의 `@@foreign_key_checks` 는 실험 내내 **`1`(켜짐)** 이었다.\
> 이 편이 만든 표는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> 문서 근거는 [PG 18 Foreign Keys](https://www.postgresql.org/docs/18/ddl-constraints.html#DDL-CONSTRAINTS-FK) · [MySQL 8.4 FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. ★★ 열 뒤에 `REFERENCES` 를 쓰면 — **MySQL 은 조용히 무시한다**

**출력**

```text
### SQL: CREATE TABLE t44_c (id int PRIMARY KEY, pid int REFERENCES t44_p(id), name varchar(10));
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
(성공)
```

```text
### SQL: INSERT INTO t44_c VALUES (3,99,'cho');
--- PG 18.6 ---
ERROR:  insert or update on table "t44_c" violates foreign key constraint "t44_c_pid_fkey"
DETAIL:  Key (pid)=(99) is not present in table "t44_p".
--- MySQL 8.4.10 ---
(성공 — 고아 행이 들어갔다)
```

```text
### SQL: DELETE FROM t44_p WHERE id=10;
--- PG 18.6 ---
ERROR:  update or delete on table "t44_p" violates foreign key constraint "t44_c_pid_fkey"
  on table "t44_c"
DETAIL:  Key (id)=(10) is still referenced from table "t44_c".
--- MySQL 8.4.10 ---
(성공 — 부모가 지워졌다)
```

**왜 그런가**

MySQL 의 파서는 **열 정의 안의 `REFERENCES` 를 받아들이고 버린다.** 만들어진 표에 외래키가 없다.

```text
--- MySQL 8.4.10 ---
SHOW CREATE TABLE t44_c\G
Create Table: CREATE TABLE `t44_c` (
  `id` int NOT NULL,
  `pid` int DEFAULT NULL,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        ↑ REFERENCES 구절이 통째로 사라졌다
```

★ **검사가 꺼진 것이 아니다.**

```text
--- MySQL 8.4.10 ---
SELECT @@foreign_key_checks;
+----------------------+
| @@foreign_key_checks |
+----------------------+
|                    1 |          <- 켜져 있다. 검사할 제약이 없는 것이다
+----------------------+
```

그 뒤 데이터 상태가 참조 무결성 붕괴를 그대로 보여 준다.

```text
--- MySQL 8.4.10 ---
SELECT * FROM t44_c;              SELECT * FROM t44_p;
+----+------+------+              +----+------+
| id | pid  | name |              | id | name |
+----+------+------+              +----+------+
|  1 |   10 | ann  |              | 20 | dev  |
|  2 |   20 | bob  |              +----+------+
|  3 |   99 | cho  |  <- 고아 행     ↑ id=10 이 사라졌는데 pid=10 인 자식이 남았다
+----+------+------+
```

**에러도 경고도 `SHOW WARNINGS` 도 없다.** 이 배치에서 가장 조용한 실패다.

**처방** — 표 수준 절로 쓴다.

```sql
CREATE TABLE t44_c (id int PRIMARY KEY, pid int, name varchar(10),
                    FOREIGN KEY (pid) REFERENCES t44_p(id));
```

---

### 2. 1번의 결과를 어떻게 미리 아는가 — **정의를 다시 읽는다**

```text
PG    : \d t44_c            -> "Foreign-key constraints:" 절이 있는지
        또는 SELECT conname, contype FROM pg_constraint WHERE conrelid='t44_c'::regclass;

MySQL : SHOW CREATE TABLE t44_c\G   -> CONSTRAINT ... FOREIGN KEY 줄이 있는지
        또는 SELECT * FROM information_schema.referential_constraints WHERE table_name='t44_c';
```

표 수준 절로 다시 만든 뒤의 MySQL 출력이다.

```text
--- MySQL 8.4.10 ---
Create Table: CREATE TABLE `t44_c` (
  `id` int NOT NULL,
  `pid` int DEFAULT NULL,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pid` (`pid`),
  CONSTRAINT `t44_c_ibfk_1` FOREIGN KEY (`pid`) REFERENCES `t44_p` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

★ **그러나 「있다」가 「지켜진다」는 아니다** — 7번(`SET DEFAULT`)이 그 반례다.\
**선언 확인과 동작 확인은 따로 해야 한다.**

---

### 3. 외래키가 막는 두 방향 — **삽입(`1452`) 과 삭제(`1451`)**

**출력**

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

**왜 그런가**

```text
1452  "child row"   : 자식이 없는 부모를 가리키려 했다
1451  "parent row"  : 가리켜지는 부모를 없애려 했다
```

PG 의 문구도 같은 두 방향을 말한다 — `insert or update on table "t44_c"` 대 `update or delete on table "t44_p"`.\
**어느 표 이름이 주어 자리에 있는지**가 방향을 알려 준다.

---

### 4. `NULL` 인 참조 열 — **위반이 아니다**

**출력**

```text
### SQL: INSERT INTO t44_c VALUES (4,NULL,'dan');
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
(성공)
```

**왜 그런가**

외래키가 묻는 것은 「**이 값이 부모에 있나?**」다. `NULL` 은 값이 아니므로 물을 것이 없다.

```text
pid = 99    -> "99 가 부모에 있나?"  -> 없다 -> 위반
pid = NULL  -> 물을 값이 없다        -> 검사 대상이 아니다 -> 통과
```

[43 의 `UNIQUE` 와 `NULL`](../43-primary-key-unique-and-null/) 과 같은 뿌리다 —\
**`NULL` 은 「아무것도 가리키지 않는다」이지 「없는 것을 가리킨다」가 아니다.**

그래서 **「반드시 부모가 있어야 한다」를 뜻하려면 `NOT NULL` 을 같이 건다.**

```sql
pid int NOT NULL, FOREIGN KEY (pid) REFERENCES p(id)
```

(단 이때 `ON DELETE SET NULL` 은 쓸 수 없다 — 11번.)

---

### 5. ★★ `ON DELETE` 네 동작 — **막는다 둘, 지운다 하나, 끊는다 하나**

**출력 — (1) `NO ACTION`**

```text
### SQL: DELETE FROM t44_p WHERE id=30;
--- PG 18.6 ---
ERROR:  update or delete on table "t44_p" violates foreign key constraint
  "t44_noaction_pid_fkey" on table "t44_noaction"
DETAIL:  Key (id)=(30) is still referenced from table "t44_noaction".
--- MySQL 8.4.10 ---
ERROR 1451 (23000) at line 1: Cannot delete or update a parent row: a foreign key constraint
  fails (`study`.`t44_noaction`, CONSTRAINT `t44_noaction_ibfk_1` FOREIGN KEY (`pid`)
  REFERENCES `t44_p` (`id`))
```

**출력 — (2) `RESTRICT`**

```text
### SQL: DELETE FROM t44_p WHERE id=40;
--- PG 18.6 ---
ERROR:  update or delete on table "t44_p" violates RESTRICT setting of foreign key constraint
  "t44_restrict_pid_fkey" on table "t44_restrict"
DETAIL:  Key (id)=(40) is referenced from table "t44_restrict".
--- MySQL 8.4.10 ---
ERROR 1451 (23000) at line 1: Cannot delete or update a parent row: a foreign key constraint
  fails (`study`.`t44_restrict`, CONSTRAINT `t44_restrict_ibfk_1` FOREIGN KEY (`pid`)
  REFERENCES `t44_p` (`id`) ON DELETE RESTRICT)
```

★ **PG 의 두 문구를 나란히 읽으면 다르다.**

```text
NO ACTION : violates foreign key constraint "..."
RESTRICT  : violates RESTRICT setting of foreign key constraint "..."
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
DETAIL 도 다르다: "is still referenced" 대 "is referenced"
```

**출력 — (3) `CASCADE`**

```text
### SQL: DELETE FROM t44_p WHERE id=50;
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

★ **`DELETE 1` 은 부모 한 행이다.** 자식이 같이 지워졌다는 사실은 **결과에 안 나온다.**\
「에러 없이 돌았다」가 「한 행만 지워졌다」를 뜻하지 않는다 — **세어 봐야 안다.**

**출력 — (4) `SET NULL`**

```text
### SQL: DELETE FROM t44_p WHERE id=60;
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

**정리**

| `ON DELETE` | 부모 삭제 | 자식 행 | 두 엔진 |
|---|---|---|---|
| `NO ACTION`(기본) | 막힌다 | 그대로 | 같다 |
| `RESTRICT` | 막힌다 | 그대로 | 같다 (PG 만 문구가 다르다) |
| `CASCADE` | 된다 | **같이 지워진다** | 같다 |
| `SET NULL` | 된다 | 남고 참조 열이 `NULL` | 같다 |
| `SET DEFAULT` | **PG 만 된다** | PG 는 기본값 · MySQL 은 그대로 | ★ 다르다(7번) |

---

### 6. ★ MySQL 에서 `NO ACTION` 과 `RESTRICT` 는 같은가 — **MySQL 은 같고 PG 는 다르다**

**먼저 — 카탈로그에는 두 엔진 다 구분해서 저장한다.**

```text
--- MySQL 8.4.10 ---
+---------------------+-------------+
| CONSTRAINT_NAME     | DELETE_RULE |
+---------------------+-------------+
| t44_c_ibfk_1        | NO ACTION   |    <- 절을 안 쓴 기본값
| t44_cascade_ibfk_1  | CASCADE     |
| t44_noaction_ibfk_1 | NO ACTION   |
| t44_restrict_ibfk_1 | RESTRICT    |
| t44_setnull_ibfk_1  | SET NULL    |
+---------------------+-------------+

--- PG 18.6 ---
        conname        | confdeltype 
-----------------------+-------------
 t44_c_pid_fkey        | a
 t44_cascade_pid_fkey  | c
 t44_noaction_pid_fkey | a
 t44_restrict_pid_fkey | r
 t44_setnull_pid_fkey  | n
```

**차이가 드러나는 유일한 자리는 「검사를 미룰 수 있느냐」다.**

```text
--- PG 18.6 ---  NO ACTION + DEFERRABLE INITIALLY DEFERRED
BEGIN;
DELETE FROM t44_dp  WHERE id=1;      DELETE 1
DELETE FROM t44_dna WHERE id=1;      DELETE 1
COMMIT;                              COMMIT      <- ★ 통과했다
```

```text
--- PG 18.6 ---  RESTRICT + DEFERRABLE INITIALLY DEFERRED  (같은 선언, 같은 순서)
BEGIN;
DELETE FROM t44_dp WHERE id=2;
ERROR:  update or delete on table "t44_dp" violates RESTRICT setting of foreign key
  constraint "t44_dre_pid_fkey" on table "t44_dre"
DETAIL:  Key (id)=(2) is referenced from table "t44_dre".
ERROR:  current transaction is aborted, commands ignored until end of transaction block
ROLLBACK
```

**MySQL 에는 미룰 수단이 없다.**

```text
### SQL: CREATE TABLE t44_dna (... ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED);
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'DEFERRABLE INITIALLY DEFERRED)' at line 1
```

**★ 어느 쪽 출력이 무엇의 근거인가** — 이 질문의 핵심이다.

```text
PG 의 두 실험(통과 / 즉시 에러)
   -> "NO ACTION 과 RESTRICT 는 다르다" 의 근거다. 같은 선언에서 결과가 갈렸다

MySQL 의 ERROR 1064
   -> "MySQL 에는 지연 문법이 없다" 의 근거다
   -> ★ "MySQL 의 NO ACTION 이 즉시 검사다" 를 직접 증명하지는 않는다. 문 자체가 안 섰다

MySQL 의 "NO ACTION 이 즉시 검사다" 의 직접 근거
   -> 5번 (1) 의 ERROR 1451. DELETE 를 실행하는 그 자리에서 터졌다
```

**결론** — **MySQL 에서 둘은 실질적으로 같다.** 갈릴 수 있는 자리가 존재하지 않기 때문이다.

---

### 7. ★ 다섯째 동작 — **MySQL 은 적어 두고 안 지킨다**

**출력**

```text
--- MySQL 8.4.10 ---
SHOW CREATE TABLE t44_sd\G
  CONSTRAINT `t44_sd_ibfk_1` FOREIGN KEY (`pid`) REFERENCES `t44_p` (`id`) ON DELETE SET DEFAULT

SELECT constraint_name, delete_rule FROM information_schema.referential_constraints
  WHERE constraint_schema='study' AND table_name='t44_sd';
+-----------------+-------------+
| CONSTRAINT_NAME | DELETE_RULE |
+-----------------+-------------+
| t44_sd_ibfk_1   | SET DEFAULT |
+-----------------+-------------+
```

```text
### SQL: DELETE FROM t44_p WHERE id=80;
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
  ↑ DEFAULT 20 이 들어갔다      ↑ 그대로. 부모 삭제 자체가 막혔다
```

**왜 스키마만 읽어서는 알 수 없는가**

```text
SHOW CREATE TABLE        -> "ON DELETE SET DEFAULT" 라고 쓰여 있다
information_schema       -> DELETE_RULE = 'SET DEFAULT' 라고 저장돼 있다
        ↓
스키마 리뷰는 통과한다
        ↓
실제로 부모를 지우면 ERROR 1451 -> NO ACTION 처럼 행동한다
```

★ **에러 문구 자체가 힌트를 준다.** 5번 (2) 의 `RESTRICT` 와 나란히 보면,

```text
RESTRICT     : ... REFERENCES `t44_p` (`id`) ON DELETE RESTRICT)   <- 절이 인용된다
SET DEFAULT  : ... REFERENCES `t44_p` (`id`))                      <- 절이 안 보인다
```

**엔진이 그 절을 실행 경로에 안 싣고 있다**는 관찰이다.

**교훈** — 이 주제에서 **「선언됐다」와 「수행된다」는 따로 확인해야 하는 두 가지**다.\
1번(선언 자체가 사라짐)과 7번(선언은 남고 수행만 안 됨)이 **같은 교훈의 두 얼굴**이다.

---

### 8. ★ 외래키가 인덱스를 요구하나 — **MySQL 은 만들고 PG 는 안 만든다**

**출력**

```text
(A) PostgreSQL 18.6                       (B) MySQL 8.4.10
\d t44_c                                  SHOW CREATE TABLE t44_c\G
Indexes:                                    PRIMARY KEY (`id`),
    "t44_c_pkey" PRIMARY KEY, btree (id)    KEY `pid` (`pid`),        <- ★ 자동 생성
Foreign-key constraints:                    CONSTRAINT `t44_c_ibfk_1`
    "t44_c_pid_fkey" FOREIGN KEY (pid)        FOREIGN KEY (`pid`)
      REFERENCES t44_p(id)                    REFERENCES `t44_p` (`id`)

 -> pid 에 인덱스가 없다                   -> pid 에 인덱스가 생겼다
```

**MySQL 은 그 인덱스를 못 지우게 막는다.**

```text
### SQL: DROP INDEX pid ON t44_cascade;
--- MySQL 8.4.10 ---
ERROR 1553 (HY000) at line 1: Cannot drop index 'pid': needed in a foreign key constraint
```

**왜 그런가** — 9번이 그 설명이다.

**PG 에서는 내가 만든다.**

```sql
CREATE INDEX t44_c_pid_idx ON t44_c (pid);
```

---

### 9. 그 인덱스는 무엇에 쓰이나 — **부모를 지울 때 자식을 찾는 조회**

```text
DELETE FROM t44_p WHERE id=10;
        ↓
엔진이 스스로 던지는 질문: "id=10 을 가리키는 자식이 있나?"
        ↓
내부 조회:  ... FROM 자식 WHERE pid = 10
        ↓
MySQL : KEY(pid) 로 바로 짚는다
PG    : 인덱스가 없으면 자식 표를 처음부터 끝까지 훑는다
```

**느려지는 조작**

```text
1. 부모 DELETE        -> 부모 1행마다 자식 전체 스캔
2. 부모 키 UPDATE     -> 같은 이유
3. ON DELETE CASCADE  -> ★ 가장 나쁘다. 지울 자식을 찾는 스캔이 부모 행마다 반복된다
4. 부모-자식 조인      -> 조인 쪽 인덱스가 없는 것과 같다
```

그래서 PG 에서 외래키를 만들 때는 **자식 열 인덱스를 세트로 만든다.**\
그 인덱스가 **실제로 쓰이는지**의 판단은 [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)가 정본이다.

---

### 10. `ON UPDATE CASCADE` — **자식의 값이 따라 바뀐다**

**출력**

```text
### SQL: UPDATE t44_up SET id=7 WHERE id=1;
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

**왜 그런가**

`ON UPDATE` 는 `ON DELETE` 와 **같은 동작 집합**을 갖고, 기본값도 `NO ACTION` 이다\
(6번의 카탈로그 출력에서 `UPDATE_RULE` 이 전부 `NO ACTION` 이었다).

```text
ON UPDATE NO ACTION / RESTRICT : 부모 키를 못 바꾼다
ON UPDATE CASCADE              : 자식의 참조 값이 따라 바뀐다
ON UPDATE SET NULL             : 자식의 참조가 끊긴다
```

★ **이 절이 필요하다는 것은 PK 가 바뀌는 값이라는 뜻**이다.\
[43 의 대리키](../43-primary-key-unique-and-null/)를 쓰면 부모 키가 안 바뀌므로 이 절이 필요 없어진다.

---

### 11. ★ `SET NULL` 인데 자식 열이 `NOT NULL` 이면 — **MySQL 은 선언 시점, PG 는 실행 시점**

**출력**

```text
### SQL: CREATE TABLE t44_snn (id int PRIMARY KEY, pid int NOT NULL,
          FOREIGN KEY (pid) REFERENCES t44_p(id) ON DELETE SET NULL);
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
ERROR 1830 (HY000) at line 1: Column 'pid' cannot be NOT NULL: needed in a foreign key
  constraint 't44_snn_ibfk_1' SET NULL
```

```text
--- PG 18.6 ---  만들어진 표에 실제로 삭제를 걸어 본다
INSERT INTO t44_snn VALUES (1,70);
INSERT 0 1

DELETE FROM t44_p WHERE id=70;
ERROR:  null value in column "pid" of relation "t44_snn" violates not-null constraint
DETAIL:  Failing row contains (1, null).
CONTEXT:  SQL statement "UPDATE ONLY "public"."t44_snn" SET "pid" = NULL
          WHERE $1 OPERATOR(pg_catalog.=) "pid""
```

**왜 그런가**

```text
선언 자체가 모순이다:  "이 열은 비면 안 된다"  +  "부모가 사라지면 이 열을 비운다"

MySQL : 그 모순을 CREATE TABLE 에서 잡는다      -> 배포 전에 드러난다
PG    : 만들어 준다. 실제로 부모를 지울 때 잡는다 -> ★ 운영 중 첫 삭제에서 장애가 된다
```

★ **`CONTEXT` 가 엔진의 내부 동작을 보여 준다** — `UPDATE ONLY ... SET "pid" = NULL`.\
**`SET NULL` 은 내부적으로 `UPDATE` 로 구현되어 있고, 그 `UPDATE` 가 `NOT NULL` 제약에 걸린 것**이다.

여기서는 **MySQL 쪽이 나은 설계**다. 빨리 잡을수록 싸다.

---

### 12. 부모 열이 유일하지 않으면 — **둘 다 거부한다**

**출력**

```text
### SQL: CREATE TABLE t44_np (id int, v int);
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
(성공)

### SQL: CREATE TABLE t44_nc (id int PRIMARY KEY, pid int, FOREIGN KEY (pid) REFERENCES t44_np(id));
--- PG 18.6 ---
ERROR:  there is no unique constraint matching given keys for referenced table "t44_np"
--- MySQL 8.4.10 ---
ERROR 6125 (HY000) at line 1: Failed to add the foreign key constraint. Missing unique key
  for constraint 't44_nc_ibfk_1' in the referenced table 't44_np'
```

**왜 그런가**

참조는 「**이 값으로 부모 행 하나를 짚는다**」는 뜻이다.\
부모 열이 유일하지 않으면 **하나를 짚을 수 없고**, `CASCADE`·`SET NULL` 이 어느 행을 따라야 할지도 정해지지 않는다.

```text
부모가 유일하지 않다면
  pid=10 인 자식이 가리키는 부모가 3행이다
        ↓
  그 중 하나를 지우면 자식은 어떻게 되나? 답이 없다
        ↓
  애초에 만들지 못하게 한다
```

[43 기본키·UNIQUE](../43-primary-key-unique-and-null/) 가 44 의 선행인 이유가 이 한 문장이다.

---

### 13. 그래서 어떻게 고르나 — **「자식 데이터가 부모 없이 의미가 있나」로 가른다**

```text
자식이 부모 없이 의미가 있나?

├─ 없다 (부모의 일부다)
│    예: 주문 상세 · 게시글의 첨부파일
│    -> ON DELETE CASCADE
│       단 ★ 대량 삭제 비용을 확인한다. 부모 1,000행이 자식 수십만 행이 될 수 있다
│
├─ 있다. 다만 어느 부모였는지는 잊어도 된다
│    예: 부서가 없어져도 남는 사원 기록
│    -> ON DELETE SET NULL
│       단 자식 열이 NOT NULL 이면 안 된다(11번)
│       그리고 NULL 이 된 자식을 누가 치우는지 정한다
│
└─ 있다. 그리고 부모를 함부로 지우면 안 된다
     예: 결제·감사 기록 · 회계 원장
     -> ON DELETE NO ACTION (기본) 또는 RESTRICT
        "부모를 지우기 전에 자식을 먼저 정리하라" 를 엔진이 강제한다
```

**고르기 전에 확인할 세 가지**

```text
1. 제약이 실제로 만들어졌나          -> 1·2번 (MySQL 의 열 뒤 REFERENCES)
2. 고른 동작이 실제로 수행되나        -> 7번 (MySQL 의 SET DEFAULT)
3. 자식 열에 인덱스가 있나            -> 8·9번 (PG 는 직접 만들어야 한다)
```

★ **세 가지 다 「선언」이 아니라 「실행」으로만 확인된다.** 이 편의 결론이 그것이다.

**`SET DEFAULT` 는 어떤가** — 두 엔진을 다 쓸 계획이면 **고르지 않는다.**\
PG 에서만 동작하므로 같은 스키마가 엔진에 따라 다르게 행동한다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| ★ 열 뒤 `REFERENCES` (1번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **MySQL 의 고아 행·부모 삭제 성공이 근거다** |
| `SHOW CREATE TABLE` 대조 (1·2번) | MySQL 8.4.10 | 3회 | 외래키 줄의 유무 |
| `@@foreign_key_checks` (1번) | MySQL 8.4.10 | 1회 | **실험 내내 `1`** |
| 표 수준 `FOREIGN KEY` 재작성 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| FK 위반 — 삽입·삭제 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 1452·1451 이 근거다** |
| `NULL` 인 FK 열 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 성공 |
| ★ `ON DELETE` 네 동작 (5번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | 자식마다 다른 부모 행을 가리키게 해 **한 동작씩 격리**했다 |
| 동작 뒤 자식 표 확인 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `CASCADE` 0행 · `SET NULL` 1행 |
| 카탈로그 delete_rule (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `pg_constraint` · `referential_constraints` |
| ★ `DEFERRABLE` 실험 (6번) | PG 18.6 | 2회 | **NO ACTION 통과 / RESTRICT 즉시 에러** |
| `DEFERRABLE` 을 MySQL 에 (6번) | MySQL 8.4.10 | 1회 | `ERROR 1064` |
| ★ `SET DEFAULT` (7번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **PG 는 20 으로 · MySQL 은 `ERROR 1451`** |
| FK 인덱스 유무 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| FK 인덱스 삭제 시도 (8번) | MySQL 8.4.10 | 1회 | `ERROR 1553` |
| `ON UPDATE CASCADE` (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 자식 `pid` 가 7 로 |
| `SET NULL` + `NOT NULL` (11번) | PG 18.6 · MySQL 8.4.10 | 각 1~3회 | **MySQL `ERROR 1830` · PG 는 실행 시점** |
| 부모가 유일하지 않을 때 (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 6125 가 근거다** |
| `ALTER ADD/DROP` FK (문법표) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `DROP CONSTRAINT`·`DROP FOREIGN KEY` 둘 다 확인 |

**구현 의존 항목** — 5·7번의 **에러 문구**와 **`t44_c_ibfk_1` 같은 자동 이름**,\
그리고 11번의 `CONTEXT:  SQL statement "UPDATE ONLY ..."`.\
외울 것은 문구가 아니라 「**`SET NULL` 은 내부적으로 `UPDATE` 다**」같은 성질이다.

**★ 구현 의존이면서 가장 중요한 항목** — **1번**(MySQL 이 열 뒤 `REFERENCES` 를 무시한다)과\
**7번**(MySQL 이 `SET DEFAULT` 를 저장만 한다)은 **두 매뉴얼이 정한 표준 의미와 다른 엔진 고유 동작**이다.\
스키마를 읽어서는 알 수 없고 **실행해야만 드러난다.**

**언어 보장 항목** — 3·4·5·10·12번.\
외래키가 두 방향을 막는다는 것, `NULL` 이 검사 대상이 아니라는 것, 네 참조 동작의 의미,\
부모 열이 유일해야 한다는 것은 두 매뉴얼의 외래키 페이지가 정한 것이다.

**버전을 적지 않은 이유** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 두 매뉴얼에서 찾지 못했다.\
목록 README 의 규칙대로 확인하지 못한 도입 버전은 적지 않았다.

**DB 잔재** — 없다. `t44_` 로 시작하는 표 13개를 전부 삭제했고 `emp`·`dept` 는 **읽지도 쓰지도 않았다.**\
두 엔진의 최종 표 목록 출력은 [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)의 「실행 검증」에 있다.
