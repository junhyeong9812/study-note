# security/20-csrf-and-samesite — 교차 사이트 요청 위조, 토큰·SameSite·Origin 검사 — 정리 (힌트)

## 해결하는 문제

브라우저는 요청을 보낼 때, 대상 사이트의 쿠키를 **누가 요청을 유발했는지와 무관하게** 자동으로 싣는다.
그래서 공격자 사이트가 피해자 브라우저로 은행 사이트에 요청을 보내게 만들면, 피해자의 세션 쿠키가 붙어 그 요청이 인증된 것처럼 처리된다.

```text
  피해자가 bank.example 로그인(세션 쿠키 보유) 상태로 evil.test 방문
  evil.test:  <form action="https://bank.example/transfer" method=POST>...
              <script>form.submit()</script>
  브라우저 → bank.example 로 POST (쿠키 자동 첨부) → 서버는 정상 이체로 처리
```

- *CSRF(Cross-Site Request Forgery, 크로스 사이트 요청 위조)*: 피해자 권한으로 상태 변경 요청을 **위조**해 보내는 공격. CWE-352.
  - 핵심: 공격자는 응답을 **읽지 못한다**(그건 CORS·SOP가 막는다 — 21번). 부수효과(이체·비밀번호 변경)만 노린다.
- 인젝션(18)·XSS(19)와 다른 점: 공격자가 코드를 주입하는 게 아니라, **정상 요청을 피해자가 모르게 유발**한다.
  - 흔한 오해: "CORS가 있으니 CSRF는 막힌다." CORS는 교차 출처 응답 읽기를 막을 뿐, 단순 요청이 서버에 닿는 것(부수효과)은 막지 않는다(21번 실험).

쉬운 예: 남의 서명이 든 백지 수표를 들고 있다가, 그 사람 모르게 금액을 적어 은행에 낸다.
- 은행은 서명(쿠키)만 보고 처리한다. "이 요청을 정말 본인이 지금 의도했나"를 따로 확인해야 한다.

### 무엇이 "교차 사이트"인가

```text
  site(사이트) = scheme + 등록 가능 도메인(eTLD+1).  https://bank.example 와 https://app.bank.example 는 같은 사이트.
                                             http://bank.example 와 https://bank.example 는 다른 사이트(scheme이 다름).
  origin(출처) = scheme + host + port.      127.0.0.1:3000 과 127.0.0.1:4000 은 다른 출처지만 같은 호스트.
```

- SameSite는 **사이트** 기준(21번 SOP/CORS는 **출처** 기준이다 — 다르다).
  - 사이트 정의는 WHATWG HTML §7.1.1.1(scheme 포함, "schemeful same site"). RFC 6265bis §5.2가 이 정의를 가져다 쓴다.

## 동작·원리

### 1. 토큰·쿠키·헤더 — 세 방어선

```text
  요청 ─▶ ① SameSite 쿠키 속성:   브라우저가 교차 사이트 요청에 세션 쿠키를 뺀다
         ② CSRF 토큰(동기화 토큰): 서버가 심은 비밀을 폼이 되돌려야 통과
         ③ Origin/Sec-Fetch-Site: 서버가 요청 출처를 헤더로 확인
```

- 셋은 계층이 다르다. ①은 브라우저가, ②③은 서버가 강제한다. 깊이 방어로 함께 쓴다.

### 2. SameSite — 브라우저가 쿠키를 뺀다

```text
  SameSite=Strict : 교차 사이트면 어떤 요청에도 쿠키 안 붙음(최상위 내비게이션 포함)
  SameSite=Lax    : 교차 사이트면 빠지되, "최상위 내비게이션 + 안전 메서드(GET 등)"는 예외로 붙음
  SameSite=None    : 항상 붙음(교차 사이트 포함) — Secure 필수
```

- Chrome 80 롤아웃부터 **SameSite 미지정 쿠키는 Lax로 취급**된다(Lax-by-default). 명시한 쿠키는 그 값대로다.
- `SameSite=None`은 `Secure`가 없으면 거부된다. `Secure`는 "secure 채널"에서만 보내라는 뜻이고, 무엇이 secure인지는 브라우저가 정한다(보통 HTTPS, RFC 6265bis §4.1.2.5). 단 Chrome은 `http://127.0.0.1`·`localhost`를 보안 문맥으로 보아, 아래 실험에서는 http로도 `Secure` 쿠키가 저장·전송되었다.
- 로컬 브라우저 실험(headless Chrome 151.0.7922.173, 2026-10-07): bank=`127.0.0.1:A`, 공격 페이지=`localhost:B`(호스트가 달라 다른 사이트). 저장된 쿠키:

