# sql/53-MERGE — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **한쪽에서만 결론이 서는 주제다.** MySQL 쪽 출력은 **1번의 `ERROR 1064` 하나뿐**이고,\
> 2~12번의 동작 근거는 **전부 PostgreSQL 18.6** 이다. 7번은 **실행이 아니라 문서 문장**이 근거다.\
> 이 편이 만든 표(`t53_tgt`·`t53_src`·`t53_dup`)는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> 문서 근거는 [PG 18 MERGE](https://www.postgresql.org/docs/18/sql-merge.html) · [PG 15 릴리스 노트](https://www.postgresql.org/docs/release/15.0/) · [PG 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. ★ MySQL 에 `MERGE` — **`ERROR 1064` 구문 오류다**

**출력**

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

더 짧은 형태로도 같다.

```text
### SQL: MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.qty = s.qty;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ... near
  'MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id WHEN MATCHED THEN UPDATE SET' at line 1
```

**왜 그런가** — `1064` 는 **구문 오류**다. **파서가 `MERGE` 라는 낱말 자체를 모른다.**\
에러가 가리키는 위치가 **문장의 맨 앞**(`MERGE INTO …`)인 것이 그 증거다.

```text
ERROR 1064  파싱 단계에서 막힌다        -> 그 문법이 아예 없다     (MERGE)
ERROR 3889  파싱은 되고 실행 경로가 없다 -> 문법은 있는데 못 돈다   (CUBE — 23번)
```

★ **[23 번의 `CUBE`](../23-grouping-sets-rollup-cube/)와 구분되는 자리다.** 그쪽은 「문서 부재」를 실측으로 뒤집은 사례였고,\
여기는 **던져 본 결과가 문서와 일치**한다 — MySQL 8.4 의 DML 문 목록에 `MERGE` 가 없다.

★ **이것이 이 편에서 얻은 MySQL 쪽 근거의 전부다.** 아래 모든 동작 설명은 PG 의 것이다.

---

### 2. 기본형이 만드는 표 — **갱신 2 · 삽입 1 · 무변화 1, `MERGE 3`**

**출력**

```text
--- PG 18.6 ---
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED     THEN UPDATE SET name = s.name, qty = s.qty
  WHEN NOT MATCHED THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
MERGE 3
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |  10      <- 안 건드렸다 (원본에 없다)
  2 | bob2 |  99      <- 갱신
  3 | cho  |  30      <- 갱신 대상이었다 (값이 같아도)
  4 | dan  |  40      <- 삽입
(4 rows)
```

**왜 그런가**

```text
ON t.id = s.id 로 양쪽을 맞춘다

 id=1 : 대상에만 있다 -> ★ WHEN 절이 없으므로 아무 일도 안 한다
 id=2 : 양쪽에 있다   -> WHEN MATCHED     -> UPDATE
 id=3 : 양쪽에 있다   -> WHEN MATCHED     -> UPDATE (값이 같아도 갱신은 한다)
 id=4 : 원본에만 있다 -> WHEN NOT MATCHED -> INSERT
                                              계 3행 -> MERGE 3
```

`id=1` 이 안 바뀐 이유는 **`WHEN NOT MATCHED BY SOURCE` 절을 안 적었기** 때문이다(5번).\
[50 번 2절의 조인형 갱신](../50-update-with-join-and-subquery/)과 같은 규칙 — **짝 없는 행은 대상 집합 밖**이다.

---

### 3. `WHEN` 절의 순서 — **`id=3` 은 `DO NOTHING`, `MERGE 2`**

**출력**

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
  2 | bob  |  99      <- 99 > 20 이라 갱신 (name 은 SET 에 없어 그대로)
  3 | cho  |  30      <- 30 > 30 이 거짓 -> 둘째 절 DO NOTHING
  4 | dan  |  40      <- 삽입
(4 rows)
ROLLBACK;
```

**왜 그런가** — **`WHEN` 절은 위에서부터 처음 맞는 것 하나만** 실행된다.

```text
 id=3 : 첫째 WHEN MATCHED AND s.qty > t.qty -> 30 > 30 = 거짓 -> 건너뛴다
        둘째 WHEN MATCHED (조건 없음)        -> 맞는다 -> DO NOTHING
```

★ **`MERGE 2` 를 주목한다.** `DO NOTHING` 으로 처리된 행은 **영향 행 수에 안 들어간다.**\
갱신 1 + 삽입 1 = 2 다.

★ **순서가 의미다.** 조건 없는 `WHEN MATCHED` 를 위로 올리면 **아래 절은 죽은 코드**가 된다.

---

### 4. `WHEN NOT MATCHED` 를 빼면 — **조용히 넘어간다. 에러가 아니다**

**출력**

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED THEN UPDATE SET qty = s.qty;
MERGE 2
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |  10
  2 | bob  |  99
  3 | cho  |  30
(3 rows)                   <- ★ id=4 가 안 들어갔다. 에러도 없다
ROLLBACK;
```

**왜 그런가** — **맞는 `WHEN` 절이 없으면 그 행은 그냥 넘어간다.** 그것이 `MERGE` 의 기본 동작이다.

```text
 id=4 : NOT MATCHED 인데 그 절이 없다 -> 아무 일도 안 한다 -> 에러 없음
```

★ **무음 사고의 자리다.** 동기화 스크립트에서 `WHEN NOT MATCHED` 를 빠뜨리면\
**신규 행이 통째로 안 들어가는데 아무도 안 알려 준다.**

[49 번의 `INSERT 0 0`](../49-insert-multi-row-and-insert-select/)과 같은 종류다 — **영향 행 수(`MERGE n`)를 반드시 읽는다.**

---

### 5. ★★ `MERGE` 만 되는 일 — **`id=1` 이 삭제된다. upsert 한 문으로는 못 한다**

**출력**

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED               THEN UPDATE SET name=s.name, qty=s.qty
  WHEN NOT MATCHED           THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty)
  WHEN NOT MATCHED BY SOURCE THEN DELETE;
