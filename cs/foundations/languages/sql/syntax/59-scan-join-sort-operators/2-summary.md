# sql/59-스캔·조인·정렬 연산자 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Planner Method Configuration](https://www.postgresql.org/docs/18/runtime-config-query.html) · [PostgreSQL 18 · Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) · [MySQL 8.4 · EXPLAIN Join Types](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html#explain-join-types) · [MySQL 8.4 · Hash Join Optimization](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 계획은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 계획은 없다.\
> **이 편이 만든 객체와 그 뒷정리** — 표 `t59_big`(20만 행) · `t59_mid`(5만 행) · `t59_small`(10행).
> PG 는 `BEGIN … ROLLBACK` 안에서 만들었고, MySQL 은 DDL 이 암묵 커밋이라 `DROP TABLE IF EXISTS` 로 직접 지웠다.
> **기존 `emp`·`dept` 는 건드리지 않았다** — 4행·3행으로는 어떤 조건에서도 전체 스캔만 나와 이 주제가 성립하지 않는다.\
> **측정 조건** — PG 계획은 전부 `max_parallel_workers_per_gather = 0`(병렬 끔)에서 찍었다. 켜면 노드가 두 겹 늘어 읽기가 나빠진다.
> **PG 의 계획은 한 트랜잭션 안에서 한 번에 찍은 것**이다 — `ANALYZE` 의 표본이 판마다 달라 숫자가 흔들리기 때문이다(3절).\
> ★ **실행 계획은 관찰이지 보장이 아니다.** 이 편은 **같은 스크립트를 8판 돌려 연산자가 갈리는 것을 실제로 관찰했다**(3절).\
> **선행** — [58 `EXPLAIN` 읽기](../58-explain-plan-tree/) · [46 인덱스 정의](../46-index-definition-composite-partial-expression/). **46 은 이 배치 작업 중에 폴더가 생겨 링크로 전환했다.**

## 한눈에 — 쉽게 말하면

**연산자는 「엔진이 쓸 수 있는 도구」이고, 어느 도구를 쓸지는 데이터 크기가 정한다.**

- 책장에서 책을 찾는 방법은 여럿이다.
  - **한 권만** 찾으면 → 색인에서 번호를 보고 **그 자리로 바로 간다.**
  - **절반쯤** 찾으면 → 색인을 오가는 게 더 번거롭다. **처음부터 훑는 게 빠르다.**
- 두 명단을 맞춰 보는 방법도 여럿이다.
  - 한쪽이 **10명**이면 → 그 10명을 들고 **한 명씩 저쪽에서 찾는다.**
  - 양쪽이 **5만 명**이면 → 한쪽을 **통째로 외워 두고**(해시) 다른 쪽을 훑는다.
  - 양쪽이 **이미 이름순**이면 → **나란히 놓고 지퍼 올리듯** 맞춘다.

| 비유 | 실체 |
|---|---|
| 색인에서 번호를 보고 그 자리로 | `Index Scan` (MySQL `ref`·`eq_ref`·`const`) |
| 처음부터 끝까지 훑는다 | `Seq Scan` (MySQL `type=ALL`) |
| 색인에서 자리 목록만 모아 한 번에 간다 | `Bitmap Heap Scan` (**PG 에만 있다**) |
| 색인만 보고 책은 안 펴도 되는 경우 | `Index Only Scan` (MySQL `Extra: Using index`) |
| 10명을 들고 한 명씩 찾기 | `Nested Loop` |
| 한쪽을 통째로 외워 두기 | `Hash Join` |
| 이름순 두 명단을 지퍼 올리기 | `Merge Join` (**PG 에만 있다**) |

```text
 찾는 행이 적다                        찾는 행이 많다
 +---------------------------+        +---------------------------+
 | 인덱스로 자리를 찍어 간다   |        | 처음부터 끝까지 훑는다      |
 | 읽는 페이지: 적다           |        | 읽는 페이지: 전부           |
 | 대신 페이지를 널뛰며 읽는다  |        | 대신 순서대로 읽는다         |
 +---------------------------+        +---------------------------+
   -> 어느 쪽이 싼가는 "몇 %를 읽나"로 갈린다
```

**똑같은 구조다** — 「인덱스를 걸었는데 왜 안 타지?」의 답이 대개 이 그림이다.\
인덱스를 안 탄 게 아니라 **타는 게 더 비싸서 안 탄 것**이고, 그 판단선을 3절에서 실제로 찍어 본다.

> **선택도(selectivity)** — 조건이 전체 중 몇 %를 남기나. 낮을수록(=조금 남길수록) 인덱스가 유리하다.\
> 예: 20만 행에서 200행을 고르면 선택도 0.1%, 10만 행을 고르면 50%.

> **연산자(operator)** — 계획 트리의 한 칸이 하는 일. 스캔·조인·정렬·집계 네 갈래로 나뉜다.\
> 예: `Seq Scan`(스캔) · `Hash Join`(조인) · `Sort`(정렬) · `HashAggregate`(집계).

## 이 주제가 답하려는 질문

1. **스캔 연산자는 몇 가지이고, 무엇이 그중 하나를 고르게 하나** — 「몇 %에서 갈리나」를 숫자로.
2. **조인 연산자 셋은 각각 어떤 상황의 도구인가** — 그리고 두 엔진이 가진 도구가 왜 다른가.
3. **집계·정렬은 계획에서 어떤 모습인가** — 해시로 묶을 때와 줄 세워 묶을 때가 어떻게 다른가.

## 예시 데이터 — 이 묶음이 공유하는 것

이 편만은 `emp`·`dept`(4행·3행)를 못 쓴다. **표가 작으면 엔진이 언제나 전체 스캔을 고른다** — 고를 것이 없다.

```sql
-- PG: BEGIN … ROLLBACK 안에서 / MySQL: 끝나고 DROP TABLE
CREATE TABLE t59_big   AS SELECT g AS id, (g % 1000) AS grp, (g % 50000) AS val, repeat('x',20) AS pad
                          FROM generate_series(1,200000) g;        -- 20만 행
ALTER TABLE t59_big ADD PRIMARY KEY (id);
CREATE INDEX t59_big_grp ON t59_big (grp);
CREATE TABLE t59_mid   AS SELECT g AS id, g*2 AS ref, g AS val FROM generate_series(1,50000) g;  -- 5만 행
ALTER TABLE t59_mid ADD PRIMARY KEY (id);
CREATE TABLE t59_small AS SELECT g AS id, g*3 AS ref FROM generate_series(1,10) g;               -- 10행
```

