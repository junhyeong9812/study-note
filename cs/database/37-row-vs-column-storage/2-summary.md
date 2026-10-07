# database/37-row-vs-column-storage — 행 저장 vs 컬럼 저장과 압축 — 정리 (힌트)

## 해결하는 문제

06번에서 본 행 저장은 **행 하나를 한곳에** 둔다. 주문 한 건을 읽고 고치기에는 딱 좋다.\
그런데 분석 쿼리는 모양이 반대다. 행은 수억 개를 훑지만 칼럼은 두세 개만 본다.

```text
  SELECT country, sum(amount) FROM orders WHERE created_at >= '2026-01-01' GROUP BY country;
  → 필요한 칼럼: country, amount, created_at   (테이블에 칼럼이 40개 있어도)

  행 저장:   [id|country|status|amount|memo|…40칸] [id|country|…] …   → 40칸을 다 읽는다
  컬럼 저장: country 파일 [KR KR KR US …]  amount 파일 [120 300 …]  → 3개 파일만 읽는다
```

로컬 재현(예시, PostgreSQL 17.11): 10만 행 `wide(id int, v int, pad char(500))`에서 `sum(v)`는 필요한 값이 4바이트 × 10만 = 약 400KB인데 **6667페이지(52MB)** 를 훑었다(06번 6절). 이번엔 전부 공유 버퍼 적중(`shared hit`)이라 디스크 읽기는 아니었지만, 훑은 페이지 양은 테이블 전체다.

쉬운 예: 학생 카드 묶음과 과목별 성적표다.
- 학생 한 명의 모든 정보가 필요하면 카드 한 장(행)을 뽑는 게 빠르다.
- "전교생 수학 평균"이 필요하면 수학 성적표 한 장(칼럼)만 보면 된다. 카드 1000장을 다 넘길 필요가 없다.

똑같은 구조다.\
**행 저장(NSM)** 은 OLTP(한 건씩 읽고 쓰기), **컬럼 저장(DSM)** 은 OLAP(많은 행의 몇 칼럼 집계)에 맞는다(CMU 15-445 L5).

실무 예:
- 운영 PostgreSQL·MySQL에서 월간 매출 리포트를 돌리면 풀 스캔으로 몇 분이 걸리고 그동안 OLTP가 느려진다.
- 같은 데이터를 ClickHouse·BigQuery·Parquet 파일로 옮기면 초 단위로 끝난다.
- 반대로 ClickHouse에서 주문 한 건 상태를 `UPDATE`로 자주 바꾸려 하면 문서가 "무거운 연산, 자주 쓰라고 만든 것이 아니다"라고 경고한다.

## 동작·원리

### 1. 같은 표, 세 가지 배치

```text
  논리 표          id  country  status   amount
                   1   KR       PAID     120
                   2   US       SHIPPED  300
                   3   KR       PAID      80

  행 저장 (NSM)    페이지: [1,KR,PAID,120][2,US,SHIPPED,300][3,KR,PAID,80]

  컬럼 저장 (DSM)  id 칼럼:      [1][2][3]
                   country 칼럼: [KR][US][KR]
                   status 칼럼:  [PAID][SHIPPED][PAID]
                   amount 칼럼:  [120][300][80]
                   → i번째 값끼리 같은 행 (고정 길이 오프셋으로 맞춘다)

  혼합 (PAX)       행 그룹 1: [id 1..3][country …][status …][amount …]   ← 그룹 안은 칼럼별
                   행 그룹 2: …
```

- *NSM(N-ary Storage Model)*: 한 행의 모든 속성을 한 페이지에 연속으로 둔다(L5). 한 번 읽으면 행 전체가 나온다.
  - 예외: 아주 큰 값은 따로 둔다. PostgreSQL은 TOAST 테이블, InnoDB는 오버플로 페이지에 저장한다(06번).
- *DSM(Decomposition Storage Model)*: 한 속성의 모든 값을 연속으로 둔다(L5).
  - 행을 다시 맞추는 법: 주로 **고정 길이 오프셋**(i번째끼리 같은 행). 드물게 값마다 행 ID를 붙인다(공간이 크다).
