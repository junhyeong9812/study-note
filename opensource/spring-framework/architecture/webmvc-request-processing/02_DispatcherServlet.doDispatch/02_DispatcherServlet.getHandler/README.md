# DispatcherServlet.getHandler

상위: [DispatcherServlet.doDispatch](../README.md)

등록된 [HandlerMapping](../../spi/HandlerMapping/README.md) 목록을 앞에서부터 물어, null이 아닌 답을 처음 준 매핑의 결과를 채택한다. 결과는 핸들러 단독이 아니라 핸들러와 인터셉터를 묶은 `HandlerExecutionChain`이다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L1154-L1164 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L1154-L1164))

```java
// DispatcherServlet.java L1154-L1164
protected @Nullable HandlerExecutionChain getHandler(HttpServletRequest request) throws Exception {
    if (this.handlerMappings != null) {
        for (HandlerMapping mapping : this.handlerMappings) {
            HandlerExecutionChain handler = mapping.getHandler(request);
            if (handler != null) {
                return handler;
            }
        }
    }
    return null;
}
```

## 동작 흐름

```text
 getHandler(request)
 |
 +-- for mapping in handlerMappings          (빈이 있으면 @Order 순, 없으면
 |                                              DispatcherServlet.properties 순)
 |      |
 |      +-- BeanNameUrlHandlerMapping.getHandler      빈 이름이 "/..."인 핸들러
 |      |      null --> 다음
 |      +-- RequestMappingHandlerMapping.getHandler   @RequestMapping 메서드
 |      |      non-null --> 즉시 return   (뒤의 매핑은 묻지 않는다)
 |      +-- RouterFunctionMapping.getHandler          함수형 라우트
 |
 +-- 전부 null --> return null  --> doDispatch가 noHandlerFound()
```

- 목록의 원소가 부르는 `getHandler`는 모두 [AbstractHandlerMapping.getHandler](01_AbstractHandlerMapping.getHandler/README.md) 하나로 모인다. 매핑마다 다른 것은 그 안의 `getHandlerInternal`뿐이다.

## 결과가 쓰이는 곳

```text
 HandlerExecutionChain
      +-- getHandler()        --> doDispatch L962  어댑터 선택
      |                        --> doDispatch L963  ha.handle(..., handler)
      +-- interceptorList     --> applyPreHandle / applyPostHandle / triggerAfterCompletion
 null
      --> noHandlerFound() --> NoHandlerFoundException
          --> DefaultHandlerExceptionResolver --> 404
```

## 하위 메서드

- [01 AbstractHandlerMapping.getHandler](01_AbstractHandlerMapping.getHandler/README.md)
