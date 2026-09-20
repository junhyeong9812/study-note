# sql/52-UPSERT (ON CONFLICT · ON DUPLICATE KEY UPDATE) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 모든 실험은 `BEGIN`/`ROLLBACK`(MySQL 은 `START TRANSACTION`/`ROLLBACK`)으로 감쌌다 — 기준 상태는 매번 같다.\
> 문서 근거는 [PG 18 INSERT](https://www.postgresql.org/docs/18/sql-insert.html) · [MySQL 8.4 ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html) · [MySQL 8.0.19 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `SELECT` 로 확인한 뒤 `INSERT`/`UPDATE` 하는 코드의 문제

**확인과 처리 **사이**에 다른 접속이 끼어들 수 있다. 두 접속이 같은 「없다」를 보고 둘 다 `INSERT` 한다.**

```text
시간   접속 A                        접속 B                    결과
────   ──────                        ──────                    ────
 t1    SELECT id=40 -> 없다
 t2                                  SELECT id=40 -> 없다       둘 다 "없다"를 봤다
 t3    INSERT (40,...)  -> 성공
 t4                                  INSERT (40,...)  -> 💥     중복 키 에러
```

`t1` 의 판정이 `t3` 시점에도 참이라는 보장이 없다. **읽은 것과 쓰는 것 사이가 비어 있다.**

upsert 는 그 틈을 없앤다.

```text
접속 A: INSERT ... ON CONFLICT (id) DO UPDATE ...
접속 B: INSERT ... ON CONFLICT (id) DO UPDATE ...
          ↓
엔진이 제약 검사와 전환을 한 문 안에서 처리한다
          ↓
둘 다 성공한다 (하나는 삽입, 하나는 갱신)
```

**핵심은 「제약이 판정한다」는 것이다.**\
애플리케이션이 「있나 없나」를 판정하면 그 판정은 곧 낡는다. 엔진이 유니크 제약으로 판정하면 **그 순간의 사실**이다.

> **upsert** — update + insert. 「있으면 갱신, 없으면 삽입」을 한 문으로 처리하는 것.\
> 예: 일별 집계 행을 매번 다시 계산해 덮어쓸 때.

대안으로 `SELECT ... FOR UPDATE` 로 잠그는 방법도 있지만, **없는 행은 잠글 수 없다.** 신규 삽입 경쟁에는 안 통한다(목록의 57번).

---

### 2. ★ `(40, 'hr')` 를 던지면 두 엔진에서 각각 무엇이 일어나나

**PG 는 에러로 죽고, MySQL 은 조용히 성공한다. 그런데 `id = 40` 인 행은 어느 쪽에도 생기지 않는다.**

`id=40` 은 새 값이지만 `name='hr'` 은 이미 `id=30` 행이 쓰고 있다. **유니크 제약이 둘**이라 어느 쪽에서 충돌을 볼지가 갈린다.

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
```

**왜 이렇게 갈리나.**

```text
PostgreSQL                              MySQL
"id 제약에서 충돌하면 갱신해라"          "아무 유니크 키에서든 충돌하면 갱신해라"
         ↓                                       ↓
id=40 은 충돌 안 함 -> 삽입 진행         name 제약에서 충돌을 잡는다
         ↓                                       ↓
name 제약이 터진다                       id=30 행의 name 을 'hr' -> 'hr' 로 갱신
         ↓                                       ↓
지목 밖 제약이므로 그냥 에러              바뀐 게 없어 ROW_COUNT() = 0
```

**두 결과의 공통점이 함정이다 — `id = 40` 인 행은 양쪽 다 안 생겼다.**\
PG 는 그 사실을 에러로 알려 주고, MySQL 은 **성공으로 알려 준다.** 애플리케이션이 이어서 `id=40` 을 조회하면 0행이 나온다.

> **충돌 대상(conflict target)** — PG 에서 「어느 제약의 위반을 충돌로 볼지」 지목하는 부분.\
> 예: `ON CONFLICT (id)` 는 기본키 위반만 잡는다. `name` 위반은 잡히지 않고 그대로 에러가 된다.

**PG 에서 대상을 `name` 으로 바꾸면 세 번째 결과가 나온다.**

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

같은 입력이 지목한 제약에 따라 **에러 / 무변화 / `id` 갱신** 셋으로 갈린다.\
그래서 PG 의 충돌 대상은 장식이 아니라 **의미의 일부**다.

**실무 처방** — 유니크 제약이 둘 이상인 표에 MySQL upsert 를 쓸 때는,\
① 그 문이 어느 제약에 걸릴 수 있는지 전수로 세어 보거나,\
② upsert 대상 표에 유니크 제약을 **하나만** 두거나,\
③ 사전에 `SELECT` 로 충돌 원인을 판별하고 분기한다(경쟁 조건은 다시 생긴다).

---

### 3. 세 문의 `ROW_COUNT()`

**1 · 2 · 0 이다.**

```text
순수 삽입    -> 1
실제 갱신    -> 2     <- 삭제 1 + 삽입 1 로 세기 때문. 실제 행은 하나다
값이 같음    -> 0     <- 갱신 대상은 찾았지만 바뀐 게 없다
```

한 트랜잭션에서 이어 돌린 실제 출력이다.

```text
START TRANSACTION;
INSERT INTO dept VALUES (40, 'legal')  AS new ON DUPLICATE KEY UPDATE name = new.name;
SELECT ROW_COUNT() AS insert_case;
+-------------+
| insert_case |
+-------------+
|           1 |
+-------------+
INSERT INTO dept VALUES (40, 'legal2') AS new ON DUPLICATE KEY UPDATE name = new.name;
SELECT ROW_COUNT() AS update_case;
+-------------+
| update_case |
+-------------+
|           2 |
+-------------+
INSERT INTO dept VALUES (40, 'legal2') AS new ON DUPLICATE KEY UPDATE name = new.name;
SELECT ROW_COUNT() AS nochange_case;
+---------------+
| nochange_case |
+---------------+
|             0 |
+---------------+
ROLLBACK;
```

**두 가지 오독이 흔하다.**

| 오독 | 실제 |
|---|---|
| 「2면 두 행이 바뀐 것」 | 한 행이다. 갱신을 삭제+삽입으로 센다 |
| 「0이면 실패」 | 값이 같아 바뀐 게 없는 것. 성공이다 |

2번의 `(40,'hr')` 이 준 `0` 도 이 세 번째 경우였다 — **실패가 아니라 무변화**다.\
그래서 **`ROW_COUNT()` 만으로는 2번의 사고를 잡아낼 수 없다.**

PG 는 삽입·갱신 모두 `INSERT 0 1` 처럼 1로 보고하고, `DO NOTHING` 이나 `WHERE` 거짓이면 `INSERT 0 0` 이다. **숫자 체계 자체가 다르다** — ORM·드라이버를 방언 사이에서 옮길 때 이 부분이 조용히 어긋난다.

---

### 4. 삽입인지 갱신인지 확실히 알아내는 방법

**PG 에는 있다(`RETURNING`). MySQL 8.4.10 에는 확실한 방법이 없고 영향 행 수로 추정만 한다.**

**PG — `RETURNING` 으로 행을 직접 받는다.**

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

한 문에서 **행마다** 삽입/갱신이 갈렸고, 그걸 그대로 돌려받았다.\
(`xmax = 0` 은 PG 의 내부 열을 이용한 관용구다 — 「이 행은 이 문에서 새로 만들어졌다」. **문서화된 계약이 아니므로** 운영 코드에서는 버전 표기 열 같은 도메인 수단을 쓰는 편이 안전하다.)

**MySQL — `RETURNING` 자체가 없다.**

```text
### SQL: INSERT INTO dept VALUES (50,'tmp') RETURNING id, name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       ERROR 1064 (42000) at line 1: You have an error in your SQL
----+------                        syntax; check the manual that corresponds to your MySQL
 50 | tmp                          server version for the right syntax to use near
(1 row)                            'RETURNING id, name' at line 1
INSERT 0 1
```

남는 수단은 `ROW_COUNT()` 인데 **3번에서 봤듯 모호하다.**

```text
ROW_COUNT() = 1  ->  삽입했다        (확실)
ROW_COUNT() = 2  ->  갱신했다        (확실)
ROW_COUNT() = 0  ->  갱신 대상은 찾았는데 값이 같았다
                     ... 또는 2번처럼 엉뚱한 제약에 걸렸다   <- 구분 불가
```

`LAST_INSERT_ID()` 도 `AUTO_INCREMENT` 열이 있을 때만 쓸모가 있고, 이 표처럼 키를 직접 주는 경우엔 안 된다.

**결론 — 삽입/갱신 분기가 도메인상 중요하면 upsert 로 합치지 않는다.**\
「신규 가입」과 「정보 수정」은 이력·알림·권한이 다르다. 한 문으로 합치면 그 분기가 사라진다.

---

### 5. PG 에서 대상을 안 적은 두 문은 각각 통과하는가

**`DO UPDATE` 는 거부되고, `DO NOTHING` 은 통과한다.**

```text
(A) DO UPDATE — 대상 필수                (B) DO NOTHING — 대상 선택
BEGIN;                                    BEGIN;
INSERT INTO dept VALUES (30,'people')     INSERT INTO dept VALUES (40, 'hr')
  ON CONFLICT DO UPDATE                     ON CONFLICT DO NOTHING;
  SET name = EXCLUDED.name;               ROLLBACK;
ROLLBACK;
--- 실제 출력 ---                         --- 실제 출력 ---
ERROR:  ON CONFLICT DO UPDATE requires    INSERT 0 0
  inference specification or                 <- 0행. 아무것도 안 넣었다
  constraint name
LINE 1: ... ON CONFLICT DO UPDATE ...      SELECT * FROM dept ORDER BY id;
                        ^                   id | name
HINT:  For example, ON CONFLICT           ----+-------
  (column_name).                           10 | sales
                                           20 | dev
                                           30 | hr
                                          (3 rows)
```

**왜 `DO UPDATE` 만 대상이 필요한가.**

```text
DO NOTHING                          DO UPDATE
"충돌하면 아무것도 하지 마라"        "충돌하면 그 행을 갱신해라"
        ↓                                   ↓
어느 제약이 걸렸든 할 일은 같다      "그 행"이 어느 행인지 정해야 한다
        ↓                                   ↓
대상을 몰라도 된다                   제약마다 다른 행이 걸린다 -> 대상 필수
```

PG 문서도 같은 말을 한다 — `DO NOTHING` 에는 `conflict_target` 이 선택이고 생략하면 모든 제약을 잡으며, `DO UPDATE` 에는 반드시 있어야 한다([INSERT 페이지](https://www.postgresql.org/docs/18/sql-insert.html)).

**(B)가 2번의 그 문장이라는 점에 주목한다.** 같은 `(40,'hr')` 인데 `DO NOTHING` 이면 에러 없이 넘어간다 — 대상을 안 적으면 **`name` 제약 위반도 삼키기** 때문이다.

대상 열에 유니크 제약이 아예 없으면 다른 에러가 난다.

```text
BEGIN;
INSERT INTO emp VALUES (5,'eve',10,200) ON CONFLICT (dept_id) DO NOTHING;
ERROR:  there is no unique or exclusion constraint matching the ON CONFLICT specification
ROLLBACK;
```

`emp.dept_id` 에는 유니크 제약이 없다. **충돌을 판정할 근거 자체가 없다**는 뜻이다.

MySQL 쪽 대응물인 `INSERT IGNORE` 는 통과하되 **경고를 남긴다.**

```text
START TRANSACTION;
INSERT IGNORE INTO dept VALUES (30, 'people');
SHOW WARNINGS;
+---------+------+---------------------------------------------+
| Level   | Code | Message                                     |
+---------+------+---------------------------------------------+
| Warning | 1062 | Duplicate entry '30' for key 'dept.PRIMARY' |
+---------+------+---------------------------------------------+
ROLLBACK;
```

**경고가 어느 키에서 걸렸는지까지 알려 준다**(`dept.PRIMARY`) — 2번의 조용한 0행보다 낫다.\
다만 `INSERT IGNORE` 는 중복 외의 에러도 경고로 낮추므로 범위가 넓다.

---

### 6. 한 문 안에 같은 키가 둘일 때

**PG 는 거부하고, MySQL 은 마지막 값을 조용히 채택한다.**

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
```

**PG 의 거부에는 이유가 있다.**

```text
한 문 안에서 같은 행을 두 번 갱신하면
        ↓
"갱신 전 값"이 무엇인지 정의되지 않는다
  - 'legal2' 는 원래 행('hr')을 기준으로 판단할까?
  - 아니면 방금 'legal' 로 바뀐 것을 기준으로?
        ↓
DO UPDATE 의 WHERE 조건과 EXCLUDED 비교가 순서에 의존하게 된다
        ↓
PG 는 그 모호함을 만들지 않고 거부한다
```

MySQL 은 **입력 순서대로 적용**해서 마지막 값이 남는다. 정의되어 있지만 **상류의 중복 버그가 드러나지 않는다.**

```text
PG 에서 배포하면                      MySQL 에서 배포하면
  배치가 즉시 실패한다                  배치가 성공한다
  -> 입력에 중복이 있다는 걸 안다       -> 중복이 있다는 걸 모른다
  -> 상류를 고친다                      -> 어느 행이 살아남을지는 입력 순서에 달린다
```

**양쪽 모두에서 안전한 처방은 upsert 전에 입력을 키 기준으로 한 번 접는 것(dedup)이다.**\
「어느 것을 남길지」를 SQL 이 아니라 **내가** 정하게 된다.

---

### 7. 「기존 값보다 클 때만 덮어써라」를 두 엔진에서 쓰는 법

**PG 는 `DO UPDATE` 에 `WHERE` 를 붙이고, MySQL 은 `IF()`·`GREATEST()` 식으로 접는다.**

```text
PG — 갱신할지 말지를 WHERE 가 정한다      MySQL — 갱신은 늘 하되 값이 같아지게 만든다
+-------------------------------+        +-------------------------------+
| ON CONFLICT (id) DO UPDATE    |        | ON DUPLICATE KEY UPDATE       |
|   SET name = EXCLUDED.name    |        |   name = IF(조건, 새값, 기존값)|
|   WHERE dept.name < EXCLUDED. |        |                               |
|         name                  |        |                               |
+-------------------------------+        +-------------------------------+
   조건 거짓이면 0행                        조건 거짓이면 같은 값으로 갱신 -> 0행
```

**PG 실제 출력** — `'hr' < 'aaa'` 는 거짓이라 안 바뀐다.

```text
BEGIN;
INSERT INTO dept VALUES (30,'aaa')
  ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
  WHERE dept.name < EXCLUDED.name;
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

`WHERE` 에서 **`dept.name` 은 기존 행, `EXCLUDED.name` 은 넣으려던 행**이다. 두 이름이 다 있어야 비교가 된다.

**MySQL 실제 출력** — 두 경우를 이어 돌렸다.

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

수치라면 `GREATEST(dept.cnt, new.cnt)` 형태가 흔하다.

**쓰임 — 늦게 도착한 오래된 데이터가 최신 값을 지우는 사고를 막는다.**\
메시지가 순서대로 오지 않는 큐에서는 이 조건이 사실상 필수다.

**주의** — 조건이 거짓일 때 두 엔진 다 `0` 행을 보고한다.\
3번의 「값이 같아서 0」과 **구분되지 않는다.** 구분이 필요하면 PG 는 `RETURNING`, MySQL 은 이어서 `SELECT` 를 쳐야 한다.

---

### 8. MySQL 8.4.10 에서 `RETURNING` 이 도는가

**돌지 않는다. `ERROR 1064` 문법 오류다.**

```text
### SQL: INSERT INTO dept VALUES (50,'tmp') RETURNING id, name;
--- PG 18.6 ---
 id | name
----+------
 50 | tmp
(1 row)
INSERT 0 1
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'RETURNING id, name' at line 1
```

`1064` 는 **문법 오류** 코드다 — 파서가 `RETURNING` 이라는 단어를 모른다.

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `INSERT ... RETURNING` | ✓ | ✗ `ERROR 1064` |
| upsert 결과를 행으로 회수 | ✓ | ✗ |
| 대안 | — | `ROW_COUNT()` 추정 / 이어서 `SELECT` |

**이어서 `SELECT` 를 치는 대안에는 틈이 있다.**

```text
INSERT ... ON DUPLICATE KEY UPDATE ...     <- 여기서 커밋 전
SELECT * FROM dept WHERE id = 40;          <- 같은 트랜잭션이면 내 변경은 보인다
                                              다른 트랜잭션이 또 바꿨다면?
```

같은 트랜잭션 안이면 내가 쓴 것은 보이므로 대부분은 괜찮다. 다만 **문 하나로 끝나지 않는다**는 점은 남는다 — 왕복이 하나 더 늘고, 격리 수준에 따라 읽히는 것이 달라진다(목록의 56번).

**정리하면 이 주제의 방언 차이는 넷이다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 충돌 대상 지목 | 가능 (`DO UPDATE` 는 필수) | 불가능 — 아무 유니크 키든 |
| 갱신 조건 | `DO UPDATE ... WHERE` | 없음 — `IF()`·`GREATEST()` 식 |
| 결과 회수 | `RETURNING` | 없음 |
| 한 문 안 같은 키 중복 | 에러 | 마지막 값 채택 |

넷 중 **2·6번의 차이만 조용하다.** 나머지 둘은 에러로 터진다.\
그래서 이식할 때 진짜 위험한 것은 **문법이 아니라 의미**다.