```text
t59_big  (200,000행)                t59_mid (50,000행)      t59_small (10행)
+--------+-------+-------+-----+    +-------+------+-----+  +------+------+
| id PK  | grp   | val   | pad |    | id PK | ref  | val |  | id   | ref  |
+--------+-------+-------+-----+    +-------+------+-----+  +------+------+
| 1      | 1     | 1     | xx… |    | 1     | 2    | 1   |  | 1    | 3    |
| 2      | 2     | 2     | xx… |    | 2     | 4    | 2   |  | 2    | 6    |
| …      | …     | …     |     |    | …     | …    | …   |  | …    | …    |
| 200000 | 0     | 0     | xx… |    | 50000 | 1e5  | 5e4 |  | 10   | 30   |
+--------+-------+-------+-----+    +-------+------+-----+  +------+------+
  grp: 값마다 200행                    ref 와 val 에는 인덱스가 없다
  val: 값마다 4행
  인덱스: id(PK) · grp
```

**인덱스를 일부러 일부 열에만 걸었다** — `val`·`ref` 에는 인덱스가 없다. 그래야 「인덱스가 없을 때」를 볼 수 있다.

## 동작 방식

### 1. 스캔 연산자 — 표의 행에 닿는 네 가지 방법

**언제 쓰나** — 계획의 **맨 아래**에 늘 하나씩 있다. 트리의 잎이 전부 스캔이다.

```text
                        인덱스를 쓰나?
                       /            \
                     아니오          예
                      |              \
                  Seq Scan        필요한 열이 전부 인덱스에 있나?
                 (표를 통째로)      /                    \
                                 예                     아니오
                                  |                        \
                          Index Only Scan          찾는 행이 하나인가 흩어져 있나?
                          (표를 안 읽는다)            /                  \
                                                  하나                 여럿
                                                    |                    \
                                              Index Scan          Bitmap Heap Scan
                                            (바로 그 자리로)        (자리를 모아 한 번에)
```

**(A) `Index Scan` — 한 행을 찍어 간다**

```text
### SQL: EXPLAIN SELECT * FROM t59_big WHERE id = 500;
--- PG 18.6 ---
 Index Scan using t59_big_pkey on t59_big  (cost=0.42..8.44 rows=1 width=33)
   Index Cond: (id = 500)
--- MySQL 8.4.10 ---
| table   | type  | key     | rows | Extra |
| t59_big | const | PRIMARY |    1 | NULL  |
```

> **표 테두리를 지웠다.** MySQL `EXPLAIN` 의 12칸 표는 그대로 실으면 화면을 넘는다.
> 이 편의 MySQL 블록은 전부 `id`·`select_type`·`partitions`·`possible_keys`·`key_len`·`ref`·`filtered` 칸 중
> 그 절에 필요 없는 것과 `+---+` 테두리를 지운 것이다. **남긴 칸의 값은 원본 그대로다.**

MySQL 의 `type=const` 는 「**기본키에 상수 하나 — 많아야 한 행**」이다. `Index Scan` 보다 더 센 판정이다.

**(B) `Bitmap Heap Scan` — 자리를 모아서 한 번에 (PG 에만 있다)**

```text
### SQL: EXPLAIN SELECT * FROM t59_big WHERE grp = 7;    -- 200행 / 200,000 = 0.1%
--- PG 18.6 ---
 Bitmap Heap Scan on t59_big  (cost=5.84..576.81 rows=199 width=33)
   Recheck Cond: (grp = 7)
   ->  Bitmap Index Scan on t59_big_grp  (cost=0.00..5.79 rows=199 width=0)
         Index Cond: (grp = 7)
--- MySQL 8.4.10 ---
| table   | type | key   | rows | Extra |
| t59_big | ref  | k_grp |  200 | NULL  |
```

```text
 Index Scan (한 행씩 표를 오간다)        Bitmap (자리를 다 모은 뒤 한 번에)
 인덱스 -> 표 -> 인덱스 -> 표 -> …       인덱스 전부 -> 자리 비트맵 -> 표를 앞에서 뒤로 한 번
   페이지를 널뛰며 읽는다                  페이지 순서대로 읽는다 (디스크에 유리)
```

그림 해설 — `Bitmap Index Scan` 이 **맞는 행들의 자리를 먼저 다 모으고**, `Bitmap Heap Scan` 이 그 자리를 **표 순서대로** 한 번에 읽는다.\
**MySQL 에는 이 연산자가 없다.** 같은 조건을 `type=ref` 한 줄로 처리한다 — 인덱스에서 찾은 자리를 그때그때 읽는다.

`Recheck Cond` 는 비트맵이 페이지 단위로 뭉개졌을 때를 대비한 재확인이다 — 조건이 두 번 적힌 이유가 이것이다.

`OR` 두 개도 한 비트맵으로 합쳐진다.

```text
### SQL: EXPLAIN SELECT * FROM t59_big WHERE grp = 7 OR grp = 9;
--- PG 18.6 ---
 Bitmap Heap Scan on t59_big  (cost=11.67..958.84 rows=398 width=33)
   Recheck Cond: ((grp = 7) OR (grp = 9))
   ->  Bitmap Index Scan on t59_big_grp  (cost=0.00..11.57 rows=398 width=0)
         Index Cond: (grp = ANY ('{7,9}'::integer[]))
```

**(C) `Seq Scan` — 전부 훑는다**

```text
### SQL: EXPLAIN SELECT * FROM t59_big WHERE grp < 900;   -- 180,000행 = 90%
--- PG 18.6 ---
 Seq Scan on t59_big  (cost=0.00..4228.00 rows=180101 width=33)
   Filter: (grp < 900)
--- MySQL 8.4.10 ---
| table   | type | possible_keys | key  | rows   | filtered | Extra       |
| t59_big | ALL  | k_grp         | NULL | 199699 |    50.00 | Using where |
```

