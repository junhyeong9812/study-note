# security/29-security-symptom-index — 정답

## 정답

### 1. 두 갈래로 나누는 이유

- 정상 요청이 막히는 증상(401·403 폭증, CORS 에러, TLS alert)은 사용자가 바로 신고한다. 막혀야 할 요청이 통과하는 증상(장애 중 `200`, 남의 데이터 `200`, 위조 토큰 `200`)은 에러가 없어 로그·감사·외부 제보로만 보인다.
- 탐지 방법이 다르다. 앞 갈래는 에러율로 보이고, 뒤 갈래는 "거부 수가 0으로 떨어진 구간"이나 "검증 실패 지표가 없는 경로"를 찾아야 보인다.
- 앞 갈래를 급히 처방해 뒤 갈래가 생기는 예
  - CORS 에러를 요청 `Origin` 반사 + `Access-Control-Allow-Credentials: true`로 없앰 → 쿠키가 실리는 다른 출처가 인증된 응답을 읽는다(`SameSite=None` 쿠키면 아무 사이트나. 장애 시나리오 2, 21 장애 4).
  - POST `403`을 `csrf.disable()`로 없앰 → 쿠키 세션에서 교차 사이트 상태 변경이 통과한다(장애 시나리오 3).
  - 인가 서버 장애 때 "서비스가 멈추면 안 된다"며 예외를 허가로 처리 → 장애 동안 권한 없는 요청이 `200`(01 장애 1).
  - 인증서 오류를 "전부 신뢰" `TrustManager`로 없앰 → 중간자에게 열린다(07 장애 4).

### 2. 401·403·404와 `WWW-Authenticate`

- `401`(RFC 9110 §15.5.2): 유효한 인증 자격 증명이 없다. 서버는 `WWW-Authenticate`를 반드시(MUST) 보낸다. 새 자격 증명으로 다시 시도할 수 있다.
- `403`(§15.5.4): 이해했지만 거부한다. 자격 증명이 있었다면 그것으로는 부족하다. 같은 자격 증명으로 자동 재시도하지 않는다(SHOULD NOT).
- `404`(§15.5.5): 못 찾았거나, 있는지 밝히고 싶지 않다. §15.5.4는 금지 대상의 존재를 숨기려면 `403` 대신 `404`를 줄 수 있다(MAY)고 한다.
- RFC 6750 §3.1(Bearer)
  - 토큰이 무효(만료·폐기·형식 오류 등) → `401` + `error="invalid_token"`(SHOULD).
  - scope 부족 → `403` + `error="insufficient_scope"`(SHOULD).
  - 인증 정보가 아예 없음 → 오류 코드를 넣지 않는다(SHOULD NOT). 예: `WWW-Authenticate: Bearer realm="example"`.
- 그래서 토큰 없음과 무효 토큰은 같은 `401`이지만 헤더의 `error` 유무로 갈린다(서버가 SHOULD를 따를 때. `error`가 없다는 것만으로 토큰 미전송을 확정하지는 못한다).

### 3. 실험의 `401` 네 줄과 `403` 세 줄

- `401` 네 줄
  - (1) 토큰 없음: `WWW-Authenticate: Bearer realm="api"` — `error` 없음.
  - (2) 서명 키가 다름: `error="invalid_token", error_description="invalid signature"`.
  - (3) 모르는 kid: `error_description="kid not found"`.
  - (4) 만료: `error_description="token expired"`.
- `403` 세 줄
  - (5) scope 부족: `WWW-Authenticate: Bearer error="insufficient_scope", scope="orders.read"`.
  - (8) 쿠키 POST·CSRF 토큰 없음: `WWW-Authenticate` 없음, 본문 `csrf token missing` — 인증 전에 CSRF 필터가 거부.
  - (9) 일반 사용자 `/admin`: `WWW-Authenticate` 없음, 본문 `forbidden` — 인가 규칙.
- 응답 코드만 세면 (2)·(3)·(4)가 한 덩어리가 된다. 키 회전(3절)·서명 키 불일치(2절)·시계 어긋남을 가를 수 없다. CSRF와 인가 거부도 섞인다. 서버 쪽 사유별 카운터(적용 2)가 필요하다.
- 문구는 예제가 고른 것이다. 실제 라이브러리는 다르다(예: Nimbus 9.40 `Signed JWT rejected: Invalid signature`).

