# systems/clickhouse-mergetree — 정리 (힌트)

> 복습은 [1-question.md](1-question.md)에서 시작하고, 막힐 때만 이 파일을 힌트로 연다.\
> 원고 출처: 개인 학습 노트 「ClickHouse MergeTree 기초」 · 이관일 2026-09-16.\
> 본문 절들(대응 관계·Too many parts·모니터링·async_insert·두 개의 키·변형 엔진)은 **원고**를 고쳐 쓴 것이다(문체·순서·SQL 유지).\
> 원고가 특정인의 "세그먼트 엔진 실측 경험"에 기댄 문장은 **일반 조건문**("세그먼트 기반 엔진을 다뤄 봤다면")으로 옮겼다.\
> 「한눈에」의 영수증 상자 비유는 **Claude가 원고 이해를 돕기 위해 새로 그린 것**이며, 원고에 없던 지식은 맨 끝 `[Claude 추가]`에만 둔다.

**MergeTree** = INSERT 한 번이 **불변 파일(파트) 하나**를 만들고, 백그라운드가 그것들을 병합하는 저장 엔진.\
구조가 Lucene 세그먼트와 같아서, **세그먼트 기반 검색 엔진을 다뤄 봤다면 학습 비용 대비 효과가 가장 크다.**

> **파트(part)** — ClickHouse MergeTree가 INSERT마다 만드는 불변 데이터 파일 단위. 병합의 대상이다.\
> 예: 행 1개짜리 INSERT를 1000번 하면 파트가 1000개 생긴다. 이게 모든 문제의 출발점이다.

---

## 한눈에 — 쉽게 말하면

**저장할 때마다 새 상자를 하나씩 만드는 창고**를 떠올리면 된다. *(Claude 보강 — 원고에 없는 비유)*

```text
영수증을 저장할 때마다 새 상자를 하나 만든다
+-------------------------------------------+
| 한 번에 영수증 1장씩 1000번 저장            |  ← INSERT 1회 = 파트 1개
|   → 상자 1000개                            |
| 창고 직원이 상자를 합쳐 큰 상자로 정리        |  ← 백그라운드 병합(merge)
| 그런데 저장이 정리보다 빠르면 상자가 쌓인다    |  ← "Too many parts" = 백프레셔
+-------------------------------------------+
```

**MergeTree도 똑같은 구조다.** INSERT 한 번이 불변 파트 하나를 만들고, 백그라운드 스레드가 그 파트들을 병합해 수를 줄인다. 저장(INSERT)이 정리(병합)보다 빠르면 파트가 쌓여 결국 INSERT를 막는다.

쉽게 말하면 이렇다.\
**"조금씩 자주 저장"이 이 엔진의 최대 적이다.** 그래서 실무 설계의 절반은 "파트를 어떻게 안 폭증시키나"(배치·async_insert·성긴 파티션)이고, 나머지 절반은 "쿼리가 어느 파트·어느 블록만 읽게 하나"(ORDER BY·PARTITION BY 키)다.

---

## 문제 — 이 개념이 답하려는 질문

이 주제에는 풀어야 할 코드 과제가 없다(운영·설계 개념 정리다). 대신 네 개의 질문에 답한다.

```text
1. 왜 파트가 폭증하나  "Too many parts는 디스크가 찬 게 아니다 — 무엇의 신호인가?"
2. 어떻게 안 폭증시키나 "배치·async_insert·파티션 성기게 — 각각 무엇을 막나?"
3. 쿼리 비용은 누가 정하나 "ORDER BY / PARTITION BY 두 키가 무엇을 결정하나?"
4. 무엇을 모니터링하나   "파트 수·병합 처리량·복제 지연을 어디서 보나?"
```

아래 서머리는 이 네 질문을 하나씩 분석·정리한 것이다.

---

## 전체 흐름

INSERT 한 건이 파트가 되고, 병합되고, 조회에서 프루닝되는 경로다.

```text
INSERT 1회
   ↓
파트 1개 생성            불변 · 그 안은 ORDER BY 키로 정렬
   ↓ 여러 개 쌓이면
백그라운드 병합           같은 파티션 안에서만 합쳐진다
   ↓ 병합 < 인서트 속도면
"Too many parts"        백프레셔 — 인서트를 지연시키거나 막는다
   ↓ (조회 시)
파티션 프루닝 → 그래뉼 스킵  PARTITION BY 로 파티션을 거르고 ORDER BY 접두사로 블록을 건너뛴다
```

