# sql/60-`EXPLAIN ANALYZE` — 추정과 실측의 어긋남 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html) · [PostgreSQL 18 · ANALYZE](https://www.postgresql.org/docs/18/sql-analyze.html) · [MySQL 8.4 · Obtaining Information with EXPLAIN ANALYZE](https://dev.mysql.com/doc/refman/8.4/en/explain.html#explain-analyze) · [MySQL 8.4 · ANALYZE TABLE](https://dev.mysql.com/doc/refman/8.4/en/analyze-table.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 계획·출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 숫자는 없다.\
> **이 편이 만든 객체와 그 뒷정리** — 표 `t60_skew`(19만 행) · `t60_big`(20만 행) · `t60_out`(10행) · `t60_tx` · `t60_s`.
> PG 는 전부 `BEGIN … ROLLBACK` 안에서 만들었고, MySQL 은 DDL 이 암묵 커밋이라 `DROP TABLE IF EXISTS` 로 직접 지웠다.\
> ★ **`emp` 에 `EXPLAIN ANALYZE DELETE` 를 실제로 던졌다** — 4행이 3행이 되는 것까지 확인하고 **`ROLLBACK` 으로 되돌렸다.**
> 그 편의 끝에서 `emp` 가 4행인 것을 다시 확인했다(3-answer 의 「실행 검증」).\
> **측정 조건** — PG 계획은 전부 `max_parallel_workers_per_gather = 0`(병렬 끔). 시간(`actual time`)은 근거로 쓰지 않는다 —
> **근거로 쓰는 칸은 `actual rows`·`loops`·`Rows Removed by Filter` 다.**\
> ★ **실행 계획은 관찰이지 보장이 아니다.** 본문 계획은 **제출 직전에 다시 찍어 대조**했다(3-answer).\
> **선행** — [58 `EXPLAIN` 읽기](../58-explain-plan-tree/). 58 의 `rows=` 가 전부 **추정**이라는 것이 이 편의 출발점이다.

## 한눈에 — 쉽게 말하면

**`EXPLAIN` 은 예보이고, `EXPLAIN ANALYZE` 는 예보와 실황을 나란히 놓은 것이다.**

- 일기예보가 「강수량 10mm」라고 했다. 실제로는 190mm 가 왔다.
- 예보가 틀린 이유는 **하늘이 이상해서가 아니라, 예보가 쓴 자료가 낡아서**다.
- SQL 도 같다. 옵티마이저는 **통계**를 보고 「이 조건이면 10,600행쯤」이라 예보한다.
- 그 통계가 낡으면 **예보가 18배 빗나가고, 그 예보로 고른 계획도 틀린다.**

| 비유 | 실체 |
|---|---|
| 예보 강수량 | `rows=` (추정 행 수) |
| 실제 강수량 | `actual rows=` (실측 행 수) |
| 예보가 쓴 관측 자료 | 통계(`ANALYZE` 가 만든다) |
| 자료가 어제 것이다 | 통계가 낡았다 |
| 관측소를 다시 돌린다 | `ANALYZE` / `ANALYZE TABLE` |
| 잘못된 예보로 우산을 안 챙겼다 | 틀린 추정으로 **연산자를 잘못 골랐다** |

```text
 EXPLAIN                               EXPLAIN ANALYZE
 +----------------------------+        +----------------------------+
 | rows=10600                 |        | rows=10600                 |  <- 추정
 |                            |        | actual rows=190100         |  <- 실측
 | 질의는 돌지 않는다           |        | 질의가 실제로 돈다           |
 +----------------------------+        +----------------------------+
   예보만 본다                            예보와 실황을 나란히 본다
```

**똑같은 구조다** — 「테스트에서는 빨랐는데 운영에서 느리다」의 답이 대개 이 그림이다.\
계획이 나쁜 게 아니라 **계획을 고를 때 본 숫자가 실제와 달랐던 것**이고, 그 격차는 `actual rows` 한 칸에 드러난다.

> **추정(estimate)** — 옵티마이저가 통계를 보고 계산한 행 수. `EXPLAIN` 의 `rows=`.\
> 예: `rows=10600` 은 「이 노드가 10,600행쯤 내놓을 것」이라는 예보다.

> **실측(actual)** — 실제로 돌려 보니 나온 행 수. `EXPLAIN ANALYZE` 의 `actual rows=`.\
> 예: `actual rows=190100.00` 은 정말로 190,100행이 나왔다는 뜻이다.

## 이 주제가 답하려는 질문

1. **추정과 실측이 어긋나면 무엇이 잘못되나** — 숫자만 틀리나, 계획도 틀리나.
2. **통계를 낡게 만들면 어떤 모습이 되나** — 그리고 `ANALYZE` 가 그것을 어디까지 고치나.
3. **`loops`·`Buffers` 는 무엇을 말하나** — 그리고 `EXPLAIN ANALYZE` 가 질의를 **실제로 돌린다**는 것의 대가는.

## 예시 데이터 — 이 묶음이 공유하는 것

기존 `emp`·`dept` 는 **읽기 실험과 `ROLLBACK` 되는 변경 실험**에만 쓴다.

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

통계를 낡게 만드는 실험은 **일부러 치우친 표**를 만들어 한다.

