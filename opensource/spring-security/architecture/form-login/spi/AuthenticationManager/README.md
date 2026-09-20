# AuthenticationManager

상위: [spi](../README.md)

인증의 입구다. 메서드 하나뿐이고, 인증 방식이 무엇이든 이 모양을 거친다.

## 위치

`core` / `org.springframework.security.authentication` / `AuthenticationManager.java` L29-L57 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authentication/AuthenticationManager.java#L29-L57))

## 실제 코드

```java
// AuthenticationManager.java L29-L57 (javadoc 생략)
public interface AuthenticationManager {

    Authentication authenticate(Authentication authentication) throws AuthenticationException;

}
```

## 흐름에서 불리는 자리

```text
 UsernamePasswordAuthenticationFilter.attemptAuthentication
   L87 getAuthenticationManager().authenticate(authRequest)
```

- [ProviderManager.authenticate](../../02_ProviderManager.authenticate/README.md)

## 구현 계층

```text
 AuthenticationManager
   +-- ProviderManager               기본. 프로바이더 목록에 위임한다
   +-- ObservationAuthenticationManager  다른 매니저를 감싸 계측한다
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 반환 계약
      --> 인증된 Authentication 을 돌려주거나
      --> AuthenticationException 을 던지거나 둘 중 하나다
      --> null 은 계약 위반이다. 반환 타입에 @Nullable 이 없고,
          AbstractAuthenticationProcessingFilter L365-366 이
          ServletException 을 던진다
      --> null 로 "다음 프로바이더에게 넘겨라"를 표현하는 것은
          AuthenticationProvider 쪽 계약이다

 인자와 반환이 같은 타입인 점
      --> 들어올 때는 unauthenticated, 나갈 때는 authenticated 다
      --> 같은 인터페이스로 "주장"과 "확인"을 모두 표현한다
```
