# 갭 리서치 — 데이터 아키텍처 · 추적성 · 단계별 타임아웃 (2026-09-28, L0)

---

## 1. 커버 점검표

판정 기준은 세 가지다.
- **이미 있음**: 그 leaf의 요지나 ⚠ 칸이 해당 주제를 직접 다룬다.
- **부분**: 한 줄 언급만 있거나 다른 관점(예: 요청 수준)으로만 다룬다. 괄호 안은 흡수 slug다.
- **없음**: 커리큘럼 어디에도 없다.

### 1.1 데이터 모델링·아키텍처

| 항목 | 판정 | 근거 / 제안 |
|---|---|---|
| 정규화·비정규화 실무 판단 | 이미 있음 (`database/03-normalization`) | 1NF~BCNF와 반정규화 판단이 요지에 있다. 다만 "기록 시스템과 파생 데이터" 관점은 없다 → 신규 `data-engineering/01` |
| 차원 모델링(스타·스노우플레이크) | 없음 | `database/08`은 저장 형식(행 vs 컬럼)만 다룬다 → 신규 `data-engineering/03` |
| SCD(천천히 변하는 차원) | 없음 | → 신규 `data-engineering/04` |
| Data Vault | 없음 | → 신규 `data-engineering/05` (심화) |
| OLTP↔OLAP 분리 | 부분 (`database/08-row-vs-column-storage`, `database/31-distributed-databases`) | 저장 엔진 관점뿐이다. 워크로드와 시스템을 나누는 판단은 없다 → 신규 `data-engineering/02` |
| ETL / ELT | 없음 | → `data-engineering/02`에 포함 |
| CDC(Debezium) | 부분 (`distributed/21-outbox-and-dual-write`) | outbox의 전달 수단으로 한 단어만 나온다. 스냅샷·복제 슬롯·DDL 처리는 없다 → 신규 `data-engineering/06` |
| Lambda·Kappa | 부분 (`distributed/28-batch-and-stream-processing`) | 처리 모델(MapReduce·윈도·워터마크)은 있다. 두 경로를 합치는 아키텍처와 재처리 전략은 없다 → 신규 `data-engineering/07` |
| 레이크하우스(Iceberg·Delta) | 없음 | → 신규 `data-engineering/08` |
| 데이터 메시 | 없음 | → 신규 `data-engineering/15` (심화) |
| 데이터 계약 | 없음 | `testing/08-contract-testing`은 API 소비자 계약이다 → 신규 `data-engineering/10` |
| 스키마 레지스트리 | 부분 (`api-design/09-schema-and-serialization`) | Avro·Protobuf 스키마 진화는 있다. 레지스트리의 호환성 모드와 강제 지점은 없다 → `data-engineering/10`에 포함 |
| 데이터 품질 검사 | 부분 (`data-analysis/23-data-cleaning-and-quality`) | 분석가가 데이터를 받은 뒤 하는 정제다. 파이프라인에서 막는 검사(신선도·볼륨·분포)는 없다 → 신규 `data-engineering/11` |
| 계보(lineage) | 없음 | → 신규 `data-engineering/12` |
| 백필·재처리 | 부분 (`database/34-schema-migration`) | 마이그레이션 백필만 다룬다. 파이프라인 재실행과 과거 구간 재계산은 없다 → 신규 `data-engineering/09` |
| 멱등 파이프라인 | 부분 (`reliability/12-idempotency`) | 요청 단위 멱등 키만 다룬다. 파티션 덮어쓰기식 멱등은 없다 → `data-engineering/09`에 포함 |
| 시계열 데이터 모델 | 이미 있음 (`database/36-timeseries-resolution-tiers`, `data-analysis/24-time-series-basics`) | 추가하지 않는다 |
| 이벤트 데이터 모델 | 부분 (`distributed/27-event-sourcing`, `distributed/28`) | 이벤트 소싱의 재생과 워터마크는 있다. 이벤트 스키마 설계(이벤트 시각·수집 시각·봉투·식별자)는 없다 → 신규 `data-engineering/13` |
| 시간 이력(유효 시간·기록 시간, bitemporal) | 없음 | → 신규 `database/41` |
| 보존·삭제(GDPR vs 불변 로그) | 부분 (`engineering-practice/15-legal-standards`, `database/36`) | 법률 기준과 디스크 보존만 다룬다. 불변 로그·백업·파생 복제본에서 지우는 설계는 없다 → 신규 `data-engineering/14` |

### 1.2 추적성

| 항목 | 판정 | 근거 / 제안 |
|---|---|---|
| 분산 추적(W3C Trace Context) | 이미 있음 (`reliability/25-distributed-tracing`) | 요지와 📚에 있다 |
| OTel span · baggage · span link | 부분 (`reliability/25`) | 비동기 경계에서 컨텍스트가 끊기는 문제는 ⚠에 있다. baggage와 span link는 없다 → **§4 보강 권고**(신규 leaf 아님) |
| 상관 ID | 이미 있음 (`reliability/23-logging`) | |
| 구조화 로그 vs 추적 vs 감사 로그의 역할 구분 | 부분 (`reliability/23`, `reliability/25`, `security/25-security-logging-and-audit`) | 셋이 따로 있고, **"무엇을 어디에 남기나"를 가르는 기준**이 없다 → 신규 `reliability/35` |
| 이벤트 소싱으로 얻는 추적성 | 이미 있음 (`distributed/27-event-sourcing`) | 추가하지 않는다. 신규 추적성 leaf의 선행으로 건다 |
| 데이터 계보 | 없음 | → `data-engineering/12` |
| "왜 이 값이 되었나" 재구성 — 결정 로그 | 없음 | → 신규 `domain-modeling/22` |
| 버전 스탬프(규칙·요율·정책 버전, 적용 시점) | 없음 | `software-design/21-architecture-decision-records`는 설계 결정의 기록이지 런타임 값의 근거가 아니다 → 신규 `domain-modeling/23` |
| 원장(복식부기, append-only 정정) | 없음 | `domain-modeling/11-time-money-and-units`는 금액의 표현만 다룬다 → 신규 `domain-modeling/24` |
| 대사(reconciliation) | 없음 | → 신규 `domain-modeling/25` |
| 감사 로그 변조 탐지 | 이미 있음 (`security/25` — 🔧 해시 체인) | |

