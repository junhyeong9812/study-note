# sql/43-기본키·UNIQUE 제약과 NULL — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 이 편이 만든 표(`t43_pk`·`t43_nnd`·`t43_comp`·`t43_comp2`·`t43_addpk`·`t43_un`·`t43_dc`)는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> 문서 근거는 [PG 18 Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) · [MySQL 8.4 CREATE TABLE](https://dev.mysql.com/doc/refman/8.4/en/create-table.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `PRIMARY KEY` 한 단어가 만드는 것 — **`NOT NULL` · 유일성 · 인덱스**

**출력**

```text
--- PG 18.6 ---
CREATE TABLE t43_pk (id int PRIMARY KEY, code varchar(10) UNIQUE, name varchar(10));
\d t43_pk
                      Table "public.t43_pk"
 Column |         Type          | Collation | Nullable | Default 
--------+-----------------------+-----------+----------+---------
 id     | integer               |           | not null | 
 code   | character varying(10) |           |          | 
 name   | character varying(10) |           |          | 
Indexes:
    "t43_pk_pkey" PRIMARY KEY, btree (id)
    "t43_pk_code_key" UNIQUE CONSTRAINT, btree (code)

--- MySQL 8.4.10 ---
SHOW CREATE TABLE t43_pk\G
Create Table: CREATE TABLE `t43_pk` (
  `id` int NOT NULL,
  `code` varchar(10) DEFAULT NULL,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

**왜 그런가**

```text
PRIMARY KEY (id)
   ├─ (1) NOT NULL 을 id 에 붙인다      <- 내가 안 썼는데 양쪽 정의에 박혀 있다
   ├─ (2) 유일성을 강제한다
   └─ (3) 그 강제를 위해 인덱스를 만든다  <- btree (id) / PRIMARY KEY (`id`)
```

★ **`code` 쪽을 같이 보면 대비가 선다.** `UNIQUE` 만 붙은 `code` 는 양쪽 다 **NULL 허용**이다\
(PG 의 `Nullable` 칸이 비었고, MySQL 은 `DEFAULT NULL` 이다).\
**`UNIQUE` 는 NULL 허용을 건드리지 않는다** — 이것이 3번의 출발점이다.

---

### 2. 세 가지 위반의 에러가 다른가 — **`NULL` 거부와 중복 거부는 서로 다른 에러다**

**출력**

```text
### SQL: INSERT INTO t43_pk VALUES (NULL,'B','bob');
--- PG 18.6 ---
ERROR:  null value in column "id" of relation "t43_pk" violates not-null constraint
DETAIL:  Failing row contains (null, B, bob).
--- MySQL 8.4.10 ---
ERROR 1048 (23000) at line 1: Column 'id' cannot be null
```

```text
### SQL: INSERT INTO t43_pk VALUES (1,'C','cho');
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t43_pk_pkey"
DETAIL:  Key (id)=(1) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry '1' for key 't43_pk.PRIMARY'
```

```text
### SQL: INSERT INTO t43_pk VALUES (2,'A','dan');
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t43_pk_code_key"
DETAIL:  Key (code)=(A) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry 'A' for key 't43_pk.code'
```

**왜 그런가**

```text
(a) NULL 위반   : PK 의 "NOT NULL 조각" 이 걸렸다     PG 1048 대응은 not-null constraint
(b) PK 중복     : PK 의 "UNIQUE 조각" 이 걸렸다       제약 이름 t43_pk_pkey / t43_pk.PRIMARY
(c) UNIQUE 중복 : 별개의 UNIQUE 제약이 걸렸다          제약 이름 t43_pk_code_key / t43_pk.code
```

★ **(a) 와 (b) 는 같은 `PRIMARY KEY` 에서 나왔는데 에러가 다르다.**\
PK 를 「하나의 제약」으로 외우면 이 둘을 같은 것으로 착각한다 — **PG 가 말까지 나눠서 한다.**

에러가 알려 주는 것은 **제약 이름**이다. 이름을 직접 주면(11번) 로그에서 바로 원인 스키마를 찾는다.

---

### 3. ★ `UNIQUE` 열에 `NULL` 을 두 번 넣으면 — **두 엔진 다 들어간다**

**출력**

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

**왜 그런가** — 4번이 그 설명이다.

여기서 기억할 실무 결론은 하나다.

```text
"code 는 UNIQUE 니까 중복이 없다"
        ↓
