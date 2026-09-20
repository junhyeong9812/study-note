# WebFilterChainProxy.filterFirewalledExchange

상위: [WebFilterChainProxy.filter](../README.md)

체인을 고르고 태운다. 서블릿 판 `doFilterInternal` 의 필터 선택·실행 부분과 `getFilters` 에 해당하는 일을 리액터 연산자 일곱 개로 이어 붙였다. (방화벽 감싸기는 `filter()` 쪽에 있다.)

## 위치

`web` / `org.springframework.security.web.server` / `WebFilterChainProxy.java` L70-L79 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/server/WebFilterChainProxy.java#L70-L79))

## 실제 코드

```java
// WebFilterChainProxy.java L70-L79
private Mono<Void> filterFirewalledExchange(ServerWebExchange firewalledExchange, WebFilterChain chain) {
    return Flux.fromIterable(this.filters)
        .filterWhen((securityWebFilterChain) -> securityWebFilterChain.matches(firewalledExchange))
        .next()
        .switchIfEmpty(Mono
            .defer(() -> this.filterChainDecorator.decorate(chain).filter(firewalledExchange).then(Mono.empty())))
        .flatMap((securityWebFilterChain) -> securityWebFilterChain.getWebFilters().collectList())
        .map((filters) -> this.filterChainDecorator.decorate(chain, filters))
        .flatMap((securedChain) -> securedChain.filter(firewalledExchange));
}
```

## 동작 흐름

```text
 filterFirewalledExchange(firewalledExchange, chain)
 |
 | L71 Flux.fromIterable(this.filters)
 |        등록된 SecurityWebFilterChain 들을 흘린다
 |
 | L72 filterWhen(chain -> chain.matches(firewalledExchange))
 |        matches 가 Mono<Boolean> 이라 filterWhen 을 쓴다
 |
 | L73 next()
 |        처음 통과한 하나만 집는다
 |
 +-- L74 switchIfEmpty(...)
 |        하나도 안 맞았을 때
 |        L75 filterChainDecorator.decorate(chain) 으로 감싸
 |            원래 체인을 그대로 태우고 then(Mono.empty())
 |
 | L76 flatMap -> 고른 체인의 getWebFilters().collectList()
 | L77 map -> filterChainDecorator.decorate(chain, filters)
 +-- L78 flatMap -> securedChain.filter(firewalledExchange)
```

```text
 filterWhen + next 가 for 문을 대신한다

 서블릿 판
   for (chain : filterChains)
       if (chain.matches(request)) return chain.getFilters();
   return null;

 리액티브
   Flux.fromIterable(filters).filterWhen(matches).next()

 next() 가 첫 항목을 집는다
 "첫 매칭이 이긴다"가 여기서도 유지된다
 (뒤의 체인에서 matches 가 불리는지는 리액터 연산자의 의미라
  이 저장소 코드만으로는 알 수 없다)
```

```text
 switchIfEmpty 안이 Mono.defer 로 감싸여 있다

 L74-75 switchIfEmpty(Mono.defer(() -> ...))

 defer 로 감싸 평가를 미룬다
 (defer 가 없을 때 무슨 일이 생기는지는 리액터 쪽 의미라
  이 저장소 코드만으로는 알 수 없다. 코드에 주석도 없다)
```

```text
 decorate 가 두 번 나온다

 L75 decorate(chain)            필터가 없을 때. 기본 구현은 원래 체인 그대로
 L77 decorate(chain, filters)   필터가 있을 때. 그것들을 엮은 체인을 만든다

 서블릿 판의 FilterChainDecorator 와 같은 두 갈래다
 관측 기능이 이 자리에 끼어드는 것도 같다
```

## 결과가 쓰이는 곳

```text
 고른 체인의 필터 목록
      --> 이 요청에 적용될 보안 규칙 전체다
      --> collectList 로 한 번에 모아 데코레이터에 넘긴다

 만들어진 securedChain
      --> 필터들을 차례로 엮은 WebFilterChain 이다
      --> 필터를 다 쓰면 원래 체인을 핸들러 자리에 두고 빠져나간다
          (L167 이 original::filter 를 핸들러로 넘긴다)

 비었을 때의 경로
      --> 매칭 체인이 하나도 없을 때만 탄다
      --> 서블릿 판의 "filters == null" 에 대응한다
      --> 매칭된 체인의 필터 목록이 비어 있으면 이쪽이 아니라
          L77 의 decorate(chain, 빈 목록) 으로 간다

 조립해서 돌려준다는 점
      --> 이 메서드는 리액터 파이프라인을 만들어 반환할 뿐이다
```
