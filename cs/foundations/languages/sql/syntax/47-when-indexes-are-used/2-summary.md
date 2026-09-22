# sql/47-인덱스를 언제 타고 언제 안 타나 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) · [PostgreSQL 18 · Indexes](https://www.postgresql.org/docs/18/indexes.html) · [MySQL 8.4 · EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html) · [MySQL 8.4 · Optimization and Indexes](https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> ★ **측정 조건** — 20,000행 `t47`, **`ANALYZE`/`ANALYZE TABLE` 직후**, 기본 설정, 다른 부하 없음.\
> ★★ **실행 계획은 관찰이지 보장이 아니다.** 아래 계획은 **제출 직전에 다시 찍어 대조했다** — 드리프트 여부는 [3-answer.md](3-answer.md) 의 「실행 검증」에 적었다.\
> **버전** — 이 주제의 동작에 「어느 버전부터」가 붙는 것을 두 매뉴얼에서 찾지 못해 **적지 않는다.**\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 20,000행짜리 `t47` 을 만들어 인덱스를 얹고 **지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> **선행** — [35 타입 체계와 캐스팅](../35-type-system-and-casting/) · [46 인덱스 정의](../46-index-definition-composite-partial-expression/).\
> ★ **범위 선언** — **[46번](../46-index-definition-composite-partial-expression/)은 「어떻게 정의하나」, 여기는 「그래서 탈까 안 탈까」다.** 탐색 구조 자체는 [`15-b-tree`](../../../../../data-structure/15-b-tree/)가 정본이다.

## 한눈에 — 쉽게 말하면

**인덱스를 탄다 = 「정렬해 둔 순서로 답할 수 있는 질문」을 던졌다는 뜻.**

```text
책 뒤의 찾아보기는 가나다순이다

"ㅂ 으로 시작하는 낱말"      -> 연속 구간이다        -> 찾아보기를 쓴다
"-하기 로 끝나는 낱말"       -> 흩어져 있다          -> 본문을 다 읽는다
"낱말을 거꾸로 뒤집은 것"     -> 정렬 기준이 다르다    -> 못 쓴다
"낱말의 절반이 해당된다"      -> ★ 쓸 수는 있는데 안 쓴다 — 본문을 그냥 읽는 게 싸다
```

"똑같은 구조다" — 인덱스가 버려지는 자리는 **딱 두 종류**다.

```text
(1) 못 쓴다 — 정렬 순서로 답할 수 없는 질문이다
      열에 함수를 씌웠다 · 앞이 열린 LIKE · 암시 타입 변환 · collation 불일치 · 선행 열 누락

(2) 쓸 수 있는데 안 쓴다 — 옵티마이저가 「그게 더 비싸다」고 판단했다
      선택도가 낮다 (찾는 행이 표의 상당 부분이다)
```

★ **이 둘을 `EXPLAIN` 한 칸으로 구분할 수 있다.**

| 비유 | 실체 |
|---|---|
| 찾아보기를 쓴다 | `Index Scan` / `type: ref`·`range` |
| 본문을 다 읽는다 | `Seq Scan` / `type: ALL` |
| 찾아보기에 그 질문이 없다 | **`possible_keys: NULL`** — 후보에서 아예 빠졌다 |
| 찾아보기는 있는데 안 썼다 | **`possible_keys` 는 있고 `key: NULL`** — 비용으로 버렸다 |
| 찾아보기만으로 답이 나온다 | `Index Only Scan` / `Extra: Using index` |

> **선택도(selectivity)** — 조건에 맞는 행이 전체에서 차지하는 비율.\
> 예: 20,000행 중 10행이면 선택도가 높다(0.05%), 7,000행이면 낮다(35%).

> **실행 계획(execution plan)** — 엔진이 그 질의를 **어떻게 처리하기로 정했는지**의 설명.\
> 예: `EXPLAIN` 이 보여 준다. ★ **그 순간의 통계와 설정이 정한 것이라 보장이 아니다.**

## 이 주제가 답하려는 질문

1. **인덱스가 「못 쓰이는」 자리와 「안 쓰이는」 자리는 어떻게 구분하나?**
2. **★ 열에 함수를 씌우면 왜 죽고, 표현식 인덱스가 왜 살리나?**
3. **★ 선택도가 얼마나 낮아지면 계획이 갈리나?** — 그 경계를 실제로 잰다.

## 예시 데이터 — 이 묶음이 공유하는 것

```text
t47 (20,000행) — 이 편이 만들었다가 지운 표
+-----+-------------+------------------------------------------+
| id  | int PK      | 1 .. 20000                               |
| a   | int         | id % 100   -> 100가지, 각 200행 (1%)      |
| b   | int         | id % 10    -> 10가지, 각 2000행 (10%)     |
| k   | int         | = id       -> 물리 순서와 상관계수 1       |
| r   | int         | (id*7919) % 20000 + 1  -> ★ 상관계수 ~0   |
| v   | varchar(30) | 'name000001' .. 'name020000'             |
+-----+-------------+------------------------------------------+

인덱스: t47_pkey(id) · t47_ab_idx(a,b) · t47_b_idx(b) · t47_k_idx(k) · t47_r_idx(r) · t47_v_idx(v)
       + 실험 중 추가한 t47_upper_idx((upper(v)))
```

