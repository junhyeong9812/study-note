# 갭 리서치 — 실무에서 자주 만나는데 교과서 목차에는 잘 안 나오는 CS (2026-09-28, L0)

> **대상**: [`curriculum.md`](curriculum.md) (18개 영역·517 leaf) 전체 표를 읽고 조사 항목과 대조했다.
> **범위 밖**: 성능, 디자인 패턴 카탈로그, 데이터 아키텍처, 추적성·타임아웃은 다른 워커가 맡으므로 이 문서에서 제안하지 않는다.
> **표기**: `[?]`는 이번 작업에서 원문을 직접 확인하지 못한 항목이다. slug는 curriculum.md에 **실제로 있는 것만** 적었다. 신규 slug 번호는 각 영역의 기존 최대 번호 다음부터 붙였다. 7.8b 절(network/46~52)처럼 영역 마감 leaf 뒤에 번호를 이어 붙이는 방식이다.

---

## 1. 커버 점검표

판정 기호
- **있음**: 해당 leaf가 주제의 본체다.
- **부분**: 다른 leaf 안의 한 줄이나 ⚠ 칸에만 나온다. `→ 제안 #n`이 붙은 항목은 2절에서 신규 leaf를 제안한다.
- **없음**: 어느 leaf에도 나오지 않는다.

### 1.1 데이터 표현과 값

| 항목 | 판정 | 근거 slug / 비고 |
|---|---|---|
| 시간대·DST | 부분 | `domain-modeling/11-time-money-and-units`에 시간·금액·단위가 한 leaf로 묶여 있다. DST는 ⚠ 칸의 한 줄뿐이다 → 제안 #1 |
| UTC 저장 | 부분 | 어디에도 명시되어 있지 않다. `data-analysis/23-data-cleaning-and-quality`에 "UTC/KST 혼합"이 나온다. DB 타입(`timestamptz`)은 없다 → 제안 #1·#2 |
| 윤초 | 있음 | `distributed/05-physical-clocks-and-ntp`, `os/37-os-incidents`, `distributed/32-distributed-incidents`(Cloudflare 2017) |
| 단조 시계 vs 벽시계 | 있음 | `distributed/05-physical-clocks-and-ntp`, `testing/12-testing-time-and-concurrency`(시계 주입) |
| 금액 정밀 소수·반올림 | 부분 | `architecture/03-floating-point-ieee754`의 ⚠ 칸(돈을 double로), `domain-modeling/11`(은행가 반올림 한 줄), `math/14-numerical-stability`. 배분 문제·통화 소수 자릿수·DB scale은 없다 → 제안 #3 |
| 유니코드 정규화 NFC/NFD | 있음 | `architecture/05-character-encoding-unicode` |
| 문자열 길이(코드포인트·그래핌) | 부분 | `architecture/05`에 서로게이트 절단만 있다. 그래핌 클러스터·길이 제한·대소문자 변환은 없다 → 제안 #4 |
| 인코딩 오류 | 있음 | `architecture/05`(모지바케, MySQL `utf8` 3바이트) |
| i18n/l10n | 없음 | → 제안 #6 |
| 정렬(collation) | 없음 | `algorithm/33-sorting-in-practice`는 비교자 계약만 다룬다. 로캘 collation과 DB collation은 없다 → 제안 #5 |
| UUID v7·ULID·Snowflake | 있음 | `distributed/18-distributed-id-generation`(Snowflake·UUIDv7), `security/16-identifiers-and-enumeration`(UUIDv4/v7·ULID), `database/12-btree-indexes`(랜덤 UUID PK 페이지 분할) |
| 공개 ID와 내부 ID | 부분 | `security/16`(열거 방지), `api-design/09-schema-and-serialization`(64비트 JSON 정밀도). 대리키·자연키·공개 ID를 한곳에서 판단하는 leaf는 없다 → 제안 #7 |

### 1.2 DB 운영

| 항목 | 판정 | 근거 slug / 비고 |
|---|---|---|
| 무중단 배포 + 스키마 마이그레이션(expand/contract) | 있음 | `database/34-schema-migration`, `reliability/27-deployment-strategies`(신·구 버전 공존) |
| 대용량 백필 | 부분 | `database/34`의 ⚠ 칸에 "백필이 복제 지연 유발" 한 줄만 있다. 청크·스로틀·재시작·검증은 없다 → 제안 #8 |
| 소프트 삭제 | 없음 | → 제안 #9 |
| 낙관적·비관적 락의 앱 코드 표현 | 있음 | `database/24-occ-and-timestamp-ordering`, `database/25-app-level-concurrency-patterns`, `api-design/13-concurrency-control-in-apis` |
| 트랜잭션 경계와 외부 호출 | 부분 | `database/20-transactions-acid`·`database/25`의 ⚠ 칸, `distributed/21-outbox-and-dual-write`. 프레임워크 선언적 트랜잭션의 함정(프록시·전파·커밋 후 훅)은 없다 → 제안 #10 |

### 1.3 캐시

| 항목 | 판정 | 근거 slug / 비고 |
|---|---|---|
| cache-aside·write-through | 있음 | `database/38-caching-with-databases` |
| write-behind | 부분 | 이름이 나오지 않는다. `database/38`에서 한 절로 흡수할 수 있는 크기다 |
| 무효화 | 있음 | `database/38`, `distributed/30-distributed-cache-consistency`, `network/40-cdn-and-edge` |
| 스탬피드 | 있음 | `reliability/13-cache-stampede` |
| TTL 지터 | 부분 | `reliability/13`의 "눈사태"와 "확률적 조기 만료"에 포함된다. 지터라는 말은 `reliability/07`(재시도)에만 나온다 |
| (추가 발견) 캐시 키 버전·직렬화 호환 | 없음 | 배포 직후 캐시 역직렬화 실패는 흔한 사고인데 다루는 leaf가 없다 → 제안 #11 |