★ **MySQL 의 `possible_keys` 에 `k_grp` 가 있는데 `key` 는 `NULL` 이다** — **쓸 수 있었는데 안 썼다.**\
이 두 칸의 대비가 「인덱스가 없다」와 「인덱스를 안 골랐다」를 가른다.

**(D) `Index Only Scan` — 표를 아예 안 읽는다**

```text
### SQL: EXPLAIN SELECT id FROM t59_big ORDER BY id LIMIT 5;
--- PG 18.6 ---
 Limit  (cost=0.42..0.59 rows=5 width=4)
   ->  Index Only Scan using t59_big_pkey on t59_big  (cost=0.42..6935.42 rows=200000 width=4)

### SQL: EXPLAIN SELECT grp FROM t59_big WHERE grp = 7;
--- MySQL 8.4.10 ---
| table   | type | key   | rows | Extra       |
| t59_big | ref  | k_grp |  200 | Using index |
```

그림 해설 — **필요한 열이 전부 인덱스 안에 있으면 표를 펼 필요가 없다.** PG 는 노드 이름으로, MySQL 은 `Extra: Using index` 로 알려 준다.\
이것을 **커버링 인덱스(covering index)** 라 부르고, 인덱스 설계의 목표 중 하나다([46 인덱스 정의](../46-index-definition-composite-partial-expression/)).

비용 — 인덱스만 읽으므로 페이지 수가 확 준다. 대가는 **인덱스가 커진다**는 것이다(열을 더 담았으니).

> **커버링 인덱스(covering index)** — 질의가 필요로 하는 열을 전부 담고 있어 표를 안 읽어도 되는 인덱스.\
> 예: `SELECT grp FROM t WHERE grp = 7` 은 `grp` 인덱스만으로 답이 나온다.

---

### 2. ★ 어디서 갈리나 — 선택도를 바꿔 가며 찍는다

**언제 쓰나** — 「인덱스를 걸었는데 왜 안 타지?」를 풀 때. **답은 %다.**

`grp < N` 의 N 을 키워 가며 같은 트랜잭션 안에서 한 번에 찍었다.

```text
--- PG 18.6 (한 트랜잭션 · 병렬 끔) ---

grp < 50     Bitmap Heap Scan  (cost=112.62..1963.72 rows=9848)      5%
grp < 200    Bitmap Heap Scan  (cost=439.47..2656.47 rows=39120)   20%
grp < 520    Bitmap Heap Scan  (cost=1146.04..4160.73 rows=102935) 51%   <- 경계 (3절)
grp < 540    Seq Scan          (cost=0.00..4228.00 rows=107169)    54%   <- 갈렸다
grp < 900    Seq Scan          (cost=0.00..4228.00 rows=180101)    90%
```

```text
--- MySQL 8.4.10 ---

grp = 7      type=ref    key=k_grp   rows=200                       0.1%
grp < 50     type=range  key=k_grp   rows=19720                    10%
grp < 120    type=range  key=k_grp   rows=47136                    24%
grp < 140    type=range  key=k_grp   rows=55890                    28%
grp < 150    type=ALL    key=NULL    rows=199699 filtered=31.18    30%   <- 갈렸다
grp < 200    type=ALL    key=NULL    rows=199699 filtered=43.04    40%
```

```text
 PostgreSQL 이 인덱스를 놓는 지점        MySQL 이 인덱스를 놓는 지점
 +---------------------------+          +---------------------------+
 | 약 52% 근처               |          | 30% 근처 (140 과 150 사이) |
 | Bitmap 이 순서대로 읽어서   |          | 한 행씩 표를 오가므로       |
 | 랜덤 접근 비용이 낮다       |          | 랜덤 접근이 비싸다          |
 +---------------------------+          +---------------------------+
   -> 두 엔진의 전환점이 다르다. 도구가 다르기 때문이다.
```

그림 해설 — **PG 가 훨씬 늦게까지 인덱스를 쓴다.** `Bitmap` 이라는 중간 도구가 있어서다(1절 B).\
MySQL 은 비트맵이 없어 인덱스로 찾은 행을 그때그때 표에서 읽는데, 그 랜덤 접근이 비싸 일찍 포기한다.

**판단의 근거는 비용 한 줄이다.**

```text
Seq Scan 의 비용은 조건과 무관하게 언제나  cost=0.00..4228.00
Bitmap 의 비용은 읽을 행 수에 따라 는다:
   grp < 50    -> 1963.72   <  4228.00   -> Bitmap 을 고른다
   grp < 200   -> 2656.47   <  4228.00   -> Bitmap 을 고른다
   grp < 520   -> 4160.73   ~= 4228.00   -> 아슬아슬하다   <- 3절
```

비용 — 인덱스는 「적게 읽는」 도구이지 「빠른」 도구가 아니다. **많이 읽을 거면 순서대로 읽는 편이 싸다.**

---

### 3. ★ 전환점 근처에서는 계획이 흔들린다 — 8판을 돌려 봤다

**언제 쓰나** — 계획을 근거로 결론을 쓸 때. **이 절이 이 묶음의 계약이다.**

2절의 전환점(`grp < 520`)에서 **똑같은 스크립트를 8번 돌렸다.** 같은 서버·같은 버전·같은 생성 코드다.

```text
--- PG 18.6 · 동일 스크립트 8판 (표 생성 → ANALYZE → EXPLAIN, 매판 새 트랜잭션) ---
판1:  Bitmap Heap Scan on t59_big  (cost=1153.63..4174.10 rows=103398 width=33)
판2:  Seq Scan on t59_big          (cost=0.00..4228.00 rows=104162 width=33)
판3:  Bitmap Heap Scan on t59_big  (cost=1158.02..4185.59 rows=103965 width=33)
판4:  Seq Scan on t59_big          (cost=0.00..4228.00 rows=104967 width=33)
판5:  Seq Scan on t59_big          (cost=0.00..4228.00 rows=104060 width=33)
판6:  Bitmap Heap Scan on t59_big  (cost=1156.46..4181.50 rows=103763 width=33)
판7:  Seq Scan on t59_big          (cost=0.00..4228.00 rows=104157 width=33)
판8:  Bitmap Heap Scan on t59_big  (cost=1157.44..4184.07 rows=103890 width=33)
```

