# cs/issue/infra/compose-variable-resolution-timing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
compose가 ${VAR}를 만나는 순간은 두 번, 서로 다른 채널이다.

① 파싱 채널 (파일 로드 시점 interpolation — 이미지 빌드와 무관)
   compose가 YAML을 "읽어 해석하는" 시점.
   container_name·image·ports 같은 필드의 ${VAR}가 여기서 풀린다.
   값 출처 = 셸 환경변수 / --env-file / 프로젝트 디렉터리 .env 자동 로드.
      ↓ 이 시점엔 컨테이너가 아직 없다.

② 런타임 채널 (env_file / environment:)
   컨테이너가 뜬 "안"에 주입되는 값.
   프로세스가 실행 중에 os.Getenv로 읽는다.

핵심 함정: env_file은 ②(컨테이너 안)이라, ①(파일 파싱)에는 존재하지 않는다.
  → container_name: ci-cd-${MODE} 는 env_file의 MODE를 절대 못 본다
  → 경고 후 빈 값, ${MODE:?}면 "required variable MODE is missing"
```

같은 부류: `image:` + `build:` 병존 → compose는 "빌드하는 서비스"로 **해석**하고,
`image:`를 "받을 주소"가 아니라 "빌드 결과 이름표"로 본다 → (관측 버전에서) `compose pull`이 Skipped.
둘 다 "내 의도"가 아니라 **도구의 파싱 규칙**이 동작을 정한다.

## 핵심 문장
- `${VAR}`를 보면 "이게 파일을 **파싱할 때** 풀리나, 컨테이너 **안에서** 쓰이나"를 먼저 가른다.
- `env_file`은 런타임 전용이다 — 파싱 시점 필드(container_name 등)엔 셸/`--env-file`/`.env`로 공급해야 한다.
- 해법 계열: 파일명을 변수화(`env_file: ${ENV_FILE:-.env}`)해 파싱 채널 값을 넣거나, `profiles`로 서비스를 나눠 변수 분기 자체를 없앤다.
- 도구의 키 조합은 내 의도가 아니라 **도구의 해석**으로 동작한다 — 성공 로그가 아니라 산출물(container image·created)을 본다.
