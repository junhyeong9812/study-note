# software-design/29-refactoring-to-patterns — 질문

## 질문

1. (왜) 패턴을 처음부터 설계하는 것과 분기를 방치하는 것은 각각 어떤 스멜로 끝나나? Kerievsky의 대안은?
2. (경계) Replace Type Code With Class, Replace Conditional Logic With Strategy, Introduce Null Object, Inline Singleton의 "문제"를 카탈로그 표현대로 한 줄씩 말하라. 이 중 패턴에서 멀어지는 것은?
3. (그림) 실험 A의 v0 → 1단계 → 2단계를 그려라. 각 단계에서 테스트 파일을 바꿨나? 바꾸지 않고 끝낼 수 있게 한 장치는?
4. (예측) BUSINESS 계좌 추가를 v0(라벨 `switch`를 깜빡함)과 2단계 뒤에 적용했다. diff 크기, 테스트 결과, 화면 라벨은 각각 어땠나?
5. (예측) 2단계 뒤 enum에서 BUSINESS의 `interest` 구현을 빠뜨리면 무슨 일이 생기나? 이 리팩터링이 실제로 "산" 것은 무엇인가?
6. (예측) 가변 싱글턴 `RateTable`을 쓰는 테스트 두 개를 `[defaultTest, promoTest]`와 `[promoTest, defaultTest]` 순서로 돌리면? Inline Singleton 뒤에는?
7. (예측) 할인이 없는 고객에게 null 반환판과 Null Object판은 각각 무엇을 돌려주나? NPE 메시지에 변수 이름 대신 `<local3>`가 나온 이유는?
8. (장애 진단) 몇 년 전 만든 `PaymentStrategyFactory`가 이제 구현 하나만 돌려주는데 아무도 못 지운다. 원인과 걷어내는 절차는?
9. (연결) 리팩터링 커밋이 "동작 보존"이었는지 git으로 확인하는 약한 신호 하나와, 리팩터링 커밋을 기능 커밋과 나누는 이유는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
