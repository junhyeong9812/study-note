# sql/53-MERGE — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · MERGE](https://www.postgresql.org/docs/18/sql-merge.html) · [PostgreSQL 15 릴리스 노트](https://www.postgresql.org/docs/release/15.0/) · [PostgreSQL 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/) · [MySQL 8.4 · Data Manipulation Statements](https://dev.mysql.com/doc/refman/8.4/en/sql-data-manipulation-statements.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **한쪽에서만 결론이 서는 주제다.** MySQL 8.4.10 에는 `MERGE` 가 **없다** — MySQL 쪽 출력은 전부 `ERROR 1064` 하나이고, **동작에 관한 모든 근거는 PostgreSQL 18.6 뿐**이다.\
> **버전** — `MERGE` 는 **PG 15 부터**, `WHEN NOT MATCHED BY SOURCE` 와 `RETURNING`·`merge_action()` 은 **PG 17 부터**다(릴리스 노트 확인). **PG 15·16·17 컨테이너가 없어 옛 버전에서의 거부는 직접 재현하지 못했다.**\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 `t53_tgt`·`t53_src`·`t53_dup` 을 만들었고 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> ★ **52 편과의 경계** — **「한 문으로 있으면 갱신, 없으면 삽입」은 [52 UPSERT](../52-upsert/)가 정본이다.** 이 편은 **그것으로 안 되는 것**(원본에 없는 행 지우기·조건별 분기·삭제)과 **그것만 되는 것**(충돌 대상 지목·동시 삽입 대응)의 경계만 다룬다.\
> **선행** — [52 UPSERT](../52-upsert/) · [49 INSERT](../49-insert-multi-row-and-insert-select/) · [50 UPDATE](../50-update-with-join-and-subquery/) · [51 DELETE 와 TRUNCATE](../51-delete-and-truncate/).

## 한눈에 — 쉽게 말하면

**`MERGE` 는 「대상 표를 원본 표에 맞춰라」를 한 문으로 시키는 것.**

```text
대상(target)                원본(source)
+----+------+-----+         +----+------+-----+
|  1 | ann  |  10 |         |    |      |     |   <- 원본에 없다
|  2 | bob  |  20 |  <----  |  2 | bob2 |  99 |   <- 양쪽에 있다
|  3 | cho  |  30 |  <----  |  3 | cho  |  30 |   <- 양쪽에 있다
|    |      |     |         |  4 | dan  |  40 |   <- 대상에 없다
+----+------+-----+         +----+------+-----+

MERGE 가 세 자리를 각각 다르게 처리한다
  양쪽에 있다  -> WHEN MATCHED              -> UPDATE / DELETE / DO NOTHING
  대상에 없다  -> WHEN NOT MATCHED          -> INSERT / DO NOTHING
  원본에 없다  -> WHEN NOT MATCHED BY SOURCE -> ★ UPDATE / DELETE / DO NOTHING  (PG 17+)
```

일상 비유로 바꾸면 **명부 동기화**다.

```text
새 명부를 받아 옛 명부를 고친다
  둘 다 있는 사람   -> 정보를 갱신한다
  새 명부에만 있는 사람 -> 새로 등록한다
  ★ 옛 명부에만 있는 사람 -> 퇴사했다는 뜻이니 지운다   <- upsert 로는 못 하는 일
```

"똑같은 구조다" — **upsert 는 「들어오는 행」만 보고, `MERGE` 는 「양쪽 표 전체」를 본다.**

| 비유 | 실체 |
|---|---|
| 새 명부를 받는다 | `USING <원본>` |
| 같은 사람인지 알아보는 기준 | `ON <조인 조건>` |
| 둘 다 있으면 | `WHEN MATCHED THEN UPDATE \| DELETE \| DO NOTHING` |
| 새 명부에만 있으면 | `WHEN NOT MATCHED THEN INSERT \| DO NOTHING` |
| ★ 옛 명부에만 있으면 | **`WHEN NOT MATCHED BY SOURCE`** — upsert 에 없는 자리 |
| 같은 사람이 새 명부에 두 번 | `MERGE command cannot affect row a second time` |

★ **이 편의 축은 하나다 — 「`MERGE` 로 할 일을 upsert 가 이미 하나」.**\
답은 **대부분 그렇다.** 갈리는 자리가 **정확히 둘**이고, 그 둘이 서로 반대 방향이다(4·5번).

## 이 주제가 답하려는 질문

1. **두 엔진에 `MERGE` 가 있나?** — MySQL 8.4 에 없다는 것을 무엇으로 확인하나.
2. **`MERGE` 로 되고 upsert 로 안 되는 일은 무엇인가?** — 그 반대는?
3. **`MERGE` 는 어느 버전부터인가?** — 그리고 그 안에서도 무엇이 나중에 들어왔나.

## 예시 데이터 — 이 편이 만든 표

`emp`·`dept` 는 **한 줄도 쓰지 않았다.**

