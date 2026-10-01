# database/12-query-optimizer-and-explain — 비용 기반 옵티마이저와 EXPLAIN 읽기 — 정리 (힌트)

## 해결하는 문제

SQL은 **무엇을** 원하는지만 적는다. **어떻게** 가져올지는 적지 않는다.\
같은 결과를 내는 실행 방법은 수십~수천 가지다. 그중 빠른 것과 느린 것의 차이는 몇 배가 아니라 몇 자릿수까지 벌어진다.

쉬운 예: 내비게이션 앱이다.

- 목적지는 사용자가 정한다(SQL).
- 경로는 앱이 고른다(옵티마이저).
- 앱은 "지금 이 도로가 얼마나 막히나"라는 **추정**으로 경로를 고른다(통계).
- 추정이 틀리면(사고 정보가 늦게 반영되면) 막힌 길로 안내한다.

똑같은 구조다.\
옵티마이저는 통계로 "이 단계에서 행이 몇 개 나올까"를 추정하고, 그 추정으로 비용을 매겨 가장 싼 계획을 고른다.\
그래서 **추정이 틀리면 계획이 틀린다.** 이 노트의 장애는 거의 전부 이 한 문장에서 나온다.

실무 예:

- 야간 배치가 한 테이블에 10만 행을 넣었다. 다음 날 아침부터 어떤 조회가 느려졌다. 쿼리도 인덱스도 안 바뀌었다.
- `EXPLAIN ANALYZE`를 보니 `rows=6`(추정)인데 `actual rows=100010`(실제)이다. 옵티마이저가 "6행뿐"이라 믿고 중첩 루프를 골랐다.

## 동작·원리

### 1. SQL이 계획이 되기까지 (PostgreSQL 17 기준)

```text
  SQL 문자열
     │  파서: 문법 → 파스 트리
     ▼
  재작성기: 뷰 펼치기, 규칙 적용
     │
     ▼
  플래너/옵티마이저 ◄──── 통계 (pg_class.reltuples·relpages, pg_statistic)
     │   1) 테이블마다 스캔 경로 후보 (Seq Scan + 인덱스 종류·조건에 따라 Index·Bitmap 스캔)
     │   2) 조인 순서 × 조인 방법(NL·Hash·Merge) 후보
     │   3) 후보마다 비용 계산 → 가장 싼 것
     ▼
  계획 트리 ──► 실행기 (54번: 반복자 모델)
```

- *경로(path)*: 계획의 요약본이다. 플래너는 비교에 필요한 정보만 담은 경로로 탐색하고, 이긴 경로만 완전한 계획 트리로 만든다(PostgreSQL 50.5).
- *옵티마이저*: 여기서는 "비용이 가장 낮다고 **추정되는** 계획을 고르는 부분"이다. 진짜 최적을 보장하지 않는다.

### 2. 비용 — 추상 단위로 매긴 점수

```text
  Seq Scan 비용 = (읽을 페이지 수 × seq_page_cost) + (훑을 행 수 × cpu_tuple_cost)

  예시 (로컬 재현, PostgreSQL 17.11): ev 테이블 500,000행, 4,673페이지
      4,673 × 1.0 + 500,000 × 0.01 = 4,673 + 5,000 = 9,673
      EXPLAIN 출력:  Seq Scan on ev  (cost=0.00..9673.00 rows=500000 width=45)
```

| 파라미터 (PostgreSQL 17 기본값) | 뜻 |
|---|---|
| `seq_page_cost` = 1.0 | 순차로 읽는 페이지 하나 |
| `random_page_cost` = 4.0 | 임의 위치 페이지 하나 |
| `cpu_tuple_cost` = 0.01 | 행 하나 처리 |
| `cpu_index_tuple_cost` = 0.005 | 인덱스 항목 하나 처리 |
| `cpu_operator_cost` = 0.0025 | 연산자·함수 호출 하나 |