★ **`k` 와 `r` 을 따로 둔 이유** — 값이 같은 범위인데 **물리적 배치가 다르다.**\
`k` 는 저장 순서와 같고 `r` 은 흩어져 있다. 3번에서 이 차이가 계획을 가른다.

```text
--- PG 18.6 ---
SELECT correlation FROM pg_stats WHERE tablename='t47' AND attname IN ('k','r');
  correlation  
---------------
             1            <- k : 저장 순서 = 값 순서
 -0.0007359975            <- r : 무관하다
(2 rows)
```

## 동작 방식

### 1. 선행 열이 빠지면 — **후보에서 아예 빠진다**

**언제 쓰나** — 복합 인덱스가 있는데 안 쓰이는 것 같을 때. [46 번 1번의 정렬 그림](../46-index-definition-composite-partial-expression/)이 근거다.

`t47_ab_idx` 는 `(a, b)` 다. 조건을 셋으로 바꿔 던졌다.

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE a=7 AND b=7;
                QUERY PLAN                 
-------------------------------------------
 Bitmap Heap Scan on t47
   Recheck Cond: ((a = 7) AND (b = 7))
   ->  Bitmap Index Scan on t47_ab_idx
         Index Cond: ((a = 7) AND (b = 7))

EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE a=7;
              QUERY PLAN               
---------------------------------------
 Bitmap Heap Scan on t47
   Recheck Cond: (a = 7)
   ->  Bitmap Index Scan on t47_ab_idx
         Index Cond: (a = 7)

EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE b=7;
    QUERY PLAN     
-------------------
 Seq Scan on t47            <- ★ 인덱스가 사라졌다
   Filter: (b = 7)
```

**MySQL 은 `key_len` 으로 「몇 칸을 썼나」까지 보여 준다.**

```text
--- MySQL 8.4.10 ---  (폭에 맞춰 select_type·partitions·filtered 를 뺐다)
EXPLAIN SELECT * FROM t47 WHERE a=7 AND b=7;
+-------+------+---------------+------------+---------+-------------+------+
| table | type | possible_keys | key        | key_len | ref         | rows |
+-------+------+---------------+------------+---------+-------------+------+
| t47   | ref  | t47_ab_idx    | t47_ab_idx |       8 | const,const |  200 |
+-------+------+---------------+------------+---------+-------------+------+

EXPLAIN SELECT * FROM t47 WHERE a=7;
| t47   | ref  | t47_ab_idx    | t47_ab_idx |       4 | const       |  200 |

EXPLAIN SELECT * FROM t47 WHERE b=7;
+-------+------+---------------+------+---------+------+-------+-------------+
| table | type | possible_keys | key  | key_len | ref  | rows  | Extra       |
+-------+------+---------------+------+---------+------+-------+-------------+
| t47   | ALL  | NULL          | NULL |    NULL | NULL | 19172 | Using where |
+-------+------+---------------+------+---------+------+-------+-------------+
```

그림 해설 — 세 줄을 나란히 읽으면 셋이 보인다.

```text
                  a=7 AND b=7    a=7 만    b=7 만
key_len           8              4         NULL      <- int 4바이트 × 쓴 열 수
possible_keys     인덱스          인덱스     ★ NULL   <- 후보에서 빠졌다
rows              200            200       19172
```

★ **`key_len` 이 「복합 인덱스의 몇 칸까지 썼나」를 바이트로 알려 준다.**\
`(a,b)` 중 `a` 만 쓰면 4, 둘 다 쓰면 8 이다. **인덱스를 「탔다」와 「제대로 탔다」가 다르다**는 것을 이 숫자가 잡아 준다.

비용 — `b=7` 은 2,000행(10%)인데 **행 수 때문에 버려진 것이 아니다.**\
`possible_keys` 가 `NULL` 인 것이 증거다 — **애초에 쓸 수 있는 인덱스가 없었다.** 3번과 대비되는 자리다.

**`b` 전용 인덱스를 만들면 다시 탄다.**

```text
--- PG 18.6 ---
CREATE INDEX t47_b_idx ON t47 (b); ANALYZE t47;
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE b=7;
              QUERY PLAN              
--------------------------------------
 Bitmap Heap Scan on t47
   Recheck Cond: (b = 7)
   ->  Bitmap Index Scan on t47_b_idx

