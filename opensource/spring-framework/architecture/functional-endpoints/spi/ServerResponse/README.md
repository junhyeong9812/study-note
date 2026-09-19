# ServerResponse

상위: [Spring 함수형 엔드포인트](../../README.md) / [spi](../README.md)

응답 값이 아니라 "응답을 쓰는 방법"이다. 상태와 헤더를 들고 있다가, 때가 되면 자기 손으로 서블릿 응답(또는 리액티브 교환)에 쓴다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function` / `ServerResponse.java` L60-L86 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/ServerResponse.java#L60-L86))

```java
// ServerResponse.java L60-L86
public interface ServerResponse {

    HttpStatusCode statusCode();

    HttpHeaders headers();

    MultiValueMap<String, Cookie> cookies();

    @Nullable ModelAndView writeTo(HttpServletRequest request, HttpServletResponse response, Context context)
        throws ServletException, IOException;
```

리액티브 쪽은 쓰기 결과가 `Mono<Void>`다.

`spring-webflux` / `org.springframework.web.reactive.function.server` / `ServerResponse.java` L62-L70 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/ServerResponse.java#L62-L70))

```java
// ServerResponse.java L62-L70
public interface ServerResponse {

    HttpStatusCode statusCode();

```

## 흐름에서 불리는 자리

```text
 서블릿
   HandlerFunctionAdapter.handle
     serverResponse.writeTo(servletRequest, servletResponse, context)  --> ModelAndView 또는 null
 리액티브
   ServerResponseResultHandler.handleResult
     response.writeTo(exchange, context)                                --> Mono<Void>
```

- [AbstractServerResponse.writeTo](../../02_webmvc.HandlerFunctionAdapter.handle/01_AbstractServerResponse.writeTo/README.md)
- [webflux.ServerResponseResultHandler.handleResult](../../05_webflux.ServerResponseResultHandler.handleResult/README.md)

## 구현 계층

```text
 ServerResponse
   +-- ErrorHandlingServerResponse        쓰기 도중 예외를 오류 처리로 넘기는 공통 부모
   |     +-- AbstractServerResponse       상태/헤더/쿠키를 먼저 쓰고 writeToInternal 위임
   |           +-- WriteFunctionResponse  본문 없음 (ok().build())
   |           +-- DefaultEntityResponse  본문 객체 (EntityResponse 구현)
   |           +-- DefaultRenderingResponse  뷰 이름 + 모델 (RenderingResponse 구현)
   |           +-- SseServerResponse      서버 전송 이벤트
   |           +-- StreamingServerResponse  스트리밍 본문
   +-- AsyncServerResponse                비동기 응답 (인터페이스)
         +-- CompletedAsyncServerResponse
         +-- DefaultAsyncServerResponse     구현은 ErrorHandlingServerResponse 도 상속한다

 만드는 방법 (정적 메서드)
   ServerResponse.ok() / status(code) / created(uri) / noContent() / badRequest() ...
     --> HeadersBuilder 또는 BodyBuilder
   BodyBuilder.body(객체)      EntityResponse
   BodyBuilder.render(뷰 이름)  RenderingResponse
   HeadersBuilder.build()      본문 없는 응답
```

## 결과가 쓰이는 곳

```text
 writeTo 의 반환값 (서블릿)
      --> null 이면 응답이 끝났다는 뜻. DispatcherServlet 이 렌더링을 건너뛴다
      --> ModelAndView 면 뷰 해석과 렌더링으로 이어진다 (RenderingResponse)

 writeTo 의 반환값 (리액티브)
      --> Mono<Void>. 구독 시점에 실제 쓰기가 일어난다

 빌더로 정한 상태와 헤더
      --> 본문보다 먼저 서블릿 응답에 반영된다
      --> 그래서 본문 쓰기 도중 예외가 나면 상태 줄은 이미 나간 뒤다

 Context
      --> 서블릿: messageConverters() 와 viewResolvers()
      --> 리액티브: messageWriters() 와 viewResolvers()
      --> 응답 객체가 프레임워크 설정에 닿는 유일한 통로다
```