- 단위는 시간(ms)이 아니다. "순차 페이지 하나 = 1"로 잡은 상대 점수다(PostgreSQL 14.1).
- `cost=A..B`에서 A는 *시작 비용*(첫 행을 내기까지), B는 *총 비용*(마지막 행까지)이다.
- `random_page_cost`가 4인 이유를 문서는 이렇게 적는다. 실제 저장장치의 임의 접근은 4배보다 훨씬 비싸지만, 인덱스 읽기 대부분이 캐시에 있다고 가정해 낮췄다(19.7.2).

### 3. 카디널리티 추정 — 비용의 입력

비용 식에 들어가는 "행 수"는 **추정치**다. 이것을 *카디널리티 추정*이라 한다.

```text
  통계 (ANALYZE가 표본으로 만든다)
  ┌────────────────────────────────────────────────────────┐
  │ pg_class   : reltuples(행 수), relpages(페이지 수)        │
  │ pg_stats   : null_frac          NULL 비율                │
  │              n_distinct         서로 다른 값 수(음수=비율)  │
  │              most_common_vals   자주 나오는 값 (MCV)       │
  │              most_common_freqs  그 값들의 빈도             │
  │              histogram_bounds   나머지 값의 등빈도 경계      │
  └────────────────────────────────────────────────────────┘

  WHERE status = 'new'
     'new'가 MCV에 있으면        → 선택도 = 그 빈도
     없으면                      → (1 − MCV 빈도 합 − null_frac) / (나머지 서로 다른 값 수)
  추정 행 수 = reltuples × 선택도
```

- *선택도(selectivity)*: 조건을 통과하는 행의 비율이다. 0.01이면 1%.
- *n_distinct*: 양수면 서로 다른 값의 추정 개수다. 음수면 −(서로 다른 값 수 ÷ 행 수)다. `-1`은 모든 행이 다른 값(유니크)이라는 뜻이다(PostgreSQL 17 `pg_stats`).
- *MCV*: most common values. 흔한 값과 그 빈도를 따로 적어 둔 목록이다.
- *히스토그램*: MCV를 뺀 나머지 값을 "각 칸에 행이 거의 같은 수만큼" 들어가도록 자른 경계값이다(`pg_stats.histogram_bounds`, 등빈도). 범위 조건(`<`, `BETWEEN`)의 선택도를 여기서 읽는다.
- ANALYZE 표본 크기는 `300 × 통계 목표`행이다(`analyze.c`의 `minrows = 300 * attstattarget`). `default_statistics_target` 기본값이 100이므로 기본 표본은 30,000행이다.
- 표본은 2단계로 뽑는다. 먼저 블록을 무작위로 고르고, 그 안에서 Vitter 알고리즘(저수지 표본 추출)으로 행을 고른다(`analyze.c` 주석).

**가정 세 개** (CMU 15-445 L15):

```text
  1) 균등 분포     : MCV 밖의 값들은 고르게 퍼져 있다
  2) 조건 독립     : WHERE a = 1 AND b = 2 의 선택도 = sel(a) × sel(b)
  3) 포함 원리     : 조인 키는 한쪽 값이 다른 쪽에도 있다
```

이 가정이 깨지는 곳에서 추정이 틀린다. 가장 흔한 것이 **2) 독립 가정**이다.

```text
  로컬 재현 (예시, PostgreSQL 17.11): orders 20만 행
  city가 정해지면 country가 정해진다(함수 종속: c10~c19 → k1)
  city = 'c11'  은 전체의 0.5% (1,000행)
  country = 'k1' 은 전체의 5%   (10,000행)

  WHERE city='c11' AND country='k1'
    독립 가정: 0.005 × 0.05 = 0.025%  → 20만 × 0.00025 = 50 근처, 출력 rows=58   실제 1000
    실제 선택도: country 조건은 아무것도 더 거르지 않는다 → 0.5%
    CREATE STATISTICS (dependencies) ON city, country 후 ANALYZE
                                     → 추정 rows ≈ 1060    실제 1000
```