MERGE 4
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  2 | bob2 |  99
  3 | cho  |  30
  4 | dan  |  40
(3 rows)                   <- ★ id=1 이 사라졌다. 대상이 원본과 똑같아졌다
ROLLBACK;
```

**왜 그런가**

```text
MERGE 4 = 갱신 2 + 삽입 1 + ★ 삭제 1
          세 종류의 DML 이 한 문에서 일어났다
```

> "If the `WHEN` clause specifies `WHEN NOT MATCHED BY SOURCE` and the candidate change row represents a row in the target table that does not match a row in the `data_source`, the `WHEN` clause is executed if the `condition` is absent or it evaluates to `true`."\
> — [PostgreSQL 18 · MERGE](https://www.postgresql.org/docs/18/sql-merge.html)

**upsert 로는 안 된다 — 보는 범위가 다르기 때문이다.**

```text
upsert 가 보는 것 : 내가 VALUES/SELECT 로 준 행들
                    -> "대상 표에만 있는 행" 은 시야 밖이다
MERGE 가 보는 것  : 대상과 원본을 ON 으로 맞춘 결과 전체
                    -> ★ "원본에 없는 대상 행" 이라는 자리가 생긴다
```

**upsert 로 같은 일을 하려면 문이 둘 필요하다.**

```sql
INSERT INTO t53_tgt SELECT * FROM t53_src ON CONFLICT (id) DO UPDATE SET ...;  -- ①
DELETE FROM t53_tgt WHERE id NOT IN (SELECT id FROM t53_src);                  -- ②
```

★ 문이 둘이면 **원자 단위가 둘**이다 — 같은 보장을 얻으려면 한 트랜잭션에 넣어야 한다([55 트랜잭션 경계](../55-transaction-boundaries-commit-rollback-savepoint/)).\
그리고 `NOT IN` 대상에 `NULL` 이 섞이면 결과가 통째로 빈다 — [19 SEMI·ANTI 조인](../19-semi-anti-join/)이 정본이다.

★ **버전** — `WHEN NOT MATCHED BY SOURCE` 는 **PG 17 부터**다(10번).

---

### 6. ★★ upsert 만 되는 일 — **`MERGE` 는 죽고, `ON CONFLICT (name)` 은 처리한다**

**출력**

```text
--- PG 18.6 ---
ALTER TABLE t53_tgt ADD CONSTRAINT t53_tgt_name_uq UNIQUE (name);
ALTER TABLE