### 1.4 배포와 운영

| 항목 | 판정 | 근거 slug / 비고 |
|---|---|---|
| 설정 관리 | 있음 | `software-design/22-configuration-and-12factor` |
| 비밀 관리 | 있음 | `security/09-randomness-and-key-management`(KMS·회전·하드코딩 유출) |
| 기능 플래그 | 부분 | `reliability/27`과 `engineering-practice/05-branching-strategies`의 요지에 한 단어로만 나온다. 플래그 수명·부채·기본값 정책은 없다 → 제안 #12 |
| 카나리·블루그린 | 있음 | `reliability/27-deployment-strategies`, `testing/17-testing-in-production` |
| 스케줄 잡 중복 실행 방지 | 있음 | `reliability/15-scheduler-and-cron-ha` |
| 배치 잡 재시작·체크포인트 | 부분 | `reliability/15`는 "미실행 보정"까지만 다룬다. 청크 커밋·재시작 지점·부분 실패 보고는 없다 → 제안 #13 |

### 1.5 파일과 알림

| 항목 | 판정 | 근거 slug / 비고 |
|---|---|---|
| 대용량 파일 업로드 | 있음 | `network/50-large-file-upload-patterns`, `network/49-range-requests-and-resume` |
| 대용량 CSV 스트리밍 파싱·인코딩 감지 | 없음 | → 제안 #14 |
| 이메일·알림 재시도·중복 방지 | 부분 | 일반 원리는 `reliability/12-idempotency`와 `distributed/21`에 있다. 알림 발송 도메인(수신 거부·바운스·선호 설정)은 없다 → 제안 #16 |
| SPF/DKIM/DMARC | 없음 | → 제안 #15 |

### 1.6 보안과 트래픽

| 항목 | 판정 | 근거 slug / 비고 |
|---|---|---|
| 세션 vs JWT 함정 | 있음 | `security/11-sessions-and-cookie-security`, `security/12-tokens-and-jwt`, `security/13-jwks-and-key-rotation` |
| 토큰 갱신(refresh·회전·재사용 탐지) | 부분 | `security/12`의 ⚠ 칸에 "폐기 불가"만 있다. refresh token 회전·동시 갱신 경합·BFF는 없다 → 제안 #17 |
| RBAC/ABAC/ReBAC | 있음 | `security/15-access-control-models` |
| 레이트 리밋 알고리즘 | 있음 | `reliability/10-rate-limiter`, `security/26-dos-and-abuse` |
| 레이트 리밋 계약(키 선택·429·헤더·쿼터) | 부분 | `reliability/10`의 📚에 RFC 6585만 있다 → 제안 #18 |

### 1.7 그 밖의 실무 주제

| 항목 | 판정 | 근거 slug / 비고 |
|---|---|---|
| 전문 검색·형태소 | 부분 | `data-structure/32-inverted-index`(⚠에 "한국어 형태소" 한 줄), `database/14-filters-and-specialized-indexes`(`LIKE '%x%'`) → 제안 #19 |
| 자동완성 | 부분 | `data-structure/09-trie`의 🔧 칸에 한 단어로만 나온다 → 제안 #20 |
| (추가 발견) 검색 인덱스와 DB 동기화·재색인 | 없음 | → 제안 #21 |
| 동시 편집·충돌 해결 | 부분 | `distributed/12-conflict-resolution-and-crdt`, `api-design/13`(ETag), `data-structure/28-rope`. OT와 실시간 협업 편집은 없다 → 제안 #22 |
| 멀티테넌시 | 있음 | `software-design/19-multi-tenancy`, `database/35-row-level-security` |
| 감사 로그 | 있음 | `security/25-security-logging-and-audit` |
| PII 마스킹·로그 유출·보관·파기 | 부분 | `security/25`의 ⚠ 칸(로그에 PII 기록), `engineering-practice/15-legal-standards` → 제안 #23 |
| 시맨틱 버저닝·lockfile | 있음 | `language/17-modules-and-dependency-resolution` |
| 공급망 보안 | 있음 | `security/24-supply-chain-security`, `web-platform/13-web-incidents`(polyfill.io) |
| 의존성 업데이트 운영(Renovate·EOL 런타임) | 부분 | 위 두 leaf에서 한 절로 흡수할 수 있다. 신규 제안은 하지 않는다 |
| 코드 리뷰와 PR 크기 | 있음 | `engineering-practice/06-code-review` |
| 기술 부채 | 있음 | `engineering-practice/10-technical-debt` |
| 레거시 개선(Strangler) | 부분 | `testing/16-characterization-tests-legacy`, `domain-modeling/15-anti-corruption-layer`. Strangler Fig·branch by abstraction·병행 실행 비교는 없다 → 제안 #24 |
| 문서화(ADR) | 있음 | `software-design/21-architecture-decision-records`, `engineering-practice/11-documentation-practices` |
| 포스트모템 | 있음 | `reliability/29-incident-response-and-postmortem` |
| 런북 | 부분 | `engineering-practice/11`의 ⚠ 칸에 "낡은 런북" 한 줄만 있다. 런북 구조·운영 준비도 점검은 없다 → 제안 #25 |
| 에러 메시지·로깅 레벨 설계 | 부분 | `reliability/23-logging`(레벨 한 단어), `api-design/04-error-format-problem-details`, `software-design/07-error-handling-design`. 레벨의 의미 정책과 사용자용·개발자용 메시지 분리는 없다 → 제안 #26 |
| (추가 발견) 원장·대사(reconciliation) | 없음 | `api-design/19-case-settlement-report`와 `21-case-refund`는 사례뿐이다. 복식부기 원장과 외부 PG 대사를 다루는 원리 leaf가 없다 → 제안 #28 |

