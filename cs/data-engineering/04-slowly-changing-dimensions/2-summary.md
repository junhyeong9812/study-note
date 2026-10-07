# data-engineering/04-slowly-changing-dimensions — 천천히 바뀌는 차원(SCD): 과거 리포트를 지키는 법 — 정리 (힌트)

## 해결하는 문제

고객이 이사하면 고객 차원의 `region`이 바뀐다. 그 값을 그냥 덮어쓰면, 팩트는 하나도 안 바뀌었는데 **지난달 지역별 매출이 바뀐다.**

```text
  9/1에 뽑은 8월 지역별 매출        10/1에 다시 뽑은 "8월" 매출 (9/15 user_001·002 서울→부산 덮어쓰기 뒤)
  busan  700                       busan  1000
  daegu 1100                       daegu  1100
  seoul  300                       (seoul 행이 사라짐)
```

- 위 숫자는 아래 실험의 실제 출력이다. 재무팀에는 "지난달 매출이 달라졌어요"로 보인다(커리큘럼 ⚠).
- 해법: 차원 속성이 바뀔 때 무엇을 할지(덮어쓰기·새 행·새 컬럼…)를 속성마다 정한다.
  - *천천히 바뀌는 차원(SCD, slowly changing dimension)*: 값이 가끔 바뀌는 차원 속성을 다루는 기법 묶음. Kimball Group Design Tip #152에 따르면 Ralph Kimball이 1996년에 이 개념을 소개했다.
  - *as-was 리포트*: 사건이 일어난 그때의 속성으로 묶은 리포트("8월에 서울 고객이 산 것").
  - *as-is 리포트*: 지금의 속성으로 묶은 리포트("지금 부산 고객들이 8월에 산 것").

쉬운 예: 반 편성.
- 3월에 1반이던 학생이 9월에 2반으로 옮겼다.
- "1학기 반별 평균"은 3월 반으로 계산해야 한다. 학생 명부를 2반으로 고쳐 쓰고 1학기 평균을 다시 내면 1반 평균이 바뀐다.
- 그래서 명부에 "3~8월 1반, 9월~ 2반" 두 줄을 남긴다.

똑같은 구조다.\
"두 줄을 남긴다"가 Type 2다.

실무 예:
- 영업 담당 지역 개편 후 지난 분기 지역별 실적이 바뀌어 성과급 계산이 흔들린다.
- 고객 등급이 바뀐 날 이전 매출이 새 등급으로 집계된다.

## 동작·원리

### 1. SCD 유형 — 바뀔 때 무엇을 하나

| 유형 | 이름(Kimball) | 하는 일 | 과거 리포트 |
|---|---|---|---|
| 0 | Retain original | 처음 값을 바꾸지 않는다 | 처음 값으로 |
| 1 | Overwrite | 덮어쓴다. 이력이 사라진다 | **현재 값으로 소급해서 바뀐다** |
| 2 | Add new row | 새 행(새 대리 키)을 추가하고 옛 행을 닫는다 | 그때 값으로(as-was) |
| 3 | Add new attribute | `prior_region` 같은 컬럼을 추가해 직전 값 하나만 남긴다 | 현재 또는 직전 값 |
| 4 | Add mini-dimension | 자주 바뀌는 속성 묶음을 작은 차원으로 떼어 팩트가 두 키를 가진다 | 미니 차원 키로 그때 값 |
| 5 | Mini-dimension + Type 1 outrigger | 4에 "현재 미니 차원 키"를 기본 차원에 Type 1로 얹는다(4 + 1) | 그때 값 + 현재 값 |
| 6 | Type 1 attributes on Type 2 | Type 2 행마다 `current_region` 컬럼을 두고 그 내구 키의 전 행을 덮어쓴다(2 + 3 + 1) | 그때 값 + 현재 값 |
| 7 | Dual Type 1 and Type 2 | 팩트에 대리 키와 내구 키를 둘 다 둔다. 대리 키 조인 = as-was, 내구 키 → 현재 행 조인 = as-is | 그때 값 + 현재 값 |

