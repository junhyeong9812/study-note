# sql/46-인덱스 정의 (복합·부분·표현식·커버링) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html) · [PostgreSQL 18 · Indexes](https://www.postgresql.org/docs/18/indexes.html) · [MySQL 8.4 · CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html) · [MySQL 8.4 · Optimization and Indexes](https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — MySQL 의 함수 인덱스(`((expr))`)는 8.0.13 부터다. ★ PG 18 의 **가상 생성 열에는 인덱스를 못 건다**(아래 7번에서 던져 확인).\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 20,000행짜리 `t46` 을 만들어 인덱스를 얹고 **지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> **선행** — [42 테이블 정의와 변경](../42-create-alter-drop-table/) · [43 기본키·UNIQUE](../43-primary-key-unique-and-null/) · **이어지는 것은 [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)** 다.\
> ★ **범위 선언** — 이 편은 「**인덱스를 어떻게 정의하나**」까지다. **「그래서 탈까 안 탈까」는 [47번](../47-when-indexes-are-used/)이 정본**이고, **자료구조 자체는 [`15-b-tree`]**(../../../../../data-structure/15-b-tree/)다.

## 한눈에 — 쉽게 말하면

**인덱스 = 「이 순서로 정렬한 사본」을 따로 만들어 두는 것.**

```text
책 뒤의 찾아보기                          인덱스
+---------------------+                  +------------------------+
| 가나다순 낱말 -> 쪽  |                  | 열 값 순서 -> 행 위치   |
| ...                 |                  | ...                    |
+---------------------+                  +------------------------+
   "ㅂ 으로 시작하는 낱말" 은 찾기 쉽다        code LIKE 'C00012%' 는 찾기 쉽다
   "-하기 로 끝나는 낱말" 은 못 찾는다         code LIKE '%00123' 은 못 찾는다
```

"똑같은 구조다" — **정렬해 둔 순서로 답할 수 있는 질문만 싸게 답한다.**

이 주제가 정하는 것은 **「무엇을 무슨 순서로 정렬해 둘 것인가」** 넷이다.

```text
복합    CREATE INDEX i ON t (a, b)              -> (a, b) 사전순
부분    CREATE INDEX i ON t (id) WHERE ...      -> 조건에 맞는 행만
표현식  CREATE INDEX i ON t ((lower(v)))        -> 값이 아니라 계산 결과를 정렬
커버링  CREATE INDEX i ON t (a) INCLUDE (b)     -> 정렬은 a 로, b 도 같이 들고 있다
```

| 비유 | 실체 |
|---|---|
| 책 뒤의 찾아보기 | 인덱스 |
| 가나다순으로 꽂아 둔다 | 열 값 순서로 정렬해 저장한다 |
| 성-이름 순 명부 | 복합 인덱스 `(a, b)` |
| ★ 이름만 알면 못 찾는다 | ★ **왼쪽 접두 규칙** — 선행 열이 없으면 못 쓴다 |
| 재직자만 실은 명부 | 부분 인덱스 |
| 대문자로 바꿔 꽂은 명부 | 표현식 인덱스 |
| 찾아보기에 쪽수 말고 요약까지 | 커버링 인덱스 |

> **인덱스(index)** — 열 값을 정렬해 따로 저장해 둔 것. 찾는 값의 위치를 바로 짚게 해 준다.\
> 예: `code` 인덱스가 있으면 `code='C000123'` 을 20,000행을 훑지 않고 찾는다.

★ **공짜가 아니다.** 인덱스는 **쓰기마다 같이 갱신되고 공간을 쓴다.**\
그래서 이 주제의 진짜 질문은 「어떻게 만드나」가 아니라 「**무엇을 안 만들 것인가**」다.

## 이 주제가 답하려는 질문

1. **복합 인덱스의 열 순서는 왜 중요한가?** — 왼쪽 접두 규칙.
2. **어떤 인덱스 문법이 어느 엔진에 있나?** — 부분·표현식·커버링·접두 길이.
3. **`UNIQUE` 제약과 `UNIQUE` 인덱스는 같은 것인가?**

## 예시 데이터 — 이 묶음이 공유하는 것

인덱스는 데이터가 있어야 이야기가 된다. **20,000행짜리 `t46` 을 만들었다가 지웠다.**

```text
t46 (20,000행)
+--------+-------------+-----------------------------------------+
| id     | int PK      | 1 .. 20000                              |
| a      | int         | id % 100   -> 값 100가지, 각 200행       |
| b      | int         | id % 10    -> 값 10가지, 각 2000행       |
| code   | varchar(20) | 'C000001' .. 'C020000'  (전부 다르다)    |
| v      | varchar(30) | 'name1' .. 'name20000'  (전부 다르다)    |
| status | varchar(10) | id%1000=0 이면 'ACTIVE'(20행), 아니면 'DONE' |
+--------+-------------+-----------------------------------------+
```

