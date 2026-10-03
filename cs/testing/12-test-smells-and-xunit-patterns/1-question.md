# testing/12-test-smells-and-xunit-patterns — 질문

## 질문

1. (왜) 테스트 스멜이 "실패했을 때" 비용으로 돌아온다는 말은 무슨 뜻인가? Meszaros가 스멜을 나누는 세 갈래(코드·행동·프로젝트)를 예와 함께 말하라.
2. (경계) Obscure Test, Mystery Guest, General Fixture의 관계를 설명하라. 테스트가 `fixtures/orders.json`을 읽는 것은 어느 것에 해당하고, 왜 Fragile Test로도 이어지나?
3. (예측) 세금 결함(9%)과 통화 결함(`"krw"`)이 있는 영수증에, 메시지 없는 `assertEquals` 세 줄 + `assertTrue(r.currency().equals("KRW"))`를 쓴 테스트는 어떤 메시지로 실패하고, 결함 몇 개를 보고하나? `assertAll`로 바꾸면?
4. (예측) `if (found != null) { assertEquals(11_000, found.total()); }` 테스트는, `find`가 `null`을 돌려주는 결함이 있을 때 어떻게 되나? 고친 테스트는?
5. (예측) 배송비 규칙에 결함이 두 입력(0원, 30,000원)에서 있다. 다섯 입력을 `for`로 도는 테스트와 `@ParameterizedTest @CsvSource` 테스트는 각각 무엇을 보고하나?
6. (경계) Custom Assertion이 푸는 스멜 세 가지는? 실험의 `hasVatOf(10)`이 합계 결함을 따로 보고하지 않은 이유는?
7. (연결) Humble Object 패턴의 질문과 답을 말하고, 스케줄러 메서드 안에 쿠폰 만료 규칙이 있는 코드를 어떻게 나누는지 그려라. software-design의 함수형 코어·명령형 셸과 무엇이 같은가?
8. (적용) Test-Specific Subclass와 Delegated Setup은 각각 언제 쓰나? 레거시 클래스가 `Instant.now()`를 직접 부를 때 Test-Specific Subclass로 어떻게 시간을 고정하나? 의존 주입이 가능하면 무엇이 낫나?
9. (장애 진단) CI 실패를 맡은 사람이 테스트를 읽고도 무엇을 검증하는지 몰라 30분을 쓴다. 어떤 스멜을 의심하고 어떤 순서로 고치나?
10. (연결) JUnit Jupiter 5.13의 기본 테스트 메서드 실행 순서는 문서에서 어떻게 설명되나? 이것이 공유 픽스처를 쓰는 테스트에 주는 경고는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