--- MySQL 8.4.10 ---
+-------+------+---------------+-----------+---------+-------+------+
| table | type | possible_keys | key       | key_len | ref   | rows |
+-------+------+---------------+-----------+---------+-------+------+
| t47   | ref  | t47_b_idx     | t47_b_idx |       4 | const | 2000 |
+-------+------+---------------+-----------+---------+-------+------+
```

★ **같은 10% 를 이번에는 탔다.** 그러니 1번의 `Seq Scan` 은 **선택도 때문이 아니었다.**\
**같은 문서 안의 반증**이다 — 원인을 선택도로 돌리면 틀린다.

### 2. ★ 열에 함수를 씌우면 — **죽는다. 그리고 표현식 인덱스가 살린다**

**언제 쓰나** — 대소문자 무시 검색·날짜 절단·문자열 가공으로 검색할 때. **이 편에서 새로 잰 것이다.**

정상 질의는 양쪽 다 인덱스를 탄다.

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE v = 'name000123';
                   QUERY PLAN                   
------------------------------------------------
 Index Scan using t47_v_idx on t47
   Index Cond: ((v)::text = 'name000123'::text)

--- MySQL 8.4.10 ---
+-------+------+---------------+-----------+---------+-------+------+
| table | type | possible_keys | key       | key_len | ref   | rows |
+-------+------+---------------+-----------+---------+-------+------+
| t47   | ref  | t47_v_idx     | t47_v_idx |     122 | const |    1 |
+-------+------+---------------+-----------+---------+-------+------+
```

**열에 함수를 씌우면 양쪽 다 죽는다.**

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
EXPLAIN (COSTS OFF) SELECT * FROM t47      EXPLAIN SELECT * FROM t47
  WHERE upper(v) = 'NAME000123';             WHERE upper(v) = 'NAME000123';

                QUERY PLAN                 type          : ALL
-----------------------------------------  possible_keys : NULL
 Seq Scan on t47                           key           : NULL
   Filter: (upper((v)::text) = 'NAME...')  rows          : 19803
                                           Extra         : Using where
 -> 20,000행을 전부 읽는다                   -> 20,000행을 전부 읽는다
```

두 그림의 결론 — **`possible_keys` 가 `NULL` 이다.** 비용 비교조차 안 했다.

**왜 그런가 — 그림 하나로 끝난다.**

```text
인덱스는 v 의 "원래 값" 순서로 정렬돼 있다

  name000001
  name000002
  ...
  name020000

질의가 묻는 것: upper(v) 가 'NAME000123' 인 행

  upper() 를 거친 값의 순서는 이 인덱스에 없다
        ↓
  어느 구간을 읽어야 할지 정할 수 없다
        ↓
  전부 훑고 행마다 upper() 를 계산해 비교한다
```

★ **처방은 「그 계산 결과를 정렬해 둔 인덱스」를 만드는 것**이다([46 번 3번](../46-index-definition-composite-partial-expression/)의 문법).

```text
--- PG 18.6 ---
CREATE INDEX t47_upper_idx ON t47 ((upper(v)));
ANALYZE t47;
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE upper(v) = 'NAME000123';
                      QUERY PLAN                       
-------------------------------------------------------
 Index Scan using t47_upper_idx on t47
   Index Cond: (upper((v)::text) = 'NAME000123'::text)

--- MySQL 8.4.10 ---
CREATE INDEX t47_upper_idx ON t47 ((upper(v)));
ANALYZE TABLE t47;
EXPLAIN SELECT * FROM t47 WHERE upper(v) = 'NAME000123';
+-------+------+---------------+---------------+---------+-------+------+
| table | type | possible_keys | key           | key_len | ref   | rows |
+-------+------+---------------+---------------+---------+-------+------+
| t47   | ref  | t47_upper_idx | t47_upper_idx |     123 | const |    1 |
+-------+------+---------------+---------------+---------+-------+------+
```

★ **`rows` 가 19,803 에서 1 로 돌아왔고, 같은 `((expr))` 문법이 두 엔진에서 다 통했다.**

비용 — 인덱스가 하나 더 생긴다(쓰기·공간). 그리고 **질의를 그 식과 똑같이 써야** 한다.\
`lower(v)` 인덱스는 `upper(v)` 질의에 안 쓰인다.

### 3. ★ 선택도 — **계획이 갈리는 지점을 재 봤다**

**언제 쓰나** — 「인덱스가 있는데 안 쓴다」를 만났을 때. **1·2번과 원인이 다르다.**

`r` 은 20,000행에 1..20,000 이 골고루 흩어져 있다. `WHERE r <= N` 의 `N` 을 키우며 계획을 봤다.

```text
--- PG 18.6 ---  (EXPLAIN 첫 줄만 모았다)
r <= 100    : Bitmap Heap Scan on t47
r <= 1000   : Bitmap Heap Scan on t47
r <= 3000   : Bitmap Heap Scan on t47
r <= 6000   : Bitmap Heap Scan on t47
r <= 6800   : Bitmap Heap Scan on t47
r <= 6900   : Bitmap Heap Scan on t47
r <= 7000   : Seq Scan on t47            <- ★ 여기서 갈린다
r <= 8000   : Seq Scan on t47
r <= 16000  : Seq Scan on t47
```

**경계 직전과 직후의 비용을 보면 이유가 숫자로 나온다.**

```text
--- PG 18.6 ---
EXPLAIN SELECT * FROM t47 WHERE r <= 6900;
 Bitmap Heap Scan on t47  (cost=157.76..539.01 rows=6900 width=31)
   Recheck Cond: (r <= 6900)
   ->  Bitmap Index Scan on t47_r_idx  (cost=0.00..156.04 rows=6900 width=0)

EXPLAIN SELECT * FROM t47 WHERE r <= 7000;
 Seq Scan on t47  (cost=0.00..545.00 rows=7000 width=31)
   Filter: (r <= 7000)
