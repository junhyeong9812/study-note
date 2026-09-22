# sql/43-기본키·UNIQUE 제약과 NULL — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) · [PostgreSQL 18 · CREATE TABLE](https://www.postgresql.org/docs/18/sql-createtable.html) · [MySQL 8.4 · CREATE TABLE](https://dev.mysql.com/doc/refman/8.4/en/create-table.html) · [MySQL 8.4 · Primary Key Optimization](https://dev.mysql.com/doc/refman/8.4/en/primary-key-optimization.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — `UNIQUE ... NULLS NOT DISTINCT` 는 PostgreSQL 15 부터다(**MySQL 8.4.10 은 문법 에러** — 아래 4번에서 던져 확인).\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 `t43_pk`·`t43_nnd`·`t43_comp`·`t43_addpk`·`t43_un` 을 만들었고 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> **선행** — [04 NULL 의 3값 논리](../04-null-three-valued-logic/) · [42 테이블 정의와 변경](../42-create-alter-drop-table/) · 이어지는 것은 [44 외래키](../44-foreign-key-referential-actions/) · [46 인덱스 정의](../46-index-definition-composite-partial-expression/) 다.

## 한눈에 — 쉽게 말하면

**기본키 = 「이 열로 행 하나를 콕 집을 수 있다」는 약속.**

그 약속은 두 조각으로 쪼개진다.

```text
PRIMARY KEY  =  UNIQUE  +  NOT NULL
                  ↑          ↑
            "겹치지 않는다"  "비어 있지 않다"
```

**`UNIQUE` 만 걸면 둘째 조각이 빠진다.** 그리고 그 빠진 자리에서 [04 의 3값 논리](../04-null-three-valued-logic/)가 그대로 나타난다.

```text
주민번호로 사람을 찾는다 (PRIMARY KEY)
  - 같은 번호인 사람은 없다          = UNIQUE
  - 번호가 없는 사람도 없다          = NOT NULL
        ↓
"똑같은 구조다"
        ↓
사번으로 사원을 찾는다 (emp.id)

그런데 "사내 메일 주소"는 UNIQUE 이지만 NOT NULL 이 아니다
  - 같은 주소를 쓰는 사람은 없다
  - ★ 아직 주소를 안 받은 사람은 여럿 있다   <- NULL 이 여러 개 들어간다
```

| 비유 | 실체 |
|---|---|
| 주민번호 | `PRIMARY KEY` — 겹치지도, 비지도 않는다 |
| 사내 메일 주소 | `UNIQUE` — 겹치지 않지만 **빌 수 있다** |
| 「아직 안 받았다」가 여럿 | `UNIQUE` 열에 `NULL` 이 여러 개 |
| 「번호가 같은가?」에 답할 수 없다 | `NULL = NULL` 이 `UNKNOWN` — 그래서 중복 판정이 안 선다 |
| 신분증은 하나만 | 표당 `PRIMARY KEY` 는 하나 |

> **제약(constraint)** — 엔진이 대신 지켜 주는 불변식. 어기는 문은 실행되지 않는다.\
> 예: `UNIQUE` 가 걸린 열에 중복 값을 넣으면 애플리케이션 코드가 없어도 `INSERT` 가 죽는다.

## 이 주제가 답하려는 질문

1. **`PRIMARY KEY` 는 정확히 무엇의 합인가?** — 그리고 그 합을 손으로 쓰면 같은 것이 되나?
2. **★ `UNIQUE` 열에 `NULL` 은 몇 개까지 들어가나?** — [04 의 3값 논리](../04-null-three-valued-logic/)가 제약에서도 나타난다.
3. **복합 `UNIQUE` 에서 일부만 `NULL` 이면 어떻게 되나?**

## 예시 데이터 — 이 묶음이 공유하는 것

이 편도 [42번](../42-create-alter-drop-table/)처럼 **표를 직접 만들었다가 지운다.** `emp`·`dept` 는 읽지 않는다.

```text
t43_pk                                t43_comp
+----+------+------+                  +---+------+
| id | code | name |                  | a | b    |    UNIQUE (a, b)
+----+------+------+                  +---+------+
|  1 | A    | ann  |   id  : PK       | 1 | NULL |
|  3 | NULL | eve  |   code: UNIQUE   | 1 | NULL |   <- 같은 값이 두 번 들어갔다
|  4 | NULL | fay  |                  | 1 | 2    |
+----+------+------+                  +---+------+
```