`status` 를 **20행만 `ACTIVE`** 로 만든 이유는 **부분 인덱스**의 값어치를 보이기 위해서다.\
[47번](../47-when-indexes-are-used/)은 이 표와 짝이 되는 `t47` 을 따로 쓴다.

## 동작 방식

### 1. 복합 인덱스 — **정렬은 사전순이고, 그것이 전부다**

**언제 쓰나** — 두 열을 함께 조건에 거는 질의가 있을 때.

```sql
CREATE INDEX t46_ab_idx ON t46 (a, b);
```

**두 엔진 다 받는다.** 만들어진 것이 무엇인지가 이 절의 본문이다.

```text
인덱스 안의 순서 — (a, b) 를 사전순으로 늘어놓은 것

  (0, 0)   (0, 1)   ...  (0, 9)
  (1, 0)   (1, 1)   ...  (1, 9)
  (2, 0)   ...
  ...
  (99, 0)  ...           (99, 9)
   ^^^      ^^^
   a 로     그 안에서 b 로
   먼저     다시
```

그림 해설 — **이 한 그림이 왼쪽 접두 규칙의 전부**다.

```text
WHERE a = 7 AND b = 7   ->  (7,7) 한 지점. 바로 짚는다
WHERE a = 7             ->  (7,0)~(7,9) 연속 구간. 좁힐 수 있다
WHERE b = 7             ->  ★ (0,7) (1,7) (2,7) ... 흩어져 있다. 못 좁힌다
```

> **왼쪽 접두 규칙(leftmost prefix)** — 복합 인덱스는 **선언한 열 순서의 앞쪽부터** 연속으로 쓸 때만 쓸모가 있다.\
> 예: `(a,b,c)` 인덱스는 `a`·`(a,b)`·`(a,b,c)` 조건에 쓰이고 `b` 나 `c` 만으로는 안 쓰인다.

**이것이 「정의」의 문제인 이유** — 열 순서는 **`CREATE INDEX` 를 쓸 때 정해지고 나중에 못 바꾼다.**\
`(a,b)` 와 `(b,a)` 는 **다른 인덱스**다.

```text
자주 쓰는 조건이 a 하나와 (a,b) 둘이다   ->  (a, b) 하나로 둘 다 덮는다
자주 쓰는 조건이 b 하나와 (a,b) 둘이다   ->  (b, a) 로 만든다
둘 다 단독으로 자주 쓰인다               ->  인덱스 둘을 만든다 (쓰기 비용이 는다)
```

비용 — 열 순서를 잘못 잡으면 **인덱스가 있는데 안 쓰인다.**\
**실제 계획 출력은 [47 번 1번](../47-when-indexes-are-used/)에 있다** — 여기서는 순서가 정의에서 정해진다는 것까지다.

### 2. ★ 부분 인덱스 — **PG 만 있다**

**언제 쓰나** — 표의 일부만 자주 찾을 때. 「미처리 주문」·「삭제 안 된 행」이 전형이다.

```text
### SQL: CREATE INDEX t46_part_idx ON t46 (id) WHERE status = 'ACTIVE';
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'WHERE status = 'ACTIVE'' at line 1
```

그림 해설 — **20,000행 중 20행만 담은 인덱스**가 만들어진다.

```text
일반 인덱스                      부분 인덱스
+---------------------+          +---------------------+
| 20,000개 항목        |          | 20개 항목            |
| 모든 행이 들어간다    |          | status='ACTIVE' 만   |
+---------------------+          +---------------------+
  -> DONE 행을 UPDATE 해도          -> DONE 행을 UPDATE 해도
     인덱스를 갱신한다                 ★ 인덱스를 안 건드린다
```

두 그림의 결론 — **부분 인덱스는 크기만 줄이는 것이 아니라 쓰기 비용도 줄인다.**\
그 조건에 안 맞는 행은 인덱스에 들어가지도, 갱신되지도 않는다.

대가 — **그 조건이 질의에 없으면 쓰이지 않는다.** `WHERE status='ACTIVE'` 를 안 쓰면 이 인덱스는 후보가 아니다.

**MySQL 에서의 대안**은 **생성 열 + 인덱스**다([45번](../45-check-not-null-default-generated-columns/)).\
「`ACTIVE` 일 때만 값이 있는 열」을 만들어 인덱스를 걸면 `NULL` 인 행이 인덱스를 덜 차지한다 —\
**완전히 같은 것은 아니다.** 부분 인덱스는 **인덱스에 아예 안 들어가는** 것이고, 생성 열은 **`NULL` 로 들어간다.**

