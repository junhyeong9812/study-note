# ReactiveSecurityContextHolder.getContext

상위: [리액티브 컨텍스트](../README.md)

Reactor `Context` 에서 보안 컨텍스트를 꺼낸다. 서블릿 판의 `SecurityContextHolder.getContext()` 에 해당하지만 **빈 Mono 를 돌려줄 수 있다.**

## 위치

`core` / `org.springframework.security.core.context` / `ReactiveSecurityContextHolder.java` L43-L50 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/core/context/ReactiveSecurityContextHolder.java#L43-L50))

## 실제 코드

```java
// ReactiveSecurityContextHolder.java L43-L58
public static Mono<SecurityContext> getContext() {
    // @formatter:off
    return Mono.deferContextual(Mono::just)
            .cast(Context.class)
            .filter(ReactiveSecurityContextHolder::hasSecurityContext)
            .flatMap(ReactiveSecurityContextHolder::getSecurityContext);
    // @formatter:on
}

private static boolean hasSecurityContext(Context context) {
    return context.hasKey(SECURITY_CONTEXT_KEY);
}

private static Mono<SecurityContext> getSecurityContext(Context context) {
    return context.<Mono<SecurityContext>>get(SECURITY_CONTEXT_KEY);
}
```

## 동작 흐름

```text
 getContext()
 |
 | L45 Mono.deferContextual(Mono::just)
 |      구독 시점의 ContextView 를 값으로 흘린다
 | L46 cast(Context.class)
 |
 +-- L47 filter(hasSecurityContext)
 |      L53 context.hasKey(SecurityContext.class)
 |      없으면 여기서 끊긴다 -- 빈 Mono 가 된다
 |
 +-- L48 flatMap(getSecurityContext)
        L57 context.get(키) 가 Mono<SecurityContext> 다
        flatMap 이 그것을 이어 붙여 실제 값을 흘린다
```

```text
 두 단계로 꺼낸다

 1. Context 에서 Mono 를 꺼낸다   (get)
 2. 그 Mono 를 이어 붙인다        (flatMap)

 담긴 것이 값이 아니라 Mono 라서 단계가 하나 더 있다
 이 두 번째 단계에서야 저장소 읽기가 실제로 일어난다
```

```text
 빈 Mono 와 null 의 차이

 서블릿    getContext() 가 null 을 안 돌려준다. 빈 컨텍스트를 만들어 준다
 리액티브  키가 없으면 아무 값도 흐르지 않는다

 소비하는 쪽이 이 차이를 다뤄야 한다

 서블릿 쪽은 SecurityContext 자체가 null 이 될 수 없고,
 AuthorizationFilter 는 Authentication 이 null 인 채로
 매니저가 그것을 요구할 때 AuthenticationCredentialsNotFoundException 을 던진다
 (AuthorizationFilter L139-146)
```

```text
 deferContextual 이 필요한 이유

 Reactor Context 는 구독 시점에 정해진다
 조립 시점에는 아직 무엇이 담길지 모른다

 그래서 Mono.deferContextual 로 구독 시점까지 미뤄
 그때의 ContextView 를 받아 온다
```

## 결과가 쓰이는 곳

```text
 돌려준 Mono<SecurityContext>
      --> 구독해야 값이 흐른다
      --> 그 구독이 저장소 읽기를 발동시킨다

 AuthorizationWebFilter 의 사용 (L53-60)
      --> L53 getContext() 로 꺼내
      --> L54 filter 로 authentication 이 있는 것만 남기고
      --> L55 mapNotNull 로 Authentication 을 꺼내고
      --> L56 as 로 그 Mono 를 통째로 verify 에 넘기고
      --> L57 doOnSuccess, L58-59 doOnError 로 로그를 남기고
      --> L60 switchIfEmpty 로 다음 체인을 잇는다

      verify 는 인가에 성공하면 빈 Mono 로 완료한다
      그래서 L60 의 switchIfEmpty 는 "없을 때"가 아니라
      "통과했을 때" 나머지 체인을 태우는 정상 경로다
      거부는 빈 Mono 가 아니라 AccessDeniedException 으로 표현된다

 static 메서드라는 점
      --> 서블릿 판의 SecurityContextHolder 와 같은 사용감이다
      --> 다만 ThreadLocal 이 아니라 구독 체인에서 가져온다
```
