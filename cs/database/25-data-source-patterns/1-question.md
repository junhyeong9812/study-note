# database/25-data-source-patterns — 질문

## 질문

1. (왜) SQL을 서비스 메서드 곳곳에 섞어 쓰면 어떤 문제가 생기나? 세 가지를 대라.
2. (구분) Table Data Gateway, Row Data Gateway, Active Record, Data Mapper를 "SQL을 아는 자 / 인스턴스 하나가 다루는 범위 / 도메인 로직의 위치"로 표로 비교하라.
3. (예측) 환불 규칙이 복잡한 `Order`를 Active Record로 만들었다. 규칙 단위 테스트를 쓰려 할 때 무엇이 걸리나? Fowler는 행 객체가 DB에 묶이는 문제를 어떻게 설명하나?
4. (연결) JPA/Hibernate는 PoEAA의 어떤 패턴들의 조합인가? `@Entity`·`@Column`은 그중 무엇에 해당하나?
5. (경계) Repository와 Data Mapper는 무엇이 다른가? Repository가 만드는 "한 방향 의존"은 무엇에서 무엇으로인가?
6. (구현) 조건 `status = 'PAID' AND (amount > 1000 OR vip = true)`를 Query Object로 표현하는 트리를 그리고, SQL과 바인딩 값을 만드는 순회를 설명하라. 컬럼 이름과 값은 각각 어떻게 넣어야 하나?
7. (장애 진단) Spring Data 리포지토리에 `findByStatusAndCreatedAtBetweenAndCustomerGradeInOrAmountGreaterThan...` 같은 메서드가 수십 개다. 원인과 대처는?
8. (설계) Data Mapper를 쓰는데 도메인 패키지에 `jakarta.persistence.*` import가 가득하다. 무엇이 문제이고, 선택지 세 가지와 각각의 비용은?
9. (판단) 단순 CRUD 관리자 화면과 복잡한 정산 도메인이 한 시스템에 있다. 각각에 어떤 패턴을 고르고, 그 기준은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
