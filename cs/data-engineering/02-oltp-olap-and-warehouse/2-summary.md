# data-engineering/02-oltp-olap-and-warehouse — 운영 DB와 분석 저장소를 나누는 이유, 웨어하우스·마트, ETL vs ELT — 정리 (힌트)

## 해결하는 문제

운영 DB 하나로 주문도 받고 월간 리포트도 뽑으면 둘이 서로를 방해한다.

```text
  같은 PostgreSQL
  ├─ 주문 API:   SELECT … WHERE id = ?           0.1 ms짜리 수천~수만 건/초
  └─ 리포트:     SELECT region, sum(amount) …     전 행 스캔, 1초 가까이
  → 리포트가 도는 동안 주문 API의 p99가 오른다
```

- 해법: 분석용 사본을 따로 둔다. 운영 DB는 원천, 분석 저장소는 파생이다([01](../01-system-of-record-and-derived-data/2-summary.md)).
  - *OLTP(Online Transaction Processing)*: 키로 몇 행을 읽고 쓰는 짧은 요청이 많은 작업. 주문·결제·로그인.
  - *OLAP(Online Analytical Processing)*: 많은 행의 몇 컬럼을 훑어 집계하는 긴 질의가 적은 작업. 리포트·대시보드·분석.

쉬운 예: 가게 계산대와 회계 사무실.
- 계산대는 손님 한 명씩 빨리 처리해야 한다.
- 회계 담당자가 계산대 앞에서 한 달 치 영수증을 넘기면 줄이 밀린다.
- 그래서 영수증 사본을 회계 사무실로 보내 거기서 계산한다.

똑같은 구조다.\
DDIA 1판 3장 "Transaction Processing or Analytics?"·"Data Warehousing" 절이 이 분리를 다룬다(절 제목은 출판사 목차로 확인).

실무 예:
- 주문 DB(PostgreSQL) → 매일 밤 적재 → 클라우드 웨어하우스(컬럼 저장) → BI 대시보드.
- 리포트를 운영 DB의 읽기 복제본으로 옮겼더니 복제 지연·쿼리 취소가 생긴다([database/32](../../database/32-replication-leader-follower/2-summary.md)).

## 동작·원리

### 1. 두 작업의 모양

| | OLTP | OLAP |
|---|---|---|
| 한 요청이 읽는 행 | 키로 찾은 몇 행 | 수백만 행의 몇 컬럼 |
| 쓰기 | 작은 INSERT·UPDATE가 잦음 | 대량 적재(배치·스트림) |
| 사용자 | 앱(최종 사용자의 요청) | 분석가·대시보드 |
| 병목 | 지연(ms), 동시성·락 | 스캔량(디스크·메모리 대역폭) |
| 맞는 저장 방식 | 행 저장 + B+Tree | 컬럼 저장 + 압축 |

- 저장 방식의 차이는 [database/37](../../database/37-row-vs-column-storage/2-summary.md)에 실험과 함께 있다. 여기서는 "왜 저장소를 나누나"만 본다.

### 2. 분석 저장소의 층

```text
  운영 DB들 ──추출──► [원본 적재 층]  ──변환──► [통합 모델 층]  ──► [마트]  ──► BI·리포트
  (주문·회원·결제)     raw / staging           웨어하우스           팀·주제별
                      원본 그대로              팩트·차원(03)          매출 마트, 마케팅 마트
```

- *데이터 웨어하우스*: 여러 운영 시스템의 데이터를 분석용으로 통합해 모아 둔 저장소.
- *데이터 마트*: 한 주제·한 부서용으로 좁힌 분석 저장소. 매출 마트, 마케팅 마트. 위 그림처럼 웨어하우스에서 떼어 내는 것은 종속(dependent) 마트다. 운영 시스템에서 직접 받는 독립(independent) 마트, 둘 다 쓰는 혼합(hybrid) 마트도 있다(Oracle Data Warehousing Guide 「Data Marts」).
- *원본 적재 층(raw·staging)*: 운영 데이터를 변환 없이 그대로 받아 두는 곳. ELT에서 이 층이 재처리의 출발점이다.
- 층 이름(raw·staging·bronze·silver·gold 등)은 팀·도구마다 다르다. 이름보다 "원본을 그대로 남기는 층이 있나"가 중요하다.

