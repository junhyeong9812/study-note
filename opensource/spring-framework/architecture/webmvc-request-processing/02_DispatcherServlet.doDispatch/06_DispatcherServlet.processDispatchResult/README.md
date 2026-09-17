# DispatcherServlet.processDispatchResult

상위: [DispatcherServlet.doDispatch](../README.md)

핸들러 단계가 남긴 두 결과(`mv`와 `dispatchException`)를 받아 마무리한다. 예외가 있으면 오류용 `ModelAndView`로 바꾸고, 그릴 뷰가 있으면 그리고, 마지막으로 인터셉터의 `afterCompletion`을 부른다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L1022-L1062 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L1022-L1062))

```java
// DispatcherServlet.java L1022-L1062
private void processDispatchResult(HttpServletRequest request, HttpServletResponse response,
        @Nullable HandlerExecutionChain mappedHandler, @Nullable ModelAndView mv,
        @Nullable Exception exception) throws Exception {

    boolean errorView = false;

    if (exception != null) {
        if (exception instanceof ModelAndViewDefiningException mavDefiningException) {
            logger.debug("ModelAndViewDefiningException encountered", exception);
            mv = mavDefiningException.getModelAndView();
        }
        else {
            Object handler = (mappedHandler != null ? mappedHandler.getHandler() : null);
            mv = processHandlerException(request, response, handler, exception);
            errorView = (mv != null);
        }
    }

    // Did the handler return a view to render?
    if (mv != null && !mv.wasCleared()) {
        render(mv, request, response);
        if (errorView) {
            WebUtils.clearErrorRequestAttributes(request);
        }
    }
    else {
        if (logger.isTraceEnabled()) {
            logger.trace("No view rendering, null ModelAndView returned.");
        }
    }

    if (WebAsyncUtils.getAsyncManager(request).isConcurrentHandlingStarted()) {
        // Concurrent handling started during a forward
        return;
    }

    if (mappedHandler != null) {
        // Exception (if any) is already handled..
        mappedHandler.triggerAfterCompletion(request, response, null);
    }
}
```

## 동작 흐름

```text
 processDispatchResult(request, response, mappedHandler, mv, exception)
 |
 +-- exception != null ?
 |     ModelAndViewDefiningException --> 예외가 들고 있는 mv 사용
 |     그 밖 --> mv = processHandlerException(handler, exception)
 |                 errorView = (mv != null)
 |                 아무도 처리 못함 --> 예외가 여기서 다시 던져짐 --> doDispatch 바깥 catch
 |
 +-- mv != null && !mv.wasCleared() ?
 |     yes --> render(mv)
 |             errorView 였으면 오류 요청 속성(jakarta.servlet.error.*) 정리
 |     no  --> "No view rendering"          (@ResponseBody, 예외 처리기가 본문을 쓴 경우)
 |
 +-- 렌더링 중 비동기가 시작됐음 (forward 대상에서) --> return
 |
 +-- mappedHandler != null --> triggerAfterCompletion(null)
       예외는 이미 처리됐으므로 인터셉터에는 null을 넘긴다
```

1. [processHandlerException](01_DispatcherServlet.processHandlerException/README.md)이 [HandlerExceptionResolver](../../spi/HandlerExceptionResolver/README.md) 목록으로 예외를 응답으로 바꾼다.
2. [render](02_DispatcherServlet.render/README.md)가 [ViewResolver](../../spi/ViewResolver/README.md)로 뷰를 찾아 그린다.
3. [triggerAfterCompletion](../03_HandlerExecutionChain/README.md)이 인터셉터를 역순으로 정리한다.

## 결과가 쓰이는 곳

```text
 이 메서드는 값을 돌려주지 않는다. 결과는 응답 자체다.

 exception 처리 결과
      +-- 오류 ModelAndView (뷰 있음)      --> render --> 오류 페이지 HTML
      +-- 빈 ModelAndView                  --> render 안 함 (리졸버가 응답을 직접 씀, 예: sendError(404))
      +-- @ExceptionHandler + @ResponseBody --> 본문 이미 씀 --> 빈 mv --> render 안 함
      +-- 처리 못함                         --> 던짐
             --> doDispatch 바깥 catch --> triggerAfterCompletion(ex)
             --> processRequest --> 서블릿 컨테이너 --> 컨테이너 오류 페이지 (/error)

 triggerAfterCompletion(null)
      --> 인터셉터의 afterCompletion(..., ex = null)
          처리된 예외는 인터셉터에게 보이지 않는다
          (처리 못한 예외만 바깥 catch 경로에서 ex로 전달됨)
```

## 하위 메서드

- [01 processHandlerException](01_DispatcherServlet.processHandlerException/README.md)
- [02 render](02_DispatcherServlet.render/README.md)