- 핵심 한 문장: **병합은 파티션 경계를 넘지 않는다.** 그래서 파티션을 잘게 쪼개면 파트가 곱하기로 늘어난다.

---

## 대응 관계부터 잡기 — 세그먼트 경험의 이식

> 출처: 개인 학습 노트 「MergeTree 기초」 — §1

**언제 쓰나** — 세그먼트 기반 검색 엔진(Lucene 계열)을 다뤄 봤을 때. 개념이 1:1로 대응돼 학습 비용이 확 준다.

```text
Lucene 계열 엔진        ClickHouse            공통 성질
──────────────────────────────────────────────────────────
세그먼트(segment)        파트(part)            불변 · 백그라운드 병합 대상
refresh로 세그먼트 생성    INSERT 1회 = 파트 1개   소량 잦은 쓰기 = 파일 폭증
세그먼트 병합            파트 병합(merge)        I/O·CPU를 조회와 나눠 씀
수동 강제 병합           OPTIMIZE TABLE         수동 병합 · 남발 금지
삭제 = tombstone        삭제 = mutation(재작성)  제자리 수정 없음
```

**가장 중요한 한 문장**: `INSERT` 한 번이 **파트 하나**를 만든다. 행 1개짜리 INSERT를 1000번 하면 파트가 1000개 생긴다.

**비용** — 이 대응이 성립하기 때문에, 세그먼트 병합에서 겪은 함정(잦은 refresh·과도한 force merge)이 그대로 재현된다. 새 지식이 아니라 이식된 지식이다.

---

## 파트 증식과 "Too many parts"

> 출처: 개인 학습 노트 「MergeTree 기초」 — §2

**언제 쓰나** — 다음 예외를 만났을 때. 디스크 문제로 오해하기 쉬운 자리다.

```text
DB::Exception: Too many parts (N).
Merges are processing significantly slower than inserts.
```

이건 디스크가 꽉 찬 게 아니라 **인서트 속도가 병합 속도를 앞질렀다는 백프레셔 신호**다.

> **백프레셔(backpressure)** — 하류(병합)가 못 따라올 때 상류(인서트)를 일부러 늦추거나 막아 시스템을 지키는 것.\
> 예: 병합이 밀리면 먼저 인서트를 인위적으로 지연시키고(1차 경고), 더 밀리면 예외를 던져 막는다(2차 차단).

### 관련 설정 (버전별 기본값이 다르므로 실제 값은 서버에서 확인)

```text
설정                      의미
────────────────────────────────────────────────────
parts_to_delay_insert     이 수를 넘으면 인서트를 인위적으로 지연 (1차 경고)
parts_to_throw_insert     이 수를 넘으면 예외 발생 (2차 차단)
max_parts_in_total        테이블 전체 파트 수 상한
background_pool_size      병합에 쓸 스레드 수
```

```sql
SELECT name, value FROM system.merge_tree_settings
WHERE name LIKE '%parts_to%';
```

### 원인 3가지와 처방

```text
원인                        처방
─────────────────────────────────────────────────────────────
소량 인서트가 너무 잦음        배치로 묶기(수만 행 단위) 또는 async_insert
파티션이 너무 잘게 쪼개짐       파티션 키를 성기게(일 단위 → 월 단위)
                            ※ 병합은 파티션 내부에서만 일어난다
병합 처리량 부족             디스크/CPU 증설, background_pool_size 조정
```

> **가장 흔한 진짜 원인은 과도한 파티셔닝이다.** 파티션 수 × 파트 수로 곱해지기 때문. 파티션 개수는 보통 수백~수천 이하를 목표로 잡는다.

**비용** — 파티션을 성기게 잡으면 파트 폭증은 막지만, 그만큼 `DROP PARTITION`으로 지울 수 있는 단위가 커진다(아래 PARTITION BY 절과 맞교환).

---

## 모니터링 쿼리 — 실측 습관

> 출처: 개인 학습 노트 「MergeTree 기초」 — §3

**언제 쓰나** — 파트 수·병합·복제를 눈으로 확인할 때. 시스템 테이블을 직접 본다.