### 1.8 개념이 아니라 판단

| 항목 | 판정 | 근거 slug / 비고 |
|---|---|---|
| 성능 vs 가독성 | 부분 | `software-design/20-quality-attributes-and-tradeoffs`, `software-design/03-deep-modules-and-abstraction`. **성능 워커 범위와 겹치므로 제안을 보류한다** |
| 빌드 vs 구매 | 부분 | `domain-modeling/13-subdomains`의 ⚠ 칸("일반 서브도메인 자체 구현")뿐이다. 총소유비용·종료 비용·벤더 종속 판단은 없다 → 제안 #27 |
| 모놀리스 vs MSA 전환 시점 | 있음 | `software-design/18-monolith-vs-microservices`(모듈러 모놀리스·분산 모놀리스). "언제 쪼개나"는 이 leaf의 한 절로 충분하다고 판단했다 |

**합계**: 조사 항목 56개 중 있음 27 · 부분 24 · 없음 5. 추가 발견 3건(캐시 키 버전, 검색 동기화, 원장·대사)은 모두 "없음"이다. 이 3건을 뺀 수치다.

---

## 2. 신규 leaf 제안 (28개)

영역별로 모았다. `#` 번호는 1절의 "→ 제안 #n"과 3절 상위 10에서 참조한다.

