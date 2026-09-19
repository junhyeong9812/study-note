# DefaultDatabaseClient.inConnection

상위: [Spring R2DBC](../README.md)

커넥션의 수명을 구독에 묶는 자리다. JDBC의 `try-finally`에 해당하는 일을 리액터의 `Mono.usingWhen`이 대신한다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.core` / `DefaultDatabaseClient.java` L116-L135 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/core/DefaultDatabaseClient.java#L116-L135))

```java
// DefaultDatabaseClient.java L116-L135
public <T> Mono<T> inConnection(Function<Connection, Mono<T>> action) {
    Assert.notNull(action, "Callback object must not be null");
    Mono<ConnectionCloseHolder> connectionMono = getConnection().map(
            connection -> new ConnectionCloseHolder(connection, this::closeConnection));

    return Mono.usingWhen(connectionMono, connectionCloseHolder -> {
        // Create close-suppressing Connection proxy
        Connection connectionToUse = createConnectionProxy(connectionCloseHolder.connection);
                try {
                    return action.apply(connectionToUse);
                }
                catch (R2dbcException ex) {
                    String sql = getSql(action);
                    return Mono.error(ConnectionFactoryUtils.convertR2dbcException("doInConnection", sql, ex));
                }
            }, ConnectionCloseHolder::close, (it, err) -> it.close(),
            ConnectionCloseHolder::close)
            .onErrorMap(R2dbcException.class,
                    ex -> ConnectionFactoryUtils.convertR2dbcException("execute", getSql(action), ex));
}
```

## 동작 흐름

```text
 inConnection(action)
 |
 | L118 getConnection()  --> ConnectionCloseHolder 로 감싼다
 |        닫는 방법(this::closeConnection)을 함께 들고 다니는 상자다
 |
 +-- L121 Mono.usingWhen(리소스, 사용, 완료, 오류, 취소)
 |      L123 close 를 막은 커넥션 프록시를 만든다
 |             콜백이 실수로 닫아도 파이프라인이 깨지지 않게 한다
 |      L125 action.apply(프록시)  사용자 콜백 실행
 |      L127 즉시 던져진 R2dbcException 은 그 자리에서 번역 (L129)
 |      L131-L132 정상/오류/취소 어느 쪽으로 끝나도 ConnectionCloseHolder::close
 |
 +-- L133 파이프라인을 흐르는 R2dbcException 도 onErrorMap 으로 번역
        convertR2dbcException("execute", SQL, ex)
```

```text
 usingWhen 이 보장하는 것

 정상 종료   --> close
 오류 종료   --> close 후 오류 전파
 구독 취소   --> close
 = try-with-resources 와 같은 보장을 비동기 경계 너머까지 유지한다

 JDBC 와의 차이
   JDBC  메서드가 반환되는 시점에 finally 가 돈다
   R2DBC 구독이 끝나는 시점에 돈다. 메서드 반환은 아무 의미가 없다
```

1. 커넥션을 실제로 얻는 규칙은 [ConnectionFactoryUtils.doGetConnection](01_ConnectionFactoryUtils.doGetConnection/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 반환한 Mono<T>
      --> FetchSpec 의 rowsUpdated() 가 이것을 돌려준다
      --> one() / first() / all() 은 L138 의 inConnectionMany 쪽을 탄다
      --> 구독되기 전에는 커넥션도 얻지 않는다

 close 억제 프록시
      --> 콜백이 커넥션을 닫아도 무시된다
      --> 닫는 책임은 usingWhen 한 곳에만 있다

 예외 번역이 두 곳인 이유
      --> 콜백이 동기적으로 던진 예외(L127-L129)와
          파이프라인을 흐르며 난 예외(L134)는 경로가 다르다
      --> 둘 다 잡아야 호출자가 보는 예외 타입이 일관된다

 여러 행을 흘리는 경우
      --> inConnectionMany 가 같은 구조를 Flux 로 한다 (L138)
      --> all() 이 그쪽을 쓴다
```

블로킹 쪽에서 같은 보장을 하는 자리는 [JdbcTemplate.execute의 finally](../../jdbc/01_JdbcTemplate.execute/README.md)에 있다.

## 하위 메서드

- [01 ConnectionFactoryUtils.doGetConnection](01_ConnectionFactoryUtils.doGetConnection/README.md)