### 4. `invalid signature`의 세 자리

- 웹훅 수신(HMAC): 일부 이벤트(비ASCII·소수점·특정 필드)만 `401`이면 원문 대신 재직렬화한 바이트로 검증한 것이다. 받은 원문 바이트로 다시 계산해 맞는지 본다(05 장애 2). 특정 시각부터 100%면 비밀 회전 시점 어긋남이다(05 장애 3).
- JWT 검증: 다른 발급자·다른 환경의 토큰이거나 옛 키로 서명된 토큰이다. 토큰 헤더의 `kid`·`alg`와 페이로드의 `iss`를 디코드해(서명 검증 없이 읽기만) 확인한다(12·13).
- 키 교체 배포 직후: 키 버전이 없어 "새 키로 쓰기 + 옛 키로 읽기"를 못 한다. `AEADBadTagException`·서명 `401`이 함께 늘어난다. 데이터·토큰에 키 버전 필드가 있는지 본다(09 장애 2, 03 장애 4).
- 덧붙여: 서명이 틀렸는데 **통과**하는 쪽이 더 위험하고 조용하다(9절).

### 5. `kid not found`를 가르기

- 회전 직후 캐시 미스: 실패 토큰의 `kid`가 발급자 JWKS에 이미 있다. 저절로 회복하고, 회복 시각 = 회전 전 마지막 페치 + 캐시 TTL이다(늦어도 회전 + TTL. 13 실험 A: t=0 페치, t=100 회전, 재페치 없으면 첫 200이 t=600).
- JWKS 엔드포인트 장애: JWKS 페치가 타임아웃·503이다. 401 시작 시각 = 마지막 성공 페치 + TTL이다(13 실험 C). 발급자 장애 시작 시각이 아니다.
- 무작위 `kid` 폭격: 매 요청 다른 `kid`이고, JWKS 페치 수 ≈ 실패 수다(13 실험 B: 쿨다운 0초면 1,000건 → 1,000회, 30초면 1회).
- Spring Security 6.5.5 소스 기준: JWKS 페치 실패(`RemoteKeySourceException`)는 `NimbusJwtDecoder`에서 `BadJwtException`이 아닌 `JwtException`이 되고, `JwtAuthenticationProvider`가 `AuthenticationServiceException`으로 바꾼다. 기본 실패 처리기가 이를 401로 바꾸지 않고 다시 던진다. 오류 페이지 장치가 처리하지 않은 예외에 서블릿 컨테이너는 `500`을 보내야 하므로(Jakarta Servlet 명세) `500`으로 보일 수 있다. 앱의 별도 오류 처리가 있으면 달라진다(소스·명세 확인, 실행 확인은 안 함).

### 6. CORS 에러와 서버 `200`

- 처리됐다. 단순 요청(`GET`·`HEAD`·`POST` + 안전 헤더)은 서버에 닿아 처리되고, 응답에 `Access-Control-Allow-Origin`이 없어서 브라우저가 스크립트에 응답을 넘기지 않았을 뿐이다. 콘솔 원문은 `No 'Access-Control-Allow-Origin' header is present`, 스크립트가 받는 것은 `TypeError: Failed to fetch`다(21 장애 1). 상태 변경이었다면 중복 처리를 확인한다.
- preflight 405는 다르다. 브라우저가 먼저 보낸 `OPTIONS`가 2xx가 아니어서 **본 요청이 아예 안 나간다**. 콘솔은 `Response to preflight request doesn't pass access control check: It does not have HTTP ok status`(21 장애 2).
- Origin 반사 + credentials는 에러를 없애는 대신 쿠키가 실리는 출처는 어디든 인증된 응답을 읽게 만든다(`SameSite=None` 쿠키면 아무 사이트나. 21 장애 4). 허용 출처 집합과 완전 일치로 비교해야 한다.

### 7. 로그인한 사용자의 POST만 `403`

