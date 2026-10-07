# data-engineering/13-data-vault — 데이터 볼트: Hub·Link·Satellite로 적재 이력을 보존하는 통합 모델 — 정리 (힌트)

## 해결하는 문제

원천 시스템이 여럿이면 "같은 고객"이 시스템마다 다른 모양으로 들어온다.\
스타 스키마([03 dimensional-modeling](../03-dimensional-modeling/2-summary.md))는 분석하기 좋은 모양이다.\
그런데 원천이 바뀔 때마다 차원·팩트를 고쳐야 한다. 원천 추출본을 따로 보존하지 않는 적재 설계라면 정제(cleansing) 과정에서 원래 값이 사라진다.

```text
  원천이 늘고 바뀔 때 — 스타 스키마에 바로 적재하면
  CRM      ─┐                         dim_customer  ← CRM 컬럼 추가 → 차원 재설계
  BILLING  ─┼── 정제·통합 ──>  스타   ← BILLING 교체 → 적재 로직 재작성
  SHOP(신규)┘                         정제에서 버린 원래 값 → "그때 원천이 뭐라고 보냈나"에 답할 수 없음
```

- 데이터 볼트의 답: **구조(키·관계)와 서술(속성)을 떼어** 따로 쌓는다. 속성은 덮어쓰지 않고 적재할 때마다 새 행으로 남긴다.
  - *데이터 볼트(Data Vault)*: Dan Linstedt가 2000년에 공개한 데이터 웨어하우스 모델링 방법. 여러 운영 시스템의 데이터를 장기 이력으로 보관하는 통합 계층용이다(Wikipedia "Data vault modeling" — 2차 출처).
  - *Hub*: 비즈니스 키(고객 번호·주문 번호처럼 업무에서 쓰는 식별자)의 목록.
  - *Link*: Hub 사이의 관계(주문–고객). 다대다 연결 테이블이다.
  - *Satellite*: Hub나 Link에 붙는 서술 속성과 그 이력. 행을 추가만 한다(insert-only).

쉬운 예: 학교의 학적부다.
- 학번 명부(Hub)는 거의 안 바뀐다.
- 수강 기록(Link)은 "학번–과목" 짝만 적는다.
- 주소·연락처(Satellite)는 바뀔 때마다 날짜와 함께 한 줄씩 덧붙인다. 지우지 않는다.

똑같은 구조다.\
새 원천이 생기면 기존 표를 고치지 않고 덧붙인다. 기존 비즈니스 키에 속성만 더하면 Satellite를 하나 더 붙이고, 새 키·관계가 있으면 Hub·Link도 더한다.\
대가로 **조회가 어려워진다.** 분석가는 볼트를 직접 쓰지 않고, 볼트에서 만든 마트(스타 스키마)를 쓴다.

실무 예:
- 금융·보험처럼 감사(audit)가 중요한 곳에서 "3월 2일 적재분에 CRM이 보낸 등급이 뭐였나"에 답해야 한다.
- 인수합병으로 고객 시스템이 둘이 됐다. 두 시스템의 고객 번호를 한 Hub에 모은다.
- 반대로, 공백·대소문자를 정리하지 않은 키로 Hub를 만들어 같은 고객이 두 줄이 된다(이 노트의 실험).

## 동작·원리

### 1. 세 가지 표 — 구조와 서술의 분리

```text
            ┌──────────────────────┐            ┌──────────────────────┐
            │ hub_customer         │            │ hub_order            │
            │ customer_hk (PK)     │            │ order_hk (PK)        │
            │ customer_bk          │            │ order_bk             │
            │ load_ts, rec_source  │            │ load_ts, rec_source  │
            └─────────┬────────────┘            └──────────┬───────────┘
                      │        ┌───────────────────────┐   │
                      └───────>│ link_customer_order   │<──┘
                               │ link_hk (PK)          │
                               │ customer_hk, order_hk │
                               │ load_ts, rec_source   │
                               └───────────────────────┘
   sat_customer_crm (hk, load_ts PK, hashdiff, tier, region, rec_source)      ← CRM에서 온 속성
   sat_customer_billing (hk, load_ts PK, hashdiff, credit_limit, rec_source)  ← BILLING에서 온 속성
   sat_order (order_hk, load_ts PK, hashdiff, amount, rec_source)
```

