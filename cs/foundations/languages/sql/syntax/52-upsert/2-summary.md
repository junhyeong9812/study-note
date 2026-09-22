# sql/52-UPSERT (ON CONFLICT · ON DUPLICATE KEY UPDATE) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · INSERT](https://www.postgresql.org/docs/18/sql-insert.html) · [MySQL 8.4 · INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — MySQL 의 행 별칭 문법(`VALUES (...) AS new`)은 **8.0.19 부터**다([8.0.19 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html)). 구식 `VALUES()` 함수는 8.4.10 서버가 직접 deprecated 경고를 낸다(아래 출력).\
> **선행** — [04 NULL 의 3값 논리](../04-null-three-valued-logic/)(제약과 `NULL`) · [목록의 **43번 주제**](../43-primary-key-unique-and-null/)(기본키·UNIQUE) · 49번(INSERT).

## 한눈에 — 쉽게 말하면

**upsert = 「있으면 고치고 없으면 넣어라」를 한 문장으로 시키는 것.**

- 두 문으로 나눠 쓰면 이렇게 된다.\
  ① 있나 본다 → ② 있으면 `UPDATE`, 없으면 `INSERT`.
- 그런데 ①과 ② **사이에** 다른 접속이 끼어들면?\
  둘 다 「없다」를 보고 둘 다 `INSERT` 를 한다 → 하나는 중복 키 에러로 죽는다.
- upsert 는 그 틈을 없앤다. **판정과 처리가 한 문 안에서 원자적으로** 일어난다.

```text
두 문으로 나눠 쓰면                  한 문 upsert
─────────────────                    ─────────────
접속 A: SELECT -> 없다               접속 A: INSERT ... ON CONFLICT ...
접속 B: SELECT -> 없다                       -> 엔진이 제약 위반을 잡아
접속 A: INSERT -> 성공                          그 자리에서 UPDATE 로 전환
접속 B: INSERT -> 중복 키 에러 💥     접속 B: 같은 문 -> 갱신으로 처리
```

그런데 **어느 제약을 「충돌」로 볼 것인가**에서 두 엔진이 갈린다.

```text
PostgreSQL                          MySQL
"이 제약에서 충돌하면"               "아무 유니크 키에서든 충돌하면"
 ON CONFLICT (id) DO UPDATE ...      ON DUPLICATE KEY UPDATE ...
       ^^^^                                  ^^^^^^^^^^^^^
    대상을 지목한다                      대상을 고를 수 없다
```

이 한 칸 차이가 **같은 문장에 서로 다른 답을 내게** 만든다 — 한쪽은 에러, 한쪽은 조용한 0행이다(아래 2번).

> **upsert** — update + insert 의 합성어. 「있으면 갱신, 없으면 삽입」을 한 문으로 처리하는 것.\
> 예: 일별 집계 행을 매번 다시 계산해 덮어쓸 때.

> **유니크 제약(unique constraint)** — 어떤 열(들)의 값이 표 안에서 중복될 수 없다는 규칙. 기본키도 그중 하나다.\
> 예: `dept.id` 는 기본키, `dept.name` 은 `UNIQUE` — 이 표에는 유니크 제약이 **둘** 있다.

## 이 주제가 답하려는 질문

1. **무엇이 「충돌」을 판정하나?** — 충돌 대상을 **지목할 수 있는** 엔진과 **고를 수 없는** 엔진.
2. **문이 성공했다는 것이 「내가 넣으려던 행이 생겼다」는 뜻인가?** — 영향 행 수 1/2/0 과 `RETURNING`.
3. **덮어쓰기가 항상 옳지는 않을 때는 어떻게 하나?** — 한 문 안에 같은 키가 둘일 때와, 조건부 갱신.

## 예시 데이터 — 이 묶음이 공유하는 것

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

**이 주제는 `dept` 만 쓴다.** 그 표에 유니크 제약이 둘이라는 점이 핵심이다.

```sql
CREATE TABLE dept (
  id   int PRIMARY KEY,        -- 유니크 제약 1
  name text UNIQUE NOT NULL    -- 유니크 제약 2
);
```

아래 모든 실험은 **`BEGIN`/`ROLLBACK`(MySQL 은 `START TRANSACTION`/`ROLLBACK`) 으로 감싸** 돌렸다. 그래서 기준 상태는 매번 같다.

## 동작 방식

### 1. 충돌이 일어나면 무슨 일이 생기나

**언제 쓰나** — upsert 를 처음 읽을 때. 「무엇이 충돌을 판정하는가」가 이 문법의 전부다.