```

그림 해설 — **539.01 대 545.00.** 인덱스 쪽 비용이 순차 스캔 비용을 **막 넘는 지점**이 경계다.

```text
r <= 6900  ->  인덱스 539.01  <  순차 545.00   -> 인덱스를 쓴다   (34.5%)
r <= 7000  ->  인덱스 545.00 을 넘는다          -> 순차로 바꾼다   (35%)
```

**MySQL 은 더 일찍 포기한다.**

```text
--- MySQL 8.4.10 ---  (처음 쟀을 때)
r <= 5200  : type=range  key=t47_r_idx  rows=5200
r <= 5400  : type=range  key=t47_r_idx  rows=5400
r <= 5600  : type=range  key=t47_r_idx  rows=5600
r <= 5800  : type=ALL    key=NULL       rows=19730   <- ★ 여기서 갈렸다
r <= 10000 : type=ALL    key=NULL       rows=19730

--- MySQL 8.4.10 ---  (★ 제출 직전 재확인 — 경계가 한 칸 옮겨 갔다)
r <= 5800  : type=range  key=t47_r_idx  rows=5800
r <= 6000  : type=ALL    key=NULL       rows=20497   <- 이제 여기서 갈린다
r <= 10000 : type=ALL    key=NULL       rows=20497
```

★ **같은 데이터·같은 버전인데 경계가 5,600\~5,800 에서 5,800\~6,000 으로 움직였다.**\
그 사이에 한 일은 **인덱스를 둘 추가하고 `ANALYZE TABLE` 을 다시 돌린 것**뿐이다.\
`rows` 추정치도 19,730 에서 20,497 로 바뀌었다(실제는 20,000 이다 — **둘 다 추정치다**).

```text
--- MySQL 8.4.10 ---  경계 전후를 표 그대로
EXPLAIN SELECT * FROM t47 WHERE r <= 5600;
+-------+-------+---------------+-----------+---------+------+------+----------+-----------------------+
| table | type  | possible_keys | key       | key_len | ref  | rows | filtered | Extra                 |
+-------+-------+---------------+-----------+---------+------+------+----------+-----------------------+
| t47   | range | t47_r_idx     | t47_r_idx |       5 | NULL | 5600 |   100.00 | Using index condition |
+-------+-------+---------------+-----------+---------+------+------+----------+-----------------------+

EXPLAIN SELECT * FROM t47 WHERE r <= 5800;
+-------+------+---------------+------+---------+------+-------+----------+-------------+
| table | type | possible_keys | key  | key_len | ref  | rows  | filtered | Extra       |
+-------+------+---------------+------+---------+------+-------+----------+-------------+
| t47   | ALL  | t47_r_idx     | NULL |    NULL | NULL | 19730 |    29.40 | Using where |
+-------+------+---------------+------+---------+------+-------+----------+-------------+
                                  ↑ 후보에는 있다        ↑ 안 골랐다
```

★★ **이 표가 1·2번과의 결정적 차이를 보여 준다.**

```text
1·2번 (못 쓴다)   possible_keys = NULL      후보에 아예 없다
3번   (안 쓴다)   possible_keys = 인덱스    후보에 있는데 key 가 NULL 이다
                                            = 비용을 비교하고 버렸다
```

**두 엔진의 경계**

| | 경계(처음) | 경계(제출 직전) | 전체 대비 |
|---|---|---|---|
| PostgreSQL 18.6 (`r`) | 6,900 → 7,000 | **같음** | **34.5% → 35%** |
| MySQL 8.4.10 (`r`) | 5,600 → 5,800 | **5,800 → 6,000** | 28% → 29% ⇒ **29% → 30%** |
| PostgreSQL 18.6 (`k`, correlation 1) | — | 9,000 → 10,000 | **45% → 50%** |

★ **이 수치는 이 서버·이 데이터의 관찰이다.** 행 폭·페이지 수·통계·설정이 바뀌면 이동한다.\
외울 것은 숫자가 아니라 **「표의 3분의 1쯤에서 갈린다」는 자릿수**와 **왜 갈리는가**다.

**왜 갈리나 — 인덱스 접근이 공짜가 아니기 때문이다.**

```text
인덱스로 찾는다            순차로 훑는다
  인덱스를 읽고              표를 처음부터 끝까지 읽는다
  그 위치의 표를 읽는다       (연속 읽기라 빠르다)
        ↓                          ↓
  찾는 행이 적으면 이득         찾는 행이 많으면 결국 표를 거의 다 읽는데
                              흩어진 순서로 읽게 되어 더 느리다
```

### 3-b. ★ 같은 선택도인데 계획이 다르다 — **무엇을 뽑느냐도 정한다**

**언제 쓰나** — 3번의 결론을 「선택도만 보면 된다」로 굳히기 전에.

`r <= 10000` 은 **50%** 다. 3번에 따르면 순차 스캔이어야 한다. 뽑는 열만 바꿔 던졌다.

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE r <= 10000;
       QUERY PLAN       
------------------------
 Seq Scan on t47
   Filter: (r <= 10000)

EXPLAIN (COSTS OFF) SELECT r FROM t47 WHERE r <= 10000;
               QUERY PLAN               
----------------------------------------
 Index Only Scan using t47_r_idx on t47      <- ★ 50% 인데 인덱스를 탄다
   Index Cond: (r <= 10000)
```