```text
t53_tgt (대상)                      t53_src (원본)
+----+------+-----+                 +----+------+-----+
| id | name | qty |                 | id | name | qty |
+----+------+-----+                 +----+------+-----+
|  1 | ann  |  10 |  <- 원본에 없다  |  2 | bob2 |  99 |
|  2 | bob  |  20 |                 |  3 | cho  |  30 |  <- 값이 같다
|  3 | cho  |  30 |                 |  4 | dan  |  40 |  <- 대상에 없다
+----+------+-----+                 +----+------+-----+

t53_dup (짝이 둘인 실험용)
+----+------+-----+
|  2 | x    |   1 |
|  2 | y    |   2 |
+----+------+-----+
```

```sql
CREATE TABLE t53_tgt (id int PRIMARY KEY, name varchar(10), qty int);
CREATE TABLE t53_src (id int PRIMARY KEY, name varchar(10), qty int);
```

실험은 전부 `BEGIN`/`ROLLBACK` 으로 감쌌다 — 기준 상태는 매번 위 그림과 같다.

## 동작 방식

### 1. ★ MySQL 8.4.10 에는 `MERGE` 가 없다 — 던져서 확인한다

**언제 쓰나** — 이 주제를 시작할 때. **「미지원」을 단정하기 전에 던져 본다.**

```text
### SQL: MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
         WHEN MATCHED THEN UPDATE SET name = s.name, qty = s.qty
         WHEN NOT MATCHED THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
--- PG 18.6 ---
MERGE 3
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id WHEN MATCHED THEN UPDATE SET' at line 1
```

★ **`ERROR 1064` 는 「구문 오류」다 — 파서가 `MERGE` 라는 낱말 자체를 모른다는 뜻**이다.\
[23 번의 `CUBE`](../23-grouping-sets-rollup-cube/)처럼 **파싱은 되는데 실행 경로가 없는 경우**(`ERROR 3889`)와 다르다.\
`MERGE` 는 **키워드 단계에서 막힌다.**

★ **이것이 이 편에서 얻을 수 있는 MySQL 쪽 근거의 전부다.**\
아래 2~7번의 모든 출력은 **PostgreSQL 18.6 하나에서만** 나온 것이고,\
**MySQL 쪽 대응물은 문법이 아니라 「무엇으로 대신하나」(6번)로만 답할 수 있다.**

MySQL 의 대응물은 두 가지다.

```text
"있으면 갱신 없으면 삽입"        -> INSERT ... ON DUPLICATE KEY UPDATE   (52번)
"원본에 없는 대상 행 지우기"      -> ★ 한 문으로는 없다. 별도 DELETE 문이 필요하다
```

### 2. 기본형 — 세 자리를 한 문으로

**언제 쓰나** — 배치 동기화. 「받은 목록대로 표를 맞춰라」가 요구사항일 때.

```text
(전) t53_tgt              원본 t53_src
+----+------+-----+       +----+------+-----+
|  1 | ann  |  10 |       |  2 | bob2 |  99 |
|  2 | bob  |  20 |       |  3 | cho  |  30 |
|  3 | cho  |  30 |       |  4 | dan  |  40 |
+----+------+-----+       +----+------+-----+
   ↓ MERGE (MATCHED -> UPDATE, NOT MATCHED -> INSERT)
(후) t53_tgt
+----+------+-----+
|  1 | ann  |  10 |   <- 안 건드렸다 (원본에 없다)
|  2 | bob2 |  99 |   <- 갱신됐다
|  3 | cho  |  30 |   <- 값이 같아도 갱신 대상이다
|  4 | dan  |  40 |   <- 삽입됐다
+----+------+-----+
```

```text
--- PG 18.6 ---
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED     THEN UPDATE SET name = s.name, qty = s.qty
  WHEN NOT MATCHED THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
MERGE 3
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |  10
  2 | bob2 |  99
  3 | cho  |  30
  4 | dan  |  40
(4 rows)
```

그림 해설 — **`MERGE 3` 은 「세 행을 건드렸다**」는 뜻이다(갱신 2 + 삽입 1).\
`id=1` 은 원본에 없어 **대상 집합 밖**이다 — [50 번 2절의 조인형 갱신](../50-update-with-join-and-subquery/)과 같은 규칙이다.

비용 — 한 문이므로 **원자적**이다. 실패하면 전부 되돌아간다([49 번](../49-insert-multi-row-and-insert-select/)).

> **대상(target)과 원본(source)** — `MERGE INTO <대상> USING <원본> ON <조건>`.\
> 예: 원본은 표일 수도, 서브쿼리일 수도, `VALUES` 목록일 수도 있다(문법 절).

### 3. 조건을 단 `WHEN` 과 `DO NOTHING`

