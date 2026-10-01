# database/45-clickhouse-mergetree — ClickHouse MergeTree: 불변 파트, 병합, 희소 인덱스 — 정리 (힌트)

## 해결하는 문제

분석 쿼리는 "행 몇 개"가 아니라 "컬럼 몇 개 × 행 수억 개"를 읽는다.

```text
  SELECT tenant_id, avg(value)            행 저장(PG 힙)으로 읽으면
  FROM events                             ┌ ts │ tenant │ metric │ value │ ... 20컬럼 ┐
  WHERE ts >= now() - INTERVAL 1 DAY      │ 필요 없는 18컬럼도 같은 페이지에 붙어 온다   │
  GROUP BY tenant_id                      └────────────────────────────────────────┘
```

- 행 저장은 한 행의 컬럼들을 한 페이지에 붙여 둔다. 두 컬럼만 필요해도 나머지를 함께 읽는다.
  - PostgreSQL은 큰 값(약 2 kB 넘는 튜플의 긴 컬럼)을 TOAST 테이블에 따로 둔다. 조회하지 않은 TOAST 값은 읽지 않는다. 보통 크기의 컬럼은 힙 튜플에 함께 있다.
- 쓰기도 문제다. 초당 수십만 행을 B+트리에 한 건씩 넣으면 무작위 쓰기가 된다.

MergeTree는 이 두 문제를 한 구조로 푼다.

1. 컬럼별로 나눠 적는다(컬럼 저장). 필요한 컬럼만 읽는다. 큰 파트(`Wide`)는 컬럼마다 파일이 따로다. 작은 파트(`Compact`)는 컬럼들을 파일 하나에 담는다(아래 1절).
2. 쓰기는 정렬된 **불변 파트**를 통째로 한 번 쓴다. 나중에 배경 작업이 파트를 합친다(병합).

쉬운 예: 영수증을 날마다 상자에 담아 창고에 넣는다. 상자 안은 날짜순으로 정리돼 있다. 상자가 많아지면 직원이 작은 상자 여러 개를 큰 상자 하나로 옮겨 담는다.

똑같은 구조다. INSERT 한 번이 상자(파트)이고, 직원이 병합 스레드다. 상자를 너무 자주 만들면 직원이 못 따라간다. 그때 창고가 입고를 늦추거나 거부한다. 이것이 `Too many parts`다.

실무 예:

- 로그·메트릭·이벤트 적재. 에이전트 수천 대가 몇 초마다 작은 묶음을 보낸다.
- 에러(26.8 소스 형식): `Too many parts (3000 with average size of 1.20 MiB) in table 'db.events'. Merges are processing significantly slower than inserts` (괄호 안 수치는 예시)

## 동작·원리

### 1. 파트 하나의 모양

```text
  테이블 events (ORDER BY (tenant_id, ts), PARTITION BY toYYYYMM(ts))
  └─ 파티션 202610
     └─ 파트 202610_5_5_0/            ← 불변. 만들어진 뒤 고치지 않는다
        ├─ primary.idx                 그래뉼 첫 행의 키 값 (희소 인덱스)
        ├─ tenant_id.bin / .mrk        컬럼 파일 + 마크(그래뉼 → 파일 오프셋)
        ├─ ts.bin / .mrk
        ├─ value.bin / .mrk
        ├─ minmax_ts.idx               파티션 키 컬럼의 최솟값·최댓값
        └─ checksums.txt, count.txt ...
```

- *파트(part)*: INSERT가 만드는 정렬된 불변 데이터 묶음이다. 병합의 단위다.
- 파트 안의 행은 `ORDER BY` 키로 정렬돼 있다.
- 작은 파트는 `Compact` 형식(모든 컬럼을 파일 하나에)으로, 큰 파트는 `Wide` 형식(컬럼마다 파일)으로 저장된다.
  - 경계는 `min_bytes_for_wide_part`다. 26.8 소스 기본값은 10485760바이트(10 MiB)다. ClickHouse Cloud 빌드는 1 GiB다.
