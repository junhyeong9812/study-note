# DispatcherServlet.processHandlerException

상위: [DispatcherServlet.processDispatchResult](../README.md)

핸들러 단계에서 난 예외를 [HandlerExceptionResolver](../../../spi/HandlerExceptionResolver/README.md) 목록에 차례로 보여 주고, 처음으로 처리하겠다고 답한 리졸버의 결과를 쓴다. 아무도 처리하지 못하면 예외를 다시 던진다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L1207-L1256 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L1207-L1256))

```java
// DispatcherServlet.java L1207-L1256
protected @Nullable ModelAndView processHandlerException(HttpServletRequest request, HttpServletResponse response,
        @Nullable Object handler, Exception ex) throws Exception {

    // Success and error responses may use different content types
    request.removeAttribute(HandlerMapping.PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE);
    // Reset the response content-type header and body buffer if the response is not committed already,
    // leaving the other response headers in place.
    try {
        response.setHeader(HttpHeaders.CONTENT_TYPE, null);
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, null);
        response.resetBuffer();
    }
    catch (IllegalStateException illegalStateException) {
        // the response is already committed, leave it to exception handlers anyway
    }

    // Check registered HandlerExceptionResolvers...
    ModelAndView exMv = null;
    if (this.handlerExceptionResolvers != null) {
        for (HandlerExceptionResolver resolver : this.handlerExceptionResolvers) {
            exMv = resolver.resolveException(request, response, handler, ex);
            if (exMv != null) {
                break;
            }
        }
    }
    if (exMv != null) {
        if (exMv.isEmpty()) {
            request.setAttribute(EXCEPTION_ATTRIBUTE, ex);
            return null;
        }
        // We might still need view name translation for a plain error model...
        if (!exMv.hasView()) {
            String defaultViewName = getDefaultViewName(request);
            if (defaultViewName != null) {
                exMv.setViewName(defaultViewName);
            }
        }
        if (logger.isTraceEnabled()) {
            logger.trace("Using resolved error view: " + exMv, ex);
        }
        else if (logger.isDebugEnabled()) {
            logger.debug("Using resolved error view: " + exMv);
        }
        WebUtils.exposeErrorRequestAttributes(request, ex, getServletName());
        return exMv;
    }

    throw ex;
}
```

## 동작 흐름

```text
 processHandlerException(request, response, handler, ex)
 |
 | L1211 PRODUCIBLE_MEDIA_TYPES 속성 제거      성공 응답용 produces가 오류 응답을 제약하지 않게
 | L1215 응답이 아직 커밋 전이면
 |         Content-Type, Content-Disposition 헤더 비우기 + 버퍼 비우기
 |         이미 커밋됐으면 IllegalStateException 삼키고 진행   (본문 일부가 이미 나감)
 |
 +-- for resolver in handlerExceptionResolvers   첫 non-null에서 멈춤
 |     ExceptionHandlerExceptionResolver     @ExceptionHandler 메서드 실행
 |     ResponseStatusExceptionResolver       @ResponseStatus 예외, ResponseStatusException --> sendError
 |     DefaultHandlerExceptionResolver       Spring MVC 표준 예외 --> 400/404/405/406/415... sendError
 |
 +-- exMv == null           --> throw ex     (아무도 처리 못함)
 +-- exMv.isEmpty()         --> EXCEPTION_ATTRIBUTE에 ex 기록, return null   (응답은 리졸버가 이미 씀)
 +-- 뷰 없는 exMv           --> 요청 URL로 기본 뷰 이름 채움
 +-- WebUtils.exposeErrorRequestAttributes()   jakarta.servlet.error.* 속성 설정
 +-- return exMv            --> 오류 뷰 렌더링
```

## @ExceptionHandler 메서드를 찾고 실행하는 길

첫 번째 리졸버인 `ExceptionHandlerExceptionResolver`의 핵심이다. 컨트롤러 자신의 `@ExceptionHandler`를 먼저 보고, 없으면 `@ControllerAdvice`들을 본다.

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `ExceptionHandlerExceptionResolver.java` L509-L564 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/ExceptionHandlerExceptionResolver.java#L509-L564))

