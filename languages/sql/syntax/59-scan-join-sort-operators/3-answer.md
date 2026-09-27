# sql/59-스캔·조인·정렬 연산자 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 계획은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 계획은 없다.\
> **측정 조건** — `study` 안에 만든 `t59_big`(20만 행) · `t59_mid`(5만 행) · `t59_small`(10행).\
> PG 계획은 전부 **`max_parallel_workers_per_gather = 0`**(병렬 끔)에서, **한 트랜잭션 안에서 한 번에** 찍었다 —
> `ANALYZE` 의 표본이 판마다 달라 숫자가 흔들리기 때문이다(6·7번).\
> PG 는 `BEGIN … ROLLBACK`, MySQL 은 `DROP TABLE IF EXISTS` 로 지웠다. **`emp`·`dept` 는 건드리지 않았다.**\
> 문서 근거는 [PG 18 Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) · [MySQL 8.4 EXPLAIN Join Types](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html#explain-join-types) · [MySQL 8.4 Hash Join](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html).

> **표 테두리를 지웠다.** 이 파일의 MySQL `EXPLAIN` 블록은 12칸 표에서 그 절에 필요 없는 칸과
> `+---+` 테두리를 지운 것이다. **남긴 칸의 값은 원본 그대로다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `Seq Scan` · `Index Scan` · `Index Only Scan` · `Bitmap` — 마지막은 PG 에만 있다

**왜 그런가** — 엔진이 표의 행에 닿는 길은 「인덱스를 쓰나」와 「표를 펴야 하나」 두 갈림으로 나뉜다.

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
                                            (바로 그 자리로)     (자리를 모아 한 번에 · PG 만)
```

| PostgreSQL 18.6 | MySQL 8.4.10 의 대응 |
|---|---|
| `Seq Scan` | `type=ALL` |
| `Index Scan` | `type=const` · `eq_ref` · `ref` · `range` |
| `Index Only Scan` | `Extra: Using index` (접근 타입은 그대로) |
| **`Bitmap Heap Scan` + `Bitmap Index Scan`** | **없다** |

**MySQL 에는 비트맵 스캔이 없다.** 이 차이가 4·5번의 전환점 차이를 만든다.

---

### 2. PG 는 `Bitmap Heap Scan`, MySQL 은 `type=ref`

**출력**

```text
### SQL: EXPLAIN SELECT * FROM t59_big WHERE grp = 7;
--- PG 18.6 ---
 Bitmap Heap Scan on t59_big  (cost=5.84..576.81 rows=199 width=33)
   Recheck Cond: (grp = 7)
   ->  Bitmap Index Scan on t59_big_grp  (cost=0.00..5.79 rows=199 width=0)
         Index Cond: (grp = 7)
--- MySQL 8.4.10 ---
| table   | type | key   | rows | Extra |
| t59_big | ref  | k_grp |  200 | NULL  |
```

**왜 그런가** — 200행은 20만 행 중 0.1% 다. **인덱스가 압도적으로 싸다.** 문제는 「그 200행을 어떻게 가져오나」다.

```text
 Index Scan (MySQL 의 ref 와 같은 성격)   Bitmap Heap Scan (PG)
 인덱스 -> 표 -> 인덱스 -> 표 -> …        인덱스를 끝까지 -> 자리 비트맵 -> 표를 앞에서 뒤로 한 번
   페이지를 널뛰며 200번 오간다             페이지 순서대로 읽는다
```

`Bitmap Index Scan` 이 **맞는 행의 자리를 먼저 다 모으고**, `Bitmap Heap Scan` 이 그 자리를 **표 순서대로** 읽는다.\
`Recheck Cond` 는 비트맵이 페이지 단위로 뭉개졌을 때를 대비한 재확인이라 **조건이 두 번 적힌다.**

**추정 행 수도 봐 둔다** — PG `rows=199`, MySQL `rows=200`. 실제는 200행이다. 이 조건에서는 둘 다 잘 맞혔다.

---

### 3. `Seq Scan` / `type=ALL` — MySQL 은 `possible_keys` 에 후보가 있는데 `key=NULL` 이다

**출력**

```text
### SQL: EXPLAIN SELECT * FROM t59_big WHERE grp < 900;
--- PG 18.6 ---
 Seq Scan on t59_big  (cost=0.00..4228.00 rows=180101 width=33)
   Filter: (grp < 900)
--- MySQL 8.4.10 ---
| table   | type | possible_keys | key  | rows   | filtered | Extra       |
| t59_big | ALL  | k_grp         | NULL | 199699 |    50.00 | Using where |
```

**왜 그런가** — 18만 행을 가져올 거면 **인덱스를 타는 게 손해다.**

```text
 인덱스로 18만 행 가져오기              표를 통째로 훑기
 +---------------------------+        +---------------------------+
 | 인덱스도 다 읽고            |        | 표만 순서대로 읽는다        |
 | 표의 페이지도 거의 다 읽는다 |        | 페이지를 두 번 안 읽는다     |
 | 게다가 순서가 뒤섞인다       |        |                           |
 +---------------------------+        +---------------------------+
   -> 일이 더 많다
```

★ **`possible_keys=k_grp` 인데 `key=NULL`** — **쓸 수 있었는데 안 썼다**는 뜻이다.

```text
 possible_keys=NULL, key=NULL       possible_keys=k_grp, key=NULL
 후보 인덱스가 아예 없다              후보는 있는데 안 골랐다
   -> 처방: 인덱스를 만든다             -> 처방: 없다. 이게 맞는 선택이다
                                       (조건을 좁히는 것이 처방이다)
```

**이 두 칸을 나눠 읽지 않으면 「인덱스를 걸었는데 왜 안 타지」에서 헛돈다.**

`filtered=50.00` 은 「읽은 행의 50% 가 조건을 통과할 것」이라는 추정이다. 실제로는 90% 다 — 추정이 틀렸다(60번).

---

### 4. PG 는 약 52%, MySQL 은 약 30% 에서 갈렸다

**출력**

```text
--- PG 18.6 (한 트랜잭션 · 병렬 끔) ---
grp < 50     Bitmap Heap Scan  (cost=112.62..1963.72 rows=9848)       5%
grp < 200    Bitmap Heap Scan  (cost=439.47..2656.47 rows=39120)    20%
grp < 520    Bitmap Heap Scan  (cost=1146.04..4160.73 rows=102935)  51%   <- 경계 (6·7번)
grp < 540    Seq Scan          (cost=0.00..4228.00 rows=107169)     54%   <- 갈렸다
grp < 900    Seq Scan          (cost=0.00..4228.00 rows=180101)     90%
```

```text
--- MySQL 8.4.10 ---
grp = 7      type=ref    key=k_grp   rows=200                        0.1%
grp < 50     type=range  key=k_grp   rows=19720                     10%
grp < 120    type=range  key=k_grp   rows=47136                     24%
grp < 140    type=range  key=k_grp   rows=55890                     28%
grp < 150    type=ALL    key=NULL    rows=199699 filtered=31.18     30%   <- 갈렸다
grp < 200    type=ALL    key=NULL    rows=199699 filtered=43.04     40%
```

**왜 그런가** — 판단은 비용 한 줄로 끝난다.

```text
Seq Scan 의 비용은 조건과 무관하게 언제나 cost=0.00..4228.00   (표를 다 읽는 값)
Bitmap 의 비용은 읽을 행 수에 비례해 는다:
   grp < 50    ->  1963.72  <  4228.00   -> Bitmap
   grp < 200   ->  2656.47  <  4228.00   -> Bitmap
   grp < 520   ->  4160.73  <  4228.00   -> Bitmap  (아슬아슬하다 — 6·7번)
   그 선을 넘는 순간 Seq Scan 으로 넘어간다
```

★ **전환점의 % 는 이 데이터·이 표 폭의 값이다.** 행이 좁아지면(페이지당 행이 늘면) `Seq Scan` 이 싸져 전환점이 앞당겨지고,\
행이 넓어지면 뒤로 밀린다. **외울 것은 숫자가 아니라 「% 로 갈린다」는 성질이다.**

---

### 5. PostgreSQL 에는 비트맵이라는 중간 도구가 있다

**왜 그런가**

```text
 PostgreSQL                             MySQL 8.4.10
 +-----------------------------+       +-----------------------------+
 | 인덱스로 자리를 다 모은 뒤    |       | 인덱스로 찾은 행을           |
 | 표를 앞에서 뒤로 한 번 읽는다  |       | 그때그때 표에서 읽는다        |
 | -> 랜덤 접근이 순차로 바뀐다  |       | -> 랜덤 접근 그대로           |
 | -> 많이 읽어도 덜 비싸다      |       | -> 많이 읽으면 급격히 비싸진다 |
 +-----------------------------+       +-----------------------------+
   약 52% 까지 버틴다                     약 30% 에서 포기한다
```

**인덱스로 많은 행을 가져올 때의 진짜 비용은 「인덱스를 읽는 값」이 아니라 「표를 널뛰며 읽는 값**」이다.\
비트맵은 그 널뛰기를 순서대로 읽기로 바꿔 준다. 그 도구가 없으면 더 일찍 포기하는 게 맞다.

★ **그래서 「PG 에서는 인덱스를 타던 질의가 MySQL 에서는 안 탄다」가 정상일 수 있다.**\
엔진을 옮길 때 계획을 그대로 기대하면 안 되는 이유가 이것이다.

---

### 6. `Bitmap` 4판 · `Seq Scan` 4판 — 반반으로 갈렸다

**출력**

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

**왜 그런가** — 같은 서버·같은 버전·같은 생성 코드인데 **연산자가 4:4 로 갈렸다.**

```text
 바뀐 것                                안 바뀐 것
 +---------------------------+         +---------------------------+
 | 연산자: Bitmap 4 / Seq 4   |         | 데이터 (같은 생성 코드)     |
 | 추정 행 수 103,398~104,967 |         | 버전 (PG 18.6)            |
 | Bitmap 총비용 4174~4186    |         | Seq Scan 비용 4228.00     |
 +---------------------------+         +---------------------------+
```

`Bitmap` 의 총비용이 `Seq Scan` 의 **4228.00 바로 아래를 오간다.** 추정이 조금만 커지면 그 선을 넘고, 연산자가 뒤집힌다.

**전환점에서 먼 자리는 안 흔들렸다** — `grp < 50` 은 8판 내내 `Bitmap`, `grp < 900` 은 내내 `Seq Scan` 이었다.\
**흔들리는 것은 경계다.**

---

### 7. `ANALYZE` 의 표본이 판마다 다르다 — 근거로는 흔들리지 않는 칸을 쓴다

**왜 그런가** — `ANALYZE` 는 표를 **전수 세지 않는다.** 일부 페이지를 표본으로 뽑아 추정한다.

```text
 ANALYZE 판1                           ANALYZE 판4
 표본 페이지 A, C, F, …                표본 페이지 B, C, G, …
        ↓                                     ↓
 grp<520 이 103,398행일 것            grp<520 이 104,967행일 것
        ↓                                     ↓
 Bitmap 총비용 4174.10 < 4228.00     Bitmap 총비용이 4228.00 을 넘는다
        ↓                                     ↓
 Bitmap Heap Scan                     Seq Scan
```

추정 폭은 103,398~104,967 — **약 1.5% 다.** 그 1.5% 가 경계에서는 연산자를 뒤집는다.

```text
 흔들리는 칸 (근거로 쓰지 않는다)        흔들리지 않는 칸 (근거로 쓴다)
 +---------------------------+        +---------------------------+
 | rows= (추정치)             |        | actual rows= (EXPLAIN ANALYZE) |
 | cost= 의 소수점            |        | Index Cond / Filter        |
 | actual time=              |        | 연산자 이름                 |
 | 경계 근처의 연산자 선택     |        | loops=                     |
 +---------------------------+        +---------------------------+
```

★ **그래서 「이 질의는 비트맵 스캔을 쓴다」고 적으면 안 된다.**\
「이 데이터·이 통계에서 비용이 이렇게 나왔고, 그래서 비트맵이 뽑혔다」로 적는다.\
[19번](../19-semi-anti-join/)에 같은 성격의 MySQL 실측이 있고, [09번](../09-limit-offset-keyset-pagination/)은 처음부터 `actual rows` 만 근거로 썼다.

**처방도 달라진다** — 경계 위에 있는 질의는 **경계에서 떨어뜨리는 것**이 처방이다(조건을 좁히거나 커버링 인덱스를 만든다).\
경계 위에서 「오늘은 빠르네」를 확인하는 것은 아무 보장도 되지 않는다.

---

### 8. `Using index` — PostgreSQL 에서는 `Index Only Scan` 이다

**출력**

```text
### SQL: EXPLAIN SELECT grp FROM t59_big WHERE grp = 7;
--- MySQL 8.4.10 ---
| table   | type | key   | rows | Extra       |
| t59_big | ref  | k_grp |  200 | Using index |

### SQL: EXPLAIN SELECT id FROM t59_big ORDER BY id LIMIT 5;
--- PG 18.6 ---
 Limit  (cost=0.42..0.59 rows=5 width=4)
   ->  Index Only Scan using t59_big_pkey on t59_big  (cost=0.42..6935.42 rows=200000 width=4)
```

**왜 그런가** — **필요한 열이 전부 인덱스 안에 있으면 표를 펼 이유가 없다.**

```text
 보통의 인덱스 접근                    커버링
 인덱스에서 자리를 찾고                인덱스에서 값을 읽고
        ↓                                  ↓
 표의 그 페이지를 읽는다                끝. 표를 안 읽는다
 (읽는 페이지: 인덱스 + 표)            (읽는 페이지: 인덱스만)
```

- **MySQL** — 접근 타입(`type`)은 그대로 두고 `Extra` 에 `Using index` 를 붙인다.
- **PostgreSQL** — 아예 **노드 이름**이 `Index Only Scan` 이 된다.

이것을 **커버링 인덱스**라 부르고, 인덱스 설계의 목표 중 하나다([46 인덱스 정의](../46-index-definition-composite-partial-expression/)).\
대가는 **인덱스가 커진다**는 것이다 — 열을 더 담았으니 쓰기와 저장이 비싸진다.

> ⚠️ **MySQL 의 `Using index` 와 `Using index condition` 은 다른 말이다.**\
> 전자는 **표를 안 읽는다**(커버링), 후자는 **조건을 인덱스 단계에서 먼저 거르고 표는 읽는다**(3·4번의 `range` 줄).

---

### 9. 10행이면 `Merge Join`, 50,000행이면 `Hash Join`

**출력**

```text
### SQL: EXPLAIN SELECT s.id, b.pad FROM t59_small s JOIN t59_big b ON b.id = s.ref;   -- (A)
--- PG 18.6 ---
 Merge Join  (cost=1.71..2.95 rows=10 width=25)
   Merge Cond: (b.id = s.ref)
   ->  Index Scan using t59_big_pkey on t59_big b  (cost=0.42..6935.42 rows=200000 width=25)
   ->  Sort  (cost=1.27..1.29 rows=10 width=8)
         Sort Key: s.ref
         ->  Seq Scan on t59_small s  (cost=0.00..1.10 rows=10 width=8)

### SQL: EXPLAIN SELECT m.id, b.pad FROM t59_mid m JOIN t59_big b ON b.id = m.ref;     -- (B)
--- PG 18.6 ---
 Hash Join  (cost=1445.00..6423.00 rows=50000 width=25)
   Hash Cond: (b.id = m.ref)
   ->  Seq Scan on t59_big b  (cost=0.00..3728.00 rows=200000 width=25)
   ->  Hash  (cost=820.00..820.00 rows=50000 width=8)
         ->  Seq Scan on t59_mid m  (cost=0.00..820.00 rows=50000 width=8)
```

**왜 그런가** — 질의 모양도, 안쪽 표도, 인덱스도 같다. **바깥 표의 크기만 바꿨는데 연산자가 갈렸다.**

```text
 (A) 바깥 10행                          (B) 바깥 50,000행
 +-----------------------------+       +-----------------------------+
 | 10행을 정렬하는 값: 1.29      |       | 5만 행을 인덱스로 5만 번 찾기  |
 | 기본키 순서로 지퍼 올리기      |       |  -> 비싸다                  |
 | 총 2.95                      |       | 차라리 20만 행을 한 번 훑고   |
 |                              |       | 5만 행을 해시 표로            |
 |                              |       | 총 6423.00                  |
 +-----------------------------+       +-----------------------------+
```

★ **작은 표 하나를 붙일 때 값싼 방법은 「안쪽을 통째로 읽지 않는 것**」이다 —\
(A)에서 `t59_big` 의 `Index Scan` 전체 비용이 6935.42 인데 `Merge Join` 전체가 2.95 다.\
**머지 조인은 한쪽이 끝나면 멈춘다** — 10행짜리 입력이 먼저 끝나므로 20만 행을 다 안 읽는다.

---

### 10. 안쪽 전체 비용 × 바깥 행 수 + 바깥 비용

**출력**

```text
### SQL: SET enable_mergejoin = off;  EXPLAIN SELECT s.id, b.pad FROM t59_small s JOIN t59_big b ON b.id = s.ref;
--- PG 18.6 ---
 Nested Loop  (cost=0.42..85.48 rows=10 width=25)
   ->  Seq Scan on t59_small s  (cost=0.00..1.10 rows=10 width=8)
   ->  Index Scan using t59_big_pkey on t59_big b  (cost=0.42..8.44 rows=1 width=25)
         Index Cond: (id = s.ref)
```

**왜 그런가** — 계획 안의 숫자로 그대로 맞아떨어진다.

```text
 안쪽 Index Scan 의 전체 비용   8.44
 바깥 Seq Scan 의 행 수         10       ->  8.44 × 10 = 84.4
 바깥 Seq Scan 의 전체 비용     1.10     ->  84.4 + 1.10 = 85.50 ≈ 85.48
```

*(직접 계산한 값이다. 계획에 적힌 85.48 과 0.02 차이는 반올림 표기 때문으로 보인다 — 이 계획만으로는 단정하지 않는다.)*

★ **이것이 중첩 루프의 성질이다 — 안쪽 비용이 바깥 행 수에 곱해진다.**\
바깥이 50,000행이면 같은 계획이 이렇게 된다.

```text
### SQL: SET enable_mergejoin=off; SET enable_hashjoin=off;  EXPLAIN (바깥 50,000행)
--- PG 18.6 ---
 Nested Loop  (cost=0.42..31811.00 rows=50000 width=25)
   ->  Seq Scan on t59_mid m  (cost=0.00..820.00 rows=50000 width=8)
   ->  Index Scan using t59_big_pkey on t59_big b  (cost=0.42..0.62 rows=1 width=25)
         Index Cond: (id = m.ref)
```

2.95 → 85.48 → 31811.00. **바깥이 커질수록 중첩 루프만 혼자 뛴다.**\
그래서 9번(B)에서 해시 조인(6423.00)이 이긴 것이다.

> `enable_mergejoin = off` 는 **실험용**이다. 금지가 아니라 벌점이고, 운영 설정으로 쓰지 않는다.

---

### 11. `Merge Join` 이고, **`Sort` 노드가 없다**

**출력**

```text
### SQL: EXPLAIN SELECT b.id, m.ref FROM t59_big b JOIN t59_mid m ON m.id = b.id;
--- PG 18.6 ---
 Merge Join  (cost=1.38..4114.72 rows=50000 width=8)
   Merge Cond: (b.id = m.id)
   ->  Index Only Scan using t59_big_pkey on t59_big b  (cost=0.42..6935.42 rows=200000 width=4)
   ->  Index Scan using t59_mid_pkey on t59_mid m  (cost=0.29..1629.29 rows=50000 width=8)
```

**왜 그런가** — **양쪽을 인덱스 순서로 읽으니 이미 정렬돼 있다.** 정렬이 공짜다.

```text
 9번 (B) : b.id = m.ref                 11번 : b.id = m.id
 +-----------------------------+       +-----------------------------+
 | m.ref 에는 인덱스가 없다      |       | 양쪽 다 기본키               |
 | -> 정렬하려면 5만 행을 정렬    |       | -> 인덱스 순서가 곧 정렬 순서 |
 | -> 해시가 낫다 (6423.00)      |       | -> 머지가 낫다 (4128.59)     |
 +-----------------------------+       +-----------------------------+
```

9번과 11번은 **같은 두 표, 같은 5만 행짜리 조인**이다. 다른 것은 **조인 키에 인덱스가 있느냐** 하나뿐이고,\
그 하나로 연산자가 바뀌었다.

★ **`Sort` 노드가 없다는 것이 머지 조인이 싸진 이유**다. 9번(A)에는 `Sort` 가 있었다(10행짜리라 값이 1.29 였을 뿐).

---

### 12. 5만 행짜리다 — 해시 표는 작은 쪽으로 만든다

**출력**

```text
### SQL: EXPLAIN SELECT count(*) FROM t59_mid m JOIN t59_big b ON b.val = m.val;
--- PG 18.6 ---
 Aggregate  (cost=8418.96..8418.97 rows=1 width=8)
   ->  Hash Join  (cost=1445.00..7919.77 rows=199677 width=0)
         Hash Cond: (b.val = m.val)
         ->  Seq Scan on t59_big b  (cost=0.00..3728.00 rows=200000 width=4)
         ->  Hash  (cost=820.00..820.00 rows=50000 width=4)
               ->  Seq Scan on t59_mid m  (cost=0.00..820.00 rows=50000 width=4)
```

**왜 그런가**

```text
 Hash Join
   ├ 프로브(probe) 쪽 : t59_big   200,000행   <- 한 행씩 흘려 보낸다
   └ Hash              t59_mid     50,000행   <- 통째로 메모리에 올린다
```

**해시 표는 메모리에 다 올려야 한다.** 그래서 **작은 쪽**으로 만든다 — 20만 행을 올리는 것보다 5만 행이 싸다.\
큰 쪽은 한 행씩 흘려 보내며 조회만 하므로 메모리가 안 든다.

MySQL 도 같다 — 5절 출력에서 `Hash` 밑에 있는 것이 5만 행짜리 `m` 이다.

★ **메모리에 안 들어가면 어떻게 되나** — 양쪽을 디스크로 나눠 여러 묶음(batch)으로 처리한다.\
그때 `EXPLAIN ANALYZE` 에 `Batches: 2` 이상이 뜬다([60번](../60-explain-analyze-estimates-vs-actuals/)).

---

### 13. 둘 다 `Nested loop inner join` 이다 — MySQL 에 머지 조인이 없다

**출력**

```text
### SQL: EXPLAIN FORMAT=TREE SELECT s.id, b.pad FROM t59_small s JOIN t59_big b ON b.id = s.ref;
--- MySQL 8.4.10 ---
-> Nested loop inner join  (cost=4.75 rows=10)
    -> Filter: (s.ref is not null)  (cost=1.25 rows=10)
        -> Table scan on s  (cost=1.25 rows=10)
    -> Single-row index lookup on b using PRIMARY (id=s.ref)  (cost=0.26 rows=1)
```

```text
### SQL: EXPLAIN SELECT m.id, b.pad FROM t59_mid m JOIN t59_big b ON b.id = m.ref;
--- MySQL 8.4.10 ---
| table | type   | key     | ref         | rows  | Extra       |
| m     | ALL    | NULL    | NULL        | 50610 | Using where |
| b     | eq_ref | PRIMARY | study.m.ref |     1 | NULL        |
```

**왜 그런가**

| 상황 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 바깥 10행 · 안쪽 기본키 | `Merge Join` | **`Nested loop`** |
| 바깥 5만행 · 안쪽 기본키 | `Hash Join` | **`Nested loop`**(`eq_ref`) |
| 양쪽 기본키 | `Merge Join` | (해당 계획 없음 — 항상 중첩 루프) |
| 조인 키에 인덱스 없음 | `Hash Join` | `Inner hash join` |

```text
 PostgreSQL 의 조인 도구               MySQL 8.4.10 의 조인 도구
 +---------------------------+        +---------------------------+
 | Nested Loop               |        | Nested loop               |
 | Hash Join                 |        | Hash join (8.0.18~)       |
 | Merge Join                |        | (머지 조인 없음)            |
 +---------------------------+        +---------------------------+
```

★ **MySQL 은 조인 키에 인덱스가 있으면 바깥이 5만 행이어도 중첩 루프를 고른다.**\
그래서 MySQL 쪽 조인 튜닝은 「**안쪽 표에 인덱스가 있나**」에 훨씬 크게 걸린다 —\
없으면 곧바로 해시 조인이 되고, 해시 조인은 양쪽을 통째로 훑는다.

★ **MySQL 이 `Filter: (s.ref is not null)` 을 스스로 덧붙였다.** 질의문에 없던 조건이다 —\
내부 조인에서 `NULL` 은 어차피 짝이 없으므로 미리 버린다([13번](../13-inner-join/)).

---

### 14. 추정 `1.01e+9`, 실측 **199,996행**

**출력**

```text
### SQL: EXPLAIN FORMAT=TREE SELECT count(*) FROM t59_mid m JOIN t59_big b ON b.val = m.val;
--- MySQL 8.4.10 ---
-> Aggregate: count(0)  (cost=1.11e+9 rows=1)
    -> Inner hash join (b.val = m.val)  (cost=1.01e+9 rows=1.01e+9)
        -> Table scan on b  (cost=0.0466 rows=199699)
        -> Hash
            -> Table scan on m  (cost=5101 rows=50610)
```

```text
### SQL: SELECT count(*) AS joined FROM t59_mid m JOIN t59_big b ON b.val = m.val;
--- MySQL 8.4.10 ---
+--------+
| joined |
+--------+
| 199996 |
+--------+
```

**왜 그런가** — 두 숫자를 나란히 놓으면 **추정이 실측의 5,000배가 넘는다.**

```text
 MySQL 의 추정   1,010,000,000 행
 실제로 센 값          199,996 행
 PG 의 추정            199,677 행     (12번 계획의 Hash Join rows=)
```

`val` 에는 인덱스가 없다. **인덱스가 없으면 그 열의 값 분포에 대한 정보도 없다** —\
MySQL 은 그 상태에서 조인 결과 크기를 크게 잡았고, PG 는 열 통계(`ANALYZE` 가 만든다)로 거의 맞혔다.

★ **이런 계획을 「느릴 것」으로 읽으면 안 된다.** 추정이 10억이어도 실제는 20만이다.\
**추정과 실측을 나란히 놓는 도구가 `EXPLAIN ANALYZE`** 이고, 그것이 [60번](../60-explain-analyze-estimates-vs-actuals/)의 주제다.

---

### 15. (A)는 순서가 없다. (B)에는 `Sort` 가 따로 붙는다

**출력**

```text
### SQL: EXPLAIN SELECT grp, count(*) FROM t59_big GROUP BY grp;              -- (A)
--- PG 18.6 ---
 HashAggregate  (cost=4728.00..4738.00 rows=1000 width=12)
   Group Key: grp
   ->  Seq Scan on t59_big  (cost=0.00..3728.00 rows=200000 width=4)

### SQL: EXPLAIN SELECT grp, count(*) c FROM t59_big GROUP BY grp ORDER BY grp; -- (B)
--- PG 18.6 ---
 Sort  (cost=4787.83..4790.33 rows=1000 width=12)
   Sort Key: grp
   ->  HashAggregate  (cost=4728.00..4738.00 rows=1000 width=12)
         Group Key: grp
         ->  Seq Scan on t59_big  (cost=0.00..3728.00 rows=200000 width=4)
```

**왜 그런가** — `HashAggregate` 는 그룹 키로 **해시 표**를 만든다. 해시 표에는 순서가 없다.

```text
 HashAggregate                          GroupAggregate
 +---------------------------+         +---------------------------+
 | 해시 표에 키를 넣고 누적    |         | 정렬된 입력을 훑으며 누적   |
 | 나오는 순서 = 해시 순서     |         | 나오는 순서 = 그룹 키 순서  |
 | -> 정렬 보장 없음          |         | -> 정렬돼 나온다            |
 +---------------------------+         +---------------------------+
```

★ **「`GROUP BY` 하면 정렬되더라」는 관찰이지 보장이 아니다.** 엔진이 `GroupAggregate` 를 고르면 정렬돼 나오고,\
`HashAggregate` 를 고르면 안 나온다. **어느 쪽이 뽑힐지는 통계가 정한다** — 6·7번과 같은 이야기다.

**순서가 필요하면 `ORDER BY` 를 쓴다.** 그러면 (B)처럼 `Sort` 가 정직하게 붙는다.\
정렬이 보장되는 것은 `ORDER BY` 뿐이라는 것은 [08번](../08-order-by-null-position-stability/)의 주제다.

MySQL 쪽은 같은 질의에 **인덱스 순서를 써서** `Group aggregate` 를 골랐다(16번 표 참고) — 같은 질의, 다른 선택이다.

---

### 16. 스캔도 바뀐다 — 계획은 한 덩어리로 고른다

**출력**

```text
### SQL: SET enable_hashagg = off;  EXPLAIN SELECT grp, count(*) FROM t59_big GROUP BY grp;
--- PG 18.6 ---
 GroupAggregate  (cost=0.29..11598.16 rows=1000 width=12)
   Group Key: grp
   ->  Index Only Scan using t59_big_grp on t59_big  (cost=0.29..10588.16 rows=200000 width=4)
```

**왜 그런가** — `GroupAggregate` 는 **입력이 그룹 키 순서일 것을 요구한다.**

```text
 HashAggregate 를 쓸 때                GroupAggregate 를 쓸 때
 +---------------------------+        +---------------------------+
 | 입력 순서는 아무래도 좋다   |        | 입력이 grp 순서여야 한다    |
 | -> Seq Scan 이면 충분      |        | -> grp 인덱스를 타거나      |
 |                           |        |    Sort 를 하나 깔아야 한다 |
 +---------------------------+        +---------------------------+
```

집계 노드 하나를 바꿨더니 **그 아래 스캔이 `Seq Scan` 에서 `Index Only Scan` 으로 바뀌었다.**\
★ **계획은 노드를 하나씩 고르는 게 아니라 트리 전체의 비용으로 고른다** — 위 노드의 요구가 아래 노드를 끌어당긴다.

**그 대신 총비용이 늘었다** — 4738.00 → 11598.16. 그래서 원래는 `HashAggregate` 가 뽑혔던 것이다.

**두 엔진이 같은 질의에 다른 방법을 골랐다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `GROUP BY grp`(인덱스 있음) | `HashAggregate` + `Seq Scan` | **`Group aggregate` + `Covering index scan`** |
| `GROUP BY val`(인덱스 없음) | `HashAggregate` + `Seq Scan` | `Aggregate using temporary table` + `Table scan` |

```text
### SQL: EXPLAIN FORMAT=TREE SELECT grp, count(*) FROM t59_big GROUP BY grp;
--- MySQL 8.4.10 ---
-> Group aggregate: count(0)  (cost=40124 rows=1004)
    -> Covering index scan on t59_big using k_grp  (cost=20154 rows=199699)

### SQL: EXPLAIN FORMAT=TREE SELECT val, count(*) FROM t59_big GROUP BY val;
--- MySQL 8.4.10 ---
-> Table scan on <temporary>
    -> Aggregate using temporary table
        -> Table scan on t59_big  (cost=20154 rows=199699)
```

---

### 17. PG 는 200,000행, MySQL 은 1,005행

**출력**

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

**왜 그런가** — `grp` 인덱스는 같은 값이 **붙어 있다.** 값이 바뀌는 자리만 찾아 건너뛰면 된다.

```text
 PG : Seq Scan + HashAggregate         MySQL : Using index for group-by
 +-----------------------------+      +-----------------------------+
 | 20만 행을 전부 읽고           |      | 인덱스에서 grp=0 의 첫 자리  |
 | 해시 표에 1,000개를 모은다     |      |  -> grp=1 의 첫 자리로 점프  |
 |                             |      |  -> … 1,000번 점프           |
 | 읽는 행: 200,000            |      | 읽는 행: 1,005              |
 +-----------------------------+      +-----------------------------+
```

★ **읽는 행 수가 200배 차이다.** MySQL 이 이 질의에 유리한 도구(느슨한 인덱스 스캔)를 갖고 있다.\
PG 에도 비슷한 성격의 최적화가 있지만 **이 데이터·이 계획에서는 뽑히지 않았다** — 본 것만 적는다.

**이 답은 두 엔진의 우열이 아니라 도구의 목록이 다르다는 뜻이다.**\
5번에서는 PG 가 가진 비트맵이 유리했고, 여기서는 MySQL 이 가진 느슨한 인덱스 스캔이 유리했다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 스캔 사다리 `grp = 7` ~ `grp < 900` (2·3·4번) | PG 18.6 · MySQL 8.4.10 | **PG 3회 · MySQL 3회** | PG 는 한 트랜잭션에 한 번에 찍었다 |
| MySQL 전환점 탐색 (4번) | MySQL 8.4.10 | 13회 | `grp < 50·60·70·80·90·100·120·125·130·135·140·150·200` |
| PG 전환점 탐색 (4번) | PG 18.6 | 20회 이상 | `grp < 100`~`900` 을 좁혀 가며 |
| ★ **전환점 8판 반복** (6·7번) | PG 18.6 | **8회** | **연산자가 4:4 로 갈렸다 — 이 편의 핵심 근거** |
| `Index Only Scan` / `Using index` (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | |
| 조인: 바깥 10행 / 50,000행 (9번) | PG 18.6 | 각 3회 | **연산자가 갈린 자리** |
| 중첩 루프 강제 (10번) | PG 18.6 | 3회 | `enable_mergejoin`·`enable_hashjoin` off |
| 양쪽 기본키 조인 (11번) | PG 18.6 | 2회 | `Sort` 노드가 없다 |
| 해시 표의 방향 (12번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 양쪽 다 작은 쪽 |
| MySQL 조인 연산자 (13번) | MySQL 8.4.10 | 4회 | 표 형식 · `FORMAT=TREE` |
| ★ 추정 대 실측 (14번) | MySQL 8.4.10 · PG 18.6 | 각 2회 | **`count(*)` 로 실측까지** |
| 집계·정렬 (15·16·17번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `enable_hashagg` off 포함 |
| 뒷정리 확인 | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\dtvm` · `SHOW FULL TABLES` |

★ **계획 드리프트 재확인(제출 직전)** — 본문 계획을 다시 찍어 1차 관찰과 대조했다.

```text
 다시 찍어도 같았던 것                          다시 찍었더니 달라진 것
 스캔 사다리의 연산자 (grp<50·grp<200·grp<540   PG 의 추정 rows= 와 cost=
   ·grp<900) — 전부 같았다                       grp<50    10,045 -> 9,848
 조인 연산자 (9·11·12·13번)                      grp<200   40,352 -> 39,120
 집계 연산자 (15·16·17번)                        J3 cost   4128.59 -> 4114.72
 MySQL 의 type·key·Extra 칸                      J4 rows   198,468 -> 199,677
 MySQL 의 추정 1.01e+9 과 실측 199,996           G3 rows   50,386 -> 50,081
 PG 의 Seq Scan 비용 4228.00 (조건과 무관)      MySQL 의 rows= 199,680 -> 199,699
                                               ★ grp<520 의 연산자 (Seq -> Bitmap)
```

★ **드리프트가 실제로 있었다.** 원인은 `ANALYZE` 가 표본 조사라는 것 하나다 —\
표를 다시 만들고 통계를 다시 잡을 때마다 추정이 ±1% 안팎으로 흔들린다.\
**본문의 계획 블록은 재확인 시점 출력으로 갱신했고**, 4번의 사다리에서 `grp < 520` 은
**「경계」로 표시를 바꿨다**(전에는 `Seq Scan` 으로 적혀 있었다).

**흔들린 것과 안 흔들린 것이 정확히 갈렸다.**

```text
 흔들렸다                                안 흔들렸다
 rows= (추정) · cost=                    경계에서 떨어진 자리의 연산자
 경계(grp<520) 위의 연산자                Index Cond / Recheck Cond / Filter 의 구분
                                         MySQL 의 type · key · Extra
                                         실측값 (count(*) = 199,996)
```

**그래서 본문은 경계 위의 값을 결론으로 쓰지 않고, 경계가 흔들린다는 사실 자체를 6·7번의 본문으로 삼았다.**

**구현 의존 항목** — 2·4·5·9·11·12·13·15·16·17번의 **연산자 선택**이다. 전부 **옵티마이저의 선택**이고,\
전환점의 정확한 % 는 **이 데이터·이 표 폭·이 통계**의 값이다. 재현되는 것은 숫자가 아니라 **「% 로 갈린다」는 성질**이다.

**언어 보장 항목** — 1·3·8·10·12·14번의 **읽는 법**이다. `possible_keys` 와 `key` 를 나눠 읽는 것,\
`Using index` 가 커버링이라는 것, 해시 표를 작은 쪽으로 만드는 것, 중첩 루프 비용이 바깥 행 수에 곱해지는 것은\
**두 엔진의 출력과 문서에서 같았다.**

**한쪽에서만 결론이 서는 실험** — 6·7번(8판 반복)은 **PG 에서만** 돌렸다. MySQL 은 이 데이터에서 전환점이\
`grp < 140`~`150` 사이인데, 그 사이를 더 좁혀 흔들림을 재는 실험은 하지 않았다. **6·7번의 근거는 PG 출력뿐이다.**\
다만 **「경계에서 계획이 흔들린다」 자체는 MySQL 에서도 관찰된 적이 있다**([19번](../19-semi-anti-join/)의 `NOT IN`).

**버전** — MySQL 의 해시 조인은 **8.0.18 부터**다. 그 이전 버전에서는 13번의 마지막 줄이 `Block Nested Loop` 가 된다.\
`EXPLAIN FORMAT=TREE` 는 8.0.16 부터다. 버전이 오르면 **4·9·13·16·17번**을 다시 돌린다.