### 2.1 데이터베이스 (`database/`) — 9.8 "애플리케이션과 DB" 뒤에 새 단원 "9.8b 실무 데이터 운영"을 둔다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 41-temporal-types-and-session-timezone | `timestamp` vs `timestamptz`·`DATETIME` vs `TIMESTAMP`, 세션 시간대, 드라이버 변환, 시간대 기준 `date_trunc` | 20-transactions-acid, 04-sql-joins-and-aggregation, distributed/05-physical-clocks-and-ntp | JVM·DB·세션 시간대가 서로 달라 저장값이 9시간 밀림(KST↔UTC). 일별 집계를 UTC 자정으로 잘라 한국 기준 매출이 전날로 넘어감. MySQL `TIMESTAMP` 2038-01-19 상한 (#2) | epoch 정수 표현, 구간 경계 계산 | PostgreSQL 문서 "Date/Time Types" 8.5 · MySQL 문서 "The DATE, DATETIME, and TIMESTAMP Types" · RFC 3339 | 필수 | 신규 (연결: `data-analysis/23-data-cleaning-and-quality`) |
| 42-collation-and-text-comparison | collation(대소문자·악센트 무시), 정렬 순서, 유니크 제약과 비교 규칙, ICU vs libc | 13-index-design, architecture/05-character-encoding-unicode | `_ci` collation에서 `a@x.com`과 `A@x.com`이 UNIQUE 위반, 또는 반대로 중복 허용. 앱 정렬과 DB `ORDER BY`가 달라 커서 페이지네이션에서 누락·중복 발생. **glibc 2.28 collation 변경 후 PG 인덱스 조용한 손상**(복제본·업그레이드) | 정렬 키 생성(UCA 다단계 가중치), B+Tree 비교 함수 | Unicode UTS #10 (UCA) https://www.unicode.org/reports/tr10/ · PostgreSQL wiki "Locale data changes" https://wiki.postgresql.org/wiki/Locale_data_changes · MySQL 문서 "Character Sets and Collations" | 필수 | 신규 (연결: `api-design/06-pagination`) |
| 43-key-strategy-surrogate-natural-public-id | 대리키 vs 자연키, bigint vs UUIDv4/v7, 내부 PK와 외부 노출 ID 분리, 접두어 ID(`cus_…`) | 12-btree-indexes, security/16-identifiers-and-enumeration, distributed/18-distributed-id-generation | 자연키(이메일·주민번호)를 PK로 써서 값이 바뀌자 FK 연쇄 수정. 순차 PK 노출 → 열거·사업 규모 노출. UUIDv4 PK → 삽입 페이지 분할·버퍼 풀 적중률 하락. 64비트 ID를 JSON 숫자로 → 끝자리 변형 | 비트 필드(시간+랜덤), B+Tree 삽입 지역성 | RFC 9562 · Stripe "Designing APIs for humans: Object IDs" (dev.to, 2022 [?]) | 필수 | 신규 (연결: `api-design/09-schema-and-serialization`) |
| 44-large-backfill-and-batch-dml | 대량 UPDATE·DELETE·백필: keyset 청크, 스로틀(복제 지연 기준), 재시작 가능성, 전후 행 수 검증 | 34-schema-migration, 29-replication-leader-follower, 23-mvcc | 단일 `UPDATE … WHERE` 1억 행 → 락·undo 폭증·복제 지연 수십 분. `LIMIT` 청크를 offset으로 돌려 **행 누락이나 중복 처리가 에러 없이 끝남**. 중단 후 재실행 시 이미 처리한 행을 다시 변환(비멱등). PG 대량 DELETE → bloat | keyset 범위 스캔, 체크포인트 커서 | Stripe "Online migrations at scale" 2017 https://stripe.com/blog/online-migrations · gh-ost https://github.com/github/gh-ost | 필수 | 신규 (연결: `systems/server-design/08-deployment-ops.md` 마이그레이션 절) |
| 45-soft-delete-and-data-lifecycle | `deleted_at` 소프트 삭제, 부분 유니크 인덱스, 기본 필터 누락, 아카이브 테이블, 보관 기한과 하드 삭제 | 02-keys-and-constraints, 13-index-design | 삭제한 회원 이메일로 재가입 시 UNIQUE 위반. 쿼리 한 곳에서 `deleted_at IS NULL` 누락 → 삭제된 데이터 노출. FK가 소프트 삭제 행을 가리켜 고아 참조. 삭제 요청 법정 기한을 넘겨도 원본이 남음 | 부분 인덱스(술어 인덱스) | Brandur "Soft deletion probably isn't worth it" 2022 https://brandur.org/soft-deletion · PostgreSQL 문서 "Partial Indexes" | 필수 | 신규 (연결: `security/30-pii-classification-masking-retention`) |
| 46-transaction-boundaries-in-app-code | 선언적 트랜잭션(프록시·자기 호출), 전파 속성, readOnly, 롤백 규칙, 커밋 후 훅, 트랜잭션 안 외부 호출 금지 | 20-transactions-acid, 32-connection-pooling, distributed/21-outbox-and-dual-write | 같은 클래스 내부 호출이라 `@Transactional`이 **조용히 무시**됨. checked 예외는 기본적으로 롤백되지 않아 반쯤 커밋됨. 트랜잭션 안 HTTP 호출 3초 → 커넥션 풀 고갈 `Connection is not available`. `REQUIRES_NEW` 남용 → 같은 행 자기 교착 | 호출 스택별 트랜잭션 컨텍스트(스레드 로컬 스택) | Spring Framework 문서 "Declarative Transaction Management" · "Transaction Propagation" · DDIA 7장 | 필수 | 신규 (연결: `engineering/data-access`) |
| 47-cache-key-versioning-and-serialization | 캐시 키 설계(네임스페이스·테넌트·버전), 값 직렬화 스키마 호환, null 캐싱, 핫 키, TTL 지터, write-behind 위험 | 38-caching-with-databases, api-design/08-versioning-and-compatibility | 배포 직후 구 버전 객체를 역직렬화하지 못해 `SerializationException`, 캐시 전부 미스 → DB 폭주. 키에 테넌트·로캘 누락 → 다른 사용자 데이터 반환. 같은 TTL 일괄 적재 → 동시 만료 눈사태. write-behind 큐 유실 → 조용한 데이터 손실 | 해시 기반 키, 난수 지터(math/11) | AWS Builders' Library "Caching challenges and strategies" https://aws.amazon.com/builders-library/caching-challenges-and-strategies/ · Nishtala 외 NSDI 2013 | 필수 | 신규 (연결: `reliability/13-cache-stampede`) |
| 48-bulk-file-import-export | CSV·엑셀 입출력: RFC 4180 인용 규칙, 스트리밍 파싱, 인코딩 감지(UTF-8·BOM·CP949), 행 단위 오류 보고, 부분 적재 정책, CSV 수식 주입 | 44-large-backfill-and-batch-dml, architecture/05-character-encoding-unicode, network/48-chunked-and-streaming-responses | 엑셀에서 연 UTF-8 CSV(BOM 없음)가 한글 깨짐. 한국 사용자가 올린 CP949 파일을 UTF-8로 읽어 `MalformedInputException` 또는 �. 파일 전체를 메모리에 적재 → OOM. 필드 안 줄바꿈·따옴표 → 열 밀림. `=HYPERLINK(…)` 셀 → 다운로드한 관리자 PC에서 수식 실행. 3만 행 중 10행 실패를 알리지 않음 | 상태 기계 파서(인용 상태), 유계 버퍼 스트리밍 | RFC 4180 · OWASP "CSV Injection" https://owasp.org/www-community/attacks/CSV_Injection · WHATWG Encoding Standard | 필수 | 신규 |
| 49-full-text-search-and-analyzers | 분석기(토크나이저·필터), 한국어 형태소(nori) vs n-gram, BM25 관련도, 동의어 | 14-filters-and-specialized-indexes, data-structure/32-inverted-index | "삼성전자"로 "삼성" 검색 누락, 또는 n-gram 과다 매칭으로 무관한 결과. 색인 분석기와 검색 분석기 불일치 → 0건. 사전 갱신 후 재색인 누락. `LIKE '%…%'` 풀스캔 | 역색인, BM25 점수, 형태소 분석(격자 위 최단 경로·비터비) | Manning 외 『Introduction to Information Retrieval』 2·6장 · Robertson–Zaragoza 2009 "The Probabilistic Relevance Framework: BM25 and Beyond" · Elasticsearch 문서 "Korean (nori) analysis plugin" | 권장 | 신규 |
| 50-autocomplete-and-typeahead | 접두사 완성, edge n-gram, 인기도 순위, 한글 자모·초성 분해, 디바운스·캐시 | 49, data-structure/09-trie | "ㅅㅁ"(초성)이나 조합 중인 "삼ㅅ" 입력에 결과 없음(자모 미분해). 키 입력마다 요청 → 검색 클러스터 QPS 폭증. 늦게 온 이전 응답이 최신 결과를 덮어씀(요청 순서 역전) | 트라이·FST, top-k 힙, 한글 음절 = 초·중·종성 산술 조합 | Unicode Standard 3.12 "Conjoining Jamo Behavior" [?] · Elasticsearch 문서 "search_as_you_type" · Lucene FST [?] | 권장 | 신규 (연결: `web-platform/05-fetch-from-browser` 중단) |
| 51-search-index-sync-and-reindexing | DB→검색 인덱스 동기화(이중 쓰기 vs CDC), 지연·불일치 감지, 별칭 교체로 무중단 재색인 | 49, distributed/21-outbox-and-dual-write | 이중 쓰기 중 검색 쪽 실패 → 삭제된 상품이 검색에 계속 노출. 매핑 변경을 제자리 재색인 → 검색 공백. 재색인 중 들어온 변경 유실 | CDC 로그 재생, 별칭(포인터 원자 교체) | Elasticsearch 문서 "Aliases" · "Reindex API" · Kleppmann DDIA 11장 (파생 데이터) | 권장 | 신규 |

