# cs/issue/infra/git-pitfalls — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

## 정답
<!-- 질문 1:1 대응 -->

1. **git 바이너리 자체의 검사**다(도커가 아니다). git 2.35.2부터, repo 디렉토리의 **소유자와 git을 실행한 사용자가 다르면** 거부한다. 컨테이너 프로세스는 root(uid 0)로 돌고, 마운트된 호스트 디렉토리의 소유자는 jun(uid 1000)이다. 도커는 기본 설정에서 uid를 격리하지 않으므로(호스트와 같은 숫자 uid를 그대로 씀) 이 소유자≠실행자 비교가 **컨테이너 안에서도 그대로 성립**한다.
   > **dubious ownership** — git이 "이 repo는 실행자 소유가 아니다"라고 판단해 작업을 거부하는 안전 검사.

2. 위협은 **공유 머신**에서 남이 만들어둔 repo에 악성 설정(예: `core.fsmonitor`에 임의 명령)을 심어두면, 그 폴더에서 git을 실행한 **다른 사용자의 권한으로** 그 명령이 실행되는 것(CVE-2022-24765). 끌지 판단하는 기준 = "그 위협 모델의 전제(신뢰 불가한 타인의 repo)가 우리 상황에서 성립하는가". 이 컨테이너는 ① 우리가 빌드한 배포 전용이고 ② 접근 가능한 디렉토리가 마운트로 고정된 3개뿐이며 ③ 실행 명령도 allowlist로 고정 — 신뢰 경계가 이미 컨테이너 바깥에서 그어져 있어 전제가 불성립한다. 그래서 `git config --global --add safe.directory '*'`로 끄는 게 정당했다.
   > **CVE-2022-24765** — dubious ownership 가드가 생긴 원인이 된 취약점(공유 머신의 악성 repo 설정 실행).

3. git은 빈 디렉토리를 추적하지 않으므로, 브랜치를 새로 checkout하면 빈 `src/app/api`가 **사라진다**. 그 상태에서 `> src/app/api/search/route.ts` 리다이렉션은 없는 디렉토리를 만들어주지 않아 **쓰기 실패**한다(`그런 파일이나 디렉터리가 없습니다`). 그런데 Next 빌드는 "없는 라우트"를 오류로 보지 않아 `✓ Compiled successfully`로 **통과** — 파일이 안 생겼는데 빌드는 초록불이 되는 조용한 실패다. 조합 = (빈 디렉토리 미추적) × (관대한 리다이렉션 실패) × (관대한 빌드).
   > **리다이렉션 `> 경로`** — 셸에서 출력을 파일로 보내는 것. 대상 디렉토리가 없으면 만들지 않고 그냥 실패한다.

4. git 기본값 `core.quotepath=true`는 비ASCII 경로를 사람이 보기 "안전하게" 이스케이프해 출력한다 — 한글이 `\352\267\270…`(8진수)로 바뀌고 경로 전체가 따옴표로 감싸인다. 이 **사람용 출력**을 그대로 **파일 경로**(기계용 입력)로 쓰면, 실제로는 존재하지 않는 이름이 되어 `No such file or directory`가 난다. `git -c core.quotepath=off ...`로 이스케이프를 끄면 원래 UTF-8 경로가 나온다.
   > **core.quotepath** — git이 비ASCII 파일명을 8진수로 이스케이프해 출력할지 정하는 설정(기본 켜짐).

5. **git의 기본값은 "사람이 공유 머신에서, 눈으로 보며" 쓰는 것을 안전하게 하도록** 맞춰져 있다 — 소유자 검사(남의 repo 조심), 빈 디렉토리 미추적(내용 없는 폴더는 무의미), 경로 이스케이프(터미널에서 안 깨지게). 배포/CI 자동화는 그 전제(사람·공유·눈)와 정반대다 — 통제된 단독 실행자, 디렉토리 구조가 의미, 출력을 기계가 파싱. 그래서 늘 이 세 지점에서 부딪힌다.

6. "그 기본값/가드가 막으려는 위협이 **내 통제된 환경에서 성립하지 않는다**"고 논증할 수 있으면 끈다(safe.directory·quotepath=off — 위협 전제 불성립, 또는 기계용 입력엔 부적절). 반대로 그 함정이 "**내 습관/구조가 git의 성질과 어긋난 것**"이면 습관을 바꾼다(빈 디렉토리는 `.gitkeep`을 넣어 추적하거나 스크립트에 `mkdir -p`를 선행 + 산출물 grep 확인).
   > **.gitkeep** — 빈 디렉토리를 git이 추적하게 하려고 넣는 관습적 빈 파일(git 공식 기능은 아님).

## 이번 프로젝트 사례
- [ci-cd/issue2](../../../../../project/study-note-deploy-system/ci-cd/issue2/) — ④ 컨테이너 root가 호스트 소유 clone에 git → dubious ownership. Dockerfile에 `git config --global --add safe.directory '*'`.
- [front/issue3](../../../../../project/study-note-deploy-system/front/issue3/) — 빈 `src/app/api`가 checkout에서 소멸 → 리다이렉션 쓰기 실패인데 Next 빌드는 초록불. `mkdir -p` + 라우트 표 grep 확인.
- [backend/issue2](../../../../../project/study-note-deploy-system/backend/issue2/) — 시도5: `git ls-files`가 한글 경로를 8진수로 이스케이프 → 파일 못 찾음. `git -c core.quotepath=off`.

## 검증 기록
- 2026-09-23: 이슈 README(ci-cd/issue2·front/issue3·backend/issue2) + 코드(ci-cd `Dockerfile`의 `safe.directory '*'`, backend `shared/infra/GitRepository.kt`의 `git -c core.quotepath=off diff/ls-files`) 대조 작성. Claude 초안.
