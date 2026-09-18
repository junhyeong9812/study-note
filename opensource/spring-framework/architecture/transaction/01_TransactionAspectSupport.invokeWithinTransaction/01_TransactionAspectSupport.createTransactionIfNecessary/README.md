# TransactionAspectSupport.createTransactionIfNecessary

상위: [TransactionAspectSupport.invokeWithinTransaction](../README.md)

트랜잭션 속성이 있으면 매니저에게 트랜잭션을 요청하고, 그 결과를 `TransactionInfo`로 감싸 현재 스레드에 건다. 속성이 없어도 `TransactionInfo`는 만들어 스택 균형을 맞춘다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.interceptor` / `TransactionAspectSupport.java` L612-L638 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L612-L638))

```java
// TransactionAspectSupport.java L612-L638
protected TransactionInfo createTransactionIfNecessary(@Nullable PlatformTransactionManager tm,
        @Nullable TransactionAttribute txAttr, final String joinpointIdentification) {

    // If no name specified, apply method identification as transaction name.
    if (txAttr != null && txAttr.getName() == null) {
        txAttr = new DelegatingTransactionAttribute(txAttr) {
            @Override
            public String getName() {
                return joinpointIdentification;
            }
        };
    }

    TransactionStatus status = null;
    if (txAttr != null) {
        if (tm != null) {
            status = tm.getTransaction(txAttr);
        }
        else {
            if (logger.isDebugEnabled()) {
                logger.debug("Skipping transactional joinpoint [" + joinpointIdentification +
                        "] because no transaction manager has been configured");
            }
        }
    }
    return prepareTransactionInfo(tm, txAttr, joinpointIdentification, status);
}
```

`spring-tx` / `org.springframework.transaction.interceptor` / `TransactionAspectSupport.java` L648-L675 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L648-L675))

```java
// TransactionAspectSupport.java L648-L675
protected TransactionInfo prepareTransactionInfo(@Nullable PlatformTransactionManager tm,
        @Nullable TransactionAttribute txAttr, String joinpointIdentification,
        @Nullable TransactionStatus status) {

    TransactionInfo txInfo = new TransactionInfo(tm, txAttr, joinpointIdentification);
    if (txAttr != null) {
        // We need a transaction for this method...
        if (logger.isTraceEnabled()) {
            logger.trace("Getting transaction for [" + txInfo.getJoinpointIdentification() + "]");
        }
        // The transaction manager will flag an error if an incompatible tx already exists.
        txInfo.newTransactionStatus(status);
    }
    else {
        // The TransactionInfo.hasTransaction() method will return false. We created it only
        // to preserve the integrity of the ThreadLocal stack maintained in this class.
        if (logger.isTraceEnabled()) {
            logger.trace("No need to create transaction for [" + joinpointIdentification +
                    "]: This method is not transactional.");
        }
    }

    // We always bind the TransactionInfo to the thread, even if we didn't create
    // a new transaction here. This guarantees that the TransactionInfo stack
    // will be managed correctly even if no transaction was created by this aspect.
    txInfo.bindToThread();
    return txInfo;
}
```

## 동작 흐름

```text
 createTransactionIfNecessary(tm, txAttr, joinpointIdentification)
 |
 | L616 트랜잭션 이름이 비어 있으면 조인포인트 이름(클래스.메서드)을 이름으로 사용
 |        --> 로그와 모니터링에서 이 이름이 보인다
 |
 +-- L626 txAttr 있음 + 매니저 있음
 |      L628 status = tm.getTransaction(txAttr)     <-- 실제 트랜잭션 시작 지점
 |
 +-- L630 매니저가 없음 --> 디버그 로그만, 트랜잭션 없이 진행
 |
 +-- L637 prepareTransactionInfo(tm, txAttr, 이름, status)
        L652 TransactionInfo 생성
        L659 txAttr 이 있으면 status 를 담는다 (hasTransaction() == true)
        L673 bindToThread()
               ThreadLocal 에 현재 TransactionInfo 를 넣고, 이전 것을 자기 안에 보관
               = 중첩 호출을 위한 스택
```

1. 전파 속성을 해석해 실제로 트랜잭션을 여는 것은 [AbstractPlatformTransactionManager.getTransaction](01_AbstractPlatformTransactionManager.getTransaction/README.md)이다.

## 결과가 쓰이는 곳

```text
 TransactionStatus
      --> commitTransactionAfterReturning / completeTransactionAfterThrowing 의 인자
      --> 애플리케이션 코드에서 TransactionAspectSupport.currentTransactionStatus()
          --> setRollbackOnly() 로 "커밋하지 마라" 표시 가능

 ThreadLocal 에 걸린 TransactionInfo
      --> 중첩된 @Transactional 메서드가 자기 위에 쌓인다
      --> cleanupTransactionInfo 가 pop 하며 이전 것으로 복원

 txAttr 이 null 일 때 만들어지는 빈 TransactionInfo
      --> hasTransaction() == false
      --> 커밋/롤백 단계가 아무 일도 하지 않는다
```

## 하위 메서드

- [01 AbstractPlatformTransactionManager.getTransaction](01_AbstractPlatformTransactionManager.getTransaction/README.md)
