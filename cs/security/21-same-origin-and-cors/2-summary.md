# security/21-same-origin-and-cors — 출처 모델·SOP·CORS·preflight — 정리 (힌트)

## 해결하는 문제

브라우저에는 여러 사이트가 동시에 열려 있고, 쿠키·세션을 공유한다.
한 사이트의 스크립트가 다른 사이트의 **데이터를 읽을 수 있으면**, 열려 있는 은행 세션의 응답을 공격 사이트가 가져갈 수 있다.
그래서 브라우저는 "스크립트는 자기 출처의 응답만 읽는다"는 경계를 둔다.

```text
  evil.test 의 JS ──fetch──▶ bank.example/account   (credentials:'include'이고 쿠키 정책이 허용하면 쿠키 첨부)
                   ◀── 응답 ── 브라우저: "다른 출처다" → JS에 응답을 주지 않음(SOP)
```

- *출처(origin)*: `scheme + host + port` 세 요소. 하나라도 다르면 다른 출처(RFC 6454).
  - `http`·`https` 같은 URL 기준이다. `data:` 등은 이 튜플 대신 고유 식별자(불투명 출처)를 받는다(RFC 6454 §4).
  - 흔한 오해: "포트만 다르면 같은 출처." 포트도 출처의 일부다. `https://a:443`과 `https://a:8443`은 다르다.
- *SOP(Same-Origin Policy, 동일 출처 정책)*: 한 출처의 문서·스크립트가 다른 출처의 리소스를 **읽는** 것을 기본 차단한다.
- *CORS(Cross-Origin Resource Sharing)*: 서버가 특정 교차 출처에 읽기를 **허용**한다고 응답 헤더로 선언하는 완화 규약(WHATWG Fetch).
- CSRF(20번)와 반대 축이다: SOP/CORS는 **읽기**를 막고, CSRF 방어는 **쓰기(부수효과)**를 막는다. 사이트(SameSite) vs 출처(SOP)로 기준도 다르다.

쉬운 예: 도서관 열람실(브라우저)에 여러 금고(사이트)가 있다.
- 내 금고 문서는 내가 본다. 남의 금고 문서는 금고 주인이 "이 사람에게 보여 줘도 된다"고 허락(CORS 헤더)해야 본다.

## 동작·원리

### 1. 단순 요청 — 막는 것은 "보내기"가 아니라 "읽기"

```text
  [JS fetch] ──▶ 요청은 서버에 도착 (쿠키는 credentials:'include'일 때만) ──▶ 서버 200 + 응답 본문 생성
       ◀── 응답 도착 ── 브라우저 CORS 검사 ── ACAO 없음? → JS엔 네트워크 오류(TypeError)
                                           ── ACAO 일치? → JS가 응답 읽음
```

- *단순 요청(simple request)*: preflight가 붙지 않는 요청. 메서드가 `GET`·`HEAD`·`POST`이고, 헤더가 안전 목록이며, `Content-Type`이 `application/x-www-form-urlencoded`·`multipart/form-data`·`text/plain`일 때.
- 단순 요청은 **서버에 먼저 도착해 처리된다.** 브라우저는 응답 **읽기만** 막는다.
  - `fetch()`의 기본 `credentials`는 `same-origin`이다(WHATWG Fetch). 교차 출처 요청에 쿠키를 실으려면 `credentials: 'include'`가 필요하다. 아래 실험 로그도 기본 `fetch`는 `cookie=no`, `include`는 `cookie=yes`였다.
  - 이것이 "서버는 200인데 브라우저가 CORS 에러"의 정체다. 그리고 CSRF가 CORS로 안 막히는 이유다(20번).

### 2. 로컬 실험 — 서버 로그와 브라우저를 함께 본다

(실험, 로컬 127.0.0.1 Node 20 서버 3개 + headless Chrome 151.0.7922.173, 2026-10-07. app=`127.0.0.1:A`, api=`127.0.0.1:B`(다른 포트 = 다른 출처), evil=`localhost:C`(다른 사이트). 쿠키는 가짜.)

```text
GET, no CORS headers           api 로그: -> 200   js: rejected TypeError: Failed to fetch
   console: ... blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present ...
GET, ACAO=app                  api 로그: -> 200   js: resolved status=200 body=secret-data
```

- 핵심: **두 경우 모두 서버 로그에 `200`이 찍힌다.** CORS 헤더가 없을 때 달라지는 것은 JS가 응답을 읽느냐뿐이다.
- 콘솔에는 이유가 나오지만 JS의 `catch`가 받는 메시지는 `Failed to fetch`로 같다([web-platform/05](../../web-platform/05-fetch-from-browser/2-summary.md)).

### 3. credentials + 와일드카드 = 불가

