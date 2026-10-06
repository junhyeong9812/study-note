# api-design/12-filtering-sorting-search — 필터·정렬·검색 파라미터와 인덱스 — 정리 (힌트)

## 해결하는 문제

목록 API의 사용자는 "내 것만", "가격 낮은 순", "이름에 abc가 든 것"을 원한다.\
이 요구를 파라미터로 열어 주는 순간, **클라이언트가 DB에 보낼 쿼리 모양을 고르게** 된다.\
어떤 모양은 인덱스로 0.1ms에 끝나고, 어떤 모양은 테이블 전체를 읽고 정렬한다.

```text
 GET /products?order_by=created_at desc      → 인덱스 순서대로 20개 읽고 끝    (0.139 ms)
 GET /products?order_by=name                 → 100만 행을 다 읽어 정렬        (366 ms)
 GET /products?order_by=name&offset=200000   → 정렬이 메모리를 넘어 디스크로   (2,880 ms)
                                               (실험 Q1·Q2·Q3, PostgreSQL 17)
```

쉬운 예: 도서관 사서에게 책을 찾아 달라고 한다.
- "제목 가나다순으로 20권"은 제목 카드 목록(색인)이 있어 앞에서 20장만 넘기면 된다.
- "표지 색깔순으로 20권"은 색깔 목록이 없다. 서고의 책을 전부 꺼내 늘어놓아야 한다.
- 사서가 받을 수 있는 주문을 "목록이 있는 기준"으로 정해 두면, 무리한 주문은 창구에서 거절할 수 있다.

똑같은 구조다.
- 카드 목록 = 인덱스. 받을 수 있는 주문 = 허용된 필터·정렬 목록(allow-list). 창구 거절 = 400.

실무 예: 관리자 화면의 "아무 컬럼이나 클릭 정렬", 범용 `?sort=` 파라미터를 ORM에 그대로 넘기는 코드, 상품명 부분 검색(`LIKE '%…%'`). 평소엔 데이터가 작아 괜찮다가, 테이블이 커지거나 크롤러가 이상한 조합을 두드리면 DB가 포화된다.

## 동작·원리

### 1. 파라미터의 모양 — 표준은 없고 관례가 있다

```text
 Google AIP-132/160   ?filter=status = "open" AND price < 1000  &order_by=price desc, id
 JSON:API 1.1         ?filter[status]=open                       &sort=-created,title
 흔한 자체 관례        ?status=open&price_lt=1000                  &sort=-created_at
```

- Google AIP-132(List 메서드): `order_by`는 쉼표로 구분한 필드 목록, 기본 오름차순, `" desc"` 접미사로 내림차순. 남는 공백은 의미 없다(`"foo, bar desc"` = `" foo , bar desc "`). 하위 필드는 `.`.
- Google AIP-160(필터 문법)
  - 비교 `=`·`!=`·`<`·`>`·`<=`·`>=`, 논리 `AND`·`OR`, 부정 `NOT`·`-`, 탐색 `.`을 제공해야 한다(should). "has" 연산자 `:`는 제공해야 한다(must).
  - 문법에 안 맞거나 스키마에 안 맞는 필터는 `INVALID_ARGUMENT`로 거절해야 한다(should). "스키마에 안 맞는다"의 정의가 없는 필드·타입이 다른 값·enum 밖의 값 등이다. 검증을 이보다 느슨하게 하면 그 차이를 문서화해야 한다(must).
  - 서비스는 이 문법 위에 추가 구조·제한을 둘 수 있다(may). 예: 논리 연산자 개수 제한으로 "쿼리 오브 데스(queries of death)"를 막는다. 그런 제한은 분명히 문서화해야 한다(must).
  - 필드 없이 쓴 리터럴(`filter=abc`)을 일부 필드에서만 찾는다면, 어느 필드인지 문서화해야 한다(must).
- JSON:API 1.1
  - `sort`: 쉼표 구분, `-` 접두사면 내림차순(MUST). 서버가 요청된 정렬을 지원하지 않으면 400(MUST).
  - `filter` 파라미터 이름 묶음만 예약한다. 필터 전략은 정하지 않는다.
- 공통점: **서버가 고른 목록만 받고 나머지는 400**. 이것이 이 노트의 중심 결정이다.

### 2. 파라미터가 쿼리가 되는 길

