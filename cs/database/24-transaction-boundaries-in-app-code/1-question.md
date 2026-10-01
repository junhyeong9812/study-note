# database/24-transaction-boundaries-in-app-code — 질문

## 질문

1. (그림) `@Transactional` 메서드를 외부에서 호출할 때 프록시가 하는 일을 순서대로 그려라. 커넥션은 언제 빌리고, DAO는 그 커넥션을 어떻게 찾나?
2. (예측) `@Transactional`이 없는 `outer()`가 같은 클래스의 `@Transactional doWork()`를 `this.doWork()`로 부른다. `doWork()` 안에서 트랜잭션은 활성인가? 에러가 나나? 세 가지 고치는 방법은?
3. (예측) `@Transactional` 메서드가 INSERT 뒤 `throw new IOException()`을 한다. 기본 설정에서 INSERT는 어떻게 되나? `IllegalStateException`이면? 어떻게 바꾸나?
4. (경계) REQUIRED 서비스 A가 REQUIRED 서비스 B를 부르고, B가 RuntimeException을 던진다. A가 그 예외를 catch하고 정상 종료하면 커밋되나? 무슨 예외가 나고 왜 그렇게 설계됐나?
5. (예측) 바깥 트랜잭션이 `UPDATE account ... WHERE id=1`을 한 뒤, `REQUIRES_NEW` 메서드가 같은 행을 UPDATE한다. 무슨 일이 일어나나? PostgreSQL이 `deadlock detected`로 풀어 주지 않는 이유는?
6. (계산) 동시 요청 스레드 20개가 각각 바깥 트랜잭션 안에서 `REQUIRES_NEW`를 한 번 부른다. 풀 교착을 피하려면 풀 크기가 최소 얼마여야 하나? Spring 문서의 권고는?
7. (경계) `@Transactional(readOnly = true)`에서 INSERT를 하면 막히나? `DataSourceTransactionManager`+pgjdbc+PostgreSQL과 `JpaTransactionManager`+Hibernate에서 각각 무엇이 일어나나?
8. (설계) 주문 커밋 뒤에 확인 메일을 보내야 한다. `afterCommit`·`@TransactionalEventListener`로 할 때의 동작과 두 가지 주의점은? 메일이 "반드시" 가야 한다면?
9. (장애 진단) 결제사 API가 느려지자 결제와 무관한 API까지 `Could not open JDBC Connection for transaction`으로 실패한다. DB에서 무엇이 보이고, 코드를 어떻게 고치나?
10. (연결) `@Async` 메서드나 `parallelStream()` 안에서 한 DB 쓰기는 바깥 `@Transactional`에 포함되나? 왜인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