```text
(전) dept                          INSERT (30, 'people') 을 시도
+----+-------+
| 10 | sales |                     ① 엔진이 행을 넣어 본다
| 20 | dev   |                     ② id=30 이 이미 있다 -> PRIMARY KEY 위반
| 30 | hr    |  <- id 30 이 있다    ③ 보통은 여기서 에러로 죽는다
+----+-------+                     ④ upsert 절이 있으면: 죽는 대신 UPDATE 로 전환
   ↓
(후) dept
+----+--------+
| 10 | sales  |
| 20 | dev    |
| 30 | people |  <- 갱신됐다
+----+--------+
```

**PG — 충돌 대상을 `(id)` 로 지목한다.**

```text
BEGIN;
INSERT INTO dept VALUES (30, 'people') ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
INSERT 0 1
SELECT * FROM dept ORDER BY id;
 id |  name
----+--------
 10 | sales
 20 | dev
 30 | people
(3 rows)
ROLLBACK;
```

**MySQL — 대상을 안 적는다.**

```text
START TRANSACTION;
INSERT INTO dept VALUES (30, 'people') AS new ON DUPLICATE KEY UPDATE name = new.name;
SELECT ROW_COUNT() AS affected;
+----------+
| affected |
+----------+
|        2 |        <- 갱신은 2로 센다. 3번 참조
+----------+
SELECT * FROM dept ORDER BY id;
+----+--------+
| id | name   |
+----+--------+
| 10 | sales  |
| 20 | dev    |
| 30 | people |
+----+--------+
ROLLBACK;
```

그림 해설 — 여기까지는 두 엔진의 결과가 같다. **차이는 유니크 제약이 둘 이상일 때 드러난다.**\
대가 — upsert 는 「제약 위반」을 정상 흐름으로 바꾸는 문법이다. 그래서 **제약이 무엇인지 모르면 무엇이 일어날지도 모른다.**

> **`EXCLUDED`** — PG 에서 「넣으려다 막힌 그 행」을 가리키는 이름.\
> 예: `SET name = EXCLUDED.name` 은 「원래 넣으려던 이름으로 갱신하라」.

> **행 별칭(`AS new`)** — MySQL 에서 같은 역할을 하는 이름. 내가 직접 붙인다(MySQL 8.0.19+).\
> 예: `VALUES (30,'people') AS new ... SET name = new.name`.

### 2. ★ 같은 문장, 다른 답 — 충돌 대상을 고를 수 있는가

**언제 쓰나** — 표에 유니크 제약이 둘 이상일 때. **이 주제에서 가장 비싼 차이다.**

같은 문장을 던진다. `id=40` 은 **새 값**이고, `name='hr'` 은 **이미 있다**.

```text
INSERT INTO dept VALUES (40, 'hr') ... 충돌 처리 ...

(전) dept
+----+-------+
| 10 | sales |
| 20 | dev   |
| 30 | hr    |   <- name='hr' 이 여기 있다. id 는 30 이다
+----+-------+
```

```text
(A) PostgreSQL — ON CONFLICT (id)          (B) MySQL — ON DUPLICATE KEY
BEGIN;                                      START TRANSACTION;
INSERT INTO dept VALUES (40, 'hr')          INSERT INTO dept VALUES (40, 'hr') AS new
  ON CONFLICT (id)                            ON DUPLICATE KEY UPDATE name = new.name;
  DO UPDATE SET name = EXCLUDED.name;        SELECT ROW_COUNT() AS affected;
ROLLBACK;                                    SELECT * FROM dept ORDER BY id;
                                             ROLLBACK;
--- 실제 출력 ---                            --- 실제 출력 ---
ERROR:  duplicate key value violates         +----------+
  unique constraint "dept_name_key"          | affected |
DETAIL:  Key (name)=(hr) already exists.     +----------+
                                             |        0 |
                                             +----------+
                                             +----+-------+
                                             | id | name  |
                                             +----+-------+
                                             | 10 | sales |
                                             | 20 | dev   |
                                             | 30 | hr    |
                                             +----+-------+
   -> 문이 실패한다. 시끄럽다                    -> 아무 일도 안 일어났다. 조용하다
   -> "id 로만 충돌을 보랬는데                   -> name 제약에서 충돌을 잡아
       name 에서 터졌다"                            id=30 행의 name 을 'hr' -> 'hr' 로
                                                     갱신했다. 바뀐 게 없어 0행
```

두 그림의 결론 — **`id=40` 인 행은 어느 쪽에도 생기지 않았다.**\
PG 는 그 사실을 **에러로 알려 주고**, MySQL 은 **정상 종료를 알려 준다.**\
애플리케이션이 「성공」만 보고 `id=40` 을 존재한다고 믿으면 그때부터 어긋난다.

대가 — MySQL 의 「아무 유니크 키든」은 문법을 짧게 만들지만, **어느 제약이 걸렸는지 문장에 안 적혀 있다.** 제약을 하나 추가하는 순간 기존 upsert 의 의미가 조용히 바뀐다.

**PG 에서 충돌 대상을 `name` 으로 바꾸면** 이번에는 통과한다 — 그리고 `id` 가 40 으로 바뀐다.

