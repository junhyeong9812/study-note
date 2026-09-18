# HandlerResultHandler.handleResult

상위: [DispatcherHandler.handle](../README.md)

컨트롤러가 돌려준 값을 응답으로 바꾼다. 반환 타입에 따라 처리기가 갈리고, `@ResponseBody` 계열은 인코더로 본문을 쓰고 뷰 계열은 템플릿을 렌더링한다. MVC의 반환값 처리기 + 메시지 컨버터에 해당한다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive.result.method.annotation` / `ResponseBodyResultHandler.java` L98-L104 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/result/method/annotation/ResponseBodyResultHandler.java#L98-L104))

```java
// ResponseBodyResultHandler.java L98-L104
@Override
public boolean supports(HandlerResult result) {
    MethodParameter returnType = result.getReturnTypeSource();
    return (this.responseBodyControllerCache.computeIfAbsent(returnType.getContainingClass(),
            clazz -> AnnotatedElementUtils.hasAnnotation(clazz, ResponseBody.class)) ||
            returnType.hasMethodAnnotation(ResponseBody.class));
}
```

`spring-webflux` / `org.springframework.web.reactive.result.method.annotation` / `ResponseBodyResultHandler.java` L106-L119 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/result/method/annotation/ResponseBodyResultHandler.java#L106-L119))

```java
// ResponseBodyResultHandler.java L106-L119
@Override
public Mono<Void> handleResult(ServerWebExchange exchange, HandlerResult result) {
    Object body = result.getReturnValue();
    MethodParameter bodyTypeParameter = result.getReturnTypeSource();
    if (body instanceof ProblemDetail detail) {
        exchange.getResponse().setStatusCode(HttpStatusCode.valueOf(detail.getStatus()));
        if (detail.getInstance() == null) {
            URI path = URI.create(exchange.getRequest().getPath().value());
            detail.setInstance(path);
        }
        invokeErrorResponseInterceptors(detail, null);
    }
    return writeBody(body, bodyTypeParameter, exchange);
}
```

본문을 실제로 쓰는 부분이다.

`spring-webflux` / `org.springframework.web.reactive.result.method.annotation` / `AbstractMessageWriterResultHandler.java` L169-L254 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/result/method/annotation/AbstractMessageWriterResultHandler.java#L169-L254))

```java
// AbstractMessageWriterResultHandler.java L169-L254
protected Mono<Void> writeBody(@Nullable Object body, MethodParameter bodyParameter,
        @Nullable MethodParameter actualParam, ServerWebExchange exchange) {

    ResolvableType bodyType = ResolvableType.forMethodParameter(bodyParameter);
    ResolvableType actualType = (actualParam != null ? ResolvableType.forMethodParameter(actualParam) : bodyType);
    ReactiveAdapter adapter = getAdapterRegistry().getAdapter(bodyType.resolve(), body);

    Publisher<?> publisher;
    ResolvableType elementType;
    ResolvableType actualElementType;
    if (adapter != null) {
        publisher = adapter.toPublisher(body);
        boolean isUnwrapped = KotlinDetector.isSuspendingFunction(bodyParameter.getMethod()) &&
                !COROUTINES_FLOW_CLASS_NAME.equals(bodyType.toClass().getName()) &&
                !Flux.class.equals(bodyType.toClass());
        ResolvableType genericType = isUnwrapped ? bodyType : bodyType.getGeneric();
        elementType = getElementType(adapter, genericType);
        actualElementType = elementType;
    }
    else {
        publisher = Mono.justOrEmpty(body);
        ResolvableType bodyInstanceType = ResolvableType.forInstance(body);
        if (bodyType.toClass() == Object.class && body != null) {
            actualElementType = bodyInstanceType;
            elementType = bodyInstanceType;
        }
        else {
            actualElementType = (body == null || bodyInstanceType.hasUnresolvableGenerics()) ? bodyType : bodyInstanceType;
            elementType = bodyType;
        }
    }

    if (ClassUtils.isVoidType(elementType.resolve())) {
        return Mono.from((Publisher<Void>) publisher);
    }

    MediaType bestMediaType;
    try {
        bestMediaType = selectMediaType(exchange, () -> getMediaTypesFor(elementType));
    }
    catch (NotAcceptableStatusException ex) {
        HttpStatusCode statusCode = exchange.getResponse().getStatusCode();
        if (statusCode != null && statusCode.isError()) {
            if (logger.isDebugEnabled()) {
                logger.debug("Ignoring error response content (if any). " + ex.getReason());
            }
            return Mono.empty();
        }
        throw ex;
    }

    // For ProblemDetail, fall back on RFC 9457 format
    if (bestMediaType == null && ProblemDetail.class.isAssignableFrom(elementType.toClass())) {
        bestMediaType = selectMediaType(exchange, () -> getMediaTypesFor(elementType), this.problemMediaTypes);
    }

    if (bestMediaType != null) {
        String logPrefix = exchange.getLogPrefix();
        if (logger.isDebugEnabled()) {
            logger.debug(logPrefix +
                    (publisher instanceof Mono ? "0..1" : "0..N") + " [" + elementType + "]");
        }
        for (HttpMessageWriter<?> writer : getMessageWriters()) {
            if (writer.canWrite(actualElementType, bestMediaType)) {
                return writer.write((Publisher) publisher, actualType, elementType,
                        bestMediaType, exchange.getRequest(), exchange.getResponse(),
                        Hints.from(Hints.LOG_PREFIX_HINT, logPrefix));
            }
        }
    }

    MediaType contentType = exchange.getResponse().getHeaders().getContentType();
    boolean isPresentMediaType = (contentType != null && contentType.equals(bestMediaType));
    Set<MediaType> producibleTypes = exchange.getAttribute(HandlerMapping.PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE);
    if (isPresentMediaType || !CollectionUtils.isEmpty(producibleTypes)) {
        return Mono.error(new HttpMessageNotWritableException(
                "No Encoder for [" + elementType + "] with preset Content-Type '" + contentType + "'"));
    }

    List<MediaType> mediaTypes = getMediaTypesFor(elementType);
    if (bestMediaType == null && mediaTypes.isEmpty()) {
        return Mono.error(new IllegalStateException("No HttpMessageWriter for " + elementType));
    }

    return Mono.error(new NotAcceptableStatusException(mediaTypes));
}
```

## 동작 흐름

```text
 DispatcherHandler.handleResult
   supports(result) 가 true 인 첫 HandlerResultHandler 에게 위임

 ResponseBodyResultHandler.handleResult
 |
 | L108 body = result.getReturnValue()
 | L110 ProblemDetail 이면 상태 코드와 instance 를 채운다
 +-- L118 writeBody(body, 반환 타입 파라미터, exchange)

 writeBody(body, bodyParameter, actualParam, exchange)
 |
 | L174 반환 타입에 맞는 ReactiveAdapter 조회  (Mono, Flux, Kotlin Flow, RxJava 등)
 |        어댑터 있음 --> publisher = adapter.toPublisher(body)
 |                        elementType = 제네릭 요소 타입
 |        없음      --> publisher = Mono.justOrEmpty(body)
 |
 | L202 요소 타입이 Void 면 그대로 완료 신호만 (본문 없음)
 |
 | L205 bestMediaType = selectMediaType(exchange, 이 타입을 쓸 수 있는 미디어 타입 목록)
 |        요청 Accept 와 서버가 만들 수 있는 타입의 교집합에서 선택
 |        ProblemDetail 이면 problem+json 계열로 재시도
 |
 +-- 선택된 타입을 쓸 수 있는 HttpMessageWriter 를 찾아
       writer.write(publisher, 타입, bestMediaType, 응답, 힌트)
       = 인코더가 요소를 DataBuffer 로 바꿔 응답에 흘려보낸다