`t43_nnd`(PG 전용 `NULLS NOT DISTINCT`) · `t43_addpk`(나중에 PK 를 붙이는 실험) · `t43_un`(`NOT NULL UNIQUE`)도 썼고 **전부 지웠다.**

## 동작 방식

### 1. `PRIMARY KEY` 는 **`UNIQUE` + `NOT NULL` + 인덱스**다

**언제 쓰나** — 표를 만들 때. 대부분의 표에 하나 있다.

```sql
CREATE TABLE t43_pk (id int PRIMARY KEY, code varchar(10) UNIQUE, name varchar(10));
```

**두 엔진이 같은 세 가지를 만들었다.**

```text
--- PG 18.6 ---
\d t43_pk
                      Table "public.t43_pk"
 Column |         Type          | Collation | Nullable | Default 
--------+-----------------------+-----------+----------+---------
 id     | integer               |           | not null |          <- (1) NOT NULL 이 붙었다
 code   | character varying(10) |           |          | 
 name   | character varying(10) |           |          | 
Indexes:
    "t43_pk_pkey" PRIMARY KEY, btree (id)                          <- (2)(3) 유일성 + 인덱스
    "t43_pk_code_key" UNIQUE CONSTRAINT, btree (code)

--- MySQL 8.4.10 ---
SHOW CREATE TABLE t43_pk\G
Create Table: CREATE TABLE `t43_pk` (
  `id` int NOT NULL,                                               <- (1)
  `code` varchar(10) DEFAULT NULL,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),                                              <- (2)(3)
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

그림 해설 — `PRIMARY KEY` 한 단어가 **세 가지를 동시에 만든다.**

```text
PRIMARY KEY (id)
   ├─ id 에 NOT NULL 을 붙인다          <- 내가 안 썼는데 붙었다
   ├─ id 의 유일성을 보장한다
   └─ 그 보장을 위해 인덱스를 만든다      <- 46번의 "UNIQUE 인덱스" 가 이것이다
```

비용 — **인덱스 하나가 공짜로 생긴다.** 쓰기마다 그 인덱스도 갱신되므로 공짜가 아니다(46번).

`code` 쪽은 `NOT NULL` 이 안 붙었다. **`UNIQUE` 는 NULL 허용을 건드리지 않는다.** 이것이 2~4번의 출발점이다.

### 2. 어기면 무엇이 출력되나 — **PK 에 `NULL`·중복**

**언제 쓰나** — 제약이 실제로 막아 주는지 확인할 때. **에러 문구가 이 절의 본문**이다.

```text
### SQL: INSERT INTO t43_pk VALUES (NULL,'B','bob');
--- PG 18.6 ---
ERROR:  null value in column "id" of relation "t43_pk" violates not-null constraint
DETAIL:  Failing row contains (null, B, bob).
--- MySQL 8.4.10 ---
ERROR 1048 (23000) at line 1: Column 'id' cannot be null
```

```text
### SQL: INSERT INTO t43_pk VALUES (1,'C','cho');       (id=1 이 이미 있다)
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t43_pk_pkey"
DETAIL:  Key (id)=(1) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry '1' for key 't43_pk.PRIMARY'
```

```text
### SQL: INSERT INTO t43_pk VALUES (2,'A','dan');       (code='A' 가 이미 있다)
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t43_pk_code_key"
DETAIL:  Key (code)=(A) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry 'A' for key 't43_pk.code'
```

그림 해설 — **에러가 세 정보를 준다.**

```text
PG   : 제약 이름 t43_pk_pkey  +  어느 키가  +  DETAIL 로 그 값
MySQL: 제약 이름 t43_pk.PRIMARY +  중복된 값 '1'
```

★ **`NULL` 거부와 중복 거부는 서로 다른 에러다.** PK 를 「하나의 제약」으로 외우면 이 둘이 섞인다.\
PG 는 `not-null constraint` 와 `unique constraint` 로 **말까지 나눠서 한다.**

비용 — 제약 위반은 **그 문 전체를 되돌린다.** 여러 행을 한 문으로 넣다가 하나만 위반해도 전부 안 들어간다.

### 3. ★ `UNIQUE` 열에 `NULL` 이 여럿 — **두 엔진 다 들어간다**

**언제 쓰나** — 「나중에 채울 수도 있는 고유 값」을 설계할 때. 이 주제의 핵심이다.

`t43_pk.code` 는 `UNIQUE` 다. `NULL` 을 두 번 넣는다.

```text
### SQL: INSERT INTO t43_pk VALUES (3,NULL,'eve');
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
(성공)

