# EntityManagerFactoryUtils.doGetTransactionalEntityManager

상위: [JpaTransactionManager.doBegin](../README.md)

"지금 이 스레드의 트랜잭션에 묶인 `EntityManager`가 있는가"를 답하는 조회 지점이다. 공유 프록시가 호출마다 여기를 지나고, 트랜잭션 매니저가 만들어 둔 바인딩이 여기서 발견된다.

## 실제 코드

이미 묶인 것이 있는지 먼저 본다.

`spring-orm` / `org.springframework.orm.jpa` / `EntityManagerFactoryUtils.java` L201-L256 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/EntityManagerFactoryUtils.java#L201-L256))

```java
// EntityManagerFactoryUtils.java L201-L256
public static @Nullable EntityManager doGetTransactionalEntityManager(
        EntityManagerFactory emf, @Nullable Map<?, ?> properties, boolean synchronizedWithTransaction)
        throws PersistenceException {

    Assert.notNull(emf, "No EntityManagerFactory specified");

    EntityManagerHolder emHolder = (EntityManagerHolder) TransactionSynchronizationManager.getResource(emf);
    if (emHolder != null && emHolder.hasEntityManager()) {
        if (synchronizedWithTransaction) {
            if (!emHolder.isSynchronizedWithTransaction()) {
                if (TransactionSynchronizationManager.isActualTransactionActive()) {
                    // Try to explicitly synchronize the EntityManager itself
                    // with an ongoing JTA transaction, if any.
                    try {
                        emHolder.getEntityManager().joinTransaction();
                    }
                    catch (TransactionRequiredException ex) {
                        logger.debug("Could not join transaction because none was actually active", ex);
                    }
                }
                if (TransactionSynchronizationManager.isSynchronizationActive()) {
                    Object transactionData = prepareTransaction(emHolder.getEntityManager(), emf);
                    TransactionSynchronizationManager.registerSynchronization(
                            new TransactionalEntityManagerSynchronization(emHolder, emf, transactionData, false));
                    emHolder.setSynchronizedWithTransaction(true);
                }
            }
            // Use holder's reference count to track synchronizedWithTransaction access.
            // isOpen() check used below to find out about it.
            emHolder.requested();
            return emHolder.getEntityManager();
        }
        else {
            // unsynchronized EntityManager demanded
            if (emHolder.isTransactionActive() && !emHolder.isOpen()) {
                if (!TransactionSynchronizationManager.isSynchronizationActive()) {
                    return null;
                }
                // EntityManagerHolder with an active transaction coming from JpaTransactionManager,
                // with no synchronized EntityManager having been requested by application code before.
                // Unbind in order to register a new unsynchronized EntityManager instead.
                TransactionSynchronizationManager.unbindResource(emf);
                emHolder = null;
            }
            else {
                // Either a previously bound unsynchronized EntityManager, or the application
                // has requested a synchronized EntityManager before and therefore upgraded
                // this transaction's EntityManager to synchronized before.
                return emHolder.getEntityManager();
            }
        }
    }
    else if (!TransactionSynchronizationManager.isSynchronizationActive()) {
        // Indicate that we can't obtain a transactional EntityManager.
        return null;
    }
```

없으면 새로 열어 바인딩한다.

`spring-orm` / `org.springframework.orm.jpa` / `EntityManagerFactoryUtils.java` L258-L269 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/EntityManagerFactoryUtils.java#L258-L269))

```java
// EntityManagerFactoryUtils.java L258-L269
// Create a new EntityManager for use within the current transaction.
logger.debug("Opening JPA EntityManager");
EntityManager em = null;
if (!synchronizedWithTransaction) {
    try {
        em = emf.createEntityManager(SynchronizationType.UNSYNCHRONIZED, properties);
    }
    catch (AbstractMethodError err) {
        // JPA 2.1 API available but method not actually implemented in persistence provider:
        // falling back to regular createEntityManager method.
    }
}
```

