# 리액티브 컨텍스트

[보안 컨텍스트](../security-context/README.md)의 WebFlux 판이다. 다만 앞 흐름과 달리 **구조가 정말 다르다.** `ThreadLocal` 을 쓸 수 없어 Reactor `Context` 로 갈아탔고, 그 결과 읽는 방법도 심는 방법도 모양이 바뀌었다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 리액티브 저장소 계약이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 리액티브 필터 체인의 한 칸
 |
 +-- [01] ReactorContextWebFilter.filter
 |        chain.filter(exchange) 에 contextWrite 를 건다
 |        이미 키가 있으면 그대로 두고, 없으면 심는다
 |
 |        |
 |        +-- [01-01] ReactiveSecurityContextHolder.withSecurityContext
 |                 Mono<SecurityContext> 를 Reactor Context 에 담는다
 |                 키는 SecurityContext.class 자체다
 |
 +-- [02] ReactiveSecurityContextHolder.getContext
          Reactor Context 에서 그 키를 꺼낸다
          없으면 빈 Mono 다
```

```text
 ThreadLocal 판과 정말 다른 점

 서블릿    ThreadLocal<Supplier<SecurityContext>>
           같은 스레드에서만 보인다. 스레드가 바뀌면 잃는다

 리액티브  Reactor Context (구독 체인에 딸린 불변 맵)
           스레드가 바뀌어도 같은 체인이면 따라간다

 그래서 리액티브 쪽에는 "비우기"가 finally 에 없다
 이 필터 전체에 clear 나 delete 호출이 하나도 없다
 (그 이후가 어떻게 정리되는지는 Reactor 쪽 문제다)
```

```text
 쓰는 방향이 반대다

 서블릿    setContext(context)   ThreadLocal 에 값을 넣는다
 리액티브  contextWrite(...)     체인에 Context 를 얹는다

 ReactorContextWebFilter 는 chain.filter(exchange) 가 만든 Mono 에
 contextWrite 를 건다

 어느 범위까지 보이는지는 Reactor 의 전파 규칙이 정하고,
 그 규칙은 이 저장소 코드로 확인할 수 없다
```

```text
 빈 컨텍스트를 만들어 주지 않는다

 서블릿    getContext() 는 비어 있으면 빈 컨텍스트를 만들어 넣는다. null 이 없다
 리액티브  getContext() 는 비어 있으면 빈 Mono 다. 아무 값도 흐르지 않는다

 그래서 소비하는 쪽이 "없을 때"를 따로 다뤄야 한다

 주의: AuthorizationWebFilter 의 switchIfEmpty 는 그 예가 아니다
 그쪽은 인가 판정이 빈 Mono 로 성공했을 때 체인을 잇는 것이다
```

## 어디에서 쓰이는가

```text
 [리액티브 필터 체인] 이 필터가 그 체인의 한 칸이다
 [보안 컨텍스트] 서블릿 판과 대비해 읽으면 차이가 분명하다
 [인가] AuthorizationWebFilter 가 여기서 Authentication 을 꺼낸다
```

서블릿 판은 [보안 컨텍스트](../security-context/README.md), 이 필터가 놓인 체인은 [리액티브 필터 체인](../reactive-filter-chain/README.md)에 있다.

## 단계

1. [ReactorContextWebFilter.filter](01_ReactorContextWebFilter.filter/README.md)가 컨텍스트를 심는다.
2. [ReactiveSecurityContextHolder.getContext](02_ReactiveSecurityContextHolder.getContext/README.md)가 꺼낸다.

## 결과가 쓰이는 곳

```text
 Reactor Context 에 담긴 Mono<SecurityContext>
      --> 값이 아니라 Mono 를 담는다
      --> 구현이 cold Mono 를 돌려주는 한, 구독 전에는 세션을 읽지 않는다
      --> 서블릿 판의 지연 Supplier 와 비슷한 효과다

 키가 SecurityContext.class 인 점
      --> 문자열이 아니라 클래스 객체를 키로 쓴다
      --> private static final 이라 바깥에서 바꿀 수 없다

 hasKey 검사
      --> 이미 키가 있으면 덮어쓰지 않는다 (L48 의 삼항)

 getContext 가 빈 Mono 를 돌려줄 수 있다는 점
      --> 호출부가 switchIfEmpty 를 준비해야 한다
      --> 서블릿 판에서는 없던 부담이다
```

## 다루지 않는 것

`WebSessionServerSecurityContextRepository`의 세션 처리, `ServerHttpSecurity` 가 이 필터를 체인에 넣는 과정, `SecurityContextServerWebExchangeWebFilter`, `@WithMockUser` 같은 테스트 지원, Reactor 의 `Context` 자체 의미와 컨텍스트 전파(`ContextPropagation`)는 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 ReactorContextWebFilter.filter](01_ReactorContextWebFilter.filter/README.md)
- [02 ReactiveSecurityContextHolder.getContext](02_ReactiveSecurityContextHolder.getContext/README.md)
- [spi](spi/README.md) — 리액티브 보안 컨텍스트 저장소
