# sql/50-UPDATE — 조인·서브쿼리를 쓰는 갱신 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **환경** — MySQL 의 `sql_safe_updates` 기본값은 **`0`**(꺼짐)이고, `sql_mode` 에 `STRICT_TRANS_TABLES` 가 켜져 있다.\
> 이 편이 만든 표(`t50_emp`·`t50_dept`·`t50_map`·`t50_u`)는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> ★ **`WHERE` 없는 `UPDATE` 실험은 전부 `t50_emp` 에서만 했다.**\
> 문서 근거는 [PG 18 UPDATE](https://www.postgresql.org/docs/18/sql-update.html) · [MySQL 8.4 UPDATE](https://dev.mysql.com/doc/refman/8.4/en/update.html) · [MySQL 8.4 mysql Client Options](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. ★ 서로의 문법 — **둘 다 구문 오류다**

**출력**

```text
### SQL: UPDATE t50_emp e SET dept_name = d.name FROM t50_dept d WHERE d.id = e.dept_id;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'FROM t50_dept d WHERE d.id = e.dept_id' at line 1

### SQL: UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.dept_name = d.name;
--- PG 18.6 ---
ERROR:  syntax error at or near "JOIN"
LINE 1: UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.d...
                         ^
```

각자 자기 엔진에서는 잘 돈다.

```text
### SQL: UPDATE t50_emp e SET dept_name = d.name FROM t50_dept d WHERE d.id = e.dept_id;
--- PG 18.6 ---
UPDATE 3

### SQL: UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.dept_name = d.name;
--- MySQL 8.4.10 ---
affected = 3
```

**왜 그런가** — 두 엔진이 **절의 자리를 다르게 정했다.**

```text
PG    : UPDATE 대상  SET ...  FROM 상대  WHERE 조인조건
                              ^^^^ SET 뒤
MySQL : UPDATE 대상 JOIN 상대 ON 조인조건  SET ...
                    ^^^^ SET 앞
```

★ **둘 다 시끄럽게 거부한다는 점은 안전하다.** [13 번의 `JOIN … ON` 누락](../13-inner-join/)처럼\
한쪽이 조용히 통과하는 자리가 아니다 — 이식할 때 **반드시 눈에 띈다.**

---

### 2. 조인형이 건드리는 행 — **`(old)` 그대로 남는다**

**출력**

```text
BEGIN;
UPDATE t50_emp SET dept_name='(old)';
UPDATE 4
UPDATE t50_emp e SET dept_name = d.name FROM t50_dept d WHERE d.id = e.dept_id;
UPDATE 3
SELECT * FROM t50_emp ORDER BY id;
 id | name | dept_id | salary | dept_name 
----+------+---------+--------+-----------
  1 | ann  |      10 |    300 | sales
  2 | bob  |      10 |    500 | sales
  3 | cho  |      20 |        | dev
  4 | dan  |         |    400 | (old)
(4 rows)
ROLLBACK;
```

MySQL 도 같다.

```text
START TRANSACTION;
UPDATE t50_emp SET dept_name='(old)';
UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.dept_name = d.name;
SELECT * FROM t50_emp ORDER BY id;
+----+------+---------+--------+-----------+
| id | name | dept_id | salary | dept_name |
+----+------+---------+--------+-----------+
|  1 | ann  |      10 |    300 | sales     |
|  2 | bob  |      10 |    500 | sales     |
|  3 | cho  |      20 |   NULL | dev       |
|  4 | dan  |    NULL |    400 | (old)     |
+----+------+---------+--------+-----------+
ROLLBACK;
```

**왜 그런가** — **조인이 안 붙은 행은 갱신 대상 집합에 아예 안 들어간다.**\
`UPDATE 3` 의 `3` 이 그 증거다 — 네 행 중 셋만 대상이었다.

[13 INNER JOIN](../13-inner-join/)에서 짝 없는 행이 결과에서 사라지는 것과 **같은 규칙**이 대상 집합에 적용된 것이다.

---

### 3. ★★ 서브쿼리로 쓰면 — **`(old)` 가 `NULL` 로 지워진다**

**출력**

```text
BEGIN;
UPDATE t50_emp SET dept_name='(old)';
UPDATE 4
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id);
UPDATE 4
SELECT * FROM t50_emp ORDER BY id;
 id | name | dept_id | salary | dept_name 
----+------+---------+--------+-----------
  1 | ann  |      10 |    300 | sales
  2 | bob  |      10 |    500 | sales
  3 | cho  |      20 |        | dev
  4 | dan  |         |    400 | 
(4 rows)
ROLLBACK;
```

MySQL 도 **데이터는 똑같이 된다.**

```text
START TRANSACTION;
UPDATE t50_emp SET dept_name='(old)';
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id);
SELECT * FROM t50_emp ORDER BY id;
+----+------+---------+--------+-----------+
| id | name | dept_id | salary | dept_name |
+----+------+---------+--------+-----------+
|  1 | ann  |      10 |    300 | sales     |
|  2 | bob  |      10 |    500 | sales     |
|  3 | cho  |      20 |   NULL | dev       |
|  4 | dan  |    NULL |    400 | NULL      |
+----+------+---------+--------+-----------+
ROLLBACK;
```

**왜 그런가** — **대상 집합의 정의가 다르다.**

```text
조인형      대상 = 조인이 붙은 행               (3행)  -> dan 은 아예 안 본다
서브쿼리형   대상 = WHERE 가 고른 행 = 전부      (4행)  -> dan 도 갱신한다
                                                        새 값이 NULL 일 뿐
```

그 「새 값이 `NULL`」은 [11 번의 규칙](../11-subquery-scalar-correlated-any-all/)이다.

```text
스칼라 서브쿼리가 0행을 돌려주면 에러가 아니라 NULL 이다

  dept_id = 10   -> 'sales' 1행  -> 'sales' 를 쓴다
  dept_id = NULL -> 0행          -> ★ NULL 을 쓴다 (건너뛰는 게 아니다)
```

★ **에러도 경고도 없다.** 운영 표에서 이 문을 돌리면 **짝 없는 행의 기존 값이 조용히 사라진다.**\
`UPDATE 4` 라는 숫자가 유일한 신호인데, 그것도 「4행을 고쳤다」로 읽으면 이상할 게 없다.

---

### 4. 그 차이를 없애려면 — **`WHERE EXISTS` 로 대상을 좁힌다**

**출력**

```text
BEGIN;
UPDATE t50_emp SET dept_name='(old)';
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id)
  WHERE EXISTS (SELECT 1 FROM t50_dept d WHERE d.id = e.dept_id);
UPDATE 3
SELECT * FROM t50_emp ORDER BY id;
 id | name | dept_id | salary | dept_name 
----+------+---------+--------+-----------
  1 | ann  |      10 |    300 | sales
  2 | bob  |      10 |    500 | sales
  3 | cho  |      20 |        | dev
  4 | dan  |         |    400 | (old)
(4 rows)
ROLLBACK;
```

**왜 그런가** — `UPDATE` 에는 **「무엇으로 바꾸나」(`SET`)와 「어느 행을 바꾸나」(`WHERE`)가 따로** 있다.\
조인형은 그 둘을 한 번에 정하고, 서브쿼리형은 **`SET` 만 정하고 `WHERE` 를 비워 둔다.**

```text
조인형       : SET 과 대상이 같은 조인에서 나온다        -> 한 번만 적으면 된다
서브쿼리형    : SET 은 서브쿼리, 대상은 WHERE            -> ★ 같은 조건을 두 번 적어야 한다
```

**그 중복이 이 형태의 대가**이고, 대신 **두 엔진에서 한 글자도 안 바꾸고 돈다.**\
`EXISTS` 자체는 [19 SEMI·ANTI 조인](../19-semi-anti-join/)이 정본이다.

---

### 5. 영향 행 수 — **PG 는 4, MySQL 은 3**

**출력**

```text
### SQL: (dept_name 이 전부 NULL 인 상태에서) UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id);
--- PG 18.6 ---
UPDATE 4
--- MySQL 8.4.10 ---
+----------+
| affected |
+----------+
|        3 |
+----------+
```

**왜 그런가** — 표의 최종 모습은 **두 엔진이 똑같다.** 세는 기준만 다르다.

```text
id=4 (dan) : NULL -> NULL 로 갱신됐다

PG      : "대상이 된 행 수" 를 센다       -> 4
MySQL   : "값이 실제로 바뀐 행 수" 를 센다 -> 3  (dan 은 안 바뀌었다고 본다)
```

★ 같은 성질을 [52 번의 upsert 영향 행 수](../52-upsert/)가 「무변화 = 0」으로 보여 준다.\
**「영향 행 수가 0이면 실패」로 짠 코드는 두 엔진에서 다르게 동작한다.**

---

### 6. 짝이 둘이면 — **조인형은 조용히 하나, 서브쿼리형은 에러**

**출력**

```text
### SQL: UPDATE t50_emp e SET dept_name = m.label FROM t50_map m WHERE m.dept_id = e.dept_id;   (조인형)
--- PG 18.6 ---
UPDATE 2
 id | name | dept_name 
----+------+-----------
  1 | ann  | AAA
  2 | bob  | AAA
  3 | cho  | 
  4 | dan  | 
(4 rows)

--- MySQL 8.4.10 ---  (UPDATE t50_emp e JOIN t50_map m ON m.dept_id=e.dept_id SET e.dept_name=m.label)
+----------+
| affected |
+----------+
|        2 |
+----------+
+----+------+-----------+
| id | name | dept_name |
+----+------+-----------+
|  1 | ann  | AAA       |
|  2 | bob  | AAA       |
|  3 | cho  | NULL      |
|  4 | dan  | NULL      |
+----+------+-----------+
```

```text
### SQL: UPDATE t50_emp e SET dept_name = (SELECT m.label FROM t50_map m WHERE m.dept_id = e.dept_id);   (서브쿼리형)
--- PG 18.6 ---
ERROR:  more than one row returned by a subquery used as an expression
--- MySQL 8.4.10 ---
ERROR 1242 (21000) at line 1: Subquery returns more than 1 row
```

**왜 그런가** — **위험의 방향이 3번과 반대다.**

```text
짝이 0개 : 조인형 = 안 건드림 (안전)   / 서브쿼리형 = NULL 덮어쓰기 (위험)
짝이 2개 : 조인형 = 조용히 하나 (위험) / 서브쿼리형 = 에러 (안전)
```

PG 문서가 조인형의 이 성질을 명시한다.

> "When using `FROM` you should ensure that the join produces at most one output row for each row to be modified. … If it does, then only one of the join rows will be used to update the target row, but **which one will be used is not readily predictable**."\
> — [PostgreSQL 18 · UPDATE](https://www.postgresql.org/docs/18/sql-update.html)

★ **이 실험에서 PG 는 세 판 모두 `AAA` 를 골랐다.**

```text
판 1:  1 | AAA   ·  2 | AAA
판 2:  1 | AAA   ·  2 | AAA
판 3:  1 | AAA   ·  2 | AAA
```

**그러나 이것은 관찰이지 보장이 아니다.** 문서가 「예측 가능하지 않다」고 적었으므로\
**`AAA` 를 기대하는 코드를 쓰면 안 된다.** 반복 실행이 같았다는 사실은 오히려 **더 위험한 근거**다\
([작성법 §2-1](../../../../../../reference/study-note-guide.md)의 「같은 값이 나와 보장된다고 오해한다」).

**처방** — 원본을 믿을 수 없으면 **원본을 먼저 접어서**(`GROUP BY`·`DISTINCT ON`) 1:1 로 만든 뒤 조인한다.

---

### 7. ★★ `SET` 목록 안의 상호 참조 — **PG 는 `(300, 10)`, MySQL 은 `(300, 300)`**

**출력**

```text
### SQL: BEGIN; UPDATE t50_emp SET dept_id = salary, salary = dept_id WHERE id = 1; SELECT id, dept_id, salary FROM t50_emp WHERE id=1; ROLLBACK;
--- PG 18.6 ---
 id | dept_id | salary 
----+---------+--------
  1 |     300 |     10
(1 row)

--- MySQL 8.4.10 ---
+----+---------+--------+
| id | dept_id | salary |
+----+---------+--------+
|  1 |     300 |    300 |
+----+---------+--------+
```

**왜 그런가**

```text
출발:  dept_id = 10 · salary = 300

PG      오른쪽 식을 전부 "갱신 전 행" 에 대고 평가한다
        (dept_id, salary) := (salary_old, dept_id_old) = (300, 10)   ★ 교환됐다

MySQL   왼쪽부터 차례로 대입한다
        dept_id := salary        -> dept_id 가 300 이 된다
        salary  := dept_id       -> ★ 이미 300 이 된 값을 읽는다 -> 300
        결과 (300, 300) — 원래의 10 이 사라졌다
```

매뉴얼이 MySQL 쪽을 명시한다.

> "Single-table `UPDATE` assignments are generally evaluated from left to right. For multiple-table updates, there is no guarantee that assignments are carried out in any particular order."\
> — [MySQL 8.4 · UPDATE Statement](https://dev.mysql.com/doc/refman/8.4/en/update.html)

★ **에러도 경고도 없다.** 이식했을 때 **데이터만 조용히 달라진다** — 이 편에서 가장 조용한 사고다.\
그리고 **다중 표 갱신에서는 MySQL 자신도 순서를 보장하지 않는다** — 그쪽에서는 이 관용구를 쓰면 안 된다.

---

### 8. `WHERE` 를 빠뜨리면 — **전부 바뀐다. 아무것도 안 막는다**

**출력**

```text
### SQL: UPDATE t50_emp SET salary = 0;
--- PG 18.6 ---                            --- MySQL 8.4.10 ---
UPDATE 4                                   affected = 4
 id | name | dept_id | salary              +----+------+---------+--------+
----+------+---------+--------              | id | name | dept_id | salary |
  1 | ann  |      10 |      0              +----+------+---------+--------+
  2 | bob  |      10 |      0              |  1 | ann  |      10 |      0 |
  3 | cho  |      20 |      0              |  2 | bob  |      10 |      0 |
  4 | dan  |         |      0              |  3 | cho  |      20 |      0 |
(4 rows)                                   |  4 | dan  |    NULL |      0 |
                                           +----+------+---------+--------+
```

**왜 그런가** — **`WHERE` 가 없으면 조건이 없는 것이 아니라 「전부 참」이다.**\
확인도 경고도 없고, `salary` 가 `NULL` 이던 `cho` 까지 `0` 이 됐다.

★ **기본 상태에서 막아 주는 것은 두 엔진 어디에도 없다.**\
MySQL 에는 켤 수 있는 장치가 하나 있고(9번), **기본값은 꺼짐**이다.

**처방은 문법이 아니라 습관이다.**

```sql
SELECT count(*) FROM t50_emp WHERE <조건>;   -- ① 먼저 이 숫자를 본다
UPDATE t50_emp SET ... WHERE <조건>;         -- ② 같은 조건을 그대로 옮긴다
```

PG 라면 [`RETURNING`](../54-returning-and-data-modifying-cte/)으로 **바뀐 행을 보면서** 트랜잭션 안에서 돌릴 수 있다.

---

### 9. ★ 안전 모드가 막는 것 — **(c) 와 (d) 만 통과한다. 기준은 행 수가 아니다**

**출력**

```text
### SQL: SET sql_safe_updates = 1; UPDATE t50_emp SET salary = 0;                             -- (a)
--- MySQL 8.4.10 ---
ERROR 1175 (HY000) at line 1: You are using safe update mode and you tried to update a table
  without a WHERE that uses a KEY column.

### SQL: SET sql_safe_updates = 1; UPDATE t50_emp SET salary = 0 WHERE name = 'ann';          -- (b)
--- MySQL 8.4.10 ---
ERROR 1175 (HY000) at line 1: You are using safe update mode and you tried to update a table
  without a WHERE that uses a KEY column.

### SQL: SET sql_safe_updates = 1; ... UPDATE t50_emp SET salary = 0 WHERE id = 1; SELECT ROW_COUNT() AS affected;   -- (c)
--- MySQL 8.4.10 ---
+----------+
| affected |
+----------+
|        1 |
+----------+

### SQL: SET sql_safe_updates = 1; UPDATE t50_emp SET salary = 0 WHERE salary > 0;
--- MySQL 8.4.10 ---
ERROR 1175 (HY000) at line 1: You are using safe update mode and you tried to update a table
  without a WHERE that uses a KEY column.

### SQL: SET sql_safe_updates = 1; ... UPDATE t50_emp SET salary = 0 WHERE salary > 0 LIMIT 10; SELECT ROW_COUNT() AS affected;   -- (d)
--- MySQL 8.4.10 ---
+----------+
| affected |
+----------+
|        3 |
+----------+
```

**왜 그런가 — 기준은 「몇 행을 바꾸나」가 아니다.**

```text
(a) WHERE 없음                     -> 막힌다
(b) WHERE name='ann' (인덱스 없음) -> ★ 1행만 바꾸는데도 막힌다
(c) WHERE id=1       (기본키)      -> 통과. 1행
(d) WHERE salary>0 LIMIT 10        -> ★ 통과. 3행을 바꿨다
```

매뉴얼이 규칙을 그대로 적는다.

> "If this option is enabled, `UPDATE` and `DELETE` statements that do not use a key in the `WHERE` clause or a `LIMIT` clause produce an error."\
> — [MySQL 8.4 · mysql Client Options](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html)

**보는 것은 「키를 썼나 · `LIMIT` 이 있나」 두 가지뿐**이다.\
★ 그래서 **`LIMIT` 을 습관적으로 붙이는 사람에게는 아무것도 안 막아 준다.**\
그리고 [51 번에서 보겠지만 **`TRUNCATE` 는 이 장치가 아예 못 본다.**](../51-delete-and-truncate/)

---

### 10. PG 에 같은 변수가 있나 — **없다**

**출력**

```text
### SQL: SET sql_safe_updates = 1;
--- PG 18.6 ---
ERROR:  unrecognized configuration parameter "sql_safe_updates"
```

**왜 그런가** — MySQL 클라이언트·세션 전용 장치다. PG 에는 같은 이름의 설정이 없다.

PG 쪽에서 같은 목적을 이루는 방법은 **문법이 아니라 절차**다.

```text
① BEGIN; 으로 열고
② UPDATE ... RETURNING * 로 바뀐 행을 눈으로 확인하고         (54번)
③ 맞으면 COMMIT, 아니면 ROLLBACK
```

`psql` 에는 `ON_ERROR_ROLLBACK` 같은 클라이언트 설정이 있지만 **이 편에서는 던져 보지 않았다.**

---

### 11. `UPDATE` 가 제약을 어기면 — **하나도 안 바뀐다. 두 엔진이 같다**

**출력**

```text
### SQL: UPDATE t50_u SET id = 99 WHERE v >= 20;
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t50_u_pkey"
DETAIL:  Key (id)=(99) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry '99' for key 't50_u.PRIMARY'

### SQL: SELECT * FROM t50_u ORDER BY id;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 id | v                    +----+------+
----+----                  | id | v    |
  1 | 10                   +----+------+
  2 | 20                   |  1 |   10 |
  3 | 30                   |  2 |   20 |
(3 rows)                   |  3 |   30 |
                           +----+------+
```

**왜 그런가** — **문 하나가 원자 단위**다. [49 번 2절](../49-insert-multi-row-and-insert-select/)과 같은 성질이 `UPDATE` 에서도 성립한다.

```text
[id=2 -> 99 시도] [id=3 -> 99 시도 -> PK 충돌] -> 문 전체 취소
      ↓                     ↓
   되돌린다  <───────────────┘
```

★ **에러가 났다는 것만으로 끝내지 않고 표를 다시 읽어 확인했다** — 세 행 다 원래대로였다.

---

### 12. `UPDATE IGNORE` 를 붙이면 — **반만 갱신된다**

**출력**

```text
### SQL: UPDATE IGNORE t50_u SET id = 99 WHERE v >= 20; SHOW WARNINGS;
--- MySQL 8.4.10 ---
+---------+------+----------------------------------------------+
| Level   | Code | Message                                      |
+---------+------+----------------------------------------------+
| Warning | 1062 | Duplicate entry '99' for key 't50_u.PRIMARY' |
+---------+------+----------------------------------------------+

### SQL: SELECT * FROM t50_u ORDER BY id;
--- MySQL 8.4.10 ---
+----+------+
| id | v    |
+----+------+
|  1 |   10 |
|  3 |   30 |     <- 이 행은 안 바뀌었다
| 99 |   20 |     <- 이 행은 바뀌었다 (원래 id=2)
+----+------+
```

**왜 그런가** — **에러가 경고로 내려앉으면 문이 안 죽고, 문이 안 죽으면 나머지가 계속 처리된다.**\
[49 번 7절의 `INSERT IGNORE`](../49-insert-multi-row-and-insert-select/)와 **완전히 같은 구조**다.

```text
11번 (IGNORE 없음)                     12번 (IGNORE 있음)
+----------------------------+         +----------------------------+
| ERROR 1062                 |         | 에러 없음. 경고 1062       |
| 표: 원래대로 (1,2,3)       |         | 표: (1, 3, 99) — 반만 반영  |
+----------------------------+         +----------------------------+
  -> 재시도하면 된다                       -> ★ 재시도하면 무엇이 되나?
```

★ **`UPDATE IGNORE` 를 쓴 문은 「성공」을 돌려주고도 절반만 반영돼 있을 수 있다.**\
`SHOW WARNINGS` 를 안 읽으면 그 사실이 어디에도 안 남는다.

---

### 13. `ORDER BY`·`LIMIT` — **(a) MySQL 만 / (b) MySQL 도 거부**

**출력**

```text
### SQL: UPDATE t50_emp SET salary = 0 ORDER BY id LIMIT 1;
--- PG 18.6 ---
ERROR:  syntax error at or near "ORDER"
LINE 1: UPDATE t50_emp SET salary = 0 ORDER BY id LIMIT 1
                                      ^
--- MySQL 8.4.10 ---
(성공)

### SQL: SELECT id,salary FROM t50_emp ORDER BY id;
--- MySQL 8.4.10 ---
+----+--------+
| id | salary |
+----+--------+
|  1 |      0 |
|  2 |    500 |
|  3 |   NULL |
|  4 |    400 |
+----+--------+
```

```text
### SQL: UPDATE t50_emp e JOIN t50_dept d ON d.id=e.dept_id SET e.salary = 0 ORDER BY e.id LIMIT 1;
--- MySQL 8.4.10 ---
ERROR 1221 (HY000) at line 1: Incorrect usage of UPDATE and ORDER BY
```

**왜 그런가** — 매뉴얼이 범위를 명시한다.

> "If the `ORDER BY` clause is specified, the rows are updated in the order that is specified. The `LIMIT` clause places a limit on the number of rows that can be updated. … **For multiple-table syntax, `ORDER BY` and `LIMIT` cannot be used.**"\
> — [MySQL 8.4 · UPDATE Statement](https://dev.mysql.com/doc/refman/8.4/en/update.html)

```text
PG    : UPDATE 에 ORDER BY / LIMIT 이 아예 없다
MySQL : 단일 표에만 있다. 다중 표에서는 ERROR 1221
```

★ **PG 에서 같은 일을 하려면 대상을 서브쿼리로 고른다.**

```sql
UPDATE t50_emp SET salary = 0
 WHERE id IN (SELECT id FROM t50_emp ORDER BY id LIMIT 1);
```

같은 관용구를 [51 번의 나눠 지우기](../51-delete-and-truncate/)에서 다시 쓴다.

---

### 14. 두 열을 안전하게 교환하려면 — **PG 는 다중 열 대입, 이식하려면 임시 열/값**

**출력**

```text
### SQL: UPDATE t50_emp SET (dept_id, salary) = (salary, dept_id) WHERE id = 1;
--- PG 18.6 ---
UPDATE 1
 id | dept_id | salary 
----+---------+--------
  1 |     300 |     10          <- 교환됐다. 의도가 문장에 드러난다
(1 row)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  '(dept_id, salary) = (salary, dept_id) WHERE id = 1' at line 1
```

**왜 그런가** — PG 의 `SET (a, b) = (식1, 식2)` 는 **오른쪽을 하나의 행 값으로 평가**한 뒤 대입한다.\
7번의 `SET a = b, b = a` 와 결과는 같지만 **「동시 대입」이라는 의도가 문장에 남는다.**

**MySQL 에는 이 문법이 없으므로** 이식 가능한 방법은 하나 더 돌아간다.

```sql
-- 어느 엔진에서나 도는 형태: 값을 미리 바깥에서 계산해 넣는다
UPDATE t50_emp SET dept_id = 300, salary = 10 WHERE id = 1;

-- 또는 세 번째 열/변수를 경유한다 (MySQL)
UPDATE t50_emp SET dept_id = @t := dept_id, dept_id = salary, salary = @t WHERE id = 1;
```

★ **두 번째 형태는 이 편에서 던져 보지 않았다** — 사용자 변수의 평가 시점이 별도 주제라\
**돌려 본 것만 「이렇게 된다」로 적는다**는 규칙에 따라 **문법 예시로만** 남긴다.\
**확실한 처방은 하나다 — `SET a = b, b = a` 관용구를 아예 쓰지 않는다.**

---

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `sql_safe_updates`·`sql_mode` 조회 (머리말) | MySQL 8.4.10 | 2회 | **기본값이 `0` 인 것이 9번의 전제다** |
| 표 4개 생성·삭제 | PG 18.6 · MySQL 8.4.10 | 각 4회 | `t50_emp`·`t50_dept`·`t50_map`·`t50_u` |
| ★ 서로의 문법 교차 투척 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **둘 다 구문 오류 — 에러가 근거다** |
| 자기 엔진 조인형 갱신 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 갱신 + `SELECT` 확인 |
| ★ `'(old)'` 선세팅 후 조인형 (2번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **dan 이 `(old)` 로 살아남았다** |
| ★★ 같은 상태에서 서브쿼리형 (3번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **dan 이 `NULL` 이 됐다 — 두 엔진 동일** |
| `WHERE EXISTS` 처방 (4번) | PG 18.6 | 3회 | **`UPDATE 3` 으로 돌아왔다** |
| 영향 행 수 비교 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 4 / MySQL 3 — 표 상태는 같다** |
| 짝이 둘일 때 조인형 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **둘 다 `AAA` 를 골랐다** |
| ★ 같은 문 반복 (6번) | PG 18.6 | **3회** | **세 판 다 `AAA` — 그러나 문서는 「예측 불가」라고 적는다** |
| 짝이 둘일 때 서브쿼리형 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **둘 다 에러 — 이쪽이 안전하다** |
| ★★ `SET a=b, b=a` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`(300,10)` 대 `(300,300)`** |
| `WHERE` 없는 `UPDATE` (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **4행 전부. `t50_emp` 에서만 던졌다** |
| ★ `sql_safe_updates` 네 형태 (9번) | MySQL 8.4.10 | 5회 | **(b) 가 막히고 (d) 가 통과하는 것이 핵심이다** |
| PG 에 `sql_safe_updates` (10번) | PG 18.6 | 1회 | `unrecognized configuration parameter` |
| `UPDATE` 원자성 (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 + 표 재확인 — 셋 다 원래대로** |
| ★ `UPDATE IGNORE` (12번) | MySQL 8.4.10 | 2회 | **경고 1062 + 반만 반영된 표** |
| `ORDER BY`/`LIMIT` (13번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 구문 오류 / MySQL 다중 표는 `ERROR 1221`** |
| 다중 열 대입 (14번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 교환 성공 / MySQL `ERROR 1064`** |
| `SET c = DEFAULT` (문법 절) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **양쪽 다 통과 — `NULL` 로 돌아갔다** |

**구현 의존 항목** — 1·13·14번의 **문법 수용 여부**, 5번의 **영향 행 수 정의**, 9번의 **`sql_safe_updates`**,\
11·12번의 **에러 코드**.\
외울 것은 문구가 아니라 「**짝 없는 행을 조인형은 안 건드리고 서브쿼리형은 `NULL` 로 덮는다**」는 성질이다.

**언어 보장 항목** — 2·3·4·11번.\
조인이 대상 집합을 정한다는 것, 0행 스칼라 서브쿼리가 `NULL` 이라는 것([11번](../11-subquery-scalar-correlated-any-all/)),\
실패한 문의 변경이 취소된다는 것은 두 매뉴얼이 정한 것이다.

★ **문서가 보장을 서로 다르게 적은 자리** — 7번.\
**MySQL 문서는 「왼쪽에서 오른쪽」을 보장**하고, **PG 문서는 다중 열 대입을 행 값 대입으로 정의**한다.\
「어느 쪽이 표준인가」는 이 편에서 **판정하지 않는다**(목록 README 의 규칙 — 표준 조항 번호를 확인하지 못했다).

**버전을 적은 자리** — 없다. 이 편의 문법은 두 엔진 모두 오래전부터 있고 **매뉴얼에 도입 버전이 없다.**

**돌려 보지 않은 것** — ① 14번의 MySQL 사용자 변수(`@t`) 경유 교환 ② 다중 표 `UPDATE` 로 **두 표를 동시에** 고치는 MySQL 형태 ③ 동시 세션에서의 갱신 경쟁([56 격리 수준](../56-isolation-levels-read-phenomena-mvcc/)·[57 명시적 잠금과 교착](../57-explicit-locking-and-deadlock/)) ④ 실행 계획(통계에 흔들리고 이 편의 결론과 무관하다).

**DB 잔재** — 없다. `t50_` 로 시작하는 표를 두 엔진에서 전부 삭제했고 `emp`·`dept` 는 **읽지도 쓰지도 않았다.**\
두 엔진의 최종 표 목록은 [54 편의 「실행 검증」](../54-returning-and-data-modifying-cte/3-answer.md)에 있다.