```sql
-- 테이블별 파트 수 / 크기 (active 파트만)
SELECT database, table,
       count() AS parts,
       sum(rows) AS rows,
       formatReadableSize(sum(bytes_on_disk)) AS size
FROM system.parts
WHERE active
GROUP BY database, table
ORDER BY parts DESC;

-- 파티션별 파트 수 (과도한 파티셔닝 탐지)
SELECT table, partition, count() AS parts
FROM system.parts WHERE active
GROUP BY table, partition
ORDER BY parts DESC LIMIT 20;

-- 지금 돌고 있는 병합
SELECT table, elapsed, progress, num_parts,
       formatReadableSize(total_size_bytes_compressed) AS size,
       formatReadableSize(memory_usage) AS mem
FROM system.merges;

-- 병합 이력 (사후 분석용, part_log 활성화 필요)
SELECT event_time, table, event_type, rows, duration_ms
FROM system.part_log
WHERE event_type = 'MergeParts'
ORDER BY event_time DESC LIMIT 50;

-- 복제 지연 / 큐 적체 (ReplicatedMergeTree)
SELECT database, table, absolute_delay, queue_size, inserts_in_queue, merges_in_queue
FROM system.replicas;
```

> **함정**: `system.parts`의 `active` 컬럼을 주의한다. 병합 후에도 옛 파트 행이 한동안 남아 있어서, `WHERE active`를 빼먹으면 파트 수가 부풀려 보인다.

**비용** — 없다(조회 전용). 다만 `part_log`는 활성화돼 있어야 이력이 남는다.

---

## 소량 인서트 대책 — async_insert

> 출처: 개인 학습 노트 「MergeTree 기초」 — §4

**언제 쓰나** — 애플리케이션에서 배치를 못 묶는 상황(여러 인스턴스가 각자 소량 전송). 표준 해법은 **서버 쪽에서 버퍼링해 묶는 것**이다.

```sql
SET async_insert = 1;
SET wait_for_async_insert = 1;   -- 버퍼 플러시까지 대기 (내구성↑, 레이턴시↑)
-- SET wait_for_async_insert = 0; -- 즉시 반환 (처리량↑, 유실 창 존재)
SET async_insert_max_data_size = 10000000;  -- 버퍼 크기
SET async_insert_busy_timeout_ms = 1000;    -- 최대 대기 시간
```

**전/후 대비 — wait_for_async_insert 의 두 값**

```text
wait_for_async_insert = 1            wait_for_async_insert = 0
+---------------------------+        +---------------------------+
| 버퍼 플러시까지 기다림       |        | 버퍼에 넣자마자 성공 응답    |
| 내구성 높음                |        | 처리량 높음                |
| 레이턴시 높음              |        | 서버가 죽으면 유실 창 존재   |
+---------------------------+        +---------------------------+
  → 잃으면 안 되는 데이터            → 유실을 감수하고 처리량을 산다
```

> **트레이드오프가 핵심**: `wait_for_async_insert = 0`이면 클라이언트가 성공 응답을 받은 뒤 서버가 죽으면 **유실된다.** 이건 메시징 신뢰성에서 반복되는 "유실 창"과 정확히 같은 구조의 선택이다. *(원고의 사내 문서 참조 「06번 아웃박스 vs 발송 로그」는 아직 이관 전이라 링크 대신 텍스트로 둔다.)*

대안: `Buffer` 테이블 엔진(메모리 버퍼 → 주기적 플러시. 서버 크래시 시 유실).

**비용** — 서버 버퍼링은 잦은 인서트를 묶어 파트 폭증을 막지만, 플러시 전 구간이 유실 창이 된다(내구성 vs 처리량).

---

## 쿼리 비용을 결정하는 두 개의 키

> 출처: 개인 학습 노트 「MergeTree 기초」 — §5

**언제 쓰나** — 테이블을 설계할 때. **이게 MergeTree 설계의 90%다.**

```sql
CREATE TABLE events (
    ts        DateTime,
    tenant_id UInt32,
    metric    LowCardinality(String),
    value     Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)          -- 파티션 키
ORDER BY (tenant_id, metric, ts)   -- 정렬 키 (= 기본 키)
TTL ts + INTERVAL 90 DAY;
```

### ORDER BY (정렬 키)

