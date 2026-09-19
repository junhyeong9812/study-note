# webflux.ServerResponseResultHandler.handleResult

상위: [Spring 함수형 엔드포인트](../README.md)

리액티브 함수형 경로의 마지막 자리다. 반환값이 `ServerResponse`이기만 하면 이 처리기가 맡고, 실제 쓰기는 응답 객체 자신에게 다시 맡긴다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive.function.server.support` / `ServerResponseResultHandler.java` L105-L107 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/support/ServerResponseResultHandler.java#L105-L107))

```java
// ServerResponseResultHandler.java L105-L107
public boolean supports(HandlerResult result) {
    return (result.getReturnValue() instanceof ServerResponse);
}
```

`spring-webflux` / `org.springframework.web.reactive.function.server.support` / `ServerResponseResultHandler.java` L110-L123 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/support/ServerResponseResultHandler.java#L110-L123))

```java
// ServerResponseResultHandler.java L110-L123
public Mono<Void> handleResult(ServerWebExchange exchange, HandlerResult result) {
    ServerResponse response = (ServerResponse) result.getReturnValue();
    Assert.state(response != null, "No ServerResponse");
    return response.writeTo(exchange, new ServerResponse.Context() {
        @Override
        public List<HttpMessageWriter<?>> messageWriters() {
            return messageWriters;
        }
        @Override
        public List<ViewResolver> viewResolvers() {
            return viewResolvers;
        }
    });
}
```

## 동작 흐름

```text
 supports(result)                               L105
   result.getReturnValue() instanceof ServerResponse
   = 애노테이션 컨트롤러가 돌려준 값은 여기에 걸리지 않는다

 handleResult(exchange, result)
 |
 | L111 반환값을 ServerResponse 로 캐스팅
 | L112 null 이면 IllegalStateException
 |
 +-- L113 response.writeTo(exchange, context)
        context 는 익명 구현으로 두 가지만 노출한다
          L115 messageWriters()   본문 인코딩에 쓸 writer 목록
          L119 viewResolvers()    RenderingResponse 의 뷰 해석기 목록
        --> Mono<Void>
```

```text
 order = 0 (L48)

 ResponseEntityResultHandler      0
 ServerResponseResultHandler      0     <-- 여기
 ResponseBodyResultHandler        100
 ViewResolutionResultHandler      가장 뒤

 같은 0 이어도 supports 조건이 겹치지 않는다
   ResponseEntity 를 돌려주는 것은 애노테이션 컨트롤러,
   ServerResponse 를 돌려주는 것은 핸들러 함수다
```

## 결과가 쓰이는 곳

```text
 Mono<Void>
      --> DispatcherHandler 가 그대로 흘려보내고, 서버 어댑터가 구독한다
      --> 구독 시점에 상태/헤더/본문 쓰기가 실제로 일어난다

 context 로 넘긴 messageWriters
      --> 응답 본문 객체를 어떤 형식으로 인코딩할지 정한다
      --> HandlerStrategies 가 기본 목록을 구성하고, 설정으로 바꿀 수 있다

 context 로 넘긴 viewResolvers
      --> RenderingResponse 일 때만 쓰인다 (템플릿 렌더링)
      --> EntityResponse 경로에서는 쓰이지 않는다
```

결과 처리기 계약 자체는 [WebFlux 요청 처리의 HandlerResultHandler](../../webflux-request-processing/spi/HandlerResultHandler/README.md)에 있다.