- *PAX(Partition Attributes Across)*: 행을 묶음(행 그룹)으로 자르고, 묶음 안에서 칼럼별로 모은다(L5).
  - Parquet가 이 모양이다. 행 그룹 → 칼럼마다 연속된 column chunk → 페이지(Parquet 문서 Concepts).

### 2. 무엇이 빨라지고 무엇이 느려지나

```text
                         행 저장 (NSM)                컬럼 저장 (DSM)
  단건 조회 (id=42 전체)  페이지 1개                    칼럼 수만큼 여러 곳에서 모아 붙임
  단건 INSERT/UPDATE      행 페이지 1개 (+인덱스)       칼럼마다 수정, 압축 블록을 풀고 다시 씀
  몇 칼럼 × 많은 행 집계   모든 칼럼을 읽음              필요한 칼럼만 읽음
  압축                    한 페이지에 타입이 섞여 어려움  같은 타입·비슷한 값이 연속 → 잘 됨
```

- CMU L5의 정리: NSM은 삽입·갱신·삭제와 행 전체 조회에 빠르고, 테이블의 큰 부분이나 일부 칼럼을 훑기에는 비효율적이다. DSM은 쿼리당 낭비 I/O가 줄고 압축이 잘 되지만, 점 조회·삽입·갱신·삭제가 느리다(행을 쪼개고 다시 붙여야 해서).
- 컬럼 저장 엔진은 쓰기를 모아서 한다. ClickHouse MergeTree는 동기 INSERT마다(블록·파티션별로) 불변 **파트**를 만들고 배경에서 병합한다. ClickHouse 26.3부터는 `async_insert`가 기본으로 켜져, 서버가 작은 INSERT 여러 개를 버퍼에 모았다가 한 파트로 쓴다(26.3 릴리스 글). 행 하나를 바꾸는 `ALTER TABLE … UPDATE`는 "뮤테이션"이다. 비동기로 돌고, 해당 데이터 파트를 다시 쓴다(ClickHouse 문서 ALTER, ALTER UPDATE).

### 3. 컬럼 압축 — 같은 칼럼은 값이 닮았다

```text
  RLE (run-length)       정렬된 country: DE DE … FR … KR … US …  →  (DE, 시작 0, 길이 20072) (FR, 20072, 20108) …
  딕셔너리               status: PAID SHIPPED PAID CANCELLED  →  사전 {0:PAID, 1:SHIPPED, 2:CANCELLED}
                                                                   코드 [0 1 0 2 …]  (2비트면 충분)
  비트맵                 country = KR ?  [1 0 1 1 0 …]
                         country = US ?  [0 1 0 0 1 …]        값 종류가 적을 때만 이득
  비트 패킹              amount가 모두 < 2^17 이면 int64 대신 17비트씩
  델타                   정렬된 시간: 1000, 1003, 1004 → 1000, +3, +1
```

- *RLE*: 같은 값이 연속된 구간을 (값, 시작, 길이)로 줄인다. **정렬해 두면** 연속 구간이 길어진다(L5).
- *딕셔너리 인코딩*: 자주 나오는 값을 작은 코드로 바꾼다. 가장 흔한 DB 압축 방식이다. 코드가 원래 값의 순서를 지키면(order-preserving) 압축된 채로 범위 비교·정렬을 할 수 있다(L5).
- *비트맵 인코딩*: 값마다 비트 벡터 하나. 값 종류(카디널리티)가 많으면 오히려 커진다(L5). 희소하면 Roaring 같은 압축 비트맵을 쓴다.

로컬 재현(예시, Python 3 zlib 레벨 6, 10만 행 합성 데이터: id·country 5종·status 3종·amount 무작위):

```text
  원본(텍스트)                      약 2.24MB
  행 단위로 이어 붙여 압축           659,979 바이트
  칼럼별로 모아 각각 압축            572,576 바이트   (id 212,846 · country 46,088 · status 39,160 · amount 274,482)
  country·status로 정렬 후 칼럼 압축  country 333 바이트 · status 1,592 바이트
  status 연속 구간(run) 수          정렬 전 66,609개 → 정렬 후 15개
  country 연속 구간                  정렬 후 5개 (DE 20072, FR 20108, JP 19843, KR 20146, US 19831)
```