### 3. ★ 표현식 인덱스 — **괄호를 둘 쓰면 양쪽 다 된다**

**언제 쓰나** — 열에 함수를 씌워 검색할 때. **[47번의 핵심 처방](../47-when-indexes-are-used/)이 이것이다.**

PG 문법을 먼저 던졌다.

```text
### SQL: CREATE INDEX t46_expr_idx ON t46 (lower(v));
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'v))' at line 1
```

★ **MySQL 문법으로 다시 던지면 양쪽 다 통과한다.**

```text
### SQL: CREATE INDEX t46_expr2_idx ON t46 ((lower(v)));
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
(성공)
```

그림 해설 — **괄호가 하나 더 있는 것이 이식 가능한 형태**다.

```text
(lower(v))     PG : 표현식으로 읽는다
               MySQL : 파서가 'lower' 를 열 이름으로 보다가 '(' 에서 막힌다

((lower(v)))   PG : 바깥 괄호는 무시된다
               MySQL : 「이건 식이다」라는 표시로 읽는다
        ↓
   양쪽 다 통과한다
```

**MySQL 쪽에 무엇이 만들어졌는지 확인했다.**

```text
--- MySQL 8.4.10 ---
SHOW INDEX FROM t46;   (폭에 맞춰 일부 칸만 옮겼다)
+-------+------------+---------------+-------------+----------+------------+
| Table | Non_unique | Key_name      | Column_name | Sub_part | Expression |
+-------+------------+---------------+-------------+----------+------------+
| t46   |          1 | t46_expr2_idx | NULL        |     NULL | lower(`v`) |
+-------+------------+---------------+-------------+----------+------------+
                                        ↑ 열이 없다      ↑ 식이 여기 들어 있다
```

비용 — **그 식과 똑같은 식으로 질의해야 쓰인다.** `lower(v)` 로 만들고 `upper(v)` 로 찾으면 안 쓰인다.\
**실제 계획 비교는 [47 번 2번](../47-when-indexes-are-used/)에 있다.**

### 4. ★ MySQL 의 접두 길이 — **PG 는 함수 호출로 읽는다**

**언제 쓰나** — 긴 문자열 열에 인덱스를 걸 때. MySQL 에는 키 길이 제한이 있다.

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

★ **PG 의 에러가 무슨 일이 일어났는지 정확히 말한다** — `code(10)` 을 **`code` 라는 함수에 `10` 을 넘긴 것**으로 읽었다.\
PG 에 「접두 길이」라는 문법이 없으니 식으로 파싱한 것이다.

**MySQL 쪽에 무엇이 만들어졌는지 본다.**

```text
--- MySQL 8.4.10 ---
+-------+--------------+-------------+----------+
| Table | Key_name     | Column_name | Sub_part |
+-------+--------------+-------------+----------+
| t46   | t46_pref_idx | code        |       10 |      <- Sub_part 가 10 이다
+-------+--------------+-------------+----------+
```

```text
전체 인덱스                      접두 10자 인덱스
'C000001'  전부 저장              'C000001'  <- 앞 10자만 (이 값은 7자라 전부)
'C0000012345678901234'           'C000001234'
        ↓                                ↓
정확한 비교가 인덱스만으로 끝난다     앞 10자로 좁힌 뒤 실제 행을 봐야 한다
```

비용 — **접두가 같은 값이 많으면 효과가 없다.** `'https://example.com/...'` 같은 열에 앞 10자는 전부 같다.

**PG 에서의 대안은 표현식 인덱스**다 — `CREATE INDEX i ON t ((left(v,10)))`.\
단 그러면 **질의도 `left(v,10)` 으로 써야** 한다(3번의 대가).

### 5. ★ 커버링 — **`INCLUDE` 는 PG 만**

**언제 쓰나** — 인덱스만 읽고 표를 안 읽게 하고 싶을 때.

```text
### SQL: CREATE INDEX t46_inc_idx ON t46 (a) INCLUDE (b);
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near 'INCLUDE (b)' at line 1
```

> **커버링 인덱스(covering index)** — 질의가 필요로 하는 열을 인덱스가 전부 갖고 있어서\
> **표 자체를 안 읽고 끝나는** 경우.\
> 예: `SELECT b FROM t WHERE a=7` 에 `(a) INCLUDE (b)` 인덱스가 있으면 표를 안 본다.