```text
 ?filter=...&order_by=...
       │
       ▼
 [파서] 문법 검사 ──── 틀림 → 400 INVALID_ARGUMENT
       │  AST (필드, 연산자, 값)
       ▼
 [허용 목록] 필드·연산자·정렬 조합이 인덱스로 받쳐지나? ── 아님 → 400 (지원 목록 안내)
       │
       ▼
 [SQL 생성] 식별자 = 허용 목록의 고정 문자열, 값 = 바인딩 파라미터 (?)
       │
       ▼
 [DB] 인덱스 범위 스캔 + LIMIT
```

- *식별자(identifier)*: 열 이름·정렬 방향처럼 SQL 구조를 이루는 부분. JDBC `?`로 **바인딩할 수 없다**. 바인딩은 값 자리에만 된다.
  - `ORDER BY ?`에 `"id DESC"`를 바인딩하면 열 이름이 아니라 **문자열 상수**로 정렬한다. 상수는 행마다 같으니 정렬 효과가 없다. 에러도 안 난다(아래 실험).
  - 그래서 정렬·필터 필드는 허용 목록에서 꺼낸 **고정 문자열**로만 SQL에 넣는다. 사용자 문자열을 이어 붙이면 SQL 인젝션 통로가 된다.
- 필터 값은 바인딩한다. `status = ?`에 `"open"`.

### 실험 A: 정렬·필터 모양별 실행 계획 (PostgreSQL 17)

- 환경: PostgreSQL 17.11 전용 컨테이너(`--cpus=2`, 메모리 1GB, `work_mem` 4MB = 기본값), `product` 100만 행(89MB). 인덱스: `(created_at DESC, id DESC)`, `(category, price, id)`. `category`는 20종, `price`는 0~99,999.

```sql
CREATE INDEX product_created   ON product(created_at DESC, id DESC);
CREATE INDEX product_cat_price ON product(category, price, id);
```

(실험, PostgreSQL 17.11, 2026-10-04 — `EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)`, 시간은 실행마다 다르다)

```text
=== Q1 order_by=created_at desc (인덱스 있음)
Limit (actual time=0.077..0.090 rows=20 loops=1)
  ->  Index Scan using product_created on product (actual time=0.075..0.084 rows=20 loops=1)
Execution Time: 0.139 ms
=== Q2 order_by=name (인덱스 없음)
Limit (actual time=358.290..366.313 rows=20 loops=1)
  ->  Gather Merge (actual time=358.286..366.302 rows=20 loops=1)
        ->  Sort (actual time=352.712..352.715 rows=15 loops=3)
              Sort Key: name, id
              Sort Method: top-N heapsort  Memory: 27kB
              ->  Parallel Seq Scan on product (actual time=0.029..131.210 rows=333333 loops=3)
Execution Time: 366.446 ms
=== Q3 order_by=name + offset 200000
Limit (actual time=2857.263..2874.970 rows=20 loops=1)
  ->  Gather Merge (actual time=2498.754..2856.018 rows=200020 loops=1)
        ->  Sort (actual time=2443.661..2574.216 rows=67161 loops=3)
              Sort Key: name, id
              Sort Method: external merge  Disk: 16880kB
              Worker 0:  Sort Method: external merge  Disk: 17312kB
              Worker 1:  Sort Method: external merge  Disk: 15760kB
              ->  Parallel Seq Scan on product (actual time=0.028..110.978 rows=333333 loops=3)
Execution Time: 2879.601 ms
=== Q4 filter=category=7 order_by=price (복합 인덱스와 맞음)
Limit (actual time=0.114..0.172 rows=20 loops=1)
  ->  Index Only Scan using product_cat_price on product (actual time=0.112..0.164 rows=20 loops=1)
        Index Cond: (category = 7)
Execution Time: 0.236 ms
=== Q5b filter=price=12345 order_by=created_at desc (드문 값, price 단독 인덱스 없음)
Limit (actual time=67.449..76.000 rows=10 loops=1)
  ->  Gather Merge (actual time=67.444..75.961 rows=10 loops=1)
        ->  Sort (actual time=61.338..61.341 rows=3 loops=3)
              Sort Key: created_at DESC, id DESC
              Sort Method: quicksort  Memory: 25kB
              ->  Parallel Seq Scan on product (actual time=22.446..61.145 rows=3 loops=3)
                    Filter: (price = 12345)
                    Rows Removed by Filter: 333330
Execution Time: 76.107 ms
```

