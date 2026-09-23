# cs/issue/infra/compose-variable-resolution-timing — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `environment-drift`

## 정답
<!-- 질문 1:1 대응 -->

1. `${VAR}`는 서로 다른 **두 시점**에 풀린다. **파싱 채널** — compose가 YAML을 읽어 해석하는 파일 로드 시점(이미지 빌드와 무관)에 `container_name`·`image`·`ports` 같은 필드의 치환을 수행한다. **런타임 채널** — `env_file`/`environment:`가 지정한 값은 컨테이너가 뜬 **안**에 주입되어 프로세스가 실행 중 읽는다. `ci-cd-${MODE}`의 `MODE`는 compose(파싱 채널)가, `env_file`의 `MODE`는 컨테이너 프로세스(런타임 채널)가 읽는다 — 읽는 주체도 시점도 다르다.
   > **interpolation(변수 치환)** — compose가 파일을 파싱하며 `${VAR}`를 그 시점의 값으로 바꾸는 것. 컨테이너 생성 전에 일어난다.

2. `${MODE}`라면 compose는 `The "MODE" variable is not set. Defaulting to a blank string.` 경고와 함께 빈 문자열로 풀어 `ci-cd-`가 되고, `${MODE:?}`처럼 필수 표기를 썼다면 `required variable MODE is missing`(container_name 보간 실패)으로 중단한다 — 어느 쪽이든 env_file의 값은 쓰이지 않는다. `env_file`은 **컨테이너 안**에 넣을 값이라, compose가 파일을 읽어 `container_name`을 정하는 **파싱 시점**엔 아직 존재하지 않기 때문이다. 두 값은 이름만 같을 뿐 다른 채널에 산다.

3. 파싱 채널의 출처는 ① compose를 실행한 **셸의 환경변수** ② `--env-file <파일>`로 명시한 파일 ③ 프로젝트 디렉터리(기본은 compose 파일 위치 — 구버전은 작업 디렉터리)의 **`.env`** 자동 로드, 셋이다(`--env-file`을 주면 기본 `.env` 대신 그 파일을 쓴다). `env_file:` 지시자는 이 셋 중 어디에도 안 낀다 — 그것은 "이 컨테이너 안에 넣어라"라는 별개의 런타임 지시이지, compose 자신이 파싱에 쓰는 변수원이 아니다.
   > **`--env-file` vs `env_file:`** — 앞은 compose 프로세스가 파싱에 쓸 변수 파일(파싱 채널), 뒤는 컨테이너 안에 주입할 변수 파일(런타임 채널). 철자가 비슷해 헷갈리지만 정반대 방향이다.

4. 같은 부류다 — 둘 다 "도구의 해석"이 "내 의도"를 이긴 사례다. `image: ghcr…${TAG}` + `build: ./wrapper`를 병존시켜 "배포는 pull, 로컬은 build"를 노렸지만, compose는 `build:`가 있으면 그 서비스를 **로컬 빌드 대상**으로 분류하고 `image:`를 "받을 주소"가 아니라 "**빌드 결과에 붙일 이름표**"로 해석한다. 그래서 `compose pull wrapper`가 `Skipped - No image to be pulled`가 됐다(관측된 버전 기준 — Compose 버전에 따라 build+image 서비스도 pull을 시도하고 실패 시 빌드로 넘기며, `--ignore-buildable`로 건너뛰게 할 수 있다). 갈린 지점 = 키의 병존이 내겐 "둘 다"였지만 도구에겐 "빌드하는 서비스"라는 단일 의미였다는 것.
   > **build:와 image:의 병존** — compose에서 이 둘이 함께 있으면 "빌드해서 이 이름표를 붙인다"로 읽힌다. pull 대상으로 다룰지는 버전·옵션(`--ignore-buildable`, `pull_policy`)에 따라 다르다.

5. `env_file: ${ENV_FILE:-.env}`는 **파일명 자체를 파싱 채널 변수로** 만든다 → `ENV_FILE=.env.master docker compose ...`로 파싱 시점에 어떤 env 파일을 쓸지 공급할 수 있다(파일 안에 `ENV_FILE=자기자신`도 넣어 런타임 채널까지 해결). 현재 코드의 `profiles`(`master`/`agent`) + `.env.master`/`.env.agent` 분리 방식은 **변수 분기 자체를 없애** 우회한다 — `container_name`을 리터럴(`ci-cd-master`)로 고정하고 서비스를 둘로 나눠, 파싱 시점에 풀 `${MODE}`가 애초에 없다.
   > **profiles** — compose 서비스에 라벨을 달아 `--profile <name>`으로 선택 기동하는 기능. 마스터 호스트는 `--profile master --profile agent`로 둘 다, 나머지 호스트는 `--profile agent`만 띄운다.

