# DispatcherServlet.getHandlerAdapter

상위: [DispatcherServlet.doDispatch](../README.md)

`DispatcherServlet`은 핸들러가 어떤 타입인지 모른다. 그래서 [HandlerAdapter](../../spi/HandlerAdapter/README.md) 목록에 "이 핸들러를 부를 줄 아나"를 물어 첫 번째로 그렇다고 답한 어댑터에게 호출을 맡긴다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L1185-L1195 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L1185-L1195))

```java
// DispatcherServlet.java L1185-L1195
protected HandlerAdapter getHandlerAdapter(Object handler) throws ServletException {
    if (this.handlerAdapters != null) {
        for (HandlerAdapter adapter : this.handlerAdapters) {
            if (adapter.supports(handler)) {
                return adapter;
            }
        }
    }
    throw new ServletException("No adapter for handler [" + handler +
            "]: The DispatcherServlet configuration needs to include a HandlerAdapter that supports this handler");
}
```

## 동작 흐름

```text
 getHandlerAdapter(handler)
 |
 +-- for adapter in handlerAdapters
 |      |
 |      +-- HttpRequestHandlerAdapter      supports: handler instanceof HttpRequestHandler
 |      |                                  (정적 리소스, CORS preflight 핸들러)
 |      +-- SimpleControllerHandlerAdapter supports: handler instanceof Controller
 |      |                                  (옛 Controller 인터페이스)
 |      +-- RequestMappingHandlerAdapter   supports: handler instanceof HandlerMethod
 |      |                                  (@RequestMapping 메서드)  <-- 대부분 여기
 |      +-- HandlerFunctionAdapter         supports: handler instanceof HandlerFunction
 |                                         (함수형 라우트)
 |
 +-- 아무도 supports 안 함 --> ServletException   (설정 오류, 404가 아니라 500)
```

- 선택된 어댑터의 `handle`은 `@Controller`라면 `AbstractHandlerMethodAdapter.handle`에서 `handleInternal`을 거쳐 [invokeHandlerMethod](../05_RequestMappingHandlerAdapter.invokeHandlerMethod/README.md)로 간다.

`spring-webmvc` / `org.springframework.web.servlet.mvc.method` / `AbstractHandlerMethodAdapter.java` L83-L87 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/AbstractHandlerMethodAdapter.java#L83-L87))

```java
// AbstractHandlerMethodAdapter.java L83-L87
public final @Nullable ModelAndView handle(HttpServletRequest request, HttpServletResponse response, Object handler)
        throws Exception {

    return handleInternal(request, response, (HandlerMethod) handler);
}
```

## 결과가 쓰이는 곳

```text
 HandlerAdapter ha
      --> doDispatch L963  mv = ha.handle(processedRequest, response, handler)
            반환 ModelAndView
              RequestMappingHandlerAdapter  --> @ResponseBody면 null, 뷰면 ModelAndView
              HttpRequestHandlerAdapter     --> 항상 null  (핸들러가 응답을 직접 씀)
              SimpleControllerHandlerAdapter --> Controller가 돌려준 값 그대로
```

어댑터가 따로 있는 덕분에 핸들러 타입이 늘어나도 `doDispatch`는 바뀌지 않는다. 함수형 엔드포인트(5.2)는 `HandlerFunctionAdapter`와 `RouterFunctionMapping`을 추가하는 것만으로 이 흐름에 들어왔다.
