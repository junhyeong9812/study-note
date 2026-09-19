# TransactionSynchronization

상위: [Spring 트랜잭션](../../README.md) / [spi](../README.md)

트랜잭션 진행 단계마다 불리는 콜백이다. 커밋 직전 플러시, 커밋 후 캐시 무효화나 이벤트 발행처럼 "트랜잭션 경계에 맞춰야 하는 일"을 여기에 건다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.support` / `TransactionSynchronization.java` L45-L189 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/support/TransactionSynchronization.java#L45-L189))

```java
// TransactionSynchronization.java L45-L189
public interface TransactionSynchronization extends Ordered, Flushable {

    int STATUS_COMMITTED = 0;

    int STATUS_ROLLED_BACK = 1;

    int STATUS_UNKNOWN = 2;

    @Override
    default int getOrder() {
        return Ordered.LOWEST_PRECEDENCE;
    }

    default void suspend() {
    }

    default void resume() {
    }

    @Override
    default void flush() {
    }

    default void savepoint(Object savepoint) {
    }

    default void savepointRollback(Object savepoint) {
    }

    default void beforeCommit(boolean readOnly) {
    }

    default void beforeCompletion() {
    }

    default void afterCommit() {
    }

    default void afterCompletion(int status) {
    }

}
```

## 흐름에서 불리는 자리

```text
 processCommit
   prepareForCommit --> beforeCommit --> beforeCompletion
     --> (doCommit) --> afterCommit --> afterCompletion(STATUS_COMMITTED)
 processRollback
   beforeCompletion --> (doRollback) --> afterCompletion(STATUS_ROLLED_BACK)
 suspend / resume 시에도 콜백이 있다
```

- [commit](../../01_TransactionAspectSupport.invokeWithinTransaction/02_TransactionAspectSupport.commitTransactionAfterReturning/01_AbstractPlatformTransactionManager.commit/README.md)
- [rollback](../../01_TransactionAspectSupport.invokeWithinTransaction/03_TransactionAspectSupport.completeTransactionAfterThrowing/01_AbstractPlatformTransactionManager.rollback/README.md)

## 구현 계층

```text
 등록
   TransactionSynchronizationManager.registerSynchronization(sync)
   (동기화가 활성화된 트랜잭션 안에서만 가능)

 대표 사용처
   TransactionalApplicationListenerSynchronization  @TransactionalEventListener
     (리스너 쪽은 TransactionalApplicationListenerMethodAdapter)
   DataSourceUtils / EntityManagerFactoryUtils     커넥션 반납, 세션 정리
   사용자 코드                                     커밋 후 외부 시스템 호출

 TransactionSynchronizationManager 가 보관하는 것
   바인딩된 리소스(DataSource -> ConnectionHolder), 동기화 목록,
   현재 트랜잭션 이름/읽기 전용/격리 수준/활성 여부
```
