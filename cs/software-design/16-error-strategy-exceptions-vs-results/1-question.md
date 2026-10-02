# software-design/16-error-strategy-exceptions-vs-results — 질문

## 질문

1. (왜) 실패를 세 종류로 나누면 무엇과 무엇인가? 각각 누가 대응하고 어떤 수단이 어울리나?
2. (그림) Railway 비유로 `parseAmount → loadAccount → withdraw` 체인을 그려라. 금액이 `abc`일 때 실행되는 함수는?
3. (예측) Spring Framework 6.2에서 `@Transactional` 메서드가 쓰기 후 checked 예외를 던지면 쓰기는 남나? `rollbackFor`를 달면? 쓰기 후 `Result.err`를 반환하면?
4. (예측) 바깥 `@Transactional` 메서드가 안쪽 `@Transactional` 빈이 던진 `RuntimeException`을 잡고 정상 종료했다. 결과는?
5. (경계) sealed `DomainError`에 새 실패를 추가하면 `default` 없는 `switch` 번역은 어떻게 되나? 예외 계층이라면? 이 장점의 반대 비용은?
6. (예측) 요청 1000건 중 30%가 잔액 부족이고, 클라이언트는 5xx만 최대 3번 재시도한다. 잔액 부족을 409로 줄 때와 500으로 줄 때 서버가 받는 호출 수는?
7. (경계) 결과 타입을 쓰면서 `get()`을 부르면 무엇이 되나? Wlaschin이 Result를 쓰지 말라고 하는 경우를 세 가지 들라.
8. (연결) Special Case(Null Object)는 언제 맞고 언제 실패를 숨기나?
9. (장애 진단) "잔액 부족" 응답을 받은 송금 요청인데 원장에 출금 행이 남았다. 의심할 두 원인과 확인 방법은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
