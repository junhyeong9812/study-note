# log — integrate-deploy-archive

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-09-28 | 배포 사이트 확인: IndexingService.kt:86 커밋 SHA 기준 재색인·stale 삭제, ChatService.kt:30,41 Redis `chat:<세션>:<경로>` TTL 7일 | 작업 C(채팅 경로 마이그레이션) 불요로 종료 |
| 2026-09-28 | spec 작성(Bash heredoc — task-mode-guard가 Write 경로만 관측해 TASK_PATH 미갱신, SPEC/MODE는 set-state로 기록) | 사용자 답변 3건 = 합의 |
| 2026-09-28 | mysql 워크트리 WIP 72파일(09-25 흐름 7개+작업기록, 비-md·시크릿 0) 커밋 1133083a → main 병합 | 기존 깨짐 7 해소, 신규 깨짐 32 = WIP의 미작성 대상(record-lock 03~11·structure/*)·경로 오기(`flows/structure/…`) — 원문 상태, NEXT 등재 |
| 2026-09-28 | main ff(c61ab015) → 워크트리 4개 remove(clean·main 포함 확인) → 로컬 브랜치 -d 10개, -d 거부 2개(upstream 기준)는 `merge-base --is-ancestor main` 확인 후 -D | `git worktree list` = 1 · `git branch` = main |
| 2026-09-28 | study-note push origin main | 20b56264..c61ab015 |
| 2026-09-28 | 하네스 deploy.sh --dry-run(변경 3파일, DEST-only 0) → 배포 | smoke 통과, 백업 ~/.claude/.deploy-backup-2489714, ~/.claude playbook·core.md = `study-note/issue/` |
| 2026-09-28 | issue-archive: 원 식별자 목록(카드 금지어) = 저장소명 2종·도구 CLI명·사용자명·홈 경로 | 스캔 기준 |
| 2026-09-28 | 매칭: 폴더 이동 상대 링크 → path-derived-key-on-move(같은 원리·다른 해법) ⓒ 방안 비교 / 중첩 샌드박스 → 기존 카드 없음 ⓐ os/nested-sandbox-capability | — |
| 2026-09-28 | codex 카드 점검(인라인): 정확성 11·노출 1·제목 1 | 채택 11(merge.directoryRenames 기본 conflict, user namespace 정의, 루프백 설정 거부로 한정, 읽기 경계≠접근통제, exit 0 비필연, 완료 게이트 코드, 내부 격리만 상실, 보조 자식 지연·인라인 무관 등) / 선택하지 않음 2(제목 `issue/os/…`는 기존 카드 관례, `Claude 초안`·git·bwrap은 관례·일반 도구명) |
| 2026-09-28 | 미push 브랜치 soft reset 후 카드별 재커밋 + 노출 스캔 0 | 98e8b78a(ⓒ) · f848366b(ⓐ) · 링크 신규 1 = 카드 A 인라인 코드 속 예시(오탐) |

## 생략한 검증

- 카드 리뷰는 codex 1패스(spec §6) — Opus 병렬 생략(문서 카드·중간).

## 완료 요약

- 통합: 모든 워크트리·브랜치 → main, 로컬 정리(워크트리 1·브랜치 main).
- 배포: 하네스 issue-archive 경로 `issue/` 적용.
- 아카이브: 카드 2건(방안 비교 1·신규 1).
- 종료: 채팅 마이그레이션(불요).
