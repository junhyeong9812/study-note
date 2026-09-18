# TransactionDefinition

상위: [Spring 트랜잭션](../../README.md) / [spi](../README.md)

트랜잭션을 어떻게 열지 기술한다. 전파, 격리 수준, 타임아웃, 읽기 전용, 이름의 다섯 가지다. `@Transactional`의 속성이 결국 이 인터페이스의 값이 된다.

## 실제 코드

`spring-tx` / `org.springframework.transaction` / `TransactionDefinition.java` L44-L293 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/TransactionDefinition.java#L44-L293))

```java
// TransactionDefinition.java L44-L293
public interface TransactionDefinition {

    int PROPAGATION_REQUIRED = 0;

    int PROPAGATION_SUPPORTS = 1;

    int PROPAGATION_MANDATORY = 2;

    int PROPAGATION_REQUIRES_NEW = 3;

    int PROPAGATION_NOT_SUPPORTED = 4;

    int PROPAGATION_NEVER = 5;

    int PROPAGATION_NESTED = 6;

    int ISOLATION_DEFAULT = -1;

    int ISOLATION_READ_UNCOMMITTED = 1;  // same as java.sql.Connection.TRANSACTION_READ_UNCOMMITTED;

    int ISOLATION_READ_COMMITTED = 2;  // same as java.sql.Connection.TRANSACTION_READ_COMMITTED;

    int ISOLATION_REPEATABLE_READ = 4;  // same as java.sql.Connection.TRANSACTION_REPEATABLE_READ;

    int ISOLATION_SERIALIZABLE = 8;  // same as java.sql.Connection.TRANSACTION_SERIALIZABLE;

    int TIMEOUT_DEFAULT = -1;

    default int getPropagationBehavior() {
        return PROPAGATION_REQUIRED;
    }

    default int getIsolationLevel() {
        return ISOLATION_DEFAULT;
    }

    default int getTimeout() {
        return TIMEOUT_DEFAULT;
    }

    default boolean isReadOnly() {
        return false;
    }

    default @Nullable String getName() {
        return null;
    }

    // Static builder methods

    static TransactionDefinition withDefaults() {
        return StaticTransactionDefinition.INSTANCE;
    }

}
```

## 흐름에서 불리는 자리

```text
 TransactionAttributeSource 가 @Transactional 을 읽어 TransactionAttribute 생성
   --> invokeWithinTransaction L338 의 txAttr
   --> getTransaction(definition) 의 인자로 전달
   --> 전파 분기, 격리 수준 적용, 타임아웃 설정의 근거
```

- [invokeWithinTransaction](../../01_TransactionAspectSupport.invokeWithinTransaction/README.md)
- [getTransaction](../../01_TransactionAspectSupport.invokeWithinTransaction/01_TransactionAspectSupport.createTransactionIfNecessary/01_AbstractPlatformTransactionManager.getTransaction/README.md)

## 구현 계층

```text
 TransactionDefinition
   +-- TransactionAttribute                    + rollbackOn(예외) 판정
   |     +-- DefaultTransactionAttribute       언체크 예외면 롤백
   |     |     +-- RuleBasedTransactionAttribute   rollbackFor / noRollbackFor 규칙
   |     +-- DelegatingTransactionAttribute    이름만 바꿔 감싸기 (조인포인트 이름 주입)
   +-- DefaultTransactionDefinition            프로그래밍 방식에서 직접 구성

 전파 7종
   REQUIRED(기본) SUPPORTS MANDATORY REQUIRES_NEW NOT_SUPPORTED NEVER NESTED
```
