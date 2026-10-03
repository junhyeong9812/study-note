# api-design/02-rest-and-resource-modeling — 질문

## 질문

1. (왜) 모든 요청을 `POST /api` 한 곳으로 보내는 RPC식 HTTP API에서, 캐시·프록시·HTTP 클라이언트 라이브러리 같은 중간자가 도와줄 수 없게 되는 이유는? REST의 어떤 제약이 이것을 해결하나?
2. (그림) Fielding 5장이 Null style에서 REST를 유도하는 제약 순서를 그려라. 무상태·캐시·균일 인터페이스 제약이 각각 얻는 것과 잃는 것은?
3. (경계) Fielding이 정의한 "자원"과 "표현"은 무엇인가? "저자가 선호하는 판(authors' preferred version) 논문"과 "학회 X 게재판 논문"이 같은 파일을 가리켜도 다른 자원인 이유는? 이것이 "API = DB 테이블" 설계에 주는 함의는?
4. (경계) Richardson 성숙도 모델의 Level 0~3을 설명하라. 업계에서 말하는 "REST API"와 Fielding의 REST는 어떻게 다른가? Fowler는 RMM을 무엇으로 쓰라고 하나?
5. (예측) 같은 상품 조회를 `GET /products/1`과 `POST /getProduct`로 만들고 둘 다 `Cache-Control: public, max-age=60`을 준다. nginx `proxy_cache`(기본 설정) 뒤에서 각각 3번 요청하면 백엔드 도착 수는? 캐시 상태 헤더는?
6. (예측) 서버가 막 닫은 keep-alive 연결로 JDK 21 `HttpClient`가 `GET /products/1`, `POST /getProduct`, `POST /orders`를 보낸다. 기본 설정에서 각각 어떻게 되나? `-Djdk.httpclient.enableAllMethodRetry=true`를 켜면? 그 근거가 되는 소스 위치는?
7. (경계) "URL에 동사를 쓰지 말라"는 규칙은 어디까지 맞나? Google AIP-136은 커스텀 메서드에 어떤 HTTP 메서드 조건을 거나? 동작을 자원으로 바꾸는 예를 들어라.
8. (연결) 검색 조건이 길어 URL에 담기 어렵다. POST로 조회할 때 잃는 것은? RFC 10008 QUERY 메서드는 무엇을 보장하고, 도입 전에 무엇을 확인해야 하나?
9. (장애 진단) 메일로 보낸 `GET /approve?id=…` 링크 때문에 아무도 누르지 않은 승인이 생겼다. 무엇이 호출했을 가능성이 높고, RFC 9110은 무엇을 요구하나? 어떻게 고치나?
10. (장애 진단) 인스턴스를 2대로 늘렸더니 단계형 결제 흐름의 "다음 단계" 요청이 간헐적으로 실패한다. 어떤 REST 제약을 어겼을 가능성이 크고, 자원 모델로 어떻게 바꾸나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
