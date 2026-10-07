# data-engineering/08-idempotent-pipelines-and-backfill — 멱등 파이프라인과 백필: 파티션 덮어쓰기, 시점별 규칙, 늦은 데이터 — 정리 (힌트)

## 해결하는 문제

배치 잡은 다시 돈다. 실패해서 재시도하고, 버그를 고쳐 과거를 다시 계산하고(백필), 늦게 온 데이터 때문에 다시 계산한다. 그때마다 결과가 바뀌면 안 된다.

```text
  잡: "10-01 수수료 합계를 daily_fee에 넣는다"
  append 방식      1회차 → [10-01: 100건]
                   재시도 → [10-01: 100건] [10-01: 100건]     ← 합계 2배, 에러 없음
  덮어쓰기 방식     1회차 → [10-01: 100건]
                   재시도 → 10-01 파티션을 지우고 다시 → [10-01: 100건]
```

- *멱등(idempotent)*: 여러 번 실행해도 한 번 실행한 것과 결과가 같은 성질. API 요청의 멱등은 [reliability/13](../../reliability/13-idempotency/2-summary.md)에서 다뤘다. 여기서는 **배치 태스크의 출력**이 대상이다.
- *백필(backfill)*: 과거 기간의 출력을 다시 계산해 채우는 일. 새 테이블을 과거부터 채우거나, 원본 수정·로직 수정 뒤 과거를 고친다.
- *파티션*: 출력을 날짜 같은 키로 나눈 단위. 여기서는 물리 파티션이든 `WHERE ds = …`로 나눈 논리 구간이든 "한 번에 통째로 다시 쓰는 단위"를 뜻한다.

쉬운 예: 반 성적표를 공책에 날마다 한 쪽씩 쓴다.
- 틀린 날이 있으면 그 쪽에 덧쓰지 않고, 그 쪽을 찢고 처음부터 다시 쓴다.
- 다시 쓸 때는 그날 시험지(원본)와 그날 적용하던 채점 기준을 쓴다. 오늘 채점 기준으로 지난 학기를 다시 채점하면 확정된 성적이 바뀐다.

똑같은 구조다.\
"한 쪽 = 파티션", "찢고 다시 쓰기 = 덮어쓰기", "그날의 채점 기준 = 시점별 규칙"이다.

실무 예:
- Airflow 같은 스케줄러가 실패한 태스크를 자동 재시도했더니 일 매출이 2배로 찍혔다.
- 수수료율 변경 후, 다른 이유로 9월을 백필했더니 확정된 9월 수수료가 줄었다.
- 모바일 이벤트가 하루 늦게 와서 어제 숫자가 영구히 조금 모자란다.

## 동작·원리

### 1. 순수한 태스크 — 결정적 + 멱등 + 덮어쓰기

```text
  태스크 인스턴스 (table=daily_fee, ds=2026-10-01)
     입력: orders_raw의 ds=10-01 (불변 적재 영역) + 그 시점의 규칙(fee_rate)
     출력: daily_fee의 ds=10-01 파티션 하나 ── 통째로 덮어쓴다
  같은 입력 + 같은 코드 → 같은 출력. 몇 번 돌려도 같다
```

- Beauchemin "Functional Data Engineering — a modern paradigm for batch data processing"(Medium, 2018-01-08)
  - "A pure task should be deterministic and idempotent". 같은 입력 파라미터로 다시 실행하면 이전 출력을 **덮어써야** 한다("forcing an overwrite approach").
  - 태스크 하나는 출력 하나(파티션 하나)를 낸다. 태스크 단위와 파티션 단위를 일치시킨다("each partition to a task instance").
  - 파티션을 불변 블록으로 보고, UPDATE·APPEND·DELETE로 고치지 말고 통째로 덮어쓴다. 물리 파티션이 없으면 "파티션 키로 DELETE 후 INSERT"도 된다. 단 `TRUNCATE PARTITION`은 보통 메타데이터 작업이지만 DELETE는 비쌀 수 있다고 적는다.
  - 원본은 "persistent and immutable staging area"에 쌓아 두고 바꾸지 않는다. 그래야 순수 태스크로 웨어하우스 전체를 처음부터 다시 만들 수 있다.
