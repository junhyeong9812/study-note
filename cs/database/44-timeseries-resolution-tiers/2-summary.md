# database/44-timeseries-resolution-tiers — 시계열 해상도 계층: 롤업·다운샘플·보존 — 정리 (힌트)

## 해결하는 문제

측정값은 멈추지 않고 들어온다. 초당 1개짜리 지표 하나가 하루 86,400행이다.\
그대로 두면 두 가지가 동시에 망가진다.

```text
  ① 조회: "지난 6개월 CPU" 그래프  → 1초 원본 약 1,580만 행(182.5일 × 86,400)을 읽어 화면 1000픽셀에 그린다 (예시)
  ② 저장: 지우는 작업이 없으면    → 테이블·디스크가 선형으로 자란다 → 어느 날 디스크 풀
```

쉬운 예: 통장 거래 내역이다. 은행 앱은 최근 거래는 한 건씩 보여 주고, 몇 년 전은 "월별 합계"로만 보여 준다. 아주 오래된 건 지운다.\
똑같은 구조다. **최근은 촘촘히, 오래된 것은 굵게 접어서, 기한이 지나면 버린다.**

실무 예:
- 모니터링 지표(Prometheus·Graphite), IoT 센서, 요금 정산용 사용량, 서비스 대시보드.
- 개념(조회 창에 맞춘 계층, min·max·sum·count 저장, 감지 경로와 조회 경로 분리, ClickHouse 구현)은 원고 [systems/timeseries-resolution-tiers](../../systems/timeseries-resolution-tiers/2-summary.md)에 있다.
- 한 프로세스 안의 구현(버킷·접기·반열린 구간·lateDrops)은 [ops-patterns/17-timeseries](../../ops-patterns/17-timeseries/2-summary.md)에 있다.
- 이 노트는 **관계형 DB(PostgreSQL 17 / MySQL 8.4) 위에서** 롤업 테이블·보존을 만들 때의 SQL, 그리고 커리큘럼 ⚠인 **경계 이중 계산**과 **보존 누락 디스크 풀**을 채운다.

## 동작·원리

### 1. 계층 = 해상도 × 보존 기간

```text
  계층        해상도    보존 기간     지표 하나의 행 수 (예시)
  raw        1초       7일          7 × 86,400      = 604,800
  rollup_1m  1분       90일         90 × 1,440      = 129,600
  rollup_1h  1시간     2년          730 × 24        =  17,520
  ───────────────────────────────────────────────────────────────
  조회 창 ≤ 6시간 → raw,  ≤ 2주 → 1m,  그 이상 → 1h        (라우팅 규칙 예시)
```

- *해상도(resolution)*: 한 점(버킷)이 대표하는 시간 폭.
- *롤업(rollup)*: 가는 버킷 여럿을 굵은 버킷 하나로 요약해 저장하는 것. *다운샘플링*이라고도 한다.
- *보존 기간(retention)*: 그 계층의 행을 들고 있는 기간. 지나면 지운다.
- 오래된 구간일수록 굵은 계층만 남는다. 원본을 영원히 두지 않는 대신, 넓은 창 조회는 적은 행을 읽는다.

### 2. 버킷에 무엇을 담나 — 합칠 수 있는 값만

```text
  1분 버킷 하나: (bucket, metric, n, sum, min, max)
      60개 원본 ──접기──> n=60, sum=Σv, min, max
  1시간 버킷 = 1분 버킷 60개를 다시 접기:
      n = Σn,  sum = Σsum,  min = min(min),  max = max(max)     ← 다시 접어도 같은 값 (수학적으로)
      avg = Σsum / Σn                                           ← 다시 접어도 같은 값 (수학적으로)
      avg(avg)                                                  ← 틀림 (버킷 크기가 다르면)
      p50 = ?                                                   ← 못 구함 (원본이나 스케치 필요)
```