- 행마다 *record source*(어느 원천이 보냈나)와 *load date*(언제 적재했나)를 붙인다. 감사자가 값을 원천까지 거슬러 올라가게 하려는 것이다(Wikipedia "Data vault modeling" 서두).
- Hub와 Link에는 서술 속성이 없다. 속성은 Satellite에만 있다(Wikipedia "Satellites").
- Satellite는 원천별로 나누는 것이 보통이다. 바뀌는 속도가 다르면 속도별로 더 나눈다(같은 절).
- 책 목차로 확인한 범위: Linstedt–Olschimke 『Building a Scalable Data Warehouse with Data Vault 2.0』(Morgan Kaufmann, 2015) 4장 "Data Vault 2.0 Modeling"이 4.3 Hub·4.4 Link·4.5 Satellite 정의를, 6장이 PIT·Bridge 테이블을, 11.2절이 해시를 다룬다(Elsevier 도서 페이지 목차). 본문은 읽지 못했다.

### 2. 해시 키 — 비즈니스 키에서 계산한 대리 키

```text
  원천 값              정규화                         해시(MD5, 16바이트)
  'C001'      ──>  UPPER(TRIM('C001'))   = 'C001' ──> 928c6512...  ┐
  ' c001 '    ──>  UPPER(TRIM(' c001 ')) = 'C001' ──> 928c6512...  ┘ 같은 Hub 행
  ' c001 '    ──>  (정규화 없음)                     ──> 059f750f...    다른 Hub 행 ← 사고
```

- *해시 키(hash key)*: 비즈니스 키를 정규화한 뒤 해시한 값. Hub·Link의 기본 키로 쓴다.
  - 시퀀스 대리 키와 다른 점: 비즈니스 키만 알면 어디서든 같은 값을 계산한다. Hub를 먼저 조회해 ID를 받아 올 필요가 없다.
  - 그래서 Hub·Link·Satellite를 같은 스테이징에서 나란히 적재할 수 있다(해석). 시퀀스 ID 방식은 Hub를 먼저 적재해 ID를 얻은 뒤 Link를 적재한다(Wikipedia "Loading practices").
- AutomateDV(dbt용 데이터 볼트 패키지) 문서 "Hashing"이 쓰는 정규화 순서
  1. 문자열로 `CAST` — 숫자 1001과 문자열 '1001'을 같게.
  2. `TRIM` — 앞뒤 공백 제거.
  3. `UPPER` — 대소문자 통일.
  4. `NULLIF(…, '')` — 빈 문자열을 NULL로.
  5. 해시(기본 MD5, SHA-1·SHA-256 선택 가능) 후 `BINARY`로 저장.
  - 여러 컬럼이면 NULL을 `^^`로 바꾸고 `||`로 이어 붙인 뒤 해시한다.
- Link의 해시 키는 참여하는 비즈니스 키들을 이어 붙여 해시한다(AutomateDV "Links").
- *hashdiff*: Satellite 속성(payload)과 키를 이어 붙여 해시한 값. 체크섬처럼 레코드의 변경을 감지하는 데 쓴다(AutomateDV "Satellites" — "a concatenation of the payload and the primary key"). AutomateDV "Hashing"은 DV 2.0 표준에 따라 hashdiff에 자연 키를 넣으라고 적는다.
  - 적재 규칙: 직전 행과 hashdiff가 같으면 바뀐 게 없으니 새 행을 넣지 않는다(이 노트의 실험이 쓴 방식).
  - 흔한 오해: "해시 키는 보안용이다." AutomateDV 문서는 해시를 보안이 아니라 최적화·유일성 용도로 쓴다고 밝힌다. 소금(salt) 없는 해시된 PII는 무차별 대입으로 되돌릴 수 있다고 경고한다.

해시 충돌 크기(계산): 128비트 해시에 키 n개를 넣을 때 충돌 확률은 생일 근사로 약 n²/2¹²⁹이다.
- n = 10¹⁰(100억 행)이면 약 1.5 × 10⁻¹⁹이다. 무작위 입력에서 충돌보다 **정규화 누락**이 훨씬 흔한 사고다(해석).
- 공격자가 키를 고를 수 있는 입력이면 MD5의 충돌 저항이 깨져 있다는 점이 따로 문제다. → [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)

