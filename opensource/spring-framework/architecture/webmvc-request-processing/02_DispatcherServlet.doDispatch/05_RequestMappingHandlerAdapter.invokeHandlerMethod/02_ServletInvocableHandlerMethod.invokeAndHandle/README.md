# ServletInvocableHandlerMethod.invokeAndHandle

상위: [RequestMappingHandlerAdapter.invokeHandlerMethod](../README.md)

컨트롤러 메서드 한 번의 실행 단위다. 인자를 만들어 메서드를 부르고(`invokeForRequest`), 응답 상태를 적용한 뒤, 반환값을 처리기에게 넘긴다. `@ExceptionHandler` 메서드도 이 메서드로 실행된다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `ServletInvocableHandlerMethod.java` L114-L144 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/ServletInvocableHandlerMethod.java#L114-L144))

```java
// ServletInvocableHandlerMethod.java L114-L144
public void invokeAndHandle(ServletWebRequest webRequest, ModelAndViewContainer mavContainer,
        @Nullable Object... providedArgs) throws Exception {

    Object returnValue = invokeForRequest(webRequest, mavContainer, providedArgs);
    setResponseStatus(webRequest);

    if (returnValue == null) {
        if (isRequestNotModified(webRequest) || getResponseStatus() != null || mavContainer.isRequestHandled()) {
            disableContentCachingIfNecessary(webRequest);
            mavContainer.setRequestHandled(true);
            return;
        }
    }
    else if (StringUtils.hasText(getResponseStatusReason())) {
        mavContainer.setRequestHandled(true);
        return;
    }

    mavContainer.setRequestHandled(false);
    Assert.state(this.returnValueHandlers != null, "No return value handlers");
    try {
        this.returnValueHandlers.handleReturnValue(
                returnValue, getReturnValueType(returnValue), mavContainer, webRequest);
    }
    catch (Exception ex) {
        if (logger.isTraceEnabled()) {
            logger.trace(formatErrorForReturnValue(returnValue), ex);
        }
        throw ex;
    }
}
```

`spring-web` / `org.springframework.web.method.support` / `InvocableHandlerMethod.java` L171-L192 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/InvocableHandlerMethod.java#L171-L192))

```java
// InvocableHandlerMethod.java L171-L192
public @Nullable Object invokeForRequest(NativeWebRequest request, @Nullable ModelAndViewContainer mavContainer,
        @Nullable Object... providedArgs) throws Exception {

    @Nullable Object[] args = getMethodArgumentValues(request, mavContainer, providedArgs);
    if (logger.isTraceEnabled()) {
        logger.trace("Arguments: " + Arrays.toString(args));
    }

    if (shouldValidateArguments() && this.methodValidator != null) {
        this.methodValidator.applyArgumentValidation(
                getBean(), getBridgedMethod(), getMethodParameters(), args, getValidationGroups());
    }

    Object returnValue = doInvoke(args);

    if (shouldValidateReturnValue() && this.methodValidator != null) {
        this.methodValidator.applyReturnValueValidation(
                getBean(), getBridgedMethod(), getReturnType(), returnValue, getValidationGroups());
    }

    return returnValue;
}
```

## 동작 흐름

```text
 invokeAndHandle(webRequest, mavContainer, providedArgs...)
 |
 +-- invokeForRequest(...)                           (부모 InvocableHandlerMethod)
 |     | args = getMethodArgumentValues(...)          파라미터마다 리졸버로 값 생성
 |     | 메서드 검증 대상이면 methodValidator.applyArgumentValidation   (@Valid 없이 제약 어노테이션)
 |     | returnValue = doInvoke(args)                 리플렉션 호출
 |     | 반환값 검증 대상이면 applyReturnValueValidation
 |     +-- return returnValue
 |
 | L118 setResponseStatus()     @ResponseStatus가 있으면 응답 상태 코드 설정
 |
 +-- returnValue == null 이고
 |     (304 Not Modified 이거나 | @ResponseStatus 있음 | 이미 requestHandled)
 |       --> requestHandled = true, return        "응답은 끝났다"
 |
 +-- @ResponseStatus(reason = "...") 있음
 |       --> requestHandled = true, return        (reason이 있으면 sendError로 이미 응답됨)
 |
 | L132 requestHandled = false
 +-- L135 returnValueHandlers.handleReturnValue(returnValue, 반환 타입, mavContainer, webRequest)
          실패하면 trace 로그 후 그대로 던짐
```

1. [getMethodArgumentValues](01_InvocableHandlerMethod.getMethodArgumentValues/README.md)가 [HandlerMethodArgumentResolver](../../../spi/HandlerMethodArgumentResolver/README.md)로 인자 배열을 만든다.
2. [doInvoke](02_InvocableHandlerMethod.doInvoke/README.md)가 컨트롤러 메서드를 실제로 부른다.
3. [handleReturnValue](03_HandlerMethodReturnValueHandlerComposite.handleReturnValue/README.md)가 반환 타입에 맞는 [HandlerMethodReturnValueHandler](../../../spi/HandlerMethodReturnValueHandler/README.md)를 골라 처리를 맡긴다.

## 결과가 쓰이는 곳

```text
 returnValue (컨트롤러 메서드의 반환값)
      +-- null + 응답 이미 완료 조건 --> mavContainer.requestHandled = true
      |                                  --> getModelAndView가 null 반환 --> 렌더링 없음
      +-- 그 밖 --> handleReturnValue
              String "home"         --> ViewNameMethodReturnValueHandler --> mavContainer.viewName
              @ResponseBody 객체     --> RequestResponseBodyMethodProcessor --> 본문 쓰기 + requestHandled
              ResponseEntity        --> HttpEntityMethodProcessor --> 헤더, 상태, 본문 쓰기 + requestHandled
              Callable / DeferredResult --> 비동기 처리기 --> 비동기 시작

 providedArgs (호출자가 미리 준 인자)
      +-- 정상 경로                 --> 없음
      +-- @ExceptionHandler 경로    --> [예외, 원인 예외들..., 핸들러 메서드]
                                        getMethodArgumentValues가 타입이 맞는 파라미터에 먼저 꽂음
```

## 하위 메서드

- [01 InvocableHandlerMethod.getMethodArgumentValues](01_InvocableHandlerMethod.getMethodArgumentValues/README.md)
- [02 InvocableHandlerMethod.doInvoke](02_InvocableHandlerMethod.doInvoke/README.md)
- [03 HandlerMethodReturnValueHandlerComposite.handleReturnValue](03_HandlerMethodReturnValueHandlerComposite.handleReturnValue/README.md)