```text
--- MySQL 8.4.10 ---
EXPLAIN SELECT * FROM t47 WHERE r <= 10000;
| t47 | ALL   | t47_r_idx | NULL      | NULL | NULL | 20462 | 48.87 | Using where |

EXPLAIN SELECT r FROM t47 WHERE r <= 10000;
| t47 | range | t47_r_idx | t47_r_idx |    5 | NULL | 10000 | 100.00| Using where; Using index |
                                                                                    ^^^^^^^^^^^^
```

그림 해설 — **`r` 만 필요하면 인덱스 안에 답이 다 있다. 표를 안 읽어도 된다.**

```text
SELECT *  ->  인덱스에서 위치를 찾고 -> 표에서 나머지 열을 읽어야 한다
              흩어진 10,000번의 표 접근 -> 비싸다 -> 순차 스캔이 이긴다

SELECT r  ->  인덱스만 읽으면 끝난다
              표 접근이 0번 -> 인덱스가 이긴다
```

> **커버링(covering)** — 질의가 필요한 열을 인덱스가 전부 갖고 있어 **표를 안 읽는** 것.\
> 예: PG 는 `Index Only Scan`, MySQL 은 `Extra: Using index` 로 표시한다.

★ **「선택도가 X% 를 넘으면 인덱스를 안 탄다」는 틀린 요약**이다.\
정하는 것은 선택도 하나가 아니라 **선택도 × 표 접근 필요 여부 × 물리적 상관**이다.

**상관(correlation)도 정한다 — `k` 와 `r` 이 그 반증이다.**

두 열은 값의 분포가 같고 **물리적 배치만 다르다.** 경계를 각각 찾았다.

```text
--- PG 18.6 ---  r : 흩어져 있다 (correlation ~ 0)
r <= 6900  : Bitmap Heap Scan on t47
r <= 7000  : Seq Scan on t47                    <- 경계 34.5% ~ 35%

--- PG 18.6 ---  k : 저장 순서 = 값 순서 (correlation = 1)
k <= 9000  : Index Scan using t47_k_idx on t47
k <= 10000 : Seq Scan on t47                    <- 경계 45% ~ 50%
```

**같은 분포인데 경계가 다르다.** 값이 정렬된 대로 저장돼 있으면 **표 접근이 연속이라 싸기** 때문에\
인덱스가 더 늦게까지 버틴다. PG 는 이 성질을 `pg_stats.correlation` 으로 갖고 있다가 비용에 반영한다.

```text
r (correlation 0)   인덱스가 짚어 주는 위치가 표 전체에 흩어져 있다 -> 임의 접근 -> 비싸다
k (correlation 1)   인덱스 순서대로 읽으면 표도 앞에서 뒤로 읽힌다  -> 연속 접근 -> 싸다
```

★ **계획 이름도 다르다.** `r` 은 `Bitmap Heap Scan`(위치를 모아 정렬한 뒤 한 번에 훑는다),\
`k` 는 `Index Scan`(하나씩 짚어 읽는다). **PG 가 상관을 보고 접근 방식까지 바꾼 것**이다.

★★ **이 자리에서 드리프트를 실제로 만났다.** 처음 쟀을 때 `k <= 10000`(50%)은 **`Index Scan`** 이었는데,\
제출 직전에 다시 찍으니 **`Seq Scan`** 이었다. 데이터도 버전도 안 바꿨고 **인덱스를 둘 추가하고 `ANALYZE` 를 다시 돌린 것**뿐이다.\
경위와 판정은 [3-answer.md](3-answer.md) 의 「실행 검증」에 적었다 — **계획을 문서에 박으면 안 되는 이유의 실물**이다.

### 4. 이미 실측된 세 자리 — **다시 재지 않고 결론만 받는다**

**언제 쓰나** — 나머지 대표적인 「못 타는」 자리들. **세 편이 이미 같은 방법으로 쟀다.**

**(1) 암시 타입 변환 — [35 타입 체계와 캐스팅 3번](../35-type-system-and-casting/)**

```text
varchar 열 = 정수 리터럴   ->  PG   : ERROR (그런 연산자가 없다). 문이 서지 않는다
                               MySQL: 돈다. type 이 index 로 내려가고 rows 1 -> 19905
                                      ★ 경고 1739 가 "인덱스 접근을 포기했다" 고 말한다
                               그리고 결과가 0행이다 — 느린 것보다 나쁘다
```

**결론만 받는다** — **열 쪽이 변하면 죽고 값 쪽만 변하면 산다.**\
`int` 열 = `bigint` 값은 **인덱스를 탄다**(거기서 실측했다).

**(2) 앞이 열린 `LIKE` — [38 패턴 매칭 5번](../38-pattern-matching-like-regex/)**

```text
LIKE 'C00012%'  ->  MySQL: type=range, rows 10
                    PG   : ★ 기본 인덱스로는 Seq Scan (collate 가 en_US.utf8 이라서)
                           varchar_pattern_ops 인덱스를 따로 만들면 Index Scan

LIKE '%00123'   ->  양쪽 다 전부 훑는다. MySQL 의 possible_keys 가 NULL 이다
```