```java
// ExceptionHandlerExceptionResolver.java L509-L564
protected @Nullable ServletInvocableHandlerMethod getExceptionHandlerMethod(
        @Nullable HandlerMethod handlerMethod, Exception exception, ServletWebRequest webRequest) {

    List<MediaType> acceptedMediaTypes = List.of(MediaType.ALL);
    try {
        acceptedMediaTypes = this.contentNegotiationManager.resolveMediaTypes(webRequest);
    }
    catch (HttpMediaTypeNotAcceptableException mediaTypeExc) {
        if (logger.isDebugEnabled()) {
            logger.debug("Could not resolve accepted media types for @ExceptionHandler [" + webRequest.getHeader(HttpHeaders.ACCEPT) + "]", mediaTypeExc);
        }
    }

    Class<?> handlerType = null;

    if (handlerMethod != null) {
        // Local exception handler methods on the controller class itself.
        // To be invoked through the proxy, even in case of an interface-based proxy.
        handlerType = handlerMethod.getBeanType();
        ExceptionHandlerMethodResolver resolver = this.exceptionHandlerCache.computeIfAbsent(
                handlerType, ExceptionHandlerMethodResolver::new);

        for (MediaType mediaType : acceptedMediaTypes) {
            ExceptionHandlerMappingInfo mappingInfo = resolver.resolveExceptionMapping(exception, mediaType);
            if (mappingInfo != null) {
                if (!mappingInfo.getProducibleTypes().isEmpty()) {
                    webRequest.setAttribute(HandlerMapping.PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE, mappingInfo.getProducibleTypes(), RequestAttributes.SCOPE_REQUEST);
                }
                return new ServletInvocableHandlerMethod(handlerMethod.getBean(), mappingInfo.getHandlerMethod(), this.applicationContext);
            }
        }
        // For advice applicability check below (involving base packages, assignable types
        // and annotation presence), use target class instead of interface-based proxy.
        if (Proxy.isProxyClass(handlerType)) {
            handlerType = AopUtils.getTargetClass(handlerMethod.getBean());
        }
    }

    for (Map.Entry<ControllerAdviceBean, ExceptionHandlerMethodResolver> entry : this.exceptionHandlerAdviceCache.entrySet()) {
        ControllerAdviceBean advice = entry.getKey();
        if (advice.isApplicableToBeanType(handlerType)) {
            ExceptionHandlerMethodResolver resolver = entry.getValue();
            for (MediaType mediaType : acceptedMediaTypes) {
                ExceptionHandlerMappingInfo mappingInfo = resolver.resolveExceptionMapping(exception, mediaType);
                if (mappingInfo != null) {
                    if (!mappingInfo.getProducibleTypes().isEmpty()) {
                        webRequest.setAttribute(HandlerMapping.PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE, mappingInfo.getProducibleTypes(), RequestAttributes.SCOPE_REQUEST);
                    }
                    return new ServletInvocableHandlerMethod(advice.resolveBean(), mappingInfo.getHandlerMethod(), this.applicationContext);
                }
            }
        }
    }

    return null;
}
```

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `ExceptionHandlerExceptionResolver.java` L430-L496 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/ExceptionHandlerExceptionResolver.java#L430-L496))

```java
// ExceptionHandlerExceptionResolver.java L430-L496
protected @Nullable ModelAndView doResolveHandlerMethodException(HttpServletRequest request,
        HttpServletResponse response, @Nullable HandlerMethod handlerMethod, Exception exception) {

    ServletWebRequest webRequest = new ServletWebRequest(request, response);
    ServletInvocableHandlerMethod exceptionHandlerMethod = getExceptionHandlerMethod(handlerMethod, exception, webRequest);

    if (exceptionHandlerMethod == null) {
        return null;
    }

    if (this.argumentResolvers != null) {
        exceptionHandlerMethod.setHandlerMethodArgumentResolvers(this.argumentResolvers);
    }
    if (this.returnValueHandlers != null) {
        exceptionHandlerMethod.setHandlerMethodReturnValueHandlers(this.returnValueHandlers);
    }

    ModelAndViewContainer mavContainer = new ModelAndViewContainer();

    ArrayList<Throwable> exceptions = new ArrayList<>();
    try {
        if (logger.isDebugEnabled()) {
            logger.debug("Using @ExceptionHandler " + exceptionHandlerMethod);
        }
        // Expose causes as provided arguments as well
        Throwable exToExpose = exception;
        while (exToExpose != null) {
            exceptions.add(exToExpose);
            Throwable cause = exToExpose.getCause();
            exToExpose = (cause != exToExpose ? cause : null);
        }
        @Nullable Object[] arguments = new Object[exceptions.size() + 1];
        exceptions.toArray(arguments);  // efficient arraycopy call in ArrayList
        arguments[arguments.length - 1] = handlerMethod;
        exceptionHandlerMethod.invokeAndHandle(webRequest, mavContainer, arguments);
    }
    catch (Throwable invocationEx) {
        if (disconnectedClientHelper.checkAndLogClientDisconnectedException(invocationEx)) {
            return new ModelAndView();
        }
        // Any other than the original exception (or a cause) is unintended here,
        // probably an accident (for example, failed assertion or the like).
        if (!exceptions.contains(invocationEx) && logger.isWarnEnabled()) {
            logger.warn("Failure in @ExceptionHandler " + exceptionHandlerMethod, invocationEx);
        }
        // Continue with default processing of the original exception...
        return null;
    }

    if (mavContainer.isRequestHandled()) {
        return new ModelAndView();
    }
    else {
        ModelMap model = mavContainer.getModel();
        HttpStatusCode status = mavContainer.getStatus();
        ModelAndView mav = new ModelAndView(mavContainer.getViewName(), model, status);
        mav.setViewName(mavContainer.getViewName());
        if (!mavContainer.isViewReference()) {
            mav.setView((View) mavContainer.getView());
        }
        if (model instanceof RedirectAttributes redirectAttributes) {
            Map<String, ?> flashAttributes = redirectAttributes.getFlashAttributes();
            RequestContextUtils.getOutputFlashMap(request).putAll(flashAttributes);
        }
        return mav;
    }
}
```

