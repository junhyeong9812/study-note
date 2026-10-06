# security/19-xss-and-csp — 반사·저장·DOM XSS, 문맥별 인코딩, CSP — 정리 (힌트)

## 해결하는 문제

브라우저는 서버가 보낸 HTML을 신뢰하고 그 안의 스크립트를 실행한다.
사용자 입력이 HTML·JS로 섞여 들어가면, 공격자의 스크립트가 **피해자의 출처(origin)**에서 실행된다.

```text
  의도: <p>검색어: [데이터]</p>
  실제: <p>검색어: <img src=x onerror="...쿠키 전송..."></p>
                     └─ 데이터가 태그·이벤트 핸들러(코드)로 해석됨
```

- *XSS(Cross-Site Scripting)*: 공격자 스크립트를 피해자 브라우저에서, 피해자가 보는 사이트의 권한으로 실행시키는 결함.
- 18번(인젝션)의 브라우저 판이다. 해석기가 DB 파서 대신 **HTML 파서·JS 엔진**이다.
- 실행되면 세션 쿠키 탈취(HttpOnly 아니면), 화면 조작, 사용자 대신 요청(CSRF 방어 무력화), 키 입력 가로채기가 가능하다.
  - 흔한 오해: "CSP를 켜면 XSS는 끝." OWASP는 CSP를 "심층 방어"로 쓰라고 한다. 1차 방어는 문맥별 출력 인코딩이다.

쉬운 예: 게시판에 "글"이 아니라 "이 페이지를 보는 사람은 자기 비밀을 내게 보내라"는 **지시문**을 올린다.
- 다른 사람이 글을 열 때 그 지시가 그 사람 브라우저에서 실행되면 사고다.

### 세 종류

```text
  반사(reflected): 요청 파라미터가 응답에 그대로 → 악성 링크 클릭 시 1회 실행
  저장(stored):    입력이 DB에 저장 → 그 글을 보는 모든 사용자에게 실행 (가장 위험)
  DOM:             브라우저의 JS가 location.hash 등을 위험 sink(innerHTML)에 넣어 실행
```

- 저장형은 한 번의 주입이 모든 열람자에게 퍼진다(웜 가능).
- DOM형은 응답 HTML에 페이로드가 안 보인다. 브라우저 안의 JS가 값을 조합하므로 응답을 검사하는 서버 측 필터로는 못 잡는다.
  - `#` 뒤 조각이 입력원이면 요청에도 안 실려 WAF가 볼 입력 자체가 없다. `location.search`가 입력원이면 요청에는 실린다(OWASP DOM Based XSS). 구분 기준은 서버 경유 여부가 아니라 "브라우저 쪽 코드의 위험한 처리"다.

## 동작·원리

### 1. 문맥마다 "코드가 되는 문자"가 다르다

```text
  HTML 본문      <p>HERE</p>              위험: < > & → 태그 시작
  HTML 속성값    <input value="HERE">     위험: " (따옴표 닫기) → 새 속성 onfocus=
  속성값(무따옴표) <input value=HERE>       위험: 공백 → 새 속성! (따옴표 없으면 공백이 경계)
  URL 속성       <a href="HERE">          위험: javascript: 스킴 → 클릭 시 실행
  <script> 안    var x = "HERE";          위험: " </script> → JS·HTML 문맥 탈출
```

- *문맥(context)*: 값이 들어가는 자리의 문법. HTML 본문·속성·JS·CSS·URL이 각기 다른 escape 규칙을 가진다.
- OWASP XSS Prevention Cheat Sheet: 문맥별로 인코딩한다. HTML 본문은 HTML 엔티티 인코딩(`&`·`<`·`>`·`"`·`'`), 속성값은 "따옴표로 감싸고 HTML 속성 인코딩, 속성 이름은 고정".
- 그래서 "한 번 escape하면 끝"이 아니다. 같은 입력도 자리마다 다르게 인코딩해야 한다 — 템플릿 엔진의 자동 문맥 인코딩(Thymeleaf의 `th:text`, React의 JSX 보간)을 쓰는 이유다.

### 2. 인코딩이 막는 것과 못 막는 것 — 로컬 브라우저 실험