- *확장 통계(extended statistics)*: `CREATE STATISTICS`로 여러 컬럼의 관계(함수 종속, 조합별 서로 다른 값 수, 조합 MCV)를 따로 모은다. 플래너는 보통 조건이 독립이라고 가정하지만, 이 통계가 있으면 상관을 반영한다(PostgreSQL 14.2.2).

### 4. 조인 순서 — 부분집합 동적 계획법

테이블이 n개면 조인 순서의 수가 폭발한다. System R(1979) 이후 대부분의 오픈소스 DB는 **아래에서 위로 쌓는 동적 계획법**을 쓴다(CMU L15: System R, DB2, MySQL, Postgres).

```text
  FROM A, B, C

  크기 1:  {A} 최선 경로   {B} 최선 경로   {C} 최선 경로
            │               │              │
  크기 2:  {A,B} = min( A⋈B, B⋈A ) × (NL, Hash, Merge)
           {A,C}, {B,C} ...           ← 조인 조건이 있는 쌍을 먼저
            │
  크기 3:  {A,B,C} = min( {A,B}⋈C, {A,C}⋈B, {B,C}⋈A, ... )

  각 부분집합마다 "가장 싼 계획"만 남긴다 → 재계산 없음
  (정렬 순서처럼 위에서 쓸모 있는 성질이 다르면 따로 남긴다)
```

- PostgreSQL은 FROM 항목이 `geqo_threshold`(기본 12)개 미만이면 거의 완전 탐색을 한다. `geqo`(기본 on)가 켜져 있고 12개 이상이면 유전 알고리즘(GEQO)으로 넘어가 최적을 보장하지 않는다(50.5.1, 19.7.3).
- `join_collapse_limit`·`from_collapse_limit`(기본 8)은 명시적 `JOIN`·서브쿼리를 하나의 탐색 공간으로 합칠 최대 크기다. 1로 두면 쓴 순서대로 조인한다(19.7.4).
- 조인 방법 자체(NL·해시·병합)는 11번에서 다룬다.

### 5. EXPLAIN 읽기 — 추정과 실제를 나란히

```text
  EXPLAIN (ANALYZE, BUFFERS) ...     ← ANALYZE는 실제로 실행한다

  Aggregate  (cost=35.04..35.05 rows=1) (actual time=152.411..152.412 rows=1 loops=1)
    ->  Nested Loop  (cost=0.71..35.03 rows=6) (actual ... rows=100010 loops=1)
          ->  Index Scan using o2_status_idx on o2  (... rows=6) (actual ... rows=100010 loops=1)
          ->  Index Only Scan using cust_pkey on cust c  (... rows=1) (actual ... rows=1 loops=100010)
                    ▲                                                          ▲
              추정: 6행이면 6번만 인덱스를 찌르면 된다               실제: 100,010번 찔렀다
```

읽는 순서:

1. **안쪽(아래)에서 바깥(위)으로** 읽는다. 자식이 만든 행을 부모가 받는다.
2. 노드마다 `rows=`(추정)와 `actual rows=`(실제)를 비교한다.
3. **어긋남이 처음 시작되는 가장 아래 노드**를 찾는다. 위쪽 노드의 어긋남은 대개 그 결과다.
4. `loops`가 1보다 크면 `actual rows`·`actual time`은 **한 번 실행당 평균**이다. 총량은 곱해서 본다(PostgreSQL 14.1).

- `EXPLAIN`만 쓰면 추정만 나온다. `ANALYZE`를 붙이면 실제로 실행하므로, `UPDATE`·`DELETE`는 `BEGIN … ROLLBACK` 안에서 본다.
- 해시 노드의 `Buckets: 131072 (originally 2048)`처럼 "원래(originally)"가 붙으면 실행 중에 추정이 틀렸음을 알고 늘린 것이다(로컬 재현).

MySQL 8.4 InnoDB에서는:

```text
  EXPLAIN FORMAT=TREE SELECT ...     추정만
  EXPLAIN ANALYZE SELECT ...         실제 실행 + 반복자별 (actual time=첫행..끝 rows=… loops=…)

  로컬 재현 (예시, MySQL 8.4.10): o2 10만 행, status='new'는 100행, 인덱스 없음
  히스토그램 없음:  Filter: (o2.status = 'new')  (rows=10041) (actual ... rows=100)
                   전통 EXPLAIN의 filtered = 10.00  ← 통계가 없어 고정 추정
  ANALYZE TABLE o2 UPDATE HISTOGRAM ON status WITH 16 BUCKETS 후:
                   Filter: (o2.status = 'new')  (rows=100)   (actual ... rows=100)
                   filtered = 0.10
```

- MySQL의 히스토그램은 두 종류다. 서로 다른 값이 버킷 수 이하면 *singleton*(값마다 한 칸), 넘으면 *equi-height*(칸마다 행 수가 비슷)다(MySQL 8.4 10.9.6).

### 6. 통계는 언제 새로 만드나

```text
  PostgreSQL 17 (autovacuum)
    변경 행 수 > autovacuum_analyze_threshold(50) + autovacuum_analyze_scale_factor(0.1) × reltuples
    → 자동 ANALYZE
    예: 100만 행 테이블 → 약 10만 행 바뀌어야 자동 ANALYZE

  MySQL 8.4 InnoDB (영구 통계)
    innodb_stats_auto_recalc = ON (기본) → 행의 10% 넘게 바뀌면 백그라운드 재계산 (몇 초 늦을 수 있음)
    innodb_stats_persistent_sample_pages = 20 (기본) → 인덱스 통계 표본 페이지 수
    히스토그램: 기본 MANUAL UPDATE → 사람이 ANALYZE TABLE … UPDATE HISTOGRAM 해야 바뀜
               AUTO UPDATE로 만들면 ANALYZE TABLE·자동 재계산 때 같이 갱신 (MySQL 8.4 문서)
```

- 핵심: 두 제품 모두 **비율 기준**이다. 큰 테이블일수록 "많이 바뀌어도 아직 재분석 전"인 구간이 길다.
- PostgreSQL은 `reltuples`가 오래됐어도 현재 페이지 수로 행 수를 비례 보정한다(14.2.1). 그래서 행 **개수**는 어느 정도 따라가지만, 값의 **분포**(MCV 빈도)는 ANALYZE 전까지 옛날 그대로다.

## 쓰이는 자료구조·알고리즘

- **부분집합 동적 계획법** — 테이블 집합을 비트마스크로 보고, 작은 부분집합의 최선 계획으로 큰 부분집합을 만든다. System R의 left-deep 탐색이 원형이다. [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md), [algorithm/22-dp-advanced](../../algorithm/22-dp-advanced/2-summary.md)
- **유전 알고리즘(GEQO)** — 테이블이 너무 많으면 완전 탐색을 포기하고 휴리스틱으로 탐색한다(PostgreSQL 60장).
- **히스토그램** — PostgreSQL은 등빈도 경계(`histogram_bounds`), MySQL은 singleton·equi-height 두 종류.
- **MCV 목록** — 자주 나오는 값과 빈도의 짧은 목록. 쏠린 분포(skew)를 잡는다.
- **저수지 표본 추출(Vitter)** — 전체 크기를 몰라도 한 번 훑으며 균등 표본을 뽑는다(`analyze.c`).
- **계획 트리** — 연산자 노드의 트리. 실행은 54번의 반복자 모델로 한다.

## 적용 — 풀어나가는 법

### 1. 느린 쿼리를 받았을 때의 순서

```sql
-- ① 실제 계획과 버퍼 (PostgreSQL)
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;

-- ② 어긋난 노드의 테이블 통계가 언제 만들어졌나
SELECT relname, n_mod_since_analyze, last_analyze, last_autoanalyze
FROM pg_stat_user_tables WHERE relname = 'o2';

-- ③ 그 컬럼의 통계
SELECT null_frac, n_distinct, most_common_vals, most_common_freqs
FROM pg_stats WHERE tablename = 'o2' AND attname = 'status';

-- ④ 통계 갱신 후 다시 ①
ANALYZE o2;
```

