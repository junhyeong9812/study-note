# software-design/39-component-principles — 질문

## 질문

1. (왜) 클래스 설계가 좋아도 컴포넌트(배포 단위) 묶음이 나쁘면 무엇이 안 되나? 응집 3원칙과 결합 3원칙은 각각 무엇을 정하나?
2. (경계) REP·CCP·CRP를 Martin "Granularity"의 정의로 말하라. 셋이 서로 당기는 관계를 한 예로 설명하라.
3. (그림) SDP와 SAP를 그림으로 그려라. Martin 1994 논문의 Ca·Ce·I·A·D·Dn 정의는?
4. (예측) 실험 A acyclic판에서 `entities`·`usecases`·`db`·`web`의 I는 각각 얼마였나? 이 순서는 SDP와 맞나?
5. (예측) `Order.describe()`가 `comp.web.WebFormat`을 직접 쓰게 바꾸면, 컴포넌트를 의존 순서대로 하나씩 빌드할 때 무슨 일이 생기나? SCC는 어떻게 바뀌나? 프로그램 출력은?
6. (경계) 실험 A의 SCC는 하나였는데 ArchUnit은 순환을 4개 보고했다. 왜 다른가? 끊을 곳은 어떻게 찾나?
7. (예측) cyclic판에서 `entities`의 I와 `web`의 Ca는 어떻게 바뀌었나? 이것은 어떤 원칙 위반인가?
8. (경계) acyclic판의 `entities`는 I=0인데 Dn=0.5였다. 이것은 꼭 나쁜 설계인가? 지표를 어떻게 다뤄야 하나?
9. (적용) Martin이 제시한 순환 끊기 두 방법은? 실험의 acyclic판은 어느 쪽인가?
10. (장애 진단) `entities` 버그 하나를 고쳐 릴리스하려는데 네 모듈을 함께 배포해야 한다. 어떤 신호로 확인하고 어떻게 고치나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
