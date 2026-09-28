# log — cs-restructure

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-09-28 | 인터뷰 rev.1(재편·이동) → 사용자 재판단 → rev.2 "제자리 유지 + 링크" | myway 150노트 3파일 완비 실측(빈 곳: DS 핵심 문장 35·Q/A Claude 초안) — 빈 곳 채우기는 다음 작업 「myway 5 cs 주제 완성」 |
| 2026-09-28 | 합의·auto, 브랜치 docs/cs-restructure(main a96e5277) | — |
| 2026-09-28 | task01 A1(학습 순서 전수) | 642/642 ok |
| 2026-09-28 | task01 A2(기존 칸 경로) | 주 경로 203 중 약식 3 → curriculum 문구 교정(language/19 경로 전개, 이동된 languages·web-api·python-basics 경로 현행화) → 0 · 미연결 노트 0(server-design·security는 파일 단위 연결) |
| 2026-09-28 | task02 기초 leaf 2 추가(data-structures-basics·algorithm-basics, 「기초」 단원), 심화 leaf 선행 연결, §19 판정 "유지(독립 기초 leaf)"로 철회 | 644 leaf |
| 2026-09-28 | 재번호 1차: 백틱 속 기존 노트 경로(`data-structure/02-linked-list` 등 — 영역명과 폴더명 충돌)까지 치환 → 미해석 141로 급증 | 사전 사본으로 원복 후 백틱 보호 추가해 재실행 → 해석 실패 0 |
| 2026-09-28 | 재번호 검증 | slug 중복 0 · 학습 순서 = 01…NN 순차(19영역) · 선행 참조 불일치 0 · 필수 351/권장 249/심화 44 |
| 2026-09-28 | 범위 참조(`area/AA~BB`) 뒷번호 미변환 5건·산문 속 번호(네트워크 TCP 구간·시간 예산 순서·12.2a·leaf 18·19·16.2) 수동 매핑 | 교정. 한계: 행 안 ⚠·📚 칸의 같은 영역 맨숫자 언급은 자동 치환 대상 아님 |
| 2026-09-28 | §20 통계 재계산, slug-map.tsv(644행) | 644 · 신규 464 · 기존 180 |
| 2026-09-28 | task03 gen_area_readme.py → 19개(신규 15 README·겹침 4 curriculum.md) | 미작성 464 · 원고 있음 74 · 초안 106 = 644, 원고+초안 180 = 기존 180(V5) · 재실행 md5 동일(V4) |
| 2026-09-28 | **사고**: 검사 명령 끝에 `git stash -q`가 섞여 실행 — curriculum.md 변경분이 스태시로 이동 | 즉시 `git stash show`로 대상 확인(curriculum 1파일) → `stash pop` 복원, stash 0 · 644 재확인. 손실 없음 |
| 2026-09-28 | task04 myway 6 index의 원본 경로·진도 칸 → project/myway/README.md(신설), cs index는 챕터 목록 + 포인터 | project/index 행 추가 |
| 2026-09-28 | task05 규칙·색인: cs/README(§코드 언어·§4 상태 4단계·§6 구조), cs/index(19영역 지도·기존 컬렉션), 루트 index·README(트리·색인 myway 원본 칸), 컬렉션 README 포인터 4, issue/authoring-guide(cs 컨벤션 의존 제거), reference/learning(옛 인용 주석), development-standards README(옛 규칙·깨진 상대경로 `../README.md` 교정), study-note-guide §2·§5·§7·§8 배너, templates/README cs 예외 | V1: R·D 0, M 21 = 대상 목록 · V2 신규 깨짐 0(기존 1건 해소) |
| 2026-09-28 | 듀얼 리뷰 1패스(OUT=/tmp/tmp.MBxQHxGz8m, mirror=/tmp/tmp.hvsXo8sxWS) — codex 인라인 4건 · Opus 12건 | 전부 채택 |
| 2026-09-28 | **정지 규칙 발동**: 재번호 결함 2회째(1차 백틱 과치환 → 2차 백틱 미치환·목록 첫 토큰만) — polish 대신 방식 재설계 | 재번호 전 사본에서 규칙 명세(노트 경로=기존 칸·§19 원본 열의 실존 경로만 보호, 그 외 leaf 참조 전부·목록·범위·같은 영역 맨 번호 판정 표)로 전체 재생성(Opus 워커) → 합격 A~E PASS(dangling 0, 의미 보존 1,312 토큰, 선행 집합 동일 644행, 노트 경로 392 바이트 동일) · 메인 독립 재검증 dangling 0 · 잔여 문장 4곳 수기 교정 |
| 2026-09-28 | 나머지 채택분 수정 | 생성기 상태 판정(전문·컬렉션 하위 스캔·검수 완료 표식) · project/myway 비-myway 3행 제거 · ops index 링크 · §5 문구 · cs/index 이력 표지·현황 열 제거 · 컬렉션 README templates 줄 · slug-map 기초 `—` |
| 2026-09-28 | 재생성·검증 | 미작성 464 · 원고 있음 72 · 초안 108(컬렉션 basic/advanced 초안으로 정정) · 링크 신규 깨짐 0(깨짐 214→209) |
| 2026-09-28 | codex post-fix 타깃 재점검 | 16건 resolved · 신규 2(검수 완료 판정이 파일 누락·본문 인용 표식도 인정) → 두 파일 존재 + 상단 15줄 날짜 표식으로 제한 · 스모크 4케이스 통과 |

## 리뷰 ledger

| id | source | 요지 | disposition | status |
|---|---|---|---|---|
| C1/O(메서드) | codex | 상태 판정 3000자·범위 | 채택 | fixed |
| C2/O7 | codex·opus | 검수 완료 도달 불가 | 채택(표식 정의) | fixed |
| C3/O6 | codex·opus | project/myway 4열 행 | 채택(비-myway 행 제거) | fixed |
| C4 | codex | ops index distributed 누락 | 채택 | fixed |
| O1~O5 | opus | 재번호 미갱신 ~150곳·오도 4·§19·math 선행 | 채택(재설계 재생성) | fixed |
| O8 | opus | 컬렉션 상태 오판 | 채택 | fixed |
| O9 | opus | 규칙↔색인 모순 | 채택 | fixed |
| O10 | opus | 컬렉션 README templates 줄 | 채택 | fixed |
| O11 | opus | slug-map 가짜 옛 slug | 채택 | fixed |
| O12 | opus | 현황 이중 관리 | 채택(열 제거) | fixed |
| P1·P2 | codex post-fix | 검수 완료 판정 느슨 | 채택 | fixed |
| (참고) | opus | 순방향 선행 7건(옛 학습 순서 그대로 굳힘) | 기록 — 사용자 보고 | — |

## 생략한 검증

- 외부 검색·설계 선검증·blind 워커: 중간 stakes·문서 재편 — 비대상.

## 완료 요약

- 노트 이동 0. 커리큘럼 644 leaf 학습 순서 재번호(slug-map·renumber-report), 기초 leaf 2 독립, 영역 생성 문서 19(미작성 464·원고 72·초안 108), myway 진도 → project/myway, 규칙·색인 정리(cs/README 코드 언어·상태 4단계·구조, 이연 stale 참조 6곳).
- 다음: 「myway 5 cs 주제 완성」(빈 곳 전부 채움) — 새 명세.
