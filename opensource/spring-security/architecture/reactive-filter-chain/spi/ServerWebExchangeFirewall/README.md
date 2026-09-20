# ServerWebExchangeFirewall

상위: [spi](../README.md)

체인에 들어가기 전에 `exchange` 를 감싸거나 거부한다. 서블릿 판의 `HttpFirewall` 에 대응한다.

## 위치

`web` / `org.springframework.security.web.server.firewall` / `ServerWebExchangeFirewall.java` L30-L46 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/server/firewall/ServerWebExchangeFirewall.java#L30-L46))

## 실제 코드

```java
// ServerWebExchangeFirewall.java L30-L46 (javadoc 생략)
public interface ServerWebExchangeFirewall {

    ServerWebExchangeFirewall INSECURE_NOOP = (exchange) -> Mono.just(exchange);

    Mono<ServerWebExchange> getFirewalledExchange(ServerWebExchange exchange);

}
```

## 흐름에서 불리는 자리

```text
 WebFilterChainProxy.filter
   L64 firewall.getFirewalledExchange(exchange)
   거부하면 Mono 가 ServerExchangeRejectedException 으로 끝난다
```

- [WebFilterChainProxy.filter](../../01_WebFilterChainProxy.filter/README.md)

## 구현 계층

```text
 ServerWebExchangeFirewall
   +-- StrictServerWebExchangeFirewall   기본. 수상한 요청을 거부한다
   +-- INSECURE_NOOP                     인터페이스 상수. 그대로 통과시킨다
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 반환이 Mono 인 점
      --> 계약상 비동기 검사를 담을 수 있다
      --> 다만 유일한 구현은 Mono.fromCallable 로 동기다

 INSECURE_NOOP
      --> 인터페이스에 상수로 들어 있다
      --> 이름이 INSECURE 로 시작해 쓰지 말라는 뜻을 담고 있다

 거부 예외
      --> 메서드, URL, 호스트, 정규화 검사에서 걸리면
          필터가 하나도 실행되지 않은 채 끝난다
      --> 헤더와 파라미터 검사는 감싼 exchange 가 지연 실행하므로
          필터가 도는 중에도 거부가 날 수 있다
      --> 어느 쪽이든 filter 의 onErrorResume 이 잡아 핸들러로 넘긴다
      --> 서블릿 판의 StrictFirewalledRequest 도 같은 지연 검증을 한다
```
