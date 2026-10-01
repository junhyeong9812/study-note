# database/03-normalization — 정규화: 한 사실은 한 곳에 — 정리 (힌트)

## 해결하는 문제

주문 테이블에 고객 이메일을 같이 넣어 두었다.

```text
  orders_flat
  order_id │ customer_id │ customer_email │ amount
  ─────────┼─────────────┼────────────────┼───────
     1     │      7      │ kim@old.com    │  100
     2     │      7      │ kim@old.com    │  200     <- 같은 사실(고객 7의 이메일)이 두 번
     3     │      8      │ lee@x.com      │   50
```

- 고객 7이 이메일을 바꿨다. 앱이 주문 2의 행만 고쳤다.
- 로컬 재현(예시, PostgreSQL 17.11): `GROUP BY customer_id HAVING count(DISTINCT customer_email) > 1`이 `7 | 2 | {kim@new.com,kim@old.com}`을 돌려줬다. **같은 사실이 두 곳에서 다른 값**이다.

이것을 **갱신 이상(update anomaly)**이라 한다. 같은 설계에서 두 가지가 더 생긴다.

- *삽입 이상*: 주문이 없는 고객의 이메일은 저장할 곳이 없다(주문 칸을 NULL로 채워야 한다).
- *삭제 이상*: 고객 8의 마지막 주문을 지우면 고객 8의 이메일도 사라진다.
- Silberschatz 7장은 이를 "정보의 반복"과 "NULL 값의 필요"로 설명한다(`in_dep` 예).

쉬운 예: 반 전화번호부를 과목별 명단마다 따로 적어 두었다. 한 학생이 번호를 바꾸면 모든 명단을 고쳐야 하고, 하나라도 빠뜨리면 어느 번호가 맞는지 모른다.

똑같은 구조다.\
정규화는 "무엇이 무엇을 결정하는가(함수 종속)"를 적고, **결정하는 쪽을 키로 하는 테이블**로 쪼개 한 사실을 한 곳에만 두는 절차다.

실무 예:
- 상품명을 주문 상세, 장바구니, 리뷰 테이블에 복사해 두었다가 상품명 변경 배치가 한 곳을 빠뜨린다.
- 반대로 너무 잘게 쪼개 목록 화면 하나에 10개 넘는 조인이 붙는다(과정규화).

## 동작·원리

### 1. 함수 종속 — "X가 같으면 Y도 같다"

```text
  X → Y  :  X 값이 같은 두 튜플은 반드시 Y 값도 같다

  orders_flat 에서
    order_id    → customer_id, customer_email, amount     (order_id가 키)
    customer_id → customer_email                          (고객이 이메일을 결정)
```

- *함수 종속(functional dependency, FD)*: 속성 집합 X의 값이 속성 집합 Y의 값을 하나로 정하는 관계.
- FD는 **데이터가 아니라 업무 규칙**에서 온다. 지금 데이터에서 우연히 성립하는 것과 구별한다.
- 키와의 관계: X → (모든 속성)이면 X는 슈퍼키다(02번).

암스트롱 공리(Silberschatz 7장, 건전하고 완전하다):

```text
  반사  β ⊆ α 이면 α → β
  증가  α → β 이면 γα → γβ
  이행  α → β, β → γ 이면 α → γ
```

### 2. 속성 폐포 — X로부터 결정되는 것 전부

```text
  R = (A, B, C, G, H, I)
  F = { A→B, A→C, CG→H, CG→I, B→H }

  (AG)+ 계산 (Silberschatz 7장 예)
  result = {A, G}
  A→B, A→C 적용           → {A, B, C, G}
  CG→H 적용 (CG ⊆ result)  → {A, B, C, G, H}
  CG→I 적용               → {A, B, C, G, H, I}  = R 전체 → AG는 슈퍼키
  A+ = {A, B, C, H}, G+ = {G} → 둘 다 R이 아님 → AG는 후보 키
```

- 결과가 더 이상 안 바뀔 때까지 규칙을 반복 적용한다(고정점 반복).
- 쓰임: 키 찾기, "이 FD가 성립하는가" 판정, 분해가 손실 없는가 판정.

### 3. 정규형 사다리

