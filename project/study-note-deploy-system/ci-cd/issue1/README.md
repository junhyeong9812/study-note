# issue1 — MODE 하나로 master도 agent도 되는 Go 서버

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-ci-cd
- 이슈 #1·#2·#3 · PR: https://github.com/junhyeong9812/study-note-deploy-system-ci-cd/pull/5

---

## 1. 무엇이 문제였나 — 수동 배포를 자동화하되, 남의 호스트를 만지는 서버다

지금까지 배포는 rsync + ssh 수동이었다. 이걸 "push 한 번 → 자동 배포"로 바꾼다. jun-bank에서
한 번 만들어봤지만, 이번엔 그 코드를 **안 보고 논리를 처음부터 다시 쌓는다**(학습 목적 —
완성 후 옛 코드와 비교 스터디 예정).

구조는 사용자가 결정했다: **.9 호스트가 master(접수·라우팅), 세 호스트 전부 agent(실제 배포
실행), 단일 코드베이스를 `.env`의 MODE 값으로 전환.**

이 서버는 성격이 특별하다 — 잘못되면 화면이 이상한 정도가 아니라 **남의 호스트에서 임의
명령이 돈다.** 그래서 처음부터 "가드를 여러 겹" 두는 걸 전제로 설계했다.

---

## 2. 무엇을 고민했나 → 그래서 이렇게

### 결정 1 — 역할별로 리포를 나눌까, MODE 하나로 갈까

리포 둘·이미지 둘·배포 방법 둘은 관리 표면이 두 배가 된다. 대신 **단일 바이너리가
MODE로 갈라지게** 했다.

```go
// cmd/server/main.go
switch mode {
case "master":
    master.New(logger).Register(mux)   // :15000 (접수·라우팅)
    defaultPort = "15000"
case "agent":
    agent.New(logger).Register(mux)    // :15001 (compose 실행)
    defaultPort = "15001"
default:
    fmt.Fprintln(os.Stderr, "MODE must be master or agent")
    os.Exit(1)                          // fail-closed: 모드 없이는 뜨지 않는다
}
```

> 용어 — fail-closed: 설정이 빠지거나 애매하면 "일단 돌리기"가 아니라 "아예 멈추기"를
> 기본값으로 삼는 것. 배포 서버처럼 위험한 것은 애매할 때 열려 있으면 안 된다.

리포 하나·이미지 하나·배포 방법 하나. .9는 같은 이미지로 master(:15000)와 agent(:15001)를
**둘 다** 띄운다 — master도 자기 호스트 배포는 agent를 거치므로 "배포 실행 경로"가 호스트마다
완전히 동일해진다.

### 결정 2 — agent를 어떻게 호스트 docker에 접근시킬까

systemd 서비스 등록에는 sudo(암호)가 필요해 자동화가 막힌다. 대신 **docker.sock을 마운트한
컨테이너**로 만들어, 컨테이너가 호스트 docker를 조종하게 했다.

```yaml
# docker-compose.yml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock     # agent: 호스트 docker 제어
  - ${HOME}/study-note-deploy-system-front:${HOME}/...    # compose 디렉토리들
  - ${HOME}/study-note-deploy-system-backend:${HOME}/...
  - ${HOME}/study-note-deploy-system-llm:${HOME}/...
```

> 용어 — docker.sock: "호스트의 도커를 조종하는 리모컨". 이게 마운트된 컨테이너는 호스트에서
> 컨테이너를 띄우고 지울 수 있다. 강력한 만큼, 이 권한을 누가 쥐느냐가 이후 이슈(리뷰)의
> 핵심 쟁점이 된다.

### 결정 3 — 원격 실행 서버라서, 가드를 4겹으로

```
① 상수시간 시크릿 비교 + 빈 설정이면 전부 거절 (fail-closed)
② 서비스 allowlist: env의 고정 열거(AGENT_URL_*·DEPLOY_DIR_*)에 있는 것만
     → 임의 경로·임의 명령 불가
③ 커밋/태그 정규식 검증 → 셸 주입·임의 ref 차단
④ agent single-flight(TryLock) → 동시 배포는 1건만
```

`shared/auth.go` — ①의 실제 코드:

```go
const SecretHeader = "X-Deploy-Secret"

// 상수시간 비교. 빈 설정은 항상 거절(fail-closed).
func SecretMatches(request *http.Request, configured string) bool {
    if configured == "" {
        return false
    }
    provided := request.Header.Get(SecretHeader)
    return subtle.ConstantTimeCompare([]byte(provided), []byte(configured)) == 1
}
```

