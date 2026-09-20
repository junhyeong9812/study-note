# AuthenticationProvider

상위: [spi](../README.md)

인증 방식 하나를 담당한다. `supports` 로 자기가 다룰 토큰인지 먼저 말한다.

## 위치

`core` / `org.springframework.security.authentication` / `AuthenticationProvider.java` L30-L67 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authentication/AuthenticationProvider.java#L30-L67))

## 실제 코드

```java
// AuthenticationProvider.java L30-L67 (javadoc 생략)
public interface AuthenticationProvider {

    @Nullable Authentication authenticate(Authentication authentication) throws AuthenticationException;

    boolean supports(Class<?> authentication);

}
```

## 흐름에서 불리는 자리

```text
 ProviderManager.authenticate
   L175 provider.supports(toTest)      자기 몫인지 묻는다
   L183 provider.authenticate(...)     맞으면 시도한다
```

- [AbstractUserDetailsAuthenticationProvider.authenticate](../../03_AbstractUserDetailsAuthenticationProvider.authenticate/README.md)

## 구현 계층

```text
 AuthenticationProvider
   +-- AbstractUserDetailsAuthenticationProvider  사용자 조회 + 검사 골격
   |     +-- DaoAuthenticationProvider            UserDetailsService + PasswordEncoder
   +-- (OAuth2, LDAP, remember-me, 익명 등 방식별 구현)
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 supports
      --> 토큰 타입으로 거른다
      --> 여러 인증 방식이 한 매니저에 공존할 수 있는 이유다

 authenticate 의 null 반환
      --> javadoc 은 "이 Authentication 객체의 인증을 지원할 수 없을 때"라고 한다
      --> supports 가 true 여도 실제로는 못 다룰 수 있다는 뜻이다
      --> ProviderManager 가 다음 프로바이더로 넘어간다
      --> 실패를 뜻하려면 예외를 던져야 한다

 던지는 예외의 종류
      --> AccountStatusException 과 InternalAuthenticationServiceException 은
          매니저가 즉시 다시 던진다
      --> 그 밖의 AuthenticationException 은 보관되고 다음 프로바이더가 이어 시도한다
```
