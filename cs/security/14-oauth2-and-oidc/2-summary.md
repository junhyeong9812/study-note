# security/14-oauth2-and-oidc — 위임 인가, 인가 코드 + PKCE, ID 토큰 — 정리 (힌트)

## 해결하는 문제

사진 인쇄 앱이 내 클라우드 사진을 읽어야 한다. 가장 쉬운 방법은 앱에 클라우드 비밀번호를 주는 것이다.

```text
  비밀번호를 건네면
  - 앱이 사진뿐 아니라 메일·결제까지 전부 할 수 있다(범위 제한 없음)
  - 앱만 따로 끊을 수 없다(비밀번호를 바꾸면 모든 곳이 끊김)
  - 앱 서버가 털리면 내 비밀번호가 샌다
```

- *OAuth 2.0*(RFC 6749): 사용자가 비밀번호를 건네지 않고, 제3자 앱에 **범위가 제한된 접근 권한**을 위임하는 인가 프레임워크. 결과물은 *access token*이다.
- *OpenID Connect(OIDC)*: OAuth 2.0 위에 얹은 **인증** 계층. "이 사용자가 누구인가"를 *ID 토큰*(보통 JWS로 서명된 JWT)으로 알려 준다(OIDC Core 1.0 §1). 서명 생략(`alg=none`)은 인가 코드 흐름처럼 인가 엔드포인트가 ID 토큰을 주지 않고, 클라이언트가 등록 때 명시 요청한 경우에만 허용된다(§2).
  - 흔한 오해: "OAuth로 로그인한다" → OAuth 자체는 "무엇을 해도 되나"(인가)다. "누구인가"(인증)는 OIDC가 더한다.
- RFC 9700(OAuth 2.0 Security BCP, 2025-01) §2.4: 비밀번호를 앱에 직접 주는 *resource owner password credentials* 그랜트는 **쓰면 안 된다**(MUST NOT).

쉬운 예: 호텔 카드키다.
- 프런트(인가 서버)가 신분을 확인하고, 내 방과 헬스장만 열리는 카드(access token)를 발급한다.
- 객실 청소 업체에 마스터키(비밀번호)를 주지 않고, 그 방만 그날만 열리는 카드를 준다.
- 숙박부(ID 토큰)는 "이 손님이 누구인가"를 적은 별도 서류다. 카드키로 신원을 증명하지 않는다.

원본 [foundations/security/oidc.md](../../foundations/security/oidc.md)는 CI 파이프라인이 OIDC ID 토큰으로 자기 신원을 증명하는 경우(claim 검증 행렬, `sub` 문자열 함정, `jti` 재전송 방지)를 다룬다. 이 노트는 브라우저 사용자 로그인과 위임의 **흐름**을 다룬다.

## 동작·원리

### 1. 네 역할

```text
  자원 소유자(사용자) ── 동의 ──> 인가 서버(AS)  ── 토큰 발급 ──> 클라이언트(앱)
                                  예: 회사 IdP, 구글                │ access token
                                                                   ▼
                                                     자원 서버(RS, API) ── 토큰 검증 → 데이터
```

- RFC 6749 §1.1의 역할: resource owner, client, authorization server, resource server.
- *공개 클라이언트(public client)*: 비밀을 지킬 수 없는 클라이언트(SPA, 모바일 앱). *기밀 클라이언트(confidential client)*: 서버에 `client_secret` 등을 안전하게 둘 수 있는 클라이언트.

### 2. 인가 코드 + PKCE 흐름