(Q2·Q3·Q5b의 `Workers Planned: 2`·`Workers Launched: 2` 줄, Q2·Q5b의 작업자별 `Sort Method` 줄, Q4의 `Heap Fetches: 0` 줄은 지면상 뺐다. 남긴 줄은 출력 그대로다)

- 관찰 1 (Q1 vs Q2) — 인덱스 순서와 같은 정렬은 20행만 읽었다(0.139ms). 인덱스 없는 열 정렬은 100만 행을 다 읽고 정렬했다(366ms, 약 2,600배). 사실 점검 재실행에서는 Q1 0.140ms·Q2 302ms·Q3 2,381ms였다 — 계획 모양과 `rows`는 같고 시간만 실행마다 다르다.
- 관찰 2 (Q2) — `LIMIT`이 있으면 PostgreSQL은 *top-N heapsort*를 쓴다. 상위 N개만 힙에 유지해 메모리는 27kB로 작다. 그래도 **읽기는 전부** 한다.
- 관찰 3 (Q3) — 정렬 + 깊은 offset이면 상위 200,020개를 힙에 담아야 하는데 `work_mem`(4MB)에 안 들어간다. 그러면 top-N heapsort를 **포기하고 받은 행 전체를 외부 병합 정렬**한다. 작업자 셋이 각자 받은 333,333행을 모두 디스크에 써서 합쳐 약 50MB, 2.9초. 200,020개만 정렬한 것이 아니다.
  - 근거: PostgreSQL 17 `src/backend/utils/sort/tuplesort.c`의 `puttuple_common`은 쌓인 행이 bound×2를 넘거나, `work_mem`이 찼을 때 쌓인 행이 bound보다 많을 때만 bounded heap으로 바꾼다. 4MB가 찼을 때 쌓인 행은 200,020개보다 훨씬 적어서 곧바로 테이프(디스크) 정렬로 넘어간다.
  - 판정자 재실행(같은 데이터, 작업자 없이 `trace_sort=on`, 로그는 일부만):

```text
LOG:  worker -1 switching to external sort with 15 tapes: CPU: user: 0.01 s, system: 0.01 s, elapsed: 0.02 s
LOG:  starting merge pass of 24 input runs on 15 tapes, 262 KB of memory for each input tape: CPU: user: 3.76 s, system: 0.07 s, elapsed: 3.87 s
LOG:  external sort of worker -1 ended, 6241 disk blocks used: CPU: user: 5.42 s, system: 0.13 s, elapsed: 5.61 s
Limit (actual time=5630.934..5630.950 rows=20 loops=1)
  ->  Sort (actual time=5489.369..5585.433 rows=200020 loops=1)
        Sort Key: name, id
        Sort Method: external merge  Disk: 49928kB
        ->  Seq Scan on product (actual time=0.087..211.555 rows=1000000 loops=1)
Execution Time: 5840.640 ms
```

  - 100만 행 전체(약 50MB)를 24개 조각으로 나눠 디스크에 쓴 뒤 병합했다. 같은 쿼리를 `OFFSET 2000`(bound 2,020)으로 바꾸면 `Sort Method: top-N heapsort  Memory: 339kB`였다(작업자 둘 334kB·338kB). 비용은 offset에 비례해 서서히 늘지 않는다. bound가 `work_mem`을 넘는 순간 "전체 정렬"로 뛴다. 메모리 한도와 스필은 [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md).
- 관찰 4 (Q4) — 필터 등호 열이 복합 인덱스 앞에, 정렬 열이 그 뒤에 있으면 `Index Only Scan` 하나로 끝난다(0.236ms).
- 관찰 5 (Q5b) — 필터 열에 맞는 인덱스가 없으면, 정렬 인덱스가 있어도 결과가 10건뿐인 쿼리가 전체를 훑었다(76ms). 정렬만이 아니라 **필터 × 정렬 조합**이 인덱스와 맞아야 한다.
- 관찰 6 (판정자 추가 실행) — 인덱스 순서를 `(price, category, id)`로 바꾸면(원래 인덱스를 지우고) 어떤가.

