# HandlerAdapter

상위: [Spring MVC 요청 처리](../../README.md) / [spi](../README.md)

핸들러 객체를 실제로 호출하는 방법을 캡슐화한다. `DispatcherServlet`은 핸들러 타입을 몰라도 어댑터에게 "부를 수 있나"만 묻는다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `HandlerAdapter.java` L49-L78 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/HandlerAdapter.java#L49-L78))

```java
// HandlerAdapter.java L49-L78
public interface HandlerAdapter {

    boolean supports(Object handler);

    @Nullable ModelAndView handle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception;

}
```

## 흐름에서 불리는 자리

```text
 DispatcherServlet.getHandlerAdapter
   --> for adapter in handlerAdapters
         adapter.supports(handler)       첫 true 채택
 doDispatch L963
   --> ha.handle(request, response, handler)   --> ModelAndView 또는 null
```

- [DispatcherServlet.getHandlerAdapter](../../02_DispatcherServlet.doDispatch/04_DispatcherServlet.getHandlerAdapter/README.md)
- [RequestMappingHandlerAdapter.invokeHandlerMethod](../../02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/README.md)

## 구현 계층

```text
 HandlerAdapter
   +-- HttpRequestHandlerAdapter        HttpRequestHandler   (정적 리소스, preflight)
   +-- SimpleControllerHandlerAdapter   Controller 인터페이스
   +-- AbstractHandlerMethodAdapter     HandlerMethod        (handle은 final)
   |     +-- RequestMappingHandlerAdapter
   +-- HandlerFunctionAdapter           HandlerFunction
```