- 칼럼별로만 모아도 압축이 좋아지고(660KB → 573KB), 정렬까지 하면 값 종류가 적은 칼럼은 거의 사라진다(46KB → 333B).
- 무작위 숫자(`amount`)는 어떤 배치든 잘 줄지 않는다. 압축률은 **데이터 분포**가 정한다.
- 그래서 컬럼 저장 엔진은 **정렬 키**를 고르게 한다. ClickHouse `ORDER BY`가 그것이다([clickhouse-mergetree](../../systems/clickhouse-mergetree/2-summary.md) 「쿼리 비용을 결정하는 두 개의 키」).

### 4. 실행도 칼럼 단위로

- 압축된 칼럼을 필요한 칼럼만 읽고, 한 번에 값 수천 개씩 묶어 처리한다(벡터화 실행, 54번).
- 행을 되도록 늦게 조립한다. 필터를 칼럼 단위로 먼저 걸고, 살아남은 위치의 다른 칼럼만 꺼낸다. 이 순서는 엔진마다 다르다 [?].

## 쓰이는 자료구조·알고리즘

- **런 렝스 인코딩(RLE)**: 연속 구간 압축. 정렬과 짝이다.
- **딕셔너리 인코딩**: 값 → 코드 사상. 순서 보존 사전이면 코드끼리 비교할 수 있다. → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)(인코딩 시 사전 조회)
- **비트맵**: 값별 비트 벡터, AND/OR로 조건 결합. → [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **비트 패킹·델타 인코딩**: 작은 정수를 적은 비트로, 정렬된 값은 차이로.
- **PAX 행 그룹**: 행 저장의 지역성과 컬럼 저장의 스캔 효율을 절충한다.
- **병합 트리(파트 + 배경 병합)**: 컬럼 저장의 쓰기를 모으는 방법. LSM과 같은 발상이다(38번).

## 적용 — 풀어나가는 법

**1) 워크로드를 먼저 나눈다.**

```text
  질문                                          행 저장 (PG·InnoDB)    컬럼 저장 (ClickHouse·Parquet)
  한 건을 ID로 읽고 고치나?                       ✓                      ✗ (느림)
  트랜잭션·제약(FK·UNIQUE)이 필요한가?            ✓                      제한적
  수억 행의 몇 칼럼을 집계하나?                   ✗ (풀 스캔)            ✓
  데이터가 주로 추가만 되나(이벤트·로그)?          가능                   ✓
```

**2) 운영 DB에서 분석 쿼리의 비용을 잰다.**

```sql
-- PostgreSQL: 칼럼 1개 집계가 몇 페이지를 읽는지
EXPLAIN (ANALYZE, BUFFERS) SELECT sum(v) FROM wide;
--   Buffers: shared hit=6667      ← 필요한 건 v 하나지만 테이블 전체
SELECT pg_size_pretty(pg_relation_size('wide'));   -- 52 MB

-- MySQL 8.4
EXPLAIN ANALYZE SELECT SUM(v) FROM wide;          -- Table scan on wide
```

**3) 분석은 분석 저장소로 보낸다.** 운영 DB → CDC·배치 → 컬럼 저장(ClickHouse 테이블, Parquet 파일). 설계는 [data-engineering/02](../../data-engineering/02-oltp-olap-and-warehouse/2-summary.md)가 다룬다.

```sql
-- ClickHouse: 정렬 키로 압축과 범위 건너뛰기를 함께 얻는다
CREATE TABLE orders_olap (
  created_at DateTime, country LowCardinality(String), status LowCardinality(String),
  amount UInt32, id UInt64
) ENGINE = MergeTree ORDER BY (country, status, created_at);
-- LowCardinality = 딕셔너리 인코딩된 문자열 타입
```

