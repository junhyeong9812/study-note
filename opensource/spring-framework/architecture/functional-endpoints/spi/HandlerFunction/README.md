# HandlerFunction

상위: [Spring 함수형 엔드포인트](../../README.md) / [spi](../README.md)

요청 하나를 받아 응답 하나를 내놓는 함수다. 인터페이스 전체가 메서드 하나뿐이라 람다가 그대로 핸들러가 된다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function` / `HandlerFunction.java` L28-L36 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/HandlerFunction.java#L28-L36))

```java
// HandlerFunction.java L28-L36
public interface HandlerFunction<T extends ServerResponse> {

    /**
     * Handle the given request.
     * @param request the request to handle
     * @return the response
     */
    T handle(ServerRequest request) throws Exception;

```

리액티브 쪽은 `Mono`로 감싼다.

`spring-webflux` / `org.springframework.web.reactive.function.server` / `HandlerFunction.java` L30-L38 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/HandlerFunction.java#L30-L38))

```java
// HandlerFunction.java L30-L38
public interface HandlerFunction<T extends ServerResponse> {

    /**
     * Handle the given request.
     * @param request the request to handle
     * @return the response
     */
    Mono<T> handle(ServerRequest request);

```

## 흐름에서 불리는 자리

```text
 HandlerFunctionAdapter.handle
   handlerFunction.handle(serverRequest)
     서블릿  --> ServerResponse       (바로 값)
     리액티브 --> Mono<ServerResponse> (조립만)
```

- [webmvc.HandlerFunctionAdapter.handle](../../02_webmvc.HandlerFunctionAdapter.handle/README.md)
- [webflux.HandlerFunctionAdapter.handle](../../04_webflux.HandlerFunctionAdapter.handle/README.md)

## 구현 계층

```text
 HandlerFunction<T>
   +-- (사용자 람다)                    req -> ServerResponse.ok().body(...)
   +-- (메서드 참조)                    userHandler::list
   +-- ResourceHandlerFunction          정적 리소스 응답
   +-- PathResourceLookupFunction 등이 만드는 내부 핸들러
```

```text
 애노테이션 컨트롤러와의 차이

 @GetMapping 메서드   인자를 프레임워크가 해석해 넣어 준다 (기본 리졸버 28종, Kotlin 이면 29종)
 HandlerFunction     인자는 ServerRequest 하나. 필요한 값은 직접 꺼낸다
                     request.pathVariable("id"), request.body(User.class)
 반환                 값(뷰 이름, 객체, ResponseEntity ...)을 프레임워크가 해석
 반환                 ServerResponse 하나. 상태/헤더/본문을 직접 정한다
```

## 결과가 쓰이는 곳

```text
 반환한 ServerResponse
      --> 서블릿: 어댑터가 곧바로 writeTo 를 부른다
      --> 리액티브: HandlerResult 로 감싸 ServerResponseResultHandler 가 받는다

 예외를 던지면
      --> 서블릿: 평소처럼 HandlerExceptionResolver 체인으로 간다
      --> 리액티브: Mono 의 오류 신호로 흘러 WebExceptionHandler 가 받는다

 반환 타입에 @Nullable 이 없다
      --> 계약상 null 을 돌려주면 안 된다
      --> 어댑터의 null 분기(L109)는 비동기 결과가 없을 때를 위한 것이다
```