- ①에서 "추정 vs 실제"가 10배 이상 벌어진 가장 아래 노드를 찾는다.
- ②의 `n_mod_since_analyze`는 마지막 ANALYZE 뒤 바뀐 행 수다. 테이블 크기에 비해 크면 통계가 낡았다.
- ④로 고쳐지면 원인은 통계 신선도다. 그러면 배치 끝에 `ANALYZE`를 넣는다.

### 2. 통계로 안 고쳐질 때

```sql
-- 상관된 컬럼: 확장 통계
CREATE STATISTICS o_city_country (dependencies) ON city, country FROM orders;
ANALYZE orders;

-- 분포가 심하게 쏠린 컬럼: 그 컬럼만 표본을 늘린다
ALTER TABLE orders ALTER COLUMN status SET STATISTICS 1000;
ANALYZE orders;
```

- 그래도 안 되면 쿼리 모양을 바꾼다. 예: 함수를 씌운 조건(`WHERE date(created_at) = …`)은 통계를 쓰기 어렵다. 범위 조건으로 바꾼다.
- PostgreSQL 코어에는 옵티마이저 힌트 문법이 없다. `enable_nestloop = off` 같은 `enable_*` 설정은 **진단용**으로 세션에서만 쓴다. 예를 들어 `enable_nestloop = off`도 중첩 루프를 완전히 막지 못하고, 다른 방법이 있을 때 덜 고르게 할 뿐이다(19.7.1).

### 3. MySQL 8.4

```sql
EXPLAIN ANALYZE SELECT ...;                                      -- 반복자별 실제 행
ANALYZE TABLE o2;                                                -- 인덱스 통계 재계산
ANALYZE TABLE o2 UPDATE HISTOGRAM ON status WITH 32 BUCKETS;     -- 인덱스 없는 컬럼 분포
SET optimizer_trace = 'enabled=on'; SELECT ...;
SELECT trace FROM information_schema.OPTIMIZER_TRACE;            -- 후보 계획과 비용
```

- 히스토그램은 주로 인덱스가 없는 컬럼용이다. 범위 옵티마이저 추정을 쓸 수 있으면 히스토그램보다 그것을 우선한다. 인덱스가 있는 컬럼의 등호 조건은 *인덱스 다이브*(인덱스를 실제로 내려가 보는 추정)가 더 나은 값을 줄 수 있다(10.9.6).

### 4. 준비된 문장(prepared statement)의 함정 — PostgreSQL

- 드라이버가 서버 측 준비된 문장을 쓰면, PostgreSQL은 처음 5번은 파라미터 값을 넣은 *맞춤 계획*을 만든다. 그다음 *일반 계획*(값 무관)을 만들어 평균 비용과 비교하고, 크게 나쁘지 않으면 이후 일반 계획을 쓴다(PREPARE 문서).
- 값에 따라 최적 계획이 크게 다르면(흔한 값 vs 드문 값) 일반 계획이 한쪽에 나쁠 수 있다. `plan_cache_mode = force_custom_plan`으로 세션·역할 단위로 끌 수 있다.

### 5. 계획 변화를 감시한다

```sql
-- postgresql.conf: shared_preload_libraries = 'pg_stat_statements'
SELECT queryid, calls, mean_exec_time, rows FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 20;

-- 느린 쿼리의 실제 계획을 로그로: auto_explain
-- auto_explain.log_min_duration = '3s', auto_explain.log_analyze = on
```

- 같은 `queryid`의 `mean_exec_time`이 어느 날 갑자기 뛰면 계획 변화를 의심한다. `auto_explain`이 그때의 계획을 남긴다(F.3).

## 장애 시나리오와 대처

### 1. 야간 배치 뒤 아침부터 조회가 느려진다 (⚠ 통계 오래됨 → 플랜 급변)