```text
CREATE INDEX i ON t (a, b)              CREATE INDEX i ON t (a) INCLUDE (b)
+---------------------------+           +---------------------------+
| 정렬 키: a, b             |           | 정렬 키: a                |
| b 로도 정렬돼 있다         |           | b 는 "그냥 들고만" 있다    |
+---------------------------+           +---------------------------+
  -> WHERE a=7 AND b=7 을 좁힌다          -> WHERE b=7 에는 못 쓴다
  -> UNIQUE (a,b) 를 만들 수 있다         -> UNIQUE 는 a 에만 걸린다
```

두 그림의 결론 — **`INCLUDE` 는 「정렬에는 안 쓰지만 같이 갖고 다니는 열**」이다.\
`(a,b)` 로 만들면 같은 효과에 정렬까지 얻지만, **인덱스가 커지고 `UNIQUE` 의 의미가 달라진다.**

**MySQL 에서의 대안은 복합 인덱스**다 — `INCLUDE` 가 없으므로 `(a, b)` 로 만든다.\
MySQL 에서 커버링이 일어났는지는 `EXPLAIN` 의 **`Extra: Using index`** 로 알 수 있다([47번](../47-when-indexes-are-used/)).

### 6. ★ `UNIQUE` 제약과 `UNIQUE` 인덱스 — **PG 에서는 다르고 MySQL 에서는 같다**

**언제 쓰나** — 유일성을 강제할 때. [43 번](../43-primary-key-unique-and-null/)의 이어짐이다.

두 가지 방법으로 같은 것을 만들어 본다.

```sql
CREATE UNIQUE INDEX t46_uix ON t46 (code);              -- (A) 인덱스로
ALTER TABLE t46 ADD CONSTRAINT t46_ucon UNIQUE (v);     -- (B) 제약으로
```

**PG 의 카탈로그를 둘 다 본다.**

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
 ...                             ★ t46_uix 는 없다
```

그림 해설 — **(B) 는 제약이면서 인덱스이고, (A) 는 인덱스일 뿐이다.**

```text
ADD CONSTRAINT ... UNIQUE   ->  제약 1개 + 그 제약을 받치는 인덱스 1개
CREATE UNIQUE INDEX         ->  인덱스 1개.  제약은 없다
```

**지울 때 차이가 드러난다.**

```text
--- PG 18.6 ---
DROP INDEX t46_ucon;
ERROR:  cannot drop index t46_ucon because constraint t46_ucon on table t46 requires it
HINT:  You can drop constraint t46_ucon on table t46 instead.

DROP INDEX t46_uix;
DROP INDEX                       <- 이쪽은 그냥 지워진다
```

**MySQL 에는 이 구분이 없다.**

```text
--- MySQL 8.4.10 ---
SHOW INDEX FROM t46;   (Non_unique=0 이 유일 인덱스다)
+-------+------------+----------+-------------+
| Table | Non_unique | Key_name | Column_name |
+-------+------------+----------+-------------+
| t46   |          0 | PRIMARY  | id          |
| t46   |          0 | t46_uix  | code        |
| t46   |          0 | t46_ucon | v           |     <- (A) 와 (B) 가 구분되지 않는다
+-------+------------+----------+-------------+

DROP INDEX t46_ucon ON t46;
(성공 — 아무 저항도 없다)
```

**PG 에만 있는 것이 하나 더 있다 — 부분 유니크 인덱스.**

```text
--- PG 18.6 ---
ALTER TABLE t46 ADD CONSTRAINT t46_pu UNIQUE (code) WHERE status='ACTIVE';
ERROR:  syntax error at or near "WHERE"
LINE 1: ...TER TABLE t46 ADD CONSTRAINT t46_pu UNIQUE (code) WHERE stat...
                                                             ^

CREATE UNIQUE INDEX t46_pu ON t46 (code) WHERE status='ACTIVE';
CREATE INDEX                     <- ★ 인덱스로는 된다
```

그림 해설 — **「조건부 유일성」은 제약 문법으로 못 쓰고 인덱스 문법으로만 쓴다.**\
「삭제 안 된 행끼리만 `code` 가 유일하다」 같은 요구가 이 형태로 풀린다\
([43 번 12번의 네 번째 선택지](../43-primary-key-unique-and-null/)가 이것이다).

비용 — 제약으로 안 만들었으므로 **외래키가 이 열을 가리킬 수 없다**([44 번 12번](../44-foreign-key-referential-actions/)).

### 7. ★ 생성 열에 인덱스 — **PG 18 의 기본값이 함정이 된다**

**언제 쓰나** — 계산값으로 검색할 때. [45 번](../45-check-not-null-default-generated-columns/)의 이어짐이다.

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

★ **[45 번 9번](../45-check-not-null-default-generated-columns/)과 이어 읽으면 함정이 보인다.**

```text
PostgreSQL 18 에서
  total int GENERATED ALWAYS AS (price*qty)          <- 키워드를 안 썼다
        ↓
  기본값이 VIRTUAL 이다 (18 부터 바뀌었다)
        ↓
  ★ 인덱스를 못 건다
        ↓
  "생성 열을 만들었으니 인덱스를 걸어 검색하겠다" 가 여기서 막힌다