- "같은 값"은 수학적으로 그렇다는 뜻이다. `double precision` 합은 합산 순서에 따라 끝자리 반올림 오차가 날 수 있다. 정확한 합이 필요하면 `numeric`으로 담는다(PostgreSQL 17 8.1 수치형).
- 로컬 재현(예시, PostgreSQL 17.11): 샘플 10개(평균 100)와 1000개(평균 200) 버킷. 평균의 평균은 150, `sum/count`는 199.0099였다.
- 로컬 재현(예시): 90개가 1, 10개가 100인 데이터. 전체 중앙값은 1이고, 두 구간 중앙값의 평균은 50.5였다.
- 자세한 표(스케치·t-digest·HLL)는 원고 2-summary의 재집계 표와 3-answer 4번(rollup of rollup).

### 3. 버킷 경계 — 반열린 구간 [시작, 끝)

```text
  시각   00:59:59   01:00:00   01:00:01
          │          │
  [00:00, 01:00)  ───┘          ← 01:00:00은 여기 아님
  [01:00, 02:00)  ──────────────  01:00:00은 여기만

  BETWEEN 00:00 AND 01:00   → 양 끝 포함 → 01:00:00이 두 버킷에 들어간다
```

- *반열린 구간*: 시작은 포함, 끝은 제외. 이어 붙여도 겹치거나 빠지지 않는다.
- SQL `BETWEEN a AND b`는 **양 끝을 포함**한다. 시간 버킷에 쓰면 경계 시각의 행이 두 번 세어진다.
- 로컬 재현(예시): 3시간 × 초당 1행 = 10,800행. 시간별로 `ts BETWEEN h AND h + 1 hour`로 세자 3601, 3601, 3600, 합 **10,802**였다. 에러는 없었다.
- `date_bin('1 hour', ts, origin)`(PostgreSQL 14+)은 행마다 버킷 시작 하나를 돌려준다. 한 행이 한 버킷에만 들어간다. 로컬 재현에서 3600 × 3 = 10,800으로 맞았다.

### 4. 롤업 작업은 다시 돌 수 있어야 한다 — 덮어쓰기

```text
  롤업 잡이 두 번 돈다 (재시도·스케줄 겹침·백필)
  ├ append (INSERT만)          → 같은 버킷 행이 2개 → 합계 2배
  └ upsert (버킷 키 + 덮어쓰기)  → 몇 번 돌아도 같은 결과
```

- 로컬 재현(예시): 같은 롤업을 두 번 INSERT한 테이블은 n 합이 21,600(원본 10,800의 2배)이었다. `PRIMARY KEY (bucket, metric)` + `ON CONFLICT … DO UPDATE SET n = EXCLUDED.n …`로 두 번 돌린 테이블은 10,800이었다.
- *멱등(idempotent)*: 여러 번 해도 한 번 한 것과 같은 결과.
- `n = n + EXCLUDED.n`처럼 **더하는** upsert는 멱등이 아니다. 버킷 전체를 원본에서 다시 계산해 **덮어쓴다.**

### 5. 늦게 온 데이터 — 닫힌 버킷을 다시 연다

```text
  01:05  롤업 잡: [00:00, 01:00) 버킷 = 3600
  01:07  수집 지연된 행 도착: ts = 00:59:30
         원본 3601 ≠ 롤업 3600          ← 조용히 어긋남
  대처:  매 실행마다 "최근 N개 버킷"을 원본에서 다시 계산해 덮어쓴다
         (N × 버킷 폭 ≥ 허용 지연 + 잡 실행 간격)
```

- 잡 실행 간격을 더하는 이유: 1시간 버킷, 허용 지연 1시간, 매시 05분 실행에서 N = 1이면 01:59에 도착한 00:59:30 행을 놓친다. 01:05 잡은 도착 전이고, 02:05 잡은 [01:00, 02:00)만 다시 계산한다. N = 2면 02:05 잡이 00:00 버킷까지 덮는다.
- 로컬 재현(예시): 롤업 뒤 00:59:30 행을 넣자 00:00 버킷이 롤업 3600, 원본 3601로 어긋났다. 최근 버킷 재계산 upsert 뒤 불일치는 0이었다.
- 원본 보존 기간은 "허용 지연 + 재계산 창"보다 길어야 한다. 원본이 먼저 지워지면 재계산할 재료가 없다.

### 6. 보존 = 지우기. DELETE보다 파티션 DROP