```text
 바뀐 것                                안 바뀐 것
 +---------------------------+         +---------------------------+
 | 연산자: Bitmap 4판 / Seq 4판|         | 데이터 (같은 생성 코드)     |
 | 추정 행 수: 103,398~104,967 |         | 버전 (PG 18.6)            |
 | Bitmap 의 총비용: 4174~4186 |         | Seq Scan 의 비용 4228.00   |
 +---------------------------+         +---------------------------+
   흔들린 원인: ANALYZE 의 표본이 판마다 다르다
```

그림 해설 — **`ANALYZE` 는 표를 전수 세지 않고 표본으로 추정한다.** 그 추정이 ±0.8% 흔들렸고,\
Bitmap 의 총비용이 `Seq Scan` 의 4228.00 **바로 아래를 오가는 지점**이라 그 흔들림이 곧 연산자 선택을 뒤집었다.\
★ **버전도 데이터도 안 바꿨는데 연산자가 반반으로 갈렸다** — [19번](../19-semi-anti-join/)의 MySQL 실측과 같은 성격의 일이다.

대가 — 그래서 **「이 질의는 비트맵 스캔을 쓴다」고 적으면 안 된다.**\
「이 데이터·이 통계에서 비용이 이렇게 나왔고, 그 결과 비트맵이 뽑혔다」로 적는다.\
근거로 쓸 칸도 흔들리는 `cost`·`rows` 가 아니라 **`Index Cond`·`actual rows`·연산자 이름**이다([09번](../09-limit-offset-keyset-pagination/)이 그렇게 했다).

**전환점에서 먼 자리는 흔들리지 않았다** — `grp < 50` 은 8판 내내 `Bitmap`, `grp < 900` 은 내내 `Seq Scan` 이었다.\
**흔들리는 것은 경계다.** 결론을 경계 위에 세우지 않으면 된다.

---

### 4. ★ 조인 연산자 셋 — 무엇이 고르나

**언제 쓰나** — 조인이 느릴 때. **먼저 어느 연산자가 뽑혔는지 본다.**

```text
 Nested Loop                    Hash Join                       Merge Join
 바깥 행 하나마다                한쪽으로 해시 표를 만들고         양쪽을 정렬해 놓고
 안쪽을 찾는다                   다른 쪽을 흘려 보낸다             지퍼 올리듯 맞춘다
 +-------------------+          +-------------------+           +-------------------+
 | for r in 바깥:     |          | 작은 쪽 -> 해시    |           | 양쪽 포인터를      |
 |   안쪽에서 r 찾기  |          | 큰 쪽을 훑으며 조회 |           | 나란히 전진        |
 +-------------------+          +-------------------+           +-------------------+
  바깥이 작고 안쪽에              양쪽이 크고 조인 키에            양쪽이 이미 정렬돼
  인덱스가 있을 때                인덱스가 없을 때                 있을 때 (인덱스 순서)
```

**바깥 표의 크기를 10행 → 50,000행으로 바꾸면 연산자가 갈린다.**

```text
### SQL: EXPLAIN SELECT s.id, b.pad FROM t59_small s JOIN t59_big b ON b.id = s.ref;   -- 바깥 10행
--- PG 18.6 ---
 Merge Join  (cost=1.71..2.95 rows=10 width=25)
   Merge Cond: (b.id = s.ref)
   ->  Index Scan using t59_big_pkey on t59_big b  (cost=0.42..6935.42 rows=200000 width=25)
   ->  Sort  (cost=1.27..1.29 rows=10 width=8)
         Sort Key: s.ref
         ->  Seq Scan on t59_small s  (cost=0.00..1.10 rows=10 width=8)

### SQL: EXPLAIN SELECT m.id, b.pad FROM t59_mid m JOIN t59_big b ON b.id = m.ref;     -- 바깥 50,000행
--- PG 18.6 ---
 Hash Join  (cost=1445.00..6423.00 rows=50000 width=25)
   Hash Cond: (b.id = m.ref)
   ->  Seq Scan on t59_big b  (cost=0.00..3728.00 rows=200000 width=25)
   ->  Hash  (cost=820.00..820.00 rows=50000 width=8)
         ->  Seq Scan on t59_mid m  (cost=0.00..820.00 rows=50000 width=8)
```

그림 해설 — **10행일 때는 `Merge Join`, 50,000행일 때는 `Hash Join`** 이다. 같은 질의 모양·같은 안쪽 표인데 갈렸다.\
10행일 때는 「정렬 비용이 1.29 밖에 안 되니 정렬해서 지퍼 올리자」가 싸고,\
50,000행일 때는 「인덱스를 5만 번 타느니 20만 행을 한 번 훑자」가 싸다.

**`Nested Loop` 는 이 데이터에서 자연스럽게는 안 뽑혔다.** 강제로 꺼내 비용을 비교해 보면 왜인지 보인다.

```text
### SQL: SET enable_mergejoin = off;  EXPLAIN (바깥 10행 · 같은 질의)
--- PG 18.6 ---
 Nested Loop  (cost=0.42..85.48 rows=10 width=25)
   ->  Seq Scan on t59_small s  (cost=0.00..1.10 rows=10 width=8)
   ->  Index Scan using t59_big_pkey on t59_big b  (cost=0.42..8.44 rows=1 width=25)
         Index Cond: (id = s.ref)
```

```text
 바깥 10행일 때 세 연산자의 비용          결론
 Merge Join        2.95                 <- 뽑혔다
 Nested Loop      85.48                 (머지를 끄면 이것)
                                        10 x 8.44 = 84.4 + 1.1 = 85.48
```

★ **`Nested Loop` 의 비용 구조가 계획에 그대로 드러난다** — 안쪽 `Index Scan` 의 전체 비용 **8.44 를 바깥 행 수 10 만큼** 치른다.\
바깥이 50,000행이면 이 값이 31,811 까지 뛴다(둘 다 끄고 찍어 확인했다). **바깥 크기에 곱해지는 것이 중첩 루프의 성질이다.**