- 위 그림의 파일 이름은 Wide 형식의 대략적인 모양이다. 확장자(`.mrk2`·`.cmrk` 등)는 형식·버전에 따라 다르다 [?].

**파트 이름 읽기** (문서 "Custom Partitioning Key"):

```text
  202610_1_9_2_11
  │      │ │ │ └─ 뮤테이션 버전 (mutation을 거친 파트만)
  │      │ │ └─── 레벨 = 병합 깊이 (0 = INSERT로 막 생긴 파트)
  │      │ └───── 포함한 블록 번호 최댓값
  │      └─────── 포함한 블록 번호 최솟값
  └────────────── 파티션 ID
```

- `_5_5_0`은 블록 5 하나만 담은, 병합된 적 없는 파트다.
- `_1_9_2`는 블록 1~9를 합친 파트다. 병합을 두 단계 거쳤다.

### 2. INSERT 하나 → 파트 몇 개?

```text
  INSERT (행 10개, ts가 9월 3행 + 10월 7행)
        │ 파티션 키로 나눈다
        ├──> 202609_12_12_0   (3행)
        └──> 202610_13_13_0   (7행)
```

- 동기 INSERT는 **최소 한 개의** 파트를 만든다. 여러 파티션 값에 걸치면 파티션마다 하나씩 만들 수 있다(문서 "Resolving the Too many parts exception").
- 행 수가 `max_insert_block_size`를 넘으면 블록이 나뉘어 파트가 더 생길 수 있다(async insert 문서).
- 원본은 "INSERT 한 번 = 파트 하나"라고 요약한다. 파티션이 하나인 작은 INSERT에서 맞는 말이다.

> 참고: 원본 「대응 관계부터 잡기」 절·「핵심 문장」의 "INSERT 한 번이 파트 하나"는 한 파티션에 들어가는 작은 INSERT에 한정된다. 여러 파티션에 걸친 INSERT는 파티션마다 파트를 만든다(ClickHouse KB "Resolving the Too many parts exception").

### 3. 병합 — 같은 파티션 안에서만

```text
  파티션 202610
  시각 t0:  [_1_1_0] [_2_2_0] [_3_3_0] [_4_4_0] [_5_5_0]      활성 5개
  시각 t1:  [_1_3_1 ─ 병합 결과] [_4_4_0] [_5_5_0]          활성 3개
            (_1_1_0, _2_2_0, _3_3_0 은 비활성으로 남았다가 지워짐)
  시각 t2:  [_1_5_2 ─────────────────────]                   활성 1개

  파티션 202609 의 파트와는 섞이지 않는다
```

- 병합은 정렬된 파트 여러 개를 k-way 병합으로 합쳐 새 파트 하나를 쓴다. 원래 파트는 고치지 않는다.
- *비활성 파트*: 병합에 쓰이고 대체된 옛 파트다. `system.parts.active = 0`으로 보인다. `old_parts_lifetime`(26.8 기본 480초) 뒤 지워진다.
- **다른 파티션의 파트는 병합하지 않는다**(MergeTree 문서: "Parts belonging to different partitions are not merged").
- 병합은 "언젠가" 일어난다. 문서는 삽입 후 대략 10~15분 안에 합쳐진다고 적지만 보장은 아니다.
- 병합 크기 상한: `max_bytes_to_merge_at_max_space_in_pool`(26.8 기본 150 GiB). 한 번에 합칠 파트들의 총크기 상한이다. 설명문은 "배경 병합이 만드는 파트의 최대 크기에 대략 해당한다"고 적는다. 그래서 큰 테이블에는 파트가 여러 개 남는 것이 정상이다.

### 4. 백프레셔 — 파트 수가 인서트를 늦추고 막는다

```text
  파티션 하나의 활성 파트 수
  0 ──────────── 1000 ─────────────────── 3000 ─────>
                  │ parts_to_delay_insert   │ parts_to_throw_insert
     정상         │ INSERT에 sleep을 넣는다   │ INSERT 거부: Too many parts (N)
                  │ (최대 max_delay_to_insert=1초)

  테이블 전체 활성 파트 수 ≥ max_parts_in_total (100000) → 역시 Too many parts
```