code 가 NULL 인 행은 몇 개든 있을 수 있다
        ↓
"code 로 행을 하나 찾을 수 있다" 는 거짓이 된다
```

---

### 4. ★ 왜 그렇게 되나 — **`NULL = NULL` 이 `UNKNOWN` 이라 중복 판정이 안 선다**

**출력**

```text
### SQL: SELECT NULL = NULL AS eq;
--- PG 18.6 ---
 eq 
----
 
(1 row)
--- MySQL 8.4.10 ---
+------+
| eq   |
+------+
| NULL |
+------+
```

**왜 그런가**

`UNIQUE` 제약이 하는 일은 **「새 값이 기존 값과 같은가?」를 묻고, `TRUE` 면 막는 것**이다.

```text
새 값이 NULL 일 때 던져지는 질문:   NULL = NULL ?
                                        ↓
                                    UNKNOWN
                                        ↓
                            TRUE 가 아니다 -> 막을 근거가 없다 -> 통과
```

[04 NULL 의 3값 논리](../04-null-three-valued-logic/)의 한 줄이 그대로다 — **`NULL` 은 「같은지 물을 수 없는 것**」이다.\
`UNIQUE` 는 「값이 같으면 막는다」이지 **「빈칸이 여럿이면 막는다」가 아니다.**

★ **두 엔진 출력이 같았다는 사실 자체가 근거가 아니다.**\
근거는 3값 논리이고, 위 `SELECT NULL = NULL` 두 줄은 **그 논리가 이 서버들에서도 성립함을 보인 것**이다.\
「여러 엔진에서 같았으니 보장된다」로 읽으면 안 된다([작성법 §2-1 규칙 3](../../../../../../reference/study-note-guide.md)).

---

### 5. ★ 「빈칸도 하나만」 을 원하면 — **PG 15+ 의 `NULLS NOT DISTINCT`. MySQL 은 문법 에러**

**출력**

```text
### SQL: CREATE TABLE t43_nnd (code varchar(10) UNIQUE NULLS NOT DISTINCT);
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'NULLS NOT DISTINCT)' at line 1
```

```text
--- PG 18.6 ---
INSERT INTO t43_nnd VALUES (NULL);
INSERT 0 1

INSERT INTO t43_nnd VALUES (NULL);
ERROR:  duplicate key value violates unique constraint "t43_nnd_code_key"
DETAIL:  Key (code)=(null) already exists.
```

(MySQL 쪽은 표가 안 만들어졌으므로 `INSERT` 가 `ERROR 1146 Table 'study.t43_nnd' doesn't exist` 다.)

**왜 그런가**

`NULLS NOT DISTINCT` 는 「**`NULL` 끼리도 같은 것으로 보라**」는 선언이다.\
`DETAIL` 에 `(code)=(null)` 이 찍힌 것이 증거다 — **엔진이 `NULL` 을 하나의 값처럼 다뤘다.**

```text
기본 (NULLS DISTINCT)          NULLS NOT DISTINCT
NULL 끼리 서로 다르다            NULL 끼리 서로 같다
  -> 몇 개든 들어간다              -> 하나만 들어간다
```

**★ 어느 쪽 출력이 근거인가**

```text
PG 쪽    : CREATE 성공 + 둘째 INSERT 의 에러
           -> "PG 는 NULL 을 하나만 받게 만들 수 있다" 의 근거다

MySQL 쪽 : ERROR 1064 (문법 에러)
           -> "MySQL 에는 이 문법이 없다" 의 근거다
           -> ★ "MySQL 이 NULL 을 몇 개 받나" 의 근거는 못 된다.
              문 자체가 안 섰기 때문이다. 그 근거는 3번의 성공한 INSERT 두 줄이다
```

---

### 6. ★ 복합 `UNIQUE` 에서 한 칸만 `NULL` 이면 — **두 번 다 통과한다**

**출력**

```text
### SQL: INSERT INTO t43_comp VALUES (1,NULL);    (두 번)
--- PG 18.6 ---
INSERT 0 1
INSERT 0 1
--- MySQL 8.4.10 ---
(두 번 다 성공)
```