```text
 doResolveHandlerMethodException(request, response, handlerMethod, exception)
 |
 +-- getExceptionHandlerMethod(handlerMethod, exception)
 |     acceptedMediaTypes = Accept 헤더 파싱          (writeWithMessageConverters와 같은 협상 경로)
 |     [1] 컨트롤러 클래스의 ExceptionHandlerMethodResolver  (클래스별 캐시)
 |           for mediaType in accepted
 |             resolveExceptionMapping(exception, mediaType)
 |               예외 타입으로 조회 --> 없으면 getCause()로 재귀
 |               조회는 lookupCache(ConcurrentLruCache, 24)를 거침
 |             찾음 --> @ExceptionHandler(produces)가 있으면 PRODUCIBLE_MEDIA_TYPES 설정
 |                  --> ServletInvocableHandlerMethod(컨트롤러 빈, 처리 메서드)
 |     [2] @ControllerAdvice 목록 (순서대로)
 |           이 컨트롤러 타입에 적용되는 advice만 --> 같은 방식으로 조회
 |     [3] 없음 --> null --> 이 리졸버는 포기, 다음 리졸버로
 |
 +-- 인자/반환값 처리기 연결
 +-- providedArgs = [exception, cause, cause의 cause, ..., handlerMethod]
 +-- exceptionHandlerMethod.invokeAndHandle(webRequest, mavContainer, providedArgs)
 |     = 컨트롤러 실행과 완전히 같은 경로   (인자 해석 -> 실행 -> 반환값 처리)
 |     실행 중 다른 예외 --> 경고 로그, return null   (원래 예외는 다음 리졸버가 처리)
 |
 +-- requestHandled (@ResponseBody 등) --> return new ModelAndView()   빈 mv
 +-- 그 밖                            --> 뷰 이름 + 모델로 ModelAndView
```

- 처리 메서드는 [invokeAndHandle](../../05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/README.md)로 실행된다. 인자 해석과 반환값 처리가 정상 경로와 같다.

## 결과가 쓰이는 곳

```text
 exMv (오류 ModelAndView)
      +-- 뷰 있음 --> processDispatchResult --> render --> 오류 페이지
      +-- null (빈 mv였음) --> processDispatchResult에서 render 생략
                                 = @ExceptionHandler가 본문을 썼거나, sendError가 호출됨
 throw ex
      --> processDispatchResult 밖 --> doDispatch 바깥 catch
      --> triggerAfterCompletion(ex) --> processRequest --> 컨테이너 오류 처리

 lookupCache (ExceptionHandlerMethodResolver L84, 조회 L222)
      --> 같은 (예외 타입, 미디어 타입) 조합은 두 번째 요청부터 메서드 탐색 생략
```

`lookupCache`는 [#37268](../../../../../prs/37268-lru-cache-double-decrement/)에서 고친 `ConcurrentLruCache`다. 이 캐시는 `remove`를 부르지 않으므로, 고친 결함이 이 경로에서 실제로 발화하지는 않는다.

`spring-web` / `org.springframework.web.method.annotation` / `ExceptionHandlerMethodResolver.java` L84-L85 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/annotation/ExceptionHandlerMethodResolver.java#L84-L85))

```java
// ExceptionHandlerMethodResolver.java L84-L85
private final ConcurrentLruCache<ExceptionMapping, ExceptionHandlerMappingInfo> lookupCache = new ConcurrentLruCache<>(24,
        cacheKey -> getMappedMethod(cacheKey.exceptionType(), cacheKey.mediaType()));
```
