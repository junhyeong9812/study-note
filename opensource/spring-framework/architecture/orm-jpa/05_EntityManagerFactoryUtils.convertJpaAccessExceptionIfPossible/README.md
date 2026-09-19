# EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible

상위: [Spring JPA 연동](../README.md)

JPA 스펙의 예외를 스프링의 `DataAccessException` 계층으로 옮기는 표다. 벤더가 달라도 호출 코드가 같은 예외를 잡을 수 있게 하는 것이 목적이다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `EntityManagerFactoryUtils.java` L477-L525 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/EntityManagerFactoryUtils.java#L477-L525))

```java
// EntityManagerFactoryUtils.java L477-L525
public static @Nullable DataAccessException convertJpaAccessExceptionIfPossible(RuntimeException ex) {
    // Following the JPA specification, a persistence provider can also
    // throw these two exceptions, besides PersistenceException.
    if (ex instanceof IllegalStateException) {
        return new InvalidDataAccessApiUsageException(ex.getMessage(), ex);
    }
    if (ex instanceof IllegalArgumentException) {
        return new InvalidDataAccessApiUsageException(ex.getMessage(), ex);
    }

    // Check for well-known PersistenceException subclasses.
    if (ex instanceof EntityNotFoundException entityNotFoundException) {
        return new JpaObjectRetrievalFailureException(entityNotFoundException);
    }
    if (ex instanceof NoResultException) {
        return new EmptyResultDataAccessException(ex.getMessage(), 1, ex);
    }
    if (ex instanceof NonUniqueResultException) {
        return new IncorrectResultSizeDataAccessException(ex.getMessage(), 1, ex);
    }
    if (ex instanceof QueryTimeoutException) {
        return new org.springframework.dao.QueryTimeoutException(ex.getMessage(), ex);
    }
    if (ex instanceof LockTimeoutException) {
        return new CannotAcquireLockException(ex.getMessage(), ex);
    }
    if (ex instanceof PessimisticLockException) {
        return new PessimisticLockingFailureException(ex.getMessage(), ex);
    }
    if (ex instanceof OptimisticLockException optimisticLockException) {
        return new JpaOptimisticLockingFailureException(optimisticLockException);
    }
    if (ex instanceof EntityExistsException) {
        return new DataIntegrityViolationException(ex.getMessage(), ex);
    }
    if (ex instanceof TransactionRequiredException) {
        return new InvalidDataAccessApiUsageException(ex.getMessage(), ex);
    }

    // If we have another kind of PersistenceException, throw it.
    if (ex instanceof PersistenceException) {
        return new JpaSystemException(ex);
    }

    // If we get here, we have an exception that resulted from user code,
    // rather than the persistence provider, so we return null to indicate
    // that translation should not occur.
    return null;
}
```

## 동작 흐름

```text
 convertJpaAccessExceptionIfPossible(ex)
 |
 +-- [1] 스펙이 허용하는 비-PersistenceException 두 종류
 |      L480 IllegalStateException    --> InvalidDataAccessApiUsageException
 |      L483 IllegalArgumentException --> InvalidDataAccessApiUsageException
 |
 +-- [2] 잘 알려진 PersistenceException 하위 타입
 |      L488 EntityNotFoundException    --> JpaObjectRetrievalFailureException
 |      L491 NoResultException          --> EmptyResultDataAccessException
 |      L494 NonUniqueResultException   --> IncorrectResultSizeDataAccessException
 |      L497 QueryTimeoutException      --> (스프링) QueryTimeoutException
 |      L500 LockTimeoutException       --> CannotAcquireLockException
 |      L503 PessimisticLockException   --> PessimisticLockingFailureException
 |      L506 OptimisticLockException    --> JpaOptimisticLockingFailureException
 |      L509 EntityExistsException      --> DataIntegrityViolationException
 |      L512 TransactionRequiredException --> InvalidDataAccessApiUsageException
 |
 +-- [3] L517 그 밖의 PersistenceException --> JpaSystemException
 |
 +-- [4] L524 어느 쪽도 아니면 null
        = 사용자 코드에서 난 예외라는 뜻. 번역하지 않고 그대로 올려 보낸다
```

```text
 null 을 돌려주는 설계

 번역기가 "모르겠다"고 답할 수 있어야
   사용자 코드의 예외를 데이터 접근 예외로 오인해 감싸지 않는다
 PersistenceExceptionTranslator 인터페이스가 같은 규약을 쓴다
```

## 결과가 쓰이는 곳

```text
 번역된 DataAccessException
      --> 모두 런타임 예외라 체크 예외 처리가 강제되지 않는다
      --> @Transactional 의 기본 롤백 규칙(언체크 예외)에 그대로 걸린다

 누가 이 메서드를 부르는가
      --> JpaTransactionManager 가 커밋/롤백 실패를 번역할 때
      --> PersistenceExceptionTranslationPostProcessor 가 붙인 @Repository 프록시가
          리포지터리 메서드의 예외를 번역할 때

 낙관적 잠금
      --> OptimisticLockException 이 JpaOptimisticLockingFailureException 이 된다
      --> 그 상위가 ObjectOptimisticLockingFailureException 이라
          JPA 와 하이버네이트 경로를 같은 타입으로 잡을 수 있다

 NoResultException 이 EmptyResultDataAccessException 이 되는 점
      --> getSingleResult() 가 빈 결과에서 던지는 예외다
      --> 스프링 쪽 타입으로 바뀌므로 JDBC 경로와 같은 예외로 다룰 수 있다
```

JDBC 쪽의 같은 역할은 [SQLExceptionTranslator](../../jdbc/spi/SQLExceptionTranslator/README.md)가 맡는다. 예외 계층 자체는 두 경로가 공유한다.
