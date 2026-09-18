# AbstractPlatformTransactionManager.getTransaction

상위: [TransactionAspectSupport.createTransactionIfNecessary](../README.md)

전파(propagation) 속성을 해석하는 곳이다. 지금 스레드에 트랜잭션이 있는지 보고, 속성에 따라 새로 열거나, 참여하거나, 잠시 중단하거나, 예외를 던진다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.support` / `AbstractPlatformTransactionManager.java` L373-L421 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/support/AbstractPlatformTransactionManager.java#L373-L421))

```java
// AbstractPlatformTransactionManager.java L373-L421
public final TransactionStatus getTransaction(@Nullable TransactionDefinition definition)
        throws TransactionException {

    // Use defaults if no transaction definition given.
    TransactionDefinition def = (definition != null ? definition : TransactionDefinition.withDefaults());

    Object transaction = doGetTransaction();
    boolean debugEnabled = logger.isDebugEnabled();

    if (isExistingTransaction(transaction)) {
        // Existing transaction found -> check propagation behavior to find out how to behave.
        return handleExistingTransaction(def, transaction, debugEnabled);
    }

    // Check definition settings for new transaction.
    if (def.getTimeout() < TransactionDefinition.TIMEOUT_DEFAULT) {
        throw new InvalidTimeoutException("Invalid transaction timeout", def.getTimeout());
    }

    // No existing transaction found -> check propagation behavior to find out how to proceed.
    if (def.getPropagationBehavior() == TransactionDefinition.PROPAGATION_MANDATORY) {
        throw new IllegalTransactionStateException(
                "No existing transaction found for transaction marked with propagation 'mandatory'");
    }
    else if (def.getPropagationBehavior() == TransactionDefinition.PROPAGATION_REQUIRED ||
            def.getPropagationBehavior() == TransactionDefinition.PROPAGATION_REQUIRES_NEW ||
            def.getPropagationBehavior() == TransactionDefinition.PROPAGATION_NESTED) {
        SuspendedResourcesHolder suspendedResources = suspend(null);
        if (debugEnabled) {
            logger.debug("Creating new transaction with name [" + def.getName() + "]: " + def);
        }
        try {
            return startTransaction(def, transaction, false, debugEnabled, suspendedResources);
        }
        catch (RuntimeException | Error ex) {
            resume(null, suspendedResources);
            throw ex;
        }
    }
    else {
        // Create "empty" transaction: no actual transaction, but potentially synchronization.
        if (def.getIsolationLevel() != TransactionDefinition.ISOLATION_DEFAULT && logger.isWarnEnabled()) {
            logger.warn("Custom isolation level specified but no actual transaction initiated; " +
                    "isolation level will effectively be ignored: " + def);
        }
        boolean newSynchronization = (getTransactionSynchronization() == SYNCHRONIZATION_ALWAYS);
        return prepareTransactionStatus(def, null, true, newSynchronization, debugEnabled, null);
    }
}
```

`spring-tx` / `org.springframework.transaction.support` / `AbstractPlatformTransactionManager.java` L426-L519 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/support/AbstractPlatformTransactionManager.java#L426-L519))

```java
// AbstractPlatformTransactionManager.java L426-L519
private TransactionStatus handleExistingTransaction(
        TransactionDefinition definition, Object transaction, boolean debugEnabled)
        throws TransactionException {

    if (definition.getPropagationBehavior() == TransactionDefinition.PROPAGATION_NEVER) {
        throw new IllegalTransactionStateException(
                "Existing transaction found for transaction marked with propagation 'never'");
    }

    if (definition.getPropagationBehavior() == TransactionDefinition.PROPAGATION_NOT_SUPPORTED) {
        if (debugEnabled) {
            logger.debug("Suspending current transaction");
        }
        Object suspendedResources = suspend(transaction);
        boolean newSynchronization = (getTransactionSynchronization() == SYNCHRONIZATION_ALWAYS);
        return prepareTransactionStatus(
                definition, null, false, newSynchronization, debugEnabled, suspendedResources);
    }

    if (definition.getPropagationBehavior() == TransactionDefinition.PROPAGATION_REQUIRES_NEW) {
        if (debugEnabled) {
            logger.debug("Suspending current transaction, creating new transaction with name [" +
                    definition.getName() + "]");
        }
        SuspendedResourcesHolder suspendedResources = suspend(transaction);
        try {
            return startTransaction(definition, transaction, false, debugEnabled, suspendedResources);
        }
        catch (RuntimeException | Error beginEx) {
            resumeAfterBeginException(transaction, suspendedResources, beginEx);
            throw beginEx;
        }
    }

    if (definition.getPropagationBehavior() == TransactionDefinition.PROPAGATION_NESTED) {
        if (!isNestedTransactionAllowed()) {
            throw new NestedTransactionNotSupportedException(
                    "Transaction manager does not allow nested transactions by default - " +
                    "specify 'nestedTransactionAllowed' property with value 'true'");
        }
        if (debugEnabled) {
            logger.debug("Creating nested transaction with name [" + definition.getName() + "]");
        }
        if (useSavepointForNestedTransaction()) {
            // Create savepoint within existing Spring-managed transaction,
            // through the SavepointManager API implemented by TransactionStatus.
            // Usually uses JDBC savepoints. Never activates Spring synchronization.
            DefaultTransactionStatus status = newTransactionStatus(
                    definition, transaction, false, false, true, debugEnabled, null);
            this.transactionExecutionListeners.forEach(listener -> listener.beforeBegin(status));
            try {
                status.createAndHoldSavepoint();
            }
            catch (RuntimeException | Error ex) {
                this.transactionExecutionListeners.forEach(listener -> listener.afterBegin(status, ex));
                throw ex;
            }
            this.transactionExecutionListeners.forEach(listener -> listener.afterBegin(status, null));
            return status;
        }
        else {
            // Nested transaction through nested begin and commit/rollback calls.
            // Usually only for JTA: Spring synchronization might get activated here
            // in case of a pre-existing JTA transaction.
            return startTransaction(definition, transaction, true, debugEnabled, null);
        }
    }

    // PROPAGATION_REQUIRED, PROPAGATION_SUPPORTS, PROPAGATION_MANDATORY:
    // regular participation in existing transaction.
    if (debugEnabled) {
        logger.debug("Participating in existing transaction");
    }
    if (isValidateExistingTransaction()) {
        if (definition.getIsolationLevel() != TransactionDefinition.ISOLATION_DEFAULT) {
            Integer currentIsolationLevel = TransactionSynchronizationManager.getCurrentTransactionIsolationLevel();
            if (currentIsolationLevel == null || currentIsolationLevel != definition.getIsolationLevel()) {
                throw new IllegalTransactionStateException("Participating transaction with definition [" +
                        definition + "] specifies isolation level which is incompatible with existing transaction: " +
                        (currentIsolationLevel != null ?
                                DefaultTransactionDefinition.getIsolationLevelName(currentIsolationLevel) :
                                "(unknown)"));
            }
        }
        if (!definition.isReadOnly()) {
            if (TransactionSynchronizationManager.isCurrentTransactionReadOnly()) {
                throw new IllegalTransactionStateException("Participating transaction with definition [" +
                        definition + "] is not marked as read-only but existing transaction is");
            }
        }
    }
    boolean newSynchronization = (getTransactionSynchronization() != SYNCHRONIZATION_NEVER);
    return prepareTransactionStatus(definition, transaction, false, newSynchronization, debugEnabled, null);
}
```

`spring-tx` / `org.springframework.transaction.support` / `AbstractPlatformTransactionManager.java` L524-L541 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/support/AbstractPlatformTransactionManager.java#L524-L541))

```java
// AbstractPlatformTransactionManager.java L524-L541
private TransactionStatus startTransaction(TransactionDefinition definition, Object transaction,
        boolean nested, boolean debugEnabled, @Nullable SuspendedResourcesHolder suspendedResources) {

    boolean newSynchronization = (getTransactionSynchronization() != SYNCHRONIZATION_NEVER);
    DefaultTransactionStatus status = newTransactionStatus(
            definition, transaction, true, newSynchronization, nested, debugEnabled, suspendedResources);
    this.transactionExecutionListeners.forEach(listener -> listener.beforeBegin(status));
    try {
        doBegin(transaction, definition);
    }
    catch (RuntimeException | Error ex) {
        this.transactionExecutionListeners.forEach(listener -> listener.afterBegin(status, ex));
        throw ex;
    }
    prepareSynchronization(status, definition);
    this.transactionExecutionListeners.forEach(listener -> listener.afterBegin(status, null));
    return status;
}
```

## 동작 흐름

```text
 getTransaction(definition)
 |
 | L379 transaction = doGetTransaction()     구현체가 현재 스레드의 리소스를 조회
 |                                            (JDBC 면 DataSource 에 바인딩된 ConnectionHolder)
 |
 +-- L382 이미 트랜잭션이 있음 --> handleExistingTransaction
 |      |
 |      +-- NEVER          --> IllegalTransactionStateException
 |      +-- NOT_SUPPORTED  --> 기존 트랜잭션 중단(suspend), 트랜잭션 없이 실행
 |      +-- REQUIRES_NEW   --> 기존 중단 후 새 트랜잭션 시작
 |      +-- NESTED         --> 세이브포인트 생성 (JDBC) 또는 중첩 begin
 |      +-- REQUIRED / SUPPORTS / MANDATORY
 |             --> 기존 트랜잭션에 참여 (새 트랜잭션 아님)
 |                 격리 수준/읽기 전용이 다르면 검증 후 경고 또는 예외
 |
 +-- 트랜잭션 없음
        +-- MANDATORY  --> IllegalTransactionStateException  (반드시 있어야 하는데 없음)
        +-- REQUIRED | REQUIRES_NEW | NESTED
        |     L400 suspend(null)   동기화만 중단
        |     L405 startTransaction
        |            newTransactionStatus 생성
        |            beforeBegin 리스너
        |            doBegin(transaction, definition)   <-- 구현체가 실제로 연다
        |            prepareSynchronization              동기화 활성화
        |            afterBegin 리스너
        +-- SUPPORTS | NOT_SUPPORTED | NEVER
              L419 "빈" 트랜잭션 상태  (실제 트랜잭션 없음, 동기화만 가능)
