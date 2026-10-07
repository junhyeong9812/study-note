# data-engineering/03-dimensional-modeling — 차원 모델링: 팩트·차원·grain 선언 — 정리 (힌트)

## 해결하는 문제

웨어하우스에 운영 DB의 정규화된 테이블을 그대로 옮기면, 분석가가 질문마다 조인 여러 개를 직접 짜야 한다. 그 과정에서 합계가 조용히 틀린다.

```text
  "9월 지역별 매출과 배송비"를 정규화된 표로 뽑으면 (예시)
  orders ⋈ order_items ⋈ customers ⋈ addresses ⋈ regions ⋈ …
  → 조인 하나만 잘못 붙여도 배송비가 상세 줄 수만큼 곱해진다 (실험: 1,350,000 → 2,700,000)
```

- 해법: 분석용 모양을 따로 정한다. 측정값은 **팩트**에, 설명은 **차원**에 둔다. 그리고 팩트 한 행의 뜻(**grain**)을 먼저 선언한다.
  - *팩트 테이블*: 업무 사건(주문 상세 한 줄, 결제 한 건)의 숫자 측정값과 차원 키를 담는 테이블.
  - *차원 테이블*: 누가·무엇을·어디서·언제를 설명하는 넓은 테이블. 리포트의 그룹·필터 기준이 된다.
  - *grain*: 팩트 테이블 한 행이 정확히 무엇을 나타내는지에 대한 선언. "주문 상세 1줄 = 1행"처럼 쓴다.
    - 흔한 오해: "grain = 시간 단위(일·월)". 시간은 grain의 한 축일 뿐이다. "고객별·상품별·일별 1행"처럼 여러 축의 조합이다.

쉬운 예: 반 성적표.
- "학생 한 명의 한 과목 점수 = 한 줄"로 정했으면, 반 평균은 줄을 다 더해 줄 수로 나누면 된다.
- 같은 표에 "학생별 총점" 줄을 끼워 넣으면, 다 더하는 순간 점수가 두 번 들어간다.

똑같은 구조다.\
Kimball Group은 grain 선언을 "the pivotal step"이라 부르고, "different grains must not be mixed in the same fact table"이라고 쓴다(Grain 페이지).

실무 예:
- 주문(배송비) 팩트와 주문 상세(상품 매출) 팩트를 주문 번호로 바로 조인했더니 배송비 합계가 2배.
- 신규 상품이 아직 상품 차원에 없어서 inner join에서 그 매출이 빠짐(에러 없음).

## 동작·원리

### 1. 스타 스키마

```text
                    dim_date
                 (date_key, full_date, month, 공휴일 …)
                        │
   dim_customer ────── fct_order_line ────── dim_product
   (customer_key,        grain: 주문 상세 1줄     (product_key, sku,
    customer_id,         ─────────────────        category …)
    region …)            order_no  (퇴화 차원)
                         date_key, customer_key, product_key   ← 차원 키
                         qty, sales                            ← 측정값
```

- 가운데 팩트, 둘레에 차원이 하나씩 붙어 별 모양이다. Kimball Group은 관계형 DB에 구현한 차원 모델을 *스타 스키마*라고 부른다(Star Schemas and OLAP Cubes 페이지).
- 차원은 넓고 평평한(비정규화된) 테이블이다. 낮은 카디널리티의 텍스트 속성이 많다(Dimension Table Structure 페이지).
- *퇴화 차원(degenerate dimension)*: 차원 테이블 없이 팩트에 들어가는 키. 주문 번호처럼 설명 속성은 없지만 묶는 기준이 되는 값.
- *스노우플레이크*: 차원의 계층(상품 → 카테고리 → 부서)을 정규화해 2차 테이블로 쪼갠 모양. Kimball Group은 사용자가 이해·탐색하기 어렵고 성능에 불리할 수 있어 피하라고 하며, 평평한 차원과 담긴 정보는 같다고 쓴다(Snowflaked Dimensions 페이지).
- DDIA 1판 3장 "Stars and Snowflakes: Schemas for Analytics" 절도 같은 구분을 다룬다(절 제목은 출판사 목차로 확인).

### 2. 4단계 설계와 grain

```text
  1. 업무 프로세스 고르기     "주문 접수"
  2. grain 선언               "주문 상세 1줄 = 1행"      ← 여기가 설계의 계약
  3. 차원 정하기               날짜·고객·상품  (grain에서 한 값으로 정해지는 것만)
  4. 팩트(측정값) 정하기       qty, sales      (grain에 맞는 숫자만)
```