### 3. ETL vs ELT — 변환을 어디서, 언제 하나

```text
  ETL:  추출(E) ──► 변환(T, 흔히 별도 서버·도구) ──► 적재(L)
                    └ 실패 행·원본은 여기서 사라질 수 있다

  ELT:  추출(E) ──► 적재(L, 원본 그대로 raw 테이블) ──► 변환(T, 웨어하우스 안 SQL)
                                    └ 원본이 남는다 → 변환 버그를 고쳐 다시 돌릴 수 있다
```

- *ETL(Extract-Transform-Load)*: 추출한 데이터를 변환한 뒤 최종 테이블에 적재한다. 최종 테이블이 받는 것은 이미 정제된 결과다. 변환 장소는 웨어하우스 밖 도구일 때가 많지만, 웨어하우스 안 staging 테이블에서 변환한 뒤 차원·팩트에 넣는 ETL도 있다(Microsoft Fabric 「Load tables in a dimensional model」).
- *ELT(Extract-Load-Transform)*: 원본을 먼저 적재하고, 웨어하우스의 계산 자원으로 변환한다.
- Armbrust 외(CIDR 2021)는 1세대 분석 플랫폼을 "운영 시스템에서 웨어하우스로 바로 ETL, schema-on-write"로, 오늘의 2계층 구조를 "먼저 레이크로 ETL하고 다시 웨어하우스로 ELT"로 묘사한다. 그리고 단계가 늘수록 "complexity, delays, and new failure modes"가 생긴다고 쓴다(1절).
- ELT의 대가: 원본을 저장하는 비용, 원본에 든 개인정보도 그대로 남는 문제(이 영역 [12](../12-data-retention-and-erasure/2-summary.md)).

### 실험: 리포트가 같은 DB의 점 조회 지연을 올린다

환경: 이 호스트(i7-13700HX), `postgres:17`(PostgreSQL 17.11) 일회용 컨테이너 `--cpus=2 --memory=1g --network none`, `shared_buffers=128MB`. `orders` 200만 행(테이블+인덱스 269 MB).

- 점 조회: `pgbench -c 4 -j 2 -T 20`, 스크립트 `SELECT status, amount FROM orders WHERE id = :id`(id 무작위).
- 리포트: `SELECT region, status, count(*), sum(amount), avg(amount) FROM orders GROUP BY region, status`를 22초 동안 반복하는 세션 2개.
- 리포트 단독 실행: `Parallel Seq Scan`, `Workers Launched: 2`, 796 ms.
- 지연 분위수는 `pgbench -l` 트랜잭션 로그를 정렬해 구했다. 3회 반복.

```text
                       latency avg      p50          p99          tps
  점 조회만 (3회)       0.234~0.256 ms   0.091~0.096  0.404~0.515  15,605~17,073
  + 리포트 2개 (3회)    0.892~0.922 ms   0.129~0.144  1.452~2.783   4,338~4,485
  리포트 완료 수: 세션당 22초에 8~9회 (단독 796 ms → 약 2.4~2.7초/회)
```

- 관찰: 리포트가 도는 동안 p99가 회차별로 약 3.6~6.7배가 되었고, 처리량은 약 1/4로 떨어졌다.
- 해석: 이 환경은 CPU 2개 몫(`--cpus=2`)을 점 조회 4클라이언트·pgbench 자신·리포트(병렬 워커 포함)가 나눠 쓴다. 리포트는 한 번에 `shared hit=11055 read=17947`로 공유 버퍼(128MB) 밖의 페이지도 읽으므로 I/O·버퍼 교체도 섞여 있다.
- 대조 실험(사실 점검 때 같은 환경에서 2회): 디스크·버퍼를 쓰지 않는 CPU 전용 쿼리 `SELECT count(*) FROM generate_series(1,40000000)`를 리포트 대신 돌렸다.