```sql
-- 1단계: 값이 고르게 퍼진 1,000행을 만들고 통계를 잡는다
CREATE TABLE t60_skew AS SELECT g AS id, (g % 10) AS grp FROM generate_series(1,1000) g;   -- grp 0~9, 각 100행
CREATE INDEX t60_skew_grp ON t60_skew (grp);
ANALYZE t60_skew;                       -- 이 시점의 통계: "grp 마다 100행"

-- 2단계: grp=7 만 190,000행을 몰아넣는다. ANALYZE 는 하지 않는다
INSERT INTO t60_skew SELECT 1000+g, 7 FROM generate_series(1,190000) g;
```

```text
 1단계 (통계를 잡은 시점)               2단계 (통계를 안 잡은 지금)
 grp | 행 수                            grp | 행 수
 ----+------                            ----+---------
   0 |  100                               0 |     100
   1 |  100                               1 |     100
  …  |  100                              …  |     100
   7 |  100   <- 통계가 기억하는 값         7 | 190,100   <- 실제
  …  |  100                              …  |     100
 합계 1,000                             합계 191,000
```

**통계는 1단계를 기억하고, 데이터는 2단계다.** 이 어긋남이 이 편의 실험대다.

## 동작 방식

### 1. ★ `EXPLAIN ANALYZE` 는 예보와 실황을 한 줄에 놓는다

**언제 쓰나** — 「계획은 멀쩡해 보이는데 느리다」일 때. **첫 동작은 두 숫자를 나란히 보는 것이다.**

```text
Bitmap Heap Scan on t60_skew  (cost=146.44..1126.94 rows=10600 width=0) (actual rows=190100.00 loops=1)
                                                    ^^^^^^^^^^           ^^^^^^^^^^^^^^^^^^  ^^^^^^^
                                                    추정 (예보)           실측 (실황)          몇 번 돌았나
```

**기존 `emp` 하나만 읽어도 이미 어긋남이 보인다.** 이 표는 한 번도 `ANALYZE` 된 적이 없다.

```text
### SQL: EXPLAIN ANALYZE SELECT * FROM emp WHERE salary > 100;
--- PG 18.6 ---
 Seq Scan on emp  (cost=0.00..24.12 rows=377 width=44) (actual time=0.012..0.014 rows=3.00 loops=1)
   Filter: (salary > 100)
   Rows Removed by Filter: 1
   Buffers: shared hit=1
 Planning:
   Buffers: shared hit=59
 Planning Time: 0.330 ms
 Execution Time: 0.064 ms
```

그림 해설 — **`rows=377` 대 `actual rows=3.00`.** `emp` 는 4행짜리 표다.\
`reltuples = -1`(=아직 센 적 없음)이라 옵티마이저가 **기본 가정**으로 예보했고, 125배 빗나갔다.\
`Rows Removed by Filter: 1` 은 `salary IS NULL` 인 `cho` 를 버린 것이다([04번](../04-null-three-valued-logic/)).

비용 — 4행짜리 표에서는 어떤 계획을 골라도 같으므로 **이 어긋남은 무해하다.**\
**무해한 어긋남과 해로운 어긋남을 가르는 것이 2절의 주제다.**

---

### 2. ★ 통계를 낡게 만들면 — 숫자만 틀리는 게 아니라 연산자가 틀린다

**언제 쓰나** — 대량 적재·대량 삭제 직후. **이 절이 이 주제의 과녁이다.**

예시 데이터 절의 두 단계를 `EXPLAIN ANALYZE` 로 세 장면에 나눠 찍었다.

```text
### 장면 1 — 1,000행 · ANALYZE 직후
--- PG 18.6 ---
 Aggregate  (cost=14.43..14.44 rows=1 width=8) (actual rows=1.00 loops=1)
   ->  Bitmap Heap Scan on t60_skew  (cost=4.93..14.18 rows=100 width=0) (actual rows=100.00 loops=1)
         Recheck Cond: (grp = 7)
         Heap Blocks: exact=5
         ->  Bitmap Index Scan on t60_skew_grp  (cost=0.00..4.90 rows=100 width=0) (actual rows=100.00 loops=1)
               Index Cond: (grp = 7)
               Index Searches: 1
```

```text
### 장면 2 — grp=7 만 190,000행 추가 · ANALYZE 안 함
--- PG 18.6 ---
 Aggregate  (cost=1153.44..1153.45 rows=1 width=8) (actual rows=1.00 loops=1)
   ->  Bitmap Heap Scan on t60_skew  (cost=146.44..1126.94 rows=10600 width=0) (actual rows=190100.00 loops=1)
         Recheck Cond: (grp = 7)
         Heap Blocks: exact=846
         ->  Bitmap Index Scan on t60_skew_grp  (cost=0.00..143.79 rows=10600 width=0) (actual rows=190100.00 loops=1)
               Index Cond: (grp = 7)
               Index Searches: 1
```

```text
### 장면 3 — ANALYZE 한 뒤
--- PG 18.6 ---
 Aggregate  (cost=3710.47..3710.48 rows=1 width=8) (actual rows=1.00 loops=1)
   ->  Seq Scan on t60_skew  (cost=0.00..3235.50 rows=189988 width=0) (actual rows=190100.00 loops=1)
         Filter: (grp = 7)
         Rows Removed by Filter: 900
```

```text
 장면          추정 rows=      실측 actual rows=     뽑힌 연산자
 1 (통계 최신)      100            100              Bitmap Heap Scan
 2 (통계 낡음)   10,600        190,100              Bitmap Heap Scan   <- 그대로다
 3 (ANALYZE 뒤) 189,988       190,100              Seq Scan           <- 바뀌었다
```

