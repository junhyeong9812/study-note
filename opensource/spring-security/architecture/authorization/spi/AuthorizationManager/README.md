# AuthorizationManager

상위: [spi](../README.md)

인가의 중심 계약이다. 대상 타입이 제네릭이라 웹 요청과 메서드 호출 모두에 쓰인다.

## 위치

`core` / `org.springframework.security.authorization` / `AuthorizationManager.java` L33-L59 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/AuthorizationManager.java#L33-L59))

## 실제 코드

```java
// AuthorizationManager.java L33-L59 (javadoc 생략)
@FunctionalInterface
public interface AuthorizationManager<T extends @Nullable Object> {

    default void verify(Supplier<? extends @Nullable Authentication> authentication, T object) {
        AuthorizationResult result = authorize(authentication, object);
        if (result != null && !result.isGranted()) {
            throw new AuthorizationDeniedException("Access Denied", result);
        }
    }

    @Nullable AuthorizationResult authorize(Supplier<? extends @Nullable Authentication> authentication, T object);

}
```

## 흐름에서 불리는 자리

```text
 AuthorizationFilter.doFilter
   L96 authorizationManager.authorize(this::getAuthentication, request)

 메서드 보안에서는 같은 계약을 MethodInvocation 에 대해 쓴다
```

- [RequestMatcherDelegatingAuthorizationManager.authorize](../../02_RequestMatcherDelegatingAuthorizationManager.authorize/README.md)
- [AuthoritiesAuthorizationManager.authorize](../../03_AuthoritiesAuthorizationManager.authorize/README.md)

## 구현 계층

```text
 AuthorizationManager<T>
   +-- RequestMatcherDelegatingAuthorizationManager  매처로 다른 매니저에 위임
   +-- AuthorityAuthorizationManager       hasRole / hasAuthority
   |     +-- (안에서 AuthoritiesAuthorizationManager 에 위임한다)
   +-- AllAuthoritiesAuthorizationManager  권한을 모두 가져야 통과
   +-- RequiredAuthoritiesAuthorizationManager
   +-- AuthenticatedAuthorizationManager   authenticated / fullyAuthenticated
   |                                       / anonymous / rememberMe
   +-- SingleResultAuthorizationManager    permitAll / denyAll 처럼 늘 같은 답
   +-- ConditionalAuthorizationManager
   +-- AllRequiredFactorsAuthorizationManager
   +-- IpAddressAuthorizationManager       (web 모듈)
   +-- ObservationAuthorizationManager     다른 매니저를 감싸 계측한다
   +-- (표현식, 메서드 보안용 구현들)

 여러 매니저를 조합하는 것은 AuthorizationManagers 의 정적 메서드다
   allOf, anyOf, not

 리액티브 쪽은 ReactiveAuthorizationManager 라는 별도 인터페이스다
```

## 결과가 쓰이는 곳

```text
 authorize 의 반환
      --> null 을 돌려줄 수 있다 (@Nullable)
      --> AuthorizationFilter 는 null 을 거부로 보지 않고 통과시킨다
      --> 거부하려면 isGranted() 가 false 인 결과를 돌려줘야 한다

 default verify
      --> authorize 를 부르고 거부면 AuthorizationDeniedException 을 던진다
      --> 다만 서블릿 경로에서는 아무도 이것을 부르지 않는다
          AuthorizationFilter 조차 L96-100 에서 같은 판정을 직접 쓴다
      --> 실제로 불리는 것은 이름이 같은 ReactiveAuthorizationManager.verify 다

 Supplier 로 받는 Authentication
      --> 필요할 때만 꺼내라는 뜻이다
      --> permitAll 은 아예 꺼내지 않아 컨텍스트를 읽지 않는다