```text
                       p99            tps
  점 조회만 (2회)       0.481~0.490    15,862~16,248
  + 리포트 2개 (2회)    1.735~2.525     4,269~4,312
  + CPU 전용 2개 (2회)  0.534~0.590     6,945~7,741
  + CPU 전용 6개 (2회)  2.303~2.884     5,434~6,154
```

- 읽는 법: I/O가 없는 CPU 경쟁만으로도 처리량이 절반 아래로, 6개면 p99가 리포트 때와 비슷한 크기로 올랐다. 그래서 CPU 경쟁이 큰 몫이라는 해석은 뒷받침된다. 다만 리포트 2개 쪽의 처리량 하락이 더 커서 I/O·버퍼 경쟁의 몫이 없다고는 말할 수 없다(둘을 따로 재지 않았다). 한 호스트·작은 데이터의 측정이라 배율은 환경마다 다르다.

## 쓰이는 자료구조·알고리즘

- **컬럼 저장·압축** — 분석 저장소는 컬럼별로 모아 RLE·딕셔너리·비트 패킹으로 압축한다. 몇 컬럼만 읽어 스캔량을 줄인다([database/37](../../database/37-row-vs-column-storage/2-summary.md), ClickHouse 예: [database/45](../../database/45-clickhouse-mergetree/2-summary.md)).
- **외부 정렬** — 메모리보다 큰 적재·집계는 정렬된 덩어리(run)를 디스크에 쓰고 k-way 병합한다([algorithm/11-external-sort-and-k-way-merge](../../algorithm/11-external-sort-and-k-way-merge/2-summary.md)). PostgreSQL의 `GROUP BY`도 해시가 메모리를 넘으면 디스크로 넘친다([database/41](../../database/41-sorting-and-aggregation/2-summary.md)).
- **해시 집계와 병렬 스캔** — 실험 계획의 `Parallel Seq Scan` → 부분 집계 → `Gather Merge`는 데이터를 나눠 집계한 뒤 합치는 구조다.
- **대조(reconciliation) = 그룹별 집계의 차** — 원천과 웨어하우스를 같은 키(일자)로 묶어 `count`·`sum`을 비교한다.

## 적용 — 풀어나가는 법

### 1. 어디서 돌릴지 정하는 순서

1. 이 쿼리는 몇 행을 읽나(`EXPLAIN (ANALYZE, BUFFERS)`의 Buffers·rows).
2. 운영 피크 시간에 돌아야 하나.
3. 결과가 얼마나 신선해야 하나(초·분·일).
4. 위 답이 "많이 읽음 + 신선도 하루"면 웨어하우스, "적게 읽음 + 실시간"이면 운영 DB(인덱스로 해결), 그 사이면 복제본·구체화 뷰를 검토한다.

### 2. 운영 DB에서 범인 찾기 (PostgreSQL 17)

```sql
-- 지금 오래 도는 쿼리
SELECT pid, now() - query_start AS running, state, left(query, 60)
FROM pg_stat_activity WHERE state = 'active' ORDER BY running DESC;

-- 누적으로 많이 읽은 쿼리 (pg_stat_statements 확장이 켜져 있을 때)
SELECT calls, round(mean_exec_time) AS ms, shared_blks_read, left(query, 60)
FROM pg_stat_statements ORDER BY shared_blks_read DESC LIMIT 10;
```

- 리포트 쿼리를 막을 때까지 기다리지 말고, 리포트용 역할에 `statement_timeout`을 건다([database/22](../../database/22-database-side-timeouts/2-summary.md)).

### 3. 적재 대조 — "합계가 운영과 다르다"를 숫자로 확인