(실험, 로컬 127.0.0.1 Node 20 서버 + headless Chrome 151.0.7922.173, playwright-core 1.62.1, 2026-10-07. 페이로드는 `document.cookie`를 변수에 넣어 **읽힘만** 확인, 외부 전송 없음. 쿠키는 가짜 값.)

```text
reflect (raw)        {"xss":"sid_plain=FAKE-1"}        ← HTML 본문에 생입력: 실행됨, HttpOnly 아닌 쿠키 노출
reflect-esc          {}                                ← HTML 엔티티 인코딩: 텍스트로 표시, 실행 안 됨
   text shown: 검색어: <img src=x onerror="...">        (화면에 글자 그대로)
attr-unquoted + esc  {"xss":1}                         ← 엔티티 인코딩해도 따옴표 없는 속성은 공백으로 탈출
attr-quoted + esc    {}                                ← 따옴표로 감싸니 막힘
href javascript: +esc {"xss":1}                        ← HTML 인코딩만으로 javascript: 스킴은 못 막음
```

- `reflect (raw)`: 쿠키 `sid_plain`(HttpOnly 없음)은 읽혔다. `sid_http`(HttpOnly)는 `document.cookie`에 없었다 — HttpOnly의 효과.
- `attr-unquoted`: HTML 엔티티 인코딩을 해도 따옴표가 없으면 공백이 속성 경계라 `onfocus=...`가 붙었다. **속성은 반드시 따옴표로 감싼다.**
- `href javascript:`: 값에 특수문자가 없어 엔티티 인코딩이 통과시킨다. URL 문맥은 스킴 허용 목록(`http`·`https`·`mailto`)이 따로 필요하다.

### 3. DOM XSS — 위험 sink를 피한다

```text
  location.hash ─▶ el.innerHTML = v     위험 sink: 문자열을 HTML로 파싱
  location.hash ─▶ el.textContent = v   안전 sink: 문자열을 텍스트로
```

```text
dom innerHTML     {"xss":"sid_plain=FAKE-1","sinkOk":1}   ← 실행됨
dom textContent   {"sinkOk":1}                            ← 텍스트로 들어가 실행 안 됨
dom innerHTML + TT {"sinkErr":"TypeError: ... requires 'TrustedHTML'"}  ← Trusted Types가 막음
```

- `innerHTML`은 문자열을 HTML로 파싱한다. `textContent`는 텍스트 노드로 넣는다([web-api/04](../../../languages/web-api/04-textcontent-innerhtml-innertext/2-summary.md)).
  - 참고: `<img onerror>`는 `innerHTML`로 삽입하면 리소스 로드 실패 시 실행된다. `<script>`를 `innerHTML`로 넣으면 실행되지 않지만 `onerror`·`onload` 핸들러는 실행되므로 안전하지 않다.
- *Trusted Types*(W3C, Chrome 83+·Firefox 148+·Safari 26+ — MDN 호환성 데이터 기준): `require-trusted-types-for 'script'` CSP가 있으면 `innerHTML`에 문자열을 직접 넣는 것을 `TypeError`로 막는다. 정책을 통과한 `TrustedHTML`만 허용한다.
  - 조건: `default` 정책이 없을 때(이 실험) 또는 `default` 정책이 값을 거부할 때다. `default` 정책이 있으면 문자열이 그 정책을 거쳐 들어갈 수 있다(W3C Trusted Types §3.5).

### 4. CSP — 심층 방어선

```text
  Content-Security-Policy: script-src 'nonce-r4nd0m'; object-src 'none'; base-uri 'none'

  <script nonce="r4nd0m">...</script>   ← nonce 일치: 실행
  <script>...</script>                  ← nonce 없음: 차단 (인젝션된 인라인)
  <img onerror="...">                   ← 이벤트 핸들러: 차단
```

- *CSP(Content Security Policy, W3C Level 3)*: 응답 헤더로 "어떤 출처의 스크립트·리소스를 허용할지" 선언한다. 브라우저가 강제한다.
- *nonce*: 응답마다 새로 만드는 1회용 난수. 서버가 심은 `<script nonce>`만 실행된다. 인젝션된 스크립트는 nonce를 모른다.
- 실험 콘솔(enforce):

```text
Executing inline script violates the following Content Security Policy directive 'script-src 'nonce-r4nd0m''. ... The action has been blocked.
Executing inline event handler violates ... The action has been blocked.
```