```text
  1NF   모든 속성 값이 원자적(더 쪼개지 않는 값)
   │      위반 예: tags = 'a,b,c' 문자열
   │      (phone1/phone2/phone3 반복 열은 값이 원자적이면 1NF 위반은 아니다 — 정규화가 못 잡는 설계 문제, Silberschatz 7장 "Other Design Issues")
   ▼
  2NF   1NF + 키가 아닌 속성이 후보 키의 "일부"에만 종속하지 않음 (부분 종속 없음)
   │      위반 예: order_item(order_id, product_id, qty, product_name)
   │               product_id → product_name  (키 (order_id, product_id)의 일부에 종속)
   ▼
  3NF   모든 α → β 가 (자명) 또는 (α가 슈퍼키) 또는 (β − α의 각 속성이 어떤 후보 키에 포함)
   │      위반 예: orders_flat 의 customer_id → customer_email (이행 종속)
   ▼
  BCNF  모든 α → β 가 (자명) 또는 (α가 슈퍼키)
          = "결정자는 모두 슈퍼키"
```

- 3NF·BCNF 정의는 Silberschatz 7장 슬라이드 그대로다. 2NF는 슬라이드에 없는 고전 정의로 적었다 [?].
- BCNF이면 3NF이다. 3NF의 세 번째 조건이 BCNF를 조금 푼 것이다.

### 4. 분해 — 잃지 않고, 가능하면 종속도 지키며

```text
  orders_flat(order_id, customer_id, customer_email, amount)
     위반 FD: customer_id → customer_email,  customer_id는 슈퍼키가 아님
     ▼ BCNF 분해: (α ∪ β) 와 (R − (β − α))
  customer(customer_id, customer_email)           orders(order_id, customer_id, amount)
                     └──────────── customer_id ────────────┘
```

- **손실 없는 분해(lossless)**: 쪼갠 두 테이블을 다시 자연 조인하면 원래와 정확히 같다. R1 ∩ R2 → R1 또는 R1 ∩ R2 → R2가 F+에 있으면 충분하다(Silberschatz 7장). 위에서 공통 속성 `customer_id`가 `customer`의 키이므로 손실이 없다.
  - 잘못 쪼개면 조인 결과에 원래 없던 행(가짜 튜플)이 생긴다. 이것을 손실 분해라 한다. 정보가 "늘어난" 게 아니라 무엇이 참인지 알 수 없게 된 것이다.
- **종속 보존(dependency preservation)**: 원래 FD를 각 테이블 안에서만 검사할 수 있다. 그래야 조인 없이 제약으로 강제할 수 있다.
- BCNF는 손실 없이 항상 만들 수 있지만 종속 보존은 못 할 수 있다. 3NF는 손실 없음과 종속 보존을 둘 다 항상 얻는다(Silberschatz 7장 "Comparison of BCNF and 3NF").

```text
  BCNF와 종속 보존이 충돌하는 예 (Silberschatz 7장 dept_advisor)
  dept_advisor(s_ID, i_ID, dept_name)
    i_ID → dept_name            (교수는 한 학과 소속)
    s_ID, dept_name → i_ID      (학생은 학과마다 지도교수 한 명)
  i_ID가 슈퍼키가 아니므로 BCNF 위반. 그러나 어떻게 쪼개도 (s_ID, dept_name → i_ID)를
  한 테이블 안에 담을 수 없다 → 3NF로 남겨 두는 선택이 있다.
```

### 5. 반정규화 — 읽기를 위해 의도적으로 되돌리기

- 정규화는 쓰기 정합성을 얻고, 읽기에 조인 비용을 낸다.
- Silberschatz 7장 "Denormalization for Performance"의 두 선택지:
  1. 반정규화한 테이블을 둔다 → 조회는 빠르다. 대신 공간·갱신 비용이 들고, 동기화 코드가 틀릴 위험이 있다.
  2. 구체화 뷰(materialized view)를 둔다 → 장단점은 같지만 동기화 코드를 사람이 짜지 않는다.
- **반정규화가 아닌 것**: 주문 상세의 `unit_price`는 "상품의 현재 가격"의 복사가 아니다. "주문 시점의 가격"이라는 **다른 사실**이다. FD가 다르므로(`(order_id, product_id) → unit_price`) 정규형을 어기지 않는다.

## 쓰이는 자료구조·알고리즘

