# cs 인덱스

CS 지식 지도. **영역 = 커리큘럼 19영역**(번호 = 권장 학습 순서), 기존 노트는 제자리에 두고 영역 표가 링크한다 — 규칙은 [README.md](README.md) 「작성 규칙」 §6.
상태: `미작성` → `원고 있음` / `초안(Claude)` → `검수 완료` (README §4).

## 영역 (커리큘럼 19영역 — 생성 문서)

영역별 현황(미작성·원고 있음·초안·검수 완료 수)은 각 생성 문서 상단 「현황」 줄이 정본이다.

| 영역 | 이름 |
|---|---|
| [math](math/README.md) | CS 수학 |
| [data-structure](data-structure/curriculum.md) | 자료구조 |
| [algorithm](algorithm/curriculum.md) | 알고리즘 |
| [architecture](architecture/README.md) | 컴퓨터 구조 |
| [os](os/README.md) | 운영체제 |
| [language](language/README.md) | 프로그래밍 언어·컴파일러 |
| [network](network/README.md) | 네트워크 |
| [security](security/README.md) | 보안 |
| [database](database/README.md) | 데이터베이스 |
| [distributed](distributed/README.md) | 분산 시스템 |
| [reliability](reliability/README.md) | 운영·신뢰성 |
| [software-design](software-design/README.md) | 소프트웨어 설계 |
| [domain-modeling](domain-modeling/curriculum.md) | 도메인 모델링 |
| [testing](testing/README.md) | 테스트 |
| [api-design](api-design/curriculum.md) | API 설계 |
| [web-platform](web-platform/README.md) | 프론트엔드 엔지니어링 |
| [engineering-practice](engineering-practice/README.md) | 엔지니어링 실천 |
| [data-engineering](data-engineering/README.md) | 데이터 공학 |
| [data-analysis](data-analysis/README.md) | 데이터 분석·통계 |

## 기존 컬렉션 (제자리 유지)

```text
cs/
├── systems/           ← 시스템 개념 — db-engine 9주제 + jun-bank 이관(architecture-styles·orchestration·event-sourcing·multi-tenancy·clickhouse·postgres-rls·timeseries·kafka-consumer·outbox·server-design 컬렉션)
├── engineering/       ← 설계·실천 — solid-principles·clean-code·design-patterns-gof·agile-and-squad·engineering-axes·data-access·failure-point-checklist·development-standards
├── foundations/       ← CS 기초 9주제 + security 컬렉션·three-virtues (languages·web-api·python-basics는 최상위 languages/로 이동 2026-09-28)
├── algorithm/         ← 01~30 myway 컬렉션 (+ curriculum.md 영역 표)
├── data-structure/    ← 01~35 myway 컬렉션 + lsm-merge-model (+ curriculum.md)
├── domain-modeling/   ← basic/advanced myway 컬렉션 + domain-vs-application-logic·pojo (+ curriculum.md)
├── ops-patterns/      ← 01~19 myway 컬렉션 + deadline-propagation·failure-at-scale·failure-modes
└── api-design/        ← 01~06 myway 컬렉션 (+ curriculum.md)
```

myway 컬렉션의 원본 경로·진도 = [project/myway/README.md](../project/myway/README.md).

---

## 이관 이력 (2026-09-28 이전 기록 — 옛 상태 어휘 `서머리`·`질문/정답`·`검토 대기`를 그대로 둔다. 현재 상태는 영역 생성 문서가 정본)

### 진행 중 (검토·정답 대기)