- 근거: Kimball Group Type 0~7 페이지, Design Tip #152(2013-02-05, Margy Ross). Type 6이라는 이름은 2000년 HP 엔지니어가 제안했고 "2 + 3 + 1 = 2 × 3 × 1 = 6"이라는 설명이 Design Tip #152에 있다.
- Kimball Group Type 1 페이지: Type 1은 이력을 지운다. 바뀐 속성에 걸린 집계 팩트·OLAP 큐브는 다시 계산해야 한다.
- 유형은 테이블이 아니라 **속성마다** 고른다. 이름 오타 수정은 Type 1, 지역은 Type 2, 최초 가입 채널은 Type 0처럼.

### 2. Type 2의 행 변화 — 타임라인

```text
  user_001 (내구 키 1)
  시간 ──────── 2026-01-01 ─────────────────────── 2026-09-15 ──────────────────► ∞
  key=1   seoul [2026-01-01, 2026-09-15)  is_current=f
  key=101                                          busan [2026-09-15, ∞)  is_current=t

  팩트:  8/05 구매 → customer_key=1   (그때 행)
         9/20 구매 → customer_key=101 (그때 행)
```

- 바뀌는 순간 한 트랜잭션에서 두 가지를 한다: 옛 행의 `valid_to`를 닫고 `is_current=false`, 새 행을 새 대리 키로 연다.
- Kimball Group Type 2 페이지는 최소 세 컬럼을 권한다: 행 유효 시작 일자(또는 시각), 행 만료 일자(또는 시각), 현재 행 표시.
- 이 노트는 기간을 반열린 구간 `[valid_from, valid_to)`로 둔다. 경계 시각에 두 행이 동시에 유효하지 않다([database/50](../../database/50-temporal-and-bitemporal-tables/2-summary.md) §3). 만료 일자를 포함으로 둘지 제외로 둘지는 Kimball 페이지가 정하지 않는다 — 팀이 하나로 정해 문서에 적는다.

### 3. 세 가지 키

```text
  customer_id  'user_001'   원천의 자연 키 — 원천 업무 규칙에 따라 바뀔 수 있다
  customer_dk  1            내구 키(durable key) — 웨어하우스가 매긴, 이 고객에게 변하지 않는 키
  customer_key 1, 101       대리 키(surrogate key) — 버전(행)마다 새 값, 팩트가 가리키는 키
```

- *대리 키*: 의미 없는 정수 PK. Type 2에서는 한 멤버에 행이 여럿이라 자연 키를 PK로 쓸 수 없다(Kimball, Dimension Surrogate Keys 페이지). 키 전략 일반은 [database/28](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md).
- *내구 키(durable key, durable supernatural key)*: 멤버(고객 한 명)마다 하나, 프로필이 바뀌어도 바뀌지 않는 키. 직원이 퇴사 후 재입사해 사번(자연 키)이 바뀌어도 같은 사람이면 같은 내구 키를 준다(Kimball, Natural, Durable, and Supernatural Keys 페이지).
- as-was는 대리 키로, as-is는 내구 키 → 현재 행으로 조인한다(Type 7).

### 실험: Type 1 vs Type 2, as-was vs as-is

환경: 이 호스트(i7-13700HX), `postgres:17`(PostgreSQL 17.11) 일회용 컨테이너 `--cpus=2 --network none`, psql. 고객 6명(seoul 2·busan 2·daegu 2), 8월 매출 6건(100~600). 9/15에 user_001·002가 서울 → 부산.

```text
  Type 1 (덮어쓰기)            9/1 조회:  busan 700 | daegu 1100 | seoul 300
                              10/1 조회: busan 1000 | daegu 1100                ← 8월이 바뀜

  Type 2 (새 행), 10/1 조회
    as-was (대리 키 조인)      busan 700 | daegu 1100 | seoul 300                ← 9/1과 같다
    as-is (내구 키 → 현재 행)   busan 1000 | daegu 1100                          ← "지금 지역" 기준
    9월 (9/20 user_001 700)    busan 700                                        ← 새 대리 키 101
```