**양쪽 조인 키에 인덱스가 있으면 5만 행이어도 `Merge Join` 이다.**

```text
### SQL: EXPLAIN SELECT b.id, m.ref FROM t59_big b JOIN t59_mid m ON m.id = b.id;
--- PG 18.6 ---
 Merge Join  (cost=1.38..4114.72 rows=50000 width=8)
   Merge Cond: (b.id = m.id)
   ->  Index Only Scan using t59_big_pkey on t59_big b  (cost=0.42..6935.42 rows=200000 width=4)
   ->  Index Scan using t59_mid_pkey on t59_mid m  (cost=0.29..1629.29 rows=50000 width=8)
```

**양쪽 다 인덱스 순서로 읽으니 정렬이 공짜다** — `Sort` 노드가 없다. 그래서 해시보다 싸졌다.

**조인 키에 인덱스가 없으면 무조건 `Hash Join` 이다.**

```text
### SQL: EXPLAIN SELECT count(*) FROM t59_mid m JOIN t59_big b ON b.val = m.val;   -- val 에 인덱스 없음
--- PG 18.6 ---
 Aggregate  (cost=8418.96..8418.97 rows=1 width=8)
   ->  Hash Join  (cost=1445.00..7919.77 rows=199677 width=0)
         Hash Cond: (b.val = m.val)
         ->  Seq Scan on t59_big b  (cost=0.00..3728.00 rows=200000 width=4)
         ->  Hash  (cost=820.00..820.00 rows=50000 width=4)
               ->  Seq Scan on t59_mid m  (cost=0.00..820.00 rows=50000 width=4)
```

**해시 표는 언제나 작은 쪽으로 만든다** — `Hash` 밑에 있는 것이 5만 행짜리 `t59_mid` 다.

---

### 5. ★ MySQL 의 조인 도구는 둘뿐이다

**언제 쓰나** — 두 엔진의 계획을 대조할 때. **`Merge Join` 을 찾으면 안 나온다.**

```text
### SQL: EXPLAIN FORMAT=TREE SELECT s.id, b.pad FROM t59_small s JOIN t59_big b ON b.id = s.ref;
--- MySQL 8.4.10 ---
-> Nested loop inner join  (cost=4.75 rows=10)
    -> Filter: (s.ref is not null)  (cost=1.25 rows=10)
        -> Table scan on s  (cost=1.25 rows=10)
    -> Single-row index lookup on b using PRIMARY (id=s.ref)  (cost=0.26 rows=1)

### SQL: EXPLAIN FORMAT=TREE SELECT count(*) FROM t59_mid m JOIN t59_big b ON b.val = m.val;
--- MySQL 8.4.10 ---
-> Aggregate: count(0)  (cost=1.11e+9 rows=1)
    -> Inner hash join (b.val = m.val)  (cost=1.01e+9 rows=1.01e+9)
        -> Table scan on b  (cost=0.0466 rows=199699)
        -> Hash
            -> Table scan on m  (cost=5101 rows=50610)
```

| 상황 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 바깥 10행 · 안쪽 기본키 | `Merge Join` | **`Nested loop inner join`** |
| 바깥 5만행 · 안쪽 기본키 | `Hash Join` | **`Nested loop inner join`** |
| 양쪽 기본키 | `Merge Join` | (해당 계획 없음 — 항상 중첩 루프) |
| 조인 키에 인덱스 없음 | `Hash Join` | `Inner hash join` |

```text
 PostgreSQL 의 조인 도구               MySQL 8.4.10 의 조인 도구
 +---------------------------+        +---------------------------+
 | Nested Loop               |        | Nested loop               |
 | Hash Join                 |        | Hash join (8.0.18~)       |
 | Merge Join                |        | (머지 조인 없음)            |
 +---------------------------+        +---------------------------+
   -> 인덱스가 있으면 MySQL 은 거의 언제나 중첩 루프다
```

그림 해설 — **MySQL 은 조인 키에 인덱스가 있으면 중첩 루프를 고른다.** 바깥이 5만 행이어도 그렇다.\
그래서 MySQL 쪽 조인 튜닝은 「**안쪽 표에 인덱스가 있나**」에 훨씬 더 크게 걸린다.

★ **MySQL 의 해시 조인 추정 행 수가 `1.01e+9` 다.** 같은 조인을 실제로 세어 보면 **199,996행**이다.

```text
### SQL: SELECT count(*) AS joined FROM t59_mid m JOIN t59_big b ON b.val = m.val;
--- MySQL 8.4.10 ---
+--------+
| joined |
+--------+
| 199996 |
+--------+
```

**추정이 실측의 5,000배가 넘는다.** (같은 조인을 PG 는 `rows=199677` 로 추정했다 — 실측 199,996 에 가깝다.)\
이 어긋남을 읽는 법이 [60번](../60-explain-analyze-estimates-vs-actuals/)의 주제다.

★ **MySQL 이 `Filter: (s.ref is not null)` 을 스스로 덧붙였다.** 질의문에 없던 조건이다 —\
내부 조인에서 `NULL` 은 어차피 짝이 없으므로 미리 버린다([13번](../13-inner-join/)).

---

### 6. 정렬·집계 연산자 — 해시로 묶나 줄 세워 묶나

**언제 쓰나** — `GROUP BY`·`DISTINCT`·`ORDER BY` 가 느릴 때.

```text
 HashAggregate                          GroupAggregate
 +---------------------------+         +---------------------------+
 | 그룹 키로 해시 표를 만들고  |         | 먼저 정렬해서 같은 키를    |
 | 값을 누적한다              |         | 붙여 놓고 훑으며 센다      |
 | 순서가 없다               |         | 순서대로 나온다            |
 | 그룹 수만큼 메모리가 든다   |         | 메모리는 거의 안 든다       |
 +---------------------------+         +---------------------------+
   그룹 수가 적을 때 유리               이미 정렬돼 있을 때 유리
```