**언제 쓰나** — 「더 나은 값일 때만 덮어써라」처럼 분기가 필요할 때.

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED AND s.qty > t.qty THEN UPDATE SET qty = s.qty
  WHEN MATCHED                   THEN DO NOTHING
  WHEN NOT MATCHED               THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
MERGE 2
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |  10
  2 | bob  |  99      <- 99 > 20 이라 갱신됐다 (name 은 안 바꿨다)
  3 | cho  |  30      <- 30 > 30 이 거짓이라 DO NOTHING
  4 | dan  |  40      <- 삽입
(4 rows)
ROLLBACK;
```

```text
WHEN 절은 위에서부터 처음 맞는 것 하나만 실행된다

  s.qty > t.qty 가 참  -> 첫째 WHEN MATCHED (UPDATE)
  거짓                 -> 둘째 WHEN MATCHED (DO NOTHING)
```

그림 해설 — **순서가 의미다.** 조건 없는 `WHEN MATCHED` 를 위로 올리면 아래 것은 절대 안 걸린다.

★ **`MERGE 2` 를 주목한다** — `DO NOTHING` 으로 처리된 행은 **안 센다.**

**아무 `WHEN` 도 안 맞으면 그 행은 그냥 넘어간다 — 에러가 아니다.**

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED THEN UPDATE SET qty = s.qty;      -- NOT MATCHED 절이 없다
MERGE 2
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |  10
  2 | bob  |  99
  3 | cho  |  30
(3 rows)                                          <- id=4 는 삽입되지 않았고 에러도 없다
ROLLBACK;
```

비용 — **「조용히 안 한다」가 기본 동작**이다. `NOT MATCHED` 절을 빠뜨리면 **삽입이 통째로 사라지는데 아무도 안 알려 준다.**\
[49 번의 `INSERT 0 0`](../49-insert-multi-row-and-insert-select/)과 같은 종류의 무음이다 — **영향 행 수를 반드시 읽는다.**

### 4. ★★ `MERGE` 만 되는 일 — `WHEN NOT MATCHED BY SOURCE`

**언제 쓰나** — 「받은 목록에 없는 행은 지워라」가 요구사항일 때. **upsert 로는 표현할 수 없는 자리다.**

```text
(전) t53_tgt              원본 t53_src
+----+------+-----+       +----+------+-----+
|  1 | ann  |  10 |  <- 원본에 없다
|  2 | bob  |  20 |       |  2 | bob2 |  99 |
|  3 | cho  |  30 |       |  3 | cho  |  30 |
+----+------+-----+       |  4 | dan  |  40 |
                          +----+------+-----+
   ↓ MERGE + WHEN NOT MATCHED BY SOURCE THEN DELETE
(후) t53_tgt
+----+------+-----+
|  2 | bob2 |  99 |
|  3 | cho  |  30 |
|  4 | dan  |  40 |
+----+------+-----+        <- ★ id=1 이 사라졌다. 대상이 원본과 똑같아졌다
```

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED              THEN UPDATE SET name=s.name, qty=s.qty
  WHEN NOT MATCHED          THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty)
  WHEN NOT MATCHED BY SOURCE THEN DELETE;
MERGE 4
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  2 | bob2 |  99
  3 | cho  |  30
  4 | dan  |  40
(3 rows)
ROLLBACK;
```

★ **`MERGE 4`** — 갱신 2 + 삽입 1 + **삭제 1**. 세 종류의 DML 이 한 문에서 일어났다.

PG 문서가 이 절을 정의한다.

> "If the `WHEN` clause specifies `WHEN NOT MATCHED BY SOURCE` and the candidate change row represents a row in the target table that does not match a row in the `data_source`, the `WHEN` clause is executed if the `condition` is absent or it evaluates to `true`."\
> — [PostgreSQL 18 · MERGE](https://www.postgresql.org/docs/18/sql-merge.html)

**왜 upsert 로는 안 되나** — `INSERT … ON CONFLICT` 는 **내가 넣으려는 행만** 본다.

```text
upsert 가 보는 것 : 내가 VALUES/SELECT 로 준 행들
                    -> "대상 표에만 있는 행" 은 시야 밖이다
MERGE 가 보는 것  : 대상 표와 원본을 ON 으로 맞춘 결과 전체
                    -> ★ "원본에 없는 대상 행" 이라는 자리가 생긴다
