# DefaultRouterFunction.route

상위: [webmvc.RouterFunctionMapping.getHandlerInternal](../README.md)

라우트 하나가 하는 일 전부다. 조건 하나를 요청에 대고 물어서, 맞으면 짝지어 둔 핸들러 함수를 내놓고 아니면 빈 값을 내놓는다. 라우터 여러 개를 합친 모양도 이 최소 단위를 순서대로 부르는 것뿐이다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function` / `RouterFunctions.java` L1216-L1226 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/RouterFunctions.java#L1216-L1226))

```java
// RouterFunctions.java L1216-L1226
public Optional<HandlerFunction<T>> route(ServerRequest request) {
    if (this.predicate.test(request)) {
        if (logger.isTraceEnabled()) {
            logger.trace(String.format("Predicate \"%s\" matches against \"%s\"", this.predicate, request));
        }
        return Optional.of(this.handlerFunction);
    }
    else {
        return Optional.empty();
    }
}
```

여러 라우트를 합친 형태는 "앞이 비면 다음"이다.

`spring-webmvc` / `org.springframework.web.servlet.function` / `RouterFunctions.java` L1110-L1118 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/RouterFunctions.java#L1110-L1118))

```java
// RouterFunctions.java L1110-L1118
public Optional<HandlerFunction<T>> route(ServerRequest request) {
    Optional<HandlerFunction<T>> firstRoute = this.first.route(request);
    if (firstRoute.isPresent()) {
        return firstRoute;
    }
    else {
        return this.second.route(request);
    }
}
```

조건은 작은 조건을 `and`로 엮어 만든다.

`spring-webmvc` / `org.springframework.web.servlet.function` / `RequestPredicates.java` L214-L216 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/RequestPredicates.java#L214-L216))

```java
// RequestPredicates.java L214-L216
public static RequestPredicate GET(String pattern) {
    return method(HttpMethod.GET).and(path(pattern));
}
```

## 동작 흐름

```text
 route(request)
 |
 +-- L1217 predicate.test(request)
 |        true  --> L1221 Optional.of(handlerFunction)
 |        false --> L1224 Optional.empty()
 |
 +-- 판정에 성공한 조건은 요청 속성에 흔적을 남긴다
        경로 조건이 맞으면 MATCHING_PATTERN_ATTRIBUTE 에 PathPattern
        경로 변수가 있으면 URI_TEMPLATE_VARIABLES_ATTRIBUTE 에 이름->값

 SameComposedRouterFunction.route(request)      라우터를 and 로 합친 경우
 |
 +-- L1111 first.route(request)
 |        결과가 있으면 그대로 반환 (먼저 등록된 라우트가 이긴다)
 |
 +-- L1116 없으면 second.route(request)

 GET("/users/{id}")
   method(GET) and path("/users/{id}")
     AndRequestPredicate 로 묶인다
     앞이 false 면 뒤는 평가하지 않는다
```

```text
 조건 판정 순서가 만드는 결과

 route()
   .GET("/users/{id}", handlerA)      먼저 등록
   .GET("/users/me",   handlerB)      나중 등록
 |
 +-- "/users/me" 요청
        첫 라우트의 경로 패턴 {id} 가 먼저 맞아 handlerA 가 선택된다
        = 함수형 라우팅은 애노테이션처럼 "가장 구체적인 패턴"을 고르지 않는다
          등록 순서가 곧 우선순위다
```

## 결과가 쓰이는 곳

```text
 Optional<HandlerFunction>
      --> 비면 getHandlerInternal 이 null 을 반환해 다음 HandlerMapping 으로 넘어간다
      --> 값이 있으면 그 함수가 그대로 DispatcherServlet 의 handler 가 된다

 MATCHING_PATTERN_ATTRIBUTE
      --> setAttributes 가 BEST_MATCHING_PATTERN_ATTRIBUTE 로 옮겨 담는다
      --> 메트릭/관측의 URI 태그가 이 값을 쓴다 (요청마다 다른 경로가 태그를 폭발시키지 않게)

 URI_TEMPLATE_VARIABLES_ATTRIBUTE
      --> 핸들러 함수 안의 request.pathVariable("id") 가 읽는 값
```

조건 인터페이스 자체는 [RequestPredicate](../../spi/RequestPredicate/README.md)에, 라우터 합성 규칙은 [RouterFunction](../../spi/RouterFunction/README.md)에 있다.
