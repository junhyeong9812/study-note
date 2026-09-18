# DispatcherHandler.handle

상위: [Spring WebFlux 요청 처리](../README.md)

리액티브 스택의 요청 처리 본체다. MVC의 `doDispatch`와 같은 일을 하지만, 단계를 순서대로 **실행**하는 대신 `Mono` 연산자로 **연결**한다. 실제 실행은 서버가 구독할 때 일어난다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive` / `DispatcherHandler.java` L136-L151 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/DispatcherHandler.java#L136-L151))

```java
// DispatcherHandler.java L136-L151

@Override
public Mono<Void> handle(ServerWebExchange exchange) {
    if (this.handlerMappings == null) {
        return createNotFoundError();
    }
    if (CorsUtils.isPreFlightRequest(exchange.getRequest())) {
        return handlePreFlight(exchange);
    }
    return Flux.fromIterable(this.handlerMappings)
            .concatMap(mapping -> mapping.getHandler(exchange))
            .next()
            .switchIfEmpty(createNotFoundError())
            .onErrorResume(ex -> handleResultMono(exchange, Mono.error(ex)))
            .flatMap(handler -> handleRequestWith(exchange, handler));
}
```

`spring-webflux` / `org.springframework.web.reactive` / `DispatcherHandler.java` L196-L209 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/DispatcherHandler.java#L196-L209))

```java
// DispatcherHandler.java L196-L209
private Mono<Void> handleRequestWith(ServerWebExchange exchange, Object handler) {
    if (ObjectUtils.nullSafeEquals(exchange.getResponse().getStatusCode(), HttpStatus.FORBIDDEN)) {
        return Mono.empty();  // CORS rejection
    }
    if (this.handlerAdapters != null) {
        for (HandlerAdapter adapter : this.handlerAdapters) {
            if (adapter.supports(handler)) {
                Mono<HandlerResult> resultMono = adapter.handle(exchange, handler);
                return handleResultMono(exchange, resultMono);
            }
        }
    }
    return Mono.error(new IllegalStateException("No HandlerAdapter: " + handler));
}
```

`spring-webflux` / `org.springframework.web.reactive` / `DispatcherHandler.java` L160-L179 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/DispatcherHandler.java#L160-L179))

```java
// DispatcherHandler.java L160-L179
private Mono<Void> handleResultMono(ServerWebExchange exchange, Mono<HandlerResult> resultMono) {
    if (this.handlerAdapters != null) {
        for (HandlerAdapter adapter : this.handlerAdapters) {
            if (adapter instanceof DispatchExceptionHandler exceptionHandler) {
                resultMono = resultMono.onErrorResume(ex2 -> exceptionHandler.handleError(exchange, ex2));
            }
        }
    }
    return resultMono.flatMap(result -> {
        Mono<Void> voidMono = handleResult(exchange, result, "Handler " + result.getHandler());
        DispatchExceptionHandler exceptionHandler = result.getExceptionHandler();
        if (exceptionHandler != null) {
            voidMono = voidMono.onErrorResume(ex ->
                    exceptionHandler.handleError(exchange, ex).flatMap(result2 ->
                            handleResult(exchange, result2, "Exception handler " +
                                    result2.getHandler() + ", error=\"" + ex.getMessage() + "\"")));
        }
        return voidMono;
    });
}
```

`spring-webflux` / `org.springframework.web.reactive` / `DispatcherHandler.java` L181-L194 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/DispatcherHandler.java#L181-L194))

```java
// DispatcherHandler.java L181-L194
private Mono<Void> handleResult(
        ServerWebExchange exchange, HandlerResult handlerResult, String description) {

    if (this.resultHandlers != null) {
        for (HandlerResultHandler resultHandler : this.resultHandlers) {
            if (resultHandler.supports(handlerResult)) {
                description += " [DispatcherHandler]";
                return resultHandler.handleResult(exchange, handlerResult).checkpoint(description);
            }
        }
    }
    return Mono.error(new IllegalStateException(
            "No HandlerResultHandler for " + handlerResult.getReturnValue()));
}
```

## 동작 흐름

```text
 handle(exchange)
 |
 | L139 전략 목록이 없음 --> 404 오류
 | L142 CORS preflight 요청 --> handlePreFlight
 |
 +-- L145 Flux.fromIterable(handlerMappings)
       .concatMap(mapping -> mapping.getHandler(exchange))   순서대로 물어본다
       .next()                                               첫 번째 결과만
       .switchIfEmpty(404 오류)
       .onErrorResume(ex -> handleResultMono(exchange, Mono.error(ex)))
       .flatMap(handler -> handleRequestWith(exchange, handler))
              |
              | L197 응답이 이미 403 (CORS 거부) --> 빈 Mono
              | L201 adapter.supports(handler) 인 첫 어댑터
              |        resultMono = adapter.handle(exchange, handler)
              +-- handleResultMono(exchange, resultMono)
                     |
                     | L162 어댑터 중 DispatchExceptionHandler 인 것들로 onErrorResume 을 감싼다
                     |        = 어댑터가 제공하는 예외 처리 (@ExceptionHandler)
                     |
                     +-- L168 결과가 오면 handleResult
                            L185 supports 가 true 인 첫 HandlerResultHandler 에게 위임
                            없으면 IllegalStateException
                            결과 처리 중 오류도 result 의 예외 처리기로 복구 시도
```

MVC와 비교하면 순서는 같고 형태만 다르다.

```text
 MVC:     mappedHandler = getHandler(request)      값이 즉시 반환된다
 WebFlux: Flux.fromIterable(mappings).concatMap(...).next()
          매핑 조회 자체가 비동기일 수 있다 (예: 인증 정보를 기다리는 매핑)

 MVC:     try/catch 로 예외 처리
 WebFlux: onErrorResume 으로 대체 Mono 를 잇는다
```

1. 핸들러 탐색은 [HandlerMapping](../spi/HandlerMapping/README.md) 목록이 맡는다.
2. 컨트롤러 호출은 [RequestMappingHandlerAdapter.handle](01_RequestMappingHandlerAdapter.handle/README.md)이 한다.
3. 결과 쓰기는 [HandlerResultHandler](02_HandlerResultHandler.handleResult/README.md)가 한다.

## 결과가 쓰이는 곳

```text
 반환 Mono<Void>
      --> 필터 체인을 거쳐 HttpWebHandlerAdapter 로
      --> 완료 = 응답 완료

 초기화 (initStrategies, L115)
      --> 컨텍스트에서 HandlerMapping / HandlerAdapter / HandlerResultHandler 빈을 모아 정렬
      --> MVC 처럼 기본 전략 파일(DispatcherServlet.properties)은 없다
          @EnableWebFlux 설정이 빈으로 등록한다

 checkpoint(description)
      --> 리액터 스택 트레이스에 단계 이름을 남긴다
      --> 비동기 스택에서 "어느 단계에서 났는지" 를 알 수 있게 하는 장치
```

## 하위 메서드

- [01 RequestMappingHandlerAdapter.handle](01_RequestMappingHandlerAdapter.handle/README.md)
- [02 HandlerResultHandler.handleResult](02_HandlerResultHandler.handleResult/README.md)
