# NEXT — 다음 작업 전망 (프로젝트 롤링 단일 문서)

> 착수는 새 작업 폴더 requirement-spec 생성부터(core §1) — 이 문서는 후보 목록이지 합의된 명세가 아니다.

## 기준

- 마지막 갱신: 2026-09-30 network-writing 완료(네트워크 51편 새 집필·검증) · 직전: 2026-09-28 cs-restructure · 작업 폴더: `docs/plans/2026-09-30/network-writing/` · 기준 커밋: d313fe16 → 작업 브랜치 docs/network-writing

## 다음 작업 후보 (우선순위순)

### N0-c. 커리큘럼 미작성 413 leaf 집필 — 우선순위: 높음 · 네트워크 51편 완료(2026-09-30) 다음 영역

- **입력**: `cs/<영역>/README.md`의 `미작성` 행 · 통일 골격·코드 언어 규칙(cs/README) · 재사용 도구: `docs/plans/2026-09-30/network-writing/`의 briefing·check_new.py·factcheck-briefing·adjudicate-briefing, scratchpad의 relink 패턴(영역 폴더 존재로 "미작성" → 링크).
- **관측(네트워크 실측)**: Opus 집필 → Opus 전수 점검만으로는 부족 — 뒤이은 codex/대체 리뷰가 편당 1~11건(합계 ~130)을 더 찾았고 판정 기각 0. 유형: 조건 없는 단정, 노트 내부 모순(그림 vs 식, 정답 N vs M), 규범 수준, **man 페이지가 최신 커널보다 뒤처짐**(tcp(7) 127초 vs 6.5+ 131초, udp(7) EMSGSIZE, ss(8) rto), 병렬 집필로 노트 간 불일치.
- **권장 파이프라인**: 집필(Opus) → 사실 점검(Opus) → **2차 리뷰(codex, 한도 시 Opus 적대 리뷰)** → 판정·반영(Opus, 1차 출처 재확인) → 노트 간 공통 사실 일관성 재점검 → 링크 전환 → README 재생성. 공통 사실(에러 매핑·기본값)은 영역 착수 전에 "정답표"로 먼저 고정하면 병렬 불일치가 준다.
- **발생 가능한 문제**: codex 사용 한도(이번에 47편 실행 중 소진 — 23:18까지) → 대체 리뷰로 모델 다양성 손실. 뒤집기 반복(duplex 불일치 쪽 — 1차 출처 재조회로 고정, 정지 규칙).
- **착수 전 확인할 것**: 다음 영역(로드맵: OS → DB …), 한 번에 몇 영역.

### N0-e. 커리큘럼 본문 오기 3건 — 우선순위: 낮음(1행)

- curriculum.md §7: 02행 "12로 이어짐" → 10(fragmentation-mtu-pmtud) · 44행 ⚠ "47의 사이드채널" → 43 · 08행 선행 `data-structure/13-radix-trie` → `20-radix-trie`. 고친 뒤 gen_area_readme.py 재실행.

### N0-f. 네트워크 51편 사용자 검수 — 우선순위: 중간

- 배포 사이트에서 읽기 → 확정 시 3파일 상단 `✅ 검수 완료(YYYY-MM-DD)`. `[?]` 잔여(편당 0~5)는 검수 때 판단. 08 blackhole `ip route get` EINVAL·23 SYN-ACK 한도 소진 뒤 결과는 실행 미검증(userns 불가).

### N0-d. myway 150편 사용자 검수 — 우선순위: 중간

- 배포 사이트에서 읽기 → 확정 시 1-question·3-answer 상단 `✅ 검수 완료(YYYY-MM-DD)`, 원래 본문 정정 줄 84곳 확인.

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
