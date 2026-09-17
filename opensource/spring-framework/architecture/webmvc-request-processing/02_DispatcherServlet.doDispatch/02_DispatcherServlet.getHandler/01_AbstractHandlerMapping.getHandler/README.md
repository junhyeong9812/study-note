# AbstractHandlerMapping.getHandler

상위: [DispatcherServlet.getHandler](../README.md)

모든 `HandlerMapping` 구현의 공통 뼈대다. 하위 클래스가 핸들러만 찾아 주면(`getHandlerInternal`), 여기서 인터셉터를 붙이고 CORS를 처리해 `HandlerExecutionChain`으로 완성한다. `final`이라 구현체가 이 순서를 바꿀 수 없다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.handler` / `AbstractHandlerMapping.java` L542-L591 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/handler/AbstractHandlerMapping.java#L542-L591))

```java
// AbstractHandlerMapping.java L542-L591
public final @Nullable HandlerExecutionChain getHandler(HttpServletRequest request) throws Exception {
    ApiVersionHolder versionHolder = initApiVersion(request);
    Object handler = getHandlerInternal(request);
    if (handler == null) {
        handler = getDefaultHandler();
    }
    if (handler == null) {
        return null;
    }

    if (versionHolder.hasError() && !request.getDispatcherType().equals(DispatcherType.ERROR)) {
        throw versionHolder.getError();
    }

    // Bean name or resolved handler?
    if (handler instanceof String handlerName) {
        handler = obtainApplicationContext().getBean(handlerName);
    }

    // Ensure presence of cached lookupPath for interceptors and others
    if (!ServletRequestPathUtils.hasCachedPath(request)) {
        initLookupPath(request);
    }

    HandlerExecutionChain executionChain = getHandlerExecutionChain(handler, request);

    if (request.getAttribute(SUPPRESS_LOGGING_ATTRIBUTE) == null) {
        if (logger.isTraceEnabled()) {
            logger.trace("Mapped to " + handler);
        }
        else if (logger.isDebugEnabled() && !DispatcherType.ASYNC.equals(request.getDispatcherType())) {
            logger.debug("Mapped to " + executionChain.getHandler());
        }
    }

    if (hasCorsConfigurationSource(handler) || CorsUtils.isPreFlightRequest(request)) {
        CorsConfiguration config = getCorsConfiguration(handler, request);
        if (getCorsConfigurationSource() != null) {
            CorsConfiguration globalConfig = getCorsConfigurationSource().getCorsConfiguration(request);
            config = (globalConfig != null ? globalConfig.combine(config) : config);
        }
        if (config != null) {
            config.validateAllowCredentials();
            config.validateAllowPrivateNetwork();
        }
        executionChain = getCorsHandlerExecutionChain(request, executionChain, config);
    }

    return executionChain;
}
```

## 동작 흐름

```text
 getHandler(request)
 |
 +-- L543 initApiVersion()             API 버전 전략이 있으면 요청에서 버전 해석
 |
 +-- L544 handler = getHandlerInternal(request)      <-- 하위 클래스마다 다름
 |          null --> getDefaultHandler()
 |          그래도 null --> return null            (다음 HandlerMapping에게 넘어감)
 |
 +-- 버전 해석 오류가 있었으면 여기서 던짐       (ERROR 디스패치는 제외)
 |
 +-- handler가 String이면 --> 컨텍스트에서 그 이름의 빈을 꺼냄
 |
 +-- L566 chain = getHandlerExecutionChain(handler, request)
 |          adaptedInterceptors 순회
 |            MappedInterceptor --> 경로 패턴이 맞을 때만 추가
 |            그 밖            --> 무조건 추가
 |
 +-- L577 CORS 설정이 있거나 preflight 요청이면
 |          전역 설정 + 핸들러 설정 결합
 |          L587 getCorsHandlerExecutionChain()
 |            preflight --> 핸들러를 PreFlightHttpRequestHandler로 교체
 |            그 밖     --> CorsInterceptor를 인터셉터 맨 앞(0번)에 삽입
 |
 +-- return chain
```

- `RequestMappingHandlerMapping`의 `getHandlerInternal`은 [lookupHandlerMethod](01_AbstractHandlerMethodMapping.lookupHandlerMethod/README.md)로 URL에 맞는 `@RequestMapping` 메서드를 찾는다.

## 인터셉터를 붙이는 코드

`spring-webmvc` / `org.springframework.web.servlet.handler` / `AbstractHandlerMapping.java` L681-L706 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/handler/AbstractHandlerMapping.java#L681-L706))

```java
// AbstractHandlerMapping.java L681-L706
protected HandlerExecutionChain getHandlerExecutionChain(Object handler, HttpServletRequest request) {

    HandlerExecutionChain chain = (handler instanceof HandlerExecutionChain handlerExecutionChain ?
            handlerExecutionChain : new HandlerExecutionChain(handler));

    for (HandlerInterceptor interceptor : this.adaptedInterceptors) {
        if (interceptor instanceof MappedInterceptor mappedInterceptor) {
            if (mappedInterceptor.matches(request)) {
                chain.addInterceptor(mappedInterceptor.getInterceptor());
            }
        }
        else {
            chain.addInterceptor(interceptor);
        }
    }

    if (this.versionStrategy != null) {
        ApiVersionHolder versionHolder = (ApiVersionHolder) request.getAttribute(API_VERSION_ATTRIBUTE);
        if (versionHolder.hasVersion()) {
            Comparable<?> version = versionHolder.getVersion();
            chain.addInterceptor(new ApiVersionDeprecationHandlerInterceptor(this.versionStrategy, version));
        }
    }

    return chain;
}
```

## 결과가 쓰이는 곳

```text
 chain.interceptorList
      = [CorsInterceptor(있으면 0번), 전역 인터셉터..., 경로가 맞은 MappedInterceptor...]
      --> applyPreHandle에서 이 순서 그대로 실행
          CorsInterceptor가 0번이라 CORS 거부는 다른 인터셉터보다 먼저 판정된다

 preflight(OPTIONS) 요청
      --> 핸들러가 컨트롤러가 아니라 PreFlightHttpRequestHandler
      --> HttpRequestHandlerAdapter가 선택되어 컨트롤러는 실행되지 않는다
```

## 하위 메서드

- [01 AbstractHandlerMethodMapping.lookupHandlerMethod](01_AbstractHandlerMethodMapping.lookupHandlerMethod/README.md)
