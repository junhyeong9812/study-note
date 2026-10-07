# 요구사항 명세서 — data-engineering-writing

> 작성일: 2026-10-07 · 작업 폴더: `docs/plans/2026-10-07/data-engineering-writing/` · 브랜치: main(origin 92ad836a + 로컬 log 커밋 f8f8fe35)에서 `docs/data-engineering-writing`.
> 선행: architecture-writing(22편, push 92ad836a). 브리핑·도구는 architecture판을 재사용한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "다음 진행하자"
- Q/A (2026-10-07): 영역 **데이터 공학 17편**(전부 신규 — 원고 없음) · 진행 **앞 영역과 같게(영역 밖 미작성 링크 교정, 검색 한도 대비 출처 URL 사전 제공), 합의 auto**
- 추가 지시(2026-10-07): "에이전트 최대 5개씩만 사용하도록 하자" · "병렬로 순차처리 진행하자" → 동시 서브에이전트 ≤5, 한 워커가 끝나면 그 자리에 다음 단계를 이어 띄운다.

## 1. 목표·대상 (필수)

- `cs/data-engineering/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **17편**(커리큘럼 §18a 01~17). 원고 없음 — 보강 대상 0.
  - 종합 2편(16 de-symptom-index·17 de-incidents)은 마지막.
- 영역 표 `cs/data-engineering/README.md` 재생성.
- 정합 단계에서 다른 영역 노트가 data-engineering 01~17을 "미작성"으로 가리키는 곳을 **링크만** 교정.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말 없음, metadata 단계 `초안`, `흔한 오해:` 한 줄(선택).
- **I2 근거**: DDIA 1판(3·10·11·12장 — 장 단위, 절 제목은 열 수 있는 목차로만, 아니면 `[?]`), Kimball Group 공개 기법 페이지·Design Tip, Armbrust 외 CIDR 2021, Apache Iceberg Spec, Delta 프로토콜 문서, Kreps 2014, Beauchemin "Functional Data Engineering", Debezium 문서·블로그, PostgreSQL 17 문서(논리 복제·복제 슬롯·`max_slot_wal_keep_size`), MySQL binlog 문서, Kafka 문서(보존·compaction·tombstone), CloudEvents 1.0 명세, Confluent Schema Registry 호환성 문서, Bitol ODCS, OpenLineage 명세, dbt·Great Expectations 문서, GDPR 제17조(EUR-Lex), EDPB 지침, 사고 원문(Unity 2022 Q1 실적·SEC 공시, Equifax 2022-08 발표, 영국 PHE 2020-10 엑셀 사건의 공식 설명). 책 본문을 못 열면 장 단위·`[?]` — **기억으로 쓴 절·페이지·연도에는 반드시 `[?]`**.
- **I3 커리큘럼 일치**: 각 행의 요지·선행·⚠·🔧·📚 전부, 선행 링크 실재 확인.
- **I4 기존 보존**: 다른 영역 노트 수정 금지(정합 단계의 링크 교정만 예외 — 문장 의미 변경 금지).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 `sn-de-w<NN>-*`(`--rm --pull never --cpus=2 -u $(id -u):$(id -g)`(postgres·kafka 공식 이미지는 이미지 기본 사용자), `--network none` 또는 이 작업 전용 내부 네트워크), 이미지는 있는 것만(postgres:17·apache/kafka:4.1.0·mysql:8.4·eclipse-temurin:21-jdk·python:3.12-slim·node:22-*), pull·빌드·rmi·prune 금지, 볼륨은 만들면 같은 워커가 지움. 호스트 python3(표준 라이브러리)·sqlite3 가능, sudo·패키지 설치 금지. 개인정보 금지(실험 데이터는 합성), 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상(종합 선택) — 예: grain 섞인 팩트 조인으로 합계 2배·inner join 누락(postgres), SCD Type 1 vs 2 과거 리포트 변화·유효 기간 겹침 탐지, 복제 슬롯이 WAL을 붙잡는 것(`pg_replication_slots`·`pg_wal` 크기, `test_decoding`), 이벤트 시각 vs 처리 시각 자정 경계 집계, append 재실행 2배 vs 파티션 덮어쓰기 멱등, 로그 보존보다 긴 재처리 구간(kafka), 스키마 호환성 판정(필드 집합 비교 — Java/Python 모형), 성공했지만 0행 적재 탐지·행 수 EWMA, 계보 DAG 영향 분석(BFS), crypto-shredding(AES-GCM 키 폐기 후 복호 실패), 스냅샷·매니페스트 CAS 커밋 모형(작은 파일 수와 계획 시간). 측정값은 이 호스트(i7-13700HX, `--cpus=2`) 한정.
- **I8 동시성**: 동시 서브에이전트 ≤5(사용자 지시).

## 3. 기준소스 (필수)

- curriculum.md §18a, `cs/data-engineering/README.md`, I2 출처, 관련 기존 노트(database/03·04·16·19·26·30·34·37·50, distributed/04·16·17·21·22·30, domain-modeling/21, reliability/13·16, api-design/08, testing/13, data-structure/11·21·42, algorithm/12·17·18, security/03·09·27, engineering-practice/17)

## 4. 금지영역 (필수)

- data-engineering 밖 노트(정합 단계 링크 교정 제외 — 읽기만), 커리큘럼 본문(NEXT로), `check_new.py`·생성기, 생성 문서 수기 수정, 이 작업이 만들지 않은 컨테이너·볼륨·이미지·네트워크, I6의 금지 행위

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 → 판정 · V4 정합(database·distributed·reliability·security 겹치는 주제 + 영역 밖 링크) · V5 웹 교차 24+, 링크 신규 깨짐 0, 영역 표 재생성, 정리 확인(sn-de 컨테이너·볼륨·네트워크 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 17편, 사실 오류(명세 규칙·기본값·호환성 모드 정의·사고 수치) 위험. 문서라 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 실험은 로컬 이미지(postgres:17·apache/kafka:4.1.0·eclipse-temurin:21-jdk)와 python 표준 라이브러리로 새 패키지 없이 된다 — Debezium·Schema Registry·Iceberg 런타임은 없으므로 PostgreSQL 논리 디코딩(`test_decoding`)과 작은 모형 코드로 원리를 보이고, 도구 동작은 1차 문서로 대신한다.
- **A2**: WebSearch 한도가 소진돼 있을 수 있다 — 브리핑에 주요 1차 출처 URL을 미리 넣고 curl/WebFetch로 연다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑 3종(architecture판 이식 + 데이터 공학 실험 예시·출처 URL 목록) | 브리핑 |
| 02 | 집필(Opus 4워커: 01~04 · 05~08 · 09~12 · 13~15), 종합 16·17 후속 | 17 PASS |
| 03 | 사실 점검 + 실험 재실행(집필 끝난 묶음부터 이어서) | packet |
| 04 | codex 2차 → 판정 → 정합(영역 밖 링크 포함) → 웹 | V3~V5 |
| 05 | 영역 표·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-07)
- [x] auto