```text
  브라우저                       클라이언트(서버)                         인가 서버(AS)
     │  ① "로그인" 클릭  ───────>   state, nonce, code_verifier 생성
     │                             code_challenge = BASE64URL(SHA256(code_verifier))
     │  <── 302 /authorize?response_type=code&client_id=..&redirect_uri=https://app.example/callback
     │          &scope=openid%20profile&state=..&nonce=..&code_challenge=..&code_challenge_method=S256
     │  ② ───────────────────────────────────────────────────────────>  로그인·동의
     │  <── 302 https://app.example/callback?code=SplxlOBeZQQYbYS6WxSbIA&state=.. ──────
     │  ③ ────── /callback ──────>  state == 세션의 state ?  (아니면 중단: 로그인 CSRF)
     │                             ④ POST /token  grant_type=authorization_code, code,
     │                                   redirect_uri, code_verifier,
     │                                   (기밀이면 클라이언트 인증 / 공개면 client_id) ──>
     │                                                                    SHA256(code_verifier) == 저장한 challenge ?
     │                                                                    redirect_uri == 인가 요청 때 값 ?
     │                                                                    code 미사용·10분 이내 ?
     │                             <── access_token, id_token, (refresh_token) ──────────────
     │                             ⑤ ID 토큰 검증(iss·aud·서명·exp·nonce) → 세션 발급(11번)
```

- 코드가 브라우저 주소창(②→③)을 지나므로 새기 쉽다. 그래서 코드만으로는 토큰을 받을 수 없게 묶는다.
  - **PKCE**(RFC 7636): 시작할 때 비밀 `code_verifier`를 만들고 그 해시만 보낸다. 토큰 교환 때 원본을 내야 한다. 코드를 가로챈 쪽은 원본을 모른다.
  - **코드 수명·일회성**(RFC 6749 §4.1.2): 수명은 짧게(최대 10분 권장), 두 번 쓰이면 거부해야 하고(MUST) 그 코드로 발급한 토큰을 폐기해야 한다(SHOULD).
  - **redirect_uri 정확 일치**(RFC 9700 §2.1): 등록한 URI와 문자열 그대로 비교해야 한다(MUST). 네이티브 앱의 localhost 포트만 예외다.
- *state*: 클라이언트가 만든 일회성 값. 콜백이 "내가 시작한 흐름"의 응답인지 확인한다(RFC 6749 §10.12). RFC 9700 §2.1: PKCE를 지원하는 AS면 PKCE의 CSRF 방어에 기댈 수 있고, OIDC에서는 `nonce`도 그 역할을 하며, 그 밖에는 state의 일회성 토큰이 필요하다(MUST).
- RFC 9700 §2.1.1: 공개 클라이언트는 PKCE를 **써야 하고**(MUST), 기밀 클라이언트에도 권한다(RECOMMENDED). 방법은 `S256`만 권한다(`plain`은 인가 요청에 verifier가 그대로 드러남). AS는 PKCE를 지원해야 한다(MUST).
- 암시적(implicit) 그랜트(토큰을 주소창으로 바로 받음)는 쓰지 않는 것이 권고다(SHOULD NOT, §2.1.2).

실험(OpenJDK 21.0.12 temurin, `--network none`, 2026-10-07) — PKCE 계산과, 한 JVM 안의 가상 인가 서버로 검증 규칙 비교:

```text
  code_verifier  = dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk (43자)
  code_challenge = E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
  RFC 일치?        true

  [redirect_uri] https://app.example.attacker.test/cb
    접두 비교: 302 → https://app.example.attacker.test/cb?code=code-0&state=…
    정확 일치: 400 invalid redirect_uri

  [가로챈 code 교환]
    PKCE 없음, 공격자(verifier 모름): 200 access_token 발급
    PKCE S256, 공격자(verifier 모름): 400 invalid_grant(code_verifier 불일치)
    같은 code 정상 클라이언트 재시도:    400 invalid_grant(없거나 이미 사용)  ← 공격 시도가 code를 소모
    PKCE S256, 정상 클라이언트:         200 access_token 발급
    같은 code 두 번째 교환:             400 invalid_grant(없거나 이미 사용)
  [state] 콜백 state=(세션 값과 같음) → 진행
  [state] 콜백 state=(없음) → 거부(로그인 CSRF 차단)
  [state] 콜백 state=attacker-chosen → 거부(로그인 CSRF 차단)
```

