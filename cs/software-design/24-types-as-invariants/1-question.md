# software-design/24-types-as-invariants — 질문

## 질문

1. (왜) 검증을 했는데도 같은 검증이 여러 곳에 반복되는 이유는 무엇인가? "parse, don't validate"에서 parse와 validate의 차이를 반환 타입으로 설명하라.
2. (예측) `findOrder(Long userId, Long orderId)`에 인자를 뒤바꿔 넣으면? `UserId`·`OrderId` record를 쓰면 무엇이 나오나?
3. (예측) 실험 C에서 String을 들고 다니는 판에 검증 없는 CSV 경로로 `"   "`를 넣으면 DB에 무엇이 남나? `save(Email)`만 있는 판에서 같은 경로를 쓰면?
4. (경계) "불법 상태를 표현할 수 없게"란 무엇인가? `status` + nullable `paidAt` 설계와 `sealed Order = Pending | Paid(paidAt)` 설계를 곱 타입·합 타입으로 비교하라.
5. (예측) `status=PAID`, `paidAt=null` 행을 두 설계로 처리하면 각각 어디서 무엇이 터지나? `sealed`에 `Refunded`를 추가하고 `switch`를 안 고치면?
6. (경계) 자바에서 스마트 생성자를 만드는 방법은? `record`로 생성자를 숨길 수 없는 이유와 대안은?
7. (연결) 타입 상태(typestate)란? 실험 D에서 `sendPasswordReset(UnverifiedEmail)`은 어떻게 되고, 이 방식의 한계는?
8. (경계) 전용 타입이 손해인 경우와 판단 기준은?
9. (장애 진단) 새벽 정산 배치가 `NullPointerException: instant ... LocalDate.ofInstant`로 멈췄다. 원인 데이터는 어떻게 찾고, 재발을 코드·DB 양쪽에서 어떻게 막나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