6. "이 `${VAR}`는 파일을 **파싱할 때** 풀리는가, 컨테이너 **안에서** 쓰이는가?" — 이 한 질문이 값을 어느 채널(셸/`--env-file`/`.env` vs `env_file:`/`environment:`)로 공급해야 하는지를 결정한다.

## 문제 구조 (추상화 코드)

### 변형 A — 런타임 채널 값으로 파싱 시점 필드를 채우려 함
① 문제 코드
```yaml
services:
  app:
    container_name: app-${MODE}     # 파싱 채널: 셸 / --env-file / 같은 폴더 .env
    env_file: .env.master           # 런타임 채널: 컨테이너 안에만 MODE=master
# → 경고 후 빈 값(app-) / ${MODE:?}였다면 required variable MODE is missing
```
② 고친 코드
```yaml
services:
  app:
    env_file: ${ENV_FILE:-.env}     # 파일명 자체를 파싱 채널 변수로
    # container_name에 ${MODE}를 계속 쓰려면 MODE도 셸/--env-file/.env로 공급해야 한다
# ENV_FILE=.env.master docker compose up -d
```
진화한 형태(변수 분기 제거):
```yaml
services:
  app-master:
    container_name: app-master      # 리터럴
    profiles: [master]
    env_file: .env.master
  app-agent:
    container_name: app-agent
    profiles: [agent]
    env_file: .env.agent
```
깨진 것: 이름만 같은 두 채널의 변수를 하나로 여겼다.

### 변형 B — 키 조합을 도구가 다르게 해석
① 문제 코드
```yaml
services:
  wrapper:
    image: registry.example/wrapper:${TAG}   # 의도: 배포는 pull
    build: ./wrapper                         # 의도: 로컬은 build
# docker compose pull wrapper → Skipped - No image to be pulled
```
② 고친 코드
```yaml
# 배포용 파일: image만 (pull 대상)
services:
  wrapper:
    image: registry.example/wrapper:${TAG}
# 로컬 빌드는 별도 override 파일에서 build: 지정
```
깨진 것: `build:`가 있으면 `image:`는 "받을 주소"가 아니라 "빌드 결과 이름표"로 해석된다.

## 검증 기록
- 2026-09-23: 원 사례 원문 대조 작성 (Claude 초안).
- 2026-09-24: 출처 표기를 추상화 코드 구조로 전환 + 방안 비교 추가, 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

> 같은 원리("값·설정이 어느 채널로, 언제, 누구에게 도달하는가")에서 나온 다른 해결 방안들이다. 각 방안은 **값이 도달하지 않는 채널이 어디였는가**에 따라 갈린다.

### 방안 1 — 초기화 채널: 빈 볼륨 최초 1회만 적용되는 설정을 별도 절차로 재적용
① 문제 코드
```yaml
services:
  db:
    image: postgres
    environment: [ "POSTGRES_PASSWORD=${DB_PASSWORD}" ]
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      - dbdata:/var/lib/postgresql/data     # 이미 데이터가 있으면 init·비번 설정 건너뜀
# 스키마·비번을 바꾸고 compose up → 반영 안 됨
```
② 고친 코드
```sh
# 스키마: init.sql이 IF NOT EXISTS 등으로 멱등일 때만 안전하게 수동 재적용
docker compose exec db psql -U "$POSTGRES_USER" -f /docker-entrypoint-initdb.d/init.sql   # exec 기본 사용자는 DB 롤이 아님
# 또는 볼륨 초기화(데이터 폐기 전제) / 비번 로테이션은 별도 절차
```
깨진 것: 공식 엔트리포인트는 데이터 디렉터리가 비었을 때만 초기화 스크립트와 비번 설정을 실행한다.