### 2.2 도메인 모델링 (`domain-modeling/`) — 13.2 전술 설계 뒤, 11번에서 가지를 친다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 22-instant-vs-local-time-and-tz-rules | Instant·LocalDateTime·LocalDate 구분, 미래 일정은 "현지 시각 + tz ID"로 저장, DST 공백·중복, tzdata 갱신, 기간(Period)과 지속시간(Duration) | 11-time-money-and-units, distributed/05-physical-clocks-and-ntp | 미래 예약을 UTC로 저장했는데 해당 국가가 DST 규칙을 바꿔 1시간 어긋남. "매월 31일" 정기 결제가 2월에 누락. DST 전환일 02:30 알람이 없거나 두 번 울림. 생일(날짜)을 자정 UTC 타임스탬프로 저장 → 해외 사용자에게 하루 전으로 표시. 2월 29일 처리 버그(Zune 2008, Azure 2012) | 구간 연산, tz 전이 테이블 이진 탐색 | Jon Skeet "Storing UTC is not a silver bullet" 2019 · IANA tz database https://www.iana.org/time-zones · RFC 9557 · Java `java.time` 문서 | 필수 | 신규 (연결: `testing/12-testing-time-and-concurrency`) |
| 23-money-arithmetic-rounding-allocation | 정밀 소수·통화별 소수 자릿수(ISO 4217), 반올림 모드와 **반올림 위치**, 배분(1원 나머지 처리), 세금·할인 계산 순서, 직렬화 | 11-time-money-and-units, architecture/03-floating-point-ieee754 | 10,000원을 3명에게 나누면 3,333×3 = 9,999로 1원 소실. 줄 단위 반올림 vs 합계 후 반올림 차이 → PG 금액과 주문 금액 불일치로 결제 거절. JPY(0자리)·KWD(3자리)를 소수 2자리로 가정. `BigDecimal("1.0").equals("1.00")`이 false라 중복 판정 실패 | 최대 잔여 배분(largest remainder), 고정 소수점 정수 | Fowler 『PoEAA』 Money(allocation) · ISO 4217 · Java `RoundingMode`·`BigDecimal` 문서 | 필수 | 신규 (연결: `advanced/05-multi-currency`) |
| 24-ledger-and-reconciliation | 복식부기 원장(불변 분개·잔액 = 분개 합), 외부 PG·은행과의 대사, 차이 분류와 조정 분개 | 23, 10-state-machines-in-domain, distributed/21-outbox-and-dual-write | 잔액 컬럼만 UPDATE → 이력이 없어 불일치 원인 추적 불가. 결제는 PG에서 승인됐는데 우리 DB는 실패(타임아웃) → 대사 없이 방치돼 고객 이중 청구. 대사 배치 날짜 경계(시간대)가 달라 매일 가짜 차이 발생 | append-only 로그, 두 집합 조인·차집합(정렬 병합) | Square "Books, an immutable double-entry accounting database service" 2019 https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/ · Fowler 『Analysis Patterns』 Account [?] | 권장 | 신규 (연결: `api-design/19-case-settlement-report`, `21-case-refund`) |

### 2.3 컴퓨터 구조 (`architecture/`) — 4.1 데이터 표현에 05 다음으로 넣는다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 23-text-length-segmentation-and-case | 길이의 4가지 뜻(바이트·UTF-16 단위·코드포인트·그래핌), 안전한 자르기, 대소문자 변환·케이스 폴딩의 로캘 의존, 혼동 문자 | 05-character-encoding-unicode | "10자 제한" 검증(JS `length`)과 DB `VARCHAR(10)`(MySQL 문자 수 vs PG) 기준이 달라 저장 실패. 이모지·국기(🇰🇷 = 코드포인트 2개)를 중간에서 잘라 깨진 미리보기. 터키 로캘 `"TITLE".toLowerCase()` → `tıtle`로 비교 실패. 정규화가 멱등이 아닌 사용자명 → **계정 탈취(Spotify 2013)** | 그래핌 경계 상태 기계, 가변 길이 역방향 탐색 | Unicode UAX #29 "Text Segmentation" https://www.unicode.org/reports/tr29/ · UTS #39 "Unicode Security Mechanisms" · Spotify Engineering "Creative usernames and Spotify account hijacking" 2013 | 필수 | 신규 |

### 2.4 웹 플랫폼 (`web-platform/`)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 14-internationalization-and-localization | 로캘 협상(`Accept-Language`·BCP 47), 메시지 카탈로그, 복수형 규칙, 숫자·통화·날짜 서식, RTL, 이름·주소 가정 | 05-fetch-from-browser, architecture/05-character-encoding-unicode, network/33-http-semantics | 문자열 이어 붙이기로 번역 → 어순이 다른 언어에서 문장 붕괴. "1 items"류 복수형 오류. 서버 로캘 기본값으로 `1,234.5`와 `1.234,5`가 뒤바뀌어 금액 파싱 오류. 이름을 성·이름 2칸으로 강제 → 가입 불가 | CLDR 복수형 규칙(술어 평가), 로캘 폴백 체인 | Unicode CLDR https://cldr.unicode.org/ · ICU MessageFormat 문서 · RFC 5646 (BCP 47) · McKenzie "Falsehoods Programmers Believe About Names" 2010 | 권장 | 신규 |

