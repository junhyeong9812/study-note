# cs 인덱스

프로젝트 무관 CS·설계 지식의 주제 목록.
상태: `서머리` → `질문/정답` → `복습중`. 기준 문서 위치는 주제마다 사용자가 지정한다.

## 진행 중

| 주제 | 상태 | 원본(따라 친 노트) 위치 |
|------|------|------------------------|
| [solid-principles](solid-principles/) | 서머리 이관 + 질문 7개 작성 완료, 정답 미작성 | `jun-bank/docs/study/organize/SOLID.md` |

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

## 후보 (db-engine-lab에서 공부한 개념 — 이관 대기, 폴더·3파일 스켈레톤 생성 2026-08-20)

원본은 `db-engine-lab/docs/study/`의 날짜 분리 노트가 아닌 개념 정리 문서들. 카프카 외에도 BookKeeper·NAND·LSM 등이 섞여 있어 카프카 폴더로 묶지 않고 개념 단위로 둔다(이후 카프카 문서가 늘면 `kafka-` 접두어로 모인다).

| 주제 | 내용 | 원본 위치 |
|------|------|-----------|
| [kafka-why-fast](kafka-why-fast/) | **서머리 완료(2026-08-20)** — 왜 빠른가 서사 + zero-copy 경로 + 용어 + 대안. SSD 내부(FTL·GC·WAF) 절은 nand-flash로 분리 예정 | `/home/jun/project/db-engine-lab/docs/study/kafka.md` |
| [lsm-tree](lsm-tree/) | LSM-Tree와 RUM Conjecture | `/home/jun/project/db-engine-lab/docs/study/LSM-Tree.md` |
| [nand-flash](nand-flash/) | NAND 플래시 동작 원리 | `/home/jun/project/db-engine-lab/docs/study/NAND.md` |
| [striping](striping/) | Striping — ledger를 여러 Bookie에 나눠 담기 (BookKeeper) | `/home/jun/project/db-engine-lab/docs/study/Striping.md` |
| [straggler](straggler/) | Straggler 문제와 대응 | `/home/jun/project/db-engine-lab/docs/study/Straggler.md` |
| [partitioning-vs-sharding](partitioning-vs-sharding/) | Partitioning vs Sharding | `/home/jun/project/db-engine-lab/docs/study/Partitioning.md`, `/home/jun/project/db-engine-lab/docs/study/Sharding.md` (둘을 한 주제로 합침) |
