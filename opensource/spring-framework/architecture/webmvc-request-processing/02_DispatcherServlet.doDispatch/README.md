# DispatcherServlet.doDispatch

상위: [Spring MVC 요청 처리](../README.md)

요청 처리의 본체다. 스스로는 아무것도 처리하지 않고, SPI 목록에 차례로 물어 핸들러를 찾고 부르고 결과를 쓰게 한다. 예외는 바로 던지지 않고 모았다가 결과 처리 단계에 한 번에 넘긴다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L935-L1004 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L935-L1004))

```java
// DispatcherServlet.java L935-L1004
protected void doDispatch(HttpServletRequest request, HttpServletResponse response) throws Exception {
    HttpServletRequest processedRequest = request;
    HandlerExecutionChain mappedHandler = null;
    boolean multipartRequestParsed = false;

    WebAsyncManager asyncManager = WebAsyncUtils.getAsyncManager(request);

    try {
        ModelAndView mv = null;
        Exception dispatchException = null;

        try {
            processedRequest = checkMultipart(request);
            multipartRequestParsed = (processedRequest != request);

            // Determine handler for the current request.
            mappedHandler = getHandler(processedRequest);
            if (mappedHandler == null) {
                noHandlerFound(processedRequest, response);
                return;
            }

            if (!mappedHandler.applyPreHandle(processedRequest, response)) {
                return;
            }

            // Determine handler adapter and invoke the handler.
            HandlerAdapter ha = getHandlerAdapter(mappedHandler.getHandler());
            mv = ha.handle(processedRequest, response, mappedHandler.getHandler());

            if (asyncManager.isConcurrentHandlingStarted()) {
                return;
            }

            applyDefaultViewName(processedRequest, mv);
            mappedHandler.applyPostHandle(processedRequest, response, mv);
        }
        catch (Exception ex) {
            dispatchException = ex;
        }
        catch (Throwable err) {
            // As of 4.3, we're processing Errors thrown from handler methods as well,
            // making them available for @ExceptionHandler methods and other scenarios.
            dispatchException = new ServletException("Handler dispatch failed: " + err, err);
        }
        processDispatchResult(processedRequest, response, mappedHandler, mv, dispatchException);
    }
    catch (Exception ex) {
        triggerAfterCompletion(processedRequest, response, mappedHandler, ex);
    }
    catch (Throwable err) {
        triggerAfterCompletion(processedRequest, response, mappedHandler,
                new ServletException("Handler processing failed: " + err, err));
    }
    finally {
        if (asyncManager.isConcurrentHandlingStarted()) {
            // Instead of postHandle and afterCompletion
            if (mappedHandler != null) {
                mappedHandler.applyAfterConcurrentHandlingStarted(processedRequest, response);
            }
            asyncManager.setMultipartRequestParsed(multipartRequestParsed);
        }
        else {
            // Clean up any resources used by a multipart request.
            if (multipartRequestParsed || asyncManager.isMultipartRequestParsed()) {
                cleanupMultipart(processedRequest);
            }
        }
    }
}
```

## 동작 흐름

```text
 doDispatch(request, response)
 |
 +-- try (안쪽)
 |     L947  processedRequest = checkMultipart(request)
 |
 |     L951  mappedHandler = getHandler(processedRequest)
 |             null --> noHandlerFound() --> NoHandlerFoundException 던짐     [E]
 |
 |     L957  mappedHandler.applyPreHandle()
 |             false --> return   (인터셉터가 응답을 이미 썼다고 본다)
 |
 |     L962  ha = getHandlerAdapter(handler)
 |     L963  mv = ha.handle(...)            ModelAndView 또는 null           [E]
 |
 |     L965  비동기 시작됐으면 return        (나머지는 재디스패치 때)
 |
 |     L969  applyDefaultViewName(mv)        뷰 이름 없으면 URL로 추론
 |     L970  mappedHandler.applyPostHandle(mv)                               [E]
 |
 |   catch Exception  --> dispatchException = ex             [E] 표시 자리의 예외가 여기로
 |   catch Throwable  --> dispatchException = new ServletException(err)
 |
 +-- L980  processDispatchResult(mappedHandler, mv, dispatchException)
 |           = 예외 처리 + 렌더링 + afterCompletion
 |
 +-- catch (바깥) --> triggerAfterCompletion(ex)    processDispatchResult 자체가 실패했을 때
 |
 +-- finally --> multipart 임시 파일 정리
```