### 3. Satellite 적재 — 추가만, 바뀐 것만

```text
  적재일   CRM 원천 (tier, region)      sat_customer_crm 행     BILLING 원천 (한도)   sat_customer_billing 행
  day1    gold, KR-SEOUL             +1 (처음)                1000                 +1 (처음)
  day2    gold, KR-SEOUL              0 (hashdiff 같음)        1000                  0
  day3    platinum, KR-SEOUL         +1                       1000                  0
  day4    platinum, KR-SEOUL          0                       3000                 +1
  day5    gold, KR-BUSAN             +1                       3000                  0
                                     = 3행                                         = 2행
```

- 덮어쓰지 않으니 차원 모델의 SCD Type 2와 효과가 비슷하다(Wikipedia "Basic notions"). → [04 slowly-changing-dimensions](../04-slowly-changing-dimensions/2-summary.md)
- 끝 시각 컬럼: Data Vault 1.0 예시에는 선택 컬럼 `S_LEDTS`(load end date)가 있다(Wikipedia Satellite 예시). AutomateDV의 Satellite 구조에는 끝 시각 컬럼이 없다. 구간은 다음 행의 `load_ts`로 계산하거나 PIT로 미리 계산한다.
- *load date* vs *effective from*: 적재 시각은 "우리가 언제 알았나", 업무 유효 시각은 "현실에서 언제 일어났나"다. AutomateDV는 `EFFECTIVE_FROM`을 선택 컬럼으로 두고 "Data Vault 2.0 표준의 일부가 아니다"라고 적는다. 두 축은 [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md)의 기록 시간·유효 시간과 같은 구분이다.

### 4. 조회 — Satellite를 그냥 조인하면 행이 곱해진다

```text
  hub(C001) ─┬─ sat_crm     3행  ┐
             └─ sat_billing 2행  ┘  JOIN → 3 × 2 = 6행   sum(credit_limit) = 12000 (실제 현재 한도 3000)

  PIT(point-in-time) 테이블: 기준 시각마다 각 Satellite에서 "그 시각에 유효한 행"의 좌표를 미리 적어 둔다
  as_of       customer_hk   crm_ldts      billing_ldts
  10-03 12:00 928c...       10-03 01:00   10-01 01:00
  10-04 12:00 928c...       10-03 01:00   10-04 01:00     → 조회는 (hk, ldts) 등가 조인 1:1
```

- *PIT 테이블*: 비즈니스 볼트(Business Vault)의 조회 보조 구조. 기준 시각 목록(as-of dates)마다 각 Satellite의 해시 키와 load 시각을 기록해, 마트 쿼리가 등가 조인(equi-join)만 쓰게 한다(AutomateDV "Point In Time (PIT) tables").
  - 같은 문서는 Satellite를 둘 이상 참조할 때, 특히 갱신 속도가 다를 때 PIT를 권한다.
- *Bridge 테이블*: Hub·Link를 여러 단계 건너는 경로를 미리 펼쳐 둔 조회 보조 구조(책 6.2절 제목으로만 확인 — 세부 `[?]`).
- *Raw Vault vs Business Vault*: Raw Vault는 원천 그대로(최소 변환)의 통합 계층이다. Business Vault는 업무 규칙과 PIT·Bridge 같은 조회 보조 구조를 얹은 파생 계층이다(Wikipedia "Layers").

### 5. 마트로 내보내기 — 분석가가 쓰는 층

```text
  원천 ──> 스테이징 ──> Raw Vault (Hub·Link·Sat) ──> Business Vault (규칙·PIT·Bridge) ──> 정보 마트(스타 스키마)
           (정규화·해시 계산)       ↑ 이력 보존·감사                                         ↑ 분석가·BI 도구
```

