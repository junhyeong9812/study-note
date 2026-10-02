# software-design/43-data-across-boundaries — 질문

## 질문

1. (왜) JPA 엔티티를 컨트롤러에서 그대로 JSON으로 돌려주면 어떤 세 가지가 한데 묶이나?
2. (그림) 요청 모델·도메인 모델·영속 모델·응답 모델을 경계와 함께 그려라. 각각이 바뀌는 이유는?
3. (예측) 양방향 연관(`Member.orders` ↔ `PurchaseOrder.member`)인 엔티티를 ① 세션 안 ② 세션 밖에서 Jackson 2.22.3으로 직렬화하면 각각 어떤 오류가 나나? ③ 컬렉션만 빼면 무엇이 나가나?
4. (예측) 호출당 5ms인 원격 경계에서 회원 이름·등급·주문 N건(주문마다 id·금액)을 세밀한 게터로 가져오면 왕복은 몇 번인가? 주문 50건이면? Remote Facade면?
5. (경계) PoEAA의 DTO·Remote Facade 정의는? Remote Facade에 도메인 로직을 두나?
6. (경계) Fowler "LocalDTO"는 어떤 DTO 사용을 비판하고, 어떤 경우는 인정하나? HTTP 응답 모델은 어느 쪽인가?
7. (예측) DTO에 `phone`을 추가하고 매퍼를 안 고쳤다. 세터식 매퍼와 레코드 생성자 매퍼는 각각 어떻게 되나?
8. (장애 진단) 서비스 테스트는 다 통과하는데 회원 API만 500이다. 로그에 `Cannot lazily initialize collection ... (no session)`이 있다. 원인과 대처는? Spring Boot에서 이 예외 대신 다른 증상이 나오는 경우는?
9. (장애 진단) 보안 점검에서 API 응답에 비밀번호 해시가 보였다. `@JsonIgnore`를 붙이는 것으로 충분한가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