```text
### SQL: EXPLAIN SELECT grp, count(*) FROM t59_big GROUP BY grp;      -- 1,000 그룹
--- PG 18.6 ---
 HashAggregate  (cost=4728.00..4738.00 rows=1000 width=12)
   Group Key: grp
   ->  Seq Scan on t59_big  (cost=0.00..3728.00 rows=200000 width=4)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Group aggregate: count(0)  (cost=40124 rows=1004)
    -> Covering index scan on t59_big using k_grp  (cost=20154 rows=199699)
```

★ **같은 질의에 두 엔진이 다른 방법을 골랐다** — PG 는 해시로 묶고(표를 훑으며), MySQL 은 **`grp` 인덱스 순서를 그대로 써서** 줄 세워 묶는다.\
MySQL 쪽은 인덱스가 이미 `grp` 순서라 정렬이 공짜다. PG 쪽은 인덱스를 안 타는 편이 싸다고 봤다.

**인덱스가 없는 열로 묶으면 MySQL 도 임시 표를 쓴다.**

```text
### SQL: EXPLAIN SELECT val, count(*) FROM t59_big GROUP BY val;      -- 50,000 그룹 · val 에 인덱스 없음
--- PG 18.6 ---
 HashAggregate  (cost=4728.00..5228.81 rows=50081 width=12)
   Group Key: val
   ->  Seq Scan on t59_big  (cost=0.00..3728.00 rows=200000 width=4)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Table scan on <temporary>
    -> Aggregate using temporary table
        -> Table scan on t59_big  (cost=20154 rows=199699)
```

**PG 에서 해시 집계를 끄면 다른 길이 보인다.**

```text
### SQL: SET enable_hashagg = off;  EXPLAIN SELECT grp, count(*) FROM t59_big GROUP BY grp;
--- PG 18.6 ---
 GroupAggregate  (cost=0.29..11598.16 rows=1000 width=12)
   Group Key: grp
   ->  Index Only Scan using t59_big_grp on t59_big  (cost=0.29..10588.16 rows=200000 width=4)
```

그림 해설 — `GroupAggregate` 를 쓰려면 **입력이 그룹 키 순서**여야 해서, 스캔까지 `Index Only Scan` 으로 바뀌었다.\
**연산자 하나를 바꾸면 그 아래 스캔도 따라 바뀐다** — 계획은 한 덩어리로 고른다.

**`ORDER BY` 는 집계 위에 별도 `Sort` 로 얹힌다.**

```text
### SQL: EXPLAIN SELECT grp, count(*) c FROM t59_big GROUP BY grp ORDER BY grp;
--- PG 18.6 ---
 Sort  (cost=4787.83..4790.33 rows=1000 width=12)
   Sort Key: grp
   ->  HashAggregate  (cost=4728.00..4738.00 rows=1000 width=12)
         Group Key: grp
         ->  Seq Scan on t59_big  (cost=0.00..3728.00 rows=200000 width=4)
```

★ **`GROUP BY grp` 를 했다고 `grp` 순서로 나오지 않는다.** 해시로 묶었으니 순서가 없고,\
`ORDER BY grp` 를 썼기 때문에 **`Sort` 가 따로 붙었다.** 「`GROUP BY` 하면 정렬되더라」는 관찰이지 보장이 아니다([08번](../08-order-by-null-position-stability/)).

**집계 함수만 쓰면 `Aggregate` 한 노드다.**

```text
### SQL: EXPLAIN SELECT count(*) FROM t59_big;
--- PG 18.6 ---
 Aggregate  (cost=4228.00..4228.01 rows=1 width=8)
   ->  Seq Scan on t59_big  (cost=0.00..3728.00 rows=200000 width=0)
--- MySQL 8.4.10 ---
| table   | type  | key   | rows   | Extra       |
| t59_big | index | k_grp |199699  | Using index |
```

**두 엔진이 읽는 대상이 다르다** — PG 는 표를 훑었고(`Seq Scan`), MySQL 은 **표가 아니라 `k_grp` 인덱스를 훑었다**(`type=index`·`key=k_grp`·`Using index`).\
`count(*)` 는 열 값이 필요 없으므로 **어느 인덱스를 훑어도 답이 같다**는 것을 쓴 것이다.

**MySQL 에만 있는 도구도 있다.**

```text
### SQL: EXPLAIN SELECT DISTINCT grp FROM t59_big;
--- PG 18.6 ---
 HashAggregate  (cost=4228.00..4238.00 rows=1000 width=4)
   Group Key: grp
   ->  Seq Scan on t59_big  (cost=0.00..3728.00 rows=200000 width=4)
--- MySQL 8.4.10 ---
| table   | type  | key   | rows | Extra                    |
| t59_big | range | k_grp | 1005 | Using index for group-by |
```

★ **`Using index for group-by` 는 20만 행을 안 읽는다** — 인덱스에서 **값이 바뀌는 자리만 건너뛰며** 1,005행만 본다.\
PG 는 20만 행을 다 훑었다(`rows=200000`). **같은 질의에서 읽는 행 수가 200배 차이 난다.**\
(PG 에도 비슷한 것이 있지만 이 데이터·이 계획에서는 뽑히지 않았다.)

## 문법 — 어느 절에서 무엇이 보이나

SQL 에서 이 절의 본체는 형태가 아니라 「**연산자를 어떻게 확인하고 어떻게 강제하나**」다.

```sql
-- PostgreSQL: 실험용으로 연산자를 끈다 (운영에서 쓰지 않는다)
SET enable_seqscan = off;      SET enable_indexscan = off;
SET enable_bitmapscan = off;   SET enable_indexonlyscan = off;
SET enable_nestloop = off;     SET enable_hashjoin = off;   SET enable_mergejoin = off;
SET enable_hashagg = off;      SET enable_sort = off;
RESET ALL;                     -- 되돌린다
SET max_parallel_workers_per_gather = 0;   -- 병렬 노드를 없애 계획을 단순하게

-- MySQL: 옵티마이저 스위치와 힌트
SET SESSION optimizer_switch = 'block_nested_loop=off';     -- 해시 조인을 끈다
SELECT /*+ NO_HASH_JOIN(t1, t2) */ …;
SELECT /*+ INDEX(t idx) */ … ;                              -- 인덱스를 지정
EXPLAIN FORMAT=TREE SELECT …;                               -- 연산자 이름이 보이는 형식
```