```

**upsert 로 같은 일을 하려면 문이 둘 필요하다.**

```sql
-- 1) 있으면 갱신 없으면 삽입
INSERT INTO t53_tgt SELECT * FROM t53_src ON CONFLICT (id) DO UPDATE SET ...;
-- 2) 원본에 없는 행 지우기 — 별도 문
DELETE FROM t53_tgt WHERE id NOT IN (SELECT id FROM t53_src);
```

비용 — **문이 둘이면 원자 단위가 둘**이다. 둘을 한 트랜잭션에 넣어야 같은 보장이 나온다([목록의 55번](../README.md)).\
그리고 `NOT IN` 에 `NULL` 이 섞이면 결과가 통째로 빈다 — [19 SEMI·ANTI 조인](../19-semi-anti-join/)이 정본이다.

★ **버전을 적는 자리다.** `WHEN NOT MATCHED BY SOURCE` 는 **PG 17 부터**다.

> "Add `WHEN NOT MATCHED BY SOURCE` to `MERGE` (Dean Rasheed) … `WHEN NOT MATCHED` on target rows was already supported."\
> — [PostgreSQL 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/)

**PG 15·16 컨테이너가 없어 그 버전에서의 거부는 직접 재현하지 못했다.**

### 5. ★★ upsert 만 되는 일 — 충돌 대상 지목과 동시 삽입

**언제 쓰나** — 4번의 반대편. **`MERGE` 가 못 하는 것이 여기 있다.**

**(a) `ON` 이 안 덮는 유니크 제약에서 `MERGE` 는 그냥 죽는다.**

`t53_tgt.name` 에 `UNIQUE` 를 걸고, **`id` 는 새 값이고 `name` 은 이미 있는** 행을 넣어 본다.

```text
--- PG 18.6 ---
ALTER TABLE t53_tgt ADD CONSTRAINT t53_tgt_name_uq UNIQUE (name);

MERGE INTO t53_tgt t USING (SELECT 9 AS id, 'ann' AS name, 5 AS qty) s ON t.id = s.id
  WHEN MATCHED     THEN UPDATE SET qty = s.qty
  WHEN NOT MATCHED THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
ERROR:  duplicate key value violates unique constraint "t53_tgt_name_uq"
DETAIL:  Key (name)=(ann) already exists.
```

**같은 입력을 upsert 로 던지면 처리된다.**

```text
--- PG 18.6 ---
BEGIN;
INSERT INTO t53_tgt (id,name,qty) VALUES (9,'ann',5)
  ON CONFLICT (name) DO UPDATE SET qty = EXCLUDED.qty;
INSERT 0 1
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |   5      <- ★ name 으로 찾아 갱신했다
  2 | bob  |  20
  3 | cho  |  30
(3 rows)
ROLLBACK;
```

```text
MERGE                                   INSERT ... ON CONFLICT
+-----------------------------+         +-----------------------------+
| 같은 행인지를 ON 이 정한다   |         | 같은 행인지를 "제약" 이 정한다 |
| ON 밖의 제약은 그냥 위반이다 |         | ★ 어느 제약을 볼지 지목한다   |
+-----------------------------+         +-----------------------------+
  -> ERROR duplicate key                   -> 그 제약으로 찾아 갱신한다
```

**`MERGE` 의 `ON` 은 조인 조건이지 제약이 아니다.**\
[52 번](../52-upsert/)의 「충돌 대상을 지목한다」가 **여기서 `MERGE` 와 갈리는 자리**다.

**(b) 동시 삽입 대응 — 문서가 직접 갈라 적는다.**

> "When `MERGE` is run concurrently with other commands that modify the target table, the usual transaction isolation rules apply… **You may also wish to consider using `INSERT ... ON CONFLICT` as an alternative statement which offers the ability to run an `UPDATE` if a concurrent `INSERT` occurs.** There are a variety of differences and restrictions between the two statement types and they are not interchangeable."\
> — [PostgreSQL 18 · MERGE](https://www.postgresql.org/docs/18/sql-merge.html)

★ **이 문장이 이 편의 경계 선언이다** — 문서 스스로 「**서로 바꿔 쓸 수 없다**」고 적는다.\
`MERGE` 의 `ON` 은 **문이 시작될 때 본 스냅숏**으로 맞춘다. 그 사이 다른 세션이 같은 키를 넣으면\
`NOT MATCHED` 로 판정된 행이 `INSERT` 하다 **유니크 위반으로 죽을 수 있다.**

★ **이 동시 상황은 이 편에서 재현하지 않았다** — 세션을 둘 띄워 경쟁을 만드는 실험을 하지 않았다.\
**근거는 실행 출력이 아니라 위 문서 문장이다.** 그 사실을 밝혀 둔다.

### 6. 그래서 경계는 어디인가 — 52 와 53

**언제 쓰나** — 「어느 문을 쓸까」를 고를 때.

```text
요구사항이 무엇인가
│
├─ "이 행들을 있으면 갱신, 없으면 삽입"
│    -> ★ 52 UPSERT. 두 엔진 다 된다. 동시 삽입에도 강하다
│
├─ "이 행들 + 목록에 없는 기존 행은 삭제" (동기화)
│    -> ★ 53 MERGE (PG 17+). MySQL 은 문 둘 + 트랜잭션
│
├─ "조건에 따라 갱신/삭제/무시를 갈라야 한다"
│    -> ★ 53 MERGE. upsert 의 WHERE 로는 삭제가 안 된다
│
└─ "어느 제약에서 충돌하는지 지목해야 한다"
     -> ★ 52 UPSERT. MERGE 의 ON 으로는 못 한다 (5번)
