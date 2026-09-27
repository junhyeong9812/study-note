# log — issue-toplevel-cs-rule

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-09-27 | 참조 조사: study-note 내 `cs/issue` 외부 참조 grep | 0건(rc=1) — 내부 92파일만 |
| 2026-09-27 | 하네스 참조 조사 | playbooks/issue-archive.md:5·18·42, src/core.md:114, README.md:70 (HISTORY·docs/plans는 이력) |
| 2026-09-27 | deploy TreeBuilder.kt 확인 | 경로 범용 트리 — 폴더 허용목록 없음(A1 코드 근거) |
| 2026-09-27 | 채팅 기록 doc_path 키 확인(ChatController.kt) | 이동 시 고아화 → 작업 C(마이그레이션) 분리, path-map 산출 |
| 2026-09-27 | requirement-spec 초안 작성 | 사용자 합의 대기 |
| 2026-09-27 | 사용자 합의 → SPEC=1·MODE=auto (set-state) | 착수 |
| 2026-09-27 | task01 링크 기준선(linkcheck.py, scratchpad) | total 29991·broken 173(기존 결함 — issue 내 4건은 예시 링크 ../foo·../kafka-why-fast·강조) |
| 2026-09-27 | task02 `git mv cs/issue issue` + relink.py | R 92건(V1) · 링크 58개 재작성 · 신규 깨짐 0(V2) · `cs/issue` 잔존 = docs/plans만(V3) |
| 2026-09-27 | 루트 index.md·README.md issue 행 추가, path-map.tsv 92행 | V7 |
| 2026-09-27 | task03 cs/README 작성 규칙 개정(흐름·융합·하지 말 것 → 작성 규칙 1~5) + 5행 templates 우선순위 문구 | 링크 재검사 신규 깨짐 0 |
| 2026-09-27 | task04 harness 브랜치 docs/issue-archive-toplevel-path(main 1a80f0f 기준) 생성, playbook 3곳·core.md:114·README.md:70 수정, HISTORY 1행 | 잔존 = HISTORY 기존행·docs/plans만(V3) · hooks/tests/run.sh 258 passed 0 failed(V4) |
| 2026-09-27 | 외부 검색 생략 | 사유: 내부 경로 변경(spec §6) |
| 2026-09-27 | 설계 선검증 생략 | 동작 불변식 없음(경로 치환 — spec I1~I5는 범위·보존 제약) |
| 2026-09-27 | 루프1 packet: OUT=/tmp/tmp.qpkZlZJtSj mirror=/tmp/tmp.fNPwubgnVH (study-note base b5b2c343 + harness base 1a80f0f), 보안 스캔: 하네스 archive의 패턴 설명문 매칭만(오탐) | 전달 |
| 2026-09-27 | codex 1차 실패 — bwrap loopback RTM_NEWADDR 권한 오류로 파일 읽기 전부 실패 | 규칙대로 1회 재시도(packet 인라인 stdin) → 성공. 미러 파일 열람 불가 → diff 밖 완전성은 Opus만(비대칭 표기) |
| 2026-09-27 | 루프1 종합: 채택 5(C1·O1·O2·O3·O4) + 범위 밖 2(O5·O6 → NEXT) | 수정 적용, 링크 재검사 신규 깨짐 0 |
| 2026-09-27 | codex 종합 감사 + 루프2(인라인) | 누락 0·신규 0, O5·O6 상태 표기 정정 지적 |
| 2026-09-27 | Opus 루프2(mirror /tmp/tmp.CA6uIWgka7) | 신규 채택 3(O7~O9) → 수정, 링크 신규 깨짐 0 → 루프3 필요 |
| 2026-09-27 | 루프3: codex(인라인) 신규 0 · Opus(mirror /tmp/tmp.cGRNEki4t7) 신규 1(O10, 낮음) | O10 수정 → codex post-fix 타깃 재점검 "resolved·신규 없음", 링크 신규 깨짐 0 |
| 2026-09-27 | 루프 종료 판정 | 3루프 상한 도달 — 루프3에 신규 채택 1건이 있어 형식상 종료조건 미충족 → `review unresolved(형식)`: O10은 fixed + 타깃 재점검 clean, open finding 0. 사용자 보고 |
| 2026-09-27 | 미러 정리 | /tmp/tmp.fNPwubgnVH·CA6uIWgka7·cGRNEki4t7 삭제 |
| 2026-09-27 | 커밋 | study-note a8f8a9e1 (R92·M3·A3, 경로 지정 스테이징) · harness c2254f0 (docs/issue-archive-toplevel-path) |
| 2026-09-27 | 마감: measurement-log 1행·NEXT.md(N0-a/b/c, 보류 1) | 둘 다 기존 미커밋분과 섞여 있어 커밋하지 않음(I5) |
| 2026-09-27 | 아카이브 보류(범위 미확인) — codex 중첩 샌드박스 bwrap 파일 읽기 실패 | NEXT 보류·이월 등재, 사용자 보고 |

