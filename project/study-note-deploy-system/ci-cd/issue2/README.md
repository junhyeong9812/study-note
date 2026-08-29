# issue2 — 배선과 E2E: 실기동이 잡은 결함 4개, 그리고 배포 방식 전환

- 이슈 #4·#7 · PR: #6, #8 (+ llm #14·#15, front #13)

## 1. 흐름 완성

```
리포 main push → Actions(호출만) → www/api/deploy(front 중계) → master → agent
                                                                      │ git fetch + reset --hard <sha>
                                                                      │ docker compose up -d --build <svc>
E2E 실측: push → 15.4초 뒤 .164 wrapper 재빌드·재생성 → health 200
```

## 2. 실기동이 잡은 결함 4 (ghcr 방식 시절 — 각각의 전말)

### ① 전체 pull이 무관 GB 이미지를 받다 타임아웃

**상황**: 에이전트 컨테이너가 llm 디렉토리에서 `docker compose pull`(서비스 지정 없이)을
실행. 이 compose에는 wrapper 외에 **ollama 서비스도** 정의돼 있다.

**문제**:
```
23:48:23 agent deploy start llm
23:52:23 agent deploy failed   ← 시작에서 정확히 4분 = 우리가 건 타임아웃
```
로그 사이를 보면 ollama/ollama:latest의 레이어를 계속 받고 있었다 — 우리가 배포하려던 건
wrapper(수백 MB)인데, compose pull은 **파일에 정의된 모든 서비스**의 이미지를 갱신하려
든다. ollama 최신 이미지는 GB급이라 4분 안에 못 받았다.

**접근**: 타임아웃 시각이 정확히 +4:00인 걸 보고 "느린 게 아니라 죽인 것"을 확정 →
에이전트 로그의 pull 진행 줄에서 ollama 레이어 해시 확인.

**결론**: 대상 서비스만 지정 — env `DEPLOY_SVC_LLM=wrapper`를 두고
`compose pull wrapper` / `up -d wrapper`. up도 대상 한정이 중요하다: 전체 up이었다면
새로 받아진 ollama 이미지로 **ollama 컨테이너까지 재생성**되어 GPU에 로딩된 모델이
날아갔을 것. **원칙**: 배포 단위는 "그 서비스"지 "그 compose 파일 전체"가 아니다.

### ② image:와 build:가 같이 있으면 compose pull이 그 서비스를 건너뛴다

**상황**: ①을 고치고 재배포. 에이전트가 `compose pull wrapper` 실행.

**문제**: 610ms 만에 "deploy ok" — 그런데 컨테이너를 보니:
```
agent deploy ok llm tag=49cb8cd... 610ms          ← 성공 로그
$ docker inspect llm-wrapper
image=study-note-deploy-system-llm-wrapper        ← 옛 로컬 빌드 이미지 그대로
```
출력을 뒤지니 진짜 이유가 한 줄 있었다: `wrapper Skipped - No image to be pulled`.

**접근**: 호스트에서 에이전트와 똑같은 명령을 수동 재현 —
`TAG=49cb8cd... docker compose pull wrapper` → 동일하게 Skipped. compose 문서·동작을
확인하니: 서비스에 `build:`가 있으면 compose는 그 서비스를 **"로컬에서 빌드하는 것"**으로
분류한다. 이때 `image:`는 "받을 주소"가 아니라 **"빌드 결과에 붙일 이름표"**로 해석된다.
그래서 pull 대상에서 제외 — 우리는 `image: ghcr…${TAG}` + `build: ./wrapper`를 병존시켜
"배포는 pull, 로컬 개발은 build"를 노렸지만, compose에게 그 두 키의 병존은 "빌드하는
서비스"라는 뜻이었다.

**결론(당시)**: `build:`를 compose에서 제거(배포 정본=ghcr, 로컬 빌드는 `docker build`
직접). — 이후 git-pull 전환으로 pull 자체가 사라지며 `build:`는 복원됐다.
**원칙**: "성공 로그"가 아니라 **산출물**(컨테이너의 image·created 시각)을 봐야 한다 +
도구의 키 조합은 내 의도가 아니라 **도구의 해석**으로 동작한다.

### ③ 설계 공백 — 이미지만 나르는 파이프라인은 compose 변경을 영원히 전달하지 못한다

**상황**: ②의 수정(compose에서 build 제거)을 **GitHub에 머지**했고 Actions도 성공.
그런데 재배포하면 **여전히 Skipped**가 나온다.

**문제**: .164 호스트의 `~/study-note-deploy-system-llm/docker-compose.yml`을 직접 열어보니
`build:`가 그대로 있었다 — **호스트의 compose는 옛날 rsync로 복사해둔 사본**이고, 그
이후 GitHub에서 일어난 변경과 아무 관계가 없다. 구조적으로 보면: 우리 파이프라인은
"코드"를 이미지에 담아 날랐지만, **compose 파일은 이미지 밖**(컨테이너를 정의하는 배포
설정)이라 그 채널에 실리지 않는다. 설정을 나르는 채널이 아예 없었던 것.

