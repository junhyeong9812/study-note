# TransactionStatus

상위: [Spring 트랜잭션](../../README.md) / [spi](../README.md)

지금 실행 중인 트랜잭션의 손잡이다. 새 트랜잭션인지, 세이브포인트가 있는지 알려 주고, 롤백 전용 표시를 걸 수 있다.

## 실제 코드

`spring-tx` / `org.springframework.transaction` / `TransactionStatus.java` L40-L71 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/TransactionStatus.java#L40-L71))

```java
// TransactionStatus.java L40-L71
public interface TransactionStatus extends TransactionExecution, SavepointManager, Flushable {

    default boolean hasSavepoint() {
        return false;
    }

    @Override
    default void flush() {
    }

}
```

## 흐름에서 불리는 자리

```text
 getTransaction 이 반환 --> TransactionInfo 에 담겨 ThreadLocal 에 바인딩
 commit / rollback 의 인자
 애플리케이션에서 TransactionAspectSupport.currentTransactionStatus() 로 조회
```

- [createTransactionIfNecessary](../../01_TransactionAspectSupport.invokeWithinTransaction/01_TransactionAspectSupport.createTransactionIfNecessary/README.md)
- [commit](../../01_TransactionAspectSupport.invokeWithinTransaction/02_TransactionAspectSupport.commitTransactionAfterReturning/01_AbstractPlatformTransactionManager.commit/README.md)
- [rollback](../../01_TransactionAspectSupport.invokeWithinTransaction/03_TransactionAspectSupport.completeTransactionAfterThrowing/01_AbstractPlatformTransactionManager.rollback/README.md)

## 구현 계층

```text
 TransactionExecution
   +-- TransactionStatus                     + SavepointManager
   |     +-- DefaultTransactionStatus        AbstractPlatformTransactionManager 가 쓰는 구현
   |     +-- SimpleTransactionStatus

 주요 상태 값
   isNewTransaction()    이 호출이 트랜잭션을 열었나 (참여면 false)
   hasSavepoint()        NESTED 로 세이브포인트를 잡았나
   isRollbackOnly()      로컬/글로벌 롤백 표시
   isCompleted()         커밋/롤백이 끝났나
```