```

| | [52 UPSERT](../52-upsert/) | 53 `MERGE` |
|---|---|---|
| PostgreSQL 18.6 | `INSERT … ON CONFLICT` | `MERGE`(**15+**) |
| MySQL 8.4.10 | `INSERT … ON DUPLICATE KEY UPDATE` | **없다**(`ERROR 1064`) |
| 무엇을 보나 | **내가 넣으려는 행** | **대상 표와 원본을 맞춘 결과 전체** |
| 삭제 | 못 한다 | `WHEN MATCHED THEN DELETE` · `NOT MATCHED BY SOURCE THEN DELETE`(17+) |
| 충돌 대상 지목 | **된다** | 안 된다 — `ON` 은 조인 조건이다 |
| 동시 삽입 | **강하다**(문서가 권한다) | 문서가 `ON CONFLICT` 를 대안으로 제시 |
| 조건 분기 | `DO UPDATE … WHERE` 하나 | `WHEN … AND 조건` 을 여러 개 |
| 한 문 안 같은 키 중복 | 에러 | 에러(문구가 다르다 — 7번) |

★ **한 줄 선언** — **「들어오는 행을 어떻게 반영하나」는 52, 「두 표를 어떻게 맞추나」는 53.**

### 7. 짝이 둘이면 — 두 문이 다른 문구로 같은 것을 말한다

**언제 쓰나** — 원본에 중복 키가 있을 때. [50 번 4절](../50-update-with-join-and-subquery/)의 `MERGE` 판이다.

```text
t53_dup
+----+------+-----+
|  2 | x    |   1 |     <- id=2 가 둘
|  2 | y    |   2 |
+----+------+-----+
```

```text
### SQL: MERGE INTO t53_tgt t USING t53_dup s ON t.id=s.id WHEN MATCHED THEN UPDATE SET qty=s.qty;
--- PG 18.6 ---
ERROR:  MERGE command cannot affect row a second time
HINT:  Ensure that not more than one source row matches any one target row.

### SQL: INSERT INTO t53_tgt (id,name,qty) SELECT id,name,qty FROM t53_dup ON CONFLICT (id) DO UPDATE SET qty=EXCLUDED.qty;
--- PG 18.6 ---
ERROR:  ON CONFLICT DO UPDATE command cannot affect row a second time
HINT:  Ensure that no rows proposed for insertion within the same command have duplicate constrained values.
```

**두 문이 같은 규칙을 지킨다 — 문구만 다르다.**

```text
MERGE          : "not more than one source row matches any one target row"
ON CONFLICT    : "no rows proposed for insertion ... have duplicate constrained values"
```

★ [**50 번의 조인형 `UPDATE` 와 대비된다.**](../50-update-with-join-and-subquery/)\
같은 중복 원본을 `UPDATE … FROM` 으로 던지면 **조용히 하나를 고르고** 넘어간다.\
`MERGE` 는 **거부한다.** 같은 상황에서 **`MERGE` 쪽이 더 안전하다.**

PG 문서가 그 규칙을 적는다.

> "You should ensure that the join produces at most one candidate change row for each target row. In other words, a target row shouldn't join to more than one data source row. If it does, then only one of the candidate change rows will be used to modify the target row; **later attempts to modify the row will cause an error**."\
> — [PostgreSQL 18 · MERGE](https://www.postgresql.org/docs/18/sql-merge.html)

**처방** — 원본을 먼저 접는다(`GROUP BY`·`DISTINCT ON`). 두 문 모두에 해당한다.

### 8. `RETURNING` 과 `merge_action()` — 무엇을 했는지 돌려받는다

**언제 쓰나** — 배치 동기화 결과를 로그로 남길 때. **PG 17 부터다.**

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED              THEN UPDATE SET qty = s.qty
  WHEN NOT MATCHED          THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty)
  WHEN NOT MATCHED BY SOURCE THEN DELETE
  RETURNING merge_action(), t.id, t.name, t.qty;
 merge_action | id | name | qty 
--------------+----+------+-----
 DELETE       |  1 | ann  |  10
 UPDATE       |  2 | bob  |  99
 UPDATE       |  3 | cho  |  30
 INSERT       |  4 | dan  |  40
(4 rows)
MERGE 4
ROLLBACK;
```

그림 해설 — **행마다 무엇이 일어났는지 문자열로 준다.**\
[52 번](../52-upsert/)에서 「삽입인지 갱신인지」를 `xmax = 0` 관용구로 추정했던 것과 대비된다 —\
**여기는 문서화된 함수**다.

> "Allow `MERGE` to use the `RETURNING` clause (Dean Rasheed) … The new `RETURNING` function `merge_action()` reports on the DML that generated the row."\
> — [PostgreSQL 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/)