- **속성 폐포 = 고정점 반복**: 결과 집합이 커지지 않을 때까지 FD를 반복 적용한다. 속성 집합은 비트셋으로 표현하면 `β ⊆ result` 검사가 `(β & ~result) == 0` 한 번이다([data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)). 커리큘럼 🔧 "함수 종속 폐포".
- **BCNF 분해 알고리즘**: 위반 FD α → β를 찾아 (α ∪ β)와 (R − (β − α))로 나누고, 결과 스키마마다 반복한다(Silberschatz 7장 "Decomposing a Schema into BCNF").
- **3NF 합성 알고리즘**: 정준 덮개(canonical cover)의 FD마다 스키마를 하나씩 만들고, 후보 키를 담은 스키마가 없으면 하나 더한다. 결과는 3NF이고 손실 없고 종속을 보존한다(Silberschatz 7장 "3NF Decomposition Algorithm").
- **조인 순서 탐색**: 쪼갤수록 조인이 늘고, 옵티마이저가 고를 조인 순서의 경우의 수가 빠르게 는다. PostgreSQL은 이를 제한하려 `join_collapse_limit`·`from_collapse_limit`(기본 8)과 `geqo_threshold`(기본 12, `geqo`가 켜져 있고 이 수 이상 FROM 항목이면 유전 알고리즘)를 둔다(PostgreSQL 17 19.7). MySQL은 `optimizer_search_depth`(기본 62)를 둔다(MySQL 8.4 7.1.8).

## 적용 — 풀어나가는 법

### 1. 설계 순서

```text
  1. 한 테이블이 무엇 한 가지에 대한 사실인지 한 문장으로 쓴다 ("이 행은 주문 한 건이다")
  2. 업무 규칙에서 FD를 적는다 (customer_id → email, product_id → name …)
  3. 폐포로 후보 키를 찾는다
  4. 결정자가 슈퍼키가 아닌 FD가 있으면 그 FD를 떼어 새 테이블로 (결정자가 새 테이블의 PK, 원래 쪽엔 FK)
     — BCNF가 목표일 때. 쪼개면 종속 보존이 깨지는 경우(위 dept_advisor)는 3NF로 남길 수 있다
  5. 조회 패턴을 보고, 측정된 병목이 있을 때만 반정규화 (동기화 방법을 같이 정한다)
```

### 2. 운영 데이터에서 FD 위반 찾기

```sql
-- "customer_id → customer_email"이 깨진 곳
SELECT customer_id, count(DISTINCT customer_email) AS emails
FROM orders_flat
GROUP BY customer_id
HAVING count(DISTINCT customer_email) > 1;
```

- 결과가 있으면 이미 갱신 이상이 난 것이다. 어느 값이 맞는지는 데이터로 알 수 없다. 원천(고객 마스터)을 기준으로 정한다.

### 3. 분해와 이관

```sql
CREATE TABLE customer (customer_id int PRIMARY KEY, email text NOT NULL);
INSERT INTO customer
SELECT DISTINCT ON (customer_id) customer_id, customer_email
FROM orders_flat ORDER BY customer_id, order_id DESC;       -- PG: order_id가 가장 큰 주문의 값을 채택(order_id가 시간순이라고 가정. 실제 기준은 주문 시각 열 등 업무가 정함)
ALTER TABLE orders_flat ADD FOREIGN KEY (customer_id) REFERENCES customer;
-- 이후 앱이 customer만 쓰게 바꾼 뒤 orders_flat.customer_email을 제거 (expand/contract, 26-schema-migration)
```

### 4. 반정규화는 동기화 방법과 한 묶음으로

```sql
-- 선택 A: 구체화 뷰 (PostgreSQL) — 새로 고칠 때까지는 옛 값
CREATE MATERIALIZED VIEW order_summary AS
SELECT o.order_id, c.email, o.amount FROM orders o JOIN customer c USING (customer_id);
REFRESH MATERIALIZED VIEW order_summary;
-- 선택 B: 캐시 열 + 같은 트랜잭션에서 갱신 (트리거 또는 앱)
-- 선택 C: 다른 사실로 모델링 (주문 시점 가격·주소 스냅샷)
```

- 구체화 뷰는 `REFRESH` 전까지 원본 변경을 반영하지 않는다. MySQL 8.4에는 구체화 뷰가 없다(로컬 재현, MySQL 8.4.10: `CREATE MATERIALIZED VIEW`가 `ERROR 1064` 문법 오류). 문법 세부는 [sql/48 뷰와 구체화 뷰](../../../languages/sql/syntax/48-views-and-materialized-views/2-summary.md).

### 5. 진단

```sql
-- PostgreSQL: 조인이 몇 개이고 어디서 시간을 쓰나
EXPLAIN (ANALYZE, BUFFERS) SELECT …;
SHOW join_collapse_limit; SHOW geqo_threshold;
-- pg_stat_statements: 호출당 평균 시간이 큰 문장 (조인 쿼리인지는 query 열을 보고 가린다)
SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
-- MySQL
EXPLAIN ANALYZE SELECT …;
```

