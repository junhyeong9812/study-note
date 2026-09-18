# PlatformTransactionManager

상위: [Spring 트랜잭션](../../README.md) / [spi](../README.md)

명령형 트랜잭션의 핵심 추상화다. 메서드는 셋뿐이고, 어떤 자원을 쓰는지(JDBC, JPA, JMS)는 구현이 감춘다. 덕분에 `@Transactional` 코드가 자원 종류와 무관해진다.

## 실제 코드

`spring-tx` / `org.springframework.transaction` / `PlatformTransactionManager.java` L47-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/PlatformTransactionManager.java#L47-L120))

```java
// PlatformTransactionManager.java L47-L120
public interface PlatformTransactionManager extends TransactionManager {

    TransactionStatus getTransaction(@Nullable TransactionDefinition definition) throws TransactionException;

    void commit(TransactionStatus status) throws TransactionException;

    void rollback(TransactionStatus status) throws TransactionException;

}
```

## 흐름에서 불리는 자리

```text
 createTransactionIfNecessary --> tm.getTransaction(txAttr)
 commitTransactionAfterReturning --> tm.commit(status)
 completeTransactionAfterThrowing --> tm.rollback(status) 또는 commit
```

- [createTransactionIfNecessary](../../01_TransactionAspectSupport.invokeWithinTransaction/01_TransactionAspectSupport.createTransactionIfNecessary/README.md)
- [getTransaction](../../01_TransactionAspectSupport.invokeWithinTransaction/01_TransactionAspectSupport.createTransactionIfNecessary/01_AbstractPlatformTransactionManager.getTransaction/README.md)

## 구현 계층

```text
 TransactionManager (마커)
   +-- PlatformTransactionManager            명령형
   |     +-- AbstractPlatformTransactionManager     전파/동기화 공통 처리 (템플릿)
   |           +-- DataSourceTransactionManager     JDBC 커넥션
   |           +-- JpaTransactionManager            EntityManager
   |           +-- JtaTransactionManager            분산 트랜잭션
   |           +-- JmsTransactionManager            JMS 세션
   +-- ReactiveTransactionManager             리액티브 (구독 컨텍스트 기반)

 구현이 채우는 템플릿 메서드
   doGetTransaction / isExistingTransaction
   doBegin / doCommit / doRollback / doSuspend / doResume / doSetRollbackOnly
```
