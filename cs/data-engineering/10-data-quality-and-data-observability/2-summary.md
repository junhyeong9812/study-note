# data-engineering/10-data-quality-and-data-observability — 파이프라인 안의 품질 검사와 데이터 관측 — 정리 (힌트)

## 해결하는 문제

매일 새벽 적재 잡이 돈다. 오케스트레이터 화면은 나흘 내내 초록이다.

```text
  잡 실행        10-01 ✅   10-02 ✅   10-03 ✅   10-04 ✅      ← 종료 코드 0, 에러 없음
  적재 행 수       400        400         0        400        ← 10-03은 상류가 빈 파일을 줬다
  customer_id NULL  0%         0%         —        40%        ← 10-04는 합계가 멀쩡해 보인다
```

- 잡의 성공은 "SQL이 오류 없이 끝났다"는 뜻이다. "맞는 데이터가 들어왔다"는 뜻이 아니다.
  - `INSERT ... SELECT`가 0행을 넣어도 `INSERT 0 0`이고 종료 코드는 0이다(아래 실험).
- 그래서 데이터 자체를 재는 장치가 따로 필요하다.
  - *데이터 품질 검사(data test)*: 적재된 데이터에 대해 "이 조건을 만족해야 한다"를 실행하는 검사. 예: `order_id` 유일, `customer_id` NULL 없음, `status`는 정해진 값만.
  - *데이터 관측(data observability)*: 개별 규칙을 미리 쓰지 않아도, 테이블의 신선도·볼륨·스키마·분포·계보를 계속 재서 평소와 다른 변화를 잡는 일.
    - 흔한 오해: "관측 도구가 있으면 품질 검사가 필요 없다." — 관측은 "평소와 다르다"를 잡고, 검사는 "규칙 위반"을 잡는다. 평소에도 틀려 있던 데이터는 관측의 기준선이 그 틀린 값을 정상으로 배운다(해석).

쉬운 예: 정수기 관리다.
- 정수기 전원이 켜져 있다(잡 성공). 그런데 물통이 비었거나(0행), 물이 탁하다(NULL 급증).
- 전원 표시등만 보지 말고, 수위계(볼륨)·마지막 교체일(신선도)·수질 검사지(분포)를 따로 본다.

똑같은 구조다.\
실무 예: 상류 내보내기가 빈 파일을 만들었고 적재 잡은 성공했다. 다음 날 아침 대시보드는 "어제 매출 0원"이 아니라 그 날짜가 **아예 빠진 그래프**를 보였다. 사람들은 어제 데이터라고 믿고 그제 숫자로 판단했다.

## 동작·원리

### 1. 관측 5축 — 무엇을 재나

```text
             ┌── 신선도(freshness)   마지막 데이터가 언제 것인가       now() - max(event_time)
             ├── 볼륨(volume)        몇 행이 들어왔나                 행 수, 파티션별 행 수
  테이블 ────┼── 스키마(schema)      컬럼·타입이 바뀌었나             information_schema diff
             ├── 분포(distribution)  값이 평소 범위인가               NULL 비율, 고유값 수, 평균·분위수
             └── 계보(lineage)       어디서 와서 어디로 가나          11번 — 원인과 영향 범위
```

- 이 다섯 축은 Monte Carlo의 Barr Moses가 정리한 "5 pillars"다. 글쓴이는 2019년에 "data observability"라는 말을 만들었다고 적는다.
  - Internet Archive의 2022-04-25 사본(페이지 표기 "Updated March 31, 2022")은 Freshness·Distribution·Volume·Schema·Lineage를 든다.
  - 2026-09-25 갱신판은 Distribution 자리에 **Quality**(NULL 비율·고유값 비율·허용 범위)를 두고 같은 다섯 개를 설명한다. 이름이 바뀌었을 뿐 재는 대상은 비슷하다(해석).
- 볼륨 예시 문장(원문): "200 million rows suddenly turns into 5 million, you should know."

### 2. 품질 검사 — "실패 행을 고르는 쿼리"

