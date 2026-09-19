# HandlerMapping

상위: [Spring WebFlux 요청 처리](../../README.md) / [spi](../README.md)

요청을 처리할 핸들러를 찾는다. MVC와 이름은 같지만 반환 타입이 `Mono<Object>`라 매핑 자체가 비동기일 수 있다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive` / `HandlerMapping.java` L32-L109 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/HandlerMapping.java#L32-L109))

```java
// HandlerMapping.java L32-L109
public interface HandlerMapping {

    String BEST_MATCHING_HANDLER_ATTRIBUTE = HandlerMapping.class.getName() + ".bestMatchingHandler";

    String BEST_MATCHING_PATTERN_ATTRIBUTE = HandlerMapping.class.getName() + ".bestMatchingPattern";

    String PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE = HandlerMapping.class.getName() + ".pathWithinHandlerMapping";

    String URI_TEMPLATE_VARIABLES_ATTRIBUTE = HandlerMapping.class.getName() + ".uriTemplateVariables";

    String MATRIX_VARIABLES_ATTRIBUTE = HandlerMapping.class.getName() + ".matrixVariables";

    String PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE = HandlerMapping.class.getName() + ".producibleMediaTypes";

    String API_VERSION_ATTRIBUTE = HandlerMapping.class.getName() + ".apiVersion";

    Mono<Object> getHandler(ServerWebExchange exchange);

}
```

## 흐름에서 불리는 자리

```text
 DispatcherHandler.handle L145
   Flux.fromIterable(handlerMappings)
     .concatMap(mapping -> mapping.getHandler(exchange))
     .next()                  첫 결과 채택
     .switchIfEmpty(404)
```

- [DispatcherHandler.handle](../../02_DispatcherHandler.handle/README.md)

## 구현 계층

```text
 HandlerMapping
   +-- AbstractHandlerMapping                CORS/버전 처리 공통
   |                                         (getHandler 가 템플릿, 하위는 getHandlerInternal 구현)
         +-- AbstractHandlerMethodMapping<T>
         |     +-- RequestMappingInfoHandlerMapping
         |           +-- RequestMappingHandlerMapping    @RequestMapping
         +-- RouterFunctionMapping                        함수형 라우트
         +-- AbstractUrlHandlerMapping
               +-- SimpleUrlHandlerMapping                정적 리소스, WebSocket

 MVC 와의 차이
   반환이 HandlerExecutionChain 이 아니라 핸들러 객체 하나다
   인터셉터 개념이 없고, 그 자리를 WebFilter 와 결과 처리기가 대신한다
```
