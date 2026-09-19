# HandlerExecutionChain

상위: [DispatcherServlet.doDispatch](../README.md)

핸들러 하나와 그 앞뒤에 도는 [HandlerInterceptor](../../spi/HandlerInterceptor/README.md) 목록의 묶음이다. `applyPreHandle`이 기록하고 `triggerAfterCompletion`이 읽는 필드 `interceptorIndex`로 두 메서드가 엮여 있어 한 폴더에서 같이 본다. 이 필드가 "`preHandle`을 어디까지 성공했나"를 기억한다. `applyPostHandle`은 이 필드를 쓰지 않고 항상 목록 끝에서부터 역순으로 돈다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `HandlerExecutionChain.java` L142-L181 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/HandlerExecutionChain.java#L142-L181))

```java
// HandlerExecutionChain.java L142-L181
boolean applyPreHandle(HttpServletRequest request, HttpServletResponse response) throws Exception {
    for (int i = 0; i < this.interceptorList.size(); i++) {
        HandlerInterceptor interceptor = this.interceptorList.get(i);
        if (!interceptor.preHandle(request, response, this.handler)) {
            triggerAfterCompletion(request, response, null);
            return false;
        }
        this.interceptorIndex = i;
    }
    return true;
}

/**
 * Apply postHandle methods of registered interceptors.
 */
void applyPostHandle(HttpServletRequest request, HttpServletResponse response, @Nullable ModelAndView mv)
        throws Exception {

    for (int i = this.interceptorList.size() - 1; i >= 0; i--) {
        HandlerInterceptor interceptor = this.interceptorList.get(i);
        interceptor.postHandle(request, response, this.handler, mv);
    }
}

/**
 * Trigger afterCompletion callbacks on the mapped HandlerInterceptors.
 * Will just invoke afterCompletion for all interceptors whose preHandle invocation
 * has successfully completed and returned true.
 */
void triggerAfterCompletion(HttpServletRequest request, HttpServletResponse response, @Nullable Exception ex) {
    for (int i = this.interceptorIndex; i >= 0; i--) {
        HandlerInterceptor interceptor = this.interceptorList.get(i);
        try {
            interceptor.afterCompletion(request, response, this.handler, ex);
        }
        catch (Throwable ex2) {
            logger.error("HandlerInterceptor.afterCompletion threw exception in interceptor [" + interceptor + "]", ex2);
        }
    }
}
```

## 동작 흐름

인터셉터 A, B, C가 등록되어 있고 B의 `preHandle`이 false를 돌려주는 경우다.

```text
 applyPreHandle                       interceptorIndex
 |  i=0  A.preHandle -> true           --> 0
 |  i=1  B.preHandle -> false
 |         triggerAfterCompletion()    i = 0 부터 역순
 |           A.afterCompletion          (B, C는 부르지 않는다)
 |         return false  --> doDispatch가 그대로 return. 핸들러는 실행되지 않음
```

전부 true인 정상 경로다.

```text
 applyPreHandle        A.pre -> B.pre -> C.pre        interceptorIndex = 2
        |
 handler 실행
        |
 applyPostHandle       C.post -> B.post -> A.post     (역순, 핸들러가 예외 없이 끝났을 때만)
        |
 render (뷰가 있으면)
        |
 triggerAfterCompletion
                       C.after -> B.after -> A.after  (역순, index 2부터)
                       각 호출의 예외는 로그만 남기고 삼킴 --> 다음 인터셉터도 반드시 호출
```

핸들러가 예외를 던진 경로다.

```text
 applyPreHandle  A.pre -> B.pre -> C.pre
 handler         예외
 applyPostHandle 건너뜀        (doDispatch의 try 블록을 빠져나갔으므로)
 processDispatchResult --> 예외 해석, 오류 뷰 렌더링
 triggerAfterCompletion(null)  C.after -> B.after -> A.after
```

## 결과가 쓰이는 곳

```text
 applyPreHandle의 boolean
      +-- false --> doDispatch L958 return   응답은 인터셉터가 썼다고 간주 (예: 401 전송)
      +-- true  --> 어댑터 호출로 진행

 interceptorIndex
      --> triggerAfterCompletion의 시작점
          = "preHandle이 true였던 인터셉터에게만 afterCompletion을 보장"
          --> 자원을 preHandle에서 열고 afterCompletion에서 닫는 짝이 항상 맞는다

 applyPostHandle에 넘기는 mv
      --> 인터셉터가 모델에 공통 속성을 추가하거나 뷰 이름을 바꿀 수 있는 마지막 자리
          (@ResponseBody면 mv가 null이고 본문은 이미 쓰였으므로 응답을 바꿀 수 없다)
```

`afterCompletion`이 불리는 자리는 세 곳이다. `preHandle`이 false일 때(위), [processDispatchResult](../06_DispatcherServlet.processDispatchResult/README.md)의 마지막, 그리고 결과 처리 자체가 실패했을 때 `doDispatch`의 바깥 catch(L983)다.