- 적재가 끝나면 원천과 웨어하우스를 같은 키(일자)로 묶어 행 수·합계를 비교한다. 잡의 성공 여부와 별개로 숫자를 본다.

### 실험: 변환에 실패한 행을 조용히 건너뛰면

같은 환경. 원천 `src_payment` 1만 행. 파일로 내보낸 텍스트를 `raw_payment`(전부 `text` 컬럼)에 그대로 적재했고, 그중 36행은 금액에 천 단위 쉼표가 붙어 왔다(`1,234`).

```sql
-- 변환 v1: 숫자가 아니면 조용히 건너뛴다
INSERT INTO fct_payment
SELECT id::int, paid_on::date, amount::int FROM raw_payment WHERE amount ~ '^[0-9]+$';
```

```text
  대조: 원천 vs 웨어하우스 (v1)
   src_rows | dw_rows | src_sum  |  dw_sum
      10000 |    9964 | 34995000 | 34867682        ← 36행·127,318 빠짐, 잡은 "성공"

  일자별 대조 (어긋난 날만, 앞 5행)
   paid_on    | src_n | dw_n | missing_amount
   2026-09-01 |   333 |  332 |           1690
   2026-09-02 |   334 |  332 |           9736
   ...

  변환 v2: 쉼표를 지우는 규칙으로 고치고 raw에서 다시 변환, 거부 행은 etl_reject에
   dw_rows 10000 | dw_sum 34995000 | rejects 0
```

- v1은 에러 없이 끝났다. 대시보드 합계만 운영과 달랐다(커리큘럼 ⚠).
- v2를 돌릴 수 있었던 것은 `raw_payment`에 원본이 남아 있었기 때문이다. 원본을 버리는 ETL이었다면 원천에서 다시 추출해야 한다. 원천이 이미 바뀌었거나 지워졌으면 그때의 값은 되살릴 수 없다.

대조 쿼리의 모양:

```sql
SELECT s.paid_on, s.n AS src_n, d.n AS dw_n, s.amt - coalesce(d.amt, 0) AS missing_amount
FROM (SELECT paid_on, count(*) n, sum(amount) amt FROM src_payment GROUP BY 1) s
LEFT JOIN (SELECT paid_on, count(*) n, sum(amount) amt FROM fct_payment GROUP BY 1) d USING (paid_on)
WHERE s.n IS DISTINCT FROM d.n OR s.amt IS DISTINCT FROM d.amt;
```

### 4. 변환 실패를 다루는 코드 모양 (Java 21, 실행하지 않은 예시)

- 아래는 모양만 보이는 조각이다. `RawPayment`·`Payment`·`batch` 정의가 없어 그대로는 컴파일되지 않고, 실험에서 돌리지 않았다. 실험은 위의 SQL(v1·v2)이다.

```java
record Rejected(String id, String raw, String reason) {}

// 건너뛰지 않고, 셈과 함께 따로 모은다
List<Payment> ok = new ArrayList<>();
List<Rejected> rejected = new ArrayList<>();
for (RawPayment r : batch) {
    try {
        ok.add(new Payment(Integer.parseInt(r.id()), LocalDate.parse(r.paidOn()),
                           Integer.parseInt(r.amount().replace(",", ""))));
    } catch (RuntimeException e) {
        rejected.add(new Rejected(r.id(), r.amount(), e.getClass().getSimpleName()));
    }
}
if (rejected.size() > batch.size() * 0.001) {          // 허용 비율(예시 0.1%)을 넘으면 실패로
    throw new IllegalStateException("rejects=" + rejected.size() + "/" + batch.size());
}
```

- 거부 행을 버리지 않고 남긴다. 몇 행을 거부했는지가 적재 결과의 일부다.
- 허용 비율을 넘으면 잡을 실패시킨다. "초록인데 숫자가 틀린" 상태를 빨간색으로 바꾸는 장치다. 차단 vs 경고 기준은 이 영역 [10](../10-data-quality-and-data-observability/2-summary.md).