★ **장면 2 가 이 절의 전부다.** 추정이 **18배** 빗나갔고, 그 결과 **190,100행을 비트맵으로 긁는 계획**이 뽑혔다.\
[59번](../59-scan-join-sort-operators/)에서 봤듯 **95% 를 읽는 질의에는 `Seq Scan` 이 맞다.** 장면 3 이 그것을 보여 준다.

```text
 통계가 낡았을 때 일어나는 일
 +---------------------------------------------------+
 | 1. rows= 가 틀린다             (10,600 대 190,100) |
 | 2. 그 rows= 로 비용을 계산한다  (1126.94)           |
 | 3. 그 비용으로 연산자를 고른다   (Bitmap)            |
 | 4. 고른 연산자가 이 데이터에 안 맞는다               |
 +---------------------------------------------------+
   -> 틀리는 것은 숫자가 아니라 "선택"이다
```

그림 해설 — **추정은 계획의 입력**이다. 입력이 틀리면 출력(계획)이 틀린다.\
비용 — `ANALYZE` 는 표를 다시 표본 조사한다. 큰 표에서는 I/O 가 들지만, **틀린 계획을 계속 도는 값보다 싸다.**

**장면 3 의 `Rows Removed by Filter: 900`** 이 `Seq Scan` 이 실제로 한 일을 말해 준다 —\
191,000행을 읽어 900행을 버렸다. **읽은 것의 99.5% 를 남겼으니 인덱스가 필요 없는 질의다.**

> **`ANALYZE`**(PG) / **`ANALYZE TABLE`**(MySQL) — 표를 표본 조사해 통계를 다시 만드는 명령.\
> 예: 대량 적재 직후에 돌리지 않으면 옵티마이저가 적재 전 분포로 계획을 짠다.

---

### 3. ★ MySQL 에서는 `ANALYZE TABLE` 이 다 고치지 못했다

**언제 쓰나** — 「`ANALYZE TABLE` 을 돌렸는데 왜 아직 느리지」일 때.

MySQL 에서 같은 세 장면을 찍었다.

```text
### 장면 1 — 1,000행 · ANALYZE TABLE 직후
--- MySQL 8.4.10 ---
-> Aggregate: count(0)  (cost=20.3 rows=1) (actual time=0.0337..0.0337 rows=1 loops=1)
    -> Covering index lookup on t60_skew using k_grp (grp=7)  (cost=10.3 rows=100) (actual time=0.0181..0.0269 rows=100 loops=1)

### 장면 2 — 190,000행 추가 · ANALYZE TABLE 안 함
--- MySQL 8.4.10 ---
-> Aggregate: count(0)  (cost=19126 rows=1) (actual time=26.8..26.8 rows=1 loops=1)
    -> Covering index lookup on t60_skew using k_grp (grp=7)  (cost=9576 rows=95500) (actual time=0.486..19.6 rows=190100 loops=1)

### 장면 3 — ANALYZE TABLE 한 뒤
--- MySQL 8.4.10 ---
-> Aggregate: count(0)  (cost=19126 rows=1) (actual time=28.9..28.9 rows=1 loops=1)
    -> Covering index lookup on t60_skew using k_grp (grp=7)  (cost=9576 rows=95496) (actual time=0.543..21.3 rows=190100 loops=1)
```

```text
 장면          MySQL 추정 rows=   실측 actual rows=      PG 는 어땠나
 1 (통계 최신)        100             100               100 / 100
 2 (통계 낡음)     95,500         190,100            10,600 / 190,100
 3 (ANALYZE 뒤)   95,496         190,100           189,988 / 190,100
```

★ **두 엔진이 정반대로 틀렸다.**

```text
 PostgreSQL                             MySQL 8.4.10
 +-----------------------------+       +-----------------------------+
 | 장면 2: 10,600 (18배 과소)    |       | 장면 2: 95,500 (2배 과소)    |
 | 장면 3: 189,988 (거의 맞다)   |       | 장면 3: 95,496 (여전히 2배)  |
 | -> ANALYZE 가 고쳤다          |       | -> ANALYZE 가 못 고쳤다      |
 +-----------------------------+       +-----------------------------+
```

**표의 행 수는 `ANALYZE TABLE` 이 고쳤다.**

```text
### SQL: SELECT table_rows FROM information_schema.tables WHERE table_schema='study' AND table_name='t60_skew';
--- MySQL 8.4.10 ---
장면 1: 1000        장면 2: 1000  <- 낡았다        장면 3: 190992  <- 고쳐졌다
```

**그런데 `grp = 7` 의 행 수 추정은 95,496 으로 남았다.** 실측은 190,100 이다.\
인덱스 카디널리티도 확인해 봤다.

```text
### SQL: SHOW INDEX FROM t60_skew;
--- MySQL 8.4.10 ---
| Key_name | Column_name | Cardinality |
| PRIMARY  | id          |      190992 |
| k_grp    | grp         |           9 |
```

> 표 테두리와 `Table`·`Non_unique`·`Seq_in_index`·`Collation`·`Sub_part`·`Packed`·`Null`·`Index_type`·
> `Comment`·`Index_comment`·`Visible`·`Expression` 칸을 지웠다. 남긴 칸의 값은 원본 그대로다.

그림 해설 — **서로 다른 값의 개수(9)는 거의 맞다**(실제 10). **그런데 한 값의 행 수 추정이 절반이다.**\
★ **왜 절반인지는 이 실측만으로 단정하지 않는다.** 확인된 것은 「**`ANALYZE TABLE` 을 돌려도 2배 어긋남이 남았다**」는 사실이다.\
표본 페이지 수를 `STATS_SAMPLE_PAGES=200` 으로 열 배 늘려 다시 돌려도 **95,256 으로 거의 같았다.**