```text
stored cookies: s_lax(Lax) s_strict(Strict) s_none(None,Secure) s_default(Lax)
```

- 교차 사이트 요청별로 어떤 쿠키가 붙었나:

```text
cross-site <img> GET          -> 쿠키: s_none            (Lax·Strict·default 모두 빠짐)
cross-site form POST          -> 쿠키: s_none, s_default  (POST는 Lax 예외 아님 → s_lax 빠짐. s_default는 Lax+POST 유예로 붙음 — 아래 참고)
cross-site top-level nav GET  -> 쿠키: s_lax, s_none, s_default  (최상위 GET = Lax 예외로 Lax 붙음)
```

- 읽는 법: `<img>`(하위 리소스 GET)에는 Lax·Strict가 모두 빠진다. 최상위 내비게이션 GET에는 Lax가 붙는다(Lax의 예외 조항).
  - 참고: 저장 목록의 `s_default(Lax)`는 Playwright가 빈 값을 `Lax`로 채워 보여 준 것이다. Chrome DevTools Protocol 원값으로는 `s_default`의 `sameSite`가 **없음**(미지정)이었다. Lax처럼 움직인 것(`<img>`에서 빠지고 최상위 GET에 붙음)은 Chrome이 요청 시점에 Lax-by-default를 적용했기 때문이다.
  - form POST 로그에 `s_default`가 보인 것은 Chrome의 "Lax+POST" 유예다. SameSite 미지정 쿠키가 발급 후 **2분 이내**면 최상위 교차 사이트 POST에 붙는다. SSO 콜백 호환용 임시 완화책이고(Chromium FAQ: 향후 제거 예정), 명시적 Lax에는 적용되지 않는다.
  - 2분 경계 재실험(같은 Chrome 151, 점검 재실행): 발급 직후 교차 사이트 POST → `s_none,s_default`, 약 126초 뒤 같은 POST → `s_none`만. 그 뒤 최상위 GET에는 `s_lax,s_none,s_default`가 그대로 붙었다.

### 3. 동기화 토큰(synchronizer token) — 서버가 심은 비밀

```text
  GET /form   → 서버: 세션에 토큰 저장 + 폼 hidden 필드에 같은 토큰
  POST /action with csrf=<토큰>  → 서버: 세션의 토큰과 비교 → 일치해야 수행
```

- 공격자 사이트는 그 토큰을 **읽을 수 없다**(응답을 못 읽으니까 — SOP). 그래서 위조 폼에 올바른 토큰을 담지 못한다.
- OWASP CSRF Cheat Sheet: 토큰은 세션당 유일·비밀·예측 불가. 동기화 토큰 패턴에서는 **쿠키로 전송하지 않고, GET URL에 넣지 않는다**(URL은 히스토리·로그·Referer로 샌다).
- 로컬 실험: 세션을 `SameSite=None` 쿠키로 받는(쿠키 방어가 없는 최악 가정) 보호 엔드포인트에 토큰+Origin 검사를 걸었다.

```text
same-site: legit form with token  token=ok   originOk=true   -> 200
cross-site form POST (no token)               -> 200  (방어 없는 /transfer: 뚫림)
cross-site form POST to token-protected  token=missing/bad originOk=false -> 403
```

- 토큰·Origin 검사가 있는 엔드포인트만 교차 사이트 POST를 `403`으로 막았다. 방어 없는 `/transfer`는 `SameSite=None` 쿠키가 붙어 `200`으로 처리되었다 — 쿠키 방어가 없으면 토큰/Origin이 필수임을 보인다.

### 4. Origin / Sec-Fetch-Site — 서버가 출처를 본다

```text
  Origin: https://evil.test          서버: 내 출처와 다르면 거부
  Sec-Fetch-Site: cross-site         서버: cross-site면 상태 변경 거부
```

- 실험 로그에 교차 사이트 요청은 `sec-fetch-site=cross-site`, 폼 POST엔 `origin=http://localhost:B`가 찍혔다. 같은 사이트 요청은 `sec-fetch-site=same-origin`.
- Origin 검사 주의(OWASP): `example.org.attacker.com`이 통과하지 않도록 정확히 비교한다(접두 일치 금지).
- `Sec-Fetch-*`는 브라우저가 붙이는 Fetch Metadata. 구형 브라우저엔 없으므로 Origin 검사를 폴백으로 둔다.