```text
BEGIN;
INSERT INTO dept VALUES (40, 'hr') ON CONFLICT (name) DO UPDATE SET id = EXCLUDED.id;
INSERT 0 1
SELECT * FROM dept ORDER BY id;
 id | name
----+-------
 10 | sales
 20 | dev
 40 | hr      <- id 가 30 -> 40 으로 바뀌었다
(3 rows)
ROLLBACK;
```

**같은 입력 `(40, 'hr')` 이 지목한 제약에 따라 셋으로 갈린다** — 에러 / 무변화 / `id` 갱신.\
그래서 PG 에서 충돌 대상은 **장식이 아니라 의미의 일부**다.

### 3. 영향 행 수 — MySQL 의 1 / 2 / 0

**언제 쓰나** — 애플리케이션이 「몇 행 바뀌었나」로 분기할 때. 숫자가 직관과 다르다.

```text
순수 삽입    -> 1
실제 갱신    -> 2     <- 삭제 1 + 삽입 1 로 세기 때문. 실제 행은 하나다
값이 같음    -> 0     <- 갱신 대상은 찾았지만 바뀐 게 없다
```

세 경우를 한 트랜잭션에서 연달아 돌린 실제 출력이다.

```text
START TRANSACTION;
INSERT INTO dept VALUES (40, 'legal')  AS new ON DUPLICATE KEY UPDATE name = new.name;
SELECT ROW_COUNT() AS insert_case;     +-------------+
                                       | insert_case |
                                       |           1 |
INSERT INTO dept VALUES (40, 'legal2') AS new ON DUPLICATE KEY UPDATE name = new.name;
SELECT ROW_COUNT() AS update_case;     +-------------+
                                       | update_case |
                                       |           2 |
INSERT INTO dept VALUES (40, 'legal2') AS new ON DUPLICATE KEY UPDATE name = new.name;
SELECT ROW_COUNT() AS nochange_case;   +---------------+
                                       | nochange_case |
                                       |             0 |
ROLLBACK;
```

그림 해설 — **`0` 은 「실패」가 아니다.** 같은 값을 다시 쓴 것뿐이다. 그런데 「0행이면 실패」로 짠 코드는 여기서 오판한다.\
대가 — 이 숫자만으로는 **「삽입했나 갱신했나」를 구분할 수 없다.** 0 은 무변화 갱신이고, 1은 삽입, 2는 갱신이다 — 세 값을 다 알아야 읽힌다.

**PG 는 이 문제를 `RETURNING` 으로 푼다.**

```text
BEGIN;
INSERT INTO dept VALUES (30,'people'), (40,'legal')
  ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
  RETURNING id, name, (xmax = 0) AS inserted;
 id |  name  | inserted
----+--------+----------
 30 | people | f          <- 갱신된 행
 40 | legal  | t          <- 삽입된 행
(2 rows)
INSERT 0 2
ROLLBACK;
```

`RETURNING` 자체가 방언이다 — **MySQL 8.4.10 에는 없다.**

```text
### SQL: INSERT INTO dept VALUES (50,'tmp') RETURNING id, name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       ERROR 1064 (42000) at line 1: You have an error in your SQL
----+------                        syntax; ... right syntax to use near 'RETURNING id, name' at line 1
 50 | tmp
(1 row)
INSERT 0 1
```

(`xmax = 0` 은 PG 의 내부 열을 이용한 관용구다 — 「이 행은 이 문에서 새로 만들어졌다」를 뜻한다. 문서화된 계약이 아니므로 참고로만 쓴다.)

### 4. 「없으면 넣고 있으면 그냥 둬라」 — DO NOTHING

**언제 쓰나** — 중복은 무시하고 넘어가고 싶을 때. 로그 적재·멱등 재시도에서 흔하다.

PG 는 `DO NOTHING` 에 한해 **대상을 안 적어도 된다.**

```text
BEGIN;
INSERT INTO dept VALUES (40, 'hr') ON CONFLICT DO NOTHING;
INSERT 0 0                    <- 0행. 아무것도 안 넣었다
SELECT * FROM dept ORDER BY id;
 id | name
----+-------
 10 | sales
 20 | dev
 30 | hr
(3 rows)
ROLLBACK;
```

2번에서 **에러를 냈던 그 문장**이, `DO NOTHING` 으로 바꾸니 조용히 넘어간다.\
대상을 안 적으면 **어느 유니크 제약이든** 삼키기 때문이다 — 이때만은 MySQL 과 같은 동작이 된다.

MySQL 쪽 대응물은 `INSERT IGNORE` 다. 다만 **경고를 남긴다.**