## 장애 시나리오와 대처

### 1. 운영 DB에서 분석 쿼리 → 리포트 시간대에 p99 급등 (⚠ 커리큘럼)

- **현상**: 매일 아침 9시 무렵 주문 API가 느려진다.
- **보이는 형태**: API p99가 평소의 몇 배(실험: 0.40~0.52 ms → 1.45~2.78 ms). `pg_stat_activity`에 BI 계정의 긴 `GROUP BY` 쿼리. DB CPU 사용률 상승.
- **원인**: 전 행 스캔 집계가 CPU·디스크·버퍼를 점 조회와 나눠 쓴다.
- **대처**: 리포트를 웨어하우스로 옮긴다. 당장은 리포트 역할에 `statement_timeout`·연결 수 제한, 실행 시간대 조정.

### 2. 리포트를 복제본으로 옮겼더니 복제 지연·쿼리 취소 (⚠ 커리큘럼)

- **현상**: 리포트용 팔로워의 데이터가 몇 분씩 늦거나, 리포트가 중간에 취소된다.
- **보이는 형태**: `canceling statement due to conflict with recovery`. 팔로워의 `pg_last_wal_receive_lsn()`과 `pg_last_wal_replay_lsn()` 차이(받았지만 아직 재생 못 한 WAL)가 커진다. `now() - pg_last_xact_replay_timestamp()`는 리더에 새 쓰기가 없어도 커지므로 단독으로는 지연의 증거가 아니다(PostgreSQL 17 문서 9.28.4).
- **원인**: 팔로워의 긴 조회가 리더의 vacuum 기록 재생과 충돌한다. 재생은 `max_standby_streaming_delay`(기본 30초)까지 기다린 뒤 조회를 취소한다(PostgreSQL 17 26.4 — [database/32](../../database/32-replication-leader-follower/2-summary.md)).
- **대처**: 아주 긴 분석은 논리 복제·별도 분석 저장소로 보낸다. 리포트 전용 팔로워는 지연 허용값을 늘리거나 `hot_standby_feedback`(리더 bloat 감수)을 쓴다.

### 3. 변환 실패 행을 조용히 건너뜀 → 대시보드 합계가 운영과 다르다 (⚠ 커리큘럼)

- **현상**: 재무팀 "대시보드 9월 매출이 결제 DB보다 12만 원 적다".
- **보이는 형태**: 잡 상태는 성공. 원천 vs 웨어하우스 대조에서 `src_rows 10000 / dw_rows 9964`. 일자별 대조에서 매일 1~2행씩 빠짐.
- **원인**: 변환 단계가 형식이 다른 행(천 단위 쉼표)을 필터로 걸러 냈다. 거부 수를 아무도 세지 않았다.
- **대처**: 거부 행을 별도 테이블에 남기고 수를 지표로 낸다. 허용 비율을 넘으면 잡을 실패시킨다. 원천과의 행 수·합계 대조를 적재 직후에 돈다.

### 4. 원본을 남기지 않는 ETL → 변환 버그를 찾아도 재처리할 원본이 없다 (⚠ 커리큘럼)

- **현상**: 3개월 전부터 환율 변환 버그가 있었다. 고쳤는데 과거 데이터를 다시 계산할 수 없다.
- **보이는 형태**: 웨어하우스에는 변환된 값만 있다. 원천 DB는 그사이 값이 갱신되어 그때의 값이 없다.
- **원인**: 변환 전 원본을 저장하지 않았다.
- **대처**: 추출한 원본을 raw 층에 적재 시각과 함께 남긴다(ELT). 변환은 raw에서 다시 돌 수 있는 순수한 SQL로 만든다(이 영역 [08](../08-idempotent-pipelines-and-backfill/2-summary.md)).

## 핵심 문장