- 파트 내부의 **물리적 정렬 순서**이자 **희소 인덱스**의 기준이다.
- 행 단위 인덱스가 아니라 `index_granularity`(기본 8192행)마다 마크 하나만 저장한다 → 인덱스가 작아 메모리에 상주한다.
- **원칙**: 카디널리티 낮은 컬럼 → 높은 컬럼 순. 그리고 **거의 모든 쿼리에 들어가는 필터 컬럼을 맨 앞에.**
- 정렬 키 **접두사(prefix)**로 필터링해야 그래뉼 스킵이 먹는다. 위 예시에서 `tenant_id` 조건 없이 `WHERE metric = 'x'`만 있으면 스킵이 잘 안 된다.
- 압축률에도 직결된다 — 비슷한 값이 인접하면 압축이 훨씬 잘 된다.

> **희소 인덱스(sparse primary index)** — 모든 행이 아니라 일정 행 간격마다 한 개의 마크만 저장하는 색인.\
> 예: 8192행마다 마크 하나면, 인덱스가 작아 메모리에 다 올라가고, 마크 단위(그래뉼)로 읽을 블록을 건너뛴다.

### PARTITION BY (파티션 키)

- 목적은 인덱싱이 **아니다.** 목적은 (1) 파티션 프루닝 (2) `DROP PARTITION`·TTL로 대량 삭제를 O(1)로 만들기다.
- **병합은 파티션 경계를 넘지 않는다** → 파티션을 잘게 쪼개면 파트가 곱하기로 늘어난다.
- 실무 기본값: **월 단위(`toYYYYMM`)**. 일 단위는 보관 기간이 짧고 일 단위 삭제가 필수일 때만.

### 확인 방법

```sql
EXPLAIN indexes = 1
SELECT ... FROM events WHERE ...;
-- 읽은 파트 수 / 그래뉼 수를 보고 프루닝이 먹었는지 확인
```

**비용** — 정렬 키를 잘못 잡으면(자주 쓰는 필터가 접두사에 없으면) 그래뉼 스킵이 안 먹어 전체 스캔이 된다. 이건 나중에 바꾸기 비싼 결정이다.

---

## 알아두면 좋은 변형 엔진

> 출처: 개인 학습 노트 「MergeTree 기초」 — §6

**언제 쓰나** — 최신 버전만·합산·사전집계·복제가 필요할 때. 이름에 함정이 있다.

```text
엔진                     용도                        함정
──────────────────────────────────────────────────────────────────
ReplacingMergeTree       최신 버전만 남기는 upsert 흉내   병합 시점에만 중복 제거 →
                                                     조회 시 FINAL 또는 집계로 보정
SummingMergeTree         같은 키 숫자 컬럼 합산         위와 동일 · 즉시 반영 아님
AggregatingMergeTree     사전 집계 상태 저장            롤업 설계의 표준 구현체
                         (*State / *Merge)            (형제 노트 timeseries-tiers)
ReplicatedMergeTree      코디네이터 기반 복제           병합 fetch 설정은 형제 노트
                                                     lsm-merge-model 참고
```

> **가장 흔한 사고**: `ReplacingMergeTree`를 "중복 없는 테이블"로 오해하는 것. **최종적 일관성**이지 즉시 유일성 보장이 아니다 — 병합이 아직 안 돈 구간에는 중복이 그대로 보인다.

**비용** — 이 엔진들의 "정리"는 전부 병합 시점에 일어난다. 즉시 정확한 결과가 필요하면 조회에서 `FINAL`·집계로 보정해야 하고, 그건 조회 비용을 올린다.

---

## 한 문단 요약 (면접용)

> MergeTree는 INSERT마다 불변 파트를 만들고 백그라운드로 병합한다. 구조가 Lucene 세그먼트와 같아서, 소량 잦은 인서트가 파트를 폭증시켜 "Too many parts"로 인서트를 막는 백프레셔가 걸린다. 그래서 배치 인서트나 async_insert로 묶고, 파티션 키는 병합이 파티션을 넘지 않는다는 점 때문에 성기게 잡는다. 쿼리 비용은 ORDER BY 키가 결정하는데, 희소 인덱스라 정렬 키 접두사로 필터링해야 그래뉼 스킵이 먹는다. 운영에서는 system.parts로 파티션별 파트 수를, system.merges와 part_log로 병합 처리량을 본다.

---

## 핵심 문장