```text
START TRANSACTION;
INSERT IGNORE INTO dept VALUES (30, 'people');
SHOW WARNINGS;
+---------+------+---------------------------------------------+
| Level   | Code | Message                                     |
+---------+------+---------------------------------------------+
| Warning | 1062 | Duplicate entry '30' for key 'dept.PRIMARY' |
+---------+------+---------------------------------------------+
SELECT * FROM dept ORDER BY id;
+----+-------+
| id | name  |
+----+-------+
| 10 | sales |
| 20 | dev   |
| 30 | hr    |
+----+-------+
ROLLBACK;
```

그림 해설 — **경고가 어느 키에서 걸렸는지 알려 준다**(`dept.PRIMARY`). 2번의 조용한 0행보다 낫다.\
대가 — `INSERT IGNORE` 는 중복만이 아니라 **다른 에러도 경고로 낮춘다.** 타입 변환 실패 같은 것까지 삼키므로 범위가 넓다. 중복만 무시하려면 `ON DUPLICATE KEY UPDATE 아무열 = 아무열` 관용구가 더 좁다.

### 5. 한 문 안에서 같은 행을 두 번 건드리면

**언제 쓰나** — 여러 행을 한 문으로 upsert 할 때. 입력에 중복 키가 섞이는 배치 적재에서 난다.

```text
INSERT INTO dept VALUES (40,'legal'), (40,'legal2') ... 충돌 처리 ...
                          ^^            ^^
                      같은 키가 한 문 안에 둘
```

```text
(A) PostgreSQL                          (B) MySQL
BEGIN;                                   START TRANSACTION;
INSERT INTO dept VALUES                  INSERT INTO dept VALUES
  (40,'legal'), (40,'legal2')              (40,'legal'), (40,'legal2') AS new
  ON CONFLICT (id)                         ON DUPLICATE KEY UPDATE name = new.name;
  DO UPDATE SET name = EXCLUDED.name;     SELECT * FROM dept ORDER BY id;
ROLLBACK;                                ROLLBACK;
--- 실제 출력 ---                        --- 실제 출력 ---
ERROR:  ON CONFLICT DO UPDATE command    +----+--------+
  cannot affect row a second time        | id | name   |
HINT:  Ensure that no rows proposed      +----+--------+
  for insertion within the same command  | 10 | sales  |
  have duplicate constrained values.     | 20 | dev    |
                                         | 30 | hr     |
                                         | 40 | legal2 |  <- 뒤엣것이 이겼다
                                         +----+--------+
   -> 거부한다                              -> 마지막 값을 조용히 채택한다
```

두 그림의 결론 — **PG 는 「어느 쪽이 맞는지 나는 모른다」고 하고, MySQL 은 「마지막 것」으로 정한다.**\
어느 쪽도 틀린 설계는 아니지만, **입력에 중복이 섞였다는 사실은 PG 에서만 드러난다.**

대가 — MySQL 에서는 중복 입력이 **에러 없이** 흡수되므로, 상류의 중복 버그가 오래 살아남는다.\
배치 적재라면 upsert 전에 입력을 **키 기준으로 한 번 접는**(dedup) 편이 양쪽 모두에서 안전하다.

### 6. 조건부 갱신 — 「더 나은 값일 때만 덮어써라」

**언제 쓰나** — 덮어쓰기가 항상 옳지 않을 때. 늦게 도착한 오래된 데이터로 최신 값을 지우는 사고를 막는다.

PG 는 `DO UPDATE` 에 `WHERE` 를 붙일 수 있다.

```text
BEGIN;
INSERT INTO dept VALUES (30,'aaa')
  ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
  WHERE dept.name < EXCLUDED.name;      -- 'hr' < 'aaa' 는 거짓
INSERT 0 0                              <- 갱신하지 않았다
SELECT * FROM dept ORDER BY id;
 id | name
----+-------
 10 | sales
 20 | dev
 30 | hr        <- 'aaa' 로 안 바뀌었다
(3 rows)
ROLLBACK;
```

그림 해설 — `WHERE` 의 `dept.name` 은 **기존 행**, `EXCLUDED.name` 은 **넣으려던 행**이다. 두 이름이 있으니 비교가 된다.\
대가 — 조건이 거짓이면 `0` 행이다. 3번의 「값이 같아서 0」과 구분이 안 되므로, 구분이 필요하면 `RETURNING` 을 같이 쓴다.

MySQL 에는 `WHERE` 절이 없다. 대신 **식으로** 같은 일을 한다. 두 경우를 이어 돌린 실제 출력이다.

```text
START TRANSACTION;
INSERT INTO dept VALUES (30,'aaa') AS new
  ON DUPLICATE KEY UPDATE name = IF(dept.name < new.name, new.name, dept.name);
SELECT * FROM dept ORDER BY id;
+----+-------+
| id | name  |
+----+-------+
| 10 | sales |
| 20 | dev   |
| 30 | hr    |   <- 'hr' < 'aaa' 가 거짓이라 안 바뀌었다
+----+-------+

INSERT INTO dept VALUES (30,'zzz') AS new
  ON DUPLICATE KEY UPDATE name = IF(dept.name < new.name, new.name, dept.name);
SELECT * FROM dept ORDER BY id;
+----+-------+
| id | name  |
+----+-------+
| 10 | sales |
| 20 | dev   |
| 30 | zzz   |   <- 'hr' < 'zzz' 가 참이라 바뀌었다
+----+-------+
ROLLBACK;
```