## 장애 시나리오와 대처

### 1. 같은 사실이 두 곳에서 다른 값 (⚠ 커리큘럼: 갱신 이상)

- **현상**: 고객 화면의 이메일과 주문 내역의 이메일이 다르다. 알림 메일이 옛 주소로 간다.
- **보이는 형태**: 에러 없음. 위의 `HAVING count(DISTINCT …) > 1` 점검 쿼리에 행이 나온다. 로컬 재현(예시): `7 | 2 | {kim@new.com,kim@old.com}`.
- **원인**: 고객 → 이메일이라는 FD를 주문 테이블에 복사했다. 갱신 경로 하나가 복사본 일부만 고쳤다.
- **대처**
  - 결정자(`customer_id`)를 키로 하는 테이블로 분리하고 FK로 잇는다.
  - 분리가 당장 어려우면 복사본 갱신을 한 트랜잭션·한 함수로 모으고, 점검 쿼리를 주기적으로 돌린다.

### 2. 과정규화 → 조인 폭발 (⚠ 커리큘럼)

- **현상**: 목록 API 하나가 테이블 10개 이상을 조인한다. 응답 시간이 들쭉날쭉하고 플랜이 가끔 크게 나빠진다.
- **보이는 형태**: `EXPLAIN ANALYZE`에 조인 노드가 줄줄이 있고, 추정 행 수(`rows=`)와 실제(`actual rows=`)가 조인을 거칠수록 크게 벌어진다. PostgreSQL에서 `geqo`(기본 on)가 켜져 있고 플래너가 한 번에 다루는 FROM 항목(collapse 한도로 묶인 뒤의 수)이 `geqo_threshold`(기본 12) 이상이면 유전 알고리즘 플래너가 쓰여 최적이 아닌 계획이 나올 수 있다(19.7).
- **원인**: 조회 단위가 한 덩어리인 데이터(예: 주소의 시·구·동을 각각 테이블로)까지 쪼갰다. 조인이 늘수록 카디널리티 추정 오차가 커진다(Leis 외 2015 "How Good Are Query Optimizers, Really?" §3: JOB 벤치마크에서 조인 수가 늘수록 오차가 지수적으로 커짐) — [12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md) 참고.
- **대처**
  - 함께 바뀌고 함께 읽히는 값(주소 문자열 등)은 한 테이블의 열로 둔다. 정규형은 "FD가 있을 때"의 규칙이지 "최대한 쪼개라"가 아니다.
  - 읽기 전용 화면은 구체화 뷰·조회용 테이블로 미리 조인해 둔다.
  - 참고: 로컬 재현(예시, PostgreSQL 17.11)에서 1,000행 테이블 14개 사슬 조인의 계획 시간은 약 1~2ms였다. 조인 수만으로 계획이 폭발하지는 않는다. 비용은 주로 실행 시 행 수와 추정 오차에서 온다.

### 3. 반정규화한 캐시 열이 원본과 어긋남

- **현상**: 게시글의 `comment_count`가 실제 댓글 수와 다르다.
- **보이는 형태**: 에러 없음. `SELECT p.id FROM post p WHERE p.comment_count <> (SELECT count(*) FROM comment c WHERE c.post_id = p.id)`에 행이 나온다.
- **원인**: 댓글 삭제 경로 하나(관리자 일괄 삭제, CASCADE 등)가 캐시 열 갱신을 빠뜨렸다. 또는 동시 갱신에서 `count = count + 1` 대신 읽고-쓰기로 값을 덮었다(lost update, [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md)).
- **대처**: 갱신을 원자적 증감(`SET comment_count = comment_count + 1`)으로 하고, 삭제 경로를 트리거로 모은다. 재계산 배치를 둔다.

### 4. 1NF 위반 — 쉼표 목록 열

- **현상**: `tags = 'java,spring,db'` 열에서 "spring 태그 글"을 `LIKE '%spring%'`으로 찾다가 `springboot`까지 걸린다. 태그 이름을 바꾸려면 모든 문자열을 고쳐야 한다.
- **보이는 형태**: 잘못된 검색 결과, 일반 B-tree 인덱스를 못 타는 풀 스캔(PostgreSQL은 `pg_trgm` GIN·GiST 인덱스가 있으면 앞 `%` 패턴도 인덱스 검색 가능, F.33), FK를 걸 수 없음.
- **원인**: 한 칸에 여러 값을 넣었다. DB가 그 안의 원소를 모른다.
- **대처**: `post_tag(post_id, tag_id)` 연결 테이블로 분리한다. 정말 문서형이 맞는 데이터면 배열·JSON 열과 전용 인덱스를 쓴다(36번).