| 주제 | 상태 | 원본(따라 친 노트) 위치 |
|------|------|------------------------|
| [solid-principles](engineering/solid-principles/) | 서머리 이관 + 질문 7개 작성 완료, 정답 미작성 | `jun-bank/docs/study/organize/SOLID.md` |
| [thrashing](systems/thrashing/) | **검토 대기(2026-08-23)** — 서머리·질문 5·정답(초안) — 동적 배열 resize 반복과 히스테리시스 | 직접 작성(원본 노트 = 2-summary) |
| [Hysteresis](systems/Hysteresis/) | **검토 대기(2026-08-23)** — 서머리·질문 5·정답(초안) — 방향별 임계값 분리, hysteresis band | 직접 작성(원본 노트 = 2-summary) |
| [development-standards](engineering/development-standards/) | 상세 문서+질문/정답 초안(2026-08-24) — 품질·보안·운영·법률 4축, 하위 [index](engineering/development-standards/index.md) | 원고 작성 예정 |
| [foundations/*](foundations/) | 이관 완료(2026-09-05) — 부트캠프 10주제(python-basics는 languages/로 이동 → 9), 하위 [index](foundations/index.md) | `computer_science` repo |

## jun-bank에서 공부한 주제 — 이관 완료 (2026-09-16)

jun-bank `docs/study/`의 학습 노트를 cs 골격으로 재작성해 이관했다.\
전부 **원고 문체 유지·프로젝트 고유명사 일반화**했고, 서머리·질문에 더해 **정답(3-answer) 초안까지 작성**했다(2026-09-17, 18개 주제). 정답은 Claude 초안 — **본인 검토 후 확정**한다(기존 db-engine·algorithm 3-answer와 같은 상태). 원본 백업 = `jun-bank/docs-backup-2026-09-15/study/`.

### 설계·개념 주제 (study/01~11)

| 주제 | cs 위치 | 상태 |
|------|---------|------|
| clean-code | [engineering/clean-code](engineering/clean-code/) | 서머리+질문+정답(초안) |
| design-patterns-gof | [engineering/design-patterns-gof](engineering/design-patterns-gof/) | 〃 |
| agile-and-squad | [engineering/agile-and-squad](engineering/agile-and-squad/) | 〃 |
| domain-vs-application-logic | [domain-modeling/domain-vs-application-logic](domain-modeling/domain-vs-application-logic/) | 〃 |
| architecture-styles | [systems/architecture-styles](systems/architecture-styles/) | 〃 |
| orchestration-vs-choreography | [systems/orchestration-choreography](systems/orchestration-choreography/) | 〃 |
| event-sourcing | [systems/event-sourcing](systems/event-sourcing/) | 〃 |
| multi-tenancy | [systems/multi-tenancy](systems/multi-tenancy/) | 〃 |
| failure-at-scale | [ops-patterns/failure-at-scale](ops-patterns/failure-at-scale/) | 〃 |
| failure-modes | [ops-patterns/failure-modes](ops-patterns/failure-modes/) | 〃 (F-01~25·실사건 보존) |

(solid-principles는 위 「진행 중」에 등재 — 먼저 이관됨.)

### notes 이관 (study/notes)

| 주제 | cs 위치 | 비고 |
|------|---------|------|
| engineering-axes | [engineering/engineering-axes](engineering/engineering-axes/) | 컬렉션(README+7축) — notes 00·08·axes 통합 |
| server-design | [systems/server-design](systems/server-design/) | 컬렉션(README+11) |
| lsm-merge-model | [data-structure/lsm-merge-model](data-structure/lsm-merge-model/) | 서머리+질문+정답(초안) |
| clickhouse-mergetree | [systems/clickhouse-mergetree](systems/clickhouse-mergetree/) | 〃 |
| postgres-rls | [systems/postgres-rls](systems/postgres-rls/) | 〃 |
| timeseries-resolution-tiers | [systems/timeseries-resolution-tiers](systems/timeseries-resolution-tiers/) | 〃 |
| kafka-consumer-failure | [systems/kafka-consumer-failure](systems/kafka-consumer-failure/) | 〃 |
| outbox-vs-dispatch-log | [systems/outbox-vs-dispatch-log](systems/outbox-vs-dispatch-log/) | 〃 |
| failure-point-checklist | [engineering/failure-point-checklist](engineering/failure-point-checklist/) | 절차/판단형 |
| pojo | [domain-modeling/pojo](domain-modeling/pojo/) | 서머리+질문+정답(초안) |
| three-virtues | [foundations/three-virtues](foundations/three-virtues/) | Larry Wall 원전 · 서머리+질문+정답(초안) |

### tech 이관 (study/tech — 컬렉션)

| 주제 | cs 위치 | 비고 |
|------|---------|------|
| data-access | [engineering/data-access](engineering/data-access/) | JPA·Data JDBC·비교 3편 |
| languages | [languages/](../languages/) — **최상위로 이동(2026-09-28)** | C계열·Go·JVM·Kotlin·Rust 5편 |
| security | [foundations/security](foundations/security/) | HMAC·SHA256·OIDC·JWKS·식별자·audit-rollout 6편 |

> infra 코드 결착 노트(infra-journey·go-syntax-in-our-code·gate1-auth-pattern)와 워크플로우 양식은 cs가 아니라 **`project/jun-bank/`**(infra-journey·infra-notes·workflow)로 이관했다 — 프로젝트 결착이라 일반 CS 지식이 아니다.

## db-engine-lab에서 공부한 개념 — 3파일 작성 완료, 정답은 본인 검토 후 확정 (2026-08-20)

원본은 `db-engine-lab/docs/study/`의 개념 정리 문서들. 카프카 외 BookKeeper·NAND·LSM 등이 섞여 개념 단위로 둔다.

2026-08-23: 6주제 서머리를 공통 구조로 통일 — 본문은 원고 그대로, 보강은 `*(Claude 보강)*`, 원고 외 지식은 `[Claude 추가]`로 분리.

| 주제 | 내용 | 원본 위치 |
|------|------|-----------|
| [kafka-why-fast](systems/kafka-why-fast/) | 검토 대기(2026-08-20) — 서머리·질문 7·정답(초안) | `db-engine-lab/docs/study/kafka.md` |
| [lsm-tree](systems/lsm-tree/) | 검토 대기(2026-08-20) — 서머리·질문 6·정답(초안) | `db-engine-lab/docs/study/LSM-Tree.md` |
| [nand-flash](systems/nand-flash/) | 검토 대기(2026-08-20) — 서머리·질문 7·정답(초안) | `db-engine-lab/docs/study/NAND.md` |
| [storage-media-workload](systems/storage-media-workload/) | 초안(Claude, 2026-09-14) — 서머리만 | 없음(k-brand-guard 사례) |
| [striping](systems/striping/) | 검토 대기(2026-08-20) — 서머리·질문 6·정답(초안) | `db-engine-lab/docs/study/Striping.md` |
| [straggler](systems/straggler/) | 검토 대기(2026-08-20) — 서머리·질문 6·정답(초안) | `db-engine-lab/docs/study/Straggler.md` |
| [partitioning-vs-sharding](systems/partitioning-vs-sharding/) | 검토 대기(2026-08-20) — 서머리·질문 6·정답(초안) | `db-engine-lab` Partitioning.md + Sharding.md |