| 설정 (26.8 소스 기본값) | 단위 | 뜻 |
|---|---|---|
| `parts_to_delay_insert` = 1000 | 파티션 하나 | 이르면 INSERT를 인위적으로 늦춘다 |
| `parts_to_throw_insert` = 3000 | 파티션 하나 | 이르면 INSERT를 예외로 거부한다 |
| `max_parts_in_total` = 100000 | 테이블 전체 | 이르면 거부한다 |
| `max_delay_to_insert` = 1 (초) | | 지연의 최댓값 계산에 쓴다 |
| `min_delay_to_insert_ms` = 10 | | 지연의 최솟값 |
| `max_avg_part_size_for_too_many_parts` = 1 GiB | 파티션 하나 | 평균 파트 크기가 이보다 크면 위 두 검사를 하지 않는다 |

- 경계: 설정 설명문은 "exceeds(넘으면)"라고 적지만, 26.8 코드(`MergeTreeData::delayInsertOrThrowIfNeeded`)는 INSERT 직전 활성 파트 수가 임계 **이상**(`>=`)이면 늦추거나 거부한다. 파트 3000개인 파티션이 있으면 INSERT가 이미 거부된다.
- 비교하는 값은 테이블에서 활성 파트가 가장 많은 파티션의 파트 수다(`getMaxPartsCountAndSizeForPartition`).
- 23.1 이후 지연 식: `delay_ms = max(min_delay_to_insert_ms, max_delay_to_insert × 1000 × (파트 수 − delay 임계 + 1) / (throw 임계 − delay 임계))`.
  - 예(기본값): 파티션에 파트가 2000개면 `1000 × 1001 / 2000 ≈ 500ms`다(계산 예시).
- `parts_to_throw_insert`는 23.6 이전 기본값이 300이었다(설정 설명문). 옛 글의 "300"은 그 시절 값이다.
- 기본값은 버전마다 바뀐다. 실제 값은 `SELECT name, value FROM system.merge_tree_settings WHERE name LIKE 'parts_to%'`로 확인한다(원본 「관련 설정」 절).

### 5. 희소 인덱스와 그래뉼 — 읽을 범위 고르기

MergeTree 문서의 그림 그대로다. 키는 `(CounterID, Date)`다.

```text
Whole data:     [---------------------------------------------]
CounterID:      [aaaaaaaaaaaaaaaaaabbbbcdeeeeeeeeeeeeefgggggggghhhhhhhhhiiiiiiiiikllllllll]
Date:           [1111111222222233331233211111222222333211111112122222223111112223311122333]
Marks:           |      |      |      |      |      |      |      |      |      |      |
                a,1    a,2    a,3    b,3    e,2    e,3    g,1    h,2    i,1    i,3    l,3
Marks numbers:   0      1      2      3      4      5      6      7      8      9      10

  WHERE CounterID IN ('a','h')            → 마크 [0,3), [6,8) 만 읽는다
  WHERE CounterID IN ('a','h') AND Date=3 → [1,3), [7,8)
  WHERE Date = 3                          → [1,10] — 거의 다 읽는다
```

- 문서는 이 예에 이어 "인덱스를 쓰는 편이 전체 스캔보다 항상 효과적"이라고 적는다. `Date = 3`만 있어도 마크 0은 건너뛴다.
- 한 범위를 읽을 때 블록마다 최대 `index_granularity × 2`행을 여분으로 읽을 수 있다(문서).

