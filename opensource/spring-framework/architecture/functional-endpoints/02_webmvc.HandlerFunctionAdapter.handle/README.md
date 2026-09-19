# webmvc.HandlerFunctionAdapter.handle

상위: [Spring 함수형 엔드포인트](../README.md)

매핑이 고른 핸들러 함수를 실제로 부르는 자리다. 애노테이션 경로의 어댑터가 인자 해석과 반환값 처리에 수백 줄을 쓰는 것과 달리, 여기서는 함수를 한 번 부르고 그 결과에게 응답 쓰기를 맡긴다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function.support` / `HandlerFunctionAdapter.java` L86-L88 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/support/HandlerFunctionAdapter.java#L86-L88))

```java
// HandlerFunctionAdapter.java L86-L88
public boolean supports(Object handler) {
    return handler instanceof HandlerFunction;
}
```

`spring-webmvc` / `org.springframework.web.servlet.function.support` / `HandlerFunctionAdapter.java` L91-L115 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/support/HandlerFunctionAdapter.java#L91-L115))

```java
// HandlerFunctionAdapter.java L91-L115
public @Nullable ModelAndView handle(HttpServletRequest servletRequest,
        HttpServletResponse servletResponse,
        Object handler) throws Exception {

    WebAsyncManager asyncManager = getWebAsyncManager(servletRequest, servletResponse);
    servletResponse = getWrappedResponse(asyncManager);

    ServerRequest serverRequest = getServerRequest(servletRequest);
    ServerResponse serverResponse;

    if (asyncManager.hasConcurrentResult()) {
        serverResponse = handleAsync(asyncManager);
    }
    else {
        HandlerFunction<?> handlerFunction = (HandlerFunction<?>) handler;
        serverResponse = handlerFunction.handle(serverRequest);
    }

    if (serverResponse != null) {
        return serverResponse.writeTo(servletRequest, servletResponse, new ServerRequestContext(serverRequest));
    }
    else {
        return null;
    }
}
```

## 동작 흐름

```text
 handle(servletRequest, servletResponse, handler)
 |
 | L95 WebAsyncManager 준비 (비동기 응답을 위한 것)
 | L96 비동기 규칙을 지키는 응답 래퍼로 교체
 |
 | L98 getServerRequest(servletRequest)
 |        요청 속성 RouterFunctions.REQUEST_ATTRIBUTE 에서 꺼낸다
 |        없으면 IllegalStateException (매핑 단계를 거치지 않았다는 뜻)
 |
 +-- L101 이미 비동기 결과가 있다 (두 번째 진입)
 |        --> handleAsync(asyncManager) 로 보관해 둔 응답을 꺼낸다
 |      그 밖 (첫 진입)
 |        --> L106 handlerFunction.handle(serverRequest)
 |              사용자가 쓴 람다가 여기서 실행된다
 |              반환값은 ServerResponse
 |
 +-- L109 응답이 null 이 아니면
 |        --> L110 serverResponse.writeTo(servletRequest, servletResponse, context)
 |              context 는 ServerRequestContext — 컨버터와 뷰 해석기를 담는다
 |      null 이면
        --> L113 null 반환. 응답은 핸들러가 직접 다 썼다는 뜻
```

```text
 supports(handler)                              L86
   handler instanceof HandlerFunction 하나뿐
   = 어댑터 선택에 타입 검사 외의 조건이 없다
```

1. 응답을 실제로 쓰는 단계는 [AbstractServerResponse.writeTo](01_AbstractServerResponse.writeTo/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 반환한 ModelAndView
      --> null 이면 DispatcherServlet 은 응답이 끝났다고 보고 렌더링을 건너뛴다
      --> 값이 있으면 (RenderingResponse) 평소처럼 뷰 해석과 렌더링으로 이어진다

 ServerRequest 를 속성에서 꺼내 쓰는 이유
      --> 매핑 단계에서 만든 것과 같은 인스턴스여야 한다
      --> 새로 만들려면 ServerRequest.create 에 넘길 컨버터 목록과 API 버전 전략이 필요한데
          어댑터는 그것을 갖고 있지 않다

 비동기 두 단계
      --> 첫 진입에서 AsyncServerResponse 를 받으면 서블릿 비동기로 나갔다가
          결과가 준비되면 같은 어댑터가 다시 불린다 (L101 분기)
```

같은 좌석을 애노테이션 컨트롤러가 채우면 [RequestMappingHandlerAdapter.invokeHandlerMethod](../../webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/README.md)로 간다.

## 하위 메서드

- [01 AbstractServerResponse.writeTo](01_AbstractServerResponse.writeTo/README.md)