- 첫 세 줄은 RFC 7636 부록 B의 32바이트 예시에서 나온 verifier·challenge와 같다.
- 접두 비교(`startsWith("https://app.example")`)는 `app.example.attacker.test`라는 **다른 호스트**를 통과시켜 코드를 그쪽으로 보냈다.
- 이 가상 AS는 실패한 교환에서도 코드를 지우게 짰다. 실제 AS가 실패 시 코드를 소모하는지는 제품마다 다르다.

### 3. OIDC가 더하는 것 — ID 토큰

```text
  scope=openid  → 토큰 응답에 id_token(JWT) 추가
  id_token payload 예:
  { "iss": "https://idp.example", "sub": "248289761001", "aud": "my-client-id",
    "exp": 1311281970, "iat": 1311280970, "nonce": "n-0S6_WzA2Mj", "auth_time": 1311280969 }
```

- OIDC Core §3.1.3.7의 ID 토큰 검증(발췌)
  - `iss`가 discovery로 얻은 발급자 식별자와 **정확히** 같아야 한다(MUST).
  - `aud`에 내 `client_id`가 있어야 하고, 믿지 않는 audience가 섞여 있으면 거부해야 한다(MUST).
  - 서명 검증: 토큰 엔드포인트에서 TLS로 직접 받은 경우에는 TLS 서버 검증으로 발급자 확인을 대신할 수 있다(MAY). 그 밖의 경로로 받은 ID 토큰은 발급자 키로 서명을 검증해야 한다(MUST). 키는 비대칭 알고리즘(RS256 등)이면 13번의 JWKS, MAC 알고리즘(HS256 등)이면 그 `client_id`의 `client_secret`이다(§3.1.3.7).
  - 현재 시각이 `exp` 이전이어야 한다(MUST).
  - 요청에 `nonce`를 보냈으면 같은 값이 있어야 한다(MUST). ID 토큰 재전송을 막는다.
- *sub*: 발급자 안에서 사용자를 영구히 가리키는 ID. 사용자를 내 DB에 연결할 때는 `(iss, sub)` 쌍을 키로 쓴다. 이메일은 바뀌거나 재사용될 수 있다. 식별자 설계는 [16-identifiers-and-enumeration](../16-identifiers-and-enumeration/2-summary.md)과 원본 oidc.md §5.

### 4. access token과 ID 토큰은 받는 쪽이 다르다

```text
                  누구를 위해 발급?          무엇을 증명?                  누가 검증?
  access token    자원 서버(API)             "이 클라이언트가 이 범위를      자원 서버
                  (JWT면 aud = API 권장)      이 사용자 대신 써도 된다"
  ID token        클라이언트                  "이 사용자가 이 발급자에서       클라이언트
                  (aud = client_id)           인증했다"(+ 있으면 auth_time·amr)

  오용: 프런트엔드가 받은 access token을 백엔드 "로그인 API"에 내밀고,
        백엔드가 그 토큰으로 /userinfo를 불러 성공하면 로그인시킨다
     → 다른 앱(공격자 앱)이 같은 사용자에게서 정당하게 받은 access token도 통과한다
       (그 토큰은 우리 앱을 위해 발급된 것이 아니다)
```

- access token은 형식이 정해져 있지 않다(불투명 문자열일 수도). 클라이언트는 그것을 열어 보고 판단하지 않는다.
- 로그인 판단은 **내 client_id를 `aud`로 가진 ID 토큰**으로 한다. 원본 oidc.md [Claude 추가]의 "confused deputy" 설명과 같은 구조다.
- RFC 9700 §2.3: access token은 특정 자원 서버로 audience를 제한하고(SHOULD), 자원 서버는 자기 대상이 아닌 토큰을 거부해야 한다(MUST).
- ID 토큰에서 필수인 `iat`는 **토큰 발급 시각**이다. 실제 인증 시각 `auth_time`은 `max_age` 요청 등 특정 조건에서만 필수이고, 인증 방법 `amr`은 선택이다(OIDC Core §2).

