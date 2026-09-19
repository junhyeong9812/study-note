# ConnectionAccessor

상위: [Spring R2DBC](../../README.md) / [spi](../README.md)

"커넥션 하나를 빌려 콜백을 실행하고, 끝나면 반납한다"는 계약이다. 메서드가 둘뿐인데 하나는 `Mono`, 하나는 `Flux`용이다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.core` / `ConnectionAccessor.java` L43-L69 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/core/ConnectionAccessor.java#L43-L69))

```java
// ConnectionAccessor.java L43-L69
public interface ConnectionAccessor {

    <T> Mono<T> inConnection(Function<Connection, Mono<T>> action);

    <T> Flux<T> inConnectionMany(Function<Connection, Flux<T>> action);

}
```

## 흐름에서 불리는 자리

```text
 DefaultFetchSpec.one() / first() / all()  --> inConnectionMany
   one() 과 first() 는 all() 을 줄인 것이다 (singleOrEmpty, next)
 DefaultFetchSpec.rowsUpdated()           --> inConnection
 사용자 코드가 직접 부르기도 한다 (드라이버 API 를 직접 쓸 때)
```

- [DefaultDatabaseClient.inConnection](../../02_DefaultDatabaseClient.inConnection/README.md)

## 구현 계층

```text
 ConnectionAccessor
   +-- DatabaseClient (인터페이스가 이것을 확장한다)
         +-- DefaultDatabaseClient
```

## 결과가 쓰이는 곳

```text
 커넥션 수명
      --> 콜백이 만든 Publisher 가 종료되거나 구독이 취소되면 반납된다
      --> javadoc 이 "커넥션 자원을 클로저 밖으로 내보내지 말라"고 못박는다
          내보내면 이미 반납된 커넥션을 쓰게 된다

 두 메서드로 나뉜 이유
      --> 반환 타입이 Mono 인지 Flux 인지에 따라 종료 시점 판정이 다르다
      --> 한 행만 읽는 경우와 스트림으로 흘리는 경우를 구분한다

 예외
      --> 콜백 안의 R2dbcException 은 DataAccessException 으로 번역돼 나온다
```
