# sql/60-`EXPLAIN ANALYZE` — 추정과 실측의 어긋남 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 계획·출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 숫자는 없다.\
> **측정 조건** — PG 계획은 전부 `max_parallel_workers_per_gather = 0`(병렬 끔), 대부분 `TIMING OFF, SUMMARY OFF`.\
> **시간은 근거로 쓰지 않는다** — 근거로 쓰는 칸은 `actual rows`·`loops`·`Rows Removed by Filter`·`Buffers` 다.\
> ★ **12번은 기존 `emp` 에 `DELETE` 를 실제로 던진 실험이다.** `BEGIN … ROLLBACK` 으로 감쌌고,
> **끝나고 `emp` 가 4행인 것을 확인했다**(맨 끝 「실행 검증」).\
> 문서 근거는 [PG 18 EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html) · [PG 18 ANALYZE](https://www.postgresql.org/docs/18/sql-analyze.html) · [MySQL 8.4 EXPLAIN ANALYZE](https://dev.mysql.com/doc/refman/8.4/en/explain.html#explain-analyze).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `actual rows` · `loops` · 시간 — 그리고 질의가 실제로 돈다

**왜 그런가**

```text
EXPLAIN          Seq Scan on emp  (cost=0.00..24.12 rows=377 width=44)
EXPLAIN ANALYZE  Seq Scan on emp  (cost=0.00..24.12 rows=377 width=44) (actual time=0.012..0.014 rows=3.00 loops=1)
                                                    ^^^^^^^^                        ^^^^^^^^^^^^ ^^^^^^^ ^^^^^^^
                                                    추정 (예보)                       실측 시간     실측 행  반복 수
```

| 칸 | 뜻 |
|---|---|
| `rows=` | 이 노드가 내놓을 것이라고 **추정한** 행 수 |
| `actual rows=` | **실제로** 내놓은 행 수 (**한 번 돌 때의 평균** — 9번) |
| `loops=` | 이 노드가 **몇 번 돌았나** |
| `actual time=a..b` | 첫 행까지 a 밀리초, 마지막 행까지 b 밀리초 (**한 번 돌 때의 평균**) |

그리고 결정적인 차이 하나 — **`EXPLAIN ANALYZE` 는 질의를 실제로 돌린다.**\
`SELECT` 면 결과를 버릴 뿐이지만, **PG 에서는 `INSERT`·`UPDATE`·`DELETE` 도 반영된다**(12번).

PG 18 에서는 `ANALYZE` 를 켜면 **`Buffers` 가 기본으로 함께** 나온다(2번 출력). 끄려면 `BUFFERS OFF` 를 명시한다.

---

### 2. `rows=377` 대 `actual rows=3.00` — 어긋나지만 무해하다

**출력**

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

**왜 그런가** — `emp` 는 **한 번도 `ANALYZE` 된 적이 없다.**

```text
### SQL: SELECT c.relname, c.reltuples, c.relpages FROM pg_class c WHERE c.relname IN ('emp','dept');
--- PG 18.6 ---
 relname | reltuples | relpages
---------+-----------+----------
 dept    |        -1 |        0
 emp     |        -1 |        0
```

`reltuples = -1` 은 「**아직 센 적 없음**」이다. 옵티마이저는 그때 **기본 가정**으로 예보하고, 125배 빗나갔다.

★ **그래도 문제가 되지 않는다.** 4행짜리 표에서는 어떤 계획을 골라도 결과와 비용이 사실상 같다.

```text
 무해한 어긋남                          해로운 어긋남
 +---------------------------+        +---------------------------+
 | 표가 작다                  |        | 표가 크다                  |
 | 어떤 계획을 골라도 같다      |        | 계획 선택이 갈린다          |
 | rows=377 / actual 3        |        | rows=10600 / actual 190100 |
 +---------------------------+        +---------------------------+
   -> 고칠 필요 없다                     -> 4·5번의 주제다
```

**「추정이 틀렸다」가 곧 「고쳐야 한다」는 아니다.** 그 어긋남이 **선택을 바꾸는지**를 본다.

---

### 3. `cho` — `salary` 가 `NULL` 이라 버려졌다

**왜 그런가** — `emp` 는 4행이고 `actual rows=3.00` 이 나왔다. 하나가 빠졌다.

```text
 emp                              salary > 100 의 판정
 +----+------+--------+           +--------------------+
 |  1 | ann  |    300 |           | 300 > 100 -> TRUE   |  남는다
 |  2 | bob  |    500 |           | 500 > 100 -> TRUE   |  남는다
 |  3 | cho  |   NULL |           | NULL > 100 -> UNKNOWN| 버린다  <- Rows Removed by Filter: 1
 |  4 | dan  |    400 |           | 400 > 100 -> TRUE   |  남는다
 +----+------+--------+           +--------------------+
```

`NULL` 과의 비교는 `TRUE` 도 `FALSE` 도 아닌 **`UNKNOWN`** 이고, `WHERE` 는 `TRUE` 인 행만 남긴다([04번](../04-null-three-valued-logic/)).

★ **`Rows Removed by Filter` 는 「사라진 행」의 정체를 계획에서 확인하는 칸이다.**\
「왜 한 행이 없지?」를 데이터가 아니라 **계획에서** 짚을 수 있다.

---

### 4. 추정 10,600 · 실측 190,100 — 18배 어긋났다

**출력**

```text
### SQL: EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS OFF) SELECT count(*) FROM t60_skew WHERE grp = 7;
--- PG 18.6 · 190,000행 추가 직후, ANALYZE 안 함 ---
 Aggregate  (cost=1153.44..1153.45 rows=1 width=8) (actual rows=1.00 loops=1)
   ->  Bitmap Heap Scan on t60_skew  (cost=146.44..1126.94 rows=10600 width=0) (actual rows=190100.00 loops=1)
         Recheck Cond: (grp = 7)
         Heap Blocks: exact=846
         ->  Bitmap Index Scan on t60_skew_grp  (cost=0.00..143.79 rows=10600 width=0) (actual rows=190100.00 loops=1)
               Index Cond: (grp = 7)
               Index Searches: 1
```

비교를 위해 **통계가 최신이던 장면**도 같이 본다.

```text
--- PG 18.6 · 1,000행 · ANALYZE 직후 ---
 Aggregate  (cost=14.43..14.44 rows=1 width=8) (actual rows=1.00 loops=1)
   ->  Bitmap Heap Scan on t60_skew  (cost=4.93..14.18 rows=100 width=0) (actual rows=100.00 loops=1)
         Recheck Cond: (grp = 7)
         Heap Blocks: exact=5
         ->  Bitmap Index Scan on t60_skew_grp  (cost=0.00..4.90 rows=100 width=0) (actual rows=100.00 loops=1)
               Index Cond: (grp = 7)
               Index Searches: 1
```

**왜 그런가** — 통계는 **1단계의 분포**를 기억하고 있다.

```text
 통계가 기억하는 것                    실제 데이터
 grp 는 10가지 값                     grp 는 10가지 값        <- 같다
 표는 1,000행                         표는 191,000행          <- 다르다
 grp=7 은 전체의 1/10                 grp=7 은 전체의 99.5%   <- 완전히 다르다
```

**행 수는 어느 정도 따라왔다**(100 → 10,600). 표 파일이 커진 것을 보고 비례로 늘려 잡기 때문이다.\
**따라오지 못한 것은 분포다** — 「grp 마다 1/10」이라는 가정이 그대로 남아 `191,000 / 10 ≈ 10,600` 이 나왔다.

★ **낡는 것은 「행 수」가 아니라 「분포」다.** 그래서 대량 적재가 **치우칠수록** 더 크게 빗나간다.

---

### 5. 연산자 선택이 잘못됐다

**출력** — `ANALYZE` 를 돌린 뒤의 계획과 나란히 놓으면 보인다.

```text
 장면          추정 rows=      실측 actual rows=     뽑힌 연산자
 1 (통계 최신)      100            100              Bitmap Heap Scan
 2 (통계 낡음)   10,600        190,100              Bitmap Heap Scan   <- 그대로다
 3 (ANALYZE 뒤) 189,988       190,100              Seq Scan           <- 바뀌었다
```

**왜 그런가** — **추정은 계획의 입력**이다.

```text
 +---------------------------------------------------+
 | 1. rows= 를 추정한다            10,600            |
 | 2. 그 rows= 로 비용을 계산한다   1126.94           |
 | 3. 그 비용으로 연산자를 고른다    Bitmap Heap Scan  |
 | 4. 실제로는 190,100행이었다      -> 잘못된 도구     |
 +---------------------------------------------------+
```

[59번](../59-scan-join-sort-operators/)에서 봤듯, **표의 절반을 넘게 읽을 거면 `Seq Scan` 이 맞다.**\
장면 2 의 질의는 표의 **99.5%** 를 읽는데 비트맵으로 긁었다 — 인덱스를 읽고, 비트맵을 만들고, 그러고도 표의 846 블록을 다 읽었다.

★ **질의는 정상으로 돌았고 결과도 맞다. 느릴 뿐이다.** 그래서 조용하다.\
`EXPLAIN` 만 봤다면 「인덱스를 타네, 좋군」으로 끝났을 것이다. **`actual rows` 를 같이 봐야 드러난다.**

---

### 6. 추정 189,988 · 연산자는 `Seq Scan` 으로 바뀐다

**출력**

```text
### SQL: ANALYZE t60_skew;  EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS OFF) SELECT count(*) FROM t60_skew WHERE grp = 7;
--- PG 18.6 ---
 Aggregate  (cost=3710.47..3710.48 rows=1 width=8) (actual rows=1.00 loops=1)
   ->  Seq Scan on t60_skew  (cost=0.00..3235.50 rows=189988 width=0) (actual rows=190100.00 loops=1)
         Filter: (grp = 7)
         Rows Removed by Filter: 900
```

**왜 그런가** — `ANALYZE` 가 표를 다시 표본 조사해 **치우친 분포를 통계에 담았다.**

```text
 ANALYZE 전                            ANALYZE 후
 추정 10,600   (18배 과소)              추정 189,988  (실측 190,100 의 99.94%)
 Bitmap Heap Scan                      Seq Scan
 인덱스 -> 비트맵 -> 표 846블록          표를 한 번 훑는다
```

★ **`Rows Removed by Filter: 900`** 이 이 계획이 실제로 한 일을 말해 준다 —\
191,000행을 읽어 900행을 버렸다. **읽은 것의 99.5% 를 남겼다.** 이런 질의에 인덱스는 방해만 된다.

**처방은 하나다 — 대량 적재·대량 삭제 직후에 `ANALYZE` 를 돌린다.**\
자동 갱신에 기대면 그사이 도는 질의가 전부 틀린 계획으로 돈다.

---

### 7. MySQL 은 장면 2·3 모두 약 95,500 — 실측은 190,100 이다

**출력**

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

**왜 그런가** — **두 엔진이 서로 다르게 틀렸다.**

```text
 장면          PostgreSQL              MySQL 8.4.10
 1 (통계 최신)   100 / 100               100 / 100
 2 (통계 낡음)   10,600 / 190,100        95,500 / 190,100
 3 (ANALYZE 뒤) 189,988 / 190,100       95,496 / 190,100     <- 거의 안 변했다
                (추정 / 실측)
```

- **PG** — 낡았을 때 18배 과소, `ANALYZE` 뒤 거의 정확.
- **MySQL** — 낡았을 때 2배 과소, **`ANALYZE TABLE` 뒤에도 2배 과소 그대로.**

★ **MySQL 쪽은 「통계가 낡아서」가 아니다.** 장면 2 와 장면 3 의 추정이 거의 같다(95,500 → 95,496).\
통계를 다시 잡아도 이 조건의 추정은 안 고쳐졌다.

**표본 페이지를 열 배로 늘려도 마찬가지였다.**

```text
### SQL: ALTER TABLE t60_skew STATS_SAMPLE_PAGES=200;  ANALYZE TABLE t60_skew;
###      EXPLAIN SELECT count(*) FROM t60_skew WHERE grp = 7;
--- MySQL 8.4.10 ---
| table    | type | key   | rows  | Extra       |
| t60_skew | ref  | k_grp | 95256 | Using index |
```

> 표 테두리와 `id`·`select_type`·`partitions`·`possible_keys`·`key_len`·`ref`·`filtered` 칸을 지웠다.

★ **왜 절반인지는 이 실측만으로 단정하지 않는다.** 확인된 사실은 둘이다 —\
**① `ANALYZE TABLE` 을 돌려도 2배 어긋남이 남았다. ② 표본을 열 배 늘려도 같았다.**

**그래서 MySQL 쪽 처방은 「`ANALYZE TABLE` 을 돌린다」로 끝나지 않는다.**\
치우친 분포에서는 `EXPLAIN ANALYZE` 로 **실측을 직접 보는** 수밖에 없다.

---

### 8. 표의 행 수는 고쳐졌고, 한 값의 행 수 추정은 안 고쳐졌다

**출력**

```text
### SQL: SELECT table_rows FROM information_schema.tables WHERE table_schema='study' AND table_name='t60_skew';
--- MySQL 8.4.10 ---
장면 1: 1000        장면 2: 1000  <- 낡았다        장면 3: 190992  <- 고쳐졌다
```

```text
### SQL: SHOW INDEX FROM t60_skew;     (장면 3)
--- MySQL 8.4.10 ---
| Key_name | Column_name | Cardinality |
| PRIMARY  | id          |      190992 |
| k_grp    | grp         |           9 |
```

> 표 테두리와 `Table`·`Non_unique`·`Seq_in_index`·`Collation`·`Sub_part`·`Packed`·`Null`·
> `Index_type`·`Comment`·`Index_comment`·`Visible`·`Expression` 칸을 지웠다.

**실제 분포는 이렇다.**

```text
### SQL: SELECT grp, count(*) FROM t60_skew GROUP BY grp ORDER BY grp;
--- MySQL 8.4.10 ---
 grp |  count(*)          grp |  count(*)
-----+----------         -----+----------
   0 |      100            5 |      100
   1 |      100            6 |      100
   2 |      100            7 |  190,100   <- 여기만 치우쳤다
   3 |      100            8 |      100
   4 |      100            9 |      100
```

**왜 그런가**

```text
 ANALYZE TABLE 이 고친 것              고치지 못한 것
 +---------------------------+        +---------------------------+
 | TABLE_ROWS  1000 -> 190992 |        | grp=7 의 행 수 추정 95,496 |
 | PRIMARY 카디널리티 190992  |        |   (실제 190,100)          |
 | k_grp 카디널리티 9         |        |                           |
 |   (실제 서로 다른 값 10)    |        |                           |
 +---------------------------+        +---------------------------+
   "몇 행인가"·"몇 가지인가"는 맞췄다      "한 가지에 몇 행인가"는 못 맞췄다
```

★ **카디널리티(9)는 거의 맞는데 한 값의 행 수 추정만 절반이다.** 이 두 숫자가 따로 논다는 것이 관찰된 사실이다.\
치우친 분포를 표현하려면 **값마다의 분포**(히스토그램)가 필요한데, 이 실험에서는 그것을 만들지 않았다.\
*(MySQL 에는 `ANALYZE TABLE … UPDATE HISTOGRAM ON` 이 있다. 이 편에서는 돌려 보지 않았다.)*

---

### 9. 모두 10행이다 — `actual rows × loops`

**출력**

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

**왜 그런가**

```text
 안쪽 노드의 표시                      실제로 일어난 일
 actual rows=1.00  loops=10           바깥 10행마다 한 번씩, 모두 10번 돌았다
        ^             ^               매번 1행씩 내놓았다
   한 번 돌 때 평균    몇 번 돌았나      -> 총 1.00 × 10 = 10행
```

★ **PG 의 `actual rows` 는 「한 번 돌 때의 평균」이다.** `actual time` 도 마찬가지다.\
`rows=1.00` 만 보고 「1행밖에 안 읽네」라고 읽으면 **일의 양을 10분의 1로 잘못 잰다.**

`Index Searches: 10` 이 같은 이야기를 다른 칸으로 한다 — 인덱스를 10번 뒤졌다.\
`Buffers: shared hit=37 read=3` 도 **10번 합계**다 — 바깥 노드의 `hit=1` 과 합쳐 부모의 `hit=38 read=3` 이 된다.

비용 — **진단할 때는 `loops` 가 큰 노드를 먼저 본다.** 한 번이 싸도 만 번 돌면 비싸다([59번](../59-scan-join-sort-operators/)).

MySQL 도 같은 표기다 — `Single-row index lookup on b using PRIMARY (id=s.ref) … (actual time=0.00296..0.00299 rows=1 loops=10)`.

---

### 10. `hit` 은 캐시에서, `read` 는 새로 읽어 온 페이지다

**왜 그런가**

```text
Buffers: shared hit=37 read=3
                ^^^^^^^   ^^^^^^
                공유 버퍼 캐시에 이미 있었다   캐시에 없어 새로 가져왔다
```

```text
 첫 실행                               두 번째 실행
 +---------------------------+        +---------------------------+
 | hit=37  read=3            |        | hit=40  read=0            |
 | 3 페이지를 새로 읽었다      |        | 그 3 페이지가 캐시에 남았다 |
 +---------------------------+        +---------------------------+
   -> "처음엔 느리고 두 번째는 빠르다" 의 정체
```

실제로 같은 질의를 두 번 던져 보면 캐시가 데워진 상태가 보인다.

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

`hit=896`·`read` 없음 — **디스크를 한 번도 안 건드렸다.** 그래서 빠르다.\
같은 계획이 캐시가 빈 상태였다면 `read=896` 이 되고 훨씬 느렸을 것이다.

★ **`Buffers` 와 `Rows Removed by Filter` 를 같이 보면 「얼마나 헛일을 했나」가 나온다.**\
896 페이지를 읽어 200행을 남기고 **199,800행을 버렸다** — 읽은 것의 0.1% 만 썼다.

---

### 11. 시간은 캐시·부하에 달렸다 — 페이지 수와 행 수를 본다

**왜 그런가**

```text
 흔들리는 칸                            흔들리지 않는 칸
 +---------------------------+        +---------------------------+
 | actual time=              |        | actual rows=              |
 |   캐시 상태에 달렸다        |        | loops=                    |
 |   다른 부하에 달렸다        |        | Buffers (페이지 수)        |
 |   판마다 다르다             |        | Rows Removed by Filter    |
 | cost= (추정)               |        | 연산자 이름 · Index Cond   |
 +---------------------------+        +---------------------------+
```

10번이 그 이유를 보여 준다 — **같은 계획이 캐시 상태만으로 수십 배 빨라지거나 느려진다.**\
시간을 근거로 두 계획을 비교하면 **먼저 돈 쪽이 지고 나중에 돈 쪽이 이긴다.**

★ **[09번](../09-limit-offset-keyset-pagination/)이 이 규칙을 처음부터 지켰다** — `OFFSET` 의 비용을 시간이 아니라\
**자식 노드의 `actual rows`**(100,010 대 10)로 쟀다. 그 숫자는 판마다 안 바뀐다.

**그래도 시간을 볼 자리는 있다** — 「어느 노드에서 시간이 가나」를 *한 계획 안에서* 비교할 때다.\
다른 계획·다른 판과 비교할 때가 아니다.

**기록에 남길 때는 `TIMING OFF, SUMMARY OFF` 를 붙인다.** 시간 칸이 없으면 대조가 쉬워진다 —\
이 편의 계획 대부분이 그 형태인 이유다.

---

### 12. 첫 번째는 **3**, 두 번째는 **4** 다

**출력**

```text
### SQL: BEGIN;
###      EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS OFF) DELETE FROM emp WHERE id = 1;
--- PG 18.6 ---
 Delete on emp  (cost=0.15..8.17 rows=0 width=0) (actual rows=0.00 loops=1)
   ->  Index Scan using emp_pkey on emp  (cost=0.15..8.17 rows=1 width=6) (actual rows=1.00 loops=1)
         Index Cond: (id = 1)
         Index Searches: 1

### SQL: SELECT count(*) FROM emp;          (같은 트랜잭션 안)
--- PG 18.6 ---
 count
-------
     3

### SQL: ROLLBACK;  SELECT count(*) FROM emp;
--- PG 18.6 ---
 count
-------
     4
```

**왜 그런가** — **`EXPLAIN ANALYZE` 는 「계획을 보여 주는」 명령이 아니라 「돌려 보고 계획을 보여 주는」 명령이다.**

```text
 안전한 절차                            위험한 절차
 +----------------------------+        +----------------------------+
 | BEGIN;                     |        | EXPLAIN ANALYZE DELETE … ; |
 | EXPLAIN ANALYZE DELETE … ; |        |   -> 지워졌다               |
 | -- 계획을 본다              |        |   -> 자동 커밋이면 끝이다    |
 | ROLLBACK;                  |        |   -> 되돌릴 수 없다          |
 +----------------------------+        +----------------------------+
```

★ **`EXPLAIN` 과 `EXPLAIN ANALYZE` 사이에는 되돌릴 수 없는 차이가 있다.** 낱말 하나다.\
「계획만 보려고」 던진 문장이 운영 데이터를 지울 수 있다.

**변경문의 계획이 궁금할 때의 규칙은 둘이다.**

```text
1. 그냥 EXPLAIN 으로 본다            (안 돈다 — 14번)
2. 실측이 꼭 필요하면 BEGIN … ROLLBACK 으로 감싼다
```

이 실험도 그 규칙을 지켰다 — `emp` 는 지금도 4행이다.

---

### 13. 지웠다 — `actual rows=0.00` 은 「돌려준 행이 없다」는 뜻이다

**왜 그런가** — 계획 노드의 `actual rows` 는 **그 노드가 위로 올린 행 수**다.

```text
 Delete on emp            (actual rows=0.00)   <- 위로 올린 행: 0개
   -> Index Scan on emp   (actual rows=1.00)   <- 찾아서 넘긴 행: 1개  <= 이게 지워진 행이다
```

`DELETE` 는 보통 아무 행도 돌려주지 않는다. `RETURNING` 을 붙이면 달라진다.

```text
 DELETE FROM emp WHERE id=1;                   Delete 노드의 actual rows = 0
 DELETE FROM emp WHERE id=1 RETURNING *;       Delete 노드의 actual rows = 1
```

★ **변경문의 계획에서 「몇 행이 영향을 받았나」는 맨 윗줄이 아니라 그 아래 스캔 노드에서 읽는다.**\
12번에서 `Index Scan` 의 `actual rows=1.00` 이 지워진 한 행이고, `SELECT count(*)` 가 4 → 3 으로 그것을 확인해 줬다.

`INSERT` 도 같다 — 12번의 `Insert on t60_tx (actual rows=0.00)` 아래 `Function Scan … (actual rows=5.00)` 이 넣은 5행이다.

---

### 14. 안 들어간다 — `EXPLAIN` 만으로는 질의가 돌지 않는다

**출력**

```text
### SQL: BEGIN; CREATE TABLE t60_tx (id int);
###      EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS OFF) INSERT INTO t60_tx SELECT g FROM generate_series(1,5) g;
--- PG 18.6 ---
 Insert on t60_tx  (cost=0.00..0.05 rows=0 width=0) (actual rows=0.00 loops=1)
   ->  Function Scan on generate_series g  (cost=0.00..0.05 rows=5 width=4) (actual rows=5.00 loops=1)

### SQL: SELECT count(*) FROM t60_tx;
 count
-------
     5        <- ANALYZE 를 붙였더니 들어갔다

### SQL: EXPLAIN INSERT INTO t60_tx SELECT g FROM generate_series(101,105) g;     -- ANALYZE 없이
 Insert on t60_tx  (cost=0.00..0.05 rows=0 width=0)
   ->  Function Scan on generate_series g  (cost=0.00..0.05 rows=5 width=4)

### SQL: SELECT count(*) FROM t60_tx;
 count
-------
     5        <- 안 들어갔다
```

**왜 그런가** — 두 계획을 나란히 놓으면 차이가 한눈에 보인다.

```text
 EXPLAIN ANALYZE 의 출력                EXPLAIN 의 출력
 Insert on t60_tx (cost=…) (actual rows=0.00 loops=1)    Insert on t60_tx (cost=…)
   -> Function Scan … (actual rows=5.00 loops=1)           -> Function Scan …
                        ^^^^^^^^^^^^^^^^^^^^^^                              ^
                        실측 칸이 있다 = 돌았다                 실측 칸이 없다 = 안 돌았다
```

★ **`(actual …)` 칸의 유무가 「돌았나」의 표시다.** 이 규칙은 15번에서 MySQL 을 읽을 때 그대로 쓰인다.

---

### 15. `UPDATE` 는 `<not executable by iterator executor>`, `INSERT` 는 계획만 — 데이터는 안 바뀐다

**출력**

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
|   0 |
+-----+
```

**왜 그런가** — **`<not executable by iterator executor>` 는 에러가 아니다.** 계획 자리에 찍힌 **문구**다.\
에러 번호도 SQLSTATE 도 없고, 결과 집합의 한 행으로 돌아온다.

`INSERT` 쪽은 계획을 주는데 — **`(actual …)` 칸이 없다**(14번의 규칙). 돌지 않았다는 표시이고,\
실제로 **`id = 98` 인 행이 0개**인 것으로 확인했다. 앞서 `(99, 99)` 로도 한 번 던져 같은 결과였다.

```text
 PostgreSQL 18.6                        MySQL 8.4.10
 +-----------------------------+       +-----------------------------+
 | EXPLAIN ANALYZE DELETE      |       | EXPLAIN ANALYZE DELETE      |
 |   -> 진짜로 지운다            |       |   -> <not executable …>     |
 |   -> 트랜잭션으로 감싸라      |       |   -> 아무 일도 안 일어난다    |
 |   -> 실측을 볼 수 있다        |       |   -> 실측을 볼 수 없다        |
 +-----------------------------+       +-----------------------------+
   위험하지만 실측이 나온다               안전하지만 실측이 없다
```

★ **안전한 쪽이 좋기만 한 것은 아니다.** MySQL 에서는 **변경문의 실측을 이 도구로 볼 방법이 없다.**\
`EXPLAIN` 으로 모양만 보고, 영향 범위는 **같은 조건의 `SELECT count(*)`** 로 가늠한다.

**두 엔진을 오갈 때 이 차이를 기억하지 않으면 두 방향으로 다 틀린다** —\
PG 에서 「MySQL 처럼 안 돌겠지」 하면 데이터가 지워지고, MySQL 에서 「PG 처럼 실측이 나오겠지」 하면 안 나온다.

---

### 16. `Sort Method` 줄이 달라진다

**출력**

```text
### SQL: SET work_mem = '64kB';  EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF, BUFFERS OFF) SELECT id FROM t60_s ORDER BY pad, id;
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

**왜 그런가**

```text
 work_mem = 64kB                       work_mem = 64MB
 +-----------------------------+       +-----------------------------+
 | Sort Method: external merge |       | Sort Method: quicksort      |
 | Disk: 8880kB                |       | Memory: 17082kB             |
 | 정렬을 디스크에 쏟아 가며 한다  |       | 메모리 안에서 끝낸다          |
 | 추정 비용 37749             |       | 추정 비용 21337             |
 +-----------------------------+       +-----------------------------+
   같은 행 수(200,000), 같은 결과. 다른 것은 어디서 정렬했나뿐이다.
```

★ **`Sort Method` 는 `EXPLAIN` 에는 안 나온다.** `EXPLAIN ANALYZE` 를 돌려야 보인다 —\
「정렬이 디스크로 넘쳤나」는 **추정할 수 없는 것**이고, 실제로 돌려 봐야 안다.

**추정 비용도 달랐다**(37749 대 21337) — 옵티마이저는 `work_mem` 설정까지 계산에 넣는다.\
즉 **메모리 설정을 바꾸면 계획 자체가 바뀔 수 있다.**

해시 조인·해시 집계에도 같은 성격의 칸이 있다 — **`Batches:` 가 2 이상**이면 메모리에 안 들어가 나눠 처리한 것이다.

**MySQL 의 `EXPLAIN ANALYZE` 출력에는 이 칸이 없다.** 정렬이 디스크를 썼는지는 다른 도구로 봐야 한다.

---

### 17. 어긋남 → `loops` → 버린 행 → 디스크

**왜 그런가** — `EXPLAIN ANALYZE` 출력에서 실제로 볼 것은 네 가지이고, 순서가 있다.

```text
1. rows= 와 actual rows= 가 크게 어긋나는 노드가 있나?     (4·5·7번)
        ↓ 있으면 -> 통계를 의심한다 (ANALYZE) · 계획 선택이 틀렸을 수 있다
2. loops= 가 큰 노드가 있나?                              (9번)
        ↓ 있으면 -> 그 노드의 비용에 loops 를 곱해 읽는다
3. Rows Removed by Filter 가 크나? Buffers 대비 남는 행이 적나?   (10번)
        ↓ 그러면 -> 읽고 버리는 헛일이다. 조건을 인덱스로 내릴 수 있나
4. Sort Method 가 external merge 인가? Batches 가 2 이상인가?    (16번)
        ↓ 그러면 -> work_mem 을 볼 자리다
```

```text
 먼저 보는 것                           나중에 보는 것 (또는 안 보는 것)
 +---------------------------+        +---------------------------+
 | 추정 대 실측의 격차         |        | actual time 의 절댓값      |
 | loops                     |        | cost 의 소수점             |
 | 버린 행 수 · 페이지 수      |        | 다른 판과의 시간 비교        |
 +---------------------------+        +---------------------------+
```

★ **1번이 가장 중요하다.** 1번이 크게 어긋나 있으면 2\~4번에서 본 것이 전부 **잘못 고른 계획의 증상**일 뿐이다.\
통계를 고치고 계획이 바뀌면 그 증상이 통째로 사라진다 — 5번과 6번이 그것을 보여 줬다.

**그리고 MySQL 에서는 1번에 함정이 있다**(7번) — `ANALYZE TABLE` 을 돌려도 어긋남이 남을 수 있다.\
그때는 통계를 더 손보는 대신 **질의나 인덱스를 바꾸는** 쪽을 본다([59번](../59-scan-join-sort-operators/)).

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `emp` 의 추정 대 실측 (2·3번) | PG 18.6 | 3회 | **`emp` 를 읽기만 했다** · `reltuples=-1` 확인 |
| ★ 통계 낡음 3장면 (4·5·6번) | PG 18.6 | **각 3회** | `BEGIN … ROLLBACK` · **연산자가 바뀐 자리** |
| ★ 통계 낡음 3장면 (7·8번) | MySQL 8.4.10 | **각 3회** | `DROP TABLE` 로 지움 · `EXPLAIN ANALYZE` |
| `STATS_SAMPLE_PAGES=200` (7번) | MySQL 8.4.10 | 2회 | 표본을 열 배로 늘려도 같았다 |
| `SHOW INDEX` · `TABLE_ROWS` (8번) | MySQL 8.4.10 | 각 3회 | 장면마다 |
| 실제 분포 `GROUP BY grp` (8번) | MySQL 8.4.10 | 1회 | 190,100 확인 |
| `loops` 와 `Buffers` (9·10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 중첩 루프 강제 |
| ★ `EXPLAIN ANALYZE DELETE` (12·13번) | PG 18.6 | **1회** | **`emp` 에 실제로 던짐** · `BEGIN … ROLLBACK` · **4→3→4 확인** |
| `EXPLAIN ANALYZE INSERT` (13·14번) | PG 18.6 | 2회 | `t60_tx` · `ANALYZE` 유무 대조 |
| ★ MySQL 변경문 (15번) | MySQL 8.4.10 | **각 2회** | `UPDATE`·`DELETE`·`INSERT` · **행이 안 바뀐 것 확인** |
| `Sort Method` (16번) | PG 18.6 | 2회 | `work_mem` 64kB / 64MB |
| 뒷정리 확인 | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\dtvm` · `SHOW FULL TABLES` · **`emp` 4행 재확인** |

★ **계획 드리프트 재확인(제출 직전)** — 본문 계획을 다시 찍어 1차 관찰과 대조했다.

```text
 다시 찍어도 같았던 것                            다시 찍었더니 달라진 것
 emp 의 rows=377 / actual rows=3.00               PG 장면 3 의 추정 189,988 -> 190,249
 장면 2 의 추정 10,600 / 실측 190,100             MySQL 장면 3 의 추정 95,496 -> 93,099
 장면 2 와 3 의 연산자 (Bitmap -> Seq Scan)        actual time 전부 (P0 블록은 재확인 값으로 갱신)
 MySQL 장면 2·3 의 실측 190,100
 loops=10 · Index Searches: 10
 Buffers: shared hit=896 · Rows Removed by Filter: 199800
 MySQL 의 <not executable by iterator executor>
 emp 가 4행인 것 (12번 실험 뒤)
```

★ **드리프트가 실제로 있었다 — 추정치에서만이다.** `ANALYZE` 가 표본 조사라 판마다 값이 다르다.\
PG 장면 3 은 189,988\~190,249, MySQL 장면 3 은 93,099\~95,500 사이를 오갔다.

```text
 흔들렸다                                안 흔들렸다
 rows= (추정)                            actual rows= (실측)
 cost= 의 값                             연산자 이름 (Bitmap -> Seq Scan 의 전환)
 actual time=                            Rows Removed by Filter · Buffers · loops
                                         MySQL 이 변경문을 안 돈다는 사실
```

★ **그래서 본문의 결론은 전부 오른쪽 칸 위에 세웠다.**\
「PG 는 `ANALYZE` 로 고쳤고 MySQL 은 **약 2배** 어긋남이 남았다」로 읽는다 — 95,496 이라는 낱값이 아니라 **배수**가 결론이다.\
본문 블록은 **세 장면을 한 세션에서 이어 찍은 출력**이라 그대로 두고, 흔들림은 이 표에 남긴다.\
([59번](../59-scan-join-sort-operators/)에서는 같은 흔들림이 경계 위에서 **연산자까지** 뒤집었다 — 이 편의 실험은 경계에서 멀어 연산자가 안 흔들렸다.)


**구현 의존 항목** — 4\~8번의 **추정치와 그 결과 뽑힌 연산자**다. 어긋남의 방향과 배수는\
**이 데이터·이 통계**의 값이고, 두 엔진이 서로 다르게 틀렸다는 것이 그 증거다.\
재현되는 것은 숫자가 아니라 **「통계가 낡으면 선택이 틀린다」는 성질**이다.

**언어 보장 항목** — 1·9·13·14번. `actual rows` 가 평균이고 `loops` 를 곱해야 하는 것,\
`EXPLAIN` 만으로는 질의가 돌지 않는 것, 변경문 노드의 `actual rows` 가 「돌려준 행 수」인 것은\
두 엔진의 출력과 문서에서 같았다.

**한쪽에서만 결론이 서는 실험** — 10·16번(`Buffers`·`Sort Method`)은 **PG 에서만** 볼 수 있다.\
MySQL 의 `EXPLAIN ANALYZE` 출력에는 그 칸이 없다. **이 둘의 근거는 PG 출력뿐이다.**\
반대로 12번과 15번은 **양쪽을 다 던져야 결론이 선다** — 한쪽만 보면 「`EXPLAIN ANALYZE` 는 위험하다」나\
「안전하다」 중 하나만 외우게 되고, 엔진을 옮기는 순간 틀린다.

**버전** — PG 18 은 `actual rows` 를 **소수 둘째 자리까지** 찍고(`rows=3.00`), `ANALYZE` 와 함께 **`BUFFERS` 가 기본으로 켜진다.**\
둘 다 이전 버전과 표기가 다르다. MySQL 의 `EXPLAIN ANALYZE` 는 8.0.18 부터다.\
버전이 오르면 **12·15·16번**(변경문 동작과 계측 칸)을 다시 돌린다.