## 쓰이는 자료구조·알고리즘

- **SHA-256 + base64url (PKCE S256)** — `code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))`. 일방향성이라 challenge에서 verifier를 못 되돌린다. [04-hash-functions-and-digests](../04-hash-functions-and-digests/2-summary.md)
- **CSPRNG** — `code_verifier`(43~128자, RFC 7636 §4.1, 32바이트 난수 → 43자), `state`, `nonce`. [09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md)
- **일회성 맵(code → 인가 정보, TTL)** — AS는 코드를 키로 `client_id`·`redirect_uri`·`code_challenge`를 저장하고, 교환 시 원자적으로 꺼내 지운다(get-and-delete).
- **정확 문자열 비교** — redirect_uri는 정규화·접두·와일드카드 없이 그대로 비교한다. URL 파서끼리 해석이 다른 틈(대소문자, 인코딩, `@`, 경로 `..`)을 없애는 가장 단순한 방법이다.
- **JWT 서명 검증 + JWKS 캐시** — ID 토큰 검증. [12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md), [13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 클라이언트 — Spring Security `oauth2Login`

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          corp:
            client-id: my-client-id
            client-secret: ${CORP_CLIENT_SECRET}         # 비밀은 환경·시크릿 저장소에서(09번)
            authorization-grant-type: authorization_code
            redirect-uri: "{baseUrl}/login/oauth2/code/{registrationId}"
            scope: openid, profile
        provider:
          corp:
            issuer-uri: https://idp.example              # discovery로 endpoints·jwks_uri를 얻는다
```

```java
@Bean
SecurityFilterChain web(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(a -> a.anyRequest().authenticated())
        .oauth2Login(Customizer.withDefaults());         // state·nonce 생성·검증, ID 토큰 검증
    return http.build();
}
```

- Spring Security 소스(main = 7.2.0-SNAPSHOT, 2026-10-07 조회)
  - `DefaultOAuth2AuthorizationRequestResolver`: OIDC면 `nonce`를 만들어 해시를 보낸다. 클라이언트 인증 방식이 `none`(공개 클라이언트)이거나 `ClientSettings.requireProofKey`가 참이면 PKCE를 붙인다.
  - `ClientSettings.Builder`의 `requireProofKey` 기본값은 `true`다(7.0.x 브랜치도 같다). 그랜트가 인가 코드가 아니면 `false`로 바뀐다.
  - 이전 판은 다르다(브랜치 소스 확인): `ClientSettings`가 처음 생긴 6.5.x에서는 기본값이 `false`였고, 6.4.x 이하에는 이 설정이 없다. 그 판들에서 기밀 클라이언트에 PKCE를 쓰려면 직접 켠다.
  - `HttpSessionOAuth2AuthorizationRequestRepository`: 인가 요청을 HTTP 세션에 저장하고, 콜백의 `state`와 같을 때만 꺼낸다. 그래서 콜백에 세션 쿠키가 실려야 한다(11번 장애 1).

### 2. 인가 서버(직접 만들거나 설정할 때) — 검증 규칙

취약 예:

```java
// 접두 비교, PKCE 선택, 코드 재사용 허용
boolean okRedirect(String uri) { return uri.startsWith(client.baseUrl()); }
Grant g = codes.get(code);                                       // 지우지 않는다
if (g.challenge() != null && verifier != null) checkPkce(...);  // verifier 없으면 그냥 통과
```

고친 예:

```java
boolean okRedirect(String uri) { return client.redirectUris().contains(uri); }   // 등록 목록과 정확 일치
Grant g = codes.remove(code);                                    // 원자적 꺼내기(분산이면 GETDEL 등)
if (g == null) { revokeTokensIssuedFrom(code); return invalidGrant(); }          // 재사용 → 발급 토큰 폐기(SHOULD)
if (g.expiresAt().isBefore(now)) return invalidGrant();
if (!g.redirectUri().equals(redirectUri)) return invalidGrant();
if (g.challenge() != null) {
    if (verifier == null || !MessageDigest.isEqual(s256(verifier), g.challenge())) return invalidGrant();
} else if (verifier != null) return invalidGrant();             // PKCE 다운그레이드 차단(RFC 9700 §2.1.1)
```

- 재사용 판정은 "삭제된 코드 목록"을 코드 수명 동안 따로 둬야 정확하다. 위 코드는 그 목록 조회를 `revokeTokensIssuedFrom`에 숨겼다.

### 3. 자원 서버(API) — access token 검증

- 12번의 리소스 서버 설정을 그대로 쓴다. 이 API의 식별자를 `aud`로 요구하고, `scope`로 인가한다.

```java
http.authorizeHttpRequests(a -> a
        .requestMatchers(HttpMethod.GET, "/photos/**").hasAuthority("SCOPE_photos.read")
        .anyRequest().authenticated())
    .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()));