- *결정적(deterministic)*: 같은 입력에 같은 출력. 현재 시각·난수·"최신" 차원 조회가 끼면 깨진다([distributed/30 장애 5](../../distributed/30-batch-and-stream-processing/2-summary.md)).
- DDIA 1판 10장의 절 "The Output of Batch Workflows"가 배치 출력을 불변 파일로 만들고 교체하는 생각을 다룬다(절 제목은 O'Reilly 목차로 확인, 본문은 열지 못함).

#### 실험 1: append 재실행 vs 덮어쓰기 재실행

(실험, `postgres:17` = PostgreSQL 17.11 전용 컨테이너 `--network none`, `p.sql`, 합성 주문 09-28~10-02 하루 100건 × 10,000원, 2026-10-07)

```sql
-- append 잡
INSERT INTO daily_fee SELECT p, count(*), sum(amount) * 0.025 FROM orders_raw WHERE event_date = p;
-- 덮어쓰기 잡 (함수 하나 = 한 트랜잭션)
DELETE FROM daily_fee WHERE ds = p;
INSERT INTO daily_fee
SELECT p, count(*), sum(o.amount * r.rate)
FROM orders_raw o JOIN fee_rate r ON o.event_date >= r.valid_from AND o.event_date < r.valid_to
WHERE o.event_date = p;
```

```text
== 1. append 잡을 10-01에 대해 두 번 실행(재시도)
     ds     | rows | orders |    fee
 2026-10-01 |    2 |    200 | 50000.000
== 2. 덮어쓰기 잡을 10-01에 대해 두 번 실행
     ds     | rows | orders |    fee
 2026-10-01 |    1 |    100 | 25000.000
```

- append는 재시도 한 번에 행·주문 수·수수료가 모두 2배가 됐다. 잡은 두 번 다 성공이다.
- 덮어쓰기는 차례로 몇 번 돌려도 한 행·100건·25,000원이었다.
- 단 같은 `ds`를 두 세션이 **동시에** 덮어쓰면 다르다. PostgreSQL 17 기본 격리 수준(READ COMMITTED)에서 두 번째 세션의 DELETE는 첫 세션이 지운 옛 행만 기다렸다 건너뛰고, 첫 세션이 새로 넣은 행은 보지 못한다. 판정 재실험(DELETE와 INSERT 사이 3초, 1초 뒤 같은 잡 시작)에서 `2026-10-01 | 2행 | 200건 | 50,000원`이 됐다. 같은 파티션 실행을 직렬화하거나(스케줄러의 파티션별 동시 실행 1개, `pg_advisory_xact_lock` 등), `ds`에 유일 제약을 두어 겹친 실행이 중복 대신 오류로 드러나게 한다.

#### 실험 2: 덮어쓰는 동안 읽는 쪽은 무엇을 보나

```text
-- 6a. DELETE와 INSERT를 한 트랜잭션에(사이에 3초 쉼), 1초 뒤 다른 세션이 읽음
reader at +1s: 100
-- 6b. DELETE와 INSERT를 따로 커밋(자동 커밋 문장 두 개, 사이에 3초)
reader at +1s: 0
after: 100
```

- 한 트랜잭션이면 읽는 쪽은 커밋 전까지 옛 값(100)을 봤다. MVCC 덕분에 지우는 중에도 읽기가 막히지 않고 옛 버전을 본다([database/16](../../database/16-mvcc/2-summary.md)).
- 따로 커밋하면 그 사이 읽은 대시보드는 **0건**을 봤다. 덮어쓰기는 "지우기 + 쓰기"를 한 단위로 바꿔야 멱등이면서 안전하다.
- 물리 파티션을 쓰는 엔진에서는 새 파티션을 따로 만든 뒤 교체하는 방식도 있다. 엔진마다 문법·원자성 범위가 다르므로 해당 엔진 문서로 확인한다 [?] — 이 노트에서는 PostgreSQL의 DELETE + INSERT 한 트랜잭션만 실험했다. 테이블 포맷의 스냅샷 교체는 [14번](../14-lakehouse-table-formats/2-summary.md)의 주제다.

### 2. 백필 = 파티션을 다시 고르는 일

```text
  태스크 DAG (테이블 수준)          파티션 DAG (Beauchemin: 실제로 다시 돌리는 단위)
  orders_raw → daily_fee → monthly   raw[09-28] → fee[09-28] ┐
                                     raw[09-29] → fee[09-29] ├→ monthly[09]
                                     raw[09-30] → fee[09-30] ┘
  백필 09-28~09-30 = 이 파티션들과 그 하류를 위상 순서로 다시 실행

  과거 의존(past dependency)이 있으면:  cum[09-28] → cum[09-29] → cum[09-30] → …
  하루를 고치면 그 뒤 날들을 차례로 다시 돌려야 하고, 병렬로 돌릴 수 없다
```

- 백필은 "어느 파티션들을 다시 계산하나"를 고르고, 그 파티션에 의존하는 하류 파티션을 위상 순서로 다시 실행하는 일이다.
- Beauchemin은 같은 테이블의 이전 파티션에 의존하는 "past dependencies"를 피하라고 권한다. 3년치 일별 스냅샷이면 그래프 깊이가 천을 넘고, 몇 달 전을 고치면 수백 파티션을 병렬 없이 다시 돌려야 한다.
- 대량 백필은 운영 DB·클러스터에 부하를 준다. 원천 DB를 직접 읽는 백필은 청크·스로틀·복제 지연 감시로 나눈다([database/34](../../database/34-large-backfill-and-batch-dml/2-summary.md), 스키마 변경 백필은 [database/26 §6](../../database/26-schema-migration/2-summary.md)).

### 3. 시점별 규칙 — 과거는 그때의 규칙으로

```text
  fee_rate (유효 기간 파라미터 테이블)
  valid_from   valid_to     rate
  2000-01-01   2026-10-01   0.030
  2026-10-01   9999-12-31   0.025   ← 10월부터 인하

  09-30 주문 ──join──> 0.030     10-01 주문 ──join──> 0.025
  코드에 0.025를 박아 두면 → 9월을 다시 계산할 때 9월에도 0.025가 적용된다
```

- Beauchemin의 세금 예: 2018년부터 적용할 새 규칙을 태스크에 그냥 반영하면, 나중에 다른 이유로 2017년을 백필한 사람이 모르는 채 2017년에 2018년 규칙을 적용한다. 해법은 유효 날짜를 가진 조건부 로직, 가능하면 **유효 기간을 가진 파라미터 테이블**이다.
- 차원도 같다. 과거 사실을 "지금의" 차원 속성으로 다시 계산하면 과거 숫자가 바뀐다. 이력 차원(SCD Type 2)이나 날짜별 차원 스냅샷을 쓴다. Beauchemin은 파티션마다 차원 전체를 스냅샷으로 남기는 방식을 권한다. SCD는 [04번](../04-slowly-changing-dimensions/2-summary.md)의 주제다.

#### 실험 3: 9월 백필 — 시점별 규칙 vs 현재 규칙

```text
== 3. 백필: 09-28 ~ 09-30을 다시 계산 (확정된 9월 수수료 = 3%)
         job          | sept_fee
 effective-dated rule | 90000.00
           job           | sept_fee
 current rule hard-coded | 75000.000
```

- 300건 × 10,000원 × 3% = 90,000이 확정된 값이다. 현재 규칙(2.5%)을 박은 잡으로 백필하자 75,000이 됐다. 잡은 성공했고, 과거 수치가 **조용히 17% 줄었다**.

### 4. 늦게 온 데이터 — 어느 파티션이 더러워졌나

```text
  orders_raw.ingested_at (적재 시각)
  ... 10-02 23:50 [10-02 주문]   ── 10-03 00:10 일괄 실행(last_run_at) ──   10-03 09:00 [10-01 주문 7건] ← 늦게 옴
                                                                         └ 10-01 파티션이 더러워졌다
  다시 계산할 파티션 = SELECT DISTINCT event_date FROM orders_raw WHERE ingested_at > last_run_at
```

- 이벤트 시각 파티션의 결과는 늦게 온 데이터가 있으면 이미 계산한 날도 바뀌어야 한다. 이벤트 시각과 적재 시각을 둘 다 남겨야 "어느 날이 바뀌었나"를 알 수 있다([06번](../06-event-data-modeling/2-summary.md)).
- Beauchemin은 늦게 오는 사실이 있으면 적재 파티션을 **처리(수신) 시각**으로 나누라고 권한다. 원본 블록을 늦지 않게 불변으로 쌓을 수 있고, "2월 매출, 3월 1일 기준"처럼 시점별 숫자를 볼 수 있다. 대가는 이벤트 시각 조건의 질의가 파티션 가지치기를 못 한다는 것이다.

#### 실험 4: 10-01 주문 7건이 10-03 09:00에 도착

```text
    src    | orders_1001
 raw       |         107
 daily_fee |         100
 dirty_partition
 2026-10-01
            src            | orders |    fee
 daily_fee after recompute |    107 | 26750.000
== 5. 대조 검사: 원천과 결과의 파티션별 건수
 event_date | raw_orders | mart_orders | diff
 2026-09-28 |        100 |         100 |    0
 2026-09-29 |        100 |         100 |    0
 2026-09-30 |        100 |         100 |    0
 2026-10-01 |        107 |         107 |    0
 2026-10-02 |        100 |         100 |    0
```

- 늦은 7건이 들어온 뒤에도 마트는 100건이었다. 다음 일괄 실행은 10-03 파티션만 계산하므로, 이대로 두면 10-01은 **영구히 7건 모자란다**.
- `ingested_at > last_run_at`으로 더러운 파티션(10-01)을 찾아 덮어쓰자 107건·26,750원으로 맞았다. 덮어쓰기 잡이라 이 재계산도 몇 번 돌려도 안전하다.

## 쓰이는 자료구조·알고리즘

- **파티션 DAG + 위상 정렬** — 백필할 파티션과 하류를 의존 순서로 실행한다. DFS로 위상 순서를 구한다. [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · 그래프 표현은 [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **집합(더러운 파티션 목록)** — `SELECT DISTINCT event_date … WHERE ingested_at > last_run_at`은 "바뀐 키의 집합"을 만든다. 의존 그래프에서 그 집합으로부터 도달 가능한 하류가 재계산 범위다.
- **구간 조인** — 유효 기간 파라미터 테이블을 `valid_from <= d < valid_to`로 붙인다. 구간이 겹치면 행이 2배가 된다(겹침 검사는 [04번](../04-slowly-changing-dimensions/2-summary.md)).
- **keyset 청크** — 원천 DB에서 큰 백필을 읽을 때 마지막 키 다음부터 나눠 읽는다. [database/34 §3](../../database/34-large-backfill-and-batch-dml/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 잡을 순수 태스크로 바꾸는 점검표

- [ ] 출력이 파티션 하나인가? 그 파티션을 통째로 덮어쓰나(append·UPDATE가 아닌가)?
- [ ] 지우기와 쓰기가 한 트랜잭션(또는 원자적 교체)인가?
- [ ] 입력이 불변 적재 영역인가? 원본을 고치는 잡은 없나?
- [ ] `now()`·난수·"최신 차원"을 쓰지 않나? 실행 날짜는 파라미터(`ds`)로만 받나?
- [ ] 바뀌는 규칙(요율·환율·분류)은 유효 기간을 가진 테이블에서 조인하나?
- [ ] 같은 테이블의 이전 파티션에 의존하나(과거 의존)? 그렇다면 정말 필요한가?

### 2. 덮어쓰기 잡의 모양 (PostgreSQL 17)

```sql
CREATE FUNCTION job_daily_fee(p date) RETURNS void LANGUAGE sql AS $$
  DELETE FROM daily_fee WHERE ds = p;
  INSERT INTO daily_fee
  SELECT p, count(*), sum(o.amount * r.rate)
  FROM orders_raw o
  JOIN fee_rate r ON o.event_date >= r.valid_from AND o.event_date < r.valid_to
  WHERE o.event_date = p $$;
-- 하나의 SELECT 문 = 하나의 트랜잭션. 재시도·백필 모두 같은 호출
SELECT job_daily_fee('2026-10-01');
```

### 3. 백필과 늦은 데이터 재계산 (Java 21 + JDBC 골격)

```java
// 실행하지 않은 골격: 더러운 파티션을 찾아 날짜 순서로 덮어쓴다. 파티션마다 한 트랜잭션
List<LocalDate> dirty = new ArrayList<>();
try (var ps = conn.prepareStatement(
        "SELECT DISTINCT event_date FROM orders_raw WHERE ingested_at > ? ORDER BY 1")) {
    ps.setObject(1, lastRunAt);
    try (var rs = ps.executeQuery()) { while (rs.next()) dirty.add(rs.getObject(1, LocalDate.class)); }
}
for (LocalDate ds : dirty) {
    try (var call = conn.prepareStatement("SELECT job_daily_fee(?)")) {
        call.setObject(1, ds);
        call.execute();                         // 자동 커밋이면 이 문장 하나가 한 트랜잭션
    }
}
// 하류(월 집계 등)는 dirty에서 도달 가능한 파티션을 위상 순서로 이어서 실행한다
```

- `last_run_at`은 실행이 **시작될 때** 읽은 적재 시각 상한으로 기록한다. 끝난 시각으로 기록하면 실행 중에 들어온 행을 다음에도 못 잡을 수 있다(해석).
- 시작 시각도 완전하지 않다. `ingested_at DEFAULT now()`는 쓰기 트랜잭션의 **시작** 시각이다. 실행 시작 전에 시작해 탐색 뒤에 커밋한 행은 이번 실행에 안 보이고, 다음 실행의 `ingested_at > last_run_at`에도 걸리지 않는다. 판정 재실험(쓰기 트랜잭션 3초, 그 사이 잡 실행)에서 두 실행 모두 그 행을 0건으로 놓쳤다. 탐색 범위를 가장 긴 적재 트랜잭션보다 넉넉히 겹쳐 다시 읽거나(덮어쓰기라 겹쳐 읽어도 안전하다), 커밋 순서를 따르는 위치(CDC의 LSN 등, [05번](../05-change-data-capture/2-summary.md))를 쓰고, 원천 대조를 함께 둔다.

### 4. 진단 쿼리

```sql
-- 파티션 안 중복 행: append 재실행의 흔적
SELECT ds, count(*) FROM daily_fee GROUP BY ds HAVING count(*) > 1;
-- 원천 대조: 파티션별 건수 차이. 양쪽을 따로 집계한 뒤 붙인다
-- (원천 행에 마트 행을 바로 조인하면 마트 중복 행 수만큼 원천 건수가 부풀고, 마트에만 있는 날짜는 안 보인다)
WITH r AS (SELECT event_date AS ds, count(*) AS raw_orders FROM orders_raw GROUP BY 1),
     m AS (SELECT ds, sum(orders) AS mart_orders, count(*) AS mart_rows FROM daily_fee GROUP BY 1)
SELECT ds, raw_orders, mart_orders, mart_rows
FROM r FULL OUTER JOIN m USING (ds)
WHERE raw_orders IS DISTINCT FROM mart_orders OR mart_rows > 1;
-- 확정 기간이 바뀌었나: 백필 전 스냅샷과 비교
SELECT ds, a.fee AS before, b.fee AS after FROM fee_before_backfill a JOIN daily_fee b USING (ds)
WHERE a.fee IS DISTINCT FROM b.fee;
```

- 백필 전에 대상 기간 출력을 복사해 두고, 백필 후 바뀐 파티션 목록을 사람이 확인한다. "바뀌어야 할 파티션만 바뀌었나"가 백필의 완료 조건이다.

## 장애 시나리오와 대처

### 1. append 방식 잡을 다시 돌린다 → 행이 2배가 된다 (⚠)

- **현상**: 스케줄러 재시도가 있던 날, 일 매출·주문 수가 정확히 2배(또는 재시도 횟수 배)다.
- **보이는 형태**: 같은 `ds`에 행이 여러 개. 실험 1: 1행 → 2행, 25,000 → 50,000. 잡 상태는 성공.
- **원인**: 출력이 `INSERT`(append)라 재실행마다 결과가 쌓인다.
- **대처**: 파티션 덮어쓰기(DELETE + INSERT 한 트랜잭션, 또는 원자적 교체)로 바꾼다. 이미 쌓인 중복은 해당 파티션을 다시 계산해 덮는다.

### 2. 백필이 현재 규칙으로 과거를 계산한다 → 확정된 과거 수치가 바뀐다 (⚠)

- **현상**: 재무가 마감한 9월 수수료가 리포트에서 바뀌었다. 그 사이 9월을 백필한 사람은 수수료와 무관한 이유로 돌렸다.
- **보이는 형태**: 백필 기간의 지표가 일정 비율로 움직인다. 실험 3: 90,000 → 75,000(−17%).
- **원인**: 규칙(요율)이 코드 상수거나 "현재" 차원 값으로 조인됐다. 과거를 다시 계산하면 오늘 규칙이 과거에 적용된다.
- **대처**: 유효 기간 파라미터 테이블·이력 차원으로 바꾼다. 마감된 기간은 백필 전후 비교를 필수 단계로 둔다. 규칙을 소급 적용하는 것이 의도라면 그 결정을 기록하고 공지한다.

### 3. 대량 백필 → 운영 DB·클러스터 지연 (⚠)

- **현상**: 1년치 백필을 시작하자 운영 API의 p99가 오르고 복제 지연이 생긴다. 같은 클러스터의 정규 잡이 밀린다.
- **보이는 형태**: 원천 DB의 CPU·I/O 상승, `replay_lag`·`Seconds_Behind_Source` 증가, 스케줄러 대기열 증가.
- **원인**: 백필이 원천 DB를 직접 대량으로 읽거나, 수백 파티션을 동시에 띄웠다. 과거 의존이 있으면 순차 실행이라 오래 붙잡는다.
- **대처**: 원천은 복제본·적재 영역에서 읽는다. 동시 실행 파티션 수를 제한하고 지표를 보며 쉰다([database/34](../../database/34-large-backfill-and-batch-dml/2-summary.md)). 백필 전용 자원 풀을 둔다.

### 4. 늦게 온 이벤트가 속한 파티션을 재계산하지 않는다 → 영구 누락 (⚠)

- **현상**: 어제 매출이 원천보다 조금 적고, 일주일이 지나도 맞춰지지 않는다.
- **보이는 형태**: 원천과 마트의 파티션별 건수 차이가 과거 날짜에 남는다. 실험 4: 10-01 원천 107 vs 마트 100.
- **원인**: 잡이 "오늘 파티션"만 계산한다. 늦게 들어온 행의 이벤트 날짜 파티션은 다시 돌지 않는다.
- **대처**: `ingested_at > last_run_at`으로 더러운 파티션을 찾아 재계산한다. 또는 최근 N일(늦음 분포의 99.9 백분위 기준)을 매일 다시 덮어쓴다. 원천 대조 검사를 붙인다.

### 5. 지우기와 쓰기를 따로 커밋한다 → 대시보드가 잠깐 0을 본다

- **현상**: 매일 새벽 몇 분 동안 대시보드의 어제 매출이 0이나 빈칸이다. 그때 내려받은 리포트가 메일로 나갔다.
- **보이는 형태**: 잡 실행 시각과 겹치는 짧은 공백. 실험 2(6b): 덮어쓰는 중 읽기 0건.
- **원인**: DELETE와 INSERT가 각각 자동 커밋됐다. 중간에 INSERT가 실패하면 파티션이 빈 채로 남는다.
- **대처**: 한 트랜잭션으로 묶는다(실험 2 6a: 읽는 쪽은 옛 값 100을 봤다). 대용량이면 새 테이블·파티션을 만들어 원자적으로 교체한다.

## 핵심 문장

- 배치 잡은 재시도·백필로 다시 돈다. 출력 파티션을 통째로 덮어쓰면 몇 번 돌려도 결과가 같다(같은 파티션을 동시에 돌리지 않는다면).
- append 잡은 재실행마다 결과가 쌓여, 잡은 성공인데 합계가 2배가 된다.
- 덮어쓰기는 지우기와 쓰기를 한 트랜잭션이나 원자적 교체로 해야 읽는 쪽이 빈 파티션을 보지 않는다.
- 백필은 "다시 계산할 파티션을 고르는 일"이다. 과거는 그때 유효했던 규칙으로 계산해야 확정된 숫자가 바뀌지 않는다.
- 늦게 온 데이터는 그것이 속한 과거 파티션을 더럽힌다. 적재 시각으로 더러운 파티션을 찾아 다시 덮어써야 영구 누락이 없다.

## 관련 주제·근거

- 선행
  - [07-batch-stream-architectures](../07-batch-stream-architectures/2-summary.md) — 재처리와 출력 전환
  - [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) — 요청 수준 멱등
- 후속·연결
  - [06-event-data-modeling](../06-event-data-modeling/2-summary.md) — 이벤트 시각과 적재 시각
  - [database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md) — 청크·스로틀·재시작·전후 검증
  - [database/26-schema-migration](../../database/26-schema-migration/2-summary.md) — 스키마 변경과 함께 하는 백필
  - [database/16-mvcc](../../database/16-mvcc/2-summary.md) — 덮어쓰는 동안 읽는 쪽이 옛 버전을 보는 이유
  - [04 SCD](../04-slowly-changing-dimensions/2-summary.md), [10 품질 검사](../10-data-quality-and-data-observability/2-summary.md), [11 계보](../11-data-lineage/2-summary.md)(영향 범위), [14 테이블 포맷](../14-lakehouse-table-formats/2-summary.md)(스냅샷 교체)
  - [distributed/30](../../distributed/30-batch-and-stream-processing/2-summary.md)(비결정적 함수와 재실행), [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)(위상 정렬)
- 글
  - Beauchemin, "Functional Data Engineering — a modern paradigm for batch data processing", Medium, 2018-01-08 — pure task(결정적·멱등·덮어쓰기), 파티션을 불변 객체로, 불변 적재 영역, 시점별 규칙·파라미터 테이블, 차원 스냅샷, 파티션 DAG, past dependencies, late arriving facts(처리 시각 파티션). 원 페이지가 차단돼 Internet Archive 2024 사본으로 읽었다 <https://maximebeauchemin.medium.com/functional-data-engineering-a-modern-paradigm-for-batch-data-processing-2327ec32c42a>
  - DDIA 1판 10장 "Batch Processing" — 절 "The Output of Batch Workflows"(O'Reilly 목차, Internet Archive 2024 사본으로 확인)
- 실험 목록(scratchpad `de/05/exp08/`, 전용 컨테이너 `sn-de-w05-pg8` `--network none`, PostgreSQL 17.11, 2026-10-07)
  - 1 `p.sql` §1·2 — append 재실행 vs DELETE+INSERT 덮어쓰기
  - 2 `q.sh` — 덮어쓰는 중 다른 세션의 읽기: 한 트랜잭션(100) vs 따로 커밋(0)
  - 3 `p.sql` §3 — 9월 백필: 유효 기간 요율 90,000 vs 현재 요율 75,000
  - 4 `p.sql` §4·5 — 늦게 온 7건, 더러운 파티션 탐지와 재계산, 원천 대조(이 실험의 5절은 원천 행에 마트를 바로 조인한 옛 쿼리로 셌다. 마트에 중복이 없어 결과는 같다)
  - 판정 재실험 `de/adj-05/exp/run.sh`(전용 컨테이너 `sn-de-a05-pg`, PostgreSQL 17.11) — 같은 `ds` 동시 덮어쓰기 2행·200건, 옛 대조 쿼리가 중복 2행에서 원천을 200건으로 셈 vs 따로 집계 FULL OUTER JOIN(100 vs 200, 2행), 시작 시각 `last_run_at`이 늦게 커밋된 행을 두 실행 모두 놓침