### 5. 상태 변경은 GET으로 하지 않는다

- GET은 Lax 쿠키가 최상위 내비게이션에서 붙고, `<img>`·`<a>`로 쉽게 유발된다. 상태 변경 GET은 CSRF의 단골이다.
- HTTP 의미상 GET은 안전(safe)·멱등이어야 한다([network/33-http-semantics](../../network/33-http-semantics/2-summary.md)). 이체·삭제는 POST/PUT/DELETE로.

## 쓰이는 자료구조·알고리즘

- **동기화 토큰 = 세션에 매인 CSPRNG 비밀**: 요청 위조자가 못 맞히도록 예측 불가해야 한다([09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md)). 서버는 세션 저장소에 토큰을 두고 상수 시간 비교(`MessageDigest.isEqual` 류)로 맞춘다 — 타이밍 노출을 피한다([05-mac-and-hmac](../05-mac-and-hmac/2-summary.md)).
- **서명된 double-submit 쿠키 = HMAC**: 무상태 서버에서 토큰을 세션 ID에 HMAC으로 묶는다(05번 HMAC). 순진한 double-submit의 쿠키 주입 문제를 막는다.
- **사이트 판정 = scheme 비교 + 등록 가능 도메인(eTLD+1) 파싱**: Public Suffix List로 등록 가능 도메인을 구해 "같은 사이트"를 정한다. 21번의 출처 튜플 비교와 대비된다.

## 적용 — 풀어나가는 법

### 1. Spring Security — 기본이 켜져 있다

```java
@Bean
SecurityFilterChain chain(HttpSecurity http) throws Exception {
    http.csrf(Customizer.withDefaults());  // 기본 ON. POST·PUT·DELETE·PATCH 보호, GET·HEAD·TRACE·OPTIONS 제외
    return http.build();
}
```

- 기본 보호 제외 메서드는 `CsrfFilter`의 기본 매처가 정한다(`GET`·`HEAD`·`TRACE`·`OPTIONS`). 기본 토큰 저장소 `HttpSessionCsrfTokenRepository`(세션), 기본 핸들러 `XorCsrfTokenRequestAttributeHandler`(요청마다 난수 XOR → BREACH 완화).
- 기본 헤더 `X-CSRF-TOKEN`, 파라미터 `_csrf`. 검증 실패 시 `AccessDeniedException` → `403`.
- SPA·쿠키 방식이 필요하면 `CookieCsrfTokenRepository.withHttpOnlyFalse()`(JS가 읽어 헤더로 재전송). Spring Security 7.0에 추가된 `.csrf(csrf -> csrf.spa())`가 SPA 구성을 묶어 준다(6.x에는 없다 — 쿠키 저장소·요청 핸들러를 직접 구성).

### 2. REST API에서 CSRF를 끄는 조건

- 세션 쿠키를 **쓰지 않고** `Authorization: Bearer` 헤더로만 인증하면 CSRF 위험이 없다(브라우저가 `Authorization`을 자동으로 붙이지 않는다). 이때만 CSRF 비활성화가 정당하다.
- 쿠키 세션을 쓰면서 CSRF를 끄면 뚫린다. "stateless"라는 말만 믿고 끄지 않는다.

### 3. 쿠키 속성 — 깊이 방어의 기본선

```text
Set-Cookie: SESSION=...; Path=/; HttpOnly; Secure; SameSite=Lax
```

- 대부분의 폼 기반 앱은 `SameSite=Lax`로 충분하다. 교차 사이트 콜백(결제·SSO)이 POST로 돌아오면 그 쿠키만 `None; Secure` + 토큰 방어.
- SameSite만으로는 부족한 경우: 같은 사이트 하위 도메인이 뚫리면 "same-site"로 취급돼 통한다(OWASP). 그래서 토큰을 함께 둔다.

### 4. Origin/Fetch Metadata 방어(토큰 보완)

```java
String site = req.getHeader("Sec-Fetch-Site");
if (site != null && !site.equals("same-origin") && !site.equals("same-site") && !site.equals("none"))
    throw new ResponseStatusException(HttpStatus.FORBIDDEN);  // cross-site 상태 변경 거부
// 폴백: Origin 헤더를 내 출처와 정확히 비교
```

