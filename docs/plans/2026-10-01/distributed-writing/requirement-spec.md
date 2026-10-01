# 요구사항 명세서 — distributed-writing

> 작성일: 2026-10-01 · 작업 폴더: `docs/plans/2026-10-01/distributed-writing/` · 브랜치: DB 커밋 뒤 `docs/db-writing`에서 `docs/distributed-writing`을 딴다(그전까지 노트는 작업 트리에서 미추적 상태로 쓴다).
> 선행 작업: network(51편)·os(38편)·db(57편, `docs/plans/2026-10-01/db-writing/` 진행 중). 도구·브리핑·교훈을 재사용한다. 머리말 정리(2026-10-01) 이후라 **제목 아래 머리말 없음 + 폴더별 metadata.md**가 새 형식이다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "병합하고 푸시한다음 다음 내용 작성 진행하자"
- Q/A (2026-10-01)
  - 영역: **분산 시스템**(`cs/distributed/`, 커리큘럼 §10)
  - 2차 리뷰: **codex high, 한도에 걸리면 Opus 적대 리뷰로 대체**(OS 방식). DB 작업의 "리셋 대기" 규칙과 다르다.
  - 로컬 재현: **Docker 임시 컨테이너 허용** — 작업이 만든 것만 쓰고 끝나면 지운다.
  - 기존 노트: **새 leaf로 보강** — 원고·예전 형식 초안은 입력으로 쓰고 원본은 그대로 둔다.
  - 추가 요청: "실제 근거가 필요하면 간단한 실험을 통해 데이터 기반으로 근거를 작성해서 설명하면 좋을 것 같아" → **실험 근거 우선**(I7)
  - 이미 정한 것(재질문 안 함): 집필 Opus, `cs/<area>/NN-slug/` 3파일 + metadata.md, 통일 골격 7절, 코드 Java·JS·TS, 검증 순서 집필 → Opus 점검 → 2차 리뷰 → 판정 → 정합 → 웹 표본

## 1. 목표·대상 (필수)

- `cs/distributed/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **36편**
  - 신규 19편: 01·02·04·06·07·08·09·11·14·19·20·25·26·28·30·32·33·34(+종합 35·36)
  - 보강 17편(기존 노트를 이어받음): 03 `ops-patterns/failure-at-scale` · 05 `ops-patterns/14-logical-clock` · 10 `ops-patterns/12-leader-election` · 12 `ops-patterns/11-distributed-lock` · 13 `ops-patterns/13-snowflake` · 15 `ops-patterns/08-saga` · 16 `ops-patterns/07-outbox` · 17 `systems/server-design/07-async-messaging.md` · 18 `systems/kafka-consumer-failure` · 21 `systems/kafka-why-fast` · 22 `systems/event-sourcing`·`ops-patterns/16-event-sourcing` · 23 `systems/orchestration-choreography` · 24 `ops-patterns/15-crdt` · 27 `systems/striping` · 29 `systems/outbox-vs-dispatch-log` · 31 `ops-patterns/18-blockchain`
  - 종합 2편(35 distributed-symptom-index·36 distributed-incidents)은 나머지를 쓴 뒤에 쓴다.
- 영역 표 `cs/distributed/README.md` 재생성: 36편 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I1 형식**: 2-summary 최상위 헤딩 7절이 순서대로 온다. Q/A 번호 일치, 6~10개. **제목 아래 머리말·표식 줄 없음**, metadata.md 단계 `초안`(날짜).
- **I2 근거**: DDIA 1판, MIT 6.5840 Spring 2026 강의, 원논문(Lamport 1978·2001, FLP 1985, Ongaro–Ousterhout 2014, Gilbert–Lynch 2002, DeCandia 2007, Corbett 2012, Shapiro 2011, Castro–Liskov 1999, Nishtala 2013 등), 제품 공식 문서·소스(etcd·ZooKeeper·Kafka·Redis 등), 사고 보고서 원문, 로컬 재현으로 확인한 것만 사실로 쓴다. 확인 못 한 것은 `[?]`. 지어낸 수치·API·사례는 0. 제품 동작은 **제품·버전**을 붙인다(예: "Kafka 4.x KRaft에서는").
- **I3 커리큘럼 일치**: curriculum.md §10 각 행의 요지·⚠·🔧·📚를 모두 다룬다. 선행 주제는 링크한다(database·network·os leaf 포함).
- **I4 기존 보존**: 원고·기존 초안·다른 영역 노트는 수정하지 않는다(링크만).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프 폴더에는 md만.
- **I7 실험 근거 우선**: 동작·수치·장애 양상처럼 실행으로 보일 수 있는 주장은 **작은 실험을 돌려 나온 데이터**로 설명한다 — 실험 코드(Java·JS·TS 또는 셸)·실행 환경(제품·버전)·실제 출력·관찰을 노트에 싣는다(예: 벽시계 vs 단조 시계 경과 시간, 램포트·벡터 시계 순서, R+W>N 정족수 읽기, etcd 리더 kill 후 재선출 시간과 term 증가, fencing token 없는 락의 이중 쓰기, Kafka acks·ISR별 유실, at-least-once 중복 소비, 2PC 코디네이터 중단 시 블로킹). 출력은 손으로 만들지 않고 실행 결과를 붙인다. 실험이 불가능하거나 과한 주장(대규모 수치·논문 증명)은 1차 출처로 대신하고 그 사실을 적는다. 편마다 실험이 가능한 핵심 주장 1개 이상을 실험으로 보인다(종합 35·36 제외).
- **I6 재현 안전**: 공용 컨테이너(etcd 3노드·Kafka·Redis)는 메인이 띄우고 이름은 `sn-dw-*`, 포트는 127.0.0.1만. 노드를 죽이거나 네트워크를 끊는 파괴 실험은 워커가 **자기 전용 일회용 컨테이너**(`sn-dw-w<NN>-*`, 전용 네트워크)를 만들어 하고 끝나면 지운다 — 공용 컨테이너는 키 접두사·토픽 이름으로 나눠 쓰기만 한다. 부하는 작게(수 초·수 개 노드). 끝나면 컨테이너·볼륨·네트워크 삭제. 기존 컨테이너는 조회만. 저장소 루트에 파일을 만들지 않고 절대 경로를 쓴다.

## 3. 기준소스 (필수)

- `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §10 각 leaf 행, `cs/distributed/README.md`
- 위 I2의 교재·강의·논문·제품 문서·소스·사고 보고서
- 원고·기존 초안: §1 보강 목록의 경로

