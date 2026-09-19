# JpaTransactionManager.doCommit

상위: [Spring JPA 연동](../README.md)

커밋 한 줄이 flush 를 부르는 자리다. 코드 어디에도 `update`가 없는데 UPDATE 문이 나가는 이유가 여기 있다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `JpaTransactionManager.java` L544-L567 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/JpaTransactionManager.java#L544-L567))

```java
// JpaTransactionManager.java L544-L567
protected void doCommit(DefaultTransactionStatus status) {
    JpaTransactionObject txObject = (JpaTransactionObject) status.getTransaction();
    if (status.isDebug()) {
        logger.debug("Committing JPA transaction on EntityManager [" +
                txObject.getEntityManagerHolder().getEntityManager() + "]");
    }
    try {
        EntityTransaction tx = txObject.getEntityManagerHolder().getEntityManager().getTransaction();
        tx.commit();
    }
    catch (RollbackException ex) {
        if (ex.getCause() instanceof RuntimeException runtimeException) {
            DataAccessException dae = getJpaDialect().translateExceptionIfPossible(runtimeException);
            if (dae != null) {
                throw dae;
            }
        }
        throw new TransactionSystemException("Could not commit JPA transaction", ex);
    }
    catch (RuntimeException ex) {
        // Assumably failed to flush changes to database.
        throw DataAccessUtils.translateIfNecessary(ex, getJpaDialect());
    }
}
```

## 동작 흐름

```text
 doCommit(status)
 |
 | L545 트랜잭션 객체에서 EntityManagerHolder 를 꺼낸다
 |
 | L551 em.getTransaction()  --> EntityTransaction
 | L552 tx.commit()
 |        이 안에서 벤더가 flush 를 수행한다
 |        더티 체킹으로 발견한 변경이 이 시점에 SQL 이 된다
 |
 +-- L554 RollbackException
 |        원인이 RuntimeException 이면 방언에게 번역을 맡긴다 (L556)
 |          번역되면 그 DataAccessException 을 던진다
 |        아니면 L561 TransactionSystemException("Could not commit JPA transaction")
 |
 +-- L563 그 밖의 RuntimeException
        DataAccessUtils.translateIfNecessary(ex, 방언)
        = flush 실패(제약 위반 등)를 스프링 예외로 바꿔 던진다
```

```text
 언제 SQL 이 나가는가

 em.persist(entity)          영속성 컨텍스트에만 등록 (INSERT 아직 아님)
 entity.setName("x")         스냅숏과 달라진 것만 기록
 ...
 커밋 시점 tx.commit()
   flush --> 쓰기 지연 저장소의 INSERT/UPDATE/DELETE 를 순서대로 실행
   이어서 실제 커밋

 예외
   JPQL 쿼리 실행 전에는 벤더가 자동 flush 하기도 한다 (flush 모드 AUTO)
   읽기 전용 트랜잭션에서는 flush 모드를 MANUAL 로 낮추는 벤더가 있다
```

## 결과가 쓰이는 곳

```text
 커밋 성공
      --> AbstractPlatformTransactionManager 가 afterCommit, afterCompletion 콜백을 부른다
      --> @TransactionalEventListener(AFTER_COMMIT) 가 이 자리에서 실행된다

 커밋 실패
      --> 스프링 DataAccessException 계층으로 번역돼 올라간다
      --> 제약 위반은 DataIntegrityViolationException, 낙관적 잠금 실패는
          JpaOptimisticLockingFailureException 으로 드러난다

 flush 가 커밋 시점에 몰린다는 점
      --> 트랜잭션이 길수록 마지막에 SQL 이 한꺼번에 나간다
      --> 중간에 검증하려면 em.flush() 를 명시적으로 부른다

 정리 단계
      --> doCleanupAfterCompletion 이 바인딩을 풀고 EntityManager 를 닫는다
      --> 그 뒤로 엔티티는 준영속이라 지연 로딩이 실패한다
```

예외가 어떤 타입으로 번역되는지는 [convertJpaAccessExceptionIfPossible](../05_EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible/README.md)에, 커밋 전후의 콜백 순서는 [트랜잭션의 commit](../../transaction/01_TransactionAspectSupport.invokeWithinTransaction/02_TransactionAspectSupport.commitTransactionAfterReturning/01_AbstractPlatformTransactionManager.commit/README.md)에 있다.
