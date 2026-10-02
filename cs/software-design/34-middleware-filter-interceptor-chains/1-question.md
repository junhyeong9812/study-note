# software-design/34-middleware-filter-interceptor-chains — 질문

## 질문

1. (왜) 인증·파싱·로깅을 컨트롤러마다 직접 쓰면 어떤 문제가 생기나? 체인으로 모으면 무엇이 정해지나? 뼈대가 되는 GoF 패턴은?
2. (그림) 필터 F1·F2와 인터셉터 I1·I2를 등록 순서대로 둔 Spring MVC 앱에서 `GET /hello`의 실행 순서를 그려라(`preHandle`·`postHandle`·`afterCompletion` 포함).
3. (예측) 위 앱에서 I2의 `preHandle`이 false를 돌려주면 컨트롤러·`postHandle`·`afterCompletion` 중 무엇이 불리나? I2 자신의 `afterCompletion`은?
4. (예측) Express에서 `log → json → auth` 순서와 `json → auth → log` 순서로 등록했다. 인증 없는 요청과 인증된 요청의 로그는 각각 어떻게 다른가? 두 번째 순서의 위험은?
5. (예측) "다음 고리 호출"을 빠뜨린 미들웨어가 있으면 Express·Koa·Servlet Filter에서 클라이언트는 각각 무엇을 받나?
6. (경계) Servlet 필터의 순서는 무엇으로 정해지나? `@WebFilter`로 순서를 줄 수 있나? Spring Boot에서 필터 빈의 순서를 주는 방법과 주지 못하는 방법은?
7. (연결) 인터셉터와 필터는 무엇이 다른가? Spring은 인증·인가를 어느 쪽에 두라고 하나? NestJS 요청 수명 주기에서 미들웨어·가드·인터셉터·파이프의 순서는?
8. (장애 진단) 한 요청에 같은 필터 로그가 두 줄씩 찍히고 레이트 리밋 카운트가 두 배로 오른다. 원인 후보와 대처는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