```text
### SQL: INSERT INTO t43_comp VALUES (1,2);       (두 번째)
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t43_comp_a_b_key"
DETAIL:  Key (a, b)=(1, 2) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry '1-2' for key 't43_comp.a'
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

**왜 그런가**

복합 키의 비교는 「**모든 칸이 같은가**」다. 한 칸이 `UNKNOWN` 이면 결합이 `UNKNOWN` 이 된다.

```text
(1, NULL) 과 (1, NULL) 이 같은가?

   a:  1 = 1         -> TRUE
   b:  NULL = NULL   -> UNKNOWN
   ─────────────────────────────
   합: TRUE AND UNKNOWN = UNKNOWN        <- 04 의 AND 진리표 그대로
        ↓
   TRUE 가 아니다 -> 중복이 아니다 -> 들어간다
```

★ **실무에서 가장 조용한 중복 사고가 여기다.**\
`(tenant_id, external_id)` 에 `UNIQUE` 를 걸어 놓고 `external_id` 가 `NULL` 인 행이 쌓이면\
**제약은 한 번도 안 걸리는데 중복이 생긴다.**

처방 — 복합 `UNIQUE` 를 쓸 때 **구성 열 전부에 `NOT NULL` 을 거는지** 같이 결정한다.

---

### 7. 이미 `NULL` 이 든 열에 PK 를 붙이면 — **두 엔진 다 거부한다**

**출력**

```text
### SQL: ALTER TABLE t43_addpk ADD PRIMARY KEY (id);
--- PG 18.6 ---
ERROR:  column "id" of relation "t43_addpk" contains null values
--- MySQL 8.4.10 ---
ERROR 1138 (22004) at line 1: Invalid use of NULL value
```

행은 그대로 남아 있다.

```text
### SQL: SELECT * FROM t43_addpk;
--- PG 18.6 ---              --- MySQL 8.4.10 ---
 id | v                      +------+------+
----+---                     | id   | v    |
  1 | a                      +------+------+
    | b                      |    1 | a    |
(2 rows)                     | NULL | b    |
                             +------+------+
```

**왜 그런가**

PK 가 되려면 `NOT NULL` 이어야 하는데(1번), **이미 `NULL` 인 행이 있으므로 그 조건을 만들 수 없다.**

★ **「MySQL 은 PK 를 붙이면 `NULL` 을 `0` 으로 바꾼다」는 옛 이야기다.**\
MySQL 8.4.10 은 `ERROR 1138` 로 **거부한다** — 던져서 확인했다.\
처방은 하나 — **먼저 `NULL` 을 채우고(`UPDATE`) 그 다음에 PK 를 붙인다.**

---

### 8. 42번과 무엇이 다른가 — **「지어낼 값이 있느냐」가 갈랐다**

**두 출력을 나란히 놓는다.**

```text
(A) 42번 — 새 열을 추가하면서       (B) 43번 — 이미 있는 열에 PK 를
ALTER TABLE t42_a                    ALTER TABLE t43_addpk
  ADD COLUMN req int NOT NULL;         ADD PRIMARY KEY (id);

--- MySQL 8.4.10 ---                 --- MySQL 8.4.10 ---
(성공. req 가 전부 0 이 됐다)          ERROR 1138 (22004) at line 1:
경고도 없다                             Invalid use of NULL value
```

**왜 그런가**

```text
(A) 새 열이다
    -> 그 열에는 아직 아무 값도 없다
    -> MySQL 은 "타입의 암묵 기본값(int 는 0)" 으로 채울 수 있다고 본다
    -> 조용히 채운다

(B) 이미 있는 열이다
    -> 그 열에는 사용자가 넣은 NULL 이 실제로 들어 있다
    -> 그것을 0 으로 바꾸면 "데이터를 고치는 것" 이다
    -> 거부한다