- Hub와 그 Satellite는 차원으로, Link와 그 Satellite는 팩트로 볼 수 있다. 그래서 뷰로 차원 모델의 원형을 빨리 만들 수 있다(Wikipedia "Data vault and dimensional modelling").
- 볼트 계층은 질의 성능에 최적화되어 있지 않다. BI 도구는 차원 모델을 기대하므로 변환이 필요하다(같은 절).
- 정제(cleansing)는 Raw Vault가 아니라 그 바깥에서 한다. Wikipedia 서두는 "정제는 마트에서 한다"고 적고, 같은 문서의 "Layers"는 Business Vault가 업무 규칙을 적용한다고 적는다. Raw Vault는 업무 규칙에 맞지 않는 데이터도 그대로 담는다 — "single version of the facts"(Wikipedia 서두).

### 실험: 키 정규화 누락 → Hub 행 2개, Satellite 조인 곱, PIT

- 환경: PostgreSQL 17.11(`postgres:17` 컨테이너, `--network none --cpus=2`), i7-13700HX 호스트. 합성 데이터(`C001` 형식).
- 코드: 스테이징 → Hub(정규화 없음/있음) → Link → Satellite(hashdiff 비교 적재 함수) → PIT → 현재 시점 차원 뷰.

```sql
-- 정규화 없음 vs 있음
INSERT INTO hub_customer_raw SELECT DISTINCT ON (hk) hk, customer_id, load_ts, src
  FROM (SELECT decode(md5(customer_id),'hex') hk, * FROM stg_customer) s ORDER BY hk, load_ts, src;
INSERT INTO hub_customer SELECT DISTINCT ON (hk) hk, bk, load_ts, src
  FROM (SELECT decode(md5(upper(trim(customer_id))),'hex') hk, upper(trim(customer_id)) bk, * FROM stg_customer) s
  ORDER BY hk, load_ts, src;

-- Satellite 적재: 최신 행의 hashdiff와 다를 때만 INSERT
INSERT INTO sat_customer_crm
SELECT n.hk, p_ts, n.hd, p_tier, p_region, 'CRM' FROM n
WHERE n.hd IS DISTINCT FROM (SELECT s.hashdiff FROM sat_customer_crm s
                             WHERE s.customer_hk = n.hk ORDER BY s.load_ts DESC LIMIT 1);
```

- 이 실험의 정규화 Hub(`hub_customer`)는 정규화된 키(`C001`)만 담는다. 원천이 보낸 원래 표기(`' c001 '`)는 이 Hub·Satellite 구조에서 복원할 수 없다. "원천이 뭐라고 보냈나"에 답하려면 원래 키를 따로 남기거나(예: Satellite 속성) 스테이징 추출본을 보존하는 경로가 필요하다(해석).

출력(요약):

```text
  [A] 정규화 없음: hub 행 3   ' c001 ' → 059f750f…, 'C001' → 928c6512…, 'C002' → dd21c430…
  [B] 정규화 후:   hub 행 2   C001 → 928c6512…, C002 → dd21c430…
  [C] 고객별 매출  정규화 없음: ' c001 ' 200 / 'C001' 100 / 'C002' 50
                  정규화 후:   C001 300 / C002 50
  [D] 5일 적재: crm 1,0,1,0,1 → 3행 / billing 1,0,0,1,0 → 2행
  [E] Satellite 둘을 그냥 조인: 6행, sum(credit_limit) = 12000
  [F] PIT 경유: 10-01 gold/KR-SEOUL/1000 … 10-04 platinum/KR-SEOUL/3000, 10-05 gold/KR-BUSAN/3000 (기준일당 1행)
  [H] 진단: normalized=C001, hub_rows=2, variants={"' c001 '",'C001'}
```

- 관찰: 정규화 하나가 빠지자 오류 없이 고객이 하나 늘었다. 고객별 매출이 두 줄로 쪼개졌다. 합계(350)는 그대로라 총액 대시보드로는 못 잡는다.
- 관찰: 최신 행을 고르지 않은 Satellite 조인은 3 × 2 = 6행을 만들었다. 한도 합이 실제(3000)의 4배(12000)가 됐다.

### 실험: Satellite 수 k와 리포트 쿼리 시간

- 환경 같음. Hub 2,000행, Satellite마다 Hub당 3버전. PIT로 최신 좌표를 미리 계산한 뒤, `hub JOIN pit` + Satellite k개 `LEFT JOIN`으로 합을 구했다. `EXPLAIN (ANALYZE, SUMMARY)`를 k마다 3번 — 같은 스크립트를 두 번 돌린 6회의 범위다.

