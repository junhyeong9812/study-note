# domain-modeling/07-domain-logic-patterns-and-service-layer — 질문

## 질문

1. (경계) Transaction Script·Table Module·Domain Model은 업무 로직을 각각 무엇 단위로 묶나? PoEAA 카탈로그의 한 줄 정의로 답하라.
2. (왜) Fowler는 왜 "도메인 로직이 이만큼 복잡하면 Domain Model"처럼 기준선을 숫자로 주지 않나? 규칙이 늘 때 Transaction Script와 Domain Model은 각각 어떻게 커지나?
3. (예측) 주문 생성·줄 추가·수량 변경 세 유스케이스에 "한도 100만 원" 규칙이 있다. "VIP 한도 200만 원"을 추가하면 Transaction Script 구현과 Domain Model 구현은 각각 몇 파일이 바뀌나? 반대로 불변식 없는 "공지 제목 수정"을 두 방식으로 짜면 코드 양은?
4. (경계) Stafford가 말한 domain logic과 application logic은 무엇이 다른가? Service Layer의 domain facade 방식과 operation script 방식은?
5. (판단) Stafford는 Service Layer가 언제 필요하고 언제 아마 필요 없다고 보나? 이 기준에 비추면 "웹 UI 하나뿐인 사내 도구"는?
6. (예측) 이체를 `debit` → `credit` → `insert transfer_log(request_id)`로 처리하고 `request_id`가 기본 키다. 같은 요청 ID로 두 번 보낼 때, 리포지토리 호출마다 자동 커밋이면 최종 잔액은? 한 트랜잭션이면? (시작 `A=1000 B=0`, 금액 100)
7. (연결) Spring Data JPA 리포지토리 메서드의 기본 트랜잭션 설정은 무엇이고, 여러 리포지토리에 걸친 경계는 어디서 정하라고 문서가 말하나? 바깥 `@Transactional`이 있으면 리포지토리 설정은 어떻게 되나?
8. (예측) 작업 5개짜리 큐를 처리하는 루프에 `if (debug) log("next=" + jobs.poll())`이 있다. debug를 켜면 몇 개가 처리되나? 무슨 원칙 위반이고 어떻게 고치나?
9. (장애 진단) 웹에서는 막히는 작업이 메시지 소비자 경로로는 실행된다. 권한 검사는 어디에 있었을 가능성이 크고, Spring Security 문서는 메서드 보안을 쓸 때 무엇을 경고하나?
10. (판단) 규칙이 지금은 적지만 늘어날 것 같다. 처음부터 Domain Model로 갈지, 스크립트로 시작할지 정하는 실무 기준을 제시하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
