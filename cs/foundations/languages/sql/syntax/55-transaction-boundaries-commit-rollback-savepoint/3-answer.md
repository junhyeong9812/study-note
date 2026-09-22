# sql/55-트랜잭션 경계 — `COMMIT`·`ROLLBACK`·`SAVEPOINT` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> **출력 형식** — PG 는 `psql -a`(입력 에코) 그대로다. MySQL 은 `mysql -v -t` 의 문장 에코를 쓰되\
> 에코를 감싸는 `--------------` 구분선만 지웠다. **결과·에러 문자열은 한 글자도 손대지 않았다.**\
> ★ **두 세션 실험은 이름 붙인 FIFO 로 두 접속을 열어 두고 한 줄씩 먹였다**(맨 끝 「실행 검증」에 스크립트 그대로).\
> ★ **기존 `emp`·`dept` 는 읽지도 잠그지도 않았다.** 이 편은 `t55_acct` 만 쓴다.\
> 문서 근거는 [PG 18 BEGIN](https://www.postgresql.org/docs/18/sql-begin.html) · [PG 18 SAVEPOINT](https://www.postgresql.org/docs/18/sql-savepoint.html) · [MySQL 8.4 COMMIT/ROLLBACK](https://dev.mysql.com/doc/refman/8.4/en/commit.html) · [MySQL 8.4 Implicit Commit](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. PG 는 그런 설정이 없다고 하고, MySQL 은 1 을 준다

**출력**

```text
### SQL: (PG) SHOW autocommit;
--- PG 18.6 ---
SHOW autocommit;
ERROR:  unrecognized configuration parameter "autocommit"
```

```text
### psql: \echo :AUTOCOMMIT
--- PG 18.6 ---
on
```

```text
### SQL: (MySQL) SELECT @@autocommit AS ac;
--- MySQL 8.4.10 ---
+------+
| ac   |
+------+
|    1 |
+------+
```

**왜 그런가** — **둘 다 기본이 자동 커밋인 것은 같다.** 다른 것은 **그 스위치가 어느 층에 있나**다.

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 자동 커밋 | **서버 설정이 아니다** — 클라이언트(`psql` 변수 `:AUTOCOMMIT` = `on`) | **서버 세션 변수** `@@autocommit = 1` |
| 끄는 법 | 드라이버·클라이언트 설정 (또는 그냥 `BEGIN` 을 친다) | `SET autocommit = 0;` |

그래서 PG 에서 「자동 커밋을 껐다」는 말은 **애플리케이션 쪽 이야기**이고, 서버에 물어봐도 알 수 없다.

---

### 2. 900 — 이미 확정됐다

**출력** — 세션 B (두 엔진 다 같다)

```text
--- PG 18.6 ---                          --- MySQL 8.4.10 ---
SELECT bal FROM t55_acct WHERE id = 1;   SELECT bal FROM t55_acct WHERE id = 1
 bal                                     +------+
-----                                    | bal  |
 900                                     +------+
(1 row)                                  |  900 |
                                         +------+
```

**왜 그런가** — `BEGIN` 을 안 쳤으므로 그 `UPDATE` 하나가 **곧 하나의 트랜잭션**이었고, 문이 끝나는 순간 커밋됐다.\
**되돌릴 방법이 없다.** 이어서 `BEGIN; UPDATE … 800;` 을 해도 B 는 계속 900 을 본다 — 그것은 아직 A 안에만 있다.\
그리고 A 가 `ROLLBACK` 하면 800 은 사라지고 B 는 여전히 900 이다(세 번째 읽기가 그 확인이다).

---

### 3. ★ PG 는 `900 / 1000`, MySQL 은 `111 / 222`

**출력**

```text
--- PG 18.6 ---
BEGIN;
BEGIN
UPDATE t55_acct SET bal = 111 WHERE id = 1;
UPDATE 1
INSERT INTO t55_acct VALUES (1, 'dup', 0);
ERROR:  duplicate key value violates unique constraint "t55_acct_pkey"
DETAIL:  Key (id)=(1) already exists.
UPDATE t55_acct SET bal = 222 WHERE id = 2;
SELECT id, bal FROM t55_acct ORDER BY id;
ERROR:  current transaction is aborted, commands ignored until end of transaction block
COMMIT;
ROLLBACK
ERROR:  current transaction is aborted, commands ignored until end of transaction block
--- 끝나고 ---
 id | bal
----+------
  1 |  900
  2 | 1000
(2 rows)
```

```text
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 3: Duplicate entry '1' for key 't55_acct.PRIMARY'
START TRANSACTION
UPDATE t55_acct SET bal = 111 WHERE id = 1
INSERT INTO t55_acct VALUES (1, 'dup', 0)
UPDATE t55_acct SET bal = 222 WHERE id = 2
SELECT id, bal FROM t55_acct ORDER BY id
+----+------+
| id | bal  |
+----+------+
|  1 |  111 |
|  2 |  222 |
+----+------+
COMMIT
--- 끝나고 ---
+----+------+
| id | bal  |
+----+------+
|  1 |  111 |
|  2 |  222 |
+----+------+
```

**왜 그런가** — **PG 는 트랜잭션을 통째로 중단 상태로 만든다.** 그 뒤의 `UPDATE` 도 `SELECT` 도 안 돈다.\
**MySQL 은 실패한 그 문만 되돌리고(문 단위 롤백) 트랜잭션은 계속 산다.** `COMMIT` 이 앞뒤 `UPDATE` 를 둘 다 확정한다.

★ **같은 다섯 줄이 한쪽에서는 「아무 일도 없었다」, 한쪽에서는 「반쯤 적용됐다」가 된다.**\
드라이버가 예외를 잡아 로그만 찍고 넘어가면, MySQL 쪽에서는 **깨진 상태가 커밋된 채 성공 응답**이 나간다.

---

### 4. `ROLLBACK` 으로 찍힌다

**출력**

```text
COMMIT;
ROLLBACK
ERROR:  current transaction is aborted, commands ignored until end of transaction block
```

**왜 그런가** — 중단된 트랜잭션에서는 `COMMIT` 도 확정을 못 한다. PG 는 그것을 롤백으로 처리하고\
**명령 태그를 `ROLLBACK` 으로 돌려준다.** 「커밋을 쳤는데 롤백이 찍혔다」가 곧 「이 트랜잭션은 죽어 있었다」는 신호다.

---

### 5. `800` 과 `1000`

**출력**

```text
--- PG 18.6 ---                            --- MySQL 8.4.10 ---
(ROLLBACK TO 직전)                          (ROLLBACK TO 직전)
 id | bal                                  +----+------+
----+-----                                 | id | bal  |
  1 | 800                                  +----+------+
  2 | 500                                  |  1 |  800 |
(2 rows)                                   |  2 |  500 |
                                           +----+------+
ROLLBACK TO SAVEPOINT sp1;                 ROLLBACK TO SAVEPOINT sp1
ROLLBACK
(직후)                                      (직후)
 id | bal                                  +----+------+
----+------                                | id | bal  |
  1 |  800                                 +----+------+
  2 | 1000                                 |  1 |  800 |
(2 rows)                                   |  2 | 1000 |
                                           +----+------+
```

**왜 그런가** — `SAVEPOINT sp1` 은 **`-100` 이 끝난 뒤** 찍혔다.\
`ROLLBACK TO` 는 **표식 이후의 변경만** 지우므로 `-500` 은 사라지고 `-100` 은 남는다. **두 엔진의 답이 같다.**

---

### 6. 살아 있다 — 괄호는 안 닫힌다

**왜 그런가** — `ROLLBACK TO SAVEPOINT` 는 **트랜잭션을 끝내지 않는다.** 표식 이후만 버리고 그 자리로 돌아갈 뿐이다.\
그 뒤에 `COMMIT` 을 치면 **표식 이전의 변경은 확정된다**(5번에서 `-100` 이 그렇다).\
그러니 「되돌렸다」와 「끝냈다」를 섞으면 안 된다 — 끝내려면 `COMMIT` 이나 `ROLLBACK` 을 따로 쳐야 한다.

---

### 7. 아무것도 되돌리지 않는다 — 이름만 뗀다

**출력**

```text
--- PG 18.6 ---
RELEASE SAVEPOINT sp1;
RELEASE
```

**왜 그런가** — `RELEASE` 는 **표식을 지우는 문**이다. 표식 이후의 변경은 **그대로 트랜잭션 안에 남는다.**\
그래서 `RELEASE` 뒤에 `COMMIT` 하면 그 변경들도 확정된다. 「`RELEASE` = 취소」로 외우면 정반대로 틀린다.

---

### 8. ★ 둘 다 에러다 — 그리고 PG 에서는 트랜잭션 전체가 날아간다

**출력**

```text
--- PG 18.6 ---
RELEASE SAVEPOINT sp1;
RELEASE
ROLLBACK TO SAVEPOINT sp1;
ERROR:  savepoint "sp1" does not exist
COMMIT;
ROLLBACK
SELECT id, bal FROM t55_acct ORDER BY id;
 id | bal
----+------
  1 |  900
  2 | 1000
(2 rows)
```

```text
--- MySQL 8.4.10 ---
ERROR 1305 (42000) at line 9: SAVEPOINT sp1 does not exist
```

**왜 그런가** — PG 에서는 이 에러도 **다른 에러와 똑같이** 트랜잭션을 중단시킨다.\
그 결과 `COMMIT` 이 `ROLLBACK` 으로 찍히고, **표식 이전의 `-100` 까지 전부 사라졌다**(800 이 아니라 900 이다).\
세이브포인트 이름 하나 잘못 불렀다고 트랜잭션 전체를 잃는 것 — 이것이 3번과 같은 규칙의 다른 얼굴이다.

---

### 9. PG 는 첫 줄에서, MySQL 은 둘째 줄에서

**출력**

```text
--- PG 18.6 ---                            --- MySQL 8.4.10 ---
SAVEPOINT sp1;                             SAVEPOINT sp9
ERROR:  SAVEPOINT can only be used in      (에러 없이 통과)
        transaction blocks                 ROLLBACK TO SAVEPOINT sp9
                                           ERROR 1305 (42000) at line 1:
                                             SAVEPOINT sp9 does not exist
```

**왜 그런가** — PG 는 **자리 자체를 막는다.** 트랜잭션 블록이 아니면 `SAVEPOINT` 를 못 친다.\
MySQL 은 그 문을 **받아들인다.** 그런데 바로 다음 줄에서 그 이름이 없다고 한다.\
자동 커밋 상태에서는 그 `SAVEPOINT` 문 자체가 하나의 트랜잭션이었고, 끝난 트랜잭션의 표식은 남지 않는다는 뜻으로 읽힌다.

★ **「통과했다」가 「먹혔다」는 아니다.** MySQL 쪽은 **한 줄 뒤에** 터지므로 원인이 멀어 보인다.

---

### 10. ★ `777` 이 살아남고, 경고는 없다

**출력**

```text
--- MySQL 8.4.10 ---
START TRANSACTION
UPDATE t55_acct SET bal = 777 WHERE id = 1
START TRANSACTION
ROLLBACK
SELECT id, bal FROM t55_acct ORDER BY id
+----+------+
| id | bal  |
+----+------+
|  1 |  777 |
|  2 | 1000 |
+----+------+
COMMIT
ROLLBACK
SHOW WARNINGS
(빈 결과 — 행이 하나도 없다)
```

```text
--- PG 18.6 ---
BEGIN;
BEGIN
BEGIN;
WARNING:  there is already a transaction in progress
BEGIN
COMMIT;
COMMIT
COMMIT;
WARNING:  there is no transaction in progress
COMMIT
ROLLBACK;
WARNING:  there is no transaction in progress
ROLLBACK
```

**왜 그런가** — MySQL 문서의 암묵 커밋 목록에 **`START TRANSACTION` 자신이 들어 있다.**\
두 번째 `START TRANSACTION` 이 앞의 트랜잭션을 커밋했고, `ROLLBACK` 은 새로 열린 빈 트랜잭션을 되돌렸다.\
★ **`SHOW WARNINGS` 를 따로 물어도 비어 있다** — 경고조차 없다.

PG 는 중첩 `BEGIN` 을 **무시하고 경고만** 낸다(괄호는 하나뿐이다). 트랜잭션 밖의 `COMMIT`·`ROLLBACK` 도 경고 대상이다.\
**어느 쪽도 트랜잭션이 중첩되지는 않는다.** 다만 PG 는 말해 주고 MySQL 은 조용히 커밋한다.

---

### 11. ★ PG 는 전부 되돌아가고, MySQL 은 전부 남는다

**출력**

```text
--- PG 18.6 ---
BEGIN;
BEGIN
UPDATE t55_acct SET bal = 555 WHERE id = 1;
UPDATE 1
CREATE TABLE t55_tmp (x int);
CREATE TABLE
UPDATE t55_acct SET bal = 666 WHERE id = 2;
UPDATE 1
ROLLBACK;
ROLLBACK
SELECT id, bal FROM t55_acct ORDER BY id;
 id | bal
----+------
  1 |  900
  2 | 1000
(2 rows)

SELECT to_regclass('t55_tmp') AS t55_tmp_exists;
 t55_tmp_exists
----------------

(1 row)
```

```text
--- MySQL 8.4.10 ---
START TRANSACTION
UPDATE t55_acct SET bal = 555 WHERE id = 1
CREATE TABLE t55_tmp (x int)
UPDATE t55_acct SET bal = 666 WHERE id = 2
ROLLBACK
SELECT id, bal FROM t55_acct ORDER BY id
+----+------+
| id | bal  |
+----+------+
|  1 |  555 |
|  2 |  666 |
+----+------+
SHOW TABLES LIKE 't55%'
+------------------------+
| Tables_in_study (t55%) |
+------------------------+
| t55_acct               |
| t55_tmp                |
+------------------------+
```

**왜 그런가** — PG 는 **DDL 도 트랜잭션 안에 들어간다.** `ROLLBACK` 이 `UPDATE` 도 `CREATE TABLE` 도 지웠다\
(`to_regclass` 가 빈 값 = 그런 표가 없다).\
MySQL 은 **DDL 이 암묵 커밋**이다. `CREATE TABLE` 이 앞의 `UPDATE`(555)를 확정해 버렸고, 표도 남았다.

---

### 12. 암묵 커밋이 트랜잭션을 **끝내기까지** 했기 때문이다

**왜 그런가** — MySQL 의 암묵 커밋은 「앞의 것을 커밋한다」로 끝나지 않는다. **트랜잭션 자체가 닫힌다.**\
그래서 `CREATE TABLE` **뒤의** `UPDATE … 666` 은 **트랜잭션 밖에서**, 즉 자동 커밋으로 혼자 돌았다.\
그 문이 끝나는 순간 확정됐고, 그 뒤의 `ROLLBACK` 은 되돌릴 것이 없는 상태에서 돌았다 — **에러도 경고도 없이.**

★ 그래서 결과가 `555 / 666` 이다. **두 값이 서로 다른 이유로 살아남았다.**

---

### 13. PG 만 받는다

**출력**

```text
### SQL: BEGIN ISOLATION LEVEL REPEATABLE READ;
--- PG 18.6 ---
BEGIN ISOLATION LEVEL REPEATABLE READ;
BEGIN
SHOW transaction_isolation;
 transaction_isolation
-----------------------
 repeatable read
(1 row)
```

```text
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 9: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'ISOLATION LEVEL REPEATABLE READ' at line 1
```

**왜 그런가** — PG 는 `BEGIN`/`START TRANSACTION` 에 트랜잭션 모드를 붙일 수 있다.\
MySQL 은 **따로 `SET TRANSACTION ISOLATION LEVEL …` 을 먼저 쳐야 한다**([56번](../56-isolation-levels-read-phenomena-mvcc/)).

---

### 14. 된다 — 괄호가 항상 열려 있는 모드다

**출력**

```text
--- MySQL 8.4.10 ---
SET autocommit = 0
SELECT @@autocommit AS ac_now
+--------+
| ac_now |
+--------+
|      0 |
+--------+
UPDATE t55_acct SET bal = 1234 WHERE id = 1
ROLLBACK
SELECT id,bal FROM t55_acct ORDER BY id
+----+------+
| id | bal  |
+----+------+
|  1 | 1000 |
|  2 | 1000 |
+----+------+
```

**왜 그런가** — `autocommit = 0` 이면 **문을 던지는 순간 트랜잭션이 자동으로 열린다.**\
그래서 `BEGIN` 없이 던진 `UPDATE` 도 `ROLLBACK` 으로 지워진다(1234 가 아니라 1000 이다).\
대가는 **깜빡 잊은 열린 트랜잭션**이다 — 커넥션 풀에서 이 설정이 켜진 채 반납되면 잠금이 오래 남는다([57번](../57-explicit-locking-and-deadlock/)).

---

### 15. `SAVEPOINT` 하나뿐이다

**왜 그런가** — 두 엔진 다 **트랜잭션은 중첩되지 않는다.**

- PG — 두 번째 `BEGIN` 은 `WARNING: there is already a transaction in progress` 를 내고 **무시된다.**
- MySQL — 두 번째 `START TRANSACTION` 은 **앞의 것을 커밋한다.**

「내부 트랜잭션」이 필요하면 `SAVEPOINT` 로 구간을 감싸고, 실패 시 `ROLLBACK TO` 한다.\
ORM 의 「중첩 트랜잭션」도 대개 내부적으로 세이브포인트를 찍는다 *(문서 근거 없음 — 이 편에서 확인하지 않았다)*.

---

### 16. MySQL 의 DDL, 그리고 두 번째 `START TRANSACTION`

둘 다 이 편에서 실측한 것이다.

| 경우 | 무슨 일이 일어났나 | 근거 |
|---|---|---|
| 트랜잭션 안의 `CREATE TABLE` | 앞의 변경이 커밋되고 트랜잭션이 닫힌다. 뒤의 문은 자동 커밋으로 돈다 | 11·12번 (`555 / 666` 이 남았다) |
| 두 번째 `START TRANSACTION` | 앞의 변경이 커밋된다. **경고도 없다** | 10번 (`777` 이 남았다) |

★ **`ROLLBACK` 의 성공 응답은 「지울 것이 있었다」를 뜻하지 않는다.**\
되돌아갔는지는 **표를 다시 읽어서** 확인한다 — 이 편의 두 사고 모두 표를 읽어야만 보인다.\
([`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 「실패가 조용하다」가 여기서도 그대로다.)

---

### 17. 문 하나로 끝나는 일, 그리고 외부 호출이 끼는 구간

- **문 하나로 끝나면 감싸지 않는다.** 자동 커밋이 이미 원자적이고, 괄호는 커밋 비용만 한 번 더 낸다.
- **조건 확인과 변경이 한 문으로 되면 감싸지 않는다.** `UPDATE … WHERE qty >= 1` 같은 조건부 갱신이\
  트랜잭션보다 먼저 검토할 수단이다([`concurrency.md`](../../../../../engineering/engineering-axes/concurrency.md) 의 「선택 순서」 2단계).
- **괄호 안에 외부 API 호출을 넣지 않는다.** 네트워크 지연만큼 잠금 유지 시간이 늘어난다.
- **사람의 입력을 기다리는 구간을 괄호에 넣지 않는다.** 긴 트랜잭션은 옛 행 버전을 못 버리게 만든다([56번](../56-isolation-levels-read-phenomena-mvcc/)).
- 반대로 **감싸야 하는 것** — 두 문 이상이 하나의 사실을 이룰 때(출금+입금, 주문+재고, 본문+첨부).

---

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 환경 확인(격리 수준·자동 커밋·잠금 타임아웃) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **제출 직전 재확인** |
| ★ 자동 커밋 가시성 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 세션** |
| ★ 트랜잭션 안 에러 (3·4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | MySQL 은 `--force` 로 에러 뒤를 계속 던졌다 |
| `SAVEPOINT`·`ROLLBACK TO`·`RELEASE` (5·6·7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 같은 스크립트 |
| ★ `RELEASE` 뒤 `ROLLBACK TO` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | PG 는 **표 값까지 확인** |
| 트랜잭션 밖 `SAVEPOINT` (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 두 엔진이 다른 줄에서 터진다 |
| ★ 중첩 `BEGIN` (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `SHOW WARNINGS` 까지 물었다 |
| ★ DDL 암묵 커밋 (11·12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `t55_tmp` 존재 여부까지 |
| `BEGIN ISOLATION LEVEL` (13번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | MySQL 은 `ERROR 1064` |
| `SET autocommit = 0` (14번) | MySQL 8.4.10 | 1회 | 끝나고 1 로 되돌렸다 |
| `COMMIT AND CHAIN` | PG 18.6 · MySQL 8.4.10 | 각 1회 | 양쪽 다 통과 |
| 뒷정리 확인 | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\dt` · `SHOW FULL TABLES` · **`emp` 4행 · `dept` 3행 재확인** |

**두 세션을 어떻게 띄웠나** — 이름 붙인 FIFO 두 개를 만들고 각 접속의 표준입력에 물린 뒤, 한 줄씩 순서대로 먹였다.\
`W <초>` 는 그 자리에서 기다리는 표시다 — **이 주제는 순서가 곧 내용**이므로 대기를 명시적으로 넣었다.

```bash
mkfifo "$D/a.in" "$D/b.in"
docker exec -i study-pg18 psql -U postgres -d study -a -P pager=off < "$D/a.in" > "$D/a.out" 2>&1 &
docker exec -i study-pg18 psql -U postgres -d study -a -P pager=off < "$D/b.in" > "$D/b.out" 2>&1 &
exec 3>"$D/a.in" 4>"$D/b.in"
# 스크립트 줄: "A <sql>" -> fd 3, "B <sql>" -> fd 4, "W 0.5" -> sleep 0.5
```

★ **대기 실험에는 먼저 타임아웃을 걸었다.** 두 접속 모두 첫 줄이 이것이다.

```sql
-- PG
SET lock_timeout = '3s'; SET statement_timeout = '10s';
-- MySQL
SET SESSION innodb_lock_wait_timeout = 3; SET SESSION max_execution_time = 10000;
```

**뒷정리** — 이 편은 트랜잭션 자체가 실험 대상이라 `ROLLBACK` 에 기댈 수 없는 자리가 많았다.\
그래서 **두 엔진 모두 `DROP TABLE` 로 직접 지웠다.**

```sql
DROP TABLE IF EXISTS t55_tmp;
DROP TABLE IF EXISTS t55_acct;
```

**구현 의존 항목** — 3·8·9·10·11·12번. **에러 뒤에 트랜잭션이 사는가**와 **DDL 이 괄호에 들어가는가**는\
표준 문법이 아니라 **엔진의 선택**이다. 에러 번호(`1062`·`1305`·`1064`)도 MySQL 구현 세부다.\
재현되는 것은 번호가 아니라 「**PG 는 중단, MySQL 은 계속**」이라는 성질이다.

**언어 보장 항목** — 5·6·7번. `SAVEPOINT`·`ROLLBACK TO`·`RELEASE` 의 의미는 **두 엔진에서 한 자리도 안 갈렸다.**\
1·2번의 「기본은 자동 커밋」도 두 엔진이 같다 — 다른 것은 스위치의 위치뿐이다.

**한쪽에서만 결론이 서는 실험** — 14번(`SET autocommit = 0`)은 **MySQL 에서만** 성립한다.\
PG 에는 그런 서버 설정이 없으므로 「PG 에서는 안 된다」가 아니라 「**PG 에서는 다른 층의 이야기다**」로 읽는다.

**버전** — 이 편의 동작은 PG 18 · MySQL 8.4 에서 확인한 것이다.\
MySQL 의 암묵 커밋 목록은 버전마다 항목이 늘 수 있으므로, 버전이 오르면 **11·12번**을 다시 돌린다.
