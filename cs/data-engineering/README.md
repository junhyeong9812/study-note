# 데이터 공학 — `cs/data-engineering/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §18a에서 `scripts/notes/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 17 · 검수 완료 0

> **번호 메모**: 기존 §18(data-analysis)과 §19~§21 번호를 유지하려고 18a로 끼웠다. 읽는 순서는 **18a → 18**이다 — 만든 데이터를 옮기고 관리한 뒤 판단한다.
> 흐름: 원천과 파생 → 분석 저장소와 모델 → 옮기기(CDC·배치·스트림) → 안전하게 다시 돌리기 → 계약·품질·계보 → 보존·삭제 → 조직. 이 영역의 "깨지면"은 크래시로 보이지 않는다. **파이프라인은 초록인데 숫자가 틀린** 모양으로 보인다 — ⚠ 칸에는 가능한 한 "어느 숫자가 어떻게 어긋나 보이나"를 적었다. 엔진 기능에 가까운 temporal 테이블(database/50)과 DB 서버 타임아웃(database/22)은 database에 둔다.
> 뼈대: DDIA 1판 3장(OLTP vs 분석·스타 스키마)·10장(배치 출력의 철학)·11장(CDC·이벤트 소싱)·12장(파생 데이터·감사 가능성, 절 제목 `[?]`), Kimball Group "Dimensional Modeling Techniques"(『The Data Warehouse Toolkit』 3판 장 번호 `[?]`), Armbrust 외 CIDR 2021 "Lakehouse", Kreps 2014 "Questioning the Lambda Architecture", Beauchemin "Functional Data Engineering"(2018), Reis–Housley 『Fundamentals of Data Engineering』(2022) `[?]`.

## 18a.1 원천·파생과 분석 저장소

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `system-of-record-and-derived-data` | 기록 시스템(원천)과 파생 데이터(캐시·검색 인덱스·집계·읽기 모델)의 구분. 비정규화는 "파생본을 하나 더 두는 결정"이다. 원천이 있어야 파생본을 재구축할 수 있다 | 필수 | 초안(Claude) | [01-system-of-record-and-derived-data](01-system-of-record-and-derived-data/) |
| 02 | `oltp-olap-and-warehouse` | 운영 DB와 분석 저장소를 나누는 이유, 웨어하우스·마트, ETL vs ELT(원본을 먼저 적재한 뒤 변환) | 필수 | 초안(Claude) | [02-oltp-olap-and-warehouse](02-oltp-olap-and-warehouse/) |
| 14 | `lakehouse-table-formats` | 객체 저장소 위의 테이블 포맷(Iceberg·Delta·Hudi): 메타데이터 트리, 스냅샷 격리, time travel, 스냅샷 만료·compaction | 권장 | 초안(Claude) | [14-lakehouse-table-formats](14-lakehouse-table-formats/) |

## 18a.2 분석 모델링

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 03 | `dimensional-modeling` | 팩트·차원·**grain(한 행의 뜻) 선언**, 스타 vs 스노우플레이크, 가산·반가산·비가산 지표, 공통 차원(conformed) | 필수 | 초안(Claude) | [03-dimensional-modeling](03-dimensional-modeling/) |
| 04 | `slowly-changing-dimensions` | SCD Type 0~3(+4·6·7), 대리 키와 내구 키, 유효 기간 컬럼 | 필수 | 초안(Claude) | [04-slowly-changing-dimensions](04-slowly-changing-dimensions/) |
| 13 | `data-vault` | Hub(비즈니스 키)·Link(관계)·Satellite(시점별 속성), 적재 이력 보존형 통합 모델 | 심화 | 초안(Claude) | [13-data-vault](13-data-vault/) |

