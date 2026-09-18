# TransactionAspectSupport.commitTransactionAfterReturning

상위: [TransactionAspectSupport.invokeWithinTransaction](../README.md)

타깃 메서드가 예외 없이 끝났을 때 커밋을 요청한다. 트랜잭션이 없었다면 아무 일도 하지 않는다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.interceptor` / `TransactionAspectSupport.java` L682-L689 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L682-L689))

```java
// TransactionAspectSupport.java L682-L689
protected void commitTransactionAfterReturning(@Nullable TransactionInfo txInfo) {
    if (txInfo != null && txInfo.getTransactionStatus() != null) {
        if (logger.isTraceEnabled()) {
            logger.trace("Completing transaction for [" + txInfo.getJoinpointIdentification() + "]");
        }
        txInfo.getTransactionManager().commit(txInfo.getTransactionStatus());
    }
}
```

## 동작 흐름

```text
 commitTransactionAfterReturning(txInfo)
 |
 +-- txInfo 가 없거나 status 가 없음 (트랜잭션 없는 메서드) --> 아무 일도 안 함
 |
 +-- L687 transactionManager.commit(status)
```

1. 실제 커밋 처리는 [AbstractPlatformTransactionManager.commit](01_AbstractPlatformTransactionManager.commit/README.md)이 한다.

## 결과가 쓰이는 곳

```text
 커밋 성공
      --> 커넥션 commit, 동기화 콜백 afterCommit / afterCompletion(COMMITTED)
      --> 리소스 바인딩 해제, 커넥션 반납

 rollback-only 표시가 있었던 경우
      --> 커밋 요청이지만 실제로는 롤백된다
      --> 바깥 트랜잭션이라면 UnexpectedRollbackException 이 호출자에게 전달

 커밋 실패 (제약 위반 등)
      --> TransactionSystemException / DataAccessException 으로 변환되어
          invokeWithinTransaction 밖으로, 즉 호출자에게 던져진다
      --> 메서드는 정상 반환했는데 호출자는 예외를 받는 상황이 된다
```