- *그래뉼(granule)*: ClickHouse가 읽는 가장 작은 행 묶음이다. 기본 `index_granularity` = 8192행이다. 행 크기가 크면 `index_granularity_bytes` 때문에 더 적은 행으로 끊긴다(적응형 그래뉼).
- *마크(mark)*: 그래뉼 첫 행의 키 값(`primary.idx`)과, 그 그래뉼이 컬럼 파일 어디서 시작하는지(`.mrk`)다.
- *희소 인덱스*: 행마다가 아니라 그래뉼마다 항목 하나를 두는 인덱스다. 작아서 메모리에 올라간다.
- 첫 키 컬럼 조건은 마크에 대한 **이진 탐색**으로 범위를 찾는다.
- 둘째 이후 키 컬럼만 조건에 있으면 **generic exclusion search**를 쓴다. 효과는 앞 컬럼의 카디널리티에 달렸다(가이드 "A Practical Introduction to Primary Indexes").
  - 앞 컬럼 카디널리티가 낮으면: 같은 앞 값이 여러 그래뉼에 이어진다. 그 구간 안에서 둘째 컬럼이 정렬돼 있어 많이 건너뛴다.
  - 앞 컬럼 카디널리티가 높으면: 그래뉼마다 앞 값이 바뀐다. 둘째 컬럼 값이 그래뉼 경계에서 흩어져 거의 못 건너뛴다.
- 그래서 가이드는 키 컬럼 카디널리티 차이가 크면 **카디널리티 오름차순**으로 두라고 권한다. 압축률도 좋아진다.
- ClickHouse의 PRIMARY KEY는 유일성 제약이 아니다. 같은 키 값의 행을 여러 번 넣을 수 있다(MergeTree 문서).

### 6. 비교: PostgreSQL BRIN도 "블록 범위당 요약 하나"다

```text
  PG 힙:  [블록 0..127][블록 128..255][블록 256..383] ...
  BRIN:   (min,max)    (min,max)      (min,max)         ← 범위당 한 항목
```

로컬 재현(예시, PostgreSQL 17.11): `ts` 순서로 30만 행을 넣고 인덱스 크기를 비교했다.

```text
   relname  | pg_size_pretty
  ----------+----------------
   ev       | 15 MB
   ev_brin  | 24 kB          ← 블록 범위(128블록)당 min/max 하나
   ev_btree | 6600 kB        ← 행마다 항목

  Bitmap Heap Scan on ev (actual rows=600 loops=1)
    Rows Removed by Index Recheck: 19496     ← 범위 단위라 여분 행을 읽고 버린다
    Heap Blocks: lossy=128
    ->  Bitmap Index Scan on ev_brin (actual rows=1280 loops=1)
```

- 공통점: 데이터가 키 순서로 놓여 있을 때만 작고 효과적이다. 범위 단위로 읽어 여분 행이 생긴다.
- 차이: BRIN은 블록 범위에 실제로 있는 값을 요약할 뿐, 힙 정렬을 보장하지 않는다. 물리 순서와 값이 상관돼 있을수록 많이 건너뛴다. MergeTree 파트는 **항상** ORDER BY로 정렬돼 쓰인다.

## 쓰이는 자료구조·알고리즘