- **`enable_*` 는 금지가 아니라 벌점이다.** PG 는 그 연산자에 막대한 비용을 매겨 사실상 안 고르게 한다.
  다른 길이 아예 없으면 그래도 쓴다.
- **운영 설정으로 끄지 않는다.** 실험으로 「왜 이걸 안 골랐나」를 비교할 때만 쓴다(4절이 그 용도다).
- MySQL 의 **`possible_keys` 와 `key`** 두 칸을 나눠 읽는 습관이 중요하다 — 후보가 없는 것과 안 고른 것은 처방이 다르다.
- 어느 연산자가 뽑혔는지는 **`EXPLAIN` 으로 충분**하다. 그것이 정말 그렇게 돌았는지는 `EXPLAIN ANALYZE` 가 필요하다([60번](../60-explain-analyze-estimates-vs-actuals/)).

## 어디서 틀리나

| 틀리는 자리 | 무슨 일이 일어나나 | 근거 |
|---|---|---|
| 「인덱스를 걸었는데 안 탄다」 | **많이 읽을 거면 안 타는 게 싸다.** 선택도 문제다 | 2절 |
| PG 의 전환점을 MySQL 에도 적용한다 | PG 는 ~52%, MySQL 은 ~30% 에서 갈렸다 | 2절 |
| `Seq Scan` 이 보이면 무조건 나쁘다고 본다 | 90% 를 읽는 질의에서는 그게 최선이다 | 2절 |
| `possible_keys` 가 있으니 인덱스를 썼다고 본다 | **`key=NULL` 이면 안 썼다** | 1절 (C) |
| 한 번 본 연산자를 그 질의의 성질로 외운다 | **같은 스크립트 8판에서 4:4 로 갈렸다** | 3절 |
| `Nested Loop` 가 항상 나쁘다고 본다 | 바깥이 작으면 가장 싸다. 바깥에 **곱해지는** 것이 문제다 | 4절 |
| MySQL 계획에서 `Merge Join` 을 찾는다 | **MySQL 에 머지 조인이 없다** | 5절 |
| MySQL 이 5만 행 바깥에도 중첩 루프를 쓰는 걸 버그로 본다 | 인덱스가 있으면 그렇게 고른다 — 설계상 그렇다 | 5절 |
| `GROUP BY` 하면 정렬돼 나온다고 믿는다 | `HashAggregate` 는 순서가 없다. `Sort` 가 따로 붙는다 | 6절 |
| `Hash Join` 의 해시 표가 큰 쪽으로 만들어진다고 본다 | **작은 쪽으로 만든다** | 4절 |
| MySQL 의 `rows=1.01e+9` 를 사실로 읽는다 | **추정이고 5,000배 넘게 틀렸다** | 5절 · 60번 |

## 구현 세부사항 대 언어 보장

| 항목 | 성격 | 근거 |
|---|---|---|
| 연산자의 존재(`Bitmap`·`Merge Join`) | **엔진 차이** — MySQL 에 둘 다 없다 | 1·5절 |
| 선택도에 따라 스캔이 갈리는 것 | **양쪽 공통 원리** — 갈리는 %는 다르다 | 2절 |
| 전환점의 정확한 % | **이 데이터·이 통계의 값** — 표 폭·행 수가 바뀌면 이동한다 | 2·3절 |
| 경계에서 연산자가 흔들리는 것 | **실측** — 같은 스크립트 8판에서 4:4 | 3절 |
| 조인 연산자 선택 | **옵티마이저의 선택** — 두 엔진이 같은 질의에 다르게 답했다 | 4·5절 |
| 해시 표를 작은 쪽으로 만드는 것 | **양쪽 공통** | 4·5절 |
| MySQL 의 `Using index for group-by` | **MySQL 의 최적화** — PG 쪽 계획에는 안 나왔다 | 6절 |
| `Nested Loop` 비용이 바깥 행 수에 곱해지는 것 | **계획 숫자로 확인** (8.44 × 10 + 1.1 = 85.48) | 4절 |

★ **이 편의 모든 계획은 「관찰」이다.** 3절이 그 증거를 직접 만들었다.\
제출 직전에 본문의 계획을 다시 찍어 대조한 결과는 3-answer 의 「실행 검증」에 있다.

## 언제 쓰고 언제 안 쓰나

```text
 이 주제를 꺼내는 자리                  이 주제로 답이 안 나오는 자리
 +---------------------------+        +---------------------------+
 | 질의가 느린데 왜인지 모른다  |        | 결과가 틀렸다 (-> 01·04번)  |
 | 인덱스를 걸었는데 안 탄다    |        | 인덱스를 어떻게 정의하나    |
 | 조인 하나가 유난히 느리다    |        |   (-> 46번 · 47번 주제)     |
 | 계획이 어제와 다르다        |        | 해시·정렬 알고리즘 자체     |
 +---------------------------+        |   (-> data-structure/ 등)  |
                                      +---------------------------+
```

- **연산자 이름은 진단의 시작이지 처방이 아니다.** `Seq Scan` 이 보였다고 인덱스를 거는 게 아니라,
  **몇 %를 읽는 질의인지** 먼저 본다.
- **경계 근처의 질의는 처방을 쓰지 않는다.** 3절처럼 흔들리는 자리라면, 질의를 고쳐 **경계에서 떨어뜨리는 것**이 처방이다.
- 「어느 연산자가 뽑혔나」까지는 `EXPLAIN` 으로 보고, **「그게 정말 그만큼 돌았나」는 `EXPLAIN ANALYZE`** 로 본다(60번).

## 핵심 문장

1. **스캔은 넷이다** — `Seq Scan`·`Index Scan`·`Index Only Scan`·`Bitmap`(PG 에만). 고르는 기준은 **선택도**다.
2. **인덱스는 「적게 읽는」 도구이지 「빠른」 도구가 아니다** — 많이 읽을 거면 순서대로 훑는 게 싸다.
3. **전환점은 엔진마다 다르다** — 이 데이터에서 PG 는 약 52%, MySQL 은 약 30% 에서 인덱스를 놓았다.
4. **전환점 근처에서는 계획이 흔들린다** — 같은 스크립트 8판에서 `Bitmap` 4판 · `Seq Scan` 4판이 나왔다.
5. **조인은 셋이다** — 바깥이 작으면 `Nested Loop`, 양쪽이 크면 `Hash Join`, 양쪽이 정렬돼 있으면 `Merge Join`.
6. **MySQL 의 조인 도구는 둘뿐이다** — 머지 조인이 없고, 인덱스가 있으면 거의 언제나 중첩 루프다.
7. **`HashAggregate` 는 순서를 만들지 않는다** — `GROUP BY` 했다고 정렬돼 나오지 않는다.

