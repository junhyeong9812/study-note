# cs/issue — 실전 이슈에서 뽑은 CS 패턴 아카이브

study-note-deploy-system(개인 위키+검색+챗봇 배포 시스템)을 만들며 실제로 겪은 이슈들을,
**프로젝트 밖에서도 통하는 재사용 가능한 CS 패턴**으로 추상화해 모은 곳이다.
프로젝트별 상세 이력은 [project/study-note-deploy-system](../../project/study-note-deploy-system/)에 있고,
여기 각 카드는 그 이슈들을 **패턴 단위로 묶어** 링크한다(예: silent-failure 카드 하나가 7개 이슈를 가리킨다).

## 분류 두 축

1. **소속(폴더)** — 이슈가 뿌리내린 곳:
   - **언어별** (프레임워크는 언어 하위 중첩): `kotlin/spring/`, `typescript/react·next/`, `python/fastapi/`
   - **cross-cutting** — 언어 무관 시스템·네트워크: `cross-cutting/{reliability, network, infra, security}/`
2. **메타 태그** — 폴더를 가로지르는 반복 주제(각 카드 본문에 표기): `silent-failure`(성공≠산출물) · `resource-bounding`(자원 상한) · `least-privilege`(최소권한·비밀).

## 포맷

각 패턴 = 폴더 하나(`1-question.md` / `2-summary.md` / `3-answer.md`) — 기존 cs 리프와 같은 인출퀴즈 방식.
질문에서 출발해 기억으로 답하고, 막히면 정리, 최후에 정답. 정답은 이슈 README·실코드가 기준.
상위 폴더(계층)는 `README.md`가 추상화+링크 인덱스, 리프(패턴)는 1/2/3.

> **작성 규약 정본**: [authoring-guide.md](authoring-guide.md) — 무엇을 한 카드로 묶나·폴더 분류 2축·파일 형태·서술 규칙(도식화·근거 노출·시크릿 금지). 새 패턴을 추가할 땐 이 가이드를 따른다.

## Phase 1 — cross-cutting (시스템·네트워크)

### reliability — 신뢰성
- [silent-failure-vs-artifact](cross-cutting/reliability/silent-failure-vs-artifact/) — "성공 로그·exit 0 ≠ 산출물". 성공을 산출물로 검증하라 (backend2·10, front3, llm1·3, ci-cd2·3)
- [resource-bounding-last-defense](cross-cutting/reliability/resource-bounding-last-defense/) — 클라이언트 타임아웃은 서버측 생성을 못 멈춘다 → 서버 자원 상한이 유일 방어선 (llm1, backend5·12, front5, ci-cd1)

### network — 프로토콜·연결
- [chunked-vs-content-length](cross-cutting/network/chunked-vs-content-length/) — chunked transfer-encoding vs Content-Length 불일치 → 0바이트 (backend12, ci-cd4)
- [http-streaming-status-locked](cross-cutting/network/http-streaming-status-locked/) — 200 헤더 전송 순간 status 확정 → 스트림 시작 후 오류코드 못 바꿈 (llm6)
- [bind-address-loopback-vs-lan](cross-cutting/network/bind-address-loopback-vs-lan/) — fail-closed 바인딩 vs 헬스체크 127.0.0.1 불일치 → 정상인데 unhealthy (backend1·9, ci-cd3)
- [proxy-passthrough](cross-cutting/network/proxy-passthrough/) — 프록시 버퍼링·status 보존·쿠키 양방향 왕복 (front3·11)
- [reverse-tunnel-nat-traversal](cross-cutting/network/reverse-tunnel-nat-traversal/) — 서브넷 단절 → 연결 방향 역전(역SSH터널+socat) (ci-cd4)

### infra — 플랫폼·툴
- [compose-variable-resolution-timing](cross-cutting/infra/compose-variable-resolution-timing/) — compose `${VAR}` 파싱채널 vs 런타임채널 (ci-cd1·2)
- [state-drift-delete-propagation](cross-cutting/infra/state-drift-delete-propagation/) — 삭제 전파 부재·설정 채널 → git 단일 채널 (backend6, ci-cd2)
- [git-pitfalls](cross-cutting/infra/git-pitfalls/) — dubious-ownership·빈디렉토리 미추적·quotepath (ci-cd2, front3, backend2)
- [nginx-broadband-defense-friendly-fire](cross-cutting/infra/nginx-broadband-defense-friendly-fire/) — 광역 방어의 아군 오사(self-DoS) → allowlist (ci-cd5)

### security — 비밀·권한
- [secret-ownership-least-privilege](cross-cutting/security/secret-ownership-least-privilege/) — 비밀 단일소유·정본은 실사용처·최소권한 (backend10, front4, ci-cd3)

## Phase 2 — 언어별 (예정)
`kotlin/spring/`(직렬화 누출·DIP·인코딩) · `typescript/`(BFF envelope·모듈정책·CSS overflow·XSS·SSOT) · `python/fastapi/`(응답정규화·PYTHONPATH·YAGNI). 착수 예정.
