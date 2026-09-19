# R2dbcTransactionManager.doCommit

상위: [Spring R2DBC](../README.md)

커밋도 값이 아니라 `Mono`다. 구독되기 전에는 커밋이 일어나지 않는다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.connection` / `R2dbcTransactionManager.java` L297-L306 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/connection/R2dbcTransactionManager.java#L297-L306))

```java
// R2dbcTransactionManager.java L297-L306
protected Mono<Void> doCommit(TransactionSynchronizationManager synchronizationManager,
        GenericReactiveTransaction status) {

    ConnectionFactoryTransactionObject txObject = (ConnectionFactoryTransactionObject) status.getTransaction();
    if (status.isDebug()) {
        logger.debug("Committing R2DBC transaction on Connection [" +
                txObject.getConnectionHolder().getConnection() + "]");
    }
    return txObject.commit().onErrorMap(R2dbcException.class, ex -> translateException("R2DBC commit", ex));
}
```

롤백도 대칭이다.

`spring-r2dbc` / `org.springframework.r2dbc.connection` / `R2dbcTransactionManager.java` L309-L318 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/connection/R2dbcTransactionManager.java#L309-L318))

```java
// R2dbcTransactionManager.java L309-L318
protected Mono<Void> doRollback(TransactionSynchronizationManager synchronizationManager,
        GenericReactiveTransaction status) {

    ConnectionFactoryTransactionObject txObject = (ConnectionFactoryTransactionObject) status.getTransaction();
    if (status.isDebug()) {
        logger.debug("Rolling back R2DBC transaction on Connection [" +
                txObject.getConnectionHolder().getConnection() + "]");
    }
    return txObject.rollback().onErrorMap(R2dbcException.class, ex -> translateException("R2DBC rollback", ex));
}
```

## 동작 흐름

```text
 doCommit(동기화 관리자, status)
 |
 | L300 트랜잭션 객체에서 ConnectionHolder 를 꺼낸다
 |
 +-- L305 txObject.commit()
        내부적으로 con.commitTransaction() 을 Mono 로 감싼다
        단 세이브포인트로 참여 중이면 빈 Mono 를 돌려주고 커밋하지 않는다
        R2dbcException 이면 onErrorMap 으로 번역
          translateException("R2DBC commit", ex)
          --> DataAccessException 으로 바뀌어 전파된다

 doRollback 도 같은 모양
        L317 txObject.rollback() + translateException("R2DBC rollback", ex)
```

```text
 언제 실제로 커밋되는가

 명령형   commit() 이 반환되면 커밋이 끝나 있다
 리액티브 doCommit 이 돌려준 Mono 를 트랜잭션 매니저가 체인에 이어 붙이고,
          그 체인이 구독될 때 커밋이 실행된다
          = 애플리케이션이 결과 Publisher 를 구독하지 않으면
            쿼리도 커밋도 일어나지 않는다
```

## 결과가 쓰이는 곳

```text
 반환한 Mono<Void>
      --> AbstractReactiveTransactionManager 가 정리 단계와 이어 붙인다
      --> 이어서 doCleanupAfterCompletion 이 바인딩을 풀고 커넥션을 반납한다

 번역된 예외
      --> 커밋 실패가 DataAccessException 으로 올라간다
      --> 제약 위반은 DataIntegrityViolationException 으로 드러난다

 커밋 이후 커넥션
      --> 새로 연 커넥션이면 반납하고, autoCommit 을 원래대로 되돌린다
      --> 바깥에서 받은 커넥션이면 그대로 둔다
```

예외가 어떤 타입으로 번역되는지는 [convertR2dbcException](../05_ConnectionFactoryUtils.convertR2dbcException/README.md)에 있다.