```text
  k(Satellite 수)   조인 수   Planning Time (ms)   Execution Time (ms)
   2                 3        0.65 ~ 1.67           6.5 ~ 10.8
   8                 9        6.5  ~ 11.5          26.6 ~ 45.5
  16                17       21.5 ~ 37.0           81.1 ~ 96.6
  32                33       45.0 ~ 60.7          156.1 ~ 205.8
  k=32 결과를 넓은 마트 테이블로 물질화한 뒤 같은 합:  계획 0.09 ~ 0.38 ms, 실행 1.6 ~ 1.9 ms
  (SHOW: join_collapse_limit = 8, geqo_threshold = 12 — PostgreSQL 17.11 기본값)
```

- 관찰: 조인 수에 따라 계획·실행 시간이 함께 늘었다. 같은 숫자를 마트 테이블에서 읽으면 실행 시간이 약 100분의 1(156~206ms → 1.6~1.9ms)이었다.
- 한계: 2,000행·한 호스트 측정이다. 늘어나는 모양(조인 순서 탐색 비용 등)의 원인은 따로 측정하지 않았다 — 해석은 "조인 수가 계획과 실행을 모두 키운다"까지만.

## 쓰이는 자료구조·알고리즘

- **해시 함수(키 → 고정 길이 값)** — 해시 키·hashdiff. 정규화가 해시의 전제다. 같은 의미가 같은 바이트열이 되어야 같은 해시가 나온다. [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
- **해시 테이블·해시 조인** — Hub·Link·Satellite는 같은 해시 키로 조인된다. 실험의 계획도 `Hash Left Join`이었다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md)
- **추가 전용 이력(append-only)과 구간 계산** — Satellite는 `load_ts`만 쌓고 구간은 다음 행에서 계산한다. "시각 t에 유효한 행"은 `max(load_ts) ≤ t`다. 구간 질의는 [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)
- **체크섬으로 변경 감지** — hashdiff는 컬럼을 하나씩 비교하는 대신 한 값으로 비교한다. 컬럼 순서·NULL 표기가 바뀌면 값이 달라진다(AutomateDV는 hashdiff 컬럼을 알파벳순으로 정렬한다).
- **사전 계산 인덱스(PIT)** — 비싼 "시각별 최신 행 찾기"를 미리 계산해 등가 조인으로 바꾼다. 물질화된 뷰와 같은 발상이다.

## 적용 — 풀어나가는 법

### 1. 증상 → 원인 → 확인 순서

| 증상(숫자) | 의심할 원인 | 확인 쿼리 |
|---|---|---|
| 고객 수가 원천 시스템보다 많다, 한 고객의 매출이 두 줄 | 비즈니스 키 정규화 누락 | 아래 2번 |
| 마트의 한도·잔액 합계가 정수배로 부풀었다 | Satellite 여러 개를 최신 행 고르기 없이 조인 | 키별 조인 결과 행 수 |
| 같은 날 적재했는데 Satellite 행이 원천 행 수만큼 늘었다 | hashdiff에 적재 시각·순서가 바뀌는 컬럼이 섞였다 | 연속 두 행의 payload 비교 |
| 리포트 하나가 수십 초, 계획 시간만 수백 ms | Satellite 폭증, PIT·마트 없음 | `EXPLAIN (ANALYZE, SUMMARY)` |

### 2. 진단 쿼리 (PostgreSQL 17)

```sql
-- 정규화하면 같아지는 비즈니스 키 → Hub 중복 후보
SELECT upper(trim(customer_bk)) AS normalized, count(*) AS hub_rows,
       array_agg(quote_literal(customer_bk) ORDER BY customer_bk) AS variants
FROM hub_customer_raw GROUP BY 1 HAVING count(*) > 1;

-- Satellite에서 직전 행과 payload가 같은데 새 행이 생긴 경우 (hashdiff 계산 오류)
SELECT customer_hk, load_ts
FROM (SELECT *, lag(row(tier, region)) OVER w AS prev FROM sat_customer_crm
      WINDOW w AS (PARTITION BY customer_hk ORDER BY load_ts)) x
WHERE prev IS NOT DISTINCT FROM row(tier, region);

-- Link 하나에 매달린 Hub 키가 정말 있는가 (적재 순서 오류로 고아 Link)
SELECT count(*) FROM link_customer_order l
WHERE NOT EXISTS (SELECT 1 FROM hub_customer h WHERE h.customer_hk = l.customer_hk);
```