대가 — 그래서 MySQL 쪽에서는 **「`ANALYZE TABLE` 을 돌렸으니 이제 맞겠지」가 성립하지 않는다.**\
치우친 분포에서는 `EXPLAIN ANALYZE` 로 **실측을 직접 보는** 수밖에 없다.

---

### 4. `loops` — 그 노드가 몇 번 돌았나

**언제 쓰나** — 중첩 루프가 낀 계획에서. **`actual rows` 를 잘못 읽는 가장 흔한 자리다.**

```text
### SQL: EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS) SELECT o.id, b.grp FROM t60_out o JOIN t60_big b ON b.id = o.ref;
--- PG 18.6 (중첩 루프 강제 · 병렬 끔) ---
 Nested Loop  (cost=0.42..85.48 rows=10 width=8) (actual rows=10.00 loops=1)
   Buffers: shared hit=38 read=3
   ->  Seq Scan on t60_out o  (cost=0.00..1.10 rows=10 width=8) (actual rows=10.00 loops=1)
         Buffers: shared hit=1
   ->  Index Scan using t60_big_pkey on t60_big b  (cost=0.42..8.44 rows=1 width=8) (actual rows=1.00 loops=10)
         Index Cond: (id = o.ref)
         Index Searches: 10
         Buffers: shared hit=37 read=3
```

```text
 안쪽 노드의 표시                      실제로 일어난 일
 actual rows=1.00  loops=10           안쪽 Index Scan 이 10번 돌았고
        ^             ^               매번 1행씩 내놓았다
   한 번 돌 때 평균    몇 번 돌았나      -> 총 10행
```

★ **PG 의 `actual rows` 는 「한 번 돌 때의 평균」이다.** 총 행 수는 `actual rows × loops` 다.\
`rows=1.00` 만 보고 「1행밖에 안 읽네」라고 읽으면 틀린다. **`loops=10` 을 같이 본다.**

`Index Searches: 10` 이 같은 이야기를 다른 칸으로 한다 — 인덱스를 10번 뒤졌다.

MySQL 도 같은 표기다.

```text
### SQL: EXPLAIN ANALYZE SELECT s.id, b.pad FROM t59_small s JOIN t59_big b ON b.id = s.ref;
--- MySQL 8.4.10 ---
-> Nested loop inner join  (cost=4.75 rows=10) (actual time=0.0288..0.0511 rows=10 loops=1)
    -> Filter: (s.ref is not null)  (cost=1.25 rows=10) (actual time=0.0154..0.0187 rows=10 loops=1)
        -> Table scan on s  (cost=1.25 rows=10) (actual time=0.0145..0.0172 rows=10 loops=1)
    -> Single-row index lookup on b using PRIMARY (id=s.ref)  (cost=0.26 rows=1) (actual time=0.00296..0.00299 rows=1 loops=10)
```

비용 — **`loops` 가 큰 노드를 먼저 본다.** 한 번이 싸도 만 번 돌면 비싸다([59번](../59-scan-join-sort-operators/)의 중첩 루프).

---

### 5. `Buffers` — 몇 페이지를 어디서 읽었나

**언제 쓰나** — 「같은 질의가 처음엔 느리고 두 번째는 빠르다」일 때.

```text
Buffers: shared hit=37 read=3
                ^^^^^^^   ^^^^^^
                캐시에서   디스크에서 (또는 OS 캐시에서)
```

> **`shared hit`** — 공유 버퍼 캐시에 이미 있어서 그냥 쓴 페이지 수.\
> 예: `hit=37` 은 37 페이지를 읽는 데 디스크를 안 건드렸다는 뜻이다.

> **`shared read`** — 캐시에 없어서 새로 읽어 온 페이지 수.\
> 예: `read=3` 은 3 페이지를 새로 가져왔다는 뜻이다. 두 번째 실행에서는 대개 `hit` 로 바뀐다.

```text
### SQL: EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS) SELECT count(*) FROM t60_big WHERE grp = 7;
--- PG 18.6 ---
 Aggregate  (cost=3396.50..3396.51 rows=1 width=8) (actual rows=1.00 loops=1)
   Buffers: shared hit=896
   ->  Seq Scan on t60_big  (cost=0.00..3396.00 rows=199 width=0) (actual rows=200.00 loops=1)
         Filter: (grp = 7)
         Rows Removed by Filter: 199800
         Buffers: shared hit=896
```

그림 해설 — **896 페이지를 읽어 200행을 남기고 199,800행을 버렸다.**\
`Rows Removed by Filter` 와 `Buffers` 를 같이 보면 「**얼마나 헛일을 했나**」가 나온다 — 읽은 것의 0.1% 만 썼다.\
`hit=896`·`read=0` 이므로 **디스크는 안 건드렸다** — 그래서 빠르다. 캐시가 비어 있었다면 같은 계획이 훨씬 느렸을 것이다.

비용 — **시간은 캐시 상태에 달렸지만 페이지 수는 안 그렇다.** 그래서 계획을 비교할 때는 `Buffers` 가 시간보다 낫다.

---

### 6. ★ `EXPLAIN ANALYZE` 는 질의를 **실제로 돌린다** — PG 에서는 `DELETE` 도 돈다

**언제 쓰나** — 변경문의 계획이 궁금할 때. **여기가 이 편에서 가장 위험한 자리다.**

