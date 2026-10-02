# software-design/25-dependency-injection-and-composition-root — 질문

## 질문

1. (왜) 클래스가 협력 객체를 `new`로 만들거나 `LocalDate.now()`를 직접 부르면 무엇이 어려워지나? "테스트하기 어렵다"가 왜 설계 신호인가?
2. (그림) Composition Root를 그려라. `new`는 어디에 모이고, 애플리케이션 코드는 무엇만 하나? 주입하지 않아도 되는 것은?
3. (예측) Spring 6.2.11에 A(B), B(C), C()를 A, B, C 순서로 등록하면 생성자는 어떤 순서로 불리나? 이 순서는 어떤 알고리즘의 결과인가?
4. (예측) X(Y), Y(X)를 생성자 주입으로 등록하면 언제, 어떤 예외로 실패하나? Spring Boot 2.6 이후 순환 참조의 기본 정책은?
5. (예측) 싱글턴 빈이 `thread` 범위 빈을 생성자로 받고, 스레드 두 개(alice, bob)가 차례로 쓴다. bob의 요청에서 무엇이 보이나? `ObjectProvider`와 범위 프록시로는?
6. (경계) `Clock` 빈이 없을 때 생성자 주입 판과 `getBean(Clock.class)` 판은 각각 언제 실패하나? 운영에서 이 차이가 왜 중요한가?
7. (경계) Seemann–van Deursen이 꼽는 DI 안티패턴 넷은? `UUID.randomUUID()` 직접 호출은 어디에 가깝나? Fowler와 Seemann은 Service Locator를 어떻게 다르게 평가하나?
8. (장애 진단) 청구일이 31일인 고객이 4월·6월에 청구되지 않았다. CI는 늘 초록이었다. 원인과 재현 방법은? 실험에서 2026년 1년 동안 버그 판과 고친 판은 몇 번 청구했나?
9. (연결) 정적 호출을 그대로 두고 Mockito `mockStatic`으로 시험할 수 있나? 실험에서 어떤 대가가 있었나?
10. (장애 진단) 의존 하나를 추가했더니 기동이 `BeanCurrentlyInCreationException`으로 실패한다. 근본 원인으로 흔한 것과 대처 순서는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