MERGE INTO t53_tgt t USING (SELECT 9 AS id, 'ann' AS name, 5 AS qty) s ON t.id = s.id
  WHEN MATCHED     THEN UPDATE SET qty = s.qty
  WHEN NOT MATCHED THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
ERROR:  duplicate key value violates unique constraint "t53_tgt_name_uq"
DETAIL:  Key (name)=(ann) already exists.
```

```text
--- PG 18.6 ---
BEGIN;
INSERT INTO t53_tgt (id,name,qty) VALUES (9,'ann',5)
  ON CONFLICT (name) DO UPDATE SET qty = EXCLUDED.qty;
INSERT 0 1
SELECT * FROM t53_tgt ORDER BY id;
 id | name | qty 
----+------+-----
  1 | ann  |   5      <- ★ name 으로 찾아 기존 행을 갱신했다
  2 | bob  |  20
  3 | cho  |  30
(3 rows)
ROLLBACK;
```

**왜 그런가 — 「같은 행인지」를 정하는 것이 다르다.**

```text
MERGE                                   INSERT ... ON CONFLICT
+-----------------------------+         +-----------------------------+
| 같은 행인지를 ON 이 정한다   |         | 같은 행인지를 "제약" 이 정한다 |
| id=9 는 대상에 없다          |         | name='ann' 이 name_uq 에 걸린다|
| -> NOT MATCHED -> INSERT     |         | -> 그 행을 찾아 UPDATE         |
| -> ★ name 제약 위반으로 죽음 |         | -> 성공                        |
+-----------------------------+         +-----------------------------+
```

**`MERGE` 의 `ON` 은 조인 조건이지 제약이 아니다.**\
[52 번](../52-upsert/)의 「충돌 대상을 지목한다」가 **여기서 `MERGE` 와 갈리는 자리**다.

---

### 7. 동시 삽입에는 무엇을 쓰나 — **문서가 `INSERT … ON CONFLICT` 를 권한다**

**근거 — 실행이 아니라 문서 문장이다.**

> "When `MERGE` is run concurrently with other commands that modify the target table, the usual transaction isolation rules apply; see Section 13.2 for an explanation on the behavior at each isolation level. **You may also wish to consider using `INSERT ... ON CONFLICT` as an alternative statement which offers the ability to run an `UPDATE` if a concurrent `INSERT` occurs. There are a variety of differences and restrictions between the two statement types and they are not interchangeable.**"\
> — [PostgreSQL 18 · MERGE](https://www.postgresql.org/docs/18/sql-merge.html)

**왜 그런가**

```text
MERGE 의 ON 은 "문이 시작될 때 본 스냅숏" 으로 짝을 맞춘다

  시각 t0 : MERGE 가 id=9 를 본다 -> 대상에 없다 -> NOT MATCHED 로 판정
  시각 t1 : 다른 세션이 id=9 를 INSERT 하고 커밋
  시각 t2 : MERGE 가 INSERT 를 실행 -> ★ 유니크 위반으로 죽을 수 있다