```text
EXPLAIN SELECT …            계획만 만든다
EXPLAIN ANALYZE SELECT …    돌린다 (결과를 버릴 뿐)
EXPLAIN ANALYZE DELETE …    ★ 진짜로 지운다
```

`emp` 에 직접 던져 봤다 — **트랜잭션 안에서**, 그리고 `ROLLBACK` 으로 되돌렸다.

```text
### SQL: BEGIN;
###      EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS OFF) DELETE FROM emp WHERE id = 1;
--- PG 18.6 ---
 Delete on emp  (cost=0.15..8.17 rows=0 width=0) (actual rows=0.00 loops=1)
   ->  Index Scan using emp_pkey on emp  (cost=0.15..8.17 rows=1 width=6) (actual rows=1.00 loops=1)
         Index Cond: (id = 1)
         Index Searches: 1

### SQL: SELECT count(*) FROM emp;
--- PG 18.6 (같은 트랜잭션 안) ---
 count
-------
     3        <- 4행이던 emp 가 3행이 됐다

### SQL: ROLLBACK;  SELECT count(*) FROM emp;
--- PG 18.6 ---
 count
-------
     4        <- 되돌아왔다
```

★ **「계획만 보려고」 던진 문장이 행을 지웠다.** `Delete on emp` 노드의 `actual rows=0.00` 은\
「돌려준 행이 0개」라는 뜻이지 「아무것도 안 했다」가 아니다 — 아래 `Index Scan` 의 `actual rows=1.00` 이 지운 행이다.

```text
 안전한 절차                            위험한 절차
 +----------------------------+        +----------------------------+
 | BEGIN;                     |        | EXPLAIN ANALYZE DELETE … ; |
 | EXPLAIN ANALYZE DELETE … ; |        |   -> 지워졌다               |
 | -- 계획을 본다              |        |   -> 자동 커밋이면 끝이다    |
 | ROLLBACK;                  |        |                            |
 +----------------------------+        +----------------------------+
```

**반드시 `BEGIN … ROLLBACK` 으로 감싼다.** `INSERT` 로도 확인했다.

```text
### SQL: BEGIN; CREATE TABLE t60_tx (id int);
###      EXPLAIN (ANALYZE, …) INSERT INTO t60_tx SELECT g FROM generate_series(1,5) g;
--- PG 18.6 ---
 Insert on t60_tx  (cost=0.00..0.05 rows=0 width=0) (actual rows=0.00 loops=1)
   ->  Function Scan on generate_series g  (cost=0.00..0.05 rows=5 width=4) (actual rows=5.00 loops=1)

### SQL: SELECT count(*) FROM t60_tx;
 count
-------
     5        <- 들어갔다

### SQL: EXPLAIN INSERT INTO t60_tx SELECT g FROM generate_series(101,105) g;   -- ANALYZE 없이
 Insert on t60_tx  (cost=0.00..0.05 rows=0 width=0)
   ->  Function Scan on generate_series g  (cost=0.00..0.05 rows=5 width=4)

### SQL: SELECT count(*) FROM t60_tx;
 count
-------
     5        <- 안 들어갔다. EXPLAIN 만으로는 안 돈다
```

비용 — `EXPLAIN` 과 `EXPLAIN ANALYZE` 사이에는 **되돌릴 수 없는 차이**가 있다. 낱말 하나다.

---

### 7. ★ MySQL 의 `EXPLAIN ANALYZE` 는 변경문을 돌리지 않는다 — 던져서 확인한다

**언제 쓰나** — PG 습관을 MySQL 로 가져갈 때. **여기서 두 엔진이 갈린다.**

```text
### SQL: EXPLAIN ANALYZE UPDATE t59_small SET ref = 1 WHERE id = 1;
--- MySQL 8.4.10 ---
+-------------------------------------------+
| EXPLAIN                                   |
+-------------------------------------------+
| -> <not executable by iterator executor>
 |
+-------------------------------------------+

### SQL: EXPLAIN ANALYZE DELETE FROM t59_small WHERE id = 1;
--- MySQL 8.4.10 ---
| -> <not executable by iterator executor>
```

```text
### SQL: EXPLAIN ANALYZE INSERT INTO t59_small VALUES (98, 98);
--- MySQL 8.4.10 ---
+----------------------------------------------------------------+
| EXPLAIN                                                        |
+----------------------------------------------------------------+
| -> Insert into t59_small
    -> Rows fetched before execution
 |
+----------------------------------------------------------------+

### SQL: SELECT count(*) AS n98 FROM t59_small WHERE id = 98;
--- MySQL 8.4.10 ---
+-----+
| n98 |
+-----+
|   0 |        <- 안 들어갔다
+-----+
```

그림 해설 — **`<not executable by iterator executor>` 는 에러가 아니다.** 계획 자리에 찍힌 **문구**다.\
`UPDATE`·`DELETE` 는 이 문구만 주고, `INSERT` 는 계획을 주되 **`(actual …)` 칸이 없다** — 실행하지 않았다는 뜻이고,\
**행이 실제로 안 들어간 것으로 확인했다**(두 번 던져 두 번 다 0행).

```text
 PostgreSQL 18.6                        MySQL 8.4.10
 +-----------------------------+       +-----------------------------+
 | EXPLAIN ANALYZE DELETE      |       | EXPLAIN ANALYZE DELETE      |
 |   -> 진짜로 지운다            |       |   -> <not executable …>     |
 |   -> 트랜잭션으로 감싸라      |       |   -> 아무 일도 안 일어난다    |
 +-----------------------------+       +-----------------------------+
   위험하지만 실측이 나온다               안전하지만 실측이 없다
```

