# ConnectionFactoryUtils.doGetConnection

상위: [DefaultDatabaseClient.inConnection](../README.md)

"지금 이 구독에 묶인 커넥션이 있는가"를 답한다. JDBC의 `DataSourceUtils.getConnection`과 같은 역할이고, 다른 점은 스레드 로컬이 아니라 리액터 컨텍스트에서 찾는다는 것뿐이다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.connection` / `ConnectionFactoryUtils.java` L114-L152 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/connection/ConnectionFactoryUtils.java#L114-L152))

```java
// ConnectionFactoryUtils.java L114-L152
public static Mono<Connection> doGetConnection(ConnectionFactory connectionFactory) {
    Assert.notNull(connectionFactory, "ConnectionFactory must not be null");
    return TransactionSynchronizationManager.forCurrentTransaction().flatMap(synchronizationManager -> {

        ConnectionHolder conHolder = (ConnectionHolder) synchronizationManager.getResource(connectionFactory);
        if (conHolder != null && (conHolder.hasConnection() || conHolder.isSynchronizedWithTransaction())) {
            conHolder.requested();
            if (!conHolder.hasConnection()) {
                return fetchConnection(connectionFactory).doOnNext(conHolder::setConnection);
            }
            return Mono.just(conHolder.getConnection());
        }
        // Else we either got no holder or an empty thread-bound holder here.

        Mono<Connection> con = fetchConnection(connectionFactory);
        if (synchronizationManager.isSynchronizationActive()) {
            return con.flatMap(connection -> Mono.just(connection).doOnNext(conn -> {
                // Use same Connection for further R2DBC actions within the transaction.
                // Thread-bound object will get removed by synchronization at transaction completion.
                ConnectionHolder holderToUse = conHolder;
                if (holderToUse == null) {
                    holderToUse = new ConnectionHolder(conn);
                }
                else {
                    holderToUse.setConnection(conn);
                }
                holderToUse.requested();
                synchronizationManager.registerSynchronization(
                        new ConnectionSynchronization(holderToUse, connectionFactory));
                holderToUse.setSynchronizedWithTransaction(true);
                if (holderToUse != conHolder) {
                    synchronizationManager.bindResource(connectionFactory, holderToUse);
                }
            })      // Unexpected exception from external delegation call -> close Connection and rethrow.
            .onErrorResume(ex -> releaseConnection(connection, connectionFactory).then(Mono.error(ex))));
        }
        return con;
    }).onErrorResume(NoTransactionException.class, ex -> Mono.from(connectionFactory.create()));
}
```

## 동작 흐름

```text
 doGetConnection(connectionFactory)
 |
 | L116 TransactionSynchronizationManager.forCurrentTransaction()
 |        리액터 구독 컨텍스트에서 동기화 관리자를 꺼낸다
 |        트랜잭션이 없으면 NoTransactionException 으로 끝난다
 |
 +-- [A] L118 커넥션 팩토리를 키로 ConnectionHolder 를 찾는다
 |    |
 |    +-- L119 홀더가 있고 커넥션을 들고 있거나 트랜잭션과 동기화돼 있으면
 |          L120 requested()  참조 카운트 증가
 |          L121 커넥션이 아직 없으면 지금 받아 홀더에 넣는다
 |          L124 있으면 그대로 반환
 |
 +-- [B] L128 홀더가 없거나 비어 있으면 팩토리에서 새로 받는다
 |    |
 |    +-- L129 동기화가 켜져 있으면 (트랜잭션 안이라는 뜻)
 |    |     L133 홀더를 만들거나 기존 홀더에 커넥션을 넣고
 |    |     L141 ConnectionSynchronization 을 등록해 종료 시 정리되게 하고
 |    |     L143 동기화 표시 후 L145 팩토리를 키로 바인딩
 |    |     L148 도중 오류가 나면 커넥션을 반납하고 오류를 전파
 |    |
 |    +-- L150 동기화가 꺼져 있으면 받은 커넥션을 그대로 반환
 |
 +-- L151 NoTransactionException 이면 팩토리에서 새 커넥션을 만들어 쓴다
        = 트랜잭션 밖 호출은 매번 새 커넥션이다
```

```text
 어디에 묶이는가

 JDBC   ThreadLocal <- 스레드가 바뀌면 잃어버린다
 R2DBC  리액터 구독 컨텍스트 <- 스레드가 바뀌어도 따라간다

 리액티브 파이프라인은 연산자마다 스레드가 바뀔 수 있다
 그래서 스레드 로컬을 쓸 수 없고, 컨텍스트가 그 자리를 대신한다
```

## 결과가 쓰이는 곳

```text
 반환한 Mono<Connection>
      --> inConnection 이 이것을 구독해 콜백에 넘긴다
      --> 트랜잭션 안이면 같은 커넥션이 체인 내내 재사용된다

 참조 카운트
      --> 같은 커넥션을 여러 곳에서 요청한 횟수를 센다
      --> 반납은 카운트만 줄인다. 실제 close 는 카운트가 0 이 된 뒤
          ConnectionSynchronization 의 완료 콜백에서 일어난다

 등록한 ConnectionSynchronization
      --> 트랜잭션 종료 시 바인딩 해제와 커넥션 반납을 수행한다

 NoTransactionException 경로
      --> 트랜잭션 없이 쓰는 DatabaseClient 호출이 여기로 온다
      --> 호출마다 커넥션을 새로 만들고 체인이 끝나면 닫는다
```

블로킹 쪽 같은 자리는 [DataSourceUtils.getConnection](../../../jdbc/01_JdbcTemplate.execute/01_DataSourceUtils.getConnection/README.md)에 있다. 커넥션을 묶는 쪽은 [R2dbcTransactionManager.doBegin](../../03_R2dbcTransactionManager.doBegin/README.md)이다.