### 3. 키 정규화는 한 곳에서

- 정규화 규칙은 스테이징의 함수 하나로 모은다. 원천마다 따로 쓰면 언젠가 하나가 다르다.

```java
// Java 21: 스테이징 적재기가 쓰는 단 하나의 키 정규화 + 해시
static byte[] hashKey(String... businessKeyParts) throws Exception {
    String joined = java.util.Arrays.stream(businessKeyParts)
        .map(p -> p == null ? null : p.strip().toUpperCase(java.util.Locale.ROOT))
        .map(p -> (p == null || p.isEmpty()) ? "^^" : p)
        .collect(java.util.stream.Collectors.joining("||"));
    return java.security.MessageDigest.getInstance("MD5")
        .digest(joined.getBytes(java.nio.charset.StandardCharsets.UTF_8));
}
```

- 이 함수는 단순화다. AutomateDV("Hashing"·"NULL Handling")는 키 성분이 모두 NULL이면 해시 키를 NULL로 만들어 Hub·Link에 적재하지 않는다. 이 코드는 그때도 `^^`의 해시를 돌려준다.
  - 경계도 모호하다. NULL과 문자열 `"^^"`가 같은 입력이 되고, `hashKey("A||B","C")`와 `hashKey("A","B||C")`도 같은 입력(`A||B||C`)이 된다. 원천 키에 구분 문자열(`||`·`^^`)이 나올 수 있으면 다른 구분자·이스케이프를 정한다.
- `Locale.ROOT`를 쓴다. 터키어 로캘에서는 `"i".toUpperCase()`가 점 있는 대문자 İ가 된다(JDK `String.toUpperCase()` Javadoc의 로캘 주의).
- SQL과 Java가 같은 규칙인지 테스트로 묶는다. PostgreSQL `trim`은 기본으로 공백 문자(스페이스)만 지우고, Java `strip()`은 `Character.isWhitespace`인 유니코드 공백까지 지운다.
  - 로컬 재현(JDK 21.0.12, PostgreSQL 17.11): 키 `'\u3000C001'`(앞에 전각 공백)을 Java `hashKey`는 `928c6512…`(= `C001`과 같음)로, SQL `md5(upper(trim(…)))`은 `f5803043…`로 계산했다. 같은 고객이 적재 경로에 따라 다른 Hub 행이 된다.
- 정규화로 의미가 다른 키가 합쳐질 수도 있다(대소문자를 구분하는 원천 키). 원천의 키 규칙을 먼저 확인한다.

### 4. 언제 데이터 볼트를 쓰나

- 맞는 경우: 원천이 많고 자주 바뀐다, 감사·이력 보존 요구가 크다, 여러 팀이 병렬로 적재한다.
- 안 맞는 경우: 원천이 하나이고 분석 질문이 안정적이다. 스타 스키마 하나가 더 싸다([03 dimensional-modeling](../03-dimensional-modeling/2-summary.md)).
- 볼트를 도입하면 마트·PIT를 **함께** 계획한다. 볼트만 있으면 분석가가 쓸 수 없다.

## 장애 시나리오와 대처

### 1. 비즈니스 키 정규화 누락 → 같은 고객의 Hub 행이 둘

- **현상**: "고객 수"가 CRM 화면보다 많다. 한 고객의 매출이 두 고객으로 나뉜다.
- **보이는 형태**: 오류 없음. 총매출은 맞다. 고객별·등급별 집계만 틀린다. 실험에서 `' c001 '` 200, `'C001'` 100으로 쪼개졌다.
- **원인**: 원천 하나가 공백·소문자가 섞인 키를 보냈다. 해시 전에 `TRIM`·`UPPER`를 안 했다.
- **대처**
  - 진단 쿼리로 묶음을 찾는다.
  - 정규화 규칙을 스테이징 함수 하나로 모으고 해시 키를 다시 계산한다. Hub·Link·Satellite 전부의 키가 바뀌므로 재적재 계획이 필요하다.
  - 이미 갈라진 키를 업무적으로 합쳐야 하면 "같은 것(same-as)" Link로 두 Hub 키를 잇는 방법이 있다(책 13.10절 "Creating Dimensions from Same-As Links" 제목으로만 확인 — 세부 `[?]`).