### 1.3 타임아웃·시간 예산 설계

| 항목 | 판정 | 근거 / 제안 |
|---|---|---|
| 계층별 타임아웃(connect·TLS·read·write·idle·전체) | 부분 (`network/15`·`21`·`29`·`35`, `reliability/06`) | 각 계층 leaf에 흩어져 있다. **HTTP 클라이언트 하나에 달린 타임아웃 목록과 서로의 포함 관계**는 없다 → 신규 `reliability/36` |
| 데드라인 전파(gRPC deadline) | 이미 있음 (`reliability/06-timeouts-and-deadline-propagation`, `api-design/10-rpc-and-grpc`) | |
| 타임아웃 예산 분배 | 부분 (`reliability/06` — 🔧 "남은 예산 전파") | 전파는 있다. **총 예산을 단계에 나누는 방법**(백분위로 정하기, per-try, 폴백 몫)은 없다 → 신규 `reliability/37` |
| 재시도 예산 | 부분 (`reliability/07-retry-backoff-jitter` — 요지에 "재시도 예산") | 이름만 있다 → §4 보강 권고, 시간 측면은 `reliability/37`에 포함 |
| 헤지 요청(Dean–Barroso) | 이미 있음 (`reliability/17-tail-latency-and-stragglers`) | |
| 취소 전파(context cancellation) | 부분 (`api-design/24-grpc-streaming-modes`의 "취소", `reliability/06`) | 타임아웃이 났을 때 **실제 작업을 멈추는 방법**은 없다 → 신규 `reliability/38` |
| 타임아웃 × 멱등성 결합 | 부분 (`distributed/03`, `reliability/12`, `api-design/05`) | 재시도 쪽은 충분하다. "결과를 모르는 요청을 어떻게 확정하나"는 없다 → `domain-modeling/25`(대사)와 `reliability/37`에 나눠 넣는다 |
| 배치·스케줄 작업의 단계 타임아웃 | 없음 (`reliability/15-scheduler-and-cron-ha`는 중복 실행 방지만 다룬다) | → 신규 `reliability/39` |
| 커넥션 풀 획득 타임아웃 | 이미 있음 (`database/32-connection-pooling`) | HikariCP 메시지까지 ⚠에 있다 |
| DB 서버 측 타임아웃(statement·lock·idle-in-transaction) | 부분 (`database/22` — `Lock wait timeout exceeded`) | → 신규 `database/42` |
| Envoy·Resilience4j 설정 사례 | 없음 | → 신규 `reliability/40` (종합 연습) |

---

## 2. 신규 leaf 제안 (29개)

배치는 네 곳이다. 신설 영역 `data-engineering/` 17개, `database/` 2개, `domain-modeling/` 4개, `reliability/` 6개다.

slug 번호는 network §7.8b 선례를 따른다. 영역의 마지막 번호 뒤에 이어 붙인다. 권장 학습 순서의 재배열은 반영 단계에서 한다.

### 2.1 신설 영역 — 데이터 공학 (`data-engineering/`)