## 리뷰 ledger

| id | loop | source | 근거 | disposition | status | fixed_in |
|---|---|---|---|---|---|---|
| C1 | 1 | codex | cs/README.md:15 "원본 위치는 주제 index에" ↔ §5 cs=지식 본문만 충돌 | 채택 | fixed | 1 |
| O1 | 1 | opus | reference/study-note-guide.md §2(43-68)·§5(947-954)가 폐기 규칙을 정본으로 유지, README.md:17 "그 문서 하나만" | 채택(우선순위 명시: cs/README:5·README.md:18) / guide 본문 개정은 범위 밖→NEXT | fixed | 1 |
| O2 | 1 | opus | README.md:47-48 융합 규칙 참조가 삭제된 절을 가리킴 | 채택 | fixed | 1 |
| O3 | 1 | opus | README.md 폴더 구조 트리에 issue/ 누락 | 채택 | fixed | 1 |
| O4 | 1 | opus | cs/README.md:10 미커밋 roadmap 경로 참조 | 채택(참조 제거) | fixed | 1 |
| O5 | 1 | opus | issue/authoring-guide.md:27,31 "cs 컨벤션대로" 암묵 의존 | 범위 제약 이연(I1 본문 최소 변경) → NEXT | deferred-scope | — |
| O6 | 1 | opus | reference/learning/README.md:33-43·cs/engineering/development-standards/README.md:5 stale 인용 | 범위 제약 이연(I5 커밋 범위 밖) → NEXT | deferred-scope | — |
| O7 | 2 | opus | cs/README.md:5·README.md:19 우선순위 선언이 가이드 §2·§5만 나열 — §2-1·§7-2·§8 cs 규칙 잔존 | 채택(가이드 전체로 확대) | fixed | 2 |
| O8 | 2 | opus | README.md:69-71 「작성 규칙」 "직접 작성"과 모순, cs 예외 없음 | 채택(cs 예외 1행) | fixed | 2 |
| O9 | 2 | opus | cs/README.md:10 참조 끝 쉼표 | 채택 | fixed | 2 |
| A1 | 2 | codex 감사 | O5·O6 status "user-deferred" 근거 없음 | 채택(deferred-scope로 정정) | fixed | 2 |
| O10 | 3 | opus | cs/README.md:39 새 상태 어휘 ↔ cs/index.md:4 옛 범례(범위 밖) 모순, 이연 표기 없음 | 채택(이연 1행) | fixed | 3 |

## 생략한 검증

- 외부 검색: 내부 경로 변경이라 불요(spec §6) · 설계 선검증: 동작 불변식 없음 · blind 테스트 워커: 실행 코드 없음 — 검사 스크립트(linkcheck·rename count·grep)를 spec 기준으로 구현 전 작성해 대체
- 배포 사이트 실렌더 확인(A1): push 후 — 범위 밖(작업 C·NEXT)
- 하네스 deploy.sh: 사용자 지시 "커밋까지만" — 배포 전까지 ~/.claude playbook은 옛 경로(NEXT 등재)

## 완료 요약

- study-note `a8f8a9e1`: `cs/issue/**` → `issue/**` 92 rename, 링크 58개 교정(`../../project/...` → `../project/...` 등), H1 `# cs/issue/...` → `# issue/...`, 루트 index·README 입구·트리, `cs/README.md` 「작성 규칙」 1~5 신설(흐름·융합·하지 말 것 절 교체), 루트 README cs 예외 2곳.
- harness `c2254f0`: `playbooks/issue-archive.md` 대상 `/home/jun/project/study-note/issue/`·`issue/README.md`·`docs(issue):` · `src/core.md` §7 ② `study-note \`issue/\`` · `README.md:70` · HISTORY 1행.
- 검증: V1 R92 · V2 신규 깨짐 0(기준선 173 동일) · V3 잔존 0 · V4 258 passed · V5 issue 비-md 0 · V7 path-map 92행 · 리뷰 3루프(채택 10, 이연 2) — 루프3 신규 1건 수정 후 타깃 재점검 clean, 형식상 `review unresolved`(3루프 상한).
- 미완: push·deploy·채팅 마이그레이션(NEXT N0-a/b).
