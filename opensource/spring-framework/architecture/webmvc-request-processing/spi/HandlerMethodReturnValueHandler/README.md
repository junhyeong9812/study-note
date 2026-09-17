# HandlerMethodReturnValueHandler

상위: [Spring MVC 요청 처리](../../README.md) / [spi](../README.md)

컨트롤러 메서드의 반환값을 응답으로 옮긴다. 본문을 직접 쓰거나, 뷰 이름과 모델을 `ModelAndViewContainer`에 기록한다.

## 실제 코드

`spring-web` / `org.springframework.web.method.support` / `HandlerMethodReturnValueHandler.java` L32-L59 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/HandlerMethodReturnValueHandler.java#L32-L59))

```java
// HandlerMethodReturnValueHandler.java L32-L59
public interface HandlerMethodReturnValueHandler {

    boolean supportsReturnType(MethodParameter returnType);

    void handleReturnValue(@Nullable Object returnValue, MethodParameter returnType,
            ModelAndViewContainer mavContainer, NativeWebRequest webRequest) throws Exception;

}
```

## 흐름에서 불리는 자리

```text
 ServletInvocableHandlerMethod.invokeAndHandle
   --> HandlerMethodReturnValueHandlerComposite.handleReturnValue
         selectHandler     첫 supportsReturnType 채택 (비동기 값이면 비동기 처리기만)
         handler.handleReturnValue(...)
```

- [HandlerMethodReturnValueHandlerComposite.handleReturnValue](../../02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/03_HandlerMethodReturnValueHandlerComposite.handleReturnValue/README.md)
- [RequestMappingHandlerAdapter.getModelAndView](../../02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/03_RequestMappingHandlerAdapter.getModelAndView/README.md)

## 구현 계층

```text
 기본 15개 (RequestMappingHandlerAdapter L734)
   본문을 쓰는 쪽 (requestHandled = true)
     RequestResponseBodyMethodProcessor   @ResponseBody
     HttpEntityMethodProcessor            ResponseEntity, HttpEntity
     HttpHeadersReturnValueHandler        HttpHeaders
   비동기
     DeferredResultMethodReturnValueHandler, CallableMethodReturnValueHandler,
     ResponseBodyEmitterReturnValueHandler (SSE, 스트리밍) ...
   뷰로 가는 쪽
     ModelAndViewMethodReturnValueHandler ModelAndView
     ViewMethodReturnValueHandler         View
     ViewNameMethodReturnValueHandler     String, void
     ModelMethodProcessor, MapMethodProcessor, ModelAttributeMethodProcessor
```