## 관련 자료

- [`data-structure/05-hashmap`](../../../../../data-structure/05-hashmap/) — **그쪽은 해시 표가 충돌을 어떻게 다루고 언제 커지나(자료구조 자체)까지, 여기는 계획에 `Hash Join`·`HashAggregate` 라는 이름이 떴을 때 그것이 무슨 뜻이고 왜 뽑혔나부터다.** 해시 함수·적재율은 그쪽, 「해시 표를 작은 쪽으로 만든다」는 여기.
- [`algorithm/02-merge-sort`](../../../../../algorithm/02-merge-sort/) — **그쪽은 병합 정렬의 절차와 복잡도(알고리즘 자체)까지, 여기는 `Merge Join`·`Sort` 노드가 계획에 뜨는 조건부터다.** 「왜 O(n log n)인가」는 그쪽, 「양쪽이 정렬돼 있으면 정렬이 공짜다」는 여기.
- [58 `EXPLAIN` 읽기](../58-explain-plan-tree/) — 계획을 읽는 법. **이 편은 그 계획에 뜨는 이름들을 다룬다.**
- [60 `EXPLAIN ANALYZE`](../60-explain-analyze-estimates-vs-actuals/) — 5절의 `rows=1.01e+9` 같은 어긋남을 읽는 법.
- [09 LIMIT·OFFSET](../09-limit-offset-keyset-pagination/) — `Index Only Scan` 과 `actual rows` 로 비용을 잰 전례.
- [19 세미·안티 조인](../19-semi-anti-join/) — 같은 서버에서 계획이 두 번 달랐던 실측. 3절과 같은 성격이다.
- [46 인덱스 정의](../46-index-definition-composite-partial-expression/) — **그쪽은 커버링·복합·부분 인덱스를 어떻게 정의하나(문법)까지, 여기는 그 인덱스가 계획에 어떤 연산자로 뜨나부터다.**

## 용어 풀이

- **선택도(selectivity)** — 조건이 전체 중 몇 %를 남기나. 예: 20만 행에서 200행이면 0.1%.
- **`Seq Scan`** — 표를 처음부터 끝까지 순서대로 읽는 것. MySQL 의 `type=ALL`. 예: `grp < 900`.
- **`Index Scan`** — 인덱스로 자리를 찾아 표의 그 행을 읽는 것. 예: `WHERE id = 500`.
- **`Index Only Scan`** — 필요한 열이 인덱스 안에 다 있어 표를 안 읽는 것. MySQL 의 `Extra: Using index`.
- **`Bitmap Heap Scan`**(PG) — 인덱스에서 맞는 행의 자리를 다 모은 뒤 표를 한 번에 순서대로 읽는 것. MySQL 에는 없다.
- **`Recheck Cond`**(PG) — 비트맵이 페이지 단위로 뭉개졌을 때를 대비해 조건을 다시 보는 것.
- **커버링 인덱스(covering index)** — 질의가 필요로 하는 열을 다 담은 인덱스. 예: `SELECT grp WHERE grp=7`.
- **`Nested Loop`** — 바깥 행 하나마다 안쪽을 찾는 조인. 비용이 바깥 행 수에 **곱해진다.**
- **`Hash Join`** — 작은 쪽으로 해시 표를 만들고 큰 쪽을 흘려 보내는 조인. 예: 조인 키에 인덱스가 없을 때.
- **`Merge Join`**(PG) — 양쪽을 정렬해 놓고 나란히 전진하며 맞추는 조인. MySQL 에는 없다.
- **`HashAggregate`** — 그룹 키로 해시 표를 만들어 묶는 집계. **순서가 없다.**
- **`GroupAggregate`** — 입력이 그룹 키 순서일 때 훑으며 묶는 집계. 메모리가 거의 안 든다.
- **`Using index for group-by`**(MySQL) — 인덱스에서 값이 바뀌는 자리만 건너뛰며 읽는 최적화. 예: `SELECT DISTINCT grp`.
- **`possible_keys` 대 `key`**(MySQL) — 쓸 수 있었던 인덱스와 실제로 고른 인덱스. 예: `k_grp` / `NULL` = 안 골랐다.

## 더 들어가면

- **`Sort Method`** — PG 의 `EXPLAIN ANALYZE` 는 정렬이 메모리에서 끝났는지(`quicksort`·`top-N heapsort`)
  디스크로 넘쳤는지(`external merge`)까지 알려 준다. `work_mem` 을 올려야 할지 판단하는 자리다. *(이 편에서는 찍지 않았다 — 60번의 영역이다.)*
- **`Incremental Sort`**(PG 13~) — 입력이 정렬 키의 **앞부분만** 정렬돼 있을 때 나머지만 정렬하는 연산자.
  복합 인덱스가 `ORDER BY` 의 일부만 덮을 때 뜬다.
- **병렬 계획** — 이 편은 읽기를 단순하게 하려고 PG 의 병렬을 껐다. 켜면 `Gather`·`Parallel Seq Scan`·
  `Parallel Hash Join` 같은 노드가 한 겹 더 생긴다. **연산자 선택의 원리는 같고, 트리가 두 겹 깊어질 뿐이다.**
- **`Materialize`** — 중첩 루프의 안쪽을 한 번만 만들어 재사용하는 노드. 안쪽이 인덱스 없는 작은 표일 때 뜬다.
- **다중 인덱스 비트맵 `AND`/`OR`**(PG) — 인덱스 둘의 비트맵을 겹쳐 쓰는 `BitmapAnd`·`BitmapOr` 노드가 있다.
  「인덱스를 두 개 걸면 둘 다 쓰나?」의 답이 여기 있다.
