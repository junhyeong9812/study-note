# RequestMappingHandlerAdapter.invokeHandlerMethod

상위: [DispatcherServlet.doDispatch](../README.md)

`@RequestMapping` 메서드 하나를 실행하기 위한 무대를 차린다. 바인더 공장, 모델 공장, 실행 래퍼, 모델 컨테이너를 만들고 실행을 맡긴 뒤, 컨테이너에 남은 결과를 `ModelAndView`로 바꿔 돌려준다.

## 진입: handleInternal

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `RequestMappingHandlerAdapter.java` L835-L870 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/RequestMappingHandlerAdapter.java#L835-L870))

```java
// RequestMappingHandlerAdapter.java L835-L870
protected @Nullable ModelAndView handleInternal(HttpServletRequest request,
        HttpServletResponse response, HandlerMethod handlerMethod) throws Exception {

    ModelAndView mav;
    checkRequest(request);

    // Execute invokeHandlerMethod in synchronized block if required.
    if (this.synchronizeOnSession) {
        HttpSession session = request.getSession(false);
        if (session != null) {
            Object mutex = WebUtils.getSessionMutex(session);
            synchronized (mutex) {
                mav = invokeHandlerMethod(request, response, handlerMethod);
            }
        }
        else {
            // No HttpSession available -> no mutex necessary
            mav = invokeHandlerMethod(request, response, handlerMethod);
        }
    }
    else {
        // No synchronization on session demanded at all...
        mav = invokeHandlerMethod(request, response, handlerMethod);
    }

    if (!response.containsHeader(HEADER_CACHE_CONTROL)) {
        if (getSessionAttributesHandler(handlerMethod).hasSessionAttributes()) {
            applyCacheSeconds(response, this.cacheSecondsForSessionAttributeHandlers);
        }
        else {
            prepareResponse(response);
        }
    }

    return mav;
}
```

```text
 handleInternal
 |  checkRequest()                지원 HTTP 메서드, 세션 필수 여부 검사
 |  synchronizeOnSession ?
 |     yes + 세션 있음 --> 세션 mutex로 synchronized 하고 invokeHandlerMethod
 |     그 밖           --> 그냥 invokeHandlerMethod
 |  Cache-Control 헤더가 아직 없으면
 |     @SessionAttributes 핸들러 --> 캐시 금지 초 적용
 |     그 밖                     --> prepareResponse (설정된 캐시 정책)
 +-- return mav
```

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `RequestMappingHandlerAdapter.java` L889-L944 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/RequestMappingHandlerAdapter.java#L889-L944))

```java
// RequestMappingHandlerAdapter.java L889-L944
protected @Nullable ModelAndView invokeHandlerMethod(HttpServletRequest request,
        HttpServletResponse response, HandlerMethod handlerMethod) throws Exception {

    WebAsyncManager asyncManager = WebAsyncUtils.getAsyncManager(request);
    AsyncWebRequest asyncWebRequest = WebAsyncUtils.createAsyncWebRequest(request, response);
    asyncWebRequest.setTimeout(this.asyncRequestTimeout);

    asyncManager.setTaskExecutor(this.taskExecutor);
    asyncManager.setAsyncWebRequest(asyncWebRequest);
    asyncManager.registerCallableInterceptors(this.callableInterceptors);
    asyncManager.registerDeferredResultInterceptors(this.deferredResultInterceptors);

    // Obtain wrapped response to enforce lifecycle rule from Servlet spec, section 2.3.3.4
    response = asyncWebRequest.getNativeResponse(HttpServletResponse.class);

    ServletWebRequest webRequest = (asyncWebRequest instanceof ServletWebRequest ?
            (ServletWebRequest) asyncWebRequest : new ServletWebRequest(request, response));

    WebDataBinderFactory binderFactory = getDataBinderFactory(handlerMethod);
    ModelFactory modelFactory = getModelFactory(handlerMethod, binderFactory);

    ServletInvocableHandlerMethod invocableMethod = createInvocableHandlerMethod(handlerMethod);
    if (this.argumentResolvers != null) {
        invocableMethod.setHandlerMethodArgumentResolvers(this.argumentResolvers);
    }
    if (this.returnValueHandlers != null) {
        invocableMethod.setHandlerMethodReturnValueHandlers(this.returnValueHandlers);
    }
    invocableMethod.setDataBinderFactory(binderFactory);
    invocableMethod.setParameterNameDiscoverer(this.parameterNameDiscoverer);
    invocableMethod.setMethodValidator(this.methodValidator);

    ModelAndViewContainer mavContainer = new ModelAndViewContainer();
    mavContainer.addAllAttributes(RequestContextUtils.getInputFlashMap(request));
    modelFactory.initModel(webRequest, mavContainer, invocableMethod);

    if (asyncManager.hasConcurrentResult()) {
        Object result = asyncManager.getConcurrentResult();
        Object[] resultContext = asyncManager.getConcurrentResultContext();
        Assert.state(resultContext != null && resultContext.length > 0, "Missing result context");
        mavContainer = (ModelAndViewContainer) resultContext[0];
        asyncManager.clearConcurrentResult();
        LogFormatUtils.traceDebug(logger, traceOn -> {
            String formatted = LogFormatUtils.formatValue(result, !traceOn);
            return "Resume with async result [" + formatted + "]";
        });
        invocableMethod = invocableMethod.wrapConcurrentResult(result);
    }

    invocableMethod.invokeAndHandle(webRequest, mavContainer);
    if (asyncManager.isConcurrentHandlingStarted()) {
        return null;
    }

    return getModelAndView(mavContainer, modelFactory, webRequest);
}
```