- OLTP는 키로 몇 행을 읽고 쓰는 짧은 요청, OLAP은 많은 행의 몇 컬럼을 훑는 긴 집계다. 한 DB에서 섞으면 서로의 자원을 빼앗는다.
- 실험(PostgreSQL 17, `--cpus=2`)에서 리포트 2개가 도는 동안 점 조회 p99가 0.40~0.52 ms에서 1.45~2.78 ms로, 처리량이 약 1/4로 떨어졌다.
- 웨어하우스는 여러 운영 DB를 분석용으로 통합한 파생 저장소, 마트는 한 주제·부서용으로 좁힌 저장소다(웨어하우스에서 떼어 내면 종속 마트).
- ELT는 원본을 먼저 적재하고 웨어하우스 안에서 변환한다. 원본이 남아 있어 변환 버그를 고친 뒤 다시 돌릴 수 있다.
- 변환 실패 행을 조용히 건너뛰면 잡은 성공하고 합계만 틀린다. 거부 행을 세어 남기고, 원천과 행 수·합계를 대조한다.

## 관련 주제·근거

- 선행
  - [01-system-of-record-and-derived-data](../01-system-of-record-and-derived-data/2-summary.md) — 분석 저장소는 파생본
  - [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md) — 행 저장 vs 컬럼 저장과 압축
- 연결
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — 팔로워의 긴 조회와 재생 지연
  - [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md) · [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md) · [database/45-clickhouse-mergetree](../../database/45-clickhouse-mergetree/2-summary.md)
  - [algorithm/11-external-sort-and-k-way-merge](../../algorithm/11-external-sort-and-k-way-merge/2-summary.md)
  - [distributed/30-batch-and-stream-processing](../../distributed/30-batch-and-stream-processing/2-summary.md) — 배치 처리의 원리
- 후속
  - [03-dimensional-modeling](../03-dimensional-modeling/2-summary.md) — 웨어하우스 안의 모델
  - [08-idempotent-pipelines-and-backfill](../08-idempotent-pipelines-and-backfill/2-summary.md) · [10-data-quality-and-data-observability](../10-data-quality-and-data-observability/2-summary.md) · [14-lakehouse-table-formats](../14-lakehouse-table-formats/2-summary.md)
- 문헌
  - Kleppmann, DDIA 1판(2017) 3장 "Transaction Processing or Analytics?"·"Data Warehousing"·"Column-Oriented Storage"·"Aggregation: Data Cubes and Materialized Views" — 절 제목은 출판사 목차(Internet Archive 2025-01-05 사본)로 확인. 본문의 OLTP/OLAP 비교표 번호는 `[?]`.
  - Armbrust, Ghodsi, Xin, Zaharia, "Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics", CIDR 2021, 1절(1세대 ETL·schema-on-write, 레이크 schema-on-read, "first ETLed into lakes, and then again ELTed into warehouses", reliability·staleness 문제) <https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf>
  - PostgreSQL 17 문서 26.4 Hot Standby(`max_standby_streaming_delay`) <https://www.postgresql.org/docs/17/hot-standby.html> · pgbench <https://www.postgresql.org/docs/17/pgbench.html>
- 실험(이 호스트 i7-13700HX, `--cpus=2 --memory=1g --network none`, PostgreSQL 17.11)
  - `orders` 200만 행(269 MB): pgbench 점 조회 4클라이언트 20초 × 3회, 단독 vs 리포트 세션 2개 동시. p99 0.404~0.515 ms → 1.452~2.783 ms, tps 15,605~17,073 → 4,338~4,485. 리포트 단독 796 ms(병렬 워커 2). 사실 점검 재실행 2회(p99 0.481~0.490 → 1.735~2.525, tps → 4,269~4,312)와 CPU 전용 쿼리 대조(2개·6개).
  - `src_payment` 1만 행 → `raw_payment`(text, 쉼표 36행) → 변환 v1(조용히 건너뜀) 9,964행·34,867,682 vs 원천 10,000행·34,995,000, 일자별 대조, 변환 v2(raw에서 재변환) 일치·거부 0.
