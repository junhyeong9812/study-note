# ServerSecurityContextRepository

상위: [spi](../README.md)

리액티브 쪽에서 컨텍스트를 요청 너머로 보관하는 계약이다.

## 위치

`web` / `org.springframework.security.web.server.context` / `ServerSecurityContextRepository.java` L32-L49 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/server/context/ServerSecurityContextRepository.java#L32-L49))

## 실제 코드

```java
// ServerSecurityContextRepository.java L32-L49 (javadoc 생략)
public interface ServerSecurityContextRepository {

    Mono<Void> save(ServerWebExchange exchange, @Nullable SecurityContext context);

    Mono<SecurityContext> load(ServerWebExchange exchange);

}
```

## 흐름에서 불리는 자리

```text
 ReactorContextWebFilter.withSecurityContext
   L54 repository.load(exchange)
   그 Mono 를 Reactor Context 에 담는다
```

- [ReactorContextWebFilter.filter](../../01_ReactorContextWebFilter.filter/README.md)

## 구현 계층

```text
 ServerSecurityContextRepository
   +-- WebSessionServerSecurityContextRepository   WebSession 에 담는다
   +-- NoOpServerSecurityContextRepository         아무것도 하지 않는다
   +-- NonRotatingWebSessionServerSecurityContextRepository
   |     oauth2-client 안의 비공개 중첩 구현
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 load
      --> Mono 를 돌려준다. 구독해야 실제로 읽는다
      --> 필터가 그것을 그대로 Context 에 담으므로
          아무도 꺼내지 않으면 세션을 건드리지 않는다

 save 에 null 을 넘기는 것
      --> 인터페이스 javadoc 은 null 을 설명하지 않는다. @Nullable 만 붙어 있다
      --> 삭제 의미는 구현이 정한다
          WebSessionServerSecurityContextRepository 가 null 이면 세션 속성을 지운다
      --> 로그아웃 핸들러가 그것을 쓴다

 서블릿 판과의 차이
      --> 서블릿 쪽은 loadDeferredContext 로 지연을 따로 표현해야 했다
      --> 여기서는 반환형이 Mono 라 지연이 기본이다
      --> 그래서 DeferredSecurityContext 같은 타입이 필요 없다

 NoOpServerSecurityContextRepository
      --> 상태 없는 API 서버에서 세션을 아예 안 쓰게 만든다
      --> 서블릿 판의 NullSecurityContextRepository 에 대응한다
```