### 5. 로그인 CSRF

- 공격자가 자기 계정으로 피해자를 로그인시켜, 피해자가 입력한 정보가 공격자 계정에 쌓이게 한다.
- 대처(OWASP): 로그인 폼에도 사전 세션 토큰, 로그인 성공 시 세션 재발급(세션 고정도 함께 막음 — security 11).

## 장애 시나리오와 대처

### 1. 이미지 태그 한 줄로 이체가 된다

- **현상**: 공격 페이지를 연 로그인 사용자의 계정에서 이체가 일어난다.
- **보이는 형태**: 서버 로그에 교차 사이트에서 온 상태 변경 요청, `Referer`/`Origin`이 외부.
- **원인**: 상태 변경을 GET으로 처리 + SameSite 미설정(또는 토큰 없음). `<img src=".../transfer?to=...">`로 유발.
- **대처**: 상태 변경은 비안전 메서드로, CSRF 토큰, `SameSite=Lax` 이상. 실험에서 토큰 보호 엔드포인트는 `403`.

### 2. CSRF 토큰을 빼먹었는데 성공한다

- **현상**: 토큰 없는 요청이 `403`이 아니라 `200`으로 처리된다.
- **보이는 형태**: 그 엔드포인트가 CSRF 보호 밖(예: `csrf.ignoringRequestMatchers(...)`로 제외한 경로, 또는 `GET` 매핑으로 상태 변경).
  - 흔한 오해: "`permitAll` 경로라 CSRF가 빠졌다." `permitAll`은 인가 규칙일 뿐이다. Spring Security에서 `CsrfFilter`는 인가(`AuthorizationFilter`, 기본으로 마지막)보다 앞에서 돌아 `permitAll` POST도 토큰 검사를 받는다.
- **원인**: 방어가 그 경로에 적용되지 않았다. 실험의 방어 없는 `/transfer`가 이 경우다(`200`).
- **대처**: 상태 변경 경로를 전수 점검, GET 상태 변경 제거, CSRF 설정 범위 확인.

### 3. SSO 콜백이 SameSite 강화 후 깨진다

- **현상**: IdP에서 돌아오는 POST 콜백에서 세션이 없어 로그인 루프.
- **보이는 형태**: 콜백 요청에 세션 쿠키 미첨부, 서버는 "세션 없음".
- **원인**: 세션 쿠키가 `SameSite=Lax`/`Strict`라 교차 사이트 POST 콜백에 빠졌다. "Lax+POST" 2분 유예도 명시적 Lax엔 적용 안 된다.
- **대처**: 콜백에 관여하는 쿠키만 `SameSite=None; Secure`로 둔다. 이 콜백은 IdP 출처에서 오는 정상 교차 사이트 POST(OIDC `form_post`)라 "내 출처가 아니면 거부" 검사에서 따로 다룬다(IdP 출처 허용 목록). 대신 요청 때 만든 OAuth `state`를 콜백에서 대조해 위조를 막는다(RFC 6749 §10.12). 또는 콜백을 최상위 GET 리다이렉트로 설계.

### 4. ⚠ XSS가 있으면 CSRF 방어가 다 무너진다

- **현상**: CSRF 토큰·SameSite를 다 걸었는데 공격이 통한다.
- **원인**: 대상 출처에 XSS가 있으면 공격 스크립트가 토큰을 읽어 정상 요청을 만든다(같은 사이트의 다른 출처라면 토큰을 바로 읽지는 못하지만, 그 요청은 same-site라 SameSite 방어는 통과한다). OWASP: "XSS는 모든 CSRF 완화를 무력화한다."
- **대처**: XSS를 먼저 막는다(19번). CSRF 방어는 XSS가 없다는 전제 위에 선다.

### 5. ⚠ Origin을 접두 일치로 검사한다

- **현상**: `bank.example.attacker.com`에서 온 요청이 통과한다.
- **원인**: `origin.startsWith("https://bank.example")` 같은 느슨한 비교.
- **대처**: 출처를 정확히(완전 일치) 비교한다. 허용 목록 집합 조회.

## 핵심 문장