- **INSERT 한 번 = 파트 하나 — "조금씩 자주 저장"이 이 엔진의 최대 적이다.**
- **"Too many parts"는 디스크가 찬 게 아니라 인서트가 병합을 앞질렀다는 백프레셔다.**
- **병합은 파티션 경계를 넘지 않는다 — 과도한 파티셔닝이 파트 폭증의 가장 흔한 진짜 원인이다.**
- **쿼리 비용은 ORDER BY 접두사가 정한다 — 자주 쓰는 필터가 맨 앞에 없으면 그래뉼 스킵이 안 먹는다.**
- **Replacing/Summing/Aggregating의 "정리"는 병합 시점에만 일어난다 — 즉시 정확이 필요하면 조회에서 보정해야 한다.**

---

## 관련 자료

- 형제 주제 `lsm-merge-model`(이 배치에서 함께 이관) — 파트·세그먼트의 병합 비용과 "누가 병합하나"의 원리. 이 노트의 밑바탕이다. *(이관 후 data-structure/ 하위 — 지금은 텍스트 참조)*
- 형제 주제 `timeseries-tiers`(이 배치에서 함께 이관) — `AggregatingMergeTree`가 롤업 설계에서 어떻게 쓰이는지. *(이관 후 systems/ 하위 — 지금은 텍스트 참조)*
- 메시징의 "유실 창"과 같은 구조인 사내 문서 「아웃박스 vs 발송 로그」는 아직 이관 전이라 링크 대신 텍스트로 둔다.

---

## 용어 풀이

- **MergeTree** — INSERT마다 불변 파트를 만들고 백그라운드로 병합하는 ClickHouse 저장 엔진 계열.
- **파트(part)** — INSERT마다 생기는 불변 데이터 파일 단위. 병합의 대상.
- **병합(merge)** — 여러 파트를 하나로 합쳐 수를 줄이는 백그라운드 작업. 파티션 경계를 넘지 않는다.
- **Too many parts** — 인서트가 병합을 앞질러 파트가 상한을 넘었을 때 나는 백프레셔 예외.
- **백프레셔(backpressure)** — 하류가 못 따라올 때 상류를 늦추거나 막아 시스템을 지키는 것.
- **async_insert** — 서버가 소량 인서트를 버퍼링해 묶어 파트 폭증을 막는 기능.
- **희소 인덱스(sparse primary index)** — 일정 행 간격마다 마크 하나만 저장하는 색인. 그래뉼 단위 스킵의 근거.
- **그래뉼(granule)** — `index_granularity`(기본 8192행) 단위의 읽기 블록. 스킵의 최소 단위.
- **파티션 프루닝(partition pruning)** — 쿼리 조건으로 읽을 파티션을 미리 걸러내는 것.
- **TTL(Time To Live)** — 데이터의 보관 기간. 지나면 파티션 단위로 싸게 지운다.
- **mutation** — ClickHouse에서 UPDATE·DELETE를 파트 재작성으로 처리하는 무거운 연산.
- **최종적 일관성(eventual consistency)** — 지금은 중복·불일치가 있어도 병합 후 결국 정리되는 상태.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **"기본 키 = 정렬 키"라는 오해.** ClickHouse의 PRIMARY KEY는 유일성 제약이 아니다. 유니크 키가 아니라 "정렬 순서이자 희소 인덱스의 기준"일 뿐이다. 그래서 같은 키가 여러 파트에 중복돼도 막지 않는다 — `ReplacingMergeTree`가 병합 시점에야 정리하는 이유가 이것이다.
- **LowCardinality 는 사전 인코딩이다.** 예시의 `LowCardinality(String)`은 값 종류가 적은 컬럼(metric 이름 등)을 정수 딕셔너리로 바꿔 저장·비교를 싸게 만든다. 카디널리티가 높은 컬럼(예: user_id)에 붙이면 오히려 사전이 커져 손해다.
- **OPTIMIZE TABLE ... FINAL 남발 금지.** 수동 병합은 쓰기 끝난 과거 파티션에만 제한적으로 쓴다. 활성 테이블에 돌리면 큰 파트를 강제로 다시 써서 I/O를 폭발시키고, 끝나도 새 인서트가 다시 파트를 만든다 — 밑 빠진 독이다.
- **materialized view = 삽입 트리거.** 롤업에 쓰는 MV는 "뷰"라는 이름과 달리, 원본에 INSERT가 들어올 때마다 집계 상태를 계산해 대상 테이블에 쓰는 삽입 시점 트리거에 가깝다. 그래서 MV를 만든 뒤 들어온 데이터만 반영되고, 과거 데이터는 별도로 채워 넣어야 한다.
</content>
