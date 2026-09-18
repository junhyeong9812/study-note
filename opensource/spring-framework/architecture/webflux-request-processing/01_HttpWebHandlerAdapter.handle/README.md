# HttpWebHandlerAdapter.handle

상위: [Spring WebFlux 요청 처리](../README.md)

서버 어댑터가 넘긴 요청과 응답을 `ServerWebExchange` 하나로 묶고, 그 위에 로깅, 관측, 오류 처리, 완료 처리를 얹은 `Mono<Void>`를 만든다. MVC의 `FrameworkServlet.processRequest`에 대응하는 자리다.

## 실제 코드

`spring-web` / `org.springframework.web.server.adapter` / `HttpWebHandlerAdapter.java` L292-L327 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/server/adapter/HttpWebHandlerAdapter.java#L292-L327))

```java
// HttpWebHandlerAdapter.java L292-L327
@Override
public Mono<Void> handle(ServerHttpRequest request, ServerHttpResponse response) {
    if (this.forwardedHeaderTransformer != null) {
        try {
            request = this.forwardedHeaderTransformer.apply(request);
        }
        catch (Throwable ex) {
            if (logger.isDebugEnabled()) {
                logger.debug("Failed to apply forwarded headers to " + formatRequest(request), ex);
            }
            response.setStatusCode(HttpStatus.BAD_REQUEST);
            return response.setComplete();
        }
    }
    ServerWebExchange exchange = createExchange(request, response);

    LogFormatUtils.traceDebug(logger, traceOn ->
            exchange.getLogPrefix() + formatRequest(exchange.getRequest()) +
                    (traceOn ? ", headers=" + formatHeaders(exchange.getRequest().getHeaders()) : ""));

    ServerRequestObservationContext observationContext = new ServerRequestObservationContext(
            exchange.getRequest(), exchange.getResponse(), exchange.getAttributes());
    exchange.getAttributes().put(
            ServerRequestObservationContext.CURRENT_OBSERVATION_CONTEXT_ATTRIBUTE, observationContext);

    if (this.defaultHtmlEscape != null) {
        exchange.getAttributes().put(ServerWebExchange.HTML_ESCAPE_ATTRIBUTE, this.defaultHtmlEscape);
    }

    return getDelegate().handle(exchange)
            .doOnSuccess(aVoid -> logResponse(exchange))
            .onErrorResume(ex -> handleUnresolvedError(exchange, observationContext, ex))
            .tap(() -> new ObservationSignalListener(observationContext))
            .then(exchange.cleanupMultipart())
            .then(Mono.defer(response::setComplete));
}
```

## 동작 흐름

```text
 handle(request, response)
 |
 | L294 forwardedHeaderTransformer 가 있으면 X-Forwarded-* 를 반영한 요청으로 교체
 |        실패 --> 400 응답 후 종료
 |
 | L306 exchange = createExchange(request, response)
 |        DefaultServerWebExchange: 요청/응답/세션 매니저/코덱/로케일 해석기/컨텍스트를 묶음
 |
 | L312 관측 컨텍스트를 만들어 exchange 속성에 저장
 |
 +-- L321 getDelegate().handle(exchange)        <-- 필터 체인 -> DispatcherHandler
        .doOnSuccess  응답 로깅
        .onErrorResume(handleUnresolvedError)   아무도 처리하지 못한 오류 --> 500 등
        .tap(관측 리스너)
        .then(exchange.cleanupMultipart())      임시 파일 정리
        .then(response.setComplete())           응답 완료 신호
```

`getDelegate()`가 가리키는 것은 보통 `WebHandler` 체인이다.

```text
 WebHttpHandlerBuilder 가 조립한 모습

 HttpWebHandlerAdapter
   -> ExceptionHandlingWebHandler      WebExceptionHandler 목록
        -> FilteringWebHandler         WebFilter 목록 (순서대로)
             -> DispatcherHandler      실제 요청 처리
```

1. 체인의 끝에서 [DispatcherHandler.handle](../02_DispatcherHandler.handle/README.md)이 요청을 처리한다.

## 결과가 쓰이는 곳

```text
 ServerWebExchange
      --> 이후 모든 단계가 이 객체 하나를 들고 다닌다
          요청/응답, 속성 맵, 세션, 로케일, 폼 데이터, multipart
      --> MVC 의 HttpServletRequest + RequestContextHolder 를 합친 역할

 조립된 Mono<Void>
      --> 서버 어댑터(ReactorHttpHandlerAdapter 등)가 구독
      --> 구독 시점에 비로소 필터와 핸들러가 실행된다

 setComplete()
      --> 헤더를 커밋하고 응답을 닫는다
      --> 이미 본문이 쓰였으면 완료만 표시한다
```