```text
credentials include + ACAO=*             js: rejected TypeError
   console: ... 'Access-Control-Allow-Origin' header ... must not be the wildcard '*'
            when the request's credentials mode is 'include'.
credentials include + 정확한 ACAO + ACAC  js: resolved status=200 body=secret-data
```

- 쿠키를 싣는(`credentials: 'include'`) 요청에는 `Access-Control-Allow-Origin: *`를 쓸 수 없다. 정확한 출처를 돌려주고 `Access-Control-Allow-Credentials: true`를 함께 줘야 한다.
- 정확한 출처를 돌려줄 때는 `Vary: Origin`을 붙여 캐시가 출처별로 분리되게 한다.

### 4. preflight — 안전하지 않은 요청의 사전 질의

```text
  PUT application/json (안전 목록 밖) ──▶ 브라우저가 먼저 OPTIONS(preflight)
     OPTIONS: Access-Control-Request-Method: PUT, -Request-Headers: content-type
     서버가 허용(Allow-Methods/Headers + ACAO)하고 2xx면 ──▶ 본 요청(PUT) 전송
```

```text
PUT json, OPTIONS -> 405        js: rejected TypeError
   console: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' ...
PUT json, OPTIONS -> 405 with ACAO   console: ... doesn't pass ...: It does not have HTTP ok status.
PUT json, preflight ok (204 + 헤더)   api 로그: OPTIONS -> 204, PUT -> 200   js: resolved 200 body=secret-data
```

- *preflight(프리플라이트)*: 본 요청 전에 `OPTIONS`로 "이 메서드·헤더로 보내도 되냐"를 묻는 사전 요청.
- 실험: 서버가 `OPTIONS`를 `405`로 답하면 **preflight 실패 → 본 요청이 안 나간다**. `ACAO`를 붙여도 상태가 2xx가 아니면 실패("It does not have HTTP ok status").
  - 이것이 "preflight 405"의 정체다. 프레임워크가 `OPTIONS`를 자동 처리하지 못하거나 라우트가 없을 때 흔하다.
- preflight 성공(`204` + `Allow-Methods`/`Headers` + `ACAO`) 뒤에야 본 `PUT`이 서버에 도착한다.
- *Access-Control-Max-Age*: preflight 결과를 캐시하는 초. 헤더가 없으면 Fetch 명세 기본값 `5`초("If max-age is failure or null, then set max-age to 5"). 브라우저마다 상한을 따로 둔다. [web-api/28](../../../languages/web-api/28-cors-simple-and-preflight/2-summary.md) 실험: 헤더 없이 같은 `PUT`을 연달아 두 번 보내면 OPTIONS가 1번만 갔다.

### 5. 잘못된 서버 설정 — 아무 Origin이나 반사

```text
evil site, reflect-any-origin + credentials   js: resolved status=200 body=secret-data   (탈취 성공)
evil site, allowlist                           js: rejected TypeError  (막힘)
```

- 서버가 요청의 `Origin`을 검증 없이 그대로 `ACAO`로 되돌리고 `ACAC: true`를 주면, **어느 사이트든 인증 쿠키가 실린 요청의 응답을 읽는다.** 조건: 인증 쿠키가 교차 사이트 요청에 실려야 한다(`SameSite=None`, 이 실험의 쿠키). `Lax`·`Strict` 쿠키는 교차 사이트 `fetch`에 안 실린다. 실험에서 `localhost:C`(다른 사이트)가 `secret-data`를 받았다.
- 고친 설정은 허용 목록과 비교해 일치할 때만 출처를 돌려준다 — 같은 `localhost:C`가 `TypeError`로 막혔다.
  - 와일드카드 서브도메인 반사(`*.example.com`을 정규식으로)도 흔한 사고다. 정확히 비교한다.

## 쓰이는 자료구조·알고리즘

