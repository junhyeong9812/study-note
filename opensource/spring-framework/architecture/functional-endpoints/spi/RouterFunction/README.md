# RouterFunction

상위: [Spring 함수형 엔드포인트](../../README.md) / [spi](../README.md)

요청 하나를 받아 그것을 처리할 핸들러 함수를 내놓는다. 못 찾으면 빈 값을 내놓는다. 이 하나의 메서드 위에 합성과 중첩과 필터가 전부 기본 메서드로 얹혀 있다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function` / `RouterFunction.java` L35-L64 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/RouterFunction.java#L35-L64))

```java
// RouterFunction.java L35-L64
public interface RouterFunction<T extends ServerResponse> {

    Optional<HandlerFunction<T>> route(ServerRequest request);

    // Default methods for composition and filtering

    default RouterFunction<T> and(RouterFunction<T> other) {
        return new RouterFunctions.SameComposedRouterFunction<>(this, other);
    }

```

리액티브 쪽은 반환 타입만 다르다.

`spring-webflux` / `org.springframework.web.reactive.function.server` / `RouterFunction.java` L36-L46 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/server/RouterFunction.java#L36-L46))

```java
// RouterFunction.java L36-L46
public interface RouterFunction<T extends ServerResponse> {

    Mono<HandlerFunction<T>> route(ServerRequest request);

```

## 흐름에서 불리는 자리

```text
 RouterFunctionMapping.getHandlerInternal
   routerFunction.route(ServerRequest)
     비면 이 매핑은 이 요청을 처리하지 않는다
 기동 시
   여러 RouterFunction 빈을 andOther 로 하나로 접는다
```

- [webmvc.RouterFunctionMapping.getHandlerInternal](../../01_webmvc.RouterFunctionMapping.getHandlerInternal/README.md)
- [DefaultRouterFunction.route](../../01_webmvc.RouterFunctionMapping.getHandlerInternal/01_DefaultRouterFunction.route/README.md)

## 구현 계층

```text
 RouterFunction<T>
   +-- AbstractRouterFunction<T>                   toString 을 Visitor 로 만든다
   |     +-- DefaultRouterFunction                 조건 1개 + 핸들러 1개 (최소 단위)
   |     +-- DefaultNestedRouterFunction           nest(조건, 라우터)
   |     +-- SameComposedRouterFunction            and (같은 응답 타입)
   |     +-- DifferentComposedRouterFunction       andOther (다른 응답 타입)
   |     +-- AttributesRouterFunction              withAttribute(s)
   |     +-- ResourcesRouterFunction               resources(...)
   |     +-- BuiltRouterFunction (RouterFunctionBuilder)  route() 빌더의 결과
   +-- FilteredRouterFunction                      filter 로 감싼 라우터 (직접 구현)
   +-- (람다로 직접 구현)

 만드는 방법
   RouterFunctions.route()                 빌더 (RouterFunctionBuilder)
   RouterFunctions.route(조건, 핸들러)      최소 단위 하나
   RouterFunctions.nest(조건, 라우터)       공통 조건으로 묶기
```

```text
 기본 메서드가 만드는 합성 규칙

 and(other)        앞이 비면 뒤를 시도. 같은 응답 타입
 andOther(other)   앞이 비면 뒤를 시도. 응답 타입이 달라도 된다
 andRoute(조건, 핸들러)   and(route(조건, 핸들러)) 와 같다
 andNest(조건, 라우터)    and(nest(조건, 라우터)) 와 같다
 filter(필터)      모든 매칭 결과를 필터로 감싼다
 withAttribute(s)  라우트에 메타데이터를 붙인다 (Visitor 가 읽는다)
 accept(visitor)   라우트 구조를 훑는다 (로깅, 경로 파서 교체, 버전 수집에 쓰인다)
```

## 결과가 쓰이는 곳

```text
 route 가 돌려준 값
      --> 그대로 DispatcherServlet 의 handler 가 된다
      --> 비면 다음 HandlerMapping 차례

 합성 순서
      --> 먼저 등록한 라우트가 이긴다. 애노테이션 매핑의 "가장 구체적인 패턴" 규칙이 없다
      --> 빌더가 만든 라우터도 목록을 등록 순서대로 순회한다 (RouterFunctionBuilder L434)
      --> 그래서 조건이 겹치는 /users/{id} 를 /users/me 보다 먼저 등록하면
          후자는 닿지 않는다 (메서드나 헤더 조건이 다르면 물론 닿는다)

 accept(Visitor)
      --> RouterFunctionMapping.afterPropertiesSet 이 PathPatternParser 를 갈아 끼울 때
      --> API 버전 전략이 지원 버전을 수집할 때
```