## 동작 흐름

```text
 doGetTransactionalEntityManager(emf, properties, synchronizedWithTransaction)
 |
 | L207 TransactionSynchronizationManager.getResource(emf)
 |        팩토리를 키로 스레드에 묶인 EntityManagerHolder 를 찾는다
 |
 +-- [A] 홀더가 있다 (L208)
 |    |
 |    +-- 동기화된 EntityManager 를 요구하는 경우 (L209)
 |    |     L210 아직 동기화되지 않았다면
 |    |       L215 실제 트랜잭션이 있으면 em.joinTransaction()  (JTA 대응)
 |    |       L221 동기화가 켜져 있으면 TransactionalEntityManagerSynchronization 등록
 |    |            = 트랜잭션이 끝날 때 정리되도록 콜백을 건다
 |    |     L230 홀더 참조 카운트 증가 후 그 EntityManager 반환
 |    |
 |    +-- 비동기화 EntityManager 를 요구하는 경우 (L233)
 |          활성 트랜잭션이 있고 홀더가 열려 있지 않으면
 |            L242 바인딩을 풀고 새로 만든다
 |          그 밖이면 L249 기존 것을 반환
 |
 +-- [B] 홀더가 없다
 |    |
 |    +-- L253 동기화 자체가 비활성 --> null 반환
 |          = 트랜잭션 밖이라는 뜻. 호출자가 임시 EntityManager 를 열어 쓴다
 |
 +-- [C] 여기까지 왔으면 트랜잭션은 있는데 EntityManager 가 없는 상태
        L261 비동기화 요구면 createEntityManager(UNSYNCHRONIZED, ...)
               벤더가 미구현이면 AbstractMethodError 를 잡아 일반 경로로 (L265)
        L270 그 밖이면 일반 createEntityManager
        이후 홀더를 만들어 바인딩하고 동기화 콜백을 등록한다
```

```text
 null 이 돌아오는 두 경우

 L253  묶인 홀더가 없고 동기화도 꺼져 있다
 L237  비동기화 EntityManager 를 요구했는데, 활성 트랜잭션 홀더가 이미 있고
       그 홀더가 열려 있지 않으며 동기화도 꺼져 있다

 어느 쪽이든
        --> 공유 프록시가 이 null 을 보고 임시 EntityManager 를 열었다 닫는다
        --> 쓰기 메서드였다면 TransactionRequiredException 으로 막힌다
```

## 결과가 쓰이는 곳

```text
 반환한 EntityManager
      --> 공유 프록시가 그 호출 하나를 위임한다
      --> JpaTransactionManager 도 같은 바인딩을 읽어 커밋 대상을 정한다

 홀더의 참조 카운트 (L230 requested)
      --> 소스 주석대로 "동기화된 접근이 있었는가"를 기록하는 용도다 (L228-L229)
      --> L235 의 isOpen() 검사가 이 값을 읽어, 비동기화 요구가 왔을 때
          기존 바인딩을 풀고 새로 만들지 정한다
      --> 트랜잭션이 끝날 때 닫을지는 "이 트랜잭션이 새로 연 것인가"가 정한다
          (doCleanupAfterCompletion 의 isNewEntityManagerHolder)

 등록한 TransactionSynchronization
      --> 트랜잭션 종료 시 EntityManager 정리, flush 시점 연결
      --> 트랜잭션 매니저가 아닌 경로(JTA 등)에서 열린 것도 같은 방식으로 정리된다

 팩토리를 키로 쓴다는 점
      --> EntityManagerFactory 가 둘이면 바인딩도 둘이다
      --> 멀티 데이터소스 구성에서 영속성 컨텍스트가 섞이지 않는 근거다
```

같은 방식으로 커넥션을 스레드에 묶는 JDBC 쪽 경로는 [DataSourceUtils.getConnection](../../../jdbc/01_JdbcTemplate.execute/01_DataSourceUtils.getConnection/README.md)에 있다.
