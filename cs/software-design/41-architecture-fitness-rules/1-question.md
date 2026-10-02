# software-design/41-architecture-fitness-rules — 질문

## 질문

1. (왜) 가시성(package-private·JPMS)이 있는데도 규칙 테스트가 따로 필요한 이유는? 가시성으로 못 막는 규칙 세 가지를 들어라.
2. (그림) ArchUnit 같은 검사기가 코드에서 위반 목록을 만들기까지의 흐름을 그려라. ArchUnit은 무엇을 읽나?
3. (예측) web → service → repository → domain 앱에 "도메인이 웹 컨트롤러의 static 필드를 읽는" 간선 하나를 넣었다. `slices().matching("com.shop.(*)..").should().beFreeOfCycles()`는 순환을 몇 개 보고했나? 왜 하나가 아닌가?
4. (예측) 위반 3건이 있는 코드에 `FreezingArchRule`을 처음 켜면? 이어서 새 위반 2건을 넣으면? 기존 위반을 고치면 저장소는?
5. (경계) 도메인이 웹 클래스의 `public static final int` 상수를 읽게 바꿨다. 소스에 import가 있는데 ArchUnit 계층·순환 규칙 결과는? 이유를 바이트코드로 설명하라.
6. (경계) JS 모듈 `orders ↔ billing` 순환이 있는 프로그램을 실행하면 어떻게 되나? 그것이 규칙 검사가 필요한 이유와 어떻게 이어지나?
7. (연결) 순환 제거 기법 다섯 가지를 들고, 실험에서 Java·JS 순환을 각각 어떤 기법으로 끊었는지 말하라.
8. (장애 진단) 새 위반을 넣은 PR이 CI를 통과했다. 동결 규칙을 쓰는 프로젝트라면 먼저 무엇을 확인하나?
9. (연결) 순환 검사와 강연결요소(SCC)는 어떤 관계인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
