# AbstractServerResponse.writeTo

상위: [webmvc.HandlerFunctionAdapter.handle](../README.md)

`ServerResponse`는 응답 값이 아니라 "응답을 쓰는 방법"이다. 상태와 헤더를 먼저 쓰고, 조건부 요청이면 거기서 멈추고, 아니면 구현별 본문 쓰기로 내려간다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function` / `AbstractServerResponse.java` L82-L102 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/AbstractServerResponse.java#L82-L102))

```java
// AbstractServerResponse.java L82-L102
public @Nullable ModelAndView writeTo(HttpServletRequest request, HttpServletResponse response,
        Context context) throws ServletException, IOException {

    try {
        writeStatusAndHeaders(response);

        long lastModified = headers().getLastModified();
        ServletWebRequest servletWebRequest = new ServletWebRequest(request, response);
        HttpMethod httpMethod = HttpMethod.valueOf(request.getMethod());
        if (SAFE_METHODS.contains(httpMethod) &&
                servletWebRequest.checkNotModified(headers().getETag(), lastModified)) {
            return null;
        }
        else {
            return writeToInternal(request, response, context);
        }
    }
    catch (Throwable throwable) {
        return handleError(throwable, request, response, context);
    }
}
```

본문을 가진 응답(`ServerResponse.ok().body(user)`)의 구현은 컨버터를 쓴다.

`spring-webmvc` / `org.springframework.web.servlet.function` / `DefaultEntityResponseBuilder.java` L263-L269 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/DefaultEntityResponseBuilder.java#L263-L269))

```java
// DefaultEntityResponseBuilder.java L263-L269
protected @Nullable ModelAndView writeToInternal(HttpServletRequest servletRequest,
        HttpServletResponse servletResponse, Context context)
        throws ServletException, IOException {

    writeEntityWithMessageConverters(this.entity, servletRequest,servletResponse, context);
    return null;
}
```

## 동작 흐름

```text
 writeTo(request, response, context)
 |
 | L86 writeStatusAndHeaders(response)
 |        L105 상태 코드
 |        L106 헤더 (writeHeaders L110-L140, Content-Type 은 서블릿 프로퍼티로도 반영)
 |        L107 쿠키 (writeCookies L142-L146)
 |
 | L88 headers().getLastModified()
 | L90 HttpMethod 확인
 |
 +-- L92 안전한 메서드(GET/HEAD 등)이고 checkNotModified 가 참
 |        --> L93 null 반환. 본문을 쓰지 않는다
 |            서블릿 응답에는 이미 304 가 찍혀 있다
 |
 +-- L96 그 밖
 |        --> writeToInternal(request, response, context)  구현별 본문 쓰기
 |
 +-- L99 도중에 예외가 나면
        --> handleError(throwable, request, response, context)
            등록된 오류 처리로 넘긴다

 DefaultEntityResponse.writeToInternal        L263
 |
 +-- L267 writeEntityWithMessageConverters(entity, ...)
 |        Resource 면 Range 헤더를 보고 206 부분 응답도 만든다 (L281)
 |        context.messageConverters() 를 순회해 쓸 수 있는 컨버터를 고른다
 |
 +-- L268 null 반환 = 뷰 렌더링 없음
```

```text
 구현별 writeToInternal 이 하는 일

 EntityResponse      본문 객체를 HttpMessageConverter 로 쓴다        --> null
 RenderingResponse   모델과 뷰 이름을 담은 ModelAndView 를 만든다    --> ModelAndView
 SseServerResponse   이벤트 스트림을 연다
 AsyncServerResponse 서블릿 비동기로 나갔다가 나중에 다시 쓴다
```

## 결과가 쓰이는 곳

```text
 반환값 (ModelAndView 또는 null)
      --> 어댑터가 그대로 DispatcherServlet 에 돌려준다
      --> null 이면 processDispatchResult 가 렌더링을 건너뛴다
      --> ModelAndView 면 뷰 해석기가 뷰를 찾아 렌더링한다

 상태와 헤더를 본문보다 먼저 쓴다
      --> 본문 쓰기 도중 예외가 나도 상태 줄은 이미 나간 뒤다
      --> 그래서 handleError 가 상태를 다시 정하지 못하는 경우가 생긴다

 checkNotModified 가 참일 때
      --> 본문 쓰기를 통째로 건너뛴다 (ETag/Last-Modified 를 헤더에 넣어 둔 값 기준)
      --> 캐시된 클라이언트에게는 헤더만 나간다
```

응답 인터페이스가 제공하는 빌더 표면은 [ServerResponse](../../spi/ServerResponse/README.md)에 있다. 본문을 쓰는 컨버터 선택 규칙 자체는 [MVC 요청 처리의 writeWithMessageConverters](../../../webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/03_HandlerMethodReturnValueHandlerComposite.handleReturnValue/01_AbstractMessageConverterMethodProcessor.writeWithMessageConverters/README.md)와 같은 원리다.