- Kimball Group 4단계 설계(Four-Step Dimensional Design Process 페이지): 업무 프로세스 → grain 선언 → 차원 → 팩트.
- grain은 차원·팩트를 고르기 **전에** 선언한다. 후보 차원·팩트는 grain과 맞아야 한다(Grain 페이지).
- 배송비는 "주문 1건"에 한 번 붙는 숫자다. "주문 상세 1줄" grain과 그대로는 맞지 않는다. 선택지는 둘이다.
  - 업무 규칙(금액 비례 등)으로 상세 줄에 **배분**해 상세 팩트에 넣는다. Kimball Group은 이쪽을 우선 권하고, 헤더 수준 팩트 테이블은 성능 이점이 있을 때만 만들라고 쓴다(Allocated Facts 페이지).
  - 배분 규칙이 아직 없으면 별도 팩트(`fct_order`, grain: 주문 1건)로 둔다. 이 노트의 실험은 이 모양이다.
- grain이 다른 팩트는 별도 물리 테이블이다(Grain 페이지). 섞으면 아래 실험처럼 합계가 부푼다.

| 팩트 테이블 종류(Kimball) | grain | 예 |
|---|---|---|
| 트랜잭션 | 사건 한 번 | 주문 상세 한 줄, 결제 한 건 |
| 주기 스냅샷 | 대상 하나 × 정해진 기간 하나(일·월) | 계좌 1개·하루 1행의 일말 잔액 |
| 누적 스냅샷 | 프로세스 하나(시작~끝) | 주문 한 건의 접수·출고·배송 일자 |

### 3. 가산·반가산·비가산

```text
  sales      주문 상세 1줄의 매출   → 어느 차원으로 더해도 된다         가산
  balance    계좌 일말 잔액          → 계좌끼리는 더해도, 날짜끼리는 X    반가산
  conv_rate  일별 전환율            → 어느 축으로도 더하면 안 된다        비가산
```

- Kimball Group(Additive, Semi-Additive, and Non-Additive Facts 페이지)
  - 가산: 팩트에 연결된 어느 차원으로든 합할 수 있다.
  - 반가산: 일부 차원으로만 합할 수 있다. 잔액은 시간을 빼고는 합할 수 있다.
  - 비가산: 비율처럼 합할 수 없다. 가산인 구성 요소(분자·분모)를 저장해 각각 합한 뒤 마지막에 나눈다.

### 4. 공통 차원과 drill-across

```text
  fct_order_line (grain: 상세 1줄)        fct_order (grain: 주문 1건)
        │ 월·지역으로 집계                       │ 월·지역으로 집계
        ▼                                       ▼
   (2026-09, busan, sales 2,018,200)     (2026-09, busan, fee 450,000)
        └──────────── 같은 행 머리(월·지역)로 맞붙임 ────────────┘
```

- *공통 차원(conformed dimension)*: 여러 팩트가 같은 컬럼 이름·같은 값 도메인으로 공유하는 차원. 서로 다른 팩트의 결과를 한 리포트의 같은 행에 맞붙일 수 있다(Conformed Dimensions 페이지).
- *drill-across*: 팩트마다 따로 질의해 같은 공통 속성으로 집계한 뒤, 그 결과끼리 맞붙이는 것(Drilling Across 페이지).
- Kimball Group은 BI 앱이 두 팩트를 팩트의 외래 키로 직접 조인하면 안 된다고 쓴다. 결과의 카디널리티를 통제할 수 없어 틀린 결과가 나온다(Multipass SQL to Avoid Fact-to-Fact Table Joins 페이지).

### 실험: grain이 다른 팩트 조인, grain을 섞은 팩트, drill-across

환경: 이 호스트(i7-13700HX), `postgres:17`(PostgreSQL 17.11) 일회용 컨테이너 `--cpus=2 --network none`, psql. 주문 600건(`fct_order`, 배송비 0 또는 3,000), 상세 1,200줄(`fct_order_line`, 주문당 1~3줄), 고객 90명(지역 3), 상품 40개.

