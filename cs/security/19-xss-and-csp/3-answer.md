# security/19-xss-and-csp — 정답

## 정답

### 1. 인젝션의 브라우저 판

- 해석기가 DB 파서 대신 브라우저의 **HTML 파서와 JS 엔진**이다. 입력이 태그·이벤트 핸들러·스킴(코드)으로 해석된다.
- 실행되면 공격자 스크립트가 **피해자의 출처 권한**으로 돈다: 세션 쿠키 읽기(HttpOnly 아니면), DOM 조작, 사용자 대신 요청, 키 입력 가로채기.

### 2. 세 종류

- 반사형: 요청 파라미터가 응답에 그대로 반사. 악성 링크를 클릭해야 하고 1회성.
- 저장형: 입력이 DB에 저장되어 그 글을 보는 **모든** 사용자에게 실행. 한 번 주입으로 퍼진다.
- DOM형: 브라우저의 JS가 `location.hash` 등을 위험 sink에 넣어 실행. 응답에는 페이로드가 없다.
- 서버 측 필터·WAF로 못 막는 이유: 값 조합이 브라우저 안에서 일어나 응답에는 페이로드가 없다. 입력원이 `#` 뒤 조각이면 요청에도 실리지 않아 볼 입력 자체가 없다. (`location.search`는 요청에 실리므로 WAF가 볼 수는 있다 — OWASP DOM Based XSS.)

### 3. 엔티티 인코딩의 한계

- (a) `value="HERE"`: 막힌다. 실험 `attr-quoted + esc` → `{}`.
- (b) `value=HERE`(따옴표 없음): 막히지 않는다. 공백이 속성 경계라 `onfocus=...`가 붙는다. 실험 `attr-unquoted + esc` → `{"xss":1}`.
- (c) `href="javascript:..."`: 막히지 않는다. 값에 특수문자가 없어 인코딩을 통과한다. 실험 `href javascript: + esc` → `{"xss":1}`. URL은 스킴 허용 목록이 따로 필요하다.

### 4. innerHTML vs textContent vs Trusted Types

- `innerHTML`: 문자열을 HTML로 파싱한다. `<img onerror>`가 삽입되고 로드 실패 시 핸들러가 실행된다. 실험 `{"xss":"sid_plain=FAKE-1","sinkOk":1}`.
- `textContent`: 텍스트 노드로 넣는다. 실행 안 됨(`div` 같은 일반 요소일 때 — `<script>` 요소의 `textContent`는 코드가 된다, OWASP XSS Cheat Sheet). 실험 `{"sinkOk":1}`(xss 없음).
- Trusted Types 강제(`require-trusted-types-for 'script'`): `default` 정책이 없으면(이 실험) `innerHTML`에 문자열 직접 대입이 `TypeError: ... requires 'TrustedHTML'`로 차단. `default` 정책이 있으면 문자열이 그 정책을 거친다. 실험 `{"sinkErr":"TypeError: ..."}`.

### 5. CSP nonce

- `<script nonce="r4nd0m">`: 실행. 실험에서 `{"legit":1}`.
- 인젝션된 `<script>`(nonce 없음): 차단. 콘솔 "Executing inline script violates ... The action has been blocked."
- `<img onerror>`: 차단(인라인 이벤트 핸들러).
- Report-Only로 주면 **막지 않는다**. XSS가 실행되고(`{"xss":"sid_plain=FAKE-1"}`) 콘솔에 "The policy is report-only, so the violation has been logged but no further action has been taken."

### 6. HttpOnly와 저장 위치

- `HttpOnly`는 JS의 `document.cookie`에서 쿠키를 숨긴다. 실험에서 `sid_http`(HttpOnly)는 안 읽혔고 `sid_plain`은 읽혔다. → 쿠키 탈취는 막는다.
- 못 막는 것: XSS는 여전히 같은 출처에서 `fetch`로 **사용자 대신 요청**할 수 있다(쿠키는 브라우저가 자동으로 싣는다).
- `localStorage`는 JS가 항상 읽을 수 있어 `HttpOnly` 같은 보호가 없다. XSS 한 번에 토큰이 탈취된다([web-platform/06](../../web-platform/06-browser-storage/2-summary.md)).

### 7. 인코딩했는데 속성에서 터짐

- 원인: 속성값을 따옴표로 감싸지 않았다. HTML 엔티티 인코딩은 공백을 바꾸지 않으므로 무따옴표 속성에서 새 속성이 붙는다(실험 (b)).
- 수정: 모든 속성값을 `"`로 감싼다. 자동 문맥 인코딩 템플릿을 쓴다.

### 8. 필터 통과 XSS

- DOM XSS다. 값이 브라우저 안에서 위험 sink로 가고 응답에는 페이로드가 없다(`#` 조각이면 요청에도 없다).
- 봐야 할 것: `location.hash`·`location.search`·`document.referrer`가 `innerHTML`·`document.write`·`eval`·`setTimeout(string)`에 닿는 경로. 안전 sink(일반 요소의 `textContent`, `title`·`value` 같은 텍스트 속성 이름을 고정한 `setAttribute`)로 바꾸고 Trusted Types 강제.

### 9. CSP만 믿기

- CSP는 우회 경로가 있다(허용된 CDN의 취약 스크립트, JSONP, `'unsafe-inline'` 오설정, 오래된 브라우저 미지원). 1차 방어가 아니다.
- OWASP는 CSP를 "defense-in-depth(심층 방어)"라고 부른다. 1차 방어는 문맥별 출력 인코딩과 안전 sink다. 인코딩과 CSP를 함께 둔다.