### SQL: INSERT INTO t43_pk VALUES (4,NULL,'fay');
--- PG 18.6 ---
INSERT 0 1
--- MySQL 8.4.10 ---
(성공)
```

**둘 다 들어갔다.**

```text
### SQL: SELECT * FROM t43_pk ORDER BY id;
--- PG 18.6 ---
 id | code | name 
----+------+------
  1 | A    | ann
  3 |      | eve
  4 |      | fay
(3 rows)

--- MySQL 8.4.10 ---
+----+------+------+
| id | code | name |
+----+------+------+
|  1 | A    | ann  |
|  3 | NULL | eve  |
|  4 | NULL | fay  |
+----+------+------+
```

**왜 이렇게 되나 — [04 의 3값 논리](../04-null-three-valued-logic/)가 그대로 여기 있다.**

```text
UNIQUE 가 하는 일: "새 값이 기존 값과 같은가?" 를 묻는다
        ↓
NULL 을 넣을 때 묻는 질문:  NULL = NULL ?
        ↓
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 eq                         +------+
----                        | eq   |
                            +------+
(1 row)   <- NULL 이다      | NULL |
        ↓
답이 TRUE 가 아니다 -> "같다" 고 판정되지 않는다 -> 중복이 아니다
```

그림 해설 — **`UNIQUE` 는 「값이 같으면 막는다」이지 「빈칸이 여럿이면 막는다」가 아니다.**\
`NULL` 은 「값이 없다」이므로 **서로 같은지 물을 수조차 없고**, 그래서 몇 개든 들어간다.

대가 — **「이 열은 UNIQUE 니까 중복이 없다」가 거짓이 될 수 있다.**\
애플리케이션이 `code` 를 안 채운 행을 100만 개 만들어도 제약은 한 번도 안 걸린다.

처방은 하나다 — **정말 하나만 있어야 하면 `NOT NULL` 을 같이 건다.**

```text
--- PG 18.6 ---
CREATE TABLE t43_un (a int NOT NULL UNIQUE, b int);
\d t43_un
 Column |  Type   | Collation | Nullable | Default 
--------+---------+-----------+----------+---------
 a      | integer |           | not null | 
 b      | integer |           |          | 
Indexes:
    "t43_un_a_key" UNIQUE CONSTRAINT, btree (a)

