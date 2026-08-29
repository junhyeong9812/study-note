# issue2 — 배선과 E2E: 실기동이 잡은 결함 4개, 그리고 배포 방식 전환

- 이슈 #4·#7 · PR: #6, #8 (+ llm #14·#15, front #13)

## 1. 흐름 완성

```
리포 main push → Actions(호출만) → www/api/deploy(front 중계) → master → agent
                                                                      │ git fetch + reset --hard <sha>
                                                                      │ docker compose up -d --build <svc>
E2E 실측: push → 15.4초 뒤 .164 wrapper 재빌드·재생성 → health 200
```

## 2. 실기동이 잡은 결함 4 (ghcr 방식 시절 — 각각이 배움)

### ① 전체 pull이 무관 GB 이미지를 받다 타임아웃

```
23:48:23 agent deploy start llm
23:52:23 agent deploy failed  ← 정확히 4분(타임아웃). ollama/ollama 최신 이미지를 받고 있었다
```
`compose pull`은 **모든 서비스**를 당긴다 — 대상만 지정하도록(DEPLOY_SVC_*) 수정.
up도 대상만 — 아니면 ollama까지 재생성돼 로딩된 모델이 날아간다.

### ② image+build 병존이면 pull이 건너뜀

```
wrapper Skipped - No image to be pulled
```
compose는 build:가 있는 서비스를 "로컬 빌드 대상"으로 보고 pull하지 않는다.
610ms 만에 "deploy ok"가 떴는데 컨테이너는 그대로였던 이유 — **성공 로그가 아니라
산출물(컨테이너 이미지·created 시각)을 봐야 한다**가 여기서 또 반복됐다.

### ③ 설계 공백 — 이미지만 배포하면 compose 변경이 영원히 안 닿는다

②를 고친 커밋이 GitHub에 머지됐는데도 호스트의 compose엔 build:가 남아 있었다.
호스트 사본은 rsync 시절 구본 — **이미지 채널과 설정 채널이 분리**돼 있었던 것.
해결: 호스트 디렉토리를 git clone으로 전환 + 에이전트가 배포 전 fetch/reset.
(이 해결이 다음 절의 방식 전환을 자연스럽게 만들었다.)

### ④ dubious ownership

```
fatal: detected dubious ownership in repository at '/home/jun/study-note-deploy-system-llm'
```
에이전트 컨테이너(root)가 호스트 사용자(jun) 소유 repo를 만지자 git 보안 가드 발동.
통제된 배포 전용 컨테이너라 `safe.directory '*'`로 해제(이미지에 명시 + 사유 주석).

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