## 4. 금지영역 (필수)

- distributed 밖 영역의 노트, 원고·기존 초안(I4), 커리큘럼 본문(필요하면 NEXT에 기록)
- 생성 문서의 수기 수정(생성기 재실행으로만)
- 진행 중인 DB 노트(`cs/database/**`)와 그 작업 기록 — 이 작업에서는 읽기만
- 이번 작업이 만들지 않은 Docker 컨테이너·볼륨·이미지(`sn-dbw-*`·`payment-codex-*` 등)

## 5. 검증 방법 (필수)

- **V1** `check_new.py`(머리말 금지·metadata 검사 포함판)
- **V1b** 실험 근거(I7): 편별 실험 목록(주장 · 코드 위치 · 환경 · 출력)을 packet에 받고, 사실 점검 워커가 편당 1개 이상을 다시 돌려 출력이 재현되는지 확인한다(비결정적 값은 범위·경향으로 대조)
- **V2** Opus 전수 사실 점검(1차 출처·로컬 재현)
- **V3** 2차 리뷰: codex(high) 전수, 한도가 차면 남은 편은 Opus 적대 리뷰. 지적은 Opus 판정 워커가 1차 출처로 재확인해 채택/기각.
- **V4** 노트 간 공통 사실 정합 재점검(DB 32·33·55 등 선행 leaf와의 정합 포함)
- **V5** 웹 교차 표본 24건 이상, linkcheck 신규 깨짐 0, 영역 README 재생성, 컨테이너 정리 확인

## 6. stakes (필수)

- 판정: **중간**
- 근거: 새 학습 자료 36편, 사실 오류 위험이 크다(앞 세 영역 모두 1차 점검 뒤에도 편당 수 건이 남음). Docker 조작은 전용 이름이라 되돌릴 수 있다.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 재현용 컨테이너(etcd 3노드·Kafka KRaft 단일·Redis)를 이 머신에서 작게 띄워 워커가 `docker exec`로 쓸 수 있다. 필요한 편이 생길 때 메인이 띄우고 스모크한다.
- **A1b**: 실험 실행 환경 — 호스트에 node 18·tsc·go·java(런타임)가 있고, 이미지 `eclipse-temurin:21-jdk`·`redis:7-alpine`이 이미 있다. Java 실험은 호스트 `java X.java`가 안 되면 temurin 21 JDK 일회용 컨테이너(`--rm`)로 돌린다. etcd·Kafka 이미지는 받아야 한다(작업 전용, 끝나면 삭제).
- **A2**: DB 작업의 codex 남은 20편과 이 작업의 리뷰가 같은 codex 한도를 나눠 쓴다 — DB를 먼저 돌리고, 이 작업은 한도가 막히면 Opus로 대체한다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(DB 것 + 분산 규칙: 제품·버전 명시, 새 형식, 재현 안전) | 브리핑 파일 |
| 02 | 집필(Opus 병렬, 워커당 5~6편), 종합 35·36은 후속 | 36 PASS |
| 03 | Opus 전수 사실 점검 | 편별 packet |
| 04 | 2차 리뷰(codex → 한도 시 Opus) → 판정 → 정합 → 웹 표본 | V3~V5 |
| 05 | README 재생성·컨테이너 삭제·커밋·(사용자 확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변 5건 + 실험 근거 요청(2026-10-01)
- [x] auto
