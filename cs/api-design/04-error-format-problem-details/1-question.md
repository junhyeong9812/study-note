# api-design/04-error-format-problem-details — 질문

## 질문

1. (왜) 상태 코드를 제대로 골랐는데도 에러 본문 형식을 표준화해야 하는 이유는? 형식이 없을 때 생기는 두 가지 문제는?
2. (그림) RFC 9457 Problem Details 응답 하나를 그려라(상태 줄·`Content-Type`·다섯 멤버·확장 멤버 하나). 각 멤버 옆에 "기계용인가 사람용인가"를 적어라.
3. (경계) `type`·`title`·`detail`·`status`에 대해 RFC 9457이 소비자와 생성자에게 거는 규칙(MUST/SHOULD)을 말하라. `type`이 없으면? 멤버 값의 타입이 틀리면? 모르는 확장 멤버는?
4. (경계) 새 문제 유형을 정의할 때 반드시 문서화할 세 가지는? 어떤 경우엔 문제 유형을 새로 만들지 말라고 하나?
5. (예측) Spring Boot 4.1.1 기본 설정에서 도메인 오류는 `ProblemDetail`로 직접 처리하고, `/orders/abc`(경로 변수 형식 오류)와 처리 안 된 예외 `/boom`은 그대로 둔다. 세 응답의 `Content-Type`과 본문 키는? `spring.mvc.problemdetails.enabled=true`를 켜면 무엇이 바뀌고 무엇이 그대로인가?
6. (예측) 같은 앱에 `--server.error.include-stacktrace=always`를 주면 `/boom` 응답에 트레이스가 나오나? `--spring.web.error.include-stacktrace=always`면? 왜 다른가? 나온다면 무엇이 노출되나?
7. (연결) 여러 필드의 검증 오류를 한 응답에 어떻게 담나? 서로 다른 유형의 문제가 동시에 생기면 RFC 9457은 무엇을 권하나?
8. (연결) RFC 9457, Google AIP-193, Stripe의 에러 형식에서 "기계용 식별자", "사람용 설명", "어느 입력이"에 해당하는 필드를 각각 대응시켜라.
9. (장애 진단) 앱의 공통 에러 처리기가 일부 오류에서 `Unexpected character '<'`로 죽고, 다른 일부에서는 `type`이 null이다. 원인 후보와 서버·클라이언트 대처는?
10. (장애 진단) `detail`이 "Your current balance is 30, but that costs 50."인 응답에서 클라이언트가 숫자를 뽑아 충전 금액을 계산한다. 무엇이 문제이고, 서버는 어떻게 바꿔야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