### 2.5 네트워크 (`network/`) — 7.6 DNS 뒤에 둔다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 53-email-delivery-and-authentication | SMTP 전달 경로, SPF·DKIM·DMARC(DNS TXT), 정렬(alignment), 바운스·수신 거부, 대량 발송자 요건 | 27-dns-resolution, security/06-public-key-and-signatures | SPF 10회 DNS 조회 한도 초과 → `permerror`로 스팸함 행. 발송 대행사 도메인과 From 도메인이 정렬되지 않아 DMARC 실패. DKIM 키 회전 중 DNS 레코드 선삭제 → 전량 거부. 2024년부터 Gmail·Yahoo 대량 발송 요건(원클릭 수신 거부) 미충족 → 거절 | DNS TXT 파싱, RSA/Ed25519 서명(헤더 정규화) | RFC 5321 · RFC 7208 (SPF) · RFC 6376 (DKIM) · RFC 7489 (DMARC) · RFC 8058 · Google "Email sender guidelines" https://support.google.com/a/answer/81126 | 권장 | 신규 |

### 2.6 API 설계 (`api-design/`) — 15.2 신뢰성 계약 뒤에 둔다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 27-notification-delivery-pipeline | 이메일·SMS·푸시 발송 파이프라인: outbox → 큐 → 공급자, 멱등 발송 키, 재시도 vs 영구 실패 구분, 억제 목록(바운스·수신 거부), 사용자 선호·야간 발송 제한, 푸시 토큰 무효화 | 05-idempotency-keys, 12-async-apis-and-webhooks, distributed/26-consumer-failure-handling | 재시도로 같은 알림 3번 발송. 트랜잭션 롤백됐는데 "주문 완료" 메일은 발송됨. 하드 바운스 주소에 계속 발송 → 발송 평판 하락으로 전체 도달률 붕괴. 만료된 FCM/APNs 토큰 누적 → 발송 실패율 상승. 광고성 정보를 야간(21~08시)에 발송 → 정보통신망법 위반 [?] | 재시도 큐 + 지수 백오프, 억제 목록 해시 셋 | Standard Webhooks 명세 [?] · Firebase Cloud Messaging 문서 "Manage registration tokens" · 방송통신위원회 "불법 스팸 방지 안내서" [?] | 필수 | 신규 (연결: `api-design/20-case-delivery-webhook`) |
| 28-rate-limit-and-quota-contracts | 제한 키 선택(사용자·API 키·IP·테넌트), 429와 `Retry-After`, `RateLimit` 헤더, 요금제 쿼터 vs 보호용 스로틀, 클라이언트 동작 계약 | 03-status-codes-for-apis, reliability/10-rate-limiter | IP 기준 제한 → 회사 NAT 뒤 수백 명이 한꺼번에 차단. `Retry-After` 없는 429 → 클라이언트가 즉시 재시도해 폭주. 로그인 엔드포인트를 전역 한도에 묶어 공격 중 정상 사용자 로그인 불가. 테넌트 하나가 공유 한도를 독점 | 토큰 버킷, 키별 카운터 해시 | RFC 6585 · RFC 9110 §10.2.3 (Retry-After) · IETF draft-ietf-httpapi-ratelimit-headers (-11, 2026-05, 초안) https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/ · Stripe "Scaling your API with rate limiters" 2017 | 권장 | 신규 |

### 2.7 보안 (`security/`) — 8.3 인증·인가, 8.5 공급망·운영 뒤에 둔다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 29-refresh-token-rotation-and-revocation | access·refresh 수명 설계, refresh 회전과 재사용 탐지, 동시 갱신 경합, 전체 로그아웃·강제 만료, 브라우저 저장 위치와 BFF | 12-tokens-and-jwt, 11-sessions-and-cookie-security | 탭 여러 개가 동시에 refresh → 회전된 토큰 재사용으로 판정돼 **정상 사용자 전원 로그아웃**. 비밀번호 변경 후에도 기존 refresh 토큰 유효. 긴 수명 access 토큰 탈취 → 만료까지 무방비. localStorage 저장 → XSS 한 번에 탈취 | 토큰 패밀리(체인) 추적, 폐기 목록(TTL 해시) | RFC 9700 (OAuth 2.0 Security BCP, 2025) · RFC 6749 §6 · IETF draft "OAuth 2.0 for Browser-Based Applications" [?] | 필수 | 신규 (연결: `web-platform/06-browser-storage`) |
| 30-pii-classification-masking-retention | 데이터 분류, 마스킹·토큰화·가명화, 로그·트레이스·에러 리포트 유출 차단(redaction), 보관 기한과 파기(백업 포함), 운영 데이터를 테스트에 복제 금지 | 25-security-logging-and-audit, 09-randomness-and-key-management | 요청 바디 전체 로깅 → 카드번호·주민번호가 로그 수집기와 외부 SaaS로 복제. 예외 메시지에 이메일 포함 → Sentry 등 에러 트래커에 노출. 탈퇴 회원 데이터가 백업·분석 DW에 영구 잔존. 운영 DB 덤프로 스테이징 구성 → 스테이징 유출이 실유출이 됨 | 형식 보존 토큰화, 키 파기로 삭제(crypto-shredding) | NIST SP 800-122 · OWASP Logging Cheat Sheet · GDPR Art. 17 · 개인정보보호위원회 "가명정보 처리 가이드라인" [?] | 필수 | 신규 (연결: `engineering-practice/15-legal-standards`) |