```

JDBC 구현의 `doBegin`이 실제로 하는 일이다.

```text
 DataSourceTransactionManager.doBegin  (DataSourceTransactionManager L263)
   DataSource 에서 커넥션 획득
   격리 수준, 읽기 전용 적용
   autoCommit 이 true 면 false 로 전환        <-- 여기서 트랜잭션이 열린다
   타임아웃 기록
   TransactionSynchronizationManager.bindResource(dataSource, connectionHolder)
```

## 결과가 쓰이는 곳

```text
 TransactionStatus
      +-- isNewTransaction()  --> 커밋/롤백 단계에서 실제 commit 을 할지, 참여만 했는지 판단
      +-- hasSavepoint()      --> NESTED 인 경우 세이브포인트로 되돌린다
      +-- suspendedResources  --> 트랜잭션 종료 시 중단했던 것을 resume

 bindResource 로 묶인 커넥션
      --> 같은 스레드의 JdbcTemplate, JPA EntityManager 가 이 커넥션을 찾아 쓴다
      --> 이 바인딩이 "같은 트랜잭션" 의 실체다

 참여(REQUIRED, 기존 트랜잭션 있음)
      --> 새 커넥션도, 새 트랜잭션도 만들지 않는다
      --> 안쪽에서 롤백하면 rollback-only 표시만 남고
          실제 롤백은 가장 바깥에서 일어난다
```