--- MySQL 8.4.10 ---
Create Table: CREATE TABLE `t43_un` (
  `a` int NOT NULL,
  `b` int DEFAULT NULL,
  UNIQUE KEY `a` (`a`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

**`NOT NULL UNIQUE` 는 PK 와 값의 성질이 같다.** 다른 것은 「이 표의 대표 키」라는 표시뿐이다.

### 4. ★ PG 만 갈 수 있는 길 — `NULLS NOT DISTINCT`

**언제 쓰나** — 「빈칸도 하나만 허용하고 싶다」일 때. **PG 15 부터 있는 문법**이다.

```text
### SQL: CREATE TABLE t43_nnd (code varchar(10) UNIQUE NULLS NOT DISTINCT);
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'NULLS NOT DISTINCT)' at line 1
```

PG 에서 `NULL` 을 두 번 넣으면 **이번에는 막힌다.**

```text
--- PG 18.6 ---
INSERT INTO t43_nnd VALUES (NULL);
INSERT 0 1

INSERT INTO t43_nnd VALUES (NULL);
ERROR:  duplicate key value violates unique constraint "t43_nnd_code_key"
DETAIL:  Key (code)=(null) already exists.
```

★ **`DETAIL` 에 `(code)=(null)` 이 적혀 있다** — 엔진이 `NULL` 을 **하나의 값으로 취급**했다는 증거다.

```text
기본(NULLS DISTINCT)          NULLS NOT DISTINCT
NULL 끼리는 서로 다르다         NULL 끼리는 서로 같다
  -> 몇 개든 들어간다             -> 하나만 들어간다
```

**한쪽에서만 결론이 서는 실험이다.** MySQL 쪽 출력은 **문법 에러**이므로\
「MySQL 은 `NULL` 을 하나만 허용한다/여럿 허용한다」의 근거가 **되지 못한다** — 문 자체가 안 섰다.\
MySQL 의 동작에 대한 근거는 **3번의 성공한 `INSERT` 두 줄**이다.

비용 — 이식성이 없다. MySQL 로 옮길 계획이 있으면 **부분 유니크 인덱스**(46번)나 애플리케이션 검사로 대신한다.

### 5. ★ 복합 `UNIQUE` — **일부만 `NULL` 이어도 「모르는 것」이다**

**언제 쓰나** — `(회사, 사번)` 처럼 둘을 묶어 유일해야 할 때. 여기가 3번보다 자주 사고 난다.

```sql
CREATE TABLE t43_comp (a int, b int, UNIQUE (a,b));
```

**둘 다 값이 있으면 막힌다.**

```text
### SQL: INSERT INTO t43_comp VALUES (1,2);    두 번째
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t43_comp_a_b_key"
DETAIL:  Key (a, b)=(1, 2) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry '1-2' for key 't43_comp.a'
```

**한쪽만 `NULL` 이면 안 막힌다.**

```text
### SQL: INSERT INTO t43_comp VALUES (1,NULL);   두 번 던졌다
--- PG 18.6 ---
INSERT 0 1
INSERT 0 1
--- MySQL 8.4.10 ---
(두 번 다 성공)
```

```text
### SQL: SELECT * FROM t43_comp;
--- PG 18.6 ---              --- MySQL 8.4.10 ---
 a | b                       +------+------+
---+---                      | a    | b    |
 1 |                         +------+------+
 1 |                         |    1 | NULL |
 1 | 2                       |    1 | NULL |
(3 rows)                     |    1 |    2 |
                             +------+------+
```

그림 해설 — **복합 키의 비교는 「전부 같은가」다.** 한 칸이라도 `UNKNOWN` 이면 전체가 `UNKNOWN` 이다.

```text
(1, NULL) 과 (1, NULL) 이 같은가?
   a:  1 = 1        -> TRUE
   b:  NULL = NULL  -> UNKNOWN
   합: TRUE AND UNKNOWN = UNKNOWN            <- 04 의 진리표 그대로
        ↓
"같다" 가 아니므로 중복이 아니다 -> 들어간다
```

★ **이것이 실무에서 가장 조용한 중복 사고다.** `(tenant_id, external_id)` 에 `UNIQUE` 를 걸어 놓고\
`external_id` 가 `NULL` 인 행이 쌓이면 **제약은 초록인데 중복이 생긴다.**

비용 — 복합 `UNIQUE` 를 쓸 거면 **구성 열 전부에 `NOT NULL` 을 거는지** 같이 결정한다.

### 6. 나중에 `PRIMARY KEY` 를 붙이면 — **둘 다 거부한다**

**언제 쓰나** — 이미 데이터가 있는 표에 PK 를 늦게 붙일 때. [42번의 `NOT NULL` 열 추가](../42-create-alter-drop-table/)와 짝이다.

```sql
CREATE TABLE t43_addpk (id int, v varchar(5));
INSERT INTO t43_addpk VALUES (1,'a'), (NULL,'b');
ALTER TABLE t43_addpk ADD PRIMARY KEY (id);
```

```text
--- PG 18.6 ---
ERROR:  column "id" of relation "t43_addpk" contains null values
--- MySQL 8.4.10 ---
ERROR 1138 (22004) at line 1: Invalid use of NULL value
```

★ **여기서는 MySQL 도 막는다.** [42번 7번에서 `NOT NULL` 열 추가를 MySQL 이 조용히 통과시킨 것](../42-create-alter-drop-table/)과 **다르다.**

```text
ALTER TABLE t ADD COLUMN req int NOT NULL     -> MySQL: 통과. 기존 행을 0 으로 채운다
ALTER TABLE t ADD PRIMARY KEY (id)            -> MySQL: ERROR 1138. 거부한다
```

**새 열은 채울 값을 지어낼 수 있지만, 이미 있는 열의 `NULL` 은 지어낼 수 없다** — 그 차이다.\
행이 그대로 남아 있는지 확인했다.

```text
--- PG 18.6 ---              --- MySQL 8.4.10 ---
 id | v                      +------+------+
----+---                     | id   | v    |
  1 | a                      +------+------+
    | b                      |    1 | a    |
(2 rows)                     | NULL | b    |
                             +------+------+
```

**표당 `PRIMARY KEY` 는 하나뿐**인 것도 던져서 확인했다.

```text
### SQL: CREATE TABLE t43_two (a int PRIMARY KEY, b int PRIMARY KEY);
--- PG 18.6 ---
ERROR:  multiple primary keys for table "t43_two" are not allowed
LINE 1: CREATE TABLE t43_two (a int PRIMARY KEY, b int PRIMARY KEY);
                                                       ^
--- MySQL 8.4.10 ---
ERROR 1068 (42000) at line 1: Multiple primary key defined
```

여러 열을 묶어 키로 쓰려면 **복합 PK 를 하나 선언**한다 — `PRIMARY KEY (a, b)`.

## 문법 — 어느 절에서 무엇이 갈리나

제약은 **열 뒤에 붙이는 형태**와 **표 수준에서 따로 선언하는 형태**가 있다. 복합 키는 후자로만 된다.

```sql
-- 열 뒤에 (단일 열만)
CREATE TABLE t (id int PRIMARY KEY, code varchar(10) UNIQUE);            -- 양쪽

-- 표 수준 (복합 키는 이 형태로만)
CREATE TABLE t (a int, b int, PRIMARY KEY (a,b), UNIQUE (a,b));          -- 양쪽

-- 제약에 이름을 준다
CREATE TABLE t (a int, CONSTRAINT t_a_uq UNIQUE (a));                    -- 양쪽

-- NULL 도 하나만
CREATE TABLE t (a int UNIQUE NULLS NOT DISTINCT);                        -- ★ PG 15+ 만

-- 나중에 붙이기
ALTER TABLE t ADD PRIMARY KEY (id);                                      -- 양쪽
ALTER TABLE t ADD CONSTRAINT t_a_uq UNIQUE (a);                          -- 양쪽

-- 떼어내기
ALTER TABLE t DROP CONSTRAINT t_a_uq;                                    -- ★ 양쪽 다 된다
ALTER TABLE t DROP INDEX t_a_uq;                                         -- MySQL (46번)
```

- **이름을 안 주면 엔진이 짓는다.** PG 는 `표_열_key`·`표_pkey`, MySQL 은 **열 이름 그대로**(`UNIQUE KEY code`).\
  에러 메시지에 그 이름이 박히므로 **이름을 직접 주면 로그가 읽기 쉬워진다.**
- ★ **`DROP CONSTRAINT` 는 MySQL 8.4.10 도 받는다** — 던져서 확인했다. 「MySQL 에는 `DROP INDEX` 밖에 없다」는 틀렸다.

```text
### SQL: CREATE TABLE t43_dc (a int, CONSTRAINT t43_dc_a_uq UNIQUE (a));
        ALTER TABLE t43_dc DROP CONSTRAINT t43_dc_a_uq;
--- PG 18.6 ---
CREATE TABLE
ALTER TABLE
--- MySQL 8.4.10 ---
(둘 다 성공)

--- MySQL 8.4.10 ---  지워졌는지 확인
SHOW CREATE TABLE t43_dc\G
Create Table: CREATE TABLE `t43_dc` (
  `a` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

## 어디서 틀리나

1. **「`UNIQUE` 니까 중복이 없다」 — `NULL` 에는 해당 안 된다.**\
   두 엔진 다 `NULL` 을 **몇 개든** 받는다(3번). 「한 개만」을 원하면 `NOT NULL` 을 같이 건다.
2. **복합 `UNIQUE` 에서 한 칸만 `NULL` 이어도 통과한다.**\
   `TRUE AND UNKNOWN = UNKNOWN` 이라 **중복 판정이 안 선다**(5번). 실무 사고의 대부분이 여기다.
3. **`PRIMARY KEY` 가 `NOT NULL` 을 붙여 준다는 것을 잊는다.**\
   `id int PRIMARY KEY` 만 썼는데 `\d` 에 `not null` 이 있다(1번). **내가 안 쓴 제약이 생긴 것**이다.
4. **`NULLS NOT DISTINCT` 를 이식 가능한 문법으로 착각한다.**\
   **MySQL 은 `ERROR 1064`** 다(4번).
5. **PK 를 두 개 선언한다.** 복합 PK 는 `PRIMARY KEY (a,b)` 한 줄이다(6번).
6. **「MySQL 은 PK 를 붙이면 `NULL` 을 `0` 으로 바꾼다」로 외운다.**\
   **MySQL 8.4.10 은 `ERROR 1138` 로 거부한다**(6번). 던져서 확인한 결과다.
7. **제약 이름을 안 주고 에러 로그를 읽으려 한다.**\
   `t43_pk.code` 처럼 자동 생성 이름이 찍힌다. **열 이름과 제약 이름이 같아져** 혼동된다.
8. **`UNIQUE` 가 인덱스를 만든다는 것을 비용에서 빼먹는다.**\
   유일성을 확인하려면 정렬된 자료가 필요하다 — **제약 하나 = 인덱스 하나**다(46번).

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| `PRIMARY KEY` | `UNIQUE` + `NOT NULL` | 인덱스 이름 · 클러스터링 여부 |
| `UNIQUE` 에 `NULL` | 기본은 `NULL` 끼리 서로 다르다 | — (두 엔진이 같았다) |
| `NULLS NOT DISTINCT` | PG 15+ 의 선택지 | **MySQL 에 없다** |
| 위반 에러 | 문이 실패한다 | **에러 코드·문구·제약 이름** |
| 제약 이름 | 내가 주면 그것을 쓴다 | 안 주면 **엔진마다 다른 규칙**으로 짓는다 |

- **「`NULL` 이 여럿 들어간다」는 이 실험에서 두 엔진이 같았지만, 그것은 보장의 근거가 아니라 관찰이다.**\
  근거는 **`NULL = NULL` 이 `UNKNOWN`** 이라는 3값 논리다([04번](../04-null-three-valued-logic/)).\
  같은 논리를 따르는 엔진이면 같게 동작한다 — **같은 출력이 나왔다는 사실 자체가 근거인 것은 아니다.**
- **`ERROR 1062` 의 `'1-2'` 같은 복합 키 표기**는 MySQL 의 구현 세부다. 파싱해서 쓰지 않는다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 거의 모든 표에 `PRIMARY KEY`.** 행을 짚을 수단이 없으면 `UPDATE`·`DELETE` 가 위험해진다.
- **쓴다 — 자연키가 흔들리면 대리키.** 사번·이메일은 바뀐다. 바뀌는 열을 PK 로 쓰면 [44번의 `ON UPDATE CASCADE`](../44-foreign-key-referential-actions/) 가 필요해진다.
- **쓴다 — `UNIQUE` + `NOT NULL` 을 세트로.** 「하나만」을 뜻하려면 둘 다 필요하다.
- **안 쓴다 — `NULL` 이 들어갈 수 있는 열만으로 복합 `UNIQUE`.** 제약이 조용히 무력해진다(5번).
- **조심한다 — `NULLS NOT DISTINCT`.** PG 15+ 전용이다. MySQL 이식 계획이 있으면 쓰지 않는다.
- **조심한다 — PK 를 나중에 붙이기.** 기존 `NULL` 이 있으면 양쪽 다 거부한다. **먼저 채워야 한다**(6번).

## 핵심 문장

- **`PRIMARY KEY` = `UNIQUE` + `NOT NULL` + 인덱스.** 한 단어가 셋을 만든다.
- **`UNIQUE` 열에는 `NULL` 이 여러 개 들어간다 — 두 엔진 다.** `NULL = NULL` 이 `UNKNOWN` 이기 때문이다.
- **복합 `UNIQUE` 는 한 칸만 `NULL` 이어도 중복 판정이 안 선다.** `TRUE AND UNKNOWN = UNKNOWN`.
- **`NULLS NOT DISTINCT` 는 PG 15+ 뿐이다.** MySQL 은 문법 에러로 거절한다.
- **`NULL` 거부와 중복 거부는 서로 다른 에러다.** PG 가 말까지 나눠서 한다.
- **PK 를 나중에 붙일 때는 두 엔진 다 `NULL` 을 거부한다.** 42번의 `NOT NULL` 열 추가와 다르다.

## 관련 자료

- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **그쪽은 `WHERE`·`AND`/`OR` 에서 `UNKNOWN` 이 어떻게 계산되나까지,\
  여기는 그 논리가 제약의 중복 판정에 나타나는 자리부터.** 진리표는 한 줄도 여기서 다시 쓰지 않는다.
- [42 테이블 정의와 변경](../42-create-alter-drop-table/) — 이 제약들을 어디에 적나.
- [44 외래키와 참조 동작](../44-foreign-key-referential-actions/) — 외래키는 **여기서 만든 키를 가리킨다.** 선행이다.
- [46 인덱스 정의](../46-index-definition-composite-partial-expression/) — **`UNIQUE` 제약과 `UNIQUE` 인덱스의 관계**는 거기가 정본이다.
- [05 NULL 비교 — IS NULL·IS DISTINCT FROM](../05-null-comparison-is-distinct-from/) — `IS DISTINCT FROM` 이 `NULLS NOT DISTINCT` 와 같은 발상이다.
- [SQL 주제 목록](../README.md) — 45(CHECK·NOT NULL) · 52(upsert — 충돌 대상이 이 제약이다) 가 이웃이다.

## 용어 풀이

- **제약(constraint)** — 엔진이 대신 지켜 주는 불변식. 어기는 문은 실행되지 않는다.\
  예: `UNIQUE` 열에 중복을 넣으면 애플리케이션 코드가 없어도 `INSERT` 가 죽는다.
- **`PRIMARY KEY`** — 그 표의 대표 키. `UNIQUE` 와 `NOT NULL` 을 함께 강제하고 인덱스를 만든다.\
  예: `id int PRIMARY KEY` 라고만 써도 `id` 에 `not null` 이 붙는다.
- **`UNIQUE`** — 값이 겹치지 않게 하는 제약. **`NULL` 은 값이 아니므로 제한하지 않는다.**\
  예: `code varchar(10) UNIQUE` 인 열에 `NULL` 을 100번 넣어도 통과한다.
- **`UNKNOWN`** — 참도 거짓도 아닌 세 번째 진릿값. `NULL` 이 낀 비교의 결과다.\
  예: `NULL = NULL` 은 `TRUE` 가 아니라 `UNKNOWN` 이다.
- **복합 키(composite key)** — 열 여러 개를 묶어 하나의 키로 쓰는 것.\
  예: `UNIQUE (tenant_id, external_id)` 는 두 값의 조합이 겹치지 않게 한다.
- **`NULLS NOT DISTINCT`** — PG 15+ 에서 `UNIQUE` 가 `NULL` 끼리도 「같다」고 보게 하는 선언.\
  예: 이 선언이 있으면 `NULL` 은 그 열에 **하나만** 들어간다.
- **대리키(surrogate key)** — 업무상 의미가 없는, 오직 행을 짚기 위해 만든 키.\
  예: 사번 대신 쓰는 자동 증가 `id`. 업무 규칙이 바뀌어도 값이 안 변한다.
- **자연키(natural key)** — 업무에서 이미 쓰는 값을 그대로 키로 쓰는 것.\
  예: 이메일 주소. 사람이 주소를 바꾸면 키가 바뀐다.
- **`ERROR 1062` / `duplicate key value`** — 중복 삽입을 막을 때 나는 에러.\
  예: MySQL 은 `Duplicate entry '1-2' for key 't43_comp.a'` 처럼 **복합 값을 하이픈으로 이어** 보여 준다.
- **`ERROR 1138`** — MySQL 이 「`NULL` 을 잘못 썼다」고 거절하는 코드.\
  예: `NULL` 이 들어 있는 열에 `ADD PRIMARY KEY` 를 할 때 나온다.

## 더 들어가면

- **InnoDB 는 PK 를 클러스터 인덱스로 쓴다** — 행 데이터 자체가 PK 순서로 저장된다.\
  PK 가 없으면 첫 `NOT NULL UNIQUE` 인덱스를, 그것도 없으면 숨은 행 ID 를 쓴다.\
  **이 서버에서 그 내부 구조를 직접 관찰하지는 못했다**(숨은 열을 보여 주는 통로가 없다) — 매뉴얼의 설명이다.
- **PG 의 `UNIQUE` 제약은 인덱스로 구현되지만, 그 반대는 성립하지 않는다.**\
  `CREATE UNIQUE INDEX` 로 만든 것은 제약이 아니다 — 카탈로그가 다르다(46번에 출력이 있다).
- **`NULL` 이 여럿 허용되는 성질을 역이용하는 설계**가 있다 — 「소프트 삭제된 행은 `code` 를 `NULL` 로」.\
  살아 있는 행만 유일하게 만들 수 있다. PG 라면 **부분 유니크 인덱스**가 더 정직한 표현이다(46번).
