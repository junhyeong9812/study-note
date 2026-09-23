# infra — 플랫폼·툴 (compose·git·nginx·배포)

docker compose·git·nginx 같은 운영 도구의 **해석 시점·기본 동작·광역 규칙**에서 터지는 부류.

| 패턴 | 한 줄 | 사례 이슈 |
|------|-------|-----------|
| [compose-variable-resolution-timing](compose-variable-resolution-timing/) | `${VAR}`가 파싱 채널(container_name)과 런타임 채널(env_file)에서 다르게 풀림 | ci-cd1·2 |
| [state-drift-delete-propagation](state-drift-delete-propagation/) | 삭제 전파 부재(rsync --delete)·설정 전달 실패 → git 단일 채널로 수렴 | be6 · ci-cd2 |
| [git-pitfalls](git-pitfalls/) | dubious-ownership·빈 디렉토리 미추적·quotepath 8진수 | ci-cd2 · front3 · be2 |
| [nginx-broadband-defense-friendly-fire](nginx-broadband-defense-friendly-fire/) | 광역 방어(봇 UA 차단)가 자체 자동화를 오사(self-DoS) → allowlist | ci-cd5 |
