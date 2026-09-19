# HandlerMethodArgumentResolver

상위: [Spring MVC 요청 처리](../../README.md) / [spi](../README.md)

컨트롤러 메서드의 파라미터 하나에 넣을 값을 만든다. `supportsParameter`로 자기 담당인지 답하고, `resolveArgument`로 값을 만든다.

## 실제 코드

`spring-web` / `org.springframework.web.method.support` / `HandlerMethodArgumentResolver.java` L34-L63 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/HandlerMethodArgumentResolver.java#L34-L63))

```java
// HandlerMethodArgumentResolver.java L34-L63
public interface HandlerMethodArgumentResolver {

    boolean supportsParameter(MethodParameter parameter);

    @Nullable Object resolveArgument(MethodParameter parameter, @Nullable ModelAndViewContainer mavContainer,
            NativeWebRequest webRequest, @Nullable WebDataBinderFactory binderFactory) throws Exception;

}
```

## 흐름에서 불리는 자리

```text
 InvocableHandlerMethod.getMethodArgumentValues
   --> for parameter
         HandlerMethodArgumentResolverComposite
           getArgumentResolver(parameter)   파라미터별 캐시, 첫 supports 채택
           resolver.resolveArgument(...)
```

- [InvocableHandlerMethod.getMethodArgumentValues](../../02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/01_InvocableHandlerMethod.getMethodArgumentValues/README.md)
- [ModelFactory.initModel](../../02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/01_ModelFactory.initModel/README.md)

## 구현 계층

```text
 기본 28개 (RequestMappingHandlerAdapter L648), 순서가 우선순위
 Kotlin 이 클래스패스에 있으면 ContinuationHandlerMethodArgumentResolver 가 더해져 29개
   어노테이션 기반  @RequestParam @PathVariable @MatrixVariable @ModelAttribute(명시)
                    @RequestBody @RequestPart @RequestHeader @CookieValue @Value
                    @SessionAttribute @RequestAttribute
   타입 기반        ServletRequest ServletResponse HttpEntity RedirectAttributes
                    Model Map Errors SessionStatus UriComponentsBuilder
   사용자 정의      WebMvcConfigurer.addArgumentResolvers
   기본 처리        Principal, 단순 타입 = @RequestParam, 그 밖 = @ModelAttribute
```