수치라면 `GREATEST(dept.cnt, new.cnt)` 형태가 흔하다.\
**차이는 「조건이 어디 있나」다** — PG 는 갱신할지 말지를 `WHERE` 가 정하고, MySQL 은 **갱신은 늘 하되 값이 같아지도록** 식으로 접는다.

## 문법 — 형태와 규칙

```sql
-- PostgreSQL
INSERT INTO t (...) VALUES (...)
  ON CONFLICT (열목록)                 -- 또는 ON CONSTRAINT 제약이름
  DO NOTHING;
INSERT INTO t (...) VALUES (...)
  ON CONFLICT (열목록)
  DO UPDATE SET c = EXCLUDED.c [, ...]
  [WHERE <조건>]                       -- 기존 행은 t.c, 새 행은 EXCLUDED.c
  [RETURNING ...];

-- MySQL (8.0.19+ 행 별칭 형태)
INSERT INTO t (...) VALUES (...) AS new
  ON DUPLICATE KEY UPDATE c = new.c [, ...];
INSERT IGNORE INTO t (...) VALUES (...);   -- DO NOTHING 에 대응
```

규칙 다섯.

1. **PG 의 `DO UPDATE` 는 충돌 대상이 필수다.** `DO NOTHING` 만 생략할 수 있다.
2. **충돌 대상은 유니크 제약(또는 유니크 인덱스)이 있는 열이어야 한다.** 아무 열이나 못 쓴다.
3. **MySQL 은 대상을 고를 수 없다.** 그 행이 걸리는 **아무 유니크 키**에서든 갱신으로 전환된다.
4. **MySQL 의 영향 행 수는 삽입 1 / 갱신 2 / 무변화 0** 이다. 「1이면 성공」이 아니다.
5. **`RETURNING` 은 PG 전용이다.** MySQL 8.4.10 은 문법 오류를 낸다.

PG 는 대상을 안 적은 `DO UPDATE` 를 거부한다.

```text
BEGIN;
INSERT INTO dept VALUES (30,'people') ON CONFLICT DO UPDATE SET name = EXCLUDED.name;
ERROR:  ON CONFLICT DO UPDATE requires inference specification or constraint name
LINE 1: INSERT INTO dept VALUES (30,'people') ON CONFLICT DO UPDATE ...
                                              ^
HINT:  For example, ON CONFLICT (column_name).
ROLLBACK;
```

유니크 제약이 없는 열을 대상으로 적어도 거부한다.

```text
BEGIN;
INSERT INTO emp VALUES (5,'eve',10,200) ON CONFLICT (dept_id) DO NOTHING;
ERROR:  there is no unique or exclusion constraint matching the ON CONFLICT specification
ROLLBACK;
```

MySQL 쪽에서 `ON CONFLICT` 문법을 흉내 내려 하면 문법 오류다.

```text
### SQL: INSERT INTO dept VALUES (30,'people') ON CONFLICT (id) DO UPDATE SET name='people';
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near 'CONFLICT (id) DO UPDATE SET name='people'' at line 1
```

#### 구식 `VALUES()` 형태 — 서버가 직접 경고한다

MySQL 8.0.19 이전에는 「넣으려던 행」을 `VALUES(열)` 함수로 가리켰다. 8.4.10 에서도 돌긴 하지만 경고가 붙는다.

```text
START TRANSACTION;
INSERT INTO dept VALUES (30, 'people') ON DUPLICATE KEY UPDATE name = VALUES(name);
SHOW WARNINGS;
+---------+------+-------------------------------------------------------------------------+
| Level   | Code | Message                                                                 |
+---------+------+-------------------------------------------------------------------------+
| Warning | 1287 | 'VALUES function' is deprecated and will be removed in a future         |
|         |      | release. Please use an alias (INSERT INTO ... VALUES (...) AS alias)    |
|         |      | and replace VALUES(col) in the ON DUPLICATE KEY UPDATE clause with     |
|         |      | alias.col instead                                                       |
+---------+------+-------------------------------------------------------------------------+
ROLLBACK;
```

(줄바꿈만 폭에 맞게 접었고, 문구는 서버가 낸 그대로다.)\
**새로 쓰는 코드는 `AS new` 별칭 형태를 쓴다.**

