# database/23-orm-and-n-plus-one — 질문

## 질문

1. (왜) 영속성 컨텍스트 안에는 어떤 자료구조가 들어 있나? 같은 트랜잭션에서 같은 id를 두 번 `find`하면 SQL이 몇 번 나가고, 무엇이 돌아오나?
2. (예측) managed 엔티티의 필드를 바꾼 뒤 save()를 부르지 않고 다른 JPQL 조회를 실행했다. UPDATE는 언제 나가나? 조회 대상 테이블이 전혀 다른 테이블이면?
3. (계산) 주문 100건, 주문마다 항목 5개. `@OneToMany(fetch=LAZY)` 항목을 반복문에서 만지면 쿼리는 몇 번인가? `default_batch_fetch_size=30`이면? fetch join이면?
4. (경계) `@ManyToOne`의 fetch 기본값은? 그것을 EAGER로 두면 JPQL `from OrderLine`에서 N+1이 사라지나? 추가 쿼리 수는 무엇에 비례하나?
5. (예측) `select o from Order o join fetch o.lines` 에 `setMaxResults(20)`을 붙였다. SQL에 LIMIT이 붙나? 무슨 경고가 나고, 어떻게 고치나?
6. (장애 진단) 컨트롤러에서 JSON 직렬화 중 `LazyInitializationException: ... could not initialize proxy - no Session`이 난다. 원인과 대처는? OSIV를 켜서 없애면 무엇을 대가로 치르나?
7. (장애 진단) 조회 API인데 SQL 로그에 `update member set name=? where id=?`가 보이고, 저장된 이름이 마스킹된 값으로 바뀌었다. 무슨 일이 일어났고, 어떻게 막나?
8. (연결) N+1은 왜 슬로 쿼리 로그로 잡히지 않나? 운영과 테스트에서 각각 무엇으로 잡나?
9. (경계) 같은 트랜잭션에서 JPQL 벌크 `update Order o set o.status = 'X'`를 실행한 뒤 `find(Order, 1)`로 읽었다. 무엇이 보일 수 있고, 왜인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
