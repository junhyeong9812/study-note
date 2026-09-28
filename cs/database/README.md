# 데이터베이스 — `cs/database/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §9에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 48 · 원고 있음 6 · 초안(Claude) 3 · 검수 완료 0

> 모델·SQL → 스토리지 → 인덱스 → 쿼리 처리 → 트랜잭션·동시성 제어 → 로깅·복구 → 복제·분할 → 애플리케이션과 DB. 기존 보유(LSM·파티셔닝·clickhouse·RLS·시계열)는 대부분 스토리지·분할 쪽이므로 **트랜잭션·격리 수준·MVCC·WAL**이 신규의 중심.
> 뼈대: CMU 15-445 Fall 2024 강의 번호(이하 L#, 확인), DDIA 1판 2~7장(확인), Berenson 외 1995, PostgreSQL·MySQL 문서.

## 9.1 모델·SQL

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `relational-model-and-algebra` | 릴레이션·튜플·관계 대수(σ·π·⋈) | 필수 | 미작성 | — |
| 02 | `keys-and-constraints` | PK·FK·UNIQUE·CHECK·NOT NULL | 필수 | 미작성 | — |
| 03 | `normalization` | 함수 종속·1NF~BCNF·반정규화 판단 | 필수 | 미작성 | — |
| 04 | `sql-joins-and-aggregation` | 논리 처리 순서·조인·집계·NULL 3치 논리 | 필수 | 미작성 | — |
| 05 | `window-functions-and-cte` | 윈도 함수·프레임·CTE·재귀 CTE | 권장 | 미작성 | — |
| 36 | `data-models-document-graph` | 관계 vs 문서 vs 그래프, 스키마 온 리드 | 권장 | 미작성 | — |

## 9.2 스토리지

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 06 | `pages-and-tuple-layout` | 힙 파일·슬롯 페이지·튜플 헤더·대형 값(TOAST) | 필수 | 미작성 | — |
| 07 | `buffer-pool` | 버퍼 풀·핀·dirty·교체 정책 | 필수 | 미작성 | — |
| 37 | `row-vs-column-storage` | 행 저장 vs 컬럼 저장·압축 | 권장 | 미작성 | — |
| 38 | `lsm-storage-engine` | memtable·SSTable·compaction·쓰기/읽기/공간 증폭 | 권장 | 초안(Claude) | [../systems/lsm-tree](../systems/lsm-tree/) |

## 9.3 인덱스

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 08 | `btree-indexes` | B+Tree 구조·분할/병합·클러스터드 vs 보조 | 필수 | 미작성 | — |
| 09 | `index-design` | 복합·커버링·부분·표현식 인덱스, 선택도 | 필수 | 미작성 | — |
| 39 | `hash-indexes` | 정적·확장·선형 해싱 | 권장 | 미작성 | — |
| 40 | `filters-and-specialized-indexes` | 블룸 필터·역색인·공간·BRIN | 권장 | 미작성 | — |
| 53 | `index-concurrency-control` | 래치·래치 크래빙·B-link 트리 | 심화 | 미작성 | — |

## 9.4 쿼리 처리

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 11 | `join-algorithms` | 중첩 루프·해시 조인·정렬 병합 조인 | 필수 | 미작성 | — |
| 12 | `query-optimizer-and-explain` | 비용 기반 최적화·통계·카디널리티 추정·EXPLAIN 읽기 | 필수 | 미작성 | — |
| 41 | `sorting-and-aggregation` | 외부 정렬·해시 집계·스필 | 권장 | 미작성 | — |
| 54 | `query-execution-models` | 반복자(Volcano)·벡터화·병렬 실행 | 심화 | 미작성 | — |

## 9.5 트랜잭션·동시성 제어

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 13 | `transactions-acid` | 원자성·일관성·격리·지속성의 정확한 뜻, 직렬화 가능성 | 필수 | 미작성 | — |
| 14 | `isolation-levels-and-anomalies` | RU/RC/RR/SI/Serializable, dirty·non-repeatable·phantom·**lost update·write skew** | 필수 | 미작성 | — |
| 15 | `two-phase-locking-and-deadlock` | 2PL·엄격 2PL·락 모드·DB 데드락 탐지 | 필수 | 미작성 | — |
| 16 | `mvcc` | 버전 체인·스냅샷·가시성·가비지 수집(vacuum) | 필수 | 미작성 | — |
| 17 | `occ-and-timestamp-ordering` | 낙관적 동시성·타임스탬프 순서·버전 컬럼 | 권장 | 미작성 | — |
| 18 | `app-level-concurrency-patterns` | `SELECT … FOR UPDATE`·조건부 UPDATE·원자적 upsert·유니크 제약 활용 | 필수 | 미작성 | — |

## 9.6 로깅·복구·백업

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 19 | `wal-and-logging` | WAL 규칙·group commit·no-force/steal | 필수 | 미작성 | — |
| 20 | `backup-and-pitr` | 논리/물리 백업·PITR·복원 검증 | 필수 | 미작성 | — |
| 42 | `recovery-aries-checkpoints` | ARIES(분석·재실행·취소)·체크포인트 | 권장 | 미작성 | — |

## 9.7 복제·분할

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 32 | `replication-leader-follower` | 동기/비동기 복제·복제 지연·읽기 보장 | 필수 | 원고 있음 | [../systems/server-design/03-data-layer.md](../systems/server-design/03-data-layer.md) |
| 33 | `partitioning-and-sharding` | 키 범위·해시 분할·보조 인덱스·재조정 | 필수 | 초안(Claude) | [../systems/partitioning-vs-sharding](../systems/partitioning-vs-sharding/) · [../systems/server-design/03-data-layer.md](../systems/server-design/03-data-layer.md) |
| 55 | `distributed-databases` | 분산 OLTP·OLAP 개관, NewSQL | 심화 | 미작성 | — |

## 9.8 애플리케이션과 DB

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 21 | `connection-pooling` | 풀 크기·대기·검증·max_connections, `maxLifetime` < 중간 장비·DB idle timeout 규칙(서버 측 한도는 22) | 필수 | 미작성 | — |
| 22 | `database-side-timeouts` | 서버 측 시간 한도(`statement_timeout`·`lock_timeout`·`idle_in_transaction_session_timeout`·MySQL `innodb_lock_wait_timeout`)와 클라이언트 측(소켓·쿼리 타임아웃·풀 `maxLifetime`)의 정렬. 역할별 기본값을 두는 방어선 | 필수 | 미작성 | — |
| 23 | `orm-and-n-plus-one` | ORM 매핑·영속성 컨텍스트·지연 로딩·N+1 | 필수 | 원고 있음 | [../engineering/data-access](../engineering/data-access/) |
| 25 | `data-source-patterns` | Table/Row Data Gateway·Active Record·Data Mapper·Repository(PoEAA 정의)·Query Object·Metadata Mapping — "누가 SQL을 아는가" | 필수 | 미작성 | — |
| 26 | `schema-migration` | 무중단 마이그레이션·expand/contract·백필 | 필수 | 원고 있음 | [../systems/server-design/08-deployment-ops.md](../systems/server-design/08-deployment-ops.md) |
| 30 | `caching-with-databases` | cache-aside·write-through·무효화·일관성 | 필수 | 원고 있음 | [../systems/server-design/04-caching.md](../systems/server-design/04-caching.md) |
| 43 | `row-level-security` | 행 수준 보안·테넌트 격리 | 권장 | 원고 있음 | [../systems/postgres-rls](../systems/postgres-rls/) |
| 44 | `timeseries-resolution-tiers` | 시계열 해상도 계층·다운샘플·보존 | 권장 | 초안(Claude) | [../systems/timeseries-resolution-tiers](../systems/timeseries-resolution-tiers/) · [../ops-patterns/17-timeseries](../ops-patterns/17-timeseries/) |
| 45 | `clickhouse-mergetree` | 컬럼 저장 + 병합 트리 엔진 | 심화 | 원고 있음 | [../systems/clickhouse-mergetree](../systems/clickhouse-mergetree/) |
| 49 | `multi-level-caching` | 로컬 L1(프로세스 내) + 분산 L2(Redis) 계층, 인스턴스 간 무효화 전파(pub/sub·서버 지원 클라이언트 캐싱), 로컬 캐시의 크기 제한과 GC 압박, 핫키 로컬화 | 권장 | 미작성 | — |
| 51 | `object-relational-structural-mapping` | Identity Field(대리키 vs 자연키)·Embedded Value·Foreign Key / Association Table Mapping·Dependent Mapping·Serialized LOB·상속 매핑 3종(단일·클래스·구체 테이블) | 권장 | 미작성 | — |
| 52 | `offline-concurrency-patterns` | 여러 요청에 걸친 **비즈니스 트랜잭션**의 동시성 — Optimistic / Pessimistic Offline Lock·Coarse-Grained Lock(aggregate 단위 버전)·Implicit Lock, 락 만료·해제 | 권장 | 미작성 | — |

## 9.8b 실무 데이터 운영 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 10 | `collation-and-text-comparison` | collation(대소문자·악센트 무시), 정렬 순서, 유니크 제약과 비교 규칙, ICU vs libc | 필수 | 미작성 | — |
| 24 | `transaction-boundaries-in-app-code` | 선언적 트랜잭션(프록시·자기 호출), 전파 속성, readOnly, 롤백 규칙, 커밋 후 훅, 트랜잭션 안 외부 호출 금지 | 필수 | 미작성 | — |
| 27 | `temporal-types-and-session-timezone` | `timestamp` vs `timestamptz`·`DATETIME` vs `TIMESTAMP`, 세션 시간대, 드라이버 변환, 시간대 기준 `date_trunc` | 필수 | 미작성 | — |
| 28 | `key-strategy-surrogate-natural-public-id` | 대리키 vs 자연키, bigint vs UUIDv4/v7, 내부 PK와 외부 노출 ID 분리, 접두어 ID(`cus_…`) | 필수 | 미작성 | — |
| 29 | `soft-delete-and-data-lifecycle` | `deleted_at` 소프트 삭제, 부분 유니크 인덱스, 기본 필터 누락, 아카이브 테이블, 보관 기한과 하드 삭제 | 필수 | 미작성 | — |
| 31 | `cache-key-versioning-and-serialization` | 캐시 키 설계(네임스페이스·테넌트·버전), 값 직렬화 스키마 호환, null 캐싱, 핫 키, TTL 지터, write-behind 위험 | 필수 | 미작성 | — |
| 34 | `large-backfill-and-batch-dml` | 대량 UPDATE·DELETE·백필: keyset 청크, 스로틀(복제 지연 기준), 재시작 가능성, 전후 행 수 검증 | 필수 | 미작성 | — |
| 35 | `bulk-file-import-export` | CSV·엑셀 입출력: RFC 4180 인용 규칙, 스트리밍 파싱, 인코딩 감지(UTF-8·BOM·CP949), 행 단위 오류 보고, 부분 적재 정책, CSV 수식 주입 | 필수 | 미작성 | — |
| 50 | `temporal-and-bitemporal-tables` | 유효 시간(현실에서 참이던 기간) vs 기록 시간(시스템이 알던 기간), SQL:2011 application-time·system-versioned 테이블, 기간 겹침 제약, "그때 무엇을 알았나" 질의 | 권장 | 미작성 | — |

## 9.8c 검색 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 46 | `full-text-search-and-analyzers` | 분석기(토크나이저·필터), 한국어 형태소(nori) vs n-gram, BM25 관련도, 동의어 | 권장 | 미작성 | — |
| 47 | `autocomplete-and-typeahead` | 접두사 완성, edge n-gram, 인기도 순위, 한글 자모·초성 분해, 디바운스·캐시 | 권장 | 미작성 | — |
| 48 | `search-index-sync-and-reindexing` | DB→검색 인덱스 동기화(이중 쓰기 vs CDC), 지연·불일치 감지, 별칭 교체로 무중단 재색인 | 권장 | 미작성 | — |

## 9.9 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 56 | `db-symptom-index` | 역색인: 1205/1213/40P01/40001, 풀 고갈 메시지, `too many clients`, bloat, 복제 지연, `Too many parts`, 플랜 급변, 스필, 저장값 9시간 밀림·일별 매출이 전날로, collation UNIQUE 위반, 백필 후 행 누락, `@Transactional` 무시, 배포 직후 캐시 역직렬화 실패, 57014 statement timeout, 앱은 끊었는데 DB 쿼리는 계속 돔 | 필수 | 미작성 | — |
| 57 | `db-incidents` | 실사건: GitLab DB 삭제 + 백업 5종 실패(2017-01-31) · Sentry PostgreSQL XID wraparound(2015) · GitHub MySQL 페일오버 불일치(2018-10-21 — 분산 관점은 distributed/36) | 권장 | 미작성 | — |
