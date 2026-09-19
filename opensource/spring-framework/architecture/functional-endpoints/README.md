# Spring 함수형 엔드포인트

`@Controller` 대신 람다로 요청을 받는 경로다. 라우터 함수가 요청을 보고 핸들러 함수를 고르고, 핸들러 함수가 만든 `ServerResponse`가 스스로 응답을 쓴다. 서블릿 스택과 리액티브 스택이 같은 이름의 타입을 각자 패키지에 하나씩 두고 있어서, 이 지도는 두 갈래를 나란히 따라간다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 함수형 계약 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

같은 이름의 클래스가 두 스택에 있으므로 폴더 이름 앞에 모듈을 붙였다(`webmvc.` / `webflux.`).

## 전체 그림

```text
 [A] 서블릿 스택 (spring-webmvc, WebMvc.fn)

 DispatcherServlet.doDispatch
 |
 +-- [01] webmvc.RouterFunctionMapping.getHandlerInternal
 |        ServerRequest.create(servletRequest, messageConverters, versionStrategy)
 |        routerFunction.route(request) --> Optional<HandlerFunction>
 |        비면 다음 HandlerMapping 으로 넘어간다
 |        매칭 여부와 무관하게 ServerRequest 를 요청 속성에 담아 둔다
 |
 +-- [02] webmvc.HandlerFunctionAdapter.handle
          속성에서 ServerRequest 를 꺼낸다 (매핑 때 만든 것 그대로)
          handlerFunction.handle(serverRequest) --> ServerResponse
          serverResponse.writeTo(request, response, context)
            --> 상태/헤더를 쓰고 본문은 HttpMessageConverter 로

 [B] 리액티브 스택 (spring-webflux, WebFlux.fn)

 DispatcherHandler.handle
 |
 +-- [03] webflux.RouterFunctionMapping.getHandlerInternal
 |        routerFunction.route(request) --> Mono<HandlerFunction>
 |        비어 있으면 다음 매핑으로
 |
 +-- [04] webflux.HandlerFunctionAdapter.handle
 |        handlerFunction.handle(request) --> Mono<ServerResponse>
 |        HandlerResult 로 감싼다
 |
 +-- [05] webflux.ServerResponseResultHandler.handleResult
          response.writeTo(exchange, context)  --> Mono<Void>
```

```text
 두 스택의 대응

 서블릿                                     리액티브
 RouterFunction<T>.route -> Optional        RouterFunction<T>.route -> Mono
 HandlerFunction.handle  -> ServerResponse  HandlerFunction.handle  -> Mono<ServerResponse>
 ServerResponse.writeTo  -> ModelAndView    ServerResponse.writeTo  -> Mono<Void>
 응답 쓰기를 어댑터가 직접 호출             응답 쓰기를 별도 ResultHandler 가 담당
```

## 어디에서 쓰이는가

```text
 [MVC 요청 처리] getHandler 가 HandlerMapping 목록을 순서대로 묻는다
   RouterFunctionMapping 도 그 목록의 하나다
 [MVC 요청 처리] getHandlerAdapter 가 supports 로 어댑터를 고른다
   HandlerFunctionAdapter 는 handler instanceof HandlerFunction 만 본다
 [컨테이너 기동] RouterFunction 빈을 모아 하나로 합친다 (afterPropertiesSet)
```

애노테이션 컨트롤러 경로는 [MVC 요청 처리](../webmvc-request-processing/README.md)와 [WebFlux 요청 처리](../webflux-request-processing/README.md)에 있다. 이 흐름은 같은 뼈대의 다른 좌석을 채운다.

## 단계

1. [webmvc.RouterFunctionMapping.getHandlerInternal](01_webmvc.RouterFunctionMapping.getHandlerInternal/README.md)이 라우터 함수에 요청을 물어 핸들러 함수를 얻는다.
2. [webmvc.HandlerFunctionAdapter.handle](02_webmvc.HandlerFunctionAdapter.handle/README.md)이 핸들러 함수를 부르고 응답을 쓴다.
3. [webflux.RouterFunctionMapping.getHandlerInternal](03_webflux.RouterFunctionMapping.getHandlerInternal/README.md)이 같은 일을 `Mono`로 한다.
4. [webflux.HandlerFunctionAdapter.handle](04_webflux.HandlerFunctionAdapter.handle/README.md)이 `HandlerResult`로 감싼다.
5. [webflux.ServerResponseResultHandler.handleResult](05_webflux.ServerResponseResultHandler.handleResult/README.md)가 응답 쓰기를 맡는다.

## 결과가 쓰이는 곳

```text
 route 의 반환값
      --> 비어 있으면 이 매핑은 이 요청을 모른다는 뜻이고 다음 매핑이 시도된다
      --> 모든 매핑이 비면 noHandlerFound --> NoHandlerFoundException

 매핑 단계에서 만든 ServerRequest
      --> 요청 속성 RouterFunctions.REQUEST_ATTRIBUTE 에 담긴다
      --> 어댑터가 그 인스턴스를 그대로 꺼내 쓴다
          (다시 만들려면 매핑이 들고 있는 컨버터 목록과 API 버전 전략이 필요한데
           어댑터에는 그 둘이 없다)

 ServerResponse
      --> 값이 아니라 "응답을 쓰는 방법"이다. 상태/헤더/본문을 스스로 쓴다
      --> 서블릿 쪽은 ModelAndView 를 돌려줄 수 있어 뷰 렌더링으로도 이어진다
      --> 리액티브 쪽은 Mono<Void> 라 구독 시점에 쓰기가 일어난다
```

## 다루지 않는 것

`RouterFunctions.route()` 빌더가 조립하는 중첩 라우터(`nest`)와 `RequestPredicates`의 조건 조합 내부, 정적 리소스 라우팅(`resources`), 비동기 응답(`AsyncServerResponse`), SSE(`SseServerResponse`)는 같은 뼈대 위의 갈래라 요약만 했다. 응답 본문을 쓰는 `HttpMessageConverter` 자체는 [MVC 요청 처리](../webmvc-request-processing/README.md)의 컨버터 절에 있다.

## 하위 메서드

- [01 webmvc.RouterFunctionMapping.getHandlerInternal](01_webmvc.RouterFunctionMapping.getHandlerInternal/README.md)
- [02 webmvc.HandlerFunctionAdapter.handle](02_webmvc.HandlerFunctionAdapter.handle/README.md)
- [03 webflux.RouterFunctionMapping.getHandlerInternal](03_webflux.RouterFunctionMapping.getHandlerInternal/README.md)
- [04 webflux.HandlerFunctionAdapter.handle](04_webflux.HandlerFunctionAdapter.handle/README.md)
- [05 webflux.ServerResponseResultHandler.handleResult](05_webflux.ServerResponseResultHandler.handleResult/README.md)
- [spi](spi/README.md) — 라우터, 핸들러, 조건, 요청, 응답, 필터