- Type 1의 10/1 결과와 Type 2 as-is 결과가 같다. Type 1은 "as-is밖에 못 뽑는 Type 2"와 같다.
- Type 2는 두 관점을 다 뽑을 수 있다. 어느 쪽을 기본 리포트로 할지는 업무가 정한다.

## 쓰이는 자료구조·알고리즘

- **구간 비교** — 유효 기간은 구간이다. "이 시각에 유효한 행"은 점이 구간에 드는지, "기간 겹침"은 두 구간의 교차 여부다. 반열린 구간이면 `a.from < b.to AND b.from < a.to`. PostgreSQL 범위 타입의 `&&`가 이 연산이다([database/50](../../database/50-temporal-and-bitemporal-tables/2-summary.md)).
- **인터벌 트리와 GiST** — 기간 겹침을 빠르게 찾는 구조들. PostgreSQL의 `EXCLUDE USING gist`는 인터벌 트리가 아니라 GiST 인덱스로 겹침을 검사한다. 원리는 커리큘럼 `data-structure/42-interval-tree`(실제 폴더 [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)).
- **정렬 + 이웃 비교(스위핑)** — 멤버별로 시작 시각 순 정렬한 뒤 "다음 행의 시작 = 이 행의 끝"을 확인하면 빈틈과 겹침을 한 번에 찾는다. SQL에서는 윈도 함수 `lead()`([database/05](../../database/05-window-functions-and-cte/2-summary.md)).
- **부분 유일 인덱스** — `UNIQUE (customer_dk) WHERE is_current`는 "현재 행은 멤버당 최대 하나"를 강제한다. 술어를 만족하는 행 사이의 유일성만 걸므로(PostgreSQL 17 문서 11.8) 현재 행이 0개인 멤버는 막지 못한다.

## 적용 — 풀어나가는 법

### 1. 속성마다 유형을 정한다

| 속성 | 유형 | 이유 |
|---|---|---|
| `customer_name` 오타 | 1 | 과거 리포트에 옛 오타를 남길 이유가 없다 |
| `region` | 2 | 지역별 실적이 소급해서 바뀌면 안 된다 |
| `signup_channel` | 0 | 처음 값의 의미다 |
| `current_region` | 6의 Type 1 컬럼 | "지금 지역" 리포트를 조인 하나로 |

### 2. Type 2 적재 SQL (PostgreSQL 17)

```sql
BEGIN;
-- 1) 바뀐 멤버의 현재 행을 닫는다
UPDATE dim_customer d
   SET valid_to = s.changed_at, is_current = false
  FROM stg_customer s
 WHERE d.customer_id = s.customer_id AND d.is_current AND d.region IS DISTINCT FROM s.region;
-- 2) 새 행을 연다 (새 대리 키, 같은 내구 키)
INSERT INTO dim_customer(customer_key, customer_dk, customer_id, region, valid_from, valid_to, is_current)
SELECT nextval('dim_customer_key_seq'), d.customer_dk, s.customer_id, s.region, s.changed_at, 'infinity', true
  FROM stg_customer s
  JOIN dim_customer d ON d.customer_id = s.customer_id AND d.valid_to = s.changed_at AND NOT d.is_current;
COMMIT;
```

