# Spring WebFlux 요청 처리

HTTP 요청 하나가 리액티브 스택에서 처리되어 응답이 되기까지의 흐름을 위에서 아래로 따라간다. [MVC 요청 처리](../webmvc-request-processing/README.md)와 단계 구성은 같지만, 모든 단계가 값 대신 `Mono`를 주고받으며 조립되고 실제 실행은 구독 시점에 일어난다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 흐름 중간의 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 서버 (Netty, Tomcat, Undertow, Jetty)
 |
 +-- [01] HttpWebHandlerAdapter.handle(request, response)
        ServerWebExchange 생성, 관측 컨텍스트 등록
        WebFilter 체인 --> (예외 시) WebExceptionHandler 체인
        |
        +-- [02] DispatcherHandler.handle(exchange)
               |
               +-- [02-01] HandlerMapping.getHandler          (spi)
               |      매핑 목록을 concatMap 으로 순회, 첫 결과 채택
               |      아무도 없으면 --> ResponseStatusException(404)
               |
               +-- [02-02] HandlerAdapter.handle              (spi)
               |      RequestMappingHandlerAdapter
               |        모델 초기화 --> InvocableHandlerMethod.invoke
               |          인자 해석(각 인자가 Mono) --> 컨트롤러 호출 --> HandlerResult
               |        예외는 @ExceptionHandler 로 복구 (onErrorResume)
               |
               +-- [02-03] HandlerResultHandler.handleResult  (spi)
                      반환 타입에 맞는 처리기 선택
                      @ResponseBody --> 인코더로 본문 쓰기
                      뷰 이름       --> ViewResolver 로 렌더링
        |
        +-- 응답 완료 (setComplete)
```

MVC와 대응시키면 다음과 같다.

```text
 MVC (서블릿)                              WebFlux (리액티브)
 DispatcherServlet.doDispatch              DispatcherHandler.handle
 HandlerMapping.getHandler                 HandlerMapping.getHandler       (Mono 반환)
 HandlerAdapter.handle -> ModelAndView     HandlerAdapter.handle -> Mono<HandlerResult>
 HandlerInterceptor                        WebFilter (앞단), HandlerResult 처리기
 HandlerExceptionResolver                  DispatchExceptionHandler, WebExceptionHandler
 ViewResolver / View                       ViewResolver / View (Mono<Void> 반환)
 반환값 처리기 + HttpMessageConverter      HandlerResultHandler + HttpMessageWriter(Encoder)
```

## 단계

1. [HttpWebHandlerAdapter.handle](01_HttpWebHandlerAdapter.handle/README.md)이 서버 요청을 `ServerWebExchange`로 감싸고 필터 체인을 조립한다.
2. [DispatcherHandler.handle](02_DispatcherHandler.handle/README.md)이 매핑, 어댑터, 결과 처리기를 차례로 엮어 하나의 `Mono<Void>`를 만든다.

## 결과가 쓰이는 곳

```text
 반환된 Mono<Void>
      --> 서버 어댑터가 구독한다. 구독해야 비로소 위 단계들이 실행된다
      --> 완료 신호가 곧 응답 완료

 스레드
      --> 요청을 받은 이벤트 루프 스레드에서 이어진다 (블로킹하면 전체 처리량이 떨어진다)
      --> @RequestMapping 메서드가 블로킹 작업을 하면 Scheduler 로 옮겨야 한다

 컨텍스트
      --> ThreadLocal 대신 Reactor Context 로 전달된다
      --> 그래서 MVC 의 RequestContextHolder 대응물이 exchange 자신이다
```

## 다루지 않는 것

함수형 엔드포인트(`RouterFunction`, `HandlerFunction`)와 WebSocket 경로는 같은 `DispatcherHandler` 골격을 쓰지만 이 지도에서는 애노테이션 컨트롤러 경로만 따라간다.

## 하위 메서드

- [01 HttpWebHandlerAdapter.handle](01_HttpWebHandlerAdapter.handle/README.md)
- [02 DispatcherHandler.handle](02_DispatcherHandler.handle/README.md)
- [spi](spi/README.md) — WebHandler, 매핑, 어댑터, 결과 처리기
