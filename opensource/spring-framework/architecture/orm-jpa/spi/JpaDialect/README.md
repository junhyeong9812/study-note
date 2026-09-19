# JpaDialect

상위: [Spring JPA 연동](../../README.md) / [spi](../README.md)

JPA 스펙만으로는 할 수 없는 두 가지를 벤더에게 맡기는 인터페이스다. 하나는 격리 수준 같은 트랜잭션 세부 설정이고, 다른 하나는 JPA가 쓰는 JDBC 커넥션을 꺼내 오는 일이다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `JpaDialect.java` L84-L94 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/JpaDialect.java#L84-L94))

```java
// JpaDialect.java L84-L94
@Nullable Object beginTransaction(EntityManager entityManager, TransactionDefinition definition)
        throws PersistenceException, SQLException, TransactionException;

```

`spring-orm` / `org.springframework.orm.jpa` / `JpaDialect.java` L153-L158 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/JpaDialect.java#L153-L158))

```java
// JpaDialect.java L153-L158
@Nullable ConnectionHandle getJdbcConnection(EntityManager entityManager, boolean readOnly)
        throws PersistenceException, SQLException;

```

## 흐름에서 불리는 자리

```text
 JpaTransactionManager.doBegin
   L411 beginTransaction(em, 정의)      트랜잭션 시작 + 격리/읽기 전용 적용
   L423 getJdbcConnection(em, 읽기 전용) 같은 커넥션을 JDBC 쪽에 노출
 doCommit / doRollback
   translateExceptionIfPossible(ex)     벤더 예외 번역
 정리 단계
   cleanupTransaction(transactionData)  격리 수준 등 복원
```

- [JpaTransactionManager.doBegin](../../03_JpaTransactionManager.doBegin/README.md)

## 구현 계층

```text
 JpaDialect (PersistenceExceptionTranslator 도 함께 구현한다)
   +-- DefaultJpaDialect          스펙 범위만. 격리 수준 지정은 지원하지 않는다
         +-- HibernateJpaDialect  커넥션 노출, 격리 수준, 플러시 모드 제어
         +-- EclipseLinkJpaDialect
```

## 결과가 쓰이는 곳

```text
 beginTransaction 이 돌려준 transactionData
      --> 트랜잭션 객체에 보관됐다가 cleanupTransaction 으로 되돌아간다
      --> 격리 수준을 바꿨다면 여기서 원래대로 복원한다

 getJdbcConnection
      --> null 이면 JPA 트랜잭션이 JDBC 로 노출되지 않는다
      --> DefaultJpaDialect 는 null 을 돌려주므로, 커넥션 공유가 필요하면
          벤더 방언을 써야 한다

 격리 수준
      --> DefaultJpaDialect 에서 ISOLATION_DEFAULT 가 아닌 값을 주면 예외가 난다
      --> "@Transactional(isolation = ...) 이 무시된다"는 오해는 대개 방언 문제다
```