**결론만 받는다** — **앞이 고정된 패턴만 구간이 된다.** `LIKE '%x'` 는 어느 엔진에서도 못 탄다.\
그리고 **PG 에서는 앞이 고정돼도 collation 때문에 못 타는 경우가 있다.**

**(3) collation 불일치 — [39 collation 6번](../39-collation/)**

```text
WHERE code = 'C000123'                     ->  PG: Index Scan   / MySQL: type=ref
WHERE code COLLATE "C" = 'C000123'         ->  PG: ★ Seq Scan
WHERE code = 'C000123' COLLATE utf8mb4_bin ->  MySQL: ★ ref -> range + 경고 1739
```

**결론만 받는다** — **collation 은 인덱스의 일부다.** 질의가 다른 정렬 규칙을 요구하면 그 인덱스는 쓸모가 없다.

★ **세 편과 이 편을 한 문장이 관통한다.**

```text
인덱스는 "그 열의 원래 값을, 그 collation 순서로" 정렬해 둔 것이다
        ↓
열에 손을 대면(함수·암시 변환·COLLATE) 그 정렬은 쓸모가 없어진다
        ↓
처방은 언제나 "열을 건드리지 말고 값 쪽을 맞춘다" 이거나
             "그 변형 결과를 정렬해 둔 인덱스를 따로 만든다"
```

## 문법 — 어느 절에서 무엇이 보이나

SQL 의 실행 계획은 **문법이 아니라 읽는 법**이 본체다.

```sql
-- PostgreSQL
EXPLAIN SELECT ...;                        -- 계획 + 추정 비용
EXPLAIN (COSTS OFF) SELECT ...;            -- 비용 칸을 빼고 구조만 (문서에 싣기 좋다)
EXPLAIN (ANALYZE) SELECT ...;              -- ★ 실제로 실행하고 실측을 같이 보여 준다
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;     -- 읽은 블록 수까지

-- MySQL
EXPLAIN SELECT ...;                        -- 표 형태
EXPLAIN FORMAT=JSON SELECT ...;            -- 비용까지
EXPLAIN ANALYZE SELECT ...;                -- ★ 실제로 실행한다
SHOW WARNINGS;                             -- ★ 인덱스를 포기한 이유가 여기 나온다 (경고 1739)
```

★ **`EXPLAIN ANALYZE` 는 질의를 실제로 실행한다.** `UPDATE`·`DELETE` 에 쓰면 **데이터가 바뀐다.**\
(이 문서의 계획은 전부 `SELECT` 에 대한 **비실행 `EXPLAIN`** 이다.)

**읽는 순서**

```text
PG                                MySQL
1. 맨 위 노드가 무엇인가           1. type    — ALL 이면 전부 훑는다
   Seq Scan / Index Scan /            const < eq_ref < ref < range < index < ALL
   Index Only Scan / Bitmap ...   2. possible_keys — NULL 이면 "못 쓴다"
2. Index Cond 대 Filter           3. key     — NULL 인데 possible_keys 가 있으면 "안 쓴다"
   Index Cond : 인덱스로 좁혔다     4. key_len — 복합 인덱스의 몇 칸을 썼나
   Filter     : 읽은 뒤 버렸다     5. rows    — 추정 행 수
3. rows= 는 추정치다               6. Extra   — Using index(커버링) · Using where · Using filesort
```

## 어디서 틀리나

1. **「인덱스가 있으니 탈 것이다」.** 두 종류의 이유로 안 탄다 — **못 쓰거나, 안 쓰거나**(1\~3번).
2. **`Seq Scan`·`type: ALL` 을 보고 곧장 「인덱스를 추가해야겠다」로 간다.**\
   **`possible_keys` 를 먼저 본다.** 후보에 있는데 안 골랐다면 **인덱스를 더 만들어도 소용없다**(3번).
3. **선택도만으로 판단한다.** 뽑는 열과 물리적 상관도 정한다(3-b번).\
   같은 50% 가 `SELECT *` 면 순차, `SELECT r` 이면 인덱스였다.
4. **`b=7` 이 안 타는 것을 「10% 라서」로 설명한다.** 틀렸다 —\
   **`b` 전용 인덱스를 만들면 같은 10% 를 탄다**(1번의 반증).
5. **열에 함수를 씌운다.** `WHERE upper(v)=...`·`WHERE date(ts)=...`·`WHERE id+0=...` 전부 죽는다(2번).
6. **표현식 인덱스를 만들고 질의를 다른 식으로 쓴다.** `lower(v)` 인덱스는 `upper(v)` 에 안 쓰인다(2번).
7. **`key_len` 을 안 본다.** `(a,b)` 인덱스를 「탔다」고 안심했는데 `key_len` 이 4 면 **앞 한 칸만 쓴 것**이다(1번).
8. **`rows` 를 실제 행 수로 읽는다.** 추정치다. 실측은 `EXPLAIN ANALYZE` 로 봐야 한다.
9. ★ **계획을 한 번 찍고 「이 질의는 인덱스를 탄다」로 문서에 박는다.**\
   **계획은 그 순간의 통계·설정이 정한 것**이다. 데이터가 늘면 바뀐다.