#### 방언 요약

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 문법 | `ON CONFLICT <대상> DO NOTHING \| DO UPDATE` | `ON DUPLICATE KEY UPDATE` |
| 충돌 대상 지목 | **가능**(`DO UPDATE` 는 필수) | **불가능** — 아무 유니크 키든 |
| 「넣으려던 행」의 이름 | `EXCLUDED`(예약됨) | `AS new` 별칭(8.0.19+) / 구식 `VALUES()`(deprecated) |
| 갱신 조건 | `DO UPDATE ... WHERE` | 없음 — `IF()`·`GREATEST()` 식으로 |
| 아무것도 안 하기 | `ON CONFLICT DO NOTHING` | `INSERT IGNORE` |
| 영향 행 수 | 삽입/갱신 모두 1 | 삽입 1 · 갱신 2 · 무변화 0 |
| 삽입인지 갱신인지 알기 | `RETURNING` 으로 가능 | 영향 행 수로 추정만 |
| 한 문 안 같은 키 중복 | **에러** | 마지막 값 채택 |

## 어디서 틀리나

- **유니크 제약이 둘 이상인데 MySQL 에서 upsert 를 쓴다.**\
  의도하지 않은 제약에서 충돌이 잡히면 **엉뚱한 행이 갱신되거나 아무 일도 안 일어난다.** 2번의 `(40,'hr')` 이 그 예다 — 에러도 경고도 없다.
- **영향 행 수 `0` 을 실패로 읽는다.**\
  MySQL 에서 0은 「값이 같아 바뀐 게 없음」이다. PG 에서도 `DO NOTHING` 과 `WHERE` 거짓일 때 0행이다.
- **영향 행 수 `2` 를 「두 행이 바뀌었다」로 읽는다.**\
  MySQL 에서 갱신 한 건은 2로 센다. 실제 행은 하나다.
- **`INSERT IGNORE` 로 중복만 무시한다고 믿는다.**\
  중복 외의 에러도 경고로 낮춘다. 범위가 생각보다 넓다.
- **배치 입력에 같은 키가 섞인 채로 던진다.**\
  PG 는 `cannot affect row a second time` 으로 거부하고, MySQL 은 마지막 값을 조용히 채택한다. upsert 전에 입력을 접는다.
- **upsert 가 잠금을 안 만든다고 생각한다.**\
  충돌을 잡으려면 행을 잡아야 한다. 같은 키에 경쟁이 몰리면 대기·교착이 생긴다([목록의 **57번 주제**](../57-explicit-locking-and-deadlock/)).
- **`ON CONFLICT` 대상 열에 유니크 제약이 없다.**\
  PG 는 `there is no unique or exclusion constraint matching...` 으로 거부한다.\
  **부분 유니크 인덱스를 대상으로 쓸 때는 인덱스의 `WHERE` 조건까지 문에 적어야** 한다 — 안 적으면 같은 에러가 난다.

```text
CREATE UNIQUE INDEX t52_uq ON t52 (id) WHERE active;

-- 조건을 안 적으면
INSERT INTO t52 VALUES (1,'b',true) ON CONFLICT (id) DO UPDATE SET tag = EXCLUDED.tag;
ERROR:  there is no unique or exclusion constraint matching the ON CONFLICT specification

-- 인덱스의 WHERE 까지 적으면
INSERT INTO t52 VALUES (1,'b',true) ON CONFLICT (id) WHERE active DO UPDATE SET tag = EXCLUDED.tag;
INSERT 0 1
```
- **`RETURNING` 을 쓴 코드를 MySQL 로 옮긴다.**\
  `ERROR 1064` 문법 오류다.

## 구현 세부사항 대 언어 보장

upsert 는 **엔진이 자기 문서로 약속한 것이 유난히 많고**, 그만큼 층이 잘 엉킨다.

| 항목 | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 충돌 = **유니크 제약·유니크 인덱스** 위반 | **정의** | 언어 — 두 문서가 같은 말을 한다(아래) |
| PG 의 `DO UPDATE` 는 충돌 대상이 **필수** | **방언** | 엔진 — PG 문서가 *"must be provided"* 로 못 박는다 |
| PG 가 한 문 안 같은 키를 **거부** | **방언** | 엔진 — PG 문서가 거부를 약속한다(아래). **관찰이 아니다** |
| MySQL 의 영향 행 수 **1 / 2 / 0** | **방언** | 엔진 — MySQL 문서가 세는 방식을 그대로 적는다(아래). **PG 엔 그 현상 자체가 없다** |
| MySQL 이 **아무 유니크 키에서든** 잡는 것 | **방언** | 엔진 — 문서가 적고, **매뉴얼이 직접 피하라고 권고**한다(아래) |
| `RETURNING` 의 유무 | **방언** | 엔진 — PG 문서의 절 / MySQL 은 `ERROR 1064` |
| ★ **`xmax = 0` 으로 삽입/갱신 가리기** | **구현** | **아무도 보장 안 한다** — 문서화된 계약이 아닌 내부 열(아래) |
| ★ **2번에서 MySQL 이 어느 제약을 잡았는지** | **관찰(그것도 되짚은 것)** | 서버가 말해 주지 않았다(아래) |
| 제약 이름 `dept_name_key`·`dept.PRIMARY` | 구현 세부 | 엔진이 붙인 이름 — 스키마가 바뀌면 바뀐다 |
| 에러·경고 번호(`1062`·`1064`·`1287`) | 구현 세부 | 엔진 — **문자열로 분기하지 마라** |

