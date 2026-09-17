# HandlerExceptionResolver

상위: [Spring MVC 요청 처리](../../README.md) / [spi](../README.md)

핸들러 단계에서 난 예외를 응답으로 바꾼다. 처리했으면 `ModelAndView`(빈 것 포함), 모르면 null을 돌려준다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `HandlerExceptionResolver.java` L35-L54 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/HandlerExceptionResolver.java#L35-L54))

```java
// HandlerExceptionResolver.java L35-L54
public interface HandlerExceptionResolver {

    @Nullable ModelAndView resolveException(
            HttpServletRequest request, HttpServletResponse response, @Nullable Object handler, Exception ex);

}
```

## 흐름에서 불리는 자리

```text
 DispatcherServlet.processHandlerException
   --> for resolver in handlerExceptionResolvers
         resolver.resolveException(request, response, handler, ex)   첫 non-null 채택
   전부 null --> 예외 재던짐
```

- [DispatcherServlet.processHandlerException](../../02_DispatcherServlet.doDispatch/06_DispatcherServlet.processDispatchResult/01_DispatcherServlet.processHandlerException/README.md)

## 구현 계층

```text
 HandlerExceptionResolver
   +-- HandlerExceptionResolverComposite      목록을 하나로 감싼 것 (@EnableWebMvc 등록)
   +-- AbstractHandlerExceptionResolver       적용 대상 필터, 캐시 헤더, 로깅
         +-- AbstractHandlerMethodExceptionResolver
         |     +-- ExceptionHandlerExceptionResolver   @ExceptionHandler, @ControllerAdvice
         +-- ResponseStatusExceptionResolver           @ResponseStatus, ResponseStatusException
         +-- DefaultHandlerExceptionResolver           표준 예외 --> 4xx/5xx
         +-- SimpleMappingExceptionResolver            예외 클래스 --> 뷰 이름 매핑
```