```text
  규칙(단언)                       검사 쿼리 = 규칙을 어기는 행을 고른다      통과 조건
  NULL 아닌 order_id는 유일        WHERE order_id IS NOT NULL
                                   GROUP BY order_id HAVING count(*) > 1      0행
  customer_id는 NULL 아님          WHERE customer_id IS NULL                  0행
  NULL 아닌 status ∈ {PAID, SHIPPED} WHERE status NOT IN (...)                0행
  NULL 아닌 customer_id는 dim에 있음 WHERE customer_id IS NOT NULL
                                     AND NOT EXISTS (SELECT ... dim)          0행
```

- dbt 문서: 데이터 테스트는 단언을 **반증하는 실패 행을 고르는 select 문**이다. 0행이면 통과한다.
  - 내장 generic 테스트는 네 개다: `unique`, `not_null`, `accepted_values`, `relationships`(참조 무결성).
  - 한 번 쓰는 SQL 파일은 singular 테스트다.
  - dbt 기본 매크로(dbt-adapters `generic_test_sql/`)에서 `unique`·`relationships`는 `IS NOT NULL`로 NULL을 빼고 센다. `accepted_values`의 `NOT IN`도 NULL 행을 고르지 않는다(`NULL NOT IN (...)`은 참이 아니라 NULL). 그래서 NULL 금지는 `not_null`로 따로 건다. NULL도 위반으로 보려면 `status IS NULL OR status NOT IN (...)`로 쓴다.
- dbt의 차단·경고 설정: `severity`(`error` 또는 `warn`, 기본 `error`), `error_if`·`warn_if`(실패 행 수 조건, 기본 `!=0`).
  - 문서 예시: `error_if: ">1000"`, `warn_if: ">10"` — 실패 행이 10건을 넘으면 경고, 1000건을 넘으면 오류다.
  - `severity: warn`인 테스트도 `--warn-error`를 주면 오류로 올라간다.
- Great Expectations(GX Core 1.23.2 문서): 같은 생각을 *Expectation*("데이터에 대한 검증 가능한 단언")이라 부른다. 예: `gx.expectations.ExpectColumnValuesToNotBeNull`, `ExpectColumnValuesToBeUnique`(GX 0.18 이전 문서는 같은 것을 `expect_column_values_to_not_be_null` 같은 메서드 이름으로 적는다).
- ODCS 계약(09번)의 품질 칸 `nullValues`·`duplicateValues`·`rowCount` 등도 이 검사들로 옮겨진다.

### 3. 차단 vs 경고 — 어디에 두나

```text
  적재 ──▶ [검사] ──▶ 공개 테이블 ──▶ 대시보드
             │
             ├─ 차단(error): 실패하면 공개 테이블로 넘기지 않는다 → 데이터는 "늦음", 대신 틀린 숫자가 안 나감
             └─ 경고(warn) : 넘기고 알린다                      → 데이터는 "제때", 대신 틀릴 수 있음
```

- 차단해야 할 것: 하류가 틀린 결정을 내리는 위반 — 0행, 키 중복(합계 2배), 참조 깨짐.
- 경고로 둘 것: 해석이 필요한 변화 — 분포 이동, 새 enum 값, 소폭 볼륨 감소.
- dbt의 `severity: error`는 이 그림의 "공개 전 차단"과 다르다. dbt 데이터 테스트는 모델이 만들어진 **뒤** 돈다. 실패하면 `dbt build`에서 하류 노드를 건너뛰게(SKIP) 할 뿐, 이미 갱신된 그 테이블을 되돌리지 않는다(dbt `build` 문서). 공개 자체를 막으려면 검증용 테이블에서 검사한 뒤 게시하는 단계를 따로 둔다.
- 차단은 신선도를 희생한다. 그래서 차단된 테이블은 **신선도 경보**로 보이게 해야 "조용히 늦은" 상태가 되지 않는다(해석).
- 검사가 너무 엄격하면 매일 경고가 나고, 사람들이 경고를 무시하게 된다(알람 피로). 아래 실험의 "전일 대비 ±5%" 규칙이 그 예다.

### 실험: 잡은 성공, 0행 적재 (PostgreSQL 17)

(실험, `postgres:17` — PostgreSQL 17.11, `--network none`, 합성 주문. 날짜마다 같은 트랜잭션 안에서 "그 날짜 삭제 + 다시 넣기 + 감사 기록"을 하는 잡을 psql로 4번 돌렸다.)

```sql
BEGIN;
DELETE FROM fct_orders WHERE day = :d;
INSERT INTO fct_orders SELECT * FROM stg_orders WHERE day = :d;
INSERT INTO load_audit SELECT :d, count(*), now() FROM fct_orders WHERE day = :d;
COMMIT;
```