- **현상**: 배치가 한 테이블에 대량으로 넣은 다음, 그 테이블을 조인하는 조회가 느려진다. 코드 변경은 없다.
- **보이는 형태** (로컬 재현, PostgreSQL 17.11, 병렬 끔)

```text
  배치 전 (status='new' 10행):
    Nested Loop (rows=3) (actual rows=10)                      0.09 ms
  배치 (새 'new' 10만 행 INSERT, ANALYZE 안 함):
    Nested Loop (rows=6) (actual rows=100010)                  152 ms
      -> Index Only Scan on cust ... (actual rows=1 loops=100010)
  ANALYZE 뒤:
    Hash Join (rows=100147) (actual rows=100010)               82 ms
```

  - 이 재현은 데이터가 전부 메모리에 있어 차이가 2배 정도였다. 디스크에서 임의 읽기를 해야 하면 중첩 루프의 반복 인덱스 탐색이 훨씬 비싸진다.
- **원인**: 배치가 바꾼 비율이 자동 ANALYZE 문턱(기본 50 + 10%)을 넘지 않았거나, 넘었어도 autovacuum이 아직 돌지 않았다. 옵티마이저는 옛 MCV 빈도를 믿고 "몇 행 안 된다"고 추정해 중첩 루프를 골랐다.
- **대처**
  - 긴급: `ANALYZE <테이블>`.
  - 근본: 대량 적재 배치의 마지막 단계에 `ANALYZE`를 넣는다. 자주 크게 바뀌는 테이블은 `ALTER TABLE … SET (autovacuum_analyze_scale_factor = 0.01)`처럼 테이블 단위로 문턱을 낮춘다.

### 2. 조건 두 개를 걸었더니 추정이 10분의 1 이하로 떨어진다 (⚠ 추정 vs 실제 행 수 괴리)

- **현상**: `WHERE city = … AND country = …`가 들어간 조인이 느리다.
- **보이는 형태**: 스캔 노드에서 `rows=58`, `actual rows=1000`(로컬 재현). 그 위의 조인이 중첩 루프로 잡힌다.
- **원인**: 독립 가정. 두 컬럼이 함수 종속이라 곱한 선택도가 실제보다 훨씬 작다.
- **대처**: PostgreSQL은 `CREATE STATISTICS … (dependencies)` 또는 `(ndistinct, mcv)` 후 ANALYZE. MySQL 8.4에는 `CREATE STATISTICS` 같은 다중 컬럼 통계 문법이 없다. 두 컬럼에 복합 인덱스가 있으면 범위 옵티마이저가 인덱스 다이브로 조합을 직접 추정할 수 있다(10.9.6의 인덱스 다이브 설명).

### 3. 같은 쿼리가 어떤 값에서만 느리다 — 준비된 문장의 일반 계획

- **현상**: 파라미터 `status = ?`가 드문 값일 때는 빠르다. 흔한 값일 때만, 그것도 **몇 번 실행된 뒤부터** 느리다.
  - psql의 `PREPARE`/`EXECUTE`라면 여섯 번째 실행쯤부터다.
  - pgJDBC는 같은 `PreparedStatement`를 `prepareThreshold`(기본 5)번째 실행할 때부터 서버 측 준비 문장을 만든다. 그래서 일반 계획 전환은 그보다 더 늦게 온다(pgJDBC 문서 "Server Prepared Statements").
- **보이는 형태**: `auto_explain` 로그의 계획에 상수 대신 `$1`이 보인다. 같은 SQL을 psql에서 상수로 돌리면 빠르다.
- **원인**: 5회 뒤 일반 계획으로 바뀌었다. 일반 계획은 값 분포를 평균으로 보고 만든다.
- **대처**: `plan_cache_mode = force_custom_plan`(역할·세션 단위). 또는 드라이버에서 서버 측 준비를 끈다. pgJDBC는 `prepareThreshold=0`이면 서버 측 준비 문장을 쓰지 않는다(pgJDBC 문서 "Server Prepared Statements" — Deactivation).