```

반환 타입별로 처리기가 나뉜다.

```text
 @ResponseBody / @RestController        ResponseBodyResultHandler
 ResponseEntity                         ResponseEntityResultHandler   (상태, 헤더까지)
 뷰 이름(String), Model, View           ViewResolutionResultHandler
 ServerResponse (함수형)                ServerResponseResultHandler
 Rendering                              ViewResolutionResultHandler
```

- 요소를 실제 바이트로 바꾸는 것은 [HttpMessageWriter](../../spi/HttpMessageWriter/README.md)와 그 안의 인코더다.

## 결과가 쓰이는 곳

```text
 반환 Mono<Void>
      --> DispatcherHandler 를 거쳐 필터 체인으로
      --> 완료 = 본문 쓰기 완료

 Flux 반환값
      --> 요소 하나하나가 인코딩되어 흘러간다
      --> text/event-stream 이면 SSE, application/json 이면 배열로 직렬화
      --> 스트리밍 도중 오류는 이미 커밋된 응답 위에서 발생하므로
          상태 코드를 바꿀 수 없다 (연결이 끊기는 형태로 드러난다)

 선택된 미디어 타입
      --> 응답 Content-Type 헤더
      --> 쓸 수 있는 writer 가 없으면 NotAcceptableStatusException (406)
```
