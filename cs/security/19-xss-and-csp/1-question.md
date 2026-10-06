# security/19-xss-and-csp — 질문

## 질문

1. (왜) XSS를 "인젝션(18번)의 브라우저 판"이라고 한다. 해석기는 무엇으로 바뀌고, 입력이 무엇으로 해석되나? 실행되면 공격자는 어떤 권한을 얻나?
2. (경계) 반사·저장·DOM XSS를 구분하라. 왜 저장형이 가장 위험하고, 왜 DOM형은 서버 측 필터·WAF로 못 막나?
3. (예측) 사용자 입력을 HTML 엔티티 인코딩(`< > & " '`)했다. (a) `<input value="HERE">`, (b) `<input value=HERE>`(따옴표 없음), (c) `<a href="HERE">`에 `javascript:...`를 넣은 경우 — 각각 막히나?
4. (예측) `el.innerHTML = location.hash.slice(1)`과 `el.textContent = location.hash.slice(1)`에 `<img src=x onerror=...>`를 주면 결과가 어떻게 다른가? Trusted Types를 강제하면?
5. (경계) CSP `script-src 'nonce-r4nd0m'`가 켜져 있다. `<script nonce="r4nd0m">`, 인젝션된 `<script>`, `<img onerror>`는 각각 실행되나? `Content-Security-Policy-Report-Only`로 같은 정책을 주면 XSS가 막히나?
6. (연결) 세션 쿠키에 `HttpOnly`를 주면 XSS에 대해 무엇을 막고 무엇을 못 막나? 토큰을 `localStorage`에 두면 왜 위험한가?
7. (장애 진단) HTML 엔티티 인코딩을 분명히 했는데 속성 자리에서 XSS가 터진다. 가장 가능성 큰 원인과 수정은?
8. (장애 진단) WAF와 서버 측 입력 필터를 모두 통과하는데 XSS가 난다. 어떤 종류이며 무엇을 봐야 하나?
9. (연결) "CSP를 켰으니 출력 인코딩은 안 해도 된다"는 주장의 문제는? OWASP는 CSP를 무엇이라 부르나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