```

- 실패 응답(RFC 6750 §3.1): 토큰 없음 → `401` + `WWW-Authenticate: Bearer`(오류 코드는 넣지 않는 것이 좋다, SHOULD NOT), 만료·위조 → `401` + `Bearer error="invalid_token"`, 범위 부족 → `403` + `error="insufficient_scope"`.

### 4. 진단 — 콜백 URL과 오류 응답을 읽는다

```text
  콜백에 ?error=...가 오면 AS가 거부한 것 (RFC 6749 §4.1.2.1)
    error=invalid_request        필수 파라미터 누락·중복, 잘못된 값
    error=unauthorized_client    이 클라이언트에 이 그랜트가 허용 안 됨
    error=access_denied          사용자가 거부
    error=invalid_scope
  토큰 엔드포인트 400 {"error":"invalid_grant"}  (RFC 6749 §5.2)
    → 코드 만료·재사용, redirect_uri 불일치, code_verifier 불일치
  redirect_uri가 없거나 틀리거나 client_id가 잘못되면, AS는 그 URI로 자동 리다이렉트하면 안 되고(MUST NOT)
  사용자에게 오류를 알린다(SHOULD, §4.1.2.1)
    → 콜백이 아예 오지 않고 브라우저에 AS의 오류 페이지가 보이면 redirect_uri·client_id 등록부터 확인
```

## 장애 시나리오와 대처

### 1. `redirect_uri` 느슨한 검증 → 코드 탈취

- **현상**: 보안 제보 — 공격자가 만든 링크로 로그인하면 인가 코드가 공격자 도메인으로 간다.
- **보이는 형태**: AS 로그에 등록 URI와 다른 `redirect_uri`(같은 접두의 다른 호스트, 등록 경로 아래의 열린 리다이렉터 경로)로 발급된 코드. 실험: 접두 비교가 `https://app.example.attacker.test/cb`를 통과.
- **원인**: 접두·와일드카드·정규화 후 비교. 또는 등록 도메인 안에 열린 리다이렉터가 있어, 정확 일치 URI에서도 코드가 다시 밖으로 나간다(RFC 9700 §2.1, §4.11).
- **대처**: 정확 문자열 일치, 열린 리다이렉터 제거, PKCE(코드를 가로채도 교환 불가 — 실험의 400 invalid_grant).

### 2. `state` 누락 → 로그인 CSRF

