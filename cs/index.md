# cs 인덱스

프로젝트 무관 CS·설계 지식의 주제 목록.
상태: `서머리` → `질문/정답` → `복습중`. 기준 문서 위치는 주제마다 사용자가 지정한다.

## 진행 중

| 주제 | 상태 | 원본(따라 친 노트) 위치 |
|------|------|------------------------|
| [solid-principles](engineering/solid-principles/) | 서머리 이관 + 질문 7개 작성 완료, 정답 미작성 | `jun-bank/docs/study/organize/SOLID.md` |
| [thrashing](systems/thrashing/) | **검토 대기(2026-08-23)** — 서머리(직접 작성, 소제목 정리)·질문 5·정답(초안) — 동적 배열 resize 반복과 히스테리시스 | 직접 작성(원본 노트 = 2-summary) |
| [Hysteresis](systems/Hysteresis/) | **검토 대기(2026-08-23)** — 서머리(직접 작성, 소제목 정리)·질문 5·정답(초안) — 방향별 임계값 분리, hysteresis band, thrashing과의 구분 | 직접 작성(원본 노트 = 2-summary) |
| [development-standards](engineering/development-standards/) | 상세 문서+질문/정답 초안(2026-08-24) — 품질(ISO 25010)·보안(OWASP Top10/ASVS·NIST SSDF)·운영(ISO 20000-1·Google SRE)·법률(개인정보보호법+관련 법령) 4축, 하위 [index](engineering/development-standards/index.md) | 원고 작성 예정(기준 문서는 각 서머리 관련 자료) |

## 후보 (jun-bank에서 공부한 주제 — 이관 대기)

| 주제 | 원본 위치 |
|------|-----------|
| clean-code | `jun-bank/docs/study/organize/CLEAN_CODE.md` |
| domain-vs-application-logic | `jun-bank/docs/study/03-domain-vs-application-logic/` |
| design-patterns-gof | `jun-bank/docs/study/04-design-patterns-gof/` |
| architecture-styles | `jun-bank/docs/study/05-architecture-styles/` |
| orchestration-vs-choreography | `jun-bank/docs/study/06-orchestration-vs-choreography/` |
| event-sourcing | `jun-bank/docs/study/08-event-sourcing/` |
| multi-tenancy | `jun-bank/docs/study/09-multi-tenancy/` |
| failure-at-scale / failure-modes | `jun-bank/docs/study/10-failure-at-scale/`, `11-failure-modes/` |
| tech (data-access·infra·languages·security) | `jun-bank/docs/study/tech/` — 직접 작성 예정 |

## db-engine-lab에서 공부한 개념 — 3파일 작성 완료, 질문·정답은 Claude 초안이라 본인 검토 후 확정 (2026-08-20)

원본은 `db-engine-lab/docs/study/`의 날짜 분리 노트가 아닌 개념 정리 문서들. 카프카 외에도 BookKeeper·NAND·LSM 등이 섞여 있어 카프카 폴더로 묶지 않고 개념 단위로 둔다(이후 카프카 문서가 늘면 `kafka-` 접두어로 모인다).

2026-08-23: 6주제 서머리를 공통 구조로 통일 — 본문은 원고 그대로, 원고에 없던 문장은 `*(Claude 보강)*` 표시, 원고 외 지식은 맨 아래 `[Claude 추가] 더 알면 좋은 것` 절로 분리(partitioning-vs-sharding의 「한 표로」「Kafka 연결」, kafka-why-fast의 §2 데이터 경로 다이어그램은 Claude 작성분으로 표시/이동).

| 주제 | 내용 | 원본 위치 |
|------|------|-----------|
| [kafka-why-fast](systems/kafka-why-fast/) | **검토 대기(2026-08-20)** — 서머리·질문 7·정답(초안) — 왜 빠른가 서사 + zero-copy 경로 + 용어 + 대안 | `/home/jun/project/db-engine-lab/docs/study/kafka.md` |
| [lsm-tree](systems/lsm-tree/) | **검토 대기(2026-08-20)** — 서머리·질문 6·정답(초안) | `/home/jun/project/db-engine-lab/docs/study/LSM-Tree.md` |
| [nand-flash](systems/nand-flash/) | **검토 대기(2026-08-20)** — 서머리·질문 7·정답(초안) — NAND.md + kafka.md SSD 내부 절(FTL·매핑·RMW·GC·WAF) 합침 | `/home/jun/project/db-engine-lab/docs/study/NAND.md` |
| [striping](systems/striping/) | **검토 대기(2026-08-20)** — 서머리·질문 6·정답(초안) | `/home/jun/project/db-engine-lab/docs/study/Striping.md` |
| [straggler](systems/straggler/) | **검토 대기(2026-08-20)** — 서머리·질문 6·정답(초안) | `/home/jun/project/db-engine-lab/docs/study/Straggler.md` |
| [partitioning-vs-sharding](systems/partitioning-vs-sharding/) | **검토 대기(2026-08-20)** — 서머리·질문 6·정답(초안) — Partitioning.md + Sharding.md 합침 | `/home/jun/project/db-engine-lab/docs/study/Partitioning.md`, `/home/jun/project/db-engine-lab/docs/study/Sharding.md` (둘을 한 주제로 합침) |