- 같은 환경에서 돌려 봤다(시퀀스 시작 100, 스테이징 3명 중 지역이 바뀐 사람은 user_001뿐): user_001만 `1 | seoul | [01-01, 09-15) | f`와 `100 | busan | [09-15, ∞) | t` 두 행이 되고, user_002·003은 그대로였다.
- 닫기와 열기를 한 트랜잭션에 둔다. 사이에 실패하면 "현재 행 0개"(빈틈) 또는 "현재 행 2개"(겹침)가 남는다.
- 이 SQL은 자연 키 `customer_id`가 바뀌지 않는다고 가정한다. 자연 키가 바뀌는 원천이면 옛 키·새 키를 같은 내구 키로 잇는 매핑을 두고, 적재와 팩트 키 조회 모두 그 매핑으로 내구 키를 먼저 찾는다(Kimball Design Tip #147).
- 이 SQL은 형태를 보이는 예시다. 같은 배치에 같은 멤버의 변경이 여러 번 있거나, 변경 시각이 현재 행 시작보다 이른(소급) 경우는 따로 처리해야 한다.
- 이 SQL은 **멱등하지 않다**. 같은 스테이징으로 한 번 더 돌리면 1)은 0행이지만, 2)는 이미 닫힌 옛 행(`valid_to = changed_at`)을 다시 찾아 새 행을 또 연다. 사실 점검 때 재실행해 보니 user_001의 현재 행이 `100`·`101` 두 개가 되었다(장애 §2·§4의 모양).
- 닫은 행만 열게 하려면 UPDATE가 실제로 닫은 행을 `RETURNING`으로 받아 INSERT한다. 같은 환경에서 두 번 돌려도 user_001의 현재 행은 `100` 하나였다.

```sql
WITH closed AS (
  UPDATE dim_customer d
     SET valid_to = s.changed_at, is_current = false
    FROM stg_customer s
   WHERE d.customer_id = s.customer_id AND d.is_current AND d.region IS DISTINCT FROM s.region
  RETURNING d.customer_dk, s.customer_id, s.region, s.changed_at)
INSERT INTO dim_customer(customer_key, customer_dk, customer_id, region, valid_from, valid_to, is_current)
SELECT nextval('dim_customer_key_seq'), customer_dk, customer_id, region, changed_at, 'infinity', true FROM closed;
```

### 3. 팩트 적재: 대리 키는 "사건 시각" 기준으로 찾는다

```sql
SELECT customer_key FROM dim_customer
WHERE customer_id = :customer_id AND :sold_at >= valid_from AND :sold_at < valid_to;
```

- 실험: 8/30 user_002 구매가 9/20에 늦게 도착했다.

```text
  is_current로 찾기          customer_key 102  busan   ← 8월 매출이 부산으로 잘못 붙는다
  as-of(판매 시각)로 찾기     customer_key 2    seoul   ← 맞다
```

- 현재 행으로만 키를 찾으면 늦게 온 팩트가 엉뚱한 버전에 붙는다. 에러는 없다.
- 차원 변경 자체가 늦게 도착(소급)하면 차원에 새 행을 넣고, 이미 적재된 관련 팩트를 다시 써야(restate) 한다(Kimball, Late Arriving Dimensions 페이지).

### 4. 진단 쿼리 — 겹침·빈틈·현재 행 중복

```sql
-- (1) 같은 내구 키의 기간 겹침
SELECT a.customer_dk, a.customer_key AS k1, b.customer_key AS k2,
       tstzrange(a.valid_from, a.valid_to) * tstzrange(b.valid_from, b.valid_to) AS overlap
FROM dim_customer a JOIN dim_customer b
  ON a.customer_dk = b.customer_dk AND a.customer_key < b.customer_key
 AND tstzrange(a.valid_from, a.valid_to) && tstzrange(b.valid_from, b.valid_to);

-- (2) 이웃 행 대조: 다음 시작 < 이 끝 = 겹침, 다음 시작 > 이 끝 = 빈틈
SELECT customer_dk, customer_key, valid_to AS this_end, next_start,
       CASE WHEN next_start < valid_to THEN 'overlap' ELSE 'gap' END AS kind
FROM (SELECT *, lead(valid_from) OVER (PARTITION BY customer_dk ORDER BY valid_from) AS next_start
      FROM dim_customer) x
WHERE next_start IS NOT NULL AND next_start <> valid_to;

-- (3) 현재 행이 둘 이상
SELECT customer_dk, count(*) FROM dim_customer WHERE is_current GROUP BY 1 HAVING count(*) > 1;

-- (4) 현재 행이 없는 멤버 (마지막 행을 닫고 새 행을 안 넣었다 — (2)는 이웃 행이 없어 못 잡는다)
SELECT customer_dk, max(valid_to) AS last_end
FROM dim_customer GROUP BY 1 HAVING count(*) FILTER (WHERE is_current) = 0;
```