### 방안 2 — 명령별 로드 범위: 모든 하위 명령에 env를 대칭 주입(+ placeholder)
① 문제 코드
```go
run("docker", "pull", digest)             // compose 아님 → 영향 없음
run("compose", "up", "-d")                 // env: IMAGE=digest
run("compose", "ps", "-q")                 // env 없음 → image: ${IMAGE} 비어 프로젝트 로드 실패
// 실패 → cleanup → run("compose","down") // env 없음 → 역시 실패 → 결과 UNKNOWN
```
② 고친 코드
```go
const placeholder = "noncreate.invalid/unused:0"      // pull 불가 값
envFor := func(cmd string) []string {
    if cmd == "up" { return []string{"IMAGE=" + digest} }  // 실 digest는 up에만
    return []string{"IMAGE=" + placeholder}           // ps·down·status도 프로젝트 로드 성립
}
```
깨진 것: compose는 어떤 하위 명령이든 프로젝트를 로드할 때 모든 서비스의 image를 먼저 보간·검증하므로, env를 `up`에만 주면 조회·정리 명령이 성립하지 않았다.\
선택하지 않은 방법: compose 파일에 `${IMAGE:-기본값}` — 대체 이미지가 파일에 남아 "지정 digest만 실행" 원칙을 흐린다.

### 방안 3 — 소비자 채널: 셸이 없는 실행 형식에서는 프로그램이 직접 읽는 변수를 쓴다
① 문제 코드
```dockerfile
ENTRYPOINT ["java", "-jar", "/app.jar"]      # exec-form: 셸 확장 없음
# compose: environment: [ "JAVA_OPTS=-Xmx2g -XX:+UseZGC" ] → 아무도 안 읽음 → 기본 힙(cgroup 25%) → OOM
```
② 고친 코드
```yaml
environment:
  - JAVA_TOOL_OPTIONS=-Xmx8g -XX:+UseZGC -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp
mem_limit: 16g
```
깨진 것: `JAVA_OPTS`는 셸 스크립트 관례일 뿐, exec-form에선 아무도 읽지 않는다 — JVM이 스스로 읽는 것은 `JAVA_TOOL_OPTIONS`다(JDK 9+의 `java` 런처는 `JDK_JAVA_OPTIONS`도 읽는다).

### 방안 4 — 대상 범위: 서비스 미지정 pull/up은 파일 전체가 대상
① 문제 코드
```go
run("compose", "pull")        // 같은 파일의 무관한 대용량 이미지까지 갱신 → 타임아웃(정확히 4:00)
run("compose", "up", "-d")    // 무관한 서비스까지 재생성될 수 있음
```
② 고친 코드
```go
pull := []string{"compose", "pull"}
up := []string{"compose", "up", "-d"}
if svc != "" {                // 배포 대상 서비스명을 설정으로 받음
    pull = append(pull, svc)
    up = append(up, svc)
}
```
깨진 것: 도구의 기본 범위(전체 서비스)가 "배포 단위 = 그 서비스"라는 의도와 달랐다.\
진단 요령: 실패 시각이 정확히 타임아웃 값이면 "느린 게 아니라 우리가 끊은 것" — pull 로그의 레이어로 대상 이미지를 식별한다.

### 비교 표

| 방안 | 전제 | 비용 | 실패 모드(안 했을 때) | 맞는 조건 |
|------|------|------|------------------------|-----------|
| 1 초기화 채널 재적용 | 설정이 "최초 1회" 채널에 있다 | 수동 절차·볼륨 초기화 시 데이터 폐기 | 바꿨는데 조용히 미반영 | 공식 이미지의 init 스크립트·초기 비번 |
| 2 대칭 주입 + placeholder | 모든 하위 명령이 같은 보간을 거친다 | 명령별 env 표 유지 | 조회·정리 명령 불성립 → 거짓 UNKNOWN | 필수 변수(무기본값)를 쓰는 compose를 프로그램이 구동 |
| 3 소비자가 읽는 변수 | 실행 형식에 셸이 없다 | 변수 이름을 런타임 규약에 맞춤 | 옵션 무시 → 기본값으로 동작(OOM 등) | exec-form ENTRYPOINT의 JVM 컨테이너 |
| 4 서비스 명시 | 한 파일에 여러 서비스 | 배포 대상명 설정 추가 | 무관한 서비스 갱신·재생성·타임아웃 | 여러 서비스가 한 compose에 공존 |

**결론**: 우열이 아니라 "값이 끊긴 채널"로 고른다.\
값이 파싱 시점에 없으면 파싱 채널 공급(변형 A) 또는 모든 명령에 대칭 공급(방안 2), 컨테이너 안 프로세스가 안 읽으면 소비자 규약 변수(방안 3), 최초 1회 채널이면 별도 재적용 절차(방안 1), 적용 범위가 넓으면 대상 명시(방안 4).\
공통 첫 질문은 정답 6번과 같다 — "이 값은 언제, 누가 읽는가?"