### 4. ANALYZE를 돌렸더니 오히려 느려졌다

- **현상**: 통계를 새로 만든 뒤 계획이 바뀌고 느려졌다.
- **보이는 형태**: `pg_stat_statements`에서 같은 `queryid`의 평균 시간이 ANALYZE 시각 이후 뛴다.
- **원인**: 표본(기본 30,000행)이 쏠린 값을 이번에는 못 잡았다. 또는 비용 상수(`random_page_cost`)가 실제 저장장치와 안 맞아, 정확한 행 수로도 잘못된 계획을 골랐다.
- **대처**: 그 컬럼의 `SET STATISTICS`를 올려 표본을 키운다. SSD에서는 `random_page_cost`를 낮추는 것을 검토한다(문서도 캐시·저장장치에 따라 조정하라고 한다). 바꾸기 전후 `EXPLAIN (ANALYZE, BUFFERS)`를 비교해 기록한다.

### 5. 테이블이 많은 조인에서 계획이 실행마다 달라진다

- **현상**: 조인 테이블이 12개 이상인 리포트 쿼리가 어떤 날은 빠르고 어떤 날은 느리다.
- **보이는 형태**: `EXPLAIN`의 조인 순서가 날마다 다르다. 테이블 수를 줄인 같은 쿼리는 안정적이다.
- **원인**: `geqo_threshold`(12)에 닿아 GEQO가 동작했다. 유전 탐색은 탐색 공간의 일부만 보므로 최적을 보장하지 않는다. 난수 시작값 `geqo_seed`는 기본 0으로 고정이라 입력이 같으면 같은 경로를 탐색한다. 하지만 통계가 조금만 바뀌어도 찾아내는 계획이 달라질 수 있다(19.7.3).
- **대처**: 쿼리를 나눈다(CTE를 `MATERIALIZED`로 고정하거나 중간 결과 테이블). 또는 조인 순서를 직접 쓰고 `join_collapse_limit = 1`로 그 순서를 강제한다.

## 핵심 문장

- 옵티마이저는 "가장 빠른 계획"이 아니라 "추정 비용이 가장 낮은 계획"을 고른다. 추정이 틀리면 계획이 틀린다.
- 추정은 통계(행 수·MCV·히스토그램)와 세 가정(균등·독립·포함)으로 만든다. 상관된 컬럼은 독립 가정을 깨서 과소추정을 낳는다.
- 조인 순서는 부분집합 동적 계획법으로 고른다(System R 계열). PostgreSQL은 `geqo`가 켜져 있고(기본) FROM 항목이 12개 이상이면 유전 탐색으로 넘어간다.
- `EXPLAIN ANALYZE`는 아래에서 위로, 추정과 실제가 처음 어긋나는 노드를 찾으며 읽는다. `loops`가 있으면 곱해서 본다.
- 통계 자동 갱신은 비율 기준(PostgreSQL 50행 + 10%, InnoDB 10%)이다. 대량 배치 뒤에는 직접 `ANALYZE`한다.

## 관련 주제·근거

- 선행
  - database `11-join-algorithms` — 조인 방법(NL·해시·병합)의 비용 → [../11-join-algorithms/2-summary.md](../11-join-algorithms/2-summary.md)
  - database `09-index-design` — 선택도와 인덱스 → [../09-index-design/2-summary.md](../09-index-design/2-summary.md)
- 연결
  - database `41-sorting-and-aggregation` — 정렬·집계 노드와 스필 → [../41-sorting-and-aggregation/2-summary.md](../41-sorting-and-aggregation/2-summary.md)
  - database `54-query-execution-models` — 계획 트리를 실제로 도는 반복자·병렬 실행 → [../54-query-execution-models/2-summary.md](../54-query-execution-models/2-summary.md)
  - 문법 쪽: [sql/58 EXPLAIN 계획 트리](../../../languages/sql/syntax/58-explain-plan-tree/2-summary.md) · [sql/59 스캔·조인·정렬 연산자](../../../languages/sql/syntax/59-scan-join-sort-operators/2-summary.md) · [sql/60 추정과 실측](../../../languages/sql/syntax/60-explain-analyze-estimates-vs-actuals/2-summary.md)
  - [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md) — 부분집합 DP
