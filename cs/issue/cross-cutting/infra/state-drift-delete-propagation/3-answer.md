# cs/issue/infra/state-drift-delete-propagation — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

## 정답
<!-- 질문 1:1 대응 -->

1. `rsync -a`는 `--delete` 없이는 "로컬에 있는 것을 서버로 복사"만 하고 "로컬에서 사라진 것을 서버에서 지우기"는 안 한다. 그래서 로컬에서 파일을 옮기거나 지운 뒤 배포하면, 서버에는 **옛 파일이 그대로 남는다**(유령/잔재). 복사는 더하기(존재)만 전파하고 빼기(부재)를 전파하지 못한다.
   > **state drift(상태 표류)** — 정본(로컬/저장소)과 배포 대상(서버)의 상태가 조용히 어긋나 쌓이는 현상.

2. 배포 스크립트가 `rsync -a`(--delete 없음)여서, git mv로 로컬에선 사라진 옛 `common/ sync/ indexing/ search/` 패키지가 **서버 소스 디렉토리에 그대로 남았다**. Docker 빌드의 `COPY src`가 옛 파일과 새 `api/` 파일을 **전부** 컴파일 → Spring이 `common.GlobalErrorHandler`와 `api.GlobalErrorHandler` 두 개의 같은 이름 빈을 보고 `ConflictingBeanDefinitionException`으로 기동을 거부했다.
   > **빈(bean)** — Spring이 관리하는 객체. 같은 이름·비호환 정의의 빈이 둘이면 어느 것을 쓸지 몰라 기동을 멈춘다.

3. `--delete`는 "로컬에 없으면 서버에서도 지운다"이므로, **서버에만 있어야 하는 파일**(예: `.env` 시크릿)까지 지워버릴 수 있다. 그래서 `rsync -a --delete --exclude .env`로 잔재는 지우되 서버 배포 설정은 보호한다.

4. 우리 파이프라인은 "코드"를 이미지에 담아 날랐지만, **compose 파일은 이미지 밖**이다 — compose는 컨테이너를 "밖에서" 정의·기동하는 설정이라, 컨테이너 "안"에 넣어봐야 아무도 읽지 않는다. 그래서 호스트의 compose는 옛 rsync 사본 그대로 남고, 그 이후 GitHub 변경(예: `build:` 제거)과 아무 관계가 없어 "여전히 Skipped"가 반복됐다. 설정을 나르는 채널이 아예 없었던 것이다.

5. agent가 배포 직전에 `git fetch --depth=50 origin main` → `git reset --hard <commit_sha>`를 돌려, **GitHub을 설정의 정본**으로 삼는다. 호스트 디렉토리가 clone이면 배포 때마다 최신 compose·설정이 따라온다. 순서가 "설정 동기화 → 컨테이너 갱신(`compose up -d --build`)"이라 compose 변경이 **항상 코드보다 먼저 도착**한다. 이로써 이미지 채널을 없애고 전달 채널을 git 하나로 통일 → "배포된 것 = 그 커밋"이 항상 성립.
   > **단일 정본(single source of truth)** — 상태의 기준이 한 곳(여기선 GitHub main)뿐이라, 대상을 그것으로 재구성하면 drift가 원리적으로 안 생긴다.

6. `git reset --hard`는 **git이 추적하는 파일만** 되돌린다. `.env`(시크릿)는 git 미추적 파일이라 `reset --hard`에도 살아남는다. 즉 "무엇을 정본이 관리하고 무엇을 관리하지 않는가"의 경계가 곧 "무엇을 덮어쓰고 무엇을 보존하는가"의 경계가 되어, 미추적이 안전장치로 작동한다.

7. **복사**는 원본의 "있는 것"만 대상에 더한다(부재는 못 옮긴다). **동기화/재구성**은 대상을 정본과 **일치**시킨다 — 없어진 것은 지우고, 바뀐 것은 갱신한다(`rsync --delete`·`reset --hard`가 이것). 이번엔 잔재가 Spring 기동 거부라는 **시끄러운 실패**로 즉시 드러나 바로 잡았지만, 충돌 없는 잔재였다면 옛 코드가 **조용히 섞여** 돌며 며칠 뒤에야 발견됐을 것이다 — 그래서 시끄러운 실패가 오히려 고마운 경우다.

## 이번 프로젝트 사례
- [backend/issue6](../../../../../project/study-note-deploy-system/backend/issue6/) — 레이어 재편(git mv) 후 `rsync -a`(--delete 없음) 잔재로 빈 이름 충돌 → 기동 거부. `rsync -a --delete --exclude .env`로 삭제 전파 + 시크릿 보호.
- [ci-cd/issue2](../../../../../project/study-note-deploy-system/ci-cd/issue2/) — ③ 이미지 채널이 compose 변경을 전달 못 함 → agent의 `git fetch + reset --hard`로 설정 채널 신설, 이후 전달 채널을 git 하나로 수렴.

## 검증 기록
- 2026-09-23: 이슈 README(backend/issue6·ci-cd/issue2) + 코드(`internal/agent/agent.go`의 `git ... fetch/reset --hard commitSha`) 대조 작성. Claude 초안.
