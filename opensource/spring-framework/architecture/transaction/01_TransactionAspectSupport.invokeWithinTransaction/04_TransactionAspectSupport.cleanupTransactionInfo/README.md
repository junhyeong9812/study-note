# TransactionAspectSupport.cleanupTransactionInfo

상위: [TransactionAspectSupport.invokeWithinTransaction](../README.md)

`finally`에서 항상 불리며, 스레드에 걸어 둔 `TransactionInfo`를 이전 것으로 되돌린다. 중첩 호출에서 스택이 어긋나지 않게 하는 장치다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.interceptor` / `TransactionAspectSupport.java` L744-L748 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L744-L748))

```java
// TransactionAspectSupport.java L744-L748
protected void cleanupTransactionInfo(@Nullable TransactionInfo txInfo) {
    if (txInfo != null) {
        txInfo.restoreThreadLocalStatus();
    }
}
```

## 동작 흐름

```text
 cleanupTransactionInfo(txInfo)
 |
 +-- txInfo 가 null --> 아무 일도 안 함
 +-- restoreThreadLocalStatus()
       bindToThread 때 보관해 둔 "이전 TransactionInfo" 를 ThreadLocal 에 복원
       = 스택 pop
```

```text
 중첩 호출에서의 스택

 outer()  @Transactional
   bindToThread(outerInfo)        ThreadLocal = outerInfo (이전 = null)
   |
   inner()  @Transactional        (프록시를 거쳐 호출된 경우)
     bindToThread(innerInfo)      ThreadLocal = innerInfo (이전 = outerInfo)
     ...
     cleanup --> ThreadLocal = outerInfo
   |
   cleanup --> ThreadLocal = null
```

## 결과가 쓰이는 곳

```text
 복원된 ThreadLocal
      --> TransactionAspectSupport.currentTransactionStatus() 가 항상 "지금 실행 중인"
          트랜잭션을 가리키게 한다
      --> 커밋/롤백보다 뒤에 불리므로, 커밋 도중에도 상태 조회가 가능하다

 트랜잭션 리소스(커넥션) 정리와는 별개
      --> 커넥션 해제는 매니저의 cleanupAfterCompletion 이 담당
      --> 이 메서드는 어드바이스 계층의 스택만 정리한다
```

이 메서드는 커밋보다 **먼저** 불린다. `invokeWithinTransaction`의 `finally`가 `commitTransactionAfterReturning`보다 앞에 있기 때문이다. 커밋 중에 예외가 나도 스택은 이미 정리된 상태다.
