# issue/infra/compose-variable-resolution-timing — compose ${VAR}의 두 채널(파싱 vs 런타임) — 질문

## 질문
1. (왜) docker compose 파일에서 `${VAR}`가 풀리는 시점이 왜 하나가 아닌가. `container_name: ci-cd-${MODE}`의 `MODE`와 `env_file`이 컨테이너에 주입하는 `MODE`는 각각 **언제·누가** 읽는가.
2. (예측) `env_file: .env`에 `MODE=master`를 넣고 `container_name: ci-cd-${MODE}`를 썼다. compose는 무엇을 출력하며(`${MODE}`와 `${MODE:?}`에서 각각), 왜 env_file의 값으로 container_name을 못 채우는가.
3. (경계) 파싱 채널(파일 로드 시점 interpolation)이 값을 얻는 출처는 어디어디인가 — 셸 환경변수·`--env-file`·프로젝트 디렉터리 `.env` 자동 로드. `env_file:` 지시자는 왜 그중 어디에도 끼지 못하는가.
4. (연결) 앞선 사례의 "`image:`와 `build:`가 같이 있으면 `compose pull`이 그 서비스를 건너뛴다(Skipped)"도 같은 부류의 함정인가. "내 의도"와 "도구의 해석"이 갈린 지점은 어디인가.
5. (경계) `env_file: ${ENV_FILE:-.env}`처럼 **파일명 자체를 변수화**하면 무엇이 풀리는가. 현재 코드가 쓰는 `profiles` + 파일 분리(`.env.master`/`.env.agent`) 방식은 같은 문제를 어떻게 우회하는가.
6. (일반화) 처음 보는 도구의 설정 파일에서 `${VAR}` 류 치환을 만났을 때 가장 먼저 던져야 할 질문 한 문장은 무엇인가.

## 복습 기록
| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