```text
  raw_p (PARTITION BY RANGE (ts), 하루 단위)
  ┌──────────┬──────────┬──────────┬──────────┐
  │ 09-29    │ 09-30    │ 10-01    │ 10-02    │ ← 미리 만들어 둔다
  └──────────┴──────────┴──────────┴──────────┘
     DROP        DELETE WHERE ts < …
     파일째 삭제   행마다 dead tuple → VACUUM 대상, 공간은 테이블 안에 남음
```

- 로컬 재현(예시, PostgreSQL 17.11): 하루치 파티션 `DETACH` 3.4ms + `DROP` 4.0ms. 같은 테이블에서 `DELETE` 21,600행 뒤 그 파티션은 `n_dead_tup = 21600`, 크기 2208 kB 그대로였다.
- 표준 VACUUM은 dead tuple 자리를 재사용 가능하게 표시할 뿐, 테이블 끝의 빈 페이지 외에는 **OS에 공간을 돌려주지 않는다**(PostgreSQL 17 24.1 Routine Vacuuming).
- **다음 파티션을 미리 만들지 않으면 쓰기가 실패한다.**
  - PostgreSQL 17: `ERROR: no partition of relation "raw_p" found for row`(로컬 재현).
  - MySQL 8.4: `ERROR 1526 (HY000): Table has no partition for value from column_list`(로컬 재현).
- *링 버퍼*와 같은 모양이다. 고정 개수의 칸을 돌려 쓰며, 새 칸을 열 때 가장 오래된 칸을 버린다. RRDtool은 이것을 파일 하나의 round robin archive(RRA)로 한다(rrdcreate 문서).

## 쓰이는 자료구조·알고리즘

