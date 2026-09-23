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

## Phase 2 — 언어별

### typescript — TS/React/Next (프레임워크 경계·도구 체계)
- **[typescript/next](typescript/next/)** — Next.js(BFF·라우팅·모듈 해석)
  - [bff-envelope-single-gate](typescript/next/bff-envelope-single-gate/) — 봉투 검사를 페이지마다 하면 잊어 오류를 정상 데이터로 렌더 → BFF 단일창구 정규화(검증 DRY), 가장 위험한 가정 먼저 실증 (front1)
  - [absolute-imports-and-per-tool-resolver](typescript/next/absolute-imports-and-per-tool-resolver/) — 상대/절대 임포트 혼용→파일이동에 깨짐(절대경로 정책) + alias는 도구마다 별도(vitest 리졸버) (front6·7)
  - [single-source-of-truth-routing](typescript/next/single-source-of-truth-routing/) — 노드 종류를 URL·백엔드 이중관리하면 어긋남 → is_subject 단일소스, 캐치올 라우팅, 상대링크 렌더시점 해석 (front2)
- **[typescript/react](typescript/react/)** — React(렌더링·CSS·출력 안전)
  - [css-negative-margin-overflow](typescript/react/css-negative-margin-overflow/) — 부모 패딩 상쇄 음수마진 × overflow → 가로 스크롤. 여백 소유권을 자식에게 (front8)
  - [xss-escape-then-assemble](typescript/react/xss-escape-then-assemble/) — 백엔드 HTML 삽입 → XSS. 텍스트 전체 이스케이프 후 마커만 `<mark>` 조립, 디바운스 (front9·backend11)
  - [separation-structure-vs-style](typescript/react/separation-structure-vs-style/) — 렌더러는 구조만, 표시는 CSS 몫인데 절반 미충족 → 관심사 분리, border-collapse (front10)

### kotlin — Kotlin/JVM·Spring (backend)
- (언어레벨) [charset-and-length-defaults](kotlin/charset-and-length-defaults/) — JVM/프레임워크 기본값이 바이트를 왜곡: ISO-8859-1 인코딩·`String.length`(문자 vs 바이트) (backend2)
- **[kotlin/spring](kotlin/spring/)** — Spring·Jackson·아키텍처
  - [serialization-contract-leak](kotlin/spring/serialization-contract-leak/) — 내부 필드명(camelCase)이 API 계약으로 누출 → snake_case 명시 (backend7)
  - [dip-port-ownership](kotlin/spring/dip-port-ownership/) — 도메인우선·DIP(usecase 포트소유)·특성테스트 안전망 (backend8)
  - [path-traversal-and-data-reality](kotlin/spring/path-traversal-and-data-reality/) — 트래버설 차단 + "버그의 절반은 데이터 실태"(0바이트 원본) (backend3)
  - [graceful-degradation-fault-isolation](kotlin/spring/graceful-degradation-fault-isolation/) — 보조기능 장애가 핵심을 인질 못하게, RRF·폴백 뱃지 (backend4)

### python — Python·FastAPI (llm)
- (언어레벨) [module-resolution-and-accidental-pass](python/module-resolution-and-accidental-pass/) — pytest vs `python -m`의 sys.path 차이로 초록불이 갈림(우연한 통과) (llm3)
- **[python/fastapi](python/fastapi/)** — 응답 경계·기능 표면
  - [response-normalization-framework-boundary](python/fastapi/response-normalization-framework-boundary/) — 프레임워크가 핸들러 밖에서 만드는 응답(422·404·500)이 계약의 구멍 → 예외 핸들러로 봉투 정규화 (llm4)
  - [yagni-dead-contract](python/fastapi/yagni-dead-contract/) — 예측 예약계약은 유지비만 → YAGNI 제거, 결정 흔적은 남김 (llm5)