**두 문서가 같은 말을 하는 자리** — 「무엇이 충돌인가」의 밑바닥 하나뿐이다.\
MySQL *"a row to be inserted would cause a duplicate value in a `UNIQUE` index or `PRIMARY KEY`"* · PG *"only `NOT DEFERRABLE` constraints and unique indexes are supported as arbiters"*.\
**그 위의 모든 것 — 대상을 고를 수 있나 · 몇으로 세나 · 무엇을 돌려주나 — 은 엔진이 각자 정했다.**

**엔진이 자기 문서로 약속한 것 — 다른 엔진엔 해당 없다.**

- PG, 충돌 대상 — *"For `ON CONFLICT DO UPDATE`, a `conflict_target` must be provided."* 그리고 유추 규칙 *"All `table_name` unique indexes that, without regard to order, contain exactly the `conflict_target`-specified columns/expressions are inferred (chosen) as arbiter indexes."* → **지목한 인덱스만 중재자가 된다.**
- PG, 한 문 안 중복 — *"the command will not be allowed to affect any single existing row more than once; a cardinality violation error will be raised when this situation arises."* 본문 5번의 거부는 **문서가 약속한 거부**다.
- MySQL, 영향 행 수 — *"the affected-rows value per row is 1 if the row is inserted as a new row, 2 if an existing row is updated, and 0 if an existing row is set to its current values."* **1/2/0 은 이 엔진에서 보장이다** — 「이 판에 그랬다」가 아니다. 다만 그 숫자로 **삽입인지 갱신인지**는 알아도 **어느 키에서 잡혔는지**는 못 안다.
- MySQL, 유니크 키가 여럿일 때 — 매뉴얼이 **스스로 경고한다**: *"If `a=1 OR b=2` matches several rows, only one row is updated. In general, you should try to avoid using an `ON DUPLICATE KEY UPDATE` clause on tables with multiple unique indexes."*\
  **본문 2번의 `(40, 'hr')` 이 바로 그 자리**다. 그 사고는 우연이 아니라 **문서가 미리 경고해 둔 것**이다.

★ **관찰일 뿐인 것 — 여기가 이 절의 핵심이다.**

- **`xmax = 0`** — 문서화된 계약이 아니라 PG 의 내부 열을 읽은 관용구다. 본문 3번의 `f`/`t` 는 **PG 18.6 이 그렇게 보였다**는 뜻이지 「삽입인지 갱신인지 아는 보장된 방법」이 아니다. 보장된 것은 `RETURNING` 이 **행을 돌려준다**는 데까지다.
- **MySQL 이 2번에서 `name` 제약을 잡았다는 것** — 서버는 그렇게 말하지 않았다. 출력은 **영향 행 수 `0` 과 안 바뀐 표**뿐이고, 「`id=30` 행의 `name` 을 `'hr'` → `'hr'` 로 갱신했다」는 **거기서 되짚은 해석**이다.\
  숫자 `0` 자체는 문서가 보장하지만(위), **어느 행·어느 키였는지는 그 출력으로 증명되지 않는다.**\
  PG 쪽은 반대로 제약 이름(`dept_name_key`)을 **에러가 직접 말해 준다** — 같은 사실을 보는 **근거의 세기가 다르다.**
- **잠금·교착** — 「upsert 가 경쟁에서 어떻게 되나」는 이 편에서 **안 돌려 봤다.** 「대기·교착이 생긴다」는 성질이고 **누가 죽느냐**는 한 판의 결과다 — [목록의 **57번 주제**](../57-explicit-locking-and-deadlock/)의 소재다.

★ **모른다** — PG 문서에서 **「지목하지 않은 다른 유니크 제약에서 충돌하면 에러가 난다」고 못 박은 문장은 찾지 못했다.**\
위 유추 규칙에서 따라 나오고 본문 2번의 실행이 그렇게 보여 주지만, **문장으로 확인한 것은 아니다.**

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 멱등 적재.** 같은 메시지가 두 번 와도 한 행만 남아야 할 때.\
  패턴 자체는 [`ops-patterns/06-idempotency-store`](../../../../../ops-patterns/06-idempotency-store/) 가 정본이고, 여기서는 **문법과 충돌 대상 지정**만 다룬다.