```text
=== Q4p filter=category=7 order_by=price (인덱스 (price, category, id))
Limit (actual time=0.108..0.146 rows=20 loops=1)
  ->  Index Only Scan using product_price_cat on product (actual time=0.106..0.140 rows=20 loops=1)
        Index Cond: (category = 7)
        Heap Fetches: 0
Execution Time: 0.188 ms
=== Q4q filter=category=99 order_by=price (0건, 같은 인덱스)
Limit (actual time=76.367..82.771 rows=0 loops=1)
  ->  Sort (actual time=76.364..82.767 rows=0 loops=1)
        Sort Key: price, id
        Sort Method: quicksort  Memory: 25kB
        ->  Gather (actual time=76.315..82.716 rows=0 loops=1)
              Workers Planned: 2
              Workers Launched: 2
              ->  Parallel Seq Scan on product (actual time=70.363..70.365 rows=0 loops=3)
                    Filter: (category = 99)
                    Rows Removed by Filter: 333333
Execution Time: 82.851 ms
```

  - 흔한 값(`category=7`, 5%)은 price 순서로 인덱스를 훑으며 category를 인덱스 안에서 걸러 금방 20개를 채웠다(0.188ms). 범위 스캔 하나로 그 구간만 읽는 Q4와는 다른 길이다.
  - 없는 값(`category=99`)은 플래너가 전체 훑기 + 정렬을 골랐다(82.851ms). 순서가 다른 인덱스는 "못 쓴다"가 아니라 **값의 분포에 따라 빠르기도 느리기도 하다**.
- 같은 쿼리 모양인 `filter=category=7 order_by=created_at desc`는 0.309ms였다(`category=7`이 5%라 정렬 인덱스를 따라가다 금방 20개를 채운다). 같은 모양도 값의 분포에 따라 계획과 비용이 달라진다([database/12-query-optimizer-and-explain](../../database/12-query-optimizer-and-explain/2-summary.md)).

### 실험 B: 인덱스 없는 정렬이 동시에 몰리면

- pgbench(PostgreSQL 17.11 내장), 같은 컨테이너, 각 10초. 쿼리마다 `OFFSET (random()*1000)::int`로 첫 몇 쪽을 무작위로.

(실험, PostgreSQL 17.11 + pgbench, 2026-10-04 — 1회씩, 2 CPU 제한 환경의 값)

```text
== q_idx   (ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 0~1000, 동시 8)
number of transactions actually processed: 29773
latency average = 2.685 ms
tps = 2979.738916 (without initial connection time)
== q_noidx (ORDER BY name, id LIMIT 20 OFFSET 0~1000, 동시 8)
number of transactions actually processed: 27
latency average = 3224.153 ms
tps = 2.481272 (without initial connection time)

[단독 idx] latency average = 1.150 ms
[단독 idx] tps = 3479.636069 (without initial connection time)
[noidx 4개와 동시 idx] latency average = 6.554 ms
[noidx 4개와 동시 idx] tps = 610.347837 (without initial connection time)
```

- 관찰 1 — 같은 "20개 주세요"인데 처리량이 약 1,200배 차이 났다(2,980 tps vs 2.5 tps). 사실 점검 재실행(각 5초, `-j 2`)은 3,518 vs 2.97 tps(약 1,180배)였다.
- 관찰 2 — 인덱스 없는 정렬 4개가 도는 동안, **인덱스를 타는 정상 요청**의 평균 지연이 1.150ms → 6.554ms, 처리량이 3,480 → 610 tps로 떨어졌다(재실행: 1.024 → 5.438ms, 3,906 → 736 tps). 비싼 쿼리는 자기만 느린 게 아니라 CPU·I/O를 나눠 쓰는 이웃을 느리게 한다.

### 실험 C: 정렬 파라미터를 바인딩하면, 허용 목록으로 해석하면

```text
-- PostgreSQL 17.11: 정렬을 값으로 바인딩
PREPARE p(text) AS SELECT id FROM product WHERE id < 5 ORDER BY $1 LIMIT 4;
EXECUTE p('id DESC');
 id
----
  1
  2
  3
  4                  ← 내림차순이 아니다. 상수로 정렬 = 정렬 없음, 에러도 없음

EXPLAIN (COSTS OFF) EXECUTE p('id DESC');
 Limit
   ->  Index Only Scan using product_pkey on product
         Index Cond: (id < 5)          ← 계획에 Sort 노드조차 없다
```

AIP-132 모양의 `order_by`를 허용 목록으로 해석하는 Java 코드(`Sort12.java`):

