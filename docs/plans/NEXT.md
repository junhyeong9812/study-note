# NEXT — 다음 작업 전망 (프로젝트 롤링 단일 문서)

> 착수는 새 작업 폴더 requirement-spec 생성부터(core §1) — 이 문서는 후보 목록이지 합의된 명세가 아니다.

## 기준

- 마지막 갱신: 2026-09-28 (N0-a 배포 완료 · N0-b 불요 종료 — 채팅은 Redis TTL 7일) · 이전: 2026-09-27 · 직전 완료 작업: `docs/plans/2026-09-27/issue-toplevel-cs-rule/` · 기준 커밋: a8f8a9e1(study-note) · c2254f0(harness 브랜치 docs/issue-archive-toplevel-path) · 병합 상태: 둘 다 미push

## 다음 작업 후보 (우선순위순)

### N0-c. CS 커리큘럼 확정 → cs 재편 — 우선순위: 높음 · 사용자 검토 대기

- **입력**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`(505 leaf·18영역, 이식 매핑 §19).
- **결정 필요**: systems/ops-patterns 해체, foundations 나머지 해체 이식 (languages·web-api·python-basics는 2026-09-28 최상위 languages/로 이동 완료).
- **함께 처리할 stale 참조(리뷰 O5·O6·O10 이연)**: `issue/authoring-guide.md:27,31` "cs 컨벤션" 의존 · `reference/learning/README.md:33-43`·`cs/engineering/development-standards/README.md:5` 옛 규칙 인용 · `reference/study-note-guide.md` §2·§2-1·§5·§7·§8 본문 · `cs/index.md:4` 옛 상태 범례 · `templates/` cs 비적용 표기.

### N1. seat-reservation-lab 첫 API — 우선순위: 중간 · 17개 랩 중 선행 cs가 가장 명확한 첫 주제

- **왜 다음인가**: 스캐폴드·기록 경로·append-only 규칙이 준비됨. 선행 cs = domain basic/02 · advanced/12 · ops 11 · ops 04.
- **발생 가능한 문제**: 관측 신호 — 기본 `java`가 1.8(JAVA_HOME 미지정 시 기동 실패) · 중단된 bootRun이 고아 프로세스로 포트를 점유(auction-lab 8105 실측).
- **권장 대처**: 착수 시 JAVA_HOME 21 고정, 기동 전 `ss -ltnp`로 포트 점유 확인.
- **착수 전 확인할 것**: 8/20 우선순위(기본기 → 도메인 → api/ops)와 포트폴리오 트랙 병행 비율 — 사용자 결정.

### NA. (issue 카드) 정확성 재점검 확대 — 우선순위: 중간

- **왜 다음인가**: codex 재점검은 표본 8장만 했다. 교정 전 48건 → 후 6건이었으니, 나머지 146장에도 예제 코드 엣지 결함이 남아 있을 수 있다(관측: 재점검 6건 모두 "고친 코드"의 오류 처리 누락).
- **권장 대처**: 복습하면서 걸리는 카드부터 `## 정정` append. 또는 폴더 단위로 codex 인라인 재점검(카드 8장당 1회).

### NB. (issue 카드) 검색엔진 카드군 도메인 추정 여지 — 우선순위: 낮음

- **왜 다음인가**: 이름·수치는 가공했지만 카드 조합으로 원 도메인 구조를 추정할 여지가 남았다(리뷰 잔여 리스크).
- **권장 대처**: 해당 폴더 README·카드의 도메인 특유 예시를 다른 도메인 예로 교체할지 판단.

### N2. mysql 아키텍처 지도 미완 링크 — 우선순위: 낮음

- **관측**: 09-25 WIP 병합으로 깨진 링크 32 — record-lock 03~11 단계·structure/(memory-structures·redo-log-files·tablespace-page·threads·undo-segments·record-format)·mvcc-read·purge 미작성, `flows/structure/…` 경로 오기 일부.
- **권장 대처**: 지도 작성 재개 시 미작성 문서부터, 경로 오기는 `../../structure/`로 교정.

## 보류·이월


- 통합 랩 08·09 — 01~07 API 서버 완성 후 동시 기동 구조로 전환(사용자 결정). 재개 조건: 01~07 완료.

- 아카이브 보류(보안 — 패치·배포 미확인) 약 20건 — 재개 조건: 원 프로젝트에서 수정 배포가 확인되면 다음 사이클 마감 때 카드화(목록은 비공개 로컬 원장).

## 완료 이력

- 완료 → `docs/plans/2026-09-26/backend-labs-scaffold/`
- 완료 → `docs/plans/2026-09-24/cs-issue-archive/`
