# JpaTransactionManager.doBegin

상위: [Spring JPA 연동](../README.md)

`@Transactional` 메서드에 들어설 때 JPA 쪽에서 실제로 일어나는 일이다. `EntityManager`를 새로 열어 스레드에 묶고, 벤더 방언에게 트랜잭션 시작을 맡기고, 데이터 소스를 알고 있으면 같은 커넥션을 JDBC 쪽에도 노출한다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `JpaTransactionManager.java` L386-L459 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/JpaTransactionManager.java#L386-L459))

```java
// JpaTransactionManager.java L386-L459
protected void doBegin(Object transaction, TransactionDefinition definition) {
    JpaTransactionObject txObject = (JpaTransactionObject) transaction;

    if (txObject.hasConnectionHolder() && !txObject.getConnectionHolder().isSynchronizedWithTransaction()) {
        throw new IllegalTransactionStateException(
                "Pre-bound JDBC Connection found! JpaTransactionManager does not support " +
                "running within DataSourceTransactionManager if told to manage the DataSource itself. " +
                "It is recommended to use a single JpaTransactionManager for all transactions " +
                "on a single DataSource, no matter whether JPA or JDBC access.");
    }

    try {
        if (!txObject.hasEntityManagerHolder() ||
                txObject.getEntityManagerHolder().isSynchronizedWithTransaction()) {
            EntityManager newEm = createEntityManagerForTransaction();
            if (logger.isDebugEnabled()) {
                logger.debug("Opened new EntityManager [" + newEm + "] for JPA transaction");
            }
            txObject.setEntityManagerHolder(new EntityManagerHolder(newEm), true);
        }

        EntityManager em = txObject.getEntityManagerHolder().getEntityManager();

        // Delegate to JpaDialect for actual transaction begin.
        int timeoutToUse = determineTimeout(definition);
        Object transactionData = getJpaDialect().beginTransaction(em,
                new JpaTransactionDefinition(definition, timeoutToUse, txObject.isNewEntityManagerHolder()));
        txObject.setTransactionData(transactionData);
        txObject.setReadOnly(definition.isReadOnly());

        // Register transaction timeout.
        if (timeoutToUse != TransactionDefinition.TIMEOUT_DEFAULT) {
            txObject.getEntityManagerHolder().setTimeoutInSeconds(timeoutToUse);
        }

        // Register the JPA EntityManager's JDBC Connection for the DataSource, if set.
        if (getDataSource() != null) {
            ConnectionHandle conHandle = getJpaDialect().getJdbcConnection(em, definition.isReadOnly());
            if (conHandle != null) {
                ConnectionHolder conHolder = new ConnectionHolder(conHandle);
                if (timeoutToUse != TransactionDefinition.TIMEOUT_DEFAULT) {
                    conHolder.setTimeoutInSeconds(timeoutToUse);
                }
                if (logger.isDebugEnabled()) {
                    logger.debug("Exposing JPA transaction as JDBC [" + conHandle + "]");
                }
                TransactionSynchronizationManager.bindResource(getDataSource(), conHolder);
                txObject.setConnectionHolder(conHolder);
            }
            else {
                if (logger.isDebugEnabled()) {
                    logger.debug("Not exposing JPA transaction [" + em + "] as JDBC transaction because " +
                            "JpaDialect [" + getJpaDialect() + "] does not support JDBC Connection retrieval");
                }
            }
        }

        // Bind the entity manager holder to the thread.
        if (txObject.isNewEntityManagerHolder()) {
            TransactionSynchronizationManager.bindResource(
                    obtainEntityManagerFactory(), txObject.getEntityManagerHolder());
        }
        txObject.getEntityManagerHolder().setSynchronizedWithTransaction(true);
    }

    catch (TransactionException ex) {
        closeEntityManagerAfterFailedBegin(txObject);
        throw ex;
    }
    catch (Throwable ex) {
        closeEntityManagerAfterFailedBegin(txObject);
        throw new CannotCreateTransactionException("Could not open JPA EntityManager for transaction", ex);
    }
}
```

