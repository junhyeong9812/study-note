# issue1 — ci-cd 설계: MODE 하나로 master도 agent도 되는 Go 서버

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-ci-cd
- 이슈 #1·#2·#3 · PR: https://github.com/junhyeong9812/study-note-deploy-system-ci-cd/pull/5

## 1. 배경

수동 배포(rsync + ssh)를 자동화한다. jun-bank에서 한 번 만들어봤지만, 이번엔 그 코드를
안 보고 논리를 다시 쌓는다(학습 목적 — 완성 후 jun-agent와 비교 스터디 예정).
구조는 사용자 결정: **.9가 master, 세 호스트 전부 agent, 단일 코드베이스를 `.env`의
MODE로 전환.**

## 2. 검토한 방식들

### 선택 — MODE 전환 단일 바이너리

```go
switch os.Getenv("MODE") {
case "master": master.New(logger).Register(mux)   // :15000
case "agent":  agent.New(logger).Register(mux)    // :15001
default:       os.Exit(1)                          // fail-closed: 모드 없이 뜨지 않는다
}
```
리포 하나·이미지 하나·배포 방법 하나. .9는 같은 이미지로 master(:15000)와
agent(:15001)를 **둘 다** 띄운다 — master도 자기 호스트 배포는 agent를 거치므로
"배포 실행 경로"가 호스트마다 완전히 동일해진다.

### 선택 — 에이전트는 컨테이너 (sudo 회피)

systemd 등록엔 sudo(암호)가 필요해서 자동화가 막힌다. 대신 docker.sock을 마운트한
컨테이너로 — 컨테이너가 호스트 docker를 조종한다:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock     # 호스트 docker 제어
  - ${HOME}/study-note-deploy-system-llm:${HOME}/study-note-deploy-system-llm  # compose 디렉토리
```

### 가드 4겹 (원격 실행 서버라서)

```go
① 상수시간 시크릿 비교 + 빈 설정이면 전부 거절 (fail-closed)
② 서비스 allowlist: env의 고정 열거(AGENT_URL_*·DEPLOY_DIR_*)에 있는 것만 — 임의 경로·명령 불가
③ 커밋 sha 정규식 ^[0-9a-f]{7,64}$ — 셸 주입·임의 ref 차단
④ 에이전트 single-flight(TryLock) — 동시 배포 1건
```

### 로그 — RESP를 직접 쓴 이유

규약(XADD 한 명령)을 위해 redis 클라이언트 라이브러리를 넣는 건 과잉이라, Redis 유선
프로토콜(RESP)을 30줄로 직접 쓴다:

```go
// *8\r\n$4\r\nXADD\r\n$4\r\nlogs\r\n ... — TCP로 이 문자열을 보내면 끝
command := respArray("XADD", stream, "MAXLEN", "~", "10000", "*", "level", level, "line", line)
```
의존성 0 + "프로토콜이 별 게 아니다"를 확인하는 학습 효과. 실패는 300ms 타임아웃 +
30초 백오프로 흡수(규약: 로그가 요청을 인질로 잡지 않는다).

## 3. 구현 중 마주친 문제

### .9에서 master·agent 동시 기동 — compose 변수의 두 얼굴

```
error while interpolating services.ci-cd.container_name: required variable MODE is missing
```
`env_file:`은 **컨테이너 안**에 넣는 값이고, `container_name: ci-cd-${MODE}` 보간은
**compose 파싱 시점** 값이라 서로 다른 채널이다. `--env-file .env.master`로 파싱 시점
값을 공급해야 했다(파일 안에 ENV_FILE=자기자신도 넣어 컨테이너용 채널도 해결).
**교훈**: compose에서 `${VAR}`가 어느 시점(파싱 vs 런타임)에 풀리는지 늘 구분할 것.

## 4. 결론

단일 바이너리·가드 4겹·의존성 0 로거. go test 9건(거절 경로 우선). PR: #5