```

★ **두 경우의 위험도는 반대다.** 막아 주는 (B) 가 안전하고, **통과시키는 (A) 가 사고**다.\
(A) 는 배포가 성공한 것처럼 보이고, **`0` 이 「미지정」인지 「실제 값」인지 구분할 방법이 사라진다.**

---

### 9. PK 를 두 개 — **둘 다 거부. 복합 PK 는 한 줄로 쓴다**

**출력**

```text
### SQL: CREATE TABLE t43_two (a int PRIMARY KEY, b int PRIMARY KEY);
--- PG 18.6 ---
ERROR:  multiple primary keys for table "t43_two" are not allowed
LINE 1: CREATE TABLE t43_two (a int PRIMARY KEY, b int PRIMARY KEY);
                                                       ^
--- MySQL 8.4.10 ---
ERROR 1068 (42000) at line 1: Multiple primary key defined
```

**왜 그런가**

`PRIMARY KEY` 는 「**이 표의 대표 키**」라는 뜻이라 개수가 하나다.\
두 열의 조합으로 행을 짚고 싶으면 **복합 PK 를 하나 선언**한다.

```text
### SQL: CREATE TABLE t43_comp2 (a int, b int, PRIMARY KEY (a,b));
--- PG 18.6 ---
CREATE TABLE
--- MySQL 8.4.10 ---
(성공)
```

「대표 키 말고도 유일해야 하는 열」이 더 있으면 그쪽은 **`UNIQUE` 로** 선언한다 — 개수 제한이 없다.

---

### 10. `NOT NULL UNIQUE` 와 `PRIMARY KEY` — **값의 성질은 같고, 표시가 다르다**

**출력**

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

**같은 것 / 다른 것**

```text
같다   : 값이 겹치지 않는다 · 비어 있지 않다 · 인덱스가 생긴다
다르다 : (1) 표당 개수 — PRIMARY KEY 는 하나, UNIQUE 는 여럿
         (2) "이 표의 대표 키" 라는 선언 — 외래키(44번)가 기본으로 가리키는 대상
         (3) 카탈로그 표시 — PG 는 PRIMARY KEY / UNIQUE CONSTRAINT 로 나눠 적는다
```

1번의 `\d t43_pk` 와 여기 `\d t43_un` 을 나란히 읽으면 (3) 이 보인다.\
`Nullable` 칸은 **둘 다 `not null`** 이다 — 값의 성질이 같다는 증거다.

---

### 11. 제약 이름은 누가 짓나 — **안 주면 엔진이 짓고, 엔진마다 규칙이 다르다**

**출력에서 읽어 낸 이름들**

```text
내가 쓴 것                          PG 가 지은 이름        MySQL 이 지은 이름
─────────────────────────────       ──────────────────     ──────────────────
id int PRIMARY KEY                  t43_pk_pkey            PRIMARY
code varchar(10) UNIQUE             t43_pk_code_key        code        <- 열 이름 그대로
UNIQUE (a,b)                        t43_comp_a_b_key       a           <- 첫 열 이름
```

에러에 그대로 박힌다.

```text
PG    : violates unique constraint "t43_comp_a_b_key"
MySQL : Duplicate entry '1-2' for key 't43_comp.a'
```

**무엇이 문제인가**

```text
MySQL 의 't43_comp.a' 를 보고
  -> "a 열이 중복이다" 로 읽기 쉽다
  -> 실제로는 (a,b) 복합 제약이다. 'a' 는 그 제약의 이름일 뿐이다
```

★ **이름이 열 이름과 같아져 에러가 오독된다.** 처방은 **이름을 직접 주는 것**이다.

```sql
CREATE TABLE t (a int, b int, CONSTRAINT t_tenant_ext_uq UNIQUE (a,b));
```

떼어낼 때도 그 이름을 쓴다. **`DROP CONSTRAINT` 는 두 엔진 다 받는다** — 던져서 확인했다.

```text
### SQL: CREATE TABLE t43_dc (a int, CONSTRAINT t43_dc_a_uq UNIQUE (a));
        ALTER TABLE t43_dc DROP CONSTRAINT t43_dc_a_uq;
--- PG 18.6 ---
CREATE TABLE
ALTER TABLE
--- MySQL 8.4.10 ---
(둘 다 성공)