## 동작 흐름

```text
 doBegin(transaction, definition)
 |
 +-- L389 이미 JDBC 커넥션이 스레드에 묶여 있고 트랜잭션과 동기화되지 않았다면
 |        --> IllegalTransactionStateException
 |            JpaTransactionManager 와 DataSourceTransactionManager 를 한 데이터 소스에
 |            같이 쓰지 말라는 경고다
 |
 +-- L398 EntityManagerHolder 가 없거나 이미 동기화된 것이면
 |        L400 createEntityManagerForTransaction() 으로 새로 연다
 |        L404 새 홀더를 트랜잭션 객체에 설정 (newEntityManagerHolder = true)
 |
 | L411 JpaDialect.beginTransaction(em, 정의)
 |        벤더가 격리 수준, 읽기 전용, 타임아웃을 실제로 건다
 |        기본 구현은 em.getTransaction().begin() 에 가깝다
 |
 | L417 타임아웃이 지정됐으면 홀더에 초 단위로 기록
 |
 +-- L444 새로 연 홀더라면 TransactionSynchronizationManager.bindResource(팩토리, 홀더)
 |        = 이 바인딩을 공유 프록시가 찾는다
 |
 +-- L422 dataSource 가 설정돼 있으면
        L423 JpaDialect.getJdbcConnection(em, 읽기 전용)
          null 이 아니면
            L425 ConnectionHolder 를 만들어
            L432 TransactionSynchronizationManager.bindResource(dataSource, 홀더)
            = 같은 트랜잭션의 JdbcTemplate 이 JPA 와 같은 커넥션을 쓴다
          null 이면 (방언이 커넥션 노출을 지원하지 않으면)
            로그만 남기고 넘어간다
```

```text
 방언이 커넥션을 내주느냐가 만드는 차이

 내준다 (HibernateJpaDialect 등)
   JPA 와 JDBC 가 한 트랜잭션, 한 커넥션
   JdbcTemplate 으로 짠 쿼리도 같은 트랜잭션에서 돈다

 내주지 않는다
   JDBC 쪽은 별도 커넥션을 얻는다
   같은 트랜잭션처럼 보이지만 실제로는 분리된다
```

1. 프록시가 이 바인딩을 찾는 방법은 [EntityManagerFactoryUtils.doGetTransactionalEntityManager](01_EntityManagerFactoryUtils.doGetTransactionalEntityManager/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 바인딩된 EntityManagerHolder
      --> 공유 프록시가 호출마다 이것을 찾아 위임한다
      --> 같은 트랜잭션의 모든 코드가 하나의 영속성 컨텍스트를 공유한다
      --> 1차 캐시와 더티 체킹이 성립하는 근거다

 바인딩된 ConnectionHolder
      --> DataSourceUtils.getConnection 이 새 커넥션 대신 이것을 돌려준다
      --> JPA 로 바꾼 데이터와 JdbcTemplate 으로 읽는 데이터가 같은 트랜잭션에 있다

 transactionData (방언이 돌려준 값)
      --> 커밋/롤백 뒤 정리 단계에서 방언에게 되돌려 준다 (격리 수준 복원 등)

 읽기 전용 표시
      --> 벤더에 따라 flush 모드를 MANUAL 로 낮춘다 (하이버네이트)
      --> 더티 체킹 비용을 줄이지만, 그 트랜잭션에서는 변경이 반영되지 않는다
```

전파와 롤백 규칙 같은 공통 골격은 [트랜잭션의 getTransaction](../../transaction/01_TransactionAspectSupport.invokeWithinTransaction/01_TransactionAspectSupport.createTransactionIfNecessary/01_AbstractPlatformTransactionManager.getTransaction/README.md)에 있다.

## 하위 메서드

- [01 EntityManagerFactoryUtils.doGetTransactionalEntityManager](01_EntityManagerFactoryUtils.doGetTransactionalEntityManager/README.md)