### 2. Satellite 폭증 → 리포트 쿼리 하나에 조인 수십 개

- **현상**: 고객 리포트 하나가 점점 느려진다. 새 원천이 붙을 때마다 더 느려진다.
- **보이는 형태**: `EXPLAIN`에 `Hash Left Join`이 수십 단. 실험에서 k=32이면 계획 45.0~60.7ms, 실행 156~206ms였다. 같은 결과를 마트 테이블로 읽으면 실행 1.6~1.9ms였다.
- **원인**: 원천·변경 속도별로 Satellite를 계속 쪼갰다. 분석 쿼리가 볼트를 직접 조인한다.
- **대처**: PIT로 시각별 좌표를 미리 계산한다. 자주 쓰는 모양은 마트 테이블로 물질화한다. Satellite 분리 기준(원천·변경 속도)을 문서로 정해 무분별한 분할을 막는다.

### 3. Satellite 둘을 최신 행 고르기 없이 조인 → 합계가 곱으로 부푼다

- **현상**: 마트의 고객 한도 합계가 원천의 몇 배다.
- **보이는 형태**: 한 고객이 여러 행으로 나온다. 실험에서 3 × 2 = 6행, 한도 합 12000(실제 3000).
- **원인**: Satellite는 이력 테이블이다. 키만으로 조인하면 이력 행끼리 곱해진다. [03 dimensional-modeling](../03-dimensional-modeling/2-summary.md)의 grain 혼합과 같은 실수다.
- **대처**: PIT 좌표 `(hk, ldts)`로 조인하거나, Satellite마다 `LATERAL … ORDER BY load_ts DESC LIMIT 1`로 최신 행을 고른다. 마트 테스트에 "키당 1행" 검사를 넣는다.

### 4. 모델만 도입하고 마트를 두지 않는다 → 분석가가 쓸 수 없다

- **현상**: 볼트 구축은 끝났는데 대시보드가 하나도 안 나온다. 분석가가 원천 DB를 직접 조회한다.
- **보이는 형태**: 볼트 테이블 조회 수가 거의 없다. 원천 복제본의 분석 쿼리가 늘어 운영 DB 부하가 오른다([02 oltp-olap-and-warehouse](../02-oltp-olap-and-warehouse/2-summary.md)).
- **원인**: 볼트는 통합·이력 계층이다. BI 도구가 기대하는 차원 모델이 아니다(Wikipedia "Data vault and dimensional modelling").
- **대처**: 첫 릴리스에 마트 한두 개를 같이 낸다. 볼트 → 마트 변환을 뷰로 먼저 만들고, 느린 것만 물질화한다.

### 5. hashdiff가 매번 달라진다 → Satellite가 적재마다 전 행을 쌓는다

- **현상**: 원천 데이터는 거의 안 바뀌는데 Satellite 행 수가 매일 원천 행 수만큼 는다. 저장 비용이 빠르게 오른다.
- **보이는 형태**: 적재 로그에 "변경 N건"이 원천 전체 행 수와 같다. 위 진단 쿼리에서 payload가 같은 연속 행이 나온다.
- **원인**(후보): hashdiff에 적재 시각·추출 시각 같은 매번 바뀌는 컬럼이 들어갔다. 컬럼 순서가 원천마다 다르다. NULL과 빈 문자열을 다르게 해시한다.
- **대처**: hashdiff 입력 컬럼 목록을 고정하고 정렬한다. NULL 표기(`^^` 등)를 통일한다. 바뀐 규칙으로 다시 적재하기 전에 중복 행을 정리한다.

## 핵심 문장