- (4)는 판정 때 따로 돌려 봤다(같은 이미지): 행이 `[01-01, 09-15)` 하나뿐인 멤버는 (2)에서 0행, (4)에서 `2 | 2026-09-15 00:00:00+00`으로 잡혔다. 원천에서 삭제된 멤버처럼 현재 행이 없는 것이 정상인 경우는 빼고 본다.

### 실험: 겹침·빈틈이 기간 조인에 주는 영향

같은 환경. Type 2 차원을 복사한 뒤 버그 적재 두 개를 넣었다.
- user_003: 9/10 이사를 처리하면서 옛 행을 닫지 않음 → 겹침 + 현재 행 2개.
- user_005: 옛 행을 9/01에 닫았는데 새 행은 9/05부터 → 빈틈.

```text
  진단 (1) 겹침      customer_dk 3 | k1 3 | k2 103 | ["2026-09-10 00:00:00+00",infinity)
  진단 (2) 이웃 대조  3 | 3 | infinity               | 2026-09-10 | overlap
                     5 | 5 | 2026-09-01 00:00:00+00 | 2026-09-05 | gap
  진단 (3) 현재 행   customer_dk 3 | count 2

  기간 조인(as-of) 매출 — 9/12 user_003 구매 900, 9/03 user_005 구매 800
   customer_id | amount | matched_rows | counted
   user_003    |    900 |            2 |    1800     ← 두 번 세짐
   user_005    |    800 |            0 |   (NULL)    ← 빠짐
```

- 겹침은 매출을 중복시키고, 빈틈은 매출을 빠뜨린다(커리큘럼 ⚠). 둘 다 에러가 없다.

### 5. 예방: 제약으로 적재 시점에 거부

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE dim_customer ADD CONSTRAINT no_overlap
  EXCLUDE USING gist (customer_dk WITH =, tstzrange(valid_from, valid_to) WITH &&);
CREATE UNIQUE INDEX one_current ON dim_customer(customer_dk) WHERE is_current;
```

```text
  겹치는 행 INSERT  → ERROR: conflicting key value violates exclusion constraint "no_overlap"
  현재 행 2번째     → ERROR: duplicate key value violates unique constraint "one_current"
```

- 두 제약 모두 실험에서 버그 적재를 거부했다.
- 빈틈은 이 두 제약으로 막히지 않는다. 현재 행 0개도 막히지 않는다. 진단 (2)·(4)를 적재 후 검사로 돌린다(이 영역 [10](../10-data-quality-and-data-observability/2-summary.md)).
- `EXCLUDE`의 원리와 PostgreSQL 18의 `WITHOUT OVERLAPS`는 [database/50](../../database/50-temporal-and-bitemporal-tables/2-summary.md) §4·§5. 웨어하우스 제품이 이런 제약을 강제하지 않으면 진단 쿼리가 유일한 방어선이 된다.

### 6. 앱 코드에서 as-of 조회 (Java 21)

```java
record CustomerVersion(int key, int durableKey, String region, Instant from, Instant to) {
    boolean validAt(Instant t) { return !t.isBefore(from) && t.isBefore(to); }   // [from, to)
}

