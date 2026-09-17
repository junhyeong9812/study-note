# DispatcherServlet.render

상위: [DispatcherServlet.processDispatchResult](../README.md)

`ModelAndView`를 실제 응답으로 그린다. 뷰 이름이면 [ViewResolver](../../../spi/ViewResolver/README.md) 목록으로 `View` 객체를 찾고, `View.render`에 모델을 넘겨 출력하게 한다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L1267-L1313 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L1267-L1313))

```java
// DispatcherServlet.java L1267-L1313
protected void render(ModelAndView mv, HttpServletRequest request, HttpServletResponse response) throws Exception {
    // Determine locale for request and apply it to the response.
    Locale locale =
            (this.localeResolver != null ? this.localeResolver.resolveLocale(request) : request.getLocale());
    response.setLocale(locale);

    View view;
    String viewName = mv.getViewName();
    if (viewName != null) {
        // We need to resolve the view name.
        view = resolveViewName(viewName, mv.getModelInternal(), locale, request);
        if (view == null) {
            throw new ServletException("Could not resolve view with name '" + mv.getViewName() +
                    "' in servlet with name '" + getServletName() + "'");
        }
    }
    else {
        // No need to lookup: the ModelAndView object contains the actual View object.
        view = mv.getView();
        if (view == null) {
            throw new ServletException("ModelAndView [" + mv + "] neither contains a view name nor a " +
                    "View object in servlet with name '" + getServletName() + "'");
        }
    }

    if (view instanceof SmartView smartView) {
        smartView.resolveNestedViews(this::resolveViewNameInternal, locale);
    }

    // Delegate to the View object for rendering.
    if (logger.isTraceEnabled()) {
        logger.trace("Rendering view [" + view + "] ");
    }
    try {
        if (mv.getStatus() != null) {
            request.setAttribute(View.RESPONSE_STATUS_ATTRIBUTE, mv.getStatus());
            response.setStatus(mv.getStatus().value());
        }
        view.render(mv.getModelInternal(), request, response);
    }
    catch (Exception ex) {
        if (logger.isDebugEnabled()) {
            logger.debug("Error rendering view [" + view + "]", ex);
        }
        throw ex;
    }
}
```

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L1345-L1355 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L1345-L1355))

```java
// DispatcherServlet.java L1345-L1355
private @Nullable View resolveViewNameInternal(String viewName, Locale locale) throws Exception {
    if (this.viewResolvers != null) {
        for (ViewResolver viewResolver : this.viewResolvers) {
            View view = viewResolver.resolveViewName(viewName, locale);
            if (view != null) {
                return view;
            }
        }
    }
    return null;
}
```

## 동작 흐름

```text
 render(mv, request, response)
 |
 | L1269 locale = localeResolver.resolveLocale(request)   (없으면 request.getLocale())
 | L1271 response.setLocale(locale)
 |
 +-- mv에 뷰 이름이 있음 ("home")
 |     resolveViewName("home", model, locale, request)
 |       --> resolveViewNameInternal
 |             for viewResolver in viewResolvers
 |               InternalResourceViewResolver --> "/WEB-INF/views/home.jsp" 를 가리키는 View
 |               ThymeleafViewResolver 등      --> 템플릿 View
 |               첫 non-null 채택
 |     null --> ServletException("Could not resolve view with name 'home'")
 |
 +-- mv에 View 객체가 직접 있음 --> 그대로 사용
 |     그것도 없음 --> ServletException
 |
 +-- SmartView (예: RedirectView) --> 중첩 뷰 이름 해석
 |
 +-- mv.getStatus() 있음 --> RESPONSE_STATUS_ATTRIBUTE 설정 + response.setStatus
 |
 +-- view.render(model, request, response)
       실패 --> 디버그 로그 후 던짐
```

## 결과가 쓰이는 곳

```text
 locale
      --> response Content-Language
      --> 템플릿의 메시지 해석 (MessageSource), 날짜/숫자 포맷

 View
      +-- InternalResourceView  --> 모델을 request 속성으로 복사 --> RequestDispatcher.forward(jsp)
      +-- RedirectView          --> 모델(단순 값)을 쿼리 파라미터로 --> 302 + Location
      |                             출력 FlashMap 저장 --> 다음 요청의 INPUT_FLASH_MAP
      +-- 템플릿 엔진 View      --> 모델로 HTML 생성 --> response writer

 render가 던진 예외
      --> processDispatchResult 밖 --> doDispatch 바깥 catch
      --> triggerAfterCompletion(ex)
          (핸들러 단계 예외와 달리 HandlerExceptionResolver를 거치지 않는다)
```

"redirect:" 접두사는 `UrlBasedViewResolver`가 `RedirectView`로 바꾼다. 뷰 이름 규칙이 리다이렉트로 이어지는 연결점이 여기다.
