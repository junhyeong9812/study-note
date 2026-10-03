# domain-modeling/08-domain-services-and-policies — 질문

## 질문

1. (왜) "계좌 A에서 B로 이체"를 `Account`의 메서드로 넣으면 무엇이 어색한가? Evans 『DDD Reference』는 이런 연산을 어떻게 모델에 넣으라고 하나(인터페이스·계약·이름)?
2. (구분) 애플리케이션 서비스·도메인 서비스·인프라 서비스가 각각 맡는 일을 이체 예로 나눠라. Fowler "AnemicDomainModel"이 인용한 Evans의 애플리케이션 계층 원칙은?
3. (예측) "잔액 ≥ 0" 검사가 `TransferService`에만 있고 `Account`는 setter만 연다. 수수료 서비스·관리자 조정 서비스로 잔액 100에서 150을 빼면 결과는? 규칙을 `Account.withdraw`로 옮기면? (실험 A)
4. (경계) Evans가 든 좋은 서비스의 세 특징은? 도메인 서비스가 상태를 가지면 어떤 문제가 생길 수 있나?
5. (예측) 환불 규칙이 `RefundService`와 `NoticeService` 두 곳에서 `if (type == …)`로 갈린다. 새 유형 `SUB`를 추가하면서 `NoticeService`를 빠뜨리면 무슨 일이 일어나나? 같은 누락을 `RefundPolicy` 인터페이스 방식에서 하면? (실험 B)
6. (반대 측면) 실험 B에서 diff 크기는 어느 쪽이 작았나? 이 결과가 "정책 객체는 언제나 이득"이라는 주장에 주는 반례는? 언제 정책 객체로 꺼내나?
7. (장애 진단) 새 상품 유형 주문이 500 에러를 낸다. 스택에 `NullPointerException`이 정책 조회 직후에 찍힌다. 원인과 재발 방지 테스트는?
8. (장애 진단) 이체 규칙 단위 테스트가 DB·HTTP 없이 돌지 않고, 도메인 패키지가 `RestTemplate`과 `@Transactional`을 import한다. 무엇이 섞였고 어떻게 나누나?
9. (연결) 이체는 계좌 애그리거트 두 개를 고친다. 05의 Vernon 기본값과 어떻게 충돌하며, 어떤 판단을 기록해야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