static int surrogateKeyAt(List<CustomerVersion> versions, Instant soldAt) {
    List<CustomerVersion> hit = versions.stream().filter(v -> v.validAt(soldAt)).toList();
    if (hit.size() != 1) {                       // 0 = 빈틈, 2+ = 겹침 — 조용히 고르지 않는다
        throw new IllegalStateException("versions at " + soldAt + " = " + hit.size());
    }
    return hit.get(0).key();
}
```

- 0개·2개 이상을 예외로 낸다. "첫 번째 것을 고른다"로 덮으면 겹침이 숨는다.
- 실행(Java 21.0.12, JDK만): 8/30 → 2, 9/15 00:00 → 102(경계 시각은 새 행), 겹침 데이터 → `versions at 2026-09-12T10:00:00Z = 2`, 빈틈 데이터 → `versions at 2026-09-03T10:00:00Z = 0`.

## 장애 시나리오와 대처

### 1. Type 1 덮어쓰기 → 과거 리포트 숫자가 소급해서 바뀐다 (⚠ 커리큘럼)

- **현상**: "지난달 지역별 매출이 달라졌어요."
- **보이는 형태**: 팩트 테이블 행 수·합계는 그대로. 지역별 분포만 바뀐다(실험: 8월 seoul 300 → 행 없음, busan 700 → 1000). 차원 테이블에 `updated_at`이 최근인 행.
- **원인**: 지역을 Type 1로 덮어써 이력이 사라졌다. 리포트는 현재 값으로 다시 묶였다.
- **대처**: 그 속성을 Type 2로 바꾼다. 이미 지운 이력은 원천의 변경 이력(감사 로그·CDC·스냅샷)이 있어야 복원할 수 있다. Type 1로 남길 속성이면 관련 집계 테이블·큐브를 다시 계산하고, 마감된 리포트는 스냅샷으로 따로 보관한다.

### 2. Type 2 유효 기간 겹침 → 기간 조인에서 매출 중복 (⚠ 커리큘럼)

- **현상**: 9월 매출이 결제 합계보다 많다.
- **보이는 형태**: 실험처럼 한 팩트가 차원 두 행에 맞아 `matched_rows 2`, 900이 1800으로 세진다. 진단 (1)·(3)에 같은 멤버.
- **원인**: 새 행을 열면서 옛 행을 닫지 않았다(닫기 UPDATE 실패, 트랜잭션 분리, 재실행 중복).
- **대처**: 닫기·열기를 한 트랜잭션에 둔다. `EXCLUDE` 제약과 `is_current` 부분 유일 인덱스를 건다. 이미 생긴 겹침은 옛 행의 `valid_to`를 새 행 시작으로 고치고, 영향받은 팩트 키를 다시 매긴다.

### 3. Type 2 유효 기간 빈틈 → 기간 조인에서 매출 누락 (⚠ 커리큘럼)

- **현상**: 특정 고객의 며칠 치 매출이 지역별 리포트에서 빠진다.
- **보이는 형태**: 실험의 user_005처럼 `matched_rows 0`. 진단 (2)의 `gap`. inner join이면 행이 사라지고, left join이면 지역이 NULL.
- **원인**: 옛 행을 닫은 시각과 새 행의 시작 시각이 다르다(타임존 변환, "끝 = 다음 시작 − 1일" 같은 닫힌 구간 규칙과 반열린 규칙 혼용).
- **대처**: 새 행의 `valid_from`을 옛 행의 `valid_to`에서 그대로 가져온다(같은 값 하나를 두 곳에 쓴다). 진단 (2)를 적재 후 검사로 돈다.

### 4. 현재 행 플래그가 둘인 멤버 (⚠ 커리큘럼)

- **현상**: "현재 고객 수"가 원천 고객 수보다 많다. as-is 리포트에서 한 고객이 두 지역에 나온다.
- **보이는 형태**: 진단 (3)에 `count 2`. Type 7 조인(내구 키 → 현재 행)에서 팩트가 2배.
- **원인**: 겹침과 같은 적재 버그, 또는 `is_current`를 기간과 따로 관리하다 어긋났다.
- **대처**: `UNIQUE (customer_dk) WHERE is_current`(2개 이상을 막는다. 0개는 진단 (4)로 본다). `is_current`를 `valid_to = 'infinity'`에서 계산되는 값으로 두는 것도 방법이다.

### 5. 늦게 온 팩트가 현재 행에 붙는다

- **현상**: 지난달 말 매출 일부가 이번 달 바뀐 지역으로 잡힌다.
- **보이는 형태**: 실험처럼 8/30 판매가 `customer_key 102(busan)`. 차원은 정상이다.
- **원인**: 팩트 적재가 대리 키를 `is_current`로 찾았다.
- **대처**: 사건 시각으로 as-of 조회한다(적용 §3). 이미 잘못 붙은 팩트는 사건 시각으로 키를 다시 찾아 갱신한다.

## 핵심 문장

- 차원 속성을 덮어쓰면(Type 1) 팩트가 그대로여도 과거 리포트가 소급해서 바뀐다(실험: 8월 busan 700 → 1000).
- Type 2는 바뀔 때 옛 행을 닫고 새 대리 키로 새 행을 연다. 팩트는 그때의 대리 키를 가리키므로 과거 리포트가 유지된다.
- 대리 키는 버전마다, 내구 키는 멤버마다 하나다. 대리 키 조인은 as-was, 내구 키 → 현재 행 조인은 as-is(Type 7)다.
- 유효 기간이 겹치면 기간 조인에서 매출이 중복되고(900 → 1800), 비면 빠진다(800 → 0). `EXCLUDE` 제약과 이웃 행 대조로 막고 찾는다.
- 팩트의 대리 키는 현재 행이 아니라 사건 시각으로 찾는다. 늦게 온 팩트가 엉뚱한 버전에 붙는다.

## 관련 주제·근거

- 선행
  - [03-dimensional-modeling](../03-dimensional-modeling/2-summary.md) — 팩트·차원·대리 키
- 연결
  - [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md) — 유효 시간·기록 시간, 반열린 구간, `EXCLUDE`·`WITHOUT OVERLAPS`
  - [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md) — 대리 키와 자연 키
  - [database/05-window-functions-and-cte](../../database/05-window-functions-and-cte/2-summary.md) — `lead()`
  - [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md) — 커리큘럼 `data-structure/42-interval-tree`
- 후속
  - [08-idempotent-pipelines-and-backfill](../08-idempotent-pipelines-and-backfill/2-summary.md)(시점별 규칙·재계산) · [13-data-vault](../13-data-vault/2-summary.md)(Satellite = 시점별 속성)
- Kimball Group "Dimensional Modeling Techniques" 하위 페이지(2026-10-07 열람): Type 0: Retain Original, Type 1: Overwrite, Type 2: Add New Row, Type 3: Add New Attribute, Type 4: Add Mini-Dimension, Type 5, Type 6, Type 7, Dimension Surrogate Keys, Natural/Durable/Supernatural Keys, Late Arriving Dimensions <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/>
- Margy Ross, Kimball Design Tip #152 "Slowly Changing Dimension Types 0, 4, 5, 6 and 7"(2013-02-05) — 1996년 SCD 소개, 『The Data Warehouse Toolkit』 3판(2013)에서 유형 번호 부여, Type 5 = 4 + 1, Type 6 = 2 + 3 + 1(2000년 HP 엔지니어 제안) <https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/>
- PostgreSQL 17 문서: 범위 타입(8.17)·`EXCLUDE`(CREATE TABLE)·`btree_gist` — 상세 근거는 database/50.
- 실험(이 호스트 i7-13700HX, `--cpus=2 --network none`, PostgreSQL 17.11)
  - Type 1 덮어쓰기 전후 8월 지역별 매출(busan 700 → 1000, seoul 300 → 없음), Type 2 as-was(유지)·as-is(Type 7 조인)·9월 새 대리 키.
  - 버그 차원: 겹침(user_003)·빈틈(user_005) 진단 쿼리 3종, 기간 조인 900 → 1800 중복·800 누락.
  - `EXCLUDE USING gist` 겹침 거부, `UNIQUE … WHERE is_current` 현재 행 2개 거부.
  - 늦게 온 팩트: `is_current` 조회 key 102(busan) vs as-of 조회 key 2(seoul).
  - Type 2 적재 SQL(닫기 UPDATE + 열기 INSERT) 실행 확인, 같은 배치 재실행 시 현재 행 2개(사실 점검), `RETURNING` CTE 판은 재실행해도 1개, Java 21.0.12(`eclipse-temurin:21-jdk`) as-of 조회 — 경계·겹침·빈틈 예외.
