# 집필 브리핑 — 커리큘럼 leaf 새 노트 (데이터 공학, 2026-10-07)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/os/19-deadlock/`, `cs/architecture/12-cache-organization/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §18a 데이터 공학 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §18a 머리 문단(흐름, "파이프라인은 초록인데 숫자가 틀린" 장애 모양, temporal 테이블·DB 타임아웃은 database에 둔다)도 읽는다.
- **이 영역의 목표**: 백엔드 개발자가 "데이터를 옮기고 다시 계산할 때 숫자가 조용히 어긋나는 이유"로 배운다. 각 편은 ⚠ 칸의 증상(합계 2배·과거 숫자 소급 변경·0행 적재·디스크 가득 등)에서 출발해 모델·파이프라인 원리로 내려갔다가, SQL·코드·진단 쿼리로 돌아온다.
- **원고 없음** — 17편 모두 신규. 커리큘럼 '기존' 칸의 "연결"·"흡수" 대상은 먼저 읽고 링크한다(되풀이하지 않는다).
- **겹치는 기존 노트(먼저 읽고 링크)**: `cs/database/{03-normalization,04-sql-joins-and-aggregation,16-mvcc,19-wal-and-logging,26-schema-migration,30-caching-with-databases,34-large-backfill-and-batch-dml,37-row-vs-column-storage,50-temporal-and-bitemporal-tables}`, `cs/distributed/{04-physical-clocks-and-ntp,16-outbox-and-dual-write,17-queues-logs-and-delivery-semantics,21-kafka-internals,22-event-sourcing,30-batch-and-stream-processing}`, `cs/domain-modeling/21-cqrs`, `cs/reliability/{13-idempotency,16-metrics-and-golden-signals}`, `cs/api-design/08-schema-and-serialization`, `cs/testing/13-contract-testing`, `cs/security/{03-symmetric-encryption-and-aead,09-randomness-and-key-management,27-pii-classification-masking-retention}`, `cs/engineering-practice/17-legal-standards`. **자료구조·알고리즘은 커리큘럼 번호 ≠ 폴더 번호**(예: 커리큘럼 `data-structure/42-interval-tree`, `algorithm/12-hash-functions`·`17-bfs`·`18-dfs`) — 대응표 `cs/data-structure/curriculum.md`·`cs/algorithm/curriculum.md`로 실제 폴더를 찾는다. `data-analysis/18`은 아직 미작성 → `../../data-analysis/README.md`로.
- **근거와 열 수 있는 1차 출처(검색 한도 대비 — 주소를 알고 curl/WebFetch로 직접 연다)**:
  - DDIA 1판: 본문은 열 수 없다 — 장 단위로 인용하고, 절 제목은 열 수 있는 목차(출판사 페이지 https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ 등)로 확인될 때만. 못 하면 `[?]`.
  - Kimball Group 기법: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/ (하위 페이지: grain, fact table types, additive facts, conformed dimensions, type-0~7) · Design Tip #152 https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/
  - Lakehouse: Armbrust 외 CIDR 2021 https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf · Apache Iceberg Spec https://iceberg.apache.org/spec/ · Delta 프로토콜 https://raw.githubusercontent.com/delta-io/delta/master/PROTOCOL.md
  - Kreps 2014 https://www.oreilly.com/radar/questioning-the-lambda-architecture/ · Marz 2011 http://nathanmarz.com/blog/how-to-beat-the-cap-theorem.html
  - Beauchemin "Functional Data Engineering" https://maximebeauchemin.medium.com/functional-data-engineering-a-modern-paradigm-for-batch-data-processing-2327ec32c42a (연도는 원문에서 확인)
  - Debezium: https://debezium.io/documentation/reference/stable/features.html · PostgreSQL connector https://debezium.io/documentation/reference/stable/connectors/postgresql.html · 블로그 https://debezium.io/blog/2021/10/07/incremental-snapshots/
  - PostgreSQL 17: 논리 디코딩 https://www.postgresql.org/docs/17/logicaldecoding-explanation.html · `test_decoding` https://www.postgresql.org/docs/17/test-decoding.html · 복제 설정(`max_slot_wal_keep_size`) https://www.postgresql.org/docs/17/runtime-config-replication.html · `pg_replication_slots` https://www.postgresql.org/docs/17/view-pg-replication-slots.html
  - MySQL 8.4 binlog 옵션(`binlog_expire_logs_seconds`) https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html (403이면 Internet Archive)
  - Kafka 문서(보존·compaction·tombstone) https://kafka.apache.org/documentation/
  - CloudEvents 1.0.2 https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md (raw: https://raw.githubusercontent.com/cloudevents/spec/v1.0.2/cloudevents/spec.md)
  - Confluent "Schema Evolution and Compatibility" https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html · Bitol ODCS https://bitol-io.github.io/open-data-contract-standard/ (버전은 원문에서)
  - OpenLineage Object Model https://openlineage.io/docs/spec/object-model
  - Monte Carlo "What is Data Observability"(5 pillars) https://www.montecarlodata.com/blog-what-is-data-observability/ · dbt data tests https://docs.getdbt.com/docs/build/data-tests · Great Expectations https://docs.greatexpectations.io/
  - GDPR 제17조 https://eur-lex.europa.eu/eli/reg/2016/679/oj (또는 https://gdpr-info.eu/art-17-gdpr/ — 2차 사본임을 밝힌다) · EDPB 지침 목록 https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en · event-driven.io https://event-driven.io/en/gdpr_in_event_driven_architecture/
  - Dehghani 2019 https://martinfowler.com/articles/data-monolith-to-mesh.html
  - 사고(17): Unity 2022 Q1 실적·SEC 공시(https://investors.unity.com/ · https://www.sec.gov/ EDGAR) · Equifax 2022-08 신용점수 오류 발표(Equifax 보도자료·CFPB 자료) · 영국 PHE 2020-10 엑셀 사건(gov.uk 공식 설명) — 원문을 못 열면 Internet Archive, 그래도 못 열면 `[?]`.
- WebSearch는 한도 소진일 수 있다 — 위 주소를 먼저 쓰고, 못 열면 Internet Archive(`https://web.archive.org/web/2024/<URL>`)를 시도한다. 그래도 못 열면 `[?]`. **기억으로 쓴 절·페이지·연도·버전 번호에는 반드시 `[?]`**를 붙인다.

## 2. 출력 — `cs/data-engineering/<NN-slug>/`의 4파일

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-07 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# data-engineering/<NN-slug> — <한 줄 제목> — 정리 (힌트)

## 해결하는 문제
## 동작·원리
## 쓰이는 자료구조·알고리즘
## 적용 — 풀어나가는 법
## 장애 시나리오와 대처
## 핵심 문장
## 관련 주제·근거
```

- 최상위 `## ` 헤딩은 이 7개만, 이 순서로 둔다(하위는 `###`). 실험 절은 `## 동작·원리`나 `## 적용` 안의 `### 실험: …`로 둔다.
- **해결하는 문제**: 이것이 없으면 무엇이 안 되나. 쉬운 예 → "똑같은 구조다" → 실무 예.
- **동작·원리**: 중심. ASCII 그림 먼저(원천 → 파생 흐름, 스타 스키마, grain 표, SCD 행 변화 타임라인, WAL·슬롯·LSN, 이벤트 봉투, 세 시각 축, Lambda/Kappa 경로, 파티션 덮어쓰기, 호환성 행렬, 관측 5축, 계보 DAG, 키 폐기, Hub/Link/Satellite, 매니페스트 트리), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 🔧 칸의 구조·알고리즘을 적고 기존 노트로 링크(대응표로 실제 폴더).
- **적용 — 풀어나가는 법**: 실무 순서: 증상(숫자 어긋남·지표) → 모델·파이프라인 원인 → SQL·코드·진단 쿼리로 확인. 코드는 Java 21·SQL(PostgreSQL 17) 기본, 파이프라인 모형은 Java 또는 Python 표준 라이브러리. 진단 쿼리(`pg_replication_slots`, `pg_ls_waldir()`, `count(*)` 대조, 기간 겹침 검사 SQL) 출력 읽기.
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(어느 숫자가 어떻게 어긋나나·지표·로그) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(이번 새 노트 `../NN-slug/2-summary.md`, 아직 없는 같은 영역 주제는 `../README.md`, 다른 영역은 실제 경로 확인), 문서 URL·명세 절, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`. 헷갈리기 쉬운 용어에만 그 아래 `    - 흔한 오해: …` 한 줄(근거 있는 오해만).
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java 21(기본)·SQL·JS·TS. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스 경로·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건. (가장 많은 지적 유형)
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M, 실험 출력과 해석. 다 쓰고 스스로 대조.
- **도구·버전 한정**: "PostgreSQL 17에서", "Debezium 문서(stable) 기준", "Kafka 4.1 기본값", "Confluent Schema Registry의 BACKWARD는…". 도구마다 다른 동작을 일반 원리로 쓰지 않는다(예: Iceberg vs Delta vs Hudi, Avro vs Protobuf 호환성 규칙).
- **모형 ≠ 실물**: 파이썬 모형으로 보인 것(호환성 판정·매니페스트 CAS·워터마크)은 "모형"이라고 쓰고, 실제 도구 동작은 1차 문서로 따로 뒷받침한다.
- **원인 확정은 근거로**: 숫자가 어긋난 원인을 실험이 직접 보이지 않았으면 "해석"·"후보"라고 쓴다. 한 호스트·작은 데이터 측정을 일반화하지 않는다.
- **법·규제는 원문 그대로**(GDPR 조항 번호·문구), 해석은 "해석", 법률 조언처럼 단정하지 않는다.
- **사고 보고서의 날짜·수치는 원문 그대로**, 해석은 "해석"이라고 표시.

## 4. (원고 없음)

- 이 영역은 원고가 없다. 대신 커리큘럼 '기존' 칸의 연결 노트(domain-modeling/21, database/30·26·34·50, engineering-practice/17, security/27)와 `distributed/16`의 CDC 한 줄(05가 흡수)을 읽고, 겹치는 설명은 링크 + 한두 줄 요약으로 둔다. 다른 영역 노트의 오류를 발견하면 고치지 말고 packet에 보고.

## 5. 실험 근거 (명세 I7 — 필수)

- 편마다 실행으로 보일 수 있는 핵심 주장 1개 이상(종합 16·17 선택). 예:
  - 01: 원천 로그를 폴드해 파생 테이블 재구축(같은 결과) vs 파생본을 원천처럼 고친 뒤 재구축하면 수정이 사라짐(postgres 또는 Java).
  - 02: 같은 집계를 행 저장 테이블에서 돌릴 때 OLTP 쿼리 지연 변화(작게, 비율), ELT에서 변환 실패 행을 조용히 건너뛰면 합계가 운영과 어긋남.
  - 03: grain이 다른 두 팩트 조인으로 합계 2배, 차원 키 누락 + inner join으로 매출 감소(에러 없음) vs left join + "Unknown" 행.
  - 04: SCD Type 1 덮어쓰기 뒤 지난달 지역별 매출 변화, Type 2 유효 기간 겹침·빈틈 탐지 SQL(`tstzrange` `&&`·`EXCLUDE` 제약).
  - 05: `postgres:17 -c wal_level=logical`에서 `pg_create_logical_replication_slot(…,'test_decoding')`·`pg_logical_slot_get_changes`, 소비하지 않는 슬롯이 `pg_wal`을 붙잡는 것(`pg_current_wal_lsn`·`restart_lsn` 차·`pg_ls_waldir()` 크기), `max_slot_wal_keep_size`로 슬롯이 `lost`가 됨. 데이터는 수십 MB 이내.
  - 06: 이벤트 시각 vs 처리 시각으로 일별 집계(자정 경계, 타임존), 이벤트 ID 없는 재전송 중복 vs ID 기반 dedup.
  - 07: Kafka(`apache/kafka:4.1.0`, 전용 네트워크·단일 노드 KRaft) 보존보다 긴 재처리 → 앞 오프셋이 사라짐(`retention.ms` 작게) — 어렵거나 무거우면 Java 모형 + Kafka 문서로 대신하고 밝힌다.
  - 08: append 재실행 2배 vs 파티션 덮어쓰기(DELETE+INSERT 한 트랜잭션 또는 교체) 멱등, 백필이 현재 규칙으로 과거를 바꾸는 것.
  - 09: 필드 집합 비교로 BACKWARD/FORWARD/FULL 판정 모형(Confluent 문서의 규칙표와 대조), 이름 바뀐 컬럼이 하류에서 NULL이 되는 재현.
  - 10: 성공했지만 0행 적재를 행 수 검사·EWMA로 잡기, 신선도 지표.
  - 11: 계보 DAG BFS로 영향 범위, 컬럼 수준 계보.
  - 12: crypto-shredding — 주체별 AES-GCM 키 폐기 후 복호 실패(JDK `javax.crypto`), 원본 삭제 후 파생 복제본에 남은 행 찾기.
  - 13: 비즈니스 키 정규화 누락으로 Hub 행 2개(해시 키), Satellite 조인 수.
  - 14: 매니페스트 트리·스냅샷·CAS 커밋 모형(동시 커밋 충돌·재시도), 작은 파일 수 vs 계획 시간(모형).
  - 15: 실험 선택(데이터 제품 계약·소유자 필드 검증 정도).
- 노트에 싣는 것: 실험 코드 핵심, 환경(호스트·이미지 버전), **실제 출력**, 관찰과 해석. 비결정 값은 여러 번 돌린 범위.
- 실험으로 보일 수 없는 주장은 1차 출처로 대신하고 그 사실을 적는다. packet에 실험 목록.

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요하면 **자기 전용 일회용 컨테이너**: 이름 `sn-de-w<NN>-*`, `--rm`, `--cpus=2` 이하, 가능하면 `--network none`(postgres는 컨테이너 안에서 `psql`로 접속하면 네트워크 불필요). 두 컨테이너가 통신해야 하면 `docker network create sn-de-w<NN>-net --internal`로 만들고 끝나면 지운다. **이미 있는 이미지만**(`postgres:17`, `apache/kafka:4.1.0`, `mysql:8.4`, `eclipse-temurin:21-jdk`, `python:3.12-slim`, `node:22-alpine`·`node:22-bookworm-slim`) — **이미지 받기(`pull`)·빌드·`rmi`·`prune` 금지**(실행은 `--pull never`). 볼륨은 가능하면 만들지 않는다(익명 볼륨은 `--rm`으로 같이 지워진다). 끝나면 `docker ps -a --filter name=sn-de-w<NN>`·`docker network ls --filter name=sn-de`가 비었는지 확인.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 외부 라이브러리는 쓰지 않는다(JDK만). JDBC 드라이버가 없으므로 DB 실험은 `psql`(postgres 컨테이너 안)로 한다.
- **호스트 도구**: python3(표준 라이브러리·sqlite3 모듈)만. **sudo·패키지 설치 금지**(pip·apt·npm install 포함). 실험은 수십 초~몇 분 이내·메모리 1GB 이하.
- **데이터**: 합성 데이터만(사람 이름·이메일·전화번호 같은 실제 개인정보 금지 — `user_001` 형식).
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/de/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.** 컨테이너는 `-u`로 돌려 root 소유 파일을 남기지 않는다(postgres·kafka 공식 이미지는 바인드 마운트 없이 쓰고, 결과는 `docker exec … psql` 출력을 호스트 파일로 리다이렉트).
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다.
- **프로세스**: 자기 PID만 종료(`pkill -f` 금지).
- **금지**: `sn-arch-*`·`sn-math-*`·`payment-*`·`jun-bank-*`·`text-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·네트워크·이미지는 건드리지 않는다.

## 7. 하지 말 것

- 담당 폴더 밖 파일(다른 영역·커리큘럼·README 등)을 수정하지 않는다. git은 조회만.
- 리프 폴더에는 md만(1-question·2-summary·3-answer·metadata).
- 하위 에이전트·fork 금지.

## 8. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>` → 전부 PASS(머리말 금지·metadata 검사 포함).
- §3-1 노트 안 모순 자기 대조. 실험 출력과 본문·정답의 수치가 같은지 대조.

## 9. 반환 packet

- 폴더 목록과 check 결과
- 편별 주요 근거(문서 URL·명세 절·논문)
- **실험 목록**(주장 · 코드 경로 · 명령 · 환경 · 출력 요지) + 전용 컨테이너·네트워크를 지웠는지
- `[?]` 목록, 커리큘럼 ⚠ 칸 커버 여부, 미완료 항목