★ **안전한 쪽이 좋기만 한 것은 아니다** — MySQL 에서는 **변경문의 실측을 볼 방법이 이 도구로는 없다.**\
`EXPLAIN` 으로 모양만 보고, 실제 영향은 `SELECT` 로 같은 조건을 세어 가늠한다.

---

### 8. 정렬이 메모리에서 끝났나 — `Sort Method`

**언제 쓰나** — 정렬이 낀 질의가 느릴 때. **`EXPLAIN` 만으로는 안 보인다.**

```text
### SQL: SET work_mem = '64kB';  EXPLAIN (ANALYZE, …) SELECT id FROM t60_s ORDER BY pad, id;
--- PG 18.6 ---
 Sort  (cost=37749.14..38249.14 rows=200000 width=35) (actual rows=200000.00 loops=1)
   Sort Key: pad, id
   Sort Method: external merge  Disk: 8880kB
   ->  Seq Scan on t60_s  (cost=0.00..3728.00 rows=200000 width=35) (actual rows=200000.00 loops=1)

### SQL: SET work_mem = '64MB';  (같은 질의)
--- PG 18.6 ---
 Sort  (cost=21337.64..21837.64 rows=200000 width=35) (actual rows=200000.00 loops=1)
   Sort Key: pad, id
   Sort Method: quicksort  Memory: 17082kB
   ->  Seq Scan on t60_s  (cost=0.00..3728.00 rows=200000 width=35) (actual rows=200000.00 loops=1)
```

```text
 work_mem 이 작을 때                    work_mem 이 넉넉할 때
 +-----------------------------+       +-----------------------------+
 | Sort Method: external merge |       | Sort Method: quicksort      |
 | Disk: 8880kB                |       | Memory: 17082kB             |
 | -> 디스크에 쏟아 가며 정렬    |       | -> 메모리 안에서 끝          |
 +-----------------------------+       +-----------------------------+
   같은 행 수, 같은 결과. 다른 것은 어디서 정렬했나뿐이다.
```

그림 해설 — **`Sort Method` 는 `EXPLAIN ANALYZE` 에만 나온다.** 계획만으로는 디스크로 넘쳤는지 알 수 없다.\
`external merge` 가 보이면 `work_mem` 을 올릴지 판단하는 자리다.\
비용 — 추정 비용도 37749 대 21337 로 달랐다. **옵티마이저는 메모리 설정까지 계산에 넣는다.**

**해시 조인·해시 집계에도 같은 성격의 칸이 있다** — `Batches:` 가 2 이상이면 메모리에 안 들어가 나눠 처리한 것이다.

## 문법 — 어느 절에서 무엇이 보이나

SQL 에서 이 절의 본체는 형태가 아니라 「**어느 옵션이 어느 칸을 켜나**」다.

```sql
-- PostgreSQL
EXPLAIN (ANALYZE) SELECT …;                          -- actual rows / loops / 시간
EXPLAIN (ANALYZE, BUFFERS) SELECT …;                 -- shared hit/read/written   (18 에서는 기본 켜짐)
EXPLAIN (ANALYZE, TIMING OFF) SELECT …;              -- 시간 측정을 끈다 (오버헤드가 준다)
EXPLAIN (ANALYZE, SUMMARY OFF) SELECT …;             -- Planning/Execution Time 줄을 끈다
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF, BUFFERS OFF) SELECT …;  -- 재현하기 좋은 최소 형태
ANALYZE;                       -- 데이터베이스 전체
ANALYZE t60_skew;              -- 한 표
ANALYZE t60_skew (grp);        -- 한 열

-- MySQL
EXPLAIN ANALYZE SELECT …;                            -- 언제나 트리 형식
ANALYZE TABLE t60_skew;
ALTER TABLE t60_skew STATS_SAMPLE_PAGES=200;         -- 표본 페이지 수 (표 단위)
SHOW INDEX FROM t60_skew;                            -- 인덱스 카디널리티
SELECT table_rows FROM information_schema.tables WHERE table_name='…';
```

- **PG 18 은 `BUFFERS` 가 `ANALYZE` 와 함께 기본으로 켜진다.** 끄려면 `BUFFERS OFF` 를 명시한다.
- **기록에 남길 계획은 `TIMING OFF, SUMMARY OFF` 를 붙인다.** 시간 칸이 판마다 달라 대조가 안 되기 때문이다 —
  이 편의 계획 대부분이 그 형태다.
- **`ANALYZE` 는 트랜잭션 안에서도 돈다.** 이 편의 PG 실험이 전부 `BEGIN … ROLLBACK` 안인 이유가 그것이다.
- MySQL 의 `ANALYZE TABLE` 은 결과를 **표 형태로 돌려준다**(`Op=analyze`·`Msg_type=status`·`Msg_text=OK`).
  실패하면 그 칸에 사유가 찍히므로 **출력을 보고 넘어간다.**
- **`EXPLAIN ANALYZE` 는 변경문에서 PG 와 MySQL 이 갈린다**(6·7절). 낱말은 같은데 동작이 다르다.

## 어디서 틀리나

