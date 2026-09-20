# ReactiveSecurityContextHolder.withSecurityContext

상위: [ReactorContextWebFilter.filter](../README.md)

`Mono<SecurityContext>` 를 Reactor `Context` 하나로 바꾼다. 한 줄이다.

## 위치

`core` / `org.springframework.security.core.context` / `ReactiveSecurityContextHolder.java` L76-L78 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/core/context/ReactiveSecurityContextHolder.java#L76-L78))

## 실제 코드

```java
// ReactiveSecurityContextHolder.java L76-L78
public static Context withSecurityContext(Mono<? extends SecurityContext> securityContext) {
    return Context.of(SECURITY_CONTEXT_KEY, securityContext);
}
```

같은 클래스에 짝이 되는 것들이 있다.

`core` / `org.springframework.security.core.context` / `ReactiveSecurityContextHolder.java` L65-L67 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/core/context/ReactiveSecurityContextHolder.java#L65-L67))

```java
// ReactiveSecurityContextHolder.java L65-L67
public static Function<Context, Context> clearContext() {
    return (context) -> context.delete(SECURITY_CONTEXT_KEY);
}
```

`core` / `org.springframework.security.core.context` / `ReactiveSecurityContextHolder.java` L85-L87 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/core/context/ReactiveSecurityContextHolder.java#L85-L87))

```java
// ReactiveSecurityContextHolder.java L85-L87
public static Context withAuthentication(Authentication authentication) {
    return withSecurityContext(Mono.just(new SecurityContextImpl(authentication)));
}
```

## 동작 흐름

```text
 withSecurityContext(securityContext)
 |
 +-- L77 Context.of(SECURITY_CONTEXT_KEY, securityContext)
        키는 L34 에서 SecurityContext.class 로 고정돼 있다

 clearContext()  L65-67
 +-- L66 context.delete(키) 를 하는 함수를 돌려준다
        값이 아니라 Context -> Context 함수다

 withAuthentication(authentication)  L85-87
 +-- L86 SecurityContextImpl 로 감싸 withSecurityContext 에 넘긴다
```

```text
 키가 클래스 객체다

 L34 SECURITY_CONTEXT_KEY = SecurityContext.class

 키가 private static final 로 고정돼 있다
 바깥에서 바꿀 수단이 없다
```

```text
 담기는 값이 Mono 다

 Context.of(키, Mono<SecurityContext>)
                ^^^^^^^^^^^^^^^^^^^^

 SecurityContext 가 아니라 그것을 감싼 Mono 를 담는다
 꺼내는 쪽(getContext)도 그 Mono 를 flatMap 으로 이어 붙인다

 그래서 저장소 읽기가 실제로 필요한 시점까지 미뤄진다
```

```text
 clearContext 가 함수를 돌려주는 이유

 값을 바꾸는 메서드가 아니라
 Context 를 받아 Context 를 돌려주는 함수를 준다 (L65-67)
 delete 의 결과를 그대로 돌려주는 형태다

 Reactor Context 가 불변인지는 이 저장소 코드로 확인할 수 없다
 main 소스에 이 메서드의 호출처도 없다. 테스트에서만 쓰인다
```

## 결과가 쓰이는 곳

```text
 돌려준 Context
      --> 호출부가 putAll 이나 contextWrite 로 합친다
      --> ReactorContextWebFilter L54 가 putAll 을 한다

 withAuthentication
      --> 테스트나 수동 설정에서 자주 쓰는 지름길이다
      --> Authentication 하나로 컨텍스트까지 만들어 준다

 정적 팩토리로만 만든다는 점
      --> Context.of(...) 와 context.delete(...) 의 결과를 그대로 쓴다
      --> 이 클래스는 Context 를 직접 고치지 않는다
```
