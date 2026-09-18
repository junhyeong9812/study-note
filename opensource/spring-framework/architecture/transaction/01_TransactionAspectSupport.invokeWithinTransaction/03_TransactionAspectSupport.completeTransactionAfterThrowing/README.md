# TransactionAspectSupport.completeTransactionAfterThrowing

상위: [TransactionAspectSupport.invokeWithinTransaction](../README.md)

타깃 메서드가 예외를 던졌을 때 롤백할지 커밋할지 판단한다. 기본 규칙은 "언체크 예외면 롤백, 체크 예외면 커밋"이고, `@Transactional(rollbackFor = ...)`이 이 규칙을 덮어쓴다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.interceptor` / `TransactionAspectSupport.java` L697-L737 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L697-L737))

```java
// TransactionAspectSupport.java L697-L737
protected void completeTransactionAfterThrowing(
        @Nullable TransactionInfo txInfo, InvocationCallback invocation, Throwable ex) {

    if (txInfo != null && txInfo.getTransactionStatus() != null) {
        if (logger.isTraceEnabled()) {
            logger.trace("Completing transaction for [" + txInfo.getJoinpointIdentification() +
                    "] after exception: " + ex);
        }
        if (txInfo.transactionAttribute != null && txInfo.transactionAttribute.rollbackOn(ex)) {
            invocation.onRollback(ex, txInfo.getTransactionStatus());
            try {
                txInfo.getTransactionManager().rollback(txInfo.getTransactionStatus());
            }
            catch (TransactionSystemException ex2) {
                logger.error("Application exception overridden by rollback exception", ex);
                ex2.initApplicationException(ex);
                throw ex2;
            }
            catch (RuntimeException | Error ex2) {
                logger.error("Application exception overridden by rollback exception", ex);
                throw ex2;
            }
        }
        else {
            // We don't roll back on this exception.
            // Will still roll back if TransactionStatus.isRollbackOnly() is true.
            try {
                txInfo.getTransactionManager().commit(txInfo.getTransactionStatus());
            }
            catch (TransactionSystemException ex2) {
                logger.error("Application exception overridden by commit exception", ex);
                ex2.initApplicationException(ex);
                throw ex2;
            }
            catch (RuntimeException | Error ex2) {
                logger.error("Application exception overridden by commit exception", ex);
                throw ex2;
            }
        }
    }
}
```

판단 기준은 트랜잭션 속성의 `rollbackOn`이다.

`spring-tx` / `org.springframework.transaction.interceptor` / `DefaultTransactionAttribute.java` L179-L182 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/DefaultTransactionAttribute.java#L179-L182))

```java
// DefaultTransactionAttribute.java L179-L182
@Override
public boolean rollbackOn(Throwable ex) {
    return (ex instanceof RuntimeException || ex instanceof Error);
}
```

`spring-tx` / `org.springframework.transaction.interceptor` / `RuleBasedTransactionAttribute.java` L122-L143 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/RuleBasedTransactionAttribute.java#L122-L143))

```java
// RuleBasedTransactionAttribute.java L122-L143
@Override
public boolean rollbackOn(Throwable ex) {
    RollbackRuleAttribute winner = null;
    int deepest = Integer.MAX_VALUE;

    if (this.rollbackRules != null) {
        for (RollbackRuleAttribute rule : this.rollbackRules) {
            int depth = rule.getDepth(ex);
            if (depth >= 0 && depth < deepest) {
                deepest = depth;
                winner = rule;
            }
        }
    }

    // User superclass behavior (rollback on unchecked) if no rule matches.
    if (winner == null) {
        return super.rollbackOn(ex);
    }

    return !(winner instanceof NoRollbackRuleAttribute);
}
```

## 동작 흐름

```text
 completeTransactionAfterThrowing(txInfo, invocation, ex)
 |
 +-- 트랜잭션이 없었음 --> 아무 일도 안 함 (예외는 그대로 전파)
 |
 +-- L705 txAttr.rollbackOn(ex) 가 true
 |      onRollback 이벤트 --> L708 transactionManager.rollback(status)
 |      롤백 중 또 예외가 나면
 |        --> 원래 예외를 로그로 남기고 롤백 예외를 던진다
 |            ("Application exception overridden by rollback exception")
 |
 +-- L720 false (롤백 대상이 아님)
        --> L724 commit(status)
            단, rollback-only 표시가 있으면 commit 안에서 롤백된다
```

```text
 rollbackOn 판정

 DefaultTransactionAttribute (규칙 없음)
   RuntimeException 또는 Error   --> 롤백
   체크 예외                      --> 커밋

 RuleBasedTransactionAttribute (@Transactional(rollbackFor/noRollbackFor) 지정)
   각 규칙과 예외 타입의 상속 거리(depth)를 재서 가장 가까운 규칙이 이긴다
   이긴 규칙이 NoRollbackRule 이면 커밋, 아니면 롤백
   맞는 규칙이 없으면 위의 기본 규칙
```

1. 실제 롤백 처리는 [AbstractPlatformTransactionManager.rollback](01_AbstractPlatformTransactionManager.rollback/README.md)이 한다.

## 결과가 쓰이는 곳

```text
 롤백 결정
      --> 커넥션 rollback, 동기화 afterCompletion(ROLLED_BACK)
      --> 참여 중이면 실제 롤백 대신 rollback-only 표시만

 "체크 예외는 커밋" 규칙
      --> IOException 을 던졌는데 데이터가 저장돼 있는 상황의 근거
      --> 바꾸려면 @Transactional(rollbackFor = Exception.class)

 롤백 중 예외
      --> 원래 예외가 로그로만 남고 호출자는 롤백 예외를 받는다
      --> 로그를 봐야 원인을 알 수 있는 경우
```

## 하위 메서드

- [01 AbstractPlatformTransactionManager.rollback](01_AbstractPlatformTransactionManager.rollback/README.md)