--- MySQL 8.4.10 ---
SHOW CREATE TABLE t43_dc\G
Create Table: CREATE TABLE `t43_dc` (
  `a` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

---

### 12. 그래서 어떻게 설계하나 — **「하나만」의 세 가지 뜻을 먼저 가른다**

```text
"이 열은 하나만 있어야 한다" 가 무엇을 뜻하나?

(1) 값이 있는 행끼리 안 겹치면 된다. 빈칸은 여럿이어도 좋다
        -> UNIQUE 만                              양쪽 다 그대로 된다 (3번)

(2) 빈칸도 하나만 허용한다
        -> PG   : UNIQUE ... NULLS NOT DISTINCT   (5번)
        -> MySQL: 이 문법이 없다. NOT NULL 을 걸고 "없음" 을 나타낼 값(빈 문자열 등)을 정하거나
                  애플리케이션에서 막는다

(3) 빈칸 자체를 허용하지 않는다
        -> NOT NULL UNIQUE                        양쪽 다 (10번)
        -> 그리고 이 열이 표의 대표 키면 PRIMARY KEY
```

**복합 키에는 한 칸이 더 있다.**

```text
UNIQUE (a, b) 를 쓸 때
  -> a, b 중 NULL 이 들어갈 수 있는 것이 있나?
     있다면 그 조합은 제약이 안 걸린다 (6번)
  -> 그래도 괜찮은지 결정하거나, 구성 열에 NOT NULL 을 건다
```

**PG 라면 네 번째 선택지가 있다 — 부분 유니크 인덱스.**

```sql
-- "삭제되지 않은 행끼리만 code 가 유일하다"
CREATE UNIQUE INDEX t_code_live_uq ON t (code) WHERE deleted_at IS NULL;
```

이 문법과 MySQL 에서의 거절 출력은 [46 인덱스 정의](../46-index-definition-composite-partial-expression/)에 있다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `PRIMARY KEY`·`UNIQUE` 정의 조회 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\d` · `SHOW CREATE TABLE` |
| PK 에 `NULL` (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러가 근거다** |
| PK 중복 · `UNIQUE` 중복 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 1062 · duplicate key** |
| ★ `UNIQUE` 열에 `NULL` 둘 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **둘 다 성공 — 이것이 근거다** |
| 넣은 뒤 `SELECT` 로 확인 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 3행이 남았다 |
| `SELECT NULL = NULL` (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 04번의 결론을 이 서버에서 재확인 |
| `NULLS NOT DISTINCT` (5번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **PG 성공 / MySQL `ERROR 1064`** |
| 복합 `UNIQUE` 4종 (6번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | `(1,NULL)` 2회 · `(1,2)` 2회 |
| `ADD PRIMARY KEY` 에 `NULL` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL `ERROR 1138` 이 근거다** |
| PK 두 개 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 복합 PK 선언 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 성공 |
| `NOT NULL UNIQUE` 정의 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **양쪽 `not null` 이 근거다** |
| `DROP CONSTRAINT` (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL 도 된다 — 던져서 확인** |

**구현 의존 항목** — 2·11번(**에러 코드·문구·자동 생성 제약 이름**).\
`t43_comp.a` 같은 이름 규칙과 `'1-2'` 같은 복합 값 표기는 MySQL 의 구현 세부다. 파싱해 쓰지 않는다.

**언어 보장 항목** — 1·3·4·6·7·9·10번.\
`PRIMARY KEY` 가 `NOT NULL` 을 함의한다는 것, `UNIQUE` 가 `NULL` 을 제한하지 않는다는 것,\
복합 키 비교가 3값 논리를 따른다는 것은 두 매뉴얼의 제약 페이지가 정한 것이다.

**버전을 적은 자리** — `NULLS NOT DISTINCT` 는 PostgreSQL 15 부터다.\
**버전을 못 적은 자리** — 「MySQL 이 옛날에는 `ADD PRIMARY KEY` 때 `NULL` 을 `0` 으로 바꿨다」는 말이 있으나,\
**이 머신에 옛 MySQL 컨테이너가 없어 직접 던져 보지 못했다.** 8.4.10 이 거부한다는 것만 실었다.

**DB 잔재** — 없다. `t43_pk`·`t43_nnd`·`t43_comp`·`t43_comp2`·`t43_addpk`·`t43_un`·`t43_dc` 는 전부 삭제했고,\
`emp`·`dept` 는 **읽지도 쓰지도 않았다.**\
두 엔진의 최종 표 목록 출력은 [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)의 「실행 검증」에 있다.
