# AuthenticationEntryPoint

상위: [spi](../README.md)

"인증을 시작하라"는 응답을 만든다. 인증 방식마다 이 응답의 모양이 다르다.

## 위치

`web` / `org.springframework.security.web` / `AuthenticationEntryPoint.java` L33-L52 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/AuthenticationEntryPoint.java#L33-L52))

## 실제 코드

```java
// AuthenticationEntryPoint.java L33-L52 (javadoc 생략)
public interface AuthenticationEntryPoint {

    void commence(HttpServletRequest request, HttpServletResponse response, AuthenticationException authException)
            throws IOException, ServletException;

}
```

## 흐름에서 불리는 자리

```text
 ExceptionTranslationFilter.sendStartAuthentication
   L221 authenticationEntryPoint.commence(request, response, reason)
```

- [ExceptionTranslationFilter.sendStartAuthentication](../../01_ExceptionTranslationFilter.doFilter/02_ExceptionTranslationFilter.sendStartAuthentication/README.md)

## 구현 계층

```text
 AuthenticationEntryPoint
   +-- Http403ForbiddenEntryPoint          아무 인증 방식도 구성하지 않았을 때의 기본
   |                                       ExceptionHandlingConfigurer L297 이 꽂는다
   +-- LoginUrlAuthenticationEntryPoint    로그인 페이지로 리다이렉트
   +-- BasicAuthenticationEntryPoint       401 + WWW-Authenticate
   +-- DigestAuthenticationEntryPoint
   +-- HttpStatusEntryPoint                지정한 상태 코드만
   +-- NoOpAuthenticationEntryPoint
   +-- DelegatingAuthenticationEntryPoint  요청에 따라 위의 것들을 고른다
   +-- BearerTokenAuthenticationEntryPoint / DPoPAuthenticationEntryPoint
   |                                       (OAuth2 리소스 서버)
   +-- CasAuthenticationEntryPoint
   +-- (사용자 구현)

 SAML 로그인은 전용 진입점을 두지 않고
 LoginUrlAuthenticationEntryPoint 를 그대로 쓴다
```

## 결과가 쓰이는 곳

```text
 commence 가 쓴 응답
      --> 브라우저용이면 302 리다이렉트
      --> API 용이면 401 이 보통이다
      --> 한 애플리케이션에 둘 다 필요하면
          DelegatingAuthenticationEntryPoint 로 요청을 보고 나눈다

 넘겨받는 AuthenticationException
      --> 왜 인증이 필요한지를 담고 있다
      --> 접근 거부에서 온 경우 InsufficientAuthenticationException 이고
          원래 AccessDeniedException 이 cause 로 들어 있다

 필터가 생성자에서 요구하는 점
      --> 생성자 둘 다 진입점을 필수로 받는다 (L101-110, Assert L106)
      --> afterPropertiesSet 도 같은 것을 한 번 더 확인한다 (L113-115)
      --> 진입점을 한 번도 부르지 않는 경로는 있다.
          완전 인증 사용자의 거부는 L210 에서 핸들러로만 끝난다
```