```java
static final Map<String, String> ALLOWED = Map.of(        // 인덱스가 받쳐 주는 조합만
    "created_at desc", "created_at DESC, id DESC",
    "created_at",      "created_at ASC, id ASC",
    "price",           "price ASC, id ASC");               // category 필터와 함께일 때만
String norm = String.join(",", Arrays.stream(orderBy.split(","))
        .map(s -> s.trim().replaceAll("\\s+", " ").toLowerCase()).toList());
String sql = ALLOWED.get(norm);
if (sql == null) throw new IllegalArgumentException("INVALID_ARGUMENT: order_by '" + orderBy + "' is not supported; ...");
if (norm.equals("price") && !filter.containsKey("category")) throw new IllegalArgumentException("... requires filter on category");
```

(실험, JDK 21.0.12, 2026-10-04)

```text
(없음)                               filter=[]        → ORDER BY created_at DESC, id DESC
"created_at desc"                  filter=[]        → ORDER BY created_at DESC, id DESC
"  created_at   DESC "             filter=[]        → ORDER BY created_at DESC, id DESC
"price"                            filter=[category] → ORDER BY price ASC, id ASC
"price"                            filter=[]        → 400 INVALID_ARGUMENT: order_by 'price' requires filter on category
"name"                             filter=[]        → 400 INVALID_ARGUMENT: order_by 'name' is not supported; supported: [created_at, created_at desc, price]
"created_at desc, id"              filter=[]        → 400 INVALID_ARGUMENT: order_by 'created_at desc, id' is not supported; supported: [created_at, created_at desc, price]
"price; DROP TABLE product--"      filter=[category] → 400 INVALID_ARGUMENT: order_by 'price; DROP TABLE product--' is not supported; supported: [created_at, created_at desc, price]
"(SELECT 1)"                       filter=[]        → 400 INVALID_ARGUMENT: order_by '(SELECT 1)' is not supported; supported: [created_at, created_at desc, price]
```

- 관찰 1 — 바인딩한 정렬은 조용히 무시됐다. 테스트 데이터가 우연히 id 순서면 "정렬이 된다"고 착각하기 쉽다.
- 관찰 2 — 허용 목록은 공백·대소문자를 정규화한 뒤 정확히 일치하는 것만 받는다. 인젝션 시도와 인덱스 없는 정렬이 같은 400으로 막혔다.
- 관찰 3 — `price` 정렬은 `category` 필터와 함께일 때만 허용했다. 인덱스 `(category, price, id)`가 받쳐 주는 조합이 그것뿐이다.
- 이 구현은 단순화다. 허용 조합이 많아지면 문자열 맵 대신 필드별 허용 표 + 조합 규칙으로 바꾼다.

### 3. 검색 — `LIKE '%…%'`는 B+Tree로 못 찾는다

```text
 name LIKE 'abc%'    앞이 고정 → B+Tree 범위 (text_pattern_ops 등 조건 있음)
 name ILIKE '%abc12%' 앞이 열림 → B+Tree 불가 → 전체 훑기
                     → 트라이그램 역색인(pg_trgm GIN) 또는 전문 검색 엔진
```

(실험, PostgreSQL 17.11 + pg_trgm 1.6, 같은 100만 행, 2026-10-04 — 각 계획의 위쪽 `Limit`·`Gather Merge`/`Sort` 줄과 `Workers`·`Heap Blocks`·`Index Cond` 줄은 뺐다)

```text
=== Q6 search: name ILIKE '%abc12%' (trgm 없음)
        ->  Parallel Index Scan using product_pkey on product (actual time=39.018..875.265 rows=11 loops=3)
              Filter: (name ~~* '%abc12%'::text)
              Rows Removed by Filter: 333322
Execution Time: 1299.773 ms
=== Q6 search: name ILIKE '%abc12%' (pg_trgm GIN)
        ->  Bitmap Heap Scan on product (actual time=3.128..3.778 rows=34 loops=1)
              Recheck Cond: (name ~~* '%abc12%'::text)
              Rows Removed by Index Recheck: 7
              ->  Bitmap Index Scan on product_name_trgm (actual time=3.052..3.052 rows=41 loops=1)
Execution Time: 4.046 ms
```

- *트라이그램(trigram)*: 문자열을 연속한 세 글자 조각으로 나눈 것. `pg_trgm` GIN 인덱스는 조각 → 행 목록의 역색인이다. 검색어 조각을 모두 가진 행만 후보로 뽑고(41행), 실제 패턴으로 다시 확인한다(7행 탈락).
- 인덱스 없이 1.3초, 트라이그램 GIN으로 4ms였다.
- 형태소·관련도 순위가 필요한 "검색"은 전문 검색 영역이다([database/46-full-text-search-and-analyzers](../../database/46-full-text-search-and-analyzers/2-summary.md)). API에서는 `filter`(정확한 조건)와 `q`/`search`(관련도 검색)를 다른 파라미터로 나누는 편이 계약이 명확하다(설계 판단).