- **출처 튜플 비교**: `(scheme, host, port)` 세 값의 동일성 비교. SOP는 이 튜플이 같아야 읽기를 허용한다. 20번의 사이트(scheme + eTLD+1) 판정과 대비 — CORS는 **출처**, SameSite는 **사이트**.
- **허용 목록 = 집합 조회**: `ACAO`를 정할 때 요청 `Origin`을 허용 집합에서 찾는다(O(1)). 반사·정규식 접두 일치는 사고의 근원.
- **preflight 캐시 = TTL 맵**: Fetch §4.9의 캐시 항목 키는 (네트워크 분할 키, 출처, URL, credentials 여부, 메서드 또는 헤더 이름)이다. 허용 결과를 `Max-Age` 동안 둔다(헤더 없으면 명세 기본 5초).
- **상태 기계(Fetch)**: Request의 mode(`cors`·`no-cors`·`same-origin`·`navigate`)와 credentials, 응답 타입(`basic`·`cors`·`opaque`·`error`)이 다음 단계를 정한다([web-platform/05](../../web-platform/05-fetch-from-browser/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. Spring CORS 설정 — 정확한 출처 + credentials

```java
@Bean
CorsConfigurationSource corsConfig() {
    CorsConfiguration c = new CorsConfiguration();
    c.setAllowedOrigins(List.of("https://app.example.com"));  // allowedOriginPatterns("*") 남용 금지
    c.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
    c.setAllowedHeaders(List.of("Content-Type", "Authorization"));
    c.setAllowCredentials(true);          // true면 ACAO에 * 불가 — Spring이 정확한 출처를 반영
    c.setMaxAge(600L);
    var src = new UrlBasedCorsConfigurationSource();
    src.registerCorsConfiguration("/**", c);
    return src;
}
```

- `allowCredentials(true)`와 `allowedOrigins("*")`를 함께 쓰면 Spring이 예외를 던진다(스펙상 불가, 실험 3과 같은 이유).
- `OPTIONS`는 CORS 필터(또는 Spring MVC의 preflight 처리)가 응답해야 한다. 보안 필터가 `OPTIONS`를 `401`로 가로채면 preflight가 깨진다.

### 2. 진단 순서

```text
1. DevTools Network: 요청이 몇 개 나갔나(OPTIONS가 따로 보이나), 상태, (failed)·CORS error 표시
2. Console: Chrome이 CORS 실패 이유를 적는다(blocked by CORS policy: ...). JS의 e.message엔 안 나온다
3. 서버 로그: 요청이 서버에 닿았나? 닿았다면 "읽기 차단"(단순 요청), 안 닿았다면 "preflight 실패"
4. 응답 헤더: ACAO 값(정확한 출처인가 *인가), ACAC, Vary: Origin, Allow-Methods/Headers
```

### 3. `no-cors`의 함정

- `mode: 'no-cors'`로 보내면 요청은 나가지만 응답이 **opaque**(상태 0, 본문 못 읽음)다. "에러를 없애려" 쓰면 데이터를 못 읽는 건 그대로다. CORS를 끄는 게 아니라 읽기를 포기하는 것.

### 4. SOP를 우회하는 정상 통로

- `<img>`·`<script>`·`<link>`·`<form>`은 SOP 이전부터 교차 출처 로드가 허용된다(읽기는 제한). JSONP는 `<script>`로 데이터를 받는 옛 방식 — CORS가 생긴 뒤로는 쓰지 않는다(콜백 인젝션 위험).
- `postMessage`는 창 간 메시지를 명시적 출처 확인과 함께 주고받는 공식 통로.

## 장애 시나리오와 대처

### 1. "서버는 200인데 브라우저가 CORS 에러"

- **현상**: 서버 로그엔 정상 `200`, 브라우저 콘솔엔 `blocked by CORS policy`.
- **보이는 형태**: `No 'Access-Control-Allow-Origin' header is present`. JS는 `TypeError: Failed to fetch`.
- **원인**: 단순 요청은 서버에 닿아 처리되지만 응답에 CORS 헤더가 없어 **읽기**가 차단됐다.
- **대처**: 서버에 정확한 `ACAO`(+ credentials면 `ACAC`·`Vary: Origin`)를 설정. 서버가 실제로 처리했으므로 상태 변경이었다면 멱등 처리 확인([reliability/13](../../reliability/13-idempotency/2-summary.md)).

### 2. preflight 405 — 본 요청이 안 나간다

- **현상**: `PUT`/`DELETE`나 커스텀 헤더 요청이 전부 실패한다.
- **보이는 형태**: Network에 `OPTIONS`가 `405`/`404`, 콘솔 `Response to preflight request doesn't pass access control check: It does not have HTTP ok status`.
- **원인**: 서버/프레임워크가 `OPTIONS`를 처리하지 못하거나 보안 필터가 가로챘다.
- **대처**: `OPTIONS`에 2xx + `Allow-Methods`/`Headers` + `ACAO`를 주게 한다. Spring이면 CORS 설정을 보안 필터보다 먼저.

### 3. credentials 요청인데 쿠키가 안 실린다

- **현상**: 로그인 세션이 있는데 교차 출처 API가 비인증으로 처리된다.
- **보이는 형태**: 요청에 쿠키 없음, 또는 `ACAO: *`로 응답이 거부됨.
- **원인**: 클라이언트가 `credentials: 'include'`를 안 줬거나, 서버가 `*`/`ACAC` 누락.
- **대처**: 클라 `credentials: 'include'`, 서버 정확한 출처 + `ACAC: true` + `Vary: Origin`. 쿠키 자체는 `SameSite=None; Secure`여야 교차 사이트에 실린다(20번).

### 4. ⚠ Origin 반사 + credentials = 전면 노출

- **현상**: 침투 테스트에서 아무 사이트나 인증된 응답을 읽는다.
- **보이는 형태**: 응답 `ACAO`가 요청 `Origin`을 그대로 반사 + `ACAC: true`.
- **원인**: "편하게" 요청 출처를 반사하도록 설정. 실험에서 `localhost:C`가 `secret-data`를 받았다.
- **대처**: 허용 목록과 정확 비교. 와일드카드·정규식 접두 일치 금지. 공개(비인증) API만 `*` 허용.

### 5. ⚠ CORS를 "보안"으로 오해

- **현상**: CORS로 막았다고 믿은 상태 변경 엔드포인트가 CSRF로 뚫린다.
- **원인**: 단순 요청에 대해 CORS는 응답 **읽기**만 막는다. 단순 요청의 부수효과는 그대로 서버에 닿는다(preflight가 필요한 요청은 preflight 실패 시 본 요청이 안 나간다 — 4절).
- **대처**: 상태 변경은 CSRF 방어(20번: 토큰·SameSite·Origin 검사)로 지킨다. CORS는 데이터 읽기 경계일 뿐이다.

## 핵심 문장

- 출처는 `scheme+host+port` 셋이다. SOP는 다른 출처의 응답 읽기를 기본 차단한다.
- CORS는 서버가 "이 출처에 읽기를 허용한다"고 응답 헤더로 선언하는 완화다. 브라우저가 강제한다.
- 단순 요청은 서버에 먼저 도착해 처리된다. 단순 요청에 대해 CORS는 응답 읽기만 막는다 — "서버 200인데 CORS 에러"의 정체이자 CSRF가 CORS로 안 막히는 이유.
- credentials 요청엔 `ACAO: *`를 쓸 수 없다. 정확한 출처 + `ACAC: true` + `Vary: Origin`.
- 안전 목록 밖 요청은 preflight(OPTIONS)가 먼저 간다. OPTIONS가 2xx가 아니면 본 요청이 안 나간다.
- Origin을 검증 없이 반사하며 credentials를 허용하면 인증 쿠키가 실리는 모든 출처(`SameSite=None` 쿠키면 모든 사이트)가 인증 응답을 읽는다. 허용 목록과 정확 비교.

## 관련 주제·근거

- 선행
  - [11-sessions-and-cookie-security](../11-sessions-and-cookie-security/2-summary.md) — 쿠키 첨부·SameSite
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — HTTP 메서드·헤더
- 후속·연결
  - [20-csrf-and-samesite](../20-csrf-and-samesite/2-summary.md) — 쓰기(부수효과) 쪽 경계. CORS는 읽기 쪽
  - [22-ssrf](../22-ssrf/2-summary.md) — 서버 측 요청. 브라우저 SOP가 없는 세계
  - [web-platform/05-fetch-from-browser](../../web-platform/05-fetch-from-browser/2-summary.md) — fetch의 CORS·credentials·응답 타입
  - [web-api/28-cors-simple-and-preflight](../../../languages/web-api/28-cors-simple-and-preflight/2-summary.md) · [29-credentials-and-cookies](../../../languages/web-api/29-credentials-and-cookies/2-summary.md) — 단순/프리플라이트·Max-Age·credentials 재현
- 1차 출처
  - RFC 6454 — The Web Origin Concept(scheme+host+port) <https://www.rfc-editor.org/rfc/rfc6454>
  - WHATWG Fetch — request credentials mode(기본 `same-origin`) <https://fetch.spec.whatwg.org/#concept-request-credentials-mode> · WHATWG HTML §7.1.1.1 Sites(scheme 포함) <https://html.spec.whatwg.org/multipage/browsers.html#sites>
  - WHATWG Fetch — CORS protocol, preflight, credentials, ACAO/ACAC/Vary <https://fetch.spec.whatwg.org/#http-cors-protocol>
  - MDN CORS <https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS>
  - Spring Framework CORS <https://docs.spring.io/spring-framework/reference/web/webmvc-cors.html>
- 실험 목록(2026-10-07, 로컬 127.0.0.1/localhost + headless Chrome만, 가짜 세션·읽힘 확인)
  - A. 단순 GET: CORS 헤더 없음(서버 200·JS reject) vs ACAO=app(JS resolve) — 서버 로그와 콘솔 대조
  - B. credentials + ACAO=*(reject) vs 정확 출처 + ACAC(resolve)
  - C. preflight: OPTIONS 405(본 요청 미발생) / 405+ACAO(여전히 실패) / 204+헤더(성공)
  - D. 서버가 Origin 반사+credentials(타 사이트 탈취) vs 허용 목록(차단)
  - 코드: `scratchpad/sec/18/web/exp21-cors.js`
