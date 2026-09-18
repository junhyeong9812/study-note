# AbstractPlatformTransactionManager.commit

상위: [TransactionAspectSupport.commitTransactionAfterReturning](../README.md)

커밋 요청을 받아 실제로 커밋할지 롤백할지 결정하고, 동기화 콜백을 순서대로 부른다. 참여 중인(새 트랜잭션이 아닌) 상태라면 실제 커밋은 하지 않는다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.support` / `AbstractPlatformTransactionManager.java` L734-L758 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/support/AbstractPlatformTransactionManager.java#L734-L758))

```java
// AbstractPlatformTransactionManager.java L734-L758
public final void commit(TransactionStatus status) throws TransactionException {
    if (status.isCompleted()) {
        throw new IllegalTransactionStateException(
                "Transaction is already completed - do not call commit or rollback more than once per transaction");
    }

    DefaultTransactionStatus defStatus = (DefaultTransactionStatus) status;
    if (defStatus.isLocalRollbackOnly()) {
        if (defStatus.isDebug()) {
            logger.debug("Transactional code has requested rollback");
        }
        processRollback(defStatus, false);
        return;
    }

    if (!shouldCommitOnGlobalRollbackOnly() && defStatus.isGlobalRollbackOnly()) {
        if (defStatus.isDebug()) {
            logger.debug("Global transaction is marked as rollback-only but transactional code requested commit");
        }
        processRollback(defStatus, true);
        return;
    }

    processCommit(defStatus);
}
```

`spring-tx` / `org.springframework.transaction.support` / `AbstractPlatformTransactionManager.java` L766-L848 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/support/AbstractPlatformTransactionManager.java#L766-L848))

```java
// AbstractPlatformTransactionManager.java L766-L848
private void processCommit(DefaultTransactionStatus status) throws TransactionException {
    try {
        boolean beforeCompletionInvoked = false;
        boolean commitListenerInvoked = false;

        try {
            boolean unexpectedRollback = false;
            prepareForCommit(status);
            triggerBeforeCommit(status);
            triggerBeforeCompletion(status);
            beforeCompletionInvoked = true;

            if (status.hasSavepoint()) {
                if (status.isDebug()) {
                    logger.debug("Releasing transaction savepoint");
                }
                unexpectedRollback = status.isGlobalRollbackOnly();
                this.transactionExecutionListeners.forEach(listener -> listener.beforeCommit(status));
                commitListenerInvoked = true;
                status.releaseHeldSavepoint();
            }
            else if (status.isNewTransaction()) {
                if (status.isDebug()) {
                    logger.debug("Initiating transaction commit");
                }
                unexpectedRollback = status.isGlobalRollbackOnly();
                this.transactionExecutionListeners.forEach(listener -> listener.beforeCommit(status));
                commitListenerInvoked = true;
                doCommit(status);
            }
            else if (isFailEarlyOnGlobalRollbackOnly()) {
                unexpectedRollback = status.isGlobalRollbackOnly();
            }

            // Throw UnexpectedRollbackException if we have a global rollback-only
            // marker but still didn't get a corresponding exception from commit.
            if (unexpectedRollback) {
                throw new UnexpectedRollbackException(
                        "Transaction silently rolled back because it has been marked as rollback-only");
            }
        }
        catch (UnexpectedRollbackException ex) {
            triggerAfterCompletion(status, TransactionSynchronization.STATUS_ROLLED_BACK);
            this.transactionExecutionListeners.forEach(listener -> listener.afterRollback(status, null));
            throw ex;
        }
        catch (TransactionException ex) {
            if (isRollbackOnCommitFailure()) {
                doRollbackOnCommitException(status, ex);
            }
            else {
                triggerAfterCompletion(status, TransactionSynchronization.STATUS_UNKNOWN);
                if (commitListenerInvoked) {
                    this.transactionExecutionListeners.forEach(listener -> listener.afterCommit(status, ex));
                }
            }
            throw ex;
        }
        catch (RuntimeException | Error ex) {
            if (!beforeCompletionInvoked) {
                triggerBeforeCompletion(status);
            }
            doRollbackOnCommitException(status, ex);
            throw ex;
        }

        // Trigger afterCommit callbacks, with an exception thrown there
        // propagated to callers but the transaction still considered as committed.
        try {
            triggerAfterCommit(status);
        }
        finally {
            triggerAfterCompletion(status, TransactionSynchronization.STATUS_COMMITTED);
            if (commitListenerInvoked) {
                this.transactionExecutionListeners.forEach(listener -> listener.afterCommit(status, null));
            }
        }

    }
    finally {
        cleanupAfterCompletion(status);
    }
}
```

## 동작 흐름

```text
 commit(status)
 |
 | L735 이미 완료된 트랜잭션 --> IllegalTransactionStateException
 |
 +-- L741 로컬 rollback-only (이 상태에 setRollbackOnly 호출됨)
 |      --> processRollback(status, false)   커밋 대신 롤백
 |
 +-- L749 글로벌 rollback-only (참여한 바깥 트랜잭션이 이미 롤백 표시)
 |      --> processRollback(status, true)    "예상치 못한 롤백" 으로 표시
 |
 +-- L757 processCommit(status)

 processCommit(status)
 |
 | L773 prepareForCommit / triggerBeforeCommit / triggerBeforeCompletion
 |        동기화 콜백 (JPA 플러시가 여기서 일어난다)
 |
 +-- L778 세이브포인트가 있음 (NESTED)
 |      --> releaseHeldSavepoint   바깥 트랜잭션은 그대로 진행
 |
 +-- L787 새 트랜잭션임
 |      --> doCommit(status)       구현체가 커넥션 commit 실행
 |
 +-- L796 그 밖 (참여 중)
 |      --> 아무 것도 하지 않는다. 커밋은 바깥이 한다
 |
 | L802 글로벌 rollback-only 인데 예외 없이 여기까지 왔다
 |      --> UnexpectedRollbackException
 |
 +-- finally  triggerAfterCompletion, 리소스 정리(cleanupAfterCompletion)
              중단했던 트랜잭션이 있으면 resume
```

## 결과가 쓰이는 곳

```text
 doCommit
      --> JDBC: Connection.commit()
      --> JPA:  EntityManager 플러시 후 트랜잭션 커밋

 동기화 콜백 순서
      beforeCommit --> beforeCompletion --> (실제 커밋) --> afterCommit --> afterCompletion
      --> @TransactionalEventListener(phase = AFTER_COMMIT) 가 afterCompletion 단계에서 실행

 UnexpectedRollbackException
      --> 안쪽 메서드가 예외를 삼켰지만 트랜잭션은 이미 롤백 표시된 경우
          "분명 커밋했는데 데이터가 없다" 가 아니라 예외로 드러나게 하는 장치
```