```

**처방** — **인덱스를 걸 생성 열에는 `STORED` 를 명시한다.**\
MySQL 은 `VIRTUAL` 에도 인덱스를 걸 수 있으므로 이 문제가 없다.

### 8. 인덱스를 만들 때 무엇이 잠기나

**언제 쓰나** — 운영 중인 표에 인덱스를 추가할 때. [42 번의 `ALTER` 잠금](../42-create-alter-drop-table/)과 짝이다.

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

★ **`ALTER TABLE` 의 `AccessExclusiveLock` 보다 약하다**([42 번 6번](../42-create-alter-drop-table/)).

```text
ShareLock            : 읽기는 된다. 쓰기(INSERT/UPDATE/DELETE)가 막힌다
AccessExclusiveLock  : 읽기까지 막힌다
```

**쓰기까지 열어 두려면 `CONCURRENTLY` 를 쓴다.**

```text
--- PG 18.6 ---
CREATE INDEX CONCURRENTLY t46_cc_idx ON t46 (status);
CREATE INDEX

BEGIN; CREATE INDEX CONCURRENTLY t46_cc2_idx ON t46 (b); COMMIT;
BEGIN
ERROR:  CREATE INDEX CONCURRENTLY cannot run inside a transaction block
```

★ **그 대가가 「트랜잭션 안에서 못 돈다**」이다. 표를 두 번 훑고, 실패하면 **쓸 수 없는 인덱스가 남는다.**

**MySQL 쪽은 [42 번의 `ALGORITHM`/`LOCK` 절](../42-create-alter-drop-table/)로 같은 것을 요구한다.**

```text
--- MySQL 8.4.10 ---
ALTER TABLE t42_b ADD INDEX (v), ALGORITHM=INPLACE, LOCK=NONE;
(성공 — 아무 출력 없음)
```

### 9. 없는 열에 인덱스를 걸면

**언제 쓰나** — 마이그레이션 스크립트의 오타를 잡을 때.

```text
### SQL: CREATE INDEX t46_bad_idx ON t46 (nosuch);
--- PG 18.6 ---
ERROR:  column "nosuch" does not exist
--- MySQL 8.4.10 ---
ERROR 1072 (42000) at line 1: Key column 'nosuch' doesn't exist in table
```

**양쪽 다 즉시 막는다** — 4번의 `code(10)` 과 대비하면 성질이 보인다.

```text
CREATE INDEX ... (nosuch)   -> "그런 열이 없다"        : 오타로 읽었다
CREATE INDEX ... (code(10)) -> "그런 함수가 없다"      : ★ 식으로 읽었다
```

PG 에서 **괄호가 붙으면 열 이름이 아니라 함수 호출로 파싱된다**는 것이 에러 문구의 차이로 드러난다.

## 문법 — 어느 절에서 무엇이 갈리나

```sql
-- 기본
CREATE INDEX i ON t (a);                          -- 양쪽
CREATE INDEX i ON t (a, b);                       -- 양쪽 (복합)
CREATE UNIQUE INDEX i ON t (a);                   -- 양쪽
CREATE INDEX i ON t (a DESC, b ASC);              -- 양쪽
DROP INDEX i;                                     -- PG
DROP INDEX i ON t;                                -- MySQL (표 이름이 필요하다)

-- 갈리는 것
CREATE INDEX i ON t (id) WHERE cond;              -- ★ PG 만 (부분 인덱스)
CREATE INDEX i ON t (lower(v));                   -- ★ PG 만 (괄호 하나)
CREATE INDEX i ON t ((lower(v)));                 -- ★ 양쪽 (괄호 둘)
CREATE INDEX i ON t (code(10));                   -- ★ MySQL 만 (접두 길이)
CREATE INDEX i ON t (a) INCLUDE (b);              -- ★ PG 만 (커버링)
CREATE INDEX CONCURRENTLY i ON t (a);             -- ★ PG 만
CREATE INDEX i ON t (a) USING HASH;               -- ★ MySQL 만 (그리고 무시된다 — 아래)
CREATE INDEX i ON t USING hash (a);               -- ★ PG 만 (USING 이 열 목록 앞이다)
ALTER TABLE t ADD INDEX (a), ALGORITHM=INPLACE;   -- ★ MySQL 만