- CSRF는 피해자의 쿠키가 자동 첨부되는 성질을 이용해 상태 변경 요청을 위조한다. 공격자는 응답을 읽지 못하고 부수효과만 노린다.
- CORS는 CSRF를 막지 못한다. 단순 요청은 CORS 검사 전에 서버에 닿는다.
- SameSite는 사이트 기준으로 브라우저가 쿠키를 뺀다. Lax는 최상위 내비게이션 GET만 예외로 쿠키를 붙인다. None은 Secure 필수.
- 동기화 토큰은 공격자가 읽을 수 없는 세션 비밀이다. 쿠키·GET URL에 넣지 않는다.
- 상태 변경은 GET으로 하지 않는다. GET은 Lax 쿠키가 붙고 `<img>`·`<a>`로 유발된다.
- SameSite·토큰·Origin은 계층이 다른 깊이 방어다. 그리고 XSS가 있으면 이 모두가 무력화된다.

## 관련 주제·근거

- 선행
  - [11-sessions-and-cookie-security](../11-sessions-and-cookie-security/2-summary.md) — 세션·쿠키 속성·세션 고정
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — GET의 안전·멱등 의미
- 후속·연결
  - [21-same-origin-and-cors](../21-same-origin-and-cors/2-summary.md) — 왜 공격자가 응답을 못 읽나(SOP/CORS)
  - [19-xss-and-csp](../19-xss-and-csp/2-summary.md) — XSS는 CSRF 방어를 무력화
  - [05-mac-and-hmac](../05-mac-and-hmac/2-summary.md) — 서명된 double-submit 토큰
  - [web-api/29-credentials-and-cookies](../../../languages/web-api/29-credentials-and-cookies/2-summary.md) · [web-platform/05-fetch-from-browser](../../web-platform/05-fetch-from-browser/2-summary.md) — credentials와 쿠키 첨부
- 1차 출처
  - OWASP CSRF Prevention Cheat Sheet — 동기화 토큰, Fetch Metadata, Origin 검증, SameSite 심층 방어, "XSS defeats CSRF", 서명 double-submit, GET 금지, 로그인 CSRF <https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html>
  - RFC 6265bis(초안) SameSite — Strict/Lax/None, Lax-by-default <https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis>
  - Chromium SameSite FAQ — Chrome 80 롤아웃 Lax-by-default, Lax+POST("at most 2 minutes old", 임시 완화책), None;Secure <https://www.chromium.org/updates/same-site/faq/>
  - WHATWG HTML §7.1.1.1 Sites(scheme 포함) <https://html.spec.whatwg.org/multipage/browsers.html#sites> · RFC 6749 §10.12 CSRF(`state`) <https://www.rfc-editor.org/rfc/rfc6749#section-10.12> · Spring Security CSRF·"AuthorizationFilter Is Last By Default" <https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html> <https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html>
  - W3C Fetch Metadata Request Headers — `Sec-Fetch-Site` 정의 <https://w3c.github.io/webappsec-fetch-metadata/> (WHATWG Fetch는 요청에 이 헤더를 붙이는 단계만 참조)
  - Spring Security Reference(7.0.x) — CSRF 기본 ON, HttpSessionCsrfTokenRepository·CookieCsrfTokenRepository, XorCsrfTokenRequestAttributeHandler, `spa()`, AccessDeniedException <https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html> · 보호 제외 메서드: `CsrfFilter.DefaultRequiresCsrfMatcher`(GET·HEAD·TRACE·OPTIONS), `CsrfConfigurer.spa()` `@since 7.0`(spring-security main 소스)
  - CWE-352 <https://cwe.mitre.org/data/definitions/352.html>
- 실험 목록(2026-10-07, 로컬 127.0.0.1/localhost + headless Chrome만, 가짜 세션)
  - A. SameSite 쿠키 첨부 — bank=`127.0.0.1:A`, 공격=`localhost:B`, Chrome 151: `<img>` GET / 폼 POST / 최상위 내비 GET별 Strict·Lax·None·미지정 쿠키 첨부 여부, 서버의 `sec-fetch-site`·`origin` 로그. 점검 재실행에서 CDP 원값(미지정 = `sameSite` 없음)과 Lax+POST 2분 경계(0초 붙음·126초 빠짐) 추가 확인
  - B. 토큰+Origin 보호 vs 무방어 엔드포인트 — 같은 사이트 정상 폼(200) / 교차 사이트 무토큰 POST(방어 없음 200·토큰 보호 403)
  - 코드: `scratchpad/sec/18/web/exp20-csrf.js`
