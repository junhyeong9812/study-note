# AuthorizationFilter.getAuthentication

상위: [AuthorizationFilter.doFilter](../README.md)

세 줄짜리 메서드지만, 인가와 [보안 컨텍스트](../../../security-context/README.md) 흐름이 만나는 지점이다.

## 위치

`web` / `org.springframework.security.web.access.intercept` / `AuthorizationFilter.java` L139-L146 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/intercept/AuthorizationFilter.java#L139-L146))

## 실제 코드

```java
// AuthorizationFilter.java L139-L146
private Authentication getAuthentication() {
    Authentication authentication = this.securityContextHolderStrategy.getContext().getAuthentication();
    if (authentication == null) {
        throw new AuthenticationCredentialsNotFoundException(
                "An Authentication object was not found in the SecurityContext");
    }
    return authentication;
}
```

## 동작 흐름

```text
 getAuthentication()
 |
 | L140 securityContextHolderStrategy.getContext().getAuthentication()
 |
 +-- L141 null 이면
 |        L142 AuthenticationCredentialsNotFoundException
 |
 +-- L145 아니면 그대로 반환
```

```text
 메서드 참조로 넘긴다

 L96 authorizationManager.authorize(this::getAuthentication, request)
                                    ^^^^^^^^^^^^^^^^^^^^^^^

 값이 아니라 Supplier 다
 매니저가 get() 을 불러야 이 코드가 돈다

 permitAll 규칙은 get() 을 부르지 않는다
 --> getContext() 도 불리지 않는다
 --> 지연된 SecurityContext 가 저장소를 읽지 않는다
 --> 정적 리소스에 permitAll 을 걸면 SecurityContext 저장소를 읽지 않는다
```

```text
 보통은 null 이 오지 않는다

 getContext() 는 null 을 돌려주지 않고 빈 컨텍스트를 만든다
 하지만 그 빈 컨텍스트의 authentication 은 null 이다

 그런데 기본 체인에는 AnonymousAuthenticationFilter 가 있어
 인증이 없으면 익명 토큰(principal "anonymousUser", 권한 ROLE_ANONYMOUS)을
 미리 심어 둔다

 그래서 기본 체인에서는 L142 의 예외에 닿기 어렵다
 익명 필터는 FilterOrderRegistration 상 AuthorizationFilter 보다 앞이다
```

## 결과가 쓰이는 곳

```text
 돌려준 Authentication
      --> getAuthorities() 가 권한 대조의 입력이다
      --> isAuthenticated() 를 authenticated() 규칙이 본다

 익명 토큰
      --> 인증되지 않은 사용자도 Authentication 객체를 갖는다
      --> 그래서 "인증 안 됨"과 "권한 부족"을 같은 코드로 다룰 수 있다
      --> 둘을 가르는 것은 뒤의 ExceptionTranslationFilter 다

 던진 AuthenticationCredentialsNotFoundException
      --> AuthenticationException 계열이라
          예외 변환 필터가 인증 진입점으로 보낸다
      --> 403 이 아니라 로그인 요구가 된다
```