```text
  0. 진짜 합계          orders 600 | lines 1200 | shipping 1,350,000 | sales 12,217,500

  1. fct_order ⋈ fct_order_line ON order_no 후 SUM
                       shipping_joined 2,700,000 | sales_joined 12,217,500 | inflate_ratio 2.00

  2. 한 팩트에 상세 줄 + 주문 합계 줄(line_no=0)을 섞음
                       mixed_sum 24,435,000 | ratio 2.00

  3. drill-across (팩트별로 월·지역 집계 → FULL JOIN)
                       2026-09 | busan | 2,018,200 | 450,000
                       2026-09 | daegu | 4,055,500 | 450,000
                       2026-09 | seoul | 6,143,800 | 450,000      합 12,217,500 / 1,350,000 ✔
```

- 1: 상세 매출은 맞지만 배송비가 주문의 상세 줄 수만큼 복제됐다. 이 데이터에서는 배송비가 붙은 주문의 평균 상세 줄 수가 2라 비율이 2.00이 되었다(배송비 가중 평균 줄 수 = 2,700,000 / 1,350,000). 비율은 데이터의 줄 수 분포에 따라 달라진다.
- 2: 상세 줄과 그 합계 줄이 한 테이블에 있으면 `SUM` 하나가 같은 돈을 두 번 센다(커리큘럼 ⚠ "주문 합계가 2배").
- 3: 팩트마다 따로 집계한 뒤 붙이면 두 합계 모두 진짜와 같다.
- 조인 팬아웃의 일반 구조는 [database/04](../../database/04-sql-joins-and-aggregation/2-summary.md) §6에 있다. 여기서는 그 원인이 "grain 선언 위반"이라는 점이 새롭다.

### 5. 차원 키 매칭 실패와 "Unknown" 행

```text
  fct_order_line                     dim_product
  product_key = 7  ─────────────►    7  book
  product_key = NULL ──── ✗ ───      (신규 상품이 아직 차원에 없음)
                                     -1 Unknown   ← 여기를 가리키게 적재하면 조인에서 안 빠진다
```

- Kimball Group: 팩트의 외래 키에는 NULL을 두지 않는다. 차원에 "unknown·not applicable"을 뜻하는 기본 행과 그 대리 키를 두고 그것을 가리킨다(Nulls in Fact Tables 페이지).
- 차원 속성의 NULL도 "Unknown" 같은 문자열로 바꾼다. DB마다 NULL의 그룹·필터 처리가 달라서다(Null Attributes in Dimensions 페이지).
- 팩트가 차원보다 먼저 도착하면 자연 키만 채운 자리표시 차원 행을 만들고, 나중에 설명이 오면 Type 1로 덮어쓴다(Late Arriving Dimensions 페이지).

### 실험: 차원 키 누락 + inner join

같은 환경. 차원에 없는 신규 상품 매출 20행(각 50,000, 합 1,000,000)을 `product_key = NULL`로 적재했다.

```text
  fact_total 13,217,500 | inner_join_total 12,217,500 | left_join_total 13,217,500

  카테고리별 (inner join):  book 2,271,050 / food 3,819,700 / tool 3,820,000 / toy 2,306,750   ← 100만이 흔적 없이 빠짐
  NULL 대신 -1(Unknown)으로 적재한 뒤 inner join:  위 넷 + Unknown 1,000,000 → 합 13,217,500
```

- inner join은 에러 없이 1,000,000을 뺐다. 카테고리별 표만 보면 빠진 줄을 알 수 없다(커리큘럼 ⚠).
- `-1` 행을 가리키게 적재하면 inner join을 써도 합계가 맞고, "Unknown"이라는 묶음으로 문제가 눈에 보인다.

### 실험: 비율 지표를 SUM·AVG

같은 환경. 일별 세션·주문 3일치: (100, 10), (10,000, 200), (50, 25).

```text
  sum_of_rates 0.62 | avg_of_rates 0.2067 | ratio_of_sums 0.0232
```

- 일별 전환율(0.10, 0.02, 0.50)을 더하면 0.62, 평균 내면 0.2067이다. 3일 전체 전환율은 235 / 10,150 = 0.0232다.
- 평균은 세션이 50인 날과 10,000인 날을 같은 무게로 센다. 분자·분모를 각각 합한 뒤 나눠야 한다(커리큘럼 ⚠ "비율 지표를 SUM → 의미 없는 숫자").

## 쓰이는 자료구조·알고리즘