```text
BEGIN
DELETE 0
INSERT 0 0          ← 10-03: 스테이징이 비어 0행
INSERT 0 1
COMMIT
job day=2026-10-03 exit=0
```

- 네 번 모두 `exit=0`. 오케스트레이터가 종료 코드만 본다면 네 번 다 초록이다.

검사를 붙인 결과:

```text
== 볼륨 검사: 0행 또는 직전 3일 평균의 50% 미만
 2026-10-01 |         400 |           | ok
 2026-10-02 |         400 |     400.0 | ok
 2026-10-03 |           0 |     400.0 | FAIL zero rows
 2026-10-04 |         400 |     266.7 | ok
== 합계만 보면: 일자별 주문 수·매출
 2026-10-01 |   400 | 559400
 2026-10-02 |   400 | 559400
 2026-10-04 |   400 | 559400
== 분포 검사: 일자별 customer_id NULL 비율
 2026-10-01 | 0.0     2026-10-02 | 0.0     2026-10-04 | 40.0
== dbt식 테스트: not_null(customer_id) 160 · unique(order_id) 0 · accepted_values(status) 0 · relationships 0
== 신선도: 각 적재 다음 날 09:00에 본 최신 이벤트 시각과 지연 (임계 30시간)
 2026-10-01 | 2026-10-02 09:00:00 | 2026-10-01 06:40:00+00 | 1 day 02:20:00  | fresh
 2026-10-02 | 2026-10-03 09:00:00 | 2026-10-02 06:40:00+00 | 1 day 02:20:00  | fresh
 2026-10-03 | 2026-10-04 09:00:00 | 2026-10-02 06:40:00+00 | 2 days 02:20:00 | STALE
 2026-10-04 | 2026-10-05 09:00:00 | 2026-10-04 06:40:00+00 | 1 day 02:20:00  | fresh
== 신선도(잡 기준): 마지막 적재 완료 시각은 방금 — job_ran_recently = t
```

- 0행은 볼륨 검사와 신선도 검사 **둘 다**에서 잡혔다. 이 실험에서 신선도는 "잡이 돈 시각"이 아니라 "데이터 안의 최신 이벤트 시각"으로 재야 잡혔다.
  - 늦게 도착하는 과거 이벤트·백필만 들어오는 적재에서는 `max(event_time)`이 오래돼도 적재는 최신일 수 있다. 그래서 SLA가 묻는 것(일어난 일의 최신성 vs 적재의 최신성)에 따라 이벤트 시각·적재 시각 컬럼(dbt freshness의 `loaded_at_field`)·저장소 메타데이터 중 기준을 고른다. 잡 기준 신선도는 `t`(방금 돌았다)라 아무것도 말해 주지 않는다.
- 10-04의 customer_id NULL 40%는 주문 수·매출 합계로는 보이지 않았다(세 날 모두 400건·559,400). 분포 검사(NULL 비율)와 `not_null` 테스트(실패 160행)만 잡았다.
- 10-04의 "직전 3일 평균"은 0이 섞여 266.7로 내려갔다. **이상값이 기준선을 오염시킨다.** 다음 실험의 주제다.

### 실험: 볼륨 감시 규칙 비교 — 고정 임계 vs EWMA (Java 모형)

(실험, `Volume.java`, eclipse-temurin:21-jdk — OpenJDK 21.0.12. 합성 일별 행 수 70일: 평일 약 10,000·주말 약 6,000, 하루 0.4% 성장, 표준편차 3% 잡음, 난수 시드 42. 주입한 이상 3건: 45일 0행, 55일 55%로 감소, 62일 1.9배. 앞 28일은 학습 기간.)

- *EWMA(지수 가중 이동 평균)*: 새 값에 가중치 α, 지난 평균에 1−α를 주어 갱신하는 평균. 최근 값을 더 반영하고 전체 이력을 저장하지 않는다.

```java
void update(double x) {                 // 이 실험에서 쓴 갱신식
    if (n++ == 0) { mean = x; return; }
    double d = x - mean;
    mean += alpha * d;                   // 평균 ← 평균 + α(x − 평균)
    var = (1 - alpha) * (var + alpha * d * d);   // 지수 가중 분산
}
// 판정: |x − mean| > 3σ 이면 이상. 이상으로 판정한 값은 기준선 갱신에서 뺀다(오염 방지).
```