| 틀리는 자리 | 무슨 일이 일어나나 | 근거 |
|---|---|---|
| `rows=` 를 사실로 읽는다 | **추정이다.** `emp` 는 4행인데 `rows=377` 이었다 | 1절 |
| 추정이 틀려도 결과만 맞으면 된다고 본다 | **연산자 선택이 틀린다** — 장면 2 가 그것이다 | 2절 |
| 대량 적재 뒤 `ANALYZE` 를 안 돌린다 | 적재 전 분포로 계획을 짠다 | 2절 |
| `ANALYZE TABLE` 을 돌렸으니 맞겠지 | **MySQL 은 2배 어긋남이 남았다** | 3절 |
| `actual rows=1.00` 을 「1행 읽었다」로 읽는다 | **한 번 돌 때의 평균**이다. `loops` 를 곱한다 | 4절 |
| 시간(`actual time`)으로 계획을 비교한다 | 캐시 상태에 달렸다. **`Buffers`·`actual rows` 를 본다** | 5절 |
| ★ `EXPLAIN ANALYZE DELETE` 를 그냥 던진다 | **PG 에서는 진짜로 지워진다** | 6절 |
| MySQL 에서도 지워질까 봐 안 던진다 | **MySQL 은 안 돈다** — `<not executable by iterator executor>` | 7절 |
| 정렬이 메모리에서 끝났는지 `EXPLAIN` 으로 본다 | **`Sort Method` 는 `ANALYZE` 에만 나온다** | 8절 |
| `Delete on emp (actual rows=0.00)` 을 「안 지웠다」로 읽는다 | **돌려준 행이 0개**라는 뜻이다. 아래 노드를 본다 | 6절 |

★ **가장 조용한 것은 2절이다.** 질의는 정상으로 돌고 결과도 맞다. **느릴 뿐이다.**\
★ **가장 위험한 것은 6절이다.** 되돌릴 수 없다.

## 구현 세부사항 대 언어 보장

| 항목 | 성격 | 근거 |
|---|---|---|
| `EXPLAIN ANALYZE` 가 질의를 돌리는 것 | **양쪽 공통** — `SELECT` 에 대해서는 | 1·3절 |
| 변경문까지 도는지 | **엔진 차이** — PG 는 돌고 MySQL 은 안 돈다 | 6·7절 |
| 통계가 낡으면 추정이 틀리는 것 | **양쪽 공통 원리** | 2·3절 |
| `ANALYZE` 가 추정을 고치는 정도 | **엔진 차이** — PG 는 고쳤고 MySQL 은 2배가 남았다 | 2·3절 |
| 추정이 빗나가는 방향과 배수 | **이 데이터·이 통계의 값** | 2·3절 |
| `actual rows` 가 평균이고 `loops` 를 곱해야 하는 것 | **양쪽 공통 표기** | 4절 |
| PG 18 이 `actual rows` 를 소수 둘째 자리까지 찍는 것 | **버전 표기** — 이전 버전과 다르다 | 전 절 |
| `Sort Method`·`Buffers` | **PG 의 계측 항목** — MySQL 출력에는 없다 | 5·8절 |

★ **이 편의 모든 계획은 「관찰」이다.** [19번](../19-semi-anti-join/)과 [59번](../59-scan-join-sort-operators/)에\
같은 조건에서 계획이 갈린 실측이 있다. 제출 직전 재확인 결과는 3-answer 의 「실행 검증」에 있다.

## 언제 쓰고 언제 안 쓰나

```text
 EXPLAIN ANALYZE 를 쓴다                EXPLAIN 만 쓴다
 +----------------------------+        +----------------------------+
 | 느린 이유를 짚어야 한다      |        | 변경문의 계획이 궁금하다     |
 | 추정이 맞았는지 봐야 한다    |        |   (PG 에서는 진짜로 돈다)    |
 | 행이 어디서 불어나는지       |        | 아주 오래 걸리는 질의        |
 | 정렬/해시가 디스크로 넘쳤나  |        |   (끝날 때까지 돌아간다)     |
 +----------------------------+        +----------------------------+
```

- **변경문에 `EXPLAIN ANALYZE` 를 쓸 거면 `BEGIN … ROLLBACK` 이 먼저다.** 예외 없다.
- **운영 데이터에 던지기 전에 같은 문을 `EXPLAIN` 으로 본다.** 영향 범위를 먼저 가늠한다.
- **기록에 남길 때는 `TIMING OFF, SUMMARY OFF`** 를 붙이고 **엔진 버전과 찍은 시각**을 같이 적는다.
- 「느리다」의 진단 순서는 **① 추정 대 실측이 크게 어긋나나(2·3절) → ② `loops` 가 큰 노드가 있나(4절) →
  ③ 읽은 것의 대부분을 버리나(`Rows Removed by Filter`, 5절) → ④ 디스크로 넘쳤나(8절)** 다.

## 핵심 문장

1. **`rows=` 는 예보, `actual rows=` 는 실황이다** — `EXPLAIN ANALYZE` 는 둘을 한 줄에 놓는다.
2. **추정이 틀리면 숫자가 아니라 「선택」이 틀린다** — 통계가 낡으면 연산자까지 잘못 고른다.
3. **통계를 낡게 만드는 법은 간단하다** — 대량으로 넣고 `ANALYZE` 를 안 돌리면 된다. 18배 어긋남이 났다.
4. **MySQL 은 `ANALYZE TABLE` 로도 2배 어긋남이 남았다** — 「돌렸으니 맞겠지」가 성립하지 않는다.
5. **`actual rows` 는 한 번 돌 때의 평균이다** — `loops` 를 곱해야 총 행 수다.
6. **PG 의 `EXPLAIN ANALYZE` 는 `DELETE` 도 진짜로 돈다** — 트랜잭션으로 감싼다. MySQL 은 안 돈다.
7. **근거로 쓸 칸은 시간이 아니라 `actual rows`·`loops`·`Buffers`·`Rows Removed by Filter` 다.**

