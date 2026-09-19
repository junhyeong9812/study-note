# FrameworkServlet.processRequest

상위: [Spring MVC 요청 처리](../README.md)

서블릿 컨테이너가 부른 요청을 받아, 현재 스레드에 Locale과 요청 객체를 걸어 두고 `doService`로 넘긴다. 끝나면 원래대로 되돌리고 처리 완료 이벤트를 발행한다.

## 진입: service

`spring-webmvc` / `org.springframework.web.servlet` / `FrameworkServlet.java` L868-L877 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/FrameworkServlet.java#L868-L877))

```java
// FrameworkServlet.java L868-L877
protected void service(HttpServletRequest request, HttpServletResponse response)
        throws ServletException, IOException {

    if (HTTP_SERVLET_METHODS.contains(request.getMethod())) {
        super.service(request, response);
    }
    else {
        processRequest(request, response);
    }
}
```

```text
 request.getMethod()
      |
      +-- 표준 8종 (GET HEAD POST PUT PATCH DELETE OPTIONS TRACE)
      |       --> HttpServlet.service --> doGet/doPost/... --> processRequest
      +-- 그 밖의 메서드 (WebDAV PROPFIND 등)
              --> processRequest (바로)
```

`doGet`, `doPost`, `doPut`, `doDelete`, `doPatch`는 모두 한 줄짜리로 `processRequest`만 부른다. `doOptions`와 `doTrace`는 다르다. `dispatchOptionsRequest`, `dispatchTraceRequest`(둘 다 기본 false)가 켜져 있거나 CORS preflight 요청일 때만 `processRequest`로 가고, 그 밖에는 서블릿 기본 구현이 처리한다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `FrameworkServlet.java` L983-L1020 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/FrameworkServlet.java#L983-L1020))

```java
// FrameworkServlet.java L983-L1020
protected final void processRequest(HttpServletRequest request, HttpServletResponse response)
        throws ServletException, IOException {

    long startTime = System.currentTimeMillis();
    Throwable failureCause = null;

    LocaleContext previousLocaleContext = LocaleContextHolder.getLocaleContext();
    LocaleContext localeContext = buildLocaleContext(request);

    RequestAttributes previousAttributes = RequestContextHolder.getRequestAttributes();
    ServletRequestAttributes requestAttributes = buildRequestAttributes(request, response, previousAttributes);

    WebAsyncManager asyncManager = WebAsyncUtils.getAsyncManager(request);
    asyncManager.registerCallableInterceptor(FrameworkServlet.class.getName(), new RequestBindingInterceptor());

    initContextHolders(request, localeContext, requestAttributes);

    try {
        doService(request, response);
    }
    catch (ServletException | IOException ex) {
        failureCause = ex;
        throw ex;
    }
    catch (Throwable ex) {
        failureCause = ex;
        throw new ServletException("Request processing failed: " + ex, ex);
    }

    finally {
        resetContextHolders(request, previousLocaleContext, previousAttributes);
        if (requestAttributes != null) {
            requestAttributes.requestCompleted();
        }
        logResult(request, response, failureCause, asyncManager);
        publishRequestHandledEvent(request, response, startTime, failureCause);
    }
}
```

## 동작 흐름

```text
 processRequest(request, response)
      |
      +-- 1. 이전 LocaleContext / RequestAttributes 보관      (복원용)
      +-- 2. 이번 요청용 LocaleContext / ServletRequestAttributes 생성
      +-- 3. initContextHolders()  --> ThreadLocal에 바인딩
      |
      +-- 4. try   doService(request, response)
      |      catch  ServletException/IOException --> 그대로 던짐
      |             그 밖의 Throwable          --> ServletException으로 감싸 던짐
      |
      +-- 5. finally
             +-- resetContextHolders()     --> 1에서 보관한 값으로 복원
             +-- requestAttributes.requestCompleted()   request scope 빈 소멸 콜백
             +-- publishRequestHandledEvent()           성공이든 실패든 발행
```

- 4의 `doService`는 [DispatcherServlet.doDispatch](../02_DispatcherServlet.doDispatch/README.md) 앞에서 요청 속성(WebApplicationContext, LocaleResolver, FlashMap)을 심고 요청 경로를 파싱해 캐시한 뒤 `doDispatch`를 부른다.

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L829-L879 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L829-L879))

```java
// DispatcherServlet.java L829-L879
protected void doService(HttpServletRequest request, HttpServletResponse response) throws Exception {
    logRequest(request);

    // Keep a snapshot of the request attributes in case of an include,
    // to be able to restore the original attributes after the include.
    Map<String, Object> attributesSnapshot = null;
    if (WebUtils.isIncludeRequest(request)) {
        attributesSnapshot = new HashMap<>();
        Enumeration<?> attrNames = request.getAttributeNames();
        while (attrNames.hasMoreElements()) {
            String attrName = (String) attrNames.nextElement();
            if (this.cleanupAfterInclude || attrName.startsWith(DEFAULT_STRATEGIES_PREFIX)) {
                attributesSnapshot.put(attrName, request.getAttribute(attrName));
            }
        }
    }

    // Make framework objects available to handlers and view objects.
    request.setAttribute(WEB_APPLICATION_CONTEXT_ATTRIBUTE, getWebApplicationContext());
    request.setAttribute(LOCALE_RESOLVER_ATTRIBUTE, this.localeResolver);

    if (this.flashMapManager != null) {
        FlashMap inputFlashMap = this.flashMapManager.retrieveAndUpdate(request, response);
        if (inputFlashMap != null) {
            request.setAttribute(INPUT_FLASH_MAP_ATTRIBUTE, Collections.unmodifiableMap(inputFlashMap));
        }
        request.setAttribute(OUTPUT_FLASH_MAP_ATTRIBUTE, new FlashMap());
        request.setAttribute(FLASH_MAP_MANAGER_ATTRIBUTE, this.flashMapManager);
    }

    RequestPath previousRequestPath = null;
    if (this.parseRequestPath) {
        previousRequestPath = (RequestPath) request.getAttribute(ServletRequestPathUtils.PATH_ATTRIBUTE);
        ServletRequestPathUtils.parseAndCache(request);
    }

    try {
        doDispatch(request, response);
    }
    finally {
        if (!WebAsyncUtils.getAsyncManager(request).isConcurrentHandlingStarted()) {
            // Restore the original attribute snapshot, in case of an include.
            if (attributesSnapshot != null) {
                restoreAttributesAfterInclude(request, attributesSnapshot);
            }
        }
        if (this.parseRequestPath) {
            ServletRequestPathUtils.setParsedRequestPath(previousRequestPath, request);
        }
    }
}
```

## 결과가 쓰이는 곳

```text
 3에서 바인딩한 ServletRequestAttributes
      |
      +-- 컨트롤러/서비스 어디서든 RequestContextHolder.currentRequestAttributes()
      |       --> 파라미터로 받지 않아도 현재 요청에 접근
      +-- @RequestScope / @SessionScope 빈
              --> 이 객체에 빈을 저장하고, 5의 requestCompleted()에서 소멸

 doService가 심은 요청 속성
      |
      +-- WEB_APPLICATION_CONTEXT_ATTRIBUTE --> RequestContextUtils.findWebApplicationContext()
      +-- INPUT_FLASH_MAP_ATTRIBUTE         --> 리다이렉트 직후 요청의 모델 초기값
      |                                         (invokeHandlerMethod의 mavContainer.addAllAttributes)
      +-- parseAndCache 한 RequestPath       --> HandlerMapping의 URL 매칭 입력
```