## 18a.3 옮기기와 다시 돌리기

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 05 | `change-data-capture` | 로그 기반 CDC(WAL·binlog 구독), 초기 스냅샷 + 스트리밍, 증분 스냅샷, 삭제 tombstone, DDL 변경 | 필수 | 초안(Claude) | [05-change-data-capture](05-change-data-capture/) |
| 06 | `event-data-modeling` | 이벤트 스키마 설계: 이벤트 시각 vs 수집 시각 vs 처리 시각, 봉투(envelope: id·type·version·source·subject), 상태 스냅샷 vs 변경 이벤트 | 필수 | 초안(Claude) | [06-event-data-modeling](06-event-data-modeling/) |
| 07 | `batch-stream-architectures` | Lambda(배치 + 속도 계층) vs Kappa(재생 가능한 로그 하나로 스트림 재처리), 재처리 전략 | 권장 | 초안(Claude) | [07-batch-stream-architectures](07-batch-stream-architectures/) |
| 08 | `idempotent-pipelines-and-backfill` | 파티션 단위 **덮어쓰기**로 멱등하게 만들기, 순수한 태스크, 백필 = 파티션 재선택, 늦게 온 데이터의 재계산, 시점별 규칙 적용 | 필수 | 초안(Claude) | [08-idempotent-pipelines-and-backfill](08-idempotent-pipelines-and-backfill/) |

## 18a.4 계약·품질·계보·보존

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 09 | `data-contracts-and-schema-registry` | 생산자–소비자 데이터 계약(스키마·의미·품질·SLA·소유자), 스키마 레지스트리 호환성 모드(BACKWARD·FORWARD·FULL·TRANSITIVE), 강제 지점 | 필수 | 초안(Claude) | [09-data-contracts-and-schema-registry](09-data-contracts-and-schema-registry/) |
| 10 | `data-quality-and-data-observability` | 파이프라인 안의 품질 검사(스키마·유일성·참조·허용값)와 관측 5축(신선도·볼륨·스키마·분포·계보), 차단 vs 경고 | 필수 | 초안(Claude) | [10-data-quality-and-data-observability](10-data-quality-and-data-observability/) |
| 11 | `data-lineage` | 데이터셋·잡·실행 단위의 계보, 테이블 수준 vs 컬럼 수준, 정적(SQL 파싱) vs 런타임 수집, 영향 분석 | 필수 | 초안(Claude) | [11-data-lineage](11-data-lineage/) |
| 12 | `data-retention-and-erasure` | 보존 기한 설계, 삭제 전파(백업·로그·파생 복제본·검색 인덱스), 불변 로그와 삭제권의 충돌, **crypto-shredding**(주체별 키 폐기), 가명화 | 필수 | 초안(Claude) | [12-data-retention-and-erasure](12-data-retention-and-erasure/) |

## 18a.5 조직

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 15 | `data-mesh-and-data-products` | 도메인 소유·데이터를 제품으로·셀프서비스 플랫폼·연합 계산 거버넌스 — 중앙 데이터팀 병목의 대안과 비용 | 심화 | 초안(Claude) | [15-data-mesh-and-data-products](15-data-mesh-and-data-products/) |

## 18a.6 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 16 | `de-symptom-index` | 역색인: 잡은 성공했는데 0행, 합계가 2배, 과거 리포트가 바뀜, 대시보드마다 다른 숫자, 컬럼이 갑자기 NULL, WAL 디스크 풀(복제 슬롯), 삭제했는데 남아 있음, 재처리 불가 | 필수 | 초안(Claude) | [16-de-symptom-index](16-de-symptom-index/) |
| 17 | `de-incidents` | 실사건 후보: Unity 2022의 두 문제 — 플랫폼 결함 → Audience Pinpointer 정확도 저하, 대형 고객의 불량 데이터 적재 → 학습 데이터 가치 일부 상실(매출 영향 공시) · Equifax 신용점수 오류(2022, 레거시 서버의 "coding issue") · 영국 PHE XLS 행 제한(2020 — `data-analysis/28-da-incidents`와 공유, 여기서는 파이프라인 관점) | 권장 | 초안(Claude) | [17-de-incidents](17-de-incidents/) |