- **쓴다 — 집계 캐시 갱신.** 「이 날짜의 집계를 다시 써라」를 한 문으로.
- **쓴다 — 경쟁 조건 제거.** `SELECT` 후 `INSERT` 의 틈을 없앤다.
- **안 쓴다 — 삽입·갱신의 의미가 다를 때.** 「신규 가입」과 「정보 수정」은 이력·알림·권한이 다르다. 한 문으로 합치면 그 분기가 사라진다.
- **안 쓴다 — 삭제까지 필요할 때.** `MERGE` 의 영역이다(PG 15+ 지원, MySQL 8.4 에는 없다 — [목록의 **53번 주제**](../53-merge/)).
- **조심한다 — 대량 upsert.** 행마다 제약 검사와 잠금이 붙는다. 대량이면 임시 표에 적재 후 한 번에 처리하는 편이 낫다.

## 핵심 문장

- upsert 는 **「제약 위반」을 정상 흐름으로 바꾸는 문법**이다. 제약을 모르면 동작도 모른다.
- **PG 는 충돌 대상을 지목하고**(`DO UPDATE` 는 필수), **MySQL 은 아무 유니크 키든** 잡는다.
- 유니크 제약이 둘 이상이면 **같은 문장이 PG 에서는 에러, MySQL 에서는 조용한 0행**이 된다.
- MySQL 의 영향 행 수는 **삽입 1 · 갱신 2 · 무변화 0** 이다. 1이 아니면 실패가 아니다.
- 삽입인지 갱신인지 확실히 알려면 **PG 의 `RETURNING`** 이다. MySQL 8.4.10 에는 없다.
- 한 문 안에 같은 키가 둘이면 **PG 는 거부, MySQL 은 마지막 값 채택**이다.

## 관련 자료

- [PostgreSQL 18 · INSERT](https://www.postgresql.org/docs/18/sql-insert.html) — `ON CONFLICT` 의 `conflict_target`·`EXCLUDED`·`DO UPDATE` 규칙.
- [MySQL 8.4 · INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html)
- [MySQL 8.0.19 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html) — 행 별칭(`AS new`) 도입.
- [`ops-patterns/06-idempotency-store`](../../../../../ops-patterns/06-idempotency-store/) — 멱등 처리 **패턴**은 거기, 여기는 **문법과 충돌 대상 지정**.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `UNIQUE` 열의 `NULL` 은 이 규칙을 따른다([목록의 **43번 주제**](../43-primary-key-unique-and-null/)).
- [SQL 주제 목록](../README.md) — 43(기본키·UNIQUE) · 49(INSERT) · 53(MERGE) · 54(RETURNING) · 57(잠금) 이 이웃이다.

## 용어 풀이

- **upsert** — update + insert. 「있으면 갱신, 없으면 삽입」을 한 문으로 처리하는 것.\
  예: 일별 집계 행을 매번 다시 계산해 덮어쓰기.
- **유니크 제약(unique constraint)** — 열(들)의 값이 표 안에서 중복될 수 없다는 규칙. 기본키도 그중 하나다.\
  예: `dept` 에는 `id`(기본키)와 `name`(UNIQUE) 둘이 있다.
- **충돌 대상(conflict target)** — PG 에서 「어느 제약의 위반을 충돌로 볼지」 지목하는 부분.\
  예: `ON CONFLICT (id)` 는 기본키 위반만 잡고, `name` 위반은 그대로 에러가 된다.
- **`EXCLUDED`** — PG 에서 「넣으려다 막힌 그 행」을 가리키는 예약된 이름.\
  예: `SET name = EXCLUDED.name` 은 원래 넣으려던 이름으로 갱신하라는 뜻.
- **행 별칭(`AS new`)** — MySQL 에서 같은 역할을 하는 이름. 내가 붙인다(8.0.19+).\
  예: `VALUES (30,'people') AS new ... SET name = new.name`.
- **`VALUES()` 함수** — MySQL 의 구식 표현. 8.4.10 서버가 deprecated 경고(1287)를 낸다.\
  예: `SET name = VALUES(name)` → `AS new ... SET name = new.name` 로 바꾼다.
- **영향 행 수(affected rows)** — 문이 바꿨다고 보고하는 행의 개수.\
  예: MySQL 에서 갱신 한 건은 2로 센다 — 삭제 1 + 삽입 1 로 세기 때문이다.
- **`RETURNING`** — PG 에서 변경한 행을 그 자리에서 돌려받는 절.\
  예: `RETURNING id, name` 으로 방금 upsert 한 행을 조회 없이 받는다.
- **`INSERT IGNORE`** — MySQL 에서 에러를 경고로 낮춰 문을 계속 진행시키는 형태.\
  예: 중복 키를 만나도 죽지 않고 경고 1062 만 남긴다.
- **멱등(idempotent)** — 같은 요청을 여러 번 보내도 결과가 한 번 보낸 것과 같은 성질.\
  예: 같은 메시지를 두 번 적재해도 행이 하나만 남는 것.