10. **MySQL 에서 `EXPLAIN` 만 보고 `SHOW WARNINGS` 를 안 친다.**\
    타입·collation 때문에 포기한 경우 **이유가 경고에만 있다**([35](../35-type-system-and-casting/)·[39](../39-collation/)번).

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| 질의의 **결과** | 인덱스가 있든 없든 같다 | — |
| 인덱스 사용 여부 | — | **전부 옵티마이저가 정한다** |
| 선택도 경계 | — | **비용 모델·통계·설정**(PG 34.5% / MySQL 28%) |
| 계획의 이름 | — | `Bitmap Heap Scan`·`Index Only Scan` 은 **PG 고유** |
| 함수 적용 시 인덱스 포기 | — | 두 엔진이 같았지만 **보장이 아니라 관찰**이다 |

★★ **이 주제 전체가 「구현이 정하는 것」 쪽에 있다.**\
SQL 이 보장하는 것은 **결과**이지 **방법**이 아니다. 그래서 이 편의 모든 출력은 **관찰**이다.

- **`rows` 는 추정치다.** 3번의 `rows=19730` 은 실제 20,000 과 다르다.
- **선택도 경계 수치는 이 서버의 값**이다. 다른 머신·다른 데이터에서 그대로 나오지 않는다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 고치기 전에 `EXPLAIN` 을 먼저.** 어느 종류의 문제인지(`possible_keys`)부터 가른다.
- **쓴다 — 열을 건드리지 않는 질의.** 값 쪽을 열의 타입·collation 에 맞춘다.
- **쓴다 — 꼭 변형해야 하면 표현식 인덱스.** `((expr))` 로 만들고 **질의도 똑같은 식**으로 쓴다(2번).
- **쓴다 — 커버링.** 필요한 열이 적으면 인덱스에 다 넣어 표 접근을 없앤다(3-b번, [46 번 7번](../46-index-definition-composite-partial-expression/)).
- **안 쓴다 — 선택도가 낮은 조건에 인덱스를 기대하는 것.** 표의 3분의 1이면 순차가 이긴다(3번).
- **안 쓴다 — `possible_keys` 에 이미 있는데 안 골라진 상황에서 인덱스 추가.** 원인이 다르다.
- **조심한다 — 개발 DB 의 계획.** 행 수가 적으면 **인덱스가 있어도 순차가 뽑힌다.** 운영과 다르다.
- **조심한다 — 계획을 문서에 박는 것.** 제출 직전에 다시 찍고, 바뀌었으면 그 사실을 적는다.

## 핵심 문장

- **인덱스가 안 쓰이는 이유는 둘뿐이다 — 못 쓰거나(`possible_keys: NULL`), 안 쓰거나(`key: NULL`).**
- **열에 함수를 씌우면 죽는다.** 인덱스는 **원래 값**의 순서이기 때문이다.
- **표현식 인덱스가 살린다.** `((expr))` 로 만들고 **질의도 똑같은 식**으로 쓴다.
- **선택도 경계는 이 서버에서 PG 34.5%, MySQL 28\~30% 였다** — ★ **자릿수만 기억한다. 제출 직전에 이미 움직였다.**
- **선택도만으로 정해지지 않는다.** 같은 50% 가 `SELECT *` 면 순차, `SELECT r` 이면 인덱스였다.
- **`key_len` 이 복합 인덱스를 몇 칸까지 썼는지 알려 준다.** 「탔다」와 「제대로 탔다」는 다르다.
- **암시 변환·앞이 열린 `LIKE`·collation 불일치는 [35](../35-type-system-and-casting/)·[38](../38-pattern-matching-like-regex/)·[39](../39-collation/) 번이 이미 실측했다** — 결론은 하나다: **열을 건드리지 마라.**
- ★ **계획은 관찰이지 보장이 아니다** — ★ **이 편을 쓰는 동안 실제로 두 자리가 움직였다**(3번·3-b번).\
  데이터도 버전도 안 바꿨고 인덱스를 둘 추가하고 통계를 다시 모았을 뿐이다.

## 관련 자료

- [`data-structure/15-b-tree`](../../../../../data-structure/15-b-tree/) — ★ **그쪽은 탐색 구조가 어떻게 생겼고 어떻게 찾나까지,\
  여기는 「그 구조를 쓸지 말지를 엔진이 어떻게 정하나」부터.** 노드·분할·높이는 한 줄도 여기서 다루지 않는다.
- [46 인덱스 정의](../46-index-definition-composite-partial-expression/) — ★ **「어떻게 정의하나」는 전부 거기다.** 여기는 정의된 것이 쓰이는지만 본다.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — ★ **암시 변환이 인덱스를 죽이는 실측은 거기가 정본**이다. 4번에서 결론만 받았다.
- [38 패턴 매칭 — LIKE·정규식](../38-pattern-matching-like-regex/) — ★ **앞이 열린 `LIKE` 의 실측은 거기가 정본**이다.
- [39 collation](../39-collation/) — ★ **collation 불일치의 실측은 거기가 정본**이다.
- [42 테이블 정의와 변경](../42-create-alter-drop-table/) · [44 외래키](../44-foreign-key-referential-actions/) — 44 번 9번의 「FK 열 인덱스가 없으면 느려진다」가 이 편의 판단으로 이어진다.
- [09 LIMIT·OFFSET·키셋 페이지네이션](../09-limit-offset-keyset-pagination/) — 깊은 `OFFSET` 이 느린 것도 같은 종류의 이야기다.
- [SQL 주제 목록](../README.md) — 58(EXPLAIN 읽기) · 60(통계와 추정) 이 이웃이다.

