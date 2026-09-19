# WebHandler

상위: [Spring WebFlux 요청 처리](../../README.md) / [spi](../README.md)

리액티브 스택에서 요청 하나를 처리하는 가장 단순한 계약이다. `exchange`를 받아 완료 신호(`Mono<Void>`)를 돌려준다. 필터, 예외 처리, 디스패처가 모두 이 타입으로 이어 붙는다.

## 실제 코드

`spring-web` / `org.springframework.web.server` / `WebHandler.java` L35-L44 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/server/WebHandler.java#L35-L44))

```java
// WebHandler.java L35-L44
public interface WebHandler {

    Mono<Void> handle(ServerWebExchange exchange);

}
```

`spring-web` / `org.springframework.web.server` / `WebFilter.java` L32-L43 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/server/WebFilter.java#L32-L43))

```java
// WebFilter.java L32-L43
public interface WebFilter {

    Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain);

}
```

`spring-web` / `org.springframework.web.server` / `WebExceptionHandler.java` L27-L39 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/server/WebExceptionHandler.java#L27-L39))

```java
// WebExceptionHandler.java L27-L39
public interface WebExceptionHandler {

    Mono<Void> handle(ServerWebExchange exchange, Throwable ex);

}
```

## 흐름에서 불리는 자리

```text
 WebHttpHandlerBuilder 가 조립
   HttpWebHandlerAdapter
     -> ExceptionHandlingWebHandler   WebExceptionHandler 목록
          -> FilteringWebHandler      WebFilter 체인
               -> DispatcherHandler
```

- [HttpWebHandlerAdapter.handle](../../01_HttpWebHandlerAdapter.handle/README.md)
- [DispatcherHandler.handle](../../02_DispatcherHandler.handle/README.md)

## 구현 계층

```text
 WebHandler
   +-- DispatcherHandler              애노테이션/함수형 라우팅
   +-- FilteringWebHandler            필터 체인 래퍼
   +-- ExceptionHandlingWebHandler    예외 처리 래퍼
   +-- HttpWebHandlerAdapter          가장 바깥 (HttpHandler 로 노출)

 WebFilter            MVC 의 서블릿 Filter 에 대응 (chain.filter(exchange) 로 이어간다)
 WebExceptionHandler  체인 어디서든 난 오류의 최종 처리
   +-- ResponseStatusExceptionHandler   ResponseStatusException -> 상태 코드 (spring-web)
         +-- WebFluxResponseStatusExceptionHandler   (spring-webflux)
```