**4) 컬럼 저장에서 "고치기"가 필요하면.**
- 행을 고치지 말고 새 버전을 추가하는 모델로 바꾼다(ReplacingMergeTree, 이벤트 소싱처럼 상태 변화를 행으로 추가).
- 꼭 고쳐야 하면 한 번에 모아서, 파티션을 좁혀서 한다(`IN PARTITION`). ClickHouse의 경량 `UPDATE`(patch part)는 문서상 베타다.

**5) 앱에서 (TypeScript).** 운영 API와 리포트 API의 저장소를 나눈다.

```ts
// 운영: 한 건 조회·갱신은 PostgreSQL
await pg.query("UPDATE orders SET status = $1 WHERE id = $2", ["SHIPPED", id]);

// 리포트: 집계는 ClickHouse (공식 Node 클라이언트 @clickhouse/client)
const rs = await ch.query({
  query: "SELECT country, sum(amount) AS total FROM orders_olap WHERE created_at >= {from:DateTime} GROUP BY country",
  query_params: { from: "2026-01-01 00:00:00" },
  format: "JSONEachRow",
});
const rows = await rs.json();
```

## 장애 시나리오와 대처

**1) OLAP 쿼리를 행 저장 OLTP DB에서 → 전체 스캔 (⚠)**
- 현상: 월말 리포트가 도는 동안 주문 API p99가 튄다. 리포트 자체도 몇 분씩 걸린다.
- 보이는 형태: PG `Seq Scan`에 `Buffers: shared read=` 수십만, `pg_stat_activity`에 긴 `active` 쿼리. MySQL 슬로 쿼리 로그 `Rows_examined` = 테이블 행 수. 버퍼 풀 적중률 하락(07번).
- 원인: 행 저장은 칼럼 몇 개가 필요해도 행 전체가 든 페이지를 모두 읽는다. 읽은 페이지가 OLTP의 뜨거운 페이지를 밀어낸다.
- 대처: 리포트를 읽기 복제본이나 컬럼 저장으로 옮긴다. 당장은 필요한 칼럼만 담은 요약 테이블을 배치로 만든다. 운영 DB에서 돌려야 하면 시간대를 나누고 keyset으로 쪼갠다.

**2) 컬럼 저장에 단건 UPDATE를 자주 → 느림 (⚠)**
- 현상: ClickHouse에 주문 상태를 행마다 `ALTER TABLE … UPDATE`로 반영했더니, 반영이 늦고 디스크 I/O가 치솟는다.
- 보이는 형태: `system.mutations`에 `is_done = 0`인 항목이 쌓인다. 쿼리 결과에 일부만 바뀐 상태가 보인다(뮤테이션은 원자적이지 않다).
- 원인: 뮤테이션은 비동기로 돌며 해당 데이터 파트를 다시 쓴다. 한 행을 위해 큰 파트를 다시 쓴다. 문서가 "자주 쓰라고 만든 것이 아니다"라고 적는다(ALTER UPDATE).
- 대처: 상태 변화를 새 행으로 추가하고 읽을 때 최신을 고른다(ReplacingMergeTree·`argMax`). 갱신은 모아서 드물게. 잦은 갱신이 본질이면 그 데이터는 행 저장 DB에 둔다.

**3) 컬럼 저장에 작은 INSERT를 자주 → 파트 폭증**
- 현상: 이벤트를 한 건씩 INSERT했더니 삽입이 거부된다.
- 보이는 형태: ClickHouse `Too many parts` 오류.
- 원인: 동기 INSERT마다 새 파트가 생기고, 병합이 따라가지 못한다(`async_insert`가 꺼져 있을 때 — 26.3 이전 기본값).
- 대처: 배치로 모아 넣는다. `async_insert`. 자세한 원인·설정은 [clickhouse-mergetree](../../systems/clickhouse-mergetree/2-summary.md) 「파트 증식과 "Too many parts"」.

