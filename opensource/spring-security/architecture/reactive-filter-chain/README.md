# 리액티브 필터 체인

[필터 체인](../filter-chain/README.md)의 WebFlux 판이다. 하는 일은 같지만 서블릿 필터가 아니라 `WebFilter` 이고, 값이 아니라 `Mono` 로 흐른다. 두 흐름을 나란히 놓고 보면 같은 설계가 리액티브로 어떻게 번역되는지가 드러난다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 체인과 방화벽 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 WebFlux 의 WebFilter 체인
 |
 +-- [01] WebFilterChainProxy.filter
 |        방화벽으로 exchange 를 감싼다
 |        거부 예외는 onErrorResume 으로 핸들러에 넘긴다
 |
 +-- [01-01] WebFilterChainProxy.filterFirewalledExchange
          체인 목록을 Flux 로 흘려 matches 로 거른다
          next() 로 첫 매칭 하나만 집는다
          없으면 switchIfEmpty 로 보안 없이 통과
          있으면 그 필터들로 체인을 만들어 태운다
```

```text
 서블릿 판과 나란히 보기

 서블릿                              리액티브
 FilterChainProxy                    WebFilterChainProxy
 SecurityFilterChain                 SecurityWebFilterChain
 boolean matches(request)            Mono<Boolean> matches(exchange)
 List<Filter> getFilters()           Flux<WebFilter> getWebFilters()
 HttpFirewall                        ServerWebExchangeFirewall
 RequestRejectedHandler              ServerExchangeRejectedHandler
 FilterChainDecorator                WebFilterChainDecorator
 VirtualFilterChain (가변 커서 재귀)  DefaultWebFilterChain (불변 링크 재귀)

 이름이 거의 그대로 대응한다
 마지막 행만 성격이 다르다 --
 VirtualFilterChain 은 FilterChainProxy 안의 private 클래스지만
 DefaultWebFilterChain 은 Spring Framework 것을 그대로 쓴다
```

```text
 matches 가 Mono 를 돌려준다

 서블릿    boolean matches(request)          즉시 답한다
 리액티브  Mono<Boolean> matches(exchange)   나중에 답할 수 있다

 그래서 체인 선택에 비동기 작업을 끼울 수 있다
 그 대신 목록 순회가 for 문이 아니라 filterWhen + next() 가 된다

 결과는 같다 -- 처음 매칭되는 체인 하나를 쓴다
```

```text
 "매칭 없음"의 처리도 같다

 서블릿    getFilters 가 null 이거나 빈 목록 -> 둘 다 보안 없이 통과
 리액티브  매칭 체인이 없으면 -> switchIfEmpty 로 보안 없이 통과

 다만 정확히 같지는 않다
 리액티브의 switchIfEmpty 는 서블릿의 null 에만 대응한다
 매칭된 체인의 필터 목록이 비어 있으면
 그쪽은 decorate(chain, 빈 목록) 경로로 간다

 큰 그림은 같다 -- "안 맞으면 막는다"가 아니라 "흘려보낸다"다
 인가 흐름이 "안 맞으면 막는다"인 것과 반대인 점도 같다
```

## 어디에서 쓰이는가

```text
 [필터 체인] 서블릿 판과 같은 구조다. 두 흐름을 나란히 읽으면 좋다
 [리액티브 컨텍스트] 이 체인 위에서 SecurityContext 가 Reactor Context 로 흐른다
 [WebFlux 요청 처리] 이 체인을 통과해야 DispatcherHandler 에 닿는다
```

서블릿 판은 [필터 체인](../filter-chain/README.md), 이 체인 위에서 컨텍스트가 어떻게 흐르는지는 [리액티브 컨텍스트](../reactive-context/README.md)에 있다. 통과한 뒤의 경로는 Spring Framework 쪽 [WebFlux 요청 처리](../../../spring-framework/architecture/webflux-request-processing/README.md) 흐름이다.

## 단계

1. [WebFilterChainProxy.filter](01_WebFilterChainProxy.filter/README.md)가 방화벽을 씌운다.
2. [WebFilterChainProxy.filterFirewalledExchange](01_WebFilterChainProxy.filter/01_WebFilterChainProxy.filterFirewalledExchange/README.md)가 체인을 골라 태운다.

## 결과가 쓰이는 곳

```text
 돌려준 Mono<Void>
      --> 리액터 파이프라인을 조립해 돌려준다
      --> WebFlux 가 이것을 구독한다

 고른 필터 목록
      --> 이 요청에 적용될 보안 규칙 전체다
      --> 서블릿 판의 가변 커서 대신 미리 엮은 불변 링크를 따라 이어진다

 방화벽이 감싼 exchange
      --> 체인 안의 모든 필터가 이 감싼 것을 본다
      --> 기본은 StrictServerWebExchangeFirewall 이다

 거부 예외
      --> onErrorResume 으로 잡아 핸들러에 넘긴다
      --> 그 뒤 Mono.empty() 로 끝내 체인을 더 태우지 않는다
```

## 다루지 않는 것

`StrictServerWebExchangeFirewall`의 차단 규칙, `DefaultWebFilterChain`의 조립 세부, `MatcherSecurityWebFilterChain`과 `ServerWebExchangeMatcher` 구현들, `ServerHttpSecurity` DSL 이 체인을 만드는 과정, 관측 연동은 같은 뼈대의 곁가지라 요약만 했다. Reactor 의 연산자 의미와 WebFlux 자체도 범위 밖이다. 본문에서 연산자를 언급할 때도 이 저장소 코드로 확인되는 것만 단정하고, 나머지는 그렇게 표시했다.

## 하위 메서드

- [01 WebFilterChainProxy.filter](01_WebFilterChainProxy.filter/README.md)
- [spi](spi/README.md) — 리액티브 체인, 체인 데코레이터, 방화벽