## 용어 풀이

- **실행 계획(execution plan)** — 엔진이 질의를 **어떻게 처리하기로 정했는지**의 설명.\
  예: `EXPLAIN` 이 보여 준다. 그 순간의 통계가 정한 것이라 **보장이 아니다.**
- **선택도(selectivity)** — 조건에 맞는 행이 전체에서 차지하는 비율.\
  예: 20,000행 중 10행이면 0.05%, 7,000행이면 35%.
- **`Seq Scan` / `type: ALL`** — 표를 처음부터 끝까지 읽는 것.\
  예: 찾는 행이 많으면 이쪽이 더 싸다.
- **`Index Scan` / `type: ref`·`range`** — 인덱스로 위치를 짚어 읽는 것.\
  예: `ref` 는 한 값을, `range` 는 구간을 짚는다.
- **`Index Only Scan` / `Extra: Using index`** — 인덱스만 읽고 **표를 안 읽는** 것(커버링).\
  예: `SELECT r FROM t WHERE r<=N` 은 `r` 인덱스만으로 답이 나온다.
- **`Bitmap Heap Scan`(PG)** — 인덱스로 읽을 행의 위치를 모아 **정렬한 뒤** 표를 한 번에 훑는 방식.\
  예: 흩어진 행을 많이 읽어야 할 때 `Index Scan` 보다 싸다.
- **`possible_keys`(MySQL)** — 옵티마이저가 **후보로 고려한** 인덱스 목록.\
  예: `NULL` 이면 그 질의로는 **어떤 인덱스도 쓸 수 없다**는 뜻이다.
- **`key`(MySQL)** — 실제로 **고른** 인덱스. `possible_keys` 는 있는데 `key` 가 `NULL` 이면 **비용으로 버린 것**이다.
- **`key_len`(MySQL)** — 인덱스에서 **실제로 쓴 바이트 수**. 복합 인덱스를 몇 칸까지 썼는지 알려 준다.\
  예: `int` 두 칸을 다 쓰면 8, 앞 한 칸만 쓰면 4.
- **`Index Cond` 대 `Filter`(PG)** — 전자는 인덱스로 **좁힌** 조건, 후자는 읽은 뒤 **버린** 조건.\
  예: `Filter` 에만 조건이 있으면 그 조건은 읽는 양을 줄이지 못했다.
- **표현식 인덱스(expression index)** — 열 값이 아니라 계산 결과를 정렬해 둔 인덱스.\
  예: `((upper(v)))` 를 만들면 `WHERE upper(v)='X'` 가 인덱스를 탄다.
- **상관(correlation)** — 열 값의 순서와 물리적 저장 순서가 얼마나 일치하는가.\
  예: `1` 이면 완전히 같고 `0` 이면 무관하다. PG 의 `pg_stats.correlation` 으로 본다.
- **경고 1739** — MySQL 이 **타입·collation 변환 때문에 인덱스 접근을 포기했다**고 알리는 경고.\
  예: `SHOW WARNINGS` 로만 보인다([35](../35-type-system-and-casting/)·[39](../39-collation/)번).

## 더 들어가면

- **`EXPLAIN ANALYZE` 는 추정과 실측을 나란히 보여 준다.** 추정이 크게 틀렸으면 **통계가 낡은 것**이다.\
  이 문서의 계획은 전부 `ANALYZE`/`ANALYZE TABLE` 직후에 찍었으므로 그 오차를 줄인 상태다.\
  **`EXPLAIN ANALYZE` 자체는 이 실험에서 쓰지 않았다** — 비실행 `EXPLAIN` 만 실었다.
- **인덱스가 실제로 쓰이는지는 계획이 아니라 누적 통계로 본다.**\
  PG 는 `pg_stat_user_indexes.idx_scan`, MySQL 은 `performance_schema` 의 인덱스 통계다.\
  **이 실험에서 그 누적 통계를 읽어 보지는 않았다.**
- **옵티마이저를 강제하는 수단이 양쪽에 있다** — MySQL 의 `FORCE INDEX`, PG 의 `enable_seqscan=off`.\
  **진단용이지 처방이 아니다.** 강제해서 빨라졌다면 통계나 비용 설정이 틀렸다는 신호다.\
  **이 실험에서는 강제하지 않았다** — 강제하면 「엔진이 무엇을 고르나」를 못 보게 된다.
- **인덱스가 많을수록 옵티마이저의 선택지가 늘고, 잘못 고를 여지도 는다.**\
  [46 번 16번](../46-index-definition-composite-partial-expression/)의 「무엇을 안 만드나」와 이어진다.