## 동작 흐름

```text
 invokeHandlerMethod(request, response, handlerMethod)
 |
 | L892-899  비동기 준비: AsyncWebRequest 생성, 타임아웃, TaskExecutor, 인터셉터 등록
 |
 | L907  binderFactory  = getDataBinderFactory(handlerMethod)
 |         컨트롤러의 @InitBinder + @ControllerAdvice의 @InitBinder 메서드 수집 (클래스별 캐시)
 | L908  modelFactory   = getModelFactory(handlerMethod, binderFactory)
 |         @ModelAttribute 메서드 + @SessionAttributes 처리기 수집 (클래스별 캐시)
 |
 | L910  invocableMethod = createInvocableHandlerMethod(handlerMethod)
 |         = ServletInvocableHandlerMethod
 |         + argumentResolvers    (@RequestParam, @RequestBody ... 기본 28개, Kotlin 이 있으면 29개, L648)
 |         + returnValueHandlers  (@ResponseBody, 뷰 이름, ResponseEntity ... 기본 15개, L734)
 |         + binderFactory, parameterNameDiscoverer, methodValidator
 |
 | L921  mavContainer = new ModelAndViewContainer()
 | L922    + 리다이렉트로 넘어온 flash 속성
 | L923  modelFactory.initModel(...)       세션 속성 병합 + @ModelAttribute 메서드 실행
 |
 | L925  비동기 결과를 들고 재디스패치된 요청이면
 |         mavContainer를 첫 요청 때 것으로 복원
 |         invocableMethod를 "결과를 바로 돌려주는" 래퍼로 교체
 |
 | L938  invocableMethod.invokeAndHandle(webRequest, mavContainer)
 |         인자 해석 -> 컨트롤러 실행 -> 반환값 처리   결과는 mavContainer에 남음
 |
 | L939  비동기가 시작됐으면 return null    (응답은 나중에)
 |
 +-- L943 getModelAndView(mavContainer, modelFactory, webRequest)
```

1. [initModel](01_ModelFactory.initModel/README.md)이 컨트롤러 메서드보다 먼저 `@ModelAttribute` 메서드를 실행해 모델을 채운다.
2. [invokeAndHandle](02_ServletInvocableHandlerMethod.invokeAndHandle/README.md)이 인자를 만들고 컨트롤러를 부르고 반환값을 처리한다.
3. [getModelAndView](03_RequestMappingHandlerAdapter.getModelAndView/README.md)가 컨테이너를 보고 `ModelAndView` 또는 null을 만든다.

## 결과가 쓰이는 곳

```text
 mavContainer (ModelAndViewContainer)  -- 이 메서드 안에서 세 단계가 공유하는 칠판
      +-- initModel          가 모델을 채움
      +-- invokeAndHandle    가 뷰 이름 / requestHandled 플래그 / 모델 추가를 기록
      +-- getModelAndView    가 읽어서 ModelAndView로 변환

 binderFactory
      +-- initModel의 @ModelAttribute 메서드 인자 해석
      +-- invokeAndHandle의 @ModelAttribute, @RequestParam 타입 변환과 검증

 반환 ModelAndView (또는 null)
      --> doDispatch L963 mv --> applyPostHandle --> processDispatchResult
```

## 하위 메서드

- [01 ModelFactory.initModel](01_ModelFactory.initModel/README.md)
- [02 ServletInvocableHandlerMethod.invokeAndHandle](02_ServletInvocableHandlerMethod.invokeAndHandle/README.md)
- [03 RequestMappingHandlerAdapter.getModelAndView](03_RequestMappingHandlerAdapter.getModelAndView/README.md)
