# 요구사항 명세서 — integrate-deploy-archive

## 0. 요구사항 원문

- 원문: "배포는 진행, 이슈 기록, 그리고 배포사이트는 어차피 수정사항에 맞게 최신화되지 않아? mysql과 우선 워크트리들 전부 main에 머지해서 우선 통합 정리하자"
- Q/A
  - mysql 워크트리의 미커밋 72파일은 그대로 커밋한 뒤 병합한다.
  - 병합 후 워크트리 4개를 제거하고, 병합된 로컬 브랜치를 삭제한다(`-d`). 원격 브랜치는 유지한다.
  - 이슈 카드 2건을 기록한다: 폴더 이동 시 상대 링크, 중첩 샌드박스 codex 실패.
  - 배포 사이트 확인 결과
    - 본문·검색은 커밋 SHA 기준으로 재색인하고 stale을 정리한다(`IndexingService.kt:86`).
    - 채팅은 Redis TTL 7일 세션 키다(`ChatService.kt:30,41`).
    - 따라서 작업 C(채팅 마이그레이션)는 **불요로 종료**한다.

## 1. 목표·대상 (필수)

아래 네 가지가 되면 끝이다.
1. study-note의 모든 워크트리·브랜치 작업이 main에 통합되어 push된다.
2. 워크트리 4개와 병합된 로컬 브랜치가 정리된다.
3. 하네스가 deploy.sh로 배포된다(issue-archive 경로 `issue/`).
4. issue 카드 2건이 playbook 절차대로 아카이브되어 push된다.

## 2. 경계·불변식 (필수)

- 삭제는 **main에 포함이 확인된 것만** 한다(`merge-base --is-ancestor`, `branch -d`). 워크트리는 clean 상태에서만 remove한다(`--force` 금지).
- 새로 깨지는 링크 0. 기준선은 현 main이다. mysql WIP의 전방 링크는 해소되는 방향이어야 한다.
- 카드는 출처 식별자 없이 추상화한다(playbook §3). 카드 1개 = 커밋 1개. `git add` 시 경로를 지정한다.
- 하네스 배포는 deploy.sh로만 한다(manifest diff → 백업 → smoke).

## 3. 기준소스 (필수)

- study-note main `20b56264`, 워크트리 4개의 현 상태
- 하네스 main `c2254f0`
- 카드 형식: `issue/authoring-guide.md`

## 4. 금지영역 (필수)

- 원격 브랜치 삭제
- 병합 미확인 브랜치 삭제, `branch -D`, `worktree remove --force`
- deploy-study-note 코드·DB
- 카드에 실제 프로젝트명·경로·호스트 기재

## 5. 검증 방법 (필수)

- `git worktree list`에 메인 1개만 남는다.
- `git branch --no-merged main`이 빈 결과다.
- 링크 비교에서 새로 깨진 링크가 0이다.
- deploy.sh smoke 통과 + `~/.claude/playbooks/issue-archive.md`에 `study-note/issue/`가 들어 있다.
- 카드: 노출 스캔 0, authoring-guide 형식 준수, 인덱스 갱신, 링크 검사 통과.

## 6. stakes (필수)

- 판정: **중간**
- 근거: 하네스 배포는 리뷰를 마친 경로 치환 결과를 배포하는 것이고 smoke와 백업이 있다. 워크트리·브랜치 삭제는 병합 확인 후에만 하므로 내용 손실이 없다. 카드는 문서다.
- 리뷰: 카드 2장은 codex 1패스로 노출·정확성을 점검한다(playbook §4 노출 스캔 포함).

## 7. 자율성

- [x] auto (이전 작업과 동일 — 사용자 "진행")

## 8. load-bearing 가정

- **A1**: mysql WIP 72파일은 md 문서와 작업 기록뿐이고, 커밋해도 비-md·시크릿이 없다. 착수 시 find와 스캔으로 확인한다.

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변 3건(2026-09-28)과 원문 "진행"
- [x] auto