### 4. 페이지네이션과 묶기

- 정렬을 바꿀 수 있으면 커서에 **그 정렬의 키들**이 들어가야 한다. `order_by=price`면 커서 = `(price, id)`.
- 토큰에 필터·정렬을 묶어, 다음 쪽 요청에서 바뀌면 400(AIP-158, [06-pagination](../06-pagination/2-summary.md)).
- 허용 정렬마다 유일 키로 끝나는지 확인한다(동률 깨기).

## 쓰이는 자료구조·알고리즘

- **복합 B+Tree 인덱스의 정렬 순서** — `(category, price, id)`는 category가 같은 행끼리 price, id 순으로 붙어 있다. 그래서 "등호 필터 → 정렬"이 범위 스캔 하나가 된다. 순서가 `(price, category, id)`면 그 구간이 한 덩어리가 아니다. 정렬 순서로 훑으며 인덱스 안에서 거를 수는 있지만, 비용이 값의 빈도에 좌우된다(실험 A 관찰 6). [database/09-index-design](../../database/09-index-design/2-summary.md), [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md).
- **Top-N 힙 정렬** — 크기 N의 힙으로 전체를 한 번 훑어 상위 N개를 남긴다. 메모리 O(N), 시간 O(전체 × log N). [data-structure/07-heap](../../data-structure/07-heap/2-summary.md).
- **외부 병합 정렬** — 메모리 한도를 넘으면 정렬된 조각을 디스크에 쓰고 병합한다. [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md).
- **역색인(트라이그램 GIN)** — 조각 → 게시 목록. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md).
- **필터 파서 → AST** — AIP-160 같은 문법을 재귀 하강 파서로 AST로 만든 뒤, 노드마다 허용 여부를 검사하고 바인딩 SQL로 바꾼다. 문자열 치환으로 SQL을 만들지 않는다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **화면·사용 사례에서 필요한 필터·정렬을 뽑는다** — "아무 열이나"가 아니라 실제로 쓰는 조합.
2. **조합마다 인덱스를 설계한다** — `(등호 필터 열, 정렬 열, id)`. `EXPLAIN`으로 Sort 노드·Seq Scan이 없는지 본다.
3. **허용 목록을 코드와 문서에 같은 출처로 둔다** — 지원 필드·연산자·정렬 조합. 그 밖은 400 + 지원 목록 안내(AIP-160 "문서화해야 한다", JSON:API "지원 안 하면 400").
4. **식별자는 허용 목록의 고정 문자열, 값은 바인딩.**
5. **비용 상한을 둔다** — `page_size` 상한, offset 깊이 상한, 필터 조건 수·`OR` 개수 상한, 쿼리 `statement_timeout`([database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md)).
6. **부분 문자열 검색은 별도 설계** — 트라이그램 인덱스나 검색 엔진. 없는 상태로 `LIKE '%…%'`를 열지 않는다.
7. **커서에 정렬 키를 넣고 토큰에 조건을 묶는다**(06).

### 2. 필터를 바인딩 SQL로 (Java, 단순화한 모양)

```java
// AIP-160의 아주 작은 부분집합: "필드 연산자 값" AND ... 만 지원
record Cond(String field, String op, String value) {}
static final Map<String, Set<String>> FILTERABLE = Map.of(
        "category", Set.of("="), "status", Set.of("="), "price", Set.of("<", ">=", "<=", ">"));

String toSql(List<Cond> conds, List<Object> binds) {
    StringJoiner where = new StringJoiner(" AND ");
    for (Cond c : conds) {
        Set<String> ops = FILTERABLE.get(c.field());
        if (ops == null || !ops.contains(c.op())) throw new BadRequest("filter on " + c.field() + " " + c.op() + " is not supported");
        where.add(c.field() + " " + c.op() + " ?");              // 식별자·연산자: 허용 목록에서 온 고정 문자열
        binds.add(c.field().equals("price") ? Integer.parseInt(c.value()) : c.value());  // 값: 타입 검사 후 바인딩
    }
    return where.length() == 0 ? "TRUE" : where.toString();
}
```

### 3. 진단

