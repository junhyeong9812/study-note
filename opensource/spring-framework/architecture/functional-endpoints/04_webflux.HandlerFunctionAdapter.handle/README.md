# webflux.HandlerFunctionAdapter.handle

상위: [Spring 함수형 엔드포인트](../README.md)

리액티브 쪽 어댑터는 서블릿 쪽보다 훨씬 얇다. 응답 쓰기를 직접 하지 않고 `HandlerResult`로 감싸 결과 처리기에 넘기기 때문이다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive.function.server.support` / `HandlerFunctionAdapter.java` L53-L55 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/support/HandlerFunctionAdapter.java#L53-L55))

```java
// HandlerFunctionAdapter.java L53-L55
public boolean supports(Object handler) {
    return handler instanceof HandlerFunction;
}
```

`spring-webflux` / `org.springframework.web.reactive.function.server.support` / `HandlerFunctionAdapter.java` L58-L63 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/support/HandlerFunctionAdapter.java#L58-L63))

```java
// HandlerFunctionAdapter.java L58-L63
public Mono<HandlerResult> handle(ServerWebExchange exchange, Object handler) {
    HandlerFunction<?> handlerFunction = (HandlerFunction<?>) handler;
    ServerRequest request = exchange.getRequiredAttribute(RouterFunctions.REQUEST_ATTRIBUTE);
    return handlerFunction.handle(request)
            .map(response -> new HandlerResult(handlerFunction, response, HANDLER_FUNCTION_RETURN_TYPE));
}
```

## 동작 흐름

```text
 handle(exchange, handler)
 |
 | L59 handler 를 HandlerFunction 으로 캐스팅
 |
 | L60 exchange.getRequiredAttribute(RouterFunctions.REQUEST_ATTRIBUTE)
 |        매핑 단계가 담아 둔 ServerRequest
 |        없으면 IllegalArgumentException
 |
 +-- L61 handlerFunction.handle(request)
        --> Mono<ServerResponse>
        L62 map 으로 HandlerResult(handlerFunction, response, 반환 타입) 생성
            아직 아무것도 쓰지 않았다. 조립만 했다
```

```text
 supports(handler)                              L53
   handler instanceof HandlerFunction

 HANDLER_FUNCTION_RETURN_TYPE
   ServerResponse 를 담은 Mono 라는 사실을 결과 처리기에 알려 주는 고정 타입
```

## 결과가 쓰이는 곳

```text
 HandlerResult
      --> DispatcherHandler 가 resultHandlers 목록에서 supports 가 참인 것을 찾는다
      --> ServerResponseResultHandler 가 반환값이 ServerResponse 인지 보고 맡는다

 응답 쓰기를 여기서 하지 않는 이유
      --> 리액티브 스택은 "무엇을 쓸지"와 "언제 쓸지"를 분리한다
      --> 어댑터는 파이프라인을 조립하고, 실제 쓰기는 구독이 일어나는 맨 끝에서 벌어진다

 서블릿 쪽과 비교
      --> 서블릿 어댑터는 같은 메서드 안에서 writeTo 까지 불러 끝낸다
      --> 리액티브는 한 단계를 더 두어 결과 처리기 목록으로 확장 지점을 만든다
```

1. 다음 단계는 [webflux.ServerResponseResultHandler.handleResult](../05_webflux.ServerResponseResultHandler.handleResult/README.md)다.

애노테이션 컨트롤러가 같은 좌석을 채우는 경로는 [WebFlux의 RequestMappingHandlerAdapter.handle](../../webflux-request-processing/02_DispatcherHandler.handle/01_RequestMappingHandlerAdapter.handle/README.md)에 있다.
