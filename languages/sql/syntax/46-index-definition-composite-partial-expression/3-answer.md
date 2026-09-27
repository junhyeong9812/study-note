# sql/46-인덱스 정의 (복합·부분·표현식·커버링) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 20,000행짜리 `t46` 과 그 위의 인덱스는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> ★ **범위** — 여기는 **정의**까지다. **「탈까 안 탈까」는 [47번]**(../47-when-indexes-are-used/)이 정본이다.\
> 문서 근거는 [PG 18 CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html) · [MySQL 8.4 CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 복합 인덱스가 저장하는 순서 — **사전순. 앞 열이 먼저다**

```text
CREATE INDEX i ON t46 (a, b)  가 만드는 순서

  (0, 0)   (0, 1)   (0, 2)  ...  (0, 9)
  (1, 0)   (1, 1)   (1, 2)  ...  (1, 9)
  (2, 0)   ...
   ...
  (99, 0)  (99, 1)  ...          (99, 9)
   ^^^      ^^^
   a 로     같은 a 안에서
   먼저     b 로 다시
```

**이 그림이 왼쪽 접두 규칙의 전부다.**

```text
WHERE a=7 AND b=7   ->  (7,7) 한 지점             -> 바로 짚는다
WHERE a=7           ->  (7,0)~(7,9) 연속 구간     -> 좁힐 수 있다
WHERE b=7           ->  (0,7) (1,7) ... (99,7)    -> ★ 흩어져 있다. 못 좁힌다
```

> **왼쪽 접두 규칙(leftmost prefix)** — 복합 인덱스는 선언한 열 순서의 **앞쪽부터 연속으로** 쓸 때만 쓸모가 있다.\
> 예: `(a,b,c)` 인덱스는 `a`·`(a,b)`·`(a,b,c)` 에 쓰이고 `b` 만으로는 안 쓰인다.

**실제 계획 출력은 [47 번 1번](../47-when-indexes-are-used/)에 있다.** 여기서는 정렬 순서까지다.

---

### 2. ★ `(a,b)` 와 `(b,a)` — **다른 인덱스다**

```text
(a, b) 인덱스                       (b, a) 인덱스
+-----------------------+           +-----------------------+
| a 로 먼저 정렬         |           | b 로 먼저 정렬         |
| WHERE a=7     : 된다   |           | WHERE a=7     : ★ 안 된다 |
| WHERE b=7     : 안 된다 |           | WHERE b=7     : 된다   |
| WHERE a=7,b=7 : 된다   |           | WHERE a=7,b=7 : 된다   |
+-----------------------+           +-----------------------+
```

**갈리는 것은 「한 열만 조건에 걸릴 때**」다. 두 열이 다 걸리면 둘 다 쓸 수 있다.

**그래서 순서를 정하는 기준은 「어느 열이 단독으로도 자주 쓰이나」다.**

```text
a 단독 + (a,b) 를 쓴다     ->  (a, b) 하나로 둘 다 덮는다
b 단독 + (a,b) 를 쓴다     ->  (b, a) 로 만든다
a 단독도 b 단독도 쓴다      ->  인덱스 둘. 쓰기 비용이 두 배가 된다
```

★ **열 순서는 `CREATE INDEX` 를 쓸 때 정해지고 나중에 못 바꾼다** — 바꾸려면 지우고 다시 만든다.\
그래서 이것이 **「정의」의 문제**이고 이 편에 있다.

---

### 3. ★ 부분 인덱스 — **PG 만 된다. 20,000 중 20행만 들어간다**

**출력**

```text
### SQL: CREATE INDEX t46_part_idx ON t46 (id) WHERE status = 'ACTIVE';
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'WHERE status = 'ACTIVE'' at line 1
```

**크기를 재어 확인했다.**

```text
--- PG 18.6 ---
CREATE INDEX t46_full_idx ON t46 (id);      -- 비교용 전체 인덱스
SELECT indexrelname, pg_size_pretty(pg_relation_size(indexrelid)) AS size
  FROM pg_stat_user_indexes WHERE relname='t46'
    AND indexrelname IN ('t46_part_idx','t46_full_idx');
 indexrelname |  size  
--------------+--------
 t46_full_idx | 456 kB
 t46_part_idx | 16 kB
(2 rows)
```

**왜 그런가**

`status='ACTIVE'` 인 행은 **20행**(`id % 1000 = 0`)이다.\
같은 `id` 열에 건 인덱스인데 크기가 **456 kB 대 16 kB** 다 — 담긴 행 수가 다르기 때문이다.

★ **크기는 이 서버에서 잰 관찰이다.** 페이지 크기·채움률에 따라 달라진다.\
읽을 것은 절댓값이 아니라 **자릿수 차이**다.

---

### 4. 부분 인덱스가 줄이는 두 가지 — **크기와 쓰기 비용**

```text
일반 인덱스 (t46_full_idx)          부분 인덱스 (t46_part_idx)
+---------------------------+       +---------------------------+
| 20,000개 항목 · 456 kB     |       | 20개 항목 · 16 kB          |
+---------------------------+       +---------------------------+
          ↓                                   ↓
(1) 탐색할 자료가 작다                 (1) 훨씬 작다
(2) DONE 행을 INSERT/UPDATE 해도       (2) ★ DONE 행은 인덱스에 들어가지도
    인덱스를 갱신해야 한다                  갱신되지도 않는다
```

두 그림의 결론 — **부분 인덱스는 읽기뿐 아니라 쓰기도 싸게 만든다.**\
19,980개의 `DONE` 행에 대한 쓰기는 이 인덱스를 **건드리지 않는다.**

**대가** — 질의에 그 조건이 없으면 **후보가 되지 못한다.**\
`WHERE status='ACTIVE' AND id=...` 는 쓰이고 `WHERE id=...` 만으로는 안 쓰인다.

**MySQL 의 대안** — [45 번의 생성 열](../45-check-not-null-default-generated-columns/) + 인덱스.\
단 **완전히 같지 않다.** 부분 인덱스는 **인덱스에 아예 안 들어가고**, 생성 열은 **`NULL` 로 들어간다.**

---

### 5. ★ 표현식 인덱스의 괄호 — **(a) PG 만 / (b) 양쪽 다**

**출력**

```text
### SQL: CREATE INDEX t46_expr_idx ON t46 (lower(v));
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'v))' at line 1
```

```text
### SQL: CREATE INDEX t46_expr2_idx ON t46 ((lower(v)));
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
(성공)
```

**왜 그런가**

```text
(lower(v))      MySQL 파서는 'lower' 를 열 이름으로 읽기 시작한다
                그 다음 '(' 에서 막힌다 -> near 'v))'

((lower(v)))    바깥 괄호가 「이건 식이다」라는 표시가 된다
                PG 에서는 그 괄호가 그냥 무시된다
        ↓
  ★ 괄호 둘이 이식 가능한 형태다
```

**MySQL 이 무엇을 만들었는지 확인했다.**

```text
--- MySQL 8.4.10 ---
SHOW INDEX FROM t46;   (폭에 맞춰 일부 칸만 옮겼다)
+-------+---------------+-------------+----------+------------+
| Table | Key_name      | Column_name | Sub_part | Expression |
+-------+---------------+-------------+----------+------------+
| t46   | t46_expr2_idx | NULL        |     NULL | lower(`v`) |
+-------+---------------+-------------+----------+------------+
                          ↑ 열이 없다              ↑ 식이 들어 있다
```

**대가** — 그 식과 **똑같은 식**으로 질의해야 쓰인다.\
`lower(v)` 인덱스는 `WHERE upper(v)=...` 에 안 쓰인다. **계획 비교는 [47 번 2번](../47-when-indexes-are-used/)에 있다.**

---

### 6. ★ 접두 길이 — **MySQL 만. PG 는 함수 호출로 읽는다**

**출력**

```text
### SQL: CREATE INDEX t46_pref_idx ON t46 (code(10));
--- PG 18.6 ---
ERROR:  function code(integer) does not exist
LINE 1: CREATE INDEX t46_pref_idx ON t46 (code(10));
                                          ^
HINT:  No function matches the given name and argument types. You might need to add
  explicit type casts.
--- MySQL 8.4.10 ---
(성공)
```

**왜 PG 의 문구가 저런가**

```text
PG 에는 "접두 길이" 문법이 없다
        ↓
code(10) 을 식으로 파싱한다
        ↓
"code 라는 이름의 함수에 정수 10 을 넘겼다" 로 읽는다
        ↓
그런 함수가 없다 -> function code(integer) does not exist
```

★ **5번과 이어 읽으면 같은 규칙이다** — PG 에서 **`이름(...)` 은 표현식 인덱스의 함수 호출로 읽힌다.**

**MySQL 이 만든 것.**

```text
--- MySQL 8.4.10 ---
+-------+--------------+-------------+----------+
| Table | Key_name     | Column_name | Sub_part |
+-------+--------------+-------------+----------+
| t46   | t46_pref_idx | code        |       10 |    <- Sub_part = 10
+-------+--------------+-------------+----------+
```

**PG 의 대안** — `CREATE INDEX i ON t ((left(v,10)))`.\
단 질의도 `left(v,10)` 으로 써야 한다(5번의 대가).

---

### 7. 커버링 — **`INCLUDE` 는 PG 만. `(a,b)` 와 뜻이 다르다**

**출력**

```text
### SQL: CREATE INDEX t46_inc_idx ON t46 (a) INCLUDE (b);
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'INCLUDE (b)' at line 1
```

**`(a,b)` 와 무엇이 다른가**

```text
CREATE INDEX i ON t (a, b)              CREATE INDEX i ON t (a) INCLUDE (b)
+---------------------------+           +---------------------------+
| 정렬 키: a, b             |           | 정렬 키: a                |
| b 로도 정렬돼 있다         |           | b 는 "그냥 들고만" 있다    |
+---------------------------+           +---------------------------+
  WHERE a=7 AND b=7 을 좁힌다             ★ b 조건에는 못 쓴다
  UNIQUE (a,b) 를 만들 수 있다            UNIQUE 는 a 에만 걸린다
  인덱스가 더 크다 (정렬 정보가 는다)       조금 작다
```

**둘 다 커버링은 된다** — `SELECT b FROM t WHERE a=7` 을 표 없이 답한다.

> **커버링 인덱스(covering index)** — 질의가 필요한 열을 인덱스가 전부 갖고 있어 **표를 안 읽는** 경우.\
> 예: PG 의 `Index Only Scan`, MySQL 의 `Extra: Using index` 가 그 표시다([47 번 4번](../47-when-indexes-are-used/)).

**MySQL 의 대안** — `INCLUDE` 가 없으므로 **복합 인덱스 `(a, b)`** 로 만든다.

---

### 8. ★ `UNIQUE` 인덱스와 `UNIQUE` 제약 — **PG 는 구분하고 MySQL 은 안 한다**

**PG 의 두 카탈로그**

```text
--- PG 18.6 ---
SELECT indexname FROM pg_indexes WHERE tablename='t46';
   indexname   
---------------
 ...
 t46_ucon             <- (B) 도 인덱스로는 보인다
 t46_uix              <- (A)

SELECT conname, contype FROM pg_constraint WHERE conrelid='t46'::regclass;
       conname       | contype 
---------------------+---------
 t46_pkey            | p
 t46_ucon            | u        <- (B) 만 제약으로도 보인다
 ...                             ★ t46_uix 는 여기 없다
```

**MySQL 은 한 목록뿐이다.**

```text
--- MySQL 8.4.10 ---
SHOW INDEX FROM t46;   (Non_unique=0 이 유일 인덱스다)
+-------+------------+----------+-------------+
| Table | Non_unique | Key_name | Column_name |
+-------+------------+----------+-------------+
| t46   |          0 | PRIMARY  | id          |
| t46   |          0 | t46_uix  | code        |
| t46   |          0 | t46_ucon | v           |     <- (A) 와 (B) 를 구분할 칸이 없다
+-------+------------+----------+-------------+
```

**왜 그런가**

```text
ADD CONSTRAINT ... UNIQUE   ->  제약 1개 + 그것을 받치는 인덱스 1개
CREATE UNIQUE INDEX         ->  인덱스 1개. 제약은 없다
```

**PG 에서 이 구분이 실무에 미치는 영향 둘**

```text
(1) 외래키가 가리킬 수 있나
     -> 제약이 있어야 한다. CREATE UNIQUE INDEX 로 만든 것은 못 가리킨다 (44번 12번)
(2) 지울 때 (9번)
```

---

### 9. 지울 때 — **제약이 받치는 인덱스는 `DROP INDEX` 로 못 지운다**

**출력**

```text
--- PG 18.6 ---
DROP INDEX t46_ucon;
ERROR:  cannot drop index t46_ucon because constraint t46_ucon on table t46 requires it
HINT:  You can drop constraint t46_ucon on table t46 instead.

DROP INDEX t46_uix;
DROP INDEX
```

**MySQL 에는 저항이 없다.**

```text
--- MySQL 8.4.10 ---
DROP INDEX t46_ucon ON t46;
(성공)
```

**왜 그런가**

```text
PG    : 제약이 그 인덱스에 "의존" 한다 -> 42번의 DROP 의존성 검사와 같은 구조다
        제약을 지우면 인덱스도 같이 사라진다:  ALTER TABLE t46 DROP CONSTRAINT t46_ucon;
MySQL : 제약과 인덱스가 같은 것이라 지울 것이 하나뿐이다
```

★ **`DROP INDEX` 의 형태도 다르다.**

```text
PG    : DROP INDEX i;          인덱스 이름이 스키마에서 유일하다
MySQL : DROP INDEX i ON t;     인덱스가 표에 딸려 있어 표 이름이 필요하다
```

---

### 10. 조건부 유일성 — **제약으로는 못 쓰고 인덱스로는 쓴다**

**출력**

```text
--- PG 18.6 ---
ALTER TABLE t46 ADD CONSTRAINT t46_pu UNIQUE (code) WHERE status='ACTIVE';
ERROR:  syntax error at or near "WHERE"
LINE 1: ...TER TABLE t46 ADD CONSTRAINT t46_pu UNIQUE (code) WHERE stat...
                                                             ^

CREATE UNIQUE INDEX t46_pu ON t46 (code) WHERE status='ACTIVE';
CREATE INDEX
```

**무엇을 뜻하는가**

```text
"code 는 status='ACTIVE' 인 행끼리만 유일하다"
        ↓
제약 문법에는 이런 표현이 없다 (제약은 표 전체에 걸린다)
        ↓
부분 유니크 인덱스로만 표현된다
```

[43 번 12번의 네 번째 선택지](../43-primary-key-unique-and-null/)가 이것이다 —\
「소프트 삭제된 행은 빼고 유일」 같은 요구가 이 형태로 풀린다.

**대가** — 제약이 아니므로 **외래키가 이 열을 가리킬 수 없다**(8번).\
그리고 **MySQL 에는 이 수단이 없다**(3번의 `ERROR 1064` 가 근거다).

---

### 11. ★ 생성 열에 인덱스 — **PG 18 은 `VIRTUAL` 에 못 건다**

**출력**

```text
### SQL: CREATE INDEX t45_gv_idx ON t45_gv (total);       (total 이 VIRTUAL)
--- PG 18.6 ---
ERROR:  indexes on virtual generated columns are not supported
--- MySQL 8.4.10 ---
(성공)

### SQL: CREATE INDEX t45_gs_idx ON t45_gs (total);       (total 이 STORED)
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
(성공)
```

**[45 번 9번](../45-check-not-null-default-generated-columns/)과 이어 읽으면 함정이 보인다.**

```text
PostgreSQL 18 에서
  total int GENERATED ALWAYS AS (price*qty)     <- STORED 를 안 썼다
        ↓
  기본값이 VIRTUAL 이다 (★ 18 부터 바뀌었다)
        ↓
  CREATE INDEX 가 거부된다
        ↓
  "생성 열로 계산값을 만들고 인덱스로 검색하겠다" 가 여기서 막힌다
```

★ **PG 17 에서 쓰던 스크립트를 18 로 옮기면 이 자리가 깨진다.**\
17 에서는 키워드를 빼면 에러였거나 `STORED` 였으므로 인덱스가 걸렸다\
(**17 을 직접 던져 보지는 못했다** — 근거는 [18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)다).

**처방** — **인덱스를 걸 생성 열에는 `STORED` 를 명시한다.**

---

### 12. 인덱스를 만들 때 무엇이 잠기나 — **`ShareLock`. `ALTER` 보다 약하다**

**출력**

```text
--- PG 18.6 ---
BEGIN;
CREATE INDEX t46_lock_idx ON t46 (status);
SELECT l.mode FROM pg_locks l JOIN pg_class c ON c.oid=l.relation WHERE c.relname='t46';
   mode    
-----------
 ShareLock
(1 row)
ROLLBACK;
```

**[42 번 6번](../42-create-alter-drop-table/)과 나란히 놓으면 차이가 선다.**

```text
CREATE INDEX          ShareLock            읽기는 된다. 쓰기가 막힌다
ALTER TABLE           AccessExclusiveLock  ★ 읽기까지 막힌다
```

**그래서 운영에서의 성격이 다르다.**

```text
CREATE INDEX 를 도는 동안
  SELECT          : 통과한다
  INSERT/UPDATE   : 대기한다
        ↓
읽기 전용 서비스는 멀쩡해 보이고 쓰기만 멈춘다
```

**MySQL 쪽은 [42 번의 `ALGORITHM`/`LOCK` 절](../42-create-alter-drop-table/)로 같은 것을 요구한다.**

```text
--- MySQL 8.4.10 ---
ALTER TABLE t42_b ADD INDEX (v), ALGORITHM=INPLACE, LOCK=NONE;
(성공 — 아무 출력 없음)
```

---

### 13. `CONCURRENTLY` 의 대가 — **트랜잭션 안에서 못 돈다**

**출력**

```text
--- PG 18.6 ---
CREATE INDEX CONCURRENTLY t46_cc_idx ON t46 (status);
CREATE INDEX                                   <- 트랜잭션 밖에서는 된다

BEGIN; CREATE INDEX CONCURRENTLY t46_cc2_idx ON t46 (b); COMMIT;
BEGIN
ERROR:  CREATE INDEX CONCURRENTLY cannot run inside a transaction block
```

**왜 그런가**

```text
CONCURRENTLY 는 표를 두 번 훑으며, 그 사이 다른 트랜잭션의 쓰기를 기다린다
        ↓
자기 자신이 긴 트랜잭션 안에 있으면 그 기다림이 성립하지 않는다
        ↓
아예 금지한다
```

**두 가지 대가가 더 있다.**

```text
(1) 표를 두 번 훑으므로 느리다
(2) 실패하면 "쓸 수 없는(INVALID) 인덱스" 가 남는다 — 찾아서 지워야 한다
    ★ 이 실험에서 실패 상황은 만들어 보지 않았다
```

★ **[42 번 3번](../42-create-alter-drop-table/)의 「PG 는 DDL 을 롤백할 수 있다」에 대한 예외**다.\
이 문만은 트랜잭션에 넣을 수 없다 — 마이그레이션 도구가 여기서 자주 걸린다.

---

### 14. ★ `USING HASH` — **자리가 다르고, MySQL 은 받고도 무시한다**

**출력**

```text
### SQL: CREATE INDEX t46_hash_idx ON t46 (b) USING HASH;
--- PG 18.6 ---
ERROR:  syntax error at or near "USING"
LINE 1: CREATE INDEX t46_hash_idx ON t46 (b) USING HASH;
                                             ^
--- MySQL 8.4.10 ---
(성공)
```

```text
### SQL: CREATE INDEX t46_hash2_idx ON t46 USING hash (b);
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... right syntax to use near 'USING hash (b)' at line 1
```

**★ MySQL 이 받은 것이 무엇이 됐나**

```text
--- MySQL 8.4.10 ---
SHOW INDEX FROM t46 WHERE Key_name='t46_hash_idx'\G
     Key_name: t46_hash_idx
  Column_name: b
   Index_type: BTREE          <- ★ HASH 가 아니다
```

**PG 쪽은 요청한 대로다.**

```text
--- PG 18.6 ---
SELECT indexdef FROM pg_indexes WHERE indexname='t46_hash2_idx';
 CREATE INDEX t46_hash2_idx ON public.t46 USING hash (b)
```

**왜 그런가**

```text
PG    : USING 이 열 목록 "앞" 에 온다        -> 뒤에 오면 문법 에러
MySQL : USING 이 열 목록 "뒤" 에 온다        -> 문법은 통과한다
        그런데 InnoDB 는 명시적 해시 인덱스를 지원하지 않는다
        -> 조용히 BTREE 로 만든다
```

★ **[44 번의 열 뒤 `REFERENCES`](../44-foreign-key-referential-actions/) 와 같은 종류의 조용한 무시**다.\
**문법이 통과했다는 것이 요청대로 만들어졌다는 뜻이 아니다** — `SHOW INDEX` 로 확인해야 한다.

---

### 15. 없는 열에 — **양쪽 다 즉시 막는다**

**출력**

```text
### SQL: CREATE INDEX t46_bad_idx ON t46 (nosuch);
--- PG 18.6 ---
ERROR:  column "nosuch" does not exist
--- MySQL 8.4.10 ---
ERROR 1072 (42000) at line 1: Key column 'nosuch' doesn't exist in table
```

**6번과 왜 다른가**

```text
(nosuch)     괄호가 없다  ->  열 이름으로 읽는다   ->  "그런 열이 없다"
(code(10))   괄호가 있다  ->  함수 호출로 읽는다   ->  "그런 함수가 없다"
```

**PG 에서 괄호가 파싱을 가른다**는 것이 두 에러 문구의 차이로 드러난다.\
MySQL 은 `code(10)` 을 접두 길이 문법으로 갖고 있으므로 이 갈림 자체가 없다.

---

### 16. 그래서 무엇을 안 만드나 — **세 가지 기준**

```text
(1) 쓰이지 않을 인덱스
      -> 인덱스는 쓰기마다 갱신되고 공간을 쓴다. 안 쓰이면 순수한 손해다
      -> "혹시 몰라서" 만들지 않는다
      -> 무엇이 쓰이는지는 47번이 다룬다 (PG: pg_stat_user_indexes 의 idx_scan)

(2) 왼쪽 접두에 덮이는 인덱스
      -> (a) 와 (a,b) 가 둘 다 있으면 (a) 는 대개 낭비다
      -> (a,b) 가 WHERE a=... 도 덮기 때문이다 (1번)

(3) 선택도가 낮은 열의 인덱스
      -> b 는 값이 10가지뿐이라 한 값이 2,000행이다
      -> 인덱스로 좁혀도 표의 10% 를 읽어야 한다 -> 옵티마이저가 안 쓴다
      -> ★ 그 경계가 어디인지는 47번 3번에서 실측한다
```

**만들기 전에 던질 질문 하나**

```text
"이 인덱스가 없으면 어떤 질의가 느려지나?"
        ↓
답이 안 나오면 만들지 않는다
```

★ **이 편은 「어떻게 정의하나」까지다.** 무엇을 만들지의 근거는\
**[47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)의 실측**에서 나온다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `t46` 20,000행 적재 (전체) | PG 18.6 · MySQL 8.4.10 | 각 1회 | PG `generate_series` · MySQL 재귀 CTE |
| 복합 인덱스 생성 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 부분 인덱스 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL `ERROR 1064` 가 근거다** |
| 인덱스 크기 비교 (3·4번) | PG 18.6 | 1회 | **456 kB 대 16 kB** — 이 서버의 관찰 |
| 표현식 인덱스 괄호 1개 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 표현식 인덱스 괄호 2개 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **양쪽 다 통과 — 이식 형태다** |
| `SHOW INDEX` 의 `Expression` (5번) | MySQL 8.4.10 | 1회 | |
| 접두 길이 `code(10)` (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 의 「함수가 없다」가 근거다** |
| `INCLUDE` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `UNIQUE` 인덱스·제약 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `pg_indexes`·`pg_constraint`·`SHOW INDEX` |
| `DROP INDEX` 두 대상 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 의 거절이 근거다** |
| 부분 유니크 (10번) | PG 18.6 | 2회 | 제약 문법은 에러, 인덱스 문법은 성공 |
| 생성 열 인덱스 (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 의 `VIRTUAL` 거절이 근거다** |
| `pg_locks` 로 잠금 확인 (12번) | PG 18.6 | 1회 | `BEGIN ... ROLLBACK` 안에서 |
| `ADD INDEX ... LOCK=NONE` (12번) | MySQL 8.4.10 | 1회 | 성공 |
| `CONCURRENTLY` (13번) | PG 18.6 | 2회 | **트랜잭션 안의 에러가 근거다** |
| `USING HASH` 두 형태 (14번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL 의 `Index_type: BTREE` 가 근거다** |
| 없는 열 (15번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `DESC`/`ASC` 인덱스 (문법표) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 양쪽 다 된다 |

**구현 의존 항목** — 3번의 **인덱스 크기**, 12번의 **잠금 이름**, 14번의 **`Index_type`**.\
크기는 페이지 크기·채움률이 정하고, 잠금 이름은 PG 고유다.\
읽을 것은 **자릿수와 성질**이지 값이 아니다.

**언어 보장 항목** — 1·2·5·6·7·8·9·10·11·15번.\
어떤 문법이 어느 엔진에 있는가, 복합 인덱스가 선언 순서대로 정렬된다는 것,\
PG 에서 제약이 인덱스를 받친다는 것은 두 매뉴얼의 `CREATE INDEX`·제약 페이지가 정한 것이다.

**버전을 적은 자리** — MySQL 의 함수 인덱스는 8.0.13 부터다.\
가상 생성 열이 PG 18 의 기본이 된 것은 [18.0 릴리스 노트](https://www.postgresql.org/docs/release/18.0/)에 있다.\
**버전을 못 적은 자리** — PG 17 이하에서 생성 열 인덱스가 어땠는지는 **컨테이너가 없어 직접 확인하지 못했다.**

**계획(`EXPLAIN`) 을 싣지 않은 이유** — 이 편은 **정의**까지이고,\
**계획은 관찰이지 보장이 아니어서** 한 곳에 모아 두는 편이 낫다.\
모든 `EXPLAIN` 비교는 [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)에 있다.

**DB 잔재** — 없다. `t46` 과 그 위의 인덱스 전부, `t46_full_idx`·`t46_cc_idx`·`t46_hash_idx`·`t46_hash2_idx` 까지\
표를 지우면서 함께 사라졌다. `emp`·`dept` 는 **읽지도 쓰지도 않았다.**\
두 엔진의 최종 표 목록 출력은 [47번](../47-when-indexes-are-used/)의 「실행 검증」에 있다.