INSERT ... ON CONFLICT 는 그 상황을 "충돌" 로 보고 UPDATE 로 전환한다
```

★ **이 경쟁 상황은 이 편에서 재현하지 않았다** — 세션 둘을 띄워 타이밍을 맞추는 실험을 하지 않았다.\
**근거는 위 문서 문장 하나**이고, 그 사실을 여기 밝힌다.\
(동시성 자체는 [56 격리 수준](../56-isolation-levels-read-phenomena-mvcc/)·[57 명시적 잠금과 교착](../57-explicit-locking-and-deadlock/) 주제다.)

★ **문서가 「서로 바꿔 쓸 수 없다」고 직접 적은 것**이 이 편의 경계 선언이다.

---

### 8. 원본에 중복이 있으면 — **에러다. `UPDATE … FROM` 은 조용히 하나를 고른다**

**출력**

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

**왜 그런가** — 두 문이 **같은 규칙을 지킨다.** 문구만 다르다.

> "You should ensure that the join produces at most one candidate change row for each target row. … If it does, then only one of the candidate change rows will be used to modify the target row; **later attempts to modify the row will cause an error**."\
> — [PostgreSQL 18 · MERGE](https://www.postgresql.org/docs/18/sql-merge.html)

★ **`UPDATE … FROM` 과 대비된다.**

```text
같은 중복 원본을 던졌을 때 ([50번 6절])

UPDATE ... FROM        : 조용히 둘 중 하나를 쓴다 (문서: not readily predictable)
MERGE                  : ★ 거부한다
INSERT ... ON CONFLICT : ★ 거부한다
```

**중복 원본이 있을 수 있는 배치라면 `MERGE`/upsert 쪽이 안전하다** — 상류의 버그가 드러난다.\
**처방** — 원본을 먼저 접는다(`GROUP BY`·`DISTINCT ON`).

---

### 9. 무엇을 했는지 돌려받기 — **행마다 `INSERT`/`UPDATE`/`DELETE` 가 찍힌다**

**출력**

```text
--- PG 18.6 ---
BEGIN;
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED               THEN UPDATE SET qty = s.qty
  WHEN NOT MATCHED           THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty)
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

원본이 `VALUES` 목록이어도 같다.

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

**왜 그런가** — `merge_action()` 이 **그 행을 만든 DML 의 이름**을 돌려준다.

★ **[52 번](../52-upsert/)에서 「삽입인지 갱신인지」를 `xmax = 0` 관용구로 추정했던 것과 대비된다** —\
그쪽은 문서화된 계약이 아니었고, 이쪽은 **문서화된 함수**다.

★ `DELETE` 행의 `t.name`·`t.qty` 가 **지워지기 전 값**으로 나온 것도 주목한다 —\
`RETURNING` 의 `OLD`/`NEW` 규칙이 [54 번](../54-returning-and-data-modifying-cte/)에 있다.

---

### 10. 버전 — **`MERGE` 는 15+, `NOT MATCHED BY SOURCE`·`RETURNING` 은 17+**

**근거 — 릴리스 노트다.**