- **스타 조인과 해시 조인** — PostgreSQL 플래너는 조인마다 중첩 루프·병합·해시 조인 가운데 하나를 고른다(PostgreSQL 17 문서 50.5). 이 실험의 스타 질의에서는 작은 차원을 필터한 뒤 해시 테이블로 만들고, 큰 팩트를 훑으며 탐색하는 해시 조인이 골라졌다. 실험 계획(PostgreSQL 17.11, 팩트 100만 행): `Hash Join`의 `Hash` 쪽에 `dim_product`(10행)·`dim_customer`(30행)가 올라갔다([database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md), [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **비트맵** — 팩트의 외래 키 인덱스 여러 개를 비트맵으로 바꿔 AND 한다. 같은 실험에서 `product_key = 4 AND customer_key = 8`이 `BitmapAnd`(두 `Bitmap Index Scan`) → `Bitmap Heap Scan`으로 실행됐다([data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md), [database/40](../../database/40-filters-and-specialized-indexes/2-summary.md)).
- **정렬 병합** — Kimball Group은 drill-across의 결과 맞붙이기를 공통 속성에 대한 sort-merge로 설명한다(Drilling Across 페이지). SQL에서는 `FULL JOIN … USING (공통 속성)`으로 결합한다. 이것은 논리 연산이고, 실제 조인 알고리즘(병합·해시 등)은 실행 계획이 정한다([algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)).
- **해시 집계** — `GROUP BY month, region`([database/41](../../database/41-sorting-and-aggregation/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 설계: grain 문장을 먼저 쓴다

```text
  fct_order_line : "주문 상세 1줄 = 1행"      측정값: qty, sales            차원: 날짜·고객·상품, 퇴화: order_no
  fct_order      : "주문 1건 = 1행"          측정값: shipping_fee          차원: 날짜·고객,      퇴화: order_no
  fct_session    : "일·채널별 1행"           측정값: sessions, orders       (전환율은 저장하지 않고 계산)
```

- 측정값마다 "이 숫자는 grain 한 행에 한 번만 생기나?"를 묻는다. 아니면 다른 팩트로 보낸다.
- Kimball Group은 header/line 구조에서 헤더 수준의 차원 키·퇴화 차원을 상세 팩트에 내려 두라고 쓴다(Header/Line Fact Tables 페이지). 헤더 수준의 **측정값**(배송비)은 값을 그대로 복사해 내리면 줄 수만큼 복제된다. 업무 규칙으로 줄마다 나눠(배분) 내리거나, 별도 팩트로 둔다(Allocated Facts 페이지).

### 2. 적재: 키 매칭 실패를 -1로

```sql
-- 차원에 기본 행
INSERT INTO dim_product VALUES (-1, NULL, 'Unknown');

-- 팩트 적재: 자연 키 → 대리 키, 못 찾으면 -1
INSERT INTO fct_order_line(order_no, line_no, date_key, customer_key, product_key, qty, sales)
SELECT s.order_no, s.line_no, s.date_key, s.customer_key,
       coalesce(p.product_key, -1), s.qty, s.sales
FROM stg_order_line s
LEFT JOIN dim_product p ON p.sku = s.sku;
```

- `-1`로 들어간 행 수를 적재 지표로 남긴다. 늘면 차원 적재가 늦거나 키 형식이 바뀐 것이다.

### 3. 질의: 두 팩트는 따로 집계한 뒤 붙인다

```sql
WITH s AS (SELECT d.month, c.region, sum(l.sales) AS sales
           FROM fct_order_line l JOIN dim_date d USING (date_key) JOIN dim_customer c USING (customer_key)
           GROUP BY 1, 2),
     f AS (SELECT d.month, c.region, sum(o.shipping_fee) AS fee
           FROM fct_order o JOIN dim_date d USING (date_key) JOIN dim_customer c USING (customer_key)
           GROUP BY 1, 2)
SELECT month, region, sales, fee FROM s FULL JOIN f USING (month, region);
```

### 4. 검증 쿼리

```sql
-- grain 위반: 선언한 grain 키로 중복이 있나
SELECT order_no, line_no, count(*) FROM fct_order_line GROUP BY 1, 2 HAVING count(*) > 1;

-- 조인 손실: inner join 전후 합계가 같은가
SELECT (SELECT sum(sales) FROM fct_order_line)                                     AS fact_total,
       (SELECT sum(sales) FROM fct_order_line JOIN dim_product USING (product_key)) AS joined_total;
```

- grain 키에 `PRIMARY KEY`·`UNIQUE` 제약을 걸 수 있으면 건다. 웨어하우스 제품에 따라 제약을 강제하지 않는 경우가 있다(예: ClickHouse의 PRIMARY KEY는 유일성 제약이 아니다 — [database/45](../../database/45-clickhouse-mergetree/2-summary.md)). 그때는 위 쿼리를 적재 후 검사로 돈다(이 영역 [10](../10-data-quality-and-data-observability/2-summary.md)).

### 5. 앱 코드에서 비율 계산 (Java 21)

```java
record Daily(long sessions, long orders) {}

static double conversion(List<Daily> days) {          // 분자·분모를 각각 합한 뒤 나눈다
    long s = days.stream().mapToLong(Daily::sessions).sum();
    long o = days.stream().mapToLong(Daily::orders).sum();
    return s == 0 ? Double.NaN : (double) o / s;
}
// 실험 데이터: (100,10), (10000,200), (50,25) → 235 / 10150 = 0.0232
```

## 장애 시나리오와 대처

### 1. grain이 섞인 팩트 → 주문 합계가 2배 (⚠ 커리큘럼)

- **현상**: 대시보드 9월 매출이 결제 DB 합계의 2배.
- **보이는 형태**: 팩트에 `line_no = 0`인 "합계 줄"이 섞여 있다. grain 키 중복 검사는 통과(키가 다르니까). `SUM(sales)` 비율 2.00(실험).
- **원인**: 한 팩트에 서로 다른 grain(상세 줄 + 주문 합계)을 넣었다.
- **대처**: grain 문장을 문서·테이블 주석에 적는다. 합계 줄은 별도 집계 팩트로 뺀다. 적재 후 원천 합계와 대조한다.

### 2. 두 팩트를 직접 조인 → 주문 단위 숫자가 부푼다

- **현상**: 지역별 배송비 리포트가 실제의 2배(실험: 1,350,000 → 2,700,000).
- **보이는 형태**: 같은 리포트의 상품 매출은 맞다. 배송비만 부푼다. 상세 줄이 많은 주문이 많은 지역일수록 더 부푼다.
- **원인**: 주문 1건 grain의 값이 주문 상세 grain과 조인되며 줄 수만큼 복제됐다.
- **대처**: drill-across — 팩트마다 공통 차원으로 따로 집계한 뒤 맞붙인다. BI 도구 시맨틱 층에서 팩트-팩트 조인을 막는다.

### 3. 차원 키 매칭 실패 + inner join → 매출이 조용히 준다 (⚠ 커리큘럼)

- **현상**: 신상품 출시 주에 카테고리별 매출 합이 결제 합보다 적다.
- **보이는 형태**: 실험처럼 `fact_total 13,217,500 / inner_join_total 12,217,500`. 카테고리 표에는 빠진 흔적이 없다.
- **원인**: 상품 차원 적재가 팩트보다 늦어 키가 NULL로 들어갔고, inner join이 그 행을 버렸다.
- **대처**: 매칭 실패는 `-1`(Unknown) 행으로 적재한다. 늦게 온 차원은 자리표시 행을 만들었다가 Type 1로 채운다. `-1` 행 수를 지표로 감시한다.

### 4. 비율 지표를 SUM·AVG → 의미 없는 숫자 (⚠ 커리큘럼)

- **현상**: 월간 전환율이 62%로 나온다.
- **보이는 형태**: 일별 전환율 컬럼을 `SUM`(0.62) 또는 `AVG`(0.2067). 실제 0.0232.
- **원인**: 비가산 지표를 더하거나 같은 무게로 평균 냈다.
- **대처**: 팩트에는 분자·분모(주문 수·세션 수)를 저장한다. 비율은 집계 뒤 마지막에 계산한다. BI 시맨틱 층에서 비율 컬럼의 기본 집계를 막는다.

### 5. 반가산 지표를 날짜로 합산 → 잔액이 수십 배

- **현상**: 월말 잔액 리포트가 실제 잔액의 수십 배.
- **보이는 형태**: 주기 스냅샷 팩트(일말 잔액)를 월 단위 `SUM`. 잔액이 한 달 내내 같았다면 30일 합은 정확히 30배다(예시).
- **원인**: 잔액은 시간 축으로 더할 수 없는 반가산 지표다.
- **대처**: 시간 축은 "기간 마지막 날 값" 또는 평균으로 집계한다. 계좌·지점 축으로는 합해도 된다.

## 핵심 문장

- 차원 모델은 측정값을 팩트에, 설명을 차원에 두고, 팩트 한 행의 뜻(grain)을 먼저 선언한다. grain은 설계의 계약이다.
- grain이 다른 숫자를 한 팩트에 섞거나 두 팩트를 직접 조인하면 합계가 부푼다(실험: 배송비 2.00배, 섞인 팩트 2.00배). 팩트마다 따로 집계한 뒤 공통 차원으로 맞붙인다(drill-across).
- 차원 키 매칭에 실패한 팩트를 NULL로 두면 inner join이 에러 없이 버린다(실험: 1,000,000 소실). 차원에 Unknown(-1) 행을 두고 그것을 가리키게 적재한다.
- 가산 지표는 어느 축으로든, 반가산은 일부 축으로만 더한다. 비율 같은 비가산 지표는 분자·분모를 저장해 합한 뒤 나눈다.
- PostgreSQL 17 실험에서 스타 질의는 작은 차원으로 만든 해시 테이블(`Hash Join`)로, 팩트의 여러 외래 키 조건은 인덱스 비트맵의 AND(`BitmapAnd`)로 실행됐다. 계획은 플래너가 데이터·통계로 고르므로 다른 데이터에서는 달라질 수 있다.

## 관련 주제·근거

- 선행
  - [02-oltp-olap-and-warehouse](../02-oltp-olap-and-warehouse/2-summary.md) — 웨어하우스와 마트
  - [database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md) — 조인 팬아웃, NULL과 집계
- 연결
  - [database/03-normalization](../../database/03-normalization/2-summary.md) — 차원은 의도적으로 비정규화한 테이블
  - [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md) · [database/40-filters-and-specialized-indexes](../../database/40-filters-and-specialized-indexes/2-summary.md) · [database/45-clickhouse-mergetree](../../database/45-clickhouse-mergetree/2-summary.md)
  - [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- 후속
  - [04-slowly-changing-dimensions](../04-slowly-changing-dimensions/2-summary.md) — 차원 속성이 바뀔 때
  - [10-data-quality-and-data-observability](../10-data-quality-and-data-observability/2-summary.md) · [13-data-vault](../13-data-vault/2-summary.md)
  - [data-analysis](../../data-analysis/README.md) — 만든 지표를 읽는 법
- Kimball Group "Dimensional Modeling Techniques" <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/> 하위 페이지(2026-10-07 열람): Grain, Four-Step Dimensional Design Process, Fact Table Structure, Dimension Table Structure, Star Schemas and OLAP Cubes, Snowflaked Dimensions, Additive/Semi-Additive/Non-Additive Facts, Transaction·Periodic Snapshot·Accumulating Snapshot Fact Tables, Conformed Dimensions, Drilling Across, Multipass SQL to Avoid Fact-to-Fact Table Joins, Header/Line Fact Tables, Allocated Facts, Degenerate Dimensions, Nulls in Fact Tables, Null Attributes in Dimensions, Late Arriving Dimensions. 『The Data Warehouse Toolkit』 3판(Wiley, 2013)의 장 번호는 `[?]`.
- Kleppmann, DDIA 1판(2017) 3장 "Stars and Snowflakes: Schemas for Analytics" — 절 제목은 출판사 목차(Internet Archive 2025-01-05 사본)로 확인.
- 실험(이 호스트 i7-13700HX, `--cpus=2 --network none`, PostgreSQL 17.11)
  - 주문 600·상세 1,200: 팩트-팩트 조인 배송비 1,350,000 → 2,700,000, grain 섞인 팩트 12,217,500 → 24,435,000, drill-across 합계 일치.
  - 차원 키 NULL 20행(1,000,000): inner 12,217,500 vs left 13,217,500, `-1` 적재 후 Unknown 묶음.
  - 비율: SUM 0.62, AVG 0.2067, 합의 비 0.0232.
  - 팩트 100만 행 + FK 인덱스: 스타 질의 계획 `Hash Join`(차원이 Hash 쪽), 두 FK 조건 `BitmapAnd`(합성 데이터의 키 상관 때문에 스타 질의 결과는 0행 — 계획 모양만 본다).