1. [checkMultipart](01_DispatcherServlet.checkMultipart/README.md)가 multipart 요청이면 래핑한 요청을 돌려준다.
2. [getHandler](02_DispatcherServlet.getHandler/README.md)가 [HandlerMapping](../spi/HandlerMapping/README.md) 목록에서 핸들러와 인터셉터 묶음을 얻는다.
3. [applyPreHandle](03_HandlerExecutionChain/README.md)이 [HandlerInterceptor](../spi/HandlerInterceptor/README.md)의 `preHandle`을 등록 순서대로 부른다.
4. [getHandlerAdapter](04_DispatcherServlet.getHandlerAdapter/README.md)가 이 핸들러를 부를 줄 아는 [HandlerAdapter](../spi/HandlerAdapter/README.md)를 고른다.
5. `ha.handle`이 `@Controller` 메서드라면 [invokeHandlerMethod](05_RequestMappingHandlerAdapter.invokeHandlerMethod/README.md)로 이어져 컨트롤러를 실행한다.
6. [applyPostHandle](03_HandlerExecutionChain/README.md)이 인터셉터를 역순으로 부른다. 핸들러가 예외 없이 끝났을 때만 온다.
7. [processDispatchResult](06_DispatcherServlet.processDispatchResult/README.md)가 예외를 해석하고 뷰를 그리고 `afterCompletion`을 부른다.

## 결과가 쓰이는 곳

```text
 mappedHandler (HandlerExecutionChain)
      +-- L957 applyPreHandle / L970 applyPostHandle      인터셉터 실행
      +-- L962 getHandlerAdapter(mappedHandler.getHandler())  어댑터 선택의 입력
      +-- L980 processDispatchResult                     예외 해석 시 "어느 핸들러에서 났나"
                                                          + afterCompletion 호출 대상

 mv (ModelAndView)
      +-- null     (@ResponseBody: 본문 이미 씀) --> processDispatchResult에서 렌더링 생략
      +-- not null (뷰 반환)                    --> applyDefaultViewName --> postHandle에서 수정 가능
                                                    --> processDispatchResult에서 render

 dispatchException
      +-- null      --> processDispatchResult는 렌더링만
      +-- not null  --> processHandlerException --> 오류용 ModelAndView로 바뀌어 render
                                                --> 아무도 처리 못하면 다시 던짐
```

`Error`까지 `ServletException`으로 감싸 같은 길로 보내기 때문에(L978) `@ExceptionHandler`가 `Error`를 받을 수 있다. 404도 같은 원리다. `noHandlerFound`가 던진 예외를 `DefaultHandlerExceptionResolver`가 404 응답으로 바꾼다.

## 하위 메서드

- [01 checkMultipart](01_DispatcherServlet.checkMultipart/README.md)
- [02 getHandler](02_DispatcherServlet.getHandler/README.md)
- [03 HandlerExecutionChain](03_HandlerExecutionChain/README.md) — preHandle, postHandle, afterCompletion
- [04 getHandlerAdapter](04_DispatcherServlet.getHandlerAdapter/README.md)
- [05 RequestMappingHandlerAdapter.invokeHandlerMethod](05_RequestMappingHandlerAdapter.invokeHandlerMethod/README.md)
- [06 processDispatchResult](06_DispatcherServlet.processDispatchResult/README.md)
