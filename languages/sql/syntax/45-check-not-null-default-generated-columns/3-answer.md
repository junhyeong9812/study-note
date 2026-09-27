# sql/45-CHECK·NOT NULL·DEFAULT·생성 열·자동 증가 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **환경** — MySQL 의 `sql_mode` 에 `STRICT_TRANS_TABLES` 가 켜져 있다.\
> 이 편이 만든 표는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> 문서 근거는 [PG 18 Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) · [PG 18 Generated Columns](https://www.postgresql.org/docs/18/ddl-generated-columns.html) · [PG 18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/) · [MySQL 8.4 CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. ★★ `CHECK` 열에 `NULL` 을 넣으면 — **(a) 막힌다 / (b) 통과한다**

**출력**

```text
### SQL: INSERT INTO t45_chk (id,qty,name) VALUES (1,-5,'ann');
--- PG 18.6 ---
ERROR:  new row for relation "t45_chk" violates check constraint "t45_chk_qty_check"
DETAIL:  Failing row contains (1, -5, ann, B).
--- MySQL 8.4.10 ---
ERROR 3819 (HY000) at line 1: Check constraint 't45_chk_chk_1' is violated.
```

```text
### SQL: INSERT INTO t45_chk (id,qty,name) VALUES (2,NULL,'bob');
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
(성공)
```

들어간 것을 확인했다.

```text
### SQL: SELECT * FROM t45_chk;
--- PG 18.6 ---                      --- MySQL 8.4.10 ---
 id | qty | name | grade             +----+------+------+-------+
----+-----+------+-------            | id | qty  | name | grade |
  2 |     | bob  | B                 +----+------+------+-------+
(1 row)                              |  2 | NULL | bob  | B     |
                                     +----+------+------+-------+
```

**왜 그런가** — 2번이 그 설명이다.

★ **MySQL 의 `CHECK` 가 실제로 강제된다는 것도 이 출력이 근거다**(`ERROR 3819`).\
8.0.16 이전에는 파싱만 하고 무시했다 — **옛 버전을 직접 던져 보지는 못했다.**

---

### 2. ★ 왜 그런가 — **`CHECK` 는 `FALSE` 일 때만 막는다**

```text
CHECK 의 판정 규칙

  조건이 TRUE     -> 통과
  조건이 FALSE    -> 막는다
  조건이 UNKNOWN  -> ★ 통과

적용하면

  qty = -5    ->  -5 > 0   =  FALSE     -> 막힌다      (1번 a)
  qty = 10    ->  10 > 0   =  TRUE      -> 통과
  qty = NULL  ->  NULL > 0 =  UNKNOWN   -> 통과        (1번 b)
```

[04 NULL 의 3값 논리](../04-null-three-valued-logic/)의 결론이 그대로 적용된 것이다 —\
**`NULL` 이 낀 비교는 `FALSE` 가 아니라 `UNKNOWN` 이고, 제약은 `FALSE` 만 거부한다.**

**처방**

```sql
qty int NOT NULL CHECK (qty > 0)               -- 빈칸 자체를 막는다
qty int CHECK (qty IS NOT NULL AND qty > 0)    -- 조건 안에서 NULL 을 FALSE 로 만든다
```

둘째 형태는 `NULL AND ...` 가 아니라 `IS NOT NULL` 이 `FALSE` 를 내므로 전체가 `FALSE` 가 된다.

---

### 3. `WHERE` 와 `CHECK` 는 `UNKNOWN` 을 같이 다루나 — **반대로 다룬다**

```text
             무엇을 기준으로 삼나            UNKNOWN 행의 운명
────────────────────────────────────────────────────────────────
WHERE  절 :  TRUE 인 행만 남긴다              ★ 버려진다
CHECK 제약 :  FALSE 인 행만 막는다             ★ 통과한다
```

**같은 조건이 두 자리에서 반대로 작동한다.**

```text
qty > 0 이라는 같은 식

SELECT * FROM t WHERE qty > 0;      -> qty 가 NULL 인 행은 결과에 안 나온다
CHECK (qty > 0)                     -> qty 가 NULL 인 행은 들어간다
        ↓
"WHERE 로 확인했더니 위반 행이 없다" 가 "제약이 잘 지켜졌다" 를 뜻하지 않는다
```

★ **이 대비가 실무에서 조용한 사고를 만든다.**\
「`SELECT count(*) FROM t WHERE qty <= 0` 이 0 이다」로 검증하면 **`NULL` 행이 세어지지 않는다.**\
검증 질의는 `WHERE qty IS NULL OR qty <= 0` 이어야 한다.

---

### 4. `NOT NULL` 을 어기면 — **양쪽 다 막고, `grade` 는 이미 `B` 다**

**출력**

```text
### SQL: INSERT INTO t45_chk (id,qty,name) VALUES (3,5,NULL);
--- PG 18.6 ---
ERROR:  null value in column "name" of relation "t45_chk" violates not-null constraint
DETAIL:  Failing row contains (3, 5, null, B).
--- MySQL 8.4.10 ---
ERROR 1048 (23000) at line 1: Column 'name' cannot be null
```

**왜 그런가**

`NOT NULL` 은 **조건식이 아니라 「빈칸 금지」 그 자체**다. 3값 논리가 낄 자리가 없다.\
[43 번의 PK 에 `NULL`](../43-primary-key-unique-and-null/) 과 **글자까지 같은 에러**다 — PK 가 `NOT NULL` 을 포함하기 때문이다.

★ **`DETAIL` 의 네 번째 칸이 `B` 다.** 내가 `grade` 를 안 줬는데 이미 채워져 있다.

```text
INSERT (id, qty, name) 만 준다
        ↓
(1) DEFAULT 를 적용한다        grade = 'B'
        ↓
(2) 제약을 검사한다            name 이 NULL -> 거부
        ↓
에러 메시지에 (3, 5, null, B) 가 찍힌다
```

**기본값 적용이 제약 검사보다 먼저**라는 것을 에러 하나가 보여 준다.

---

### 5. ★ `DEFAULT CURRENT_TIMESTAMP` 는 언제 계산되나 — **`INSERT` 마다. 두 값이 다르다**

**출력**

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

**왜 그런가**

```text
CREATE TABLE 시점 : "CURRENT_TIMESTAMP" 라는 식(expression)을 카탈로그에 저장한다
INSERT 시점       : 그 식을 실행해 값을 만든다
```

★ **저장되는 것은 결과가 아니라 식이다.** 그래서 2초 차이가 값에 그대로 나타난다.\
만약 `CREATE TABLE` 때 한 번 계산돼 박혔다면 **두 행이 같은 값**이었을 것이다 — 그 반증이 위 출력이다.

★ **덤 — 정밀도가 다르다.** PG 는 마이크로초까지, MySQL 의 `timestamp` 는 **기본이 초 단위**다.\
초 미만이 필요하면 MySQL 에서는 `timestamp(6)` 으로 선언해야 한다\
([40 날짜·시간 타입과 함수](../40-date-time-types-and-functions/)가 정본이다).

---

### 6. `DEFAULT` 를 바꾸면 기존 행은 — **안 바뀐다**

**출력**

```text
### SQL: ALTER TABLE t45_def ALTER COLUMN g SET DEFAULT 'Z';
--- PG 18.6 ---
ALTER TABLE
--- MySQL 8.4.10 ---
(성공 — ★ 이 문법을 양쪽 다 받는다)

### SQL: INSERT INTO t45_def (id) VALUES (3);
        SELECT id, g FROM t45_def ORDER BY id;
--- PG 18.6 ---        --- MySQL 8.4.10 ---
 id | g                +----+------+
----+---               | id | g    |
  1 | B                +----+------+
  2 | B                |  1 | B    |
  3 | Z                |  2 | B    |
(3 rows)               |  3 | Z    |
                       +----+------+
```

**왜 그런가**

```text
DEFAULT 는 "그 순간 행에 복사되는 값" 이다
        ↓
1·2 행에는 이미 'B' 가 복사돼 들어 있다
        ↓
열의 기본값을 'Z' 로 바꿔도 그 행들의 값은 그대로다
        ↓
'Z' 는 그 뒤 INSERT 에만 적용된다
```

★ **[42 번의 `ADD COLUMN ... NOT NULL`](../42-create-alter-drop-table/) 과 대비하면 성질이 보인다.**\
그쪽은 **새 열이라 기존 행에 값이 없어서** 채워 넣었다.\
여기는 **이미 값이 있어서** 안 건드린다. 두 경우 다 「기존 행의 값은 함부로 안 고친다」는 같은 원칙이다.

기존 행까지 바꾸려면 `UPDATE` 를 따로 던져야 한다.

---

### 7. ★ `CHECK` 에 못 쓰는 것 — **(a) 둘 다 거부 / (b) PG 만 통과**

**출력 — (a) 서브쿼리**

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

**출력 — (b) 비결정 함수**

```text
### SQL: CREATE TABLE t45_cn (d date, CHECK (d <= CURRENT_DATE));
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
ERROR 3814 (HY000) at line 1: An expression of a check constraint 't45_cn_chk_1' contains
  disallowed function: curdate.
```

**왜 그런가**

```text
(a) 서브쿼리
    CHECK 는 "이 행 하나만 보고" 판정해야 한다
    다른 표를 보면 그 표가 바뀔 때마다 이미 통과한 행이 위반이 된다
    -> 둘 다 금지

(b) 비결정 함수
    같은 행이 시점에 따라 통과/위반이 갈린다
    -> MySQL 은 금지 (함수 이름 curdate 까지 찍어 준다)
    -> PG 는 허용     <- 8번이 그 위험이다
```

★ **MySQL 의 (a) 에러 코드가 `3815`(서브쿼리 포함) 이고 (b) 가 `3814`(함수) 다.**\
`3814` 는 **어느 함수가 문제인지 이름을 찍어 준다** — `disallowed function: curdate`.

---

### 8. 7번 (b) 를 받아 주는 쪽의 위험 — **검사 시점과 데이터가 어긋난다**

**PG 는 받아 주고 실제로 동작한다.**

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

**무엇이 문제인가**

```text
CHECK 는 "행이 들어오거나 바뀔 때" 만 검사된다
        ↓
그 사이에 CURRENT_DATE 는 계속 움직인다
        ↓
표 안의 데이터와 제약식의 관계가 "지금 다시 검사하면 어떻게 되나" 로만 정의된다
        ↓
다시 검사되는 순간이 오면 결과가 달라질 수 있다
```

**다시 검사되는 순간**은 이런 것들이다.

```text
- 덤프를 복원할 때 (제약을 다시 걸면서 검증한다)
- ALTER TABLE ... VALIDATE CONSTRAINT 를 돌릴 때
- 그 행을 UPDATE 할 때 (값을 안 바꿔도 제약은 다시 검사된다)
```

★ **이 실험에서 그 거부 자체는 재현하지 못했다** — 재현하려면 날짜를 넘기거나 덤프/복원을 돌려야 한다.\
**재현한 것은 「PG 가 이 제약을 받아 준다」까지**이고, 그 뒤는 검사 시점에서 따라 나오는 결론이다.

**규칙** — **`CHECK` 에는 「그 행의 값만으로 영원히 판정되는 것」만 쓴다.**\
「미래 날짜 금지」 같은 요구는 애플리케이션이나 트리거로 옮긴다.

---

### 9. ★ 생성 열의 `STORED` 와 `VIRTUAL` — **셋 다 통과. (c) 는 양쪽 다 `VIRTUAL`**

**출력**

```text
### SQL: ... STORED / ... VIRTUAL / 키워드 없음
--- PG 18.6 ---
CREATE TABLE      (a)
CREATE TABLE      (b)     <- ★ VIRTUAL 이 통과한다
CREATE TABLE      (c)
--- MySQL 8.4.10 ---
(세 문 다 성공)
```

**(c) 가 무엇이 됐는지 카탈로그에 물었다.**

```text
--- PG 18.6 ---
 relname | attgenerated 
---------+--------------
 t45_gd  | v                <- 키워드 없음 -> VIRTUAL
 t45_gs  | s
 t45_gv  | v

--- MySQL 8.4.10 ---
+------------+-------------------+
| TABLE_NAME | EXTRA             |
+------------+-------------------+
| t45_gd     | VIRTUAL GENERATED |     <- 키워드 없음 -> VIRTUAL
| t45_gs     | STORED GENERATED  |
| t45_gv     | VIRTUAL GENERATED |
+------------+-------------------+
```

**왜 그런가 — ★ 버전이 붙는 자리다**

```text
PostgreSQL 17 이하 : STORED 만 있었다. 키워드를 빼면 에러였다
PostgreSQL 18      : VIRTUAL 이 생겼고, ★ 키워드 없을 때의 기본이 VIRTUAL 이 됐다
MySQL 5.7+         : 처음부터 둘 다 있었고 기본이 VIRTUAL 이었다
```

근거는 [PostgreSQL 18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)와 위 실측이다.\
**이 머신에 PG 17 컨테이너가 없어 17 이하의 에러는 직접 던져 보지 못했다.**

**둘의 성질**

```text
              STORED                       VIRTUAL
저장          디스크에 값을 쓴다            안 쓴다
읽기          그냥 읽는다                  읽을 때마다 계산한다
쓰기 비용      INSERT/UPDATE 마다 계산+저장  없다
공간          열 하나만큼                  안 든다
인덱스        걸 수 있다                   ★ 엔진에 따라 다르다 (46번)
```

---

### 10. ★ 생성 열에 직접 대입하면 — **(a)(b) 거부 / (c) `DEFAULT` 는 허용**

**출력**

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

```text
### SQL: INSERT INTO t45_gs (id,price,qty,total) VALUES (3,10,2,DEFAULT);
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
(성공)
```

**왜 그런가**

★ **PG 의 두 에러 문구가 서로 다르다** — 그리고 둘 다 **`DEFAULT` 만은 허용한다**고 말한다.

```text
INSERT 쪽 : "cannot insert a non-DEFAULT value"        -> DEFAULT 는 된다
UPDATE 쪽 : "column can only be updated to DEFAULT"    -> DEFAULT 는 된다
```

(c) 의 성공이 그 문구를 확인해 준다. MySQL 은 두 경우 모두 `ERROR 3105` 로 같다.

**기반 열을 바꾸면 따라 바뀐다.**

```text
### SQL: UPDATE t45_gs SET qty=5 WHERE id=1;    (price=100, total 은 300 이었다)
        SELECT * FROM t45_gs ORDER BY id;
--- PG 18.6 ---                       --- MySQL 8.4.10 ---
 id | price | qty | total             +----+-------+------+-------+
----+-------+-----+-------            | id | price | qty  | total |
  1 |   100 |   5 |   500             +----+-------+------+-------+
  3 |    10 |   2 |    20             |  1 |   100 |    5 |   500 |
(2 rows)                              |  3 |    10 |    2 |    20 |
                                      +----+-------+------+-------+
```

**실무 함의** — `INSERT` 문을 자동 생성하는 ORM 은 그 열을 **읽기 전용으로 표시**해야 한다.\
안 그러면 모든 저장이 `ERROR 3105` / `cannot insert a non-DEFAULT value` 로 실패한다.

---

### 11. ★ 자동 증가 세 이름 — **둘은 서로를 거부하고, 하나는 조용히 다르다**

**출력**

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

★ **가장 위험한 것은 `serial` 이다 — 양쪽 다 통과하는데 결과가 다르다.**

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

**세 가지가 다르다.**

```text
              PG 의 serial              MySQL 의 SERIAL
타입          integer (4바이트)          bigint unsigned (8바이트)
구현          별도 시퀀스 객체            AUTO_INCREMENT
덤            —                          ★ UNIQUE KEY 가 하나 더 생긴다 (PK 와 같은 열에 중복)
```

**왜 위험한가** — [35 번의 `CAST(123 AS CHAR)`](../35-type-system-and-casting/) · [42 번의 이식 목록](../42-create-alter-drop-table/) 과 같은 구조다.

```text
IDENTITY / AUTO_INCREMENT  -> 상대 엔진이 문법 에러로 거절한다  -> 배포 전에 드러난다. 안전하다
serial                     -> 양쪽 다 통과한다                 -> ★ 끝까지 모른다
```

MySQL 쪽에는 **쓸모없는 인덱스가 하나 더** 생기고(쓰기마다 갱신된다), 키 폭이 두 배가 된다.

---

### 12. 그래서 어떻게 설계하나 — **`NOT NULL` + `CHECK` 를 세트로**

```sql
qty int NOT NULL CHECK (qty > 0)
```

**왜 둘 다 필요한가**

```text
CHECK (qty > 0) 만    -> qty = NULL 이 통과한다            (1·2번)
NOT NULL 만           -> qty = -5 가 통과한다
둘 다                 -> 빈칸도 음수도 못 들어온다
```

**검증 질의도 같이 정한다.**

```sql
-- 틀린 검증 (NULL 행을 못 센다 — 3번)
SELECT count(*) FROM t WHERE qty <= 0;

-- 맞는 검증
SELECT count(*) FROM t WHERE qty IS NULL OR qty <= 0;
```

**이식까지 생각하면 두 가지를 더 고른다.**

```text
자동 증가   : 엔진별로 다른 문법을 쓴다. serial 은 쓰지 않는다 (11번)
생성 열     : STORED 를 명시한다. 키워드를 빼면 엔진·버전에 따라 VIRTUAL 이 된다 (9번)
```

**엔진에 맡기지 말아야 할 것도 하나 있다.**

```text
"오늘 이전 날짜만" 같은 시간 의존 규칙
  -> PG 는 받아 주지만 어긋난다 (8번)
  -> 애플리케이션이나 트리거로 옮긴다
```

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `sql_mode` 조회 (머리말) | MySQL 8.4.10 | 1회 | `STRICT_TRANS_TABLES` 확인 |
| `CHECK` 위반 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 3819 가 MySQL 강제의 근거다** |
| ★ `CHECK` 열에 `NULL` (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **둘 다 통과 — 삽입 + `SELECT` 확인** |
| `NOT NULL` 위반 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`DETAIL` 의 `B` 가 기본값 선적용의 근거다** |
| `DEFAULT CURRENT_TIMESTAMP` (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **2초 간격 두 번 — 값이 달랐다** |
| `SET DEFAULT` 후 재삽입 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **기존 행 불변 확인** |
| `DROP DEFAULT` (문법표) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **양쪽 다 받는다** |
| `CHECK` 에 서브쿼리 (7a) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러가 근거다** |
| `CHECK` 에 `CURRENT_DATE` (7b·8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 성공 / MySQL `ERROR 3814`** |
| 7b 의 PG 제약에 삽입 (8번) | PG 18.6 | 1회 | 오늘 날짜는 통과 |
| 표 수준 `CHECK` (문법표) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **이름을 주면 두 엔진이 같은 이름을 찍는다** |
| 생성 열 3종 선언 (9번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **PG 18 이 `VIRTUAL` 을 받았다** |
| 카탈로그로 저장 방식 확인 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `pg_attribute.attgenerated` · `information_schema.columns.extra` |
| 생성 열 직접 대입 (10번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `INSERT`·`UPDATE`·`DEFAULT` |
| 기반 열 변경 전파 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `total` 이 300 → 500 |
| 자동 증가 3종 (11번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **`serial` 만 양쪽 통과** |
| `serial` 의 결과 정의 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`integer` 대 `bigint unsigned`** |

**구현 의존 항목** — 1·7·10번의 **에러 코드·문구**, 5번의 **시간 정밀도**,\
11번의 **`serial` 이 무엇으로 펼쳐지는가**.\
외울 것은 문구가 아니라 **「`CHECK` 는 `FALSE` 만 막는다」**·「**`serial` 은 엔진마다 다른 것이 된다**」는 성질이다.

**언어 보장 항목** — 1·2·3·5·6·10번.\
`CHECK` 가 `UNKNOWN` 을 통과시킨다는 것, `DEFAULT` 가 `INSERT` 때 계산된다는 것,\
생성 열에 직접 대입할 수 없다는 것은 두 매뉴얼의 제약·생성 열 페이지가 정한 것이다.

**버전을 적은 자리** — ★ **생성 열의 기본이 `VIRTUAL` 인 것은 PostgreSQL 18 부터다**\
([18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)). MySQL 의 `CHECK` 강제는 8.0.16 부터다.\
**버전을 못 적은 자리** — 이 머신에 PG 17 이하·MySQL 8.0.15 이하 컨테이너가 없어\
**옛 동작(생성 열 키워드 생략 시 에러 · `CHECK` 무시)은 직접 재현하지 못했다.**

**DB 잔재** — 없다. `t45_` 로 시작하는 표를 전부 삭제했고 `emp`·`dept` 는 **읽지도 쓰지도 않았다.**\
두 엔진의 최종 표 목록 출력은 [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)의 「실행 검증」에 있다.