**4) 정렬 키를 잘못 골라 압축·건너뛰기가 안 된다**
- 현상: 컬럼 저장으로 옮겼는데 예상만큼 작지도 빠르지도 않다.
- 보이는 형태: 칼럼별 압축률(`system.columns`의 압축 전후 크기)이 낮다. 조건이 있는 쿼리도 거의 전체 행을 읽는다.
- 원인: 정렬 키가 무작위에 가까운 칼럼(ID·UUID)으로 시작한다. 같은 값이 흩어져 RLE·딕셔너리가 덜 먹히고, 범위 건너뛰기도 안 된다. 재현에서 정렬 전후 status 연속 구간이 66,609 → 15개였다.
- 대처: 필터에 자주 쓰고 카디널리티가 낮은 칼럼을 정렬 키 앞쪽에 둔다.

## 핵심 문장

- 행 저장(NSM)은 한 행을 한곳에, 컬럼 저장(DSM)은 한 칼럼을 한곳에 둔다. 전자는 한 건 읽고 쓰기, 후자는 많은 행의 몇 칼럼 집계에 맞는다.
- 행 저장에서 테이블을 순차 스캔하면 칼럼 하나를 집계해도 행 전체가 든 페이지를 다 읽는다(커버링 인덱스·인덱스 전용 스캔이면 예외). 재현에서 400KB가 필요한 집계가 52MB를 훑었다.
- 컬럼 저장은 같은 타입·비슷한 값이 이어져 RLE·딕셔너리·비트맵·비트 패킹이 잘 먹는다. 정렬하면 더 잘 먹는다.
- 대가로 점 조회·단건 갱신이 느리다. 컬럼 저장 엔진은 쓰기를 모아 불변 파트로 쓰고, 행 갱신은 무거운 재작성(뮤테이션)이 된다.
- PAX(Parquet의 행 그룹)는 행 묶음 안에서 칼럼별로 모아 두 방식을 절충한다.

## 관련 주제·근거

- 선행: [06-pages-and-tuple-layout](../06-pages-and-tuple-layout/2-summary.md) — 행 저장 페이지와 "행이 넓으면 스캔 I/O 증가"
- 연결
  - [clickhouse-mergetree](../../systems/clickhouse-mergetree/2-summary.md) — 컬럼 저장 + 병합 트리 엔진, 파트·정렬 키 (curriculum 45번)
  - [38-lsm-storage-engine](../38-lsm-storage-engine/2-summary.md) — 불변 파일 + 배경 병합이라는 같은 발상
  - database [54-query-execution-models](../54-query-execution-models/2-summary.md) — 벡터화 실행.
  - [data-engineering/02-oltp-olap-and-warehouse](../../data-engineering/02-oltp-olap-and-warehouse/2-summary.md) — 운영 DB와 분석 저장소 분리
- 강의·교재
  - CMU 15-445 Fall 2024 L5 Storage Models & Compression(NSM·DSM·PAX, 행 재조립, RLE·비트 패킹·비트맵·델타·딕셔너리, 순서 보존 인코딩)
  - DDIA 1판 3장 "Column-Oriented Storage"(칼럼 압축·비트맵, 정렬 순서) — 이 노트의 수치는 인용하지 않았다
- 문서
  - Apache Parquet Concepts(row group · column chunk · page) <https://parquet.apache.org/docs/concepts/>
  - ClickHouse 문서 ALTER — Mutations(비동기, 파트 재작성, 원자성 없음, `system.mutations`) <https://clickhouse.com/docs/sql-reference/statements/alter>
  - ClickHouse 26.3 릴리스 글("async inserts turned on by default") <https://clickhouse.com/blog/clickhouse-release-26-03> · 소스 `src/Core/Settings.cpp` `async_insert`(기본 true, 26.2 변경 이력)
  - ClickHouse 문서 ALTER TABLE … UPDATE("heavy operation not designed for frequent use") <https://clickhouse.com/docs/sql-reference/statements/alter/update> · 경량 UPDATE(patch part, 베타) <https://clickhouse.com/docs/sql-reference/statements/update>
- 로컬 재현: PostgreSQL 17.11 narrow/wide `sum(v)`의 읽은 버퍼(443 vs 6667), Python 3 zlib으로 10만 행 합성 데이터의 행 단위·칼럼 단위·정렬 후 압축 크기와 RLE 구간 수
