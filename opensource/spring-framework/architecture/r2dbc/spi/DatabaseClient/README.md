# DatabaseClient

상위: [Spring R2DBC](../../README.md) / [spi](../README.md)

R2DBC의 진입 표면이다. `JdbcTemplate`이 콜백 중심인 것과 달리, 여기서는 SQL부터 결과까지가 체인으로 이어진다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.core` / `DatabaseClient.java` L63-L70 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/core/DatabaseClient.java#L63-L70))

```java
// DatabaseClient.java L63-L70
public interface DatabaseClient extends ConnectionAccessor {

    ConnectionFactory getConnectionFactory();

```

## 흐름에서 불리는 자리

```text
 databaseClient.sql("...")        --> GenericExecuteSpec
   .bind("id", 42)                   바인딩을 쌓는다
   .map(row -> ...)                  행 매핑 함수를 건다
   .one() / .all() / .rowsUpdated()  Mono 나 Flux 를 만든다
 구독 시점에 실제 실행
```

- [DefaultGenericExecuteSpec.execute](../../01_DefaultGenericExecuteSpec.execute/README.md)

## 구현 계층

```text
 ConnectionAccessor
   +-- DatabaseClient
         +-- DefaultDatabaseClient       유일한 프로덕션 구현
               DefaultGenericExecuteSpec  sql(...) 이 돌려주는 내부 스펙

 만드는 방법
   DatabaseClient.create(connectionFactory)
   DatabaseClient.builder()
     .connectionFactory(cf)
     .bindMarkers(factory)       드라이버 표기 지정
     .namedParameters(true)      :name 표기 사용 여부 (기본 true)
```

## 결과가 쓰이는 곳

```text
 sql(String) 과 sql(Supplier<String>)
      --> Supplier 형태는 SQL 생성을 지연시킨다 (쿼리 빌더 연동)

 getConnectionFactory()
      --> 트랜잭션 매니저와 같은 팩토리를 쓰는지 확인하는 통로
      --> 다르면 같은 트랜잭션에 참여하지 못한다

 반환 타입이 전부 Publisher 라는 점
      --> 호출만으로는 아무 일도 일어나지 않는다
      --> 로그에 SQL 이 안 보인다면 대개 구독을 안 한 것이다
```
