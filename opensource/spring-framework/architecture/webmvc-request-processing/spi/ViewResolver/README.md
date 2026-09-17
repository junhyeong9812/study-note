# ViewResolver

상위: [Spring MVC 요청 처리](../../README.md) / [spi](../README.md)

뷰 이름을 `View` 객체로 바꾼다. `View`는 모델을 받아 응답을 그린다. 이 폴더는 두 인터페이스를 함께 다룬다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `ViewResolver.java` L38-L57 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/ViewResolver.java#L38-L57))

```java
// ViewResolver.java L38-L57
public interface ViewResolver {

    @Nullable View resolveViewName(String viewName, Locale locale) throws Exception;

}
```

`spring-webmvc` / `org.springframework.web.servlet` / `View.java` L46-L98 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/View.java#L46-L98))

```java
// View.java L46-L98
public interface View {

    String RESPONSE_STATUS_ATTRIBUTE = View.class.getName() + ".responseStatus";

    String PATH_VARIABLES = View.class.getName() + ".pathVariables";

    String SELECTED_CONTENT_TYPE = View.class.getName() + ".selectedContentType";

    default @Nullable String getContentType() {
        return null;
    }

    void render(@Nullable Map<String, ?> model, HttpServletRequest request, HttpServletResponse response)
            throws Exception;

}
```

## 흐름에서 불리는 자리

```text
 DispatcherServlet.render
   --> resolveViewNameInternal
         for viewResolver in viewResolvers
           viewResolver.resolveViewName(viewName, locale)   첫 non-null 채택
   --> view.render(model, request, response)
```

- [DispatcherServlet.render](../../02_DispatcherServlet.doDispatch/06_DispatcherServlet.processDispatchResult/02_DispatcherServlet.render/README.md)

## 구현 계층

```text
 ViewResolver
   +-- UrlBasedViewResolver               "redirect:", "forward:" 접두사 처리
   |     +-- InternalResourceViewResolver JSP  (prefix + name + suffix)
   |     +-- FreeMarkerViewResolver 등     템플릿 엔진
   +-- ContentNegotiatingViewResolver     Accept에 맞는 뷰를 다른 리졸버들에서 고름
   +-- BeanNameViewResolver               뷰 이름 = 빈 이름
 View
   +-- InternalResourceView    forward
   +-- RedirectView            302/303
   +-- AbstractJacksonView 등  모델을 JSON으로
```