- 첫 후보는 CSRF 토큰 누락이다. Spring Security에서 `CsrfFilter`는 인가보다 앞에서 돌아, 인증된 사용자도 토큰이 없으면 `403`이다(실험 (8): `WWW-Authenticate` 없음, `csrf token missing`). GET은 기본 보호 대상이 아니라서 통과한다.
- 확인: 요청에 토큰(Spring 기본 헤더 `X-CSRF-TOKEN`, 파라미터 `_csrf`)이 실렸나. SPA면 쿠키로 받은 토큰을 헤더로 다시 보내는 구성이 있나.
- CSRF를 꺼도 되는 조건: 세션 쿠키·HTTP Basic처럼 브라우저가 자동으로 싣는 자격 증명을 쓰지 않고, 스크립트가 붙이는 `Authorization: Bearer`로만 인증할 때다. 브라우저가 Bearer 토큰은 자동으로 붙이지 않기 때문이다(HTTP Basic은 기억했다가 자동으로 붙인다). 쿠키 세션에서 끄면 뚫린다(20 적용 2, 장애 시나리오 3).

### 8. `169.254.169.254` 요청

- 원인 후보와 확인
  - 사용자 URL을 가져오는 기능(SSRF) + 토큰 없는 메타데이터(IMDSv1): 그 요청의 입력 URL, 인스턴스의 IMDSv2 필수 여부(22 장애 1).
  - 허용 목록을 문자열 포함·접두 일치로 검사: 파싱한 호스트 전체가 허용 집합에 있나(22 장애 2).
  - 리다이렉트 자동 추적·DNS rebinding·다른 주소 표기: HTTP 클라이언트의 리다이렉트 기본값, 이름 해석 기록, 정규화 후 대역 판정 여부(22 장애 3~5).
  - XXE로 서버가 내부 요청: 요청 본문의 `<!DOCTYPE … SYSTEM`(23 장애 3).
- 먼저 할 일: 그 인스턴스 역할의 자격 증명이 나갔다고 보고 회전한다. CloudTrail에서 그 역할의 평소와 다른 호출을 찾는다(09 적용 4).
- 실제 사례: Capital One 2019(30 사건 3). 공소장은 "방화벽 설정 오류로 명령이 서버에 닿았고, 첫 명령이 `*****-WAF-Role` 자격 증명을 얻었다"고 적는다. 이를 SSRF로 부른 것은 상원의원 서한 등 이후 문서다.

### 9. 로그인 폭주 가르기

- 크리덴셜 스터핑: 로그인 `401` 비율 급등, 실패가 수천 IP에 흩어져 IP당 몇 건, 다양한 계정에 적은 시도, 소수 성공(10 장애 1).
- 계정 열거: 없는 계정과 있는 계정의 응답 코드·문구·시간이 다르다(10 실험: 취약 판 없는 계정 0.0 ms vs 있는 계정 약 90 ms)(10 장애 3).
- KDF 과부하: 로그인 API만 느리고 CPU 포화, 메모리 큰 Argon2면 `OOMKilled`. 공격이 아니어도 피크 시간 정상 로그인으로 생길 수 있다(08 장애 3).
- IP당 한도가 부족한 이유: 스터핑은 IP를 분산해 IP당 몇 건만 보낸다. 한도에 걸리는 IP가 거의 없다. 계정 단위 제한 + 전역 실패율 + 봇 탐지 + MFA를 겹친다(장애 시나리오 4).

### 10. "에러율 변화 없음"을 다시 보기

- 거부 수(`403`)와 검증 실패 수가 장애 구간에 0으로 떨어졌는지 본다. 판정 불가를 허가로 처리했다면 에러율은 그대로이고 거부만 사라진다.
- 실험 (10): 취약 판(PDP 예외 = 허가)은 PDP 장애 중 일반 사용자의 `/admin`에 `200 admin page`. 고친 판은 같은 상황에서 `503 authz unavailable`. 장애가 없을 때는 두 판 모두 `403`((9))이라, 평소 테스트로는 차이가 안 보인다.
- 대처: 거부·검증 실패 지표에 "0으로 떨어짐" 알람, 판정 불가는 거부(01 장애 1, 15 장애 3), 장애 주입 테스트.
