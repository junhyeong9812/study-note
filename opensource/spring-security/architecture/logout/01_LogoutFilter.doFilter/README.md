# LogoutFilter.doFilter

상위: [로그아웃](../README.md)

로그아웃 요청인지 보고, 맞으면 핸들러를 돌린 뒤 체인을 끊는다.

## 위치

`web` / `org.springframework.security.web.authentication.logout` / `LogoutFilter.java` L99-L111 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/logout/LogoutFilter.java#L99-L111))

## 실제 코드

public 진입점은 캐스팅만 한다.

```java
// LogoutFilter.java L93-L97
@Override
public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    doFilter((HttpServletRequest) request, (HttpServletResponse) response, chain);
}
```

```java
// LogoutFilter.java L99-L111
private void doFilter(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    if (requiresLogout(request, response)) {
        Authentication auth = this.securityContextHolderStrategy.getContext().getAuthentication();
        if (this.logger.isDebugEnabled()) {
            this.logger.debug(LogMessage.format("Logging out [%s]", auth));
        }
        this.handler.logout(request, response, auth);
        this.logoutSuccessHandler.onLogoutSuccess(request, response, auth);
        return;
    }
    chain.doFilter(request, response);
}
```

매처 판정은 바로 아래에 있다.

`web` / `org.springframework.security.web.authentication.logout` / `LogoutFilter.java` L119-L127 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/logout/LogoutFilter.java#L119-L127))

```java
// LogoutFilter.java L119-L127
protected boolean requiresLogout(HttpServletRequest request, HttpServletResponse response) {
    if (this.logoutRequestMatcher.matches(request)) {
        return true;
    }
    if (this.logger.isTraceEnabled()) {
        this.logger.trace(LogMessage.format("Did not match request to %s", this.logoutRequestMatcher));
    }
    return false;
}
```

## 동작 흐름

```text
 doFilter(request, response, chain)
 |
 +-- L101 requiresLogout(request, response)
 |      |
 |      +-- L120 logoutRequestMatcher.matches(request) 이면 L121 true
 |      +-- L126 아니면 false (L123-125 는 trace 로그)
 |
 +-- 로그아웃 요청이면
 |      L102 현재 컨텍스트에서 Authentication 을 꺼낸다
 |      L106 handler.logout(request, response, auth)
 |             CompositeLogoutHandler 다 (생성자 L74, L82)
 |      L107 logoutSuccessHandler.onLogoutSuccess(request, response, auth)
 |      L108 return -- 체인을 끊는다
 |
 +-- L110 아니면 chain.doFilter
```

```text
 인증을 먼저 꺼내 둔다

 L102 에서 꺼낸 auth 를 L106 과 L107 에 넘긴다

 핸들러가 컨텍스트를 비우기 때문에,
 비운 뒤에 꺼내면 null 이 된다
 그래서 비우기 전에 꺼내 인자로 전달한다

 성공 핸들러도 "누가 로그아웃했는지"를 알 수 있다
```

```text
 auth 가 null 일 수 있다

 L102 는 null 검사를 하지 않는다
 로그인하지 않은 상태로 /logout 을 호출하면 null 이 넘어간다

 그래서 LogoutHandler 와 LogoutSuccessHandler 의
 authentication 파라미터는 @Nullable 로 선언되어 있다

 로그아웃은 "이미 로그아웃된 상태"에서 불려도 성공으로 처리된다
```

```text
 기본 URL 은 생성자가 정한다

 생성자 둘 다 L77 / L90 에서 setFilterProcessesUrl("/logout") 을 부른다
 그 메서드는 L146 에서 경로 패턴 매처를 만든다

 설정을 쓰면 LogoutConfigurer 가 L339 에서
 setLogoutRequestMatcher 로 덮어쓴다
 그때 CSRF 설정 여부에 따라 허용 메서드가 달라진다
```

## 결과가 쓰이는 곳

```text
 체인을 끊는 것
      --> 매처에 걸린 요청은 컨트롤러에 닿지 않는다
      --> 기본 매처가 POST 전용이므로 @PostMapping("/logout") 은 불리지 않는다
      --> GET 은 이 매처에 안 걸린다. 커스텀 로그아웃 엔드포인트를
          컨트롤러로 만드는 것은 레퍼런스가 안내하는 정식 선택지다

 넘긴 auth
      --> 핸들러들이 "누구를 로그아웃시키는지" 안다
      --> 이벤트 발행 핸들러가 이 값을 이벤트에 담는다

 성공 핸들러
      --> 응답을 쓰는 유일한 자리다
      --> 기본은 SimpleUrlLogoutSuccessHandler 계열의 리다이렉트다
```

## 하위 메서드

- [01 CompositeLogoutHandler.logout](01_CompositeLogoutHandler.logout/README.md)
- [02 SecurityContextLogoutHandler.logout](02_SecurityContextLogoutHandler.logout/README.md)