```sql
-- 느린 목록 쿼리 모양 찾기 (pg_stat_statements 확장이 켜져 있을 때)
SELECT calls, mean_exec_time, left(query, 120)
  FROM pg_stat_statements WHERE query ILIKE '%ORDER BY%' ORDER BY mean_exec_time DESC LIMIT 10;

-- 의심 모양 재현: Sort 노드·Seq Scan·external merge가 있으면 그 정렬/필터는 인덱스가 받쳐 주지 않는다
EXPLAIN (ANALYZE, BUFFERS) SELECT ... WHERE ... ORDER BY ... LIMIT 20;
```

- 접근 로그에서 `order_by`·`filter` 값 분포를 본다. 허용 목록 밖 요청(400)이 몰리면 문서·클라이언트를 고친다.

## 장애 시나리오와 대처

### 1. 임의 필드 정렬 허용 → 인덱스 없는 정렬로 DB 과부하 (⚠)

- **현상**: 관리자 화면의 "이름순" 클릭이나 크롤러 요청 뒤 DB CPU가 포화되고 다른 API까지 느려진다.
- **보이는 형태**: 느린 쿼리 로그에 `ORDER BY name` 등. 계획에 `Seq Scan` + `Sort`(top-N heapsort 또는 external merge). 정상 요청의 지연도 같이 오른다(실험 B: 1.150ms → 6.554ms).
- **원인**: `sort` 파라미터를 검사 없이 ORM 정렬로 넘겼다. 그 열에는 인덱스가 없다.
- **대처**: 허용 목록 + 400. 필요한 정렬은 인덱스를 만든 뒤 목록에 추가한다. 응급으로 `statement_timeout`, 해당 엔드포인트 속도 제한.

### 2. 정렬 + 깊은 offset → 디스크 스필

- **현상**: 특정 정렬의 뒤쪽 페이지가 수 초 걸리고 임시 파일이 쌓인다.
- **보이는 형태**: `Sort Method: external merge  Disk: …kB`(실험 Q3: 2.9초), `temp_files` 증가.
- **원인**: 깊은 offset이면 상위 offset + limit개를 담을 힙이 `work_mem`을 넘는다. 그러면 top-N heapsort를 포기하고 입력 전체를 외부 병합 정렬한다(PostgreSQL 17 `tuplesort.c`, 관찰 3).
- **대처**: 커서 페이지네이션, 정렬 인덱스, offset 깊이 상한. `work_mem` 전역 상향은 마지막 수단([database/41](../../database/41-sorting-and-aggregation/2-summary.md)).

### 3. 정렬을 바인딩 파라미터로 → 정렬이 조용히 안 된다

- **현상**: "최신순"을 골라도 목록 순서가 안 바뀐다. 에러는 없다.
- **보이는 형태**: SQL 로그에 `ORDER BY $1`. 계획에 Sort 노드가 없다(실험 C).
- **원인**: 식별자는 바인딩할 수 없다. 값으로 바인딩하면 상수 정렬이 된다.
- **대처**: 허용 목록 → 고정 문자열로 SQL 조립. 이를 피하려고 사용자 문자열을 이어 붙이면 인젝션이 된다([security 18-injection](../../security/18-injection/2-summary.md)).

### 4. 부분 문자열 검색 → 풀스캔

- **현상**: 검색창 입력마다 1초 이상 걸리고, 사용자가 많을수록 더 느려진다.
- **보이는 형태**: `Filter: (name ~~* '%…%')`, `Rows Removed by Filter`가 테이블 크기만큼(실험 Q6: 1.3초).
- **원인**: 앞이 열린 패턴은 B+Tree로 찾을 수 없다.
- **대처**: `pg_trgm` GIN(실험: 4ms), 검색어 최소 글자 수(뽑을 트라이그램이 없는 짧은 패턴은 인덱스 전체 스캔으로 퇴화한다, PostgreSQL 17 F.33), 전문 검색 엔진. 검색 파라미터를 필터와 분리하고 별도 속도 제한.

### 5. 드문 값 필터 × 다른 정렬 → 예측 못한 느림

- **현상**: 같은 엔드포인트가 어떤 필터 값에서만 느리다.
- **보이는 형태**: 결과는 몇 건인데 `Rows Removed by Filter`가 수십만(실험 Q5b: 10건에 76ms). 흔한 값(`category=7`)은 0.3ms.
- **원인**: 필터 열에 맞는 인덱스가 없거나, 정렬 인덱스를 따라가며 드문 값을 찾느라 많이 훑는다.
- **대처**: 허용 조합마다 `(필터 열, 정렬 열, id)` 인덱스. 조합이 너무 많으면 "이 정렬은 이 필터와 함께일 때만" 같은 규칙으로 줄인다(실험 C의 `price` 규칙).

