# HandlerResultHandler

상위: [Spring WebFlux 요청 처리](../../README.md) / [spi](../README.md)

핸들러가 돌려준 `HandlerResult`를 응답으로 바꾼다. MVC의 반환값 처리기와 뷰 렌더링을 합친 자리다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive` / `HandlerResultHandler.java` L30-L48 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/HandlerResultHandler.java#L30-L48))

```java
// HandlerResultHandler.java L30-L48
public interface HandlerResultHandler {

    boolean supports(HandlerResult result);

    Mono<Void> handleResult(ServerWebExchange exchange, HandlerResult result);

}
```

## 흐름에서 불리는 자리

```text
 DispatcherHandler.handleResult L185
   supports(result) 가 true 인 첫 처리기에게 위임
   없으면 IllegalStateException
```

- [HandlerResultHandler.handleResult](../../02_DispatcherHandler.handle/02_HandlerResultHandler.handleResult/README.md)

## 구현 계층

```text
 HandlerResultHandler
   +-- ResponseEntityResultHandler        ResponseEntity, HttpHeaders   (order 0)
   +-- ServerResponseResultHandler        함수형 ServerResponse
   +-- ResponseBodyResultHandler          @ResponseBody                 (order 100)
   +-- ViewResolutionResultHandler        뷰 이름, Model, Rendering     (가장 뒤)

 공통 상위
   AbstractMessageWriterResultHandler   본문 쓰기 (HttpMessageWriter 선택)
   HandlerResultHandlerSupport          미디어 타입 협상, 리액티브 어댑터
```