### 2.8 운영·신뢰성 (`reliability/`) — 11.5 배포·변경·사고 대응 뒤에 둔다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 35-feature-flag-lifecycle | 플래그 유형(릴리스·운영 킬 스위치·실험·권한), 평가 일관성, 플래그 서비스 장애 시 기본값, 제거 부채 | 27-deployment-strategies, engineering-practice/05-branching-strategies | 재사용한 오래된 플래그가 죽은 코드를 되살림(Knight Capital 2012). 플래그 서버 장애 → 기본값이 "켜짐"이라 미완성 기능 전면 노출. 요청마다 평가가 달라 한 화면 안에서 신·구 UI 혼재. 수백 개 방치 플래그 → 조합 테스트 불가 | 결정적 해시 버킷(사용자 → %), 규칙 트리 평가 | Hodgson "Feature Toggles (aka Feature Flags)" https://martinfowler.com/articles/feature-toggles.html · SEC 명령 34-70694 (Knight Capital) | 필수 | 신규 (연결: `engineering-practice/18-practice-incidents`) |
| 36-batch-job-restart-and-checkpoint | 배치 설계: 청크 커밋·체크포인트, 멱등 재실행, 실행 이력(잡 저장소), 부분 실패 보고, 크론 시간대·DST, 배포와 장시간 잡 공존 | 15-scheduler-and-cron-ha, 12-idempotency, database/44-large-backfill-and-batch-dml | 중간 실패 후 처음부터 재실행 → 앞부분 이중 정산. 실패 행을 스킵하고 "COMPLETED"로 끝남(**부분 실패 성공 위장**). DST 전환일에 `0 2 * * *` 잡이 누락되거나 두 번 실행. 배포 SIGTERM에 잡이 죽어 락만 남음 | 체크포인트 커서, 실행 상태 기계 | Spring Batch 문서 "Configuring a Step"(재시작·skip) · Kubernetes 문서 "CronJob"(`concurrencyPolicy`·`timeZone`·`startingDeadlineSeconds`) | 필수 | 신규 (연결: `api-design/19-case-settlement-report`) |
| 37-runbooks-and-operational-readiness | 런북 구조(증상·확인 명령·완화·에스컬레이션), 알람 → 런북 링크, 출시 전 운영 준비도 점검(PRR), 온콜 인수인계 | 29-incident-response-and-postmortem, 26-alerting-and-on-call | 새벽 알람에 런북이 없어 담당자 호출까지 30분. 런북 명령이 구 인프라 기준이라 실행 시 2차 사고. 출시 후 대시보드·알람이 없어 고객 문의로 장애 인지 | 결정 트리(증상 분기) | SRE Workbook "On-Call" [?] · SRE 32장 "The Evolving SRE Engagement Model"(PRR) [?] · PagerDuty Incident Response 문서 https://response.pagerduty.com/ | 권장 | 신규 (연결: `engineering-practice/11-documentation-practices`) |

### 2.9 소프트웨어 설계 (`software-design/`) — 12.5 아키텍처 뒤에 둔다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 25-legacy-migration-strangler-fig | Strangler Fig, branch by abstraction, 병행 실행·결과 비교(shadow), 라우팅 전환과 되돌리기, 빅뱅 재작성의 위험 | 18-monolith-vs-microservices, testing/16-characterization-tests-legacy, domain-modeling/15-anti-corruption-layer | 전면 재작성 2년 → 구·신 기능 격차로 전환 불가·중단. 신규 경로와 레거시가 같은 테이블에 이중 쓰기 → 불일치. 비교 없이 전환 → 레거시의 문서화 안 된 동작(반올림·정렬) 소실 | 라우팅 테이블(기능별 전환 비율), 결과 diff | Fowler "StranglerFigApplication" https://martinfowler.com/bliki/StranglerFigApplication.html · Fowler "BranchByAbstraction" · GitHub Scientist https://github.com/github/scientist | 권장 | 신규 |
| 26-error-messages-and-log-level-policy | 로그 레벨의 조작적 정의(ERROR = 사람 조치 필요, WARN = 자동 복구됨 등), 사용자용·개발자용 메시지 분리, 에러 코드 체계, 한 번만 로깅 | 07-error-handling-design, reliability/23-logging, api-design/04-error-format-problem-details | 예상된 4xx(검증 실패)를 ERROR로 기록 → 알람 피로로 진짜 장애 무시. catch-log-rethrow 계층마다 반복 → 스택 트레이스 5중 기록. 사용자에게 SQL 에러 원문 노출(정보 누출). "오류가 발생했습니다"만 표시 → 고객 문의로 원인 역추적 불가 | 에러 코드 → 메시지 맵 | RFC 5424 §6.2.1 (severity) · OWASP Error Handling Cheat Sheet · OWASP Logging Cheat Sheet | 필수 | 신규 |

### 2.10 분산 시스템 (`distributed/`) — 10.3 복제·일관성, 12번 뒤에 둔다

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 33-collaborative-editing-ot-and-sequence-crdt | 실시간 공동 편집: OT(변환 함수·중앙 서버) vs 시퀀스 CRDT(RGA·Yjs), 오프라인 병합, 프레즌스·커서 | 12-conflict-resolution-and-crdt, data-structure/28-rope | 두 사용자 동시 입력 후 문서가 사용자마다 다르게 수렴(변환 함수 버그). 오프라인 병합 시 문단이 섞여 끼워짐(interleaving). tombstone 누적 → 문서 크기·메모리 증가 | 변환 함수, 위치 식별자 트리, 벡터 시계 | Ellis–Gibbs SIGMOD 1989 · Figma "How Figma's multiplayer technology works" 2019 · Kleppmann 외 "Local-first software" Onward! 2019 | 심화 | 신규 |

### 2.11 엔지니어링 실천 (`engineering-practice/`)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 19-build-vs-buy-and-adoption | 직접 만들기 vs SaaS·OSS 도입: 핵심·범용 판별, 총소유비용(운영·온콜 포함), 종료 비용·데이터 반출, 벤더 종속, OSS 건강도(유지보수자·라이선스) | 03-estimation-and-planning, domain-modeling/13-subdomains, security/24-supply-chain-security | 인증·결제·검색을 자체 구현해 핵심 기능 개발 인력을 소진. 반대로 핵심 차별화 기능을 SaaS에 의존 → 가격 인상·API 폐기 시 대안 없음. 라이선스 변경(예: 오픈소스 → 소스 공개 라이선스 전환) 후 대응 불가 | 의사결정 행렬(가중합) | Fowler "UtilityVsStrategicDichotomy" https://martinfowler.com/bliki/UtilityVsStrategicDichotomy.html · OpenSSF Scorecard https://securityscorecards.dev/ | 권장 | 신규 |