**접근** — 채널 후보 셋:
- (a) 필요할 때 수동 rsync — 자동 배포의 목적 자체를 부정. 탈락.
- (b) compose 파일도 이미지에 넣기 — 불가능. compose는 컨테이너를 "밖에서" 띄우는
  정의라, 그걸 컨테이너 "안"에 넣어봐야 아무도 읽지 않는다.
- (c) 호스트 디렉토리를 git clone으로 만들고, **에이전트가 배포 직전에
  `git fetch + reset --hard`** — GitHub이 곧 설정의 정본이 되고, 배포 때마다 최신
  설정이 따라온다.

**결론**: (c) 채택. 이게 문제를 없애는 메커니즘: 이제 "설정 채널 = git"이 생겼고,
배포 순서가 *설정 동기화 → 컨테이너 갱신*이라 compose 변경이 항상 코드보다 먼저
도착한다. `.env`(시크릿)는 git 미추적 파일이라 `reset --hard`(추적 파일만 되돌림)에도
살아남는다. — 그리고 이 결정이 다음 질문을 낳았다: "git 채널이 어차피 필수라면
이미지 채널(ghcr)은 왜 필요하지?" → §3의 방식 전환으로 이어진다.

### ④ dubious ownership — git 자신의 보안 가드에 걸리다

**상황**: (③ 해결 후) **에이전트 컨테이너 안에서 실행된 git**이, 컨테이너에 마운트된
**호스트 디렉토리**(`/home/jun/study-note-deploy-system-llm` — 소유자 jun, uid 1000)를
대상으로 `git fetch`를 실행. 에이전트 컨테이너의 프로세스는 root(uid 0)로 돈다.

**문제**:
```
fatal: detected dubious ownership in repository at '/home/jun/study-note-deploy-system-llm'
```
도커가 막은 게 아니다 — **git 바이너리 자체의 검사**다. git 2.35.2부터: repo 디렉토리의
소유자와 git을 실행한 사용자가 다르면 거부한다. 이유는 실제 취약점(CVE-2022-24765) —
공유 머신에서 남이 만들어둔 repo에 악성 설정(예: `core.fsmonitor`에 임의 명령)을 심어두면,
그 폴더에서 git을 실행한 **다른 사용자**의 권한으로 그 명령이 실행될 수 있었다. 그래서
"소유자가 다른 repo는 신뢰하지 않는다"가 기본값이 됐다.

우리 상황이 정확히 그 패턴에 걸린다: 파일 소유자(jun, uid 1000) ≠ 실행자(컨테이너 root,
uid 0). 컨테이너와 호스트는 **같은 uid 공간**을 쓰기 때문에(도커는 uid를 격리하지 않는다,
기본 설정에서) 이 비교가 컨테이너 안에서도 그대로 성립한다.

**접근**: 에러 메시지가 해법을 직접 안내한다(safe.directory 등록). 판단할 것은 범위 —
특정 경로만 등록 vs 전체(`*`). 이 컨테이너는 (1) 우리가 빌드한 배포 전용이고 (2) 접근
가능한 디렉토리가 compose 마운트로 고정된 3개뿐이며 (3) 그 안에서 실행하는 명령도
allowlist 고정이라, "신뢰 경계가 이미 컨테이너 바깥에서 그어져 있다"고 판정.

**결론**: 이미지 빌드에 명시(+사유 주석):
```dockerfile
RUN apk add --no-cache git && git config --global --add safe.directory '*'
# safe.directory: 에이전트(root)가 호스트 사용자 소유 clone을 다룬다 — 통제된 배포 전용
```
**원칙**: 보안 가드에 걸리면 "끄는 법"보다 **"무엇을 막으려던 가드인지"**를 먼저 이해하고,
우리 상황에서 그 위협이 성립하는지로 판단한다(여기선 위협 모델의 전제 — 신뢰 불가한
타인의 repo — 가 성립하지 않았다).

## 3. 방식 전환 — ghcr pull → git pull + 호스트 재빌드 (사용자 결정)

③을 풀고 나니 git 채널은 어차피 필수였다. 그럼 이미지 채널(ghcr)은 왜 필요하지? —
전달 채널을 **git 하나**로 통일:

```diff
- Actions: docker build & push ghcr (26초) ──▶ agent: compose pull <svc>
+ Actions: curl 호출만 (2초)              ──▶ agent: git reset --hard <commit_sha>
+                                                    compose up -d --build <svc>
```

트레이드오프를 알고 선택: 호스트 빌드 시간(backend gradle 수 분·.9는 CPU 약함)을
감수하는 대신 — 레지스트리 의존·이미지/설정 이원화·ghcr 가시성 문제가 전부 사라지고
"배포된 것 = 그 커밋"이 항상 성립한다. payload도 image_tag → **commit_sha**(hex 검증)로
의미가 정직해졌다.

## 4. 결론

push 한 번이 15초 뒤 실서비스 재배포가 되는 사슬 완성(llm 배선). backend·front의
Actions 확장과 롤백(태그 이력은 /status에 축적 중)은 다음 이슈. PR: #6·#8