```text
규칙                             탐지(주입 3건 중) / 오경보(정상 39일 중)
rows == 0                      1 / 0
전일 대비 ±5%                    3 / 21
EWMA 전체 3σ                    2 / 2
EWMA 전체 3σ(이상값도 학습)      1 / 0
EWMA 요일별 3σ(하한 없음)        3 / 9
EWMA 요일별 max(3σ, 15%)         3 / 2
```

```text
day 45 dow 3 rows      0 | 전체EWMA   10484± 6377 | 학습판   10484± 6377 | ...
day 46 dow 4 rows  11447 | 전체EWMA   10484± 6377 | 학습판    8387±13813 | ...   ← 0을 배운 뒤 밴드가 ±13,813로 넓어짐
day 62 dow 6 rows  13424 | 전체EWMA   11004± 7023 | ...                            ← 주말 1.9배인데 전체 밴드 안
```

관찰과 해석(이 합성 데이터 한정):
- `rows == 0`은 오경보가 없지만 0행만 잡는다. 반토막·2배는 못 잡았다.
- "전일 대비 ±5%"는 셋 다 잡았지만 정상 39일 중 21일 울렸다. 평일↔주말 전환마다 울린다. 이런 규칙은 곧 무시된다(알람 피로).
- 전체 EWMA는 평일·주말이 섞여 σ가 커지고(밴드 약 ±6,400) 주말 1.9배(62일)를 놓쳤다.
- 이상값도 학습한 판은 0을 배운 다음 날 밴드가 ±13,813로 넓어졌다. 열흘 뒤 55일에도 밴드가 10,183±8,050으로 넓게 남아 반토막(3,842행)을 놓쳤다. **이상으로 판정한 값은 기준선에 섞지 않는다.**
- 요일별 EWMA는 계절성을 따로 배워 셋 다 잡았다. 하지만 하한이 없으면 요일마다 표본이 적어 σ가 작게 잡히고, 성장 추세만으로도 9번 울렸다. 상대 하한(15%)을 두자 오경보가 2번으로 줄었다.
- 숫자는 이 합성 데이터·이 매개변수(α 0.2/0.3, 3σ, 15%)에서 나온 것이다. 실제 테이블은 계절성·성장·이벤트 날짜가 다르므로 과거 데이터로 다시 맞춰야 한다.

## 쓰이는 자료구조·알고리즘

