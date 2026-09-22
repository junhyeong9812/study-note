# sql/51-DELETE 와 TRUNCATE — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·수치는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **환경** — MySQL `autocommit=1` · `sql_safe_updates=0`(기본) · 스토리지 엔진 **InnoDB**.\
> ★ **측정 조건** — 11번의 수치는 JMH 가 아니라 **클라이언트 타이머**다(`psql \timing` · `SYSDATE(6)` 차). **3판 원값**을 싣는다.\
> 이 편이 만든 표(`t51_a`·`t51_p`·`t51_c`·`t51_pc`·`t51_cc`·`t51_big`)는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> 문서 근거는 [PG 18 TRUNCATE](https://www.postgresql.org/docs/18/sql-truncate.html) · [MySQL 8.4 TRUNCATE TABLE](https://dev.mysql.com/doc/refman/8.4/en/truncate-table.html) · [MySQL 8.4 mysql Client Options](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `DELETE` 는 되돌아오나 — **둘 다 5다**

**출력**

```text
### SQL: BEGIN; DELETE FROM t51_a; SELECT count(*) AS n FROM t51_a; ROLLBACK;
--- PG 18.6 ---
BEGIN
DELETE 5
 n 
---
 0
(1 row)
ROLLBACK
### SQL: SELECT count(*) AS n_after_rollback FROM t51_a;
--- PG 18.6 ---
 n_after_rollback 
------------------
                5
(1 row)

### SQL: START TRANSACTION; DELETE FROM t51_a; SELECT count(*) AS n FROM t51_a; ROLLBACK; SELECT count(*) AS n_after_rollback FROM t51_a;
--- MySQL 8.4.10 ---
+---+
| n |
+---+
| 0 |
+---+
+------------------+
| n_after_rollback |
+------------------+
|                5 |
+------------------+
```

**왜 그런가** — `DELETE` 는 **DML** 이라 트랜잭션의 지배를 받는다. 두 엔진이 같다.\
되돌릴 수 있다는 것은 **되돌릴 정보를 쌓아 둔다**는 뜻이고, 그 비용을 12번에서 잰다.

---

### 2. ★★ `TRUNCATE` 는 되돌아오나 — **PG 는 5, MySQL 은 0**

**출력**

```text
### SQL: BEGIN; TRUNCATE t51_a; SELECT count(*) AS n FROM t51_a; ROLLBACK;
--- PG 18.6 ---
BEGIN
TRUNCATE TABLE
 n 
---
 0
(1 row)
ROLLBACK
### SQL: SELECT count(*) AS n_after_rollback FROM t51_a;
--- PG 18.6 ---
 n_after_rollback 
------------------
                5          <- ★ 돌아왔다
(1 row)

### SQL: START TRANSACTION; TRUNCATE t51_a; SELECT count(*) AS n FROM t51_a; ROLLBACK; SELECT count(*) AS n_after_rollback FROM t51_a;
--- MySQL 8.4.10 ---
+---+
| n |
+---+
| 0 |
+---+
+------------------+
| n_after_rollback |
+------------------+
|                0 |          <- ★★ 0 이다. 데이터가 사라졌다
+------------------+
```

**왜 그런가** — 3번이 그 설명이다.\
★ **에러도 경고도 없었다.** `ROLLBACK` 은 성공했고, 되돌릴 것이 없었을 뿐이다.

(이 실험을 위해 MySQL 쪽 `t51_a` 의 5행을 **다시 넣어 복구**했다 — 되돌아오지 않았으므로.)

---

### 3. 왜 그런가 — **MySQL 의 `TRUNCATE` 는 DDL 이고 암묵 커밋을 일으킨다**

두 문서가 각각 명시한다.

> "`TRUNCATE` is transaction-safe with respect to the data in the tables: the truncation will be safely rolled back if the surrounding transaction does not commit."\
> — [PostgreSQL 18 · TRUNCATE](https://www.postgresql.org/docs/18/sql-truncate.html)

> "Although `TRUNCATE TABLE` is similar to `DELETE`, it is classified as a DDL statement rather than a DML statement… **Truncate operations cause an implicit commit, and so cannot be rolled back.**"\
> — [MySQL 8.4 · TRUNCATE TABLE](https://dev.mysql.com/doc/refman/8.4/en/truncate-table.html)

```text
MySQL 에서 실제로 일어난 일

START TRANSACTION;      <- 트랜잭션 시작
INSERT ...;             <- ★ 이 변경도
TRUNCATE t51_a;         <- ★ 여기서 암묵 커밋 — 앞의 INSERT 까지 확정된다
                           TRUNCATE 자신은 트랜잭션 밖에서 돈다
ROLLBACK;               <- 되돌릴 것이 하나도 없다
```

**`TRUNCATE` 앞에서 한 `INSERT` 에 주는 영향** — **그것도 커밋된다.**\
★ 그래서 MySQL 에서 `TRUNCATE` 를 트랜잭션 스크립트에 넣으면 **그 문 하나만 위험한 것이 아니라\
그 앞의 모든 문이 안전망 밖으로 나간다.**

**처방** — MySQL 에서 「비우고 다시 채우기」가 필요하면\
① `DELETE` 를 쓰거나 ② **새 표에 채운 뒤 `RENAME TABLE` 로 바꿔 끼운다**(★ 후자는 이 편에서 던져 보지 않았다).

---

### 4. 비운 뒤 다음 번호 — **PG (6, 6, 1) · MySQL (6, 1, 문법 없음)**

**출력**

두 엔진 다 **「다음 번호 6」** 으로 맞춘 뒤 던졌다(PG 는 `ALTER TABLE … ALTER COLUMN id RESTART WITH 6`).

```text
### SQL: BEGIN; DELETE FROM t51_a; INSERT INTO t51_a (v) VALUES ('new'); SELECT id FROM t51_a; ROLLBACK;
--- PG 18.6 ---
BEGIN
DELETE 5
INSERT 0 1
 id 
----
  6
(1 row)
ROLLBACK

### SQL: BEGIN; TRUNCATE t51_a; INSERT INTO t51_a (v) VALUES ('new'); SELECT id FROM t51_a; ROLLBACK;
--- PG 18.6 ---
 id 
----
  6            <- ★ 초기화되지 않았다
(1 row)

### SQL: BEGIN; TRUNCATE t51_a RESTART IDENTITY; INSERT INTO t51_a (v) VALUES ('new'); SELECT id FROM t51_a; ROLLBACK;
--- PG 18.6 ---
 id 
----
  1
(1 row)
```

```text
### SQL: START TRANSACTION; DELETE FROM t51_a; INSERT INTO t51_a (v) VALUES ('new'); SELECT * FROM t51_a; ROLLBACK;
--- MySQL 8.4.10 ---
+----+------+
| id | v    |
+----+------+
|  6 | new  |
+----+------+

### SQL: TRUNCATE t51_a; INSERT INTO t51_a (v) VALUES ('new'); SELECT * FROM t51_a;
--- MySQL 8.4.10 ---
+----+------+
| id | v    |
+----+------+
|  1 | new  |          <- ★ 적지 않아도 초기화됐다
+----+------+

### SQL: TRUNCATE t51_a RESTART IDENTITY;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'RESTART IDENTITY' at line 1
```

**왜 그런가**

```text
                              PG 18.6          MySQL 8.4.10
(a) DELETE                    6                6
(b) TRUNCATE                  ★ 6             ★ 1
(c) TRUNCATE RESTART IDENTITY 1                ★ 문법이 없다 (ERROR 1064)
```

MySQL 매뉴얼이 (b) 를 명시한다.

> "Any `AUTO_INCREMENT` value is reset to its start value. This is true even for `MyISAM` and `InnoDB`, which normally do not reuse sequence values."\
> — [MySQL 8.4 · TRUNCATE TABLE](https://dev.mysql.com/doc/refman/8.4/en/truncate-table.html)

★ **PG 에서 시퀀스는 표와 별개의 객체**라 `TRUNCATE` 가 건드리지 않는다 — 그래서 옵션이 따로 있다.\
MySQL 의 `AUTO_INCREMENT` 는 **표의 속성**이라 표를 새로 만들면 같이 초기화된다([45 번](../45-check-not-null-default-generated-columns/)의 구조 차이가 여기서 결과로 나타난다).

---

### 5. 롤백하면 번호도 돌아오나 — **아니다. `'y'` 는 7 이다**

**출력**

```text
--- PG 18.6 ---
BEGIN; INSERT INTO t51_a (v) VALUES ('x'); ROLLBACK;
INSERT INTO t51_a (v) VALUES ('y');
SELECT * FROM t51_a ORDER BY id;
 id | v 
----+---
  1 | a
  2 | b
  3 | c
  4 | d
  5 | e
  7 | y        <- ★ 6 이 비었다
(6 rows)

--- MySQL 8.4.10 ---
START TRANSACTION; INSERT INTO t51_a (v) VALUES ('x'); ROLLBACK;
INSERT INTO t51_a (v) VALUES ('y'); SELECT * FROM t51_a ORDER BY id;
+----+------+
| id | v    |
+----+------+
|  1 | a    |
|  2 | b    |
|  3 | c    |
|  4 | d    |
|  5 | e    |
|  7 | y    |    <- ★ 여기도 6 이 비었다
+----+------+
```

**왜 그런가** — **번호 발급은 트랜잭션 밖에서 일어난다.**\
그렇지 않으면 동시에 들어오는 세션들이 서로의 번호를 기다려야 한다.

```text
번호 발급이 트랜잭션 안이면 : 세션 A 가 커밋할 때까지 세션 B 가 번호를 못 받는다
번호 발급이 트랜잭션 밖이면 : 아무도 안 기다린다. ★ 대신 롤백하면 번호가 빈다
```

★ **자동 증가 번호에 「연속」을 기대하면 안 된다.** 순서는 보장돼도 빈칸은 생긴다.\
(둘 다 「같은 값이 나왔다」 — 그런데 이것은 **두 엔진이 같은 설계 선택을 했다**는 관찰이지\
표준이 정한 것이라는 뜻은 아니다.)

---

### 6. ★ FK 자식이 있는 표 — **(a) 막힌다 / (b) 막힌다 / (c) 자식을 비워도 막힌다**

**출력**

```text
### SQL: DELETE FROM t51_p WHERE id = 1;
--- PG 18.6 ---
ERROR:  update or delete on table "t51_p" violates foreign key constraint "t51_c_fk" on table "t51_c"
DETAIL:  Key (id)=(1) is still referenced from table "t51_c".
--- MySQL 8.4.10 ---
ERROR 1451 (23000) at line 1: Cannot delete or update a parent row: a foreign key constraint fails
  (`study`.`t51_c`, CONSTRAINT `t51_c_fk` FOREIGN KEY (`p_id`) REFERENCES `t51_p` (`id`))

### SQL: TRUNCATE t51_p;
--- PG 18.6 ---
ERROR:  cannot truncate a table referenced in a foreign key constraint
DETAIL:  Table "t51_c" references "t51_p".
HINT:  Truncate table "t51_c" at the same time, or use TRUNCATE ... CASCADE.
--- MySQL 8.4.10 ---
ERROR 1701 (42000) at line 1: Cannot truncate a table referenced in a foreign key constraint
  (`study`.`t51_c`, CONSTRAINT `t51_c_fk`)

### SQL: DELETE FROM t51_c;                 -- 자식 행을 0개로 만든다
--- PG 18.6 ---            --- MySQL 8.4.10 ---
DELETE 3                   (성공)

### SQL: TRUNCATE t51_p;                    -- (c) 다시 던진다
--- PG 18.6 ---
ERROR:  cannot truncate a table referenced in a foreign key constraint
DETAIL:  Table "t51_c" references "t51_p".
HINT:  Truncate table "t51_c" at the same time, or use TRUNCATE ... CASCADE.
--- MySQL 8.4.10 ---
ERROR 1701 (42000) at line 1: Cannot truncate a table referenced in a foreign key constraint
  (`study`.`t51_c`, CONSTRAINT `t51_c_fk`)
```

**왜 그런가 — 보는 것이 다르다.**

```text
            무엇을 검사하나                    자식 행이 0개면
DELETE      실제 참조 행을 행마다 본다          ★ 통과한다
TRUNCATE    ★ 제약의 존재만 본다 (행을 안 본다) ★ 여전히 막힌다
```

`TRUNCATE` 는 **행을 하나씩 보지 않는 것이 존재 이유**다. 행을 안 보니 참조 검사도 못 한다.\
그래서 **제약이 있다는 사실만으로 거부**한다.

> "`TRUNCATE` cannot be used on a table that has foreign-key references from other tables, unless all such tables are also truncated in the same command."\
> — [PostgreSQL 18 · TRUNCATE](https://www.postgresql.org/docs/18/sql-truncate.html)

★ **PG 는 `HINT` 로 우회법까지 알려 준다.** MySQL 은 제약 이름만 준다.

---

### 7. 두 개의 `CASCADE` — **같은 것이 아니다. `t51_cc` 에 남는 행이 0 과 1 이다**

**출력**

```text
### SQL: BEGIN; TRUNCATE t51_pc CASCADE; SELECT (SELECT count(*) FROM t51_pc) AS p, (SELECT count(*) FROM t51_cc) AS c; ROLLBACK;
--- PG 18.6 ---
NOTICE:  truncate cascades to table "t51_cc"
BEGIN
TRUNCATE TABLE
 p | c 
---+---
 0 | 0            <- ★ 자식 표가 통째로 비었다
(1 row)
ROLLBACK

### SQL: BEGIN; DELETE FROM t51_pc WHERE id=1; SELECT (SELECT count(*) FROM t51_pc) AS p, (SELECT count(*) FROM t51_cc) AS c; ROLLBACK;
--- PG 18.6 ---
BEGIN
DELETE 1
 p | c 
---+---
 1 | 1            <- 부모 1행 · 자식 1행 (p_id=2 인 행만 살아남았다)
(1 row)
ROLLBACK

--- MySQL 8.4.10 ---  (같은 DELETE)
+----------+------+------+
| reported | p    | c    |
+----------+------+------+
|        1 |    1 |    1 |
+----------+------+------+
```

MySQL 에는 `TRUNCATE … CASCADE` 자체가 없다.

```text
### SQL: TRUNCATE t51_pc CASCADE;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'CASCADE' at line 1
```

**왜 그런가 — 두 `CASCADE` 는 대상이 다르다.**

```text
ON DELETE CASCADE      "지워진 부모 행을 참조하던 자식 행" 만 지운다
                       -> p_id=1 인 두 행만 사라지고 p_id=2 인 행은 남는다  (c = 1)

TRUNCATE ... CASCADE   ★ 자식 "표 전체" 를 비운다 (참조 여부와 무관)
                       -> p_id=2 인 행까지 사라진다                        (c = 0)
```

★ **`TRUNCATE … CASCADE` 는 참조하지 않는 행까지 지운다.** 이름이 같아서 가장 쉽게 오해하는 자리다.\
`ON DELETE CASCADE` 자체는 [44 번](../44-foreign-key-referential-actions/)이 정본이다.

★ 그리고 PG 의 `NOTICE` 가 **무엇이 같이 비워지는지 알려 준다** — 「경고도 출력이다」가 여기서도 쓰인다.

---

### 8. 영향 행 수를 믿어도 되나 — **`1` 이다. 실제로는 세 행이 사라졌다**

**출력**

```text
--- PG 18.6 ---
DELETE 1                     <- 1 이라고 보고한다
 p | c 
---+---
 1 | 1                       <- 부모 2->1 (한 행) · 자식 3->1 (두 행) = 세 행이 사라졌다
(1 row)

--- MySQL 8.4.10 ---
+----------+------+------+
| reported | p    | c    |
+----------+------+------+
|        1 |    1 |    1 |   <- ROW_COUNT() 도 1 이다
+----------+------+------+
```

**왜 그런가** — 영향 행 수는 **그 문이 직접 지목한 표의 행**만 센다.\
참조 동작(`ON DELETE CASCADE`)으로 따라 지워진 자식 행은 **그 숫자에 안 들어간다.**

★ **「1행을 지웠습니다」를 사용자에게 그대로 보여 주면 거짓말이 된다.**\
[49 번의 `INSERT ... SELECT` 0행](../49-insert-multi-row-and-insert-select/)·[50 번의 영향 행 수 4 대 3](../50-update-with-join-and-subquery/)과\
같은 교훈이다 — **보고 값이 아니라 `SELECT` 로 세야 안다.**

---

### 9. ★ MySQL 의 FK 우회 — **`p=0, c=3` 이다. 참조 무결성이 깨졌다**

**출력**

```text
### SQL: SET FOREIGN_KEY_CHECKS=0; TRUNCATE t51_p; SET FOREIGN_KEY_CHECKS=1; SELECT (SELECT count(*) FROM t51_p) AS p_rows, (SELECT count(*) FROM t51_c) AS c_rows;
--- MySQL 8.4.10 ---
+--------+--------+
| p_rows | c_rows |
+--------+--------+
|      0 |      3 |
+--------+--------+

### SQL: SELECT * FROM t51_c ORDER BY id;
--- MySQL 8.4.10 ---
+----+------+
| id | p_id |
+----+------+
| 11 |    1 |      <- t51_p 에 id=1 은 이제 없다
| 12 |    1 |
| 13 |    2 |      <- id=2 도 없다
+----+------+
```

**왜 그런가** — 검사를 껐으니 `TRUNCATE` 가 통과했고, **부모만 사라졌다.**\
★ **`FOREIGN_KEY_CHECKS=1` 로 다시 켜도 엔진은 기존 행을 재검사하지 않는다.**\
그래서 고아 행 셋이 그대로 남는다.

```text
PG 의 CASCADE                          MySQL 의 FOREIGN_KEY_CHECKS=0
+-----------------------------+        +-----------------------------+
| 자식 표도 같이 비운다        |        | 부모만 비운다                |
| 무결성이 유지된다            |        | ★ 고아 행 3개가 남는다       |
| NOTICE 로 알려 준다          |        | ★ 아무 말도 없다             |
| ROLLBACK 으로 되돌아온다     |        | ★ 되돌아오지 않는다 (2번)    |
+-----------------------------+        +-----------------------------+
```

★★ **「통과했는데 안 한 것」이다.** 문은 성공했고, 경고도 없고, **불변식만 거짓이 됐다.**\
그때부터 `t51_c` 를 조인하는 모든 질의가 조용히 행을 잃는다([14 LEFT JOIN](../14-left-right-outer-join/)이 그 장면이다).

(이 실험 뒤 `t51_p`·`t51_c` 를 **같은 값으로 다시 채워** 복구했다.)

---

### 10. 비운 뒤 디스크 — **`DELETE` 는 거의 안 준다. `TRUNCATE` 는 즉시 준다**

**출력**

```text
--- PG 18.6 ---
 size_before                 size_after_delete | rows        size_after_truncate | rows 
-------------                -------------------+------      ---------------------+------
 3304 kB                      3304 kB           |    0        8192 bytes          |    0
```

```text
--- MySQL 8.4.10 ---  (ANALYZE TABLE 뒤 information_schema 조회)
+---------+--------+   +----------------------+--------+   +------------------------+--------+
| size_kb | n_rows |   | size_kb_after_delete | n_rows |   | size_kb_after_truncate | n_rows |
+---------+--------+   +----------------------+--------+   +------------------------+--------+
|    2576 |  50000 |   |                 2128 |      0 |   |                     16 |      0 |
+---------+--------+   +----------------------+--------+   +------------------------+--------+
```

**왜 그런가**

```text
DELETE 후 표 안에 남는 것
  PG    : 죽은 튜플(dead tuple) — 파일에는 그대로 있다. VACUUM 이 회수한다
  MySQL : 비워진 페이지 — 파일 크기는 그대로, 다음 INSERT 가 재사용한다
TRUNCATE 후
  두 엔진 다 : 내용물 자체를 버리고 새 통을 만든다 -> 즉시 최소 크기
```

PG 는 카탈로그에 숫자로 남는다.

```text
### SQL: SELECT n_live_tup, n_dead_tup, pg_size_pretty(pg_total_relation_size('t51_big')) AS size FROM pg_stat_user_tables WHERE relname='t51_big';
--- PG 18.6 ---  (DELETE 직후)
 n_live_tup | n_dead_tup |  size   
------------+------------+---------
          0 |      50000 | 3312 kB
(1 row)

--- PG 18.6 ---  (VACUUM t51_big 뒤)
 n_live_tup | n_dead_tup | size_after_vacuum 
------------+------------+-------------------
          0 |          0 | 1128 kB
(1 row)
```

★ **`VACUUM` 을 돌려도 `TRUNCATE` 만큼 작아지지 않았다** — 1128 kB 대 8192 bytes.\
`VACUUM` 은 **재사용 가능하게 만드는 것**이지 파일을 완전히 줄이는 것이 아니다\
(완전히 줄이려면 `VACUUM FULL` 이 필요한데 **이 편에서는 던져 보지 않았다** — 표 전체를 다시 쓰는 무거운 작업이다).

---

### 11. 얼마나 빠른가 — **PG 는 6\~7배, MySQL 은 1.3배. 결론의 강도가 다르다**

**출력** (5만 행, 3판 원값)

```text
--- PG 18.6 ---  DELETE FROM t51_big;        --- PG 18.6 ---  TRUNCATE t51_big;
DELETE 50000   Time: 26.033 ms               TRUNCATE TABLE   Time: 4.740 ms
DELETE 50000   Time: 31.312 ms               TRUNCATE TABLE   Time: 4.319 ms
DELETE 50000   Time: 32.893 ms               TRUNCATE TABLE   Time: 4.962 ms

--- MySQL 8.4.10 ---  DELETE                 --- MySQL 8.4.10 ---  TRUNCATE
delete_ms = 123.8520                         truncate_ms = 90.2080
delete_ms = 125.2010                         truncate_ms = 81.8240
delete_ms = 109.4050                         truncate_ms = 84.3030
```

**왜 그런가 — 신호 대 잡음을 먼저 본다.**

```text
PG    : 26~33 ms  대  4.3~5.0 ms   -> 신호 약 6~7배 · 흔들림 약 25%   -> ★ 결론이 선다
MySQL : 109~125 ms 대 82~90 ms     -> 신호 약 1.3배 · 흔들림 약 13%   -> ★ 결론이 약하다
```

★ **두 엔진에서 결론의 강도가 다르다.**\
PG 에서는 `TRUNCATE` 가 확실히 빠르다. **MySQL 8.4.10 에서는 이 크기로 「훨씬 빠르다」를 단정할 수 없다** —\
신호가 잡음의 세 배 정도밖에 안 된다.

★ **원인 추정** — MySQL 의 `TRUNCATE` 는 **테이블스페이스 파일을 지우고 다시 만드는** 비용을 치른다.\
**이 설명은 추론이다** — 파일시스템 수준을 직접 재지 않았다.

★ **측정 조건을 다시 밝힌다.** JMH 가 아니라 클라이언트 타이머이고, 컨테이너·캐시 상태가 섞여 있다.\
**재현되는 것은 절댓값이 아니라 자릿수와 방향**이다.

**속도보다 확실한 근거는 10번의 공간이다.** 그쪽은 두 엔진에서 결론이 같고 강하다.

---

### 12. ★ 대량 삭제를 왜 나누나 — **잠금 50,111 개를 커밋까지 들고 있기 때문**

**출력**

```text
### SQL: START TRANSACTION; DELETE FROM t51_big; SELECT COUNT(*) AS locks_held FROM performance_schema.data_locks; ROLLBACK; SELECT COUNT(*) AS locks_after FROM performance_schema.data_locks;
--- MySQL 8.4.10 ---
+------------+
| locks_held |
+------------+
|      50111 |
+------------+
+-------------+
| locks_after |
+-------------+
|           0 |
+-------------+

### SQL: START TRANSACTION; DELETE FROM t51_big LIMIT 10000; SELECT COUNT(*) AS locks_held_chunk FROM performance_schema.data_locks; ROLLBACK;
--- MySQL 8.4.10 ---
+------------------+
| locks_held_chunk |
+------------------+
|            10022 |
+------------------+
```

트랜잭션 자체의 지표도 같은 말을 한다.

```text
### SQL: START TRANSACTION; DELETE FROM t51_big; SELECT trx_rows_modified, trx_rows_locked, trx_lock_structs FROM information_schema.innodb_trx; ROLLBACK;
--- MySQL 8.4.10 ---
+-------------------+-----------------+------------------+
| trx_rows_modified | trx_rows_locked | trx_lock_structs |
+-------------------+-----------------+------------------+
|             50000 |           50110 |              111 |
+-------------------+-----------------+------------------+

### SQL: (같은 문에 LIMIT 10000 을 붙여)
+-------------------+-----------------+------------------+
| trx_rows_modified | trx_rows_locked | trx_lock_structs |
+-------------------+-----------------+------------------+
|             10000 |           10021 |               23 |
+-------------------+-----------------+------------------+
```

PG 쪽에 대응하는 수치는 죽은 튜플이다(10번) — `n_dead_tup = 50000`.

**왜 그런가**

```text
한 문으로 5만 행                        1만 행씩 다섯 번
+---------------------------+           +---------------------------+
| 잠금 50,111 개            |           | 잠금 10,022 개 x 5 회     |
| 커밋까지 한 번도 안 풀린다 |           | 회마다 커밋하고 풀린다     |
| 실패하면 5만 행을 되돌린다 |           | 실패해도 1만 행만 되돌린다 |
+---------------------------+           +---------------------------+
  -> 다른 세션이 계속 기다린다              -> 틈틈이 지나갈 수 있다
```

★ **잰 것과 못 잰 것을 나눠 적는다.**

```text
잰 것   : MySQL 의 행 잠금 수(50,111) · 수정 행 수(50,000) · PG 의 죽은 튜플(50,000)
못 잰 것: 되돌리기 정보(undo log)의 크기 · 복제 지연
          (복제를 구성하지 않았고 undo 크기를 직접 조회하지 않았다)
```

나눠 돌면 **전체 소요는 늘어난다.** 대신 **다른 세션이 멈추지 않고, 실패 시 되돌릴 양이 작다.**

---

### 13. 나눠 도는 문법 — **MySQL 만 `LIMIT`. PG 는 서브쿼리로 고른다**

**출력**

```text
### SQL: DELETE FROM t51_big LIMIT 10000;
--- PG 18.6 ---
ERROR:  syntax error at or near "LIMIT"
LINE 1: DELETE FROM t51_big LIMIT 10000
                            ^
--- MySQL 8.4.10 ---
+---------+-------+
| deleted | n     |
+---------+-------+
|   10000 | 40000 |
+---------+-------+

### SQL: BEGIN; DELETE FROM t51_big WHERE id IN (SELECT id FROM t51_big ORDER BY id LIMIT 10000); SELECT count(*) AS n FROM t51_big; ROLLBACK;
--- PG 18.6 ---
BEGIN
DELETE 10000
   n   
-------
 40000
(1 row)
ROLLBACK
```

**왜 그런가** — PG 의 `DELETE` 문법에는 `LIMIT` 이 없다. **대상을 서브쿼리로 골라 넘긴다.**\
[50 번 13절](../50-update-with-join-and-subquery/)의 `UPDATE` 쪽과 **같은 관용구**다.

```sql
-- 두 엔진에서 같은 글자로 도는 형태
DELETE FROM t51_big WHERE id IN (SELECT id FROM t51_big ORDER BY id LIMIT 10000);
```

★ `ORDER BY` 를 붙이면 매 회차가 **같은 쪽부터** 지워 인덱스 스캔이 앞에서 진행된다.\
**이 효과는 계획으로 확인하지 않았다** — 계획은 통계에 흔들린다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).

---

### 14. ★★ 안전 모드 — **(a) 막힌다 / (b) 통과한다**

**출력**

```text
### SQL: SET sql_safe_updates=1; DELETE FROM t51_c;
--- MySQL 8.4.10 ---
ERROR 1175 (HY000) at line 1: You are using safe update mode and you tried to update a table
  without a WHERE that uses a KEY column.

### SQL: SET sql_safe_updates=1; START TRANSACTION; DELETE FROM t51_c WHERE id=11; SELECT ROW_COUNT() AS deleted; ROLLBACK;
--- MySQL 8.4.10 ---
+---------+
| deleted |
+---------+
|       1 |
+---------+

### SQL: SET sql_safe_updates=1; TRUNCATE t51_c; SELECT count(*) AS n FROM t51_c;
--- MySQL 8.4.10 ---
+---+
| n |
+---+
| 0 |             <- ★★ 그대로 비워졌다
+---+
```

**왜 그런가** — 매뉴얼의 문장에 `TRUNCATE` 가 없다.

> "If this option is enabled, **`UPDATE` and `DELETE` statements** that do not use a key in the `WHERE` clause or a `LIMIT` clause produce an error."\
> — [MySQL 8.4 · mysql Client Options](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html)

```text
sql_safe_updates = 1 인 상태에서

DELETE FROM t (WHERE 없음)  -> ERROR 1175. 막힌다
TRUNCATE t                  -> ★ 통과한다 + 롤백도 안 된다(2번) + 자동 증가도 초기화(4번)
```

★★ **가장 위험한 문에 가장 약한 방어**가 걸려 있다.\
`TRUNCATE` 는 DDL 이라 안전 모드의 대상 목록 밖이다(3번).

「안전 모드를 켜 뒀으니 괜찮다」는 감각이 **틀린 자리가 정확히 여기**다.\
[50 번 9절](../50-update-with-join-and-subquery/)에서 배운 규칙이 여기서 구멍을 드러낸다.

(이 실험 뒤 `t51_c` 를 다시 채워 복구했다.)

---

### 15. 조인을 쓰는 삭제 — **서로를 거부한다. 이식 형태는 `IN (SELECT …)`**

**출력**

```text
### SQL: BEGIN; DELETE FROM t51_c USING t51_p WHERE t51_p.id = t51_c.p_id AND t51_p.name='p1'; SELECT * FROM t51_c ORDER BY id; ROLLBACK;
--- PG 18.6 ---
BEGIN
DELETE 2
 id | p_id 
----+------
 13 |    2
(1 row)
ROLLBACK

### SQL: DELETE FROM t51_c USING t51_p WHERE t51_p.id = t51_c.p_id AND t51_p.name='p1';
--- MySQL 8.4.10 ---
ERROR 1109 (42S02) at line 1: Unknown table 't51_c' in MULTI DELETE
```

```text
### SQL: START TRANSACTION; DELETE c FROM t51_c c JOIN t51_p p ON p.id = c.p_id WHERE p.name='p1'; SELECT ROW_COUNT() AS deleted; SELECT * FROM t51_c ORDER BY id; ROLLBACK;
--- MySQL 8.4.10 ---
+---------+
| deleted |
+---------+
|       2 |
+---------+
+----+------+
| id | p_id |
+----+------+
| 13 |    2 |
+----+------+

### SQL: DELETE c FROM t51_c c JOIN t51_p p ON p.id = c.p_id WHERE p.name='p1';
--- PG 18.6 ---
ERROR:  syntax error at or near "c"
LINE 1: DELETE c FROM t51_c c JOIN t51_p p ON p.id = c.p_id WHERE p....
               ^
```

★ **MySQL 에도 `USING` 은 있다 — 다만 지울 표를 따로 지목해야 한다.**

```text
### SQL: START TRANSACTION; DELETE FROM c USING t51_c c JOIN t51_p p ON p.id = c.p_id WHERE p.name='p1'; SELECT ROW_COUNT() AS deleted; ROLLBACK;
--- MySQL 8.4.10 ---
+---------+
| deleted |
+---------+
|       2 |
+---------+
```

**왜 그런가**

```text
PG    : DELETE FROM 대상 USING 상대 WHERE 조인조건
                     ^^^^ 대상이 FROM 뒤에 한 번. 상대는 USING 에
MySQL : DELETE 별칭 FROM 대상 별칭 JOIN 상대 ON ...
        ^^^^^^ ★ "어느 표를 지울지" 를 앞에 따로 적는다
        (또는 DELETE FROM 별칭 USING 대상 별칭 JOIN 상대 ON ...)
```

`ERROR 1109 Unknown table 't51_c' in MULTI DELETE` 가 그 규칙을 그대로 말한다 —\
「**지울 표 목록에 `t51_c` 가 없다**」는 뜻이다.

**이식 형태는 서브쿼리다.**

```sql
DELETE FROM t51_c WHERE p_id IN (SELECT id FROM t51_p WHERE name = 'p1');
```

[50 번 1절](../50-update-with-join-and-subquery/)의 `UPDATE` 와 **같은 구조의 방언 분기**다.

---

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `autocommit`·`sql_safe_updates`·엔진 확인 (머리말) | MySQL 8.4.10 | 3회 | **InnoDB 가 전제다** |
| 표 6개 생성·삭제 | PG 18.6 · MySQL 8.4.10 | 각 6회 | `t51_a`·`t51_p`·`t51_c`·`t51_pc`·`t51_cc`·`t51_big` |
| `DELETE` 롤백 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **둘 다 5행 복귀** |
| ★★ `TRUNCATE` 롤백 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 5 / MySQL 0 — MySQL 쪽은 손으로 복구했다** |
| 자동 증가 3경우 (4번) | PG 18.6 | 3회 | **출발점을 6으로 맞추고** 각각 던졌다 |
| 자동 증가 2경우 (4번) | MySQL 8.4.10 | 2회 | `DELETE` 6 / `TRUNCATE` 1 |
| `RESTART IDENTITY` (4번) | MySQL 8.4.10 | 1회 | `ERROR 1064` |
| 롤백 후 번호 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **둘 다 6이 비고 7이 나왔다** |
| FK 부모 `DELETE` (6a) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `1451` / `violates foreign key constraint` |
| FK 부모 `TRUNCATE` (6b) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `1701` / `cannot truncate…` + `HINT` |
| ★ 자식 비운 뒤 `TRUNCATE` (6c) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **여전히 막힌다 — 제약만 보는 것이 근거** |
| `TRUNCATE … CASCADE` (7번) | PG 18.6 | 2회 | `NOTICE` + `p=0, c=0` + 롤백 복귀 |
| `ON DELETE CASCADE` 대비 (7·8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`c=1` — 두 CASCADE 가 다르다** |
| MySQL 에 `TRUNCATE … CASCADE` (7번) | MySQL 8.4.10 | 1회 | `ERROR 1064` |
| ★ `FOREIGN_KEY_CHECKS=0` (9번) | MySQL 8.4.10 | 2회 | **고아 행 3개 — 손으로 복구했다** |
| 표 크기 (10번) | PG 18.6 | 4회 | `3304 kB` → `3304 kB` → `8192 bytes` |
| 표 크기 (10번) | MySQL 8.4.10 | 3회 | `ANALYZE TABLE` 뒤 조회 — `2576`→`2128`→`16 kB` |
| 죽은 튜플·`VACUUM` (10번) | PG 18.6 | 3회 | `n_dead_tup 50000` → `VACUUM` → `1128 kB` |
| ★ 속도 (11번) | PG 18.6 | **3판 x 2문** | **26\~33 ms 대 4.3\~5.0 ms — 신호 6\~7배** |
| ★ 속도 (11번) | MySQL 8.4.10 | **3판 x 2문** | **109\~125 ms 대 82\~90 ms — 신호 1.3배, 결론 약함** |
| ★ 잠금 수 (12번) | MySQL 8.4.10 | 2회 | **50,111 대 10,022** |
| `innodb_trx` 지표 (12번) | MySQL 8.4.10 | 2회 | `trx_rows_modified` 50000 대 10000 |
| `DELETE … LIMIT` (13번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 구문 오류 / MySQL 10000행** |
| PG 관용구 (13번) | PG 18.6 | 1회 | `DELETE 10000` |
| ★★ 안전 모드와 `TRUNCATE` (14번) | MySQL 8.4.10 | 3회 | **`DELETE` 는 막고 `TRUNCATE` 는 통과** |
| 조인 삭제 3형태 (15번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`ERROR 1109` 가 MySQL 규칙의 근거** |
| `DELETE IGNORE` 문법 확인 (문법 절) | MySQL 8.4.10 | 1회 | 통과 — 이 편에서는 더 파고들지 않았다 |

**구현 의존 항목** — 2·4번의 **트랜잭션 성질과 자동 증가**, 6·7·15번의 **에러 코드·문법**,\
10·11·12번의 **수치 전부**.\
외울 것은 숫자가 아니라 「**`TRUNCATE` 는 표 단위 작업이라 되돌리기·참조 검사·조건이 전부 다르다**」는 성질이다.

**언어 보장 항목** — 1·2·3·6번.\
`DELETE` 가 DML 이라는 것, **PG 의 `TRUNCATE` 가 transaction-safe 라는 것**,\
**MySQL 의 `TRUNCATE` 가 암묵 커밋이라는 것**, `TRUNCATE` 가 FK 참조를 받는 표에 못 쓰인다는 것은\
두 매뉴얼이 문장으로 정한 것이다.

★ **두 문서가 서로 다른 것을 보장하는 자리** — 2·3번.\
「어느 쪽이 표준인가」는 이 편에서 **판정하지 않는다**(목록 README 의 규칙 — 표준 조항 번호를 확인하지 못했다).

**버전을 적은 자리** — 없다. **두 매뉴얼에 이 문들의 도입 버전이 적혀 있지 않아 적지 않았다.**

**돌려 보지 않은 것** — ① MyISAM 등 **다른 스토리지 엔진** ② `VACUUM FULL` ③ MySQL 의 `RENAME TABLE` 교체 기법\
④ **undo log 크기와 복제 지연**(복제를 구성하지 않았다) ⑤ `TRUNCATE` 가 잡는 **잠금 수준**([57 명시적 잠금과 교착](../57-explicit-locking-and-deadlock/))\
⑥ 나눠 도는 `DELETE` 의 **실행 계획**(통계에 흔들린다).

★ **복구한 자리** — 2번(MySQL `t51_a` 5행)·9번(MySQL `t51_p`·`t51_c`)·14번(MySQL `t51_c`)에서\
**롤백이 안 되는 문을 던졌으므로 값을 손으로 다시 채웠다.** 그 사실을 여기 남긴다.

**DB 잔재** — 없다. `t51_` 로 시작하는 표를 두 엔진에서 전부 삭제했고 `emp`·`dept` 는 **읽지도 쓰지도 않았다.**\
두 엔진의 최종 표 목록은 [54 편의 「실행 검증」](../54-returning-and-data-modifying-cte/3-answer.md)에 있다.