> "Add SQL `MERGE` command to adjust one table to match another (Simon Riggs, Pavan Deolasee, Álvaro Herrera, Amit Langote) … This is similar to `INSERT ... ON CONFLICT` but more batch-oriented."\
> — [PostgreSQL 15 릴리스 노트](https://www.postgresql.org/docs/release/15.0/)

> "Add `WHEN NOT MATCHED BY SOURCE` to `MERGE` (Dean Rasheed) … `WHEN NOT MATCHED` on target rows was already supported."\
> — [PostgreSQL 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/)

> "Allow `MERGE` to use the `RETURNING` clause (Dean Rasheed) … The new `RETURNING` function `merge_action()` reports on the DML that generated the row."\
> — [PostgreSQL 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/)

```text
PG 15 : MERGE 도입 (WHEN MATCHED · WHEN NOT MATCHED)
PG 16 : (이 편에서 다루는 변화 없음)
PG 17 : WHEN NOT MATCHED BY SOURCE · RETURNING · merge_action()
PG 18 : 이 편의 실행 환경 (18.6)
```

★ **15 릴리스 노트가 스스로 `ON CONFLICT` 와의 관계를 적는다** — 「비슷하지만 더 배치 지향」.\
그 한 줄이 [52 번과의 경계](../52-upsert/)를 문서 수준에서 뒷받침한다.

★ **PG 15·16·17 컨테이너가 없어 옛 버전에서의 거부는 직접 재현하지 못했다.**\
**버전 표기의 근거는 릴리스 노트이지 실행 출력이 아니다.**

---

### 11. 52 와의 경계 — **「들어오는 행을 반영」이 52, 「두 표를 맞춤」이 53**

```text
요구사항이 무엇인가
│
├─ "이 행들을 있으면 갱신, 없으면 삽입"
│    -> ★ 52 UPSERT. 두 엔진 다 된다. 동시 삽입에도 강하다 (7번)
│
├─ "이 행들 + 목록에 없는 기존 행은 삭제" (동기화)
│    -> ★ 53 MERGE (PG 17+). MySQL 은 문 둘 + 트랜잭션 (5번)
│
├─ "조건에 따라 갱신/삭제/무시를 갈라야 한다"
│    -> ★ 53 MERGE (3번)
│
└─ "어느 제약에서 충돌하는지 지목해야 한다"
     -> ★ 52 UPSERT (6번)
```

| | [52 UPSERT](../52-upsert/) | 53 `MERGE` |
|---|---|---|
| 무엇을 보나 | **내가 넣으려는 행** | **대상과 원본을 맞춘 결과 전체** |
| 삭제 | 못 한다 | 된다(`WHEN … THEN DELETE`) |
| 충돌 대상 지목 | **된다** | 안 된다 — `ON` 은 조인 조건 |
| 동시 삽입 | **문서가 권한다** | 문서가 `ON CONFLICT` 를 대안으로 제시 |
| MySQL 8.4.10 | `ON DUPLICATE KEY UPDATE` | **없다** |

★ **한 줄 선언** — **「들어오는 행을 어떻게 반영하나」는 52, 「두 표를 어떻게 맞추나」는 53.**\
충돌 대상 지정·영향 행 수·`EXCLUDED`·`INSERT IGNORE` 는 **전부 52 가 정본**이고 이 편에서 다시 쓰지 않는다.

---

### 12. 원본이 비어 있으면 — **대상 표가 통째로 비워진다**

**출력**

```text
--- PG 18.6 ---
BEGIN;
DELETE FROM t53_src;
DELETE 3
MERGE INTO t53_tgt t USING t53_src s ON t.id=s.id
  WHEN MATCHED               THEN UPDATE SET name=s.name, qty=s.qty
  WHEN NOT MATCHED           THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty)
  WHEN NOT MATCHED BY SOURCE THEN DELETE;
MERGE 3
SELECT count(*) AS n FROM t53_tgt;
 n 
---
 0          <- ★ 세 행이 전부 지워졌다
(1 row)
ROLLBACK;
```

**왜 그런가** — 원본이 0행이면 **대상의 모든 행이 `NOT MATCHED BY SOURCE`** 가 된다.

```text
원본 0행 -> 짝이 있는 대상 행이 하나도 없다
         -> 전부 WHEN NOT MATCHED BY SOURCE THEN DELETE 로 간다
         -> 표가 비워진다. 에러도 경고도 없다
```

★ **동기화 스크립트에서 가장 위험한 실패 모드다.**\
원본을 가져오는 API 가 빈 응답을 주거나, 임시 표 적재가 실패해 0행이면\
**「동기화」가 「전체 삭제」가 된다.**

**처방 두 가지.**

```sql
-- ① 원본 행 수를 먼저 검사한다 (애플리케이션에서)
SELECT count(*) FROM t53_src;   -- 0 이면 MERGE 를 아예 던지지 않는다

-- ② 삭제 조건을 좁힌다
WHEN NOT MATCHED BY SOURCE AND t.updated_at < <이번 적재 시각> THEN DELETE
```

★ **`MERGE 3` 이라는 영향 행 수가 유일한 신호**인데, 그것도 「세 행을 처리했다」로 읽으면 이상할 게 없다.\
[51 번의 `WHERE` 없는 `DELETE`](../51-delete-and-truncate/)와 같은 종류의 위험이 **정상적인 문법으로 포장된 자리**다.

---

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 표 3개 생성·삭제 | PG 18.6 · MySQL 8.4.10 | 각 3회 | `t53_tgt`·`t53_src`·`t53_dup`(PG 만) |
| ★ `MERGE` 투척 (1번) | MySQL 8.4.10 | **2회** | **긴 형태·짧은 형태 둘 다 `ERROR 1064`** |
| 기본형 (2번) | PG 18.6 | 2회 | `MERGE 3` + `SELECT` 확인 |
| 조건부 `WHEN` + `DO NOTHING` (3번) | PG 18.6 | 2회 | **`MERGE 2` — `DO NOTHING` 은 안 센다** |
| `WHEN NOT MATCHED` 생략 (4번) | PG 18.6 | 2회 | **에러 없이 `id=4` 가 안 들어갔다** |
| ★★ `NOT MATCHED BY SOURCE` (5번) | PG 18.6 | 2회 | **`MERGE 4` — 삭제 1 포함** |
| ★★ `ON` 밖의 유니크 제약 (6번) | PG 18.6 | 3회 | **제약 추가 → `MERGE` 에러 → `ON CONFLICT` 성공 → 제약 제거** |
| 원본 중복 (8번) | PG 18.6 | 2회 | **`MERGE` 와 `ON CONFLICT` 가 같은 규칙, 다른 문구** |
| `RETURNING merge_action()` (9번) | PG 18.6 | 2회 | **표 원본 · `VALUES` 원본 각 1회** |
| `WHEN MATCHED THEN DELETE` (더 들어가면) | PG 18.6 | 1회 | 조건부 삭제 — `MERGE 3` |
| ★ 원본이 빈 경우 (12번) | PG 18.6 | 1회 | **대상 3행이 전부 지워졌다** |

**실행으로 확인하지 않은 것 — 근거가 문서인 자리**

| 항목 | 근거 |
|---|---|
| 7번 **동시 삽입** | [PG 18 MERGE 문서](https://www.postgresql.org/docs/18/sql-merge.html) 의 Notes — 세션 둘을 띄운 경쟁 실험은 하지 않았다 |
| 10번 **도입 버전** | [PG 15](https://www.postgresql.org/docs/release/15.0/) · [PG 17 릴리스 노트](https://www.postgresql.org/docs/release/17.0/) — **15·16·17 컨테이너가 없다** |
| MySQL 의 **대응물이 없다** | 8.4 DML 문 목록 + 1번의 `ERROR 1064` |

**구현 의존 항목** — 1번의 **에러 번호**, 2·3·5번의 **영향 행 수 세는 법**, 6·8번의 **에러 문구**.\
외울 것은 문구가 아니라 「**`MERGE` 는 두 표를 맞추고 upsert 는 들어오는 행을 반영한다**」는 성질이다.

**언어 보장 항목** — 3·4·5·8번.\
`WHEN` 절이 위에서부터 하나만 실행된다는 것, 맞는 절이 없으면 넘어간다는 것,\
`NOT MATCHED BY SOURCE` 의 의미, 한 대상 행에 원본이 둘 맞으면 에러라는 것은 **PG 문서가 정한 것**이다.\
★ **MySQL 쪽에는 이 항목들에 대응하는 보장이 존재하지 않는다** — 문법 자체가 없다.

**버전을 적은 자리** — 10번 전부(15 · 17).\
**버전을 못 적은 자리** — MySQL 이 `MERGE` 를 **언제 추가할지**(예고가 매뉴얼에 없다).

**돌려 보지 않은 것** — ① 동시 세션 경쟁(7번) ② PG 15·16·17 에서의 거부(10번)\
③ 뷰를 대상으로 한 `MERGE` ④ `WHEN NOT MATCHED BY TARGET` 긴 형태 ⑤ Oracle·SQL Server 의 `MERGE`(엔진이 없다).

**DB 잔재** — 없다. `t53_` 로 시작하는 표를 두 엔진에서 전부 삭제했고,\
6번에서 추가한 `t53_tgt_name_uq` 제약도 **실험 직후 `DROP CONSTRAINT` 로 되돌렸다.**\
`emp`·`dept` 는 **읽지도 쓰지도 않았다.**\
두 엔진의 최종 표 목록은 [54 편의 「실행 검증」](../54-returning-and-data-modifying-cte/3-answer.md)에 있다.
