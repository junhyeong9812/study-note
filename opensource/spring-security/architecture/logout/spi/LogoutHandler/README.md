# LogoutHandler

상위: [spi](../README.md)

로그아웃 때 정리할 것이 있으면 이 계약을 구현한다. 메서드 하나에 반환값이 없다.

## 위치

`web` / `org.springframework.security.web.authentication.logout` / `LogoutHandler.java` L33-L43 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/logout/LogoutHandler.java#L33-L43))

## 실제 코드

```java
// LogoutHandler.java L33-L43 (javadoc 생략)
public interface LogoutHandler {

    void logout(HttpServletRequest request, HttpServletResponse response, @Nullable Authentication authentication);

}
```

## 흐름에서 불리는 자리

```text
 LogoutFilter.doFilter
   L106 handler.logout(request, response, auth)
   이 handler 는 언제나 CompositeLogoutHandler 다
```

- [CompositeLogoutHandler.logout](../../01_LogoutFilter.doFilter/01_CompositeLogoutHandler.logout/README.md)
- [SecurityContextLogoutHandler.logout](../../01_LogoutFilter.doFilter/02_SecurityContextLogoutHandler.logout/README.md)

## 구현 계층

```text
 LogoutHandler
   +-- CompositeLogoutHandler                여럿을 묶어 순서대로 부른다
   +-- SecurityContextLogoutHandler          세션 무효화 + 컨텍스트 정리
   +-- LogoutSuccessEventPublishingLogoutHandler  이벤트 발행
   +-- CookieClearingLogoutHandler           쿠키를 지운다
   +-- CsrfLogoutHandler                     CSRF 토큰을 지운다
   +-- HeaderWriterLogoutHandler             응답 헤더를 쓴다
   +-- AbstractRememberMeServices            RememberMeServices 가 이 계약도 구현한다
   +-- OidcBackChannelLogoutHandler          config 모듈. OIDC 백채널
   +-- (사용자 구현)

 서블릿 쪽 main 구현은 이 아홉이다

 Java 설정(LogoutConfigurer)이 목록 끝에 둘을 덧붙인다 (L334-335)
   SecurityContextLogoutHandler
   LogoutSuccessEventPublishingLogoutHandler
```

## 결과가 쓰이는 곳

```text
 반환값이 없는 점
      --> 성공 여부를 알릴 방법이 없다
      --> 합성 핸들러도 결과를 보지 않고 다음으로 넘어간다
      --> 실패를 알리려면 예외를 던져야 하고, 그러면 전체가 멈춘다

 @Nullable authentication
      --> 로그인하지 않은 상태의 로그아웃 요청도 들어온다
      --> 구현은 null 을 다룰 수 있어야 한다

 응답을 쓰지 않는 계약
      --> 응답은 LogoutSuccessHandler 의 몫이다
      --> 다만 HeaderWriterLogoutHandler 처럼 헤더를 쓰는 구현은 있다
```
