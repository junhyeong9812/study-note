# software-design/36-extension-points-and-plugins — 질문

## 질문

1. (왜) 확장 지점이 없을 때 결제 수단 하나를 추가하면 무엇이 바뀌나? SPI는 보통의 API와 방향이 어떻게 다른가?
2. (그림) PoEAA Separated Interface·Plugin을 코어 모듈·플러그인 모듈 그림으로 그려라. 컴파일 의존 화살표는 어느 쪽을 향하나?
3. (예측) `ServiceLoader`로 `api.jar`만, `+card.jar`, `+card.jar+kakao.jar`를 차례로 실행하면 각각 어떻게 되나? `stream()`으로 타입만 볼 때 생성자가 불리나?
4. (예측) 클래스패스에서 `kakao.jar`와 `card.jar` 순서를 바꾸면 무엇이 바뀌나? 레지스트리가 `putIfAbsent`라면 어떤 위험이 있나?
5. (경계) Spring Boot 자동 설정은 사용자 설정과 비교해 언제 등록되나? `@ConditionalOnMissingBean`을 일반 `@Configuration`보다 자동 설정에 쓰라는 이유는?
6. (예측) 자동 설정의 `@Bean` 반환 타입이 `DefaultPaymentClient`(구현 클래스)이고 `@ConditionalOnMissingBean`만 붙어 있다. 사용자가 `PaymentClient` 타입 `CustomPaymentClient`를 정의하면 기동 결과는? 어떻게 고치나?
7. (예측) 자동 설정이 조건 없이 사용자 빈과 같은 이름 `paymentClient`를 등록한다. Boot 기본 설정에서와 `allow-bean-definition-overriding=true`에서 결과는?
8. (연결) 이벤트 리스너는 어떤 의미의 확장 지점인가? Spring 기본 동작에서 리스너의 예외·지연은 발행자에게 어떤 영향을 주나?
9. (장애 진단) 배포 후 특정 기능만 조용히 꺼졌다. 플러그인 방식에서 의심할 원인 둘과 확인 방법은?
10. (장애 진단) SPI 인터페이스에 메서드를 하나 추가해 배포했더니 외부 플러그인에서 실패가 났다. 언제 어떤 오류가 나며, 어떻게 피하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