- **현상**: 사용자가 자기도 모르게 **공격자 계정**으로 로그인돼 있다. 그 상태에서 등록한 카드·주소가 공격자 계정에 쌓인다.
- **보이는 형태**: 콜백 요청에 `state`가 없거나, 세션에 저장한 값과 비교하지 않는다. 공격자 링크(`/callback?code=<공격자 계정의 코드>`)를 연 직후 로그인 상태가 바뀐 로그.
- **원인**: 콜백이 "내가 시작한 흐름"의 응답인지 확인하지 않는다.
- **대처**: 세션에 묶인 일회성 `state`를 검증한다(실험: 없음·다른 값 → 거부). PKCE·OIDC `nonce`도 같은 방어를 겸하지만(RFC 9700 §2.1), 라이브러리 기본 기능(Spring `oauth2Login`)을 끄지 않는 것이 가장 쉽다.

### 3. access token을 인증으로 오용 → 남의 앱 토큰으로 로그인

- **현상**: 모바일 앱 백엔드가 "소셜 로그인"을 받는데, 다른 앱(공격자 앱)에서 받은 같은 사용자의 토큰으로도 로그인된다.
- **보이는 형태**: 백엔드가 받은 토큰으로 `/userinfo`만 호출해 성공 여부로 로그인한다. 토큰의 `aud`·`client_id`를 보지 않는다.
- **원인**: access token은 "누가 누구를 위해 쓰도록 받은 것인지"를 우리 앱에 증명하지 않는다. 다른 클라이언트용 토큰도 `/userinfo`를 부를 수 있다.
- **대처**: 로그인 판단은 `aud = 우리 client_id`인 ID 토큰을 §3.1.3.7대로 검증해서 한다. 서버 쪽에서 인가 코드 흐름을 직접 돌리는 것이 가장 단순하다.

### 4. 발급자 문자열 불일치로 전원 로그인 실패

- **현상**: IdP 설정을 바꾼 뒤 모든 로그인이 콜백에서 실패한다.
- **보이는 형태**: 로그에 `iss` 불일치(예: 설정은 `https://idp.example`, 토큰은 `https://idp.example/`). Spring Security(main 소스)의 `OidcIdTokenValidator`는 토큰의 `iss`를 provider 메타데이터의 issuer와 비교하고, 다르면 오류 코드 `invalid_id_token`, 설명 `The ID Token contains invalid claims: {iss=…}`로 인증을 실패시킨다.
- **원인**: OIDC는 `iss`의 **정확한** 일치를 요구한다. 끝 슬래시·경로·대소문자 차이도 다른 발급자다.
- **대처**: discovery 문서의 `issuer` 값을 그대로 설정에 복사한다(`curl -s $ISSUER/.well-known/openid-configuration | jq -r .issuer`). 비교를 느슨하게 바꾸지 않는다.

### 5. SPA가 토큰을 브라우저에 쥐고 XSS로 털림

- **현상**: XSS 한 번으로 다수 사용자의 access·refresh 토큰이 외부로 나갔다.
- **보이는 형태**: SPA가 `localStorage`에 토큰을 저장. 공격 시간대에 토큰 사용 IP가 사용자와 다르다.
- **원인**: 공개 클라이언트(SPA)는 비밀을 지킬 수 없고, JS가 읽을 수 있는 곳의 토큰은 XSS가 읽는다.
- **대처**: BFF(백엔드가 토큰을 쥐고 브라우저에는 `HttpOnly` 세션 쿠키만) 패턴, 짧은 수명, refresh 회전. 자세히는 [17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md), [api-design/19-api-gateway-and-bff](../../api-design/19-api-gateway-and-bff/2-summary.md).

## 핵심 문장