- 결과: nonce 있는 `window.__legit=1`만 실행(`{"legit":1}`), 인젝션된 인라인 스크립트와 `onerror`는 차단. XSS 미실행.
- 보고 전용 모드(`Content-Security-Policy-Report-Only`): 위반을 **로그만** 하고 막지 않는다. 실험에서 XSS가 그대로 실행되며(`{"xss":"sid_plain=FAKE-1"}`) 콘솔에 "The policy is report-only, so the violation has been logged but no further action has been taken." 배포 전 정책을 시험하는 용도다.
  - 흔한 오해: Report-Only가 켜져 있으면 막힌다고 착각한다. 막지 않는다.

## 쓰이는 자료구조·알고리즘

- **문맥 인코딩 상태 기계**: HTML 파서는 데이터 상태·태그 상태·속성 상태·스크립트 상태를 오가는 상태 기계다(WHATWG HTML tokenizer). 어느 상태에서 값이 들어가느냐가 escape 규칙을 정한다. 18번의 파서 문맥 분리와 같은 뿌리.
- **nonce = CSPRNG 1회용 토큰**: 요청마다 새 난수. 예측 불가가 핵심이라 암호학적 난수가 필요하다([09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md)).
- **허용 목록**: URL 스킴·CSP의 소스 목록 모두 "허용된 것만"의 집합 조회다.
- **HTML 정화(sanitize) = 파싱 후 트리 화이트리스트 순회**: DOMPurify는 입력을 DOM 트리로 파싱한 뒤 허용된 태그·속성만 남긴다(사용자 서식 HTML이 꼭 필요할 때).

## 적용 — 풀어나가는 법

### 1. 서버 템플릿 — 자동 인코딩을 끄지 않는다

```html
<!-- Thymeleaf: th:text 는 HTML 엔티티 인코딩(안전) -->
<p th:text="${q}">검색어</p>
<!-- th:utext 는 인코딩 안 함(생 HTML) — 사용자 입력에 쓰면 저장형 XSS -->
<p th:utext="${q}"></p>   <!-- 위험 -->
```

- 대부분의 템플릿 엔진은 기본이 escape다. "unescaped" 기능(`th:utext`, Mustache `{{{ }}}`, JSTL `<c:out escapeXml="false">`)이 구멍이다.
  - 예외: JSP 본문에 쓴 `${...}` EL 출력은 기본으로 escape되지 않는다. JSTL `<c:out>`은 기본 `escapeXml=true`다(Jakarta Tags 3.0 §4.1).

### 2. 프런트엔드 프레임워크 — 탈출구를 피한다

```jsx
// React: 기본 보간은 텍스트로 안전
<p>{q}</p>
// 위험한 탈출구 — 사용자 입력엔 쓰지 않는다 (불가피하면 DOMPurify)
<p dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />
```

- 프레임워크별 탈출구: React `dangerouslySetInnerHTML`, Angular `bypassSecurityTrustHtml`, Vue `v-html`, Lit `unsafeHTML`. 이름에 "danger/bypass/unsafe"가 들어간다.

### 3. URL·속성 문맥

```java
// href에 사용자 URL을 넣기 전에 스킴 허용 목록
URI u = URI.create(input);
String scheme = u.getScheme() == null ? "" : u.getScheme().toLowerCase();
if (!Set.of("http", "https", "mailto").contains(scheme)) throw new IllegalArgumentException("bad scheme");
```

- 실험 3에서 봤듯 HTML 엔티티 인코딩만으로 `javascript:`는 통과한다. 속성 자체도 항상 따옴표로 감싼다.

### 4. CSP를 단계적으로 — 설정과 진단

```text
# 1단계: 보고 전용으로 현황 파악
Content-Security-Policy-Report-Only: script-src 'self'; report-uri /csp-report
# 2단계: nonce 기반으로 강제 (인라인 제거)
Content-Security-Policy: script-src 'nonce-{요청별난수}' 'strict-dynamic'; object-src 'none'; base-uri 'none'
```

- `'strict-dynamic'`: nonce로 신뢰된 스크립트가 동적으로 로드하는 스크립트까지 신뢰한다(호스트 허용 목록 유지 부담을 던다, CSP Level 3).
- 진단: 브라우저 콘솔의 CSP 위반 메시지, `report-uri`/`report-to`로 수집한 위반 보고를 본다.
- Spring Security 헤더 설정:

```java
// policyDirectives 문자열은 그대로 헤더로 나간다 — Spring Security가 nonce를 만들어 넣지 않는다
http.headers(h -> h.contentSecurityPolicy(csp ->
    csp.policyDirectives("script-src 'self'; object-src 'none'; base-uri 'none'")));
```

- 여기에 `'nonce-{random}'`처럼 쓰면 그 글자 그대로 고정 값이 된다(`ContentSecurityPolicyHeaderWriter`는 문자열을 그대로 `setHeader`한다). 요청마다 다른 nonce가 필요하면 필터에서 난수를 만들어 헤더와 템플릿에 같은 값을 넣는 코드를 직접 둔다.

### 5. 쿠키·CSP를 함께

- 세션 쿠키에 `HttpOnly`를 주면 XSS가 `document.cookie`로 세션을 훔치지 못한다(실험에서 `sid_http`는 안 읽혔다). 단 XSS는 여전히 사용자 대신 요청할 수 있다.
- 토큰을 `localStorage`에 두면 XSS 한 번에 탈취된다([17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md) 참조, [web-platform/06-browser-storage](../../web-platform/06-browser-storage/2-summary.md)).

## 장애 시나리오와 대처

### 1. 저장형 XSS — 게시글 열람자마다 세션 탈취

- **현상**: 특정 글을 연 사용자들의 계정이 탈취된다.
- **보이는 형태**: 글 본문에 `<img onerror>`·`<script>`, 접근 로그에 공격자 수집 서버로의 요청(HttpOnly 아닌 경우).
- **원인**: 저장 시 또는 출력 시 인코딩 없이 HTML 본문에 삽입.
- **대처**: 출력 문맥 인코딩, 서식이 필요하면 DOMPurify, 세션 쿠키 `HttpOnly`, 심층 방어로 nonce CSP. 유출 범위 산정은 감사 로그([26-security-logging-and-audit](../26-security-logging-and-audit/2-summary.md)).

### 2. "escape했는데 뚫렸다" — 따옴표 없는 속성

- **현상**: HTML 엔티티 인코딩을 했는데도 속성 자리에서 실행된다.
- **보이는 형태**: `<input value=사용자입력>`처럼 따옴표 없는 속성.
- **원인**: 따옴표가 없으면 공백이 속성 경계다. 엔티티 인코딩은 공백을 바꾸지 않는다(실험 `attr-unquoted`).
- **대처**: 속성을 항상 따옴표로 감싼다. 자동 인코딩 템플릿을 쓴다.

### 3. DOM XSS — 서버 로그엔 안 보인다

- **현상**: WAF·서버 필터를 통과하는데도 XSS가 난다.
- **보이는 형태**: `location.hash`·`location.search`가 `innerHTML`·`document.write`·`eval`에 닿는 JS.
- **원인**: 값이 브라우저 안에서 위험 sink로 간다. 응답에는 페이로드가 없다. 특히 `#` 뒤 조각은 서버로 전송조차 안 된다(`location.search`는 요청에는 실린다).
- **대처**: 일반 요소의 `textContent`, `setAttribute`(`title`·`value`처럼 텍스트로만 쓰이는 고정 이름 — `on*`·`href`·`src`·`style` 제외) 같은 안전 sink, Trusted Types 강제(실험에서 `innerHTML`을 `TypeError`로 차단).

### 4. ⚠ CSP를 Report-Only로 켜 두고 안심

- **현상**: CSP 헤더가 있는데 XSS가 실행된다.
- **보이는 형태**: 헤더가 `Content-Security-Policy-Report-Only`, 콘솔에 "...logged but no further action has been taken."
- **원인**: 보고 전용 모드는 막지 않는다.
- **대처**: 검토가 끝나면 `Content-Security-Policy`로 강제한다. 두 헤더를 함께 둘 수 있다(강제 + 다음 정책 시험).

### 5. CSP에 `'unsafe-inline'`을 넣어 무력화

- **현상**: CSP가 있는데도 인라인 스크립트가 실행된다.
- **원인**: 기존 인라인 코드를 살리려 `script-src`에 `'unsafe-inline'`을 넣었다. nonce와 함께 쓰면 최신 브라우저는 nonce를 우선해 `'unsafe-inline'`을 무시하지만, nonce가 없으면 모든 인라인이 허용된다.
- **대처**: 인라인 스크립트를 외부 파일로 옮기거나 nonce/hash로 허용한다. `'strict-dynamic'`으로 호스트 목록 부담을 던다.

