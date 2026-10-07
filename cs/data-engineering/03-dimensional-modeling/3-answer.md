# data-engineering/03-dimensional-modeling — 정답

## 정답

### 1. 차원 모델과 grain 선언

- 정규화된 운영 테이블은 쓰기에 맞춘 모양이다. 분석가가 질문마다 조인 여러 개를 직접 짜야 하고, 조인 하나를 잘못 붙이면 합계가 조용히 틀린다.
- 차원 모델은 측정값(팩트)과 설명(차원)을 나눠, 질의 모양을 "팩트 + 차원 몇 개 조인 + GROUP BY"로 고정한다.
- grain을 먼저 선언하는 이유: 후보 차원·팩트가 grain과 맞는지 판정하는 기준이기 때문이다. Kimball Group은 grain 선언을 "binding contract"라 부르고, grain이 다른 숫자는 별도 물리 테이블에 두라고 한다(Grain 페이지).

### 2. 스타 스키마

```text
           dim_date
              │
  dim_customer ── fct_order_line ── dim_product
                  grain: 주문 상세 1줄
                  order_no (퇴화 차원)
                  date_key, customer_key, product_key (차원 키)
                  qty, sales (측정값)
```

- 차원 키·측정값은 팩트에, 설명 속성은 차원에 둔다. 주문 번호처럼 설명 속성이 없는 키는 팩트에 퇴화 차원으로 둔다.
- 스노우플레이크: 차원의 계층(상품 → 카테고리 → 부서)을 정규화해 2차 테이블로 쪼갠다.
- Kimball Group이 피하라는 이유: 사용자가 이해·탐색하기 어렵고 질의 성능에 불리할 수 있다. 평평한 차원과 담긴 정보는 같다(Snowflaked Dimensions 페이지).

### 3. grain이 다른 팩트 조인

- 실험: `shipping_joined 2,700,000`, `inflate_ratio 2.00`. 상품 매출(12,217,500)은 그대로다.
- 이유: 주문 1건의 배송비가 그 주문의 상세 줄 수만큼 복제된다. 이 데이터는 주문당 1~3줄이고, 배송비가 붙은 주문의 평균 줄 수가 2라 2.00이 되었다.
- 비율은 데이터에 따라 바뀐다. 상세 줄 수 분포와 배송비가 붙은 주문의 분포가 달라지면 2.00이 아니다. "정확히 2배"는 원인을 특정하는 단서가 못 된다.

### 4. drill-across

```sql
WITH s AS (SELECT d.month, c.region, sum(l.sales) AS sales
           FROM fct_order_line l JOIN dim_date d USING (date_key) JOIN dim_customer c USING (customer_key)
           GROUP BY 1, 2),
     f AS (SELECT d.month, c.region, sum(o.shipping_fee) AS fee
           FROM fct_order o JOIN dim_date d USING (date_key) JOIN dim_customer c USING (customer_key)
           GROUP BY 1, 2)
SELECT month, region, sales, fee FROM s FULL JOIN f USING (month, region);
```

- 이름: drill-across. 팩트마다 따로 집계한 뒤 같은 행 머리로 맞붙인다.
- 실험: busan 2,018,200 / 450,000, daegu 4,055,500 / 450,000, seoul 6,143,800 / 450,000. 합 12,217,500 / 1,350,000으로 진짜와 같다.
- 전제: 두 팩트가 **공통 차원**(같은 컬럼 이름·같은 값 도메인의 월·지역)을 써야 한다. 한쪽은 `region='Seoul'`, 다른 쪽은 `'서울'`이면 같은 행에 붙지 않는다.

### 5. 차원 키 누락

- 실험: `fact_total 13,217,500`, `inner_join_total 12,217,500`, `left_join_total 13,217,500`.
- 카테고리별 표(inner join)에는 book·food·tool·toy 네 줄만 나오고, 1,000,000이 빠진 흔적이 없다.
- Kimball 방식: 팩트 외래 키에 NULL을 두지 않고, 차원의 Unknown 행(`-1`)을 가리키게 적재한다(Nulls in Fact Tables 페이지). 바꾼 뒤 inner join 합계는 13,217,500이고 카테고리 표에 `Unknown | 1000000`이 나타난다.

### 6. 가산·반가산·비가산

| 종류 | 예 | 더할 수 있는 축 |
|---|---|---|
| 가산 | 주문 상세 매출 | 어느 차원이든 |
| 반가산 | 계좌 일말 잔액 | 계좌·지점은 되고 시간은 안 됨 |
| 비가산 | 전환율·단가 | 더하지 않는다 |

- 일별 전환율 0.10, 0.02, 0.50 → SUM 0.62, AVG 0.2067.
- 올바른 3일 전환율: (10 + 200 + 25) / (100 + 10,000 + 50) = 235 / 10,150 = 0.0232.
- 원칙: 분자·분모를 저장해 각각 합한 뒤 마지막에 나눈다(Kimball, Additive/Semi-Additive/Non-Additive Facts 페이지).

### 7. 스타 조인의 실행 계획

- 실험(팩트 100만 행, FK 인덱스): 스타 질의는 `Hash Join` 두 개로 돌았다. `Hash` 쪽(해시 테이블을 만드는 쪽)에 필터된 `dim_product`(10행)와 `dim_customer`(30행)가 올라갔다. 날짜 차원은 1행이라 `Nested Loop` + 팩트의 `Bitmap Heap Scan`(date_key 인덱스)으로 붙었다.
- 같은 팩트에 `product_key = 4 AND customer_key = 8`을 걸면 두 FK 인덱스의 `Bitmap Index Scan`을 `BitmapAnd`로 합친 뒤 힙을 읽었다.
- 즉 이 실험에서 해시 조인은 작은 차원으로 큰 팩트를 거르는 데, 비트맵은 여러 차원 조건을 팩트 행 위치 집합의 AND로 합치는 데 쓰인다.

### 8. 정확히 2배

- 의심
  - 팩트에 grain이 다른 행이 섞였다(상세 줄 + 주문 합계 줄). grain 키(`order_no, line_no`)가 서로 달라 중복 검사를 통과한다.
  - 또는 grain이 다른 팩트끼리 조인했다.
- 확인
  - 원천 합계와 대조: 실험에서 `mixed_sum 24,435,000` vs 진짜 12,217,500.
  - grain에 맞지 않는 행 찾기: `line_no = 0` 같은 특수 값, `sales`가 같은 주문의 다른 줄 합과 같은 행.
- 수정: 합계 줄을 별도 집계 팩트로 빼고, grain 문장을 테이블 주석·문서에 적는다. 적재 후 원천과 합계 대조를 돈다.

### 9. 잔액이 수십 배

- 주기 스냅샷 팩트(일말 잔액)의 반가산 지표를 시간 축으로 `SUM`했다. 잔액이 한 달 내내 같았다면 30일 합은 정확히 30배다.
- 시간 축은 "기간 마지막 날 값"(월말 잔액) 또는 평균 잔액으로 집계한다. 계좌·지점 축으로는 합해도 된다.
