# R2dbcTransactionManager.doBegin

상위: [Spring R2DBC](../README.md)

리액티브 트랜잭션을 여는 자리다. 하는 일은 `DataSourceTransactionManager`와 같지만, 반환이 `void`가 아니라 `Mono<Void>`이고 바인딩 대상이 스레드가 아니라 구독 컨텍스트다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.connection` / `R2dbcTransactionManager.java` L183-L232 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/connection/R2dbcTransactionManager.java#L183-L232))

```java
// R2dbcTransactionManager.java L183-L232
protected Mono<Void> doBegin(TransactionSynchronizationManager synchronizationManager, Object transaction,
        TransactionDefinition definition) {

    ConnectionFactoryTransactionObject txObject = (ConnectionFactoryTransactionObject) transaction;

    if (definition.getPropagationBehavior() == TransactionDefinition.PROPAGATION_NESTED &&
            txObject.isTransactionActive()) {
        return txObject.createSavepoint();
    }

    return Mono.defer(() -> {
        Mono<Connection> connectionMono;

        if (!txObject.hasConnectionHolder() || txObject.getConnectionHolder().isSynchronizedWithTransaction()) {
            Mono<Connection> newCon = Mono.from(obtainConnectionFactory().create());
            connectionMono = newCon.doOnNext(connection -> {
                if (logger.isDebugEnabled()) {
                    logger.debug("Acquired Connection [" + connection + "] for R2DBC transaction");
                }
                txObject.setConnectionHolder(new ConnectionHolder(connection), true);
            });
        }
        else {
            txObject.getConnectionHolder().setSynchronizedWithTransaction(true);
            connectionMono = Mono.just(txObject.getConnectionHolder().getConnection());
        }

        return connectionMono.flatMap(con -> doBegin(con, txObject, definition)
                .then(prepareTransactionalConnection(con, definition))
                .doOnSuccess(v -> {
                    txObject.getConnectionHolder().setTransactionActive(true);
                    Duration timeout = determineTimeout(definition);
                    if (!timeout.isNegative() && !timeout.isZero()) {
                        txObject.getConnectionHolder().setTimeoutInMillis(timeout.toMillis());
                    }
                    // Bind the connection holder to the thread.
                    if (txObject.isNewConnectionHolder()) {
                        synchronizationManager.bindResource(obtainConnectionFactory(), txObject.getConnectionHolder());
                    }
                }).onErrorResume(ex -> {
                    if (txObject.isNewConnectionHolder()) {
                        return ConnectionFactoryUtils.releaseConnection(con, obtainConnectionFactory())
                                .doOnTerminate(() -> txObject.setConnectionHolder(null, false))
                                .then(Mono.error(ex));
                    }
                    return Mono.error(ex);
                })).onErrorMap(ex -> new CannotCreateTransactionException(
                        "Could not open R2DBC Connection for transaction", ex));
    }).then();
}
```

실제 시작은 드라이버에게 맡긴다.

`spring-r2dbc` / `org.springframework.r2dbc.connection` / `R2dbcTransactionManager.java` L234-L243 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/connection/R2dbcTransactionManager.java#L234-L243))

```java
// R2dbcTransactionManager.java L234-L243
private Mono<Void> doBegin(
        Connection con, ConnectionFactoryTransactionObject transaction, TransactionDefinition definition) {

    transaction.setMustRestoreAutoCommit(con.isAutoCommit());
    io.r2dbc.spi.TransactionDefinition transactionDefinition = createTransactionDefinition(definition);
    if (logger.isDebugEnabled()) {
        logger.debug("Starting R2DBC transaction on Connection [" + con + "] using [" + transactionDefinition + "]");
    }
    return Mono.from(con.beginTransaction(transactionDefinition));
}
```

## 동작 흐름

```text
 doBegin(동기화 관리자, transaction, definition)
 |
 +-- L188 전파가 NESTED 이고 이미 트랜잭션이 활성이면
 |        --> L190 createSavepoint(). 새 트랜잭션을 열지 않는다
 |
 | L193 Mono.defer(...)  구독 시점까지 아무것도 하지 않는다
 |
 +-- L196 커넥션 홀더가 없거나 이미 동기화된 것이면
 |        L197 팩토리에서 새 커넥션을 받는다
 |        L202 새 홀더를 트랜잭션 객체에 설정 (isNewConnectionHolder = true)
 |      그 밖이면
 |        L206 기존 홀더를 동기화 표시하고 그 커넥션을 쓴다
 |
 +-- L210 doBegin(커넥션, 트랜잭션 객체, 정의)
 |        L237 원래 autoCommit 값을 기억해 둔다 (복원용)
 |        L238 createTransactionDefinition 으로 격리 수준/읽기 전용/타임아웃을 담고
 |        L242 con.beginTransaction(정의)  드라이버가 실제로 연다
 |
 | L211 prepareTransactionalConnection(커넥션, 정의)
 |
 +-- L212 성공하면
 |        L213 홀더에 트랜잭션 활성 표시
 |        L216 타임아웃이 있으면 밀리초로 기록
 |        L220 새로 만든 홀더라면 팩토리를 키로 구독 컨텍스트에 바인딩
 |
 +-- L222 실패하면
 |        새로 만든 홀더였다면 커넥션을 반납하고 홀더를 비운 뒤 오류 전파
 |
 +-- L229 어떤 오류든 CannotCreateTransactionException 으로 감싼다
```

```text
 JDBC 와 다른 점

 커넥션 획득   blocking getConnection()   -->  Mono.from(factory.create())
 autoCommit    con.setAutoCommit(false)   -->  드라이버의 beginTransaction(정의)
 격리 수준     커넥션에 직접 설정          -->  TransactionDefinition 에 담아 전달
 바인딩 대상   ThreadLocal                -->  구독 컨텍스트
 반환          void (끝나면 열려 있다)     -->  Mono<Void> (구독해야 열린다)
```

## 결과가 쓰이는 곳

```text
 바인딩된 ConnectionHolder
      --> 같은 체인의 DatabaseClient 호출이 doGetConnection 으로 이것을 찾는다
      --> 여러 쿼리가 한 트랜잭션, 한 커넥션에서 돈다

 isNewConnectionHolder
      --> 이 트랜잭션이 직접 연 커넥션인지 표시한다
      --> 정리 단계에서 닫을지, 바깥에 돌려줄지를 이 값으로 정한다

 mustRestoreAutoCommit
      --> 커넥션을 풀에 돌려주기 전에 원래 autoCommit 으로 되돌린다

 NESTED 세이브포인트
      --> 중첩 트랜잭션은 새 커넥션 없이 세이브포인트로 처리한다
      --> 드라이버가 세이브포인트를 지원해야 한다
```

전파와 롤백 규칙 같은 공통 골격은 [트랜잭션](../../transaction/README.md) 흐름에 있다. 다만 그 흐름은 명령형 경로(`PlatformTransactionManager`)이고, 여기는 `ReactiveTransactionManager` 쪽이다.
