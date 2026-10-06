# security/14-oauth2-and-oidc — 질문

## 질문

1. (왜) 사진 인쇄 앱에 클라우드 비밀번호를 주는 방식의 문제 세 가지는? OAuth 2.0은 그것을 어떻게 바꾸나? RFC 9700은 비밀번호를 앱에 주는 그랜트를 어떻게 규정하나?
2. (경계) OAuth 2.0과 OIDC가 각각 답하는 질문은? access token과 ID 토큰은 각각 누구를 위해 발급되고 누가 검증하나?
3. (그림) 인가 코드 + PKCE 흐름을 브라우저·클라이언트·인가 서버 세 줄로 그려라. `state`, `code_challenge`, `code_verifier`, `redirect_uri`는 각각 어느 단계에서 만들어지고 어디서 검사되나?
4. (계산) RFC 7636 부록 B의 `code_verifier`가 `dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk`일 때 `code_challenge`는 어떻게 계산하나? 왜 `plain`이 아니라 `S256`을 쓰나?
5. (예측) 인가 서버가 `redirect_uri`를 `startsWith("https://app.example")`로 검사한다. `https://app.example.attacker.test/cb`로 요청하면 어떻게 되나? PKCE를 쓰고 있으면 피해가 어떻게 달라지나?
6. (장애 진단) 사용자가 자기도 모르게 다른 사람 계정으로 로그인돼 있었고, 그 상태에서 카드 정보를 등록했다. 어떤 검사가 빠졌을 가능성이 크고, 어떻게 막나?
7. (장애 진단) 모바일 앱 백엔드가 클라이언트가 보낸 access token으로 `/userinfo`를 불러 성공하면 로그인시킨다. 무엇이 문제이고, 로그인 판단은 무엇으로 해야 하나?
8. (적용) ID 토큰 검증에서 OIDC Core §3.1.3.7이 요구하는 항목을 대라. 토큰 엔드포인트에서 직접 받은 ID 토큰은 서명 검증을 생략할 수 있다는 규정은 왜 있고, 어떤 경우엔 생략할 수 없나?
9. (장애 진단) IdP 설정 변경 뒤 모든 로그인이 콜백에서 실패하고, 로그에 발급자 불일치가 보인다. 설정은 `https://idp.example`, 토큰은 `https://idp.example/`이다. 어떻게 확인하고 고치나? 비교를 느슨하게 바꾸면 안 되는 이유는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
