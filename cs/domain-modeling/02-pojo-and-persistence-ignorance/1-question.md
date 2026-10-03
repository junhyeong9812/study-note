# domain-modeling/02-pojo-and-persistence-ignorance — 질문

## 질문

1. (왜) 업무 규칙을 담은 객체가 ORM 동작에 기대면 무엇이 어려워지나? "컴파일 의존"과 "실행 의미 의존"을 나눠 예를 하나씩 들어라.
2. (연결) POJO라는 이름은 누가, 언제, 무엇에 맞서 만들었나? 이 유래가 "POJO = getter·setter 있는 클래스"라는 오해를 어떻게 반박하나?
3. (경계) Jakarta Persistence와 Hibernate 6.6이 엔티티 클래스에 요구하는 것(생성자·final·접근자)은 각각 무엇인가? 둘이 다른 지점은?
4. (예측) Hibernate 6.6.29에서 `@ManyToOne(fetch = LAZY)`로 얻은 `customer`가 아직 초기화되지 않았다. `customer.getClass()`의 이름, 필드 `customer.id`, `customer.getId()`는 각각 무엇이 나오나? 같은 id의 `new Customer(1L, …)`와 비교할 때 `getClass()` 비교 equals, `instanceof` + 필드 접근, `instanceof` + getter 중 어느 것이 `true`인가?
5. (예측) 트랜잭션 안에서 `find(PurchaseOrder, 10)` 뒤 `approve()`만 부르고 `save`·`merge`는 부르지 않았다. 커밋 뒤 DB의 `status`는? 그 이유가 되는 동작의 이름과 원리는?
6. (장애 진단) 같은 도메인 메서드가 서비스 안에서는 되는데 이벤트 리스너에서는 `could not initialize proxy - no Session`으로 실패한다. 원인과 대처 세 가지는?
7. (판단) 도메인 = JPA 엔티티, `orm.xml` 매핑, 도메인·영속 모델 분리 — 세 선택의 비용과 맞는 경우는? 셋에 공통으로 지켜야 할 기준은?
8. (장애 진단) 불변 객체로 만들겠다며 엔티티를 `final`로 바꾸고 인자 없는 생성자를 지웠다. 배포 뒤 무슨 일이 생길 수 있나? Hibernate 6.6에서 보이는 형태와 대처는?
9. (경계) 실험에서 `new`로 만든 객체로 규칙을 검사하는 시간과 `SessionFactory`를 띄워 같은 검사를 하는 시간은 어느 정도 차이가 났나? 이 수치를 일반화할 때 주의할 점은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