- **이동 평균·EWMA** — 행 수·NULL 비율 같은 시계열의 기준선. EWMA는 상태가 평균·분산 두 개라 테이블 수천 개에 붙여도 싸다. 계절성은 요일·시간대별로 기준선을 나눠 다룬다.
- **분포 스케치** — 고유값 수(HyperLogLog), 값별 빈도 추정(Count-Min — 스케치만으로는 상위 값 목록을 복원하지 못해 후보 값을 따로 유지하거나 Frequent Items 계열 스케치를 쓴다) 같은 확률적 요약으로 큰 테이블의 분포를 싸게 잰다([data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md)). 어제와 오늘의 고유 고객 수가 크게 다르면 조인 키·필터 이상을 의심한다.
- **실패 행 쿼리** — 유일성(`GROUP BY ... HAVING`), 참조(`NOT EXISTS` 반조인), 허용값(`NOT IN`). PostgreSQL은 반조인을 비용 추정에 따라 중첩 루프·병합·해시 조인 중 하나로 실행한다. 실제 방식은 `EXPLAIN`으로 본다([database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md)).
- **히스테리시스** — 경보를 켜는 임계와 끄는 임계를 다르게 두어 경계에서 깜빡이지 않게 한다([reliability/33-hysteresis-and-flapping](../../reliability/33-hysteresis-and-flapping/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. 테이블마다 **신선도 기준 컬럼**(이벤트 시각 또는 적재 시각 — SLA가 묻는 것에 맞춰)과 기대 갱신 주기를 정한다. 계약(09번)의 SLA 칸이 출처다.
2. 적재 잡이 끝날 때 **행 수를 감사 테이블에 남긴다**(실험의 `load_audit`). 볼륨 기준선의 재료다.
3. 키·참조·허용값 검사를 넣는다. 합계를 2배로 만들거나 행을 빠뜨리는 위반은 차단, 나머지는 경고.
4. NULL 비율·고유값 수 같은 분포 지표를 컬럼별로 쌓고, 요일별 기준선과 비교한다.
5. 경보마다 **소유자와 대응 절차**를 붙인다. 소유자 없는 경보는 무시된다.

### 2. 신선도·볼륨 진단 쿼리 (PostgreSQL 17)

```sql
-- 신선도: 데이터 안의 최신 이벤트 시각 기준
SELECT now() - max(event_time) AS lag,
       now() - max(event_time) > interval '30 hours' AS stale
FROM fct_orders;

-- 볼륨: 오늘 적재 행 수 vs 같은 요일 최근 4주 평균
SELECT a.day, a.rows_loaded,
       (SELECT avg(b.rows_loaded) FROM load_audit b
         WHERE b.day IN (a.day - 7, a.day - 14, a.day - 21, a.day - 28)) AS same_dow_avg
FROM load_audit a ORDER BY a.day DESC LIMIT 1;

-- 분포: 컬럼별 NULL 비율
SELECT day, round(100.0 * count(*) FILTER (WHERE customer_id IS NULL) / count(*), 1) AS null_pct
FROM fct_orders GROUP BY day ORDER BY day DESC LIMIT 7;

-- 통계로 대략 보기: 플래너 통계의 NULL 비율·고유값 추정 (ANALYZE 이후 값)
SELECT attname, null_frac, n_distinct FROM pg_stats WHERE tablename = 'fct_orders';
```

- `pg_stats`는 `ANALYZE`가 표본으로 만든 추정값이다. 정확한 검사가 아니라 싼 1차 신호로 쓴다.
- 이 절의 쿼리 중 NULL 비율 쿼리만 실험(위)에서 같은 형태로 실행했다. 나머지(같은 요일 평균·`pg_stats`·`now()` 기준 신선도)는 형태 예시이고 이 노트에서 실행하지 않았다.

### 3. 검사 결과를 지표로 내보내기 (Java)

```java
// 적재 직후 검사 결과를 지표로 — 대시보드·경보는 reliability/16의 방식 그대로
long rows = jdbc.queryForObject("SELECT count(*) FROM fct_orders WHERE day = ?", Long.class, day);
long nulls = jdbc.queryForObject("SELECT count(*) FROM fct_orders WHERE day = ? AND customer_id IS NULL", Long.class, day);
rowsLoaded.set(rows);     // 게이지는 시작할 때 한 번만 등록하고, 적재마다 값만 바꾼다
nullRows.set(nulls);
if (rows == 0) throw new IllegalStateException("fct_orders " + day + ": 0 rows loaded");   // 차단 규칙은 잡을 실패시킨다

// 시작 시 한 번 등록 (rowsLoaded·nullRows는 오래 사는 필드의 AtomicLong)
Gauge.builder("dq_rows_loaded", rowsLoaded, AtomicLong::get).tag("table", "fct_orders").register(registry);
Gauge.builder("dq_null_ratio", this, s -> s.rowsLoaded.get() == 0 ? Double.NaN   // 0행이면 비율은 정의 안 됨
                                         : (double) s.nullRows.get() / s.rowsLoaded.get())
     .tag("table", "fct_orders").tag("column", "customer_id").register(registry);
```

- 위 코드는 Spring JDBC·Micrometer를 가정한 설명용 조각이고 이 노트에서 실행하지 않았다.
- Micrometer는 레지스트리에 이름·태그 조합마다 미터를 하나만 두고, 같은 조합으로 다시 등록하면 새 등록을 무시한다(문서: "the registration will be ignored"). 그래서 적재 때마다 람다로 새로 등록하면 첫 값에 고정된다. 값은 오래 사는 가변 상태(`AtomicLong`)에 두고 갱신한다(Micrometer "Gauges" 문서 — 관측 대상은 약한 참조라 강한 참조를 유지할 책임은 호출자에게 있다).
- 0행일 때 NULL 비율은 0/0이라 정의되지 않는다. `1.0`(전부 NULL)으로 두면 거짓 측정값이 된다. 여기서는 NaN으로 두고, 0행은 볼륨 지표와 차단 규칙이 맡는다.
- 핵심은 `throw` 줄이다. 차단 규칙 위반은 **잡을 실패로 만든다**. 그래야 오케스트레이터의 초록이 다시 의미를 갖는다.
- 지표 형·레이블 카디널리티 주의는 [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md). 테이블·컬럼 레이블은 수가 유한해야 한다.

## 장애 시나리오와 대처

### 1. 잡은 성공(초록)인데 0행 적재 (⚠ 커리큘럼)

- 현상: 대시보드에서 어제 날짜가 빠져 있다. 오케스트레이터는 초록.
- 보이는 형태: `INSERT 0 0`, `exit=0`(실험). 감사 테이블 행 수 0. 데이터 기준 신선도 지연 2일 이상.
- 원인: 상류 내보내기가 빈 파일을 만들었거나, 경로·파티션 이름이 바뀌어 아무것도 읽지 못했다. SQL은 0행을 오류로 보지 않는다.
- 대처: 즉시 — 상류 재추출 후 그 날짜 파티션만 다시 적재(덮어쓰기라 재실행 안전). 재발 방지 — 0행·볼륨 급감을 차단 규칙으로, 신선도는 이벤트 시각 기준으로.

### 2. 신선도 지연을 모른다 → 어제 데이터로 결정 (⚠ 커리큘럼)

- 현상: 오전 회의에서 "어제 매출"이라고 본 숫자가 실은 그제 숫자였다.
- 보이는 형태: 대시보드는 "최근 업데이트: 방금"을 표시한다. 잡이 돈 시각이기 때문이다.
- 원인: 신선도를 잡 실행 시각으로 쟀다. 실험에서 잡 기준은 `t`, 데이터 기준은 `STALE`이었다.
- 대처: 대시보드에 `max(event_time)`을 표시하고, 계약 SLA(예: 매일 09:00까지 전날 분)를 넘으면 경보.

### 3. NULL 비율 급변, 합계는 멀쩡 (⚠ 커리큘럼)

- 현상: 매출 합계는 그대로인데, 고객 세그먼트별 매출에서 "알 수 없음"이 커진다.
- 보이는 형태: 실험에서 주문 수·매출은 세 날 모두 400건·559,400인데, customer_id NULL 비율이 0% → 40%.
- 원인: 상류 필드 이름 변경(09번), 조인 키 형식 변경, 수집 SDK 버그 등 — 실험이 원인까지 보인 것은 아니다.
- 대처: 컬럼별 NULL 비율을 분포 지표로 쌓고 같은 요일 기준선과 비교. 계보(11번)로 그 컬럼의 상류를 거슬러 원인을 찾는다.

### 4. 검사가 너무 엄격 → 매일 경고 → 무시 (⚠ 커리큘럼)

- 현상: 데이터 품질 채널에 하루 수십 건의 경고가 쌓이고 아무도 보지 않는다. 그러다 진짜 0행이 묻힌다.
- 보이는 형태: 실험의 "전일 대비 ±5%" 규칙 — 정상 39일 중 21일 경보.
- 원인: 계절성(요일)과 성장을 모르는 고정 임계.
- 대처: 요일별 기준선 + 상대 하한(실험: 오경보 21 → 2), 경고와 차단 분리, 경보마다 소유자. 일정 기간 아무도 대응하지 않은 경고 규칙은 고치거나 지운다.

### 5. 이상값이 기준선을 오염시킨다

- 현상: 0행 사고가 한 번 난 뒤, 며칠 동안 반토막 적재가 경보 없이 지나간다.
- 보이는 형태: 실험의 "이상값도 학습" 판 — 0을 배운 뒤 밴드가 ±6,377 → ±13,813으로 넓어졌고, 55일에도 ±8,050으로 넓어 반토막(3,842행)을 놓쳤다.
- 원인: 이상으로 판정한 값까지 평균·분산 갱신에 넣었다.
- 대처: 이상 판정 값은 기준선에서 빼고, 사고로 확인된 날짜는 수동으로 제외 표시한다.

## 핵심 문장

- 잡의 성공은 SQL이 오류 없이 끝났다는 뜻이다. 0행을 넣어도 종료 코드는 0이다.
- 관측 5축은 신선도·볼륨·스키마·분포·계보다. 신선도는 잡 실행 시각이 아니라 데이터 안의 시각(SLA에 따라 최신 이벤트 시각 또는 적재 시각)으로 잰다.
- 품질 검사는 "규칙을 어기는 행을 고르는 쿼리"이고, 0행이면 통과다. 합계를 틀리게 만드는 위반은 차단, 해석이 필요한 변화는 경고로 둔다.
- 합계가 멀쩡해도 분포는 틀릴 수 있다. 컬럼별 NULL 비율을 따로 잰다.
- 볼륨 기준선은 계절성을 나누고, 이상으로 판정한 값은 기준선에 섞지 않는다. 고정 임계는 알람 피로를 만든다.

## 관련 주제·근거

- 선행
  - [09-data-contracts-and-schema-registry](../09-data-contracts-and-schema-registry/2-summary.md) — 계약의 품질·SLA 칸
  - data-analysis/18-data-cleaning-and-quality — 분석 쪽 품질 검사(미작성 — [data-analysis 영역 표](../../data-analysis/README.md))
  - [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md) — 지표 형, 카디널리티
- 후속·연결
  - [11-data-lineage](../11-data-lineage/2-summary.md) — 관측 5축의 계보, 원인 추적과 영향 범위
  - [08-idempotent-pipelines-and-backfill](../08-idempotent-pipelines-and-backfill/2-summary.md) — 문제 날짜만 다시 적재
  - [reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md) — 신선도를 SLI로, [reliability/33-hysteresis-and-flapping](../../reliability/33-hysteresis-and-flapping/2-summary.md) — 경보 깜빡임
  - [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md) — 분포 스케치
- 근거
  - Barr Moses, "What is Data Observability? 5 Pillars …" — 현재판(2026-09-25 갱신, Freshness·Quality·Volume·Schema·Lineage) <https://www.montecarlodata.com/blog-what-is-data-observability/> · Internet Archive 2022-04-25 사본(Freshness·Distribution·Volume·Schema·Lineage) <https://web.archive.org/web/20220425214127/https://www.montecarlodata.com/blog-what-is-data-observability/>
  - dbt "Add data tests to your DAG" — 실패 행 select, generic 4종, singular <https://docs.getdbt.com/docs/build/data-tests> · dbt-adapters `generic_test_sql/{unique,relationships,accepted_values}.sql`(NULL 처리) <https://github.com/dbt-labs/dbt-adapters/tree/main/dbt-adapters/src/dbt/include/global_project/macros/generic_test_sql> · dbt `build`(테스트 실패 시 하류 SKIP) <https://docs.getdbt.com/reference/commands/build> · dbt freshness(`loaded_at_field`) <https://docs.getdbt.com/reference/resource-configs/freshness>
  - Micrometer "Gauges" — 약한 참조, NaN·사라짐 <https://docs.micrometer.io/micrometer/reference/concepts/gauges.html> · "severity, error_if, and warn_if" — 기본 `error`·`!=0`, `--warn-error` <https://docs.getdbt.com/reference/resource-configs/severity>
  - Great Expectations GX Core 1.23.2 "GX Core overview"·"Define Expectations" — Expectation 정의 <https://docs.greatexpectations.io/docs/core/introduction/gx_overview/> · Expectation 갤러리(`ExpectColumnValuesToNotBeNull`) <https://greatexpectations.io/expectations/expect_column_values_to_not_be_null> · 0.18.21 용어집(메서드 이름 표기) <https://docs.greatexpectations.io/docs/reference/learn/terms/expectation>
  - Bitol ODCS v3.2.0 Data Quality — 라이브러리 지표 <https://bitol-io.github.io/open-data-contract-standard/latest/data-quality/>
  - OpenLineage Object Model — 입력 데이터셋의 `dataQualityMetrics`(행 수·NULL 수·고유값 수 등)·`dataQualityAssertions` facet <https://openlineage.io/docs/spec/object-model>
- 실험 목록
  - 0행 성공·볼륨·분포·dbt식 4검사·신선도(데이터 기준 vs 잡 기준) — postgres:17(PostgreSQL 17.11) 일회용 컨테이너, `--network none`, psql로 잡 4회 실행, 합성 주문 1,200건
  - 볼륨 감시 규칙 6종 비교(고정 임계·EWMA·요일별·하한) — `Volume.java`, eclipse-temurin:21-jdk(OpenJDK 21.0.12), 합성 70일, 시드 42