> 흐름은 "원천과 파생 → 분석 저장소와 모델 → 옮기기(CDC·배치·스트림) → 안전하게 다시 돌리기 → 계약·품질·계보 → 보존·삭제 → 조직"이다.
> 이 영역의 "깨지면"은 크래시로 보이지 않는다. **파이프라인은 초록인데 숫자가 틀린** 모양으로 보인다. 그래서 ⚠ 칸에는 가능한 한 "어느 숫자가 어떻게 어긋나 보이나"를 적었다.
> 뼈대 후보는 다음과 같다.
> - DDIA 1판 3장(OLTP vs 분석·스타 스키마), 10장(배치 출력의 철학), 11장(CDC·이벤트 소싱), 12장(파생 데이터·감사 가능성). 12장의 절 제목은 `[?]`.
> - Kimball Group "Dimensional Modeling Techniques"(웹, 확인). 『The Data Warehouse Toolkit』 3판의 장 번호는 `[?]`.
> - Armbrust 외 CIDR 2021 "Lakehouse"(확인).
> - Kreps 2014 "Questioning the Lambda Architecture"(확인).
> - Beauchemin 2018 "Functional Data Engineering"(확인, 연도 `[?]`).
> - Reis–Housley 『Fundamentals of Data Engineering』(2022) `[?]`.

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-system-of-record-and-derived-data | 기록 시스템(원천)과 파생 데이터(캐시·검색 인덱스·집계·읽기 모델)의 구분. 비정규화는 "파생본을 하나 더 두는 결정"이다. 원천이 있어야 파생본을 재구축할 수 있다 | database/03-normalization, distributed/24-queues-logs-and-delivery-semantics | 두 저장소가 서로 원천이라고 주장한다 → 값이 다를 때 어느 쪽이 맞는지 판정할 수 없다. 검색 인덱스를 직접 수정한다 → 재색인하는 순간 수정분이 사라진다. 비정규화 사본의 갱신 경로가 누락된다 → 목록 화면과 상세 화면의 값이 다르다 | 파생 = 원천 로그의 폴드(fold) | DDIA 1판 3부 서론 · 11·12장 [?] | 필수 | 신규 (연결: `domain-modeling/17-cqrs`, `database/38-caching-with-databases`) |
| 02-oltp-olap-and-warehouse | 운영 DB와 분석 저장소를 나누는 이유, 웨어하우스·마트, ETL vs ELT(원본을 먼저 적재한 뒤 변환) | 01, database/08-row-vs-column-storage | 운영 DB에서 분석 쿼리를 돌린다 → 리포트 시간대에 p99가 급등하고 복제 지연이 생긴다. 변환에 실패한 행을 조용히 건너뛴다 → 대시보드 합계가 운영 DB와 다르다. 원본을 남기지 않는 ETL → 변환 버그를 찾아도 재처리할 원본이 없다 | 컬럼 저장·압축, 외부 정렬 | DDIA 1판 3장 "Transaction Processing or Analytics?" | 필수 | 신규 |
| 03-dimensional-modeling | 팩트·차원·**grain(한 행의 뜻) 선언**, 스타 vs 스노우플레이크, 가산·반가산·비가산 지표, 공통 차원(conformed) | 02, database/04-sql-joins-and-aggregation | grain이 섞인 팩트 테이블 → 주문 합계가 2배로 나온다. 차원 키 매칭 실패 + inner join → 팩트 행이 빠져 매출 합계가 줄어든다(에러 없음). 비율 지표를 `SUM` → 의미 없는 숫자 | 스타 조인 = 해시 조인 + 비트맵 | Kimball Group "Dimensional Modeling Techniques" · DDIA 1판 3장 "Stars and Snowflakes" | 필수 | 신규 |
| 04-slowly-changing-dimensions | SCD Type 0~3(+4·6·7), 대리 키와 내구 키, 유효 기간 컬럼 | 03 | Type 1 덮어쓰기 → **과거 리포트 숫자가 소급해서 바뀐다**("지난달 지역별 매출이 달라졌어요"). Type 2의 유효 기간이 겹치거나 빈다 → 기간 조인에서 행이 중복되거나 누락된다. 현재 행 플래그가 둘인 멤버 | 구간 비교(`data-structure/30-interval-tree`) | Kimball Group "Type 2: Add New Row" · Design Tip #152 (Types 0,4,5,6,7) | 필수 | 신규 |
| 05-data-vault | Hub(비즈니스 키)·Link(관계)·Satellite(시점별 속성), 적재 이력 보존형 통합 모델 | 04 | 비즈니스 키 정규화 누락(공백·대소문자) → 같은 고객의 Hub 행이 둘이 된다. Satellite가 폭증한다 → 리포트 쿼리 하나에 조인 수십 개. 모델만 도입하고 마트를 두지 않는다 → 분석가가 쓸 수 없다 | 해시 키(`algorithm/35-hash-functions`) | Linstedt–Olschimke 『Building a Scalable Data Warehouse with Data Vault 2.0』 [?] | 심화 | 신규 |
| 06-change-data-capture | 로그 기반 CDC(WAL·binlog 구독), 초기 스냅샷 + 스트리밍, 증분 스냅샷, 삭제 tombstone, DDL 변경 | 01, database/26-wal-and-logging, distributed/21-outbox-and-dual-write | 커넥터가 멈춘 사이 복제 슬롯이 WAL을 붙잡는다 → PG 디스크가 가득 찬다(`pg_replication_slots`에 inactive 슬롯). binlog 보존 기간이 지난다 → 전체 재스냅샷이 필요하다. 스냅샷과 스트림 경계에서 중복이 생긴다. 삭제 이벤트를 처리하지 않는다 → 하류에 지운 행이 남는다 | append-only 로그 오프셋, 체크포인트 | Debezium 문서 "Features"·PostgreSQL connector · Debezium 블로그 2021-10-07 "Incremental Snapshots" | 필수 | 신규 (흡수: `distributed/21`의 CDC 한 줄) |
| 07-batch-stream-architectures | Lambda(배치 + 속도 계층) vs Kappa(재생 가능한 로그 하나로 스트림 재처리), 재처리 전략 | 06, distributed/28-batch-and-stream-processing, distributed/25-kafka-internals | 배치 경로와 스트림 경로의 결과가 다르다 → 같은 지표가 대시보드마다 다르다. 로그 보존 기간이 재처리 구간보다 짧다 → 과거를 다시 돌릴 수 없다. 재처리 잡이 운영 출력 토픽에 쓴다 → 하류에 이중으로 반영된다 | 세그먼트 로그 재생, 윈도 | Kreps 2014 "Questioning the Lambda Architecture" (O'Reilly Radar) · Marz 2011 "How to beat the CAP theorem" [?] | 권장 | 신규 |
| 08-lakehouse-table-formats | 객체 저장소 위의 테이블 포맷(Iceberg·Delta·Hudi): 메타데이터 트리, 스냅샷 격리, time travel, 스냅샷 만료·compaction | 02, database/23-mvcc | 작은 파일이 폭증한다 → 쿼리 계획 시간이 실행 시간보다 길다. 스냅샷을 만료시키지 않는다 → 스토리지 비용이 계속 는다. 만료 후 time travel 쿼리가 실패한다. 동시 커밋이 충돌한다 → 쓰기 재시도 [?] | 매니페스트 트리(Merkle 유사), 원자적 메타데이터 교체(CAS) | Apache Iceberg Spec · Armbrust 외 CIDR 2021 | 권장 | 신규 |
| 09-idempotent-pipelines-and-backfill | 파티션 단위 **덮어쓰기**로 멱등하게 만들기, 순수한 태스크, 백필 = 파티션 재선택, 늦게 온 데이터의 재계산, 시점별 규칙 적용 | 07, reliability/12-idempotency | append 방식 잡을 다시 돌린다 → 행이 2배가 된다. 백필이 **현재 규칙으로 과거를 계산**한다 → 확정된 과거 수치가 바뀐다. 대량 백필 → 운영 DB·클러스터 지연. 늦게 온 이벤트가 속한 파티션을 재계산하지 않는다 → 영구 누락 | 파티션 DAG(`algorithm/12-dfs` 위상정렬) | Beauchemin "Functional Data Engineering — a modern paradigm for batch data processing" · DDIA 1판 10장 [?] | 필수 | 신규 (연결: `database/34-schema-migration` 백필) |
| 10-data-contracts-and-schema-registry | 생산자–소비자 데이터 계약(스키마·의미·품질·SLA·소유자), 스키마 레지스트리 호환성 모드(BACKWARD·FORWARD·FULL·TRANSITIVE), 강제 지점 | 01, api-design/09-schema-and-serialization, testing/08-contract-testing | 상류 팀이 컬럼 이름을 바꾼다 → 하류 컬럼이 **조용히 NULL**이 된다. enum에 새 값이 생긴다 → 집계의 "기타"가 급증한다. 호환성을 `NONE`으로 둔다 → 소비자 역직렬화가 실패한다. 비transitive `BACKWARD` → 최신 직전 버전과만 검사되어, 처음부터 재생할 때 오래된 레코드를 못 읽는다 | 스키마 호환성 검사 = 필드 집합 비교 | Confluent 문서 "Schema Evolution and Compatibility" · Bitol ODCS v3.x | 필수 | 신규 |
| 11-data-quality-and-data-observability | 파이프라인 안의 품질 검사(스키마·유일성·참조·허용값)와 관측 5축(신선도·볼륨·스키마·분포·계보), 차단 vs 경고 | 10, data-analysis/23-data-cleaning-and-quality, reliability/24-metrics-and-golden-signals | **잡은 성공(초록)인데 0행 적재**. 신선도 지연을 모른다 → 어제 데이터로 의사결정을 한다. NULL 비율이 급변했는데 합계는 멀쩡해 보인다. 검사가 너무 엄격하다 → 매일 경고가 나 무시된다(알람 피로) | 행 수 이동 평균·EWMA, 분포 스케치(`data-structure/19-probabilistic-counting`) | Monte Carlo "The 5 Pillars of Data Observability" · dbt tests·Great Expectations 문서 [?] | 필수 | 신규 |
| 12-data-lineage | 데이터셋·잡·실행 단위의 계보, 테이블 수준 vs 컬럼 수준, 정적(SQL 파싱) vs 런타임 수집, 영향 분석 | 09, 11 | 컬럼을 지운 영향 범위를 모른다 → 하류 대시보드가 깨진 걸 며칠 뒤에 안다. "이 숫자 왜 틀렸나"를 추적하는 데 며칠이 걸린다. PII가 어디까지 복제됐는지 모른다 → 삭제 요청을 일부만 처리한다 | **계보 그래프(DAG) 순회**(`data-structure/08-graph`, `algorithm/11-bfs`) | OpenLineage 명세 "Object Model"(run·job·dataset·facet) | 필수 | 신규 |
| 13-event-data-modeling | 이벤트 스키마 설계: 이벤트 시각 vs 수집 시각 vs 처리 시각, 봉투(envelope: id·type·version·source·subject), 상태 스냅샷 vs 변경 이벤트 | 06, distributed/05-physical-clocks-and-ntp, distributed/27-event-sourcing | 처리 시각으로 일별 집계 → 자정 경계에서 수치가 어긋난다. 이벤트 ID가 없다 → 중복을 제거할 수 없다. 클라이언트 시계를 믿는다 → "미래" 이벤트가 생긴다. 상태 스냅샷만 보낸다 → 무엇이 왜 바뀌었는지 모른다 | 워터마크, 해시 기반 중복 제거 | CloudEvents 1.0 명세 [?] · DDIA 1판 11장 | 필수 | 신규 |
| 14-data-retention-and-erasure | 보존 기한 설계, 삭제 전파(백업·로그·파생 복제본·검색 인덱스), 불변 로그와 삭제권의 충돌, **crypto-shredding**(주체별 키 폐기), 가명화 | 12, security/03-symmetric-encryption-and-aead, security/09-randomness-and-key-management | 원본은 지웠는데 백업·분석 복제본·로그에 남아 있다 → 삭제 요청에 거짓으로 답한 셈이 된다. 불변 이벤트 로그에 평문 PII가 있다 → 지울 방법이 없다. 보존 기한이 없는 로그 → 비용과 규제 위반. 키를 폐기했더니 필요한 비개인 데이터까지 복호화할 수 없다(암호화 범위 설계 오류) | 주체별 키 맵, 톰스톤·compaction | GDPR 제17조 · EDPB Guidelines 02/2025(블록체인) [?] · event-driven.io "GDPR in event-driven architecture" | 필수 | 신규 (연결: `engineering-practice/15-legal-standards`) |
| 15-data-mesh-and-data-products | 도메인 소유·데이터를 제품으로·셀프서비스 플랫폼·연합 계산 거버넌스 — 중앙 데이터팀 병목의 대안과 비용 | 10, 12, domain-modeling/12-bounded-contexts | 중앙 팀이 병목이 된다 → 요청이 수주씩 대기한다. 도메인마다 "활성 사용자" 정의가 다르다 → 경영 보고 숫자가 서로 다르다. 거버넌스 없이 분산한다 → 아무도 소유하지 않는 테이블이 쌓인다 | — | Dehghani 『Data Mesh』(2022) [?] · Dehghani 2019 "How to Move Beyond a Monolithic Data Lake" [?] | 심화 | 신규 |
| 16-de-symptom-index | 역색인: 잡은 성공했는데 0행, 합계가 2배, 과거 리포트가 바뀜, 대시보드마다 다른 숫자, 컬럼이 갑자기 NULL, WAL 디스크 풀(복제 슬롯), 삭제했는데 남아 있음, 재처리 불가 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 17-de-incidents | 실사건 후보: Unity Audience Pinpointer 불량 데이터 적재(2022, 매출 영향 공시) [?] · Equifax 신용점수 오류(2022, 레거시 서버의 "coding issue") [?] · 영국 PHE XLS 행 제한(2020 — `data-analysis/28`과 공유, 여기서는 파이프라인 관점) | 16 | — | — | Unity 2022 Q1 실적 발표 [?] · Equifax 2022-08 발표 [?] · 영국 PHE 2020-10 | 권장 | 신규 |

### 2.2 `database/` 추가 (9.7·9.8 뒤)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 41-temporal-and-bitemporal-tables | 유효 시간(현실에서 참이던 기간) vs 기록 시간(시스템이 알던 기간), SQL:2011 application-time·system-versioned 테이블, 기간 겹침 제약, "그때 무엇을 알았나" 질의 | 23, 02 | UPDATE로 덮어쓴다 → "3월 1일 기준으로 시스템이 알던 주소"를 물으면 답할 수 없다. 소급 정정 후 과거 리포트를 재현하지 못한다. 기간 겹침 제약이 없다 → 같은 시점에 유효한 행이 둘 | 구간 트리(`data-structure/30-interval-tree`), 제외 제약(GiST) | SQL:2011 Part 2 (temporal) · Snodgrass 『Developing Time-Oriented Database Applications in SQL』 [?] · Fowler "Bitemporal History" [?] | 권장 | 신규 (연결: `data-engineering/04`, `domain-modeling/23`) |
| 42-database-side-timeouts | 서버 측 시간 한도(`statement_timeout`·`lock_timeout`·`idle_in_transaction_session_timeout`·MySQL `innodb_lock_wait_timeout`)와 클라이언트 측(소켓·쿼리 타임아웃·풀 `maxLifetime`)의 정렬. 역할별 기본값을 두는 방어선 | 22, 32 | 폭주 쿼리가 커넥션을 붙잡는다 → 풀 고갈(`Connection is not available`). `ERROR: canceling statement due to statement timeout`(57014). `lock_timeout` 없는 DDL이 락 대기열 앞에 선다 → 뒤의 모든 쿼리가 멈춘다. idle in transaction → vacuum이 막히고 락이 유지된다(25P03 [?]). **앱 소켓 타임아웃으로 끊어도 DB 쿼리는 계속 돈다.** `maxLifetime`이 중간 장비의 idle timeout보다 길다 → 이미 끊긴 커넥션을 빌린다 | 타이머, 락 대기 큐 | PostgreSQL 문서 "Client Connection Defaults" [?] · HikariCP README (`connectionTimeout`·`maxLifetime`) | 필수 | 신규 (연결: `reliability/36`·`38`) |

### 2.3 `domain-modeling/` 추가 — 신설 단원 13.3b 「추적 가능한 도메인 — 결정·버전·원장·대사」

> 사용자가 말한 "로그보다는 추적성"을 받는 단원이다. 핵심 주장은 이렇다. **"왜 이 값이 되었나"는 로그를 grep해서 재구성하는 게 아니다. 도메인 데이터에 근거를 1급으로 저장해야 한다.** 로그는 버려도 되는 운영 신호다. 결정의 근거는 버리면 안 되는 업무 기록이다(구분은 `reliability/35`).

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 22-decision-log-and-provenance | 결정 기록: 입력 스냅샷(또는 참조 + 버전)·적용 규칙 ID와 버전·중간 산출·결과·결정 시각을 한 레코드로. 재현 가능성 테스트("같은 입력으로 다시 계산하면 같은가") | 06, 07, distributed/27-event-sourcing | 고객이 "왜 이 금액인가"를 물었는데 재현할 수 없다. 로그로 재구성하려 했으나 보존 기한이 지났다. 규칙 ID만 남기고 입력을 참조로만 뒀다 → 참조 데이터가 바뀌어 재계산 결과가 다르다 | 불변 레코드, 해시 체인(변조 탐지) | W3C PROV-DM(2013) [?] · DDIA 1판 12장 "Designing for auditability" [?] | 필수 | 신규 |
| 23-versioned-rules-and-effective-dating | 요율표·세율·정책·가격표를 버전으로 관리하고 **적용 기준 시각**(주문 시각? 결제 시각?)을 명시한다. 결과 행에 버전 스탬프를 남긴다. 미래 발효 예약 | 22, 11-time-money-and-units | 요율표를 덮어쓴다 → 과거 주문을 재계산하면 금액이 다르다. 적용 기준 시각이 불명확하다 → 경계 시각 주문에서 분쟁이 난다. "배포 시각 = 발효 시각"으로 가정한다 → 배포가 늦어지면 구 요율로 결제된다 | 구간 탐색(발효일 이진 탐색, `algorithm/06-binary-search`) | Fowler "Temporal Patterns"(Effectivity·Temporal Property) [?] · `database/41` | 필수 | 신규 |
| 24-double-entry-ledger | 복식부기 원장: 모든 이동 = 차변·대변 쌍, 잔액은 파생값, 정정은 역분개(UPDATE·DELETE 금지), 멱등 전표, 잔액 스냅샷 | 05-aggregates-and-invariants, 11-time-money-and-units, database/25-app-level-concurrency-patterns | 잔액 컬럼만 UPDATE한다 → 잔액이 틀려도 원인을 추적할 수 없다. 정정을 UPDATE·DELETE로 한다 → 감사 흔적이 사라진다. 차변 합 ≠ 대변 합인데 알람이 없다. 동시 이체에서 잔액이 음수가 된다 | append-only 로그, 폴드(잔액 = 전표 합) | Fowler 『Analysis Patterns』 Accounting Patterns [?] · Modern Treasury "Accounting for Developers" [?] | 필수 | 신규 (연결: `api-design/19-case-settlement-report`·`21-case-refund`) |
| 25-reconciliation | 대사: 내부 원장 vs 외부(PG·은행·파트너) 기록을 키로 맞추고 차이를 분류(누락·중복·금액 불일치·상태 불일치)해 처리한다. **타임아웃으로 결과를 모르는 요청의 최종 확정 경로** | 24, reliability/12-idempotency, distributed/03-partial-failure-and-timeouts | PG는 승인했는데 내부 호출이 타임아웃 났다 → 돈은 빠졌는데 주문이 없다. 대사를 하지 않는다 → 누락이 고객 민원으로 발견된다. 대사 키(외부 거래 ID)를 저장하지 않았다 → 수작업으로 매칭한다. 차이를 자동 보정한다 → 원인이 은폐된다 | 정렬 병합 조인(`algorithm/34-external-sort-and-k-way-merge`), 해시 조인 | 결제사 정산 문서 [?] · `reliability/04-failure-modes-catalog` 결제 F-항목 | 필수 | 신규 |

### 2.4 `reliability/` 추가

#### 11.4 관측성 — 1개

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 35-logs-traces-audit-roles | 네 가지 기록의 역할 구분. 운영 로그(버려도 됨·샘플링 가능), 지표, 추적(인과·지연 — 샘플링됨), **감사 기록·업무 기록**(버리면 안 됨·보존 기한·변조 방지). "이 사건은 어디에 남겨야 하나" 판정 기준 | 23, 25, security/25-security-logging-and-audit | 감사가 필요한 사건을 앱 로그에만 남긴다 → 14일 보존이 지나면 증거가 사라진다. 로그 샘플링·레벨 조정이 업무 이벤트까지 버린다. 트레이스를 감사 근거로 쓴다 → head 샘플링으로 해당 요청이 없다. 로그에 PII를 남긴다 → 삭제 요청 범위가 로그까지 번진다 | 해시 체인, 링 버퍼(운영 로그) | OpenTelemetry 명세 Signals(Logs·Traces·Metrics) · OWASP Logging Cheat Sheet [?] | 필수 | 신규 |

#### 신설 단원 11.2b 「시간 예산 설계」 — 5개 (+ 기존 06·07·17 재편입)

> 사용자가 물은 "단계별 타임아웃 설계"를 받는 단원이다.
> 단원 순서: `06 데드라인 전파(기존)` → `36 계층별 타임아웃` → `37 예산 분배` → `07 재시도·재시도 예산(기존)` → `38 취소 전파` → `17 헤지(기존)` → `39 배치·잡 시간 한도` → `40 종합 연습`.

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 36-timeout-taxonomy-by-layer | 호출 하나에 달린 타임아웃 목록과 포함 관계: 풀 획득 → DNS → connect → TLS 핸드셰이크 → 요청 쓰기 → 첫 바이트(응답 헤더) → 읽기 idle → 전체(call) → 커넥션 idle·수명. 라이브러리마다 다른 기본값과 "무엇이 포함되나" | 06, network/15-tcp-handshake-and-backlog, network/29-tls-handshake, network/35-http-connection-management | connect 타임아웃을 설정하지 않았다 → 방화벽이 SYN을 drop하면 OS 기본 재시도(리눅스 `tcp_syn_retries`=6에서 약 2분 [?]) 동안 스레드가 멈춘다. read(idle) 타임아웃만 있다 → 조금씩 흘러오는 응답(slow drip)은 끝나지 않는다. 전체 타임아웃이 필요하다. 풀 대기가 타임아웃에 포함되지 않는다 → 실제 지연 = 대기 + 호출 | 타이머 휠(`data-structure/37-timer-structures`) | Envoy FAQ "How do I configure timeouts?"(connect_timeout은 TLS 포함, 기본 5초) · Cloudflare 블로그 "The complete guide to Go net/http timeouts" [?] | 필수 | 신규 |
| 37-time-budget-allocation | **총 예산을 단계에 나누는 설계 패턴.** SLO에서 총 예산 역산, 단계별 타임아웃 = 하류 p99.x 기반(오탐률 선택), per-try 타임아웃 vs 전체, 재시도·폴백·응답 직렬화 몫 예약, 남은 예산이 최소치 미만이면 시작하지 않기 | 36, 07, 02-slo-sli-error-budget, data-analysis/06-percentiles-and-latency-distributions | 단계 타임아웃의 합이 전체보다 크다 → 마지막 단계가 늘 잘린다. per-try 없이 재시도 → 첫 시도가 예산을 다 쓴다. 상류 5s·하류 10s(역전) → 헛일. p50 기준 타임아웃 → 오탐 타임아웃과 재시도 폭풍. 폴백 몫이 없다 → 폴백을 실행할 시간이 없어 결국 504 | 예산 = 남은 시간 차감, 백분위 추정 | Amazon Builders' Library "Timeouts, retries, and backoff with jitter"(오탐률 → p99.9) · Envoy `per_try_timeout` · gRPC Deadlines 가이드(경과 시간 차감 변환) | 필수 | 신규 (흡수: `reliability/06`의 "남은 예산 전파"를 여기서 심화) |
| 38-cancellation-propagation | 타임아웃이 나면 **작업을 실제로 멈추는** 방법: Go `context`, Java 인터럽트·`Future.cancel`·구조적 동시성(StructuredTaskScope), gRPC 취소, DB 쿼리 취소, 취소 불가 구간(외부 결제 호출)의 처리 | 37, language/15-concurrency-models, os/06-signals | 클라이언트는 포기했는데 서버는 끝까지 처리한다 → 과부하 때 헛일이 폭증하고 goodput이 0이 된다. `CompletableFuture` 타임아웃(Resilience4j TimeLimiter)이 원래 작업을 취소하지 않는다 → 스레드가 새어 나간다. 인터럽트를 삼킨다(`catch InterruptedException {}`). 취소 불가 외부 호출 → 결과가 모호해진다 → `domain-modeling/25` 대사로 넘긴다 | 취소 트리(부모 → 자식 전파) | Go `context` 패키지 문서 · JEP 505/525 Structured Concurrency (preview) · Resilience4j TimeLimiter 문서(`cancelRunningFuture`는 Future에만 적용) | 필수 | 신규 |
| 39-batch-and-job-time-bounds | 배치·스케줄 작업의 시간 한도: 잡 전체·단계·태스크 타임아웃, heartbeat·lease, 마감 알림(끝나지 않아도 발화), 체크포인트와 재개, 강제 종료 후 부분 산출물 정리 | 37, 15-scheduler-and-cron-ha, data-engineering/09-idempotent-pipelines-and-backfill | 잡이 멈춘다(hang) → 다음 스케줄과 겹쳐 이중 실행된다. 잡 전체 타임아웃만 있다 → 어느 단계가 느린지 모른다. 타임아웃으로 kill한 뒤 부분 산출물이 남는다 → 다음 단계가 반쯤 된 데이터를 읽는다. 체크포인트가 없다 → 매번 처음부터 다시 해서 영원히 못 끝낸다. SLA 알림이 **작업이 끝난 뒤에야** 발화한다 | lease·fencing(`distributed/17-coordination-and-fencing`), 체크포인트 | Airflow 문서 `execution_timeout`·`dagrun_timeout`·Deadline Alerts(3.x, SLA 대체) · Spring Batch 문서 [?] | 권장 | 신규 |
| 40-timeout-design-worksheet | 종합 연습: 요청 경로 하나(게이트웨이 → 서비스 A → B·DB·외부 PG)에 **단계별 시간 예산표**를 쓰고 Envoy(route `timeout`·`per_try_timeout`·`idle_timeout`, cluster `connect_timeout`)와 Resilience4j(TimeLimiter·Retry·CircuitBreaker 순서) 설정으로 옮긴다. 결과가 모호한 단계는 멱등 키와 대사 경로를 붙인다 | 36, 37, 38, 08-circuit-breaker, api-design/05-idempotency-keys | 게이트웨이 타임아웃 < 서비스 타임아웃 → 사용자는 504를 받았는데 결제는 된다. 데코레이터 순서 착오(Retry가 TimeLimiter 안쪽) → 재시도 전체가 한 번의 타임아웃에 묶인다 [?]. 서킷브레이커가 타임아웃을 실패로 세지 않는다 → 느린 하류를 계속 호출한다 | 예산표 = 트리(호출 그래프)의 경로 합 | Envoy route_components 문서 · Resilience4j 문서 · `reliability/06`·`12` | 권장 | 신규 |

---

## 3. 판단

### 3.1 "데이터 공학" 영역을 새로 만드나, 기존 영역에 나눠 넣나 → **신설한다** (`data-engineering/`, 17 leaf)

- **이유 ① — 규모.** 17개를 `database/`에 넣으면 40 → 57개가 된다. `database/`의 축인 "엔진 내부"(페이지·인덱스·MVCC·WAL)가 흐려진다. `distributed/`(32)나 `data-analysis/`(28)에 넣어도 같은 문제가 생긴다.
- **이유 ② — 장애 양상이 다르다.** DB·분산 영역의 "깨지면"은 에러 코드와 지연으로 보인다. 데이터 공학의 "깨지면"은 **잡이 성공했는데 숫자가 틀린 것**으로 보인다. 역색인(`16-de-symptom-index`)을 따로 두어야 증상 검색이 된다. 이는 curriculum §0.3의 영역 마감 규칙과도 맞는다.
- **이유 ③ — 선행 위치.** `database/08`, `distributed/21·24·28`, `reliability/12`에 기대고, `data-analysis/`가 이 영역의 산출물을 소비한다. 그래서 **Part 6 맨 앞, `data-analysis/` 직전**에 둔다. 흐름은 "만든 데이터를 옮기고 관리 → 판단"이 된다. 영역 번호는 반영할 때 18a 또는 재번호로 정한다.
- **예외.** 엔진 기능에 가까운 두 leaf만 기존 영역에 둔다. `database/41`(temporal 테이블은 SQL 표준 기능)과 `database/42`(DB 서버 설정)다.
- **기존 흡수.** `distributed/21`의 CDC 한 줄은 `data-engineering/06`으로 심화한다. `data-analysis/23`은 분석 쪽 정제로 남기고 `data-engineering/11`을 선행 연결로 둔다.

### 3.2 추적성은 독립 영역인가 → **아니다. 단원 1개 + 관측성 leaf 1개 + 읽기 경로로 처리한다**

- 추적성은 층위가 아니다. 여러 층을 가로지르는 **성질**이다. 영역으로 만들면 이벤트 소싱·트레이싱·감사 로그·계보가 중복된다.
- 대신 다음과 같이 배치한다.
  - 업무 데이터 쪽 근거 저장(22~25)은 `domain-modeling/` 신설 단원으로 모은다. 규칙·금액·상태를 다루는 곳이 도메인 모델링이기 때문이다.
  - 운영 신호와 업무 기록의 경계는 `reliability/35`로 둔다.
  - 데이터 흐름 쪽은 `data-engineering/12`(계보)로 둔다.
- **읽기 경로 "추적성 트랙"을 roadmap에 둘 것을 권고한다**(leaf 아님).

  ```text
  reliability/23 → 25 → 35 → distributed/27 → domain-modeling/22 → 23 → 24 → 25 → database/41 → data-engineering/12 → 14
  ```

### 3.3 "시간 예산 설계"를 독립 패턴 단원으로 세우나 → **세운다. 단 영역이 아니라 `reliability/` 안의 단원(11.2b)으로 세운다**

- 사용자의 직관이 맞다. 흩어진 조각이 이미 5곳에 있다. `reliability/06`(전파), `07`(재시도), `17`(헤지), `database/32`(풀 대기), `network/21·35`(TCP·HTTP idle)다.
- 그런데 **"총 예산을 단계에 나누고, 넘으면 멈추고, 모호하면 확정한다"**는 설계 절차가 한 곳에 없다. 이 절차가 곧 패턴이다.
- 근거 자료도 같은 구조를 보인다. 모두 "단계별 한도 + 전체 한도 + 남은 시간 전파"를 하나의 설계 대상으로 다룬다.
  - Envoy는 route `timeout`·`per_try_timeout`·`idle_timeout`, cluster `connect_timeout`을 서로 다른 층의 한도로 나눈다.
  - gRPC는 데드라인을 "경과 시간을 뺀 타임아웃"으로 바꿔 전파한다.
  - AWS Builders' Library는 오탐률에서 하류 백분위를 골라 타임아웃을 정한다.
- 영역으로 분리하지 않는 이유가 있다. 선행(백분위·SLO·재시도·멱등)이 모두 `reliability/`에 있다. 따로 떼면 선행 링크만 늘어난다.
- 반영할 때 기존 `06·07·17`을 단원 11.2b로 옮길지, 11.2에 두고 순서만 묶을지는 사용자가 결정한다. 이 문서의 권고는 **순서만 묶기**다. 번호 이동을 최소화하기 위해서다.

---

## 4. 기존 leaf 보강 권고 (신규 leaf 아님 — 중복 방지)

| 대상 | 보강 내용 | 근거 |
|---|---|---|
| `reliability/25-distributed-tracing` | 요지에 **baggage**(업무 문맥 전파, W3C Baggage — 64항목·8192바이트까지 전파 의무)와 **span link**(큐·배치에서 여러 부모 연결)를 추가한다. ⚠에 "배치 소비에서 producer span을 부모로 삼아 트레이스가 왜곡됨"을 넣는다 | W3C Baggage · OTel Messaging semconv |
| `reliability/07-retry-backoff-jitter` | "재시도 예산"의 구체형을 추가한다. Finagle 기본(요청의 20% + 초당 최소 10회, 토큰 10초 만료), gRPC `retryThrottling`(maxTokens·tokenRatio — 토큰이 절반 미만이면 재시도·헤지 중단) | Finagle 블로그 2016-02-08 "Retry Budgets" · gRFC A6 |
| `reliability/06-timeouts-and-deadline-propagation` | 요지에 "gRPC는 절대 시각 대신 경과 시간을 뺀 타임아웃으로 전파(시계 어긋남 회피), 서버는 취소를 주기적으로 확인할 책임"을 추가한다. 심화는 `37`·`38`로 넘긴다 | gRPC Deadlines 가이드 |
| `database/32-connection-pooling` | `maxLifetime` < 중간 장비·DB idle timeout 규칙 한 줄을 추가하고 `database/42`로 연결한다 | HikariCP 문서 |
| `distributed/21-outbox-and-dual-write` | CDC 상세를 `data-engineering/06`으로 위임한다는 링크를 둔다 | — |
| `data-analysis/23-data-cleaning-and-quality` | 선행 또는 연결로 `data-engineering/11`을 둔다. 역할은 정제(분석 측)와 검사(파이프라인 측)로 나눈다 | — |
| `security/25-security-logging-and-audit` | 연결로 `reliability/35`를 둔다 | — |
| 역색인 `reliability/33`·`database/39`·`domain-modeling/20` | 증상을 추가한다. "504인데 결제됨", "타임아웃 났는데 DB 쿼리는 계속 돔", "잡 hang 후 이중 실행", "과거 금액 재계산 불일치", "잔액 원인 불명" | 본 문서 ⚠ 칸 |

---

## 5. 확인하지 못한 것 (`[?]` 모음)

- DDIA 1판 12장의 절 제목("Designing for auditability" 등)과 10장 "batch 출력 철학" 절의 위치. DDIA 2판(Kleppmann–Riccomini)의 장 구성은 검색으로 목차를 확보하지 못했다.
- Kimball 『The Data Warehouse Toolkit』 3판의 장 번호. 웹 "Dimensional Modeling Techniques"와 Design Tip #152는 확인했다.
- Linstedt Data Vault 2.0 서적, Dehghani 『Data Mesh』 서적의 서지. 4원칙 자체는 확인했다.
- Beauchemin "Functional Data Engineering"의 발행 연도(2018로 기억).
- CloudEvents 1.0 명세 필드, W3C PROV-DM, Fowler "Temporal Patterns"·"Bitemporal History"·『Analysis Patterns』 Accounting Patterns의 원문. 이번에 검색하지 않았다.
- `data-engineering/17` 사건 후보(Unity 2022, Equifax 2022)의 1차 출처. 기억 기반이므로 노트 작성 전에 반드시 확인한다.
- 리눅스 `tcp_syn_retries` 기본값에 따른 connect 대기 시간(약 127초), PostgreSQL SQLSTATE 25P03, Iceberg 동시 커밋 실패 예외명.
- Resilience4j 데코레이터 기본 적용 순서(Retry·CircuitBreaker·TimeLimiter 간), Spring Batch의 단계 타임아웃 지원 방식.
- EDPB Guidelines 02/2025의 정확한 제목과 범위(검색 결과에 연도 표기가 혼재했다).

## 6. 출처 (이번 작업에서 검색으로 확인)

- gRPC "Deadlines" 가이드 — https://grpc.io/docs/guides/deadlines/
- gRFC A6 Client Retries — https://github.com/grpc/proposal/blob/master/A6-client-retries.md
- Envoy FAQ "How do I configure timeouts?" — https://www.envoyproxy.io/docs/envoy/latest/faq/configuration/timeouts
- Finagle "Retry Budgets"(2016-02-08) — https://finagle.github.io/blog/2016/02/08/retry-budgets/
- Resilience4j TimeLimiter — https://resilience4j.readme.io/docs/timeout
- Amazon Builders' Library "Timeouts, retries, and backoff with jitter" — https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- Airflow "Deadline Alerts"·"Migrating from SLA to Deadline Alerts" — https://airflow.apache.org/docs/apache-airflow/stable/howto/deadline-alerts.html
- Go context / JEP 505·525 Structured Concurrency — https://openjdk.org/jeps/525
- W3C Trace Context — https://www.w3.org/TR/trace-context/ · W3C Baggage — https://www.w3.org/TR/baggage/
- OpenTelemetry Messaging spans semconv — https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/
- Debezium Features·Incremental Snapshots — https://debezium.io/documentation/reference/stable/features.html · https://debezium.io/blog/2021/10/07/incremental-snapshots/
- Kimball Group SCD Type 2 · Design Tip #152 — https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/
- Kreps "Questioning the Lambda Architecture"(2014) — https://www.oreilly.com/radar/questioning-the-lambda-architecture/
- Apache Iceberg Spec — https://iceberg.apache.org/spec/ · Armbrust 외 CIDR 2021 Lakehouse — https://vldb.org/cidrdb/2021/lakehouse-a-new-generation-of-open-platforms-that-unify-data-warehousing-and-advanced-analytics.html
- Crypto-shredding / GDPR in event-driven — https://event-driven.io/en/gdpr_in_event_driven_architecture/
- OpenLineage Object Model — https://openlineage.io/docs/spec/object-model/
- Beauchemin "Functional Data Engineering" — https://maximebeauchemin.medium.com/functional-data-engineering-a-modern-paradigm-for-batch-data-processing-2327ec32c42a
- Bitol ODCS — https://bitol-io.github.io/open-data-contract-standard/ · Confluent Schema Evolution — https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html
- Data mesh 4원칙 — https://en.wikipedia.org/wiki/Data_mesh · Data Vault Hub·Link·Satellite(2차 자료)
- SQL:2011 temporal — https://en.wikipedia.org/wiki/SQL:2011
- PostgreSQL 타임아웃·HikariCP(2차 자료 — 1차 문서 재확인 필요)
- Monte Carlo "5 Pillars of Data Observability" — https://www.montecarlodata.com/blog-introducing-the-5-pillars-of-data-observability/