- 데이터 볼트는 구조(Hub의 비즈니스 키·Link의 관계)와 서술(Satellite의 속성 이력)을 떼어, 원천이 바뀌어도 기존 표를 고치지 않고 덧붙이게 한다.
- 해시 키는 정규화한 비즈니스 키에서 계산한다. 정규화가 하나라도 빠지면 오류 없이 같은 고객이 두 Hub 행이 된다.
- Satellite는 추가 전용 이력이다. hashdiff로 바뀐 것만 쌓고, 조회할 때는 시각별로 한 행을 골라야 한다(일반 Satellite 기준 — Multi-Active Satellite는 같은 시각에 여러 행이 정상이다).
- 이력 테이블끼리 그냥 조인하면 행이 곱해진다. PIT 테이블은 시각별 좌표를 미리 계산해 이 조인을 등가 조인 1:1로 바꾼다.
- 볼트는 분석가용 모델이 아니다. 마트(스타 스키마)를 같이 만들지 않으면 아무도 못 쓴다.

## 관련 주제·근거

- 선행
  - [04 slowly-changing-dimensions](../04-slowly-changing-dimensions/2-summary.md) — Satellite ≈ Type 2 이력
  - [03 dimensional-modeling](../03-dimensional-modeling/2-summary.md) — 마트의 모양, grain
  - [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) — 해시의 용도, 암호/비암호 구분
- 연결
  - [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md) — 대리 키 vs 자연 키
  - [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md) — 기록 시간·유효 시간 두 축
  - [database/03-normalization](../../database/03-normalization/2-summary.md) — 볼트는 정규화 쪽, 마트는 비정규화 쪽
  - [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md) · [database/12-query-optimizer-and-explain](../../database/12-query-optimizer-and-explain/2-summary.md)
  - [14-lakehouse-table-formats](../14-lakehouse-table-formats/2-summary.md) — 볼트를 레이크하우스 테이블 위에 둘 때의 저장 계층
  - [15-data-mesh-and-data-products](../15-data-mesh-and-data-products/2-summary.md) — 통합을 중앙에서 할지 도메인에서 할지
- 근거
  - Linstedt, Olschimke, 『Building a Scalable Data Warehouse with Data Vault 2.0』, Morgan Kaufmann, 2015 — 출판 정보·목차만 확인(Elsevier 도서 페이지 <https://shop.elsevier.com/books/building-a-scalable-data-warehouse-with-data-vault-20/linstedt/978-0-12-802510-9>: 4.3~4.5 Hub·Link·Satellite 정의, 6.1 PIT, 6.2 Bridge, 11.2 Hashing, 13.10 Same-As Links, 14 Information Mart). 본문 미열람.
  - Wikipedia "Data vault modeling" <https://en.wikipedia.org/wiki/Data_vault_modeling> — 2차 출처. 2000년 공개, record source·load date, Hub·Link·Satellite 필드 예시(1.0), Raw/Business Vault, 적재 순서, 차원 모델 변환.
  - AutomateDV 문서(dbt 패키지) — "Hashing" <https://automate-dv.readthedocs.io/en/latest/best_practises/hashing/>(정규화 단계·MD5 기본·SHA 선택·hashdiff·PII 소금 경고), "Hubs"·"Links"·"Satellites"(구조·`EFFECTIVE_FROM`은 DV 2.0 표준 밖), "Point In Time (PIT) tables", "NULL Handling"(성분이 모두 NULL인 키는 적재하지 않음), "Multi-Active Satellites"(child dependent key). 특정 도구의 구현이지 표준 자체는 아니다.
  - PostgreSQL 17 문서 — `md5()`·`decode()`, `EXPLAIN (ANALYZE, SUMMARY)`.
- 실험 목록(2026-10-07, PostgreSQL 17.11 `postgres:17` 컨테이너 `--network none --cpus=2`, i7-13700HX)
  - 정규화 없음/있음 Hub 행 수(3 vs 2)와 고객별 매출 분할, hashdiff 적재(5일 → 3행·2행), Satellite 곱 조인(6행·12000), PIT 경유 시각별 1행, 정규화 진단 쿼리·payload 중복 진단 쿼리(중복 행을 일부러 넣어 1행 검출).
  - Java 21 `hashKey`(`eclipse-temurin:21-jdk`, JDK 21.0.12) vs SQL `md5(upper(trim()))` — 전각 공백 키에서 해시가 갈림.
  - Satellite k = 2·8·16·32개 리포트 쿼리의 계획·실행 시간(각 3회) vs 물질화 마트.