- **링 버퍼** — 보존 기간 = 칸 수 × 칸 폭. 파티션 회전(새 파티션 생성 + 가장 오래된 DROP)이 DB판 링 버퍼다.
- **롤업(합칠 수 있는 요약)** — (n, sum, min, max)는 결합법칙이 성립해 몇 단계로 접어도 (수학적으로) 같은 값이다. 부동소수점 합은 끝자리 오차가 날 수 있다. 분위수·고유 개수는 원본이나 머지 가능한 스케치가 필요하다. [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md), [data-structure/13-segment-tree](../../data-structure/13-segment-tree/2-summary.md)
- **버킷 정렬(floor 나눗셈)** — `bucket = origin + floor((ts − origin) / 폭) × 폭`. `date_bin`이 이것이다.
- **B+트리** — 아래 예시 DDL의 PK는 `(bucket, metric)`이다. 버킷·지표마다 행 하나를 지키는 키(upsert 대상)다. "metric 등호 + bucket 범위" 조회가 주라면 선두 열이 metric인 `(metric, bucket)` 인덱스를 따로 두거나 PK 순서를 바꾼다(PostgreSQL 17 11.3 다중 열 인덱스). [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- **범위 파티셔닝** — 시간 범위로 나누면 보존이 파티션 단위 DROP이 되고, 조회는 파티션 프루닝을 받는다.

## 적용 — 풀어나가는 법

### 1. 먼저 적는다: 무엇을 물을 것인가

- 평균·최대만이면 (n, sum, min, max). p95가 필요하면 원본 보존을 늘리거나 히스토그램 버킷을 저장한다.
- 계층·보존·허용 지연을 표로 정한다. 접은 원본은 되돌릴 수 없다.

### 2. PostgreSQL 17 — 롤업 테이블과 멱등 롤업

```sql
CREATE TABLE m_1h (
  bucket timestamptz NOT NULL, metric text NOT NULL,
  n bigint, s double precision, mn double precision, mx double precision,
  PRIMARY KEY (bucket, metric));

-- 최근 3시간 버킷을 원본에서 다시 계산해 덮어쓴다 (늦은 데이터 흡수)
INSERT INTO m_1h
SELECT date_bin('1 hour', ts, '2026-01-01+00'), metric, count(*), sum(v), min(v), max(v)
  FROM m_raw
 WHERE ts >= date_bin('1 hour', now(), '2026-01-01+00') - interval '3 hours'
   AND ts <  date_bin('1 hour', now(), '2026-01-01+00')          -- 진행 중인 버킷은 제외
 GROUP BY 1, 2
ON CONFLICT (bucket, metric) DO UPDATE
   SET n = EXCLUDED.n, s = EXCLUDED.s, mn = EXCLUDED.mn, mx = EXCLUDED.mx;

-- 조회: 평균은 sum/count
SELECT bucket, s / n AS avg_v, mx FROM m_1h WHERE metric = 'cpu' AND bucket >= now() - interval '30 days';
```

- 일 단위 버킷은 **시간대**를 정한다. `date_bin('1 day', …)`의 origin이 UTC 자정이면 KST 기준 일별 집계와 9시간 어긋난다. [27-temporal-types-and-session-timezone](../27-temporal-types-and-session-timezone/2-summary.md).

### 3. MySQL 8.4 — 같은 구조

```sql
CREATE TABLE raw_p (ts DATETIME NOT NULL, metric VARCHAR(20) NOT NULL, v DOUBLE NOT NULL)
PARTITION BY RANGE COLUMNS(ts) (
  PARTITION p20260930 VALUES LESS THAN ('2026-10-01'),
  PARTITION p20261001 VALUES LESS THAN ('2026-10-02'));

INSERT INTO m_1h
SELECT * FROM (SELECT DATE_FORMAT(ts, '%Y-%m-%d %H:00:00') b, metric,
                      COUNT(*) n, SUM(v) s, MIN(v) mn, MAX(v) mx
                 FROM raw_p GROUP BY b, metric) AS x
ON DUPLICATE KEY UPDATE n = x.n, s = x.s, mn = x.mn, mx = x.mx;   -- 두 번 돌려도 같은 결과 (로컬 재현)

ALTER TABLE raw_p DROP PARTITION p20260930;                       -- 보존
```

### 4. 보존 작업과 감시

```sql
-- PostgreSQL: 파티션별 크기·dead tuple
SELECT relname, n_live_tup, n_dead_tup, pg_size_pretty(pg_total_relation_size(relid))
  FROM pg_stat_user_tables WHERE relname LIKE 'raw_p%' ORDER BY relname;
-- 가장 오래된 행이 보존 기간을 넘었나 (보존 잡이 안 도는지)
SELECT now() - min(ts) AS oldest_age FROM raw_p;
-- 롤업 정합성: 원본과 롤업 건수 비교 (최근 창, 진행 중인 버킷 제외)
-- (bucket, metric) 둘 다로 맞추고, LEFT JOIN이라 롤업이 통째로 빠진 버킷도 잡는다
SELECT x.b, x.metric, x.n AS raw_n, r.n AS rollup_n
  FROM (SELECT date_bin('1 hour', ts, '2026-01-01+00') b, metric, count(*) n
          FROM m_raw
         WHERE ts >= now() - interval '1 day'
           AND ts <  date_bin('1 hour', now(), '2026-01-01+00')
         GROUP BY 1, 2) x
  LEFT JOIN m_1h r ON r.bucket = x.b AND r.metric = x.metric
 WHERE r.n IS DISTINCT FROM x.n;
```

- 로컬 재현(예시, PostgreSQL 17.11, 지표 2개): 롤업 행 하나를 지운 뒤 버킷만으로 조인한 옛 쿼리는 정상 버킷 9개를 불일치로 냈고 빠진 행은 못 잡았다. 위 쿼리는 빠진 1행만 냈다.
- 경보 세 가지: `oldest_age > 보존 + 여유`, 미래 파티션 수 < 2, 롤업 불일치 > 0.
- Prometheus는 `--storage.tsdb.retention.time`과 `.size`를 둘 다 안 주면 보존 기간이 **15d**다(Prometheus storage 문서). 원본 계층의 기본 보존을 확인하는 습관이 같다.

## 장애 시나리오와 대처

### 1. 롤업 경계 버그 → 집계 이중 계산

- **현상**: 월 합계 리포트가 원본 합보다 조금 크다. 차이는 버킷 수만큼이다.
- **보이는 형태**: 에러 없음. 로컬 재현 10,800행 → 시간별 합 10,802. 정각 행만 두 버킷에 있다.
- **원인**: `BETWEEN h AND h + interval '1 hour'` 또는 `ts <= end` — 양 끝 포함.
- **대처**
  - 버킷은 `ts >= 시작 AND ts < 끝` 또는 `date_bin`으로 정한다.
  - 검증: 롤업 `sum(n)`과 원본 `count(*)`를 같은 기간으로 비교하는 쿼리를 잡 끝에 둔다.

### 2. 롤업 잡 재실행 → 버킷 중복

- **현상**: 장애 복구 뒤 특정 시간대 그래프만 두 배로 튄다.
- **보이는 형태**: 같은 `(bucket, metric)` 행이 2개. 로컬 재현 n 합 21,600(2배).
- **원인**: 롤업이 INSERT만 한다. 재시도·스케줄 겹침·수동 백필이 같은 구간을 다시 넣었다.
- **대처**: 버킷 키에 PK/UNIQUE를 걸고 **덮어쓰기** upsert로 바꾼다. 중복 행은 원본에서 버킷을 다시 계산해 교체한다. 백필 일반은 [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md).

### 3. 보존 정책 누락 → 디스크 풀

- **현상**: 몇 달 잘 돌던 DB가 어느 날 쓰기를 멈춘다.
- **보이는 형태**
  - PostgreSQL: `ERROR: could not extend file "…": No space left on device` + `HINT: Check free disk space.`(소스 `src/backend/storage/smgr/md.c`의 `could not extend file "%s": %m`. 디스크를 채우는 재현은 하지 않았다).
  - 디스크 사용량 그래프가 선형 증가. `now() - min(ts)`가 설계 보존 기간보다 훨씬 크다.
- **원인**: 보존 잡이 없거나 멈췄다. 기록·조회는 정상이라 아무 신호가 없었다. DELETE로 지웠다면 공간이 테이블 안에 남아 파일이 줄지 않는다(24.1).
- **대처**
  - 긴급: 가장 오래된 원본 파티션부터 `DETACH` → `DROP`. DELETE + `VACUUM FULL`은 ACCESS EXCLUSIVE 락을 잡고, 새 사본을 쓰는 동안 테이블 크기만큼 디스크를 더 쓴다(24.1). 디스크가 찬 상황에서는 특히 맞지 않는다.
  - 근본: 파티션 회전을 잡으로 만들고, `oldest_age`·디스크 여유에 경보를 둔다.

### 4. 미래 파티션 미생성 → 자정에 쓰기 실패

- **현상**: 매일 자정(또는 월초)에 수집이 전부 실패한다.
- **보이는 형태**: PostgreSQL `no partition of relation "raw_p" found for row`, MySQL `ERROR 1526 … Table has no partition for value from column_list`(로컬 재현).
- **원인**: 파티션 생성 잡이 멈췄다. 보존 잡과 짝인 "링 버퍼의 다음 칸"이 없다.
- **대처**: 며칠 앞까지 미리 만든다. 미래 파티션 개수에 경보를 둔다. DEFAULT 파티션은 임시 방편이다. DEFAULT에 행이 들어간 범위로 새 파티션을 만들면 `ERROR: updated partition constraint for default partition "raw_p_def" would be violated by some row`로 거부된다(로컬 재현). 그 행을 먼저 옮겨야 한다.

### 5. 늦게 온 데이터 → 롤업이 원본과 조용히 어긋남

- **현상**: 대시보드(롤업)와 원본 드릴다운의 숫자가 다르다.
- **보이는 형태**: 로컬 재현 00:00 버킷 롤업 3600 / 원본 3601.
- **원인**: 버킷을 닫고 롤업한 뒤 그 구간의 행이 도착했다. 수집 지연·재전송·기기 시계 오차.
- **대처**: 최근 N개 버킷을 매번 덮어써 재계산한다. 원본 보존 > 허용 지연 + 재계산 창. 너무 늦은 행은 버리되 **센다**(원고 ops-patterns/17의 lateDrops).

## 핵심 문장

- 계층은 해상도 × 보존 기간의 표다. 오래된 구간일수록 굵은 계층만 남기고, 넓은 창 조회는 굵은 계층을 읽는다.
- 버킷에는 합칠 수 있는 값(n, sum, min, max)을 담는다. 평균은 sum/count로 만들고, 분위수는 원본이나 스케치가 필요하다.
- 시간 버킷은 반열린 구간이다. `BETWEEN`은 양 끝을 포함해 경계 행을 두 번 센다.
- 롤업은 버킷 키 + 덮어쓰기 upsert로 멱등하게 만든다. 최근 버킷을 다시 계산해 늦은 데이터를 흡수한다.
- 보존은 파티션 DROP으로 한다. DELETE는 공간을 돌려주지 않는다. 다음 파티션 생성과 가장 오래된 파티션 삭제는 링 버퍼의 두 바늘이다.

## 관련 주제·근거

- 선행: [37-row-vs-column-storage](../37-row-vs-column-storage/2-summary.md) — 시계열에 컬럼 저장이 유리한 이유
- 원고·연결
  - [systems/timeseries-resolution-tiers](../../systems/timeseries-resolution-tiers/2-summary.md) — 계층 설계, 감지/조회 분리, ClickHouse `AggregatingMergeTree` 구현
  - [ops-patterns/17-timeseries](../../ops-patterns/17-timeseries/2-summary.md) — 버킷·접기·반열린 구간·lateDrops의 인메모리 구현
  - [systems/clickhouse-mergetree](../../systems/clickhouse-mergetree/2-summary.md) — database 45의 원고
  - [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md) — 과거 구간 롤업 백필
  - [33-partitioning-and-sharding](../33-partitioning-and-sharding/2-summary.md) — 범위 파티셔닝. 초안: [systems/partitioning-vs-sharding](../../systems/partitioning-vs-sharding/2-summary.md)
  - [16-mvcc](../16-mvcc/2-summary.md) — DELETE가 dead tuple을 남기는 이유
- PostgreSQL 17 문서
  - 9.9 Date/Time Functions — `date_bin(stride, source, origin)` <https://www.postgresql.org/docs/17/functions-datetime.html>
  - 5.12 Table Partitioning, `ALTER TABLE … DETACH PARTITION` <https://www.postgresql.org/docs/17/ddl-partitioning.html>
  - 24.1 Routine Vacuuming — 표준 VACUUM은 끝 페이지 외 공간을 OS에 돌려주지 않음, VACUUM FULL은 ACCESS EXCLUSIVE <https://www.postgresql.org/docs/17/routine-vacuuming.html>
  - INSERT `ON CONFLICT … DO UPDATE` <https://www.postgresql.org/docs/17/sql-insert.html>
  - 소스 `src/backend/storage/smgr/md.c`(REL_17_STABLE) — `could not extend file "%s": %m`, `Check free disk space.`
- MySQL 8.4 Reference Manual — 26 Partitioning(RANGE COLUMNS, `DROP PARTITION`), `INSERT … SELECT … ON DUPLICATE KEY UPDATE`(파생 테이블 열 참조) <https://dev.mysql.com/doc/refman/8.4/en/partitioning.html>
- Prometheus Storage — `--storage.tsdb.retention.time` 기본 15d <https://prometheus.io/docs/prometheus/latest/storage/>
- RRDtool `rrdcreate` — round robin archive(RRA), consolidation function <https://oss.oetiker.ch/rrdtool/doc/rrdcreate.en.html>
- 로컬 재현(PostgreSQL 17.11 / MySQL 8.4.10, DB `w31`): BETWEEN 경계 이중 계산(10,800 → 10,802), `date_bin` 반열린 버킷, append 롤업 재실행 2배 vs upsert 멱등, 평균의 평균·중앙값의 평균 오류, 늦은 행 불일치와 재계산, 파티션 DETACH/DROP vs DELETE의 dead tuple·크기, 미래 파티션 없음 에러(PG·MySQL), MySQL `INSERT … SELECT … ON DUPLICATE KEY UPDATE`(파생 테이블) 롤업과 `DROP PARTITION`