`RETURNING` 자체와 그것을 CTE 에 넣는 법은 [54 번](../54-returning-and-data-modifying-cte/)이 정본이다.

## 문법 — 어느 절에서 무엇이 갈리나

```sql
MERGE INTO <대상> [AS] t
USING <원본> [AS] s          -- 표 · 서브쿼리 · VALUES 목록
   ON <조인 조건>
WHEN MATCHED [AND 조건] THEN { UPDATE SET ... | DELETE | DO NOTHING }
WHEN NOT MATCHED [BY TARGET] [AND 조건] THEN { INSERT (...) VALUES (...) | DO NOTHING }
WHEN NOT MATCHED BY SOURCE [AND 조건] THEN { UPDATE SET ... | DELETE | DO NOTHING }   -- PG 17+
[RETURNING merge_action(), ... ]                                                      -- PG 17+
;
```

원본은 `VALUES` 목록이어도 된다 — 애플리케이션이 보낸 배치를 그대로 맞출 때 쓴다.

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING (VALUES (2,'bob9',77),(9,'new',88)) AS s(id,name,qty) ON t.id = s.id
  WHEN MATCHED     THEN UPDATE SET name=s.name, qty=s.qty
  WHEN NOT MATCHED THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty)
  RETURNING merge_action(), t.*;
 merge_action | id | name | qty 
--------------+----+------+-----
 UPDATE       |  2 | bob9 |  77
 INSERT       |  9 | new  |  88
(2 rows)
MERGE 2
ROLLBACK;
```

규칙 일곱.

1. **`WHEN` 절은 위에서부터 처음 맞는 것 하나만** 실행된다. 순서가 의미다.
2. **아무 `WHEN` 도 안 맞으면 그 행은 조용히 넘어간다.** 에러가 아니다(3번).
3. **`ON` 은 조인 조건이지 제약이 아니다.** 그 밖의 유니크 위반은 그냥 에러다(5번).
4. **한 대상 행에 원본이 둘 맞으면 에러**다 — `cannot affect row a second time`(7번).
5. **`MERGE` 는 PG 15+**, **`NOT MATCHED BY SOURCE`·`RETURNING`·`merge_action()` 은 PG 17+** 다.
6. **MySQL 8.4.10 에는 `MERGE` 가 없다** — `ERROR 1064`.
7. **영향 행 수(`MERGE n`)는 실제로 처리한 행만** 센다. `DO NOTHING` 은 안 센다(3번).

읽을 때 붙잡을 것은 **「어느 쪽에 없는 행인가」** 하나다.

```text
 원본에 있고 대상에 없다 -> NOT MATCHED            -> INSERT
 양쪽에 다 있다          -> MATCHED                -> UPDATE / DELETE / DO NOTHING
 대상에 있고 원본에 없다 -> NOT MATCHED BY SOURCE  -> ★ 여기가 upsert 에 없는 자리 (PG 17+)
