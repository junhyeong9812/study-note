# sql/47-인덱스를 언제 타고 언제 안 타나 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **측정 조건** — 20,000행 `t47`, **`ANALYZE`/`ANALYZE TABLE` 직후**, 기본 설정, 다른 부하 없음. 비실행 `EXPLAIN` 만 썼다.\
> ★★ **계획은 관찰이지 보장이 아니다.** 제출 직전에 전부 다시 찍었고, **움직인 두 자리를 아래 「실행 검증」에 적었다.**\
> 이 편이 만든 `t47` 과 인덱스는 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> 문서 근거는 [PG 18 Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) · [MySQL 8.4 EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. ★ 복합 인덱스의 선행 열 — **(a)(b) 탄다 / (c) 못 탄다**

**출력**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE a=7 AND b=7;
 Bitmap Heap Scan on t47
   Recheck Cond: ((a = 7) AND (b = 7))
   ->  Bitmap Index Scan on t47_ab_idx
         Index Cond: ((a = 7) AND (b = 7))

EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE a=7;
 Bitmap Heap Scan on t47
   Recheck Cond: (a = 7)
   ->  Bitmap Index Scan on t47_ab_idx
         Index Cond: (a = 7)

EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE b=7;
 Seq Scan on t47
   Filter: (b = 7)
```

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

**왜 그런가** — [46 번 1번의 정렬 그림](../46-index-definition-composite-partial-expression/)이 근거다.

```text
인덱스 안의 순서 = (a, b) 사전순

  (0,0) (0,1) ... (0,9) (1,0) (1,1) ... (99,9)

WHERE a=7 AND b=7  ->  (7,7) 한 지점        -> 짚는다
WHERE a=7          ->  (7,0)~(7,9) 연속     -> 좁힌다
WHERE b=7          ->  (0,7)(1,7)...(99,7)  -> ★ 흩어져 있다. 구간이 안 된다
```

---

### 2. MySQL 의 `key_len` 이 말해 주는 것 — **복합 인덱스의 몇 칸까지 썼나**

```text
(a, b) 는 int 두 개 = 4바이트 + 4바이트

key_len = 8   ->  a 와 b 를 둘 다 썼다
key_len = 4   ->  ★ a 만 썼다. b 는 안 쓰였다
key_len = NULL ->  인덱스를 아예 안 썼다
```

★ **「인덱스를 탔다」와 「제대로 탔다」가 다르다는 것을 이 숫자 하나가 잡아 준다.**

```text
WHERE a=7 AND b>3   같은 질의에서
  key_len 이 4 면   -> a 로만 좁히고 b>3 은 읽은 뒤 거른 것이다
  key_len 이 8 이면 -> 둘 다로 좁힌 것이다
```

PG 에는 이 칸이 없다. 대신 **`Index Cond` 에 무엇이 들어 있나**로 같은 것을 본다.

```text
Index Cond: ((a = 7) AND (b = 7))    -> 둘 다로 좁혔다
Index Cond: (a = 7)                  -> a 로만 좁혔다
Filter:     (b = 7)                  -> b 는 읽은 뒤 버렸다
```

---

### 3. ★ (c) 가 안 탄 이유는 선택도인가 — **아니다. 전용 인덱스를 만들면 같은 10% 를 탄다**

**확인 방법 두 가지**

**(1) `possible_keys` 를 본다.**

```text
WHERE b=7  ->  possible_keys: NULL
                              ^^^^
              후보에 아무 인덱스도 없었다 = 비용 비교 자체를 안 했다
```

선택도로 버렸다면 **후보에는 있고 `key` 만 `NULL`** 이어야 한다(8번).

**(2) `b` 전용 인덱스를 만들어 반증한다.**

```text
--- PG 18.6 ---
CREATE INDEX t47_b_idx ON t47 (b); ANALYZE t47;
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE b=7;
 Bitmap Heap Scan on t47
   Recheck Cond: (b = 7)
   ->  Bitmap Index Scan on t47_b_idx
         Index Cond: (b = 7)

--- MySQL 8.4.10 ---
+-------+------+---------------+-----------+---------+-------+------+
| table | type | possible_keys | key       | key_len | ref   | rows |
+-------+------+---------------+-----------+---------+-------+------+
| t47   | ref  | t47_b_idx     | t47_b_idx |       4 | const | 2000 |
+-------+------+---------------+-----------+---------+-------+------+
```

★ **같은 2,000행(10%)을 이번에는 탔다.** 그러니 1번 (c) 의 `Seq Scan` 은 **행 수 때문이 아니었다.**\
**같은 문서 안에서 반증을 실은 것**이다 — 원인을 선택도로 돌렸으면 틀린 처방(「인덱스를 더 만들지 마라」)이 나왔다.

---

### 4. ★ 열에 함수를 씌우면 — **(a) 탄다 / (b) 양쪽 다 죽는다**

**출력 — (a)**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE v = 'name000123';
 Index Scan using t47_v_idx on t47
   Index Cond: ((v)::text = 'name000123'::text)

--- MySQL 8.4.10 ---
+-------+------+---------------+-----------+---------+-------+------+
| table | type | possible_keys | key       | key_len | ref   | rows |
+-------+------+---------------+-----------+---------+-------+------+
| t47   | ref  | t47_v_idx     | t47_v_idx |     122 | const |    1 |
+-------+------+---------------+-----------+---------+-------+------+
```

**출력 — (b)**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE upper(v) = 'NAME000123';
 Seq Scan on t47
   Filter: (upper((v)::text) = 'NAME000123'::text)

--- MySQL 8.4.10 ---
+-------+------+---------------+------+---------+------+-------+-------------+
| table | type | possible_keys | key  | key_len | ref  | rows  | Extra       |
+-------+------+---------------+------+---------+------+-------+-------------+
| t47   | ALL  | NULL          | NULL |    NULL | NULL | 19803 | Using where |
+-------+------+---------------+------+---------+------+-------+-------------+
```

★ **`possible_keys` 가 `NULL` 이다.** `rows` 가 1 에서 19,803 으로 뛰었다.\
**두 엔진이 같은 판정을 냈다** — 이 자리에는 방언 차이가 없다.

---

### 5. 왜 죽는가 — **인덱스는 「원래 값」의 순서이기 때문이다**

```text
t47_v_idx 가 저장한 순서

  name000001
  name000002
  ...
  name020000

질의가 묻는 것 : upper(v) 가 'NAME000123' 인 행
        ↓
upper() 를 거친 값의 순서는 이 인덱스 안에 없다
        ↓
어느 구간을 읽으면 되는지 정할 수 없다
        ↓
전부 읽고, 행마다 upper() 를 계산해 비교한다   <- Filter 에만 조건이 남는다
```

**같은 규칙이 붙는 모든 자리**

```text
WHERE upper(v) = ...        문자열 가공
WHERE date(ts) = ...        날짜 절단
WHERE id + 0 = ...          산술
WHERE SUBSTR(code,2) = ...  부분 문자열
        ↓
전부 "열이 변형됐다" 는 한 가지 이유다
```

★ **판정 기준이 한 줄이다** — **`WHERE` 의 왼쪽에 열 이름만 있나?**\
열에 무엇이 씌워져 있으면 그 열의 인덱스는 후보가 아니다.

---

### 6. ★ 어떻게 살리나 — **표현식 인덱스. 그리고 `((expr))` 은 양쪽 다 된다**

**출력**

```text
--- PG 18.6 ---
CREATE INDEX t47_upper_idx ON t47 ((upper(v)));
ANALYZE t47;
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE upper(v) = 'NAME000123';
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

**왜 그런가**

```text
이제 "upper(v) 의 값" 을 정렬해 둔 자료가 생겼다
        ↓
질의가 묻는 것과 정렬 기준이 일치한다
        ↓
구간을 정할 수 있다 -> rows 19,803 -> 1
```

★ **문법은 `((expr))` — 괄호 둘이 이식 가능한 형태다**([46 번 5번](../46-index-definition-composite-partial-expression/)).\
괄호 하나(`(upper(v))`)는 MySQL 에서 `ERROR 1064` 다.

**대가 둘**

```text
1. 인덱스가 하나 더 생긴다 — 쓰기마다 갱신되고 공간을 쓴다
2. ★ 질의를 그 식과 똑같이 써야 한다
     lower(v) 인덱스는 WHERE upper(v)=... 에 쓰이지 않는다
```

MySQL 에는 **생성 열 + 인덱스**라는 같은 뜻의 길도 있다([45](../45-check-not-null-default-generated-columns/)·[46 번 11번](../46-index-definition-composite-partial-expression/)).

---

### 7. ★ 선택도의 경계 — **PG 34.5% · MySQL 29~30%. 그리고 움직인다**

**출력 — PG**

```text
--- PG 18.6 ---  (EXPLAIN 첫 줄만 모았다)
r <= 100    : Bitmap Heap Scan on t47
r <= 1000   : Bitmap Heap Scan on t47
r <= 3000   : Bitmap Heap Scan on t47
r <= 6000   : Bitmap Heap Scan on t47
r <= 6800   : Bitmap Heap Scan on t47
r <= 6900   : Bitmap Heap Scan on t47
r <= 7000   : Seq Scan on t47            <- 여기서 갈린다 (34.5% -> 35%)
r <= 16000  : Seq Scan on t47
```

**비용을 보면 이유가 숫자로 나온다.**

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

```text
539.01  <  545.00   -> 인덱스가 이긴다
그 위로 올라가면    -> 순차가 이긴다
        ↓
경계는 "비용이 교차하는 점" 이지 고정된 비율이 아니다
```

**출력 — MySQL (★ 두 번 쟀고 달랐다)**

```text
--- MySQL 8.4.10 ---  (처음)
r <= 5600  : type=range  key=t47_r_idx  rows=5600
r <= 5800  : type=ALL    key=NULL       rows=19730   <- 여기서 갈렸다

--- MySQL 8.4.10 ---  (제출 직전 재확인)
r <= 5800  : type=range  key=t47_r_idx  rows=5800
r <= 6000  : type=ALL    key=NULL       rows=20497   <- 이제 여기다
```

| | 경계(처음) | 경계(제출 직전) | 전체 대비 |
|---|---|---|---|
| PostgreSQL 18.6 (`r`) | 6,900 → 7,000 | **같음** | 34.5% → 35% |
| MySQL 8.4.10 (`r`) | 5,600 → 5,800 | **5,800 → 6,000** | 28~30% |

★ **수치는 이 서버·이 데이터의 관찰이다.** 외울 것은 **「표의 3분의 1쯤」이라는 자릿수**와 **왜 갈리는가**다.

```text
인덱스로 찾는다              순차로 훑는다
 인덱스를 읽고                표를 앞에서 뒤로 연속으로 읽는다
 그 위치의 표를 읽는다         (디스크에 친화적이라 싸다)
        ↓                             ↓
 찾는 행이 적으면 이득          찾는 행이 많으면 결국 표를 거의 다 읽는데
                             흩어진 순서라 더 비싸다
```

---

### 8. ★ 「못 쓴다」와 「안 쓴다」를 어떻게 가르나 — **`possible_keys` 와 `key`**

```text
possible_keys = NULL          ->  ★ 못 쓴다
                                  그 질의로는 어떤 인덱스도 쓸 수 없다
                                  (선행 열 누락 · 함수 · 암시 변환 · collation · 앞이 열린 LIKE)
                                  -> 인덱스를 더 만들거나 질의를 고쳐야 한다

possible_keys = 인덱스,  key = NULL  ->  ★ 안 쓴다
                                  후보로 고려했고 비용을 비교한 뒤 버렸다
                                  -> 인덱스를 더 만들어도 소용없다
```

**이 문서 안의 두 실물**

```text
4번 (b)  upper(v)=...    possible_keys: NULL         <- 못 쓴다
7번      r <= 10000      possible_keys: t47_r_idx    <- 안 쓴다
                         key: NULL
```

```text
--- MySQL 8.4.10 ---  7번의 그 줄
+-------+------+---------------+------+---------+------+-------+----------+-------------+
| table | type | possible_keys | key  | key_len | ref  | rows  | filtered | Extra       |
+-------+------+---------------+------+---------+------+-------+----------+-------------+
| t47   | ALL  | t47_r_idx     | NULL |    NULL | NULL | 20497 |    29.40 | Using where |
+-------+------+---------------+------+---------+------+-------+----------+-------------+
                  ↑ 후보에는 있다     ↑ 안 골랐다
```

**PG 에는 `possible_keys` 칸이 없다.** 대신 이렇게 가른다.

```text
- 인덱스를 지우지 않고 enable_seqscan=off 로 강제해 본다
    -> 계획이 인덱스로 바뀌면 "쓸 수는 있었다" = 안 쓴 것이다
    -> 여전히 Seq Scan 이면 "못 쓴다"
  ★ 이 실험에서는 강제하지 않았다 — 강제하면 "엔진이 무엇을 고르나" 를 못 보게 된다
- 또는 3번처럼 조건을 바꿔 가며 반증을 만든다
```

---

### 9. ★ 같은 50% 인데 계획이 다르다 — **뽑는 열이 정한다**

**출력**

```text
--- PG 18.6 ---
EXPLAIN (COSTS OFF) SELECT * FROM t47 WHERE r <= 10000;
 Seq Scan on t47
   Filter: (r <= 10000)

EXPLAIN (COSTS OFF) SELECT r FROM t47 WHERE r <= 10000;
 Index Only Scan using t47_r_idx on t47
   Index Cond: (r <= 10000)
```

```text
--- MySQL 8.4.10 ---
EXPLAIN SELECT * FROM t47 WHERE r <= 10000;
| t47 | ALL   | t47_r_idx | NULL      | NULL | NULL | 20497 | 48.87 | Using where |

EXPLAIN SELECT r FROM t47 WHERE r <= 10000;
| t47 | range | t47_r_idx | t47_r_idx |    5 | NULL | 10000 |100.00 | Using where; Using index |
                                                                                   ^^^^^^^^^^^^
```

**왜 갈리나**

```text
SELECT *
  인덱스에서 위치를 찾는다 -> 나머지 열을 읽으러 표로 간다
  10,000번의 흩어진 표 접근 -> 비싸다 -> 순차 스캔이 이긴다

SELECT r
  ★ 필요한 값이 인덱스 안에 이미 있다
  표 접근이 0번 -> 인덱스가 이긴다
```

> **커버링(covering)** — 질의가 필요한 열을 인덱스가 전부 갖고 있어 **표를 안 읽는** 것.\
> 예: PG 는 `Index Only Scan`, MySQL 은 `Extra: Using index` 로 표시한다.

★ **「선택도가 X% 를 넘으면 인덱스를 안 탄다」는 틀린 요약이다.**\
정하는 것은 **선택도 × 표 접근 필요 여부 × 물리적 상관** 셋이다(10번).

---

### 10. `k` 와 `r` 이 왜 다른가 — **상관(correlation)**

**두 열은 분포가 같고 물리적 배치만 다르다.**

```text
--- PG 18.6 ---
SELECT attname, correlation FROM pg_stats WHERE tablename='t47' AND attname IN ('k','r');
 attname |  correlation  
---------+---------------
 k       |             1            <- 저장 순서 = 값 순서
 r       | -0.0007359975            <- 무관하다
(2 rows)
```

**경계를 각각 찾았다.**

```text
--- PG 18.6 ---
r <= 6900  : Bitmap Heap Scan on t47
r <= 7000  : Seq Scan on t47                    <- 34.5% ~ 35%

k <= 9000  : Index Scan using t47_k_idx on t47
k <= 10000 : Seq Scan on t47                    <- 45% ~ 50%
```

**왜 그런가**

```text
r (correlation 0)   인덱스가 짚는 위치가 표 전체에 흩어져 있다
                    -> 같은 페이지를 여러 번 오가는 임의 접근 -> 비싸다

k (correlation 1)   인덱스를 앞에서 뒤로 읽으면 표도 앞에서 뒤로 읽힌다
                    -> 연속 접근 -> 싸다 -> 더 늦게까지 인덱스가 이긴다
```

★ **계획 이름까지 다르다.**

```text
r : Bitmap Heap Scan     위치를 먼저 모아 정렬한 뒤 표를 한 번에 훑는다 (흩어짐 대응)
k : Index Scan           하나씩 짚어 읽는다 (어차피 순서대로라 괜찮다)
```

**PG 가 상관을 보고 접근 방식까지 바꿨다.** MySQL 에는 이에 해당하는 통계 칸이 `EXPLAIN` 에 노출되지 않는다.

---

### 11. 이미 실측된 세 자리 — **다시 재지 않고 결론만 받는다**

**(1) 암시 타입 변환 — [35 타입 체계와 캐스팅 3번](../35-type-system-and-casting/)이 정본**

```text
거기서 잰 것 : varchar 열 = 정수 리터럴
  PG    : ERROR (character varying = integer 연산자가 없다) — 문이 서지 않는다
  MySQL : 돈다. type 이 index 로, rows 가 1 -> 19905
          ★ 경고 1739 "Cannot use ref access ... due to type or collation conversion"
          그리고 결과가 0행이다

결론 : 열 쪽이 변하면 죽고 값 쪽만 변하면 산다.
       int 열 = bigint 값은 인덱스를 탄다 (거기서 반증을 실었다)
```

**(2) 앞이 열린 `LIKE` — [38 패턴 매칭 5번](../38-pattern-matching-like-regex/)이 정본**

```text
거기서 잰 것 :
  LIKE 'C00012%'  MySQL: type=range, rows 10
                  PG   : ★ 기본 인덱스로는 Seq Scan (DB collate 가 en_US.utf8 이라서)
                         varchar_pattern_ops 인덱스를 따로 만들면 Index Scan
  LIKE '%00123'   양쪽 다 전부 훑는다. MySQL 의 possible_keys 가 NULL

결론 : 앞이 고정된 패턴만 구간이 된다. LIKE '%x' 는 어느 엔진에서도 못 탄다.
       그리고 PG 는 앞이 고정돼도 collation 때문에 못 타는 경우가 있다
```

**(3) collation 불일치 — [39 collation 6번](../39-collation/)이 정본**

```text
거기서 잰 것 :
  WHERE code = 'C000123'                      PG: Index Scan / MySQL: type=ref
  WHERE code COLLATE "C" = 'C000123'          PG: ★ Seq Scan
  WHERE code = 'C000123' COLLATE utf8mb4_bin  MySQL: ref -> range + ★ 경고 1739

결론 : collation 은 인덱스의 일부다. 질의가 다른 정렬 규칙을 요구하면 그 인덱스는 쓸모가 없다
```

★ **이 편에서 새로 잰 것과 받아 온 것을 갈라 두면 이렇다.**

```text
새로 잰 것 (이 편)              받아 온 것 (다른 편이 정본)
1. 선행 열 누락 (1·2·3번)        암시 타입 변환        -> 35번
2. 열에 함수 씌우기 (4·5번)       앞이 열린 LIKE        -> 38번
3. 표현식 인덱스로 살리기 (6번)    collation 불일치      -> 39번
4. 선택도 경계 (7번)
5. 커버링 (9번)
6. 상관 (10번)
```

---

### 12. 네 자리를 관통하는 한 문장 — **열을 건드리지 마라**

```text
인덱스는 "그 열의 원래 값을, 그 타입과 그 collation 의 순서로" 정렬해 둔 것이다
        ↓
열에 손이 닿으면 그 정렬은 쓸모가 없어진다

   내가 함수를 씌운다        upper(v)                   4번
   엔진이 변환을 끼워 넣는다  varchar 열 = 정수           35번
   내가 collation 을 바꾼다  code COLLATE "C"            39번
   패턴이 앞을 열어 둔다      LIKE '%x'  (구간이 안 선다)  38번
        ↓
처방도 둘뿐이다
   (1) 열을 건드리지 말고 값 쪽을 맞춘다
   (2) 그 변형 결과를 정렬해 둔 인덱스를 따로 만든다
         표현식 인덱스 (6번) · varchar_pattern_ops (38번) · COLLATE 인덱스 (39번)
```

---

### 13. MySQL 에서 이유를 못 봤을 때 — **`SHOW WARNINGS`**

```text
EXPLAIN 은 "무엇을 골랐나" 를 보여 준다
SHOW WARNINGS 는 "왜 못 골랐나" 를 말해 주는 경우가 있다
```

[35](../35-type-system-and-casting/)·[39 번](../39-collation/)에서 받은 경고가 그것이다.

```text
| Warning | 1739 | Cannot use ref access on index 't39_code_idx' due to type or
|         |      | collation conversion on field 'code'                          |
| Warning | 1739 | Cannot use range access on index ... (같은 이유)                |
```

★ **경고는 결과에 안 실린다.** 물어야만 보인다 — [42 번의 Note 1050](../42-create-alter-drop-table/) 과 같은 통로다.

**PG 에는 이런 경고가 없다.** 대신 계획 자체가 이유를 드러낸다.

```text
Index Cond 에 있다   -> 인덱스로 좁혔다
Filter 에만 있다     -> 읽은 뒤 버렸다 = 그 조건은 인덱스를 못 썼다
```

---

### 14. ★ 계획을 문서에 박아도 되나 — **조건을 같이 적어야 한다**

**같이 적을 것**

```text
1. 버전            PostgreSQL 18.6 · MySQL 8.4.10
2. 행 수와 분포     20,000행 · r 은 1..20000 균등 · 상관 ~0
3. 통계 상태        ANALYZE / ANALYZE TABLE 직후
4. 설정            기본값 · 다른 부하 없음
5. ★ 다시 찍은 날짜  그리고 달라졌으면 그 사실
```

★ **이 편에서 실제로 두 자리가 움직였다.** 데이터도 버전도 안 바꿨다.

```text
(1) MySQL 의 선택도 경계    5,600~5,800  ->  5,800~6,000
(2) PG 의 k <= 10000        Index Scan   ->  Seq Scan
```

그 사이에 한 일은 **인덱스 둘(`t47_b_idx`·`t47_upper_idx`)을 추가하고 `ANALYZE` 를 다시 돌린 것**뿐이다.\
경위는 아래 「실행 검증」에 적었다.

**그래서 문서에 적는 방식이 달라진다.**

```text
(나쁨) "이 질의는 인덱스를 탄다"
(좋음) "PG 18.6 · 20,000행 · ANALYZE 직후에 Index Scan 이 나왔다 (2026-09-21 관찰)"
```

**운영에서도 같다** — 개발 DB 에서 찍은 계획은 **행 수가 달라서** 운영과 다르다.\
행이 적으면 **인덱스가 있어도 순차가 뽑힌다.**

---

### 15. 그래서 어떻게 고치나 — **네 단계 순서**

```text
1. possible_keys 를 본다 (MySQL) / Index Cond 대 Filter 를 본다 (PG)
      NULL 이다        -> "못 쓴다". 2단계로
      인덱스가 있다     -> "안 쓴다". 4단계로

2. 왜 못 쓰나를 가른다
      WHERE 왼쪽에 열 이름만 있나?           아니면 -> 함수·연산을 뗀다 (4·5번)
      열과 값의 타입이 같나?                아니면 -> 값 쪽을 맞춘다 (35번)
      collation 이 같나?                   아니면 -> 열/인덱스 쪽을 고친다 (39번)
      LIKE 의 앞이 고정됐나?                아니면 -> 앞을 고정하거나 다른 색인을 쓴다 (38번)
      복합 인덱스의 선행 열이 조건에 있나?   아니면 -> 열 순서를 바꾸거나 인덱스를 추가한다 (1번)

3. 그래도 변형이 필요하면 그 변형을 정렬해 둔 인덱스를 만든다
      CREATE INDEX i ON t ((upper(v)));       <- 양쪽 다 된다 (6번)
      그리고 질의를 그 식과 똑같이 쓴다

4. "안 쓴다" 였다면 인덱스를 추가하지 않는다
      뽑는 열을 줄여 커버링을 만든다 (9번)
      조건을 더 좁힌다 (선택도를 높인다)
      그래도 안 되면 ★ 그게 맞는 계획일 수 있다 — 표의 절반을 읽는 질의는 순차가 옳다
```

★ **1단계를 건너뛰면 처방이 통째로 틀린다.**\
「`Seq Scan` 이 보인다 → 인덱스를 추가한다」는 **「안 쓴다」인 경우에 아무 효과가 없고 쓰기만 느려진다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `t47` 20,000행 적재 | PG 18.6 · MySQL 8.4.10 | 각 1회 | PG `generate_series` · MySQL 재귀 CTE |
| `pg_stats.correlation` (10번) | PG 18.6 | 2회 | `k`=1 · `r`≈0 |
| 복합 인덱스 3조건 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **`key_len` 8/4/NULL 이 근거다** |
| `b` 전용 인덱스 반증 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **같은 10% 를 탔다** |
| 열에 함수 (4·5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`possible_keys: NULL` 이 근거다** |
| 표현식 인덱스로 복구 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `((expr))` — **양쪽 다 통과** |
| ★ 선택도 스윕 (7번) | PG 18.6 | 19회 | 100 ~ 16000, 경계 부근을 좁혔다 |
| ★ 선택도 스윕 (7번) | MySQL 8.4.10 | 24회 | 처음 15회 + 재확인 9회 |
| 경계 전후 비용 (7번) | PG 18.6 | 3회 | **539.01 대 545.00** |
| 커버링 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `SELECT *` 대 `SELECT r` |
| `k` 경계 (10번) | PG 18.6 | 7회 | 6900 ~ 14000 |
| ★ 제출 직전 재확인 | PG 18.6 · MySQL 8.4.10 | 각 11·9회 | **아래 드리프트 참조** |
| 뒷정리 후 표 목록 | PG 18.6 · MySQL 8.4.10 | 각 1회 | 아래 |

### ★ 계획 드리프트 — 실제로 두 자리가 움직였다

**데이터도 버전도 설정도 바꾸지 않았다.** 사이에 한 일은 **인덱스 둘 추가 + 통계 재수집**이다.

```text
(1) MySQL 의 선택도 경계
      처음        : r <= 5600 range / r <= 5800 ALL      (28% -> 29%)
      제출 직전   : r <= 5800 range / r <= 6000 ALL      (29% -> 30%)
      rows 추정치도 19,730 -> 20,497 로 바뀌었다 (실제는 20,000 — 둘 다 추정치다)

(2) PG 의 k <= 10000 (50%)
      처음        : Index Scan using t47_k_idx on t47
      제출 직전   : Seq Scan on t47
      ★ correlation 은 여전히 1 이다. 바뀐 것은 비용 계산 쪽이다
      경계를 다시 찾으니 k <= 9000 은 Index Scan, k <= 10000 은 Seq Scan 이었다
```

**본문에는 재확인한 값을 실었고**(7·10번), **처음 값도 지우지 않고 나란히 남겼다.**\
움직였다는 사실 자체가 이 주제의 결론 하나이기 때문이다 — **계획은 관찰이지 보장이 아니다.**

**움직이지 않은 것** — 1·2·3·4·6·9번의 계획은 처음과 제출 직전이 **전부 같았다.**\
「인덱스를 쓰나 마나」 수준의 판정은 안정적이고, **경계에 가까운 수치가 흔들린다.**

**구현 의존 항목** — ★ **이 편 전체다.**\
SQL 이 보장하는 것은 **결과**이지 **방법**이 아니다. 계획·비용·`rows`·경계 수치는 전부 옵티마이저가 정한 것이다.\
`Bitmap Heap Scan`·`Index Only Scan` 이라는 이름조차 PG 고유다.

**언어 보장 항목** — **없다.** 이 편에서 「문서가 보장한다」고 말할 수 있는 것은\
**「인덱스가 있든 없든 결과 집합은 같다」** 하나뿐이고, 그것은 계획 이야기가 아니다.

**버전을 적지 않은 이유** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 두 매뉴얼에서 찾지 못했다.\
다만 **비용 모델은 버전마다 바뀐다** — 그래서 머리말에 버전을 박았다.

### ★ DB 뒷정리 확인

이 배치(42~47)가 만든 표를 전부 지운 뒤 **두 엔진의 표 목록을 눈으로 확인했다.**\
접두 규칙(`t4N_`)에서 새는 `t46`·`t47`(밑줄 없음)도 따로 지웠다.

```text
--- PG 18.6 ---
\dt
          List of tables
 Schema | Name | Type  |  Owner   
--------+------+-------+----------
 public | dept | table | postgres
 public | emp  | table | postgres
(2 rows)
```

```text
--- MySQL 8.4.10 ---
SHOW FULL TABLES;
+-----------------+------------+
| Tables_in_study | Table_type |
+-----------------+------------+
| dept            | BASE TABLE |
| emp             | BASE TABLE |
+-----------------+------------+
```

**뷰·시퀀스도 확인했다.**

```text
--- PG 18.6 ---
\dv
Did not find any views.
\ds
Did not find any sequences.
```

(`t45_ai2` 의 `serial` 이 만든 시퀀스 `t45_ai2_id_seq` 도 표를 지우면서 함께 사라졌다.)

`emp`·`dept` 는 이 배치의 **여섯 편 어느 곳에서도 읽거나 쓰지 않았고**, 내용도 그대로다.

```text
--- PG 18.6 ---                      --- MySQL 8.4.10 ---
 id | name | dept_id | salary        +----+------+---------+--------+
----+------+---------+--------       | id | name | dept_id | salary |
  1 | ann  |      10 |    300        +----+------+---------+--------+
  2 | bob  |      10 |    500        |  1 | ann  |      10 |    300 |
  3 | cho  |      20 |               |  2 | bob  |      10 |    500 |
  4 | dan  |         |    400        |  3 | cho  |      20 |   NULL |
(4 rows)                             |  4 | dan  |    NULL |    400 |
                                     +----+------+---------+--------+
 id | name                           +----+-------+
----+-------                         | id | name  |
 10 | sales                          +----+-------+
 20 | dev                            | 10 | sales |
 30 | hr                             | 20 | dev   |
(3 rows)                             | 30 | hr    |
                                     +----+-------+
```
