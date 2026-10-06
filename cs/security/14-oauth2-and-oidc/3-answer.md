# security/14-oauth2-and-oidc — 정답

## 정답

### 1. 비밀번호를 건네는 문제

- 범위 제한이 없다: 앱이 사진뿐 아니라 계정의 모든 것을 할 수 있다.
- 따로 끊을 수 없다: 앱만 막으려면 비밀번호를 바꿔야 하고, 그러면 다른 곳도 다 끊긴다.
- 유출 면이 늘어난다: 앱 서버가 털리면 내 비밀번호가 샌다.
- OAuth 2.0: 사용자는 인가 서버에서만 로그인·동의하고, 앱은 비밀번호 대신 범위(scope)가 제한된 access token(필요하면 refresh token, OIDC면 ID 토큰도)을 받는다. 수명을 알려 주는 `expires_in`은 RECOMMENDED이고, 짧은 수명은 설계 선택이다(RFC 6749 §5.1). 토큰은 앱 단위로 폐기할 수 있다.
- RFC 9700 §2.4: resource owner password credentials 그랜트는 쓰면 안 된다(MUST NOT).

### 2. OAuth vs OIDC, 두 토큰

| | 답하는 질문 | 발급 대상(aud) | 검증하는 쪽 |
|---|---|---|---|
| OAuth 2.0 → access token | "이 앱이 이 사용자 대신 무엇을 해도 되나"(인가) | 자원 서버(API) — JWT면 `aud`로 제한 권장(RFC 9700 §2.3 SHOULD), 불투명 토큰일 수도 | 자원 서버 |
| OIDC → ID 토큰 | "이 사용자가 누구이고 이 발급자에서 인증했나"(인증, `auth_time`·`amr`은 있으면) | 클라이언트(`client_id`) | 클라이언트 |

### 3. 인가 코드 + PKCE 흐름

```text
  브라우저            클라이언트                                 인가 서버
  ①클릭 ──────>  state·nonce·code_verifier 생성, challenge = S256(verifier)
         <── 302 /authorize?...redirect_uri, state, code_challenge
  ② ─────────────────────────────────────────────────>  로그인·동의, redirect_uri 정확 일치 검사
         <── 302 redirect_uri?code=..&state=.. ─────────
  ③ ──/callback──> state == 세션 값? 
                  ④ POST /token(code, redirect_uri, code_verifier, 공개면 client_id) ──>  S256(verifier) == challenge?
                                                                       redirect_uri 같은가? code 1회·10분 이내?
                  <── access_token, id_token ───────────
                  ⑤ ID 토큰 검증 → 세션 발급
```

- `state`: 클라이언트가 ①에서 만들어 세션에 저장, ③에서 비교.
- `code_challenge`: ①에서 계산해 인가 요청에 실음, AS가 코드와 함께 저장.
- `code_verifier`: ①에서 만들어 클라이언트만 보관, ④에서 처음 보냄. AS가 해시해 challenge와 비교.
- `redirect_uri`: ②에서 등록값과 정확 일치 검사, ④에서 인가 요청 때 값과 같은지 다시 검사.

### 4. S256 계산

- `code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))` = `E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM`. 실험(OpenJDK 21.0.12)에서 RFC 7636 부록 B와 일치했다. verifier는 32바이트 난수를 base64url로 바꾼 43자다.
- `plain`은 challenge = verifier다. 인가 요청(브라우저 주소창·로그)을 볼 수 있는 공격자가 verifier를 그대로 얻는다. S256은 해시라 challenge에서 verifier를 되돌릴 수 없다. RFC 9700 §2.1.1은 verifier를 노출하지 않는 방법을 쓰라고 하고, 현재 그런 방법은 S256뿐이라고 적는다.

### 5. 접두 비교의 결과

- `https://app.example.attacker.test/cb`는 문자열 `https://app.example`로 시작한다. 검사를 통과하고, 인가 코드가 공격자 호스트로 간다. 실험에서 `302 → https://app.example.attacker.test/cb?code=...`.
- PKCE가 있으면: 공격자는 코드를 받았지만 `code_verifier`를 모른다. 토큰 교환이 `400 invalid_grant`로 실패한다(실험). 그래도 정확 일치 검사는 필요하다. PKCE가 없는 클라이언트, 토큰을 주소로 바로 주는 흐름, 열린 리다이렉터 같은 다른 경로가 남기 때문이다(RFC 9700 §2.1).

### 6. 다른 사람 계정으로 로그인됨

- 빠진 검사: 콜백의 `state`(또는 그에 준하는 PKCE·nonce 묶음). 공격자가 **자기 계정**으로 받은 코드를 담은 콜백 링크를 피해자에게 열게 하면, 피해자 브라우저가 공격자 계정으로 로그인된다(로그인 CSRF). 피해자가 등록한 카드는 공격자 계정에 쌓인다.
- 막는 법: 세션에 묶인 일회성 `state`를 만들고 콜백에서 같은 값인지 확인한다. 실험에서 없음·다른 값은 거부됐다. Spring `oauth2Login`은 인가 요청을 세션에 저장하고 `state`가 같을 때만 꺼낸다.

### 7. access token으로 로그인

- 문제: access token은 "어떤 클라이언트가 이 사용자 대신 API를 써도 된다"는 표시다. **우리 앱을 위해** 발급됐다는 증거가 아니다. 공격자가 자기 앱으로 같은 사용자에게서 정당하게 받은 토큰도 `/userinfo`를 부를 수 있어서, 우리 백엔드가 그 사용자로 로그인시킨다.
- 로그인 판단: `aud`에 우리 `client_id`가 있는 ID 토큰을 §3.1.3.7대로 검증한다. 가장 단순한 것은 백엔드가 직접 인가 코드 흐름을 돌려 토큰 엔드포인트에서 ID 토큰을 받는 것이다.

### 8. ID 토큰 검증 항목

- `iss`가 발급자 식별자와 정확히 일치(MUST).
- `aud`에 내 `client_id`, 믿지 않는 audience가 있으면 거부(MUST).
- 서명 검증(발급자 키 — 비대칭이면 JWKS, HS256 등 MAC이면 `client_secret`).
- 현재 시각 < `exp`(MUST).
- 요청에 `nonce`를 보냈으면 같은 값(MUST).
- (선택) `iat`가 너무 오래되지 않았나, `auth_time`·`acr` 확인.
- 서명 생략 규정: 클라이언트가 토큰 엔드포인트와 TLS로 **직접** 통신해 받은 ID 토큰은, TLS 서버 인증이 발급자를 확인해 주므로 서명 검증을 대신할 수 있다(MAY). 브라우저나 다른 시스템을 거쳐 온 ID 토큰(예: 프런트엔드가 백엔드에 넘긴 토큰, CI가 보낸 토큰)은 서명을 검증해야 한다(MUST).

### 9. 발급자 끝 슬래시

- 확인: discovery 문서의 `issuer` 값을 본다.

```bash
curl -s https://idp.example/.well-known/openid-configuration | jq -r .issuer
```

- 고침: 설정의 issuer를 그 값과 **문자 그대로** 맞춘다(끝 슬래시 포함).
- 느슨하게 바꾸면 안 되는 이유: OIDC Core는 `iss`의 정확한 일치를 요구한다. 접두·정규화 비교를 허용하면 같은 접두를 쓰는 다른 발급자(멀티 테넌트 IdP의 다른 테넌트 등)의 토큰을 받아들일 수 있다. 문자열 비교의 틈은 redirect_uri 접두 비교와 같은 종류의 구멍이다.