-- 제약으로 만들기
ALTER TABLE t ADD CONSTRAINT c UNIQUE (a);        -- 양쪽 (6번)
ALTER TABLE t ADD CONSTRAINT c UNIQUE (a) WHERE cond;  -- ★ 양쪽 다 문법 에러
CREATE UNIQUE INDEX i ON t (a) WHERE cond;        -- ★ PG 만 (부분 유니크)
```

- **`DROP INDEX` 의 형태가 다르다.** PG 는 인덱스 이름이 스키마에서 유일하고, MySQL 은 **표에 딸려 있다.**
- ★ **`USING` 의 자리가 다르고, MySQL 은 받고도 무시한다.** 던져서 확인했다.

```text
### SQL: CREATE INDEX t46_hash_idx ON t46 (b) USING HASH;
--- PG 18.6 ---
ERROR:  syntax error at or near "USING"
LINE 1: CREATE INDEX t46_hash_idx ON t46 (b) USING HASH;
                                             ^
--- MySQL 8.4.10 ---
(성공)

### SQL: CREATE INDEX t46_hash2_idx ON t46 USING hash (b);
--- PG 18.6 ---
CREATE INDEX
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... right syntax to use near 'USING hash (b)' at line 1
```

  **MySQL 이 받은 `USING HASH` 가 무엇이 됐는지 물었다.**

```text
--- MySQL 8.4.10 ---
SHOW INDEX FROM t46 WHERE Key_name='t46_hash_idx'\G
     Key_name: t46_hash_idx
  Column_name: b
   Index_type: BTREE          <- ★ HASH 가 아니다. 조용히 B-트리가 됐다
```

  PG 쪽은 요청한 대로 만들어졌다.

```text
--- PG 18.6 ---
SELECT indexdef FROM pg_indexes WHERE indexname='t46_hash2_idx';
 CREATE INDEX t46_hash2_idx ON public.t46 USING hash (b)
