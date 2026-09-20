# ReactorContextWebFilter.filter

상위: [리액티브 컨텍스트](../README.md)

본문이 세 줄인 `filter` 와 네 줄짜리 private 헬퍼가 전부다. 체인에 `contextWrite` 를 한 번 거는 것이 하는 일의 전부다.

## 위치

`web` / `org.springframework.security.web.server.context` / `ReactorContextWebFilter.java` L45-L50 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/server/context/ReactorContextWebFilter.java#L45-L50))

## 실제 코드

```java
// ReactorContextWebFilter.java L36-L57
public class ReactorContextWebFilter implements WebFilter {

    private final ServerSecurityContextRepository repository;

    public ReactorContextWebFilter(ServerSecurityContextRepository repository) {
        Assert.notNull(repository, "repository cannot be null");
        this.repository = repository;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        return chain.filter(exchange)
            .contextWrite((context) -> context.hasKey(SecurityContext.class) ? context
                    : withSecurityContext(context, exchange));
    }

    private Context withSecurityContext(Context mainContext, ServerWebExchange exchange) {
        return mainContext
            .putAll(this.repository.load(exchange).as(ReactiveSecurityContextHolder::withSecurityContext).readOnly());
    }

}
```

## 동작 흐름

```text
 filter(exchange, chain)
 |
 | L47 chain.filter(exchange)
 |      먼저 체인을 조립한다. 아직 실행되지 않는다
 |
 +-- L48 contextWrite(context -> ...)
        L48 context.hasKey(SecurityContext.class) 이면
              그 context 를 그대로 돌려준다 (덮어쓰지 않는다)
        L49 없으면 withSecurityContext(context, exchange)

 withSecurityContext (L52-55)
 |
 +-- L54 repository.load(exchange)
        .as(ReactiveSecurityContextHolder::withSecurityContext)
        .readOnly()
        를 mainContext 에 putAll 한다
```

```text
 contextWrite 는 위로 전파된다

 L47 chain.filter(exchange) 가 만든 Mono 에 contextWrite 를 건다

 어느 범위까지 보이는지는 Reactor Context 의 전파 규칙에 달려 있고
 그 규칙은 이 저장소 코드로는 확인할 수 없다
 (레퍼런스 문서도 Reactor 쪽 문서를 링크만 한다)
```

```text
 load 를 바로 구독하지 않는다

 L54 repository.load(exchange) 는 Mono 다
 그것을 .as(withSecurityContext) 로 Context 에 담는다

 즉 컨텍스트에 들어가는 값이 SecurityContext 가 아니라
 Mono<SecurityContext> 다

 load 메서드 호출 자체는 L54 에서 즉시 일어난다
 미뤄지는 것은 그 Mono 의 구독이다
 구현이 cold Mono 를 돌려주는 한, 꺼내 구독하기 전에는
 세션을 실제로 읽지 않는다
 서블릿 판이 Supplier 를 담는 것과 비슷한 효과다
```

```text
 readOnly() 가 붙는 대상

 L54 끝의 readOnly() 는 Mono 가 아니라 Context 에 붙는다
 .as(withSecurityContext) 가 Context 를 돌려주기 때문이다 (L76-78)
 그 결과를 mainContext.putAll(...) 한다
 readOnly() 자체의 의미는 Reactor API 라 이 저장소에서는 확인할 수 없다
```

## 결과가 쓰이는 곳

```text
 심어진 Context
      --> 체인 안쪽의 모든 연산자가 본다
      --> ReactiveSecurityContextHolder.getContext 가 이것을 꺼낸다

 hasKey 검사
      --> 이미 키가 있으면 덮어쓰지 않는다 (L48 의 삼항)

 저장 경로가 없다는 점
      --> 이 필터는 읽기만 한다
      --> 서블릿 판과 같다. 저장은 인증한 쪽이 직접 한다
```

## 하위 메서드

- [01 ReactiveSecurityContextHolder.withSecurityContext](01_ReactiveSecurityContextHolder.withSecurityContext/README.md)
