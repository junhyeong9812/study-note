# SecurityWebFilterChain

상위: [spi](../README.md)

체인 하나를 나타낸다. 서블릿 판의 `SecurityFilterChain` 과 메서드 개수가 같고 역할도 대응한다.

## 위치

`web` / `org.springframework.security.web.server` / `SecurityWebFilterChain.java` L32-L48 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/server/SecurityWebFilterChain.java#L32-L48))

## 실제 코드

```java
// SecurityWebFilterChain.java L32-L48 (javadoc 생략)
public interface SecurityWebFilterChain {

    Mono<Boolean> matches(ServerWebExchange exchange);

    Flux<WebFilter> getWebFilters();

}
```

## 흐름에서 불리는 자리

```text
 WebFilterChainProxy.filterFirewalledExchange
   L72 filterWhen 안에서 matches(exchange)
   L76 고른 체인의 getWebFilters().collectList()
```

- [WebFilterChainProxy.filterFirewalledExchange](../../01_WebFilterChainProxy.filter/01_WebFilterChainProxy.filterFirewalledExchange/README.md)

## 구현 계층

```text
 SecurityWebFilterChain
   +-- MatcherSecurityWebFilterChain   프레임워크 구현. 매처 하나 + 필터 목록
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 두 메서드 모두 시그니처가 다르다
      --> boolean matches       -> Mono<Boolean> matches
      --> List<Filter> getFilters -> Flux<WebFilter> getWebFilters
      --> 이름까지 바뀐 것은 뒤쪽이다. 같은 것은 개수뿐이다

 getWebFilters 가 Flux 인 점
      --> 호출부가 collectList() 로 한 번에 모아 쓴다
      --> 유일한 구현은 이미 가진 List 를 그대로 흘린다

 메서드가 둘뿐인 점
      --> 서블릿 판과 같다. 체인이 아는 것은 조건과 목록뿐이다
      --> 순서나 우선순위는 이 계약에 없다
      --> 주입받는 빈 목록의 순서가 정한다 (@Order 가 있으면 그것)
```