- 교재·논문
  - CMU 15-445/645 Fall 2024 Lecture #15 "Query Planning & Optimization" — System R, 선택도 가정 3개(균등·독립·포함), 히스토그램·표본, bottom-up vs top-down <https://15445.courses.cs.cmu.edu/fall2024/>
  - P. G. Selinger 외, "Access Path Selection in a Relational Database Management System", SIGMOD 1979 (CMU L15 경유, 원문 미열람)
- PostgreSQL 17 문서
  - 14.1 Using EXPLAIN(비용 식 `(pages × seq_page_cost) + (rows × cpu_tuple_cost)`, loops는 평균) <https://www.postgresql.org/docs/17/using-explain.html>
  - 14.2 Statistics Used by the Planner(reltuples·relpages 비례 보정, 확장 통계) <https://www.postgresql.org/docs/17/planner-stats.html> · 68.1 Row Estimation Examples <https://www.postgresql.org/docs/17/row-estimation-examples.html>
  - 50.5 Planner/Optimizer(경로, 조인 전략, geqo_threshold) <https://www.postgresql.org/docs/17/planner-optimizer.html>
  - 19.7 Query Planning(`*_cost` 기본값, `default_statistics_target` 100, `geqo_threshold` 12, `join_collapse_limit`·`from_collapse_limit` 8, `plan_cache_mode`) <https://www.postgresql.org/docs/17/runtime-config-query.html>
  - 19.10 Automatic Vacuuming(`autovacuum_analyze_threshold` 50, `autovacuum_analyze_scale_factor` 0.1) <https://www.postgresql.org/docs/17/runtime-config-autovacuum.html>
  - `pg_stats` 뷰(`histogram_bounds` 등빈도) <https://www.postgresql.org/docs/17/view-pg-stats.html> · CREATE STATISTICS <https://www.postgresql.org/docs/17/sql-createstatistics.html> · PREPARE(처음 5회 맞춤 계획) <https://www.postgresql.org/docs/17/sql-prepare.html> · F.3 auto_explain · F.30 pg_stat_statements
  - 소스 `src/backend/commands/analyze.c`(`minrows = 300 * attstattarget`, 2단계 표본·Vitter) <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/commands/analyze.c>
- pgJDBC 문서 "Server Prepared Statements"(`prepareThreshold` 기본 5, `0`이면 비활성) <https://jdbc.postgresql.org/documentation/server-prepare/>
- MySQL 8.4 Reference Manual
  - 15.8.2 EXPLAIN Statement(EXPLAIN ANALYZE는 반복자 기반, TREE 형식) <https://dev.mysql.com/doc/refman/8.4/en/explain.html>
  - 10.9.6 Optimizer Statistics(히스토그램 singleton·equi-height) <https://dev.mysql.com/doc/refman/8.4/en/optimizer-statistics.html> · 15.7.3.1 ANALYZE TABLE(`UPDATE HISTOGRAM`, 기본 100 버킷, `AUTO UPDATE`/`MANUAL UPDATE`) <https://dev.mysql.com/doc/refman/8.4/en/analyze-table.html>
  - 17.8.10.1 Configuring Persistent Optimizer Statistics(`innodb_stats_auto_recalc` 10%, `innodb_stats_persistent_sample_pages` 20) <https://dev.mysql.com/doc/refman/8.4/en/innodb-persistent-stats.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10, 전용 DB `w12`): 대량 INSERT 뒤 ANALYZE 전후 중첩 루프 → 해시 조인 전환, 상관 컬럼 추정 58 → 확장 통계 뒤 1060(실제 1000), Seq Scan 비용 9673 계산, MySQL 히스토그램 전후 `filtered` 10.00 → 0.10
