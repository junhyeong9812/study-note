# HandlerAdapter

상위: [Spring WebFlux 요청 처리](../../README.md) / [spi](../README.md)

찾은 핸들러를 실제로 호출하는 방법을 감춘다. 결과는 `Mono<HandlerResult>`이고, 일부 어댑터는 `DispatchExceptionHandler`도 함께 구현해 예외 복구를 제공한다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive` / `HandlerAdapter.java` L39-L73 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/HandlerAdapter.java#L39-L73))

```java
// HandlerAdapter.java L39-L73
public interface HandlerAdapter {

    boolean supports(Object handler);

    Mono<HandlerResult> handle(ServerWebExchange exchange, Object handler);

}
```

## 흐름에서 불리는 자리

```text
 DispatcherHandler.handleRequestWith L201
   supports(handler) 가 true 인 첫 어댑터
   adapter.handle(exchange, handler) --> Mono<HandlerResult>
 DispatcherHandler.handleResultMono L162
   어댑터가 DispatchExceptionHandler 이면 onErrorResume 으로 엮는다
```

- [RequestMappingHandlerAdapter.handle](../../02_DispatcherHandler.handle/01_RequestMappingHandlerAdapter.handle/README.md)
- [DispatcherHandler.handle](../../02_DispatcherHandler.handle/README.md)

## 구현 계층

```text
 HandlerAdapter
   +-- RequestMappingHandlerAdapter     HandlerMethod (@RequestMapping)
   +-- HandlerFunctionAdapter           HandlerFunction (함수형)
   +-- SimpleHandlerAdapter             WebHandler 를 핸들러로 등록한 경우
   +-- WebSocketHandlerAdapter          WebSocketHandler

 DispatchExceptionHandler
   handleError(exchange, ex) -> Mono<HandlerResult>
   RequestMappingHandlerAdapter 가 @ExceptionHandler 로 구현
```
