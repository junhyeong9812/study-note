# testing/03-test-doubles — 질문

## 질문

1. (왜) 테스트 더블이 없으면 "결제 실패면 주문을 취소한다" 같은 동작을 왜 시험하기 어려운가? 더블이 대신하는 것은 SUT인가 DOC인가?
2. (그림) 간접 입력과 간접 출력을 SUT·DOC·테스트 사이의 화살표로 그려라. Stub·Spy·Mock은 각각 어느 화살표에 끼어드나?
3. (경계) Dummy·Fake·Stub·Spy·Mock을 "무엇을 하나" 기준으로 한 줄씩 구분하라. Mockito의 `spy()`는 Meszaros의 Spy와 무엇이 다른가?
4. (경계) "mock"이라는 말을 Meszaros·Fowler, Khorikov, SWE@G, Mockito가 각각 어떻게 쓰나? Khorikov가 stub과의 상호작용을 단언하지 말라고 하는 이유는?
5. (예측) 서비스가 "없는 계좌면 저장소가 -1을 준다", "최근 이체는 오래된 것이 먼저 온다"고 잘못 믿고 있다. 같은 시나리오 테스트를 Mockito Stub, 계약 테스트를 통과한 Fake, H2 실제 구현으로 돌리면 각각 어떻게 되나?
6. (예측) 아무것도 stub하지 않은 Mockito mock에서 `long count()`, `List<String> list()`, `Optional<String> opt()`, `Object obj()`를 부르면 무엇이 나오나? 원시 `long` 잔액 조회를 stub하지 않으면 어떤 조용한 버그가 생기나?
7. (연결) 계약 테스트란 무엇이고, Fake를 믿을 수 있으려면 왜 필요한가? 누가 Fake를 만들고 유지하라고 SWE@G는 권하나?
8. (장애 진단) 리팩터링 뒤 여러 테스트가 `UnnecessaryStubbingException`으로 실패한다. 무엇을 뜻하며, `lenient()`로 덮기 전에 무엇을 확인하나?
9. (장애 진단) 단위 테스트는 수백 개가 초록인데 배포 직후 저장소 조회 경로에서 `NoSuchElementException`이 난다. 원인 후보와 재발 방지책을 대라.
10. (연결) 더블을 고르는 순서(실제 구현 → Fake → Stub → Mock)를 설명하고, "Only Mock Types That You Own"이 무엇을 막는지 말하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
