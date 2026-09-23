# cs/issue/infra/nginx-broadband-defense-friendly-fire — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

## 정답
<!-- 질문 1:1 대응 -->

1. 엣지 nginx가 스캐너가 흔히 쓰는 UA(`python-requests`·`curl/`·`wget/` 등)를 `map`으로 판별해 `if ($bad_bot) return 444`로 연결 단계에서 끊는다. 그런데 우리 자동화(study-note `sync.yml`, 각 서비스 `deploy.yml`)가 **바로 그 curl로** 엣지를 호출하고, GitHub Actions의 curl 기본 UA는 `curl/8.x`다. 즉 내가 넣은 차단 규칙이 내 파이프라인을 스캐너로 오인해 끊었다 — 봇 차단이 아군을 오사한 self-DoS.
   > **self-DoS / friendly fire** — 자기 방어 규칙이 자기 정상 트래픽(아군)을 막아버리는 것.

2. `444`는 nginx가 **응답을 보내지 않고 연결을 끊는** 특수 코드다(스캐너에 정보 0). 그래서 클라이언트는 HTTP 응답 코드를 받지 못해 `http: 000`(코드 없음)으로 기록하고, HTTP/2에서는 스트림이 중간에 끊겨 `HTTP/2 stream ... was not closed cleanly: PROTOCOL_ERROR`로 보인다. 403/429처럼 "서버가 거절 응답을 준" 게 아니라 "아무 응답 없이 끊긴" 것이라 이런 모양이 된다.
   > **return 444** — nginx 비표준 코드. 응답 헤더·바디 없이 TCP 연결만 종료한다.

3. **B(아군이 고유 UA로 자기를 밝힘)**를 택했다. A(차단에서 curl 제외)는 스캐너도 curl을 쓰므로 curl 전체를 허용하게 되어 방어가 약해진다. 차단의 목적은 "정체불명 스캐너 거르기"인데, 우리 자동화는 정체가 분명하니 그 이름을 대면 된다 — 방어를 약화시키지 않고 오사만 없앤다.

4. 엣지 map은 `~*curl/`, 즉 UA가 **`curl/`로 시작(하위문자열 매치)** 하는 것을 잡는데, `study-note-sync/1.0`(배포는 `study-note-deploy/1.0`)은 `curl/`을 포함하지 않아 규칙에 안 걸린다. `-A`로 UA를 그 고유 이름으로 덮어썼기 때문이다. 함께 붙인 `--http1.1`은, 혹시 444로 끊길 때 HTTP/2에서 나던 `PROTOCOL_ERROR`(더러운 끊김)를 피해 실패를 깔끔한 코드로 받게 한다.
   > **user-agent map** — nginx에서 `$http_user_agent`를 정규식으로 분류해 변수(`$bad_bot`)로 만드는 것. 그 변수로 `if`·rate limit 등을 건다.

5. 광역(broadband) 규칙은 "요청의 **속성**(UA 패턴·요청률·IP 대역)"으로 무차별하게 거르므로, 그 속성을 공유하는 아군까지 함께 걸린다 — 아군이 흔한 도구(curl·python-requests)나 높은 빈도(폭주처럼 보이는 배치)를 쓰면 더 그렇다. 규칙 설계 단계에서 "**내 아군도 이 규칙에 걸리나**"를 먼저 점검하고, 아군을 식별자(고유 UA·허용 IP allowlist)로 **명시적으로 통과**시킨다 — 이는 "curl 제외"식 denylist 완화보다 방어를 덜 깎는다.

6. UA는 클라이언트가 **자유롭게 설정**할 수 있어, 스캐너가 `study-note-sync/1.0`을 흉내 내면 뚫린다 — 약한 식별이다. 그래도 실용적인 이유는 이 규칙의 목표가 "표적 공격 차단"이 아니라 "**무차별 대량 스캔 걸러내기**"라, 우리 UA를 굳이 흉내 낼 표적 공격자는 이 방어의 대상이 아니기 때문이다. 진짜 신뢰가 필요한 경계(예: 배포/색인 트리거)는 별도로 시크릿 헤더나 **HMAC 서명 webhook** 같은 강한 식별을 둔다(그래서 후속 TODO로 남았다).
   > **allowlist(허용 목록)** — 미리 정한 것만 통과시키는 방식. 반대는 denylist(정한 것만 차단).

## 이번 프로젝트 사례
- [ci-cd/issue5](../../../../../project/study-note-deploy-system/ci-cd/issue5/) — 엣지 봇 UA 차단(`~*curl/` → 444)이 GitHub Actions의 배포·색인 curl을 self-DoS. 4개 워크플로에 `--http1.1 -A "study-note-sync/1.0"`(배포는 `study-note-deploy/1.0`) 부여 → 전부 202로 복구.

## 검증 기록
- 2026-09-23: 이슈 README(ci-cd/issue5) + nginx conf 로컬 사본(`edge/nginx/conf.d/01-security.conf`의 `map $http_user_agent $bad_bot { ~*(…|curl/|…) 1 }`, `www.junproject.xyz.conf`의 `if ($bad_bot) return 444`) 대조 작성. 내부 IP·시크릿은 개념·링크로만. Claude 초안.