- OAuth 2.0은 비밀번호 없이 범위가 제한된 접근을 위임하는 인가이고, OIDC는 그 위에 "누구인가"를 ID 토큰으로 더한 인증이다.
- 인가 코드는 브라우저를 지나므로 새기 쉽다. PKCE(S256)로 코드를 시작한 클라이언트에만 묶고, 코드는 짧게 한 번만 쓴다.
- redirect_uri는 등록값과 정확한 문자열로 비교한다. 접두 비교는 다른 호스트로 코드를 보낸다.
- `state`(또는 PKCE·nonce)로 콜백이 내가 시작한 흐름인지 확인한다. 없으면 로그인 CSRF가 된다.
- access token은 자원 서버가, ID 토큰은 클라이언트가 검증한다. 로그인 판단에 access token을 쓰지 않는다.
- ID 토큰은 iss 정확 일치, aud에 내 client_id, 서명(또는 TLS 직접 수신), exp, nonce를 모두 확인한다.

## 관련 주제·근거

- 선행
  - [12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md) — JWT 검증, access token 검증
  - [13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md) — discovery와 JWKS
  - 원본 [foundations/security/oidc.md](../../foundations/security/oidc.md) — §2 OAuth(인가) vs OIDC(인증), §3 JWT·claim, §4 claim 검증 행렬, §5 `sub` 합성 문자열의 함정, §6 `jti` 재전송 방지, §7 GitHub Actions의 실제 claim
- 후속·연결
  - [11-sessions-and-cookie-security](../11-sessions-and-cookie-security/2-summary.md) — 콜백의 SameSite 문제, 로그인 뒤 세션
  - [17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md) — refresh 토큰, BFF
  - [20-csrf-and-samesite](../20-csrf-and-samesite/2-summary.md) — CSRF 일반
  - [api-design/19-api-gateway-and-bff](../../api-design/19-api-gateway-and-bff/2-summary.md)
- 1차 출처
  - RFC 6749 OAuth 2.0 — §1.1 역할, §4.1 인가 코드(§4.1.2 코드 수명 최대 10분 권장·재사용 거부 MUST·토큰 폐기 SHOULD, §4.1.2.1 오류 코드), §5.2 `invalid_grant`, §10.12 CSRF와 state <https://www.rfc-editor.org/rfc/rfc6749>
  - RFC 7636 PKCE — §4.1 verifier 43~128자, §4.2 S256, 부록 B 예시 <https://www.rfc-editor.org/rfc/rfc7636>
  - RFC 9700 OAuth 2.0 Security BCP (BCP 240, 2025-01) — §2.1 redirect URI 정확 일치·CSRF, §2.1.1 PKCE(공개 MUST·기밀 RECOMMENDED, S256, 다운그레이드 방지), §2.1.2 implicit SHOULD NOT, §2.3 audience 제한, §2.4 ROPC MUST NOT <https://www.rfc-editor.org/rfc/rfc9700>
  - RFC 6750 Bearer Token Usage — §3.1 오류 코드 <https://www.rfc-editor.org/rfc/rfc6750>
  - OpenID Connect Core 1.0 — §3.1.3.7 ID 토큰 검증(iss 정확 일치, aud, TLS 직접 수신 시 서명 대신 가능, exp, nonce) <https://openid.net/specs/openid-connect-core-1_0.html>
  - OpenID Connect Discovery 1.0 <https://openid.net/specs/openid-connect-discovery-1_0.html>
  - Spring Security 소스(main = 7.2.0-SNAPSHOT, 2026-10-07 조회) — `DefaultOAuth2AuthorizationRequestResolver`(nonce·PKCE 적용 조건), `ClientRegistration.ClientSettings`(`requireProofKey` 기본 true, 6.5.x 브랜치는 false), `HttpSessionOAuth2AuthorizationRequestRepository`(state 대조), `OidcIdTokenValidator`(`invalid_id_token`)
- 실험(2026-10-07, eclipse-temurin:21-jdk = OpenJDK 21.0.12, `--network none`, 한 JVM 안 가상 AS)
  - RFC 7636 부록 B verifier·challenge 재현
  - redirect_uri 접두 비교 vs 정확 일치, 가로챈 코드 교환(PKCE 없음 200 vs S256 400), 코드 재사용 거부, state 대조
