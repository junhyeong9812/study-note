# ExchangeFunction

상위: [Spring HTTP 클라이언트](../../README.md) / [spi](../README.md)

리액티브 클라이언트에서 "요청 하나를 응답 하나로 바꾸는 함수"다. 필터는 이 함수를 감싸는 방식으로 끼어든다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive.function.client` / `ExchangeFunction.java` L42-L68 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/client/ExchangeFunction.java#L42-L68))

```java
// ExchangeFunction.java L42-L68
public interface ExchangeFunction {

    Mono<ClientResponse> exchange(ClientRequest request);

    default ExchangeFunction filter(ExchangeFilterFunction filter) {
        return filter.apply(this);
    }

}
```

`spring-webflux` / `org.springframework.web.reactive.function.client` / `ExchangeFilterFunction.java` L35-L98 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/client/ExchangeFilterFunction.java#L35-L98))

```java
// ExchangeFilterFunction.java L35-L98
public interface ExchangeFilterFunction {

    Mono<ClientResponse> filter(ClientRequest request, ExchangeFunction next);

    default ExchangeFilterFunction andThen(ExchangeFilterFunction afterFilter) {
        Assert.notNull(afterFilter, "ExchangeFilterFunction must not be null");
        return (request, next) ->
                filter(request, afterRequest -> afterFilter.filter(afterRequest, next));
    }

    default ExchangeFunction apply(ExchangeFunction exchange) {
        Assert.notNull(exchange, "ExchangeFunction must not be null");
        return request -> this.filter(request, exchange);
    }

    static ExchangeFilterFunction ofRequestProcessor(Function<ClientRequest, Mono<ClientRequest>> processor) {
        Assert.notNull(processor, "ClientRequest Function must not be null");
        return (request, next) -> processor.apply(request).flatMap(next::exchange);
    }

    static ExchangeFilterFunction ofResponseProcessor(Function<ClientResponse, Mono<ClientResponse>> processor) {
        Assert.notNull(processor, "ClientResponse Function must not be null");
        return (request, next) -> next.exchange(request).flatMap(processor);
    }

}
```

## 흐름에서 불리는 자리

```text
 DefaultWebClient.exchange L462
   finalFilterFunction.apply(exchangeFunction).exchange(request)
     필터가 ExchangeFunction 을 감싸 새 ExchangeFunction 을 만든다
 ExchangeFunctions.exchange
   커넥터에 위임해 실제 전송
```

- [DefaultWebClient.exchange](../../02_DefaultWebClient.exchange/README.md)
- [ExchangeFunctions.exchange](../../02_DefaultWebClient.exchange/01_ExchangeFunctions.exchange/README.md)

## 구현 계층

```text
 ExchangeFunction
   +-- ExchangeFunctions.DefaultExchangeFunction   커넥터 호출
   +-- (필터로 감싼 익명 구현)

 ExchangeFilterFunction
   filter(request, next) 형태
   andThen 으로 체인 구성
   기본 제공: ExchangeFilterFunctions.basicAuthentication, limitResponseSize
   자주 쓰는 용도: 토큰 주입, 재시도, 로깅, 관측
```
