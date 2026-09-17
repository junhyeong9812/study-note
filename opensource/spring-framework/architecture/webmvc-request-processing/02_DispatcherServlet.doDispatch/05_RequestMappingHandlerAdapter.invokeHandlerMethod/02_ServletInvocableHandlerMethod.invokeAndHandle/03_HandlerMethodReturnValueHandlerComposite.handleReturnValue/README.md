# HandlerMethodReturnValueHandlerComposite.handleReturnValue

상위: [ServletInvocableHandlerMethod.invokeAndHandle](../README.md)

반환값 처리기 목록을 하나로 감싼 Composite다. 반환 타입을 처리할 수 있는 첫 [HandlerMethodReturnValueHandler](../../../../spi/HandlerMethodReturnValueHandler/README.md)를 골라 맡긴다. 비동기 반환값이면 비동기 처리기만 후보로 삼는다.

## 실제 코드

`spring-web` / `org.springframework.web.method.support` / `HandlerMethodReturnValueHandlerComposite.java` L70-L78 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/HandlerMethodReturnValueHandlerComposite.java#L70-L78))

```java
// HandlerMethodReturnValueHandlerComposite.java L70-L78
public void handleReturnValue(@Nullable Object returnValue, MethodParameter returnType,
        ModelAndViewContainer mavContainer, NativeWebRequest webRequest) throws Exception {

    HandlerMethodReturnValueHandler handler = selectHandler(returnValue, returnType);
    if (handler == null) {
        throw new IllegalArgumentException("Unknown return value type: " + returnType.getParameterType().getName());
    }
    handler.handleReturnValue(returnValue, returnType, mavContainer, webRequest);
}
```

`spring-web` / `org.springframework.web.method.support` / `HandlerMethodReturnValueHandlerComposite.java` L80-L91 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/HandlerMethodReturnValueHandlerComposite.java#L80-L91))

```java
// HandlerMethodReturnValueHandlerComposite.java L80-L91
private @Nullable HandlerMethodReturnValueHandler selectHandler(@Nullable Object value, MethodParameter returnType) {
    boolean isAsyncValue = isAsyncReturnValue(value, returnType);
    for (HandlerMethodReturnValueHandler handler : this.returnValueHandlers) {
        if (isAsyncValue && !(handler instanceof AsyncHandlerMethodReturnValueHandler)) {
            continue;
        }
        if (handler.supportsReturnType(returnType)) {
            return handler;
        }
    }
    return null;
}
```

`@ResponseBody`를 맡는 처리기의 선택 조건과 처리 코드다.

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `RequestResponseBodyMethodProcessor.java` L139-L143 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/RequestResponseBodyMethodProcessor.java#L139-L143))

```java
// RequestResponseBodyMethodProcessor.java L139-L143
public boolean supportsReturnType(MethodParameter returnType) {
    return (this.responseBodyControllerCache.computeIfAbsent(returnType.getContainingClass(),
            clazz -> AnnotatedElementUtils.hasAnnotation(clazz, ResponseBody.class)) ||
            returnType.hasMethodAnnotation(ResponseBody.class));
}
```

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `RequestResponseBodyMethodProcessor.java` L195-L214 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/RequestResponseBodyMethodProcessor.java#L195-L214))

```java
// RequestResponseBodyMethodProcessor.java L195-L214
public void handleReturnValue(@Nullable Object returnValue, MethodParameter returnType,
        ModelAndViewContainer mavContainer, NativeWebRequest webRequest)
        throws IOException, HttpMediaTypeNotAcceptableException, HttpMessageNotWritableException {

    mavContainer.setRequestHandled(true);
    ServletServerHttpRequest inputMessage = createInputMessage(webRequest);
    ServletServerHttpResponse outputMessage = createOutputMessage(webRequest);

    if (returnValue instanceof ProblemDetail detail) {
        outputMessage.setStatusCode(HttpStatusCode.valueOf(detail.getStatus()));
        if (detail.getInstance() == null) {
            URI path = URI.create(inputMessage.getServletRequest().getRequestURI());
            detail.setInstance(path);
        }
        invokeErrorResponseInterceptors(detail, null);
    }

    // Try even with null return value. ResponseBodyAdvice could get involved.
    writeWithMessageConverters(returnValue, returnType, inputMessage, outputMessage);
}
```

## 동작 흐름

```text
 handleReturnValue(returnValue, returnType, mavContainer, webRequest)
 |
 +-- selectHandler(returnValue, returnType)
 |     isAsyncValue = 비동기 처리기 중 누가 "이건 비동기 값"이라고 답하나
 |     for handler in returnValueHandlers
 |        isAsyncValue 인데 비동기 처리기가 아님 --> 건너뜀
 |        handler.supportsReturnType(returnType) --> 첫 true 채택
 |
 +-- 없음 --> IllegalArgumentException("Unknown return value type")
 |
 +-- handler.handleReturnValue(...)
```

`@RestController`의 `User` 반환이 `RequestResponseBodyMethodProcessor`에 도착한 뒤다.

```text
 RequestResponseBodyMethodProcessor.handleReturnValue
 |
 | L199 mavContainer.setRequestHandled(true)     <-- 가장 먼저. "뷰는 없다"는 선언
 | L200 inputMessage  = ServletServerHttpRequest  (Accept 헤더 읽기용)
 | L201 outputMessage = ServletServerHttpResponse (헤더, 본문 쓰기용)
 |
 +-- 반환값이 ProblemDetail 이면
 |     상태 코드를 detail.status로, instance가 비었으면 요청 URI로 채움
 |
 +-- L213 writeWithMessageConverters(returnValue, returnType, inputMessage, outputMessage)
          null이어도 호출 (ResponseBodyAdvice가 값을 만들 수 있으므로)
```

- 본문을 실제로 쓰는 [writeWithMessageConverters](01_AbstractMessageConverterMethodProcessor.writeWithMessageConverters/README.md)가 응답 미디어 타입을 정하고 [HttpMessageConverter](../../../../spi/HttpMessageConverter/README.md)를 고른다.

## 결과가 쓰이는 곳

```text
 선택된 처리기별로 mavContainer에 남는 것
      +-- ViewNameMethodReturnValueHandler   (String, void)
      |     viewName = "home"          --> getModelAndView --> render
      |     "redirect:" 접두사면 redirectModelScenario = true
      +-- ModelAndViewMethodReturnValueHandler (ModelAndView)
      |     view, model, status 복사   --> getModelAndView --> render
      +-- RequestResponseBodyMethodProcessor (@ResponseBody)
      |     requestHandled = true      --> getModelAndView가 null --> 렌더링 없음
      +-- HttpEntityMethodProcessor (ResponseEntity)
            requestHandled = true      --> 위와 같음

 selectHandler 결과의 캐시
      없음. 요청마다 목록을 순회한다  (인자 리졸버와 달리)
```

## 하위 메서드

- [01 AbstractMessageConverterMethodProcessor.writeWithMessageConverters](01_AbstractMessageConverterMethodProcessor.writeWithMessageConverters/README.md)
