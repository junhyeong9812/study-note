# webflux.RouterFunctionMapping.getHandlerInternal

상위: [Spring 함수형 엔드포인트](../README.md)

리액티브 스택의 라우팅 입구다. 하는 일은 서블릿 쪽과 같지만 결과가 `Optional`이 아니라 `Mono`이고, 요청 속성은 서블릿 요청이 아니라 `ServerWebExchange`의 속성 맵에 담긴다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive.function.server.support` / `RouterFunctionMapping.java` L159-L166 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/support/RouterFunctionMapping.java#L159-L166))

```java
// RouterFunctionMapping.java L159-L166
protected Mono<?> getHandlerInternal(ServerWebExchange exchange) {
    if (this.routerFunction == null) {
        return Mono.empty();
    }
    ServerRequest request = ServerRequest.create(exchange, this.messageReaders, getApiVersionStrategy());
    return this.routerFunction.route(request)
            .doOnNext(handler -> setAttributes(exchange.getAttributes(), request, handler));
}
```

`spring-webflux` / `org.springframework.web.reactive.function.server.support` / `RouterFunctionMapping.java` L168-L186 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/support/RouterFunctionMapping.java#L168-L186))

```java
// RouterFunctionMapping.java L168-L186
@SuppressWarnings("unchecked")
private void setAttributes(
        Map<String, Object> attributes, ServerRequest serverRequest, HandlerFunction<?> handlerFunction) {

    attributes.put(RouterFunctions.REQUEST_ATTRIBUTE, serverRequest);
    attributes.put(BEST_MATCHING_HANDLER_ATTRIBUTE, handlerFunction);

    PathPattern matchingPattern = (PathPattern) attributes.get(RouterFunctions.MATCHING_PATTERN_ATTRIBUTE);
    if (matchingPattern != null) {
        attributes.put(BEST_MATCHING_PATTERN_ATTRIBUTE, matchingPattern);
        ServerRequestObservationContext.findCurrent(serverRequest.exchange().getAttributes())
                .ifPresent(context -> context.setPathPattern(matchingPattern.toString()));
    }
    Map<String, String> uriVariables =
            (Map<String, String>) attributes.get(RouterFunctions.URI_TEMPLATE_VARIABLES_ATTRIBUTE);
    if (uriVariables != null) {
        attributes.put(URI_TEMPLATE_VARIABLES_ATTRIBUTE, uriVariables);
    }
}
```

## 동작 흐름

```text
 getHandlerInternal(exchange)
 |
 +-- L160 routerFunction 이 null
 |        --> Mono.empty(). 다음 HandlerMapping 이 시도된다
 |
 | L163 ServerRequest.create(exchange, messageReaders, versionStrategy)
 |        컨버터가 아니라 리액티브 messageReaders 를 넘긴다
 |
 +-- L164 routerFunction.route(request)
        --> Mono<HandlerFunction>
        L165 doOnNext 로 매칭에 성공했을 때만 속성을 채운다

 setAttributes(attributes, serverRequest, handlerFunction)      L169
 |
 | L172 REQUEST_ATTRIBUTE = ServerRequest
 | L173 BEST_MATCHING_HANDLER_ATTRIBUTE = handlerFunction
 |
 +-- L176 MATCHING_PATTERN_ATTRIBUTE 가 있으면
 |        BEST_MATCHING_PATTERN_ATTRIBUTE 에도 복사한다 (PathPattern 객체 그대로)
 |        원 키는 지우지 않는다. 서블릿 쪽은 원 키를 지우고 문자열로 바꿔 담는다
 |        관측 컨텍스트에도 패턴을 알린다
 |
 +-- L183 URI_TEMPLATE_VARIABLES_ATTRIBUTE 가 있으면 표준 키에도 복사한다
```

```text
 서블릿 쪽과 다른 점

 반환      Optional<HandlerFunction>      -->  Mono<HandlerFunction>
 비었을 때 null                            -->  Mono.empty()
 속성 저장 servletRequest.setAttribute      -->  exchange.getAttributes() 맵
 속성 시점 route 직후 바로                  -->  doOnNext, 즉 구독 후 값이 흐를 때
```

## 결과가 쓰이는 곳

```text
 Mono<HandlerFunction>
      --> DispatcherHandler 가 매핑 목록을 concatMap 으로 돌며 첫 값을 취한다
      --> 전부 비면 createNotFoundError --> ResponseStatusException(404)

 REQUEST_ATTRIBUTE
      --> 어댑터가 exchange.getRequiredAttribute 로 꺼낸다
      --> 없으면 IllegalArgumentException 이 난다 (매핑을 거치지 않은 경로)

 속성을 doOnNext 안에서 채우는 이유
      --> 핸들러가 있어야 setAttributes 에 넘길 인자가 생기기 때문이다 (구조상 필연)
```

1. 다음 단계는 [webflux.HandlerFunctionAdapter.handle](../04_webflux.HandlerFunctionAdapter.handle/README.md)이다.

리액티브 요청 처리의 전체 골격은 [WebFlux 요청 처리](../../webflux-request-processing/README.md)에 있다.
