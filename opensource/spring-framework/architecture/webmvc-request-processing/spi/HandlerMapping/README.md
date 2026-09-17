# HandlerMapping

상위: [Spring MVC 요청 처리](../../README.md) / [spi](../README.md)

요청을 보고 처리할 핸들러와 인터셉터 묶음을 돌려준다. 못 찾으면 null이고, 그것은 오류가 아니라 "다음 매핑에게 물어라"는 뜻이다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `HandlerMapping.java` L58-L181 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/HandlerMapping.java#L58-L181))

```java
// HandlerMapping.java L58-L181
public interface HandlerMapping {

    String BEST_MATCHING_HANDLER_ATTRIBUTE = HandlerMapping.class.getName() + ".bestMatchingHandler";

    @Deprecated(since = "5.3")
    String LOOKUP_PATH = HandlerMapping.class.getName() + ".lookupPath";

    String PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE = HandlerMapping.class.getName() + ".pathWithinHandlerMapping";

    String BEST_MATCHING_PATTERN_ATTRIBUTE = HandlerMapping.class.getName() + ".bestMatchingPattern";

    String INTROSPECT_TYPE_LEVEL_MAPPING = HandlerMapping.class.getName() + ".introspectTypeLevelMapping";

    String URI_TEMPLATE_VARIABLES_ATTRIBUTE = HandlerMapping.class.getName() + ".uriTemplateVariables";

    String MATRIX_VARIABLES_ATTRIBUTE = HandlerMapping.class.getName() + ".matrixVariables";

    String PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE = HandlerMapping.class.getName() + ".producibleMediaTypes";

    String API_VERSION_ATTRIBUTE = HandlerMapping.class.getName() + ".apiVersion";

    default boolean usesPathPatterns() {
        return false;
    }

    @Nullable HandlerExecutionChain getHandler(HttpServletRequest request) throws Exception;

}
```

## 흐름에서 불리는 자리

```text
 DispatcherServlet.getHandler
   --> for mapping in handlerMappings
         mapping.getHandler(request)    첫 non-null 채택
```

- [DispatcherServlet.getHandler](../../02_DispatcherServlet.doDispatch/02_DispatcherServlet.getHandler/README.md)
- [AbstractHandlerMapping.getHandler](../../02_DispatcherServlet.doDispatch/02_DispatcherServlet.getHandler/01_AbstractHandlerMapping.getHandler/README.md)

## 구현 계층

```text
 HandlerMapping
   +-- AbstractHandlerMapping                  인터셉터, CORS 공통 처리 (getHandler는 final)
         +-- AbstractUrlHandlerMapping
         |     +-- BeanNameUrlHandlerMapping         빈 이름 "/foo" --> 핸들러
         |     +-- SimpleUrlHandlerMapping           URL 맵 설정 (정적 리소스 등)
         +-- AbstractHandlerMethodMapping<T>
         |     +-- RequestMappingInfoHandlerMapping
         |           +-- RequestMappingHandlerMapping  @RequestMapping
         +-- RouterFunctionMapping                  함수형 라우트
```
