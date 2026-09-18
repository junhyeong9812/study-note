# AbstractPlatformTransactionManager.rollback

상위: [TransactionAspectSupport.completeTransactionAfterThrowing](../README.md)

롤백 요청을 처리한다. 새 트랜잭션이면 실제로 되돌리고, 참여 중이면 "이 트랜잭션은 커밋될 수 없다"는 표시만 남긴다. 세이브포인트가 있으면 거기까지만 되돌린다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.support` / `AbstractPlatformTransactionManager.java` L858-L866 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/support/AbstractPlatformTransactionManager.java#L858-L866))

```java
// AbstractPlatformTransactionManager.java L858-L866
public final void rollback(TransactionStatus status) throws TransactionException {
    if (status.isCompleted()) {
        throw new IllegalTransactionStateException(
                "Transaction is already completed - do not call commit or rollback more than once per transaction");
    }

    DefaultTransactionStatus defStatus = (DefaultTransactionStatus) status;
    processRollback(defStatus, false);
}
```

`spring-tx` / `org.springframework.transaction.support` / `AbstractPlatformTransactionManager.java` L874-L944 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/support/AbstractPlatformTransactionManager.java#L874-L944))

```java
// AbstractPlatformTransactionManager.java L874-L944
private void processRollback(DefaultTransactionStatus status, boolean unexpected) {
    try {
        boolean unexpectedRollback = unexpected;
        boolean rollbackListenerInvoked = false;

        try {
            triggerBeforeCompletion(status);

            if (status.hasSavepoint()) {
                if (status.isDebug()) {
                    logger.debug("Rolling back transaction to savepoint");
                }
                this.transactionExecutionListeners.forEach(listener -> listener.beforeRollback(status));
                rollbackListenerInvoked = true;
                status.rollbackToHeldSavepoint();
            }
            else if (status.isNewTransaction()) {
                if (status.isDebug()) {
                    logger.debug("Initiating transaction rollback");
                }
                this.transactionExecutionListeners.forEach(listener -> listener.beforeRollback(status));
                rollbackListenerInvoked = true;
                doRollback(status);
            }
            else {
                // Participating in larger transaction
                if (status.hasTransaction()) {
                    if (status.isLocalRollbackOnly() || isGlobalRollbackOnParticipationFailure()) {
                        if (status.isDebug()) {
                            logger.debug("Participating transaction failed - marking existing transaction as rollback-only");
                        }
                        doSetRollbackOnly(status);
                    }
                    else {
                        if (status.isDebug()) {
                            logger.debug("Participating transaction failed - letting transaction originator decide on rollback");
                        }
                    }
                }
                else {
                    logger.debug("Should roll back transaction but cannot - no transaction available");
                }
                // Unexpected rollback only matters here if we're asked to fail early
                if (!isFailEarlyOnGlobalRollbackOnly()) {
                    unexpectedRollback = false;
                }
            }
        }
        catch (RuntimeException | Error ex) {
            triggerAfterCompletion(status, TransactionSynchronization.STATUS_UNKNOWN);
            if (rollbackListenerInvoked) {
                this.transactionExecutionListeners.forEach(listener -> listener.afterRollback(status, ex));
            }
            throw ex;
        }

        triggerAfterCompletion(status, TransactionSynchronization.STATUS_ROLLED_BACK);
        if (rollbackListenerInvoked) {
            this.transactionExecutionListeners.forEach(listener -> listener.afterRollback(status, null));
        }

        // Raise UnexpectedRollbackException if we had a global rollback-only marker
        if (unexpectedRollback) {
            throw new UnexpectedRollbackException(
                    "Transaction rolled back because it has been marked as rollback-only");
        }
    }
    finally {
        cleanupAfterCompletion(status);
    }
}
```

## 동작 흐름

```text
 rollback(status)
 |
 | L859 이미 완료 --> IllegalTransactionStateException
 +-- processRollback(status, unexpected = false)

 processRollback(status, unexpected)
 |
 | L880 triggerBeforeCompletion   동기화 콜백
 |
 +-- L882 세이브포인트 있음 (NESTED)
 |      --> rollbackToHeldSavepoint   바깥 트랜잭션은 살아 있다
 |
 +-- L890 새 트랜잭션임
 |      --> doRollback(status)        구현체가 커넥션 rollback 실행
 |
 +-- L898 참여 중 (새 트랜잭션 아님)
 |      --> 로컬 rollback-only 이거나 globalRollbackOnParticipationFailure(기본 true)
 |            --> doSetRollbackOnly(status)    글로벌 rollback-only 표시
 |          아니면 아무 일도 안 함 (바깥이 결정)
 |
 | unexpected 였으면 --> UnexpectedRollbackException
 |
 +-- finally  triggerAfterCompletion(ROLLED_BACK), 리소스 정리, 중단 트랜잭션 resume
```

## 결과가 쓰이는 곳

```text
 doRollback
      --> JDBC: Connection.rollback()

 글로벌 rollback-only 표시
      --> 바깥 트랜잭션이 commit 을 요청해도 롤백되고
          호출자는 UnexpectedRollbackException 을 받는다
      --> 안쪽 @Transactional 메서드에서 예외가 났고 바깥에서 그것을 잡아도
          전체가 롤백되는 이유

 세이브포인트 롤백 (NESTED)
      --> 안쪽 작업만 되돌리고 바깥은 계속 진행할 수 있다
      --> REQUIRES_NEW 와 달리 커넥션은 하나다
```