### 5. "정규화"한다며 주문의 가격을 상품 테이블로 옮겼다

- **현상**: 상품 가격을 올리자 지난달 주문의 금액까지 바뀌어 정산이 틀어진다.
- **보이는 형태**: 에러 없음. 과거 매출 재계산 값이 매번 다르다.
- **원인**: "주문 시점 가격"과 "현재 가격"은 다른 사실이다. FD가 `(order_id, product_id) → unit_price`인 것을 `product_id → price`로 잘못 적었다.
- **대처**: 주문 상세에 주문 시점 가격을 스냅샷으로 둔다. 반정규화가 아니라 올바른 모델링이다. 기간별 값이 필요하면 유효 기간 테이블([50-temporal-and-bitemporal-tables](../50-temporal-and-bitemporal-tables/2-summary.md))을 둔다.

## 핵심 문장

- 정규화는 함수 종속(X가 같으면 Y도 같다)을 적고, 결정자를 키로 하는 테이블로 쪼개 한 사실을 한 곳에만 두는 일이다.
- 결정자가 슈퍼키가 아닌 종속이 남아 있으면 갱신·삽입·삭제 이상이 생긴다. BCNF는 "모든 결정자가 슈퍼키"다.
- 분해는 손실이 없어야 하고, 가능하면 종속을 보존해야 한다. BCNF는 종속 보존을 못 할 때가 있고, 3NF는 둘 다 항상 얻는다.
- 속성 폐포는 FD를 고정점까지 반복 적용해 키와 종속을 판정하는 기본 알고리즘이다.
- 반정규화는 측정된 읽기 병목이 있을 때, 동기화 방법(구체화 뷰·트리거·스냅샷)과 한 묶음으로 결정한다. 시점 스냅샷은 반정규화가 아니라 다른 사실이다.

## 관련 주제·근거

- 선행: [02-keys-and-constraints](../02-keys-and-constraints/2-summary.md)
- 연결
  - [01-relational-model-and-algebra](../01-relational-model-and-algebra/2-summary.md) — 사영·자연 조인(분해와 재결합)
  - [04-sql-joins-and-aggregation](../04-sql-joins-and-aggregation/2-summary.md) — 분해한 테이블을 다시 잇는 조인
  - [36-data-models-document-graph](../36-data-models-document-graph/2-summary.md) — 문서 모델의 비정규화와 다대다
  - [12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md) · [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md) · [26-schema-migration](../26-schema-migration/2-summary.md) · [50-temporal-and-bitemporal-tables](../50-temporal-and-bitemporal-tables/2-summary.md)
  - [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- 교재
  - Silberschatz, Korth, Sudarshan 『Database System Concepts』 7판 7장 "Normalization" 슬라이드 — 좋은 설계의 특징(`in_dep`), 손실 없는 분해, BCNF·3NF 정의, dept_advisor 예, BCNF vs 3NF 비교, 암스트롱 공리, 속성 폐포 알고리즘과 (AG)+ 예, 반정규화, 1NF <https://www.db-book.com/slides-dir/PDF-dir/ch7.pdf>
  - Kleppmann 『DDIA』 1판 2장 — 정규화의 핵심은 중복 제거, ID 참조 (각주: 규범 형식 구분보다 "한 곳에 둘 수 있는 값을 복제하면 비정규화"라는 경험칙)
- 공식 문서
  - PostgreSQL 17 19.7 Query Planning(`from_collapse_limit`·`join_collapse_limit` 기본 8, `geqo_threshold` 기본 12) <https://www.postgresql.org/docs/17/runtime-config-query.html> · 14.3 Controlling the Planner with Explicit JOIN Clauses
  - MySQL 8.4 7.1.8 `optimizer_search_depth`(기본 62) <https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html>
- 논문: V. Leis 외, "How Good Are Query Optimizers, Really?", PVLDB 9(3), 2015 — 조인 수에 따른 추정 오차 증가 <https://www.vldb.org/pvldb/vol9/p204-leis.pdf>
- 로컬 재현(PostgreSQL 17.11): 갱신 이상(한 고객에 이메일 2개) 탐지 쿼리, 14개 사슬 조인 계획 시간 / (MySQL 8.4.10): `CREATE MATERIALIZED VIEW` 문법 오류
