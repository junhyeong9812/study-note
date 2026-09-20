# AuthenticationTrustResolver

상위: [spi](../README.md)

현재 인증이 얼마나 믿을 만한지 판정한다. 401 과 403 의 갈림길이 이 판정에 달려 있다.

## 위치

`core` / `org.springframework.security.authentication` / `AuthenticationTrustResolver.java` L29-L89 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authentication/AuthenticationTrustResolver.java#L29-L89))

## 실제 코드

```java
// AuthenticationTrustResolver.java L29-L89 (javadoc 생략)
public interface AuthenticationTrustResolver {

    boolean isAnonymous(@Nullable Authentication authentication);

    boolean isRememberMe(@Nullable Authentication authentication);

    default boolean isFullyAuthenticated(@Nullable Authentication authentication) {
        return isAuthenticated(authentication) && !isRememberMe(authentication);
    }

    @Contract("null -> false")
    default boolean isAuthenticated(@Nullable Authentication authentication) {
        return authentication != null && authentication.isAuthenticated() && !isAnonymous(authentication);
    }

}
```

## 흐름에서 불리는 자리

```text
 ExceptionTranslationFilter.handleAccessDeniedException
   L191 authenticationTrustResolver.isAnonymous(authentication)
   L192 || authenticationTrustResolver.isRememberMe(authentication)
```

- [ExceptionTranslationFilter.handleAccessDeniedException](../../01_ExceptionTranslationFilter.doFilter/01_ExceptionTranslationFilter.handleAccessDeniedException/README.md)

## 구현 계층

```text
 AuthenticationTrustResolver
   +-- AuthenticationTrustResolverImpl   기본
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 isAnonymous / isRememberMe
      --> 추상 메서드 둘이다. 구현이 반드시 채워야 한다

 isAuthenticated / isFullyAuthenticated
      --> default 메서드다. 위의 둘로 조합해 만든다
          isAuthenticated  = 인증이 있고 authenticated 이며 익명이 아님
          isFullyAuthenticated = isAuthenticated 이고 기억된 사용자가 아님

 세 단계의 신뢰 수준
      --> 익명 < 기억된 사용자 < 완전 인증
      --> 인가 규칙의 anonymous(), rememberMe(), fullyAuthenticated() 가
          같은 구분을 쓴다

 판정이 갈림길을 정하는 점
      --> 앞의 둘이면 인증을 다시 요구한다 (더 하면 풀릴 수 있다)
      --> 완전 인증이면 403 이다 (더 해도 달라지지 않는다)
```