**영역별 합계**: database 11 · domain-modeling 3 · architecture 1 · web-platform 1 · network 1 · api-design 2 · security 2 · reliability 3 · software-design 2 · distributed 1 · engineering-practice 1 = **28**. 등급은 필수 17 · 권장 10 · 심화 1이다.

---

## 3. 실무 빈도 상위 10 — 먼저 채울 것

판단 기준은 세 가지다. ① 1~3년 차 백엔드가 **첫 해에 거의 확실히 만나는가** ② **에러 없이 틀리는가**(silent failure — 발견이 늦고 피해가 쌓인다) ③ 다른 제안이 이 leaf를 선행으로 쓰는가.

| 순위 | # | slug | 이유 |
|---|---|---|---|
| 1 | 10 | database/46-transaction-boundaries-in-app-code | 스프링·JPA 실무에서 가장 흔한 "트랜잭션이 안 걸려 있었다" 사고다. 자기 호출과 checked 예외 비롤백은 **조용히** 틀린다. 커넥션 풀 고갈 장애의 대표 원인이기도 하다 |
| 2 | 1 | domain-modeling/22-instant-vs-local-time-and-tz-rules | 국내 서비스도 해외 사용자, 서버 UTC, 정산일 경계 때문에 반드시 만난다. 표준 교재 목차에는 없다 |
| 3 | 2 | database/41-temporal-types-and-session-timezone | #1과 짝이다. "9시간 밀림"과 "일별 매출이 전날로 넘어감"은 한국 개발자가 가장 먼저 겪는 시간 버그다 |
| 4 | 3 | domain-modeling/23-money-arithmetic-rounding-allocation | 결제·정산이 있는 모든 서비스에서 1원 차이가 대사 실패와 CS로 이어진다. 기존 leaf 11은 시간과 묶여 있어 깊이가 부족하다 |
| 5 | 8 | database/44-large-backfill-and-batch-dml | 신입이 운영 DB에서 처음 사고를 내는 전형적인 작업이다. 락과 복제 지연이 생기고, **행 누락이 에러 없이 끝난다** |
| 6 | 23 | security/30-pii-classification-masking-retention | 로그 유출은 법적 책임(개인정보보호법)으로 직결된다. 모든 서비스가 해당하고 발견은 늦다 |
| 7 | 26 | software-design/26-error-messages-and-log-level-policy | 매일 쓰는 코드인데 정책이 없어 알람 피로·로그 폭증·정보 누출이 동시에 생긴다. 학습 비용이 작고 효과는 즉시 나타난다 |
| 8 | 9 | database/45-soft-delete-and-data-lifecycle | 거의 모든 CRUD 서비스가 도입한다. 재가입 UNIQUE 충돌과 필터 누락 노출은 반복되는 사고다. PII 파기(#23)와도 맞물린다 |
| 9 | 13 | reliability/36-batch-job-restart-and-checkpoint | 정산·집계 배치는 한국 백엔드의 기본 업무다. "부분 실패인데 COMPLETED"는 silent failure의 대표 사례다 |
| 10 | 14 | database/48-bulk-file-import-export | 관리자 엑셀 업로드·다운로드는 거의 모든 B2B·백오피스에 있다. CP949·BOM 한글 깨짐과 CSV 수식 주입은 국내 실무 빈출 주제다 |

차순위는 #17 refresh 토큰 회전, #11 캐시 키 버전·직렬화, #12 기능 플래그 수명, #5 collation이다. #5는 빈도는 중간이지만 glibc 사례처럼 **조용한 인덱스 손상**이라 피해 규모가 크다.

---

## 4. 확인하지 못한 것 (`[?]`)

- 알림 야간 발송 제한 조항(정보통신망법 제50조 계열)의 정확한 조문과 시간대, 방송통신위원회 안내서의 현행 판본.
- 개인정보보호위원회 "가명정보 처리 가이드라인"의 최신 개정 연도.
- Standard Webhooks 명세의 현행 URL과 버전.
- IETF "OAuth 2.0 for Browser-Based Applications" 초안의 현재 상태(RFC 발행 여부).
- Stripe "Designing APIs for humans: Object IDs"의 원 게시 위치와 연도. 검색 결과 dev.to의 게시 계정이 현재 원 저자와 다르게 나온다.
- Unicode Standard의 Conjoining Jamo 절 번호(3.12), Lucene FST 문서 위치.
- SRE Workbook "On-Call" 장 번호, SRE 책 32장 제목의 정확성.
- Fowler 『Analysis Patterns』의 Account 패턴 장 위치.
- 신규 slug 번호는 각 영역의 마감 leaf(역색인·실사건) **뒤**에 붙였다. 통합할 때 번호를 다시 매길지, 각 영역 역색인(예: `database/39-db-symptom-index`)의 ⚠ 증상 목록에 새 증상을 추가할지는 통합 워커가 결정해야 한다.

### 이번 작업에서 확인한 외부 근거
- RateLimit 헤더 초안의 현재 상태(-11, 2026-05, 아직 Internet-Draft): https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
- Square Books(2019-10-16): https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/
- Spotify 사용자명 정규화 계정 탈취(2013-06): https://engineering.atspotify.com/2013/06/creative-usernames
- Stripe 접두어 객체 ID(2012년부터 사용): https://dev.to/4thzoa/designing-apis-for-humans-object-ids-3o5a
