# database/51-object-relational-structural-mapping — 질문

## 질문

1. (왜) 객체와 관계형 테이블의 모양 차이 다섯 가지를 대고, 각각을 푸는 PoEAA 구조 패턴 이름을 짝지어라.
2. (경계) Identity Field에 대리키를 쓸 때와 자연키를 쓸 때의 위험은 각각 무엇인가? 대리키를 써도 자연키 쪽에 반드시 해 두어야 할 것은?
3. (그림) `Employment`가 `DateRange period`와 `Money salary`를 가진다. Embedded Value로 매핑한 테이블을 그려라. 같은 값 객체를 별도 테이블로 빼면 어떤 문제가 생기나?
4. (예측) JPA에서 `Order`에 `@OneToMany List<OrderLine> lines`만 달고(`mappedBy`·`@JoinColumn` 없음) 스키마를 생성한다. 어떤 테이블이 생기나? 줄 하나를 컬렉션에서 빼면 Hibernate는 어떤 SQL을 내보내나? 어떻게 고치나?
5. (비교) `Payment ← CardPayment, BankTransfer`를 Single Table, Class Table, Concrete Table로 매핑할 때 한 건 조회·다형 조회·하위 컬럼 NOT NULL·상위 타입 FK를 비교하라. JPA 명세가 구현에 지원을 요구하는 전략은?
6. (설계) Single Table 상속에서 "카드 결제면 카드 번호는 필수"를 DB가 강제하게 하라. PostgreSQL과 MySQL에서 위반 시 오류는 어떻게 보이나?
7. (장애 진단) 주문의 부가 정보를 `extra jsonb`(Serialized LOB)에 넣어 왔다. "쿠폰 C42를 쓴 주문" 검색이 수 초 걸린다. 계획에서 무엇이 보이며, 질의 모양별로 어떤 인덱스가 맞나? 장기적 대처는?
8. (장애 진단) 결제 목록 API가 하위 결제 타입이 추가될 때마다 느려진다. 상속 전략은 JOINED다. SQL 로그에서 무엇이 보이고, 원인과 대처는?
9. (연결) Class Table 상속에서 한 객체를 읽는 일을 트리와 조인으로 설명하라. N:M 연결 테이블은 어떤 그래프 표현인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
