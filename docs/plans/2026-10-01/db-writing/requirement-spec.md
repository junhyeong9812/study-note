# 요구사항 명세서 — db-writing

> 작성일: 2026-10-01 · 작업 폴더: `docs/plans/2026-10-01/db-writing/` · 브랜치: `docs/db-writing`(main d43fa61a)
> 선행 작업: `docs/plans/2026-09-30/network-writing/`(51편), `docs/plans/2026-09-30/os-writing/`(38편) — 도구·브리핑·교훈을 재사용한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "진행하자" (OS 완료 보고에서 "다음 영역(DB)은 새 명세부터"에 대한 답)
- Q/A (2026-10-01)
  - 범위: **57편 전부** — 미작성 48편은 새로 쓰고, 원고가 있는 6편·기존 초안 3편은 새 leaf 폴더로 보강한다(원본은 그대로 두고 링크로 이어받음, OS 방식).
  - 로컬 재현: **Docker 임시 DB 컨테이너 허용** — PostgreSQL 17·MySQL 8.4. 이번 작업 전용 이름, 127.0.0.1 포트, 끝나면 삭제. 기존 컨테이너는 건드리지 않는다.
  - 2차 리뷰: **codex high로, 한도가 모자라면 리셋까지 대기**한다. Opus 대체는 쓰지 않는다.
  - OS에서 이미 정한 것(재질문 안 함): 집필 모델 Opus, `cs/<area>/NN-slug/` 3파일, 통일 골격 7절, 코드 Java·JS·TS(SQL은 SQL로), "Claude 초안" 표기, 검증 순서 집필 → Opus 점검 → 2차 리뷰 → 판정 → 일관성 → 웹 표본

## 1. 목표·대상 (필수)

- `cs/database/NN-slug/{1-question,2-summary,3-answer}.md` **57편**
  - 미작성 48편: 영역 표에서 `미작성`인 행 전부
  - 원고 보강 6편: 32 replication-leader-follower · 23 orm-and-n-plus-one · 26 schema-migration · 30 caching-with-databases · 43 row-level-security · 45 clickhouse-mergetree. 원고(`systems/server-design/*`, `engineering/data-access`, `systems/postgres-rls`, `systems/clickhouse-mergetree`)가 다룬 부분은 링크로 이어받고, 빈 곳을 채운다.
  - 초안 보강 3편: 38 lsm-storage-engine · 33 partitioning-and-sharding · 44 timeseries-resolution-tiers(기존 `systems/*` 초안을 이어받음)
  - 종합 2편(56 db-symptom-index·57 db-incidents)은 나머지를 쓴 뒤에 쓴다.
- 영역 표 `cs/database/README.md` 재생성: 57편 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I1 골격**: 2-summary 최상위 헤딩 7절이 순서대로 온다. Q/A 번호 일치, 6~10개.
- **I2 근거**: PostgreSQL·MySQL 공식 문서, 소스(postgres/postgres, mysql/mysql-server), CMU 15-445 강의, DDIA, 논문(Berenson 1995, ARIES 등), 로컬 재현으로 확인한 것만 사실로 쓴다. 확인 못 한 것은 `[?]`. 지어낸 수치·API·사례는 0. **DB마다 동작이 다르다** — "PostgreSQL 17에서는 / MySQL 8.4 InnoDB에서는"처럼 제품·버전을 붙이고, 한 제품의 동작을 일반 규칙처럼 쓰지 않는다.
- **I3 커리큘럼 일치**: curriculum.md §9 각 행의 요지·⚠·🔧·📚를 모두 다룬다. 선행 주제는 링크한다.
- **I4 기존 보존**: 원고·기존 초안·다른 영역 노트는 수정하지 않는다(링크만).
- **I5 링크·트리**: 노트가 새로 깨는 링크 0, 리프 폴더에는 md만.
- **I6 재현 안전**
  - 컨테이너는 메인이 띄운다. 이름은 `sn-dbw-pg`·`sn-dbw-my`, 포트는 127.0.0.1만 연다. 워커는 `docker exec`로 자기 전용 DB/스키마만 쓴다.
  - 부하 상한: 데이터 수만~수십만 행, 쿼리 수 초 이내, 동시 세션 몇 개.
  - 끝나면 컨테이너와 볼륨을 삭제한다. 기존 컨테이너·볼륨·네트워크는 조회만 한다.
  - 저장소 루트에 파일을 만들지 않는다. 작업 경로는 절대 경로로 쓴다(OS 사고 교훈).

## 3. 기준소스 (필수)

- `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §9 각 leaf 행, `cs/database/README.md`
- PostgreSQL 17 문서·소스, MySQL 8.4 Reference Manual·소스, CMU 15-445 Fall 2024, DDIA 1판, Berenson 외 1995, Mohan ARIES 1992
- 원고·기존 초안: `cs/systems/server-design/{03-data-layer,04-caching,08-deployment-ops}.md`, `cs/engineering/data-access`, `cs/systems/{postgres-rls,clickhouse-mergetree,lsm-tree,partitioning-vs-sharding,timeseries-resolution-tiers}`

## 4. 금지영역 (필수)

- DB 밖 영역의 노트, 원고·기존 초안(I4), 커리큘럼 본문(필요하면 NEXT에 기록)
- 생성 문서의 수기 수정(생성기 재실행으로만)
- 이번 작업이 만들지 않은 Docker 컨테이너·볼륨·이미지(`payment-codex-*` 등)

## 5. 검증 방법 (필수)

- **V1** `check_new.py`(network-writing의 것을 재사용)
- **V2** Opus 전수 사실 점검(1차 출처·로컬 재현)
- **V3** 2차 리뷰: codex(high) 전수. 한도가 차면 리셋까지 기다렸다 이어서 한다. 지적은 Opus 판정 워커가 1차 출처로 재확인해 채택/기각한다.
- **V4** 노트 간 공통 사실 일관성 재점검
- **V5** 웹 교차 표본 24건 이상, linkcheck 노트 신규 깨짐 0, 영역 README 재생성, 컨테이너 정리 확인(`docker ps -a` 목록)

## 6. stakes (필수)

- 판정: **중간**
- 근거: 새 학습 자료 57편이고 사실 오류 위험이 크다(두 영역 모두 1차 점검 뒤에도 편당 수 건이 남음). 로컬 Docker 조작이 있지만 전용 이름이고, 되돌릴 수 있다.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 임시 컨테이너 두 개(PG 17·MySQL 8.4)를 띄워 워커 여러 개가 동시에 `docker exec`로 쓸 수 있다. 착수 직후 스모크로 확인한다.
- **A2**: codex high 한도는 한 번에 약 9~10편이다(OS 실측). 따라서 57편 2차 리뷰는 리셋을 여러 번 기다려야 한다. 대기 중에는 판정·다른 단계를 병행한다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 컨테이너 기동·스모크(A1), 브리핑(OS 것 + DB 규칙: 제품·버전 명시, 재현 안전, 절대 경로) | 스모크 기록 |
| 02 | 집필(Opus 병렬, 워커당 5~6편), 종합 56·57은 후속 | 57 PASS |
| 03 | Opus 전수 사실 점검 | 편별 packet |
| 04 | codex 2차 리뷰(리셋 대기 포함) → 판정 → 일관성 → 웹 표본 | V3~V5 |
| 05 | 링크 전환·README 재생성·컨테이너 삭제·커밋·(사용자 확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변 4건(2026-10-01)
- [x] auto