## 핵심 문장

- 필터·정렬 파라미터를 여는 것은 클라이언트에게 쿼리 모양을 고르게 하는 것이다. 받는 조합은 인덱스가 받쳐 주는 것으로 제한하고 나머지는 400으로 거절한다.
- 실험에서 인덱스 순서 정렬은 0.139ms, 인덱스 없는 열 정렬은 366ms였고, 동시 부하에서는 처리량이 약 1,200배 차이 났다.
- 비싼 정렬은 자기만 느린 것이 아니다. 실험에서 인덱스 없는 정렬 4개가 정상 요청의 지연을 1.15ms에서 6.55ms로 올렸다.
- 열 이름·정렬 방향은 바인딩할 수 없다. 허용 목록의 고정 문자열로 넣고, 값만 바인딩한다.
- 부분 문자열 검색은 B+Tree로 못 찾는다. 트라이그램 역색인이나 검색 엔진을 따로 설계한다.

## 관련 주제·근거

- 선행
  - [06-pagination](../06-pagination/2-summary.md) — 정렬 키가 커서가 된다, 토큰에 조건 묶기
  - [database/09-index-design](../../database/09-index-design/2-summary.md) — 복합 인덱스 순서
- 후속·연결
  - [database/12-query-optimizer-and-explain](../../database/12-query-optimizer-and-explain/2-summary.md) · [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md) · [database/46-full-text-search-and-analyzers](../../database/46-full-text-search-and-analyzers/2-summary.md) · [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md)
  - [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md) — 비싼 엔드포인트 보호
  - [17-graphql](../17-graphql/2-summary.md) — 클라이언트가 쿼리 모양을 고르는 극단, 쿼리 비용 제한
  - [security/18-injection](../../security/18-injection/2-summary.md)
- 근거
  - Google AIP-132 Standard methods: List(`order_by` 문법·`" desc"`·공백 무시·`.` 하위 필드, `filter` 필드) <https://google.aip.dev/132>
  - Google AIP-160 Filtering(비교·논리·부정·탐색 should, `:` must, 잘못된 필터 `INVALID_ARGUMENT`, 필드 존재·타입 must, 대상 필드 문서화 must, queries of death 제한 may) <https://google.aip.dev/160>
  - JSON:API 1.1 "Sorting"(`sort`, `-` 내림차순 MUST, 미지원 400 MUST), "Filtering"(`filter` 파라미터 묶음 예약, 전략 미정) <https://jsonapi.org/format/>
  - PostgreSQL 17 문서 — 14.1 Using EXPLAIN, F.33 pg_trgm(트라이그램 인덱스로 `LIKE`·`ILIKE` 검색, 왼쪽 고정 불필요, 뽑을 트라이그램이 없는 패턴은 인덱스 전체 스캔으로 퇴화), `work_mem` 기본 4MB(실험 `SHOW work_mem`으로 확인) <https://www.postgresql.org/docs/17/pgtrgm.html>
- 실험 목록
  - 실험 A: Q1~Q6 정렬·필터·검색 모양별 `EXPLAIN (ANALYZE, BUFFERS)` — `sort12.sql`·`sort12-explain.sh`·`sort12-explain2.sh`, PostgreSQL 17.11 전용 컨테이너, 100만 행
  - 실험 B: pgbench 동시 8 인덱스 정렬 vs 비인덱스 정렬, 비인덱스 4개와 동시 인덱스 4개 — PostgreSQL 17.11 내장 pgbench, 각 10초 1회. 사실 점검 재실행: `pgbench -n -T 5 -j 2 -c 8|4 -f q.sql`(q = 위 헤더의 `SELECT id, name FROM product ORDER BY … LIMIT 20 OFFSET (random()*1000)::int`), 비인덱스 4개는 7초 동안 뒤에서 함께 돌림
  - 판정자 추가(2026-10-04, PostgreSQL 17.11 전용 컨테이너, 같은 `sort12.sql`): Q3을 `trace_sort=on`·작업자 없이 다시 실행, `OFFSET 2000` 비교, 인덱스를 `(price, category, id)`로 바꾼 Q4p·Q4q
  - 실험 C: `ORDER BY $1` 바인딩(psql `PREPARE`), 허용 목록 order_by 해석 — `Sort12.java`, JDK 21.0.12
