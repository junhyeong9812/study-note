# webmvc.RouterFunctionMapping.getHandlerInternal

상위: [Spring 함수형 엔드포인트](../README.md)

서블릿 스택에서 함수형 경로의 입구다. 요청을 `ServerRequest`로 감싸 라우터 함수에 묻고, 맞는 핸들러 함수가 있으면 그것을 핸들러로 돌려준다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function.support` / `RouterFunctionMapping.java` L206-L214 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/support/RouterFunctionMapping.java#L206-L214))

```java
// RouterFunctionMapping.java L206-L214
protected @Nullable Object getHandlerInternal(HttpServletRequest servletRequest) throws Exception {
    if (this.routerFunction == null) {
        return null;
    }
    ServerRequest request = ServerRequest.create(servletRequest, this.messageConverters, getApiVersionStrategy());
    HandlerFunction<?> handlerFunction = this.routerFunction.route(request).orElse(null);
    setAttributes(servletRequest, request, handlerFunction);
    return handlerFunction;
}
```

라우터 함수 목록은 기동 때 한 번 모아 하나로 접어 둔다.

`spring-webmvc` / `org.springframework.web.servlet.function.support` / `RouterFunctionMapping.java` L155-L169 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/support/RouterFunctionMapping.java#L155-L169))

```java
// RouterFunctionMapping.java L155-L169
private void initRouterFunctions() {
    List<RouterFunction<?>> routerFunctions = obtainApplicationContext()
            .getBeanProvider(RouterFunction.class)
            .orderedStream()
            .map(router -> (RouterFunction<?>) router)
            .collect(Collectors.toList());

    ApplicationContext parentContext = obtainApplicationContext().getParent();
    if (parentContext != null && !this.detectHandlerFunctionsInAncestorContexts) {
        parentContext.getBeanProvider(RouterFunction.class).stream().forEach(routerFunctions::remove);
    }

    this.routerFunction = routerFunctions.stream().reduce(RouterFunction::andOther).orElse(null);
    logRouterFunctions(routerFunctions);
}
```

## 동작 흐름

```text
 getHandlerInternal(servletRequest)
 |
 +-- L207 routerFunction 이 null (등록된 라우터가 없다)
 |        --> null 반환. 이 매핑은 이 요청을 모른다
 |
 | L210 ServerRequest.create(servletRequest, messageConverters, versionStrategy)
 |        서블릿 요청을 함수형 API 로 감싼다
 |        여기서 넘긴 컨버터가 나중에 request.body(...) 의 본문 변환에 쓰인다
 |
 | L211 routerFunction.route(request)
 |        조건에 맞는 HandlerFunction 을 Optional 로 받는다
 |        비면 orElse(null) --> null 반환 --> 다음 HandlerMapping 차례
 |
 +-- L212 setAttributes(servletRequest, request, handlerFunction)
        MATCHING_PATTERN_ATTRIBUTE 가 있으면 BEST_MATCHING_PATTERN_ATTRIBUTE 로 옮기고
          관측 컨텍스트에도 패턴 문자열을 알려 준다
        BEST_MATCHING_HANDLER_ATTRIBUTE = handlerFunction
        RouterFunctions.REQUEST_ATTRIBUTE = 방금 만든 ServerRequest
```

```text
 initRouterFunctions()   기동 시 1회
 |
 | L156 컨텍스트에서 RouterFunction 타입 빈을 전부 꺼낸다 (orderedStream 이라 @Order 반영)
 |
 +-- L163 부모 컨텍스트가 있고 detectHandlerFunctionsInAncestorContexts 가 false 면
 |        부모 쪽 라우터는 목록에서 뺀다
 |
 +-- L167 reduce(RouterFunction::andOther)
        여러 개의 라우터 함수를 "앞이 비면 다음" 순서로 하나로 접는다
        하나도 없으면 null (위 L207 분기로 이어진다)
```

1. 실제 조건 판정과 핸들러 선택은 [DefaultRouterFunction.route](01_DefaultRouterFunction.route/README.md)에서 일어난다.

## 결과가 쓰이는 곳

```text
 반환한 HandlerFunction
      --> AbstractHandlerMapping 이 HandlerExecutionChain 으로 감싼다 (인터셉터가 그대로 붙는다)
      --> getHandlerAdapter 가 supports 로 어댑터를 고른다
            HandlerFunctionAdapter 만 handler instanceof HandlerFunction 을 만족한다

 null 을 반환하면
      --> DispatcherServlet 이 다음 HandlerMapping 에게 묻는다
      --> 전부 실패하면 noHandlerFound --> NoHandlerFoundException

 REQUEST_ATTRIBUTE 에 담긴 ServerRequest
      --> 어댑터가 같은 인스턴스를 꺼내 쓴다 (HandlerFunctionAdapter L142-L148)
      --> 어댑터에는 컨버터 목록과 API 버전 전략이 없어 같은 요청 객체를 다시 만들 수 없다
```

애노테이션 컨트롤러가 같은 자리를 채우는 경로는 [MVC 요청 처리](../../webmvc-request-processing/02_DispatcherServlet.doDispatch/02_DispatcherServlet.getHandler/README.md)에 있다.

## 하위 메서드

- [01 DefaultRouterFunction.route](01_DefaultRouterFunction.route/README.md)
