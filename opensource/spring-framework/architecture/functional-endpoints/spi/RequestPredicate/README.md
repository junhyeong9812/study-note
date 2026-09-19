# RequestPredicate

상위: [Spring 함수형 엔드포인트](../../README.md) / [spi](../README.md)

"이 요청이 이 라우트에 해당하는가"를 판정한다. 메서드, 경로, 헤더, 파라미터 같은 작은 조건을 `and`/`or`/`negate`로 엮어 하나의 조건을 만든다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function` / `RequestPredicate.java` L33-L56 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/RequestPredicate.java#L33-L56))

```java
// RequestPredicate.java L33-L56
public interface RequestPredicate {

    boolean test(ServerRequest request);

    default RequestPredicate and(RequestPredicate other) {
        return new RequestPredicates.AndRequestPredicate(this, other);
    }

```

중첩 라우팅을 위해 조건이 요청을 바꿔 돌려주기도 한다.

`spring-webmvc` / `org.springframework.web.servlet.function` / `RequestPredicate.java` L83-L85 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/RequestPredicate.java#L83-L85))

```java
// RequestPredicate.java L83-L85
default Optional<ServerRequest> nest(ServerRequest request) {
    return (test(request) ? Optional.of(request) : Optional.empty());
}
```

## 흐름에서 불리는 자리

```text
 DefaultRouterFunction.route
   predicate.test(request)
     true 면 짝지어진 핸들러 함수를 내놓는다
 DefaultNestedRouterFunction.route
   predicate.nest(request)
     맞으면 "남은 경로"만 남긴 요청을 내놓아 안쪽 라우터에 넘긴다
```

- [DefaultRouterFunction.route](../../01_webmvc.RouterFunctionMapping.getHandlerInternal/01_DefaultRouterFunction.route/README.md)

## 구현 계층

```text
 RequestPredicate
   +-- SingleHttpMethodPredicate        method(GET)
   +-- MultipleHttpMethodsPredicate     methods(GET, HEAD)
   +-- RequestModifyingPredicate        판정하며 요청 속성을 바꾸는 계열
   |     +-- PathPatternPredicate       path("/users/{id}")  경로 변수를 푼다
   |     +-- AndRequestPredicate / OrRequestPredicate / NegateRequestPredicate  합성
   +-- HeadersPredicate                 headers(...)
   |     +-- SingleContentTypePredicate / MultipleContentTypesPredicate  contentType(...)
   |     +-- SingleAcceptPredicate / MultipleAcceptsPredicate            accept(...)
   +-- ApiVersionPredicate              version(...)
   +-- ParamPredicate                   param("q", ...)
   +-- PathExtensionPredicate           pathExtension(...)

 자주 쓰는 조합 헬퍼
   RequestPredicates.GET(pattern) = method(GET).and(path(pattern))
   POST, PUT, PATCH, DELETE, HEAD, OPTIONS 도 같은 모양
```

## 결과가 쓰이는 곳

```text
 test 의 true/false
      --> 라우트 선택. false 면 다음 라우트가 시도된다

 경로 조건이 맞을 때 남기는 것
      --> MATCHING_PATTERN_ATTRIBUTE 에 PathPattern
      --> URI_TEMPLATE_VARIABLES_ATTRIBUTE 에 경로 변수 맵
      --> 핸들러 함수의 request.pathVariable("id") 와 관측 태그가 이 값을 읽는다

 nest 가 돌려주는 요청
      --> 바깥 조건이 먹은 경로만큼 잘라낸 요청이다
      --> 그래서 nest("/users", route().GET("/{id}", ...)) 가 /users/42 에 맞는다

 and 의 단축 평가
      --> 앞 조건이 false 면 뒤 조건은 평가하지 않는다
      --> 경로 조건을 뒤에 두면 메서드가 다른 요청에서 경로 파싱 비용을 아낀다
```