## 핵심 문장

- XSS는 18번(인젝션)의 브라우저 판이다. 해석기가 HTML 파서·JS 엔진이고, 입력이 태그·핸들러·스킴으로 해석된다.
- 1차 방어는 **문맥별 출력 인코딩**이다. 같은 입력도 HTML 본문·속성·JS·URL에서 escape 규칙이 다르다.
- HTML 엔티티 인코딩만으로는 따옴표 없는 속성과 `javascript:` 스킴을 못 막는다. 속성은 따옴표로 감싸고, URL은 스킴 허용 목록.
- DOM XSS는 브라우저 쪽 코드가 만든다(`#` 조각이면 서버를 아예 안 거친다). `innerHTML` 대신 일반 요소의 `textContent` 같은 안전 sink, Trusted Types로 막는다.
- CSP는 심층 방어다. nonce 기반이 인라인 인젝션을 막는다. Report-Only는 로그만 하고 막지 않는다.
- 세션 쿠키 `HttpOnly`는 쿠키 탈취를 막지만, XSS가 사용자 대신 요청하는 것은 못 막는다.

## 관련 주제·근거

- 선행
  - [18-injection](../18-injection/2-summary.md) — 데이터가 코드로 읽히는 결함의 뿌리
- 후속·연결
  - [20-csrf-and-samesite](../20-csrf-and-samesite/2-summary.md) — XSS는 CSRF 방어를 무력화한다
  - [11-sessions-and-cookie-security](../11-sessions-and-cookie-security/2-summary.md)(HttpOnly·Secure), [17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md)(토큰 저장 위치)
  - [web-api/04-textcontent-innerhtml-innertext](../../../languages/web-api/04-textcontent-innerhtml-innertext/2-summary.md) — innerHTML·textContent·innerText의 파싱과 XSS
  - [web-platform/06-browser-storage](../../web-platform/06-browser-storage/2-summary.md) — 토큰을 localStorage에 두면 XSS로 탈취
- 1차 출처
  - OWASP Top 10 2021 A03 Injection — XSS(CWE-79) 포함 <https://top10.owasp.org/2021/A03_2021-Injection/>
  - OWASP XSS Prevention Cheat Sheet — 문맥별 출력 인코딩, 속성 따옴표, URL 스킴 <https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html> · DOM based XSS Prevention Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html>
  - OWASP DOM Based XSS(쿼리 문자열 사례·`#` 조각 변형) <https://owasp.org/www-community/attacks/DOM_Based_XSS> · Jakarta Tags 3.0 §4.1 `<c:out>` `escapeXml` 기본 true <https://jakarta.ee/specifications/tags/3.0/jakarta-tags-spec-3.0.pdf>
  - W3C Content Security Policy Level 3 — script-src·nonce·strict-dynamic·Report-Only <https://www.w3.org/TR/CSP3/>
  - W3C Trusted Types <https://w3c.github.io/trusted-types/dist/spec/> · 브라우저 지원: MDN browser-compat-data `api/TrustedHTML.json`(Chrome 83·Firefox 148·Safari 26)
  - WHATWG HTML Standard — tokenization(파서 상태) <https://html.spec.whatwg.org/multipage/parsing.html#tokenization>
  - CWE-79 <https://cwe.mitre.org/data/definitions/79.html>
- 실험 목록(2026-10-07, 로컬 127.0.0.1 + headless Chrome만, 가짜 쿠키·읽힘만 확인)
  - A. 반사형 생입력 vs HTML 엔티티 인코딩 — 실행 여부·HttpOnly 쿠키 노출 차이
  - B. 따옴표 없는/있는 속성, `javascript:` href — 엔티티 인코딩의 한계
  - C. DOM: `innerHTML` vs `textContent` vs Trusted Types 강제 — Chrome 151, `TypeError: requires 'TrustedHTML'`
  - D. CSP nonce 강제(인라인·핸들러 차단, nonce 스크립트 실행) vs Report-Only(미차단) — 콘솔 위반 메시지 수집
  - 코드: `scratchpad/sec/18/web/exp19-xss-csp.js`
