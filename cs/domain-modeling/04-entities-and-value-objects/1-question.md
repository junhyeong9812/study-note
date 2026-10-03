# domain-modeling/04-entities-and-value-objects — 질문

## 질문

1. (왜) 엔티티와 값 객체는 "같음"을 각각 무엇으로 판단하나? 같은 개념(예: 주소)이 어떤 시스템에서는 값, 다른 시스템에서는 엔티티가 되는 이유는?
2. (그림) Evans 『DDD Reference』가 값 객체에 요구하는 성질 세 가지를 대고, `Money`를 가변 클래스로 두었을 때 생기는 별칭 버그를 그림으로 그려라.
3. (예측) `equals`/`hashCode`가 없는 `MoneyNoEq(1000, "KRW")`를 `HashSet`에 두 번 넣으면 `size()`와 `contains(new MoneyNoEq(1000, "KRW"))`는? 같은 실험을 record로 하면?
4. (예측) 생성 ID(`@GeneratedValue`)로 `equals`/`hashCode`를 만든 엔티티를 저장 전에 `HashSet`에 넣고, persist·커밋한 뒤 `contains`·`remove`·`size`는 각각 무엇을 돌려주나(Hibernate 6.6)? 왜 그런가?
5. (경계) Hibernate 6.6 User Guide가 `equals`/`hashCode` 구현이 "절대적"이라고 부르는 경우는? 생성 ID 엔티티에 대해 가이드가 제시한 대안 두 가지와 각 대가는?
6. (장애 진단) 고객 한 명의 주소를 바꿨는데 다른 고객의 주소도 DB에서 바뀌었다. 매핑은 `@Embedded Address`(가변 클래스)다. 원인과 JPA 3.1 명세의 입장, 대처는?
7. (장애 진단) 해외 결제가 섞인 정산 합계가 맞지 않는다. 금액 필드가 `long amount` 하나뿐이다. 왜 컴파일·테스트가 막지 못했나? 값 객체로 어떻게 막나?
8. (연결) 금액 값 객체에 `BigDecimal`을 담은 record를 쓰면 `1.0`원과 `1.00`원은 같은가? 통화별 소수 자릿수와 묶어 생성자에서 무엇을 해야 하나?
9. (경계) 주문의 배송지는 값으로 복사해야 하나, 주소록 항목을 참조해야 하나? 각각을 택했을 때 어떤 요구에 답할 수 없게 되나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