> 용어 — 상수시간(constant-time) 비교: 문자열이 몇 글자째에서 틀렸는지에 따라 비교 시간이
> 달라지면, 공격자가 그 시간차로 시크릿을 한 글자씩 알아낼 수 있다(타이밍 공격).
> `subtle.ConstantTimeCompare`는 항상 같은 시간을 쓴다.

`agent/agent.go` — ②③④가 한 핸들러에 순서대로 걸린다:

```go
directory, allowed := agent.directories[payload.Service]   // ② allowlist
if !allowed {
    shared.WriteFail(writer, 422, "unknown_service", payload.Service); return
}
if !validTag.MatchString(payload.ImageTag) {               // ③ 태그 정규식
    shared.WriteFail(writer, 422, "invalid_tag", ""); return
}
if !agent.busy.TryLock() {                                 // ④ single-flight
    shared.WriteFail(writer, 409, "deploy_in_progress", ""); return
}
defer agent.busy.Unlock()
```

(`validTag = ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` — 셸 메타문자를 원천 차단. 이후 issue2의
git-pull 전환에서 이 검증은 커밋 해시 전용 `^[0-9a-f]{7,64}$`로 더 좁혀진다.)

> 용어 — single-flight: "동시에 한 번만". `TryLock`은 잠금이 이미 잡혀 있으면 기다리지 않고
> 즉시 실패를 돌려준다 — 그래서 배포 중에 또 배포 요청이 오면 409로 바로 거절한다.

### 결정 4 — 로그 규약을 위해 redis 라이브러리를 넣을까

규약(XADD 한 명령)을 위해 redis 클라이언트 라이브러리를 통째로 넣는 건 과잉이라, Redis 유선
프로토콜(RESP)을 직접 30줄로 썼다.

```go
// shared/logger.go — RESP: XADD <stream> MAXLEN ~ 10000 * level <level> line <line>
command := respArray("XADD", logger.stream, "MAXLEN", "~", "10000", "*",
                     "level", level, "line", line)
connection, err := net.DialTimeout("tcp", logger.redisAddress, 300*time.Millisecond)
if err != nil {
    logger.disabledUntil = time.Now().Add(30 * time.Second)   // 백오프 — 로그가 요청을 인질로 잡지 않는다
    return
}
```

> 용어 — RESP(REdis Serialization Protocol): Redis가 쓰는 아주 단순한 텍스트 프로토콜.
> `*3\r\n$4\r\nXADD\r\n...` 처럼 "몇 개짜리 배열, 각 항목 몇 바이트"를 TCP로 보내면 끝이다.
> 라이브러리 없이 직접 쓸 만큼 단순하다는 걸 확인하는 학습 효과도 노렸다.

의존성 0 + "프로토콜이 별 게 아니다"를 확인. 실패는 300ms 타임아웃 + 30초 백오프로 흡수한다
(규약: 로그가 요청을 인질로 잡지 않는다 — llm issue2와 동일 원칙).

---

## 3. 구현 중 마주친 문제

### 문제 — .9에서 master·agent 동시 기동, compose 변수의 두 얼굴

.9 한 호스트에서 master와 agent를 **동시에** 띄우려 하니:

```
error while interpolating services.ci-cd.container_name: required variable MODE is missing
```

**원인**: compose에서 `${VAR}`는 **두 개의 다른 채널**에서 풀린다.

```
env_file: .env          → 컨테이너 안에 넣어줄 값 (런타임 채널)
container_name: ci-cd-${MODE}   → compose가 파일을 파싱하는 시점의 값 (파싱 채널)
```

`env_file`은 컨테이너 **안**에 들어가는 값이라, compose가 파일을 읽어 `container_name`을
정하는 **파싱 시점**엔 아직 존재하지 않는다. 서로 다른 채널이다.

**그래서 이렇게** (`docker-compose.yml`, `feat 969f248`): env_file 자체를 변수로 만들어
`--env-file`로 파싱 시점 값을 공급했다.

```diff
-    env_file: .env
+    env_file: ${ENV_FILE:-.env}
```

`.9`는 `ENV_FILE=.env.master docker compose ...` / `ENV_FILE=.env.agent ...`로 각각 기동
(파일 안에 `ENV_FILE=자기자신`도 넣어 컨테이너용 런타임 채널도 해결). **교훈**: compose에서
`${VAR}`가 어느 시점(파싱 vs 런타임)에 풀리는지 늘 구분할 것.

---

## 4. 결론

단일 바이너리(MODE 전환)·가드 4겹·의존성 0 로거. go test 9건(거절 경로 우선 — 401·422·409).
응답은 llm·backend와 같은 success 봉투 규약을 따른다. PR: #5. 실제 배선과 E2E는 issue2에서.