- **정렬된 불변 파트 + 배경 병합(LSM 계열)** — memtable 없이 INSERT 블록이 바로 정렬 파트가 된다는 점이 LSM과 다르다. [systems/lsm-tree](../../systems/lsm-tree/2-summary.md), [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md), [data-structure/lsm-merge-model](../../data-structure/lsm-merge-model/)
- **k-way 병합** — 정렬된 파트 여러 개를 하나로 합친다. [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)
- **희소 인덱스 + 이진 탐색** — 마크 배열에서 첫 키 컬럼 범위를 찾는다. [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)
- **generic exclusion search** — 둘째 이후 키 컬럼으로 마크 구간을 재귀적으로 배제한다.
- **컬럼 저장 + 압축** — 정렬 덕분에 비슷한 값이 붙어 압축이 잘 된다. `LowCardinality`는 사전 인코딩이다.
- **데이터 스키핑 인덱스** — minmax, set, bloom_filter, ngrambf_v1 등. 그래뉼 묶음마다 요약을 둔다. [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 테이블 설계 순서

```sql
CREATE TABLE events (
    ts        DateTime,
    tenant_id UInt32,
    metric    LowCardinality(String),
    value     Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)            -- 삭제·보존 단위. 인덱스 목적이 아니다
ORDER BY (tenant_id, metric, ts)     -- 거의 모든 쿼리의 WHERE 컬럼을 앞에
TTL ts + INTERVAL 90 DAY;
```

1. **ORDER BY**: 자주 거르는 컬럼을 앞에 둔다. 카디널리티 차이가 크면 낮은 것부터 둔다. 테이블을 만든 뒤에는 기존 키를 바꾸거나 순서를 뒤집을 수 없다. `ALTER TABLE ... MODIFY ORDER BY`는 같은 ALTER에서 `ADD COLUMN`한 새 컬럼을 뒤에 붙이는 것만 된다(문서 "ALTER TABLE ... MODIFY ORDER BY"). 다른 순서가 필요하면 projection을 쓴다(데이터가 중복된다).
2. **PARTITION BY**: 문서는 대부분 파티션 키가 필요 없고, 있어도 월보다 잘게 나눌 일은 드물다고 한다. 관측(observability) 데이터는 일 단위가 흔하다. 고객 ID로 나누지 말라고 한다. 고객 ID는 ORDER BY 첫 컬럼에 둔다.
3. **쓰기 경로**: 동기 INSERT면 클라이언트가 묶는다. 묶기 어려우면 async insert를 쓴다.

### 2. 쓰기 경로 — 묶어서 넣기

```text
  에이전트 1000대 ──(수 행씩)──┐
                              ├─> [서버 버퍼 (쿼리 모양·설정별)] ──flush──> 파트 1개
  (async_insert = 1)          ┘      flush 조건: 크기 / 시간 / 쿼리 수 중 먼저 오는 것 (파티션이 여럿이면 파트도 여럿)
```

- 26.8 소스 기본값: `async_insert = true`(26.2부터 기본 켜짐), `wait_for_async_insert = true`, `async_insert_max_data_size = 10485760`(10 MiB, Cloud 100 MiB), `async_insert_busy_timeout_max_ms = 200`(Cloud 1000), `async_insert_max_query_number = 450`.
  - 쿼리 수 조건은 insert 중복 제거가 켜져 있을 때만 flush를 일으킨다(`src/Interpreters/AsynchronousInsertQueue.cpp`의 `has_enough_queries`, 설정 설명문).
  - async insert 가이드 본문은 크기 기본값을 "100 MiB"라고 적는다. 소스와 설정 레퍼런스는 10 MiB, Cloud 100 MiB다. 소스 기준으로 적었다.
- 24.2부터 적응형 타임아웃이 기본이다(`async_insert_use_adaptive_busy_timeout`). 50ms~200ms 사이에서 움직인다.
- `wait_for_async_insert = 1`: 버퍼가 디스크로 flush된 뒤 응답한다. 실패하면 클라이언트가 에러를 받는다.
- `wait_for_async_insert = 0`: 버퍼에 넣자마자 응답한다. 문서는 "데이터가 저장된다는 보장이 없다"고 적는다. 에러는 서버 로그와, 로깅을 켠 경우 `system.asynchronous_insert_log`(`status = 'FlushError'`·`exception` 컬럼)에만 남는다. `system.asynchronous_inserts`는 아직 대기 중인 INSERT만 보여 준다. 원본 「async_insert」 절의 트레이드오프 표가 이 부분이다.
- 26.2부터 async insert도 재시도 중복 제거를 한다. 일반 MergeTree는 `non_replicated_deduplication_window`가 0보다 커야 한다.
- async insert를 켜도 파티션 키 카디널리티가 높으면 `Too many parts`가 난다. flush 하나가 파티션 값마다 파트를 만들기 때문이다(가이드).

Java 쪽에서 묶는 예:

```java
// 동기 INSERT를 쓸 때: 행을 모아 한 번에 보낸다 (JDBC 배치)
try (PreparedStatement ps = conn.prepareStatement(
        "INSERT INTO events (ts, tenant_id, metric, value) VALUES (?, ?, ?, ?)")) {
    for (Event e : buffer) {            // buffer: 수만 행 단위로 모은 것 (예시)
        ps.setObject(1, e.ts());
        ps.setInt(2, e.tenantId());
        ps.setString(3, e.metric());
        ps.setDouble(4, e.value());
        ps.addBatch();
    }
    ps.executeBatch();                  // 드라이버가 한 INSERT로 보내는지는 드라이버 구현에 달렸다 [?]
}
```

### 3. 진단 — 파트·병합 보기

```sql
-- 파티션별 활성 파트 수 (Too many parts 원인 찾기)
SELECT database, table, partition_id, count() AS active_parts,
       sum(rows) AS rows, formatReadableSize(sum(bytes_on_disk)) AS size
FROM system.parts
WHERE active AND database = 'db' AND table = 'events'
GROUP BY database, table, partition_id
ORDER BY active_parts DESC;

-- 레벨 0 파트가 많으면: 막 들어온 파트를 병합이 못 따라간다
SELECT partition_id, level, count() FROM system.parts
WHERE active AND table = 'events' GROUP BY partition_id, level ORDER BY partition_id, level;

-- 지금 도는 병합
SELECT table, elapsed, progress, num_parts, result_part_name FROM system.merges;

-- 읽은 파트·그래뉼 수 확인
EXPLAIN indexes = 1
SELECT count() FROM events WHERE tenant_id = 42 AND ts >= now() - INTERVAL 1 DAY;
```

- `WHERE active`를 빼면 병합 후 아직 안 지운 비활성 파트까지 센다(원본 「모니터링 쿼리」 절).
- 병합 이력은 `system.part_log`에 남는다. 서버 설정에서 켜져 있어야 한다.

## 장애 시나리오와 대처

### 1. 작은 INSERT 폭주 → `Too many parts`

- **현상**: 적재가 느려지다가 INSERT가 실패한다.
- **보이는 형태**: 먼저 INSERT 지연이 늘어난다(파티션의 활성 파트 1000개부터). 서버 로그에 `Delaying inserting block by N ms. because there are M parts ...`가 찍힌다. 그다음 `Too many parts (3000 with average size of …) in table '…'. Merges are processing significantly slower than inserts`. 클라이언트는 이 예외(에러 코드 `TOO_MANY_PARTS`)를 받는다.
- **원인**: 에이전트가 수 행짜리 동기 INSERT를 초당 수백 번 보낸다. 파트 생성 속도가 병합 속도를 넘는다.
- **대처**
  - 긴급: 보내는 쪽 빈도를 낮춘다. `parts_to_throw_insert`를 올리는 것은 시간을 버는 것뿐이다. 설정 설명문도 SELECT 성능이 떨어지고 병합 문제를 늦게 알아챈다고 경고한다.
  - 근본: 클라이언트 배치로 묶거나 `async_insert = 1, wait_for_async_insert = 1`로 서버에서 묶는다.

### 2. 파티션 키가 너무 잘다 → 파트가 곱으로 늘어난다

- **현상**: 배치로 넣는데도 파트가 많다. 쿼리도 느리다.
- **보이는 형태**: `system.parts`에 파티션이 수천 개다. 파티션마다 파트가 몇 개씩 있다.
- **원인**: `PARTITION BY (tenant_id, toDate(ts))`처럼 잘게 나눴다. 배치 하나가 파티션 수만큼 파트를 만든다. 병합은 파티션을 넘지 않는다. 같은 파티션 안의 파트끼리는 합쳐지지만, 파티션마다 최소 한 파트씩은 남는다. 문서는 파티션 약 1000개 초과를 피하라고 한다(파일·파일 디스크립터 수).
- **대처**: 파티션을 월 단위로 성기게 바꾸고 tenant_id는 ORDER BY 앞으로 옮긴다. 기존 테이블의 파티션 키를 제자리에서 바꾸는 방법은 확인하지 못했다 [?]. 보통 새 테이블로 옮겨 담는다(`INSERT INTO new SELECT * FROM old`).

### 3. 병합이 멈췄다 → 파트는 계속 쌓인다

- **현상**: 적재량은 평소와 같은데 파트 수가 계속 오른다.
- **보이는 형태**: `system.merges`가 비어 있거나 한 병합이 오래 걸린다. 서버 로그에 디스크 공간 부족 메시지가 보인다 [?].
- **원인**: 병합은 결과 파트를 새로 쓴 뒤 옛 파트를 지운다. 여유 공간이 부족하면 큰 병합을 시작하지 못한다. 병합 스레드 풀이 뮤테이션(`ALTER ... UPDATE/DELETE`)에 묶여 있을 수도 있다.
- **대처**: 디스크를 확보한다. 진행 중인 무거운 뮤테이션을 `system.mutations`에서 확인하고 필요하면 `KILL MUTATION`한다. 뮤테이션을 일상 갱신 경로로 쓰지 않는다.

### 4. `ReplacingMergeTree`인데 중복이 보인다

- **현상**: 같은 키의 행이 두 번 나온다. 집계가 부풀려진다.
- **원인**: 문서 그대로 "중복 제거는 병합 때만 일어나고, 병합 시점은 알 수 없다". 다른 파티션에 들어간 같은 키는 영원히 합쳐지지 않는다.
- **대처**: 조회에 `FINAL`을 붙이거나 `argMax`로 최신 행을 고른다. `OPTIMIZE ... FINAL`을 주기적으로 돌리는 것은 대처가 아니다(다음 항목).

### 5. `OPTIMIZE TABLE ... FINAL` 크론

- **현상**: 새벽마다 CPU·디스크 I/O가 치솟고 그 시간대 쿼리가 느리다.
- **원인**: `OPTIMIZE FINAL`은 파티션마다 그 안의 활성 파트를 파트 하나로 합친다(`PARTITION`을 안 주면 모든 파티션에 대해). 이미 큰 파트도 풀고 다시 압축해 쓴다. 평소 병합 상한(`max_bytes_to_merge_at_max_space_in_pool`, 약 150 GB)도 무시한다. 문서는 대부분의 경우 피하라고 한다. 끝나도 새 INSERT가 곧 다시 파트를 만든다.
- **대처**: 크론을 지운다. 중복 제거가 목적이면 조회 쪽 `FINAL`을 쓴다. `FINAL`은 필터가 기본 키 컬럼과 같을 때 무리가 적다(문서 "Avoid OPTIMIZE FINAL").

## 핵심 문장

- MergeTree는 INSERT 블록을 정렬된 불변 파트로 한 번에 쓰고, 배경 병합이 파트 수를 줄인다.
- `Too many parts`는 디스크가 찬 것이 아니라 백프레셔다. 흔한 원인은 파티션 하나의 활성 파트 수가 임계(26.8 기본 3000)에 이른 것이고, 테이블 전체 파트 수(`max_parts_in_total`) 등 다른 임계로도 같은 에러 코드가 난다.
- 병합은 파티션 경계를 넘지 않는다. 그래서 잘게 나눈 파티션은 파트 수를 곱으로 늘린다.
- 희소 인덱스는 그래뉼(기본 8192행)마다 마크 하나를 둔다. 첫 키 컬럼은 이진 탐색, 나머지는 앞 컬럼 카디널리티에 따라 효과가 달라지는 배제 탐색을 쓴다.
- ClickHouse의 PRIMARY KEY는 정렬·인덱스 기준일 뿐 유일성 제약이 아니다.

## 관련 주제·근거

원본 노트: [systems/clickhouse-mergetree](../../systems/clickhouse-mergetree/2-summary.md). 세그먼트 대응표·모니터링 쿼리 모음·변형 엔진 표는 원본에 있다. 이 노트는 엔진 내부(파트 이름·병합 선택·그래뉼 탐색), 설정 기본값의 버전, 장애 대처, 질문·정답을 채운다.

버전 기준: ClickHouse 소스 `26.8` 브랜치(`src/Storages/MergeTree/MergeTreeSettings.cpp`, `src/Core/Settings.cpp`)와 ClickHouse 공식 문서(2026-10 확인). 로컬 ClickHouse 서버는 없다. 비교용 재현은 PostgreSQL 17.11 BRIN으로 했다.

- 원본: [systems/clickhouse-mergetree](../../systems/clickhouse-mergetree/2-summary.md) — 세그먼트 대응, 모니터링 쿼리, async_insert 트레이드오프, 두 키, 변형 엔진
- 선행
  - [37-row-vs-column-storage](../37-row-vs-column-storage/2-summary.md)
  - [38-lsm-storage-engine](../38-lsm-storage-engine/2-summary.md) · 원본 [systems/lsm-tree](../../systems/lsm-tree/2-summary.md)
- 연결
  - [systems/timeseries-resolution-tiers](../../systems/timeseries-resolution-tiers/2-summary.md) — AggregatingMergeTree 롤업
  - [data-structure/lsm-merge-model](../../data-structure/lsm-merge-model/) — 병합 비용 모델
  - [40-filters-and-specialized-indexes](../40-filters-and-specialized-indexes/2-summary.md) — BRIN·블룸 필터
- ClickHouse 문서 (github.com/ClickHouse/ClickHouse `docs/`, 2026-10 확인)
  - MergeTree table engine — 파트·Wide/Compact·그래뉼·희소 인덱스 그림·"Parts belonging to different partitions are not merged" <https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree>
  - Custom Partitioning Key — 파트 이름 형식, "about a thousand partitions" <https://clickhouse.com/docs/engines/table-engines/mergetree-family/custom-partitioning-key>
  - ReplacingMergeTree — "Data deduplication occurs only during a merge" <https://clickhouse.com/docs/engines/table-engines/mergetree-family/replacingmergetree>
  - A Practical Introduction to Primary Indexes — 이진 탐색·generic exclusion search·카디널리티 오름차순 <https://clickhouse.com/docs/guides/best-practices/sparse-primary-indexes>
  - Choosing a primary key · Avoid OPTIMIZE FINAL (best practices)
  - Asynchronous inserts (`docs/snippets/_async_inserts.mdx`) · KB "Resolving the Too many parts exception"
  - Session settings `async_insert`(26.2 기본 1) · MergeTree settings
- ClickHouse 소스 `26.8` 브랜치
  - `src/Storages/MergeTree/MergeTreeSettings.cpp` — `index_granularity` 8192, `parts_to_delay_insert` 1000, `parts_to_throw_insert` 3000(23.6 이전 300), `max_parts_in_total` 100000, `max_delay_to_insert` 1, `min_delay_to_insert_ms` 10, `max_avg_part_size_for_too_many_parts` 1 GiB, `old_parts_lifetime` 480초, `max_bytes_to_merge_at_max_space_in_pool` 150 GiB, `min_bytes_for_wide_part` 10 MiB
  - `src/Core/Settings.cpp` — async insert 기본값 · `src/Core/SettingsChangesHistory.cpp` — 26.2 "Enable async inserts by default."
- PostgreSQL 17 문서 11.8 BRIN Indexes <https://www.postgresql.org/docs/17/brin.html>
- PostgreSQL 17 문서 65.2 TOAST <https://www.postgresql.org/docs/17/storage-toast.html>
- ClickHouse 문서 `ALTER TABLE ... MODIFY ORDER BY`, `OPTIMIZE`, `system.asynchronous_inserts`·`system.asynchronous_insert_log` (`docs/reference/` 아래, 2026-10 확인)
- ClickHouse 소스 `26.8` `src/Storages/MergeTree/MergeTreeData.cpp` `delayInsertOrThrowIfNeeded` — `TOO_MANY_PARTS`를 내는 경로(테이블 전체·비활성 파트·dead blob·파티션별 활성 파트)
- 로컬 재현(PostgreSQL 17.11): 정렬 적재 30만 행의 BRIN(24 kB)·B-tree(6600 kB) 크기, BRIN 범위 스캔의 lossy 블록과 recheck 제거 행