```

  ★ **[44 번의 열 뒤 `REFERENCES`](../44-foreign-key-referential-actions/) 와 같은 종류의 조용한 무시**다 —\
  문법은 통과하고 만들어진 것이 다르다. InnoDB 는 명시적 해시 인덱스를 지원하지 않는다.

## 어디서 틀리나

1. **복합 인덱스의 열 순서를 아무렇게나 정한다.** `(a,b)` 와 `(b,a)` 는 **다른 인덱스**다(1번).
2. **`(a,b)` 인덱스가 `WHERE b=...` 에도 쓰일 것이라 기대한다.** 안 쓰인다 — 왼쪽 접두 규칙(1번, 계획은 47번).
3. **부분 인덱스를 MySQL 에서 쓰려 한다.** `ERROR 1064` 다(2번).
4. **표현식 인덱스를 `(lower(v))` 로 쓴다.** MySQL 은 **괄호 둘**이 필요하다(3번).\
   ★ **괄호 둘로 쓰면 양쪽 다 통과**하므로 그쪽을 습관으로 삼는다.
5. **PG 에서 `code(10)` 을 쓴다.** 「함수가 없다」는 이상한 에러를 받는다(4번).
6. **`INCLUDE` 를 MySQL 에 쓴다.** 없다. 복합 인덱스로 대신한다(5번).
7. **`CREATE UNIQUE INDEX` 로 만든 것을 제약이라고 생각한다.** PG 에서는 **제약이 아니다**(6번).\
   외래키가 그 열을 가리킬 수 없다.
8. ★ **PG 18 에서 생성 열에 인덱스를 걸려다 막힌다.** 기본이 `VIRTUAL` 이 됐다 — **`STORED` 를 명시**한다(7번).
9. **인덱스를 「만들면 좋은 것」으로 생각한다.** 쓰기마다 갱신되고 공간을 쓴다.\
   **안 쓰이는 인덱스는 순수한 손해**다 — 무엇이 쓰이는지는 [47번](../47-when-indexes-are-used/)이 다룬다.
10. **운영 중 표에 그냥 `CREATE INDEX` 를 친다.** PG 는 **쓰기를 막는다**(8번). `CONCURRENTLY` 를 쓴다.
11. ★ **MySQL 에서 `USING HASH` 를 쓰고 해시 인덱스가 생겼다고 믿는다.**\
    문법은 통과하지만 `SHOW INDEX` 의 `Index_type` 은 **`BTREE`** 다(문법 절). PG 는 `USING` 의 **자리가 다르다.**

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| 복합 인덱스의 순서 | 선언한 순서로 정렬된다 | **그 순서를 옵티마이저가 어떻게 쓰나**(47번) |
| 부분 인덱스 | — | **PG 에만 있다** |
| 표현식 인덱스 | — | **문법이 다르다**(괄호 개수) |
| `UNIQUE` 제약 대 인덱스 | 유일성은 같다 | **카탈로그에서 구분하나**(PG 는 하고 MySQL 은 안 한다) |
| 생성 열 인덱스 | — | **`VIRTUAL` 에 걸 수 있나**(PG 18 은 못 한다) |
| 인덱스 생성 잠금 | — | **`ShareLock` · `CONCURRENTLY` · `ALGORITHM/LOCK`** |

- **`Sub_part`·`Expression` 같은 `SHOW INDEX` 의 칸 이름**은 MySQL 의 구현 세부다.
- **`ShareLock` 이라는 이름과 등급**도 PG 의 구현 세부다. 외울 것은 「**인덱스 생성은 쓰기를 막는다**」이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 자주 쓰는 조건 열에 인덱스.** 다만 **무엇이 자주인지 측정 뒤에**([47번](../47-when-indexes-are-used/)).
- **쓴다 — 복합 인덱스를 「좁은 열부터」가 아니라 「단독으로도 쓰이는 열부터」.** 왼쪽 접두 규칙 때문이다.
- **쓴다 — PG 에서 부분 인덱스.** 대상이 표의 1% 이하면 크기와 쓰기 비용이 함께 준다.
- **쓴다 — 표현식 인덱스를 `((expr))` 형태로.** 양쪽에서 통한다.
- **안 쓴다 — 「혹시 몰라서」 만드는 인덱스.** 쓰기마다 비용이고 계획을 흔든다.
- **안 쓴다 — 중복되는 인덱스.** `(a)` 와 `(a,b)` 가 둘 다 있으면 `(a)` 는 대개 낭비다(왼쪽 접두).
- **조심한다 — `CREATE UNIQUE INDEX` 대 `ADD CONSTRAINT UNIQUE`.** PG 에서 의미가 다르다(6번).
- **조심한다 — 운영 중 인덱스 추가.** PG 는 `CONCURRENTLY`, MySQL 은 `ALGORITHM=INPLACE, LOCK=NONE`.

## 핵심 문장

- **복합 인덱스는 선언 순서대로 사전순 정렬이다.** 그래서 **선행 열이 빠지면 못 쓴다**(왼쪽 접두 규칙).
- **`(a,b)` 와 `(b,a)` 는 다른 인덱스다.** 순서는 정의에서 정해지고 나중에 못 바꾼다.
- **부분 인덱스(`WHERE`)와 `INCLUDE` 는 PG 만, 접두 길이(`col(10)`)는 MySQL 만 있다.**
- **표현식 인덱스는 `((expr))` 로 쓰면 양쪽 다 통과한다.**
- **PG 에서 `CREATE UNIQUE INDEX` 는 제약이 아니다.** 제약으로 만든 것은 `DROP INDEX` 로 못 지운다.
- **조건부 유일성은 제약 문법으로 못 쓰고 부분 유니크 인덱스로만 쓴다(PG).**
- ★ **PG 18 에서 생성 열의 기본은 `VIRTUAL` 이고, 가상 생성 열에는 인덱스를 못 건다.**
- **인덱스 생성은 PG 에서 쓰기를 막는다(`ShareLock`).** `CONCURRENTLY` 는 트랜잭션 안에서 못 돈다.
- **MySQL 의 `USING HASH` 는 받아들여지고 `BTREE` 가 된다.** PG 는 `USING` 이 열 목록 **앞**에 온다.

## 관련 자료

- [`data-structure/15-b-tree`](../../../../../data-structure/15-b-tree/) — ★ **그쪽은 B-트리가 어떻게 생겼고 어떻게 탐색·분할하나까지,\
  여기는 「그 구조를 SQL 로 어떻게 선언하나」부터.** 노드·차수·분할은 한 줄도 여기서 다루지 않는다.
- [47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/) — ★ **「그래서 탈까 안 탈까」는 전부 거기다.**\
  여기의 계획 출력은 8번의 잠금 확인뿐이고, `EXPLAIN` 비교는 47번이 정본이다.
- [42 테이블 정의와 변경](../42-create-alter-drop-table/) — `ALTER` 의 잠금. 8번이 그 이어짐이다.
- [43 기본키·UNIQUE 제약과 NULL](../43-primary-key-unique-and-null/) — 6번의 `UNIQUE` 제약이 거기서 온다.
- [44 외래키와 참조 동작](../44-foreign-key-referential-actions/) — FK 가 요구하는 인덱스.
- [45 CHECK·DEFAULT·생성 열](../45-check-not-null-default-generated-columns/) — 7번의 생성 열이 거기서 온다.
- [38 패턴 매칭](../38-pattern-matching-like-regex/) — `varchar_pattern_ops` 같은 연산자 클래스의 실측이 거기 있다.
- [SQL 주제 목록](../README.md) — 58(EXPLAIN 읽기) 이 이웃이다.

## 용어 풀이

- **인덱스(index)** — 열 값을 정렬해 따로 저장해 둔 것. 찾는 값의 위치를 바로 짚게 해 준다.\
  예: `code` 인덱스가 있으면 20,000행을 훑지 않고 한 값을 찾는다.
- **복합 인덱스(composite index)** — 열 여러 개를 묶어 만든 인덱스. 선언 순서대로 사전순 정렬된다.\
  예: `(a,b)` 는 `a` 로 먼저, 같은 `a` 안에서 `b` 로 정렬된다.
- **왼쪽 접두 규칙(leftmost prefix)** — 복합 인덱스는 선언 순서의 앞쪽부터 연속으로 쓸 때만 쓸모가 있다.\
  예: `(a,b,c)` 인덱스는 `b` 조건만으로는 안 쓰인다.
- **부분 인덱스(partial index)** — 조건에 맞는 행만 담은 인덱스. **PG 에만 있다.**\
  예: `WHERE status='ACTIVE'` 를 붙이면 20,000행 중 20행만 인덱스에 들어간다.
- **표현식 인덱스(expression index)** — 열 값이 아니라 **계산 결과**를 정렬해 둔 인덱스.\
  예: `((lower(v)))` 로 만들면 `WHERE lower(v)='x'` 가 인덱스를 탄다.
- **커버링 인덱스(covering index)** — 질의가 필요한 열을 인덱스가 전부 갖고 있어 **표를 안 읽는** 경우.\
  예: PG 의 `Index Only Scan`, MySQL 의 `Extra: Using index` 가 그 표시다.
- **`INCLUDE`** — PG 에서 **정렬에는 안 쓰지만 인덱스가 같이 들고 다닐** 열을 지정하는 절.\
  예: `(a) INCLUDE (b)` 는 `WHERE b=...` 에는 못 쓰지만 `SELECT b` 를 표 없이 답한다.
- **접두 길이(prefix length)** — MySQL 에서 문자열 열의 **앞 N 자만** 인덱스에 담는 것.\
  예: `code(10)` 은 앞 10자만 저장한다. `SHOW INDEX` 의 `Sub_part` 가 `10` 으로 보인다.
- **`UNIQUE` 인덱스 대 `UNIQUE` 제약** — PG 에서 **제약은 인덱스를 만들지만 인덱스는 제약이 아니다.**\
  예: 제약이 받치는 인덱스는 `DROP INDEX` 로 못 지운다.
- **부분 유니크 인덱스** — 조건에 맞는 행끼리만 유일하게 하는 것. **인덱스 문법으로만 쓴다.**\
  예: `CREATE UNIQUE INDEX ... ON t (code) WHERE deleted_at IS NULL`.
- **`ShareLock`** — PG 의 표 잠금 중 **읽기는 허용하고 쓰기를 막는** 등급.\
  예: `CREATE INDEX` 가 이것을 잡는다. `ALTER TABLE` 의 `AccessExclusiveLock` 보다 약하다.
- **`CONCURRENTLY`** — 쓰기를 막지 않고 인덱스를 만드는 PG 옵션. 표를 두 번 훑는다.\
  예: 트랜잭션 블록 안에서는 못 돈다(`ERROR: cannot run inside a transaction block`).

## 더 들어가면

- **인덱스의 종류는 B-트리만이 아니다.** PG 에는 GIN·GiST·BRIN·SP-GiST·해시가 있고 MySQL 에는 FULLTEXT·SPATIAL 이 있다.\
  **이 실험에서는 기본(B-트리)만 만들었다** — 다른 종류는 던져 보지 않았으므로 여기 적지 않는다.
- **인덱스가 많을수록 옵티마이저의 선택지도 늘어난다.** 선택지가 늘면 **잘못 고를 가능성도 는다.**\
  「인덱스를 지웠더니 빨라졌다」가 나오는 이유다([47번](../47-when-indexes-are-used/)의 계획 이야기와 이어진다).
- **PG 의 `CREATE INDEX CONCURRENTLY` 가 실패하면 `INVALID` 인덱스가 남는다.**\
  `\d` 에 보이고 공간을 쓰지만 쓰이지 않는다. 찾아서 지워야 한다.\
  **이 실험에서 실패 상황을 만들어 보지는 않았다.**
- **MySQL 의 접두 길이는 「길이 제한」 때문에 강제되기도 한다.** utf8mb4 에서 한 글자가 최대 4바이트라\
  `varchar(1000)` 전체에는 인덱스를 못 건다. **이 실험의 `varchar(20)` 에서는 그 제한에 걸리지 않았다.**
