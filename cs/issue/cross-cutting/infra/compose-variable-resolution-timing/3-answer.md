# cs/issue/infra/compose-variable-resolution-timing — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

## 정답
<!-- 질문 1:1 대응 -->

1. `${VAR}`는 서로 다른 **두 시점**에 풀린다. **파싱 채널** — compose가 YAML을 읽어 해석하는 build-time에 `container_name`·`image`·`ports` 같은 필드의 치환을 수행한다. **런타임 채널** — `env_file`/`environment:`가 지정한 값은 컨테이너가 뜬 **안**에 주입되어 프로세스가 실행 중 읽는다. `ci-cd-${MODE}`의 `MODE`는 compose(파싱 채널)가, `env_file`의 `MODE`는 컨테이너 프로세스(런타임 채널)가 읽는다 — 읽는 주체도 시점도 다르다.
   > **interpolation(변수 치환)** — compose가 파일을 파싱하며 `${VAR}`를 그 시점의 값으로 바꾸는 것. 컨테이너 생성 전에 일어난다.

2. compose는 `required variable MODE is missing`(services.ci-cd.container_name 보간 실패)을 낸다. `env_file`은 **컨테이너 안**에 넣을 값이라, compose가 파일을 읽어 `container_name`을 정하는 **파싱 시점**엔 아직 존재하지 않기 때문이다. 두 값은 이름만 같을 뿐 다른 채널에 산다.

3. 파싱 채널의 출처는 ① compose를 실행한 **셸의 환경변수** ② `--env-file <파일>`로 명시한 파일 ③ compose 파일과 **같은 폴더의 `.env`** 자동 로드, 셋이다. `env_file:` 지시자는 이 셋 중 어디에도 안 낀다 — 그것은 "이 컨테이너 안에 넣어라"라는 별개의 런타임 지시이지, compose 자신이 파싱에 쓰는 변수원이 아니다.
   > **`--env-file` vs `env_file:`** — 앞은 compose 프로세스가 파싱에 쓸 변수 파일(파싱 채널), 뒤는 컨테이너 안에 주입할 변수 파일(런타임 채널). 철자가 비슷해 헷갈리지만 정반대 방향이다.

4. 같은 부류다 — 둘 다 "도구의 해석"이 "내 의도"를 이긴 사례다. `image: ghcr…${TAG}` + `build: ./wrapper`를 병존시켜 "배포는 pull, 로컬은 build"를 노렸지만, compose는 `build:`가 있으면 그 서비스를 **로컬 빌드 대상**으로 분류하고 `image:`를 "받을 주소"가 아니라 "**빌드 결과에 붙일 이름표**"로 해석한다. 그래서 `compose pull wrapper`가 `Skipped - No image to be pulled`가 됐다. 갈린 지점 = 키의 병존이 내겐 "둘 다"였지만 도구에겐 "빌드하는 서비스"라는 단일 의미였다는 것.
   > **build:와 image:의 병존** — compose에서 이 둘이 함께 있으면 "빌드해서 이 이름표를 붙인다"로 읽힌다. pull 대상이 아니다.

5. `env_file: ${ENV_FILE:-.env}`는 **파일명 자체를 파싱 채널 변수로** 만든다 → `ENV_FILE=.env.master docker compose ...`로 파싱 시점에 어떤 env 파일을 쓸지 공급할 수 있다(파일 안에 `ENV_FILE=자기자신`도 넣어 런타임 채널까지 해결). 현재 코드의 `profiles`(`master`/`agent`) + `.env.master`/`.env.agent` 분리 방식은 **변수 분기 자체를 없애** 우회한다 — `container_name`을 리터럴(`ci-cd-master`)로 고정하고 서비스를 둘로 나눠, 파싱 시점에 풀 `${MODE}`가 애초에 없다.
   > **profiles** — compose 서비스에 라벨을 달아 `--profile <name>`으로 선택 기동하는 기능. `.9`는 `--profile master --profile agent`로 둘 다, 나머지 호스트는 `--profile agent`만 띄운다.

6. "이 `${VAR}`는 파일을 **파싱할 때** 풀리는가, 컨테이너 **안에서** 쓰이는가?" — 이 한 질문이 값을 어느 채널(셸/`--env-file`/`.env` vs `env_file:`/`environment:`)로 공급해야 하는지를 결정한다.

## 이번 프로젝트 사례
- [ci-cd/issue1](../../../../../project/study-note-deploy-system/ci-cd/issue1/) — `.9`에서 master·agent 동시 기동 시 `container_name: ci-cd-${MODE}`가 `required variable MODE is missing`. `env_file: ${ENV_FILE:-.env}`로 파일명을 변수화해 파싱 채널에 값 공급(현재 코드는 profiles로 진화).
- [ci-cd/issue2](../../../../../project/study-note-deploy-system/ci-cd/issue2/) — ② `image:`+`build:` 병존 → `compose pull wrapper` Skipped. 같은 "도구의 해석 vs 의도" 함정.

## 검증 기록
- 2026-09-23: 이슈 README(ci-cd/issue1·2) + 현재 `study-note-deploy-system-ci-cd/docker-compose.yml`(profiles·`.env.master`/`.env.agent`) 대조 작성. 과거 `${MODE}` interpolation·`${ENV_FILE:-.env}` 근거는 README 정본(현재 compose는 profiles로 진화함을 확인). Claude 초안.