```

#### 방언 요약

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `MERGE` | **있다**(15+) | **없다** — `ERROR 1064` |
| `WHEN MATCHED THEN DELETE` | 있다 | — |
| `WHEN NOT MATCHED BY SOURCE` | 있다(17+) | — |
| `RETURNING` · `merge_action()` | 있다(17+) | — |
| 대응물 | — | `INSERT … ON DUPLICATE KEY UPDATE`([52번](../52-upsert/)) + 별도 `DELETE` |
| 짝이 둘일 때 | `MERGE command cannot affect row a second time` | — |

## 어디서 틀리나

1. ★ **「`MERGE` 는 표준이니 어디서나 되겠지」로 이식한다.** MySQL 8.4.10 은 `ERROR 1064` 다(1번).
2. ★ **`MERGE` 를 upsert 의 다른 이름으로 안다.**\
   **문서가 「서로 바꿔 쓸 수 없다」고 적는다**(5번). 동시 삽입에는 `ON CONFLICT` 를 권한다.
3. **`ON` 이 유니크 제약을 대신한다고 생각한다.**\
   `ON` 밖의 제약 위반은 **그냥 에러**다(5번 a). upsert 는 그 제약을 지목할 수 있다.
4. **`WHEN NOT MATCHED` 를 빠뜨린다.** 삽입이 통째로 사라지는데 **에러도 경고도 없다**(3번).
5. **`WHEN` 절의 순서를 아무렇게나 둔다.** 조건 없는 절을 위에 두면 아래는 죽은 코드다.
6. **`MERGE n` 을 「바뀐 행 수」로 읽는다.** `DO NOTHING` 행은 안 센다(3번).
7. **원본의 중복을 확인하지 않는다.** `cannot affect row a second time` 으로 문 전체가 죽는다(7번).
8. **`WHEN NOT MATCHED BY SOURCE` 를 PG 15·16 에서 쓴다.** **17 부터**다(4번).
9. **동기화를 「upsert + `DELETE … NOT IN`」 두 문으로 쪼개고 트랜잭션을 안 건다.**\
   원자 단위가 둘이 된다. 그리고 `NOT IN` 에 `NULL` 이 섞이면 결과가 빈다([19번](../19-semi-anti-join/)).

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| `MERGE` 의 존재 | — | ★ **전부** — PG 15+ / MySQL 8.4 에는 없다 |
| `WHEN` 절 선택 | 위에서부터 처음 맞는 하나 | — |
| 아무 절도 안 맞을 때 | **조용히 넘어간다**(PG 문서) | — |
| 한 대상 행에 원본 둘 | **PG 문서: 나중 시도가 에러** | 에러 문구 |
| 동시 삽입 | **PG 문서: `ON CONFLICT` 를 대안으로 제시** | ★ 실제 경쟁 동작 |
| `merge_action()` | PG 17+ 의 문서화된 함수 | — |

- ★ **이 편의 MySQL 쪽 근거는 `ERROR 1064` 하나뿐이다.** 그 밖의 모든 비교는 **PG 출력과 두 문서**에서 나왔다.
- ★ **5번 (b) 의 동시 삽입은 실행으로 확인하지 않았다** — **근거는 문서 문장이다.**
- **`t53_tgt_name_uq` 같은 제약 이름**은 내가 지은 것이다. 에러 문구의 나머지는 PG 가 만든 것이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 배치 동기화.** 「받은 목록대로 표를 맞춰라」. `NOT MATCHED BY SOURCE` 가 그 마지막 조각이다.
- **쓴다 — 조건별로 갱신·삭제·무시가 갈릴 때.** `WHEN … AND` 를 여러 개 쌓는다.
- **쓴다 — 무엇을 했는지 로그로 남겨야 할 때.** `RETURNING merge_action()`(PG 17+).
- **안 쓴다 — 단순 upsert.** [52 번](../52-upsert/)이 짧고, 두 엔진에서 돌고, 동시 삽입에 강하다.
- **안 쓴다 — 경쟁이 심한 단일 행 갱신.** 문서가 `ON CONFLICT` 를 권한다(5번 b).
- **안 쓴다 — MySQL 을 같이 쓰는 코드베이스.** 한쪽에서 안 돈다(1번).
- **조심한다 — 원본에 중복이 섞일 수 있을 때.** 먼저 접는다(7번).
- **조심한다 — `NOT MATCHED BY SOURCE THEN DELETE`.** **원본이 비면 대상 표가 통째로 비워진다.**\
  조건을 붙이거나(`AND t.updated_at < …`) 원본 행 수를 먼저 검사한다.

## 핵심 문장

- **MySQL 8.4.10 에는 `MERGE` 가 없다** — `ERROR 1064`, 키워드 단계에서 막힌다.
- **`MERGE` 는 PG 15 부터**, `WHEN NOT MATCHED BY SOURCE` 와 `RETURNING`·`merge_action()` 은 **17 부터**다.
- ★ **`MERGE` 만 되는 일은 「원본에 없는 대상 행을 지우기**」다 — upsert 는 들어오는 행만 본다.
- ★ **upsert 만 되는 일은 「충돌 제약 지목」과 「동시 삽입 대응**」이다 — `ON` 은 조인 조건이지 제약이 아니다.
- **PG 문서가 둘을 「서로 바꿔 쓸 수 없다」고 명시한다.**
- **`WHEN` 절은 위에서부터 처음 맞는 하나만** 실행되고, **아무것도 안 맞으면 조용히 넘어간다.**
- **원본이 한 대상 행에 둘 맞으면 에러**다 — 같은 상황에서 `UPDATE … FROM` 은 조용히 하나를 고른다.

## 관련 자료

- [PostgreSQL 18 · MERGE](https://www.postgresql.org/docs/18/sql-merge.html) — `WHEN` 절의 정의, 동시성 주의, 중복 원본 규칙.
- [PostgreSQL 15 릴리스 노트](https://www.postgresql.org/docs/release/15.0/) — `MERGE` 도입.
- [PostgreSQL 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/) — `WHEN NOT MATCHED BY SOURCE` · `RETURNING` · `merge_action()`.
- [MySQL 8.4 · Data Manipulation Statements](https://dev.mysql.com/doc/refman/8.4/en/sql-data-manipulation-statements.html) — DML 문 목록에 `MERGE` 가 없다.
- [52 UPSERT — ON CONFLICT 와 ON DUPLICATE KEY UPDATE](../52-upsert/) — ★ **경계 선언: 「들어오는 행을 어떻게 반영하나」는 52, 「두 표를 어떻게 맞추나」는 53.**\
  충돌 대상 지정·영향 행 수·`EXCLUDED`·`INSERT IGNORE` 는 **전부 52 가 정본**이고 여기서 다시 쓰지 않는다.
- [`ops-patterns/06-idempotency-store`](../../../../../ops-patterns/06-idempotency-store/) — 멱등 처리 **패턴**은 거기, 여기는 **문법과 52 와의 경계**.
- [49 INSERT](../49-insert-multi-row-and-insert-select/) · [50 UPDATE](../50-update-with-join-and-subquery/) · [51 DELETE 와 TRUNCATE](../51-delete-and-truncate/) — `MERGE` 가 한 문으로 합치는 세 문.
- [54 RETURNING 과 변경문을 품은 CTE](../54-returning-and-data-modifying-cte/) — 8번의 `RETURNING` 이 거기가 정본이다.
- [19 SEMI·ANTI 조인](../19-semi-anti-join/) — 4번의 `DELETE … NOT IN` 우회가 왜 위험한가.
- [SQL 주제 목록](../README.md) — 55(트랜잭션 경계)·56(격리 수준)이 5번 (b) 의 이웃이다.

## 용어 풀이

- **`MERGE`** — 대상 표를 원본에 맞춰 삽입·갱신·삭제를 한 문으로 기술하는 문.\
  예: 받은 명부대로 기존 명부를 고치고, 명부에 없는 사람은 지우는 것.
- **대상(target)** — `MERGE INTO` 뒤의 표. 바뀌는 쪽이다.\
  예: `MERGE INTO t53_tgt t …` 의 `t53_tgt`.
- **원본(source)** — `USING` 뒤의 것. 표·서브쿼리·`VALUES` 목록이 될 수 있다.\
  예: `USING (VALUES (2,'bob9',77)) AS s(id,name,qty)`.
- **`WHEN MATCHED`** — `ON` 조건에 맞는 짝이 있는 대상 행에 적용되는 절.\
  예: `WHEN MATCHED AND s.qty > t.qty THEN UPDATE SET qty = s.qty`.
- **`WHEN NOT MATCHED`** — 원본에는 있는데 대상에 짝이 없는 행. 기본은 `BY TARGET` 이다.\
  예: 새로 등록해야 할 행이다.
- **`WHEN NOT MATCHED BY SOURCE`** — ★ 대상에는 있는데 원본에 짝이 없는 행(PG 17+).\
  예: 명부에서 빠진 사람 — upsert 로는 표현할 수 없는 자리다.
- **`merge_action()`** — `RETURNING` 안에서 그 행에 무엇이 일어났는지 돌려주는 함수(PG 17+).\
  예: `INSERT`·`UPDATE`·`DELETE` 중 하나를 문자열로 준다.
- **`DO NOTHING`** — 그 행에 아무것도 하지 않는 절. 영향 행 수에 안 들어간다.\
  예: 조건 있는 `WHEN MATCHED` 아래에 두어 「나머지는 그냥 두기」를 명시한다.
- **`ERROR 1064`** — MySQL 의 구문 오류. **파서가 그 낱말 자체를 모른다**는 뜻이다.\
  예: `MERGE` 는 여기서 막힌다 — 실행 경로가 없어 실패하는 `ERROR 3889`([23번](../23-grouping-sets-rollup-cube/))와 다르다.
- **동기화(synchronization)** — 한 표를 다른 표와 똑같은 내용으로 만드는 것.\
  예: 삽입·갱신·삭제 셋이 다 필요하므로 upsert 하나로는 안 된다.

## 더 들어가면

- **`MERGE` 로 「조건부 삭제」도 된다.** `WHEN MATCHED AND <조건> THEN DELETE` 형태다.

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING t53_src s ON t.id=s.id
  WHEN MATCHED AND s.qty >= 99 THEN DELETE
  WHEN MATCHED                 THEN UPDATE SET qty=s.qty
  WHEN NOT MATCHED             THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
MERGE 3
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |  10
  3 | cho  |  30
  4 | dan  |  40       <- id=2 는 s.qty=99 라 삭제됐다
(3 rows)
ROLLBACK;
```

- **`MERGE` 의 대상은 뷰일 수도 있다**(PG 문서). **이 편에서는 던져 보지 않았다** — [48 번](../48-views-and-materialized-views/)이 뷰의 정본이다.
- **`WHEN NOT MATCHED BY TARGET`** 은 `WHEN NOT MATCHED` 의 긴 이름이다. **이 편에서는 짧은 형태만 던졌다.**
- **다른 엔진의 `MERGE`** — Oracle·SQL Server 에도 있고 세부가 다르다.\
  **이 머신에 그 엔진이 없어 확인하지 않았다.** 이 편의 결론은 **PG 18.6 과 MySQL 8.4.10 에 한정**한다.
- **`MERGE` 가 잡는 잠금**은 `UPDATE`/`DELETE` 와 같은 행 잠금이다. 경쟁이 몰리면 대기·교착이 생긴다 —\
  [57 명시적 잠금과 교착](../57-explicit-locking-and-deadlock/) 주제다. **이 편에서는 동시 세션 실험을 하지 않았다.**