## 관련 자료

- [58 `EXPLAIN` 읽기](../58-explain-plan-tree/) — **그쪽은 계획의 구조와 `cost`·`rows`·`width` 칸의 뜻까지, 여기는 그 `rows=` 가 실제와 얼마나 어긋나나부터다.** 「계획을 어떻게 읽나」는 그쪽, 「그 계획이 옳았나」는 여기.
- [59 스캔·조인·정렬 연산자](../59-scan-join-sort-operators/) — 2절에서 연산자가 바뀐 이유(`Bitmap` 대 `Seq Scan`)가 그쪽 주제다. 같은 데이터로 계획이 흔들린 실측도 거기 있다.
- [09 LIMIT·OFFSET](../09-limit-offset-keyset-pagination/) — `actual rows` 만을 근거로 비용을 잰 전례. 시간이 아니라 행 수를 본다.
- [19 세미·안티 조인](../19-semi-anti-join/) — 같은 서버에서 계획이 두 번 달랐던 실측.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — 1절의 `Rows Removed by Filter: 1` 이 `salary IS NULL` 인 행이다.
- [48 뷰와 구체화 뷰](../48-views-and-materialized-views/) — 구체화 뷰를 쓰기로 했다면 「낡음」을 이 편의 통계 낡음과 같은 눈으로 관리한다.

## 용어 풀이

- **추정(estimate)** — 옵티마이저가 통계로 계산한 행 수. `EXPLAIN` 의 `rows=`. 예: `rows=10600`.
- **실측(actual)** — 실제로 나온 행 수. `EXPLAIN ANALYZE` 의 `actual rows=`. 예: `actual rows=190100.00`.
- **통계(statistics)** — 표·열의 요약값(행 수·서로 다른 값 수·값 분포). `ANALYZE` 가 만든다.
- **`ANALYZE`**(PG) / **`ANALYZE TABLE`**(MySQL) — 통계를 다시 만드는 명령. 예: 대량 적재 직후에 돌린다.
- **낡은 통계(stale statistics)** — 데이터는 바뀌었는데 통계가 옛 상태인 것. 예: 19만 행을 넣고 `ANALYZE` 를 안 돌림.
- **`loops`** — 그 노드가 몇 번 돌았나. 예: 중첩 루프의 안쪽이 `loops=10`.
- **`Rows Removed by Filter`**(PG) — 읽었다가 조건에서 버린 행 수. 예: `199800` 이면 헛일을 많이 했다는 뜻.
- **`Buffers: shared hit`**(PG) — 캐시에 있어 그냥 쓴 페이지 수. 예: `hit=896` 이면 디스크를 안 건드렸다.
- **`Buffers: shared read`**(PG) — 새로 읽어 온 페이지 수. 예: `read=3`.
- **`Sort Method`**(PG) — 정렬을 어떻게 했나. 예: `quicksort  Memory: 17082kB` / `external merge  Disk: 8880kB`.
- **`work_mem`**(PG) — 한 정렬·해시 연산이 쓸 수 있는 메모리 상한. 예: 작으면 디스크로 넘친다.
- **`<not executable by iterator executor>`**(MySQL) — 변경문에 `EXPLAIN ANALYZE` 를 썼을 때 계획 자리에 찍히는 문구. 에러가 아니다.
- **`STATS_SAMPLE_PAGES`**(MySQL) — 통계를 만들 때 표본으로 볼 페이지 수. 표 단위로 지정한다.
- **카디널리티(cardinality)** — 인덱스가 가진 서로 다른 값의 개수(추정). 예: `k_grp` 가 `9`.

## 더 들어가면

- **자동 통계 갱신** — PG 의 autovacuum 은 일정 비율이 바뀌면 스스로 `ANALYZE` 를 돌린다. 이 편의 실험은
  **트랜잭션 안**에서 했기 때문에 그 개입이 없었고, 그래서 낡은 상태를 안정적으로 재현할 수 있었다.
  운영에서는 「언젠가 자동으로 갱신된다」에 기대지 말고 **대량 작업 직후 직접 돌리는** 편이 낫다.
- **확장 통계(`CREATE STATISTICS`)** — PG 는 **두 열의 상관**을 따로 통계로 잡을 수 있다.
  `WHERE city='서울' AND zip='06236'` 처럼 사실상 같은 뜻인 두 조건을 독립으로 가정해 추정이 크게 어긋나는 자리를 고친다. *(이 편에서는 돌려 보지 않았다.)*
- **`pg_stat_statements`** — 어느 질의가 전체 시간을 먹는지 **누적으로** 보는 확장. `EXPLAIN ANALYZE` 가
  「이 질의 하나」를 보는 도구라면 이쪽은 「어느 질의를 볼지」를 고르는 도구다.
- **`EXPLAIN (ANALYZE, WAL)`** — 변경문이 만든 WAL 양을 보여 준다. 6절처럼 변경문을 계측할 때 딸려 오는 칸이다.
- **MySQL 의 옵티마이저 트레이스** — `SET optimizer_trace='enabled=on'` 뒤 질의를 돌리면
  「왜 그 계획을 골랐나」의 내부 계산을 JSON 으로 볼 수 있다. `EXPLAIN` 이 결론이라면 이쪽은 과정이다. *(이 편에서는 돌려 보지 않았다.)*
