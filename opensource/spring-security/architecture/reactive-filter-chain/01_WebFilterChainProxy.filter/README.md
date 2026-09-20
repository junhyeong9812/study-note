# WebFilterChainProxy.filter

상위: [리액티브 필터 체인](../README.md)

WebFlux 가 이 클래스를 부르는 지점이다. 방화벽을 씌우고, 거부 예외를 핸들러로 돌린다.

## 위치

`web` / `org.springframework.security.web.server` / `WebFilterChainProxy.java` L62-L68 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/server/WebFilterChainProxy.java#L62-L68))

## 실제 코드

```java
// WebFilterChainProxy.java L62-L68
@Override
public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
    return this.firewall.getFirewalledExchange(exchange)
        .flatMap((firewalledExchange) -> filterFirewalledExchange(firewalledExchange, chain))
        .onErrorResume(ServerExchangeRejectedException.class,
                (rejected) -> this.exchangeRejectedHandler.handle(exchange, rejected).then(Mono.empty()));
}
```

필드 기본값이 위에 모여 있다. 클래스 선언과 필드까지만 잘라 왔다.

`web` / `org.springframework.security.web.server` / `WebFilterChainProxy.java` L44-L56 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/server/WebFilterChainProxy.java#L44-L56))

```java
// WebFilterChainProxy.java L44-L52
public class WebFilterChainProxy implements WebFilter {

    private final List<SecurityWebFilterChain> filters;

    private WebFilterChainDecorator filterChainDecorator = new DefaultWebFilterChainDecorator();

    private ServerWebExchangeFirewall firewall = new StrictServerWebExchangeFirewall();

    private ServerExchangeRejectedHandler exchangeRejectedHandler = new HttpStatusExchangeRejectedHandler();
```

## 동작 흐름

```text
 filter(exchange, chain)
 |
 | L64 firewall.getFirewalledExchange(exchange)
 |        Mono 를 돌려준다. 검사도 이 안에서 일어난다
 |
 | L65 flatMap -> filterFirewalledExchange(감싼 exchange, chain)
 |
 +-- L66 onErrorResume(ServerExchangeRejectedException.class, ...)
        L67 exchangeRejectedHandler.handle(exchange, rejected)
             then(Mono.empty()) 로 끝낸다
```

```text
 서블릿 판의 try-catch 가 onErrorResume 이 된다

 서블릿    try { ... } catch (RequestRejectedException e) { handler.handle(...) }
 리액티브  ...onErrorResume(ServerExchangeRejectedException.class, handler)

 하는 일은 같다. 표현 수단만 다르다

 다만 서블릿 판은 원인 사슬을 펴서 찾아야 했다
 (다른 예외로 감싸여 올라오기 때문)
 리액티브 쪽은 타입으로 바로 건진다
```

```text
 핸들러에 넘기는 것은 감싸기 전 exchange 다

 L67 exchangeRejectedHandler.handle(exchange, rejected)
                             ^^^^^^^^
 L63 의 원본이다. 감싼 것이 아니다
 (그 이유는 소스에 적혀 있지 않다)
```

```text
 필드 기본값 셋

 L48 filterChainDecorator = DefaultWebFilterChainDecorator
 L50 firewall = StrictServerWebExchangeFirewall
 L52 exchangeRejectedHandler = HttpStatusExchangeRejectedHandler

 서블릿 판의 VirtualFilterChainDecorator / StrictHttpFirewall /
 HttpStatusRequestRejectedHandler 와 나란히 대응한다
```

## 결과가 쓰이는 곳

```text
 돌려준 Mono<Void>
      --> 리액터 파이프라인을 조립해 돌려준다
      --> 서블릿 판이 메서드 안에서 곧바로 체인을 태우는 것과 가장 다른 점이다

 then(Mono.empty())
      --> 거부를 처리한 뒤 아무 값도 흘리지 않는다
      --> 뒤의 체인이 이어지지 않는다

 firewall
      --> 메서드, URL, 호스트, 정규화 검사는 체인 선택 전에 끝난다
      --> 헤더와 파라미터 검사는 감싼 exchange 가 지연 실행한다
          그래서 필터가 도는 중에도 거부가 날 수 있다
      --> onErrorResume 이 flatMap 뒤에 놓인 것이 그 늦은 거부까지 잡는다
```

## 하위 메서드

- [01 WebFilterChainProxy.filterFirewalledExchange](01_WebFilterChainProxy.filterFirewalledExchange/README.md)
