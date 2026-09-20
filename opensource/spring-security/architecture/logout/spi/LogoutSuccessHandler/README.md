# LogoutSuccessHandler

상위: [spi](../README.md)

정리가 끝난 뒤 응답을 쓴다. 로그아웃 경로에서 응답을 만드는 유일한 자리다.

## 위치

`web` / `org.springframework.security.web.authentication.logout` / `LogoutSuccessHandler.java` L39-L44 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/logout/LogoutSuccessHandler.java#L39-L44))

## 실제 코드

```java
// LogoutSuccessHandler.java L39-L44
public interface LogoutSuccessHandler {

    void onLogoutSuccess(HttpServletRequest request, HttpServletResponse response,
            @Nullable Authentication authentication) throws IOException, ServletException;

}
```

## 흐름에서 불리는 자리

```text
 LogoutFilter.doFilter
   L107 logoutSuccessHandler.onLogoutSuccess(request, response, auth)
   핸들러들이 모두 끝난 뒤, return 하기 직전이다
```

- [LogoutFilter.doFilter](../../01_LogoutFilter.doFilter/README.md)

## 구현 계층

```text
 LogoutSuccessHandler
   +-- SimpleUrlLogoutSuccessHandler   기본. 지정한 URL 로 리다이렉트
   +-- HttpStatusReturningLogoutSuccessHandler  상태 코드만. API 용
   +-- ForwardLogoutSuccessHandler     포워드한다
   +-- DelegatingLogoutSuccessHandler  요청에 따라 나눈다
   +-- (OIDC, SAML 등 모듈별 구현)
   +-- (사용자 구현)

 LogoutFilter 의 두 번째 생성자는 URL 을 받아
 SimpleUrlLogoutSuccessHandler 를 직접 만든다 (L85-89)
```

## 결과가 쓰이는 곳

```text
 쓴 응답
      --> 그것으로 요청이 끝난다. 필터가 바로 return 한다
      --> 리다이렉트가 기본이라 브라우저를 전제한다

 REST API 로 쓰는 경우
      --> HttpStatusReturningLogoutSuccessHandler 로 바꿔
          204 나 200 만 돌려주는 식으로 만든다
      --> 리다이렉트를 따라가지 않는 클라이언트에 맞춘다

 넘겨받는 authentication
      --> 이미 컨텍스트에서는 지워진 값이다
      --> 필터가 지우기 전에 꺼내 두었다가 넘긴 것이다
      --> null 일 수 있다
```
